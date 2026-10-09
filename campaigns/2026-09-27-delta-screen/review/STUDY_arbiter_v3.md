# STUDY arbiter v3: 2026-09-27-delta-screen (Delta wave 2)

Arbiter, fresh context, 2026-09-27. Re-review, iteration n = 3.
Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (1,369 lines, commit f00fd93) with `plan.md`,
`budget.py`, `screen_null.py`, `rank_sim.py`. Inputs read: `review/STUDY_physics_v3.md`,
`review/STUDY_critical_v3.md`, `review/STUDY_constructive_v3.md` (+ `constructive_v3_*.py`),
`review/STUDY_validators_v3.txt`, `review/STUDY_arbiter_v1.md`, `review/STUDY_arbiter_v2.md`,
`review/STUDY_fixer_v2.md`; `docs/methodology/06-review.md` §6.1-§6.8; `.claude/memory/decisions.md`
top entries; the experiment-log stub (`.claude/memory/experiment-log.md` l. 11-16);
`campaigns/2026-09-26-delta/code/GATES.md` §6 and `manifests/delta_w2_{cells,t0}_packs.json`; anchor
STUDY at 96b95f2. No plot-validator file (STUDY has no figures).

**§6.5 warning, iteration 3.** This is the third panel iteration of this STUDY. The panel tier
warns at 3, warns strongly at 5 and escalates at 10. The open items below are all text-level
pre-registrations or budget rows; none needs a GPU, and none reopens a v2 A item. The fixer must
close them in one pass (iteration 4), with every changed number carried through the cascade, so
that the loop ends there.

## Validator lines

`STUDY_validators_v3.txt`: no mechanical STUDY validator exists; `prose_lint` on STUDY.md scores 0,
"reads human" (19,939 words). No line is A-marked, so the validator rule makes nothing Category A.

## Independent checks (arbiter)

- **`screen_null.py` re-run** (`uv run --with numpy,scipy`, seed 20260927). R2 own-sd critical
  values 4.406 (m 12) / 6.751 (m 40) at n 4 and 6.948 / 12.984 at n 3. Bit-identical branch 4.426 /
  6.791, false "yes" 0.103 without offset and 0.261 at 0.707 SE (m 12). Scenario rows at n 4, m 12:
  equal 0.102, one cell 3x 0.105, 25 % at 3x 0.111, two-mode 0.053 / 0.038 / 0.042, offset 0.103 / 0.104.
  All match STUDY l. 755-781 and the three reviewers. Section 1 prints m 40: 0.023 simulated,
  "1/(m+1) = 0.024" (phys C3; STUDY l. 142 attributes 0.023 to 1/(m + 1)).
- **`budget.py` re-run.** (4, 4): 302 runs, 176,000 run-epochs, 318 certifications. "Not packable
  today" row: M006, M047, M048, M049, P-T1, P-T2 left out → 268 runs (240 cell, 8 placebo, 20
  replica), 156,000 run-epochs, 284 certifications.
- **Critic B3 traced to the packs.** `GATES.md` §6 "Packs" (l. 836-842): "cells: 83 pods, 220 arms
  … unpacked: cache_not_built M009 (N=32), M038 (ungated), M040 (derived features), M041 (real-slot
  std); floor_untraced M006; GATE_FAIL M047, M048, M049, P-T1, P-T2". Counting run names in
  `manifests/delta_w2_cells_packs.json`: 220 unique names, 212 cells + 8 placebos (`p` 8), no m006,
  m009, m038, m040, m041, m047-m049. `delta_w2_t0_packs.json`: 20 replica names. Packable today is
  **240 runs**, not 268. The 28-run gap is M009 (350k, 5M), M038 (350k, 5M), M040 (350k, 5M), M041
  (5M) × 4 seeds. Critic B3 confirmed.
- **Related inconsistency (keep looking, arbiter).** Launch gate 3 (l. 412-418) makes the Z10
  caches for M009, M038, M040, M041 part of "Nothing in this wave launches before all of these
  hold" (l. 395). Gate 13 (l. 476-477) says "those cells are unpacked until they are" and "the rest
  of the wave does not wait". The two gates disagree on whether the caches block the wave or only
  their cells.
