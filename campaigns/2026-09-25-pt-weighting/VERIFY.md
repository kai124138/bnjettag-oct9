# VERIFY — 2026-09-25-pt-weighting

Every number below was recomputed in this session (2026-09-26, results-analyst) from the named
artifact with the command shown. Labels: metric · split · n · status. The held-out split is
the 26-file validation archive (ROC-test), n = 260,000, macro one-vs-rest AUC over g/q/W/Z/t;
"validation" means each seed's internal 20 % split of the train archive, n = 124,000. The two
are never compared with each other. Configuration for every arm: input set l1x3, N = 8, W1A8,
101-epoch schedule with early stopping (patience 15), seeds 1–8.

**Status of this verification.** The three arms, seeds 1–8 and the cap/bin settings were
fixed before launch (log entry 2026-09-25). The primary metric, the per-seed comparison rule, the
falsifier and the pT-sextile analysis were written after the results were in (log entry
2026-09-26 and the STUDY.md stub; newton flagged this on 2026-09-26, flag 8). This VERIFY.md
therefore confirms that the numbers are the numbers the arrays give and that the intervals are
computed as stated. It does not certify a pre-registered test, and outward text must say so.

## Recompute

Arrays: `research/bnjettag/roc-results/ptw-n8/{BASE,PTW5,PTWNC}-s{1..8}.npz`, keys
`y (260000, 5) float32 one-hot`, `score (260000, 5) float32 softmax`, `j_pt (260000,) float32 GeV`,
`meta` (JSON string). Reference: `research/bnjettag/roc-results/r14/n8/W1A8-s{1,2,3}.npz`.
`y` is byte-equal and `j_pt` row-equal across all 24 files and the three r14 files (asserted in
the script); class counts g/q/W/Z/t = 52,404 / 50,468 / 52,235 / 52,298 / 52,595.

Run from the lab root with the script saved as `ptw_verify.py` (it is reproduced verbatim
below so a reviewer can rerun it):

```
uv run --with numpy,scikit-learn python ptw_verify.py
```

