# STUDY review, critical-reviewer, v2: 2026-09-26-training-batch

Panel mode, re-review (n = 2). No verdict; the arbiter decides. Artifact: `STUDY.md` (711
lines, mtime 2026-09-27 00:02), `plan.md` (fixer sections), `review/STUDY_fixer_v1.md`.
Earlier findings: `review/STUDY_arbiter_v1.md` (#1-#27) and my own `STUDY_critical_v1.md`
(A1-A3, B1-B5, C1-C4). Investigator: `review/STUDY_investigation_350k.md`.
Validators: `STUDY_validators_v1.txt` and `_v2.txt`. No mechanical STUDY validator exists.
`prose_lint` gives score 0 (8,915 words, 0 em-dashes). There are no A lines to quote. STUDY
has no figures, so `plot_check` does not apply.

Code paths `ablation.py`, `run_study.py` and `check_engram.py` are from the screen bundle
`campaigns/2026-09-22-constituent-screen/study-code.tar.gz`, re-extracted read-only to the
session scratchpad in this session.

## Recomputed in this session

- **Archived N=64 spread** (STUDY:67, 189). I recomputed it from
  `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz`. Keys are `y`, `score` and `meta`;
  `y` has shape (260000, 5) and every score is finite. Held-out top-1 accuracy:
  - W1A8: 0.6718 / 0.7264 / 0.6721, mean 0.6901, sd 0.0314 (ddof = 1);
  - FP32: 0.7942 / 0.7883 / 0.7910, mean 0.7911, sd 0.0030.

  This matches STUDY:67 "69.0 ± 3.1 %" and "79.1 ± 0.3 %". `meta` confirms the metric
  `roc_test_auc_macro_ovr` with n = 260,000. RESEARCH.md:114 confirms "101 epochs" (STUDY:62).
- **Arithmetic** (scipy):

  | quantity | recomputed | STUDY |
  | --- | --- | --- |
  | t(.975,7)/√8 | 0.8360 | 0.836 ✓ |
  | t(.975,5)/√6 | 1.0494 | 1.05 ✓ |
  | 0.836 × 3.14 | 2.625 | 2.63 ✓ |
  | 1.049 × 3.14 | 3.29 | 3.3 ✓ |
  | 0.5 / 0.836 | 0.598 | 0.6 ✓ |
  | 0.5 / 1.049 | 0.477 | 0.48 ✓ |
  | binomial SE, n = 62,000 | 0.164 pt | 0.16 ✓ |
  | binomial SE, n = 124,000 | 0.116 pt | 0.12 ✓ |
  | 83 s × 7,000 | 6.72 d | 6.7 ✓ |
  | 172.8 s × 7,000 | 14.0 d | 14 ✓ |
  | P = 2 at 30 s | 4 × 58.3 h = 9.7 d | 9.7 ✓ |
  | W&B artifact versions | 48 × 280 + 8 × 40 = **13,760** | "about 15,700" ✗ (C3) |

- **Code claims.**
  - `ablation.py:278-287`: `cost_before_auc=True` gives (acc, −EBOPs, AUC, −epoch). `:421`
    sets `cost_first = bool(cfg.get('engram_study'))`. [A13] is correct.
  - `run_study.py:29` and `check_engram.py:147` index `cfg['engram_study']` directly, so
    preferring an explicit override is right.
  - `save_checkpoint` is at `:192` and is called at `:456` every epoch. `:462` reads only
    `remote_every_epochs`. `const0922-a07-n64-s1-fast50-fp32.json:98` has
    `"checkpoint_every_epochs": 1`, and the runner never reads it. [A15] is correct.
  - `:414-424`: `model_unconstrained.keras` is AUC-best with no feasibility filter, so [A19]
    is right.
  - `jsc150/model.py:186` has `b0=4, f0=4, SAT_SYM` and `:195` has `QMultiHeadAttention(h, 16)`.
    `:295` has `LayerConfigScope(beta0=0)`. The fidelity table is correct.

## Earlier A and B findings, by name

| earlier finding | status | evidence in STUDY v2 |
| --- | --- | --- |
| **Arb #1 / crit A3(b)**: descriptive recast, iso-EBOPs, no "binary survives" | **Resolved** | Frontmatter l. 6, title l. 30, Question l. 32-37, Null l. 39-42, Bearing l. 44-51. "iso-cost" appears only in negation (l. 47). The experiment-log stub (`experiment-log.md:11-13`) matches. |
| **Arb #2 / crit A3(a)**: competing-group answer, arm H | **Resolved** (at the arbiter's minimum) | The l. 656-665 block gives arm H and the in-house arm, the reasons they are omitted, and "FLAG FOR HUMAN" at the launch gate. "Kai asked for binary trainings" is backed by `method-atlas/BRIEF.md:19` ("Our binary {−1,+1} weights"). |
| **Arb #3 / crit A1**: resolving power | **Resolved, with a new hole** | l. 187-200 state both bounds, k = 6 and the 0.6 / 0.48-pt ceilings. [D13] is amended at l. 503-506. The consequence can be undefined: see new B1. |
| **Arb #4 / crit A2**: tie-break | **Resolved** | l. 204-211 and [A13] l. 561-567 give the explicit override and the unit test on a constructed tie. Verified against the code above. |
| **Arb #5**: reference uncertainty [L1] | **Resolved** | l. 603-612 give the deltas, best-of-several and the gate question. Labelling nit in C1. |
| **Arb #6 / crit B2**: comparand fixed unconditionally | **Resolved** | l. 272-279 fix 79.4 with its reason and put the 79.8 and 77.9 distances "in every outcome". The conditional sentence is gone. |
| **Arb #7**: attention diagnostic | **Resolved** | l. 299-310 give Q/K and V separately plus entropy / log 64. l. 695-700 are corrected. |
| **Arb #8 / crit B3**: pairing, infeasibility, divergence, stability | **Resolved, with a coherence issue** | l. 214-229 and 290-294: pre-divergence checkpoints are not evaluated, survivor bias is stated, and McNemar is used. The Holm label on the stability claim contradicts the count rule: new B2. |
| **Arb #9**: EBOPs equivalence | **Resolved** | [A14] l. 568-572. |
| **Arb #10 / crit B1**: expected [D15] branch, pod count to Kai | **Resolved in structure; the numerical basis is wrong** | l. 338-345 and 358-361 are present, but the per-epoch times they rest on are mis-sourced: new **A1**. |
| **Arb #11**: overhead [A15] | **Resolved** | [A15] l. 573-577. The 50 % overhead rule is at l. 381-384. The code is verified above. |
| **Arb #12**: epoch-matched A1000 − R | **Resolved** | l. 120-122, 253-254 and 288. |
| **Arb #13 / crit B4**: screen history as a gate | **Resolved** | [A16] l. 578-589 carries the investigator's answer, and confirmation on the PVC is required before the canary. |
| **Arb #14 / crit B5**: [D1] rationale | **Resolved** | The claim is dropped (l. 460-465). |
| **Arb #15**: A vs F pairing | **Resolved** | [A17] l. 590-593, the comparisons table l. 113, Seeds l. 183-185. |
| C batch #16-#27 | All present | #16 l. 439; #17 l. 312-315; #18 l. 234-237; #19 l. 230-233; #20 l. 64; #21 l. 124-142; #22 l. 258-262; #23 l. 531-533; #24 l. 238-240; #25 [A18]; #26 l. 377-380; #27 l. 704-708 (corrected per the investigator: the reason is recorded, `CONFIRMATION_RUNS_20260924.md:26`). |

## Category A

**A1. The per-epoch times behind the expected [D15] branch, the R projection and the pod-count
decision are mis-sourced. One of them has no source. The base architecture's own measured
time is left out.** (STUDY:332-336, 338-345; plan.md fixer pass "83 s → T_run 6.7 d; 190-245 s
→ 15.4-19.8 d"; `experiment-log.md:13`)

- STUDY:338-340 says: "The only measurements are at batch 256 and **N=64**: the screen's
  corrected canary, 83-190 s per epoch". The **83 s** is an **N=8** arm:
  - `attempt2/live-status.json`: `const0922-e02-n8-s1-fast50-fp32` has
    `last_epoch_wall_seconds` 83.53;
  - `verified-launch-gates.json` shows the same.

  The log line (`experiment-log.md`, 2026-09-22, "Corrected canary epoch wall times83–190s")
  mixes N=8 and N=64 arms. STUDY relabels it as N=64.
- STUDY:332-334 and 340 cite "190-245 s per epoch (`live-status.json`)". **245 does not appear
  in `live-status.json`**, and it does not appear anywhere in the screen campaign directory
  (grep). The per-run values in that file are:

  | run | s per epoch |
  | --- | --- |
  | a02-n64 | 189.7 |
  | **a07-n64** | **100.1** |
  | a07-n8 | 104.8 |
  | e02-n8 | 83.5 |
  | e03-n64 | 640.2 |
  | e03-n8 | 86.7 |
  | a02-n8 | 749.7 |

  The "190" is A02-N64: two blocks, FFN 32, the flagship lineage. It is not the A07
  architecture this design runs.
- **The base architecture's own time is in the same file.** A07-N64 ran 100.1 s per epoch at
  batch 256, epoch 2, packed. Taken the way STUDY takes its numbers (no speed-up from the
  larger batch), that gives T_run = 7,000 × 100.1 s = **8.1 d**. That fits the 14-day rule,
  so the stated expected branch "report to Kai before launch" does not follow from the
  relevant measurement.
- The R projection has the same flaw. "214-276 s … 59-77 h per run … 120-150 pod-hours"
  (l. 335-336) is 190-245 × 558/496. From A07's 100.1 s it is about 113 s, about 31 h per
  run, and about 63 pod-hours.
- A better source exists. The runner logs `epoch_seconds` to W&B every epoch
  (`ablation.py:442`). The investigator has already queried group
  `constituent-20260922-fast50`, which holds all 50 epochs of A07-N64-s1.
- **Impact.** A number with no source ("245"), and a measurement relabelled from N=8 to
  N=64, feed a decision the design routes to Kai: the expected [D15] branch, and "10 pods
  versus a couple". The same framing was copied into the experiment-log stub
  (`experiment-log.md:13`, "83-245 s/epoch"). The design's structure survives, because the
  canary decides [D15]. The pre-registered expectation Kai will read is still wrong in
  direction.
- **Fix.**
  - Cite per-arm, per-N times with file and run name.
  - Use A07-N64 (100.1 s in `live-status.json`, or the W&B `epoch_seconds` median over
    epochs 2-49 of `const0922-a07-n64-s1-fast50-fp32`) as the base-architecture prior.
  - Drop "245" unless a source is named.
  - Restate the expected branch and the R pod-hours from that prior.
  - Correct the stub line.

## Category B

**B1. The epoch-500 consequence for [D13] is undefined in the most likely case. No
pre-registered consequence covers a trajectory that is nowhere near the budget.**
(STUDY:195-200, 241-246, 503-506; investigation "Answer" and "Caveats" 1 and 4)

- A readout reports the **best-feasible-as-of-E** snapshot (l. 243). The trigger is "arm A's
  epoch-500 validation accuracy sd". If fewer than 2 A seeds are feasible at epoch 500,
  there is no sd, and the one pre-registered consequence cannot fire. That is the fix for
  arbiter #3.
- This case is not remote. The investigator found that A07-N64 got no lower than 4,630,276
  EBOPs in 50 epochs (13.2× the target). β was 1.8e-5 against a 1e-3 cap.
- The PID updates once per epoch (`ablation.py:387, 429`: `pid.on_epoch_begin` /
  `on_epoch_end`). At batch 2,790 an epoch is 200 steps against 2,180 in the screen, so the
  screen's per-epoch trajectory does not transfer, in either direction.
- Nothing in the design says what happens if, at epoch 500 or 1,000, 0/8 A seeds are feasible
  and the EBOPs trend is flat far above 350k. The full 336,000 run-epochs continue by
  default.
- **Fix.**
  - Define the sd trigger when k < 2 at epoch 500. Either use the sd of the unconstrained
    validation accuracy, labelled as such, or state "undefined, report to Kai".
  - Add one more report-to-Kai consequence, with the same "never selects" wording: A's
    feasible count and median EBOPs / target at epochs 500 and 1,000, with a stated threshold
    (for example 0/8 feasible and median EBOPs > 3× target at epoch 1,000).
  - This is a report, not a stop rule. It keeps [D13]'s spirit and closes the silent-spend
    path.

**B2. The Holm label on the stability claim contradicts its own count rule.** (STUDY:258-262,
290-294; plan.md fixer pass notes "a McNemar-plus-count stability rule was unreachable at 4-0
(exact one-sided p 0.0625)")

- The claim is falsified at a divergence excess of ≥ 4. With exact McNemar on 8 pairs:
  - 4-0 discordant gives two-sided p 0.125 (one-sided 0.0625);
  - 5-0 gives 0.0625;
  - p < 0.05 needs 6-0 or better.
- Holm over {recipe, stability} can only raise p. Every stability falsification at 4-0 or
  5-0 will therefore be reported as "falsified" and "fails the multiplicity adjustment" at
  once. The fixer knew this (plan.md) and left the contradiction in STUDY. STUDY also does
  not say whether McNemar is one-sided or two-sided.
- Separately, "A diverged count exceeds D diverged count by ≥ 4" is a statement about
  marginal counts, while McNemar tests the discordant pairs. The two coincide only when no
  seed diverges in both arms. Say which one decides.
- **Fix.** Say the count rule decides the stability claim and that its exact p is
  informative, outside the Holm family. Or keep it in the family and say explicitly that a
  4-0 or 5-0 falsification will carry the multiplicity label. State the sidedness.

## Category C

- **C1. [L1] and reference-table labels** (l. 65, 606-608).
  `_attic/repro-chang/repro-chang/comparison.md:8-9` says that `xfmt` "is the post-paper
  LUT/QDenseT Linformer (k=4), not the paper's Linformer", and that the REPRO-CHANG runs used
  the **open-loop β `PieceWiseSchedule`**, not the paper's PID.
  - The +1.05-pt delta is therefore across two architectures.
  - "It shows the recipe works on our infrastructure" (l. 65) holds for the open-loop β
    recipe, not for the PID recipe of [D5].

  Label both.
- **C2. Canary stability checks are qualitative** (l. 370-373): "β moving" and "EBOPs
  falling". Given B1, give a number the canary can fail on, for example EBOPs at epoch 10
  relative to epoch 1, set against the screen's epoch-9 value (7,610,858, investigation
  trajectory; W&B, not a result).
- **C3. W&B artifact count** (l. 412-413). 280 versions per run is right for the 48
  Chang-schedule runs. R has 1,000 epochs and therefore 40 versions, so the total is 13,760,
  not "about 15,700 across 56 runs".
- **C4. Kai's quotes are recorded only in STUDY and the review files.** "a couple of pods"
  appears nowhere else (grep across the repo, excluding `research/` and `publication*/`).
  `method-atlas/BRIEF.md:14-19` records the recipe, the lower EBOPs limit, "the way it's
  implemented", the changed architecture and "binary". It does not record the pod count.
  Record Kai's brief with its date in `decisions.md` or the campaign directory, because the
  launch gate turns on it.

## Numerical self-consistency (STUDY vs stub vs plan)

| quantity | STUDY | stub `experiment-log.md:13` | status |
| --- | --- | --- | --- |
| 56 runs | l. 105 | 56 | ✓ |
| 0.836·sd, ±0.16, ±2.63 pt | l. 179, 188-189 | same | ✓ |
| archived sd 3.14 pt | l. 189 | 3.14 pt | ✓ (recomputed 0.0314) |
| 0.6-pt trigger | l. 198 | 0.6 pt | ✓ |
| timing basis | 83-190 / 190-245 s | "83-245 s/epoch" | **✗ mis-sourced in both (A1)** |

## Decision-label traceability

- [D2], [D3], [D4], [D5], [D7], [D9] and [D18] were confirmed in v1 and are unchanged.
- [D11] is now consistent with the code through [A13].
- [D13] is amended and dated in the change log (l. 16-24). Its consequence is incomplete (B1).
- [D1] is amended (l. 462-465).
- [D15]'s expected branch rests on mis-sourced numbers (A1).
- No [D] is replaced silently.

## Completeness cross-check

- Arms: 7 × 8 = 56, and the stub agrees.
- Every arbiter item #1-#27 is present in the text.
- The Kai decisions are all routed to the canary/launch gate: arm H, the in-house arm, pod
  count, the [D15] branch, the split, the comparand, the base architecture, arm F and
  "the way it's implemented".

## Competing-group question

A group publishing next month would have a seeded, matched run of Sun et al.'s own code
(arm H). STUDY now justifies omitting it: Kai asked for binary trainings, it is one more
7,000-epoch JAX pipeline, and it is pre-registered as a follow-up and a Kai decision. The
answer is non-empty but justified. Not A.

## Summary of new findings

A1 (timing sources), B1 (epoch-500 consequence undefined; no far-from-budget consequence),
B2 (Holm versus count rule on stability), C1-C4.
