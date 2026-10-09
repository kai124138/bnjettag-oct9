# STUDY physics review v2: 2026-09-27-delta-screen

Reviewer: physics-reviewer (fresh context; read STUDY.md, the scripts it cites, delta.json, screen_power.py).
Phase STUDY, iteration 2. No results exist; checks applied to the plan.

## Figures

- **None in the artifact.** STUDY has no figure and cites none. Planned figures (l. 779): forest
  plots of paired g per family with n per row, per-seed points, GPU class, placebo row and the
  Dunnett line; the floor-family package list as its own plot. Status: plan acceptable, with the
  requirements in C5 below. No ROC figure is planned; none is needed at a validation-accuracy screen.

## What I recomputed (all reproduce)

- `delta.json` sha256 = f4ad2571...8029204, matches l. 9.
- `budget.py` (uv, numpy): 302 runs, 176,000 run-epochs (E 42,000 / A07 134,000), 318 retraces,
  1,776.3 / 3,128.7 pod-hours, 8.6 / 14.7 d, cheap version 129 runs / 79,500 / 4.6-7.4 d; every
  row of the Budget tables (l. 676-682, 711-717) matches.
- `screen_null.py`: critical t 2.410 (m 12, n 4), 2.793 (m 40, n 4); P(no | null) 0.896 / 0.904;
  placebo flag 0.0336 / 0.0126; P(no | one +1 pt) 0.489 / 0.846 / 0.880 (350k) and 0.617 / 0.879 /
  0.900 (5M); ceilings 1.3 pt (5M), 2.7 pt (350k). Match l. 581-582, 636-638, 657-658, 484-489.
- `screen_power.py` k_joint 3.66 / 2.09 / 1.58 (m 19) and 4.83 / 2.50 / 1.83 (m 43); the sd_rep
  thresholds 0.058 / 0.102 / 0.134 and 0.044 / 0.085 / 0.116 pt follow as 0.3 / (k · √2).
- Arithmetic: t(0.975, 3)/2 = 1.591; 4.44 × 1.59 = 7.07; p_maj 12,579/62,000 = 0.20289, class
  counts sum to 62,000; 5 × 4,354 MiB = 21,770 = 94.5 % of 23,028.

Every seeded simulation reproduces to the digit. That is expected of a fixed-seed Monte Carlo and
is not evidence that the model behind it (normal, homoscedastic gaps, cells independent given the
seed) matches training. The one in-design check that would catch a departure from that model is
the placebo, and A2 below says the placebo is not calibrated either way.

## Findings

### (A) must resolve

