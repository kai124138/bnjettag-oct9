# STUDY review, constructive, v2: 2026-09-27-delta-screen (Delta wave 2)

Reviewer: constructive-reviewer, fresh context, 2026-09-27. Artifact: `STUDY.md` (1,026 lines,
iteration 2, after fixer v1). Read: `docs/methodology/06-review.md`, `03-phases.md` Phase 1,
`docs/conventions/jet-tagging-metrics.md` (seeds and intervals), the campaign's `plan.md`,
`budget.py`, `rank_sim.py`, `screen_null.py`, `review/STUDY_validators_v2.txt`, my own
`review/STUDY_constructive_v1.md` and `review/STUDY_fixer_v1.md` (the response to it). Not read: the
arbiter, critical or physics files of either iteration. Also read: the anchor STUDY at dde5ca7,
l. 344-366; `delta.json` entry M001 (structure of `prediction`); the experiment log (newest entries,
plus a grep for seed correlation); the research log (grep for screening and seed-variance prior art:
nothing found); the anchor runner `campaigns/2026-09-26-training-batch/code/tree/bnhgq2/ablation.py`
and `train.py` (determinism calls).

Scripts. Everything below is design arithmetic from seeded Monte Carlo, not a result. The new scripts
are copied into `review/` so they can be rerun:
- `python3 budget.py` reproduces every Budget row (302 runs, 176,000 run-epochs, 1,776.3 / 3,128.7
  pod-hours, 8.6 / 14.7 d at (4, 4); cheap 129 runs, 79,500, 4.6 / 7.4 d). ✓
- `python3 screen_null.py` reproduces the quoted numbers: critical t 2.410 (m 12, n 4) and 2.793
  (m 40, n 4); P(no | null) 0.896-0.904; P(no | one +1-pt cell) 0.489 / 0.846 / 0.880 at σ 0.6 /
  1.5 / 3.14 (m 12); placebo false-flag rate 0.034 / 0.013; ceilings 1.3 and 2.7 pt. ✓
- `budget.py` with K_E = 4 (the value the STUDY itself expects on an A10, l. 729-731) in place of 5:
  run-epochs and pod-hours unchanged, wall clock unchanged (8.6 / 14.7 d, A07-bound), replica gate
  20.2 h instead of 25.2 h at r = 1.
- `review/constructive_v2_hetero.py`: calibration of the STUDY's pooled max-t when cells differ in
  gap sd, and when the placebo is more tightly coupled to the replica than cells are.
- `review/constructive_v2_mixture.py`: the same under a two-mode seed outcome.
- `review/constructive_v2_boot.py`: a critical value resampled from 8 replica values, as a fix.
- `review/constructive_v2_percell.py`: max-t on each cell's own sd, as the alternative fix.
- `review/constructive_v2_unpaired.py`: the paired control against an unpaired control built from
  the mean of 8 replica seeds, as a function of seed coupling ρ.

## What is done well

- [+] **Every DELTA departure is now dated and listed with its reason** (change log l. 25-56), and
  each is marked where it applies. v1's claim "nothing loosened" is withdrawn in plain words. This
  was v1's largest honesty gap, and it is closed.
- [+] **The expected-mode "no" can now fire.** The Dunnett-type max-t with a simulated critical
  value replaces the LCB80 count (which fired under the null with probability 0.73-0.84). The
  arbiter's placebo-beats-cells wording is rejected with a number (P(no | null) = 1/(m + 1)) and not
  just an argument. The power of the "no" is stated next to it (l. 72-73, 636-638), so a reader is
  not led to treat a "no" as absence.
- [+] **The "can and cannot say" box (l. 62-73)** carries the sentence a reader who stops early
  needs: no quotable number, ±7.1 pt at the archived spread, recovery 0.10-0.20 against 0.018 by
  chance. That is the honest summary.
- [+] **The winner's-curse handling is concrete.** A non-selecting companion (last feasible epoch
  ≤ H, which is the end of the cosine cycle), the eligible-epoch count, Kendall τ and a rank-move
  flag. [L6] names the levers where the bias does not cancel.
- [+] **Missing pairs have a rule** (n_p printed, incomplete-pairs list, survivors labelled as an
  upper estimate, imputation beside them).
- [+] **The floor-family package list is separated from the paired list**, with its Welch SE
  penalty stated (l. 584-590), and a rescue with large static headroom is labelled "structural, by
  construction".
- [+] **The [L1] attempt (seed-rank persistence of rep-A and rep-C across horizons) costs no GPU**
  and uses runs that are already paid for.
