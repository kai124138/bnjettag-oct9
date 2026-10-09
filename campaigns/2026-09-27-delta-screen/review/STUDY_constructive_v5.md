# STUDY review, constructive, v5: 2026-09-27-delta-screen (Delta wave 2)

Reviewer: constructive-reviewer, fresh context, 2026-09-27. Artifact: `STUDY.md` (1,068 lines,
14,762 words, iteration 5, after fixer v4, commit 094db11). Read: `docs/methodology/06-review.md`,
`03-phases.md` Phase 1, `docs/conventions/jet-tagging-metrics.md`, `review/STUDY_arbiter_v4.md`,
my own `review/STUDY_constructive_v4.md` (to track findings by name), `screen_null.py`, `budget.py`,
`plan.md` (grep), the newest entries of `.claude/memory/experiment-log.md` and
`.claude/memory/research-log.md` (2026-09-27 screen-design entry). Not read: the physics or
critical files of this or any iteration.

**Verdict in one line. No Category A.** Two B items, both text plus one script block, no GPU.
B1: the pre-registered label threshold T is a Monte-Carlo artefact. Across six RNG seeds of the
unchanged `screen_null.py`, the rule as written returns T = 0.9-1.3 pt at 5M and 1.1-1.5 pt at
350k, and the STUDY's 1.3 / 1.5 is the most permissive draw in both families. B2: under the
seed structure the STUDY calls dominant (two-mode, drawn per run), a median-of-4 paired g ranks
far better than mean g (5M recovery 0.96 against 0.54 at q 0.05, 0.85 against 0.29 at q 0.1).
It needs no mode assignment and no new run. The box reports 0.14-0.28 without it. Four C items.

## Reproduced (evidence for the [+] items)

- `uv run --with numpy,scipy python screen_null.py` (seed 20260927, 18 s) reproduces every number
  the STUDY quotes from it:
  - §13 critical values: 4.284 / 6.585 at n = 4 and 6.733 / 12.290 at n = 3.
  - §15: false "yes", power 0.214 / 0.087 / 0.051 / 0.026 (m 11) and 0.077 / 0.030 / 0.016 /
    0.007 (m 37), multipliers 2.168 / 2.136, unpaired critical values 2.880 / 3.590.
  - §15 Gaussian recovery (5M 0.57 at 1.3, 0.52 at 1.4; 350k 0.73 at 1.5).
  - §18:
    - T = 1.3 (5M) and 1.5 (350k);
    - per-run recovery 0.79 / 0.55 / 0.28 / 0.19 / 0.14 at 5M; seed-shared recovery 1.00;
    - extension in the band 0.61 / 0.58 / 0.51 against 0.61 / 0.56 / 0.49;
    - the [DK8] failure rows (1.4 fails on 201 draws at 0.43; 350k 1.6-1.9 on 1-8 draws).
  ✓
- `budget.py` (v5): (4, 4) 302 runs, 176,000 run-epochs, 1,112.2 pod-hours at r = 1, 318
  certifications; extension 390; packable today 240 / 142,000; cheap 129 / 79,500. ✓
- Cascade grep (`pause|ceiling|§14|§10|DK17|37`): the remaining hits are the change log, the
  withdrawal notes at l. 873, 888 and 945, the A07-memory pause (l. 401) and the base-stability
  pause (l. 472). The last two are different rules and correctly stay. Every "37" after l. 180 is
  labelled "design grid". ✓
- New scripts in `review/` (seeded, design arithmetic, not results):
  - `constructive_v5_tstab.py`: `screen_null.py` unchanged except the RNG seed and an optional
    minimum conditional-set size;
  - `constructive_v5_robust.py`: mean g against median g under Gaussian and two-mode seeds, plus
    mode-flag power and the Welch half-width;
  - `constructive_v5_pooled_mode.py` and `constructive_v5_mode12.py`: alternative mode flags
    (neither is recommended, see C2).

## What is done well

- [+] **The compute pause is gone, cleanly.** Withdrawn with its budget rows, its options and
  Falsifier (v). [DK17] is marked withdrawn (l. 888), and the grep finds no stale branch text. The
  design is now the (4, 4) screen, and the box says so. The pause saved at most 48 of 302 runs,
  so removing it simplified the design at almost no cost.
