# Calibration of the STUDY's Dunnett-type max-t (screen_null.py tstats) when cells differ in
# gap variance (coupling to the replica differs by lever). Design arithmetic only.
import numpy as np
rng=np.random.default_rng(7)
ALPHA=0.10
def tstats(g,gp,include_placebo=True):
    n=g.shape[2]
    parts=[g-g.mean(2,keepdims=True)]
    if include_placebo: parts.append((gp-gp.mean(1,keepdims=True))[:,None,:])
    res=np.concatenate(parts,1)
    s=np.sqrt((res**2).sum((1,2))/(res.shape[1]*(n-1)))
    return g.mean(2)/(s[:,None]/np.sqrt(n)), gp.mean(1)/(s/np.sqrt(n))
def draw(m,n,reps,cell_sd,pla_sd):
    # gap = cell-specific independent part (sd cell_sd_i) minus shared replica part (sd 1)
    rep=rng.normal(size=(reps,n))
    c=rng.normal(size=(reps,m,n))*cell_sd[None,:,None]
    pla=rng.normal(size=(reps,n))*pla_sd
    return c-rep[:,None,:], pla-rep
def crit(m,n,reps=40000):
    g,gp=draw(m,n,reps,np.ones(m),1.0); t,_=tstats(g,gp); return np.quantile(t.max(1),1-ALPHA)
for m in (12,40):
    n=4; c=crit(m,n)
    print(f"m={m} n={n} homogeneous crit {c:.3f}")
    for label,cs,ps in [("homogeneous",np.ones(m),1.0),
                        ("placebo coupled (sd 0.2)",np.ones(m),0.2),
                        ("25% cells sd x2",np.r_[np.full(m//4,2.0),np.ones(m-m//4)],1.0),
                        ("25% cells sd x3",np.r_[np.full(m//4,3.0),np.ones(m-m//4)],1.0),
                        ("1 cell sd x3",np.r_[3.0,np.ones(m-1)],1.0)]:
        g,gp=draw(m,n,20000,cs,ps); t,tp=tstats(g,gp)
        print(f"   {label:28s} P(false 'above replica') {(t.max(1)>c).mean():.3f}  placebo flag {(np.abs(tp)>c).mean():.4f}  placebo rank-top-quartile {( (g.mean(2)>gp.mean(1)[:,None]).sum(1) < (m+1)/4).mean():.3f}")
