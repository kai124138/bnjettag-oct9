import numpy as np
rng=np.random.default_rng(7)
def run(m,sigma,rho,eff,k,reps=10000):
    one=two=0
    for _ in range(reps):
        d=np.zeros(m); d[:k]=eff
        a=rng.normal(size=8)*np.sqrt(rho)*sigma
        x=a[None,:]+d[:,None]+rng.normal(size=(m,8))*np.sqrt(1-rho)*sigma
        # one stage: 4 seeds each (172 runs)
        top=np.argsort(-x[:,:4].mean(1))[:12]; one+=np.isin(np.arange(k),top).all()
        # two stage: 2 seeds all (86), top 14 get seeds 3-8 (84) -> 170 runs
        s1=np.argsort(-x[:,:2].mean(1))[:14]
        score=np.full(m,-np.inf); score[s1]=x[s1,:8].mean(1)
        top2=np.argsort(-score)[:12]; two+=np.isin(np.arange(k),top2).all()
    return one/reps,two/reps
for sigma in (0.6,1.5,3.14):
    for eff in (1.0,3.0):
        o,t=run(43,sigma,0.0,eff,3)
        print("sigma %.2f eff +%.1f: one-stage n4 %.2f  two-stage (2 -> top14 x8) %.2f"%(sigma,eff,o,t))
