"""Bounded metadata-only export, copied from reviewed historical readout transport."""
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
            before=os.fstat(f);need(stat.S_ISREG(before.st_mode) and before.st_size<=limit,'not regular or exceeds byte limit')
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
            entries.append({'name':name,'status':'missing_or_refused','reason':type(e).__name__})
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