```python
#!/usr/bin/env python
"""Recompute every pt-weighting N8 number from the .npz arrays (VERIFY.md, 2026-09-26).
Run from the lab root: uv run --with numpy,scikit-learn python ptw_verify.py
"""
import json, sys
import numpy as np
from scipy import stats
from sklearn.metrics import roc_auc_score

ROOT = "research/bnjettag/roc-results"
ARMS = ["BASE", "PTW5", "PTWNC"]
SEEDS = list(range(1, 9))
CLS = ["g", "q", "W", "Z", "t"]
T975 = stats.t.ppf(0.975, df=7)


def load(path):
    d = np.load(path)
    assert d.files == ["y", "score", "j_pt", "meta"], d.files
    y, s, pt = d["y"], d["score"], d["j_pt"]
    assert y.shape == (260000, 5) and s.shape == (260000, 5) and pt.shape == (260000,), (y.shape, s.shape, pt.shape)
    assert np.all(y.sum(1) == 1.0)                       # one-hot
    return y, s, pt


def macro(y, s):
    return roc_auc_score(y, s, multi_class="ovr", average="macro")


def paired(a, b):
    """b - a per seed: mean, sd, 95 % t-interval (df 7), count of seeds with b<a."""
    d = np.asarray(b) - np.asarray(a)
    m, sd = d.mean(), d.std(ddof=1)
    h = T975 * sd / np.sqrt(len(d))
    return dict(mean=m, sd=sd, lo=m - h, hi=m + h, lower=int((d < 0).sum()), n=len(d))


# ---- load all 24, assert the shared split -------------------------------------------------
Y, S, PT = {}, {}, {}
y0 = pt0 = None
for arm in ARMS:
    for sd in SEEDS:
        y, s, pt = load(f"{ROOT}/ptw-n8/{arm}-s{sd}.npz")
        if y0 is None:
            y0, pt0 = y, pt
        assert y.tobytes() == y0.tobytes(), f"y differs {arm}-s{sd}"
        assert pt.tobytes() == pt0.tobytes(), f"j_pt differs {arm}-s{sd}"
        Y[(arm, sd)], S[(arm, sd)], PT[(arm, sd)] = y, s, pt
print("split check: y byte-equal and j_pt row-equal across 24 files; n =", len(y0),
      "class counts", y0.sum(0).astype(int).tolist())

# ---- per-seed metrics --------------------------------------------------------------------
per = {}
for (arm, sd), s in S.items():
    per[(arm, sd)] = dict(
        macro=macro(y0, s),
        cls=[roc_auc_score(y0[:, c], s[:, c]) for c in range(5)],
        acc=float((s.argmax(1) == y0.argmax(1)).mean()),   # held-out top-1 accuracy
    )

print("\n## per seed (held-out, n=260000)")
print("| arm | seed | macro AUC | acc | " + " | ".join(f"AUC({c})" for c in CLS) + " |")
for arm in ARMS:
    for sd in SEEDS:
        p = per[(arm, sd)]
        print(f"| {arm} | {sd} | {p['macro']:.4f} | {p['acc']:.4f} | " + " | ".join(f"{v:.4f}" for v in p["cls"]) + " |")

print("\n## seed-averaged (mean ± sd ddof=1, 8 seeds)")
agg = {}
for arm in ARMS:
    m = np.array([per[(arm, sd)]["macro"] for sd in SEEDS])
    a = np.array([per[(arm, sd)]["acc"] for sd in SEEDS])
    c = np.array([per[(arm, sd)]["cls"] for sd in SEEDS])
    agg[arm] = dict(macro=m, acc=a, cls=c)
    print(f"| {arm} | macro {m.mean():.4f} ± {m.std(ddof=1):.4f} | acc {a.mean():.4f} ± {a.std(ddof=1):.4f} | "
          + " | ".join(f"{CLS[k]} {c[:, k].mean():.4f} ± {c[:, k].std(ddof=1):.4f}" for k in range(5)) + " |")
    best = max(SEEDS, key=lambda sd: per[(arm, sd)]["macro"])
    print(f"   best seed by held-out macro AUC: s{best} {per[(arm, best)]['macro']:.4f} acc {per[(arm, best)]['acc']:.4f}")

print("\n## paired vs BASE (mean [95% t, df 7], seeds lower)")
for arm in ["PTW5", "PTWNC"]:
    for key in ["macro", "acc"]:
        r = paired(agg["BASE"][key], agg[arm][key])
        print(f"{arm}-BASE {key}: {r['mean']:+.4f} ± {r['sd']/np.sqrt(8):.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}] {r['lower']}/8")
    for k in range(5):
        r = paired(agg["BASE"]["cls"][:, k], agg[arm]["cls"][:, k])
        print(f"{arm}-BASE held-out AUC({CLS[k]}): {r['mean']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}] {r['lower']}/8")
r = paired(agg["PTWNC"]["macro"], agg["PTW5"]["macro"])
print(f"PTW5-PTWNC macro: {r['mean']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}] {r['lower']}/8")

# ---- pT sextiles ---------------------------------------------------------------------------
q = np.quantile(pt0, [k / 6 for k in range(1, 6)])
edges = np.round(q)                       # store rounds to 1 GeV before binning
print("\n## pT sextiles (held-out j_pt): exact quantiles", np.round(q, 2).tolist(), "rounded edges", edges.tolist())
print("   j_pt min/max", float(pt0.min()), float(pt0.max()))
b = np.digitize(pt0, edges)               # bin i: edges[i-1] <= pt < edges[i]
counts = [int((b == i).sum()) for i in range(6)]
print("   bin counts", counts)
gfrac6 = float(y0[b == 5, 0].mean())
print(f"   bin 6 gluon fraction {gfrac6:.3f}")
binauc = {arm: np.array([[macro(y0[b == i], S[(arm, sd)][b == i]) for i in range(6)] for sd in SEEDS]) for arm in ARMS}
print("| bin | range | n | BASE | PTW5 | PTWNC | PTW5-BASE | PTWNC-BASE |")
lo_e = [float(pt0.min())] + edges.tolist()
hi_e = edges.tolist() + [float(pt0.max())]
for i in range(6):
    row = f"| {i+1} | {lo_e[i]:.0f}-{hi_e[i]:.0f} | {counts[i]} | "
    row += " | ".join(f"{binauc[a][:, i].mean():.4f} ± {binauc[a][:, i].std(ddof=1):.4f}" for a in ARMS)
    for a in ["PTW5", "PTWNC"]:
        r = paired(binauc["BASE"][:, i], binauc[a][:, i])
        row += f" | {r['mean']:+.4f} [{r['lo']:+.4f}, {r['hi']:+.4f}] {r['lower']}/8"
    print(row + " |")

# ---- r14 N=8 W1A8 reference (3 seeds) and the pull -------------------------------------------
ref = []
for sd in (1, 2, 3):
    d = np.load(f"{ROOT}/r14/n8/W1A8-s{sd}.npz")
    yy, ss = d["y"], d["score"]
    assert yy.shape == (260000, 5) and yy.tobytes() == y0.tobytes(), "r14 split differs"
    ref.append(macro(yy, ss))
ref = np.array(ref)
bm, bs = agg["BASE"]["macro"].mean(), agg["BASE"]["macro"].std(ddof=1)
rm, rs = ref.mean(), ref.std(ddof=1)
pull = (bm - rm) / np.sqrt(bs**2 / 8 + rs**2 / 3)
print(f"\n## r14 n8 W1A8 recomputed: per seed {np.round(ref, 4).tolist()} mean {rm:.4f} ± {rs:.4f} (3 seeds)")
print(f"   BASE (8 seeds) {bm:.4f} ± {bs:.4f}; difference {bm-rm:+.4f}; pull = (BASE - r14)/sqrt(sd_B^2/8 + sd_r^2/3) = {pull:+.2f}")

json.dump(dict(per={f"{a}-s{s}": v for (a, s), v in per.items()}, edges=edges.tolist(), counts=counts,
               ref=ref.tolist(), pull=float(pull)),
          open(sys.argv[1] if len(sys.argv) > 1 else "/dev/null", "w"), indent=1, default=float)
```

