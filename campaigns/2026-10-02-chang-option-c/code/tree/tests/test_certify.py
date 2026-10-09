"""[D20] certification: a checkpoint saved by run_training retraces to its logged EBOPs on
the same rows; a changed log or a lower target is caught; the ROC evaluator refuses an
uncertified file; the train+val sensitivity copy is written outside the run. CPU, synthetic."""
import copy
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

from test_d20_trace import arrays
from test_resume_cadence import tiny_cfg

CAMPAIGN = Path(__file__).resolve().parents[1] / 'campaigns' / 'chang0926'
sys.path.insert(0, str(CAMPAIGN))


def test_certify(tmp_path):
    from bnhgq2 import ablation
    import certify_ebops
    import evaluate_roc
    cfg = tiny_cfg()
    cfg['train'].update(epochs=2, ebops_trace_sample='train_full', ebops_reload_check='stored')
    (xt, yt, xv, yv), info = arrays()
    run = tmp_path / 'run'
    ablation.run_training(cfg, (xt, yt, xv, yv), info, run)
    state = json.loads((run / 'ebops_budget.json').read_text())
    point = state['selected']
    ok = certify_ebops.certify_checkpoint(run / 'model_best.keras', point, cfg, xt)
    assert ok['status'] == 'CERTIFIED' and ok['retraced_ebops'] == point['ebops'], ok
    assert ok['stored_ebops'] == point['ebops'], ok
    # the file is not rewritten by the retrace
    assert certify_ebops.sha(run / 'model_best.keras') == ok['checkpoint_sha256']
    bad = certify_ebops.certify_checkpoint(run / 'model_best.keras', {**point, 'ebops': point['ebops'] + 1}, cfg, xt)
    assert bad['status'] == 'EBOPS_MISMATCH'
    low = copy.deepcopy(cfg)
    low['train']['ebops']['pid']['target_ebops'] = point['ebops'] - 1
    assert certify_ebops.certify_checkpoint(run / 'model_best.keras', point, low, xt)['status'] == 'ABOVE_TARGET'
    # a 256-row retrace would not certify a full-split selection in general; the rule is same rows
    cert = {'mode': 'terminal', 'runs': [{'checkpoints': [ok]}]}
    assert evaluate_roc.certified(cert, run / 'model_best.keras') is ok
    with pytest.raises(RuntimeError):
        evaluate_roc.certified({'mode': 'terminal', 'runs': [{'checkpoints': [bad]}]}, run / 'model_best.keras')
    sens = certify_ebops.trainval_sensitivity(run / 'model_best.keras', cfg, xt, xv, tmp_path / 'tv.keras')
    assert sens['ebops_trainval'] >= point['ebops'] and (tmp_path / 'tv.keras').exists()
    assert sens['trace_rows'] == len(xt) + len(xv)
