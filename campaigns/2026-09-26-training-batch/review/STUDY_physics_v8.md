# STUDY physics review v8: 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context; read only `STUDY.md` and the files it cites).
Artifact: `campaigns/2026-09-26-training-batch/STUDY.md` (2,281 lines, working tree after the
arbiter v7 fixer pass). No compiled PDF exists beside it. Phase STUDY: no results, so the checks
apply to the plan.

## Figures

No figure exists at STUDY. Every pre-registered figure (STUDY l. 1192-1228) is listed with its
status and the gaps found in its spec.

| figure (pre-registered) | status | spec check |
| --- | --- | --- |
| Primary measurement: per-seed A ROC-test accuracy, mean, 95 % t-interval, lines at 79.4 / 78.4 / 79.8 / 77.9 % (l. 1193-1197) | not produced; spec checked | split, n and "external single-model" are in the caption spec; k is in the legend. The reference's own noise (≥ 1 pt, [L1]) is not drawn (C1) |
| Recipe-ladder paired-gap panel: A − D, D − R, A − R, A1000 − R, D1000 − R (l. 1198-1200) | not produced; spec checked | paired Δ with t-interval and n_pairs; GPU class noted. OK |
| Per-class ROC on ROC-test, log mistag axis, seed band sd ddof = 1, A and R; A07-350 and C in a separate panel (l. 1201-1204) | not produced; spec gap | the log mistag axis, the split, n and the seed count are specified. The spec does **not** say the legend prints the per-class AUC (seed mean ± sd), so the legend-against-table check cannot run at REPORT (F1) |
| Selected epoch, cycle index, best-feasible validation accuracy per cycle (l. 1205-1208) | not produced; spec checked | labelled validation, n = 62,000. OK |
| Accuracy-versus-EBOPs ladders, E (B, A) and A07 (A07-350, C), with paired-gap panels beneath (l. 1209-1214) | not produced; spec checked | EBOPs above the 0-bit floor per rung, empty marker for 0/8, degenerate seeds counted. OK |
| Attention state per arm (Q/K and V fraction at 0 bits, entropy / log 64), A07-350 expectation marked (l. 1215-1216) | not produced; spec gap | no split or n in the caption spec: the widths come from `activation_widths.jsonl` (a checkpoint property) and the entropy from validation, n = 62,000 (l. 1185). Both should be in the caption. No threshold for "collapsed" is drawn (B2) |
| Validation − held-out accuracy per run (l. 1217) | not produced; spec checked | OK |
| Interim-readout figures, "validation, n = 62,000" (l. 1218) | not produced; spec checked | OK |
| Second wave: A − NB paired-gap panel with a 1.0-pt line, beside H − NB and H − A Welch intervals; per-class ROC with A, NB, H; NB weight-width distribution; per-class paired AUC-gap panels for A − NB and A − FP32-E (l. 1219-1224) | not produced; spec checked | iso-EBOPs and package gaps are kept out of one panel (l. 1225-1227). The per-class ROC has the same legend-AUC gap as above (F1) |
| FP32-E: A − FP32-E and NB − FP32-E in their own panel, "package: 350k against unconstrained FP32" (l. 1225-1228) | not produced; spec checked | no EBOPs position for FP32-E. OK |

F1 (figure spec, class C, but it applies to every ROC figure): require the legend of every per-class
ROC figure to print the per-class ROC-test AUC as seed mean ± sd (ddof = 1, k), so the REPORT
plot-validator can check the legend against the table.

## What I verified (recomputed or read from the cited source)

- Round-14 N=64 sizing spread, recomputed from `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz`
  (keys `y`, `score`; n = 260,000 each): W1A8 per-seed top-1 67.18 / 72.64 / 67.21 %, mean
  69.01 %, **sd 3.145 pt (ddof = 1)** (population sd would be 2.568); FP32 79.42 / 78.83 / 79.10 %,
  79.11 ± 0.297 pt. Matches the reference table (l. 383) and the 3.14 pt used for sizing.
