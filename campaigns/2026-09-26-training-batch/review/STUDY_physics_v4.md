# STUDY physics review v4: 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context; read only the artifact, the files it cites and the
arrays behind its numbers). Artifact: `campaigns/2026-09-26-training-batch/STUDY.md` (1,655 lines,
status `designed`). No compiled PDF exists beside it. Phase STUDY: no results yet, so the checks
below apply to the plan.

## Figures

No figure exists yet, and the artifact embeds or cites none. The pre-registered figures (Falsifier,
"Figures") were checked as a plan:

| pre-registered figure | status |
| --- | --- |
| Per-class ROC on ROC-test, log mistag axis, seed band (sd ddof = 1, seed count, k when k < 8), arms A, R, C, A07-350, caption "ROC-test, n = 260,000" | Plan OK on axis, split, n and band. Puts C (A07 at 5M) beside A and R (E at 350k) on one axis, which invites a comparison across budgets (C3) |
| Accuracy-versus-EBOPs ladders, E (B 250k, A 350k) and A07 (A07-350 350k, C 5M), rungs labelled with EBOPs above the 0-bit floor, paired-gap panel beneath, empty marker for 0/8 | Plan OK. The paired-gap panel is the right way to draw it, and infeasible rungs are drawn rather than dropped |
| Attention state per arm (Q/K and V fraction at 0 bits, entropy / log 64), A07-350 expectation marked | Plan OK |
| Validation − held-out accuracy per run (winner's curse) | Plan OK |
| Interim-readout figures labelled "validation, n = 62,000" | Plan OK |
| Second wave: A − NB paired-gap panel with the 1.0-pt line, H − NB and H − A Welch intervals, GPU class in caption; per-class ROC with A, NB, H; NB weight-width distribution | Plan OK |
| **Missing:** a figure for the primary measurement (per-seed A accuracies, mean with t-interval, lines at 79.4 / 78.4 / 79.8 / 77.9) and a paired-gap panel for the recipe ladder A → D → R (A − D, D − R, A − R, A1000 − R, D1000 − R) | Not planned (B5) |

## What I verified

- **Round-14 sizing spread.** I recomputed it from `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz`
  (keys `y`, `score`, shape (260000, 5)). W1A8 top-1: 67.18 / 72.64 / 67.21 %, mean 69.01, sd 3.145
  (ddof = 1). FP32: 79.42 / 78.83 / 79.10 %, mean 79.11, sd 0.297. n = 260,000. This matches the
  reference table (69.0 ± 3.1, 79.1 ± 0.3).
- **Static floors.** Every floor matches `code/evidence/static_floors_fix6_a07_e_e1.json`
  (CPU, synthetic sample, not a result). A07 0-bit / 1-bit-alive / narrow / full: 343,053 /
  1,005,741 / 605,197 / 801,805. E: 171,526 / 619,198 / 368,134 / 478,726. E1: 85,763 / 533,435 /
  282,371 / 392,963. The headroom arithmetic is correct (350,000 − 171,526 = 178,474; − 343,053 = 6,947;
  − 85,763 = 264,237; 250,000 − 171,526 = 78,474).
- **Minimal attention path.** The per-channel costs derived from the `one` entries of that JSON give:
  A07 input_proj 6,144 / 3 = 2,048 per input channel, Wk 65,536 / 32 = 2,048, scores
  131,072 / (4 × 8) = 4,096 per (head, key-channel) pair; E 4,608 / 3 = 1,536, 36,864 / 24 = 1,536,
  98,304 / 24 = 4,096. The path input_proj + Wk input + one Q·K pair (Q nonzero through its bias)
  costs 8,192 in A07 and 7,168 in E, as stated. The conclusion that A07-350 cannot carry
  data-dependent attention holds (C4 is about the wording).
- **Interval arithmetic.** 2.365/√8 = 0.836; 0.836 · √2 · 3.14 = 3.71 pt; t(0.975,5)/√6 = 1.05;
  t(0.975,14) · 0.5 = 1.07 (3.4 pt at 3.14); 1.0/0.836 = 1.20 pt; 0.5/0.836 = 0.60 pt; binomial SE at
  p = 0.79, n = 62,000 = 0.16 pt; cheap version t(0.975,3)/2 = 1.59. McNemar two-sided 4-0 to 7-0:
  0.125 / 0.0625 / 0.031 / 0.016. Timing: 7,000 × 112.6 s = 9.1 d; 172.8 s ↔ 14 d; 1.66 × 112.6 =
  187 s → 15.1 d. The Sun et al. per-class AUC means (0.9532 Linformer, 0.9428 MHA) follow from the quoted legend values.
  All correct.

## Findings

### (A) Must resolve

None. The plan keeps selection (validation, n = 62,000) and evaluation (ROC-test, n = 260,000)
apart, states sd as ddof = 1 over seeds, pairs by seed with a t-interval and a sign count, keeps
per-class AUCs beside the headline, and labels the 79.4 % distance as descriptive with the
reference's own uncertainty ([L1]). No projection is presented as a result: floors and timings are
labelled CPU, synthetic, not results.

### (B) Should address

**B1. A cost is attributed to binary weights that has nothing to do with them, and the sentence is
pre-registered into the REPORT text.** "Binary weights reach 350k at N=64 here only because
attention may prune to 0 bits, which the paper's protocol may not have allowed" appears in the
Primary measurement (as something the report *must* state), in "Paper's ≥ 1-bit attention rule"
and in [L2]. The narrow-reading floor for E is softmax 171,526 + scores 98,304 + ctx 98,304 =
368,134 (JSON above). All three are activation × activation terms with no weight factor. The same
floor therefore binds NB (learned-width weights, [D22]) and any 2-head E-sized model, whatever its
weight type. Chang's `xfm` at key_dim 16 pays scores 2 · 16 · 4,096 = 131,072 at 1 bit, which is
even more. Written this way, a reader of the REPORT would take away a binary-specific caveat that
is really a caveat about the 2-head architecture under [D19]. *Settle:* reword it as "the 2-head
E architecture under [D19] (any weight type, including NB and Sun et al.'s `xfm`) reaches 350k only
because the Q·K and A·V streams may prune to 0 bits". The A − NB comparison is unaffected, because
both arms share this floor.

**B2. The budget claim is close to empty by construction.** Condition (a) is what the PID drives
toward. Condition (b) passes for any positive number of EBOPs above the floor. Condition (c) is
p_maj + 5 · SE, and on a five-class set that is roughly balanced this is about 0.2 + 0.008. One
live 1-bit input channel will clear it. A seed at 30 % top-1 accuracy "supports" the claim that
the binary tagger "reaches the budget non-degenerately". The artifact admits (Selection rule,
"Feasibility is the cost outcome") that the EBOPs side holds by construction. The accuracy side of
"non-degenerate" is also almost automatic. *Attack:* at REPORT, "budget claim supported, 8/8" will
read as a success about the tagger when it only shows that the network is not constant. *Settle:*
do one of the following before PREFLIGHT. Either demote the budget claim to a reported count with
no pass/fail wording, or pre-register an accuracy floor that means something physically (for
example, a stated fraction of the R or A07-350 validation accuracy, or a fixed level justified now).
Do not tune that floor after any pilot number exists.

**B3. The feasibility signal and the PID control signal can differ, and no rule covers that
case.** [D20] leaves to PREFLIGHT whether BetaPID reads the traced full-split EBOPs or the
in-training `FreeEBOPs`; if the latter, the plan only logs the ratio. A reset trace over all
558,000 training jets sets each WRAP `i` to the global range, and that range is at least any
per-batch or decayed range. The expected direction is therefore traced ≥ in-training. If the PID
holds `FreeEBOPs` at 350,000, the traced EBOPs sits above the target at equilibrium, and (a) is met
only on downward excursions. The feasible checkpoints are then a subset of epochs chosen by those
dips, the max-validation-accuracy selection runs over that subset, and the budget and recipe
branches (R reaching 350k in 1,000 epochs) turn on a controller offset instead of on the recipe.
The epoch-500 pilot would catch a total failure but not the bias. *Settle:* pre-register now that
the PID reads the same traced quantity the feasibility test uses. If that is too expensive,
pre-register the fixed rule (for example, a target offset computed from the canary ratio before the
pilot starts). Record the ratio at the canary. This is the item that most decides whether the
design yields an unbiased feasible checkpoint.

**B4. The one comparison that bears on the thesis (A − NB) cannot measure a "modest" cost, and no
remedy is pre-registered.** The thesis promises a "modest, measurable cost". At zero pair
correlation and the archived spread, the paired resolution is about 3.7 pt (Seeds). The weight-type
claim has no pass condition, only "not falsified at this resolution", so the default outcome of an
underpowered run is the wording most easily read as support for the thesis. The epoch-500 sd gate
([D13]) covers only arm A's sd. The second wave has no pilot and no readout rule on sd_diff.
*Settle:* pre-register a second-wave epoch-500 readout of the paired A − NB validation sd_diff,
with the same Kai options as [D13] (including add seeds), triggered at sd_diff > 1.2 pt (the value
that gives a ±1.0-pt half-width at 8 pairs, already stated in Seeds). Also state in the Falsifier
the smallest A − NB this design can resolve at the measured sd_diff, so that REPORT prints it beside
the interval.

**B5. The primary measurement has no figure.** The only quantity the Question asks for (A's
seed-mean ROC-test accuracy and A − 79.4 with its interval) gets no pre-registered figure. Neither
does the recipe ladder A → D → R with its epoch-matched gaps. *Settle:* add (i) per-seed A
accuracies with the mean and 95 % t-interval (k in the legend), with horizontal lines at 79.4
(comparand), 78.4 (descriptive line), 79.8 and 77.9, and caption "ROC-test, n = 260,000, external
references single-model"; (ii) a paired-gap panel for A − D, D − R, A − R, A1000 − R and D1000 − R
with n_pairs and the GPU-class note.

### (C) Suggestions

**C1. An identity is described as a confirmation.** "The arbiter's sums of traced per-layer terms
for A07 and E ... are confirmed exactly". A sum of per-layer terms taken from a trace reproduces
that trace's total by construction, so it confirms nothing. The only independent prediction that
held is the E1 per-head projection (softmax 171,526 / 2 = 85,763, scores and ctx unchanged, as the
JSON shows). Say that, and drop "confirmed" for the A07 and E sums.

**C2. The stability claim counts only NaN divergence.** The Round-14 binary N=64 instability that
motivates it shows up as low-accuracy seeds (67.18 / 72.64 / 67.21 %, recomputed above), not as
non-finite losses. A collapsed run that stays finite counts as "not diverged". Report the
feasible-degenerate counts and a pre-registered low-accuracy-outlier count beside the divergence
count, so that "not falsified" in the A-versus-D stability claim does not hide collapsed runs.

**C3. The ROC figure mixes budgets.** C (A07, 5M) is drawn beside A and R (E, 350k). Either move C
to its own panel with its EBOPs above the floor in the legend, or leave it out of the primary ROC.

**C4. The A07 minimal-path wording.** "At 1 bit one input channel of `input_proj` or of any d32
dense layer costs 2,048 ... one Q·K pair costs 4,096 ... at least one of each, 8,192". Read
literally, "one of each" of those two items is 6,144, which is below 6,947 and reverses the
conclusion. The 8,192 figure is right only as input_proj channel + Wk input channel + Q·K pair,
which is how the E sentence spells it out (1,536 + 1,536 + 4,096). Write the A07 sentence the same
way.

**C5. Neither thesis axis is addressed directly.** The design has no FP32 or W8A8 baseline and no
A8 → A6 → A4 ladder. Activations are learned-width under WRAP, and NB is learned-width, not full
precision. [L10] and "Bearing on the thesis" are honest about this. A one-line scope statement
("this campaign does not measure the cost against FP32 or 8-bit, nor the activation ladder") would
keep the REPORT from being quoted against the thesis's two axes.

**C6. WRAP overflow on ROC-test has no threshold.** The overflow fraction is reported ([L8]),
which is good, and the ROC-test accuracy already includes the wrap effect. However, a non-negligible
ROC-test overflow means the EBOPs traced on training data understates the width the deployed model
needs. Pre-register a threshold above which the EBOPs of that checkpoint is labelled "train-range
EBOPs; deployment range wider".

**C7. The binary scale factor.** `binary_absmean` carries a per-layer (or per-channel) scale. State
whether native HGQ2 EBOPs counts it (folded or not), so that iso-EBOPs between A and NB does not
hide a multiply on the binary side.

## Resolving power, stated once

At the archived N=64 binary sd (3.145 pt, 3 seeds, recomputed), 8 seeds give a ±2.63-pt half-width
on the A mean and about ±3.7 pt on a paired gap at zero pair correlation. At the N=8 lower bound
(0.19 pt) they give ±0.16 pt. The design says so and routes the case to Kai at an epoch-500 sd of
0.6 pt for A. B4 asks for the same treatment of A − NB.

## Suspiciously good agreement

Nothing here is a result yet. The two exact agreements in the artifact are C1, an identity called
a confirmation, and E1 × 2 = E, a genuine prediction that is expected because the softmax term is
per head. I also asked what the certification retrace (≤ 1e-6) could miss. It reruns the same trace
on the same data, so it tests the reload path and not the EBOPs formula. The formula check is
[A14] (against HGQ2's own counter on a REPRO-CHANG checkpoint), and it should stay a gate.

## Verdict

I would approve this STUDY for PREFLIGHT once B1-B5 land in the text. B3, which fixes the PID
signal to the traced feasibility quantity before any GPU time, is the item that most decides the
call, because it determines whether the feasible checkpoints are an unbiased sample.
