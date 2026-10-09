# ROUND 15 GAMMA sm6i0 (l1x3, N=8) - ROC-test AUC (W1A8 + softmax_out grid sm6i0)
#
# metric : ROC-test macro one-vs-rest AUC on the held-out val split
#          (sklearn roc_auc_score per class; macro = unweighted mean) — NOT val AUC
# n_eval : 260000 jets    era : 2  (NEVER compare to era-1 numbers)
# source : recomputed from roc-results/r15-gamma/sm6i0/*.npz (y, score)
# gen    : 2026-08-23 by code/hgq2/roc_final.py

## Per-seed

| run | variant | w/a bits | seed | AUC(g) | AUC(q) | AUC(W) | AUC(Z) | AUC(t) | macro | n |
|---|---|---|---|---|---|---|---|---|---|
| W1A8-s1 | w1a8 | 1/8 | 1 | 0.8096 | 0.8601 | 0.8896 | 0.8722 | 0.9114 | **0.8686** | 260000 |
| W1A8-s2 | w1a8 | 1/8 | 2 | 0.8145 | 0.8638 | 0.8925 | 0.8751 | 0.9123 | **0.8716** | 260000 |
| W1A8-s3 | w1a8 | 1/8 | 3 | 0.8161 | 0.8610 | 0.8917 | 0.8746 | 0.9146 | **0.8716** | 260000 |

## Seed-averaged (mean ± sample std over available seeds)

| variant | w/a bits | seeds | AUC(g) | AUC(q) | AUC(W) | AUC(Z) | AUC(t) | macro | n_seed |
|---|---|---|---|---|---|---|---|---|
| w1a8 | 1/8 | 1,2,3 | 0.8134±0.0034 | 0.8616±0.0019 | 0.8912±0.0015 | 0.8740±0.0016 | 0.9128±0.0016 | **0.8706±0.0017** | 3 |
