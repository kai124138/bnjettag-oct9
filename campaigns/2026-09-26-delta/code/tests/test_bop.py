"""Bop tests. gamma/tau values here are TEST-ONLY, chosen to make flips observable; they are not
proposals for the wave STUDY."""
import keras
import numpy as np
import pytest

from conftest import assert_binary, small_cfg, synth
from newmods.bop import BopAdam, bop_optimizer_for, binary_latents


def test_flip_rule_exact():
    w = keras.Variable(np.array([-1.0, -0.2, 0.3, 1.1], 'float32'), name='w')
    u = keras.Variable(np.array([0.5, -0.5], 'float32'), name='u')
    opt = BopAdam(gamma=1.0, tau=0.5, bop_variables=[w], learning_rate=1e-2, weight_decay=0.01)
    opt.build([w, u])
    g_w = np.array([-1.0, 0.1, 1.0, -1.0], 'float32')      # gamma=1 -> m = g
    opt.apply_gradients([(g_w, w), (np.array([1.0, 1.0], 'float32'), u)])
    # alpha = mean(w) = 0.05; q = [-,-,+,+]; flip where |m|>tau and sign(m)==q: indices 0 and 2
    np.testing.assert_allclose(w.numpy(), [1.1, -0.2, -0.2, 1.1], atol=1e-6)
    assert not np.allclose(u.numpy(), [0.5, -0.5])            # Adam moved u
    assert len(opt.variables) == len(keras.optimizers.Adam().variables) + 4  # same slots as Adam


def test_no_flip_below_threshold():
    w = keras.Variable(np.array([-1.0, 1.0], 'float32'))
    opt = BopAdam(gamma=0.1, tau=0.5, bop_variables=[w], learning_rate=1.0)
    opt.build([w])
    opt.apply_gradients([(np.array([-1.0, 1.0], 'float32'), w)])   # m = 0.1*g, |m| < tau
    np.testing.assert_array_equal(w.numpy(), [-1.0, 1.0])


def test_requires_gamma_tau():
    with pytest.raises(ValueError):
        BopAdam(gamma=None, tau=1e-6)
    with pytest.raises(ValueError):
        BopAdam(gamma=0.0, tau=1e-6)


def test_on_standin_model(standin):
    from bnhgq2 import ablation
    cfg = small_cfg(standin, n_part=8)
    cfg['train'].update(binary_optimizer='bop', bop_gamma=1e-2, bop_tau=1e-8)   # test-only values
    x, y = synth(256, 8)
    model, _ = ablation.matching_initialization(cfg, x, 1)
    latents = binary_latents(model)
    q0 = {v.path: np.where(v.numpy() - v.numpy().mean() >= 0, 1, -1) for v in latents}
    c0 = {v.path: np.abs(v.numpy() - v.numpy().mean()).mean() for v in latents}
    others0 = [v.numpy().copy() for v in model.trainable_variables if all(v is not l for l in latents)]
    opt = bop_optimizer_for(cfg, model)
    plain = ablation.optimizer_for(small_cfg(standin, n_part=8), ablation.matching_initialization(cfg, x, 1)[0])
    assert len(opt.variables) == len(plain.variables)       # checkpoint save/restore by index unchanged
    opt.learning_rate.assign(1e-3)
    step = ablation.make_epoch_step(model, opt, x, y, cfg)
    assert np.isfinite(step(np.arange(256, dtype='int32')).numpy()).all()
    assert_binary(model, ablation.expected_binary_layers(cfg))
    flipped = sum(int((np.where(v.numpy() - v.numpy().mean() >= 0, 1, -1) != q0[v.path]).sum()) for v in latents)
    assert flipped > 0
    for v in latents:                                       # |w - alpha| kept (beta nearly unchanged)
        c1 = np.abs(v.numpy() - v.numpy().mean()).mean()
        assert abs(c1 - c0[v.path]) / c0[v.path] < 0.05, (v.path, c0[v.path], c1)
    others1 = [v.numpy() for v in model.trainable_variables if all(v is not l for l in latents)]
    assert any(not np.array_equal(a, b) for a, b in zip(others0, others1))
