"""Build a dated publication update from cluster status and allowlisted log lines."""
from pathlib import Path
import datetime
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'publication-status-20260920'
DOC=ROOT/'docs/current-work'
STAMP='2026-09-20T20:46:42Z'
items=json.loads((HERE/'cluster.json').read_text())['items']
jobs={x['metadata']['name']:x for x in items if x['kind']=='Job'}
pods=[x for x in items if x['kind']=='Pod']
def write(path,data): path.write_text(json.dumps(data,indent=2,allow_nan=False)+'\n')
def final_metric(prefix,index,epoch):
 for p in pods:
  name=p['metadata']['name']
  if not name.startswith(f'{prefix}-{index}-'): continue
  path=HERE/(name+'.log')
  if not path.exists(): continue
  for line in path.read_text().splitlines():
   match=re.search(r'^(\S+) \[epoch (\d+)/(\d+)\] EBOPs=(\d+) target=(\d+) beta=(\S+) (?:val_AUC|AUC)=(\S+)(?: val_accuracy=(\S+))? seconds=(\S+) checkpoint=(\S+)',line)
   if match and int(match[2])==epoch:
    return {'epoch':epoch,'training_horizon_epochs':int(match[3]),'native_ebops':int(match[4]),
      'target_ebops':int(match[5]),'beta':float(match[6]),'validation_macro_ovr_auc':float(match[7]),
      'validation_accuracy':float(match[8]) if match[8] else None,'epoch_seconds':float(match[9]),
      'source_updated_utc':datetime.datetime.fromisoformat(match[1]).astimezone(datetime.timezone.utc).isoformat(),
      'source':'training_log','source_line':line,'source_line_sha256':hashlib.sha256(line.encode()).hexdigest(),
      'metric_precision':'Six decimal places as printed by the trainer; not independently recomputed.'}
 return None

campaign_jobs=['kai-batch0917-screen-e100-r3','kai-batch0918-screen-e400','kai-ebops-abl-0912-e1000']
public_jobs=[]
for name in campaign_jobs:
 j=jobs[name]; s=j['status']
 public_jobs.append({'job_name':name,'status':'Complete','completed_indexes':s['completedIndexes'],
 'succeeded_indexes':s['succeeded'],'started_at_utc':s['startTime'],'completed_at_utc':s['completionTime'],
 'active_workers':s.get('active',0),'failed_pod_attempts':s.get('failed',0)})
write(DOC/'training-status-20260920.json',{'schema_version':1,'cluster_snapshot_at_utc':STAMP,
 'scope':'Public architecture, attention and original EBOP ablation campaigns',
 'source':'Kubernetes Job status and retained training log lines',
 'active_workers':sum(j['active_workers'] for j in public_jobs),'jobs':public_jobs,
 'limitations':['Screen completion is not full 1000-epoch completion.','Some completed container logs are no longer available.',
 'W&B was not refreshed: anonymous reads unavailable; authenticated credential read awaiting approval.',
 'Latest-epoch metrics are not selected-checkpoint results; no new held-out evaluation or hardware validation.']})

b=json.loads((DOC/'batch20260918-status.json').read_text())
j=jobs['kai-batch0918-screen-e400']
b.update(cluster_snapshot_at_utc=STAMP,pod_snapshot_at_utc=STAMP,status='screening_rung_complete',
 active_workers=0,ready_workers=0,pod_phases={'Succeeded':15},completed_at_utc=j['status']['completionTime'],
 completed_runs=15,metrics_refreshed_at_utc=STAMP,metrics_source='retained_training_logs',
 metrics_note='Latest epoch only, rounded to six decimals by trainer. Missing logs do not imply missing training. Historical W&B registration counts below retain their original timestamp.',
 best_feasible_note='Not refreshed; an over-budget last checkpoint does not prove that every earlier checkpoint was over budget.')
