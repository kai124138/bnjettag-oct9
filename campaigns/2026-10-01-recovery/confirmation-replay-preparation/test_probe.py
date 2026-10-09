import ast,copy,hashlib,importlib.util,json,tempfile,types,unittest
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
def load(name):
 s=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('probe');t=load('transport');r=load('receive')
class Model:
 def __init__(self,api):self.api=api;self.variables=[np.array([1.,-1.],dtype=np.float32)];self.jit_compile=False;self.dtype_policy='float32'
 def predict(self,x,batch_size,verbose):self.api.predictions.append((len(x),batch_size,verbose));return self.api.logits.copy()
class API:
 def __init__(self):self.loads=[];self.predictions=[];self.traces=[];self.logits=np.eye(5,dtype=np.float32)
 def load_model(self,path,compile):assert compile is False;self.loads.append(path);return Model(self)
 def trace(self,m,sample):self.traces.append(sample.shape);return {'total':12,'per_layer':{}}
 def metrics(self,y,z):return .5,[.5]*5,.4
 def width(self,m):return {'layer':{'bits':1,'i':1,'f':0}}
class ProbeTests(unittest.TestCase):
 def fixture(self):
  api=API();keras=types.SimpleNamespace(models=api);ablation=types.SimpleNamespace(compute_ebops=api.trace,validation_metrics=api.metrics,width_snapshot=api.width);arrays=(np.zeros((256,8,3),dtype=np.float32),np.zeros((256,5),dtype=np.float32),np.zeros((5,8,3),dtype=np.float32),np.eye(5,dtype=np.float32));scope={'selected':'bound-model.keras','selected_record':{'ebops':12,'val_macro_auc':.5,'val_categorical_accuracy':.4},'val_batch':4096};return api,keras,ablation,arrays,scope
 def test_exact_sequence_and_original_tolerance(self):
  api,keras,ablation,arrays,scope=self.fixture()
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp);first=p.predict_sequence(np,keras,ablation,arrays,scope,out,'p1');second=p.predict_sequence(np,keras,ablation,arrays,scope,out,'p2')
   self.assertEqual(len(api.loads),3);self.assertEqual(len(api.traces),3);self.assertEqual(api.predictions,[(5,4096,0)]*4);self.assertTrue(all(x['historical_assertion']=='PASS' for x in first+second))
   self.assertEqual(len(list(out.glob('*.npy'))),4)
 def test_metric_mismatch_continues_without_relaxation(self):
  api,keras,ablation,arrays,scope=self.fixture();scope['selected_record']['val_macro_auc']=.5+2e-7
  with tempfile.TemporaryDirectory() as tmp:
   rows=p.predict_sequence(np,keras,ablation,arrays,scope,Path(tmp),'p1');self.assertEqual(len(rows),3);self.assertTrue(all(x['historical_assertion']=='MISMATCH' for x in rows))
 def test_cost_or_nonfinite_stop(self):
  for kind in ['cost','nonfinite']:
   api,keras,ablation,arrays,scope=self.fixture()
   if kind=='cost':scope['selected_record']['ebops']=13
   else:api.logits[0,0]=np.nan
   with tempfile.TemporaryDirectory() as tmp:
    with self.assertRaises(ValueError):p.predict_sequence(np,keras,ablation,arrays,scope,Path(tmp),'p1')
    self.assertLessEqual(len(api.loads),1);self.assertLessEqual(len(api.predictions),1)
 def test_input_tamper_symlink_and_root_mismatch(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);source=d/'model';source.write_bytes(b'opaque');scope={'inputs':[{'path':str(source),'bytes':6,'sha256':hashlib.sha256(b'opaque').hexdigest()}],'root_selected':str(d/'root'),'selected_sha256':hashlib.sha256(b'opaque').hexdigest()};p.check_inputs(scope)
   (d/'root').write_bytes(b'wrong')
   with self.assertRaises(ValueError):p.check_inputs(scope)
   (d/'root').unlink();source.write_bytes(b'broken')
   with self.assertRaises(ValueError):p.check_inputs(scope)
   source.unlink();source.symlink_to(d/'target')
   with self.assertRaises(ValueError):p.check_inputs(scope)
 def test_no_training_calls_and_frozen_sequence(self):
  tree=ast.parse((HERE/'probe.py').read_text());calls=[n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)]
  self.assertFalse(set(calls)&{'train','run_training','restore_checkpoint','fit','compile','apply_gradients','save_model'})
  self.assertEqual(calls.count('load_model'),1);self.assertEqual(calls.count('predict'),1)
 def test_single_job_policy(self):
  job=json.loads((HERE/'candidate/job.json').read_bytes());spec=job['spec']
  self.assertFalse(set(spec)&{'completionMode','backoffLimitPerIndex','maxFailedIndexes','successPolicy','podFailurePolicy','podReplacementPolicy'})
  self.assertEqual(spec['backoffLimit'],0);self.assertEqual(spec['activeDeadlineSeconds'],1800)
  containers=spec['template']['spec']['containers'];self.assertEqual(len(containers),1);self.assertEqual(containers[0]['resources']['limits']['nvidia.com/gpu'],'1')
 def test_envelope_preserves_historical_members_and_config(self):
  import base64,io,tarfile
  cm=json.loads((HERE/'candidate/source-configmap.json').read_bytes());new=tarfile.open(fileobj=io.BytesIO(base64.b64decode(cm['binaryData']['hgq2.tar.gz'])),mode='r:gz');original=json.loads(new.extractfile('code/diagnostics/original-source-configmap.json').read());raw=base64.b64decode(original['binaryData']['hgq2.tar.gz']);self.assertEqual(hashlib.sha256(raw).hexdigest(),'26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45')
  old=tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz');members=[m for m in old if m.isfile()];self.assertEqual(len(members),152)
  for member in members:self.assertEqual(old.extractfile(member).read(),new.extractfile(member.name).read())
  cfg=new.extractfile('code/diagnostics/configs/confirm0923-a02-s3-e1000.json').read();self.assertEqual(hashlib.sha256(cfg).hexdigest(),'2d3b61146cd9cf1d2a33bdb7a552a1b542b46e4eb4460f099bd92fb22a676fe0')
 def test_transport_has_explicit_all_artifacts_and_no_logits(self):
  identity={'run_id':'rh-fixture','handoff_sha256':'a'*64,'job_name':'fixture','pod_uid':'fixture'}
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);(d/'identity.json').write_bytes(t.enc(identity));(d/'result.json').write_bytes(t.enc({'identity':identity}));lines=[];receipt=t.export(d,identity,sorted(r.ALLOWED),lambda line,**kw:lines.append(line));self.assertEqual(receipt['status'],'emitted_incomplete')
   files,rec=r.decode(('\n'.join(lines)+'\n').encode(),identity);self.assertEqual(len(rec['entries']),8);self.assertFalse(any(name.endswith('.npy') for name in files))
   with self.assertRaises(ValueError):r.decode(('\n'.join(lines[:-1])+'\n').encode(),identity)
 def startup(self,tmp,record_name='fixture'):
  import contextlib,io,os,sys
  from unittest import mock
  d=Path(tmp);handoffs=d/'handoffs';(handoffs/'rh-fixture').mkdir(parents=True);raw=json.dumps({'job':{'metadata':{'name':record_name}}}).encode();(handoffs/'rh-fixture'/'record.json').write_bytes(raw)
  out=d/'data'/'diagnostics'/'replay-r2';(d/'data').mkdir(exist_ok=True);scope=d/'scope.json';scope.write_text(json.dumps({'output':str(out),'inputs':[{'path':str(d/'absent-input'),'bytes':1,'sha256':'0'*64}],'root_selected':str(d/'root'),'selected_sha256':'0'*64,'source_archive_sha256':'0'*64}))
  env={'RUN_ID':'rh-fixture','HANDOFF_SHA256':hashlib.sha256(raw).hexdigest(),'JOB_NAME':'fixture','POD_UID':'fixture'};log=io.StringIO()
  with mock.patch.dict(os.environ,env),mock.patch.object(p,'HANDOFF_ROOT',str(handoffs)+'/'),mock.patch.object(sys,'argv',['probe.py','--scope',str(scope)]),mock.patch.object(sys,'path',[str(HERE),*sys.path]),contextlib.redirect_stdout(log):code=p.main()
  return code,out,log.getvalue()
 def test_startup_creates_absent_parent_then_records_guard_failure(self):
  with tempfile.TemporaryDirectory() as tmp:
   code,out,log=self.startup(tmp);self.assertEqual(code,1);self.assertTrue(out.is_dir());self.assertNotIn('STARTUP_FAILED',log)
   result=json.loads((out/'result.json').read_bytes());self.assertEqual(result['status'],'incomplete_or_guard_failure');self.assertIn('input identity mismatch',result['error'])
 def test_startup_refuses_existing_leaf_and_logs(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);(d/'data'/'diagnostics'/'replay-r2').mkdir(parents=True);(d/'data'/'diagnostics'/'replay-r2'/'old').write_bytes(b'kept')
   code,out,log=self.startup(tmp);self.assertEqual(code,1);self.assertIn('CONFIRMATION_REPLAY_STARTUP_FAILED FileExistsError',log);self.assertEqual(sorted(x.name for x in out.iterdir()),['old'])
 def test_startup_refuses_symlinked_parent_and_wrong_handoff(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp);(d/'elsewhere').mkdir();(d/'data').mkdir();(d/'data'/'diagnostics').symlink_to(d/'elsewhere')
   with self.assertRaises(ValueError):p.make_output(d/'data'/'diagnostics'/'leaf')
   self.assertEqual(list((d/'elsewhere').iterdir()),[])
  with tempfile.TemporaryDirectory() as tmp:
   code,out,log=self.startup(tmp,record_name='other');self.assertEqual(code,1);self.assertIn('STARTUP_FAILED ValueError: handoff Job mismatch',log)
if __name__=='__main__':unittest.main()
