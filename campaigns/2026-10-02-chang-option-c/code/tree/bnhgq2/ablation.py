"""Controlled, resumable 1000-epoch EBOPs ablations. TensorFlow backend only.

All arms use the same epoch-indexed data order. Recovery excludes only i/f from
Adam updates (including weight decay), without rebuilding/resetting its slots.
Checkpoints contain model, optimizer, PID, selection, freeze and epoch state.
"""
from __future__ import annotations
import copy
import gc
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import time

import keras
import numpy as np
import tensorflow as tf
from hgq.utils.sugar import BetaPID
from . import qat
from .compat import apply_keras_compat
from .ebops_calc import compute_ebops
from .ebops_target import activation_quantizers, width_snapshot
from .train import load_train_data, macro_ovr_auc, _softmax
from .data import input_std_stats, apply_input_std


# Files whose content depends on the trajectory; each checkpoint generation carries a copy
# so that a resume rolls them back to the resume point ([A5]).
SELECTED_FILES = ('model_best.keras', 'model_min_ebops.keras', 'model_unconstrained.keras',
                  'model_best_auc_feasible.keras')


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def array_hash(a):
    return hashlib.sha256(np.ascontiguousarray(a).view(np.uint8)).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')
    os.replace(temp, path)


def prepare_arrays(cfg, data_dir):
    tr = cfg['train']
    x, y, nfiles = load_train_data(data_dir, cfg['arch']['n_part'], features=cfg['arch']['features'])
    permutation = np.random.default_rng(tr['split_seed']).permutation(len(x))
    x, y = x[permutation], y[permutation]
    if cfg['arch'].get('pt_gate_gev') is not None:
        from .data import apply_pt_gate
        x = apply_pt_gate(x, cfg['arch']['features'], cfg['arch']['pt_gate_gev'])
    nv = int(len(x) * tr['validation_split'])
    xv, yv, xt, yt = x[:nv], y[:nv], x[nv:], y[nv:]
    mu, sigma = input_std_stats(xt)
    xt, xv = apply_input_std(xt, mu, sigma), apply_input_std(xv, mu, sigma)
    std = {'mu': mu.tolist(), 'sigma': sigma.tolist(), 'computed_from': 'train split only'}
    info = {'n_train': len(xt), 'n_val': len(xv), 'n_files': nfiles,
            'split_seed': tr['split_seed'], 'order_seed': tr['order_seed'],
            'permutation_sha256': array_hash(permutation), 'input_std': std,
            'train_sha256': array_hash(xt), 'val_sha256': array_hash(xv)}
    return (xt, yt, xv, yv), info


def matching_initialization(cfg, sample, seed):
    """Copy equal-shape kernels/biases/position tables; channel grids start identical."""
    baseline = copy.deepcopy(cfg)
    baseline['arch']['ffn_dim'] = 64
    baseline['quant'].update(act_granularity='tensor', softmax_out_bits=10, softmax_out_i=1)
    reference, rtaps = qat.build_qat_model(baseline, seed=seed)
    qat.calibrate_activations(reference, rtaps, sample, cfg['quant']['act_bits'])
    model, taps = qat.build_qat_model(cfg, seed=seed)
    source = {v.path: v for v in reference.weights if v.name in ('kernel', 'bias', 'pos_table')}
    copied = []
    for variable in model.weights:
        other = source.get(variable.path)
        if other is not None and variable.shape == other.shape:
            variable.assign(other)
            copied.append(variable.path)
    expected_copied = {v.path for v in model.weights
                       if v.path in source and v.shape == source[v.path].shape}
    assert expected_copied and set(copied) == expected_copied, 'Missing equal-shape initialization weights'
    matched_kernels = sum(v.name == 'kernel' and v.path in expected_copied for v in model.weights)
    changed_ffn_kernels = 2 * cfg['arch']['n_layers'] if cfg['arch']['ffn_dim'] != baseline['arch']['ffn_dim'] else 0
    assert matched_kernels == len(expected_binary_layers(cfg)) - changed_ffn_kernels, 'Unexpected matched projection count'
    equivalent_to_weight_reference = (cfg['arch']['ffn_dim'] == baseline['arch']['ffn_dim']
                                     and cfg['quant'].get('softmax_out_bits', max(cfg['quant']['act_bits'], 10)) == 10
                                     and cfg['quant'].get('softmax_out_i', 1) == 1)
    if cfg['quant']['act_granularity'] == 'channel':
        if not equivalent_to_weight_reference:
            # Preserve the shared FFN64 weight reference above, but calibrate a
            # tensor-grid model with this variant's actual forward architecture.
            # In particular, FFN32 and different probability precision are not
            # functionally equivalent to the historical reference.
            tensor_cfg = copy.deepcopy(cfg)
            tensor_cfg['quant']['act_granularity'] = 'tensor'
            reference, rtaps = qat.build_qat_model(tensor_cfg, seed=seed)
            initialized = {v.path: v for v in model.weights if v.name in ('kernel', 'bias', 'pos_table')}
            for variable in reference.weights:
                if variable.path in initialized:
                    variable.assign(initialized[variable.path])
            qat.calibrate_activations(reference, rtaps, sample, cfg['quant']['act_bits'])
        refs = dict(activation_quantizers(reference))
        for name, q in activation_quantizers(model):
            if q.trainable and hasattr(q, '_f'):
                r = refs[name]
                q._i.assign(np.full(q._i.shape, np.asarray(r._i.numpy()).item(), dtype='float32'))
                q._f.assign(np.full(q._f.shape, np.asarray(r._f.numpy()).item(), dtype='float32'))
        np.testing.assert_allclose(model(sample[:8], training=False), reference(sample[:8], training=False), atol=2e-6, rtol=2e-6)
    else:
        qat.calibrate_activations(model, taps, sample, cfg['quant']['act_bits'])
    evidence = {'matched_weight_paths': copied,
                'matched_projection_count': matched_kernels,
                'equivalent_to_weight_reference': equivalent_to_weight_reference,
                'channel_tensor_forward_equivalence_checked': cfg['quant']['act_granularity'] == 'channel',
                'kernel_hashes': {v.path: array_hash(v.numpy()) for v in model.weights
                                  if v.name in ('kernel', 'bias', 'pos_table')}}
    del reference
    return model, evidence


def chang_cosine_restarts(eta0, period, t_mul=1.0, m_mul=1.0, alpha=0.0, hold=0):
    """[A1]/[D2] Cosine decay with warm restarts, evaluated per epoch (zero-based `epoch`),
    implemented from the STUDY [D2] formula, the schedule of jsc150 run_train.py:21-37,93
    (HGQ2-examples 6cdc6e3; no code copied, that repository has no license file):
      cycle c starts at epoch s_c with length L_c = period * t_mul**c,
      t = min((epoch - s_c) / (L_c - hold), 1),
      lr = alpha + 0.5 * (eta0 - alpha) * (1 + cos(pi * t)) * m_mul**c.
    alpha is an absolute floor, held for the last `hold` epochs of each cycle; no warmup."""
    from math import cos, pi

    def schedule(epoch):
        cycle, start, length = 0, 0, period
        while epoch >= start + length:
            start += length
            length *= t_mul
            cycle += 1
        t = min((epoch - start) / (length - hold), 1.0)
        return alpha + 0.5 * (eta0 - alpha) * (1.0 + cos(pi * t)) * m_mul ** cycle
    return schedule


def learning_rate(cfg, epoch):
    tr = cfg['train']
    if tr.get('lr_schedule') == 'chang_cosine_restarts':
        return float(chang_cosine_restarts(tr['lr'], tr['lr_cycle_epochs'], tr.get('lr_t_mul', 1.0),
                                           tr.get('lr_m_mul', 1.0), tr['lr_alpha'],
                                           tr['lr_alpha_epochs'])(epoch))
    if tr.get('lr_schedule', 'poly') != 'poly':
        raise ValueError(f"Unsupported train.lr_schedule in the ablation runner: {tr['lr_schedule']!r}")
    warmup, decay = tr['warmup_epochs'], tr['decay_epochs']
    if epoch < warmup:
        return tr['lr'] * (epoch + 1) / warmup
    return tr['lr'] * (1 - min(1., (epoch - warmup) / decay)) ** tr['decay_power'] if decay else tr['lr']


def training_target(cfg, epoch):
    result = float(cfg['train']['ebops']['pid']['target_ebops'])
    for start, budget in cfg['experiment'].get('target_schedule', []):
        if epoch >= start:
            result = float(budget)
    return result


