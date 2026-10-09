import numpy as np
rng=np.random.default_rng(1)
def run(m,n,crit,frac_wide,wide,pl_scale,reps=20000):
    k=int(round(frac_wide*m))
    sc=np.ones(m); sc[:k]=wide
    # gap per cell: (cell noise * sc) - replica; replica shared
    rep=rng.normal(size=(reps,n))
    c=rng.normal(size=(reps,m,n))*sc[None,:,None]
    g=c-rep[:,None,:]
    pla=rng.normal(size=(reps,n))*pl_scale  # placebo gap independent of replica if deterministic-ish
    gp=pla
    res=np.concatenate([g-g.mean(2,keepdims=True),(gp-gp.mean(1,keepdims=True))[:,None,:]],1)
    s=np.sqrt((res**2).sum((1,2))/(res.shape[1]*(n-1)))
    t=g.mean(2)/(s[:,None]/np.sqrt(n)); tp=gp.mean(1)/(s/np.sqrt(n))
    return (t.max(1)>crit).mean(), (t[:,:k].max(1)>crit).mean() if k else 0, (np.abs(tp)>crit).mean()
for m,crit in ((12,2.41),(40,2.793)):
    for fw,w in ((0,1),(0.1,2),(0.2,2),(0.1,3)):
        print(m,fw,w,"FWER, wide-cell hit, placebo flag:",run(m,4,crit,fw,w,np.sqrt(2)))
    print(m,"placebo near-deterministic (gap sd 0.1 of sqrt2):",run(m,4,crit,0,1,0.14))
