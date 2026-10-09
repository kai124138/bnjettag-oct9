#!/usr/bin/env python3
"""[A22] pairing prerequisite for NB (patch 0036): NB's initial kernels equal A's at seeds 1-8.

python campaigns/pilot1005/pair_nb.py [--seeds 1,2,3,4,5,6,7,8] [--out pairing.json]

For each seed s: A = campaigns/chang1002c/configs/chang1002c-a-n64-s<s>.json (option-(c) arm A),
NB = the same config with quant.weight "kbi_learnable" (the only change, as pilot1005/generate.py makes
the NB350-C arm). Both go through `ablation.matching_initialization` on the cpu_gate synthetic sample
(standard normal, 4,096 x 64 x 3, numpy seed 0) at seed s; the `kernel_hashes` must be equal.
Prints NB_PAIRED_OK <seed> per seed and NB_PAIRING_ALL_OK <n> at the end; exit 1 on any mismatch.
Synthetic data: nothing here is a result.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import numpy as np

A_DIR = HERE.parent / 'chang1002c' / 'configs'


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', default='1,2,3,4,5,6,7,8')
    ap.add_argument('--out', type=Path)
    args = ap.parse_args(argv)
    import keras
    import tensorflow as tf
    import run_engram
    ablation, _ = run_engram.runtime()
    tf.config.experimental.enable_tensor_float_32_execution(False)
    rng = np.random.default_rng(0)
    x = rng.standard_normal((4096, 64, 3)).astype('float32')
    report, bad = [], []
    for seed in [int(s) for s in args.seeds.split(',')]:
        a = json.loads((A_DIR / f'chang1002c-a-n64-s{seed}.json').read_text())
        nb = copy.deepcopy(a)
        nb['quant']['weight'] = 'kbi_learnable'
        hashes = {}
        for label, cfg in (('A', a), ('NB', nb)):
            keras.backend.clear_session()
            run_engram.validate_cfg(cfg)
            model, evidence = ablation.matching_initialization(cfg, x, seed)
            hashes[label] = evidence['kernel_hashes']
            del model
        same = hashes['A'] == hashes['NB'] and bool(hashes['A'])
        report.append({'seed': seed, 'equal': same, 'n_kernels': len(hashes['A']), 'A': hashes['A'], 'NB': hashes['NB']})
        print('NB_PAIRED_OK' if same else 'NB_PAIRING_MISMATCH', seed, 'kernels', len(hashes['A']), flush=True)
        if not same:
            bad.append(seed)
    if args.out:
        args.out.write_text(json.dumps(report, indent=1) + '\n')
    if bad:
        print('NB_PAIRING_FAIL', bad, flush=True)
        return 1
    print('NB_PAIRING_ALL_OK', len(report), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
