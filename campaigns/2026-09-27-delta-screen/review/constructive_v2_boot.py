# Fix check: critical value for the pooled max-t simulated by resampling the 8 replica epoch-500
# values (read at the gate, before cells launch) instead of from a Gaussian. Truth = two-mode
# outcome. Outer loop over replica draws; FWER of the resulting procedure on fresh null families.
import numpy as np
rng=np.random.default_rng(9)
def t_pool(g,gp):
    n=g.shape[2]; r=np.concatenate([g-g.mean(2,keepdims=True),(gp-gp.mean(1,keepdims=True))[:,None,:]],1)
    s=np.sqrt((r**2).sum((1,2))/(r.shape[1]*(n-1)))
    with np.errstate(divide='ignore',invalid='ignore'):
        return g.mean(2)/(s[:,None]/np.sqrt(n))
f=lambda shape,q: (rng.random(shape)<q)*5.4+rng.normal(size=shape)*0.3
for m in (12,40):
  for q in (0.1,0.33):
    n=4; fw=[]; crits=[]
    for outer in range(150):
        rep8=f(8,q)
        B=4000
        pick=lambda shape: rep8[rng.integers(0,8,size=shape)]
        g=pick((B,m,n))-(r:=pick((B,n)))[:,None,:]; gp=pick((B,n))-r
        t=np.nan_to_num(t_pool(g,gp),nan=0.0,posinf=1e9)
        c=np.quantile(t.max(1),0.9); crits.append(c)
        rep=f((1000,n),q); gt=f((1000,m,n),q)-rep[:,None,:]; gpt=f((1000,n),q)-rep
        tt=np.nan_to_num(t_pool(gt,gpt),nan=0.0)
        fw.append((tt.max(1)>c).mean())
    print(f"m={m} q={q}: bootstrap-null FWER mean {np.mean(fw):.3f} (median crit {np.median(crits):.2f})")
