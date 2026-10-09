"""body-deepsets: binary {-1,+1}-weight Deep Sets body (Delta M006; card A09). T2, new builder.

Topology (dimensions only, re-implemented; no code lifted: HGQ2-examples has no LICENSE).
Read from reference-code/HGQ2-examples/jsc150/model.py:77-104 (`get_gnn`) at commit
6cdc6e34d4cea0fb0f2e3ac502e2bfea01b2a805:
  phi1   per constituent  F -> 64, ReLU                       (model.py:88)
  phi2   per constituent  64 -> 64, ReLU  ("s")               (model.py:89)
  ctx    sum over constituents x 2^-round(log2 N), then 64 -> 64, ReLU  ("d")   (model.py:87, 90-92)
  add    s + d, broadcast over constituents                   (model.py:93)
  phi3   per constituent  64 -> 64, ReLU                      (model.py:95)
  pool   sum over constituents x 1/16                          (model.py:96)
  rho    64 -> 64 -> 32 -> 16, ReLU; out 16 -> C               (model.py:97-100)

Deliberate deviations from the reference (they can move a number; stated, not hidden):
  * No batch normalization. The reference fuses BN into every dense except the output
    (QEinsumDenseBatchnorm). A fused BN folds gamma/sigma into the kernel, so the deployed
    weights stop being +-beta (code-surface §3 row 11); the anchor transformer is norm-free
    (arch.norm none), and so is this body.
  * Weights are BitNet absmean binary (qat.bitnet_binary_ste via BitQEinsumDense/BitQDense),
    not HGQ learned-width fixed point. Biases are float, as in the transformer (qat.py:398).
  * Activation quantizers are the anchor's (qat._free_act: learned widths, SAT, from the
    act_bits grid, MSE-calibrated), not the reference's WRAP datalane. When the anchor [A20]
    quantizer set lands, this builder must take its act_iq factory instead (WIRING.md).
  * Pooling layers carry no input quantizer (enable_iq=False), as the transformer's GAP.
  * No positional encoding: the body is permutation invariant by construction.

Config: cfg['arch']['body'] == 'deepsets'; cfg['arch']['deepsets_dims'] optional dict with the
keys of DEFAULT_DIMS (delta.json leaves it as a placeholder string for the wave STUDY; the
generator refuses the placeholder, so the STUDY must write either this default or its own).
"""
from __future__ import annotations

from math import log2

import keras
import numpy as np
from hgq.config import LayerConfigScope
from hgq.layers.ops.accum import QSum

from bnhgq2 import qat

# Sun et al. get_gnn dims (model.py:88-100). A proposal for the wave STUDY, not a decision.
DEFAULT_DIMS = {'phi': [64, 64], 'ctx': 64, 'phi_post': [64], 'rho': [64, 32, 16], 'pool_scale': 1.0 / 16}


def dims_for(cfg):
    dims = dict(DEFAULT_DIMS)
    given = cfg['arch'].get('deepsets_dims')
    if given is None:
        return dims
    if not isinstance(given, dict):
        raise ValueError(f'arch.deepsets_dims must be a dict of {sorted(DEFAULT_DIMS)} or absent; got {given!r}')
    unknown = set(given) - set(DEFAULT_DIMS)
    if unknown:
        raise ValueError(f'arch.deepsets_dims has unknown keys {sorted(unknown)}')
    dims.update(given)
    if dims['phi'][-1] != dims['ctx']:
        raise ValueError('context width must equal the last phi width (broadcast add)')
    if not log2(dims['pool_scale']).is_integer():
        raise ValueError('pool_scale must be a power of two (a shift in hardware)')
    return dims


def expected_binary_layers(cfg):
    """Binary layer names of the Deep Sets body (for ablation.binary_gate / expected_binary_layers)."""
    d = dims_for(cfg)
    names = {f'ds_phi{i + 1}' for i in range(len(d['phi']))} | {'ds_ctx'}
    names |= {f'ds_post{i + 1}' for i in range(len(d['phi_post']))}
    names |= {f'ds_rho{i + 1}' for i in range(len(d['rho']))} | {'ds_out'}
    return names