Validation accuracy (second command, same session) from
`research/bnjettag/roc-results/ptw-n8/internal-val/<ARM>-s<seed>.npz` (keys `label (124000,)`,
`pred (124000,)` argmax, `meta`), validation split: `acc = (label == pred).mean()`. Those files hold argmax
predictions, not scores, so validation AUC cannot be recomputed from them; the validation AUC
of each selected checkpoint below is quoted from its `train_meta.json` (`best_val_macro_auc`)
and labelled as quoted. The `meta` of `internal-val/BASE-s1.npz` records an eval-time recompute
of validation AUC against `train_meta` agreeing to 1.4e-6.

Comparison targets: the store's own table `research/bnjettag/roc-results/ptw-n8/roc_auc.md`
(2026-09-26) and the log claims in `research/.claude/memory/experiment-log.md` (2026-09-26
entry), copied into STUDY.md.

## Selection (as pre-registered in STUDY.md)

Rule: **STUDY.md pre-registers no selection rule** (its Design paragraph names arms, seeds and
the paired test only). What was applied is the rule implemented in `train.py` for every arm:
EarlyStopping on validation macro AUC (n = 124,000, internal split, unweighted) with patience
15 and restore-best-weights, so the single committed checkpoint per run, `model_best.keras`,
is the epoch with the highest validation macro AUC. There was one candidate per run, so no
choice among checkpoints was made and the held-out set was touched once, at the end
(`eval_ptw_n8.py`, log 2026-09-26). This is stated as "the rule as implemented", flagged
because it was not written down in STUDY.md before launch. `best epoch` is 0-based
(`train_meta.json`; the Keras log line is 1-based).

Selected checkpoints (`research/bnjettag/results/ptw-n8-20260925/checkpoints/<arm>-s<seed>/model_best.keras`,
W&B artifact `model-ptw-n8-0925-<arm>-s<seed>`):