**A1. The family-level max-t is calibrated for homoscedastic gaps; this design builds in heteroscedastic ones.**
Attack: t_i = mean g_i / (s_pool / √n_p,i) with one family-pooled paired sd (l. 576-583), critical
value simulated with equal variance for every cell (`screen_null.py` `draw`). Cells that keep
shapes share the init and data order with the replica at seed s (confounds 6-7), so their per-pair
correlation ρ can be well above 0 and their gap sd narrow. Shape-changing cells (the
paired-if-hash entries M001, M002, M004, M005, M016, M040, M042-M045, M049; M046 if [A17] fails)
and the Welch cells (M006, M009 on C) have ρ ≈ 0 and a gap sd up to √2 wider (the STUDY says so
itself for Welch, l. 586-587). Unstable levers (M018-M020, M028) add variance too. The STUDY also
never says how a Welch cell, which has no per-seed pair, enters t_i at all.
Evidence (my simulation, `review/het_physics_v2.py`, seed 1, 20,000 reps, the STUDY's null model with some cells wider): at
m = 40, n = 4, critical 2.793, family-wise false-"yes" rate is 0.095 with equal variances, 0.160
with 10 % of cells at 2× gap sd, 0.192 with 20 % at 2×, 0.276 with 10 % at 3×; the wide cells take
almost all of the false hits (0.13-0.27). At m = 12: 0.099 → 0.124-0.153. The pre-registered
"above the replica at family-wise α 0.10" then has an error rate up to about 2.8 × nominal, and it
selectively names the noisiest cells.
Settle: either (a) each cell's own sd (t on df n_p − 1), with the max-t critical value simulated
for the family's actual n_p vector; or (b) a pre-registered homogeneity gate on the per-pair
correlation / gap-sd column the STUDY already reports, with a stated fallback to (a). Write how
Welch and hash-failed cells enter (own-sd Welch t with Satterthwaite df, calibrated in the same
simulation), or exclude them from the max-t and say so. Rerun `screen_null.py` with a mixed-variance
row to show the chosen statistic holds 0.10.

**A2. The placebo's behaviour under the pipeline's determinism is not predicted, so it cannot calibrate anything.**
Attack: P-350 / P-5M are the base config plus a no-op key, same `experiment.seed`, same
`order_seed`, same code sha, TF32 off, `jit_compile false` (l. 142-150, 158-165). Whether two such
runs on GPU are bit-identical is unknown: "Bit-identity across packs is not assumed" (l. 452).
- If training is (near-)deterministic, the placebo gap is ≈ 0 at every seed. Then (i) it is pooled
  into s_pool (l. 577) and deflates it: my simulation with a placebo gap sd of 0.1 × the null gives
  family false-"yes" 0.121 (m 12) and 0.106 (m 40) instead of 0.10; (ii) its placebo flag can
  never fire (rate 0.000), so design validity (iv) (l. 654-658) tests nothing; (iii) "its rank is
  uniform under the null" (l. 147, 662) is false, it sits mid-list; (iv) the "exactly zero per-seed g
  is a red flag, the runs did not vary" rule (l. 525-526, 662-663) flags a healthy deterministic
  pipeline as broken.
- If training is not deterministic, the placebo measures GPU nondeterminism plus pod/pack
  offset. That is still not the null a changed-config cell faces (a config change diverges the
  trajectory from epoch 1), so its spread understates the cells' null spread.
Either way the placebo's legitimate role is narrower than stated: a check for a systematic
pod/pack/run-identity offset between cells and replica, since that offset shifts every cell's g
and is exactly what the "above the replica" claim is exposed to. At n = 4 its detection threshold
is about crit × s_pool / √4 ≈ 1.2-1.4 s_pool, so it only catches large offsets.
Settle: a PREFLIGHT determinism probe (base config, same seed, two processes, same product,
a few epochs: bit-identical or not); a written prediction of the placebo's per-seed |g| before
launch; placebo excluded from s_pool; its role restated as "systematic offset only" with its
detectable offset in pt printed; the zero-g red-flag rule rewritten to match the probe's outcome.

**A3. One replica-seed failure empties the main ranked list, and no rule fires.**
Attack: n_p counts seeds usable in both cell and replica (l. 550-552); "a cell with 3 ≤ n_p < n
is not in the main ranked list" (l. 553). At n = 4, if rep-A or rep-C loses one of seeds 1-4
(infeasible, degenerate, diverged, collapsed or certification-failed), every cell in the family has
n_p ≤ 3 and the main list is empty. Base stability pauses only above a quarter (l. 403-404: 1 of 4
is not more than a quarter), and ⌈3 · 4/4⌉ = 3 passes (l. 408-409). The ⌈3n/4⌉ rule exists
because near-floor 350k failures are expected, so this case is foreseeable, and the design leaves
the family's main deliverable undefined, which invites a post-hoc rule.
Settle: "incomplete pairs" means cell-side missing seeds only; a replica-side loss lowers the
family's n uniformly, the main list stands at that n (stated), the critical value is resimulated at
it, and the survivorship label applies to cell-side losses. (Seeds 5-8 of rep-A/rep-C cannot
substitute, since the cells run seeds 1-n; say so.)

### (B) should address

**B1. [L1] persistence check is uninformative as written.** Spearman of rep-A over seeds 1-n_350
(n = 4, 24 orderings) cannot resolve anything, and seed-rank persistence of one config is not
treatment-rank persistence across configs, which is what "one cycle predicts 7,000" needs. Label it
"not a test of L1" or replace with something that bears on it (for example, rank persistence of the
long-horizon cells M015/M031/M032 and their replicas at 500 vs their own H, stated with n).

**B2. Long-horizon cells in the same pooled sd.** M015 (1,000), M031 (1,500), M032 (2,000) are read
against replicas at their own horizon, whose seed spread need not equal the H-500 spread, yet they
enter the same s_pool and max-t (l. 576-583). Fold into A1 (own-sd statistic) or exclude them
from the Dunnett family and report them in their own list.

**B3. sd_rep from survivors.** sd_rep is over feasible, non-degenerate, certified seeds of 1-8
(l. 395-397). Seeds that fail are the ones most likely to have sat in a tail; dropping them biases
sd_rep low, which can pass the 1.3-pt ceiling or, in principle, qualify a larger n. Print the usable
count beside sd_rep and pre-register that sd_rep on ≤ 6 of 8 usable seeds is reported as such and
cannot by itself raise n.

**B4. "the family's actual m and n" (l. 581) must be the actual n_p vector** per cell, after
exclusions X1-X4 and incomplete pairs, not a single n. State it.

**B5. Metric against the thesis.** Selection and ranking on top-1 validation accuracy (house
record uses macro AUC under budget; deviation flagged, l. 774). For a trigger the operating region
is low mistag; neither metric is it. Acceptable at a screen; the accuracy-vs-AUC rank concordance
(l. 617) should be given a pre-registered consequence (for example, a cell ranked in the top 12 on
one and outside it on the other is flagged to Kai, as the companion flag does).

### (C) suggestions

- **C1. Significance mode will not arm** at any plausible sd_rep (needs ≤ 0.044-0.134 pt against
  the 0.6-pt referral line and the 3.14-pt archived spread, l. 495-498) but leads the Question
  (l. 82-85). Put ranking mode first and label significance mode "not expected to arm".
- **C2. Split-half as a second companion.** It costs no GPU, removes best-of-H selection bias on the
  read half directly, and at an expected seed sd ≥ 0.6 pt the binomial SE increase (0.16 → 0.23 pt)
  is negligible. The last-epoch companion measures something else (end-of-cycle state).
- **C3. Wall clock at E K = 5.** `budget.py` schedules E at K = 5 (`SE_E`), while l. 730 expects the
  canary to return K = 4 on 23-24 GB cards. Labelled a projection, but restate the table at K = 4.
- **C4. Family definitions.** BH m = 19 at 350k contains the floor-family Welch cells; the Dunnett
  family (m = 12) excludes them. Consistent with the list separation; say why once, in one place.
- **C5. Planned forest plots.** When n_p differs across cells the Dunnett line is not one line in
  g units; draw per-cell thresholds or plot t. Label each bar with which interval it is (own sd or
  pooled), n_p, and "validation, n = 62,000, screen, not quotable".

## Other checks

- Question and thesis: well posed as a lever screen; it states that it does not measure the cost of
  binary weights and yields no quotable number (l. 98-108). Tuning asymmetry against untuned
  baselines M047-M050 is named with a rule for confirm. Adequate.
- Matching: key-diff gate against the replica at every seed (l. 152-156), same cache and y_val
  sha, same seed/order_seed, GPU product per pair, diagnostics-on invariance. Adequate.
- Tautology: best-of-H checkpoint is selected and ranked on the same 62,000 jets; acknowledged
  ([L6], companion readout). ROC-test untouched. Acceptable for nominating confirm cells, not for
  any gap estimate.
- Projections labelled as projections (timing, r, K). No synthesis claim.
- Resolving power stated honestly: ±1.35 pt half-width at sd_d 0.85, ±7.1 pt at the archived
  spread; +1-pt effects barely above chance at σ 3.14.

**Verdict.** I would approve this STUDY for launch once A1-A3 are fixed; the deciding question is
whether the family-level max-t, the only inferential statement ranking mode makes, holds its stated
α 0.10 on the mixed-variance cell set the design actually contains, with a placebo whose behaviour
is predicted rather than assumed.
