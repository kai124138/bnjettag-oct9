# STUDY critical review v6: 2026-09-27-delta-screen (Delta wave 2)

Critical reviewer, fresh context, 2026-09-28. Panel mode, re-review, iteration n = 6. No verdict
(the arbiter issues it).

Artifact: `STUDY.md` (1,160 lines, 16,331 words; HEAD 31db77d, after fixer v5 at 979331a and the
experiment-designer's median-g re-simulation), with `plan.md`, `budget.py`, `screen_null.py`
(§1-§19), `rank_sim.py` (v6 block). Read: `review/STUDY_validators_v6.txt`,
`review/STUDY_arbiter_v5.md`, `review/STUDY_fixer_v5.md`, `review/STUDY_critical_v5.md`,
`.claude/memory/decisions.md` top three entries, the experiment-log stub (l. 11-17),
`campaigns/2026-09-26-delta/DELTA.md` l. 858-860 and 1023-1026,
`campaigns/2026-09-26-training-batch/review/INCIDENT_stall_20260928.md` §0-§2 and
`campaigns/2026-09-26-training-batch/RUN.md` l. 455-510, `docs/methodology/06-review.md` §6.1 and
§6.4, `git diff 979331a HEAD` and `git diff --word-diff 094db11 979331a` on STUDY.md. The physics
and constructive v6 files were not read, to keep the panel independent.

Kai's rule for this round (`decisions.md` 2026-09-28): if only new Category B items remain, the
design is frozen and launched with them disclosed. I use A only for a genuine error, a dropped
pre-registered rule, or a claim contradicted by its own source, and I say for each B why it is
not A.

## Validator lines, verbatim

`review/STUDY_validators_v6.txt`:

```
STUDY validators v6 (2026-09-27 23:13)
No mechanical STUDY validator exists; prose_lint on STUDY.md:

Desktop/bnjettag/campaigns/2026-09-27-delta-screen/STUDY.md  —  score 0, reads human
  16331 words · 439 sentences · mean 24 words (σ=17.5) · 14% bullets · 1 em-dashes
```

No A-marked line. No plot-validator file (the STUDY has no figures).

## Recomputed (design arithmetic, laptop CPU, not results, not quotable)

Copies of `screen_null.py` and `rank_sim.py` run in the session scratchpad with
`uv run --with numpy,scipy python`. `screen_null.py` took 7 min 51 s of wall time, with nine child
processes.

- **§15 Gaussian grid, mean g**: 5M 1.2:0.63, 1.3:0.57, 1.4:0.52; 350k 1.8:0.65, 2.1:0.61. These
  match STUDY l. 623 ("0.55 against 0.63 at 1.2 pt").
- **§18 per-seed T.** All 40 values match the [DK8] block l. 1009-1010:
  - floor rule, mean g: 5M 1.3 / 1.2 1.3 1.3 1.2 1.2 1.3 1.3 1.3 1.3; 350k 1.9 / 1.9 1.9 1.8 1.9 …
  - v4 rule: 5M 1.3 / 1.0 1.1 1.1 0.9 …; 350k 1.5 / 1.3 1.2 1.1 1.4 …
- **§19a, median g.** 5M T 1.2 at all ten seeds. 350k T per seed 2.1 / 2.1 2.7 2.1 2.3 2.1 2.1
  2.6 2.6 2.1, minimum 2.1. Both match l. 1008 and l. 720-721.
  - Design-seed Gaussian recovery by median g: 5M 0.52 at 1.2 and 0.46 at 1.3; 350k 0.56 at 2.1.
  - 350k failing T values: 2.2-2.7 fail at q 0.5 on sets of 338-9,126 draws, recovery 0.45-0.50.
  - Both match l. 1012-1015.
- **§19b.** Values match Seeds l. 575-579:
  - 5M in-band: 0.98 / 0.97 / 0.96 at n = 4 and 0.98 / 0.97 / 0.95 extended.
  - 350k in-band: 0.99 / 0.98 / 0.95.
  - Above the band: 350k 0.61 → 0.71 at q 0.33 and 0.54 → 0.67 at q 0.5; 5M 0.26 → 0.34 and 0.26 → 0.29.
  - 350k at T 2.1, q 0.5: the set is 113 draws with recovery 0.48 (l. 1014).
- **§18b, two-mode table** (l. 609-615).
  - 5M median g: 0.99 / 0.96 / 0.85 / 0.26 / 0.26.
  - 350k median g: 1.00 / 0.99 / 0.95 / 0.61 / 0.53.
  - Mean-g columns from §18: 0.79 / 0.55 / 0.28 / 0.19 / 0.14 and 0.92 / 0.81 / 0.66 / 0.49 / 0.45.
  - Gaussian cost (l. 617-618): 0.77 → 0.66, 0.57 → 0.46; 0.89 → 0.84, 0.79 → 0.73.
  - All match.
- **§19c** (l. 570-573). 5M σ 1.0: 0.71 / 0.81 / 0.83. 350k: 0.86 / 0.94 / 0.92 at σ 1.0 and
  0.70 / 0.80 / 0.76 at σ 1.5. The §16 mean-g values in brackets also match. Match.
- **§19d** (l. 765-768). m = 11: T 4 (0.6), 5 (0.9), 6 (0.9). m = 37: T 12 at r 0.95 (0.9); at
  r 0.9 the T-15 count is 1.2; at r 0.7 it is 5.0. Match.
- **§15a** (l. 744-746). 1.65 / 2.40, 4.10 / 5.95, 8.55 / 12.40 pt at m 11; 2.50 / 3.55,
  6.25 / 8.85, 13.05 / above the grid edge at m 37. Match.
- **§18c** (l. 486-488). False flag 0.071; power 0.067 / 0.102 / 0.214 / 0.510 / 0.801 / 0.930. Match.
- **§17** (l. 664-666). 0.038 / 0.121 / 0.104; 0.312 / 0.738 / 0.948. Match.
- **`rank_sim.py` v6 block, m = 37** (fidelity table l. 601-603). Median / mean / LCB80:
  - σ 0.6, +1, ρ 0: 0.96 / 0.99 / 0.97.
  - σ 1.5, +1, ρ 0 and 0.5: 0.37 / 0.47 / 0.40 and 0.62 / 0.73 / 0.65.
  - σ 3.14: 0.13 / 0.16 / 0.14; 0.21 / 0.26 / 0.22; 0.63 / 0.74 / 0.66; 0.87 / 0.94 / 0.90.
  - Every cell matches.
- **`budget.py`**: (4, 4) 302 runs, 176,000 run-epochs, 318 certifications. Extension rows
  390 / 366 / 326. Packable today 240 runs, 142,000 run-epochs. Cheap version 129 runs, 79,500
  run-epochs. [DK18] 84 runs, 366.5 pod-hours. All match l. 857-867 and l. 1045-1047.
- **Own check 1, floor sensitivity** (for B2). This used a copy of `screen_null.py` whose only
  change is `T_FLOOR = float(os.environ["TF"])`, run with `--t-only` at the design seed. The
  median-g T at 350k, with the mean-g T in brackets, is:

  | floor | 350k T by median g (by mean g) |
  | --- | --- |
  | 0.005 | 2.0 (1.9) |
  | 0.01 | 2.1 (1.9) |
  | 0.02 | 2.2 (1.9) |
  | 0.05 | 2.3 (2.0) |

  The 5M median-g T is 1.2 at every floor.
- **Own check 2, rare high mode** (for C1). The per-run two-mode draw of §18 was extended to
  q > 0.5, with the same jump and within-mode sd and 20,000 draws per q, at seeds 20260927, 1 and 2.
  The code is short:
  ```
  lr=rng.random((reps,4))<q; lc=rng.random((reps,m,4))<q
  r=-5.4*lr+N(0,0.3); c=-5.4*lc+N(0,0.3)+eff; s_int as §18; g=c-r
  hit on np.median(g,2); recovery among draws with s_int <= T
  ```
  Results for 350k at T 2.1 (median g, conditional on s_int ≤ T):

  | q | P(s_int ≤ T) | recovery at the three seeds |
  | --- | --- | --- |
  | 0.6 | 0.011-0.012 | 0.53 / 0.53 / 0.51 |
  | 0.67 | 0.044 | 0.63 / 0.61 / 0.61 |
  | 0.75 | 0.18-0.19 | 0.77-0.81 |
  | 0.9 | 0.92 | 0.98 |

  For 5M at T 1.2, the set is empty up to q 0.8; at q 0.9 recovery is 1.00 on 1.3-1.6 % of draws.
  The median-g T survives a rare high mode.

## Findings

### Category A

None.

I checked specifically for:
- a dropped pre-registered rule, using the word-level diff v5 → fixer v5 and the line diff
  fixer v5 → HEAD (only replacements; no rule text removed);
- a number contradicted by its script (every quoted design value above reproduces);
- a [D] or [DK] label changed without a dated amendment ([DK6] l. 954-955 and [DK8] l. 956-957
  are both dated v6, 2026-09-28).

The nearest candidate to an A is B1 below. I explain there why it is B.

### Category B

**B1. The 2026-09-28 decision "Delta must not launch on the leaking anchor bundles" is not in the
STUDY's launch gates, packing or Reference table.**

The decision is `decisions.md` l. 16-18. It says:
- the chang0926 runner/trainer leaks host memory at about 80-95 MB per epoch per arm;
- Delta launches only on the *fixed* regime-B bundle, after a rebase;
- Delta's PREFLIGHT runs the anchor's memory-growth canary (fail above 5 MB per epoch) on E and
  A07 cells;
- `run_pack` patch 0038 is rebased onto the anchor's run_pack fix.

The STUDY does not reflect any of this:
- `grep -i "leak|memory-growth|memory growth|5 MB|heartbeat"` on STUDY.md hits nothing relevant.
- The launch-gate list claims completeness: "Nothing launches before all of these hold" (l. 407).
- Gate 7 (l. 432-441) checks GPU memory only, over epochs 1-3.
- PACK (l. 885) budgets "about 6 Gi host memory per arm".
- The Reference row (l. 272) calls the regime-A pilot "descriptive only" and does not say it was
  stopped (2026-09-28T05:31Z) because of the leak.
- The frontmatter `code_sha` (l. 9) names f2107a04 or e90327d4 as the code base.

*Impact.* The consequence below applies **if** the named regime-B bundles carry the same leak
(not established; see Disputed facts). At 6 Gi per arm and about 90 MB per epoch, an arm runs out
of host memory at about epoch 65-70. No H-500 cell, and no 1,000-2,000-epoch replica, would
finish. The anchor's pod stalled with the GPU at 0 % and no OOM kill
(`INCIDENT_stall_20260928.md` §2). That also blocks launch gate 1, the regime-B pilot's
epoch-500 readout. The Budget's wall clock, the packing and gate 7 all assume the fix.

*Why B and not A.* No sentence of the STUDY is false:
- `code_sha` says "not fixed … ml-engineer records the sha in PREFLIGHT.md";
- gate 11 requires a rebase before launch;
- the Reference rows are pinned to 96b95f2 / e620173;
- the decision's own **Check** line routes the constraint to PREFLIGHT, where the STUDY already
  delegates the sha.

So this is a missing disclosure in the launch contract, not a dropped rule or a contradicted
claim. That is the class Kai said is frozen and disclosed.

*Fix* (four lines, no design change):
1. Gate 7 or a new gate 14: "host-memory growth canary on E and A07 cells, fail above 5 MB per
   epoch per arm (`decisions.md` 2026-09-28, anchor incident); launch only on the leak-fixed
   regime-B bundle".
2. Gate 4: "run_pack patch 0038 rebased onto the anchor's run_pack fix (stale-heartbeat relaunch
   defect)".
