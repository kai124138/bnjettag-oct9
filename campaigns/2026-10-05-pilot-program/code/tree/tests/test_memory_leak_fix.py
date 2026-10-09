"""Incident 2026-09-28 (review/INCIDENT_stall_20260928.md): per-epoch host-memory growth.

- `ValidationReloader`: one validation model per run; later epochs `load_weights` the saved
  candidate into it. Its variables and predictions must equal a fresh `load_model` of the same
  file byte for byte, epoch after epoch, and a whole run must give the same records as the
  fresh-load path.
- RSS canary gate (`BNJ_RSS_GATE_LIMIT_MB`, projection form): unset -> no gate and no epoch-line
  field; baseline + slope x train.epochs <= limit passes; above it the arm stops with exit 5 and
  RSS_GATE_FAIL.json.
CPU, tiny model, synthetic data."""
import json
import os

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

from test_d20_trace import arrays, records
from test_resume_cadence import tiny_cfg

TIMING = ('epoch_seconds', 'ebops_trace_seconds', 'ebops_reload_check_seconds', 'ebops_trace_over_epoch')


def test_reloader_equals_fresh_load_every_epoch(tmp_path):
    import keras
    from bnhgq2 import ablation
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    keras.utils.set_random_seed(1)
    cfg = tiny_cfg()
    (xt, yt, xv, yv), _ = arrays()
    model, _ = ablation.matching_initialization(cfg, xt[:256], 1)
    ablation.compute_ebops(model, xt)
    reload = ablation.ValidationReloader()
    path = tmp_path / 'validation_candidate.keras'
    rng = np.random.default_rng(1)
    first = None
    for epoch in range(3):
        # move every trainable variable, and the ranges, as training and a trace would
        for v in model.trainable_variables:
            v.assign(np.asarray(v) + rng.normal(0, 0.05, v.shape).astype(v.dtype))
        ablation.compute_ebops(model, xt[: 200 + 100 * epoch])
        model.save(path)
        persistent = reload(path)
        fresh = keras.models.load_model(path, compile=False)
        if first is None:
            first = persistent
        assert persistent is first                               # one model for the run
        for a, b in zip(persistent.weights, fresh.weights):
            assert np.asarray(a).tobytes() == np.asarray(b).tobytes(), a.path
        assert ablation.stored_state_ebops(model, persistent) == ablation.stored_state_ebops(model, fresh)
        p = np.asarray(persistent.predict(xv, batch_size=64, verbose=0))
        q = np.asarray(fresh.predict(xv, batch_size=64, verbose=0))
        assert p.tobytes() == q.tobytes()
        del fresh


def run(tmp_path, monkeypatch, fresh_load):
    import keras
    from bnhgq2 import ablation
    if fresh_load:
        class Fresh:
            def __call__(self, path):
                return keras.models.load_model(path, compile=False)
        monkeypatch.setattr(ablation, 'ValidationReloader', Fresh)
    keras.backend.clear_session()
    cfg = tiny_cfg()
    cfg['train'].update(epochs=4, ebops_trace_sample='train_full', ebops_reload_check='stored')
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    recs = records(tmp_path)
    for r in recs:
        for k in TIMING:
            r.pop(k)
    return recs


def test_run_records_equal_fresh_load_path(tmp_path, monkeypatch):
    a = run(tmp_path / 'persistent', monkeypatch, fresh_load=False)
    b = run(tmp_path / 'fresh', monkeypatch, fresh_load=True)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def test_gate_unset_changes_nothing(monkeypatch):
    from bnhgq2 import ablation
    monkeypatch.delenv('BNJ_RSS_GATE_LIMIT_MB', raising=False)
    assert ablation.rss_gate_from_env(7000) is None


def test_gate_window_must_span_100_epochs(monkeypatch):
    from bnhgq2 import ablation
    monkeypatch.setenv('BNJ_RSS_GATE_LIMIT_MB', '6144')
    monkeypatch.setenv('BNJ_RSS_GATE_WINDOW', '5:50')
    with pytest.raises(ValueError):
        ablation.rss_gate_from_env(7000)


# baseline 2,200 MB, limit 6,144 MiB, 7,000 epochs: the largest passing slope is 0.563 MB/epoch
@pytest.mark.parametrize('slope,verdict', [(0.0, 'PASS'), (0.5, 'PASS'), (0.6, 'FAIL'), (5.0, 'FAIL'), (90.0, 'FAIL')])
def test_gate_projection(tmp_path, monkeypatch, capsys, slope, verdict):
    from bnhgq2 import ablation
    monkeypatch.setenv('BNJ_RSS_GATE_LIMIT_MB', '6144')
    monkeypatch.setenv('BNJ_RSS_GATE_WINDOW', '5:105')
    gate = ablation.rss_gate_from_env(7000)
    # warm-up jump before W, +-20 MB alternating noise, then the slope under test
    series = iter([2200.0 + (800.0 if e < 5 else 0.0) + slope * (e - 5) + (20.0 if e % 2 else -20.0)
                   for e in range(105)])
    monkeypatch.setattr(ablation, 'host_rss_mb', lambda: next(series))
    for e in range(104):
        ablation.rss_gate_step(gate, 'arm', tmp_path)
    if verdict == 'PASS':
        ablation.rss_gate_step(gate, 'arm', tmp_path)
        out = capsys.readouterr().out
        assert 'RSS_GATE arm PASS' in out and 'projection_mb' in out and 'at_epoch 7000' in out
        assert not (tmp_path / 'RSS_GATE_FAIL.json').exists()
    else:
        with pytest.raises(SystemExit) as stop:
            ablation.rss_gate_step(gate, 'arm', tmp_path)
        assert stop.value.code == ablation.RSS_GATE_EXIT == 5
        assert 'RSS_GATE arm FAIL' in capsys.readouterr().out
        rec = json.loads((tmp_path / 'RSS_GATE_FAIL.json').read_text())
        assert rec['limit_mb'] == 6144.0 and rec['projection_mb'] > 6144.0
    s, b, p, v = ablation.rss_gate_verdict(gate)
    assert abs(s - slope) < 0.05 and abs(b - 2200.0) < 25 and v == verdict


def test_gate_prints_rss_on_epoch_line(tmp_path, monkeypatch, capsys):
    from bnhgq2 import ablation
    monkeypatch.setenv('BNJ_RSS_GATE_LIMIT_MB', '1000000')
    monkeypatch.setenv('BNJ_RSS_GATE_WINDOW', '0:100')
    cfg = tiny_cfg()
    cfg['train'].update(epochs=2, ebops_trace_sample='train_full', ebops_reload_check='stored')
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    lines = [l for l in capsys.readouterr().out.splitlines() if l.startswith('[epoch ')]
    assert len(lines) == 2 and all(' host_rss_mb=' in l for l in lines)