def optimizer_for(cfg, model):
    tr = cfg['train']
    optimizer_class, extra = keras.optimizers.Adam, {}
    study = cfg.get('engram_study', {})
    if study.get('module') is not None:
        from .engram import MemoryAdam
        optimizer_class = MemoryAdam
        extra['memory_lr_multiplier'] = study.get('memory_lr_multiplier', 5.)
    kind = tr.get('optimizer', 'adam_ours')
    if kind == 'adam_default':
        # [A2]/[D3] jsc150 run_train.py:97, `keras.optimizers.Adam()`: beta_1 0.9,
        # beta_2 0.999, epsilon 1e-7, no weight decay, no clipping.
        if study.get('module') is not None:
            raise ValueError('adam_default is not defined for the Engram memory optimizer')
        optimizer = keras.optimizers.Adam(learning_rate=tr['lr'])
        assert (optimizer.beta_1, optimizer.beta_2, optimizer.epsilon) == (0.9, 0.999, 1e-7)
        assert optimizer.weight_decay is None and optimizer.clipvalue is None
        assert optimizer.clipnorm is None and optimizer.global_clipnorm is None
    elif kind == 'adam_ours':
        optimizer = optimizer_class(**extra, learning_rate=tr['lr'], beta_1=.9, beta_2=tr['beta2'],
                                    weight_decay=tr['weight_decay'], clipvalue=tr['clipvalue'])
    else:
        raise ValueError(f'Unsupported train.optimizer: {kind!r}')
    optimizer.build(model.trainable_variables)
    model.compile(optimizer=optimizer, loss=keras.losses.CategoricalCrossentropy(from_logits=True), jit_compile=False)
    return optimizer


def make_epoch_step(model, optimizer, xt, yt, cfg, teacher_logits=None):
    x = tf.convert_to_tensor(xt, dtype=tf.float32)
    y = tf.convert_to_tensor(yt, dtype=tf.float32)
    teacher = tf.convert_to_tensor(teacher_logits if teacher_logits is not None else np.zeros_like(yt), dtype=tf.float32)
    distillation = cfg['experiment'].get('distillation')
    temperature = float(distillation['temperature']) if distillation else 2.
    coefficient = float(distillation['coefficient']) if distillation else 0.
    all_vars = tuple(model.trainable_variables)
    width_ids = {id(v) for _, q in activation_quantizers(model) if q.trainable and hasattr(q, '_f') for v in (q._i, q._f)}
    weight_vars = tuple(v for v in all_vars if id(v) not in width_ids)
    batch = int(cfg['train']['batch'])
    n = len(xt)

    @tf.function(jit_compile=False)
    def epoch_step(order, frozen=False):
        variables = weight_vars if frozen else all_vars
        totals = tf.zeros((4,), dtype=tf.float32)
        for start in tf.range(0, n, batch):
            idx = order[start:tf.minimum(start + batch, n)]
            xb, yb = tf.gather(x, idx), tf.gather(y, idx)
            with tf.GradientTape() as tape:
                logits = model(xb, training=True)
                ce = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(labels=yb, logits=logits))
                teacher_logp = tf.nn.log_softmax(tf.gather(teacher, idx) / temperature)
                student_logp = tf.nn.log_softmax(logits / temperature)
                kd = temperature ** 2 * tf.reduce_mean(tf.reduce_sum(tf.exp(teacher_logp) * (teacher_logp - student_logp), axis=-1)) if distillation else tf.constant(0.)
                resource_loss = tf.add_n(model.losses) if model.losses else tf.constant(0.)
                loss = ce + coefficient * kd + resource_loss
            gradients = tape.gradient(loss, variables)
            pairs = [(g, v) for g, v in zip(gradients, variables) if g is not None]
            optimizer.apply_gradients(pairs)
            count = tf.cast(tf.shape(idx)[0], tf.float32)
            acc = tf.reduce_mean(tf.cast(tf.argmax(logits, -1) == tf.argmax(yb, -1), tf.float32))
            totals += count * tf.stack([loss, ce, kd, acc])
        return totals / tf.cast(n, tf.float32)
    return epoch_step


def raw_widths(model):
    return {name: {'i': q._i.numpy().tolist(), 'f': q._f.numpy().tolist()}
            for name, q in activation_quantizers(model) if q.trainable and hasattr(q, '_f')}


def save_checkpoint(out, model, optimizer, state):
    out = Path(out)
    root = out / 'checkpoints'
    root.mkdir(exist_ok=True)
    leaf = f"epoch-{state['completed_epochs']:04d}"
    temp = root / ('.' + leaf)
    if temp.exists():
        shutil.rmtree(temp)
    temp.mkdir()
    model.save(temp / 'model.keras')
    np.savez(temp / 'optimizer.npz', **{f'v{i}': v.numpy() for i, v in enumerate(optimizer.variables)})
    atomic_json(temp / 'state.json', state)
    for name in SELECTED_FILES:
        if (out / name).exists():
            shutil.copyfile(out / name, temp / name)
    final = root / leaf
    if final.exists():
        shutil.rmtree(final)
    os.replace(temp, final)
    atomic_json(out / 'latest.json', {'checkpoint': leaf})
    # Retain two complete generations; partial writes can never replace latest.json.
    for old in sorted(root.glob('epoch-*'))[:-2]:
        shutil.rmtree(old)
    return final


def save_snapshot(out, state):
    """[A6] out/snapshots/epoch-EEEE/: the selected files and state as of the end of epoch
    E (one-based), written once, atomically."""
    out = Path(out)
    root = out / 'snapshots'
    root.mkdir(exist_ok=True)
    leaf = f"epoch-{state['completed_epochs']:04d}"
    temp = root / ('.' + leaf)
    if temp.exists():
        shutil.rmtree(temp)
    temp.mkdir()
    for name in SELECTED_FILES:
        if (out / name).exists():
            shutil.copyfile(out / name, temp / name)
    if (out / 'pid_telemetry.jsonl').exists():
        # option (c): frozen controller telemetry through this boundary (absent file: unchanged)
        shutil.copyfile(out / 'pid_telemetry.jsonl', temp / 'pid_telemetry.jsonl')
    atomic_json(temp / 'state.json', state)
    final = root / leaf
    if final.exists():
        shutil.rmtree(final)
    os.replace(temp, final)
    return final


def restore_checkpoint(out, cfg, dataset_info):
    out = Path(out)
    pointer = out / 'latest.json'
    if not pointer.exists():
        return None
    directory = out / 'checkpoints' / json.loads(pointer.read_text())['checkpoint']
    state = json.loads((directory / 'state.json').read_text())
    assert state['config_sha256'] == digest_json(cfg), 'Resume config mismatch'
    assert state['data_sha256'] == digest_json(dataset_info), 'Resume data mismatch'
    assert state['code_sha256'] == os.environ.get('BNHGQ2_CODE_SHA256', 'local-check'), 'Resume code mismatch'
    model = keras.models.load_model(directory / 'model.keras', compile=False)
    optimizer = optimizer_for(cfg, model)
    with np.load(directory / 'optimizer.npz') as arrays:
        assert len(arrays.files) == len(optimizer.variables)
        for i, v in enumerate(optimizer.variables):
            assert arrays[f'v{i}'].shape == v.shape
            v.assign(arrays[f'v{i}'])
    for name in SELECTED_FILES:
        target = out / name
        if (directory / name).exists():
            shutil.copyfile(directory / name, target)
        elif target.exists():
            target.unlink()
    # [A5] Replayed epochs are not bit-exact on GPU: drop every trace of the abandoned
    # trajectory past the resume point (selected files were restored above).
    for snap in sorted((out / 'snapshots').glob('epoch-*')) if (out / 'snapshots').exists() else []:
        if int(snap.name.split('-')[1]) > state['completed_epochs']:
            shutil.rmtree(snap)
    history = out / 'activation_widths.jsonl'
    lines = history.read_text().splitlines() if history.exists() else []
    kept = [line for line in lines if json.loads(line)['epoch'] < state['completed_epochs']]
    assert len(kept) == state['completed_epochs'], 'Missing committed epoch history'
    history.write_text('\n'.join(kept) + ('\n' if kept else ''))
    if pid_traced_only(cfg) is not None:
        # option (c): the controller telemetry has exactly the committed epochs, like the history
        truncate_jsonl(out / PID_TELEMETRY, state['completed_epochs'])
    return model, optimizer, state


def expected_binary_layers(cfg):
    """The configured transformer has 6 projections per block and 3 outside it."""
    names = {'input_proj', 'head_fc1', 'head_fc2'}
    for index in range(cfg['arch']['n_layers']):
        names.update(f'bit_block_{index}_{suffix}' for suffix in
                     ('attn_Wq', 'attn_Wk', 'attn_Wv', 'attn_Wo', 'ffn_fc1', 'ffn_fc2'))
    if cfg['arch'].get('pair_bias', False):
        names.update(('pair_fc1', 'pair_fc2'))
    return names


