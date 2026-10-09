"""Build a run_handoff record for attempt N from the current code/ directory."""
import argparse
import base64
import importlib.util
import io
import json
import os
import sys
import tarfile
from pathlib import Path

ws = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('run_handoff', os.environ['RUN_HANDOFF'])
rh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rh)
attempt = int(sys.argv[1])
buf = io.BytesIO()
with tarfile.open(fileobj=buf, mode='w:gz') as tar:
    for p in sorted((ws / 'code').rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts:
            info = tarfile.TarInfo('code/' + str(p.relative_to(ws / 'code')))
            data = p.read_bytes()
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
payload = buf.getvalue()
name = f'kai-harness-demo-a{attempt}'
source = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
          'metadata': {'name': f'{name}-code', 'namespace': 'cms-ml',
                       'annotations': {rh.PREFIX + 'bundle-sha256': rh.sha(payload)}},
          'binaryData': {'hgq2.tar.gz': base64.b64encode(payload).decode()}}
job = {'apiVersion': 'batch/v1', 'kind': 'Job',
       'metadata': {'name': name, 'namespace': 'cms-ml',
                    'labels': {'user': 'kai', 'campaign': 'harness-demo'},
                    'annotations': {'bnjettag.io/arm': 'demo-a1'}},
       'spec': {'completionMode': 'Indexed', 'completions': 1, 'parallelism': 1,
                'backoffLimitPerIndex': 1,
                'podFailurePolicy': {'rules': [
                    {'action': 'Ignore', 'onPodConditions': [{'type': 'DisruptionTarget'}]},
                    {'action': 'FailIndex', 'onExitCodes': {'containerName': 'train',
                                                            'operator': 'In', 'values': [76, 124]}}]},
                'template': {'metadata': {'labels': {'user': 'kai'}}, 'spec': {
                    'activeDeadlineSeconds': 600, 'automountServiceAccountToken': False,
                    'restartPolicy': 'Never',
                    'containers': [{'name': 'train', 'image': 'python:3.12',
                                    'command': ['python', '/cmcode/code/run.py'],
                                    'resources': {'requests': {'cpu': '1', 'memory': '1Gi'},
                                                  'limits': {'cpu': '1', 'memory': '1Gi',
                                                             'nvidia.com/gpu': '1'}},
                                    'volumeMounts': [{'name': 'persistent', 'mountPath': '/data'},
                                                     {'name': 'code', 'mountPath': '/cmcode',
                                                      'readOnly': True}]}],
                    'volumes': [{'name': 'persistent', 'persistentVolumeClaim': {'claimName': 'kai-data'}},
                                {'name': 'code', 'configMap': {'name': f'{name}-code'}}]}}}}
brief = {'purpose': 'Harness recovery demo (local substitute only)',
         'changes': f'attempt {attempt}', 'approval_ref': 'HARNESS-DEMO',
         'scientific_gate': {'status': 'cleared', 'reference': 'local demo; no physics claim'},
         'runs': [{'name': 'demo', 'config_path': 'code/config.json'}],
         'expected_metrics': [{'name': 'synthetic_mean', 'split': 'synthetic', 'expectation': 'finite'}],
         'stop_rules': [{'condition': 'any failure', 'action': 'notify-only', 'approval_ref': 'HARNESS-DEMO'}],
         'outputs': [f'/data/outputs/{name}']}
if os.environ.get('DEMO_CODE_COMMIT'):           # candidate tests: the commit this handoff packages
    job['metadata']['annotations']['bnjettag.io/code-commit'] = os.environ['DEMO_CODE_COMMIT']
    name_suffix = os.environ.get('DEMO_NAME_SUFFIX', '')
    if name_suffix:
        job['metadata']['name'] = name + name_suffix
if os.environ.get('DEMO_JOB_DEADLINE'):          # hard-bound tests: Job-level deadline
    job['spec']['activeDeadlineSeconds'] = int(os.environ['DEMO_JOB_DEADLINE'])
    job['spec']['podReplacementPolicy'] = 'Failed'
out = Path(os.environ['HANDOFF_ROOT'])
tmp = out / f'.inputs-{attempt}'
tmp.mkdir(parents=True, exist_ok=True)
for fname, obj in [('job.json', job), ('source.json', source), ('brief.json', brief)]:
    (tmp / fname).write_bytes(rh.encoded(obj))
(tmp / 'info.json').write_text('{"array_sha256":{"x":"' + 'a' * 64 + '"},"split_seed":1}\n')
args = argparse.Namespace(job=tmp / 'job.json', configmap=tmp / 'source.json', brief=tmp / 'brief.json',
                          data_info=tmp / 'info.json', data_path='/data/demo/data_info.json', out=out)
rh.prepare(args)
