# Max-t with each cell's own paired sd (df n-1), critical value simulated under the shared-replica
# null; compare calibration under heteroscedasticity and power against the pooled version.
import numpy as np
rng=np.random.default_rng(11); ALPHA=0.10
def draw(m,n,reps,cell_sd,eff=None,sigma=1.0):
    rep=rng.normal(size=(reps,n))*sigma
    c=rng.normal(size=(reps,m,n))*cell_sd[None,:,None]*sigma
    if eff is not None: c=c+eff[None,:,None]
    return c-rep[:,None,:]
def t_own(g): n=g.shape[2]; return g.mean(2)/(g.std(2,ddof=1)/np.sqrt(n))
def t_pool(g):
    n=g.shape[2]; r=g-g.mean(2,keepdims=True); s=np.sqrt((r**2).sum((1,2))/(g.shape[1]*(n-1)))
    return g.mean(2)/(s[:,None]/np.sqrt(n))
for m in (12,40):
  n=4
  g0=draw(m,n,40000,np.ones(m))
  cp=np.quantile(t_pool(g0).max(1),0.9); co=np.quantile(t_own(g0).max(1),0.9)
  print(f"m={m}: crit pooled {cp:.2f}, crit own-sd {co:.2f}")
  for lab,cs in [("homog",np.ones(m)),("25% x3",np.r_[np.full(m//4,3.0),np.ones(m-m//4)])]:
    g=draw(m,n,20000,cs)
    print(f"   null {lab}: FWER pooled {(t_pool(g).max(1)>cp).mean():.3f} own {(t_own(g).max(1)>co).mean():.3f}")
  for sig in (0.6,1.5):
    eff=np.zeros(m); eff[0]=1.0
    g=draw(m,n,20000,np.ones(m),eff=eff,sigma=sig)
    print(f"   one +1pt cell, sigma {sig}: P(true cell above) pooled {(t_pool(g)[:,0]>cp).mean():.3f} own {(t_own(g)[:,0]>co).mean():.3f}")
