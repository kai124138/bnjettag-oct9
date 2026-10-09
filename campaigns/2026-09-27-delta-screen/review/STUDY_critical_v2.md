# STUDY critical review v2: 2026-09-27-delta-screen (Delta wave 2)

Critical reviewer, panel mode, fresh context, 2026-09-27. Re-review, iteration 2. No verdict (the
arbiter issues it).

Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (1,025 lines, commit 9f9deeb), with `plan.md`,
`budget.py`, `screen_null.py`, `rank_sim.py`. Read: `review/STUDY_arbiter_v1.md`,
`review/STUDY_fixer_v1.md`, `review/STUDY_validators_v2.txt`; the experiment-log stub
(`.claude/memory/experiment-log.md` l. 11-16); `.claude/memory/decisions.md` (working tree); anchor
`campaigns/2026-09-26-training-batch/STUDY.md` (working tree and HEAD); anchor code tree
(`code/tree`) and Delta code notes (`campaigns/2026-09-26-delta/code/`). Scratch simulations are in
the session scratchpad; nothing here is a result.

## Validator output (verbatim)

```
STUDY validators v2 (2026-09-27 15:02)
No mechanical STUDY validator exists; prose_lint on STUDY.md:

Desktop/bnjettag/campaigns/2026-09-27-delta-screen/STUDY.md  —  score 0, reads human
  14625 words · 347 sentences · mean 24 words (σ=17.6) · 16% bullets · 13 em-dashes
```

No red flag, so nothing below is Category A by the validator rule. No figures at STUDY, no
plot-validator output.

## Recomputed (show-your-work)

- `python3 screen_null.py` (seed 20260927), reproduced in full: arbiter-v1 wording P(no | null)
  0.076 (m 12) and 0.023 (m 40), against 1/(m+1) = 0.077 and 0.024. Dunnett critical t 2.410 /
  2.337 / 2.304 (m 12, n 4 / 6 / 8) and 2.793 / 2.680 / 2.651 (m 40); P(no | null) 0.896-0.904;
  placebo false flag 0.0336 (m 12) and 0.0126 (m 40) at n = 4; P(no | one +1-pt cell) 0.489 /
  0.846 / 0.880 at σ 0.6 / 1.5 / 3.14 (m 12) and 0.617 / 0.879 / 0.900 (m 40); recovery 0.53 at
  σ 1.3 and 0.48 at 1.4 (5M, chance 0.022), so the ceiling is 1.3 pt; 350k criterion 2.7 pt. Every
  value matches STUDY l. 72-73, 92, 484-488, 581-582, 635-638, 657. The fixer's diagnosis of the
  arbiter's wording is correct: under the global null the placebo is one of m + 1 exchangeable draws.
- `python3 budget.py` (v2), reproduced: (4, 4) 302 runs, run-epochs 42,000 / 134,000 / 176,000,
  318 certification readouts, 1,776.3 / 3,128.7 pod-hours, 8.6 / 14.7 d; every other Budget row
  (l. 676-682, 711-717) matches; cheap 129 runs, 79,500 run-epochs, 802.4 / 1,362.5 pod-hours,
  4.6 / 7.4 d (l. 741-742). By hand: 14,000 · 4 + 27,000 · 4 + 12,000 = 176,000 (l. 672); E-class
  = 4 · (15 · 500 + 1,000) + 2,000 + (4,000 + 2,000) = 42,000; certification = 272 + 8 + 2 + rep-A
  12 + rep-C 20 + rep-A07-350 4 = 318.
- `rank_sim.py` (identical to `review/rank_sim.py`, `diff` empty), rerun: every cell of the table
  at l. 515-519 matches (for example σ 3.14, +1 pt, ρ 0: 0.11 / 0.10; σ 1.5, +1 pt, ρ 0.5: 0.67 /
  0.59). Null "contradicted" counts 0.48 / 1.07 match l. 644-645.
- Cell counts from the table at l. 171-221: 5M cells run = 44 (40 with G3, 4 baselines; M027,
  M035, M036 deferred, so BH m 43 = 40 + 3); 350k = 12 accuracy + M050 + 3 probes + 7 floor = 23.
  Matches l. 242-244 and `budget.py` ("68 by target: 350000: 23, 1400000: 1, 5000000: 44").
