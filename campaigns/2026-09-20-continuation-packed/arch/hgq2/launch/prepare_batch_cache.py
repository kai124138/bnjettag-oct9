"""Prepare immutable N8/N16/N32 caches from one existing training-data read."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
from bnhgq2.train import load_train_data
from bnhgq2.data import input_std_stats, apply_input_std

NAMES = ('x_train', 'y_train', 'x_val', 'y_val')


def array_hash(array):
    return hashlib.sha256(np.ascontiguousarray(array).view(np.uint8)).hexdigest()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(temporary, path)


def verify(cache, n_part, config, require_ready=True):
    ready = json.loads((cache / 'READY.json').read_text()) if require_ready else None
    info = json.loads((cache / 'data_info.json').read_text())
    assert (ready is None or ready['prepared']) and info['n_part'] == n_part
    assert info['features'] == config['arch']['features']
    assert info['split_seed'] == config['train']['split_seed']
    assert info['validation_split'] == config['train']['validation_split']
    assert info['order_seed'] == config['train']['order_seed']
    arrays = [np.load(cache / (name + '.npy'), mmap_mode='r') for name in NAMES]
    assert arrays[0].shape == (496000, n_part, 3) and arrays[2].shape == (124000, n_part, 3)
    assert arrays[1].shape == (496000, 5) and arrays[3].shape == (124000, 5)
    for name, array in zip(NAMES, arrays):
        assert array.dtype == np.float32 and np.isfinite(array).all()
        assert array_hash(array) == info['array_sha256'][name]
    assert info['train_sha256'] == info['array_sha256']['x_train']
    if ready is not None:
        assert ready['train_sha256'] == info['train_sha256']
    assert info['val_sha256'] == info['array_sha256']['x_val']
    for y in (arrays[1], arrays[3]):
        assert np.isin(y, [0, 1]).all() and (y.sum(1) == 1).all()
    return info


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--configs', type=Path, default=Path('/work/code/configs/batch20260917'))
    parser.add_argument('--root', type=Path, default=Path('/data/batch20260917'))
    parser.add_argument('--raw', type=Path, default=Path('/data/hls4ml_lhc_jet/train/train'))
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--n-parts', default='8,16,32')
    args = parser.parse_args()
    configs = [json.loads(p.read_text()) for p in sorted(args.configs.glob('*.json'))]
    assert len(configs) == 12, len(configs)
    requested = [int(x) for x in args.n_parts.split(',')]
    by_n = {}
    for cfg in configs:
        n = cfg['arch']['n_part']
        if n in by_n:
            ref = by_n[n]
            assert ref['arch']['features'] == cfg['arch']['features']
            assert all(ref['train'][k] == cfg['train'][k] for k in ('split_seed', 'validation_split', 'order_seed'))
        by_n[n] = cfg
    assert set(requested) <= set(by_n) == {8, 16, 32}
    args.root.mkdir(parents=True, exist_ok=True)
    raw_x = raw_y = None
    reports = []
    for n in requested:
        cfg = by_n[n]
        cache = args.root / f'n{n}' / 'data'
        if not args.verify_only:
            cache.mkdir(parents=True, exist_ok=True)
        with (cache / 'prepare.lock').open('a+b') as lock:
            fcntl.flock(lock, fcntl.LOCK_SH if args.verify_only else fcntl.LOCK_EX)
            if (cache / 'READY.json').exists():
                reports.append(verify(cache, n, cfg))
                print('[cache_verified]', str(cache), flush=True)
                continue
            assert not args.verify_only, f'cache not ready: {cache}'
            started = time.perf_counter()
            if raw_x is None:
                files = sorted(args.raw.glob('*.h5'))
                assert len(files) == 62, (str(args.raw), len(files))
                raw_manifest = [{'name': p.name, 'size': p.stat().st_size} for p in files]
                print('[raw_load]', str(args.raw), 'N32 once', flush=True)
                raw_x, raw_y, nfiles = load_train_data(str(args.raw), 32, features=cfg['arch']['features'])
                assert raw_x.shape == (620000, 32, 3) and raw_y.shape == (620000, 5) and nfiles == 62
                print('[raw_loaded]', raw_x.shape, flush=True)
            permutation = np.random.default_rng(cfg['train']['split_seed']).permutation(len(raw_x))
            # Preserve loader's feature-major memory layout before its canonical
            # first-axis shuffle: forcing C-contiguous here changes float32
            # reduction order and can change standardization cache hashes.
            x = raw_x[:, :n, :][permutation]
            y = raw_y[permutation]
            nv = int(len(x) * cfg['train']['validation_split'])
            assert nv == 124000
            mu, sigma = input_std_stats(x[nv:])
            arrays = (apply_input_std(x[nv:], mu, sigma), y[nv:], apply_input_std(x[:nv], mu, sigma), y[:nv])
            hashes = {name: array_hash(a) for name, a in zip(NAMES, arrays)}
            info = {
                'n_train': len(arrays[0]), 'n_val': len(arrays[2]), 'n_files': 62,
                'n_part': n, 'features': cfg['arch']['features'],
                'split_seed': cfg['train']['split_seed'], 'order_seed': cfg['train']['order_seed'],
                'validation_split': cfg['train']['validation_split'],
                'permutation_sha256': array_hash(permutation),
                'input_std': {'mu': mu.tolist(), 'sigma': sigma.tolist(), 'computed_from': 'train split only'},
                'train_sha256': hashes['x_train'], 'val_sha256': hashes['x_val'],
                'array_sha256': hashes, 'raw_source': str(args.raw), 'raw_files': raw_manifest,
                'code_sha256': os.environ['BNHGQ2_CODE_SHA256'],
            }
            previous = Path('/data/ebops-n8-20260912-ablation/data/data_info.json')
            if n == 8 and previous.exists():
                old = json.loads(previous.read_text())
                if old['split_seed'] == info['split_seed']:
                    for key in ('train_sha256', 'val_sha256', 'permutation_sha256'):
                        assert old[key] == info[key], (key, old[key], info[key])
                    info['previous_n8_cache_byte_identical'] = True
            for name, array in zip(NAMES, arrays):
                temporary = cache / (name + '.npy.tmp')
                with temporary.open('wb') as f:
                    # Canonical feature-major arrays must become contiguous only
                    # after statistics are fixed. Otherwise np.save iterates
                    # 8-KiB writes across the remote PVC and is latency bound.
                    np.save(f, np.ascontiguousarray(array))
                    f.flush()
                    os.fsync(f.fileno())
                os.replace(temporary, cache / (name + '.npy'))
            atomic_json(cache / 'data_info.json', info)
            verify(cache, n, cfg, require_ready=False)
            atomic_json(cache / 'READY.json', {'prepared': True, 'train_sha256': hashes['x_train'], 'code_sha256': os.environ['BNHGQ2_CODE_SHA256']})
            reports.append(verify(cache, n, cfg))
            print('[cache_ready]', str(cache), 'seconds', time.perf_counter() - started, flush=True)
            del arrays, x, y
    if not args.verify_only:
        atomic_json(args.root / 'cache_manifest.json', {'caches': reports})
    print('BATCH_CACHES_ALL_PASS', flush=True)

if __name__ == '__main__':
    main()
