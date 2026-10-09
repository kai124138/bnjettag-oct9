Residual validation-AUC review

Fresh CPU evaluation of the channel checkpoint gives validation AUC 0.8518019217821239 versus recorded training-selection AUC 0.851884371427292: difference -0.0000824496451681. The selected checkpoint's published CPU accuracy is reproduced. This residual AUC difference does not explain the roughly 0.26 numerical gap between multiclass accuracy and AUC.

The training order is validation prediction, compute_ebops, checkpoint save. Installed hgq2 0.1.9 source was inspected read-only at /Users/kaiyamaguchi/Downloads/bnjettag-training-results/.venv-hgq2/lib/python3.12/site-packages/hgq:

- utils/minmax_trace.py:13 resets integer/sign state only on trainable quantizers possessing _i_decay_speed.
- quantizer/internal/fixed_point_quantizer.py:61 creates _i_decay_speed only for WRAP overflow. KIF/KBI assignments during tracing are likewise guarded by WRAP and trainable (approximately lines 277 and 402).
- The experiment's learned activation grids in publication/code/hgq2/bnhgq2/qat.py:279 use SAT/RND_CONV; attention table configurations use SAT; the binary accounting quantizer uses SAT_SYM. The inspected tracing path therefore does not provide evidence of learned i/f mutation in this configuration.
- layers/core/base.py:95 updates _ebops and adds resource losses during tracing. TrainingFlagWrapper('tracing') is false in a boolean test; this does not activate ordinary training behavior. QSoftmax's configured table quantizers follow the same SAT paths.

A possible float32/float64 probability discrepancy was checked and rejected as the explanation. Although metrics() itself preserves input dtype, its actual callers explicitly cast logits to float64. Root's controlled R1 recomputation gives float32-probability AUC 0.8518019422088461 versus float64 0.8518019217821239, only about 2.04e-8 apart. Both remain roughly 8.24e-5 below the recorded selection AUC. Independent sklearn verification also reproduces the fresh probability-ranking metric.

Conclusion: no evidence from the inspected source supports trace_minmax changing learned SAT quantizer widths as the cause. Historical GPU versus fresh CPU forward arithmetic, batch shape, or score ties are hypotheses only; original historical logits or a controlled same-input/device comparison would be needed to attribute the cause. Preserve recorded selection AUC and freshly recomputed CPU AUC as distinct measurements, and state this small reproducibility limitation rather than assigning an unverified numerical explanation. No additional compute was launched for this review.
