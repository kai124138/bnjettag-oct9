# STUDY physics review v9: 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context; read STUDY.md in full, RUN.md as cited by the
pilot amendment, the Sun et al. PDF Table 1 and §3, the R14 N=64 `.npz`, and the evidence
files `static_floors_fix6_a07_e_e1.json`, `cpu_gate_d25.log` and
`cpu_gate_shipped_77f1ca4e.log`). No earlier review, methodology, conventions or memory
file was read.

## Figures

No figure exists at STUDY: there is no compiled PDF, and every figure is pre-registered for
REPORT (STUDY l. 1233-1274). I checked each specification against the figure checks.

| pre-registered figure | status |
| --- | --- |
| Primary measurement (per-seed A ROC-test accuracy, mean, 95 % t-interval, k; lines at 79.4 / 78.4 / 79.8 / 77.9) | Not yet made. The spec is adequate: split, n and k are in the caption and legend, and the external references are labelled single-model. |
| Recipe ladder, paired-gap panel (A − D, D − R, A − R, A1000 − R, D1000 − R) | Not yet made. The spec is adequate: paired Δ with t-interval and n_pairs, and GPU class in the caption. If [D15] truncates the terminal epoch, the A1000/D1000 rungs stay valid, but the "7,000" framing does not (B1). |
| Per-class ROC on ROC-test (A, R; A07-350 and C in a separate panel) | Not yet made. The spec is adequate: log mistag axis, seed band with ddof = 1, k, and per-class AUC as mean ± sd in the legend. Budgets are kept on separate axes. |
| Per-run selected epoch and cycle index, best-feasible validation accuracy per cycle | Not yet made. It is labelled validation, n = 62,000. "14 points per run" assumes 7,000 epochs (B1). |
| E and A07 accuracy-versus-EBOPs ladders with paired-gap panels | Not yet made. The spec is adequate: EBOPs above the floor on each rung, empty markers for 0/8, and degenerate seeds counted. |
| Attention state per arm (Q/K and V at 0 bits, entropy / log 64, 0.99 cut, A07-350 expectation) | Not yet made. The spec is adequate. |
| Validation − held-out per run | Not yet made. The spec is adequate. |
| Interim readouts | Not yet made. They are labelled validation, n = 62,000. |
| Second wave: A − NB paired panel; H − NB and H − A Welch; per-class ROC with A, NB, H; NB width distribution; per-class paired AUC-gap panels | Not yet made. The spec is adequate. Iso-EBOPs and package gaps are never drawn in one panel, and FP32-E gets no EBOPs position. Both rules are correct. |

No figure contradicts the text, because none exists yet. REPORT gets the figure checks in full.

## Independent checks (recomputed)

- **Archived N=64 sizing spread.** Recomputed from `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz`
  (keys `y`, `score`, shapes (260000, 5)). W1A8 top-1 is 67.176 / 72.638 / 67.207 %, mean
  69.007, sd (ddof = 1) 3.145 pt. FP32 is 79.422 / 78.828 / 79.095 %, mean 79.115, sd 0.297 pt.
  Both match the reference table (l. 401).
- **Interval factors** (scipy). The half-width factor t(0.975, 7)/√8 is 0.836, and at k = 6 it
  is 1.049. The sizing table thresholds are 1.196 / 1.574 / 1.877 / 2.011 / 2.137 pt for
  8 / 12 / 16 / 18 / 20 pairs, which matches l. 1086-1095 rounded down. The 80 %-power
  detectable paired gap at 8 pairs (noncentral t, two-sided α 0.05) is 1.156 · sd_diff; the
  artifact says 1.16. At √2 · 3.145 that gives 5.16 pt; the artifact says 5.2. The Welch H − NB
  half-width is 1.07 · sd, 3.37 pt at 3.14; the artifact says 3.4. The McNemar reach values
  (0.125 / 0.0625 / 0.031 / 0.016) are verified.
- **Threshold (c).** p_maj + 5·SE at p ≈ 0.20 and n = 62,000 is 0.208, consistent with "about
  0.21". The real value comes from PREFLIGHT.
