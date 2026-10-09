# STUDY critical review v1: 2026-09-27-delta-screen (Delta wave 2)

Reviewer: critical-reviewer (panel mode, no verdict). Date: 2026-09-27.
Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (647 lines), with `plan.md` and `budget.py`.
Upstream read: `campaigns/2026-09-26-delta/DELTA.md` §3.3, §5.1-§5.4, §7; `delta.json`
(sha256 checked); anchor `campaigns/2026-09-26-training-batch/STUDY.md` at `dde5ca7`
(`git show`), anchor `RUN.md` l. 55-130, anchor `PREFLIGHT.md` l. 70-75, 488-495, 522-528;
`campaigns/2026-09-26-delta/code/README.md`; `.claude/memory/decisions.md` l. 1-90;
experiment-log head; `docs/methodology/03-phases.md` phase 1, `06-review.md` §6.4 and §6.8;
`docs/conventions/*.md`.

## Validator output (verbatim)

```
STUDY validators v1 (2026-09-27 14:30)
No mechanical STUDY validator exists; prose_lint on STUDY.md:

Desktop/bnjettag/campaigns/2026-09-27-delta-screen/STUDY.md  —  score 0, reads human
  8900 words · 199 sentences · mean 22 words (σ=16.8) · 18% bullets · 13 em-dashes
```
Category A from validators: none (prose_lint score 0). No figures at STUDY, so no plot_check.

## What I verified (numbers, not impressions)

- `delta.json` sha256 = `f4ad2571667af56ccbd28e4271e315aad36d378575d83b9864ace979b8029204`,
  equal to STUDY.md:9.
- The cell table (STUDY.md:91-141) against `delta.json` W2 entries, checked by a script: all 49
  entries present, no extra rows; for every entry the horizon, pairing type, 350k/5M presence,
  `code_changes` and `anchor_patches_required` slugs and `config_delta` keys match. Two value
  renderings differ, and both are documented generator mappings: M038 `pt_gate_gev` 0 → explicit
  null (`delta.json` `config_delta_semantics`; `code/README.md:35`), and M032 `"=horizon"` → 2000.
  No `extra_delta` is non-empty.
- `python3 budget.py` reproduces every Budget number: 68 cells (23 / 1 / 44), 16 E-class cells;
  per-seed epochs 12,500 / 25,000; (4,4) 286 runs, 38,000 / 130,000 / 168,000 run-epochs,
  1,695.6 / 3,007.6 pod-hours, 8.8 / 15.1 d; (6,4) 338 / 196,000 / 1,978.1 / 3,381.0 / 9.5 / 16.4;
  (8,4) 390 / 224,000 / 2,260.7 / 3,754.4 / 10.7 / 17.7; (8,8) 570 / 332,000 / 3,350.7 / 5,934.4 /
  15.1 / 26.5; cheap version 114 + 9 runs, 70,500, 711.5 / 1,211.1, 4.4 / 6.3 d. The formula at
  STUDY.md:433 gives 14,000·4 + 27,000·4 + 4,000 = 168,000. The n_5M = 8 increment (STUDY.md:604),
  108,000 run-epochs and 1,090 pod-hours, equals 3,350.7 − 2,260.7.
- Counts: m = 19 at 350k (12 accuracy + 7 floor family), m = 43 at 5M (44 − 4 baselines + 3
  deferred teacher cells), 272 = 284 − 3 × 4 (DELTA §5.4 counts the teacher cells).
- Threshold (c): class counts 12,479 + 11,882 + 12,499 + 12,579 + 12,561 = 62,000;
  p_maj = 12,579 / 62,000 = 0.202887; SE = 0.0016151; p_maj + 5·SE = 0.2109624. This matches
  anchor `PREFLIGHT.md` `NONDEGENERATE_THRESHOLD`, and STUDY.md:57 truncates it to 0.21096.
  `y_val` sha256 63049d9b…7709 and `x_val` 7b56c1b2…4d31 match `PREFLIGHT.md` `DATA_INFO`.
