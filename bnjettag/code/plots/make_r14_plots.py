#!/usr/bin/env python3
"""R14 summary figures — everything loaded from verified stores, nothing hand-typed.

Sources:
  * ROC-test AUCs  — recomputed HERE from bnjettag/roc-results/r14/n<N>/*.npz (y, score),
    the same arrays verify-roc passed 60/60 on 2026-08-04.
  * EBOPs          — bnjettag/results/r14/ebops_r14.json (hgq2 trace_minmax).

Outputs (png 220 dpi + pdf): bnjettag/results/r14/figures/
  fig_r14_auc_vs_n        — ROC-test macro AUC vs N per arm, seed mean ± std
  fig_r14_pareto          — AUC vs EBOPs Pareto (quantized arms; fp32 has no EBOPs)
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import roc_auc_score

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ROC = os.path.join(REPO, "bnjettag", "roc-results", "r14")
FIG = os.path.join(REPO, "bnjettag", "results", "r14", "figures")
os.makedirs(FIG, exist_ok=True)

N_SWEEP = [8, 16, 32, 64]
# palette consistent with roc_final.py overlays (colorblind-safe, one color per arm)
COLORS = {"FP32": "#e87bd0", "W8A8": "#d2691e",
          "W1A8": "#56b4b0", "W1A6": "#e6a817", "W1A4": "#cf3bc4"}
ARMS = ["FP32", "W8A8", "W1A8", "W1A6", "W1A4"]

PROV = ("public HLS4ML LHC Jet 5-class | L1-realistic (N,3) inputs: pT, eta_rel, phi_rel | "
        "ROC-test macro-OvR AUC, n=260,000 | seed mean +/- sample std (3 seeds)")


# POSTER=1: poster variants — neutral titles (no campaign labels), jargon-free footer, larger type,
# written as fig_auc_vs_n_poster / fig_pareto_poster beside the originals (originals unchanged).
POSTER = bool(os.environ.get("POSTER"))
if POSTER:
    PROV = ("HLS4ML LHC jet dataset, 5 classes; per-constituent inputs pT, \u03b7rel, \u03c6rel; "
            "held-out macro one-vs-rest AUC, n = 260,000; mean \u00b1 s.d. over 3 seeds")
SUFFIX = "_poster" if POSTER else ""
FS = 1.25 if POSTER else 1.0
def load_aucs():
    """{(N, KEY): [auc x3]} recomputed from the npz arrays (never the tables)."""
    out = {}
    for n in N_SWEEP:
        for f in sorted(glob.glob(os.path.join(ROC, f"n{n}", "*.npz"))):
            d = np.load(f, allow_pickle=True)
            meta = json.loads(str(d["meta"]))
            per = [roc_auc_score(d["y"][:, c], d["score"][:, c]) for c in range(5)]
            out.setdefault((n, meta["key"]), []).append(float(np.mean(per)))
    return out


def fig_auc_vs_n(aucs):
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=220)
    for arm in ARMS:
        mu = [np.mean(aucs[(n, arm)]) for n in N_SWEEP]
        sd = [np.std(aucs[(n, arm)], ddof=1) for n in N_SWEEP]
        ax.errorbar(N_SWEEP, mu, yerr=sd, color=COLORS[arm], marker="o", ms=5,
                    lw=1.8, capsize=3, label=None)
        ax.annotate(arm, (N_SWEEP[-1] * 1.04, mu[-1]), color=COLORS[arm],
                    fontsize=11 * FS, fontweight="bold", va="center")
    ax.set_xscale("log", base=2)
    ax.set_xticks(N_SWEEP)
    ax.set_xticklabels([str(n) for n in N_SWEEP])
    ax.set_xlim(7, 92)
    ax.set_xlabel("Constituents per jet, N (top-N by $p_T$)", fontsize=12 * FS)
    ax.set_ylabel(("Held-out macro one-vs-rest AUC" if POSTER else "ROC-test macro-OvR AUC"), fontsize=12 * FS)
    ax.set_title("Held-out AUC vs constituent count, by precision" if POSTER else
                 "Round 14 — accuracy vs constituent count, by quantization arm", fontsize=12.5 * FS)
    ax.tick_params(labelsize=11 * FS); ax.grid(alpha=0.3)
    fig.text(0.5, 0.015, PROV, ha="center", fontsize=6.8 * FS, color="0.35")
    fig.tight_layout(rect=[0, 0.035, 1, 1])
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig_r14_auc_vs_n{SUFFIX}.{ext}"))
    plt.close(fig)
    print(f"[fig] fig_r14_auc_vs_n  <- roc-results/r14/n*/[*.npz]")


def fig_pareto(aucs):
    eb = json.load(open(os.path.join(REPO, "bnjettag", "results", "r14",
                                     "ebops_r14.json")))["models"]
    by = {}
    for row in eb.values():
        by.setdefault((row["n_part"], row["variant"].upper()), []).append(row["ebops"])
    fig, ax = plt.subplots(figsize=(7.5, 5.2), dpi=220)
    for arm in ["W8A8", "W1A8", "W1A6", "W1A4"]:
        xs = [np.mean(by[(n, arm)]) for n in N_SWEEP]
        ys = [np.mean(aucs[(n, arm)]) for n in N_SWEEP]
        sd = [np.std(aucs[(n, arm)], ddof=1) for n in N_SWEEP]
        ax.errorbar(xs, ys, yerr=sd, color=COLORS[arm], marker="o", ms=5, lw=1.6,
                    capsize=3)
        ax.annotate(arm, (xs[-1] * 1.1, ys[-1]), color=COLORS[arm], fontsize=11 * FS,
                    fontweight="bold", va="center")
        for n, x, y in zip(N_SWEEP, xs, ys):
            if arm == "W1A8":
                ax.annotate(f"N={n}", (x, y), textcoords="offset points",
                            xytext=(-6, 7), fontsize=8 * FS, color="0.3")
    ax.set_xscale("log")
    ax.set_xlabel("Estimated bit-operations per jet (EBOPs), mean over 3 seeds" if POSTER else "EBOPs (HGQ2 trace_minmax, mean over 3 seeds)", fontsize=12 * FS)
    ax.set_ylabel(("Held-out macro one-vs-rest AUC" if POSTER else "ROC-test macro-OvR AUC"), fontsize=12 * FS)
    ax.set_title("Held-out AUC vs estimated bit-operations per jet" if POSTER else
                 "Round 14 — accuracy vs estimated hardware cost (Pareto view)", fontsize=12.5 * FS)
    ax.tick_params(labelsize=11 * FS); ax.grid(alpha=0.3, which="both")
    fig.text(0.5, 0.015, ("Same dataset and metric as the AUC-vs-N figure; mean \u00b1 s.d. over 3 seeds. FP32 has no bit-operation count and is omitted." if POSTER else PROV + " | FP32 has no quantizers => no EBOPs point"),
             ha="center", fontsize=6.4 * FS, color="0.35")
    fig.tight_layout(rect=[0, 0.035, 1, 1])
    for ext in ("png", "pdf"):
        fig.savefig(os.path.join(FIG, f"fig_r14_pareto{SUFFIX}.{ext}"))
    plt.close(fig)
    print(f"[fig] fig_r14_pareto    <- ebops_r14.json + roc-results/r14/n*/[*.npz]")


if __name__ == "__main__":
    aucs = load_aucs()
    fig_auc_vs_n(aucs)
    fig_pareto(aucs)
    # print the seed-averaged table this figure encodes (for the record)
    for n in N_SWEEP:
        row = "  ".join(f"{arm}={np.mean(aucs[(n, arm)]):.4f}±{np.std(aucs[(n, arm)], ddof=1):.4f}"
                        for arm in ARMS)
        print(f"n{n:<3d} {row}")
