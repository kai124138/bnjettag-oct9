import json,subprocess,concurrent.futures,re,datetime
from pathlib import Path
out=Path(__file__).parent
p=subprocess.run(['kubectl','-n','cms-ml','get','pods','-l','continuation=full1000-20260920','-o','json'],check=True,capture_output=True,text=True)
pods=json.loads(p.stdout)['items'];(out/'pods-current.json').write_text(p.stdout)
def one(p):
 name=p['metadata']['name'];row={'pod':name,'index':p['metadata']['labels'].get('batch.kubernetes.io/job-completion-index'),'job':p['metadata']['labels'].get('job-name'),'phase':p['status']['phase'],'node':p['spec'].get('nodeName'),'reason':p['status'].get('reason'),'message':p['status'].get('message')}
 row['conditions']=p['status'].get('conditions',[])
 r=subprocess.run(['kubectl','-n','cms-ml','logs',name,'--tail=100'],capture_output=True,text=True,timeout=45)
 (out/(name+'.log')).write_text(r.stdout+r.stderr)
 row['milestones']=[s for s in r.stdout.splitlines() if re.search(r'resume_epoch|\[epoch|PASS|Error|Traceback|Requirement already|Successfully installed',s)]
 row['last_lines']=r.stdout.splitlines()[-3:]
 return row
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex: rows=list(ex.map(one,pods))
summary={'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pods':rows};(out/'monitor-current.json').write_text(json.dumps(summary,indent=2))
for r in rows:
 print(r['pod'],r['phase'],r['node'],r['milestones'][-1:] or r['last_lines'][-1:])
