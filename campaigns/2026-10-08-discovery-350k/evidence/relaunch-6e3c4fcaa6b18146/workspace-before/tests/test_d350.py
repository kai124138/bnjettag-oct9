"""discovery-350k (campaigns/2026-10-08-discovery-350k): generated configs, byte copies, and the
resume-to-a-later-stop-epoch path the follow-up stage relies on (PROPOSAL.md §5). CPU only."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np

from test_d20_trace import arrays, records
from test_pid_traced_only import option_c
from test_trace_every import TIMING

TREE = Path(__file__).resolve().parents[1]
D350 = TREE / 'campaigns' / 'd350'
PILOT = TREE / 'campaigns' / 'pilot1005'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def flat(d, prefix=''):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(flat(v, prefix + k + '.'))
        else:
            out[prefix + k] = v
    return out


def test_generator_reproduces_committed_configs():
    gen = load(D350 / 'generate.py', 'd350_generate')
    _, _, rows = gen.build_all()
    index = json.loads((D350 / 'index.json').read_text())['runs']
    # The two wave-1 rows come first and are exactly what the generator produces. Candidate rows
    # may follow (discovery campaign); each must be internally consistent.
    assert [r['name'] for r in index[:2]] == ['d350-baseline-e-350k-s1', 'd350-reference-e-5m-s1']
    for r, row in zip(rows[:2], index[:2]):
        data = gen.encode(r['cfg'])
        assert data == (D350 / 'configs' / row['file']).read_bytes(), row['name']
        assert hashlib.sha256(data).hexdigest() == row['config_sha256']
        assert json.loads((D350 / row['pack']).read_text()) == [[row['index']]]
    for row in index[2:]:
        data = (D350 / 'configs' / row['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == row['config_sha256'], row['name']
        assert json.loads((D350 / row['pack']).read_text()) == [[row['index']]], row['name']


def test_only_stated_keys_differ_from_the_pilot_config():
    base = flat(json.loads((PILOT / 'configs' / 'pilot1005-h1-e-350k-c-s1.json').read_text()))
    identity = {'name', 'experiment.arm', 'experiment.group', 'campaign.study', 'campaign.revision_of',
                'campaign.pilot.round', 'campaign.pilot.arm', 'campaign.pilot.hypothesis'}
    for name, target in (('d350-baseline-e-350k-s1', 350_000), ('d350-reference-e-5m-s1', 5_000_000)):
        cfg = flat(json.loads((D350 / 'configs' / f'{name}.json').read_text()))
        assert cfg.keys() == base.keys()
        changed = {k for k in cfg if cfg[k] != base[k]}
        scientific = {'train.ebops.pid.target_ebops', 'campaign.pilot.budget'} if target != 350_000 else set()
        assert changed == identity | scientific, (name, changed ^ (identity | scientific))
        assert cfg['train.ebops.pid.target_ebops'] == target
        assert cfg['train.epochs'] == 7000 and cfg['experiment.snapshot_every_epochs'] == 500


def test_campaign_scripts_are_byte_copies_of_the_pilot():
    for name in ('cpu_gate.py', 'monitor_p.py'):
        assert (D350 / name).read_bytes() == (PILOT / name).read_bytes(), name


def test_resume_to_a_later_stop_epoch_replays_the_straight_run(tmp_path):
    """Follow-up stage: a run paused at stop epoch E1 (run_pack <pack> E1) and relaunched with a
    later stop epoch E2 must equal a run taken straight to E2: same per-epoch records, controller
    telemetry, selected checkpoints and the E1 snapshot. Production: E1 = 1000, E2 = 2000,
    snapshots every 500, checkpoints every 25, trace every 10; here 6, 9, 6, 2, 3 (CPU)."""
    import keras
    from bnhgq2 import ablation
    cfg = option_c()
    cfg['train']['epochs'] = 12                   # neither stop epoch is the end of training
    (xt, yt, xv, yv), info = arrays()
    a = ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'straight', stop_after=9)
    b1 = ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'resumed', stop_after=6)
    assert b1['completed_epochs'] == 6
    assert json.loads((tmp_path / 'resumed' / 'latest.json').read_text())['checkpoint'] == 'epoch-0006'
    b = ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'resumed', stop_after=9)
    assert a['completed_epochs'] == b['completed_epochs'] == 9

    def strip(rs):
        return [{k: v for k, v in r.items() if k not in TIMING} for r in rs]
    assert strip(records(tmp_path / 'straight')) == strip(records(tmp_path / 'resumed'))
    assert [r['epoch'] for r in records(tmp_path / 'resumed')] == list(range(9))
    tel = [(tmp_path / d / ablation.PID_TELEMETRY).read_text().splitlines() for d in ('straight', 'resumed')]
    assert [json.loads(x)['epoch'] for x in tel[1]] == list(range(9))
    drop = ('learning_rate',)
    assert [{k: v for k, v in json.loads(x).items() if k not in drop} for x in tel[0]] == \
        [{k: v for k, v in json.loads(x).items() if k not in drop} for x in tel[1]]
    for name in ('model_best.keras', 'model_min_ebops.keras'):
        ma = keras.models.load_model(tmp_path / 'straight' / name, compile=False)
        mb = keras.models.load_model(tmp_path / 'resumed' / name, compile=False)
        for va, vb in zip(ma.weights, mb.weights):
            assert np.asarray(va).tobytes() == np.asarray(vb).tobytes(), va.path
    for d in ('straight', 'resumed'):
        assert sorted(p.name for p in (tmp_path / d / 'snapshots').glob('epoch-*')) == ['epoch-0006']
    sa = json.loads((tmp_path / 'straight' / 'snapshots' / 'epoch-0006' / 'state.json').read_text())
    sb = json.loads((tmp_path / 'resumed' / 'snapshots' / 'epoch-0006' / 'state.json').read_text())
    sa.pop('train_seconds'), sb.pop('train_seconds')
    assert sa == sb
    # the state the score reads at the stop epoch is the checkpoint written at the pause
    final = json.loads((tmp_path / 'resumed' / 'checkpoints' / 'epoch-0009' / 'state.json').read_text())
    assert final['completed_epochs'] == 9 and final['best_feasible'] == b['best_feasible']
