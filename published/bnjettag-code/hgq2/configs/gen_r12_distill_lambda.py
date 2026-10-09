#!/usr/bin/env python3
"""Round-12 knowledge-distillation configs — the lambda sweep (post-dossier design).

SUPERSEDES the pre-dossier draft `gen_r12_distill.py` (an LR sweep at fixed
alpha=0.5), which is kept untouched for the record but must NOT be run for this
round.  The 2311.14160 dossier (literature/jet-tagging-transformers/) changed the
design in two ways this generator implements:

  1. CO-PRIMARY ENDPOINTS, pre-registered BEFORE launch: (a) ROC-test macro-OvR
     AUC — PROMOTE >= 0.8952, KILL <= 0.8922 after the sweep — AND (b) background
     rejection @ eps_S = 0.5 (rejection.py convention, macro-mean 1/FPR at first
     TPR >= eps).  The dossier's central finding is that KD moves the operating-
     point metric far more than AUC (their DeepSet: +29.9% rejection for +0.0011
     AUC), so an AUC-only gate would misread a real KD win as a failure.
  2. The sweep axis is the LOSS MIX lambda, not LR, with the paper's lambda=1
     pure-KL diagnostic included: lambda in {0.5, 0.9, 1.0} at fixed T=3.

LOSS CONVENTION (pinned; the paper omitted the T^2 factor, which confounds any
T-scan with an effective-lambda scan — dossier "recipe hole" #2):

    L = (1 - lambda) * CE(labels, student_logits)
      + lambda * T^2 * KL( softmax(teacher/T) || softmax(student/T) )

distill_r12.py parametrizes the same loss as alpha*CE + (1-alpha)*T^2*KL, i.e.
alpha = 1 - lambda.  Both numbers are written into the "distill" block so the
cfg_hash pins the convention: l50 -> alpha 0.5, l90 -> alpha 0.1, l100 -> alpha
0.0 (pure KL, hard labels off — the dossier's dark-knowledge isolation arm).

TEACHER (pre-registered, one fixed checkpoint for every student seed):
`r11-d128-w8a8-stdnn-s1`.  Selection rule: best validation macro-OvR AUC among
the round-11 d128 arms.  Source — W&B summary `best_val_macro_auc`, project
kayamaguchi-uc-san-diego/bnjettag-final, queried read-only 2026-07-26:
    w8a8-stdnn  s1 0.93908  s2 0.93841  s3 0.93731   <- best arm, best seed
    w1a8-stdnn  s1 0.93491  s2 0.93336  s3 0.93285
    w8a8-std    s1 0.93258  s2 0.93194  s3 0.93218
    fp32-std    s1 0.93202  s2 0.92986  s3 0.93111
The winner is also the best d128 arm on ROC-test (0.9380 +/- 0.0008,
roc-results/r11/roc_auc_r11_ladder.md), is norm-free like the student, shares
the round-8 input_std contract, and its run carries the checkpoint on W&B
(model_best.keras 3,921,254 B + input_std.json, verified via the API 2026-07-26
— identical byte size to the local copy under models/r11/).

FALLBACK (generated, NOT launched): `r12-distill-d32-w1a8-t64` — the l50 arm
with the teacher swapped to `r11-d64-w8a8-stdnn-s1` (best-val d64 by the same
rule, 0.93668; 73,025 params -> 3.8x the student instead of 14.85x).  The
dossier has no data point anywhere near our 15x capacity ratio and the KD
literature's known failure mode at large gaps is why this arm exists ready-made.
Only the teacher differs from l50, so launching it later isolates the
teacher-capacity variable.

STUDENT — arch+quant blocks are BYTE-IDENTICAL to `r8-small-w1a8-stdnn.json`
(the r8/r11 d32 flagship: d32/H4/L2/FFN64, binary_absmean, A8 trainable-scale
grids, norm none, input_std), read from that file and asserted, so
`model_best.keras` drops into the existing convert/ROC pipeline unchanged.
The train block is the flagship recipe verbatim (tuned peak LR 2e-5, 101 epochs,
warmup 1 + poly decay, beta2 0.98, wd 0.01, clipvalue 1.0, ES 15).  Seeds are
NOT set here: the job YAMLs pass --seed 1/2/3, the same seeds as the
r8-small-w1a8-stdnn baselines, so every comparison is PAIRED (same split, same
init) — required because the +0.005 target is smaller than the 0.0067 seed
spread (uncertainty-analyst design pass required before launch; see
../jobs/training/variants/R12-PREFLIGHT.md).

Usage (from code/hgq2/configs/):
    python gen_r12_distill_lambda.py            # write the 4 configs
    python gen_r12_distill_lambda.py --check    # print param counts, write nothing
"""
from __future__ import annotations

