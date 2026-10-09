# STUDY review, constructive, v3: 2026-09-27-delta-screen (Delta wave 2)

Reviewer: constructive-reviewer, fresh context, 2026-09-27. Artifact: `STUDY.md` (1,369 lines,
iteration 3, after fixer v2). Read: `docs/methodology/06-review.md`, `03-phases.md` Phase 1,
`docs/conventions/jet-tagging-metrics.md`, `plan.md`, `budget.py`, `screen_null.py`, `rank_sim.py`,
`review/STUDY_validators_v3.txt`, my own `review/STUDY_constructive_v2.md`, `review/STUDY_arbiter_v2.md`
(so earlier findings can be tracked by name), the newest entries of `.claude/memory/experiment-log.md`
and `decisions.md`, and `research-log.md` (grep for screen-design, seed-variance or multiple-comparison
prior art: nothing found). Not read: the critical or physics files of this iteration.

**Verdict in one line. No Category A.** Two B items. Both are text-level pre-registrations that
need no GPU before PASS. Eight C items.

## Reproduced (evidence for the [+] items)

- `python3 screen_null.py` (seed 20260927, about 10 s) reproduces every family-test number the
  STUDY quotes. Own-sd critical values are 4.406 (m 12) and 6.751 (m 40) at n = 4, and 4.284 / 6.585
  at m = 11 / 37. Achieved false "yes" with the own-sd rule (R2) is 0.099-0.111 under equal and
  unequal spread and 0.038-0.089 under two-mode seeds. Power for one +1-pt cell is 0.204 / 0.046 /
  0.022 (m 12) and 0.074 / 0.015 / 0.007 (m 40). The ranking-interval multiplier is 2.179 / 2.146,
  with nominal coverage 0.934. G3′ power is 0.074 / 0.041 / 0.031. The rank-move null counts and the
  sd_rep false-pause and false-pass rates also match. ✓
- `python3 budget.py` (run from the campaign directory) reproduces 302 runs, 176,000 run-epochs,
  1,112.2 / 1,959.0 pod-hours, 5.4 / 9.2 d and 318 retraces at (4, 4). It also gives 268 runs /
  156,000 run-epochs for the part that can be packed today, and cheap 129 runs / 79,500 run-epochs. ✓
- Code claims:
  - `ablation.py:597` sets only `keras.utils.set_random_seed(seed)`.
  - `digest_json` is at `:35` and `config_sha256 = digest_json(cfg)` at `:623`.
  - `train.py:261` and `qat.py:386` are the only other seed calls in the tree. No
    `enable_op_determinism` exists under `bnhgq2/`.
  - The placebo emitter is at `campaigns/2026-09-26-delta/code/generate_delta.py:588-603`.
  All match STUDY l. 192-206 and 443-447. ✓
- New scripts, design arithmetic only (seeded Monte Carlo, not results), in `review/`:
  - `constructive_v3_extend.py`: uniform n = 6, and n = 4 plus seeds 5-8 for the top k.
  - `constructive_v3_moderated.py`: variance-moderated max-t at prior df d0 ∈ {0, 3, 6, 12, ∞}, and
    the power of the STUDY's unpaired companion.
  - `constructive_v3_placebo8.py`: an unpaired Welch test against a placebo at 8 seeds.
  - `constructive_v3_gated.py`: moderated d0 = 3, gated by a shape read on the 8 replica seeds.

## What is done well

- [+] **The family test is now calibrated, and the design says what that calibration costs.** The
  placebo-referenced own-sd max-t holds 0.10-0.11 in every equal- and unequal-spread row and
  ≤ 0.089 under two-mode seeds (reproduced). The STUDY prints the price next to it: power 0.204 at
  best, below α at σ ≥ 1.5 pt, and "the ranking is the only output" (l. 114-117). The n = 3 rows are
  labelled "not calibrated under two-mode seeds" (l. 773-774, 1010). This is the honest version of
  the test.
- [+] **Negative results are framed plainly.** "A 'no' is not evidence of absence" (l. 117, 871).
  G3′ failure reads "non-inferiority not shown at this n", never "inferior" (l. 724). The flat-gap
  convention deviation is declared with its reason (l. 1035). A reader who stops at the box
  (l. 99-117) comes away with the right sentence.
