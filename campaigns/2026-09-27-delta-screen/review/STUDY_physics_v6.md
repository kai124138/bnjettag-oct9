# STUDY physics review, v6: 2026-09-27-delta-screen

Reviewer: physics-reviewer (fresh context; thesis paragraph plus the artifact and what it cites).
Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (v6, 1,161 lines). No compiled PDF exists beside it.
Re-run for this review: `screen_null.py` (design seed, all sections plus the nine child seeds),
`rank_sim.py`, `budget.py`; one new check, `review/physics_v6_rarehigh.py`.

## Figures

The artifact shows and cites no figure; at STUDY there are none to inspect. The planned figures
(Conventions table, `figures.md` row, l. 926) are specified as follows:

| planned figure | status |
| --- | --- |
| Forest plot of g per family (per-seed points, n_p, GPU class, placebo row, each bar's interval named, "validation, n = 62,000, screen, not quotable") | not inspectable at STUDY. The specification covers split, n, interval source and placebo. It does not say which statistic the bar centre shows (median g, the primary, or mean g, which the interval belongs to); see B1 |
| Family-test t_i panel against the re-simulated critical line, placebo named | not inspectable; specification adequate |
| A named cell shown with d and g | not inspectable; specification adequate |
| Long-horizon and Welch lists in separate panels | not inspectable; specification adequate (no cross-list comparison) |
| Per-cell EBOPs column beside g | not inspectable; specification adequate |

There are no ROC figures. None is planned, since the screen reads validation top-1 accuracy only.

## What I verified (recomputed, not quoted)

- **Half-widths (l. 581-590).** t(0.975, 3)/2 = 1.591. The products 0.85·1.59 = 1.35, 4.44·1.59 = 7.06, 1.04·1.59 = 1.65 (sd_d = 0.6·√3 = 1.039) and 5.44·1.59 = 8.65 all match.
- **Binomial SE (l. 278).** √(0.79·0.21/62,000) = 0.001636.
- **Non-degeneracy threshold (l. 279).** The class counts sum to 62,000. p_maj = 12,579/62,000 = 0.20289, SE = 0.001615, and 0.20289 + 5·0.001615 = 0.21096.
- **Counts (l. 361-365).** 350k: 12 accuracy cells on A + M050 + 3 probes + 7 floor-family cells = 23. 5M: 44, and 44 − 4 baselines − 3 long-horizon − 2 Welch = 35. `budget.py` prints 68 cells (23 / 1 / 44).
- **Budget (l. 855-867).** `budget.py` reproduces 302 runs, 176,000 run-epochs (42,000 E / 134,000 A07), 318 certifications, 1,112.2 / 1,959.0 pod-hours, 5.4 / 9.2 d, the packable-today total of 240 runs, and every extension, (6, ·), (·, 6), (8, ·) and cheap-version row digit for digit. The formula 14,000·4 + 27,000·4 + 12,000 = 176,000 is consistent.
- **`screen_null.py`, re-run at the design seed with its nine child seeds.** These all match the STUDY:
  - §19a T per seed: 5M 1.2 ×10; 350k 2.1 / 2.1 / 2.7 / 2.1 / 2.3 / 2.1 / 2.1 / 2.6 / 2.6 / 2.1, so T = 1.2 / 2.1 (l. 1008).
  - Median-g Gaussian recovery at T: 0.52 (5M) and 0.56 (350k).
  - The failing-T rows at 350k: q 0.5 sets of 338-9,126 draws recover 0.45-0.50.
  - §19b: 5M 0.99 / 0.96 / 0.85 / 0.26 / 0.26. Above the band the extension moves 0.26 → 0.34 and 0.26 → 0.29 at 5M, and 0.61 → 0.71 and 0.54 → 0.67 at 350k. The q = 0.5 set at 350k is 113 draws recovering 0.48.
  - §19c: 0.71 | 0.81 | 0.83 (5M, σ 1.0); 0.86 | 0.94 | 0.92 and 0.70 | 0.80 | 0.76 (350k).
  - §19d: m = 37 at r = 0.95 gives T 12 (0.9); r = 0.9 gives 1.2 at T 15; r = 0.7 gives 5.0. At m = 11: 6 / 5 / 4 at r ≥ 0.5 / 0.7 / 0.9.
  - §18b: 0.77 → 0.66 and 0.57 → 0.46 (5M); 0.89 → 0.84 and 0.79 → 0.73 (350k).
  - §18c: 0.071 false flag; power 0.067 / 0.102 / 0.214 / 0.510 / 0.801.
  - §15a: detectable effects 1.65 / 2.40 up to 13.05 pt.
  - §13 / §15: critical values 4.284 / 6.585; false "yes" 0.103 / 0.101; power 0.214 / 0.087 / 0.051 / 0.026 and 0.077 / 0.030 / 0.016 / 0.007; interval multiplier 2.168 / 2.136 with nominal coverage 0.936 / 0.933; ρ̂ null ±0.34 / ±0.18; unpaired critical values 2.880 / 3.590.
- **`rank_sim.py` v6 block (l. 599-603).** Every median / mean / LCB80 triple at m = 37 matches, for example 0.37 / 0.47 / 0.40 at σ 1.5, ρ 0.
- **Suspiciously good: the seed-shared recovery of 1.00 (l. 221-228, 625-628).** In `twomode(shared=True)`, a mode set by the seed moves the replica and every cell at seed s together. It therefore cancels exactly in g = c − r, and what remains is 0.3-pt within-mode noise against a +1-pt effect. The explanation produces the observed size; it is by construction, and the artifact says so.
- **Condition (i) of the T rule reads the true σ, while the label reads the estimated s_int.** I checked the leakage.
  - At 350k, median-g Gaussian recovery stays ≥ 0.50 up to σ 2.7 (§19a grid), so a true σ above T that reads under T does not drop recovery below 0.5 there.
  - At 5M (df 108), P(s_int ≤ 1.2 | σ = 1.4) ≈ P(χ²₁₀₈ ≤ 79.3) ≈ 0.03.
  - The leakage is negligible and is not a finding.
- **Quotability.** No path takes a screen number into the record. The ROC-test set is never touched (l. 789), every number carries "validation, n = 62,000, screen, not quotable" (l. 918), and the thesis-bearing comparisons are deferred to confirm with a metric restatement (l. 254-263).

## Findings

I find no Category A item. The one candidate I weighed is B1, and I explain there why it is not A.

### (B) should address

**B1. The primary ranking statistic, median g, has no interval of its own.**
- *Attack.* House rule: "never report a gap without seeds and an interval". Median g orders the list and sets the confirm cap order (l. 698-700). Its only interval belongs to mean g (l. 1001: "The ranking interval belongs to mean g"). The per-cell readout (l. 771-781) and the planned forest plot will print a median-g value per cell. A reader will read that value as a gap, and nothing tells them what uncertainty it carries.
- *Why this is B and not A.* Every cell row carries mean g with its own-sd 95 % t-interval (df n_p − 1) and the family-pooled "95 % at equal spread" interval (l. 672-674, 704-709), plus the per-seed points, n_p and the sign count. No gap is stated without an interval. What is missing is an interval for the ordering statistic, not for the gap.
- *What would settle it.* Either of two changes:
  - Print the distribution-free interval for the median beside median g. At n = 4 the (min, max) of the four g_s covers the population median of the per-seed gap with probability 1 − 2·2⁻⁴ = 0.875; at n = 3 it is 0.75. Label it with that coverage.
  - Or add one sentence to the Readout and the figure specification: median g is a rank score, printed without a centre-plus-interval format, and the forest-plot bar is mean g with its interval, with the median as a separate marker.

  Either is text only and changes no rule.

**B2. The q > 0.5 regime (a rare high mode) is left "not simulated" (l. 618-620). It is the shape of the only observed N=64 data, and it is now cheap to close.**
- *Attack.* The archived three values (67.18 / 72.64 / 67.21 %) are two low runs and one high run. That is P(high) ≈ 1/3, the q > 0.5 case in the artifact's parameterisation. The T rule's condition (ii) grid stops at q = 0.5. Per-run q and 1 − q are not mirror images once the replica is shared: a rare high run in a null cell is exactly what lifts a null cell into the top k.
- *Evidence (new; `review/physics_v6_rarehigh.py`; same model as `twomode()`: jump 5.4 pt, within-mode sd 0.3 pt, n = 4, shared replica; RNG seed 606; 20,000 draws).*

  At 350k, T = 2.1:

  | q | P(s_int ≤ T) | median-g recovery given s_int ≤ T | mean-g recovery given s_int ≤ T |
  | --- | --- | --- | --- |
  | 0.67 | 0.042 | 0.61 (846 draws) | 0.39 |
  | 0.80 | 0.396 | 0.87 | 0.46 |
  | 0.90 | 0.92 | 0.98 | 0.55 |
  | 0.95 | 1.00 | 1.00 | 0.79 |

  At 5M, T = 1.2: every q ≥ 0.9 set recovers 1.00. At q ≤ 0.8 the set is empty, so the list reads "descriptive".

  Control: my q = 0.5 set at 350k is 128 draws recovering 0.42, against the artifact's 113 draws and 0.48. The RNG is independent and the model is the same; the Monte Carlo SE on about 120 draws is about 0.045, so the two agree.
- *Reading.* The v6 primary passes condition (ii) at every simulated q > 0.5 above the 0.01 floor. v6's switch to median g is exactly what protects the "ranked" label in the rare-high regime. The mean-g companion does not pass there: it recovers 0.39-0.55 when the 350k list would read "ranked". That matters wherever mean g is used as the "stability readout" or ranks the rank-move companion.
- *What would settle it.* Replace the sentence at l. 618-620 with these rows, or append the q ∈ {0.67, 0.8, 0.9, 0.95} rows to `screen_null.py` §19b. Also state that the mean-g companion falls under 0.5 in that regime while the list is labelled "ranked", so a median-g / mean-g disagreement there is expected, not alarming. The K3a flag at l. 711-712 fires on such disagreement.

### (C) suggestions

**C1. The "ranked" label is weaker than the word suggests. Print the recovery on both branches.** At 350k, "ranked" means median-g Gaussian recovery ≥ 0.5 for one +1-pt cell in the top 3 of 11 (chance 0.27). At s_int = T = 2.1 pt, a single cell's own 95 % half-width is 1.59·√2·2.1 ≈ 4.7 pt. The artifact cites the recovery rows only on the "descriptive" branch (l. 718-720). Print "ranked: recovery ≈ x at the measured s_int (§19a / §19b)" too, so a reader does not take "ranked" for "resolved".

**C2. The 350k T = 2.1 pt sits on a knife-edge.** It is the value at which the failing q = 0.5 conditional set (113 draws, recovery 0.48) drops under the 0.01 floor. The artifact discloses this (l. 1013-1016) and my re-run confirms it. No change is needed beyond keeping that disclosure beside the label wherever a 350k s_int lands in 1.9-2.1 pt.

**C3. The rank-move bands at 350k merge r ≥ 0.9.** The same rule applied at the r = 0.95 lower edge gives T 3 (null 0.6; §19d m = 11). The STUDY uses T 4 for all r ≥ 0.9, which is conservative (null 0.2 at r ≥ 0.95). This is not an error. One clause stating that the r ≥ 0.95 row was merged on purpose would pre-empt the question.

**C4. The family-test half of the question is nearly uninformative, and the one-line question gives it equal billing.** It detects one named cell at 50 % power only at 1.65-4.10 pt (350k) and 2.50-6.25 pt (5M) for σ 0.6-1.5 (§15a, verified). This is disclosed (l. 230-232) and the "no is not evidence of absence" line is mandated. Consider rewording the one-line question's second clause as a calibrated guard against a false "yes", which is what it is.

**C5. Tuning asymmetry (l. 259-263).** It is disclosed at the thesis-bearing level: confirm either gives the matched non-binary arm the recipe-level winners or labels the gap "binary tuned, baseline not". This is adequate for a screen. Carry the sentence into the confirm STUDY verbatim.

## Method health, statistics, scope

- **Arms matched.** The cell and its replica differ only by the delta, `epochs`, identity keys and the re-traced floor key. The key diff is asserted at PREFLIGHT (l. 308-315). The placebo isolates pod, pack and identity (l. 293-306, 549-550). The confounds table covers GPU product and packing.
- **Baselines.** FP32 and 8-bit comparands (M047-M050) are screen-level only, and three of the four are blocked by X5. The thesis comparison is correctly deferred to confirm and not claimed here.
- **Metric.** Validation top-1 accuracy is both the selection metric and the ranking metric. The AUC deviation is declared, and per-class AUCs appear in every readout with any value under 0.7 called out (l. 771-772).
- **Seed spread.** ddof-1 per family (l. 478). Comparisons are paired, with own-sd t-intervals at df n_p − 1 and sign counts. The resolving power is stated (l. 581-628) and matches the re-runs.
- **Tautology.** Selection and reading use the same validation split, so a winner's curse is present. It is acknowledged ([L6]) and mitigated by two non-selecting companions, including a split-half on disjoint jets, and by the seeds-5-8 selection-free estimate.
- **Projection versus result.** Timing and memory are labelled projections (l. 842-846), and EBOPs is labelled "not silicon" ([L5]).

## Verdict

I would approve this STUDY for launch under the freeze rule. It has no Category A; its two B items are text or one-block-simulation fixes that change no rule. The single thing that most decides it is that the primary median-g ranking holds its "ranked" label in the rare-high-mode regime the archived N=64 seeds suggest (B2, verified here), and that its values be shown with their own 87.5 % order-statistic interval or explicitly as ranks (B1).
