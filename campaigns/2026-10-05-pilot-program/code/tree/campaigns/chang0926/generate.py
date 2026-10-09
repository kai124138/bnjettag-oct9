#!/usr/bin/env python3
"""Generate the 2026-09-26-training-batch configs (Sun et al. recipe at N=64, binary W1).

python campaigns/chang0926/generate.py [--no-floors]

Source: configs/const0922-a07-n64-s1-fast50-fp32.json (screen bundle 26f3cc40). Every arm is
that config plus the fields below; nothing else is edited. Generated files are never
hand-edited; change ARMS / COMMON here and regenerate. Writes only inside this directory.

Arm set [D21] (arbiter v3 fix 2; PENDING the STUDY amendment, STUDY.md at da0e4ee still has
the A07-primary table): the 350k ladder moves to the E architecture (d24, 2 heads, 1 block,
FFN 32). A = E at 350k; B = E at 250k; C = A07 at 5M; D = E with our optimizer; F = E with a
learned PE; R = our recipe on E; A07-350 = A07 at 350k (descriptive). Every no-PE E-family
config draws the PE initializer ([A17] `pos_enc_none_consume_rng`) so A, B, D, R and F share
kernels at each seed. Pilot-only rows (never production, never ROC-test): C-PRIME (A07,
Chang recipe, current SAT/fixed-softmax quantizer, 5M) and E1 (E with 1 head, 350k).

Every config: [D20] full-training-split reset trace (`train.ebops_trace_sample` "train_full")
every 10 epochs (`train.ebops_trace_every` 10, regime B, Kai [D15] decision 2026-09-27; the
77f1ca4e bundle traced every epoch), stored-variable reload check, and the
non-degeneracy condition (arbiter v3 fix 1) with the arm's traced 0-bit floor read from
static_floors.json (static_floor.py on the s1 configs; `--no-floors` writes configs without
the block so the floors can be traced; cpu_gate re-traces and asserts the value).
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parents[1]
SOURCE = TREE / 'configs' / 'const0922-a07-n64-s1-fast50-fp32.json'
SEEDS = range(1, 9)
GROUP = 'chang-n64-20260926'
PROJECT = 'BNJetTag-ChangRecipe'
ORDER_SEED_BASE = 20260926          # [D9] order_seed = ORDER_SEED_BASE * 100 + s

# [D19]/[A20]: the Chang quantizer set in every production arm.
QUANT = {'act_overflow': 'WRAP', 'softmax_quant': 'chang',
         'i_decay_speed': 0.001}     # [D25]: jsc150's 1e-3 (HGQ2 default 0.01)
CURRENT_QUANT = {}                   # C-PRIME: the screen's SAT / fixed-softmax quantizer

CHANG_SCHEDULE = {  # [D2]/[D4]: jsc150 run_train.py:67, 93, 104
    'epochs': 7000, 'batch': 2790, 'lr': 3e-3, 'lr_schedule': 'chang_cosine_restarts',
    'lr_cycle_epochs': 500, 'lr_t_mul': 1.0, 'lr_m_mul': 1.0, 'lr_alpha': 1e-6, 'lr_alpha_epochs': 10,
}
OUR_SCHEDULE = {    # [D4] arm R: the record recipe
    'epochs': 1000, 'batch': 256, 'lr': 2e-5, 'lr_schedule': 'poly',
    'warmup_epochs': 1, 'decay_epochs': 999, 'decay_power': 1.0,
}
CHANG_OPT = {'optimizer': 'adam_default'}                                            # [D3]
OUR_OPT = {'optimizer': 'adam_ours', 'beta2': 0.98, 'weight_decay': 0.01, 'clipvalue': 1.0}
D20 = {'ebops_trace_sample': 'train_full', 'ebops_trace_batch': 2048,               # [D20]
       'ebops_reload_check': 'stored',
       'ebops_trace_every': 10}         # [D20] regime B (Kai, 2026-09-27): trace at epochs 10, 20, ...
SE_MULTIPLE = 5                                                                      # fix 1

A07 = {}
E_ARCH = {'d_model': 24, 'n_heads': 2, 'pos_enc': 'none',                            # [D18]
          'pos_enc_none_consume_rng': True}                                          # [A17]
F_ARCH = {'d_model': 24, 'n_heads': 2, 'pos_enc': 'learned'}                         # E + PE
E1_ARCH = {**E_ARCH, 'n_heads': 1}                                                   # fix 6

# arm: (label, optimizer, schedule, target, arch delta, quant, production, question)
ARMS = {
    'a': ('A', CHANG_OPT, CHANG_SCHEDULE, 350000, E_ARCH, QUANT, True, 'primary: Sun et al. recipe on E at 350k'),
    'b': ('B', CHANG_OPT, CHANG_SCHEDULE, 250000, E_ARCH, QUANT, True, 'budget ladder, lower limit (E at 250k)'),
    'c': ('C', CHANG_OPT, CHANG_SCHEDULE, 5000000, A07, QUANT, True, 'budget ladder, A07 at 5M'),
    'd': ('D', OUR_OPT, CHANG_SCHEDULE, 350000, E_ARCH, QUANT, True, 'optimizer control on E'),
    'f': ('F', CHANG_OPT, CHANG_SCHEDULE, 350000, F_ARCH, QUANT, True, 'E with learned positional encoding'),
    'r': ('R', OUR_OPT, OUR_SCHEDULE, 350000, E_ARCH, QUANT, True, 'recipe package control (our recipe) on E'),
    'a07-350': ('A07-350', CHANG_OPT, CHANG_SCHEDULE, 350000, A07, QUANT, True,
                'descriptive: our A07 at the paper budget; attention data-independent by construction'),
}
PILOT_ONLY = {
    'cprime': ('C-PRIME', CHANG_OPT, CHANG_SCHEDULE, 5000000, A07, CURRENT_QUANT, False,
               'pilot only: A07, Chang recipe, current quantizer, 5M'),
    'e1': ('E1', CHANG_OPT, CHANG_SCHEDULE, 350000, E1_ARCH, QUANT, False,
           'pilot only: E with one head at 350k'),
}
SEED_BLOCK = ('a', 'b', 'c', 'd', 'f', 'a07-350')      # K = 6 per pod, 8 pods (superseded by the regime-B packing below)
# Wave-1 packing, regime B (Kai 2026-09-27: K=5 on the A10 class, about 13 pods; STUDY Pods: R
# packs separately; plan.md DECISION R-B3, provisional until the regime-B pilot's per-process
# GPU memory is read at PREFLIGHT). The 32 E Chang-schedule runs {A, B, D, F} in seed order at
# K=5 (5 x 4,354 MiB per RUN.md fits a 23,028 MiB A10), chunked 5, 5, 5, 5, 4, 4, 4 (7 pods,
# launchable without the K=3 readout); the 16 A07 runs {C, A07-350} in seed pairs at K=4 (4 pods;
# 5 x 5,172 MiB, the C' figure, would not fit an A10), which wait for the K=3 regime-B pilot pod's
# A07-350-s1 epoch-500 readout (STUDY arbiter v8 fix 2 (3)); R s1-4 and s5-8 at K=4 (2 pods).
E_ARMS = ('a', 'b', 'd', 'f')
E_PACK_SIZES = (5, 5, 5, 5, 4, 4, 4)
A07_ARMS = ('c', 'a07-350')
A07_PACK_SIZES = (4, 4, 4, 4)
# Regime-B pilot (Kai 2026-09-27): a K=5 pod (the regime-A pilot minus A07-350-s1, which OOMed at
# K=6 on an A10) and the arbiter v8 K=3 pod (A07-350-s1, C-s1, F-s1).
PILOT_B_K5 = [('a', 1), ('a', 2), ('d', 1), ('cprime', 1), ('e1', 1)]
PILOT_B_K3 = [('a07-350', 1), ('c', 1), ('f', 1)]
# arbiter v3 fix 3: one pod, K = 6, epoch 500, validation only. E1-s1 takes the last slot
# because its traced 0-bit floor leaves 264,237 EBOPs of headroom at 350k (plan.md, fix 6).
PILOT = [('a', 1), ('a', 2), ('d', 1), ('a07-350', 1), ('cprime', 1), ('e1', 1)]
FLOORS = HERE / 'static_floors.json'

TRAIN_DROP = ('warmup_epochs', 'decay_epochs', 'decay_power', 'beta2', 'weight_decay', 'clipvalue')


def name_of(arm, seed):
    return f'chang0926-{arm}-n64-s{seed}'


def build(source, arm, seed, floors=None):
    label, opt, schedule, target, arch, quant, production, question = {**ARMS, **PILOT_ONLY}[arm]
    cfg = copy.deepcopy(source)
    cfg['name'] = name_of(arm, seed)
    cfg['arch'].update(arch)
    cfg['arch']['pt_gate_gev'] = 2.0                                   # [D7]
    cfg['quant'].update(quant)
    tr = cfg['train']
    for key in TRAIN_DROP:                                             # set again below if used
        tr.pop(key, None)
    tr.update(schedule)
    tr.update(opt)
    tr.update(D20)
    tr.update(validation_split=0.1, split_seed=1,                      # [D8], [A18]
              order_seed=ORDER_SEED_BASE * 100 + seed,                 # [D9], [A18]
              wandb_project=PROJECT)                                   # [A18]
    tr['ebops']['pid']['target_ebops'] = target                        # [D5]/[D6]
    cfg['experiment'] = {
        'arm': cfg['name'], 'group': GROUP, 'seed': seed,
        'selection_metric': 'val_categorical_accuracy',
        'cost_before_auc': False,                                      # [A13]
        'keep_auc_selected_feasible': True,                            # [A19]
        'checkpoint_every_epochs': 25,                                 # [A15]/[D14]
        'snapshot_every_epochs': 500,                                  # [A6]
        'remote_every_epochs': 500,                                    # [D14]
    }
    if floors is not None:                                             # arbiter v3 fix 1
        cfg['experiment']['nondegenerate'] = {'zero_floor_ebops': floor_of(floors, arm, cfg),
                                              'se_multiple': SE_MULTIPLE}
    cfg['engram_study'] = {**cfg['engram_study'], 'question': f'chang0926 arm {label}: {question}'}
    cfg.pop('constituent_study')                                       # [A18]
    cfg['campaign'] = {
        'study': 'campaigns/2026-09-26-training-batch', 'arm': label, 'seed': seed,
        'production': production,
        'source_config': SOURCE.name,
        'source_config_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
        'test_set_used_for_selection': False, 'tf32_enabled': False,
    }
    return cfg


def floor_signature(cfg):
    """What the static floor depends on: architecture and quantizer sections."""
    keys = ('arch', 'quant')
    return hashlib.sha256(json.dumps({k: cfg[k] for k in keys}, sort_keys=True).encode()).hexdigest()


def floor_of(floors, arm, cfg):
    entry = floors.get(arm)
    if entry is None:
        raise SystemExit(f'no traced floor for arm {arm}; run generate.py --no-floors, static_floor.py, then again')
    probe = copy.deepcopy(cfg)
    probe.get('experiment', {}).pop('nondegenerate', None)
    if entry['floor_signature'] != floor_signature(probe):
        raise SystemExit(f'static_floors.json is stale for arm {arm} (arch/quant changed); re-trace')
    return int(entry['zero'])


def flatten(value, prefix=''):
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            out.update(flatten(item, f'{prefix}.{key}' if prefix else key))
        return out
    return {prefix: value}


def diff(a, b):
    fa, fb = flatten(a), flatten(b)
    return {'changed': {k: [fa[k], fb[k]] for k in sorted(fa.keys() & fb.keys()) if fa[k] != fb[k]},
            'removed': {k: fa[k] for k in sorted(fa.keys() - fb.keys())},
            'added': {k: fb[k] for k in sorted(fb.keys() - fa.keys())}}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-floors', action='store_true')
    args = parser.parse_args()
    floors = None if args.no_floors else json.loads(FLOORS.read_text())['arms']
    source = json.loads(SOURCE.read_text())
    out = HERE / 'configs'
    out.mkdir(exist_ok=True)
    for old in out.glob('*.json'):
        old.unlink()
    rows = []
    plan = [(arm, seed) for arm in ARMS for seed in SEEDS] + [(arm, 1) for arm in PILOT_ONLY]
    for arm, seed in plan:
        cfg = build(source, arm, seed, floors)
        path = out / (cfg['name'] + '.json')
        path.write_text(json.dumps(cfg, indent=2) + '\n')
        rows.append({'index': len(rows), 'name': cfg['name'], 'arm': cfg['campaign']['arm'], 'seed': seed,
                     'n_part': 64, 'file': path.name, 'production': cfg['campaign']['production'],
                     'target_ebops': cfg['train']['ebops']['pid']['target_ebops'],
                     'zero_floor_ebops': cfg['experiment'].get('nondegenerate', {}).get('zero_floor_ebops'),
                     'arch': {k: cfg['arch'][k] for k in ('d_model', 'n_heads', 'pos_enc')},
                     'quant_set': 'chang' if cfg['quant'].get('act_overflow') == 'WRAP' else 'current',
                     'config_sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    production = [r for r in rows if r['production']]
    assert len(production) == 56 and len({r['name'] for r in rows}) == len(rows) == 58
    assert [r['index'] for r in production] == list(range(56))
    index = {r['name']: r['index'] for r in rows}
    def chunk(runs, sizes):
        assert sum(sizes) == len(runs)
        out = []
        for size in sizes:
            out.append(runs[:size])
            runs = runs[size:]
        return out
    packs = chunk([index[name_of(arm, s)] for s in SEEDS for arm in E_ARMS], E_PACK_SIZES)
    waiting = list(range(len(packs), len(packs) + len(A07_PACK_SIZES)))
    packs += chunk([index[name_of(arm, s)] for s in SEEDS for arm in A07_ARMS], A07_PACK_SIZES)
    packs += [[index[name_of('r', s)] for s in (1, 2, 3, 4)], [index[name_of('r', s)] for s in (5, 6, 7, 8)]]
    assert sorted(i for p in packs for i in p) == list(range(56))
    pilot = [[index[name_of(arm, s)] for arm, s in PILOT]]
    pilot_b_k5 = [[index[name_of(arm, s)] for arm, s in PILOT_B_K5]]
    pilot_b_k3 = [[index[name_of(arm, s)] for arm, s in PILOT_B_K3]]
    (HERE / 'index.json').write_text(json.dumps({'runs': rows, 'count': len(rows),
                                                 'production_count': len(production)}, indent=2) + '\n')
    (HERE / 'packs.json').write_text(json.dumps(packs) + '\n')
    (HERE / 'pilot_packs.json').write_text(json.dumps(pilot) + '\n')
    (HERE / 'canary_packs.json').write_text(json.dumps(pilot) + '\n')   # canary = the pilot pod at --stop-after 2
    (HERE / 'pilot_b_k5_packs.json').write_text(json.dumps(pilot_b_k5) + '\n')
    (HERE / 'pilot_b_k3_packs.json').write_text(json.dumps(pilot_b_k3) + '\n')
    (HERE / 'packs_meta.json').write_text(json.dumps({
        'packs': 'packs.json', 'arms_per_pack': [len(p) for p in packs],
        'wait_for_k3_readout': waiting,
        'rule': 'packs holding A07-350 or C launch only after the K=3 regime-B pilot pod has an '
                'A07-350-s1 epoch-500 readout (STUDY arbiter v8 fix 2 (3)); plan.md DECISION R-B3'}, indent=1) + '\n')
    # [A4] cache spec: gated, 90/10, order seed not pinned (one cache for all seeds)
    spec = build(source, 'a', 1)
    spec['name'] = 'chang0926-cache-n64'
    spec['cache'] = {'order_seed_in_cache': False, 'root_suggestion': '/data/chang-n64-20260926'}
    (HERE / 'cache_configs').mkdir(exist_ok=True)
    (HERE / 'cache_configs' / 'n64.json').write_text(json.dumps(spec, indent=2) + '\n')
    # [A18] every changed field of one generated config against the source
    (HERE / 'config_diff_a_s1.json').write_text(json.dumps(diff(source, build(source, 'a', 1, floors)), indent=2) + '\n')
    print(f'Generated {len(rows)} configs ({len(production)} production), {len(packs)} packs '
          f'(waiting on the K=3 readout: {waiting}), pilot {pilot[0]}, pilot-b K=5 {pilot_b_k5[0]}, K=3 {pilot_b_k3[0]}'
          + (' WITHOUT floors' if floors is None else ''))


if __name__ == '__main__':
    main()
