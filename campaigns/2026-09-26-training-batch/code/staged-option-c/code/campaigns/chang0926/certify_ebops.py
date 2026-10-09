#!/usr/bin/env python3
"""[D20] EBOPs certification of every checkpoint that will be evaluated, before ROC-test.

python campaigns/chang0926/certify_ebops.py --run-root /data/chang-n64-20260926/runs \
    --cache /data/chang-n64-20260926/n64/data --out cert.json [--snapshot 500] \
    [--trainval-dir DIR]

Terminal mode (default): the checkpoints `evaluate_roc.targets` lists (primary
`model_best.keras`, [A19] `model_best_auc_feasible.keras`, and for A and D the epoch-1,000
snapshot). `--snapshot E`: the best-feasible-as-of-E snapshot files (pilot rule at 500).
Each file is loaded fresh and retraced with `trace_minmax(reset=True)` on the full training
split of the run's cache (the [D20] sample) at the run's `train.ebops_trace_batch`. It is
CERTIFIED if the retraced EBOPs equals the EBOPs logged when it was selected (relative
difference <= 1e-6) and is <= the run's target. The retrace lives in memory only: no file
is rewritten, and `predict` later runs on the ranges as saved. A mismatch is a pipeline
defect reported at VERIFY, never a reason to reselect.

`--trainval-dir`: the labelled sensitivity (Chang's `trace_and_save` convention). A second
fresh copy is retraced on train + validation and saved to DIR/<run>__<which>__trainval.keras
with its EBOPs; never used for selection or feasibility, never written into the run dir.

Why a retrace and not only the stored widths: the saved file carries every width and each
layer's stored `ebops` (written by the per-epoch trace), and their sum is recorded here as
`stored_ebops`. Comparing it with the log proves the file is the one that was logged; it
cannot prove the logged number came from a full-split trace (a run traced on 256 rows
would pass it). The reset retrace on the full training split is the independent check, so
it is the certification; the stored sum is recorded beside it and must agree too.

Run it where training ran (same GPU class, TF32 off): the min/max trace is exact
arithmetic on the activations, but a CPU/GPU rounding difference at a power-of-two boundary
would move one integer bit. The device is recorded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))
import numpy as np

REL_TOL = 1e-6


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run_state(run):
    latest = json.loads((run / 'latest.json').read_text())['checkpoint']
    return json.loads((run / 'checkpoints' / latest / 'state.json').read_text())


def snapshot_targets(run, epoch):
    snap = run / 'snapshots' / f'epoch-{epoch:04d}'
    if not (snap / 'state.json').exists():
        return []
    state = json.loads((snap / 'state.json').read_text())
    items = []
    if state.get('best_feasible'):
        items.append((f'snapshot{epoch}_primary', snap / 'model_best.keras', state['best_feasible']))
    if state.get('best_feasible_auc'):
        items.append((f'snapshot{epoch}_auc_sensitivity', snap / 'model_best_auc_feasible.keras',
                      state['best_feasible_auc']))
    return items


def certify_checkpoint(path, point, cfg, x_train):
    """Retrace one saved checkpoint on the [D20] rows; return the certification record."""
    import keras
    from bnhgq2 import ablation
    keras.backend.clear_session()
    model = keras.models.load_model(path, compile=False)
    stored = int(sum(int(layer.ebops) for layer in model.layers if getattr(layer, 'enable_ebops', False)))
    batch = ablation.ebops_trace_batch(cfg)
    start = time.monotonic()
    retraced = ablation.compute_ebops(model, x_train, batch_size=batch)['total']
    logged = int(point['ebops'])
    target = float(cfg['train']['ebops']['pid']['target_ebops'])
    rel = abs(retraced - logged) / max(abs(logged), 1)
    equal = rel <= REL_TOL
    stored_equal = abs(stored - logged) / max(abs(logged), 1) <= REL_TOL
    status = 'CERTIFIED' if equal and stored_equal and retraced <= target else (
        'EBOPS_MISMATCH' if not equal else 'STORED_MISMATCH' if not stored_equal else 'ABOVE_TARGET')
    floor = cfg.get('experiment', {}).get('nondegenerate', {}).get('zero_floor_ebops')
    del model
    return {'checkpoint': str(path), 'checkpoint_sha256': sha(path), 'logged_ebops': logged,
            'retraced_ebops': int(retraced), 'stored_ebops': stored, 'relative_difference': rel, 'tolerance': REL_TOL,
            'zero_floor_ebops': floor, 'ebops_above_floor': (int(retraced) - int(floor)) if floor is not None else None,
            'target_ebops': target, 'epoch': point.get('epoch'), 'trace_rows': int(len(x_train)),
            'trace_batch': batch, 'trace_seconds': time.monotonic() - start, 'status': status}


def trainval_sensitivity(path, cfg, x_train, x_val, out_path):
    import keras
    from bnhgq2 import ablation
    keras.backend.clear_session()
    model = keras.models.load_model(path, compile=False)
    rows = np.concatenate([np.asarray(x_train), np.asarray(x_val)])
    ebops = ablation.compute_ebops(model, rows, batch_size=ablation.ebops_trace_batch(cfg))['total']
    model.save(out_path)
    del model
    return {'label': 'train+val retrace sensitivity (Chang trace_and_save convention); '
                     'never used for selection or feasibility',
            'file': str(out_path), 'file_sha256': sha(out_path), 'ebops_trainval': int(ebops),
            'trace_rows': int(len(rows))}


def main():
    import tensorflow as tf
    import run_engram
    from bnhgq2.compat import apply_keras_compat
    from evaluate_roc import targets
    tf.config.experimental.enable_tensor_float_32_execution(False)
    apply_keras_compat()
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--snapshot', type=int, help='certify the best-as-of-E snapshot (e.g. 500)')
    parser.add_argument('--only', default='', help='comma-separated run names')
    parser.add_argument('--trainval-dir', type=Path)
    args = parser.parse_args()
    if args.trainval_dir:
        args.trainval_dir.mkdir(parents=True, exist_ok=False)
    rows = json.loads((HERE / 'index.json').read_text())['runs']
    only = {n for n in args.only.split(',') if n}
    report = {'mode': f'snapshot-{args.snapshot}' if args.snapshot else 'terminal',
              'devices': [d.name for d in tf.config.list_physical_devices()],
              'gpu_details': [tf.config.experimental.get_device_details(d)
                              for d in tf.config.list_physical_devices('GPU')],
              'tf32': bool(tf.config.experimental.tensor_float_32_execution_enabled()),
              'runs': []}
    cache = None
    for row in rows:
        run = args.run_root / row['name']
        if (only and row['name'] not in only) or not run.exists():
            continue
        cfg = json.loads((run / 'config.json').read_text())
        entry = {'name': row['name'], 'arm': row['arm'], 'seed': row['seed'], 'checkpoints': []}
        if cfg['train'].get('ebops_trace_sample') != 'train_full':
            entry['status'] = 'not a [D20] run (train.ebops_trace_sample != train_full)'
        elif args.snapshot is None and (run / 'DIVERGED.json').exists():
            entry['status'] = 'diverged: no accuracy number, nothing to certify'
        else:
            if cache is None:
                cache = run_engram.load_cache(args.cache, cfg)
            (x_train, _, x_val, _), info = cache
            run_info = json.loads((run / 'data_info.json').read_text())
            assert run_info['train_sha256'] == info['train_sha256'], (row['name'], 'train split differs from cache')
            items = snapshot_targets(run, args.snapshot) if args.snapshot else targets(run, cfg, run_state(run))
            entry['status'] = 'checked' if items else 'no feasible checkpoint'
            for which, path, point in items:
                record = {'which': which, **certify_checkpoint(path, point, cfg, x_train)}
                if args.trainval_dir:
                    record['trainval_sensitivity'] = trainval_sensitivity(
                        path, cfg, x_train, x_val, args.trainval_dir / f"{row['name']}__{which}__trainval.keras")
                entry['checkpoints'].append(record)
                print(record['status'], row['name'], which, record['logged_ebops'], record['retraced_ebops'], flush=True)
        report['runs'].append(entry)
        args.out.write_text(json.dumps(report, indent=2) + '\n')
    bad = [(r['name'], c['which'], c['status']) for r in report['runs'] for c in r['checkpoints']
           if c['status'] != 'CERTIFIED']
    n = sum(len(r['checkpoints']) for r in report['runs'])
    report['summary'] = {'checkpoints': n, 'not_certified': bad}
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print('CERTIFICATION_ALL_PASS' if not bad else 'CERTIFICATION_FAIL', n, len(bad), flush=True)
    raise SystemExit(0 if not bad else 4)


if __name__ == '__main__':
    main()
