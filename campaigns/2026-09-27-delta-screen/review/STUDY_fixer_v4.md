# STUDY fixer v4: 2026-09-27-delta-screen (Delta wave 2)

Fixer, fresh context, 2026-09-27, after `review/STUDY_arbiter_v4.md` (ITERATE, 0 A / 8 B, iteration
4). This is a consolidation pass with a frozen scope: the arbiter's deletions, fixes 1-7, cons C2
(appendix), and nothing else added. STUDY.md is edited in place with a v5 change-log entry (no
regression ticket). Nothing is committed.

Scripts re-run (design arithmetic, not a result):
- `uv run --with numpy,scipy python screen_null.py` (seed 20260927, 17 s; re-run after the last
  edit). Every number of §1-§9, §11-§13 and §15-§17 reproduces digit for digit against the v3
  output; the diff is the deleted §10 and §14 lines, the two §3 label lines (reworded, same
  numbers) and the appended §18.
- `python3 budget.py`. Every line is identical to v4 except the three extension-band labels and the
  deleted [DK17] block.

Word counts (same tokenizer as `tools/prose_lint.py`, total 14,762, was 24,788):

| part | words |
| --- | ---: |
| Main text (frontmatter to the end of "Where I am not sure", change log excluded) | 11,957 |
| Change log (v1-v5) | 2,250 |
| Appendix A | 555 |

`prose_lint`: score 0, reads human.

## Per finding

