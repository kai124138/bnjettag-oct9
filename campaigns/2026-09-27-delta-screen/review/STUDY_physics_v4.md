# STUDY physics review, v4: 2026-09-27-delta-screen

Reviewer: physics-reviewer (fresh context; I read only the thesis, `STUDY.md` and what it cites:
`screen_null.py`, `rank_sim.py`, `budget.py` numbers as quoted). Phase STUDY, iteration 4. There are
no results yet, so I review the plan: the arms, the seed count, the planned intervals and figures.

## Figures

The STUDY contains no figures and cites none. The planned figures are in the `figures.md`
conventions row (l. 1259). This is how the spec compares with the mandatory figure checks:

| planned figure | status against the checklist |
| --- | --- |
| Forest plot of paired g per family (H 500 ranked list) | Spec OK. Label "validation, n = 62,000, screen, not quotable" (split and n present). n_p per row, per-seed points, GPU-class column, placebo row, and each bar names its interval (own sd or pooled). It does not say that error bars will be checked against the stated seed spread; "each bar says which interval it is" is close enough at STUDY. |
| Family-test panel (t_i against one critical line, or per-cell thresholds) | Spec OK. The critical value is re-simulated at the actual m and n_p vector, and the placebo is named as the reference. A named cell shows both d and g. |
| Long-horizon panel (M015, M031, M032, marked with H) | Spec OK. It is kept apart from the ranked list. |
| Floor-family cross-architecture package plot | Spec OK. It is kept separate, with Welch intervals. |
| ROC curves | None planned. That is correct for a validation-only screen that never touches ROC-test (l. 1033). The linear-mistag and random-line checks do not apply. |
| Per-class AUC | Planned as a table (l. 1007-1009, "any class under 0.7 called out"), with no figure. That is acceptable. |

No figure can contradict the text at this phase.

## What I verified (recomputed, not quoted)

- I re-ran `screen_null.py` (uv, numpy + scipy, 11 s), and §13-§17 reproduce the STUDY:
  - own-sd critical values 4.28 / 6.59 at n = 4 and 6.73 / 12.29 at n = 3;
  - false "yes" 0.103 / 0.101 at equal spread, and 0.036-0.082 two-mode at n = 4;
  - two-mode at n = 3: 0.063-0.115 (m = 11) and 0.081-0.232 (m = 37);
  - power 0.214 / 0.087 / 0.051 / 0.026 (m = 11) and 0.077 / 0.030 / 0.016 / 0.007 (m = 37);
  - ranking multiplier 2.168 / 2.136 (nominal t covers 0.936 / 0.933);
  - rank-move null counts behind T;
  - ρ̂ null interval ±0.34 / ±0.18; unpaired critical values 2.880 / 3.590;
  - 5M recovery 0.57 at 1.3 pt and 0.52 at 1.4 pt, with chance 0.0283;
  - 350k recovery 0.50 at 3.0 pt;
  - extension rows 0.77 → 0.87 and 0.57 → 0.69 (5M), 0.89 → 0.96 and 0.79 → 0.90 (350k);
  - G2 false-rescue rates 0.038 / 0.121 / 0.104 and 0.312 / 0.738 / 0.948.
- P(pause) is exact χ²₇. At σ = 1.5 pt, 7 · 1.69 / 2.25 = 5.26 and P(χ²₇ > 5.26) ≈ 0.63. At
  3.14 pt the statistic is 1.20 and the probability ≈ 0.99. Both match l. 745-748.
- Half-width t(0.975, 3) / 2 = 3.182 / 2 = 1.591. The rows ±0.48 / 1.35 / 7.1 / 1.65 / 8.65 pt
  (l. 786-792) follow.
- The seed-rule thresholds are 0.3 / (k_joint · √2): 0.058 / 0.102 / 0.134 (350k) and 0.044 /
  0.085 / 0.116 (5M). All six match l. 700-704.
- Budget: 14,000 · 4 + 27,000 · 4 + 12,000 = 176,000 run-epochs, and × 22.75 / 3,600 = 1,112.2
  pod-hours. Per-seed cell-epochs are 12,500 at 350k (23 cells + M015 extra + M010) and 25,000 at
  5M (41 × 500 + 1,000 + 1,500 + 2,000).
