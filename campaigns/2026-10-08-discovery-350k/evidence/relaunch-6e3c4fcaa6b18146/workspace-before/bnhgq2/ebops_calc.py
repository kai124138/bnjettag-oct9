"""Native HGQ2 EBOPs for a built model.

trace_minmax runs a training='tracing' forward pass that (re)computes each
layer's _ebops from its quantizer bitwidths and stores the total. With frozen
quantizers this is a deterministic structural metric. NOTE: the HGQ2 formula
(multiply term + accumulator term + LUT terms) differs from the HGQ-v1 Eq.5
convention used by code/training/ebops.py — the two are reported side by side,
never mixed (see results store).
"""
from __future__ import annotations

import numpy as np


def compute_ebops(model, X_calib, batch_size=2048):
    from hgq.utils import trace_minmax

    # asarray, not astype: no copy when the sample is already float32 (a full training
    # split under [D20] is ~430 MB at N=64). Same values either way.
    total = trace_minmax(model, np.asarray(X_calib, dtype=np.float32), batch_size=batch_size,
                         verbose=0)
    per_layer = {}
    for layer in model.layers:
        if getattr(layer, "enable_ebops", False) and getattr(layer, "_ebops", None) is not None:
            per_layer[layer.name] = int(np.asarray(layer.ebops))
    return {"total": int(total), "per_layer": per_layer}
