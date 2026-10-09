import copy

import keras
import numpy as np
import pytest

from conftest import assert_binary, synth
from newmods import deepsets


def cfg_for(standin, n_part=64, dims=None):
    cfg = copy.deepcopy(standin)
    cfg['arch'].update(n_part=n_part, body='deepsets')
    if dims is not None:
        cfg['arch']['deepsets_dims'] = dims
    cfg['train']['batch'] = 64
    return cfg


def test_build_binary_and_invariant(standin):
    cfg = cfg_for(standin)
    x, _ = synth(128, 64)
    model, ev = deepsets.deepsets_initialization(cfg, x, 1)
    assert_binary(model, deepsets.expected_binary_layers(cfg))
    deepsets.binary_gate(model, cfg)
    assert model.output_shape == (None, 5)
    perm = np.random.default_rng(1).permutation(64)
    a = np.asarray(model(x[:16], training=False))
    b = np.asarray(model(x[:16, perm], training=False))
    np.testing.assert_allclose(a, b, atol=1e-5)           # permutation invariant (sum order only)
    assert not any(v.name == 'pos_table' for v in model.weights)


def test_one_step_reload_and_cost(standin, tmp_path):
    from bnhgq2 import ablation
    from bnhgq2.ebops_calc import compute_ebops
    cfg = cfg_for(standin)
    x, y = synth(128, 64)
    model, _ = deepsets.deepsets_initialization(cfg, x, 1)
    before = [v.numpy().copy() for v in model.trainable_variables]
    opt = ablation.optimizer_for(cfg, model)
    step = ablation.make_epoch_step(model, opt, x[:64], y[:64], cfg)
    totals = step(np.arange(64, dtype='int32')).numpy()
    assert np.isfinite(totals).all()
    assert any(not np.array_equal(b, v.numpy()) for b, v in zip(before, model.trainable_variables))
    deepsets.binary_gate(model, cfg)
    cost = compute_ebops(model, x[:32])['total']
    assert np.isfinite(cost) and cost > 0
    path = tmp_path / 'ds.keras'
    model.save(path)
    loaded = keras.models.load_model(path, compile=False)
    np.testing.assert_allclose(loaded(x[:16], training=False), model(x[:16], training=False), atol=1e-7, rtol=0)
    assert compute_ebops(loaded, x[:32])['total'] == cost


def test_dims_validation(standin):
    with pytest.raises(ValueError):
        deepsets.dims_for(cfg_for(standin, dims='per Sun et al.'))
    with pytest.raises(ValueError):
        deepsets.dims_for(cfg_for(standin, dims={'pool_scale': 0.1}))
    with pytest.raises(ValueError):
        deepsets.dims_for(cfg_for(standin, dims={'ctx': 32}))
    assert deepsets.dims_for(cfg_for(standin))['rho'] == [64, 32, 16]