- [+] **Labels read the right variance.** s_int is defined once (l. 652-658), with df
  (m − 1)(n − 1) = 30 / 108. It reads no effect size or order. It is printed beside sd_rep, s_pool
  and ρ̂. l. 572-577 explains in two sentences why a seed-shared term cancels, and the two-mode
  table shows it (seed-shared column 1.00). My v4 B1 is resolved as intended.
- [+] **The box tells the truth about the likely case.** l. 193-199 says that at the only
  measured spread recovery is 1.00 or 0.14-0.28, depending on a mechanism nobody has measured,
  and that the design measures it instead of assuming it. l. 199-200 says the family test is
  "calibrated and nearly powerless". A reader of the box takes away the right sentence (but see
  B2, which changes what the right sentence is).
- [+] **The T rule prints its own failures.** [DK8] (l. 926-933) shows the rows that fail and
  their set sizes instead of hiding them. That is what made B1 findable.
- [+] **The family test is read in every family** (l. 662-663, 731-733), and a descriptive list
  is limited to "nomination with its label, never a resolved gap" (l. 737). My v4 B2 is resolved.
- [+] **Per-cell constraint label** for the five EBOPs-pressure cells on their own seeds, with a
  one-line rationale for 0.8 and 0.9 and a stated β tolerance (l. 454-468).
- [+] **Significance mode moved to Appendix A** with a one-line pointer (l. 210). The artifact
  went from 1,681 lines at v4 to 1,068 now (`wc -w` 14,762) without losing a rule.

## Category A

None.

## Category B

### B1. The label threshold T is set by Monte-Carlo noise; the pre-registered 1.3 / 1.5 pt is the most permissive of six seeds

- **Current state.** T is "the largest 0.1-pt value at which … recovery among draws with
  s_int ≤ T is ≥ 0.5 at every q of the grid where such draws exist" (l. 658-661; `screen_null.py`
  l. 410-414: `(si <= T).sum() > 0`). A conditional set of **one** draw in 20,000 can therefore
  veto a T. At that size its recovery is 0 or 1 by chance. The design run shows this:
  - at 350k, T = 1.6 fails on 1 draw, 1.7 on 3, 1.8 on 1 and 1.9 on 8;
  - T = 1.2 fails on 3 draws while 1.3-1.5 pass, so the rule is not even monotone in T;
  - at 5M, 0.8 and 0.9 fail on 1 and 5 draws.

  [DK8] reads the 1.6-1.9 failures as "consistent" with the 2.0-3.0 failures. They are events of
  probability under 1/2,500 per family.
- **Evidence** (`review/constructive_v5_tstab.py`, `screen_null.py` with only the RNG seed
  changed, 20,000 reps as designed):

  | rule | seed 20260927 (STUDY) | seeds 1 / 2 / 3 / 4 / 5 | range |
  | --- | --- | --- | --- |
  | as written (set ≥ 1 draw), 5M | 1.3 | 1.0 / 1.1 / 1.1 / 0.9 / 1.2 | 0.9-1.3 |
  | as written, 350k | 1.5 | 1.3 / 1.2 / 1.1 / 1.4 / 1.2 | 1.1-1.5 |
  | set ≥ 200 draws (P(s_int ≤ T) ≥ 0.01), 5M | 1.3 | 1.2 / 1.3 / 1.3 / 1.2 / 1.2 | 1.2-1.3 |
  | set ≥ 200 draws, 350k | 1.9 | 1.9 / 1.9 / 1.8 / 1.9 / 1.9 | 1.8-1.9 |

  Under the rule as written, the STUDY's seed gave the largest T of the six in both families. So
  the pre-registered value is not what the stated rule produces; it is one draw of it. A
  different RNG seed of the design script would have given a different "pre-registered"
  threshold. The label does not reach a figure yet, but it decides whether K3a reads a list as
  "ranked" or "descriptive".