| arm | seed | best epoch | validation macro AUC, n = 124,000, single seed (quoted, `train_meta.json`) | validation accuracy, n = 124,000, single seed (recomputed) | store `val acc` |
| --- | --- | --- | --- | --- | --- |
| BASE | s1 | 74 | 0.8725 | 0.6268 | 0.6268 ✓ |
| BASE | s2 | 72 | 0.8710 | 0.6222 | 0.6222 ✓ |
| BASE | s3 | 86 | 0.8704 | 0.6229 | 0.6229 ✓ |
| BASE | s4 | 63 | 0.8689 | 0.6222 | 0.6222 ✓ |
| BASE | s5 | 84 | 0.8709 | 0.6250 | 0.6250 ✓ |
| BASE | s6 | 92 | 0.8733 | 0.6264 | 0.6264 ✓ |
| BASE | s7 | 71 | 0.8716 | 0.6242 | 0.6242 ✓ |
| BASE | s8 | 59 | 0.8709 | 0.6236 | 0.6236 ✓ |
| PTW5 | s1 | 78 | 0.8605 | 0.6111 | 0.6111 ✓ |
| PTW5 | s2 | 39 | 0.8587 | 0.6055 | 0.6055 ✓ |
| PTW5 | s3 | 94 | 0.8635 | 0.6120 | 0.6120 ✓ |
| PTW5 | s4 | 49 | 0.8591 | 0.6028 | 0.6028 ✓ |
| PTW5 | s5 | 57 | 0.8590 | 0.6065 | 0.6065 ✓ |
| PTW5 | s6 | 67 | 0.8622 | 0.6094 | 0.6094 ✓ |
| PTW5 | s7 | 66 | 0.8618 | 0.6142 | 0.6142 ✓ |
| PTW5 | s8 | 55 | 0.8588 | 0.6048 | 0.6048 ✓ |
| PTWNC | s1 | 87 | 0.8596 | 0.6083 | 0.6083 ✓ |
| PTWNC | s2 | 50 | 0.8582 | 0.6039 | 0.6039 ✓ |
| PTWNC | s3 | 72 | 0.8595 | 0.6102 | 0.6102 ✓ |
| PTWNC | s4 | 77 | 0.8603 | 0.6058 | 0.6058 ✓ |
| PTWNC | s5 | 71 | 0.8545 | 0.6006 | 0.6006 ✓ |
| PTWNC | s6 | 62 | 0.8581 | 0.6031 | 0.6031 ✓ |
| PTWNC | s7 | 84 | 0.8612 | 0.6100 | 0.6100 ✓ |
| PTWNC | s8 | 98 | 0.8590 | 0.6033 | 0.6033 ✓ |

Validation accuracy seed-averaged (n = 124,000, 8 seeds, mean ± sd): BASE 0.6242 ± 0.0018,
PTW5 0.6083 ± 0.0040, PTWNC 0.6056 ± 0.0035; log claims 0.6242 / 0.0018, 0.6083 / 0.0040,
0.6056 / 0.0035 ✓ all six.

## Numbers

Per seed, held-out (ROC-test) split, n = 260,000, single seed each row. "store" is the macro
column of `roc_auc.md`; every one of the 24 macro values and 24 accuracies agrees to all four
printed decimals ✓.

