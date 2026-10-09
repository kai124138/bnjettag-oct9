#!/usr/bin/env python3
"""ROC-test AUC of the EXPORTED (synthesized) graph for the five shipped articles.

Today the accuracy tables quote the TRAINED (QAT) checkpoints' ROC-test AUC; the
exported hardware graphs (the networks actually pushed through hls4ml/csynth) only
carry a 4,096-jet correlation gate (GATE1). This driver measures the exported
graph's macro one-vs-rest AUC on the FULL held-out 260,000-jet split, per article.

Method :
  * load the QAT checkpoint whole via convert_binary.load_qat_model (train.py contract);
  * rebuild the SHIPPED export byte-identically: qat_binz_pe -> read_qat_act_ibits ->
    qat_stream_ranges on the first 2,048 of the 4,096 linspace gate jets ->
    build_export(beta_mode='fx8', qat_model=...)  — no force flags, no ladder builds;
  * prove the rebuild IS the shipped graph by reproducing the stored GATE1
    corr_scores (results/synthesis/runs/<hash>/<leaf>/export_verify.json) on the
    same 4,096 jets;
  * evaluate QAT and export on all 260,000 jets (article's own input_std.json,
    reference experiment contract), softmax in float64 (evaluate_roc.softmax64), macro-OvR +
    per-class AUC (evaluate_roc.macro_ovr_auc);
  * sanity chain: y byte-equal to the article's roc-results npz; QAT AUC recomputed
    here vs the npz-recomputed trained AUC (tolerance ~1e-4, CPU/GPU tail).

Outputs (results/pre-conference/): export_roc_auc.json + export_roc_auc.md, rewritten after
every article so a crash never loses finished work.

NEVER conflate: trained_auc_ref and export_auc are both ROC-test (n=260,000),
never validation AUC. delta = export_auc - trained_auc_ref.
"""
from __future__ import annotations

import gc
import json
import os
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from bnhgq2.config import load_config, cfg_hash, PROJECT_ROOT          # noqa: E402
from bnhgq2.data import CLASS_NICE, load_eval_set, apply_input_std     # noqa: E402
from convert_binary import (load_qat_model, qat_binz_pe,                # noqa: E402
                           read_qat_act_ibits, qat_stream_ranges,
                           build_export, gate1)
from evaluate_roc import macro_ovr_auc, softmax64                        # noqa: E402

BETA_MODE = "fx8"          # the shipped encoding rung
N_GATE = 4096              # convert_binary default --n-gate
EXPECT_N = 260000
DATA_DIR = os.path.join(PROJECT_ROOT, "data", "val")
OUT_DIR = os.path.join(PROJECT_ROOT, "results", "pre_conference")
OUT_JSON = os.path.join(OUT_DIR, "export_roc_auc.json")
OUT_MD = os.path.join(OUT_DIR, "export_roc_auc.md")

_R = PROJECT_ROOT
ARTICLES = [
    dict(article="n8-w1a8-s3", n_part=8, config_hash="38a20c62",
         ckpt=f"{_R}/results/predictions/pre_conference/n8/_ckpt_dl/w1a8-s3/model_best.keras",
         config=f"{_R}/code/hgq2/configs/pre_conference-n8-w1a8.json",
         export_verify=f"{_R}/results/synthesis/runs/38a20c62/w1a8-s3-pre_conference_n8/export_verify.json",
         npz=f"{_R}/results/predictions/pre_conference/n8/W1A8-s3.npz",
         roc_auc_md="results/predictions/pre_conference/n8/roc_auc.md", roc_auc_md_value=0.8724),
    dict(article="n8-w1a6-s3", n_part=8, config_hash="794e925f",
         ckpt=f"{_R}/outputs/models/cache/pre_conference-n8-w1a6-s3/model_best.keras",
         config=f"{_R}/code/hgq2/configs/pre_conference-n8-w1a6.json",
         export_verify=f"{_R}/results/synthesis/runs/794e925f/w1a6-s3/export_verify.json",
         npz=f"{_R}/results/predictions/pre_conference/n8/W1A6-s3.npz",
         roc_auc_md="results/predictions/pre_conference/n8/roc_auc.md", roc_auc_md_value=0.8701),
    dict(article="n8-w1a4-s3", n_part=8, config_hash="5f839ab5",
         ckpt=f"{_R}/outputs/models/cache/pre_conference-n8-w1a4-s3/model_best.keras",
         config=f"{_R}/code/hgq2/configs/pre_conference-n8-w1a4.json",
         export_verify=f"{_R}/results/synthesis/runs/5f839ab5/w1a4-s3/export_verify.json",
         npz=f"{_R}/results/predictions/pre_conference/n8/W1A4-s3.npz",
         roc_auc_md="results/predictions/pre_conference/n8/roc_auc.md", roc_auc_md_value=0.8533),
    dict(article="n16-w1a8-s1", n_part=16, config_hash="2ae656b6",
         ckpt=f"{_R}/results/predictions/pre_conference/n16/_ckpt_dl/w1a8-s1/model_best.keras",
         config=f"{_R}/code/hgq2/configs/pre_conference-n16-w1a8.json",
         export_verify=f"{_R}/results/synthesis/runs/2ae656b6/w1a8-s1-pre_conference_n16/export_verify.json",
         npz=f"{_R}/results/predictions/pre_conference/n16/W1A8-s1.npz",
         roc_auc_md="results/predictions/pre_conference/n16/roc_auc.md", roc_auc_md_value=0.8959),
    dict(article="n8-softmax_precision-sm4i0-s3", n_part=8, config_hash="ba72a91a",
         ckpt=f"{_R}/outputs/models/cache/post_conference_softmax-sm4i0-n8-w1a8-s3/model_best.keras",
         config=f"{_R}/code/hgq2/configs/post_conference_softmax-sm4i0-n8-w1a8.json",
         export_verify=f"{_R}/results/synthesis/runs/ba72a91a/w1a8-s3-softmax_precision-sm4i0/export_verify.json",
         npz=f"{_R}/results/predictions/softmax_precision/sm4i0/W1A8-s3.npz",
         roc_auc_md="results/predictions/softmax_precision/sm4i0/roc_auc.md", roc_auc_md_value=0.8723),
]


