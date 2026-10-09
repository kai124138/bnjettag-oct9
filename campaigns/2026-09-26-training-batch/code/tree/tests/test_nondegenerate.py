"""[ND, arbiter v3 fix 1] non-degeneracy condition and [D20] i_decay_speed record. CPU, tiny model, synthetic."""
import json
import os

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

from test_d20_trace import arrays
from test_resume_cadence import tiny_cfg


def records(out):
    return [json.loads(line) for line in (out / 'activation_widths.jsonl').read_text().splitlines()]


def test_majority_rule_formula():
    from bnhgq2.ablation import majority_rule
    y = np.eye(3, dtype='float32')[np.repeat([0, 1, 2], [50, 30, 20])]
    r = majority_rule(y, 5)
    assert r['class_counts'] == [50, 30, 20] and r['n_val'] == 100
    assert r['p_maj'] == 0.5 and r['se'] == pytest.approx(0.05)
    assert r['val_accuracy_threshold'] == pytest.approx(0.75)
    assert majority_rule(y.argmax(1), 5)['val_accuracy_threshold'] == r['val_accuracy_threshold']


def test_spec_checked():
    from bnhgq2.ablation import nondegenerate_rule
    cfg = tiny_cfg()
    y = np.eye(5, dtype='float32')[np.arange(10) % 5]
    assert nondegenerate_rule(cfg, y) is None
    for bad in ({'zero_floor_ebops': 1}, {'zero_floor_ebops': -1, 'se_multiple': 5},
                {'zero_floor_ebops': 1.5, 'se_multiple': 5}, {'zero_floor_ebops': 1, 'se_multiple': 5, 'x': 0}):
        cfg['experiment']['nondegenerate'] = bad
        with pytest.raises(ValueError):
            nondegenerate_rule(cfg, y)


def run(tmp_path, floor, se_multiple, epochs=2):
    from bnhgq2 import ablation
    cfg = tiny_cfg()
    cfg['train'].update(epochs=epochs, ebops_trace_sample='train_full', ebops_reload_check='stored')
    cfg['experiment']['nondegenerate'] = {'zero_floor_ebops': floor, 'se_multiple': se_multiple}
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    return cfg, json.loads((tmp_path / 'ebops_budget.json').read_text()), records(tmp_path)


def test_below_floor_is_degenerate(tmp_path):
    # floor above any EBOPs the tiny model can have: every epoch meets the budget (10^9) but
    # is degenerate, so nothing is selected as feasible
    _, result, recs = run(tmp_path, 10 ** 9 - 1, -100.0)
    assert result['best_feasible'] is None and result['feasible_degenerate_epochs'] == 2
    assert result['checkpoint'] == 'model_min_ebops.keras'
    assert result['first_feasible_degenerate']['epoch'] == 0
    for r in recs:
        assert r['ebops_budget_met'] == 1 and r['feasible_degenerate'] == 1 and r['budget_met'] == 0
        assert r['ebops_above_floor'] == r['ebops'] - (10 ** 9 - 1) < 0
    assert not (tmp_path / 'model_best.keras').exists()
    assert not (tmp_path / 'model_best_auc_feasible.keras').exists()


def test_accuracy_rule_is_degenerate(tmp_path):
    # floor 0, threshold p_maj + 5 SE: 64 rows, counts 13,13,13,13,12, p_maj 13/64
    _, result, recs = run(tmp_path, 0, 5.0)
    rule = result['nondegenerate_rule']
    p = 13 / 64
    assert rule['class_counts'] == [13, 13, 13, 13, 12] and rule['n_val'] == 64
    assert rule['p_maj'] == p and rule['val_accuracy_threshold'] == pytest.approx(p + 5 * np.sqrt(p * (1 - p) / 64))
    for r in recs:
        assert r['ebops_above_floor'] == r['ebops'] > 0
        assert r['nondegenerate'] == int(r['val_categorical_accuracy'] > rule['val_accuracy_threshold'])
    if all(r['nondegenerate'] == 0 for r in recs):
        assert result['best_feasible'] is None


def test_nondegenerate_selects_and_records(tmp_path):
    _, result, recs = run(tmp_path, 0, -100.0)
    assert result['best_feasible'] is not None and result['feasible_degenerate_epochs'] == 0
    assert result['best_feasible']['ebops_above_floor'] == result['best_feasible']['ebops']
    assert all(r['nondegenerate'] == 1 and r['budget_met'] == 1 for r in recs)
    decay = json.loads((tmp_path / 'i_decay_speed.json').read_text())
    assert decay and result['i_decay_speed'] == decay
    # HGQ2 0.1.9 default for a KIF datalane quantizer built without the key (jsc150 scopes 1e-3)
    assert decay['input_proj'] == pytest.approx(0.01)
    # a changed rule on resume is refused
    from bnhgq2 import ablation
    cfg = tiny_cfg()
    cfg['train'].update(epochs=2, ebops_trace_sample='train_full', ebops_reload_check='stored')
    cfg['experiment']['nondegenerate'] = {'zero_floor_ebops': 0, 'se_multiple': -100.0}
    (xt, yt, xv, yv), info = arrays()
    yv2 = yv.copy()
    yv2[:5] = np.eye(5, dtype='float32')[0]
    with pytest.raises(RuntimeError):
        ablation.run_training(cfg, (xt, yt, xv, yv2), info, tmp_path)
