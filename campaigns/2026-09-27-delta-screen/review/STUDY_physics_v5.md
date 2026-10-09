# STUDY physics review v5: 2026-09-27-delta-screen

Reviewer: physics-reviewer (fresh context; thesis paragraph and artifact only). Artifact:
`campaigns/2026-09-27-delta-screen/STUDY.md` (v5, 1,068 lines). No compiled PDF exists beside it.
Scripts the artifact cites (`screen_null.py`, `rank_sim.py`) were re-run in full on the laptop
(design arithmetic only, CPU seconds; no training, no data).

## Figures

No figure is shown or cited at STUDY, and no PNG or PDF exists in the campaign directory.
The planned figures (Conventions, `figures.md` row, l. 855) were checked as a plan:

| figure (planned) | status |
| --- | --- |
| Forest plot of g per family: per-seed points, n_p, GPU class, placebo row, interval named, caption "validation, n = 62,000, screen, not quotable" | plan adequate: split, n and status are in the caption; per-seed points show the spread |
| Family-test t_i panel against the re-simulated critical line, placebo named | plan adequate |
| Named cell showing d and g together | plan adequate |
| Welch and long-horizon lists in their own panels | plan adequate (keeps unpaired and H ≠ 500 numbers off the paired axis) |
| ROC curves / mistag axis | not applicable: validation only, the ROC-test set is never touched (l. 720) |

## What was verified (recomputed, not quoted)

- `screen_null.py` v4, full run: every §13, §15, §16, §17 and §18 number the STUDY quotes reproduces
  to the printed digit. Examples: own-sd critical t 4.284 / 6.585 (m 11 / 37, n 4; STUDY l. 667:
  4.28 / 6.59); false "yes" 0.103 / 0.101 at equal spread (l. 672); power 0.214 / 0.087 / 0.051 /
  0.026 (m 11) and 0.077 / 0.030 / 0.016 / 0.007 (m 37) (l. 676-678); ranking multiplier 2.168 /
  2.136, nominal coverage 0.936 / 0.933 (l. 647-649); two-mode rows 0.79 / 0.55 / 0.28 / 0.19 / 0.14
  (5M) and 0.92 / 0.81 / 0.66 / 0.49 / 0.45 (350k) (l. 566-570); T = 1.3 / 1.5 pt (l. 658);
  G2 null false-rescue 0.038 / 0.121 / 0.104 (l. 614).
- `rank_sim.py`, full run: the Ranking-fidelity table (l. 555-559) reproduces in every cell
  (m 37: 0.99 / 0.97, 0.47 / 0.40, 0.73 / 0.65, 0.16 / 0.14, 0.26 / 0.22, 0.74 / 0.66, 0.94 / 0.90).
- Hand arithmetic: archived N=64 seeds 67.18 / 72.64 / 67.21 give ddof-1 sd 3.144 pt (l. 243: 3.14);
  jump 72.64 − 67.20 = 5.44 pt (model uses 5.4). Binomial SE √(0.79 · 0.21 / 62,000) = 0.00164
  (l. 244). Class counts sum to 62,000; 12,579 / 62,000 = 0.20289, + 5 · 0.001615 = 0.21096 (l. 245).
  Half-widths 1.591 · {0.3, 0.85, 4.44, 1.04, 5.44} = 0.48 / 1.35 / 7.07 / 1.65 / 8.65 pt (l. 541-547).
  Run-epochs 14,000 · 4 + 27,000 · 4 + 12,000 = 176,000; × 22.75 / 3,600 = 1,112.2 pod-hours (l. 786, 803).
- Statistics conventions: sd_rep is ddof 1 with k_rep stated (l. 443-445); every per-cell interval is
  a paired t on the own sd with df n_p − 1 (l. 620-622); sign count printed (l. 622); per-class AUCs,
  macro AUC beside accuracy, and a flag for top-12 accuracy vs macro-AUC disagreement (l. 703-712);
  s_int is a two-way residual sd with df (m − 1)(n − 1) (l. 652-655). No Category A defect of this
  kind found.

## Findings

### (A) must resolve

None. Every planned gap carries a seed-based interval, pairing is paired, per-class AUCs are in the
readout, no number is quotable, and the ROC-test set is untouched. There is nothing a figure could
contradict at this phase.

### (B) should address

**B1. The 350k label threshold T is set by Monte Carlo noise, and the rule is non-monotone.**
*Attack.* T is "the largest 0.1-pt value at which ... recovery among draws with s_int ≤ T is ≥ 0.5 at
every q where such draws exist" (l. 658-661). The §18 filter has no minimum conditional set size.
In the re-run, 350k T = 1.6 fails on **one draw of 20,000** (q 0.3893, set 1, recovery 0.00); 1.7,
1.8 and 1.9 fail on sets of 3, 1 and 8. The STUDY discloses those (l. 929-930) but not that the same
rule also *fails at T = 1.2* at 350k (set 3, recovery 0.33) and at *T = 0.8 and 0.9* at 5M (sets 1
and 5), below the chosen values. A rule that fails at 1.2, passes at 1.3-1.5 and fails at 1.6 is
reading sampling noise, not recovery. At 5M the binding condition passes by about half a binomial SE
(q 0.1, set 823, recovery 0.51, SE ≈ 0.017).
*Evidence (my re-run, same draws, only the filter changed; scratch copies of `screen_null.py`):*

| variant of the §18 rule | T at 5M | T at 350k |
| --- | --- | --- |
| as written (set ≥ 1) | 1.3 | 1.5 |
| conditional set ≥ 30 draws | 1.3 | 1.7 |
| conditional set ≥ 100 draws | 1.3 | 1.9 |
| low mode rare-high instead of rare-low (jump sign flipped, set ≥ 1) | 1.4 | 1.4 |

