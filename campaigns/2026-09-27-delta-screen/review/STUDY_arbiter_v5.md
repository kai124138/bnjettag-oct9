# STUDY arbiter v5: 2026-09-27-delta-screen (Delta wave 2)

Arbiter, fresh context, 2026-09-27. Re-review, iteration n = 5.
Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (1,067 lines, 14,762 words, commit 094db11,
after fixer v4), with `plan.md`, `budget.py` v5, `screen_null.py` (§1-§9, §11-§13, §15-§18),
`rank_sim.py`. Inputs read: `review/STUDY_physics_v5.md`, `review/STUDY_critical_v5.md`,
`review/STUDY_constructive_v5.md` (+ `constructive_v5_*.py`), `review/STUDY_validators_v5.txt`,
`review/STUDY_arbiter_v4.md`, `review/STUDY_fixer_v4.md`, `docs/methodology/06-review.md` §6.1-§6.8,
`.claude/memory/decisions.md` top entries, the v4 STUDY (`git show 0b11518:…/STUDY.md`, l. 960-975),
`campaigns/2026-09-26-delta/DELTA.md` (cap lines), the experiment-log stub. No plot-validator file
(STUDY has no figures).

**§6.5 STRONG WARNING, iteration 5.** This is the fifth panel iteration of this STUDY, the tier at
which §6.5 warns strongly; the fixer's pass produces iteration 6, and the cap (ESCALATE) is 10.
Since v2 every round's added machinery has produced the next round's B items; this round's
largest item (B1) is a defect in the v4 arbiter's own threshold rule. The fix list below is sized
to close in one pass and **adds no gate and no branch** (see the line under the fix list). If
iteration 6 raises new B items that trace to rules added here, the next arbiter should weigh
ESCALATE to Kai with the choice "freeze the design as is and launch with the residuals disclosed"
rather than a seventh loop.

## Validator lines

`STUDY_validators_v5.txt`: no mechanical STUDY validator exists; `prose_lint` on STUDY.md scores 0,
"reads human" (14,762 words, 1 em-dash). No A-marked line. No plot-validator file at STUDY.

## Independent checks (arbiter)

All seeded design arithmetic, run on the laptop in CPU seconds, not results, not quotable.
Evidence kept in `review/`: `arbiter_v5_tstab_gen.py` (variant generator), `arbiter_v5_tstab.txt` (per-seed T and the §18 lines quoted below), `arbiter_v5_power.py` (physics B2 check).

- **`screen_null.py` at the design seed** (`arbiter_v5_tstab.txt`, run `sn_m1_s20260927`: the unchanged script except a
  filter parameter set to its original value 1). §18 reproduces the STUDY: T = 1.3 pt (5M), 1.5 pt
  (350k); two-mode per-run recovery 0.79 / 0.55 / 0.28 / 0.19 / 0.14 (5M) and 0.92 / 0.81 / 0.66 /
  0.49 / 0.45 (350k); seed-shared 1.00 with median s_int 0.30 pt at every q; largest median-s_int
  step 0.186 / 0.055 pt (5M) and 0.421 / 0.093 pt (350k). The T failure lines are exactly those
  the physics and critical reviewers quote: 5M T 0.8 fails on a set of 1 draw, 0.9 on 5, 1.4 on 201;
  350k T 1.2 fails on 3, 1.6-1.9 on 1 / 3 / 1 / 8; 350k T = 1.5 passes at q 0.33 on a set of 1.