- Threshold (c): ROC-test class fractions 0.2016 / 0.1941 / 0.2009 / 0.2011 / 0.2023; p_maj +
  5 · √(p_maj(1 − p_maj)/62,000) = **0.2104**. Matches "about 0.21" (l. 919), which STUDY labels
  review arithmetic on ROC-test; the binding value is the PREFLIGHT one on `y_val`.
- Interval factors: t(0.975, 7)/√8 = 0.836, t(0.975, 5)/√6 = 1.049 (l. 741-744). Sizing table
  (l. 1066-1072): sd_diff limits 1.196 / 1.574 / 1.877 / 2.011 / 2.137 pt at n = 8 / 12 / 16 / 18 /
  20; the table rounds down correctly. H − NB Welch 1.07 · sd, 3.4 pt; A − FP32-E paired and Welch
  ≈ 2.6 pt; McNemar two-sided 0.125 / 0.0625 / 0.031 / 0.016: all reproduce.
- Floors in the evidence files: `code/evidence/static_floors_trace_step2.json` headroom 178,474
  (E) and 6,947 (A07), zero-floor/target 0.490 / 0.980, current-quantizer ratios 13.09 / 7.72;
  `static_floors_fix6_a07_e_e1.json` totals 605,197 / 801,805 / 368,134 / 478,726 / 85,763 /
  282,371 / 392,963. All match the text. The Linformer and MHA macro means 0.9532 / 0.9428
  (l. 380) are the arithmetic means of the quoted legend values.
- `trace_cost_cpu.json`: trace/train 0.657 (E) and 0.664 (A07), 16,740 rows, CPU, as stated.
- `a17_pairing_d25_8seeds.json`: `n_shared` 15 at each entry, as [A25] states.
- `pytest_shipped_77f1ca4e.log`: 71 passed, 2 skipped, including the uniform-logits and one-hot
  entropy tests [A26]; `cpu_gate_shipped_77f1ca4e.log` `PREFLIGHT_ALL_PASS 26 production 24
  pilot_only 2`; `cpu_gate_d25.log` `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`, C′
  `I_DECAY_OK ... quantizers 0 values []`.
- Budget arithmetic (467 / 933 / 1,750 / 63 / 876 pod-hours, 15.1 d, 172.8 s, 13,760 W&B
  versions) reproduces.

**Suspiciously good agreement.** None of this tests the science. Every number checked is
arithmetic, a CPU trace on synthetic data, or, as STUDY says itself (l. 532-533), an identity on
the trace's own per-layer terms. The one independent prediction that held is E1's per-head softmax
split (E1 × 2 = E, residual 0). Nothing at STUDY can yet be suspiciously good. The first places
where it could be are the epoch-500 readout (collapsed seeds agree closely; STUDY already sends a
mean that fails (c) to Kai, l. 779-780) and certification, which checks determinism, not
accounting (l. 837).

## Assessment of the design

- **Question and bearing.** The first wave is honestly descriptive: it varies no weight type, and
  STUDY says so (l. 324-334). The only thesis-bearing comparison is A − NB (iso-EBOPs, not
  iso-cost) in the second wave, and A − FP32-E is labelled as a package. The hardware half of the
  thesis (DSP ≈ 0) is correctly ruled out of scope ([L7]), with the observation that the published
  comparands are already DSP = 0 (l. 347-352). The activation ladder A8 → A6 → A4 is out of scope
  (l. 354-356). That scoping is correct and unusually explicit.
- **Matching.** Arms share the split, cache, gate, standardization, quantizer, controller, seeds,
  order and (gated by kernel hashes) the init. The package comparisons (A − R, D − R, A − A07-350,
  A − FP32-E, H − NB) are labelled as packages. OK.
- **Baselines.** FP32-E and NB run the same recipe, epochs and selection as A, so they are tuned as
  hard as the binary arm. There is no 8-bit baseline, and Scope says so.