The 5M threshold is stable at 1.3-1.4. The 350k threshold moves over 1.4-1.9 pt under defensible
variants. *Consequence:* label only ("ranked" / "descriptive") and the [DK16] band edge; nothing
that trains changes. This is why it is B, not A.
*What would settle it:* a stated minimum conditional set size (or a one-sided binomial lower bound ≥
0.5 on the conditional recovery) in the §18 filter, the re-run T per family quoted, and the [DK8]
decision block updated with the range it moves over.

**B2. The headline question poses a test whose detectable effect is several pt; say so in pt.**
*Attack.* The one-line question (frontmatter, l. 180-182) leads with "is any of them above the
family's do-nothing placebo at family-wise α 0.10?". The artifact calls the test "calibrated and
nearly powerless" and gives power only at +1 pt. A referee asks what effect it *can* see.
*Evidence (my simulation: own-sd t against the placebo, n = 4, ρ = 0, the §13 critical values):*
effect for 50 % / 80 % power on one named cell is 1.65 / 2.40 pt at σ 0.6 and 4.10 / 5.90 pt at σ
1.5 at 350k (m 11; about 2.8σ / 4.0σ), and 2.50 / 3.60 pt at σ 0.6 and 6.25 / 8.90 pt at σ 1.5 at 5M
(m 37; about 4.2σ / 6.0σ). At the archived 3.14-pt spread the 5M test needs roughly a 13-pt effect.
*What would settle it:* put the 50 %-power effect in pt beside the family-test clause (Question and
Falsifier), or demote the clause below the ranking question. The honest label is already there; the
resolving power in the thesis unit is not.

**B3. The lead box's "recovery 1.00" for a seed-shared mode restates an assumption.**
*Attack.* "What this wave can and cannot say" (l. 193-198) contrasts recovery 1.00 (seed-shared mode)
with 0.14-0.28 (per-run). In the §18 seed-shared model every configuration at seed s shares the mode,
so the cell × seed interaction is exactly the within-mode sd, fixed at 0.3 pt; the re-run gives median
s_int 0.30 pt at every q. The 1.00 is therefore the Gaussian row at σ = 0.3 pt, a consequence of
assuming a 0.3-pt interaction, not a property of pairing on two-mode seeds.
*What would settle it:* one clause in the lead box: "1.00 because the seed-shared model has a cell ×
seed interaction of 0.3 pt by construction; the design measures s_int instead of assuming it".

### (C) suggestions

**C1. Direction of the rare mode.** The model draws the *low* mode with probability q ≤ 0.5. The only
data (67.18 / 72.64 / 67.21) have the *high* value as the minority. The direction matters for top-k
recovery (my simulation, per-run mode, n 4): 5M q 0.33 rare-low 0.19 vs rare-high 0.10; 350k q 0.1
0.66 vs 0.55. Add a rare-high column to the two-mode table, or state that q > 0.5 was not simulated.

**C2. s_int is itself noisy near T.** At 350k the df is 30, so s_int has a relative SE of about 13 %;
an estimate of 1.5 pt is compatible with roughly 1.3-1.7 pt, the whole span over which B1's T moves.
Print a 90 % interval on s_int beside the label and mark the label "near threshold" when it straddles T.

**C3. Primary metric vs thesis metric.** The thesis is stated in tagging efficiency; the screen
ranks on validation top-1 accuracy, with macro AUC as tie-break and a top-12 disagreement flag. That
deviation is declared (l. 845, 852) and is fine for nomination. Confirm should restate the metric in
AUC or working-point efficiency before any thesis claim.

**C4. Iso-cost at 5M.** If rep-C shows the constraint slack, the 5M accuracy ranking compares cells at
uncontrolled EBOPs. The label and [DK18] follow-up already cover this; a per-cell EBOPs column next
to g in the forest plot would let a reader see it directly.

**C5. G2 for the floor family is near-tautological,** and the STUDY says so ("rescue expected from
floor arithmetic", ≥ 178,474 EBOPs of headroom against 6,947). M001's traced floor of 171,526 against a
trigger of 171,526.5 is on the edge by half an EBOP; label it with the other six rather than as a
special case, or state the traced floor's own reproducibility.

## Method health

The comparison can separate arms only at the scale shown: at n = 4 the ranking recovers three true
+1-pt cells in the 5M top 12 with probability 0.77 at σ 1.0 and 0.47 at σ 1.5 (Gaussian), less under
per-run two-mode seeds. The family test resolves only multi-pt effects (B2). The design states this
and measures which regime holds (s_int, ρ̂, n_low) instead of assuming it. The placebo is referenced
in every branch, its false-"yes" rate is calibrated at 0.099-0.108 under unequal spread and offset
(re-run §15), and it is conservative (0.036-0.082) under two-mode seeds at n = 4. At n = 3 it is
anti-conservative under two-mode seeds (up to 0.232) and is labelled so (l. 674-676). No suspiciously
good agreement: every simulated number reproduces, which checks the arithmetic, not the model. The
model's two load-bearing assumptions are the 0.3-pt within-mode sd and the direction of the rare mode
(B3, C1). The design measures the first directly and does not test the second.

## Verdict

I approve this design at STUDY, subject to the B list. The item that decides it most is B1: the 350k
"ranked" / "descriptive" threshold is the one pre-registered value shown to be set by 1-8 Monte Carlo
draws, and it should be fixed with a set-size floor before launch.
