import datetime, json, re, subprocess, time
from pathlib import Path
job='kai-ebops-n8-0911-e1000-b350k-s1'
out=Path('/Users/kaiyamaguchi/Downloads/bnjettag-training-results/bnjettag/results/ebops-n8-long-20260911/launch')
k=['kubectl','--context','nautilus','-n','cms-ml','--request-timeout=20s']
for attempt in range(30):
    pods=json.loads(subprocess.check_output(k+['get','pods','-l','job-name='+job,'-o','json']))['items']
    p=pods[0] if pods else {}
    phase=p.get('status',{}).get('phase','Pending')
    result=subprocess.run(k+['logs','job/'+job],capture_output=True,text=True)
    log=result.stdout
    (out/'startup.log').write_text(log)
    urls=re.findall(r'https://wandb.ai/[^\s\x1b]+/runs/[a-zA-Z0-9]+',log)
    marks=[line for line in log.splitlines() if any(s in line for s in ('[gpu]', '[wandb] authentication OK', 'EBOPS_LONG_ALL_PASS', '[data]', '[budget] initial=', 'Epoch 1/1000', 'Epoch 2/1000'))]
    record={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'job':job,'pod':p.get('metadata',{}).get('name'),'node':p.get('spec',{}).get('nodeName'),'phase':phase,'run_url':urls[-1] if urls else None,'first_epoch_complete':'Epoch 2/1000' in log,'milestones':marks[-12:]}
    (out/'startup_status.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(record),flush=True)
    if record['first_epoch_complete']:
        break
    if phase in ('Failed','Succeeded'):
        print(log[-5000:],flush=True)
        raise SystemExit('Job ended before first epoch verification')
    time.sleep(45)
else:
    print('Startup still pending; saved current state.',flush=True)
