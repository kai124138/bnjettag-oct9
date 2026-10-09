#!/usr/bin/env python3
"""Repair test for this campaign (BRIEF repair_test_command). Run in code/ after an agent repair.

python3 tools/repair_check_d350.py <failed job name>

1. Scientific-setting fingerprint (first, about 1 minute): the CPU gate (campaigns/d350/cpu_gate.py) is re-run for the
   failed job's arm, and every field it reports for that job's config must equal the frozen
   fingerprint in settings/ (learning rate at the schedule landmarks, optimizer, one training
   step at the config's batch size (loss and EBOPs after it), parameter count, initial kernel
   hashes, initial and 0-bit-floor EBOPs, quantizer decay speeds, trace cadence, and the PID-input
   assertions the gate makes). A difference means the repair changed what is being trained, which
   is a new experiment, not a repair: exit 4 with SCIENTIFIC_SETTING_CHANGED.
2. The copied training tree's test suite must pass (pytest -q -x tests; about 9 minutes).
Not covered: PID gains and data handling beyond what one training step exercises.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

CDIR = Path(__file__).resolve().parents[1]
CODE = CDIR / 'code'
PY = '/home/kaimoe/lab/.venvs/preflight-20261001/bin/python'


def main():
    job = sys.argv[1]
    rec = next((json.loads(p.read_text()) for p in sorted((CDIR / 'attempts').glob('*.json'))
                if json.loads(p.read_text()).get('job') == job), None)
    if rec is None:
        sys.exit(f'no attempt record for job {job}')
    env = dict(os.environ, PYTHONPATH=str(CODE), KERAS_BACKEND='tensorflow')
    frozen = {}
    for f in sorted((CDIR / 'settings').glob('*.json')):
        frozen.update({r['name']: r for r in json.loads(f.read_text())})
    name = rec['config_name']
    if name not in frozen:
        sys.exit(f'no frozen settings fingerprint for {name}; refusing to accept a repair')
    arm = frozen[name]['arm']
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'gate.json'
        g = subprocess.run([PY, 'campaigns/d350/cpu_gate.py', '--only', arm, '--out', str(out)],
                           cwd=CODE, env=env, capture_output=True, text=True)
        if g.returncode != 0 or not out.exists():
            print(g.stdout[-2000:] + g.stderr[-2000:])
            print(f'GATE_FAILED exit={g.returncode}')
            sys.exit(1)
        now = {r['name']: r for r in json.loads(out.read_text())}
    if name not in now:
        print(f'SCIENTIFIC_SETTING_CHANGED {name}: config no longer produced by the gate')
        sys.exit(4)
    diff = sorted(k for k in set(frozen[name]) | set(now[name]) if frozen[name].get(k) != now[name].get(k))
    if diff:
        print(f'SCIENTIFIC_SETTING_CHANGED {name}: ' + ', '.join(
            f'{k}: {frozen[name].get(k)!r} -> {now[name].get(k)!r}' for k in diff[:12]))
        sys.exit(4)
    t = subprocess.run([PY, '-m', 'pytest', '-q', '-x', 'tests'], cwd=CODE, env=env)
    if t.returncode != 0:
        print(f'TESTS_FAILED exit={t.returncode}')
        sys.exit(1)
    print(f'REPAIR_CHECK_PASS {name} tests ok, settings fingerprint unchanged')


if __name__ == '__main__':
    main()
