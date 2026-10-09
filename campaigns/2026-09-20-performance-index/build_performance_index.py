"""Reproducible, private analysis of matched screening snapshots (31 runs)."""
from pathlib import Path
import hashlib
import json
import os

HERE = Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR', str(HERE / '.mplconfig'))
os.environ.setdefault('XDG_CACHE_HOME', str(HERE / '.cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, NullFormatter
import numpy as np
from scipy.optimize import brentq

BASE = HERE.parents[1]
SOURCE = BASE / 'local/status-20260920'
CONFIG = BASE / 'publication-status-20260920/code/hgq2/configs'
CHANCE = .20
DESCRIPTIONS = {
 'A00':'Channel, FFN64; reference', 'A01':'Tensor, FFN64', 'A02':'Channel, FFN32',
 'A03':'Tensor, FFN32', 'A04':'N16, FFN32', 'A05':'N32, FFN32',
 'A06':'N16, narrower D16', 'A07':'N16, one block', 'A08':'N16, two heads',
 'A09':'N16, 500k target', 'A10':'N16, 250k target', 'A11':'N8, FFN32, 500k target',
 'B00':'Reference', 'B01':'One attention head', 'B02':'No positional table',
 'B03':'8-bit attention probabilities', 'B04':'Gradual budget schedule',
 'E00':'Two-block baseline', 'E01':'One-block baseline',
 'E02':'One block + ungated memory', 'E03':'One block + gated memory'}
FAMILIES = [
 {'name':'Architecture','prefix':'batch20260917','epochs':100,'reference':'A00','seeds':[1],
  'color':'#237A8A','cost_label':'Native HGQ2 EBOPs (thousands)'},
 {'name':'Attention','prefix':'batch20260918','epochs':400,'reference':'B00','seeds':[4,5,6],
  'color':'#B45B29','cost_label':'Native HGQ2 EBOPs (thousands)'},
 {'name':'Engram','prefix':'engram','epochs':100,'reference':'E01','seeds':[1],
  'color':'#7956A4','cost_label':'Backbone EBOPs + estimated memory bitops (thousands)'}]

def read(path): return json.loads(path.read_text())
def save_json(path, data): path.write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')
raw = []
sources = []
for filename in ['BNJetTag-Batch20260917.json','BNJetTag-Engram-Experimental.json']:
 path=SOURCE/filename; data=read(path); raw.extend(data['runs'])
 sources.append({'file':filename,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                 'fetched_at_utc':data['fetched_at_utc']})

def efficiency(rows, power=1):
 return np.array([(r['accuracy']-CHANCE)/(r['cost']/1000)**power for r in rows])

def score(family, arm, power=1):
 return 100*efficiency(family['arms'][arm]['runs'],power).mean()/efficiency(
     family['arms'][family['reference']]['runs'],power).mean()

for family in FAMILIES:
 arms={}
 for run in raw:
  if not run['name'].startswith(family['prefix']+'-'): continue
  s=run['summary']; assert s['completed_epochs']==family['epochs']
  arm=run['name'].split('-')[1].upper(); seed=int(run['name'].rsplit('-s',1)[1])
  cfg=read(CONFIG/family['prefix']/(run['name']+'.json')) if family['name']!='Engram' else read(
      BASE/'publication/code/hgq2/configs/engram'/(run['name']+'.json'))
  r={'name':run['name'],'seed':seed,'completed_epochs':s['completed_epochs'],
     'accuracy':s['val_categorical_accuracy'],'cost':s['ebops'],
     'target':cfg['train']['ebops']['pid']['target_ebops'],
     'auc':s['val_macro_auc'],'source_metric_unix_timestamp':s['_timestamp']}
  assert r['accuracy']>CHANCE and r['cost']>0
  arms.setdefault(arm,{'label':DESCRIPTIONS[arm],'runs':[]})['runs'].append(r)
 family['arms']=dict(sorted(arms.items()))
 for arm,a in family['arms'].items():
  a['runs'].sort(key=lambda r:r['seed']);assert [r['seed'] for r in a['runs']]==family['seeds']
  a['accuracy_mean']=float(np.mean([r['accuracy'] for r in a['runs']]))
  a['cost_mean']=float(np.mean([r['cost'] for r in a['runs']]))
  a['accuracy_seed_sd']=float(np.std([r['accuracy'] for r in a['runs']],ddof=1)) if len(a['runs'])>1 else None
  a['cost_seed_sd']=float(np.std([r['cost'] for r in a['runs']],ddof=1)) if len(a['runs'])>1 else None
  a['index']=float(score(family,arm))
  a['seed_indices']=(100*efficiency(a['runs'])/efficiency(arms[family['reference']]['runs']).mean()).tolist()
  a['index_seed_sd']=float(np.std(a['seed_indices'],ddof=1)) if len(a['runs'])>1 else None
  a['all_latest_checkpoints_feasible']=all(r['cost']<=r['target'] for r in a['runs'])
 for arm,a in family['arms'].items():
  a['dominated_by']=[k for k,b in family['arms'].items() if k!=arm
      and b['accuracy_mean']>=a['accuracy_mean'] and b['cost_mean']<=a['cost_mean']
      and (b['accuracy_mean']>a['accuracy_mean'] or b['cost_mean']<a['cost_mean'])]
  a['pareto_frontier']=not a['dominated_by']
 family['ranking']=sorted(family['arms'],key=lambda k:family['arms'][k]['index'],reverse=True)
 for rank,arm in enumerate(family['ranking'],1):family['arms'][arm]['rank']=rank

assert sum(len(a['runs']) for f in FAMILIES for a in f['arms'].values())==31
assert all(abs(score(f,f['reference'])-100)<1e-10 for f in FAMILIES)
assert all(not a['all_latest_checkpoints_feasible'] for f in FAMILIES for a in f['arms'].values())
# Monotonicity: a point dominated in both raw means must not outrank its dominator
# in single-seed studies; three-seed efficiency aggregates retain individual costs.
for f in FAMILIES:
 if len(f['seeds'])==1:
  for a in f['arms'].values():assert all(a['index']<=f['arms'][k]['index'] for k in a['dominated_by'])

arch_pairs=[('A00','A01','Tensor instead of channel, FFN64'),
 ('A00','A02','FFN64 → FFN32, channel'),('A01','A03','FFN64 → FFN32, tensor'),
 ('A02','A03','Tensor instead of channel, FFN32'),('A02','A04','8 → 16 constituents'),
 ('A04','A05','16 → 32 constituents'),('A04','A06','Embedding32 → 16'),
 ('A04','A07','Two → one transformer block'),('A04','A08','Four → two heads'),
 ('A04','A09','350k → 500k target, N16'),('A04','A10','350k → 250k target, N16'),
 ('A02','A11','350k → 500k target, N8')]
interventions=[]
for f in FAMILIES:
 pairs=arch_pairs if f['name']=='Architecture' else (
   [('B00',k,DESCRIPTIONS[k]) for k in ('B01','B02','B03','B04')] if f['name']=='Attention' else
   [('E00','E01','Two → one transformer block'),('E01','E02','Add ungated memory'),('E02','E03','Add gated memory package')])
 for control,variant,label in pairs:
  aa=f['arms'][variant];bb=f['arms'][control]
  ratios=efficiency(aa['runs'])/efficiency(bb['runs'])
  interventions.append({'family':f['name'],'control':control,'variant':variant,'change':label,
   'local_control_index_100':float(100*efficiency(aa['runs']).mean()/efficiency(bb['runs']).mean()),
   'paired_seed_efficiency_ratios':ratios.tolist(),
   'uncertainty_scope':'Single training seed; no seed-uncertainty estimate.' if len(ratios)==1 else
       'Three matched seeds; ratios describe observed seed variation, not a confidence interval.'})

grid=np.linspace(0,1.5,301)
sensitivity={f['name']:{arm:[float(score(f,arm,x)) for x in grid] for arm in f['arms']} for f in FAMILIES}
attn=FAMILIES[1]
cross=brentq(lambda x:score(attn,'B01',x)-score(attn,'B02',x),0,1)
data={'name':'Accuracy–Cost Index','formula':'100 * mean_seed[(accuracy - 0.20) / (cost / 1000)^lambda] / mean_seed[(control_accuracy - 0.20) / (control_cost / 1000)^lambda]',
 'default_lambda':1,'uniform_random_guess_accuracy':CHANCE,'sources':sources,'families':FAMILIES,
 'controlled_interventions':interventions,'attention_b01_b02_crossover_lambda':float(cross),
 'sensitivity_lambda':grid.tolist(),'sensitivity_scores':sensitivity,
 'notes':['Descriptive index, not a validated scientific metric or a hardware estimate.',
          'All comparisons use matched frozen screening epochs, not ongoing resumed runs.',
          'Index100 is local to each study; normalized scores must not be ranked across studies.',
          'All31 latest checkpoints exceed their own configured budget; index rank does not imply deployability.',
          'Engram total combines native backbone EBOPs and custom memory bitops; memory storage is separate.',
          'Attention aggregates per-seed efficiencies before normalization; not efficiency of averaged accuracy/cost.',
          'Current three studies only. Final matched accuracy unavailable for original seven1000-epoch ablations; their mixed-maturity September15 evaluation is excluded.']}
save_json(HERE/'performance_index.json',data)

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.titlesize':12,
 'axes.titleweight':'bold','axes.labelcolor':'#263347','text.color':'#182638',
 'axes.edgecolor':'#C8D0D8','xtick.color':'#465568','ytick.color':'#465568',
 'axes.spines.top':False,'axes.spines.right':False,'figure.facecolor':'#F7F9FC',
 'axes.facecolor':'white','svg.hashsalt':'bnjet-accuracy-cost-index-20260920'})