def binary_gate(model, cfg=None):
    # Optional inference retains compatibility with the older standalone checks.
    if cfg is None:
        blocks = [layer for layer in model.layers if layer.name.startswith('bit_block_') and layer.name.endswith('_attn_Wq')]
        cfg = {'arch': {'n_layers': len(blocks), 'pair_bias': any(layer.name == 'pair_fc1' for layer in model.layers)}}
    values = qat.effective_weight_values(model)
    assert set(values) == expected_binary_layers(cfg), 'Binary projection names/count do not match configured architecture'
    assert all(len(v) == 2 and not (v == 0).any() and np.isclose(v[0], -v[1]) for v in values.values()), 'Binary gate failed'


def checkpoint_selection_metric(cfg):
    """Keep the registered AUC objective unless a new experiment opts into accuracy."""
    metric = cfg['experiment'].get('selection_metric', 'val_macro_auc')
    if metric not in ('val_macro_auc', 'val_categorical_accuracy'):
        raise ValueError(f'Unsupported experiment.selection_metric: {metric!r}')
    return metric


def checkpoint_selection_key(point, metric, *, cost_before_auc=False):
    """Default ordering also accepts historical checkpoint points without accuracy."""
    tail = (point['val_macro_auc'], -point['ebops'], -point['epoch'])
    if metric == 'val_macro_auc':
        return tail
    if metric == 'val_categorical_accuracy':
        if cost_before_auc:
            return (point[metric], -point['ebops'], point['val_macro_auc'], -point['epoch'])
        return (point[metric],) + tail
    raise ValueError(f'Unsupported checkpoint selection metric: {metric!r}')


def cost_before_auc(cfg):
    """[A13] Tie-break order. `experiment.cost_before_auc` (bool) overrides the historical
    inference from the presence of an `engram_study` block, which put -EBOPs before val AUC
    (accuracy -> -EBOPs -> AUC -> -epoch). Absent key => historical behaviour."""
    explicit = cfg['experiment'].get('cost_before_auc')
    if explicit is not None:
        if not isinstance(explicit, bool):
            raise ValueError('experiment.cost_before_auc must be a bool')
        return explicit
    return bool(cfg.get('engram_study'))


def keep_auc_feasible(cfg):
    return bool(cfg['experiment'].get('keep_auc_selected_feasible', False))


def validation_metrics(labels, logits):
    """Measure ranking and decisions on exactly the same inference outputs."""
    logits = np.asarray(logits)
    if logits.shape != labels.shape or not np.isfinite(logits).all():
        raise ValueError('Validation logits must be finite and match label shape')
    auc, per_auc = macro_ovr_auc(labels, _softmax(logits))
    accuracy = float(np.mean(logits.argmax(axis=-1) == labels.argmax(axis=-1)))
    return auc, per_auc, accuracy


class Diverged(RuntimeError):
    """[A12] A recorded divergence: DIVERGED.json is written, the arm is never resumed."""


def record_divergence(out, cfg, state, epoch, reason, metrics, wandb_run=None):
    """Write DIVERGED.json (zero-based divergence epoch, the non-finite metrics, the last
    completed epoch's selection state) before raising. STUDY: a diverged run is an outcome,
    never relaunched; its pre-divergence best-feasible checkpoint is reported, not used."""
    def finite(value):
        return value if isinstance(value, (int, float)) and np.isfinite(value) else repr(value)
    record = {'name': cfg['name'], 'divergence_epoch_zero_based': int(epoch),
              'completed_epochs_before': int(state['completed_epochs']), 'reason': reason,
              'metrics_at_divergence': {k: finite(float(v)) for k, v in metrics.items()},
              'best_feasible_before': state['best_feasible'], 'lowest_before': state['lowest'],
              'best_auc_before': state['best_auc'],
              'best_feasible_auc_before': state.get('best_feasible_auc'),
              'model_best_present': (Path(out) / 'model_best.keras').exists(),
              'code_sha256': state['code_sha256'], 'config_sha256': state['config_sha256']}
    atomic_json(Path(out) / 'DIVERGED.json', record)
    print('ARM_DIVERGED', cfg['name'], json.dumps(record), flush=True)
    if wandb_run is not None:
        wandb_run.summary.update({'phase': 'diverged', 'divergence_epoch': int(epoch) + 1})
        wandb_run.finish(exit_code=3)
    return record


def seeded_run_name(name, seed):
    suffix = f'-s{seed}'
    return name if name.endswith(suffix) else name + suffix


def training_status_summary(state, selection_metric, stop_after=None, paused=False):
    summary = {'completed_epochs': state['completed_epochs'], 'selection_metric': selection_metric,
               'phase': 'paused_for_promotion' if paused else 'screening' if stop_after is not None else 'training'}
    if stop_after is not None:
        summary['screening_target_epochs'] = int(stop_after)
    point = state['best_feasible']
    if point is not None:
        summary.update(best_feasible_val_macro_auc=point['val_macro_auc'],
                       best_feasible_ebops=point['ebops'], best_feasible_epoch=point['epoch'] + 1,
                       best_feasible_epoch_zero_based=point['epoch'])
        if 'val_categorical_accuracy' in point:
            summary['best_feasible_val_accuracy'] = point['val_categorical_accuracy']
    return summary


def ebops_trace_sample(cfg, xt):
    """[D20] Rows every `compute_ebops` trace runs on (WRAP ranges and feasibility EBOPs).

    `train.ebops_trace_sample` absent: the first 256 training rows (the screen runner).
    "train_full": the whole training split. An int n: the first n training rows.
    Training rows only; validation never enters the range fit."""
    spec = cfg['train'].get('ebops_trace_sample')
    if spec is None:
        return xt[:256]
    if spec == 'train_full':
        return xt
    if isinstance(spec, bool) or not isinstance(spec, int) or spec <= 0:
        raise ValueError(f"train.ebops_trace_sample must be 'train_full' or a positive int, got {spec!r}")
    return xt[:spec]


def ebops_trace_batch(cfg):
    """Forward batch of the trace. The traced min/max is a max over rows, so the batch
    changes only speed, not the result (up to kernel-selection rounding on GPU); the
    certification retrace reads the same key."""
    return int(cfg['train'].get('ebops_trace_batch', 2048))


def ebops_trace_every(cfg):
    """[D20] regime B (Kai, 2026-09-27): `train.ebops_trace_every: k` runs the full-split reset
    trace only at traced epochs (see `is_traced_epoch`). Absent: None, one trace per epoch
    (regime A, byte-identical to the runner before this key). Requires the [D20] trace sample
    and the stored reload check, and a snapshot cadence that is a multiple of k, so every
    snapshot (the epoch-500 readout) falls on a traced epoch."""
    k = cfg['train'].get('ebops_trace_every')
    if k is None:
        return None
    if isinstance(k, bool) or not isinstance(k, int) or k < 1:
        raise ValueError(f'train.ebops_trace_every must be a positive int, got {k!r}')
    if cfg['train'].get('ebops_trace_sample') is None:
        raise ValueError('train.ebops_trace_every needs train.ebops_trace_sample ([D20])')
    if cfg['train'].get('ebops_reload_check', 'retrace') != 'stored':
        raise ValueError('train.ebops_trace_every needs train.ebops_reload_check "stored": a retrace '
                         'on an untraced epoch would compare a reset trace with in-training EBOPs')
    snapshot = cfg['experiment'].get('snapshot_every_epochs')
    if snapshot and int(snapshot) % k:
        raise ValueError(f'snapshot_every_epochs {snapshot} is not a multiple of ebops_trace_every {k}')
    return k


def is_traced_epoch(cfg, epoch):
    """Zero-based `epoch` is traced iff epoch == 0, (epoch + 1) % k == 0, or it is the last epoch.
    The epoch-0 trace is not needed to initialize the ranges (the reset trace before training,
    `initial_ebops`, does that); it is there so the canary reads a traced end of epoch 1
    against the end of epoch 10 (STUDY slot T, arbiter v9)."""
    k = ebops_trace_every(cfg)
    return k is None or epoch == 0 or (epoch + 1) % k == 0 or epoch + 1 == cfg['train']['epochs']


PID_TRACED_INTEGRAL = ('per_epoch', 'per_step')


