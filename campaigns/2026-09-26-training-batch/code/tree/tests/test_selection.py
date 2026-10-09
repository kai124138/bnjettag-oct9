"""[A13] tie-break order on a constructed accuracy tie; [A19] key semantics (CPU, no model)."""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
BASE = json.loads((HERE / 'configs' / 'const0922-a07-n64-s1-fast50-fp32.json').read_text())
M = 'val_categorical_accuracy'


def pick(points, cfg):
    from bnhgq2.ablation import checkpoint_selection_key, cost_before_auc
    first = cost_before_auc(cfg)
    return max(points, key=lambda p: checkpoint_selection_key(p, M, cost_before_auc=first))


def tie():
    # equal accuracy; a has higher AUC but more EBOPs; b cheaper, lower AUC
    return [{'epoch': 10, M: 0.79, 'val_macro_auc': 0.940, 'ebops': 340000},
            {'epoch': 20, M: 0.79, 'val_macro_auc': 0.930, 'ebops': 300000}]


def test_inherited_block_flips_order():
    assert 'engram_study' in BASE and 'cost_before_auc' not in BASE['experiment']
    assert pick(tie(), BASE)['epoch'] == 20          # historical: -EBOPs before AUC


def test_override_restores_study_order():
    cfg = copy.deepcopy(BASE)
    cfg['experiment']['cost_before_auc'] = False
    assert pick(tie(), cfg)['epoch'] == 10           # accuracy -> AUC -> -EBOPs -> -epoch
    same_auc = [dict(p, val_macro_auc=0.94) for p in tie()]
    assert pick(same_auc, cfg)['epoch'] == 20        # then lower EBOPs
    same_cost = [dict(p, val_macro_auc=0.94, ebops=300000) for p in tie()]
    assert pick(same_cost, cfg)['epoch'] == 10       # then earlier epoch
    better = tie() + [{'epoch': 30, M: 0.80, 'val_macro_auc': 0.90, 'ebops': 349999}]
    assert pick(better, cfg)['epoch'] == 30          # accuracy first


def test_override_type_checked():
    import pytest
    from bnhgq2.ablation import cost_before_auc
    cfg = copy.deepcopy(BASE)
    cfg['experiment']['cost_before_auc'] = 'false'
    with pytest.raises(ValueError):
        cost_before_auc(cfg)


def test_auc_selected_key():
    from bnhgq2.ablation import checkpoint_selection_key
    best = max(tie(), key=lambda p: checkpoint_selection_key(p, 'val_macro_auc'))
    assert best['epoch'] == 10
