"""Build public continuation evidence, excluding private pilot and infrastructure data."""
from pathlib import Path
import collections
import json
import re

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
OPS=BASE/'local/continuation-20260920'
ROOT=BASE/'publication-status-20260920'
DOC=ROOT/'docs/current-work'
def read(p):return json.loads(p.read_text())
def write(p,x):p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
monitor=read(OPS/'monitor-current.json')
stamp=monitor['checked_at']
jobs=[]
for label,batch,base_epoch in [('arch','batch20260917',100),('attn','batch20260918',400)]:
 manifest=read(OPS/(label+'-job.json'))
 name=manifest['metadata']['name']
 pods=[p for p in monitor['pods'] if p['job']==name]
 rows=[]
 for p in sorted(pods,key=lambda p:int(p['index'])):
  resumes=[];epoch_lines=[]
  logfile=OPS/(p['pod']+'.log')
  if logfile.exists():
   for line in logfile.read_text().splitlines():
    if 'resume_epoch=' in line:resumes.append(line)
    m=re.search(r'\[epoch (\d+)/1000\]',line)
    if m:epoch_lines.append(int(m[1]))
  rows.append({'index':int(p['index']),'pod_phase':p['phase'],
   'scheduled':any(c['type']=='PodScheduled' and c['status']=='True' for c in p['conditions']),
   'resume_epoch_observed':base_epoch if any(f'resume_epoch={base_epoch}' in line for line in resumes) else None,
   'latest_observed_completed_epoch':max(epoch_lines) if epoch_lines else None})
 jobs.append({'batch':batch,'job_name':name,'status':'submitted','screening_completed_epochs':base_epoch,
 'target_epochs':1000,'run_count':manifest['spec']['completions'],
 'configured_parallelism':manifest['spec']['parallelism'],
 'active_deadline_seconds':manifest['spec']['activeDeadlineSeconds'],
 'backoff_limit_per_index':manifest['spec']['backoffLimitPerIndex'],
 'pod_phases':dict(collections.Counter(r['pod_phase'] for r in rows)),'runs':rows})
record={'schema_version':1,'snapshot_at_utc':stamp,
 'scope':'27 public architecture/attention continuations; separate private studies are not included.',
 'policy':'All current arms continue to their unchanged1000-epoch schedules; selective screening promotion is superseded.',
 'preflight':'PREFLIGHT_ALL_PASS: existing checkpoints, canonical config/source hashes and1000-epoch schedules verified; no completed run is restarted.',
 'scientific_identity':'Original immutable source bundles, configurations, data roots, optimizer state and training arithmetic preserved.',
 'scheduling_note':'Full campaign parallelism; pending runs start as shared-cluster capacity becomes available. Running pod phase can include dependency installation.',
 'jobs':jobs}
write(DOC/'continuation-20260920.json',record)
lines=['# Full-length continuation — 20 September 2026','',
 'All **27 current public training runs** have been submitted to complete their existing **1,000-epoch schedules**. This supersedes selective promotion for the architecture and attention screens. The original seven EBOP ablations are already complete and are not rerun.','',
 f'Execution snapshot: **{stamp}**. [Machine-readable status](continuation-20260920.json) · [Recovered screening metrics](TRAINING_PROGRESS_20260920.md) · [Checkpoint preflight evidence](checkpoint-screen-status-20260920.json).','',
 '| Campaign | Runs | Resume checkpoint | Target | Pod phases |','|---|---:|---:|---:|---|']
for j in jobs:
 phases=', '.join(f'{n} {phase}' for phase,n in j['pod_phases'].items())
 lines.append(f"| {j['batch']} | {j['run_count']} | {j['screening_completed_epochs']} | 1,000 | {phases} |")
lines.extend(['','Pending runs are submitted, not missing. The scheduler starts them as compatible GPUs, CPU and memory become available. A Running container may still be installing dependencies; per-index resume and completed-epoch observations are recorded separately in the JSON.', '',
 '## Checkpoint and schedule continuity','',
 'The CPU inspection verified every saved screening checkpoint against its submitted code and canonical configuration hashes. All configurations already specify1,000 epochs, and none has a full-training COMPLETE marker. Each trainer retains its existing output root, optimizer/controller state and data identity. No model source, training configuration, learning-rate schedule or TF32 setting was changed.', '',
 'The screening wrapper accepts only100/200/400-epoch stops. These continuations call the same frozen trainer directly and omit the screening-stop argument, allowing the configured1,000 epochs and normal completion/artifact path to execute. Three-seed attention comparisons retain seeds4,5,6.', '',
 'Each public campaign can run all its indexes concurrently (12 and15), subject to scheduler capacity. Indexed retries preserve checkpoints, with six retries per index, a14-day whole-job deadline and a71-hour process timeout. Jobs run independently of the laptop. These limits do not guarantee a completion time.', '',
 '## Metrics and remaining interpretation','',
 'All six previously unavailable attention summaries were recovered from W&B. All15 attention last checkpoints are over350k EBOPs, with27.6992%–42.0290% internal-validation accuracy. Preflight also confirms that all27 durable screening states record no feasible checkpoint at their own final targets. Full training is being continued under the existing protocol; no accuracy or budget improvement is assumed.', '',
 'The earlier100/400-epoch snapshots remain linked as historical measurements. New resumed measurements retain their source timestamps. Final selected-checkpoint evaluation and hardware validation are separate from a job reaching1,000 epochs.', '',
 '[Return to current work](README.md).'])
