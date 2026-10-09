#!/usr/bin/env python3
"""Run the unchanged `nrp-lab/nrp_doctor.py lint` on the prepared handoff Jobs without a cluster.

python3 campaigns/2026-10-02-chang-option-c/offline_lint.py

nrp_doctor reads `kubectl get nodes -o json` only to map GPU product labels to resource keys. Here a
temporary stub `kubectl` replays that map from the saved 2026-09-29T07:39:45Z node survey
(campaigns/2026-09-29-gpu-benchmark/code/evidence/node_survey_20260929T073945Z.json; one synthetic
node item per surveyed node, carrying only its product label and resource key). Any other kubectl
call fails. The lint rules are untouched. The live action-time lint by run_handoff launch remains
required; the snapshot says nothing about today's nodes.
Writes lint-offline.log and lint-offline.json beside this file.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SURVEY = REPO / 'campaigns/2026-09-29-gpu-benchmark/code/evidence/node_survey_20260929T073945Z.json'
STUB = '''#!{py}
import json, sys
if sys.argv[1:4] != ['get', 'nodes', '-o'] :
    sys.stderr.write('offline lint stub: only "get nodes -o json" is replayed\\n'); sys.exit(1)
sys.stdout.write(open({nodes!r}).read())
'''


def main():
    survey = json.loads(SURVEY.read_bytes())
    items = []
    for product, entry in survey['products'].items():
        key = entry['resource_keys'][0]
        for node in entry['per_node']:
            items.append({'metadata': {'name': node['node'], 'labels': {'nvidia.com/gpu.product': product}},
                          'status': {'allocatable': {key: '1'}}})
    prepared = json.loads((HERE / 'PREPARED.json').read_text())
    jobs = [str(HERE / v['handoff'] / 'job.json') for v in prepared['jobs'].values()]
    with tempfile.TemporaryDirectory() as tmp:
        nodes = Path(tmp) / 'nodes.json'
        nodes.write_text(json.dumps({'items': items}))
        stub = Path(tmp) / 'kubectl'
        stub.write_text(STUB.format(py=sys.executable, nodes=str(nodes)))
        stub.chmod(0o755)
        env = {**os.environ, 'PATH': f'{tmp}:/usr/bin:/bin'}
        result = subprocess.run([sys.executable, str(REPO / 'nrp-lab/nrp_doctor.py'), 'lint', *jobs],
                                capture_output=True, text=True, env=env, cwd=REPO)
    log = result.stdout + result.stderr + f'exit={result.returncode}\n'
    (HERE / 'lint-offline.log').write_text(log)
    (HERE / 'lint-offline.json').write_text(json.dumps({
        'exit_code': result.returncode, 'meaning': '0 OK, 1 warnings only, 2 errors',
        'node_snapshot': str(SURVEY.relative_to(REPO)), 'node_snapshot_sha256': hashlib.sha256(SURVEY.read_bytes()).hexdigest(),
        'node_snapshot_read_utc': survey['read_utc'], 'synthetic_node_items': len(items),
        'nrp_doctor_sha256': hashlib.sha256((REPO / 'nrp-lab/nrp_doctor.py').read_bytes()).hexdigest(),
        'jobs': {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in jobs}}, indent=1) + '\n')
    print(log, end='')
    return result.returncode


if __name__ == '__main__':
    sys.exit(main())