- **Improved state.**
  - Evaluate condition (ii) only at q where the conditional set has probability ≥ 0.01, that is
    where a real family could plausibly land. That is 200 of 20,000 draws.
  - Run §18 at five or more RNG seeds (or at 10× the reps) and fix T as the **minimum** over
    seeds. The minimum is the conservative end. Print the per-seed values beside it.
  - With the floor the rule is almost seed-stable. It gives **T = 1.2 pt at 5M and 1.8 pt at
    350k**. The 5M boundary sits at the floor itself: 1.4 fails on 201 draws at seed 20260927.
    Taking the minimum over seeds absorbs that.
  - The 350k value moves up, not down. That is the honest outcome of removing noise-driven
    vetoes. Under the floor it still stays well under the Gaussian-only 3.0 pt: from 1.9-2.0
    upward, condition (ii) fails on sets of at least 200 draws at every seed (the design run
    shows 2.2-3.0 failing on 338-18,795 draws at 0.38-0.44), and those are real failures.
  - Say in [DK8] that the rule is evaluated with a probability floor and a seed minimum. Replace
    "the failures are consistent" with the per-seed table.
- **Why.** A pre-registered threshold has to be the output of a stated rule, not of one RNG
  draw. As written, a referee who reruns `screen_null.py` with another seed gets a different T
  and can fairly ask whether the seed was chosen. The fix makes the answer reproducible, costs no GPU and changes only labels.
- **Effort.** Low: a one-line change in §18, a loop over seeds (about 4 min of CPU), and [DK8],
  Label (l. 658) and the experiment-log stub updated with the new T.

### B2. Under the seed structure the STUDY calls dominant, a median-of-4 paired g recovers most of what mean g loses, at no run cost; the design does not compute it

- **Current state.** The one ranking statistic is mean g ([DK6], Kai-decided; l. 645-651), with
  last-epoch and split-half companions (l. 689-702). Those companions change the *checkpoint*,
  not the *aggregation over seeds*. Under per-run two-mode seeds, one low-mode run (5.4 pt down)
  in a cell or in the replica moves a 4-seed mean by 1.35 pt. That is larger than the +1-pt
  effects the design is sized for, and it is why 5M recovery falls to 0.55 / 0.28 at q 0.05 /
  0.1. The box (l. 193-198) reports 0.14-0.28 as what n = 4 resolves in that case. `plan.md` and
  the STUDY never consider a robust aggregate (grep: no "median", "trimmed", "robust" or
  "Hodges").
- **What this is not.** Arbiter v4 dismissed "within-mode paired g" because a mode assignment at
  n = 4 leaves 1-3 seeds per mode. The median of the four paired g_s needs **no mode assignment,
  no threshold and no extra certification**. It is the same four certified checkpoints per cell,
  aggregated differently.
- **Evidence** (`review/constructive_v5_robust.py`, seed 5092027, same seed model as §18: jump
  5.4 pt, within-mode sd 0.3 pt; 5M m 37, three +1-pt cells in the top 12; 350k m 11, one in the
  top 3; n 4). Recovery, mean g / median g:

  | seeds | 5M | 350k |
  | --- | --- | --- |
  | Gaussian σ 0.6 | 0.99 / 0.96 | 0.99 / 0.98 |
  | Gaussian σ 1.0 | 0.77 / 0.66 | 0.89 / 0.84 |
  | Gaussian σ 1.3 | 0.57 / 0.47 | 0.80 / 0.74 |
  | per-run, q 0.02 | 0.78 / **0.99** | 0.92 / **1.00** |
  | per-run, q 0.05 | 0.54 / **0.96** | 0.81 / **0.99** |
  | per-run, q 0.10 | 0.29 / **0.85** | 0.66 / **0.95** |
  | per-run, q 0.20 | 0.11 / **0.56** | 0.49 / **0.81** |
  | per-run, q 0.33 | 0.19 / 0.27 | 0.48 / 0.60 |
  | seed-shared, any q | 1.00 / 1.00 | 1.00 / 1.00 |

  - The mean-g column reproduces §18 (0.79 / 0.55 / 0.28 there).
  - The median costs 0.05-0.11 under Gaussian seeds.
  - It gains 0.4-0.6 in the q range where mean-g recovery is 0.3-0.55 (q 0.05-0.1, median
    s_int 1.2-1.6 pt), which straddles the 5M label boundary.
  - Among 5M families with s_int ≤ 1.3 at q 0.1, recovery is 0.51 by the mean and 0.93 by the
    median.
