# Dunnett-type pooled max-t (screen_null.py) under a two-mode seed outcome, as in the archived N=64
# W1A8 seeds 67.18 / 72.64 / 67.21 %: each run lands in the upper mode with prob q (+5.4 pt), plus
# Gaussian sd 0.3 pt. Critical value from the Gaussian null (as the STUDY does). Design arithmetic.
import numpy as np
rng=np.random.default_rng(5); ALPHA=0.10
def t_pool(g,gp):
    n=g.shape[2]; r=np.concatenate([g-g.mean(2,keepdims=True),(gp-gp.mean(1,keepdims=True))[:,None,:]],1)
    s=np.sqrt((r**2).sum((1,2))/(r.shape[1]*(n-1))); return g.mean(2)/(s[:,None]/np.sqrt(n)), gp.mean(1)/(s/np.sqrt(n))
def gauss(m,n,reps):
    rep=rng.normal(size=(reps,n)); c=rng.normal(size=(reps,m,n)); p=rng.normal(size=(reps,n))
    return c-rep[:,None,:], p-rep
def mix(m,n,reps,q,jump=5.4,sd=0.3,qcell=None):
    f=lambda shape,qq: (rng.random(shape)<qq)*jump+rng.normal(size=shape)*sd
    rep=f((reps,n),q); p=f((reps,n),q)
    qc=np.full(m,q) if qcell is None else qcell
    c=f((reps,m,n),qc[None,:,None])
    return c-rep[:,None,:], p-rep
for m in (12,40):
    n=4; g,gp=gauss(m,n,40000); t,_=t_pool(g,gp); crit=np.quantile(t.max(1),0.9)
    for q in (0.1,0.33,0.5):
        g,gp=mix(m,n,20000,q); t,tp=t_pool(g,gp)
        print(f"m={m} q={q}: null FWER {(t.max(1)>crit).mean():.3f}; placebo flag {(np.abs(tp)>crit).mean():.3f}")
    # a cell that only raises escape probability 0.33 -> 0.66 (mean +1.8 pt)
    qc=np.full(m,0.33); qc[0]=0.66
    g,gp=mix(m,n,20000,0.33,qcell=qc); t,_=t_pool(g,gp)
    print(f"m={m}: one cell with escape prob 0.66 vs 0.33 (+1.8 pt in mean): P(named above) {(t[:,0]>crit).mean():.3f}; P(rank 1) {(g.mean(2).argmax(1)==0).mean():.3f}")
