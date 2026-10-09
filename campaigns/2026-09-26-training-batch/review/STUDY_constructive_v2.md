# STUDY constructive review, v2 (re-review, iteration 2)

Campaign: `campaigns/2026-09-26-training-batch/`. Artifact: `STUDY.md` (711 lines; prose_lint score 0,
`review/STUDY_validators_v2.txt`). Reviewer: constructive-reviewer, 2026-09-27, fresh context.
Read: `docs/methodology/06-review.md` §6.1-6.5 and §6.8, `03-phases.md` Phase 1, `plan.md`,
`review/STUDY_arbiter_v1.md`, my `review/STUDY_constructive_v1.md`, `review/STUDY_investigation_350k.md`,
experiment-log (newest four entries), research-log 2026-08-04 and 2026-07-26 entries on
arXiv:2510.24784. Code traced: screen bundle `campaigns/2026-09-22-constituent-screen/study-code.tar.gz`
(extracted read-only to the session scratchpad; paths below relative to its `code/`), HGQ2 0.1.9 in
`.venv-hgq2` (the same version the pods pin, `hgq2==0.1.9`), and
`reference-code/HGQ2-examples/jsc150/model.py`. Other reviewers' v2 output not read.

## Status of my v1 findings

| v1 | finding | status in STUDY v1-revised |
| --- | --- | --- |
| A1 | "a miss measures what binary costs" | **Resolved.** Bearing paragraph (l. 44-51) says no arm varies weight type; iso-EBOPs not iso-cost; arm H and the in-house arm are follow-ups (l. 655-665). |
| B1 | tie-break differs from inherited config | **Resolved.** [A13] with an explicit override and a unit test (l. 561-567). |
| B2 | comparand choice | **Resolved** the arbiter's way (79.4 fixed unconditionally, 79.8 and 77.9 beside it, l. 271-279). |
| B3 | attention diagnostic conflates Q/K and V | **Applied, but my v1 wording was wrong for this quantizer**; see B1 below (self-correction). |
| B4 | epoch-matched A1000 − R | **Resolved** (l. 119-122, 253-254). |
| B5 | has any N=64 run reached 350k | **Answered** by the investigator: no, lowest 4,630,276 (W&B, seed 1, 50 epochs, not a result). STUDY records it (l. 578-589, 701-709) but does not draw the design consequence; see A1. |
| B6 | per-epoch overhead | **Resolved** ([A15], canary rule l. 381-384). |
| C1-C5 | fidelity table, AUC sensitivity, stale fields, memory prior, winner's curse | **Applied** (l. 124-142, [A19], [A18], l. 377-380, l. 234-237). The fidelity table misses two rows that matter most (A1). |

## What is done well (keep)

- [+] **Honest reframing.** The primary question is now descriptive, with "iso-EBOPs, not iso-cost"
  and an explicit sentence that the gap to Sun et al. mixes weight type with family, head, backend,
  standardization and selection (l. 44-51). This is the truthful version of the study.
- [+] **Resolving power at both bounds, with a consequence.** ±0.16 pt at the N=8 sd and ±2.63 pt at
  the archived same-N sd, the k = 6 factor (1.05·sd), and a pre-registered epoch-500 report to Kai
  (l. 187-200). Arithmetic rechecked: 2.365/√8 = 0.836, 2.571/√6 = 1.050, 0.5/1.05 = 0.48.
- [+] **Infeasible and diverged seeds** carry no accuracy, the survivor bias is named, paired gaps
  use seeds valid in both arms with the count stated (l. 214-229).
- [+] **Fidelity table** (l. 124-142) makes "verbatim" checkable field by field; it is the right
  instrument, and it is what exposed A1 when extended.
- [+] **[A12] failed-arm isolation, [A5] resume rollback, [A15] cadence, [A13] tie-break**: each
  names the code line it changes and the test that proves it.