- **Caveat, stated once.** The two statistics answer different questions:
  - mean g credits a lever that lowers the probability of the low mode (a stability lever);
  - the median hides that effect and measures the within-mode shift;
  - n_low (l. 705-706) is the readout for the stability part.

  So the median belongs beside the mean, not in place of it. Replacing the primary is Kai's call
  under [DK6].
- **Improved state.**
  - Add **median g** as a third non-selecting companion. Per cell: median g and its rank. Per
    family: Kendall τ against the primary. Cells in the top 12 (5M) or top 3 (350k) by one
    statistic and not the other are marked for K3a, in the same way as the existing
    accuracy-vs-AUC flag (l. 710-712). The rank-move T values (§15) were simulated for the
    last-epoch companion, so do not reuse them. Print τ and the marks only, or add a §18 block
    for a median null.
  - Add one §18 block that prints both columns above, so the numbers are the design script's and
    not this review's.
  - In the box (l. 193-198), put the median-companion recovery over the same q span beside
    "0.14-0.28": 0.26-0.85 (q 0.5 → 0.1; this review's script until the §18 block exists).
    Otherwise the reader's takeaway, that n = 4 cannot rank under per-run two-mode seeds,
    overstates the limit: n = 4 cannot rank *by the mean* there.
  - Optionally, in "Where I am not sure", offer Kai the switch of the primary with the Gaussian
    cost (0.77 → 0.66 at 5M, σ 1.0) against the two-mode gain.
- **Why.** The only measured N=64 spread is two-mode (67.18 / 72.64 / 67.21 %, l. 243). The STUDY
  says the dominant uncertainty is whether that mode is per run or seed-shared, and the box
  frames the wave's resolving power around it. If it is per run, the design as written returns a
  "descriptive" 5M list with recovery 0.3 or less. The same data, aggregated by a median, would
  have recovered 0.85. That is the largest resolving-power gain available anywhere in this
  design, and it costs no GPU. It is also what a competing group would report (§6.3 question 3):
  a robust location estimate beside the mean when the seed distribution is known to be
  heavy-tailed. Picard 2021 is already cited for exactly this (l. 1022; `research-log.md`
  2026-09-27).
- **Effort.** Low: text in Selection rule, Readout, the box and [DK6]'s "Where I am not sure";
  one §18 block (seconds of CPU); a few lines at VERIFY.

## Category C

- **C1. The Welch-list SE sentence is wrong at the STUDY's own planning ρ.**
  - *Current (l. 634-636):* the floor-family package's "SE is about √2 larger and df about
    2(n − 1), so a paired power row overstates it".
  - *Check:* at ρ = 0, which is the STUDY's planning case (l. 713-719 says there is "no
    information on ρ"), the paired SE σ√2/√4 equals the Welch SE σ√(2/4). The √2 holds only at
    ρ = 0.5.
  - *Effect of df:* with df 6 against 3, the Welch 95 % half-width at n = 4 is **narrower**:
    1.04 against 1.35 pt at σ 0.6, and 5.43 against 7.07 pt at σ 3.14
    (`constructive_v5_robust.py`, last lines).
  - *Improved:* "equal SE at ρ = 0 and √2 larger at ρ = 0.5; with df about 2(n − 1) against
    n − 1, the Welch interval is not wider at n = 4 unless ρ > 0; a paired power row overstates
    it only if pairing helps (ρ̂, l. 716)."
  - *Why:* as written, a reader concludes that the Welch cells are less resolved than the paired
    cells. Nothing measured says so.
  - *Effort:* low.
- **C2. Print the mode flag's operating characteristics, and define n_low without the flag.**
  - *Current:* the family is "two-mode" by a gap rule on the 8 replica values (l. 447-451), and
    n_low exists only if the flag fires (l. 705-706).
  - *Flag power* (`constructive_v5_robust.py`): false flag 0.067 under Gaussian seeds; power
    0.07 / 0.10 / 0.22 / 0.51 / 0.80 at per-run q 0.02 / 0.05 / 0.1 / 0.2 / 0.33. So the flag is
    weakest exactly where mean-g recovery collapses (q 0.05-0.1).
  - *Alternatives tried, not recommended:* the flag on the 12 lever-free values (replica +
    placebo) gains little (0.13 / 0.34 at q 0.05 / 0.1). The flag on the median-centred cell
    matrix breaks at high q (0.00 at q 0.33) (`constructive_v5_mode12.py`).
  - *Improved:* print the flag's false-flag rate and power beside it, so that "not two-mode" is
    not read as "Gaussian". Also count n_low in every family against a threshold fixed now,
    independent of the flag: for example, runs more than 2.7 pt (half the archived jump) below
    the replica median. It stays descriptive.
  - *Effort:* low.
- **C3. Mid-sentence line breaks with stray indentation** at l. 627 ("    0, ρ = 0, n = 4"), l. 671
  ("    REPORT carries …", which also runs to about 150 characters) and l. 678 ("    (m = 37)").
  These are fixer artefacts. Reflow them. *Effort:* low.
- **C4. State once how s_int handles a missing value.** "Cells with complete pairs only"
  (l. 653-654) drops a cell with a lost seed. It does not say what happens when a *replica* seed
  s ≤ 4 is lost. The cell accuracies still exist, but n_p drops uniformly (l. 483-489). One
  clause would settle it: "s_int uses the seeds of the family's n_p; a lost replica seed drops
  that column from every cell". Otherwise VERIFY has to decide it after the data exist.
  *Effort:* low.

## Earlier findings (constructive v4), tracked

| v4 item | status in v5 | evidence |
| --- | --- | --- |
| B1 labels read sd_rep, not the interaction sd | resolved | s_int defined l. 652-658; sd_rep's one role l. 443-446; l. 572-577 |
| B2 paused family reads no family test | resolved (pause withdrawn) | l. 662-663, 731-733 |
| B3 two-mode seeds only a nuisance | resolved at the arbiter's scope | mode readout l. 447-451; n_low l. 705-706; two-mode rows l. 561-570. Residual power issue: C2 above; estimator issue: B2 above |
| C1 frontmatter question length | resolved | l. 6 |
| C2 significance mode to an appendix | resolved | Appendix A l. 1029-1067 |
| C3 "expected from floor arithmetic" | resolved | l. 214, 616 |
| C4 init-vs-order factorial as follow-up | resolved | l. 1013-1016 |

## Answers to 06-review §6.3

1. **Conventions.** Implemented or declared as deviations, with reasons (l. 840-856). The
   flat-gap rule is declared as a deviation, correctly for n = 4.
2. **Reference table.** Present and sourced, and it correctly has no comparand for a
   never-quotable screen (l. 231-246).
3. **What a competing group would have.** A robust seed aggregate beside the mean for a
   heavy-tailed seed population (B2), and a label threshold that reproduces under a rerun of
   its own script (B1).
4. **Honest uncertainties and resolving power.** Honest in both directions: the box states
   0.14-0.28 recovery and a nearly powerless family test. It understates what the data could
   resolve under per-run two-mode seeds (B2), which is an under-claim, not an over-claim.
5. **Limitations with attempts.** [L1], [L6], [L7] and G3′ each carry an attempt or a power
   statement.
6. **Context.** Not applicable at STUDY (no results).

## Summary for the arbiter

No Category A. Keep:
- the pause withdrawal;
- s_int as the label variance;
- the box;
- the placebo-referenced own-sd family test read in every family;
- the per-cell constraint label;
- Appendix A.

The numbers reproduce digit for digit.

B1 is a reproducibility defect in a pre-registered threshold. Under the stated rule, T moves
0.9-1.3 (5M) and 1.1-1.5 (350k) with the RNG seed, and the STUDY's value is the top of both
ranges. A probability floor plus a seed minimum gives 1.2 / 1.8 pt, stable across seeds.

B2 is the largest resolving-power gain left in the design. A median-of-4 paired g, reported as a
non-selecting companion beside mean g, takes 5M recovery under per-run two-mode seeds from
0.54 / 0.29 to 0.96 / 0.85 at q 0.05 / 0.1. It costs 0.05-0.11 under Gaussian seeds and nothing
in GPU.

Both are text plus one script block.