- Experiment-log stub (l. 11-16): 302 runs, 176,000 run-epochs, 1,776.3 / 3,128.7 pod-hours, 318
  retraces, 1.3-pt ceiling, P(no | null) 0.90, cheap 129 / 79,500, all equal to STUDY. No stale
  "286" outside the labelled v1 comparison at l. 720.
- Own stress tests of the [DK7] family test (numpy, 20,000 reps each, critical values from
  `screen_null.crit`) and of G3′: numbers quoted in findings A1, A2, B3, B4, B5 below.

## Category A (must resolve)

**A1. The STUDY is built on a trace regime the anchor abandoned: Kai's [D15] regime-B decision is
absent.** `.claude/memory/decisions.md` (working tree, uncommitted at review time), entry
"2026-09-27 (Kai, [D15] branch after the canary)": the [D20] full-split trace runs every 10 epochs,
a second pilot pod runs under regime B, wave 1 at about 13 pods at K = 5 on the A10 class, "Delta at
10 after this campaign's epoch-500 readout", about 27 pods at peak. Commit 5276ee0 (14:55, before the
fixer's 9f9deeb at 15:02) names "regime-B amendment as dated execution of [D15]"; the anchor STUDY
working tree carries it (l. 299, 535-536, 854, 1396-1420, 1451, 1458-1463). Under regime B the
feasibility test (a)-(c) runs only on traced epochs, and "only a traced epoch that meets (a)-(c) can
become `model_best.keras`" (anchor STUDY working tree, l. 1416-1418). Sites in this STUDY that are now
wrong or undecided:
- l. 164: "the [D20] full-training-split EBOPs trace every epoch" is in the list of what is
  identical across every run. Which regime the Delta runs use is not stated anywhere.
- l. 532-539 (selection "among epochs 1..H"), l. 593-598 (companion "last feasible epoch" from
  per-epoch logs; eligible-epoch count): under regime B at most 50 epochs per 500-epoch cycle are
  eligible, which changes the eligible count, the winner's-curse size ([L6]) and the companion.
- l. 118-119 and l. 39-40: "Anchor production has not launched … waiting for Kai, anchor [D15]" is
  stale. Kai has answered [D15], and the reason given for amendment §7 wave 2a is no longer the
  reason.
- l. 307-311 (launch gate 1, "anchor pilot A rule passed at epoch 500"): there are now two pilot
  pods (regime A and regime B). The gate does not say which one.
- l. 690-723: every pod-hour and wall-clock row uses 218 s per E epoch at K = 6. That figure
  includes a trace median of 0.42 of the epoch, which regime B pays one epoch in ten. Under regime B
  the rows are roughly a third too high. Under regime A they describe a config the anchor no longer
  runs.
- l. 727-731, 857-859, 978-983: the STUDY's 90 % rule predicts K = 4 for E on an A10 (21,770 MiB =
  94.5 %). The anchor runs K = 5 on the A10 class (working tree l. 1461-1463), with the pod map fixed
  from the regime-B pilot's measured peak. So the two campaigns use different packing rules for the
  same arm on the same card, or the 4,354 MiB basis is stale.
- l. 363, 859, 869, 979: "about 24 GPU pods at peak". Kai's figure is about 27.
- l. 9 and l. 359-362 ([DK4]): the code base "anchor pilot bundle 77f1ca4e". That is the regime-A
  bundle. If the Delta stays on it, the relabel rule "rep-A / rep-C at config sha X" fires the day the
  wave launches. If it moves to patch 0027 (`ebops_trace_every`), the X2/Z13 gate and the
  horizon-truncation check (launch gate 5) must cover the new key.

Impact: the design basis for selection, budget, packing and the anchor link contradicts a recorded
Kai decision. Fix: add a dated amendment choosing the Delta's trace regime (regime B to match the
anchor is the obvious default; if regime A, give the reason and label every pairing with the anchor
"cross-regime"). Rewrite l. 164, the selection rule and companion for traced epochs, launch gate 1
(name the pilot pod), the Reference rows, the amendment reason at l. 39-40, the timing basis, and the
pod ceiling. Rerun `budget.py` with the regime-B per-epoch cost labelled as a projection until the
regime-B canary reports. Align the E packing rule with the anchor's regime-B memory measurement, or
state why the two differ. Cascade to the experiment-log stub.

