from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
root=Path(__file__).resolve().parent
arms={'control':('ed3piak8','#64748b'),'75% budget':('3bynw2ra','#0d9488'),'25% budget':('zyj0gwkq','#d97706')}
verified=json.loads((root/'checkpoint_verification.json').read_text())
rows=[]
fig,axs=plt.subplots(2,2,figsize=(13,8.5),layout='constrained')
for label,(rid,color) in arms.items():
 d=root/rid
 h=json.loads((d/'history.json').read_text())
 m=json.loads((d/'artifact/train_meta.json').read_text())
 b=json.loads((d/'artifact/ebops_budget.json').read_text())
 epoch=np.array([r['epoch'] for r in h])+1
 cost=np.array([r['ebops'] for r in h])/b['initial_ebops']
 auc=np.array([r['val_macro_auc'] for r in h])
 axs[0,0].plot(epoch,100*cost,label=label,color=color,lw=2)
 axs[0,1].plot(epoch,auc,label=label,color=color,lw=1.5)
 axs[1,0].plot(epoch,[r['activation_bits_mean'] for r in h],color=color,lw=2,label=label)
 if label!='control':
  axs[1,1].semilogy(epoch,[r['beta'] for r in h],color=color,lw=2,label=f'{label}: beta')
 axs[0,1].scatter([m['best_epoch']+1],[m['best_val_macro_auc']],s=45,color=color,zorder=5)
 feasible=[r for r in h if b['target_ebops'] is not None and r['ebops']<=b['target_ebops']]
 rows.append({'arm':label,'run_id':rid,'run_url':f'https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-EBOPs-N8/runs/{rid}',
 'validation_auc_reported':m['best_val_macro_auc'],'checkpoint':b['checkpoint'],'checkpoint_epoch_1based':m['best_epoch']+1,
 'initial_ebops':b['initial_ebops'],'target_ebops':b['target_ebops'],'checkpoint_ebops_verified':verified[rid]['measured_ebops'],
 'checkpoint_reduction_vs_control_pct':100*(1-b['checkpoint_ebops']/verified['ed3piak8']['measured_ebops']),
 'budget_met':b['budget_met'],'first_feasible_epoch_1based':feasible[0]['epoch']+1 if feasible else None,
 'final_epoch_ebops_reported':h[-1]['ebops'],'final_epoch_validation_auc_reported':h[-1]['val_macro_auc'],
 'final_beta':h[-1].get('beta',0),'final_learning_rate':h[-1]['learning_rate'],
 'checkpoint_width_histogram':verified[rid]['width_histogram'],'checkpoint_mean_bits':verified[rid]['mean_learnable_activation_bits']})
axs[0,0].axhline(75,color='#0d9488',ls='--',lw=1)
axs[0,0].axhline(25,color='#d97706',ls='--',lw=1)
axs[0,0].set(title='Resource cost: 75% target reached; 25% target missed',ylabel='EBOPs (% of initial model)',ylim=(18,108))
axs[0,0].legend(frameon=False,fontsize=9)
axs[0,1].set(title='Validation AUC (single seed; dots mark saved models)',ylabel='Macro one-vs-rest AUC',ylim=(.73,.88))
axs[1,0].set(title='Widths actually learned during training',ylabel='Mean bits across 21 learnable activation sites',ylim=(4.7,8.5))
axs[1,1].set(title='Compression pressure rose while learning rate decayed',ylabel='EBOPs penalty coefficient beta')
lr_ax=axs[1,1].twinx()
lr_ax.semilogy(epoch,[r['learning_rate'] for r in h],color='#7c3aed',ls=':',lw=2,label='Learning rate')
lr_ax.set_ylabel('Learning rate',color='#7c3aed')
lines=axs[1,1].get_lines()+lr_ax.get_lines()
axs[1,1].legend(lines,[l.get_label() for l in lines],frameon=False,fontsize=8,loc='upper center')
for ax in axs.flat:
 ax.set_xlabel('Epoch (1-based)');ax.grid(alpha=.18);ax.spines[['top']].set_visible(False)
fig.suptitle('N=8 binary-weight EBOPs pilot · 101 epochs · seed 1\n50% arm failed at GPU compilation before its first completed epoch',fontsize=14)
fig.savefig(root/'pilot_results.png',dpi=170)
(root/'analysis.json').write_text(json.dumps({'rows':rows,'failed_arm':{'arm':'50% budget','run_id':'mkvzt7ur','reason':'XLA/Triton GEMM autotuning: NOT_FOUND: No valid config found','completed_epochs':0},'auc_status':'Quoted from train_meta.json; no independently recomputed ROC-test AUC','source':'Downloaded committed W&B model artifacts and complete scan_history; EBOPs remeasured from checkpoints'},indent=2)+'\n')
print(json.dumps(rows,indent=2))