- **Threshold stability, 20 runs** (`arbiter_v5_tstab.txt`; variants from `arbiter_v5_tstab_gen.py`:
  `screen_null.py` with only the RNG seed and the minimum conditional-set size changed):

  | rule | 5M T at seeds 20260927 / 1-9 | range | 350k T at seeds 20260927 / 1-9 | range |
  | --- | --- | --- | --- | --- |
  | as written (set ≥ 1 draw) | 1.3 / 1.0 1.1 1.1 0.9 1.2 1.2 1.1 1.1 1.2 | 0.9-1.3 | 1.5 / 1.3 1.2 1.1 1.4 1.2 1.3 1.4 1.4 1.4 | 1.1-1.5 |
  | set ≥ 200 of 20,000 (P ≥ 0.01) | 1.3 / 1.2 1.3 1.3 1.2 1.2 1.3 1.3 1.3 1.3 | 1.2-1.3 | 1.9 / 1.9 1.9 1.8 1.9 1.9 1.9 1.9 1.9 1.9 | 1.8-1.9 |

  The design seed gives the largest T of ten under the written rule in both families. With the
  probability floor, the minimum over the ten seeds is **1.2 pt (5M) and 1.8 pt (350k)**; the
  minimum over the constructive reviewer's six seeds is the same. The floor alone is edge-sensitive
  at the design seed: 5M T 1.4 fails on a set of exactly 201, and 350k T 1.9 passes at q 0.33 on a
  set of exactly 200 (`arbiter_v5_tstab.txt`, run `sn_m200_s20260927`). The seed minimum absorbs that. Above T the
  failures are real: at 350k T ≥ 2.0 fails on sets of 34-18,795 draws at recovery 0.26-0.44
  (design seed, written rule); Gaussian recovery at 1.8 pt is 0.65.
- **[DK16] above the band** (design seed, per-run grid, unconditional recovery → extension): 350k
  q 0.33 0.49 → 0.60, q 0.5 0.45 → 0.59 (median s_int 2.56 / 2.72, above either T); 5M q 0.33
  0.19 → 0.19, q 0.5 0.14 → 0.23. Critical B3's numbers reproduce.
- **Median-of-4 g** (`review/constructive_v5_robust.py`, re-run, 10 s): 5M mean / median recovery
  Gaussian σ 0.6 / 1.0 / 1.3: 0.99 / 0.96, 0.77 / 0.66, 0.57 / 0.47; per-run q 0.02 / 0.05 / 0.1 /
  0.2 / 0.33 / 0.5: 0.78 / 0.99, 0.54 / 0.96, 0.29 / 0.85, 0.11 / 0.56, 0.19 / 0.27, 0.14 / 0.26;
  seed-shared 1.00 / 1.00. 350k: 0.99 / 0.98, 0.89 / 0.84, 0.80 / 0.74; per-run 0.92 / 1.00, 0.81 /
  0.99, 0.66 / 0.95, 0.49 / 0.81, 0.48 / 0.60, 0.45 / 0.54. Mode flag: false flag 0.067, power 0.070
  / 0.102 / 0.217 / 0.506 / 0.799 / 0.931 at q 0.02-0.5. Welch n 4 / 4 half-width 1.04 / 2.60 /
  5.43 pt against paired (ρ 0) 1.35 / 3.38 / 7.07 at σ 0.6 / 1.5 / 3.14. All match constructive v5.
- **Physics B2, effect at 50 % / 80 % power for one named cell** (`arbiter_v5_power.py`, own-sd t on d = cell −
  placebo, n 4, §13 critical values 4.284 / 6.585): m 11: 1.65 / 2.40 pt (σ 0.6), 4.10 / 5.90 pt
  (σ 1.5), 8.55 / 12.35 pt (σ 3.14); m 37: 2.50 / 3.55 pt (σ 0.6), 6.25 / 8.85 pt (σ 1.5); at σ 3.14
  and m 37 the 80 % point is above the 16-pt grid edge. Matches physics v5 within 0.05 pt.
- **`budget.py`**: (4, 4) 302 runs, 176,000 run-epochs (42,000 E / 134,000 A07), 318
  certifications; extension both / 5M only / 350k only 390 / 366 / 326 runs; packable today 240,
  142,000; cheap 129, 79,500. **`rank_sim.py`** m = 37 block: 0.99 / 0.97, 0.47 / 0.40, 0.16 / 0.14,
  0.73 / 0.65, 0.26 / 0.22, 0.74 / 0.66, 0.94 / 0.90 (mean / LCB80). Both match the STUDY (Budget
  table l. 784-796, fidelity table l. 555-559).
