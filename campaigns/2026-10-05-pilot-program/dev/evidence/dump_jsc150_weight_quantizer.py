"""[A22] Resolve the jsc150 xfm weight-quantizer config on the pinned hgq2 0.1.9.

get_transformer's QEinsumDenseBatchnorm('...c,cC->...C') does not build on the pin (ValueError in
_compute_fused_einsum_specs), so the full xfm cannot be built. Instead: enter exactly the scope stack
of get_model('xfm', 7, 7, 1e-8, 64, True) + get_transformer, build the layer types xfm uses for kernels
(QEinsumDense, QMultiHeadAttention) on xfm shapes, and dump each built kernel quantizer."""
import json, numpy as np, keras
from hgq.config import LayerConfigScope, QuantizerConfig, QuantizerConfigScope
from hgq.constraints import Min, MinMax
from hgq.layers import QEinsumDense, QMultiHeadAttention
from hgq.regularizers import MonoL1
keras.utils.set_random_seed(1)
bw_k, bw_a, l1_reg = 7, 7, 1e-8          # run_train.py:76
homogeneous_axis = (0,)
scope0 = QuantizerConfigScope(default_q_type='kbi', b0=bw_k, overflow_mode='wrap', i0=0,
                              fr=MonoL1(l1_reg), ir=MonoL1(l1_reg), i_decay_speed=1e-3)
scope1 = QuantizerConfigScope(default_q_type='kif', place='datalane', overflow_mode='wrap', f0=bw_a,
                              fr=MonoL1(l1_reg), ic=MinMax(0, 12))
scope2 = LayerConfigScope(beta0=0)
def desc(q):
    d = {'class': type(q).__name__}
    for a in ('_k', '_b', '_i', '_i_decay_speed'):
        v = getattr(q, a, None)
        if v is not None:
            arr = np.asarray(v)
            d[a] = {'shape': list(arr.shape), 'unique': [float(x) for x in np.unique(arr)][:6],
                    'trainable': bool(getattr(v, 'trainable', False))}
    for a in ('overflow_mode', 'round_mode'):
        d[a] = getattr(q, a, None)
    for a in ('b_constraint', 'i_constraint', 'b_regularizer', 'i_regularizer'):
        v = getattr(q, a, None)
        d[a] = None if v is None else {'type': type(v).__name__, **(v.get_config() if hasattr(v, 'get_config') else {})}
    bm = getattr(q, 'bw_mapper', None)
    d['bw_mapper'] = None if bm is None else type(bm).__name__
    return d
out = {}
with scope0, scope1, scope2:
    with (QuantizerConfigScope(place=('weight', 'bias'), overflow_mode='SAT_SYM', b0=4, f0=4),
          QuantizerConfigScope(place='datalane', homogeneous_axis=homogeneous_axis),
          QuantizerConfigScope(place='table', homogeneous_axis=homogeneous_axis, bc=Min(4))):
        cfgw = QuantizerConfig(place='weight')
        out['QuantizerConfig(place=weight)'] = {k: repr(v) for k, v in cfgw.config.items()} if hasattr(cfgw, 'config') else repr(cfgw)
        out['q_type'] = getattr(cfgw, 'q_type', None)
        x = keras.Input((64, 24))
        ffn = QEinsumDense('btc,cC->btC', (64, 32), bias_axes='C', name='ffn_like')
        y = ffn(x)
        mha = QMultiHeadAttention(2, 16, dropout=0.0, name='mha')
        z = mha(x, x)
for ly in [ffn] + [l for l in mha._flatten_layers(include_self=False, recursive=True)]:
    kq = getattr(ly, 'kq', None)
    if kq is None:
        continue
    q = getattr(kq, 'quantizer', kq)
    out[ly.name] = desc(q)
    bq = getattr(ly, 'bq', None)
    if bq is not None:
        out[ly.name + '/bias'] = desc(getattr(bq, 'quantizer', bq))
print(json.dumps(out, indent=1, default=str))
