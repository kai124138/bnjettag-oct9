"""[L8] WRAP overflow fraction: zero on the rows the ranges were traced on, positive on a
heavier-tailed superset; the diagnostic neither changes outputs nor touches any range."""
import os

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np

from test_d20_trace import arrays
from test_resume_cadence import tiny_cfg


def test_overflow_fraction():
    import keras
    from bnhgq2 import ablation
    from bnhgq2.compat import apply_keras_compat
    from bnhgq2.wrap_overflow import overflow_fractions, wrap_quantizers
    apply_keras_compat()
    (xt, _, _, _), _ = arrays(n_train=4000)
    keras.backend.clear_session()
    model, _ = ablation.matching_initialization(tiny_cfg(), xt[:512], 1)
    ablation.compute_ebops(model, xt[:256])
    names = [n for n, _ in wrap_quantizers(model)]
    from bnhgq2.ebops_target import width_snapshot
    assert 'input_proj' in names and any(n.endswith('__inv_iq') for n in names), names
    assert set(names) <= set(width_snapshot(model)), names
    before = [np.asarray(v).copy() for v in model.weights]
    out = np.asarray(model(xt[:64], training=False))
    traced = overflow_fractions(model, xt[:256], batch_size=100)
    assert traced['overflow_fraction_all'] == 0.0, traced
    wider = overflow_fractions(model, xt, batch_size=1000)
    assert wider['overflow_fraction_all'] > 0 and wider['n_rows'] == 4000
    assert all(np.array_equal(a, np.asarray(b)) for a, b in zip(before, model.weights))
    np.testing.assert_array_equal(np.asarray(model(xt[:64], training=False)), out)
    # after a full-split trace, the full split no longer overflows
    ablation.compute_ebops(model, xt)
    assert overflow_fractions(model, xt, batch_size=1000)['overflow_fraction_all'] == 0.0
