#!/usr/bin/env python3
"""Delta wave-2 PREFLIGHT CPU checks on a fresh extraction of the bundle. Synthetic inputs; not a result.

    PYTHONPATH=<extraction>/code pyenv.sh preflight_checks.py <extraction>/code [--anchor-cache <n64.json>]

Checks (STUDY launch gates, 2026-09-27-delta-screen):
  PLACEBO   (Arms, X2/Z13) for P-350 s1-4 vs REP-A s1-4 and P-5M s1-4 vs REP-C s1-4:
            equal digest_json(cfg) after deleting name, experiment.arm, delta_study, engram_study.question
            and setting train.epochs to one value; equal init kernel_hashes; equal first-step CPU loss.
  DIAG_ONOFF (gate 8) REP-A s1 and REP-C s1 with vs without the always-on keys (experiment.collapse_stop,
            experiment.accumulator_metric, experiment.diagnostics if present): equal kernel hashes after init,
            equal loss and EBOPs trace after each of 3 steps, equal kernel hashes after them.
  HORIZON   (gate 5, function level only) learning_rate, training_target and is_traced_epoch equal for every
            epoch 0..H-1 between train.epochs = H and 500 / 1,000 / 2,000 / 7,000.
  CACHE_ID  every packed run's cache_identity equals the anchor n64 cache config identity keys.
"""
import copy
import json
import os
import sys
from pathlib import Path

import numpy as np

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '-1')
CODE = Path(sys.argv[1]).resolve()
CAMP = CODE / 'campaigns' / 'delta0926'
W2 = CAMP / 'configs' / 'W2'
N_SAMPLE, N_TRACE = 512, 32


def load(name):
    return json.loads((W2 / name).read_text())


def synth(n, n_part, n_feat, n_classes, seed):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, n_part, n_feat)).astype('float32')
    y = np.eye(n_classes, dtype='float32')[rng.integers(0, n_classes, n)]
    return x, y


def normalized(cfg, epochs=500):
    c = copy.deepcopy(cfg)
    for k in ('name',):
        c.pop(k, None)
    c['experiment'].pop('arm', None)
    c.pop('delta_study', None)
    c.get('engram_study', {}).pop('question', None)
    c['train']['epochs'] = epochs
    return c


def build_and_step(cfg, steps=1, x_seed=None):
    import keras
    import tensorflow as tf
    import run_engram
    from bnhgq2 import qat as qat_mod
    from bnhgq2.ebops_calc import compute_ebops
    ablation, _ = run_engram.runtime()
    tf.config.experimental.enable_tensor_float_32_execution(False)
    keras.backend.clear_session()
    run_engram.validate_cfg(cfg)
    A = cfg['arch']
    seed = int(cfg['experiment']['seed'])
    batch = int(cfg['train']['batch'])
    x, y = synth(max(N_SAMPLE, batch), A['n_part'], A['n_feat'], A['n_classes'], seed if x_seed is None else x_seed)
    info = {'input_std': {'mu': [0.0] * A['n_feat'], 'sigma': [1.0] * A['n_feat']}}
    model, evidence = run_engram.builder_for(info)(cfg, x[:N_SAMPLE], seed)
    ablation.binary_gate(model, cfg)
    init_hashes = evidence['kernel_hashes']
    opt = ablation.delta_optimizer_for(cfg, model)
    opt.learning_rate.assign(ablation.learning_rate(cfg, 0))
    qat_mod.set_delta_epoch(cfg, 0)
    step = ablation.make_epoch_step(model, opt, x[:batch], y[:batch], cfg, input_std=info['input_std'])
    losses, ebops = [], [compute_ebops(model, x[:N_TRACE])['total']]
    for _ in range(steps):
        totals = step(np.arange(batch, dtype='int32'), False).numpy()
        losses.append([float(v) for v in totals])
        ebops.append(compute_ebops(model, x[:N_TRACE])['total'])
    after = {v.path: ablation.array_hash(v.numpy()) for v in model.weights if v.name in ('kernel', 'bias', 'pos_table')}
    return {'init_hashes': init_hashes, 'losses': losses, 'ebops': ebops, 'after_hashes': after,
            'params': int(model.count_params())}


def placebo():
    from bnhgq2.ablation import digest_json
    ok_all = True
    for rep, pla, target in (('REP-A', 'P-350', 350000), ('REP-C', 'P-5M', 5000000)):
        for s in (1, 2, 3, 4):
            r, p = load(f'{rep}-t{target}-s{s}.json'), load(f'{pla}-t{target}-s{s}.json')
            d_ok = digest_json(normalized(r)) == digest_json(normalized(p))
            br, bp = build_and_step(r), build_and_step(p)
            k_ok = br['init_hashes'] == bp['init_hashes'] and len(br['init_hashes']) > 0
            l_ok = br['losses'][0] == bp['losses'][0]
            ok = d_ok and k_ok and l_ok
            ok_all &= ok
            print(f"PLACEBO_{'PASS' if ok else 'FAIL'} {pla}-s{s} vs {rep}-s{s} digest_equal {d_ok} "
                  f"init_kernel_hashes_equal {k_ok} (n {len(br['init_hashes'])}) first_step_loss_equal {l_ok} "
                  f"loss {br['losses'][0][0]!r} {bp['losses'][0][0]!r}", flush=True)
    return ok_all