def save(fig,name):
 for ext in ('png','svg'):
  fig.savefig(HERE/(name+'.'+ext),dpi=190,bbox_inches='tight',
              metadata={'Date':None} if ext=='svg' else {})
 plt.close(fig)

fig=plt.figure(figsize=(16,16.5))
gs=fig.add_gridspec(3,2,height_ratios=[1.48,1,1],hspace=.48,wspace=.42,
                   left=.075,right=.97,bottom=.09,top=.86)
fig.text(.075,.973,'Accuracy versus computational cost',fontsize=25,weight='bold')
fig.text(.075,.942,'31 runs  ·  Three studies  ·  Matched screening snapshots from 20 September 2026',fontsize=12,color='#526278')
fig.text(.075,.910,'Accuracy–Cost Index = 100 × (accuracy above 20% chance per cost) ÷ control efficiency',fontsize=13)
fig.text(.075,.885,'Higher index means more accuracy above chance per unit of cost. Controls: A00, B00, E01 = 100.',fontsize=11,color='#526278')
offsets={'A00':(8,14),'A01':(-30,-14),'A02':(-30,-19),'A03':(-29,9),'A04':(10,9),
 'A05':(-32,7),'A06':(11,-10),'A07':(8,-13),'A08':(-29,4),'A09':(8,6),
 'A10':(3,-18),'A11':(9,5),'B00':(8,-14),'B01':(9,9),'B02':(10,7),
 'B03':(-34,6),'B04':(13,-10),'E00':(10,-8),'E01':(9,-12),'E02':(9,9),'E03':(10,6)}