- [+] **The placebo is specified mechanically**, not by intent. The only keys that differ are
  identity and provenance keys, each checked against the runner. The PREFLIGHT assertion covers the
  digest without those keys, init `kernel_hashes` and first-step CPU loss (l. 190-215). Both
  determinism outcomes are pre-registered before any result exists (l. 775-785).
- [+] **Replica-side losses have a rule** (l. 536-544): n drops uniformly, the critical value is
  re-simulated, and replica seeds 5-8 cannot substitute. This closes the "empty main list" hole.
- [+] **The ranking is correctly understood to be invariant to pairing.** "The replica term is
  common … it cancels from the order of the means" (l. 656-658). Pairing is then tested, not
  assumed: ρ̂ is printed with its null interval, and an unpaired companion is added (l. 839-849).
- [+] **Winner's-curse handling was re-derived for regime B.** Traced epochs only, with the
  denominator printed from `is_traced_epoch` on the frozen bundle (50 or 51 per cycle, l. 669-678).
  Split-half is a second non-selecting companion. The rank-move threshold T comes from simulated
  null counts, and the family goes to Kai where no T keeps the null count near one (l. 806-816).
- [+] **The tuning-asymmetry paragraph** (l. 151-155) says, before any result, what a confirm
  comparison against an untuned baseline would mean.
- [+] **Budget and timing are labelled projections, with the arithmetic shown** (l. 930-981), and
  they reproduce exactly.

## Earlier findings (constructive v2), by name

| v2 | finding | status | evidence |
| --- | --- | --- | --- |
| A1 | family test calibrated only under homogeneous Gaussian | **resolved** | own-sd placebo-referenced rule l. 751-774; scenario rows reproduced; "by construction" gone |
| B1 | pairing efficiency assumed | **resolved** | ρ̂ with null interval and unpaired companion l. 839-849 |
| B2 | placebo rests on unmeasured GPU determinism | **resolved in substance**; residual in B2 below | probe l. 443-448, both branches l. 775-785, excluded from s_pool |
| C1 | lower bracket 0.19 pt, two-mode note | resolved | l. 171, 624-630 (label refinement: C5 below) |
| C2 | family-test power at the ceiling | resolved | box l. 114-117 |
| C3 | "cannot call a gap flat" undeclared | resolved | conventions row l. 1035 |
| C4 | mean over last k epochs as companion | considered, rejected with a reason | l. 818-819 (split-half instead); acceptable |
| C5 | +1 / +3 pt illustrations | resolved | l. 110, 646-647 |
| C6 | significance mode is dead text | partly | ranking mode now first in the Question; the BH machinery is still spread over Seeds and Selection; acceptable |
| C7 | E packing K = 4 | resolved | l. 983-993, [D16] |

## Category A

None. I checked every escalation trigger:
- no selection on held-out data (l. 850-851);
- no projection stated as a result (timing labelled l. 930-943);
- no tautological comparison presented as evidence (the placebo branch is pre-registered);
- no required validation missing (the conventions table is complete, l. 1031-1051);
- no method failure accepted without remediation.

## Category B

### B1. In ranking mode n is fixed at 4 whatever sd_rep reads, although the budget already prices n = 6 and the replicas already pair seeds 5-8

- **Current.** Seeds, l. 599-606: n ∈ {4, 6, 8} is chosen by the significance-mode k_joint
  thresholds, sd_rep ≤ 0.058 / 0.102 / 0.134 pt (350k) and 0.044 / 0.085 / 0.116 pt (5M). "If no n
  qualifies, the family runs in ranking mode at n = 4, unless Kai buys n = 8". The STUDY expects
  none to qualify (l. 624-632). So the Budget rows (6, 4), (4, 6) and (6, 6) (l. 914-922) are priced
  but no rule can reach them. In ranking mode, n = 4 is fixed whether sd_rep reads 0.6 pt or
  1.29 pt, just under the pause line.
