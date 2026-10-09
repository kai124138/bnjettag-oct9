# STUDY constructive review, v1

Campaign: `campaigns/2026-09-26-training-batch/`. Artifact: `STUDY.md` (483 lines, prose_lint score 0).
Reviewer: constructive-reviewer, 2026-09-26. Read: `docs/methodology/06-review.md`, `03-phases.md`
(Phase 1), `docs/conventions/{jet-tagging-metrics,quantization-and-cost}.md`, `plan.md`,
`review/STUDY_validators_v1.txt`, experiment-log entries 2026-09-26 back to 2026-09-21,
research-log 2026-08-04 and 2026-08-01 entries on arXiv:2510.24784,
`_attic/repro-chang/repro-chang/comparison.md`, and the screen code bundle
`campaigns/2026-09-22-constituent-screen/study-code.tar.gz` (extracted read-only to the session
scratchpad; paths below are relative to its `code/` directory).

## What is done well (keep)

- [+] **Selection rule is pre-registered in full** (STUDY.md 134-159): the feasibility test (<=, with
  Chang's `< 5e5` explicitly not used), the tie-break, "no feasible checkpoint" handling that forbids
  the `model_min_ebops.keras` fallback, the k >= 6 of 8 claim threshold, and divergence as a
  recorded outcome that is never relaunched. This closes the two historical pitfalls in
  `quantization-and-cost.md` (silent unconstrained fallback; final-epoch cost).
- [+] **Held-out touched once, interim readouts validation-only and non-gating** (152-158, [D13]).
- [+] **Reference table refuses the wrong comparands** (36-41): Round 14 is named and excluded, and
  REPRO-CHANG is labelled single-seed, unverified, and test-selected (circular), context only.
- [+] **Static EBOPs floor gate [A7]** before GPU time, with the E07 precedent; the falsifier
  (169-170) turns a static floor >= 350k into a pre-GPU answer.
- [+] **Failed-arm isolation [A12]** correctly spots that the pack runner's exit-1 plus
  `backoffLimit 0` would convert one divergence into six killed runs and an unrecorded retry.
- [+] **Resume ghost-trajectory rollback [A5]** and the W&B artifact cadence fix (265-267).
- [+] **Seed-block pods** (212-215): a lost pod costs one seed of every arm, and same-seed paired
  comparisons share a GPU type.
- [+] **Resolving-power arithmetic with limiting cases** (124-132): 0.836 * sd, the sd = 0 check, and
  the explicit statement that if the epoch-500 validation sd exceeds 0.6 pt the design cannot
  resolve the 1.0-pt tolerance.
- [+] **A -> D -> R ladder** (89-90) decomposes the recipe honestly and labels the packages ([L5]).
- [+] **Cheap version offered with its cost and its loss** (273-280); the 1/21 figure was
  recomputed (plan.md line 66).
- [+] **Attention-alive diagnostic** as a required companion to every accuracy number (185-189).
  The idea is right; the definition needs one fix (B3).

## Category A

### A1. "A miss measures what binary costs at that budget" is not supported by this design

- **Current state.** STUDY.md 26-31: "A miss measures what binary costs at that budget, with one
  caveat: EBOPs leave out the accumulator". The primary test is one-sample: our 8-seed mean against
  one published model (79.4 %), trained in JAX with TF32 on, standardized on train+val, with an
  unstated selection rule and split ([L1], [L3]).
- **Evidence that the gap between pipelines is larger than the tolerance.** Our own run of the
  released code (`_attic/repro-chang/repro-chang/comparison.md`, table rows xfm-n64 and xfmt-n64)
  gave 80.56 % (xfm-n64, 348k) against the paper's 77.9 % MHA-64, a +2.7 pt difference, and
  80.85 % against the paper's 79.8 % Linformer-64, +1.05 pt. Both are single seed and test-selected,
  so they are not results; but they show that the implementation, head count and selection differences
  alone move the N=64 number by 1 to 3 points, which is equal to or larger than the 1.0-pt tolerance.
- **Dominant uncertainty.** With 8 seeds our mean is bounded to +-0.84 * sd. The reference's own
  uncertainty (single model, unknown seed noise, unknown selection, a demonstrated 1-3 pt
  code-vs-paper spread) is the dominant term, and more seeds on our side do not reduce it. Only a
  matched reference arm does. A referee would write exactly this sentence.
- **Improved state (three options, in increasing strength).**
  (c, required minimum, low) Rewrite 26-31 and the falsifier outcomes so that a miss or hit is read
  as "binary N=64 in our pipeline against a published single-model number", not as the cost of
  binary. Add the REPRO-CHANG spread to [L1] as the reason.
  (a, medium to high) Add a reference arm H: Chang's released `jsc150` xfm-n64 (HGQ weights, not
  binary), 8 seeds, on this campaign's gated 90/10 split, selected by the same pre-registered
  validation-accuracy rule, evaluated once on ROC-test. The code already ran on NRP (REPRO-CHANG);
  its per-epoch time is not recorded in the comparison note, so it needs the canary too. Then
  A - H is the cost of binary plus our architecture at matched split, gate, selection and budget,
  with a Welch interval.
  (b, high) An in-house learned-width-weight arm on A07. Not available today: the qat builder
  accepts only `binary_absmean`, `int8_absmax` and `none` (`bnhgq2/qat.py` 333-336, 356; the
  `kbi_learnable` mode exists only in the Keras path, `bnhgq2/train.py` 559). New code.