for i,f in enumerate(FAMILIES):
 ax=fig.add_subplot(gs[i,0]);bar=fig.add_subplot(gs[i,1]);color=f['color']
 ax.set_title(f"{'ABC'[i]}  {f['name']}  ·  {f['epochs']} epochs  ·  {len(f['seeds'])} seed"+('s' if len(f['seeds'])>1 else ''),loc='left',pad=14)
 ax.axvline(350,color='#CF4E55',lw=1.25,ls='--',alpha=.8)
 ax.text(350,.97,'350k guide',transform=ax.get_xaxis_transform(),ha='right',va='top',fontsize=8,color='#AC4045',rotation=90)
 frontier=sorted([a for a in f['arms'].values() if a['pareto_frontier']],key=lambda a:a['cost_mean'])
 if len(frontier)>1:ax.plot([a['cost_mean']/1000 for a in frontier],[100*a['accuracy_mean'] for a in frontier],color=color,lw=1.4,ls=':',zorder=1)
 for arm,a in f['arms'].items():
  x=a['cost_mean']/1000;y=100*a['accuracy_mean'];highlight=a['pareto_frontier']
  c=color if highlight else '#8794A5'
  if len(a['runs'])>1:
   ax.errorbar(x,y,xerr=a['cost_seed_sd']/1000,yerr=100*a['accuracy_seed_sd'],fmt='none',ecolor=c,alpha=.5,capsize=3,lw=1,zorder=1)
   ax.scatter([r['cost']/1000 for r in a['runs']],[r['accuracy']*100 for r in a['runs']],s=16,color=c,alpha=.3,zorder=2)
  ax.scatter(x,y,s=105 if arm==f['reference'] else 75,marker='s' if arm==f['reference'] else 'o',
             facecolors=c if highlight else 'white',edgecolors=c,linewidth=1.6,zorder=3)
  suffix='*' if any(r['target']!=350000 for r in a['runs']) else ''
  ax.annotate(arm+suffix,(x,y),xytext=offsets[arm],textcoords='offset points',fontsize=10,weight='bold',color=c)
 ax.set_xlabel(f['cost_label'],fontsize=9,labelpad=9);ax.set_ylabel('Validation accuracy (%)')
 ax.grid(alpha=.18);ax.set_axisbelow(True)
 if i==0:
  ax.set_xscale('log');ax.set_xlim(310,2900);ax.set_ylim(33,65)
  ax.set_xticks([350,500,750,1000,2000]);ax.xaxis.set_major_formatter(ScalarFormatter())
  ax.xaxis.set_minor_formatter(NullFormatter())
 elif i==1:ax.set_xlim(320,805);ax.set_ylim(23,49)
 else:ax.set_xlim(320,930);ax.set_ylim(46,65)
 bar.set_title(f"Index ranking  ·  {f['reference']} = 100",loc='left',pad=14)
 order=f['ranking'];yy=np.arange(len(order));values=[f['arms'][k]['index'] for k in order]
 maximum=max(values+[v for a in f['arms'].values() for v in a['seed_indices']])
 colors=[color if f['arms'][k]['pareto_frontier'] else '#CBD3DE' for k in order]
 bar.barh(yy,values,height=.65,color=colors,zorder=2)
 for j,k in enumerate(order):
  a=f['arms'][k]
  if len(a['runs'])>1:
   bar.scatter(a['seed_indices'],[j]*len(a['runs']),s=28,facecolor='white',edgecolor='#24374B',linewidth=.9,zorder=4)
  bar.text(maximum*1.15,j,f'{values[j]:.1f}',va='center',ha='right',fontsize=10,weight='bold')
 bar.set_yticks(yy,[f'{k}  {DESCRIPTIONS[k]}' for k in order],fontsize=9)
 bar.invert_yaxis();bar.axvline(100,ls='--',lw=1,color='#738196',zorder=1)
 bar.set_xlim(0,maximum*1.18);bar.set_xlabel('Accuracy–Cost Index (higher is better)',fontsize=9)
 bar.grid(axis='x',alpha=.17);bar.set_axisbelow(True);bar.spines['left'].set_visible(False)
 bar.tick_params(axis='y',length=0)