- **Critical A1, traced.** v4 l. 971-972: "**Cap** (restored from DELTA §5.3): at most 12 confirm
  cells per confirm wave; Kai picks from the ranked lists at K3/K3a. Nothing advances automatically
  into GPU time." v5: `grep -i "cap\b|12 confirm|advances automatically|at most 12"` hits only change
  log l. 45 and l. 55. DELTA.md l. 858 and l. 1023 still carry the cap. Confirmed.

## Adjudication of v5 findings

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | The DELTA §5.3 12-cell confirm cap was dropped in the v5 consolidation. The change log (l. 53-55) still says the body restores it, [DK6] (l. 45) amends the order of a rule the body no longer states, and the Falsifier (l. 735-737) sends lists to K3a with no bound | crit A1 | A | **A** | Case 3, confirmed (Independent checks). DELTA l. 858 still carries the cap, so one could argue it binds anyway; the defect is the STUDY's own: it claims a restored rule that is absent, amends it, and leaves K3a unbounded in the text Kai reads. Same defect class as v1 #4 (rated A). Not on arbiter v4's deletion list. Three-line restore, no new rule |
| 2 | The label threshold T is set by Monte Carlo noise: the rule's pass set is not an interval (5M 0.8 / 0.9 fail, 1.0-1.3 pass; 350k 1.2 fails, 1.3-1.5 pass, 1.6 fails), vetoes and passes come from sets of 1-8 of 20,000 draws, the design seed returns the largest T of the seeds tried, and [DK8] calls the failures "consistent" | phys B1 / crit B1 / cons B1 (merged, as instructed) | B / B / B | **B** | Case 1. Reproduced over ten seeds (Independent checks). The defect is in the v4 arbiter's own rule text ("wherever that conditional set is non-empty", arbiter v4 fix 2(ii)); it reads Monte Carlo noise and is **replaced** here, not defended. The fixer applied it correctly. Rule fixed now (fix 2): condition (ii) is evaluated only at q where P(s_int ≤ T \| q) ≥ 0.01; (i) and (ii) are evaluated at ten RNG seeds (20260927, 1-9); T is the minimum over the ten. Both parts are needed: the floor alone is edge-sensitive (sets of 200 / 201 decide 350k 1.9 and 5M 1.4 at the design seed). Arbiter's reproduced values: **T = 1.2 pt (5M), 1.8 pt (350k)**; per-seed ranges 1.2-1.3 / 1.8-1.9. Crit B1's alternative (upper 95 % bound) is not taken: it passes every small set and is permissive at the edge |
| 3 | The arbiter's grid-fineness condition (consecutive median s_int within 0.1 pt) fails below 1.0 pt (0.186 / 0.421 pt) and the STUDY does not say so, though the fixer report says it does | crit B2 | B | **B**, folded into fix 2 | Case 3, confirmed (0.186 / 0.055 and 0.421 / 0.093 pt). The jump region lies below 1.0 pt and no T candidate is in it, so the substance is nil; the missing disclosure is the defect. One sentence in the rewritten [DK8] block |
| 4 | The [DK16] block reports that the extension gains nothing inside the band but not that §18 shows it gains above the band at 350k (0.49 → 0.60, 0.45 → 0.59) | crit B3 | B | **B** | Case 3, reproduced. Still true after T moves to 1.8 (median s_int 2.56 / 2.72 at q 0.33 / 0.5). Disclosure only: the rows go into the [DK16] block, and "extend above T at 350k" becomes an ALTERNATIVES entry priced from the existing Budget row (326 runs, 1,188.1 / 2,034.9 pod-hours). It is Kai's choice at the launch gate, not a new branch in the rule |
| 5 | Under per-run two-mode seeds a median-of-4 paired g recovers far more than mean g (5M 0.54 → 0.96 at q 0.05, 0.29 → 0.85 at q 0.1) at no run cost; the design never computes it, and the box reports only mean-g recovery | cons B2 | B | **B** (companion); primary switch to Kai | Case 3, reproduced. It is a non-selecting companion in the same form as the existing ones, so it adds no gate. The primary statistic is [DK6], Kai-decided (`decisions.md` "2026-09-27 (Kai, direct)"), so the STUDY's primary does not move in this iteration; the switch and its trade-off go to "What Kai must decide". The companion is required because without it the box states a resolving-power limit ("n = 4 cannot rank under per-run two-mode seeds") that holds only for the mean; that is an under-statement of what the data resolve (§6.3 q4) |
| 6 | The family-test power is given only at +1 pt; the effect it can see in pt (50 % power 1.65-4.10 pt at m 11, 2.50-6.25 pt at m 37, σ 0.6-1.5; about 13 pt at 5M and 3.14 pt) is not stated beside the headline question | phys B2 | B | **B** | Case 3, reproduced (Independent checks). §6.3 q4 asks for resolving power in the thesis unit. One print in §15 and one clause beside the family-test clause in the box, Question and Falsifier |
| 7 | The box's "recovery 1.00" for a seed-shared mode restates an assumption: in that model the cell × seed interaction is the within-mode sd, 0.3 pt, by construction | phys B3 | B | **B** | Case 3, confirmed: §18 seed-shared rows print median s_int 0.30 pt at every q. One clause in the box |
| 8 | "The ranking's resolution is set by n and the interaction sd … not by σ" contradicts the preceding sentence (matched sd, different recovery) | crit C1 | C | C | Reword as the critic proposes |
| 9 | Box range "0.14-0.28" is the three named q; the grid spans 0.10-0.29 | crit C2 | C | C | Name the q values or quote the grid range |
| 10 | 350k ranked list "11" should be "at most 11" (five paired-if-hash cells) | crit C3 | C | C | |
| 11 | Consolidation dropped four scope half-lines (cell-side-only loss scope; placebo [D17] rule; M049 at 5M runs; "by mean g" in the AUC-concordance flag) | crit C4 | C | C | Restore all four; each is one half-line |
| 12 | Experiment-log stub header still asks "or 350k feasibility"; INDEX line stale | crit C5 | C | C | Header update; `tools/index.py build` is the orchestrator's |
| 13 | Stray indentation at l. 627, 671, 678 | crit C6 / cons C3 | C / C | C | Reflow |
| 14 | Direction of the rare mode (data have the high value in the minority); rare-high changes recovery and gives T 1.4 / 1.4 under the old rule | phys C1 | C | C | One sentence: "q > 0.5 (rare high mode) not simulated; physics v5 variant gives T 1.4 / 1.4 under the v4 rule". Not a new block |
| 15 | s_int is noisy near T (df 30, relative SE about 13 %) | phys C2 | C | C | Print a 90 % interval on s_int in the header. A "near threshold" label would be a new branch and is **not** adopted |
| 16 | Confirm should restate the metric in AUC or working-point efficiency | phys C3 | C | C | One line in [L]-list or Bearing on the thesis |
| 17 | Per-cell EBOPs column in the forest plot | phys C4 | C | C | One phrase in the figures row |
| 18 | M001 borderline: label with the other six or state its floor's reproducibility | phys C5 | C | C | |
| 19 | Welch-list SE sentence wrong at ρ = 0 (equal SE; Welch half-width narrower at n = 4: 1.04 vs 1.35 pt at σ 0.6) | cons C1 | C | C | Reproduced. Use the constructive wording |
| 20 | Mode flag operating characteristics; n_low defined independent of the flag | cons C2 | C | C | Print false flag 0.067 and power beside the flag (numbers from a §18 print, not this file). n_low against a fixed threshold is optional; if adopted, it stays descriptive |
| 21 | How s_int handles a lost replica seed | cons C4 | C | C | One clause |