```
1 (B, v4 #1+#5+#7) Labels read sd_rep, not the cell × seed interaction; the pause is close to a full launch; a paused family reads no test — RESOLVED
  changed: STUDY 441-452 (Replica epoch-500 readout: sd_rep has one role, the Appendix A seed rule); 652-663 ("Label": s_int
    defined, df (m − 1)(n − 1), sd_rep / s_int / s_pool / ρ̂ printed side by side, "ranked" if s_int ≤ T else
    "descriptive: recovery below 0.5 at this spread", family test read in every family, caveat once); 521-536 ([DK16] band on
    s_int, above T no extension); 573-577 (resolution set by n and σ√(1 − ρ), not σ); 730-737 (Falsifier: every family's
    list goes to Kai at K3a; a descriptive list supports nomination, never a resolved gap); [D7] 870, [D8] 872, [DK8] 884 and
    [DK17] 888 dated v5; cheap version 822-824 (s_int on 3 seeds, df 2(m − 1), "threshold simulated at n = 4");
    [DK2] reason 974-977. Deleted: the pause everywhere, [DK17] bullet and block, four options, three budget rows,
    Falsifier (v), the no-family-test line, "guard wording", the (4, 4)-only-if-pass wording.
  verified: screen_null.py re-run (above); budget.py re-run (above); grep in "Grep sites" below
  propagated: 27 STUDY grep sites, 7 plan.md lines, budget.py, screen_null.py, stub (listed below)
  neighbourhood: every use of sd_rep (now only Appendix A, the readout print and [D7]/[L3]); every [DK16] band mention
    (Seeds, [DK16] label, DECISION block, budget.py label, stub); every "family test" mention (Selection rule, Falsifier,
    box, cheap version) reads "in every family"
2 (B, v4 #2, absorbs phys C4) Ranking and extension simulated for Gaussian seeds only; threshold must hold under two-mode seeds — RESOLVED
  changed: screen_null.py §18 appended (per-run and seed-shared mode, jump 5.4, within-mode sd 0.3, q grid of 52 values incl.
    0.02 / 0.05 / 0.1 / 0.33 / 0.5; m 37 / 11; median s_int, recovery, [DK16] extension, the threshold rule with conditional
    set sizes). STUDY 551-577: Gaussian table labelled "design grid m = 37" and "optimistic under per-run two-mode seeds",
    two-mode table beside it; §16 rows labelled the same (531-536) with the two-mode extension rows.
  verified: §18 returns T = 1.3 pt (5M) and 1.5 pt (350k). Arbiter scratch values reproduced by the script: 5M median s_int
    0.80 / 1.20 / 1.64 (arbiter 0.81 / 1.20 / 1.64); recovery | s_int ≤ 1.3 = 0.79 / 0.62 / 0.51 (arbiter 0.78 / 0.61 /
    0.55; the q 0.1 set is 823 of 20,000 draws, SE about 0.02); 350k unconditional 0.49 / 0.45 at q 0.33 / 0.5 (arbiter
    0.48 / 0.45), median s_int 2.56 / 2.72.
  propagated: T in STUDY "Label" (656), [DK8] DECISION block (926), change log v5, stub; 3 locations, all cited to §18
  neighbourhood: every Gaussian recovery row (fidelity table, §16 rows, [DK16] block) now carries the optimistic label or
    sits beside its two-mode row
  remains / route to: two points for Kai, both in the [DK8] and [DK16] rows (not design changes by the fixer):
    (a) the arbiter's grid condition "consecutive median s_int within 0.1 pt" cannot hold below 1 pt: the median jumps
        where the m × 4 matrix goes from 0 to 1 to 2 low-mode runs (0.19 pt at 5M, 0.42 pt at 350k). Above 1.0 pt the largest
        step is 0.055 / 0.093 pt. §18 prints both. No T candidate in the jump region decides T.
    (b) the rule was applied literally ("wherever the conditional set is non-empty"). At 350k, T 1.6-1.9 fail on sets of
        1-8 draws (q 0.39-0.44), and T 2.0-3.0 fail on sets of 34-18,795 draws at 0.26-0.44, so the small-set failures
        agree with the large ones. At 5M, T 1.4 fails on 201 draws (0.43). No minimum set size was added.
    Also found: under per-run two-mode seeds, among draws in the band, the [DK16] extension adds no recovery (5M 0.61 /
    0.58 / 0.51 → 0.61 / 0.56 / 0.49; 350k 0.80 / 0.79 / 0.77 → 0.80 / 0.78 / 0.74). Reported in Seeds and the [DK16]
    row; the rule is unchanged (a design call for Kai).
3 (B, v4 #3, with cons C1, C3) Floor-family G2 posed as live but uninformative — RESOLVED
  changed: frontmatter l. 6 → the "In one line" sentence plus pointers; Question 211-215 (the Welch package is the
    informative quantity, G2 a feasibility count, "rescue expected from floor arithmetic", M001 borderline 171,526 against
    171,526.5); Selection rule G2 612-621 ("structural, by construction" → "rescue expected from floor arithmetic",
    headroom necessary, not sufficient, as cons C3 asks). The [DK17] half is gone with fix 1.
  verified: grep "structural, by construction" → change log only (v4 entry l. 122, v5 entry l. 163-164)
  propagated: stub Question and Design lines
  neighbourhood: the Welch list (631-644) names the package; the box (184-200) no longer poses G2
4 (B, v4 #4) M006, M009 inside the "paired" 5M ranked list; paired bound 35 — RESOLVED
  changed: Lists 631-644 (the one statement of membership: ranked list "at most 35 paired cells"; M006, M009 and M046 if
    [A17] fails in the Welch list; design values at "design grid m = 11 / 37", read re-simulates at the actual m); box 185;
    Counts 326-330; fidelity caption 551 ("design grid m = 37"); family-test calibration, critical values, multiplier,
    rank-move and ρ̂ rows labelled "design grid". Not re-simulated at 35, as instructed.
  verified: grep "m ≤ 37|at most 37|up to 37|37 cells|of 37" → change log v4 entry only (l. 115)
  propagated: stub Design line
  neighbourhood: 350k list checked (11 cells; M016, M040, M042, M043, M045 are paired-if-hash and go to the Welch list only
    if their check fails, already the rule); M046 is in the grouped cells table with "paired if [A17], else Welch"
5 (B, v4 #6) "Mechanism not exercised" inferred from rep-C — RESOLVED
  changed: Controls 454-468 (per-cell label for M003, M007, M008, M011, M012 at 5M on their own seeds, same ⌈3k/4⌉; family
    label stays on rep-C; crit C1: one line each for 0.8 and 0.9, β tolerance |log10 β − log10 1e-10| ≤ 0.01); readout per
    cell prints (a)-(c) for those five cells; [DK18] block 951-959
  verified: text; no number changed
  propagated: stub Design line
  neighbourhood: Falsifier (v) and [L7] read the family label; the cell label is read only in Controls and Readout
6 (B, v4 #8) Two-mode seeds only a calibration nuisance — RESOLVED (minimal, as the arbiter scoped it)
  changed: Controls 447-451 (mode readout on the 8 replica values: two-mode if the largest gap exceeds 3× the pooled
    within-cluster sd with ≥ 2 seeds each side; midpoint fixed as the mode threshold); Readout per cell (n_low of n beside
    mean g with the replica's and placebo's). No decision reads it. Within-mode g not added (arbiter dismissal).
  verified: text
  propagated: stub Design line
  neighbourhood: s_int / ρ̂ print (fix 1(b)) is the "is the low mode seed-shared" half
7 (C, rows 9-19) — RESOLVED
  phys C1: 713-719 "carries no information on ρ"; the ρ = −0.5 rows kept as "stress case" (546-547)
  phys C2: 754-756 flag worded "pack-composition effect or nondeterminism, not separated"
  phys C3 / crit C3: 738-741 "≤ 0.025 · (cells read), printed at the read"
  phys C5 / crit C2: 641-644 packable-today m 9 / ≤ 32; 525 "k stays 16 / 6 whatever the actual m" (Budget rows at these k)
  crit C4: n_p (g) and n_d (d) throughout (Pairs 602-606, family test 665, losses 483-489)
  crit C5: [L7] 910-914 "if Kai decides so at K3"
  cons C1: frontmatter question (fix 3)
  cons C2: significance mode moved to Appendix A (1029-); one pointer each in the box, Question, Seeds, Falsifier
  cons C4: 1013-1016 init-vs-order factorial named as the follow-up
```

