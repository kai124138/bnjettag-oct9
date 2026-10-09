"""Bounded, read-only model evaluation; writes new diagnostics only.

Run in the pinned training environment with PYTHONPATH pointing at its code.
Capture committed checkpoint generations so state and model cannot race training.
"""
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

os.environ.setdefault('WANDB_MODE', 'disabled')
os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np
import tensorflow as tf
import keras
from bnhgq2.compat import apply_keras_compat
from bnhgq2.subln import register_subln
from bnhgq2.data import load_eval_set, apply_input_std
from bnhgq2.ebops_calc import compute_ebops
import bnhgq2.qat  # registers custom layers


def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def predict(model, x, batch=2048):
    @tf.function(input_signature=[tf.TensorSpec([None, 8, 3], tf.float32)])
    def infer(v):
        return model(v, training=False)
    infer(np.asarray(x[:8]))  # trace outside throughput measurement
    start = time.perf_counter()
    z = np.concatenate([np.asarray(infer(np.asarray(x[i:i+batch])))
                        for i in range(0, len(x), batch)])
    seconds = time.perf_counter() - start
    assert z.shape == (len(x), 5) and np.isfinite(z).all()
    return z, seconds


def main():
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    apply_keras_compat()
    register_subln()
    root = Path(os.environ.get('DIAG_ROOT', '/data/ebops-n8-20260912-ablation'))
    output = Path(os.environ['DIAG_OUTPUT'])
    output.mkdir(parents=True, exist_ok=False)
    xv = np.load(root / 'data/x_val.npy', mmap_mode='r')
    yv = np.load(root / 'data/y_val.npy')
    xt, yt = load_eval_set('/data/hls4ml_lhc_jet/val/val', n_part=8,
                           features=['pt', 'etarel', 'phirel'])
    assert xv.shape == (124000, 8, 3) and xt.shape == (260000, 8, 3)
    for y in (yv, yt):
        assert y.shape[1] == 5 and np.isin(y, [0, 1]).all() and (y.sum(1) == 1).all()
    np.savez_compressed(output / 'labels.npz', validation=yv, test=yt)
    data_info = json.loads((root / 'data/data_info.json').read_text()) if (root / 'data/data_info.json').exists() else None
    manifest = {'versions': {'numpy': np.__version__, 'tensorflow': tf.__version__, 'keras': keras.__version__},
                'devices': [d.name for d in tf.config.list_physical_devices()],
                'data_info': data_info, 'runs': []}
    arms = os.environ.get('DIAG_ARMS', 'r0-baseline,r1-channel,r2-ffn32,r3-prob8,r4-gradual,r5-recovery,r6-distill').split(',')
    for arm in arms:
        run = root / 'runs' / arm
        generation = json.loads((run / 'latest.json').read_text())['checkpoint']
        source = run / 'checkpoints' / generation
        snap = output / 'snapshots' / arm
        snap.mkdir(parents=True)
        state = json.loads((source / 'state.json').read_text())
        selected = state['best_feasible']
        if selected is None:
            continue
        shutil.copyfile(source / 'model_best.keras', snap / 'model_best.keras')
        for name in ('input_std.json', 'config.json'):
            shutil.copyfile(run / name, snap / name)
        (snap / 'state.json').write_text(json.dumps(state, indent=2))
        cfg = json.loads((snap / 'config.json').read_text())
        assert cfg['arch']['n_part'] == 8 and cfg['arch']['features'] == ['pt', 'etarel', 'phirel']
        std = json.loads((snap / 'input_std.json').read_text())
        if data_info is not None:
            assert std['mu'] == data_info['input_std']['mu'] and std['sigma'] == data_info['input_std']['sigma']
        print(f'[load] {arm} {generation}', flush=True)
        model = keras.models.load_model(snap / 'model_best.keras', compile=False)
        zv, sv = predict(model, xv)
        zt, st = predict(model, apply_input_std(xt, std['mu'], std['sigma']))
        np.savez_compressed(output / f'{arm}.npz', validation_logits=zv, test_logits=zt)
        # Measure EBOPs after inference because trace_minmax can change model state.
        ebops = compute_ebops(model, np.asarray(xv[:2048]))
        rec = {'arm': arm, 'generation': generation, 'completed_epochs': state['completed_epochs'],
               'complete': (run / 'COMPLETE.json').exists(), 'selected': selected,
               'checkpoint_sha256': digest(snap / 'model_best.keras'), 'ebops': ebops,
               'validation_accuracy': float((zv.argmax(1) == yv.argmax(1)).mean()),
               'test_accuracy': float((zt.argmax(1) == yt.argmax(1)).mean()),
               'validation_inference_seconds': sv, 'test_inference_seconds': st,
               'timing_note': 'CPU/GPU batch throughput with batch=2048, includes host conversion; not FPGA latency',
               'prediction_sha256': digest(output / f'{arm}.npz')}
        assert ebops['total'] == selected['ebops'], (arm, ebops['total'], selected)
        manifest['runs'].append(rec)
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        print(json.dumps({k:v for k,v in rec.items() if k != 'ebops'}), flush=True)
        del model, zv, zt
        keras.utils.clear_session()
        gc.collect()
    print('[done]', flush=True)


if __name__ == '__main__':
    main()
