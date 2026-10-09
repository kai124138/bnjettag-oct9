# STUDY constructive review, v3 (re-review, iteration 3)

Campaign: `campaigns/2026-09-26-training-batch/`. Artifact: `STUDY.md` (1,086 lines, 14,534 words;
prose_lint score 0, `review/STUDY_validators_v3.txt`). Reviewer: constructive-reviewer, 2026-09-27,
fresh context. Read: `docs/methodology/06-review.md`, `03-phases.md` Phase 1, `review/STUDY_arbiter_v2.md`,
my `review/STUDY_constructive_v2.md`, experiment-log (newest four entries), research-log entries on
arXiv:2510.24784 (2026-07-26, 2026-08-04, 2026-09-27 pin note). Evidence and code traced:
`code/evidence/static_floors_arms_s1.json`, `static_floors_trace_step2.json`, staged tree
`code/tree/bnhgq2/{ablation.py,ebops_calc.py,qat.py}`, HGQ2 0.1.9 (`.venv-hgq2`), HGQ2
0.1.10.dev17+g88ddffde2 (`.venv-chang`), `reference-code/HGQ2` at 88ddffd,
`_attic/repro-chang/repro-chang/comparison.md`. Other reviewers' v3 output not read.

## Status of my v2 findings

| v2 | finding | status |
| --- | --- | --- |
| A1 | static floor above every 350k/175k target; fidelity rows missing | **Resolved.** [D19], traced floors with every residual a named term (l. 210-249), fidelity rows (l. 196-201, 208), [A7] rewritten (l. 813-826). |
| B1 | 0-bit SAT channel is not silent; Deep-Set wording | **Resolved, with a correction I accept**: a SAT channel at its floor outputs exactly 0 and is billed 1 bit (l. 441-445); Deep-Set-class wording in place (l. 451-453, 1068-1069). |
| B2 | stability falsifier cannot survive Holm | **Resolved.** Count rule; two-sided McNemar outside Holm with its reach (l. 427-432). |
| B3 | Fig. 2 per-class AUCs | **Resolved** (l. 116, 409-412). Means rechecked: 0.9532, 0.9428. |
| B4 | stage the commitment on dynamic feasibility | **Resolved in structure** (canary plus epoch-500 pilot, l. 526-579), but the pilot's A rule is now satisfiable by a collapsed network; see A1. |
| C1-C5 | ladder placement, pairing correlation, expected R branch, one Kai table, atlas fallback | **Applied** (B on E at 250k [D6]; l. 295-297; l. 421-424; l. 938-947; l. 103-107). |

## What is done well (keep)

- [+] **Traced floors replace arithmetic, and the residuals are explained.** Every difference from the
  arbiter (+21,390 LUT table term; +16,384 SAT exp input) is a named term with a file and line. The
  current-quantizer init trace reproduces 24,816,782 exactly, so the tool is calibrated.
- [+] **The exp-input SAT choice is faithful to Chang's actual library, not only to our pin.** The
  research log (2026-09-27) warns that jsc150 HEAD needs a newer hgq2 than 0.1.9. I checked: the
  `softmax_exp_iq_conf` default `QuantizerConfig(place='datalane', overflow_mode='SAT')` is identical
  in 0.1.9 (`.venv-hgq2/.../hgq/layers/attn/mha.py:65`), in 0.1.10.dev17 (`.venv-chang/.../mha.py:68`)
  and in `reference-code/HGQ2` at 88ddffd (`src/hgq/layers/attn/mha.py:68`); so is the WRAP datalane
  softmax output (l. 69 / 72 / 72). The 343,053 floor is the right one for "Chang's code".
- [+] **B moved to E at 250k and paired with E by seed**: E − B is a clean target-only gap.
- [+] **[D20] certification uses the per-epoch sample** with the reason stated (a larger sample would
  fail PID-held checkpoints and become a second selection). That is the correct instinct.
- [+] **C′-s1 in the pilot** reads both [D19] branches with one GPU slot.
- [+] **Timing sourced per run and per N** (l. 484-493); the expected [D15] branch and the binding pod
  decision now follow from the right architecture.
