# Outputs v1 — Jev on the flawed note (iteration 1, 3 Jev calls)
All verdicts advisory; model jev-1.13.0; catalog dd6593d7…; policy e8a26bf5….

## jev_check_methods (audit jv-f4024de9c4a948b6b1f996bda723e601)
| rule | choice | conf | disposition |
|---|---|---|---|
| selection | conflict (p=1.00) | 1.00 | mandatory_review |
| uncertainty | conflict (p=0.94) | 0.92 | mandatory_review |
| metrics | conflict (p=0.87) | 0.82 | mandatory_review |
| comparability | missing (p=0.74; conflict 0.24) | 0.65 | review |
| provenance | missing (p=0.90) | 0.86 | review |
| authority | missing (p=0.70) | 0.59 | review |

## jev_rank_snippets (audit jv-cd03c68b73644872a92de6a4982d56f4)
Ranking c (metrics L40-47 seeds/intervals) 2.25 > d (cost L31-36 selection+no-mix) 2.24 >
a (metrics L17-20 ROC-test never for selection) 1.98 > b (metrics L30-31 validation is selection metric) 1.62 >
e (03-phases L37-38 no circular selection) 1.49 > f (metrics L21-23 labels/y arrays, decoy) 0.45.
No snippet scored "3 directly answers" as the top class; decoy correctly lowest.

## jev_check_claims (audit jv-831728aa016f49a483202d9560c6b6a7), thresholds heuristic (conf 0.8, margin 0.25)
| id | flawed sentence vs source | choice | p(supported) |
|---|---|---|---|
| a | ROC-test selection vs metrics L17-20 | absent 0.67 / overstated 0.32 | 0.00 |
| b | final-epoch cost + best AUC vs cost L31-36 | overstated 0.78 | 0.01 |
| c | single-seed +0.002 claim vs metrics L40-47 | absent 0.82 | 0.00 |
Note: the claims label set has no "contradicted"; "absent/overstated" with p(supported)≈0 is the
negative signal. All three below the 0.8 confidence threshold except none; dispositions "review".
