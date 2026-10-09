#!/usr/bin/env python3
"""Offline, new handoff from exact historical payload; never freeze historical source again."""
import base64, copy, hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
HIST=ROOT/'campaigns/2026-09-26-training-batch/manifests'
EXPORT=ROOT/'campaigns/2026-10-01-recovery/captures/pvc-20261001T0555Z'
BUNDLE='42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0'
IMAGE='docker.io/library/python@sha256:4d1caded1f729ae443eb803f26ffde7b61e696aeaef62f099abb6dd6b14257c7'
RUNS=['chang0926-a-n64-s1','chang0926-a-n64-s2','chang0926-d-n64-s1','chang0926-cprime-n64-s1','chang0926-e1-n64-s1']
NAME='kai-chang1001-readoutb5-42abed-r1';BASE='/data/chang-n64-20260926';OUT=BASE+'/pilot-b/readout-epoch-0500-42abed-b5-recovery-20261001-r1'
def sha(b):return hashlib.sha256(b).hexdigest()
def enc(v):return (json.dumps(v,indent=2,sort_keys=True)+'\n').encode()
def main():
 cm=json.loads((HIST/'configmap-42abed4b.json').read_bytes());assert sha(base64.b64decode(cm['binaryData']['hgq2.tar.gz']))==BUNDLE
 cm['metadata']['name']=NAME+'-code'
 job=json.loads((HIST/'readout-b5-job.json').read_bytes());job['metadata']['name']=NAME
 spec=job['spec']['template']['spec'];c=spec['containers'][0];c['image']=IMAGE
 for v in spec['volumes']:
  if 'configMap' in v:v['configMap']['name']=cm['metadata']['name']
 inputs=[];receipt=json.loads((EXPORT/'export-receipt.json').read_bytes())
 for row in receipt['files']:
  path=row['pvc_path'];part=path.removeprefix(BASE+'/pilot-b/runs/').split('/')
  wanted=(len(part)>1 and part[0] in RUNS and (part[1] in ['config.json','data_info.json','input_std.json','source_manifest.json'] or part[1:3]==['snapshots','epoch-0500']))
  wanted=wanted or path in [BASE+'/n64/data/data_info.json',BASE+'/n64/data/READY.json']
  if wanted and row.get('accepted') and path.endswith(('.json','.keras')):
   inputs.append({'path':path,'sha256':row['source_sha256'],'bytes':row['bytes']})
 assert len(inputs)>30
 scope={'runs':RUNS,'indices':[0,1,24,56,57],'run_root':BASE+'/pilot-b/runs','cache':BASE+'/n64/data','output':OUT,'inputs':inputs,'expected_absent':[BASE+'/pilot-b/runs/'+run+'/DIVERGED.json' for run in RUNS],'image':IMAGE,'packages':['tensorflow','keras','hgq2','quantizers','scikit-learn','h5py','wandb','hls4ml','numpy']}
 driver=(HERE/'driver.py').read_bytes();scopebytes=enc(scope)
 # Exact helper bytes are part of the Job command and hence immutable handoff record.
 command=c['args'][0].split('BUNDLE6=')[0]
 command += "python - <<'READOUT_HELPERS'\nimport base64,hashlib\nfrom pathlib import Path\n"
 for name,raw in [('driver.py',driver),('scope.json',scopebytes)]:
  command+=f"b=base64.b64decode({base64.b64encode(raw).decode()!r});assert hashlib.sha256(b).hexdigest()=={sha(raw)!r};Path('/work/{name}').write_bytes(b)\n"
 command+='READOUT_HELPERS\nexec python -u /work/driver.py\n';c['args']=[command]
 c['env']=[{'name':'JOB_NAME','value':NAME},{'name':'POD_UID','valueFrom':{'fieldRef':{'apiVersion':'v1','fieldPath':'metadata.uid'}}},{'name':'RUN_ID','valueFrom':{'fieldRef':{'apiVersion':'v1','fieldPath':"metadata.labels['bnjettag.io/run-id']"}}},{'name':'HANDOFF_SHA256','valueFrom':{'fieldRef':{'apiVersion':'v1','fieldPath':"metadata.annotations['bnjettag.io/handoff-sha256']"}}}]
 brief={'purpose':'Recover missing registered historical b5 certification/entropy and genuine PID telemetry for five epoch500 snapshots; diagnostic only.',
 'changes':'Original 42abed compressed payload/code/configs unchanged. New Job/source ConfigMap/output identity; digest-pinned Python3.12 CPU image; input byte binding, bounded exact telemetry copying and <=4MiB encoded JSON/JSONL log export. No training or checkpoint writes.',
 'approval_ref':'Kai-20261001-execute-finish-readout',
 'runs':[{'name':n,'config_path':'code/campaigns/chang0926/configs/'+n+'.json'} for n in RUNS],
 'expected_metrics':[{'name':'selected feasible snapshot full-training traced eBOP certification','split':'training n=558000','expectation':'Registered relative tolerance <=1e-6; only feasible primary/AUC selections are certified. Stored mismatch is immediately a defect; registered conditional original-GPU adjudication remains separate.'},{'name':'registered attention entropy/state','split':'validation n=62000','expectation':'Descriptive pilot only; minimum-cost fallback is labelled by original code; no scientific promotion.'},{'name':'genuine in-training/traced cost telemetry','split':'training epoch history through500','expectation':'Copy exact five JSONL histories and hashes. Full A/Cprime/K1 and regime-A/B analysis remains separately pending.'}],
 'stop_rules':[{'condition':'Four-hour Job deadline or failure of any input/handoff/hash/readout guard','action':'existing-runner-guard','approval_ref':'Registered historical readout4h bound; Kai original finish-readout instruction'},{'condition':'Scientific disagreement or incomplete/missing telemetry/export','action':'notify-only','approval_ref':'Registered readout and K1 study; no automatic GPU rerun or production launch'}],
 'outputs':[OUT,'/data/run-handoffs/<content-addressed-id>'],
 'scientific_gate':{'status':'pending','reference':'Readout-only preparation review and action-time authorization pending','scope':'historical b5 diagnostic computation and exact telemetry recovery only'},
 'production_gate':{'status':'pending','reference':'K1 already triggered; option(c) chosen at2026-10-01T06:00:02.706672Z, amendment/newfreeze/preflight/replacementpilot required'},
 'limitations':['Historical training immutable handoff remains unavailable. New record does not retroactively establish it.','PVC must be writable for supported provenance init and new output. Source nonmutation is enforced by exact commands and before/after hashes, not a read-only PVC mount.','Full rules and matched regimeA/B analysis are separate, still pending after successful cert/entropy.','CPU route retains registered computations; one GPU allowance is not numerical-equivalence evidence.','Log export may be incomplete/refused or lost to rotation; complete artifacts remain at new durable output and incomplete transport is never PASS.'],
 'input_inventory_sha256':sha(scopebytes),'driver_sha256':sha(driver),'image_digest_receipt':'local/2026-10-01-execution/python-readout-image.json','decision_ref':'local/2026-10-01-execution/chang-option-c-decision.json'}
 dest=HERE/'candidate';dest.mkdir(exist_ok=True)
 for name,value in [('job.json',job),('source-configmap.json',cm),('scope.json',scope),('brief.json',brief)]: (dest/name).write_bytes(enc(value))
 result=subprocess.run([sys.executable,str(ROOT/'tools/run_handoff.py'),'prepare','--job',str(dest/'job.json'),'--configmap',str(dest/'source-configmap.json'),'--brief',str(dest/'brief.json'),'--data-info',str(EXPORT/'chang-n64-20260926/n64/data/data_info.json'),'--data-path',BASE+'/n64/data/data_info.json','--out',str(HERE/'handoffs')],capture_output=True,text=True)
 print(result.stdout,end='');print(result.stderr,end='',file=sys.stderr);assert result.returncode==0
 (HERE/'CANDIDATE.json').write_bytes(enc({'status':'offline_candidate_pending_review','job_name':NAME,'output':OUT,'input_count':len(inputs),'driver_sha256':sha(driver),'scope_sha256':sha(scopebytes),'bundle_sha256':BUNDLE,'prepare_stdout':result.stdout.strip()}))
if __name__=='__main__':main()
