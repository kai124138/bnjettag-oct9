"""PREFLIGHT gate v1 (2026-09-27): W&B run id and group follow BNJ_STAGE (Job manifest env).
Deterministic within a stage, distinct across stages; pilot/canary -> '<group>-canary';
production -> the config group; unset stage refused for a tracked run. Pure functions."""
import hashlib

import pytest


def test_run_id_per_stage():
    from bnhgq2.wandb_util import stage_run_id
    name = 'chang0926-a-n64-s1'
    pilot, prod = stage_run_id(name, 'pilot'), stage_run_id(name, 'production')
    assert pilot == stage_run_id(name, 'pilot') and prod == stage_run_id(name, 'production')
    assert pilot != prod and len(pilot) == len(prod) == 12
    legacy = hashlib.sha256(name.encode()).hexdigest()[:12]
    assert stage_run_id(name, None) == legacy and legacy not in (pilot, prod)
    assert stage_run_id('chang0926-a-n64-s2', 'pilot') != pilot


def test_group_per_stage():
    from bnhgq2.wandb_util import stage_group
    assert stage_group('chang-n64-20260926', 'pilot') == 'chang-n64-20260926-canary'
    assert stage_group('chang-n64-20260926', 'canary') == 'chang-n64-20260926-canary'
    assert stage_group('chang-n64-20260926', 'production') == 'chang-n64-20260926'
    assert stage_group('chang-n64-20260926-wave2', 'canary') == 'chang-n64-20260926-wave2-canary'
    assert stage_group('chang-n64-20260926', None) == 'chang-n64-20260926'


def test_stage_env(monkeypatch):
    from bnhgq2.wandb_util import run_stage
    monkeypatch.delenv('BNJ_STAGE', raising=False)
    assert run_stage() is None
    with pytest.raises(RuntimeError):
        run_stage(required=True)
    monkeypatch.setenv('BNJ_STAGE', 'pilot')
    assert run_stage(required=True) == 'pilot'
    monkeypatch.setenv('BNJ_STAGE', 'prod')
    with pytest.raises(ValueError):
        run_stage()


def test_run_training_passes_stage_id_and_group(monkeypatch, tmp_path):
    """run_training(remote=True) hands wandb.init the stage id and group (wandb stubbed)."""
    import sys
    import types
    from bnhgq2 import ablation
    from bnhgq2.wandb_util import stage_group, stage_run_id
    from test_d20_trace import arrays
    from test_resume_cadence import tiny_cfg
    seen = {}

    class Run:
        summary = types.SimpleNamespace(update=lambda *a, **k: None)
        def log(self, *a, **k): pass
        def finish(self, *a, **k): pass

    def init(**kw):
        seen.update(kw)
        return Run()
    monkeypatch.setitem(sys.modules, 'wandb', types.SimpleNamespace(init=init, run=None))
    cfg = tiny_cfg()
    cfg['train']['epochs'] = 1
    cfg['experiment']['remote_every_epochs'] = 10 ** 6
    (xt, yt, xv, yv), info = arrays(n_train=300)
    monkeypatch.delenv('BNJ_STAGE', raising=False)
    with pytest.raises(RuntimeError):
        ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'none', remote=True)
    monkeypatch.setenv('BNJ_STAGE', 'pilot')
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'pilot', remote=True, stop_after=1)
    assert seen['id'] == stage_run_id(cfg['name'], 'pilot') and seen['resume'] == 'allow'
    assert seen['group'] == stage_group(cfg['experiment']['group'], 'pilot')
    assert seen['group'].endswith('-canary')


def test_pilot_b_cannot_collide_with_pilot():
    """[D20] regime B (2026-09-27): the second pilot runs the same config names as the regime-A
    pilot. Its W&B id and group differ from the pilot's, production's and the legacy id, for
    every one of the 58 config names."""
    import json
    from pathlib import Path
    from bnhgq2.wandb_util import run_stage, stage_group, stage_run_id
    rows = json.loads((Path(__file__).resolve().parents[1] / 'campaigns' / 'chang0926' / 'index.json').read_text())['runs']
    ids = {}
    for row in rows:
        name = row['name']
        for stage in ('pilot', 'pilot-b', 'production', None):
            ids.setdefault(stage_run_id(name, stage), []).append((name, stage))
    assert all(len(v) == 1 for v in ids.values()), [v for v in ids.values() if len(v) > 1]
    assert len(ids) == 4 * len(rows)
    group = 'chang-n64-20260926'
    assert stage_group(group, 'pilot-b') == 'chang-n64-20260926-pilot-b'
    assert stage_group(group, 'pilot-b') not in (stage_group(group, 'pilot'), stage_group(group, 'production'))
    import os
    old = os.environ.get('BNJ_STAGE')
    try:
        os.environ['BNJ_STAGE'] = 'pilot-b'
        assert run_stage(required=True) == 'pilot-b'
    finally:
        if old is None:
            os.environ.pop('BNJ_STAGE', None)
        else:
            os.environ['BNJ_STAGE'] = old
