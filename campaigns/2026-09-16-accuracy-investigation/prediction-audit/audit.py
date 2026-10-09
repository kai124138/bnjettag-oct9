"""Read-only audit of archived five-class predictions; NumPy only, no training.

Accuracy intervals are Wilson binomial intervals conditional on a fixed model.
Paired delta intervals use the empirical variance of per-event correctness differences.
Seed summaries report sample SD, not independent event replication across seeds.
"""
import argparse
import hashlib
import itertools
import json
import time
from pathlib import Path
import numpy as np

CLASSES = ['g', 'q', 'W', 'Z', 't']

def auc(y, s):
    """Mann–Whitney AUC with average ranks for tied scores."""
    idx = np.argsort(s, kind='stable')
    ss = s[idx]
    starts = np.r_[0, np.flatnonzero(ss[1:] != ss[:-1]) + 1]
    ends = np.r_[starts[1:], len(s)]
    ranks = np.repeat((starts + ends + 1) / 2, ends - starts)
    npos = int(np.sum(y))
    return float((ranks[y[idx].astype(bool)].sum() - npos * (npos + 1) / 2) / (npos * (len(y) - npos)))

def wilson(p, n):
    z = 1.959963984540054
    center = (p + z*z/(2*n))/(1+z*z/n)
    half = z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return [float(center-half), float(center+half)]

