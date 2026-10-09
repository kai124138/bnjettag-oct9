# STUDY arbiter v3: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-27. Artifact `STUDY.md` (1,086 lines, amended after the [A7] trace),
`plan.md`, `code/` and `code/evidence/`. Reviews v3: `STUDY_physics_v3.md`, `STUDY_critical_v3.md`,
`STUDY_constructive_v3.md`. Validators `STUDY_validators_v3.txt`: `prose_lint` score 0, no A lines;
no plot-validator file (STUDY has no figures). Earlier arbiter `STUDY_arbiter_v2.md`. Read
`docs/methodology/06-review.md` §6.1-6.8. Iteration **3** of the STUDY panel (warn tier).

## Independent checks made by the arbiter

- **Traced per-layer floors** (`code/evidence/static_floors_trace_step2.json`, entries `a07-chang`,
  `e-chang`, fields `zero.per_layer`, `one.per_layer`; CPU, synthetic sample, not results):
  - A07 0-bit 343,053 (all softmax), 1-bit-alive 1,005,741: input_proj 6,144, Wq/Wk/Wv/Wo/fc1/fc2
    65,536 each, scores 131,072, ctx 131,072, head 1,024 + 160. Headroom at 350k 6,947.
  - E 0-bit 171,526, 1-bit-alive 619,198: input_proj 4,608, Wq/Wk/Wv/Wo 36,864 each, fc1/fc2 49,152,
    scores 98,304, ctx 98,304. Headroom at 350k 178,474 (25.7 × A07's).
- **Critical A1 bound, checked.** A07 per 1-bit channel: input_proj 6,144/3 = 2,048; Wq input
  65,536/32 = 2,048; one Q·K (h, e) pair 131,072/32 = 4,096 (stream per (h, e), patched
  `qat.py:486-487`). Data-dependent logits need ≥ 8,192 > 6,947. **Confirmed: every feasible A07
  checkpoint at 350k has data-independent attention by construction.** The same path in E costs
  1,536 + 1,536 + 4,096 = 7,168, 4 % of E's headroom.
- **Arbiter v2's default no longer holds.** v2 kept A07 primary on an arithmetic headroom of 23,344,
  which fits a ~12,300-EBOPs attention path; the traced 6,947 does not. This arbiter reverses that
  default (below).
- **Paper's "at least one bit" (physics B1 vs arbiter v2, case 4).** pdftotext -layout of the cited PDF
  l. 168-170: "the attention layer which is constrained to at least one bit to disable pruning";
  l. 175-176: MHA-64 collapsed "despite the bitwidth constrained to at least one bit"; Fig. 3
  caption l. 226-228: "the distribution of the **weight** bitwidths ... For the attention layers,
  the bitwidths are constrained to at least one bit". `jsc150/model.py:193` carries a commented-out
  `QuantizerConfigScope(place='datalane', default_q_type='kbi', bc=Min(1))` directly above the
  attention input. **Finding: ambiguous (weights stated in the caption; activations plausible from
  the text and the commented code). v2's "weights only" was too confident; STUDY's fidelity row
  "not stated" (l. 196) is wrong.** Arbiter sums of traced per-layer terms under a datalane
  reading:

  | arm | narrow reading (Q·K and A·V streams ≥ 1 bit) | full reading (plus Wq, Wk, Wv inputs) | vs 350k |
  | --- | ---: | ---: | --- |
  | A07 | 605,197 | 801,805 | infeasible either way |
  | E (d24, h 2) | 368,134 | 478,726 | infeasible either way |
  | E1 (d24, h 1; projection, per-head softmax 85,763) | ≈ 282,371 | ≈ 392,963 | feasible only under the narrow reading |

  Under the paper's rule read as a datalane constraint, **no arm of the 56-run design is feasible at
  350k**; only the E1 projection, under the narrow reading, could be. That is a zero-GPU finding, not a GPU variant.
- **[D20] not staged.** `code/tree/bnhgq2/ablation.py:450` `sample = xt[:256]`; `compute_ebops`
  twice per epoch at `:515`, `:521` (reset trace on the live model). Physics B3, constructive B3
  confirmed.
- **Upstream file (critical C3 vs constructive C2, case 4).**
  `campaigns/2026-09-23-confirmation/UPSTREAM_FEEDBACK.md:13-23` carries 4,580,398, 1.092 and 1.1 %.
  Critical is right; STUDY l. 235-236 is stale; constructive C2 is dismissed on that evidence.
- **Arithmetic.** 0.836 · √2 · 3.1446 = 3.72 pt (physics B6). McNemar reach, t-factors, timing
  and Fig. 2 means were recomputed by two reviewers and agree with STUDY; not repeated.

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | "Feasible" is satisfiable by a collapsed network: every arm's 0-bit floor is below its target under [D19] (A07 343,053, E 171,526), the 0-bit state is a constant classifier (WRAP zero outputs 0, [A20] test), and the budget claim, the pilot A rule (feasibility only since the 3× clause was dropped), the recipe "supported on feasibility" branch and the epoch-500 sd gate all pass on it. Needs a pre-registered non-degeneracy condition. | phys A1, cons A1 | A, A | **A** | Case 1. A pass condition a constant model meets is a tautological validation (§6.3, §6.7 trigger pattern), fixed at design. Applies to every arm, not only A07. |
| 2 | The A07-at-350k family (A, D, F, R: 32 of 56 runs; A, D, F are 168,000 of the 336,000 Chang-schedule run-epochs, plus R's 8,000) is floor-bound: attention cannot be data-dependent (≥ 8,192 > 6,947), ≤ 3 per-constituent input bits; budget, recipe, stability and A − F are largely fixed before training. STUDY says "may"; atlas BRIEF says "dead by construction". E-primary option in the FLAG leaves D and R on A07. | crit A1, phys A2, cons A2 | A, A, A | **A** | Case 1, verified above. The design as defaulted cannot answer its own question; §6.4 "question falsifiable" fails for three claims. |
| 3 | Fidelity row misstates the paper: the ≥ 1-bit attention constraint is stated (l. 169, 176, Fig. 3); under a datalane reading A07 and E are infeasible at 350k. | phys B1 | B | **B** | Case 4 settled above: stated but ambiguous. Handled as a corrected fidelity row, a zero-GPU static finding with the table above, and an [L2]/[L9] sentence. Not the default, because Kai asked to replicate the code, which has the scope commented out. |
| 4 | Iso-EBOPs against Deep Sets hides a softmax tax (A07 343,053 = 98 % of 350k; E 171,526 = 49 %); state usable budget beside every distance to 79.4. | phys B2, cons B4 | B, B | **B** | Case 1. One sentence per distance; also the usable-budget column in #1. |
| 5 | [D20] not in the staged code (`ablation.py:450` 256 jets); per-epoch `reset=True` trace on the live model changes training dynamics relative to Chang (one trace after training); `i_decay_speed` unrecorded; cost of two 558k traces unmeasured. | phys B3, cons B3 | B, B | **B** | Case 1, verified. "ml-engineer is implementing it" is not evidence. The dynamics point is a fidelity row, not a PREFLIGHT nit. |
| 6 | Stability claim can only fail to falsify at 8 seeds; never write "safe". | phys B4 | B | **B** | Case 3; correct (3-0 does not falsify). Wording. |
| 7 | "Recipe supported on feasibility" when R is infeasible is a width-decay-speed statement, not "beats". | phys B5 | B | **B** | Case 3; reinforced by #1. Wording plus the non-degeneracy condition. |
| 8 | Resolving power for paired gaps rests on an unmeasured sd_diff; at zero correlation the resolvable paired gap at the archived spread is ≈ 3.7 pt. | phys B6 | B | **B** | Case 3; arithmetic checked (3.72). One sentence. |
| 9 | REPRO-CHANG xfm-n64 (h 2, 80.56 % at 348k; single seed, test-selected, HGQ weights) is the strongest context for E and is unused in the FLAG. | cons B1, phys C5 | B, C | **B** | Case 2: sided with B because it is one labelled sentence that bears on a Kai decision; its weakness (weights prune) must be stated with it. |
| 10 | A one-head arm matches the paper's text; per-head softmax floor additive (85,763), headroom ≈ 264,237 at 350k; config-only (`qat.py:390`). | cons B2 | B | **B** | Case 3. Also the only configuration that may be feasible under the narrow ≥ 1-bit reading (#3). Projection; needs an [A7] trace before it is written as a number. |
| 11 | STUDY l. 229 "350k and 175k" (no 175k arm remains). | crit C1 | C | C | |
| 12 | l. 212 "to be confirmed by CPU trace" (done); [A14] l. 852 lists "fixed 10-bit softmax output" (wrong under [D19]). | crit C2 | C | C | |
| 13 | l. 235-236 stale sentence on `UPSTREAM_FEEDBACK.md`. | crit C3 (cons C2 contradicted) | C | C | Case 4: file read, critical right. |
| 14 | Two init EBOPs (13,613,261 and 13,182,317): name the sample beside each. | crit C4 | C | C | |
| 15 | Evidence JSON arm B stale; C′ "one" column equals "zero". | crit C5 | C | C (becomes a gate under fix 5) | |
| 16 | Inert `calib_n 8192` in the arms field list. | crit C6 | C | C | |
| 17 | Name arms in ROC figure; paired-gap panel; pre-register attention-state and val − held-out figures; parameter count 12,788 vs 61,951; GPU-class column; [A17] all 8 seeds as a gate. | phys C1-C4, C6; cons C1 | C | C | |
| 18 | "Amended after [A7] trace" appears 31 times in running prose; ladder rung for a floor-bound arm needs "EBOPs above floor". | cons C3, C4 | C | C | |

## Earlier A and B findings (arbiter v2), by name

| v2 # | finding | status | evidence in STUDY v3 |
| --- | --- | --- | --- |
| 1 (A) | static floor above 350k/175k under our quantizer | **resolved** | [D19] l. 750-764; traced table l. 210-237; falsifier l. 391-395; FLAG l. 949-960 |
| 2 (A) | fixed softmax internals, half-fix risk | **resolved** | [D19]/[A20] l. 889-903; fidelity rows l. 196-199; LUT term named l. 222-227 |
| 3 (A) | matched A07 pruned by construction; pre-register floors | **resolved as written, superseded by new #2** | l. 74-82, [A7] l. 813-826; traced headroom 6,947 turns "almost fully pruned" into "attention data-independent by construction" |
| 4 (A) | timing mis-sourced | **resolved** | l. 484-506 cite 100.09 s, file and field; 83.53 s and 189.68 s relabelled (l. 492-493); expected branch "fits 14 days" (l. 495) |
| 5 (B) | stage the commitment with a pilot | **resolved in structure, reopened in part by new #1** | pilot l. 526-579; the dropped 3× clause is correctly argued (l. 553-556) but leaves a feasibility-only rule a collapsed model passes |
| 6 (B) | [D13] undefined at k < 2; far-from-budget report | **resolved** | l. 313-316, 365-369, [D13] l. 733-738. The sd gate inherits new #1 (needs the seed-mean beside the sd) |
| 7 (B) | stability count rule, McNemar sidedness | **resolved** | l. 427-432; wording issue is new #6 |
| 8 (B) | width quantity, Deep-Set wording | **resolved** | l. 437-456 |
| 9 (B) | arm B | **resolved** | [D6] l. 708-714 (E at 250k, paired with E) |
| 10 (B) | survivor bias to A − 79.4 | **resolved** | l. 400-401 |
| 11 (B) | arm H inherits [D19] | **resolved** | l. 1012-1013 |
| 12 (B) | Fig. 2 per-class AUCs | **resolved** | l. 116, 409-412 |

## Regression triggers (§6.7), checked independently

No results exist; STUDY is the origin phase.
- selection on held-out, or changed after results: **not met** (validation only, l. 318-336). The new pilot accuracy readout must not move the primary default (fix 3).
- validation vs ROC-test AUC > 0.01: not met (no numbers).
- single-seed / < 100-epoch / lab-pod headline: not met (screen, REPRO-CHANG labelled context).
- cross-N, input-set, split or schedule series: not met.
- gap < seed sd with < 3 seeds: not met.
- reload > 1e-7, TF32: not met (confound 9).
- EBOPs not remeasured / final-epoch cost mixed: not met; certification l. 330-336. [D20] must be implemented as written (fix 5) or this becomes a PREFLIGHT trigger.
- binary layer > 2 values: not met (gate committed).
- DSP / C-sim / C-synth: not applicable ([L7]).
- per-class AUC < 0.7 hidden: not met.
- byte-identical arms / different `y`: not met ([A11]).
- failed validation or **tautological validation**: **not met, fixed at design** (new #1: the feasibility test passes trivially on a constant classifier; closed by the non-degeneracy condition before any run).
- [D] replaced without dated amendment: not met. Fix 2 changes [D1]/[D6]/the arms table and must be a dated [D21].
- outward mismatch: not applicable.

## Disputed facts for the investigator

None blocking. The paper's ≥ 1-bit rule is ambiguous in the source itself and is handled by
recording both readings (#3), not by an investigation. The one-head floor is a projection that
ml-engineer traces (fix 6).

## Dismissals

- Constructive C2 (UPSTREAM file still stale): dismissed on evidence (`UPSTREAM_FEEDBACK.md:13-23`).
  Cost 0; it does not change the conclusion; nothing to do.

## Motivated-reasoning check

- The STUDY states that A at 350k "is close to a test of the floor" and recommends E, yet keeps
  A07 as the default and leaves D and R on it. Deferring a known design defect to Kai's row is the
  "later" pattern: it changes the verdict, so it blocks now.
- Dropping the 3× pilot clause was right, but it left a feasibility-only rule that a dead network
  passes; the only pass/fail gates would then agree hardest when the model measures nothing.
- Nothing inflates an interval. The survivor bias and the unmeasured sd_diff are the two places
  where precision could read better than it is; both are carried (v2 #10, new #8).

## Question 2: E primary as the default tonight

**Yes, as the STUDY default; Kai confirms at the launch gate; not an ESCALATE.** Reasons:
(i) nothing irreversible happens before Kai returns (production is already held on [D19], primary
architecture and pod count; the pilot is one pod inside "a couple of pods"); (ii) E is our binary
pipeline sized as Chang's xfm, which is within "replicate his code" and "change the architecture
for some of them"; (iii) the arbiter may not PASS a default whose three claims are fixed by
construction. The Kai row must state plainly that the default now puts **40 of 56 runs** on the
changed architecture (a broader reading of "some of them"), with the alternative "A07 primary, as
v2" and its consequence (claims are feasibility probes of the floor). The switch is decided on
static headroom now and **never on pilot accuracy**.

## Verdict

**ITERATE** (STUDY panel, iteration 3 → fixer, then re-review v4). **Warning: third iteration.**
No validator A lines. Two A clusters (#1, #2), eight B (#3-#10). Kai is not needed for the fixes;
the fixer owns text and generator changes, the experiment-designer owns fix 2 if the fixer
returns CANNOT RESOLVE.

Required fixes, in priority order:

1. **(#1, A) Non-degeneracy condition, every arm, dated in the change log.** A checkpoint is
   *feasible* only if (a) traced EBOPs ≤ target, (b) EBOPs − that arm's traced 0-bit floor > 0, and
   (c) validation top-1 accuracy > p_maj + 5 · √(p_maj (1 − p_maj) / 62,000), where p_maj is the
   majority-class fraction of `y_val`, computed at PREFLIGHT from the gated split and fixed before
   the canary (the formula is fixed now; no threshold is set after pilot numbers exist). Failing
   (b) or (c) with (a) is reported as "feasible, degenerate", counted separately, never carries an
   accuracy. Apply it to the selection rule (l. 320), the budget claim (l. 389-396), the recipe
   branches (l. 417-420), the epoch-500 sd gate (report the seed-mean validation accuracy beside
   the sd; to Kai if the mean fails (c)) and the pilot rules. Beside every EBOPs number report
   **EBOPs above the 0-bit floor** (usable budget).
2. **(#2, A) Move the 350k ladder as a unit onto E; new dated [D21], arms table and comparisons
   rewritten.** Default: primary **A = E architecture at 350k** (d24, 2 heads, 1 block, FFN 32, no
   PE). **D** (our optimizer) and **R** (our recipe) move to E; **B** stays E at 250k (so A − B is
   the target-only rung); **F** becomes E + learned PE (so A − F is the PE knob on the live model;
   `pos_enc_none_consume_rng` on every no-PE E-family config, [A17] re-run at 8 seeds) or is cut
   first; **C** stays A07 at 5M; old A becomes one descriptive arm **A07-350** (A07 at 350k, 8
   seeds, paired with C for the A07 target rung, labelled "our A07 at the paper's budget:
   attention data-independent by construction"). Net 56 runs, 7 arms, pods unchanged (seed block
   K = 6: A, B, C, D, F, A07-350; R on 2 pods). State in Question, Bearing and "Where I am not
   sure" as a fact: at 350k a feasible A07 checkpoint cannot carry data-dependent attention
   (≥ 8,192 needed, 6,947 available) and has ≤ 3 per-constituent input bits; pre-register that
   expected attention state for A07-350. Restate the expected R branch for R on E (the old
   argument came from the A07 screen). Update the Holm set (C − A07-350, A − B, A − D, A − F,
   A − A07-350 as a labelled package) and the ladders figure. Kai row: default E-primary (40 of 56
   runs on the changed architecture), alternative A07-primary with the consequence stated.
   Cascade: `experiment-log.md` stub, `plan.md`, generator (ml-engineer), note to the atlas owner
   that the anchor default is E (BRIEF l. 30-50 already says so).
3. **(#1, #2, #10, A/B) Pilot composition.** Pilot configs regenerate under fix 2 before the canary (the v3 pod must not ship). One pod, K = 6, epoch 500, validation only:
   **A-s1, A-s2** (E architecture), **D-s1** (E), **A07-350-s1**, **C′-s1**, and **E1-s1** (E with
   `n_heads 1`, pilot-only like C′) if fix 6 traces its floor before the canary, otherwise
   **B-s1**. Rules: production waits for Kai if neither A seed has a non-degenerate feasible
   checkpoint; report per run the fraction of headroom used, attention state and best-feasible
   validation accuracy (descriptive, never quoted, selects nothing, and **does not switch the
   primary default**). A07-350-s1 reports whether its attention state matches the pre-registered
   prediction.
4. **(#3, B) Paper's ≥ 1-bit rule.** Correct fidelity row l. 196 ("stated for the attention layer;
   Fig. 3 caption says weight bitwidths; `jsc150/model.py:193` datalane `bc=Min(1)` commented
   out; ambiguous"). Add a zero-GPU static finding with the table above (A07 605,197 / 801,805;
   E 368,134 / 478,726; E1 projection ≈ 282,371 / ≈ 392,963) and the sentence "binary weights reach
   350k at N=64 here only because attention may prune to 0 bits, which the paper's protocol may not
   have allowed" in [L2] and beside A − 79.4. Kai row: "paper-rule variant" as an option (only E1
   under the narrow reading could run it at 350k), not the default.
5. **(#5, B) [D20] as a named PREFLIGHT gate** citing `ablation.py:450, 515, 521`: default one
   full-split trace per epoch, reload check compares stored `i`, `f`, `k` and EBOPs (no second
   trace); fidelity row "WRAP range update: per-batch `i` tracking plus per-epoch reset trace on
   the live model (ours) vs one trace after training (Chang)"; record `i_decay_speed`; canary
   measures the trace's share of s_e. Regenerated `static_floors_arms_s1.json` for the amended
   arm set is a PREFLIGHT gate.
6. **(#10, B) Trace before PASS (ml-engineer, CPU, minutes):** [A7] floors of E1 (d24, h 1):
   0-bit, 1-bit-alive, and both ≥ 1-bit readings; confirm per-head additivity. Required before E1 is
   written into the pilot; if not traced, drop E1 from the pilot (B-s1 takes the slot) and keep it
   as a Kai option with the label "projection".
7. **(#4, B)** Softmax tax as a number beside every distance to 79.4 (A07 98 %, E 49 %).
8. **(#6, #7, B)** Stability outcome "not falsified at this resolution (8 seeds)", never "safe";
   recipe-on-feasibility outcome "R did not reach 350k non-degenerately in 1,000 epochs" with
   A1000 and D1000 feasibility beside it, never "beats".
9. **(#8, B)** Beside the resolving power: at zero pair correlation sd_diff ≈ √2 · sd, so the
   resolvable paired gap at the archived spread is about 3.7 pt; "flat" reads "cannot resolve
   below ~3-4 pt".
10. **(#9, B)** Quote REPRO-CHANG xfm-n64 in the primary-architecture FLAG with its full label and
    the caveat that its weights prune.
11. **C items #11-#18**, apply before commit.

Iteration count: this is 3 (warn). The next ITERATE would be 4; at 5 the arbiter warns strongly.
