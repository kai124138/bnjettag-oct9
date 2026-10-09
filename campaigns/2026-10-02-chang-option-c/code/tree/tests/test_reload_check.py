"""[D20] stored-variable post-reload check: equal after save/load, catches a moved width,
agrees with a reset retrace of the same rows. CPU, synthetic."""
import os

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

from test_d20_trace import arrays
from test_resume_cadence import tiny_cfg


def test_stored_check(tmp_path):
    import keras
    from bnhgq2 import ablation
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    (xt, _, _, _), _ = arrays()
    keras.backend.clear_session()
    model, _ = ablation.matching_initialization(tiny_cfg(), xt[:256], 1)
    cost = ablation.compute_ebops(model, xt)
    model.save(tmp_path / 'm.keras')
    loaded = keras.models.load_model(tmp_path / 'm.keras', compile=False)
    stored = ablation.stored_state_ebops(model, loaded)
    assert stored['total'] == cost['total']
    assert ablation.compute_ebops(loaded, xt)['total'] == cost['total']   # the retrace agrees
    # a moved WRAP integer width (what a different trace sample would do) is caught
    wrap_i = [v for v in loaded.weights if v.path.endswith('/i') or v.path.endswith('_i')]
    assert wrap_i, [v.path for v in loaded.weights][:20]
    wrap_i[0].assign(np.asarray(wrap_i[0]) + 1)
    with pytest.raises(AssertionError):
        ablation.stored_state_ebops(model, loaded)


def test_run_training_stored_mode(tmp_path):
    from bnhgq2 import ablation
    cfg = tiny_cfg()
    cfg['train'].update(epochs=2, ebops_trace_sample='train_full', ebops_reload_check='stored')
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    cfg['train']['ebops_reload_check'] = 'nope'
    with pytest.raises(ValueError):
        ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'bad')
