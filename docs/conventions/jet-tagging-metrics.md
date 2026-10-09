---
title: Jet-tagging metrics
status: current
date: 2026-09-26
---

# Jet-tagging metrics

Applies whenever a tagging-performance number is computed, compared or quoted.

## Data and splits

- Dataset: public HLS4ML LHC Jet dataset (Zenodo record 3602260), five classes
  g / q / W / Z / t. Round-14 input set `l1x3`: N constituents × 3 features
  (pt, etarel, phirel), N ∈ {8, 16, 32, 64}. Source: `DATASET.md`,
  `.claude/memory/project-context.md`.
- Training archive (62 files) is split 80/20 into train and **validation**; the validation
  part has n = 124,000 at the recorded N=8 runs (`publication/results/post_conference/
  ablation_metrics.json`, `n_validation`). The separate validation archive (26 files) is the
  **held-out** set, n = 260,000, called ROC-test. It is never used for selection.
- Labels are one-hot; scores are the five softmax outputs. `y` arrays for the same split
  must be byte-equal across arms (the pt-weighting eval asserted this against
  `r14/n8/W1A8-s1.npz`; `.claude/memory/experiment-log.md` 2026-09-26).

## Metrics

- Headline: **macro one-vs-rest AUC** on the held-out set,
  `roc_auc_score(y_onehot, scores, multi_class="ovr", average="macro")`, plus the five
  per-class AUCs.
- **Validation macro AUC** is the training-time monitor and the selection metric. It is a
  different measurement from held-out AUC and is always labelled as such.
- **Accuracy** (argmax agreement) is reported beside AUC, never instead of it; the two rank
  models differently (constituent study 2026-09-16: reduced-FFN had the highest validation
  AUC, channel-wise the highest held-out accuracy). Calibration does not change argmax.
- Background rejection at signal efficiency 0.5 when a working point is asked for;
  `publication/results/pre_conference/working_points.json` has the recorded ones.

## Seeds and intervals

- At least three seeds for any claim; eight when the expected gap is under 0.005. Report
  mean ± sample sd (ddof=1). Seed sd at N=8 W1A8, 1000 epochs: about 0.0013 to 0.0016
  (pt-weighting BASE 0.8711 ± 0.0013 over 8 seeds; r14 0.8712 ± 0.0016 over 3).
- A gap between arms is paired by seed: mean difference with a 95 % t-interval
  (df = seeds − 1) and the count of seeds on which the sign holds. A gap whose interval
  covers zero is flat. Finite-test-set uncertainty is the paired bootstrap over jets when
  the seed count is one, and it is then labelled single-seed.
- Headline rule: seed-averaged and held-out.

## Labelling (non-negotiable)

Every number carries **metric** (validation AUC / held-out AUC / accuracy / rejection),
**split and n**, and **status** (single seed / seed-averaged, screen / full schedule).
Round-14 numbers also carry the input set and N. Two numbers are comparable only at the same
N, input set, split, schedule and selection rule.

## Required validation checks

1. Recompute from the `.npz` in the current session; inspect `d.files` and shapes first.
2. n equals the expected split size; a different n means a different split and is said so.
3. Baseline arm reproduces the recorded value for the same configuration within the seed
   spread; state the pull.
4. Selection was on validation; the held-out set was touched once, at the end.
5. Per-class AUCs shown; a class under 0.7 is called out.
6. `tools/verify_check.py` clean.

## Pitfalls, with the incident

- Cross-axis comparison: binary-without-norm vs FP32-with-norm quoted as a 2.6-point gap
  when the matched gap was 3.29 (2026-08-01, `.claude/memory/archive`).
- Screen numbers compared to full-schedule numbers (constituent screen, 50 epochs at
  LR 2e-4 vs 1000 at 2e-5; the log says not comparable, keep it that way).
- Validation AUC quoted in a README beside held-out numbers without the label
  (post-conference table, 2026-09-15; the label was added).
- Mixing best-checkpoint AUC with final-epoch cost (EBOPs pilot, 2026-09-10).
