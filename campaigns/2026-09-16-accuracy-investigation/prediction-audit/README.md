# Prediction audit — 2026-09-16

Recomputed all 60 Round-14 l1x3 archives under `research/bnjettag/roc-results/r14/n{8,16,32,64}`. Each contains the same 260,000 held-out ROC-test events. This is analysis of archived cluster predictions, not new model evaluation or training. No research-tree files were changed. Run `python3 local/accuracy-investigation/prediction-audit/audit.py` from the lab root to reproduce `results.json`; runtime was 16 seconds with one local process. `verification.json` cross-checks three representative archives against scikit-learn and tests tied-score AUC edge cases.

## Accuracy first

Percentages below are three-seed means; ± is sample standard deviation across seeds, not a confidence interval.

| Constituents | Precision | Top-1 accuracy (%) | Macro OvR AUC (%) | Top-2 accuracy (%) |
|---|---|---:|---:|---:|
| 8 | FP32 | 64.628 ± 0.059 | 88.643 ± 0.054 | 84.426 |
| 8 | W8A8 | 64.481 ± 0.133 | 88.622 ± 0.089 | 84.421 |
| 8 | W1A8 | 62.236 ± 0.258 | 87.122 ± 0.160 | 83.037 |
| 8 | W1A6 | 61.901 ± 0.494 | 86.890 ± 0.203 | 82.914 |
| 8 | W1A4 | 58.476 ± 0.213 | 85.336 ± 0.123 | 81.701 |
| 16 | W1A8 | 67.520 ± 0.141 | 89.561 ± 0.024 | 86.032 |
| 32 | W1A8 | 68.412 ± 2.362 | 90.524 ± 0.793 | 87.407 |
| 64 | W1A8 | 69.007 ± 3.145 | 91.213 ± 1.160 | 88.423 |
| 64 | FP32 | 79.115 ± 0.297 | 94.860 ± 0.120 | 91.391 |

The n8 W1A8 seed-1 accuracy is 62.401% with a conditional event-level Wilson 95% interval [62.215%, 62.587%]. AUC is not the fraction of jets assigned the correct class: it measures within-class positive/negative ranking. A model can rank each class well against most other classes while assigning the wrong winner among close alternatives. No general equality between AUC and multiclass accuracy is expected.

## Findings

- All 60 macro AUCs agree with archived metadata within 1e-12. The three representative scikit-learn comparisons agree exactly.
- All labels are valid one-hot vectors and every archive has identical label order. Counts for g/q/W/Z/t are 52,404 / 50,468 / 52,235 / 52,298 / 52,595. Class imbalance is small.
- All scores are finite probabilities; inspected row-sum error is at floating-point rounding scale. No top-score ties. The identity class-column permutation maximizes categorical accuracy in all 60 archives. No evidence of a systematic label permutation or broken softmax.
- For n8 W1A8 seed 1, class recalls are g 50.786%, q 59.154%, W 68.385%, Z 59.681%, t 73.851%. There are 22,798 g↔q errors and 16,646 W↔Z errors. These two pairs account for 40.35% of all errors. Pair-restricted AUC based on score differences is only 0.755 for g/q and 0.835 for W/Z, despite macro OvR AUC 0.872. These are direct signs of insufficient discrimination between particular classes.
- n8 W1A8 seed-1 ECE is 1.16% (20 fixed confidence bins). Severe global miscalibration is not supported by this diagnostic; ECE alone does not exclude class-specific correction opportunities.
- Binary threshold accuracy on n8 W1A8 seed 1 is 86.010%, while categorical accuracy is 62.401%. Binary accuracy counts each of five one-hot entries separately and has an 80% all-negative baseline. It must not be presented as jet classification accuracy.
- Large binary models are unstable across seeds. n64 W1A8 accuracies are 67.176%, 72.638%, 67.207%. The first two seeds' W/Z conditional AUCs are 0.751 and 0.881, respectively. These observations motivate auditing training/quantization of attention; they do not establish a particular implementation bug.

## Evidence for practical changes

Comparisons below use paired differences across the three training seeds, with a Student-t 95% interval (2 degrees of freedom). Individual event-paired intervals are separately saved in `results.json`. Three seeds provide limited precision and the event sample is shared, so repeating events across seeds is not treated as independent data.

- n8 FP32 minus n8 W1A8 accuracy: +2.393 percentage points, seed-paired 95% CI [1.737, 3.048]. Quantization accounts for a measurable part of the classification loss, but FP32 still has substantial error.
- n8 W8A8 minus n8 W1A8: +2.245 points [1.325, 3.165]. Precision is a possible tradeoff, contingent on measured hardware cost.
- n16 W1A8 minus n8 W1A8: +5.284 points [4.586, 5.983]. This is a more stable observed improvement than further increases to 32/64 constituents, and merits hardware resource/latency comparison before choosing it.
- n32 and n64 W1A8 relative to n8: the seed-paired intervals include zero, [-0.230, 12.582] and [-1.680, 15.223] points, respectively. More constituents alone do not resolve binary training instability.

Recommended next steps are explicit categorical reporting, validation-selected checkpoints, a disjoint calibration/decision-rule experiment, and targeted n8→n16 or precision experiments with latency/EBOP/hardware gates. Global positive temperature scaling preserves the argmax mathematically and cannot increase top-1 accuracy by itself. Avoid tuning against the complete archived test set; use a prespecified disjoint exploratory split or a separate validation split, then confirm on untouched data.
