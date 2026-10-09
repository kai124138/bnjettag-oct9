#!/usr/bin/env python3
"""b5 historical readout: registered epoch-500 pilot rules from the five recovered histories.

Diagnostic, unreviewed. Computed on the local laptop, so nothing here is quotable
(CLAUDE.md: "Nothing computed in the lab pod or the local kernel is quotable").

Inputs (read-only, streamed one JSON line at a time; no file is loaded whole):
  captures/readout-run-20261001T0625Z/telemetry-raw-01/chang0926-<arm>-activation_widths.jsonl
  captures/readout-run-20261001T0625Z/terminal-handoff-20261001T0815Z/received/*.json
Outputs (this directory):
  history-<run>.csv   compact per-epoch scalars (one row per JSONL line)
  rules-b5.txt        every number cited by ../VERIFY.md, one per numbered line

Rules: campaigns/2026-09-26-training-batch/STUDY.md:1720-1847 (pilot rules) and :995-1021
(feasibility (a)-(c)). Epochs are zero-based in the JSONL (`epoch`), one-based when written
"ep1=". JSONL line n holds zero-based epoch n-1.

Run from the repository root:  python3 campaigns/2026-10-01-recovery/readout-preparation/analysis/b5_rules.py
Standard library only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMP = HERE.parent.parent
RAW = CAMP / 'captures/readout-run-20261001T0625Z/telemetry-raw-01'
RECV = CAMP / 'captures/readout-run-20261001T0625Z/terminal-handoff-20261001T0815Z/received'

# Registered constants (STUDY.md:1732-1734, :1752-1755, :1810-1811)
RUNS = {
    #  name                      target      floor      headroom   T for offset
    'chang0926-a-n64-s1':      (350_000,   171_526,   178_474,   350_000),
    'chang0926-a-n64-s2':      (350_000,   171_526,   178_474,   350_000),
    'chang0926-d-n64-s1':      (350_000,   171_526,   178_474,   350_000),
    'chang0926-cprime-n64-s1': (5_000_000, 4_580_398, 419_602,   5_000_000),
    'chang0926-e1-n64-s1':     (350_000,   85_763,    264_237,   350_000),
}
THRESH_C = 0.2109624456315518  # PREFLIGHT.md:519 (training-batch); also in every JSONL line
BETA_FLOOR = 1e-10
# b3 medians (one-based window), READOUT_epoch500.md table (4): rules-b3.txt:135,142,149
B3_MEDIAN_R = {'A07-350-s1': 1.005448, 'C-s1': 1.080792, 'F-s1': 1.028816}

out_lines: list[str] = []


def emit(s: str) -> None:
    out_lines.append(s)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def zero_bit_count(width_entry) -> tuple[int, int]:
    """(channels at 0 bits, channels) for one widths[...] entry, from its 'bits' array."""
    flat = []

    def walk(x):
        if isinstance(x, list):
            for y in x:
                walk(y)
        else:
            flat.append(float(x))
    walk(width_entry['bits'])
    return sum(1 for b in flat if b == 0.0), len(flat)


def median_ci(values: list[float]) -> tuple[float, float, float]:
    """Order-statistic interval on the median, as rules_b3.py (approx. 95 %, n >= 20)."""
    v = sorted(values)
    n = len(v)
    k = int(math.floor(n / 2 - 0.98 * math.sqrt(n)))
    lo, hi = v[max(k, 0)], v[min(n - 1 - k, n - 1)]
    return statistics.median(v), lo, hi


def analyse(name: str) -> dict:
    target, floor, headroom, t_off = RUNS[name]
    path = RAW / f'{name}-activation_widths.jsonl'
    rows = []
    attn = {}  # traced epoch -> (Qz,Qn,Kz,Kn,Vz,Vn)
    per_layer_last = None
    best_feasible_last = None
    with open(path, 'r') as fh:
        for lineno, line in enumerate(fh, start=1):
            d = json.loads(line)
            row = {k: d.get(k) for k in (
                'epoch', 'ebops_traced', 'ebops', 'ebops_in_training', 'pid_ebops',
                'ebops_in_training_over_traced', 'ebops_above_floor', 'beta', 'learning_rate',
                'val_categorical_accuracy', 'val_macro_auc', 'train_categorical_accuracy',
                'task_loss', 'loss', 'budget_met', 'ebops_budget_met', 'nondegenerate',
                'feasible_degenerate', 'activation_bits_mean', 'target_ebops',
                'val_accuracy_threshold')}
            row['line'] = lineno
            if d.get('ebops_traced') == 1 and d.get('widths'):
                w = d['widths']
                q = zero_bit_count(w['bit_block_0_attn_scores__in0'])
                k = zero_bit_count(w['bit_block_0_attn_scores__in1'])
                v = zero_bit_count(w['bit_block_0_attn_ctx__in1'])
                attn[d['epoch']] = q + k + v
                row['softmax_ebops'] = (d.get('per_layer') or {}).get('bit_block_0_attn_softmax')
                pl = d.get('per_layer') or {}
                row['attn_nonsoftmax_ebops'] = sum(val for key, val in pl.items()
                                                   if key.startswith('bit_block_0_attn_')
                                                   and key != 'bit_block_0_attn_softmax')
            if d.get('per_layer'):
                per_layer_last = (d['epoch'], d['per_layer'])
            best_feasible_last = d.get('best_feasible')
            rows.append(row)
            del d
    # CSV
    cols = list(rows[0].keys()) + ['softmax_ebops', 'attn_nonsoftmax_ebops']
    cols = list(dict.fromkeys(cols))
    with open(HERE / f'history-{name}.csv', 'w', newline='') as fh:
        wtr = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore')
        wtr.writeheader()
        for r in rows:
            wtr.writerow(r)

    emit(f'## {name}  file={path.relative_to(CAMP)}  sha256={sha256(path)}')
    epochs = [r['epoch'] for r in rows]
    emit(f'{name} lines={len(rows)} epochs_min={min(epochs)} epochs_max={max(epochs)} '
         f'unique={len(set(epochs))} monotonic={epochs == sorted(epochs)} '
         f'contiguous={epochs == list(range(len(rows)))}')
    traced = [r for r in rows if r['ebops_traced'] == 1]
    emit(f'{name} traced_epochs={len(traced)} zero_based={[r["epoch"] for r in traced][:4]}...'
         f'{[r["epoch"] for r in traced][-2:]}')
    thr = {r['val_accuracy_threshold'] for r in rows}
    emit(f'{name} threshold_c_values_in_file={sorted(thr)} registered={THRESH_C}')

    # feasibility (a)-(c) on traced epochs
    a_met = [r for r in traced if r['ebops'] <= target]
    feas = [r for r in a_met if r['ebops'] - floor > 0 and r['val_categorical_accuracy'] > THRESH_C]
    degen = [r for r in a_met if r not in feas]
    emit(f'{name} traced (a)_met={len(a_met)} feasible={len(feas)} feasible_degenerate={len(degen)} '
         f'of {len(traced)}; (a)_met ep0={[r["epoch"] for r in a_met]}')
    # cross-check runner flags
    flag_feas = [r['epoch'] for r in traced if r['ebops_budget_met'] == 1 and r['nondegenerate'] == 1
                 and not r['feasible_degenerate']]
    emit(f'{name} runner_flags feasible_ep0={flag_feas} matches_recompute='
         f'{flag_feas == [r["epoch"] for r in feas]}')
    fails_c = [r['epoch'] for r in traced if r['val_categorical_accuracy'] <= THRESH_C]
    emit(f'{name} traced epochs failing (c): n={len(fails_c)} first_ep0={fails_c[:1]} last_ep0={fails_c[-1:]}')

    # selection (STUDY.md:984-993): key acc -> AUC -> -EBOPs -> -epoch
    if feas:
        best = max(feas, key=lambda r: (r['val_categorical_accuracy'], r['val_macro_auc'],
                                        -r['ebops'], -r['epoch']))
        best_auc = max(feas, key=lambda r: (r['val_macro_auc'], r['val_categorical_accuracy'],
                                            -r['ebops'], -r['epoch']))
        emit(f'{name} selected_primary ep0={best["epoch"]} ebops={best["ebops"]} '
             f'above_floor={best["ebops"] - floor} headroom_frac={(best["ebops"] - floor) / headroom:.6f} '
             f'val_acc={best["val_categorical_accuracy"]:.6f} val_auc={best["val_macro_auc"]:.6f} line={best["line"]}')
        emit(f'{name} selected_auc_sensitivity ep0={best_auc["epoch"]} ebops={best_auc["ebops"]} '
             f'val_acc={best_auc["val_categorical_accuracy"]:.6f} val_auc={best_auc["val_macro_auc"]:.6f} line={best_auc["line"]}')
        for r in feas:
            emit(f'{name}   feasible ep0={r["epoch"]} ebops={r["ebops"]} val_acc={r["val_categorical_accuracy"]:.6f} '
                 f'val_auc={r["val_macro_auc"]:.6f} line={r["line"]}')
    emit(f'{name} best_feasible_in_last_line={best_feasible_last}')

    # minimum traced EBOPs (fallback model_min_ebops)
    mn = min(traced, key=lambda r: (r['ebops'], r['epoch']))
    emit(f'{name} min_traced ep0={mn["epoch"]} ebops={mn["ebops"]} over_target={mn["ebops"] - target} '
         f'x_target={mn["ebops"] / target:.6f} above_floor={mn["ebops"] - floor} '
         f'headroom_frac={(mn["ebops"] - floor) / headroom:.6f} x_floor={mn["ebops"] / floor:.6f} '
         f'val_acc={mn["val_categorical_accuracy"]:.6f} val_auc={mn["val_macro_auc"]:.6f} line={mn["line"]}')
    # untraced in-training below target?
    untr = [r for r in rows if r['ebops_traced'] != 1]
    below = [r for r in untr if r['ebops_in_training'] is not None and r['ebops_in_training'] <= target]
    mn_it = min(untr, key=lambda r: r['ebops_in_training'])
    emit(f'{name} untraced={len(untr)} in_training<=target on {len(below)}; min_in_training '
         f'ep0={mn_it["epoch"]} {mn_it["ebops_in_training"]:.0f}')
    # last 10 traced
    last10 = traced[-10:]
    emit(f'{name} last10 traced ep0={[r["epoch"] for r in last10]}')
    emit(f'{name} last10 ebops min={min(r["ebops"] for r in last10)} max={max(r["ebops"] for r in last10)} '
         f'x_target {min(r["ebops"] for r in last10) / target:.4f}-{max(r["ebops"] for r in last10) / target:.4f} '
         f'over_target={sum(r["ebops"] > target for r in last10)}/10')
    emit(f'{name} last10 val_acc min={min(r["val_categorical_accuracy"] for r in last10):.6f} '
         f'max={max(r["val_categorical_accuracy"] for r in last10):.6f}; '
         f'beta min={min(r["beta"] for r in last10):.4e} max={max(r["beta"] for r in last10):.4e}')
    emit(f'{name} over_target traced={sum(r["ebops"] > target for r in traced)}/{len(traced)}')

    # trajectory checkpoints (one-based epochs)
    by_ep = {r['epoch']: r for r in rows}
    for ep1 in (1, 10, 50, 100, 150, 200, 250, 300, 350, 400, 450, 500):
        r = by_ep.get(ep1 - 1)
        if r is None:
            continue
        emit(f'{name} traj ep1={ep1} traced={r["ebops_traced"]} ebops={r["ebops"]} '
             f'in_training={r["ebops_in_training"]} beta={r["beta"]:.4e} lr={r["learning_rate"]:.3e} '
             f'val_acc={r["val_categorical_accuracy"]:.6f} val_auc={r["val_macro_auc"]:.6f} '
             f'train_acc={r["train_categorical_accuracy"]:.6f} bits_mean={r["activation_bits_mean"]:.4f}')
    # peak validation accuracy over all epochs (descriptive)
    pk = max(rows, key=lambda r: r['val_categorical_accuracy'])
    emit(f'{name} peak val_acc ep0={pk["epoch"]} {pk["val_categorical_accuracy"]:.6f} '
         f'in_training={pk["ebops_in_training"]} traced={pk["ebops"]}')
    # max beta
    bmax = max(rows, key=lambda r: r['beta'])
    emit(f'{name} max beta ep0={bmax["epoch"]} {bmax["beta"]:.4e}')

    # attention 0-bit state over traced epochs
    first_all_zero = None
    for ep in sorted(attn):
        qz, qn, kz, kn, vz, vn = attn[ep]
        if qz == qn and kz == kn and first_all_zero is None:
            first_all_zero = ep
    stays = first_all_zero is not None and all(attn[e][0] == attn[e][1] and attn[e][2] == attn[e][3]
                                               for e in attn if e >= first_all_zero)
    emit(f'{name} attn first traced ep0 with Q and K all 0-bit={first_all_zero} stays_zero_after={stays}')
    for ep in (0, 9, 49, 99, 199, 299, 399, 499):
        if ep in attn:
            qz, qn, kz, kn, vz, vn = attn[ep]
            r = by_ep[ep]
            emit(f'{name} attn ep0={ep} Q0bit={qz}/{qn} K0bit={kz}/{kn} V0bit={vz}/{vn} '
                 f'softmax_ebops={r.get("softmax_ebops")} attn_other_ebops={r.get("attn_nonsoftmax_ebops")}')
    if per_layer_last:
        emit(f'{name} per_layer last traced ep0={per_layer_last[0]} {json.dumps(per_layer_last[1])}')

    # K1 inputs: r on traced epochs, one-based window 100-500 (zero-based 99..499) and zero-based 110-500
    def k1(sel, label):
        rs = [r['ebops_in_training_over_traced'] for r in sel]
        med, lo, hi = median_ci(rs)
        off = t_off * (1 - med ** -0.9)
        thr10 = 0.10 * headroom
        emit(f'{name} K1 window={label} n={len(rs)} median_r={med:.6f} ci=[{lo:.6f},{hi:.6f}] '
             f'offset={off:.1f} threshold={thr10:.1f} share={off / headroom:.4f} '
             f'clause={"exceeds" if off > thr10 else "below"}')
        rstar = (1 - thr10 / t_off) ** (-1 / 0.9)
        emit(f'{name} K1 window={label} r*={rstar:.6f} n_above_r*={sum(x > rstar for x in rs)}/{len(rs)} '
             f'ci_contains_r*={lo <= rstar <= hi}')
        return med, lo, hi
    w1 = [r for r in traced if 99 <= r['epoch'] <= 499]
    w0 = [r for r in traced if 109 <= r['epoch'] <= 499]
    med1 = k1(w1, 'one-based 100-500')
    k1(w0, 'zero-based 110-500')
    # consistency: logged ratio equals in_training / traced
    bad = [r['epoch'] for r in traced
           if abs(r['ebops_in_training'] / r['ebops'] - r['ebops_in_training_over_traced']) > 1e-12]
    emit(f'{name} ratio field equals in_training/traced on traced epochs: mismatches={bad}')

    # C' constraint readout (STUDY.md:1841-1844)
    if 'cprime' in name:
        over5 = [r for r in traced if r['ebops'] > 5_000_000]
        emit(f'{name} Cprime (i) traced over 5M = {len(over5)}/{len(traced)} = {len(over5) / len(traced):.4f}')
        emit(f'{name} Cprime (ii) fallback min traced / 5M = {mn["ebops"]} / 5000000 = {mn["ebops"] / 5e6:.6f} '
             f'(fallback, no feasible checkpoint)')
        at_floor = [r for r in last10 if abs(r['beta'] - BETA_FLOOR) / BETA_FLOOR <= 1e-6]
        emit(f'{name} Cprime (iii) beta at 1e-10 on last 10 traced = {len(at_floor)}/10; '
             f'beta range {min(r["beta"] for r in last10):.4e}-{max(r["beta"] for r in last10):.4e}')
        emit(f'{name} Cprime last10 over 5M = {sum(r["ebops"] > 5e6 for r in last10)}/10')
        emit(f'{name} Cprime min/floor = {mn["ebops"]} / {floor} = {mn["ebops"] / floor:.6f}')
    return {'median_r': med1, 'traced': traced}


def main() -> int:
    emit('# rules-b5.txt  diagnostic, unreviewed, local computation (not quotable)')
    for f in sorted(RECV.glob('*.json')):
        emit(f'input {f.relative_to(CAMP)} sha256={sha256(f)}')
    res = {n: analyse(n) for n in RUNS}

    emit('## K1 pairwise clause (median r, one-based window; |diff| > 0.02 fires)')
    meds = {n.replace('chang0926-', '').replace('-n64', ''): res[n]['median_r'] for n in RUNS}
    meds.update({k: (v, None, None) for k, v in B3_MEDIAN_R.items()})
    names = list(meds)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            ma, la, ha = meds[a]
            mb, lb, hb = meds[b]
            gap = ''
            if la is not None and lb is not None:
                gap_v = max(lb - ha, la - hb, 0.0)
                gap = f' gap_between_ci={gap_v:.6f}'
            emit(f'pair {a} {b} |dmedian|={abs(ma - mb):.6f} over_0.02={abs(ma - mb) > 0.02}{gap}')

    emit('## Regime-B half of matched table (one-based traced epochs 10..120)')
    for n in ('chang0926-a-n64-s1', 'chang0926-a-n64-s2', 'chang0926-d-n64-s1',
              'chang0926-e1-n64-s1', 'chang0926-cprime-n64-s1'):
        target, floor, _, _ = RUNS[n]
        for r in res[n]['traced']:
            ep1 = r['epoch'] + 1
            if 10 <= ep1 <= 120:
                f = (r['ebops'] <= target and r['ebops'] > floor and r['val_categorical_accuracy'] > THRESH_C)
                emit(f'regB {n} ep1={ep1} traced={r["ebops"]} in_training={r["ebops_in_training"]:.0f} '
                     f'r={r["ebops_in_training_over_traced"]:.6f} beta={r["beta"]:.4e} feasible={int(f)}')

    out = HERE / 'rules-b5.txt'
    with open(out, 'w') as fh:
        for i, s in enumerate(out_lines, start=1):
            fh.write(f'{i:4d}  {s}\n')
    print(f'wrote {out} ({len(out_lines)} lines)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