- [+] **Investigator result integrated with its label** ("W&B-logged, seed 1, 50 epochs, not
  verified, not a result", l. 585-587) and the post hoc 5M reason stated plainly (l. 704-708).
- [+] **Winner's-curse numbers** (0.16 pt at n_val 62,000) and the per-run validation − held-out gap.

## Category A

### A1. By the pipeline's own EBOPs accounting, every 350k and 175k arm has a static floor above its target

- **Current state.** STUDY treats 350k feasibility as open: "[A7] gates this statically" and "the
  A·V term stays expensive unless V channels prune to 0 bits" (l. 695-700); the static floor is "unmeasured"
  (l. 545). The fidelity table (l. 126-142) has no row for the softmax output width or the activation
  overflow mode.
- **What the code says.**
  - Softmax output into A·V is a fixed, non-trainable 10-bit quantizer: `attn_iq` kif `k0=0, i0=1,
    f0=9`, `trainable=False`, `heterogeneous_axis=()` (`bnhgq2/qat.py:496-499`; config
    `softmax_out_bits 10`, `softmax_out_i 1`).
  - V enters `attn_ctx` through `stream_iq()` = `_free_act(ab, 6, axes=(-2,-1))`: kif, `k0=1`,
    `overflow_mode="SAT"`, one width per (head, channel), shared over particles (`qat.py:431-432,
    298-302, 500-502`).
  - In HGQ2 0.1.9, `bits = relu(i+f) + k` in SAT mode and `relu(i+f)` otherwise
    (`hgq/quantizer/internal/fixed_point_quantizer.py:93-97, 435-437`); in tracing, `k` is only
    OR-ed, never cleared (`:419-421`). A signed SAT channel therefore costs **at least 1 bit** in
    EBOPs, however far `i+f` falls.
  - `QEinsum._compute_ebops` = `einsum(eq, bits0, bits1)` summed (`hgq/layers/ops/einsum.py:61-64`).
    For `bhts,bshe->bthe` at T = 64, H = 4, E = 8: EBOPs(A·V) = 10 · 64 · 64 · Σ_{h,e} b_v(h,e)
    ≥ 10 · 4,096 · 32 = **1,310,720**.
  - Traced, not assumed: an isolated `QEinsum` with exactly these two quantizer configs, HGQ2 0.1.9,
    jax backend, `trace_minmax` on 256 random inputs, gives 1,310,720 at V `(i0,f0)` = (0,0) and at
    (2,−2), 2,621,440 at (1,0), 7,864,320 at (2,3) (scratchpad `ebops_av_check.py`). A review
    trace on the laptop, not a result; it confirms the formula.
  - Q·K adds ≥ 4,096 · 32 · 1 · 1 = 131,072 by the same rule (`qat.py:490-491`).
- **Consequence.** A07's static floor is at least about 1.44M EBOPs before input projection, W_o, FFN
  and head: 4.1× the 350k target of A, D, F, R and 8.2× the 175k of B. Arm E (H = 2, key_dim 12,
  24 V channels) has an A·V floor of 983,040, 2.8× its target. Only C (5M) is statically feasible.
  Under the design's own rule ("an arm whose floor is at or above its target is `STATIC_INFEASIBLE`",
  l. 541-545; "falsified before any GPU time", l. 266-267) the budget claim is falsified, the primary
  measurement A − 79.4 does not exist, the recipe claim has no content, and the method-atlas wave 0
  anchor (l. 53-56) has no accuracy. This also explains the screen plateau at 4.6M (investigation,
  A07 at β 1.8e-5) better than "a short run" does.
- **Why it is a Sun et al. fidelity gap and not physics.** Chang's attention uses HGQ2 defaults:
  softmax output quantizer `QuantizerConfig(place='datalane')` (`hgq/layers/attn/mha.py:69`), i.e.
  kif `overflow_mode='WRAP'`, learned, per-element (`hgq/quantizer/config.py:131-143`;
  `jsc150/model.py:187`, `homogeneous_axis=(0,)`). In WRAP mode bits = relu(i+f), which reaches 0.
  Two of our choices (fixed 10-bit softmax output; SAT with k = 1 on every signed channel) multiply
  the attention floor by about 10 and remove the 0-bit route. The study measures those choices
  more than it measures the recipe.
