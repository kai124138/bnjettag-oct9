#!/usr/bin/env python3
"""Round-13 configs — binary weights under EBOPs pressure (jsc150-aligned).

Implements `code/hgq2/R13-DESIGN.md` verbatim. One generator, one scaling rule, so
the arms cannot drift apart by hand-editing (the memo's §3 requirement).

The question (memo §1): can a binary-{-1,+1}-weight transformer, trained with learnable
activation bitwidths under HGQ2 EBOPs pressure, produce a checkpoint at <= 5e5 EBOPs at
all — and if so, how far below a MATCHED multi-bit HGQ2 model at the same budget does its
macro-OvR ROC-test AUC sit?  Every model this project has trained so far ran with the
EBOPs term switched off (`beta0 = 0.0`, hard-coded until now); r13 turns it on.

Arms (memo §3) — architecture block byte-identical to `r8-small-w1a8-stdnn.json`:
  A1  r13-small-w1-freeact-beta   binary weights, learnable act bitwidths, beta schedule
  A2  r13-small-wq-freeact-beta   LEARNABLE MULTI-BIT weights (control), otherwise == A1
  A3  r13-small-w1-freeact-beta0  binary + learnable acts, beta == 0 (budget bridge)
  A4  r13-small-w1-fixa8-beta0    binary + FIXED A8 (r8 mechanism), beta == 0 (freedom ctl)
Stage 0   r13-lrprobe-w1-freeact-lr{2e5,5e5,1e4,2e4}   A1 @ beta=0, 300 epochs, seed 1
Stage 0b  r13-sighter-w1-freeact-beta                  A1 verbatim, seed 1 — the go/no-go

A2 is a COMPARISON BASELINE only. Binary {-1,+1} is the thesis; no ternary arm exists in
r13 and none may be added (memo §3).

Seeds are handled at the job layer (gen_r13_jobs.py), as in r7/r11/r12.

Usage (from code/hgq2/configs/):
    python gen_r13.py                 # write the configs
    python gen_r13.py --check         # build each model, print params; write nothing
    python gen_r13.py --lr 5e-5       # pin the Stage-0 LR winner into the 4 arms
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "r8-small-w1a8-stdnn.json")

# ---------------------------------------------------------------------------
# Peak LR for the four production arms.
#
# NOT INHERITED FROM r8 AS A DECISION (memo §4.5): r13 changes batch 4x (256 -> 1024) and
# epochs 15x (101 -> 1500), and this project's LR optimum is not monotone in scale or in
# recipe (tiny 1e-4, small 2e-5, large 5e-5; r7b's inherited LR invalidated a whole
# column). Stage 0 probes {2e-5, 5e-5, 1e-4, 2e-4} on A1/seed 1 at 300 epochs and the
# WINNER IS APPLIED TO ALL FOUR ARMS IDENTICALLY.
#
# The value below is a PLACEHOLDER equal to the r8 value so the configs are complete and
# hashable before Stage 0 returns. Re-run with `--lr <winner>` and re-generate BEFORE
# Stage 1 is launched; the generator prints a loud reminder while the placeholder stands.
# ---------------------------------------------------------------------------
PROD_LR_PLACEHOLDER = 2e-05
LR_GRID = {"2e5": 2e-05, "5e5": 5e-05, "1e4": 1e-04, "2e4": 2e-04}

EPOCHS = 1500
BATCH = 1024
WARMUP = 5
LR_CYCLE = 500            # 3 cosine cycles over the 1500 epochs (memo §6)
LR_MIN_FRAC = 0.02
VAL_BATCH = 4096          # memo §6 infra note; IDENTICAL in every arm
EBOPS_THRESHOLD = 5e5     # jsc150 repo's admission threshold (NOT the paper body's 3.5e5)

# memo §6, fixed before launch: 0-300 accuracy only, 300-600 log ramp over 6 decades,
# 600-1500 terminal pressure. Revising the terminal beta after the Stage-0b sighter is
# allowed ONCE, before the production runs, and must be logged as a schedule revision.
BETA_SCHEDULE = [[0, 0.0, "constant"],
                 [300, 1e-9, "log"],
                 [600, 1e-3, "constant"]]

PROBE_EPOCHS = 300


def _base() -> dict:
    with open(BASE) as f:
        return json.load(f)


def arch() -> dict:
    """The r8 flagship architecture block, VERBATIM (memo §3). norm 'none' in every arm:
    the 2026-07-25 norm confound does not recur here."""
    a = _base()["arch"]
    assert a["norm"] == "none", "r8 base must be norm-free"
    return a


def quant(weight: str, act_calib: str, beta0: float = 0.0) -> dict:
    q = {
        "weight": weight,
        "act_bits": 8,
        "act_policy": "static_per_tensor_mse_calibrated",
        "calib_n": 8192,
        "act_calib": act_calib,
        "beta0": float(beta0),
    }
    if act_calib == "free":
        q["act_bw_l1"] = 1e-08
    if weight == "kbi_learnable":
        q["weight_bw_l1"] = 1e-08
    return q


def train(lr: float, epochs: int = EPOCHS, beta_schedule=None,
          ebops: bool = True) -> dict:
    t = {
        "data": "/data/hls4ml_lhc_jet/train/train",
        "validation_split": 0.2,
        "epochs": epochs,
        "batch": BATCH,
        "lr": lr,
        "lr_schedule": "cosine_restarts",
        "lr_cycle_epochs": LR_CYCLE,
        "lr_min_frac": LR_MIN_FRAC,
        "warmup_epochs": WARMUP,
        "decay_epochs": 0,
        "decay_power": 1.0,
        "beta2": 0.98,
        "weight_decay": 0.01,
        "clip_mode": "value",
        "clipvalue": 1.0,
        "clipnorm": 1.0,
        # 0 DISABLES early stopping: under EBOPs pressure val AUC is EXPECTED to fall as
        # the bitwidths anneal, and stopping on it would truncate the Pareto front, which
        # IS the deliverable. Identical in every arm so the arms stay comparable.
        "es_patience": 0,
        "val_batch": VAL_BATCH,
        "wandb_project": "bnjettag-final",
    }
    if ebops:
        t["ebops"] = {
            "enable": True,
            "beta_schedule": beta_schedule,     # None => no BetaScheduler (beta stays 0)
            "threshold": EBOPS_THRESHOLD,
            "front_dir": "front",
            "metrics": ["val_macro_auc", "ebops"],
            "sides": [1, -1],
        }
    return t


HLS = _base()["hls"]


def cfg(name: str, weight: str, act_calib: str, lr: float,
        beta_schedule=None, epochs: int = EPOCHS) -> dict:
    return {
        "name": name,
        "era": 2,
        "arch": arch(),
        "quant": quant(weight, act_calib),
        "train": train(lr, epochs=epochs, beta_schedule=beta_schedule),
        "hls": HLS,
    }


def all_configs(prod_lr: float) -> dict:
    out = {}
    # ---- Stage 0: LR probe (A1 recipe, beta = 0, 300 epochs, seed 1 at the job layer) --
    for tag, lr in LR_GRID.items():
        n = f"r13-lrprobe-w1-freeact-lr{tag}"
        out[n] = cfg(n, "binary_absmean", "free", lr, beta_schedule=None,
                     epochs=PROBE_EPOCHS)

    # ---- the four production arms (memo §3) ----
    out["r13-small-w1-freeact-beta"] = cfg(
        "r13-small-w1-freeact-beta", "binary_absmean", "free", prod_lr,
        beta_schedule=BETA_SCHEDULE)                                        # A1
    out["r13-small-wq-freeact-beta"] = cfg(
        "r13-small-wq-freeact-beta", "kbi_learnable", "free", prod_lr,
        beta_schedule=BETA_SCHEDULE)                                        # A2
    out["r13-small-w1-freeact-beta0"] = cfg(
        "r13-small-w1-freeact-beta0", "binary_absmean", "free", prod_lr,
        beta_schedule=None)                                                 # A3
    out["r13-small-w1-fixa8-beta0"] = cfg(
        "r13-small-w1-fixa8-beta0", "binary_absmean", "trainable", prod_lr,
        beta_schedule=None)                                                 # A4

    # ---- Stage 0b: the beta sighter — A1 verbatim, one seed. Separate name so the run
    # is unambiguously the go/no-go feasibility gate and not one of A1's three seeds. ----
    s = json.loads(json.dumps(out["r13-small-w1-freeact-beta"]))
    s["name"] = "r13-sighter-w1-freeact-beta"
    out[s["name"]] = s
    return out


def _assert_matched(cfgs: dict) -> None:
    """The arms may differ ONLY in the fields the memo tabulates (§3). Asserted at
    generation time so a hand-edit cannot silently open a second axis."""
    arms = ["r13-small-w1-freeact-beta", "r13-small-wq-freeact-beta",
            "r13-small-w1-freeact-beta0", "r13-small-w1-fixa8-beta0"]
    ref = cfgs[arms[0]]
    for n in arms[1:]:
        c = cfgs[n]
        assert c["arch"] == ref["arch"], f"{n}: arch differs from A1"
        assert c["hls"] == ref["hls"], f"{n}: hls differs from A1"
        for k, v in ref["train"].items():
            if k == "ebops":
                continue
            assert c["train"][k] == v, f"{n}: train.{k}={c['train'][k]} != A1 {v}"
        for k in ("act_bits", "act_policy", "calib_n", "beta0"):
            assert c["quant"][k] == ref["quant"][k], f"{n}: quant.{k} differs from A1"
        assert c["train"]["ebops"]["threshold"] == EBOPS_THRESHOLD
        assert c["train"]["ebops"]["metrics"] == ["val_macro_auc", "ebops"]
        assert c["train"]["ebops"]["sides"] == [1, -1]
    # weights are binary in A1/A3/A4; the ONLY multi-bit arm is the A2 control
    for n in ("r13-small-w1-freeact-beta", "r13-small-w1-freeact-beta0",
              "r13-small-w1-fixa8-beta0", "r13-sighter-w1-freeact-beta"):
        assert cfgs[n]["quant"]["weight"] == "binary_absmean", f"{n} must stay binary"
    assert cfgs["r13-small-wq-freeact-beta"]["quant"]["weight"] == "kbi_learnable"
    # A1 is the ONLY pressured binary arm; A3/A4 carry no schedule
    assert cfgs["r13-small-w1-freeact-beta"]["train"]["ebops"]["beta_schedule"] == BETA_SCHEDULE
    for n in ("r13-small-w1-freeact-beta0", "r13-small-w1-fixa8-beta0"):
        assert cfgs[n]["train"]["ebops"]["beta_schedule"] is None, f"{n} must be beta=0"
    # Stage 0b is A1 with a different name and nothing else
    a1 = json.loads(json.dumps(cfgs["r13-small-w1-freeact-beta"]))
    sig = json.loads(json.dumps(cfgs["r13-sighter-w1-freeact-beta"]))
    a1.pop("name"), sig.pop("name")
    assert a1 == sig, "the Stage-0b sighter must be A1 verbatim"


def count_params(c: dict) -> int:
    """Build the QAT model and report its parameter count (needs .venv-hgq2).
    enable_ebops=True matches bnhgq2/train.py, i.e. the AS-TRAINED count."""
    import sys
    sys.path.insert(0, os.path.dirname(HERE))
    from bnhgq2 import qat  # noqa: E402
    m, _ = qat.build_qat_model(c, seed=1, enable_ebops=True)
    return int(m.count_params())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="build each model and print its param count; write nothing")
    ap.add_argument("--lr", type=float, default=PROD_LR_PLACEHOLDER,
                    help="peak LR for the four production arms (the Stage-0 winner)")
    args = ap.parse_args()

    cfgs = all_configs(args.lr)
    _assert_matched(cfgs)

    if args.lr == PROD_LR_PLACEHOLDER:
        print("[WARN] production LR is the r8 PLACEHOLDER 2e-5. Run Stage 0 (the four "
              "r13-lrprobe-* configs, seed 1), then re-generate with --lr <winner> "
              "before launching Stage 1.")

    if args.check:
        for n, c in sorted(cfgs.items()):
            q, t = c["quant"], c["train"]
            eb = t.get("ebops", {})
            print(f"{n:34s} w={q['weight']:15s} act={q['act_calib']:9s} "
                  f"lr={t['lr']:g} ep={t['epochs']:4d} "
                  f"beta={'sched' if eb.get('beta_schedule') else '0':5s} "
                  f"params={count_params(c):,}")
        return

    for n, c in sorted(cfgs.items()):
        p = os.path.join(HERE, f"{n}.json")
        with open(p, "w") as f:
            json.dump(c, f, indent=2)
            f.write("\n")
        print(f"wrote {p}")
    print(f"{len(cfgs)} configs")


if __name__ == "__main__":
    main()
