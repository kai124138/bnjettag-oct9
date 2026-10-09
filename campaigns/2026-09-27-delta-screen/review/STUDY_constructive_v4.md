# STUDY review, constructive, v4: 2026-09-27-delta-screen (Delta wave 2)

Reviewer: constructive-reviewer, fresh context, 2026-09-27. Artifact: `STUDY.md` (1,681 lines,
iteration 4, after fixer v3). Read: `docs/methodology/06-review.md`, `03-phases.md` Phase 1,
`review/STUDY_validators_v4.txt`, `screen_null.py`, `rank_sim.py`, `budget.py`, my own
`review/STUDY_constructive_v3.md` (to track earlier findings by name), the newest entries of
`.claude/memory/experiment-log.md`, `.claude/memory/research-log.md` l. 22-43, and
`research/screen-design-literature.md`. Not read: the physics or critical files of any iteration.

**Verdict in one line. No Category A.** Three B items, all text-level pre-registrations with no
GPU cost. B1 is the one that matters. The pause gate reads the wrong variance. The seed main
effect cancels from the ranking and the family test, but it does not cancel from sd_rep. At the
only measured spread the gate labels the whole wave "descriptive" with probability 0.99, even in
a case where the ranking is essentially perfect. Four C items.

## Reproduced (evidence for the [+] items)

- `python3 screen_null.py` (seed 20260927, 9 s) reproduces every number the STUDY quotes from
  §13-§17:
  - Critical values: 4.284 / 6.585 at m = 11 / 37 (n = 4), and 6.733 / 12.290 at n = 3.
  - False "yes": 0.099-0.108 under equal and unequal spread; 0.036-0.082 under two-mode seeds.
    At n = 3 two-mode it reaches 0.232 (m = 37).
  - Power for one +1-pt cell: 0.214 / 0.087 / 0.051 / 0.026 (m = 11) and 0.077 / 0.030 / 0.016 /
    0.007 (m = 37).
  - Ranking multiplier 2.168 / 2.136. Placebo-wording P(no | null) 0.084 / 0.026.
  - P(pause) with 8 seeds: 0.000 / 0.106 / 0.629 / 0.889 / 0.991 at σ 0.6 / 1.0 / 1.5 / 2.0 /
    3.14.
  - Recovery at the ceiling (5M) 0.57 at 1.3 pt and 0.52 at 1.4 pt; the 350k criterion holds to
    3.0 pt.
  - Top-k extension at σ 1.0 / 1.3: 0.77 → 0.87 and 0.57 → 0.69.
  - G2 false rescue: 0.038 / 0.121 / 0.104.
  - Rank-move null counts, e.g. m = 37: T 10 at r 0.95 gives 0.6, T 15 at r 0.9 gives 0.3. ✓
- `python3 rank_sim.py` reproduces the m = 37 table (STUDY l. 802-806): 0.99 / 0.97, 0.47 / 0.40,
  0.16 / 0.14, 0.74 / 0.66 and the ρ = 0.5 columns. ✓
- `python3 budget.py` reproduces:
  - (4, 4): 302 runs, 176,000 run-epochs, 1,112.2 / 1,959.0 pod-hours, 5.4 / 9.2 d, 318
    retraces.
  - Extension, both families: 390 runs, 1,390.3 / 2,439.3 pod-hours.
  - Paused: 350k 286, 5M 270, both 254 runs.
  - Packable today: 240 runs (212 cell + 8 placebo + 20 replica), 142,000 run-epochs, 897.4 /
    1,592.5 pod-hours.
  - Cheap version: 129 runs, 79,500 run-epochs.
  - [DK18] follow-up: 84 runs, 366.5 pod-hours. ✓
- New script: `review/constructive_v4_modes.py` (seed 4040927). Design arithmetic, seeded Monte
  Carlo, not a result. Its numbers are used in B1 and B3.

## What is done well

- [+] **The design is honest about its likely branch.** The box (l. 158-163) and the Seeds
  section (l. 745-751, 769-781) say a pause is nearly certain at the only measured spread
  (P = 0.99), give the exact chi-square rows and label them "a guide, not a bound" because seeds
  may be two-mode. It does not pretend the (4, 4) ranking branch is the plan. A reader of the box
  takes away the right sentence.
- [+] **One family-test reference.** Withdrawing the bit-identical replica switch (change log
  l. 102-108) removed the last assumed-not-measured condition from the test. The test is now the
  same arithmetic in every branch, and the determinism probe only decides how the placebo row
  reads (l. 948-958). My v3 B2 is resolved.
