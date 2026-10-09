# STUDY arbiter v4: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-27. Artifact `STUDY.md` (1,655 lines), `plan.md`, `code/` (patches
0001-0023 staged; 0024 for [D25] not yet in `code/patches/`) and `code/evidence/`. Reviews v4:
`STUDY_physics_v4.md`, `STUDY_critical_v4.md`, `STUDY_constructive_v4.md`. Validators
`STUDY_validators_v4.txt`: `prose_lint` score 0, `E1-TRACE-PENDING` 0, no A lines; no figures, so
no plot-validator file. Earlier arbiter `STUDY_arbiter_v3.md`. Read `06-review.md` §6.1-6.8.
Kai's 08:40 answers (`decisions.md:57-76`: [D19], [D21] confirmed; 8-10 pods; H and NB as a
second wave, 8 seeds, paired by seed with A) are decided and not findings. Iteration **4**.

## Independent checks made by the arbiter

- **PID signal (physics B3).** `code/tree/bnhgq2/ablation.py:698-703`: when `d20`, the runner
  asserts `abs(pid._ebops - cost['total']) <= 1e-6 * cost` every epoch, where `cost` is the
  per-epoch full-split trace that feasibility reads (`:631`, `:664`). `d20` is
  `cfg['train'].get('ebops_trace_sample') is not None` (`:546`), and
  `chang0926-a-n64-s1.json:91` carries `"ebops_trace_sample": "train_full"`. The in-training value
  is logged beside it (`:629`, `:723`). **Resolved in code for A, B, C, D, F, R, A07-350.**
  **Not resolved for H:** STUDY l. 396-401 traces a *clone* and leaves the live model's per-batch
  `i`, so H's BetaPID would read the live `layer.ebops` while feasibility reads the clone. That is
  B3's scenario exactly, and H has no code yet. The STUDY text still says "ml-engineer states in
  PREFLIGHT whether BetaPID reads ..." (l. 1162-1164, 1360), which is stale.
- **[D25] staging (critical C2, constructive C1).** `grep i_decay_speed code/tree/bnhgq2` finds
  only the recorder `i_decay_speeds()` (`ablation.py:491-497`) and its callers (`:575-576`,
  `:791`); no setter, and `chang0926-a-n64-s1.json` has no `quant.i_decay_speed`. `decisions.md:30`
  records only "Finding, not changed: 0.01". STUDY l. 284 says "yes" and l. 1358 "is set to
  0.001". Confirmed stale until patch 0024 lands.
- **Selection text vs code (critical C5, constructive C3).** `ablation.py:664-668`: `model_best`
  is updated only when `feasible` = (a) ∧ (b) ∧ (c); STUDY l. 559-561 says "among (a)
  checkpoints". Outcome-equivalent for `model_best`, not for [A19]; the sentence is wrong.
- **Budget-claim threshold.** Constructive's proxy (ROC-test class fractions, n = 260,000;
  review arithmetic, not a result) gives p_maj 0.2023 and threshold 0.2104. Physics' and critical's
  ≈ 0.208 agree to rounding. The (c) test excludes only a near-constant classifier.
- **Physics B1.** Narrow-reading E floor 368,134 = softmax 171,526 + scores 98,304 + ctx 98,304
  (`static_floors_fix6_a07_e_e1.json`); all three are activation × activation terms. The sentence
  attributing this to binary weights is at l. 351, 656 and 1433. Physics is right.