- **Why A.** §6.3 question 3 ("what would a competing group have that we do not?") has a non-empty
  answer, a matched non-binary arm, and the thesis sentence currently claims what only that arm could
  measure. Option (c) resolves the A; options (a)/(b) are the stronger design and should at least
  be put to Kai in "Where I am not sure".
- **Effort.** (c) low; (a) medium engineering plus compute of order one more arm; (b) high.

## Category B

### B1. The tie-break stated in STUDY is not the one the inherited config will run

- **Current state.** STUDY.md 138-141 states the tie-break as accuracy -> validation macro AUC ->
  lower EBOPs -> earlier epoch, "exactly as `checkpoint_selection_key`". Configs are "copied field for
  field" from `configs/const0922-a07-n64-s1-fast50-fp32.json` (STUDY 59-60), which carries an
  `engram_study` block (config line 102, `module: null`). The runner sets
  `cost_first = bool(cfg.get('engram_study'))` (`bnhgq2/ablation.py` 421) and passes it as
  `cost_before_auc` (422), which reorders the key to accuracy -> lower EBOPs -> validation AUC ->
  earlier epoch (`ablation.py` 278-287). A non-empty dict is truthy, so `cost_first` is True for
  these configs.
- **Why it matters.** Validation accuracy on n_val = 62,000 is quantized at 1/62,000; over up to
  7,000 candidate epochs per run, exact accuracy ties near the maximum are plausible, so the
  tie-break can change which checkpoint is evaluated on ROC-test. The pre-registered rule and the
  implemented rule would differ.
- **Improved state.** STUDY says the generator drops the `engram_study` and `constituent_study`
  blocks (or sets the flag explicitly), and adds to [A1] a unit test asserting the selection key
  order on a constructed accuracy tie. Alternatively, keep the code and restate the rule; either is
  fine, but it must be one rule.
- **Effort.** Low.

### B2. Comparand and tolerance: pre-register the conditional choice

- **Current state.** The bar is 79.4 % (Deep Sets, the lowest of the paper's live N=64 rows:
  Linformer 79.8, MLP Mixer 79.7) minus 1.0 pt = 78.4 %. "Where I am not sure" rates this LOW
  confidence (442-446). The justification for Deep Sets is attention collapse (185-189), which is
  itself an outcome of this campaign.
- **Improved state.** Pre-register the comparand as conditional on the attention diagnostic,
  decided before ROC-test is read: attention alive at the selected checkpoint in >= 6/8 A seeds ->
  Linformer 79.8 % (bar 78.8 %); collapsed -> Deep Sets 79.4 % (bar 78.4 %). Report the other bar
  beside it. Otherwise the reader sees the easiest of three published rows chosen and then relaxed
  by a point.
