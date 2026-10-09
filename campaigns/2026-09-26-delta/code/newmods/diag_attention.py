"""diag-attention: attention entropy / log(n_valid) with gated keys masked, and the
attention-ablation delta (A.V replaced by the mean of V over valid keys). Delta Z08, always-on
diagnostic (delta.json always_on_diagnostics). Diagnostic only: never a result, never quotable.

Definitions (stated so the numbers can be checked):
  * p[b,h,t,s] = the softmax layer's output (`*_attn_softmax`), before the output quantizer.
  * valid[b,s] = constituent s is real, not gated or padded. Under the anchor pT gate the gated
    constituents have all features 0 before standardization; pass `valid` explicitly (from the
    raw pT column) or it is taken as all-true.
  * Masked renormalization: p'[.,s] = p[.,s] valid[s] / sum_s p[.,s] valid[s].
  * Entropy ratio r[b,h,t] = -sum_s p' log p' / log(n_valid[b]), for valid queries t of jets with
    n_valid >= 2. r = 1 is uniform over the valid keys (a Deep Set, THEORY M5); r -> 0 is
    one-hot. Reported mean per layer and per head, plus the jet count used.
  * Ablation: every softmax layer's output replaced by valid[s] / n_valid (uniform over valid
    keys), so A.V becomes the masked mean of V; delta = metric(ablated) - metric(model) on the
    same inputs. For Linformer layers the keys are the k projected slots, so the mask is not
    applicable there and uniform over k is used (reported as such).

    python -m newmods.diag_attention --checkpoint model.keras --npz val.npz [--max-jets 4096]
      (npz keys: x (N,T,F) model inputs, y one-hot labels, optional valid (N,T) bool)
"""
from __future__ import annotations

import argparse
import contextlib
import json

import keras
import numpy as np
from keras import ops


def softmax_layers(model):
    return [ly for ly in model.layers if ly.name.endswith('_attn_softmax')]


def attention_probs(model, x, batch=1024):
    """{layer_name: (N, H, T, S) float64} softmax outputs."""
    layers = softmax_layers(model)
    if not layers:
        return {}
    probe = keras.Model(model.inputs, [ly.output for ly in layers])
    outs = [[] for _ in layers]
    for i in range(0, len(x), batch):
        res = probe(x[i:i + batch], training=False)
        res = res if isinstance(res, (list, tuple)) else [res]
        for j, r in enumerate(res):
            outs[j].append(np.asarray(r, dtype=np.float64))
    return {ly.name: np.concatenate(o) for ly, o in zip(layers, outs)}


def entropy_ratio(p, valid=None):
    """p: (N,H,T,S) probabilities over s; valid: (N,S) bool or None. Returns dict of means."""
    p = np.asarray(p, dtype=np.float64)
    n, h, t, s = p.shape
    if valid is None or valid.shape[1] != s:
        valid_k = np.ones((n, s), bool)
        masked = False
    else:
        valid_k = np.asarray(valid, bool)
        masked = True
    pm = p * valid_k[:, None, None, :]
    z = pm.sum(-1, keepdims=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        pn = np.where(z > 0, pm / z, 0.0)
        ent = -np.sum(np.where(pn > 0, pn * np.log(pn), 0.0), axis=-1)       # (N,H,T)
    n_valid = valid_k.sum(1)                                                  # (N,)
    use_jet = n_valid >= 2
    if valid is not None and masked and valid.shape[1] == t:
        q_ok = np.asarray(valid, bool)                                        # valid queries
    else:
        q_ok = np.ones((n, t), bool)
    w = (use_jet[:, None] & q_ok)[:, None, :].repeat(h, 1)                     # (N,H,T)
    ratio = np.where(w, ent / np.log(np.maximum(n_valid, 2))[:, None, None], np.nan)
    return {'mean': float(np.nanmean(ratio)) if w.any() else float('nan'),
            'per_head': [float(np.nanmean(ratio[:, i])) if w[:, i].any() else float('nan') for i in range(h)],
            'jets_used': int(use_jet.sum()), 'keys_masked': masked}


@contextlib.contextmanager
def uniform_attention(model, valid=None):
    """Replace every softmax output by uniform over valid keys while inside the context.

    Works for eager calls (model(x)); the patched `call` is an instance attribute, removed on exit."""
    layers = softmax_layers(model)
    state = {'valid': None if valid is None else ops.convert_to_tensor(np.asarray(valid, 'float32'))}

    def make(ly):
        def call(x, *args, **kwargs):
            shape = ops.shape(x)
            s = shape[-1]
            vk = state['valid']
            if vk is None or int(vk.shape[-1]) != int(s):
                u = ops.ones_like(x) / ops.cast(s, x.dtype)
            else:
                m = ops.reshape(vk, (-1, 1, 1, s))
                u = ops.broadcast_to(m / ops.maximum(ops.sum(m, axis=-1, keepdims=True), 1.0), shape)
            return u
        return call

    for ly in layers:
        ly.call = make(ly)
    try:
        yield state
    finally:
        for ly in layers:
            if 'call' in ly.__dict__:
                del ly.__dict__['call']


def _metrics(logits, y):
    from sklearn.metrics import roc_auc_score
    acc = float(np.mean(logits.argmax(-1) == y.argmax(-1)))
    e = np.exp(logits - logits.max(-1, keepdims=True))
    prob = e / e.sum(-1, keepdims=True)
    try:
        auc = float(roc_auc_score(y, prob, average='macro', multi_class='ovr'))
    except ValueError:
        auc = float('nan')
    return acc, auc


def predict_eager(model, x, batch=1024):
    return np.concatenate([np.asarray(model(x[i:i + batch], training=False)) for i in range(0, len(x), batch)])


def run(model, x, y, valid=None, batch=1024):
    probs = attention_probs(model, x, batch)
    report = {'layers': {name: entropy_ratio(p, valid) for name, p in probs.items()}}
    base = predict_eager(model, x, batch)
    acc0, auc0 = _metrics(base, y)
    report['ablation'] = {'n_jets': int(len(x))}
    if probs:
        chunks = []
        for i in range(0, len(x), batch):
            with uniform_attention(model, None if valid is None else valid[i:i + batch]):
                chunks.append(np.asarray(model(x[i:i + batch], training=False)))
        abl = np.concatenate(chunks)
        acc1, auc1 = _metrics(abl, y)
        report['ablation'].update(delta_accuracy=acc1 - acc0, delta_macro_auc=auc1 - auc0,
                                  split='as given by the caller', status='diagnostic, not quotable')
    return report


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--checkpoint', required=True)
    ap.add_argument('--npz', required=True)
    ap.add_argument('--max-jets', type=int, default=4096)
    args = ap.parse_args(argv)
    from bnhgq2.compat import apply_keras_compat
    apply_keras_compat()
    model = keras.models.load_model(args.checkpoint, compile=False)
    with np.load(args.npz) as d:
        x, y = d['x'][:args.max_jets], d['y'][:args.max_jets]
        valid = d['valid'][:args.max_jets] if 'valid' in d.files else None
    print(json.dumps(run(model, x, y, valid), indent=1))


if __name__ == '__main__':
    main()