- **Problem.** The only output the STUDY expects is the ranking, and its fidelity depends on n and
  σ alone (l. 656-657). Between about 1.0 pt and the 1.3-pt ceiling, n = 4 loses much of the
  recovery that n = 6 buys. `review/constructive_v3_extend.py` (ρ = 0, 20,000 reps, same model as
  `screen_null.py` §3):

  | family, criterion | σ | n = 4 (STUDY) | n = 4 + seeds 5-8 for the top k | n = 6, every cell |
  | --- | ---: | ---: | ---: | ---: |
  | 5M, 3 true +1 pt all in top 12 of 40 | 1.0 | 0.75 | 0.84 (k 16) | 0.89 |
  | | 1.3 | 0.54 | 0.67 | 0.70 |
  | | 1.5 | 0.43 | 0.55 | 0.59 |
  | 350k, 1 true +1 pt in top 3 of 12 | 1.0 | 0.88 | 0.95 (k 6) | 0.94 |
  | | 1.3 | 0.78 | 0.88 | 0.86 |
  | two-mode q 0.33, 5M | – | 0.09 | 0.19 | 0.26 |

  At σ ≤ 0.6 pt, n = 4 is already saturated (0.99). The gain sits in exactly the band the ceiling
  admits.
- **Costs.** The costs come from `budget.py` rows already in the STUDY: (4, 6) is 392 runs,
  1,453.5 / 2,641.5 pod-hours and 6.6 / 11.6 d; (6, 4) is 354 runs and 5.9 / 10.3 d. Replica seeds
  5-8 already run to epoch 500 ([DK2], l. 307-310), so pairing the extra seeds costs no replica
  runs for the H = 500 cells.
- **Improved.** Pre-register a ranking-mode n rule keyed to sd_rep, as a [DK] default Kai may
  override:
  - n = 4 if sd_rep < 1.0 pt;
  - n = 6 if 1.0 ≤ sd_rep ≤ 1.3 pt;
  - pause above 1.3 pt, as now.
  Put it beside the significance-mode rule, not in place of it.

  The cheaper alternative is the top-k extension. After the n = 4 readout, the top 16 cells at 5M
  and the top 6 at 350k get seeds 5-8. That is 64 + 24 cell runs, 44,000 run-epochs, paired with
  the replica seeds that already exist. It recovers most of the n = 6 gain for about 60 % of the
  runs that (6, 6) adds (88 against 142, `budget.py`).
  - This is **not** the two-stage design rejected in `plan.md` l. 53-55. That design cut stage 1 to
    2 seeds and lost. This one keeps n = 4 for every cell and only adds seeds.
  - The 8-seed mean of an extended cell includes the seeds it was selected on. The seeds-5-8 mean
    must therefore be printed separately as the selection-free estimate.
  - The long-horizon cells are excluded, because their replicas stop at 500 above n.

  Either option also halves the interval half-width for the cells Kai picks from: t(0.975, 7) / √8
  = 0.84 · sd_d against 1.59 · sd_d. That matters because the next spend is the 8-seed,
  7,000-epoch confirm.
- **Why B.** §6.3 Q4 asks whether the design has resolving power at the gap it cares about. In the
  1.0-1.3-pt band it has less than the priced budget allows, and no rule uses what is already paid
  for.
- **Effort.** Low for the text: one rule, one [DK] row and one "Where I am not sure" row with the
  costs above. The GPU cost is Kai's call at the launch gate.

### B2. The determinism probe does not test what the placebo branch depends on, and the branch is not needed for the test

- **Current.** Launch gate 7 (l. 443-448): "in the E canary pod, the same E config and seed run
  twice on one GPU product for 3 epochs". The outcome selects one of two placebo branches
  (l. 775-785). In the bit-identical branch, the family test is referenced to the replica and "the
  assumption 'no common offset between the replica's pod and the cells' pods'" is printed beside
  every error rate, with the 0.261 / 0.258 false "yes" at a 0.707-SE offset.
