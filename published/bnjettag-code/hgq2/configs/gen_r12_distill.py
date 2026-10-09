#!/usr/bin/env python3
"""Round-12 knowledge-distillation configs — the d32 flagship as a KD student.

WHY (W1.5): the compiler fit levers (fold, FR) spend accuracy nowhere, but the
campaign carries an AUC floor of 0.8835 and the flagship sits at 0.8902 +/- 0.0067
(ROC-test, 3 seeds, roc-results/r11/roc_auc_r11_ladder.md).  KD banks accuracy
headroom the levers can later spend.  Pre-registered gates: PROMOTE if the student
reaches ROC-test macro-OvR AUC >= 0.8952 (+0.005 over 0.8902); KILL if <= 0.8922
after the LR sweep.

TEACHER (pre-registered, one fixed checkpoint for every student seed):
`r11-d128-w8a8-stdnn-s1`.  Selection rule: best validation macro-OvR AUC among
the round-11 d128 runs.  Source — W&B summary `best_val_macro_auc`, project
kayamaguchi-uc-san-diego/bnjettag-final, queried read-only 2026-07-26:
    w8a8-stdnn  s1 0.93908  s2 0.93841  s3 0.93731   <- best arm, best seed s1
    w1a8-stdnn  s1 0.93491  s2 0.93336  s3 0.93285
    w8a8-std    s1 0.93258  s2 0.93194  s3 0.93218
    fp32-std    s1 0.93202  s2 0.92986  s3 0.93111
The winner also carries its checkpoint on the run (model_best.keras 3,921,254 B +
input_std.json, verified via the API the same day) and is the best d128 arm on
ROC-test as well (0.9380 +/- 0.0008, roc_auc_r11_ladder.md).  The teacher is
norm-free like the student, and shares the round-8 input_std contract.

STUDENT — arch+quant blocks are BYTE-IDENTICAL to `r8-small-w1a8-stdnn.json`
(the r8/r11 flagship: d32/H4/L2/FFN64, binary_absmean, A8 trainable-scale grids,
norm none, input_std), so `model_best.keras` is convert/ROC-compatible unchanged.
Only the `train` block (LR for the probes) and the new `distill` block differ.
Asserted, not hoped: this generator diffs its arch+quant against the r8 file and
refuses to write on any mismatch; preflight_r12.sh re-checks the emitted JSONs.

LR: the flagship's tuned peak is 2e-5 (r8, decisions.md).  KD changes the loss
landscape, so the round carries an LR probe in the r11 LR_PROBE pattern: one rung
below (1e-5) and one above (5e-5), one seed each.  The r11 lesson (an inherited
LR invalidated round 7b's tiny column; d64's first-pass optimum sat on the grid
edge) is why the probe brackets rather than trusts 2e-5.

KD hyperparameters: standard Hinton loss, alpha=0.5, T=3.0 (the distill_r12.py
defaults, written explicitly into the config so the cfg_hash pins them).

Usage (from code/hgq2/configs/):
    python gen_r12_distill.py            # write the configs
    python gen_r12_distill.py --check    # print param counts, write nothing
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

R8_FLAGSHIP = os.path.join(HERE, "r8-small-w1a8-stdnn.json")

TEACHER_RUN = "r11-d128-w8a8-stdnn-s1"
TEACHER_PROJECT = "kayamaguchi-uc-san-diego/bnjettag-final"

# main run at the flagship's tuned LR; probes bracket it (r11 LR_PROBE pattern)
LR_MAIN = 2e-05
LR_PROBES = {"1e5": 1e-05, "5e5": 5e-05}


def base_blocks() -> tuple[dict, dict]:
    """arch + quant, read from the r8 flagship config so they are byte-identical
    BY CONSTRUCTION (json round-trip preserves key order)."""
    with open(R8_FLAGSHIP) as f:
        r8 = json.load(f)
    return r8["arch"], r8["quant"]


def train_block(lr: float) -> dict:
    """The r8/r11 flagship train recipe; only `lr` varies across the probe."""
    return {
        "data": "/data/hls4ml_lhc_jet/train/train",
        "validation_split": 0.2,
        "epochs": 101,
        "batch": 256,
        "lr": lr,
        "warmup_epochs": 1,
        "decay_epochs": 100,
        "decay_power": 1.0,
        "beta2": 0.98,
        "weight_decay": 0.01,
        "clip_mode": "value",
        "clipvalue": 1.0,
        "clipnorm": 1.0,
        "es_patience": 15,
        "wandb_project": "bnjettag-final",
    }


DISTILL = {
    "teacher_run": TEACHER_RUN,
    "teacher_project": TEACHER_PROJECT,
    "alpha": 0.5,
    "temperature": 3.0,
}

HLS = {
    "backend": "Vitis",
    "part": "xcvu13p-flga2577-2-e",
    "clock_ns": 2.5,
    "rf": 256,
    "io": "io_parallel",
}


def cfg(name: str, lr: float) -> dict:
    arch, quant = base_blocks()
    return {
        "name": name,
        "era": 2,
        "arch": arch,
        "quant": quant,
        "train": train_block(lr),
        "distill": dict(DISTILL),
        "hls": dict(HLS),
    }


def all_configs() -> dict:
    out = {"r12-distill-d32-w1a8": cfg("r12-distill-d32-w1a8", LR_MAIN)}
    for tag, lr in LR_PROBES.items():
        n = f"r12-distill-d32-w1a8-lr{tag}"
        out[n] = cfg(n, lr)
    return out


def assert_flagship_identity(c: dict) -> None:
    """Hard gate: arch+quant must match the r8 flagship byte-for-byte (canonical
    JSON), or the student is not convert-compatible and the config must not exist."""
    with open(R8_FLAGSHIP) as f:
        r8 = json.load(f)
    for block in ("arch", "quant"):
        a = json.dumps(c[block], sort_keys=True, separators=(",", ":"))
        b = json.dumps(r8[block], sort_keys=True, separators=(",", ":"))
        if a != b:
            raise SystemExit(f"{c['name']}: {block} block differs from "
                             f"r8-small-w1a8-stdnn.json — refusing to write")


def count_params(c: dict) -> int:
    """Build the QAT student and report its parameter count (needs .venv-hgq2).
    enable_ebops=True matches bnhgq2/train.py, i.e. the AS-TRAINED count
    (19,201 for d32); building with False under-reports by 50 (the EBOPs
    counters) and produced a table mixing conventions — do not change this."""
    import sys

    sys.path.insert(0, os.path.dirname(HERE))
    from bnhgq2 import qat  # noqa: E402

    m, _ = qat.build_qat_model(c, seed=1, enable_ebops=True)
    return int(m.count_params())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="build each student and print its param count; write nothing")
    args = ap.parse_args()

    cfgs = all_configs()
    for c in cfgs.values():
        assert_flagship_identity(c)

    if args.check:
        for n, c in sorted(cfgs.items()):
            print(f"{n:34s} lr={c['train']['lr']:g} teacher={c['distill']['teacher_run']} "
                  f"alpha={c['distill']['alpha']} T={c['distill']['temperature']} "
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
