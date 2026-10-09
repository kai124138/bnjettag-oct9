# STUDY arbiter v1: 2026-09-27-delta-screen (Delta wave 2)

Arbiter, fresh context, 2026-09-27. Iteration n = 1 (no earlier arbiter file).
Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (647 lines) with `plan.md` and `budget.py`.
Inputs read: `review/STUDY_physics_v1.md`, `review/STUDY_critical_v1.md`,
`review/STUDY_constructive_v1.md` (with `review/rank_sim.py`, `review/two_stage.py`),
`review/STUDY_validators_v1.txt`; `docs/methodology/06-review.md` §6.1-§6.8;
`docs/conventions/{jet-tagging-metrics,quantization-and-cost,fpga-synthesis,figures}.md`;
upstream `campaigns/2026-09-26-delta/DELTA.md` (§3.3, §5.1-§5.4, §6, §7), `delta.json`,
`code/README.md`; anchor `campaigns/2026-09-26-training-batch/STUDY.md` (diff `dde5ca7..HEAD`)
and `RUN.md` (pilot, epoch-10 canary). No plot-validator file (STUDY has no figures).

## Validator lines

`STUDY_validators_v1.txt`: no mechanical STUDY validator exists; `prose_lint` on STUDY.md score 0
("reads human"). No A-marked line, so nothing here is Category A by rule.

## Independent checks (arbiter)

- **Ranking-mode null** (own simulation, numpy seed 1, 20,000 reps, n = 4, one shared replica per
  family, equal variances): cells with LCB80 > 0 under the global null, mean 3.82 of 19 and 8.53 of
  43; P(none) 0.26 and 0.165; P(no cell in either family) = 0.043. The 95th percentile of that
  count is **13 of 19 and 28 of 43**, because the shared replica term moves every gap of a family
  together. All three reviewers' numbers agree with this (phys 0.27 / 0.16; crit 0.26 / 0.16; cons
  P(≥1) 0.73 / 0.84). Consequence for the fix: a count threshold (Bin(m, 0.2) or the simulated 95th
  percentile) is nearly powerless; a placebo line is required (item 1 below).
