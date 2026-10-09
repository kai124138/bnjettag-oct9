---
id: 2026-10-05-pilot-program
date: 2026-10-05
type: pilot-program
status: draft (pre-registered before any pilot result; not reviewed, not frozen)
question: Why do binary-weight N=64 transformers collapse at 350k EBOPs but stay healthy at 5M, and at which budget and fix should A and NB production run?
code_sha: R1/R2 = the option-(c) bundle after the CPU-gate fix (sha not yet assigned); R3 = that bundle plus NB code (and H3 if built)
wandb: BNJetTag-ChangRecipe / group per round (filled at PREFLIGHT)
---

Owner: experiment-designer. Approved program: `docs/PILOT_PROGRAM.md`, `.claude/memory/decisions.md`
(2026-10-05 10:08 JST). This document is written before any pilot of the program exists.
Rule changes after an R1 number exists are dated amendments signed by Kai and labelled post hoc.
**Pilots are directional.** They choose what to run next and which production configuration to
launch. No pilot number is a result, enters `verify.json` or appears in outward text.

## 1. Question, null, bearing

**Question.** Why does binary N=64 collapse at 350k EBOPs (uniform attention, degenerate or weak
checkpoints) when it stays healthy at 5M? Which budget and variant should production use?
**Null.** No single tested factor (controller input, budget headroom, attention width, squeeze
timing, binary weights) changes health at 350k.
**Bearing.** Every paper tier needs A − NB at 8 paired seeds (`docs/ROADMAP.md` §5). This program
picks the budget and variant, using a rule fixed here.

Prior state. Every number below is a single seed on validation (n = 62,000), pilot telemetry,
and never quoted. At 350k every head is at entropy/log 64 = 1.000000 (b5 `VERIFY.md` §6;
`READOUT_epoch500.md` table (2)). A-s1 is degenerate, and the A-s2 and D-s1 best checkpoints
are weak (0.320871 and 0.405371). C-s1 (A07, 5M) has heads 0.622127, 0.913695, 0.543640 and
0.880046, with val acc 0.664726. These come from the 42abed code, without option (c), on A10.

## 2. Hypotheses and predictions

The static floors come from a synthetic CPU trace, which is not a result
(`campaigns/2026-10-02-chang-option-c/code/tree/campaigns/chang1002c/static_floors.json`):

| arch | 0-bit floor | ≥1-bit attention, narrow (Q·K, A·V streams) | full (+ Wq/Wk/Wv inputs) |
| --- | --- | --- | --- |
| E (d24, 2 heads) | 171,526 | 368,134 | 478,726 |
| A07 (d32, 4 heads) | 343,053 | 605,197 | 801,805 |

Headroom (budget − 0-bit floor). E: 250k 78,474; 350k 178,474; 500k 328,474; 750k 578,474;
1M 828,474; 2M 1,828,474; 5M 4,828,474. A07: 350k 6,947; 500k 156,947; 1M 656,947;
2M 1,656,947; 5M 4,656,947. (Arithmetic on the floors.)

| # | hypothesis | prediction if true | prediction if false |
| --- | --- | --- | --- |
| H1 | The controller's input error causes the collapse | A@350k with (c) is healthy on both seeds; without (c) it is not | (c) is unhealthy on both seeds |
| H2 | The fixed binary floor leaves too little headroom | health is monotone up each ladder; A07 recovers at the smallest A07 rung whose headroom is ≥ the headroom at E's recovery rung (E 250k→A07 500k; 350k, 500k or 750k→1M; 1M→2M; 2M→5M) | no rung of the ladder is healthy (E at 5M unhealthy), or A07 recovers ≥2 rungs away from the prediction |
| H3 | Attention is starved first (Q/K/V go to 0 bits) | with a 1-bit Q/K/V floor, A is healthy at a budget where it is otherwise unhealthy. Static corollary, checked on R1: the E entropy transition falls at 500k (the first rung ≥ 368,134) and A07's at 1M (≥ 605,197) | the floored arm is still unhealthy on all 3 seeds |
| H4 | The squeeze comes too early | A PID warmup of 50 or 150 epochs is healthy where warmup 1 is not | both warmups do no better than warmup 1, while both still reach the budget |
| H5 | Binary weights themselves cause it | NB (learned-width weights) is healthy at 350k when the best binary fix is not | NB is no healthier than binary at 350k (in particular 0/3: then the cause is the budget, not binary) |

