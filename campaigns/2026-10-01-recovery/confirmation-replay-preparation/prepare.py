#!/usr/bin/env python3
"""Offline diagnostic repack; preserves every historical member and original archive bytes."""
import base64, copy, gzip, hashlib, io, json, subprocess, sys, tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
IMAGE='docker.io/library/python@sha256:4d1caded1f729ae443eb803f26ffde7b61e696aeaef62f099abb6dd6b14257c7'
NAME='kai-confirm1001-replay-a02s3-r2';OUTPUT='/data/confirmation-20260923/diagnostics/replay-a02s3-20261001-r2'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def enc(v):return (json.dumps(v,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def main():
 specpath=ROOT/'campaigns/2026-10-01-recovery/confirmation-repro-spec.json';spec=json.loads(specpath.read_bytes());case=spec['cases'][0];assert case['run_name']==spec['primary_case']
 originalcm=ROOT/spec['source']['configmap']['path'];rawcm=originalcm.read_bytes();assert sha(rawcm)==spec['source']['configmap']['byte_sha256'];cm=json.loads(rawcm);old=base64.b64decode(cm['binaryData']['hgq2.tar.gz']);assert sha(old)==spec['source']['archive_byte_sha256']
 historical={}
 with tarfile.open(fileobj=io.BytesIO(old),mode='r:gz') as tf:
  for member in tf:
   if member.isfile():historical[member.name]=tf.extractfile(member).read()
 assert len(historical)==152
 cfg=(ROOT/case['config']['path']).read_bytes();assert sha(cfg)==case['config']['byte_sha256']
 export=ROOT/'campaigns/2026-10-01-recovery/captures/pvc-20261001T0555Z';receipt=json.loads((export/'export-receipt.json').read_bytes());by_path={x['pvc_path']:x for x in receipt['files'] if x.get('accepted')}
 inputs=[];prefix='campaigns/2026-10-01-recovery/captures/pvc-20261001T0555Z/'
 paths=[case['selected_model_on_pvc'],case['cache_root_on_pvc']+'/data_info.json',case['cache_root_on_pvc']+'/READY.json']
 paths += ['/data/'+case[k]['path'].removeprefix(prefix) for k in ['config','run_data_info','state','source_manifest','input_std']]
 for path in paths:
  row=by_path[path];inputs.append({'path':path,'sha256':row['source_sha256'],'bytes':row['bytes']})
 scope={'run':case['run_name'],'selected':case['selected_model_on_pvc'],'selected_sha256':case['selected_model_byte_sha256_from_transport_receipt'],'selected_record':case['selected_record_zero_based_epoch'],'root_selected':case['run_root_on_pvc']+'/model_best.keras','config':case['run_root_on_pvc']+'/config.json','cache':case['cache_root_on_pvc'],'val_batch':case['validation_batch'],'output':OUTPUT,'inputs':inputs,'source_archive_sha256':spec['source']['archive_byte_sha256'],'source_manifest_sha256':case['recorded_source_and_versions_sha256'],'array_sha256':case['array_hash_metadata'],'runtime_environment':spec['historical_runtime']['environment'],'limitations':spec['historical_runtime']['not_recorded']+['Trained-process history and concurrent three-arm execution are not recreated.','New image digest and transitive GPU dependencies cannot be proven identical to failed historical attempt.','Writable supported handoff PVC; no source writes in diagnostic commands, source inputs and arrays checked before/after.','Four original-tolerance passes mean not reproduced, not fixed or safe to resume.']}
 additions={'code/diagnostics/probe.py':(HERE/'probe.py').read_bytes(),'code/diagnostics/transport.py':(HERE/'transport.py').read_bytes(),'code/diagnostics/scope.json':enc(scope),'code/diagnostics/configs/'+case['run_name']+'.json':cfg,'code/diagnostics/original-source-configmap.json':rawcm}
 files={**historical,**additions};assert len(files)==157
 stream=io.BytesIO()
 with tarfile.open(fileobj=stream,mode='w') as tf:
  for name,raw in sorted(files.items()):
   info=tarfile.TarInfo(name);info.size=len(raw);info.mode=0o444;info.mtime=0;tf.addfile(info,io.BytesIO(raw))
 archive=gzip.compress(stream.getvalue(),mtime=0);bundle=sha(archive)
 newcm=copy.deepcopy(cm);newcm['metadata']['name']=NAME+'-code';newcm['metadata'].setdefault('annotations',{})['bnjettag.io/bundle-sha256']=bundle;newcm['binaryData']['hgq2.tar.gz']=base64.b64encode(archive).decode()
 job=json.loads((ROOT/'campaigns/2026-09-23-confirmation/one-gpu-job.json').read_bytes());job['metadata']['name']=NAME;job['metadata'].setdefault('annotations',{}).update({'bnjettag.io/arms-per-pod':'1','bnjettag.io/single-arm-justified':'Bounded four-prediction diagnostic of one retained artifact; concurrency would change the diagnostic question.30min,nooptimizersteps; not a training utilization certificate.'})
 job['spec']={k:v for k,v in job['spec'].items() if k not in ['completionMode','completions','parallelism','backoffLimitPerIndex','podReplacementPolicy','podFailurePolicy','maxFailedIndexes','successPolicy']};job['spec'].update(backoffLimit=0,activeDeadlineSeconds=1800)
 ps=job['spec']['template']['spec'];ps['terminationGracePeriodSeconds']=30;ps['affinity']['nodeAffinity'].pop('preferredDuringSchedulingIgnoredDuringExecution',None)
 for term in ps['affinity']['nodeAffinity']['requiredDuringSchedulingIgnoredDuringExecution']['nodeSelectorTerms']:
  for expr in term['matchExpressions']:
   if expr['key']=='nvidia.com/gpu.product':expr['values']=['NVIDIA-A10']
 ps['volumes']=[v for v in ps['volumes'] if v['name']!='configs']
 for v in ps['volumes']:
  if v['name']=='code':v['configMap']['name']=newcm['metadata']['name']
  if 'emptyDir' in v:v['emptyDir']['sizeLimit']='12Gi'
 c=ps['containers'][0];c['name']='diagnostic';c['image']=IMAGE;c['volumeMounts']=[m for m in c['volumeMounts'] if m['name']!='configs'];c['resources']={k:{'cpu':'4','memory':'16Gi','ephemeral-storage':'12Gi','nvidia.com/gpu':'1'} for k in ['requests','limits']}
 c['env']=[{'name':k,'value':v} for k,v in {**scope['runtime_environment'],'WANDB_MODE':'disabled','JOB_NAME':NAME}.items()]
 for key,path in [('POD_UID','metadata.uid'),('RUN_ID',"metadata.labels['bnjettag.io/run-id']"),('HANDOFF_SHA256',"metadata.annotations['bnjettag.io/handoff-sha256']")]:c['env'].append({'name':key,'valueFrom':{'fieldRef':{'apiVersion':'v1','fieldPath':path}}})
 command="set -euo pipefail\nmkdir -p /work/code\necho '"+bundle+"  /cmcode/hgq2.tar.gz' | sha256sum -c -\ntar -xzf /cmcode/hgq2.tar.gz -C /work/code --strip-components=1\nexport PYTHONPATH=/work/code\nexport PYTHONDONTWRITEBYTECODE=1\npython - <<'VERIFY_ORIGINAL'\nimport base64,hashlib,json,tarfile,io\nfrom pathlib import Path\np=Path('/work/code');cm=json.loads((p/'diagnostics/original-source-configmap.json').read_bytes());raw=base64.b64decode(cm['binaryData']['hgq2.tar.gz']);assert hashlib.sha256(raw).hexdigest()=='"+scope['source_archive_sha256']+"'\nwith tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as tf:\n files=[m for m in tf if m.isfile()];assert len(files)==152\n for m in files:assert (p/m.name.removeprefix('code/')).read_bytes()==tf.extractfile(m).read()\nVERIFY_ORIGINAL\npip install -q --no-cache-dir -r /work/code/requirements-training.txt\ncd /work/code\nexec python -u /work/code/diagnostics/probe.py --scope /work/code/diagnostics/scope.json\n"
 c['command']=['bash','-c'];c['args']=[command]
 brief={'purpose':'Diagnose selected-checkpoint validation replay for A02-s3 through four predictions, three loads and two serial processes; zero optimizer steps.', 'changes':'New explicitly diagnostic repack:157files including152byte-identical historical members, embedded unchanged original26f3 archive, exact recovered A02-s3 config and diagnostic helpers. Newoutput/provenance only; no source/checkpoint mutation. Writable handoff mount adaptation requires review.', 'approval_ref':'Kai-20261001-confirmation-replay-diagnostic-pending-action-time-record','runs':[{'name':case['run_name'],'config_path':'code/diagnostics/configs/'+case['run_name']+'.json'}], 'expected_metrics':[{'name':'selected-checkpoint historical validation AUC/accuracy replay','split':'same ordered validation n=124000; training trace n=256 from cache n=496000','expectation':'Original metric functions, batch4096, rtol0 atol1e-7; mismatch is recorded, not tolerated or used for reselection.'},{'name':'prediction and variable-state reproducibility','split':'same124000 validation rows across four predeclared predictions','expectation':'Record hashes and differences; neither passes nor mismatches authorize resume.'}], 'stop_rules':[{'condition':'30-minute deadline, identity/cost/nonfinite/resource failure','action':'existing-runner-guard','approval_ref':'confirmation-repro-spec proposed bound; pending reviewed action-time scope'},{'condition':'metric mismatch','action':'notify-only','approval_ref':'predeclared diagnostic repeats may complete without tolerance change'}],'outputs':[OUTPUT,'/data/run-handoffs/<content-addressed-id>'],'scientific_gate':{'status':'pending','reference':'Diagnostic design/storage adaptation, tests, live resource/lint review and action-time authorization pending','scope':'single retained A02-s3 diagnostic only'},'production_gate':{'status':'pending','reference':'No training resume, optimizer restoration or schedule clearance from this probe'},'historical_archive_sha256':scope['source_archive_sha256'],'diagnostic_archive_sha256':bundle,'config_canonical_sha256':case['config_canonical_sha256'],'repro_spec_sha256':sha(specpath.read_bytes()),'storage_adaptation':'Original proposal read-only PVC cannot use supported handoff. Proposed explicit writable /data only for newprovenance/output; no sourcewrites and before/after input+arrayhashes. Not kernel-enforced read-only; requires review.','limitations':scope['limitations']}
 dest=HERE/'candidate';dest.mkdir(exist_ok=True)
 for name,value in [('job.json',job),('source-configmap.json',newcm),('scope.json',scope),('brief.json',brief),('envelope-manifest.json',{'historical_archive_sha256':scope['source_archive_sha256'],'diagnostic_archive_sha256':bundle,'historical_files':{k:sha(v) for k,v in historical.items()},'added_files':{k:sha(v) for k,v in additions.items()}})]: (dest/name).write_bytes(enc(value))
 args=[sys.executable,str(ROOT/'tools/run_handoff.py'),'prepare','--job',str(dest/'job.json'),'--configmap',str(dest/'source-configmap.json'),'--brief',str(dest/'brief.json'),'--data-info',str(export/'constituent-study-20260922/n8/data/data_info.json'),'--data-path',scope['cache']+'/data_info.json','--out',str(HERE/'handoffs')]
 result=subprocess.run(args,capture_output=True,text=True);print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr);assert result.returncode==0
 (HERE/'CANDIDATE.json').write_bytes(enc({'status':'offline_pending_review_not_submitted','handoff':result.stdout.strip(),'diagnostic_archive_sha256':bundle,'historical_archive_sha256':scope['source_archive_sha256'],'historical_member_count':152,'total_member_count':157,'input_count':len(inputs),'image':IMAGE,'job_name':NAME,'output':OUTPUT}))
if __name__=='__main__':main()
