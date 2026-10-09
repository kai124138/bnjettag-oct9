"""constructive v3: family test against a placebo run at seeds 1-8 (unpaired, own-sd Welch t per cell,
many-to-one max-t, one-sided alpha 0.10, critical value simulated under equal spread) against the
STUDY's paired own-sd rule (placebo at seeds 1-n). Scenario rows as screen_null.py §4; rho is the
seed coupling between any two runs at the same seed (the STUDY plans at rho = 0). Design arithmetic,
seeded Monte Carlo, not a result."""
import numpy as np
rng = np.random.default_rng(20260927)

def gen(m, reps, cs=None, mix=None, eff=None, sigma=1.0, rho=0.0):
    if mix is not None:
        q, jump, sd = mix
        f = lambda shape: (rng.random(shape) < q) * jump + rng.normal(size=shape) * sd
        p, c = f((reps, 8)), f((reps, m, 4))
    else:
        a = rng.normal(size=(reps, 8)) * np.sqrt(rho) * sigma
        p = a + rng.normal(size=(reps, 8)) * np.sqrt(1 - rho) * sigma
        cs = np.ones(m) if cs is None else cs
        c = a[:, None, :4] + rng.normal(size=(reps, m, 4)) * np.sqrt(1 - rho) * cs[None, :, None] * sigma
    if eff is not None:
        c = c + eff[None, :, None]
    return p, c

def t_paired(p, c):
    d = c - p[:, None, :4]
    return d.mean(2) / (d.std(2, ddof=1) / 2)

def t_welch(p, c):
    se = np.sqrt(c.var(2, ddof=1) / 4 + p.var(1, ddof=1)[:, None] / 8)
    return (c.mean(2) - p.mean(1)[:, None]) / se

for m in (12, 40):
    rows = [("equal", {}), ("1 cell 3x", dict(cs=np.r_[3.0, np.ones(m - 1)])),
            ("25% 2x", dict(cs=np.r_[np.full(m // 4, 2.0), np.ones(m - m // 4)])),
            ("25% 3x", dict(cs=np.r_[np.full(m // 4, 3.0), np.ones(m - m // 4)])),
            ("2-mode q.1", dict(mix=(0.1, 5.4, 0.3))), ("2-mode q.33", dict(mix=(0.33, 5.4, 0.3))),
            ("2-mode q.5", dict(mix=(0.5, 5.4, 0.3)))]
    for lab, f in (("paired own sd, placebo n 4 (STUDY)", t_paired), ("Welch own sd, placebo n 8", t_welch)):
        p, c = gen(m, 60000); crit = np.quantile(f(p, c).max(1), 0.9)
        fw = [(f(*gen(m, 20000, **kw)).max(1) > crit).mean() for _, kw in rows]
        pw = []
        for sigma, rho in ((0.6, 0), (1.0, 0), (1.5, 0), (0.6, 0.5)):
            eff = np.zeros(m); eff[0] = 1.0
            pw.append((f(*gen(m, 20000, eff=eff, sigma=sigma, rho=rho))[:, 0] > crit).mean())
        print(f"m {m}: {lab:36s} crit {crit:5.2f} FWER " + " ".join(f"{x:.3f}" for x in fw)
              + " | power s0.6 / s1.0 / s1.5 (rho 0), s0.6 rho 0.5: " + " / ".join(f"{x:.3f}" for x in pw))
    print("   FWER columns: " + ", ".join(r[0] for r in rows))
