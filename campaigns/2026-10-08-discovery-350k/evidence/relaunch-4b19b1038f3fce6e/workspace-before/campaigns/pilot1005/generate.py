#!/usr/bin/env python3
"""Generate the pilot-program round-1 configs (campaigns/2026-10-05-pilot-program, docs/PILOT_PROGRAM.md).

python campaigns/pilot1005/generate.py

Every arm starts from an existing, byte-checked config and changes only what its hypothesis names:
  base (option c)      chang1002c `revise(chang0926.build(arm, seed))`, which must equal the
                       chang1002c config on disk byte for byte
  base (no option c)   chang0926 `build(arm, seed)`, which must equal the chang0926 config on disk
                       (the historical in-training PID input: pid_input / pid_traced_integral absent)
  scientific changes   train.ebops.pid.target_ebops (H2 ladder), train.ebops.pid.warmup (H4),
                       quant.weight "kbi_learnable" (H5, NB; patch 0036) or quant.attn_bit_floor
                       {"bits": 1, "sites": ["q", "k", "v"]} (H3; patch 0037), each with its own
                       traced 0-bit floor in experiment.nondegenerate.zero_floor_ebops
  identity/provenance  name, experiment.arm (= name), experiment.group, campaign.study,
                       campaign.revision_of, campaign.pilot (round, arm id of STUDY.md §4 /
                       PROGRAM.json, hypothesis, arch, budget, option_c, warmup)
Every other flattened key equals the base config (asserted per arm, recorded in config_map.json).
The 0-bit floor is unchanged because arch/quant are unchanged (floor signature asserted).
All arms: Chang recipe, regime B (trace every 10), epochs 7000 in the config, run with
`run_pack.py <pack> 500` (epoch-500 pause). Writes only inside this directory: configs/, packs/,
index.json, r1_packs.json, config_map.json. Generated files are never hand-edited.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD_DIR = HERE.parent / 'chang0926'
C_DIR = HERE.parent / 'chang1002c'
PREFIX = 'pilot1005'
GROUP = 'chang-n64-20261005'            # W&B group = GROUP + '-pilot-r1' under BNJ_STAGE=pilot-r1
STUDY = 'campaigns/2026-10-05-pilot-program'
ROUND = 'R1'
TRACE_EVERY = 10
HEADROOM_FLAG = 0.05                     # flag a rung whose 0-bit headroom is under 5 % of its target
ARCH_BASE = {'E': 'a', 'A07': 'a07-350'}  # chang0926 arms: A = E arch at 350k; A07-350 = A07 at 350k
SCIENTIFIC = {'train.ebops.pid.target_ebops', 'train.ebops.pid.warmup', 'quant.weight', 'quant.attn_bit_floor.bits',
              'quant.attn_bit_floor.sites', 'experiment.nondegenerate.zero_floor_ebops'}
# Variants added to R1 by the orchestrator's scope change (2026-10-05): NB (H5) and the H3 attention
# floor, both E at 350k with option (c), warmup 1, seeds 1 and 2. Their 0-bit floors are the structural
# traces in dev/evidence/static_floor_a_nb.json (NB zero 171,526) and static_floor_a_h3.json (q,k,v at
# 1 bit: zero 269,830); cpu_gate.py re-traces both and must reproduce them.
VARIANTS = {
    'nb': {'hyp': 'H5', 'arm': 'NB350-C', 'quant': {'weight': 'kbi_learnable'}, 'zero_floor': 171_526},
    'qkv1': {'hyp': 'H3', 'arm': 'A350-C-qkv1', 'quant': {'attn_bit_floor': {'bits': 1, 'sites': ['q', 'k', 'v']}},
              'zero_floor': 269_830},
    # [A3] (STUDY_arbiter_v1 F2 ii): E positive control with no binding budget. Expressed as config alone:
    # PID target_ebops UNC_TARGET, above E's initial EBOPs (about 9.4M at s1, synthetic init, dev/README.md),
    # so the controller drives beta to its min_beta (1e-10) and the budget never binds. Arch and quant are
    # unchanged, so its floor is E's (171,526).
    'unc': {'hyp': 'control', 'arm': 'E-unc-C', 'quant': {}, 'zero_floor': None},
}
UNC_TARGET = 100_000_000
PROVENANCE = {'name', 'experiment.arm', 'experiment.group', 'campaign.study', 'campaign.revision_of',
              'campaign.production'}      # [A3] F2 iv: pilot configs carry campaign.production false


def k(target):
    return f'{target // 1000}k' if target < 1_000_000 else f'{target // 1_000_000}m'


# (hypothesis, arch, target, option_c, warmup, seed[, variant]). The E 350k option-(c) seed-1 arm is both the
# H1 with-(c) arm and the H2-E ladder's 350k rung; it is listed once (under H1).
R1 = ([('H1', 'E', 350_000, True, 1, s) for s in (1, 2)]
      + [('H1', 'E', 350_000, False, 1, s) for s in (1, 2)]
      + [('H2', 'E', t, True, 1, 1) for t in (250_000, 500_000, 750_000, 1_000_000, 2_000_000, 5_000_000)]
      + [('H2', 'A07', t, True, 1, 1) for t in (500_000, 1_000_000, 2_000_000, 5_000_000)]   # [A3] no A07 350k
      + [('H4', 'E', 350_000, True, w, s) for w in (50, 100) for s in (1, 2)]   # [A3] D3: Kai chose w100 (2026-10-05)
      + [(VARIANTS[v]['hyp'], 'E', 350_000, True, 1, s, v) for v in ('nb', 'qkv1') for s in (1, 2)]
      + [('H3', 'E', 450_000, True, 1, 1, 'qkv1'),          # [A3] matched-headroom H3 arm, A350-C-qkv1-450k
         ('control', 'E', UNC_TARGET, True, 1, 1, 'unc')])  # [A3] E-unc-C positive control
N_ARMS = 24


def program_arm(hyp, arch, target, option_c, warmup, seed, variant=None):
    """The arm id of STUDY.md §4 / PROGRAM.json (A350-noC, A350-C, A350-C-w50, E500k-C, A07-1000k-C, ...);
    NB350-C and A350-C-qkv1 for the two added variants (STUDY.md §4 rows 7-8)."""
    if variant is not None:
        arm = VARIANTS[variant]['arm']
        return arm if target == 350_000 or variant == 'unc' else f'{arm}-{k(target)}'
    if arch == 'E' and target == 350_000:
        return f"A350-{'C' if option_c else 'noC'}" + (f'-w{warmup}' if warmup != 1 else '')
    assert option_c and warmup == 1
    return f"{arch}{'-' if arch == 'A07' else ''}{target // 1000}k-C"


def name_of(hyp, arch, target, option_c, warmup, seed, variant=None):
    if variant == 'unc':
        return f'{PREFIX}-ctl-{arch.lower()}-unc-c-s{seed}'
    tag = f"{hyp.lower()}-{arch.lower()}-{k(target)}-{'c' if option_c else 'noc'}"
    if warmup != 1:
        tag += f'-w{warmup}'
    if variant is not None:
        tag += f'-{variant}'
    return f'{PREFIX}-{tag}-s{seed}'


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(cfg):
    return (json.dumps(cfg, indent=2) + '\n').encode()


def warmup_ok(warmup):
    """Option (c) needs zero-based epoch warmup - 1 traced (ablation.pid_traced_only): epoch 0 or
    (e + 1) % TRACE_EVERY == 0. cpu_gate.py re-checks this with the runner's own function."""
    e = warmup - 1
    return warmup >= 1 and (e == 0 or (e + 1) % TRACE_EVERY == 0)


