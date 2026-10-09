"""eval/score.py on synthetic run directories, in the style of the pilot's tests/test_readout_pilot.py.

Fixture runs write what the runner writes (activation_widths.jsonl, snapshots/epoch-EEEE/state.json,
nondegenerate_rule.json, config.json, data_info.json, DIVERGED.json). Cache, certification, CPU
replay and entropy are stubbed hooks here, except in the end-to-end test, which trains a tiny model
on CPU with the frozen runner and certifies and replays its checkpoint for real.

Run: PYTHONPATH=<code tree> python -m pytest -q eval/tests  (from the campaign directory)
"""
import copy
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

EVAL = Path(__file__).resolve().parents[1]
CAMPAIGN = EVAL.parent
TREE = CAMPAIGN / 'code'
sys.path.insert(0, str(TREE))
sys.path.insert(0, str(TREE / 'tests'))
os.environ.setdefault('KERAS_BACKEND', 'tensorflow')

spec = importlib.util.spec_from_file_location('d350_score', EVAL / 'score.py')
score = importlib.util.module_from_spec(spec)
spec.loader.exec_module(score)
readout = score.load('readout_pilot')
THR, LABELS = readout.THRESHOLD_C, readout.LABELS_SHA256
FLOOR = 171526
BASE_CFG = json.loads((TREE / 'campaigns' / 'd350' / 'configs' / 'd350-baseline-e-350k-s1.json').read_text())
TRAIN_SHA = 'a' * 64


def traced(e):
    return e == 0 or (e + 1) % 10 == 0


def cfg_for(target=350_000):
    cfg = copy.deepcopy(BASE_CFG)
    cfg['train']['ebops']['pid']['target_ebops'] = target
    return cfg


def make_run(root, curve, *, epochs=1000, target=350_000, threshold=THR, labels=LABELS, floor=FLOOR,
             runner='auto', snapshots=(500, 1000), diverged=False, drop_epoch=None, model_file=True,
             rec_threshold=None, train_sha=TRAIN_SHA):
    """curve(epoch) -> (ebops, val_acc, val_auc); the runner's best_feasible per snapshot as the
    frozen rule picks it, unless `runner` overrides the stop-epoch choice."""
    run = Path(root) / 'run'
    run.mkdir(parents=True)
    (run / 'config.json').write_text(json.dumps(cfg_for(target)))
    (run / 'data_info.json').write_text(json.dumps({'train_sha256': train_sha}))
    (run / 'nondegenerate_rule.json').write_text(json.dumps({'val_accuracy_threshold': threshold, 'labels_sha256': labels,
                                                             'zero_floor_ebops': floor, 'n_val': 62000}))
    best, best_at = None, {}
    with (run / 'activation_widths.jsonl').open('w') as f:
        for e in range(epochs):
            if e == drop_epoch:
                continue
            ebops, acc, auc = curve(e)
            t = traced(e)
            f.write(json.dumps({'epoch': e, 'ebops': ebops if t else None, 'ebops_traced': int(t),
                                'val_categorical_accuracy': acc, 'val_macro_auc': auc,
                                'val_accuracy_threshold': rec_threshold if rec_threshold is not None else threshold,
                                'activation_bits_mean': 3.5, 'activation_bits/x': 3.5}) + '\n')
            if t and ebops <= target and ebops - floor > 0 and acc > THR:
                p = {'epoch': e, 'ebops': ebops, 'val_categorical_accuracy': acc, 'val_macro_auc': auc}
                if best is None or readout.key(p) > readout.key(best):
                    best = p
            if e + 1 in snapshots:
                best_at[e + 1] = best
    for s in snapshots:
        if s > epochs:
            continue
        d = run / 'snapshots' / f'epoch-{s:04d}'
        d.mkdir(parents=True)
        chosen = best_at.get(s)
        if s == max(snapshots) and runner != 'auto':
            chosen = runner
        (d / 'state.json').write_text(json.dumps({'completed_epochs': s, 'best_feasible': chosen}))
        if chosen is not None and model_file:
            (d / 'model_best.keras').write_bytes(b'stub checkpoint')
    if diverged:
        (run / 'DIVERGED.json').write_text('{}')
    return run