- **Metric.** Top-1 accuracy is primary because the replication target is an accuracy number, and
  selection uses validation accuracy, so the metric used for selection is the metric reported. Macro
  and per-class AUC sit beside it, with an AUC-selected sensitivity. OK; see C2 for the trigger
  metric.
- **Tautology.** Selection uses validation only and ROC-test is touched once. The WRAP ranges are
  traced on train only, and validation is kept out of the range fit so that it wraps as ROC-test
  does. The per-epoch trace feeds both the PID and the feasibility test, and STUDY states that
  certification is determinism only. None of this is tautological.
- **Statistics.** Sample sd with ddof = 1; paired t with df = pairs − 1 and a sign count; McNemar
  on feasibility; survivor bias labelled with a pre-registered imputation line; Holm families with
  m fixed under dropouts before any number; winner's curse reported as validation − held-out.
  Per-class AUCs sit beside every macro number. No uncertainty is a round number without a source.

## Findings

### (A) Must resolve

None. No part of the plan, as written, would produce a wrong number or an unlabelled comparison.

### (B) Should address

**B1: the pilot as registered is not the pilot as launched (disputed fact).**
Attack: STUDY l. 1309-1312 registers the pilot pod as A-s1, A-s2, D-s1, **A07-350-s1**, C′-s1 and
E1-s1 (K=6), and l. 1351-1353 pre-registers an A07-350-s1 attention-state readout at epoch 500.
Commit 956a491 (git log) reads "pilot kai-chang0926-pilot-77f1ca launched ... on an A10
(A07-350-s1 dropped after OOM)". STUDY carries no amendment. I did not open RUN.md, which STUDY
does not cite. If the commit is accurate, two consequences are physics, not ops: (i) the
pre-registered check of the A07 floor accounting (the only pilot test of the "at most 3
per-constituent input bits" expectation) has no data before production; (ii) a d32 arm that OOMs
at K=6 on an A10 puts every production seed block at risk, since each packs C and A07-350 on
A07. The K=3 fallback (l. 1294-1297, 16 pods) then becomes the expected branch, which changes the
pod count Kai answered (8-10) and the overlap with wave 2 (about 14 pods).
Settle: a dated amendment to the pilot composition stating what replaced A07-350-s1, where the
A07-350 floor-accounting check now happens (for example the first production epoch-500 readout),
and whether the K=6 memory assumption for production still holds, with the measured peak memory
per process. Paths: `STUDY.md` l. 1309-1312, 1351-1353, 1294-1297, 1408-1411; commit 956a491.

**B2: Deep-Set collapse has no pre-registered threshold.**
Attack: WRAP overflow received a numeric threshold before any pilot number (0.1 %, l. 1174). The
attention diagnostics did not: the Q/K and V fractions at 0 bits and the entropy / log 64 are
reported "beside every accuracy number" (l. 1162-1190) with no rule that turns them into
"collapsed". Under [D19], E reaches 350k only because Q·K and A·V may prune to 0 bits (l.
544-548), so a Deep-Set-class A (and NB) at the selected checkpoint is a live outcome, not a
corner case. The thesis says "transformer jet tagger". Without a pre-registered cut, whether
A − NB and A − 79.4 compare transformers or Deep Sets becomes a post-hoc call made after the
numbers exist.
Settle: fix now, before the pilot's epoch-500 readout, a collapse label (for example: Q/K
fraction at 0 bits = 1, or V fraction at 0 bits = 1, or row-renormalized entropy / log 64 ≥ a
stated value such as 0.99 on every head) and its wording consequence: a selected checkpoint that
meets it is labelled "Deep-Set-class at 350k", and the A − NB, A − FP32-E and A − 79.4 headlines
carry the per-arm count of such seeds. Descriptive only, like the overflow label.

