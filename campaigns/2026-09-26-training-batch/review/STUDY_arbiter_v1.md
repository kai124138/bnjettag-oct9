# STUDY arbiter v1: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-26. Artifact `STUDY.md` (483 lines) and `plan.md`. Reviews:
`review/STUDY_physics_v1.md`, `review/STUDY_critical_v1.md`, `review/STUDY_constructive_v1.md`.
Validators: `review/STUDY_validators_v1.txt` (no mechanical STUDY validator; `prose_lint` score 0,
no A lines). No plot-validator file (STUDY has no figures). No earlier arbiter file (n = 1).
Read: `docs/methodology/06-review.md` §6.1-6.8, `docs/conventions/jet-tagging-metrics.md`,
`docs/conventions/quantization-and-cost.md`.

## Independent checks made by the arbiter

- **Tie-break (facts behind crit A2 / cons B1).** Screen bundle
  `campaigns/2026-09-22-constituent-screen/study-code.tar.gz`, sha256 `26f3cc40...5a45`
  (recomputed), extracted read-only to the session scratchpad. `bnhgq2/ablation.py:278-287`: with
  `cost_before_auc=True` the key is (accuracy, −EBOPs, val AUC, −epoch). `:421`
  `cost_first = bool(cfg.get('engram_study'))`, `:422` passes it. `const0922-a07-n64-s1-fast50-fp32.json`
  has `engram_study = {'module': None, ...}` (non-empty, truthy). Both reviewers are right.
- **Same-N binary spread (crit A1).** Recomputed from `bnjettag/roc-results/r14/n64/*-s{1,2,3}.npz`
  (y shape (260000, 5)), held-out top-1 accuracy, ddof = 1, archived Round 14:
  W1A8 0.6718 / 0.7264 / 0.6721, mean 0.6901, sd 0.0314; W1A6 0.6984 ± 0.0168;
  FP32 0.7911 ± 0.0030; W8A8 0.7752 ± 0.0035. Matches the critical reviewer.
- **Initialization pairing (crit C4).** `ablation.py:61-78` `matching_initialization` copies every
  equal-shape `kernel`, `bias` and `pos_table` by variable path from a reference built at the same
  seed. Removing PE (arm F) removes `pos_table` only; every other A07 kernel has the same path and
  shape, so A-s{s} and F-s{s} very probably share init, and they share data order by [D9].
- **Checkpoint cadence (cons B6).** `ablation.py:190-213` `save_checkpoint` has no cadence test and
  is called every epoch (`:456`); the epoch also runs `compute_ebops` twice and a 62,000-jet
  predict (`:392-403`). [D14] "every 25 epochs" is therefore a code change, not a setting.
- **[D1] rationale (crit B5).** `campaigns/2026-09-23-confirmation/n64-full-preflight-result.json`
  traces three configs only: a07 (24,816,782), e02 (24,888,462), e05 (25,023,758). A07 is the only
  plain transformer traced, so "lowest of the plain N=64 arms traced" is vacuous.
- **"5M without a recorded reason" (crit B4, second part).** `.claude/memory/experiment-log.md`
  2026-09-24 records "N64 target5M" and `project-context.md` records N64 5M enforced from
  2026-09-10; neither gives a reason. The sentence is half right: the target is recorded, the
  reason is not. Wording fix only.