- **Problem.**
  - (i) Under regime B the first traced epoch is epoch 10 (l. 669-671). A 3-epoch probe never
    reaches the PID's traced-value branch or an in-training trace. The only trace it runs is the
    initial one at `ablation.py:622`.
  - (ii) The 5M family is A07 (4 heads, learned PE), yet the branch for both families is chosen from
    a probe on E only.
  - (iii) The placebo is never in its replica's pod (l. 207). Bit-identity of two processes in one
    pod does not show cross-pod or cross-pack identity. Library algorithm choice can depend on
    co-tenant memory pressure, and K differs between packs.
  - (iv) The branch changes nothing in the test's arithmetic. When the placebo equals the replica at
    seed s, d_i,s = c_i,s − p_s = c_i,s − r_s = g_i,s. The two branches' critical values are 4.406
    and 4.426 (m 12) and 6.751 and 6.791 (m 40) (`screen_null.py` §4). The distribution of c − p is
    the same whether p is an independent null draw or the replica itself.
  - (v) The "no-offset assumption" does not need to be assumed. If the placebo, in a cell pod,
    reproduces its replica bit for bit at every seed, the offset between the replica's pods and the
    cells' pods has been measured to be zero on that GPU product. Printing 0.26 beside a measured
    zero misleads the reader.
- **Improved.**
  1. Use one reference for the family test in every case, the placebo (d_i = cell − placebo),
     critical value simulated as now. Delete the test branch in l. 775-785.
  2. Let the probe and the placebo decide only how the placebo row is read. If the placebo equals
     its replica bitwise at every seed of the family, the row is read as "pod, pack and identity
     check passed: offset measured zero", its rank is not read, and the 0.26 line is dropped. Any
     seed where they differ switches that family to the divergent reading (placebo as the
     in-family null draw, divergence printed).
  3. Run the probe per architecture class (E and A07), for at least 11 epochs so that one traced
     epoch and the PID's traced-value branch are exercised. The added cost is a few canary epochs.
- **Why B.** The branch is pre-registered on a probe that cannot establish its premise for the 5M
  family or across pods. It also attaches a hypothetical error rate to a quantity the placebo
  measures directly. Removing the branch simplifies the design and makes the stated error rate
  true in both outcomes.
- **Effort.** Low (text, and one line in the canary spec).

## Category C

- **C1. A third calibrated family-test option was not on the arbiter's (a)/(b) menu.**
  - *Current:* own sd (df 3) was chosen over pooled + homogeneity gate (l. 758-764).
  - *Alternative, tested:* the per-cell variance shrunk toward the family pool with prior df d0 = 3
    (`constructive_v3_moderated.py`), used when a shape read on the 8 replica seeds at the epoch-500
    gate finds no mode gap, and own sd otherwise (`constructive_v3_gated.py`). The gate is the
    largest sorted gap over sd_rep, against its Gaussian 95th percentile of 1.718.
    - At m = 12, false "yes" is 0.043-0.111 in every row (equal, 25 % at 3×, two-mode q 0.1 / 0.33
      / 0.5). Power for one +1-pt cell rises 0.196 → 0.427 at σ 0.6 and 0.077 → 0.167 at σ 1.0.
    - At m = 40, power rises 0.070 → 0.289, but the 25 %-at-3× row reaches 0.153. The shape gate
      only catches two-mode seeds.
    - An unpaired Welch test against a placebo run at 8 seeds (`constructive_v3_placebo8.py`) gains
      similar power (0.475 / 0.300) but fails the unequal-spread rows (0.14-0.18) and the two-mode
      rows (0.12-0.21). It is not recommended.
  - *Improved:* either adopt the gated moderated rule at 350k only, where it holds ≤ 0.111
    everywhere, or record it in `plan.md` dead ends with these numbers. The STUDY's choice is
    defensible. The point is that the power ceiling comes from df 3, and only seeds (B1) or
    moderation move it.
  - *Effort:* low.
- **C2. [L8] contradicts two other places in the STUDY.** Arms l. 214-215 and Selection l. 738-740
  say the long-horizon cells (M015, M031, M032) are outside the family test and reported against
  the replica. [L8] l. 1196-1197 says they "use the H-500 placebo as their reference, labelled so".
  Make [L8] match. Effort: low.
