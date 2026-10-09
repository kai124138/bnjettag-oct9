"""Replace missing log-derived metrics with authenticated W&B summaries."""
from pathlib import Path
import datetime
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]/'publication-status-20260920'
DOC=ROOT/'docs/current-work'
def read(p): return json.loads(p.read_text())
def write(p,x): p.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n')
raw=read(HERE/'BNJetTag-Batch20260917.json')
stamp=raw['fetched_at_utc']
runs={r['id']:r for r in raw['runs']}
def utc(t): return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
b=read(DOC/'batch20260918-status.json')
b.update(wandb_snapshot_at_utc=stamp,wandb_registered_runs_at_snapshot=15,
 metrics_refreshed_at_utc=stamp,metrics_source='authenticated_wandb_graphql',
 metrics_note='All 15 final screening summaries recovered. Latest-epoch internal validation metrics; not independently recomputed from predictions.',
 runs_with_final_epoch_metrics=15,metrics_recovery='The six unavailable container-log rows were recovered from durable W&B summaries.')
for row in b['runs']:
 run=runs[row['run_id']]; s=run['summary']; assert s['completed_epochs']==400
 row.update(latest_validation_accuracy=s['val_categorical_accuracy'],
 latest_validation_macro_ovr_auc=s['val_macro_auc'],latest_native_ebops=s['ebops'],
 latest_within_final_target=s['ebops']<=row['target_ebops'],source_updated_utc=utc(s['_timestamp']),
 metric_availability='wandb_summary_available',epoch_count_source='wandb_completed_epochs',
 runtime_seconds=s['_runtime'],runtime_basis='wandb_reported_session_seconds',
 metric_source='authenticated_wandb_graphql')
write(DOC/'batch20260918-status.json',b)
a=read(DOC/'live-status.json')
a.update(refreshed_at_utc=stamp,refresh_source='authenticated_wandb_graphql')
a['cluster_verification_note']='The September 20 cluster check confirmed completed 100-epoch screens. W&B was refreshed afterward; per-run source timestamps retain the actual metric times.'
for row in a['runs']:
 s=runs[row['run_id']]['summary']; assert s['completed_epochs']==100
 assert row['latest_validation_accuracy']==s['val_categorical_accuracy']
 assert row['latest_native_ebops']==s['ebops']
write(DOC/'live-status.json',a)
snapshot={'description':'Allowlisted authenticated W&B summaries for previously public campaigns; internal validation only.',
 'fetched_at_utc':stamp,'project_url':b['project_url'],'runs':raw['runs']}
write(DOC/'wandb-snapshot-20260920.json',snapshot)
abraw=read(HERE/'BNJetTag-EBOPs-N8.json')
ab=read(ROOT/'results/post_conference/ablation-training-status-20260920.json')
ab['wandb_refreshed_at_utc']=abraw['fetched_at_utc']
for row in ab['runs']:
 run=next(r for r in abraw['runs'] if f"ablation-r{row['index']}-" in r['name'])
 s=run['summary']; assert s['epochs_run']==1000
 row['wandb_final_epoch_metrics']={'run_id':run['id'],'run_name':run['name'],'completed_epochs':1000,
 'native_ebops':s['ebops'],'validation_macro_ovr_auc':s['val_macro_auc'],'source_updated_utc':utc(s['_timestamp']),
 'selection_note':'Final epoch, not necessarily best feasible checkpoint; held-out evaluation unchanged.'}
write(ROOT/'results/post_conference/ablation-training-status-20260920.json',ab)
status=read(DOC/'training-status-20260920.json')
status['wandb_refreshed_at_utc']=stamp
status['limitations']=[x for x in status['limitations'] if 'W&B summaries were not refreshed' not in x]
status['metrics_recovery']='All 27 architecture/attention summaries and all seven original ablation summaries recovered from authenticated W&B; older unavailable log evidence remains archived.'
write(DOC/'training-status-20260920.json',status)

p=DOC/'TRAINING_PROGRESS_20260920.md'; text=p.read_text()
start=text.index('All 15 jobs completed'); end=text.index('## Architecture screen',start)
lines=['All 15 jobs completed the 400-epoch screen. **All 15 final-epoch summaries are now available**, fetched from authenticated W&B at **'+stamp+'**. This supersedes the earlier nine-of-fifteen container-log coverage. These are internal-validation measurements on 124,000 jets; they have not been recomputed from saved predictions.','',
 '| Run | Epochs | Latest val accuracy | Latest val AUC | Latest EBOPs / 350k |',
 '|---|---:|---:|---:|---:|']
for r in b['runs']:
 lines.append(f"| [{r['arm'].upper()} / seed {r['seed']}]({r['run_url']}) | 400 / 1,000 | {100*r['latest_validation_accuracy']:.4f}% | {r['latest_validation_macro_ovr_auc']:.6f} | {r['latest_native_ebops']:,} / 350,000 |")