- [+] **Kept from v1:** certification before reading; BH m fixed with p = 1 for unrun cells; the
  ROC-test set never touched; selection matches the runner (`ablation.py:664, 683-685`); the budget
  script reproduces every row.

## Category A

### A1. The family-level "above the replica" test is calibrated only under a model the STUDY's own text contradicts, and the check offered for calibration cannot detect the failure

- **Current.** Null (l. 91-92): "P(no | global null) = 0.90 per family by construction". The
  critical value comes from `screen_null.py`, which draws every run from one Gaussian with a common
  σ. The pooled sd is pooled over all cells and the placebo (l. 576-577). Falsifier (iv)
  (l. 654-659) presents the placebo |t| check as the validity check: "null not calibrated" if it
  fires.
- **Problem.** The pooled max-t keeps its α only if every cell's gap has the same sd and the seed
  outcome is roughly Gaussian. The STUDY itself says the first condition fails: [L6] (l. 886-892)
  names M018-M020, M028, M029, M032, M034, M008 and M011-M013 as levers whose epoch-to-epoch
  fluctuation differs from the replica's. That is heteroscedasticity by the STUDY's own account.
  Rerunning the STUDY's own `tstats` (constructive_v2_hetero.py, n = 4, 20,000 reps):

  | truth under the null | FWER m = 12 | FWER m = 40 | placebo flag m = 12 / 40 |
  | --- | ---: | ---: | --- |
  | homogeneous (the STUDY's model) | 0.103 | 0.104 | 0.032 / 0.014 |
  | one cell at 3× sd | 0.156 | 0.159 | 0.016 / 0.010 |
  | 25 % of cells at 2× sd | 0.147 | 0.195 | 0.013 / 0.004 |
  | 25 % of cells at 3× sd | 0.209 | 0.333 | 0.004 / 0.0004 |

  Two-mode seed outcomes do the same (constructive_v2_mixture.py). The model is: each run lands in an
  upper mode with probability q, +5.4 pt, plus a Gaussian with sd 0.3 pt. It is shaped on the only
  same-N seeds in the record: archived N=64 W1A8, 67.18 / 72.64 / 67.21 %, anchor STUDY l. 350,
  archived recipe, 3 seeds. Whether [D19] behaves this way is what rep seeds 1-8 will show. Under
  that model FWER is 0.35 / 0.17 / 0.08 at q = 0.1 / 0.33 / 0.5 for m = 12, and 0.54 / 0.20 / 0.06
  for m = 40.
  In every row the placebo check fires at 0.03-0.045 or less. It gets *less* sensitive as the
  miscalibration grows, because inflated cells inflate s_pool for the placebo. So the stated
  error rate of the expected mode's headline answer is not supported. The check the design offers
  cannot see that failure. A "cell above the replica at family-wise α 0.10" could be a
  high-variance lever that had one lucky seed. In this screen the high-variance levers (STE, Bop,
  LR) are the ones most likely to show up.
  The same Gaussian assumption sits under the sd_rep ceiling (l. 484-491). Under the two-mode
  model, a cell that only doubles the escape probability (q 0.33 → 0.66, +1.8 pt in mean) ranks
  first in only 0.41 (m = 12) and 0.22 (m = 40) of families.
- **Improved.** Three steps, all before launch.
  1. Add heteroscedastic and two-mode rows to `screen_null.py` and print the FWER beside the
     Gaussian one.
  2. Pre-register a shape read on the 8 replica values at the epoch-500 gate, which is read anyway
     before any cell starts. Use a gap rule, for example the largest gap between sorted values
     above k · sd_rep with k fixed now, or a split by the anchor's collapse label.
     - If the shape read passes, the Gaussian critical value stands.
     - If it fails, the critical value is resampled from the 8 replica values
       (constructive_v2_boot.py), and the family's "above the replica" is labelled "calibration
       partial". The recovery is partial and should be said so: FWER 0.20 → 0.14 at q = 0.33 and
       0.54 → 0.28 at q = 0.1 (m = 40), because 8 seeds often miss a rare mode.
  3. Report, per named cell, its own paired sd beside s_pool, and flag any cell whose own sd
     exceeds s_pool by more than a pre-registered factor.

  Switching outright to each cell's own sd is calibrated (FWER 0.10-0.11 with 25 % of cells at 3×
  sd) but costs most of the power at n = 4 (P(true +1-pt cell named) 0.50 → 0.19 at σ 0.6, m = 12;
  constructive_v2_percell.py). So the flag plus the shape read is the better trade.
  Delete "by construction" at l. 92. The many-cells, few-replicates setting has a standard
  shrinkage-variance answer in the statistics literature (variance moderated toward the pooled
  value). Ask physics-researcher for a research-log entry; this review cites nothing from memory.