- **Improved state.** (1) Add two rows to the fidelity table: softmax output width (Chang learned,
  per element, WRAP; ours fixed 10 bits) and activation overflow mode (Chang WRAP, 0 bits reachable;
  ours SAT, k = 1, 1-bit floor per channel). (2) Move the [A7] floor out of PREFLIGHT and into STUDY
  now: a CPU trace of A07 and the E shape with every trainable width at its minimum, with the formula
  bits = relu(i+f) + k stated so the floor is not computed as "0 bits". Minutes of work. (3) Put the
  design response to Kai before PREFLIGHT, one of: (a) a softmax-output and overflow configuration
  that matches Sun et al. (trainable softmax output width, WRAP or a k-clearing quantizer), with the
  train = deploy concern that motivated SAT (`qat.py:292-293`) named as a limitation; the floor at a
  1-bit softmax output is about 131,072 for A·V plus 131,072 for Q·K, so even this is tight at 350k
  and must be traced; (b) keep our quantizers and move every target above the traced floor (a ladder
  that starts at the floor, say floor × 1.5, and ends at 5M), and drop the 79.4 % comparison, which is
  defined at 350k; (c) a Linformer-style key/value projection (their `xfmt`, k = 4), which cuts T·S
  from 4,096 to 256. Record whichever is chosen as a [D] with the traced floor beside it.
- **Why A.** A method failure the design would discover only after PREFLIGHT or the canary, with the
  evidence already in the code and the pinned library; and the primary question, as written, has no
  feasible answer under the stated accounting. §6.3 Q5: a known limitation must show an attempt.
- **Effort.** Low to confirm (full-model CPU trace); medium for option (a) or (c) (code); low for (b)
  (targets only, but it changes the question). Kai decision.

## Category B

### B1. The attention diagnostic, and my v1 wording, assume a 0-bit channel is silent; under SAT with k = 1 it is not

- **Current state.** "V at 0 bits removes the attention branch and leaves the residual path: a
  different model, not a Deep Set" and "Q/K at 0 bits gives constant logits" (l. 301-304, 697-700).
  This came from my v1 B3.
- **Problem.** With `relu(i+f) = 0` and k = 1 in SAT mode the channel still outputs two values,
  {−2^i, 0}: a live 1-bit signal, and it is what EBOPs charges for. "0 bits" in
  `activation_widths.jsonl` needs a definition (magnitude bits relu(i+f), or total bits with k). And a
  model whose attention branch is removed is a per-particle MLP (input projection + FFN), mean pooling
  and a head: that is a Deep-Set-class model (φ, pool, ρ), position-aware only through the learned PE.
  "Not a Deep Set" is wrong.
- **Improved state.** Define the width quantity used (state both relu(i+f) and k); report the Q/K and V
  fractions at relu(i+f) = 0 as "sign-only channels", not "0 bits"; keep the entropy number, which
  is the cleanest collapse measure; replace "not a Deep Set" with "attention branch reduced to sign-only
  values; the remaining path is Deep-Set-class". If A1's option (a) is taken, WRAP channels can reach
  true zero and the original wording becomes correct for them.
- **Effort.** Low.

### B2. The stability falsifier cannot survive its own multiplicity adjustment at the pre-registered threshold

- **Current state.** Falsified at "diverged A exceeds diverged D by at least 4 (for example 4 of 8
  against 0)"; the exact McNemar p is Holm-adjusted with the recipe p, and a decision whose adjusted p
  exceeds 0.05 is labelled "fails the multiplicity adjustment" (l. 258-262, 290-294).
- **Arithmetic.** Two-sided exact McNemar with b discordant pairs all one way: p = 2 · 0.5^b. At 4-0,
  p = 0.125; 5-0, 0.0625; 6-0, 0.031; 7-0, 0.0156. Holm over two tests needs the smaller p ≤ 0.025,
  so the threshold event 4-0 is always labelled "fails", and nothing short of 7-0 passes. (plan.md
  records the one-sided 4-0 value, 0.0625, and still left the p in the family.)
