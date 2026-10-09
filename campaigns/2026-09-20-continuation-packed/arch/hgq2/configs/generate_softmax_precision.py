#!/usr/bin/env python3
'Generate attention-softmax precision configurations at eight constituents.\n\nAll other parameters match the pre-conference W1A8 configuration.'
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from generate_pre_conference import make  # the pre-conference recipe, verbatim

ARMS = {"sm4i0": (4, 0), "sm6i0": (6, 0)}

if __name__ == "__main__":
    for arm, (bits, ibits) in ARMS.items():
        cfg = make(8, "w1a8")
        cfg["name"] = f"post_conference_softmax-{arm}-n8-w1a8"
        cfg["quant"]["softmax_out_bits"] = bits
        cfg["quant"]["softmax_out_i"] = ibits
        p = os.path.join(HERE, f"{cfg['name']}.json")
        with open(p, "w") as f:
            json.dump(cfg, f, indent=2)
        print(f"wrote {os.path.basename(p)}")
