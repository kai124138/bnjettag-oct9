"""Linformer layer tests on a minimal one-block binary model.

The model below re-creates the closures of qat.build_qat_model (dense_einsum, einsum, softmax,
stream_iq) from qat's own quantizer factories, because they are local to that function; the
wiring patch passes the real closures (WIRING.md). Test scaffolding only, not a fork."""
import keras
import numpy as np
from hgq.config import LayerConfigScope
from hgq.layers import QGlobalAveragePooling1D, QSoftmax
from hgq.quantizer import QuantizerConfig

from bnhgq2 import qat
from conftest import assert_binary, synth
from newmods.linformer import linformer_attention, linformer_binary_layers

T, F, D, H, K, C = 16, 3, 16, 2, 4, 5
E = D // H


def build(seed=1):
    keras.utils.set_random_seed(seed)

    def act(axes=(-1,)):
        return qat._free_act(8, qat._PROV_I, 1e-8, heterogeneous_axis=())

    def dense_einsum(name, eq, out_shape, x, bias_axes=None):
        return qat.BitQEinsumDense(eq, output_shape=out_shape, bias_axes=bias_axes, iq_conf=act(),
                                   kq_conf=qat._binary_kq(),
                                   bq_conf=qat._dummy('bias') if bias_axes else None, name=name)(x)

    def einsum(name, eq, xs, iqs):
        from hgq.layers.ops.einsum import QEinsum
        return QEinsum(eq, iq_confs=iqs, name=name)(xs)

    def softmax(name, x, scale):
        return QSoftmax(axis=-1, stable=True, input_scaler=float(scale),
                        exp_iq_conf=qat._static_act(10, 6),
                        inv_iq_conf=QuantizerConfig('kif', 'datalane', k0=0, i0=4, f0=8, round_mode='RND_CONV',
                                                    overflow_mode='SAT', trainable=False, heterogeneous_axis=()),
                        exp_oq_conf=qat._table(1, 11), inv_oq_conf=qat._table(1, 11), name=name)(x)

    attn_iq = QuantizerConfig('kif', 'datalane', k0=0, i0=1, f0=9, round_mode='RND_CONV', overflow_mode='SAT',
                              trainable=False, heterogeneous_axis=())
    with LayerConfigScope(enable_ebops=True, beta0=1e-7):
        x_in = keras.Input((T, F))
        h = dense_einsum('input_proj', 'btf,fd->btd', (T, D), x_in, 'td')
        q = dense_einsum('bit_block_0_attn_Wq', 'btd,dhe->bthe', (T, H, E), h)
        k = dense_einsum('bit_block_0_attn_Wk', 'btd,dhe->bthe', (T, H, E), h)
        v = dense_einsum('bit_block_0_attn_Wv', 'btd,dhe->bthe', (T, H, E), h)
        ctx = linformer_attention('bit_block_0', q, k, v, lin_k=K, dense_einsum=dense_einsum, einsum=einsum,
                                  softmax=softmax, attn_iq=attn_iq, stream_iq=lambda: act((-2, -1)),
                                  scale=1.0 / np.sqrt(E))
        wo = dense_einsum('bit_block_0_attn_Wo', 'bthe,hed->btd', (T, D), ctx, 'd')
        h = keras.layers.Add()([h, wo])
        h = QGlobalAveragePooling1D(enable_iq=False)(h)
        out = qat.BitQDense(C, iq_conf=act(), kq_conf=qat._binary_kq(), bq_conf=qat._dummy('bias'), name='head')(h)
    return keras.Model(x_in, out)


def test_shapes_binary_step_reload(tmp_path):
    from bnhgq2.ebops_calc import compute_ebops
    model = build()
    names = {ly.name for ly in model.layers}
    assert {'bit_block_0_attn_Elin', 'bit_block_0_attn_Flin'} <= names
    vals = assert_binary(model)
    assert 'bit_block_0_attn_Elin' in vals and 'bit_block_0_attn_Flin' in vals
    assert tuple(model.get_layer('bit_block_0_attn_Elin')._kernel.shape) == (T, K)
    assert tuple(model.get_layer('bit_block_0_attn_softmax').output.shape) == (None, H, T, K)
    x, y = synth(64, T)
    opt = keras.optimizers.Adam(1e-3)
    with __import__('tensorflow').GradientTape() as tape:
        loss = keras.losses.CategoricalCrossentropy(from_logits=True)(y, model(x, training=True))
    grads = tape.gradient(loss, model.trainable_variables)
    assert grads[[v.path for v in model.trainable_variables].index(model.get_layer('bit_block_0_attn_Elin')._kernel.path)] is not None
    opt.apply_gradients(zip(grads, model.trainable_variables))
    assert np.isfinite(float(loss))
    assert_binary(model)
    cost = compute_ebops(model, x[:32])['total']
    assert np.isfinite(cost) and cost > 0
    model.save(tmp_path / 'lin.keras')
    loaded = keras.models.load_model(tmp_path / 'lin.keras', compile=False)
    np.testing.assert_allclose(loaded(x[:8], training=False), model(x[:8], training=False), atol=1e-7, rtol=0)


def test_binary_layer_names():
    cfg = {'arch': {'attn_kind': 'linformer', 'n_layers': 2}}
    assert linformer_binary_layers(cfg) == {'bit_block_0_attn_Elin', 'bit_block_0_attn_Flin',
                                            'bit_block_1_attn_Elin', 'bit_block_1_attn_Flin'}
    assert linformer_binary_layers({'arch': {'n_layers': 1}}) == set()
