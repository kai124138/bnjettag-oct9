"""Extract frozen quantized head features; never fit on validation or held-out data."""
import hashlib
import json
import os
from pathlib import Path
import time

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('WANDB_MODE', 'disabled')
import numpy as np
import tensorflow as tf
import keras
from bnhgq2.compat import apply_keras_compat
from bnhgq2.subln import register_subln
from bnhgq2.data import load_eval_set, apply_input_std
import bnhgq2.qat


def main():
    start = time.perf_counter()
    tf.config.set_visible_devices([], 'GPU')
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    apply_keras_compat()
    register_subln()
    root = Path('/data/ebops-n8-20260912-ablation')
    snapshot = Path('/data/accuracy-diagnostics-20260917/snapshots/r1-channel')
    destination = Path('/data/accuracy-head-features-20260917')
    expected_sha = 'd76050090655a68546e8bee51b695ef34c42083bcbd52832758b96f0e06f6e4c'
    actual_sha = hashlib.sha256((snapshot / 'model_best.keras').read_bytes()).hexdigest()
    assert actual_sha == expected_sha, actual_sha
    cfg = json.loads((snapshot / 'config.json').read_text())
    std = json.loads((snapshot / 'input_std.json').read_text())
    data_info = json.loads((root / 'data/data_info.json').read_text())
    assert data_info['n_train'] == 496000 and data_info['n_val'] == 124000
    assert data_info['train_sha256'] != data_info['val_sha256']
    assert std['mu'] == data_info['input_std']['mu'] and std['sigma'] == data_info['input_std']['sigma']
    # Cache provenance declares distinct train/validation partitions; no row content
    # overlap claim is inferred from feature values, which can naturally repeat.
    xt = np.load(root / 'data/x_train.npy', mmap_mode='r')
    yt = np.load(root / 'data/y_train.npy', mmap_mode='r')
    xv = np.load(root / 'data/x_val.npy', mmap_mode='r')
    yv = np.load(root / 'data/y_val.npy', mmap_mode='r')
    assert xt.shape == (496000, 8, 3) and xv.shape == (124000, 8, 3)
    assert yt.shape == (496000, 5) and yv.shape == (124000, 5)
    assert hashlib.sha256(np.ascontiguousarray(xt).view(np.uint8)).hexdigest() == data_info['train_sha256']
    assert hashlib.sha256(np.ascontiguousarray(xv).view(np.uint8)).hexdigest() == data_info['val_sha256']
    train_indices = np.sort(np.random.default_rng(20260917).choice(len(xt), 100000, replace=False))
    assert len(np.unique(train_indices)) == 100000
    permutation = np.random.default_rng(data_info['split_seed']).permutation(len(xt) + len(xv))
    assert hashlib.sha256(permutation.view(np.uint8)).hexdigest() == data_info['permutation_sha256']
    train_source_indices = permutation[len(xv):][train_indices]
    assert not np.isin(train_source_indices, permutation[:len(xv)]).any()
    model = keras.models.load_model(snapshot / 'model_best.keras', compile=False)
    head = model.get_layer('head_fc2')
    assert head.enable_iq
    assert model.layers[-1] is head, model.layers[-1].name
    features_model = keras.Model(model.inputs, head.input)
    @tf.function(input_signature=[tf.TensorSpec([None, 8, 3], tf.float32)])
    def quantized_features(batch):
        return head.iq(features_model(batch, training=False), training=False)
    kernel = np.asarray(head.qkernel)
    bias = np.asarray(head.qbias) if head.bias is not None else np.zeros(5, dtype=np.float32)
    check_x = np.asarray(xv[:256])
    check_features = np.asarray(quantized_features(check_x))
    check_model = np.asarray(model(check_x, training=False))
    check_rebuilt = check_features @ kernel + bias
    max_error = float(np.max(np.abs(check_model - check_rebuilt)))
    np.testing.assert_allclose(check_rebuilt, check_model, atol=1e-5, rtol=1e-5)
    assert np.array_equal(check_rebuilt.argmax(1), check_model.argmax(1))
    destination.mkdir(parents=True, exist_ok=False)
    payload = {'train_indices': train_indices, 'train_source_indices': train_source_indices,
               'original_kernel': kernel, 'original_bias': bias}
    timings = {}
    def extract(name, x, y):
        t0 = time.perf_counter()
        out = np.concatenate([np.asarray(quantized_features(np.asarray(x[i:i+2048], dtype=np.float32)))
                              for i in range(0, len(x), 2048)])
        assert out.shape == (len(x), 32) and np.isfinite(out).all()
        labels = np.asarray(y).argmax(1)
        payload[name + '_x'] = out
        payload[name + '_y'] = labels
        timings[name] = time.perf_counter() - t0
        print('[features]', name, out.shape, timings[name], flush=True)
    extract('train', xt[train_indices], yt[train_indices])
    extract('validation', xv, yv)
    xe, ye = load_eval_set('/data/hls4ml_lhc_jet/val/val', n_part=8, features=['pt', 'etarel', 'phirel'])
    assert xe.shape == (260000, 8, 3) and ye.shape == (260000, 5)
    extract('test', apply_input_std(xe, std['mu'], std['sigma']), ye)
    np.savez_compressed(destination / 'features.npz', **payload)
    (destination / 'config.json').write_text(json.dumps(cfg, indent=2))
    (destination / 'head_config.json').write_text(json.dumps(head.get_config(), indent=2))
    manifest = {
        'checkpoint_sha256': actual_sha, 'train_sample_seed': 20260917,
        'data_info': data_info, 'train_indices_sha256': hashlib.sha256(train_indices.tobytes()).hexdigest(),
        'train_validation_disjoint_source_indices_verified': True,
        'head_name': head.name, 'head_class': type(head).__name__,
        'feature_definition': 'head_fc2.iq(backbone_output, training=False)',
        'n_train_subset': 100000, 'n_validation': 124000, 'n_test': 260000,
        'reconstruction_rows': 256, 'reconstruction_max_abs_error': max_error,
        'reconstruction_argmax_equal': True, 'inference_seconds': timings,
        'original_validation_accuracy': float(((payload['validation_x'] @ kernel + bias).argmax(1) == payload['validation_y']).mean()),
        'original_test_accuracy': float(((payload['test_x'] @ kernel + bias).argmax(1) == payload['test_y']).mean()),
        'versions': {'numpy': np.__version__, 'tensorflow': tf.__version__, 'keras': keras.__version__},
        'feature_sha256': hashlib.sha256((destination / 'features.npz').read_bytes()).hexdigest(),
        'total_seconds': time.perf_counter() - start,
    }
    (destination / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest, indent=2), flush=True)

if __name__ == '__main__':
    main()