# Keep ordinary prose spacing around numbers.
text='\n'.join(lines)+'\n'
for old,new in [('specify1,000','specify 1,000'),('only100','only 100'),('configured1,000','configured 1,000'),('seeds4','seeds 4'),('and15','and 15'),('a14-day','a 14-day'),('a71-hour','a 71-hour'),('All15','All 15'),('over350k','over 350k'),('with27.6992','with 27.6992'),('all27','all 27'),('earlier100','earlier 100'),('reaching1,000','reaching 1,000')]:text=text.replace(old,new)
(DOC/'FULL_LENGTH_CONTINUATION_20260920.md').write_text(text)

p=DOC/'README.md';text=p.read_text()
start=text.index('## Current execution status')+len('## Current execution status\n\n');end=text.index('The separate [R4 hardware study]',start)
count=collections.Counter(p['pod_phase'] for j in jobs for p in j['runs'])
phases=', '.join(f'{n} {phase}' for phase,n in count.items())
text=text[:start]+f'''**All27 public architecture and attention runs are submitted for full1,000-epoch continuation.** Snapshot **{stamp}**: {phases}. Pending runs are queued for shared resources; Running containers may still be starting. The original seven ablations have already completed1,000 epochs.

**[Continuation status and checkpoint guarantees](FULL_LENGTH_CONTINUATION_20260920.md)** · **[Complete screening metrics](TRAINING_PROGRESS_20260920.md)**. The six previously unavailable attention summaries were recovered from W&B. All15 last screening checkpoints exceed350k EBOPs, and all27 durable screening states record no feasible checkpoint at their own targets. Per-run source timestamps distinguish historical screening metrics from resumed execution.

'''+text[end:]
for old,new in [('All27','All 27'),('full1,000','full 1,000'),('completed1,000','completed 1,000'),('All15','All 15'),('exceed350k','exceed 350k'),('all27','all 27')]:text=text.replace(old,new)
p.write_text(text)
p=ROOT/'README.md';text=p.read_text();start=text.index('**[Current-work hub:');start=text.index('\n\n',start)+2;end=text.index('\n\n[Live training curves]',start)
text=text[:start]+'''All **27 current architecture and attention runs** have been submitted to complete their existing **1,000-epoch schedules**, resuming from the100- and400-epoch screening checkpoints. All seven original EBOP ablations have already finished1,000 epochs. The six missing attention summaries have been recovered from W&B. See the **[continuation status](docs/current-work/FULL_LENGTH_CONTINUATION_20260920.md)** and **[complete screening results](docs/current-work/TRAINING_PROGRESS_20260920.md)** for execution evidence, metrics and budget limitations. Frozen-backbone classifier refinements and FPGA implementation remain separate follow-up stages.'''.replace('the100- and400-','the 100- and 400-').replace('finished1,000','finished 1,000')+text[end:]
p.write_text(text)
p=DOC/'TRAINING_PROGRESS_20260920.md';text=p.read_text();header='# Training progress — 20 September 2026\n'
if 'Later execution update:' not in text:text=text.replace(header,header+'\n**Later execution update:** all27 public architecture/attention runs are submitted for full-length continuation. [Current continuation status](FULL_LENGTH_CONTINUATION_20260920.md). The screening-completion observations below retain their original times.\n'.replace('all27','all 27'),1)
text=text.replace('Continuation execution is recorded separately when verified.','See the [verified submission and continuation record](FULL_LENGTH_CONTINUATION_20260920.md).')
p.write_text(text)
for filename in ('BATCH20260918_ATTENTION_STUDY.md','TRAINING_BATCH_PLAN_WITH_FROZEN_BACKBONE_FOLLOWUP.md'):
 p=DOC/filename;text=p.read_text();first,rest=text.split('\n',1)
 if 'Continuation amendment (20 September)' not in text:text=first+'\n\n**Continuation amendment (20 September):** all current architecture/attention arms will complete their existing1,000-epoch schedules, superseding selective promotion below. Original scientific settings remain fixed. [Execution record](FULL_LENGTH_CONTINUATION_20260920.md).\n'.replace('existing1,000','existing 1,000')+rest
 p.write_text(text)
for filename in ('live-status.json','batch20260918-status.json'):
 p=DOC/filename;x=read(p);j=next(j for j in jobs if j['batch']==x['batch'])
 x['continuation_status']={'source':'continuation-20260920.json','snapshot_at_utc':stamp,'job_name':j['job_name'],'target_epochs':1000,'status':'submitted'}
 x['screening_snapshot_note']='Per-run metric/phase values below describe the completed screening stop. Consult continuation_status for subsequent execution.'
 write(p,x)
print('Built public continuation evidence at',stamp,phases)
