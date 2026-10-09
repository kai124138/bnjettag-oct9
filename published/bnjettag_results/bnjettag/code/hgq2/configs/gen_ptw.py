#!/usr/bin/env python3
"""Per-class jet-Pt sample-weighting study, N=8 headline model; only writes configs.

Three arms derived from the headline configs/r14-l1x3-n8-w1a8.json (N=8, L1x3 inputs,
binary absmean weights, A8, 101-epoch recipe, ES patience as in the headline):
  base   no pt_weights block (unweighted)
  ptw5   pt_weights: 100 log(Pt) bins, cap 5.0, no class weight
  ptwnc  same as ptw5, no cap
All arms pin train.jit_compile=false (the XLA/Triton autotuning failure of the 2026-09-10
b50 pilot; identical in every arm so they stay matched). Only `name`, `train.pt_weights`
and `train.jit_compile` may differ from the headline; asserted below.
Seeds (1-8) are chosen at launch; the seed sets both the data split and the model init.
"""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEADLINE = HERE / "r14-l1x3-n8-w1a8.json"
PREFIX = "ptw-n8-20260925"
PROJECT = "BNJetTagAug"
GROUP = PREFIX
PTW = {"enable": True, "n_bins": 100, "cap": 5.0, "class_weight": None, "plot": True}
ARMS = {"base": None, "ptw5": PTW, "ptwnc": {**PTW, "cap": None}}


def make(arm):
    cfg = copy.deepcopy(json.loads(HEADLINE.read_text()))
    cfg["name"] = f"{PREFIX}-{arm}-w1a8"
    cfg["train"]["jit_compile"] = False
    if ARMS[arm] is not None:
        cfg["train"]["pt_weights"] = dict(ARMS[arm])
    return cfg


def check_matched(cfg):
    """Everything except name / train.pt_weights / train.jit_compile equals the headline."""
    head = json.loads(HEADLINE.read_text())
    a, b = copy.deepcopy(cfg), copy.deepcopy(head)
    for c in (a, b):
        c.pop("name")
        c["train"].pop("pt_weights", None)
        c["train"].pop("jit_compile", None)
    assert a == b, f"{cfg['name']} differs from the headline beyond the allowed keys"
    assert cfg["train"]["wandb_project"] == PROJECT


if __name__ == "__main__":
    for arm in ARMS:
        cfg = make(arm)
        check_matched(cfg)
        path = HERE / f"{cfg['name']}.json"
        path.write_text(json.dumps(cfg, indent=2) + "\n")
        print(path.name)
