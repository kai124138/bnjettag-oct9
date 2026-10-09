#!/usr/bin/env python3
"""Pass/fail checks for the pilot-program CPU gate Job (standard library only).

python campaigns/pilot1005/gate_check.py threshold --json OUT/threshold.json
python campaigns/pilot1005/gate_check.py cpu-gate --log OUT/cpu_gate.log --exit-code N
python campaigns/pilot1005/gate_check.py nb-pairing --log OUT/nb_pairing.log --exit-code N
python campaigns/pilot1005/gate_check.py pytest --junit OUT/pytest.xml --exit-code N

Each mode prints one line `GATE_CHECK <mode> PASS` or `GATE_CHECK <mode> FAIL <reason>` and exits 0 or 1.
The Job script stops at the first FAIL and prints `GATE_RESULT FAIL <reason>` as its last line.

pytest: the suite must show exactly the known skips and every other collected test passed
(option-(c) review B2, campaigns/2026-10-02-chang-option-c/review/PREFLIGHT_critical_v1.md):
  - failures = errors = 0 and pytest exit 0;
  - exactly EXPECTED_SKIPS skipped tests, each at analysis/test_attn_entropy.py:142 (the C-prime
    main() case, skipped unconditionally);
  - exactly PYTEST_TOTAL tests collected (the count of this tree, measured locally at freeze);
  - every file in REQUIRED has at least one test and all of its tests passed.
cpu-gate: exit 0, `PREFLIGHT_ALL_PASS <N_CONFIGS>`, N_CONFIGS CONFIG_PREFLIGHT_PASS lines, one PID line
  per config, PAIRED_INIT_OK for the E and A07 groups.
threshold: nondegenerate_threshold.py on the cache gives the registered threshold (c) and labels sha.
nb-pairing: pair_nb.py exit 0, NB_PAIRED_OK for seeds 1-8 and NB_PAIRING_ALL_OK 8 ([A22]).
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PYTEST_TOTAL = 166             # collected tests in this tree (local --collect-only at freeze; PREFLIGHT)
EXPECTED_SKIPS = 2
SKIP_SITE = 'analysis/test_attn_entropy.py:142'
REQUIRED = ('tests/test_run_pack.py', 'tests/test_pid_traced_only.py', 'tests/test_option_c_amendment.py',
            'tests/test_pilot1005.py', 'tests/test_pilot_stage.py', 'tests/test_readout_pilot.py',
            'tests/test_gate_check.py', 'tests/test_nb_arm.py', 'tests/test_attn_bit_floor.py',
            'tests/test_pilot_variants_runner.py')
N_CONFIGS = 24
NB_SEEDS = tuple(range(1, 9))
THRESHOLD_C = 0.2109624456315518
LABELS_SHA256 = 'e593f51fad6a19e14c1df783ab762ffd5dfd566b6b1df13ba251a41fa1ad7617'


def case_file(case):
    """tests/test_x.py from a junit testcase: pytest writes classname 'tests.test_x' or
    'tests.test_x.ClassName'; the file attribute is used when present."""
    if case.get('file'):
        return case.get('file')
    parts = case.get('classname', '').split('.')
    for cut in range(len(parts), 0, -1):
        if parts[cut - 1].startswith('test_'):
            return '/'.join(parts[:cut]) + '.py'
    return case.get('classname', '')


def check_pytest(junit, exit_code, total=PYTEST_TOTAL):
    root = ET.parse(junit).getroot()
    cases = list(root.iter('testcase'))
    outcome = {}
    skipped = []
    for case in cases:
        key = f"{case_file(case)}::{case.get('name')}"
        if case.find('failure') is not None or case.find('error') is not None:
            outcome[key] = 'failed'
        elif case.find('skipped') is not None:
            node = case.find('skipped')
            outcome[key] = 'skipped'
            skipped.append((key, (node.get('message') or '') + ' ' + (node.text or '')))
        else:
            outcome[key] = 'passed'
    failed = [k for k, v in outcome.items() if v == 'failed']
    suite_errors = sum(int(s.get('errors', 0)) for s in root.iter('testsuite'))
    if failed:
        return f'{len(failed)} failed: {",".join(failed[:5])}'
    if suite_errors:
        return f'{suite_errors} collection/suite errors'
    if exit_code != 0:
        return f'pytest exit {exit_code}'
    if len(skipped) != EXPECTED_SKIPS:
        return f'{len(skipped)} skipped, expected {EXPECTED_SKIPS}: {[k for k, _ in skipped]}'
    stray = [k for k, text in skipped if SKIP_SITE not in text or not k.startswith('analysis/test_attn_entropy.py::')]
    if stray:
        return f'unexpected skip: {stray}'
    if len(outcome) != total:
        return f'{len(outcome)} tests collected, expected {total}'
    for name in REQUIRED:
        mine = {k: v for k, v in outcome.items() if k.startswith(name + '::')}
        if not mine or any(v != 'passed' for v in mine.values()):
            return f'required file {name}: {len(mine)} tests, not all passed'
    return None


def check_cpu_gate(log, exit_code):
    lines = Path(log).read_text().splitlines()
    if exit_code != 0:
        return f'cpu_gate exit {exit_code}'
    if f'PREFLIGHT_ALL_PASS {N_CONFIGS} production 0 pilot_only {N_CONFIGS}' not in lines:
        return 'no PREFLIGHT_ALL_PASS line for all configs'
    n_pass = sum(line.startswith('CONFIG_PREFLIGHT_PASS ') for line in lines)
    n_pid = sum(line.startswith(('PID_TRACED_ONLY_OK ', 'PID_HISTORICAL_INPUT_OK ')) for line in lines)
    groups = {line.split()[1] for line in lines if line.startswith('PAIRED_INIT_OK ')}
    if n_pass != N_CONFIGS or n_pid != N_CONFIGS:
        return f'{n_pass} CONFIG_PREFLIGHT_PASS, {n_pid} PID lines, expected {N_CONFIGS}'
    if groups != {'E', 'A07'}:
        return f'PAIRED_INIT_OK groups {sorted(groups)}'
    return None


def check_nb_pairing(log, exit_code):
    lines = Path(log).read_text().splitlines()
    if exit_code != 0:
        return f'pair_nb exit {exit_code}'
    seeds = sorted(int(line.split()[1]) for line in lines if line.startswith('NB_PAIRED_OK '))
    if tuple(seeds) != NB_SEEDS or f'NB_PAIRING_ALL_OK {len(NB_SEEDS)}' not in lines:
        return f'NB pairing seeds {seeds}, expected {list(NB_SEEDS)}'
    return None


def check_threshold(path):
    rule = json.loads(Path(path).read_text())
    if rule.get('val_accuracy_threshold') != THRESHOLD_C:
        return f"threshold {rule.get('val_accuracy_threshold')} != {THRESHOLD_C}"
    if rule.get('labels_sha256') != LABELS_SHA256:
        return f"labels sha {rule.get('labels_sha256')} != {LABELS_SHA256}"
    return None


def main(argv=None):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('pytest')
    p.add_argument('--junit', required=True)
    p.add_argument('--exit-code', type=int, required=True)
    p.add_argument('--total', type=int, default=PYTEST_TOTAL)
    c = sub.add_parser('cpu-gate')
    c.add_argument('--log', required=True)
    c.add_argument('--exit-code', type=int, required=True)
    n = sub.add_parser('nb-pairing')
    n.add_argument('--log', required=True)
    n.add_argument('--exit-code', type=int, required=True)
    t = sub.add_parser('threshold')
    t.add_argument('--json', required=True)
    args = ap.parse_args(argv)
    try:
        if args.mode == 'pytest':
            problem = check_pytest(args.junit, args.exit_code, args.total)
        elif args.mode == 'cpu-gate':
            problem = check_cpu_gate(args.log, args.exit_code)
        elif args.mode == 'nb-pairing':
            problem = check_nb_pairing(args.log, args.exit_code)
        else:
            problem = check_threshold(args.json)
    except (OSError, ValueError, ET.ParseError) as exc:
        problem = f'unreadable input: {type(exc).__name__}: {exc}'
    print(f'GATE_CHECK {args.mode} ' + ('PASS' if problem is None else f'FAIL {problem}'), flush=True)
    return 0 if problem is None else 1


if __name__ == '__main__':
    sys.exit(main())
