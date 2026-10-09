#!/usr/bin/env python3
"""Bounded synthetic preflight for the twelve 20260917 screening configurations.

This checks training mechanics, not physics accuracy or real-data budget attainment.
Run from any directory with this hgq2 directory on PYTHONPATH.
"""
import argparse
import copy
import gc
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
os.environ.setdefault('WANDB_MODE', 'disabled')
os.environ.setdefault('OMP_NUM_THREADS', '2')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')

import keras
import numpy as np
import tensorflow as tf
from bnhgq2 import qat
from bnhgq2.ablation import (
    array_hash, binary_gate, expected_binary_layers, matching_initialization,
    optimizer_for, run_training, seeded_run_name, training_status_summary,
)
from bnhgq2.compat import apply_keras_compat
from bnhgq2.ebops_calc import compute_ebops
from bnhgq2.ebops_target import activation_quantizers


def synthetic_arrays(cfg):
    rng = np.random.default_rng(1729)
    x = rng.normal(size=(60, cfg['arch']['n_part'], cfg['arch']['n_feat'])).astype('float32')
    y = np.eye(5, dtype='float32')[np.arange(60) % 5]
    return x[:40], y[:40], x[40:], y[40:]


def build_gradient_reload(cfg, directory):
    xt, yt, xv, _ = synthetic_arrays(cfg)
    model, evidence = matching_initialization(cfg, xt, cfg['experiment']['seed'])
    binary_gate(model, cfg)
    assert len(qat.effective_weight_values(model)) == 6 * cfg['arch']['n_layers'] + 3
    initial_logits = np.asarray(model(xv, training=False))
    assert np.isfinite(initial_logits).all()
    initial_kernels = evidence['kernel_hashes']
    optimizer = optimizer_for(cfg, model)
    trainables = tuple(model.trainable_variables)
    width_ids = {id(v) for _, q in activation_quantizers(model) if q.trainable and hasattr(q, '_f') for v in (q._i, q._f)}
    before = [np.asarray(v).copy() for v in trainables]
    with tf.GradientTape() as tape:
        logits = model(xt[:10], training=True)
        ce = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=yt[:10], logits=logits))
        resource = tf.add_n(model.losses) if model.losses else tf.constant(0.)
        loss = ce + resource
    gradients = tape.gradient(loss, trainables)
    assert np.isfinite(float(loss)), 'Nonfinite one-step loss'
    assert all(g is not None and np.isfinite(np.asarray(g)).all() for g in gradients), 'Missing/nonfinite gradient'
    assert any(np.any(np.asarray(g) != 0) for g, v in zip(gradients, trainables) if id(v) in width_ids), 'No width gradient'
    assert any(np.any(np.asarray(g) != 0) for g, v in zip(gradients, trainables) if id(v) not in width_ids), 'No weight gradient'
    optimizer.apply_gradients(zip(gradients, trainables))
    assert any(not np.array_equal(a, np.asarray(b)) for a, b in zip(before, trainables)), 'Optimizer changed no variable'
    binary_gate(model, cfg)
    cost = compute_ebops(model, xt[:20])['total']
    predictions = np.asarray(model(xv, training=False))
    path = directory / (cfg['name'] + '.keras')
    model.save(path)
    loaded = keras.models.load_model(path, compile=False)
    binary_gate(loaded, cfg)
    np.testing.assert_allclose(loaded(xv, training=False), predictions, atol=1e-6, rtol=1e-6)
    assert compute_ebops(loaded, xt[:20])['total'] == cost
    result = {'name': cfg['name'], 'n_part': cfg['arch']['n_part'], 'n_layers': cfg['arch']['n_layers'],
              'parameters': int(model.count_params()),
              'trainable_parameters': sum(int(np.prod(v.shape)) for v in model.trainable_variables),
              'binary_projection_count': len(expected_binary_layers(cfg)), 'gradient_step_passed': True,
              'save_reload_passed': True, 'synthetic_ebops': cost,
              'matched_projection_count': evidence['matched_projection_count'],
              'channel_tensor_forward_equivalence_checked': evidence['channel_tensor_forward_equivalence_checked']}
    del model, loaded, optimizer, trainables, gradients
    keras.backend.clear_session()
    gc.collect()
    return result, initial_logits, initial_kernels


