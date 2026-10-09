import json,copy,hashlib
from pathlib import Path
out=Path('local/continuation-20260920')
inputs=[('arch','local/training-batch-20260917/launch/relaunch-job-r3.json'),('attn','local/training-batch-20260918/launch/job.json'),('engram','local/engram-study/ops/gpu-job-parallel4.json')]
inspection='''import json, pathlib, hashlib, tarfile, time
P=pathlib.Path
records=[]
for label,campaign in [('arch','batch20260917'),('attn','batch20260918'),('engram','engram')]:
    bundle=P('/bundles')/label/'hgq2.tar.gz'
    digest=hashlib.sha256(bundle.read_bytes()).hexdigest()
    target=P('/work')/label; target.mkdir(parents=True,exist_ok=True)
    with tarfile.open(bundle) as t: t.extractall(target,filter='data')
    code=target/'hgq2'
    for cfgp in sorted((code/'configs'/campaign).glob('*.json')):
        cfg=json.loads(cfgp.read_text())
        if 'experiment' not in cfg: continue
        arm=cfg['experiment']['arm']
        if label=='engram' and arm not in [f'engram-e{i:02d}-s1' for i in range(4)]: continue
        root=P('/data/engram-study-20260918') if label=='engram' else P('/data/batch20260917')/('n'+str(cfg['arch']['n_part']))
        run=root/'runs'/arm
        latest=json.loads((run/'latest.json').read_text())
        state=json.loads((run/'checkpoints'/latest['checkpoint']/'state.json').read_text())
        cfgsha=hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()
        assert cfg['train']['epochs']==1000,(arm,'configured schedule')
        assert state['config_sha256']==cfgsha,(arm,'config mismatch')
        if label=='engram':
            manifest=json.loads((run/'source_manifest.json').read_text())
            assert state['code_sha256']==manifest['sha256'],(arm,'engram source mismatch')
            for name,sha in manifest['files'].items(): assert hashlib.sha256((code/name).read_bytes()).hexdigest()==sha,(arm,name)
        else: assert state['code_sha256']==digest,(arm,'code mismatch')
        assert not (run/'COMPLETE.json').exists(),(arm,'COMPLETE exists')
        row=dict(label=label,arm=arm,run=str(run),bundle_sha256=digest,latest=latest,state=state,config_sha256=cfgsha,files=[p.name for p in run.iterdir()])
        if label=='engram': row['source_manifest']=manifest
        records.append(row)
assert len(records)==31,len(records)
P('/work/pvc-state.json').write_text(json.dumps(records,indent=2))
print('PREFLIGHT_ALL_PASS '+json.dumps([{'arm':r['arm'],'epoch':r['state']['completed_epochs']} for r in records]),flush=True)
time.sleep(3600)
'''
job={'apiVersion':'batch/v1','kind':'Job','metadata':{'name':'kai-continuation-inspect-0920-r2','namespace':'cms-ml','labels':{'app':'kai-continuation-inspect'}},'spec':{'backoffLimit':0,'activeDeadlineSeconds':7200,'ttlSecondsAfterFinished':86400,'template':{'metadata':{'labels':{'app':'kai-continuation-inspect'}},'spec':{'restartPolicy':'Never','automountServiceAccountToken':False,'nodeSelector':{'kubernetes.io/arch':'amd64'},'affinity':{'nodeAffinity':{'requiredDuringSchedulingIgnoredDuringExecution':{'nodeSelectorTerms':[{'matchExpressions':[{'key':'kubernetes.io/hostname','operator':'NotIn','values':['nautilus-ext-gpu01.fullerton.edu','ren-gp-argo-01.madren.org']}]}]}}},'containers':[{'name':'inspect','image':'python:3.12','command':['python','-u','-c',inspection],'resources':{'requests':{'cpu':'1','memory':'2Gi','ephemeral-storage':'2Gi'},'limits':{'cpu':'1','memory':'2Gi','ephemeral-storage':'2Gi'}},'volumeMounts':[{'name':'persistent','mountPath':'/data','readOnly':True},{'name':'work','mountPath':'/work'}]}],'volumes':[{'name':'persistent','persistentVolumeClaim':{'claimName':'kai-data'}},{'name':'work','emptyDir':{'sizeLimit':'2Gi'}}]}}}}
for label,path in inputs:
 original=json.loads(Path(path).read_text())
 cm=next(v['configMap']['name'] for v in original['spec']['template']['spec']['volumes'] if 'configMap' in v)
 job['spec']['template']['spec']['volumes'].append({'name':label,'configMap':{'name':cm}})
 job['spec']['template']['spec']['containers'][0]['volumeMounts'].append({'name':label,'mountPath':'/bundles/'+label,'readOnly':True})
(out/'inspect-job.json').write_text(json.dumps(job,indent=2))
(out/'check_checkpoint_identity.py').write_text(inspection)