| arm | seed | metric | split | n | value | artifact |
| --- | --- | --- | --- | --- | --- | --- |
| BASE | s1 | macro OvR AUC / accuracy | held-out | 260000 | 0.8718 / 0.6242 (store 0.8718 / 0.6242 ✓) | `ptw-n8/BASE-s1.npz` |
| BASE | s2 | macro OvR AUC / accuracy | held-out | 260000 | 0.8714 / 0.6229 (store 0.8714 / 0.6229 ✓) | `ptw-n8/BASE-s2.npz` |
| BASE | s3 | macro OvR AUC / accuracy | held-out | 260000 | 0.8713 / 0.6229 (store 0.8713 / 0.6229 ✓) | `ptw-n8/BASE-s3.npz` |
| BASE | s4 | macro OvR AUC / accuracy | held-out | 260000 | 0.8682 / 0.6196 (store 0.8682 / 0.6196 ✓) | `ptw-n8/BASE-s4.npz` |
| BASE | s5 | macro OvR AUC / accuracy | held-out | 260000 | 0.8713 / 0.6250 (store 0.8713 / 0.6250 ✓) | `ptw-n8/BASE-s5.npz` |
| BASE | s6 | macro OvR AUC / accuracy | held-out | 260000 | 0.8729 / 0.6260 (store 0.8729 / 0.6260 ✓) | `ptw-n8/BASE-s6.npz` |
| BASE | s7 | macro OvR AUC / accuracy | held-out | 260000 | 0.8709 / 0.6233 (store 0.8709 / 0.6233 ✓) | `ptw-n8/BASE-s7.npz` |
| BASE | s8 | macro OvR AUC / accuracy | held-out | 260000 | 0.8712 / 0.6233 (store 0.8712 / 0.6233 ✓) | `ptw-n8/BASE-s8.npz` |
| PTW5 | s1 | macro OvR AUC / accuracy | held-out | 260000 | 0.8591 / 0.6086 (store 0.8591 / 0.6086 ✓) | `ptw-n8/PTW5-s1.npz` |
| PTW5 | s2 | macro OvR AUC / accuracy | held-out | 260000 | 0.8592 / 0.6061 (store 0.8592 / 0.6061 ✓) | `ptw-n8/PTW5-s2.npz` |
| PTW5 | s3 | macro OvR AUC / accuracy | held-out | 260000 | 0.8641 / 0.6133 (store 0.8641 / 0.6133 ✓) | `ptw-n8/PTW5-s3.npz` |
| PTW5 | s4 | macro OvR AUC / accuracy | held-out | 260000 | 0.8587 / 0.6027 (store 0.8587 / 0.6027 ✓) | `ptw-n8/PTW5-s4.npz` |
| PTW5 | s5 | macro OvR AUC / accuracy | held-out | 260000 | 0.8591 / 0.6069 (store 0.8591 / 0.6069 ✓) | `ptw-n8/PTW5-s5.npz` |
| PTW5 | s6 | macro OvR AUC / accuracy | held-out | 260000 | 0.8615 / 0.6077 (store 0.8615 / 0.6077 ✓) | `ptw-n8/PTW5-s6.npz` |
| PTW5 | s7 | macro OvR AUC / accuracy | held-out | 260000 | 0.8612 / 0.6131 (store 0.8612 / 0.6131 ✓) | `ptw-n8/PTW5-s7.npz` |
| PTW5 | s8 | macro OvR AUC / accuracy | held-out | 260000 | 0.8593 / 0.6056 (store 0.8593 / 0.6056 ✓) | `ptw-n8/PTW5-s8.npz` |
| PTWNC | s1 | macro OvR AUC / accuracy | held-out | 260000 | 0.8583 / 0.6061 (store 0.8583 / 0.6061 ✓) | `ptw-n8/PTWNC-s1.npz` |
| PTWNC | s2 | macro OvR AUC / accuracy | held-out | 260000 | 0.8586 / 0.6035 (store 0.8586 / 0.6035 ✓) | `ptw-n8/PTWNC-s2.npz` |
| PTWNC | s3 | macro OvR AUC / accuracy | held-out | 260000 | 0.8605 / 0.6121 (store 0.8605 / 0.6121 ✓) | `ptw-n8/PTWNC-s3.npz` |
| PTWNC | s4 | macro OvR AUC / accuracy | held-out | 260000 | 0.8597 / 0.6044 (store 0.8597 / 0.6044 ✓) | `ptw-n8/PTWNC-s4.npz` |
| PTWNC | s5 | macro OvR AUC / accuracy | held-out | 260000 | 0.8544 / 0.6004 (store 0.8544 / 0.6004 ✓) | `ptw-n8/PTWNC-s5.npz` |
| PTWNC | s6 | macro OvR AUC / accuracy | held-out | 260000 | 0.8575 / 0.6020 (store 0.8575 / 0.6020 ✓) | `ptw-n8/PTWNC-s6.npz` |
| PTWNC | s7 | macro OvR AUC / accuracy | held-out | 260000 | 0.8608 / 0.6085 (store 0.8608 / 0.6085 ✓) | `ptw-n8/PTWNC-s7.npz` |
| PTWNC | s8 | macro OvR AUC / accuracy | held-out | 260000 | 0.8594 / 0.6032 (store 0.8594 / 0.6032 ✓) | `ptw-n8/PTWNC-s8.npz` |

Best single model by held-out macro AUC: BASE-s6 (0.8729, acc 0.6260; log ✓); best weighted:
PTW5-s3 (0.8641, held-out acc 0.6133; log ✓). These are single-seed numbers and are not the headline.

Seed-averaged (mean ± sample sd, ddof = 1), held-out split, n = 260,000, 8 seeds each:

| arm | metric · split · n | mean ± sd | seeds | claimed (log / STUDY / store) |
| --- | --- | --- | --- | --- |
| BASE | macro OvR AUC · held-out · 260000 | 0.8711 ± 0.0013 | 8 | 0.8711 ± 0.0013 ✓ |
| PTW5 | macro OvR AUC · held-out · 260000 | 0.8603 ± 0.0019 | 8 | 0.8603 ± 0.0019 ✓ |
| PTWNC | macro OvR AUC · held-out · 260000 | 0.8587 ± 0.0020 | 8 | 0.8587 ± 0.0020 ✓ |
| BASE | top-1 accuracy · held-out · 260000 | 0.6234 ± 0.0019 | 8 | 0.6234 ± 0.0019 ✓ |
| PTW5 | top-1 accuracy · held-out · 260000 | 0.6080 ± 0.0037 | 8 | 0.6080 ± 0.0037 ✓ |
| PTWNC | top-1 accuracy · held-out · 260000 | 0.6050 ± 0.0038 | 8 | 0.6050 ± 0.0038 ✓ |

