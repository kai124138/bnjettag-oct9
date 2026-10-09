#!/usr/bin/env python3
'Convert an eight-bit weight and activation baseline to hls4ml and compare numerical outputs.'
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from bnhgq2.config import load_config, cfg_hash, PROJECT_ROOT  # noqa: E402

import convert_binary as cf  # noqa: E402  — reuse the proven helpers, touch nothing


# --------------------------------------------------------------------------- #
# export: QAT graph minus pos_enc, PE folded into input_proj's bias table      #
# --------------------------------------------------------------------------- #
def build_w8a8_export(cfg: dict, qat_model, seed: int, snap_biases: bool = False):
    """Rebuild the QAT graph without AddPositional, port every layer's variables by
    name, then fold the trained pos table into input_proj's (T,D) bias. Returns
    (export_model, n_layers_ported, max_abs_pos_folded, bias_snap_record)."""
    from bnhgq2.qat import build_qat_model

    export, _taps = build_qat_model(cfg, seed=seed, with_pos_enc=False)

    qat_names = {ly.name for ly in qat_model.layers}
    exp_names = {ly.name for ly in export.layers}
    missing = qat_names - exp_names
    extra = exp_names - qat_names
    if missing != {"pos_enc"} or extra:
        raise SystemExit(f"export graph mismatch: missing={sorted(missing)} "
                         f"extra={sorted(extra)} (expected exactly {{'pos_enc'}} missing)")

    n_ported = 0
    for ly in export.layers:
        src = qat_model.get_layer(ly.name)
        ws, dst = src.get_weights(), ly.get_weights()
        if not ws and not dst:
            continue
        if len(ws) != len(dst):
            raise SystemExit(f"{ly.name}: variable count mismatch {len(ws)} vs {len(dst)}")
        for a, b in zip(ws, dst):
            if tuple(np.shape(a)) != tuple(np.shape(b)):
                raise SystemExit(f"{ly.name}: variable shape mismatch "
                                 f"{np.shape(a)} vs {np.shape(b)}")
        ly.set_weights(ws)
        n_ported += 1

    # the fold: (x·W + b) + pos  ==  x·W + (b + pos)  — exact constant-add identity
    pos = cf._to_np(qat_model.get_layer("pos_enc").pos)          # (1, T, D)
    ip = export.get_layer("input_proj")
    bv = getattr(ip, "_bias", None)
    if bv is None:
        bv = ip.bias
    bv.assign((cf._to_np(bv) + pos[0]).astype("float32"))

    # OPTIONAL fixed-point bias snap (the binary export's bq_wide f=16, applied to
    # values). Default OFF — both configurations were measured 2026-08-24 (n=128):
    #   raw biases : GATE1 corr 1.000000 (export IS the trained function),
    #                GATE2 corr 0.9998325, max|Δ| 0.173828125, hls4ml qinterval
    #                warns 'not a multiple of delta' on the fp32 bias constants;
    #   snap 2^-16 : GATE1 corr 0.999802 (the ≤2^-17 bias delta flips RND_CONV
    #                ties on the post-einsum lattice), GATE2 corr 0.9998360,
    #                max|Δ| 0.173828125 — byte-identical residue, warnings gone.
    # The snap buys nothing measurable on GATE2 (the residue is per-site 1-LSB
    # quantization semantics, localized by trace: softmax output-table LSB +
    # fused producer-output rounding — not the bias representation) and costs
    # GATE1 exactness, so raw biases ship.
    snap = {"applied": bool(snap_biases),
            "grid": "2^-16 (binary-export bq_wide f=16 parity)",
            "n_biases": 0, "max_abs_delta": 0.0}
    if snap_biases:
        for ly in export.layers:
            b_var = getattr(ly, "_bias", None)
            if b_var is None:
                b_var = getattr(ly, "bias", None)
            if b_var is None:
                continue
            b = cf._to_np(b_var).astype(np.float64)
            bs = np.round(b * 65536.0) / 65536.0
            snap["max_abs_delta"] = max(snap["max_abs_delta"],
                                        float(np.abs(bs - b).max()))
            snap["n_biases"] += 1
            b_var.assign(bs.astype("float32"))
    return export, n_ported, float(np.abs(pos).max()), snap