fig.text(.075,.047,'Colored points/bars: observed Pareto frontier (no alternative has both higher accuracy and lower cost). Squares: controls.',fontsize=10)
fig.text(.075,.030,'Attention: means ± sample SD on the left; individual seed indices on the right. Single-seed studies have no seed-uncertainty estimate.',fontsize=10)
fig.text(.075,.013,'All31 checkpoints are over their own budgets. * Architecture targets: A09/A11 = 500k; A10 = 250k. Engram cost includes a custom estimate.'.replace('All31','All 31'),fontsize=10,color='#A14148')
save(fig,'accuracy_cost_overview')

fig,axs=plt.subplots(1,3,figsize=(16,5.5))
fig.subplots_adjust(left=.07,right=.97,bottom=.20,top=.72,wspace=.3)
fig.text(.07,.94,'Does the ranking survive a different cost preference?',fontsize=21,weight='bold')
fig.text(.07,.865,'Index(λ) uses (accuracy − 20%) / cost^λ.   λ = 0: accuracy only   ·   λ = 0.5: softer cost penalty   ·   λ = 1: default efficiency',fontsize=11)
for ax,f in zip(axs,FAMILIES):
 keep={'A00','A01','A02','A03','A11'} if f['name']=='Architecture' else set(f['arms'])
 palette=plt.get_cmap('tab10');n=0
 for arm,a in f['arms'].items():
  yy=sensitivity[f['name']][arm]
  if arm in keep:
   ax.plot(grid,yy,color=palette(n),lw=2,label=arm);n+=1
  else:ax.plot(grid,yy,color='#BFC7D2',lw=.8,alpha=.6)
 ax.axvline(1,color='#36445B',ls='--',lw=1);ax.axhline(100,color='#CBD1DA',lw=.8)
 ax.set_title(f"{f['name']} · control {f['reference']}",loc='left',fontsize=12)
 ax.set_xlabel('Cost weight λ');ax.grid(alpha=.15);ax.legend(ncol=3,fontsize=8,frameon=False,loc='upper left')
 ax.set_xlim(0,1.5);ax.set_ylim(0,max(max(y) for y in sensitivity[f['name']].values())*1.20)