def stub_hooks(cert_status='CERTIFIED', replay_shift=0.0, threshold=THR, labels=LABELS, calls=None):
    calls = calls if calls is not None else {}

    def load_arrays(cache, cfg):
        return (None, None, 'x_val', 'y_val'), {'train_sha256': TRAIN_SHA}

    def derive_threshold(nt, cache, cfg):
        return {'val_accuracy_threshold': threshold, 'labels_sha256': labels, 'n_val': 62000}

    def certify(cert, path, point, cfg, x_train):
        calls['certify'] = (str(path), point['epoch'])
        return {'status': cert_status, 'logged_ebops': point['ebops'], 'retraced_ebops': point['ebops'],
                'stored_ebops': point['ebops'], 'trace_seconds': 1.0}

    def replay_val(path, x_val, y_val, cfg):
        state = json.loads((Path(path).parent / 'state.json').read_text())
        return state['best_feasible']['val_categorical_accuracy'] + replay_shift, state['best_feasible']['val_macro_auc']

    def entropy(attn, path, x_val):
        return {'mean': 0.9, 'heads': [0.9, 0.9], 'reason': None}
    return {'load_arrays': load_arrays, 'derive_threshold': derive_threshold, 'certify': certify,
            'replay_val': replay_val, 'entropy': entropy}


def run_score(run, capsys, hooks=None, extra=()):
    code = score.main([str(run), '--cache', str(run.parent / 'cache'), '--code', str(TREE), *extra],
                      hooks=hooks or stub_hooks())
    out = capsys.readouterr().out.splitlines()
    return code, out


def squeeze(e):
    """Squeezes to the budget by epoch 500; accuracy dips at arrival and recovers after the restart."""
    ebops = max(400_000 - 100 * (e + 1), 300_000) if e >= 300 else 2_000_000
    acc = 0.30 + 0.0002 * (e % 500) if e < 500 else 0.35 + 0.0001 * (e - 500)
    return ebops, round(acc, 6), round(0.80 + acc / 10, 6)