def base_config(gen, cgen, source, floors, arch, option_c, seed):
    arm = ARCH_BASE[arch]
    old = gen.build(source, arm, seed, floors)
    old_bytes = encode(old)
    assert old_bytes == (OLD_DIR / 'configs' / f'{old["name"]}.json').read_bytes(), old['name']
    if not option_c:
        return old
    new = cgen.revise(old, arm, seed)
    assert encode(new) == (C_DIR / 'configs' / f'{new["name"]}.json').read_bytes(), new['name']
    return new


def build_all():
    gen = load(OLD_DIR / 'generate.py', 'chang0926_generate')
    cgen = load(C_DIR / 'generate.py', 'chang1002c_generate')
    floors = json.loads((OLD_DIR / 'static_floors.json').read_text())['arms']
    for other in (C_DIR, HERE):
        assert json.loads((other / 'static_floors.json').read_text())['arms'] == floors, other
    source = json.loads(gen.SOURCE.read_text())
    names = [name_of(*a) for a in R1]
    assert len(R1) == N_ARMS and len(set(names)) == N_ARMS, names
    out = []
    for arm, name in zip(R1, names):
        hyp, arch, target, option_c, warmup, seed = arm[:6]
        variant = arm[6] if len(arm) > 6 else None
        base = base_config(gen, cgen, source, floors, arch, option_c, seed)
        cfg = copy.deepcopy(base)
        pid = cfg['train']['ebops']['pid']
        assert pid['warmup'] == 1 and (('pid_input' in cfg['train']['ebops']) == option_c)
        pid['target_ebops'] = target
        if option_c:
            assert warmup_ok(warmup), (name, warmup)
        else:
            assert warmup == 1, name      # H4 is defined with option (c) only
        pid['warmup'] = warmup
        cfg['name'] = name
        cfg['experiment']['arm'] = name
        cfg['experiment']['group'] = GROUP
        cfg['campaign']['study'] = STUDY
        cfg['campaign']['revision_of'] = base['name']
        cfg['campaign']['production'] = False
        if variant is not None and VARIANTS[variant]['quant']:
            assert option_c and warmup == 1 and arch == 'E'
            for key, value in VARIANTS[variant]['quant'].items():
                assert key not in cfg['quant'] or key == 'weight', (name, key)
                cfg['quant'][key] = copy.deepcopy(value)
            cfg['experiment']['nondegenerate']['zero_floor_ebops'] = VARIANTS[variant]['zero_floor']
        cfg['campaign']['pilot'] = {'round': ROUND, 'arm': program_arm(*arm),
                                    'hypothesis': hyp, 'arch': arch, 'budget': target,
                                    'option_c': option_c, 'warmup': warmup, 'variant': variant}
        delta = gen.diff(base, cfg)
        changed = set(delta['changed']) | set(delta['added'])
        allowed = SCIENTIFIC | PROVENANCE | {f'campaign.pilot.{x}' for x in cfg['campaign']['pilot']}
        assert not delta['removed'] and changed <= allowed, (name, changed - allowed)
        assert ('train.ebops.pid.target_ebops' in changed) == (target != base['train']['ebops']['pid']['target_ebops'])
        assert ('train.ebops.pid.warmup' in changed) == (warmup != 1)
        assert (changed & {'quant.weight', 'quant.attn_bit_floor.bits', 'quant.attn_bit_floor.sites'} != set()) \
            == (variant is not None and bool(VARIANTS[variant]['quant'])), name
        # floor: arch/quant unchanged -> same signature, same 0-bit floor; a variant carries its own
        # traced floor (re-traced by cpu_gate.py)
        probe = copy.deepcopy(cfg)
        probe['experiment'].pop('nondegenerate', None)
        entry = floors[ARCH_BASE[arch]]
        floor = cfg['experiment']['nondegenerate']['zero_floor_ebops']
        if variant is None or not VARIANTS[variant]['quant']:
            assert gen.floor_signature(probe) == entry['floor_signature'], name
            assert floor == entry['zero'], name
        else:
            assert gen.floor_signature(probe) != entry['floor_signature'], name
            assert floor == VARIANTS[variant]['zero_floor'], name
        headroom = target - floor
        if headroom <= 0:
            raise SystemExit(f'{name}: target {target} at or below the 0-bit floor {floor}; not generated')
        out.append({'hyp': hyp, 'arch': arch, 'target': target, 'option_c': option_c, 'warmup': warmup, 'variant': variant,
                    'seed': seed, 'base': base, 'cfg': cfg, 'delta': delta, 'floor': floor, 'headroom': headroom,
                    'flag': headroom < HEADROOM_FLAG * target})
    return out


