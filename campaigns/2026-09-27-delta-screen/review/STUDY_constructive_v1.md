# STUDY review, constructive, v1: 2026-09-27-delta-screen (Delta wave 2)

Reviewer: constructive-reviewer (fresh context). Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md`
(647 lines, iteration 1). I read `docs/methodology/06-review.md` and `03-phases.md`,
`docs/conventions/jet-tagging-metrics.md` and `quantization-and-cost.md`, the campaign's `plan.md`,
`budget.py` and `review/STUDY_validators_v1.txt`, DELTA.md §5.1 and §5.3 (l. 686-735, 826-871), the
newest experiment-log entries and the research log. I did not read any other reviewer's output.

Scripts I ran (design arithmetic only, nothing quotable). The two simulation scripts are copied into
`review/` so the results can be reproduced:
- `python3 campaigns/2026-09-27-delta-screen/budget.py` reproduces every Budget row (l. 435-440,
  462-467): (4, 4) gives 286 runs, 168,000 run-epochs and 1,695.6 / 3,007.6 pod-hours at 8.8 / 15.1 d.
  The cheap version gives 70,500 run-epochs and 711.5 / 1,211.1 pod-hours. ✓
- `python3 campaigns/2026-09-26-delta/screen_power.py` gives W2 350k k_joint 3.66 / 2.09 / 1.58 and
  W2 5M m 43, α_eff 0.00233, matching l. 330-336 ✓. I checked the ceilings by hand:
  0.3 / (3.66·√2) = 0.058, 0.3 / (2.09·√2) = 0.102, 0.3 / (1.58·√2) = 0.134 ✓.
- `review/rank_sim.py` (seeded MC, 4,000-20,000 reps): the ranking-mode null behaviour and the
  recovery of true effects at n = 4. It also prints t(0.975, 3)/2 = 1.5912, which checks the
  1.59 · sd_d half-width at l. 350 ✓.
- `review/two_stage.py`: a one-stage design against a two-stage design at equal run count (C6).

## What is done well

- [+] **Counts reconcile.** 350k: 12 accuracy + 1 baseline (M050) + 3 probes + 7 floor-family = 23
  (l. 153). m = 19 = 12 + 7, and m = 43 = 40 G3 cells + the 3 deferred teacher cells. `budget.py` gives
  the same 68 cells (23 / 1 / 44), with 16 E-class cells.
- [+] **Selection is pre-registered, runs on validation only, and matches the code.** l. 355-403: the
  runner's rule is cited to `ablation.py:664, 683-685`. The DELTA wording difference is written down
  as a dated clarification ([D10]) and not left silent. The ROC-test set is never touched (l. 395).
- [+] **Certification comes before any number is read** ([D11]). A mismatch is a defect, never a
  reason to reselect (l. 371-375).
- [+] **BH m is fixed, and unrun cells enter with p = 1** ([D9]). This tightens the design and closes
  the "drop the losers to shrink m" path.
- [+] **Both K2 branches are written before launch, and the guard can only move toward ranking**
  (l. 324-342). The STUDY states plainly that ranking mode is expected (l. 344). That is the honest
  default.
- [+] **Matched-arm discipline.** Launch gate 8 is the diagnostics-on invariance check. Z13 checks
  byte-identity. PREFLIGHT prints the key diff of every cell against its replica (l. 72-76).
  GPU product is held per pair ([D17]). The labels "crosses N" and "crosses input set" are in place.
- [+] **Every limitation and projection is labelled.** A07 timing is labelled "illustration, not
  measurement" (l. 449-452). The anchor's 112.6 s prior is rejected with a reason. Certification cost
  is stated as outside the table.
- [+] **The floor family has its own endpoint** (k_e ≥ 3 and k_e − k_base ≥ 2, with a descriptive
  McNemar test) instead of being forced into the accuracy family.

## Category A

### A1. The ranking-mode "no" answer cannot fire under the null, so it is not a falsifier
- **Current (l. 32-34, 409-412).** "Ranking mode: no cell's lower 80 % bound on g is above 0 in
  either family" is the wave's "no". Ranking mode is the expected mode (l. 344).
- **Problem.** A one-sided 80 % lower bound excludes 0 with probability 0.20 per null cell. With
  independent cells, P(at least one LCB80 > 0 | global null) is 1 − 0.8^19 = 0.986 at 350k and
  1 − 0.8^43 = 0.9999 at 5M (`rank_sim.py`). With the shared replica (the same rep-A or rep-C at
  seed s is subtracted from every cell), the simulated values are 0.73 (m = 19) and 0.84 (m = 43),
  with a mean of 3.8 and 8.5 null cells above 0. The "no" answer therefore almost never fires when
  nothing works. The expected mode has no falsifier, and the headline sentence "k cells have a
  positive lower bound" is what pure noise produces. This fits two escalation criteria: a genuine
  error (the stated falsifier for the expected mode cannot fire), and a comparison that is
  uninformative by construction presented as evidence.
- **Improved.** Pre-register a family-level null reference for ranking mode, for example: the
  number of cells with LCB80 > 0 compared with its null distribution, simulated with the
  shared-replica correlation and the family's own measured sd_rep. `rank_sim.py` is that simulation
  in 40 lines. The plain Bin(m, 0.2) 95th percentiles (7 at m = 19, 13 at m = 43) are the wrong
  reference, because the common replica term widens the null distribution. Alternatively, state that
  ranking mode has no family-level falsifier and delete the "no" sentence for that mode. Either is
  honest; the current sentence is not.
- **Effort.** Low (under an hour: one paragraph plus the simulation script moved into the campaign).

## Category B

### B1. The ranking inherits the anchor's survivor-pair rule without the anchor's k guard (survivorship bias)
- **Current.** The screen inherits "no accuracy number" from the anchor (l. 366-370). The anchor
  rule at HEAD dde5ca7 (checked with `git show dde5ca7:campaigns/2026-09-26-training-batch/STUDY.md`,
  l. 818-825) says:
  - "Paired gaps use seeds that are feasible and not diverged in **both** arms".
  - The arm mean "carries a survivor bias ... an upper estimate of the arm".
  - "A claim needs k ≥ 6" of 8.

  The screen takes the survivor-pair rule but states no k guard. Nothing in the STUDY or in DELTA
  (grep for surviving / missing / k < n) says how a cell with k < n pairs enters the ranking. DELTA
  l. 858-859 makes the ranked list *the* mechanism for selecting confirm cells.
- **Problem.** Under the inherited rule, a destabilizing lever (Bop M020, EDE M019, LR M028/M029,
  M032) that loses 2 of 4 seeds is ranked on its 2 surviving pairs, which are plausibly its best.
  The anchor acknowledges this bias for an arm mean and fences it with k ≥ 6. The screen has no such
  fence, and its ranking selects the cells that go to confirm. This is a selection rule, so I place
  it on the A/B line. I keep it at B only because the fix is mechanical and nothing has run yet. The
  arbiter may raise it.
- **Improved.** Before launch, state one rule. Either rank only cells with k = n (or k ≥ n − 1) and
  list the rest separately with their G1/G2 counts, or rank all cells with each missing seed imputed
  at a stated value (for example threshold (c), 0.21096, or the family's worst replica seed). Say
  which in [D10].
- **Effort.** Low.

### B2. The resolving-power paragraph omits the only measured spread
- **Current (l. 349-353).** Half-widths are quoted at sd_d = 0.3 pt (±0.48) and 0.85 pt (±1.35).
  The reference table's only measured spread is 3.14 pt (l. 55), and the paragraph does not use it.
- **Improved.** Add the row sd_d = √2 · 3.14 = 4.44 pt, which gives a half-width of 1.591 × 4.44 ≈
  ±7.1 pt, labelled "archived, sizing only". Next to it, give what the ranking can recover
  (`rank_sim.py`, 43 cells, n = 4, three true effects, P(all three in the top 12)):
  - At σ = 0.6 pt, +1 pt effects are recovered with probability 0.97-1.00.
  - At σ = 1.5 pt, the probability is 0.35-0.67.
  - At σ = 3.14 pt, it is 0.10-0.20, against 0.018 by chance, C(12,3)/C(43,3) = 220/12,341. At that spread only +3 pt effects
    are reliably found (0.60-0.92).

  This tells Kai what 1,700-3,000 pod-hours buy under each spread. At present the paragraph shows
  only the optimistic cases.
- **Effort.** Low.

### B3. Use the replica read as a go/no-go gate, not only a mode switch
- **Current (l. 269-274, 341-342).** The replicas run first (about 30 h), and sd_rep can only move a
  family into ranking mode. The family is expected to be in ranking mode already, so under the
  expected branch the gate changes nothing.
- **Improved.** Pre-register an sd_rep ceiling per family (for example the σ at which B2's recovery
  probability for a +1 pt effect falls below 0.5, about 1.5-2 pt). Above it, the family pauses and
  goes to Kai with three options: cut m (DELTA l. 723-725 already allows this), raise n, or run the
  cheap version. Pods for cells are not requested before the release (l. 459-460), so the gate costs
  nothing extra and can save up to about 1,300-2,600 A07 pod-hours on a ranking that is close to
  chance.
- **Effort.** Low.

### B4. Rank on mean g, not on the per-cell lower bound. Say that the replica does not set the order.
- **Current.** Cells are ranked by LCB80 = ḡ − t(0.80, 3) · s_d/2 (l. 384-385; DELTA §5.3).
- **Problem.** With 3 df, the per-cell s_d is itself very noisy, so the ranking rewards cells whose
  4 pairs happen to agree. In every row of `rank_sim.py`, ranking by mean g matched or beat ranking by
  LCB80. For example, at σ = 1.5, ρ = 0.5 and +1 pt, recovery is 0.67 against 0.59; at σ = 3.14,
  ρ = 0 and +3 pt, it is 0.68 against 0.60. The replica term (rep_s) is common to every cell of a
  family at seed s, so it cancels from the order of the means. The replica sets the zero line and the
  interval, not the ranking.
- **Improved.** Rank by ḡ. Carry an interval that uses a family-pooled paired sd (df ≈ 3m) and keep
  per-cell LCB80 as a descriptive column. This amends DELTA §5.3's rule, so it needs a dated
  amendment before launch. Also state in one line that the ranking's resolution is set by the cell
  seed count n and σ only.
- **Effort.** Low (text plus a dated DELTA amendment).

### B5. Give the 5M family, and branch S, a real sd input: replica seeds to 8 at epoch 500
- **Current.** The 5M rule "has no input" (l. 335-337), so the family runs 43 cells, 77 % of the
  run-epochs (130,000 of 168,000 A07-class), at n = 4 by default. Branch S uses a 2-seed sd with
  df 1 ([L3]). The Kai row (l. 604-606) rejects "set n_5M from rep-C's sd" as conflicting with
  "replicas first".
- **Improved.** Launch rep-A and rep-C at seeds 1-8 at t = 0 with the other replicas. The extra seeds
  only need to reach epoch 500, unless n rises and cells at seeds 5-8 need them longer. The cost is
  4 × 500 E + 4 × 500 A07 = 4,000 run-epochs, which is 40-61 pod-hours at the l. 446-452 basis
  (2.4 % / 2.0 % of the (4, 4) total at r = 1 / 2). Wall clock does not change, because the extra
  seeds run in parallel inside the 30 h replica window. Replica seeds do not conflict with "replicas
  first". The benefit is a df-7 sd in both families, instead of df 1 at 350k and nothing at 5M, and
  the §5.1 rule then has an input everywhere. This changes the guard ("never raises n") and the
  branch structure, so it goes to Kai as a K2 option, but it should be offered.
- **Effort.** Low to design; the run cost is given above.

### B6. The argument at l. 344-346 is wrong, although its conclusion holds
- **Current.** "n_350 = 8 needs sd_A500 ≤ 0.134 pt, below the 0.16-pt binomial SE of a single
  checkpoint's validation accuracy; a seed sd that small is not expected."
- **Problem.** Every seed is scored on the same 62,000 validation jets. The binomial SE describes
  resampling that set, which is shared across seeds, so it is not a lower bound on seed-to-seed sd.
  DELTA l. 833-835 calls the same 0.16 pt "an upper bound on the SE of a paired difference on the
  same jets", which is the opposite framing. The expectation of ranking mode rests on the archived
  3.14 pt spread and the anchor's 0.6 pt referral line, not on the binomial SE.
- **Improved.** Replace the reason with the 3.14 pt and 0.6 pt arguments already in the file.
- **Effort.** Low.

### B7. [L6] does not hold for exactly the levers that change curve noise or the number of minima
- **Current.** [L6]: "the maximum over up to H checkpoints is biased upward; both arms of a pair
  share it."
- **Problem.** The bias of a best-of-H maximum grows with the epoch-to-epoch fluctuation of
  validation accuracy and with the number of eligible checkpoints. Several levers change exactly
  those:
  - M034 (EMA of latents, smoother) and M028/M029 (lower peak LR) reduce the fluctuation.
  - M032 has one cosine minimum where the replica has four in 2,000 epochs.
  - M013 and M008 change when checkpoints become feasible.

  For these cells the winner's curse does not cancel in the pair, and it enters g with a sign fixed
  by the lever. It is plausibly of the order of the 0.3 pt target (this is a qualitative mechanism,
  not measured here).
- **Improved.** Pre-register a secondary readout that does not select, for example validation
  accuracy at the last feasible epoch at or before H (the end of the cosine cycle for H = 500), or the
  mean over the last 10 feasible epochs, both read from the per-epoch logs. Report the rank
  concordance (Kendall τ) between the primary and secondary rankings per family, and flag cells whose
  rank moves by more than a stated amount.
- **Effort.** Low (the per-epoch logs are already written).

### B8. [L1] is accepted with no attempt to test it
- **Current.** "One cosine cycle may not predict the 7,000-epoch outcome" (l. 571-572). Under
  06-review §6.3 Q5, a limitation accepted without an attempt is B.
- **Improved.** Two zero-GPU checks can be pre-registered now:
  1. When anchor production has [A6] snapshots, the rank correlation of epoch-500 against
     epoch-7,000 validation accuracy across the anchor's arms and seeds (A, B, D, F, R, C, A07-350,
     and the second wave).
  2. Within this campaign, seed-rank persistence of rep-A (500 → 1,000) and rep-C
     (500 → 1,000 → 2,000).

  Neither changes what trains. Both say whether a 500-epoch ranking carries information about the
  long run.
- **Effort.** Low.

### B9. Per-cell "prediction contradicted" in ranking mode carries no false-positive count
- **Current (l. 413-418).** A 95 % interval entirely below 0 gives "contradicted at screen". There is
  no multiplicity control in ranking mode.
- **Improved.** State the expected number of false contradictions under the null: 0.025 · m, which
  is 0.5 at 350k and 1.1 at 5M (`rank_sim.py`). Label the list with it, or apply the same BH as in
  significance mode.
- **Effort.** Low.

## Category C

- **C1. Question framing (l. 6, 22-29).** The question leads with "by at least g0 = 0.3 pt", but the
  advance test is BH p ≤ 0.10 with mean g ≥ 0.15 pt (l. 383-384), and the expected mode is a
  ranking. Suggested wording: "Expected mode: a declared ranking of W2 single cells by paired
  validation-accuracy gap at H (n = 4); if the seed rule qualifies, a test at MDE target g0 = 0.3 pt
  with advance threshold g0/2." Effort: low.
- **C2. Full against cheap (l. 584-588).** For Kai, frame the choice as coverage (T2 entries,
  baselines, 5M cells of two-target entries, long replicas), not resolution. Going from n = 3 to
  n = 4 changes the SE of a cell mean by √(4/3) = 1.15, and both designs are rankings. Effort: low.
- **C3. Control branching (l. 235-257).** The expected branch is replica-primary in every family
  (l. 254-257). The STUDY already lists "always replica-primary" as an alternative. Adopting it
  removes a read-time branch and the anchor-primary half of launch gate 8. g_rep can stay as a
  descriptive transfer check. Effort: low.
- **C4. Recoverable information.** Two cheap internal checks are available.
  - About 15 entries run at both 350k (on E) and 5M (on C): M008, M011, M012, M015, M016,
    M038-M040, M042, M043, M045 and the baselines. Sign concordance of g across the two targets is
    a free replication check; report it.
  - Report accuracy-against-AUC rank concordance per family. The metrics convention records that the
    two rank models differently (constituent study 2026-09-16).

  Effort: low.
- **C5. Prior art.** The research log (2,393 lines, grep for screening / seed variance / Dunnett /
  successive halving / winner) has no entry on screen design or seed-variance methodology for ML
  benchmarks. A physics-researcher note on that literature would support the choice between
  ranking and testing, and the winner's-curse handling. I cite nothing from memory here. Effort:
  medium.
- **C6. Considered and rejected, with evidence.** A two-stage screen (2 seeds for all 43 cells, then
  6 more seeds for the top 14; 170 runs against 172) does *not* beat one stage at n = 4 for "all true
  effects in the top 12". `two_stage.py` gives 0.99 against 0.89 (σ 0.6, +1 pt), 0.39 against 0.28
  (σ 1.5, +1), and 0.69 against 0.48 (σ 3.14, +3). Recording this in plan.md's dead ends stops it
  from being proposed again. Effort: low.
- **C7. Length.** 8,900 words (validators v1). The Arms table and the decision list repeat DELTA.
  Everything should still be kept, but a 10-line "what this wave can and cannot say" box at the top
  would carry B2 and A1 to a reader who stops there. Effort: low.

## Answers to 06-review §6.3

1. **Conventions.** Implemented or justified; the deviations are inherited and flagged (l. 504-505).
   OK.
2. **Reference table.** Present, with sources; correctly states that no comparand exists. OK.
3. **What a competing group would have.** A family-level null for the ranking (A1), a rule for
   missing seeds (B1), a non-selecting secondary readout (B7), and a measured base sd (B5).
4. **Honest uncertainties and resolving power.** Not yet. The expected mode has no working
   falsifier (A1), and the resolving-power paragraph omits the only measured spread (B2).
5. **Limitations accepted without an attempt.** [L1] (B8) and [L6] (B7).
6. **Context.** Not applicable at STUDY; no screen number is quotable.

## Summary for the arbiter

Keep the pre-registration machinery, the certification, the fixed BH m and the honest "ranking mode
expected". Fix A1 before PASS: the expected mode needs a falsifier that can fire. Of the B items,
B1 (missing seeds in the ranking) and B3/B5 (make the 30 h replica gate measure the sd and decide
whether the family is worth running) change the most for the least effort. B4 and B7 make the ranked
list, which is the confirm-selection mechanism, harder to fool.
