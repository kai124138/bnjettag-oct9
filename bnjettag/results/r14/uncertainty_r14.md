# R14 uncertainty pass (ROC-test macro AUC; seed spread + paired bootstrap x200)

| N | comparison | gap | σ_seed | σ_boot | σ_total | verdict |
|---|---|---|---|---|---|---|
| 8 | fp32 - w1a8 | +0.01520 | 0.00097 | 0.00018 | 0.00099 | RESOLVED |
| 8 | fp32 - w8a8 | +0.00020 | 0.00060 | 0.00012 | 0.00061 | UNRESOLVED |
| 8 | w1a8 - w1a6 | +0.00232 | 0.00149 | 0.00019 | 0.00150 | TENTATIVE |
| 8 | w1a8 - w1a4 | +0.01786 | 0.00116 | 0.00023 | 0.00119 | RESOLVED |
| 16 | fp32 - w1a8 | +0.01717 | 0.00076 | 0.00018 | 0.00078 | RESOLVED |
| 16 | fp32 - w8a8 | +0.00042 | 0.00109 | 0.00012 | 0.00109 | UNRESOLVED |
| 16 | w1a8 - w1a6 | +0.00457 | 0.00055 | 0.00017 | 0.00058 | RESOLVED |
| 16 | w1a8 - w1a4 | +0.02630 | 0.00121 | 0.00026 | 0.00124 | RESOLVED |
| 32 | fp32 - w1a8 | +0.03218 | 0.00468 | 0.00022 | 0.00468 | RESOLVED |
| 32 | fp32 - w8a8 | +0.00164 | 0.00114 | 0.00012 | 0.00115 | TENTATIVE |
| 32 | w1a8 - w1a6 | +0.00300 | 0.00461 | 0.00022 | 0.00461 | UNRESOLVED |
| 32 | w1a8 - w1a4 | +0.02195 | 0.00464 | 0.00023 | 0.00465 | RESOLVED |
| 64 | fp32 - w1a8 | +0.03647 | 0.00674 | 0.00025 | 0.00674 | RESOLVED |
| 64 | fp32 - w8a8 | +0.00385 | 0.00094 | 0.00013 | 0.00095 | RESOLVED |
| 64 | w1a8 - w1a6 | -0.00151 | 0.00757 | 0.00021 | 0.00758 | UNRESOLVED |
| 64 | w1a8 - w1a4 | +0.00485 | 0.00672 | 0.00027 | 0.00673 | UNRESOLVED |

Q4 binary seed-variance ratio (n32/64 vs n8/16): 0.5x

CORRECTION (2026-08-04): the pooled Q4 ratio above is invalid (pooling mixes the different per-N means). Corrected statistic — mean per-N seed variance, (n32,n64)/(n8,n16): **75.8x**.
