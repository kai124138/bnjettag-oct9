#!/usr/bin/env python3
"""Constructive review v4 (2026-09-27): design arithmetic, seeded Monte Carlo, not a result.
Two-mode seeds (archived N=64: 67.18 / 72.64 / 67.21 %), jump 5.4 pt, within-mode sd 0.3 pt,
P(low mode) q = 1/3. Two mechanisms with the same per-run sd (so the same sd_rep, the same pause):
  'shared'  - the mode is set by the seed (init / data order) and shared by every config at seed s;
  'indep'   - each run draws its mode independently.
Prints, per mechanism: P(pause) from 8 replica seeds (sd_rep > 1.3 pt); 5M ranking recovery
(3 true +1 pt cells all in the top 12 of 37, n = 4, mean-g rank); the cell x seed interaction sd
(two-way residual over the 37 x 4 cell matrix, what actually limits the ranking) against sd_rep;
and recovery when the ranking uses a mode-aware readout (drop nothing; rank by mean g, with the
lower-mode count per cell reported).
Also: the same at Gaussian sigma with a shared seed share rho (rho 0 / 0.5 / 0.8)."""
import numpy as np
rng = np.random.default_rng(4040927)
m, n, top, k, reps = 37, 4, 12, 3, 20000
JUMP, WSD, Q = 5.4, 0.3, 1 / 3

def run(mech, reps=reps):
    eff = np.zeros(m); eff[:k] = 1.0
    low_seed = rng.random((reps, 8)) < Q                      # seed-level mode (shared case)
    if mech == 'shared':
        low_rep = low_seed; low_c = np.broadcast_to(low_seed[:, None, :n], (reps, m, n))
    else:
        low_rep = rng.random((reps, 8)) < Q; low_c = rng.random((reps, m, n)) < Q
    rep = -JUMP * low_rep + rng.normal(size=(reps, 8)) * WSD
    c = -JUMP * low_c + rng.normal(size=(reps, m, n)) * WSD + eff[None, :, None]
    sd_rep = rep.std(1, ddof=1)
    g = c - rep[:, None, :n]
    order = np.argsort(-g.mean(2), 1)[:, :top]
    rec = np.all([(order == i).any(1) for i in range(k)], 0).mean()
    resid = c - c.mean(2, keepdims=True) - c.mean(1, keepdims=True) + c.mean((1, 2), keepdims=True)
    s_int = np.sqrt((resid ** 2).sum((1, 2)) / ((m - 1) * (n - 1)))
    return (sd_rep > 1.3).mean(), rec, np.median(sd_rep), np.median(s_int)

print("two-mode seeds, q = 1/3, jump 5.4 pt, within-mode sd 0.3 pt:")
for mech in ('shared', 'indep'):
    p, rec, sr, si = run(mech)
    print(f"  {mech:6s}: P(pause) {p:.2f}; 5M recovery (3 x +1 pt in top 12 of 37, n 4) {rec:.2f}; "
          f"median sd_rep {sr:.2f} pt; median cell x seed interaction sd {si:.2f} pt")

print("Gaussian, per-run sigma, shared seed share rho:")
from scipy import stats
for sigma in (1.5, 3.14):
    for rho in (0.0, 0.5, 0.8):
        eff = np.zeros(m); eff[:k] = 1.0
        a = rng.normal(size=(reps, 1, n)) * np.sqrt(rho) * sigma
        c = a + rng.normal(size=(reps, m, n)) * np.sqrt(1 - rho) * sigma + eff[None, :, None]
        order = np.argsort(-c.mean(2), 1)[:, :top]
        rec = np.all([(order == i).any(1) for i in range(k)], 0).mean()
        ppause = stats.chi2.sf(7 * 1.3 ** 2 / sigma ** 2, 7)
        resid = c - c.mean(2, keepdims=True) - c.mean(1, keepdims=True) + c.mean((1, 2), keepdims=True)
        s_int = np.median(np.sqrt((resid ** 2).sum((1, 2)) / ((m - 1) * (n - 1))))
        print(f"  sigma {sigma}, rho {rho}: P(pause) {ppause:.2f}; recovery {rec:.2f}; "
              f"median interaction sd {s_int:.2f} (= sigma*sqrt(1-rho) {sigma*np.sqrt(1-rho):.2f})")

print("top-k extension beyond the ceiling (rho 0, 5M m 37, top 12, extend top 16; 350k m 11, top 3, extend top 6):")
for fam, mm, kk, tp, ext in (("5M", 37, 3, 12, 16), ("350k", 11, 1, 3, 6)):
    for sigma in (1.5, 2.0, 3.14):
        d = np.zeros(mm); d[:kk] = 1.0
        x = rng.normal(size=(reps, mm, 8)) * sigma + d[None, :, None]
        a4 = np.argsort(-x[:, :, :4].mean(2), 1)
        s1 = a4[:, :ext]
        m8 = np.take_along_axis(x.mean(2), s1, 1)
        b = np.take_along_axis(s1, np.argsort(-m8, 1)[:, :tp], 1)
        hit = lambda sel: np.all([(sel == i).any(1) for i in range(kk)], 0).mean()
        print(f"  {fam} sigma {sigma}: n 4 {hit(a4[:, :tp]):.2f} | extension {hit(b):.2f}")
