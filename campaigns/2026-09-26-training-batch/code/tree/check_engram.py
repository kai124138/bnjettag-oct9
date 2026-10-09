"""Small deterministic correctness tests. Synthetic metrics are never science results."""
from __future__ import annotations

import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import keras
import numpy as np
import tensorflow as tf

from bnhgq2 import ablation, engram
from run_engram import (DEFAULT_BASE, builder_for, configs, default_spec, enforce_memory,
                        source_manifest, validate_tracking_destination, write_json)


def run_checks(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(712)
    n, t, d = 20, 4, 8
    x = rng.uniform(-1, 1, (n, t, 3)).astype('float32')
    x[..., 0] = rng.uniform(.05, 2, (n, t))
    x[:, -1] = 0  # real zero-padded constituents
    h = rng.normal(size=(n, t, d)).astype('float32')
    info = {'input_std': {'mu': [0., 0., 0.], 'sigma': [1., 1., 1.]}}
    passed = []
    for orders, gate, heads, slots in [([1], 'none', 1, 512), ([1], 'hard', 1, 512),
                                      ([2, 3], 'hard', 2, 257)]:
        spec = {**default_spec(), 'orders': orders, 'gate': gate, 'heads': heads, 'table_size': slots}
        tokenizer = engram.fit_tokenizer(x, info['input_std'], spec)
        layer = engram.JetEngram(spec, tokenizer)
        result = np.asarray(layer([h, x]))
        np.testing.assert_array_equal(result, h)  # exact baseline-preserving initialization
        ids, masks = layer.addresses(tf.constant(x))
        ref_ids, ref_masks = engram.address_numpy(x, tokenizer, spec)
        np.testing.assert_array_equal(ids, ref_ids)
        np.testing.assert_array_equal(masks, ref_masks)
        assert np.all(ref_ids >= 0) and np.all(ref_ids < slots)
        # Changing a previous jet cannot affect any address in the next jet.
        isolated_ids, isolated_masks = engram.address_numpy(x[1:2], tokenizer, spec)
        np.testing.assert_array_equal(isolated_ids[0], ref_ids[1])
        np.testing.assert_array_equal(isolated_masks[0], ref_masks[1])
        if orders == [2, 3]:
            assert not ref_masks[:, 0].any()
            assert not ref_masks[:, :2, 2:].any()
        layer.values.assign(rng.uniform(-.75, .75, layer.values.shape))
        output = np.asarray(layer([h, x]))
        np.testing.assert_array_equal(output[:, -1], h[:, -1])
        if orders == [1]:
            p = np.array([2, 0, 3, 1])
            np.testing.assert_allclose(layer([h[:, p], x[:, p]]), output[:, p], atol=1e-7)
        with tf.GradientTape() as tape:
            y = layer([tf.constant(h), tf.constant(x)])
            loss = tf.reduce_sum(tf.square(y))
        gradients = tape.gradient(loss, layer.trainable_variables)
        for variable, gradient in zip(layer.trainable_variables, gradients):
            assert gradient is not None, variable.name
            array = np.asarray(tf.convert_to_tensor(gradient))
            assert np.isfinite(array).all() and np.any(array != 0), variable.name
        hi, xi = keras.Input((t, d)), keras.Input((t, 3))
        model = keras.Model([hi, xi], layer([hi, xi]))
        with tempfile.TemporaryDirectory(dir=out) as directory:
            path = Path(directory) / 'model.keras'
            model.save(path)
            restored = keras.models.load_model(path, compile=False)
            np.testing.assert_array_equal(restored([h, x]), output)
        passed.append(f'address_reference_mask_gradient_serialization_{orders}_{gate}_{heads}')
        print(f'PASS {passed[-1]}', flush=True)

    # Exact bin threshold and round/saturation agreement, including ties and padding.
    spec = default_spec()
    tokenizer = engram.fit_tokenizer(x, info['input_std'], spec)
    edge_x = np.array(tokenizer['edges'], dtype='float32').T[None]
    layer = engram.JetEngram(spec, tokenizer)
    a, m = layer.addresses(tf.constant(edge_x))
    aa, mm = engram.address_numpy(edge_x, tokenizer, spec)
    np.testing.assert_array_equal(a, aa)
    np.testing.assert_array_equal(m, mm)
    probe = np.array([-100., -.1875, -.0625, .0625, .1875, 100.], dtype='float32')
    np.testing.assert_array_equal(engram.fixed_ste(tf.constant(probe), 4, 0), engram.fixed_np(probe, 4, 0))
    passed.append('round_to_even_saturation_bin_boundaries')

    # Verify an actual Adam step multiplier (not ineffective gradient rescaling),
    # and that zero gradients decay only the ordinary backbone variable.
    host = keras.layers.Layer(name='optimizer_probe')
    ordinary = host.add_weight(name='kernel', shape=(1,), initializer='ones')
    memory = engram.JetEngram(spec, tokenizer, name='jet_engram')
    memory([h, x])
    memory.values.assign(np.ones(memory.values.shape, dtype='float32'))
    opt = engram.MemoryAdam(learning_rate=.001, memory_lr_multiplier=5., weight_decay=.1)
    opt.build([ordinary, memory.values])
    opt.apply_gradients([(tf.zeros_like(ordinary), ordinary), (tf.zeros_like(memory.values), memory.values)])
    assert float(ordinary.numpy()[0]) < 1.
    np.testing.assert_array_equal(memory.values, 1.)
    before_o, before_m = ordinary.numpy().copy(), memory.values.numpy().copy()
    opt.weight_decay = 0.
    opt.apply_gradients([(tf.ones_like(ordinary), ordinary), (tf.ones_like(memory.values), memory.values)])
    np.testing.assert_allclose((before_m - memory.values.numpy()).mean(),
                              5 * (before_o - ordinary.numpy()).mean(), rtol=1e-3)
    passed.append('table_adam_lr_multiplier_and_no_weight_decay')

    base = json.loads(DEFAULT_BASE.read_text())
    # The screening plan itself must pass memory checks at its actual N=16, D=32.
    ledgers = {}
    for arm, _, cfg in configs(base, [1]):
        ledgers[arm] = enforce_memory(cfg, engram)
    passed.append('all_eight_production_configs_fit_declared_module_budgets')

    tiny = json.loads(DEFAULT_BASE.read_text())
    tiny['arch'].update(n_part=t, d_model=d, ffn_dim=8, n_heads=2)
    tiny['train'].update(epochs=2, batch=10, val_batch=10)
    tiny['train']['ebops']['pid'].update(target_ebops=1000000)
    all_cfg = {arm: cfg for arm, _, cfg in configs(tiny, [1])}
    from convert_binary import build_export
    try:
        build_export(all_cfg['e03'], None, None, None)
    except NotImplementedError:
        pass
    else:
        raise AssertionError('Exporter silently accepted unsupported memory')
    same_accuracy = {'val_categorical_accuracy': .7, 'val_macro_auc': .9, 'ebops': 100, 'epoch': 1}
    cheaper = {**same_accuracy, 'val_macro_auc': .8, 'ebops': 90}
    assert ablation.checkpoint_selection_key(cheaper, 'val_categorical_accuracy', cost_before_auc=True) > ablation.checkpoint_selection_key(same_accuracy, 'val_categorical_accuracy', cost_before_auc=True)
    assert ablation.checkpoint_selection_key(cheaper, 'val_categorical_accuracy') < ablation.checkpoint_selection_key(same_accuracy, 'val_categorical_accuracy')
    passed.append('engram_cost_tiebreak_legacy_order_preserved_and_export_rejected')
    y = np.eye(5, dtype='float32')[np.arange(n) % 5]
    arrays = (x, y, x.copy(), y.copy())
    try:
        ablation.run_training(all_cfg['e03'], arrays, info, out)
    except ValueError as error:
        assert 'memory builder' in str(error)
    else:
        raise AssertionError('Generic trainer silently dropped memory')
    info.update(n_train=n, n_val=n, train_sha256=ablation.array_hash(x),
                val_sha256=ablation.array_hash(x), synthetic=True)
    for arm, cfg in all_cfg.items():
        keras.backend.clear_session()
        model, evidence = builder_for(info)(cfg, x, 1)
        ablation.binary_gate(model, cfg)
        trace = ablation.compute_ebops(model, x)
        report = engram.accounting(model, trace)
        assert sum(trace['per_layer'].values()) == trace['total']
        assert report['native_hgq2_backbone_ebops'] > 0
        if cfg['engram_study']['module']:
            assert trace['per_layer']['jet_engram'] == report['custom_estimated_bitops']
            assert evidence['backbone_initial_output_identical']
            assert report['custom_estimated_bitops'] > 0
        else:
            assert report['custom_estimated_bitops'] == 0
        before_diagnostics = [v.numpy().copy() for v in model.weights]
        diagnostics = engram.diagnostic_observer()(model, x, 0)
        for before, variable in zip(before_diagnostics, model.weights):
            np.testing.assert_array_equal(before, variable)
        assert diagnostics['cost/custom_estimated_bitops'] == report['custom_estimated_bitops']
        if cfg['engram_study']['module'] and cfg['engram_study']['module']['gate'] == 'hard':
            assert 0 <= diagnostics['memory/gate_half_fraction'] <= 1
            assert np.isclose(sum(v for k, v in diagnostics.items() if k.startswith('memory/gate_hist_')), 1)
            assert diagnostics['memory/residual_nonzero_fraction'] == 0
        with tempfile.TemporaryDirectory(dir=out) as directory:
            path = Path(directory) / 'full.keras'
            model.save(path)
            loaded = keras.models.load_model(path, compile=False)
            np.testing.assert_array_equal(loaded(x), model(x))
        print(f'PASS {arm} build/binary/init/cost/reload', flush=True)
    passed.append('all_eight_arms_build_binary_initialization_cost_reload')
    passed.append('diagnostics_are_finite_nonmutating_and_show_initial_zero_residual')

    cfg = all_cfg['e03']
    with patch.dict(os.environ, {'WANDB_MODE': 'online',
                                'WANDB_ENTITY': cfg['engram_study']['wandb_entity'],
                                'WANDB_PROJECT': cfg['train']['wandb_project']}):
        validate_tracking_destination(cfg, fetch_project=lambda *args: {'access': 'PRIVATE'})
        for response in (None, {'access': 'PUBLIC'}, {'access': 'OPEN'}):
            try:
                validate_tracking_destination(cfg, fetch_project=lambda *args: response)
            except ValueError:
                pass
            else:
                raise AssertionError('Unverified/non-private tracking destination was accepted')
        os.environ['WANDB_PROJECT'] = 'BNJetTag-Batch20260918'
        try:
            validate_tracking_destination(cfg, fetch_project=lambda *args: {'access': 'PRIVATE'})
        except ValueError:
            pass
        else:
            raise AssertionError('Existing campaign accepted as tracking destination')
    passed.append('private_tracking_and_campaign_isolation_guards')

    # Real existing training loop, interrupted vs uninterrupted, including Adam/PID state.
    cfg = all_cfg['e03']
    with tempfile.TemporaryDirectory(dir=out) as directory:
        resumed, full = Path(directory) / 'resumed', Path(directory) / 'full'
        for path in (resumed, full):
            path.mkdir()
        builder = builder_for(info)
        ablation.run_training(cfg, arrays, info, resumed, stop_after=1, model_builder=builder,
                              epoch_observer=engram.diagnostic_observer())
        ablation.run_training(cfg, arrays, info, resumed, stop_after=2, model_builder=builder,
                              epoch_observer=engram.diagnostic_observer())
        ablation.run_training(cfg, arrays, info, full, stop_after=2, model_builder=builder,
                              epoch_observer=engram.diagnostic_observer())
        history = [json.loads(line) for line in (resumed / 'activation_widths.jsonl').read_text().splitlines()]
        assert len(history) == 2 and all('memory/gate_std' in point for point in history)
        rm, ro, rs = ablation.restore_checkpoint(resumed, cfg, info)
        fm, fo, fs = ablation.restore_checkpoint(full, cfg, info)
        np.testing.assert_allclose(rm(x), fm(x), rtol=1e-6, atol=1e-6)
        assert rs['completed_epochs'] == fs['completed_epochs'] == 2
        assert rs['pid'] == fs['pid']
        for rvar, fvar in zip(ro.variables, fo.variables):
            np.testing.assert_allclose(rvar, fvar, rtol=1e-6, atol=1e-7)
        wrong = dict(info, val_sha256='wrong')
        try:
            ablation.restore_checkpoint(resumed, cfg, wrong)
        except AssertionError:
            pass
        else:
            raise AssertionError('Resume accepted changed dataset provenance')
    passed.append('existing_trainer_resume_matches_uninterrupted_optimizer_pid_outputs')
    write_json(out / 'preflight.json', {'status': 'PASS', 'checks': passed,
                                       'source_manifest': source_manifest(),
                                       'production_module_estimates': ledgers,
                                       'data': 'synthetic only', 'accuracy_gain_measured': False,
                                       'hardware_validated': False})
    print(f'ENGRAM_PREFLIGHT_PASS: {out / "preflight.json"}', flush=True)


if __name__ == '__main__':
    raise SystemExit('Use: python run_engram.py preflight --out <directory>')