import argparse
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

R8_FLAGSHIP = os.path.join(HERE, "r8-small-w1a8-stdnn.json")

TEACHER_PROJECT = "kayamaguchi-uc-san-diego/bnjettag-final"
TEACHER_MAIN = "r11-d128-w8a8-stdnn-s1"   # best-val d128 (0.93908, W&B 2026-07-26)
TEACHER_T64 = "r11-d64-w8a8-stdnn-s1"     # best-val d64  (0.93668) — fallback only

TEMPERATURE = 3.0                          # dossier: gains saturate by T=3; T2 factor
LAMBDAS = {"l50": 0.5, "l90": 0.9, "l100": 1.0}

LOSS_CONVENTION = ("L = (1-lambda)*CE + lambda*T^2*KL(softmax(teacher/T)||"
                   "softmax(student/T)); alpha = 1-lambda (distill_r12.py)")


def base_blocks() -> tuple[dict, dict]:
    """arch + quant, read from the r8 flagship config so they are byte-identical
    BY CONSTRUCTION (json round-trip preserves key order)."""
    with open(R8_FLAGSHIP) as f:
        r8 = json.load(f)
    return r8["arch"], r8["quant"]


def train_block() -> dict:
    """The r8/r11 d32 flagship train recipe verbatim (tuned peak LR 2e-5)."""
    return {
        "data": "/data/hls4ml_lhc_jet/train/train",
        "validation_split": 0.2,
        "epochs": 101,
        "batch": 256,
        "lr": 2e-05,
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


HLS = {
    "backend": "Vitis",
    "part": "xcvu13p-flga2577-2-e",
    "clock_ns": 2.5,
    "rf": 256,
    "io": "io_parallel",
}


def cfg(name: str, lam: float, teacher_run: str) -> dict:
    arch, quant = base_blocks()
    return {
        "name": name,
        "era": 2,
        "arch": arch,
        "quant": quant,
        "train": train_block(),
        "distill": {
            "teacher_run": teacher_run,
            "teacher_project": TEACHER_PROJECT,
            "alpha": round(1.0 - lam, 10),      # what distill_r12.py consumes
            "temperature": TEMPERATURE,
            "lambda_kl": lam,                    # the pre-registered sweep axis
            "loss_convention": LOSS_CONVENTION,  # pins the T^2 form in the hash
        },
        "hls": dict(HLS),
    }


def all_configs() -> dict:
    out = {}
    for tag, lam in LAMBDAS.items():
        n = f"r12-distill-d32-w1a8-{tag}"
        out[n] = cfg(n, lam, TEACHER_MAIN)
    # d64-teacher fallback: l50 with ONLY the teacher changed. NOT launched.
    n = "r12-distill-d32-w1a8-t64"
    out[n] = cfg(n, 0.5, TEACHER_T64)
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
    dz = c["distill"]
    if abs(dz["alpha"] - (1.0 - dz["lambda_kl"])) > 1e-12:
        raise SystemExit(f"{c['name']}: alpha != 1 - lambda_kl — convention broken")


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
            d = c["distill"]
            print(f"{n:32s} lambda={d['lambda_kl']:<4g} alpha={d['alpha']:<4g} "
                  f"T={d['temperature']:g} teacher={d['teacher_run']} "
                  f"params={count_params(c):,}")
        return

    for n, c in sorted(cfgs.items()):
        p = os.path.join(HERE, f"{n}.json")
        with open(p, "w") as f:
            json.dump(c, f, indent=2)
            f.write("\n")
        print(f"wrote {p}")
    print(f"{len(cfgs)} configs (t64 is the un-launched d64-teacher fallback)")


if __name__ == "__main__":
    main()
