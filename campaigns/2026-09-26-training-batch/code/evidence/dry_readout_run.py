"""Run a readout Job's own bash script locally on the dry-run layout (`dry_readout_build.py`).

    python3 dry_readout_run.py MANIFEST.json DRY_ROOT BUNDLE_TARBALL UVPY_SHIM

The container script is taken verbatim from the manifest; only these substitutions are made:
`/data/chang-n64-20260926` -> DRY_ROOT/chang-n64-20260926, `/work` -> DRY_ROOT/work-<job>,
`/cmcode/hgq2.tar.gz` -> BUNDLE_TARBALL, the `pip install` line removed (the pinned
interpreter comes from UVPY_SHIM, a `uv run --with <pins> python` wrapper, placed on PATH as
`python`), and `sha256sum` provided as a shim over `shasum -a 256` (macOS). Everything else,
including the bundle sha check, the MANIFEST_SHA check, the snapshot gate, certify_ebops.main(),
attn_entropy.py and the exit logic, runs as written. CPU, synthetic; nothing is a result.
"""
import json
import os
import re
from pathlib import Path
import subprocess
import sys

manifest, dry, tarball, uvpy = (Path(a).resolve() for a in sys.argv[1:5])
job = json.loads(manifest.read_text())
name = job['metadata']['name']
script = job['spec']['template']['spec']['containers'][0]['args'][0]
work = dry / f'work-{name}'
shims = dry / f'shims-{name}'
for d in (work, shims):
    d.mkdir(parents=True, exist_ok=True)
(shims / 'python').write_text(f'#!/bin/bash\nexec "{uvpy}" "$@"\n')
(shims / 'sha256sum').write_text('#!/bin/bash\nexec shasum -a 256 "$@"\n')
for f in shims.iterdir():
    f.chmod(0o755)
lines = [ln for ln in script.splitlines() if not ln.startswith('pip install')]
assert len(lines) == len(script.splitlines()) - 1, 'expected exactly one pip install line'
local = '\n'.join(lines) + '\n'
local = (local.replace('/data/chang-n64-20260926', str(dry / 'chang-n64-20260926'))
              .replace('/cmcode/hgq2.tar.gz', str(tarball))
              .replace('/work', str(work)))
# an absolute /data/ path left over (the cache's own `n64/data/` subdirectory is not one)
assert not re.search(r'(?<![\w.-])/data/', local.replace(str(dry), 'DRY')), 'unsubstituted /data path'
(dry / f'{name}.local.sh').write_text(local)
env = {**os.environ, 'PATH': f'{shims}:{os.environ["PATH"]}'}
print('DRY_RUN_JOB', name, flush=True)
rc = subprocess.run(['bash', '-c', local], env=env).returncode
print('DRY_RUN_EXIT', name, rc, flush=True)
sys.exit(rc)
