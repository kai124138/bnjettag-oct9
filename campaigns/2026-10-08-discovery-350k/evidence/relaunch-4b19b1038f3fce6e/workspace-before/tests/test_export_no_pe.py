"""pos_enc none: qat_binz_pe returns a zero PE table instead of failing (convert_binary:405)."""
import copy
import json
import os
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np

HERE = Path(__file__).resolve().parents[1]
BASE = json.loads((HERE / 'configs' / 'const0922-a07-n64-s1-fast50-fp32.json').read_text())


def test_no_pe_export_table():
    import convert_binary
    from bnhgq2 import qat
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    cfg = copy.deepcopy(BASE)
    cfg['arch'].update(n_part=8, pos_enc='none')
    model, _ = qat.build_qat_model(cfg, seed=1)
    assert not any(layer.name == 'pos_enc' for layer in model.layers)
    binz, pe, names = convert_binary.qat_binz_pe(model, cfg)
    assert pe.shape == (8, 32) and not pe.any()
    cfg['arch']['pos_enc'] = 'learned'
    model, _ = qat.build_qat_model(cfg, seed=1)
    _, pe, _ = convert_binary.qat_binz_pe(model, cfg)
    assert pe.shape == (8, 32) and pe.any()
