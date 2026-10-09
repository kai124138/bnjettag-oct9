"""Read training summaries; credentials stay in memory, evidence stays local."""
import base64
import datetime
import json
from pathlib import Path
import subprocess
import sys
import urllib.request

OUT = Path(__file__).resolve().parent
key = base64.b64decode(subprocess.check_output([
    'kubectl', '-n', 'cms-ml', 'get', 'secret', 'kai-wandb',
    '-o', 'jsonpath={.data.WANDB_API_KEY}'], text=True)).decode().strip()
query = '''query($entity:String!, $project:String!) {
 project(name:$project, entityName:$entity) {
 name access runs(first:100) { pageInfo { hasNextPage }
 edges { node { name displayName state summaryMetrics } } }
 }}'''
keys = {'completed_epochs', 'epochs_run', 'epoch', 'phase', 'screening_target_epochs',
 'val_categorical_accuracy', 'val_macro_auc', 'ebops', 'epoch_seconds',
 'best_feasible_val_accuracy', 'best_feasible_val_macro_auc', 'best_feasible_ebops',
 'best_feasible_epoch', 'train_seconds', '_runtime', '_timestamp', 'best_feasible_val_auc',
 'selected_validation_accuracy','selected_validation_macro_auc','selected_native_backbone_ebops',
 'selected_custom_estimated_bitops','selected_augmented_cost','selected_cost_convention',
 'screening_completed_epochs','physics_test_set_used','hardware_validated'}
projects=sys.argv[1:] or ['BNJetTag-Batch20260917', 'BNJetTag-EBOPs-N8', 'BNJetTag-Engram-Experimental']
for project in projects:
 req = urllib.request.Request('https://api.wandb.ai/graphql', data=json.dumps({
  'query':query, 'variables':{'entity':'kayamaguchi-uc-san-diego','project':project}}).encode(),
  headers={'Content-Type':'application/json','Authorization':'Basic '+base64.b64encode(('api:'+key).encode()).decode()})
 with urllib.request.urlopen(req,timeout=45) as response: data=json.load(response)
 if data.get('errors'): raise RuntimeError('W&B query failed')
 p=data['data']['project']
 assert p and not p['runs']['pageInfo']['hasNextPage']
 rows=[]
 for edge in p['runs']['edges']:
  node=edge['node']; summary=json.loads(node['summaryMetrics'] or '{}')
  rows.append({'id':node['name'],'name':node['displayName'],'state':node['state'],
   'summary':{k:v for k,v in summary.items() if k in keys or k.startswith(('memory/','cost/'))}})
 result={'project':project,'access':p['access'],'fetched_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':rows}
 (OUT/(project+'.json')).write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
 print(project,p['access'],len(rows),'runs')
 for r in rows:
  print(r['name'],r['state'],json.dumps(r['summary'],sort_keys=True))
