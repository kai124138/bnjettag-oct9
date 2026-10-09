# STUDY critical review v5: 2026-09-27-delta-screen (Delta wave 2)

Critical reviewer, fresh context, 2026-09-27. Panel mode, re-review, iteration n = 5 (§6.5 strong
warning). Artifact: `STUDY.md` at commit 094db11 (working tree identical; 1,067 lines, 14,762
words), with `plan.md`, `budget.py` v5, `screen_null.py` (§1-§9, §11-§13, §15-§18), `rank_sim.py`,
`research/screen-design-literature.md`. Inputs read: `review/STUDY_validators_v5.txt`,
`review/STUDY_arbiter_v4.md`, `review/STUDY_fixer_v4.md`, the v4 STUDY (`git show
0b11518:…/STUDY.md`, 1,681 lines, read in full for the consolidation audit), `.claude/memory/decisions.md`
top entries, the experiment-log stub, `delta.json` `prerequisite_jobs`, DELTA.md §5.3 "Cap". No
verdict (panel mode).

## Validator lines, verbatim

`STUDY_validators_v5.txt`:

```
No mechanical STUDY validator exists; prose_lint on STUDY.md:
Desktop/bnjettag/campaigns/2026-09-27-delta-screen/STUDY.md  —  score 0, reads human
  14762 words · 403 sentences · mean 24 words (σ=16.8) · 14% bullets · 1 em-dashes
```

No line is A-marked. No plot-validator file (the STUDY has no figures).

## Recomputed (design arithmetic, not results)

- `uv run --with numpy,scipy python screen_null.py` (seed 20260927, 26 s). §1-§17 match an earlier
  v3 output digit for digit, except the two reworded §3 labels and the removed §10 / §14 prints.
  STUDY values checked against my run: §13 4.284 / 6.585 / 6.733 / 12.290 (l. 667, 487); §15
  calibration 0.103 / 0.101, 0.099-0.108, two-mode 0.036-0.082, offset 0.099-0.102, placebo
  0.099 / 0.097, n = 3 two-mode 0.063-0.232 (l. 671-676); power 0.214 / 0.087 / 0.051 / 0.026
  and 0.077 / 0.030 / 0.016 / 0.007 (l. 676-678); multiplier 2.168 / 2.136 → 2.17 / 2.14
  (l. 648); ρ̂ null ±0.34 / ±0.18, unpaired 2.880 / 3.590 (l. 716-718); rank-move T and null
  counts (l. 696-699); §16 (l. 532-534); §17 (l. 613-615). All match.
- §18 checked against the STUDY: two-mode table l. 564-570 (5M 0.79 / 0.55 / 0.28 / 0.19 / 0.14;
  350k 0.92 / 0.81 / 0.66 / 0.49 / 0.45; seed-shared 1.00; per-run sd 0.81-2.72); [DK16] in-band
  rows l. 534-536 (5M 0.61 / 0.58 / 0.51 → 0.61 / 0.56 / 0.49; 350k 0.80 / 0.79 / 0.77 → 0.80 /
  0.78 / 0.74); T = 1.3 pt (5M) and 1.5 pt (350k). All match.
- `python3 budget.py`: (4, 4) 302 runs, 176,000 run-epochs, 1,112.2 / 1,959.0 pod-hours, 318
  certifications; extension 390 / 366 / 326; packable today 240, 142,000, 897.4 / 1,592.5;
  cheap version 129, 79,500, 502.4 / 853.1, 2.8 / 4.5 d; [DK18] 84 runs, 366.5 pod-hours. Matches
  the Budget table (l. 784-796) and [DK18] (l. 951-955). The diff against the v4 output is the
  three band labels and the removed pause rows.
- `uv run --with numpy python rank_sim.py`, m = 37 block: 0.99 / 0.97, 0.47 / 0.40, 0.16 / 0.14,
  0.74 / 0.66, 0.26 / 0.22, 0.94 / 0.90 (mean / LCB80). Matches the fidelity table l. 555-559.
- Appendix A thresholds: 0.3 / (k_joint · √2) gives 0.058 / 0.102 / 0.134 and 0.044 / 0.085 /
  0.116 pt; g_res(8) = 1.58 · √2 · 0.6 = 1.34 pt. Match l. 1044-1050.