- **Improved state.** State the stability claim as a count rule only and report the exact p beside it
  as descriptive, outside the Holm family; or state the smallest reachable p per count in the
  Falsifier so the reader sees the rule's reach. Either way, one rule.
- **Effort.** Low.

### B3. Recoverable reference: the paper's per-class AUCs at N=64

- **Current state.** The reference table (l. 58-67) carries accuracy only, while the house metric is
  macro-OvR AUC and the two rank models differently (2026-09-16, cited l. 667-670).
- **Available.** Sun et al. Fig. 2 legends give five per-class OvR AUCs per model and N for Linformer
  and MHA; our arithmetic mean at N=64 is 0.9532 (Linformer) and 0.9428 (MHA)
  (`.claude/memory/research-log.md` 2026-08-04, https://arxiv.org/abs/2510.24784). Deep Sets AUCs are
  not published.
- **Improved state.** Add them to the reference table, labelled "read from figure legends, macro is our
  arithmetic mean, one model", and report per-class AUC distances to Linformer and MHA beside the
  accuracy distance. A threshold-free comparison where the paper gives one.
- **Effort.** Low.

### B4. Stage the commitment on dynamic feasibility

- **Current state.** After A1 is settled, whether any configuration actually reaches its target over a
  long schedule is still unknown: the only dynamic evidence is 50 epochs at LR 2e-4 with β unsaturated
  (investigation). The canary (10 epochs) tests timing, not feasibility; the epoch-500 readout comes
  after all 56 runs are launched.
- **Improved state.** Pre-register a feasibility pilot, or make the cheap version (l. 419-426) stage 1:
  A (and the A1-chosen variant) on two seeds to epoch 500 (one cosine cycle), validation-only, never
  quoted, with a stated rule ("if neither seed is at or under target by epoch 500, the ladder is
  re-targeted before the full launch"). Pre-registering the rule keeps it a design decision, not
  selection on results.
- **Why.** 336,000 run-epochs should not be committed on an unmeasured floor and an untested descent.
- **Effort.** Medium (one pod for 11-34 h at the recorded 83-245 s per epoch, a projection).

## Category C

- **C1. Ladder placement.** B at 175k is further below the floor than A. Once the floor is traced, place
  the budget ladder across the region where attention cost switches on (floor to 5M), where A − B
  actually measures something. Low.
- **C2. Pairing expectation.** After 14 restarts to LR 3e-3, same-seed trajectories in A, B, D may
  decorrelate, so paired intervals may not be narrower than Welch. Report the per-pair seed correlation
  of the accuracies so a reader sees whether pairing helped. Low.
- **C3. Expected recipe branch.** Given the screen (4.6M after 50 epochs at LR 2e-4) and the floor, R at
  LR 2e-5 for 1,000 epochs is expected infeasible at 350k; say so beside the "R infeasible" branch
  (l. 284-287). Low.
- **C4. One decision table for Kai.** Nine FLAG FOR HUMAN blocks (l. 629-693) plus the A1 decision; the
  document is 8,915 words. A single table at the top (decision, options, default, when needed) would
  make the launch gate a five-minute read. Low.
- **C5. Atlas anchor fallback.** `campaigns/2026-09-26-method-atlas/BRIEF.md` should name what the
  anchor becomes if arm A has no feasible checkpoint. Low.

## §6.3 answers

1. Conventions: complete, deviations flagged. Yes.
2. Reference table: present and sourced; missing the published AUCs (B3).
3. A competing group would have traced the static floor before designing a 350k ladder, and would have
   matched the softmax and overflow quantization of the reference (A1).
4. Uncertainties: honest on our side; resolving power stated with a consequence. The stability rule's
   reach is overstated (B2).
5. Limitations with attempts: the floor is deferred to PREFLIGHT although it is computable now (A1).
6. Context with a pull: not possible, stated (l. 442).