3. Reference row l. 272: "stopped 2026-09-28T05:31Z, host-memory leak".
4. PACK l. 885: "6 Gi per arm presumes the leak fix".

**B2. At 350k the median-g label threshold T is set by the 0.01 probability floor, not by a
recovery crossing. Condition (ii) has no resolving power there.**

The facts:
- At the design seed, median-g recovery at q 0.5 conditional on s_int ≤ T is 0.45-0.50 at every
  T from 2.2 to 2.7 (§19a).
- At T 2.1 it is 0.48 on 113 draws, which is under the 200-draw floor and therefore not evaluated
  (§19b; [DK8] block l. 1014).
- So T = 2.1 is where P(s_int ≤ T | q = 0.5) crosses 0.01, not where recovery crosses 0.5.
- Own check 1 confirms this: the 350k median-g T moves 2.0 / 2.1 / 2.2 / 2.3 as the floor goes
  0.005 / 0.01 / 0.02 / 0.05. The mean-g T stays at 1.9 / 1.9 / 1.9 / 2.0.
- The ten-seed spread widens from 1.8-1.9 (mean g) to 2.1-2.7 (median g).
- The q 0.5 at which (ii) binds is the edge of the q grid.

The STUDY says "Those near-0.5 rows are why the 350k seeds spread 2.1-2.7; the ten-seed minimum
absorbs it" (l. 1015-1016). The minimum absorbs the seed noise but not the floor dependence. This
is the v5 B1 defect class (T set by an arbitrary constant or by Monte Carlo noise), now exposed by
the median switch.

