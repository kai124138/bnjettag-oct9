"""[L8]/[D20] per-quantizer WRAP overflow fraction of a saved model on a data set.

Diagnostic only (never selects anything). For every datalane quantizer in WRAP mode (the
[A20] activation, Q/K/V-stream, softmax-output and softmax inv-input quantizers, nested ones
included) it counts, on the rows given, the elements whose rounded input lies outside the
quantizer's stored range [min, max]; those elements wrap at inference. The model is run
with training=False, so no range (i, k) is touched: the ranges are the ones as saved.

Elements of a 0-bit channel (b = relu(i + f) = 0) output 0 by design and are counted as
`pruned`, not in the overflow denominator.
"""
from __future__ import annotations

from contextlib import contextmanager

import numpy as np


def wrap_quantizers(model):
    """[(name, quantizer)] named as `ebops_target.width_snapshot` names them (`layer`,
    `layer__in<j>`, `layer__inv_iq`), so the two records join. Cross-checked against a
    recursive walk, so no nested WRAP datalane quantizer is missed."""
    from hgq.quantizer.internal.fixed_point_quantizer import FixedPointQuantizerBase
    from .ebops_target import activation_quantizers

    def is_wrap(q):
        return (isinstance(q, FixedPointQuantizerBase) and q.overflow_mode == 'WRAP'
                and not getattr(q, '_is_weight', False))
    found = [(name, q) for name, q in activation_quantizers(model) if is_wrap(q)]
    walked = {id(q) for q in model._flatten_layers(include_self=False, recursive=True) if is_wrap(q)}
    if walked != {id(q) for _, q in found}:
        raise AssertionError(f'WRAP quantizers outside activation_quantizers: {len(walked)} vs {len(found)}')
    return found


@contextmanager
def _counting(quantizers):
    from keras import ops
    counts = {id(q): {'alive': 0, 'overflow': 0, 'pruned': 0} for _, q in quantizers}
    originals = {}
    for cls in {type(q) for _, q in quantizers}:
        original = cls.call
        originals[cls] = original

        def call(self, inputs, training=None, _original=original):
            c = counts.get(id(self))
            if c is not None and not training:
                shape = ops.shape(inputs)
                f = self.bw_mapper.bw_to_x(self.f, shape)
                xr = self.stateless_quantizer.round(inputs, f, False, self.seed_gen)
                lo = self.bw_mapper.bw_to_x(self.min, shape)
                hi = self.bw_mapper.bw_to_x(self.max, shape)
                alive = self.bw_mapper.bw_to_x(self.b, shape) > 0
                over = ops.logical_and(ops.logical_or(xr > hi, xr < lo), alive)
                n_alive = int(ops.convert_to_numpy(ops.sum(ops.cast(alive, 'int64'))))
                c['alive'] += n_alive
                c['overflow'] += int(ops.convert_to_numpy(ops.sum(ops.cast(over, 'int64'))))
                c['pruned'] += int(np.prod(ops.convert_to_numpy(shape))) - n_alive
            return _original(self, inputs, training=training)

        cls.call = call
    try:
        yield counts
    finally:
        for cls, original in originals.items():
            cls.call = original


def overflow_fractions(model, x, batch_size=4096):
    """{quantizer: {alive, overflow, pruned, fraction}} over the rows of x (eager, CPU or GPU)."""
    quantizers = wrap_quantizers(model)
    with _counting(quantizers) as counts:
        for start in range(0, len(x), batch_size):
            model(np.asarray(x[start:start + batch_size], dtype=np.float32), training=False)
    result = {}
    for name, q in quantizers:
        c = counts[id(q)]
        result[name] = {**c, 'fraction': (c['overflow'] / c['alive']) if c['alive'] else None}
    total_alive = sum(v['alive'] for v in result.values())
    total_over = sum(v['overflow'] for v in result.values())
    return {'per_quantizer': result, 'n_rows': int(len(x)), 'n_wrap_quantizers': len(result),
            'overflow_fraction_all': (total_over / total_alive) if total_alive else None}