def build_deepsets_model(cfg: dict, seed: int, enable_ebops: bool = True):
    """Return (model, taps) like qat.build_qat_model; taps feed qat.calibrate_activations."""
    if cfg['arch'].get('body') != 'deepsets':
        raise ValueError("build_deepsets_model needs arch.body == 'deepsets'")
    if cfg['quant']['weight'] != 'binary_absmean':
        raise ValueError('the Deep Sets body is built binary only (binary_absmean)')
    keras.utils.set_random_seed(int(seed))
    A, Q = cfg['arch'], cfg['quant']
    T, F, C = A['n_part'], A['n_feat'], A['n_classes']
    d = dims_for(cfg)
    ab = int(Q['act_bits'])
    act_calib = str(Q.get('act_calib', 'frozen')).lower()
    granularity = Q.get('act_granularity', 'tensor')
    if granularity not in ('tensor', 'channel'):
        raise ValueError(f'Unsupported act_granularity: {granularity}')
    taps = {}

    def act_iq(axes=(-1,)):
        if act_calib == 'free':
            return qat._free_act(ab, qat._PROV_I, float(Q.get('act_bw_l1', 1e-8)),
                                 heterogeneous_axis=axes if granularity == 'channel' else ())
        return qat._trainable_act(ab, qat._PROV_I) if act_calib == 'trainable' else qat._static_act(ab, qat._PROV_I)

    def per_particle(name, units, x, n_out):
        taps[name] = x
        return qat.BitQEinsumDense('bnc,cC->bnC', output_shape=(n_out, units), bias_axes='C',
                                   iq_conf=act_iq(), kq_conf=qat._binary_kq(), bq_conf=qat._dummy('bias'),
                                   name=name)(x)

    def dense(name, units, x):
        taps[name] = x
        return qat.BitQDense(units, use_bias=True, iq_conf=act_iq(), kq_conf=qat._binary_kq(),
                             bq_conf=qat._dummy('bias'), name=name)(x)

    relu = keras.layers.ReLU
    with LayerConfigScope(enable_ebops=enable_ebops, beta0=float(Q.get('beta0', 0.0))):
        x_in = keras.Input((T, F), name='input_1')
        if len(d['phi']) < 2:
            raise ValueError('deepsets_dims.phi needs at least two layers (phi1, then s)')
        x = x_in
        for i, units in enumerate(d['phi']):
            x = relu(name=f'ds_phi{i + 1}_act')(per_particle(f'ds_phi{i + 1}', units, x, T))
            if i == len(d['phi']) - 2:
                s_in = x                       # the branch point: ctx pools phi[-2]'s output
        s = x
        ctx = QSum(axes=1, scale=2.0 ** -round(log2(T)), keepdims=True, enable_iq=False, name='ds_ctx_pool')(s_in)
        ctx = relu(name='ds_ctx_act')(per_particle('ds_ctx', d['ctx'], ctx, 1))
        x = keras.layers.Add(name='ds_add_ctx')([s, ctx])
        for i, units in enumerate(d['phi_post']):
            x = relu(name=f'ds_post{i + 1}_act')(per_particle(f'ds_post{i + 1}', units, x, T))
        x = QSum(axes=1, scale=float(d['pool_scale']), keepdims=False, enable_iq=False, name='ds_pool')(x)
        for i, units in enumerate(d['rho']):
            x = relu(name=f'ds_rho{i + 1}_act')(dense(f'ds_rho{i + 1}', units, x))
        out = dense('ds_out', C, x)
        model = keras.Model(x_in, out, name=cfg['name'])
    return model, taps


def deepsets_initialization(cfg, sample, seed):
    """Builder with the (model, evidence) signature of ablation.matching_initialization.

    There is no transformer reference to copy from (unpaired by design, Delta M006 pairing =
    Welch), so the model keeps its seed-derived init and is calibrated on `sample`."""
    from bnhgq2.ablation import array_hash
    model, taps = build_deepsets_model(cfg, seed)
    site_i = qat.calibrate_activations(model, taps, np.asarray(sample), int(cfg['quant']['act_bits']))
    evidence = {'body': 'deepsets', 'dims': dims_for(cfg), 'calibrated_sites': site_i,
                'matched_weight_paths': [], 'equivalent_to_weight_reference': False,
                'kernel_hashes': {v.path: array_hash(v.numpy()) for v in model.weights
                                  if v.name in ('kernel', 'bias')}}
    return model, evidence


def binary_gate(model, cfg):
    """Exactly two symmetric non-zero values per binary layer, and the right layer set."""
    values = qat.effective_weight_values(model)
    assert set(values) == expected_binary_layers(cfg), (sorted(values), sorted(expected_binary_layers(cfg)))
    for name, v in values.items():
        assert len(v) == 2 and not (v == 0).any() and np.isclose(v[0], -v[1]), f'binary gate failed on {name}: {v}'
