#!/usr/bin/env python3
"""Option-(c) pilot reader: canary, controller audit and at-target monitoring from one run's
`pid_telemetry.jsonl` (standard library only; reads no model, array or W&B).

python campaigns/chang1002c/monitor_c.py --config configs/<run>.json --telemetry <run>/pid_telemetry.jsonl [--json OUT]

Canary (STUDY lines 1855-1865, cadence-adjusted by the option-(c) amendment):
  CANARY_LOSS        loss finite on every epoch present; for arms A and D, loss at one-based
                     epoch 10 (zero-based 9) below one-based epoch 1 (zero-based 0)
  CANARY_TRACE       traced cost at zero-based 9 below zero-based 0
  CANARY_PID_E11     at one-based epoch 11 (zero-based 10): stepped, span 9, input equal to the
                     zero-based-9 trace (rel 1e-6), per_epoch integral = previous + 9 x error,
                     beta = clamp(10 ** (p x error + i x integral)) and beta moved from its value
                     at the end of zero-based 9. Seeding at zero-based 1 is not evidence of feedback.
Controller audit (every epoch present): held epochs keep beta, integral and previous error;
stepped epochs at or after warmup consume the most recent trace.
At-target monitoring (report only, never a stop by itself): per traced epoch the budget,
feasibility, degenerate-under-budget (budget met, accuracy at or below the registered threshold
or not above the 0-bit floor), Q/K all-0-bit attention, beta at a bound. NOTIFY lines are for
the operator and Kai; this script mutates nothing.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

REL = 1e-6


def close(a, b, rel):
    return a is not None and b is not None and abs(a - b) <= rel * max(abs(b), 1e-300)


def load(path):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    epochs = [r['epoch'] for r in rows]
    assert epochs == list(range(len(rows))), 'telemetry epochs must be contiguous from 0'
    return rows


def canary(cfg, rows):
    pid = cfg['train']['ebops']['pid']
    out = {}
    arm = cfg['campaign']['arm']
    losses = [r['loss'] for r in rows]
    finite = all(isinstance(v, (int, float)) and math.isfinite(v) for v in losses)
    if len(rows) >= 10:
        falling = rows[9]['loss'] < rows[0]['loss']
        out['CANARY_LOSS'] = finite and (falling if arm in ('A', 'D') else True)
        out['CANARY_TRACE'] = (rows[0]['ebops_traced'] is not None and rows[9]['ebops_traced'] is not None
                               and rows[9]['ebops_traced'] < rows[0]['ebops_traced'])
    if len(rows) >= 11:
        e, prev = rows[10], rows[9]
        err = e['pid_error']
        beta = None if err is None else 10 ** (pid['p'] * err + pid['i'] * e['pid_integral'])
        beta = None if beta is None else min(max(beta, pid.get('min_beta', 0.0)), pid.get('max_beta', math.inf))
        checks = {
            'stepped': e['pid_stepped'] == 1, 'span9': e['pid_step_span'] == 9,
            'input_is_trace': close(e['pid_input'], prev['ebops_traced'], REL),
            'error': err is not None and close(err, math.log10(e['pid_input'] / e['pid_target_ebops']), 1e-9),
            'integral': err is not None and close(e['pid_integral'], prev['pid_integral'] + 9 * err, 1e-9),
            'beta_formula': close(e['beta_after_step'], beta, 1e-9),
            'beta_moved': e['beta_after_step'] != prev['beta_end'],
        }
        out['CANARY_PID_E11'] = all(checks.values())
        out['CANARY_PID_E11_detail'] = checks
        if e['beta_after_step'] > 0 and prev['beta_end'] > 0:
            out['beta_log10_change_e11'] = math.log10(e['beta_after_step']) - math.log10(prev['beta_end'])
    return out


def audit(cfg, rows):
    warmup = int(cfg['train']['ebops']['pid'].get('warmup', 10))
    problems, last_trace = [], None
    for i, r in enumerate(rows):
        if r['pid_stepped'] and r['epoch'] >= warmup:
            if not close(r['pid_input'], last_trace, REL):
                problems.append(f"epoch {r['epoch']}: input {r['pid_input']} != last trace {last_trace}")
        elif not r['pid_stepped'] and i > 0:
            p = rows[i - 1]
            same = (r['beta_after_step'] == p['beta_end'] and r['pid_integral'] == p['pid_integral']
                    and r['pid_prev_error'] == p['pid_prev_error'] and r['pid_input'] is None)
            if not same:
                problems.append(f"epoch {r['epoch']}: held epoch moved controller state")
        if r['ebops_traced_flag']:
            last_trace = r['ebops_traced']
            if not close(r['pid_ebops_end'], last_trace, REL):
                problems.append(f"epoch {r['epoch']}: PID end value differs from trace")
        elif i > 0 and r['pid_ebops_end'] != rows[i - 1]['pid_ebops_end']:
            problems.append(f"epoch {r['epoch']}: PID end value moved on an untraced epoch")
    return problems


def at_target(cfg, rows):
    pid = cfg['train']['ebops']['pid']
    traced = [r for r in rows if r['ebops_traced_flag']]
    degenerate = [r['epoch'] for r in traced if r.get('budget_met') == 1 and r.get('nondegenerate') == 0]
    qk_zero = [r['epoch'] for r in traced if r.get('attn_qk_all_zero') == 1]
    at_bound = [r['epoch'] for r in traced
                if r['beta_end'] <= pid.get('min_beta', 0.0) or r['beta_end'] >= pid.get('max_beta', math.inf)]
    last = traced[-1] if traced else {}
    return {'traced_epochs': len(traced),
            'budget_met': sum(r.get('budget_met') == 1 for r in traced),
            'feasible': sum(r.get('feasible') == 1 for r in traced),
            'feasible_degenerate': len(degenerate), 'first_feasible_degenerate': degenerate[0] if degenerate else None,
            'qk_all_zero_bit': len(qk_zero), 'first_qk_all_zero_bit': qk_zero[0] if qk_zero else None,
            'beta_at_bound': len(at_bound),
            'min_traced_ebops': min((r['ebops_traced'] for r in traced), default=None),
            'last_traced': {k: last.get(k) for k in ('epoch', 'ebops_traced', 'val_categorical_accuracy',
                                                       'val_macro_auc', 'val_accuracy_threshold', 'ebops_above_floor',
                                                       'beta_end', 'attn_zero_bits')}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', type=Path, required=True)
    ap.add_argument('--telemetry', type=Path, required=True)
    ap.add_argument('--json', type=Path)
    args = ap.parse_args(argv)
    cfg = json.loads(args.config.read_text())
    rows = load(args.telemetry)
    report = {'run': cfg['name'], 'epochs_present': len(rows), 'canary': canary(cfg, rows),
              'audit_problems': audit(cfg, rows), 'at_target': at_target(cfg, rows)}
    for key in ('CANARY_LOSS', 'CANARY_TRACE', 'CANARY_PID_E11'):
        if key in report['canary']:
            print(key, cfg['name'], 'PASS' if report['canary'][key] else 'FAIL', flush=True)
    print('CONTROLLER_AUDIT', cfg['name'], 'PASS' if not report['audit_problems'] else 'FAIL',
          len(report['audit_problems']), flush=True)
    t = report['at_target']
    if t['feasible_degenerate']:
        print('NOTIFY_DEGENERATE_UNDER_BUDGET', cfg['name'], 'traced_epochs', t['feasible_degenerate'],
              'first', t['first_feasible_degenerate'], flush=True)
    if t['qk_all_zero_bit']:
        print('NOTIFY_ATTENTION_QK_ZERO_BIT', cfg['name'], 'traced_epochs', t['qk_all_zero_bit'],
              'first', t['first_qk_all_zero_bit'], flush=True)
    if t['beta_at_bound']:
        print('NOTIFY_BETA_AT_BOUND', cfg['name'], 'traced_epochs', t['beta_at_bound'], flush=True)
    if args.json:
        args.json.write_text(json.dumps(report, indent=1) + '\n')
    return report


if __name__ == '__main__':
    main()