source=[]
for r in b['runs']:
 m=final_metric(j['metadata']['name'],r['index'],400)
 r.update(status='paused_for_promotion',completed_epochs=400,epoch_count_source='completed_index_of_fixed_400_epoch_screen',
 run_url=f"{b['project_url']}/runs/{r['run_id']}",latest_validation_accuracy=m['validation_accuracy'] if m else None,
 latest_validation_macro_ovr_auc=m['validation_macro_ovr_auc'] if m else None,
 latest_native_ebops=m['native_ebops'] if m else None,latest_within_final_target=m['native_ebops']<=r['target_ebops'] if m else None,
 latest_beta=m['beta'] if m else None,source_updated_utc=m['source_updated_utc'] if m else None,
 metric_availability='final_epoch_log_available' if m else 'completed_container_log_unavailable',best_feasible=None)
 if m: source.append({'config_name':r['name'],**m})
b['runs_with_final_epoch_metrics']=len(source)
write(DOC/'batch20260918-status.json',b)
write(DOC/'training-log-metrics-20260920.json',{'fetched_on_utc_date':'2026-09-20','scope':'Allowlisted final epoch lines only; no raw logs or credentials.','runs':source})

arms=['tensor_quantization','channel_quantization','reduced_feedforward','attention_probability_8bit','gradual_budget_schedule','fixed_width_recovery','knowledge_distillation']
ab=[]
for i,arm in enumerate(arms):
 m=final_metric('kai-ebops-abl-0912-e1000',i,1000)
 ab.append({'arm':arm,'index':i,'status':'training_complete','completed_epochs':1000,
 'completion_source':'Kubernetes completedIndexes 0-6','latest_epoch_metrics':m,
 'selected_checkpoint_evaluation':'See separately dated ablation_metrics.json; not refreshed by this status update.'})
write(ROOT/'results/post_conference/ablation-training-status-20260920.json',{
 'refreshed_at_utc':STAMP,'job_completed_at_utc':jobs['kai-ebops-abl-0912-e1000']['status']['completionTime'],
 'scope':'Training completion and final-epoch log metrics; distinct from selected-checkpoint held-out evaluation.',
 'runs':ab})

launch=json.loads((DOC/'launch-record.json').read_text()); launch['latest_execution']['snapshot_at_utc']=STAMP
write(DOC/'launch-record.json',launch)
a=json.loads((DOC/'live-status.json').read_text())
a['cluster_verified_at_utc']=STAMP
a['cluster_verification_note']='All 12 recovered screening indexes remain complete; numerical W&B snapshot retains its original 2026-09-18 freshness.'
write(DOC/'live-status.json',a)

table=['| Run | Epochs | Latest val accuracy | Latest val AUC | Latest EBOPs / 350k |','|---|---:|---:|---:|---:|']
for r in b['runs']:
 acc=f"{r['latest_validation_accuracy']*100:.4f}%" if r['latest_validation_accuracy'] is not None else 'Unavailable'
 auc=f"{r['latest_validation_macro_ovr_auc']:.6f}" if r['latest_validation_macro_ovr_auc'] is not None else '—'
 cost=f"{r['latest_native_ebops']:,} / 350,000" if r['latest_native_ebops'] is not None else '—'
 table.append(f"| [{r['arm'].upper()} / seed {r['seed']}]({r['run_url']}) | 400 / 1,000 | {acc} | {auc} | {cost} |")