These hypotheses are not exclusive. Most of all, H2 and the static H3 corollary predict the same
rungs in the likely case (E at 500k, A07 at 1M). R1 can be consistent with both but cannot tell
them apart. R2's direct H3 arm separates them.

## 3. Common setup (all rounds)

Recipe as in training-batch `STUDY.md`: Chang optimizer and cosine restarts (peak 3e-3, cycles
of 500), batch 2,790, [D19] quantizers, [D20] trace sample, `split_seed` 1, `order_seed = f(s)`.
Data: cache `/data/chang-n64-20260926/n64/data`, `data_info.json` sha256 `c6d058f5…e228` (from the
option-(c) handoff `record.json`), N = 64, features pt/etarel/phirel, train 558,000, validation
62,000. Regime B: trace every 10 epochs. Each run is stopped at **epoch 500**, the end of the
first cosine cycle. Product: **RTX 3090, one arm per GPU, one product per round.** Option (c) means
`train.ebops.pid_input: traced_only`, `pid_traced_integral: per_epoch`; "no (c)" means the keys are
absent. PID warmup is `train.ebops.pid.warmup`, 1 by default. Under (c), epoch warmup−1 must be
traced (`ablation.py:535-541`), so the allowed warmups are 1, 10, 20 and so on.

## 4. R1, broad sweep (fixed, 19 pods)

| # | arm id | hyp | arch | budget | (c) | warmup | seeds | pods | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | A350-noC | H1 | E | 350k | no | 1 | 1, 2 | 2 | H1 control; the 42abed controller on the new sha and the 3090 |
| 2 | A350-C | H1, H2 | E | 350k | yes | 1 | 1, 2 | 2 | H1 treatment; s1 is the E ladder's 350k rung; baseline for H4 |
| 3 | E250-C … E5M-C | H2 | E | 250k, 500k, 750k, 1M, 2M, 5M | yes | 1 | 1 | 6 | E ladder; locates E's recovery rung |
| 4 | A07-350-C … A07-5M-C | H2 | A07 | 350k, 500k, 1M, 2M, 5M | yes | 1 | 1 | 5 | A07 ladder; tests whether health follows headroom across architectures |
| 5 | A350-C-w50 | H4 | E | 350k | yes | 50 | 1, 2 | 2 | squeeze held past the observed Q/K collapse at ep0 29-39 (b5 `VERIFY.md` §6) |
| 6 | A350-C-w150 | H4 | E | 350k | yes | 150 | 1, 2 | 2 | 3× later; 350 epochs still remain to reach the budget (b5 runs first met (a) at ep0 ≈259-389) |

19 pods. Matched: only the listed column differs from A350-C.

## 5. Readout (one row per run; the shared `readout.json`)

Exactly these fields: `arm`, `hypothesis`, `arch`, `budget`, `option_c`, `warmup`, `seed`, `epochs_done`,
`feasible_any`, `min_traced_ebops`, `best_feasible_val_acc`, `best_feasible_val_auc`, `nondegenerate_best`,
`attn_entropy_norm_mean`, `status`. Definitions, on validation (n = 62,000) and traced epochs 1-500:

- `feasible_any`: at least one traced epoch meets (a) traced EBOPs ≤ budget and (b) EBOPs above the
  architecture's 0-bit floor > 0 (training-batch `STUDY.md:995-1012`).
- `nondegenerate_best`: the runner's best-feasible checkpoint exists. It meets (a), (b) and (c): val acc
  > 0.2109624456315518 (`PREFLIGHT.md:519`, p_maj + 5·SE; the readout asserts the same labels sha
  `e593f51f…7617`). If it is true while `feasible_any` is false, the readout is inconsistent and the
  program stops.
