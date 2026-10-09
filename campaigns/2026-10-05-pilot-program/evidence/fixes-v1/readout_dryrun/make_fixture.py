#!/usr/bin/env python3
"""Synthetic fixture for the R1 readout dry run (PREFLIGHT fixes after review v1, A1). Not data.

python make_fixture.py --tree TREE --data DATA_ROOT --runs RUN_ROOT/runs [--only name,...]

Writes, for the 23 R1 rows of TREE/campaigns/pilot1005/index.json:
  DATA_ROOT/n64/data/  a synthetic cache in run_engram.load_cache's format (620,000 rows, random
                       inputs, random one-hot labels, READY.json, data_info.json with array hashes)
  RUN_ROOT/runs/<name>/  config.json, data_info.json, activation_widths.jsonl (500 records),
                       nondegenerate_rule.json, latest.json + checkpoints/epoch-0500/state.json,
                       snapshots/epoch-0500/{state.json, model_best.keras | model_min_ebops.keras,
                       pid_telemetry.jsonl (option-(c) arms)}
Models are the real pilot configs built by run_engram.builder_for (untrained), with activation widths
set by static_floor.set_floor: designated arms get a width setting whose full-train-split EBOPs lie in
(floor, budget] and become the runner's best_feasible at epoch 499; every other arm is at its zero
floor (model_min_ebops). Accuracies and AUCs in the records are placeholders. Telemetry comes from
tests/test_option_c_amendment.simulate (hgq2 BetaPID on a scalar plant). Nothing here is a result.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
import numpy as np

THR = 0.2109624456315518
LABELS = 'e593f51fad6a19e14c1df783ab762ffd5dfd566b6b1df13ba251a41fa1ad7617'
DESIGNATED = ('pilot1005-h2-e-500k-c-s1', 'pilot1005-ctl-e-unc-c-s1')   # the one certified (non-degenerate) arm; others at the zero floor


def traced(epoch):
    return epoch == 0 or (epoch + 1) % 10 == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tree', type=Path, required=True)
    ap.add_argument('--data', type=Path, required=True)
    ap.add_argument('--runs', type=Path, required=True)
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    sys.path[:0] = [str(args.tree), str(args.tree / 'tests')]
    import run_engram
    import static_floor
    from bnhgq2 import ablation
    import test_option_c_amendment as amendment
    import keras
    camp = args.tree / 'campaigns' / 'pilot1005'
    rows = [r for r in json.loads((camp / 'index.json').read_text())['runs'] if r['round'] == 'R1']
    only = {n for n in args.only.split(',') if n}
    cfg0 = json.loads((camp / 'configs' / rows[0]['file']).read_text())
    a = cfg0['arch']
    cache = args.data / 'n64' / 'data'
    if not (cache / 'READY.json').is_file():
        cache.mkdir(parents=True)
        rng = np.random.default_rng(20261005)
        n_val = int(620000 * cfg0['train']['validation_split'])
        arrays = {}
        for split, n in (('train', 620000 - n_val), ('val', n_val)):
            x = rng.standard_normal((n, a['n_part'], a['n_feat']), dtype=np.float32)
            y = np.eye(a['n_classes'], dtype=np.float32)[rng.integers(0, a['n_classes'], n)]
            arrays['x_' + split], arrays['y_' + split] = x, y
        for k, v in arrays.items():
            np.save(cache / f'{k}.npy', v)
        info = {'synthetic': 'readout dry run fixture, not data', 'n_part': a['n_part'], 'features': a['features'],
                'split_seed': cfg0['train']['split_seed'], 'order_seed': None, 'pt_gate_gev': a.get('pt_gate_gev'),
                'validation_split': cfg0['train']['validation_split'], 'input_std': None,
                'array_sha256': {k: ablation.array_hash(v) for k, v in arrays.items()}}
        info['train_sha256'] = info['array_sha256']['x_train']
        info['val_sha256'] = info['array_sha256']['x_val']
        (cache / 'data_info.json').write_text(json.dumps(info, indent=1))
        (cache / 'READY.json').write_text('{"synthetic": true}')
        print('FIXTURE_CACHE', cache, flush=True)
    info_raw = json.loads((cache / 'data_info.json').read_text())
    for row in rows:
        if only and row['name'] not in only:
            continue
        t0 = time.monotonic()
        cfg = json.loads((camp / 'configs' / row['file']).read_text())
        (x_train, _, _, _), info = run_engram.load_cache(cache, cfg)
        run = args.runs / row['name']
        snap = run / 'snapshots' / 'epoch-0500'
        snap.mkdir(parents=True)
        (run / 'config.json').write_text(json.dumps(cfg, indent=1))
        (run / 'data_info.json').write_text(json.dumps(info_raw, indent=1))
        keras.backend.clear_session()
        sample = np.asarray(x_train[:256])
        model, _ = run_engram.builder_for(info)(cfg, sample, int(cfg['train'].get('seed', row['seed'])))
        floor, budget = int(row['zero_floor_ebops']), int(row['budget'])
        batch = ablation.ebops_trace_batch(cfg)
        best, ebops = None, None
        if row['name'] in DESIGNATED:
            for mode in ('attn_narrow', 'one'):
                static_floor.set_floor(model, mode, sample)
                ebops = int(ablation.compute_ebops(model, x_train, batch_size=batch)['total'])
                print('FIXTURE_TRY', row['name'], mode, ebops, 'floor', floor, 'budget', budget, flush=True)
                if floor < ebops <= budget:
                    best = {'epoch': 499, 'ebops': ebops, 'val_categorical_accuracy': 0.6, 'val_macro_auc': 0.8}
                    break
        if best is None:
            static_floor.set_floor(model, 'zero', sample)   # not certified (no best_feasible): sample trace only
            ebops = int(ablation.compute_ebops(model, sample, batch_size=batch)['total'])
        model.save(snap / ('model_best.keras' if best else 'model_min_ebops.keras'))
        # F5 inputs: the epoch-500 checkpoint model and the best-AUC (unconstrained) copy; same synthetic model
        (run / 'checkpoints' / 'epoch-0500').mkdir(parents=True, exist_ok=True)
        model.save(run / 'checkpoints' / 'epoch-0500' / 'model.keras')
        model.save(snap / 'model_unconstrained.keras')
        with (run / 'activation_widths.jsonl').open('w') as f:
            for e in range(500):
                t = traced(e)
                val = (best['ebops'] if (best and e == 499) else budget + 1000 + e) if t else None
                acc = 0.6 if (best and e == 499) else 0.3
                f.write(json.dumps({'epoch': e, 'ebops': val, 'ebops_traced': int(t), 'val_categorical_accuracy': acc,
                                    'val_macro_auc': 0.8 if (best and e == 499) else 0.7,
                                    'val_accuracy_threshold': THR, 'widths': {}, 'per_layer': None}) + '\n')
        state = {'completed_epochs': 500, 'best_feasible': best, 'synthetic': True}
        for p in (snap / 'state.json', run / 'checkpoints' / 'epoch-0500' / 'state.json'):
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(json.dumps(state))
        (run / 'latest.json').write_text(json.dumps({'checkpoint': 'epoch-0500'}))
        (run / 'nondegenerate_rule.json').write_text(json.dumps(
            {'val_accuracy_threshold': THR, 'labels_sha256': LABELS, 'zero_floor_ebops': floor}))
        if row['option_c']:
            telemetry, _ = amendment.simulate(cfg, 500)
            for r in telemetry:
                ablation.append_jsonl(snap / 'pid_telemetry.jsonl', r)
        print('FIXTURE_RUN', row['name'], 'nondegenerate' if best else 'min_ebops', 'ebops', ebops,
              'floor', floor, 'budget', budget, f'{time.monotonic() - t0:.0f}s', flush=True)
        del model


if __name__ == '__main__':
    main()
