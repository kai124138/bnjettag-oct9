#!/usr/bin/env python3
"""[A26] Attention-entropy readout (offline; STUDY arbiter v6 fix 10).

Loads a saved `.keras` checkpoint with the campaign's custom objects (`run_engram.runtime()`
registers the `bnhgq2` serializables, then `keras.models.load_model(..., compile=False)`, the
pattern of `run_study.train`), builds one sub-model on every `{blk}_attn_softmax` output
(`qat.py:574`; binary and fp32 branches share the name; the model is functional, `qat.py:615`)
and runs the **validation split** through it. Nothing here trains, writes into a run directory,
or reads the ROC-test set: the only data path is `run_engram.load_cache`, which opens
`x_train`, `y_train`, `x_val`, `y_val` and nothing else, and only `x_val` is fed.

Per block and head, over jets and query rows, with S = 64 keys:
    H_norm = mean( -sum_s p_s log p_s ) / log S,   p = q / sum_s q  (row-renormalized)
where q is the `{blk}_attn_softmax` output as the model computes it (quantized tables).
Renormalization is the primary definition because the quantized softmax does not always emit
rows that sum to 1 (fixed-softmax builds saturate the 1/sum input at 16, so a diffuse row sums
to > 1); see `.claude/memory/decisions.md`, 2026-09-27 [A26]. The un-renormalized value
`-sum q log q / log S` and the row-sum min / mean / max are reported beside it.

Beside the entropy: the Q/K and V 0-bit channel fractions (STUDY "attention state"). Sites:
Q = `{blk}_attn_scores__in0`, K = `{blk}_attn_scores__in1`, V = `{blk}_attn_ctx__in1`. A
channel is at 0 bits when its magnitude width b = relu(i + f) is 0 (HGQ2 0.1.9 KIF `q.b`); the
sign bit k is reported too. Under WRAP a 0-bit channel outputs 0 and costs 0 EBOPs; under SAT
with k = 1 it outputs 0 but is billed 1 bit ("silent, billed 1 bit"). fp32 (dummy quantizers):
undefined. No attention mask exists in the model, so zero-padded constituents are attended keys.

Pilot use (in-pod, CPU):
    python -u attn_entropy.py --indices 0 1 24 48 56 57 --epoch 500 \
        --out /data/chang-n64-20260926/pilot/analysis/a26-epoch-0500.json
reads `$BNJ_RUN_ROOT/runs/<name>/snapshots/epoch-0500/` and picks the checkpoint by the
`run_study.train` rule: `model_best.keras` if `state['best_feasible']` else
`model_min_ebops.keras`. VERIFY use: `--indices I --checkpoint PATH` on one selected file.
Output numbers are diagnostics for the phase-4 VERIFY; nothing printed here is a result.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path

import numpy as np

N_KEYS = 64            # STUDY: normalize by log 64 (N = 64 constituents)
SNAPSHOT_FILES = ('model_best.keras', 'model_min_ebops.keras')


# --------------------------------------------------------------------------- entropy
def row_entropies(q):
    """Per-row entropies of attention rows q[..., S] (the softmax output as computed).

    Returns (h_norm, h_raw, row_sum, n_negative) as float64 arrays of shape q.shape[:-1]
    (n_negative is a scalar count). h_norm uses p = q / sum(q) and 0 log 0 = 0, divided by
    log S; h_raw is -sum q log q / log S on q as emitted. Rows with sum <= 0 give NaN in
    h_norm (counted by the caller). Negative q (not expected: tables are unsigned) are
    counted and treated as 0."""
    q = np.asarray(q, dtype=np.float64)
    s_keys = q.shape[-1]
    n_negative = int(np.count_nonzero(q < 0))
    q = np.where(q > 0, q, 0.0)
    row_sum = q.sum(-1)
    log_s = math.log(s_keys)
    with np.errstate(divide='ignore', invalid='ignore'):
        p = q / row_sum[..., None]
        h_norm = -np.where(p > 0, p * np.log(np.where(p > 0, p, 1.0)), 0.0).sum(-1) / log_s
        h_norm = np.where(row_sum > 0, h_norm, np.nan)
        h_raw = -np.where(q > 0, q * np.log(np.where(q > 0, q, 1.0)), 0.0).sum(-1) / log_s
    return h_norm, h_raw, row_sum, n_negative


def softmax_layer_names(model):
    names = [ly.name for ly in model.layers if ly.name.endswith('_attn_softmax')]
    if not names:
        raise ValueError(f'{model.name}: no *_attn_softmax layer')
    return sorted(names)


def attention_submodel(model):
    import keras
    names = softmax_layer_names(model)
    return names, keras.Model(model.inputs, [model.get_layer(n).output for n in names])


def analyze(model, x, batch=1024, n_keys=N_KEYS):
    """Stream x (validation rows) through the softmax sub-model; per block and head return
    the jet/query-row mean of H_norm (primary), of the raw value, row-sum stats, and the
    across-jet spread of the per-jet mean H_norm."""
    names, sub = attention_submodel(model)
    acc = {}
    n = len(x)
    for start in range(0, n, batch):
        outs = sub(np.asarray(x[start:start + batch], dtype=np.float32), training=False)
        outs = outs if isinstance(outs, (list, tuple)) else [outs]
        for name, q in zip(names, outs):
            q = np.asarray(q)
            if q.ndim != 4 or q.shape[-1] != n_keys or q.shape[-2] != n_keys:
                raise ValueError(f'{name}: expected (B, H, {n_keys}, {n_keys}), got {q.shape}')
            h_norm, h_raw, row_sum, n_neg = row_entropies(q)          # (B, H, T)
            a = acc.setdefault(name, {
                'heads': q.shape[1], 'sum': np.zeros(q.shape[1]), 'sum_raw': np.zeros(q.shape[1]),
                'jet_sum': np.zeros(q.shape[1]), 'jet_sumsq': np.zeros(q.shape[1]),
                'rows': np.zeros(q.shape[1], dtype=np.int64), 'zero_rows': 0, 'negative': 0,
                'rs_min': np.inf, 'rs_max': -np.inf, 'rs_sum': 0.0, 'rs_n': 0})
            valid = np.isfinite(h_norm)
            a['zero_rows'] += int((~valid).sum())
            a['negative'] += n_neg
            a['sum'] += np.where(valid, h_norm, 0.0).sum((0, 2))
            a['sum_raw'] += np.where(valid, h_raw, 0.0).sum((0, 2))
            a['rows'] += valid.sum((0, 2))
            per_jet = np.nanmean(h_norm, axis=2) if valid.all() else np.array(
                [[np.nanmean(r) for r in jet] for jet in h_norm])       # (B, H)
            a['jet_sum'] += per_jet.sum(0)
            a['jet_sumsq'] += (per_jet ** 2).sum(0)
            a['rs_min'] = min(a['rs_min'], float(row_sum.min()))
            a['rs_max'] = max(a['rs_max'], float(row_sum.max()))
            a['rs_sum'] += float(row_sum.sum())
            a['rs_n'] += row_sum.size
    report = {}
    for name in names:
        a = acc[name]
        blk = name[:-len('_attn_softmax')]
        heads = []
        for h in range(a['heads']):
            mean_jet = a['jet_sum'][h] / n
            var = max(a['jet_sumsq'][h] / n - mean_jet ** 2, 0.0)
            heads.append({'head': h,
                          'entropy_over_log_n': float(a['sum'][h] / a['rows'][h]),
                          'entropy_over_log_n_unrenormalized': float(a['sum_raw'][h] / a['rows'][h]),
                          'per_jet_std': float(math.sqrt(var)),
                          'query_rows': int(a['rows'][h])})
        report[blk] = {'layer': name, 'n_keys': n_keys, 'n_jets': int(n), 'heads': heads,
                       'row_sum': {'min': a['rs_min'], 'mean': a['rs_sum'] / a['rs_n'],
                                   'max': a['rs_max']},
                       'zero_sum_rows': a['zero_rows'], 'negative_entries': a['negative']}
    return report


# --------------------------------------------------------------------------- 0-bit widths
def _quantizer(model, layer, index):
    iq = getattr(model.get_layer(layer), 'iq', None)
    qs = [] if iq is None else list(iq) if hasattr(iq, '__len__') else [iq]
    qz = getattr(qs[index], 'quantizer', None) if index < len(qs) else None
    if qz is None or getattr(qz, '__dummy__', False) or not hasattr(qz, 'b'):
        return None
    return qz


def zero_bit_fractions(model, n_heads):
    """Per block: fraction of Q, K, Q/K combined and V channels with b = relu(i+f) = 0, the
    sign bits, per-head counts, and the live Q.K pair count per head (e with b_Q > 0 and
    b_K > 0; zero live pairs => constant logits in that head)."""
    out = {}
    for name in softmax_layer_names(model):
        blk = name[:-len('_attn_softmax')]
        sites = {'Q': (f'{blk}_attn_scores', 0), 'K': (f'{blk}_attn_scores', 1),
                 'V': (f'{blk}_attn_ctx', 1)}
        qs = {role: _quantizer(model, *site) for role, site in sites.items()}
        if all(q is None for q in qs.values()):
            out[blk] = {'status': 'undefined (no width variables: fp32 / dummy quantizers)'}
            continue
        if any(q is None for q in qs.values()):
            raise ValueError(f'{blk}: some but not all of Q/K/V carry width variables')
        entry, per_head_b = {'status': 'defined'}, {}
        for role, q in qs.items():
            b = np.asarray(q.b, dtype=np.float64).ravel()
            k = np.broadcast_to(np.asarray(q.k, dtype=np.float64).ravel(), b.shape) \
                if np.asarray(q.k).size in (1, b.size) else np.asarray(q.k, dtype=np.float64).ravel()
            zero = b == 0
            granularity = 'channel' if b.size > 1 else 'tensor'
            if granularity == 'channel' and b.size % n_heads:
                raise ValueError(f'{blk} {role}: {b.size} width channels not divisible by {n_heads} heads')
            hb = b.reshape(n_heads, -1) if granularity == 'channel' else np.full((n_heads, 1), b[0])
            per_head_b[role] = hb
            silent_billed = bool(q.overflow_mode == 'SAT' and np.any(zero & (k > 0)))
            entry[role] = {'site': f'{sites[role][0]}__in{sites[role][1]}',
                           'overflow_mode': q.overflow_mode, 'granularity': granularity,
                           'channels': int(b.size), 'zero_bit': int(zero.sum()),
                           'zero_bit_fraction': float(zero.mean()),
                           'sign_bit_channels': int((k > 0).sum()),
                           'zero_bit_per_head': [int((row == 0).sum()) for row in hb],
                           'label': ('silent, billed 1 bit' if silent_billed else
                                     'true zero, 0 EBOPs' if q.overflow_mode == 'WRAP' else '')}
        nq, nk = entry['Q']['channels'], entry['K']['channels']
        entry['QK_zero_bit_fraction'] = (entry['Q']['zero_bit'] + entry['K']['zero_bit']) / (nq + nk)
        entry['V_zero_bit_fraction'] = entry['V']['zero_bit_fraction']
        if per_head_b['Q'].shape == per_head_b['K'].shape:
            entry['QK_live_pairs_per_head'] = [int(((qb > 0) & (kb > 0)).sum())
                                               for qb, kb in zip(per_head_b['Q'], per_head_b['K'])]
        out[blk] = entry
    return out


# --------------------------------------------------------------------------- I/O
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def load_checkpoint(path):
    """Campaign pattern: runtime() registers the bnhgq2 custom objects, then load."""
    import run_engram
    run_engram.runtime()
    import keras
    return keras.models.load_model(path, compile=False)


def select_snapshot_checkpoint(run_dir, epoch):
    snap = Path(run_dir) / 'snapshots' / f'epoch-{int(epoch):04d}'
    state_path = snap / 'state.json'
    if not state_path.is_file():
        return None, None, f'no snapshot {snap}'
    state = json.loads(state_path.read_text())
    name = 'model_best.keras' if state.get('best_feasible') else 'model_min_ebops.keras'
    reason = ('best_feasible present (feasible as of epoch)' if state.get('best_feasible')
              else 'no feasible checkpoint as of epoch: lowest-EBOPs file')
    path = snap / name
    if not path.is_file():
        return None, None, f'{path} missing ({reason})'
    return path, reason, None


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--indices', type=int, nargs='+', required=True, help='rows of index.json')
    ap.add_argument('--epoch', type=int, default=500, help='snapshots/epoch-EEEE to read')
    ap.add_argument('--checkpoint', type=Path, help='explicit .keras (exactly one index)')
    ap.add_argument('--n-val', type=int, default=None, help='first n validation rows (default all)')
    ap.add_argument('--batch', type=int, default=1024)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args(argv)
    if args.checkpoint and len(args.indices) != 1:
        ap.error('--checkpoint takes exactly one --indices value')
    if args.out.exists():
        ap.error(f'{args.out} exists; refusing to overwrite')

    import run_engram
    import run_study
    run_engram.runtime()
    import keras
    campaign = Path(os.environ.get('BNJ_CAMPAIGN_DIR', run_study.CAMPAIGN))
    data_root = Path(os.environ.get('BNJ_DATA_ROOT', run_study.DATA_ROOT))
    run_root = Path(os.environ.get('BNJ_RUN_ROOT', run_study.ROOT))
    rows = json.loads((campaign / 'index.json').read_text())['runs']
    source = run_study.manifest()
    record = {'a26': 'attention entropy readout', 'split': 'validation', 'test_set_used': False,
              'script_sha256': sha256_file(__file__), 'code_manifest_sha256': source['sha256'],
              'versions': source['versions'], 'epoch': None if args.checkpoint else args.epoch,
              'definition': 'mean over jets and query rows of -sum p log p / log 64, '
                            'p = softmax output / row sum; unrenormalized value and row sums beside it',
              'runs': []}
    cache, failures = {}, 0
    for index in args.indices:
        row = rows[index]
        cfg = json.loads((campaign / 'configs' / row['file']).read_text())
        run_dir = run_root / 'runs' / row['name']
        entry = {'index': index, 'name': row['name'], 'arm': row.get('arm')}
        if args.checkpoint:
            path, reason, problem = args.checkpoint, 'explicit --checkpoint', None
        elif (run_dir / 'DIVERGED.json').exists():
            path, reason, problem = None, None, 'DIVERGED.json present'
        else:
            path, reason, problem = select_snapshot_checkpoint(run_dir, args.epoch)
        if problem:
            entry['status'] = problem
            record['runs'].append(entry)
            print('A26_SKIPPED', row['name'], problem, flush=True)
            failures += 0 if problem == 'DIVERGED.json present' else 1
            continue
        n_part = int(cfg['arch']['n_part'])
        if n_part != N_KEYS:
            raise ValueError(f"{row['name']}: n_part {n_part} != {N_KEYS}")
        if n_part not in cache:
            arrays, info = run_engram.load_cache(data_root / f'n{n_part}' / 'data', cfg)
            cache[n_part] = (arrays[2], info)
        x_val, info = cache[n_part]
        x = x_val if args.n_val is None else x_val[:args.n_val]
        keras.backend.clear_session()
        model = load_checkpoint(path)
        if model.name != cfg['name']:
            raise ValueError(f'checkpoint model name {model.name!r} != config {cfg["name"]!r}')
        entry.update(status='ok', checkpoint=str(path), checkpoint_reason=reason,
                     checkpoint_sha256=sha256_file(path), n_val_rows=int(len(x)),
                     x_val_sha256=info['engram_array_sha256']['x_val'],   # hashed by load_cache
                     y_val_sha256=info['engram_array_sha256']['y_val'],
                     entropy=analyze(model, x, batch=args.batch),
                     zero_bit=zero_bit_fractions(model, int(cfg['arch']['n_heads'])))
        record['runs'].append(entry)
        for blk, e in entry['entropy'].items():
            for h in e['heads']:
                print('A26_ENTROPY', row['name'], blk, 'head', h['head'],
                      'H_over_logN', f"{h['entropy_over_log_n']:.6f}",
                      'unrenormalized', f"{h['entropy_over_log_n_unrenormalized']:.6f}",
                      'split validation n', e['n_jets'], flush=True)
            print('A26_ROWSUM', row['name'], blk, json.dumps(e['row_sum']), flush=True)
        for blk, z in entry['zero_bit'].items():
            if z['status'] != 'defined':
                print('A26_ZEROBIT', row['name'], blk, z['status'], flush=True)
                continue
            print('A26_ZEROBIT', row['name'], blk,
                  'QK', f"{z['QK_zero_bit_fraction']:.6f}", 'V', f"{z['V_zero_bit_fraction']:.6f}",
                  'Q', z['Q']['zero_bit'], '/', z['Q']['channels'],
                  'K', z['K']['zero_bit'], '/', z['K']['channels'],
                  'V', z['V']['zero_bit'], '/', z['V']['channels'],
                  'labels', repr(z['Q']['label']), flush=True)
        del model
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + '.tmp')
    tmp.write_text(json.dumps(record, indent=2, allow_nan=False) + '\n')
    os.replace(tmp, args.out)
    print('A26_WROTE', args.out, 'sha256', sha256_file(args.out), flush=True)
    print('A26_DONE' if failures == 0 else f'A26_INCOMPLETE {failures}', flush=True)
    return 0 if failures == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
