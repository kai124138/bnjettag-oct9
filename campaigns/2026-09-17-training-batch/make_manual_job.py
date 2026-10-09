#!/usr/bin/env python3
"""Print one resumable, single-GPU Job manifest. Never submit a workload."""
import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--index', type=int, required=True, choices=range(12))
parser.add_argument('--stop-after', type=int, default=100, choices=(100, 200, 400))
parser.add_argument('--name', required=True)
args = parser.parse_args()
if not re.fullmatch(r'kai-[a-z0-9-]{1,58}[a-z0-9]', args.name):
    parser.error('Use a unique lowercase kai- Job name, at most 63 characters')
source = Path(__file__).resolve().parent / 'launch/gpu-screen-job.json'
job = json.loads(source.read_text())
job['metadata']['name'] = args.name
labels = {'app': 'kai-batch0917-manual', 'campaign': 'batch20260917',
          'arm': f'a{args.index:02d}'}
job['metadata']['labels'] = labels
spec = job['spec']
spec.update(completionMode='NonIndexed', completions=1, parallelism=1,
            backoffLimit=0, activeDeadlineSeconds=86400)
for key in ('backoffLimitPerIndex', 'maxFailedIndexes'):
    spec.pop(key, None)
spec['template']['metadata']['labels'] = labels.copy()
container = spec['template']['spec']['containers'][0]
old = 'run_batch_screen.py --root /data/batch20260917 --stop-after 100'
new = (f'run_batch_screen.py --root /data/batch20260917 '
       f'--index {args.index} --stop-after {args.stop_after}')
assert container['args'][0].count(old) == 1
container['args'][0] = container['args'][0].replace(old, new)
print(json.dumps(job, indent=2))