## Consolidation (orchestrator's scope rules)

- Rule 1 deletions: done (see grep list). Kept: the A07 memory pause (launch gate 7, l. 399-401) and
  the base-stability pause (l. 470-472).
- Rule 3, nothing added beyond the fix list: the only new text is s_int and its print, the threshold
  rule and §18, the Welch-list move, the per-cell constraint label, the n_low line, and the C items.
  The two §18 observations in "remains" above are reported, not acted on.
- Rule 4, numbers in more than one place: T (1.3 / 1.5) and every §15-§18 and `budget.py` number
  that repeats is cited to its section. The calibration rows, power rows, P(no | null), critical
  values and multiplier now each appear once (Selection rule or Falsifier); the box, Null, [DK7]
  and cheap version point to them. "48 of 302" appears once (change log v5, cited to `budget.py`
  v4). The pod count "about 27" appears once in the body ([A3]).
- Rule 5, duplicated explanation removed: the [DK] labels are one-liners pointing to "Where I am not
  sure"; DECISION blocks for [DK3]-[DK5] and [DK9]-[DK15] are merged; the cells table is grouped by
  identical (350k role, 5M cell, H, pairing), keeping every entry's assignment (counts re-checked: 23
  at 350k, 40 G3 + 4 baselines at 5M), with names and deltas left to `delta.json`; [DK1]/[DK16]
  budget prose points to the Budget table, which now carries pod-hours and wall clock in the same
  table. Change-log entries v1-v4 are unchanged except four annotations of withdrawn rules (l. 33,
  56, 128-129, 133-134).

## Grep sites (arbiter "Independent checks"), each changed or unaffected

Line numbers on the left are the v4 file (0b11518).

