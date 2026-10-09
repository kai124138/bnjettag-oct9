#!/usr/bin/env python3
"""Run a readout handoff's Job script locally on CPU (PREFLIGHT fixes after review v1, A1).

python run_job_script.py HANDOFF_DIR TREE DATA_PARENT [--out-suffix S]
Takes job.json's container script verbatim and changes only what cannot exist on the home PC:
drops the 4 bundle-install lines (mkdir /work/code, sha256sum -c /cmcode, tar -x, pip install; the
local tree is build_tree.py's TREE_MATCHES copy of the same bundle), maps /work/code -> TREE and
/data/ -> DATA_PARENT/, and runs it with bash on PATH=~/venv-hgq2/bin first. Every export (PYTHONPATH,
BNJ_*, CUDA_VISIBLE_DEVICES=-1, WANDB_MODE), the manifest-sha assertion and every step are kept.
"""
import json, os, re, subprocess, sys
from pathlib import Path
handoff, tree, data = Path(sys.argv[1]), sys.argv[2], sys.argv[3].rstrip('/')
suffix = sys.argv[5] if len(sys.argv) > 5 and sys.argv[4] == '--out-suffix' else ''
job = json.loads((handoff / 'job.json').read_text())
script = job['spec']['template']['spec']['containers'][0]['args'][0]
drop = ('mkdir -p /work/code', "/cmcode/hgq2.tar.gz' | sha256sum -c -", 'tar -xzf /cmcode/', 'pip install ')
kept, dropped = [], []
for line in script.splitlines():
    (dropped if any(d in line for d in drop) else kept).append(line)
assert len(dropped) == 4, dropped
text = re.sub(r'(?<![\w.-])/data/', data + '/', '\n'.join(kept).replace('/work/code', tree))
if suffix:
    text = re.sub(r'(readout-epoch-0500-[0-9a-f]{6}-r1)', r'\1' + suffix, text)
print('DRYRUN_HANDOFF', handoff.name, 'job', job['metadata']['name'], 'dropped', len(dropped), flush=True)
env = {**os.environ, 'PATH': str(Path.home() / 'venv-hgq2/bin') + ':' + os.environ['PATH'], 'PYTHONDONTWRITEBYTECODE': '1'}
for k in ('PYTHONPATH', 'BNJ_DATA_ROOT', 'BNJ_RUN_ROOT', 'BNJ_CAMPAIGN_DIR', 'BNJ_STAGE'):
    env.pop(k, None)
rc = subprocess.run(['bash', '-c', text], env=env).returncode
print('DRYRUN_JOB_EXIT', rc, flush=True)
sys.exit(rc)
