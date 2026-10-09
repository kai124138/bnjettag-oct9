#!/usr/bin/env python3
"""Gated launch of the pre-registered seven-run ablation; no unguarded GPU submission."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
DEFAULT=HERE.parents[3]/'results/ebops-n8-ablation-20260912/launch'


def main():
    p=argparse.ArgumentParser()
    p.add_argument('stage',choices=('prepare','preflight','benchmark','train','status'))
    p.add_argument('--out-dir',type=Path,default=DEFAULT)
    a=p.parse_args(); out=a.out_dir
    if a.stage=='prepare':
        subprocess.run([sys.executable,str(HERE/'gen_ebops_ablation_jobs.py'),'--out-dir',str(out)],check=True)
        return
    m=json.loads((out/'launch_manifest.json').read_text())
    k=['kubectl','--context','nautilus','-n','cms-ml']
    def apply(name): subprocess.run(k+['apply','-f',str(out/name)],check=True)
    def require_complete(job,markers=()):
        obj=json.loads(subprocess.check_output(k+['get','job',job,'-o','json']))
        assert obj.get('status',{}).get('succeeded',0)>=1, f'{job} must complete first'
        logs=subprocess.check_output(k+['logs','job/'+job],text=True)
        for marker in markers: assert marker in logs, f'Missing {marker}'
        (out/(job+'.log')).write_text(logs)
        return logs
    if a.stage=='preflight':
        subprocess.run(k+['apply','--server-side','-f',str(out/'configmap.json')],check=True)
        apply('preflight.yaml'); apply('prepare-data.yaml')
    elif a.stage=='benchmark':
        require_complete(m['preflight_job'],('PREFLIGHT_ALL_PASS','EBOPS_ABLATION_ALL_PASS'))
        require_complete(m['prepare_job'],('[data] shared immutable arrays ready',))
        apply('benchmark.yaml')
    elif a.stage=='train':
        logs=require_complete(m['benchmark_job'],('EBOPS_ABLATION_ALL_PASS','[epoch 2/1000]'))
        import re
        match=re.search(r'\[epoch 2/1000\].*seconds=([0-9.]+)',logs)
        assert match
        seconds=float(match.group(1))
        print(f'Benchmark second epoch {seconds:.1f}s; rough 1000-epoch training estimate {(seconds+1)*1000/3600:.1f}h before retry/storage overhead')
        apply('training.yaml')
    else:
        subprocess.run(k+['get','jobs,pods','-l','app=kai-ebops-ablation','-o','wide'],check=True)

if __name__=='__main__':main()