def weight_port_exactness(qat_model, export_model):
    """max|qkernel(export) − qkernel(QAT)| over every weighted layer — must be 0.0:
    the kernels and their kq quantizer state are copied variables, not re-derived."""
    worst, n = 0.0, 0
    for ly in export_model.layers:
        if not hasattr(ly, "qkernel"):
            continue
        d = np.abs(cf._to_np(ly.qkernel) - cf._to_np(qat_model.get_layer(ly.name).qkernel))
        worst = max(worst, float(d.max()))
        n += 1
    return worst, n


# --------------------------------------------------------------------------- #
# firmware read-back (structural evidence for the baseline's DSP story)        #
# --------------------------------------------------------------------------- #
def audit_w8a8_firmware(out_dir: str):
    """Parse the emitted firmware: how are the 8-bit weights typed, which arrays feed
    which layers, and how many einsum_dense/dense cores exist. Verbatim quotes only."""
    fw = os.path.join(out_dir, "firmware")
    defines = open(os.path.join(fw, "defines.h")).read()
    params = open(os.path.join(fw, "parameters.h")).read()
    cpp = open(os.path.join(fw, "myproject.cpp")).read()

    m = re.search(r"typedef\s+(.+?)\s+model_default_t;", defines)
    weight_typedefs = {layer: typ for typ, layer in
                       re.findall(r"typedef\s+(ap_u?fixed<[^>]*>)\s+(\w+)_weight_t;", defines)}
    arrays = {name: {"type": t.strip(), "n": int(n)} for t, n, name in
              re.findall(r"load_weights_from_txt<([^,]+),\s*(\d+)>\((\w+),", cpp)}

    calls, n_einsum_dense, n_dense = {}, 0, 0
    for kind, args, layer in re.findall(
            r"nnet::(einsum_dense|dense\w*)<[^>]*>\(([^)]*)\);\s*//\s*(\w+)", cpp):
        warr = [a.strip() for a in args.split(",") if re.fullmatch(r"w\d+", a.strip())]
        rec = {"core": kind}
        if warr:
            rec["weight_array"] = warr[0]
            if warr[0] in arrays:
                rec.update(arrays[warr[0]])
        calls[layer] = rec
        if kind == "einsum_dense":
            n_einsum_dense += 1
        else:
            n_dense += 1

    return {
        "model_default_t": m.group(1) if m else None,
        "weight_typedefs": weight_typedefs,
        "n_weight_typedefs": len(weight_typedefs),
        "config_weight_t_kinds": sorted(set(re.findall(r"typedef\s+(\w+)\s+weight_t;", params))),
        "n_model_default_weight_t": params.count("typedef model_default_t weight_t;"),
        "weighted_cores": calls,
        "n_einsum_dense": n_einsum_dense,
        "n_dense": n_dense,
    }


