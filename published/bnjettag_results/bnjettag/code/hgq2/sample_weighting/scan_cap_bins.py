#!/usr/bin/env python3
"""Pre-training scan that fixed the bin count and cap of the jet-pT sample weights.

Rebuilds seed 1's training split exactly as the trainer does (default_rng(1).permutation
over the training archive in file order, first 20 % held back as internal validation), then
for every (n_bins, cap) pair computes the per-class weights with bnhgq2.pt_weights and records:
  worst_tv   largest total-variation distance, over the five classes, between a class's
             weighted log(pT) histogram and the mean of the five (100 fixed bins; 0 = same
             shape, 1 = disjoint). The unweighted row is the starting point.
  eff_<c>    effective sample size (sum w)^2 / sum w^2 as a fraction of class c's jets
  max_w      largest weight after the per-class rescaling
It also redraws the three diagnostic figures of the write-up for the chosen settings.

Usage: python scan_cap_bins.py --train-dir <train .h5 dir> --out <dir>
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HGQ2 = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, HGQ2)

from bnhgq2.data import CLASS_NICE  # noqa: E402
from bnhgq2 import pt_weights as ptw  # noqa: E402

ROOT = os.environ.get("BNJETTAG_ROOT", os.path.abspath(os.path.join(HGQ2, "..", "..", "..")))
SEED = 1
VSPLIT = 0.20


def worst_tv(Pts, y, w, n_bins=100):
    edges = np.linspace(np.log(Pts).min(), np.log(Pts).max(), n_bins + 1)
    H = [np.histogram(np.log(Pts[y == c]), edges, weights=w[y == c])[0] for c in range(5)]
    H = [h / h.sum() for h in H]
    ref = sum(H) / 5
    return float(max(0.5 * np.abs(h - ref).sum() for h in H))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train-dir", default=os.path.join(ROOT, "data", "train"))
    ap.add_argument("--out", default=os.path.join(ROOT, "bnjettag", "results", "pt-weighting"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    Pts, Y = ptw.load_train_pt(args.train_dir)
    idx = np.random.default_rng(SEED).permutation(len(Pts))
    tr = idx[int(len(Pts) * VSPLIT):]
    Pts, y = Pts[tr], np.argmax(Y[tr], axis=1)

    rows = [{"n_bins": None, "cap": None, "weighted": False,
             "worst_tv": round(worst_tv(Pts, y, np.ones(len(y))), 4)}]
    for n_bins in (100, 50, 25):
        for cap in (None, 20.0, 10.0, 5.0):
            w, _ = ptw.compute_pt_weights(Pts, y, n_bins=n_bins, cap=cap)
            s = ptw.weight_summary(w, y, CLASS_NICE)
            rows.append({"n_bins": n_bins, "cap": cap, "weighted": True,
                         "worst_tv": round(worst_tv(Pts, y, w), 4),
                         "max_w": round(float(w.max()), 2),
                         **{f"eff_{k}": round(v["eff_frac"], 3) for k, v in s.items()}})
            print(rows[-1], flush=True)
    with open(os.path.join(args.out, "cap_bins_scan.json"), "w") as f:
        json.dump({"split": f"seed {SEED} training split", "n_jets": int(len(y)),
                   "rows": rows}, f, indent=1)

    w, info = ptw.compute_pt_weights(Pts, y, n_bins=100, cap=5.0)
    ptw.plot_pt_weights(info, CLASS_NICE, args.out, "seed1_cap5")
    ptw.plot_weight_hist(w, y, CLASS_NICE, args.out, "seed1_cap5")
    _, info_nc = ptw.compute_pt_weights(Pts, y, n_bins=100, cap=None)
    ptw.plot_pt_weights(info_nc, CLASS_NICE, args.out, "seed1_nocap")


if __name__ == "__main__":
    main()
