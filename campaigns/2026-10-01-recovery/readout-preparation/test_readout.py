import base64, copy, gzip, hashlib, importlib.util, json, tempfile, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
def module(name):
 s=importlib.util.spec_from_file_location(name,HERE/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
d=module('driver');r=module('receive')
ID={'run_id':'rh-fixture','handoff_sha256':'a'*64,'job_name':'fixture','pod_uid':'pod-fixture'}
class ExportTests(unittest.TestCase):
 def fixture(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'identity.json').write_bytes(d.enc(ID));(p/'result.json').write_bytes(d.enc({'identity':ID}));lines=[]
   receipt=d.export(p,ID,sorted(r.ALLOWED),lambda line,**kw:lines.append(line));self.assertEqual(receipt['status'],'emitted_incomplete');return ('\n'.join(lines)+'\n').encode()
 def test_roundtrip_and_no_models(self):
  files,receipt=r.decode(self.fixture(),ID);self.assertEqual(set(files),{'identity.json','result.json'});self.assertEqual(receipt['status'],'transport_verified_scientific_review_pending')
 def test_truncation_duplication_corruption(self):
  raw=self.fixture();lines=raw.splitlines(True)
  for bad in [b''.join(lines[:-1]),raw+raw,b''.join([lines[0],lines[1],lines[1],*lines[2:]]),raw.replace(b'"index":0',b'"index":1')]:
   with self.assertRaises((ValueError,KeyError)):r.decode(bad,ID)
 def test_missing_and_unknown_file_entries(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'identity.json').write_bytes(d.enc(ID));(p/'result.json').write_bytes(d.enc({'identity':ID}))
   for names in [['identity.json','result.json'],sorted(r.ALLOWED)+['unknown.json']]:
    lines=[];d.export(p,ID,names,lambda line,**kw:lines.append(line))
    with self.assertRaises(ValueError):r.decode(('\n'.join(lines)+'\n').encode(),ID)
 def test_wrong_identity(self):
  with self.assertRaises(ValueError):r.decode(self.fixture(),{**ID,'pod_uid':'other'})
 def test_gzip_bomb_and_trailing(self):
  with self.assertRaises(ValueError):r.decompress(gzip.compress(b'x'*(r.MAX_FILE+1)))
  with self.assertRaises(ValueError):r.decompress(gzip.compress(b'{}')+b'trailing')
 def test_source_symlink_and_byte_bound(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'a').write_bytes(b'123');(p/'b').symlink_to(p/'a')
   with self.assertRaises(OSError):d.read_regular(p/'b',3)
   with self.assertRaises(ValueError):d.read_regular(p/'a',2)
 def test_encoded_budget(self):
  old=d.MAX_ENCODED;d.MAX_ENCODED=8
  try:
   with tempfile.TemporaryDirectory() as tmp:self.assertEqual(d.export(Path(tmp),ID,[],lambda *a,**kw:None)['status'],'refused_encoded_budget')
  finally:d.MAX_ENCODED=old
 def test_missing_outputs_and_completion(self):
  with tempfile.TemporaryDirectory() as tmp:
   receipt=d.export(Path(tmp),ID,['result.json'],lambda *a,**kw:None)
   self.assertEqual(receipt['status'],'emitted_incomplete');self.assertEqual(receipt['missing_or_refused'],['result.json'])
  self.assertEqual(d.completion({'certify':0,'a26':0},None,5,{'status':'emitted_complete'}),[])
  for codes,n,receipt in [({'certify':1,'a26':0},5,{'status':'emitted_complete'}),({'certify':0,'a26':0},4,{'status':'emitted_complete'}),({'certify':0,'a26':0},5,{'status':'emitted_incomplete'})]:self.assertTrue(d.completion(codes,None,n,receipt))
 def test_aggregate_budget_stops_reads(self):
  old=d.MAX_TOTAL;d.MAX_TOTAL=5
  try:
   with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);(p/'a.json').write_bytes(b'null');(p/'b.json').write_bytes(b'null');(p/'c.json').write_bytes(b'null')
    receipt=d.export(p,ID,['a.json','b.json','c.json'],lambda *a,**kw:None)
    self.assertEqual(receipt['source_bytes_read'],4);self.assertEqual(receipt['missing_or_refused'],['b.json','c.json'])
  finally:d.MAX_TOTAL=old
 def test_captured_object_guards(self):
  candidate=json.loads((HERE/'CANDIDATE.json').read_bytes());directory=Path(candidate['prepare_stdout']);tool=r.load_tool();record=tool.validate_dir(directory);job,handoff=tool.manifests(record);source=record['source_configmap'];job['metadata']['uid']='job-uid';pod={'metadata':copy.deepcopy(job['spec']['template']['metadata']),'spec':copy.deepcopy(job['spec']['template']['spec'])};pod['metadata'].update(uid='pod-uid',namespace='cms-ml',ownerReferences=[{'controller':True,'uid':'job-uid','name':job['metadata']['name'],'kind':'Job'}]);pod['spec']['containers'][0]['env'].append({'name':'NVIDIA_VISIBLE_DEVICES','value':'void'})
  args=[directory,job,pod,source,handoff,'job-uid','pod-uid'];r.validate_objects(*args)
  for value in ['all','0']:
   changed=copy.deepcopy(pod);changed['spec']['containers'][0]['env'][-1]['value']=value
   with self.assertRaises(ValueError):r.validate_objects(directory,job,changed,source,handoff,'job-uid','pod-uid')
  for field,value in [('env',[{'name':'UNAPPROVED','value':'1'}]),('args',['override']),('lifecycle',{'postStart':{'exec':{'command':['unexpected']}}})]:
   changed=copy.deepcopy(pod);changed['spec']['initContainers'][0][field]=value
   with self.assertRaises(ValueError):r.validate_objects(directory,job,changed,source,handoff,'job-uid','pod-uid')
  for field in ['subPath','subPathExpr']:
   changed=copy.deepcopy(pod);changed['spec']['containers'][0]['volumeMounts'][0][field]='redirect'
   with self.assertRaises(ValueError):r.validate_objects(directory,job,changed,source,handoff,'job-uid','pod-uid')
  changed=copy.deepcopy(pod);changed['metadata']['ownerReferences'][0]['uid']='other'
  with self.assertRaises(ValueError):r.validate_objects(directory,job,changed,source,handoff,'job-uid','pod-uid')
 def test_oversize_refusal_names_size_and_limit(self):
  with tempfile.TemporaryDirectory() as tmp:
   p=Path(tmp);(p/'big.json').write_bytes(b'{}'+b' '*30)
   with self.assertRaisesRegex(ValueError,'32 bytes exceeds 16-byte limit'):d.read_regular(p/'big.json',16)
   (p/'identity.json').write_bytes(d.enc(ID));(p/'result.json').write_bytes(d.enc({'identity':ID}))
   old=d.MAX_FILE;d.MAX_FILE=16
   try:receipt=d.export(p,ID,['big.json'],lambda line,**kw:None)
   finally:d.MAX_FILE=old
   self.assertEqual(receipt['missing_or_refused'],['big.json'])
if __name__=='__main__':unittest.main()
