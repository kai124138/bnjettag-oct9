# STUDY physics review v10: 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context; artifact, its cited evidence and the Sun et al. PDF only).
Artifact: `campaigns/2026-09-26-training-batch/STUDY.md` (2,658 lines, working tree 2026-09-28).
No compiled PDF sits beside it. Phase STUDY: no results exist, so the checks are applied to the plan.

## Figures

No figure file exists or is cited as an image at STUDY. Each pre-registered figure (l. 1330-1371) is checked as a specification.

| figure (spec) | status |
| --- | --- |
| Primary measurement: per-seed A ROC-test accuracy, seed mean, 95 % t-interval, k, lines at 79.4 / 78.4 / 79.8 / 77.9 % | spec only; OK. Split and n are in the caption (ROC-test, n = 260,000), and the references are labelled single-model |
| Recipe ladder: paired-gap panel A − D, D − R, A − R, A1000 − R, D1000 − R | spec only; OK. Paired Δ with t-interval and n_pairs. The caption's "R crosses GPU type" is stale (C3) |
| Per-class ROC, ROC-test, log mistag axis, seed band sd ddof = 1, k; A/R panel separate from A07-350/C panel; per-class AUC mean ± sd in legend | spec only; OK. It has the log axis, splits by budget, and puts AUCs in the legend |
| Selected epoch, cycle index and best-feasible validation accuracy per cycle | spec only; OK. Labelled "validation, n = 62,000" |
| Accuracy-versus-EBOPs ladders (E: B, A; A07: A07-350, C) with EBOPs above the floor and paired-gap panels | spec only; OK. Empty rungs are drawn and degenerate seeds are counted |
| Attention state per arm (Q/K, V at 0 bits, entropy / log 64, 0.99 cut, A07-350 expectation) | spec only; OK |
| Validation − held-out per run (winner's curse) | spec only; OK |
| Interim readouts | spec only; OK. Labelled validation |
| Second wave: A − NB paired panel; H − NB and H − A Welch; per-class ROC A/NB/H; NB width distribution; per-class paired AUC gaps; A − FP32-E and NB − FP32-E in their own panel | spec only; OK. Iso-EBOPs and package gaps never share a panel |

No figure can contradict a table yet. The specifications already carry the log mistag axis, a ddof = 1 seed band with k, and split and n in every caption.

## Numbers I recomputed

- Archived Round-14 N=64 sizing spread from `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz` (keys `y`, `score`, shape (260000, 5)): W1A8 top-1 67.18 / 72.64 / 67.21 %, mean 69.007, sd (ddof 1) 3.145 pt; FP32 79.42 / 78.83 / 79.10 %, mean 79.115, sd 0.297 pt. These match l. 489 and l. 1212. **Verified.**
- ROC-test class fractions [0.2016, 0.1941, 0.2009, 0.2011, 0.2023]. The threshold p_maj + 5·SE at n = 62,000 comes to 0.2104, matching "about 0.21" at l. 1034. The binding value comes from gated `y_val` at PREFLIGHT, as the artifact says. **Verified.**
- Interval multipliers (scipy): t(0.975,7)/√8 = 0.8360, t(0.975,5)/√6 = 1.0494, Welch 8 v 8 t(0.975,14)·√(2/8) = 1.0724. The zero-correlation paired value 0.836·√2·3.145 = 3.72 pt. The 80 %-power effect size for a paired t at n = 8 is 1.156·sd_diff. The sizing table (8/12/16/18/20 pairs at sd_diff ≤ 1.196/1.574/1.877/2.011/2.137 pt) matches l. 1183-1192 after rounding down. For A − FP32-E at zero correlation the half-width is 0.836·√(3.145² + 0.297²) = 2.64 pt (l. 1258, "about 2.6"). **Verified.**
- Comparand: `literature/jet-tagging-transformers/2510.24784_...pdf`, pdftotext l. 261, "Deep Sets (HGQ) 64 79.4 44 191 1 0". §3 says "All models trained in this work have been trained with a target EBOPs of 350,000 ... PID controller over β", and the "constrained to at least one bit" sentence reads as quoted. Linformer N=64 per-class legend values 0.941/0.921/0.972/0.968/0.964 appear in the extracted legend text. **Verified.**
- Floor ratios: 171,526/350,000 = 0.490; 343,053/350,000 = 0.980; 5e6/4,580,398 = 1.092; 4,630,276/4,580,398 = 1.011; 5e6/343,053 = 14.6. These are consistent with the text. Regime-B arithmetic: 127.45 + 90.61/10 = 136.5 s, T_run = 11.06 d. It is labelled arithmetic, not a measurement, and that is correct.

No suspicious agreement arises at STUDY. The one exact agreement (E1 × 2 = E, residual 0) is labelled by the artifact as partly an identity of the trace's own terms (l. 638-640).

## Findings

### (A) Must resolve

**A1. Regime B introduced a controller/feasibility quantity mismatch, and nothing pre-registered says how its effect is read.**

*The attack.* Slot P (l. 1483-1492) says BetaPID reads the in-training EBOPs on 9 of every 10 epochs and the traced full-split EBOPs on the 10th. Feasibility test (a) and selection use only the traced value (l. 1464-1466). Between traces each WRAP quantizer follows `i ← max(i − i_decay_speed, i_batch)` per step (l. 1495-1497). After each full-split reset, `i` sits at the full-split maximum and then decays toward the per-batch maximum. The artifact itself gives the rate: 0.2 bits per epoch at 200 steps (l. 2116). The per-batch maximum over 2,790 jets is at most the full-split maximum over 558,000 jets, so the expected sign from the cited code is in-training EBOPs ≤ traced EBOPs.

If that holds, the PID spends most epochs holding a quantity at 350k that sits systematically below the one test (a) reads. The traced epochs then land above target by the gap. The feasible traced-epoch count falls, and so can k. The budget claim (l. 1025-1041) would then be falsified by a mechanism added on 2026-09-27 to save wall time, and it would be reported as an outcome of "this recipe". The same mechanism shifts which checkpoints are selectable in every traced arm. R has 101 traced epochs against 701 for the Chang-schedule arms, so A − R and the R feasibility count carry it asymmetrically. A − NB shares it, but NB's weight widths react to β while A's cannot, so it need not cancel.

*The evidence.* `plan.md` DECISION R-B1 (l. 888-897) says: "No measurement of the in-training / traced ratio exists yet (`ebops_in_training_over_traced` is logged by every [D20] run; the regime-A canary pull did not fetch it)." STUDY reports that ratio per run at the pilot (l. 1493-1494) but attaches no consequence to it. The budget claim's list of screened failures (controller failure, divergence, collapse, l. 1039-1041) does not name this mechanism, and the pilot A rule (l. 1611-1615) only catches the case where both seeds fail completely.

*What would settle it.* Add one dated paragraph before the pilot's epoch-500 readout, with no arm, seed or target change:
- a pre-registered readout of the median traced / in-training EBOPs ratio and the fraction of traced epochs meeting (a), per run;
- a threshold, chosen now, above which a low k or a budget-claim failure is labelled "setpoint-quantity mismatch (regime B)", not a recipe outcome;
- the named remedy Kai chooses between if the threshold is crossed. R-B1 already lists "feed the in-training value on every epoch" as the alternative; the other option is a traced-quantity-only PID update.

State the sign as expected from `FixedPointQuantizerKIF.call`, not as measured.

### (B) Should address

**B1. FP32-E has ten times A's selection candidates, and the package label predates regime B.**

FP32-E selects over "all 7,000 epochs that meet (c)" (l. 695-697). A, NB and every traced arm select over at most 701 traced epochs (l. 899). The A − FP32-E package label (l. 780, confound 12 at l. 843-847) still reads "the selection domain (≤ target against all epochs)", written before regime B. This is the one gap the artifact lets REPORT cite on the "close to full precision" axis (l. 460-468). A tenfold candidate-count asymmetry adds winner's-curse inflation on validation and a small real held-out advantage to FP32-E, and it costs nothing to remove.

*Settle:* restrict FP32-E's candidate grid to the slot-T epochs (`e == 0`, `(e + 1) % 10 == 0`, last epoch), or keep the full grid and name "7,000 against 701 candidate epochs" in the package label and confound 12. Pre-register it now, before any FP32-E number.

**B2. The one thesis-bearing gap is expected to be uninformative at 8 pairs, and the cap that decides its power is still open.**

The artifact states this honestly: A − NB is detectable at 80 % power only if sd_diff ≤ about 0.86 pt (l. 1213-1216), and "not falsified at this resolution" is the stated expected outcome. The only sd evidence at N=64 is 3.145 pt (recomputed above). That puts the zero-correlation paired half-width at about 3.7 pt, against a Sloot prior of about 1 pt. The adaptive extra-pair rule reads only sd_diff, not the mean or sign, and that is acceptable. But the Kai row "extra A/NB pairs (cap)" is open (l. 2468). Without a cap the campaign may deliver the thesis comparison at 3-5 pt resolution.

*Settle:* ask Kai for the cap before the wave-2 epoch-500 readout, as the row allows. The REPORT should print the resolvable gap in the first sentence of any A − NB statement, not after it.

### (C) Suggestions

**C1. The budget claim is a screen by construction.** Three things together make a pass nearly automatic: a PID held at the target, the ≤ target filter, (b) passing at 1 EBOP above the floor, and (c) at about 21 %. The artifact says so (l. 1039-1041). Consider presenting it in REPORT as "feasibility count" beside the claims rather than as one of three falsifiable claims.

**C2. "Upper estimate" wording (l. 972-973, l. 1066-1068).** Survivor bias makes the arm mean an upper estimate only with respect to dropped seeds. Threshold (c) at about 21 % keeps a 30 %-accuracy seed, which pulls the mean down. The range and low-accuracy counts (l. 1107-1113) already show this. Word the label as "upper estimate with respect to dropped seeds".

**C3. The GPU-class statements for R contradict each other.** Confound 9 says every wave-1 pod runs on A10, so every same-seed comparison stays within one class (l. 813-815). The Pods paragraph (l. 1519-1520) and the recipe-ladder caption (l. 1338-1339) say R crosses GPU type. R is wave 1, and the stale sentence dates from before the K=5 A10 packing. Pick one.

**C4. Trigger operating point.** Signal efficiency at mistag 10⁻² per class is pre-registered beside A − NB and A − FP32-E only (l. 1229, l. 1267). A Level-1 reader will look for it beside A's primary number and the A − R ladder too. Add it there, and at 10⁻³ if statistics allow at n = 260,000.

**C5. Size of the document.** 38,412 words, of which about 370 lines are change log (`review/STUDY_validators_v10.txt`). C3 is the kind of drift this produces. Consolidating by deletion before PASS would lower the chance that a stale sentence becomes a REPORT sentence.

## Question, arms and statistics (brief)

- **The question is well posed** for what it claims to measure. The artifact correctly says the first wave does not measure the cost of binary weights. It confines the thesis-bearing statements to A − NB (iso-EBOPs, not iso-cost, with [L2] on the unbilled absmean scale and accumulator) and A − FP32-E (a labelled package). Scope excludes W8A8, the A8 → A6 → A4 ladder and any DSP, LUT or latency statement ([L7]). That is a real limit on the thesis bearing, and it is stated, not hidden.
- **Arms are matched.** Each one-knob comparison names what varies. Package comparisons are labelled. Pairing rests on kernel-hash gates ([A17], [A22], [A25]) with a Welch fallback fixed before data.
- **Statistics are pre-registered correctly:**
  - ddof = 1 over seeds;
  - paired t, df = n − 1, with sign count and per-pair correlation;
  - McNemar on discordant feasibility;
  - Holm families fixed, with m under dropouts;
  - per-class AUC beside macro;
  - the validation − held-out gap reported against winner's curse;
  - ROC-test touched only after selection;
  - interim readouts labelled validation.
- **Resolving power is stated** at both sd bounds, with the formula.
- **No tautology** between selection and evaluation splits. Certification retraces on train only and never on validation or test.

## Verdict

Do not approve yet. The deciding item is A1: regime B changed the quantity the controller holds at target without changing the quantity feasibility is tested on, and nothing pre-registered says how a resulting drop in k is read. The fix is one dated paragraph before the pilot's epoch-500 readout, not an arm, seed or target change.