# --------------------------------------------------------------------------- #
# driver                                                                       #
# --------------------------------------------------------------------------- #
def run_convert_w8a8(seed: int, *, checkpoint=None, tag=None, rf=1,
                     strategy="Latency", n_gate=4096, n_csim=128, n_ebops=4096,
                     data_dir=None, store_root=None, run_dir=None,
                     config_path=None, input_std_path=None, fix_relu_parse=False,
                     snap_biases=False):
    cfg_path = config_path or os.path.join(_HERE, "configs", "pre_conference-n8-w8a8.json")
    cfg = load_config(cfg_path)
    if cfg["quant"]["weight"] != "int8_absmax":
        raise SystemExit(f"{cfg['name']}: convert_w8a8 only converts int8_absmax "
                         f"configs (got quant.weight={cfg['quant']['weight']!r}); the "
                         "binary variants stay on convert_binary.py")
    h = cfg_hash(cfg)
    A = cfg["arch"]
    leaf = f"w8a8-s{seed}" + (f"-{tag}" if tag else "")
    data_dir = data_dir or os.path.join(PROJECT_ROOT, "data", "val")
    store_root = store_root or os.path.join(PROJECT_ROOT, "results", "synthesis")
    run_dir = run_dir or os.path.join(store_root, "runs", h, leaf)
    os.makedirs(run_dir, exist_ok=True)

    kp = os.path.abspath(checkpoint or os.path.join(
        PROJECT_ROOT, "results", "predictions", "pre_conference", "n8", "_ckpt_dl",
        f"w8a8-s{seed}", "model_best.keras"))
    if not os.path.isfile(kp):
        raise SystemExit(f"checkpoint not found: {kp}")
    mp = os.path.join(os.path.dirname(kp), "train_meta.json")
    meta = json.load(open(mp)) if os.path.isfile(mp) else {}
    if input_std_path is None:
        cand = os.path.join(os.path.dirname(kp), "input_std.json")
        input_std_path = cand if os.path.isfile(cand) else None

    print(f"=== convert_w8a8 {leaf}  cfg={cfg['name']} [{h}] rf={rf} "
          f"strategy={strategy} ===", flush=True)

    qat_model = cf.load_qat_model(kp)
    print(f"[load] {os.path.basename(kp)}  params={qat_model.count_params():,}", flush=True)

    Xg, yg = cf._load_jets(data_dir, A["n_part"], n_gate, features=A.get("features"))
    _std = None
    if input_std_path:
        from bnhgq2.data import apply_input_std
        _std = json.load(open(input_std_path))
        Xg = apply_input_std(Xg, _std["mu"], _std["sigma"])
        print(f"[data] input_std applied from {input_std_path} (input-standardized model contract)", flush=True)
    print(f"[data] {len(Xg)} real jets from {os.path.relpath(data_dir, PROJECT_ROOT)}",
          flush=True)

    # ---- export: same graph minus pos_enc, PE folded into input_proj bias ----
    export_model, n_ported, pos_max, bias_snap = build_w8a8_export(
        cfg, qat_model, seed, snap_biases=snap_biases)
    w_exact, n_weighted = weight_port_exactness(qat_model, export_model)
    snap_msg = (f"{bias_snap['n_biases']} biases snapped to 2^-16 "
                f"(max|Δ|={bias_snap['max_abs_delta']:.2e})"
                if bias_snap["applied"] else "biases raw (snap OFF, the shipping config)")
    print(f"[export] {export_model.count_params():,} params; {n_ported} layers ported; "
          f"pos table folded into input_proj bias (max|pos|={pos_max:.4f}); {snap_msg}; "
          f"weight |Δ| vs QAT = {w_exact:.3e} over {n_weighted} weighted layers "
          f"(0 => ported, not re-derived)", flush=True)
    if w_exact != 0.0:
        raise SystemExit("STOP: ported effective weights differ from the QAT forward")

    # ---- GATE 1 ----
    g1 = cf.gate1(qat_model, export_model, Xg)
    g1["weight_port_max_abs_diff"] = w_exact
    g1_thr = 0.997
    g1_pass = g1["corr_scores"] >= g1_thr
    print(f"[GATE1] export vs QAT: corr_scores={g1['corr_scores']:.6f} "
          f"corr_logits={g1['corr_logits']:.6f} argmax={g1['argmax_agreement']:.4f} "
          f"pass={g1_pass}", flush=True)
    g1_sanity = 0.9999 if not snap_biases else 0.999
    if g1["corr_scores"] < g1_sanity:
        raise SystemExit(f"STOP: GATE1 below {g1_sanity} — raw-bias export has NO "
                         "approximation (expected 1.000000); the snap variant only "
                         "sub-LSB tie flips (expected ~0.9998). Anything lower is a "
                         "porting bug. Not writing artifacts.")

    export_verify = {
        "config": cfg["name"], "config_hash": h, "variant": "w8a8", "seed": seed,
        "tag": tag, "checkpoint": (os.path.relpath(kp, PROJECT_ROOT)
                                   if kp.startswith(PROJECT_ROOT) else kp),
        "train_meta": meta,
        "mechanism": ("direct HGQ2 QAT graph (int8_absmax weights, trained KBI act "
                      "grids): no β restoration — the export is the trained model "
                      "rebuilt WITHOUT the AddPositional layer "
                      "(qat.build_qat_model with_pos_enc=False), all variables copied "
                      "per layer, the trained (T,D) pos table folded into input_proj's "
                      "bias_axes='td' bias (the build.py PE fold)"),
        "pos_fold": {"max_abs_pos": pos_max, "layers_ported": n_ported,
                     "n_weighted_layers": n_weighted},
        "bias_snap": bias_snap,
        "input_std": (os.path.relpath(input_std_path, PROJECT_ROOT)
                      if input_std_path and input_std_path.startswith(PROJECT_ROOT)
                      else input_std_path),
        "gate1": g1, "gate1_pass": bool(g1_pass), "gate1_threshold": g1_thr,
        "gate1_policy": ("direct QAT graph, no β story — threshold 0.997 per the binary "
                         "bar. Raw biases (default): the export IS the trained function "
                         "up to bias+pos float reassociation, expected corr 1.000000. "
                         "With --snap-biases the ≤2^-17 bias delta flips RND_CONV ties "
                         "on the post-einsum lattice (measured 0.999802). Below the "
                         "sanity bar the driver aborts as a porting bug."),
    }
    cf._store(run_dir, "export_verify.json", export_verify)

    # ---- convert + GATE 2 (C-sim) ----
    from bnhgq2.convert import convert, package_hls_project
    cf.patch_resource_einsum_check()
    if fix_relu_parse:
        cf.patch_relu_parse()
        print("[relu] plain-relu parse restored (ThresholdedReLU(0) defect bypassed)",
              flush=True)
    out = os.path.join(run_dir, f"hls_prj_rf{rf}")
    csim_X = Xg[:n_csim]
    keras_ref = cf.predict(export_model, csim_X)
    relu_fixed = {"n": 0}

    def _post_parse(hm):
        relu_fixed["n"] = cf.fix_relu_saturation(hm)

    hm, report = convert(export_model, cfg, out, rf=rf, strategy=strategy,
                         csim_X=csim_X, keras_ref=keras_ref, post_parse=_post_parse)
    tar = package_hls_project(out, out + ".tar.gz")
    cs = report.get("csim", {})
    g2_pass = cs.get("corr", 0.0) >= 0.997
    print(f"[GATE2] hls4ml C-sim vs export: corr={cs.get('corr')} "
          f"max|Δ|={cs.get('max_abs_diff')} bit_exact={cs.get('bit_exact')} "
          f"pass={g2_pass}", flush=True)

    # extended characterization: C-sim over the FULL gate set (n_gate jets) — turns
    # the not-bit-exact residue into a measured attribution cost, not a caveat.
    y_ext_k = cf.predict(export_model, Xg)
    y_ext_h = np.asarray(hm.predict(np.ascontiguousarray(Xg.astype(np.float32))))
    y_ext_h = y_ext_h.reshape(y_ext_k.shape)
    d_ext = np.abs(y_ext_h - y_ext_k)
    s_k, s_h = cf._softmax(y_ext_k), cf._softmax(y_ext_h)
    csim_ext = {
        "n": int(len(Xg)),
        "corr_logits": float(np.corrcoef(y_ext_h.ravel(), y_ext_k.ravel())[0, 1]),
        "corr_scores": float(np.corrcoef(s_h.ravel(), s_k.ravel())[0, 1]),
        "max_abs_diff_logits": float(d_ext.max()),
        "mean_abs_diff_logits": float(d_ext.mean()),
        "argmax_agreement": float(np.mean(s_h.argmax(1) == s_k.argmax(1))),
    }
    # paired macro-OvR AUC on the SAME jets (evaluate_roc convention: per-class sklearn
    # roc_auc_score on softmax scores, macro = unweighted mean). The paired delta is
    # the attribution cost in the metric that matters; NOT a quotable AUC (n=4096
    # val jets, not the 260k ROC-test set).
    from sklearn.metrics import roc_auc_score
    auc_k = [float(roc_auc_score(yg[:, c], s_k[:, c])) for c in range(s_k.shape[1])]
    auc_h = [float(roc_auc_score(yg[:, c], s_h[:, c])) for c in range(s_h.shape[1])]
    csim_ext["paired_macro_ovr_auc"] = {
        "export_keras": float(np.mean(auc_k)), "hls_csim": float(np.mean(auc_h)),
        "delta_csim_minus_export": float(np.mean(auc_h) - np.mean(auc_k)),
        "per_class_export": auc_k, "per_class_csim": auc_h,
        "note": ("paired, same 4096 data/val jets — quantifies the not-bit-exact "
                 "residue in AUC terms; NOT a headline AUC (wrong split/size)"),
    }
    print(f"[GATE2+] extended C-sim n={csim_ext['n']}: "
          f"corr_scores={csim_ext['corr_scores']:.6f} "
          f"argmax_agreement={csim_ext['argmax_agreement']:.4f} "
          f"max|Δ|logits={csim_ext['max_abs_diff_logits']:.4g} "
          f"paired ΔmacroAUC={csim_ext['paired_macro_ovr_auc']['delta_csim_minus_export']:+.6f}",
          flush=True)

    audit = audit_w8a8_firmware(out)
    print(f"[firmware] einsum_dense cores={audit['n_einsum_dense']} "
          f"dense cores={audit['n_dense']} weight typedefs={audit['n_weight_typedefs']} "
          f"(model_default_t={audit['model_default_t']})", flush=True)

    csim_verify = {
        "config": cfg["name"], "config_hash": h, "variant": "w8a8", "seed": seed,
        "tag": tag, "rf": rf, "strategy": strategy,
        "backend": report.get("backend"),
        "macos_local_csim": platform.system() == "Darwin",
        "csim": cs, "gate2_pass": bool(g2_pass), "gate2_threshold": 0.997,
        "csim_extended": csim_ext,
        "bit_exactness_localization": {
            "summary": ("NOT bit-exact, unlike the binary comparator — the binary "
                        "path's bit-exactness is a property of ±1 arithmetic, not of "
                        "the pipeline. The residue is per-site 1-LSB quantization "
                        "semantics on grids the binary export never carries into "
                        "hls4ml; no saturation wraps, no lost grids."),
            "method": "per-layer hls4ml trace vs keras export, n=128 (2026-08-24)",
            "first_surviving_divergences": {
                "bit_block_0_attn_softmax": ("max|Δ| 0.000976562 = exactly 2^-10, one "
                                             "LSB of the ufixed<10,1> attention grid; "
                                             "the QAT softmax exp-input grid is SIGNED "
                                             "(_static_act(10,6)) — a shape the binary "
                                             "export's unsigned build.py grids never "
                                             "ship"),
                "bit_block_0_attn_Wo": "max|Δ| 15*2^-16 ≈ 2.3e-4 onto the residual bus",
            },
            "propagation": ("upstream producer-output roundings wash out at the stream "
                            "re-quantizers (scores maxD=0); the surviving LSBs "
                            "accumulate along the residual stream to max|Δ| 0.174 at "
                            "logits of scale O(10)"),
            "snap_experiment": ("2^-16 bias snap changed GATE2 by <1e-5 in corr and "
                                "0 in max|Δ| (0.173828125 both) while dropping GATE1 "
                                "from 1.000000 to 0.999802 — biases are NOT the "
                                "residue source; raw biases ship"),
        },
        "relu_sat_fix": (f"n={relu_fixed['n']} patched — n=0 is CORRECT here, not a "
                         "silent failure: BitExact fused the downstream trained SAT "
                         "grids into the relu output types "
                         "(ufixed<7,i,RND_CONV,SAT>), so nothing needed repair"),
        "relu_parse_fix": bool(fix_relu_parse),
        "widen_accum": False,
        "widen_accum_note": ("deliberately OFF: accumulator widening is the binary "
                             "DSP-0 trick; this baseline exists to measure the real "
                             "8b*8b DSP mapping"),
        "bias_typing_note": ("QAT biases are dummy-quantized fp32 (qat._dummy) and ship "
                             "raw (snap OFF): hls4ml stores them on model_default "
                             "fixed<24,12> (qinterval warns 'not a multiple of delta' — "
                             "measured harmless: the snap experiment above shows the "
                             "bias representation does not move GATE2)"),
    }
    cf._store(run_dir, "csim_verify.json", csim_verify)

    convert_rec = {
        "config_hash": h, "variant": "w8a8", "seed": seed, "tag": tag,
        "output_dir": os.path.relpath(out, PROJECT_ROOT),
        "tarball": os.path.relpath(tar, PROJECT_ROOT),
        "rf": rf, "strategy": strategy, "weight_mode": "int8_absmax",
        "part": cfg["hls"].get("part"), "clock_ns": cfg["hls"].get("clock_ns"),
        "io": cfg["hls"].get("io"),
        "firmware_audit": audit,
        "dsp_story": ("8-bit weights x 8-bit activations: the weighted-core multiplies "
                      "are real 8bx8b products and are EXPECTED to map to DSP48 at "
                      "csynth — that is the point of this baseline. No DSP count is "
                      "claimed here; HLS synthesis measures it."),
        "synthesis_command": "vitis_hls -f build_prj.tcl",
    }
    cf._store(run_dir, "convert.json", convert_rec)

    # ---- EBOPs LAST (trace_minmax after the gates, never before) ----
    from bnhgq2.ebops_calc import compute_ebops
    Xe, _ = cf._load_jets(data_dir, A["n_part"], n_ebops, features=A.get("features"))
    if _std is not None:
        from bnhgq2.data import apply_input_std
        Xe = apply_input_std(Xe, _std["mu"], _std["sigma"])
    eb = compute_ebops(export_model, Xe)
    eb.update({"config": cfg["name"], "config_hash": h, "variant": "w8a8", "seed": seed,
               "convention": "HGQ2_native_trace_minmax",
               "order_note": "computed AFTER conversion+gates (deviation from "
                             "convert_binary's step order; trace_minmax must not touch "
                             "quantizer state before the gates)"})
    cf._store(run_dir, "ebops.json", eb)
    print(f"[EBOPs] total = {eb['total']:,}", flush=True)

    tar_mb = os.path.getsize(tar) / 1e6
    print(f"\n[done] {leaf}: GATE1={'PASS' if g1_pass else 'CHECK'} "
          f"GATE2={'PASS' if g2_pass else 'CHECK'}  EBOPs={eb['total']:,}\n"
          f"       results -> {os.path.relpath(run_dir, PROJECT_ROOT)}\n"
          f"       tarball -> {os.path.relpath(tar, PROJECT_ROOT)} ({tar_mb:.1f} MB) "
          f"[NOT shipped]", flush=True)
    return {"gate1": g1, "gate1_pass": g1_pass, "gate2": cs, "gate2_pass": g2_pass,
            "ebops": eb["total"], "run_dir": run_dir, "tarball": tar}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--checkpoint", default=None,
                    help="local model_best.keras (default: the results/predictions/pre_conference/n8 "
                         "w8a8-s<seed> checkpoint)")
    ap.add_argument("--config", default=None,
                    help="config JSON (default configs/pre_conference-n8-w8a8.json)")
    ap.add_argument("--tag", default=None, help="results leaf suffix, e.g. 'pre_conference_n8'")
    ap.add_argument("--rf", type=int, default=1)
    ap.add_argument("--strategy", default="Latency",
                    help="MUST be Latency for the full model (hls4ml 1.3.0 EinsumDense "
                         "codegen is Latency-only)")
    ap.add_argument("--n-gate", type=int, default=4096)
    ap.add_argument("--n-csim", type=int, default=128)
    ap.add_argument("--n-ebops", type=int, default=4096)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--run-dir", default=None)
    ap.add_argument("--store-root", default=None)
    ap.add_argument("--input-std", default=None,
                    help="input_std.json (default: the checkpoint's sibling file)")
    ap.add_argument("--fix-relu-parse", action="store_true",
                    help="opt-in hls4ml ThresholdedReLU(0) parse-defect bypass "
                         "(OFF by default to match the recorded binary rf1 comparator)")
    ap.add_argument("--snap-biases", action="store_true",
                    help="opt-in 2^-16 bias snap (bq_wide parity). Measured 2026-08-24: "
                         "buys nothing on GATE2 (residue identical) and costs GATE1 "
                         "exactness (1.000000 -> 0.999802) — raw biases ship by default")
    a = ap.parse_args()
    run_convert_w8a8(a.seed, checkpoint=a.checkpoint, tag=a.tag, rf=a.rf,
                     strategy=a.strategy, n_gate=a.n_gate, n_csim=a.n_csim,
                     n_ebops=a.n_ebops, data_dir=a.data_dir, run_dir=a.run_dir,
                     store_root=a.store_root, config_path=a.config,
                     input_std_path=a.input_std, fix_relu_parse=a.fix_relu_parse,
                     snap_biases=a.snap_biases)


if __name__ == "__main__":
    main()