- [+] **One Kai decision table** (l. 938-947), and the designer's E-primary recommendation is stated
  with its reason rather than silently applied.
- [+] **Resolving power** unchanged and still honest: 0.836·sd and 1.05·sd at k = 6, with the
  ±2.63 pt consequence at the archived N=64 spread and a pre-registered epoch-500 report.

## Category A

### A1. The budget claim and the pilot's A rule can be satisfied by a fully collapsed network

- **Current state.** Budget claim: "arm A reaches a feasible checkpoint at 350k in at least 6 of 8
  seeds" (l. 389-396). Pilot A rule: production waits only "if neither A pilot seed has a feasible
  checkpoint by epoch 500"; the median-EBOPs clause was dropped (l. 551-558). Recipe claim: "R
  infeasible while A meets the budget claim: the recipe claim is supported on feasibility" (l. 417-419).
- **Problem.** Under [D19] the A07 0-bit floor is 343,053 ≤ 350,000
  (`code/evidence/static_floors_arms_s1.json`, `zero.total`). The 0-bit state has every activation
  width at `relu(i+f) = 0`, so under WRAP every channel outputs 0 ([A20] unit test) and the logits are
  the head bias: a constant classifier. That state is a feasible checkpoint. A PID pushing β up at LR
  3e-3 restarts can reach it or its neighbourhood, and the ≤ target filter accepts it. So:
  (i) the budget claim can be "supported" by a model that does not tag; (ii) the pilot rule, now
  feasibility-only, passes on the same model and tells Kai nothing about whether A works; (iii) the
  recipe claim can be "supported on feasibility" because A collapses faster than R, which is the
  opposite of what "the recipe beats ours" means. This is a pass condition that is close to
  tautological at this headroom (6,947 EBOPs, 2.0 % of target). It became A in this iteration because
  the traced headroom is a third of the arbiter's 23,344.
- **Improved state.**
  1. Pre-register a **non-degeneracy condition** for "feasible" in the budget claim, the recipe
     feasibility branch and the pilot: EBOPs − 0-bit floor > 0 (at least one live channel) **and**
     validation top-1 accuracy above a stated trivial baseline (for example the majority-class
     fraction of the validation split plus 5 binomial SE, or a value the designer fixes now).
     Checkpoints failing it are reported as "feasible, degenerate", counted separately, and never
     carry the arm's accuracy.
  2. Beside every EBOPs number, report **EBOPs above the 0-bit floor** (A07: EBOPs − 343,053;
     E: − 171,526) as the model's usable budget.
  3. In the pilot, report the validation accuracy of each run's best-feasible-as-of-500 snapshot
     (validation only, never quoted, selects nothing). This keeps the arbiter's intent (the pilot
     does not rank arms on accuracy) while making the A readout informative; the A rule becomes
     "neither A pilot seed has a non-degenerate feasible checkpoint".
- **Why.** §6.3: a pass condition that a constant model meets is a tautological validation. The fix
  is a sentence per rule and changes no run.
- **Effort.** Low.

### A2. The whole A07-at-350k family (A, D, F, R) is floor-bound; moving only the budget claim to E leaves the recipe, stability and PE comparisons without content

- **Current state.** The primary-architecture row (l. 943, 962-978) keeps A07 primary by default,
  recommends E, and says that if Kai picks E "the recipe claim (A − R) and the stability claim (A − D)
  stay on A07, because D and R are A07 (adding D and R on E is +16 runs, a Kai option)". A − F stays on
  A07. l. 78-80: "6,947 buys at most three such 1-bit channels in the whole network".
