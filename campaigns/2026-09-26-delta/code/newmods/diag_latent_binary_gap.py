"""diag-latent-binary-gap: validation accuracy with the latent kernels in place of q * beta
(Delta Z08). Diagnostic only; the latent model is not a deployable model.

Mechanism: BitQEinsumDense.call and BitQDense.call look up the module-level function
`bnhgq2.qat.bitnet_binary_ste` at call time. Inside `latent_kernels()` that name is bound to an
identity (the float latent, cast to float32), so an eager forward pass uses the latents; on exit
the original function is restored. No bundle file is edited. Eager calls only: a tf.function
traced before entering the context keeps the binary kernels.

Reported: accuracy with binary kernels, accuracy with latent kernels, and the gap
(latent - binary), on the inputs given, with n. It measures how far the binary forward pass is
from the float network the optimizer actually moves (THEORY M2, STE bias).

    python -m newmods.diag_latent_binary_gap --checkpoint model.keras --npz val.npz
"""
from __future__ import annotations

import argparse
import contextlib
import json

import numpy as np
from keras import ops


@contextlib.contextmanager
def latent_kernels():
    from bnhgq2 import qat
    original = qat.bitnet_binary_ste

    def identity(w, eps=qat.EPS_BETA):
        return ops.cast(w, 'float32')

    qat.bitnet_binary_ste = identity
    try:
        yield
    finally:
        qat.bitnet_binary_ste = original


def accuracy(model, x, y, batch=1024):
    logits = np.concatenate([np.asarray(model(x[i:i + batch], training=False)) for i in range(0, len(x), batch)])
    return float(np.mean(logits.argmax(-1) == np.asarray(y).argmax(-1))), logits


def run(model, x, y, batch=1024):
    acc_b, _ = accuracy(model, x, y, batch)
    with latent_kernels():
        acc_l, _ = accuracy(model, x, y, batch)
    return {'n': int(len(x)), 'accuracy_binary': acc_b, 'accuracy_latent': acc_l,
            'gap_latent_minus_binary': acc_l - acc_b, 'status': 'diagnostic, not quotable'}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--npz', required=True)
    ap.add_argument('--max-jets', type=int, default=None)
    args = ap.parse_args(argv)
    import keras
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    import bnhgq2.qat  # noqa: F401
    model = keras.models.load_model(args.checkpoint, compile=False)
    with np.load(args.npz) as d:
        x, y = d['x'][:args.max_jets], d['y'][:args.max_jets]
    print(json.dumps(run(model, x, y), indent=1))


if __name__ == '__main__':
    main()
