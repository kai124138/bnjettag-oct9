#!/usr/bin/env python3
"""Frozen primary metric of campaigns/2026-10-08-discovery-350k (PROPOSAL.md §4).

python eval/score.py RUN_DIR [--stop-epoch 1000] [--expect-target 350000] [--score-attempt K] [--cache DIR] [--code DIR]

RUN_DIR is one run record directory (what run_study.train writes: config.json,
activation_widths.jsonl, nondegenerate_rule.json, snapshots/epoch-EEEE/, data_info.json).

Score: the validation top-1 accuracy of the best feasible checkpoint over zero-based epochs
< stop epoch, selected by the frozen key (accuracy, macro AUC, -EBOPs, -epoch). A checkpoint is
feasible when (a) its traced EBOPs <= the run's target and (b) above the 0-bit floor, (c) its
validation accuracy exceeds the non-degeneracy threshold (majority-class rate + 5 SE of y_val),
and (d) certify_ebops.py certifies its EBOPs (fresh reset retrace on the full training split,
relative tolerance 1e-6, <= target). The definitions are not reimplemented here: the record
reader, contiguity check and selection key are readout_pilot.py's (`records`, `key`,
`THRESHOLD_C`, `LABELS_SHA256`), the certification is certify_ebops.py's `certify_checkpoint`, the
threshold is re-derived by nondegenerate_threshold.py's `main` on the cache's y_val, and the
attention entropy is attn_entropy.py's `analyze`. Those files are byte copies of the pilot's,
checked against MANIFEST.json before anything else runs.

stdout: exactly one line. On success the score as a finite float; on any failure
`INVALID[<class>]: <reason>` and exit status 2 (an internal error also prints an INVALID line,
exit 3). <class> is scientific, evaluator or infrastructure, looked up by reason prefix in
INVALID_REASONS.json (an unmatched reason is evaluator). Everything else goes to stderr. The
result is written beside the record as RUN_DIR/score-s<K>.json (K = --score-attempt, default 1;
or --out) in both cases; an existing file of the same attempt with a different primary result is
itself INVALID and is never overwritten. A new attempt writes a new file and leaves the earlier
ones in place.

Input checks beyond the four conditions (each an INVALID reason): eval files match MANIFEST.json;
no DIVERGED.json; the config target equals --expect-target; the epoch-<stop> snapshot exists with
completed_epochs == stop; records contiguous 0..stop-1; nondegenerate_rule.json and every traced
record carry THRESHOLD_C and LABELS_SHA256 and the config's 0-bit floor; the threshold re-derived
from the cache equals THRESHOLD_C; the runner's best_feasible equals the recomputed selection; the
run's training split equals the cache's; the selected checkpoint's validation accuracy replayed on
CPU agrees with the logged value within REPLAY_ACC_TOL.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import traceback

HERE = Path(__file__).resolve().parent
DEFAULT_CACHE = '/data/chang-n64-20260926/n64/data'
EXPECT_TARGET = 350_000
STOP_EPOCH = 1000
SECONDARY_EPOCHS = (500, 1000)
WINDOW = 200                # best feasible accuracy per window of one-based epochs (slow-starter rule)
ACC_050 = 0.50
REPLAY_ACC_TOL = 1e-3       # |CPU replay - logged| validation accuracy of the selected checkpoint
MANIFEST = HERE / 'MANIFEST.json'
COPIES = ('readout_pilot.py', 'certify_ebops.py', 'nondegenerate_threshold.py', 'attn_entropy.py')
SCHEMA = 1
REASONS = HERE / 'INVALID_REASONS.json'
DEFAULT_CLASS = 'evaluator'


class Invalid(Exception):
    pass


def need(ok, reason):
    if not ok:
        raise Invalid(reason)


def classify(reason, path=None):
    """Class of an INVALID reason by literal prefix (INVALID_REASONS.json). A reason matched by no
    prefix, or by prefixes of more than one class, is DEFAULT_CLASS."""
    try:
        classes = json.loads(Path(path or REASONS).read_text())['classes']
    except Exception:
        return DEFAULT_CLASS
    hit = {c for c, prefixes in classes.items() if any(str(reason).startswith(p) for p in prefixes)}
    return hit.pop() if len(hit) == 1 else DEFAULT_CLASS


def sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    spec = importlib.util.spec_from_file_location(f'd350_eval_{name}', HERE / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_manifest():
    need(MANIFEST.is_file(), 'eval/MANIFEST.json missing')
    files = json.loads(MANIFEST.read_text())['files']
    for name, want in files.items():
        path = HERE / name
        need(path.is_file() and sha_file(path) == want, f'eval file {name} differs from MANIFEST.json')
    need(set(COPIES) | {'score.py'} <= set(files), 'MANIFEST.json does not cover every eval module')
    return hashlib.sha256(MANIFEST.read_bytes()).hexdigest()


# --------------------------------------------------------------------------- default hooks (real data)
def load_arrays(cache, cfg):
    """((x_train, y_train, x_val, y_val), info) through the frozen loader (hash-checked cache)."""
    import run_engram
    return run_engram.load_cache(Path(cache), cfg)


def derive_threshold(nt, cache, cfg):
    """nondegenerate_threshold.py `main`, unchanged, pointed at this run's config: it reads
    HERE/index.json -> configs/<file>, so it gets a one-row index of the run's config.json."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        (tmp / 'configs').mkdir()
        (tmp / 'configs' / 'config.json').write_text(json.dumps(cfg))
        (tmp / 'index.json').write_text(json.dumps({'runs': [{'file': 'config.json'}]}))
        out = tmp / 'threshold.json'
        old_here, old_argv = nt.HERE, sys.argv
        nt.HERE, sys.argv = tmp, ['nondegenerate_threshold.py', '--cache', str(cache), '--out', str(out)]
        try:
            nt.main()
        except SystemExit as exc:            # its own config/cache mismatch exits with a message
            raise Invalid(f'nondegenerate_threshold.py: {exc}') from None
        finally:
            nt.HERE, sys.argv = old_here, old_argv
        return json.loads(out.read_text())