- **Why.** Honest framing: the choice must not look like it was picked to be passable, and it must
  not be made after seeing A.
- **Effort.** Low.

### B3. "Attention alive" conflates two different failure modes

- **Current state.** 185-189 define attention alive as the fraction of Q, K and V channels at
  0 bits, and 474-477 call V-pruning to 0 bits "the attention-collapse route".
- **Problem.** Q or K channels at 0 bits give constant logits, a uniform softmax, and a mean pool
  of V: that is the Deep-Set collapse Sun et al. describe (§3). V at 0 bits removes the attention
  branch entirely (only the residual path is left), which is a different model, not a Deep Set.
  Summing the three hides which one happened, and the comparand logic (B2) depends on it.
- **Improved state.** Report Q/K 0-bit fraction and V 0-bit fraction separately, and add the mean
  attention entropy over validation jets at the selected checkpoint, as a fraction of log(64)
  (entropy near log 64 = uniform = Deep Set). Fix the wording at 474-477. Validation jets only.
- **Effort.** Low (one forward pass with the softmax tap on the selected checkpoint).

### B4. Epoch-matched A vs R is recoverable almost for free

- **Current state.** A - R and D - R compare 7,000 Chang-schedule epochs with 1,000 of ours and are
  labelled packages ([L5], confound 11). [A6] already saves a best-feasible-as-of-E snapshot at
  every 500-epoch boundary, including E = 1,000.
- **Improved state.** Pre-register a second held-out evaluation for A and D on the as-of-1,000
  snapshot (selected by the same validation rule, restricted to epochs <= 1,000). Then A1000 - R
  and D1000 - R separate "more epochs" from "the schedule and batch" at matched epoch count.
  State that ROC-test is then touched twice for A and D, both evaluations pre-registered, neither
  used to select anything; this is not circular.
- **Why.** The secondary question ("does the recipe beat ours") is otherwise dominated by a 7x
  epoch difference that everyone will suspect. The information is already on disk.
- **Effort.** Low (one extra evaluation per run at VERIFY).

### B5. Disputed fact for the investigator: has any binary N=64 run ever reached 350k?

- **Question.** Did any N=64 arm of the 2026-09-22 screen (target 350k, 50 epochs) reach a
  feasible checkpoint, and how fast did EBOPs fall? Why did the 2026-09-24 N=64 confirmation runs
  move to 5M (log 2026-09-24: "N8 target 350k eBOPs, N64 target 5M", no reason given)?
- **What I checked.** `campaigns/2026-09-22-constituent-screen/screen-pod-logs.txt` (207 lines)
  contains no `[epoch ...] EBOPs=` lines; `live-status.json` is a launch snapshot (STUDY 478-481 says
  the same). No local file answers it.
- **What would settle it.** `activation_widths.jsonl` (per-epoch `ebops`, `budget_met`) under PVC
  `/data/constituent-study-20260922/fp32/`, or W&B group `constituent-20260922-fast50`; and the
  EBOPs trajectories of the in-flight A07-N64 5M confirmation runs
  (`campaigns/2026-09-23-confirmation/configs-n64/confirm0924-a07-n64-s{2,3}-e1000-5m.json`).
- **Why B.** It decides whether A, D, E, F and R are feasible at all, and whether B (175k) is a
  budget ladder or a guaranteed "no feasible checkpoint". It should be answered before the canary,
  not after 7,000 epochs. [A7] gives the static floor; this gives the dynamic evidence.
- **Effort.** Low for the investigator (read-only PVC or W&B query).

### B6. Per-epoch overhead: say which parts may move

- **Current state.** [D14] says "resume checkpoint every 25 epochs". The runner writes a full
  checkpoint every epoch unconditionally (`ablation.py` 456 calls `save_checkpoint`, 190-213, with
  no cadence test), and each epoch also saves the candidate, reloads it, traces `compute_ebops`
  twice, and predicts 62,000 jets (`ablation.py` 392-403). At batch 2,790 (200 steps/epoch) this
  fixed cost may dominate s_e, and it is multiplied by 7,000.