axs[0].set_ylabel('Relative index')
fig.text(.07,.055,f'Engram E02 leads throughout this range. Attention switches from B02 to B01 at λ ≈ {cross:.2f}; there is no preference-free scalar winner.',fontsize=11)
save(fig,'index_sensitivity')

lines=['# Accuracy–cost ranking of the current training changes','',
 'This report compares all31 active continuation runs at their completed screening stops: architecture at100 epochs (seed1), attention at400 epochs (seeds4–6), and Engram at100 epochs (seed1). Ongoing resumed epochs are deliberately not mixed into these comparisons. This combined report includes private Engram results and is kept local.','',
 '## The index','',
 '**Accuracy–Cost Index (ACI)** = `100 × mean[(accuracy − 0.20) / cost] / mean[(control accuracy − 0.20) / control cost]`.', '',
 'Accuracy is a fraction. Twenty percent is the expected accuracy of uniform random guessing across five classes; it is not a measured majority-class baseline. Subtracting it avoids rewarding a random classifier solely for being cheap. This is a proposed descriptive utility, not an established metric. ACI120 means20% more accuracy above chance per unit of cost than that study’s control, not20 percentage points more accuracy.', '',
 'Single-seed studies use their one observation. For attention, compute each seed’s efficiency, average those efficiencies, then normalize by the reference’s mean efficiency. Do not substitute a ratio of mean accuracy and mean cost. Controls are A00, B00 and E01; cross-study normalized index values are not comparable.', '',
 'For a general cost preference use `cost^λ`: λ0 ranks accuracy alone; λ1 is the default efficiency metric. The [sensitivity figure](index_sensitivity.png) shows how the choice changes rankings. Cost is native HGQ2 EBOPs for architecture/attention and native backbone EBOPs plus custom estimated memory bitops for Engram. Logical memory storage is not included in ACI.', '',
 '![Accuracy–cost overview](accuracy_cost_overview.png)','',
 '## Variant rankings','']
for f in FAMILIES:
 lines.extend([f"### {f['name']} — {f['epochs']} epochs; control {f['reference']} = 100",'',
 '| Rank | Variant | Validation accuracy | Cost | ACI | Observed Pareto frontier |',
 '|---:|---|---:|---:|---:|---|'])
 for arm in f['ranking']:
  a=f['arms'][arm];acc=f"{a['accuracy_mean']*100:.2f}%";cost=f"{a['cost_mean']:,.0f}"
  if len(a['runs'])>1:acc+=f" ± {a['accuracy_seed_sd']*100:.2f} pp"
  lines.append(f"| {a['rank']} | {arm}: {a['label']} | {acc} | {cost} | **{a['index']:.1f}** | {'Yes' if a['pareto_frontier'] else 'No'} |")
 lines.extend(['','Three-seed accuracy spreads are sample standard deviations, not confidence intervals.' if len(f['seeds'])>1 else 'Single initialization seed: no estimate of training-seed variation.',''])
lines.extend(['## Ranking individual changes against the appropriate control','',
 'These contrasts use the closest intended control, rather than attributing a compound architecture difference to one change. Each local control is100. Ratios describe this training prefix and background architecture; they do not establish a general causal benefit. A03 versus A00 combines two changes, so its individual effects appear against A01 and A02 instead.',''])
