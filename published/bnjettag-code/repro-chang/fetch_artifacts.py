#!/usr/bin/env python3
"""Fetch repro-chang Pareto checkpoint artifacts from W&B into <out>/<model>-n<N>/.

Artifacts are named kai-repro-chang-<model>-n<N>-pareto (type=model), entity
kayamaguchi-uc-san-diego, project bnjettag-bitnet (uploaded by the EXIT trap in the
job YAMLs). Latest version wins.
"""

import argparse
from pathlib import Path

import wandb

MODELS = ['xfm', 'xfmt']
NS = [8, 16, 32, 64]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('-o', '--output', default='bnjettag/models/repro-chang')
    ap.add_argument('--entity', default='kayamaguchi-uc-san-diego')
    ap.add_argument('--project', default='bnjettag-bitnet')
    args = ap.parse_args()

    api = wandb.Api()
    for model in MODELS:
        for n in NS:
            name = f'kai-repro-chang-{model}-n{n}-pareto'
            dst = Path(args.output) / f'{model}-n{n}'
            try:
                art = api.artifact(f'{args.entity}/{args.project}/{name}:latest')
            except wandb.errors.CommError as e:
                print(f'[miss] {name}: {e}')
                continue
            art.download(root=str(dst))
            n_ckpt = len(list(dst.glob('*.keras')))
            print(f'[ok] {name} v{art.version} -> {dst} ({n_ckpt} checkpoints)')


if __name__ == '__main__':
    main()
