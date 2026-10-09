#!/usr/bin/env python3
"""Ranking-mode null, family-level test and label threshold for the Delta wave-2 screen (STUDY.md,
fixer v1, 2026-09-27). Design arithmetic by seeded Monte Carlo, not a result.

Model (as in review/rank_sim.py): run accuracy at seed s = shared seed term a_s (share rho of the
variance) + independent term; every cell of a family is paired with the same replica seed s, so
every gap g_is = c_is - r_s carries the same -r_s. sigma is the per-run seed sd (what sd_rep
estimates); rho = 0 is the conservative case (DELTA §5.1's sqrt 2).

Prints:
 1. the arbiter-v1 placebo wording ("no cell's statistic exceeds the placebo's"): P(no | null)
    = 1/(m+1), which is why it is not used as the family-level "no";
 2. the Dunnett-type many-to-one max-t (one-sided, family-pooled paired sd, critical value by
    simulation under the shared-replica null; the null distribution depends on m and n only):
    critical values at alpha 0.10, P(no | null), P(no | one or three true +1 pt effects);
    the placebo's two-sided false-flag rate at the same critical value;
 3. recovery by mean-g rank against sigma (rho = 0): 5M, three true +1 pt cells all in the top 12
    of 40 (chance C(12,3)/C(40,3)); 350k, one true +1 pt cell in the top 3 of 12 (chance 0.25);
    the largest grid sigma at which recovery is >= 0.5 (the v1 ceiling, withdrawn in v5).

v2 (fixer v2, 2026-09-27, STUDY arbiter v2 fixes 2-11). Sections 1-3 are unchanged (section 2 is
the v2 STUDY rule, replica-referenced with a pooled sd, kept for the record; superseded). Added:
 4. family-test calibration under the arbiter's scenario rows, for four rules: R0 the superseded
    v2 rule (d = cell - replica, pooled sd); R1 placebo-referenced, pooled sd; R2 = rule (a)
    placebo-referenced, each cell's own sd (df n - 1); R3 = rule (b) pooled sd plus a homogeneity
    gate (largest own sd / s_pool above its null 95th percentile) falling back to R2. Scenario
    rows: equal spread; one cell at 3x run sd; 25 % of cells at 2x and 3x; two-mode seeds q = 0.1 /
    0.33 / 0.5 (constructive model, jump 5.4 pt, sd 0.3 pt); a common offset of 0.5 / 0.707 SE on
    every non-replica run; a near-deterministic placebo (placebo - replica gap sd 0.15x); n = 3
    (cheap version, and a family after one replica or placebo seed is lost). Plus the
    bit-identical branch (placebo = replica, so d = g): own sd, with and without the offset.
 5. power of R1 / R2 / R3: one true +1 pt cell at sigma 0.6 / 1.5 / 3.14 pt.
 6. coverage of the ranking interval mean g +- t(0.975, df) s_pool / sqrt(n) with df = m(n - 1)
    (nominal 95 %) and the simulated multiplier that gives 95 %.
 7. G3' power: P(lower 95 % bound on g > -0.3 pt | true g = 0), own sd, df 3, two-sided and
    one-sided bound.
 8. rank-move flag: expected number of null cells whose rank moves by more than T places between
    the primary and the companion, against the run-level primary-companion correlation.
 9. null interval of the family-pooled cell-replica correlation rho-hat (rho = 0).
10. withdrawn in v5 (sd_rep ceiling; draws kept unprinted so later sections reproduce).
11. unpaired companion (cell against the 8 replica seeds, own-sd Welch t): critical values.
12. placebo check (two-sided paired t, own sd, alpha 0.05): false-flag rate and the offset
    detected with probability 0.5 / 0.8, in pt, at sigma 0.6 / 1.5 / 3.14.
13. own-sd critical values at m = 11 (350k) and 37 (5M), the family-test m once the long-horizon
    cells M015, M031, M032 leave it (printed last so sections 1-12 keep their random stream).

v3 (fixer v3, 2026-09-27, STUDY arbiter v3 fixes 4, 7, 9, 10). Sections 1-13 are unchanged and
reproduce digit for digit (new sections are appended, so the random stream of 1-13 is untouched;
section 13 now also stores its values for reuse). Added:
14. withdrawn in v5 (P(pause) at the sd_rep ceiling; exact, no draws).
15. The ranked list and the family test at their actual design m once M015, M031 and M032 leave
    both (fix 4): m = 11 (350k) and m = 37 (5M, at most). Own-sd (R2) calibration rows at n = 4
    and 3 with the section-13 critical values; power; ranking-interval multiplier; rank-move
    null counts; rho-hat null interval; unpaired-companion critical values; the Gaussian
    recovery criterion (condition (i) of the section-18 label threshold) (5M: three true +1 pt cells all in the top 12 of 37; 350k: one in the top
    3 of 11); the arbiter-v1 placebo wording at these m.
16. Ranking-mode top-k extension (fix 10, [DK16]): after the n = 4 readout the top 16 of 37 (5M)
    or top 6 of 11 (350k) get seeds 5-8; the final order of the extended cells is by their 8-seed
    mean. P(all true cells in the final top 12 / top 3) for n = 4, the extension and n = 6.
17. Floor-family G2 null false-rescue rate (fix 7), exact binomial: P(k_e >= 3 and
    k_e - k_base >= 2) with k_e, k_base ~ Bin(n, p) independent, and at a fixed k_base.
v4 (fixer v4, 2026-09-27, STUDY arbiter v4 fixes 1-2). The compute pause is withdrawn, so
sections 10 and 14 no longer print (section 10's draws are kept so 11-17 reproduce digit for
digit). Section 15 stores its Gaussian recovery rows for reuse. Added, at the end:
18. Two-mode seeds (jump 5.4 pt, within-mode sd 0.3 pt; per-run mode and seed-shared mode) for
    both families (5M: m 37, 3 x +1 pt, top 12, extension top 16; 350k: m 11, 1 x +1 pt, top 3,
    extension top 6; n 4): median s_int (the two-way cell x seed residual sd of the m x 4 cell
    matrix), recovery, and the [DK16] extension, over a q grid; then the label threshold T per
    family: the largest 0.1-pt T with (i) Gaussian recovery at sigma = T >= 0.5 (section 15 grid)
    and (ii) per-run two-mode recovery conditional on s_int <= T >= 0.5 at every q whose
    conditional set is non-empty. Conditional set sizes are printed. [T rule replaced in v5 below]
v5 (fixer v5, 2026-09-28, STUDY arbiter v5 fixes 2, 4-5 and C row 20; Kai's decision 2026-09-28: median
of the 4 paired gaps is the primary ranking statistic). Sections 1-17 and the section-18 draws are
unchanged and reproduce digit for digit at the design seed (every new draw is appended after the last
existing one). Changed in 18:
    the label threshold T. Condition (ii) fails a q only where P(s_int <= T | q) >= 0.01 (a probability
    floor, 200 of 20,000 draws), and (i) and (ii) are evaluated with the whole script run at ten RNG
    seeds, the design seed 20260927 and seeds 1-9 (child processes, --t-only); T per family is the
    minimum over the ten. The per-seed T under the v4 rule (any non-empty set) is printed beside it.
    Recovery is also scored by median g (median of the n = 4 paired g_s) from the same draws.
Added at the end (fresh draws, printed last so that sections 1-18 keep their random stream):
18b. mean-g against median-g recovery: Gaussian sigma 0.6 / 1.0 / 1.3, per-run two-mode q 0.02 / 0.05 /
    0.1 / 0.2 / 0.33 / 0.5 (with the recovery among draws with s_int <= T), seed-shared mode; both
    families (after review/constructive_v5_robust.py).
18c. the mode readout's operating characteristics on 8 replica values (STUDY Controls rule): false
    flag under Gaussian seeds, power at per-run q.
15a. the family test's detectable effect for one named cell: effect in pt at 50 % / 80 % power, own-sd t
    on d = cell - placebo, n = 4, section-13 critical values, m 11 / 37, sigma 0.6 / 1.5 / 3.14 (after
    review/arbiter_v5_power.py; belongs with 15, printed last to keep the stream).
18d. Gaussian recovery at sigma = T by mean g and by median g (condition (i) under the median primary).
v6 (experiment-designer, 2026-09-28, fixer v5's routed item: re-simulate with median g as the ranking statistic,
same seed models, grids, reps and rules). Median-g scores are computed from the draws already made in sections
8, 15, 16 and 18 (np.median over the same seed axis; zero new random numbers), so every earlier line reproduces
digit for digit at the design seed; they are printed only in a new section at the end:
19. median g as the ranking statistic: (a) the label threshold T by the unchanged v5 rule with both conditions
    scored by median g (condition (i) on the section-15 Gaussian grid, the same draws; condition (ii) on the
    section-18 per-run draws; floor 0.01; minimum over the ten seeds; children emit TMSEED lines); (b) the
    conditional, band and above-band rows at that T, n = 4 and [DK16] extension, the extension selecting the top
    k by 4-seed median g and ordering them by 8-seed median g; seed-shared rows; (c) section 16 by median g
    (n = 4 / extension / n = 6 by 6-seed median); (d) sections 8 and 15 rank-move null counts with both primary
    and companion ranked by median g, and the thresholds the unchanged rule gives (smallest grid T whose count
    at the lower edge of r's band is <= 1.0).
v7 (fixer v6, 2026-09-28): 19e appended, the design-seed T at floors 0.005 / 0.01 / 0.02 / 0.05 by median g and
mean g from the stored recovery (no new draws; every earlier line unchanged).
Usage: python3 screen_null.py [--seed N] [--t-only]   (--t-only: print only the per-seed T lines)
"""
import argparse
import os
import subprocess
import sys
import numpy as np
from math import comb
from scipy import stats

