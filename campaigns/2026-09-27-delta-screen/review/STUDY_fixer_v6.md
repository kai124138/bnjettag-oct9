# STUDY fixer v6: 2026-09-27-delta-screen (iteration 7)

Fixer, fresh context, 2026-09-28. Input: `review/STUDY_arbiter_v6.md` (ITERATE, 1 A; B1-B6 and
K1-K7 pre-specified). Scope from the orchestrator: A1-A7, B1-B6, K1-K7 verbatim, nothing else.
STUDY.md line numbers below are the edited file's. Every A line carries "(amended v7, 2026-09-28,
`decisions.md` 2026-09-28 'Delta must not launch on the leaking anchor bundles')".

## Scripts (numbers come from them)

- `screen_null.py`: §19e appended at the end (design-seed T by the unchanged rule at floor 0.005 /
  0.01 / 0.02 / 0.05, from the stored §15 / §18 recovery; zero new random numbers; asserts that
  floor 0.01 equals the rule's design-seed T). Full run `uv run --with numpy,scipy python
  screen_null.py` (1 min 36 s wall): lines 1-461 byte-identical to
  `review/constructive_v6_screen_null_out.txt` (`diff` empty); new lines 462-464 print 350k median g
  2.0 / 2.1 / 2.2 / 2.3 pt (mean g 1.9 / 1.9 / 1.9 / 2.0), 5M 1.2 throughout (mean g 1.3). Output kept
  in `review/fixer_v6_screen_null_out.txt`.
- `budget.py`: one PACK-MEM line printed last (baseline 2.1 GB, anchor incident §5 l. 138; 5 MB per
  epoch; 6 Gi = 6.44 GB): 4.6 / 7.1 / 12.1 GB at H 500 / 1,000 / 2,000. `diff` against the
  pre-edit output: only that line added.
- `review/physics_v6_rarehigh.py` re-run (B6 source): 350k T 2.1, median / mean g given s_int ≤ T
  0.61 / 0.39 (q 0.67), 0.87 / 0.46 (0.8), 0.98 / 0.55 (0.9); 5M empty for q ≤ 0.8, 1.00 at q ≥ 0.9.
  Matches the arbiter.

## A fixes

| # | status | where |
| --- | --- | --- |
| A1 `code_sha` | RESOLVED | frontmatter l. 9, arbiter text; rest of the field kept. YAML parses (10 keys) |
| A2 gate 11 | RESOLVED | l. 462-466 |
| A3 gate 14 + gate 7 note | RESOLVED | gate 14 l. 471-476 (after gate 13); gate 7 "(GPU memory; host memory is gate 14 …)" l. 441-443 |
| A4 gate 4 | RESOLVED | l. 431-434 |
| A5 PACK + Budget | RESOLVED | PACK l. 921-927 (values from `budget.py` PACK-MEM); wall-clock sentence l. 887-889 |
| A6 Reference row | RESOLVED | l. 277, anchor `RUN.md` l. 480 "## Stopped 2026-09-28T05:31Z" confirmed |
| A7 change log v7 + stub | RESOLVED | change log l. 207-211 (arbiter text plus one clause naming the two added prints, since `budget.py` is no longer untouched); experiment-log stub rewritten in place: header "arbiters v1-v6 (fixers v1-v6)", Design line names gate 14 and the non-launchable bundles, and "budget.py v5" → "v6" (1 instance; no version pin in STUDY.md) |

## B corrections (arbiter wording)

| # | status | where; phrase sites |
| --- | --- | --- |
| B1 Label | RESOLVED | l. 748-753. "recovery below 0.5": 1 site in STUDY (changed), 0 in `plan.md`, 0 in the stub |
| B2 [DK8] | RESOLVED | l. 1087-1090 (added "`screen_null.py` §19e" as the script source beside critical v6 own check 1); ALTERNATIVES l. 1094-1095. "absorbs it": 1 site (changed) |
| B3 interval | RESOLVED | G3 report l. 698-699; Ranking l. 729-731 (the phrase "median g and mean g" is not in the Ranking bullet, so the clause follows "the median of the cell's n_p paired g_s"); figures row l. 967 |
| B4 rank-move | RESOLVED | fallback l. 801; [L6] l. 1022-1024. "companion disagrees at the null level": STUDY 1 site (changed), stub 1 (changed), `plan.md` l. 229 historical record (tagged "[superseded v7]", not rewritten) |
| B5 relaunch | RESOLVED | Confounds item 12 l. 570-571; Readout l. 812-813; placebo reading l. 789 |
| B6 rare high mode | RESOLVED | l. 639-647. "not simulated": 1 site (changed) |

## Known limitations at freeze

K1-K7 inserted verbatim as `## Known limitations at freeze`, l. 1033-1059, after [L8] and before
"Where I am not sure". RESOLVED.

## Not applied, on purpose

- C rows 10-20 (orchestrator scope A/B/K only; the arbiter marks them "before commit"). Pre-existing
  lines > 150 characters remain at l. 707, 729 (C row 14); no new one added.

## For the orchestrator / solo check

- `prose_lint` on STUDY.md: score 6 (was 0), all from "robust" ×3 in K2 (l. 1042, 1044), the arbiter's
  verbatim text. Rewording would break "verbatim"; left for the orchestrator.
- The anchor tarball now hashes **ceb174db** (`decisions.md` 2026-09-28 ml-engineer entry: patches
  0030-0031, "staged, not applied", leak "not reproduced on CPU", "Delta must rebase onto ceb174db").
  A1's "not yet frozen" was written against f2107a04; ceb174db is a staged candidate that has not
  passed gate 14, so the sentence is not false, but the STUDY does not name it. Not edited (outside
  the arbiter's text). The same entry keeps 6 GiB per arm (2.16 GB + 5 MB × 500), which agrees with
  A5 at H 500 only; at H 1,000 / 2,000 (rep-C, M032) A5's 7.1 / 12.1 GB applies.
- Nothing CANNOT RESOLVE. Nothing launched, no other campaign edited, nothing committed.