**A2. Arbiter #1 is only partly resolved: the family "no/yes" does not use the placebo, so it is not
calibrated against the confound the placebo was added to measure.** STUDY l. 579-582: t_i = mean g_i
/ (s_pool / √n_p,i) against a critical value simulated under the model "cells and placebo differ from
the replica only by independent noise". The placebo enters only through s_pool and the validity flag
(iv) (l. 654-658). l. 458-459 say the placebo "measures what pod, pack and run identity alone do to
g", but the test never subtracts that. The design has a named source of common offset between the
replica and every non-replica run. Replicas are never in a cell's pod (l. 144, 458). They run from
t = 0 in their own packs, configured to 1,000 or 2,000 epochs and read at the epoch-500 [A6] snapshot,
while cells and placebos are configured to 500 and read at `model_best.keras` (l. 536-538). [A6] is
"best-feasible-as-of-E" (anchor STUDY l. 2038), so the selection path matches in intent, but pack
composition, K, GPU node and start time differ systematically.

Stress test (common shift δ on every non-replica run, per-run σ = 1, so the SE of g at n = 4 is
0.707):

| δ | m | P(fixer "yes" given null cells) | P(placebo flag) | P("yes" and no flag) |
| --- | --- | --- | --- | --- |
| 0 | 12 | 0.099 | 0.030 | 0.088 |
| 0.5 | 12 | 0.297 | 0.070 | 0.241 |
| 0.707 | 12 | 0.412 | 0.113 | 0.311 |
| 0.5 | 40 | 0.310 | 0.035 | 0.278 |
| 0.707 | 40 | 0.422 | 0.062 | 0.364 |

A shift of 0.7 SE triples the false "yes" rate, and the validity flag catches it about 6-11 % of
the time. So "P(no | global null) = 0.90 per family by construction" (l. 92, 635) holds only if no
such offset exists, which is the assumption the placebo was added to remove.

