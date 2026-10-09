# Static contract-fixture review — v1

Date: 2026-10-01. Verdict: **provisional ITERATE — contract fixtures only**.

This reviews the inspected `preflight_worker.py` functions against the executable
fixture table in `STUDY_v3.md`. It is not the final PREFLIGHT verdict. The owner is
revising these fixtures; this record describes the version inspected before those
fixes. No worker, ML package, model/array evaluation or network operation was run.
Parent-runner provenance issues are outside this bounded review.

## Required fixture corrections

1. **pT capped case does not exercise clipping.** `training_contracts` uses 60
   log-spaced pT values, eight bins, a 48-row training subset, at most twelve
   rows/class and cap 5. Each bin contains at most eight original points. Under
   `pt_weights.compute_pt_weights`'s recorded smoothing, even the largest
   class-bin ratio is bounded by `(8.5/48)/(0.5/12) = 4.25`, below the cap.
   Thus naming a case “capped” does not test the clipping operation. Use a fixture
   or cap that demonstrably clips populated bins; assert capped and uncapped
   weights differ and that both reproduce their captured-original counterparts.
   This implements the existing capped/uncapped row, not a new weighting study.

2. **Teacher dispatch lacks path/input assertions.** `teacher_contracts` patches
   `keras.models.load_model` to return one fixed model without recording its path
   or `compile` argument. The fake prediction ignores its inputs, and training
   and validation arrays are identical. Wrong checkpoint-path or train/validation
   dispatch can therefore produce the same tested output. Record normalized load
   paths and arguments, use distinct training/validation fixtures, and verify the
   prediction input identity. Keep artifact calls fake. The production contracts
   are in `run_ablation.py`'s local/artifact teacher resolution and prediction block.

3. **Missing promised legacy aliases can silently pass.** `core_contracts` checks
   `pack_for_mulder` only when `hasattr` succeeds and each legacy wrapper only when
   its file exists, then returns `aliases: PASS`. Deleting a declared alias can
   skip its test. Require the candidate's declared aliases/imports explicitly;
   original-public absence can be a justified NOT_APPLICABLE. Retain the useful
   existing signature/function-identity and forwarding checks for present aliases.

4. **Fixed-cap tests do not cover target scheduling/final-target filtering.**
   `selection_contracts` meaningfully tests `BudgetMonitor` at costs below/at/above
   one cap and tests ranking ties. It imports `ablation` without exercising
   `ablation.training_target` or the distinction between temporary training target
   and final feasibility in `ablation.run_training` (source anchors: lines 101,
   252 and 290 in the inspected source). Add bounded fabricated boundary/selection
   evidence for the already promised target/final-target cases, or retain their
   explicit incomplete status. No optimizer step or new training run is needed.

5. **Evaluation utilities do not establish entry-point wiring.**
   `evaluation_contracts` tests softmax/dtype, batching, standardization, HDF5 row
   loading and `scores_for`; it never exercises `eval_one`, the adapted evaluator
   entry-point path dispatch, or `load_jet_pt`. Explicit checkpoint/data paths,
   per-model preprocessing and saved label/score/pT association remain uncovered.
   Use the existing fabricated fixtures and stubbed model/metric/file interfaces
   to verify the declared wiring. Make class-score patterns and file-label patterns
   distinct enough to expose row swaps: the inspected logits differ primarily by
   additive offsets, and both fixture files repeat the same label sequence.

## Positive coverage in the inspected version

- pT absent/disabled cases check no pT load or sample weights and equal unweighted
  behavior. Enabled cases check training partition/permutation; label mismatch is
  rejected before the stub fit. Captured-original/candidate comparisons provide
  independent regression evidence beyond the in-worker helper comparisons.
- Tracking missing/disabled/offline modes assert false with credential-file reads
  trapped. The opt-in teacher runner cases inspect the `remote` flag; artifact
  calls are fake.
- Fixed-cap admission, lower-cost/higher-AUC ranking and earlier-epoch ties are
  exercised through actual selection functions with fabricated records.
- Public training CLI dispatch and `--skip-convert`, path defaults/output override,
  present alias signatures, stable equal-pT constituent sorting, batch row order,
  score dtype and already-softmaxed pT-score rejection have executable assertions.

Resolve the five listed coverage gaps and re-review those changes. This record
adds no experiments or gates beyond `STUDY_v3.md`; it does not judge build/reload
completion, historical metrics, hardware, or launch readiness.