- **Why A.** The expected mode's only inferential statement carries an error rate that the design's
  own named levers break by 1.5-3×. The validity check offered for it is blind to exactly this.
  That is a genuine error in a stated falsifier's calibration, not a presentation issue.
- **Effort.** Low (an hour: script rows, one gate rule, one label).

## Category B

### B1. The pairing's efficiency is assumed, and the 8 replica seeds, already paid for, serve only sd_rep

- **Current.** Every G3 statistic is paired against the same-seed replica. sd_plan = √2 · sd_rep
  assumes ρ = 0 (l. 398). rep-A and rep-C run seeds 1-8 ([DK2]), but seeds above n enter only the
  sd read.
- **Problem.** Pairing helps only if a cell and its replica at the same seed stay correlated after
  500 epochs of a chaotic, PID-driven trajectory. The only record is a hint in the other direction:
  "pairing by seed is measured NOT to help", with n8 cross-arm correlations −0.34 / −0.79 / −0.56
  (`.claude/memory/experiment-log.md` l. 2277-2278; 3 seeds, archived, too few points to be more
  than a hint). constructive_v2_unpaired.py compares the paired Dunnett with an unpaired Dunnett
  against the mean of the 8 replica seeds (m = 12, one +1-pt cell, σ 0.6):

  | ρ | power, paired | power, unpaired against 8 seeds |
  | ---: | ---: | ---: |
  | 0 | 0.50 | 0.64 |
  | −0.5 | 0.38 | 0.63 |
  | 0.7 | 0.95 | 0.69 |

  At ρ ≈ 0.3 the two are level; at m = 40 the pattern is the same. At ρ < 0 the unpaired version's
  FWER rises to about 0.13, so neither is safe everywhere.
