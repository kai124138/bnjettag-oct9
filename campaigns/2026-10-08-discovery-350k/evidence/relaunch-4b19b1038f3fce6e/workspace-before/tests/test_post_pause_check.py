"""PREFLIGHT gate v1 (2026-09-27): the post-pause check of run_study.train on a keyed [D20]
WRAP config. Trains a tiny model 2 epochs with stop_after=2 (full-split trace, stored reload
check, [D25] i_decay_speed), then runs run_study.verify_selected, the block train() runs after
the pause (GPU/TF32 asserts stay in train()). It must print CHECKPOINT_VERIFICATION_PASS.
The pre-fix check (retrace on arrays[0][:256]) is shown to fail on the same checkpoint.
CPU, synthetic, seconds; nothing here is a result."""
import json
import os

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

from test_d20_trace import arrays
from test_resume_cadence import tiny_cfg


def d20_cfg(reload_check='stored'):
    cfg = tiny_cfg()
    cfg['quant']['i_decay_speed'] = 0.001
    cfg['train'].update(epochs=5, ebops_trace_sample='train_full')
    if reload_check is not None:
        cfg['train']['ebops_reload_check'] = reload_check
    return cfg


def paused(tmp_path, cfg, n_train=2000):
    from bnhgq2 import ablation
    (xt, yt, xv, yv), info = arrays(n_train=n_train)
    info = {**info, 'array_sha256': {'y_val': ablation.array_hash(yv)}}
    state = ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path, stop_after=2)
    assert state['completed_epochs'] == 2 and not (tmp_path / 'COMPLETE.json').exists()
    return (xt, yt, xv, yv), info, state


def verify(tmp_path, cfg, data, info, state):
    import time
    import run_study
    row = {'name': cfg['name'], 'file': 'unit.json'}
    return run_study.verify_selected(cfg, row, tmp_path, state, data, info, {'sha256': 'unit'},
                                     time.monotonic())


@pytest.mark.parametrize('reload_check', ['stored', 'retrace'])
def test_post_pause_check_passes_under_d20(tmp_path, capsys, reload_check):
    import keras
    from bnhgq2 import ablation
    cfg = d20_cfg(reload_check)
    data, info, state = paused(tmp_path, cfg)
    report = verify(tmp_path, cfg, data, info, state)
    out = capsys.readouterr().out
    assert 'CHECKPOINT_VERIFICATION_PASS' in out
    assert report['reload_ebops_check'] == reload_check and report['status'] == 'verified_canary'
    selected = state['best_feasible'] or state['lowest']
    assert report['selection_cost'] == selected['ebops']
    assert json.loads((tmp_path / 'screen_result.json').read_text())['reload_ebops_check'] == reload_check
    # the pre-fix check: a reset retrace on the first 256 rows, against the full-split value
    loaded = keras.models.load_model(tmp_path / report['checkpoint'], compile=False)
    legacy = ablation.compute_ebops(loaded, np.asarray(data[0][:256]))['total']
    print('POST_PAUSE_TEST', reload_check, 'selected', selected['ebops'], 'legacy_256_row_retrace', legacy)
    assert legacy != selected['ebops'], 'synthetic data no longer reproduces the gate v1 defect'


def test_post_pause_check_catches_a_wrong_log(tmp_path):
    cfg = d20_cfg('stored')
    data, info, state = paused(tmp_path, cfg)
    key = 'best_feasible' if state['best_feasible'] else 'lowest'
    state[key] = {**state[key], 'ebops': state[key]['ebops'] + 1}
    with pytest.raises(AssertionError):
        verify(tmp_path, cfg, data, info, state)


def test_screen_path_unchanged():
    """No [D20] key: the helper is the screen runner's call, compute_ebops(xt[:256]) at 2048."""
    import keras
    from bnhgq2 import ablation
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    cfg = tiny_cfg()
    assert 'ebops_trace_sample' not in cfg['train'] and 'ebops_reload_check' not in cfg['train']
    (xt, _, _, _), _ = arrays(n_train=2000)
    keras.backend.clear_session()
    model, _ = ablation.matching_initialization(cfg, xt[:256], 1)
    got = ablation.selected_checkpoint_ebops(cfg, model, xt)
    assert got['method'] == 'retrace'
    assert got['total'] == ablation.compute_ebops(model, np.asarray(xt[:256]))['total']
    # a full-split key moves the rows the retrace uses
    cfg['train']['ebops_trace_sample'] = 'train_full'
    assert ablation.selected_checkpoint_ebops(cfg, model, xt)['total'] == ablation.compute_ebops(model, xt)['total']
