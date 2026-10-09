#!/usr/bin/env python3
"""[A7] Static EBOPs floor of an architecture under its configured quantizers (CPU).

python static_floor.py configs/<arm>.json [...] --out floors.json

Two floors per config, both native HGQ2 EBOPs from `trace_minmax` on a fixed synthetic
standard-normal sample (256 jets):
  zero  every learnable activation / softmax width at its lower bound. KIF SAT:
        i = ic.min, f = fc.min, so bits = relu(i+f) + k = k (1 bit, sign only). KIF WRAP:
        f = fc.min; tracing sets i from the data (<= ic.max), so bits = relu(i+f) = 0.
        KBI tables: b = bc.min (4 under quant.softmax_quant="chang").
  one   "1-bit-alive": every learnable magnitude width at 1 bit. WRAP: f = 1 - i, iterated
        with tracing until i is stable; SAT KIF at relu(i+f) = 0 (1 bit with k); tables at
        bc.min. Every learnable width is asserted after the final trace, not assumed.
  attn_narrow / attn_full  the paper's ">= 1 bit for attention" rule read as a datalane
        constraint (arbiter v3 #3, fix 6): every width at the zero floor except the named
        attention datalane quantizers, which are held at 1 bit (WRAP f = 1 - i, iterated as
        in "one"). narrow: the Q.K and A.V streams (`*_attn_scores__in0/1`,
        `*_attn_ctx__in0/1`, the latter is the softmax output into A.V); full: narrow plus the
        inputs of Wq, Wk, Wv. The "weights only" reading adds nothing here: the kernels are
        binary, fixed at 1 bit, and a dense with a 0-bit input costs 0 EBOPs, so that floor
        is the zero floor (recorded as `weights_only_rule`).
Fixed-width quantizers (trainable=False) stay at their configured widths.

Weights are binary (1 bit, fixed) and not touched. [D22] NB (`quant.weight: kbi_learnable`):
the modes above keep the learned weight widths at init (b0 4); NB adds zero_w0 (zero floor,
every weight at 0 bits), one_w1 and one_w0 (1-bit-alive with every weight at 1 / 0 bits).
The floor depends on widths only, not
on the sample, because EBOPs are priced from bit widths; the WRAP i that tracing sets is
bounded by ic.max and does not enter relu(i + fc.min) = 0. STATIC_INFEASIBLE means the
zero floor is at or above the arm's target (STUDY [A7]). Not a result; a structural trace.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')

import numpy as np


def _learnable(model):
    from bnhgq2.ebops_target import activation_quantizers
    for name, q in activation_quantizers(model):
        if q.trainable:
            yield name, q


def _full(var, value):
    var.assign(np.full(var.shape, value, dtype='float32'))


ATTN_NARROW = ('_attn_scores__in0', '_attn_scores__in1', '_attn_ctx__in0', '_attn_ctx__in1')
ATTN_FULL = ATTN_NARROW + ('_attn_Wq', '_attn_Wk', '_attn_Wv')


def one_bit_names(model, mode):
    """Names of the learnable quantizers held at 1 bit in `mode` (None = all of them)."""
    if mode == 'one':
        return None
    if mode == 'zero':
        return set()
    suffixes = {'attn_narrow': ATTN_NARROW, 'attn_full': ATTN_FULL}[mode]
    names = {name for name, _ in _learnable(model) if name.endswith(suffixes)}
    assert names, (mode, 'no attention quantizer matched')
    return names


def set_weight_bits(model, bits):
    """[D22] NB only: set every learned-width (kbi) kernel to `bits` per weight (b = bits, i
    unchanged). Binary kernels are fixed at 1 bit and are never touched."""
    from bnhgq2 import qat
    layers = qat.kbi_weight_layers(model)
    assert layers, 'weight_bits set on a model without learned-width weights'
    for layer in layers.values():
        _full(layer.kq.quantizer._b, bits)
    return len(layers)


def set_floor(model, mode, sample, max_iter=48, weight_bits=None):
    from bnhgq2.ebops_calc import compute_ebops
    held = one_bit_names(model, mode)
    if weight_bits is not None:
        set_weight_bits(model, weight_bits)

    def at_one(name, q):
        return (held is None or name in held) and hasattr(q, '_f')
    for _, q in _learnable(model):
        if hasattr(q, '_f'):
            fmin = q.f_constraint.min_value
            if q.overflow_mode == 'WRAP':
                _full(q._f, fmin)
            else:
                _full(q._i, q.i_constraint.min_value)
                _full(q._f, fmin)
        else:
            _full(q._b, q.b_constraint.min_value)
    cost = compute_ebops(model, sample)
    if mode != 'zero':
        for _ in range(max_iter):
            changed = False
            for name, q in _learnable(model):
                if at_one(name, q) and q.overflow_mode == 'WRAP':
                    want = 1.0 - np.asarray(q.i)
                    if not np.array_equal(np.asarray(q._f), want):
                        q._f.assign(want.astype('float32'))
                        changed = True
            cost = compute_ebops(model, sample)
            if not changed:
                break
    check = {}
    for name, q in _learnable(model):
        bits = np.asarray(q.bits).ravel()
        if hasattr(q, '_f'):
            expect = (1 if at_one(name, q) and mode != 'zero' else 0) if q.overflow_mode == 'WRAP' else np.asarray(q.k).ravel()
        else:
            expect = q.b_constraint.min_value
        if hasattr(q, 'min_bits'):
            # H3 quant.attn_bit_floor: a floored quantizer never reads below its floor
            expect = np.maximum(expect, q.min_bits)
        ok = bool(np.all(bits == expect))
        check[name] = {'bits_min': float(bits.min()), 'bits_max': float(bits.max()), 'ok': ok,
                       'held_at_one_bit': bool(at_one(name, q) and mode != 'zero')}
        assert ok, (name, mode, bits.min(), bits.max())
    return cost, check


def floors(cfg, n_sample=256, seed=0, with_attn_rule=True):
    import keras
    from bnhgq2.compat import apply_keras_compat
    from bnhgq2 import qat
    from bnhgq2.ebops_calc import compute_ebops
    apply_keras_compat()
    A = cfg['arch']
    sample = np.random.default_rng(seed).standard_normal((n_sample, A['n_part'], A['n_feat'])).astype('float32')
    out = {'name': cfg['name'], 'target_ebops': cfg['train']['ebops']['pid']['target_ebops'],
           'quant': {k: cfg['quant'].get(k) for k in ('act_overflow', 'softmax_quant', 'softmax_out_bits',
                                                      'softmax_out_i', 'act_granularity', 'act_bits')},
           'arch': {k: A[k] for k in ('n_part', 'd_model', 'n_heads', 'n_layers', 'ffn_dim', 'pos_enc')},
           'sample': f'synthetic standard normal, n={n_sample}, seed={seed}'}
    nb = cfg['quant']['weight'] == 'kbi_learnable'
    # [D22] NB: learned weight widths also move, so the activation floors are traced with the
    # weights at their init width (b0 4, the modes above) and at 0 and 1 bit per weight.
    nb_modes = (('zero_w0', 'zero', 0), ('one_w1', 'one', 1), ('one_w0', 'one', 0)) if nb else ()
    modes = [(m, m, None) for m in ('init', 'zero', 'one') + (('attn_narrow', 'attn_full') if with_attn_rule else ())]
    for key, mode, weight_bits in modes + list(nb_modes):
        keras.backend.clear_session()
        model, taps = qat.build_qat_model(cfg, seed=1)
        if mode == 'init':
            qat.calibrate_activations(model, taps, sample, cfg['quant']['act_bits'])
            cost, check = compute_ebops(model, sample), None
        else:
            cost, check = set_floor(model, mode, sample, weight_bits=weight_bits)
        mode = key
        out[mode] = {'total': cost['total'], 'per_layer': cost['per_layer']}
        if check is not None:
            out[mode]['width_check'] = {'n_quantizers': len(check), 'all_ok': all(v['ok'] for v in check.values()),
                                        'held_at_one_bit': sorted(k for k, v in check.items() if v['held_at_one_bit'])}
        out['parameters'] = int(model.count_params())
        del model
    target = out['target_ebops']
    out['weights_only_rule'] = {'total': out['zero']['total'],
                                'why': ('learned-width kernels (NB); a 0-bit input costs 0 EBOPs whatever the weight width'
                                        if nb else 'binary kernels are fixed at 1 bit; a 0-bit input costs 0 EBOPs')}
    out['headroom'] = {str(budget): {mode: budget - out[mode]['total']
                                     for mode in ('zero', 'one', 'attn_narrow', 'attn_full') if mode in out}
                       for budget in sorted({target, 350000, 250000})}
    out['zero_floor_over_target'] = out['zero']['total'] / target
    out['one_bit_alive_over_target'] = out['one']['total'] / target
    out['headroom_at_zero_floor'] = target - out['zero']['total']
    out['status'] = 'STATIC_INFEASIBLE' if out['zero']['total'] >= target else 'STATIC_FEASIBLE'
    if 'attn_bit_floor' in cfg['quant']:   # H3: record the floor the widths were traced under
        out['quant']['attn_bit_floor'] = cfg['quant']['attn_bit_floor']
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('configs', nargs='+', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    results = []
    for path in args.configs:
        r = floors(json.loads(path.read_text()))
        results.append(r)
        if 'zero_w0' in r:
            print('STATIC_FLOOR_NB', r['name'], 'zero_w0', r['zero_w0']['total'],
                  'one_w1', r['one_w1']['total'], 'one_w0', r['one_w0']['total'], flush=True)
        print('STATIC_FLOOR', r['name'], 'init', r['init']['total'], 'zero', r['zero']['total'],
              'one_bit_alive', r['one']['total'],
              'attn_narrow', r.get('attn_narrow', {}).get('total'), 'attn_full', r.get('attn_full', {}).get('total'),
              'target', r['target_ebops'], r['status'], flush=True)
    if args.out:
        args.out.write_text(json.dumps(results, indent=2) + '\n')


if __name__ == '__main__':
    main()
