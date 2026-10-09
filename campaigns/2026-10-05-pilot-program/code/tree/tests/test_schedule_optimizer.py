"""[A1] Chang LR schedule values and [A2] optimizer paths (CPU)."""
import copy
import json
import os
from math import isclose
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import pytest

HERE = Path(__file__).resolve().parents[1]
BASE = json.loads((HERE / 'configs' / 'const0922-a07-n64-s1-fast50-fp32.json').read_text())


def chang_cfg():
    cfg = copy.deepcopy(BASE)
    cfg['train'].update(lr=3e-3, lr_schedule='chang_cosine_restarts', lr_cycle_epochs=500,
                        lr_t_mul=1.0, lr_m_mul=1.0, lr_alpha=1e-6, lr_alpha_epochs=10)
    return cfg


def reference(e, eta=3e-3, alpha=1e-6, period=500, hold=10):
    from math import cos, pi
    t = min((e % period) / (period - hold), 1)
    return alpha + 0.5 * (eta - alpha) * (1 + cos(pi * t))


@pytest.mark.parametrize('epoch', [0, 1, 250, 489, 490, 499, 500, 501, 999, 1000, 6500, 6999])
def test_chang_schedule(epoch):
    from bnhgq2.ablation import learning_rate
    assert isclose(learning_rate(chang_cfg(), epoch), reference(epoch), rel_tol=0, abs_tol=1e-15)


def test_chang_schedule_landmarks():
    from bnhgq2.ablation import learning_rate
    cfg = chang_cfg()
    assert learning_rate(cfg, 0) == pytest.approx(3e-3, abs=1e-15)
    assert learning_rate(cfg, 500) == pytest.approx(3e-3, abs=1e-15)
    for e in (490, 495, 499, 990, 6999):
        assert learning_rate(cfg, e) == pytest.approx(1e-6, abs=1e-15)
    assert learning_rate(cfg, 489) > 1e-6
    assert all(learning_rate(cfg, e) >= 2.99e-3 for e in range(10))   # canary sits on the peak


def test_poly_unchanged():
    from bnhgq2.ablation import learning_rate
    tr = BASE['train']
    assert learning_rate(BASE, 0) == tr['lr'] * 1 / tr['warmup_epochs']
    assert learning_rate(BASE, 25) == tr['lr'] * (1 - (25 - 1) / 49)


def test_optimizers():
    import keras
    from bnhgq2 import ablation
    model = keras.Sequential([keras.Input((3,)), keras.layers.Dense(2)])
    cfg = chang_cfg()
    cfg['train']['optimizer'] = 'adam_default'
    opt = ablation.optimizer_for(cfg, model)
    assert (opt.beta_1, opt.beta_2, opt.epsilon, opt.weight_decay, opt.clipvalue) == (0.9, 0.999, 1e-7, None, None)
    cfg['train']['optimizer'] = 'adam_ours'
    opt = ablation.optimizer_for(cfg, model)
    assert (opt.beta_2, opt.weight_decay, opt.clipvalue) == (0.98, 0.01, 1.0)
