#!/usr/bin/env python3
"""PF-PROBE v2 — can hls4ml 1.3.0 emit a TOKEN-FOLDED flagship from config/attribute space?

Mechanism (measured on the installed hls4ml 1.3.0; experiment-log 2026-07-26
"PF-PROBE v2 DESIGN"):
  * The deployed flagship firmware's `myproject` body is ONE `#pragma HLS PIPELINE`
    region -> Vitis force-unrolls every loop inside it; no reuse knob could ever roll
    the token axis (why "RF changes nothing").
  * `nnet_einsum_dense.h`'s l0 loop over n_free_data (= the token axis, T=10, for the
    shared-weight per-token denses) carries
    `#pragma HLS UNROLL factor = CONFIG_T::parallelization_factor`;
    `vivado_backend.init_einsum_dense` defaults pf = L0 (fully unrolled) and EinsumDense
    has NO ConfigurableAttribute/config plumbing for ParallelizationFactor -> pf must be
    written into `layer.attributes` on the converted graph.
  * Model-level `PipelineStyle: 'dataflow'` (graph.py `HLSConfig`; validated by
    `vivado:set_pipeline_style`) replaces the force-unroll PIPELINE region with
    `#pragma HLS DATAFLOW` -> each layer is its own process and pf=1 keeps the token
    loop ROLLED: hls4ml's own emission of a T-folded per-token dense.
  * TIMING CAVEAT (found building this probe): hls4ml applies its optimizer flows —
    including `vivado:apply_templates`, which bakes `parallelization_factor` into each
    einsum-dense `config_cpp` — at ModelGraph CREATION, and `write()` does NOT re-apply
    them.  So setting the attribute alone is not enough: the EinsumDense config template
    must be RE-RUN per folded node after the attribute change (done here in post-parse).

The probe: ONE build of the r8 stdnn flagship (small-stdnn-s2 — the exact
config/checkpoint/export chain behind `whole_model_rf8_stdnn.xml`), identical to the
deployed rf8 emit (io_parallel / Latency / rf=8 / bit_exact / relu-SAT fix /
widen_accum OFF, matching that build's manifest) except the intervention:
  (a) PipelineStyle = 'dataflow' in the model-level hls_config, and
  (b) parallelization_factor = 1 on every per-token EinsumDense (input_proj + the 12
      block denses; the weightless act*act attention einsums, softmax and affines are
      untouched).
Then the GATE2 C-sim fidelity gate (corr >= 0.997 vs the export reference, exactly as
convert_final) and a mulder-ready tarball + manifest.  This script does NOT ship to
mulder and does NOT synthesize.

Pre-registered bands (verbatim in results/adder-graph/pfprobe/DESIGN.md):
  SUCCESS = any per-token dense >=3x under its whole_model_rf8_stdnn.xml census line
  with a workable dataflow interval; KILL = area unchanged / conversion or csim
  failure / unbounded interval.

Usage:
  cd bnjettag/code/hgq2
  KERAS_BACKEND=tensorflow ../../../.venv-hgq2/bin/python probe_pf_dataflow.py
  # options: --checkpoint /path/model_best.keras  --n-gate 4096  --n-csim 128
  #          --skip-gate1  --widen-accum (NOT used by the reference rf8 build)
"""
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

import convert_final as cf  # noqa: E402  (the proven export/gate chain — reused, not modified)
from bnhgq2.config import load_config, cfg_hash, PROJECT_ROOT  # noqa: E402

# ---- flagship provenance (from bnjettag/r7/results/convert/r8stdnn-s2/rf8/*.json) ---- #
FLAGSHIP_CONFIG = os.path.join(_HERE, "configs", "r8-small-w1a8-stdnn.json")
FLAGSHIP_CKPT = os.path.join(PROJECT_ROOT, "bnjettag", "r7", "models",
                             "small-stdnn-s2", "model_best.keras")
FLAGSHIP_STD = os.path.join(PROJECT_ROOT, "bnjettag", "r7", "models",
                            "small-stdnn-s2", "input_std.json")
FLAGSHIP_WANDB_RUN = "r8-small-w1a8-stdnn-s2"   # W&B fallback only; local ckpt wins
FLAGSHIP_WANDB_SUBDIR = "small-stdnn-s2"
CENSUS_XML = os.path.join(PROJECT_ROOT, "bnjettag", "r7", "results", "csynth",
                          "whole_model_rf8_stdnn.xml")

