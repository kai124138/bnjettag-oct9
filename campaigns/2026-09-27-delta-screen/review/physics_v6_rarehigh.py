# physics v6 check: per-run two-mode seeds with q > 0.5 (a rare HIGH mode, the archived shape 67.18/72.64/67.21),
# same model as screen_null.py twomode(): jump 5.4 pt, within-mode sd 0.3 pt, n = 4, replica shared.
import numpy as np
rng = np.random.default_rng(606)
J, W = 5.4, 0.3
def run(m, k, top, q, T, reps=20000):
    eff = np.zeros(m); eff[:k] = 1.0
    lr = rng.random((reps, 4)) < q; lc = rng.random((reps, m, 4)) < q
    r = -J*lr + rng.normal(size=(reps, 4))*W
    c = -J*lc + rng.normal(size=(reps, m, 4))*W + eff[None, :, None]
    res = c - c.mean(2, keepdims=True) - c.mean(1, keepdims=True) + c.mean((1, 2), keepdims=True)
    si = np.sqrt((res**2).sum((1, 2))/((m-1)*3))
    g = c - r[:, None, :]
    hit = lambda s: np.all([(np.argsort(-s, 1)[:, :top] == i).any(1) for i in range(k)], 0)
    hmd, hmn = hit(np.median(g, 2)), hit(g.mean(2))
    sel = si <= T
    f = lambda a: f"{a[sel].mean():.2f}" if sel.sum() else "nan"
    return (f"q {q:.2f} (P(high) {1-q:.2f}): per-run sd {np.sqrt(J*J*q*(1-q)+W*W):.2f}; median s_int {np.median(si):.2f}; "
            f"uncond median/mean {hmd.mean():.2f}/{hmn.mean():.2f}; P(s_int<=T) {sel.mean():.3f}; | s_int<=T median/mean {f(hmd)}/{f(hmn)} (set {sel.sum()})")
for fam, m, k, top, T in (("5M", 37, 3, 12, 1.2), ("350k", 11, 1, 3, 2.1)):
    print(fam, "T", T)
    for q in (0.5, 0.67, 0.8, 0.9, 0.95, 0.98):
        print("  ", run(m, k, top, q, T))