- **Critic B1 confirmed.** "Only `name`" survives at l. 84 (change log: "the replica's config with
  only `name` changed"), l. 124 (Question: "under another run name"), l. 1122-1123 ([DK7]: "under
  another `name`") and in the experiment-log stub, l. 13 ("with only `name` changed (PREFLIGHT
  asserts equal digest without name …)"). Arms l. 192-207 and X2 l. 349-351 name the full key set,
  consistent with the generator diff the critic printed.
- **Critic B4 / constructive C2 confirmed.** [L8] l. 1196-1197: "the long-horizon cells (M015, M031,
  M032) use the H-500 placebo as their reference, labelled so". Arms l. 214-215 and Selection
  l. 739-740: no placebo at their horizon, outside the family test, against the replica. The
  paired list (l. 786-787) holds "the 12 accuracy cells on A" and "the G3 cells on C", which include
  M015 (H 1,000), M031 (H 1,500) and M032 (H 2,000); s_pool is "pooled over the ranked cells only"
  (l. 745), so it includes them.
- **Physics B1 reproduced** (exact binomial, n = 4, p_e = p_base = p): P(false rescue) per entry
  0.038 / 0.121 / 0.104 at p 0.25 / 0.5 / 0.75; 0.85 expected over 7 entries at p 0.5; at n 3: 0.062
  (0.44). With k_base = 0: 0.31 / 0.74 / 0.95 at p_e 0.5 / 0.75 / 0.9. Stronger support from the
  traced floors (`GATES.md` §6 "Zero floor"): M005 0, M004 41,985, M009 85,507, M002 85,763, M003
  114,182, M001 171,526, against A07-350's 343,053 with headroom 6,947 (STUDY l. 186). Every traced
  floor-family entry has at least 178,474 EBOPs of headroom at 350k (M001: 350,000 − 171,526), about 26 times A07-350's: a rescue
  is expected from the floor arithmetic alone.
- **Physics B4, pause probability** (arbiter arithmetic, χ² with df k − 1, Gaussian seeds, not
  quotable): P(sd_rep > 1.3 pt) with 8 usable seeds is 0.000 / 0.106 / 0.629 / 0.889 / 0.991 at
  σ 0.6 / 1.0 / 1.5 / 2.0 / 3.14 pt; with 6 seeds 0.000 / 0.133 / 0.585 / 0.833 / 0.973. The
  1.5 and 2.0 rows match STUDY l. 618-620 (1 − 0.37, 1 − 0.11). At the only measured N=64 spread the
  pause is nearly certain.
- **Lower bracket provenance (constructive C5).** Experiment-log inventory entry (2026-09-27,
  "What has this project already tried"): the pT-weighting BASE config has "epochs 101,
  es_patience 15 and no EBOPs block, so the 0.0019 accuracy sd is from the archived Round-14
  recipe". STUDY l. 171 and l. 628-630 use it as "the 0.6-pt row below is plausible, not
  optimistic" without that label.
- **Physics B2 context.** Anchor 96b95f2 l. 559-565, 1497: 5M was set 9.2 % above the old
  quantizer's traced floor (4,580,398). Under [D19] the A07 0-bit floor is 343,053 and the
  all-1-bit cost is 1,005,741 (`GATES.md` §6, M007 C row "one 1005741"). Whether BetaPID pushes at
  5M is not known, and the STUDY does not say how it would tell.
- **Traced-epoch count.** decisions.md, "ml-engineer, regime B implemented": traced e with
  e == 0, (e + 1) % 10 == 0 or the last epoch, 701 per 7,000-epoch run. STUDY l. 669-678 keeps 50
  as primary with "PREFLIGHT prints". Acceptable as written; critic C2 asks that the staged tree's
  51 be the stated expectation.
- **Kai's decisions verified.** decisions.md "2026-09-27 (Kai, direct)": (1) regime-B pilot
  epoch-500 validation readout; (2) mean paired gap primary, LCB80 beside it, "this signs [DK6]".
  STUDY l. 38-42, 396-401, 743-750, 1119-1121, 1204-1207 implement both.