- **Comparands.** Sun et al. Table 1 (pdftotext) gives Deep Sets (HGQ) N=64 at 79.4 %,
  Linformer at 79.8 % and MHA at 77.9 %, with DSP 0 on every row except the three QKeras
  rows. §3 says "All models trained in this work ... target EBOPs of 350,000 ... PID". The
  attention "constrained to at least one bit" wording is as quoted. All verified.
- **Floors.** 171,526, 85,763, 343,053, 368,134, 282,371, 533,435, 619,198 and 98,304 are
  present in `static_floors_fix6_a07_e_e1.json`. The headroom arithmetic (178,474; 6,947;
  264,237; 7,168 / 178,474 = 4.0 %; 49 % and 98 % softmax shares) is correct.
- **Gate lines.** `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2` is at
  `cpu_gate_d25.log:119`, and `26 production 24 pilot_only 2` is at
  `cpu_gate_shipped_77f1ca4e.log:55`, as cited.

## Findings

### (A) must resolve

None in the design's science. The arms are one-knob or labelled packages. Selection is on
validation and evaluation on an untouched held-out split. Seed spread uses ddof = 1. Gaps are
paired with a t-interval, sign count and pair correlation, and Welch applies only where the
init-hash gate fails. Per-class AUC sits beside the macro metric. Survivor bias is carried
into the distance and into the imputation line. The resolving power is stated with its
consequence: "flat" means "cannot resolve below about 3-4 pt".

### (B) should address

**B1. The canary has fired the [D15] "> 14 d" branch, and the STUDY still states the opposite
expectation.**
- *Attack:* The STUDY (l. 1305-1306, [D15], the FLAG block at l. 2283) states "Expected [D15]
  branch: fits 14 days single-wave". Every wall-clock and pod-hour number is built on the
  112.6 s A07 prior: 9.1 d, 1,750 pod-hours, the 15.6 h / 26 h pilot, and 876 pod-hours for the
  second wave.
- *Evidence:* RUN.md, which the STUDY cites in its own pilot amendment (l. 1374-1394), measured
  mean s/epoch over epochs 1-10 at K=6 on an A10:

  | arm | s/epoch | T_run |
  | --- | --- | --- |
  | A-s1 | 219.65 | 17.8 d |
  | A-s2 | 219.37 | 17.8 d |
  | D-s1 | 215.16 | 17.4 d |
  | C′-s1 (epochs 1-5 only) | 293.6 | 23.8 d |
  | E1-s1 (pilot-only) | 163.88 | 13.3 d |

  RUN.md l. 156-162 and 231-237 hold these numbers. Only E1 fits, and it is a pilot-only arm.
  A07-350 has no clean epoch, so C and A07-350, the likely wall-clock binders, have no timing
  at all.
- *Consequences the STUDY has not drawn:*
  - The frontmatter question, the arms table and [D4] fix 7,000 epochs. One [D15] option is a
    terminal epoch of 2,000 or 4,000. If Kai takes it, the question text, the "14 points per
    run" figure and the Seeds caveat about "14 restarts" all change.
  - The K=7 slot rules for FP32-E and NB (l. 1580-1588, 1553) require a measured T_run at K=7
    of at most 14 d. The K=6 measurement is already 17.8 d with five resident processes, so
    those branches are effectively closed unless K drops.
  - The second-wave cost is stale by about 2×.
- *What settles it:* a dated amendment that
  - records the measured s_e and T_run per arm, labelled telemetry;
  - states that the [D15] branch has fired and production waits for Kai;
  - replaces "expected: fits 14 days" with the measured basis;
  - states explicitly that the question's epoch count, the cycle-count figure and the Seeds
    restart caveat are provisional until Kai's [D15] answer is folded in;
  - makes the open Kai row "wave-1 packing after the A10 out-of-memory" (l. 2159) carry timing
    as well as memory.

  The pre-registration is not final until that answer is in the text.

**B2. Two canary fail-conditions have no readable input.**
- *Attack:* The canary fails on "epoch-10 train loss below epoch-1 train loss" (l. 1467). The
  pre-approved changes trigger on "per-epoch overhead > 50 % of s_e" (l. 1480), and the trace
  rule reads `ebops_trace_seconds` and `ebops_trace_over_epoch` (l. 1322-1324).
