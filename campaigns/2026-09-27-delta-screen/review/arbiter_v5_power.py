# Arbiter v5: effect for 50 % / 80 % power of one named cell, own-sd t on d = cell - placebo, n 4, section-13 critical values. Design arithmetic, not a result.
import numpy as np
rng=np.random.default_rng(20260927)
def pw(eff,sig,crit,reps=40000,n=4):
    d = (rng.normal(size=(reps,n))+eff/sig - rng.normal(size=(reps,n)))  # cell - placebo, sd sqrt2 in sigma units
    t = d.mean(1)/(d.std(1,ddof=1)/np.sqrt(n))
    return (t>crit).mean()
for crit,lab in ((4.284,'m11'),(6.585,'m37')):
    for sig in (0.6,1.5,3.14):
        out=[]
        for eff in np.arange(0.5,16,0.05):
            p=pw(eff,sig,crit)
            out.append((eff,p))
        e50=min(e for e,p in out if p>=0.5); e80=min(e for e,p in out if p>=0.8)
        print(lab,sig,round(e50,2),round(e80,2))