- Cell counts from the table (l. 314-364): 23 at 350k and 44 at 5M, 68 with M010. m = 11 at 350k
  (12 accuracy cells minus M015) and m ≤ 37 at 5M (40 G3 minus 3 long-horizon).
- The statistics conventions are stated:
  - sd_rep is ddof = 1 with k_rep printed (l. 590-593);
  - paired t-interval, df n_p − 1, sign count (l. 879-881);
  - per-class AUCs beside macro (l. 1007-1009);
  - a resolving-power table (l. 784-792);
  - accuracy is the declared selection metric, with an accuracy-vs-AUC concordance flag
    (l. 1018-1021, 1247, 1254);
  - the tuning asymmetry against the baselines is declared (l. 216-220).
- `gen()` in `screen_null.py` (l. 141-144) draws the two-mode component independently per run.
  That matters for B2 below.

## Findings

### (A) Must resolve

None. The plan has no tautology in the primary quantity:
- selection and the gap are both on validation, and the screen is labelled never quotable;
- ROC-test is never touched;
- every design number I recomputed reproduces;
- the resolving power is stated honestly: at the only measured spread the wave is expected to
  pause and deliver a descriptive ranking.

### (B) Should address

**B1. The pause gate reads the wrong spread.**

*Attack.* The ceiling at l. 734-767 and [DK8] / [DK17] is keyed to sd_rep, the marginal
across-seed sd of the replica, through sd_plan = √2 · sd_rep. That assumes ρ = 0. The ranking's
fidelity depends on sd(g), the paired cell − replica sd, which equals √(2(1 − ρ)) · σ. The only
measured N=64 spread (3.14 pt, l. 236) is two-mode (67.18 / 72.64 / 67.21 %). Two structures
give the same sd_rep and opposite answers:
- If the mode is locked to the seed (init or data order, which `order_seed = f(s)` shares across
  arms at seed s), pairing removes it. The ranking then works at any sd_rep.
- If the mode is drawn per run, pairing does not help.

*Evidence.* `review/physics_v4_twomode.py` (seeded, 8,000 reps) uses the STUDY's own two-mode
model: jump 5.4 pt, sd 0.3 pt, m = 37, n = 4, three true +1-pt cells, top 12. P(all three
recovered) is:

| q | per-run sd | per-run mode | seed-locked mode |
| --- | --- | --- | --- |
| 0.1 | 1.65 pt | 0.28 | 1.00 |
| 0.33 | 2.56 pt | 0.19 | 1.00 |
| 0.5 | 2.72 pt | 0.14 | 1.00 |

In both structures sd_rep is far above 1.3 pt, so the family pauses with probability about 0.9 or
more. The gate cannot tell these cases apart. It pauses in exactly the case where pairing rescues
the ranking.

*Why it matters.* On a pause, [DK17] still runs the T0/T0a/T1 singles at n = 4 (254-286 runs,
l. 758-761). So s_pool and the pooled ρ̂ (l. 1022-1027) exist after the readout anyway. The pause
costs little GPU time but downgrades the output to "descriptive, no family test". That label is
fixed by a quantity the ranking does not depend on.

*What would settle it:*
- a pre-registered re-read at the n = 4 readout of a paused family: if the observed family-pooled
  paired sd s_pool ≤ √2 · 1.3 = 1.84 pt, the family is read in ranking mode with its family test,
  and otherwise it stays descriptive;
- or a stated reason why the marginal sd is the right gate.

In both cases, print sd_rep, s_pool and ρ̂ side by side at the readout.

**B2. Ranking fidelity is simulated only for Gaussian seeds, while the ranking is "the only output".**

*Attack.* The STUDY calls the ranking "the only output at this power" (l. 173, 929-930). Its
fidelity rows are all Gaussian with a shared-ρ component: `rank_sim.py`, `screen_null.py` §3,
§15 and §16. The family test has two-mode rows (§4, §15). The ranking and the top-k extension
do not. The only measured spread is two-mode. l. 749-751 notes that non-Gaussian seeds make the
pause rows "a guide", but says nothing about the ranking table at l. 802-806.

*Evidence.* In the per-run-mode case above, recovery at q = 0.1 (per-run sd 1.65 pt) is 0.28.
The Gaussian §15 row at a matched 1.6-1.7 pt gives 0.42 / 0.39. Two-mode seeds cost about a third
of the recovery at the same sd.