- [+] **Ranked list = family-test set.** Taking M015, M031 and M032 out of both (l. 896-908,
  959-966) and re-simulating every m-dependent value at 11 / 37 is the right fix. The STUDY did
  not keep the design-grid values, and all of them reproduce.
- [+] **The top-k extension is well specified.** Its five limits are stated: H-500 only;
  placebos and the family test stay on seeds 1-4 because those seeds selected the cells; the
  seeds-5-8 mean is the one selection-free estimate; mixed-n ordering; lost seeds (l. 708-730).
  The selection-on-seeds-1-4 point is exactly right. My v3 B1 is resolved.
- [+] **5M constraint-active readout** (l. 601-614). A fixed three-number rule on rep-C, read
  before any cell. It holds nothing back and changes only labels and a priced follow-up (84
  runs, 366.5 pod-hours, reproduced). It turns an unknown into a pre-registered measurement.
- [+] **The floor-family G2 is labelled for what it is.** Every traced floor-family entry meets
  the "≤ ½ of A07's floor" trigger (l. 871-879), so the STUDY says a rescue is expected from
  arithmetic and points the reader to the cross-architecture accuracy instead. The null
  false-rescue rates sit beside it.
- [+] **The literature is in the record.** `research-log.md` l. 22-43 has dated, URL-backed
  entries. The STUDY answers each point (l. 1657-1681), including the Bouthillier caveat (abstract
  only, no number used).
- [+] **Packable-today matches the manifests** (l. 1175-1184): 212 cells + 8 placebos in
  `delta_w2_cells_packs.json`, 20 replicas in `delta_w2_t0_packs.json`, and 240 runs in
  `budget.py`.

## Category A

None.

## Category B

### B1. The pause gate and the "descriptive" label read the total seed sd, but the ranking's resolution is set by the cell × seed interaction sd

- **Current state.** Three decisions hang on sd_rep: the pause at 1.3 pt ([DK8], l. 734-751), the
  "descriptive, family paused" label with no family test ([DK17], l. 752-765), and the [DK16]
  extension band (l. 708-730). sd_rep is the across-seed sd of the replica alone: 8 seeds, df ≤ 7,
  read before any cell runs. The STUDY's own argument (l. 809-811) is that "the replica term is
  common to every cell of a family at seed s, so it cancels from the order of the means". The same
  holds for any seed-level component a_s that every configuration shares at seed s (init, data
  order, a seed-determined training mode). All m cells run on seeds 1-4, so a_s cancels from the
  order of the cell means, and it cancels in d = cell − placebo too. The resolution is set by
  σ·√(1 − ρ), the cell × seed interaction. It is not set by σ, which is what sd_rep measures.
  `rank_sim.py` already shows this: at σ 3.14, recovery is 0.16 at ρ = 0 and 0.26 at ρ = 0.5
  (l. 806). The gate ignores it.
- **Evidence** (`review/constructive_v4_modes.py`). The model is two-mode seeds like the
  archived 67.18 / 72.64 / 67.21 %: a 5.4-pt jump, 0.3-pt sd within a mode, P(low mode) 1/3, and
  two mechanisms with the same per-run sd.

  | mechanism | P(pause) | 5M recovery (3 × +1 pt in top 12 of 37, n 4) | median sd_rep | median interaction sd |
  | --- | ---: | ---: | ---: | ---: |
  | mode set by the seed, shared by every config | 0.96 | **1.00** | 2.67 pt | **0.30 pt** |
  | mode drawn independently per run | 0.96 | 0.19 | 2.67 pt | 2.57 pt |

  With Gaussian seeds and a shared share ρ, at σ 1.5 pt: P(pause) is 0.63 in every row, while
  recovery is 0.47 / 0.73 / 0.97 at ρ 0 / 0.5 / 0.8. The interaction sd is 1.50 / 1.06 / 0.67,
  which equals σ√(1 − ρ). The gate cannot tell these cases apart. Under the likely branch it
  labels a ranking with recovery 1.00 as "descriptive, not a K3a ranking" and withholds the
  family test.

  The only record on pairing (negative cross-arm correlations at N = 8, l. 1022-1027) argues
  against a large shared term. Pham et al. and Zhuang et al. (research-log l. 34-38) argue that
  GPU tooling alone decorrelates runs. So the independent row may well be the truth. That is not
  known, though, and the design already measures it: ρ̂ is printed per family (l. 1026-1027).
