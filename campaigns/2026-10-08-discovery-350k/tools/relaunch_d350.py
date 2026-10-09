#!/usr/bin/env python3
"""Harness prepare step: build the next attempt of the arm a failed Job belongs to.

python3 tools/relaunch_d350.py <failed job name> <attempt> [<failure class>]

Runs in code/ (the workspace). If the working tree has changes (an agent repair that passed the
repair test), they are committed on a new branch `repair-<arm>-a<attempt>` from the failed
attempt's commit, so every relaunched run trains on a recorded commit. Without changes (an
infrastructure relaunch) the failed attempt's own branch is reused. Prints the handoff directory.
"""
import json
import subprocess
import sys
from pathlib import Path

CDIR = Path(__file__).resolve().parents[1]
CODE = CDIR / 'code'


IDENTITY = ['-c', 'user.name=BNJetTag harness', '-c', 'user.email=harness@bnjettag.local']


def git(*args):
    return subprocess.run(['git', '-C', str(CODE), *IDENTITY, *args], capture_output=True,
                          text=True, check=True).stdout


def main():
    job, attempt = sys.argv[1], int(sys.argv[2])
    rec = next((json.loads(p.read_text()) for p in sorted((CDIR / 'attempts').glob('*.json'))
                if json.loads(p.read_text()).get('job') == job), None)
    if rec is None:
        sys.exit(f'no attempt record for job {job}')
    head = git('rev-parse', 'HEAD').strip()
    if head != rec['commit']:
        sys.exit(f'workspace HEAD {head[:12]} is not the failed attempt commit {rec["commit"][:12]}; '
                 'refusing to build a relaunch from unrecorded code')
    cls = sys.argv[3] if len(sys.argv) > 3 else ''
    base = [sys.executable, str(CDIR / 'tools/prepare_attempt.py'), rec['arm'], str(attempt),
            '--stage', rec['stage'], '--stop-epoch', str(rec['stop_epoch'])]
    if git('status', '--porcelain').strip():
        # A repair changed code: commit it on its own branch and start a fresh run, so no run
        # mixes code versions.
        branch = f"repair-{rec['arm']}-a{attempt}"
        git('checkout', '-b', branch)          # from the detached failed-attempt commit
        git('add', '-A')
        git('commit', '-m', f'repair of {job} for attempt {attempt} (harness task)')
        out = subprocess.run(base + ['--branch', branch], capture_output=True, text=True)
    else:
        # No code change (infrastructure or deadline): same commit, on a branch pinned to it.
        branch = f"relaunch-{rec['arm']}-a{attempt}"
        git('branch', '-f', branch, rec['commit'])
        out = None
        if cls in ('infra', 'relaunch', 'deadline'):
            out = subprocess.run(base + ['--branch', branch, '--resume-from', rec['run_name']],
                                 capture_output=True, text=True)
            if out.returncode != 0:
                sys.stderr.write('resume not possible, starting a fresh run: ' + out.stderr[-500:])
                out = None
        if out is None:
            out = subprocess.run(base + ['--branch', branch], capture_output=True, text=True)
    sys.stdout.write(out.stdout)
    sys.stderr.write(out.stderr)
    sys.exit(out.returncode)


if __name__ == '__main__':
    main()