- `best_feasible_val_acc` / `_auc`: top-1 accuracy and macro-OvR AUC of that checkpoint, selected
  by accuracy, then AUC, then −EBOPs, then −epoch (the frozen rule); null if none exists.
- `attn_entropy_norm_mean`: the mean over heads of the row-renormalized entropy / log 64
  (`code/analysis/attn_entropy.py`, [A26]), computed on the best-feasible checkpoint, or on
  `model_min_ebops` when none exists. Uniform attention = 1.0.
- `status`: `complete` means epochs_done = 500, no divergence, certification pass for the
  selected checkpoint, and (if `option_c`) CONTROLLER_AUDIT PASS. Otherwise `failed`, `diverged`,
  `cert_fail` or `audit_fail`.

**Healthy** = `status == complete` AND `feasible_any` AND `nondegenerate_best` AND
`attn_entropy_norm_mean < 0.95`.
Why 0.95: under WRAP quantizers a 0-bit Q gives logits that are identically zero, so collapsed
heads sit at exactly 1.000000 with a per-jet sd of 0.0. Every collapsed head in b3/b5 does. The only
working reference has a mean of 0.739877 (C-s1, arithmetic on the four heads) and a highest head of
0.913695. A cut at 0.95 sits between the two and allows for a small spread. With 2 heads, one uniform
head passes only if the other is below 0.90.

## 6. Judging (directional; counts carry a Clopper-Pearson 95 % interval)

With 2 seeds, 2/2 against 0/2 is the only separating pattern. With 3 seeds, 0/3 has the interval
[0, 0.708] and 3/3 has [0.292, 1], so only the extremes count. Paired val-acc differences are
listed per seed. When there are ≥ 3 matched seeds with both values non-null, a 95 % t-interval
(df = n − 1) is added. Comparisons always use matched seeds.

| hyp | round | supported | refuted | otherwise |
| --- | --- | --- | --- | --- |
| H1 | R1 | A350-C 2/2 healthy and A350-noC 0/2 | A350-C 0/2 | inconclusive |
| H2 | R1 (+R2 rung) | both ladders monotone (no healthy rung below an unhealthy one) and the A07 recovery rung equals the H2 prediction | E unhealthy at 5M, or A07 ≥ 2 rungs from the prediction | inconclusive (1 rung off, or a non-monotone ladder) |
| H3 | R2 | H3 arm healthy on all matched seeds and baseline on none | H3 arm 0/3 | inconclusive; R1 entropy transition at E 500k / A07 1M reported as consistent or not, never judged |
| H4 | R1 | a warmup arm 2/2 healthy while A350-C 0/2 | both warmups ≤ A350-C's count, with `feasible_any` on all 4 rows | inconclusive (incl. a warmup row with `feasible_any` false: time-limited) |
| H5 | R3 | NB@350k 3/3 and best binary fix@350k 0/3 (same R3 sha, seeds 1-3) | NB@350k count ≤ binary count | inconclusive |

## 7. R2, zoom in (rule; ≤ 12 pods)

Computed by the autopilot from the R1 readout:
1. **r1** = the lowest E rung (A350-C s1 counts as the 350k rung) whose seed-1 row is healthy. If no E
   rung is healthy: **stop**, notify Kai (pivot: characterization; ROADMAP §4).
2. **Bracket** = {the rung below r1, r1}. If r1 = 250k, it is {250k, 350k}. Each bracket rung is
   brought to seeds {1,2,3,4} (A350-C already has 1 and 2), with (c) and warmup 1. That is 5-6 pods.
3. **V_b**, the best H1/H4 variant among A350-noC, A350-C, A350-C-w50 and A350-C-w150, ordered by:
   healthy count, then `nondegenerate_best` count, then `feasible_any` count, then lower mean
   entropy, then the fixed order C > noC > C-w50 > C-w150. It is brought to seeds {3,4,5} at 350k,
   skipping seeds that step 2 already launches. That is ≤ 3 pods. Accuracy is not a criterion,
   to avoid selecting on single-seed noise.
