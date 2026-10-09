#!/usr/bin/env python3
"""Bounded local compatibility matrix; historical scientific gates remain separate."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import tarfile
import tempfile
import time
import traceback


CAMPAIGN=Path(__file__).resolve().parent
LAB=CAMPAIGN.parents[1]
PINNED=Path('/home/kaimoe/lab/.venvs/preflight-20261001/bin/python')
ENV={"CUDA_VISIBLE_DEVICES":"-1","WANDB_MODE":"disabled","KERAS_BACKEND":"tensorflow",
     "OMP_NUM_THREADS":"2","TF_NUM_INTRAOP_THREADS":"2","TF_NUM_INTEROP_THREADS":"1",
     "TF_ENABLE_ONEDNN_OPTS":"0","NVIDIA_TF32_OVERRIDE":"0","PYTHONDONTWRITEBYTECODE":"1",
     "TF_CPP_MIN_LOG_LEVEL":"2","OPENBLAS_NUM_THREADS":"2","MKL_NUM_THREADS":"2"}
ACTIVE_RECEIPT=None
ACTIVE_OUTPUT=None


def refuse_reuse(output,evidence):
    if output.exists() or evidence.exists():raise FileExistsError('Use a new output path for every preflight attempt')


def comparison_status(workers,matched):
    states=[w.get('status') for w in workers]
    if 'FAIL' in states:return 'FAIL'
    if 'TIMEOUT' in states:return 'TIMEOUT'
    if any(s in ['PENDING','MISSING'] for s in states):return 'PENDING'
    return 'PASS' if all(s=='PASS' for s in states) and matched else 'FAIL'


def process_outcome(result,returncode,reason=None):
    result=dict(result)
    if returncode!=0:
        result['worker_reported_status']=result.get('status')
        result.update(status='TIMEOUT' if reason or returncode in [-signal.SIGXCPU,-signal.SIGXFSZ,-signal.SIGKILL] else 'FAIL',error=reason or f'worker exited {returncode}')
    if reason:result.update(status='TIMEOUT',error=reason)
    return result


def record_exception(exc):
    if ACTIVE_RECEIPT is not None and ACTIVE_OUTPUT is not None:
        ACTIVE_RECEIPT.update(status='MERGE_ENGINEERING_INVALID',fatal_error=f'{type(exc).__name__}: {exc}',
                              finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
        ACTIVE_OUTPUT.write_text(json.dumps(ACTIVE_RECEIPT,sort_keys=True,indent=2)+'\n')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def absolute(path):
    p=Path(path)
    return p if p.is_absolute() else LAB/p


def process_group_rss(pgid):
    total=0
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:
            fields=(p/'stat').read_text().rsplit(')',1)[1].split()
            if int(fields[2])==pgid:total+=int(fields[21])*os.sysconf('SC_PAGE_SIZE')
        except (OSError,ValueError,IndexError):pass
    return total


def child_limits():
    resource.setrlimit(resource.RLIMIT_CPU,(120,120))
    resource.setrlimit(resource.RLIMIT_FSIZE,(1024**2,1024**2))


def compare_outputs(original, candidate):
    import numpy as np
    a,b=Path(original['output_file']),Path(candidate['output_file'])
    assert a.resolve()!=b.resolve(),'original and candidate outputs share a path'
    assert sha(a)==original['output_file_sha256'],'original output checksum changed'
    assert sha(b)==candidate['output_file_sha256'],'candidate output checksum changed'
    x,y=np.load(a,allow_pickle=False),np.load(b,allow_pickle=False)
    assert x.shape==y.shape and np.isfinite(x).all() and np.isfinite(y).all()
    return float(np.max(np.abs(x-y)))


def main():
    global ACTIVE_RECEIPT,ACTIVE_OUTPUT
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--capture',default=str(CAMPAIGN/'originals/capture_20261001.json'))
    ap.add_argument('--candidate',default='publication/code/hgq2')
    ap.add_argument('--inventory',default=str(CAMPAIGN/'inventory_20261001.json'))
    ap.add_argument('--environment-lock',default='/home/kaimoe/lab/environment-records/preflight-20261001/requirements.lock')
    ap.add_argument('--phase',choices=['contracts','build','reload','all'],default='all')
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    capture=json.loads(absolute(args.capture).read_text());inventory=json.loads(absolute(args.inventory).read_text())
    assert sha(absolute(args.inventory))==capture['inventory_sha256'],'inventory differs from captured reviewed inventory'
    assert len(inventory['model_configs'])==sum(inventory['counts']['model_configs_by_side'].values())==100
    candidate=absolute(args.candidate);output=absolute(args.output);output.parent.mkdir(parents=True,exist_ok=True)
    evidence=output.parent/output.stem
    refuse_reuse(output,evidence)
    evidence.mkdir()
    candidate_files={str(p.relative_to(candidate)):sha(p) for p in candidate.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
    candidate_sha=digest(candidate_files);environment_sha=sha(absolute(args.environment_lock))
    matrix={'schema_version':1,'phase':args.phase,'claim_scope':'engineering compatibility only; no scientific metrics or optimizer steps',
            'runner_sha256':sha(__file__),'worker_sha256':sha(CAMPAIGN/'preflight_worker.py'),
            'candidate_manifest_sha256':candidate_sha,'candidate_files':candidate_files,
            'environment_lock_sha256':environment_sha,'environment':ENV,'rows':[],
            'historical_metric_status':'PENDING_PROVENANCE_AND_APPLICABILITY',
            'historical_remeasured_width_status':'PENDING_ORIGINAL_CALIBRATION_REFERENCE',
            'limits':{'worker_wall_seconds':180,'contract_worker_wall_seconds':30,'worker_cpu_seconds':120,
                      'rss_bytes':8*1024**3,'aggregate_wall_seconds':5400,'aggregate_child_cpu_seconds':5400},
            'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    matrix['inventory_sha256']=capture['inventory_sha256']
    ACTIVE_RECEIPT,ACTIVE_OUTPUT=matrix,output
    matrix['pending_build_identities']=[c['canonical_sha256']+'-'+c['side'] for c in inventory['model_configs']]
    (evidence/'candidate_manifest.json').write_text(json.dumps(candidate_files,sort_keys=True,indent=2)+'\n')
    began=time.monotonic();cpu_start=resource.getrusage(resource.RUSAGE_CHILDREN);counter=0
    def persist():
        matrix['elapsed_seconds']=round(time.monotonic()-began,3)
        output.write_text(json.dumps(matrix,sort_keys=True,indent=2)+'\n')
    def run_task(task):
        nonlocal counter
        usage=resource.getrusage(resource.RUSAGE_CHILDREN)
        usedcpu=(usage.ru_utime+usage.ru_stime)-(cpu_start.ru_utime+cpu_start.ru_stime)
        if time.monotonic()-began>5400 or usedcpu>5400:
            matrix.update(status='MERGE_ENGINEERING_INCOMPLETE',reason='aggregate engineering budget exhausted');persist();raise SystemExit(2)
        assert sha(__file__)==matrix['runner_sha256'] and sha(CAMPAIGN/'preflight_worker.py')==matrix['worker_sha256'],'preflight code changed during execution'
        counter+=1;name=f'{counter:03d}-{task["label"]}'
        out=evidence/(name+'.json');log=evidence/(name+'.log');request=evidence/(name+'.request.json')
        task={**task,'output':str(out),'is_candidate':Path(task['source'])==candidate};request.write_text(json.dumps(task,indent=2)+'\n')
        env={**os.environ,**ENV};env.pop('PYTHONPATH',None);env.pop('WANDB_API_KEY',None)
        for key in ['BNHGQ2_STORE','BNHGQ2_OUT_ROOT','BNHGQ2_TRAIN_DATA']:env.pop(key,None)
        timeout=180 if task['phase'] in ['build','reload'] else 30
        started=time.monotonic();peak=0;reason=None
        with log.open('w') as stream:
            proc=subprocess.Popen([str(PINNED),str(CAMPAIGN/'preflight_worker.py'),str(request)],env=env,
                                  cwd=LAB,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True,preexec_fn=child_limits)
            while proc.poll() is None:
                peak=max(peak,process_group_rss(proc.pid))
                if time.monotonic()-started>timeout:reason='worker wall timeout'
                elif peak>8*1024**3:reason='worker group RSS limit'
                elif log.stat().st_size>1024**2:reason='worker log limit'
                elif time.monotonic()-began>5400:reason='aggregate wall budget'
                if reason:
                    os.killpg(proc.pid,signal.SIGKILL);proc.wait();break
                time.sleep(.2)
        result=json.loads(out.read_text()) if out.exists() else {'status':'TIMEOUT' if reason else 'FAIL','error':reason or f'worker exit {proc.returncode}'}
        result=process_outcome(result,proc.returncode,reason)
        if log.stat().st_size>1024**2:
            with log.open('r+b') as stream:stream.truncate(1024**2)
            result.update(status='TIMEOUT',error='log cap exceeded; retained first 1 MiB')
        result['execution']={'exit_code':proc.returncode,'seconds':round(time.monotonic()-started,3),'peak_rss_bytes':peak,
                             'request':str(request.relative_to(LAB)),'log':str(log.relative_to(LAB)),'result_file':str(out.relative_to(LAB))}
        if reason:result.update(status='TIMEOUT',error=reason)
        assert sha(__file__)==matrix['runner_sha256'] and sha(CAMPAIGN/'preflight_worker.py')==matrix['worker_sha256'],'preflight code changed during worker execution'
        print(name,result['status'],f'{result["execution"]["seconds"]}s',flush=True)
        return result
    def add(row):
        matrix['rows'].append({**row,'candidate_manifest_sha256':candidate_sha,'environment_lock_sha256':environment_sha});persist()

    persist()
    with tempfile.TemporaryDirectory(prefix='bnjettag-merge-baseline-') as temp, contextlib.ExitStack() as cleanup:
        def writable():
            for p in Path(temp).rglob('*'):
                if p.is_dir():p.chmod(0o755)
        cleanup.callback(writable)
        originals={};manifest_shas={}
        for record in capture['originals']:
            archive=absolute(args.capture).parent.parent/record['archive']
            assert sha(archive)==record['archive_sha256']
            root=Path(temp)/record['side'];root.mkdir()
            with tarfile.open(archive,'r:gz') as tar:
                manifest_bytes=tar.extractfile('SOURCE_MANIFEST.json').read()
                assert hashlib.sha256(manifest_bytes).hexdigest()==record['manifest_sha256']
                manifest=json.loads(manifest_bytes)
                for entry in manifest['files']:
                    rel=Path(entry['path']);assert not rel.is_absolute() and '..' not in rel.parts
                    data=tar.extractfile('hgq2/'+entry['path']).read();assert hashlib.sha256(data).hexdigest()==entry['sha256']
                    p=root/'hgq2'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);p.chmod(0o444)
            originals[record['side']]=root/'hgq2';manifest_shas[record['side']]=record['manifest_sha256']
        for path in Path(temp).rglob('*'):
            if path.is_dir():path.chmod(0o555)
        def pair(phase,label,side,items=None,extra=None):
            task={'phase':phase,'items':items or [],**(extra or {})}
            a=run_task({**task,'source':str(originals[side]),'label':label+'-original'})
            preserved={r['output_file']:sha(r['output_file']) for r in a.get('result',[]) if isinstance(r,dict) and 'output_file' in r} if phase=='reload' else {}
            b=run_task({**task,'source':str(candidate),'label':label+'-candidate'})
            assert all(sha(path)==value for path,value in preserved.items()),'candidate overwrote original predictions'
            return a,b
        if args.phase in ['contracts','all']:
            # Source/config preservation is checked before any execution.
            for side,root in originals.items():
                configs=[c for c in inventory['model_configs'] if c['side']==side]
                assert all(sha(root/'configs'/Path(c['path']).relative_to(inventory['roots'][side]).relative_to('configs'))==sha(candidate/Path(c['path']).relative_to(inventory['roots'][side])) for c in configs)
            add({'id':'exact-config-preservation','status':'PASS','config_count':len(inventory['model_configs'])})
            for phase in ['core','selection','evaluation','teacher','delivered','final_filter']:
                a,b=pair(phase,phase,'publication')
                comparable=phase!='core'
                if phase=='evaluation' and a.get('result') and b.get('result'):
                    comparable_result=all(b['result'].get(k)==v for k,v in a['result'].items())
                else:comparable_result=a.get('result')==b.get('result')
                add({'id':phase,'source_side':'publication','original_manifest_sha256':manifest_shas['publication'],
                     'status':comparison_status([a,b],not comparable or comparable_result),'original':a,'candidate':b})
            result=run_task({'phase':'generator_order','source':str(candidate),'label':'generator-order-candidate'})
            add({'id':'generator-import-order','source_side':'publication+research','status':result['status'],'candidate':result})
            for side in ['research','publication']:
                cfg='configs/r14-l1x3-n8-w1a8.json' if side=='research' else 'configs/pre_conference-n8-w1a8.json'
                a,b=pair('training','training-'+side,side,extra={'config_relative':cfg})
                ok=a['status']==b['status']=='PASS' and all(b['result'].get(k)==v for k,v in a.get('result',{}).items())
                add({'id':'training-'+side,'source_side':side,'original_manifest_sha256':manifest_shas[side],'status':comparison_status([a,b],ok),'original':a,'candidate':b})
            a,b=pair('evaluation','evaluation-research','research')
            add({'id':'evaluation-research','source_side':'research','original_manifest_sha256':manifest_shas['research'],'status':comparison_status([a,b],a.get('result')==b.get('result')),'original':a,'candidate':b})
            a,b=pair('ptw_entry','ptw-entry-research','research')
            add({'id':'ptw-entry-research','source_side':'research','original_manifest_sha256':manifest_shas['research'],'status':comparison_status([a,b],a.get('result')==b.get('result')),'original':a,'candidate':b})
            for side in ['research','publication']:
                names=['gen_r14.py','gen_r15_gamma.py','gen_ptw.py','gen_ebops_n8.py','gen_ebops_ablation.py'] if side=='research' else ['generate_pre_conference.py','generate_softmax_precision.py','gen_ebops_n8.py','gen_ebops_ablation.py']
                for name in names:
                    original='configs/'+name
                    candidate_rel='configs/legacy/'+name if side=='research' and name in ['gen_ebops_n8.py','gen_ebops_ablation.py'] else original
                    a=run_task({'phase':'generators','source':str(originals[side]),'label':side+'-'+name+'-original','generators':[original]})
                    b=run_task({'phase':'generators','source':str(candidate),'label':side+'-'+name+'-candidate','generators':[candidate_rel]})
                    ok=a['status']==b['status']=='PASS' and a.get('result',{}).get(original)==b.get('result',{}).get(candidate_rel)
                    add({'id':'generator-'+side+'-'+name,'source_side':side,'original_manifest_sha256':manifest_shas[side],'status':comparison_status([a,b],ok),'original':a,'candidate':b})
        if args.phase in ['build','all']:
            for side in ['research','publication']:
                items=[{'id':c['config_hash']+'-'+side,'config_relative':str(Path(c['path']).relative_to(inventory['roots'][side])),'config_sha256':c['canonical_sha256']} for c in inventory['model_configs'] if c['side']==side]
                for start in range(0,len(items),5):
                    group=items[start:start+5];a,b=pair('build',f'build-{side}-{start:03d}',side,group)
                    aa={r['id']:r for r in a.get('result',[])};bb={r['id']:r for r in b.get('result',[])}
                    for item in group:
                        ar,br=aa.get(item['id'],{}),bb.get(item['id'],{})
                        ok=a.get('status')==b.get('status')==ar.get('status')==br.get('status')=='PASS' and all(ar.get(k)==br.get(k) for k in ['parameters','input_shape','output_shape','graph_sha256','binary','width_state_sha256'])
                        state=comparison_status([a,b],ok)
                        matrix['pending_build_identities'].remove(item['config_sha256']+'-'+side)
                        add({**item,'source_side':side,'original_manifest_sha256':manifest_shas[side],'status':state,'original':ar or a,'candidate':br or b,'execution':[a['execution'],b['execution']]})
        if args.phase in ['reload','all']:
            configs={c['name']:c for c in inventory['model_configs'] if c['side']=='research'}
            groups={};unmapped=[]
            for cp in inventory['checkpoints']:
                cfg=configs.get(cp['config'])
                if not cfg or cfg['config_hash']!=cp['config_hash']:
                    unmapped.append(cp['path']);continue
                key=(cp['config'],cp['seed']);groups.setdefault(key,[]).append(cp)
            items=[]
            for (name,seed),cps in sorted(groups.items()):
                cfg=configs[name];by_content={}
                for cp in cps:
                    preprocessing=(LAB/cp['path']).with_name('input_std.json')
                    if not preprocessing.exists():unmapped.append(cp['path']);continue
                    by_content.setdefault((sha(LAB/cp['path']),sha(preprocessing)),[]).append(cp)
                for (cksha,stdsha),candidates in by_content.items():
                    cp=sorted(candidates,key=lambda c:len(c['path']))[0];std=(LAB/cp['path']).with_name('input_std.json')
                    if not std.exists():unmapped.extend(c['path'] for c in candidates);continue
                    items.append({'id':digest([cfg['canonical_sha256'],seed,cksha,stdsha]),'config_relative':str(Path(cfg['path']).relative_to(inventory['roots']['research'])),
                                  'config_sha256':cfg['canonical_sha256'],'checkpoint':str(LAB/cp['path']),'checkpoint_sha256':cksha,
                                  'preprocessing':str(std),'preprocessing_sha256':stdsha,'duplicate_paths':[c['path'] for c in candidates],
                                  'mapping_scope':'named config and metadata lookup hash plus explicit current config bytes; historical training-source provenance not established'})
            assert len({item['id'] for item in items})==len(items),'duplicate reload identities'
            matrix['reload_selected_content_identities']=len(items);matrix['unmapped_checkpoint_paths']=sorted(set(unmapped));persist()
            for start in range(0,len(items),5):
                group=items[start:start+5];a,b=pair('reload',f'reload-{start:03d}','research',group)
                aa={r['id']:r for r in a.get('result',[])};bb={r['id']:r for r in b.get('result',[])}
                for item in group:
                    ar,br=aa.get(item['id'],{}),bb.get(item['id'],{});difference=None
                    ok=a.get('status')==b.get('status')==ar.get('status')==br.get('status')=='PASS'
                    if ok:
                        difference=compare_outputs(ar,br)
                        ok=difference<=1e-7 and all(ar[k]==br[k] for k in ['processed_probe_sha256','graph_sha256','width_state_sha256','binary'])
                    state=comparison_status([a,b],ok)
                    add({**item,'source_side':'research','original_manifest_sha256':manifest_shas['research'],'status':state,'max_abs_output_difference':difference,
                         'original':ar or a,'candidate':br or b,'execution':[a['execution'],b['execution']],
                         'historical_metric':'UNKNOWN_APPLICABILITY','stored_vs_remeasured_widths':'PENDING'})
        current={str(p.relative_to(candidate)):sha(p) for p in candidate.rglob('*') if p.is_file() and '__pycache__' not in p.parts}
        assert current==candidate_files,'candidate changed during execution'
    failures=[r['id'] for r in matrix['rows'] if r['status']!='PASS']
    matrix['status']='MERGE_ENGINEERING_FAIL' if any(r['status']=='FAIL' for r in matrix['rows']) else 'MERGE_ENGINEERING_INCOMPLETE' if failures else 'MERGE_ENGINEERING_PASS' if args.phase=='all' else 'MERGE_ENGINEERING_PHASE_PASS'
    matrix['scope_complete']=args.phase=='all';matrix['failed_rows']=failures
    matrix['finished_utc']=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime());persist()
    print(matrix['status'],len(matrix['rows']),'rows',len(failures),'failures',flush=True)
    return bool(failures)


if __name__=='__main__':
    try:sys.exit(main())
    except (Exception,KeyboardInterrupt) as exc:
        record_exception(exc);traceback.print_exc();sys.exit(2)
