"""diag-input-proj-rows: distinct sign patterns of the binary input projection (Delta Z04, Z08).

input_proj is BitQEinsumDense 'btf,fd->btd', kernel (F, D). Its deployed weight is
beta * q with q = bipolar_sign(w - mean(w)) (qat.bitnet_binary_ste, never 0). Each output
channel d sees the F input features through the sign vector q[:, d] in {-1,+1}^F, so at F = 3
there are at most 2^3 = 8 distinct patterns, and at most 4 up to a global sign flip. This is
the "fan-in-3 first layer" capacity bound of THEORY M1: D = 32 channels can carry at most 8
distinct directions.

Reported: n_channels (D), fan_in (F), n_distinct, n_distinct_up_to_sign, the count per pattern,
and the maximum possible (2^F, 2^(F-1)). Diagnostic only.

    python -m newmods.diag_input_proj_rows --checkpoint model.keras [--layer input_proj]
"""
from __future__ import annotations

import argparse
import json
from collections import Counter

import numpy as np


def sign_patterns(kernel_latent):
    """kernel_latent (F, D) latent floats -> q (F, D) in {-1,+1}, same math as the forward pass."""
    w = np.asarray(kernel_latent, dtype=np.float32)
    wc = w - w.mean(dtype=np.float32)
    return np.where(wc >= 0.0, 1, -1).astype(np.int8)


def distinct_rows(q):
    """q (F, D) in {-1,+1}: count distinct fan-in sign vectors over the D output channels."""
    q = np.asarray(q)
    if q.ndim != 2 or not np.isin(q, (-1, 1)).all():
        raise ValueError('expected a 2-D array of -1/+1 (fan_in, channels)')
    cols = [tuple(int(v) for v in q[:, d]) for d in range(q.shape[1])]
    counts = Counter(cols)
    canon = Counter(c if c[0] == 1 else tuple(-v for v in c) for c in cols)
    f = q.shape[0]
    return {'fan_in': f, 'n_channels': q.shape[1], 'n_distinct': len(counts),
            'n_distinct_up_to_sign': len(canon), 'max_distinct': 2 ** f, 'max_up_to_sign': 2 ** (f - 1),
            'pattern_counts': {''.join('+' if v > 0 else '-' for v in k): n for k, n in sorted(counts.items())}}


def from_model(model, layer='input_proj'):
    ly = model.get_layer(layer)
    k = np.asarray(ly._kernel.numpy())
    if k.ndim != 2:
        raise ValueError(f'{layer} kernel has shape {k.shape}; expected (fan_in, channels)')
    rep = distinct_rows(sign_patterns(k))
    rep['layer'] = layer
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--layer', default='input_proj')
    args = ap.parse_args(argv)
    import keras
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    import bnhgq2.qat  # noqa: F401  (registers the binary layers for deserialization)
    model = keras.models.load_model(args.checkpoint, compile=False)
    print(json.dumps(from_model(model, args.layer), indent=1))


if __name__ == '__main__':
    main()