Eight seeds is enough here: the smallest headline gap (0.0108) is about six seed sd of the
noisier arm, so no additional seeds are needed to resolve it. The seed sd of BASE (0.0013) is
the value the metrics convention quotes for N = 8 W1A8.

## Gaps

Paired by seed (same seed, same held-out split), mean difference with the 95 % t-interval
(df = 7) and the count of seeds on which the weighted arm is lower. Metric: held-out macro
OvR AUC on the held-out split unless labelled acc; n = 260,000; 8 seeds.

| comparison (held-out, n = 260,000 unless stated) | mean Δ | 95 % interval (paired, df) | seeds lower / total | verdict |
| --- | --- | --- | --- | --- |
| PTW5 − BASE, held-out macro AUC | −0.0108 | [−0.0124, −0.0093] (df 7) | 8 / 8 | lower; claimed −0.0108 [−0.0124, −0.0093] 8/8 ✓ |
| PTWNC − BASE, held-out macro AUC | −0.0125 | [−0.0148, −0.0101] (df 7) | 8 / 8 | lower; claimed −0.0125 [−0.0148, −0.0101] 8/8 ✓ |
| PTW5 − BASE, held-out accuracy | −0.0154 | [−0.0183, −0.0125] (df 7) | 8 / 8 | lower; claimed −0.0154 [−0.0183, −0.0125] 8/8 ✓ |
| PTWNC − BASE, held-out accuracy | −0.0184 | [−0.0223, −0.0145] (df 7) | 8 / 8 | lower; claimed −0.0184 [−0.0223, −0.0145] 8/8 ✓ |
| PTW5 − PTWNC, held-out macro AUC | +0.0016 | [−0.0002, +0.0034] (df 7) | 2 / 8 (PTW5 lower) | flat: interval covers zero; claimed +0.0016 [−0.0002, +0.0034] ✓ |
| PTW5 − BASE, validation accuracy (n = 124,000) | −0.0159 | [−0.0189, −0.0129] (df 7) | 8 / 8 | lower; store −0.0159 [−0.0189, −0.0129] ✓ |
| PTWNC − BASE, validation accuracy (n = 124,000) | −0.0185 | [−0.0220, −0.0151] (df 7) | 8 / 8 | lower; store −0.0185 [−0.0220, −0.0151] ✓ |

Both weighted arms are lower than BASE on every seed, and each interval lies entirely below
zero at a distance of several seed sd: the loss is resolvable at the data we have. The cap-5
versus no-cap difference is not resolvable at eight seeds.

## Per-class and binned

Per-class one-vs-rest AUC, held-out split, n = 260,000, mean ± sd over 8 seeds, with the
paired difference to BASE (95 % t-interval, df 7; seeds lower). Store values agree on every entry ✓.

| class | BASE (held-out, n = 260000) | PTW5 | PTWNC | PTW5 − BASE | PTWNC − BASE |
| --- | --- | --- | --- | --- | --- |
| g | 0.8131 ± 0.0032 | 0.7850 ± 0.0037 | 0.7852 ± 0.0040 | −0.0282 [−0.0312, −0.0251] 8/8 | −0.0280 [−0.0330, −0.0229] 8/8 |
| q | 0.8635 ± 0.0017 | 0.8577 ± 0.0030 | 0.8564 ± 0.0020 | −0.0059 [−0.0080, −0.0038] 8/8 | −0.0072 [−0.0096, −0.0047] 8/8 |
| W | 0.8926 ± 0.0011 | 0.8836 ± 0.0024 | 0.8809 ± 0.0033 | −0.0090 [−0.0113, −0.0068] 8/8 | −0.0117 [−0.0149, −0.0085] 8/8 |
| Z | 0.8741 ± 0.0013 | 0.8680 ± 0.0024 | 0.8648 ± 0.0031 | −0.0062 [−0.0085, −0.0038] 8/8 | −0.0094 [−0.0125, −0.0062] 8/8 |
| t | 0.9122 ± 0.0010 | 0.9072 ± 0.0012 | 0.9061 ± 0.0020 | −0.0050 [−0.0061, −0.0039] 8/8 | −0.0062 [−0.0080, −0.0043] 8/8 |

Every class is lower on 8/8 seeds for both arms; gluon is the largest loss (−0.0282 and
−0.0280; log says "g largest (−0.028)" ✓). No class is under 0.7.

