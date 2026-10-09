import json,copy
from pathlib import Path
out=Path('local/continuation-20260920')
inputs=[('arch','local/training-batch-20260917/launch/relaunch-job-r3.json','kai-batch0917-full-e1000-0920'),('attn','local/training-batch-20260918/launch/job.json','kai-batch0918-full-e1000-0920'),('engram','local/engram-study/ops/gpu-job-parallel4.json','kai-engram-full-e1000-0920')]
for label,path,name in inputs:
 j=json.loads(Path(path).read_text());j['metadata']['name']=name
 for obj in (j['metadata'],j['spec']['template']['metadata']):obj['labels']['continuation']='full1000-20260920'
 s=j['spec'];s['parallelism']=s['completions'];s['activeDeadlineSeconds']=1209600;s['backoffLimitPerIndex']=6;s.pop('maxFailedIndexes',None)
 p=s['template']['spec'];c=p['containers'][0]
 command=c['args'][0]
 command=command.replace('82800s','255600s')
 if label=='engram': command=command.replace(' --stop-after 100','')
 else:
  campaign='batch20260917' if label=='arch' else 'batch20260918'
  helper='''import json, os, pathlib, subprocess, sys
code=pathlib.Path('/work/code')
campaign=CAMPAIGN
i=int(os.environ['JOB_COMPLETION_INDEX'])
if campaign=='batch20260917':
    assert 0<=i<12
    name=f'batch20260917-a{i:02d}-s1'
else:
    runs=json.loads((code/'configs'/campaign/'index.json').read_text())['runs']
    assert [r['index'] for r in runs]==list(range(len(runs)))
    name=runs[i]['name']
config=code/'configs'/campaign/(name+'.json')
cfg=json.loads(config.read_text()); assert cfg['train']['epochs']==1000
root=pathlib.Path('/data/batch20260917')/('n'+str(cfg['arch']['n_part']))
print('[continuation] '+name+' full configured1000 epochs',flush=True)
subprocess.run([sys.executable,'-u',str(code/'run_ablation.py'),'train','--config',str(config),'--root',str(root),'--track'],check=True)
'''.replace('CAMPAIGN',repr(campaign))
  command=command[:command.index('timeout --signal')]+"cat > /work/continue_full.py <<'PYCONTINUE'\n"+helper+"PYCONTINUE\ntimeout --signal=TERM --kill-after=180s 255600s python -u /work/continue_full.py\n"
 c['args']=[command]
 # Additional previous bad mount excluded for all campaigns.
 expressions=p['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms'][0]['matchExpressions']
 hosts=next(x['values'] for x in expressions if x['key']=='kubernetes.io/hostname')
 if 'ren-gp-argo-01.madren.org' not in hosts:hosts.append('ren-gp-argo-01.madren.org')
 (out/(label+'-job.json')).write_text(json.dumps(j,indent=2)+'\n')
 if label!='engram':compile(helper,label,'exec')
 print(name,s['parallelism'],c['args'][0].splitlines()[-1])
