# STUDY review, critical-reviewer, v1: 2026-09-26-training-batch

Panel mode. No verdict (the arbiter decides). Artifact: `STUDY.md` (483 lines), `plan.md`
beside it. Validator output: `review/STUDY_validators_v1.txt`. No mechanical STUDY validator
exists. `prose_lint` score 0, 5,737 words. No figures at STUDY.

Code paths cited as `ablation.py`, `data.py`, `qat.py` are from the 2026-09-22 screen bundle
`campaigns/2026-09-22-constituent-screen/study-code.tar.gz` (sha256 `26f3cc40...`, recomputed
in this session, matching the log). I extracted it read-only to the session scratchpad at
`code/bnhgq2/`. Chang code is `reference-code/HGQ2-examples/jsc150/`.

## What was checked and holds (with evidence)

- **Paper numbers.** From `pdftotext -layout` of the PDF: Table 1 has Deep Sets (HGQ) N=64 at
  79.4, Linformer 79.8, MLP Mixer [18] 79.7 and MHA 77.9. The test set is "260,000 jets"
  (§3). "All models trained in this work ... target EBOPs of 350,000 ... PID controller over
  β" (§3). The MHA-64 collapse is "consistently collapsing over several trained models
  despite the bitwidth constrained to at least one bit". STUDY:38-39 match.
- **Chang code citations.** `run_train.py:21-37` holds the cosine-restart function.
  `:93` is `(3e-3, 500, t_mul=1, m_mul=1, alpha=1e-6, alpha_steps=10)`, so the divisor is 490
  and [D2] is correct. I recomputed lr(9) = 2.9975e-3, which matches the ≥ 2.99e-3 at
  STUDY:239. `:97` is `Adam()` defaults ([D3]). `:67` is batch 2790 and `:104` is 7000 epochs
  ([D4]). In `data.py:22-26`, features `[5, 8, 11]` are pt, etarel and phirel per
  `tools/prepare_data.py` (constituent list: 5 pt, 8 etarel, 11 phirel), and the gate is
  `X *= X[..., :1] >= 2` ([D7]). Standardization runs over axis (0,1), gated and padded
  constituents included, as in our `data.py:77-85`. The test set is `150c-test.h5`, built
  from `val/`, i.e. our ROC-test archive. [D18] matches `model.py:178-210` (d24, h=2, FFN
  `dim*h` = 32, no PE).
- **Our config lineage.** In `const0922-a07-n64-s1-fast50-fp32.json` the PID block is
  p 1.0, i 0.05, d 0, warmup 1, bounds 1e-10 to 1e-3, damp 0 ([D5] ✓). It also has
  `order_seed` 20260912 ([D9] ✓), `selection_metric val_categorical_accuracy` and
  `stop_on_target false`. R's recipe matches `confirm0924-a07-n64-s2-e1000-5m.json`: lr 2e-5,
  warmup 1, decay 999, batch 256, β₂ 0.98, wd 0.01, clipvalue 1.0 ([D4] ✓). That config has
  PID warmup 10, as STUDY:465 says.
- **Initial EBOPs and parameters.** `n64-full-preflight-result.json` gives
  24,816,782 EBOPs and 12,788 parameters for `confirm0924-a07-n64-s2-e1000-5m` (STUDY:41 ✓).
- **Feasibility operator.** `ablation.py:409` is `feasible = cost['total'] <= final_target`
  (≤ ✓). The trace sample is `xt[:256]`, train jets (STUDY:117 ✓). The runner raises on a
  non-finite loss or AUC (`:390`, `:412`), which matches STUDY:149.
- **Arithmetic** (recomputed with scipy; every value holds):
  - t(0.975,7)/√8 = 0.8360, and t(0.975,3)/2 = 1.5912.
  - 0.836 × 0.19 = 0.159 pt, and the sd for a 0.5-pt half-width is 0.598 pt.
  - T_run is 58.3 h at 30 s and 116.7 h at 60 s. Pod-hours are 466.7 and 933.3.
  - At 190 and 245 s the runs take 15.4 and 19.8 d. The 14-day threshold is s_e = 172.8 s.
  - R at 213.8-275.6 s runs 59.4-76.6 h.
  - The cheap version costs 16,000/336,000 = 1/21 of the full one.
- **Seed-spread source.** Experiment-log 2026-09-26 gives BASE held-out accuracy
  0.6234 ± 0.0019 (8 seeds) (STUDY:44 ✓).

## Category A

**A1. Resolving power comes from a favourable cross-N proxy. The same-N measured spread
exists and shows the design cannot resolve its tolerance.** (STUDY:43-47, 124-132; §6.3 Q4)

- STUDY sizes the primary interval from the N=8 accuracy sd (0.19 pt → ±0.16 pt). STUDY:296
  forbids cross-N comparison.