No B is raised to A; no finding is dismissed. The only A (row 1) is a restore of a pre-existing
DELTA rule.

## Earlier A and B findings (arbiter v4), by name

| v4 # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 (B) | labels on s_int, not sd_rep | **resolved** | s_int defined l. 652-655, df (m − 1)(n − 1); side-by-side print l. 655-656; label rule l. 656-658; caveat once l. 661-663; sd_rep one role l. 443-446, [D7] l. 870-871. The threshold T it reads is row 2 above (a defect in the v4 T rule, not in fix 1) |
| 2 (B) | two-mode rows; thresholds that hold under them | **resolved as specified; the specification was defective → row 2, row 3** | §18 present and re-run digit for digit (Independent checks); two-mode table l. 561-570; Gaussian tables labelled "optimistic under per-run two-mode seeds" l. 532, 553 |
| 3 (B) | floor-family question | **resolved** | frontmatter l. 6; Question l. 211-215; G2 l. 612-620 "rescue expected from floor arithmetic", M001 "borderline" l. 215, 617 |
| 4 (B) | ranked-list membership (Welch cells out, "at most 35") | **resolved** (C residual row 10) | l. 185, 328-330, 631-644; "design grid m = 37" l. 551, 641, 649, 671, 699; grep finds no unlabelled "37" after the change log |
| 5 (B) | pause default ≈ full launch; Falsifier / K3a text | **resolved** | pause withdrawn (grep: `pause|ceiling|DK17` hits only change log, withdrawal notes l. 873-874, 888, 945, and the two different rules l. 401, 472); Falsifier l. 735-737 |
| 6 (B) | per-cell constraint label | **resolved** | l. 463-467 (M003, M007, M008, M011, M012, own seeds, ⌈3k/4⌉); 0.8 / 0.9 rationale l. 460-463; β tolerance l. 459 |
| 7 (B) | family test in every family | **resolved** | l. 662-663, 731-733 |
| 8 (B) | one mode readout line | **resolved** (C residual row 20) | l. 447-451; n_low l. 705-706; no decision reads it |
| deletion list | compute pause, [DK17], options, budget rows, §10 / §14 citations, "(4, 4) only if" | **resolved**, with one collateral loss | all deleted (critical v5 item-by-item audit, arbiter grep above); A07 memory pause l. 400-402 and base stability l. 470-473 kept as instructed. Collateral loss: the confirm cap (row 1) and four scope half-lines (row 11) |
| C items 9-19 | phys C1-C5, crit C1-C5, cons C1-C4 | **applied** | critical v5 table row "fix 7 C items" cites a line for each; spot checks l. 6, 713-716, 740, 1013-1016, Appendix A l. 1029 |

