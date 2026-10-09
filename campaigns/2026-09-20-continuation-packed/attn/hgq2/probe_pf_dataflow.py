#!/usr/bin/env python3
'Characterize HLS parallelization factors and dataflow for binary-transformer inference.'
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback

os.environ.setdefault("KERAS_BACKEND", "tensorflow")

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import convert_binary as cf  # noqa: E402  (the proven export/gate chain — reused, not modified)
from bnhgq2.config import load_config, cfg_hash, PROJECT_ROOT  # noqa: E402

PROBE_NAME = "pfprobe_dataflow_rf8"
OUT_ROOT = os.path.join(PROJECT_ROOT, "results", "adder-graph", "pfprobe")

# the rf8 stdnn export's measured norm-free carry-site grid widths (export_verify.json)
# — reproduced here as a same-export sanity reference, never asserted as a gate.
REF_NF_WIDTHS = {"bit_block_0_attn_Wo": 15, "bit_block_0_ffn_fc2": 16,
                 "bit_block_1_attn_Wo": 16, "bit_block_1_ffn_fc2": 17, "head_fc2": 17}

GATE2_THRESHOLD = 0.997


# --------------------------------------------------------------------------- #
# the intervention                                                             #
# --------------------------------------------------------------------------- #
def token_fold_einsum_dense(hm):
    """Set parallelization_factor=1 on every per-token EinsumDense node (n_free_data>1)
    and RE-RUN the EinsumDense config template on it so the regenerated `config_cpp`
    carries pf=1 (templates were already applied at conversion; write() will not re-run
    them).  Weightless `Einsum` (attention scores/ctx), softmax, affines and the 2-D
    head denses are untouched.  Returns {layer_name: fold record}."""
    from hls4ml.backends.vivado.passes.einsum_dense import EinsumDenseConfigTemplate

    tmpl = EinsumDenseConfigTemplate()
    folded = {}
    for node in hm.get_layers():
        if node.class_name != "EinsumDense":
            continue
        l0 = int(node.attributes["n_free_data"])
        pf_before = int(node.attributes["parallelization_factor"])
        if l0 <= 1:
            continue  # no token axis -> nothing to fold
        node.attributes["parallelization_factor"] = 1
        tmpl.transform(hm, node)  # regenerate config_cpp with pf=1
        folded[node.name] = {"n_free_data": l0, "pf_before": pf_before, "pf_after": 1,
                             "n_contract": int(node.attributes["n_contract"]),
                             "n_free_kernel": int(node.attributes["n_free_kernel"])}
    return folded


def convert_dataflow(model, cfg, out_dir, rf, csim_X, keras_ref, post_parse):
    """bnhgq2.convert.convert with ONE addition: `PipelineStyle: 'dataflow'` in the
    model-level hls_config (bnhgq2.convert has no plumbing for it and existing files
    must not be edited — this wrapper is the additive path).  Same backend/io/part/
    clock/bit_exact, same macOS csim patching, same report shape."""
    import platform

    import hls4ml

    from bnhgq2.compat import apply_hls4ml_compat, patch_project_for_macos
    from bnhgq2.subln import register_subln

    apply_hls4ml_compat()
    register_subln()

    hlscfg = cfg["hls"]
    config = {
        "Model": {
            "Precision": "fixed<24,12>",  # fallback only; BitExact overrides the quantized path
            "ReuseFactor": rf,
            "Strategy": "Latency",
            "PipelineStyle": "dataflow",  # THE intervention: no whole-model PIPELINE region
        },
    }
    hm = hls4ml.converters.convert_from_keras_model(
        model,
        backend=hlscfg.get("backend", "Vitis"),
        io_type=hlscfg.get("io", "io_parallel"),
        output_dir=out_dir,
        part=hlscfg.get("part", "xcvu13p-flga2577-2-e"),
        clock_period=hlscfg.get("clock_ns", 2.5),
        hls_config=config,
        bit_exact=True,  # kwarg, as in bnhgq2.convert (silently rides on hls_config)
    )
    if hm.config.pipeline_style != "dataflow":
        raise RuntimeError(f"PipelineStyle did not stick: model.config.pipeline_style="
                           f"{hm.config.pipeline_style!r} (expected 'dataflow')")
    fold_record = post_parse(hm)
    hm.write()

    report = {"output_dir": out_dir, "rf": rf, "strategy": "Latency",
              "pipeline_style": hm.config.pipeline_style,
              "backend": hlscfg.get("backend", "Vitis")}

    if csim_X is not None:
        if platform.system() == "Darwin":
            # patch AFTER write() and compile via _compile() — plain compile()
            # re-writes the project and undoes the patch (bnhgq2.convert precedent)
            patch_project_for_macos(out_dir)
        hm._compile()
        xs = np.ascontiguousarray(csim_X.astype(np.float32))
        y_hls = hm.predict(xs)
        ref = keras_ref if keras_ref is not None else np.asarray(model(csim_X, training=False))
        y_hls = y_hls.reshape(ref.shape)
        d = np.abs(y_hls - ref)
        report["csim"] = {
            "n": int(len(csim_X)),
            "max_abs_diff": float(d.max()),
            "mean_abs_diff": float(d.mean()),
            "bit_exact": bool(d.max() == 0.0),
            "corr": float(np.corrcoef(y_hls.ravel(), ref.ravel())[0, 1]),
        }
    return hm, report, fold_record


