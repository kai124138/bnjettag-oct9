# STUDY fixer v5: 2026-09-27-delta-screen (Delta wave 2)

Fixer, fresh context, 2026-09-28, after `review/STUDY_arbiter_v5.md` (ITERATE, 1 A / 6 B, iteration
5; this pass is iteration 6) and Kai's answers of 2026-09-28 (`.claude/memory/decisions.md` top
entry, verified: (a) median of the 4 paired gaps is the primary ranking statistic, [DK6]
re-decided; (b) if round 6 finds only new B items, the design is frozen and launched with them
disclosed). Scope freeze as in v4: fixes 1-7 in the arbiter's order, nothing added beyond them and
Kai's decision. STUDY.md edited in place with a v6 change-log entry (no regression ticket). Nothing
committed, nothing launched.

Scripts re-run (design arithmetic, not a result):
- `uv run --with numpy,scipy python screen_null.py` (v5; design seed 20260927; 57 s with nine
  child processes). **§1-§17 reproduce digit for digit** against the v4 output (diff of everything up
  to the "18." header is empty), and every §18 grid, seed-shared, and step line is also unchanged. What
  changed in §18 are the T-rule failure lines, the T lines and the conditional rows at the new T.
  §18b, §18c, §15a and §18d are appended after the last existing draw (§18d added last, after an
  advisor check; the output above it is unchanged by that addition, diffed).
- Per-seed T matches `review/arbiter_v5_tstab.txt` in all 40 values (2 rules × 2 families × 10 seeds).
- `python3 budget.py`: output identical to v5 (diffed).
- `tools/prose_lint.py STUDY.md`: score 0, reads human (16,095 words, 1 em-dash).

**T values: 1.2 pt (5M), 1.8 pt (350k)**; per-seed ranges under the floor rule 1.2-1.3 / 1.8-1.9.

Word counts (whitespace tokens, same split as fixer v4):

| part | v5 | v6 | change |
| --- | ---: | ---: | ---: |
| Main text (frontmatter to the end of "Where I am not sure", change log excluded) | 11,957 | 12,969 | +1,012 |
| Change log | 2,250 | 2,571 | +321 |
| Appendix A | 555 | 555 | 0 |
| Total | 14,762 | 16,095 | +1,333 |

## Per finding

Line numbers are of STUDY.md as handed back (1,151 lines).

