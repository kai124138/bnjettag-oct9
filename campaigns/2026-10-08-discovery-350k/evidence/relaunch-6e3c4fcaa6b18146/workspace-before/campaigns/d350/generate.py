#!/usr/bin/env python3
"""Generate the discovery-350k configs (campaigns/2026-10-08-discovery-350k, PROPOSAL.md §3).

python campaigns/d350/generate.py

Both configs start from the pilot's `pilot1005-h1-e-350k-c-s1`, rebuilt by the pilot generator
(campaigns/pilot1005/generate.py `build_all`) and required to equal the pilot file on disk byte for
byte. Only these keys change:
  scientific   train.ebops.pid.target_ebops: unchanged (350,000) for the baseline,
               5,000,000 for the reference (and campaign.pilot.budget, which cpu_gate.py requires
               to equal the target)
  identity     name, experiment.arm (= name), experiment.group, campaign.study, campaign.revision_of,
               campaign.pilot.round / arm / hypothesis
Every other flattened key equals the pilot config (exhaustive diff asserted, recorded in
config_map.json). The training length is not a config key: `train.epochs` stays 7000 as in the pilot
and the Job stops the run with `run_pack.py <pack> <stop epoch>` (the pilot's mechanism, there 500,
here 1000), so the config hash does not depend on the stop epoch and a run can resume to a later one.
The reference is also checked against the pilot's own E-5M config (pilot1005-h2-e-5m-c-s1): the two
may differ only in identity keys.

Writes only inside this directory: configs/, packs/, index.json, config_map.json. Generated files are
never hand-edited.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent / 'pilot1005'
BASE_NAME = 'pilot1005-h1-e-350k-c-s1'
PILOT_5M = 'pilot1005-h2-e-5m-c-s1'
PREFIX = 'd350'
GROUP = 'discovery-350k-20261008'
STUDY = 'campaigns/2026-10-08-discovery-350k'
ROUND = 'D350'
# (arm, hypothesis, target): the arm name is the config name without the 'd350-' prefix
ARMS = [('baseline-e-350k-s1', 'baseline', 350_000),
        ('reference-e-5m-s1', 'reference', 5_000_000)]
SCIENTIFIC = {'train.ebops.pid.target_ebops', 'campaign.pilot.budget'}
IDENTITY = {'name', 'experiment.arm', 'experiment.group', 'campaign.study', 'campaign.revision_of',
            'campaign.pilot.round', 'campaign.pilot.arm', 'campaign.pilot.hypothesis'}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(cfg):
    return (json.dumps(cfg, indent=2) + '\n').encode()


def pilot_configs():
    """The pilot generator's own output for the base and the E-5M rung, each equal to its file."""
    gen = load(PILOT / 'generate.py', 'pilot1005_generate')
    built = {r['cfg']['name']: r for r in gen.build_all()}   # asserts its own bases against chang0926/chang1002c
    out = {}
    for name in (BASE_NAME, PILOT_5M):
        data = encode(built[name]['cfg'])
        assert data == (PILOT / 'configs' / f'{name}.json').read_bytes(), name
        out[name] = built[name]
    return gen, out


