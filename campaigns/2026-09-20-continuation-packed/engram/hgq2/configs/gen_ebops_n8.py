#!/usr/bin/env python3
"""Four-run N=8 binary-weight pilot; only writes configurations, never launches.

Matched seed 1, initial A8, free per-tensor activation widths in all four arms.
Budgets resolve once from the calibrated initial model, per run. The control
has beta=0 but retains the same tiny width L1 as the three target arms.
"""
import argparse
import json
from pathlib import Path
from generate_pre_conference import make

PROJECT = "binary-transformer"
PREFIX = "post_conference_budget_pilot"
ARMS = {"control": None, "b75": 0.75, "b50": 0.50, "b25": 0.25}


def make_pilot(arm):
    cfg = make(8, "w1a8")
    cfg["name"] = f"{PREFIX}-{arm}-w1a8"
    ratio = ARMS[arm]
    cfg["quant"].update(act_calib="free", act_policy="learned_per_tensor_width",
                         act_bw_l1=1e-8, beta0=0.0 if ratio is None else 1e-7)
    # Keep every arm on the same full-data, 101-epoch schedule; AUC early stopping
    # would terminate compression before the controller has a chance to act.
    cfg["train"].update(es_patience=0, wandb_project=PROJECT)
    cfg["train"]["ebops"] = {
        "enable": True, "monitor_widths": True,
        "controller": "none" if ratio is None else "pid",
        "beta_schedule": None, "front_dir": "front",
        "metrics": ["val_macro_auc", "ebops"], "sides": [1, -1],
    }
    if ratio is not None:
        cfg["train"]["ebops"].update(target_ratio=ratio, pid={
            "init_beta": 1e-7, "p": 1.0, "i": 0.05, "d": 0.0,
            "warmup": 10, "log": True, "min_beta": 1e-10,
            "max_beta": 1e-3, "damp_beta_on_target": 0.0,
        })
    return cfg


def make_cost_first():
    """Single resource-priority retry, same N8/L1x3/seed1 and 50% ceiling."""
    cfg = make_pilot("b50")
    cfg["name"] = f"{PREFIX}-costfirst-b50-w1a8"
    cfg["quant"]["beta0"] = 1e-4
    cfg["train"].update(lr=1e-4, warmup_epochs=0, decay_epochs=0, jit_compile=False)
    eb = cfg["train"]["ebops"]
    eb.pop("target_ratio")
    eb.update(selection="min_ebops", stop_on_target=True, metrics=["ebops"], sides=[-1])
    eb["pid"].update(target_ebops=869591, init_beta=1e-4, min_beta=1e-4,
                     max_beta=1e-2, warmup=0)
    return cfg


def make_long_budget():
    """Single 1000-epoch N8 run; recover AUC while targeting 350k EBOPs."""
    cfg = make_pilot("b25")
    cfg["name"] = "post_conference_extended_budget350k-w1a8"
    cfg["train"].update(epochs=1000, decay_epochs=999, jit_compile=False)
    eb = cfg["train"]["ebops"]
    eb.pop("target_ratio")
    eb.update(selection="max_auc", stop_on_target=False)
    eb["pid"]["target_ebops"] = 350000
    return cfg


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cost-first", action="store_true")
    mode.add_argument("--long-budget", action="store_true")
    args = parser.parse_args()
    configs = ([make_long_budget()] if args.long_budget else
               [make_cost_first()] if args.cost_first else [make_pilot(arm) for arm in ARMS])
    for cfg in configs:
        path = Path(__file__).parent / f"{cfg['name']}.json"
        path.write_text(json.dumps(cfg, indent=2) + "\n")
        print(path.name)
