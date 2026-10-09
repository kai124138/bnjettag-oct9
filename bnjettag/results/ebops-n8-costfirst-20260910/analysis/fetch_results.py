import json
from pathlib import Path
import datetime
import wandb
out=Path('/tmp/bnjettag-costfirst-analysis')
api=wandb.Api(timeout=90)
rows=[]
for run in api.runs('kayamaguchi-uc-san-diego/BNJetTag-EBOPs-N8', filters={'group':'ebops-n8-20260910-costfirst'}):
    d=out/run.id
    d.mkdir(exist_ok=True)
    summary=dict(run.summary)
    row={'id':run.id,'name':run.name,'state':run.state,'url':run.url,'config':run.config,'summary':summary,'artifacts':[]}
    history=list(run.scan_history(page_size=200))
    (d/'history.json').write_text(json.dumps(history,indent=2,default=str)+'\n')
    for art in run.logged_artifacts():
        a={'name':art.name,'type':art.type,'state':art.state}
        if art.type=='model':
            a['local_path']=art.download(root=str(d/'artifact'))
        row['artifacts'].append(a)
    (d/'run.json').write_text(json.dumps(row,indent=2,default=str)+'\n')
    rows.append(row)
    keys=['best_val_macro_auc','best_epoch','epoch','ebops','beta','budget_met','checkpoint','checkpoint_ebops','target_ebops','activation_bits_mean','activation_width_sites_changed']
    print(json.dumps({'id':run.id,'name':run.name,'state':run.state,'history_rows':len(history),'metrics':{k:summary.get(k) for k in keys},'artifacts':row['artifacts']},default=str),flush=True)
(out/'runs.json').write_text(json.dumps({'fetched_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runs':rows},indent=2,default=str)+'\n')