- **Improved state.**
  - Keep the pre-launch sd_rep read for what only it can do: the compute decisions (n in
    significance mode, and which cells launch under [DK17]).
  - Move the *labelling* decisions to the n = 4 readout, and read them on the two-way cell ×
    seed residual sd s_int of the family's cell accuracy matrix. That is the residual after
    removing cell and seed means, with df (m − 1)(n − 1) = 30 at 350k and 108 at 5M, against
    df 7 for sd_rep. The labelling decisions are: "ranked" versus "descriptive"; whether the
    family test is read (see also B2); and the [DK16] band for the top-k extension.
  - The [DK16] extension is released after the n = 4 readout anyway (l. 710-711, 1165-1166), so
    reading its band on s_int costs nothing.
  - The thresholds need no re-derivation. The 1.3 / 1.4 pt (5M) and 3.0 pt (350k) recovery
    criteria were simulated at ρ = 0 (`screen_null.py` §3, §15), where σ is exactly the
    interaction sd. Only the estimator changes.
  - Print sd_rep, s_int and ρ̂ side by side at the readout.
- **Why.** At the archived spread this is the difference between a wave whose main output is
  labelled "descriptive" with probability 0.99 and a wave whose label follows the noise that
  actually limits it. Extra seeds cannot fix a high σ_eff. The extension beyond the ceiling gains
  little: 0.16 → 0.20 at σ 3.14 and 0.30 → 0.40 at σ 2.0 (5M, same script). So measuring σ_eff
  correctly is the useful lever, not more GPU. The pause saves little compute in any case:
  302 → 286 runs when only 350k pauses (only the baselines and probes drop), and 302 → 254 when
  both pause (`budget.py`). The gate is in practice a labelling rule, so it should read the
  quantity the label is about.
- **Not a post-hoc rule.** s_int is a variance estimate that reads no effect size and no cell
  order. Written now, it is pre-registered like sd_rep (§6.3.3, §6.7).
- **Caveat, once.** A lever that changes mode probability adds cell-specific seed structure,
  which inflates s_int. The error is toward "descriptive", which is conservative.
- **Effort.** Low. One paragraph in Seeds and in [DK8] / [DK16] / [DK17], plus a two-way residual
  at VERIFY.

### B2. A paused family reads no family test, although the test is calibrated at any σ and its inputs run anyway

- **Current state.** On a pause "no family test is read" (l. 757-758, 947; [DK17] l. 1585-1586).
  The paused family still runs its placebo and its T0/T0a/T1 cells at n = 4 (l. 752-757;
  `budget.py` lists the cells kept).
- **Improved state.** Read the placebo-referenced own-sd max-t in a paused family too. Re-simulate
  its critical value at the paused family's actual m (the rule at l. 902-903 already does this).
  Report it with the same "a 'no' is not evidence of absence" sentence and "descriptive family"
  in its header.
- **Why.** Own-sd t is scale-invariant. Its calibration rows (§15: 0.099-0.108, and 0.036-0.082
  two-mode at n = 4) do not depend on σ, so the pause does not change the test's size, only its
  power. Withholding a calibrated test that costs nothing discards the one family-wise answer the
  paused wave can give. If B1 is adopted, most of this item follows from it. It stands alone if B1
  is not.
- **Effort.** Low (text).

### B3. The dominant uncertainty (two-mode seeds) is modelled only as a calibration nuisance; the design already computes what would identify it and does not use it

- **Current state.** Two-mode seeds appear in the sizing (l. 236, 772) and in the family-test
  scenario rows (l. 941-946). The readout already computes the anchor's collapse label per seed
  (l. 1012-1015) and the full cell × seed accuracy matrix. Nothing reads them as a mode: mean g at
  n = 4 mixes "the lever shifts accuracy within a mode" with "the lever moves seeds between modes".
  If the archived 5.4-pt jump recurs, a single seed changing mode moves a 4-seed mean by 1.35 pt,
  more than the +1-pt effects the design is sized to find.
- **Improved state.** Pre-register a fixed rule at the replica epoch-500 gate, on the 8 replica
  values only and before any cell runs:
  - Is the family bimodal? One example: the largest gap between sorted values exceeds 3× the
    pooled within-cluster sd, with at least 2 seeds on each side.
  - If so, fix a mode threshold then.
  - Per cell, report n_low of n (with the replica's and the placebo's beside it) and the
    within-mode paired g beside mean g.
  - Report per family whether the collapse label coincides with the low mode, and whether the
    low mode is seed-shared across cells (the same seeds low in most cells). That last check is
    what B1's ρ̂ / s_int split measures.
  - None of this changes the primary list.
- **Why.** A stability lever (T0) is worth something precisely if it moves seeds out of the low
  mode. That shows as n_low, not as a resolved mean g. The data already exist; this is a readout
  rule. It also tells VERIFY whether the spread is a symptom of a training instability (an
  identified mode) or diffuse noise, which is the question §6 asks about the dominant
  uncertainty.
- **Effort.** Low (text now; a few lines at VERIFY).

