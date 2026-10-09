# EBOP-ablation categorical accuracy

Top-1 categorical accuracy is computed as `mean(argmax(logits) == argmax(labels))`.
The test column uses the full held-out 260,000-jet split; validation contains 124,000 jets.

| Run | Status at evaluation | EBOPs | Selected validation AUC | Validation accuracy | Test accuracy |
|---|---|---:|---:|---:|---:|
| R0 | finished | 348,526 | 0.8453 | 57.67% | **57.48%** |
| R1 | finished | 317,890 | 0.8519 | 58.89% | **58.74%** |
| R2 | finished | 329,838 | 0.8545 | 58.52% | **58.31%** |
| R3 | interim checkpoint | 340,174 | 0.8463 | 57.62% | **57.34%** |
| R4 | no <=350k checkpoint yet | — | — | — | — |
| R5 | finished | 349,390 | 0.8410 | 57.04% | **56.94%** |
| R6 | interim checkpoint | 348,366 | 0.8420 | 57.12% | **56.91%** |

R3 and R6 values are checkpoint snapshots, not final completed-run results.
R4 has no point until a checkpoint satisfies the final 350k-EBOP constraint.