def main():
    rows = build_all()
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
        index.append({'index': i, 'name': cfg['name'], 'arm': cfg['campaign']['arm'], 'seed': r['seed'],
                      'n_part': 64, 'file': path.name, 'production': False,
                      'target_ebops': r['target'], 'zero_floor_ebops': r['floor'], 'headroom_zero': r['headroom'],
                      'headroom_flag': r['flag'],
                      'arch': {key: cfg['arch'][key] for key in ('d_model', 'n_heads', 'pos_enc')},
                      'quant_set': 'chang' if cfg['quant'].get('act_overflow') == 'WRAP' else 'current',
                      'round': ROUND, 'program_arm': cfg['campaign']['pilot']['arm'], 'hypothesis': r['hyp'], 'arch_name': r['arch'], 'budget': r['target'],
                      'option_c': r['option_c'], 'warmup': r['warmup'], 'variant': r['variant'],
                      'pack': f"packs/{cfg['name']}.json", 'config_sha256': sha(data)})
        mapping.append({'index': i, 'name': cfg['name'],
                        'base': {'name': r['base']['name'], 'sha256': sha(encode(r['base'])),
                                 'file': ('campaigns/chang1002c/configs/' if r['option_c'] else
                                          'campaigns/chang0926/configs/') + r['base']['name'] + '.json'},
                        'sha256': sha(data), 'exhaustive_flat_diff': r['delta']})
        if r['flag']:
            print(f"FLAG_LOW_HEADROOM {cfg['name']} target {r['target']} floor {r['floor']} headroom {r['headroom']}")
    (HERE / 'index.json').write_text(json.dumps({'runs': index, 'count': len(index), 'production_count': 0,
                                                 'round': ROUND}, indent=2) + '\n')
    (HERE / 'r1_packs.json').write_text(json.dumps([[r['index']] for r in index]) + '\n')
    (HERE / 'config_map.json').write_text(json.dumps({
        'schema': 1, 'round': ROUND, 'count': len(mapping), 'scientific_keys': sorted(SCIENTIFIC),
        'provenance_keys': sorted(PROVENANCE) + ['campaign.pilot'],
        'unchanged': 'every other flattened key equals the base config (exhaustive_flat_diff per row)',
        'rows': mapping}, indent=1) + '\n')
    print(f'Generated {len(index)} pilot R1 configs: ' + ', '.join(r['name'] for r in index))


if __name__ == '__main__':
    main()
