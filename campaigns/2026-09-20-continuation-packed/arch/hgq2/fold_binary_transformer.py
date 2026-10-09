#!/usr/bin/env python3
'Fold binary weight scales into the exported transformer graph and verify numerical agreement.'
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
import traceback

os.environ.setdefault("KERAS_BACKEND", "tensorflow")

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import convert_binary as cf  # noqa: E402  (the proven export/gate chain — reused, not modified)
from bnhgq2.config import load_config, cfg_hash, PROJECT_ROOT  # noqa: E402
from probe_pf_dataflow import (  # noqa: E402  (PF-PROBE mechanism; the EinsumDense fold
    audit_pragmas,               #  is generalised locally in v2 — fold_einsum_dense —
    convert_dataflow,            #  so token_fold_einsum_dense is no longer imported)
)

GATE1_POLICY_BAR = 0.997  # norm-free policy
GATE2_BAR = 0.997


# --------------------------------------------------------------------------- #
# v2 fold mechanism: EinsumDense generalised to pf>=1, plus the Softmax fold   #
# --------------------------------------------------------------------------- #
def fold_einsum_dense(hm, pf):
    """token_fold_einsum_dense generalised: pf on every per-token EinsumDense node
    (n_free_data > 1), config template re-run per node (write() does not re-apply).
    pf must divide the token axis or the last unroll body is ragged — refuse."""
    from hls4ml.backends.vivado.passes.einsum_dense import EinsumDenseConfigTemplate

    tmpl = EinsumDenseConfigTemplate()
    folded = {}
    for node in hm.get_layers():
        if node.class_name != "EinsumDense":
            continue
        l0 = int(node.attributes["n_free_data"])
        if l0 <= 1:
            continue
        if l0 % pf:
            raise ValueError(f"pf={pf} does not divide token axis n_free_data={l0} "
                             f"on {node.name}")
        pf_before = int(node.attributes["parallelization_factor"])
        node.attributes["parallelization_factor"] = pf
        tmpl.transform(hm, node)
        folded[node.name] = {"n_free_data": l0, "pf_before": pf_before, "pf_after": pf,
                             "n_contract": int(node.attributes["n_contract"]),
                             "n_free_kernel": int(node.attributes["n_free_kernel"])}
    return folded


def fold_softmax(hm, pf):
    """The v2 fix, part (a): pf on every multidim Softmax node (n_outer > 1) + template
    re-run, so the emitted softmax_config carries pf instead of n_outer.  Part (b) —
    making the n_outer UNROLL actually honour it — is patch_softmax_unroll below."""
    from hls4ml.backends.vivado.passes.core_templates import SoftmaxConfigTemplate

    tmpl = SoftmaxConfigTemplate()
    folded = {}
    for node in hm.get_layers():
        if node.class_name != "Softmax":
            continue
        n_outer = int(node.attributes.get("n_outer", 1) or 1)
        if n_outer <= 1:
            continue  # head softmax: plain path, never instantiates softmax_multidim
        if n_outer % pf:
            raise ValueError(f"pf_softmax={pf} does not divide n_outer={n_outer} "
                             f"on {node.name}")
        pf_before = int(node.attributes.get("parallelization_factor", -1) or -1)
        node.attributes["parallelization_factor"] = pf
        tmpl.transform(hm, node)
        folded[node.name] = {"n_outer": n_outer, "pf_before": pf_before, "pf_after": pf}
    return folded


_SMX_LOOP = "    for (signed i = 0; i < CONFIG_T::n_outer; i++) {\n        #pragma HLS UNROLL\n"
_SMX_LOOP_PATCHED = ("    for (signed i = 0; i < CONFIG_T::n_outer; i++) {\n"
                     "        #pragma HLS UNROLL factor = CONFIG_T::parallelization_factor\n")