## Regression triggers (§6.7), each checked

| trigger | status | evidence |
| --- | --- | --- |
| selection on held-out, or changed after results | not met | validation only (l. 579, 720); no result exists; the T change is a labelling rule changed before any run, with a dated amendment (fix 2) |
| val AUC vs ROC-test AUC > 0.01 | not met | no ROC-test evaluation (l. 720) |
| single-seed / < 100-epoch / lab-pod headline against the record | not met | never quotable; Reference table has no comparand (l. 231-246) |
| comparison across N, input sets, splits, schedules as one series | not met | M009 in the Welch list (l. 636-637); long-horizon list apart (l. 637-639) |
| gap smaller than seed sd with < 3 seeds | not met | n ≥ 4; n_p ≥ 3 for any reading (l. 604-606) |
| reload outside 1e-7, TF32 on | not met | l. 506, 853 |
| eBOPs not remeasured on the selected checkpoint | not met | certification l. 598-601 |
| binary layer with > 2 values | not met | conventions row l. 853 |
| DSP / C-sim / C-synthesis | not applicable | l. 854 |
| per-class AUC < 0.7 hidden | not met | l. 703-704 |
| byte-identical arms / different y arrays | not met; watch | y_val sha asserted (l. 434-437); the placebo's bit-identical reading is pre-registered (l. 681-688) |
| failed validation without remediation; tautological comparison as validation | not met | nothing has run; T comes from simulation only, not from the data it labels |
| STUDY [D] label replaced without dated amendment | not met; **watch in fix 2** | [D7], [D8], [DK8] dated v5 (l. 870-874, 884-885). Fix 2 changes [DK8]'s values: dated v6 amendment required. The cap (row 1) is a DELTA rule, not a [D] label |
| outward numbers ≠ VERIFY | not applicable | none |
| suspiciously good | not applicable | no results |