- **Half-width at the archived spread:** t(0.975, 3)/√4 · √2 · 3.14 = 7.07 pt (computed).
- **DELTA departures** (critical A1), traced:
  - G3′ non-inferiority exists at DELTA §5.3 ("G3′, non-inferiority (cost levers M023 and
    M024/M025 when read for cost, and floor entries at 5M): the lower 95 % bound > −0.3 pt");
    `grep "G3′|G3'|non-inferior"` on STUDY.md returns nothing. `delta.json` M023 `prediction` is
    "non-inferior accuracy; …", so without G3′ M023's pre-registered question cannot be answered.
  - "If arm A fails at 350k (fewer than ⌈3n/4⌉ of seeds 1-n feasible at epoch H, the FF2 rule)"
    exists at DELTA §3.3 R2 with four consequences; STUDY l. 201-205 applies R2 only to the pilot
    and the base-stability rule (l. 276-279) counts only diverged, collapsed, H1-degraded seeds.
  - DELTA §5.1 rule 1: sd_plan from the anchor's epoch-500 sd "over seeds 1-8"; STUDY l. 327-329
    uses the 2-seed pilot and l. 597 says "as written in DELTA §5.1". That statement is false.
  - DELTA §7 wave 2a starts when "the anchor's epoch-500 snapshots of seeds 1-n exist", and §6.3
    says "Delta waits for the anchor's epoch-500 pilot"; STUDY [D6] launches on replicas without
    anchor production. Flagged to Kai (l. 589-595), but not listed as a departure in the change log.
  - Also absent from STUDY (found in the same trace, §6.3.2): the 12-cell confirm cap (DELTA §5.3
    "Cap"); R1 static-infeasible removal (a cell whose traced floor is ≥ its target is removed,
    DELTA §3.3 R1; crit C4); the 2a/2b ordering (floor family first, DELTA §7); K6 (whether
    M047-M050 run at all, DELTA §7) and the teacher jobs as a K2 item (DELTA §7 K2 lists "the
    teacher jobs P-T1/P-T2"; STUDY [D13] cites the orchestrator brief, which is not Kai).
- **Always-on patches:** `code/README.md` l. 42-48 lists `accumulator-ebops-metric`,
  `diag-*` and `screen-collapse-stop` as `gated-on-tarball`; `delta.json`
  `always_on_diagnostics` = `diag-attention`, `screen-collapse-stop`, `accumulator-ebops-metric`.
  X2 (STUDY l. 174-178) does not cover them. Critical B3 confirmed.
- **E at K = 6 (new evidence, after the STUDY was written).** Anchor `RUN.md` epoch-10 canary
  (commit e620173, after the STUDY commit d571cc5): per-process 4,354 MiB for A-s1 / A-s2 / D-s1;
  "Six same-size arms … would need ≈6 × 4,354 ≈ 26,124 MiB, already ≈3.1 GiB over the A10's
  23,028 MiB"; "a K=6 pack of the smaller E arms alone is not obviously safe either"; "K=3 / K=4
  projections: no measured basis exists". [D16] fixes E at K = 6 and every Budget row uses
  218 s / 6 as the per-slot cost.
- **Anchor has moved since the cited sha.** `git log dde5ca7..HEAD` on the anchor STUDY: fba27d5
  (arbiter v7 fixes), 1115121 (arbiter v8: dated pilot amendment, A07-350-s1 re-runs in a K=3 pod
  with C-s1 and F-s1; wave-1 pods holding A07-350 or C wait for that readout and for Kai's packing
  answer; collapse label "Deep-Set-class", with A07-350 "Deep-Set-class by construction"), c2f5447.
  STUDY Reference row "A07-350 … no run exists … dropped" (l. 54) and the timing basis (l. 446-452)
  are stale; C′-s1 now has 293.6 s/epoch over epochs 1-5 at K = 6 (old quantizer, labelled
  indication for the A07 class only).
- **Per-class AUC:** readout list l. 391-394 has macro AUC only; conventions rows l. 505 and 508
  item 5 promise per-class AUC per cell. Physics B5 confirmed.
- **Cheap version:** `budget.py cheap()` includes M015 (T0, H 1,000), M031 (T1, H 1,500) and M032
  (T0a, H 2,000) against 500-epoch replicas; DELTA §5.4 controlled them with anchor snapshots,
  which do not exist (STUDY l. 254-257). Critical B7 confirmed.
- **Conventions:** `quantization-and-cost.md` l. 31 "Rule of record: … highest validation
  macro-OvR AUC"; STUDY l. 512 does not mark the accuracy deviation there. Both conventions files
  have a "Pitfalls, with the incident" section (`jet-tagging-metrics.md` l. 66,
  `quantization-and-cost.md` l. 49) with no row in the STUDY table. Critical B9 confirmed.
- Budget, counts, k_joint, threshold (c), sha256 of `delta.json`: reproduced by all three reviewers
  with `budget.py` and `screen_power.py`; no reviewer contradicts another; not re-run here.

## Adjudication

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Ranking-mode "no" answer (l. 32-34, 409-412) essentially cannot fire under the null; the expected mode has no falsifier and produces a ranked list about 96 % of the time when nothing works | phys A1 / crit A2 / cons A1 | A / A / A | **A** | Case 1. Recomputed (P(no) = 0.043). A shared-replica count threshold is powerless (null 95th pct 13/19, 28/43), so the fix is a placebo line, not a count |
| 2 | Selection and readout on the same 62,000 jets; best-of-H winner's curse does not cancel in the pair for levers that change curve noise or the number of eligible checkpoints (M018-M020, M028/M029, M032, M034, M008, M011-M013); [L6] claims it cancels | phys A2 / crit A4 / cons B7 | A / A / B | **A** | Case 2, sided with A. [L6]'s cancellation claim is factually false for the named cells, the bias is of the order of g0 with a sign set by the lever, the ranked list selects confirm cells, and the fix costs no GPU |
| 3 | Resolving power shown only at 0.3 and 0.85 pt, not at the only measured spread (3.14 pt → ±7.1 pt at n = 4); no ranking-fidelity number; no sd_rep ceiling that stops a family whose ranking would be near chance | phys B1 / crit A3 / cons B2 + B3 | B / A / B, B | **A** | Case 2, sided with A by rule: §6.3 Q4 ("does the design have resolving power … given the measured sd?"); a "no" without justification is Category A. The stop line is part of the same fix (crit A3's remedy) |
| 4 | STUDY departs from DELTA's pre-registration without dated amendments while the change log says "nothing loosened": G3′ missing, ⌈3n/4⌉ arm-A-fails rule missing, sd_plan source changed and misattributed (l. 597), wave-2a start condition replaced; plus 12-cell cap, R1 static removal, 2a/2b ordering, K6 and teacher K2 item | crit A1 (+ crit C4; arbiter additions) | A | **A** | Case 3, verified line by line (Independent checks). M023's own prediction is non-inferiority, so a question of the wave is unanswerable as written. Additions found by the arbiter carry the same category because they are the same defect |
| 5 | Missing-pair / survivor rule not stated: g over seeds usable in both, n_p ≥ 3, no rule for cells with n_p < n in the ranking | crit B1 / cons B1 | B / B | **B** | Case 1. The constructive reviewer invited a raise; kept at B because both reviewers agree, nothing has run and the fix is mechanical |
| 6 | Ranking statistic: per-cell LCB80 with df 3 rewards cells whose s_d is small by chance; mean g (or pooled-sd bound) matched or beat it in every simulated row | cons B4 / phys C2 | B / C | **B** | Case 2, sided with B: `rank_sim.py` is evidence, not taste, and the list is the confirm-selection mechanism. Fixer reports both and declares the DELTA rule primary; switching primary is a DELTA amendment for Kai |
| 7 | E packing at K = 6 breaks the STUDY's own ≤ 90 % memory rule (22.6/23.0 GiB); anchor canary now shows 6 E arms need ≈26.1 GiB > 23.0 GiB on the A10 | crit B2 (+ arbiter evidence) | B | **B** | Case 3, strengthened by anchor `RUN.md` epoch-10 canary. Every Budget row rests on 218 s / 6; the numbers are labelled projections, so B, not A, but Kai decides full vs cheap on them |
| 8 | Always-on patches (`screen-collapse-stop`, `accumulator-ebops-metric`, `diag-*`) not in the X2 gate; they are gated on the tarball only | crit B3 | B | **B** | Case 3, verified `code/README.md` l. 42-48 |
| 9 | Anchor production config not frozen; replicas could encode a config arm A / C no longer uses | crit B4 | B | **B** | Case 3. Anchor [D15] (T_run 17.8 d > 14 d) is open; anchor STUDY changed twice after the cited sha |
| 10 | Anchor state stale: citations pinned to dde5ca7; A07-350 now re-runs in a K=3 pilot pod (1115121); collapse label "Deep-Set-class" not carried into the screen readout; C′ timing indication available | arbiter (everyone missed) | – | **B** | Case 5. The reference table and budget basis are what Kai decides on; the collapse label is a descriptive readout the anchor now prints for every arm and the floor family needs it |
| 11 | Question states "by at least g0" (two-sided "change"); the advance rule is one-sided BH p ≤ 0.10 with mean g ≥ g0/2, and the expected mode is a ranking | crit B5 / cons C1 | B / C | **B** | Case 2, sided with B: the frontmatter question is what VERIFY tests against; a question the rule does not answer is a falsifiability defect, cheap to fix |
| 12 | Floor-family accuracy (A07-derived + entry vs E, Welch) is a package inside the m = 19 advance family and ranking, and is sized with paired power | phys B3 / crit B6 | B / B | **B** | Case 1 |
| 13 | Floor-family feasibility partly decided by construction (static headroom); traced headroom not reported beside k_e | phys B2 | B | **B** | Case 3; DELTA §3.3 "Reporting" already requires floor and h per 350k result, the STUDY does not restate it |
| 14 | Baseline asymmetry: 46 levers tuned for binary, baselines untuned; confirm comparison would favour binary | phys B4 | B | **B** | Case 3; bears on the thesis comparison at confirm; text fix |
| 15 | Per-class AUC promised (conventions rows) but absent from the per-cell readout | phys B5 | B | **B** | Case 3, verified l. 391-394 vs l. 505, 508 |
| 16 | Cheap version's M015/M031/M032 have only 500-epoch replicas and no anchor snapshots | crit B7 | B | **B** | Case 3, verified `budget.py cheap()` |
| 17 | [D14] (training-only levers at 5M on A07 only) has no matching limitation or transfer test | crit B8 | B | **B** | Case 3 |
| 18 | Conventions rows: selection-metric deviation unmarked in "Selection under a budget"; check 3 (reproduction) via g_rep probably unavailable; no Pitfalls rows | crit B9 | B | **B** | Case 3, verified conventions l. 31, l. 66, l. 49 |
| 19 | [L1] accepted with no attempt; zero-GPU rank-persistence checks available | cons B8 | B | **B** | Case 3; §6.3 Q5 makes an unattempted limitation B |
| 20 | Per-cell "prediction contradicted" in ranking mode has no false-positive count (0.025·m = 0.5 / 1.1) | cons B9 | B | **B** | Case 3 |
| 21 | Replica seeds 1-8 to epoch 500 would give a df-7 sd in both families for 4,000 run-epochs; STUDY l. 604-606 wrongly says this conflicts with "replicas first" | cons B5 | B | **B** | Case 3. Checked: 4 × 500 E + 4 × 500 A07 = 4,000 run-epochs, 20.2 + 20.2·r pod-hours (40.4 / 60.6 at r = 1 / 2). The fixer writes the option; Kai decides |
| 22 | l. 344-346 argues from the binomial SE as a lower bound on seed sd; wrong (shared validation set), conclusion holds on other grounds | cons B6 | B | **B** | Case 3; DELTA §5.3 calls the same 0.16 pt an upper bound on a paired-difference SE |
| 23 | K6 (baselines run at all) and teachers P-T1/P-T2 are Kai decisions in DELTA §7, assumed in the STUDY | arbiter (everyone missed) | – | **B** | Case 5; folded into fix 4's list and the Kai section |
| 24 | A07 fallback if K = 3 still OOMs on 23-GB cards | phys C1 | C | C | Required C: one sentence |
| 25 | Branch S df 1: note the replica guard makes it conservative | phys C3 | C | C | |
| 26 | Anchor-primary branch almost empty; consider always replica-primary | phys C4 / cons C3 | C / C | C | Kai row already exists; see Kai section |
| 27 | Certification count ≈ 300 + teachers (+ placebo), not 286 | crit C1 | C | C | Update with fix 1 cascade |
| 28 | "Formula check": exact-zero per-seed g_rep across shas would be a red flag, not the limiting case | crit C2 | C | C | Required C; the placebo of fix 1 is the real identical-arms check |
| 29 | Confound 8 list misses M016, M017-M026 | crit C3 | C | C | |
| 30 | P-T1/P-T2 selected on the same validation jets as the KD/warm-start students | crit C5 | C | C | Note in the X1 amendment |
| 31 | Baselines' place in the ranked list; M010 pairing purpose; one-line question | crit C6, C7, C8 | C | C | |
| 32 | Full vs cheap framed as coverage, not resolution; two-target sign concordance and acc/AUC rank concordance; prior-art note; two-stage rejected with evidence; "can and cannot say" box | cons C2, C4, C5, C6, C7 | C | C | cons C6 goes into plan.md dead ends |

## Regression triggers (§6.7), each checked

| trigger | status | evidence |
| --- | --- | --- |
| selection on held-out, or changed after results | not met | Selection rule l. 355-403 validation only, ROC-test never touched (l. 395-396); [D10] clarification dated before any run |
| val AUC vs ROC-test AUC > 0.01 | not met | no ROC-test evaluation in this campaign ([D5]) |
| single-seed / < 100-epoch / lab-pod headline against the 1000-epoch record | not met | nothing quotable; no record comparison (Reference table l. 46-58) |
| comparison across N, input sets, splits or schedules as one series | not met at STUDY | M009, M038, M040 labelled (l. 266-267); fix 12 keeps them from being interleaved unlabelled in the ranked list |
| gap smaller than seed sd with < 3 seeds | not met | n ≥ 4 in every branch (l. 321) |
| reload outside 1e-7, TF32 on | not met | TF32 off, reload within 1e-7 committed (l. 309) |
| eBOPs not remeasured on the selected checkpoint | not met | [D11] certification of every selected checkpoint |
| binary layer with > 2 values | not met | conventions check 1 (l. 513) |
| DSP / C-sim / C-synthesis | not applicable | no synthesis ([L5], l. 497) |
| per-class AUC < 0.7 hidden behind macro | not met (nothing measured); prevented by fix 15 | readout lacks per-class AUC today |
| byte-identical arms / different y arrays | not met | y_val sha256 asserted for every cache (l. 259-263) |
| failed validation accepted without remediation; tautological comparison as validation | not met at STUDY | the tautology risk (selection = readout split) is fix 2; the "exact-zero g_rep" wording is C28 |
| STUDY [D] label replaced without dated amendment | not met literally (no earlier version of this STUDY) | the analogous departures from DELTA's pre-registration are A item 4, fixed within this phase by dated amendments; no upstream phase re-run is needed |
| outward numbers ≠ VERIFY | not applicable | |
| suspiciously good | not applicable | no results |

No trigger is met; no investigator and no `REGRESSION_TICKET.md`.

## §6.8 validation target

The Reference table names no binding comparand (every row "no number" or "sizing only"), which is
correct for a never-quotable screen. The reproduction check (conventions check 3) rests on g_rep,
which the expected replica-primary branch mostly cannot form (l. 254-257). Fix 18 makes the STUDY
say so and name what stands in (placebo cell of fix 1 for identical-arm behaviour; g_rep when
anchor [A6] snapshots exist; the pilot A-s1/A-s2 epoch-500 values as descriptive context).

## Competing-group question

A group running this screen next month would have: an in-family null (fix 1), a readout that did
not select (fix 2), the ranking's fidelity at the measured spread and a stop line (fix 3), the
base arm's seed sd measured before spending 1,700-3,000 pod-hours (fix 21 offered), and a rule for
missing seeds (fix 5). All are required below.

## Disputed facts for the investigator

None. The three reviewers' null simulations agree with each other and with the arbiter's; every
other fact was traced to file and line above.

## Dismissals

None.

## Verdict: **ITERATE** (iteration 1)

No warning (warn at 3). Four A, nineteen B. Required fixes for the `fixer`, in priority order.
Every changed number is propagated (cascade): `budget.py` output, both Budget tables, Counts
(l. 153-157), "Where I am not sure" rows, the certification count, the experiment-log stub.

1. **(A, #1) In-family null for ranking mode.** Add one A/A placebo cell per accuracy family:
   `P-350` = arm A config plus a no-op key (run identity only) at seeds 1-n_350, H 500; `P-5M` =
   arm C config likewise at seeds 1-n_5M, H 500. Each is packed and placed like a cell (never in
   the replica's pod; same GPU-product rule as cells, [D17]), goes through the same selection,
   certification and pairing against the replica, and is **not** in BH m. Rewrite the ranking-mode
   "no" (l. 32-34, 409-412) as: "no cell's lower 80 % bound (and, per fix 6, mean g) exceeds the
   placebo's in its family"; state that a count criterion is not used because the shared replica
   makes its null 95th percentile 13 of 19 and 28 of 43 (arbiter simulation). Add the placebo row
   to the planned forest plots (l. 515). Cost: 8 runs, 4,000 run-epochs at (4, 4), +40.4 / +60.6
   pod-hours at r = 1 / 2; 286 → 294 runs. Regenerate `budget.py` and every Budget row. If the
   designer rejects the placebo, the only alternative is to delete the ranking-mode "no" and state
   that ranking mode has no family-level negative answer.
2. **(A, #2) Winner's curse.** (a) Pre-register a non-selecting companion readout for every run
   and replica: validation top-1 at the last feasible, non-degenerate epoch ≤ H (end of cycle), from
   the per-epoch logs, with its own paired interval and rank. (b) Report the count of eligible
   (feasible, non-degenerate) checkpoints per run beside every g. (c) Report Kendall τ between the
   primary and companion rankings per family and flag any cell whose rank moves by more than a
   pre-set amount (state it, e.g. crosses the top-12 line or moves > 5 places); a flagged cell goes
   to Kai with the flag. (d) Rewrite [L6] to say the bias cancels only when the two arms have the
   same fluctuation and eligible-checkpoint count, and name the cells where it does not (M018-M020,
   M028, M029, M032, M034, M008, M011-M013). The best-of-H primary stays (DELTA/anchor rule); the
   split-half alternative may be offered to Kai as an option.
3. **(A, #3) Resolving power at the measured spread, and a stop line.** In "What n = 4 resolves"
   add the row sd_d = √2 · 3.14 = 4.44 pt → ±7.1 pt (archived, sizing only), and the ranking
   fidelity from `rank_sim.py` (copy the script into the campaign): P(three true effects all in
   the top 12 of 43) at σ 0.6 / 1.5 / 3.14 pt, against 0.018 by chance. Pre-register an sd_rep
   ceiling per family, read at the replicas' epoch-500 snapshot before cells launch (for example
   the σ at which recovery of a +1 pt effect falls below 0.5, about 1.5-2 pt; the designer states
   the value and its source). Above it the family pauses and goes to Kai with options: cut m, raise
   n, cheap version, or feasibility counts only with no ranked list. Correct the guard sentence
   (l. 341-342, [D8]) so that it can pause a family, not only switch mode.
4. **(A, #4, #23) DELTA departures.** For each item, restore DELTA's rule verbatim or write a dated
   amendment against the DELTA section with its reason: (a) G3′ non-inferiority for M023,
   M024/M025 (read for cost) and floor entries at 5M, in the G0-G3 list, with its K5 consequence;
   (b) the ⌈3n/4⌉ arm-A-fails rule, applied to the base at H (replica or anchor, whichever is
   primary), with its four consequences, and say what happens when a replica is "stable" but has
   fewer than 3 feasible seeds; (c) sd_plan source: amendment stating the pilot 2-seed sd replaces
   DELTA's seeds 1-8, and delete "as written in DELTA §5.1" at l. 597; (d) wave-2a start
   condition: amendment for launching on replicas without anchor production snapshots; (e) the
   12-cell confirm cap; (f) R1: a cell whose traced floor is ≥ its target is removed, not run and
   read as degenerate (X4); (g) the 2a/2b ordering (floor family first) restored or amended with
   reason; (h) K6 and the teacher jobs listed as K2 Kai items ([D13] cites the orchestrator brief).
   Rewrite the change log l. 17-20 to list every departure.
5. **(B, #7, #10) Packing and anchor state.** Set E's K from the per-class memory canary like
   A07's ([D16], l. 473-476, 558-559), citing anchor `RUN.md` epoch-10 canary (6 × 4,354 MiB ≈
   26,124 MiB > 23,028 MiB); label every pod-hour and wall-clock row "assumes a GPU-throughput-bound
   per-slot cost of 218 / 6 s; K = 3 not measured". Re-pin anchor citations to the current anchor
   HEAD (c2f5447) or state which sha each cites; update Reference row l. 54 (A07-350-s1 re-runs in a
   K=3 pilot pod per the 1115121 amendment) and the timing basis (C′-s1 293.6 s/epoch at K = 6, old
   quantizer, epochs 1-5, labelled indication for the A07 class only); add the anchor's collapse
   label ("Deep-Set-class", with its three criteria) to the per-cell readout, descriptive. Add
   phys C1's fallback sentence.
6. **(B, #8) Always-on patches** in launch gate 3 / X2: every run needs them rebased and gated on
   the anchor tree; if one fails, the wave waits.
7. **(B, #9) Anchor config freeze:** add a launch gate (anchor [D15] answer recorded, or the
   anchor production config sha fixed), or a pre-registered relabel rule ("rep-A at config sha X")
   if the anchor changes after launch.
8. **(B, #5) Missing pairs:** restate g over seeds usable in both, n_p ≥ 3; report n_p per cell;
   rank cells with n_p < n in a separate list, or with a stated imputation (the anchor's
   surviving-minimum imputation, labelled as such) beside the survivor value. Say which in [D10].
9. **(B, #6) Ranking statistic:** report a second ranking by mean g with a family-pooled paired sd
   interval beside the DELTA LCB80 ranking; LCB80 stays primary unless Kai amends DELTA §5.3.
10. **(B, #11) Question:** rewrite frontmatter `question:` and l. 22-29 as the rule: one-sided
    improvement, BH-adjusted p ≤ 0.10 and mean g ≥ g0/2 with g0 = 0.3 pt the MDE target
    (significance mode); expected mode a declared ranking. Propagate to the experiment-log stub.
11. **(B, #12, #13) Floor family:** rank floor-family accuracy cells in a separate list labelled
    "cross-architecture package", never interleaved; size them with the Welch SE (or remove them
    from the advance decision and keep m = 19 fixed as a tightening). Report traced headroom
    (350,000 − own floor) and h beside k_e and k_base; a rescue with large static headroom is
    labelled structural.
12. **(B, #14) Bearing:** state that confirm either gives the matched non-binary arm the same
    recipe-level winners or labels the gap "binary tuned, baseline not".
13. **(B, #15) Readout:** add the five per-class validation AUCs per cell, any class under 0.7
    called out.
14. **(B, #16) Cheap version:** extend its rep-A to 1,000 and rep-C to 2,000 epochs and restate its
    budget, or drop M015, M031, M032 from it.
15. **(B, #17) [D14] limitation:** add an [L] that the 5M/A07 training-lever screen does not test
    transfer to 350k/E, and name the confirm cell that does.
16. **(B, #18) Conventions:** mark the accuracy-vs-AUC deviation in the "Selection under a budget"
    row; say check 3 is probably unavailable under replica-primary and what stands in (§6.8 note
    above); add Pitfalls rows for both conventions (cross-axis comparison applies to the floor
    family).
17. **(B, #19) [L1] attempt:** pre-register rep-A seed-rank persistence 500 → 1,000 and rep-C
    500 → 1,000 → 2,000, and the epoch-500 vs epoch-7,000 rank correlation across anchor arms when
    [A6] snapshots exist.
18. **(B, #20)** Label the per-cell "contradicted" list with its expected null count, 0.025·m =
    0.5 (350k) and 1.1 (5M), or apply the same BH.
19. **(B, #21)** In "Where I am not sure", replace the n_5M row's rejected alternative with the
    option "rep-A and rep-C at seeds 1-8 to epoch 500 at t = 0: +4,000 run-epochs, +40.4 / +60.6
    pod-hours, no wall-clock change, df-7 sd in both families"; remove the claim that it conflicts
    with "replicas first".
20. **(B, #22)** Replace the binomial-SE argument at l. 344-346 with the 3.14 pt and 0.6 pt
    arguments.
21. **(C, required before commit)** #24-#32: C27 certification count, C28 formula-check wording,
    C29 confound 8 list, C30 teacher leakage note, C31 baselines out of the ranked list and M010
    pairing purpose, one-line question and null; cons C6 two-stage result into `plan.md` dead ends.

## What Kai must decide (K2; blocks launch, not PASS)

The fixer writes each as a "Where I am not sure" row with its cost; Kai picks. None of these
blocks the STUDY PASS by itself; the artifact must present them correctly.

1. **Full W2 screen or cheap version.** Full: 294 runs at (4, 4) with placebos, about 1,736-3,068
   pod-hours at r = 1-2 (projection, to be regenerated by `budget.py`). Cheap: about 123 runs plus
   the fix-14 replicas, ranking only. Frame as coverage (T2 entries, baselines, 5M cells of
   two-target entries, long replicas), not resolution (n 3 → 4 changes a cell's SE by 1.15×).
2. **Replica seeds 1-8 to epoch 500** (cons B5): +4,000 run-epochs, gives a df-7 sd for both
   families and an input to the §5.1 rule at 5M; changes the guard ("never raises n") and the
   branch structure.
3. **Control branch:** always replica-primary, or the read-time rule [D6].
4. **Launching wave 2 without anchor production snapshots** (the dropped DELTA §7 2a condition) and
   without the anchor production config frozen.
5. **Branch S on a df-1 pilot sd**, or its upper bound, or branch R.
6. **n_5M** (4 in ranking mode, 8, or from replica seeds 1-8).
7. **Ranking statistic primary:** DELTA's LCB80 or mean g with a pooled sd (a DELTA §5.3 amendment).
8. **sd_rep ceiling value** and what the family does above it (fix 3).
9. **K6:** whether M047-M050 run at all; **teachers P-T1/P-T2** in this campaign.
10. **Training-only levers target** ([D14]: 5M on C, 350k on A, or both).
11. **A07 and E packing, GPU classes and pod count** (10 Delta pods beside the anchor, about 24 at
    peak, quota not checked; E at K = 6 does not fit an A10 by the anchor canary).
12. **Bop τ scan** (none, or a 3-point scan pre-registered from the |m| measurement).
