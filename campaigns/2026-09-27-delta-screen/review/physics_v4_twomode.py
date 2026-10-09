import numpy as np
rng=np.random.default_rng(1)
def run(q,shared,m=37,n=4,k=3,top=12,reps=8000,jump=5.4,sd=0.3,eff=1.0):
    hit=0
    for _ in range(reps):
        if shared:
            low=rng.random(n)<q
            rep=-jump*low+rng.normal(size=n)*sd
            cells=-jump*low[None,:]+rng.normal(size=(m,n))*sd
        else:
            rep=-jump*(rng.random(n)<q)+rng.normal(size=n)*sd
            cells=-jump*(rng.random((m,n))<q)+rng.normal(size=(m,n))*sd
        cells[:k]+=eff
        g=(cells-rep).mean(1)
        hit+=np.isin(np.arange(k),np.argsort(-g)[:top]).all()
    return hit/reps
for q in (0.1,0.33,0.5):
    sig=np.sqrt(q*(1-q))*5.4
    print(f"q {q} per-run sd {np.hypot(sig,0.3):.2f}: independent-mode recovery {run(q,False):.3f}; seed-shared mode {run(q,True):.3f}")