def pid_traced_only(cfg):
    """Option (c) (Kai K1, 2026-09-28; staged): `train.ebops.pid_input: "traced_only"`. Under
    regime B the PID reads only the traced full-split EBOPs: it is stepped at the start of epoch
    e iff epoch e - 1 was traced (or e is inside the BetaPID warmup), and beta is held otherwise.
    Absent key: None, and the runner is byte-identical to 42abed4b (slot P: the PID steps every
    epoch and reads the in-training EBOPs on untraced epochs).

    `train.ebops.pid_traced_integral` ("per_epoch", the default, or "per_step") says how the
    integral is fed when a step covers D epochs: "per_epoch" adds D times the held traced error
    (the error the per-epoch controller would have integrated had it seen that trace for D
    epochs; i = 0.05 keeps its per-epoch meaning); "per_step" adds it once (hgq2 `PID.__call__`
    unchanged, so the integral acts D times slower per epoch). Returns the mode or None."""
    eb = cfg['train']['ebops']
    mode = eb.get('pid_input')
    if mode is None:
        if eb.get('pid_traced_integral') is not None:
            raise ValueError('train.ebops.pid_traced_integral needs train.ebops.pid_input "traced_only"')
        return None
    if mode != 'traced_only':
        raise ValueError(f'train.ebops.pid_input must be absent or "traced_only", got {mode!r}')
    if ebops_trace_every(cfg) is None:
        raise ValueError('train.ebops.pid_input "traced_only" needs train.ebops_trace_every (regime B)')
    # Option-(c) amendment (2026-10-01): the integral convention is explicit in every config,
    # never a silent default.
    if eb.get('pid_traced_integral') is None:
        raise ValueError('train.ebops.pid_input "traced_only" needs an explicit train.ebops.pid_traced_integral')
    integral = eb['pid_traced_integral']
    if integral not in PID_TRACED_INTEGRAL:
        raise ValueError(f'train.ebops.pid_traced_integral must be one of {PID_TRACED_INTEGRAL}, got {integral!r}')
    pid = eb['pid']
    if float(pid.get('d', 0.0)) != 0.0:
        raise ValueError('train.ebops.pid_input "traced_only" is defined for d == 0 only (a derivative '
                         'over a D-epoch step has no per-epoch meaning)')
    warmup = int(pid.get('warmup', 10))
    if warmup >= 1 and not is_traced_epoch(cfg, warmup - 1):
        # BetaPID seeds the integral only at epoch == warmup (beta_pid.py:140-148); a held step
        # there would skip the seed and jump beta from init_beta to 10 ** (p * err).
        raise ValueError(f'train.ebops.pid_input "traced_only" needs epoch warmup - 1 = {warmup - 1} traced')
    return integral


def pid_step_epochs(cfg, epoch):
    """Option (c): (stepped, span). `stepped`: whether BetaPID.on_epoch_begin runs at zero-based
    `epoch`. `span`: epochs since the previous stepped epoch at or after the warmup (1 for the
    first such step, where BetaPID seeds the integral). A pure function of (cfg, epoch), so a
    resume from an untraced checkpoint needs no new state."""
    warmup = int(cfg['train']['ebops']['pid'].get('warmup', 10))
    if epoch < warmup:
        return True, 1    # hgq2 warmup branch: only re-applies init_beta, reads no EBOPs
    if not is_traced_epoch(cfg, epoch - 1):
        return False, 0
    previous = epoch - 1
    while previous >= warmup and not is_traced_epoch(cfg, previous - 1):
        previous -= 1
    return True, (epoch - previous if previous >= warmup else 1)


def pid_error(pid):
    """The error hgq2 0.1.9 `BetaPID.on_epoch_begin` feeds `PID.__call__` (neg=True, so
    err = pv - sv): log10(E / T) with `log`, else E / T - 1 (beta_pid.py:150-153)."""
    ratio = pid._ebops / pid.target_ebops
    return math.log10(ratio) if pid.log else ratio - 1.0


def pid_begin_traced_only(pid, cfg, epoch, integral_mode):
    """Option (c) replacement for `pid.on_epoch_begin(epoch, {})`. Held epoch: not called, beta
    and the PID state unchanged. Stepped epoch: with "per_epoch", the integral first receives
    (span - 1) extra copies of the held traced error, then hgq2 adds the last one. hgq2 has no
    anti-windup (`PID.__call__` integrates unconditionally, beta_pid.py:29; beta is clamped only
    after, :158), and neither mode adds one. Returns (stepped, span)."""
    stepped, span = pid_step_epochs(cfg, epoch)
    if not stepped:
        return False, 0
    warmup = int(cfg['train']['ebops']['pid'].get('warmup', 10))
    if integral_mode == 'per_epoch' and epoch > warmup and span > 1:
        pid.pid.integral += (span - 1) * pid_error(pid)
    pid.on_epoch_begin(epoch, {})
    return True, span


PID_TELEMETRY = 'pid_telemetry.jsonl'
PID_INPUT_RTOL = 1e-6   # the registered [D20] PID/trace tolerance


def pid_input_check(pid_input, last_trace):
    """Option-(c) amendment: a stepped epoch at or after the warmup consumes the most recent
    traced cost, within the registered relative 1e-6; anything else is a controller defect."""
    if last_trace is None:
        raise AssertionError('Option (c) PID stepped before any traced cost exists')
    if abs(pid_input - last_trace) > PID_INPUT_RTOL * max(abs(last_trace), 1.0):
        raise AssertionError(('Option (c) PID input differs from the last trace', pid_input, last_trace))


def pid_telemetry_row(epoch, *, stepped, span, pid_input, pid_error_value, integral, prev_error,
                      beta_after_step, beta_end, target, ebops_in_training, traced, ebops_traced,
                      pid_ebops_end, learning_rate, monitor=None):
    """One line of `pid_telemetry.jsonl` (option-(c) amendment: controller telemetry durable
    without stdout or W&B). Epoch semantics, all zero-based `epoch`:
      begin of epoch: stepped, span, pid_input (cost the step consumed; null when held or in the
        warmup branch, which reads no cost), pid_error (log10(pid_input / target) under `log`),
        pid_integral / pid_prev_error (after the step), beta_after_step (beta used for training);
      end of epoch: ebops_in_training (stored layer cost of the last training step, never a PID
        input under (c)), ebops_traced (full-split trace, null when untraced), beta_end and
        pid_ebops_end (the value the next step would consume).
    `monitor` (end of epoch, never a controller input): loss, validation accuracy/AUC, the
    registered feasibility flags (traced epochs only) and the attention summary."""
    return {**(monitor or {}),'epoch': int(epoch), 'pid_stepped': int(stepped), 'pid_step_span': int(span),
            'pid_input': None if pid_input is None else float(pid_input),
            'pid_error': None if pid_error_value is None else float(pid_error_value),
            'pid_integral': float(integral), 'pid_prev_error': float(prev_error),
            'beta_after_step': float(beta_after_step), 'beta_end': float(beta_end),
            'pid_target_ebops': float(target),
            'ebops_in_training': None if ebops_in_training is None else float(ebops_in_training),
            'ebops_traced_flag': int(traced),
            'ebops_traced': None if ebops_traced is None else float(ebops_traced),
            'pid_ebops_end': float(pid_ebops_end), 'learning_rate': float(learning_rate)}


ATTN_WIDTHS = {'q': '_attn_scores__in0', 'k': '_attn_scores__in1', 'v': '_attn_ctx__in1'}


def _zero_bits(bits):
    flat = np.asarray(bits, dtype=float).ravel()
    return [int((flat == 0).sum()), int(flat.size)]


def attention_summary(widths, per_layer=None):
    """Option-(c) pilot monitoring (b5 readout 2026-10-02: at 350k every head went uniform by
    about epoch 40). Per block, [channels at 0 bits, channels] of the Q, K and V inputs, read
    from HGQ2 `bits` (the field the b5 readout used; under SAT it counts the sign bit, so a SAT
    channel never reads 0 here), and on traced epochs the attention cost outside the softmax
    table. Q and K all at 0 bits under WRAP means jet-independent attention logits."""
    blocks = {}
    for name, entry in widths.items():
        for role, suffix in ATTN_WIDTHS.items():
            if name.startswith('bit_block_') and name.endswith(suffix):
                block = name[len('bit_block_'):-len(suffix)]
                blocks.setdefault(block, {})[role] = _zero_bits(entry['bits'])
    out = {'attn_zero_bits': blocks,
           'attn_qk_all_zero': int(bool(blocks) and all(
               b.get(r, [0, 1])[0] == b.get(r, [0, 1])[1] for b in blocks.values() for r in ('q', 'k')))}
    if per_layer:
        out['attn_nonsoftmax_ebops'] = float(sum(v for k, v in per_layer.items()
                                                 if '_attn_' in k and not k.endswith('_attn_softmax')))
        out['attn_softmax_ebops'] = float(sum(v for k, v in per_layer.items() if k.endswith('_attn_softmax')))
    return out


def truncate_jsonl(path, completed_epochs, required=True):
    """Keep only committed epochs (< completed_epochs) of an epoch-keyed JSONL history."""
    lines = path.read_text().splitlines() if path.exists() else []
    kept = [line for line in lines if json.loads(line)['epoch'] < completed_epochs]
    if required:
        assert len(kept) == completed_epochs, 'Missing committed epoch history'
    if path.exists() or kept:
        path.write_text('\n'.join(kept) + ('\n' if kept else ''))
    return len(kept)