- Counts: the cells table (l. 298-314) gives 40 G3 cells at 5M (4+1+2+5+5+1+11+3+4+1+1+2). Less 3
  long-horizon and 2 Welch that is 35; plus 4 baselines, 44 in all. At 350k it gives 7 FF + 12 on A
  + 3 probes + M050 = 23. Matches l. 326-330 and `budget.py`.
- **Threshold sensitivity** (scratch copy only:
  `/private/tmp/claude-501/-Users-kaiyamaguchi-Desktop-bnjettag/f3113eb2-31b2-4d10-9d44-a725a8196f9e/scratchpad/sn_sens.py`,
  `screen_null.py` with one loop added after §18's `T18[fam] = max(ok)`. The loop draws nothing,
  so every earlier value is unchanged). It re-applies the rule and fails a q only if its
  conditional set has at least MINSET draws. MINSET = 1 is the STUDY's rule and reproduces its
  output. Results:
  - 5M: largest passing T is 1.3 at MINSET 1 / 30 / 100 / 300. At MINSET 1, 0.8 and 0.9 fail and
    1.0-1.3 pass.
  - 350k: largest passing T is **1.5 / 1.7 / 1.9 / 1.9**. At MINSET 1, 1.2 fails and 1.3-1.5 pass.

## Findings

### Category A

**A1. The DELTA §5.3 confirm cap was dropped in the consolidation. The arbiter did not list it
for deletion, and the change log still says it is restored.**
- Where: v4 l. 971-972, Selection rule: "**Cap** (restored from DELTA §5.3): at most 12 confirm
  cells per confirm wave; Kai picks from the ranked lists at K3/K3a. Nothing advances
  automatically into GPU time."
- v5: `grep -n -i "cap\b|12 confirm|advances automatically"` finds only two lines, both in the
  change log:
  - l. 55, the v2 entry: "Restored from DELTA verbatim (missing in v1): … the 12-cell confirm cap
    (§5.3)";
  - l. 45, the [DK6] amendment: "§5.3 ranking statistic and **cap order**".
