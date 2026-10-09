#!/usr/bin/env python3
"""Every number of the jet-pT sample-weighting study, recomputed from the stored arrays.

Reads <store>/{BASE,PTW5,PTWNC}-s{1..8}.npz (keys y, score, j_pt, meta; held-out split,
n = 260,000) and <store>/internal-val/*.npz (keys label, pred; each seed's own 20 %
validation split, n = 124,000). Writes <store>/summary.json and <store>/roc_auc.md.

Per model: macro one-vs-rest AUC and the five per-class AUCs; top-1 accuracy and per-class
recall; background rejection at fixed signal efficiency (per-class one-vs-rest 1/FPR at the
first threshold where TPR >= eps, macro over classes); macro AUC inside fixed jet-pT bins
whose edges are the held-out sextiles of jets[j_pt], rounded to 1 GeV.
Across seeds: mean and sample std (ddof=1) for AUC and accuracy, population std (ddof=0)
for rejection (the convention of the repository's rejection tables). Paired differences
against the unweighted arm, seed by seed: mean, standard error, 95 % t-interval (df = 7),
and the number of seeds in which the weighted arm is lower.

    pip install numpy scikit-learn
    python ptw_n8_metrics.py [store]
"""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

STORE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[3] / "roc-results" / "ptw-n8"
ARMS = ["BASE", "PTW5", "PTWNC"]
SEEDS = list(range(1, 9))
CLASSES = ["g", "q", "W", "Z", "t"]
EPS = (0.3, 0.5, 0.7)
N_PT_BINS = 6
T975_DF7 = 2.3646242510102993  # scipy.stats.t.ppf(0.975, 7)


def per_class_auc(y, s):
    return np.array([roc_auc_score(y[:, c], s[:, c]) for c in range(y.shape[1])])


def rejection(y, s, eps):
    out = []
    for c in range(y.shape[1]):
        fpr, tpr, _ = roc_curve(y[:, c], s[:, c])
        i = min(int(np.searchsorted(tpr, eps, side="left")), len(fpr) - 1)
        out.append(np.inf if fpr[i] == 0 else 1.0 / fpr[i])
    return float(np.mean(out))


def pt_edges(j_pt):
    q = np.quantile(j_pt.astype(np.float64), np.linspace(0, 1, N_PT_BINS + 1)[1:-1])
    return np.concatenate([[-np.inf], np.round(q), [np.inf]])


def load():
    runs = {}
    for a in ARMS:
        for s in SEEDS:
            d = np.load(STORE / f"{a}-s{s}.npz")
            v = np.load(STORE / "internal-val" / f"{a}-s{s}.npz")
            runs[(a, s)] = dict(y=d["y"], score=d["score"], j_pt=d["j_pt"],
                                vlabel=v["label"], vpred=v["pred"])
    return runs


def model_metrics(r, edges):
    y, s = r["y"], r["score"]
    lab, pred = y.argmax(1), s.argmax(1)
    pc = per_class_auc(y, s)
    m = {"auc": float(pc.mean()), "auc_per_class": pc.tolist(),
         "acc": float((lab == pred).mean()),
         "recall_per_class": [float((pred[lab == c] == c).mean()) for c in range(5)],
         "val_acc": float((r["vlabel"] == r["vpred"]).mean()),
         "rej": {str(e): rejection(y, s, e) for e in EPS}}
    b = np.digitize(r["j_pt"], edges[1:-1], right=False)
    m["auc_ptbin"] = [float(per_class_auc(y[b == k], s[b == k]).mean()) for k in range(N_PT_BINS)]
    m["auc_ptbin_per_class"] = [per_class_auc(y[b == k], s[b == k]).tolist() for k in range(N_PT_BINS)]
    m["auc_ptbin_mean"] = float(np.mean(m["auc_ptbin"]))
    m["acc_ptbin"] = [float((lab[b == k] == pred[b == k]).mean()) for k in range(N_PT_BINS)]
    return m


def spread(v, ddof=1):
    v = np.asarray(v, dtype=np.float64)
    return {"mean": float(v.mean()), "sd": float(v.std(ddof=ddof)), "values": v.tolist()}


def paired(a, b):
    d = np.asarray(a, np.float64) - np.asarray(b, np.float64)
    se = d.std(ddof=1) / np.sqrt(len(d))
    return {"mean": float(d.mean()), "se": float(se),
            "ci95": [float(d.mean() - T975_DF7 * se), float(d.mean() + T975_DF7 * se)],
            "n_lower": int((d < 0).sum()), "n": int(len(d)), "values": d.tolist()}