def resume_check(original, directory, *, seed, compare_uninterrupted):
    cfg = copy.deepcopy(original)
    cfg['name'] = f"resume-{cfg['experiment']['arm']}-s{seed}"
    cfg['experiment']['seed'] = seed
    cfg['train'].update(epochs=2, batch=20, val_batch=20)
    cfg['train']['ebops']['pid'].update(warmup=0, target_ebops=10**12)
    arrays = synthetic_arrays(cfg)
    info = {'synthetic': True, 'input_std': {'mu': [0., 0., 0.], 'sigma': [1., 1., 1.]}}
    out = directory / cfg['name']
    first = run_training(cfg, arrays, info, out, stop_after=1)
    assert first['completed_epochs'] == 1 and not (out / 'COMPLETE.json').exists()
    history = out / 'activation_widths.jsonl'
    committed = history.read_bytes()
    checkpoint = out / 'checkpoints/epoch-0001/model.keras'
    digest = hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    # Retrying an already-reached rung must perform no extra epoch or checkpoint.
    retry = run_training(cfg, arrays, info, out, stop_after=1)
    assert retry['completed_epochs'] == 1
    assert history.read_bytes() == committed
    assert hashlib.sha256(checkpoint.read_bytes()).hexdigest() == digest
    assert not (out / 'checkpoints/epoch-0002').exists()
    with history.open('a') as handle:
        handle.write(json.dumps({'epoch': 999, 'uncommitted': True}) + '\n')
    changed = copy.deepcopy(cfg)
    changed['experiment']['selection_metric'] = 'val_macro_auc'
    try:
        run_training(changed, arrays, info, out)
    except AssertionError as error:
        assert 'Resume config mismatch' in str(error)
    else:
        raise AssertionError('Changed selection objective bypassed config guard')
    previous_hash = os.environ.get('BNHGQ2_CODE_SHA256')
    try:
        os.environ['BNHGQ2_CODE_SHA256'] = 'deliberate-preflight-wrong-code-hash'
        try:
            run_training(cfg, arrays, info, out)
        except AssertionError as error:
            assert 'Resume code mismatch' in str(error)
        else:
            raise AssertionError('Changed source hash bypassed resume guard')
    finally:
        if previous_hash is None:
            os.environ.pop('BNHGQ2_CODE_SHA256', None)
        else:
            os.environ['BNHGQ2_CODE_SHA256'] = previous_hash
    final = run_training(cfg, arrays, info, out)
    rows = [json.loads(line) for line in history.read_text().splitlines()]
    assert final['completed_epochs'] == 2 and [row['epoch'] for row in rows] == [0, 1]
    assert (out / 'COMPLETE.json').exists()
    selected = max(rows, key=lambda row: (row['val_categorical_accuracy'], row['val_macro_auc'], -row['ebops'], -row['epoch']))
    assert final['best_feasible']['epoch'] == selected['epoch']
    meta = json.loads((out / 'train_meta.json').read_text())
    assert meta['seed'] == seed
    assert meta['ebops_budget']['selection'] == 'max_accuracy_under_final_budget'
    if compare_uninterrupted:
        normal_out = directory / (cfg['name'] + '-uninterrupted')
        normal = run_training(cfg, arrays, info, normal_out)
        assert normal['pid'] == final['pid']
        a = keras.models.load_model(out / 'checkpoints/epoch-0002/model.keras', compile=False)
        b = keras.models.load_model(normal_out / 'checkpoints/epoch-0002/model.keras', compile=False)
        for av, bv in zip(a.weights, b.weights):
            np.testing.assert_allclose(av.numpy(), bv.numpy(), atol=1e-7, rtol=1e-6)
        with np.load(out / 'checkpoints/epoch-0002/optimizer.npz') as ao, np.load(normal_out / 'checkpoints/epoch-0002/optimizer.npz') as bo:
            assert set(ao.files) == set(bo.files)
            for key in ao.files:
                np.testing.assert_allclose(ao[key], bo[key], atol=1e-7, rtol=1e-6)
        del a, b
    summary = training_status_summary(final, 'val_categorical_accuracy', 2, paused=True)
    assert summary['completed_epochs'] == 2 and summary['phase'] == 'paused_for_promotion'
    assert summary['best_feasible_epoch'] == selected['epoch'] + 1
    assert summary['best_feasible_val_accuracy'] == selected['val_categorical_accuracy']
    assert seeded_run_name(cfg['name'], seed) == cfg['name']
    assert seeded_run_name('historical-arm', seed) == f'historical-arm-s{seed}'
    keras.backend.clear_session()
    gc.collect()
    return {'name': cfg['name'], 'seed': seed, 'resume_passed': True,
            'reached_rung_retry_did_not_train': True, 'config_and_code_guards_passed': True,
            'uninterrupted_equivalence_checked': compare_uninterrupted, 'summary': summary}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--configs', type=Path, default=Path(__file__).parent / 'configs/batch20260917')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    apply_keras_compat()
    tf.config.set_visible_devices([], 'GPU')
    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    paths = sorted(args.configs.glob('batch20260917-a*-s1.json'))
    assert len(paths) == 12, paths
    configs = [json.loads(path.read_text()) for path in paths]
    assert [cfg['name'] for cfg in configs] == [f'batch20260917-a{i:02d}-s1' for i in range(12)]
    assert all(cfg['experiment']['selection_metric'] == 'val_categorical_accuracy' for cfg in configs)
    start = time.monotonic()
    report = {'synthetic_regression_only': True, 'versions': {'tensorflow': tf.__version__, 'keras': keras.__version__, 'numpy': np.__version__},
              'build_gradient_reload': [], 'resume': []}
    with tempfile.TemporaryDirectory(prefix='batch-preflight-') as temporary:
        directory = Path(temporary)
        initials = {}
        for cfg in configs:
            record, logits, hashes = build_gradient_reload(cfg, directory)
            report['build_gradient_reload'].append(record)
            initials[cfg['name']] = logits, hashes
            print('CONFIG_PASS ' + json.dumps(record), flush=True)
        for channel, tensor in [(0, 1), (2, 3)]:
            a, b = (initials[f'batch20260917-a{i:02d}-s1'] for i in (channel, tensor))
            np.testing.assert_allclose(a[0], b[0], atol=2e-6, rtol=2e-6)
            assert a[1] == b[1], 'Channel/tensor initial kernels differ'
        # Future B05 changes probability precision: calibration must use its own forward path.
        probability = copy.deepcopy(configs[2])
        probability['name'] = 'preflight-channel-ffn32-prob8'
        probability['quant']['softmax_out_bits'] = 8
        record, _, _ = build_gradient_reload(probability, directory)
        report['softmax_variant'] = record
        print('SOFTMAX_VARIANT_PASS', flush=True)
        report['resume'].append(resume_check(configs[7], directory, seed=2, compare_uninterrupted=True))
        print('RESUME_L1_SEED2_PASS', flush=True)
        report['resume'].append(resume_check(configs[2], directory, seed=1, compare_uninterrupted=False))
        print('RESUME_CHANNEL_FFN32_PASS', flush=True)
    report['seconds'] = time.monotonic() - start
    report['passed'] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print('RESULT_JSON=' + json.dumps(report), flush=True)
    print('PREFLIGHT_ALL_PASS', flush=True)


if __name__ == '__main__':
    main()
