import os,sys,json
from pathlib import Path
os.environ.setdefault('KERAS_BACKEND','tensorflow')
os.environ.setdefault('CUDA_VISIBLE_DEVICES','-1')
sys.path.insert(0,'/Users/kaiyamaguchi/Downloads/bnjettag-training-results/bnjettag/code/hgq2')
import keras,numpy as np
from bnhgq2.compat import apply_keras_compat
from bnhgq2 import qat
from bnhgq2.ebops_calc import compute_ebops
from bnhgq2.ebops_target import width_snapshot
apply_keras_compat()
root=Path('/tmp/bnjettag-ebops-analysis')
records={}
for rid in ['ed3piak8','3bynw2ra','zyj0gwkq']:
    d=root/rid/'artifact'
    b=json.loads((d/'ebops_budget.json').read_text())
    m=keras.models.load_model(d/b['checkpoint'],compile=False)
    zero=np.zeros((8,8,3),dtype='float32')
    rnd=np.random.default_rng(101).normal(size=(8,8,3)).astype('float32')
    c=compute_ebops(m,zero)
    c2=compute_ebops(m,rnd)
    assert c==c2 and c['total']==b['checkpoint_ebops']
    widths=width_snapshot(m)
    assert widths==b['checkpoint_widths']
    binary=qat.effective_weight_values(m)
    assert len(binary)==15 and all(len(v)==2 and not (v==0).any() and np.isclose(v[0],-v[1]) for v in binary.values())
    free=[v['bits'] for v in widths.values() if v['width_trainable']]
    records[rid]={'checkpoint':b['checkpoint'],'measured_ebops':c['total'],'per_layer':c['per_layer'],'binary_layers':len(binary),'mean_learnable_activation_bits':float(np.mean(free)),'width_histogram':{str(int(n)):free.count(n) for n in sorted(set(free))},'sample_independent_check':True}
    print(rid,records[rid],flush=True)
(root/'checkpoint_verification.json').write_text(json.dumps(records,indent=2)+'\n')