- **v3 items spot-checked by line:** arms table l. 227-240 (E for A, B, D, F, R; A07 for C,
  A07-350; 56 runs) (#2); stability wording l. 686-694 "not falsified at this resolution (8 seeds)
  ... never calls the optimizer safe" (#6); FLAG l. 1497-1502 carries REPRO-CHANG xfm-n64 with
  its full label and "weights prune" caveat (#9).
- **Stability claim (physics C2).** l. 688-692 counts only diverged seeds (non-finite, l. 580).
  The Round-14 N=64 binary spread that motivates the claim is 67.18 / 72.64 / 67.21 % with
  finite losses (physics recomputed from `roc-results/r14/n64/W1A8-s{1,2,3}.npz`). As written the
  claim cannot see its own motivating failure mode.

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Certified-checkpoint mismatch has no stated outcome; can silently change k, gaps, budget count; certification batch unstated | crit B1 | B | **B** | Case 3; correct (l. 566-572 says "defect reported at VERIFY" only). Text |
| 2 | H: selection metric and (c) may be computed on the live model while the traced clone is saved and evaluated; and H's BetaPID reads the live model, not the traced clone | crit B2, phys B3 (H half, arbiter) | B, B | **B** | Case 1 plus case 4 (code checked above). Text in [A23] + a PREFLIGHT unit test |
| 3 | PID reads in-training vs traced EBOPs (A family) | phys B3 | B | **C** | Case 4: answered by `ablation.py:698-703` + `:546` + config l. 91. Remaining work is the stale text at l. 1162-1164, 1360 |
| 4 | Budget claim near-empty: (c) ≈ 0.21 on 5 balanced classes; "supported, 8/8" would read as a tagger success | phys B2, cons B3, crit C8 | B, B, C | **B** | Case 2, with physics and constructive. Resolve by demotion of wording, not a new floor (a threshold chosen now on no data, at iteration 4, invites tuning) |
| 5 | "Binary weights reach 350k only because attention may prune" attributes an activation × activation floor to binary weights | phys B1 | B | **B** | Case 3; verified on the JSON. Three sites |
| 6 | A − NB cannot resolve a "modest" cost; no wave-2 sd_diff readout; smallest resolvable gap not stated | phys B4 | B | **B** | Case 3. Text |
| 7 | Size wave 2 from wave-1 measured sd_diff (formula now, n later) | cons B1 | B | **B (text) + Kai option (seeds)** | Merged with #6. Pre-registering the formula and table is required; adding A/NB pairs beyond 8 changes Kai's 08:40 "8 seeds" and is his |
| 8 | Lead the A − NB report with the lower 95 % bound; state the directional prior (Sloot, FastML 2026) | cons B2 | B | **B** | Case 3; closes the §6.3.3 "wide interval read as support" pattern. Text |
| 9 | Wave 2 has no epoch-500 rule | cons B5 | B | **B** | Case 3. Text, mirrors wave-1 A rule |
| 10 | Primary measurement and recipe ladder have no pre-registered figure | phys B5 | B | **B** | Case 3; checked l. 758-776. Text |
| 11 | Stability claim counts only non-finite divergence; R14 instability was finite low-accuracy seeds | phys C2 | C | **B** | Case 5 (raised): the claim cannot detect its motivating failure mode (§6.4 falsifiability). Text, descriptive count |
| 12 | FP32 E arm | cons B4 | B | **B (row) + Kai option (arm)** | The Kai row and physics C5's scope sentence are required text; running the arm is Kai's (compute, and the runner path for `quant.weight: "none"` is untraced) |
| 13 | NB in the wave-1 seed blocks when its gates pass | cons B6 | B | **Kai option** | Kai took the second-wave default at 08:40 (`decisions.md:57-76`); the confounds of the default are stated (l. 435-436). Add as a Kai row, not a fix |
| 14 | [D25] reads as staged; absent from `decisions.md` | crit C2, cons C1 | C | C | Verified above; conditional fix |
| 15 | Stale "not staged" [D20] text (l. 469, 1170-1171, [A21] l. 1353-1355, experiment-log stub) | crit C1, cons C1 | C | C | Verified (`ablation.py:438-450, 546, 639`) |
| 16 | Selection sentence "among (a) checkpoints"; W&B `budget_met` semantics | crit C5, cons C3 | C | C | Verified above |
| 17 | [A17] body stale; F floor already traced | crit C3, C4 | C | C | |
| 18 | Pilot wall time without the trace factor (15.6 h vs ≈ 26 h) | crit C6 | C | C | |
| 19 | Three A07 / two E init EBOPs; name the PREFLIGHT value and sample | crit C7 | C | C | |
| 20 | "Confirmed exactly" for sums that are identities | phys C1 | C | C | |
| 21 | ROC figure mixes budgets (C beside A, R) | phys C3 | C | C | |
| 22 | A07 minimal-path sentence reads as 6,144 | phys C4 | C | C | |
| 23 | Scope sentence: no FP32/W8A8 baseline, no A8→A6→A4 ladder | phys C5 | C | C (required with #12) | |
| 24 | ROC-test WRAP overflow threshold; binary scale factor in EBOPs | phys C6, C7 | C | C | |
| 25 | Holm family carries foregone A − A07-350 | cons C4 | C | C | |
| 26 | Tag repetition "Kai request, 08:40" (29×); superseded FLAG block | cons C5 | C | C | |
| 27 | Split Kai rows by what they block | cons C6 | C | C | |
| 28 | Per-run selected epoch and cosine-cycle index | cons C7 | C | C | |

## Earlier A and B findings (arbiter v3), by name

| v3 # | finding | status | evidence (arbiter's own check) |
| --- | --- | --- | --- |
| 1 (A) | feasibility met by a collapsed network | **resolved** | STUDY l. 544-564 (a)-(c); `ablation.py:660-664` feasible = budget ∧ above floor ∧ above threshold; configs carry `experiment.nondegenerate`. Residual framing is new #4 |
| 2 (A) | A07-350k family floor-bound; ladder to E | **resolved** | arms table l. 227-240; Kai-confirmed `decisions.md:62-65` |
| 3 (B) | paper's ≥ 1-bit rule | **resolved** | fidelity row l. 270; static table l. 332-353; the attribution wording is new #5 |
| 4 (B) | softmax tax beside 79.4 | **resolved** | l. 653-656, [L2] l. 1431-1433 |
| 5 (B) | [D20] staging, dynamics, `i_decay_speed` | **resolved in code; text stale** | `ablation.py:438-450, 546, 639-644, 698-703`; fidelity rows l. 283-284. `i_decay_speed` value not yet set in code (#14) |
| 6 (B) | stability "never safe" | **resolved** | l. 690-692 |
| 7 (B) | recipe "never beats" | **resolved** | l. 675-680 (critical, A1000/D1000 beside) |
| 8 (B) | paired resolving power | **resolved** | l. 504-509; 0.836 · √2 · 3.1446 = 3.72 |
| 9 (B) | REPRO-CHANG in FLAG | **resolved** | l. 1497-1502 |
| 10 (B) | one-head E1 traced before pilot | **resolved** | `static_floors_fix6_a07_e_e1.json` E1 85,763; `pilot_packs.json` index 57 |

## Regression triggers (§6.7), checked independently

STUDY is the origin phase; no results exist.
- selection on held-out / changed after results: not met (validation only; `ablation.py:664`).
- val vs ROC-test AUC > 0.01; single-seed headline; cross-N series; gap < sd at < 3 seeds: not met (no numbers; REPRO-CHANG labelled context).
- reload > 1e-7 / TF32: not met (stored-state reload assert `:644`).
- EBOPs not remeasured / final-epoch cost mixed: not met (certification l. 566-572; its failure outcome is #1).
- binary > 2 values: not met (`binary_gate`, `:582`).
- DSP / C-sim / C-synth: not applicable.
- per-class AUC hidden: not met.
- byte-identical arms / different `y`: not met ([A11], [A17] 8-seed pairing).
- failed validation or tautological comparison: **not met**; the near-trivial (c) threshold was weighed and is handled by #4's demotion so no claim rests on it.
- [D] replaced without dated amendment: not met; [D25] must also be logged in `decisions.md` (#14).
- outward mismatch: not applicable.

## Disputed facts for the investigator

None. Physics B3 settled on code (above). The FP32 runner path is a question for ml-engineer only if Kai takes #12.

## Dismissals

None.

## Motivated-reasoning check

- The budget claim and the A − NB claim both default to the thesis-favourable wording when the
  data are weak ("supported" at ≈ 21 %, "not falsified" at 3.7 pt). #4, #6, #8 fix the wording so
  the weak outcome reads as weak. Nothing inflates an interval; pairing is used where arms pair.
- "The staged code answers it" was checked, not taken on trust (#3 yes for A family, #2 no for H).

## Verdict

**ITERATE** (STUDY panel, iteration 4 → fixer, then re-review v5). No A. Nine open B (#1, #2, #4-#12
as merged below), all text-only: none needs a regenerated config, a new trace or a Kai decision.
There is no PASS-with-conditions in `06-review.md`: PASS requires no unresolved B, and §6.5 calls
fix → advance without a re-review a process failure. Recommended v5: a diff-scoped panel pass
(reviewers check the listed edits; a new B only if it changes a number, a claim or the design).
**Warning: a fifth iteration is the strong-warn tier.** PREFLIGHT work that does not depend on
STUDY text (patch 0024, CPU gates) may continue meanwhile; nothing ships.

Required fixes, in priority order (fixer; experiment-designer if CANNOT RESOLVE):

1. **(#1) Certification failure.** Selection rule l. 566-572: "A mismatch blocks VERIFY for that
   arm until ml-engineer resolves it without reselecting; if unresolved, the seed counts as 'no
   accuracy number' in k and both EBOPs values are reported per seed. Certification uses the same
   `ebops_trace_sample` and `ebops_trace_batch` as the per-epoch trace."
2. **(#2) H.** l. 396-401 and [A23] l. 1398-1406: H's validation accuracy, macro AUC and test (c)
   are computed on the reloaded traced clone; H's BetaPID reads the clone's traced EBOPs, with
   the same per-epoch assertion as `ablation.py:698-703`; [A23] adds a CPU unit test that logged
   validation accuracy equals a fresh-load prediction of the saved clone and that the PID EBOPs
   equals the clone trace.
3. **(#4) Budget-claim demotion.** Keep the 6-of-8 count rule. Reword "supported" (l. 632-640,
   and l. 119-121) as "k/8 A seeds reached 350k above the 0-bit floor and above chance
   (threshold (c) printed, about 0.21 on the gated `y_val`)"; print each feasible seed's
   validation accuracy beside the count; add "non-degenerate means not a constant classifier; it
   does not mean the model tags well". Same sentence at the pilot A rule (l. 884). No new floor.
4. **(#5) Attribution.** At l. 351, 656, 1433 replace with "the 2-head E architecture under [D19]
   (any weight type, including NB and Sun et al.'s `xfm`) reaches 350k only because the Q·K and
   A·V streams may prune to 0 bits"; note A − NB is unaffected (shared floor).
5. **(#10) Figures** (l. 758-776): (i) per-seed A accuracies, mean and 95 % t-interval (k in
   legend), lines at 79.4 / 78.4 / 79.8 / 77.9, caption "ROC-test, n = 260,000, external
   references single-model"; (ii) paired-gap panel A − D, D − R, A − R, A1000 − R, D1000 − R with
   n_pairs and GPU-class note.
6. **(#8) A − NB headline** (l. 708-717): lead with the lower 95 % bound ("binary costs at most
   |L| pt against learned-width weights, n pairs, 95 %, iso-EBOPs"), "not falsified" beneath;
   one sentence of prior (Sloot, FastML 2026, research-log 2026-09-01: HGQ above binary on a
   different task; expected A ≤ NB; a wide interval is not support).
7. **(#9) Wave-2 epoch-500 rule** (l. 1006-1009): if no NB (resp. H) seed has a feasible,
   non-degenerate checkpoint by epoch 500, that arm goes to Kai (continue / H open-loop / stop);
   nothing else decided on it.
8. **(#6, #7) Wave-2 resolution.** Pre-register an epoch-500 readout of the paired A − NB
   validation sd_diff with [D13]'s Kai options, triggered at sd_diff > 1.2 pt; state in the
   Falsifier the smallest A − NB resolvable at the measured sd_diff (printed at REPORT); add
   constructive B1's formula (smallest n with t(0.975, n−1)/√n · sd_diff ≤ 1.0 pt, from the
   wave-1 epoch-1,000 A − D paired sd, a floor not a guarantee) and its table as the input to a
   new Kai row "extra A/NB pairs (cap)". Default stays 8 pairs.
9. **(#11) Stability.** Beside the divergence count (l. 688-692) report per arm the
   feasible-degenerate count and a low-accuracy-outlier count, defined now: a seed whose
   selected-checkpoint validation accuracy is more than 3 pt below its arm's seed median
   (descriptive, not in the decision rule); say that the count rule sees only non-finite failures.
10. **(#12, #23) Scope and FP32.** One-line scope statement in "Bearing on the thesis" (no FP32 /
    W8A8 baseline, no activation ladder); Kai row "FP32 E arm (8 seeds; cheap 4 × 2,000 epochs),
    runner path for `quant.weight: none` to be confirmed by ml-engineer", not a default.
11. **(#13) Kai row** for NB in wave-1 seed blocks conditional on the canary's K=7 memory reading.
12. **C items #3, #14-#28**, apply now. [D25] conditional: if patch 0024 is in `code/patches/`
    and `chang0926-a-n64-s1.json` carries `quant.i_decay_speed` when the fixer runs, l. 284 and
    l. 1358 stand; otherwise reword both as the [A21] PREFLIGHT gate. Either way log [D25] in
    `decisions.md`. Update l. 1162-1164 and 1360 to cite `ablation.py:698-703`.

Kai options (not required fixes): extra wave-2 pairs (#7), the FP32 E arm (#12), NB in wave-1
blocks (#13).