def append_jsonl(path, record):
    with path.open('a') as f:
        f.write(json.dumps(record, allow_nan=False) + '\n')
        f.flush()
        os.fsync(f.fileno())


def model_ebops(model):
    """The EBOPs sum BetaPID reads (`BaseBetaPID.get_ebops`, hgq2 0.1.9): the stored
    `layer.ebops` of the top-level layers, whatever pass wrote them last."""
    return float(sum(float(layer.ebops) for layer in model.layers if hasattr(layer, 'ebops')))


def stored_state_ebops(model, loaded):
    """[D20] post-reload check without a second trace (`train.ebops_reload_check: "stored"`).

    Every variable of the reloaded model (kernels, biases, PE, every quantizer's i/f/b/k,
    and each layer's stored `ebops`) must equal the in-memory model's byte for byte. EBOPs
    are a function of those widths only, so equal variables give equal EBOPs; the stored
    per-layer `ebops`, summed as trace_minmax sums them, is returned for the equality test.
    Stronger than `raw_widths` (which skips KBI tables and k)."""
    import re

    def role(path):   # auto-numbered sublayer names (quantizer_kif_17) differ per build
        return re.sub(r'_\d+(?=/|$)', '', path)

    a, b = list(model.weights), list(loaded.weights)
    if [role(v.path) for v in a] != [role(v.path) for v in b]:
        raise AssertionError('Variable layout differs after reload')
    for var, other in zip(a, b):
        x, y = np.asarray(var), np.asarray(other)
        if x.dtype != y.dtype or x.shape != y.shape or x.tobytes() != y.tobytes():
            raise AssertionError(f'{var.path} changed after reload')
    total = sum(int(layer.ebops) for layer in loaded.layers if getattr(layer, 'enable_ebops', False))
    return {'total': int(total)}


def saved_ebops(loaded):
    """The EBOPs a saved file carries: its layers' stored `ebops`, written by the last trace
    before the save and summed as `stored_state_ebops` and certify_ebops.py sum them.
    Reads the file's state; runs nothing, so every WRAP range stays as saved."""
    return int(sum(int(layer.ebops) for layer in loaded.layers if getattr(layer, 'enable_ebops', False)))


def selected_checkpoint_ebops(cfg, loaded, xt):
    """Post-pause / post-run check of a reloaded selected checkpoint (run_study.train,
    run_engram train), by the same method as the per-epoch reload check (PREFLIGHT gate v1,
    2026-09-27; before this, both sites retraced on xt[:256] whatever the config said).

    `train.ebops_reload_check: "stored"` ([D20]): the file's stored EBOPs (`saved_ebops`), no
    trace, so `predict` then runs on the ranges as saved. The full-split reset retrace of the
    same file is certify_ebops.py's job, outside the training pod.
    Otherwise ("retrace" or absent): a reset retrace on `ebops_trace_sample(cfg, xt)` at
    `ebops_trace_batch(cfg)`, the rows the logged EBOPs came from. With neither [D20] key set
    that is xt[:256] at batch 2048, the screen runner's call unchanged."""
    if cfg['train'].get('ebops_reload_check', 'retrace') == 'stored':
        per_layer = {layer.name: int(layer.ebops) for layer in loaded.layers
                     if getattr(layer, 'enable_ebops', False)}
        return {'total': saved_ebops(loaded), 'per_layer': per_layer, 'method': 'stored'}
    cost = compute_ebops(loaded, np.asarray(ebops_trace_sample(cfg, xt)), batch_size=ebops_trace_batch(cfg))
    return {**cost, 'method': 'retrace'}


def i_decay_speeds(model):
    """[D20] per datalane quantizer, HGQ2's `i_decay_speed`: in training, a WRAP quantizer's
    integer bits follow i <- max(i - i_decay_speed, i_batch) every step (0.1.9
    `FixedPointQuantizerKIF.call`), so between two per-epoch traces the range can shrink by
    this much per step. Recorded, not changed."""
    return {name: float(np.asarray(q.i_decay_speed)) for name, q in activation_quantizers(model)
            if hasattr(q, '_i_decay_speed')}


def majority_rule(yv, se_multiple):
    """[ND, arbiter v3 fix 1] validation-accuracy floor of the non-degeneracy condition, from the class counts
    of the validation labels actually used: p_maj + k * sqrt(p_maj (1 - p_maj) / n_val).
    A constant classifier that always predicts the majority class scores p_maj."""
    yv = np.asarray(yv)
    labels = yv.argmax(axis=-1) if yv.ndim == 2 else yv.astype(int)
    counts = np.bincount(labels, minlength=yv.shape[-1] if yv.ndim == 2 else 0)
    n = int(len(labels))
    p_maj = float(counts.max() / n)
    se = float(np.sqrt(p_maj * (1.0 - p_maj) / n))
    return {'class_counts': [int(c) for c in counts], 'n_val': n, 'p_maj': p_maj, 'se': se,
            'se_multiple': float(se_multiple), 'val_accuracy_threshold': p_maj + float(se_multiple) * se,
            'labels_sha256': array_hash(np.ascontiguousarray(labels))}


def nondegenerate_rule(cfg, yv):
    """[ND, arbiter v3 fix 1] opt-in `experiment.nondegenerate` = {zero_floor_ebops, se_multiple}. Absent:
    feasible means EBOPs <= target, as before. Present: a checkpoint is feasible only if
    EBOPs <= target AND EBOPs - zero_floor_ebops > 0 AND val accuracy > the majority rule;
    EBOPs <= target without the other two is 'feasible, degenerate' (counted, never
    selected)."""
    spec = cfg['experiment'].get('nondegenerate')
    if spec is None:
        return None
    if set(spec) != {'zero_floor_ebops', 'se_multiple'}:
        raise ValueError(f'experiment.nondegenerate needs exactly zero_floor_ebops, se_multiple: {sorted(spec)}')
    floor = spec['zero_floor_ebops']
    if isinstance(floor, bool) or not isinstance(floor, int) or floor < 0:
        raise ValueError(f'experiment.nondegenerate.zero_floor_ebops must be an int >= 0, got {floor!r}')
    return {**majority_rule(yv, spec['se_multiple']), 'zero_floor_ebops': int(floor)}


class ValidationReloader:
    """Per-epoch reload of the saved validation candidate (incident 2026-09-28,
    review/INCIDENT_stall_20260928.md: host memory grew ~90 MB/epoch per arm on the GPU pods).

    The first call builds the model from the file (`keras.models.load_model`); every later call
    loads the file's variables into that same model (`load_weights`), so one model and one
    predict function live for the whole run instead of a new model, graph and predict function
    per epoch. What is evaluated is still exactly the serialized artifact: every variable comes
    from the file, and `stored_state_ebops` / the retrace check compare them with the live model
    each epoch as before. The architecture never changes within a run (one config)."""

    def __init__(self):
        self.model = None

    def __call__(self, path):
        if self.model is None:
            self.model = keras.models.load_model(path, compile=False)
        else:
            self.model.load_weights(path)
        return self.model


RSS_GATE_EXIT = 5


def host_rss_mb():
    """Resident memory of this process in MiB: VmRSS on Linux; phys_footprint on macOS."""
    try:
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return int(line.split()[1]) / 1024
    except OSError:
        pass
    import sys
    if sys.platform == 'darwin':
        import ctypes
        buf = (ctypes.c_uint64 * 40)()
        if ctypes.CDLL('/usr/lib/libproc.dylib').proc_pid_rusage(os.getpid(), 2, ctypes.byref(buf)) == 0:
            return buf[9] / 2 ** 20
    return None


def rss_gate_from_env(total_epochs):
    """Memory canary gate (incident 2026-09-28, review/INCIDENT_stall_20260928.md), set by the Job
    env, never by a config, so config_sha256 is unchanged.

    BNJ_RSS_GATE_LIMIT_MB: the per-arm memory limit written in the manifest (MiB).
    BNJ_RSS_GATE_WINDOW "W:E" (default 5:105): fit host RSS against epoch, by least squares, over
    this process's epochs W..E-1 (counted from the epoch it started or resumed at; E - W >= 100).
    At the end of process epoch E the gate projects the run's terminal RSS:
        projection = baseline + slope * total_epochs,
    with baseline the fitted RSS at epoch W and total_epochs the config's `train.epochs` (7,000;
    R 1,000). projection > limit: RSS_GATE FAIL, RSS_GATE_FAIL.json, exit 5. At 6 GiB and a
    ~2.2 GB baseline this admits a slope of about 0.55 MB/epoch over 7,000 epochs.
    Unset: no gate and no RSS field on the epoch line."""
    raw = os.environ.get('BNJ_RSS_GATE_LIMIT_MB')
    if not raw:
        return None
    warm, end = (int(v) for v in os.environ.get('BNJ_RSS_GATE_WINDOW', '5:105').split(':'))
    if not (0 <= warm and end - warm >= 100):
        raise ValueError('BNJ_RSS_GATE_WINDOW must be W:E with E - W >= 100')
    return {'limit_mb': float(raw), 'warm': warm, 'end': end, 'total_epochs': int(total_epochs), 'rss': []}