```
1 (A, row 1) DELTA §5.3 confirm cap dropped in the v5 consolidation — RESOLVED
  changed: STUDY 688-690 new "Cap" bullet after "Lists": "(DELTA §5.3; order amended by [DK6]): at most 12
    confirm cells per confirm wave, taken in median-g order from the ranked lists; Kai picks at K3/K3a; nothing
    advances automatically into GPU time" (median-g order per Kai's decision, not the arbiter's mean-g
    wording); Falsifier 796 "(at most 12 cells go to confirm, Selection rule 'Cap')"
  verified: grep "Cap|at most 12|advances automatically": the change log (v2 l. 55, v6), Selection rule, Falsifier, stub
  propagated: stub Design line   neighbourhood: re-read the v4 → v5 consolidation audit (critical v5): the only
    other dropped items are the four C4 half-lines (row 11), restored below
2 (B, rows 2 + 3) Label threshold T set by Monte Carlo noise; grid condition undisclosed — RESOLVED
  changed: screen_null.py: --seed / --t-only arguments; §18 condition (ii) read only where P(s_int <= T | q)
    >= 0.01; the whole script run at seeds 20260927 and 1-9; T = minimum over the ten; per-seed table of both
    rules printed; conditional rows and the 5M check print follow T (hard-coded 1.3 removed). STUDY Label
    703-714 (one-sentence rule, values, 90 % interval, lost-seed clause); [DK8] block 998-1013 (per-seed table
    for both rules and families, edge-sensitivity sentence, grid-condition sentence, "failures are consistent"
    removed; alternatives 1.3 / 1.5, one T 1.2, Gaussian-only 1.4 / 3.0); [DK8] label line 946-947 "amended
    v6, 2026-09-28"; change-log v5 l. 159 annotated "[T replaced in v6]"
  verified: §18 prints "5M floor rule: 1.3 / 1.2 / 1.3 / 1.3 / 1.2 / 1.2 / 1.3 / 1.3 / 1.3 / 1.3 (range 1.2-1.3);
    v4 rule: 1.3 / 1.0 / 1.1 / 1.1 / 0.9 / 1.2 / 1.2 / 1.1 / 1.1 / 1.2" and "350k floor rule: 1.9 / 1.9 / 1.9 /
    1.8 / 1.9 ... (range 1.8-1.9); v4 rule: 1.5 / 1.3 / 1.2 / 1.1 / 1.4 / 1.2 / 1.3 / 1.4 / 1.4 / 1.4"; "5M label
    threshold T = 1.2 pt ... (Gaussian recovery at T 0.63)"; "350k ... T = 1.8 pt ... (0.65)"; step lines 0.186 /
    0.055 and 0.421 / 0.093 unchanged
  propagated: 1.3 → 1.2 and 1.5 → 1.8 in 5 live sites across 3 files (STUDY Label, [DK8] block, v6 entry; plan.md
    l. 129 and 155-157 tagged "[superseded v6]"; stub Design line). Band rows regenerated (fix 2(d)): Seeds
    565-571 5M band 1.0-1.2 (0.62 / 0.60 / 0.58 → 0.62 / 0.58 / 0.56), 350k band 1.0-1.8 (0.79 / 0.76 / 0.71 →
    0.80 / 0.76 / 0.69); Gaussian extension rows now quoted at sigma inside each band (5M sigma 1.0: 0.77 / 0.87 /
    0.90; 350k sigma 1.0 / 1.5); [DK16] block gain quoted at sigma 1.0 (0.77 -> 0.87). Unaffected because the
    text reads "T" generically: Seeds l. 552-555 band rule, cheap version "against the family's T",
    budget.py l. 48-49 docstring and l. 239 label. Change-log v1-v5 not rewritten
  neighbourhood: every number printed by the old §18 T block was checked against the new output; the other
    fixed constants of the rule (0.1-pt grid, 0.5 recovery, q grid) are unchanged; plan.md fixer v3 / v4 notes
    that quote 1.3 / 1.5 are tagged
3 (B, row 4) [DK16] above-band gain undisclosed — RESOLVED
  changed: Seeds 569-571 above-band rows (350k 0.49 → 0.60 at q 0.33, 0.45 → 0.59 at q 0.5; 5M 0.19 → 0.19, 0.14
    → 0.23; §18 unconditional, and the new "| s_int > T" print agrees); [DK16] ALTERNATIVES "extend above T at
    350k (the '+ extension, 350k only' Budget row: 326 runs, 1,188.1 / 2,034.9 pod-hours)"
  verified: §18 grid lines q 0.3300 / 0.5000 and the conditional rows at T; budget.py row unchanged
  propagated: stub Design line   neighbourhood: the band rule itself unchanged (disclosure only)
4 (B, row 5, re-scoped by Kai) Median g — RESOLVED as Kai decided: median g primary, mean g the companion
  changed: Ranking 691-702 (median g primary with its reason; mean g with the s_pool interval beside it; LCB80;
    "mean g and n_low are the stability readouts"; Kendall τ median vs mean and a top-12 / top-3 disagreement
    mark for K3a, no threshold); box 207-209, 217-223 (named q 0.1 / 0.33 / 0.5: mean 0.28 / 0.19 / 0.14,
    median 0.85 / 0.26 / 0.26; the hiding caveat); Question 232; Cap order; Falsifier via the Cap; Seeds
    extension selection "by median g" and 8-seed ordering by median g (555, 561); G3 report "median g and
    mean g" (662); Readout "beside median g and mean g" (764); AUC-concordance flag "by median g" (770);
    two-mode table gains median columns (§18b), Gaussian cost sentence; [DK6] label line 944-945 dated v6;
    "Already answered" paragraph; change-log v2 l. 45-48 annotated "[Primary re-decided in v6: median g.]".
    screen_null.py: median-g hits from the existing §18 draws (zero new random numbers) and §18b (mean vs
    median, Gaussian sigma 0.6 / 1.0 / 1.3, per-run q 0.02-0.5 with the s_int <= T subset, seed-shared)
  family test: it does NOT read the ranking statistic (own-sd t of mean d = cell − placebo); its calibration
    and critical values are unchanged, stated at 718-719 and in the v6 entry. No re-simulation needed for it
  §18d (condition (i) under the median): Gaussian recovery at sigma = T is 0.53 (5M) and 0.61 (350k) by median g
    against 0.63 / 0.66 by mean g, so T's condition (i) still holds under the primary, narrowly at 5M; stated in
    the flagged paragraph. The Ranking bullet cites `.claude/memory/decisions.md` 2026-09-28 (Kai's Check line)
  flagged, not changed (numbers simulated with mean g; STUDY 989-995 "Simulated with mean g, flagged for
    re-simulation with median g"): the T rule's conditions (i) and (ii); the [DK16] extension recovery (§16,
    §18); the rank-move null counts (§8, §15; label at 751-752); rank_sim.py's fidelity table (labelled "the two
    companions"). The ranking interval belongs to mean g and stays valid
  verified: §18b 5M Gaussian 0.99 / 0.96, 0.77 / 0.66, 0.57 / 0.46; per-run q 0.02-0.5 mean 0.79 / 0.54 / 0.28 /
    0.11 / 0.19 / 0.14, median 0.99 / 0.96 / 0.85 / 0.56 / 0.26 / 0.26; 350k Gaussian 0.99 / 0.98, 0.89 / 0.84,
    0.79 / 0.73; per-run median 1.00 / 0.99 / 0.95 / 0.81 / 0.61 / 0.53 (script values; constructive v5 and
    Kai's entry quote their own stream, e.g. 0.47 at sigma 1.3, not used)
  propagated: stub Question / Design lines   neighbourhood: every "mean g" in STUDY checked (grep): switched where
    it names the ranking; kept where it is an estimate (survivor mean g, l. 647; seeds-5-8 selection-free
    mean g, l. 559; Appendix A advance gate "mean g >= g0 / 2", significance mode, not the ranking statistic)
  remains / route to: re-simulation of the four flagged design values with median g (experiment-designer), if
    Kai or round 6 wants them; re-deriving T on median recovery reopens the arbiter's rule (a design change)
5 (B, row 6) Family test's detectable effect in pt — RESOLVED
  changed: screen_null.py §15a (printed last to keep the stream; the arbiter's "in §15" would shift §16-§18);
    STUDY Family test power 733-736 (full 50 % / 80 % rows); box 224-226, Question 232-234, Falsifier 790-792 (clause)
  verified: §15a "m = 11: sigma 0.6: 1.65 / 2.40 pt; sigma 1.5: 4.10 / 5.95 pt; sigma 3.14: 8.55 / 12.40 pt";
    "m = 37: 2.50 / 3.55; 6.25 / 8.85; 13.05 / above the 16-pt grid edge" (arbiter: 5.90 and 12.35 at 80 %,
    within 0.05 pt)
  propagated: stub   neighbourhood: §15 power rows (0.214 / 0.077 ...) unchanged
6 (B, row 7) Seed-shared recovery 1.00 restates an assumption — RESOLVED
  changed: box 217-219 "because in that model the cell × seed interaction is the within-mode sd, 0.3 pt, by
    construction"; "measures s_int, ρ̂ and n_low instead of assuming either case"
  verified: §18 seed-shared rows median s_int 0.30 pt at every q (unchanged lines)
  propagated: stub   neighbourhood: the resolution paragraph (613-619) says the same without restating the number
7 (C, rows 8-21) — RESOLVED except row 20's optional part (not adopted, as allowed)
  8 crit C1: 613-616 "set by n, the interaction sd and the shape of the seed distribution; s_int estimates the
    second, the §18 rows bound the third"
  9 crit C2: box names q 0.1 / 0.33 / 0.5 with their sd
  10 crit C3: box 207 and Lists 673-674 "at most 11"
  11 crit C4: (a) 520-521 cell-side losses only; (b) 297 GPU-product rule [D17]; (c) 382 M049 at 5M runs;
    (d) 770 "by median g" (the critic asked "by mean g"; Kai's decision makes the primary median g)
  12 crit C5: stub header rewritten (no "350k feasibility"); INDEX.md / index-head.md are the orchestrator's
    `tools/index.py build`
  13 crit C6 / cons C3: v5 l. 627, 671, 678 reflowed; two long lines from this pass reflowed
  14 phys C1: 608-611 rare-high not simulated; physics v5 C1's T 1.4 / 1.4 cited, not re-run
  15 phys C2: 706-707 s_int printed with its 90 % chi-square interval; no "near threshold" label
  16 phys C3: 256-257 confirm restates the metric in macro AUC or working-point efficiency
  17 phys C4: figures row, per-cell EBOPs column beside g
  18 phys C5: M001 labelled with the others (658); Question's special-case sentence removed
  19 cons C1: 677-679 Welch SE sentence (equal at ρ = 0, √2 at ρ = 0.5, not wider at n = 4 unless ρ > 0)
  20 cons C2: 480-482 false flag 0.071 and power 0.067-0.801 from §18c (arbiter's 0.067 was constructive's
    stream); n_low against a fixed threshold not adopted (optional; scope freeze)
  21 cons C4: 704-705 s_int on the family's n_p seeds, a lost replica seed drops that column
```