- **Improved state.** STUDY states: the candidate save/reload/validate is a correctness gate and
  stays every epoch (it is what makes the selected file the evaluated one); the full
  optimizer checkpoint moves to every 25 epochs as a code change under [A1]-style testing, which is
  what makes [A5] necessary. The canary already splits train-step from overhead (196, 230); add a
  pre-registered rule for what happens if overhead > 50 % of s_e (for example, pre-approved code
  changes that do not touch selection).
- **Why.** The launch policy [D15] hinges on s_e; the design should not discover after the canary
  that the only lever is truncating epochs.
- **Effort.** Low to write; medium to implement.

## Category C

### C1. One fidelity table for "the Sun et al. recipe"

Current: deltas are scattered over [D3], [D5], [D7], [L2], [L3], [D18]. Research-log 2026-08-04
lists further ones not in STUDY: initial widths `bw_k = bw_a = 7` (ours: 8-bit init),
`beta0 = 0` (ours 1e-7), per-position ("value-wise") activation widths
(`homogeneous_axis=(0,)`; ours per-channel), open-loop beta (ours PID, justified in [D5]), input
quantizer `MinMax(0,12)`. Improved: one table, field / Chang code / paper / ours / matched?, so
"verbatim" is precise. Effort low.

### C2. Selection-metric sensitivity

Every epoch record carries `val_macro_auc`, `val_categorical_accuracy` and `ebops`
(`ablation.py` 424-441, logged to `activation_widths.jsonl`). Pre-register reporting the
validation-AUC-selected feasible checkpoint as a labelled sensitivity beside the primary (it is the
house rule, `quantization-and-cost.md` "Selection under a budget"), since the two metrics rank
models differently (constituent study 2026-09-16, cited at 448-451). Requires keeping that
checkpoint; the runner's `model_unconstrained.keras` is AUC-best but not feasibility-filtered, so a
second feasible-AUC-best copy is needed. Effort low.

### C3. Strip stale inherited fields

The source config carries `validation_split: 0.2` (line 39), `wandb_project:
BNJetTag-Engram-Experimental` (52), `order_seed: 20260912` (84), and a `constituent_study` block
(114) describing the 50-epoch protocol with `test_set_used: false`. STUDY overrides split, project
and order seed; state that the generator rewrites or drops every one of these, and have PREFLIGHT
diff one generated config against the source. Effort low.

### C4. Memory prior for the K=6 canary

The only recorded memory figure for A07-class N=64 is three processes at 3,849 / 23,028 MiB on one
A10 at batch 256 (experiment-log 2026-09-24). Cite it in the canary section as the prior, and note
that batch 2,790 with 64x64 attention per head raises activation memory roughly 11x per step, so
the K=3 fallback is not unlikely. Effort low.

### C5. Validation noise at n_val = 62,000

Binomial SE on accuracy near 0.8 is about sqrt(0.16/62,000) = 0.16 pt per checkpoint; max-over-7,000
selection on it adds optimism on validation (not on ROC-test) and adds selection noise to the
seed spread. The 90/10 choice is flagged (437-440); add this number to it so Kai sees the cost of
fidelity (80/20 gives about 0.11 pt). Effort low.

## Answers to the §6.3 questions

1. Conventions: every applicable row is present; three deviations are flagged with reasons. Yes.
2. Reference table: present and sourced; its rigour gap (single model) is admitted, but see A1.
3. Competing group next month: would have a matched non-binary reference arm in the same pipeline
   (A1), and epoch-matched recipe comparison (B4).
4. Uncertainties: our side honest (0.836 * sd, k/8 stated); the reference side understated in the
   thesis sentence (A1). Resolving power stated conditionally on the epoch-500 sd; good.
5. Limitations with attempts: [L4] (restart peaks) is accepted with a recording plan; fine.
6. Context with a pull: not possible (no record exists), and STUDY says so (295). Fine.
