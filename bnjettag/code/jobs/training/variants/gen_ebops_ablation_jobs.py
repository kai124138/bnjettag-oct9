#!/usr/bin/env python3
"""Generate immutable source, CPU preflight/data jobs and a 3-at-a-time GPU array."""
import argparse
import base64
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import yaml


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--code-root', type=Path)
    p.add_argument('--out-dir', type=Path, required=True)
    a = p.parse_args()
    code = a.code_root or Path(__file__).resolve().parents[3] / 'hgq2'
    sys.path.insert(0, str(code / 'configs'))
    from gen_ebops_ablation import GROUP, ARMS, make_ablation
    out = a.out_dir
    out.mkdir(parents=True, exist_ok=True)
    files = list((code/'bnhgq2').rglob('*.py')) + list((code/'hls_templates').glob('*.h'))
    files += [code/n for n in ('run_ablation.py','check_ebops_ablation.py','preflight_final.sh')]
    files += [code/'configs'/n for n in ('gen_r14.py','gen_ebops_n8.py','gen_ebops_ablation.py')]
    files += list((code/'configs').glob(GROUP+'-*.json'))
    for arm in ARMS:
        cfg = make_ablation(arm)
        assert json.loads((code/'configs'/(cfg['name']+'.json')).read_text()) == cfg
    raw = io.BytesIO()
    records = {}
    with tarfile.open(fileobj=raw,mode='w') as tar:
        for file in sorted(set(files)):
            relative = str(file.relative_to(code)); data = file.read_bytes()
            records[relative] = hashlib.sha256(data).hexdigest()
            info = tarfile.TarInfo('hgq2/'+relative); info.mode=0o644; info.size=len(data)
            tar.addfile(info,io.BytesIO(data))
    payload=gzip.compress(raw.getvalue(),mtime=0)
    assert len(payload)<900000
    sha=hashlib.sha256(payload).hexdigest(); cm='kai-ebops-abl-code-'+sha[:10]
    (out/'hgq2.tar.gz').write_bytes(payload)
    (out/'configmap.json').write_text(json.dumps({'apiVersion':'v1','kind':'ConfigMap','immutable':True,
        'metadata':{'name':cm,'namespace':'cms-ml'},'binaryData':{'hgq2.tar.gz':base64.b64encode(payload).decode()}},indent=2)+'\n')
    root='/data/'+GROUP
    common=f'''set -euo pipefail
export KERAS_BACKEND=tensorflow MPLBACKEND=Agg TF_FORCE_GPU_ALLOW_GROWTH=true
export OMP_NUM_THREADS=4 TF_NUM_INTRAOP_THREADS=4 TF_NUM_INTEROP_THREADS=2
mkdir -p /work/code {root}
echo '{sha}  /cmcode/hgq2.tar.gz' | sha256sum -c -
tar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1
export PYTHONPATH=/work/code BNHGQ2_CODE_SHA256={sha}
export WANDB_ENTITY=kayamaguchi-uc-san-diego WANDB_PROJECT=BNJetTag-EBOPs-N8 WANDB_GROUP={GROUP}
'''
    deps='keras==3.15.0 hgq2==0.1.9 quantizers==1.2.2 scikit-learn==1.9.0 h5py==3.14.0 wandb==0.28.0 hls4ml==1.3.0 numpy==2.5.0'
    gpu_setup=common+f'''pip install -q --no-cache-dir 'tensorflow[and-cuda]==2.21.0' {deps}
NVLIBS=$(python -c "import glob; print(':'.join(sorted(glob.glob('/usr/local/lib/python*/site-packages/nvidia/*/lib'))))")
export LD_LIBRARY_PATH="$NVLIBS${{LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
python -c "import tensorflow as tf; assert tf.config.list_physical_devices('GPU'); print('[gpu] TensorFlow GPU gate PASS')"
python -c "import wandb; wandb.Api().viewer; print('[wandb] authentication PASS')"
'''
    cpu_setup=common+f'''export CUDA_VISIBLE_DEVICES=-1 WANDB_MODE=disabled
pip install -q --no-cache-dir tensorflow==2.21.0 {deps}
'''
    def job(name,script,gpu=False,secret=False):
        requests={'cpu':'4','memory':'12Gi' if gpu else '8Gi','ephemeral-storage':'24Gi' if gpu else '8Gi'}
        if gpu: requests['nvidia.com/gpu']='1'
        container={'name':'train' if gpu else 'preflight','image':'python:3.12','command':['bash','-c'],'args':[script],
                   'resources':{'requests':dict(requests),'limits':dict(requests)},
                   'volumeMounts':[{'name':'code','mountPath':'/cmcode','readOnly':True},{'name':'work','mountPath':'/work'},
                                   {'name':'persistent','mountPath':'/data'}]}
        if secret: container['env']=[{'name':'WANDB_API_KEY','valueFrom':{'secretKeyRef':{'name':'kai-wandb','key':'WANDB_API_KEY'}}}]
        spec={'restartPolicy':'Never','terminationGracePeriodSeconds':180,'nodeSelector':{'kubernetes.io/arch':'amd64'},
              'containers':[container], 'volumes':[{'name':'code','configMap':{'name':cm}},
                    {'name':'work','emptyDir':{'sizeLimit':'24Gi' if gpu else '8Gi'}},
                    {'name':'persistent','persistentVolumeClaim':{'claimName':'kai-data'}}]}
        if gpu:
            pool=['NVIDIA-GeForce-RTX-4090','NVIDIA-L40S','NVIDIA-L40']
            spec['affinity']={'nodeAffinity':{'requiredDuringSchedulingIgnoredDuringExecution':{'nodeSelectorTerms':[{'matchExpressions':[
                {'key':'nvidia.com/gpu.product','operator':'In','values':pool}]}]},
                'preferredDuringSchedulingIgnoredDuringExecution':[{'weight':100,'preference':{'matchExpressions':[
                    {'key':'nvidia.com/gpu.product','operator':'In','values':pool[:2]}]}}]}}
        return {'apiVersion':'batch/v1','kind':'Job','metadata':{'name':name,'namespace':'cms-ml','labels':{'app':'kai-ebops-ablation'}},
                'spec':{'backoffLimit':2,'template':{'metadata':{'labels':{'app':'kai-ebops-ablation'}},'spec':spec}}}
    pre_name='kai-ebops-abl-preflight-'+sha[:8]
    preflight=job(pre_name,cpu_setup+f'''export BNF_CODE=/work/code BNF_CONFIG_GLOB='{GROUP}-*.json' BNF_SKIP_INSTALL=1
bash /work/code/preflight_final.sh
python -u /work/code/check_ebops_ablation.py --integration
''')
    preflight['spec'].update(backoffLimit=0,activeDeadlineSeconds=3600)
    prepare_name='kai-ebops-abl-data-'+sha[:8]
    prepare=job(prepare_name,cpu_setup+f'python -u /work/code/run_ablation.py prepare --config /work/code/configs/{make_ablation(ARMS[0])["name"]}.json --root {root}\n')
    # Finite data preparation; no wall-time cutoff on 1000-epoch training Jobs.
    benchmark_name='kai-ebops-abl-benchmark-'+sha[:8]
    benchmark=job(benchmark_name,gpu_setup+f'''WANDB_MODE=disabled python -u /work/code/check_ebops_ablation.py --integration --gpu
python -u /work/code/run_ablation.py train --config /work/code/configs/{make_ablation(ARMS[0])['name']}.json --root {root} --benchmark-epochs 2
''',gpu=True,secret=True)
    array_name='kai-ebops-abl-0912-e1000'
    names=' '.join(make_ablation(arm)['name'] for arm in ARMS)
    script=gpu_setup+f'''CONFIGS=({names})
CONFIG=${{CONFIGS[$JOB_COMPLETION_INDEX]}}
echo "[run] index=$JOB_COMPLETION_INDEX config=$CONFIG"
python -u /work/code/run_ablation.py train --config "/work/code/configs/$CONFIG.json" --root {root}
'''
    array=job(array_name,script,gpu=True,secret=True)
    array['spec'].pop('backoffLimit')
    array['spec'].update(completions=7,parallelism=3,completionMode='Indexed',backoffLimitPerIndex=2)
    for name,obj in [('preflight',preflight),('prepare-data',prepare),('benchmark',benchmark),('training',array)]:
        (out/(name+'.yaml')).write_text(yaml.safe_dump(obj,sort_keys=False))
    manifest={'group':GROUP,'code_sha256':sha,'configmap':cm,'files':records,'arms':list(ARMS),
              'preflight_job':pre_name,'prepare_job':prepare_name,'benchmark_job':benchmark_name,'training_job':array_name,
              'persistent_root':root,'gpu_pool':['RTX 4090','L40S','L40'],'parallelism':3,'epochs':1000,
              'activeDeadlineSeconds':None,'backoffLimitPerIndex':2}
    (out/'launch_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps({k:v for k,v in manifest.items() if k!='files'},indent=2))

if __name__=='__main__': main()