*What would settle it:* two-mode rows in §15 and §16 (recovery and the extension) under both mode
structures, quoted beside the Gaussian table with "Gaussian rows are optimistic under per-run
two-mode seeds".

**B3. The floor-family question is posed as live but declared uninformative by construction.**

*Attack.* The frontmatter question (l. 6) and the Question section (l. 189-196) pose G2, "does
each floor-family entry reach 350k in more seeds than A07-350". The Selection rule (l. 871-879)
then says that every traced entry meets the "structural, by construction" trigger:
- the floors are M001 171,526, M002 85,763, M003 114,182, M004 41,985, M005 0 and M009 85,507,
  against a trigger of 171,526.5;
- each entry has headroom ≥ 178,474 against A07-350's 6,947;
- so the G2 rescue "is not read as a finding".

Yet [DK17] (l. 754-756, 1584-1585) keeps every floor-family cell and M010 on a pause "so that the
floor-family G2 answers exist". Those are A07-class runs, about 28 at n = 4 including k_base.

*What would settle it:*
- rewrite the floor-family question as what the STUDY says is informative: the cross-architecture
  accuracy package against A, Welch, which is itself a package and not a single lever;
- state that G2 is a sanity check expected to pass by floor arithmetic;
- justify the floor family's place in the pause branch by the accuracy package, or drop it from
  that branch.

M001 sits 0.5 EBOPs under the trigger, so its label rests on a rounding edge. Print it as
borderline.

### (C) Suggestions

**C1. The pairing "hint" is uninformative.** The only pairing record (l. 1023-1024) is three
correlations (−0.34, −0.79, −0.56), each computed on 3 seeds. At n = 3 the null density of a
sample r is ∝ (1 − r²)^(−1/2), which piles up near ±1. A value of −0.79 is unremarkable under
ρ = 0. Call it "no information on ρ" rather than "a hint against pairing". The ρ = −0.5 rows can
stay as a stress case.

**C2. The determinism probe does not cover pack composition.** The probe (launch gate 7) runs one
config in two pods of one product. Placebos are packed with cells, at a possibly different K and
with different co-residents. Kernel or algorithm choice can depend on free workspace memory. So
check (iv)'s "flags on its own if the probe found that product bit-identical" (l. 1080-1083) can
fire on a pack effect the probe never exercised. Either run the probe with the two copies in
packs of different composition, or word the flag "pack-composition effect or nondeterminism, not
separated".

**C3. The "contradicted" count's cell set is unclear.** The expected null count for the
"contradicted" list uses m = 19 / 43 (l. 1062-1063), the BH counts. The ranked list is 11 / 37.
Say which cells the "contradicted" list covers (every G3 cell including the floor-family Welch
package and the baselines, or only the ranked list) and use the matching m.

**C4. The 350k ceiling is borrowed from 5M.** The 1.3-pt ceiling applied to 350k is declared
(l. 739-740), but that family's own criterion allows 3.0 pt (recovery 0.50 at 3.0, §15). Given
B1, a per-family ceiling, or none at 350k where [DK17] already runs almost everything, would lose
nothing.

**C5. The packable-today m is not written down.** Packable today (l. 1175-1184) removes M038 and
M040 from the 350k ranked list (m = 9), and M006, M009, M038, M040 and M041 from the 5M list
(m ≤ 32). The STUDY says the read re-simulates at the actual m. Also print the packable-today m
here, so that the design power rows are not read at m = 11 / 37 when fewer cells run.

## Stripped of framing

The plan produces:
- a validation-only, never-quotable ranking with honest, reproducible design arithmetic;
- a family test that is correctly calibrated but nearly powerless;
- a pre-declared likely pause.

It does not dress a projection as a result. Its weakest point is that the gate deciding whether
the ranking is read as a ranking or only as a description uses the marginal seed sd. The ranking
depends on the paired one, and at the only measured, two-mode spread these can differ by the
whole effect.

**Verdict.** I would approve this STUDY for launch once B1 is addressed. The deciding factor is
whether the pause and ranking-mode gate is re-keyed to, or re-read on, the paired spread (s_pool,
ρ̂) that the paused branch measures anyway.