for f in FAMILIES:
 lines.extend([f"### {f['name']} changes",'', '| Change | Control → variant | Local ACI |','|---|---|---:|'])
 for r in sorted([r for r in interventions if r['family']==f['name']],key=lambda r:r['local_control_index_100'],reverse=True):
  lines.append(f"| {r['change']} | {r['control']} → {r['variant']} | {r['local_control_index_100']:.1f} |")
 lines.append('')
lines.extend(['## Interpretation','',
 '- **Architecture:** A03 (tensor quantization, FFN32) leads efficiency; A11 retains the highest latest accuracy. A03, A02, A00 and A11 form the observed frontier. The biggest local efficiency change among the tested N16 architecture contrasts is reducing two blocks to one (A04 → A07). Different architecture rows have different cost targets, so the combined ranking is a realized-cost comparison, not a matched-budget causal claim.',
 '- **Attention:** B01 (one head) leads default efficiency. B02 (no positional table) has the highest mean accuracy. Both are on the frontier of arm means. Seed variation is large; these are descriptive rankings, not established superiority.',
 '- **Engram:** E02 (ungated memory) has both the highest accuracy and the lowest combined cost of these four arms at epoch100. It therefore leads both Pareto and index comparisons. The gated package adds storage and estimated operations without improving this snapshot’s accuracy.',
 f'- **Preference sensitivity:** attention B02 leads when cost weight λ is below about{cross:.2f}; B01 leads above it. E02 leads for every λ from0 to1.5. The index weight is a choice, not a discovered physical constant.',
 '- **Hard-budget result:** none of the31 latest checkpoints is feasible under its own configured target. Durable screening states also record no feasible checkpoint. If350k is mandatory, the current deployment ranking is “no eligible candidate,” regardless of ACI.', '',
 '## Uncertainty and scope','',
 'Pareto labels use point estimates (arm means for attention), not confidence-aware dominance. Architecture/Engram have one seed. Attention has three matched seeds; the figure shows sample SD and individual seed indices, not formal significance. This index should be recomputed at matching later training prefixes and for final feasible checkpoints before selection.', '',
 'The Engram E02/E03 predictions were independently verified on124,000 validation jets. The E02-minus-E03 accuracy difference was+0.845 percentage points, with a paired bootstrap95% interval+0.628 to+1.061 points. This is validation-sample uncertainty conditional on the chosen checkpoints, not training-seed variation or an independent test-set result. No equivalent paired interval is claimed for the other contrasts.', '',
 'The seven original EBOP ablations have completed1,000 training epochs, but a matched final categorical-accuracy evaluation is not available in these sources. Their older September15 records mix interim and completed selected checkpoints and are not ranked alongside the current studies. No held-out test or FPGA advantage is inferred from these validation/cost scores.', '',
 '## Reproduction','',
 '`python build_performance_index.py` regenerates JSON, report and PNG/SVG figures from the frozen local summaries. Requires NumPy, SciPy and Matplotlib. `performance_index.json` retains source-file hashes, per-run metrics, local-control contrasts and the full cost-weight sensitivity grid.',''])
text='\n'.join(lines)
for old,new in [('all31','all 31'),('at100','at 100'),('seed1','seed 1'),('at400','at 400'),('seeds4','seeds 4'),('ACI120','ACI 120'),('means20','means 20'),('not20','not 20'),('λ0','λ = 0'),('λ1','λ = 1'),('is100','is 100'),('FFN32','FFN32'),('epoch100','epoch 100'),('about0','about 0'),('from0 to1.5','from 0 to 1.5'),('the31','the 31'),('If350k','If 350k'),('on124,000','on 124,000'),('was+0.845','was +0.845'),('bootstrap95%','bootstrap 95%'),('interval+0.628 to+1.061','interval +0.628 to +1.061'),('completed1,000','completed 1,000'),('September15','September 15')]:text=text.replace(old,new)
(HERE/'REPORT.md').write_text(text+'\n')
print('Built31-run report, two PNG/SVG figures and reproducible index JSON.')
for f in FAMILIES:print(f['name'],[(k,round(f['arms'][k]['index'],1)) for k in f['ranking']])
print('Attention cost-weight crossover',cross)