def diag_onoff():
    ok_all = True
    for name in ('REP-A-t350000-s1.json', 'REP-C-t5000000-s1.json'):
        on = load(name)
        off = copy.deepcopy(on)
        removed = [k for k in ('collapse_stop', 'accumulator_metric', 'diagnostics') if off['experiment'].pop(k, None) is not None]
        a, b = build_and_step(on, steps=3), build_and_step(off, steps=3)
        ok = (a['init_hashes'] == b['init_hashes'] and a['losses'] == b['losses'] and a['ebops'] == b['ebops']
              and a['after_hashes'] == b['after_hashes'])
        ok_all &= ok
        print(f"DIAG_ONOFF_{'PASS' if ok else 'FAIL'} {on['name']} removed {removed} steps 3 "
              f"losses_equal {a['losses'] == b['losses']} ebops_equal {a['ebops'] == b['ebops']} "
              f"kernel_hashes_equal_init {a['init_hashes'] == b['init_hashes']} after {a['after_hashes'] == b['after_hashes']}",
              flush=True)
    return ok_all


def horizon():
    import run_engram
    ablation, _ = run_engram.runtime()
    ok_all = True
    for name in ('REP-A-t350000-s1.json', 'REP-A07-350-t350000-s1.json', 'REP-C-t5000000-s1.json'):
        base = load(name)
        for h in (500, 1000, 2000):
            ref = copy.deepcopy(base); ref['train']['epochs'] = h
            for other in (500, 1000, 2000, 7000):
                if other < h:
                    continue
                c = copy.deepcopy(base); c['train']['epochs'] = other
                bad = [e for e in range(h)
                       if ablation.learning_rate(ref, e) != ablation.learning_rate(c, e)
                       or ablation.training_target(ref, e) != ablation.training_target(c, e)
                       or (ablation.is_traced_epoch(ref, e) != ablation.is_traced_epoch(c, e) and e != h - 1)]
                ok_all &= not bad
                traced = sum(ablation.is_traced_epoch(ref, e) for e in range(h))
                print(f"HORIZON_{'OK' if not bad else 'DIFF'} {base['name']} H {h} vs epochs {other} "
                      f"epochs_checked {h} first_diff {bad[:3]} traced_in_H {traced}", flush=True)
    return ok_all


def cache_identity(anchor_cache):
    cache = json.loads(Path(anchor_cache).read_text())
    want = {'arch.n_part': cache['arch'].get('n_part'), 'arch.features': cache['arch'].get('features'),
            'arch.pt_gate_gev': cache['arch'].get('pt_gate_gev'), 'train.validation_split': cache['train'].get('validation_split'),
            'train.split_seed': cache['train'].get('split_seed')}
    rows = {r['name']: r for r in json.loads((CAMP / 'index.json').read_text())['runs']}
    bad, n = [], 0
    for f in ('delta_canary_packs.json', 'delta_w2_t0_packs.json', 'delta_w2_cells_packs.json'):
        p = json.loads((CAMP / f).read_text())
        for i, pack in enumerate(p['packs']):
            for run in pack:
                n += 1
                row = rows[run]
                cfg = json.loads((CAMP / 'configs' / row['file']).read_text())
                got = {'arch.n_part': cfg['arch'].get('n_part'), 'arch.features': cfg['arch'].get('features'),
                       'arch.pt_gate_gev': cfg['arch'].get('pt_gate_gev'),
                       'train.validation_split': cfg['train'].get('validation_split'),
                       'train.split_seed': cfg['train'].get('split_seed')}
                extra = {k: row['cache_identity'].get(k) for k in ('arch.derived_features', 'data.std_scope')}
                if got != want or any(v is not None for v in extra.values()) or p['pack_meta'][i]['data_root'] != '/data/chang-n64-20260926':
                    bad.append((f, run))
    print(f"CACHE_ID_{'OK' if not bad else 'DIFF'} packed_runs {n} anchor_identity {json.dumps(want, sort_keys=True)} "
          f"data_root /data/chang-n64-20260926 mismatches {bad[:5]}", flush=True)
    return not bad


if __name__ == '__main__':
    which = sys.argv[2:] or ['cache', 'horizon', 'placebo', 'diag']
    anchor_cache = CODE / 'campaigns' / 'chang0926' / 'cache_configs' / 'n64.json'
    results = {}
    if 'cache' in which:
        results['cache'] = cache_identity(anchor_cache)
    if 'horizon' in which:
        results['horizon'] = horizon()
    if 'placebo' in which:
        results['placebo'] = placebo()
    if 'diag' in which:
        results['diag'] = diag_onoff()
    print('PREFLIGHT_CHECKS', json.dumps(results, sort_keys=True))
