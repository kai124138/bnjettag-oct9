# Sample-weighting implementation options

2026-09-25 — Planning only. No option selected or implemented; no training launched.

The dataset already identifies each jet as g/q/W/Z/t. The decision is how to convert those known labels and jet Pt into one loss weight per training row. The first three options retain the existing five-class labels, outputs, and categorical loss.

Let `n[c,b]` be the training count for class `c` in log-Pt bin `b`, `n[rest,b]` the summed count for the other four, and `r[c,b]=(n[c,b]+0.5)/(n[rest,b]+0.5)`. Use 100 equal-width natural-log bins fitted only to the actual training subset.

| Option | Per-jet rule | What it tests |
|---|---|---|
| A. One target class, five-class model | Target-class jets receive `r[target,b]`; all other jets receive 1 | Closest application of the supplied binary rule to a chosen class without changing the classifier task. The existing top/rest plots illustrate this. |
| B. All five classes, five-class model | A jet of true class `c` receives `r[c,b]` | Symmetric multiclass extension: emphasize each class's relatively class-rich regions. Every class can receive non-unit weights. This is not five copies of a jet, five models, or simultaneous application of five weights. It is not yet a confirmed Russell prescription. |
| C. A group of classes, five-class model | Sum counts across a chosen target group; group members receive `(n[group,b]+0.5)/(n[complement,b]+0.5)` and others receive 1 | Group-level prioritization, e.g. W/Z/top versus g/q, while continuing to classify all five identities. A group's members share the same bin factor. This grouping is hypothetical, not selected. |
| D. Binary task | Map selected original classes to two targets and use Russell's binary rule | Direct binary application, but changes the scientific task, labels, output head/loss, and evaluation. Requires a matched binary baseline and is not a drop-in comparison to current five-class results. |
| E. Match Pt distributions | Choose a common target distribution `q[b]` and weight class `c` by approximately `q[b]/p_c[b]`, where `p_c` is its normalized training histogram | A different objective: reduce Pt-shape differences across classes. Requires shared-support and sparse-bin decisions. Reversing S/B to B/S for signal is a two-group special case up to normalization and smoothing. It is not the supplied signal-rich-region rule. |

Independent binary one-vs-rest models or a per-output weighted binary loss are broader redesigns under D, not necessary for ordinary per-jet sample weighting. Resampling jets is another way to alter training exposure, but changes sampling noise and exposure; keep ordinary sample weights for a first implementation of this idea.

## Choices separate from the grouping

- **Class balance:** use Pt factors alone, class factors alone as a control, or their product. For the five-class loss, conventional balanced factors are `N/(5*N_c)` from training rows. Binary/group-balanced factors instead balance the two selected groups; they are a different choice and must be named explicitly. Multiplying class factors by Pt factors does not guarantee equal weighted class totals.
- **Overall scale:** retain literal factors for formula fidelity, or explicitly divide all training weights by their mean to preserve average weight 1. Global rescaling preserves relative weights but changes loss/gradient scale and potentially its balance with regularization. Record raw and applied factors. Per-class mean normalization is another, scientifically different policy: it changes relative class contributions.
- **Sparse bins/extremes:** begin diagnostics with the stated 100 bins/+0.5, inspect counts, weight tails, per-class weight sums, and effective sample size. Clipping, stronger smoothing, or alternate bins are optional variants, never silent alterations of Russell's formula.

## Recommended implementation scope and experiment sequence

Keep the existing five-class model. Implement a reusable, default-off per-jet weighting path with explicit A and B modes; C is the same grouped-count construction as A if subsequently requested. B is a candidate for an all-class study, while A is the closer test of the literal supplied assignment. No mode is selected by this document, and B must be identified as an adaptation unless Russell confirms it.

Keep 100 bins and +0.5 as explicit recorded settings. First isolate Pt weighting against an unweighted baseline; add class-factor multiplication as a distinct treatment if desired. A class-only control can separate that effect. Freeze any weight normalization or clipping choice before a comparison.

In `../bnhgq2/train.py`, `load_train_data` currently returns features and five-column labels but not jet Pt. The trainer permutes and splits those arrays explicitly, then calls `model.fit` without sample weights. The validation AUC callback uses its separate validation arrays. An eventual implementation must carry Pt through exactly the same row operations, derive bins/counts after the split, and pass one scalar weight per training jet. Weighting does not add Pt as a model input. Preserve unweighted validation/model selection and held-out evaluation for the matched comparison, unless a different metric is explicitly chosen.

Before training, verify alignment, endpoint assignment, count sums, disabled-mode behavior, and weighted-loss behavior. Save seed, source/order hashes, bin edges/counts, grouping, raw/applied weight statistics, class-factor policy, and config. Each seed or data subset requires recomputation; do not reuse the full-dataset diagnostic ratios. Training-only weights use their own fitted support; an out-of-range policy is needed only if the lookup is subsequently applied to other rows, and must then be explicit.

Use the same architecture, inputs, seeds/splits, optimizer schedule, training budget, and checkpoint-selection rule for baseline and treatment. Evaluate the intended metric plus per-class and Pt-dependent behavior; follow initial matched runs with matched additional seeds. Existing diagnostic figures establish the calculation, not a performance benefit. B/C/E require their own diagnostics because the current hypothetical-weight plots apply only one target-class ratio at a time and leave the remaining jets at 1.