**pT sextiles.** Edges are the exact held-out sextiles of `j_pt` — 979.98, 1005.80, 1022.11,
1045.77, 1105.85 GeV — rounded to 1 GeV before binning (980, 1006, 1022, 1046, 1106), as the
store did; the bin counts then reproduce the store's exactly (43,352 / 43,812 / 42,580 /
43,929 / 43,051 / 43,276). `j_pt` spans 159 to 3157 GeV. Bin 6 is 59.5 % gluon (25,761 of
43,276; STUDY says "60 % gluon" ✓). Values are held-out macro OvR AUC inside the bin, mean ± sd
over 8 seeds; differences are paired (95 % t-interval, df 7; seeds lower).

| bin | pT (GeV) | n (held-out) | BASE | PTW5 | PTWNC | PTW5 − BASE | PTWNC − BASE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 159–980 | 43352 | 0.8597 ± 0.0024 | 0.8644 ± 0.0028 | 0.8634 ± 0.0019 | +0.0047 [+0.0020, +0.0074] 0/8 | +0.0037 [+0.0004, +0.0069] 2/8 |
| 2 | 980–1006 | 43812 | 0.8810 ± 0.0013 | 0.8800 ± 0.0019 | 0.8790 ± 0.0015 | −0.0010 [−0.0027, +0.0007] 6/8 | −0.0020 [−0.0039, −0.0001] 6/8 |
| 3 | 1006–1022 | 42580 | 0.8910 ± 0.0015 | 0.8873 ± 0.0023 | 0.8858 ± 0.0019 | −0.0037 [−0.0059, −0.0015] 7/8 | −0.0052 [−0.0074, −0.0029] 8/8 |
| 4 | 1022–1046 | 43929 | 0.8935 ± 0.0010 | 0.8899 ± 0.0022 | 0.8880 ± 0.0019 | −0.0035 [−0.0055, −0.0016] 7/8 | −0.0055 [−0.0075, −0.0036] 8/8 |
| 5 | 1046–1106 | 43051 | 0.8843 ± 0.0012 | 0.8845 ± 0.0015 | 0.8823 ± 0.0027 | +0.0003 [−0.0012, +0.0017] 4/8 | −0.0020 [−0.0043, +0.0003] 6/8 |
| 6 | 1106–3157 | 43276 | 0.8106 ± 0.0047 | 0.8271 ± 0.0028 | 0.8272 ± 0.0042 | +0.0165 [+0.0114, +0.0215] 0/8 | +0.0165 [+0.0109, +0.0222] 0/8 |

Bin-6 paired difference (95 % t-interval, df 7): PTW5 − BASE +0.0165 [+0.0114, +0.0215], higher on 8/8 seeds; PTWNC −
BASE +0.0165 [+0.0109, +0.0222], higher on 8/8 (log: +0.0165, 8/8, both arms ✓; store's six
per-bin differences for both arms ✓). Two caveats on how this is read. First, the sextile
analysis was chosen after the results, and bin 6 is the largest of six binned comparisons, so
its interval is not corrected for that selection; the effect is about seven seed sd wide and
would survive a Bonferroni factor of 6, but the point stands. Second, bin 1 (below 980 GeV)
also gains for both arms — +0.0047 [+0.0020, +0.0074] on 8/8 seeds for PTW5, +0.0037
[+0.0004, +0.0069] on 6/8 for PTWNC — so the tail gain is not the only gain. The central bins
2–4 lose, bin 5 is flat.

## Cost and hardware

Not applicable: no eBOP remeasurement and no synthesis were part of this campaign (log
2026-09-25: "No ROC/test eval or synthesis" at launch; the 2026-09-26 eval added held-out ROC
only). The weighting changes the loss, not the architecture, so the parameter count (18,657)
is the same for every arm; no hardware claim is made or checked here.

## Consistency with the record

Baseline against `research/bnjettag/roc-results/r14/n8/W1A8-s{1,2,3}.npz` (round 14, l1x3, N = 8,
W1A8, held-out, n = 260,000, three seeds), recomputed in the same script: per seed 0.8719,
0.8694, 0.8724; mean 0.8712 ± 0.0016 (ddof = 1). The log's quoted 0.8712 ± 0.0016 ✓.