def main():
    runs = load()
    ref = runs[("BASE", 1)]
    for k, r in runs.items():
        assert r["y"].shape == (260000, 5) and np.array_equal(r["y"], ref["y"]), k
        assert np.array_equal(r["j_pt"], ref["j_pt"]), k
        assert len(r["vlabel"]) == 124000, k
    edges = pt_edges(ref["j_pt"])
    b = np.digitize(ref["j_pt"], edges[1:-1])
    lab = ref["y"].argmax(1)
    bins = [{"lo_GeV": None if not np.isfinite(edges[k]) else float(edges[k]),
             "hi_GeV": None if not np.isfinite(edges[k + 1]) else float(edges[k + 1]),
             "n": int((b == k).sum()),
             "n_per_class": [int(((b == k) & (lab == c)).sum()) for c in range(5)]}
            for k in range(N_PT_BINS)]

    M = {k: model_metrics(r, edges) for k, r in runs.items()}

    def col(a, f):
        return [f(M[(a, s)]) for s in SEEDS]

    fields = {"auc": lambda m: m["auc"], "acc": lambda m: m["acc"], "val_acc": lambda m: m["val_acc"]}
    for c in range(5):
        fields[f"auc_{CLASSES[c]}"] = (lambda c: lambda m: m["auc_per_class"][c])(c)
        fields[f"recall_{CLASSES[c]}"] = (lambda c: lambda m: m["recall_per_class"][c])(c)
    for k in range(N_PT_BINS):
        fields[f"auc_ptbin{k + 1}"] = (lambda k: lambda m: m["auc_ptbin"][k])(k)
        fields[f"acc_ptbin{k + 1}"] = (lambda k: lambda m: m["acc_ptbin"][k])(k)
    fields["auc_ptbin_mean"] = lambda m: m["auc_ptbin_mean"]
    rejf = {f"rej_{e}": (lambda e: lambda m: m["rej"][str(e)])(e) for e in EPS}

    arms = {a: {**{n: spread(col(a, f)) for n, f in fields.items()},
                **{n: spread(col(a, f), ddof=0) for n, f in rejf.items()}} for a in ARMS}
    deltas = {}
    for a, bref in (("PTW5", "BASE"), ("PTWNC", "BASE"), ("PTW5", "PTWNC")):
        deltas[f"{a}-{bref}"] = {n: paired(col(a, f), col(bref, f))
                                 for n, f in {**fields, **rejf}.items()}
    best_acc = max(M, key=lambda k: M[k]["acc"])
    best_auc = max(M, key=lambda k: M[k]["auc"])
    summary = {
        "study": "ptw-n8-20260925: jet-pT sample weighting, N=8, l1x3 inputs (pt, etarel, phirel), W1A8",
        "metric": "held-out macro one-vs-rest AUC etc. on the 260,000-jet val archive; val_acc on each seed's internal 20 % split (124,000 jets)",
        "conventions": "AUC/accuracy spread = sample sd (ddof=1); rejection spread = population sd (ddof=0); paired CI = t(0.975, df=7)",
        "generated": datetime.date.today().isoformat(),
        "pt_bins": bins, "arms": arms, "paired": deltas,
        "per_model": {f"{a}-s{s}": M[(a, s)] for a, s in M},
        "best_by_heldout_acc": {"model": f"{best_acc[0]}-s{best_acc[1]}", "acc": M[best_acc]["acc"], "auc": M[best_acc]["auc"], "val_acc": M[best_acc]["val_acc"]},
        "best_by_heldout_auc": {"model": f"{best_auc[0]}-s{best_auc[1]}", "acc": M[best_auc]["acc"], "auc": M[best_auc]["auc"], "val_acc": M[best_auc]["val_acc"]},
    }
    (STORE / "summary.json").write_text(json.dumps(summary, indent=1) + "\n")
    write_table(summary, runs)
    print((STORE / "roc_auc.md").read_text())


def f4(x):
    return f"{x:.4f}"


def ms(d, p=4):
    return f"{d['mean']:.{p}f} ± {d['sd']:.{p}f}"


def dl(d, p=4):
    lo, hi = d["ci95"]
    return f"{d['mean']:+.{p}f} ± {d['se']:.{p}f} [{lo:+.{p}f}, {hi:+.{p}f}] {d['n_lower']}/{d['n']}"