progress='''# Training progress — 20 September 2026

Cluster verified at **2026-09-20T20:46:42Z** (13:46 PDT). The three public training campaigns have **zero active workers**. Screening runs are awaiting a continuation decision; completion of a screening interval does not imply completion of the configured 1,000-epoch schedule.

| Campaign | Runs | Progress | Execution state |
|---|---:|---|---|
| Architecture screen, A00–A11 | 12 | 100 / 1,000 epochs each | All 12 screening indexes completed September 18 |
| Attention / precision / schedule, B00–B04 × seeds 4–6 | 15 | 400 / 1,000 epochs each | All 15 screening indexes completed September 19 |
| Original EBOP ablations | 7 | 1,000 / 1,000 epochs each | All seven completed; final distillation run finished September 20 |

[Machine-readable job evidence](training-status-20260920.json) · [Architecture metrics](live-status.json) · [Attention metrics](batch20260918-status.json) · [Original ablation completion and final-epoch metrics](../../results/post_conference/ablation-training-status-20260920.json).

## Attention screen: final-epoch observations

All 15 jobs completed the 400-epoch screen. Final-epoch metrics were recoverable from **9 of 15** retained container logs; the other six completed containers no longer expose their logs. Missing values below are unavailable, not zero. These are internal-validation measurements on 124,000 jets, rounded by the trainer to six decimals. They have not been recomputed from saved predictions.

'''+ '\n'.join(table)+'''

**All nine observable last checkpoints exceed the 350,000-EBOP target**, at 465,506–723,763 EBOPs. Their validation accuracies span 31.5903%–41.3782%, and each reports the cost-controller coefficient at its configured maximum, beta=0.001. This indicates that the observed final checkpoints have not achieved the intended accuracy/resource tradeoff. It does not establish whether an earlier feasible checkpoint exists, and the six unavailable rows cannot be ranked. No winner or promotion is declared. Inspect complete checkpoint histories and the cost/controller behavior before selecting continuations.

The [allowlisted final-epoch source lines](training-log-metrics-20260920.json) retain timestamps and line hashes. The [protocol](BATCH20260918_ATTENTION_STUDY.md) describes the matched arms and final-budget selection rule. Full three-seed comparisons require the six missing summaries and selected-checkpoint records.

## Architecture screen

The original 12-run screen remains complete at 100 epochs per run, with no continuation job present at this cluster check. The existing September 18 W&B metrics remain the latest verified numerical snapshot. Every latest checkpoint in that snapshot exceeds its own target. A11 records 61.2129% validation accuracy at 688,677 EBOPs against its 500k target; among the 350k-target rows, A00 records 58.3468% at 599,799 EBOPs. These observations are not feasible-checkpoint selections or claims of statistical superiority.

## Original seven ablations

The 1,000-epoch job completed all seven indexes at **2026-09-20T06:08:41Z**. The previously stalled distillation arm resumed and reached epoch 1,000: its final training-log AUC is **0.844425**, at **344,430 EBOPs**. This is the final epoch, not necessarily the selected checkpoint; no categorical accuracy was printed on that line.

The main README's September 15 held-out table is a separately dated evaluation snapshot. Its interim checkpoint evaluations remain historical until final selected checkpoints are re-evaluated. Training completion alone does not update held-out accuracy or checkpoint digests.

## Verification scope

This update uses read-only Kubernetes job status and retained logs. An anonymous W&B query did not expose the projects; authenticated metric refresh is awaiting approval to read the stored credential. Existing W&B source timestamps are preserved. No training was started, resumed, or promoted, and no model, dataset, project visibility, or hardware measurement changed. The earlier fixed-precision study remains the archived 60-run result set in the main README.

[Return to current work](README.md).
'''
(DOC/'TRAINING_PROGRESS_20260920.md').write_text(progress)
readme=(DOC/'README.md').read_text().replace('**Updated 18 September 2026','**Updated 20 September 2026')
readme=readme.replace('A further 15 training runs have been submitted to test attention design, attention precision, and compression timing.', 'The further 15 runs testing attention design, attention precision, and compression timing have completed their 400-epoch screen. All seven original ablations have now completed 1,000 epochs.')
start=readme.index('Cluster checked at **'); end=readme.index('The separate [R4 hardware study]',start)
readme=readme[:start]+'''Cluster checked at **2026-09-20T20:46:42Z**. **No training workers are active.** The original architecture screen completed **12/12 runs at 100 epochs**, the attention follow-up completed **15/15 runs at 400 epochs**, and the original EBOP ablations completed **7/7 runs at 1,000 epochs**. Screening runs retain their unchanged 1,000-epoch schedules and await a continuation decision.

**[Full September 20 progress report and per-run metrics](TRAINING_PROGRESS_20260920.md).** Final-epoch logs are available for 9 of 15 attention runs: all nine exceed 350k EBOPs, with 31.5903%–41.3782% validation accuracy and beta=0.001. The other six metric rows remain unavailable. Review checkpoint histories and budget-controller behavior before promotion; no selected winner is established. The architecture table below retains its September 18 W&B metric timestamp.

'''+readme[end:]
readme=readme.replace('## The 15 additional runs now launching','## The 15 additional runs: 400-epoch screen complete')
(DOC/'README.md').write_text(readme)
study=(DOC/'BATCH20260918_ATTENTION_STUDY.md').read_text()
study=study.replace('**Campaign `batch20260918` · submitted 2026-09-18T12:14:11Z**','**Campaign `batch20260918` · all 15 screening runs completed 2026-09-19T10:05:38Z · verified 20 September**')
study=study.replace('[Current results and startup status](README.md)','[Current results and completion status](TRAINING_PROGRESS_20260920.md)')
study=study.replace('The timestamped worker counts are in the [status record](batch20260918-status.json); submission and Running/Ready status do not prove a completed training epoch.', 'All 15 indexes completed the 400-epoch rung; zero workers remain active at the September 20 check. The [status record](batch20260918-status.json) and [progress report](TRAINING_PROGRESS_20260920.md) record completion and the available final-epoch metrics.')
(DOC/'BATCH20260918_ATTENTION_STUDY.md').write_text(study)
readme=(ROOT/'README.md').read_text()
old='The active batch tests 12 binary-transformer architectures and EBOP budgets, selecting checkpoints by validation accuracy. Runs are screened at 100, 200 and 400 epochs before longer, multi-seed confirmation. The hub explains the intent of each run, shows the experiment diagrams, and links to live training curves and dated status snapshots. Frozen-backbone classifier refinements and II=1 hybrid-DSP implementation studies are separate follow-up stages.'
new='As of **20 September 2026**, all 12 architecture runs have completed their 100-epoch screen, all 15 attention/precision/schedule runs have completed their 400-epoch screen, and all seven original EBOP ablations have finished 1,000 epochs. No training workers are active. The nine recoverable final-epoch attention logs all remain over budget; continuation requires checkpoint-history and controller review. See the **[dated progress report and per-run results](docs/current-work/TRAINING_PROGRESS_20260920.md)** for evidence and missing-metric coverage. Frozen-backbone classifier refinements and II=1 hybrid-DSP implementation studies remain separate follow-up stages.'
assert old in readme
readme=readme.replace(old,new)
readme=readme.replace('Evaluation snapshot: **2026-09-15**. All experiments use eight constituents and one training seed.','Evaluation snapshot: **2026-09-15**. All experiments use eight constituents and one training seed. All seven training runs have since completed 1,000 epochs; the checkpoint evaluations below retain their original date and interim labels pending final re-evaluation. [Training completion record](results/post_conference/ablation-training-status-20260920.json).')
(ROOT/'README.md').write_text(readme)

# Keep the deliberately private pilot's numerical report in the local workspace.
private=[]
for i in range(4):
 private.append({'arm':f'E{i:02d}','completed_epochs':100,'report_status':'complete' if i in (2,3) else 'reload_check_failed',
 'latest_epoch_metrics':final_metric('kai-engram-screen-e100-a10364ed',i,100)})
write(HERE/'engram-status.json',{'cluster_verified_at_utc':STAMP,'visibility':'local_only_private_pilot',
 'job_status':'Failed','completed_report_indexes':[2,3],'failed_report_indexes':[0,1],
 'finalize_retry_submitted':False,'runs':private})
print('Updated public documentation; retained Engram metrics locally. Attention log coverage:',len(source),'/ 15')
