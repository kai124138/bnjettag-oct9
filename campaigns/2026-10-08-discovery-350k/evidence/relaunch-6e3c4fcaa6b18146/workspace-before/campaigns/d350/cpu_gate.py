#!/usr/bin/env python3
"""CPU build/reload gate for every pilot1005 (pilot program R1) config (synthetic inputs; no cache, no GPU).

python campaigns/pilot1005/cpu_gate.py [--only a,b] [--out gate.json]

Copied from campaigns/chang1002c/cpu_gate.py; pilot changes (2026-10-05, patch 0035):
- the PID check follows each config: with option (c) (`campaign.pilot.option_c`) the traced-only
  schedule for its own warmup W (steps at every e < W, the seed step at e = W with span 1, the
  first feedback step at the next epoch after a trace with span = e - W); without option (c) the
  keys are absent and `ablation.pid_traced_only` returns None (historical in-training input);
- matched initialization: every config with the same architecture and seed must produce the same
  `kernel_hashes` (the arms differ in target, warmup, PID input, NB weights ([A22]) or the H3
  attention floor, none of which may change the initial kernels), printed as PAIRED_INIT_OK per group;
- the 0-bit floor re-trace is keyed by the arch/quant sections, so NB and the H3 floor arm are
  re-traced against their own registered floors.

Per config: run_engram.validate_cfg; the production initializer
(ablation.matching_initialization) on a fixed synthetic sample; binary gate; native EBOPs
trace; optimizer path and LR at the schedule landmarks; ONE training step at the config's
batch size (ablation.make_epoch_step, loss finite); save -> reload -> predictions within the
screen preflight tolerance (atol = rtol = 2e-6) and re-traced EBOPs equal. Prints
CONFIG_PREFLIGHT_PASS <name> params <n> ... per config and PREFLIGHT_ALL_PASS at the end.
Synthetic data: nothing here is a result.

Added for [D20] / arbiter v3 (patch 0022): traces run on the config's
`train.ebops_trace_sample` rows of the synthetic sample (train_full = all 4,096); the EBOPs
BetaPID reads (`ablation.model_ebops`) must equal the traced total; the stored-variable
reload check must equal it too; `i_decay_speed` is read per quantizer; the config's
`experiment.nondegenerate.zero_floor_ebops` is re-traced with static_floor.py once per arm
(seed 1) and must be equal. Pilot-only rows run too and are counted apart.

[D25] (patch 0024): a config with `quant.i_decay_speed` must record that value (at float32) on
every quantizer `ablation.i_decay_speeds` lists, the list must cover every `i_decay_speed`
weight in the model, and the values must survive the training step and the save/reload. A
config without the key (C-PRIME) must record nothing: it has no WRAP quantizer, so no quantizer
carries the knob and the HGQ2 default 0.01 acts on nothing. Printed as I_DECAY_OK per config.

[D20] regime B (patch 0027, Kai 2026-09-27): `train.ebops_trace_every` is validated by
`ablation.ebops_trace_every` (positive int, needs the trace sample and the stored reload check,
snapshot cadence a multiple of k); the epoch count and the snapshot cadence must be multiples of
k, so the traced epochs are exactly epochs / k plus zero-based epoch 0 (STUDY slot T) and include
every snapshot. Printed as
TRACE_EVERY_OK per config (k None = every epoch).
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault('KERAS_BACKEND', 'tensorflow')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', default='')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    import keras
    import tensorflow as tf
    import run_engram
    ablation, _ = run_engram.runtime()
    tf.config.experimental.enable_tensor_float_32_execution(False)
    from static_floor import floors as static_floors
    rows = json.loads((HERE / 'index.json').read_text())['runs']
    only = {a.upper() for a in args.only.split(',') if a}
    floor_checked = {}
    rng = np.random.default_rng(0)
    x = rng.standard_normal((4096, 64, 3)).astype('float32')
    y = np.eye(5, dtype='float32')[rng.integers(0, 5, 4096)]
    reports = []
    for row in rows:
        if only and row['arm'] not in only:
            continue
        keras.backend.clear_session()
        cfg = json.loads((HERE / 'configs' / row['file']).read_text())
        assert cfg['name'] == row['name'] and cfg['experiment']['seed'] == row['seed']
        run_engram.validate_cfg(cfg)
        assert ablation.cost_before_auc(cfg) is False
        pilot = cfg['campaign']['pilot']
        warmup = int(cfg['train']['ebops']['pid']['warmup'])
        assert warmup == pilot['warmup'] and cfg['train']['ebops']['pid']['target_ebops'] == pilot['budget'] == row['budget']
        if pilot['option_c']:
            # option-(c) amendment: explicit traced-only PID, per_epoch, and the registered cadence
            assert ablation.pid_traced_only(cfg) == 'per_epoch', row['name']
            steps = [e for e in range(int(cfg['train']['epochs'])) if ablation.pid_step_epochs(cfg, e)[0]]
            assert steps[:warmup + 1] == list(range(warmup + 1)), (row['name'], steps[:warmup + 2])
            assert ablation.pid_step_epochs(cfg, warmup) == (True, 1), row['name']
            first = steps[warmup + 1]
            assert ablation.is_traced_epoch(cfg, first - 1) and ablation.pid_step_epochs(cfg, first) == (True, first - warmup)
            assert all(not ablation.is_traced_epoch(cfg, e - 1) for e in range(warmup + 1, first)), row['name']
            if warmup == 1:
                assert steps[:3] == [0, 1, 10] and ablation.pid_step_epochs(cfg, 10) == (True, 9), (row['name'], steps[:3])
            print('PID_TRACED_ONLY_OK', row['name'], 'warmup', warmup, 'first_feedback', first,
                  'span', first - warmup, 'steps', len(steps), flush=True)
        else:
            assert ablation.pid_traced_only(cfg) is None, row['name']
            assert 'pid_input' not in cfg['train']['ebops'] and 'pid_traced_integral' not in cfg['train']['ebops']
            assert warmup == 1, row['name']
            print('PID_HISTORICAL_INPUT_OK', row['name'], 'warmup', warmup, flush=True)
        model, evidence = ablation.matching_initialization(cfg, x, cfg['experiment']['seed'])
        ablation.binary_gate(model, cfg)
        sample = ablation.ebops_trace_sample(cfg, x)
        cost = ablation.compute_ebops(model, sample, batch_size=ablation.ebops_trace_batch(cfg))
        assert ablation.model_ebops(model) == cost['total'], ('PID-read EBOPs differ', ablation.model_ebops(model), cost['total'])
        decay = ablation.i_decay_speeds(model)
        want = cfg['quant'].get('i_decay_speed')
        n_decay_weights = sum(v.name == 'i_decay_speed' for v in model.weights)
        assert n_decay_weights == len(decay), ('i_decay_speed weights not all enumerated', n_decay_weights, len(decay))
        if want is not None:
            assert decay and all(v == float(np.float32(want)) for v in decay.values()), (row['name'], want, decay)
        else:
            assert decay == {} and n_decay_weights == 0, (row['name'], 'no key but quantizers carry i_decay_speed', decay)
        k = ablation.ebops_trace_every(cfg)
        epochs_total = int(cfg['train']['epochs'])
        snapshot = cfg['experiment'].get('snapshot_every_epochs')
        traced_epochs = [e for e in range(epochs_total) if ablation.is_traced_epoch(cfg, e)]
        if k is not None:
            assert epochs_total % k == 0 and (not snapshot or int(snapshot) % k == 0), (row['name'], k)
            assert len(traced_epochs) == epochs_total // k + 1 and traced_epochs[0] == 0
            assert all((e + 1) % k == 0 for e in traced_epochs[1:])
            if snapshot:
                assert all(ablation.is_traced_epoch(cfg, e - 1) for e in range(int(snapshot), epochs_total + 1, int(snapshot)))
        else:
            assert len(traced_epochs) == epochs_total
        optimizer = ablation.optimizer_for(cfg, model)
        tr = cfg['train']
        lrs = {e: ablation.learning_rate(cfg, e) for e in (0, 489, 490, 499, 500, tr['epochs'] - 1)}
        batch = int(tr['batch'])
        step = ablation.make_epoch_step(model, optimizer, x[:batch], y[:batch], cfg)
        optimizer.learning_rate.assign(lrs[0])
        loss = [float(v) for v in step(np.arange(batch, dtype='int32')).numpy()]
        assert np.isfinite(loss).all(), loss
        cost_after = ablation.compute_ebops(model, sample, batch_size=ablation.ebops_trace_batch(cfg))
        pred = np.asarray(model(x[:16], training=False))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'm.keras'
            model.save(path)
            loaded = keras.models.load_model(path, compile=False)
            reload_pred = np.asarray(loaded(x[:16], training=False))
            np.testing.assert_allclose(reload_pred, pred, atol=2e-6, rtol=2e-6)
            stored = ablation.stored_state_ebops(model, loaded)
            assert stored['total'] == cost_after['total'], ('stored reload check', stored, cost_after['total'])
            traced = ablation.compute_ebops(loaded, sample, batch_size=ablation.ebops_trace_batch(cfg))
            assert traced['total'] == cost_after['total']
            reload_diff = float(np.max(np.abs(reload_pred - pred)))
            assert ablation.i_decay_speeds(model) == decay, 'i_decay_speed changed by the training step'
            assert ablation.i_decay_speeds(loaded) == decay, 'i_decay_speed changed by save/reload'
        nd = cfg['experiment'].get('nondegenerate')
        # pilot: floors are keyed by the arch/quant sections (NB and the H3 floor share campaign.arm 'A')
        floor_key = json.dumps({'arch': cfg['arch'], 'quant': cfg['quant']}, sort_keys=True)
        if nd is not None and floor_key not in floor_checked:
            probe = json.loads(json.dumps(cfg))
            probe['experiment'].pop('nondegenerate')
            floor_checked[floor_key] = static_floors(probe, with_attn_rule=False)['zero']['total']
        if nd is not None:
            assert floor_checked[floor_key] == nd['zero_floor_ebops'], (row['name'], floor_checked[floor_key], nd)
        weights = int(sum(np.prod(v.shape) for v in model.weights if v.name in ('kernel', 'bias', 'pos_table')))
        report = {'name': row['name'], 'arm': row['arm'], 'seed': row['seed'], 'floor_group': row['arch_name'],
                  'params_count_params': int(model.count_params()), 'params_kernel_bias_pos': weights,
                  'initial_ebops_synthetic': cost['total'], 'ebops_after_one_step': cost_after['total'],
                  'one_step_loss': loss[0], 'lr': lrs, 'reload_max_abs_diff': reload_diff,
                  'optimizer': tr.get('optimizer'), 'kernel_hashes': evidence['kernel_hashes'],
                  'production': row.get('production', True), 'trace_rows': int(len(sample)),
                  'zero_floor_ebops': None if nd is None else nd['zero_floor_ebops'],
                  'zero_floor_retraced': floor_checked.get(floor_key) if nd is not None else None,
                  'i_decay_speed': decay, 'i_decay_speed_config': want,
                  'i_decay_speed_values': sorted(set(decay.values())),
                  'ebops_trace_every': k, 'traced_epochs': len(traced_epochs), 'status': 'PASS'}
        reports.append(report)
        print('CONFIG_PREFLIGHT_PASS', row['name'], 'params', report['params_count_params'],
              'kernel_bias_pos', weights, 'initial_ebops', cost['total'], 'reload_max_abs_diff',
              reload_diff, 'zero_floor', report['zero_floor_ebops'], 'floor_retraced', report['zero_floor_retraced'],
              'production', int(report['production']), flush=True)
        print('I_DECAY_OK', row['name'], 'config', want, 'quantizers', len(decay),
              'values', report['i_decay_speed_values'], flush=True)
        print('TRACE_EVERY_OK', row['name'], 'k', k, 'epochs', epochs_total, 'traced_epochs', len(traced_epochs),
              'snapshot_every', snapshot, flush=True)
        del model, loaded, optimizer, step
    groups = {}
    for report in reports:
        groups.setdefault((report['floor_group'], report['seed']), []).append(report)
    for (group, seed), members in sorted(groups.items()):
        first = members[0]['kernel_hashes']
        bad = [m['name'] for m in members if m['kernel_hashes'] != first]
        assert not bad, ('matched arms do not share initial kernels', group, seed, bad)
        print('PAIRED_INIT_OK', group, 'seed', seed, 'arms', len(members), ' '.join(m['name'] for m in members), flush=True)
    if args.out:
        args.out.write_text(json.dumps(reports, indent=2) + '\n')
    n_prod = sum(r['production'] for r in reports)
    print('PREFLIGHT_ALL_PASS', len(reports), 'production', n_prod, 'pilot_only', len(reports) - n_prod, flush=True)


if __name__ == '__main__':
    main()
