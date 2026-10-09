#!/usr/bin/env python3
"""Offline bounded readout log receiver; requires captured exact Job/owned Pod and handoff."""
import argparse, base64, copy, hashlib, importlib.util, json, os, zlib
from pathlib import Path
PREFIX='BNJ_READOUT_EXPORT_V1 ';MAX_ENCODED=4*1024*1024;MAX_FILE=8*1024*1024;MAX_TOTAL=48*1024*1024
RUNS=['chang0926-a-n64-s1','chang0926-a-n64-s2','chang0926-d-n64-s1','chang0926-cprime-n64-s1','chang0926-e1-n64-s1']
ALLOWED={'identity.json','input-manifest.json','runtime.json','result.json','certify-snapshot-0500.json','a26-entropy-epoch-0500.json'}|{'telemetry-'+r+'.jsonl' for r in RUNS}
def need(v,m):
 if not v:raise ValueError(m)
def sha(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,sort_keys=True,separators=(',',':'))+'\n').encode()
def load_tool():
 p=Path(__file__).resolve().parents[3]/'tools/run_handoff.py';s=importlib.util.spec_from_file_location('readout_handoff',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def check_execution(expected,actual,allow_admission=False):
 need(expected.get('ephemeralContainers',[])==actual.get('ephemeralContainers',[]),'unexpected ephemeral containers')
 for key in ('containers','initContainers'):
  need(len(expected.get(key,[]))==len(actual.get(key,[])),'unexpected containers')
  for ec,ac in zip(expected.get(key,[]),actual.get(key,[])):
   for field in ('name','image','command','args','env','envFrom','resources','securityContext','workingDir','lifecycle','livenessProbe','readinessProbe','startupProbe'):
    ev=ec.get(field, [] if field in ('command','args','env','envFrom') else {} if field in ('resources','securityContext','lifecycle','livenessProbe','readinessProbe','startupProbe') else None)
    av=ac.get(field, [] if field in ('command','args','env','envFrom') else {} if field in ('resources','securityContext','lifecycle','livenessProbe','readinessProbe','startupProbe') else None)
    if field=='env' and allow_admission:
     injected=[x for x in av if x.get('name')=='NVIDIA_VISIBLE_DEVICES']
     need(injected in ([],[{'name':'NVIDIA_VISIBLE_DEVICES','value':'void'}]),'unexpected GPU environment injection')
     av=[x for x in av if x not in injected]
    need(ev==av,'changed container execution field: '+field)
   def mounts(c):
    values=copy.deepcopy(c.get('volumeMounts',[]))
    for m in values:
     if m.get('readOnly') is False:m.pop('readOnly')
    return values
   need(mounts(ec)==mounts(ac),'changed mount shape or subPath')
 def volumes(spec):
  values=copy.deepcopy(spec.get('volumes',[]))
  for v in values:
   if v.get('configMap',{}).get('defaultMode')==420:v['configMap'].pop('defaultMode')
   if v.get('persistentVolumeClaim',{}).get('readOnly') is False:v['persistentVolumeClaim'].pop('readOnly')
  return values
 need(volumes(expected)==volumes(actual),'changed volume source')
 for field in ('hostNetwork','hostPID','hostIPC','shareProcessNamespace'):
  need(expected.get(field,False)==actual.get(field,False),'changed pod isolation')
 need(expected.get('securityContext',{})==actual.get('securityContext',{}),'changed pod security context')
def validate_objects(directory,job,pod,source,handoff,job_uid,pod_uid):
 tool=load_tool();record=tool.validate_dir(directory);expected_job,expected_handoff=tool.manifests(record)
 need(tool.subset(expected_job,job),'Job differs from immutable handoff')
 check_execution(expected_job['spec']['template']['spec'],job['spec']['template']['spec'])
 need(tool.subset(record['source_configmap'],source) and tool.subset(expected_handoff,handoff),'immutable ConfigMap differs')
 need(source.get('immutable') is True and handoff.get('immutable') is True,'ConfigMaps not immutable')
 need(job['metadata']['uid']==job_uid and pod['metadata']['uid']==pod_uid,'object UID mismatch')
 need(pod['metadata']['namespace']=='cms-ml','pod namespace mismatch')
 owners=pod['metadata'].get('ownerReferences',[])
 need(len(owners)==1 and owners[0].get('controller') is True and owners[0]['uid']==job_uid and owners[0]['name']==job['metadata']['name'] and owners[0]['kind']=='Job','pod controller mismatch')
 actual=copy.deepcopy(pod['spec']);expected=expected_job['spec']['template']['spec']
 check_execution(expected,actual,allow_admission=True)
 need(len(actual.get('containers',[]))==1 and len(actual.get('initContainers',[]))==1,'unexpected containers')
 for c in actual['containers']+actual['initContainers']:
  env=c.get('env',[]);injected=[e for e in env if e.get('name')=='NVIDIA_VISIBLE_DEVICES']
  need(injected in ([],[{'name':'NVIDIA_VISIBLE_DEVICES','value':'void'}]),'unexpected GPU environment injection')
  if injected:c['env']=[e for e in env if e not in injected]
  if not c.get('env'):c.pop('env',None)
  need(not c.get('envFrom'),'unexpected environment source')
  need(not c.get('resources',{}).get('limits',{}).get('nvidia.com/gpu'),'unexpected GPU')
 need(tool.subset(expected,actual),'owned pod differs from submitted spec')
 rid=tool.identity(record);digest=sha((Path(directory)/'record.json').read_bytes())
 for meta in [job['metadata'],pod['metadata']]:
  need(meta['labels']['bnjettag.io/run-id']==rid and meta['annotations']['bnjettag.io/handoff-sha256']==digest,'handoff annotation mismatch')
 return {'run_id':rid,'handoff_sha256':digest,'job_name':job['metadata']['name'],'pod_uid':pod_uid}
def decompress(raw):
 d=zlib.decompressobj(31);out=d.decompress(raw,MAX_FILE+1)
 need(len(out)<=MAX_FILE and not d.unconsumed_tail and d.eof and not d.unused_data,'invalid/trailing/oversize gzip')
 return out
def decode(log,identity):
 need(len(log)<=16*1024*1024,'captured log too large')
 lines=[line for line in log.decode('utf-8').splitlines() if line.startswith(PREFIX)]
 need(lines and sum(len(x.encode())+1 for x in lines)<=MAX_ENCODED,'missing or oversized export')
 rows=[json.loads(line[len(PREFIX):]) for line in lines];begin=rows[0];end=rows[-1]
 need(begin.get('kind')=='begin' and end.get('kind')=='end','missing envelope boundary')
 for row in (begin,end):
  need(all(row.get(k)==v for k,v in identity.items()),'export identity mismatch')
 need(type(begin.get('chunks')) is int and 0<begin['chunks']<=2048,'invalid chunk count')
 need(len(rows)==begin['chunks']+2 and end.get('chunks')==begin['chunks'] and end.get('sha256')==begin.get('sha256'),'incomplete/duplicate export')
 parts=[]
 for i,row in enumerate(rows[1:-1]):
  need(set(row)=={'kind','run_id','index','data'} and row['kind']=='chunk' and type(row['index']) is int and row['index']==i and row['run_id']==identity['run_id'],'wrong/duplicate chunk')
  parts.append(base64.b64decode(row['data'],validate=True))
 payload=b''.join(parts);need(len(payload)==begin.get('bytes') and sha(payload)==begin['sha256'],'export size/hash mismatch')
 envelope=json.loads(payload);need(envelope.get('schema')==1 and envelope.get('identity')==identity,'payload identity mismatch')
 files={};entries=[];total=0;seen=set()
 for item in envelope['entries']:
  name=item['name'];need(name in ALLOWED and name not in seen,'unknown/duplicate file');seen.add(name)
  if item.get('status')=='missing_or_refused':entries.append(item);continue
  raw=decompress(base64.b64decode(item['gzip_base64'],validate=True));total+=len(raw)
  need(total<=MAX_TOTAL and len(raw)==item['bytes'] and sha(raw)==item['sha256'],'file byte/hash/budget mismatch')
  if name.endswith('.jsonl'):
   for line in raw.splitlines():json.loads(line)
  else:json.loads(raw)
  files[name]=raw;entries.append({k:v for k,v in item.items() if k!='gzip_base64'})
 need(seen==ALLOWED,'missing explicit artifact entries')
 need({'identity.json','result.json'}.issubset(files),'required receipt missing')
 need(json.loads(files['identity.json'])==identity and json.loads(files['result.json'])['identity']==identity,'embedded identity mismatch')
 return files,{'status':'transport_verified_scientific_review_pending','identity':identity,'log_sha256':sha(log),'envelope_sha256':sha(payload),'entries':entries,'bytes':total}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['handoff','job','pod','source-configmap','handoff-configmap','job-uid','pod-uid','log','out']:p.add_argument('--'+name,required=True)
 a=p.parse_args();out=Path(a.out);need(not out.exists(),'output already exists')
 paths={key:Path(getattr(a,key.replace('-','_'))) for key in ['job','pod','source-configmap','handoff-configmap']}
 objects={key:json.loads(path.read_bytes()) for key,path in paths.items()}
 identity=validate_objects(a.handoff,objects['job'],objects['pod'],objects['source-configmap'],objects['handoff-configmap'],a.job_uid,a.pod_uid)
 files,receipt=decode(Path(a.log).read_bytes(),identity)
 receipt['captured_objects']={k:{'path':str(v),'sha256':sha(v.read_bytes())} for k,v in paths.items()};receipt['receiver_sha256']=sha(Path(__file__).read_bytes())
 out.mkdir(parents=False)
 for name,raw in files.items():
  with (out/name).open('xb') as stream:stream.write(raw)
 with (out/'transfer-receipt.json').open('xb') as stream:stream.write(encoded(receipt))
 print(json.dumps({'status':receipt['status'],'files':len(files),'bytes':receipt['bytes']}))
if __name__=='__main__':main()