*Provenance.* The floor is arbiter v5's own constant; Kai's median decision exposed it. This is
the case the v5 arbiter asked to weigh toward "freeze with residuals".

*Impact.* It affects the label only ("ranked" against "descriptive" for a 350k s_int in about
2.0-2.3 pt). No run and no cost depend on it.

*Why not A.* The rule is applied as written, and the number reproduces.

*Fix* (disclosure): one sentence in the [DK8] block:
> "at 350k, T by median g follows the floor (2.0 / 2.1 / 2.2 / 2.3 pt at floor 0.005 / 0.01 /
> 0.02 / 0.05, design seed; mean g 1.9-2.0); a 350k s_int between 2.0 and 2.3 pt is labelled
> 'ranked, near threshold'"

Alternatively, list "350k T 1.8-2.0 (mean-g or floor-0.005 value)" under ALTERNATIVES.

**B3. The primary statistic has no interval of its own.**

- The G3 report (l. 672-674) gives "median g and mean g; 95 % t-interval on mean g".
- The Ranking bullet (l. 704-709) puts the family-pooled interval on mean g.
- The figures row (l. 926) says "each bar's interval named" without saying which statistic the bar
  shows.

A reader of the K3a list sees median g, the ranking statistic, next to an interval computed for
a different statistic.

