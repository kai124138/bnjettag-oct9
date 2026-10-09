"""Freeze a reviewed study bundle and generate CPU/GPU manifests; never submit."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import tarfile

LAB = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CODE = LAB / 'research/bnjettag/code/constituent-study-20260922'
bundle = OUT / 'study-code.tar.gz'
with tarfile.open(bundle, 'w:gz') as archive:
    archive.add(CODE, arcname='code', filter=lambda info: None if '__pycache__' in info.name else info)
sha = hashlib.sha256(bundle.read_bytes()).hexdigest()
cm = 'kai-n8n64-code-' + sha[:10]
labels = {'user': 'kai', 'campaign': 'constituent-study-20260922'}
configmap = {'apiVersion': 'v1', 'kind': 'ConfigMap', 'immutable': True,
             'metadata': {'name': cm, 'namespace': 'cms-ml', 'labels': labels},
             'binaryData': {'hgq2.tar.gz': base64.b64encode(bundle.read_bytes()).decode()}}
(OUT / 'study-configmap.json').write_text(json.dumps(configmap) + '\n')

header = f'''set -euo pipefail
export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_FORCE_GPU_ALLOW_GROWTH=true TF_CPP_MIN_LOG_LEVEL=2
export NVIDIA_TF32_OVERRIDE=0
export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p /work/code
echo '{sha}  /cmcode/hgq2.tar.gz' | sha256sum -c -
tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1
export PYTHONPATH=/work/code BNHGQ2_CODE_SHA256={sha}
'''
gpu = '''export WANDB_ENTITY=kayamaguchi-uc-san-diego WANDB_PROJECT=BNJetTag-Engram-Experimental
export WANDB_GROUP=constituent-20260922-fast50 WANDB_MODE=online WANDB_TAGS=constituents,fast50,matched,validation-only
export WANDB_DIR=/work WANDB_CACHE_DIR=/work/wandb-cache WANDB_DATA_DIR=/work/wandb-data WANDB_DISABLE_CODE=true WANDB_QUIET=true
pip install -q --no-cache-dir -r /work/code/requirements-training.txt
NVLIBS=$(python -c "import glob; print(':'.join(sorted(glob.glob('/usr/local/lib/python*/site-packages/nvidia/*/lib'))))")
export LD_LIBRARY_PATH="$NVLIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
python -c "import tensorflow as tf; assert tf.config.list_physical_devices('GPU'); print('GPU_GATE_PASS')"
'''
packs = json.loads((CODE / 'packs.json').read_text())
for stage, count, tail in [
    ('preflight', 2, 'python -u /work/code/run_study.py preflight --index "$JOB_COMPLETION_INDEX" --shards 2\n'),
    ('canary', 2, 'python -u /work/code/run_pack.py canary_packs.json 2\n'),
    ('screen', len(packs), 'python -u /work/code/run_pack.py packs.json\n'),
]:
    j = json.loads((LAB / 'local/continuation-20260920/engram-job.json').read_text())
    name = f'kai-n8n64-{stage}-0922-{sha[:6]}'
    j['metadata'] = {'name': name, 'namespace': 'cms-ml', 'labels': {**labels, 'app': 'kai-n8n64-' + stage}}
    s = j['spec']
    s.update(completions=count, parallelism=min(count, 12), backoffLimitPerIndex=2,
             activeDeadlineSeconds=28800, ttlSecondsAfterFinished=604800)
    s['template']['metadata'] = {'labels': j['metadata']['labels']}
    p = s['template']['spec']
    c = p['containers'][0]
    for volume in p['volumes']:
        if volume['name'] == 'code':
            volume['configMap']['name'] = cm
    for kind in ('requests', 'limits'):
        c['resources'][kind].update(cpu='6', memory='18Gi')
    if stage == 'preflight':
        c.pop('env', None)
        for kind in ('requests', 'limits'):
            c['resources'][kind].pop('nvidia.com/gpu')
            c['resources'][kind].update(cpu='4', memory='16Gi', **{'ephemeral-storage': '12Gi'})
        node = p['affinity']['nodeAffinity']
        node.pop('preferredDuringSchedulingIgnoredDuringExecution', None)
        expressions = node['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'][0]['matchExpressions']
        expressions[:] = [x for x in expressions if x['key'] != 'nvidia.com/gpu.product']
        setup = 'export CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled\npip install -q --no-cache-dir -r /work/code/requirements-cpu.txt\n'
    else:
        setup = gpu
    c['args'] = [header + setup + tail]
    (OUT / f'{stage}-job.json').write_text(json.dumps(j, indent=2) + '\n')
    print(stage, name, count)
(OUT / 'bundle-manifest.json').write_text(json.dumps({'sha256': sha, 'configmap': cm,
    'bytes': len(bundle.read_bytes()), 'files': {str(p.relative_to(CODE)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(CODE.rglob('*')) if p.is_file() and '__pycache__' not in str(p)}}, indent=2) + '\n')
print('bundle', sha)
