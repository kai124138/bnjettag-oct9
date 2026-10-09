"""Stand-in training task for the recovery demo. Exit 76 marks a deterministic failure."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
config = json.loads((HERE / 'config.json').read_text())
values = [((i * 7919) % 1000) / 1000 for i in range(1000)]
try:
    steps = len(values) // config['batch_size']
except ZeroDivisionError:
    print(f"training setup failed: batch_size={config['batch_size']} in config.json gives no steps",
          file=sys.stderr)
    sys.exit(76)
batch_means = [sum(values[k * config['batch_size']:(k + 1) * config['batch_size']]) /
               config['batch_size'] for k in range(steps)]
result = {'metric': 'synthetic_mean', 'value': round(sum(batch_means) / steps, 6),
          'split': 'synthetic', 'n': len(values), 'status': 'exploratory'}
if '--dry-run' in sys.argv:
    print('dry run ok', result['value'])
    sys.exit(0)
out = Path(os.environ.get('DATA_ROOT', '/data')) / 'outputs' / os.environ['JOB_NAME']
out.mkdir(parents=True, exist_ok=True)
(out / 'metrics.json').write_text(json.dumps(result) + '\n')
print('done', result['value'])
