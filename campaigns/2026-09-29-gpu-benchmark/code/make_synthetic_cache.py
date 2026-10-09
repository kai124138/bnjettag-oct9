#!/usr/bin/env python3
"""CPU gate helper: a synthetic N=64 cache that passes run_engram.load_cache unchanged.

    python make_synthetic_cache.py OUT_DIR      # writes OUT_DIR/n64/data/{x,y}_{train,val}.npy, data_info.json, READY.json

run_engram.load_cache (bundle 42abed4b, l. 177-221) requires READY.json, data_info.json whose
n_part / features / split_seed / pt_gate_gev / validation_split match the config (order_seed null, as
the anchor cache: cache.order_seed_in_cache false), finite float32 arrays whose sha256 equal
data_info's, one-hot labels with every class present, and exactly 620,000 - 62,000 / 62,000 rows.
So the cache is full size (about 490 MB); bench_driver --test-rows slices it after loading.
Random numbers, seed 0: nothing trained on it is a result.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

N_RAW, N_VAL = 620000, 62000


def array_hash(a):   # ablation.array_hash
    return hashlib.sha256(np.ascontiguousarray(a).view(np.uint8)).hexdigest()


def main(out):
    data = Path(out) / 'n64' / 'data'
    data.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(0)
    n_train = N_RAW - N_VAL
    arrays = {'x_train': rng.standard_normal((n_train, 64, 3), dtype=np.float32),
              'y_train': np.eye(5, dtype=np.float32)[rng.integers(0, 5, n_train)],
              'x_val': rng.standard_normal((N_VAL, 64, 3), dtype=np.float32),
              'y_val': np.eye(5, dtype=np.float32)[rng.integers(0, 5, N_VAL)]}
    hashes = {}
    for name, a in arrays.items():
        np.save(data / f'{name}.npy', a)
        hashes[name] = array_hash(a)
    info = {'synthetic': True, 'n_part': 64, 'features': ['pt', 'etarel', 'phirel'], 'n_train': n_train,
            'n_val': N_VAL, 'split_seed': 1, 'order_seed': None, 'validation_split': 0.1, 'pt_gate_gev': 2.0,
            'permutation_sha256': 'synthetic', 'input_std': {'mu': [0.0, 0.0, 0.0], 'sigma': [1.0, 1.0, 1.0],
                                                             'computed_from': 'synthetic'},
            'train_sha256': hashes['x_train'], 'val_sha256': hashes['x_val'], 'array_sha256': hashes}
    (data / 'data_info.json').write_text(json.dumps(info, indent=2) + '\n')
    (data / 'READY.json').write_text(json.dumps({'prepared': True, 'synthetic': True,
                                                 'train_sha256': hashes['x_train']}) + '\n')
    print('SYNTHETIC_CACHE', data, json.dumps({k: v[:12] for k, v in hashes.items()}))


if __name__ == '__main__':
    main(sys.argv[1])