## Category C

- **C1. Question length.** The frontmatter `question:` (l. 6) is one sentence of about 230 words.
  `03-phases.md` Phase 1 asks for "one sentence each" for question and null, readable as such.
  The "In one line" (l. 145-147) is that sentence. Put it in the frontmatter and leave the full
  specification to the Question section. Effort: low.
- **C2. Significance-mode machinery in the main line.** k_joint, BH m, g0 and the n = 6 / 8
  thresholds (l. 695-707, 894-895, 1003-1006) need sd_rep ≤ 0.044-0.134 pt. That is below any
  spread this project has recorded, including the 0.19-pt lower bracket, and the STUDY says it is
  not expected to arm (l. 769-781). Move it to an appendix, keeping a one-line pointer where it
  would apply. That shortens the main line of a 24,788-word STUDY (`prose_lint`) by several pages
  without loss. Effort: low.
- **C3. Floor-family G2: "expected", not "tautological".** The label "structural, by construction"
  (l. 871-879) slightly overstates. Headroom is necessary for feasibility but not sufficient:
  A07-350 itself has not yet produced a run (OOM ×3, l. 232), and non-degeneracy (c) is not
  guaranteed. "Expected from floor arithmetic" is the accurate phrase. The Question block
  (l. 189-196) should then name the cross-architecture accuracy as the informative floor-family
  quantity and keep G2 as the feasibility check. Effort: low.
- **C4. Seed convention and Dodge et al.** `order_seed = f(s)` ties init and data order to one
  seed (l. 1667-1669). If B3 finds a seed-shared low mode, the natural follow-up is a small
  factorial on replica seeds (init fixed, order varied, and the reverse) to find which one sets
  the mode. Record that as the follow-up now, so VERIFY does not have to invent it. Effort: low
  (text); the factorial itself is a separate campaign.

## Earlier findings (constructive v3), tracked

| v3 item | status in v4 | evidence |
| --- | --- | --- |
| B1 ranking-mode n rule using priced rows / replica seeds 5-8 | resolved | [DK16] l. 708-730; `screen_null.py` §16 reproduced |
| B2 single placebo reference, offset measured not assumed | resolved | change log l. 102-108; Selection rule l. 920-958 |
| C1 variance moderation | recorded as a dead end | l. 1506-1507, 1675-1676 (`plan.md`) |
| C2 [L8] contradiction | resolved | [L8] l. 1432-1435 matches l. 280-282, 959-966 |
| C3 review trail in body | resolved | grep after l. 144 finds only label-provenance mentions (l. 1269, 1326, 1341, 1441, 1676) |
| C4 literature note | resolved | `research-log.md` l. 22-43; STUDY l. 1657-1681 |
| C5 lower-bracket label | resolved | l. 236, 776 |
| C6 rank-move r centred per cell | resolved | l. 985-988 |
| C7 candidate code base | resolved | frontmatter l. 9 (f2107a04 / e90327d4) |
| C8 box powers at actual m | resolved | l. 168-173 |

## Answers to 06-review §6.3

1. **Conventions.** Implemented or declared as deviations with reasons: the 90/10 split,
   accuracy as the selection metric, the flat-gap rule (l. 1244-1264).
2. **Reference table.** Present and sourced. It correctly has no comparand for a screen that is
   never quoted (l. 222-239).
3. **What a competing group would have.** A noise gate on the quantity that limits the ranking
   (B1), and a mode-aware estimand for a population the STUDY itself calls two-mode (B3).
4. **Honest uncertainties and resolving power.** Honest in both directions. The pause
   probability, the near-zero family-test power and the chance-level recovery at 3.14 pt are all
   stated. The resolving-power statement uses σ where σ√(1 − ρ) is the operative quantity (B1).
   That does not overstate anything, but it can mislabel the output.
5. **Limitations with attempts.** [L1], [L6], [L7] and G3′ each carry an attempt or a power
   statement. No limitation is accepted bare.
6. **Context.** Not applicable at STUDY (no results).

## Summary for the arbiter

No Category A. Keep:
- the "can and cannot say" box;
- the placebo-referenced own-sd family test with its scenario rows;
- the single reference;
- the extension's five limits;
- the 5M constraint-active readout;
- the replica-loss rule;
- the budget, which reproduces exactly.

B1 is the substantive item. The pre-launch sd_rep gate cannot distinguish a seed-shared spread
(which cancels, recovery 1.00) from an independent one (recovery 0.19): both pause with
probability 0.96. Read the labelling decisions on the cell × seed residual at the n = 4 readout,
with the thresholds already simulated. B2 and B3 are readout rules on data the design already
produces. All three are text and cost no GPU.