No trigger is met; no investigator and no `REGRESSION_TICKET.md`.

## §6.8 validation target

No binding comparand, correctly, for a never-quotable screen (l. 231-246). Unchanged.

## Motivated reasoning

- **350k T rises 1.5 → 1.8.** A loosened label threshold reads as "moved the rule so the list is
  called ranked". Checked, and it does not hold. The 1.5 was the largest T over ten seeds under a
  rule that one draw of 20,000 could veto or pass; 1.8 is the smallest over ten seeds under a rule
  that ignores q with under 1 % chance of the observed s_int. The real failure region is unchanged
  (T ≥ 2.0 fails on sets of 34-18,795 at recovery 0.26-0.44), Gaussian recovery at 1.8 is 0.65, and
  the value stays far under the Gaussian-only 3.0. At 5M the change runs the conservative way
  (1.3 → 1.2). No data exist, and `budget.py` confirms nothing that runs depends on T.
- **"The failures are consistent"** ([DK8] l. 929-930) is not accepted: it cited the failures above
  T and omitted those below. Fix 2 replaces it with the per-seed table.
- **The box's "0.14-0.28"** understated what n = 4 seeds can resolve under per-run two-mode seeds
  (it holds for the mean only). An under-claim, but §6.3 q4 asks for honesty in both directions:
  fix 4.
- **"Cost: none" for [DK8]**: correct.
- Checked and not found: no interval inflated (paired multiplier simulated; unpaired companion
  non-selecting); no selection rule moved after results; G3′ failure not read as inferiority
  (l. 628-629); "no" not claimed as absence (l. 199-200, 734-735); the cap drop (row 1) removed a
  bound, not a burden, but it was collateral in a consolidation, not an argued change.

## Competing-group question

A group publishing the same screen next month would have: a stated confirm cap (row 1); a
"ranked" / "descriptive" threshold that reproduces when its own script is re-run at another seed
(row 2); a robust seed aggregate beside the mean for a seed population known to be two-mode
(row 5); the family test's detectable effect in pt (row 6). All four are text or a short script
change, no GPU.

## Disputed facts for the investigator

None. Every fact was settled from the artifact, the v4 STUDY, DELTA.md, and the arbiter's runs of
`screen_null.py` (20 variants), `budget.py`, `rank_sim.py`, `constructive_v5_robust.py` and `arbiter_v5_power.py`.

## Dismissals

None.

## Verdict: **ITERATE** (iteration 5, §6.5 strong warning; the fixer's pass is iteration 6)

One Category A (row 1) and six B items (rows 2, 3 folded into 2, 4, 5, 6, 7). All verified against
the artifact or the arbiter's runs; none can be downgraded (§6.5.1).

### Fix list for the `fixer`, in priority order

Add a **v6 change-log entry, dated 2026-09-27** (or the date of the fix). Change-log entries v1-v5
are not rewritten; where they state a T value (l. 158-159) they get an annotation "[T replaced in
v6]". Every changed number cascades to each place it appears; the fixer's report lists each site
as "changed" or "unaffected because …".

1. **(A, row 1) Restore the confirm cap.** One bullet after "Lists" in the Selection rule:
   "**Cap** (DELTA §5.3; order amended by [DK6]): at most 12 confirm cells per confirm wave, taken
   in mean-g order from the ranked lists; Kai picks at K3/K3a; nothing advances automatically into
   GPU time." Add "(at most 12 cells, Selection rule 'Cap')" to the Falsifier sentence at
   l. 735-737.
