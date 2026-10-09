#!/usr/bin/env python3
"""NRP-only selected-checkpoint replay. Never trains, restores optimizer or selects a model."""
import argparse, hashlib, importlib.metadata, json, os, resource, subprocess, sys, time
from pathlib import Path

def encoded(value):return (json.dumps(value,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def need(ok,message):
 if not ok:raise ValueError(message)
def hash_file(path):
 digest=hashlib.sha256()
 with Path(path).open('rb') as stream:
  for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
 return digest.hexdigest()
HANDOFF_ROOT='/data/run-handoffs/'
def make_output(out):
 """Create the immediate parent if absent; the leaf stays exclusive so no earlier output is reused."""
 need(out.is_absolute() and '..' not in out.parts,'output path must be absolute and normalized')
 need(out.parent.parent.is_dir() and not any(p.is_symlink() for p in [out.parent,*out.parent.parents]),'output parent chain missing or symlinked: '+str(out.parent))
 out.parent.mkdir(exist_ok=True);need(out.parent.is_dir() and not out.parent.is_symlink(),'output parent refused: '+str(out.parent))
 out.mkdir(exist_ok=False)
def write_json(path,value):
 with Path(path).open('xb') as stream:stream.write(encoded(value))
def check_inputs(scope):
 rows=[]
 for item in scope['inputs']:
  path=Path(item['path'])
  need(path.is_absolute() and not any(p.is_symlink() for p in [path,*path.parents]),'source symlink refused')
  need(path.is_file() and path.stat().st_size==item['bytes'] and hash_file(path)==item['sha256'],'input identity mismatch: '+str(path))
  rows.append(item)
 root=Path(scope['root_selected'])
 if root.exists():
  need(not root.is_symlink(),'root selection symlink refused');h=hash_file(root)
  need(h==scope['selected_sha256'],'root selected bytes differ from committed generation')
  rows.append({'path':str(root),'sha256':h,'status':'matched_committed_selection'})
 else:rows.append({'path':str(root),'status':'absent_retained_generation_used'})
 return rows
def fingerprint(model,np,ablation):
 variables=[]
 for i,var in enumerate(model.variables):
  value=np.asarray(var)
  need(value.dtype.kind not in 'OUSV' and np.isfinite(value).all(),'nonfinite/unsupported model variable')
  variables.append({'index':i,'name':getattr(var,'path',getattr(var,'name',str(i))),'shape':list(value.shape),'dtype':str(value.dtype),'sha256':sha(np.ascontiguousarray(value).tobytes())})
 widths=ablation.width_snapshot(model)
 return {'variables':variables,'variables_sha256':sha(encoded(variables)),'activation_width_state_sha256':sha(encoded(widths))}
def predict_sequence(np,keras,ablation,arrays,scope,out,process):
 """Three predictions in p1, one in p2; dependencies injectable for synthetic tests."""
 xt,yt,xv,yv=arrays;expected=scope['selected_record'];rows=[]
 for load_number,repeats in ([(1,2),(2,1)] if process=='p1' else [(1,1)]):
  model=keras.models.load_model(scope['selected'],compile=False)
  states={'before_trace':fingerprint(model,np,ablation)}
  trace=ablation.compute_ebops(model,np.asarray(xt[:256]))
  need(trace['total']==expected['ebops'],'selected cost mismatch')
  states['after_trace']=fingerprint(model,np,ablation)
  for repeat in range(1,repeats+1):
   name=f'{process}-load{load_number}-predict{repeat}';before=fingerprint(model,np,ablation)
   logits=np.asarray(model.predict(xv,batch_size=scope['val_batch'],verbose=0))
   need(logits.shape==yv.shape and np.isfinite(logits).all(),'nonfinite/shape-invalid prediction')
   auc,per_auc,accuracy=ablation.validation_metrics(yv,logits)
   assertion='PASS'
   try:np.testing.assert_allclose([auc,accuracy],[expected['val_macro_auc'],expected['val_categorical_accuracy']],atol=1e-7,rtol=0)
   except AssertionError:assertion='MISMATCH'
   need(np.isfinite([auc,accuracy,*per_auc]).all(),'nonfinite metric')
   # New diagnostic logits are durable only here; never replace historical predictions.
   with (out/(name+'.npy')).open('xb') as stream:np.save(stream,logits,allow_pickle=False)
   record={'name':name,'process':process,'load':load_number,'repeat':repeat,'trace':trace,'historical_assertion':assertion,'validation_n':len(yv),'auc':auc,'accuracy':accuracy,'per_class_auc':per_auc,'logits':{'shape':list(logits.shape),'dtype':str(logits.dtype),'sha256':sha(np.ascontiguousarray(logits).tobytes()),'file_sha256':hash_file(out/(name+'.npy'))},'load_states':states,'before_predict':before,'after_predict':fingerprint(model,np,ablation),'prediction_settings':{'jit_compile':str(getattr(model,'jit_compile','unavailable')),'dtype_policy':str(getattr(model,'dtype_policy','unavailable')),'batch_size':scope['val_batch']}}
   write_json(out/(name+'.json'),record);rows.append(record)
  del model
 return rows
def worker(scope,process):
 out=Path(scope['output']);before=check_inputs(scope)
 import run_engram
 ablation,_=run_engram.runtime()
 import numpy as np,keras,tensorflow as tf
 actual=run_engram.source_manifest();need(actual['sha256']==scope['source_manifest_sha256'],'source/package manifest mismatch')
 devices=tf.config.list_physical_devices('GPU');need(len(devices)==1,'exactly one GPU required')
 details=tf.config.experimental.get_device_details(devices[0]);need(details.get('device_name','').strip()=='NVIDIA A10','required A10 not observed')
 cfg=json.loads(Path(scope['config']).read_bytes());run_engram.validate_cfg(cfg)
 need(cfg['train']['val_batch']==scope['val_batch']==4096,'validation batch changed')
 arrays,info=run_engram.load_cache(Path(scope['cache']),cfg)
 need(info['array_sha256']==scope['array_sha256'],'cache identity fields differ')
 runtime={'process':process,'python':sys.version,'source_manifest':actual,'packages':{d.metadata['Name']:d.version for d in importlib.metadata.distributions()},'tensorflow_build':tf.sysconfig.get_build_info(),'device':details,'logical_devices':[x.name for x in tf.config.list_logical_devices()],'tf32_api_enabled':tf.config.experimental.tensor_float_32_execution_enabled(),'mixed_precision_policy':str(keras.mixed_precision.global_policy()),'op_determinism':'not changed; no historical/runtime query established','environment':{k:os.environ.get(k) for k in scope['runtime_environment']},'nvidia_smi':subprocess.run(['nvidia-smi','--query-gpu=name,uuid,driver_version,memory.total,memory.used','--format=csv,noheader'],capture_output=True,text=True,timeout=10).stdout.strip()}
 write_json(out/(process+'-runtime.json'),runtime)
 rows=predict_sequence(np,keras,ablation,arrays,scope,out,process)
 for key,array in zip(('x_train','y_train','x_val','y_val'),arrays):need(ablation.array_hash(array)==scope['array_sha256'][key],'cache array changed during replay: '+key)
 after=check_inputs(scope);need(before==after,'source inputs changed during replay')
 write_json(out/(process+'-complete.json'),{'process':process,'predictions':[x['name'] for x in rows],'source_unchanged':True,'max_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'gpu_memory':tf.config.experimental.get_memory_info('GPU:0')})
def summarize(scope):
 import numpy as np
 out=Path(scope['output']);names=['p1-load1-predict1','p1-load1-predict2','p1-load2-predict1','p2-load1-predict1']
 records=[json.loads((out/(n+'.json')).read_bytes()) for n in names];base=np.load(out/(names[0]+'.npy'),allow_pickle=False);comparisons=[]
 for name in names[1:]:
  value=np.load(out/(name+'.npy'),allow_pickle=False);need(base.shape==value.shape and np.isfinite(value).all(),'invalid saved diagnostic outputs')
  comparisons.append({'baseline':names[0],'other':name,'byte_equal':base.dtype==value.dtype and base.tobytes()==value.tobytes(),'max_absolute_difference':float(np.max(np.abs(base.astype(np.float64)-value.astype(np.float64)))),'predicted_label_disagreements':int(np.count_nonzero(base.argmax(-1)!=value.argmax(-1)))})
 return {'status':'diagnostic_complete_requires_scientific_review','case':scope['run'],'predictions':records,'comparisons':comparisons,'interpretation':'not_reproduced_in_this_probe' if all(x['historical_assertion']=='PASS' for x in records) else 'metric_disagreement_reproduced_in_this_probe','optimizer_steps':0,'resume_authorized':False,'historical_runtime_exact':False,'limitations':scope['limitations']}
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--scope',required=True);parser.add_argument('--worker',choices=['p1','p2']);a=parser.parse_args();scope=json.loads(Path(a.scope).read_bytes())
 if a.worker:
  worker(scope,a.worker);return 0
 out=Path(scope['output'])
 try:make_output(out);identity={k:os.environ[k.upper()] for k in ('run_id','handoff_sha256','job_name','pod_uid')};raw=Path(HANDOFF_ROOT+identity['run_id']+'/record.json').read_bytes();need(sha(raw)==identity['handoff_sha256'],'handoff record mismatch');need(json.loads(raw)['job']['metadata']['name']==identity['job_name'],'handoff Job mismatch')
 except Exception as exc:
  # No durable result.json can be trusted yet, so the pod log is the startup record.
  print('CONFIRMATION_REPLAY_STARTUP_FAILED '+type(exc).__name__+': '+str(exc),flush=True);return 1
 write_json(out/'identity.json',identity);status={'identity':identity,'status':'started','production_gate':'pending','resume_authorized':False};exit_code=1
 try:
  inputs=check_inputs(scope);write_json(out/'input-manifest.json',{'inputs':inputs,'source_archive':scope['source_archive_sha256'],'diagnostic_scope_sha256':sha(Path(a.scope).read_bytes())})
  for process in ['p1','p2']:
   result=subprocess.run([sys.executable,__file__,'--scope',a.scope,'--worker',process],check=False)
   need(result.returncode==0,'worker failure: '+process)
  summary=summarize(scope);write_json(out/'replay-summary.json',summary)
  need(check_inputs(scope)==inputs,'source input changed across processes');status['status']='diagnostic_complete_requires_review';exit_code=0
 except Exception as exc:status.update(status='incomplete_or_guard_failure',error=type(exc).__name__+': '+str(exc))
 finally:
  write_json(out/'result.json',status)
  # Small metadata transport only; predictions stay on PVC and never enter logs.
  from transport import export
  names=['identity.json','input-manifest.json','result.json','replay-summary.json','p1-runtime.json','p2-runtime.json','p1-complete.json','p2-complete.json']
  receipt=export(out,identity,names);write_json(out/'export-receipt.json',receipt)
  if receipt['status']!='emitted_complete':exit_code=1
 print('CONFIRMATION_REPLAY_DONE exit='+str(exit_code)+' no_training=true',flush=True);return exit_code
if __name__=='__main__':sys.exit(main())