## Adjudication of v3 findings

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Placebo still "only `name`" at l. 84, 124, 1122-1123 and in the experiment-log stub; the stub's PREFLIGHT assertion fails as written (`train.epochs`, `delta_study.*` differ) | crit B1 | B | **B** | Case 3, confirmed at the four lines (Independent checks). A pre-registered assertion that fails on correct configs invites an ad hoc loosening |
| 2 | Determinism probe too narrow (3 epochs, one pod, E only; the placebo is never in its replica's pod; A07 kernels differ). Branch (i) drops the placebo reference for a no-offset assumption (0.261 / 0.258 at 0.707 SE) with no gain in arithmetic (4.41 vs 4.43, 6.75 vs 6.79); check (iv)'s t is undefined at sd 0 | crit B2 / cons B2 / phys B3 | B / B / B | **B** | Case 1. Reproduced: branch (i) 0.261 (m 12) at 0.707 SE, R2 0.104 at the same offset. One fix, adopting cons B2's structure with phys B3's cross-pod condition (fix 2) |
| 3 | "What can be packed today" 268 runs / 156,000 run-epochs overstates the set in its cited source (GATES §6: 220 cell-phase arms + 20 replicas = 240) | crit B3 | B | **B** (not A) | Case 3, confirmed from the packs JSON. Not raised to A: §6.4 makes numerical self-consistency Category A at VERIFY and REPORT; at STUDY this is a labelled planning row; the full-design table (302 / 176,000) is correct; the 28-run error changes no statistical rule, falsifier or pre-registered decision. It does reach Kai at the launch gate through [DK1] (l. 1212), which is why it is B and not C. Keep-looking addition: gates 3 and 13 disagree on whether the Z10 caches block the wave or only their cells |
| 4 | Long-horizon cells (M015, M031, M032) ranked in one list with H = 500 cells and pooled into s_pool; [L8] l. 1196-1197 contradicts Arms l. 214-215 and Selection l. 739-740 | crit B4 / cons C2 | B / C | **B** | Case 2, sided with B. Two pre-registrations of one rule leave the choice to read time. The mixed-horizon list is the "schedules as one series" pattern (§6.7) in a pre-registered table; each g is horizon-matched, but the ordering and s_pool mix horizons |
| 5 | Rank-move flag: r is "family-pooled run-level", not centred per cell, while `screen_null.py` §8 simulates within-configuration noise; real between-cell differences inflate r, select a smaller T and flag more than about one null cell | crit B5 / cons C6 | B / C | **B** | Case 2, sided with B. The T table exists to hold the null flag count near one (arbiter v2 fix 7, a B item). An uncentred r reopens that defect whenever some cells have real effects, which is the case the flag is for. The pairing section already centres per cell (l. 842) |
| 6 | Literature note on screen design and seed-variance methodology requested, not tracked (l. 1367-1369) | crit B6 / cons C4 | B / C | **B**, in progress | Case 2, sided with B: the note could bear on the design (cons B1's top-k extension is a successive-halving-type rule; variance moderation, cons C1). physics-researcher is writing `campaigns/2026-09-27-delta-screen/research/screen-design-literature.md` now. Pending, not dismissed: fix 6 |
| 7 | Floor-family G2 rule has no null rate; "structural, by construction" is applied by eye; for M001/M002 (and every traced floor-family entry) the rescue follows from halving the floor | phys B1 | B | **B** | Case 3, reproduced (0.121 per entry at p 0.5; 0.31-0.95 at k_base 0) and strengthened by the GATES §6 floors |
| 8 | Whether the 5M constraint binds is not stated; 40 of 68 cells and every training-only lever sit at 5M (14.6× C's 0-bit floor under [D19]); no "constraint active" readout | phys B2 | B | **B** | Case 3. The 5M target was set against the old quantizer's floor (anchor l. 559-565, 1497). If BetaPID never pushes, the EBOPs-pressure levers (M003, M007, M008, M011, M012) are not exercised, and [L7]'s transfer rule changes. Text-level readout, no GPU |
| 9 | "Expected outcome: ranking mode at (4, 4)" while the only measured N=64 spread (3.14 pt) makes a pause at the 1.3-pt ceiling nearly certain; budget, timeline and [DK1] assume (4, 4); no default among the four pause options | phys B4 | B | **B** | Case 3. Arbiter arithmetic: P(pause) 0.63 / 0.89 / 0.99 at σ 1.5 / 2.0 / 3.14 pt (8 seeds). Naming the default now keeps the choice from reading as post hoc |
| 10 | Ranking-mode n is fixed at 4 whatever sd_rep reads below 1.3 pt; the priced (6, 4), (4, 6), (6, 6) rows are unreachable by any rule; at σ 1.0-1.3 pt n = 6 or a top-k extension on replica seeds 5-8 raises 5M top-12 recovery from 0.54-0.75 to 0.67-0.89 | cons B1 | B | **B** | Case 3. §6.3 Q4/Q5: the design has less resolving power than its priced budget allows, in the band its own ceiling admits. The GPU cost is Kai's; the rule is text |
| 11 | Replica loss re-simulates the family test at n′ although the test (cell − placebo) does not contain the replica; a rep-A seed lost at 1,000 only | crit C1 | C | C | |
| 12 | State the staged tree's epoch-0 trace (51 per first cycle) as the expectation | crit C2 | C | C | |
| 13 | Pins: anchor RUN.md at c9c9942 for the 90.61 / 127.45-s split; name both regime-B bundles (f2107a04, e90327d4 uncommitted), "PREFLIGHT fixes which" | crit C3 / cons C7 | C / C | C | Case 1 |
| 14 | [L1](a) epoch-500 readouts of M015, M031, M032 uncertified: certify (+16) or label | crit C4 | C | C | |
| 15 | In the bit-identical reading, say whether the placebos still launch | crit C5 | C | C | Largely answered by fix 2: the placebo is the reference in both readings, so it launches |
| 16 | Pooled ranking interval simulated at equal spread only: label "95 % at equal spread" | crit C6 | C | C | |
| 17 | Pod-hours are slot-seconds; partly empty pods bill more | crit C7 | C | C | |
| 18 | `plan.md` v1 sections not tagged superseded | crit C8 | C | C | |
| 19 | "A 'no' is not evidence of absence" beside every family-test answer in VERIFY and REPORT | phys C1 | C | C | |
| 20 | Half-width table row at ρ = −0.5 | phys C2 | C | C | |
| 21 | l. 142: 0.023 at m = 40 is the simulated value; 1/(m + 1) = 0.024 | phys C3 | C | C | Confirmed from `screen_null.py` §1 output; reword, keep the number |
| 22 | Forest plot shows both d (vs placebo) and g (vs replica) for a named cell | phys C4 | C | C | |
| 23 | Gated variance-moderated max-t (d0 = 3) as a third option, or record it in `plan.md` dead ends | cons C1 | C | C | |
| 24 | Review-cycle trail in the body (24 references after l. 94); move to the change log (§6.6) | cons C3 | C | C | |
| 25 | Label the 0.19-pt lower bracket "101 epochs, early stopping, archived recipe" | cons C5 | C | **C, required** | Confirmed (experiment-log inventory). It carries the "0.6 pt is plausible" argument (l. 628-630), so the label is required with fix 9 |
| 26 | Box and Falsifier powers are at m 12 / 40; the test's m is 11 / ≤ 37 | cons C8 | C | C | |

None of the three reviewers raised a Category A, and the arbiter finds none. No B item is raised
to A (row 3 gives the reason for the one candidate the orchestrator named).

## Earlier A and B findings (arbiter v2), by name

| v2 # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 (A) | regime B absent (with v1 #4d, #9, #10) | **resolved** | frontmatter l. 9; change log l. 63-68; l. 237-241 (trace every 10 epochs, [DK13]); Selection l. 669-678 (traced epochs only, denominator printed); gate 5 l. 423-429 covers `ebops_trace_every`; gate 11 l. 464-468; Budget on 136.5 s l. 930-943; anchor re-pinned to 96b95f2. The generated configs carry no `ebops_trace_every` yet (critic: 312 of 312), which gate 11 covers (rebase before launch). Pin residuals: row 13 (C) |
| 2 (B) | Kai's launch timing | **resolved** | launch gate 1 l. 396-409 quotes Kai's decisions.md entry and names the regime-B pilot readout; [DK4] l. 1110-1116 |
| 3 (A) | heteroscedastic family test | **resolved** | own-sd, placebo-referenced max-t, l. 751-774; `screen_null.py` §4 re-run above (0.099-0.111 equal / unequal, 0.038-0.089 two-mode at n 4); "by construction" gone (critic grep) |
| 4 (A) | family test not placebo-referenced | **resolved in branch (ii); not in branch (i)** | l. 751-752 set d = cell − placebo; branch (i) l. 776-783 reverts to the replica with a no-offset assumption (0.261 at 0.707 SE, re-run above). The residual is v3 #2 (B). The A defect as named (the rule that governs the expected, divergent stack) is closed |
| 5 (A) | placebo specification and determinism | **resolved in Arms; residual B** | Arms l. 190-215 names the mechanism and assertion, matching the generator diff; probe at gate 7 l. 443-448; both outcomes l. 775-785. Residuals are v3 #1 (stale "only `name`") and v3 #2 (probe scope), each B |
| 6 (A) | replica-side losses | **resolved** | l. 536-544 (uniform n′, critical value re-simulated, seeds 5-8 cannot substitute). Crit C1 (row 11) is a refinement |
| 7 (A) | G3′ power (v1 #4a) | **resolved** | l. 716-727: two-sided 95 % t on own sd, df n_p − 1; P(pass) 0.074 / 0.041 / 0.031; "non-inferiority not shown at this n"; [DK15] |
| 8 (B) | pooled interval under-covers | **resolved** | l. 746-749, simulated multipliers 2.18 / 2.15 (critic and physics reproduced 2.179 / 2.146) |
| 9 (B) | rank-move flag without null rate | **resolved as specified; residual B** | l. 806-816, T from `screen_null.py` §8. The definition of r is v3 #5 (B) |
| 10 (B) | [DK6] against DELTA §5.3 (v1 #6) | **resolved by Kai** | decisions.md "2026-09-27 (Kai, direct)" (2); l. 743-750, 1119-1121 |
| 11 (B) | E packing (v1 #7) | **resolved** | [D16] l. 1094-1099; Budget l. 983-993 (planning K 4, K 5 alternative, reason stated once) |
| 12 (B) | [L1] attempt (v1 #19) | **resolved** | l. 1160-1172: long-horizon cells at 500 vs their own H, "a count of order changes, not a test"; seed-rank persistence "not a test of [L1]" |
| 13 (B) | sd_rep usable count | **resolved** | l. 508-514 (k_rep printed, ≤ 6 of 8 labelled, cannot raise n) |
| 14 (B) | accuracy-vs-AUC consequence | **resolved** | l. 835-838 |
| 15 (B) | pairing efficiency | **resolved** | l. 839-849 (ρ̂ with null interval −0.32 / +0.33 and −0.18 / +0.18; unpaired companion 2.92 / 3.62) |
| 16 (B) | cheap version at n = 3 | **resolved** | l. 772-774, 1006-1011: n = 3 rows printed, "not calibrated under two-mode seeds" |

Arbiter v1 A/B items carried into v2 (v1 #4a, #4d, #6, #7, #9, #10, #19) are closed through v2
rows 1, 7, 10, 11 and 12 above. v2 C items #17-#31: applied (critic's check; the 0.023 attribution
at l. 142 is a residual, row 21).

## Regression triggers (§6.7), each checked

| trigger | status | evidence |
| --- | --- | --- |
| selection on held-out, or changed after results | not met | validation only (l. 665-686, 850-851); no results exist |
| val AUC vs ROC-test AUC > 0.01 | not met | no ROC-test evaluation ([D5], l. 850) |
| single-seed / < 100-epoch / lab-pod headline against the record | not met | nothing quotable; Reference table has no comparand (l. 159-174) |
| comparison across N, input sets, splits or **schedules** as one series | **pattern present in the design, no result; origin STUDY** | M009, M038, M040 labelled (l. 506, 1038). The pre-registered paired list mixes H 500 with H 1,000 / 1,500 / 2,000 cells and pools them into s_pool (v3 #4). No result exists and the origin phase is this STUDY, so no earlier phase re-runs and no investigator is needed; fixed in this iteration (fix 4) |
| gap smaller than seed sd with < 3 seeds | not met | n ≥ 4; n_p ≥ 3 for any reading (l. 699-704) |
| reload outside 1e-7, TF32 on | not met | l. 576, 1044 |
| eBOPs not remeasured on the selected checkpoint | not met | certification l. 692-696, unchanged under regime B |
| binary layer with > 2 values | not met | conventions check 1, l. 1044 |
| DSP / C-sim / C-synthesis | not applicable | l. 1026, 1045 |
| per-class AUC < 0.7 hidden | not met | l. 824-825 |
| byte-identical arms / different y arrays | not met; watch | y_val sha asserted (l. 499-502). The placebo is byte-identical in training-relevant config by design; fix 2 pre-registers how a bit-identical outcome is read, so it is neither hidden nor misread |
| failed validation without remediation; tautological comparison as validation | not met | no validation has run. The placebo's formula check (l. 898-903) is read by the pre-registered branch, not presented as validation |
| STUDY [D] label replaced without dated amendment | not met | [D16] amended v3, dated (l. 72-74, 1094-1099); [DK6] Kai-decided and cited; [L8] contradicts Selection (v3 #4) but replaces no [D] label |
| outward numbers ≠ VERIFY | not applicable | none |
| suspiciously good | not applicable | no results |

No trigger requires an investigator or a `REGRESSION_TICKET.md`.

## §6.8 validation target

No binding comparand, correctly, for a never-quotable screen (Reference table l. 159-174). The
stand-ins for reproduction (conventions check 3, l. 1037) are unchanged.

## Motivated reasoning

- **The expected branch is the least likely one under the STUDY's own prior.** The budget, the
  wall clock and [DK1] are written for (4, 4) in ranking mode, while the only measured N=64 spread
  makes the 1.3-pt pause nearly certain (0.99 at 3.14 pt), and the argument that 0.6 pt is
  "plausible, not optimistic" rests on a 101-epoch, early-stopped, archived-recipe N=8 run. Fix 9.
- **"Structural, by construction" by eye** where the floor arithmetic already predicts the
  rescue for every traced floor-family entry. Fix 7.
- **An assumed zero offset with a printed hypothetical rate** where the placebo can measure it.
  Fix 2.
- Checked and not found: no interval is inflated to make a gap look consistent (the ranking
  interval uses the simulated multiplier on paired seeds); no selection rule moved; G3′ failure is
  not read as inferiority.

## Competing-group question

A group running this screen next month would have: an n rule in ranking mode that spends the
already-priced seeds where the ceiling admits σ of 1.0-1.3 pt (fix 10); a readout showing whether
the 5M constraint binds (fix 8); one placebo reference with the offset measured (fix 2); and a
literature grounding for the ranking-vs-testing design (fix 6, in progress). None has a
justification for being absent.

## Disputed facts for the investigator

None. Every fact above was settled from the artifact, `GATES.md` §6, the packs JSON, the
experiment log, decisions.md or a re-run script, with the line cited.

## Dismissals

None.

## Verdict: **ITERATE** (iteration 3; §6.5 warning issued above)

No Category A. Ten B items are open (v3 #1-#10), all verified against the artifact, so none can be
downgraded (§6.5.1). PASS requires no unresolved B (§6.1: B is "fixed before PASS"), and "fix →
advance without a re-review is a process failure" (§6.5). A PASS that sends B items to the fixer
with no re-review is not available. Only the C items skip re-review. The next arbiter pass is
iteration 4. The panel warns strongly at 5.

Required fixes for the `fixer`, in priority order. Add a v4 change-log entry (dated
2026-09-27) that lists fixes 2, 3, 4, 7, 8, 9 and 10 as dated amendments where they touch a
pre-registered rule. Fix 2 withdraws the branch-(i) test switch that the v3 entry (l. 84-85)
describes, so without a v4 entry the audit trail contradicts the body. Every changed number cascades: `budget.py`
output, the Budget tables, Counts (l. 318-323), the box (l. 99-117), Null (l. 134-143), Falsifier,
the [DK] rows, "Where I am not sure", `plan.md` and the experiment-log stub (`experiment-log.md`
l. 11-16).

1. **(B, v3 #1) Placebo wording.** Replace "only `name`" / "under another run name" / "under
   another `name`" at STUDY l. 84, l. 124, l. 1122-1123 and in the experiment-log stub l. 13 with
   the Arms wording: identity and provenance keys (`name`, `experiment.arm`, `delta_study.*`,
   `engram_study.question`) plus `train.epochs`; the assertion is equal `digest_json(cfg)` after
   deleting those keys and setting `train.epochs` to one value, equal init `kernel_hashes`, equal
   first-step CPU loss (l. 205-207). Grep for "only `name`" and "run name" afterwards.
2. **(B, v3 #2) One family-test reference; probe decides only the placebo row.**
   (a) The family test is referenced to the placebo (d_i = cell − placebo) in every case. Delete
   the test switch in branch (i) (l. 776-783), with its 4.43 / 6.79 values and the 0.261 / 0.258
   row, from Selection, [DK7] and wherever else it is quoted.
   (b) Rewrite the two readings as readings of the placebo row only. *Bit-identical reading:*
   placebo and replica have equal weight hashes at epoch 500 at every seed where they share a GPU
   product, across pods (phys B3). The row is then read as "pod, pack and identity check passed:
   offset measured zero on this product", and its rank is not read. *Divergent reading:* any seed
   where they differ puts the family in this reading. The divergence is printed and the placebo is
   read as the in-family null draw.
   (c) Probe spec, launch gate 7 (l. 443-448): per architecture class (E and A07); the same config
   and seed in two different pods of one GPU product; run past the first in-training traced epoch
   so the PID's traced-value branch runs (past the end of epoch 10, one-based; name the count
   from `is_traced_epoch` on the frozen bundle); compare weight hashes and
   per-epoch losses.
   (d) Check (iv) (l. 889-897) when every per-seed placebo g is 0 and the t is undefined: "any
   nonzero per-seed placebo g on a shared product flags". Update the formula check (l. 898-903)
   and l. 659-662 to match.
3. **(B, v3 #3) Packable-today row.** Add M009 (350k, 5M), M038 (350k, 5M), M040 (350k, 5M)
   and M041 (5M) × 4 seeds to `budget.py`'s excluded ("not packable today") set, re-run it, and replace 268 /
   156,000 / 985.8 / 1,744.2 / 4.9 / 8.4 d / 284 at STUDY l. 967-972, the [DK1] row (l. 1210-1212),
   `plan.md` l. 89 and anywhere else the fixer's grep finds them. Expected: 240 runs (212 cell,
   8 placebo, 20 replica), matching `manifests/delta_w2_cells_packs.json` (220) +
   `delta_w2_t0_packs.json` (20). Cite GATES §6 l. 836-842. Then make launch gates 3 and 13 agree
   on whether the Z10 caches block the whole wave or only their cells, and state it once.
4. **(B, v3 #4) Long-horizon cells.** Take M015, M031, M032 out of the paired single-lever list
   into their own list "horizon H ≠ 500" (or mark each row with its H and exclude it from the
   ranking order), and exclude them from s_pool (l. 745). Rewrite [L8] (l. 1196-1197) to match
   Arms l. 214-215 and Selection l. 739-740 (no placebo at their horizon, outside the family test,
   reported against the replica at their H). Update the lists paragraph (l. 786-793). The ranked
   m falls from 12 / 40 to 11 / ≤ 37, and m is quoted in the box (l. 100, 110: "12 … up to 40",
   chance 0.022), the ranking-interval multiplier (l. 748, 2.18 / 2.15 at m 12 / 40), the rank-move
   T table (l. 810-812), the fidelity table and `rank_sim.py` (l. 643-653), and the sd_rep ceiling
   derivation (l. 610-613, "top 12 of 40"). Either re-simulate at m 11 / 37 or state once that the
   design grid stays at m 12 / 40 and every read re-simulates at the family's actual m (the
   convention the family test already uses, l. 735-737), and apply that choice at each of those
   places.
5. **(B, v3 #5) Rank-move r.** At l. 806-809 define r as the correlation of primary and
   last-epoch companion values centred per cell (as ρ̂ at l. 842), pooled over the family's runs,
   and say that this matches `screen_null.py` §8's within-configuration draw.
6. **(B, v3 #6) Literature note.** Cite `campaigns/2026-09-27-delta-screen/research/
   screen-design-literature.md` at l. 1367-1369, with its owner (physics-researcher, requested by
   the orchestrator 2026-09-27). If the note exists when the fixer runs: read it, and for each
   point it makes on multi-fidelity or successive-halving screening, seed variance, winner's
   curse or variance moderation, either apply it to the design or write one line on why not. If it
   does not exist yet: write "pending, path above", and the iteration-4 arbiter reads it.
7. **(B, v3 #7) Floor-family null rate.** Beside the G2 rule (l. 131-132, 710-713) print the null
   false-rescue rate per entry at n = 4 (0.038 / 0.121 / 0.104 at p 0.25 / 0.5 / 0.75; about 0.85
   expected over 7 entries at p 0.5) and at the observed k_base (0.31 / 0.74 / 0.95 at k_base = 0,
   p_e 0.5 / 0.75 / 0.9). Give "structural, by construction" a numeric trigger fixed now, for
   example cell floor ≤ ½ of A07-350's 343,053. The GATES §6 floors (M001 171,526, M002 85,763,
   M003 114,182, M004 41,985, M005 0, M009 85,507) meet that trigger for every traced entry. State
   that for those entries the informative quantity is the cross-architecture accuracy, not G2.
8. **(B, v3 #8) 5M constraint active.** Pre-register a "constraint active" readout on rep-C at
   the epoch-500 gate: the fraction of traced epochs over target, the selected checkpoint's
   EBOPs / target, and whether β sits at its bound. Fix the rule now. If the constraint does not
   bind, the 5M family is labelled "constraint slack at 5M", the EBOPs-pressure cells (M003, M007,
   M008, M011, M012) are labelled "mechanism not exercised", and [L7] / [DK10] say what that means
   for sending a training-only lever to confirm. Add a "Where I am not sure" row.
9. **(B, v3 #9) Pause as a likely branch.** At l. 624-632 and in the box, state P(pause at the
   1.3-pt ceiling) at σ 0.6 / 1.5 / 3.14 pt (8 usable seeds, Gaussian: 0.00 / 0.63 / 0.99;
   compute in `screen_null.py` §10 and cite it). Pre-register the default among the four options
   (cut m, raise n, cheap version, feasibility only) as a [DK] row with its cost from `budget.py`.
   Budget and [DK1] say that (4, 4) is the branch taken only if the ceiling passes. Label the
   0.19-pt bracket "101 epochs, early stopping, archived Round-14 recipe" (experiment-log
   inventory entry; C row 25, required here).
10. **(B, v3 #10) Ranking-mode n rule.** Add a [DK] default beside the significance-mode rule:
    n = 4 if sd_rep < 1.0 pt; n = 6, or the top-k extension, if 1.0 ≤ sd_rep ≤ 1.3 pt; pause
    above 1.3 pt. For the top-k extension, state its limits. Seeds 5-8 for the top 16 cells at 5M
    and the top 6 at 350k pair with replica seeds 5-8 that already run to 500, so it applies to
    H = 500 cells only. The placebos run seeds 1-4, so the family test stays at n = 4 unless P-350
    and P-5M are extended too; say which. The 8-seed mean includes the seeds the cell was selected
    on, so the seeds-5-8 mean is printed as the selection-free estimate. Run `budget.py` for the
    88-run variant and quote its runs, run-epochs, pod-hours and wall clock. The GPU cost is a Kai
    row.
11. **(C, apply before commit, no re-review of their own)** rows 11-26. Crit C1-C8, phys C1-C4 and
    cons C1, C3, C7, C8. Notably: l. 142 "0.023 (simulated; 1/(m + 1) = 0.024)"; the 51-per-cycle
    expectation; pins c9c9942 and both bundle shas; "95 % at equal spread"; tag `plan.md` v1
    sections superseded; move the review-cycle trail out of the body.

## What Kai must decide (at the launch gate; not a STUDY blocker)

The fixer writes each as a "Where I am not sure" row with its cost.

1. **Ranking-mode n rule** (fix 10): n = 6 or the top-k extension in the 1.0-1.3-pt band, with
   its GPU cost from `budget.py`.
2. **Default on a ceiling pause** (fix 9): cut m, raise n, the cheap version, or feasibility
   counts only. At the archived spread this is the likely branch.
3. **5M constraint slack** (fix 8): if rep-C shows the constraint does not bind at 5M, whether the
   training-only levers still screen at 5M ([DK10]) or move to 350k on A, and what [L7] then says.
4. **X5 non-binary path** under the anchor's [A20] guard (M047-M049, teachers, KD cells): a
   design call for the patches owner and Kai.
5. **Carried defaults:** [DK1]-[DK5], [DK7]-[DK15] (with [DK1] restated at 240 packable runs,
   [DK7] rewritten by fix 2); [DK6] and the launch readout are already Kai-decided.