4. **H3**, only if its option has passed its CPU gate and has a traced static floor F_H3 before the R1
   readout. B_H3 = 350k if F_H3 ≤ 350,000 − 17,847 (10 % of E headroom, the K1 scale). Otherwise
   it is the lower bracket rung r_lo, if F_H3 ≤ r_lo − 0.1·(r_lo − 171,526) and r_lo ≥ 350k.
   Otherwise H3 is not run, and Kai is notified. It runs with (c), warmup 1 and seeds 1-3 (3 pods).
   Its baseline is A-(c)-w1 at B_H3, on matched seeds. On the static numbers above, E at 350k
   **cannot** hold 1-bit narrow attention (368,134 > 350,000), so the 350k test is possible only if
   the H3 option floors fewer streams.

After R2: **r_rec** = the lowest bracket rung with ≥ 3 of 4 seeds healthy. If none: **stop**, notify.

## 8. R3, the decisive test (rule; ≤ 9 pods; needs the NB code CPU gate)

- **Best binary fix** = whichever of {V_b at 350k, H3 if B_H3 = 350k} has the higher healthy fraction
  over all its 350k seeds; on a tie, V_b. It runs at seeds 1-3 on the R3 sha (3 pods), so the
  binary control shares NB's code and round.
- **NB@350k**, seeds 1-3 (3 pods). It uses the best binary fix's configuration with only the
  weights changed (kbi learned width, training-batch `STUDY.md:749`).
- **NB@r_rec**, seeds 1-3 (3 pods), with (c) and warmup 1. If r_rec ≤ 350k, it runs at 250k instead.

## 9. Production trigger (fires without asking only if every condition holds)

Candidates are fixed by rule after R2, when ml-engineer builds their handoffs: **P350** = (350k, best
binary fix) and **Prec** = (r_rec, (c), warmup 1), each as A and NB.
1. **P350** if: the R3 binary fix at 350k is healthy 3/3, NB@350k is healthy 3/3, and every one of
   those 6 rows has `best_feasible_val_acc ≥ 0.50`.
2. Otherwise **Prec** if: r_rec > 350k, A at r_rec is healthy ≥ 3/4 (R2), NB@r_rec is healthy 3/3,
   and every healthy A row and every NB row at r_rec has `best_feasible_val_acc ≥ 0.50`.
3. Otherwise: no launch. Stop and notify Kai with the readout.

Guards, all required: every R3 row has `status` complete and the readout integrity checks pass; the
chosen candidate's handoffs are listed in `PROGRAM.json` and Kai re-signed that fill; the
spend-so-far plus 960 GPU-h stays ≤ 1,200; the product is RTX 3090.
**What launches:** two Jobs, A and NB at the chosen budget and variant, seeds 1-8, 7,000 epochs,
regime B, one arm per GPU, 16 pods. Production selection and analysis follow the frozen
training-batch rules (validation selection; ROC-test touched once at production VERIFY).
Why 0.50: the 350k checkpoints of the earlier pilots reached 0.236-0.405 (weak), and the 5M or
unconstrained ones 0.65-0.66. A run below 0.50 at epoch 500 is not worth 960 GPU-h without Kai.

## 10. Stop rules (the autopilot stops, notifies and launches nothing further)

- Any row with `status` ≠ complete, a Job with backoff exhausted, or a missing row or unexpected
  row count in `readout.json`.
- A readout integrity failure: the threshold is not 0.2109624456315518, the labels sha differs, or
  `nondegenerate_best` is true while `feasible_any` is false.
- A pod not on an RTX 3090, or GPU utilization < 40 % at 30 min after launch (notify; repacking
  needs a new handoff).
- A cap reached or projected over (§11).
- A scientific stop: no E rung healthy (§7.1), r_rec undefined, or A350-noC healthy 2/2 while
  A350-C is 0/2 ((c) harmful).
- No rule matches, or a handoff named by a rule is still a placeholder. An AI session may draft
  the next step for Kai; it never launches.

## 11. Spend caps (RTX 3090 GPU-h, pod running time)