- **Improved.** Keep paired as the primary; the convention (`jet-tagging-metrics.md` l. 43) asks for
  it. Pre-register the unpaired-against-8-seed Dunnett as a non-selecting companion, like the
  companion readout. Report the family-pooled cell-replica correlation ρ̂ with its null interval.
  At confirm (wave 4), ρ̂ decides whether pairing by seed is worth its constraints (same GPU
  product, never in the replica's pod). The companion never changes the primary list.
- **Effort.** Low.

### B2. The placebo's role rests on unmeasured GPU run-to-run nondeterminism

- **Current.** P-350 / P-5M are the base config plus a no-op key, at the replica's seed
  (l. 142-150). The STUDY says the placebo's rank is "uniform under the null" (l. 147, 662). It also
  says an exactly zero per-seed placebo gap "would mean the runs did not vary and is a red flag"
  (l. 525-526, 662-663).
- **Problem.** The runner sets only `keras.utils.set_random_seed(seed)`
  (`campaigns/2026-09-26-training-batch/code/tree/bnhgq2/ablation.py:595`; `train.py:261`). There is
  no `enable_op_determinism`. Z13 byte-identity was measured on CPU with `TF_DETERMINISTIC_OPS=1`
  (`.claude/memory/decisions.md` l. 233). Whether two GPU runs of an identical config at one seed
  diverge, and by how much after 500 epochs, is not measured. If they stay close, the placebo is
  more tightly coupled to the replica than any cell with a real delta. Then:
  - its rank is not uniform. It sits near g = 0: in constructive_v2_hetero.py, a placebo with gap
    sd 0.2× lands in the top quartile about one third as often as an exchangeable one at m = 12
    (0.098 against 0.303) and a tenth as often at m = 40 (0.015 against 0.271);
  - its flag never fires (0.005 / 0.0015);
  - its near-zero residuals pull s_pool down slightly.

  If the runs are bit-identical, the zero gap is the expected behaviour of a deterministic pipeline,
  not a red flag.
- **Improved.** Add one item to the launch-gate-7 canary: the same E config and seed twice on one
  GPU product for 3 epochs; compare the weight hashes and the per-epoch losses. Pre-register both
  outcomes:
  - If the runs are bit-identical or nearly so, the placebo is read as a pod, pack and identity
    check only. Its rank claim is dropped, and it is excluded from s_pool. Optionally, a seed-offset
    placebo (seeds 101-10n, unpaired) stands in as the null draw.
  - If they diverge, the current text stands, with the measured divergence printed.

  Exclude the placebo from s_pool in either case. It is a check, and it should not feed the
  statistic it checks.
- **Effort.** Low (a few minutes of canary GPU time, already scheduled pods).

## Category C

- **C1. Resolving power, both directions (l. 495-500).** The anchor STUDY brackets the N=64 spread
  between a weak lower bound (N=8 W1A8, 8 seeds, held-out sd 0.19 pt; anchor l. 353-360) and the
  archived 3.14 pt. This STUDY quotes only the upper end. Adding the lower bound does not change the
  expected mode: 0.19 is still above the n = 8 threshold of 0.134 pt. It does show that the 0.6-pt
  fidelity row is plausible and not optimistic. It also records that the 3.14-pt seeds are two-mode
  (A1), which is the more useful fact for this design. Effort: low.
- **C2. The family test's power at the ceiling.** At σ 1.5 the Dunnett's power for one +1-pt cell
  is 0.099 at m = 12 and 0.051 at m = 40 (`screen_null.py`), which equals α. The ceiling (1.3 pt)
  was set on ranking recovery, not on test power, so a family can launch where the family test says
  nothing. One sentence in the box: "above about σ 1 pt the family test is at chance for +1-pt
  effects; the ranking is the only output". Effort: low.
- **C3. "Cannot call a gap flat" (l. 67, 527) is an undeclared deviation** from
  `jet-tagging-metrics.md` l. 44-45 ("A gap whose interval covers zero is flat"). The STUDY's
  position is the honest one at ±1.35-7.1 pt. Add it to the conventions table as a deviation with
  that reason, so a later phase does not "fix" it. Effort: low.
- **C4. Companion readout.** The last feasible epoch is one checkpoint. The mean validation accuracy
  over the last k feasible epochs of the cycle (k fixed now, for example 25) is equally non-selecting
  and less noisy. It is read from the same per-epoch logs. Effort: low.
- **C5. The +1-pt effect size is an assumption.** `delta.json` predictions are qualitative
  (M001: "accuracy at 5M flat to slightly down"). Say in the Seeds section that +1 and +3 pt are
  illustrations with no prior, so the fidelity table is not read as the expected yield. Effort: low.
- **C6. Significance mode is dead text at the stated thresholds.** It needs sd_rep ≤ 0.044-0.134 pt,
  against a 0.19-3.14 pt bracket. Compress it to one paragraph that keeps the rule (DELTA
  requires it) and the thresholds. About 60 lines of BH and g0 machinery then stop competing with
  the mode that will run. Effort: low.
- **C7. Packing.** K_E = 4 (the STUDY's own expectation on 23-24 GB cards) leaves wall clock and
  pod-hours unchanged and moves the replica gate from 25.2 h to 20.2 h (`budget.py` with K_E = 4).
  Say so in [DK11], so the canary's likely answer is not read as a budget change. Effort: low.

## Answers to 06-review §6.3

1. **Conventions.** Implemented or justified, except that "cannot call a gap flat" is an undeclared
   deviation (C3).
2. **Reference table.** Present, sourced, and correctly without a comparand.
3. **What a competing group would have.** A family test calibrated under unequal variances and
   two-mode seeds (A1); a measured seed coupling before pairing is relied on (B1); a determinism
   check before an A/A cell is interpreted (B2).
4. **Honest uncertainties and resolving power.** Ranking fidelity is stated honestly. The family
   test's error rate is overstated as exact (A1), and its power at the ceiling is not stated (C2).
5. **Limitations with attempts.** [L1] and [L6] now have attempts. [L6]'s own list is what breaks
   A1's calibration, so the attempt should reach the test as well.
6. **Context.** Not applicable at STUDY.

## Summary for the arbiter

Keep the dated amendment list, the placebo and Dunnett machinery, the companion readout, the box
and the budget. v1's A1 is resolved: the "no" can now fire. The new A1 is narrower and cheap to fix.
The 0.90 is a Gaussian, equal-variance number. The levers the STUDY itself names in [L6] break it
to 0.15-0.33, two-mode seeds break it to as much as 0.54, and the placebo check cannot see either.
A shape read on the 8 replica values, which is already scheduled, plus a per-cell sd flag closes
most of it. B1 and B2 each cost under an hour and one canary item, and they tell wave 4 whether
pairing by seed and A/A placebos are worth carrying forward.