- **What the traced numbers imply** (`static_floors_arms_s1.json`, `one.per_layer`): at 1 bit, one input
  channel of every T-scaled layer costs 2,048 (input_proj 6,144 / 3; Wq, Wk, Wv, Wo, fc1, fc2
  65,536 / 32); Q·K and A·V at 1 bit are 131,072 each. Head channels are cheap (head_fc1 1,024 / 32 =
  32 each; head_fc2 160 / 32 = 5). So a feasible A07 at 350k can afford roughly: the three input
  features at 1 bit (6,144), nothing in attention or the FFN (V at 0 bits, fc1 at 0 bits), and about
  25 head input channels at 1 bit. The network is 1-bit features → linear projection + PE → mean pool
  → small head, with ~98 % of its EBOPs billed to a softmax whose inputs are zero. (Correction for
  l. 79-80: "three channels in the whole network" is true for T-scaled layers only; the head adds
  cheap channels. The conclusion stands.)
- **Consequence.** A, D, F and R at 350k are all forced into the same near-trivial structure, so:
  A − R (the only p-valued claim) is expected flat, or decided by which arm collapses first (A1);
  A − F measures nothing, because a learned PE added before a mean pool with no live nonlinearity
  after it is a constant; A − D divergence counts remain meaningful but describe an optimizer on a
  near-empty model. Moving only the budget claim to E leaves 32 of 56 runs (A, D, F, R) spending up
  to 7,000 epochs on this structure.
- **Improved state.** Make the architecture choice apply to the **350k ladder as a unit**. Default
  proposal for the Kai row: A, D, F-equivalent and R run on the chosen primary architecture; this is a
  **move, not an addition** (zero net runs), so "+16 runs" should read "0 runs if D and R move". Keep
  A07 at 350k as one descriptive arm (8 runs, or 4) that records the floor-bound result, and keep C
  (A07 at 5M), where A07 has room. If E is primary, F's role (PE split of E) needs restating, because
  E has no PE; a candidate is E + learned PE, if Kai wants the PE question at all.
- **Why.** A design whose secondary claim is flat or decided by collapse before any run is not
  resolving power the seeds can buy back. The atlas (method-atlas wave 0) inherits the same problem
  through its anchor.
- **Effort.** Low for the text and generator change; Kai decision (it rides on the existing row).
  If the arbiter prefers B, it should at least block production of D, F and R on A07.

## Category B

### B1. The evidence for E-primary is already in the reference table and is not used

- **Current state.** The recommendation rests on headroom (178,474 against 6,947) only (l. 962-968).
- **Available.** REPRO-CHANG `xfm-n64` is Chang's h=2 model and reached 80.56 % at 348k EBOPs
  (`_attic/repro-chang/repro-chang/comparison.md:23`; single seed 42, selected on test, unverified,
  HGQ weights). Its softmax floor is the same per-head term as E's (the softmax EBOPs do not depend on
  key_dim), so a 2-head model at 350k has been seen to tag at about 80 % on our infrastructure with
  about half the budget left for φ and ρ.
