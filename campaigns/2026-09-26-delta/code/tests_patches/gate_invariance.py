"""Invariance gate (test b): run on a code tree, write a fingerprint JSON.

usage: pyenv.sh gate_invariance.py --tree <.../code> --out fp.json [--configs a07-n64 ...]

For each const0922 config: config digest, validate_cfg, model build through the S builder
(matching_initialization, seed 1) on a fixed synthetic sample, init kernel_hashes, model JSON
hash, initial EBOPs, forward predictions, binary gate, one epoch_step (512 synthetic jets,
batch 256 -> 2 optimizer steps), then hashes of every model and optimizer variable and the
epoch metrics. Two fingerprints (pristine tree vs patched tree) must be equal field by field.
Synthetic inputs only; nothing here is a result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

DEFAULT = ['a07-n64', 'a00-n8', 'a01-n64', 'b02-n64', 'b04-n8', 'a08-n64', 'e03-n8']


def h(a):
    a = np.ascontiguousarray(np.asarray(a))
    return hashlib.sha256(a.view(np.uint8)).hexdigest()[:16]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tree', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--configs', nargs='*', default=DEFAULT)
    args = p.parse_args()
    sys.path.insert(0, str(args.tree))
    import run_engram
    ablation, _ = run_engram.runtime()
    import keras
    import tensorflow as tf
    tf.config.experimental.enable_tensor_float_32_execution(False)
    result = {}
    for short in args.configs:
        t0 = time.monotonic()
        path = args.tree / 'configs' / f'const0922-{short}-s1-fast50-fp32.json'
        cfg = json.loads(path.read_text())
        run_engram.validate_cfg(cfg)
        keras.backend.clear_session()
        T, F = cfg['arch']['n_part'], cfg['arch']['n_feat']
        rng = np.random.default_rng(0)
        xt = rng.standard_normal((512, T, F)).astype('float32')
        yt = np.eye(5, dtype='float32')[rng.integers(0, 5, 512)]
        info = {'input_std': {'mu': [0., 0., 0.], 'sigma': [1., 1., 1.]}}
        model, evidence = run_engram.builder_for(info)(cfg, xt, 1)
        ablation.binary_gate(model, cfg)
        ebops = ablation.compute_ebops(model, xt[:256])
        preds = np.asarray(model(xt[:64], training=False))
        opt = ablation.optimizer_for(cfg, model)
        opt.learning_rate.assign(ablation.learning_rate(cfg, 0))
        step = ablation.make_epoch_step(model, opt, xt, yt, cfg)
        order = np.random.default_rng(1).permutation(512).astype('int32')
        metrics = [float(v) for v in step(order, False).numpy()]
        after = {v.path: h(v.numpy()) for v in model.weights}
        opt_vars = h(np.concatenate([np.asarray(v.numpy(), 'float64').ravel() for v in opt.variables]))
        result[short] = {
            'config_sha256': ablation.digest_json(cfg),
            'kernel_hashes': evidence['kernel_hashes'],
            'matched_weight_paths': evidence['matched_weight_paths'],
            'model_json_sha256': hashlib.sha256(model.to_json().encode()).hexdigest(),
            'params': model.count_params(),
            'initial_ebops': ebops['total'], 'initial_ebops_per_layer': ebops['per_layer'],
            'predictions': h(preds),
            'epoch_metrics': metrics,
            'weights_after_step': after, 'optimizer_after_step': opt_vars,
            'seconds': round(time.monotonic() - t0, 1),
        }
        print('FINGERPRINT', short, 'params', model.count_params(), 'ebops', ebops['total'],
              'seconds', result[short]['seconds'], flush=True)
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True) + '\n')


if __name__ == '__main__':
    main()
