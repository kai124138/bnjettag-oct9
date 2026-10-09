#!/usr/bin/env python3
"""Round-15 "Gamma" configs — the softmax-output-grid arms at N = 8.

Motivation (experiment-log 2026-08-23): the BETA-1 characterization build (ctx-einsum
softmax operand forced ap_ufixed<4,0> on the scoped-fabric folded n8 W1A8 export) is the
first measured 0-DSP point under the VU13P LUT budget (post-opt 1,694,625 = 98.07%,
xczu7ev OOC, pre-route). That grid was FORCED at export; these arms TRAIN it, so a real
operating point with an AUC can be claimed (or the frontier reported).

Recipe = r14-l1x3-n8-w1a8 VERBATIM (gen_r14.py make(8, "w1a8")) plus exactly two keys:
  quant.softmax_out_bits  (the ctx-einsum attention-operand TOTAL width; R14 = 10)
  quant.softmax_out_i     (its integer bits; 0 => value in (0,1], 16 levels at 4 bits)
Absent keys reproduce R14 byte-for-byte (fingerprint gate, experiment-log 2026-08-19).

Arms: sm4i0 (the BETA-1 width) and sm6i0 (the knee candidate / fallback).
Naming: r15-gamma-<arm>-n8-w1a8 so roc_final.py's <run_prefix>-<variant>-s<seed> contract
holds with --run-prefix r15-gamma-<arm>-n8 --variants w1a8.
Control (B0) = the existing R14 W1A8 n8 checkpoints (same code path, knob absent).

Usage: python gen_r15_gamma.py   (writes r15-gamma-sm{4,6}i0-n8-w1a8.json here)
"""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from gen_r14 import make  # the r14 recipe, verbatim

ARMS = {"sm4i0": (4, 0), "sm6i0": (6, 0)}

if __name__ == "__main__":
    for arm, (bits, ibits) in ARMS.items():
        cfg = make(8, "w1a8")
        cfg["name"] = f"r15-gamma-{arm}-n8-w1a8"
        cfg["quant"]["softmax_out_bits"] = bits
        cfg["quant"]["softmax_out_i"] = ibits
        p = os.path.join(HERE, f"{cfg['name']}.json")
        with open(p, "w") as f:
            json.dump(cfg, f, indent=2)
        print(f"wrote {os.path.basename(p)}")
