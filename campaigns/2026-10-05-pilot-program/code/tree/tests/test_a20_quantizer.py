"""[A20] unit tests: a WRAP activation channel at relu(i+f) = 0 costs 0 EBOPs and outputs 0;
the SAT channel at its floor still costs 1 bit (the sign bit k). CPU, synthetic inputs."""
import copy
import json
import os
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

HERE = Path(__file__).resolve().parents[1]
BASE = HERE / 'configs' / 'const0922-a07-n64-s1-fast50-fp32.json'


def _layer_model(overflow):
    import keras
    from bnhgq2 import qat
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    keras.utils.set_random_seed(0)
    x = keras.Input((8, 3))
    layer = qat.BitQDense(4, use_bias=True, name='probe',
                          iq_conf=qat._free_act(8, 2, 1e-8, heterogeneous_axis=(-1,), overflow=overflow),
                          kq_conf=qat._binary_kq(), bq_conf=qat._dummy('bias'))
    return keras.Model(x, layer(x)), layer


@pytest.mark.parametrize('overflow,expect_zero', [('WRAP', True), ('SAT', False)])
def test_channel_floor(overflow, expect_zero):
    from hgq.utils import trace_minmax
    model, layer = _layer_model(overflow)
    q = layer.iq.quantizer
    x = np.random.default_rng(1).standard_normal((64, 8, 3)).astype('float32')
    if overflow == 'SAT':
        q._i.assign(np.full(q._i.shape, q.i_constraint.min_value, 'float32'))
    q._f.assign(np.full(q._f.shape, q.f_constraint.min_value, 'float32'))
    total = trace_minmax(model, x, batch_size=64)
    ebops = int(layer.ebops)
    out = np.asarray(layer.iq(x, training=False))
    if expect_zero:
        assert ebops == 0 and total == 0
        assert np.all(np.asarray(q.bits) == 0)
        assert np.all(out == 0)
    else:
        # SAT at i = ic.min, f = fc.min: EBOPs still bill the sign bit k (1 bit per
        # channel), while HGQ2 0.1.9 inference zeroes the output (k + i + f <= 0 branch
        # of FixedPointQuantizerBase.call). Billed but silent: the SAT floor is 1 bit.
        assert np.all(np.asarray(q.bits) == 1)
        assert ebops == 8 * 3 * 4                       # 1 bit x 1-bit weight per MAC
        assert np.all(out == 0)


def test_softmax_internals_learned_and_floor():
    import keras
    from bnhgq2 import qat
    from bnhgq2.ebops_target import activation_quantizers
    cfg = json.loads(BASE.read_text())
    cfg['quant'].update(act_overflow='WRAP', softmax_quant='chang')
    model, _ = qat.build_qat_model(cfg, seed=1)
    names = {n for n, q in activation_quantizers(model) if q.trainable}
    for role in ('exp_iq', 'exp_oq', 'inv_iq', 'inv_oq'):
        assert f'bit_block_0_attn_softmax__{role}' in names
    sm = model.get_layer('bit_block_0_attn_softmax')
    for table in (sm.exp_table, sm.inv_table):
        oq = table.oq.quantizer
        assert oq.b_constraint.min_value == 4 and oq.overflow_mode == 'SAT' and oq.trainable
    ctx = model.get_layer('bit_block_0_attn_ctx')
    assert ctx.iq[0].quantizer.overflow_mode == 'WRAP' and ctx.iq[0].quantizer.trainable


def test_absent_keys_unchanged():
    """No [A20] key => the fixed/SAT build: same trainable set and same quantizer modes."""
    from bnhgq2 import qat
    from bnhgq2.ebops_target import activation_quantizers
    cfg = json.loads(BASE.read_text())
    model, _ = qat.build_qat_model(cfg, seed=1)
    assert all(q.overflow_mode == 'SAT' for _, q in activation_quantizers(model))
    assert not any('__exp_' in n or '__inv_' in n for n, _ in activation_quantizers(model))
    sm = model.get_layer('bit_block_0_attn_softmax')
    assert not sm.exp_table.oq.quantizer.trainable
    assert not model.get_layer('bit_block_0_attn_ctx').iq[0].quantizer.trainable
