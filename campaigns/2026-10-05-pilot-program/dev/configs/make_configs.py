#!/usr/bin/env python3
"""Exploration configs for the dev patches (not pilot configs; those are patch 0035's job).

Each is chang1002c-a-n64-s<seed> (option-(c) arm A) with exactly one scientific change:
  nb      quant.weight "kbi_learnable"                                   (patch 0036, [D22])
  h3qkv1  quant.attn_bit_floor {"bits": 1, "sites": ["q", "k", "v"]}     (patch 0037, H3)
  h3qkv2  quant.attn_bit_floor {"bits": 2, "sites": ["q", "k", "v"]}
  h3all1  quant.attn_bit_floor {"bits": 1, "sites": ["q", "k", "v", "softmax_out"]}
plus name/arm identity. Run from anywhere: python make_configs.py
"""
import copy
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / 'tree' / 'campaigns' / 'chang1002c' / 'configs'
VARIANTS = {
    'nb': {'quant.weight': 'kbi_learnable'},
    'h3qkv1': {'quant.attn_bit_floor': {'bits': 1, 'sites': ['q', 'k', 'v']}},
    'h3qkv2': {'quant.attn_bit_floor': {'bits': 2, 'sites': ['q', 'k', 'v']}},
    'h3all1': {'quant.attn_bit_floor': {'bits': 1, 'sites': ['q', 'k', 'v', 'softmax_out']}},
}


def make(variant, seed=1):
    base = json.loads((SRC / f'chang1002c-a-n64-s{seed}.json').read_text())
    cfg = copy.deepcopy(base)
    for dotted, value in VARIANTS[variant].items():
        block, key = dotted.split('.')
        cfg[block][key] = copy.deepcopy(value)
    name = f'dev1005-{variant}-n64-s{seed}'
    cfg['name'] = name
    cfg['experiment']['arm'] = name
    cfg['experiment']['group'] = 'dev-20261005-local'
    cfg['campaign'] = dict(cfg['campaign'], study='campaigns/2026-10-05-pilot-program/dev',
                           arm=variant.upper(), production=False, revision_of=base['name'])
    return cfg


if __name__ == '__main__':
    for v in VARIANTS:
        (HERE / f'dev1005-{v}-n64-s1.json').write_text(json.dumps(make(v), indent=2) + '\n')
        print('wrote', f'dev1005-{v}-n64-s1.json')
