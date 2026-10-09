"""SIMULATED candidate tools for harness tests (not language models).

sim_candidate.py implement <mode>   run in the workspace: edits per mode (ok | protected | none)
sim_candidate.py review <verdict>   writes $HARNESS_VERDICT
sim_candidate.py check <node> <ok|fail>
sim_candidate.py prepare <node> <attempt>   prepares a handoff for the committed HEAD
"""
import json
import os
import subprocess
import sys
from pathlib import Path

cmd = sys.argv[1]
if cmd == 'implement':
    mode = sys.argv[2]
    if mode == 'ok':
        Path('code/scales.py').write_text('SCALE = 1.0  # simulated candidate change\n')
    elif mode == 'protected':
        Path('tools/check.py').write_text('# tampered\n')
    print(f'simulated implementation: {mode}')
elif cmd == 'review':
    Path(os.environ['HARNESS_VERDICT']).write_text(json.dumps({'verdict': sys.argv[2], 'findings': ['simulated']}))
elif cmd == 'check':
    # the real check prints the node id in lower case
    print(f'CANDIDATE_CHECK_PASS {sys.argv[2].lower()} simulated' if sys.argv[3] == 'ok' else 'TESTS_FAILED simulated')
    sys.exit(0 if sys.argv[3] == 'ok' else 1)
elif cmd == 'prepare':
    br = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], capture_output=True, text=True).stdout.strip()
    if br != f'cand-{sys.argv[2].lower()}':           # as prepare_candidate_d350.py requires
        sys.exit(f'branch cand-{sys.argv[2].lower()} is not checked out (on {br})')
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
    env = dict(os.environ, DEMO_CODE_COMMIT=head, DEMO_NAME_SUFFIX=f'-{sys.argv[2].lower()}',
               DEMO_JOB_DEADLINE='1200')
    out = subprocess.run([sys.executable, 'tools/prepare.py', sys.argv[3]], env=env, capture_output=True, text=True)
    sys.stdout.write(out.stdout)
    sys.stderr.write(out.stderr)
    sys.exit(out.returncode)
