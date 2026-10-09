import numpy as np

from conftest import assert_binary, small_cfg, synth
from newmods import diag_attention as da
from newmods import diag_input_proj_rows as dr
from newmods import diag_latent_binary_gap as dg


def test_entropy_ratio_limits():
    n, h, t, s = 3, 2, 4, 4
    uniform = np.full((n, h, t, s), 1 / s)
    assert np.isclose(da.entropy_ratio(uniform)['mean'], 1.0)
    onehot = np.zeros((n, h, t, s)); onehot[..., 0] = 1
    assert np.isclose(da.entropy_ratio(onehot)['mean'], 0.0)
    valid = np.array([[1, 1, 0, 0]] * n, bool)            # 2 valid keys; mass on gated keys dropped
    p = np.tile(np.array([0.1, 0.1, 0.4, 0.4]), (n, h, t, 1))
    r = da.entropy_ratio(p, valid)
    assert np.isclose(r['mean'], 1.0) and r['keys_masked']
    one = np.array([[1, 0, 0, 0]] * n, bool)              # n_valid < 2: no jets used
    assert da.entropy_ratio(p, one)['jets_used'] == 0


def test_attention_diag_on_standin(standin):
    from bnhgq2 import ablation
    cfg = small_cfg(standin, n_part=8)
    x, y = synth(128, 8)
    model, _ = ablation.matching_initialization(cfg, x, 1)
    before = np.asarray(model(x[:16], training=False))
    valid = np.ones((128, 8), bool); valid[:, 6:] = False
    rep = da.run(model, x, y, valid, batch=64)
    (name, layer), = rep['layers'].items()
    assert 0.0 <= layer['mean'] <= 1.0 and len(layer['per_head']) == cfg['arch']['n_heads']
    assert 'delta_accuracy' in rep['ablation']
    with da.uniform_attention(model, valid[:16]):
        abl = np.asarray(model(x[:16], training=False))
    assert not np.allclose(abl, before)
    np.testing.assert_array_equal(np.asarray(model(x[:16], training=False)), before)   # restored


def test_input_proj_rows_synthetic_and_model(standin):
    q = np.array([[1, 1, -1, -1, 1], [1, 1, -1, -1, -1], [1, 1, -1, 1, 1]])
    rep = dr.distinct_rows(q)
    assert rep['n_distinct'] == 4 and rep['n_distinct_up_to_sign'] == 3 and rep['max_distinct'] == 8
    from bnhgq2 import ablation
    cfg = small_cfg(standin, n_part=8)
    x, _ = synth(64, 8)
    model, _ = ablation.matching_initialization(cfg, x, 1)
    r = dr.from_model(model)
    assert r['fan_in'] == 3 and r['n_channels'] == cfg['arch']['d_model'] and 1 <= r['n_distinct'] <= 8
    kq = dr.sign_patterns(model.get_layer('input_proj')._kernel.numpy())
    eff = model.get_layer('input_proj').qkernel.numpy()
    np.testing.assert_array_equal(np.sign(eff), kq)       # same sign as the forward binarizer


def test_latent_gap_context(standin):
    from bnhgq2 import ablation
    cfg = small_cfg(standin, n_part=8)
    x, y = synth(128, 8)
    model, _ = ablation.matching_initialization(cfg, x, 1)
    before = np.asarray(model(x[:16], training=False))
    with dg.latent_kernels():
        lat = np.asarray(model(x[:16], training=False))
    assert not np.allclose(lat, before)
    np.testing.assert_array_equal(np.asarray(model(x[:16], training=False)), before)
    assert_binary(model, ablation.expected_binary_layers(cfg))
    rep = dg.run(model, x, y, batch=64)
    assert rep['n'] == 128 and 0 <= rep['accuracy_latent'] <= 1