- **C3. The body still carries the review-cycle trail.** It has 24 references after l. 94 such as
  "arbiter v2 fix 3d", "(v1 argued … withdrawn)", "The v2 thresholds … flagged 6.9-24.4 null
  cells" and "constructive C4". §6.6 asks that "the body reads as if the current design was the
  plan from the start, and the change log at the top carries the audit trail". Move these into
  the change log and keep one label per decision in the body. Effort: low.
- **C4. The prior-art note is still missing at iteration 3** (l. 1367-1369, "requested, not
  assumed"). The research log has no entry on multiple-comparison screens, variance moderation or
  seed-variance methodology (grep). This bears directly on C1 and on the ranking-versus-testing
  choice. Ask physics-researcher for dated, URL-backed entries before REPORT. This review cites
  none from memory. Effort: medium (a session).
- **C5. Label the lower bracket as the record now describes it.** The "N=8 W1A8, 8 seeds, held-out
  sd 0.19 pt" (l. 171, 628) is the pT-weighting BASE. The 2026-09-27 inventory entry in the
  experiment log records that run as 101 epochs with early stopping on the archived Round-14
  recipe, not a constrained 1,000-epoch run. Add "101 epochs, archived recipe" to the label.
  Effort: low.
- **C6. Compute the rank-move r cell-centred.** `screen_null.py` §8 draws x (primary) and y
  (companion) per run with no between-cell means. The observed r at l. 808-809 is "family-pooled
  run-level" and includes real between-cell differences. Centre each cell's primary and companion
  values on the cell before pooling, so the observed r is the quantity the T table was simulated
  for. Effort: low.
- **C7. Name the candidate code base.** `decisions.md`, top entry (ml-engineer, 2026-09-27), says
  the anchor re-froze `chang0926-code.tar.gz` to e90327d4 (regime B), uncommitted, and that
  `apply_anchor.sh`'s default now fails its sha check. The frontmatter and launch gate 11 say
  only "the sha the anchor PREFLIGHT addendum for patch 0027 names". Add "candidate e90327d4,
  uncommitted as of 2026-09-27, confirmed at PREFLIGHT". Effort: low.
- **C8. The box's family-test powers are at m = 12 / 40, but the test's m is 11 / ≤ 37**
  (l. 733-737). Either print the m = 11 / 37 values or add "design grid m = 12 / 40" in the box
  (l. 114-117) and the Falsifier (l. 871-873). Effort: low.

## Answers to 06-review §6.3

1. **Conventions.** Implemented or justified. The deviations (90/10 split, accuracy as the
   selection metric, the flat-gap rule) are declared with reasons (l. 1033-1041).
2. **Reference table.** Present, sourced, and correctly without a comparand for a screen that is
   never quoted (l. 157-174).
3. **What a competing group would have.** An n rule in ranking mode that uses the priced n = 6 rows
   or the already-paired replica seeds 5-8 (B1). A single placebo reference, with the offset
   measured and not assumed (B2). A literature note on screen statistics (C4).
4. **Honest uncertainties and resolving power.** Honest in both directions. The own-sd rule is
   calibrated and its low power is stated. Resolving power is stated per σ (l. 634-663). B1 is
   where it could be better within budget.
5. **Limitations with attempts.** [L1], [L6] and G3′ now carry attempts or power statements. The
   determinism probe is an attempt that tests less than it is used for (B2).
6. **Context.** Not applicable at STUDY (no results).

## Summary for the arbiter

No Category A. Keep:
- the placebo-referenced own-sd family test with its scenario rows;
- the "can and cannot say" box;
- the replica-loss rule;
- the G3′ power statement and the M023 decoupling;
- the unpaired companion and ρ̂;
- the regime-B selection rule;
- the budget, which reproduces exactly.

B1 is one pre-registered rule and one Kai row. At σ 1.0-1.3 pt it raises 5M top-12 recovery from
0.54-0.75 to 0.67-0.84 with the top-k extension, or 0.70-0.89 at n = 6, at costs already in
`budget.py`. B2 removes a branch that does not change
the test's arithmetic, and it turns an assumed no-offset condition into a measured one. Both are
text. C1-C8 are text or labels, except C4 (a research-log note).