DESIGN_SEED = 20260927
T_SEEDS = (DESIGN_SEED, 1, 2, 3, 4, 5, 6, 7, 8, 9)
T_FLOOR = 0.01    # condition (ii) is evaluated only where P(s_int <= T | q) >= T_FLOOR
_ap = argparse.ArgumentParser()
_ap.add_argument("--seed", type=int, default=DESIGN_SEED)
_ap.add_argument("--t-only", action="store_true")
ARGS = _ap.parse_args()
OUT = sys.stdout
if ARGS.t_only:
    sys.stdout = open(os.devnull, "w")
rng = np.random.default_rng(ARGS.seed)
ALPHA = 0.10


def draw(m, n, reps, sigma=1.0, rho=0.0, eff=None):
    a = rng.normal(size=(reps, 1, n)) * np.sqrt(rho) * sigma
    rep = a[:, 0, :] + rng.normal(size=(reps, n)) * np.sqrt(1 - rho) * sigma
    pla = a[:, 0, :] + rng.normal(size=(reps, n)) * np.sqrt(1 - rho) * sigma
    c = a + rng.normal(size=(reps, m, n)) * np.sqrt(1 - rho) * sigma
    if eff is not None:
        c = c + eff[None, :, None]
    return c - rep[:, None, :], pla - rep          # cell gaps, placebo gap


def tstats(g, gp):
    n = g.shape[2]
    res = np.concatenate([g - g.mean(2, keepdims=True), (gp - gp.mean(1, keepdims=True))[:, None, :]], 1)
    s = np.sqrt((res ** 2).sum((1, 2)) / (res.shape[1] * (n - 1)))   # family-pooled paired sd
    return g.mean(2) / (s[:, None] / np.sqrt(n)), gp.mean(1) / (s / np.sqrt(n))


def crit(m, n, reps=40000):
    g, gp = draw(m, n, reps)
    t, _ = tstats(g, gp)
    return np.quantile(t.max(1), 1 - ALPHA)


