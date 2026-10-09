"""constructive v3: stage-2 seed extension of the top-k cells onto replica seeds 5-8 (already run).
Design arithmetic, seeded Monte Carlo, not a result. Model as rank_sim.py / screen_null.py: per-run
seed sd sigma, rho = 0, three true +1 pt cells among m. Ranking by mean g; the replica term is common
to every cell at seed s so it does not change the order; cells are drawn directly.
Metrics: P(all three true cells in the final top 12), mean number of true cells in the top 12."""
import numpy as np
rng = np.random.default_rng(20260927)

def sim(m, sigma, k=3, eff=1.0, top=12, ext=16, reps=20000, mix=None):
    d = np.zeros(m); d[:k] = eff
    if mix is None:
        x = rng.normal(size=(reps, m, 8)) * sigma
    else:
        q, jump, sd = mix
        x = (rng.random((reps, m, 8)) < q) * jump + rng.normal(size=(reps, m, 8)) * sd
    x = x + d[None, :, None]
    true = np.arange(k)
    def score(sel):
        return (sel[:, :, None] == true[None, None, :]).any(1)
    # A: one stage, n = 4
    a = np.argsort(-x[:, :, :4].mean(2), 1)[:, :top]
    # B: n = 4, then the top `ext` get seeds 5-8; final top 12 by 8-seed mean among the extended
    s1 = np.argsort(-x[:, :, :4].mean(2), 1)[:, :ext]
    m8 = np.take_along_axis(x[:, :, :8].mean(2), s1, 1)
    b = np.take_along_axis(s1, np.argsort(-m8, 1)[:, :top], 1)
    # C: uniform n = 6 (roughly the same run count as B at m = 40, ext = 16: 240 vs 224 cell runs)
    c = np.argsort(-x[:, :, :6].mean(2), 1)[:, :top]
    out = []
    for sel in (a, b, c):
        h = score(sel)
        out.append((h.all(1).mean(), h.sum(1).mean()))
    return out

for fam, m, ext in (("5M", 40, 16), ("350k", 12, 6)):
    top = 12 if m == 40 else 3
    k = 3 if m == 40 else 1
    print(f"{fam}: m {m}, {k} true +1 pt, final top {top}; A one-stage n4 | B n4 + top-{ext} to 8 seeds | C uniform n6")
    for sigma in (0.6, 1.0, 1.3, 1.5, 2.0, 3.14):
        r = sim(m, sigma, k=k, top=top, ext=ext)
        print(f"   sigma {sigma:4.2f}: P(all in top) {r[0][0]:.2f} | {r[1][0]:.2f} | {r[2][0]:.2f};   "
              f"E[true in top] {r[0][1]:.2f} | {r[1][1]:.2f} | {r[2][1]:.2f}")
    r = sim(m, 1.0, k=k, top=top, ext=ext, mix=(0.33, 5.4, 0.3))
    print(f"   two-mode q 0.33 (true cells +1 pt): P(all) {r[0][0]:.2f} | {r[1][0]:.2f} | {r[2][0]:.2f}")
print("extra cell runs: 5M B = 16 x 4 = 64 (32,000 run-epochs at H 500); 350k B = 6 x 4 = 24 (12,000); "
      "C = 2 extra seeds for every cell. Replica seeds 5-8 already run to epoch 500 ([DK2]).")
