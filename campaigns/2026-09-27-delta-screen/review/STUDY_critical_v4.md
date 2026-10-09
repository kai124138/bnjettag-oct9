# STUDY critical review v4: 2026-09-27-delta-screen (Delta wave 2)

Critical reviewer, fresh context, 2026-09-27. Panel mode, re-review, iteration n = 4. No verdict
(the arbiter issues it).

Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (1,681 lines, working tree after fixer v3,
commit 0b11518) with `plan.md`, `budget.py` (v4), `screen_null.py` (v3, §1-§17), `rank_sim.py`,
`research/screen-design-literature.md`. Also read: `review/STUDY_arbiter_v3.md`,
`review/STUDY_fixer_v3.md`, `review/STUDY_validators_v4.txt`, `.claude/memory/decisions.md` top
entries, the experiment-log stub (`.claude/memory/experiment-log.md` l. 11-16), the
`research-log.md` head, `campaigns/2026-09-26-delta/delta.json` (pairing fields of M001, M006,
M009, M027, M046), the anchor tree's `bnhgq2/ablation.py` (β logged per epoch, l. 778-786).

## Validator output (verbatim)

```
STUDY validators v4 (2026-09-27 20:23)
No mechanical STUDY validator exists; prose_lint on STUDY.md:

Desktop/bnjettag/campaigns/2026-09-27-delta-screen/STUDY.md  —  score 0, reads human
  24788 words · 592 sentences · mean 27 words (σ=21.0) · 12% bullets · 15 em-dashes
```

No line is A-marked. Nothing is Category A by the validator rule.

## What does not apply at this phase

- Figure and array sanity: no arrays and no results exist (validation-only screen, not
  launched). No AUC, ROC, eBOP or csynth number to check. Not applicable.
- `tools/plot_check.py`: the STUDY has no figures and no figure scripts. Not applicable.
- `tools/prose_lint.py` at REPORT: not this phase (the STUDY-phase run is quoted above).

## Recomputed (design arithmetic, nothing quotable)