The fix costs no power. Referencing the max-t to the placebo, d_i = g_i − g_P = cell − placebo (the
textbook Dunnett many-to-one with the placebo as control, pooled sd as now, critical value simulated
the same way), gives critical t 2.418 (m 12) and 2.799 (m 40). P("yes" | null) is 0.105 / 0.102 /
0.101 at δ 0 / 0.5 / 0.707 (m 12) and 0.093 / 0.096 / 0.098 (m 40). P(no | one +1-pt cell) is 0.498
/ 0.849 / 0.887 at σ 0.6 / 1.5 / 3.14 (m 12), against the fixer's 0.489 / 0.846 / 0.880. The replica
stays the pairing partner for g and for the ranking. The family test compares against the placebo
(or reports both, with the placebo-referenced one primary). Update l. 60 ("the placebo sits where
the cells sit" is then true), l. 89-96, 575-583, 632-640, 654-658, [DK7], `screen_null.py`, the
stub. If the designer keeps the replica-referenced test, the STUDY must state the no-common-offset
assumption beside every "0.90" and give the flag's power against δ.

**A3. G3′ is restored but has no resolving power, and the STUDY does not say so.** l. 568-572:
non-inferiority "lower 95 % bound on g > −0.3 pt", for M023, M024/M025 (read for cost) and
floor-family entries at 5M; "a non-inferior M023 goes to a synthesis check on `mulder`". At n = 4 on
the cell's own sd (df 3), with true g = 0 and ρ = 0 (40,000 reps), P(pass) is:

| per-run σ | P(pass) |
| --- | --- |
| 0.10 pt | 0.80 |
| 0.13 pt | 0.60 |
| 0.20 pt | 0.32 |
| 0.30 pt | 0.17 |
| 0.60 pt (anchor referral line) | 0.074 |
| 1.5 pt | 0.040 |
| 3.14 pt (archived spread) | 0.032 |

So a truly equal cell is declared non-inferior less than 8 % of the time at any spread the STUDY
expects (l. 495-498). M023's pre-registered question, which arbiter #4 restored for this reason, is
still effectively unanswerable. The K5 consequence is unreachable, and "not non-inferior" will be
read as "inferior". Precedent: arbiter #3 (resolving power at the measured spread, §6.3 Q4). The box
at l. 67-68 says "cannot … resolve 0.3 pt" in general but never names G3′. l. 569 does not say
whether the bound uses the cell's own sd (df 3, computed above) or the family-pooled sd, and the pass
rate differs between the two. Fix: state P(pass | g = 0) at σ 0.6 / 1.5 / 3.14 and the σ at which
G3′ has power (about 0.13 pt). Label the expected G3′ outcome "non-inferiority not shown at this n",
never "inferior". Name the sd. Say whether M023 goes to the zero-GPU synthesis check on `mulder`
regardless (the cost question is answered by synthesis, not accuracy), which is a Kai K5 item.

## Earlier findings, checked by name (arbiter v1 #1-#23)

| # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 | ranking-mode "no" cannot fire | **partial** | Dunnett line fires 0.90 under the no-offset null (reproduced); placebo not in the test, see A2 |
| 2 | winner's curse | resolved in text, one gap | companion, eligible count, τ, flag at l. 593-603; [L6] l. 886-892 names the cells. The flag has no null rate: B5. Regime B changes the eligible set: A1 |
| 3 | resolving power at 3.14 pt, stop line | resolved | l. 505-519 (±7.1 pt: t(0.975,3)/2 · 4.44 = 7.07); ceiling 1.3 pt l. 484-491, reproduced; guard l. 492-493 |
| 4 | DELTA departures | **partial** | change log l. 25-51 lists every amendment; G3′ l. 568, ⌈3n/4⌉ l. 408-418, R1 l. 293-298, cap l. 591, K6 l. 299, teachers l. 256-258; "as written in DELTA" appears only at l. 30 as a deletion note. G3′ restored without power: A3. Amendment reason at l. 39-40 now stale: A1 |
| 5 | missing pairs | resolved | l. 550-557, [D10] l. 813-815. Whether incomplete-pairs cells enter the max-t is unstated: C3 |
| 6 | ranking statistic | resolved, but against the arbiter's wording | arbiter fix 9: "LCB80 stays primary unless Kai amends DELTA §5.3"; STUDY makes mean g primary by orchestrator default ([DK6], l. 43-45, 575-578): B6 |
| 7 | E packing at K = 6 | **re-opened** | K from the canary (l. 335-343), but planning K = 5 violates the STUDY's own 90 % rule, and the anchor now runs K = 5 under regime B: A1 |
| 8 | always-on patches | resolved | X2 l. 278-282, launch gate 9 l. 349-351 |
| 9 | anchor config freeze | **re-opened** | relabel rule l. 359-362, but it fires at launch under regime B: A1 |
| 10 | anchor state stale | **re-opened** | l. 118-122 updated to c2f5447/e620173, stale again after Kai's [D15] answer: A1 |
| 11 | question vs rule | resolved | frontmatter l. 6, l. 75-88, stub Question line |
| 12 | floor-family package | resolved | l. 223-226, 584-590. Dunnett membership unstated: C3 |
| 13 | structural headroom | resolved | l. 563-565 |
| 14 | baseline tuning asymmetry | resolved | l. 104-108 |
| 15 | per-class AUC | resolved | l. 608-609, l. 770 |
| 16 | cheap-version long cells | resolved | l. 739-742; `budget.py` cheap reproduced |
| 17 | [D14] limitation | resolved | [L7] l. 893-896 |
| 18 | conventions rows | resolved | l. 770, 774-776 |
| 19 | [L1] attempt | resolved | l. 872-877 |
| 20 | contradicted null count | resolved | l. 644-645, reproduced 0.48 / 1.07 |
| 21 | replica seeds 1-8 | resolved (adopted [DK2]) | l. 228-240, 916-920 |
| 22 | binomial-SE argument | resolved | l. 498-500 |
| 23 | K6 and teachers as Kai items | resolved | [DK9] l. 966-970 |

C items #24-#32: applied as the fixer lists. Spot-checked C27 (318, reproduced), C28 (formula check,
but see B2), C29 (l. 442-445), C31 (l. 137-141, 588-589), C32 (box l. 62-73; `plan.md` dead ends).

