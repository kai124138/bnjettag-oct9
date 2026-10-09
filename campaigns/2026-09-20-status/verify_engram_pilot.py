"""Recompute private E02/E03 pilot metrics and paired validation uncertainty."""
from pathlib import Path
import hashlib
import json
import numpy as np
from sklearn.metrics import roc_auc_score

ROOT=Path(__file__).resolve().parent/'engram-e100-archive'
rows=[]; correct=[]; reference=None
for arm in ('engram-e02-s1','engram-e03-s1'):
 path=ROOT/arm/'validation_predictions.npz'
 report=json.loads((ROOT/arm/'engram_result.json').read_text())
 with np.load(path,allow_pickle=False) as a:
  labels=a['labels']; logits=a['logits']
 assert labels.shape==logits.shape==(124000,5)
 assert np.isfinite(logits).all()
 if reference is None: reference=labels.copy()
 else: np.testing.assert_array_equal(reference,labels)
 hit=np.argmax(logits,axis=1)==np.argmax(labels,axis=1)
 acc=float(hit.mean())
 z=logits.astype(np.float64)
 exp=np.exp(z-z.max(axis=-1,keepdims=True))
 scores=exp/exp.sum(axis=-1,keepdims=True)
 per=[float(roc_auc_score(labels[:,i],scores[:,i])) for i in range(5)]
 auc=float(np.mean(per))
 assert abs(acc-report['validation_accuracy'])<1e-12
 assert abs(auc-report['validation_macro_auc'])<1e-12
 rows.append({'arm':arm,'validation_accuracy':acc,'macro_ovr_auc':auc,
  'per_class_auc':per,'augmented_cost':report['selection_cost'],'budget_met':report['budget_met'],
  'predictions_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
 correct.append(hit)
# Resampling the four joint correctness categories exactly reproduces a paired
# empirical bootstrap for accuracy differences, without materializing jet arrays.
codes=2*correct[0].astype(int)+correct[1].astype(int)
counts=np.bincount(codes,minlength=4)
rng=np.random.default_rng(20260920)
draws=rng.multinomial(len(codes),counts/len(codes),size=50000)
deltas=(draws[:,2]-draws[:,1])/len(codes)
result={'n_validation':len(codes),'initialization_seed':1,'completed_epochs':100,
 'runs':rows,'comparison':'E02 minus E03 categorical accuracy',
 'difference_percentage_points':100*(rows[0]['validation_accuracy']-rows[1]['validation_accuracy']),
 'paired_bootstrap_95_percent_interval_percentage_points':(100*np.quantile(deltas,[.025,.975])).tolist(),
 'joint_correctness_counts':counts.tolist(),'bootstrap_replicates':50000,'bootstrap_seed':20260920,
 'caveat':'Descriptive validation-sample uncertainty conditional on these selected single-seed checkpoints; not training-seed uncertainty or an independent test-set significance claim.'}
(ROOT/'verified-comparison.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