def certify(cert, path, point, cfg, x_train):
    return cert.certify_checkpoint(path, point, cfg, x_train)


def replay_val(path, x_val, y_val, cfg):
    import keras
    import numpy as np
    from bnhgq2 import ablation
    keras.backend.clear_session()
    model = keras.models.load_model(path, compile=False)
    logits = np.asarray(model.predict(x_val, batch_size=cfg['train']['val_batch'], verbose=0))
    auc, _, acc = ablation.validation_metrics(y_val, logits)
    return float(acc), float(auc)


def entropy(attn, path, x_val):
    """attn_entropy.analyze on the selected checkpoint (validation split); mean over blocks and
    heads of entropy_over_log_n (row-renormalized, uniform = 1). None and a reason on failure."""
    import keras
    try:
        keras.backend.clear_session()
        model = attn.load_checkpoint(path)
        report = attn.analyze(model, x_val)
        raw = [h['entropy_over_log_n'] for blk in report.values() for h in blk['heads']]
        good = [h for h in raw if h is not None and math.isfinite(h)]
        heads = [h if h is not None and math.isfinite(h) else None for h in raw]     # JSON null, never NaN
        excluded = len(raw) - len(good)
        why = 'non-finite: all-zero softmax rows' if excluded else None
        if not good:
            return {'mean': None, 'heads': heads, 'n_heads_excluded': excluded, 'excluded_reason': why,
                    'reason': 'no heads' if not raw else 'no finite head entropy: ' + why}
        return {'mean': sum(good) / len(good), 'heads': heads, 'n_heads': len(raw),
                'n_heads_excluded': excluded, 'excluded_reason': why, 'n_val_rows': int(len(x_val)),
                'definition': 'attn_entropy.analyze: mean over jets and query rows of -sum p log p / log 64, '
                              'p row-renormalized; mean over blocks and heads', 'reason': None}
    except Exception as exc:                # secondary only: never changes the score
        return {'mean': None, 'reason': f'{type(exc).__name__}: {exc}'[:300]}


HOOKS = {'load_arrays': load_arrays, 'derive_threshold': derive_threshold, 'certify': certify,
         'replay_val': replay_val, 'entropy': entropy}


# --------------------------------------------------------------------------- scoring
def feasible_points(recs, target, floor, threshold):
    """Traced records meeting (a), (b), (c), as readout_pilot builds its candidates."""
    traced = [r for r in recs if r['ebops_traced'] == 1 and r['ebops'] is not None]
    ab = [r for r in traced if r['ebops'] <= target and r['ebops'] - floor > 0]
    return traced, [{'epoch': r['epoch'], 'ebops': r['ebops'], 'val_categorical_accuracy': r['val_categorical_accuracy'],
                     'val_macro_auc': r['val_macro_auc']} for r in ab if r['val_categorical_accuracy'] > threshold]