def rss_gate_verdict(gate):
    """(slope MB/epoch, baseline MB at W, projection MB, PASS/FAIL) over the gate window."""
    window = np.asarray(gate['rss'][gate['warm']:gate['end']], dtype=float)
    slope, intercept = (float(v) for v in np.polyfit(np.arange(len(window)), window, 1))
    projection = intercept + slope * gate['total_epochs']
    return slope, intercept, projection, 'PASS' if projection <= gate['limit_mb'] else 'FAIL'


def rss_gate_step(gate, name, out):
    """Record this epoch's RSS; at the window end, print the verdict and stop on failure."""
    rss = host_rss_mb()
    gate['rss'].append(rss)
    if len(gate['rss']) == gate['end']:
        if any(v is None for v in gate['rss'][gate['warm']:gate['end']]):
            print(f'RSS_GATE {name} unreadable, not evaluated', flush=True)
            return rss
        slope, baseline, projection, verdict = rss_gate_verdict(gate)
        print(f"RSS_GATE {name} {verdict} slope_mb_per_epoch {slope:.3f} baseline_mb {baseline:.0f} "
              f"projection_mb {projection:.0f} at_epoch {gate['total_epochs']} limit_mb {gate['limit_mb']:.0f} "
              f"fit_epochs {gate['warm']}-{gate['end'] - 1} of this process", flush=True)
        if verdict == 'FAIL':
            (Path(out) / 'RSS_GATE_FAIL.json').write_text(json.dumps(
                {'slope_mb_per_epoch': slope, 'baseline_mb': baseline, 'projection_mb': projection,
                 'limit_mb': gate['limit_mb'], 'total_epochs': gate['total_epochs'], 'rss_mb': gate['rss']}) + '\n')
            raise SystemExit(RSS_GATE_EXIT)
    return rss


