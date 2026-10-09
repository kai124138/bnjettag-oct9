"""Option (c) (Kai K1, 2026-09-28; staged, not shipped): `train.ebops.pid_input: "traced_only"`.
Under regime B the PID steps only on the traced full-split EBOPs of the previous epoch and holds
beta on every other epoch; `train.ebops.pid_traced_integral` ("per_epoch" default, "per_step")
sets how the integral is fed across a D-epoch step. Absent key: slot P, as in 42abed4b
(test_trace_every.py). CPU, tiny model, synthetic rows."""
import copy
import json
import math
import os

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import pytest

from test_d20_trace import arrays, records
from test_trace_every import TIMING, regime_b


def option_c(integral=None, **kw):
    cfg = regime_b(**kw)
    cfg['train']['ebops']['pid_input'] = 'traced_only'
    if integral is not None:
        cfg['train']['ebops']['pid_traced_integral'] = integral
    return cfg


def test_key_semantics_and_guards():
    from bnhgq2.ablation import pid_traced_only
    assert pid_traced_only(regime_b()) is None                       # absent: slot P
    assert pid_traced_only(option_c()) == 'per_epoch'                # default
    assert pid_traced_only(option_c('per_step')) == 'per_step'
    bad = []
    c = option_c(); c['train']['ebops']['pid_input'] = 'in_training'; bad.append(c)
    c = option_c('per_time'); bad.append(c)
    c = option_c(); del c['train']['ebops_trace_every']; bad.append(c)        # regime A
    c = option_c(); c['train']['ebops']['pid']['d'] = 0.1; bad.append(c)      # derivative
    c = option_c(); c['train']['ebops']['pid']['warmup'] = 2; bad.append(c)   # seed epoch 1 untraced (k=3)
    c = regime_b(); c['train']['ebops']['pid_traced_integral'] = 'per_step'; bad.append(c)
    for c in bad:
        with pytest.raises(ValueError):
            pid_traced_only(c)


def test_production_step_schedule():
    """k = 10, 7,000 epochs, warmup 1: steps at 0 (warmup branch), 1 (seed, after the epoch-0
    trace), then 10, 20, ..., 6,990; spans 1, 1, 9, 10, 10, ...; the last trace (end of epoch
    7,000) drives no step."""
    from bnhgq2.ablation import pid_step_epochs, pid_traced_only
    cfg = option_c(epochs=7000, k=10)
    cfg['experiment']['snapshot_every_epochs'] = 500
    cfg['train']['ebops']['pid']['warmup'] = 1
    assert pid_traced_only(cfg) == 'per_epoch'
    steps = [(e, span) for e in range(7000) for stepped, span in [pid_step_epochs(cfg, e)] if stepped]
    assert [e for e, _ in steps] == [0, 1] + list(range(10, 7000, 10))
    assert [s for _, s in steps[:5]] == [1, 1, 9, 10, 10] and {s for _, s in steps[3:]} == {10}
    assert len(steps) == 701
    # per unit time the integral receives one error per epoch, as in the per-epoch controller
    assert sum(s for e, s in steps if e >= 1) == 6990          # epochs 1..6,990, one error each


@pytest.mark.parametrize('integral', ['per_epoch', 'per_step'])
def test_beta_held_on_untraced_stepped_on_traced(tmp_path, integral):
    from bnhgq2 import ablation
    cfg = option_c(integral)                       # epochs 7, k 3: traced 0, 2, 5, 6
    target = cfg['train']['ebops']['pid']['target_ebops']
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path)
    recs = records(tmp_path)
    assert [r['ebops_traced'] for r in recs] == [1, 0, 1, 0, 0, 1, 1]
    # stepped at the start of e iff e - 1 was traced (or e < warmup = 1)
    assert [r['pid_stepped'] for r in recs] == [1, 1, 0, 1, 0, 0, 1]
    assert [r['pid_step_span'] for r in recs] == [1, 1, 0, 2, 0, 0, 3]
    last_traced = None
    for e, r in enumerate(recs):
        if e >= 1 and not r['pid_stepped']:
            # held: beta and integral exactly as at the end of the previous epoch
            assert r['beta'] == recs[e - 1]['beta'] and r['pid_integral'] == recs[e - 1]['pid_integral']
        if e >= 2 and r['pid_stepped']:
            # stepped on the previous (traced) EBOPs; beta moves (target 1e9, never clamped here)
            assert r['beta'] != recs[e - 1]['beta']
            err = math.log10(recs[e - 1]['ebops'] / target)
            span = r['pid_step_span'] if integral == 'per_epoch' else 1
            assert r['pid_integral'] == pytest.approx(recs[e - 1]['pid_integral'] + span * err, rel=1e-12)
            p, i = cfg['train']['ebops']['pid']['p'], cfg['train']['ebops']['pid']['i']
            beta = 10 ** (p * err + i * r['pid_integral'])
            assert r['beta'] == pytest.approx(min(max(beta, 1e-10), 1e-3), rel=1e-9)
        if r['ebops_traced']:
            last_traced = r['ebops']
            assert r['pid_ebops'] == pytest.approx(r['ebops'], rel=1e-6)
        else:
            # the PID never reads the in-training EBOPs: it holds the last traced value
            assert r['pid_ebops'] == last_traced and r['ebops_in_training'] > 0


def test_per_epoch_and_per_step_differ_only_in_integral(tmp_path):
    from bnhgq2 import ablation
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(option_c('per_epoch'), (xt, yt, xv, yv), info, tmp_path / 'a')
    ablation.run_training(option_c('per_step'), (xt, yt, xv, yv), info, tmp_path / 'b')
    a, b = records(tmp_path / 'a'), records(tmp_path / 'b')
    assert [r['beta'] for r in a[:3]] == [r['beta'] for r in b[:3]]   # before the first span > 1
    assert a[3]['pid_integral'] != b[3]['pid_integral']


def test_resume_across_untraced_pause_replays(tmp_path):
    """checkpoint_every 2 against k 3 (production: 25 against 10), so the pause at epoch 4 is
    untraced; resume must replay the uninterrupted run (beta held, span recomputed)."""
    import keras
    from bnhgq2 import ablation
    cfg = option_c()
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'straight')
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'paused', stop_after=4)
    ablation.run_training(cfg, (xt, yt, xv, yv), info, tmp_path / 'paused')

    def strip(rs):
        return [{k: v for k, v in r.items() if k not in TIMING} for r in rs]
    assert strip(records(tmp_path / 'straight')) == strip(records(tmp_path / 'paused'))
    for name in ('model_best.keras', 'model_min_ebops.keras'):
        a = keras.models.load_model(tmp_path / 'straight' / name, compile=False)
        b = keras.models.load_model(tmp_path / 'paused' / name, compile=False)
        for va, vb in zip(a.weights, b.weights):
            assert np.asarray(va).tobytes() == np.asarray(vb).tobytes(), va.path


def test_slot_p_run_cannot_resume_as_option_c(tmp_path):
    """A regime-B (slot P) checkpoint refuses an option-(c) config: the config sha differs."""
    from bnhgq2 import ablation
    (xt, yt, xv, yv), info = arrays()
    ablation.run_training(regime_b(), (xt, yt, xv, yv), info, tmp_path, stop_after=4)
    with pytest.raises(AssertionError, match='Resume config mismatch'):
        ablation.run_training(option_c(), (xt, yt, xv, yv), info, tmp_path)