# --------------------------------------------------------------------------- #
# emitted-firmware audit                                                       #
# --------------------------------------------------------------------------- #
def audit_pragmas(out_dir):
    """Read back what was actually emitted: every `#pragma HLS` line in the top function
    (firmware/myproject.cpp) and every `parallelization_factor` line in
    firmware/parameters.h.  The probe's claim lives or dies on these lines."""
    cpp = os.path.join(out_dir, "firmware", "myproject.cpp")
    par = os.path.join(out_dir, "firmware", "parameters.h")
    top_pragmas = [ln.strip() for ln in open(cpp) if "#pragma HLS" in ln]
    pf_lines = [ln.strip() for ln in open(par) if "parallelization_factor" in ln]
    counts = {kw: sum(1 for ln in top_pragmas if kw in ln)
              for kw in ("DATAFLOW", "PIPELINE", "UNROLL", "ARRAY_PARTITION", "INLINE")}
    pf_values = {}
    for ln in pf_lines:
        # "static const unsigned parallelization_factor = N; ..."
        try:
            val = int(ln.split("=")[1].split(";")[0].strip())
            pf_values[val] = pf_values.get(val, 0) + 1
        except (IndexError, ValueError):
            pass
    return {"myproject_cpp_pragmas": top_pragmas, "pragma_counts": counts,
            "parameters_h_pf_lines": pf_lines, "pf_value_histogram": pf_values}


