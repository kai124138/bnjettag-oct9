# ROUND 15 GAMMA sm4i0 (l1x3, N=8) - ROC-test AUC (W1A8 + softmax_out grid sm4i0)
#
# metric : ROC-test macro one-vs-rest AUC on the held-out val split
#          (sklearn roc_auc_score per class; macro = unweighted mean) — NOT val AUC
# n_eval : 260000 jets    era : 2  (NEVER compare to era-1 numbers)
# source : recomputed from roc-results/r15-gamma/sm4i0/*.npz (y, score)
# gen    : 2026-08-23 by code/hgq2/roc_final.py

## Per-seed

| run | variant | w/a bits | seed | AUC(g) | AUC(q) | AUC(W) | AUC(Z) | AUC(t) | macro | n |
|---|---|---|---|---|---|---|---|---|---|
| W1A8-s1 | w1a8 | 1/8 | 1 | 0.8132 | 0.8613 | 0.8890 | 0.8720 | 0.9114 | **0.8694** | 260000 |
| W1A8-s2 | w1a8 | 1/8 | 2 | 0.8108 | 0.8632 | 0.8871 | 0.8714 | 0.9105 | **0.8686** | 260000 |
| W1A8-s3 | w1a8 | 1/8 | 3 | 0.8163 | 0.8631 | 0.8941 | 0.8753 | 0.9130 | **0.8723** | 260000 |

## Seed-averaged (mean ± sample std over available seeds)

| variant | w/a bits | seeds | AUC(g) | AUC(q) | AUC(W) | AUC(Z) | AUC(t) | macro | n_seed |
|---|---|---|---|---|---|---|---|---|
| w1a8 | 1/8 | 1,2,3 | 0.8134±0.0028 | 0.8625±0.0010 | 0.8901±0.0036 | 0.8729±0.0021 | 0.9116±0.0012 | **0.8701±0.0020** | 3 |