def run_training(cfg, arrays, data_info, out, *, teacher_logits=None, remote=False, stop_after=None,
                 model_builder=None, epoch_observer=None):
    """Pause at a cumulative epoch for screening/tests without changing config hashes."""
    if cfg.get('engram_study', {}).get('module') is not None and model_builder is None:
        raise ValueError('Engram needs the memory builder; use run_engram.py train')
    selection_metric = checkpoint_selection_metric(cfg)
    apply_keras_compat()
    seed = cfg['experiment']['seed']
    keras.utils.set_random_seed(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    xt, yt, xv, yv = arrays
    sample = xt[:256]   # engram epoch_observer diagnostics (unchanged)
    # [D20] opt-in: the trace sample of every compute_ebops below. Absent key => xt[:256].
    d20 = cfg['train'].get('ebops_trace_sample') is not None
    if cfg['train'].get('ebops_reload_check', 'retrace') not in ('retrace', 'stored'):
        raise ValueError("train.ebops_reload_check must be 'retrace' or 'stored'")
    trace_rows = ebops_trace_sample(cfg, xt)
    trace_batch = ebops_trace_batch(cfg)
    trace_every = ebops_trace_every(cfg)   # [D20] regime B; None => every epoch (regime A)
    pid_integral_mode = pid_traced_only(cfg)   # option (c); None => slot P as in 42abed4b

    def traced_ebops(m):
        return compute_ebops(m, trace_rows, batch_size=trace_batch)
    rule = nondegenerate_rule(cfg, yv)
    resumed = restore_checkpoint(out, cfg, data_info)
    if resumed:
        model, optimizer, state = resumed
    else:
        if (out / 'activation_widths.jsonl').exists() or (out / PID_TELEMETRY).exists():
            raise RuntimeError('History exists without a committed checkpoint')
        builder = model_builder or matching_initialization
        model, initialization = builder(cfg, xt[:4096], seed)
        optimizer = optimizer_for(cfg, model)
        initial = traced_ebops(model)
        state = {'config_sha256': digest_json(cfg), 'data_sha256': digest_json(data_info),
                 'code_sha256': os.environ.get('BNHGQ2_CODE_SHA256', 'local-check'),
                 'completed_epochs': 0, 'initial_ebops': initial['total'], 'initial_widths': width_snapshot(model),
                 'best_feasible': None, 'lowest': None, 'best_auc': None, 'recovery_frozen': False,
                 'freeze_epoch': None, 'freeze_widths': None, 'pid': None, 'train_seconds': 0.}
        atomic_json(out / 'initialization.json', initialization)
        atomic_json(out / 'config.json', cfg)
        atomic_json(out / 'data_info.json', data_info)
        atomic_json(out / 'input_std.json', data_info['input_std'])
        if d20:
            state['i_decay_speed'] = i_decay_speeds(model)
            atomic_json(out / 'i_decay_speed.json', state['i_decay_speed'])
        if rule is not None:
            state.update(nondegenerate_rule=rule, feasible_degenerate_epochs=0, first_feasible_degenerate=None)
            atomic_json(out / 'nondegenerate_rule.json', rule)
    if rule is not None and state.get('nondegenerate_rule') != rule:
        raise RuntimeError('Non-degeneracy rule differs from the one fixed at the start of this run')
    binary_gate(model, cfg)
    print(f"[train] {cfg['name']} params={model.count_params()} resume_epoch={state['completed_epochs']} initial_ebops={state['initial_ebops']}", flush=True)
    final_target = cfg['train']['ebops']['pid']['target_ebops']
    pid = BetaPID(**cfg['train']['ebops']['pid'])
    pid.set_model(model)
    pid.on_train_begin({})
    if state['pid']:
        p = state['pid']
        pid.beta, pid._ebops = p['beta'], p['ebops']
        pid.pid.integral, pid.pid.prev_error = p['integral'], p['prev_error']
        pid.set_beta(pid.beta)
    # option (c): the most recent traced cost. On resume it is the PID's stored input: under (c)
    # only a traced epoch end moves `_ebops` (held ends assert it), so the two are equal.
    last_trace = state['pid']['ebops'] if state['pid'] else None
    if cfg['experiment'].get('distillation'):
        assert teacher_logits is not None and teacher_logits.shape == yt.shape
    wandb_run = None
    if remote:
        import wandb
        from .wandb_util import init_kwargs, run_stage, stage_group, stage_run_id
        stage = run_stage(required=True)   # BNJ_STAGE from the Job manifest (never a config key)
        run_id = stage_run_id(cfg['name'], stage)
        wandb_run = wandb.init(**init_kwargs(name=seeded_run_name(cfg['name'], seed), job_type='train',
                         cfg_project=cfg['train']['wandb_project'], group=stage_group(cfg['experiment']['group'], stage),
                         config={'experiment_config': cfg, 'data': data_info, 'code_sha256': state['code_sha256']}),
                         id=run_id, resume='allow')
        wandb_run.summary.update(training_status_summary(state, selection_metric, stop_after))
    if stop_after is not None and state['completed_epochs'] >= stop_after:
        if wandb_run:
            wandb_run.summary.update(training_status_summary(state, selection_metric, stop_after, paused=True))
            wandb_run.finish()
        return state
    step = make_epoch_step(model, optimizer, xt, yt, cfg, teacher_logits)
    epochs = cfg['train']['epochs']
    reload_candidate = ValidationReloader()
    rss_gate = rss_gate_from_env(epochs)
    for epoch in range(state['completed_epochs'], epochs):
        start = time.monotonic()
        lr = learning_rate(cfg, epoch)
        optimizer.learning_rate.assign(lr)
        pid.target_ebops = training_target(cfg, epoch)
        if pid_integral_mode is None:
            pid.on_epoch_begin(epoch, {})
        else:
            # option (c): step only on the traced EBOPs of epoch - 1; otherwise beta is held
            reads_cost = pid_step_epochs(cfg, epoch)[0] and epoch >= int(cfg['train']['ebops']['pid'].get('warmup', 10))
            pid_input = float(pid._ebops) if reads_cost else None
            if reads_cost:
                pid_input_check(pid_input, last_trace)
            pid_err = pid_error(pid) if reads_cost else None
            pid_stepped, pid_span = pid_begin_traced_only(pid, cfg, epoch, pid_integral_mode)
            beta_after_step = float(pid.beta)
        order = np.random.default_rng(np.random.SeedSequence([cfg['train']['order_seed'], epoch])).permutation(len(xt)).astype('int32')
        loss, ce, kd, accuracy = [float(v) for v in step(order, state['recovery_frozen']).numpy()]
        if not np.isfinite([loss, ce, kd, accuracy]).all():
            record_divergence(out, cfg, state, epoch, 'nonfinite training metrics',
                              {'loss': loss, 'task_loss': ce, 'distillation_loss': kd,
                               'train_categorical_accuracy': accuracy}, wandb_run)
            raise Diverged('Nonfinite training metrics')
        # Cost tracing updates HGQ range state. Validate the traced state that
        # is actually saved, so checkpoint metrics and reloaded predictions agree.
        # [D20] the in-training EBOPs (what HGQ2's FreeEBOPs would log: the stored
        # layer.ebops of the last training step), read before the trace overwrites it.
        in_training_ebops = model_ebops(model) if d20 else None
        # [D20] regime B: untraced epochs run no trace; the model keeps its in-training
        # ranges and stored EBOPs, and nothing below may select or test feasibility on them.
        traced = is_traced_epoch(cfg, epoch)
        trace_start = time.monotonic()
        if traced:
            cost = traced_ebops(model)
        else:
            cost = {'total': saved_ebops(model), 'per_layer': None}
        trace_seconds = time.monotonic() - trace_start
        # Evaluate exactly the serialized artifact. Live compiled-model inference
        # and fresh-load inference can choose different floating-point kernels.
        candidate = out / 'validation_candidate.keras'
        model.save(candidate)
        validation_model = reload_candidate(candidate)
        check_start = time.monotonic()
        if cfg['train'].get('ebops_reload_check', 'retrace') == 'stored':
            verified_cost = stored_state_ebops(model, validation_model)
        else:
            verified_cost = traced_ebops(validation_model)
        reload_check_seconds = time.monotonic() - check_start
        assert verified_cost['total'] == cost['total'], 'Candidate cost changed after reload'
        logits = np.asarray(validation_model.predict(xv, batch_size=cfg['train']['val_batch'], verbose=0))
        if not np.isfinite(logits).all():
            record_divergence(out, cfg, state, epoch, 'nonfinite validation logits',
                              {'loss': loss, 'train_categorical_accuracy': accuracy}, wandb_run)
            raise Diverged('Nonfinite validation logits')
        auc, per_auc, val_accuracy = validation_metrics(yv, logits)
        gc.collect()
        widths = width_snapshot(model)
        if state['recovery_frozen']:
            assert raw_widths(model) == state['freeze_widths'], 'Frozen activation grids moved'
        # [D20] regime B: the budget, feasibility and every selection below exist only on a
        # traced epoch; an untraced epoch is validated and logged, never a candidate.
        budget_met = cost['total'] <= final_target if traced else None
        feasible = budget_met if traced else False
        point = {'epoch': epoch, 'val_macro_auc': auc,
                 'val_categorical_accuracy': val_accuracy, 'ebops': cost['total']}
        if rule is not None and not traced:
            above_floor = nondegenerate = None
        elif rule is not None:
            # [ND, arbiter v3 fix 1] feasible = budget met AND above the 0-bit floor AND above the majority rule.
            above_floor = cost['total'] - rule['zero_floor_ebops']
            nondegenerate = above_floor > 0 and val_accuracy > rule['val_accuracy_threshold']
            feasible = budget_met and nondegenerate
            point['ebops_above_floor'] = above_floor
            if budget_met and not nondegenerate:
                state['feasible_degenerate_epochs'] += 1
                if state['first_feasible_degenerate'] is None:
                    state['first_feasible_degenerate'] = point
        if not np.isfinite(auc):
            record_divergence(out, cfg, state, epoch, 'nonfinite validation AUC',
                              {'loss': loss, 'train_categorical_accuracy': accuracy,
                               'val_categorical_accuracy': val_accuracy}, wandb_run)
            raise Diverged('Nonfinite validation AUC')
        if traced and (state['lowest'] is None or cost['total'] < state['lowest']['ebops']):
            shutil.copy2(candidate, out / 'model_min_ebops.keras')
            state['lowest'] = point
        if traced and (state['best_auc'] is None or auc > state['best_auc']['val_macro_auc']):
            shutil.copy2(candidate, out / 'model_unconstrained.keras')
            state['best_auc'] = point
        previous = state['best_feasible']
        cost_first = cost_before_auc(cfg)
        if feasible and (previous is None or checkpoint_selection_key(point, selection_metric, cost_before_auc=cost_first) > checkpoint_selection_key(previous, selection_metric, cost_before_auc=cost_first)):
            shutil.copy2(candidate, out / 'model_best.keras')
            state['best_feasible'] = point
        # [A19] AUC-selected sensitivity copy: the feasible checkpoint with the highest
        # validation macro AUC (ties: lower EBOPs, earlier epoch). Never replaces model_best.
        if keep_auc_feasible(cfg) and feasible:
            prior = state.get('best_feasible_auc')
            if prior is None or checkpoint_selection_key(point, 'val_macro_auc') > checkpoint_selection_key(prior, 'val_macro_auc'):
                shutil.copy2(candidate, out / 'model_best_auc_feasible.keras')
                state['best_feasible_auc'] = point
        recovery_after = cfg['experiment'].get('recovery_after_epochs')
        if recovery_after is not None and epoch + 1 >= recovery_after and feasible and not state['recovery_frozen']:
            state.update(recovery_frozen=True, freeze_epoch=epoch + 1, freeze_widths=raw_widths(model))
            print(f'[recovery] freeze at end of epoch {epoch + 1}; Adam slots and LR preserved', flush=True)
        pid_held = pid_integral_mode is not None and not traced
        if pid_held:
            # option (c), untraced epoch: on_epoch_end is not called, so the PID never reads the
            # in-training EBOPs; it keeps the last traced value, the only number it steps on.
            assert pid._ebops == state['pid']['ebops'], \
                ('BetaPID EBOPs moved on an untraced epoch', pid._ebops, state['pid']['ebops'])
        else:
            pid.on_epoch_end(epoch, {})
        if traced:
            last_trace = cost['total']
        if d20 and traced:
            # [D20] BetaPID reads the stored layer.ebops at on_epoch_end, which the trace
            # above wrote last: the PID is driven by the traced EBOPs, the same number the
            # feasibility test uses. Enforced here, not left to call order.
            assert abs(pid._ebops - cost['total']) <= 1e-6 * max(cost['total'], 1), \
                ('BetaPID EBOPs differs from the traced EBOPs', pid._ebops, cost['total'])
        elif d20 and not pid_held:
            # [D20] regime B, untraced epoch: no trace ran, so the PID reads the in-training
            # EBOPs of the last training step (the number jsc150's FreeEBOPs logs).
            assert pid._ebops == in_training_ebops, \
                ('BetaPID EBOPs differs from the in-training EBOPs', pid._ebops, in_training_ebops)
        state['pid'] = {'beta': pid.beta, 'ebops': pid._ebops,
                        'integral': pid.pid.integral, 'prev_error': pid.pid.prev_error}
        elapsed = time.monotonic() - start
        state['train_seconds'] += elapsed
        state['completed_epochs'] = epoch + 1
        free = [np.asarray(w['bits']).ravel() for w in widths.values() if w['width_trainable']]
        logs = {'epoch': epoch, 'ebops': cost['total'], 'target_ebops': final_target,
                'training_target_ebops': pid.target_ebops, 'budget_met': int(feasible),
                'beta': pid.beta, 'learning_rate': lr, 'val_macro_auc': auc,
                'loss': loss, 'task_loss': ce, 'distillation_loss': kd, 'categorical_accuracy': accuracy,
                'train_categorical_accuracy': accuracy, 'val_categorical_accuracy': val_accuracy,
                'activation_bits_mean': float(np.mean(np.concatenate(free))),
                'recovery_frozen': int(state['recovery_frozen']), 'epoch_seconds': elapsed,
                **{f'val_auc_{i}': v for i, v in enumerate(per_auc)}}
        if rule is not None and traced:
            logs.update(ebops_budget_met=int(budget_met), ebops_above_floor=above_floor,
                        nondegenerate=int(nondegenerate), feasible_degenerate=int(budget_met and not nondegenerate),
                        val_accuracy_threshold=rule['val_accuracy_threshold'])
        elif rule is not None:
            logs.update(ebops_budget_met=None, ebops_above_floor=None, nondegenerate=None,
                        feasible_degenerate=None, val_accuracy_threshold=rule['val_accuracy_threshold'])
        if d20:
            logs.update(ebops_in_training=in_training_ebops, pid_ebops=float(pid._ebops),
                        ebops_in_training_over_traced=in_training_ebops / max(cost['total'], 1),
                        ebops_trace_rows=int(len(trace_rows)),
                        # [D20] the trace's share of s_e, measured by every run (canary included)
                        ebops_trace_seconds=trace_seconds, ebops_reload_check_seconds=reload_check_seconds,
                        ebops_trace_over_epoch=(trace_seconds + reload_check_seconds) / max(elapsed, 1e-9))
        if pid_integral_mode is not None:
            logs.update(pid_stepped=int(pid_stepped), pid_step_span=int(pid_span),
                        pid_integral=float(pid.pid.integral))
        if trace_every is not None:
            # [D20] regime B: `ebops` and `budget_met` are traced quantities; null on an
            # untraced epoch (the in-training value is `ebops_in_training`).
            logs['ebops_traced'] = int(traced)
            if not traced:
                logs.update(ebops=None, budget_met=None, ebops_in_training_over_traced=None)
        if epoch_observer is not None:
            diagnostics = epoch_observer(model, sample, epoch)
            if set(diagnostics) & set(logs):
                raise ValueError('Epoch observer cannot replace training metrics')
            logs.update(diagnostics)
        for name, width in widths.items():
            logs[f'activation_bits/{name}'] = float(np.mean(width['bits']))
        record = {**logs, 'widths': widths, 'per_layer': cost['per_layer'], 'best_feasible': state['best_feasible']}
        with (out / 'activation_widths.jsonl').open('a') as f:
            f.write(json.dumps(record, allow_nan=False) + '\n')
            f.flush()
            os.fsync(f.fileno())
        if pid_integral_mode is not None:
            append_jsonl(out / PID_TELEMETRY, pid_telemetry_row(
                epoch, stepped=pid_stepped, span=pid_span, pid_input=pid_input, pid_error_value=pid_err,
                integral=pid.pid.integral, prev_error=pid.pid.prev_error, beta_after_step=beta_after_step,
                beta_end=pid.beta, target=pid.target_ebops, ebops_in_training=in_training_ebops,
                traced=traced, ebops_traced=cost['total'] if traced else None,
                pid_ebops_end=pid._ebops, learning_rate=lr,
                monitor={'loss': loss, 'val_categorical_accuracy': val_accuracy, 'val_macro_auc': auc,
                         'budget_met': None if not traced else int(budget_met),
                         'feasible': None if not traced else int(feasible),
                         'ebops_above_floor': above_floor if rule is not None else None,
                         'nondegenerate': None if rule is None or nondegenerate is None else int(nondegenerate),
                         'val_accuracy_threshold': rule['val_accuracy_threshold'] if rule is not None else None,
                         **attention_summary(widths, cost['per_layer'] if traced else None)}))
        # [A15] Full (model + optimizer + PID + selection) checkpoint every
        # `experiment.checkpoint_every_epochs` (absent => 1, the historical cadence), and
        # always at a pause (stop_after) and at the last epoch. The per-epoch candidate
        # save, reload, validation and feasibility test above are unchanged.
        pause = stop_after is not None and epoch + 1 >= stop_after
        every = int(cfg['experiment'].get('checkpoint_every_epochs', 1))
        saved = None
        if (epoch + 1) % every == 0 or epoch + 1 == epochs or pause:
            saved = save_checkpoint(out, model, optimizer, state)
        # [A6] boundary snapshot: best-feasible-as-of-E files plus state, never rewritten.
        snapshot_every = cfg['experiment'].get('snapshot_every_epochs')
        if snapshot_every and (epoch + 1) % int(snapshot_every) == 0:
            assert saved is not None, 'snapshot_every_epochs must be a multiple of checkpoint_every_epochs'
            save_snapshot(out, state)
        floor_text = '' if rule is None or not traced else f" above_floor={above_floor} feasible={int(feasible)} degenerate={int(budget_met and not nondegenerate)}"
        ebops_text = cost['total'] if traced else f"untraced in_training_ebops={cost['total']}"
        # physics v9 B2: under [D20] the line carries the s_e split and the train loss, so the
        # canary can be read from the arm log without W&B.
        d20_text = '' if not d20 else (f" ebops_trace_seconds={trace_seconds:.2f}"
                                       f" ebops_trace_over_epoch={logs['ebops_trace_over_epoch']:.3f} loss={loss:.6f}")
        if rss_gate is not None:
            rss = rss_gate_step(rss_gate, cfg['name'], out)
            d20_text += f" host_rss_mb={rss:.0f}" if rss is not None else ' host_rss_mb=na'
        print(f"[epoch {epoch + 1}/{epochs}] EBOPs={ebops_text} target={final_target}{floor_text} beta={pid.beta:.3g} val_AUC={auc:.6f} val_accuracy={val_accuracy:.6f} seconds={elapsed:.1f} checkpoint={saved.name if saved else '-'}{d20_text}", flush=True)
        if wandb_run:
            import wandb
            wandb_run.log(logs if trace_every is None else {k: v for k, v in logs.items() if v is not None},
                          step=epoch + 1)
            wandb_run.summary.update(training_status_summary(state, selection_metric, stop_after))
            if saved is not None and (epoch + 1) % cfg['experiment']['remote_every_epochs'] == 0:
                from .wandb_util import log_files_artifact
                log_files_artifact(wandb_run, name='resume-' + cfg['name'], type='checkpoint', files=[str(saved)], metadata={'completed_epochs': epoch + 1})
        if stop_after is not None and epoch + 1 >= stop_after:
            if wandb_run:
                wandb_run.summary.update(training_status_summary(state, selection_metric, stop_after, paused=True))
                wandb_run.finish()
            return state
    binary_gate(model, cfg)
    selected = state['best_feasible'] or state['lowest']
    filename = 'model_best.keras' if state['best_feasible'] else 'model_min_ebops.keras'
    delivered = keras.models.load_model(out / filename, compile=False)
    measured = traced_ebops(delivered)
    assert measured['total'] == selected['ebops']
    binary_gate(delivered, cfg)
    result = {'initial_ebops': state['initial_ebops'], 'target_ebops': final_target,
              'checkpoint': filename, 'checkpoint_ebops': measured['total'],
              'checkpoint_widths': width_snapshot(delivered), 'selected': selected,
              'best_feasible': state['best_feasible'], 'budget_met': measured['total'] <= final_target,
              'selection_metric': selection_metric,
              'selection': ('minimum_ebops_no_feasible_checkpoint' if state['best_feasible'] is None
                            else 'max_auc_under_final_budget' if selection_metric == 'val_macro_auc'
                            else 'max_accuracy_under_final_budget'),
              'code_sha256': state['code_sha256']}
    if rule is not None:
        result.update(feasibility_rule='nondegenerate (arbiter v3 fix 1)', nondegenerate_rule=rule,
                      checkpoint_ebops_above_floor=measured['total'] - rule['zero_floor_ebops'],
                      feasible_degenerate_epochs=state['feasible_degenerate_epochs'],
                      first_feasible_degenerate=state['first_feasible_degenerate'])
    if d20:
        result['i_decay_speed'] = state.get('i_decay_speed')
    if keep_auc_feasible(cfg):
        result['auc_selected_feasible'] = state.get('best_feasible_auc')
        result['auc_selected_checkpoint'] = ('model_best_auc_feasible.keras'
                                             if state.get('best_feasible_auc') else None)
    atomic_json(out / 'ebops_budget.json', result)
    meta = {'config': cfg['name'], 'seed': seed, 'epochs_run': state['completed_epochs'],
            'params': model.count_params(), 'best_epoch': selected['epoch'],
            'best_val_macro_auc': selected['val_macro_auc'], 'ebops_budget': result,
            'selected_val_categorical_accuracy': selected.get('val_categorical_accuracy'),
            'train_seconds': state['train_seconds'], 'freeze_epoch': state['freeze_epoch'],
            'n_train': len(xt), 'n_val': len(xv), 'data_sha256': state['data_sha256'], 'jit_compile': False}
    atomic_json(out / 'train_meta.json', meta)
    if wandb_run:
        from .wandb_util import log_files_artifact
        wandb_run.summary.update({'checkpoint_ebops': measured['total'], 'budget_met': result['budget_met'],
                                 'completed_epochs': state['completed_epochs'], 'phase': 'complete',
                                 'selection_metric': selection_metric,
                                 'selected_val_categorical_accuracy': selected.get('val_categorical_accuracy'),
                                 'best_val_macro_auc': selected['val_macro_auc'], 'epochs_run': state['completed_epochs']})
        files = [str(out / n) for n in (filename, 'model_unconstrained.keras', 'train_meta.json', 'ebops_budget.json', 'config.json', 'input_std.json', 'data_info.json', 'initialization.json', 'activation_widths.jsonl')]
        if (out / PID_TELEMETRY).exists():
            files.append(str(out / PID_TELEMETRY))
        log_files_artifact(wandb_run, name='model-' + seeded_run_name(cfg['name'], seed), type='model', files=list(dict.fromkeys(files)), metadata=meta)
        wandb_run.finish()
    atomic_json(out / 'COMPLETE.json', meta)
    return state
