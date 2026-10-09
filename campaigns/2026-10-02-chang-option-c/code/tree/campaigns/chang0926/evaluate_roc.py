#!/usr/bin/env python3
"""[A11] ROC-test (held-out) predictions for the chang0926 runs, after the terminal epoch.

python campaigns/chang0926/evaluate_roc.py --run-root /data/chang-n64-20260926/runs \
    --cache /data/chang-n64-20260926/n64/data --eval-dir /data/hls4ml_lhc_jet/val/val --out DIR

Checkpoints are fixed by validation before this runs; nothing here selects anything.
Per run (STUDY "Selection rule"): the primary `model_best.keras`, the [A19] AUC-selected
sensitivity `model_best_auc_feasible.keras`, and for arms A and D the best-feasible-as-of-
epoch-1,000 snapshot `snapshots/epoch-1000/model_best.keras`. A run with DIVERGED.json or
without a feasible checkpoint gets no prediction ("no accuracy number"); the fallback
`model_min_ebops.keras` is never evaluated.

The held-out set is loaded with the same pT sort, top-64 truncation, feature subset and pT
gate as training (`load_eval_set(..., pt_gate_gev=cfg)`), then standardized with that run's
train-split `input_std.json`. Every run's `y` must be byte-identical. Each checkpoint is
loaded twice; logits must agree within 1e-7, and the validation replay must reproduce the
recorded selection metrics within 1e-7. Writes <out>/<run>__<which>.npz with keys y, score
(softmax), logits, meta (the r14 layout plus logits) and <out>/manifest.json. It computes
no summary metric: results-analyst does that at VERIFY.

[D20] (patch 0019): every evaluated checkpoint must carry a CERTIFIED record with the same
file sha256 in `--certification` (certify_ebops.py output); an uncertified checkpoint is
refused. Beside every evaluation the per-quantizer WRAP overflow fraction on validation and
ROC-test is recorded ([L8], diagnostic, `bnhgq2.wrap_overflow`). `--trainval-dir` also
evaluates the train+val retrace copies written by certify_ebops.py, labelled
`<which>__trainval_retrace` (sensitivity, never primary). Pilot-only rows
(`production: false`, C') are never evaluated on ROC-test.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def array_sha(a):
    return hashlib.sha256(np.ascontiguousarray(a).view(np.uint8)).hexdigest()


def softmax(z):
    z = z.astype(np.float64) - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def predict_twice(path, x, batch=4096):
    import keras
    out = []
    for _ in range(2):
        model = keras.models.load_model(path, compile=False)
        out.append(np.asarray(model.predict(x, batch_size=batch, verbose=0)))
        del model
        keras.utils.clear_session()
        gc.collect()
    diff = float(np.max(np.abs(out[0] - out[1])))
    assert diff <= 1e-7, (str(path), diff)
    return out[0], diff


def targets(run, cfg, state):
    arm = cfg['campaign']['arm']
    items = []
    if state.get('best_feasible'):
        items.append(('primary', run / 'model_best.keras', state['best_feasible']))
    if state.get('best_feasible_auc'):
        items.append(('auc_sensitivity', run / 'model_best_auc_feasible.keras', state['best_feasible_auc']))
    snap = run / 'snapshots' / 'epoch-1000'
    if arm in ('A', 'D') and (snap / 'state.json').exists():
        snap_state = json.loads((snap / 'state.json').read_text())
        if snap_state.get('best_feasible'):
            items.append(('epoch1000', snap / 'model_best.keras', snap_state['best_feasible']))
    return items


def certified(cert, path):
    digest = sha(path)
    for run in cert['runs']:
        for record in run['checkpoints']:
            if record['checkpoint_sha256'] == digest and record['status'] == 'CERTIFIED':
                return record
    raise RuntimeError(f'{path}: no CERTIFIED EBOPs record for this file; run certify_ebops.py first')


def overflow(path, rows):
    import keras
    from bnhgq2.wrap_overflow import overflow_fractions
    model = keras.models.load_model(path, compile=False)
    result = overflow_fractions(model, rows)
    del model
    keras.utils.clear_session()
    gc.collect()
    return result


def main():
    import tensorflow as tf
    from bnhgq2.compat import apply_keras_compat
    from bnhgq2.data import load_eval_set, apply_input_std
    from bnhgq2.ablation import validation_metrics
    tf.config.experimental.enable_tensor_float_32_execution(False)
    tf.config.experimental.enable_op_determinism()
    apply_keras_compat()
    parser = argparse.ArgumentParser()
    parser.add_argument('--run-root', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--eval-dir', default='/data/hls4ml_lhc_jet/val/val')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--y-reference', type=Path, help='an r14 n64 .npz for the label/row alignment gate')
    parser.add_argument('--certification', type=Path, required=True, help='certify_ebops.py terminal-mode output')
    parser.add_argument('--trainval-dir', type=Path, help='certify_ebops.py --trainval-dir output (sensitivity)')
    args = parser.parse_args()
    cert = json.loads(args.certification.read_text())
    assert cert['mode'] == 'terminal', cert['mode']
    args.out.mkdir(parents=True, exist_ok=False)
    rows = json.loads((HERE / 'index.json').read_text())['runs']
    gate = {json.loads((HERE / 'configs' / r['file']).read_text())['arch']['pt_gate_gev'] for r in rows}
    assert len(gate) == 1
    gate_stats = {}
    x_raw, y = load_eval_set(args.eval_dir, n_part=64, features=['pt', 'etarel', 'phirel'],
                             pt_gate_gev=gate.pop(), gate_stats=gate_stats)
    assert x_raw.shape == (260000, 64, 3) and y.shape == (260000, 5)
    if args.y_reference:
        with np.load(args.y_reference, allow_pickle=True) as ref:
            assert np.array_equal(ref['y'], y), 'held-out labels / row order differ from the reference'
    x_val = np.load(args.cache / 'x_val.npy', mmap_mode='r')
    y_val = np.load(args.cache / 'y_val.npy')
    manifest = {'y_sha256': array_sha(y), 'n': int(len(y)), 'class_counts': y.sum(0).astype(int).tolist(),
                'gate_stats': gate_stats, 'eval_dir': args.eval_dir, 'runs': []}
    for row in rows:
        if not row.get('production', True):
            continue
        run = args.run_root / row['name']
        cfg = json.loads((HERE / 'configs' / row['file']).read_text())
        entry = {'name': row['name'], 'arm': row['arm'], 'seed': row['seed']}
        if (run / 'DIVERGED.json').exists():
            entry['status'] = 'diverged: no accuracy number'
        elif not (run / 'VERIFIED_COMPLETE.json').exists():
            entry['status'] = 'not complete'
        else:
            state = json.loads((run / 'checkpoints' / json.loads((run / 'latest.json').read_text())['checkpoint']
                                / 'state.json').read_text())
            std = json.loads((run / 'input_std.json').read_text())
            x = apply_input_std(x_raw, std['mu'], std['sigma'])
            entry['status'] = 'evaluated' if state.get('best_feasible') else 'no feasible checkpoint'
            entry['evaluations'] = []
            items = [(which, path, point, False) for which, path, point in targets(run, cfg, state)]
            if args.trainval_dir:
                items += [(which + '__trainval_retrace', args.trainval_dir / f"{row['name']}__{which}__trainval.keras",
                           point, True) for which, _, point, _ in list(items)]
            for which, path, point, sensitivity in items:
                certificate = None if sensitivity else certified(cert, path)
                val_logits, val_diff = predict_twice(path, x_val)
                auc, _, acc = validation_metrics(y_val, val_logits)
                if not sensitivity:   # the train+val retrace changes ranges, so no replay check
                    assert abs(acc - point['val_categorical_accuracy']) <= 1e-7 and abs(auc - point['val_macro_auc']) <= 1e-7, \
                        (row['name'], which, acc, auc, point)
                logits, diff = predict_twice(path, x)
                target = args.out / f"{row['name']}__{which}.npz"
                meta = {'run': row['name'], 'which': which, 'checkpoint': str(path), 'checkpoint_sha256': sha(path),
                        'selected': point, 'split': 'ROC-test (held-out)', 'n': int(len(y)),
                        'pt_gate_gev': cfg['arch']['pt_gate_gev'], 'reload_max_abs_logit_diff': diff,
                        'label': ('train+val retrace sensitivity, not primary' if sensitivity else 'as selected'),
                        'ebops_certificate': certificate,
                        'wrap_overflow': {'validation': overflow(path, x_val), 'roc_test': overflow(path, x)}}
                if sensitivity:
                    meta['validation_after_retrace'] = {'val_categorical_accuracy': acc, 'val_macro_auc': auc}
                np.savez_compressed(target, y=y, score=softmax(logits), logits=logits, meta=json.dumps(meta))
                entry['evaluations'].append({**meta, 'npz': target.name, 'npz_sha256': sha(target),
                                             'validation_replay_max_abs_logit_diff': val_diff})
                print('ROC_EVAL', row['name'], which, 'ok', flush=True)
        manifest['runs'].append(entry)
        (args.out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print('ROC_EVALUATION_WRITTEN', len(manifest['runs']), flush=True)


if __name__ == '__main__':
    main()
