import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
rid='8dzauzyp'
a=root/rid/'artifact'
b=json.loads((a/'ebops_budget.json').read_text())
m=json.loads((a/'train_meta.json').read_text())
h=json.loads((root/rid/'history.json').read_text())
v=json.loads((root/'checkpoint_verification.json').read_text())[rid]
summary={
 'run_url':f'https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-EBOPs-N8/runs/{rid}',
 'initial_ebops':b['initial_ebops'],'target_ebops':b['target_ebops'],
 'verified_checkpoint_ebops':v['measured_ebops'],
 'reduction_from_initial_pct':100*(1-v['measured_ebops']/b['initial_ebops']),
 'reduction_from_control_pct':100*(1-v['measured_ebops']/1780910),
 'under_budget_pct':100*(1-v['measured_ebops']/b['target_ebops']),
 'validation_auc_quoted':m['best_val_macro_auc'],
 'epochs_run':m['epochs_run'],'train_seconds':m['train_seconds'],
 'width_histogram_verified':v['width_histogram'],
 'auc_status':'Single-seed N8/L1x3 validation on 124000 jets; quoted from artifact/train_meta.json, not independently recomputed from predictions.',
 'hardware_status':'No MAC reduction or LUT/synthesis result claimed.'}
(root/'analysis.json').write_text(json.dumps(summary,indent=2)+'\n')
report=f'''# N8 EBOPs-priority retry: target met

Run [{rid}]({summary['run_url']}) finished with a committed model artifact.
The saved `model_best.keras` measures **{v['measured_ebops']:,} EBOPs**, below the
**{b['target_ebops']:,.0f}** ceiling by **{summary['under_budget_pct']:.2f}%**.
That is **{summary['reduction_from_initial_pct']:.2f}% below initialization** and
**{summary['reduction_from_control_pct']:.2f}% below the earlier control checkpoint**.
Training stopped after **{m['epochs_run']} epochs**, {m['train_seconds']/60:.2f} minutes
of training (the cluster Job includes additional setup/download time).

| Saved checkpoint | EBOPs | Recorded validation macro-OvR AUC |
|---|---:|---:|
| Earlier control | 1,780,910 | 0.87166 |
| Earlier 75% budget | 1,263,790 | 0.87005 |
| New EBOPs-priority 50% retry | 847,982 | 0.79728 |

All are single-seed N8/L1x3 runs. AUCs are **quoted from the corresponding model
artifact's `train_meta.json`**, not recomputed from predictions here. New source:
[train_meta.json]({rid}/artifact/train_meta.json); earlier sources:
[control](../../ebops-n8-20260910/analysis/ed3piak8/artifact/train_meta.json) and
[75%](../../ebops-n8-20260910/analysis/3bynw2ra/artifact/train_meta.json).
These use the 124,000-jet internal validation split, not the held-out ROC-test split.
No seed uncertainty or statistical significance is established.

## What changed during training

- Epochs 1–2: 1,739,182 EBOPs, average activation width 8 bits.
- Epochs 3–7: 1,276,686 EBOPs, average width about 6.05 bits.
- Epoch 8: 847,982 EBOPs, average width about 4.14 bits; target passed, automatic stop.
- All 21 learnable sites changed: 19 ended at 4 bits, one at 5, one at 6.
  The two explicitly fixed attention probability input sites remain fixed.
- Beta started at 1e-4, briefly reached about 1.0718e-4, then stayed at its 1e-4 floor.
  It never approached the configured 1e-2 maximum. The much stronger initial
  pressure plus constant 1e-4 learning rate was sufficient for this target.
- The preceding epoch recorded validation AUC 0.85162 at 1,276,686 EBOPs; the last
  width reduction coincided with the drop to 0.79728. This does not prove that
  0.79728 is the best achievable AUC at the final widths: there was no recovery
  training after crossing the budget. Beta, LR, schedule, and checkpoint selection
  all changed, so this is not an isolated measurement of beta's effect.

## Verification and interpretation

Reloaded the committed checkpoint in a fresh process; zero-input and random-input
HGQ2 cost measurements both equal **847,982**, and every activation-width record
matches the artifact. All **15 binary layers** retain exactly two nonzero,
symmetric effective weight values. See [verification](checkpoint_verification.json).
The source hash matches the launched immutable code snapshot; `jit_compile=false`
and the budget-based stopping rule are recorded in the artifact metadata.

This run demonstrates sub-million EBOPs within the existing architecture, with
lower recorded validation AUC. It stopped at the requested budget; it does not
establish the lowest achievable EBOPs. EBOPs remain a hardware-cost proxy; no new
MAC count reduction or synthesized LUT result is established. A possible next
experiment is to freeze these widths and fine-tune weights while checking that
EBOPs remains under the cap; accuracy recovery is a hypothesis, not a guarantee.
No additional training jobs were launched during this analysis.

![Training history](costfirst_history.png)
'''
(root/'report.md').write_text(report)
epochs=[int(r['epoch'])+1 for r in h]
fig,axs=plt.subplots(2,1,figsize=(8,6),sharex=True,layout='constrained')
axs[0].step(epochs,[r['ebops']/1e6 for r in h],where='post',color='#126782',linewidth=2)
axs[0].scatter(epochs,[r['ebops']/1e6 for r in h],color='#126782',s=25)
axs[0].axhline(b['target_ebops']/1e6,color='#ad2831',linestyle='--',label='Target: 869,591')
axs[0].set_ylabel('EBOPs (millions)');axs[0].legend(loc='upper right',frameon=False)
axs[0].set_title('N=8: EBOPs-priority retry reached its budget at epoch 8',loc='left')
axs[1].plot(epochs,[r['val_macro_auc'] for r in h],marker='o',color='#694f98',linewidth=2)
axs[1].set_ylim(.77,.89);axs[1].set_ylabel('Recorded validation AUC');axs[1].set_xlabel('Epoch')
for ax in axs:
 ax.grid(alpha=.2);ax.spines[['top','right']].set_visible(False);ax.set_xticks(epochs)
fig.savefig(root/'costfirst_history.png',dpi=180)
print(json.dumps(summary,indent=2))
