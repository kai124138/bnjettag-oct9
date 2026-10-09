"""Invariance gate on the anchor tree (chang0926 bundle 77f1ca4e): run on a code tree, write a
fingerprint JSON. Two fingerprints (pristine anchor extract vs anchor + patches-anchor) must be
equal field by field (compare_fp.py).

usage: pyenv.sh gate_invariance_anchor.py --tree <.../code> --out fp.json
           [--arms A,A07-350,...] [--seeds 1,2] [--const a07-n64 ...] [--train A,A07-350]

Per config (the anchor's generated arm configs, campaigns/chang0926/configs, unmodified; and
the const0922 screen configs): config digest, run_engram.validate_cfg, the runner's builder
(run_engram.builder_for -> matching_initialization, the config's seed) on a fixed synthetic
sample of 4,096 jets (as the runner, xt[:4096]), init kernel hashes, model JSON hash, count_params,
native EBOPs on the config's trace rows/batch ([D20]), the PID-read EBOPs (model_ebops), the
i_decay_speed record, LR at the schedule landmarks, predictions, binary gate, then ONE epoch
(make_epoch_step over n >= 2 * train.batch synthetic jets, >= 2 optimizer steps at the config's
own batch) with the runner's optimizer dispatch (delta_optimizer_for when the tree has it,
else optimizer_for), then hashes of every model and optimizer variable and the epoch metrics.

--train: additionally a 2-epoch ablation.run_training per arm (seed 1) on synthetic rows with
epochs=2, batch=128, val_batch=256 set identically on both sides (the anchor's own
regress_train.py procedure): per-epoch records minus wall-clock fields, the saved selected
checkpoints' weights, and the file list. Synthetic inputs only; nothing here is a result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

WALL = ('epoch_seconds', 'ebops_trace_seconds', 'ebops_reload_check_seconds', 'ebops_trace_over_epoch')


def h(a):
    a = np.ascontiguousarray(np.asarray(a))
    return hashlib.sha256(a.view(np.uint8)).hexdigest()[:16]


def fingerprint(cfg, run_engram, ablation, keras):
    keras.backend.clear_session()
    run_engram.validate_cfg(cfg)
    T, F = cfg['arch']['n_part'], cfg['arch']['n_feat']
    batch = int(cfg['train']['batch'])
    n = max(512, 2 * batch + 20)
    rng = np.random.default_rng(0)
    xt = rng.standard_normal((n, T, F)).astype('float32')
    yt = np.eye(5, dtype='float32')[rng.integers(0, 5, n)]
    info = {'input_std': {'mu': [0.] * F, 'sigma': [1.] * F}}
    seed = cfg['experiment']['seed']
    model, evidence = run_engram.builder_for(info)(cfg, xt[:4096], seed)
    ablation.binary_gate(model, cfg)
    sample = ablation.ebops_trace_sample(cfg, xt[:4096]) if hasattr(ablation, 'ebops_trace_sample') else xt[:256]
    tb = ablation.ebops_trace_batch(cfg) if hasattr(ablation, 'ebops_trace_batch') else 2048
    ebops = ablation.compute_ebops(model, sample, batch_size=tb)
    pid_ebops = ablation.model_ebops(model) if hasattr(ablation, 'model_ebops') else None
    decay = ablation.i_decay_speeds(model) if hasattr(ablation, 'i_decay_speeds') else None
    preds = np.asarray(model(xt[:64], training=False))
    epochs = int(cfg['train']['epochs'])
    lrs = {str(e): ablation.learning_rate(cfg, e) for e in sorted({0, 9, 10, 489, 490, 499, 500, epochs - 1})
           if e < epochs}
    opt = getattr(ablation, 'delta_optimizer_for', ablation.optimizer_for)(cfg, model)
    opt.learning_rate.assign(ablation.learning_rate(cfg, 0))
    qat = sys.modules.get('bnhgq2.qat')
    if qat is not None and hasattr(qat, 'set_delta_epoch'):
        qat.set_delta_epoch(cfg, 0)
    step = ablation.make_epoch_step(model, opt, xt, yt, cfg)
    order = np.random.default_rng(1).permutation(n).astype('int32')
    metrics = [float(v) for v in step(order, False).numpy()]
    ablation.binary_gate(model, cfg)
    after = {v.path: h(v.numpy()) for v in model.weights}
    opt_vars = h(np.concatenate([np.asarray(v.numpy(), 'float64').ravel() for v in opt.variables]))
    return {
        'config_sha256': ablation.digest_json(cfg),
        'kernel_hashes': evidence['kernel_hashes'],
        'matched_weight_paths': evidence.get('matched_weight_paths'),
        'model_json_sha256': hashlib.sha256(model.to_json().encode()).hexdigest(),
        'params': model.count_params(),
        'initial_ebops': ebops['total'], 'initial_ebops_per_layer': ebops['per_layer'],
        'pid_read_ebops': pid_ebops, 'i_decay_speed': decay, 'lr_landmarks': lrs,
        'optimizer_class': type(opt).__name__, 'n_optimizer_steps': -(-n // batch),
        'predictions': h(preds), 'epoch_metrics': metrics,
        'weights_after_step': after, 'optimizer_after_step': opt_vars,
    }


def train_fingerprint(cfg, ablation, keras, epochs=2):
    keras.backend.clear_session()
    cfg = json.loads(json.dumps(cfg))
    cfg['train'].update(epochs=epochs, batch=128, val_batch=256)
    T, F = cfg['arch']['n_part'], cfg['arch']['n_feat']
    rng = np.random.default_rng(0)
    xt = rng.standard_normal((768, T, F)).astype('float32')
    xv = rng.standard_normal((256, T, F)).astype('float32')
    yt = np.eye(5, dtype='float32')[rng.integers(0, 5, 768)]
    yv = np.eye(5, dtype='float32')[np.arange(256) % 5]
    info = {'unit': True, 'input_std': {'mu': [0.] * F, 'sigma': [1.] * F}}
    d = tempfile.mkdtemp()
    ablation.run_training(cfg, (xt, yt, xv, yv), info, d)
    recs = [json.loads(line) for line in open(os.path.join(d, 'activation_widths.jsonl'))]
    for r in recs:
        for k in WALL:
            r.pop(k, None)
    ckpt = {}
    for f in sorted(os.listdir(d)):
        if f.endswith('.keras'):
            m = keras.models.load_model(os.path.join(d, f), compile=False)
            ckpt[f] = hashlib.sha256(b''.join(np.asarray(v).tobytes() for v in m.weights)).hexdigest()
    leaves = sorted(p.name for p in Path(d, 'checkpoints').iterdir()) if Path(d, 'checkpoints').exists() else []
    leaf_files = {leaf: sorted(os.listdir(Path(d, 'checkpoints', leaf))) for leaf in leaves}
    return {'records_sha': hashlib.sha256(json.dumps(recs, sort_keys=True).encode()).hexdigest(),
            'record_keys': sorted(recs[0]), 'ebops': [r['ebops'] for r in recs], 'ckpt': ckpt,
            'files': sorted(os.listdir(d)), 'checkpoint_leaf_files': leaf_files}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tree', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--arms', default='')
    p.add_argument('--seeds', default='')
    p.add_argument('--const', nargs='*', default=[])
    p.add_argument('--train', default='')
    p.add_argument('--train-epochs', type=int, default=2,
                   help='epochs of the run_training fingerprint (12 crosses regime-B untraced epochs)')
    args = p.parse_args()
    sys.path.insert(0, str(args.tree))
    import run_engram
    ablation, _ = run_engram.runtime()
    import keras
    import tensorflow as tf
    tf.config.experimental.enable_tensor_float_32_execution(False)
    camp = args.tree / 'campaigns' / 'chang0926'
    rows = json.loads((camp / 'index.json').read_text())['runs']
    arms = {a.upper() for a in args.arms.split(',') if a}
    seeds = {int(s) for s in args.seeds.split(',') if s}
    result = {}
    for row in rows:
        if (arms and row['arm'].upper() not in arms) or (seeds and row['seed'] not in seeds):
            continue
        t0 = time.monotonic()
        cfg = json.loads((camp / 'configs' / row['file']).read_text())
        result[row['name']] = fingerprint(cfg, run_engram, ablation, keras)
        result[row['name']]['seconds'] = round(time.monotonic() - t0, 1)
        print('FINGERPRINT', row['name'], 'params', result[row['name']]['params'], 'ebops',
              result[row['name']]['initial_ebops'], 'seconds', result[row['name']]['seconds'], flush=True)
    for short in args.const:
        t0 = time.monotonic()
        cfg = json.loads((args.tree / 'configs' / f'const0922-{short}-s1-fast50-fp32.json').read_text())
        result['const0922-' + short] = fingerprint(cfg, run_engram, ablation, keras)
        result['const0922-' + short]['seconds'] = round(time.monotonic() - t0, 1)
        print('FINGERPRINT const0922-' + short, 'seconds', result['const0922-' + short]['seconds'], flush=True)
    for arm in [a for a in args.train.split(',') if a]:
        row = next(r for r in rows if r['arm'].upper() == arm.upper() and r['seed'] == 1)
        t0 = time.monotonic()
        cfg = json.loads((camp / 'configs' / row['file']).read_text())
        key = f'run_training-{args.train_epochs}ep-' + row['name']
        result[key] = train_fingerprint(cfg, ablation, keras, args.train_epochs)
        result[key]['seconds'] = round(time.monotonic() - t0, 1)
        print('FINGERPRINT', key, 'seconds', result[key]['seconds'], flush=True)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
