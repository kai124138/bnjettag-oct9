"""Freeze final current code+configs into an immutable, content-addressed bundle.

Run only after code owners confirm final edits. Generates files locally; remote
submission uses kubectl create explicitly after reviewing the manifest.
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


def main():
    configs = sorted((CODE / 'configs/batch20260917').glob('*.json'))
    assert len(configs) == 12
    for p in configs:
        json.loads(p.read_text())
    for required in ('run_batch_screen.py', 'check_training_batch_preflight.py'):
        assert (CODE / required).exists(), required
    entries = {}
    for p in sorted(CODE.rglob('*')):
        if p.is_file() and '__pycache__' not in p.parts and p.suffix in ('.py', '.json', '.sh', '.md'):
            assert not p.is_symlink(), p
            entries[p.relative_to(CODE).as_posix()] = p.read_bytes()
    requirements = (ROOT / 'publication/requirements-training.txt').read_bytes()
    entries['requirements-training.txt'] = requirements
    entries['requirements-cpu.txt'] = requirements.replace(b'tensorflow[and-cuda]', b'tensorflow')
    entries['launch/prepare_batch_cache.py'] = (OUT / 'prepare_batch_cache.py').read_bytes()
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
    name = 'kai-batch0917-code-' + sha[:10]
    cm = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': name, 'namespace': 'cms-ml',
          'labels': {'app': 'kai-batch0917'}, 'annotations': {'bnjettag/code-sha256': sha}},
          'immutable': True, 'binaryData': {'hgq2.tar.gz': base64.b64encode(archive).decode()}}
    assert len(json.dumps(cm).encode()) < 1000000, 'ConfigMap must remain below 1MB'
    (OUT / 'hgq2.tar.gz').write_bytes(archive)
    (OUT / 'code-configmap.json').write_text(json.dumps(cm, indent=2) + '\n')
    provenance = {'code_sha256': sha, 'configmap': name, 'archive_bytes': len(archive),
                  'file_sha256': {k: hashlib.sha256(v).hexdigest() for k, v in sorted(entries.items())},
                  'requirements_cpu_note': 'Identical pinned versions; CUDA extra omitted because preflight has no GPU.'}
    (OUT / 'bundle-manifest.json').write_text(json.dumps(provenance, indent=2) + '\n')
    command = f'''set -euo pipefail
export KERAS_BACKEND=tensorflow CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled
export TF_CPP_MIN_LOG_LEVEL=2 OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1
export BNHGQ2_CODE_SHA256={sha}
mkdir -p /work/code
printf '%s  %s\\n' '{sha}' '/cmcode/hgq2.tar.gz' | sha256sum -c -
tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1
export PYTHONPATH=/work/code
pip install -q --no-cache-dir -r /work/code/requirements-cpu.txt
python -u /work/code/launch/prepare_batch_cache.py --configs /work/code/configs/batch20260917 --root /data/batch20260917 --raw /data/hls4ml_lhc_jet/train/train
python -u /work/code/check_training_batch_preflight.py --configs /work/code/configs/batch20260917 --output /data/batch20260917/preflight-result.json
'''
    job = {'apiVersion': 'batch/v1', 'kind': 'Job',
           'metadata': {'name': 'kai-batch0917-preflight-' + sha[:8], 'namespace': 'cms-ml', 'labels': {'app': 'kai-batch0917-preflight'}},
           'spec': {'backoffLimit': 0, 'activeDeadlineSeconds': 1800, 'ttlSecondsAfterFinished': 86400,
             'template': {'metadata': {'labels': {'app': 'kai-batch0917-preflight'}}, 'spec': {
               'restartPolicy': 'Never', 'nodeSelector': {'kubernetes.io/arch': 'amd64'},
               'containers': [{'name': 'preflight', 'image': 'python:3.12', 'command': ['bash', '-c'], 'args': [command],
                  'resources': {'requests': {'cpu': '2', 'memory': '8Gi', 'ephemeral-storage': '8Gi'},
                                'limits': {'cpu': '2', 'memory': '8Gi', 'ephemeral-storage': '8Gi'}},
                  'volumeMounts': [{'name': 'code', 'mountPath': '/cmcode', 'readOnly': True},
                                   {'name': 'work', 'mountPath': '/work'}, {'name': 'data', 'mountPath': '/data'}]}],
               'volumes': [{'name': 'code', 'configMap': {'name': name}}, {'name': 'work', 'emptyDir': {'sizeLimit': '8Gi'}},
                           {'name': 'data', 'persistentVolumeClaim': {'claimName': 'kai-data'}}]}}}}
    (OUT / 'preflight-job.json').write_text(json.dumps(job, indent=2) + '\n')
    print(json.dumps({k: v for k, v in provenance.items() if k != 'file_sha256'}, indent=2))

if __name__ == '__main__':
    main()