- A same-N binary spread exists, and I recomputed it from
  `bnjettag/roc-results/r14/n64/W1A8-s{1,2,3}.npz` (keys y, score, meta; n = 260,000 each; all
  scores finite). Held-out accuracy is 0.6718 / 0.7264 / 0.6721: mean 0.6901, **sd 0.0314**
  (ddof = 1). W1A6 is 0.6984 ± 0.0168, and FP32 is 0.7911 ± 0.0030.
- This is archived (Round 14: no EBOPs target, no gate, 80/20, different recipe), so it is
  an order of magnitude only. It is still the same N and the same weight type. The N=8 number
  is neither.
- At sd = 3.14 pt the 8-seed half-width is 0.836 × 3.14 = **2.63 pt**, which is 2.6× the
  1.0-pt tolerance. The design would return "inconclusive" for any outcome within about
  ±2.6 pt of 78.4 %.
- STUDY:130-132 concedes this might happen, but nothing follows from it. [D13] says interim
  readouts "never gate anything", so the full 56 × 7,000 epochs run whether or not the
  design can resolve its question.
- Fix:
  - State resolving power at both bounds: the N=8 sd and the labelled archived N=64 sd.
  - Pre-register a consequence of the epoch-500 validation sd: a seed-count contingency, or a
    stop and report to Kai. This amends [D13] explicitly.
  - Add a labelled "archived context" row to the reference table: binary N=64 69.0 ± 3.1 %
    against FP32 79.1 ± 0.3 %, held-out accuracy, 3 seeds, n = 260,000, from
    `roc-results/r14/n64/`. STUDY:37 says only "none". The design's own prior shows a
    10-pt binary-vs-FP32 gap at N=64 before any EBOPs constraint, and the reader needs that
    to weigh a 1.0-pt tolerance.

**A2. The pre-registered tie-break is not what the code STUDY tells the engineer to copy
would run.** (STUDY:138-141, [D11], STUDY:59-60)

- STUDY says ties break in the order validation accuracy, then validation AUC, then −EBOPs,
  then −epoch, "exactly as `checkpoint_selection_key` ... does".
- `ablation.py:278-287` gives that order only when `cost_before_auc=False`.
- `ablation.py:421` sets `cost_first = bool(cfg.get('engram_study'))`, and `:422` passes it.
- Both source configs carry an `engram_study` block (`module: null`, but the dict is
  non-empty, so it is True): `const0922-a07-n64-s1-fast50-fp32.json` and
  `confirm0924-a07-n64-s2-e1000-5m.json` (checked: `'engram_study' in d` → True).
- A "field for field" copy therefore selects on accuracy, then **−EBOPs**, then AUC, then
  −epoch.
- With 7,000 checkpoints per run and accuracy quantized at 1/62,000, ties in accuracy on the
  plateau are plausible, so the order matters. As written, [D11] would be broken silently.
- Fix: state the order that will run, or add an [A] constraint that the generated configs
  drop `engram_study` (or override `cost_first`). Either way, add a unit test in PREFLIGHT
  that asserts the key order on a constructed tie.

**A3. The competing-group question has a non-empty, unjustified answer.** (§6.3 Q3;
STUDY:26-31, 38-40)

A group publishing this comparison next month would have two things this design lacks.

(a) **A seeded, validation-selected reference arm from Sun et al.'s own code on the same
test set.**
- The pipeline already runs on our infrastructure: `_attic/repro-chang/repro-chang/comparison.md:23`
  gives xfm-n64 80.56 % at 348k, single seed, selected on test (line 12).
- Without such an arm, the primary claim is a one-sample test against one number. The paper
  does not state that number's selection rule, and it comes from "several trained models"
  (§3), so it is possibly a best-of-k. [L1] names this but gives no reason for not closing it.
- A matched arm (8 seeds, the same selection rule, the same ROC-test) turns the headline into
  a two-sample comparison with its own interval. It also tests whether 79.4 is even the
  right bar: our single test-selected run of their code sits 1.2 pt above it.

(b) **A non-binary control in our pipeline.**
- STUDY:29-30 says "A miss measures what binary costs at that budget". [L2] lists several
  differences besides the weights:
  - per-channel against per-position activation widths (`model.py:181`
    `homogeneous_axis=(0,)`; ours is `heterogeneous_axis=(-1,)` in `qat.py:394`);
  - a norm-free ReLU block against a tanh LUT with batchnorm;
  - a different head;
  - a fixed 10-bit softmax.
- Without a control that changes only the weights, a miss cannot be attributed to binary.
- STUDY:28 calls the comparison "iso-cost". [L2] says equal EBOPs is not equal LUT, so it is
  iso-EBOPs.

Fix: add arm (a), or give a quota or other reason for omitting it. Either add a control for
(b), or reword the Bearing paragraph to say "a miss measures the gap between this binary
pipeline and their HGQ models at equal EBOPs", and replace "iso-cost" with "iso-EBOPs".

## Category B

