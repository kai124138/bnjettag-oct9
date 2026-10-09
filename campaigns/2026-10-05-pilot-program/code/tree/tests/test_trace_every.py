"""[D20] regime B (Kai, 2026-09-27): `train.ebops_trace_every: k`. The full-split reset trace runs
only at traced epochs (e == 0, (e + 1) % k == 0, or the last epoch); BetaPID reads the in-training EBOPs
on untraced epochs; feasibility and every selected file come from traced epochs only; the
selected file retraces to its logged EBOPs; a resume across an untraced pause replays the same
trajectory; an absent key traces every epoch and logs nothing new. CPU, tiny model, synthetic."""
import copy
import json
import os

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

from test_d20_trace import arrays, records
from test_resume_cadence import tiny_cfg

TIMING = ('epoch_seconds', 'ebops_trace_seconds', 'ebops_reload_check_seconds', 'ebops_trace_over_epoch')


def regime_b(epochs=7, k=3):
    cfg = tiny_cfg()
    cfg['train'].update(epochs=epochs, ebops_trace_sample='train_full', ebops_reload_check='stored',
                        ebops_trace_every=k)
    # checkpoint cadence deliberately not a multiple of k (production: 25 against 10)
    cfg['experiment'].update(checkpoint_every_epochs=2, snapshot_every_epochs=6)
    return cfg


def test_key_semantics():
    from bnhgq2.ablation import ebops_trace_every, is_traced_epoch
    cfg = tiny_cfg()
    assert ebops_trace_every(cfg) is None
    assert all(is_traced_epoch(cfg, e) for e in range(cfg['train']['epochs']))
    cfg = regime_b(epochs=7, k=3)
    assert ebops_trace_every(cfg) == 3
    assert [e for e in range(7) if is_traced_epoch(cfg, e)] == [0, 2, 5, 6]  # 0: canary; 6: last
    prod = regime_b(epochs=7000, k=10)
    prod['experiment']['snapshot_every_epochs'] = 500
    traced = [e for e in range(7000) if is_traced_epoch(prod, e)]
    assert len(traced) == 701 and traced[:2] == [0, 9]
    # STUDY slot T: the ends of epochs 1, 10, 500, 1,000, 2,000, 4,000 and 7,000 are traced
    assert all(e - 1 in traced for e in (1, 10, 500, 1000, 2000, 4000, 7000))
    for bad in (0, -1, True, 2.5, '10'):
        c = regime_b()
        c['train']['ebops_trace_every'] = bad
        with pytest.raises(ValueError):
            ebops_trace_every(c)
    c = regime_b()
    del c['train']['ebops_trace_sample']
    with pytest.raises(ValueError):
        ebops_trace_every(c)
    c = regime_b()
    c['train']['ebops_reload_check'] = 'retrace'
    with pytest.raises(ValueError):
        ebops_trace_every(c)
    c = regime_b()
    c['experiment']['snapshot_every_epochs'] = 4
    with pytest.raises(ValueError):
        ebops_trace_every(c)


def test_regime_b_selection_and_pid(tmp_path, capsys):
    import keras
    from bnhgq2 import ablation
    cfg = regime_b()
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    recs = records(tmp_path)
    assert [r['ebops_traced'] for r in recs] == [1, 0, 1, 0, 0, 1, 1]
    for r in recs:
        if r['ebops_traced']:
            assert r['ebops'] is not None and r['budget_met'] in (0, 1) and r['per_layer']
            assert r['pid_ebops'] == pytest.approx(r['ebops'], rel=1e-6)
            assert r['ebops_trace_seconds'] > 0
        else:
            # (a) untraced: no trace ran, BetaPID read the in-training EBOPs
            assert r['ebops'] is None and r['budget_met'] is None and r['per_layer'] is None
            assert r['pid_ebops'] == r['ebops_in_training'] > 0
            assert r['ebops_trace_seconds'] < 0.05 and r['ebops_in_training_over_traced'] is None
            assert np.isfinite(r['val_macro_auc'])            # validated every epoch
    state = json.loads((tmp_path / 'checkpoints' / 'epoch-0007' / 'state.json').read_text())
    for key in ('best_feasible', 'best_feasible_auc', 'lowest', 'best_auc'):
        assert state[key]['epoch'] in (0, 2, 5, 6), (key, state[key])
    # (c) every selected file is a traced candidate and retraces (reset, same rows) to its log
    for name, key in (('model_best.keras', 'best_feasible'), ('model_min_ebops.keras', 'lowest'),
                      ('model_best_auc_feasible.keras', 'best_feasible_auc')):
        loaded = keras.models.load_model(tmp_path / name, compile=False)
        assert ablation.saved_ebops(loaded) == state[key]['ebops']
        assert ablation.compute_ebops(loaded, xt)['total'] == state[key]['ebops']
    snap = json.loads((tmp_path / 'snapshots' / 'epoch-0006' / 'state.json').read_text())
    assert snap['best_feasible']['epoch'] in (0, 2, 5)       # snapshots fall on traced epochs
    budget = json.loads((tmp_path / 'ebops_budget.json').read_text())
    assert budget['selected']['epoch'] in (0, 2, 5, 6)
    out = capsys.readouterr().out
    assert '[epoch 2/7] EBOPs=untraced in_training_ebops=' in out and '[epoch 1/7] EBOPs=untraced' not in out
    assert ' ebops_trace_seconds=' in out and ' ebops_trace_over_epoch=' in out and ' loss=' in out


