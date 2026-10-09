# STUDY physics review v3: 2026-09-27-delta-screen

Reviewer: physics-reviewer (fresh context). Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md`
(1,370 lines, v3 after fixer v2). No compiled PDF exists beside it. Opened: `STUDY.md`,
`screen_null.py` (run in full), the anchor STUDY at git 96b95f2 (the lines this artifact cites:
438-460, 875-885, 1400-1460, 2337). Earlier reviews were not used.

## Figures

The STUDY has no results, shows no figure and cites none. The planned figures (Conventions row
`figures.md`, l. 1046; Arms l. 187; Selection rule l. 786-793) are checked as a plan.

| figure (planned) | status | checks to apply at REPORT |
| --- | --- | --- |
| Forest plot of paired g per family (350k, 5M), placebo row, per-seed points, GPU-class column | planned, not produced | "validation top-1, n = 62,000, screen, not quotable" on every panel; n_p per row; each bar says own-sd or pooled; the placebo row is present and its branch ((i) or (ii)) is stated; the zero line is the replica, not the placebo |
| Family-test panel (t_i against one critical line, or per-cell thresholds) | planned, not produced | the critical value drawn is the one re-simulated at the family's actual m and n_p vector, not the 4.41 / 6.75 design values; the reference (placebo) is named on the axis |
| Floor-family "cross-architecture package" plot (Welch) | planned, not produced | its own figure, never on the paired-list axis; each entry shows its traced floor and headroom beside k_e and k_base |
| A07 ladder plot (350k, 1.4M, 5M on shared seeds) | planned, not produced | G2 counts at different targets are not drawn as a gap (l. 187-189) |
| ROC curves | none planned | ROC/mistag-axis checks not applicable: no ROC-test evaluation (l. 850) |

## Verified

- `screen_null.py` run in full (`uv run --with numpy,scipy python screen_null.py`, 6 s). Every
  design number it sources reproduces: own-sd critical values 4.406 (m 12, n 4) and 6.751 (m 40,
  n 4) against STUDY l. 756 "4.41 / 6.75"; n = 3: 6.948 / 12.984 against "6.95 / 12.98"; m 11 /
  37: 4.284 / 6.585 against "4.28 / 6.59" (l. 736); R2 false "yes" 0.098-0.111 (equal and unequal
  spread) and 0.038-0.089 (two-mode, n 4) against l. 763-770; n = 3 two-mode 0.067-0.122 /
  0.080-0.237 against l. 772-774; power 0.204 / 0.046 / 0.022 (m 12) and 0.074 / 0.015 / 0.007 (m
  40) against l. 765-767; ranking multipliers 2.179 / 2.146, nominal coverage 0.934 / 0.932
  against l. 747-748; G3' power 0.074 / 0.041 / 0.031 against l. 721; ceiling probabilities (8
  seeds: P(sd_rep > 1.3) 0.041 / 0.201 at σ 0.9 / 1.1; P(≤ 1.3) 0.371 / 0.110 at 1.5 / 2.0; 6
  seeds 0.065 / 0.223, 0.417 / 0.165) against l. 617-620; rank-move null counts and T thresholds
  against l. 810-816; unpaired critical values 2.923 / 3.622 against l. 847; placebo-check
  offsets 1.25 / 1.85, 3.05 / 4.55, 6.55 / 9.55 pt against l. 895-896; recovery ceiling 1.3 pt (5M)
  and 2.7 pt (350k) against l. 611-615.
- Closed-form arithmetic: sd_rep thresholds 0.3 / (k_joint · √2) = 0.058 / 0.102 / 0.134 (350k)
  and 0.044 / 0.085 / 0.116 (5M), l. 600-603; half-width t(0.975, 3) / 2 = 1.591, l. 635; binomial
  SE √(0.79 · 0.21 / 62,000) = 0.00164, l. 172; p_maj 12,579 / 62,000 = 0.20289, class counts sum to
  62,000, threshold 0.20289 + 5 · 0.001615 = 0.21097, l. 173; chance C(12,3)/C(43,3) = 0.0178 and
  C(12,3)/C(40,3) = 0.0223, l. 110; wave-level 1 − 0.90² = 0.19, l. 114; runs 272 + 8 + 20 + 2 = 302 and
  run-epochs 14,000·4 + 27,000·4 + 12,000 = 176,000, 176,000 × 22.75 / 3,600 = 1,112.2 pod-hours,
  l. 912-916, 974; E packing floor(0.9 · 23,028 / 4,354) = 4 and 5 · 4,354 = 21,770 MiB = 94.5 %, l.
  987-988.
- Anchor citations checked at 96b95f2: archived N=64 W1A8 seeds 67.18 / 72.64 / 67.21 %, sd 3.14 pt,
  sizing only (anchor l. 444); N=8 lower bracket 0.19 pt (l. 449-454); regime-B traced-epoch rule,
  no epoch-0 trace, and BetaPID reading in-training EBOPs between traces (l. 1400-1435); s_e ≈ 136.5
  s "Neither is a measurement" (l. 1455-1457). The artifact quotes them correctly and labels each.

The design's statistics are internally consistent and honestly labelled: every number is
validation, n = 62,000, screen, not quotable; seed sd is ddof = 1; gaps are paired with own-sd
t-intervals; per-class AUCs are in the readout (l. 825); selection and ranking on the same
validation split are acknowledged (winner's curse [L6]) with two non-selecting companions. No
Category A finding.

## Findings

### (A) must resolve

None.

### (B) should address

**B1. The floor-family G2 rule has no stated null rate, and for several entries the rescue is
arithmetic.** The rule "k_e ≥ 3 and k_e − k_base ≥ 2" (l. 131-132, 711) has no error rate
beside it. Computed (binomial, n = 4, p_e = p_base = p): P(false rescue) per entry = 0.038 / 0.121 /
0.104 at p = 0.25 / 0.5 / 0.75, so about 0.85 false rescues are expected across the 7 entries at p =
0.5 (at n = 3: 0.062, about 0.44). Worse, A07-350 has traced headroom 6,947 EBOPs (l. 186) and
A07-350-s1 has never completed an epoch (l. 167), so k_base = 0 is the likely value; then a null
entry "rescues" with probability 0.31 / 0.74 / 0.95 at p_e = 0.5 / 0.75 / 0.9. The traced floors
scale with head count (anchor l. 2337: one head 85,763; M001 two heads 171,526, l. 225; A07 four
heads 343,053), so for M001 and M002 the rescue is a consequence of halving the floor, not a
finding. The artifact's label "structural, by construction" (l. 713) is applied by eye.
*Settle:* print the null false-rescue rate at the observed k_base beside k_e; give
"structural, by construction" a numeric trigger fixed now (for example traced headroom at 350k
above a stated fraction of the target, or floor ratio to A07's), and state that for those entries
the informative quantity is the cross-architecture accuracy, not G2.

**B2. Whether the 5M constraint binds is not stated, and it decides what 40 of 68 cells
measure.** Under anchor [D19], C's traced 0-bit floor is 343,053 (l. 184), so the 5M target is
14.6× the floor; the 5M target was set against the old quantizer's 4.58M floor (anchor l. 1497,
2361: "9.2 % above its traced floor"). If BetaPID never pushes at 5M, the 5M family screens an
effectively unconstrained binary model. That matters most for the levers whose mechanism is EBOPs
pressure (M008 attention-group EBOPs weight, M011 / M012 activation widths, M003 / M007 width
floors) and for every training-only lever (M017-M037), which run at 5M only ([L7]). The thesis
regime (L1 budget) is 350k, where only 12 accuracy cells sit. *Settle:* pre-register a
"constraint active" readout on rep-C at epoch 500 (fraction of traced epochs over target, the
selected checkpoint's EBOPs / target, β at its bound or not); if the constraint does not bind,
label the 5M family "constraint slack at 5M" and the EBOPs-pressure cells "mechanism not
exercised", and carry that into the [L7] transfer rule for confirm.

**B3. The bit-identical placebo branch is under-specified.** The determinism probe runs one
config twice in one pod (l. 443-448); branch (i) then sets d = g and drops the placebo as the
reference (l. 776-783). In that branch the family test's false "yes" rises to 0.261 (m 12) / 0.258
(m 40) at a common offset of 0.707 SE (reproduced, §4), and the placebo check cannot see offsets
below 1.25 pt at σ 0.6 (50 % detection, §12); with a bit-identical placebo the check's own sd is 0
and its t is undefined. *Settle:* branch (i) requires, in addition to the in-pod probe, that the
placebo equal its replica bit-for-bit (weight hashes at epoch 500) at every seed that shares a GPU
product, across pods. If any such seed differs, the family falls to branch (ii). Cross-pod
equality is the observation that shows the offset is zero, so the 0.26 row does not apply.

**B4. "Expected outcome: ranking mode at (4, 4)" disagrees with the ceiling at the only measured
N=64 spread.** The sole N=64 seed spread is 3.14 pt (two-mode, archived; l. 171), well above the 1.3-pt
ceiling (l. 610). At that prior the likely outcome is that both families pause at the replica gate
(P(sd_rep ≤ 1.3) is 0.11 at σ 2.0), not that they run at (4, 4). The artifact says (l. 624-632) that
a replica sd below the thresholds is not expected, but it does not say that a pause is plausible or
likely. The budget, timeline and [DK1] are written for (4, 4). *Settle:* state the pause as a likely
branch with its trigger probability at σ = 0.6 / 1.5 / 3.14, and pre-register which of the four
options (cut m, raise n, cheap version, feasibility only) is the default. Choosing among them on
replica data alone does not bias cell results, but naming the default now keeps it from reading as
a choice made after the fact.

### (C) suggestions

- **C1.** The family test names a true +1-pt cell with probability 0.046 / 0.015 at σ 1.5 pt (m 12 /
  40), below its own α. The artifact says so (l. 116-117, 871-873). Put "the ranking is the only
  output; a 'no' is not evidence of absence" next to every family-test answer in VERIFY and
  REPORT, or drop the test if σ ≥ 1.5 pt is measured.
- **C2.** sd_plan = √2 · sd_rep assumes ρ = 0 (l. 514, 839-844). The only record hints at negative
  cross-arm seed correlation (−0.34 to −0.79). Then sd_d can be up to 2σ, and n = 4 resolves less
  than the half-width table (l. 637-641) shows. ρ̂ is printed. Add one row to that table at ρ = −0.5.
- **C3.** l. 142: 1/(m + 1) at m = 40 is 0.024, not 0.023 (the simulation prints 0.024).
- **C4.** The family test's reference is the placebo, but the ranking's zero line is the replica. A
  cell can be named "above the placebo" while its g against the replica is negative. Where a
  cell is named, the forest plot should show both d and g.

## Verdict

As a screen design I would approve it for launch once B1-B4 are addressed. Its statistics
reproduce and are honestly labelled. It will produce a ranking, not a measurement. The deciding
item is B2: whether the 5M family, which holds most of the cells and every training-only lever,
measures a model that the EBOPs constraint actually shapes.