def patch_softmax_unroll(out_dir):
    """The v2 fix, part (b): make softmax_multidim's n_outer loop factor-bound in the
    PROJECT-LOCAL header (run after hm.write(); the venv copy is never touched).
    Pragma-only — C semantics identical, so GATE B must still show Δ = 0.  Only the
    two attention softmaxes instantiate softmax_multidim in this graph (head softmax
    has n_outer = 1), and both get an explicit pf, so the template constant is always
    defined where the pragma is instantiated."""
    hpath = os.path.join(out_dir, "firmware", "nnet_utils", "nnet_activation.h")
    src = open(hpath).read()
    marker = "void softmax_multidim"
    at = src.find(marker)
    if at < 0:
        raise RuntimeError(f"softmax_multidim not found in {hpath}")
    n = src.count(_SMX_LOOP, at)
    if n != 1:
        raise RuntimeError(f"expected exactly 1 n_outer UNROLL site after softmax_multidim "
                           f"in {hpath}, found {n} — header layout changed, refusing to patch")
    patched = src[:at] + src[at:].replace(_SMX_LOOP, _SMX_LOOP_PATCHED, 1)
    with open(hpath, "w") as f:
        f.write(patched)
    return {"file": os.path.relpath(hpath, out_dir),
            "patched_pragma": _SMX_LOOP_PATCHED.strip().splitlines()[-1].strip()}

# --------------------------------------------------------------------------- #
# the articles: everything read from the baseline run dir, nothing guessed     #
# --------------------------------------------------------------------------- #
ARTICLES = {
    # n8: the article of record — the only whole-model rollup that exists (STATUS §2.3).
    "n8": {
        "config": "configs/pre_conference-n8-w1a8.json",
        "checkpoint": "results/predictions/pre_conference/n8/_ckpt_dl/w1a8-s3/model_best.keras",
        "baseline_run_dir": "results/synthesis/runs/38a20c62/w1a8-s3-pre_conference_n8",
        "variant": "w1a8",
        "seed": 3,
        "beta_mode": "fx8",   # the pre-registered rung
        "rf": 1,              # matched to the reference build
    },
    # n16: attempted only after n8 succeeds.  Its RF = 1 whole-model run OOM-killed at
    # 112.5 GB of 125 GB (§3.1); folding is the only untried lever at that scale.  A folded
    # n16 point does NOT fill the n8<->n16 RF = 1 comparison gap and must not be labelled
    # as though it does.  Note the fx8 GATE1 margin at n16 is only +0.0004 (§3.3).
    # n8-sm4i0 (Job softmax precision, 2026-08-24): the shipped trained-grid arm — the pre-conference n8 W1A8 recipe with
    # quant.softmax_out_bits=4 / softmax_out_i=0 (the grid of the fitting characterization build),
    # seed 3, exported 2026-08-24 (GATE1 0.998052 vs its own checkpoint, GATE2 bit-exact).
    "n8-sm4i0": {
        "config": "configs/post_conference_softmax-sm4i0-n8-w1a8.json",
        "checkpoint": "outputs/models/cache/post_conference_softmax-sm4i0-n8-w1a8-s3/model_best.keras",
        "baseline_run_dir": "results/synthesis/runs/ba72a91a/w1a8-s3-softmax_precision-sm4i0",
        "variant": "w1a8",
        "seed": 3,
        "beta_mode": "fx8",
        "rf": 1,
    },
    "n16": {
        "config": "configs/pre_conference-n16-w1a8.json",
        "checkpoint": "results/predictions/pre_conference/n16/_ckpt_dl/w1a8-s1/model_best.keras",
        "baseline_run_dir": "results/synthesis/runs/2ae656b6/w1a8-s1-pre_conference_n16",
        "variant": "w1a8",
        "seed": 1,
        "beta_mode": "fx8",
        "rf": 1,
    },
}


def _abs(p):
    return p if os.path.isabs(p) else os.path.join(PROJECT_ROOT, p)


def _rel(p):
    return os.path.relpath(p, PROJECT_ROOT) if str(p).startswith(PROJECT_ROOT) else p


def read_baseline(run_dir):
    """The stored gate results of the unfolded build — GATE B's reference."""
    ev = json.load(open(os.path.join(run_dir, "export_verify.json")))
    cv_path = os.path.join(run_dir, "csim_verify.json")
    cv = json.load(open(cv_path)) if os.path.isfile(cv_path) else {}
    return {
        "run_dir": _rel(run_dir),
        "gate1_corr_scores": ev["gate1"]["corr_scores"],
        "gate1_argmax_agreement": ev["gate1"]["argmax_agreement"],
        "gate1_beta_mode": ev["gate1"].get("beta_mode"),
        "gate2_max_abs_diff": cv.get("csim", {}).get("max_abs_diff"),
        "gate2_bit_exact": cv.get("csim", {}).get("bit_exact"),
        "written": ev.get("written"),
    }


