"""Shared fixtures: the stand-in base config (read from the sha-verified screen tarball) and
synthetic inputs. Synthetic data only; nothing here is a result."""
import copy
import os
import sys
from pathlib import Path

import numpy as np
import pytest

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))

from bnhgq2.compat import apply_keras_compat  # noqa: E402

apply_keras_compat()


@pytest.fixture(scope='session')
def standin():
    from generate_delta import load_standin
    cfg, _ = load_standin()
    return cfg


def small_cfg(base, n_part=8, **arch):
    cfg = copy.deepcopy(base)
    cfg['arch']['n_part'] = n_part
    cfg['arch'].update(arch)
    cfg['train']['batch'] = 64
    return cfg


def synth(n, n_part, n_feat=3, n_classes=5, seed=0):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, n_part, n_feat)).astype('float32')
    y = np.eye(n_classes, dtype='float32')[rng.integers(0, n_classes, n)]
    return x, y


def assert_binary(model, names=None):
    from bnhgq2 import qat
    values = qat.effective_weight_values(model)
    if names is not None:
        assert set(values) == set(names), (sorted(values), sorted(names))
    assert values
    for name, v in values.items():
        assert len(v) == 2 and not (v == 0).any() and np.isclose(v[0], -v[1]), (name, v)
    return values
