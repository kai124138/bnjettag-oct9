#!/usr/bin/env python3
"""[A7] traced static floors of every chang0926 arm (seed 1 configs), for generate.py and PREFLIGHT.

python campaigns/chang0926/generate.py --no-floors
python campaigns/chang0926/trace_floors.py            # writes static_floors.json (+ --evidence PATH)
python campaigns/chang0926/generate.py                 # configs now carry experiment.nondegenerate

The floor depends on arch and quant only (static_floor.py docstring), so one trace per arm;
`floor_signature` ties it to those sections and generate.py refuses a stale entry. CPU,
synthetic sample; a structural trace, not a result.
"""
import argparse
import json
import os
from pathlib import Path
import sys

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))


def main():
    import generate
    from static_floor import floors
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, help='full per-layer output (static_floor.py format)')
    args = parser.parse_args()
    arms, full = {}, []
    for arm in list(generate.ARMS) + list(generate.PILOT_ONLY):
        cfg = json.loads((HERE / 'configs' / f'{generate.name_of(arm, 1)}.json').read_text())
        cfg.get('experiment', {}).pop('nondegenerate', None)
        r = floors(cfg)
        full.append(r)
        arms[arm] = {'config': cfg['name'], 'floor_signature': generate.floor_signature(cfg),
                     'target_ebops': r['target_ebops'], 'parameters': r['parameters'],
                     'init_synthetic': r['init']['total'],
                     **{mode: r[mode]['total'] for mode in ('zero', 'one', 'attn_narrow', 'attn_full')},
                     'headroom': r['headroom'], 'status': r['status']}
        print('ARM_FLOOR', arm, 'zero', r['zero']['total'], 'one', r['one']['total'],
              'attn_narrow', r['attn_narrow']['total'], 'attn_full', r['attn_full']['total'],
              'target', r['target_ebops'], 'headroom', r['target_ebops'] - r['zero']['total'], r['status'], flush=True)
    (HERE / 'static_floors.json').write_text(json.dumps(
        {'sample': full[0]['sample'], 'tool': 'static_floor.py', 'arms': arms}, indent=2) + '\n')
    if args.evidence:
        args.evidence.write_text(json.dumps(full, indent=2) + '\n')


if __name__ == '__main__':
    main()
