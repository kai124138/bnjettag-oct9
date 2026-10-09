"""Independent scikit-learn checks of audit metric implementations."""
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import roc_auc_score, accuracy_score
from audit import auc

checks=[]
for n,key in [(8,'W1A8'),(8,'FP32'),(64,'W1A4')]:
    with np.load(f'research/bnjettag/roc-results/r14/n{n}/{key}-s1.npz') as d:
        y=d['y']; score=d['score']
    custom=float(np.mean([auc(y[:,k],score[:,k]) for k in range(5)]))
    expected=roc_auc_score(y,score,average='macro',multi_class='ovr')
    assert abs(custom-expected)<1e-12
    checks.append({'n':n,'precision':key,'numpy_auc':custom,'sklearn_auc':expected,
                   'accuracy':accuracy_score(y.argmax(1),score.argmax(1))})
for y,scores in [(np.array([0,1,0,1]),np.array([0.,0.,1.,1.])),
                 (np.array([0,1]),np.array([.5,.5])),
                 (np.array([0,1]),np.array([1.,0.]))]:
    assert auc(y,scores)==roc_auc_score(y,scores)
(Path(__file__).parent/'verification.json').write_text(json.dumps(
    {'sklearn_checks':checks,'tie_edge_cases_passed':3},indent=2)+'\n')
print('3 archive comparisons and 3 tied-score edge cases passed.')
