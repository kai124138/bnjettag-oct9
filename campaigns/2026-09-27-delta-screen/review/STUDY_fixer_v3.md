# STUDY fixer v3: 2026-09-27-delta-screen (Delta wave 2)

Fixer, fresh context, 2026-09-27. Input: `review/STUDY_arbiter_v3.md` (ITERATE, iteration 3; 0 A,
10 B, fix list v3 #1-#10 and C rows 11-26), `review/STUDY_fixer_v2.md`, the three v3 panel files and
`constructive_v3_*.py`, `research/screen-design-literature.md` (physics-researcher), `plan.md`,
`budget.py`, `screen_null.py`, `rank_sim.py`, `.claude/agents/experiment-designer.md`,
`campaigns/2026-09-26-delta/code/GATES.md` §6, the rep-C config, the anchor tree's
`is_traced_epoch`, `decisions.md` l. 28 and 80. STUDY.md is edited in place with a v4 change-log
entry (l. 98-142); there is no regression ticket. Line numbers below were taken at 1,678 lines;
three one-line additions came after them (sd_rep usable-count clause l. 594-596, Budget
reachability sentence l. 1119-1120, [D8] amendment tag l. 1293-1295), so the final file has 1,681
lines and citations after l. 594 sit 1-3 lines later. Nothing was launched, no other campaign was edited, nothing was committed.

The orchestrator's defaults for the arbiter's new Kai items are written as [DK16]-[DK18], each
"default, Kai may override at the launch gate": [DK16] top-k extension in the 1.0-1.3-pt band;
[DK17] feasibility plus a descriptive T0/T0a/T1 ranking on a pause; [DK18] 350k follow-up of the
training-only levers if the 5M constraint is slack. X5 stays a launch gate, and the STUDY now says
that the non-binary path is anchor [A22] (being written by the training-batch session) and that the
Delta rebases on it.

## Scripts run (design arithmetic, nothing quotable)

- `uv run --with numpy,scipy python screen_null.py` (v3). §1-§13 are byte-identical to the v2 output
  (`diff` of the first 123 lines: no difference). New §14-§17 are appended. §13 now also stores its
  values for reuse (no change to the random stream). The arbiter asked for P(pause) "in §10". It is
  in §14 instead, as an exact chi-square, so that §10-§13 keep their random stream and their quoted
  values.
  - §14, P(sd_rep > 1.3 pt), 8 / 6 usable seeds: 0.000 / 0.000 at σ 0.6; 0.106 / 0.133 at 1.0;
    0.629 / 0.585 at 1.5; 0.889 / 0.833 at 2.0; 0.991 / 0.973 at 3.14. These match the arbiter.
  - §13 / §15, m = 11 / 37: R2 critical values 4.284 / 6.585 (n 4) and 6.733 / 12.290 (n 3).
    False "yes" at n 4 is 0.102-0.106 / 0.099-0.108 (equal and unequal spread), 0.036-0.052 /
    0.051-0.082 (two-mode), 0.100-0.102 / 0.099 (offset) and 0.099 / 0.097 (near-deterministic).
    At n 3 it is 0.100-0.105 / 0.100-0.104 (equal and unequal) and 0.063-0.115 / 0.081-0.232
    (two-mode). Power at σ 0.6 / 1.0 / 1.5 / 3.14 is 0.214 / 0.087 / 0.051 / 0.026 (m 11) and
    0.077 / 0.030 / 0.016 / 0.007 (m 37). The ranking multiplier is 2.168 / 2.136 (nominal
    coverage 0.936 / 0.933). ρ̂ null is −0.34 / +0.34 and −0.18 / +0.18. Unpaired critical values
    are 2.880 / 3.590. The rejected "no cell exceeds the placebo" wording gives P(no) 0.084 / 0.026
    (1/(m + 1) 0.083 / 0.026). Rank-move null counts: at m 11, r 0.9 / 0.7 / 0.5 with T 3 / 5 / 6
    gives 0.7 / 0.6 / 0.6; at m 37, r 0.95 / 0.9 with T 10 / 15 gives 0.6 / 0.3, and r 0.7 with
    T 15 gives 3.2. For recovery, the 5M ceiling criterion at m = 37 gives 1.4 pt (0.57 at 1.3,
    0.52 at 1.4, chance 0.028), and the 350k criterion at m = 11 gives ≥ 3.0 pt (the grid end,
    chance 0.27).
  - §16, top-k extension, P(all true cells in the final top): n = 4 / extension / n = 6. At 5M
    (m 37, top 16 extended) this is 0.77 / 0.87 / 0.90 at σ 1.0 and 0.57 / 0.69 / 0.72 at 1.3. At
    350k (m 11, top 6) it is 0.89 / 0.96 / 0.95 and 0.79 / 0.90 / 0.87.
  - §17, floor-family false rescue, n 4: 0.038 / 0.121 / 0.104 at p 0.25 / 0.5 / 0.75 (× 7: 0.27 /
    0.85 / 0.73). At n 3: 0.013 / 0.063 / 0.066. At k_base 0 or 1: 0.312 / 0.738 / 0.948 at p_e
    0.5 / 0.75 / 0.9. At k_base 2: 0.062 / 0.316 / 0.656. The arbiter's values reproduce.
- `uv run --with numpy,scipy python rank_sim.py`: the earlier 25 lines are identical (diffed). The
  appended m = 37 block gives mean-g / LCB80, P(all 3 in top 12), chance 0.0283. At σ 0.6 every
  cell is 0.99-1.00. At σ 1.5: +1 pt 0.47 / 0.40 (ρ 0) and 0.73 / 0.65 (ρ 0.5); +3 pt 1.00. At
  σ 3.14: +1 pt 0.16 / 0.14 and 0.26 / 0.22; +3 pt 0.74 / 0.66 and 0.94 / 0.90.
- `python3 budget.py` (v4). The first 27 lines (the full-design table and cheap version) are
  identical to v3. New rows at (4, 4):
  - Packable today: 240 runs (212 cell, 8 placebo, 20 replica), 142,000 run-epochs (E 32,000 /
    A07 110,000), 897.4 / 1,592.5 pod-hours, 4.5 / 7.9 d, 256 certifications.
  - [DK16] extension, both families: 390 runs, 220,000 run-epochs, 1,390.3 / 2,439.3 pod-hours,
    6.7 / 11.6 d, 406 certifications. The increment is +88 runs (64 A07, 24 E), +44,000
    run-epochs, +278.1 / +480.3 pod-hours.
  - [DK16] extension at 5M only: 366 runs, 1,314.4 / 2,363.5 pod-hours, 6.6 / 11.6 d.
  - [DK16] extension at 350k only: 326 runs, 1,188.1 / 2,034.9 pod-hours, 5.9 / 9.7 d.
  - [DK17] pause, 350k paused: 286 runs, 168,000 run-epochs, 1,061.7 / 1,908.5 pod-hours,
    5.0 / 9.0 d.
  - [DK17] pause, 5M paused: 270 runs, 160,000 run-epochs, 1,011.1 / 1,756.8 pod-hours,
    4.9 / 8.2 d.
  - [DK17] pause, both paused: 254 runs, 152,000 run-epochs, 960.6 / 1,706.2 pod-hours,
    4.6 / 8.2 d.
  - [DK18] 350k follow-up: 18 entries, 84 runs, 58,000 E run-epochs, 366.5 pod-hours, 2.6 d.
  - The K_E = 5 alternative block is unchanged and printed last.
- `python3 tools/prose_lint.py STUDY.md`: score 0, reads human (24,689 words).

## Per finding (arbiter priority order)

```
1 (B, v3 #1) Placebo still "only `name`" in change log, Question, [DK7], stub — RESOLVED
  changed: change log l. 84-89 (v3 item reworded to the Arms key set and assertion); Question
    l. 180-183 ("under another run name" → run-identity and provenance keys and train.epochs);
    [DK7] l. 1333-1343 (full key set and assertion); experiment-log stub Design line
  verified: grep 'only `name`', 'another `name`', 'run name' in STUDY.md, plan.md, stub: the one hit
    left, l. 266, is the W&B run name in the Arms mechanism (correct)
  propagated: 4 instances across 2 files   neighbourhood: X2 assertion l. 413-416, cell-key class
    (3) and Arms l. 255-274 re-read: consistent with the stub wording now

2 (B, v3 #2) One family-test reference; probe decides only the placebo row — RESOLVED
  changed: branch (i) test switch deleted with 4.43 / 6.79 and 0.261 / 0.258 / 0.103 / 0.096
    (old Selection l. 776-785) → "Two readings of the placebo row" l. 947-957 (bit-identical =
    equal epoch-500 hashes at every same-product seed across pods; any differing seed → divergent
    reading; family test identical in both). Family-level test l. 919-946 "in every case". Launch
    gate 7 l. 509-531: probe per class (E and A07), same config and seed in two pods of one
    product, 21 epochs, traced set named (ends of epochs 1, 10, 20, 21 on the staged bundle;
    10, 20, 21 on the committed text; PREFLIGHT prints); outcome changes nothing in the test;
    placebos launch whatever it finds (crit C5). Check (iv) l. 1071-1082: sd-0 rule and "any
    nonzero per-seed placebo g on a shared product flags" where the probe found it
    bit-identical. Formula check l. 1086-1091, Check paragraph l. 811-815, Arms l. 275-281,
    [DK7] row, stub rewritten to match. v4 change-log entry states the withdrawal (l. 101-107)
  verified: grep 4.43, 6.79, 0.261, 0.258, "no-offset", "bit-identical branch", "placebo branch",
    "3 epochs": only the v4 change-log line that records the withdrawal remains
  propagated: 5 places (Selection, Falsifier (iv) and formula check, [DK7] decision row, stub)
    across 2 files   neighbourhood: the literature note's §5 quotes "0.10 vs 0.26" for the old
    branches; it is physics-researcher's file and was not edited (listed below)

3 (B, v3 #3) Packable-today row overstated (268 → 240) — RESOLVED
  changed: budget.py main block (M009, M038, M040, M041 added to the exclusion); Budget
    l. 1173-1183: 268 / 156,000 / 985.8 / 1,744.2 / 4.9 / 8.4 d / 284 → 240 (212 + 8 + 20) /
    142,000 / 897.4 / 1,592.5 / 4.5 / 7.9 d / 256, citing GATES §6 l. 836-842 and the packs JSON
    (220 + 20); [DK1] row l. 1445-1450; plan.md l. 89 tagged superseded with the new number;
    stub. Gates 3 and 13 now agree: the intro l. 465-467 names the per-cell exception, gate 3
    l. 490-494 states the rule once (a missing Z10 cache or Z01 trace holds back only its own
    cells), gate 13 l. 557-558 refers to it
  verified: budget.py prints "cell runs 212, placebo runs 8, replica runs 20 … total runs 240"
  propagated: 7 numbers × 3 files (STUDY Budget and [DK1], plan.md, stub)
  neighbourhood: X4 ("a cell whose trace is missing … excluded like X2") and X5 read against
    gate 3: consistent; no other "268" / "156,000" in the repo outside review/ (DELTA.md l. 878's
    268 is wave 3, unrelated)

4 (B, v3 #4) Long-horizon cells ranked with H-500 cells and pooled into s_pool — RESOLVED
  changed: Lists l. 958-967 (new list (2) "horizon H ≠ 500", rows marked with H, not ranked, not
    in s_pool or the family test); Families l. 895-904 (ranked list = family-test set, m 11 /
    ≤ 37); Ranking mode s_pool "ranked H-500 cells only; placebo and long-horizon excluded";
    [L8] l. 1429-1432 rewritten to match Arms and Selection; Arms l. 278-281; Counts l. 385-393.
    Re-simulated at m 11 / 37 instead of keeping the 12 / 40 grid: box l. 149-172 (11 / up to 37;
    fidelity 0.16-0.26 vs 0.028; power 0.214 / 0.051 / 0.026 and 0.077 / 0.016 / 0.007);
    Null l. 198-206 (rates, 0.084 / 0.026 with 1/(m+1) = 0.083 / 0.026, phys C3); ranking
    multiplier 2.18 / 2.15 → 2.17 / 2.14; family-test critical values 4.41 / 6.75 → 4.28 / 6.59
    and 6.95 / 12.98 → 6.73 / 12.29 (Selection, replica-loss rule l. 637, cheap version
    l. 1214); scenario rows and power at m 11 / 37; rank-move null counts; ρ̂ −0.32 / +0.33 →
    −0.34 / +0.34 (m 11); unpaired 2.92 / 3.62 → 2.88 / 3.59; fidelity table l. 796-806 at 37
    cells (chance 0.018 / 0.022 → 0.028); ceiling derivation l. 733-742 ("top 12 of 40" → 37:
    the criterion gives 1.4 pt; 1.3 kept as the stricter default, 1.4 listed as an [DK8]
    alternative); Falsifier l. 1046-1057; [DK6], [DK7], [DK8] rows; stub. The comparison rows for
    the rejected rules stay at the design grid m 12 / 40 (§4-§5) and are labelled so
  verified: screen_null.py §13, §15; rank_sim.py m = 37 block (outputs above)
  propagated: 14 distinct values (m, 4 critical values, multiplier ×2, power ×6, ρ̂ ×2, unpaired
    ×2, chance, fidelity ×12, v1-wording ×2), in the box, Null, Seeds, Selection (Families,
    Ranking, Family test, companions, pairing), Falsifier, cheap version, [DK6]-[DK8] and the stub:
    about 45 instances across 2 files
  neighbourhood: every "m = 12", "m = 40", "(m 12)", "(m 40)" and "of 40" grepped; the remaining
    ones are labelled design-grid comparisons of the rejected rules (l. 929-935, [DK7]
    alternatives); BH m (19 / 43) and the "contradicted" count use BH m and are unchanged

5 (B, v3 #5) Rank-move r not centred per cell — RESOLVED
  changed: l. 982-991: r = correlation of primary and companion values centred per cell, pooled
    over the family's ranked cells, "the within-configuration correlation that §8 and §15
    draw"; T is the smallest grid value with null count ≤ 1.0 at the band's lower edge (T 3 / 5
    / 6 and 10 / 15 unchanged; null counts restated at m 11 / 37)
  verified: §15 rank-move rows   propagated: "Other rows" decision block l. 1624-1628
  neighbourhood: ρ̂ (l. 1021-1026) already centres per cell; the unpaired companion does not use r

6 (B, v3 #6) Literature note — RESOLVED
  changed: "Where I am not sure", Literature l. 1654-1678: the note is cited with its owner
    (physics-researcher, requested by the orchestrator 2026-09-27). Each point is applied or
    answered in one line. Multi-fidelity → [L1] l. 1387-1392 (no transfer number exists; the
    extension adds seeds at a fixed horizon, so it does not rely on the successive-halving
    assumption). Heavy-tailed seeds → own sd, and the Gaussian pause rows are labelled a guide
    (l. 744-750). Init and order conflation (Dodge) → a VERIFY note, no design change.
    Bouthillier is cited from its abstract only and none of its numbers is used. Winner's
    curse → the companions are labelled mitigations, and the seeds-5-8 mean is the
    selection-free estimate (l. 994-999). Dunnett → kept. Variance moderation → not covered by
    the note; it is recorded in plan.md dead ends. Nondeterminism → gate 7 and the placebo
    readings
  verified: the note was read whole   propagated: none needed
  neighbourhood: the note's "log lines to append" are not written to research-log.md (not the
    fixer's to add; listed below)

7 (B, v3 #7) Floor-family G2 null rate and numeric trigger — RESOLVED
  changed: Question l. 189-195 and G0-G3 l. 864-877. Rates printed from §17. Trigger: "traced
    floor ≤ ½ of A07's 343,053 = 171,526.5". M001's 171,526 sits at the line and is flagged as
    exactly half (two heads of four). The GATES §6 floors are listed, and every traced entry
    meets the trigger; M006 is read against it once traced. For those entries the informative
    quantity is the cross-architecture accuracy, not G2. Stub updated
  verified: §17 output; 171,526 / 343,053 = 0.4999985
  propagated: stub   neighbourhood: McNemar and "contradicted at screen" for the floor family
    (Falsifier) unchanged; k_base = 0 is the expected value (A07-350 has no completed epoch)

8 (B, v3 #8) 5M constraint active — RESOLVED
  changed: Controls l. 600-614 fixes the rule on rep-C at epoch 500. Per seed it reads (a) the
    fraction of traced epochs 251-500 over 5M, (b) the selected EBOPs / 5M and (c) the fraction
    of epochs 251-500 with β at min_beta 1e-10 (the rep-C config values are quoted). A seed is
    slack if (a) = 0, (b) ≤ 0.8 and (c) ≥ 0.9; the family is slack if ⌈3k/4⌉ of k seeds are.
    The rule holds nothing back. Falsifier (vi) l. 1083-1085; [L7] l. 1422-1428 (slack form);
    [DK10] and [DK18] labels and rows (l. 1593-1602, with the budget.py follow-up cost);
    "Where I am not sure" closing paragraph; stub
  verified: rep-C config train.ebops.pid read (init 1e-7, min 1e-10, max 1e-3, log true);
    budget.py [DK18] row
  propagated: none (new)   neighbourhood: the EBOPs-pressure list (M003, M007, M008, M011,
    M012) is the arbiter's; M013 (PID gains) is 350k only and M016 is not an EBOPs lever

9 (B, v3 #9) Pause as a likely branch — RESOLVED
  changed: Seeds l. 744-766 (P(pause) from §14; the Gaussian caveat with the literature cite;
    [DK17] default with its budget.py cost, and the other three options listed with their
    costs); Expected outcome l. 768-780 rewritten (pause likely; 0.19-pt bracket labelled "101
    epochs, early stopping, archived Round-14 recipe", no longer called evidence that 0.6 pt is
    plausible); Reference table l. 235 (label and experiment-log source, cons C5, required);
    box l. 157-162; Question l. 176-177 and frontmatter question; Counts; Budget tables
    (pause rows); [DK1], [DK8], [DK17] rows; "n_5M" other row; stub
  verified: §14 (0.000 / 0.629 / 0.991 match the arbiter's 0.00 / 0.63 / 0.99); budget.py
  propagated: 6 places in STUDY plus the stub   neighbourhood: the §10 false-pause / false-pass
    rows (l. 739-742) agree with §14's exact values (0.041 / 0.202 at 0.9 / 1.1)

10 (B, v3 #10) Ranking-mode n rule — RESOLVED
  changed: Seeds l. 707-731: [DK16] with limits (1)-(5): H-500 only; placebos and the family
    test stay at n = 4, because the extended cells are selected on seeds 1-4; the seeds-5-8 mean
    is the selection-free estimate; ordering and pooled interval for mixed n; loss of a replica
    seed among 5-8. Recovery comes from §16 and the cost from budget.py (+88 runs, +44,000
    run-epochs, 1,390.3 / 2,439.3 pod-hours, 6.7 / 11.6 d). [DK16] label l. 1368 and decision
    row l. 1567-1578. Budget rows. Replica-loss rule l. 646-647. Stub
  verified: §16; budget.py extension rows. The wall clock releases the extension when the last
    H-500 pack of the n = 4 schedule ends
  propagated: none (new)   neighbourhood: the priced (6, 4), (4, 6), (6, 6) rows are named as the
    alternative; the significance-mode rule is unchanged and takes precedence
```

Advisor-prompted closures in the same pass: the Budget sentence "an n above 4 … not expected"
now separates significance mode from [DK16] (constructive B1's "unreachable rows"); the sd_rep
usable-count rule says that a survivors-only value in 1.0-1.3 pt still triggers [DK16]; [D8]
carries a dated v4 amendment tag for [DK16] and [DK17].

C items (rows 11-26), applied:

- Crit C1: the replica loss no longer costs the family test a seed, and a loss at a longer
  horizon lowers n only for that H (l. 632-647).
- Crit C2: 51 traced epochs in the first cycle is the expectation, with 50 on the committed text
  (l. 821-828, [L6], closing paragraph, stub, gate 7).
- Crit C3 and cons C7: RUN.md pinned at c9c9942 for the split (frontmatter, Reference row). Both
  bundle shas are named, with "PREFLIGHT fixes which" (frontmatter).
- Crit C4: the [L1](a) epoch-500 readouts are labelled "uncertified, [L1] only" ([L1],
  Certification).
- Crit C5: the placebos launch in both readings.
- Crit C6: the pooled interval is labelled "95 % at equal spread".
- Crit C7: a slot-second note is under the pod-hour table.
- Crit C8: the `plan.md` v1 sections are tagged superseded.
- Phys C1: "a 'no' is not evidence of absence" is written beside every family-test answer.
- Phys C2: two ρ = −0.5 half-width rows (±1.65 and ±8.65 pt).
- Phys C3: 0.023 attributed to the simulation.
- Phys C4: the forest plot shows d and g for a named cell (Selection and the figures row).
- Cons C1: the moderated max-t is recorded in `plan.md` dead ends with the reviewer's numbers.
- Cons C3: review-cycle references are removed from the body. What remains is the [D] "amended
  vN" tags and "the review's range".
- Cons C8: covered by fix 4.

No CANNOT RESOLVE. Nothing here needs a Nautilus job or a `mulder` run.

## Record or outward copies for Kai

- None of the changed numbers appears in a record or outward file. `grep -r` over `*.md`
  (excluding review/, archive/, research/, publication*, sessions/) finds 268 / 156,000 /
  4.43 / 6.79 / 0.261 / 0.258 / 'only `name` changed' only in this campaign's STUDY and plan
  (labelled historical) and an unrelated wave-3 count in DELTA.md l. 878.
- For the orchestrator, not edited by the fixer:
  - `research/screen-design-literature.md` §5 and its implications list quote the withdrawn
    branch rates ("0.10 vs. 0.26"). That is physics-researcher's file.
  - The note's four proposed research-log lines have not been added to
    `.claude/memory/research-log.md`.
  - INDEX.md and index-head.md carry the campaign title only and are regenerated by
    `tools/index.py build`.
