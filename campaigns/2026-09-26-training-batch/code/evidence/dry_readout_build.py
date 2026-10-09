"""CPU dry run of the epoch-500 readout (STUDY: before the pilot reaches epoch 500): build a
synthetic full-shape gated cache and epoch-500 snapshot layouts, so the readout Job scripts
(`manifests/readout-{a,b5,b3}-job.json`) run unmodified apart from path substitution.

    python dry_readout_build.py DRY_ROOT CODE_DIR OLD_CODE_DIR
(CODE_DIR: the extracted regime-B bundle's code/; OLD_CODE_DIR: the 77f1ca4e bundle's code/, whose
configs the regime-A run directories carry, as the running pilot's do)

Synthetic, nothing here is a result. The cache has the real shape (558,000 / 62,000 x 64 x 3,
float32, one-hot labels with every class), because `run_engram.load_cache` refuses any other
split. Each snapshot model is the production initializer on the real config, then one
full-split reset trace at batch 2,048 (the [D20] trace), saved: its stored EBOPs equal a
retrace, as a trained traced candidate's do. The run directory's config.json copies the bundle
config with `target_ebops` raised to 1e9 so an untrained model can certify (the pass path);
one file (F-s1 under pilot-b) logs traced + 1,000 to exercise EBOPS_MISMATCH and exit 4 (+1, the
first version, is inside certify_ebops.REL_TOL = 1e-6 at ~1e7 EBOPs and certified).
"""
import json
import os
from pathlib import Path
import shutil
import sys

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
DRY, CODE, OLD_CODE = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
sys.path.insert(0, str(CODE))
import numpy as np

A_ROOT = DRY / 'chang-n64-20260926' / 'pilot'
B_ROOT = DRY / 'chang-n64-20260926' / 'pilot-b'
CACHE = DRY / 'chang-n64-20260926' / 'n64' / 'data'
LAYOUT = {A_ROOT: ['chang0926-a-n64-s1', 'chang0926-a-n64-s2', 'chang0926-d-n64-s1',
                   'chang0926-cprime-n64-s1', 'chang0926-e1-n64-s1'],
          B_ROOT: ['chang0926-a-n64-s1', 'chang0926-a-n64-s2', 'chang0926-d-n64-s1',
                   'chang0926-cprime-n64-s1', 'chang0926-e1-n64-s1',
                   'chang0926-a07-350-n64-s1', 'chang0926-c-n64-s1', 'chang0926-f-n64-s1']}
MISMATCH = (B_ROOT, 'chang0926-f-n64-s1')
MISMATCH_OFFSET = 1000                   # relative ~1e-4 at ~1e7, above REL_TOL 1e-6
AUC_COPY = 'chang0926-a-n64-s1'          # also gets model_best_auc_feasible.keras ([A19])


def build_cache(ablation):
    if (CACHE / 'READY.json').exists():
        return json.loads((CACHE / 'data_info.json').read_text())
    CACHE.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260927)
    arrays = {}
    for split, n in (('train', 558000), ('val', 62000)):
        arrays['x_' + split] = rng.standard_normal((n, 64, 3), dtype=np.float32)
        arrays['y_' + split] = np.eye(5, dtype=np.float32)[np.arange(n) % 5][rng.permutation(n)]
    hashes = {k: ablation.array_hash(v) for k, v in arrays.items()}
    for k, v in arrays.items():
        np.save(CACHE / (k + '.npy'), v)
    info = {'n_train': 558000, 'n_val': 62000, 'n_part': 64, 'features': ['pt', 'etarel', 'phirel'],
            'split_seed': 1, 'order_seed': None, 'validation_split': 0.1, 'pt_gate_gev': 2.0,
            'input_std': {'mu': [0, 0, 0], 'sigma': [1, 1, 1]},
            'train_sha256': hashes['x_train'], 'val_sha256': hashes['x_val'], 'array_sha256': hashes,
            'code_sha256': 'synthetic-dry-run', 'synthetic': True}
    (CACHE / 'data_info.json').write_text(json.dumps(info, indent=1) + '\n')
    (CACHE / 'READY.json').write_text('{"synthetic": true}\n')
    return info


def main():
    import keras
    import tensorflow as tf
    import run_engram
    tf.config.experimental.enable_tensor_float_32_execution(False)
    ablation, _ = run_engram.runtime()
    info = build_cache(ablation)
    xt = np.load(CACHE / 'x_train.npy', mmap_mode='r')
    configs = CODE / 'campaigns' / 'chang0926' / 'configs'
    models = DRY / 'models'
    models.mkdir(exist_ok=True)
    traced = {}
    for name in sorted({n for names in LAYOUT.values() for n in names}):
        path = models / f'{name}.keras'
        meta = models / f'{name}.json'
        if meta.exists():
            traced[name] = json.loads(meta.read_text())['ebops']
            continue
        keras.backend.clear_session()
        cfg = json.loads((configs / f'{name}.json').read_text())
        model, _ = ablation.matching_initialization(cfg, np.asarray(xt[:4096]), cfg['experiment']['seed'])
        cost = ablation.compute_ebops(model, xt, batch_size=ablation.ebops_trace_batch(cfg))
        model.save(path)
        traced[name] = int(cost['total'])
        meta.write_text(json.dumps({'ebops': traced[name]}) + '\n')
        print('DRY_MODEL', name, 'full_split_traced_ebops', traced[name], flush=True)
    for root, names in LAYOUT.items():
        for name in names:
            run = root / 'runs' / name
            snap = run / 'snapshots' / 'epoch-0500'
            snap.mkdir(parents=True, exist_ok=True)
            source = (OLD_CODE if root == A_ROOT else CODE) / 'campaigns' / 'chang0926' / 'configs'
            cfg = json.loads((source / f'{name}.json').read_text())
            assert ('ebops_trace_every' in cfg['train']) == (root == B_ROOT)
            cfg['train']['ebops']['pid']['target_ebops'] = 10 ** 9     # synthetic: pass path
            (run / 'config.json').write_text(json.dumps(cfg, indent=2) + '\n')
            (run / 'data_info.json').write_text(json.dumps(info, indent=1) + '\n')
            logged = traced[name] + (MISMATCH_OFFSET if (root, name) == MISMATCH else 0)
            point = {'epoch': 499, 'ebops': logged, 'val_macro_auc': 0.5, 'val_categorical_accuracy': 0.2}
            state = {'completed_epochs': 500, 'best_feasible': point, 'lowest': point, 'best_auc': point,
                     'best_feasible_auc': point if name == AUC_COPY else None, 'synthetic': True}
            (snap / 'state.json').write_text(json.dumps(state, indent=1) + '\n')
            shutil.copyfile(models / f'{name}.keras', snap / 'model_best.keras')
            if name == AUC_COPY:
                shutil.copyfile(models / f'{name}.keras', snap / 'model_best_auc_feasible.keras')
    print('DRY_LAYOUT_READY', {str(k.name): v for k, v in LAYOUT.items()}, flush=True)


if __name__ == '__main__':
    main()