## Category B (should address)

**B1. Kai's timing of the Delta launch is not the STUDY's.** decisions.md (working tree): "Delta at 10
after this campaign's epoch-500 readout". STUDY launch gate 1 (l. 307-314) and [DK4] (l. 837-840) say
launch waits for the pilot A rule only. Whether "this campaign's epoch-500 readout" means the pilot's
or production's decides whether [DK4] (launch without anchor-production snapshots) is compatible with
Kai's instruction. Fix: quote Kai's line in launch gate 1, and if it means production, drop [DK4]'s
"does not wait" or put it to Kai as a question. This could fold into A1's amendment.

**B2. The A/A placebo is not specified well enough to be A/A, and its determinism status is not
pre-registered.** (a) "arm A's config plus a no-op key (run identity only)" (l. 142-143). No
placebo or no-op key exists in the Delta series (`grep -rin "no-op|noop|placebo"` over
`campaigns/2026-09-26-delta/code` and `delta.json` finds only unrelated notes). The strict validator
refuses unknown keys (decisions.md, ml-engineer 2026-09-27 entry: "The strict validator refuses the
old `atlas_study` block by name"). Either the placebo cannot be generated as written, or its key
enters `config_sha256` or a seed derivation. Fix: state the mechanism (run name and W&B id only, no
config key; or a registered key excluded from `config_sha256`). Add a PREFLIGHT assertion that the
placebo and the replica at seed s have equal `digest_json(cfg)` apart from identity, equal init
`kernel_hashes`, and equal first-step loss on CPU. List the placebo under X2/Z13.
(b) Training is not run with op determinism: `enable_op_determinism` appears only in
`code/tree/campaigns/chang0926/evaluate_roc.py:115`; the deterministic runs are the CPU invariance
gates (`campaigns/2026-09-26-delta/code/PLAN_rebase.md` l. 32, 157). So the placebo's per-seed g is
expected to be non-zero only through GPU non-determinism and pod differences. Its size is unknown,
and it bounds how informative the A/A row is. l. 524-526 and l. 660-663 call an exactly zero
placebo g "a red flag (the runs did not vary)". That wording fits across-seed spread; it does not
fit an identical-config pair at the same seed, where zero is what a deterministic stack gives. Fix:
pre-register that GPU training is expected to be non-deterministic (cite the grep). Say that a zero
placebo g would mean the stack is deterministic, in which case the placebo measures nothing, must
not enter s_pool, and the family test falls back to the replica reference with the A2 assumption
stated.

**B3. Heterogeneous variances break the "0.90 by construction" claim.** The pooled-sd max-t
(l. 575-582) assumes every cell has the replica's seed variance. Levers such as Bop, the STE
variants and LR changes (M018-M020, M028, M029) can change it. Stress test: one null cell with
k times the others' sd gives P("yes" | null) 0.117 / 0.150 (m 12, k 2 / 3) and 0.120 / 0.161 (m 40),
and that single cell produces most of the false "yes" (P(it exceeds) 0.116 at m 12, k 3). Fix:
report a per-family variance-heterogeneity statistic (for example, the ratio of the largest cell sd
to the pooled sd, with its null distribution from the same simulation). Pre-register the fallback:
any cell named "above the replica" must also clear its own-sd t at the same α, or it is labelled
"driven by variance".

**B4. The "95 % interval on the family-pooled paired sd, df = Σ(n_p − 1)" (l. 576-577) under-covers.**
The shared replica term contributes only n − 1 = 3 degrees of freedom to every residual, so the
effective df is far below Σ(n_p − 1). Simulated marginal coverage of the stated interval under the
null is 0.933 at both m = 12 (t(39) = 2.023) and m = 40 (t(123) = 1.979), with 2.70 intervals
excluding 0 per 40 against a nominal 2.00. Fix: take the interval quantile from the same
shared-replica simulation, or label it "nominal 95 %, simulated coverage 0.93". The same applies to
G3 at l. 565-567 where it uses the pooled sd.

**B5. The rank-move flag has no null rate and will flag most of the 5M list.** Flag: a rank move of
more than 5 places (5M) or 3 places (350k), or a crossing of rank 12 (l. 598-601). Null simulation,
with the companion correlated with the primary at c across cells: 5M flags 25.2 / 18.2 / 8.5 of 40
cells at c = 0.5 / 0.8 / 0.95; 350k flags 3.8 / 1.6 / 0.2 of 12. At 5M, crossing the rank-12 line
alone flags about a fifth of the list even at c = 0.95. "A flagged cell goes to Kai with the flag"
then carries no information. This is the defect arbiter #20 fixed for the contradicted list. Fix:
print the expected null flag count per family (from the simulation, as a function of the observed
primary-companion correlation), or flag on a threshold calibrated to about 1 expected null flag per
family.

**B6. [DK6] reverses arbiter fix 9's default.** Arbiter fix 9: "LCB80 stays primary unless Kai amends
DELTA §5.3". STUDY l. 43-45, 575-578 and [DK6] make mean g primary by orchestrator default and
describe it as an amendment of DELTA §5.3, which is a pre-registration Kai owns. `rank_sim.py`
supports mean g (reproduced), but the arbiter placed that choice with Kai (item 7). [DK7]'s Dunnett
line is the same pattern (fixer report, "remains: the arbiter should confirm"). Fix: keep DELTA's
LCB80 as the primary until Kai signs [DK6], with mean g beside it, or have the arbiter record that
it accepts the reversal. The same goes for [DK7].

**B7. The E planning value K = 5 is used where the STUDY's own rule rejects it.** l. 729-731 and
[DK11] l. 857-859, 982-983 say K = 5 is 94.5 % of an A10 and the canary is expected to return K = 4,
yet `budget.py` and every wall-clock row plan at K = 5. The replica epoch-500 gate time (25.2 h at
r = 1) and the wall clock depend on it. Resolve this together with A1 (the anchor's K = 5 under
regime B). Otherwise plan at K = 4 and give the K = 5 row as the alternative.

## Category C (suggestions)

**C1.** The wave-level "no" requires "no" in each family (l. 632-634), so under the global null
it fires with probability about 0.90² = 0.81, not 0.90. Say so beside the per-family figure.

**C2.** Chance baselines mix m = 43 (l. 69-70, 511-513: 0.018, `rank_sim.py`) and m = 40 (l. 486-487:
0.022, `screen_null.py`). The 5M ranked list has 40 G3 cells. Use 40 in the box and the fidelity
table, or label the 43-row "includes the 3 deferred cells".

**C3.** State the Dunnett family membership. At 350k, `screen_null.py` uses m = 12, the paired
single-lever list. Say that the floor-family Welch package and the incomplete-pairs cells (n_p < n)
are outside the max-t, and whether the critical value is re-simulated at the observed n_p per cell
(l. 579-582 mentions n_p,i but the simulation uses one n).

**C4.** l. 641-643: "95 % interval on g lies entirely below 0". Name the sd (own or pooled; see B4).

**C5.** The sd_rep ceiling (l. 484-491) is a point estimate at df ≤ 7. At a true σ of 1.0 pt,
P(sample sd > 1.3) = P(χ²₇ > 11.8) ≈ 0.11. One sentence on the chance of a false pause (and of a
false pass at σ 1.6) would help Kai read the gate.

## Competing-group question

A group running this screen next month would have: (1) a family-level test referenced to the
in-family A/A cell, calibrated against pod/pack/start-time offsets at no power cost (A2); (2) the
screen run at the anchor's actual production trace regime, so that its gaps transfer and its budget
is right (A1); (3) a stated power for the non-inferiority question, or the synthesis check that
actually answers M023's cost question (A3); (4) an A/A cell whose identity is verified at PREFLIGHT,
with a known non-determinism floor (B2). None of these has a justification in the STUDY for being
absent. Items 1-3 are Category A above.

## Disputed facts for the investigator

None. [A6] is "best-feasible-as-of-E" (anchor STUDY l. 2038), so the replica-at-500 and cell
`model_best` readouts follow the same rule. Regime B was traced to decisions.md (working tree), commit
5276ee0 and the anchor STUDY working tree l. 1396-1420. Neither needs an investigator.