def secondary(run, recs, traced, feas, target, stop, readout):
    out = {}
    by_epoch = {r['epoch']: r for r in recs}
    fe = {p['epoch'] for p in feas}
    at = {}
    for e in SECONDARY_EPOCHS:
        if e > stop:
            continue
        r = by_epoch.get(e - 1)
        snap = run / 'snapshots' / f'epoch-{e:04d}' / 'state.json'
        best = json.loads(snap.read_text()).get('best_feasible') if snap.is_file() else None
        at[str(e)] = {'epoch_zero_based': e - 1, 'traced': bool(r and r['ebops_traced'] == 1),
                      'feasible': (e - 1) in fe,
                      'val_acc_if_feasible': r['val_categorical_accuracy'] if (e - 1) in fe else None,
                      'val_acc': r['val_categorical_accuracy'] if r else None,
                      'ebops': r['ebops'] if r else None,
                      'best_feasible_as_of_snapshot_val_acc': best['val_categorical_accuracy'] if best else None,
                      'best_feasible_as_of_snapshot_epoch': best['epoch'] if best else None,
                      'snapshot_present': snap.is_file()}
    out['at_epoch'] = at
    out['feasible_epochs'] = len(feas)
    out['feasible_epochs_acc_ge_050'] = sum(p['val_categorical_accuracy'] >= ACC_050 for p in feas)
    first = next((r['epoch'] for r in traced if r['ebops'] <= target), None)
    out['first_budget_met_epoch_zero_based'] = first
    out['first_budget_met_epoch_one_based'] = None if first is None else first + 1
    out['min_traced_ebops'] = min(int(r['ebops']) for r in traced) if traced else None
    windows = {}
    for lo in range(1, stop + 1, WINDOW):
        hi = min(lo + WINDOW - 1, stop)
        pts = [p for p in feas if lo - 1 <= p['epoch'] <= hi - 1]
        windows[f'{lo}-{hi}'] = max(pts, key=readout.key)['val_categorical_accuracy'] if pts else None
    out['best_feasible_acc_by_window_one_based'] = windows
    return out


def activation_bits(run, epoch):
    with (run / 'activation_widths.jsonl').open() as f:
        for line in f:
            if line.strip():
                row = json.loads(line)
                if int(row['epoch']) == epoch:
                    return {'activation_bits_mean': row.get('activation_bits_mean'),
                            'per_site_mean_bits': {k[len('activation_bits/'):]: v for k, v in row.items()
                                                   if k.startswith('activation_bits/')}}
    return None