| round | pods | GPU-h cap | basis |
| --- | --- | --- | --- |
| R1 | 19 | 114 | 6 h per pod. 500 × 30.85 s ≈ 4.3 h for A07 (PILOT_PROGRAM §3); E speed unmeasured |
| R2 | ≤ 12 | 72 | same |
| R3 | ≤ 9 | 54 | same |
| production | 16 | 960 | 7,000 × 30.85 s ≈ 60 h per pod (the A07 rate; projection) |
| **total** | ≤ 56 | **1,200** | decisions.md 2026-10-05 |

Pods in flight never exceed 24. At a cap the autopilot launches nothing further. Running pods end
by their Job deadline (`activeDeadlineSeconds`, set by cluster-ops to the per-pod basis).

## 12. Not allowed

- No pilot or readout reads the ROC-test (held-out) set, and no selection uses it.
- Selection uses validation only. Pilot numbers are never quoted, compared in a claim, or put in `verify.json`.
- No threshold, rung, seed or rule changes after an R1 number exists, except by a dated amendment
  signed by Kai and labelled post hoc.
- No code, config or manifest edit to a live round. A fix is a new PREFLIGHT and a new sha.
- No comparison across GPU product or code sha inside a judgement row (the R3 binary control exists for this).
- No number from the home PC enters any rule.

## 13. Conventions compliance

| convention | status |
| --- | --- |
| jet-tagging-metrics: validation selection, labels, matched seeds, intervals | will implement (§5-6); the N=64 line uses 90/10 (n_val 62,000) and accuracy-first selection, as frozen in training-batch, not the 80/20 AUC default (ROADMAP §7.2) |
| quantization-and-cost: native EBOPs at the selected checkpoint, "no feasible checkpoint" | will implement (certification in `status`) |
| fpga-synthesis, figures | not applicable (no synthesis, no figure in this program) |

## 14. Where I am not sure (all FLAG FOR HUMAN: YES)

```
D1 DECISION: healthy needs attn_entropy_norm_mean < 0.95 (set from 42abed pilots, before any program data).
   ALTERNATIVES: < 0.99; per-head max < 0.95; no entropy term (feasible + non-degenerate only).  CONFIDENCE: MEDIUM
D2 DECISION: the recovery rung (r1, r_rec) uses healthy, not only feasible + non-degenerate.
   ALTERNATIVES: feasible + non-degenerate only (lower rung, possibly uniform attention).  CONFIDENCE: MEDIUM
D3 DECISION: H4 warmups 50 and 150 (under (c) the warmup must be 1 or a multiple of 10).
   ALTERNATIVES: 100 and 250 (250 leaves 250 epochs to reach budget); unconstrained-then-squeeze (new code).  CONFIDENCE: MEDIUM
D4 DECISION: H3 at 350k only with >= 10 % headroom over its traced floor, else at the lower bracket rung.
   ALTERNATIVES: always 350k (narrow 1-bit floor on E is 368,134 > 350,000).  CONFIDENCE: HIGH (arithmetic), MEDIUM (fallback)
D5 DECISION: production auto-launch needs 3/3 healthy for binary and NB, and val acc >= 0.50 at epoch 500.
   ALTERNATIVES: floor 0.40; no accuracy floor; >= 2/3 healthy.  CONFIDENCE: MEDIUM
D6 DECISION: Prec (a budget other than 350k) is pre-authorized by signing PROGRAM.json; it re-scopes the
   frozen training-batch question to A - NB at r_rec, with a dated amendment drafted during R3.
   ALTERNATIVES: Prec always stops for Kai; only P350 fires on its own.  CONFIDENCE: LOW
D7 DECISION: production handoffs built after R2 for the two rule-chosen candidates; Kai re-signs the fill (ids only).
   ALTERNATIVES: pre-build all ~18 candidates (NB code missing); autopilot checks a config spec, not ids.  CONFIDENCE: MEDIUM
D8 DECISION: production seeds 1-8 (pairing with frozen training-batch, [A17] checked at 1-8).
   ALTERNATIVES: fresh seeds 9-16 (config was chosen on validation of seeds 1-5; test clean either way).  CONFIDENCE: MEDIUM
```
- The epoch-500 cut does not see the first LR restart, so a late recovery (D-s1 re-grew attention
  after epoch 400) would be missed. E's speed and utilization at one arm per GPU are unmeasured.