- The binomial SE √(0.79·0.21/62,000) is 0.001636 (STUDY.md:56). The archived sd of seeds
  67.18 / 72.64 / 67.21 % is 3.14 pt with ddof = 1, matching anchor STUDY l. 350.
- k values recomputed with the noncentral t (scipy): k_t(n, 0.10/19) = 3.656 / 2.085 / 1.581 and
  k_t(n, 0.10/43) = 4.821 / 2.498 / 1.828 at n = 4 / 6 / 8. This is consistent with the k_joint
  values 3.66 / 2.09 / 1.58 and 4.83 / 2.50 / 1.83 (k_joint ≥ k_t by ≤ 0.03, DELTA:703). The sd
  thresholds 0.058 / 0.102 / 0.134 pt (STUDY.md:332) equal 0.3 / (k_joint·√2). The half-width
  t(0.975, 3)/√4 is 1.591 (STUDY.md:350).
- Headroom: 350,000 − 343,053 = 6,947 and 350,000 − 171,526 = 178,474.
- Anchor citations spot-checked at `dde5ca7`: l. 344-351 (reference rows), l. 386-394 (arm
  table), l. 665-670 (matching_initialization), l. 774-806 (selection among (a)-(c), certification),
  l. 835-838 (winner's curse), l. 1228-1232 (no A100), l. 1261-1275 (pilot A rule). Every cited
  line says what STUDY attributes to it. The anchor `RUN.md` pilot telemetry (218.8 / 221.1 /
  216.1 s; A07-350-s1 OOM ×3; 18.8-22.6 of 23.0 GiB) matches STUDY.md:52-54 and 446-449.
- The 12 blocked slugs in X2 (STUDY.md:181-184) match `code/README.md`: 8 on [A1]/[A20] and 4 on
  [A3]/[A4], plus the Linformer wiring on [A20].

## Category A

**A1. Pre-registered DELTA rules dropped or altered, while the change log says "nothing loosened".**
STUDY.md:17-20 says the rules are copied from DELTA §5, "tightened where marked … nothing
loosened", with one dated clarification ([D10]). The STUDY departs from the upstream
pre-registration in four places, and none has a dated amendment:
- (a) **G3′ non-inferiority is missing.** DELTA:844-846 pre-registers G3′ (lower 95 % bound
  > −0.3 pt) for the cost levers M023, M024/M025 and for floor entries at 5M. A non-inferior
  M023 goes to the K5 synthesis check. `grep "G3′|non-inferior"` on STUDY.md returns nothing,
  and the G0-G3 list (STUDY.md:376-386) stops at G3. The cost levers are therefore read only on
  superiority, which is the wrong question for them.
- (b) **The "arm A fails at 350k" rule is missing.** DELTA:571-580 defines failure as fewer than
  ⌈3n/4⌉ of seeds 1-n feasible at epoch H, with consequences for the arm-A cells, the floor
  family, M013 and FF2. STUDY.md:201-205 applies R2 only when the pilot fails. The base-stability
  rule (STUDY.md:276-279) counts only diverged, collapsed and H1-degraded seeds, not infeasible
  or degenerate ones. So a rep-A with 2 of 4 seeds feasible is a "valid control" that supports no
  G3 reading (n_p < 3), and the STUDY says nothing about what happens next. This is a live risk:
  pilot A-s1 is at 9.1M EBOPs at epoch 3 against a 350k target (anchor `RUN.md` telemetry).
- (c) **The sd_plan source is changed and misattributed.** DELTA:710-711 takes sd_plan from arm
  A's epoch-500 sd "over seeds 1-8, feasible, non-degenerate". STUDY.md:327-329 uses the pilot's
  2 seeds (df 1), and STUDY.md:597 says this is "as written in DELTA §5.1". It is not. The per-cell
  t-test stays valid whatever sd_plan is, so the effect is on power and on which mode is declared,
  not on the type-I rate. It is still a change to a pre-registered rule.
- (d) **The wave-2 start condition is dropped.** DELTA:998 (§7, wave 2a) starts wave 2 when "the
  anchor's epoch-500 snapshots of seeds 1-n exist", and DELTA:654 makes the anchor snapshot the
  control. STUDY [D6] (STUDY.md:235-257, 540-542) replaces this with replica-primary at read time
  and launches without anchor production. [D6] is flagged to Kai (STUDY.md:589-595), which is
  right. The change log still does not list it as a departure.

Impact: the claim that STUDY equals DELTA plus tightenings is false. Two rules that decide what
a cell's number means (G3′, base feasibility) are absent. Fix: restore G3′ and the ⌈3n/4⌉ rule
(for the replica at H; state which branch follows) verbatim. Correct STUDY.md:17-20 and
STUDY.md:597. Record (c) and (d) as dated amendments against DELTA §5.1 and §7, with the reason.
Also restate the 12-cell cap (DELTA:858), which is absent too (B-level alone).

**A2. The falsifier in ranking mode (the expected mode) is close to unable to return "no".**
STUDY.md:33-34 and 409-412 define the wave's "no" in ranking mode as "no cell's lower 80 % bound
on g exceeds 0 in either family". This is STUDY's addition: DELTA:838-843 defines "zero
advances" for significance mode only. Under the full null, each cell's lower 80 % bound is above
0 with probability about 0.2. I simulated n = 4, a shared replica per family and equal
variances (20,000 reps, numpy seed 0). P(no bound above 0) came out 0.26 at m = 19 and 0.16 at
m = 43, with 3.8 and 8.5 false "positive" cells expected per family. P(the wave's "no" | no
effect anywhere) is therefore about 0.26 × 0.16 ≈ 0.04. STUDY.md:344 says ranking is the expected
outcome, so the stated falsifier is expected to report positive cells when nothing works.
Fix: add one or two A/A null cells per family: the base config with a no-op delta (for example
a different run identity) at seeds 1-n, which go through the same selection, certification and
ranking. Define the ranking-mode "no" as "no cell ranks above the A/A cells" (or use a
sign-flip/permutation null on the max lower bound). Alternatively, state that ranking mode has
no negative answer and remove the sentence. Cost: 4 runs × 500 epochs per family.

**A3. Resolving power is shown only at spreads below the one measured reference.** STUDY.md:349-353
works the n = 4 interval at sd_d = 0.3 and 0.85 pt. The only measured spread in the reference
table is 3.14 pt (STUDY.md:55; sd_d ≈ 4.4 pt at ρ = 0). DELTA:728-729 states g_res(8) = 8.12 pt
at that spread, and the STUDY omits it. At sd_d = 4.4 pt the n = 4 95 % half-width is 1.59 × 4.4
= ±7.0 pt. In my simulation (m = 43, one true 0.3-pt effect, ranking by lower 80 % bound), the
true effect lands in the top 12 with probability 0.32 at sd_d = 4.4 against 0.28 by chance, and
0.52 at sd_d = 0.85. The ranking that goes to Kai at K3a can be close to random, and the STUDY
does not say so. This is the "wide spread means no resolving power, and that is the finding"
case. Fix: add the 3.14-pt row to "What n = 4 resolves" with its half-width and its
ranking-fidelity number. State the sd_rep at which the ranked list is no better than chance.
Pre-register what the ranked list may be used for if the replica's epoch-500 sd_rep exceeds
that value (for example: no ranked list to Kai, feasibility counts only).

**A4. Circular selection: the ranked number is the maximum over the split it is read on, and
[L6] rationalizes it.** STUDY.md:358-363 selects the best-feasible checkpoint by maximum
validation accuracy over up to H (500-2,000) epochs. STUDY.md:391-394 reads and ranks that same
number, and no held-out readout exists (STUDY.md:395-396). [L6] (STUDY.md:578-579) says "in the
screen both arms of a pair share it". That holds only if the cell and its control have the same
epoch-to-epoch fluctuation and the same H. Several cells change exactly that: M018/M019 (STE),
M020 (Bop), M028/M029 (LR), M032 (one cosine over 2,000 epochs against four restarts), M034
(EMA). The max-over-epochs inflation is then treatment-dependent, and with a binomial SE of
0.16 pt per checkpoint it can be the size of g0. Fix: pre-register a non-selected companion
readout for every run: validation accuracy at epoch H (LR at its 1e-6 floor), or the mean over
the last k epochs of the final cycle, among feasible, non-degenerate epochs. Report both. Flag any
cell whose rank moves by more than a pre-set amount between the two, and rewrite [L6] to say what
is and is not shared.

## Category B

**B1. Missing-pair rule and informative missingness.** DELTA:772 computes g_s only over seeds
"usable in both", and G3 needs n_p ≥ 3 (DELTA:813). STUDY states neither (STUDY.md:376-386). With
n = 4, an entry that fails on the hard seeds is scored on the easy seeds against the replica on
the same seeds, which is a selection effect. Fix: restate the rule, report n_p per cell, and rank
cells with n_p < n separately or with the missing seeds shown (a worst-case bound, or feasibility
beside accuracy).

**B2. E packing violates the STUDY's own memory rule.** [D16] fixes E at K = 6 (STUDY.md:473,
558). Its evidence is 18.8-22.6 of 23.0 GiB on the A10 (anchor `RUN.md` "GPU"), which is up to
98 %, while the canary rule accepts K only at ≤ 90 % of card memory (STUDY.md:474-475). Launch
gate 7 (STUDY.md:224-226) runs the canary for E too. The pilot pack was mixed (two A07 arms
OOM'd), so a pure-E K = 6 figure is unmeasured. Either exempt E with a reason, or take the E K
from the canary like A07 and mark s_e = 218 s at K = 6 as provisional in the budget.

**B3. Always-on patches are not gated by X2.** X2 (STUDY.md:174-178) checks only each entry's
`code_changes` and `anchor_patches_required`. Every run, replicas included, also needs
`screen-collapse-stop` (G1), `accumulator-ebops-metric` (Z03 readout) and the `diag-*` patches.
`code/README.md` lists all of them as "gated-on-tarball", not gated on the anchor tree. Fix: add
a launch gate that these are rebased and gated on the anchor tree. If one fails, the whole wave
waits, not one cell.

**B4. The anchor config can change after Delta launches.** Anchor production is waiting for Kai
because T_run = 17.7 d exceeds the 14-day rule (anchor `RUN.md` "Canary and projections"; anchor
STUDY [D15] options: a different trace cadence, K or terminal epoch). No launch gate requires the
anchor's production config to be frozen. rep-A and rep-C could then encode a config that arm A
and arm C no longer use, and W3/W4 inherit the mismatch. Fix: add a gate (Kai's [D15] answer
recorded, or the anchor production config sha fixed) or a pre-registered rule that relabels the
screen's base as "rep-A at config sha X" if the anchor changes.

**B5. The question states a threshold the decision rule does not use.** STUDY.md:6 and 22-26
ask whether the entry changes accuracy "by at least g0 = 0.3 pt". The advance gate is BH p ≤ 0.10
and mean g ≥ 0.15 pt, one-sided (STUDY.md:383-384; g0 is the MDE target, DELTA:833-837), and
"change" reads as two-sided. Fix: word the question as the rule: one-sided improvement,
BH-adjusted, mean ≥ g0/2, with g0 as the MDE target.

**B6. Floor-family accuracy readings mix a package with single-lever effects.** The seven
floor-family cells compare an A07-derived architecture plus the entry against arm A (E) by Welch
(STUDY.md:93-101), which measures architecture plus entry. They sit in the same m = 19 BH family
and the same ranking as the 12 paired single-lever cells on A (STUDY.md:387-389). The question
(STUDY.md:22-25, "applied to its base arm … paired by seed") does not describe them. Fix: rank
them in a separate labelled list, "cross-architecture package". Keep the BH m fixed if you want
it conservative, but never interleave the ranks.

**B7. The cheap version leaves its long-horizon cells uncontrolled.** The cheap selection (from
`budget.py` `cheap()`) includes M015 (H 1,000), M031 (1,500) and M032 (2,000), and its replicas
run to 500 only (STUDY.md:481-484). DELTA:922-923 controlled those cells with anchor snapshots,
which do not exist (STUDY.md:254-257). Fix: extend the cheap version's rep-A to 1,000 and rep-C
to 2,000 and restate its budget, or drop the three cells from it.

**B8. [D14] has no matching limitation.** The training-only levers (M017-M037) screen at 5M on
A07 only, while the thesis target is 350k on E. Nothing in [L1]-[L6] says the screen does not
test transfer to 350k/E. Fix: add an [L] and say which confirm cell tests the transfer.

**B9. Conventions rows.** (i) `quantization-and-cost.md` "Selection under a budget" names
validation macro-OvR AUC as the rule of record. STUDY.md:512 says "will implement the anchor rule"
(top-1 accuracy) without marking it as a deviation. The Metrics row (STUDY.md:505) does mark it.
Mark it in both rows. (ii) Check 3 of `jet-tagging-metrics.md` (baseline reproduces the record)
is claimed through g_rep (STUDY.md:508). Under the expected replica-primary branch, anchor
snapshots mostly do not exist (STUDY.md:254-257), so say it will probably be unavailable and what
stands in for it. (iii) The "Pitfalls" sections of both conventions have no row. The
cross-axis-comparison pitfall applies directly to the floor-family Welch readings (B6).

## Category C

- C1. Certification count: STUDY.md:493 says "about 286 retraces". Replicas are read at several
  horizons (rep-A at 500 and 1,000; rep-C at 500, 1,000, 1,500 and 2,000), so the count at (4,4)
  is about 272 + 8 + 4 + 16 = 300 plus teachers.
- C2. "Formula check" (STUDY.md:424-426) expects per-seed g_rep "exactly 0 at the same sha and
  product", but g_rep is replica (Delta sha) − anchor (anchor sha) (STUDY.md:245), and
  bit-identity is not assumed (STUDY.md:311). An exact-zero per-seed difference would be a red
  flag (the runs did not vary), not the limiting case. The A/A cells of A2 give a real
  identical-arms check.
- C3. Confound 8 (STUDY.md:303-304) lists the quantizer-changing entries as M003, M007, M008,
  M011, M012, M047-M050. M016 and M017-M026 (tanh LUT, binarizer centre, STE, β mode, channel
  gain, pre-quant shift) also change the quantization path.
- C4. X4 (STUDY.md:188-194) covers a missing trace but does not restate DELTA R1 (DELTA:519-523):
  a cell whose traced floor is at or above its target is removed, not run and read as degenerate.
- C5. P-T1/P-T2 are selected on validation accuracy (DELTA prerequisite_jobs), on the same
  62,000 jets that later select and rank the KD and warm-start students (M027, M035, M036). This
  is mild leakage. Note it in the X1 amendment.
- C6. Baselines M047-M050 in ranking mode: say whether they appear in the ranked list (they
  should not, or only as marked comparands).
- C7. M010 (1.4M) has A07-350 (a 350k run) as its "seed partner" (STUDY.md:70, 150). Say what the
  pairing is used for, since G2 counts at two different targets are not a contrast.
- C8. 03-phases.md:70 asks for a one-sentence question and null. The question (STUDY.md:22-29)
  and null (STUDY.md:31-34) are paragraphs. A one-line version at the top would help Kai at K2.

## Competing-group question

A group publishing the same screen next month would have (1) a readout not used for selection
(A4), (2) an A/A null inside the ranking that calibrates what a top-ranked cell means (A2), and
(3) a statement of how often the ranking finds a real 0.3-pt effect at the measured spread (A3).
They would also rank on a noise-robust statistic (a pooled per-family sd, not a per-cell df-3 sd,
for the lower bound). None of these is justified as unnecessary in the STUDY; each is covered
above. To its credit, the STUDY already reads the replicas' epoch-500 sd before any cell starts,
and it fixes BH m with p = 1 for unrun cells, which a competing design might not do.

## Disputed facts for the investigator

None needed; every concern above was traced to file and line in this review.