- `uv run --with numpy,scipy python screen_null.py` (seed 20260927), all sections re-run:
  - §13: own-sd critical values 4.284 / 6.585 (m 11 / 37, n 4) and 6.733 / 12.290 (n 3).
    STUDY l. 924-925 and l. 639: 4.28 / 6.59 and 6.73 / 12.29. Match.
  - §14: P(sd_rep > 1.3 pt) with 8 seeds 0.000 / 0.106 / 0.629 / 0.889 / 0.991 at σ 0.6 / 1.0 /
    1.5 / 2.0 / 3.14; with 6 seeds 0.000 / 0.133 / 0.585 / 0.833 / 0.973. STUDY l. 745-747 and
    box l. 159-160. Match.
  - §15, m 11: false "yes" 0.103 (equal), 0.102 / 0.102 / 0.106 (one cell 3×, 25 % 2×, 25 % 3×),
    0.052 / 0.036 / 0.042 (two-mode), 0.102 / 0.100 (offset), 0.099 (near-deterministic).
    m 37: 0.101, 0.099 / 0.102 / 0.108, 0.051 / 0.082 / 0.063, 0.099 / 0.099, 0.097. STUDY
    l. 939-943. Match. Power 0.214 / 0.087 / 0.051 / 0.026 (m 11) and 0.077 / 0.030 / 0.016 /
    0.007 (m 37). STUDY l. 937-938 and box l. 171-172. Match. Multiplier 2.168 / 2.136 (nominal t
    covers 0.936 / 0.933). STUDY l. 913-914. Match. ρ̂ null −0.34 / +0.34 and −0.18 / +0.18,
    unpaired 2.880 / 3.590, rejected wording 0.084 / 0.026. STUDY l. 1027, 1030, 207. Match.
  - §15 rank-move null counts. The T rule ("smallest grid T with null count ≤ 1.0 at the band's
    lower edge") gives these values. 350k: r 0.9, T 2 1.6 → T 3 0.7; r 0.7, T 4 1.2 → T 5 0.6;
    r 0.5, T 5 1.2 → T 6 0.6. 5M: r 0.95, T 8 1.6 → T 10 0.6; r 0.9, T 12 1.1 → T 15 0.3.
    STUDY l. 990-992. Match.
  - §15 recovery: 5M 0.57 at 1.3 pt and 0.52 at 1.4 (largest grid σ with ≥ 0.5 is 1.4); 350k
    0.79 at 1.3 and 0.50 at 3.0 (the grid end). STUDY l. 737-740. Match.
  - §16 extension: 5M 0.77 / 0.87 / 0.90 at σ 1.0 and 0.57 / 0.69 / 0.72 at 1.3; 350k 0.89 /
    0.96 / 0.95 and 0.79 / 0.90 / 0.87. STUDY l. 721-724. Match. The code (l. 330-336 of
    `screen_null.py`) orders the extended top 16 by 8-seed mean and takes the top 12 from them,
    which is limit (4) at STUDY l. 718-720.
  - §17: 0.038 / 0.121 / 0.104 per entry (× 7: 0.27 / 0.85 / 0.73); k_base 0 or 1: 0.312 / 0.738 /
    0.948; k_base 2: 0.062 / 0.316 / 0.656. STUDY l. 190-193 and l. 867-871. Match.
- `rank_sim.py`, m = 37 block: chance 0.0283. Mean-g / LCB80: σ 0.6 0.99 / 0.97; σ 1.5 0.47 / 0.40
  (ρ 0) and 0.73 / 0.65 (ρ 0.5); σ 3.14 0.16 / 0.14, 0.26 / 0.22, +3 pt 0.74 / 0.66 and 0.94 /
  0.90. STUDY table l. 802-806. Match.
- `python3 budget.py` (v4): (4, 4) 302 runs, 176,000 run-epochs, 1,112.2 / 1,959.0 pod-hours,
  5.4 / 9.2 d, 318 certifications. Packable today 240 (212 + 8 + 20 + 0), 142,000, 897.4 /
  1,592.5, 4.5 / 7.9 d, 256. Extension, both families: 390, 220,000, 1,390.3 / 2,439.3, 6.7 /
  11.6 d, 406. 5M only 366; 350k only 326. Pause: 350k 286 / 168,000; 5M 270 / 160,000; both
  254 / 152,000 / 960.6 / 1,706.2 / 4.6 / 8.2 d. [DK18] follow-up 84 runs, 58,000, 366.5, 2.6 d.
  STUDY Budget l. 1105-1117, 1151-1163, 1179-1181; [DK1], [DK16]-[DK18] rows. Match. Placebo check
  (l. 1187): 2 × 4 × 500 × 22.75 / 3,600 = 25.3 pod-hours at r = 1; at r = 2, 12.6 + 25.3 =
  37.9. Match.
- Completeness arithmetic: 68 cells = 23 (350k) + 1 (1.4M) + 44 (5M), `budget.py` line 1. 350k:
  12 accuracy on A (11 at H 500 + M015) + M050 + 3 probes + 7 floor family = 23. 5M: 44 − 4
  baselines = 40 with G3; 40 − 3 long-horizon = 37. 272 cell runs (68 × 4) + 8 + 20 + 2 = 302.
  Extension +88 = 16 × 4 + 6 × 4. [DK18] 18 entries = M017-M026 (10) + M028-M034 (7) + M037. All
  consistent. The 37 contains two cells that `delta.json` pairs Welch by construction (B1).

## Earlier findings, by name (arbiter v3 fixes #1-#10 and C rows 11-26)

| v3 # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 (B) | placebo "only `name`" | **resolved** | grep `only \`name\`` / `another \`name\`` / `run name` over STUDY.md and plan.md: the only hit is l. 267, the W&B run name in the Arms mechanism (correct). Change log l. 84-87, Question l. 181-182, [DK7] l. 1336-1340 and the stub's Design line all carry the key set and the assertion |
| 2 (B) | one family-test reference; probe scope | **resolved** | Family test l. 920-921: "the family's placebo, in every case". Two readings l. 948-958 read the placebo row only. Probe l. 518-529: E and A07, two pods of one product, 21 epochs, traced set named (1, 10, 20, 21 staged; 10, 20, 21 committed; PREFLIGHT prints), weight hashes and per-epoch losses, "changes nothing in the family test". Check (iv) sd-0 rule and flag rule l. 1079-1083; formula check l. 1087-1092. 4.43 / 6.79 / 0.261 / 0.258 survive only in the v4 change-log line that records the withdrawal (l. 105) |
| 3 (B) | packable today 268 → 240 | **resolved** | `budget.py` prints 240 (212 + 8 + 20); STUDY l. 1179-1184 cites GATES §6 l. 836-842 and both packs JSONs; [DK1] l. 1452; plan.md l. 89 tagged superseded. Gates 3 and 13 agree: l. 465-467, 490-494 ("the one statement of that rule"), 557-558 |
| 4 (B) | long-horizon cells out of the ranked list | **resolved as asked; residual B1** | Lists l. 959-967, Families l. 899-906, s_pool l. 911-912, [L8] l. 1432-1435, Arms l. 280-282 now agree. Re-simulated at m 11 / 37 (numbers above). Keep-looking residual: the 37 still holds two Welch-by-construction cells (B1) |
| 5 (B) | rank-move r centred per cell | **resolved** | l. 985-989; T values checked above |
| 6 (B) | literature note | **resolved** | Cited with owner at l. 1657-1681; each point applied or answered. The note's §5 stale "0.10 vs 0.26" now carries a dated annotation (note l. 324-330). The four research-log lines are in `.claude/memory/research-log.md` l. 23-39 |
| 7 (B) | floor-family null rate, numeric trigger | **resolved; residual B3** | l. 189-196 and l. 865-879: rates printed, trigger "≤ ½ of 343,053 = 171,526.5", M001 171,526 flagged as exactly half (171,526 / 343,053 = 0.4999985). Residual: the pause default still justifies the floor family by G2 (B3) |
| 8 (B) | 5M constraint-active readout | **resolved at family level; residual B4** | Controls l. 601-614, Falsifier (vi) l. 1084-1086, [L7] l. 1428-1431, [DK18] rows. β is logged per epoch (anchor `ablation.py:786`, `'beta': pid.beta`), so (c) can be read. Residuals: per-cell labelling (B4), thresholds and tolerance (C1) |
| 9 (B) | pause is a likely branch | **resolved as asked; residual B2** | P(pause) printed (box l. 158-163, Seeds l. 745-751); [DK17] default with costs; (4, 4) labelled "taken only if both families pass" (l. 391-392, 1105, [DK1]); 0.19-pt bracket labelled (l. 236, 775-778). Residual: the default is close to a full launch, and the Falsifier has no reading for it (B2) |
| 10 (B) | ranking-mode n rule | **resolved** | [DK16] l. 708-730, 1371-1374, 1570-1581: limits (1)-(5), extension priced with `budget.py` (+88 runs, 1,390.3 / 2,439.3 pod-hours, 6.7 / 11.6 d), recovery from §16. Residual C2 (fixed k at a smaller m) |
| 11-26 (C) | crit C1-C8, phys C1-C4, cons C1/C3/C5/C7/C8 | **applied** | Crit C1 l. 636-642; C2 l. 823-830; C3 frontmatter l. 9; C4 l. 1232-1234; C5 l. 278, 958; C6 l. 916; C7 l. 1166-1169; C8 plan.md l. 18, 30, 36. Phys C1 l. 929-930; C2 l. 791-792; C3 l. 206-208; C4 l. 926-928, 1259. Cons C1 plan.md l. 130-136; C3: body after l. 144 has no arbiter/fixer cycle references except the [DK] preamble (l. 1269, 1441) and "the review's range" (l. 1515); C5 l. 236; C8 via fix 4 |

Decision-label traceability: [D8] carries a dated v4 amendment (l. 1292-1294); [DK7] is rewritten
to match the body (l. 1336-1346); [L8] rewritten (l. 1432-1435); [D16] amended v3 (dated); [DK6]
cites Kai's decisions.md entry. No [D] label is silently replaced. Kai's two decisions of
2026-09-27 (regime-B pilot readout as launch gate 1; mean g primary) are implemented at l. 468-481,
909-919 and [DK6].

## Findings

### Category A

None.

### Category B

**B1. Two Welch-by-construction cells sit inside the "paired" 5M ranked list; the paired bound is
35, not 37.**
- Where: Families l. 899-901 ("the ranked list and the family test's m cells are the same set,
  the paired single-lever list at H = 500 only … at 5M the G3 cells on C that run minus M015,
  M031, M032, so m ≤ 37"). Outside the list, l. 904-905: "cells whose paired-if-hash check failed
  (Welch)". Lists l. 959-961. Box l. 150. Counts l. 388-389.
- Evidence: `delta.json` pairing fields: M006 "unpaired (Welch): no shared attention tensors";
  M009 "unpaired (Welch): different inputs; crosses N by design, labelled". Both run "on C" at 5M
  (Arms table l. 321, 324) and both are among the 40 G3 cells. The STUDY's own rule puts
  Welch cells outside the ranked list, so the paired ranked list at 5M holds at most 35 cells.
  If M009 is ranked, a cross-N cell is interleaved with 36 same-N cells in one order. That is the
  "one series across N" pattern that arbiter v3 marked as "watch".
- Impact: the list is pre-registered two ways, and the read would have to choose. Every m = 37
  design value (critical value 6.59, multiplier 2.14, chance 0.028, fidelity table, recovery 0.57
  at 1.3 pt, the top-16 extension, T = 10 / 15) is stated for a count the rule does not produce.
  This is the defect class of v3 #4 (B).
- Fix: state list membership once. The consistent choice is to put M006 and M009 at 5M in the
  Welch list, beside the floor-family package, with m ≤ 35. Either re-simulate at 35, or state
  once that the design grid stays at 37 and the read re-simulates at the actual m, and apply that
  at the box, Families, the fidelity table, [DK6]-[DK8] and [DK16]. If the choice is to keep them
  ranked, drop "paired" from the list's name and say how a Welch g and its interval enter s_pool
  and the ordering.

**B2. The pause default is close to a full launch, and the Falsifier has no reading for the
likely branch.**
- Where: box l. 158-163 ("pauses before its cells launch"); [DK8] l. 1347-1348 and l. 1511-1512;
  Falsifier (v) l. 1083-1084; Seeds l. 752-765; [DK17] l. 1375-1377 and l. 1583-1594; Falsifier
  l. 1056-1058; family test l. 946-947.
- Evidence: `budget.py` "[DK17] pause default" keeps 36 of 44 5M cells in a paused 5M family and
  20 cells at 350k. The pause rows are 254-286 runs against 302, 960.6-1,061.7 pod-hours against
  1,112.2 at r = 1. Three inconsistencies:
  (a) The box, [DK8] and Falsifier (v) say the family "pauses before its cells launch". Under
  [DK17], 36 of 44 cells launch at 5M (82 %) and 20 of 23 at 350k. "Unless Kai picks otherwise" makes the pause a relabel, not
  a hold.
  (b) At the likely σ the descriptive ranking has almost no resolving power. Three +1-pt cells
  land in the top 12 of 37 with probability 0.16-0.26 at 3.14 pt and 0.47-0.73 at 1.5 pt
  (`rank_sim.py`), against 0.028 by chance. [DK17] does not state these numbers. The one
  alternative that could buy resolution at that σ, "cut m", is "not priced", and "raise n to 8"
  has no recovery row. Kai would choose between priced options that do not resolve and an
  unpriced option that might.
  (c) Under a pause no family test is read (l. 946-947, 757), so "the wave's no" (l. 1047-1053)
  is never produced in the branch the STUDY calls likely. And l. 1056-1058 ("Either way the
  ranked lists still go to Kai at K3a") contradicts [DK17] l. 758 ("the list is not a K3a
  ranking, and nothing advances"). What the ~1,000-1,900 pod-hours of the likely branch feed
  downstream (wave 3, wave 4, Kai's K3a cut) is not said.
- Impact: this is the competing-group gap (below). The pre-registered ceiling ([DK8]) exists
  because recovery drops below 0.5 above 1.3 pt, and its default consequence spends almost the
  whole budget on the configuration the ceiling rejects. It also leaves the Falsifier with no
  outcome for the most probable branch.
- Fix: text and `budget.py` rows. (1) Reword the box, [DK8] and Falsifier (v) to match [DK17]:
  "above the ceiling the family goes to Kai; by default its T0/T0a/T1 cells run as a descriptive
  ranking". (2) Beside [DK17], print the recovery at σ 1.5 and 3.14 pt for the default, for n = 8
  on every cell, and for a priced cut-m row (for example 12 named cells × 8 seeds; `budget.py`
  plus a `screen_null.py` §16-style simulation). (3) Add the Falsifier's reading for a paused
  family: what is reported, and that no "no" is issued. (4) Reconcile l. 1056-1058 with [DK17]:
  say whether a paused family's descriptive list reaches Kai at K3a, and what it can be used for
  there.

**B3. The pause default keeps the 350k floor family "so that the floor-family G2 answers exist",
while fix 7 makes G2 not a finding for every traced entry.**
- Where: Seeds l. 754-755; [DK17] l. 1375-1377, 1584-1585; G2 trigger l. 871-879.
- Evidence: l. 877-879: "For an entry that meets the trigger the G2 rescue is reported with that
  label and is not read as a finding; the informative quantity is its cross-architecture
  accuracy against A". Every traced floor-family entry meets the trigger (M001 171,526, M002
  85,763, M003 114,182, M004 41,985, M005 0, M009 85,507). M006 is untraced and not packable
  today. [DK17] does not say whether the Welch package list is read under a 350k pause. If it
  is, it is read against an A whose sd_rep exceeded the ceiling.
- Impact: the stated reason for the 28 floor-family runs in the paused branch contradicts the
  STUDY's own rule. They are 14,000 run-epochs, 14,000 × 22.75 / 3,600 = 88.5 pod-hours at r = 1
  (177.0 at r = 2), by the Budget basis. At STUDY, a default must carry a reason that holds.
- Fix: either justify the floor family under a pause by the Welch package (and say it is read
  against a paused A, labelled so), or drop it from [DK17] and re-price.

**B4. "Mechanism not exercised" is inferred from rep-C for cells whose EBOPs path differs from
rep-C's.**
- Where: Controls l. 612-614; [DK18] l. 1596-1598; stub Design line.
- Evidence: the five labelled cells change the constraint the controller sees. M007 raises the
  traced floor to 474,125 (X4 l. 438-439). M008 weights the attention group's EBOPs by 0.1 in
  the controller's input (`campaigns/2026-09-26-delta/code/BLOCKED.md:30`: per-layer β =
  controller β × w[group]). M011 moves activation widths to per-element granularity. M003 and
  M012 change the softmax-table and activation-init widths. For any of these the 5M constraint
  can bind for the cell while rep-C is slack, or the other way round.
- Impact: a cell could be labelled "mechanism not exercised" while its own constraint was
  active. That is a wrong label on exactly the cells the readout exists to judge.
- Fix: print readout (a)-(c) per seed for each EBOPs-pressure cell as well, and label the cell
  by its own seeds under the same ⌈3k/4⌉ rule. The family label "constraint slack at 5M" stays
  on rep-C.

### Category C

- **C1. Constraint-rule thresholds** (l. 606-610). (b) ≤ 0.8 and (c) ≥ 0.9 carry no rationale.
  A seed at 0.85 × target with β pinned at `min_beta` for the whole window is "active" by the
  rule. (c) compares a logged float with 1e-10: state a tolerance (for example |log10 β −
  log10 min_beta| ≤ 0.01). Write one line each on why 0.8 and 0.9.
- **C2. Top-k counts at a smaller actual m** (l. 710-712, [DK16]). 16 and 6 are fixed at m 37 /
  11. The 350k list packable today is 9 (M038 and M040 wait for caches). The 5M list is at most
  32 (M006, M009, M038, M040, M041 not packable), with or without B1. Say whether k is fixed or scales (for example ⌈0.45 m⌉ / ⌈0.55 m⌉), and
  that `budget.py`'s +88 is at the design m.
- **C3. "Contradicted" null count** (l. 1062-1063) uses BH m 19 / 43 (0.5 / 1.1 expected). The
  list is read over cells that run with an "up" prediction, so the expectation should use that
  count. State it as "≤ 0.025 · (cells read)" or print it at the read.
- **C4. n_p for two pair types.** n_p is the cell-replica count (l. 853-854), and the family test
  uses n_p,i for cell-placebo pairs (l. 922-925). After a replica loss or a placebo loss the two
  differ. Use separate symbols (for example n_p for g, n_d for d).
- **C5. [L7] slack form escape** (l. 1430-1431): "or with the label 'screened with the
  constraint slack'" lets a lever go to confirm without the 350k follow-up. Name who decides
  (Kai at K3) so the rule is not optional by default.

## Competing-group question

A group that ran this screen next month would have one of two things for the branch this
design expects (a pause at σ well above 1.3 pt): a design that still resolves something there
(fewer cells at more seeds, priced and simulated), or an explicit statement that the likely
branch produces a descriptive list that feeds no pre-registered decision. This STUDY has neither
(B2). They would also have a ranked list whose membership is stated once (B1). Neither absence
is justified in the artifact. Both are text and `budget.py` rows, not GPU work.

## Adversarial notes

- "The saving is small" (l. 762) is candid, but the design reads this as a reason to accept the
  default. A pause that runs over 80 % of the cells is a launch, and the text should call it one (B2).
- "Structural, by construction" is now numeric and correct (fix 7). The [DK17] rationale was not
  updated to match it (B3). This is the one-table-updated, other-stale pattern, at STUDY scale.
- Checked and not found: no selection on held-out data; the placebo is never in s_pool, BH m or
  the m cells; the ceiling was not moved after the m = 37 re-simulation, which allows 1.4 pt
  (kept at 1.3, alternative listed); no number in the box, Null, Falsifier, [DK] rows or stub
  differs from the scripts' output.

## Scope note for the arbiter

All four B items are text and `budget.py` / `screen_null.py` rows. None needs a GPU, and none
reopens a v2 or v3 A item. B1 is a residual of v3 #4, B2 and B3 of v3 #9 and #7, and B4 of v3 #8.
Iteration counter: 4.