*Why not A.* Every cell still carries n_p, the per-seed g_s (forest-plot points) and an interval
from its per-seed values, and nothing is quotable. The convention's "gap with seeds and an
interval" is met by mean g.

*Fix.* Print the distribution-free order-statistic interval [min g_s, max g_s]. For n = 4 it
covers the population median with probability 1 − 2 · 0.5⁴ = 0.875. Label it "87.5 %, median".
Also state in the figures row that bars show median g with that interval and mean g with its t
interval.

**B4. Under median ranks, the 5M rank-move flag has a threshold only for r ≥ 0.95, and this new
consequence of the median switch is not shown to Kai as a cost.**

- §19d, m = 37, gives no grid T with a null count ≤ 1.0 for 0.9 ≤ r < 0.95 (1.2 at T 15).
- Under mean g the same band had T 15 (count 0.3; §15 l. 179-180 of the output).
- So a 5M family whose centred primary-companion r falls in 0.90-0.95 now goes to Kai labelled
  "companion disagrees at the null level" (l. 766-768), where v5 would have read it.
- Nothing bounds the likely r for best-feasible against last-epoch values.

The change log (l. 202-203) records the move. "Where I am not sure" (l. 999-1002) lists the
re-scored thresholds without this consequence, and Kai's decision entry quotes only the recovery
trade-off.

*Why not A.* It is disclosed in the change log. The rule is unchanged and applied as written.

