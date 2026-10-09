#!/usr/bin/env python3
"""[A17] pairing with F: build <arm>-s{s} and F-s{s} through the production initializer
(ablation.matching_initialization) and compare `kernel_hashes`. Paired by seed only if
every entry present in one build only is `pos_table` and no shared entry differs
(`--arms a,b,d,r`, default a; under [D21] F carries the learned PE and the no-PE
E-family arms draw it with `pos_enc_none_consume_rng`). CPU; the sample is a fixed synthetic batch (the
kernel/bias/pos_table hashes do not depend on it; activation calibration does, and is not
compared). Prints A_F_PAIRING PAIRED|UNPAIRED and writes the evidence with --out."""
import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import numpy as np


def hashes(cfg, sample):
    import keras
    from bnhgq2 import ablation
    keras.backend.clear_session()
    model, evidence = ablation.matching_initialization(cfg, sample, cfg['experiment']['seed'])
    return evidence['kernel_hashes']


def main():
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    parser = argparse.ArgumentParser()
    parser.add_argument('--seeds', default='1')
    parser.add_argument('--arms', default='a')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    sample = np.random.default_rng(0).standard_normal((4096, 64, 3)).astype('float32')
    report = {}
    cache = {}

    def arm_hashes(arm, seed):
        if (arm, seed) not in cache:
            cfg = json.loads((HERE / 'configs' / f'chang0926-{arm}-n64-s{seed}.json').read_text())
            cache[arm, seed] = hashes(cfg, sample)
        return cache[arm, seed]
    for arm in args.arms.split(','):
        for seed in [int(s) for s in args.seeds.split(',')]:
            ha, hf = arm_hashes(arm, seed), arm_hashes('f', seed)
            only_a, only_f = sorted(set(ha) - set(hf)), sorted(set(hf) - set(ha))
            differ = sorted(k for k in set(ha) & set(hf) if ha[k] != hf[k])
            paired = all(k.endswith('pos_table') for k in only_a + only_f) and not differ
            report[f'{arm}-s{seed}'] = {'paired': paired, 'only_in_arm': only_a, 'only_in_f': only_f,
                                        'differing_shared': differ, 'n_shared': len(set(ha) & set(hf))}
            print(f'{arm.upper()}_F_PAIRING', 'seed', seed, 'PAIRED' if paired else 'UNPAIRED',
                  'only_in_arm', only_a, 'only_in_f', only_f, 'differing_shared', len(differ),
                  'of', len(set(ha) & set(hf)), flush=True)
    if args.out:
        args.out.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
