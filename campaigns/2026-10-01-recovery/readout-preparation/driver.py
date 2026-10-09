#!/usr/bin/env python3
"""NRP-only historical readout wrapper; immutable inputs, bounded JSON telemetry export."""
import base64, gzip, hashlib, importlib.metadata, json, os, stat, subprocess, sys, time
from pathlib import Path
MAX_FILE=8*1024*1024
MAX_TOTAL=48*1024*1024
MAX_ENCODED=4*1024*1024
PREFIX='BNJ_READOUT_EXPORT_V1 '
def sha(b): return hashlib.sha256(b).hexdigest()
def enc(v): return (json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
def need(ok,msg):
    if not ok: raise ValueError(msg)
def read_regular(path,limit):
    path=Path(path); fd=os.open('/',os.O_RDONLY|os.O_DIRECTORY)
    try:
        for part in path.parts[1:-1]:
            new=os.open(part,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW,dir_fd=fd);os.close(fd);fd=new
        f=os.open(path.name,os.O_RDONLY|os.O_NOFOLLOW,dir_fd=fd)
        try:
            before=os.fstat(f);need(stat.S_ISREG(before.st_mode),'not a regular file');need(before.st_size<=limit,f'{before.st_size} bytes exceeds {limit}-byte limit')
            with os.fdopen(os.dup(f),'rb') as stream: raw=stream.read(limit+1)
            after=os.fstat(f);need(len(raw)<=limit and (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'source changed or over limit')
            return raw
        finally: os.close(f)
    finally:os.close(fd)
def export(out,identity,names,printer=print):
    entries=[];total=0;exhausted=False
    for name in names:
        try:
            need(not exhausted and total<MAX_TOTAL,'expanded export budget exhausted')
            remaining=MAX_TOTAL-total
            if (out/name).stat().st_size>remaining:
                exhausted=True;raise ValueError('expanded export budget exhausted')
            raw=read_regular(out/name,min(MAX_FILE,remaining));total+=len(raw)
            # Only named JSON diagnostics; opaque model/cache files cannot enter this list.
            if name.endswith('.jsonl'):
                for line in raw.splitlines(): json.loads(line)
            else:json.loads(raw)
            entries.append({'name':name,'sha256':sha(raw),'bytes':len(raw),'gzip_base64':base64.b64encode(gzip.compress(raw,mtime=0)).decode()})
        except (OSError,ValueError) as e:
            entries.append({'name':name,'status':'missing_or_refused','reason':type(e).__name__,'detail':str(e)})
    payload=enc({'schema':1,'identity':identity,'entries':entries});digest=sha(payload)
    if len(payload)+100000>MAX_ENCODED:
        printer('READOUT_EXPORT_REFUSED encoded_budget_exceeded durable_artifacts_retained',flush=True)
        return {'status':'refused_encoded_budget','bytes':len(payload),'limit':MAX_ENCODED}
    chunks=[base64.b64encode(payload[i:i+2048]).decode() for i in range(0,len(payload),2048)]
    # Base64 plus per-line framing is charged, not merely decoded payload bytes.
    lines=[PREFIX+json.dumps({'kind':'begin',**identity,'sha256':digest,'bytes':len(payload),'chunks':len(chunks)},separators=(',',':'))]
    lines += [PREFIX+json.dumps({'kind':'chunk','run_id':identity['run_id'],'index':i,'data':v},separators=(',',':')) for i,v in enumerate(chunks)]
    lines += [PREFIX+json.dumps({'kind':'end',**identity,'sha256':digest,'chunks':len(chunks)},separators=(',',':'))]
    need(sum(len(x.encode())+1 for x in lines)<=MAX_ENCODED,'encoded export budget exceeded')
    for line in lines:printer(line,flush=True)
    missing=[x['name'] for x in entries if x.get('status')=='missing_or_refused']
    return {'status':'emitted_incomplete' if missing else 'emitted_complete','missing_or_refused':missing,'source_bytes_read':total,'envelope_sha256':digest,'encoded_bytes':sum(len(x.encode())+1 for x in lines),'files':len(entries)}
def completion(codes,failure,telemetry_count,receipt):
    issues=[]
    if failure:issues.append('input_or_readout_failure')
    if codes.get('certify')!=0:issues.append('certify_exit_nonzero_or_not_run')
    if codes.get('a26')!=0:issues.append('a26_exit_nonzero_or_not_run')
    if telemetry_count!=5:issues.append('telemetry_incomplete')
    if receipt.get('status')!='emitted_complete':issues.append('export_incomplete')
    issues.extend(receipt.get('missing_or_refused',[]))
    return issues
def main():
    scope=json.loads(Path('/work/scope.json').read_bytes());out=Path(scope['output']);out.mkdir(exist_ok=False)
    identity={k:os.environ[k.upper()] for k in ('run_id','handoff_sha256','job_name','pod_uid')}
    record=read_regular('/data/run-handoffs/'+identity['run_id']+'/record.json',1000000)
    need(sha(record)==identity['handoff_sha256'],'installed handoff hash mismatch')
    need(json.loads(record)['job']['metadata']['name']==identity['job_name'],'job identity mismatch')
    (out/'identity.json').write_bytes(enc(identity));rows=[];histories=[];failure=None;codes={}
    try:
        for path in scope['expected_absent']:
            need(not os.path.lexists(path),'unexpected divergence marker: '+path)
            rows.append({'path':path,'status':'expected_absent_verified'})
        for item in scope['inputs']:
            raw=read_regular(item['path'],item['bytes']);need(len(raw)==item['bytes'] and sha(raw)==item['sha256'],'recovered input identity mismatch: '+item['path'])
            rows.append({'path':item['path'],'sha256':sha(raw),'bytes':len(raw),'status':'matched_recovered_input'})
        for run in scope['runs']:
            state=json.loads(read_regular(scope['run_root']+'/'+run+'/snapshots/epoch-0500/state.json',MAX_FILE));need(state['completed_epochs']==500,'epoch500 snapshot required')
            path=scope['run_root']+'/'+run+'/activation_widths.jsonl';name='telemetry-'+run+'.jsonl'
            try:
                raw=read_regular(path,MAX_FILE)
                for line in raw.splitlines():json.loads(line)
                (out/name).write_bytes(raw);histories.append(name);rows.append({'path':path,'sha256':sha(raw),'bytes':len(raw),'status':'copied_exact','destination':name})
            except (OSError,ValueError) as e: rows.append({'path':path,'status':'missing_or_refused','reason':type(e).__name__,'detail':str(e)})
        (out/'input-manifest.json').write_bytes(enc({'inputs':rows,'historical_context':'original immutable training handoff unavailable','full_rules':'pending later registered analysis'}))
        versions={p:importlib.metadata.version(p) for p in scope['packages']}
        (out/'runtime.json').write_bytes(enc({'python':sys.version,'packages':versions,'requested_image':scope['image'],'cuda_visible_devices':os.environ.get('CUDA_VISIBLE_DEVICES'),'tf32_policy':'certification explicitly disables TF32; entropy retains its original CPU-only route'}))
        commands={
          'certify':['python','-u','/work/code/campaigns/chang0926/certify_ebops.py','--run-root',scope['run_root'],'--cache',scope['cache'],'--out',str(out/'certify-snapshot-0500.json'),'--snapshot','500','--only',','.join(scope['runs'])],
          'a26':['python','-u','/work/code/analysis/attn_entropy.py','--indices',*map(str,scope['indices']),'--epoch','500','--out',str(out/'a26-entropy-epoch-0500.json')]}
        for name,command in commands.items(): codes[name]=subprocess.run(command,check=False).returncode
        # Rehash every model/config/cache metadata input after analysis. No model writes are permitted.
        for item in scope['inputs']:
            raw=read_regular(item['path'],item['bytes']);need(sha(raw)==item['sha256'],'input changed during readout: '+item['path'])
        for path in scope['expected_absent']:need(not os.path.lexists(path),'divergence marker appeared during readout: '+path)
        for item in rows:
            if item.get('destination'):need(sha(read_regular(item['path'],MAX_FILE))==item['sha256'],'telemetry changed during readout')
    except Exception as e:failure=type(e).__name__+': '+str(e)
    result={'identity':identity,'exit_codes':codes,'failure':failure,'telemetry_complete':len(histories)==5,'full_registered_rule_analysis':'pending','production_gate':'pending','option_c':'selected_new_revision_and_pilot_pending','certification_scope':'feasible primary/AUC selections only; absent feasible selections are not certified'}
    (out/'result.json').write_bytes(enc(result))
    names=['identity.json','input-manifest.json','runtime.json','result.json','certify-snapshot-0500.json','a26-entropy-epoch-0500.json']+['telemetry-'+run+'.jsonl' for run in scope['runs']]
    result['missing_outputs']=[name for name in names if not (out/name).is_file()]
    (out/'result.json').write_bytes(enc(result))
    try:receipt=export(out,identity,names)
    except Exception as e:receipt={'status':'refused','reason':type(e).__name__,'detail':str(e)}
    (out/'export-receipt.json').write_bytes(enc(receipt))
    issues=completion(codes,failure,len(histories),receipt)
    print('READOUT_JOB_DONE certify_exit='+str(codes.get('certify','not_run'))+' a26_exit='+str(codes.get('a26','not_run'))+' missing='+(' none' if not issues else ','.join(issues)),flush=True)
    return 1 if issues else 0
if __name__=='__main__':sys.exit(main())