def _f(x):
    return None if x is None else float(x)


def _rel(p):
    return os.path.relpath(p, PROJECT_ROOT)


def predict_batches(model, X, batch=4096):
    out = []
    for i in range(0, len(X), batch):
        out.append(np.asarray(model(X[i:i + batch], training=False)))
    return np.concatenate(out)


def scores_from_logits(raw):
    """eval_one's contract: heads emit LOGITS -> softmax64 once; guard the simplex."""
    rowsum = raw.astype(np.float64).sum(axis=1)
    if raw.min() >= -1e-6 and np.allclose(rowsum, 1.0, atol=1e-3):
        sys.stderr.write("[warn] output already a probability simplex — using as-is\n")
        return raw.astype(np.float64)
    return softmax64(raw)


_DATA_CACHE = {}


def full_eval_set(n_part, features):
    key = (n_part, tuple(features))
    if key not in _DATA_CACHE:
        X, y = load_eval_set(DATA_DIR, n_part=n_part, features=list(features))
        if len(X) != EXPECT_N:
            raise AssertionError(f"held-out split n={len(X)} != {EXPECT_N}")
        if y.shape[1] != 5:
            raise AssertionError(f"labels have {y.shape[1]} columns, expected 5")
        _DATA_CACHE[key] = (X, y)
    return _DATA_CACHE[key]