- **Improved state.** Quote it beside the recommendation with its label ("single seed, test-selected,
  unverified, HGQ weights; context, not a comparand").
- **Effort.** Low.

### B2. A one-head arm matches the paper's text and has about 264k headroom

- **Current state.** [D18] notes the paper says one head and Chang's code uses h=2; no arm has H = 1.
- **Arithmetic.** The traced floors are additive per head: E 171,526 = 2 × 85,763; A07 343,053 =
  4 × 85,763.25. A one-head N=64 model therefore has a softmax floor of about 85,763 and about 264,237
  EBOPs of headroom at 350k (reviewer arithmetic from two traced points, a projection, not traced).
  The builder derives the head dimension as `E = D // H` (`code/tree/bnhgq2/qat.py:391`), so
  `n_heads 1` on d32 or d24 is a config change.
- **Improved state.** Add "one head (paper's text)" as an option in the primary-architecture row, and
  add its floor to [A7]'s trace list so PREFLIGHT records it. It is the cheapest route to room at 350k
  without new code (the Linformer option needs code).
- **Effort.** Low (trace and text); an arm would be Kai's call.

### B3. [D20] is not in the staged tree, and its dynamics and cost differ from Chang's

- **Current state.** The staged runner traces `sample = xt[:256]` (`code/tree/bnhgq2/ablation.py:450`)
  twice per epoch on the live model and on the reloaded candidate (`:515`, `:521`), each via
  `trace_minmax` with its default `reset=True` (`hgq/utils/minmax_trace.py:38`). STUDY l. 498-503 asks
  ml-engineer whether the second trace can be replaced by a comparison of stored widths.
- **Observations.**
  - Cost: under [D20] each trace is a forward pass over 558,000 jets at batch 2,048 (273 batches);
    two of them are comparable to the 200 training steps at batch 2,790 (forward plus backward). The
    9.1 d prior predates this.
  - Dynamics: in training mode a WRAP-trainable quantizer returns rounded, unwrapped values and moves
    `i` by `max(i − i_decay_speed, new_i)` per batch (`fixed_point_quantizer.py:402-413`); a
    `reset=True` trace on the live model then pins `i` to the full-split maximum at every epoch.
    Chang traces once after training. `i_decay_speed` is not set anywhere in `bnhgq2/` (grep), so
    the default applies and is unrecorded.
- **Improved state.** Make "one full-split trace per epoch; the reload check compares stored `i`, `f`,
  `k` and the stored EBOPs, no second trace" the pre-approved default, not a question. Add a fidelity
  row "WRAP range update during training: per-batch `i` tracking plus a per-epoch reset trace on the
  live model (ours) against per-batch tracking and one trace after training (Chang)", and record
  `i_decay_speed`. Or trace a copy so training dynamics stay Chang's; PREFLIGHT states which.
- **Effort.** Low to state; medium if the trace moves to a copy.

### B4. Honest framing of "350k against 350k"

- **Current state.** A − 79.4 and the per-class AUC distances are presented at "matched native HGQ2
  EBOPs" (l. 91-97, 398-412).
- **Problem.** At the budget, Sun et al.'s Deep Sets (HGQ) spends its 350k on φ and ρ; A07 spends
  343,053 of it on a softmax that, in any feasible state, operates on (near-)zero scores. A reader
  will take "same EBOPs" as "same capacity".
- **Improved state.** One sentence beside the distance in every outcome: "of A's 350k EBOPs, X are the
  softmax floor; the usable budget is 350,000 − X", with the E and one-head equivalents if they run.
- **Effort.** Low.

## Category C

- **C1. Parameter count.** Under [D19] A07 has 61,951 parameters against 12,788 on the current
  quantizer (`static_floors_trace_step2.json`), mostly per-element softmax-output widths (4 × 64 × 64
  elements, `i` and `f`). State it so PREFLIGHT's count is not read as a bug. Low.
- **C2. Upstream file.** `campaigns/2026-09-23-confirmation/UPSTREAM_FEEDBACK.md` still carries 1.6 %
  and 4,559,008 (STUDY notes it, l. 235-236); list the edit to 1.1 % and 4,580,398 as a cascade item.
  Low.
- **C3. Readability.** "Amended after [A7] trace, 2026-09-27" appears 31 times.
  The change log already records provenance; keep the tag on the tables and the [D]/[A] entries,
  drop it from running prose. The document is 14,534 words; the launch gate needs the decision table
  and the arms table, which are good. Low.
- **C4. Figure ladder.** If A07 at 350k is kept only as a descriptive arm (A2), its rung on the A07
  ladder should show "EBOPs above floor" on a secondary axis or in the label, so the plot does not
  show 350k and 5M as comparable capacities. Low.

## §6.3 answers

1. Conventions: complete, deviations flagged. Yes.
2. Reference table: complete; the REPRO-CHANG h=2 row is under-used (B1).
3. A competing group would size the architecture to the budget before launch: at 350k, four heads
   leave 2 % headroom; two heads 51 %; one head about 75 % (B2, projection).
4. Uncertainties: honest; resolving power stated with a consequence.
5. Limitations with attempts: the floor problem was attacked properly ([D19]); what remains is a
   degenerate-feasibility loophole (A1) and a design that leaves 32 runs on a floor-bound architecture
   (A2).
6. Context with a pull: not possible, stated.

## Disputed facts for the investigator

None blocking. The one-head floor (B2) is a two-point projection; [A7] traces it at PREFLIGHT.