def test_degenerate_counter_counts_traced_epochs_only(tmp_path):
    from bnhgq2 import ablation
    cfg = regime_b()
    # 64 validation rows: threshold p_maj + 5 SE = 0.2 + 5 * 0.05 = 0.45, above a tiny model's
    # accuracy, so every traced epoch is feasible-degenerate
    cfg['experiment']['nondegenerate'] = {'zero_floor_ebops': 0, 'se_multiple': 5}
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    recs = records(tmp_path)
    state = json.loads((tmp_path / 'checkpoints' / 'epoch-0007' / 'state.json').read_text())
    traced_degenerate = sum(1 for r in recs if r['ebops_traced'] and r['feasible_degenerate'])
    assert state['feasible_degenerate_epochs'] == traced_degenerate
    assert state['feasible_degenerate_epochs'] <= 4
    for r in recs:
        if not r['ebops_traced']:
            assert r['ebops_above_floor'] is None and r['nondegenerate'] is None
            assert r['feasible_degenerate'] is None and r['ebops_budget_met'] is None


def test_resume_across_untraced_pause_replays(tmp_path):
    """Pause at epoch 4 (untraced), resume to 7: the same records (minus wall time) and the
    same selected-file weights as an uninterrupted run (CPU)."""
    import keras
    from bnhgq2 import ablation
    cfg = regime_b()
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'straight')
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'paused', stop_after=4)
    # (c) the checkpoint written at an untraced epoch carries the last traced selection
    ck = tmp_path / 'paused' / 'checkpoints' / 'epoch-0004'
    assert json.loads((ck / 'state.json').read_text())['best_feasible']['epoch'] in (0, 2)
    assert (ck / 'model_best.keras').read_bytes() == (tmp_path / 'paused' / 'model_best.keras').read_bytes()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'paused')

    def strip(rs):
        return [{k: v for k, v in r.items() if k not in TIMING} for r in rs]
    assert strip(records(tmp_path / 'straight')) == strip(records(tmp_path / 'paused'))
    for name in ('model_best.keras', 'model_min_ebops.keras'):
        a = keras.models.load_model(tmp_path / 'straight' / name, compile=False)
        b = keras.models.load_model(tmp_path / 'paused' / name, compile=False)
        for va, vb in zip(a.weights, b.weights):
            assert np.asarray(va).tobytes() == np.asarray(vb).tobytes(), va.path


def test_absent_key_traces_every_epoch(tmp_path):
    from bnhgq2 import ablation
    cfg = tiny_cfg()
    cfg['train'].update(epochs=3, ebops_trace_sample='train_full', ebops_reload_check='stored')
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    for r in records(tmp_path):
        assert 'ebops_traced' not in r and r['ebops'] is not None and r['per_layer']
        assert r['pid_ebops'] == pytest.approx(r['ebops'], rel=1e-6)


def test_pause_before_first_trace_skips_verification(tmp_path, capsys):
    import run_study
    cfg = regime_b()
    state = {'best_feasible': None, 'lowest': None, 'completed_epochs': 2}
    assert run_study.verify_selected(cfg, {}, tmp_path, state, None, None, None, 0.) is None
    assert 'CHECKPOINT_VERIFICATION_SKIPPED' in capsys.readouterr().out