lines.extend(['', '**All 15 latest checkpoints exceed the 350,000-EBOP target**, at 465,506–723,763 EBOPs. Their validation accuracies span 27.6992%–42.0290%. The nine retained final-epoch logs each report the cost-controller coefficient at its configured maximum, beta=0.001; that coefficient was not recovered for the remaining six summaries. These final checkpoints have not achieved the intended accuracy/resource tradeoff. Earlier feasible-checkpoint records require separate verification; no winner is declared.', '',
 'The [complete W&B source snapshot](wandb-snapshot-20260920.json) preserves exact metrics and source timestamps. The earlier [nine final-epoch log lines](training-log-metrics-20260920.json) remain as corroborating evidence. The [protocol](BATCH20260918_ATTENTION_STUDY.md) describes the matched arms and final-budget selection rule.', '',
 'The user authorized continuation of every current architecture and attention run to the configured 1,000 epochs on September 20, superseding selective promotion for these campaigns. Continuation execution is recorded separately when verified.', '',''])
text=text[:start]+'\n'.join(lines)+text[end:]
text=text.replace('The existing September 18 W&B metrics remain the latest verified numerical snapshot.','A fresh W&B read on September 20 confirmed the existing September 18 numerical values and source timestamps.')
text=text.replace('An anonymous W&B query did not expose the projects, and authenticated W&B summaries were not refreshed for this snapshot. Existing W&B source timestamps are preserved.','Authenticated W&B summaries were refreshed after the initial log-only report. All missing attention metrics are recovered, and original per-run source timestamps are preserved.')
p.write_text(text)
p=DOC/'README.md'; text=p.read_text()
text=text.replace('Final-epoch logs are available for 9 of 15 attention runs: all nine exceed 350k EBOPs, with 31.5903%–41.3782% validation accuracy and beta=0.001. The other six metric rows remain unavailable. Review checkpoint histories and budget-controller behavior before promotion; no selected winner is established. The architecture table below retains its September 18 W&B metric timestamp.',
 'All 15 attention summaries have been recovered from W&B: every latest checkpoint exceeds 350k EBOPs, with 27.6992%–42.0290% validation accuracy. No selected winner is established. The architecture numerical values were rechecked and retain their original September 18 source timestamps. The user has authorized all current runs to continue to 1,000 epochs; execution is recorded after checkpoint-resume verification.')
p.write_text(text)
p=ROOT/'README.md'; text=p.read_text().replace('The nine recoverable final-epoch attention logs all remain over budget; continuation requires checkpoint-history and controller review.','All 15 attention summaries have been recovered from W&B and all latest checkpoints remain over budget. Full-length continuation of every current run has now been authorized.')
p.write_text(text)

# Private pilot report: augmented cost must not be mislabeled native HGQ2 EBOPs.
eng=read(HERE/'BNJetTag-Engram-Experimental.json')
rows=sorted(eng['runs'],key=lambda r:r['name'])
out=['# Engram pilot at 100 epochs','',f"Verified from W&B at {eng['fetched_at_utc']}. Private local report; initialization seed 1, 124,000 internal-validation jets. Latest epoch results; no held-out test or synthesized hardware results.",'',
 '| Arm | Design | Validation accuracy | Macro AUC | Native backbone EBOPs | Estimated memory bitops | Combined proxy |',
 '|---|---|---:|---:|---:|---:|---:|']
names=['Two-block reference','One-block baseline','One block + ungated memory','One block + gated memory']
for i,r in enumerate(rows):
 s=r['summary']; out.append(f"| E{i:02d} | {names[i]} | {100*s['val_categorical_accuracy']:.4f}% | {s['val_macro_auc']:.6f} | {s['cost/native_hgq2_backbone_ebops']:,.0f} | {s['cost/custom_estimated_bitops']:,.0f} | {s['ebops']:,} |")
out.extend(['','None met the 350,000 combined-cost target. E02 has the highest observed accuracy at this prefix; the gated design has not shown an advantage. This one-seed pilot does not establish reproducible superiority. E02/E03 passed selected-checkpoint reload validation; E00/E01 report finalization failed on a strict numerical comparison, after durable epoch-100 training checkpoints had been saved.', '',
 'For E02/E03 the reported total is native HGQ2 backbone EBOPs plus a custom memory-operation estimate; it is not a measured native-only cost or FPGA resource count. Logical tables are 16 KiB (E02) and 32 KiB (E03).', '',
 'E03 gate diagnostics on the fixed 256-example training probe: mean 0.5421, standard deviation 0.0669, 69.04% exactly 0.5, no recorded saturation or query clipping. Thus the gate is active but often unchanged at its midpoint. The effective value tables are 97.76% nonzero in E02 and 98.42% in E03. These probe observations do not establish a causal gating benefit.', '',
 'All four arms are authorized to resume the original 1,000-epoch schedule. Preserve source/config/data/optimizer identity and original training arithmetic.'])
(HERE/'ENGRAM_PILOT_RESULTS.md').write_text('\n'.join(out)+'\n')
private=read(HERE/'engram-status.json')
for r in private['runs']:
 m=r['latest_epoch_metrics']
 m['augmented_cost']=m.pop('native_ebops')
 m['cost_convention']='native_hgq2_plus_custom_memory_estimate'
write(HERE/'engram-status.json',private)
print('Recovered all15 attention metrics and all7 ablation final summaries; wrote private Engram report.')
