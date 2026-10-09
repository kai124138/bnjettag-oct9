# constructive v5: mode flag on the 12 lever-free values (8 replica + 4 placebo), and on the cell matrix
# centred per cell by its median (lever effects removed without reading order); design arithmetic, not a result
import numpy as np
rng = np.random.default_rng(5092029); JUMP, WSD = 5.4, 0.3
def flag(x):
    xs = np.sort(x); gaps = np.diff(xs); i = np.argmax(gaps); lo, hi = xs[:i+1], xs[i+1:]
    if len(lo) < 2 or len(hi) < 2: return False
    ps = np.sqrt(((lo-lo.mean())**2).sum() + ((hi-hi.mean())**2).sum()) / np.sqrt(len(x)-2)
    return gaps[i] > 3*ps
for fam, m in (("5M", 35), ("350k", 11)):
    for q in (0.0, 0.02, 0.05, 0.1, 0.33):
        f12, fc = [], []
        for _ in range(4000):
            low = lambda sh: rng.random(sh) < q
            rep = -JUMP*low(8) + rng.normal(size=8)*WSD
            pla = -JUMP*low(4) + rng.normal(size=4)*WSD
            eff = rng.normal(size=m)*1.5            # spread of lever effects, sd 1.5 pt (illustration)
            cel = -JUMP*low((m, 4)) + rng.normal(size=(m, 4))*WSD + eff[:, None]
            f12.append(flag(np.concatenate([rep, pla])))
            cen = cel - np.median(cel, 1, keepdims=True)
            fc.append(flag(np.concatenate([rep - np.median(rep), pla - np.median(pla), cen.ravel()])))
        print(f"{fam} q {q}: flag on replica+placebo (12) {np.mean(f12):.3f}; on median-centred matrix {np.mean(fc):.3f}")