2. **(B, rows 2 + 3) Replace the T rule, fixed now.**
   (a) `screen_null.py` §18: condition (ii) fails a q only where P(s_int ≤ T | q) ≥ 0.01 (write
   the floor as a probability, not a draw count). Conditions (i) and (ii) are evaluated at ten RNG
   seeds, the design seed 20260927 and seeds 1-9; T per family is the **minimum** over the ten.
   Implementation: a `--seed` argument plus a small driver, or a wrapper in the style of
   `review/constructive_v5_tstab.py`; §1-§17 must still reproduce digit for digit at the design
   seed. §18 prints the per-seed T table. Expected output (arbiter's runs, to be reproduced by
   the script, not quoted from here): **T = 1.2 pt at 5M, 1.8 pt at 350k**, per-seed 1.2-1.3 /
   1.8-1.9. The 5M `check` print (hard-coded 1.3) follows T; the 350k unconditional check (q 0.33 / 0.5) does not read T and stays.
   (b) STUDY Label (l. 658-661): state the new rule in one sentence (floor, ten seeds, minimum)
   and the values. Keep "The family test is read in every family".
   (c) [DK8] block (l. 926-933): replace "the failures are consistent" with the per-seed table
   (written rule and floor rule, both families), the sentence "the floor alone is edge-sensitive
   (sets of 200-201 at the design seed); the ten-seed minimum absorbs it", and one sentence on
   the grid condition: "consecutive median s_int differ by ≤ 0.1 pt above 1.0 pt (0.055 / 0.093)
   and cannot below it (0.186 / 0.421, low-mode count jumps in the m × 4 matrix); no T candidate
   lies in that region". ALTERNATIVES: the v5 values 1.3 / 1.5 (one seed, written rule); one T
   for both families (1.2); the Gaussian-only limits.
   (d) Cascade: the [DK16] band becomes 1.0-1.2 pt (5M) and 1.0-1.8 pt (350k) at l. 521-525 and
   935-941; regenerate the in-band rows at l. 534-536 and every "recovery | s_int ≤ T" value from
   §18 at the new T; the [DK16] Gaussian gain is quoted "at σ 1.3", which is above the 5M band
   now: quote it at σ 1.0 (§16 has that row: 0.77 → 0.87). Change log v6; [DK8] label line
   l. 884-885 "amended v6"; `plan.md` l. 129 and 155-157 tagged "[superseded v6]"; the
   experiment-log stub (Design line, "T = 1.3 pt (5M), 1.5 pt (350k)").
3. **(B, row 4) [DK16] above-band disclosure.** In the [DK16] block and Seeds l. 534-536 add the
   above-band two-mode rows from §18 (350k q 0.33 / 0.5: 0.49 → 0.60, 0.45 → 0.59; 5M 0.19 →
   0.19, 0.14 → 0.23, script values). Add to ALTERNATIVES: "extend above T at 350k, the '+
   extension, 350k only' Budget row: 326 runs, 1,188.1 / 2,034.9 pod-hours". Disclosure only;
   the band rule does not change.
4. **(B, row 5) Median g as a third non-selecting companion.** In "Winner's curse, non-selecting
   companions" (l. 689-702): per cell, median of the n paired g_s and its rank; per family,
   Kendall τ against the primary; cells in the top 12 (5M) or top 3 (350k) by one statistic and
   not the other are marked for K3a, in the same form as the accuracy-vs-AUC flag (l. 710-712). No
   threshold, no reuse of the rank-move T. One §18 print: mean-g and median-g recovery under
   Gaussian σ 0.6 / 1.0 / 1.3 and per-run q 0.02 / 0.05 / 0.1 / 0.2 / 0.33 / 0.5, both families,
   so the numbers are the script's. Box (l. 193-198): beside "0.14-0.28" put the median-companion
   recovery over the same q from that print, with one clause: the median hides a lever that
   changes mode probability, which n_low reads. Readout line (l. 703-712): add "median g and its
   rank". [DK6] stays: mean g is the primary.
