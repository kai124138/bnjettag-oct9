"""SIMULATED agent for the recovery demo. Not a language model: it applies a scripted fix when
the failure log names the batch_size problem, and reports what it did."""
import json
import os
import sys
from pathlib import Path

log = (Path(os.environ['HARNESS_EVIDENCE']) / 'pod.log').read_text()
if 'batch_size=0' not in log:
    print('simulated agent: failure not recognised; no change')
    sys.exit(0)
cfg_path = Path('code/config.json')
cfg = json.loads(cfg_path.read_text())
cfg['batch_size'] = 50
cfg_path.write_text(json.dumps(cfg) + '\n')
print('simulated agent: log shows batch_size=0 gives zero steps; set batch_size to 50 in '
      'code/config.json. Uncertainty: 50 is a scripted value, not a tuned one.')
