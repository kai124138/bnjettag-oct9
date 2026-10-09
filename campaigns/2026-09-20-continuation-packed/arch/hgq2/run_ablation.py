#!/usr/bin/env python3
"""Cluster entrypoint: prepare shared data once, or run one resumable ablation."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import tarfile
import urllib.request
import sys
import socket
socket.setdefaulttimeout(120)
import numpy as np

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
from bnhgq2.compat import apply_keras_compat
apply_keras_compat()
from bnhgq2.ablation import atomic_json, prepare_arrays, run_training, array_hash
from bnhgq2 import qat
import keras


def prepare(cfg, root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'prepare.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (root / 'READY.json').exists():
            print('[data] shared immutable arrays ready (existing)', flush=True)
            return
        data = root / 'raw'
        data.mkdir(exist_ok=True)
        if not (data / 'EXTRACTED').exists():
            archive = root / 'train.tar.gz'
            print('[data] fetching full Zenodo training split', flush=True)
            urllib.request.urlretrieve('https://zenodo.org/records/3602260/files/hls4ml_LHCjet_150p_train.tar.gz?download=1', archive)
            assert archive.stat().st_size == 2725115104
            with tarfile.open(archive) as tar:
                tar.extractall(data, filter='data')
            (data / 'EXTRACTED').write_text('complete\n')
            archive.unlink()
        directory = next(data.rglob('jetImage_*.h5')).parent
        arrays, info = prepare_arrays(cfg, str(directory))
        assert info['n_train'] == 496000 and info['n_val'] == 124000 and info['n_files'] == 62
        for name, array in zip(('x_train', 'y_train', 'x_val', 'y_val'), arrays):
            np.save(root / (name + '.npy'), array)
        atomic_json(root / 'data_info.json', info)
        atomic_json(root / 'READY.json', {'prepared': True, 'train_sha256': info['train_sha256']})
        print('[data] shared immutable arrays ready', flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=('prepare', 'train'))
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--benchmark-epochs', type=int)
    parser.add_argument('--track', action='store_true', help='Enable optional Weights & Biases tracking')
    parser.add_argument('--teacher-checkpoint', type=Path, help='Local teacher model_best.keras for knowledge distillation')
    args = parser.parse_args()
    cfg = json.loads(args.config.read_text())
    data = args.root / 'data'
    if args.stage == 'prepare':
        prepare(cfg, data)
        return
    import tensorflow as tf
    assert tf.config.list_physical_devices('GPU'), 'Training requires GPU'
    assert (data / 'READY.json').exists(), 'CPU data preparation required'
    arrays = tuple(np.load(data / (name + '.npy')) for name in ('x_train', 'y_train', 'x_val', 'y_val'))
    info = json.loads((data / 'data_info.json').read_text())
    assert array_hash(arrays[0]) == info['train_sha256'] and array_hash(arrays[2]) == info['val_sha256']
    out = args.root / 'runs' / cfg['experiment']['arm']
    out.mkdir(parents=True, exist_ok=True)
    with (out / 'run.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if (out / 'COMPLETE.json').exists():
            print('[train] already completed and committed; no duplicate run', flush=True)
            return
        teacher_logits = None
        if cfg['experiment'].get('distillation'):
            teacher_source = cfg['experiment']['distillation'].get('teacher_artifact')
            if args.teacher_checkpoint:
                teacher_dir = args.teacher_checkpoint.resolve().parent
                if args.teacher_checkpoint.name != 'model_best.keras':
                    raise ValueError('Teacher checkpoint must be named model_best.keras')
                teacher_source = str(args.teacher_checkpoint)
            elif teacher_source:
                import wandb
                teacher_dir = out / 'teacher'
                art = wandb.Api().artifact(teacher_source)
                art.download(root=str(teacher_dir))
            else:
                raise ValueError('Distillation requires --teacher-checkpoint or a versioned teacher_artifact')
            ts = json.loads((teacher_dir / 'input_std.json').read_text())
            for key in ('mu', 'sigma'):
                np.testing.assert_allclose(ts[key], info['input_std'][key], atol=1e-7, rtol=1e-6)
            teacher = keras.models.load_model(teacher_dir / 'model_best.keras', compile=False)
            teacher.trainable = False
            teacher_logits = np.asarray(teacher.predict(arrays[0], batch_size=1024, verbose=0), dtype='float32')
            assert np.isfinite(teacher_logits).all()
            atomic_json(out / 'teacher_provenance.json', {'teacher_source': teacher_source,
                         'logits_sha256': array_hash(teacher_logits), 'temperature': 2., 'coefficient': .5})
            del teacher
        run_training(cfg, arrays, info, out, teacher_logits=teacher_logits, remote=args.track, stop_after=args.benchmark_epochs)


if __name__ == '__main__':
    main()