| site | status |
| --- | --- |
| STUDY l. 6 (frontmatter question) | changed: "In one line" sentence plus pointers |
| l. 32 (v2 entry, pause) | annotated "withdrawn in v5" |
| l. 56 (v2 entry, ceiling 1.3 pt) | annotated "withdrawn in v5" |
| l. 126-128 (v4 entry, pause is a likely branch) | annotated "withdrawn in v5" |
| l. 158-163 (box, pause) | deleted; box rewritten (two-mode sentence, label) |
| l. 176-177 (Question, ranking mode "if the family passes") | changed: ranking question with its label |
| l. 391-393 (Counts, "only if both pass", 254) | changed: Counts rewritten, runs point to Budget |
| l. 595-597 (sd_rep's roles) | changed: one role, Appendix A |
| l. 710 ([DK16] band, pause above) | changed: band on s_int, above T no extension |
| l. 734-767 (ceiling, P(pause), on a pause, guard wording) | deleted |
| l. 769-779 (expected outcome) | changed: moved to Appendix A (not armed) and the box |
| l. 946-947 (paused family reads no test) | deleted; "read in every family" |
| l. 1083-1084 (Falsifier (v)) | deleted; old (vi) is (v) |
| l. 1105 ((4, 4) row label) | changed: "(4, 4), the design" |
| l. 1115-1117, 1161-1163 (pause rows) | deleted |
| l. 1220-1221 (cheap version ceiling on 3 seeds) | changed: s_int on 3 seeds, df 2(m − 1) |
| l. 1292-1294 ([D8]) | changed: dated v5 amendment |
| l. 1347-1348 ([DK8]) | changed: label threshold T, dated v5 |
| l. 1375-1377 ([DK17] bullet) | deleted; "[DK17] withdrawn in v5" |
| l. 1409 ([L3] "at the ceiling") | changed: "a point estimate in the seed rule" |
| l. 1448-1453 ([DK1] block) | changed: points to the Budget row |
| l. 1511-1516 ([DK8] block) | changed: T per family with the §18 detail |
| l. 1573 ([DK16] block, pause) | changed: band on s_int, two-mode note |
| l. 1583-1594 ([DK17] block) | deleted |
| l. 1621-1622 (Other rows, n_5M) | deleted (n = 4 in ranking mode is stated in Seeds) |
| l. 1666 (Literature §2, "pause and ceiling rows") | changed: "the ranking carries two-mode rows" |
| fix-list extras: l. 809-811, 1319-1321, 1056-1058, 1047-1053, 150, 388-389, 797-798, 901, 959-961, 612-614, 1596-1598, 189-196, 871-879, 153 | changed (per findings 1-5 above) |
| plan.md l. 73, 84, 114, 119, 122, 129, 153 | tagged "[superseded v5: …]"; l. 128 is the start of the l. 129 sentence (tag at 129) |
| budget.py l. 39 (docstring) | changed: "withdrawn in v5" |
| budget.py l. 63-78 (pause_keep, paused=) | deleted |
| budget.py l. 184-185 (report paused=) | deleted |
| budget.py l. 247-253 ([DK17] block) | deleted |
| screen_null.py l. 2 (title "sd_rep ceiling") | changed: "label threshold" |
| screen_null.py l. 19 (§3 docstring, ceiling) | changed: "the v1 ceiling, withdrawn in v5" |
| screen_null.py l. 40 (§10 docstring) | changed: "withdrawn in v5" |
| screen_null.py l. 51-57 (§14 docstring) | changed: "withdrawn in v5" |
| screen_null.py l. 134 (§3 print "sd_rep ceiling") | changed: label only; the §3 numbers are unchanged |
| screen_null.py l. 234 (§10 code) | changed: draws kept, print removed (stream preserved) |
| screen_null.py l. 270 (§14 code) | deleted (exact, no draws) |
| experiment-log stub l. 12 | changed: header, Question and Design rewritten in place |

Final grep over STUDY.md (`pause|paused|ceiling|DK17|sd_plan|structural, by construction|m ≤ 37|at most
37|268|254|286|270|branch taken only if|before its cells launch|§10|§14|(vi)|P(pause)`). Survivors:
- change-log history (l. 26, 32-33, 56, 99, 110, 115, 122, 126-134, 147-155);
- the A07 memory pause (l. 401) and the base-stability pause (l. 472);
- [D8], [DK8] and [DK17] saying "withdrawn in v5" (l. 873-874, 885, 888) and the no-touchpoint row
  (l. 945);
- `sd_plan` in Appendix A;
- "DELTA §10" (l. 729), which is DELTA's section, not `screen_null.py`.

## CANNOT RESOLVE

None.

## Record or outward copies for Kai

None. No number of this screen is in the record or outward. `INDEX.md` l. 7 and
`.claude/memory/index-head.md` l. 7 still carry the pre-v2 question line. They are regenerated from
the frontmatter by `python3 tools/index.py build`, which is the orchestrator's step.