def write_table(S, runs):
    A = S["arms"]
    L = ["# Jet-pT sample weighting (l1x3, N=8, W1A8) - ROC-test AUC and accuracy",
         "#",
         "# metric : ROC-test macro one-vs-rest AUC on the held-out val archive",
         "#          (sklearn roc_auc_score per class; macro = unweighted mean) - NOT val AUC",
         "# n_eval : 260000 jets    (comparable only at matched input set l1x3 and N=8)",
         "# arms   : BASE unweighted; PTW5 per-class jet-pT weights, cap 5; PTWNC same, no cap",
         "# source : recomputed from roc-results/ptw-n8/*.npz (y, score, j_pt) by ptw_n8_metrics.py",
         "# val_acc: top-1 accuracy on each seed's internal 20 % validation split (internal-val/*.npz)",
         f"# gen    : {S['generated']}",
         "",
         "## Per-seed", "",
         "| run | seed | " + " | ".join(f"AUC({c})" for c in CLASSES) + " | macro | acc | val acc | n |",
         "|" + "---|" * 11]
    for a in ARMS:
        for s in SEEDS:
            m = S["per_model"][f"{a}-s{s}"]
            L.append(f"| {a}-s{s} | {s} | " + " | ".join(f4(v) for v in m["auc_per_class"])
                     + f" | **{f4(m['auc'])}** | {f4(m['acc'])} | {f4(m['val_acc'])} | 260000 |")
    L += ["", "## Seed-averaged (mean ± sample std, 8 seeds)", "",
          "| arm | " + " | ".join(f"AUC({c})" for c in CLASSES) + " | macro | acc | val acc |",
          "|" + "---|" * 9]
    for a in ARMS:
        L.append(f"| {a} | " + " | ".join(ms(A[a][f'auc_{c}']) for c in CLASSES)
                 + f" | **{ms(A[a]['auc'])}** | {ms(A[a]['acc'])} | {ms(A[a]['val_acc'])} |")
    L += ["", "## Per-class accuracy (recall), mean ± sample std", "",
          "| arm | " + " | ".join(CLASSES) + " |", "|" + "---|" * 6]
    for a in ARMS:
        L.append(f"| {a} | " + " | ".join(ms(A[a][f'recall_{c}']) for c in CLASSES) + " |")
    L += ["", "## Background rejection, macro over classes (mean ± population std)", "",
          "| arm | " + " | ".join(f"eps_S={e}" for e in EPS) + " |", "|" + "---|" * 4]
    for a in ARMS:
        L.append(f"| {a} | " + " | ".join(ms(A[a][f'rej_{e}'], 1) for e in EPS) + " |")
    L += ["", "## Held-out macro AUC in jet-pT bins (edges = held-out sextiles, rounded to 1 GeV)", "",
          "| bin | pT range (GeV) | n | " + " | ".join(ARMS) + " |", "|" + "---|" * 6]
    for k, b in enumerate(S["pt_bins"]):
        lo = "min" if b["lo_GeV"] is None else f"{b['lo_GeV']:.0f}"
        hi = "max" if b["hi_GeV"] is None else f"{b['hi_GeV']:.0f}"
        L.append(f"| {k + 1} | {lo}-{hi} | {b['n']} | " + " | ".join(ms(A[a][f'auc_ptbin{k + 1}']) for a in ARMS) + " |")
    L.append("| mean of the six bins | | | " + " | ".join(ms(A[a]["auc_ptbin_mean"]) for a in ARMS) + " |")
    L += ["", "Per-class jet counts per bin (g, q, W, Z, t): "
          + "; ".join(f"bin {k + 1}: " + ", ".join(str(n) for n in b["n_per_class"]) for k, b in enumerate(S["pt_bins"])), ""]
    L += ["## Paired differences (mean ± SE [95 % t-interval, df 7], seeds lower)", "",
          "| quantity | PTW5 - BASE | PTWNC - BASE | PTW5 - PTWNC |", "|---|---|---|---|"]
    names = (["auc", "acc", "val_acc"] + [f"auc_{c}" for c in CLASSES] + [f"recall_{c}" for c in CLASSES]
             + [f"auc_ptbin{k + 1}" for k in range(N_PT_BINS)] + ["auc_ptbin_mean"] + [f"rej_{e}" for e in EPS])
    P = S["paired"]
    for n in names:
        p = 1 if n.startswith("rej") else 4
        L.append(f"| {n} | " + " | ".join(dl(P[k][n], p) for k in ("PTW5-BASE", "PTWNC-BASE", "PTW5-PTWNC")) + " |")
    ba, bu = S["best_by_heldout_acc"], S["best_by_heldout_auc"]
    L += ["", f"Best single model by held-out accuracy: {ba['model']} (acc {f4(ba['acc'])}, macro AUC {f4(ba['auc'])}).",
          f"Best single model by held-out macro AUC: {bu['model']} (macro AUC {f4(bu['auc'])}, acc {f4(bu['acc'])}).", ""]
    (STORE / "roc_auc.md").write_text("\n".join(L))


if __name__ == "__main__":
    main()
