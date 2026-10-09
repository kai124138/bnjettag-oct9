# N=8 binary-weight EBOPs pilot: result analysis

The 75% budget arm met its resource target and is the strongest result of this pilot.
The 25% arm compressed the model but did not meet its requested budget. The 50% arm
failed during GPU compilation before a completed epoch. Three runs completed all
101 epochs and committed their model artifacts to W&B.

All results concern N=8, L1x3 inputs (pt/etarel/phirel), binary absmean weights,
initial 8-bit activations with learnable per-tensor widths, and seed 1. Each completed
run used 496,000 training jets and the same 124,000-jet internal validation split.
The common initial HGQ2 EBOPs count was 1,739,182.

## Saved checkpoints

| Arm | Requested EBOPs ceiling | Saved checkpoint EBOPs | Reported validation macro-OvR AUC | Budget status |
|---|---:|---:|---:|---|
| Free-width control, beta=0 | None | 1,780,910 | 0.871660 | No target |
| 75% budget | 1,304,386.5 | 1,263,790 | 0.870054 | Met |
| 50% budget | 869,591 | — | — | GPU compilation failed |
| 25% budget | 434,795.5 | 1,177,006 | 0.862902 | Missed; unconstrained checkpoint |

AUC entries above are quoted from the downloaded training metadata:
[control](ed3piak8/artifact/train_meta.json),
[75%](3bynw2ra/artifact/train_meta.json),
[25%](zyj0gwkq/artifact/train_meta.json).
They have not been independently recomputed from prediction arrays in this analysis.
No held-out ROC-test arrays or synthesis reports were produced by this pilot.
Single-seed observations do not establish accuracy equivalence or significance;
no across-seed uncertainty interval is available.

Checkpoint EBOPs were independently recomputed after loading each downloaded Keras
model, using zero and random input batches. Both agreed exactly with the stored cost.
All learned widths agreed with the artifact metadata, and all 15 binary projection/head
layers retained exactly two symmetric nonzero effective weights. See
[checkpoint verification](checkpoint_verification.json).

## What worked

The 75% arm first reached its ceiling at epoch 50 (1-based). Its selected model is from
epoch 95 and uses 27.33% fewer EBOPs than initialization, or 29.04% fewer than the
selected control checkpoint. Those are deterministic cost comparisons of these
particular checkpoints, not estimates of LUT savings.

Its 21 learnable activation sites have a mean width of 6.14 bits. Distribution: five
sites at 5 bits, eleven at 6, three at 7, one at 8, and one at 9. For example, first-block
Q/K score operands became 5/6 bits, many projections and FFN inputs became 6 bits,
and the input projection retained 9 bits. The final head input retained 8 bits. The
control's corresponding mean was 8.14 bits, with three sites growing to 9 bits.
The two explicitly frozen attention-probability operands remain 10 bits and are excluded
from these 21-site means. Learned allocation therefore differs by quantizer site.

## Why the 25% result needs a separate interpretation

Its best-AUC checkpoint is epoch 49 and has 1,177,006 EBOPs. Its final epoch has
1,062,318 EBOPs and reported validation AUC 0.858577. The final cost is 61.08% of
initial cost, still above the requested 25%. No feasible checkpoint was recorded;
the artifact correctly contains model_unconstrained.keras and budget_met=false.
Do not pair the best-epoch AUC with the final-epoch EBOPs.

The controller was active: beta rose from 1e-7 to 6.37e-6, and the mean learned width
ended at 5.33 bits. Meanwhile the common learning rate decayed from 2e-5 to 2e-7.
The final discrete cost plateau began at epoch 85. The raw i/f parameters continued
moving. This is consistent with insufficient remaining optimization under the stronger
penalty as the learning rate became small. It does not establish that 25% is achievable,
or that it is fundamentally impossible. A longer compression phase with a nonzero
learning-rate floor is an experiment to test, not a demonstrated fix.

## Missing 50% arm

[The log](b50.log) records an NVIDIA A10 and failure in XLA/Triton GEMM autotuning:
`NOT_FOUND: No valid config found!`. W&B has zero completed-epoch history rows and no
model artifact for this run. This budget remains untested. The CPU preflight covered
model/controller semantics but could not expose this GPU compiler failure.

A practical recovery test is an opt-in `jit_compile=False` at model.compile, followed
by a small GPU training smoke before rerunning this arm. Keras documents that this
argument controls XLA compilation:
https://keras.io/api/models/model_training_apis/#compile-method
The workaround has not been tested or applied during this analysis.

## Recommended next experiments

1. Recover the missing 50% point with a GPU compiler smoke and a separately identified retry.
2. Evaluate the control and 75% selected checkpoints on held-out ROC-test data; use paired
   prediction-based uncertainty, then repeat across seeds before claiming preserved accuracy.
3. Test an extended compression schedule for the aggressive budget, tracking both cost and
   validation quality; retain the strict feasible-checkpoint selection.
4. Preserve learned widths in export and synthesize the 75% checkpoint before claiming
   actual FPGA LUT/DSP/latency savings. Architectural MAC count did not change.

[Training curves](pilot_results.png) show the complete histories. The underlying data,
model artifacts, job logs, and reproducible analysis scripts are saved beside this report.
No new training, ROC, or synthesis jobs were launched during this analysis.
