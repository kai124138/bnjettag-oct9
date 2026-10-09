import numpy as np
from scipy import stats
rng=np.random.default_rng(20260927)
t80=stats.t.ppf(0.80,3); t975=stats.t.ppf(0.975,3)
print("t80(3)=%.4f t975(3)=%.4f half-width factor=%.4f"%(t80,t975,t975/2))
for m in (19,43):
    print("m=%d P(>=1 LCB80>0 | null, indep)=%.5f  Bin(m,.2) mean %.1f 95pct %d"%(m,1-0.8**m,0.2*m,stats.binom.ppf(0.95,m,0.2)))
    print("   expected false 'contradicted' (95%% two-sided lower tail) per family: %.2f"%(0.025*m))
MED=[]  # v6 (experiment-designer, 2026-09-28): median-g rank hits from the same draws, printed at the end
def sim(m,n,sigma,rho,eff,k_true,top,reps=20000,shared=True):
    # seed-level: each run acc = common seed effect (corr rho across arms at seed) + indep
    hits_lcb=hits_mean=hits_pool=hits_med=0; nfalse=[]
    for _ in range(reps):
        a=rng.normal(size=n)*np.sqrt(rho)*sigma           # shared seed component
        rep=a+rng.normal(size=n)*np.sqrt(1-rho)*sigma
        cells=a[None,:]+rng.normal(size=(m,n))*np.sqrt(1-rho)*sigma
        d=np.zeros(m); d[:k_true]=eff
        g=cells+d[:,None]-rep[None,:]
        mean=g.mean(1); sd=g.std(1,ddof=1)
        lcb=mean-t80*sd/np.sqrt(n)
        nfalse.append((lcb[k_true:]>0).sum())
        if k_true:
            hits_lcb+=np.isin(np.arange(k_true),np.argsort(-lcb)[:top]).all()
            hits_mean+=np.isin(np.arange(k_true),np.argsort(-mean)[:top]).all()
            hits_med+=np.isin(np.arange(k_true),np.argsort(-np.median(g,1))[:top]).all()
    if k_true: MED.append((m,sigma,rho,eff,hits_med/reps,hits_mean/reps,hits_lcb/reps))
    return hits_lcb/reps,hits_mean/reps,np.mean(nfalse),np.mean(np.array(nfalse)>0)
for sigma in (0.6,1.5,3.14):
  for rho in (0.0,0.5):
    for eff in (0.3,1.0,3.0):
      l,mn,nf,pf=sim(43,4,sigma,rho,eff,3,12,reps=4000)
      print("5M m43 n4 sigma %.2f rho %.1f 3 true @+%.1f: P(all 3 in top-12) LCB-rank %.2f mean-rank %.2f | null cells LCB>0 mean %.1f"%(sigma,rho,eff,l,mn,nf))
# null only
for m in (19,43):
    _,_,nf,pf=sim(m,4,1.0,0.0,0,0,12,reps=20000)
    print("global null m=%d shared replica: mean #LCB80>0 %.2f, P(>=1) %.4f"%(m,nf,pf))
# fixer v3 (2026-09-27, STUDY arbiter v3 fix 4): the ranked 5M list holds at most 37 cells once the
# long-horizon cells M015, M031, M032 leave it. Appended so the rows above keep their random stream.
from math import comb
print("m=37 (5M ranked list, H 500 only): chance C(12,3)/C(37,3) = %.4f" % (comb(12, 3) / comb(37, 3)))
for sigma in (0.6,1.5,3.14):
  for rho in (0.0,0.5):
    for eff in (1.0,3.0):
      l,mn,nf,pf=sim(37,4,sigma,rho,eff,3,12,reps=4000)
      print("5M m37 n4 sigma %.2f rho %.1f 3 true @+%.1f: P(all 3 in top-12) LCB-rank %.2f mean-rank %.2f"%(sigma,rho,eff,l,mn))
# v6 (experiment-designer, 2026-09-28; [DK6] re-decided: median g primary). Scored on the draws above (no new
# random numbers), so every line above reproduces digit for digit.
print("v6: P(all 3 true cells in top-12) by median-g rank / mean-g rank / LCB80 rank (same draws as the rows above):")
for m,sigma,rho,eff,md,mn,l in MED:
    print("   m%d sigma %.2f rho %.1f 3 true @+%.1f: median %.2f / mean %.2f / LCB80 %.2f"%(m,sigma,rho,eff,md,mn,l))