def run_article(a):
    t0 = time.time()
    rec = {"article": a["article"], "ckpt": _rel(a["ckpt"]), "config": _rel(a["config"]),
           "config_hash": a["config_hash"], "beta_mode": BETA_MODE}
    if not os.path.isfile(a["ckpt"]):
        rec["error"] = f"checkpoint not found: {a['ckpt']}"
        return rec

    cfg = load_config(a["config"])
    h = cfg_hash(cfg)
    assert h == a["config_hash"], f"{a['article']}: cfg hash {h} != expected {a['config_hash']}"
    A = cfg["arch"]

    # --- data (raw, un-standardized; cached per n_part) + article's own input_std ---
    X_raw, y = full_eval_set(A["n_part"], A["features"])
    std = json.load(open(os.path.join(os.path.dirname(a["ckpt"]), "input_std.json")))
    rec["input_std"] = _rel(os.path.join(os.path.dirname(a["ckpt"]), "input_std.json"))

    # --- QAT model + shipped export rebuild (mirrors run_convert_binary exactly) ---
    qat = load_qat_model(a["ckpt"])
    print(f"[{a['article']}] loaded QAT ({qat.count_params():,} params)", flush=True)
    idx = np.linspace(0, len(X_raw) - 1, min(N_GATE, len(X_raw))).astype(np.int64)
    Xg = apply_input_std(X_raw[idx].astype(np.float32), std["mu"], std["sigma"])
    binz, pe, names = qat_binz_pe(qat, cfg)
    calib = read_qat_act_ibits(qat, names)
    calib.update(qat_stream_ranges(qat, cfg, binz, Xg[:2048]))
    export = build_export(cfg, binz, calib, pe, beta_mode=BETA_MODE, qat_model=qat)

    # --- GATE1 reproduction: proves the rebuild IS the shipped graph ---
    g1 = gate1(qat, export, Xg)
    ev = json.load(open(a["export_verify"]))
    stored = ev["gate1"]
    d_corr = abs(g1["corr_scores"] - stored["corr_scores"])
    rec["gate1_stored"] = {"corr_scores": _f(stored["corr_scores"]),
                           "argmax_agreement": _f(stored["argmax_agreement"]),
                           "n": stored["n"], "beta_mode": stored.get("beta_mode"),
                           "source": _rel(a["export_verify"])}
    rec["gate1_reproduced"] = {k: _f(g1[k]) for k in
                               ("corr_scores", "corr_logits", "argmax_agreement")}
    rec["gate1_reproduced"]["n"] = g1["n"]
    rec["gate1_repro_abs_delta_corr"] = _f(d_corr)
    rec["gate1_repro_exact"] = bool(d_corr < 1e-6)
    print(f"[{a['article']}] GATE1 repro corr_scores={g1['corr_scores']:.10f} "
          f"stored={stored['corr_scores']:.10f} |d|={d_corr:.2e} "
          f"exact={rec['gate1_repro_exact']}", flush=True)
    if not rec["gate1_repro_exact"]:
        print(f"[{a['article']}] WARNING: GATE1 not byte-reproduced — export may not "
              f"be the shipped graph; numbers below carry that caveat", flush=True)

    # --- full 260k eval ---
    Xs = apply_input_std(X_raw, std["mu"], std["sigma"])
    lq = predict_batches(qat, Xs)
    le = predict_batches(export, Xs).reshape(lq.shape)
    sq, se = scores_from_logits(lq), scores_from_logits(le)

    # sanity chain vs the article's stored ROC npz
    with np.load(a["npz"]) as z:
        y_npz, score_npz = z["y"], z["score"]
    rec["npz_ref"] = _rel(a["npz"])
    rec["npz_y_match"] = bool(np.array_equal(y.astype("float32"), y_npz))
    trained_ref, trained_per = macro_ovr_auc(y_npz, score_npz)
    qat_auc, qat_per = macro_ovr_auc(y, sq.astype("float32"))
    rec["trained_auc_ref"] = _f(trained_ref)          # recomputed from the stored npz
    rec["trained_auc_ref_md_4dp"] = a["roc_auc_md_value"]
    rec["trained_auc_ref_md_source"] = a["roc_auc_md"]
    rec["trained_md_consistent"] = bool(abs(round(trained_ref, 4) - a["roc_auc_md_value"]) < 5e-5)
    rec["qat_auc_recomputed_260k"] = _f(qat_auc)
    rec["qat_vs_npz_auc_abs_delta"] = _f(abs(qat_auc - trained_ref))

    exp_auc, exp_per = macro_ovr_auc(y, se.astype("float32"))
    rec["export_auc"] = _f(exp_auc)
    rec["delta"] = _f(exp_auc - trained_ref)          # export - trained (negative = cost)
    rec["per_class"] = {c: _f(v) for c, v in zip(CLASS_NICE, exp_per)}
    rec["per_class_trained_ref"] = {c: _f(v) for c, v in zip(CLASS_NICE, trained_per)}
    rec["corr_scores_260k"] = _f(np.corrcoef(se.ravel(), sq.ravel())[0, 1])
    rec["argmax_agreement_260k"] = _f(np.mean(se.argmax(1) == sq.argmax(1)))
    rec["n"] = int(len(y))
    rec["elapsed_s"] = round(time.time() - t0, 1)
    print(f"[{a['article']}] export AUC={exp_auc:.6f} trained(npz)={trained_ref:.6f} "
          f"delta={exp_auc - trained_ref:+.6f} corr260k={rec['corr_scores_260k']:.6f} "
          f"({rec['elapsed_s']}s)", flush=True)

    del qat, export, lq, le, sq, se, Xs, binz
    try:
        import keras
        keras.utils.clear_session()
    except Exception:
        pass
    gc.collect()
    return rec


