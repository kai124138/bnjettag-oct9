#!/usr/bin/env python3
"""Local smoke run (home PC, exploration only, never quotable): one config through the real
`ablation.run_training` on a subset of the local raw hls4ml train files.

Same steps as `ablation.prepare_arrays` (split permutation, 2 GeV pT gate, train-only
standardisation) but on the first `--files` sorted files, so it is NOT the cluster cache. Config
changes: train.epochs only (and experiment checkpoint/snapshot cadences scaled down so the run
writes them). TF32 off as in run_study.train. Writes <out>/smoke_summary.json.

usage: smoke.py CONFIG --tree TREE --data DIR --files N --epochs E --out OUT
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('config', type=Path)
    ap.add_argument('--tree', type=Path, required=True)
    ap.add_argument('--data', type=Path, required=True)
    ap.add_argument('--files', type=int, default=10)
    ap.add_argument('--epochs', type=int, default=20)
    ap.add_argument('--out', type=Path, required=True)
    a = ap.parse_args()
    sys.path.insert(0, str(a.tree))
    import numpy as np
    import tensorflow as tf
    tf.config.experimental.enable_tensor_float_32_execution(False)
    gpus = tf.config.list_physical_devices('GPU')
    from bnhgq2 import ablation
    from bnhgq2.train import load_train_data
    from bnhgq2.data import apply_pt_gate
    from bnhgq2.data import input_std_stats, apply_input_std

    cfg = json.loads(a.config.read_text())
    cfg['train']['epochs'] = a.epochs
    cfg['experiment'].update(checkpoint_every_epochs=10, snapshot_every_epochs=10, remote_every_epochs=10)
    tr = cfg['train']
    t0 = time.monotonic()
    x, y, nfiles = load_train_data(str(a.data), cfg['arch']['n_part'], max_files=a.files,
                                   features=cfg['arch']['features'])
    perm = np.random.default_rng(tr['split_seed']).permutation(len(x))
    x, y = x[perm], y[perm]
    x = apply_pt_gate(x, cfg['arch']['features'], cfg['arch']['pt_gate_gev'])
    nv = int(len(x) * tr['validation_split'])
    xv, yv, xt, yt = x[:nv], y[:nv], x[nv:], y[nv:]
    mu, sigma = input_std_stats(xt)
    xt, xv = apply_input_std(xt, mu, sigma), apply_input_std(xv, mu, sigma)
    info = {'n_train': len(xt), 'n_val': len(xv), 'n_files': nfiles, 'split_seed': tr['split_seed'],
            'order_seed': tr['order_seed'], 'input_std': {'mu': mu.tolist(), 'sigma': sigma.tolist()},
            'source': f'LOCAL SMOKE: first {nfiles} sorted raw files of {a.data}, not the cluster cache'}
    load_s = time.monotonic() - t0
    a.out.mkdir(parents=True, exist_ok=True)
    t1 = time.monotonic()
    state = ablation.run_training(cfg, (xt, yt, xv, yv), info, a.out)
    wall = time.monotonic() - t1
    hist = [json.loads(l) for l in (a.out / 'activation_widths.jsonl').read_text().splitlines()]
    keep = ('epoch', 'loss', 'task_loss', 'train_categorical_accuracy', 'val_categorical_accuracy', 'ebops',
            'ebops_in_training', 'beta', 'epoch_seconds', 'activation_bits_mean', 'weight_bits_mean',
            'weight_zero_bits_fraction', 'attn_qk_all_zero')
    rows = [{**{k: h.get(k) for k in keep if k in h},
             **{k.split('/')[1]: round(v, 3) for k, v in h.items()
                if k.startswith('activation_bits/bit_block_0_attn_') and ('scores' in k or 'ctx' in k)}}
            for h in hist]
    budget = json.loads((a.out / 'ebops_budget.json').read_text())
    summary = {'config': cfg['name'], 'label': 'LOCAL SMOKE, exploration only, not quotable',
               'gpu': [d.name for d in gpus], 'n_train': len(xt), 'n_val': len(xv), 'files': nfiles,
               'epochs': a.epochs, 'load_seconds': load_s, 'train_wall_seconds': wall,
               'initial_ebops': state['initial_ebops'], 'history': rows,
               'selected': budget.get('selected'), 'weight_widths': budget.get('weight_widths')}
    (a.out / 'smoke_summary.json').write_text(json.dumps(summary, indent=1) + '\n')
    print('SMOKE_DONE', json.dumps({k: summary[k] for k in ('config', 'n_train', 'initial_ebops', 'train_wall_seconds')}))


if __name__ == '__main__':
    main()