5. **(B, row 6) Detectable effect in pt.** One print in §15: the effect for 50 % / 80 % power of
   one named cell at the §13 critical value, m 11 / 37, σ 0.6 / 1.5 / 3.14. One clause in the box
   (l. 199-200), Question (l. 207-209) and Falsifier (l. 734-735): "it sees, at 50 % power, about
   X-Y pt at σ 0.6-1.5" with the script's values (arbiter's: 1.65-4.10 pt at 350k, 2.50-6.25 pt
   at 5M).
6. **(B, row 7) Seed-shared clause.** Box l. 196: "1.00 because the seed-shared model's cell ×
   seed interaction is the within-mode sd, 0.3 pt, by construction; the design measures s_int
   instead of assuming it".
7. **(C, apply before commit)** rows 8-21. Do not adopt a "near threshold" label (row 15) or any
   rule reading n_low (row 20).

**No fix adds a gate or a branch.** Fix 1 restores a pre-existing DELTA rule; fix 2 changes a
design-time computation of one constant per family; fix 3 is an ALTERNATIVES line priced from an
existing Budget row; fix 4 adds a print and a mark in an existing flag form; fixes 5-6 are a print
and text. `budget.py` is unaffected (T moves labels only); the fixer re-runs it once to confirm.

## What Kai must decide (at the launch gate; not a STUDY blocker)

The fixer writes each as a "Where I am not sure" row with its cost.

1. **Primary ranking statistic, mean g against median-of-4 g** ([DK6] is his; this iteration adds
   the median only as a companion). Trade-off from the arbiter's re-run of
   `constructive_v5_robust.py` (to be replaced by the §18 print, fix 4), 5M, three +1-pt cells in
   the top 12:
   - Gaussian seeds, median costs: 0.99 → 0.96 (σ 0.6), 0.77 → 0.66 (σ 1.0), 0.57 → 0.47 (σ 1.3);
   - per-run two-mode seeds, median gains: 0.78 → 0.99 (q 0.02), 0.54 → 0.96 (q 0.05), 0.29 →
     0.85 (q 0.1), 0.11 → 0.56 (q 0.2); little at q 0.33 / 0.5 (0.19 → 0.27, 0.14 → 0.26);
   - seed-shared mode: 1.00 either way;
   - caveat: the mean credits a lever that lowers the low-mode probability (a stability lever);
     the median hides it, and n_low is that readout. Switching changes no run and no cost; it
     changes which list K3a reads first. The data that decide it (s_int against sd_rep, ρ̂, the
     mode readout) arrive at the replica epoch-500 gate, before any cell reads.
2. **Label thresholds** (fix 2): 1.2 / 1.8 pt from the fixed rule, against one T for both
   families or the v5 values. Labels only.
3. **[DK16] extension**: in-band only (as designed; nil gain under per-run two-mode seeds), or
   above T at 350k (+24 runs, 1,188.1 / 2,034.9 pod-hours at r = 1 / 2, gain 0.49 → 0.60 at
   q 0.33), or n = 6 for every cell.
4. **Compute touchpoint at the replica gate** (carried from v4): none pre-registered; the full
   (4, 4) runs (302 runs, 1,112.2 / 1,959.0 pod-hours, 240 packable today).
5. **[DK18]** (carried): 350k follow-up (84 runs, 366.5 pod-hours) or confirm with the slack
   label, at K3.
6. **X5** (carried): the non-binary path under [A20], for the patches owner and Kai.
7. **Carried defaults** [DK1]-[DK5], [DK7], [DK9]-[DK16], [DK18]; [DK8] as amended v6; [DK6] and
   launch gate 1 already Kai-decided.