**B1. The budget as written most likely lands in the "do not launch" branch.**
(STUDY:202-225, [D15])
- The 30 s and 60 s projections have no measured basis.
- The only measurement is `live-status.json`: 189.68 s per epoch for A02-N64 at batch 256,
  K = 2-3. That is 15.4-19.8 days for T_run, above the 14-day threshold.
- The runner also saves, reloads and predicts all of validation every epoch (`ablation.py:396-403`).
  That per-epoch overhead does not shrink with the batch.
- Fix: say which [D15] branch is expected. Present the cheap version, or waves, as the likely
  design rather than the fallback. Reconcile 10 pods with Kai's "a couple of pods" as a stated
  decision for Kai, not a flag inside the budget.

**B2. The comparand is conditioned on a post-hoc diagnostic, and the diagnostic misses the
paper's failure mode.** (STUDY:185-189, 442-446)
- The falsifier fixes 79.4 %. STUDY:188 says Deep Sets is "the right comparand" only if ours
  collapses. That invites re-choosing the bar after results: Linformer 79.8, Mixer 79.7, or
  our 80.56 run of their code.
- Deep Sets is also the lowest non-collapsed N=64 row.
- The paper's attention was constrained to ≥ 1 bit and still collapsed (§3), so a fraction of
  Q/K/V channels at 0 bits cannot detect that kind of collapse.
- Fix: the comparand is 79.4, unconditionally, and the text says why it was chosen over
  79.8. Define collapse operationally as well, for example by the attention-weight entropy
  on validation jets, or by the accuracy change when attention is replaced with the
  uniform mean.

**B3. Divergence, infeasibility and pairing are under-specified.** (STUDY:144-159, 176-183)
- A diverged run has no terminal epoch. Does its pre-divergence best-feasible checkpoint get
  evaluated on ROC-test and enter the seed mean? STUDY:150 records it, and STUDY:157 touches
  ROC-test "at its terminal epoch".
- For the paired gaps (A−B, A−D, A−R), which seeds count when one arm's seed is infeasible or
  diverged? A mean over feasible seeds only carries survivor bias, and that should be said.
- The optimizer-stability falsifier ("more A seeds diverge than D seeds") has no threshold,
  so 1 against 0 would falsify it. Pre-register a count or an exact test.

**B4. The one existing N=64 trajectory at 350k is treated as unavailable.**
(STUDY:478-481)
- `const0922-a07-n64-s1-fast50-fp32` (target 350,000) started
  (`screen-pod-logs.txt:95`, ARM_STARTED 11). Its outcome should be on PVC
  `/data/constituent-study-20260922/fp32` and in W&B group `constituent-20260922-fast50`.
- Recorded as a **disputed fact for the investigator**: did any N=64 screen arm reach
  EBOPs ≤ 350k within 50 epochs, and what was its minimum EBOPs? The evidence that settles
  it is the run's `activation_widths.jsonl` / `ebops_budget.json`, or the W&B summary
  `checkpoint_ebops` and `budget_met`.
- Fix: make this a PREFLIGHT [A] item beside [A7], not an "unanswered input".
- STUDY:480 says the N=64 confirmation "moved to 5M without a recorded reason".
  `project-context.md` records the 5M N=64 target as enforced from 2026-09-10, so the
  sentence overstates.

**B5. The rationale in [D1] is vacuous.** (STUDY:313-316) "The lowest of the plain N=64
transformer arms that preflight has traced" is true only because A07 is the only plain arm
traced. The other two traced configs, E02 (24,888,462) and E05 (25,023,758), are Engram
variants (`n64-full-preflight-result.json`). A06-N64 (d16, 4 heads, 2 layers, FFN 32; 7,867
parameters, `production-preflight.json`) is untraced and could have a lower static floor.
Fix: have [A7] trace A06 too, or drop the claim.

## Category C

- C1. Chang initializes widths at 7/7 bits (`run_train.py:76`, `get_model(..., 7, 7, 1e-8, ...)`),
  against "8-bit init" here. Label it a deviation or match it.
- C2. Arm E: Chang's xfm uses a key_dim of 16 per head (`model.py:195`); ours uses
  d_model/heads = 12. Note it in [D18].
- C3. Holm covers the five secondary gaps but not the family of three claims (primary,
  recipe, stability). State the family explicitly.
- C4. A vs F is declared unpaired. `matching_initialization` copies equal-shape kernels, so
  PREFLIGHT can compare `kernel_hashes` between A-s1 and F-s1. If everything but `pos_table`
  matches, pair them. An unpaired interval where init is shared is inflation (§6.3 Q4).

## Decision-label traceability

[D2], [D3], [D4], [D5], [D7], [D9] and [D18] are confirmed against source, with lines above.
[D11] conflicts with the code path (A2). [D13] conflicts with the resolving-power fallback
(A1). [D1]'s rationale is vacuous (B5). The rest are design statements with nothing to check
at STUDY.

## Competing-group question

The answer is (a) a seeded, validation-selected run of the reference code on the same test
set, and (b) a weights-only control. Neither is justified as omitted: A3.