PROBE_NAME = "pfprobe_dataflow_rf8"
OUT_ROOT = os.path.join(PROJECT_ROOT, "bnjettag", "results", "adder-graph", "pfprobe")

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
    ap.add_argument("--checkpoint", default=None,
                    help=f"local model_best.keras (default {FLAGSHIP_CKPT})")
    ap.add_argument("--rf", type=int, default=8, help="ReuseFactor (8 = the census build)")
    ap.add_argument("--n-gate", type=int, default=4096,
                    help="gate/calibration jets (4096 = the rf8 build; keeps the "
                         "norm-free grid-sizing jets Xg[:2048] identical)")
    ap.add_argument("--n-csim", type=int, default=128)
    ap.add_argument("--skip-gate1", action="store_true",
                    help="skip the informational export-vs-QAT gate1 (GATE2 is the gate)")
    ap.add_argument("--widen-accum", action="store_true",
                    help="widen weighted-layer accums (convert_final --widen-accum). OFF "
                         "by default: the reference rf8 build ran widen_accum=false")
    ap.add_argument("--data-dir", default=None)
    a = ap.parse_args()

    cfg = load_config(FLAGSHIP_CONFIG)
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
            "flagship": "r8stdnn-s2 rf8 (bnjettag/r7/results/convert/r8stdnn-s2/rf8)",
            "config": cfg["name"], "config_hash": h,
            "census_xml": os.path.relpath(CENSUS_XML, PROJECT_ROOT),
        },
        "hls": {"part": cfg["hls"].get("part"), "clock_ns": cfg["hls"].get("clock_ns"),
                "backend": "Vitis", "io": "io_parallel", "strategy": "Latency",
                "rf": a.rf, "pipeline_style": "dataflow",
                "widen_accum": bool(a.widen_accum)},
        "bands": ("SUCCESS = any per-token dense >=3x under its "
                  "whole_model_rf8_stdnn.xml census line with a workable dataflow "
                  "interval (report the interval; no rewind hook exists so interval "
                  "may land ~latency+II); KILL = area unchanged / conversion or csim "
                  "failure / unbounded interval."),
        "status": "INCOMPLETE",
    }

    def bail(exc):
        manifest["status"] = "KILL-candidate: failure during stage '%s'" % stage
        manifest["error"] = {"stage": stage, "type": type(exc).__name__,
                             "message": str(exc),
                             "traceback": traceback.format_exc()}
        mpath = os.path.join(OUT_ROOT, "manifest_pfprobe.json")
        with open(mpath, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\n[KILL-candidate] {type(exc).__name__} during '{stage}': {exc}\n"
              f"                 full traceback in {os.path.relpath(mpath, PROJECT_ROOT)}",
              flush=True)
        sys.exit(1)

    try:
        # ---- (1) checkpoint: local cache wins; W&B fallback exactly as convert_final
        ckpt = a.checkpoint or FLAGSHIP_CKPT
        if os.path.isfile(ckpt):
            kp = os.path.abspath(ckpt)
            print(f"[fetch] local checkpoint {os.path.relpath(kp, PROJECT_ROOT)}", flush=True)
        else:
            kp, _ = cf.fetch_checkpoint("w1a8", 2, FLAGSHIP_WANDB_RUN,
                                        os.path.join(PROJECT_ROOT, "bnjettag", "models", "r7"),
                                        local_checkpoint=None, subdir=FLAGSHIP_WANDB_SUBDIR)
        manifest["source"]["checkpoint"] = (os.path.relpath(kp, PROJECT_ROOT)
                                            if kp.startswith(PROJECT_ROOT) else kp)
        if not os.path.isfile(FLAGSHIP_STD):
            raise FileNotFoundError(f"{FLAGSHIP_STD}: input_std.json is part of the r8 "
                                    "contract (arch.input_std=true) — refusing to gate "
                                    "on unstandardized jets")
        manifest["source"]["input_std"] = os.path.relpath(FLAGSHIP_STD, PROJECT_ROOT)

        # ---- (2) load + jets (input_std applied, round-8 contract)
        stage = "load"
        qat_model = cf.load_qat_model(kp)
        print(f"[load] {os.path.basename(kp)}  params={qat_model.count_params():,}", flush=True)
        data_dir = a.data_dir or os.path.join(PROJECT_ROOT, "data", "val")
        Xg, _ = cf._load_jets(data_dir, A["n_part"], a.n_gate)
        from bnhgq2.data import apply_input_std
        _std = json.load(open(FLAGSHIP_STD))
        Xg = apply_input_std(Xg, _std["mu"], _std["sigma"])
        print(f"[data] {len(Xg)} real jets, input_std applied", flush=True)

        # ---- (3) export: the identical convert_final chain (binz/calib/norm-free grids)
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

        # ---- (4) gate1 (informational — 0.989 is this flagship's characterized ceiling)
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
                             "reference": "export model predictions (as convert_final)"}
        print(f"[GATE2] hls4ml C-sim vs export: corr={cs.get('corr')} "
              f"max|delta|={cs.get('max_abs_diff')} bit_exact={cs.get('bit_exact')} "
              f"pass={g2_pass}", flush=True)
        if not g2_pass:
            manifest["status"] = "KILL-candidate: GATE2 csim failed (corr < 0.997)"
            mpath = os.path.join(OUT_ROOT, "manifest_pfprobe.json")
            with open(mpath, "w") as f:
                json.dump(manifest, f, indent=2)
            print(f"[KILL-candidate] GATE2 failed -> {os.path.relpath(mpath, PROJECT_ROOT)}",
                  flush=True)
            sys.exit(2)

        # ---- (6) pack for mulder (ship + csynth happen elsewhere, on purpose)
        stage = "pack"
        from bnhgq2.convert import pack_for_mulder
        tar = pack_for_mulder(out, out + ".tar.gz")
        manifest["tarball"] = os.path.relpath(tar, PROJECT_ROOT)
        manifest["mulder_command"] = (
            f"scp {os.path.relpath(tar, PROJECT_ROOT)} mulder:~/bnjet_hgq2/ && "
            f"ssh mulder 'cd ~/bnjet_hgq2 && ./mulder_csynth.sh {os.path.basename(tar)}'"
        )
        manifest["fetch_command"] = "bnjettag/code/hgq2/fetch_pf.sh"
        manifest["status"] = "EMITTED — GATE2 PASS — ready for mulder (not shipped)"

        mpath = os.path.join(OUT_ROOT, "manifest_pfprobe.json")
        with open(mpath, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\n[done] {PROBE_NAME}: GATE2 PASS; folded {len(folded)} einsum denses\n"
              f"       manifest -> {os.path.relpath(mpath, PROJECT_ROOT)}\n"
              f"       tarball  -> {os.path.relpath(tar, PROJECT_ROOT)}\n"
              f"       mulder   -> {manifest['mulder_command']}", flush=True)

    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — a KILL band IS a result; record it
        bail(exc)


if __name__ == "__main__":
    main()
