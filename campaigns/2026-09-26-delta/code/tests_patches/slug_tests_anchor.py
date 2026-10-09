"""Per-slug CPU tests on the ANCHOR tree (chang0926 bundle 77f1ca4e + patches-anchor).

usage: pyenv.sh slug_tests_anchor.py --tree <apply_anchor.sh build>/code --out results.json [--only name ...]

Two groups:
  * the 13 slugs that exist only in patches-anchor (0025-0037): a mechanism unit test, then on
    both anchor shapes under the Chang quantizers (arm A = E: d24/h2/L1/FFN32/no PE; arm A07-350:
    d32/h4/L1/FFN32; [A20] WRAP datalanes + learned softmax, [D25] i_decay_speed 1e-3), each keyed
    config validates, builds through the runner's builder (run_engram.builder_for), passes the
    binary gate, runs one epoch of >= 2 optimizer steps, passes the post-step binary gate, and
    reloads within atol 1e-7 before and after the step;
  * the rebase decisions of 0012 / 0014 / 0023 / 0024 on the anchor code paths ([A15] 25-epoch
    checkpoint cadence, [A6] snapshots, 0025 verify_selected, [A2] adam_default, [A20] WRAP).
The arm configs are the anchor's generated files, unmodified except: train.batch 256 and a
512-jet synthetic sample (CPU time; shapes unchanged), and train.epochs for mini runs.
Synthetic inputs only (mu 0, sigma 1); nothing here is a result.
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
import tempfile
import time
import traceback
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import slug_tests as T  # noqa: E402  (helpers: build, reload_check, synth, with_keys, one_step, refused)

TESTS = {}
SHAPES = {'E (arm A)': 'chang0926-a-n64-s1.json', 'A07-350': 'chang0926-a07-350-n64-s1.json'}


def test(name):
    def wrap(fn):
        TESTS[name] = fn
        return fn
    return wrap


def arm(file):
    cfg = json.loads((T.CTX['tree'] / 'campaigns' / 'chang0926' / 'configs' / file).read_text())
    cfg['train']['batch'] = 256
    return cfg


def on_shapes(keys, check=None, gate=True):
    """keys: dotted '__' kwargs for with_keys. Build, gate, reload, one epoch (2 steps), gate,
    reload, on both anchor shapes. check(model, cfg, shape) adds slug-specific asserts."""
    ablation = T.CTX['ablation']
    facts = {}
    for shape, file in SHAPES.items():
        cfg = T.with_keys(arm(file), **keys)
        xt, yt = T.synth(cfg)
        model, ev = T.build(cfg, xt)
        if gate:
            ablation.binary_gate(model, cfg)
        extra = check(model, cfg, shape) if check else {}             # on the built state (before any trace)
        ebops = ablation.compute_ebops(model, xt[:256])['total']
        _, rel0 = T.reload_check(model, xt)
        metrics, _ = T.one_step(model, cfg, xt, yt)                  # includes the post-step binary gate
        assert np.isfinite(metrics).all(), metrics
        _, rel1 = T.reload_check(model, xt)
        facts[shape] = {'params': model.count_params(), 'initial_ebops_synthetic': ebops,
                        'reload_max_abs_diff_init': rel0['reload_max_abs_diff'],
                        'reload_max_abs_diff_after_step': rel1['reload_max_abs_diff'],
                        'epoch_metrics': metrics, **(extra or {})}
    return facts


def must_refuse(cfg, fragment):
    msg = T.refused(cfg)
    assert msg and fragment in msg, (fragment, msg)
    return msg[-100:]


# --------------------------------------------------------------------------- #
@test('pt-gate-threshold')
def t_pt_gate():
    from bnhgq2.data import apply_pt_gate
    a = arm(SHAPES['E (arm A)'])
    facts = {'zero_refused': must_refuse(T.with_keys(a, arch__pt_gate_gev=0), 'arch.pt_gate_gev')}
    assert T.refused(T.with_keys(a, arch__pt_gate_gev=None)) is None
    assert T.refused(T.with_keys(a, arch__pt_gate_gev=2.0)) is None
    x = np.abs(np.random.default_rng(0).normal(0, 3, (4, 8, 3))).astype('float32')
    assert np.array_equal(apply_pt_gate(x, ['pt', 'etarel', 'phirel'], None), x)
    gated = apply_pt_gate(x, ['pt', 'etarel', 'phirel'], 2.0)
    assert np.array_equal(gated[x[..., 0] < 2.0], np.zeros_like(gated[x[..., 0] < 2.0]))
    facts.update(on_shapes({'arch__pt_gate_gev': None}))
    return facts


@test('softmax-table-min-bits')
def t_table_min_bits():
    from bnhgq2.ebops_target import activation_quantizers

    def check(model, cfg, shape):
        floor = cfg['quant'].get('softmax_table_min_bits', 4)
        tables = [q for n, q in activation_quantizers(model) if n.endswith(('__exp_oq', '__inv_oq'))]
        assert tables
        for q in tables:
            projected = np.asarray(q._b.constraint(q._b * 0.0 - 5.0))    # a step that pushes b down
            assert np.all(projected == floor), (shape, projected, floor)
        return {'tables': len(tables), 'b_floor_after_push': floor}
    facts = {'default_floor_4': on_shapes({}, check)['E (arm A)']['b_floor_after_push']}
    facts.update(on_shapes({'quant__softmax_table_min_bits': 2}, check))
    fixed = T.with_keys(arm(SHAPES['E (arm A)']), quant__softmax_table_min_bits=2)
    fixed['quant']['softmax_quant'] = 'fixed'
    facts['fixed_softmax_refused'] = must_refuse(fixed, 'softmax_quant')
    return facts


@test('lr-schedule-variants')
def t_lr_warmup():
    ablation = T.CTX['ablation']
    a = arm(SHAPES['E (arm A)'])
    w = T.with_keys(a, train__lr_warmup_epochs=10)
    got = {e: ablation.learning_rate(w, e) for e in (0, 4, 9, 10, 489, 490, 499, 500)}
    ref = {e: ablation.learning_rate(a, e) for e in got}
    for e in got:
        want = ref[e] * (e + 1) / 10 if e < 10 else ref[e]
        assert got[e] == want, (e, got[e], want)
    m = T.with_keys(a, train__lr_m_mul=0.85)                         # M031: anchor key, no Delta code
    alpha = a['train']['lr_alpha']                                   # lr = alpha + m_mul**c (lr_c - alpha)
    assert np.isclose(ablation.learning_rate(m, 500), alpha + 0.85 * (ablation.learning_rate(a, 500) - alpha))
    must_refuse(T.with_keys(a, train__lr_warmup_epochs=500), 'lr_warmup_epochs')
    facts = {'lr_at': got, 'anchor_lr_at': ref}
    facts.update(on_shapes({'train__lr_warmup_epochs': 10}))
    return facts


@test('act-init-f0')
def t_act_f0():
    from bnhgq2.ebops_target import activation_quantizers
    ref_i = {}
    for shape, file in SHAPES.items():                                  # calibrated i without the key
        base = T.with_keys(arm(file))
        ref, _ = T.build(base, T.synth(base)[0])
        ref_i[shape] = {n: q._i.numpy() for n, q in activation_quantizers(ref) if q.trainable and hasattr(q, '_f')}

    def check(model, cfg, shape):
        free = [(n, q) for n, q in activation_quantizers(model) if q.trainable and hasattr(q, '_f')]
        assert free and all(np.all(q._f.numpy() == 7.0) for _, q in free)
        assert all(np.array_equal(q._i.numpy(), ref_i[shape][n]) for n, q in free), 'i must stay as calibrated'
        return {'quantizers_f0_7': len(free)}
    return on_shapes({'quant__act_f0': 7}, check)


@test('act-granularity-element')
def t_element():
    from bnhgq2.ebops_target import activation_quantizers

    def check(model, cfg, shape):
        q = dict(activation_quantizers(model))
        n_part, d = cfg['arch']['n_part'], cfg['arch']['d_model']
        wq = q['bit_block_0_attn_Wq']._f.shape
        assert tuple(wq)[-2:] == (n_part, d), wq                      # one width per (position, channel)
        s0 = q['bit_block_0_attn_scores__in0']._f.shape
        assert tuple(s0)[-3:] == (n_part, cfg['arch']['n_heads'], d // cfg['arch']['n_heads']), s0
        return {'Wq_width_shape': list(wq), 'q_stream_width_shape': list(s0)}
    return on_shapes({'quant__act_granularity': 'element'}, check)


@test('ebops-group-weight')
def t_group_weight():
    ablation = T.CTX['ablation']
    from hgq.utils.sugar import BetaPID
    facts = {}
    for shape, file in SHAPES.items():
        cfg = T.with_keys(arm(file), quant__ebops_group_weight={'attention': 0.1, 'rest': 1.0})
        xt, _ = T.synth(cfg)
        model, _ = T.build(cfg, xt)
        pid = BetaPID(**cfg['train']['ebops']['pid'])
        pid.set_model(model)
        ablation.group_weighted_beta(pid, model, cfg['quant']['ebops_group_weight'])
        pid.set_beta(1e-6)
        seen = {}
        for layer in model.layers:
            for sub in layer._flatten_layers():
                if getattr(sub, '_beta', None) is not None:
                    want = 1e-7 if ablation.ATTENTION_GROUP.match(layer.name) else 1e-6
                    assert np.isclose(float(sub._beta.numpy()), want, rtol=1e-6), (layer.name, float(sub._beta.numpy()))
                    seen[ablation.ATTENTION_GROUP.match(layer.name) is not None] = True
        assert seen.get(True) and seen.get(False)
        loss = float(sum(float(l) for l in model.losses)) if model.losses else 0.0
        facts[shape] = {'resource_loss_after_set_beta': loss}
    state, out, _, _ = T.mini_train(T.with_keys(arm(SHAPES['E (arm A)']),
                                                quant__ebops_group_weight={'attention': 0.1}), epochs=2)
    facts['mini_train_epochs'] = state['completed_epochs']
    facts.update(on_shapes({'quant__ebops_group_weight': {'attention': 0.1, 'rest': 1.0}}))
    return facts


@test('qk-stream-min-bits')
def t_qk_min_bits():
    qat = T.CTX['qat']

    def check(model, cfg, shape):
        qs = qat.qk_stream_quantizers(model)
        assert len(qs) == 2 * cfg['arch']['n_layers']
        for q in qs:
            assert np.all(q._i.numpy() + q._f.numpy() >= 1 - 1e-6)
            q._f.assign(np.full(q._f.shape, -30.0, 'float32'))        # push the widths down
        return {'qk_quantizers': len(qs)}

    def after(model, cfg):
        for q in qat.qk_stream_quantizers(model):
            assert np.all(q._i.numpy() + q._f.numpy() >= 1 - 1e-6), 'floor not re-imposed after the step'
    facts = {}
    for shape, file in SHAPES.items():
        cfg = T.with_keys(arm(file), quant__qk_min_bits=1)
        xt, yt = T.synth(cfg)
        model, _ = T.build(cfg, xt)
        facts[shape] = check(model, cfg, shape)
        T.one_step(model, cfg, xt, yt)
        after(model, cfg)
        v = model.get_layer('bit_block_0_attn_ctx').iq[1].quantizer
        facts[shape]['v_stream_untouched'] = not any(v is q for q in qat.qk_stream_quantizers(model))
    facts.update(on_shapes({'quant__qk_min_bits': 1}))
    return facts


@test('pre-quant-shift')
def t_pre_shift():
    import tensorflow as tf
    # forward equals the unshifted build at init, and the gradient reaches the shift
    cfg0 = T.with_keys(arm(SHAPES['E (arm A)']))
    xt, yt = T.synth(cfg0)
    base, _ = T.build(cfg0, xt)
    base_pred = np.asarray(base(xt[:32], training=False))
    cfg = T.with_keys(arm(SHAPES['E (arm A)']), quant__pre_quant_shift='channel')
    model, _ = T.build(cfg, xt)
    np.testing.assert_array_equal(np.asarray(model(xt[:32], training=False)), base_pred)
    with tf.GradientTape() as tape:
        loss = tf.reduce_mean(tf.nn.softmax_cross_entropy_with_logits(yt[:64], model(xt[:64], training=True)))
    grad = tape.gradient(loss, model.get_layer('input_proj_pqshift').shift)
    assert grad is not None and np.any(np.asarray(grad) != 0)
    facts = {'init_forward_equals_unshifted': True, 'gradient_reaches_shift': True}

    def check(model, cfg, shape):
        shifts = [ly for ly in model.layers if ly.name.endswith('_pqshift')]
        assert shifts and all(np.all(ly.shift.numpy() == 0) for ly in shifts)
        return {'shift_layers': len(shifts)}
    facts.update(on_shapes({'quant__pre_quant_shift': 'channel'}, check))
    return facts


@test('attn-linformer')
def t_linformer():
    def check(model, cfg, shape):
        e = model.get_layer('bit_block_0_attn_Elin')
        assert tuple(e._kernel.shape) == (cfg['arch']['n_part'], 8)
        assert tuple(model.get_layer('bit_block_0_attn_softmax').output.shape)[-1] == 8
        return {'scores_last_dim': 8}
    facts = on_shapes({'arch__attn_kind': 'linformer', 'arch__linformer_k': 8}, check)
    export = T.CTX['delta_keys'].export_blockers(T.with_keys(arm(SHAPES['E (arm A)']),
                                                             arch__attn_kind='linformer', arch__linformer_k=8))
    assert any('arch.attn_kind' in b for b in export)
    facts['export_refused'] = export
    return facts


@test('std-real-slots')
def t_std_real():
    from bnhgq2.data import input_std_stats, input_std_stats_real_slots, apply_pt_gate
    rng = np.random.default_rng(5)
    x = np.abs(rng.normal(0, 5, (50, 16, 3))).astype('float32')
    x[..., 1:] = rng.normal(0, 1, (50, 16, 2)).astype('float32')
    x = apply_pt_gate(x, ['pt', 'etarel', 'phirel'], 2.0)
    real = x[x[..., 0] != 0]
    mu, sigma = input_std_stats_real_slots(x, ['pt', 'etarel', 'phirel'])
    np.testing.assert_allclose(mu, real.mean(0), rtol=1e-6)
    np.testing.assert_allclose(sigma, real.std(0), rtol=1e-6)
    mu_all, _ = input_std_stats(x)
    assert not np.allclose(mu, mu_all)
    facts = {'n_real_slots': int(len(real)), 'n_slots': int(x.shape[0] * x.shape[1]),
             'mu_real': mu.tolist(), 'mu_all': mu_all.tolist()}
    facts.update(on_shapes({'data__std_scope': 'real_slots'}))            # model side unchanged
    return facts


@test('derived-input-features')
def t_derived():
    from bnhgq2.data import derive_features, apply_pt_gate
    feats = ['pt', 'etarel', 'phirel']
    x = np.array([[[4.0, 0.3, -0.4], [1.0, 0.1, 0.1], [0.0, 0.0, 0.0]]], 'float32')
    g = apply_pt_gate(x, feats, 2.0)
    d = derive_features(g, feats, ['log_pt', 'delta_r'])
    assert d.shape == (1, 3, 5)
    np.testing.assert_allclose(d[0, 0, 3:], [np.log(4.0), 0.5], rtol=1e-6)
    assert np.all(d[0, 1:, 3:] == 0)                                     # gated and padded slots
    flipped = g.copy(); flipped[..., 1:] *= -1
    np.testing.assert_array_equal(derive_features(flipped, feats, ['log_pt', 'delta_r'])[..., 3:], d[..., 3:])
    keys = {'arch__n_feat': 5, 'arch__derived_features': ['log_pt', 'delta_r']}
    facts = on_shapes(keys)
    must_refuse(T.with_keys(arm(SHAPES['E (arm A)']), arch__derived_features=['log_pt', 'delta_r']), 'n_feat')
    facts['hand_example'] = d[0, 0].tolist()
    return facts


@test('gated-key-mask')
def t_mask():
    keras = T.CTX['keras']

    def check(model, cfg, shape):
        xt, _ = T.synth(cfg, n=16, seed=3)
        xt[:, 40:, 0] = 0.0                                              # pad value for mu 0, sigma 1
        probe = keras.Model(model.inputs, model.get_layer('bit_block_0_attn_softmax').output)
        attn = np.asarray(probe(xt, training=False))
        assert np.all(attn[..., 40:] == 0.0), 'masked keys must get exactly 0 attention'
        assert np.all(attn[..., :40].sum(-1) > 0)
        return {'masked_attention_max': float(attn[..., 40:].max()), 'unmasked_row_sum_min': float(attn[..., :40].sum(-1).min())}
    facts = on_shapes({'arch__mask_gated_keys': True}, check)
    # no gated slot in the input -> forward equals the unmasked build
    cfg = T.with_keys(arm(SHAPES['E (arm A)']), arch__mask_gated_keys=True)
    xt, _ = T.synth(cfg)
    base, _ = T.build(T.with_keys(arm(SHAPES['E (arm A)'])), xt)
    want = np.asarray(base(xt[:32], training=False))
    model, _ = T.build(cfg, xt)
    np.testing.assert_array_equal(np.asarray(model(xt[:32], training=False)), want)
    facts['no_gated_slot_forward_equal'] = True
    try:
        T.CTX['ablation'].matching_initialization(cfg, xt, 1)
        raise AssertionError('mask built without input_std')
    except ValueError:
        facts['needs_input_std'] = True
    return facts


@test('attn-relu-over-n')
def t_relu():
    keras = T.CTX['keras']
    from bnhgq2.ebops_target import activation_quantizers

    def check(model, cfg, shape):
        n = cfg['arch']['n_part']
        xt, _ = T.synth(cfg, n=8, seed=4)
        sc = keras.Model(model.inputs, model.get_layer('bit_block_0_attn_scores').output)(xt)
        at = keras.Model(model.inputs, model.get_layer('bit_block_0_attn_relu_over_n').output)(xt)
        np.testing.assert_array_equal(np.asarray(at), np.maximum(np.asarray(sc), 0) * np.float32(1.0 / n))
        assert not any(name.endswith(('__exp_oq', '__inv_oq', '__exp_iq', '__inv_iq')) for name, _ in activation_quantizers(model))
        return {'n_is_power_of_two': n & (n - 1) == 0}
    facts = on_shapes({'arch__attn_kind': 'relu_over_n'}, check)
    fixed = T.with_keys(arm(SHAPES['E (arm A)']), arch__attn_kind='relu_over_n')
    fixed['quant']['softmax_quant'] = 'fixed'
    facts['fixed_softmax_refused'] = must_refuse(fixed, 'softmax_quant')
    return facts


# ---- rebase decisions on the anchor code paths ----------------------------------------- #
@test('rebase-0012-latent-ema-cadence')
def t_ema_cadence():
    """[A15] checkpoint every 25 epochs: a pause (stop_after) commits a leaf with the EMA shadow;
    the resume restores it and the run completes; the candidate carries EMA latents."""
    keras = T.CTX['keras']
    cfg = T.with_keys(arm(SHAPES['E (arm A)']), experiment__latent_ema_decay=0.9)
    assert cfg['experiment']['checkpoint_every_epochs'] == 25
    out = Path(tempfile.mkdtemp(prefix='delta-ema-anchor-'))
    T.mini_train(cfg, epochs=3, out=out, stop_after=1)
    leaf1 = out / 'checkpoints' / json.loads((out / 'latest.json').read_text())['checkpoint']
    assert (leaf1 / 'latent_ema.npz').exists()
    state, out, _, _ = T.mini_train(cfg, epochs=3, out=out)
    assert state['completed_epochs'] == 3
    leaf = out / 'checkpoints' / json.loads((out / 'latest.json').read_text())['checkpoint']
    shadow = dict(np.load(leaf / 'latent_ema.npz'))
    cand = keras.models.load_model(out / 'validation_candidate.keras', compile=False)
    for key, value in shadow.items():
        np.testing.assert_array_equal(cand.get_layer(key.split('__')[0])._kernel.numpy(), value)
    return {'leaves': sorted(p.name for p in (out / 'checkpoints').iterdir()), 'completed': 3}


@test('rebase-0014-collapse-cadence')
def t_collapse_cadence():
    """Collapse under the 25-epoch cadence: the collapse epoch is committed (forced checkpoint),
    a re-invocation does not train on, and run_study.verify_selected reports verified_collapsed."""
    import run_study
    rule = {'threshold': 0.99, 'patience': 2, 'after_epoch': 1}
    cfg = T.with_keys(arm(SHAPES['E (arm A)']), experiment__collapse_stop=rule)
    out = Path(tempfile.mkdtemp(prefix='delta-collapse-anchor-'))
    state, out, arrays, info = T.mini_train(cfg, epochs=6, out=out)
    assert state['collapsed']['epoch'] == 3 and state['completed_epochs'] == 3
    leaf = json.loads((out / 'latest.json').read_text())['checkpoint']
    assert leaf == 'epoch-0003', leaf
    state2, _, _, _ = T.mini_train(cfg, epochs=6, out=out)
    assert state2['completed_epochs'] == 3
    run_cfg = copy.deepcopy(cfg); run_cfg['train'].update(epochs=6, warmup_epochs=0, decay_epochs=0)
    info = {**info, 'array_sha256': {'y_val': 'synthetic'}}
    report = run_study.verify_selected(run_cfg, {'name': cfg['name']}, out, state2, arrays, info,
                                       {'sha256': 'synthetic'}, time.monotonic())
    assert report['status'] == 'verified_collapsed' and (out / 'VERIFIED_COMPLETE.json').exists()
    return {'collapsed_epoch': 3, 'committed_leaf': leaf, 'verify_selected_status': report['status']}


@test('rebase-0024-bop-adam-default')
def t_bop_adam_default():
    ablation = T.CTX['ablation']
    cfg = T.with_keys(arm(SHAPES['E (arm A)']), train__binary_optimizer='bop', train__bop_gamma=1e-4, train__bop_tau=1e-8)
    assert cfg['train']['optimizer'] == 'adam_default'
    xt, yt = T.synth(cfg)
    model, _ = T.build(cfg, xt)
    opt = ablation.delta_optimizer_for(cfg, model)
    assert type(opt).__name__ == 'BopAdam' and opt.beta_2 == 0.999 and opt.weight_decay is None and opt.clipvalue is None
    plain, _ = T.build(T.with_keys(arm(SHAPES['E (arm A)'])), xt)
    assert len(opt.variables) == len(ablation.optimizer_for(arm(SHAPES['E (arm A)']), plain).variables)
    model, _ = T.build(cfg, xt)
    metrics, _ = T.one_step(model, cfg, xt, yt)
    out = Path(tempfile.mkdtemp(prefix='delta-bop-anchor-'))
    T.mini_train(cfg, epochs=2, out=out, stop_after=1)
    state, _, _, _ = T.mini_train(cfg, epochs=2, out=out)
    assert state['completed_epochs'] == 2
    return {'optimizer': 'BopAdam(adam_default)', 'beta_2': 0.999, 'resumed_to_epoch': 2, 'epoch_metrics': metrics}


@test('rebase-0023-deepsets-wrap')
def t_deepsets_wrap():
    ablation = T.CTX['ablation']
    cfg = T.with_keys(arm(SHAPES['E (arm A)']), arch__body='deepsets')
    cfg['arch']['pos_enc'] = 'none'
    xt, yt = T.synth(cfg)
    model, _ = T.build(cfg, xt)
    decay = ablation.i_decay_speeds(model)
    assert decay and set(decay.values()) == {float(np.float32(1e-3))}
    from bnhgq2.ebops_target import activation_quantizers
    modes = {getattr(q, 'overflow_mode', None) for _, q in activation_quantizers(model)}
    ablation.binary_gate(model, cfg)
    metrics, _ = T.one_step(model, cfg, xt, yt)
    _, rel = T.reload_check(model, xt)
    return {'params': model.count_params(), 'i_decay_quantizers': len(decay), 'overflow_modes': sorted(map(str, modes)),
            'reload_max_abs_diff': rel['reload_max_abs_diff']}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--tree', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--only', nargs='*')
    args = p.parse_args()
    sys.path.insert(0, str(args.tree))
    import run_engram
    ablation, _ = run_engram.runtime()
    import keras
    import tensorflow as tf
    from bnhgq2 import qat, delta_keys
    tf.config.experimental.enable_tensor_float_32_execution(False)
    T.CTX.update(tree=args.tree, ablation=ablation, keras=keras, qat=qat, delta_keys=delta_keys)
    results = json.loads(args.out.read_text()) if args.out.exists() else {}
    for name in args.only or list(TESTS):
        t0 = time.monotonic()
        try:
            facts = TESTS[name]()
            results[name] = {'status': 'PASS', 'seconds': round(time.monotonic() - t0, 1), **(facts or {})}
            print('ANCHOR_SLUG_TEST_PASS', name, 'seconds', results[name]['seconds'], flush=True)
        except Exception as exc:  # noqa: BLE001
            results[name] = {'status': 'FAIL', 'error': f'{type(exc).__name__}: {exc}',
                             'traceback': traceback.format_exc()[-2500:]}
            print('ANCHOR_SLUG_TEST_FAIL', name, results[name]['error'][:300], flush=True)
        args.out.write_text(json.dumps(results, indent=1, sort_keys=True, default=str) + '\n')
    bad = [k for k in (args.only or TESTS) if results[k]['status'] != 'PASS']
    print('ANCHOR_SLUG_TESTS_ALL_PASS' if not bad else f'ANCHOR_SLUG_TESTS_FAIL {bad}', flush=True)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