- DELTA.md l. 858 still carries the cap ("At most 12 confirm cells per confirm wave, ranked by the
  lower 80 % bound of g").
- Precedent: the same absence was part of arbiter v1 #4, rated A ("12-cell cap … carry the same
  category because they are the same defect").
- Scope: the rule is not on arbiter v4's deletion list (arbiter v4 l. 224-244). The fixer's
  report says "Consolidation, no rule changed beyond the above" (STUDY l. 176).
- Impact:
  - A pre-registered rule restored from DELTA is gone.
  - The change log (l. 53-55) now makes a false claim about the body.
  - [DK6]'s dated amendment of the cap's ordering (LCB80 → mean g) now amends a rule the STUDY no
    longer states.
  - K3a has no stated cap: the Falsifier (l. 735-737) sends the lists to Kai with no bound on how
    many cells may go to confirm.
- Fix (three lines, no new machinery): restore one bullet after "Lists" in the Selection rule:
  "**Cap** (DELTA §5.3; order amended by [DK6]): at most 12 confirm cells per confirm wave, taken
  in mean-g order from the ranked lists, Kai picks at K3/K3a; nothing advances automatically into
  GPU time."
- Neighbourhood: the rest of the v4 → v5 sweep found no other dropped decision rule (list under
  "Consolidation audit").

### Category B

**B1. The label threshold T comes out non-monotone, and at 350k it is set by Monte Carlo sets of
1-8 draws. The STUDY hides this with "the failures are consistent".**
- Where: [DK8] DECISION block l. 926-933; Selection rule "Label" l. 656-661; `screen_null.py`
  §18 `T18[fam] = max(ok)`.
- The fixer applied the arbiter's rule literally and correctly, so 1.3 / 1.5 pt are the rule's
  outputs. My run of §18 shows three things the STUDY does not say.
  - (a) **The set of passing T values is not an interval.**
    - 5M: T 0.8 fails (worst q 0.1003, a set of **1** draw of 20,000, recovery 0.00) and T 0.9
      fails (set of 5, 0.40). T 1.0-1.3 pass.
    - 350k: T 1.2 fails (q 0.2643, set of **3**, 0.33). T 1.3-1.5 pass, and T 1.6 fails (q 0.3893,
      set of **1**, 0.00).
    - `max(ok)` skips the gaps without saying so.
  - (b) **350k T = 1.5 passes at q 0.33 on one draw.** §18 prints: "q 0.33: P(s_int <= T) 0.00;
    recovery | s_int <= T 1.00 (set 1)". Had that one draw missed, 1.5 would fail too.
  - (c) **Sensitivity** (Recomputed, above). If a q may fail T only on a conditional set of at
    least 30 / 100 draws, the 350k threshold becomes 1.7 / 1.9 pt. The 5M value stays 1.3 pt under
    every convention. So 5M's T is robust. 350k's T depends on a minimum-set convention the rule
    does not state.
- The rationalization: l. 929-930 says "1.6-1.9 fail … on sets of 1-8 draws …; 2.0-3.0 fail on
  sets of 34-18,795 draws …, so the failures are consistent". That is true only for failures
  above T. The failures below T (5M 0.8 / 0.9; 350k 1.2), on sets of the same size, point the other
  way and are not mentioned.
- The fixer's report records "No minimum set size was added", which is honest. The STUDY is what
  Kai reads, and it does not say so.
- Impact: label only; nothing that runs changes. But the label is the wave's main readout
  ("ranked" / "descriptive"). At 350k, a family whose s_int falls between 1.5 and 1.9 pt gets a
  label that one Monte Carlo draw decides.
- Fix, either way (the choice is Kai's; the design is not the fixer's):
  - (i) keep the literal rule, and state in [DK8] the non-monotone pass set, the one-draw pass at
    q 0.33, and the 1.5 / 1.7 / 1.9 sensitivity;
  - (ii) fix a minimum conditional set size, or fail a q only when the upper 95 % bound of its
    conditional recovery is below 0.5.
  - In both cases print the sensitivity from §18, so the number comes from the script and not from
    this review.

**B2. The arbiter's grid-fineness condition is not met, and the STUDY does not say so, although
the fixer's report says it does.**
- Arbiter v4 fix 2: "The q grid must be fine enough that consecutive median s_int values differ by
  at most 0.1 pt."
- §18 prints "largest step … 0.186 pt overall; 0.055 pt where the medians are >= 1.0 pt" (5M), and
  0.421 / 0.093 pt (350k). The condition therefore fails overall and holds only above 1.0 pt.
- The fixer's report ("remains / route to", point (a)) says both points go to Kai "in the [DK8]
  and [DK16] rows". The [DK8] row (l. 926-933) carries point (b) only. The [DK16] row (l. 935-941)
  carries neither.
- Impact: a condition the arbiter set is unmet, and the artifact Kai reads does not record it.
  Checked: in both families the jump region lies below 1.0 pt, so it does not decide T (T ≥ 1.3).
  The substance is small; the problem is the missing disclosure.
- Fix: one sentence in the [DK8] block: the condition holds above 1.0 pt (0.055 / 0.093 pt) and
  cannot hold below it (m × 4 low-mode count jumps, 0.186 / 0.421 pt), and no T candidate lies in
  the jump region.

**B3. The [DK16] block reports where the extension gains nothing but not where §18 shows it
gains.**
- Where: Seeds l. 521-536; [DK16] DECISION l. 935-941.
- The rule extends only for 1.0 ≤ s_int ≤ T and never above T. That design came from arbiter v4
  fix 1(d), which cited the constructive script's 5M value "0.16 → 0.20 at 3.14 pt".
- §18, run after that decision, shows:
  - **within the band, under per-run two-mode seeds, the extension adds nothing** (disclosed,
    l. 534-536);
  - **above the band at 350k it adds 0.10-0.14**: unconditional recovery 0.49 → 0.60 at q 0.33
    and 0.45 → 0.59 at q 0.5, where nearly every draw has s_int > T (P(s_int ≤ 1.5) = 0.00).
  - At 5M the above-band gain is 0.19 → 0.19 and 0.14 → 0.23.
- Impact: Kai is asked to buy +88 runs (1,390.3 vs 1,112.2 pod-hours at r = 1) with Gaussian
  gains (0.57 → 0.69) and a two-mode "nil". He is not told that under the only measured seed
  structure the gain sits in the region the rule excludes, at 350k. That is the "thing we are
  quietly not saying" for this default.
- Fix: add the above-band two-mode rows to the [DK16] block, and name "extend above T at 350k" as
  an alternative with its cost (the 350k-only extension row: +24 runs, 1,188.1 / 2,034.9
  pod-hours). The decision stays Kai's; this is disclosure, not a design change.

### Category C

- **C1.** l. 573-577 says "The ranking's resolution is set by n and the cell × seed interaction
  sd … not by σ." But the sentence before it (l. 572-573) shows two-mode seeds costing recovery at
  a matched sd (0.79 vs 0.92 at 0.8 pt). s_int ≈ the per-run sd in the per-run rows, so the same
  s_int gives different recovery. Reword to "set by n, the interaction sd and the shape of the
  seed distribution; s_int estimates the second, the §18 rows bound the third".
- **C2.** Box l. 195-196 gives "0.14-0.28" for per-run sd 1.65-2.72 pt. That is the three named q.
  The §18 grid over the same sd range goes down to 0.10 (q 0.4444, sd 2.70) and up to 0.29. Say
  "0.10-0.29 over the §18 grid", or name the q values.
- **C3.** l. 185 and 632 say "11" for the 350k ranked list, but five of those cells (M016, M040,
  M042, M043, M045) are paired-if-hash and leave for the Welch list if their check fails. Write
  "at most 11", to match "at most 35".
- **C4.** The consolidation lost some half-lines that carried a rule or a scope. None changes a
  decision; restore or accept:
  - (a) v4 l. 642-643: "The incomplete-pairs list and the survivorship label apply to cell-side
    losses only". v5 l. 483-489 no longer says so.
  - (b) v4 l. 272-273: the placebo follows "the same GPU-product rule as cells, [D17]". v5 l. 268
    says only "packed like a cell". The rule survives in [D17] l. 879, and the two placebo readings
    (l. 683-687) depend on it.
  - (c) v4 l. 434: "M049 at 5M is not covered and runs" (X3). v5 l. 352-353 drops it.
  - (d) v4 l. 1018-1020: the AUC-concordance flag used "top 12 … by mean g in accuracy … by mean g
    in validation macro AUC". v5 l. 711 says "top 12 by accuracy". That is ambiguous between raw
    accuracy and the gap. Restore "by mean g".
- **C5.** The experiment-log stub header (`experiment-log.md` l. 11) still asks "…validation
  accuracy **or 350k feasibility** against its base arm…". That is the pre-v5 question; the
  Question and Design lines below it are updated. `INDEX.md` / `index-head.md` also carry the old
  line (the fixer flagged this for the orchestrator's `tools/index.py build`).
- **C6.** Stray four-space indentation at l. 627, 671 and 678, inside list items. Cosmetic; check
  that it renders.

## Earlier findings, by name (arbiter v4 fix list 1-7, findings #1-#8)

| v4 item | status | evidence |
| --- | --- | --- |
| fix 1 / #1 labels on s_int | **resolved** | s_int defined l. 652-655 (df (m − 1)(n − 1), 30 / 108), side-by-side print l. 655-656, label rule l. 656-658, "descriptive: recovery below 0.5 at this spread" l. 657, caveat once l. 661-663; sd_rep one role l. 443-446, [D7] l. 870-871 |
| fix 1(d) / #7 [DK16] band on s_int, test in every family | **resolved** (residual B3) | l. 521-525; family test "read in every family, whatever the label" l. 663, Falsifier l. 732 |
| fix 1(e) / #5 Falsifier and K3a | **resolved** | l. 735-737: "In every family the list goes to Kai at K3a … A 'descriptive' list supports nomination with its label, never a resolved gap" |
| fix 1(f) resolution sentence | **resolved** (wording C1) | l. 573-577 |
| fix 2 / #2 two-mode rows and T | **resolved as specified; residuals B1, B2** | §18 present and reproduced; Gaussian rows labelled "optimistic under per-run two-mode seeds" l. 532, 553; two-mode table l. 561-570; T 1.3 / 1.5 l. 658 |
| fix 3 / #3 floor-family question | **resolved** | frontmatter l. 6; Question l. 211-215; G2 l. 612-620 "rescue expected from floor arithmetic", M001 "borderline" l. 215, 617; "necessary, not sufficient" l. 618-619; "structural, by construction" survives only in change log l. 122, 163-164 |
| fix 4 / #4 ranked-list membership | **resolved** (C3) | l. 185, 328-330, 631-644 "at most 35 paired cells"; M006, M009, M046-if-[A17]-fails in the Welch list l. 636-637; "design grid m = 37" labels l. 551, 641, 649, 671, 699; no "at most 37" left (grep) |
| fix 5 / #6 per-cell constraint label | **resolved** | l. 463-467 (M003, M007, M008, M011, M012, own seeds, ⌈3k/4⌉); 0.8 / 0.9 rationale l. 460-463 (0.2 × 5,000,000 = 1,000,000 checks); β tolerance l. 459; readout l. 708 |
| fix 6 / #8 mode readout | **resolved** | l. 447-451; n_low l. 705-706; no decision reads it |
| fix 7 C items | **resolved** | phys C1 l. 713-716; phys C2 l. 755; phys C3 / crit C3 l. 740; phys C5 / crit C2 l. 643-644, 525; crit C4 n_p / n_d l. 485-486, 603, 665; crit C5 l. 914; cons C1 l. 6; cons C2 Appendix A l. 1029-; cons C4 l. 1013-1016. Packable-today m: 35 − 3 = 32, 11 − 2 = 9 |
| [D] / [DK] amendments | **resolved** | [D7], [D8] "amended v5, 2026-09-27" l. 870-874; [DK8] l. 884-885; [DK17] "withdrawn in v5" l. 888; change log v5 l. 146-178 |

**Arbiter v4 deletion list, item by item.** Box pause: deleted. Question "if the family passes":
deleted (l. 206-209). Seeds "likely branch" / "on a pause" / guard wording: deleted. Falsifier
(v): deleted, old (vi) is (v) (l. 756-757). [DK17] bullet and block: deleted, one-line "withdrawn"
(l. 888). The four options: deleted. The three budget rows and the Counts "254": deleted
(l. 784-796, 326-330). `budget.py` pause code: deleted (diff above). The false-pause sentence and
§10 / §14 citations: deleted (grep "§10|§14": change log only, plus "DELTA §10" l. 728, which is
DELTA's section). The no-family-test line: deleted. "(4, 4) the branch taken only if": deleted,
now "(4, 4), the design" (l. 786). `plan.md` l. 114, 122: tagged "[superseded v5 …]". **Kept, as
instructed:** the A07 memory pause (l. 400-402) and base stability (l. 470-473).

**Consolidation audit (were other rules deleted?).** I read v4 l. 143-1681 against v5 section by
section. Every pre-registered rule is present, restated or moved (Appendix A, [D17], Falsifier),
with these exceptions:
- A1, the confirm cap: dropped.
- C4 (a)-(d): scope half-lines dropped.
- Specification detail that `delta.json` holds: the teacher's "PID target 1e12, β bounds at min"
  is in `prerequisite_jobs.P-T1.what`.
- Rationale sentences that decide nothing: G1's "0.25 stays because (c) is 0.211"; G3′'s one-sided
  power; [DK13]'s "cross-regime" consequence; the per-architecture canary list.

## Regression triggers (§6.7)

None new.
- Selection on held-out: no, validation only (l. 579, 720).
- Cross-N as one series: M009 moved to the Welch list (fix 4).
- [D] replaced without a dated amendment: no. [D7], [D8] and [DK8] are dated v5, and [DK17] is
  withdrawn in the change log.
- Nothing has run, so the result-based triggers do not apply.

A1 is a dropped DELTA rule, not a changed [D] label. No investigator is needed.

## Adversarial checks

- **"The failures are consistent"** (l. 930): not accepted, see B1.
- **"Cost: none"** for [DK8]: correct. T changes only labels, and `budget.py` confirms that
  nothing that runs depends on it.
- **Re-keying the gate** (the arbiter v4 motivated-reasoning check): still holds.
  - The pause saved 48 of 302 runs (v4 `budget.py` 254).
  - T was not loosened at 5M (1.3, unchanged).
  - At 350k it is 1.5 against the Gaussian 3.0, so it was tightened, though B1 shows the 1.5 is
    fragile upward, not downward.
- **Circular selection:** none. T comes from simulation only. The extension is selected on seeds
  1-4, and its seeds-5-8 mean is the selection-free estimate (l. 527-528).
- **Tautological validation:** none new. The placebo stays the family-test reference in every
  case (l. 664).

## Competing-group question

A group publishing the same screen next month would have two things this STUDY lacks:
- a stated confirm cap at K3a (A1);
- a "ranked" / "descriptive" threshold that does not move with an unstated Monte Carlo
  minimum-set convention (B1, 350k).

Both are text or a short script change, with no GPU cost and no justification for being absent.

## Disputed facts for the investigator

None. Every item was settled from the artifact, the v4 file, DELTA.md, `delta.json` and my runs of
`screen_null.py`, `budget.py`, `rank_sim.py` and the scratch sensitivity copy.
