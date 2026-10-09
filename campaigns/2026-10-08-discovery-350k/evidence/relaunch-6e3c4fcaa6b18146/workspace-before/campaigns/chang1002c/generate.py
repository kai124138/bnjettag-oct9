#!/usr/bin/env python3
"""Generate the option-(c) revision of the 58 chang0926 configs (amendment 2026-10-01).

python campaigns/chang1002c/generate.py

Every config is chang0926/generate.py `build()` for the same (arm, seed), unchanged, then:
  scientific additions   train.ebops.pid_input = "traced_only"
                         train.ebops.pid_traced_integral = "per_epoch"
  identity/provenance    name, experiment.arm (= name), experiment.group, campaign.study,
                         campaign.revision_of, campaign.amendment
Nothing else changes. The script first rebuilds every chang0926 config and requires it to be
byte-identical to the file on disk, so the old/new map compares real historical configs.
Writes only inside this directory: configs/, index.json, packs.json, pilot_c_packs.json,
pilot_c<n>_packs.json, packs_meta.json, config_map.json. Generated files are never hand-edited.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD_DIR = HERE.parent / 'chang0926'
PREFIX = 'chang1002c'
GROUP = 'chang-n64-20261002-c'
STUDY = 'campaigns/2026-10-02-chang-option-c'
AMENDMENT = 'campaigns/2026-10-01-chang-traced-pid/AMENDMENT_DRAFT.md'
PID_KEYS = {'pid_input': 'traced_only', 'pid_traced_integral': 'per_epoch'}
SCIENTIFIC_ADDED = {'train.ebops.pid_input', 'train.ebops.pid_traced_integral'}
PROVENANCE = {'name', 'experiment.arm', 'experiment.group', 'campaign.study',
              'campaign.revision_of', 'campaign.amendment'}
# Replacement pilot, packed for the current GPU policy (peak GPU memory <= 90 % of the card):
# the historical K=5 pod peaked at 22,540 / 23,028 MiB (97.9 %) on an A10, so the eight
# registered pilot arms are split into three pods by measured per-process memory class.
PILOT_C = [[('a', 1), ('a', 2), ('d', 1), ('e1', 1)],      # E class, 4 x ~4,350 MiB
           [('a07-350', 1), ('c', 1)],                     # A07 WRAP, 2 x ~8,446 MiB
           [('f', 1), ('cprime', 1)]]                      # E + PE ~4,350, C' ~5,110 MiB


def load_old_generator():
    spec = importlib.util.spec_from_file_location('chang0926_generate', OLD_DIR / 'generate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(cfg):
    return (json.dumps(cfg, indent=2) + '\n').encode()


def name_of(arm, seed):
    return f'{PREFIX}-{arm}-n64-s{seed}'


def revise(old_cfg, arm, seed):
    cfg = copy.deepcopy(old_cfg)
    eb = cfg['train']['ebops']
    assert not set(PID_KEYS) & set(eb), 'historical config already carries option-(c) keys'
    eb.update(PID_KEYS)
    cfg['name'] = name_of(arm, seed)
    cfg['experiment']['arm'] = cfg['name']
    cfg['experiment']['group'] = GROUP
    cfg['campaign']['study'] = STUDY
    cfg['campaign']['revision_of'] = old_cfg['name']
    cfg['campaign']['amendment'] = AMENDMENT
    return cfg


def build_all():
    gen = load_old_generator()
    floors = json.loads((OLD_DIR / 'static_floors.json').read_text())['arms']
    assert json.loads((HERE / 'static_floors.json').read_text())['arms'] == floors
    source = json.loads(gen.SOURCE.read_text())
    old_index = json.loads((OLD_DIR / 'index.json').read_text())['runs']
    plan = [(arm, seed) for arm in gen.ARMS for seed in gen.SEEDS] + [(arm, 1) for arm in gen.PILOT_ONLY]
    assert len(plan) == len(old_index) == 58
    out = []
    for position, ((arm, seed), old_row) in enumerate(zip(plan, old_index)):
        old_cfg = gen.build(source, arm, seed, floors)
        old_bytes = encode(old_cfg)
        assert old_cfg['name'] == old_row['name'] and old_row['index'] == position
        assert old_bytes == (OLD_DIR / 'configs' / old_row['file']).read_bytes(), old_row['file']
        assert sha(old_bytes) == old_row['config_sha256'], old_row['file']
        new_cfg = revise(old_cfg, arm, seed)
        delta = gen.diff(old_cfg, new_cfg)
        changed = set(delta['changed']) | set(delta['added']) | set(delta['removed'])
        assert not delta['removed'] and changed <= SCIENTIFIC_ADDED | PROVENANCE, changed
        assert SCIENTIFIC_ADDED <= set(delta['added']), delta
        out.append((arm, seed, old_row, old_cfg, new_cfg, delta))
    return gen, out


def main():
    gen, rows = build_all()
    configs = HERE / 'configs'
    configs.mkdir(exist_ok=True)
    for old in configs.glob('*.json'):
        old.unlink()
    index, mapping = [], []
    for arm, seed, old_row, old_cfg, new_cfg, delta in rows:
        path = configs / (new_cfg['name'] + '.json')
        data = encode(new_cfg)
        path.write_bytes(data)
        row = {**old_row, 'name': new_cfg['name'], 'file': path.name, 'config_sha256': sha(data)}
        index.append(row)
        mapping.append({'index': old_row['index'], 'arm': old_row['arm'], 'seed': seed,
                        'production': old_row['production'],
                        'old': {'name': old_row['name'], 'file': 'campaigns/chang0926/configs/' + old_row['file'],
                                'sha256': old_row['config_sha256']},
                        'new': {'name': new_cfg['name'], 'file': 'campaigns/chang1002c/configs/' + path.name,
                                'sha256': row['config_sha256']},
                        'scientific_additions': {k: delta['added'][k] for k in sorted(SCIENTIFIC_ADDED)},
                        'provenance_changes': {k: v for k, v in {**delta['changed'], **delta['added']}.items()
                                               if k in PROVENANCE},
                        'exhaustive_flat_diff': delta})
    production = [r for r in index if r['production']]
    assert len(production) == 56 and len(index) == 58 and [r['index'] for r in production] == list(range(56))
    (HERE / 'index.json').write_text(json.dumps({'runs': index, 'count': len(index),
                                                 'production_count': len(production)}, indent=2) + '\n')
    # Production packs keep the historical indices (production packing is re-decided at its own
    # preflight under the GPU policy); the pilot packs are new.
    (HERE / 'packs.json').write_bytes((HERE.parent / 'chang0926' / 'packs.json').read_bytes())
    by_name = {r['name']: r['index'] for r in index}
    pilot = [[by_name[name_of(arm, seed)] for arm, seed in pod] for pod in PILOT_C]
    assert sorted(i for p in pilot for i in p) == sorted(
        by_name[name_of(a, s)] for a, s in gen.PILOT_B_K5 + gen.PILOT_B_K3)
    (HERE / 'pilot_c_packs.json').write_text(json.dumps(pilot) + '\n')
    for number, pod in enumerate(pilot, 1):   # one single-pack file per pilot Job (index 0)
        (HERE / f'pilot_c{number}_packs.json').write_text(json.dumps([pod]) + '\n')
    (HERE / 'packs_meta.json').write_text(json.dumps({
        'pilot_c': 'pilot_c_packs.json', 'arms_per_pod': [len(p) for p in pilot],
        'pilot_c_runs': [[name_of(a, s) for a, s in pod] for pod in PILOT_C],
        'rule': 'same eight registered pilot arms as pilot-b (K5 + K3); repacked so each A10 pod stays under '
                '90 % GPU memory by measured per-process peaks (training-batch RUN.md, GPU memory per process)',
        'packs': 'packs.json is the historical production packing, carried for index compatibility only'},
        indent=1) + '\n')
    (HERE / 'config_map.json').write_text(json.dumps({
        'schema': 1, 'count': len(mapping), 'production_count': len(production),
        'scientific_additions': PID_KEYS, 'provenance_keys': sorted(PROVENANCE),
        'unchanged': 'every other flattened key of every config (exhaustive_flat_diff per row)',
        'rows': mapping}, indent=1) + '\n')
    print(f'Generated {len(index)} option-(c) configs ({len(production)} production); pilot-c pods {pilot}')


if __name__ == '__main__':
    main()
