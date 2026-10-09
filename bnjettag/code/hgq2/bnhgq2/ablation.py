"""Controlled, resumable 1000-epoch EBOPs ablations. TensorFlow backend only.

All arms use the same epoch-indexed data order. Recovery excludes only i/f from
Adam updates (including weight decay), without rebuilding/resetting its slots.
Checkpoints contain model, optimizer, PID, selection, freeze and epoch state.
"""
from __future__ import annotations
import copy
import hashlib
import json
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
    assert len(copied) >= 15, 'Expected matched binary-layer initialization'
    if cfg['quant']['act_granularity'] == 'channel':
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
                'kernel_hashes': {v.path: array_hash(v.numpy()) for v in model.weights
                                  if v.name in ('kernel', 'bias', 'pos_table')}}
    del reference
    return model, evidence


def learning_rate(cfg, epoch):
    tr = cfg['train']
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
    optimizer = keras.optimizers.Adam(learning_rate=tr['lr'], beta_1=.9, beta_2=tr['beta2'],
                                     weight_decay=tr['weight_decay'], clipvalue=tr['clipvalue'])
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
    for name in ('model_best.keras', 'model_min_ebops.keras', 'model_unconstrained.keras'):
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
    for name in ('model_best.keras', 'model_min_ebops.keras', 'model_unconstrained.keras'):
        target = out / name
        if (directory / name).exists():
            shutil.copyfile(directory / name, target)
        elif target.exists():
            target.unlink()
    history = out / 'activation_widths.jsonl'
    lines = history.read_text().splitlines() if history.exists() else []
    kept = [line for line in lines if json.loads(line)['epoch'] < state['completed_epochs']]
    assert len(kept) == state['completed_epochs'], 'Missing committed epoch history'
    history.write_text('\n'.join(kept) + ('\n' if kept else ''))
    return model, optimizer, state


def binary_gate(model):
    values = qat.effective_weight_values(model)
    assert len(values) == 15 and all(len(v) == 2 and not (v == 0).any() and np.isclose(v[0], -v[1]) for v in values.values()), 'Binary gate failed'