**B3: resolving power is given as a half-width, not as detectable-gap power, for the one
thesis-bearing comparison.**
Attack: STUDY states the 95 % half-width (0.836 · sd_diff; about 3.7 pt at zero pair correlation
and the archived spread, l. 757-760) and the sizing formula for ±1.0 pt. It does not state the
gap the design can detect. My arithmetic (paired t, α = 0.05 two-sided, 80 % power, 8 pairs):
about **4.4 pt** at sd_diff = √2 · 3.14; **1.15 pt** at sd_diff = 1.0 pt; 0.31 pt at the N=8 proxy.
The stated prior (Sloot, l. 1054-1057) puts the expected cost of binary weights at about 1 pt
(AUC-scale, different task). Unless sd_diff comes in near or below 1 pt, the expected outcome of
A − NB is "not falsified at this resolution". The wording rules already prevent reading that as
support ("at most |L| pt" headline, l. 1037-1043; no non-inferiority pass). What is missing is the
plain statement, before 24 second-wave runs × 7,000 epochs are spent, that the weight-type claim
at 8 pairs probably cannot resolve the size of cost the prior expects.
Settle: one sentence in the weight-type claim and in "Where I am not sure" giving the 80 %-power
detectable gap at the proxy and archived spreads, and a rule that the second-wave epoch-500 packet
(which already carries sd_diff, l. 1078-1081) puts that detectable gap in front of Kai beside the
extra-pair cap. This does not block STUDY. It should block claiming anything about "the cost of
binary weights" from 8 pairs if the measured sd_diff exceeds about 1.2 pt and no extra pairs are
approved.

### (C) Suggestions

- **C1. The reference's noise beside A − 79.4.** The t-interval on A − 79.4 carries our seed noise
  only. [L1] puts the reference's own uncertainty at ≥ 1 pt (REPRO-CHANG moved their N=64 rows by
  +1.05 and +2.7 pt). Print that beside the 78.4 % line and in the primary figure's caption, so a
  reader does not take the interval for the uncertainty of the distance. The paper's selection rule
  is unstated and may be test-based, which would bias the reference upward against our
  validation-selected A. Say so beside the distance.
- **C2. Trigger metric for the primary.** Signal efficiency at mistag 10⁻² is pre-registered only
  beside the second-wave gaps (l. 1105, 1143). A Level-1 trigger operates there, and the thesis
  speaks of tagging efficiency. Extend it to A and R (the recipe claim) and report it per class for
  A beside A − 79.4 (no published comparand, so descriptive).
- **C3. The budget claim is a weak screen, by design.** With 178,474 EBOPs of headroom and (c) at
  about 0.9 pt above chance, a pass is expected (STUDY says so, l. 924-926). Keep the per-seed
  validation accuracy printed beside k/8 as registered, so that "6/8 feasible" is never read as
  "6/8 tag well".
- **C4. Duplicated rule text drifts.** The "≥ 1-bit attention ... `xfm` (key_dim 16) is expected to
  be at least as constrained" sentence appears verbatim at l. 546, 947 and 2045, and the survivor
  imputation paragraph twice (l. 1044-1053, 1119-1128). The first-wave "Family size under dropouts"
  paragraph (l. 1008-1009) ends with the second-wave sentence "against the thesis in the second
  wave", which is out of place in the first-wave family. Define each rule once and cite it.
- **C5. The epoch-500 sd gate is noisy.** An sd from 8 seeds has about ±25 % relative error, and at
  epoch 500 it may understate the terminal spread (l. 773-774). The 0.6-pt gate only routes to Kai,
  so this is acceptable. Print the 95 % chi-square interval on that sd beside it.
- **C6. The (b) condition is nearly vacuous.** "EBOPs above the 0-bit floor > 0" is met by one
  alive bit. It is harmless because (c) does the work, but the budget claim's wording ("above the
  0-bit floor") should not imply more.

## Verdict

Approve at STUDY. The deciding point is that the design separates a descriptive first wave from a
low-power, thesis-bearing second wave and pre-registers honest wording for the likely unresolved
A − NB outcome. B1 (the pilot composition and the K=6 memory assumption after the reported
A07-350-s1 OOM) must be amended before wave-1 production launches, and B2 before the pilot's
epoch-500 readout.