- **N=64 at 350k, local evidence.** `screen-pod-logs.txt` has no per-epoch EBOPs lines;
  `campaigns/2026-09-23-confirmation/active-checkpoints-0924.json` holds N=8 runs only. Nothing
  local settles it (see Disputed facts).

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | No arm varies the weight type; "Bearing on the thesis" (l. 26-31) claims a hit means binary "survives an iso-cost comparison" and a miss "measures what binary costs". Neither follows from a one-sample test against one external HGQ Deep Sets number that differs in family, head, backend, standardization, selection. "Iso-cost" contradicts [L2]. | phys A1, crit A3(b), cons A1 | A, A, A | **A** | Case 1. Minimum fix is a rewording (below); a matched non-binary arm is the stronger design and goes to Kai. |
| 2 | Competing-group answer non-empty and unjustified: a seeded, validation-selected run of Sun et al.'s own code on the same gated split and ROC-test (arm H). REPRO-CHANG shows the code runs on NRP. | crit A3(a), cons A1 option (a) | A, (option) | **A** | §6.3: a non-empty Q3 answer without justification is A. Resolved by either adding H or stating why it is omitted (Kai's request was binary trainings; one more 7,000-epoch arm; new pipeline in JAX) and pre-registering it as a follow-up and a Kai decision. |
| 3 | Resolving power sized from the N=8 sd (0.19 pt) although the design forbids cross-N; the same-N archived binary sd is 3.14 pt (recomputed), giving an 8-seed half-width of 2.63 pt against a 1.0-pt tolerance; the epoch-500 sd check has no consequence because [D13] says readouts never gate. | crit A1; phys C2, C7 | A; C, C | **A** | Case 3, recomputed by the arbiter. §6.3 Q4 "no resolving power" without a consequence is A. Physics C2 (k = 6 gives 1.05·sd) and C7 fold in. |
| 4 | Pre-registered tie-break (acc → val AUC → −EBOPs → −epoch "exactly as `checkpoint_selection_key`") is not what a field-for-field copy runs (acc → −EBOPs → val AUC → −epoch). | crit A2, cons B1 | A, B | **A** | Case 2. Sided with A: the pre-registered selection rule states a code fact that is false, and left as is it becomes the §6.7 trigger "selection rule changed" at VERIFY. The fix is minutes. |
| 5 | Reference uncertainty is at the scale of the tolerance: REPRO-CHANG moved the paper's N=64 rows by +1.05 (Linformer) and +2.7 (MHA) pt; the paper's selection rule is unstated and possibly best-of-several; the gate may not apply to the paper's number. A pass/fail at 78.4 treats 79.4 as exact. | phys B1, cons A1 | B, (in A) | **B** | Case 1. Fix: quantify [L1] with those deltas (labelled single seed, test-selected) and report the primary as a distance with its interval; the 78.4 bar may stay only as a labelled pre-registered descriptive line. |
| 6 | Comparand chosen as the lowest live N=64 row, then conditioned on a post-hoc attention diagnostic (l. 185-189); invites re-choosing the bar after results. | crit B2, cons B2, phys C8 | B, B, C | **B** | Case 2 on direction. Sided with the critical reviewer: fix 79.4 unconditionally now with a stated reason, and report the distance to 79.8 (Linformer) and 77.9 (MHA) beside it. A conditional rule rests on a diagnostic whose definition is itself contested (#7). |
| 7 | "Attention alive" (0-bit fraction of Q, K, V pooled) conflates Q/K collapse (uniform softmax, Deep Set) with V pruning (branch removed), and cannot detect the paper's ≥1-bit collapse. | cons B3, crit B2 | B, B | **B** | Case 1. Report Q/K and V 0-bit fractions separately plus mean attention entropy over validation jets as a fraction of log 64; fix wording at l. 474-477. |
| 8 | Survivorship, pairing, divergence and the stability falsifier under-specified: feasible-only means biased upward; paired gaps undefined when one arm's seed is infeasible or diverged; no branch if R never reaches 350k; unclear whether a pre-divergence checkpoint enters the mean; "more A than D diverge" falsifies at 1 vs 0. | phys B3, B4; crit B3 | B, B, B | **B** | Case 1, merged. |
| 9 | "Native HGQ2 EBOPs" equivalence with Sun et al. asserted, not checked; an accounting offset moves the effective budget more than the A-B ladder. | phys B2 | B | **B** | Case 3; no evidence against it. Fix: a pre-registered PREFLIGHT attempt, with a quantified-limitation fallback. |
| 10 | Budget most likely lands in the "do not launch" branch (only measurement 83-245 s/epoch at batch 256; per-epoch overhead does not shrink with batch); 10 pods against Kai's "a couple of pods" left as a flag. | crit B1 | B | **B** | Case 3. The expected [D15] branch must be stated and the pod count put to Kai as a decision at the launch gate. |
| 11 | Per-epoch overhead: full checkpoint every epoch in code, [D14] says every 25; no rule if overhead dominates s_e. | cons B6 | B | **B** | Case 3, confirmed at `ablation.py:190-213, 456`. Needs an [A] constraint. |
| 12 | Epoch-matched A1000 − R and D1000 − R from the [A6] epoch-1,000 snapshot, pre-registered. | cons B4 | B | **B** | Case 3. The secondary question is otherwise dominated by a 7× epoch difference; the snapshot already exists by design. Pre-register the second ROC-test touch. |
| 13 | Only N=64 trajectory at 350k (screen `const0922-a07-n64-s1`) treated as unavailable; should be a PREFLIGHT item. | crit B4, cons B5 | B, B | **B** | Case 1. Disputed fact for the investigator (below). |
| 14 | [D1] rationale vacuous (A07 is the only plain N=64 arm traced); A06-N64 untraced. | crit B5 | B | **B** | Case 3, confirmed from `n64-full-preflight-result.json`. Drop the claim or have [A7] trace A06. |
| 15 | A vs F declared unpaired although init is very probably shared. | crit C4 | C | **B** | Case 5 upgrade. `matching_initialization` copies by path; an unpaired interval where init and order are shared is the inflation case of §6.3 Q4. Fix: pre-register a PREFLIGHT `kernel_hashes` comparison; if only `pos_table` differs, A − F is paired. |
| 16 | §6.8: STUDY names 79.4 as a reference but does not say whether any arm is bound by it at VERIFY. If arm H is added it becomes the binding baseline (REPRO-CHANG sits +2.7 pt over MHA-64, which would trip Tier 1). | arbiter | none | **C** | Case 5. One sentence in the conventions table. |
| 17 | Figures not pre-registered (per-class ROC, log mistag axis, seed band, A-B-C ladder with paired intervals). | phys C1 | C | **C** | Case 3. |
| 18 | Winner's curse on validation (binomial SE about 0.16 pt at n_val 62,000; about 0.11 pt at 80/20); report the validation − held-out gap per run; add the number to the 90/10 flag. | phys C4, cons C5 | C, C | **C** | Case 1. |
| 19 | EBOPs at selection sits at the target by construction; report feasibility count only. | phys C5 | C | **C** | Case 3. |
| 20 | MLP Mixer 79.7 % is quoted from ref. [18]; not stated as trained at 350k. Label it. | phys C6 | C | **C** | Case 3. |
| 21 | Chang width init 7/7 bits vs our 8-bit init; E key_dim 16 vs 12; one fidelity table (field / Chang code / paper / ours / matched). | crit C1, C2; cons C1 | C, C, C | **C** | Case 1. |
| 22 | Holm family: state the three claims (primary, recipe, stability) as a family. | crit C3 | C | **C** | Case 3. |
| 23 | Gate-then-standardize: gated constituents become −shift/scale and enter `gap`; confirm our loader matches, including masks. | phys C3 | C | **C** | Case 3. Add to [A3]. |
| 24 | Validation-AUC-selected feasible checkpoint as a labelled sensitivity (house rule). | cons C2 | C | **C** | Case 3. |
| 25 | Strip stale inherited fields (`validation_split 0.2`, `wandb_project`, `order_seed 20260912`, `constituent_study`); PREFLIGHT diffs one generated config against the source. | cons C3 | C | **C** | Case 3. Pairs with #4. |
| 26 | K=6 memory prior: 3,849 / 23,028 MiB for three A07 N=64 processes at batch 256 (log 2026-09-24); batch 2,790 raises activation memory about 11×. | cons C4 | C | **C** | Case 3. |
| 27 | "Moved to 5M without a recorded reason" overstates: the target is recorded, the reason is not. | crit B4 (part) | B | **C** | Case 4, settled from the log and `project-context.md`: wording only, no effect on design. |

## Regression triggers (§6.7), checked independently

No results exist at STUDY, so every result-based trigger is **not met**:
- selection on held-out / changed after results: not met. The rule is validation-only
  (l. 134-159); #4 prevents a future silent change.
- validation vs ROC-test AUC > 0.01: not met (no numbers).
- single-seed, < 100-epoch or lab-pod headline: not met. REPRO-CHANG is labelled context
  only (l. 40).
- cross-N / input-set / split / schedule comparison as one series: not met. A−R and D−R are
  labelled packages ([L5]); the N=8 sd is used for sizing, not comparison (#3 fixes that).
- gap < seed sd with < 3 seeds: not met (8 seeds).
- reload > 1e-7 or TF32 on: not met (TF32 off committed, confound 9).
- reported EBOPs not remeasured, or final-epoch cost mixed: not met (l. 116-117, 299).
- binary layer with > 2 values: not met (check 1 committed, l. 300).
- DSP / C-sim / C-synth: not applicable, no synthesis ([L7]).
- per-class AUC < 0.7 hidden: not met (per-class AUC committed, l. 294).
- byte-identical arms / different `y`: not met (byte-equal `y` gate committed, l. 294).
- failed validation accepted without remediation, or tautological validation: not met.
- [D] replaced without amendment: not met (first version).
- outward document mismatch: not applicable.

## Disputed facts for the investigator

1. **Did any N=64 arm of the 2026-09-22 screen (target 350,000, 50 epochs) reach a feasible
   checkpoint, and what was each arm's minimum EBOPs and its epoch?** Evidence:
   `activation_widths.jsonl` / `ebops_budget.json` under PVC `/data/constituent-study-20260922/fp32/`,
   or W&B group `constituent-20260922-fast50` (`checkpoint_ebops`, `budget_met`); also the EBOPs
   trajectories of the in-flight A07-N64 5M runs
   (`campaigns/2026-09-23-confirmation/configs-n64/confirm0924-a07-n64-s{2,3}-e1000-5m.json`).
   **Blocks:** not the STUDY re-review (the design already covers both answers through [A7] and the
   "falsified at the budget" branch), and not the start of PREFLIGHT. It **blocks the canary and the
   production launch**: STUDY must list it as a PREFLIGHT gate item beside [A7].
2. Why the N=64 confirmation target is 5M (decision, not a trace; no record found). Non-blocking;
   answer if the same query finds it.

## Dismissals

None.

## Motivated-reasoning check

- Comparand: the lowest live N=64 row, a 1.0-pt allowance below it, and a post-hoc conditional
  re-choice: self-serving as written (#6).
- Resolving power: sized from the favourable cross-N sd while a same-N sd 16× larger exists (#3).
- "Iso-cost" and "binary survives" claimed while [L2] concedes EBOPs omit the accumulator (#1).
- Interval inflation: A vs F unpaired where init is shared (#15).
- A limitation admitted in prose but absent from the uncertainty: the reference's own spread
  ([L1]) (#5).

## What is fixed before PREFLIGHT, and what is a follow-up

Everything in the ITERATE list is rewording or pre-registration in STUDY.md, plus [A]
constraints the ml-engineer implements in PREFLIGHT. No new arm and no new code is required
to PASS. Pre-registered follow-ups (named in STUDY, not run here): arm H (Sun et al.'s code, 8
seeds, same gated split and selection); an in-house non-binary weight arm on A07 (new qat code,
`qat.py:333-336`). Both go to Kai in "Where I am not sure".

## Verdict

**ITERATE** (iteration 1 of the STUDY panel tier). No A validator lines; four A findings and
twelve B findings, all resolvable by the fixer in STUDY.md without upstream work.

Required fixes, in priority order:

1. **(#1, A) Recast the primary question as descriptive.** Rewrite the frontmatter `question`,
   the title, the Question and Bearing paragraphs (l. 6, 14-31) and the Falsifier: "what
   held-out accuracy our binary N=64 pipeline reaches under the Sun et al. recipe at 350k EBOPs,
   and its distance to the published single-model 79.4 % Deep Sets (HGQ) row". Replace "iso-cost"
   with "iso-EBOPs". Remove "binary survives" and "a miss measures what binary costs"; say a
   miss or hit measures the gap between this binary pipeline and their HGQ models at equal
   EBOPs, not the cost of binary weights. Update the experiment-log stub to match.
2. **(#2, A) Competing-group answer.** Add arm H (Sun et al.'s code, 8 seeds, gated 90/10,
   same selection, ROC-test once) to "Where I am not sure" as a FLAG FOR HUMAN decision, with
   the reason it is not in this design (Kai asked for binary trainings; one more 7,000-epoch
   arm; separate JAX pipeline and canary) and name it as a pre-registered follow-up. Name the
   in-house non-binary weight arm too.
3. **(#3, A) Resolving power.** State the half-width at both sd bounds: N=8 sd 0.19 pt → ±0.16
   pt, and archived N=64 binary sd 3.14 pt (held-out accuracy, `roc-results/r14/n64/W1A8-s{1,2,3}`,
   3 seeds, n = 260,000, archived, sizing only, not a comparand) → ±2.63 pt. Add it to the
   reference table as "archived context for sd only", with FP32 79.1 ± 0.3 % beside it. Give the
   k = 6 half-width (1.05·sd; the 0.6-pt ceiling becomes 0.48 pt) and label the epoch-500 sd an
   early estimate that may understate the terminal spread. Amend [D13] with a pre-registered
   consequence: if the epoch-500 validation accuracy sd of arm A exceeds 0.6 pt, report to Kai
   before epoch 1,000 with the options (continue as descriptive, add seeds, stop). The readout
   still never selects a checkpoint or an arm.
4. **(#4, A) Tie-break.** Add an [A] constraint: the config generator drops `engram_study` and
   `constituent_study` (or sets `cost_first` False explicitly), and PREFLIGHT has a unit test that
   asserts the key order acc → val AUC → −EBOPs → −epoch on a constructed accuracy tie. Replace
   "exactly as `checkpoint_selection_key` does" with the explicit order plus that constraint.
5. **(#5, B) Reference uncertainty.** Extend [L1] with the REPRO-CHANG deltas (+1.05 pt
   Linformer, +2.7 pt MHA; single seed, test-selected, unverified), the unstated selection rule
   (possibly best of several models, §3) and the gate question. Report the primary as the
   distance A − 79.4 with its 95 % interval; keep 78.4 only as a labelled pre-registered
   descriptive line, not a pass/fail on the thesis.
6. **(#6, B) Comparand.** Fix 79.4 unconditionally now, with the reason (the paper's attention
   N=64 model collapsed into a Deep Set, so Deep Sets is the published model at this budget and
   input set that attention actually reached). Report the distances to 79.8 and 77.9 beside it
   in every outcome. Delete "Deep Sets is the right comparand if ours collapses" (l. 188).
7. **(#7, B) Attention diagnostic.** Report Q/K 0-bit fraction, V 0-bit fraction, and mean
   attention entropy over validation jets as a fraction of log 64, at the selected checkpoint.
   Fix l. 474-477 (V pruning removes the branch; Q/K collapse gives the Deep Set).
8. **(#8, B) Pairing, infeasibility, divergence, stability.** Pre-register: paired gaps use
   seeds feasible (and not diverged) in both arms, with the count stated; feasibility and
   divergence rates are an outcome of their own, compared with an exact paired test; an
   "R infeasible" branch of the recipe claim; whether a pre-divergence best-feasible checkpoint
   is evaluated on ROC-test and enters the mean (say yes or no, once); a threshold for the
   optimizer-stability falsifier (an exact test on paired divergence outcomes, or a stated
   count difference such as ≥ 4 of 8 against 0). State that the feasible-only mean carries a
   survivor bias.
9. **(#9, B) EBOPs equivalence.** Add an [A] PREFLIGHT item: compute the EBOPs of a REPRO-CHANG
   xfm-n64 checkpoint with our `compute_ebops` and with HGQ2's own, and report the ratio. If our
   tool cannot trace their model, record why and state the accounting difference as a
   quantified limitation.
10. **(#10, B) Budget.** State which [D15] branch is expected from the recorded 83-245 s per
    epoch at batch 256 (log 2026-09-22, `live-status.json`), and present the cheap version and
    the P = 2 waves as the likely alternatives. Move "10 pods versus a couple of pods" into a
    Kai decision at the canary/launch gate: no production pod launches beyond Kai's stated
    footprint without his answer.
11. **(#11, B) Overhead.** Add an [A] constraint that moving the full optimizer checkpoint to
    every 25 epochs is a code change (`ablation.py:190-213, 456`), tested with [A5]. State that
    the candidate save/reload/validate stays every epoch. Pre-register what happens if the canary
    shows overhead above 50 % of s_e (the code changes allowed, none touching selection).
12. **(#12, B) Epoch-matched recipe gap.** Pre-register a second ROC-test evaluation for A and D
    on the as-of-epoch-1,000 best-feasible snapshot ([A6]), giving A1000 − R and D1000 − R.
    State that ROC-test is touched twice for A and D, both pre-registered, neither selecting.
13. **(#13, B) Screen history.** Replace the "unanswered input" (l. 478-481) with a PREFLIGHT
    gate item beside [A7]: the investigator's answer to Disputed fact 1, before the canary.
14. **(#14, B) [D1].** Drop "lowest of the plain N=64 arms traced", or have [A7] also trace
    A06-N64 (d16, h4, L2, FFN32) and say how the result would bear on the base choice.
15. **(#15, B) A vs F pairing.** Pre-register a PREFLIGHT comparison of `kernel_hashes` for A-s1
    and F-s1; if only `pos_table` differs, A − F is a paired comparison (t, df 7, sign count),
    else Welch. Update the comparisons table and the Seeds section.
16. **C items (#16-#27), apply before commit, no re-review needed for them:** §6.8 sentence;
    figure pre-registration; winner's-curse numbers and per-run validation − held-out gap;
    EBOPs-at-selection wording; MLP Mixer label; one fidelity table (7/7 width init, key_dim
    16 vs 12, β0, value-wise widths, input quantizer); Holm family; gate-then-standardize check
    in [A3]; AUC-selected sensitivity; stale-field stripping with a config diff; the K=6 memory
    prior; the "5M" wording.

Iteration 1: no cap warning. Nothing here needs Kai before the fixer acts; the Kai decisions
(arm H, pod count, the [D15] launch branch, the flagged "Where I am not sure" items) are
routed to the canary/launch gate.