# --------------------------------------------------------------------------- #
# driver                                                                       #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--checkpoint", required=True, help="Local model_best.keras")
    ap.add_argument("--config", required=True, help="Model configuration JSON")
    ap.add_argument("--rf", type=int, default=8, help="ReuseFactor (8 = the census build)")
    ap.add_argument("--n-gate", type=int, default=4096,
                    help="gate/calibration jets (4096 = the rf8 build; keeps the "
                         "norm-free grid-sizing jets Xg[:2048] identical)")
    ap.add_argument("--n-csim", type=int, default=128)
    ap.add_argument("--skip-gate1", action="store_true",
                    help="skip the informational export-vs-QAT gate1 (GATE2 is the gate)")
    ap.add_argument("--widen-accum", action="store_true",
                    help="widen weighted-layer accums (convert_binary --widen-accum). OFF "
                         "by default: the reference rf8 build ran widen_accum=false")
    ap.add_argument("--data-dir", default=None)
    a = ap.parse_args()

    cfg = load_config(a.config)
    input_std_path = os.path.join(os.path.dirname(a.checkpoint), "input_std.json")
    h = cfg_hash(cfg)
    A = cfg["arch"]
    os.makedirs(OUT_ROOT, exist_ok=True)
    stage = "fetch"
    manifest = {
        "probe": PROBE_NAME,
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "question": "can hls4ml 1.3.0 emit a token-folded model from config/attribute "
                    "space (PipelineStyle=dataflow + parallelization_factor=1)?",
        "source": {
            "config": cfg["name"], "config_hash": h,
        },
        "hls": {"part": cfg["hls"].get("part"), "clock_ns": cfg["hls"].get("clock_ns"),
                "backend": "Vitis", "io": "io_parallel", "strategy": "Latency",
                "rf": a.rf, "pipeline_style": "dataflow",
                "widen_accum": bool(a.widen_accum)},
        "bands": ("SUCCESS = any per-token dense >=3x under its "
                  "whole_model_rf8_stdnn.xml census line with a workable dataflow "
                  "interval (report the interval; no rewind hook exists so interval "
                  "may land ~latency+II); failure = area unchanged / conversion or csim "
                  "failure / unbounded interval."),
        "status": "INCOMPLETE",
    }

    def bail(exc):
        manifest["status"] = "failed configuration: failure during stage '%s'" % stage
        manifest["error"] = {"stage": stage, "type": type(exc).__name__,
                             "message": str(exc),
                             "traceback": traceback.format_exc()}
        mpath = os.path.join(OUT_ROOT, "manifest_pfprobe.json")
        with open(mpath, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\n[failed configuration] {type(exc).__name__} during '{stage}': {exc}\n"
              f"                 full traceback in {os.path.relpath(mpath, PROJECT_ROOT)}",
              flush=True)
        sys.exit(1)

    try:
        # ---- (1) checkpoint: local cache wins; W&B fallback exactly as convert_binary
        kp = os.path.abspath(a.checkpoint)
        if not os.path.isfile(kp):
            raise FileNotFoundError(kp)
        manifest["source"]["checkpoint"] = (os.path.relpath(kp, PROJECT_ROOT)
                                            if kp.startswith(PROJECT_ROOT) else kp)
        if not os.path.isfile(input_std_path):
            raise FileNotFoundError(f"{input_std_path}: input_std.json is required by the preprocessing "
                                    "contract (arch.input_std=true) — refusing to gate "
                                    "on unstandardized jets")
        manifest["source"]["input_std"] = os.path.relpath(input_std_path, PROJECT_ROOT)

        # ---- (2) load + jets (input_std applied, reference experiment contract)
        stage = "load"
        qat_model = cf.load_qat_model(kp)
        print(f"[load] {os.path.basename(kp)}  params={qat_model.count_params():,}", flush=True)
        data_dir = a.data_dir or os.path.join(PROJECT_ROOT, "data", "val")
        Xg, _ = cf._load_jets(data_dir, A["n_part"], a.n_gate, features=A.get("features"))
        from bnhgq2.data import apply_input_std
        _std = json.load(open(input_std_path))
        Xg = apply_input_std(Xg, _std["mu"], _std["sigma"])
        print(f"[data] {len(Xg)} real jets, input_std applied", flush=True)

        # ---- (3) export: the identical convert_binary chain (binz/calib/norm-free grids)
        stage = "export"
        binz, pe, names = cf.qat_binz_pe(qat_model, cfg)
        calib = cf.read_qat_act_ibits(qat_model, names)
        calib.update(cf.qat_stream_ranges(qat_model, cfg, binz, Xg[:2048]))
        export_model = cf.build_export(cfg, binz, calib, pe, beta_mode="csd2",
                                       qat_model=qat_model, attn_grids="build_default",
                                       calib_jets=Xg[:2048])
        nf_grids = getattr(export_model, "_bnhgq2_norm_free_grids", {})
        nf_widths = {n: v["width"] for n, v in nf_grids.items()}
        manifest["export"] = {
            "norm_free_grids": nf_grids,
            "nf_widths_match_rf8_reference": nf_widths == REF_NF_WIDTHS,
            "weight_export_max_abs_diff": cf.weight_export_exactness(qat_model, binz),
        }
        print(f"[export] {export_model.count_params():,} params; norm-free widths "
              f"{'MATCH' if nf_widths == REF_NF_WIDTHS else 'DIFFER from'} the rf8 "
              f"reference {REF_NF_WIDTHS}", flush=True)

        # ---- (4) gate1 (informational — 0.989 is this reference model's characterized ceiling)
        if not a.skip_gate1:
            stage = "gate1"
            g1 = cf.gate1(qat_model, export_model, Xg)
            manifest["gate1_informational"] = {
                "corr_scores": g1["corr_scores"], "argmax_agreement": g1["argmax_agreement"],
                "note": "export vs QAT; 0.98907 = the characterized DSP-free ceiling of "
                        "this norm-free flagship (LEDGER 2026-07-18), NOT a probe gate",
            }
            print(f"[GATE1] (informational) corr_scores={g1['corr_scores']:.6f}", flush=True)

        # ---- (5) convert with PipelineStyle=dataflow, fold in post-parse, GATE2 csim
        stage = "convert+csim"
        cf.patch_resource_einsum_check()
        out = os.path.join(OUT_ROOT, PROBE_NAME)
        import shutil
        shutil.rmtree(out, ignore_errors=True)
        csim_X = Xg[:a.n_csim]
        keras_ref = cf.predict(export_model, csim_X)
        widen_n = {"n": 0}

        def post_parse(hm):
            cf.fix_relu_saturation(hm)
            if a.widen_accum:
                widen_n["n"] = cf.widen_weighted_accum(hm)
            return token_fold_einsum_dense(hm)

        hm, report, folded = convert_dataflow(export_model, cfg, out, a.rf,
                                              csim_X, keras_ref, post_parse)
        manifest["folded_layers"] = folded
        manifest["n_folded"] = len(folded)
        manifest["n_layers_widened"] = widen_n["n"]
        expected = 4 * A["n_layers"] + 2 * A["n_layers"] + 1  # Wq/Wk/Wv/Wo + fc1/fc2 + input_proj
        if len(folded) != expected:
            print(f"[WARN] folded {len(folded)} EinsumDense layers, expected {expected} "
                  f"(input_proj + {expected - 1} block denses) — check folded_layers",
                  flush=True)
        print(f"[fold] pf=1 on {len(folded)} per-token EinsumDense layers: "
              + ", ".join(sorted(folded)), flush=True)

        stage = "audit"
        manifest["pragma_audit"] = audit_pragmas(out)
        pc = manifest["pragma_audit"]["pragma_counts"]
        print(f"[audit] myproject.cpp pragmas: DATAFLOW={pc['DATAFLOW']} "
              f"PIPELINE={pc['PIPELINE']} UNROLL={pc['UNROLL']}; parameters.h pf "
              f"histogram={manifest['pragma_audit']['pf_value_histogram']}", flush=True)

        cs = report.get("csim", {})
        g2_pass = cs.get("corr", 0.0) >= GATE2_THRESHOLD
        manifest["gate2"] = {"csim": cs, "threshold": GATE2_THRESHOLD,
                             "pass": bool(g2_pass),
                             "reference": "export model predictions (as convert_binary)"}
        print(f"[GATE2] hls4ml C-sim vs export: corr={cs.get('corr')} "
              f"max|delta|={cs.get('max_abs_diff')} bit_exact={cs.get('bit_exact')} "
              f"pass={g2_pass}", flush=True)
        if not g2_pass:
            manifest["status"] = "failed configuration: GATE2 csim failed (corr < 0.997)"
            mpath = os.path.join(OUT_ROOT, "manifest_pfprobe.json")
            with open(mpath, "w") as f:
                json.dump(manifest, f, indent=2)
            print(f"[failed configuration] GATE2 failed -> {os.path.relpath(mpath, PROJECT_ROOT)}",
                  flush=True)
            sys.exit(2)

        # ---- (6) pack for the synthesis host (ship + csynth happen elsewhere, on purpose)
        stage = "pack"
        from bnhgq2.convert import package_hls_project
        tar = package_hls_project(out, out + ".tar.gz")
        manifest["tarball"] = os.path.relpath(tar, PROJECT_ROOT)
        manifest["synthesis_command"] = "vitis_hls -f build_prj.tcl"
        manifest["status"] = "EMITTED — GATE2 PASS — ready for HLS synthesis"

        mpath = os.path.join(OUT_ROOT, "manifest_pfprobe.json")
        with open(mpath, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\n[done] {PROBE_NAME}: GATE2 PASS; folded {len(folded)} einsum denses\n"
              f"       manifest -> {os.path.relpath(mpath, PROJECT_ROOT)}\n"
              f"       tarball  -> {os.path.relpath(tar, PROJECT_ROOT)}\n"
              f"       synthesis -> {manifest['synthesis_command']}", flush=True)

    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — a KILL band IS a result; record it
        bail(exc)


if __name__ == "__main__":
    main()
