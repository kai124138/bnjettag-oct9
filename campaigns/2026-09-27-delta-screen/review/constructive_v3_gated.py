"""constructive v3: moderated max-t (prior df d0 = 3) gated by a shape read on the 8 replica seeds at
the epoch-500 gate (flag two-mode if the largest gap between sorted replica values exceeds its
Gaussian null 95th percentile in sd_rep units); flagged -> the STUDY's own-sd rule. Placebo-referenced,
n = 4, alpha 0.10. Design arithmetic, seeded Monte Carlo, not a result."""
import numpy as np
rng = np.random.default_rng(20260928)

def gap_ratio(r):
    s = np.sort(r, 1); return np.diff(s, axis=1).max(1) / r.std(1, ddof=1)

G = np.quantile(gap_ratio(rng.normal(size=(200000, 8))), 0.95)
print(f"gate: largest sorted gap / sd_rep over 8 replica seeds, Gaussian null 95th pct {G:.3f}")

def draw(m, reps, cs=None, mix=None, eff=None, sigma=1.0):
    if mix is not None:
        q, jump, sd = mix
        f = lambda shape: (rng.random(shape) < q) * jump + rng.normal(size=shape) * sd
        r, p, c = f((reps, 8)), f((reps, 4)), f((reps, m, 4))
    else:
        r = rng.normal(size=(reps, 8)) * sigma; p = rng.normal(size=(reps, 4)) * sigma
        cs = np.ones(m) if cs is None else cs
        c = rng.normal(size=(reps, m, 4)) * cs[None, :, None] * sigma
    if eff is not None:
        c = c + eff[None, :, None]
    return r, p, c

def t_mod(d, d0):
    v = d.var(2, ddof=1)
    s2 = v if d0 == 0 else (d0 * v.mean(1, keepdims=True) + 3 * v) / (d0 + 3)
    return d.mean(2) / np.sqrt(s2 / 4)

for m in (12, 40):
    r, p, c = draw(m, 60000); d = c - p[:, None, :]
    c0 = np.quantile(t_mod(d, 0).max(1), 0.9); c3 = np.quantile(t_mod(d, 3).max(1), 0.9)
    def rule(r, p, c):
        d = c - p[:, None, :]; flag = gap_ratio(r) > G
        return np.where(flag[:, None], t_mod(d, 0) > c0, t_mod(d, 3) > c3), flag
    rows = [("equal", {}), ("25% 3x", dict(cs=np.r_[np.full(m // 4, 3.0), np.ones(m - m // 4)])),
            ("2-mode q.1", dict(mix=(0.1, 5.4, 0.3))), ("2-mode q.33", dict(mix=(0.33, 5.4, 0.3))),
            ("2-mode q.5", dict(mix=(0.5, 5.4, 0.3)))]
    out = []
    for lab, kw in rows:
        hit, flag = rule(*draw(m, 20000, **kw)); out.append(f"{lab} {hit.any(1).mean():.3f} (gate {flag.mean():.2f})")
    pw = []
    for sigma in (0.6, 1.0, 1.5):
        eff = np.zeros(m); eff[0] = 1.0
        hit, _ = rule(*draw(m, 20000, eff=eff, sigma=sigma)); pw.append(f"{hit[:, 0].mean():.3f}")
    print(f"m {m}: crit own {c0:.2f}, d0=3 {c3:.2f}; FWER: " + "; ".join(out) + " | power s0.6/1.0/1.5 " + " / ".join(pw))