# --------------------------------------------------------------------------- #
# driver                                                                       #
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--article", default="n8", choices=sorted(ARTICLES),
                    help="which already-synthesised pre-conference article to fold (default n8)")
    ap.add_argument("--pf", type=int, default=1,
                    help="parallelization_factor on the per-token EinsumDense layers "
                         "(1 = maximum fold, the token axis stays fully rolled)")
    ap.add_argument("--pf-softmax", type=int, default=None,
                    help="parallelization_factor on the multidim Softmax nodes "
                         "(default: match --pf). v2: leaving softmax unrolled under "
                         "DATAFLOW is what wedged the pf1df run (log 2026-08-11)")
    ap.add_argument("--n-gate", type=int, default=4096,
                    help="gate/calibration jets — MUST match the baseline build (4096), "
                         "since Xg[:2048] sizes the stream ranges")
    ap.add_argument("--n-csim", type=int, default=128)
    ap.add_argument("--gate1-tol", type=float, default=1e-9,
                    help="max allowed |GATE1 - baseline GATE1|. A scheduling change must "
                         "move nothing; the default is float-identity in practice")
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--tag", default=None,
                    help="results leaf suffix (default pf<PF>df)")
    a = ap.parse_args()

    art = ARTICLES[a.article]
    cfg_path = _abs(os.path.join(_HERE, art["config"]))
    cfg = load_config(cfg_path)
    h = cfg_hash(cfg)
    A = cfg["arch"]
    norm_free = str(A.get("norm", "subln")).lower() == "none"
    baseline_dir = _abs(art["baseline_run_dir"])
    pf_smx = a.pf_softmax if a.pf_softmax is not None else a.pf
    # v2 tags are pf<PF>sm<PFS>df — deliberately distinct from the wedged pf1df leaf,
    # whose record (incl. the wedge diagnostics tarball) must not be clobbered.
    tag = a.tag or f"pf{a.pf}sm{pf_smx}df"
    run_dir = baseline_dir + "-" + tag
    os.makedirs(run_dir, exist_ok=True)

    # 4L (Wq/Wk/Wv/Wo) + 2L (fc1/fc2) + 1 (input_proj) — 13 at L = 2, matching the
    # "13 einsum_dense layers" of §3.1.
    expected_folded = 4 * A["n_layers"] + 2 * A["n_layers"] + 1
    # one attention softmax per block; the head softmax has n_outer = 1 and is untouched
    expected_softmax = A["n_layers"]

    stage = "baseline"
    manifest = {
        "driver": "fold_binary_transformer.py",
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "question": "does PipelineStyle=dataflow + parallelization_factor=%d actually fold "
                    "this design, and what does the folded point cost in silicon?" % a.pf,
        "article": a.article,
        "config": cfg["name"],
        "config_hash": h,
        "variant": art["variant"],
        "seed": art["seed"],
        "beta_mode": art["beta_mode"],
        "intervention": {
            "pipeline_style": "dataflow",
            "parallelization_factor": a.pf,
            "parallelization_factor_softmax": pf_smx,
            "target_layers": "EinsumDense with n_free_data > 1 AND Softmax with n_outer > 1",
            "expected_folded": expected_folded,
            "expected_softmax": expected_softmax,
            "softmax_header_patch": "project-local nnet_activation.h: softmax_multidim "
                                    "n_outer UNROLL -> factor = parallelization_factor",
            "rationale": "STATUS-2026-08-08 §3.1: the top-level `#pragma HLS PIPELINE` "
                         "force-unrolls every loop beneath it, which is why RF and PF were "
                         "both inert. dataflow removes that region. v2 (log 2026-08-11): "
                         "the pf1df wedge was the 2 Softmax nodes left at pf=n_outer under "
                         "DATAFLOW — 32 process clones each re-triggering the softmax "
                         "inline/partition cycle; roll them with everything else.",
        },
        "labelling": "FOLDED, DEPLOYABLE-CLASS POINT. Answers a different question from the "
                     "RF=1 reference (latency ~ sum over layers, interval set by the slowest "
                     "process). MUST NOT be tabulated against the RF=1 whole-model figures "
                     "(STATUS §2.3, §3.2). Report the dataflow interval as found; do not "
                     "substitute the RF=1 II=1.",
        "gates": {
            "A": "emitted firmware: top-level PIPELINE==0, DATAFLOW>=1, pf accounted on ALL "
                 f"pf lines ({expected_folded} EinsumDense at pf={a.pf} + {expected_softmax} "
                 f"Softmax at pf={pf_smx}, nothing else), softmax header patch present",
            "B": f"GATE1 reproduces the baseline to {a.gate1_tol:g}; GATE2 bit-exact",
        },
        "status": "INCOMPLETE",
    }

    def bail(exc, why=None):
        manifest["status"] = why or ("KILL: failure during stage '%s'" % stage)
        if exc is not None:
            manifest["error"] = {"stage": stage, "type": type(exc).__name__,
                                 "message": str(exc), "traceback": traceback.format_exc()}
        mpath = os.path.join(run_dir, "fold_manifest.json")
        with open(mpath, "w") as f:
            json.dump(manifest, f, indent=2)
        print(f"\n[KILL] {manifest['status']}\n       manifest -> {_rel(mpath)}", flush=True)
        sys.exit(1)

    try:
        # ---- (0) the baseline this build must reproduce
        base = read_baseline(baseline_dir)
        manifest["baseline"] = base
        if base["gate1_beta_mode"] != art["beta_mode"]:
            bail(None, f"KILL: baseline was built at beta_mode={base['gate1_beta_mode']!r}, "
                       f"not {art['beta_mode']!r} — GATE B would compare unlike builds")
        print(f"=== fold {a.article} {art['variant']}-s{art['seed']} cfg={cfg['name']} [{h}] "
              f"pf={a.pf} beta={art['beta_mode']} rf={art['rf']} ===\n"
              f"[baseline] {base['run_dir']}  GATE1={base['gate1_corr_scores']:.16f}  "
              f"GATE2 bit_exact={base['gate2_bit_exact']}", flush=True)

        # ---- (1) checkpoint + jets, exactly as the baseline build sourced them
        stage = "load"
        kp = _abs(art["checkpoint"])
        if not os.path.isfile(kp):
            bail(None, f"KILL: checkpoint not found at {_rel(kp)} — refusing to fold a "
                       "different article than the one already synthesised")
        qat_model = cf.load_qat_model(kp)
        print(f"[load] {_rel(kp)}  params={qat_model.count_params():,}", flush=True)

        data_dir = a.data_dir or os.path.join(PROJECT_ROOT, "data", "val")
        Xg, _ = cf._load_jets(data_dir, A["n_part"], a.n_gate, features=A.get("features"))
        std_path = None
        if A.get("input_std"):
            # arch.input_std is part of this article's contract — gating on unstandardized
            # jets would silently change GATE1 and break the GATE B comparison.
            std_path = os.path.join(os.path.dirname(kp), "input_std.json")
            if not os.path.isfile(std_path):
                bail(None, f"KILL: arch.input_std=true but {_rel(std_path)} is missing")
            from bnhgq2.data import apply_input_std
            _std = json.load(open(std_path))
            Xg = apply_input_std(Xg, _std["mu"], _std["sigma"])
            print(f"[data] input_std applied from {_rel(std_path)}", flush=True)
        manifest["source"] = {"checkpoint": _rel(kp), "input_std": _rel(std_path) if std_path else None,
                              "data_dir": _rel(data_dir), "n_gate": a.n_gate}
        print(f"[data] {len(Xg)} real jets from {_rel(data_dir)}", flush=True)

        # ---- (2) export — the convert_binary v5 chain, unmodified
        stage = "export"
        binz, pe, names = cf.qat_binz_pe(qat_model, cfg)
        calib = cf.read_qat_act_ibits(qat_model, names)
        calib.update(cf.qat_stream_ranges(qat_model, cfg, binz, Xg[:2048]))
        export_model = cf.build_export(cfg, binz, calib, pe, beta_mode=art["beta_mode"],
                                       qat_model=qat_model, attn_grids="build_default")
        w_exact = cf.weight_export_exactness(qat_model, binz)
        manifest["export"] = {"norm_free": norm_free, "params": int(export_model.count_params()),
                              "weight_export_max_abs_diff": w_exact}
        print(f"[export] {export_model.count_params():,} params; norm_free={norm_free}; "
              f"weight |Δ| vs QAT forward = {w_exact:.3e}", flush=True)

        # ---- (3) GATE 1 — policy bar AND the baseline-reproduction bar
        stage = "gate1"
        g1 = cf.gate1(qat_model, export_model, Xg)
        d1 = abs(g1["corr_scores"] - base["gate1_corr_scores"])
        g1_policy = g1["corr_scores"] >= GATE1_POLICY_BAR
        g1_repro = d1 <= a.gate1_tol
        manifest["gate1"] = {
            "corr_scores": g1["corr_scores"], "corr_logits": g1["corr_logits"],
            "argmax_agreement": g1["argmax_agreement"],
            "baseline_corr_scores": base["gate1_corr_scores"],
            "delta_vs_baseline": d1, "tol": a.gate1_tol,
            "policy_bar": GATE1_POLICY_BAR, "policy_pass": bool(g1_policy),
            "reproduces_baseline": bool(g1_repro),
            "policy": "norm-free 0.997 (numerical-agreement criterion); reproduction bar is this "
                      "driver's own — a scheduling change must not move numerics",
        }
        print(f"[GATE1] corr_scores={g1['corr_scores']:.16f}  Δ vs baseline={d1:.3e}  "
              f"policy_pass={g1_policy}  reproduces_baseline={g1_repro}", flush=True)
        if not (g1_policy and g1_repro):
            bail(None, "KILL (GATE B): GATE1 did not reproduce the baseline "
                       f"(Δ={d1:.3e} > tol={a.gate1_tol:g}) — the build changed more than "
                       "scheduling; do not ship")

        # ---- (4) convert with PipelineStyle=dataflow + pf fold, then GATE 2
        stage = "convert+csim"
        cf.patch_resource_einsum_check()
        out = os.path.join(run_dir, f"hls_prj_{tag}")
        import shutil
        shutil.rmtree(out, ignore_errors=True)
        csim_X = Xg[:a.n_csim]
        keras_ref = cf.predict(export_model, csim_X)

        smx_folded = {}

        def post_parse(hm):
            cf.fix_relu_saturation(hm)               # same repair as the baseline build
            ed = fold_einsum_dense(hm, a.pf)         # pf AND re-run the config template
            smx_folded.update(fold_softmax(hm, pf_smx))  # v2: roll the softmaxes too
            return ed

        hm, report, folded = convert_dataflow(export_model, cfg, out, art["rf"],
                                              csim_X, keras_ref, post_parse)
        manifest["folded_layers"] = folded
        manifest["n_folded"] = len(folded)
        manifest["folded_softmax"] = smx_folded
        print(f"[fold] pf={a.pf} on {len(folded)} per-token EinsumDense layers: "
              + ", ".join(sorted(folded)), flush=True)
        print(f"[fold] pf={pf_smx} on {len(smx_folded)} multidim Softmax nodes: "
              + ", ".join(f"{k}(n_outer={v['n_outer']})" for k, v in sorted(smx_folded.items())),
              flush=True)
        if len(smx_folded) != expected_softmax:
            bail(None, f"KILL: expected {expected_softmax} multidim Softmax nodes, folded "
                       f"{len(smx_folded)} — graph shape differs from the wedge diagnosis")

        # v2 part (b): the header patch that makes the softmax pf real (pragma-only,
        # AFTER write(); GATE2 above already ran and pragmas are invisible to g++)
        stage = "patch-softmax-header"
        manifest["softmax_header_patch"] = patch_softmax_unroll(out)
        print(f"[patch] {manifest['softmax_header_patch']['file']}: "
              f"{manifest['softmax_header_patch']['patched_pragma']}", flush=True)

        # ---- (5) GATE A — the emitted firmware is the arbiter, not the intent
        stage = "gateA"
        aud = audit_pragmas(out)
        manifest["pragma_audit"] = aud
        pc = aud["pragma_counts"]
        hist = aud["pf_value_histogram"]
        # v2: the histogram must account for EVERY pf line — 13 einsum_dense at a.pf plus
        # 2 softmax at pf_smx, and NOTHING else (a leftover pf=n_outer softmax is exactly
        # the wedge). When a.pf == pf_smx the two merge into one bucket.
        expected_hist = {}
        expected_hist[a.pf] = expected_hist.get(a.pf, 0) + expected_folded
        expected_hist[pf_smx] = expected_hist.get(pf_smx, 0) + expected_softmax
        hist_ok = {int(k): int(v) for k, v in hist.items()} == expected_hist
        smx_patch_ok = _SMX_LOOP_PATCHED in open(
            os.path.join(out, "firmware", "nnet_utils", "nnet_activation.h")).read()
        gateA = {
            "top_pipeline_zero": pc["PIPELINE"] == 0,
            "dataflow_present": pc["DATAFLOW"] >= 1,
            "pf_histogram": hist,
            "pf_histogram_expected": expected_hist,
            "pf_histogram_ok": hist_ok,
            "softmax_header_patch_ok": smx_patch_ok,
        }
        gateA["pass"] = all((gateA["top_pipeline_zero"], gateA["dataflow_present"],
                             hist_ok, smx_patch_ok))
        manifest["gateA"] = gateA
        print(f"[GATE A] myproject.cpp PIPELINE={pc['PIPELINE']} DATAFLOW={pc['DATAFLOW']} "
              f"UNROLL={pc['UNROLL']}; parameters.h pf histogram={hist} "
              f"(expected {expected_hist}); softmax header patch={smx_patch_ok}; "
              f"pass={gateA['pass']}", flush=True)
        if not gateA["pass"]:
            bail(None, "KILL (GATE A): the emitted firmware is not fully folded — "
                       f"PIPELINE={pc['PIPELINE']} (want 0), DATAFLOW={pc['DATAFLOW']} "
                       f"(want >=1), pf histogram {hist} (want {expected_hist}), softmax "
                       f"header patch present={smx_patch_ok}. A partial fold under "
                       "DATAFLOW is the 08-09 wedge; do not ship.")

        # ---- (6) GATE 2 — C-sim must stay bit-exact
        stage = "gate2"
        cs = report.get("csim", {})
        g2_bit_exact = bool(cs.get("bit_exact"))
        g2_policy = cs.get("corr", 0.0) >= GATE2_BAR
        manifest["gate2"] = {
            "csim": cs, "threshold": GATE2_BAR, "policy_pass": bool(g2_policy),
            "bit_exact": g2_bit_exact,
            "baseline_bit_exact": base["gate2_bit_exact"],
            "macos_local_csim": platform.system() == "Darwin",
            "reference": "export model predictions (as convert_binary)",
        }
        print(f"[GATE2] C-sim vs export: corr={cs.get('corr')} "
              f"max|Δ|={cs.get('max_abs_diff')} bit_exact={g2_bit_exact}", flush=True)
        if not (g2_policy and g2_bit_exact):
            bail(None, "KILL (GATE B): GATE2 is not bit-exact "
                       f"(corr={cs.get('corr')}, max|Δ|={cs.get('max_abs_diff')}); the "
                       "baseline was bit-exact and a scheduling change cannot alter this")

        # ---- (7) pack for the synthesis host (ship + csynth happen elsewhere, on purpose)
        stage = "pack"
        from bnhgq2.convert import package_hls_project
        tar = package_hls_project(out, out + ".tar.gz")
        manifest["output_dir"] = _rel(out)
        manifest["tarball"] = _rel(tar)
        manifest["synthesis_command"] = "vitis_hls -f build_prj.tcl"
        manifest["status"] = "EMITTED — GATE A PASS, GATE B PASS — ready for HLS synthesis"

        # lineage in the same shape convert_binary writes, so the leaf reads like any other
        lineage = {
            "written": manifest["written"], "config_hash": h, "variant": art["variant"],
            "seed": art["seed"], "tag": tag, "output_dir": _rel(out), "tarball": _rel(tar),
            "rf": art["rf"], "strategy": "Latency", "beta_mode": art["beta_mode"],
            "pipeline_style": "dataflow", "parallelization_factor": a.pf,
            "parallelization_factor_softmax": pf_smx,
            "n_folded_einsum_dense": len(folded),
            "n_folded_softmax": len(smx_folded),
            "softmax_header_patch": manifest.get("softmax_header_patch"),
            "part": cfg["hls"].get("part"), "clock_ns": cfg["hls"].get("clock_ns"),
            "parent_run_dir": base["run_dir"],
            "export_version": "v5-beta-restore",
            "labelling": manifest["labelling"],
        }
        with open(os.path.join(run_dir, "convert_lineage.json"), "w") as f:
            json.dump(lineage, f, indent=2)
        mpath = os.path.join(run_dir, "fold_manifest.json")
        with open(mpath, "w") as f:
            json.dump(manifest, f, indent=2)

        print(f"\n[done] folded {len(folded)} einsum denses; both gates pass\n"
              f"       manifest -> {_rel(mpath)}\n"
              f"       tarball  -> {_rel(tar)}\n"
              f"       synthesis -> {manifest['synthesis_command']}", flush=True)

    except SystemExit:
        raise
    except Exception as exc:  # noqa: BLE001 — a KILL band IS a result; record it
        bail(exc)


if __name__ == "__main__":
    main()
