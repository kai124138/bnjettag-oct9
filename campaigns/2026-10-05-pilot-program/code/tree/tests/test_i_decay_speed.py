"""[D25] opt-in quant.i_decay_speed (patch 0024). CPU, generated chang0926 configs, synthetic input."""
import copy
import json
import os
import tempfile
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import keras
import numpy as np
import pytest

from bnhgq2 import ablation, qat

CFG = Path(__file__).resolve().parents[1] / 'campaigns' / 'chang0926' / 'configs'


def _cfg(name):
    return json.loads((CFG / f'{name}.json').read_text())


def _weights(model):
    return [(v.path, np.asarray(v).tobytes()) for v in model.weights]


def test_key_sets_every_enumerated_quantizer():
    cfg = _cfg('chang0926-e1-n64-s1')
    assert cfg['quant']['i_decay_speed'] == 0.001
    keras.backend.clear_session()
    model, _ = qat.build_qat_model(cfg, seed=1)
    decay = ablation.i_decay_speeds(model)
    assert decay and set(decay.values()) == {float(np.float32(0.001))}
    assert sum(v.name == 'i_decay_speed' for v in model.weights) == len(decay)


def test_absent_key_is_the_hgq2_default_and_byte_identical():
    cfg = _cfg('chang0926-e1-n64-s1')
    bare = copy.deepcopy(cfg)
    bare['quant'].pop('i_decay_speed')
    keras.backend.clear_session()
    m0, _ = qat.build_qat_model(bare, seed=1)
    assert set(ablation.i_decay_speeds(m0).values()) == {float(np.float32(0.01))}
    keras.backend.clear_session()
    m1, _ = qat.build_qat_model(cfg, seed=1)
    w0, w1 = _weights(m0), _weights(m1)
    assert [p for p, _ in w0] == [p for p, _ in w1]
    differ = {p for (p, a), (_, b) in zip(w0, w1) if a != b}
    assert differ and all(p.endswith('/i_decay_speed') for p in differ)


def test_key_without_wrap_raises():
    cfg = _cfg('chang0926-cprime-n64-s1')
    assert 'i_decay_speed' not in cfg['quant']
    cfg['quant']['i_decay_speed'] = 0.001
    with pytest.raises(ValueError, match='i_decay_speed'):
        qat.build_qat_model(cfg, seed=1)


@pytest.mark.parametrize('bad', [0, -0.001, float('nan'), True, '0.001'])
def test_bad_values_raise(bad):
    cfg = _cfg('chang0926-e1-n64-s1')
    cfg['quant']['i_decay_speed'] = bad
    with pytest.raises(ValueError, match='i_decay_speed'):
        qat.build_qat_model(cfg, seed=1)


def test_value_survives_save_reload():
    cfg = _cfg('chang0926-e1-n64-s1')
    keras.backend.clear_session()
    model, _ = qat.build_qat_model(cfg, seed=1)
    model(np.zeros((2, 64, 3), 'float32'), training=False)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'm.keras'
        model.save(path)
        loaded = keras.models.load_model(path, compile=False)
    assert ablation.i_decay_speeds(loaded) == ablation.i_decay_speeds(model)
