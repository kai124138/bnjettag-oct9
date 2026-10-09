# STUDY physics review v1 — 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context). Artifact: `campaigns/2026-09-26-training-batch/STUDY.md`
(plus `plan.md`, which it cites). Phase STUDY: no results exist; checks apply to the plan.

## Figures

The artifact shows and cites **no figures**, and there is no compiled PDF beside it. Nothing
to inspect by eye.

- Planned figures: **underspecified** (see C1). The only figure named is "interim-readout
  figures labelled validation" (STUDY.md line 302). No ROC figure is pre-registered, and
  nothing fixes a log mistag axis, per-class curves, or split, n and seed count in the caption.

## What I verified

- Sun et al. Table 1 (pdftotext of `literature/jet-tagging-transformers/2510.24784_...fpga.pdf`):
  Deep Sets (HGQ) N=64 **79.4 %**, Linformer 64 **79.8 %**, MLP Mixer [18] 64 **79.7 %**, MHA 64
  **77.9 %**. All four rows list **DSP = 0**. §3 gives 620,000 train and 260,000 test jets and
  states that "all models trained in this work" used a 350,000 EBOPs target with a PID on β.
  The quoted values match STUDY.md lines 38-39.
- [D2] LR schedule against `reference-code/HGQ2-examples/jsc150/run_train.py`: lines 21-37
  define the schedule, and line 93 calls it with `(lr, 500, t_mul=1, m_mul=1, alpha=1e-6,
  alpha_steps=10)`. So cycle_t = min(step/490, 1), lr(490..499) = 1e-6, lr(500) = 3e-3.
  Matches. Adam defaults are at line 97, batch 2,790 at line 67, and 7,000 epochs at line 104.
  All match [D3] and [D4].
- [D7] pT gate against `jsc150/data.py`: lines 25-26 apply the gate. Lines 28-31 then
  standardize with mean and std over train plus validation (620k jets). Lines 11, 14 and 33
  cast to float16. The STUDY's description matches, including the deviation to train-only
  statistics.
- Seed-spread input: I recomputed top-1 accuracy over the eight
  `bnjettag/roc-results/ptw-n8/BASE-s{1..8}.npz` files (keys `y`, `score`; 260,000 rows each).
  Mean 0.6234, **sd (ddof=1) 0.00188**, against the claimed 0.0019. The population sd would be
  0.00176, so the STUDY uses the correct ddof. Macro-OvR AUC is 0.8711 ± 0.0013 (ddof=1).
- Resolving-power arithmetic: t(0.975,7)/√8 = 2.365/2.828 = 0.836. 0.836 × 0.19 pt = ±0.16 pt,
  and 0.5/0.836 = 0.60 pt. All correct.
- Existing context for the reference: `_attic/repro-chang/repro-chang/comparison.md` lines
  23-27. Our run of Chang's own code gave xfm-n64 80.56 % (paper MHA-64: 77.9 %, Δ +2.7) and
  xfmt-n64 80.85 % (paper Linformer-64: 79.8 %, Δ +1.05). Both are single seed and were
  selected on test.
- `docs/chang-vs-bnjettag.md` line 154 says "the pT gate is in their code but not their paper".

## Findings

### (A) Must resolve

**A1. No arm manipulates the thesis variable, so neither outcome of the primary question bears
on the thesis as the "Bearing on the thesis" paragraph claims.**
- *Attack.* All 56 runs are binary. The thesis is about the cost of binary weights against
  full-precision and 8-bit baselines. The only non-binary comparand is one external number
  (79.4 %), produced under a different setup:
  - a different model family (Deep Sets with per-parameter HGQ widths);
  - a different backend (JAX, float16 inputs);
  - different standardization statistics;
  - a different head;
  - possibly a different input distribution (the gate is in the code but not stated in the
    paper);
  - an unstated selection rule.

  A gap between arm A and 78.4 % therefore cannot be attributed to binary weights rather than
  to any of these. The STUDY says (line 29) "A hit means binary survives an iso-cost
  comparison". But [L2] already concedes that EBOPs omit the accumulator, the dominant cost of
  a ±1 adder tree. So "iso-cost" does not hold even on a hit.
- *Table 1 weakens it further.* Every HGQ row in Table 1 already uses 0 DSP. Against this
  reference, the thesis's differentiator ("essentially no DSP") is no differentiator at all.
  Only LUT or latency could be one, and [L7] rules out synthesis.
- *Evidence.* STUDY.md lines 26-31, 65-75 (no non-binary arm), 408-411 ([L2]), 420 ([L7]);
  Table 1 DSP column.
- *Settle.* Choose one of two fixes:
  - (a) Add a matched non-binary arm: HGQ float-latent weights, or W8 with learned activation
    widths. It needs the same gate, split, recipe, target and seeds, paired by seed with A. A−H
    is then the binary cost at matched EBOPs, measured in this pipeline.
  - (b) Rewrite the primary question and "Bearing on the thesis" as a descriptive replication:
    "what our binary N=64 model reaches under this recipe at 350k". Attach no thesis claim to
    either outcome, and drop "survives an iso-cost comparison".

  The archived r14 n64 FP32 and W8A8 arrays (`bnjettag/roc-results/r14/n64/`) are ungated and
  use a different architecture and split, so they cannot substitute ([L6] is right).

### (B) Should address

