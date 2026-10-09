#!/usr/bin/env python3
'Estimate seed variation and paired bootstrap uncertainty of macro one-vs-rest AUC.'
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ROC = os.path.join(REPO, "results", "predictions", "pre_conference")

N_SWEEP = [8, 16, 32, 64]
KEY = {"fp32": "FP32", "w8a8": "W8A8", "w1a8": "W1A8", "w1a6": "W1A6", "w1a4": "W1A4"}


def load_scores(n, variant, seed):
    f = os.path.join(ROC, f"n{n}", f"{KEY[variant]}-s{seed}.npz")
    d = np.load(f, allow_pickle=True)
    return d["y"], d["score"]


def macro_auc_fast(y, s, order_cache):
    """Macro OvR AUC via rank statistics (exact, no sklearn loop)."""
    aucs = []
    for c in range(y.shape[1]):
        sc = s[:, c]
        yc = y[:, c].astype(bool)
        r = np.empty(len(sc))
        o = np.argsort(sc, kind="stable")
        r[o] = np.arange(1, len(sc) + 1)
        # midranks for ties
        _, inv, cnt = np.unique(sc, return_inverse=True, return_counts=True)
        csum = np.cumsum(cnt)
        mid = (csum - (cnt - 1) / 2.0)
        r = mid[inv]
        n1 = yc.sum(); n0 = len(yc) - n1
        aucs.append((r[yc].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))
    return float(np.mean(aucs))


def paired_boot_gap(yA, sA, sB, n_boot, rng, block=None):
    """Bootstrap std of macroAUC(A) - macroAUC(B) over paired resamples."""
    n = len(yA)
    gaps = np.empty(n_boot)
    for b in range(n_boot):
        idx = rng.integers(0, n, n)
        gaps[b] = (macro_auc_fast(yA[idx], sA[idx], None)
                   - macro_auc_fast(yA[idx], sB[idx], None))
    return float(gaps.mean()), float(gaps.std(ddof=1))


def arm_aucs(n, variant):
    out = []
    for s in (1, 2, 3):
        y, sc = load_scores(n, variant, s)
        out.append(macro_auc_fast(y, sc, None))
    return out


def verdict(gap, sigma):
    r = abs(gap) / sigma if sigma > 0 else float("inf")
    return "RESOLVED" if r > 2 else ("TENTATIVE" if r > 1 else "UNRESOLVED")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--boot", type=int, default=200)
    ap.add_argument("--no-wandb", action="store_true")
    a = ap.parse_args()
    rng = np.random.default_rng(20260802)

    aucs = {(n, v): arm_aucs(n, v) for n in N_SWEEP for v in KEY}
    rows = []

    def compare(n, va, vb, label):
        A, B = np.array(aucs[(n, va)]), np.array(aucs[(n, vb)])
        gap = float(A.mean() - B.mean())
        seed_var = A.var(ddof=1) / 3 + B.var(ddof=1) / 3
        # paired bootstrap on seed-1 pair (test-set noise is model-pair specific
        # but stable across seeds; one pair suffices at n_boot=200)
        y, sA = load_scores(n, va, 1)
        _, sB = load_scores(n, vb, 1)
        _, boot_sd = paired_boot_gap(y, sA, sB, a.boot, rng)
        sigma = float(np.sqrt(seed_var + boot_sd ** 2))
        v = verdict(gap, sigma)
        rows.append({"n_part": n, "comparison": label, "gap": round(gap, 5),
                     "sigma_seed": round(float(np.sqrt(seed_var)), 5),
                     "sigma_boot": round(boot_sd, 5),
                     "sigma_total": round(sigma, 5), "verdict": v})
        print(f"[unc] n{n:<3d} {label:14s} gap={gap:+.5f} ± {sigma:.5f} "
              f"(seed {np.sqrt(seed_var):.5f}, boot {boot_sd:.5f})  {v}")

    for n in N_SWEEP:
        compare(n, "fp32", "w1a8", "fp32 - w1a8")   # Q1
        compare(n, "fp32", "w8a8", "fp32 - w8a8")   # Q2
        compare(n, "w1a8", "w1a6", "w1a8 - w1a6")   # Q3
        compare(n, "w1a8", "w1a4", "w1a8 - w1a4")   # Q3

    # Q4: binary seed-variance growth (n32+n64 pooled vs n8+n16 pooled)
    lo = np.concatenate([aucs[(8, "w1a8")], aucs[(16, "w1a8")]])
    hi = np.concatenate([aucs[(32, "w1a8")], aucs[(64, "w1a8")]])
    q4 = {"var_lo_n8n16": float(np.var(lo, ddof=1)),
          "var_hi_n32n64": float(np.var(hi, ddof=1)),
          "ratio": float(np.var(hi, ddof=1) / np.var(lo, ddof=1))}
    print(f"[unc] Q4 binary seed-variance ratio (n32/64 vs n8/16): {q4['ratio']:.1f}x")

    out = {"boot_replicates": a.boot, "rows": rows, "q4_instability": q4,
           "aucs_roc_test": {f"n{n}-{v}": aucs[(n, v)] for n, v in aucs}}
    store = os.path.join(REPO, "results", "pre_conference", "estimate_auc_uncertainty.json")
    os.makedirs(os.path.dirname(store), exist_ok=True)
    with open(store, "w") as f:
        json.dump(out, f, indent=1)
    md = os.path.join(REPO, "results", "pre_conference", "estimate_auc_uncertainty.md")
    with open(md, "w") as f:
        f.write("# pre-conference uncertainty pass (ROC-test macro AUC; seed spread + paired "
                f"bootstrap x{a.boot})\n\n| N | comparison | gap | σ_seed | σ_boot | "
                "σ_total | verdict |\n|---|---|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['n_part']} | {r['comparison']} | {r['gap']:+.5f} | "
                    f"{r['sigma_seed']:.5f} | {r['sigma_boot']:.5f} | "
                    f"{r['sigma_total']:.5f} | {r['verdict']} |\n")
        f.write(f"\nQ4 binary seed-variance ratio (n32/64 vs n8/16): "
                f"{q4['ratio']:.1f}x\n")
    print(f"[unc] wrote {store} + {md}")

    if not a.no_wandb:
        from bnhgq2 import wandb_util as wbu
        if wbu.wandb_enabled():
            import wandb
            run = wandb.init(**wbu.init_kwargs(
                name="pre_conference-uncertainty", job_type="eval",
                tags=["uncertainty", "roc-test"],
                config={"boot": a.boot, "n_seeds": 3}))
            for r in rows:
                run.summary[f"gap/{r['comparison']}/n{r['n_part']}"] = r["gap"]
                run.summary[f"verdict/{r['comparison']}/n{r['n_part']}"] = r["verdict"]
            run.summary["q4_variance_ratio"] = q4["ratio"]
            try:
                wbu.log_files_artifact(run, name="pre-conference-uncertainty", type="evaluation",
                                       files=[store, md], metadata=q4)
            except Exception as e:
                print(f"[wandb] artifact warn: {e}")
            wandb.finish()


if __name__ == "__main__":
    main()