def score_run(args, hooks=HOOKS):
    """Returns (score, report). Raises Invalid with the reason."""
    report = {'schema': SCHEMA, 'run_dir': str(args.run_dir), 'stop_epoch': args.stop_epoch,
              'score_attempt': args.score_attempt,
              'definition': 'PROPOSAL.md §4: best feasible validation top-1 accuracy over epochs < stop epoch, '
                            'key (acc, macro AUC, -EBOPs, -epoch); feasible = traced EBOPs <= target, above the '
                            '0-bit floor, acc > threshold, certify_ebops CERTIFIED',
              'split': 'validation (n from nondegenerate_rule.json)', 'test_set_used': False}
    report['eval_manifest_sha256'] = check_manifest()
    readout, cert, nt, attn = (load(n[:-3]) for n in COPIES)
    run = Path(args.run_dir)
    need(run.is_dir(), f'run directory missing: {run}')
    need(not (run / 'DIVERGED.json').exists(), 'DIVERGED.json present')
    need((run / 'config.json').is_file(), 'config.json missing')
    cfg = json.loads((run / 'config.json').read_text())
    report['config_name'] = cfg.get('name')
    report['config_json_sha256'] = sha_file(run / 'config.json')
    target = cfg['train']['ebops']['pid']['target_ebops']
    report['target_ebops'] = target
    need(target == args.expect_target, f'config target {target} != expected {args.expect_target}')
    floor = cfg['experiment']['nondegenerate']['zero_floor_ebops']
    report['zero_floor_ebops'] = floor
    snap_every = cfg['experiment'].get('snapshot_every_epochs')
    need(snap_every and args.stop_epoch % int(snap_every) == 0,
         f'stop epoch {args.stop_epoch} is not a snapshot boundary (snapshot_every_epochs {snap_every})')
    snap = run / 'snapshots' / f'epoch-{args.stop_epoch:04d}'
    need((snap / 'state.json').is_file(), f'snapshot epoch-{args.stop_epoch:04d} missing')
    state = json.loads((snap / 'state.json').read_text())
    need(int(state['completed_epochs']) == args.stop_epoch,
         f"snapshot completed_epochs {state['completed_epochs']} != {args.stop_epoch}")
    recs, gap = readout.records(run, args.stop_epoch)
    need(gap is None, gap or '')
    rule_path = run / 'nondegenerate_rule.json'
    need(rule_path.is_file(), 'nondegenerate_rule.json missing')
    rule = json.loads(rule_path.read_text())
    threshold = readout.THRESHOLD_C
    report['threshold'] = threshold
    report['labels_sha256'] = readout.LABELS_SHA256
    need(rule.get('val_accuracy_threshold') == threshold, f"run threshold {rule.get('val_accuracy_threshold')} != {threshold}")
    need(rule.get('labels_sha256') == readout.LABELS_SHA256, 'run validation labels sha differs')
    need(rule.get('zero_floor_ebops') == floor, f"run 0-bit floor {rule.get('zero_floor_ebops')} != config {floor}")
    report['n_val'] = rule.get('n_val')
    traced, feas = feasible_points(recs, target, floor, threshold)
    need(traced, 'no traced epoch')
    bad = {r['val_accuracy_threshold'] for r in traced} - {threshold}
    need(not bad, f'traced records carry another threshold: {sorted(map(str, bad))}')
    derived = hooks['derive_threshold'](nt, args.cache, cfg)
    report['threshold_rederived'] = {k: derived.get(k) for k in ('val_accuracy_threshold', 'labels_sha256', 'n_val', 'p_maj', 'se')}
    need(derived['val_accuracy_threshold'] == threshold, f"threshold from y_val {derived['val_accuracy_threshold']} != {threshold}")
    need(derived['labels_sha256'] == readout.LABELS_SHA256, 'labels sha from y_val differs')
    report['secondary'] = secondary(run, recs, traced, feas, target, args.stop_epoch, readout)
    best = max(feas, key=readout.key) if feas else None
    runner = state.get('best_feasible')
    report['selected'] = best
    need(best is not None or runner is not None, f'no feasible checkpoint in epochs < {args.stop_epoch}')
    need(best is not None and runner is not None and int(runner['epoch']) == best['epoch']
         and runner['val_categorical_accuracy'] == best['val_categorical_accuracy']
         and runner['val_macro_auc'] == best['val_macro_auc'] and runner['ebops'] == best['ebops'],
         f'runner best_feasible {runner and runner.get("epoch")} differs from the recomputed selection '
         f'{best and best["epoch"]}')
    path = snap / 'model_best.keras'
    need(path.is_file(), f'model_best.keras missing from snapshot epoch-{args.stop_epoch:04d}')
    report['selected'] = {**best, 'epoch_one_based': best['epoch'] + 1, 'checkpoint': str(path),
                          'checkpoint_sha256': sha_file(path)}
    (x_train, _, x_val, y_val), info = hooks['load_arrays'](args.cache, cfg)
    run_info = json.loads((run / 'data_info.json').read_text())
    need(run_info.get('train_sha256') and run_info.get('train_sha256') == info.get('train_sha256'),
         'run training split differs from the cache (data_info.json train_sha256)')
    record = hooks['certify'](cert, path, best, cfg, x_train)
    record = {k: v for k, v in record.items() if k != 'trace_seconds'}
    report['certification'] = record
    need(record['status'] == 'CERTIFIED', f"certify_ebops {record['status']} (logged {record['logged_ebops']}, "
                                          f"retraced {record['retraced_ebops']}, stored {record['stored_ebops']})")
    acc, auc = hooks['replay_val'](path, x_val, y_val, cfg)
    diff = abs(acc - best['val_categorical_accuracy'])
    report['cpu_replay'] = {'val_acc': acc, 'val_macro_auc': auc, 'abs_acc_difference': diff, 'tolerance': REPLAY_ACC_TOL}
    need(diff <= REPLAY_ACC_TOL, f'CPU replay accuracy {acc} differs from logged {best["val_categorical_accuracy"]} by {diff}')
    report['secondary']['selected_val_macro_auc'] = best['val_macro_auc']
    report['secondary']['selected_activation_bits'] = activation_bits(run, best['epoch'])
    report['secondary']['attention_entropy'] = (hooks['entropy'](attn, path, x_val) if not args.no_entropy
                                                else {'mean': None, 'reason': '--no-entropy'})
    score = float(best['val_categorical_accuracy'])
    need(math.isfinite(score), 'score not finite')
    return score, report


