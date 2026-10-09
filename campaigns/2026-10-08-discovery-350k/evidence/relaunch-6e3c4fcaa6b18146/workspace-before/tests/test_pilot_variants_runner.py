"""Pilot R1 variants through the runner's own path (patch 0041): NB ([D22], 0036) and the H3 attention
floor (0037) pass run_engram.validate_cfg and train under ablation.run_training with
run_study.train's model builder and epoch observer (option (c), regime B, tiny synthetic data).

Found while folding 0036 into the R1 bundle: run_engram.validate_cfg rejected every weight type
except binary_absmean, so run_study.train would have refused the NB arm before its first epoch.
"""
import copy
import json
import sys
from pathlib import Path

import numpy as np
import pytest

TREE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TREE))
sys.path.insert(0, str(TREE / 'tests'))

from test_d20_trace import arrays, records  # noqa: E402
from test_pid_traced_only import option_c  # noqa: E402

PILOT = TREE / 'campaigns' / 'pilot1005' / 'configs'


def variant(kind):
    cfg = option_c()
    if kind == 'nb':
        cfg['quant']['weight'] = 'kbi_learnable'
    elif kind == 'qkv1':
        cfg['quant']['attn_bit_floor'] = {'bits': 1, 'sites': ['q', 'k', 'v']}
    cfg['name'] = f'unit-pilot-{kind}'
    return cfg


def test_validate_cfg_accepts_nb_and_rejects_others():
    import run_engram
    for name in ('pilot1005-h5-e-350k-c-nb-s1', 'pilot1005-h3-e-350k-c-qkv1-s2', 'pilot1005-h1-e-350k-c-s1'):
        run_engram.validate_cfg(json.loads((PILOT / f'{name}.json').read_text()))
    cfg = json.loads((PILOT / 'pilot1005-h5-e-350k-c-nb-s1.json').read_text())
    for bad in ('int8_absmax', 'none', 'kbi_learned'):
        probe = copy.deepcopy(cfg)
        probe['quant']['weight'] = bad
        with pytest.raises(ValueError):
            run_engram.validate_cfg(probe)


@pytest.mark.parametrize('kind', ['nb', 'qkv1'])
def test_runner_path_trains(tmp_path, kind):
    import run_engram
    ablation, engram = run_engram.runtime()
    cfg = variant(kind)
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path, stop_after=3,
                          model_builder=run_engram.builder_for(info), epoch_observer=engram.diagnostic_observer())
    recs = records(tmp_path)
    assert [r['epoch'] for r in recs] == [0, 1, 2]
    assert all(np.isfinite(r['loss']) for r in recs)
    assert [r['pid_stepped'] for r in recs][:2] == [1, 1]
    if kind == 'nb':
        assert all('weight_bits_mean' in r for r in recs)