if __name__ == "__main__":
    print("1. arbiter-v1 placebo wording, P(no cell mean g > placebo mean g | global null):")
    for m in (12, 40):
        g, gp = draw(m, 4, 20000)
        print(f"   m = {m}: {(g.mean(2).max(1) <= gp.mean(1)).mean():.3f}  (1/(m+1) = {1 / (m + 1):.3f})")
    print(f"2. Dunnett-type max-t, one-sided, alpha {ALPHA}, pooled paired sd (cells + placebo):")
    C = {}
    for m in (12, 40):
        for n in (4, 6, 8):
            C[m, n] = c = crit(m, n)
            g, gp = draw(m, n, 20000)
            t, tp = tstats(g, gp)
            p_no = (t.max(1) <= c).mean()
            flag = (np.abs(tp) > c).mean()
            print(f"   m = {m}, n = {n}: critical t {c:.3f}; P(no | null) {p_no:.3f}; placebo |t| > crit {flag:.4f}")
    for m, k in ((12, 1), (40, 1), (40, 3)):
        for sigma in (0.6, 1.5, 3.14):
            eff = np.zeros(m); eff[:k] = 1.0
            g, gp = draw(m, 4, 10000, sigma=sigma, eff=eff)
            t, _ = tstats(g, gp)
            print(f"   m = {m}, n = 4, {k} true +1 pt, sigma {sigma}: P(no) {(t.max(1) <= C[m, 4]).mean():.3f}; "
                  f"P(a true cell above crit) {(t[:, :k] > C[m, 4]).any(1).mean():.3f}")
    print("3. recovery by mean-g rank, rho = 0, n = 4:")
    ceil = {}
    for fam, m, k, top in (("5M", 40, 3, 12), ("350k", 12, 1, 3)):
        chance = comb(top, k) / comb(m, k)
        rows = []
        for sigma in np.round(np.arange(0.4, 3.01, 0.1), 2):
            eff = np.zeros(m); eff[:k] = 1.0
            g, _ = draw(m, 4, 8000, sigma=sigma, eff=eff)
            order = np.argsort(-g.mean(2), 1)[:, :top]
            rec = np.all([(order == i).any(1) for i in range(k)], 0).mean()
            rows.append((sigma, rec))
        ceil[fam] = max(s for s, r in rows if r >= 0.5)
        print(f"   {fam}: m {m}, {k} true +1 pt, top {top}, chance {chance:.3f}: " +
              ", ".join(f"{s:.1f}:{r:.2f}" for s, r in rows))
        print(f"   {fam} largest sigma with recovery >= 0.5 (v1 design grid; the v1 sd_rep ceiling is withdrawn in v5): {ceil[fam]:.1f} pt")

    # ---------------------------------------------------------------- v2 sections (fixer v2)
    def gen(m, n, reps, cs=None, pl=1.0, mix=None, off=0.0, eff=None, sigma=1.0):
        """replica r, placebo p, cells c (reps, m, n). cs: per-cell run-sd multipliers; pl: 'det' for a
        near-deterministic placebo (placebo - replica gap sd 0.15x of a cell's); mix: (q, jump, sd)
        two-mode seeds; off: offset on every non-replica run (cells and placebo), in run-sd units."""
        if mix is not None:
            q, jump, sd = mix
            f = lambda shape: (rng.random(shape) < q) * jump + rng.normal(size=shape) * sd
            r, p, c = f((reps, n)), f((reps, n)), f((reps, m, n))
        else:
            r = rng.normal(size=(reps, n)) * sigma
            p = r + rng.normal(size=(reps, n)) * 0.15 * sigma * np.sqrt(2) if pl == 'det' else rng.normal(size=(reps, n)) * sigma
            cs = np.ones(m) if cs is None else cs
            c = rng.normal(size=(reps, m, n)) * cs[None, :, None] * sigma
        c = c + off; p = p + off
        if eff is not None:
            c = c + eff[None, :, None]
        return r, p, c

    def t_pool(d):
        n = d.shape[2]; res = d - d.mean(2, keepdims=True)
        s = np.sqrt((res ** 2).sum((1, 2)) / (d.shape[1] * (n - 1)))
        return d.mean(2) / (s[:, None] / np.sqrt(n)), s

    def t_own(d):
        return d.mean(2) / (d.std(2, ddof=1) / np.sqrt(d.shape[2]))

    def ratio(d):
        return d.std(2, ddof=1).max(1) / t_pool(d)[1]

    print("4. family test, P(false 'some cell above' | every cell null), one-sided alpha 0.10 per family:")
    CRIT = {}
    for m in (12, 40):
        for n in (3, 4):
            r, p, c = gen(m, n, 60000)
            d = c - p[:, None, :]; g = c - r[:, None, :]
            cp = np.quantile(t_pool(d)[0].max(1), 0.9); co = np.quantile(t_own(d).max(1), 0.9)
            cg = np.quantile(ratio(d), 0.95); c0 = np.quantile(t_pool(g)[0].max(1), 0.9)
            cb = np.quantile(t_own(g).max(1), 0.9)
            CRIT[m, n] = (cp, co, cg, cb)
            print(f"   m = {m}, n = {n}: critical t R0 {c0:.3f}, R1 {cp:.3f}, R2 own-sd {co:.3f}; gate ratio 95th pct {cg:.3f}; "
                  f"bit-identical branch own-sd {cb:.3f}")
            se = np.sqrt(2 / n)   # SE of one cell's mean gap, run-sd units
            rows = [("equal spread", {}), ("one cell 3x", dict(cs=np.r_[3.0, np.ones(m - 1)])),
                    ("25 % of cells 2x", dict(cs=np.r_[np.full(m // 4, 2.0), np.ones(m - m // 4)])),
                    ("25 % of cells 3x", dict(cs=np.r_[np.full(m // 4, 3.0), np.ones(m - m // 4)])),
                    ("two-mode q 0.1", dict(mix=(0.1, 5.4, 0.3))), ("two-mode q 0.33", dict(mix=(0.33, 5.4, 0.3))),
                    ("two-mode q 0.5", dict(mix=(0.5, 5.4, 0.3))), ("offset 0.5 SE", dict(off=0.5 * se)),
                    ("offset 0.707 SE", dict(off=0.707 * se)), ("near-deterministic placebo", dict(pl='det'))]
            for lab, kw in rows:
                r, p, c = gen(m, n, 20000, **kw)
                d = c - p[:, None, :]; g = c - r[:, None, :]
                r0 = (t_pool(g)[0].max(1) > c0).mean(); r1 = (t_pool(d)[0].max(1) > cp).mean()
                to = t_own(d).max(1) > co; gate = ratio(d) > cg
                r3 = np.where(gate, to, t_pool(d)[0].max(1) > cp).mean()
                print(f"      {lab:27s} R0 {r0:.3f}  R1 {r1:.3f}  R2 {to.mean():.3f}  R3 {r3:.3f} (gate fails {gate.mean():.2f})")
            for lab, off in (("no offset", 0.0), ("offset 0.707 SE", 0.707 * se)):
                r, p, c = gen(m, n, 20000, off=off)
                g = c - r[:, None, :]
                print(f"      bit-identical branch (d = g), own sd, {lab:15s}: {(t_own(g).max(1) > cb).mean():.3f}")
    print("5. power, one true +1 pt cell (others null), P(that cell named):")
    for m in (12, 40):
        n = 4; cp, co, cg, _ = CRIT[m, n]
        for sigma in (0.6, 1.5, 3.14):
            eff = np.zeros(m); eff[0] = 1.0
            r, p, c = gen(m, n, 20000, eff=eff, sigma=sigma)
            d = c - p[:, None, :]; tp = t_pool(d)[0]; to = t_own(d); gate = ratio(d) > cg
            print(f"   m = {m}, n = 4, sigma {sigma}: R1 {(tp[:, 0] > cp).mean():.3f}  R2 {(to[:, 0] > co).mean():.3f}  "
                  f"R3 {np.where(gate, to[:, 0] > co, tp[:, 0] > cp).mean():.3f}")
    print("6. ranking interval mean g +- t(0.975, m(n-1)) s_pool / sqrt(n), shared replica, placebo excluded:")
    for m in (12, 40):
        n = 4
        r, p, c = gen(m, n, 20000)
        g = c - r[:, None, :]; tp, s = t_pool(g)
        tq = stats.t.ppf(0.975, m * (n - 1))
        print(f"   m = {m}, n = 4: nominal 95 % (t {tq:.3f}) covers {(np.abs(tp) <= tq).mean():.3f}; "
              f"multiplier for 95 % coverage {np.quantile(np.abs(tp), 0.95):.3f}")
    print("7. G3' power, P(lower 95 % bound > -0.3 pt | g = 0), own sd df 3 (sigma = per-run seed sd, rho = 0):")
    t2, t1 = stats.t.ppf(0.975, 3), stats.t.ppf(0.95, 3)
    for sigma in (0.10, 0.13, 0.20, 0.30, 0.6, 1.5, 3.14):
        g = rng.normal(size=(40000, 4)) * sigma * np.sqrt(2)
        mu, sd = g.mean(1), g.std(1, ddof=1) / 2
        print(f"   sigma {sigma:4.2f} pt: two-sided bound {(mu - t2 * sd > -0.3).mean():.3f}; one-sided bound {(mu - t1 * sd > -0.3).mean():.3f}")
    RMM = {}   # v6: rank-move null counts by median g, printed in section 19
    print("8. rank-move flag, expected number of null cells flagged per family (run-level corr of primary and companion r):")
    for m, Ts in ((12, (2, 3, 4, 5, 6)), (40, (5, 8, 10, 12, 15))):
        for rr in (0.5, 0.7, 0.9, 0.95):
            n = 4; reps = 4000
            x = rng.normal(size=(reps, m + 1, n)); y = rr * x + np.sqrt(1 - rr ** 2) * rng.normal(size=(reps, m + 1, n))
            gp = x[:, 1:].mean(2) - x[:, :1].mean(2); gc = y[:, 1:].mean(2) - y[:, :1].mean(2)
            rk = lambda a: np.argsort(np.argsort(-a, 1), 1)
            mv = np.abs(rk(gp) - rk(gc))
            mvm = np.abs(rk(np.median(x[:, 1:] - x[:, :1], 2)) - rk(np.median(y[:, 1:] - y[:, :1], 2)))   # v6, same draws
            RMM[m, rr] = [(T, (mvm > T).sum(1).mean()) for T in Ts]
            print(f"   m = {m}, r = {rr}: " + ", ".join(f"T {T}: {(mv > T).sum(1).mean():.1f}" for T in Ts))
    print("9. family-pooled cell-replica correlation rho-hat under rho = 0 (centred per seed-set), 95 % null interval:")
    for m in (12, 40):
        n = 4; r, p, c = gen(m, n, 20000)
        cc = c - c.mean(2, keepdims=True); rc = (r - r.mean(1, keepdims=True))[:, None, :]
        rho = (cc * rc).sum((1, 2)) / np.sqrt((cc ** 2).sum((1, 2)) * (rc ** 2).sum((1, 2)) * m)
        print(f"   m = {m}, n = 4: 2.5 / 97.5 % {np.quantile(rho, 0.025):+.2f} / {np.quantile(rho, 0.975):+.2f}")
    # 10. withdrawn in v5 (the sd_rep ceiling and compute pause are withdrawn, STUDY v5). Its draws
    #     are kept, unprinted, so that sections 11-18 keep their random stream and reproduce.
    for k in (8, 6):
        for sigma in (0.9, 1.1, 1.3, 1.5, 2.0):
            rng.normal(size=(40000, k))
    print("11. unpaired companion, cell (n = 4) against the 8 replica seeds, own-sd Welch t, one-sided alpha 0.10:")
    for m in (12, 40):
        c = rng.normal(size=(40000, m, 4)); r = rng.normal(size=(40000, 8))
        se_ = np.sqrt(c.var(2, ddof=1) / 4 + r.var(1, ddof=1)[:, None] / 8)
        t = (c.mean(2) - r.mean(1)[:, None]) / se_
        print(f"   m = {m}: critical t {np.quantile(t.max(1), 0.9):.3f}")
    print("12. placebo check, two-sided paired t of placebo - replica on its own sd (df 3), alpha 0.05:")
    t2 = stats.t.ppf(0.975, 3)
    g = rng.normal(size=(40000, 4)) * np.sqrt(2)
    print(f"   false flag under the null {(np.abs(t_own(g[:, None, :])[:, 0]) > t2).mean():.3f}")
    for sigma in (0.6, 1.5, 3.14):
        res = []
        for target in (0.5, 0.8):
            grid = np.arange(0.0, 12.0, 0.05)
            z = rng.normal(size=(8000, 4)) * sigma * np.sqrt(2)
            for delta in grid:
                gg = z + delta
                if (np.abs(gg.mean(1) / (gg.std(1, ddof=1) / 2)) > t2).mean() >= target:
                    break
            res.append(f"P {target}: {delta:.2f} pt")
        print(f"   sigma {sigma}: offset detected with " + ", ".join(res))
    print("13. own-sd (R2) critical values at the family-test m after the long-horizon cells leave it (m 11 at 350k, <= 37 at 5M):")
    CR13 = {}
    for m, n in ((11, 4), (37, 4), (11, 3), (37, 3)):
        r, p, c = gen(m, n, 60000)
        CR13[m, n] = np.quantile(t_own(c - p[:, None, :]).max(1), 0.9)
        print(f"   m = {m}, n = {n}: {CR13[m, n]:.3f}")

    # ---------------------------------------------------------------- v3 sections (fixer v3)
    # 14. withdrawn in v5 (exact, no random draws; the pause it priced is withdrawn).
    print("15. ranked list and family test at m = 11 (350k) / 37 (5M); R2 = own sd against the placebo:")
    for m in (11, 37):
        for n in (4, 3):
            co = CR13[m, n]
            print(f"   m = {m}, n = {n}: critical t (section 13) {co:.3f}; P(false 'yes') per row:")
            se = np.sqrt(2 / n)
            rows = [("equal spread", {}), ("one cell 3x", dict(cs=np.r_[3.0, np.ones(m - 1)])),
                    ("25 % of cells 2x", dict(cs=np.r_[np.full(m // 4, 2.0), np.ones(m - m // 4)])),
                    ("25 % of cells 3x", dict(cs=np.r_[np.full(m // 4, 3.0), np.ones(m - m // 4)])),
                    ("two-mode q 0.1", dict(mix=(0.1, 5.4, 0.3))), ("two-mode q 0.33", dict(mix=(0.33, 5.4, 0.3))),
                    ("two-mode q 0.5", dict(mix=(0.5, 5.4, 0.3))), ("offset 0.5 SE", dict(off=0.5 * se)),
                    ("offset 0.707 SE", dict(off=0.707 * se)), ("near-deterministic placebo", dict(pl='det'))]
            for lab, kw in rows:
                r, p, c = gen(m, n, 20000, **kw)
                print(f"      {lab:27s} {(t_own(c - p[:, None, :]).max(1) > co).mean():.3f}")
        co = CR13[m, 4]
        pw = []
        for sigma in (0.6, 1.0, 1.5, 3.14):
            eff = np.zeros(m); eff[0] = 1.0
            r, p, c = gen(m, 4, 20000, eff=eff, sigma=sigma)
            pw.append(f"sigma {sigma}: {(t_own(c - p[:, None, :])[:, 0] > co).mean():.3f}")
        print(f"   m = {m}, n = 4, power (one true +1 pt cell named): " + "; ".join(pw))
        r, p, c = gen(m, 4, 20000)
        g = c - r[:, None, :]; tp, _ = t_pool(g)
        tq = stats.t.ppf(0.975, m * 3)
        print(f"   m = {m}, n = 4, ranking interval: nominal t {tq:.3f} covers {(np.abs(tp) <= tq).mean():.3f}; "
              f"multiplier for 95 % coverage (equal spread) {np.quantile(np.abs(tp), 0.95):.3f}")
        Ts = (2, 3, 4, 5, 6) if m == 11 else (5, 8, 10, 12, 15)
        for rr in (0.5, 0.7, 0.9, 0.95):
            n = 4; reps = 4000
            x = rng.normal(size=(reps, m + 1, n)); y = rr * x + np.sqrt(1 - rr ** 2) * rng.normal(size=(reps, m + 1, n))
            gp = x[:, 1:].mean(2) - x[:, :1].mean(2); gc = y[:, 1:].mean(2) - y[:, :1].mean(2)
            rk = lambda a: np.argsort(np.argsort(-a, 1), 1)
            mv = np.abs(rk(gp) - rk(gc))
            mvm = np.abs(rk(np.median(x[:, 1:] - x[:, :1], 2)) - rk(np.median(y[:, 1:] - y[:, :1], 2)))   # v6, same draws
            RMM[m, rr] = [(T, (mvm > T).sum(1).mean()) for T in Ts]
            print(f"   m = {m}, rank-move null flags, r = {rr}: " + ", ".join(f"T {T}: {(mv > T).sum(1).mean():.1f}" for T in Ts))
        r, p, c = gen(m, 4, 20000)
        cc = c - c.mean(2, keepdims=True); rc = (r - r.mean(1, keepdims=True))[:, None, :]
        rho = (cc * rc).sum((1, 2)) / np.sqrt((cc ** 2).sum((1, 2)) * (rc ** 2).sum((1, 2)) * m)
        print(f"   m = {m}, rho-hat null 2.5 / 97.5 %: {np.quantile(rho, 0.025):+.2f} / {np.quantile(rho, 0.975):+.2f}")
        c = rng.normal(size=(40000, m, 4)); r = rng.normal(size=(40000, 8))
        se_ = np.sqrt(c.var(2, ddof=1) / 4 + r.var(1, ddof=1)[:, None] / 8)
        print(f"   m = {m}, unpaired companion critical t: {np.quantile(((c.mean(2) - r.mean(1)[:, None]) / se_).max(1), 0.9):.3f}")
        g, gp = draw(m, 4, 20000)
        print(f"   m = {m}, arbiter-v1 placebo wording P(no | null): {(g.mean(2).max(1) <= gp.mean(1)).mean():.3f} "
              f"(1/(m+1) = {1 / (m + 1):.3f})")
    REC15 = {}   # Gaussian recovery rows, stored for section 18 (no extra draws)
    REC15M = {}  # v6: the same rows scored by median g (same draws)
    for fam, m, k, top in (("5M", 37, 3, 12), ("350k", 11, 1, 3)):
        chance = comb(top, k) / comb(m, k)
        rows = []
        for sigma in np.round(np.arange(0.4, 3.01, 0.1), 2):
            eff = np.zeros(m); eff[:k] = 1.0
            g, _ = draw(m, 4, 8000, sigma=sigma, eff=eff)
            order = np.argsort(-g.mean(2), 1)[:, :top]
            rows.append((sigma, np.all([(order == i).any(1) for i in range(k)], 0).mean()))
            om15 = np.argsort(-np.median(g, 2), 1)[:, :top]
            REC15M.setdefault(fam, []).append((sigma, np.all([(om15 == i).any(1) for i in range(k)], 0).mean()))
        REC15[fam] = rows
        print(f"   recovery {fam}: m {m}, {k} true +1 pt, top {top}, chance {chance:.4f}: " +
              ", ".join(f"{s_:.1f}:{r_:.2f}" for s_, r_ in rows))
        print(f"   {fam} largest grid sigma with recovery >= 0.5: {max(s_ for s_, r_ in rows if r_ >= 0.5):.1f} pt")
    EXT16M = []   # v6
    print("16. top-k extension (seeds 5-8 for the top k after n = 4), rho = 0, true cells +1 pt:")
    for fam, m, k, top, ext in (("5M", 37, 3, 12, 16), ("350k", 11, 1, 3, 6)):
        for sigma in (0.6, 1.0, 1.3, 1.5):
            reps = 20000
            d = np.zeros(m); d[:k] = 1.0
            x = rng.normal(size=(reps, m, 8)) * sigma + d[None, :, None]
            a = np.argsort(-x[:, :, :4].mean(2), 1)[:, :top]
            s1 = np.argsort(-x[:, :, :4].mean(2), 1)[:, :ext]
            m8 = np.take_along_axis(x.mean(2), s1, 1)
            b = np.take_along_axis(s1, np.argsort(-m8, 1)[:, :top], 1)
            c6 = np.argsort(-x[:, :, :6].mean(2), 1)[:, :top]
            hit = lambda sel: np.all([(sel == i).any(1) for i in range(k)], 0).mean()
            s1m = np.argsort(-np.median(x[:, :, :4], 2), 1)[:, :ext]   # v6, median g, same draws
            bm = np.take_along_axis(s1m, np.argsort(-np.take_along_axis(np.median(x, 2), s1m, 1), 1)[:, :top], 1)
            EXT16M.append((fam, sigma, hit(np.argsort(-np.median(x[:, :, :4], 2), 1)[:, :top]), hit(bm),
                           hit(np.argsort(-np.median(x[:, :, :6], 2), 1)[:, :top])))
            print(f"   {fam} m {m}, top {top}, extend top {ext}, sigma {sigma}: n = 4 {hit(a):.2f} | extension {hit(b):.2f} | n = 6 {hit(c6):.2f}")
    print("17. floor-family G2 null false-rescue, P(k_e >= 3 and k_e - k_base >= 2), exact binomial:")
    for n in (4, 3):
        out = []
        for pp in (0.25, 0.5, 0.75):
            pe = stats.binom.pmf(np.arange(n + 1), n, pp)
            prob = sum(pe[ke] * pe[kb] for ke in range(n + 1) for kb in range(n + 1) if ke >= 3 and ke - kb >= 2)
            out.append(f"p {pp}: {prob:.3f} (x 7 entries: {7 * prob:.2f})")
        print(f"   p_e = p_base = p, n = {n}: " + "; ".join(out))
    for kb in (0, 1, 2):
        out = [f"p_e {pe_}: {stats.binom.sf(max(3, kb + 2) - 1, 4, pe_):.3f}" for pe_ in (0.5, 0.75, 0.9)]
        print(f"   n = 4, observed k_base = {kb} (rescue needs k_e >= {max(3, kb + 2)}): " + "; ".join(out))

    # ---------------------------------------------------------------- v4 section (fixer v4)
    print("18. two-mode seeds: s_int, ranking recovery, top-k extension and the label threshold T:")
    JUMP, WSD = 5.4, 0.3
    NAMED_Q = (0.02, 0.05, 0.1, 0.33, 0.5)
    # q grid: the named q values plus q at per-run sd steps of 0.05 pt (sd(q)^2 = JUMP^2 q (1 - q) + WSD^2)
    v = np.arange(0.35, 2.701, 0.05) ** 2 - WSD ** 2
    QGRID = sorted(set(np.round((1 - np.sqrt(1 - 4 * v / JUMP ** 2)) / 2, 5)) | set(NAMED_Q))
    FAM18 = (("5M", 37, 3, 12, 16), ("350k", 11, 1, 3, 6))   # family, m, true +1 pt cells, top, extend top

    def twomode(m, k, top, ext, q, shared, reps=20000):
        """Replica seeds 1-8 and cells at seeds 1-8; the low mode is JUMP below, within-mode sd WSD.
        shared: the mode is set by the seed and shared by every config at seed s; else drawn per run.
        Returns s_int (two-way cell x seed residual sd of the m x 4 cell matrix, df (m-1)*3), the
        n = 4 recovery hit and the [DK16] extension hit per replication."""
        eff = np.zeros(m); eff[:k] = 1.0
        if shared:
            low = rng.random((reps, 8)) < q
            low_r, low_c = low, np.broadcast_to(low[:, None, :], (reps, m, 8))
        else:
            low_r, low_c = rng.random((reps, 8)) < q, rng.random((reps, m, 8)) < q
        r = -JUMP * low_r + rng.normal(size=(reps, 8)) * WSD
        c = -JUMP * low_c + rng.normal(size=(reps, m, 8)) * WSD + eff[None, :, None]
        c4 = c[:, :, :4]
        res = c4 - c4.mean(2, keepdims=True) - c4.mean(1, keepdims=True) + c4.mean((1, 2), keepdims=True)
        s_int = np.sqrt((res ** 2).sum((1, 2)) / ((m - 1) * 3))
        g = c - r[:, None, :]
        o4 = np.argsort(-g[:, :, :4].mean(2), 1)
        hit = lambda sel: np.all([(sel == i).any(1) for i in range(k)], 0)
        s1 = o4[:, :ext]
        m8 = np.take_along_axis(g.mean(2), s1, 1)
        b = np.take_along_axis(s1, np.argsort(-m8, 1)[:, :top], 1)
        om = np.argsort(-np.median(g[:, :, :4], 2), 1)   # median g, same draws (no extra random numbers)
        s1m = om[:, :ext]   # v6: [DK16] extension by median g (4-seed median selects, 8-seed median orders)
        bm = np.take_along_axis(s1m, np.argsort(-np.take_along_axis(np.median(g, 2), s1m, 1), 1)[:, :top], 1)
        return s_int, hit(o4[:, :top]), hit(b), hit(om[:, :top]), hit(bm)


    T18, PRS, GAUSS = {}, {}, {}
    SHM, PRX, T18M, FAILM = {}, {}, {}, {}   # v6: median-g seed-shared rows, extension hits, T, design-seed failures
    for fam, m, k, top, ext in FAM18:
        print(f"   {fam}: m {m}, {k} true +1 pt, top {top}, extension top {ext}; jump {JUMP} pt, within-mode sd {WSD} pt, n = 4")
        print("   seed-shared mode (context; not used by the threshold rule):")
        for q in NAMED_Q:
            si, h, hx, hm, hmx = twomode(m, k, top, ext, q, True)
            SHM[fam, q] = (hm.mean(), hmx.mean())
            print(f"      q {q:.2f}: per-run sd {np.sqrt(JUMP ** 2 * q * (1 - q) + WSD ** 2):.2f} pt; median s_int {np.median(si):.2f} pt; "
                  f"recovery {h.mean():.2f}; extension {hx.mean():.2f}")
        print("   per-run mode, q grid:")
        PR = []
        for q in QGRID:
            si, h, hx, hm, hmx = twomode(m, k, top, ext, q, False)
            PR.append((q, si, h, hx, hm))
            PRX[fam, q] = hmx
            print(f"      q {q:.4f}: per-run sd {np.sqrt(JUMP ** 2 * q * (1 - q) + WSD ** 2):.2f} pt; median s_int {np.median(si):.2f} pt; "
                  f"recovery {h.mean():.2f}; extension {hx.mean():.2f}")
        PRS[fam] = PR
        med = [np.median(x[1]) for x in PR]
        # below about 1 pt the median jumps between 0, 1 and 2 low-mode runs in the m x 4 matrix; no q grid removes that
        st = np.diff(med); hi = np.array(med[:-1]) >= 1.0
        print(f"   largest step between consecutive median s_int: {st.max():.3f} pt overall; {st[hi].max():.3f} pt where the "
              f"medians are >= 1.0 pt (rule: <= 0.1 pt)")
        # threshold rule (v5): the largest 0.1-pt T with (i) Gaussian recovery at sigma = T >= 0.5 (section 15 grid) and
        # (ii) per-run two-mode recovery conditional on s_int <= T >= 0.5 at every q with P(s_int <= T | q) >= T_FLOOR.
        # The v4 rule (every q whose conditional set is non-empty) is computed beside it for the record.
        gauss = dict((round(s_, 1), r_) for s_, r_ in REC15[fam])
        GAUSS[fam] = gauss
        ok, ok_v4 = [], []
        for T in np.round(np.arange(0.4, 3.01, 0.1), 1):
            fails = [(q, (si <= T).sum(), h[si <= T].mean()) for q, si, h, _, _ in PR
                     if (si <= T).mean() >= T_FLOOR and h[si <= T].mean() < 0.5]
            fails_v4 = [q for q, si, h, _, _ in PR if (si <= T).sum() > 0 and h[si <= T].mean() < 0.5]
            if gauss[T] >= 0.5 and not fails_v4:
                ok_v4.append(T)
            if gauss[T] >= 0.5 and not fails:
                ok.append(T)
            else:
                f0 = min(fails, key=lambda x: x[2]) if fails else None
                print(f"      T {T:.1f} fails: Gaussian recovery {gauss[T]:.2f}" +
                      (f"; worst conditional q {f0[0]:.4f} (set {f0[1]} of 20000) recovery {f0[2]:.2f}" if f0 else ""))
        T18[fam] = (max(ok), max(ok_v4))
        # v6: the same v5 rule with both conditions scored by median g (no print here; section 19)
        gm = dict((round(s_, 1), r_) for s_, r_ in REC15M[fam])
        okm, FAILM[fam] = [], []
        for T in np.round(np.arange(0.4, 3.01, 0.1), 1):
            fm = [(q, (si <= T).sum(), hm[si <= T].mean()) for q, si, h, _, hm in PR
                  if (si <= T).mean() >= T_FLOOR and hm[si <= T].mean() < 0.5]
            if gm[T] >= 0.5 and not fm:
                okm.append(T)
            else:
                FAILM[fam].append((T, gm[T], min(fm, key=lambda x: x[2]) if fm else None))
        T18M[fam] = max(okm)
        print(f"   {fam} T at this seed: {max(ok):.1f} pt (floor rule), {max(ok_v4):.1f} pt (v4 rule, any non-empty set)")
    if ARGS.t_only:
        for fam in T18:
            OUT.write(f"TSEED {ARGS.seed} {fam} {T18[fam][0]:.1f} {T18[fam][1]:.1f}\n")
            OUT.write(f"TMSEED {ARGS.seed} {fam} {T18M[fam]:.1f}\n")
        OUT.flush()
        sys.exit(0)
    # the other nine seeds: the whole script at that seed (so section 15's Gaussian rows are that seed's too)
    procs = {sd: subprocess.Popen([sys.executable, os.path.abspath(__file__), "--seed", str(sd), "--t-only"],
                                  stdout=subprocess.PIPE, text=True) for sd in T_SEEDS[1:]}
    TS = {(ARGS.seed, fam): T18[fam] for fam in T18}
    TSM = {(ARGS.seed, fam): T18M[fam] for fam in T18M}
    for sd, pr in procs.items():
        out, _ = pr.communicate()
        assert pr.returncode == 0, f"seed {sd} failed"
        for line in out.split("\n"):
            if line.startswith("TSEED "):
                _, s_, fam, tf, t4 = line.split()
                TS[int(s_), fam] = (float(tf), float(t4))
            elif line.startswith("TMSEED "):
                _, s_, fam, tm = line.split()
                TSM[int(s_), fam] = float(tm)
    print(f"   label threshold T per seed (seeds {' / '.join(str(x) for x in T_SEEDS)}), floor rule P(s_int <= T | q) >= {T_FLOOR}:")
    TFIN = {}
    for fam in T18:
        tf = [TS[sd, fam][0] for sd in T_SEEDS]; t4 = [TS[sd, fam][1] for sd in T_SEEDS]
        TFIN[fam] = min(tf)
        print(f"      {fam} floor rule: {' / '.join(f'{x:.1f}' for x in tf)} (range {min(tf):.1f}-{max(tf):.1f}); "
              f"v4 rule: {' / '.join(f'{x:.1f}' for x in t4)} (range {min(t4):.1f}-{max(t4):.1f})")
    for fam, m, k, top, ext in FAM18:
        T = TFIN[fam]
        print(f"   {fam} label threshold T = {T:.1f} pt, the minimum over the ten seeds (Gaussian recovery at T {GAUSS[fam][T]:.2f}, design seed)")
        nan = float('nan')
        for q, si, h, hx, hm in PRS[fam]:
            if q in NAMED_Q:
                sel = si <= T; band = (si >= 1.0) & (si <= T); above = si > T
                print(f"      q {q:.2f}: P(s_int <= T) {sel.mean():.2f}; recovery | s_int <= T {h[sel].mean() if sel.any() else nan:.2f} "
                      f"(median g {hm[sel].mean() if sel.any() else nan:.2f}; set {sel.sum()}); | 1.0 <= s_int <= T: n = 4 "
                      f"{h[band].mean() if band.any() else nan:.2f}, extension {hx[band].mean() if band.any() else nan:.2f} (set {band.sum()}); "
                      f"| s_int > T: n = 4 {h[above].mean() if above.any() else nan:.2f}, extension {hx[above].mean() if above.any() else nan:.2f} "
                      f"(set {above.sum()})")
        if fam == "5M":
            print(f"   check, 5M recovery | s_int <= {T:.1f} at q 0.02 / 0.05 / 0.1: " + " / ".join(
                f"{h[si <= T].mean():.2f}" for q, si, h, _, _ in PRS[fam] if q in (0.02, 0.05, 0.1)))
        else:
            print("   check, 350k unconditional recovery at q 0.33 / 0.5: " + " / ".join(
                f"{h.mean():.2f}" for q, si, h, _, _ in PRS[fam] if q in (0.33, 0.5)))

    # ---------------------------------------------------------------- v5 sections (fixer v5), fresh draws, printed last
    print("18b. recovery by mean g and by median g (median of the n = 4 paired g_s), jump 5.4 pt, within-mode sd 0.3 pt:")

    def rec2(m, k, top, reps=20000, gauss_sigma=None, q=None, shared=False, T=None):
        eff = np.zeros(m); eff[:k] = 1.0
        if gauss_sigma is None:
            lr = rng.random((reps, 4)) < q
            lc = np.broadcast_to(lr[:, None, :], (reps, m, 4)) if shared else rng.random((reps, m, 4)) < q
            r = -JUMP * lr + rng.normal(size=(reps, 4)) * WSD
            c = -JUMP * lc + rng.normal(size=(reps, m, 4)) * WSD + eff[None, :, None]
        else:
            r = rng.normal(size=(reps, 4)) * gauss_sigma
            c = rng.normal(size=(reps, m, 4)) * gauss_sigma + eff[None, :, None]
        res = c - c.mean(2, keepdims=True) - c.mean(1, keepdims=True) + c.mean((1, 2), keepdims=True)
        s_int = np.sqrt((res ** 2).sum((1, 2)) / ((m - 1) * 3))
        g = c - r[:, None, :]
        hit = lambda score: np.all([(np.argsort(-score, 1)[:, :top] == i).any(1) for i in range(k)], 0)
        hmn, hmd = hit(g.mean(2)), hit(np.median(g, 2))
        sel = s_int <= T if T is not None else np.ones(reps, bool)
        nan = float('nan')
        return hmn.mean(), hmd.mean(), (hmn[sel].mean() if sel.any() else nan), (hmd[sel].mean() if sel.any() else nan), sel.sum()

    for fam, m, k, top, ext in FAM18:
        T = TFIN[fam]
        print(f"   {fam}: m {m}, {k} true +1 pt, top {top}; mean g / median g")
        print("      Gaussian: " + "; ".join(f"sigma {gs}: {a:.2f} / {b:.2f}" for gs in (0.6, 1.0, 1.3)
                                                for a, b, *_ in [rec2(m, k, top, gauss_sigma=gs)]))
        for q in (0.02, 0.05, 0.1, 0.2, 0.33, 0.5):
            a, b, ca, cb, n_ = rec2(m, k, top, q=q, T=T)
            print(f"      per-run q {q}: {a:.2f} / {b:.2f}; | s_int <= T ({T:.1f} pt) {ca:.2f} / {cb:.2f} (set {n_})")
        print("      seed-shared: " + "; ".join(f"q {q}: {a:.2f} / {b:.2f}" for q in (0.1, 0.33, 0.5)
                                                   for a, b, *_ in [rec2(m, k, top, q=q, shared=True)]))

    print("18c. mode readout on the 8 replica values (two-mode if the largest gap > 3x the pooled within-group sd, >= 2 each side):")

    def flag(x):
        xs = np.sort(x); gaps = np.diff(xs); i = np.argmax(gaps)
        lo, hi_ = xs[:i + 1], xs[i + 1:]
        if len(lo) < 2 or len(hi_) < 2:
            return False
        ps = np.sqrt(((lo - lo.mean()) ** 2).sum() + ((hi_ - hi_.mean()) ** 2).sum()) / np.sqrt(len(x) - 2)
        return gaps[i] > 3 * ps
    fg = np.mean([flag(rng.normal(size=8)) for _ in range(20000)])
    pw18 = [f"q {q}: {np.mean([flag(-JUMP * (rng.random(8) < q) + rng.normal(size=8) * WSD) for _ in range(20000)]):.3f}"
            for q in (0.02, 0.05, 0.1, 0.2, 0.33, 0.5)]
    print(f"   false flag, Gaussian seeds (any sigma): {fg:.3f}; power, per-run two-mode: " + "; ".join(pw18))

    print("15a. family test, effect of one named cell detected with probability 0.5 / 0.8 (own-sd t on d = cell - placebo, n = 4, section-13 critical value):")
    for m in (11, 37):
        co = CR13[m, 4]
        out = []
        for sigma in (0.6, 1.5, 3.14):
            d0 = rng.normal(size=(40000, 4)) - rng.normal(size=(40000, 4))   # cell - placebo at zero effect, sigma units
            mu, se = d0.mean(1), d0.std(1, ddof=1) / 2
            grid = np.arange(0.0, 16.001, 0.05)
            pw = np.array([((mu + e / sigma) / se > co).mean() for e in grid])
            e50 = grid[np.argmax(pw >= 0.5)] if (pw >= 0.5).any() else nan
            e80 = grid[np.argmax(pw >= 0.8)] if (pw >= 0.8).any() else nan
            out.append(f"sigma {sigma}: {e50:.2f} / " + (f"{e80:.2f} pt" if e80 == e80 else "above the 16-pt grid edge"))
        print(f"   m = {m} (critical {co:.3f}): " + "; ".join(out))

    print("18d. Gaussian recovery at sigma = T (the T rule's condition (i)) by mean g and by median g (printed last):")
    for fam, m, k, top, ext in FAM18:
        T = TFIN[fam]
        a, b, *_ = rec2(m, k, top, gauss_sigma=T)
        print(f"   {fam} (T {T:.1f} pt): mean g {a:.2f}; median g {b:.2f}")

    # ---------------------------------------------------------------- v6 section (experiment-designer), no new draws
    print("19. median g as the ranking statistic (v5 rules unchanged; scores from the draws of sections 8, 15, 16, 18):")
    TMED = {}
    for fam, m, k, top, ext in FAM18:
        tm = [TSM[sd, fam] for sd in T_SEEDS]
        TMED[fam] = T = min(tm)
        print(f"   19a. {fam} Gaussian recovery by median g, section-15 grid (design seed): " +
              ", ".join(f"{s_:.1f}:{r_:.2f}" for s_, r_ in REC15M[fam]))
        print(f"      {fam} T by median g per seed ({' / '.join(str(x) for x in T_SEEDS)}): {' / '.join(f'{x:.1f}' for x in tm)} "
              f"(range {min(tm):.1f}-{max(tm):.1f}); T = {T:.1f} pt (mean-g T {TFIN[fam]:.1f} pt)")
        gm = dict((round(s_, 1), r_) for s_, r_ in REC15M[fam])
        print(f"      design seed: median-g Gaussian recovery at T {gm[T]:.2f} (mean g {GAUSS[fam][T]:.2f}); failing T in 0.4-3.0:")
        for Tf, gr, f0 in FAILM[fam]:
            if Tf <= T18M[fam] + 0.6:
                print(f"         T {Tf:.1f}: Gaussian {gr:.2f}" + (f"; worst conditional q {f0[0]:.4f} (set {f0[1]} of 20000) recovery {f0[2]:.2f}" if f0 else ""))
        print(f"   19b. {fam} at T = {T:.1f} pt, per-run mode, median g (n = 4 / [DK16] extension by median g):")
        for q, si, h, hx, hm in PRS[fam]:
            if q in NAMED_Q:
                hmx = PRX[fam, q]
                sel = si <= T; band = (si >= 1.0) & (si <= T); above = si > T
                f = lambda a, s_: f"{a[s_].mean():.2f}" if s_.any() else "nan"
                print(f"      q {q:.2f}: P(s_int <= T) {sel.mean():.2f}; unconditional {hm.mean():.2f} / {hmx.mean():.2f}; | s_int <= T {f(hm, sel)} "
                      f"(set {sel.sum()}); | 1.0 <= s_int <= T {f(hm, band)} / {f(hmx, band)} (set {band.sum()}); "
                      f"| s_int > T {f(hm, above)} / {f(hmx, above)} (set {above.sum()})")
        print("      seed-shared, median g n = 4 / extension: " + "; ".join(f"q {q}: {SHM[fam, q][0]:.2f} / {SHM[fam, q][1]:.2f}" for q in NAMED_Q))
    print("   19c. section 16 by median g (Gaussian, rho = 0): n = 4 | extension (4-seed median selects, 8-seed median orders) | n = 6")
    for fam, sigma, a, b, c6 in EXT16M:
        print(f"      {fam} sigma {sigma}: {a:.2f} | {b:.2f} | {c6:.2f}")
    print("   19d. rank-move null flags, primary and companion both ranked by median g (sections 8 and 15 draws):")
    for (m, rr), row in RMM.items():
        print(f"      m = {m}, r = {rr}: " + ", ".join(f"T {T}: {c:.1f}" for T, c in row))
    for m in (11, 37):
        out = []
        for rr in (0.5, 0.7, 0.9, 0.95):
            okT = [(T, c) for T, c in RMM[m, rr] if c <= 1.0]
            out.append(f"r >= {rr}: " + (f"T {okT[0][0]} ({okT[0][1]:.1f})" if okT else "no grid T"))
        print(f"      rule (smallest grid T with null count <= 1.0 at the band's lower edge), m = {m}: " + "; ".join(out))
    # v7 (fixer v6, 2026-09-28, STUDY arbiter v6 fix B2): the design-seed T at other probability floors, the
    # unchanged rule re-evaluated on the stored section-15 / section-18 recovery (zero new random numbers).
    print("   19e. design-seed T by the floor rule at other probability floors (same draws; floor 0.01 is the rule):")
    for fam, m, k, top, ext in FAM18:
        gm = dict((round(s_, 1), r_) for s_, r_ in REC15M[fam])
        row = []
        for fl in (0.005, 0.01, 0.02, 0.05):
            tt = []
            for idx, gg in ((4, gm), (2, GAUSS[fam])):   # 4: median-g recovery, 2: mean-g recovery
                okf = [T for T in np.round(np.arange(0.4, 3.01, 0.1), 1)
                       if gg[T] >= 0.5 and not [1 for x in PRS[fam] if (x[1] <= T).mean() >= fl and x[idx][x[1] <= T].mean() < 0.5]]
                tt.append(max(okf))
            if fl == T_FLOOR:
                assert (tt[0], tt[1]) == (T18M[fam], T18[fam][0]), "19e floor 0.01 must equal the rule's design-seed T"
            row.append(f"floor {fl}: median g {tt[0]:.1f} (mean g {tt[1]:.1f})")
        print(f"      {fam}: " + "; ".join(row) + " pt")