PRIMARY = ('status', 'score', 'invalid_reason', 'selected', 'stop_epoch', 'target_ebops', 'config_json_sha256')


def write_report(out, report):
    data = json.dumps(report, indent=1, sort_keys=True, allow_nan=False) + '\n'
    if out.exists():
        old = json.loads(out.read_text())
        if any(old.get(k) != report.get(k) for k in PRIMARY):
            raise Invalid(f'score file exists with a different primary result, not overwritten: {out}')
        print(f'SCORE_JSON_EXISTS_CONSISTENT {out}', file=sys.stderr)
        return
    tmp = out.with_name(out.name + '.tmp')
    tmp.write_text(data)
    os.replace(tmp, out)
    print(f'SCORE_JSON_WROTE {out} sha256 {hashlib.sha256(data.encode()).hexdigest()}', file=sys.stderr)


def main(argv=None, hooks=HOOKS):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('run_dir', type=Path)
    ap.add_argument('--stop-epoch', type=int, default=STOP_EPOCH)
    ap.add_argument('--expect-target', type=int, default=EXPECT_TARGET)
    ap.add_argument('--cache', type=Path, default=Path(os.environ.get('BNJ_SCORE_CACHE', DEFAULT_CACHE)))
    ap.add_argument('--code', type=Path, default=Path(os.environ.get('BNJ_SCORE_CODE', '/work/code')),
                    help='training code tree used to load the checkpoint (bnhgq2, run_engram)')
    ap.add_argument('--score-attempt', type=int, default=1,
                    help='score attempt K; the result goes to RUN_DIR/score-s<K>.json (a second attempt is for '
                         'evaluator or infrastructure INVALID reasons only, INVALID_REASONS.json)')
    ap.add_argument('--out', type=Path, help='default RUN_DIR/score-s<K>.json')
    ap.add_argument('--no-entropy', action='store_true', help='skip the attention-entropy secondary')
    args = ap.parse_args(argv)
    if args.score_attempt < 1:
        ap.error('--score-attempt must be >= 1')
    if str(args.code) not in sys.path:
        sys.path.insert(0, str(args.code))
    os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
    out = args.out or args.run_dir / f'score-s{args.score_attempt}.json'
    real_stdout = sys.stdout
    report = {'schema': SCHEMA, 'run_dir': str(args.run_dir), 'stop_epoch': args.stop_epoch}
    code = 0
    report['score_attempt'] = args.score_attempt
    try:
        with contextlib.redirect_stdout(sys.stderr):
            try:
                score, report = score_run(args, hooks)
                report.update(status='valid', score=score, invalid_reason=None)
            except Invalid as exc:
                report = {**report, 'status': 'invalid', 'score': None, 'invalid_reason': str(exc)}
                code = 2
            except Exception as exc:
                traceback.print_exc()
                report = {**report, 'status': 'invalid', 'score': None,
                          'invalid_reason': f'internal error {type(exc).__name__}: {exc}'[:500]}
                code = 3
            if report['status'] == 'invalid':
                report['invalid_class'] = classify(report['invalid_reason'])
            if args.run_dir.is_dir() or args.out:
                write_report(out, report)
    except Invalid as exc:
        report.update(status='invalid', score=None, invalid_reason=str(exc))
        code = code or 2
    except Exception as exc:
        report.update(status='invalid', score=None, invalid_reason=f'internal error {type(exc).__name__}: {exc}'[:500])
        code = 3
    line = repr(report['score']) if report['status'] == 'valid' and code == 0 else \
        f"INVALID[{classify(report['invalid_reason'])}]: " + ' '.join(str(report['invalid_reason']).split())
    print(line, file=real_stdout, flush=True)
    return code


if __name__ == '__main__':
    raise SystemExit(main())