def build_all():
    _, pilot = pilot_configs()
    diff = load(PILOT.parent / 'chang0926' / 'generate.py', 'chang0926_generate').diff   # the pilot's diff
    base = pilot[BASE_NAME]['cfg']
    row0 = next(r for r in json.loads((PILOT / 'index.json').read_text())['runs'] if r['name'] == BASE_NAME)
    rows = []
    for arm, hyp, target in ARMS:
        cfg = copy.deepcopy(base)
        name = f'{PREFIX}-{arm}'
        cfg['name'] = name
        cfg['experiment']['arm'] = name
        cfg['experiment']['group'] = GROUP
        cfg['campaign']['study'] = STUDY
        cfg['campaign']['revision_of'] = BASE_NAME
        cfg['campaign']['pilot'].update(round=ROUND, arm=arm, hypothesis=hyp, budget=target)
        cfg['train']['ebops']['pid']['target_ebops'] = target
        delta = diff(base, cfg)
        changed = set(delta['changed']) | set(delta['added'])
        assert not delta['removed'] and not delta['added'] and changed <= SCIENTIFIC | IDENTITY, (name, changed)
        assert ('train.ebops.pid.target_ebops' in changed) == (target != 350_000), name
        assert cfg['train']['epochs'] == 7000 and cfg['experiment']['snapshot_every_epochs'] == 500
        assert cfg['experiment']['checkpoint_every_epochs'] == 25 and cfg['train']['ebops_trace_every'] == 10
        floor = cfg['experiment']['nondegenerate']['zero_floor_ebops']
        assert floor == row0['zero_floor_ebops'] == 171_526 and target - floor > 0
        if target == 5_000_000:
            other = diff(pilot[PILOT_5M]['cfg'], cfg)
            extra = set(other['changed']) | set(other['added']) | set(other['removed'])
            assert extra <= IDENTITY, (name, 'differs from pilot E-5M beyond identity', extra - IDENTITY)
        rows.append({'arm': arm, 'hyp': hyp, 'target': target, 'cfg': cfg, 'delta': delta, 'floor': floor})
    return base, row0, rows


def main():
    base, row0, rows = build_all()
    configs, packs = HERE / 'configs', HERE / 'packs'
    for d in (configs, packs):
        d.mkdir(exist_ok=True)
        for old in d.glob('*.json'):
            old.unlink()
    index, mapping = [], []
    for i, r in enumerate(rows):
        cfg = r['cfg']
        data = encode(cfg)
        path = configs / f"{cfg['name']}.json"
        path.write_bytes(data)
        (packs / f"{cfg['name']}.json").write_text(json.dumps([[i]]) + '\n')
        index.append({'index': i, 'name': cfg['name'], 'arm': cfg['campaign']['arm'], 'seed': cfg['experiment']['seed'],
                      'n_part': 64, 'file': path.name, 'production': False,
                      'target_ebops': r['target'], 'zero_floor_ebops': r['floor'], 'headroom_zero': r['target'] - r['floor'],
                      'headroom_flag': False, 'arch': {k: cfg['arch'][k] for k in ('d_model', 'n_heads', 'pos_enc')},
                      'quant_set': row0['quant_set'], 'round': ROUND, 'program_arm': r['arm'], 'hypothesis': r['hyp'],
                      'arch_name': 'E', 'budget': r['target'], 'option_c': True, 'warmup': 1, 'variant': None,
                      'd350_arm': r['arm'], 'pack': f"packs/{cfg['name']}.json", 'config_sha256': sha(data)})
        mapping.append({'index': i, 'name': cfg['name'],
                        'base': {'name': BASE_NAME, 'sha256': sha(encode(base)),
                                 'file': f'campaigns/pilot1005/configs/{BASE_NAME}.json'},
                        'sha256': sha(data), 'exhaustive_flat_diff': r['delta']})
    (HERE / 'index.json').write_text(json.dumps({'runs': index, 'count': len(index), 'production_count': 0,
                                                 'round': ROUND}, indent=2) + '\n')
    (HERE / 'config_map.json').write_text(json.dumps({
        'schema': 1, 'round': ROUND, 'count': len(mapping), 'scientific_keys': sorted(SCIENTIFIC),
        'identity_keys': sorted(IDENTITY),
        'unchanged': 'every other flattened key equals the base config (exhaustive_flat_diff per row)',
        'stop_epoch': 'not a config key: run_pack.py <pack> <stop epoch> in the Job (pilot mechanism)',
        'rows': mapping}, indent=1) + '\n')
    print(f'Generated {len(index)} d350 configs: ' + ', '.join(f"{r['name']} {r['config_sha256'][:12]}" for r in index))


if __name__ == '__main__':
    main()
