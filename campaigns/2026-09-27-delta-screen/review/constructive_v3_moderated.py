"""constructive v3: a variance-moderated max-t (each cell's paired variance shrunk toward the family
pool with a fixed prior df d0, df_i = 3 + d0) against the STUDY's own-sd rule (d0 = 0) and the pooled
rule (d0 -> inf). Placebo-referenced, d_i = cell - placebo, n = 4, one-sided alpha 0.10, critical
value simulated under equal spread for each d0, then applied to screen_null.py's scenario rows.
Also: power of the STUDY's unpaired companion (cell vs 8 replica seeds, own-sd Welch t, crit 2.92 /
3.62). Design arithmetic, seeded Monte Carlo, not a result."""
import numpy as np
rng = np.random.default_rng(20260927)

def gen(m, n, reps, cs=None, mix=None, eff=None, sigma=1.0):
    if mix is not None:
        q, jump, sd = mix
        f = lambda shape: (rng.random(shape) < q) * jump + rng.normal(size=shape) * sd
        p, c = f((reps, n)), f((reps, m, n))
    else:
        p = rng.normal(size=(reps, n)) * sigma
        cs = np.ones(m) if cs is None else cs
        c = rng.normal(size=(reps, m, n)) * cs[None, :, None] * sigma
    if eff is not None:
        c = c + eff[None, :, None]
    return p, c

def t_mod(d, d0):
    n = d.shape[2]; v = d.var(2, ddof=1)
    if d0 == np.inf:
        s2 = v.mean(1, keepdims=True) * np.ones_like(v)
    else:
        s2 = (d0 * v.mean(1, keepdims=True) + (n - 1) * v) / (d0 + n - 1)
    return d.mean(2) / np.sqrt(s2 / n)

for m in (12, 40):
    n = 4
    rows = [("equal spread", {}), ("one cell 3x", dict(cs=np.r_[3.0, np.ones(m - 1)])),
            ("25 % of cells 2x", dict(cs=np.r_[np.full(m // 4, 2.0), np.ones(m - m // 4)])),
            ("25 % of cells 3x", dict(cs=np.r_[np.full(m // 4, 3.0), np.ones(m - m // 4)])),
            ("two-mode q 0.1", dict(mix=(0.1, 5.4, 0.3))), ("two-mode q 0.33", dict(mix=(0.33, 5.4, 0.3)))]
    print(f"m = {m}, n = 4: FWER per scenario | power (one true +1 pt cell) at sigma 0.6 / 1.0 / 1.5")
    for d0 in (0, 3, 6, 12, np.inf):
        p, c = gen(m, n, 60000); crit = np.quantile(t_mod(c - p[:, None, :], d0).max(1), 0.9)
        fw = []
        for lab, kw in rows:
            p, c = gen(m, n, 20000, **kw); fw.append((t_mod(c - p[:, None, :], d0).max(1) > crit).mean())
        pw = []
        for sigma in (0.6, 1.0, 1.5):
            eff = np.zeros(m); eff[0] = 1.0
            p, c = gen(m, n, 20000, eff=eff, sigma=sigma); pw.append((t_mod(c - p[:, None, :], d0)[:, 0] > crit).mean())
        lab = "own sd (STUDY)" if d0 == 0 else ("pooled" if d0 == np.inf else f"d0 = {d0}")
        print(f"   {lab:15s} crit {crit:5.2f}  FWER " + " ".join(f"{x:.3f}" for x in fw) + "  | power " + " / ".join(f"{x:.3f}" for x in pw))
    print("   (FWER columns: " + ", ".join(r[0] for r in rows) + ")")
    # unpaired companion power
    crit_u = {12: 2.923, 40: 3.622}[m]; pw = []
    for sigma in (0.6, 1.0, 1.5):
        c = rng.normal(size=(20000, m, 4)) * sigma; c[:, 0] += 1.0; r = rng.normal(size=(20000, 8)) * sigma
        se = np.sqrt(c.var(2, ddof=1) / 4 + r.var(1, ddof=1)[:, None] / 8)
        pw.append((((c.mean(2) - r.mean(1)[:, None]) / se)[:, 0] > crit_u).mean())
    print(f"   unpaired companion (STUDY, crit {crit_u}), rho = 0: power " + " / ".join(f"{x:.3f}" for x in pw))