**B1. The reference's own uncertainty is at the scale of the tolerance, and the test treats it
as exact.**
- *Attack.* The primary test is one-sample: A's seed-mean interval against 78.4 %. Our own
  rerun of the same code family moved the paper's N=64 rows by +1.05 (Linformer) and +2.7 (MHA)
  points (`comparison.md` 23, 27). The Deep Sets row was never reproduced. The gate may not
  apply to the paper's number. The selection rule is unstated. A 1.0-point tolerance is smaller
  than the known code-versus-paper spread for this family.
- *Settle.* Quantify [L1] with these numbers. Then either widen the tolerance to cover the
  demonstrated reproduction spread, or report the primary outcome as a distance with its
  interval and no pass/fail label.

**B2. "Native HGQ2 EBOPs" equivalence is asserted, not checked.**
- *Attack.* "Iso-EBOPs" requires that our `compute_ebops` count our custom binary layers
  exactly as HGQ2 counts Chang's models. The terms at risk are:
  - 1-bit weight accounting;
  - the fixed 10-bit softmax output;
  - the A·V product;
  - the learned positional-encoding add;
  - the 256-jet trace versus HGQ2's in-training `FreeEBOPs`.

  A 10-30 % accounting offset moves the effective budget more than the B-versus-A ladder does.
- *Settle.* Pre-register a PREFLIGHT cross-check: take a repro-chang xfm-n64 checkpoint, compute
  its EBOPs with our tool and with HGQ2's own, and report the ratio. The 350k target means
  nothing until that ratio is near 1.

**B3. Survivorship bias, and undefined pairs when seeds are infeasible or diverge.**
- *Attack 1.* Arm summaries average over feasible seeds only (line 147). At k = 6 of 8, the two
  seeds that failed to reach the budget, which are plausibly the weakest, drop out, and the
  mean is biased upward.
- *Attack 2.* The paired comparisons (A−B, A−D, A−R) do not say what happens when a seed is
  feasible in one arm and not the other.
- *Attack 3.* Arm R (LR 2e-5 linear, 1,000 epochs, starting from 24.8M EBOPs) may well never
  reach 350k. In that case A−R, the secondary question, has no branch in the falsifier (lines
  176-178).
- *Attack 4.* Line 150 keeps "the best feasible checkpoint before [divergence]". It is ambiguous
  whether that checkpoint's accuracy enters the arm mean.
- *Settle.* Pre-register four rules:
  - paired gaps use seeds feasible in both arms, with the count stated;
  - feasibility rates are compared as their own outcome;
  - an "R infeasible" branch of the recipe claim is defined (for example, "recipe claim
    supported on feasibility");
  - it is stated whether pre-divergence checkpoints count.

**B4. The optimizer-stability falsifier is a bare count.**
- *Attack.* "More A seeds diverge than D seeds" (line 182) falsifies the claim at 1 versus 0 out
  of 8, which is well inside chance.
- *Settle.* State a threshold in advance: a minimum count difference (for example ≥ 4 of 8
  versus 0) or an exact test on the paired divergence outcomes.

### (C) Suggestions

- **C1. Figures.** Pre-register the held-out figures:
  - per-class ROC with a **log mistag axis**;
  - seed band (sd, ddof=1) with the seed count in the legend;
  - "ROC-test, n = 260,000" in the caption;
  - the accuracy-versus-EBOPs ladder (A, B, C) with paired-gap intervals, not unpaired error bars.
- **C2. Resolving power at k = 6.** The claim floor is k ≥ 6. There the half-width is
  t(0.975,5)/√6 · sd = 1.05 · sd, not 0.836 · sd. State that the 0.6-point sd ceiling becomes
  0.48 pt.
- **C3. Gate, then standardize.** Gated constituents become −shift/scale, not zero, and with
  `pool gap` and no mask they enter the average. This is also true of Chang's code, but confirm
  that our loader does the same, including whether it has a padding mask that would treat the
  two differently. Add this to [A3].
- **C4. Winner's curse on validation.** Selection runs over up to 7,000 checkpoints on
  n_val = 62,000 (binomial SE ≈ 0.16 pt at 79 %), so validation accuracy at selection is
  inflated. Held-out is untouched, so there is no tautology, but report the validation−held-out
  gap per run.
- **C5. EBOPs at selection is not an outcome.** With the PID and the ≤ target feasibility
  filter, the selected EBOPs sits at the target by construction. Do not report "reached 350k"
  as a finding beyond the feasibility count.
- **C6. The reference band.** The MLP Mixer 79.7 % is quoted from ref. [18], and the paper does
  not state that it was trained at 350k. Label it so in the band on line 39.
- **C7. Epoch-500 sd.** This is one cosine cycle, ending at the LR floor. Label it an early
  estimate that may understate the terminal spread (Round-14 N ≥ 32 binary instability).
- **C8. Attention-alive.** If attention does not collapse, the like-for-like comparand is
  Linformer 79.8 % or MHA 77.9 %, not Deep Sets. State in advance which comparand applies in
  each case, so it cannot be chosen after the result.

## Statistical design: summary

- Seeds 8 per arm, ddof = 1 stated, and paired t-intervals (df 7) with sign counts where init
  and order are shared: correct.
- Welch for E and F, and Holm across the five secondary gaps: appropriate.
- Per-class AUCs beside the macro: pre-registered.
- The held-out set is touched once, on a checkpoint selected on validation: no tautology.
- The one uncertainty the design cannot measure is the reference's own (B1).

## Verdict

I would not approve this for launch as designed. The deciding issue is A1: no arm varies the
thesis variable, so the primary outcome cannot be read as the cost of binary weights. Either
add a matched non-binary arm, or remove the thesis claim from the question.