*Fix* (one line in "Where I am not sure", with the alternative): run the rank-move flag on
mean-g ranks, the companion. Its thresholds exist: T 10 at r ≥ 0.95, T 15 at 0.9-0.95. The rest
of the primary stays on median g.

### Category C

- **C1.** The rare-high caveat is stale for the primary.
  - l. 618-620 says "q > 0.5 … not simulated; the physics review's variant gives lower recovery
    for it and T 1.4 / 1.4 pt under the v4 rule". That holds for mean g under the v4 rule.
  - Under median g, the floor rule and T 2.1 / 1.2, own check 2 finds conditional recovery
    0.51-0.63 at q 0.6-0.67 and 0.77-1.00 at q ≥ 0.75, at three seeds. The median-g T is
    unchanged by a rare high mode.
  - This is in the STUDY's favour. Replace the sentence with a script-backed line, or say "mean
    g, v4 rule" explicitly.
  - Near-miss: at q 0.6 the margin is 0.51-0.53 on sets of about 1 % of draws.
- **C2.** Two rationale sentences are stale now that the median is the primary.
  - Ranking l. 702-703: "one low-mode run in a cell or in the replica moves a 4-seed mean by
    1.35 pt and the median much less". A low-mode run in the *replica* shifts every cell's mean g
    equally, which leaves the rank unchanged. It perturbs median-g ranks, as the STUDY itself
    says at l. 573-575.
  - l. 626-628: "the replica's term … cancels from the order of the means" is true, but the
    ranking is now by median. The T derivation includes the replica, so no number is affected.
  - Fix: drop "or in the replica" and add "(for mean g; for median g the replica's per-run term
    enters the order, and §18b, §19 include it)".
- **C3.** l. 191-192 says "[350k T 2.1 pt by median g, next bullet]", but the median-g bullet is
  the fourth bullet on. Say "the 'Median-g re-simulation' bullet".
- **C4.** Arbiter v5 fix 5 asked for the pt clause in the Question. The Question (l. 240-241) now
  reads "it resolves only multi-pt effects, box". Acceptable. Optionally copy "(50 % power at
  1.65-6.25 pt, σ 0.6-1.5)" there, as in the Falsifier l. 801.
- **C5.** Kai's decision entry quotes 0.29 (mean, q 0.1, constructive stream); the STUDY and §18
  give 0.28. No action in the STUDY; note it for the record if the entry is ever cited.
- **C6.** Lines over 150 characters: l. 9, 680, 702, 725, 746, 761, 768. There is also a short
  orphan line at l. 304. Reflow.
- **C7.** The STUDY is 16,331 words (was 14,762 at v5). The v6 additions are proportionate, but
  the [DK8] block now carries three per-seed rows plus two paragraphs. A reader needs only the
  median-g row and the alternatives.

## Earlier findings, by name (arbiter v5 fix list 1-7)

| arbiter v5 fix | status | evidence |
| --- | --- | --- |
| 1 (A) confirm cap restored | **resolved** | Cap bullet l. 698-700 ("at most 12 confirm cells per confirm wave, taken in median-g order … nothing advances automatically into GPU time"); Falsifier l. 806; faithful to DELTA l. 858-860 with the order amended by [DK6]; stub carries it |
| 2 (B) T rule: floor + ten seeds + minimum; cascade | **resolved as specified**; residual → B2 | `screen_null.py` l. 115, 516-534; §18 per-seed table reproduced 40/40; Label l. 713-727; [DK8] block l. 1005-1021 with the grid-condition sentence l. 1017-1018; [DK8] line dated v6 l. 956-957; v5 change log annotated l. 159; `plan.md` l. 129, 155-156 tagged; stub Design line updated (T 1.2 / 2.1, mean-g 1.2 / 1.8). Band now 1.0-1.2 (5M) / 1.0-2.1 (350k), read generically at l. 560 |
| 3 (B) [DK16] above-band disclosure | **resolved** | Seeds l. 578-579 (median-g values, §19b); ALTERNATIVES l. 1030-1031 (326 runs, 1,188.1 / 2,034.9 pod-hours, matches `budget.py`) |
| 4 (B) median g companion | **superseded by Kai's decision** (median primary) and **resolved** | Ranking l. 701-712 cites `decisions.md` 2026-09-28 (Kai's Check line met); Kendall τ and the disagreement mark l. 711-712; readout l. 774; §18b print; box l. 225-228; the four mean-g design values re-simulated (§19, `rank_sim.py` v6). Residuals → B3, B4 |
| 5 (B) detectable effect in pt | **resolved** (C4) | §15a reproduced; box l. 230-232; Selection rule l. 744-746; Falsifier l. 801 |
| 6 (B) seed-shared clause | **resolved** | Box l. 223-225 ("because in that model the cell × seed interaction is the within-mode sd, 0.3 pt, by construction") |
| 7 (C) rows 8-21 | **resolved** | row 8 l. 623-625; row 9 l. 225-226; row 10 l. 213, 683-684; row 11 l. 526-527, 303, 388, 780; row 12 stub header l. 11 (no "350k feasibility"); row 14 l. 618-620 (now stale, C1); row 15 l. 718; row 16 l. 262-263; row 17 l. 926; row 18 l. 668; row 19 l. 687-689; row 20 l. 486-488 (0.071 from §18c, n_low rule not adopted, as allowed); row 21 l. 715 |