def run_training(cfg, arrays, data_info, out, *, teacher_logits=None, remote=False, stop_after=None):
    """stop_after is used only by checkpoint-interruption tests, never by real configs."""
    apply_keras_compat()
    seed = cfg['experiment']['seed']
    keras.utils.set_random_seed(seed)
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    xt, yt, xv, yv = arrays
    sample = xt[:256]
    resumed = restore_checkpoint(out, cfg, data_info)
    if resumed:
        model, optimizer, state = resumed
    else:
        if (out / 'activation_widths.jsonl').exists():
            raise RuntimeError('History exists without a committed checkpoint')
        model, initialization = matching_initialization(cfg, xt[:4096], seed)
        optimizer = optimizer_for(cfg, model)
        initial = compute_ebops(model, sample)
        state = {'config_sha256': digest_json(cfg), 'data_sha256': digest_json(data_info),
                 'code_sha256': os.environ.get('BNHGQ2_CODE_SHA256', 'local-check'),
                 'completed_epochs': 0, 'initial_ebops': initial['total'], 'initial_widths': width_snapshot(model),
                 'best_feasible': None, 'lowest': None, 'best_auc': None, 'recovery_frozen': False,
                 'freeze_epoch': None, 'freeze_widths': None, 'pid': None, 'train_seconds': 0.}
        atomic_json(out / 'initialization.json', initialization)
        atomic_json(out / 'config.json', cfg)
        atomic_json(out / 'data_info.json', data_info)
        atomic_json(out / 'input_std.json', data_info['input_std'])
    binary_gate(model)
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
    if cfg['experiment'].get('distillation'):
        assert teacher_logits is not None and teacher_logits.shape == yt.shape
    wandb_run = None
    if remote:
        import wandb
        from .wandb_util import init_kwargs
        run_id = hashlib.sha256(cfg['name'].encode()).hexdigest()[:12]
        wandb_run = wandb.init(**init_kwargs(name=cfg['name'] + '-s1', job_type='train',
                         cfg_project=cfg['train']['wandb_project'], group=cfg['experiment']['group'],
                         config={'experiment_config': cfg, 'data': data_info, 'code_sha256': state['code_sha256']}),
                         id=run_id, resume='allow')
    step = make_epoch_step(model, optimizer, xt, yt, cfg, teacher_logits)
    epochs = cfg['train']['epochs']
    for epoch in range(state['completed_epochs'], epochs):
        start = time.monotonic()
        lr = learning_rate(cfg, epoch)
        optimizer.learning_rate.assign(lr)
        pid.target_ebops = training_target(cfg, epoch)
        pid.on_epoch_begin(epoch, {})
        order = np.random.default_rng(np.random.SeedSequence([cfg['train']['order_seed'], epoch])).permutation(len(xt)).astype('int32')
        loss, ce, kd, accuracy = [float(v) for v in step(order, state['recovery_frozen']).numpy()]
        if not np.isfinite([loss, ce, kd, accuracy]).all():
            raise RuntimeError('Nonfinite training metrics')
        scores = _softmax(np.asarray(model.predict(xv, batch_size=cfg['train']['val_batch'], verbose=0)))
        auc, per_auc = macro_ovr_auc(yv, scores)
        cost = compute_ebops(model, sample)
        widths = width_snapshot(model)
        if state['recovery_frozen']:
            assert raw_widths(model) == state['freeze_widths'], 'Frozen activation grids moved'
        feasible = cost['total'] <= final_target
        point = {'epoch': epoch, 'val_macro_auc': auc, 'ebops': cost['total']}
        if not np.isfinite(auc):
            raise RuntimeError('Nonfinite validation AUC')
        if state['lowest'] is None or cost['total'] < state['lowest']['ebops']:
            model.save(out / 'model_min_ebops.keras')
            state['lowest'] = point
        if state['best_auc'] is None or auc > state['best_auc']['val_macro_auc']:
            model.save(out / 'model_unconstrained.keras')
            state['best_auc'] = point
        previous = state['best_feasible']
        if feasible and (previous is None or (auc, -cost['total'], -epoch) > (previous['val_macro_auc'], -previous['ebops'], -previous['epoch'])):
            model.save(out / 'model_best.keras')
            state['best_feasible'] = point
        recovery_after = cfg['experiment'].get('recovery_after_epochs')
        if recovery_after is not None and epoch + 1 >= recovery_after and feasible and not state['recovery_frozen']:
            state.update(recovery_frozen=True, freeze_epoch=epoch + 1, freeze_widths=raw_widths(model))
            print(f'[recovery] freeze at end of epoch {epoch + 1}; Adam slots and LR preserved', flush=True)
        pid.on_epoch_end(epoch, {})
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
                'activation_bits_mean': float(np.mean(np.concatenate(free))),
                'recovery_frozen': int(state['recovery_frozen']), 'epoch_seconds': elapsed,
                **{f'val_auc_{i}': v for i, v in enumerate(per_auc)}}
        for name, width in widths.items():
            logs[f'activation_bits/{name}'] = float(np.mean(width['bits']))
        record = {**logs, 'widths': widths, 'per_layer': cost['per_layer'], 'best_feasible': state['best_feasible']}
        with (out / 'activation_widths.jsonl').open('a') as f:
            f.write(json.dumps(record, allow_nan=False) + '\n')
            f.flush()
            os.fsync(f.fileno())
        saved = save_checkpoint(out, model, optimizer, state)
        print(f"[epoch {epoch + 1}/{epochs}] EBOPs={cost['total']} target={final_target} beta={pid.beta:.3g} AUC={auc:.6f} seconds={elapsed:.1f} checkpoint={saved.name}", flush=True)
        if wandb_run:
            import wandb
            wandb_run.log(logs, step=epoch + 1)
            if (epoch + 1) % cfg['experiment']['remote_every_epochs'] == 0:
                from .wandb_util import log_files_artifact
                log_files_artifact(wandb_run, name='resume-' + cfg['name'], type='checkpoint', files=[str(saved)], metadata={'completed_epochs': epoch + 1})
        if stop_after is not None and epoch + 1 >= stop_after:
            if wandb_run:
                wandb_run.finish()
            return state
    binary_gate(model)
    selected = state['best_feasible'] or state['lowest']
    filename = 'model_best.keras' if state['best_feasible'] else 'model_min_ebops.keras'
    delivered = keras.models.load_model(out / filename, compile=False)
    measured = compute_ebops(delivered, sample)
    assert measured['total'] == selected['ebops']
    binary_gate(delivered)
    result = {'initial_ebops': state['initial_ebops'], 'target_ebops': final_target,
              'checkpoint': filename, 'checkpoint_ebops': measured['total'],
              'checkpoint_widths': width_snapshot(delivered), 'selected': selected,
              'best_feasible': state['best_feasible'], 'budget_met': measured['total'] <= final_target,
              'selection': 'max_auc_under_final_budget', 'code_sha256': state['code_sha256']}
    atomic_json(out / 'ebops_budget.json', result)
    meta = {'config': cfg['name'], 'seed': seed, 'epochs_run': state['completed_epochs'],
            'params': model.count_params(), 'best_epoch': selected['epoch'],
            'best_val_macro_auc': selected['val_macro_auc'], 'ebops_budget': result,
            'train_seconds': state['train_seconds'], 'freeze_epoch': state['freeze_epoch'],
            'n_train': len(xt), 'n_val': len(xv), 'data_sha256': state['data_sha256'], 'jit_compile': False}
    atomic_json(out / 'train_meta.json', meta)
    if wandb_run:
        from .wandb_util import log_files_artifact
        wandb_run.summary.update({'checkpoint_ebops': measured['total'], 'budget_met': result['budget_met'],
                                 'best_val_macro_auc': selected['val_macro_auc'], 'epochs_run': state['completed_epochs']})
        files = [str(out / n) for n in (filename, 'model_unconstrained.keras', 'train_meta.json', 'ebops_budget.json', 'config.json', 'input_std.json', 'data_info.json', 'initialization.json', 'activation_widths.jsonl')]
        log_files_artifact(wandb_run, name='model-' + cfg['name'] + '-s1', type='model', files=list(dict.fromkeys(files)), metadata=meta)
        wandb_run.finish()
    atomic_json(out / 'COMPLETE.json', meta)
    return state
