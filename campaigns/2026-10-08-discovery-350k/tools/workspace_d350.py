#!/usr/bin/env python3
"""Harness workspace step: check out the failed attempt's exact commit in code/ before an agent
repairs it. Refuses when the working tree has uncommitted changes (nothing is discarded)."""
import json
import subprocess
import sys
from pathlib import Path

CDIR = Path(__file__).resolve().parents[1]
CODE = CDIR / 'code'


def git(*args):
    return subprocess.run(['git', '-C', str(CODE), *args], capture_output=True, text=True, check=True).stdout


job = sys.argv[1]
rec = next((json.loads(p.read_text()) for p in sorted((CDIR / 'attempts').glob('*.json'))
            if json.loads(p.read_text()).get('job') == job), None)
if rec is None:
    sys.exit(f'no attempt record for job {job}')
if git('status', '--porcelain').strip():
    sys.exit('workspace has uncommitted changes; refusing to switch commits')
git('checkout', '-q', '--detach', rec['commit'])
print(f"workspace at {rec['commit'][:12]} for {job}")
