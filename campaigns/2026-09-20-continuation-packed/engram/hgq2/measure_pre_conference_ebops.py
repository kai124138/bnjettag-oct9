#!/usr/bin/env python3
'Measure HGQ2 effective bit operations for the pre-conference checkpoints.'
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

N_SWEEP = [8, 16, 32, 64]
VARIANTS = ["w8a8", "w1a8", "w1a6", "w1a4"]
SEEDS = [1, 2, 3]
FEATURES = ["pt", "etarel", "phirel"]
CALIB_N = 8192


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-wandb", action="store_true")
    ap.add_argument("--out", default=os.path.join(REPO, "results",
                                                  "pre_conference", "measure_pre_conference_ebops.json"))
    a = ap.parse_args()

    os.environ.setdefault("KERAS_BACKEND", "tensorflow")
    from bnhgq2.data import load_eval_set, calibration_batch, apply_input_std
    from bnhgq2.ebops_calc import compute_ebops
    from evaluate_roc import load_final_model

    results = {}
    for n in N_SWEEP:
        X, _ = load_eval_set(os.path.join(REPO, "data", "val"), n_part=n,
                             features=FEATURES)
        Xc = calibration_batch(X, CALIB_N)
        del X
        for v in VARIANTS:
            for s in SEEDS:
                leaf = f"pre_conference-n{n}-{v}-s{s}"
                ckdir = os.path.join(REPO, "results", "predictions", "pre_conference",
                                     f"n{n}", "_ckpt_dl", f"{v}-s{s}")
                ck = os.path.join(ckdir, "model_best.keras")
                if not os.path.isfile(ck):
                    print(f"[skip] {leaf}: {ck} missing (run the ROC pass first)")
                    continue
                std_p = os.path.join(ckdir, "input_std.json")
                Xm = Xc
                if os.path.isfile(std_p):
                    st = json.load(open(std_p))
                    Xm = apply_input_std(Xc, st["mu"], st["sigma"])
                model = load_final_model(ck)
                eb = compute_ebops(model, Xm)
                results[leaf] = {"n_part": n, "variant": v, "seed": s,
                                 "ebops": eb["total"], "per_layer": eb["per_layer"],
                                 "checkpoint": os.path.relpath(ck, REPO),
                                 "convention": "hgq2_trace_minmax"}
                print(f"[ebops] {leaf:28s} {eb['total']:>12,}")
                del model

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump({"features": FEATURES, "calib_n": CALIB_N,
                   "convention": "hgq2_trace_minmax (never mix with HGQ-v1 Eq.5)",
                   "models": results}, f, indent=1)
    print(f"[ebops] wrote {a.out} ({len(results)} models)")

    if not a.no_wandb:
        from bnhgq2 import wandb_util as wbu
        if not wbu.wandb_enabled():
            print("[wandb] no credential — skipping summary writes")
            return
        import wandb
        api = wandb.Api(timeout=120)
        for leaf, row in results.items():
            try:
                for r in api.runs(f"{wbu.resolve_entity()}/binary-transformer-fixed-precision",
                                  filters={"display_name": leaf}):
                    r.summary["ebops"] = row["ebops"]
                    r.summary.update()
                print(f"[wandb] ebops -> {leaf}")
            except Exception as e:
                print(f"[wandb] warn {leaf}: {e}")


if __name__ == "__main__":
    main()
