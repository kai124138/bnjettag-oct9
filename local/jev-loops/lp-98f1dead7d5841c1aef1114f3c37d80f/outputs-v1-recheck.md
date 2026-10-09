# Outputs v1 recheck — Jev on method-note-corrected-v1.md (2 Jev calls; loop total 5)

## jev_check_methods (audit jv-8bf392f69dce4e2fbef80caa0e534e57)
| rule | flawed v1 | corrected v1 |
|---|---|---|
| selection | conflict 1.00 | consistent 1.00 |
| uncertainty | conflict 0.94 | consistent 1.00 |
| metrics | conflict 0.87 | consistent 0.60 (missing 0.40) |
| comparability | missing 0.74 | missing 0.53 / consistent 0.46 |
| provenance | missing 0.90 | missing 0.93 |
| authority | missing 0.70 | missing 0.72 |

## jev_check_claims (audit jv-812fdbcf22a341ceb3592dd6f349e0e1)
| id | claim -> source | choice | p(supported) |
|---|---|---|---|
| a | validation selection + "ROC-test never" -> cost L31-36 | supported 0.49 / overstated 0.39 | 0.49 |
| b | eBOPs remeasured on selected ckpt -> cost L31-36 | overstated 0.55 | 0.04 |
| c | 8 seeds + paired t-interval + flat rule -> metrics L40-47 | overstated 0.58 | 0.30 |
| d | ROC-test never for selection -> metrics L17-20 | supported 0.92 | 0.92 |
