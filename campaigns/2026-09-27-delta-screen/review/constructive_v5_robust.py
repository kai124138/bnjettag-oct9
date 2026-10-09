# constructive v5: design arithmetic, seeded, not a result.
import numpy as np
rng = np.random.default_rng(5092027)
JUMP, WSD = 5.4, 0.3
def sim(m, k, top, q, reps=20000, gauss_sigma=None, T=None, shared=False):
    eff = np.zeros(m); eff[:k] = 1.0
    if gauss_sigma is None:
        lr = rng.random((reps, 4)) < q; lc = np.broadcast_to(lr[:,None,:],(reps,m,4)) if shared else rng.random((reps, m, 4)) < q
        r = -JUMP*lr + rng.normal(size=(reps,4))*WSD
        c = -JUMP*lc + rng.normal(size=(reps,m,4))*WSD + eff[None,:,None]
    else:
        r = rng.normal(size=(reps,4))*gauss_sigma
        c = rng.normal(size=(reps,m,4))*gauss_sigma + eff[None,:,None]
    res = c - c.mean(2,keepdims=True) - c.mean(1,keepdims=True) + c.mean((1,2),keepdims=True)
    s_int = np.sqrt((res**2).sum((1,2))/((m-1)*3))
    g = c - r[:,None,:]
    cen = c - np.median(c,1,keepdims=True)          # per-seed centring on the family median (no replica)
    hit = lambda score: np.all([(np.argsort(-score,1)[:,:top]==i).any(1) for i in range(k)],0)
    out = dict(mean=hit(g.mean(2)), median_g=hit(np.median(g,2)), median_cen=hit(np.median(cen,2)))
    sel = s_int <= T if T else np.ones(reps,bool)
    return {kk: (v.mean(), v[sel].mean() if sel.any() else np.nan, sel.sum()) for kk,v in out.items()}
for fam,m,k,top,T in (("5M",37,3,12,1.3),("350k",11,1,3,1.5)):
    print(fam)
    for gs in (0.6,1.0,1.3):
        o = sim(m,k,top,None,gauss_sigma=gs)
        print(f"  Gaussian sigma {gs}: " + "; ".join(f"{kk} {v[0]:.2f}" for kk,v in o.items()))
    for q in (0.02,0.05,0.1,0.2,0.33,0.5):
        o = sim(m,k,top,q,T=T)
        os_ = sim(m,k,top,q,shared=True)
        print(f"  seed-shared q {q}: " + "; ".join(f"{kk} {v[0]:.2f}" for kk,v in os_.items()))
        print(f"  per-run q {q}: " + "; ".join(f"{kk} {v[0]:.2f} (|s_int<=T {v[1]:.2f}, set {v[2]})" for kk,v in o.items()))
# mode readout detection on 8 replica values (rule as in STUDY Controls)
def flag(x):
    xs = np.sort(x); gaps = np.diff(xs); out=False
    i = np.argmax(gaps)
    lo, hi = xs[:i+1], xs[i+1:]
    if len(lo)<2 or len(hi)<2: return False
    ps = np.sqrt(((lo-lo.mean())**2).sum()+((hi-hi.mean())**2).sum())/np.sqrt(len(x)-2)
    return gaps[i] > 3*ps
print("mode readout P(two-mode flag), 8 replica values")
for q in (0.02,0.05,0.1,0.2,0.33,0.5):
    f = [flag(-JUMP*(rng.random(8)<q)+rng.normal(size=8)*WSD) for _ in range(20000)]
    print(f"  per-run q {q}: {np.mean(f):.3f}")
f = [flag(rng.normal(size=8)) for _ in range(20000)]
print(f"  Gaussian (any sigma): {np.mean(f):.3f}")
# Welch half-width, n = 4 per side, equal sd: t(0.975, 6) * sigma * sqrt(2/4)
from scipy import stats
for s in (0.6,1.5,3.14):
    print(f"Welch n4/n4 sigma {s}: half-width {stats.t.ppf(0.975,6)*s*np.sqrt(0.5):.2f} pt; paired rho0 sd_d={s*np.sqrt(2):.2f}: {stats.t.ppf(0.975,3)/2*s*np.sqrt(2):.2f}")
