#!/usr/bin/env python3
"""Pilot-program round readout: one row per arm in the shared readout.json (STUDY.md §5, PROGRAM.json
`definitions.readout_fields`). Standard library only; reads files, trains nothing, never reads the
ROC-test set.

python campaigns/pilot1005/readout_pilot.py --run-root RUN_ROOT/runs --round R1 --bundle-sha256 SHA \
    --a26 a26.json --cert cert.json --controller-dir DIR --out OUT/readout.json [--epoch 500]

Inputs per arm (row of this directory's index.json):
  RUN_ROOT/runs/<name>/activation_widths.jsonl   per-epoch record (with and without option (c))
  .../snapshots/epoch-0500/state.json            the runner's state at the pause (best_feasible)
  .../latest.json -> checkpoints/<leaf>/state.json   committed epochs when no snapshot exists
  .../nondegenerate_rule.json                    threshold (c) and the validation labels sha
  .../DIVERGED.json                              a recorded divergence
  --a26      analysis/attn_entropy.py output for these runs at --epoch ([A26]; validation)
  --cert     certify_ebops.py --snapshot <epoch> output (registered relative 1e-6)
  --controller-dir/controller-<name>.json        monitor_p.py --json, option-(c) arms only

Per-arm fields (exactly these, in this order; validation n = 62,000, traced epochs < --epoch only):
  arm, hypothesis, arch, budget, option_c, warmup, seed   from index.json (campaign.pilot)
  epochs_done           committed epochs (snapshot state, else the latest checkpoint state)
  feasible_any          some traced epoch has (a) traced EBOPs <= budget and (b) EBOPs above the
                        architecture's 0-bit floor (training-batch STUDY.md:995-1012)
  min_traced_ebops      lowest traced EBOPs
  nondegenerate_best    the runner's best-feasible checkpoint exists in the epoch-<E> snapshot
                        (it meets (a), (b) and (c): val acc > threshold)
  best_feasible_val_acc / _auc   that checkpoint's validation accuracy / macro AUC, else null.
                        Recomputed from the records with the frozen key (acc, AUC, -EBOPs, -epoch)
                        and required to equal the runner's choice
  attn_entropy_norm_mean mean over blocks and heads of the a26 `entropy_over_log_n` (row-renormalized
                        entropy / log 64, uniform = 1) on the snapshot checkpoint a26 chose
                        (best-feasible, else model_min_ebops)
  status                complete | diverged | failed | cert_fail | audit_fail. complete: epochs_done
                        == --epoch, no divergence, inputs consistent, the selected checkpoint
                        CERTIFIED (if one exists), and CONTROLLER_AUDIT PASS for option-(c) arms
Top level: round, bundle_sha256, n_arms, complete (every expected arm present and complete), plus
threshold_c and labels_sha256 (the values found in the runs; PROGRAM.json integrity checks read
them) and arms. readout_detail.json beside it holds the reasons and cross-checks. Exit 0 when the
files are written; the verdict is in the file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDS = ('arm', 'hypothesis', 'arch', 'budget', 'option_c', 'warmup', 'seed', 'epochs_done', 'feasible_any',
          'min_traced_ebops', 'best_feasible_val_acc', 'best_feasible_val_auc', 'nondegenerate_best',
          'attn_entropy_norm_mean', 'status')
THRESHOLD_C = 0.2109624456315518          # training-batch PREFLIGHT.md:519, :550-552 (p_maj + 5 SE)
LABELS_SHA256 = 'e593f51fad6a19e14c1df783ab762ffd5dfd566b6b1df13ba251a41fa1ad7617'
STATUSES = ('complete', 'diverged', 'failed', 'cert_fail', 'audit_fail')


def read_json(path):
    return json.loads(Path(path).read_text())


def committed_epochs(run, epoch):
    """(epochs_done, state, source). The epoch-<E> snapshot state wins; else the latest checkpoint."""
    snap = run / 'snapshots' / f'epoch-{epoch:04d}' / 'state.json'
    if snap.is_file():
        state = read_json(snap)
        return int(state['completed_epochs']), state, 'snapshot'
    latest = run / 'latest.json'
    if latest.is_file():
        state = read_json(run / 'checkpoints' / read_json(latest)['checkpoint'] / 'state.json')
        return int(state['completed_epochs']), state, 'checkpoint'
    return 0, None, None


def records(run, limit):
    """Per-epoch records with epoch < limit, which must be contiguous from 0."""
    path = run / 'activation_widths.jsonl'
    out = []
    if not path.is_file():
        return out, 'activation_widths.jsonl missing' if limit else None
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if int(row['epoch']) < limit:
                out.append({k: row.get(k) for k in ('epoch', 'ebops', 'ebops_traced', 'val_categorical_accuracy',
                                                     'val_macro_auc', 'val_accuracy_threshold')})
    epochs = [r['epoch'] for r in out]
    if epochs != list(range(limit)):
        return out, f'records not contiguous 0..{limit - 1} (have {len(epochs)})'
    return out, None


def key(point):
    """The frozen selection key (ablation.checkpoint_selection_key, val_categorical_accuracy, AUC tie)."""
    return (point['val_categorical_accuracy'], point['val_macro_auc'], -point['ebops'], -point['epoch'])


def entropy_mean(entry):
    heads = [h['entropy_over_log_n'] for blk in entry['entropy'].values() for h in blk['heads']]
    if not heads or not all(isinstance(h, (int, float)) and math.isfinite(h) for h in heads):
        return None, heads
    return sum(heads) / len(heads), heads


def read_arm(row, args, a26_runs, cert_runs):
    pilot = {'arm': row['program_arm'], 'hypothesis': row['hypothesis'], 'arch': row['arch_name'],
             'budget': row['budget'], 'option_c': row['option_c'], 'warmup': row['warmup'], 'seed': row['seed']}
    out = {**pilot, 'epochs_done': 0, 'feasible_any': False, 'min_traced_ebops': None,
           'best_feasible_val_acc': None, 'best_feasible_val_auc': None, 'nondegenerate_best': False,
           'attn_entropy_norm_mean': None, 'status': 'failed'}
    detail = {'name': row['name'], 'problems': []}
    problems = detail['problems']
    run = args.run_root / row['name']
    if not run.is_dir():
        problems.append('run directory missing')
        return out, detail, set(), set()
    diverged = (run / 'DIVERGED.json').is_file()
    done, state, source = committed_epochs(run, args.epoch)
    out['epochs_done'] = done
    detail['state_source'] = source
    recs, gap = records(run, min(done, args.epoch))
    if gap:
        problems.append(gap)
    budget, floor = int(row['budget']), int(row['zero_floor_ebops'])
    traced = [r for r in recs if r['ebops_traced'] == 1 and r['ebops'] is not None]
    detail['traced_epochs'] = len(traced)
    thresholds = {r['val_accuracy_threshold'] for r in traced}
    labels = set()
    rule_path = run / 'nondegenerate_rule.json'
    if rule_path.is_file():
        rule = read_json(rule_path)
        labels.add(rule.get('labels_sha256'))
        thresholds.add(rule.get('val_accuracy_threshold'))
        if rule.get('zero_floor_ebops') != floor:
            problems.append(f"nondegenerate_rule zero_floor_ebops {rule.get('zero_floor_ebops')} != {floor}")
    elif done:
        problems.append('nondegenerate_rule.json missing')
    if thresholds - {THRESHOLD_C}:
        problems.append(f'threshold differs from {THRESHOLD_C}: {sorted(map(str, thresholds))}')
    if labels - {LABELS_SHA256}:
        problems.append(f'labels sha differs: {sorted(map(str, labels))}')
    if traced:
        out['min_traced_ebops'] = min(int(r['ebops']) for r in traced)
    feasible_ab = [r for r in traced if r['ebops'] <= budget and r['ebops'] - floor > 0]
    out['feasible_any'] = bool(feasible_ab)
    candidates = [{'epoch': r['epoch'], 'ebops': r['ebops'], 'val_categorical_accuracy': r['val_categorical_accuracy'],
                   'val_macro_auc': r['val_macro_auc']}
                  for r in feasible_ab if r['val_categorical_accuracy'] > THRESHOLD_C]
    recomputed = max(candidates, key=key) if candidates else None
    runner = (state or {}).get('best_feasible')
    detail['best_recomputed'] = recomputed
    detail['best_runner'] = runner
    if runner is not None:
        out['nondegenerate_best'] = True
        out['best_feasible_val_acc'] = runner['val_categorical_accuracy']
        out['best_feasible_val_auc'] = runner['val_macro_auc']
    if (runner is None) != (recomputed is None) or (runner is not None and int(runner['epoch']) != recomputed['epoch']):
        problems.append('runner best_feasible differs from the recomputed selection')
    if out['nondegenerate_best'] and not out['feasible_any']:
        problems.append('nondegenerate_best true while feasible_any false')
    a26 = a26_runs.get(row['name'])
    detail['a26'] = None if a26 is None else {k: a26.get(k) for k in ('status', 'checkpoint', 'checkpoint_reason')}
    if a26 is not None and a26.get('status') == 'ok':
        mean, heads = entropy_mean(a26)
        out['attn_entropy_norm_mean'] = mean
        detail['a26']['heads'] = heads
        want = 'model_best.keras' if out['nondegenerate_best'] else 'model_min_ebops.keras'
        if not str(a26.get('checkpoint', '')).endswith(f'epoch-{args.epoch:04d}/{want}'):
            problems.append(f'a26 checkpoint is not the snapshot {want}')
        if mean is None:
            problems.append('a26 entropy not finite')
    elif not diverged:
        problems.append('a26 entropy missing')
    cert = cert_runs.get(row['name'])
    primary = None if cert is None else next((c for c in cert.get('checkpoints', [])
                                              if c.get('which') == f'snapshot{args.epoch}_primary'), None)
    detail['cert'] = None if cert is None else {'status': cert.get('status'),
                                                 'checkpoints': {c.get('which'): c.get('status') for c in cert.get('checkpoints', [])}}
    cert_ok = (not out['nondegenerate_best']) or (primary is not None and primary.get('status') == 'CERTIFIED')
    audit_ok = True
    if row['option_c']:
        path = args.controller_dir / f"controller-{row['name']}.json"
        if path.is_file():
            report = read_json(path)
            detail['controller_audit_problems'] = len(report.get('audit_problems', []))
            audit_ok = report.get('audit_problems') == []
        else:
            detail['controller_audit_problems'] = None
            audit_ok = False
    if diverged:
        out['status'] = 'diverged'
    elif problems or done != args.epoch or source != 'snapshot':
        if done != args.epoch:
            problems.append(f'epochs_done {done} != {args.epoch}')
        out['status'] = 'failed'
    elif not cert_ok:
        out['status'] = 'cert_fail'
    elif not audit_ok:
        out['status'] = 'audit_fail'
    else:
        out['status'] = 'complete'
    detail['thresholds'] = sorted(map(str, thresholds))
    return out, detail, labels, thresholds


def runs_by_name(path, key_name):
    if path is None or not Path(path).is_file():
        return {}
    data = read_json(path)
    return {r['name']: r for r in data.get(key_name, [])}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--run-root', type=Path, required=True, help='.../runs')
    ap.add_argument('--round', required=True)
    ap.add_argument('--bundle-sha256', required=True)
    ap.add_argument('--a26', type=Path)
    ap.add_argument('--cert', type=Path)
    ap.add_argument('--controller-dir', type=Path, required=True)
    ap.add_argument('--epoch', type=int, default=500)
    ap.add_argument('--index', type=Path, default=HERE / 'index.json')
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(argv)
    if args.out.exists():
        ap.error(f'{args.out} exists; refusing to overwrite')
    index = read_json(args.index)
    rows = [r for r in index['runs'] if r['round'] == args.round]
    if not rows:
        ap.error(f'no index rows for round {args.round}')
    a26 = runs_by_name(args.a26, 'runs')
    if args.a26 is not None and a26:
        epoch = read_json(args.a26).get('epoch')
        if epoch != args.epoch:
            a26 = {}
            print(f'READOUT_A26_EPOCH_MISMATCH {epoch} != {args.epoch}', flush=True)
    cert = runs_by_name(args.cert, 'runs')
    arms, details, labels, thresholds = [], [], set(), set()
    for row in rows:
        arm, detail, arm_labels, arm_thresholds = read_arm(row, args, a26, cert)
        assert tuple(arm) == FIELDS and arm['status'] in STATUSES
        arms.append(arm)
        details.append(detail)
        labels |= arm_labels
        thresholds |= arm_thresholds
        print('READOUT_ARM', detail['name'], json.dumps(arm), 'problems', json.dumps(detail['problems']), flush=True)
    top = {'round': args.round, 'bundle_sha256': args.bundle_sha256, 'n_arms': len(rows),
           'complete': len(arms) == len(rows) and all(a['status'] == 'complete' for a in arms),
           'threshold_c': thresholds.pop() if len(thresholds) == 1 else None,
           'labels_sha256': labels.pop() if len(labels) == 1 else None,
           'arms': arms}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    for path, value in ((args.out, top), (args.out.with_name('readout_detail.json'),
                                          {'round': args.round, 'epoch': args.epoch, 'arms': details})):
        tmp = path.with_suffix(path.suffix + '.tmp')
        tmp.write_text(json.dumps(value, indent=1, allow_nan=False) + '\n')
        os.replace(tmp, path)
    digest = hashlib.sha256(args.out.read_bytes()).hexdigest()
    print('READOUT_WROTE', args.out, 'sha256', digest, 'complete', top['complete'], 'n_arms', top['n_arms'], flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
