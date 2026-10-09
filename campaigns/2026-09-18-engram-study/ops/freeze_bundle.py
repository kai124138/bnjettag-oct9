#!/usr/bin/env python3
"""Freeze audited current code and prepare manifests locally. Never submits them."""
import base64
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[3]
CODE = ROOT / 'publication/code/hgq2'
OUT = Path(__file__).resolve().parent
STUDY = '/data/engram-study-20260918'


def write(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2) + '\n')


def main():
    entries = {}
    for path in sorted(CODE.rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts and path.suffix in ('.py', '.json', '.sh', '.md'):
            assert not path.is_symlink()
            entries[path.relative_to(CODE).as_posix()] = path.read_bytes()
    requirements = (ROOT / 'publication/requirements-training.txt').read_bytes()
    entries['requirements-training.txt'] = requirements
    entries['requirements-cpu.txt'] = requirements.replace(b'tensorflow[and-cuda]', b'tensorflow')
    for name in ('private_project.py', 'preflight_production.py'):
        entries['ops/' + name] = (OUT / name).read_bytes()
    for name in ('ENGRAM_HYPOTHESES_AND_ABSTRACT.md', 'ENGRAM_RESEARCH_AND_RUNBOOK.md'):
        entries['study/' + name] = (ROOT / 'publication/docs' / name).read_bytes()
    raw = io.BytesIO()
    with gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped:
        with tarfile.open(fileobj=zipped, mode='w') as archive:
            for name, content in sorted(entries.items()):
                member = tarfile.TarInfo('hgq2/' + name)
                member.size, member.mode, member.mtime = len(content), 0o644, 0
                archive.addfile(member, io.BytesIO(content))
    archive = raw.getvalue()
    sha = hashlib.sha256(archive).hexdigest()
    cmname = 'kai-engram-code-' + sha[:10]
    cm = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': cmname,
        'namespace': 'cms-ml', 'labels': {'app': 'kai-engram'},
        'annotations': {'bnjettag/code-sha256': sha}}, 'immutable': True,
        'binaryData': {'hgq2.tar.gz': base64.b64encode(archive).decode()}}
    assert len(json.dumps(cm).encode()) < 1000000
    (OUT / 'hgq2.tar.gz').write_bytes(archive)
    write('code-configmap.json', cm)
    write('bundle-manifest.json', {'code_sha256': sha, 'configmap': cmname,
        'file_sha256': {n: hashlib.sha256(c).hexdigest() for n, c in entries.items()},
        'study_document_sha256': {n: hashlib.sha256(c).hexdigest()
                                 for n, c in entries.items() if n.startswith('study/')},
        'arms': [f'engram-e{i:02d}-s1' for i in range(4)], 'stop_after': 100,
        'full_schedule_epochs': 1000, 'parallelism': 4, 'synthesis': False})
    setup = f'''set -euo pipefail
export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_FORCE_GPU_ALLOW_GROWTH=true
export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p /work/code
echo '{sha}  /cmcode/hgq2.tar.gz' | sha256sum -c -
tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1
export PYTHONPATH=/work/code BNHGQ2_CODE_SHA256={sha}
'''
    base = json.loads((ROOT / 'local/training-batch-20260918/launch/job.json').read_text())
    job = copy.deepcopy(base)
    labels = {'app': 'kai-engram-screen', 'campaign': 'engram-study-20260918'}
    job['metadata'] = {'name': 'kai-engram-screen-e100-' + sha[:8], 'namespace': 'cms-ml', 'labels': labels}
    job['spec'].update(completions=4, parallelism=4, maxFailedIndexes=3,
                       activeDeadlineSeconds=86400)
    job['spec']['template']['metadata'] = {'labels': labels}
    spec = job['spec']['template']['spec']
    for expression in spec['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'][0]['matchExpressions']:
        if expression['key'] == 'kubernetes.io/hostname':
            expression['values'] = sorted(set(expression['values'] + [
                'k8s-chase-ci-07.calit2.optiputer.net', 'ren-gp-argo-01.madren.org']))
    for volume in spec['volumes']:
        if volume['name'] == 'code':
            volume['configMap']['name'] = cmname
    container = spec['containers'][0]
    container['args'] = [setup + f'''
export WANDB_ENTITY=kayamaguchi-uc-san-diego WANDB_PROJECT=BNJetTag-Engram-Experimental
export WANDB_GROUP=engram-screen WANDB_MODE=online WANDB_TAGS=engram,pilot,l1x3,n16,validation-only
export WANDB_DIR=/work WANDB_CACHE_DIR=/work/wandb-cache WANDB_DATA_DIR=/work/wandb-data
export WANDB_DISABLE_CODE=true WANDB_QUIET=true
pip install -q --no-cache-dir -r /work/code/requirements-training.txt
NVLIBS=$(python -c "import glob; print(':'.join(sorted(glob.glob('/usr/local/lib/python*/site-packages/nvidia/*/lib'))))")
export LD_LIBRARY_PATH="$NVLIBS${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}"
python /work/code/ops/private_project.py
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python -c "import tensorflow as tf; assert tf.config.list_physical_devices('GPU'); print('GPU_GATE_PASS')"
ARM=$(python -c "import os; i=int(os.environ['JOB_COMPLETION_INDEX']); assert 0<=i<4; print(f'engram-e{{i:02d}}-s1')")
timeout --signal=TERM --kill-after=180s 82800s python -u /work/code/run_engram.py train --config /work/code/configs/engram/$ARM.json --data-cache /data/batch20260917/n16/data --out {STUDY}/runs/$ARM --stop-after 100 --track
''']
    write('gpu-job.json', job)
    preflight = copy.deepcopy(job)
    preflight['metadata'] = {'name': 'kai-engram-preflight-' + sha[:8], 'namespace': 'cms-ml', 'labels': {'app': 'kai-engram-preflight'}}
    preflight['spec'] = {k: v for k, v in preflight['spec'].items() if k in ('template', 'ttlSecondsAfterFinished')}
    preflight['spec'].update(backoffLimit=0, activeDeadlineSeconds=3600)
    p = preflight['spec']['template']
    p['metadata'] = {'labels': {'app': 'kai-engram-preflight'}}
    p['spec']['affinity'] = {'nodeAffinity': {
        'requiredDuringSchedulingIgnoredDuringExecution': {'nodeSelectorTerms': [{
            'matchExpressions': [{'key': 'kubernetes.io/hostname', 'operator': 'NotIn',
                'values': ['nautilus-ext-gpu01.fullerton.edu',
                           'k8s-chase-ci-07.calit2.optiputer.net',
                           'ren-gp-argo-01.madren.org']}]}]}}}
    c = p['spec']['containers'][0]
    c.pop('env', None)
    c['name'] = 'preflight'
    c['resources'] = {side: {'cpu': '2', 'memory': '8Gi', 'ephemeral-storage': '8Gi'} for side in ('requests', 'limits')}
    c['args'] = [setup + f'''
export CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled TF_CPP_MIN_LOG_LEVEL=2
pip install -q --no-cache-dir -r /work/code/requirements-cpu.txt
python -u /work/code/run_engram.py preflight --out {STUDY}/preflight/synthetic-{sha[:8]}
python -u /work/code/ops/preflight_production.py
''']
    write('preflight-job.json', preflight)
    print(json.dumps({'configmap': cmname, 'sha256': sha, 'bytes': len(archive)}, indent=2))


if __name__ == '__main__':
    main()