def paired(a, b):
    d = a.astype(float)-b.astype(float)
    mean = float(d.mean())
    half = float(1.959963984540054*d.std(ddof=1)/np.sqrt(len(d)))
    return dict(delta=mean, ci95=[mean-half,mean+half], gains=int(np.sum(d>0)), losses=int(np.sum(d<0)), n=len(d))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--predictions', type=Path, default=Path('research/bnjettag/roc-results/r14'))
    ap.add_argument('--output', type=Path, default=Path(__file__).parent/'results.json')
    args=ap.parse_args()
    start=time.monotonic()
    rows=[]; correct={}; common_y=None
    for n in (8,16,32,64):
        for precision in ('FP32','W8A8','W1A8','W1A6','W1A4'):
            for seed in (1,2,3):
                p=args.predictions/f'n{n}'/f'{precision}-s{seed}.npz'
                with np.load(p,allow_pickle=False) as f:
                    y=f['y']; s=f['score']; meta=json.loads(str(f['meta']))
                assert y.shape==s.shape==(260000,5)
                assert np.isfinite(s).all() and np.isin(y,[0,1]).all() and np.all(y.sum(1)==1)
                label=y.argmax(1); pred=s.argmax(1); ok=label==pred
                if common_y is None: common_y=y.copy()
                same_labels=bool(np.array_equal(common_y,y))
                assert same_labels, 'Pairing requires identical labels and archived event order'
                key=f'n{n}-{precision}-s{seed}'; correct[key]=ok
                confusion=np.bincount(5*label+pred,minlength=25).reshape(5,5)
                perauc=[auc(y[:,k],s[:,k]) for k in range(5)]
                macro=float(np.mean(perauc)); assert abs(macro-meta['auc'])<1e-12
                best=max(itertools.permutations(range(5)),key=lambda v:sum(confusion[i,v[i]] for i in range(5)))
                top2=np.argpartition(s,-2,axis=1)[:,-2:]
                probs=np.clip(s,1e-15,1); confidence=s.max(1)
                ece=0.
                for low in np.arange(0,1,0.05):
                    sel=(confidence>=low)&(confidence<low+0.05 if low<0.95 else confidence<=1)
                    if sel.any(): ece+=sel.mean()*abs(ok[sel].mean()-confidence[sel].mean())
                pair=[]
                for i,j in itertools.combinations(range(5),2):
                    mask=(label==i)|(label==j)
                    pair.append(dict(classes=[CLASSES[i],CLASSES[j]], conditional_auc=auc(label[mask]==i,s[mask,i]-s[mask,j]), mutual_confusions=int(confusion[i,j]+confusion[j,i])))
                row=dict(configuration=key,n=n,precision=precision,seed=seed,path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),count=len(y),
                         accuracy=float(ok.mean()),accuracy_ci95=wilson(ok.mean(),len(ok)), macro_ovr_auc=macro, auc_metadata_delta=macro-meta['auc'],auc_per_class=dict(zip(CLASSES,perauc)),
                         top2_accuracy=float((top2==label[:,None]).any(1).mean()), binary_threshold_accuracy=float(((s>0.5)==y).mean()),
                         confusion_matrix_true_rows_pred_cols=confusion.tolist(),class_count=confusion.sum(1).tolist(),prediction_count=confusion.sum(0).tolist(),
                         recall=dict(zip(CLASSES,(confusion.diagonal()/confusion.sum(1)).tolist())),pairwise=pair,
                         best_column_permutation=list(best),best_permuted_accuracy=float(sum(confusion[i,best[i]] for i in range(5))/len(y)),
                         score_min=float(s.min()),score_max=float(s.max()),max_row_sum_error=float(abs(s.sum(1)-1).max()),
                         max_score_tie_rate=float(((s==s.max(1)[:,None]).sum(1)>1).mean()),same_label_order_all_archives=same_labels,
                         negative_log_likelihood=float(-np.log(probs[np.arange(len(y)),label]).mean()),ece_20_bins=float(ece),
                         error_rate_margin_under_01=float(((np.sort(s,axis=1)[:,-1]-np.sort(s,axis=1)[:,-2]<.1)&~ok).sum()/max((~ok).sum(),1)))
                rows.append(row)
                print(key, 'accuracy',round(row['accuracy'],6),'auc',round(macro,6),flush=True)
    summaries=[]
    for n in (8,16,32,64):
        for precision in ('FP32','W8A8','W1A8','W1A6','W1A4'):
            subset=[r for r in rows if r['n']==n and r['precision']==precision]
            summaries.append(dict(n=n,precision=precision,**{k:dict(mean=float(np.mean([r[k] for r in subset])),seed_sd=float(np.std([r[k] for r in subset],ddof=1))) for k in ['accuracy','macro_ovr_auc','top2_accuracy']}))
    comparisons=[]
    for n in (8,16,32,64):
        for seed in (1,2,3):
            for precision in ('FP32','W8A8','W1A6','W1A4'):
                a=f'n{n}-{precision}-s{seed}';b=f'n{n}-W1A8-s{seed}'
                comparisons.append(dict(a=a,b=b,**paired(correct[a],correct[b])))
    for n in (16,32,64):
        for seed in (1,2,3):
            a=f'n{n}-W1A8-s{seed}';b=f'n8-W1A8-s{seed}'
            comparisons.append(dict(a=a,b=b,**paired(correct[a],correct[b])))
    groups={}
    for comparison in comparisons:
        group=(comparison['a'].rsplit('-s',1)[0],comparison['b'].rsplit('-s',1)[0])
        groups.setdefault(group,[]).append(comparison['delta'])
    seed_comparisons=[]
    for (a,b),ds in groups.items():
        mean=float(np.mean(ds))
        # t(2) interval over three paired training seeds; does not triple event count.
        half=float(4.302652729911275*np.std(ds,ddof=1)/np.sqrt(len(ds)))
        seed_comparisons.append(dict(a=a,b=b,delta_mean=mean,seed_paired_t_ci95=[mean-half,mean+half],n_seeds=len(ds)))
    result=dict(classes=CLASSES,scope='Round 14 l1x3, cluster archived ROC-test predictions, held-out Zenodo validation archive',
                caveat='Paired comparisons assume saved arrays preserve identical event order; all label arrays verified identical. Conditional event CIs exclude training and dataset-selection uncertainty.',
                runtime_seconds=time.monotonic()-start,numpy_version=np.__version__,rows=rows,seed_summaries=summaries,paired_accuracy_comparisons=comparisons,seed_paired_accuracy_comparisons=seed_comparisons)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print('Wrote',args.output,'elapsed',result['runtime_seconds'],flush=True)

if __name__=='__main__': main()