# --------------------------------------------------------------------------- valid
def test_valid_score_is_the_single_stdout_line(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    calls = {}
    code, out = run_score(run, capsys, stub_hooks(calls=calls))
    assert code == 0 and len(out) == 1
    value = float(out[0])
    rec = json.loads((run / 'score-s1.json').read_text())
    assert rec['status'] == 'valid' and rec['score'] == value
    # best feasible: max accuracy over feasible traced epochs < 1000 -> zero-based 999
    assert rec['selected']['epoch'] == 999 and value == squeeze(999)[1]
    assert calls['certify'] == (str(run / 'snapshots' / 'epoch-1000' / 'model_best.keras'), 999)
    s = rec['secondary']
    assert s['at_epoch']['500']['epoch_zero_based'] == 499 and s['at_epoch']['500']['feasible']
    assert s['at_epoch']['500']['best_feasible_as_of_snapshot_epoch'] == 499
    assert s['at_epoch']['1000']['val_acc_if_feasible'] == squeeze(999)[1]
    assert s['first_budget_met_epoch_zero_based'] == 499 and s['first_budget_met_epoch_one_based'] == 500
    assert s['min_traced_ebops'] == 300_000
    assert s['feasible_epochs'] == len([e for e in range(1000) if traced(e) and e >= 499])
    assert s['feasible_epochs_acc_ge_050'] == 0
    assert s['selected_val_macro_auc'] == squeeze(999)[2]
    assert s['attention_entropy']['mean'] == 0.9
    assert s['best_feasible_acc_by_window_one_based']['801-1000'] == squeeze(999)[1]
    assert s['best_feasible_acc_by_window_one_based']['1-200'] is None
    assert 'trace_seconds' not in rec['certification']


def test_tie_break_follows_the_frozen_key(tmp_path, capsys):
    # equal accuracy everywhere under budget: AUC breaks the tie, then lower EBOPs, then earlier epoch
    def flat(e):
        ebops = 340_000 if e == 99 or e % 20 != 19 else 300_000
        return ebops, 0.4, (0.9 if e in (99, 199, 399) else 0.8)
    run = make_run(tmp_path, flat)
    code, out = run_score(run, capsys)
    rec = json.loads((run / 'score-s1.json').read_text())
    # AUC 0.9 at 99 (340k), 199 and 399 (300k): lower EBOPs beats 99, the earlier epoch beats 399
    assert code == 0 and rec['selected']['epoch'] == 199
    assert float(out[0]) == 0.4


def test_reference_scored_at_its_own_target(tmp_path, capsys):
    def ref(e):
        return 4_000_000, 0.65, 0.9
    run = make_run(tmp_path, ref, target=5_000_000)
    code, out = run_score(run, capsys, extra=('--expect-target', '5000000'))
    assert code == 0 and float(out[0]) == 0.65


def test_rerun_with_same_result_keeps_score_json(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    assert run_score(run, capsys)[0] == 0
    before = (run / 'score-s1.json').read_bytes()
    code, out = run_score(run, capsys)
    assert code == 0 and (run / 'score-s1.json').read_bytes() == before


# --------------------------------------------------------------------------- INVALID
def class_hits(reason):
    classes = json.loads((EVAL / 'INVALID_REASONS.json').read_text())['classes']
    return {c for c, ps in classes.items() if any(reason.startswith(p) for p in ps)}


def invalid(run, capsys, hooks=None, extra=()):
    code, out = run_score(run, capsys, hooks, extra)
    assert code == 2 and len(out) == 1 and out[0].startswith('INVALID['), out
    rec = json.loads((run / 'score-s1.json').read_text()) if (run / 'score-s1.json').exists() else None
    if rec is not None and rec.get('status') == 'invalid':
        assert rec['score'] is None and rec['invalid_reason']
    reason = out[0].split(']: ', 1)[1]
    assert score.classify(reason) == out[0][len('INVALID['):out[0].index(']')]
    assert len(class_hits(reason)) == 1, reason
    return out[0]


def test_no_feasible_checkpoint(tmp_path, capsys):
    run = make_run(tmp_path, lambda e: (2_000_000, 0.6, 0.9))
    assert invalid(run, capsys).startswith('INVALID[scientific]: no feasible checkpoint')


def test_degenerate_under_budget_is_not_feasible(tmp_path, capsys):
    run = make_run(tmp_path, lambda e: (300_000, THR, 0.6))         # acc == threshold: not above it
    assert 'no feasible checkpoint' in invalid(run, capsys)


def test_at_or_below_the_zero_bit_floor_is_not_feasible(tmp_path, capsys):
    run = make_run(tmp_path, lambda e: (FLOOR, 0.5, 0.8))
    assert 'no feasible checkpoint' in invalid(run, capsys)


def test_diverged(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, diverged=True)
    assert 'DIVERGED' in invalid(run, capsys)


def test_missing_stop_snapshot(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, epochs=750, snapshots=(500,))
    assert 'snapshot epoch-1000 missing' in invalid(run, capsys)


def test_records_gap(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, drop_epoch=640)
    assert 'not contiguous' in invalid(run, capsys)


def test_threshold_mismatch_in_run(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, threshold=0.25)
    assert 'run threshold' in invalid(run, capsys)


def test_threshold_mismatch_in_records(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, rec_threshold=0.3)
    assert 'another threshold' in invalid(run, capsys)


def test_threshold_rederived_from_cache_differs(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    assert 'threshold from y_val' in invalid(run, capsys, stub_hooks(threshold=0.2))


def test_labels_sha_mismatch(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, labels='b' * 64)
    assert 'labels sha' in invalid(run, capsys)


def test_floor_mismatch(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, floor=100)
    assert '0-bit floor' in invalid(run, capsys)


def test_target_not_expected(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, target=400_000)
    assert 'expected 350000' in invalid(run, capsys)


def test_runner_choice_differs(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, runner={'epoch': 509, 'ebops': 349_100, 'val_categorical_accuracy': 0.3009,
                                              'val_macro_auc': 0.83009})
    assert 'differs from the recomputed selection' in invalid(run, capsys)


def test_certification_fails(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    assert 'certify_ebops EBOPS_MISMATCH' in invalid(run, capsys, stub_hooks(cert_status='EBOPS_MISMATCH'))


def test_cpu_replay_disagrees(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    assert 'CPU replay' in invalid(run, capsys, stub_hooks(replay_shift=0.01))


def test_training_split_differs(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, train_sha='c' * 64)
    assert 'training split' in invalid(run, capsys)


def test_checkpoint_file_missing(tmp_path, capsys):
    run = make_run(tmp_path, squeeze, model_file=False)
    assert 'model_best.keras missing' in invalid(run, capsys)


def test_stop_epoch_off_snapshot_boundary(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    assert 'not a snapshot boundary' in invalid(run, capsys, extra=('--stop-epoch', '900'))


def test_missing_run_dir(tmp_path, capsys):
    code = score.main([str(tmp_path / 'nope'), '--code', str(TREE)], hooks=stub_hooks())
    out = capsys.readouterr().out.splitlines()
    assert code == 2 and out == [f"INVALID[infrastructure]: run directory missing: {tmp_path / 'nope'}"]


def test_existing_score_json_with_other_result_is_not_overwritten(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    (run / 'score-s1.json').write_text(json.dumps({'status': 'valid', 'score': 0.99}))
    assert 'exists with a different primary result' in invalid(run, capsys)
    assert json.loads((run / 'score-s1.json').read_text())['score'] == 0.99


def test_eval_file_tampered(tmp_path, capsys, monkeypatch):
    run = make_run(tmp_path, squeeze)
    fake = tmp_path / 'MANIFEST.json'
    data = json.loads((EVAL / 'MANIFEST.json').read_text())
    data['files']['readout_pilot.py'] = '0' * 64
    fake.write_text(json.dumps(data))
    monkeypatch.setattr(score, 'MANIFEST', fake)
    assert 'differs from MANIFEST.json' in invalid(run, capsys)


def test_internal_error_is_an_invalid_line(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    hooks = stub_hooks()
    hooks['certify'] = lambda *a: 1 / 0
    code = score.main([str(run), '--code', str(TREE)], hooks=hooks)
    out = capsys.readouterr().out.splitlines()
    assert code == 3 and len(out) == 1 and out[0].startswith('INVALID[evaluator]: internal error ZeroDivisionError')


def test_manifest_covers_the_copies_byte_for_byte():
    data = json.loads((EVAL / 'MANIFEST.json').read_text())
    src = {'readout_pilot.py': 'campaigns/pilot1005/readout_pilot.py', 'certify_ebops.py': 'campaigns/pilot1005/certify_ebops.py',
           'nondegenerate_threshold.py': 'campaigns/pilot1005/nondegenerate_threshold.py',
           'attn_entropy.py': 'analysis/attn_entropy.py'}
    for name, rel in src.items():
        assert (EVAL / name).read_bytes() == (TREE / rel).read_bytes(), name
        assert data['files'][name] == hashlib.sha256((EVAL / name).read_bytes()).hexdigest()


# --------------------------------------------------------------------------- real pieces
def test_threshold_rederivation_uses_the_frozen_script(tmp_path):
    """derive_threshold runs nondegenerate_threshold.py main unchanged on a small cache."""
    import numpy as np
    from bnhgq2.ablation import majority_rule
    cache = tmp_path / 'cache'
    cache.mkdir()
    y = np.eye(5, dtype='float32')[np.r_[np.zeros(30, int), np.arange(70) % 5]]
    np.save(cache / 'y_val.npy', y)
    (cache / 'data_info.json').write_text(json.dumps({'pt_gate_gev': 2.0, 'validation_split': 0.1, 'split_seed': 1}))
    got = score.derive_threshold(score.load('nondegenerate_threshold'), cache, BASE_CFG)
    want = majority_rule(y, 5)
    assert got['val_accuracy_threshold'] == want['val_accuracy_threshold'] and got['labels_sha256'] == want['labels_sha256']
    (cache / 'data_info.json').write_text(json.dumps({'pt_gate_gev': 1.0, 'validation_split': 0.1, 'split_seed': 1}))
    with pytest.raises(score.Invalid, match='pt_gate_gev'):
        score.derive_threshold(score.load('nondegenerate_threshold'), cache, BASE_CFG)


def test_end_to_end_tiny_run_real_certification_and_replay(tmp_path, capsys, monkeypatch):
    """Frozen runner on CPU (tiny option-(c) regime-B config, stop epoch 6 = snapshot), then the
    score with the real certify_checkpoint and the real CPU replay; only the cache loader and the
    threshold constants are substituted (the tiny run has its own labels)."""
    from bnhgq2 import ablation
    from test_d20_trace import arrays
    from test_pid_traced_only import option_c
    cfg = option_c()
    cfg['train']['epochs'] = 12
    cfg['experiment']['nondegenerate'] = {'zero_floor_ebops': 1, 'se_multiple': -5}   # every acc qualifies
    (xt, yt, xv, yv), info = arrays()
    info = {**info, 'train_sha256': TRAIN_SHA}
    run = tmp_path / 'run'
    ablation.run_training(cfg, (xt, yt, xv, yv), info, run, stop_after=6)
    capsys.readouterr()                       # the runner's own epoch lines are not the score's
    rule = json.loads((run / 'nondegenerate_rule.json').read_text())
    real_load = score.load

    def patched(name):
        m = real_load(name)
        if name == 'readout_pilot':
            m.THRESHOLD_C, m.LABELS_SHA256 = rule['val_accuracy_threshold'], rule['labels_sha256']
        return m
    monkeypatch.setattr(score, 'load', patched)
    hooks = dict(score.HOOKS)
    hooks['load_arrays'] = lambda cache, c: ((xt, yt, xv, yv), info)
    hooks['derive_threshold'] = lambda nt, cache, c: {k: rule[k] for k in ('val_accuracy_threshold', 'labels_sha256', 'n_val')}
    target = cfg['train']['ebops']['pid']['target_ebops']
    code = score.main([str(run), '--stop-epoch', '6', '--expect-target', str(target), '--code', str(TREE)], hooks=hooks)
    out = capsys.readouterr().out.splitlines()
    rec = json.loads((run / 'score-s1.json').read_text())
    assert code == 0 and len(out) == 1, (out, rec.get('invalid_reason'))
    state = json.loads((run / 'snapshots' / 'epoch-0006' / 'state.json').read_text())
    assert float(out[0]) == state['best_feasible']['val_categorical_accuracy']
    assert rec['certification']['status'] == 'CERTIFIED'
    assert rec['cpu_replay']['abs_acc_difference'] <= 1e-7
    # the tiny model has 8 constituents, attn_entropy requires 64: a secondary null with a reason
    assert rec['secondary']['attention_entropy']['mean'] is None and rec['secondary']['attention_entropy']['reason']
    # tampering with the logged EBOPs of the selected epoch makes certification fail
    lines = (run / 'activation_widths.jsonl').read_text().splitlines()
    sel = rec['selected']['epoch']
    recs = [json.loads(x) for x in lines]
    recs[sel]['ebops'] += 1
    (run / 'activation_widths.jsonl').write_text('\n'.join(json.dumps(r) for r in recs) + '\n')
    (run / 'score-s1.json').unlink()
    code = score.main([str(run), '--stop-epoch', '6', '--expect-target', str(target), '--code', str(TREE)], hooks=hooks)
    out = capsys.readouterr().out.splitlines()
    assert code == 2 and out[0].startswith('INVALID['), out


# --------------------------------------------------------------------------- B1: non-finite head entropy
class FakeAttn:
    def __init__(self, heads):
        self.heads = heads

    def load_checkpoint(self, path):
        return 'model'

    def analyze(self, model, x_val):
        return {'block0': {'heads': [{'entropy_over_log_n': h} for h in self.heads]}}


def test_nan_head_is_null_and_mean_is_over_finite_heads():
    out = score.entropy(FakeAttn([0.5, float('nan'), 0.7]), 'p', [0] * 5)
    assert out['heads'] == [0.5, None, 0.7] and out['n_heads_excluded'] == 1
    assert out['mean'] == pytest.approx(0.6) and out['reason'] is None
    assert 'all-zero softmax rows' in out['excluded_reason']
    json.dumps(out, allow_nan=False)
    none = score.entropy(FakeAttn([float('nan'), float('inf')]), 'p', [0])
    assert none['mean'] is None and none['reason'] and none['heads'] == [None, None]
    json.dumps(none, allow_nan=False)


def test_nan_head_does_not_invalidate_a_valid_score(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    hooks = stub_hooks()
    hooks['entropy'] = lambda attn, path, x_val: score.entropy(FakeAttn([0.4, float('nan')]), path, x_val)
    code, out = run_score(run, capsys, hooks)
    rec = json.loads((run / 'score-s1.json').read_text())
    assert code == 0 and len(out) == 1 and rec['status'] == 'valid' and float(out[0]) == rec['score']
    ent = rec['secondary']['attention_entropy']
    assert ent['mean'] == 0.4 and ent['heads'] == [0.4, None] and ent['n_heads_excluded'] == 1


# --------------------------------------------------------------------------- B2: per-attempt score files
def test_second_attempt_writes_its_own_file_and_leaves_the_first(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    bad = stub_hooks()
    bad['certify'] = lambda *a: 1 / 0
    code, out = run_score(run, capsys, bad)
    assert code == 3 and out[0].startswith('INVALID[evaluator]: internal error')
    first = (run / 'score-s1.json').read_bytes()
    code, out = run_score(run, capsys, extra=('--score-attempt', '2'))
    assert code == 0 and float(out[0]) == json.loads((run / 'score-s2.json').read_text())['score']
    assert json.loads((run / 'score-s2.json').read_text())['score_attempt'] == 2
    assert (run / 'score-s1.json').read_bytes() == first and not (run / 'score.json').exists()


def test_same_attempt_different_result_still_refused(tmp_path, capsys):
    run = make_run(tmp_path, squeeze)
    bad = stub_hooks()
    bad['certify'] = lambda *a: 1 / 0
    assert run_score(run, capsys, bad)[0] == 3
    code, out = run_score(run, capsys)           # attempt 1 again, now a valid result
    assert code == 2 and 'score file exists with a different primary result' in out[0]
    assert json.loads((run / 'score-s1.json').read_text())['status'] == 'invalid'
    assert run_score(run, capsys, bad)[0] == 3   # same result again is idempotent


# --------------------------------------------------------------------------- B3: reason classes
def literal_prefix(node):
    import ast
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        first = node.values[0] if node.values else None
        return first.value if isinstance(first, ast.Constant) else ''
    return None


def emitted_reason_prefixes():
    import ast
    tree = ast.parse((EVAL / 'score.py').read_text())
    found = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'need' and len(n.args) == 2:
            found.append(literal_prefix(n.args[1]))
        if isinstance(n, ast.Call) and getattr(n.func, 'id', None) == 'Invalid' and n.args:
            found.append(literal_prefix(n.args[0]))
    return found


def test_every_reason_score_can_emit_maps_to_exactly_one_class():
    data = json.loads((EVAL / 'INVALID_REASONS.json').read_text())
    assert data['version'] == 1 and data['match'] == 'prefix'
    assert set(data['classes']) == {'scientific', 'diverged', 'evaluator', 'infrastructure'}
    # Orchestrator decision after review v2 (B4): divergence is its own outcome class.
    assert data['classes']['scientific'] == ['no feasible checkpoint in epochs <']
    assert data['classes']['diverged'] == ['DIVERGED.json present']
    emitted = emitted_reason_prefixes()
    assert len(emitted) >= 20
    # score.py's own reasons (a bare name is the records gap), reasons of the copied modules, the
    # internal-error wrapper, and the certification status text
    extra = ['activation_widths.jsonl missing', 'records not contiguous 0..999 (have 3)', 'internal error ValueError: x']
    for p in emitted + extra:
        if p is None:
            continue                                  # need(gap, gap): covered by `extra`
        assert p, 'reason with no literal prefix'
        assert len(class_hits(p)) == 1, p
    ps = [p for ps in data['classes'].values() for p in ps]
    assert len(ps) == len(set(ps))
    assert score.classify('something unforeseen') == 'evaluator'
