#!/usr/bin/env python3
"""Round-14 configs — L1-realistic (N, 3) inputs, constituent-count sweep.

Input change (the ONLY axis vs the r8-small recipe): the 16 offline-style
constituent features are cut to the 3 the Level-1 trigger will actually provide —
pT, eta_rel, phi_rel — per Odagiu et al. (arXiv:2402.01876), the input set the
L1 field standardized on (and the one Chang's group uses, so cross-referencing
their numbers becomes input-matched). Sweep N constituents in {8, 16, 32, 64}.

Everything else is the r8-small recipe VERBATIM (d_model 32, 2 layers, 4 heads,
ffn 64, norm-free, input_std on, 101 epochs, lr 2e-5, es 15, act_calib trainable)
so any AUC difference vs the 16-feature r7/r8 tables is attributable to the input
set, and any difference across N to the constituent count.

Arms per N: fp32 / w8a8 (baselines) + w1a8 (thesis) = stage 1;
            w1a6 / w1a4 (activation ladder) = stage 2.
W&B: project BNJetTagAug (env-set by the job YAMLs; the config key is fallback).

Usage: python gen_r14.py   (writes r14-l1x3-n<N>-<variant>.json here)
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

N_SWEEP = [8, 16, 32, 64]
FEATURES = ["pt", "etarel", "phirel"]          # exact-suffix resolved (data.py)
VARIANTS = {
    "fp32": {"weight": "none", "act_bits": 32},
    "w8a8": {"weight": "int8_absmax", "act_bits": 8},
    "w1a8": {"weight": "binary_absmean", "act_bits": 8},
    "w1a6": {"weight": "binary_absmean", "act_bits": 6},
    "w1a4": {"weight": "binary_absmean", "act_bits": 4},
}


def make(n_part: int, variant: str) -> dict:
    q = VARIANTS[variant]
    return {
        "name": f"r14-l1x3-n{n_part}-{variant}",
        "era": 2,
        "arch": {
            "n_part": n_part, "n_feat": len(FEATURES), "features": FEATURES,
            "d_model": 32, "n_heads": 4, "n_layers": 2, "ffn_dim": 64,
            "n_classes": 5, "pool": "gap", "ffn_act": "relu",
            "norm": "none", "norm_placement": "per_linear",
            "pos_enc": "learned", "softmax_free": False, "input_std": True,
        },
        "quant": {
            "weight": q["weight"], "act_bits": q["act_bits"],
            "act_policy": "static_per_tensor_mse_calibrated",
            "calib_n": 8192, "act_calib": "trainable",
        },
        "train": {
            "data": "/data/hls4ml_lhc_jet/train/train",
            "validation_split": 0.2, "epochs": 101, "batch": 256,
            "lr": 2e-05, "warmup_epochs": 1, "decay_epochs": 100,
            "decay_power": 1.0, "beta2": 0.98, "weight_decay": 0.01,
            "clip_mode": "value", "clipvalue": 1.0, "clipnorm": 1.0,
            "es_patience": 15, "wandb_project": "BNJetTagAug",
        },
        "hls": {"backend": "Vitis", "part": "xcvu13p-flga2577-2-e",
                "clock_ns": 2.5, "rf": 256, "io": "io_parallel"},
    }


if __name__ == "__main__":
    for n in N_SWEEP:
        for v in VARIANTS:
            cfg = make(n, v)
            p = os.path.join(HERE, f"{cfg['name']}.json")
            with open(p, "w") as f:
                json.dump(cfg, f, indent=2)
            print(f"wrote {os.path.basename(p)}")