- *Evidence:* RUN.md l. 164-180 and 203-208 show that neither the train loss nor the trace
  fields reach the per-arm log. `ablation.py:783` prints neither, and they go to W&B only
  (`:754-755`). The canary as recorded therefore did not evaluate the loss check or the
  train-step / overhead split.
- *Why it matters:* The stability gate is what licenses 7,000 epochs at LR 3e-3 on binary
  weights. The trace share decides whether the 17.8 d is trace-dominated, which in turn
  decides which [D15] option is sensible.
- *What settles it:* The STUDY names the W&B history as the source for both checks. It states
  that a check that cannot be evaluated counts as a canary fail, not a pass, and the canary is
  re-read from W&B before any production decision.

**B3. Confound 9's "same GPU at seed s" does not survive the K=3 split.**
- *Attack:* Confound 9 (l. 722-724) and Pods (l. 1336-1340) say every Chang-schedule arm at
  seed s runs on one GPU. Under the K=3 fallback, now the likely production packing (A, B, D |
  C, F, A07-350; l. 1341-1342, 2159), A − F crosses pods and possibly GPU class. So do any
  pilot-resumed seeds: A-s1, A-s2 and D-s1 ran at K=6 on an A10, while seeds 3-8 may run at
  K=3 on another class.
- *Evidence:* The pairing itself survives. TF32 is off and the data order is seeded, so a run
  has no numerical dependence on its co-residents, and every paired table carries a GPU-class
  column. The sentence as written is false under the branch the STUDY now expects.
- *What settles it:* Amend confound 9 for the K=3 branch. Either require the two half-blocks of
  seed s to share a GPU class, or state that A − F may cross class and is covered by the
  column. State that the reason pilot checkpoints may resume into production at a different K
  is TF32 off plus seeded order, not co-residency.

### (C) suggestions

- **C1. The budget claim is close to a PID-landing check.** Threshold (c) is about 0.21 top-1,
  so a 25 % tagger passes. The STUDY says so (l. 939-944) and prints per-seed validation
  accuracy beside k. That is honest. Consider also printing the count of feasible seeds whose
  selected checkpoint carries the Deep-Set-class label directly in the budget-claim sentence,
  since that is the physically informative failure at 350k.
- **C2. Collapse cut at 0.99 · log 64.** This corresponds to an effective support of about 61
  of 64 slots, which is strict. A partially collapsed head at 0.95-0.98 is unlabelled. The
  label is descriptive and the raw entropy is printed, so this is fine. The per-head entropy
  distribution in the attention figure would show the near-collapse region.
- **C3. Holm grouping of A − FP32-E with A − NB.** In the likely case, the package gap is
  large and A − FP32-E has the smallest p and passes at α/3, so A − NB is then tested at α/2,
  the same as in a two-member family. The power cost falls only when A − FP32-E fails. The STUDY states the direction and fixes it before any number. No
  change needed. Note in REPORT that the family mixes a package with the one-knob thesis gap.
- **C4. Scope relative to the thesis.** Of 80 runs, only A − NB (iso-EBOPs, not iso-cost) and
  A − FP32-E (a package) bear on the thesis. Neither bears on the DSP claim ([L7]; the
  comparands are already DSP 0 in Table 1) or on the A8 → A6 → A4 axis. The STUDY says this
  plainly (l. 341-380). Keep that paragraph verbatim into REPORT.

## Stripped of framing

If it executes as written, the design produces:
- a correct seed-mean held-out accuracy with an honest t-interval;
- paired gaps with stated resolving power: about ±2.6 pt half-width at the archived spread,
  and a 5.2 pt 80 %-power gap for A − NB at zero correlation;
- survivor-bias labelling;
- the expected outcome of "not falsified at this resolution" for the thesis-bearing gap,
  stated in advance.

Nothing is tautological that is not labelled as such (feasibility at target, certification
as determinism). The open problem is not the statistics. The measured canary says the design
as written (7,000 epochs, K=6, 14 d) will not run as specified, and the text has not caught up.

**Verdict:** I approve the science of the design for launch once B1 is folded in. The single
deciding item is recording that the canary's 17.8 d has fired [D15], and what Kai's answer
(terminal epoch or packing) does to the question's 7,000-epoch premise.
