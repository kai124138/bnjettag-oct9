#!/usr/bin/env python3
"""Non-degeneracy threshold (arbiter v3 fix 1) from the gated 90/10 validation labels, for PREFLIGHT.

python campaigns/chang1002c/nondegenerate_threshold.py --cache /data/chang-n64-20260926/n64/data [--out PATH]

Prints the validation class counts, p_maj, SE and p_maj + 5 SE exactly as
`ablation.run_training` computes them at the start of every run (`ablation.majority_rule`),
so the number is fixed before the canary. Every run re-derives it from the same y_val and
records it in nondegenerate_rule.json; a mismatch there is a data defect. Reads y_val only.
"""
import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))


def main():
    import numpy as np
    from bnhgq2.ablation import majority_rule
    parser = argparse.ArgumentParser()
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    rows = json.loads((HERE / 'index.json').read_text())['runs']
    cfg = json.loads((HERE / 'configs' / rows[0]['file']).read_text())
    info = json.loads((args.cache / 'data_info.json').read_text())
    for key, value in (('pt_gate_gev', cfg['arch']['pt_gate_gev']), ('validation_split', cfg['train']['validation_split']),
                       ('split_seed', cfg['train']['split_seed'])):
        if info.get(key) != value:
            raise SystemExit(f'cache {key} = {info.get(key)!r}, config {value!r}')
    y_val = np.load(args.cache / 'y_val.npy', mmap_mode='r', allow_pickle=False)
    rule = majority_rule(y_val, cfg['experiment']['nondegenerate']['se_multiple'])
    rule.update(cache=str(args.cache), split='validation (gated 90/10)')
    print('NONDEGENERATE_THRESHOLD', json.dumps(rule), flush=True)
    if args.out:
        args.out.write_text(json.dumps(rule, indent=2) + '\n')


if __name__ == '__main__':
    main()
