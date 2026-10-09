# constructive v5: mode rule on the whole family matrix at the n = 4 readout; design arithmetic, not a result
import numpy as np
rng = np.random.default_rng(5092028); JUMP, WSD = 5.4, 0.3
def flag(x):
    xs = np.sort(x); gaps = np.diff(xs); i = np.argmax(gaps); lo, hi = xs[:i+1], xs[i+1:]
    if len(lo) < 2 or len(hi) < 2: return False
    ps = np.sqrt(((lo-lo.mean())**2).sum() + ((hi-hi.mean())**2).sum()) / np.sqrt(len(x)-2)
    return gaps[i] > 3*ps
for fam, m in (("5M", 37), ("350k", 11)):
    for q in (0.02, 0.05, 0.1):
        f = []
        for _ in range(4000):
            eff = np.zeros(m); eff[:3 if m == 37 else 1] = 1.0
            rep = -JUMP*(rng.random(8) < q) + rng.normal(size=8)*WSD
            cel = -JUMP*(rng.random((m + 1, 4)) < q) + rng.normal(size=(m + 1, 4))*WSD   # m cells + placebo
            cel[:m] += eff[:, None]
            f.append(flag(np.concatenate([rep, cel.ravel()])))
        print(f"{fam} per-run q {q}: pooled-matrix flag {np.mean(f):.3f}")
    f = [flag(rng.normal(size=8 + 4*(m + 1))) for _ in range(4000)]
    print(f"{fam} Gaussian pooled false flag {np.mean(f):.3f}")
