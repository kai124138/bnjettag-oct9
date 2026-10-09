# Dunnett-type max-t: paired against the same-seed replica (STUDY) vs unpaired against the mean of
# the 8 replica seeds (rep-A / rep-C seeds 1-8 exist by [DK2]). rho = seed coupling between a cell
# and the replica at the same seed. Pooled sd over cells (+ replica for the unpaired version).
import numpy as np
rng=np.random.default_rng(3); ALPHA=0.10
def sim(m,n,nr,rho,sigma,eff,reps):
    a=rng.normal(size=(reps,1,nr))*np.sqrt(max(rho,0))*sigma
    rep=a[:,0,:]+rng.normal(size=(reps,nr))*np.sqrt(1-max(rho,0))*sigma
    if rho<0:  # negative coupling: cell = -|rho| * replica component + independent
        rep=rng.normal(size=(reps,nr))*sigma
        c=(rho*rep[:,None,:n]+rng.normal(size=(reps,m,n))*np.sqrt(1-rho**2)*sigma)
    else:
        c=a[:,:,:n]+rng.normal(size=(reps,m,n))*np.sqrt(1-rho)*sigma
    c=c+eff[None,:,None]
    g=c-rep[:,None,:n]
    r=g-g.mean(2,keepdims=True); s=np.sqrt((r**2).sum((1,2))/(m*(n-1)))
    tp=g.mean(2)/(s[:,None]/np.sqrt(n))
    # unpaired: pooled within-group sd of runs (cells and all nr replica seeds)
    rc=c-c.mean(2,keepdims=True); rr=rep-rep.mean(1,keepdims=True)
    su=np.sqrt(((rc**2).sum((1,2))+(rr**2).sum(1))/(m*(n-1)+nr-1))
    tu=(c.mean(2)-rep.mean(1)[:,None])/(su[:,None]*np.sqrt(1/n+1/nr))
    return tp,tu
m,n,nr=12,4,8
for m in (12,40):
  tp0,tu0=sim(m,n,nr,0.0,1.0,np.zeros(m),40000)
  cp,cu=np.quantile(tp0.max(1),0.9),np.quantile(tu0.max(1),0.9)
  print(f"m={m}: crit paired {cp:.2f} unpaired-8 {cu:.2f}")
  for rho in (-0.5,0.0,0.3,0.7):
    for sig in (0.6,1.0):
      eff=np.zeros(m); eff[0]=1.0
      tp,tu=sim(m,n,nr,rho,sig,eff,20000)
      tp0,tu0=sim(m,n,nr,rho,sig,np.zeros(m),20000)
      print(f"  rho {rho:+.1f} sigma {sig}: power paired {(tp[:,0]>cp).mean():.2f} unpaired {(tu[:,0]>cu).mean():.2f} | FWER paired {(tp0.max(1)>cp).mean():.3f} unpaired {(tu0.max(1)>cu).mean():.3f}")