def write_outputs(results):
    import numpy, keras, tensorflow
    payload = {
        "written": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "script": "code/hgq2/export_roc_eval.py",
        "method": ("shipped export rebuilt from checkpoint via convert_binary.build_export "
                   f"(beta_mode={BETA_MODE}, no force flags); GATE1 reproduced on the same "
                   f"{N_GATE} linspace jets as the arbiter; AUC = ROC-test macro OvR "
                   "(sklearn), softmax64, held-out data/val split"),
        "metric": "roc_test_auc_macro_ovr (NOT validation AUC)",
        "sign_convention": "delta = export_auc - trained_auc_ref (negative = export costs AUC)",
        "n_eval": EXPECT_N, "era": 2, "data_dir": _rel(DATA_DIR),
        "env": {"numpy": numpy.__version__, "keras": keras.__version__,
                "tensorflow": tensorflow.__version__,
                "python": sys.version.split()[0]},
        "articles": results,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT_JSON, "w") as f:
        json.dump(payload, f, indent=1)

    lines = [
        "# Exported-graph ROC-test AUC (the five synthesized articles)",
        "#",
        "# metric : ROC-test macro one-vs-rest AUC on the held-out val split (n=260,000)",
        "#          of the EXPORTED hardware graph (convert_binary.build_export, beta=fx8,",
        "#          the network actually synthesized) — NOT val AUC, NOT the QAT number",
        "# arbiter: stored GATE1 corr_scores reproduced on the same 4,096 linspace jets",
        "#          before each 260k eval (proves the rebuild is the shipped graph)",
        "# era    : 2  (NEVER compare to era-1 numbers)",
        f"# gen    : {time.strftime('%Y-%m-%d')} by code/hgq2/export_roc_eval.py -> export_roc_auc.json",
        "",
        "## Macro AUC: trained checkpoint vs exported graph",
        "",
        "| article | config [hash] | trained AUC (ROC-test) | export AUC | delta (export-trained) "
        "| corr(scores) 260k | argmax agree 260k | GATE1 stored / reproduced (4,096) | n |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {r['article']} | {r.get('config','?')} [{r.get('config_hash','?')}] "
                         f"| — | — | — | — | — | ERROR: {r['error']} | — |")
            continue
        g1s, g1r = r["gate1_stored"], r["gate1_reproduced"]
        exact = "exact" if r["gate1_repro_exact"] else f"|d|={r['gate1_repro_abs_delta_corr']:.1e}"
        lines.append(
            f"| {r['article']} | {os.path.basename(r['config']).replace('.json','')} "
            f"[{r['config_hash']}] | {r['trained_auc_ref']:.5f} | {r['export_auc']:.5f} "
            f"| {r['delta']:+.5f} | {r['corr_scores_260k']:.6f} "
            f"| {r['argmax_agreement_260k']:.4f} "
            f"| {g1s['corr_scores']:.6f} / {g1r['corr_scores']:.6f} ({exact}) | {r['n']} |")
    lines += ["", "## Per-class AUC of the exported graph", "",
              "| article | AUC(g) | AUC(q) | AUC(W) | AUC(Z) | AUC(t) | macro |",
              "|---|---|---|---|---|---|---|"]
    for r in results:
        if "error" in r:
            continue
        pc = r["per_class"]
        lines.append(f"| {r['article']} | " +
                     " | ".join(f"{pc[c]:.4f}" for c in CLASS_NICE) +
                     f" | **{r['export_auc']:.4f}** |")
    lines += ["", "## Provenance", ""]
    for r in results:
        if "error" in r:
            lines.append(f"- **{r['article']}**: ERROR — {r['error']}")
            continue
        lines.append(
            f"- **{r['article']}**: ckpt `{r['ckpt']}` · config `{r['config']}` "
            f"[{r['config_hash']}] · beta_mode {r['beta_mode']} · input_std `{r['input_std']}` "
            f"· trained ref recomputed from `{r['npz_ref']}` "
            f"(= {r['trained_auc_ref']:.5f}; roc_auc.md quotes {r['trained_auc_ref_md_4dp']:.4f}, "
            f"consistent={r['trained_md_consistent']}) · y-alignment vs npz: {r['npz_y_match']} "
            f"· QAT recompute |d| vs npz = {r['qat_vs_npz_auc_abs_delta']:.1e} "
            f"· GATE1 source `{r['gate1_stored']['source']}`")
    lines.append("")
    with open(OUT_MD, "w") as f:
        f.write("\n".join(lines))


def main():
    results = []
    for a in ARTICLES:
        print(f"=== {a['article']} ===", flush=True)
        try:
            rec = run_article(a)
        except Exception as e:
            import traceback
            traceback.print_exc()
            rec = {"article": a["article"], "ckpt": _rel(a["ckpt"]),
                   "config": _rel(a["config"]), "config_hash": a["config_hash"],
                   "beta_mode": BETA_MODE, "error": f"{type(e).__name__}: {e}"}
        results.append(rec)
        write_outputs(results)   # rewrite after EVERY article — crash-safe
    print(f"[done] {OUT_JSON}\n[done] {OUT_MD}", flush=True)


if __name__ == "__main__":
    main()
