# Engram pilot at 100 epochs

Verified from W&B at 2026-09-20T21:57:54.122893+00:00. Private local report; initialization seed 1, 124,000 internal-validation jets. Latest epoch results; no held-out test or synthesized hardware results.

| Arm | Design | Validation accuracy | Macro AUC | Native backbone EBOPs | Estimated memory bitops | Combined proxy |
|---|---|---:|---:|---:|---:|---:|
| E00 | Two-block reference | 49.7782% | 0.799996 | 849,916 | 0 | 849,916 |
| E01 | One-block baseline | 56.1016% | 0.840804 | 566,719 | 0 | 566,719 |
| E02 | One block + ungated memory | 61.0298% | 0.869458 | 515,172 | 17,920 | 533,092 |
| E03 | One block + gated memory | 60.1847% | 0.863988 | 499,662 | 78,496 | 578,158 |

None met the 350,000 combined-cost target. E02 has the highest observed accuracy at this prefix; the gated design has not shown an advantage. This one-seed pilot does not establish reproducible superiority. E02/E03 passed selected-checkpoint reload validation; E00/E01 report finalization failed on a strict numerical comparison, after durable epoch-100 training checkpoints had been saved.

For E02/E03 the reported total is native HGQ2 backbone EBOPs plus a custom memory-operation estimate; it is not a measured native-only cost or FPGA resource count. Logical tables are 16 KiB (E02) and 32 KiB (E03).

E03 gate diagnostics on the fixed 256-example training probe: mean 0.5421, standard deviation 0.0669, 69.04% exactly 0.5, no recorded saturation or query clipping. Thus the gate is active but often unchanged at its midpoint. The effective value tables are 97.76% nonzero in E02 and 98.42% in E03. These probe observations do not establish a causal gating benefit.

All four arms are authorized to resume the original 1,000-epoch schedule. Preserve source/config/data/optimizer identity and original training arithmetic.

## Independent prediction check

E02 and E03 accuracy and macro AUC were recomputed from the archived 124,000-event prediction arrays and match the report values to 1e-12. The observed E02-minus-E03 accuracy difference is **+0.845 percentage points**, with a paired bootstrap 95% interval of **+0.628 to +1.061 points** (50,000 resamples; fixed seed 20260920). This measures validation-sample uncertainty conditional on these selected checkpoints, not variation across training seeds or an independent held-out test. Evidence: [verified comparison](engram-e100-archive/verified-comparison.json).
