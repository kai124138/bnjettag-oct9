"""Read-only campaign status, with actual checkpoint wall intervals for ETA."""
import datetime
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
K = ['kubectl', '--context', 'nautilus', '-n', 'cms-ml']
def get(*args):
    return json.loads(subprocess.check_output(K + list(args), text=True))
jobs = get('get', 'jobs', '-l', 'campaign=constituent-study-20260922', '-o', 'json')['items']
pods = get('get', 'pods', '-l', 'campaign=constituent-study-20260922', '-o', 'json')['items']
running = [p for p in pods if p['status']['phase'] == 'Running']
pod = running[-1]['metadata']['name'] if running else 'kai-engram-full-e1000-0920-0-rwqwp'
remote = '''
from pathlib import Path
import json,datetime
root=Path('/data/constituent-study-20260922/fp32')
result={'snapshot_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'runs':[], 'preflight':[]}
for path in sorted((root/'preflight').glob('shard-*.json')):
 d=json.loads(path.read_text());result['preflight'].append({'file':path.name,'status':d['status'],'runs':len(d['runs'])})
for p in sorted((root/'runs').glob('*')):
 row={'name':p.name}
 if (p/'latest.json').exists():
  latest=json.loads((p/'latest.json').read_text())
  state=json.loads((p/'checkpoints'/latest['checkpoint']/'state.json').read_text())
  row.update(completed_epochs=state['completed_epochs'],best_feasible=state['best_feasible'],lowest=state['lowest'])
  checkpoints=sorted((p/'checkpoints').glob('epoch-*'))
  if len(checkpoints)==2:
   dt=(checkpoints[1]/'state.json').stat().st_mtime-(checkpoints[0]/'state.json').stat().st_mtime
   row.update(last_epoch_wall_seconds=dt,estimated_hours_remaining=(50-state['completed_epochs'])*dt/3600)
 if (p/'screen_result.json').exists():
  row['result']=json.loads((p/'screen_result.json').read_text())
  if row['result']['status']=='verified_canary' and row.get('completed_epochs')==row['result']['completed_epochs']+1:
   row['canary_to_screen_pause_seconds_in_interval']=True
   row.pop('estimated_hours_remaining',None)
   row.pop('last_epoch_wall_seconds',None)
 if (p/'STATIC_INFEASIBLE.json').exists():row['static_infeasible']=json.loads((p/'STATIC_INFEASIBLE.json').read_text())
 row['verified_complete']=(p/'VERIFIED_COMPLETE.json').exists()
 result['runs'].append(row)
print(json.dumps(result))
'''
snapshot = json.loads(subprocess.check_output(K + ['exec', pod, '--', 'python', '-c', remote], text=True))
snapshot['jobs'] = [{'name':j['metadata']['name'], 'status':j.get('status',{})} for j in jobs]
snapshot['pods'] = [{'name':p['metadata']['name'], 'phase':p['status']['phase'],
                     'node':p['spec'].get('nodeName'), 'conditions':p['status'].get('conditions',[])} for p in pods]
(HERE / 'live-status.json').write_text(json.dumps(snapshot,indent=2)+'\n')
print(snapshot['snapshot_utc'], 'preflight', snapshot['preflight'])
for j in snapshot['jobs']:
    print(j['name'], {k:v for k,v in j['status'].items() if k in ['active','succeeded','failed','completedIndexes','failedIndexes']})
for row in snapshot['runs']:
    if row.get('static_infeasible'):
        print(row['name'], 'STATIC_INFEASIBLE', row['static_infeasible']['reason'])
        continue
    print(row['name'], 'epoch',row.get('completed_epochs',0),
          'feasible',bool(row.get('best_feasible')), 'verified',row.get('result',{}).get('status'),
          'last_epoch_s',round(row.get('last_epoch_wall_seconds',0),1),
          'ETA_h',round(row.get('estimated_hours_remaining',0),2))
