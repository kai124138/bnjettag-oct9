"""Independent sklearn verification of fresh CPU-export prediction metrics."""
import json
from pathlib import Path
import numpy as np
from scipy.special import softmax
from sklearn.metrics import roc_auc_score, confusion_matrix
from calibrate_outputs import auc, paired_ci
from check_deployment_stability import apply, constants

root = Path('local/accuracy-investigation/remote-results')
report = json.loads((root/'calibration_report.json').read_text())
manifest = json.loads((root/'manifest.json').read_text())
deploy = json.loads((root/'deployment_stability_report.json').read_text())
saved = {r['arm']: r for r in manifest['runs']}
with np.load(root/'labels.npz') as d:
    labels = {k:d[k].argmax(1) for k in ('validation','test')}
checks = []
for run in report['runs']:
    with np.load(root/(run['arm']+'.npz')) as d:
        for split in ('validation','test'):
            z = d[split+'_logits'].astype(np.float64)
            p = softmax(z, axis=1)
            y = labels[split]
            calculated = np.asarray(auc(y,p))
            sklearn = roc_auc_score(np.eye(5)[y],p,average=None)
            np.testing.assert_allclose(calculated,sklearn,rtol=0,atol=1e-12)
            recorded = run['baseline_'+split]['macro_auc']
            np.testing.assert_allclose(sklearn.mean(),recorded,rtol=0,atol=1e-12)
            check = {'arm':run['arm'],'split':split,'sklearn_per_class_auc':sklearn.tolist(),
                     'sklearn_macro_auc':float(sklearn.mean()),'max_rankdata_vs_sklearn_delta':float(abs(calculated-sklearn).max()),
                     'recorded_fresh_cpu_auc':recorded}
            if split == 'validation':
                training = saved[run['arm']]['selected']['val_macro_auc']
                check['recorded_training_validation_auc'] = training
                check['fresh_cpu_minus_recorded_training_auc'] = float(sklearn.mean()-training)
            checks.append(check)

run = next(r for r in report['runs'] if r['arm']=='r2-ffn32')
deployment = next(r for r in deploy['runs'] if r['arm']=='r2-ffn32')
with np.load(root/'r2-ffn32.npz') as d:
    r2 = d['test_logits'].astype(np.float64)
with np.load(root/'r1-channel.npz') as d:
    r1 = d['test_logits'].astype(np.float64)
y = labels['test']
corrected = r2*run['scale']+run['bias']
rounded = apply(r2,*constants(run['scale'],run['bias'],deployment['chosen_representation']))
classes = ['g','q','W','Z','t']
cms = {name:confusion_matrix(y,z.argmax(1),labels=range(5)) for name,z in
       [('r2_uncorrected',r2),('r2_corrected_float64',corrected),('r2_corrected_deployment',rounded)]}
confusions = {}
for name,cm in cms.items():
    confusions[name] = {'accuracy':float(cm.trace()/cm.sum()),'confusion_true_rows_pred_cols':cm.tolist(),
                       'recall':dict(zip(classes,(cm.diagonal()/cm.sum(1)).tolist())),
                       'predicted_counts':cm.sum(0).tolist(),
                       'mutual_confusions':{'g_q':int(cm[0,1]+cm[1,0]),'W_Z':int(cm[2,3]+cm[3,2])}}
recall_comparisons=[]
for k,name in enumerate(classes):
    mask=y==k
    recall_comparisons.append({'class':name,'float64_vs_uncorrected':paired_ci(y[mask],r2[mask],corrected[mask]),
                              'deployment_vs_uncorrected':paired_ci(y[mask],r2[mask],rounded[mask])})
result={'scope':'Fresh CPU-export logits: sklearn independently reproduces rankdata metrics. Historical GPU training-validation AUC is a separate recorded measurement, not asserted equal to CPU re-evaluation.',
        'checks':checks,'r2_float64_corrected_vs_r1_uncorrected':paired_ci(y,r1,corrected),
        'r2_deployment_corrected_vs_r1_uncorrected':paired_ci(y,r1,rounded),
        'r2_confusions':confusions,'r2_recall_paired_changes':recall_comparisons}
(root/'independent_prediction_verification.json').write_text(json.dumps(result,indent=2)+'\n')
print('All 14 fresh archive/split AUC checks passed.')
print('R2 float64 vs R1 baseline',result['r2_float64_corrected_vs_r1_uncorrected'])
print('R2 deploy vs R1 baseline',result['r2_deployment_corrected_vs_r1_uncorrected'])
print('Confusions',json.dumps(confusions))