BASE (8 seeds) 0.8711 ± 0.0013 vs r14 (3 seeds) 0.8712 ± 0.0016: difference −0.0001; pull
defined as (BASE − r14) / sqrt(sd_BASE² / 8 + sd_r14² / 3) = −0.09. The baseline reproduces the
recorded value well inside the seed spread. The two campaigns share the split (`y`
byte-equal, asserted) and the configuration (`gen_ptw.py` asserts that only name, pt_weights
and jit_compile differ from `r14-l1x3-n8-w1a8`); the r14 runs used jit_compile on, this
campaign off, which the pull says did not matter at this precision.

## Verdicts

Claims are those in STUDY.md's Result and Interpretation paragraphs and its falsifier. Every
numeric claim was copied into STUDY.md from the log, so "✓" means the arrays give that number,
not that the claim was pre-registered (see the status note at the top).

| STUDY claim | verdict (held-out, n = 260,000 unless stated) | evidence line |
| --- | --- | --- |
| Question: does pT reweighting improve held-out macro AUC? | falsified for both arms: PTW5 −0.0108 [−0.0124, −0.0093], PTWNC −0.0125 [−0.0148, −0.0101], lower on 8/8 seeds each | Gaps table, first two rows |
| Question: does it improve accuracy? | falsified: PTW5 −0.0154 [−0.0183, −0.0125], PTWNC −0.0184 [−0.0223, −0.0145], lower on 8/8; validation accuracy agrees | Gaps table rows 3–4, 6–7 |
| BASE 0.8711 ± 0.0013, PTW5 0.8603 ± 0.0019, PTWNC 0.8587 ± 0.0020 (held-out, seed-averaged) | supported ✓ all six numbers | Seed-averaged table |
| Falsifier (post hoc): "PTW arms not lower on 8/8 seeds" | not triggered: both arms lower on 8/8 seeds for held-out AUC and for held-out accuracy. Written after the results, so this is a consistency check, not a test | Gaps table |
| Per-class AUC lower 8/8, gluon largest (−0.028) | supported ✓: all five classes lower 8/8 for both arms; g −0.0282 / −0.0280 | Per-class table |
| "Only the highest-pT sextile (≥1106 GeV, 60 % gluon) gains, +0.0165 on 8/8" | number supported ✓ (+0.0165 [+0.0114, +0.0215] and [+0.0109, +0.0222], 8/8 higher, 59.5 % gluon); the word "only" is **not supported**: bin 1 (< 980 GeV) also gains, +0.0047 [+0.0020, +0.0074] 8/8 higher for PTW5 and +0.0037 [+0.0004, +0.0069] 6/8 for PTWNC. Post-hoc binning; largest of six | Sextile table, bins 1 and 6 |
| Interpretation: "the gain is confined to the tail" | not supported as worded, same evidence; REPORT.md should say "gains at both ends of the pT range, losses in the centre" or drop the word | Sextile table |
| BASE agrees with r14 n8 W1A8 3-seed 0.8712 ± 0.0016 | supported ✓: pull −0.09 | Consistency section |
| Design: 8 seeds can resolve the gap | supported: smallest headline gap is about six sd of the noisier arm; PTW5 vs PTWNC (+0.0016 [−0.0002, +0.0034]) is not resolvable at 8 seeds and is reported as flat | Gaps table row 5 |

Nothing in the arrays contradicts the store's `roc_auc.md`; every number checked against it
agrees to the printed precision. The one finding for REPORT.md is the wording "only" / "confined
to the tail", which the bin-1 result does not support.

What was not verified here: the pod-side claim that `train_meta` matches the pod logs 24/24
(RUN.md records it from the log; the pod logs were read for epochs and run ids, not for the
validation AUC lines); the eBOP and hardware rows (not applicable); the public-repo §4.5
numbers (outside this campaign directory).

## Sanity

Run 2026-09-26 after the fixes noted below:

```
$ python3 tools/verify_check.py local/2026-09-25-pt-weighting/VERIFY.md
== local/2026-09-25-pt-weighting/VERIFY.md
   ok

worst grade: C
```

First run raised A flags that were all checker-regex hits, not numeric problems: "top-1" and a
bare seed digit in a table row were read as a perfect score (rows now say "accuracy" and
"s1"), the script's `acc=` and per-class print lines lacked a split word (labelled, script
rerun, output identical), prose lines with "paired" or "vs" lacked the word "interval" or "sd"
(the checker does not count `[+a, +b]` as an interval), and the Gaps and Verdicts headers
lacked `n`. No number changed.
