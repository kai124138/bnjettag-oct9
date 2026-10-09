# Outputs v2 — Jev on method-note-corrected-v2.md (2 Jev calls; loop total 7 of 12)

## jev_check_methods (audit jv-7f5e96bd5a0e4258b04f371c88b56c85)
| rule | flawed v1 | corrected v1 | corrected v2 |
|---|---|---|---|
| selection | conflict 1.00 | consistent 1.00 | consistent 1.00 |
| uncertainty | conflict 0.94 | consistent 1.00 | consistent 1.00 |
| metrics | conflict 0.87 | consistent 0.60 | consistent 0.64 (missing 0.35) |
| comparability | missing 0.74 | missing 0.53 | consistent 0.70 |
| provenance | missing 0.90 | missing 0.93 | missing 0.95 |
| authority | missing 0.70 | missing 0.72 | missing 0.88 |

## jev_check_claims (audit jv-b9b743d9e6234390badca501c5614f96), threshold conf 0.8 heuristic
| id | source | choice | p(sup) | conf | >= 0.8 |
|---|---|---|---|---|---|
| a eBOPs on selected ckpt | quant L21-22 | supported | 0.94 | 0.92 | yes |
| b validation selection under budget | quant L31-32 | supported | 0.84 | 0.78 | no |
| c no final-epoch mix | quant L35-36 | supported | 0.59 | 0.45 | no |
| d ROC-test never for selection | metrics L17-20 | supported | 0.98 | 0.97 | yes |
| e eight seeds, gap < 0.005 | metrics L40-41 | supported | 0.52 | 0.35 | no |
| f paired t-interval, flat rule | metrics L43-45 | supported | 0.94 | 0.92 | yes |
| g matched arms | 03-phases L74-75 | supported | 0.73 | 0.63 | no |
Compared with v1 recheck: the eBOPs claim went from overstated (p_sup 0.04, wrong lines) to supported 0.94 (right lines).