Kai (b), the round-6 freeze: recorded in the v6 change-log entry (l. 197-199) and in "Where I am not
sure" (l. 983-987), citing the 2026-09-28 entry; not a new [DK].

Note for reviewers: `review/arbiter_v5_tstab_gen.py` asserts the literal `default_rng(20260927)` and the
v4 condition-(ii) string; both are gone from `screen_null.py` v5 (now `--seed` and the floor rule), so
the generator no longer applies. The ten-seed table it produced is now built into §18
(`python3 screen_null.py` runs the nine other seeds as child processes). The [DK8] block's
"set of 200 passes 350k 1.9" is cited to `review/arbiter_v5_tstab.txt` l. 120, since 1.9 passes at
the design seed and §18 prints no line for it.

## CANNOT RESOLVE

None. One routed item (not a blocker): re-simulating the T rule, the [DK16] extension recovery,
the rank-move null counts and `rank_sim.py` with median g → experiment-designer, if Kai or the
round-6 arbiter asks for it. No Nautilus job and no `mulder` run is involved.

## Record or outward copies for Kai

None. No number of this screen is in the record or outward. `INDEX.md` and
`.claude/memory/index-head.md` still carry the old question line; `python3 tools/index.py build`
is the orchestrator's step. The experiment-log stub (`.claude/memory/experiment-log.md` l. 11-16)
was rewritten in place.
