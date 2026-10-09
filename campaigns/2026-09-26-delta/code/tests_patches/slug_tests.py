"""Per-slug CPU tests for the Delta patch series (tests a and c).

usage: pyenv.sh slug_tests.py --tree <patched .../code> --out results.json [--only slug ...]

(a) a unit test of each slug's mechanism; (c) one config with the key set (a delta on
const0922-a07-n64) builds through the S builder, passes its gate, and a saved model reloads
with predictions within atol 1e-7 (the 2e-6 preflight tolerance is reported beside it). Where
shapes allow, the init kernel_hashes are compared with the unkeyed a07-n64 build at the same
seed ([A17]-style pairing evidence). Synthetic inputs only; nothing here is a result.
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

TESTS = {}
CTX = {}


def slug(name):
    def wrap(fn):
        TESTS[name] = fn
        return fn
    return wrap


def base_cfg(short='a07-n64'):
    tree = CTX['tree']
    return json.loads((tree / 'configs' / f'const0922-{short}-s1-fast50-fp32.json').read_text())


def with_keys(cfg, **dotted):
    cfg = copy.deepcopy(cfg)
    for key, value in dotted.items():
        node = cfg
        parts = key.split('__')
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    cfg['name'] = cfg['name'] + '-delta-test'
    return cfg


def synth(cfg, n=512, seed=0):
    rng = np.random.default_rng(seed)
    T, F = cfg['arch']['n_part'], cfg['arch']['n_feat']
    xt = rng.standard_normal((n, T, F)).astype('float32')
    yt = np.eye(cfg['arch']['n_classes'], dtype='float32')[rng.integers(0, cfg['arch']['n_classes'], n)]
    return xt, yt


def build(cfg, xt, seed=1):
    import run_engram
    run_engram.validate_cfg(cfg)
    info = {'input_std': {'mu': [0.] * cfg['arch']['n_feat'], 'sigma': [1.] * cfg['arch']['n_feat']}}
    CTX['keras'].backend.clear_session()
    return run_engram.builder_for(info)(cfg, xt, seed)


def reload_check(model, xt):
    keras = CTX['keras']
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / 'm.keras'
        model.save(path)
        loaded = keras.models.load_model(path, compile=False)
    a = np.asarray(model(xt[:32], training=False))
    b = np.asarray(loaded(xt[:32], training=False))
    diff = float(np.max(np.abs(a - b)))
    assert np.isfinite(a).all() and diff <= 1e-7, f'reload max|diff| {diff} > 1e-7'
    return loaded, {'reload_max_abs_diff': diff, 'within_1e-7': diff <= 1e-7, 'within_2e-6': diff <= 2e-6}


def base_hashes():
    if 'base_hashes' not in CTX:
        cfg = base_cfg()
        xt, _ = synth(cfg)
        _, ev = build(cfg, xt)
        CTX['base_hashes'] = ev['kernel_hashes']
    return CTX['base_hashes']


def pairing(evidence):
    base = base_hashes()
    mine = evidence['kernel_hashes']
    common = sorted(set(base) & set(mine))
    same = [k for k in common if base[k] == mine[k]]
    return {'kernel_hash_paths_equal_to_base': len(same), 'kernel_hash_paths_common': len(common),
            'kernel_hash_paths_differing': sorted(set(common) - set(same)),
            'paths_only_here': sorted(set(mine) - set(base)), 'paths_only_in_base': sorted(set(base) - set(mine))}


def keyed_build(cfg, gate='binary'):
    """Test (c): build, gate, one forward, save -> reload."""
    ablation = CTX['ablation']
    xt, yt = synth(cfg)
    model, ev = build(cfg, xt)
    if gate == 'binary':
        ablation.binary_gate(model, cfg)
    ebops = ablation.compute_ebops(model, xt[:256])['total']
    _, rel = reload_check(model, xt)
    return model, ev, xt, yt, {'params': model.count_params(), 'initial_ebops_synthetic': ebops, **rel}


def one_step(model, cfg, xt, yt, **kw):
    ablation = CTX['ablation']
    opt = ablation.optimizer_for(cfg, model)
    opt.learning_rate.assign(ablation.learning_rate(cfg, 0))
    step = ablation.make_epoch_step(model, opt, xt, yt, cfg, **kw)
    order = np.random.default_rng(1).permutation(len(xt)).astype('int32')
    assert len(xt) >= 2 * int(cfg['train']['batch']), 'post-step gate needs >= 2 optimizer steps'
    metrics = [float(v) for v in step(order, False).numpy()]
    ablation.binary_gate(model, cfg)          # post-step gate on the deployed (quantized) kernels
    return metrics, opt


# --------------------------------------------------------------------------- #
@slug('binarizer-center-flag')
def t_center():
    import tensorflow as tf
    qat = CTX['qat']
    from bnhgq2.binarize import absmean_binarize
    w = np.random.default_rng(3).normal(0.3, 1.0, (6, 5)).astype('float32')
    out = np.asarray(qat.bitnet_binary_ste(tf.constant(w), center=False))
    beta = np.abs(w).mean() + 1e-6
    np.testing.assert_allclose(out, np.where(w >= 0, 1., -1.) * beta, rtol=1e-6)
    q, b, alpha, _ = absmean_binarize(w, center=False)
    assert alpha == 0.0 and np.isclose(b, beta) and np.array_equal(q, np.sign(w))
    centered = np.asarray(qat.bitnet_binary_ste(tf.constant(w)))
    assert not np.allclose(centered, out), 'center flag had no effect'
    cfg = with_keys(base_cfg(), quant__binary_center=False)
    model, ev, xt, yt, facts = keyed_build(cfg)
    layer = model.get_layer('input_proj')
    k = layer._kernel.numpy()
    np.testing.assert_allclose(np.asarray(layer.qkernel), np.where(k >= 0, 1., -1.) * (np.abs(k).mean() + 1e-6), rtol=1e-6)
    metrics, _ = one_step(model, cfg, xt, yt)
    return {**facts, **pairing(ev), 'post_step_gate': True}


def _grad(fn, w, g):
    import tensorflow as tf
    wv = tf.Variable(w)
    with tf.GradientTape() as tape:
        out = fn(wv)
        loss = tf.reduce_sum(out * g)
    return np.asarray(out), np.asarray(tape.gradient(loss, wv))


@slug('ste-variants')
def t_ste():
    qat = CTX['qat']
    rng = np.random.default_rng(4)
    w = rng.normal(0.0, 1.5, (8, 6)).astype('float32')     # some |wc| > 1 on purpose
    g = rng.normal(0.0, 1.0, w.shape).astype('float32')
    wc = w - w.mean()
    beta = np.abs(wc).mean() + 1e-6
    q = np.where(wc >= 0, 1., -1.)
    n = w.size
    P = lambda v: v - v.mean()
    beta_term = (g * q).sum() / n * (np.sign(wc) - np.sign(wc).mean())
    facts = {}
    # bounded (default): d/dw = P(g) + beta term
    out, gr = _grad(lambda v: qat.bitnet_binary_ste(v), w, g)
    np.testing.assert_allclose(out, q * beta, rtol=1e-6)
    np.testing.assert_allclose(gr, P(g) + beta_term, atol=1e-5)
    # clip_identity: forward q*beta; d/dw = P(g * 1{|wc|<=1}); no beta path
    out, gr = _grad(lambda v: qat.bitnet_binary_ste(v, ste='clip_identity'), w, g)
    np.testing.assert_allclose(out, q * beta, rtol=1e-6)
    mask = (np.abs(wc) <= 1).astype('float32')
    np.testing.assert_allclose(gr, P(g * mask), atol=1e-5)
    facts['clip_identity_zero_grad_fraction'] = float(1 - mask.mean())
    # ede at three temperatures: d/dw = P(g*k*t*sech^2(t*ws)) + beta term
    for t in (0.1, 1.0, 10.0):
        qat.ede_temperature().assign(t)
        out, gr = _grad(lambda v: qat.bitnet_binary_ste(v, ste='ede'), w, g)
        np.testing.assert_allclose(out, q * beta, rtol=1e-6)
        ws = wc / beta
        k = max(1 / t, 1.0)
        np.testing.assert_allclose(gr, P(g * k * t / np.cosh(t * ws) ** 2) + beta_term, atol=1e-4)
    # schedule: restarts every period; period = horizon anneals once
    at = qat.ede_temperature_at
    assert np.isclose(at(0, 500), 0.1) and np.isclose(at(500, 500), 0.1) and np.isclose(at(1000, 500), 0.1)
    assert np.isclose(at(250, 500), 1.0) and at(499, 500) < 10.0 and at(499, 500) > 9.8
    assert np.isclose(at(3500, 7000), 1.0) and np.isclose(at(500, 7000), 0.1 * 10 ** (2 * 500 / 7000))
    facts['ede_t_epoch_0_250_499_500_period500'] = [at(e, 500) for e in (0, 250, 499, 500)]
    # validator
    import run_engram
    bad = with_keys(base_cfg(), quant__ste='ede', quant__ste_ede_period='=horizon')
    try:
        run_engram.validate_cfg(bad)
        raise AssertionError('"=horizon" string accepted')
    except ValueError as exc:
        facts['validator_rejects_horizon_string'] = str(exc)[-80:]
    # (c) keyed builds + epoch hook sets t
    for variant in ('clip_identity', 'ede'):
        extra = {'quant__ste_ede_period': 500} if variant == 'ede' else {}
        cfg = with_keys(base_cfg(), quant__ste=variant, **extra)
        model, ev, xt, yt, f = keyed_build(cfg)
        assert model.get_layer('bit_block_0_attn_Wq').binary == {'ste': variant}
        metrics, _ = one_step(model, cfg, xt, yt)
        assert np.isfinite(metrics).all()
        facts[variant] = {**f, **pairing(ev)}
    qat.set_delta_epoch(cfg, 250)
    assert np.isclose(float(qat.ede_temperature().numpy()), 1.0)
    return facts


def binary_layers(model):
    qat = CTX['qat']
    return [ly for ly in model.layers if isinstance(ly, (qat.BitQEinsumDense, qat.BitQDense))]


@slug('latent-clip')
def t_latent_clip():
    c = 0.05                     # tight on purpose so the synthetic step must clip
    cfg = with_keys(base_cfg(), quant__latent_clip=c)
    model, ev, xt, yt, facts = keyed_build(cfg)
    before = {ly.name: float(np.abs(ly._kernel.numpy()).max()) for ly in binary_layers(model)}
    assert max(before.values()) > c, 'init already inside the clip; test would be vacuous'
    metrics, _ = one_step(model, cfg, xt, yt)
    after = {ly.name: float(np.abs(ly._kernel.numpy()).max()) for ly in binary_layers(model)}
    assert all(v <= c + 1e-7 for v in after.values()), after
    return {**facts, **pairing(ev), 'max_abs_latent_before': max(before.values()),
            'max_abs_latent_after_step': max(after.values()), 'epoch_metrics': metrics}


def export_parity(model):
    """binarize.py (export math) vs the QAT forward, per binary layer."""
    from bnhgq2.binarize import binarize_checkpoint
    layers = {}
    for ly in binary_layers(model):
        layers[ly.name] = {'kernel': ly._kernel.numpy(), 'bias': None, 'binary': dict(ly.binary)}
        if hasattr(ly, 'beta_log2'):
            layers[ly.name]['beta_log2'] = float(ly.beta_log2.numpy())
        if hasattr(ly, 'channel_gain_log2'):
            layers[ly.name]['channel_gain_log2'] = ly.channel_gain_log2.numpy()
    binz = binarize_checkpoint(layers, norm='none')
    worst = 0.0
    for ly in binary_layers(model):
        b = binz[ly.name]
        eff = b['q'] * b['beta'] * (b['gain'] if b.get('gain') is not None else 1.0)
        worst = max(worst, float(np.max(np.abs(eff - np.asarray(ly.qkernel)))))
    assert worst <= 1e-6 * max(1.0, worst), worst
    assert binz['_summary']['total_sign_zeros'] == 0
    return worst


@slug('beta-mode')
def t_beta_mode():
    import tensorflow as tf
    qat = CTX['qat']
    rng = np.random.default_rng(5)
    w = rng.normal(0.0, 0.2, (8, 6)).astype('float32')
    g = rng.normal(0.0, 1.0, w.shape).astype('float32')
    out, gr = _grad(lambda v: qat.bitnet_binary_ste(v, beta_mode='absmean_pow2'), w, g)
    beta = np.abs(w - w.mean()).mean() + 1e-6
    p2 = 2.0 ** np.round(np.log2(np.float32(beta)))
    assert set(np.unique(np.abs(out))) == {np.float32(p2)}, np.unique(out)
    assert np.isfinite(gr).all() and np.abs(gr).sum() > 0
    s = tf.Variable(-2.3)
    wv = tf.Variable(w)
    with tf.GradientTape() as tape:
        out2 = qat.bitnet_binary_ste(wv, beta_mode='learned_pow2', beta_log2=s)
        loss = tf.reduce_sum(out2 * g)
    ds, dw = tape.gradient(loss, [s, wv])
    q = np.where(w - w.mean() >= 0, 1., -1.)
    np.testing.assert_allclose(np.asarray(out2), q * 0.25, rtol=0)          # 2^round(-2.3) = 1/4
    np.testing.assert_allclose(float(ds), np.log(2) * 0.25 * float((g * q).sum()), rtol=1e-5)
    facts = {'absmean_pow2_value': float(p2)}
    for mode in ('absmean_pow2', 'learned_pow2'):
        cfg = with_keys(base_cfg(), quant__beta_mode=mode)
        model, ev, xt, yt, f = keyed_build(cfg)
        values = qat.effective_weight_values(model)
        exps = sorted({float(np.log2(abs(v[1]))) for v in values.values()})
        assert all(e == int(e) for e in exps), exps
        if mode == 'learned_pow2':
            ly = model.get_layer('input_proj')
            k = ly._kernel.numpy().astype('float64')
            assert np.isclose(float(ly.beta_log2.numpy()), np.log2(np.abs(k - k.mean()).mean() + 1e-6), atol=1e-6)
            names = [v.path for v in model.trainable_variables if v.name == 'beta_log2']
            assert len(names) == len(values), names
        metrics, _ = one_step(model, cfg, xt, yt)
        assert np.isfinite(metrics).all()
        facts[mode] = {**f, **pairing(ev), 'log2_beta_values': exps, 'export_parity_max_abs': export_parity(model)}
    return facts


def base_predictions(xt):
    if 'base_pred' not in CTX:
        cfg = base_cfg()
        model, _ = build(cfg, xt)
        CTX['base_pred'] = np.asarray(model(xt[:32], training=False))
    return CTX['base_pred']


@slug('channel-gain-pow2')
def t_channel_gain():
    import tensorflow as tf
    qat, ablation = CTX['qat'], CTX['ablation']
    facts = {}
    for layers in (['input_proj'], 'all_binary'):
        cfg = with_keys(base_cfg(), quant__channel_gain={'layers': layers, 'mode': 'pow2'})
        model, ev, xt, yt, f = keyed_build(cfg)
        pred = np.asarray(model(xt[:32], training=False))
        same_as_base = bool(np.array_equal(pred, base_predictions(xt)))
        gained = [ly for ly in binary_layers(model) if hasattr(ly, 'channel_gain_log2')]
        assert [ly.name for ly in gained] == (['input_proj'] if layers != 'all_binary' else [ly.name for ly in binary_layers(model)])
        rng = np.random.default_rng(6)
        for ly in gained:
            s = ly.channel_gain_log2
            s.assign(rng.integers(-2, 3, s.shape).astype('float32') + rng.uniform(-0.3, 0.3, s.shape).astype('float32'))
        ablation.binary_gate(model, cfg)                       # per-channel gate passes
        per_tensor = qat.effective_weight_values(model)
        assert max(len(v) for k, v in per_tensor.items() if k in {g.name for g in gained}) > 2
        chans = qat.channel_weight_values(model)
        ly = gained[0]
        k = ly._kernel.numpy().astype('float64')
        beta = np.abs(k - k.mean()).mean() + 1e-6
        expect = 2.0 ** np.round(ly.channel_gain_log2.numpy().ravel()) * beta
        got = np.array([np.abs(c).max() for c in chans[ly.name]])
        one_sign = sum(len(c) == 1 for c in chans[ly.name])
        # the gate must reject a third value or a zero in a channel
        bad = copy.deepcopy(chans)
        bad[ly.name][0] = np.array([-1.0, 0.5, 1.0])
        values_ok = lambda cs: all(len(v) in (1, 2) and not (v == 0).any() and np.allclose(np.abs(v), np.abs(v[0])) for c in cs.values() for v in c)
        assert values_ok(chans) and not values_ok(bad)
        np.testing.assert_allclose(got, expect, rtol=1e-6)
        with tf.GradientTape() as tape:
            loss = tf.reduce_sum(model(xt[:16], training=True) ** 2)
        grads = tape.gradient(loss, [g.channel_gain_log2 for g in gained])
        one_step(model, cfg, xt, yt)                        # 2 optimizer steps, then the per-channel gate
        assert all(gr is not None and float(tf.reduce_sum(tf.abs(gr))) > 0 for gr in grads)
        _, rel = reload_check(model, xt)
        facts[str(layers)] = {**f, **pairing(ev), 'init_forward_bitwise_equal_to_base': same_as_base,
                              'channels_checked_input_proj': len(chans['input_proj']),
                              'one_sign_channels_first_layer': int(one_sign),
                              'per_tensor_values_after_gain_input_proj': int(len(per_tensor['input_proj'])),
                              'reload_after_gain': rel, 'export_parity_max_abs': export_parity(model)}
        assert same_as_base, 'gain 1 at init must leave the forward unchanged'
    return facts


def mini_train(cfg, epochs=2, n_train=512, n_val=256, out=None, **kw):
    """ablation.run_training for a few epochs on synthetic arrays (CPU; never a result)."""
    ablation = CTX['ablation']
    cfg = copy.deepcopy(cfg)
    cfg['train'].update(epochs=epochs, warmup_epochs=0, decay_epochs=0)
    xt, yt = synth(cfg, n_train, seed=0)
    xv, yv = synth(cfg, n_val, seed=9)
    info = {'input_std': {'mu': [0.] * cfg['arch']['n_feat'], 'sigma': [1.] * cfg['arch']['n_feat'],
                          'computed_from': 'synthetic'}, 'synthetic': True}
    import run_engram
    CTX['keras'].backend.clear_session()
    out = Path(out or tempfile.mkdtemp(prefix='delta-mini-'))
    state = ablation.run_training(cfg, (xt, yt, xv, yv), info, out,
                                  model_builder=run_engram.builder_for(info), **kw)
    return state, out, (xt, yt, xv, yv), info


def history(out):
    return [json.loads(line) for line in (out / 'activation_widths.jsonl').read_text().splitlines()]


@slug('weight-scheme-baselines')
def t_weight_schemes():
    qat = CTX['qat']
    facts = {}
    cfg = with_keys(base_cfg(), quant__weight='none')
    model, ev, xt, yt, f = keyed_build(cfg)
    assert not binary_layers(model) and not qat.effective_weight_values(model)
    state, out, _, _ = mini_train(cfg, epochs=1)
    rec = history(out)[-1]
    assert rec['activation_bits_mean'] is None and (out / 'COMPLETE.json').exists()
    facts['fp32'] = {**f, **pairing(ev), 'mini_train_epochs': state['completed_epochs'],
                     'ebops_after_epoch': rec['ebops']}
    cfg = with_keys(base_cfg(), quant__layer_weight_override={'input_proj': 'int8_absmax'})
    model, ev, xt, yt, f = keyed_build(cfg)
    ly = model.get_layer('input_proj')
    assert type(ly).__name__ == 'QEinsumDense' and 'input_proj' not in qat.effective_weight_values(model)
    kbits = np.unique(np.asarray(ly.kq.bits_(tuple(ly._kernel.shape))))
    assert list(kbits) == [8.0], kbits
    assert len(qat.effective_weight_values(model)) == 8
    metrics, _ = one_step(model, cfg, xt, yt)
    facts['int8_input_proj'] = {**f, **pairing(ev), 'input_proj_weight_bits': kbits.tolist(), 'epoch_metrics': metrics}
    cfg = with_keys(base_cfg(), quant__weight='int8_absmax')
    model, ev, xt, yt, f = keyed_build(cfg)
    facts['int8_all'] = {**f, **pairing(ev)}
    import run_engram
    try:
        run_engram.validate_cfg(with_keys(base_cfg(), quant__layer_weight_override={'input_proj': 'ternary'}))
        raise AssertionError('bad override accepted')
    except ValueError:
        pass
    return facts


def make_teacher(tag='teacher-fp32-test', mu=0.0, shape_cfg=None):
    """A float (quant.weight none) A07-shaped model with scrambled weights, saved as an
    artifact <root>/<tag>/model.keras + input_std.json. A stand-in, not a trained teacher."""
    import os
    root = Path(CTX.setdefault('artifact_root', tempfile.mkdtemp(prefix='delta-artifacts-')))
    os.environ['BNHGQ2_ARTIFACT_ROOT'] = str(root)
    cfg = with_keys(shape_cfg or base_cfg(), quant__weight='none')
    xt, _ = synth(cfg)
    model, _ = build(cfg, xt, seed=7)
    rng = np.random.default_rng(8)
    for v in model.weights:
        if v.name in ('kernel', 'bias', 'pos_table'):
            v.assign(rng.normal(0, 0.3, v.shape).astype('float32'))
    (root / tag).mkdir(parents=True, exist_ok=True)
    model.save(root / tag / 'model.keras')
    (root / tag / 'input_std.json').write_text(json.dumps({'mu': [mu] * 3, 'sigma': [1.] * 3}))
    return tag, {v.path: v.numpy() for v in model.weights if v.name in ('kernel', 'bias', 'pos_table')}


@slug('init-from-checkpoint')
def t_init_ckpt():
    ablation = CTX['ablation']
    tag, teacher = make_teacher()
    cfg = with_keys(base_cfg(), experiment__init_checkpoint=tag)
    model, ev, xt, yt, f = keyed_build(cfg)
    student = {v.path: v.numpy() for v in model.weights if v.name in ('kernel', 'bias', 'pos_table')}
    assert set(student) <= set(teacher)
    for path, value in student.items():
        np.testing.assert_array_equal(value, teacher[path], err_msg=path)
    state, out, _, _ = mini_train(cfg, epochs=1)
    init = json.loads((out / 'initialization.json').read_text())
    assert init['init_checkpoint_artifact']['sha256'] and len(init['init_checkpoint']['copied_paths']) == len(student)
    bad_tag, _ = make_teacher('teacher-bad-std', mu=0.5)
    try:
        mini_train(with_keys(base_cfg(), experiment__init_checkpoint=bad_tag), epochs=1)
        raise AssertionError('mismatched input_std accepted')
    except ValueError as exc:
        assert 'input_std' in str(exc)
    p = pairing(ev)
    return {**f, 'kernel_hash_paths_equal_to_base': p['kernel_hash_paths_equal_to_base'],
            'all_student_latents_equal_teacher': True, 'copied_paths': len(student),
            'std_mismatch_refused': True, 'mini_train_epochs': state['completed_epochs']}


def _kd_np(t_logits, s_logits, T):
    ls = lambda z: z - np.log(np.exp(z - z.max(-1, keepdims=True)).sum(-1, keepdims=True)) - z.max(-1, keepdims=True)
    tl, sl = ls(t_logits / T), ls(s_logits / T)
    return T ** 2 * float(np.mean(np.sum(np.exp(tl) * (tl - sl), axis=-1)))


@slug('kd-unblock-s-runner')
def t_kd_unblock():
    ablation, keras = CTX['ablation'], CTX['keras']
    tag, _ = make_teacher()
    kd = {'teacher_artifact': tag, 'temperature': 2, 'coefficient': 0.5}
    cfg = with_keys(base_cfg(), experiment__distillation=kd)
    model, ev, xt, yt, f = keyed_build(cfg)
    teacher = keras.models.load_model(ablation.resolve_artifact(tag)[0], compile=False)
    x1, y1 = xt[:256], yt[:256]                       # one batch: the reported kd is pre-update
    s_logits = np.asarray(model(x1, training=True))
    t_logits = np.asarray(teacher(x1, training=False))
    expect = _kd_np(t_logits.astype('float64'), s_logits.astype('float64'), 2.0)
    opt = ablation.optimizer_for(cfg, model)
    step = ablation.make_epoch_step(model, opt, x1, y1, cfg, teacher_model=teacher)
    loss, ce, kd_val, acc = [float(v) for v in step(np.arange(256, dtype='int32'), False).numpy()]
    assert abs(kd_val - expect) < 1e-4 * max(1, expect), (kd_val, expect)
    state, out, _, _ = mini_train(cfg, epochs=1)
    rec = history(out)[-1]
    assert rec['distillation_loss'] > 0 and (out / 'teacher_artifact.json').exists()
    import run_engram
    for bad in ({'teacher_artifact': '', 'temperature': 2, 'coefficient': 0.5}, {'teacher_artifact': tag, 'temperature': 2}):
        try:
            run_engram.validate_cfg(with_keys(base_cfg(), experiment__distillation=bad))
            raise AssertionError(f'accepted {bad}')
        except ValueError:
            pass
    return {**f, **{k: v for k, v in pairing(ev).items() if k.startswith('kernel_hash_paths_equal')},
            'kd_step_value': kd_val, 'kd_numpy_value': expect, 'mini_train_distillation_loss': rec['distillation_loss']}


@slug('kd-attention-map')
def t_kd_attention():
    import tensorflow as tf
    ablation, keras = CTX['ablation'], CTX['keras']
    tag, _ = make_teacher()
    kd = {'teacher_artifact': tag, 'temperature': 2, 'coefficient': 0.0, 'attention_coefficient': 1.0}
    cfg = with_keys(base_cfg(), experiment__distillation=kd, experiment__init_checkpoint=tag)
    model, ev, xt, yt, f = keyed_build(cfg)
    teacher = keras.models.load_model(ablation.resolve_artifact(tag)[0], compile=False)
    x1, y1 = xt[:256], yt[:256]
    maps = [ly.name for ly in model.layers if ly.name.endswith('_attn_softmax')]
    sp = keras.Model(model.inputs, [model.outputs[0]] + [model.get_layer(n).output for n in maps])
    tp = keras.Model(teacher.inputs, [teacher.outputs[0]] + [teacher.get_layer(n).output for n in maps])
    logits = model(x1, training=True)
    res_direct = float(tf.add_n(model.losses))
    out = sp(x1, training=True)
    res_probe = float(tf.add_n(model.losses))
    assert res_direct == res_probe, (res_direct, res_probe)
    np.testing.assert_array_equal(np.asarray(out[0]), np.asarray(logits))
    t_maps = [np.asarray(m, 'float64') for m in tp(x1, training=False)[1:]]
    s_maps = [np.asarray(m, 'float64') for m in out[1:]]
    att = np.mean([np.mean(np.sum(t * (np.log(np.maximum(t, 1e-9)) - np.log(np.maximum(s, 1e-9))), -1)) for t, s in zip(t_maps, s_maps)])
    ce = float(np.mean(-np.sum(np.asarray(y1, 'float64') * (np.asarray(logits, 'float64') - np.log(np.exp(np.asarray(logits, 'float64')).sum(-1, keepdims=True))), -1)))
    opt = ablation.optimizer_for(cfg, model)
    step = ablation.make_epoch_step(model, opt, x1, y1, cfg, teacher_model=teacher)
    loss, ce_s, kd_s, _ = [float(v) for v in step(np.arange(256, dtype='int32'), False).numpy()]
    expect = ce + res_direct + att
    assert abs(loss - expect) < 1e-4 * max(1, abs(expect)), (loss, expect)
    assert att > 0
    state, outdir, _, _ = mini_train(cfg, epochs=1)
    return {**f, 'model_losses_equal_direct_vs_probe': True, 'attention_kl_numpy': float(att),
            'step_loss': loss, 'expected_loss': expect, 'attention_maps': len(maps),
            'mini_train_epochs': state['completed_epochs']}


@slug('augment-eta-phi-reflect')
def t_augment():
    ablation = CTX['ablation']
    std = {'mu': [1.3, 0.02, -0.01], 'sigma': [2.0, 0.1, 0.12]}
    cfg = with_keys(base_cfg(), data__augment={'reflect_eta': True, 'reflect_phi': True})
    plain = base_cfg()
    xt, yt = synth(cfg, 256)
    order = np.arange(256, dtype='int32')
    rng = np.random.default_rng(11)
    signs = rng.choice(np.array([-1., 1.], 'float32'), size=(256, 2))
    # manual reflection in raw space
    raw = xt * np.array(std['sigma'], 'float32') + np.array(std['mu'], 'float32')
    raw[..., 1] *= signs[:, None, 0]
    raw[..., 2] *= signs[:, None, 1]
    manual = ((raw - np.array(std['mu'], 'float32')) / np.array(std['sigma'], 'float32')).astype('float32')
    runs = {}
    for label, c, x, sg in (('aug', cfg, xt, signs), ('manual', plain, manual, None),
                            ('aug_all_plus', cfg, xt, np.ones_like(signs)), ('plain', plain, xt, None)):
        model, _ = build(c, xt)
        opt = ablation.optimizer_for(c, model)
        step = ablation.make_epoch_step(model, opt, x, yt, c, input_std=std)
        runs[label] = [float(v) for v in (step(order, False, sg) if sg is not None else step(order, False)).numpy()]
    np.testing.assert_allclose(runs['aug'], runs['manual'], rtol=2e-5, atol=2e-6)
    assert runs['aug_all_plus'] == runs['plain'], (runs['aug_all_plus'], runs['plain'])
    a = ablation.reflection_signs(cfg, 3, 100)
    assert np.array_equal(a, ablation.reflection_signs(cfg, 3, 100)) and not np.array_equal(a, ablation.reflection_signs(cfg, 4, 100))
    model, ev, xt2, yt2, f = keyed_build(cfg)
    state, out, _, _ = mini_train(cfg, epochs=1)
    return {**f, **{k: v for k, v in pairing(ev).items() if k.startswith('kernel_hash_paths_equal')},
            'step_metrics_aug_vs_manual': [runs['aug'], runs['manual']],
            'all_plus_signs_bitwise_equal_to_plain': True, 'mini_train_epochs': state['completed_epochs']}


@slug('latent-ema-eval')
def t_latent_ema():
    ablation, keras = CTX['ablation'], CTX['keras']
    cfg = with_keys(base_cfg(), experiment__latent_ema_decay=0.5)
    model, ev, xt, yt, f = keyed_build(cfg)
    ema = ablation.LatentEMA(model, 0.5)
    init = {k: s.numpy().copy() for k, _, s in ema.pairs}
    opt = ablation.optimizer_for(cfg, model)
    step = ablation.make_epoch_step(model, opt, xt[:256], yt[:256], cfg, latent_ema=ema)
    step(np.arange(256, dtype='int32'), False)
    for key, variable, shadow in ema.pairs:
        np.testing.assert_allclose(shadow.numpy(), 0.5 * init[key] + 0.5 * variable.numpy(), rtol=1e-6, atol=1e-7)
    live = {k: v.numpy().copy() for k, v, _ in ema.pairs}
    ema.swap_in()
    assert all(np.array_equal(v.numpy(), s.numpy()) for _, v, s in ema.pairs)
    ema.swap_out()
    assert all(np.array_equal(v.numpy(), live[k]) for k, v, _ in ema.pairs), 'swap is not exact'
    cfg_d = with_keys(base_cfg(), experiment__latent_ema_decay=0.9)
    out = Path(tempfile.mkdtemp(prefix='delta-ema-'))
    mini_train(cfg_d, epochs=2, out=out, stop_after=1)                      # pause, then resume
    state, out, _, _ = mini_train(cfg_d, epochs=2, out=out)
    leaf = out / 'checkpoints' / json.loads((out / 'latest.json').read_text())['checkpoint']
    shadow = dict(np.load(leaf / 'latent_ema.npz'))
    cand = keras.models.load_model(out / 'validation_candidate.keras', compile=False)
    live_m = keras.models.load_model(leaf / 'model.keras', compile=False)
    for key, value in shadow.items():
        name = key.split('__')[0]
        np.testing.assert_array_equal(cand.get_layer(name)._kernel.numpy(), value)
    differs = any(not np.array_equal(live_m.get_layer(k.split('__')[0])._kernel.numpy(), v) for k, v in shadow.items())
    assert differs, 'candidate should carry EMA latents, the resume checkpoint the live ones'
    return {**f, **{k: v for k, v in pairing(ev).items() if k.startswith('kernel_hash_paths_equal')},
            'ema_update_checked': True, 'swap_exact': True, 'resumed_to_epoch': state['completed_epochs'],
            'candidate_kernels_equal_saved_shadow': True}


@slug('beta-schedule-s-runner')
def t_beta_schedule():
    from hgq.utils.sugar import PieceWiseSchedule
    sched = [[0, 2e-08, 'linear'], [2, 3e-07, 'log'], [4, 3e-06, 'constant']]
    cfg = with_keys(base_cfg())
    cfg['train']['ebops'].update(controller='schedule', beta_schedule=sched)
    model, ev, xt, yt, f = keyed_build(cfg)
    out = Path(tempfile.mkdtemp(prefix='delta-beta-'))
    mini_train(cfg, epochs=5, out=out, stop_after=2)
    state, out, _, _ = mini_train(cfg, epochs=5, out=out)                  # resumed at epoch 2
    fn = PieceWiseSchedule([tuple(v) for v in sched])
    betas = [r['beta'] for r in history(out)]
    np.testing.assert_allclose(betas, [fn(e) for e in range(5)], rtol=1e-12)
    chang = PieceWiseSchedule([(0, 2e-8, 'linear'), (2000, 3e-7, 'log'), (7000, 3e-6, 'constant')])
    import run_engram
    bad = with_keys(base_cfg())
    bad['train']['ebops']['beta_schedule'] = sched                        # controller still "pid"
    try:
        run_engram.validate_cfg(bad)
        raise AssertionError('inert beta_schedule accepted')
    except ValueError:
        pass
    return {**f, 'betas_per_epoch': betas, 'resumed_run_completed': state['completed_epochs'],
            'state_pid_json': state['pid'],
            'chang_schedule_at_0_1000_2000_4500_7000': [float(chang(e)) for e in (0, 1000, 2000, 4500, 7000)]}


@slug('screen-collapse-stop')
def t_collapse():
    rule = {'threshold': 0.99, 'patience': 2, 'after_epoch': 1}          # synthetic labels: always "collapsed"
    cfg = with_keys(base_cfg(), experiment__collapse_stop=rule)
    model, ev, xt, yt, f = keyed_build(cfg)
    out = Path(tempfile.mkdtemp(prefix='delta-collapse-'))
    state, out, _, _ = mini_train(cfg, epochs=6, out=out)
    assert state['collapsed']['epoch'] == 3 and state['completed_epochs'] == 3, state.get('collapsed')
    assert (out / 'COLLAPSED.json').exists()
    meta = json.loads((out / 'COMPLETE.json').read_text())
    assert meta['collapsed']['epoch'] == 3
    state2, _, _, _ = mini_train(cfg, epochs=6, out=out)                  # re-invocation must not train on
    assert state2['completed_epochs'] == 3
    quiet = with_keys(base_cfg(), experiment__collapse_stop={'threshold': 0.01, 'patience': 2, 'after_epoch': 1})
    state3, out3, _, _ = mini_train(quiet, epochs=3)
    assert 'collapsed' not in state3 and not (out3 / 'COLLAPSED.json').exists() and state3['collapse_run'] == 0
    return {**f, 'collapsed_at_epoch': state['collapsed']['epoch'], 'reinvocation_completed_epochs': state2['completed_epochs'],
            'no_collapse_run_completed': state3['completed_epochs']}


@slug('head-dims')
def t_head_dims():
    ablation = CTX['ablation']
    cfg = with_keys(base_cfg(), arch__head_dims=[32, 32, 32])
    model, ev, xt, yt, f = keyed_build(cfg)
    names = [ly.name for ly in binary_layers(model) if ly.name.startswith('head_fc')]
    assert names == ['head_fc1', 'head_fc2', 'head_fc3', 'head_fc4'], names
    shapes = [tuple(model.get_layer(n)._kernel.shape) for n in names]
    assert shapes == [(32, 32), (32, 32), (32, 32), (32, 5)], shapes
    assert ablation.expected_binary_layers(cfg) == ablation.projection_layers(cfg) and len(ablation.projection_layers(cfg)) == 11
    metrics, _ = one_step(model, cfg, xt, yt)
    assert np.isfinite(metrics).all()
    return {**f, **pairing(ev), 'head_kernel_shapes': shapes, 'export_parity_max_abs': export_parity(model)}


def e_cfg():
    """Arm E shape (d24, 2 heads, 1 block, FFN 32, no PE) on the a07-n64 config; the [D19]/[D21]
    Chang quantizers are anchor keys not in this tarball, so this is the E shape on bundle quantizers."""
    return with_keys(base_cfg(), arch__d_model=24, arch__n_heads=2, arch__pos_enc='none')


@slug('pre-block-tanh-lut')
def t_tanh_lut():
    ablation, keras = CTX['ablation'], CTX['keras']
    facts = {}
    for label, cfg0 in (('a07', base_cfg()), ('E', e_cfg())):
        cfg = with_keys(cfg0, arch__pre_block_act='tanh_lut')
        model, ev, xt, yt, f = keyed_build(cfg)
        luts = [ly for ly in model.layers if ly.name.endswith('_tanh')]
        assert [ly.name for ly in luts] == ['bit_block_0_attn_tanh', 'bit_block_0_ffn_tanh']
        probe = keras.Model(model.inputs, [ly.output for ly in luts])
        outs = [np.asarray(o) for o in probe(xt[:32], training=False)]
        assert all(np.abs(o).max() <= 1.0 for o in outs)
        bits = [float(np.min(np.asarray(ly.oq.quantizer.bits))) for ly in luts]
        assert min(bits) >= 4, bits
        per_layer = ablation.compute_ebops(model, xt[:256])['per_layer']
        widths = ablation.width_snapshot(model)
        assert all(ly.name in widths for ly in luts), 'LUT input grid not tracked'
        metrics, _ = one_step(model, cfg, xt, yt)
        assert np.isfinite(metrics).all()
        facts[label] = {**f, **pairing(ev), 'lut_ebops_synthetic': {ly.name: per_layer.get(ly.name) for ly in luts},
                        'table_min_bits': bits}
    return facts


@slug('ternary-absmean')
def t_ternary():
    import tensorflow as tf
    qat, ablation = CTX['qat'], CTX['ablation']
    w = np.random.default_rng(12).normal(0, 1, (8, 6)).astype('float32')
    out = np.asarray(qat.ternary_absmean_ste(tf.constant(w)))
    g = np.abs(w).mean() + 1e-6
    np.testing.assert_allclose(out, np.clip(np.round(w / g), -1, 1) * g, rtol=1e-6)
    assert (out == 0).any(), 'ternary test input produced no zero'
    cfg = with_keys(base_cfg(), quant__weight='ternary_absmean')
    model, ev, xt, yt, f = keyed_build(cfg, gate='none')
    ablation.binary_gate(model, cfg)                      # runs the labelled ternary gate
    tern = qat.ternary_weight_values(model)
    assert len(tern) == 9 and not qat.effective_weight_values(model)
    ly = model.get_layer('input_proj')
    kbits = float(np.max(np.asarray(ly.kq.bits_(tuple(ly._kernel.shape)))))
    assert kbits == 2.0
    try:                                                  # a binary config must refuse ternary layers
        ablation.binary_gate(model, base_cfg())
        raise AssertionError('binary gate accepted ternary layers')
    except AssertionError as exc:
        assert 'accepted' not in str(exc)
    metrics, _ = one_step(model, cfg, xt, yt)
    return {**f, **pairing(ev), 'weight_bits_billed': kbits,
            'values_per_layer': {k: len(v) for k, v in tern.items()}, 'epoch_metrics': metrics}


@slug('hgq-learnable-weights')
def t_hgq_learnable():
    import tensorflow as tf
    qat = CTX['qat']
    cfg = with_keys(base_cfg(), quant__weight='hgq_learnable')
    model, ev, xt, yt, f = keyed_build(cfg)             # binary gate: no binary layers expected
    assert not binary_layers(model)
    ly = model.get_layer('input_proj')
    bits0 = np.asarray(ly.kq.bits_(tuple(ly._kernel.shape)))
    assert np.allclose(bits0, 4.0), np.unique(bits0)
    trainable = [v.path for v in model.trainable_variables if 'input_proj' in v.path]
    assert any(v.endswith('/b') for v in trainable) and any(v.endswith('/i') for v in trainable), trainable
    with tf.GradientTape() as tape:
        loss = tf.reduce_sum(model(xt[:16], training=True) ** 2) + tf.add_n(model.losses)
    b_var = next(v for v in model.trainable_variables if v.path.startswith('input_proj') and v.path.endswith('/b'))
    grad = tape.gradient(loss, b_var)
    assert grad is not None and float(tf.reduce_sum(tf.abs(grad))) > 0
    metrics, _ = one_step(model, cfg, xt, yt)
    return {**f, **pairing(ev), 'weight_bits_init': float(bits0.mean()),
            'width_vars_input_proj': trainable, 'epoch_metrics': metrics}


@slug('accumulator-ebops-metric')
def t_accumulator():
    from bnhgq2.ebops_calc import accumulator_bits
    facts = {}
    for label, cfg0 in (('a07', base_cfg()), ('E', e_cfg())):
        cfg = with_keys(cfg0, experiment__accumulator_metric=True)
        model, ev, xt, yt, f = keyed_build(cfg)
        acc = accumulator_bits(model)
        D = cfg['arch']['d_model']
        expect_fan = {'input_proj': 3, 'bit_block_0_attn_Wq': D, 'bit_block_0_attn_Wo': D,
                      'bit_block_0_ffn_fc2': cfg['arch']['ffn_dim'], 'head_fc1': D, 'head_fc2': D}
        for name, fan in expect_fan.items():
            assert acc[name]['fan_in'] == fan, (name, acc[name])
            assert acc[name]['b_acc'] == acc[name]['b_act_max'] + int(np.ceil(np.log2(fan)))
        state, out, _, _ = mini_train(cfg, epochs=1)
        rec = history(out)[-1]
        assert all(f'accumulator_bits/{n}' in rec for n in acc) and 'ebops' in rec
        facts[label] = {**f, 'per_layer_synthetic_init': acc}
    return facts


@slug('diag-sign-flips')
def t_sign_flips():
    ablation = CTX['ablation']
    cfg = with_keys(base_cfg(), experiment__diagnostics=['sign_flips'])
    model, ev, xt, yt, f = keyed_build(cfg)
    out = Path(tempfile.mkdtemp(prefix='delta-diag-'))
    diag = ablation.DeltaDiagnostics(cfg, model, out)
    ly = model.get_layer('head_fc2')
    k = ly._kernel.numpy()
    before = np.asarray(ly.qkernel) > 0
    mean = k.mean()
    k2 = k.copy(); flat = k2.reshape(-1)
    idx = np.argsort(np.abs(flat - mean))[-10:]            # far from threshold: mirror 10 latents
    flat[idx] = 2 * mean - flat[idx]
    ly._kernel.assign(k2)
    after = np.asarray(ly.qkernel) > 0
    logs = diag(model, 0)
    expect = float(np.mean(after != before))
    assert abs(logs['diag/flip_fraction/head_fc2'] - expect) < 1e-12 and expect > 0
    assert logs['diag/flip_fraction/input_proj'] == 0.0 and logs['diag/c2i/head_fc2'] == expect
    logs2 = diag(model, 1)
    assert logs2['diag/flip_fraction/head_fc2'] == 0.0 and logs2['diag/c2i/head_fc2'] == expect
    state, outdir, _, _ = mini_train(cfg, epochs=2)
    rec = history(outdir)
    assert all('diag/flip_fraction' in r and 'diag/c2i' in r for r in rec)
    return {**f, 'flip_fraction_head_fc2_after_mirroring_10': expect,
            'mini_train_flip_fraction_per_epoch': [r['diag/flip_fraction'] for r in rec],
            'mini_train_c2i_per_epoch': [r['diag/c2i'] for r in rec]}


@slug('diag-beta-trajectory')
def t_beta_traj():
    ablation = CTX['ablation']
    cfg = with_keys(base_cfg(), experiment__diagnostics=['beta_trajectory'])
    model, ev, xt, yt, f = keyed_build(cfg)
    diag = ablation.DeltaDiagnostics(cfg, model, tempfile.mkdtemp())
    logs = diag(model, 0)
    k = model.get_layer('input_proj')._kernel.numpy().astype('float64')
    beta = np.abs(k - k.mean()).mean() + 1e-6
    assert abs(logs['diag/beta/input_proj'] - beta) < 1e-6
    fr = [v for key, v in logs.items() if key.startswith('diag/latent_over_absmean/input_proj/')]
    assert len(fr) == 6 and abs(sum(fr) - 1) < 1e-9
    state, outdir, _, _ = mini_train(with_keys(base_cfg(), experiment__diagnostics=['sign_flips', 'beta_trajectory']), epochs=1)
    rec = history(outdir)[-1]
    assert 'diag/beta/head_fc2' in rec and 'diag/c2i' in rec
    return {**f, 'beta_input_proj_init': logs['diag/beta/input_proj'], 'hist_input_proj_init': fr}


@slug('E-shape-sweep')
def t_e_sweep():
    """Every write-now slug's key on arm E's shape (350k arms run on E, Kai 2026-09-27):
    build, gate, save -> reload within 1e-7. Bundle quantizers ([D19]/[D21] are anchor keys)."""
    tag, _ = make_teacher('teacher-fp32-E', shape_cfg=e_cfg())
    kd = {'teacher_artifact': tag, 'temperature': 2, 'coefficient': 0.5, 'attention_coefficient': 1.0}
    deltas = {
        'binarizer-center-flag': {'quant__binary_center': False},
        'ste-variants': {'quant__ste': 'ede', 'quant__ste_ede_period': 500},
        'latent-clip': {'quant__latent_clip': 1.0},
        'beta-mode': {'quant__beta_mode': 'learned_pow2'},
        'channel-gain-pow2': {'quant__channel_gain': {'layers': 'all_binary', 'mode': 'pow2'}},
        'init-from-checkpoint': {'experiment__init_checkpoint': tag},
        'kd-unblock-s-runner+kd-attention-map': {'experiment__distillation': kd},
        'latent-ema-eval': {'experiment__latent_ema_decay': 0.999},
        'augment-eta-phi-reflect': {'data__augment': {'reflect_eta': True, 'reflect_phi': True}},
        'weight-scheme-baselines': {'quant__layer_weight_override': {'input_proj': 'int8_absmax'}},
        'ternary-absmean': {'quant__weight': 'ternary_absmean'},
        'hgq-learnable-weights': {'quant__weight': 'hgq_learnable'},
        'head-dims': {'arch__head_dims': [32, 32, 32]},
        'pre-block-tanh-lut': {'arch__pre_block_act': 'tanh_lut'},
        'screen-collapse-stop': {'experiment__collapse_stop': {'threshold': 0.25, 'patience': 10, 'after_epoch': 20}},
        'accumulator-ebops-metric': {'experiment__accumulator_metric': True},
        'diag-sign-flips+diag-beta-trajectory': {'experiment__diagnostics': ['sign_flips', 'beta_trajectory']},
    }
    facts = {}
    ablation = CTX['ablation']
    for name, delta in deltas.items():
        cfg = with_keys(e_cfg(), **delta)
        gate = 'none' if 'ternary' in name else 'binary'
        model, ev, xt, yt, f = keyed_build(cfg, gate=gate)
        ablation.binary_gate(model, cfg)
        kw = {}
        if 'kd-' in name:
            kw['teacher_model'] = CTX['keras'].models.load_model(ablation.resolve_artifact(tag)[0], compile=False)
        if 'augment' in name:
            kw['input_std'] = {'mu': [0.] * 3, 'sigma': [1.] * 3}
        opt = ablation.delta_optimizer_for(cfg, model) if hasattr(ablation, 'delta_optimizer_for') else ablation.optimizer_for(cfg, model)
        step = ablation.make_epoch_step(model, opt, xt, yt, cfg, **kw)
        order = np.arange(len(xt), dtype='int32')
        args = (ablation.reflection_signs(cfg, 0, len(xt)),) if 'augment' in name else ()
        step(order, False, *args)
        ablation.binary_gate(model, cfg)                     # post-step gate (2 optimizer steps)
        facts[name] = {k: f[k] for k in ('params', 'initial_ebops_synthetic', 'reload_max_abs_diff', 'within_1e-7')}
    sched = with_keys(e_cfg())
    sched['train']['ebops'].update(controller='schedule', beta_schedule=[[0, 2e-08, 'linear'], [2, 3e-07, 'constant']])
    model, ev, xt, yt, f = keyed_build(sched)
    facts['beta-schedule-s-runner'] = {k: f[k] for k in ('params', 'initial_ebops_synthetic', 'reload_max_abs_diff', 'within_1e-7')}
    base_model, _, _, _, bf = keyed_build(e_cfg())
    facts['E_unkeyed'] = {k: bf[k] for k in ('params', 'initial_ebops_synthetic')}
    return facts


def delta_cfg(entry_glob, raw=False):
    """A generated Delta config (new-files engineer's generator output, stand-in base).
    Until the generator is re-run under the atlas -> Delta rename (2026-09-27), its configs carry
    the provenance block under the old name `atlas_study`, which the renamed strict validator
    refuses by design; raw=False moves that block to `delta_study` (provenance only, no key
    below it is read), raw=True returns the file as written."""
    import glob
    # configs/ = generated on the anchor base (anchor keys; only the anchor tree accepts them);
    # configs-standin/ = the same entries on the tarball stand-in base (tarball tree).
    anchor_tree = (CTX['tree'] / 'campaigns' / 'chang0926').is_dir()
    root = Path(__file__).resolve().parents[1] / ('configs' if anchor_tree else 'configs-standin')
    if not root.is_dir():
        root = root.parent / 'configs'
    cfg = json.loads(Path(sorted(glob.glob(str(root / 'W*' / entry_glob)))[0]).read_text())
    cfg['train']['batch'] = min(int(cfg['train']['batch']), 256)   # CPU: 512 synthetic jets, >= 2 steps
    if not raw and 'atlas_study' in cfg:
        cfg['delta_study'] = cfg.pop('atlas_study')
    return cfg


def refused(cfg):
    import run_engram
    try:
        run_engram.validate_cfg(cfg)
    except ValueError as exc:
        return str(exc)
    return None


@slug('strict-keys')
def t_strict_keys():
    """Review A1-v3: an unread key is refused by name; on a tree without the wiring patches the
    M006/M020 keys are refused too, with it they build the Deep Sets body / BopAdam."""
    from bnhgq2 import delta_keys
    facts = {}
    bogus = with_keys(base_cfg(), train__totally_bogus_key=1)
    msg = refused(bogus)
    assert msg and 'train.totally_bogus_key' in msg, msg
    facts['invented_key'] = msg[-90:]
    for entry, key in (('M004-t350000-s2.json', 'arch.attn_kind'), ('M006-t350000-s2.json', 'arch.body'),
                       ('M020-t5000000-s2.json', 'train.binary_optimizer')):
        cfg = delta_cfg(entry)
        msg = refused(cfg)
        wired = key in delta_keys.REGISTRY
        if wired:
            assert msg is None, msg
        else:
            assert msg and key in msg, msg
        facts[entry.split('-')[0]] = 'accepted (wired)' if wired else msg[-100:]
    stale = delta_cfg('M001-t350000-s1.json', raw=True)
    if 'atlas_study' in stale:                        # pre-rename generator output: refused by name
        msg = refused(stale)
        assert msg and 'atlas_study' in msg, msg
        facts['pre_rename_block_refused'] = msg[-90:]
    element_wired = 'element' in delta_keys.VALUE_SETS.get('quant.act_granularity', ())   # anchor tree 0029
    for key, value in ((() if element_wired else (('quant__act_granularity', 'element'),))
                       + (('train__es_patience', 15), ('train__ebops__selection', 'min_ebops'))):
        msg = refused(with_keys(base_cfg(), **{key: value}))
        assert msg, (key, value)
    cfg = base_cfg(); cfg['train']['ebops']['controller'] = 'none'
    assert refused(cfg)
    import glob
    for f in sorted(glob.glob(str(CTX['tree'] / 'configs' / 'const0922-*.json'))):
        assert refused(json.loads(Path(f).read_text())) is None, f
    facts['bundle_configs_accepted'] = len(glob.glob(str(CTX['tree'] / 'configs' / 'const0922-*.json')))
    return facts


@slug('body-deepsets')
def t_deepsets():
    ablation, qat = CTX['ablation'], CTX['qat']
    cfg = delta_cfg('M006-t350000-s2.json')
    cfg['train'].update(epochs=2)
    model, ev, xt, yt, f = keyed_build(cfg)                   # includes ablation.binary_gate(model, cfg)
    names = set(qat.effective_weight_values(model))
    from newmods.deepsets import expected_binary_layers
    assert names == expected_binary_layers(cfg) and not any(n.startswith('bit_block') for n in names)
    assert ev.get('body') == 'deepsets' and f['params'] != 12788
    metrics, _ = one_step(model, cfg, xt, yt)
    assert np.isfinite(metrics).all()
    ablation.binary_gate(model, cfg)
    state, out, _, _ = mini_train(cfg, epochs=1)
    assert (out / 'COMPLETE.json').exists()
    assert refused(with_keys(cfg, arch__head_dims=[32]))
    return {**f, 'binary_layers': sorted(names), 'epoch_metrics': metrics, 'mini_train_epochs': state['completed_epochs']}


@slug('bop-optimizer')
def t_bop():
    ablation, qat, keras = CTX['ablation'], CTX['qat'], CTX['keras']
    cfg = delta_cfg('M020-t5000000-s2.json')             # gamma/tau are the generator's stand-in values
    model, ev, xt, yt, f = keyed_build(cfg)
    opt = ablation.delta_optimizer_for(cfg, model)
    assert type(opt).__name__ == 'BopAdam'
    plain_cfg = copy.deepcopy(cfg)                          # same architecture, no Bop keys
    for key in ('binary_optimizer', 'bop_gamma', 'bop_tau'):
        plain_cfg['train'].pop(key, None)
    plain_model, _ = build(plain_cfg, xt)
    assert len(opt.variables) == len(ablation.optimizer_for(plain_cfg, plain_model).variables)
    signs0 = {ly.name: np.asarray(ly.qkernel) > 0 for ly in binary_layers(model)}
    opt.learning_rate.assign(ablation.learning_rate(cfg, 0))
    step = ablation.make_epoch_step(model, opt, xt, yt, cfg)
    metrics = [float(v) for v in step(np.arange(len(xt), dtype='int32'), False).numpy()]
    flipped = sum(int(((np.asarray(ly.qkernel) > 0) != signs0[ly.name]).sum()) for ly in binary_layers(model))
    ablation.binary_gate(model, cfg)
    _, rel = reload_check(model, xt)
    out = Path(tempfile.mkdtemp(prefix='delta-bop-'))
    mini_train(cfg, epochs=2, out=out, stop_after=1)
    state, out, _, _ = mini_train(cfg, epochs=2, out=out)     # resume restores BopAdam by index
    assert state['completed_epochs'] == 2
    return {**f, 'optimizer': type(opt).__name__, 'signs_flipped_one_epoch': flipped,
            'epoch_metrics': metrics, 'reload_after_step': rel, 'resumed_to_epoch': 2}


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
    from bnhgq2 import qat
    tf.config.experimental.enable_tensor_float_32_execution(False)
    CTX.update(tree=args.tree, ablation=ablation, keras=keras, qat=qat)
    results = json.loads(args.out.read_text()) if args.out.exists() else {}
    for name in args.only or list(TESTS):
        t0 = time.monotonic()
        try:
            facts = TESTS[name]()
            results[name] = {'status': 'PASS', 'seconds': round(time.monotonic() - t0, 1), **(facts or {})}
            print('SLUG_TEST_PASS', name, 'seconds', results[name]['seconds'], flush=True)
        except Exception as exc:  # noqa: BLE001 - report every failure verbatim
            results[name] = {'status': 'FAIL', 'error': f'{type(exc).__name__}: {exc}',
                             'traceback': traceback.format_exc()[-2000:]}
            print('SLUG_TEST_FAIL', name, results[name]['error'], flush=True)
        args.out.write_text(json.dumps(results, indent=1, sort_keys=True, default=str) + '\n')
    bad = [k for k in (args.only or TESTS) if results[k]['status'] != 'PASS']
    print('SLUG_TESTS_ALL_PASS' if not bad else f'SLUG_TESTS_FAIL {bad}', flush=True)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