Critical v5 items by name: A1 = fix 1, resolved; B1 = fix 2, resolved, with B2 as the new
residual; B2 (grid disclosure) resolved at l. 1017-1018; B3 = fix 3, resolved; C1-C6 resolved
(C6 reflow: partial, see C6 above).

## Regression triggers (§6.7)

None met. No result exists. Selection is on validation only (l. 630, 789). The T change and the
median switch are labelling and ranking rules changed before any run, each with a dated
amendment. No ROC-test evaluation. No cross-N or cross-input comparison is treated as a series.
The placebo's bit-identical reading is pre-registered. No investigator ticket.

## Adversarial checks

- **"No rule changed"** (change log l. 199-200). The rules' text is unchanged. Their outcomes
  moved:
  - 350k T 1.8 → 2.1 is looser;
  - the 5M rank-move band 0.9-0.95 went from "read" to "to Kai" (B4).
  "No rule changed" is literally true, but it undersells both moves.
- **"The ten-seed minimum absorbs it."** It absorbs seed noise, not dependence on the floor
  constant (B2).
- **Circular selection:** none. T comes from simulation only. The extension selects on seeds 1-4
  and prints the seeds-5-8 mean as its selection-free estimate (l. 565-566).
- **Tautological validation:** none. The re-simulation reuses draws (no new random numbers), and
  that is what makes the first 401 output lines byte-identical to v5. Its median-g rows are scored
  independently of the mean-g rows on the same draws, so their agreement is not assumed.
- **Motivated framing of Kai's decision:** the STUDY shows the Gaussian cost of the median
  (l. 617-618) and the §16 optimism for the median (l. 573-575). Both run against the choice, and
  both are stated.

## Competing-group question

A group publishing this screen next month would have:
1. A launch gate that names the known host-memory leak and its canary (B1).
2. A 350k label threshold that does not move with an arbitrary floor constant, or a stated band
   around it (B2).
3. An interval on the ranking statistic itself (B3).
4. A rank-move flag that is readable at the r a real companion is likely to show (B4).

All four are text or a one-line rule choice, with no GPU. None changes what trains.

## Disputed facts for the investigator

1. **Do the regime-B bundles f2107a04 and e90327d4 carry the chang0926 host-memory leak
   (80-95 MB per epoch per arm)?** The incident traced it on 77f1ca4e.
   - Paths: `campaigns/2026-09-26-training-batch/review/INCIDENT_stall_20260928.md` §1-§2;
     `campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz` (sha e90327d4);
     `.claude/memory/decisions.md` l. 16-18, 28, 80; `.claude/memory/cluster-inventory.md`
     2026-09-28.
   - If they do, B1's arithmetic applies: at 6 Gi per arm, about 65-70 epochs before the pod
     stalls. The STUDY's named code base then cannot complete any run until the fix lands.

## Dismissals

None.
