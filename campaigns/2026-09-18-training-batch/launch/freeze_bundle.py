"""Freeze code+configs for the 20260918 campaign into an immutable ConfigMap and its Job.

Same bundle recipe as ../../training-batch-20260917/launch/freeze_preflight_bundle.py.
The Job is derived from that campaign's working r3 shape (relaunch-job-r3.json): same
GPU pool, known-bad-node exclusion, failure policy, PVC root and N16 data cache; new
ConfigMap, labels, W&B group and campaign index. Nothing is submitted from here.
"""
import base64
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / 'publication/code/hgq2'
OUT = Path(__file__).resolve().parent
PREVIOUS = ROOT / 'local/training-batch-20260917/launch'
CAMPAIGN = 'batch20260918'
STOP_AFTER = 400
PARALLELISM = 15


def main():
    index = json.loads((CODE / 'configs' / CAMPAIGN / 'index.json').read_text())['runs']
    assert len(index) == 15 and len(sorted((CODE / 'configs' / CAMPAIGN).glob('batch*.json'))) == 15
    entries = {}
    for p in sorted(CODE.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py', '.json', '.sh', '.md'):
            assert not p.is_symlink(), p
            entries[p.relative_to(CODE).as_posix()] = p.read_bytes()
    requirements = (ROOT / 'publication/requirements-training.txt').read_bytes()
    entries['requirements-training.txt'] = requirements
    entries['requirements-cpu.txt'] = requirements.replace(b'tensorflow[and-cuda]', b'tensorflow')
    entries['launch/prepare_batch_cache.py'] = (PREVIOUS / 'prepare_batch_cache.py').read_bytes()
    raw = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as tar:
            for name, content in sorted(entries.items()):
                member = tarfile.TarInfo('hgq2/' + name)
                member.size = len(content)
                member.mode = 0o755 if name.endswith('.sh') else 0o644
                member.mtime = 0
                tar.addfile(member, io.BytesIO(content))
    archive = raw.getvalue()
    sha = hashlib.sha256(archive).hexdigest()
    cm_name = 'kai-batch0918-code-' + sha[:10]
    cm = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': cm_name, 'namespace': 'cms-ml',
          'labels': {'app': 'kai-batch0918'}, 'annotations': {'bnjettag/code-sha256': sha}},
          'immutable': True, 'binaryData': {'hgq2.tar.gz': base64.b64encode(archive).decode()}}
    assert len(json.dumps(cm).encode()) < 1000000, 'ConfigMap must remain below 1MB'
    (OUT / 'hgq2.tar.gz').write_bytes(archive)
    (OUT / 'code-configmap.json').write_text(json.dumps(cm, indent=2) + '\n')
    (OUT / 'bundle-manifest.json').write_text(json.dumps(
        {'code_sha256': sha, 'configmap': cm_name, 'archive_bytes': len(archive),
         'file_sha256': {k: hashlib.sha256(v).hexdigest() for k, v in sorted(entries.items())}}, indent=2) + '\n')

    job = json.loads((PREVIOUS / 'relaunch-job-r3.json').read_text())
    labels = {'app': 'kai-batch0918-screen', 'campaign': CAMPAIGN}
    job['metadata'] = {'name': f'kai-batch0918-screen-e{STOP_AFTER}', 'namespace': 'cms-ml', 'labels': labels}
    spec = job['spec']
    spec.update(completions=len(index), parallelism=PARALLELISM)
    spec['template']['metadata'] = {'labels': dict(labels)}
    pod = spec['template']['spec']
    pod['volumes'] = [v if v['name'] != 'code' else {'name': 'code', 'configMap': {'name': cm_name, 'defaultMode': 420}}
                      for v in pod['volumes']]
    container = pod['containers'][0]
    old_sha = 'ddd3761d2a566790b42a1c55c036727df624e58a6f65305c1aeca3d05365584d'
    command = container['args'][0]
    assert command.count(old_sha) == 2
    command = command.replace(old_sha, sha)
    command = command.replace('WANDB_GROUP=batch20260917', f'WANDB_GROUP={CAMPAIGN}')
    command = command.replace('WANDB_TAGS=batch20260917,architecture-screen,l1x3',
                              f'WANDB_TAGS={CAMPAIGN},attention-precision-schedule,l1x3')
    old_run = '/work/code/run_batch_screen.py --root /data/batch20260917 --stop-after 100'
    assert command.count(old_run) == 1
    command = command.replace(old_run, f'/work/code/run_batch_screen.py --campaign {CAMPAIGN} '
                                       f'--root /data/batch20260917 --stop-after {STOP_AFTER}')
    assert 'batch20260917,' not in command and 'GROUP=batch20260917' not in command
    container['args'] = [command]
    (OUT / 'job.json').write_text(json.dumps(job, indent=1) + '\n')
    print(json.dumps({'code_sha256': sha, 'configmap': cm_name, 'job': job['metadata']['name'],
                      'completions': len(index), 'parallelism': PARALLELISM}, indent=2))


if __name__ == '__main__':
    main()
