# STUDY physics review v5: 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context; read only the artifact, its `code/evidence/` files and
the patches listing it cites). Artifact: `campaigns/2026-09-26-training-batch/STUDY.md` (1,800
lines, mtime 2026-09-27 09:51). Phase: STUDY, so this is a review of the plan. No results exist yet.

## Figures

No figure is rendered at STUDY, and no compiled PDF sits beside the artifact. The pre-registered
figures (STUDY l.869-899) are checked here as specifications against the mandatory list.

| figure (planned) | status |
| --- | --- |
| Primary measurement: per-seed A ROC-test accuracy, seed mean, 95 % t-interval, k in legend, lines at 79.4 / 78.4 / 79.8 / 77.9, caption "ROC-test, n = 260,000, external references single-model" | planned, not rendered; spec OK |
| Recipe ladder: paired-gap panel A − D, D − R, A − R, A1000 − R, D1000 − R with t-interval and n_pairs, GPU class in caption | planned; spec OK (paired, not unpaired bars) |
| Per-class ROC on ROC-test, **log mistag axis**, seed band sd (ddof = 1) with seed count, A and R named; A07-350 and C in a separate panel with EBOPs above floor | planned; spec OK (split, n, log axis, budgets not mixed) |
| Per-run selected epoch, cycle index, best-feasible validation accuracy per cycle, "validation, n = 62,000" | planned; spec OK |
| Two accuracy-vs-EBOPs ladders (E: B, A; A07: A07-350, C), paired-gap panels beneath, empty marker for 0/8 rungs | planned; spec OK |
| Attention state per arm (Q/K and V fraction at 0 bits, entropy / log 64), A07-350 expectation marked | planned; see finding B1 (the expectation as worded can mark a correct checkpoint as a mismatch) |
| Validation − held-out accuracy per run (winner's curse) | planned; spec OK |
| Interim-readout figures, "validation, n = 62,000" | planned; spec OK |
| Second wave: A − NB paired-gap panel with 1.0-pt line, H − NB and H − A Welch intervals; per-class ROC A/NB/H; NB weight-width distribution | planned; spec OK |

Per-class AUCs beside the macro average are required (l.1156, l.1230), and per-class AUC < 0.7 is
called out (l.1160). No figure findings.

## What I verified (numbers recomputed or read from the cited files)

- Archived N=64 W1A8 spread: from 67.18 / 72.64 / 67.21 % I get mean 69.01 %, sample sd (ddof = 1)
  3.144 pt; the artifact's 3.14 pt matches (l.234).
- 0.836 = t(0.975, 7)/√8 = 2.365/2.828; 1.05 at k = 6; Welch H − NB half-width t(0.975, ≈14)·√(2/8)
  = 1.07·sd, 3.4 pt at 3.14; paired zero-correlation 0.836·√2·3.14 = 3.7 pt; ±0.5 pt needs sd ≤ 0.60
  (8 seeds) / 0.48 (k = 6). All correct.
- McNemar exact two-sided: 4-0 0.125, 5-0 0.0625, 6-0 0.031, 7-0 0.016. Correct.
- Validation SE at p = 0.79: 0.16 pt at n = 62,000, 0.12 pt at 124,000. Correct.
- Budget arithmetic: 7,000 × 112.6 s = 9.12 d; 7,000 × 172.8 s = 14.0 d; 1.66 × 112.6 s = 187 s gives
  15.1 d; 8 pods × 9.1 d ≈ 1,750 pod-hours; 4 × 218.9 h ≈ 876. Correct.
- Floors: `code/evidence/static_floors_arms_s1.json` and `static_floors_arms_s1_d25.json` give 0-bit
  floors E 171,526 (A, B, D, F, R), A07 343,053 (C, A07-350), E1 85,763, C′ 4,580,398; 1-bit-alive
  E 619,198, A07 1,005,741; narrow / full attention readings E 368,134 / 478,726, A07 605,197 /
  801,805, E1 282,371 / 392,963. Every field is identical before and after [D25] (0 differing
  numeric fields per arm), so "no effect on the static floors" is checked, not assumed.
- Minimal attention path: `one.per_layer` gives E `input_proj` 4,608 / 3 = 1,536 per input channel,
  `Wk` 36,864 / 24 = 1,536, `scores` 98,304 / (2 heads × 12) = 4,096 per (head, key-channel) pair;
  A07 6,144 / 3 = 2,048, 65,536 / 32 = 2,048, 131,072 / (4 × 8) = 4,096. So 7,168 (E) and 8,192
  (A07) against 6,947 A07 headroom hold.
- Pairing: `a17_pairing_d25_8seeds.json` has A, B, D and R paired with F at all 8 seeds, only
  `pos_enc/pos_table` differing, 0 of 15 shared variables differing, no UNPAIRED entry.
- CPU gate: `cpu_gate_d25.log` ends `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`, and every
  [D19] config reports `I_DECAY_OK ... 0.001 quantizers 14`.

## Findings

### (A) must resolve

None. The plan pre-registers selection on validation only, keeps ROC-test untouched until the
terminal epoch, gives every gap a seed-paired t-interval with df = k − 1 and a sign count, uses
ddof = 1, states the survivor bias, states the resolving power at both sd bounds, and labels every
number with metric, split, n and status.

### (B) should address

**B1. The A07-350 pre-registered expectation can flag a correct checkpoint as a defect.**
Attack: l.711-712 expects "at most three 1-bit `input_proj` or d32 dense input channels in total",
and l.713-714 and l.1018-1019 send a mismatch to ml-engineer as a floor-accounting defect.
Evidence: in `static_floors_arms_s1_d25.json` (`chang0926-a07-350-n64-s1`, `one.per_layer`),
`head_fc1` costs 1,024 for 32 channels, **32 EBOPs per input channel** after the pool, against
2,048 per channel for the per-constituent layers. A checkpoint with 3 `input_proj` bits (6,144)
and up to 25 live `head_fc1` channels (800) fits in the 6,947 headroom. That checkpoint is exactly
what the floor predicts, but "d32 dense input channels in total" read literally includes the head,
so the report would call it a mismatch. This is the plan's only pre-registered defect trigger, so
it should not be able to fire on a correct result.
Settle: restrict the expectation to the per-constituent layers (`input_proj`, Wq, Wk, Wv, Wo,
ffn_fc1, ffn_fc2): at most 3 input bits in total there. State the post-pool head separately (up to
about 25 channels at 1 bit, or fewer at more bits). The same wording is in the Question (l.179) and
[D21] (l.1310).

**B2. As designed, the campaign produces no evidence on the thesis's first axis.**
Attack: the thesis claims efficiency "close to full precision" against FP32 and 8-bit baselines.
Neither wave has an FP32 or W8A8 arm. The only weight-type gap is A − NB, which is iso-EBOPs
against learned-width weights, and the artifact itself says it is "not the thesis's 'close to full
precision' gap" (l.207-209). The FP32 E arm is a Kai option that "blocks nothing" (l.1630).
The artifact is honest about this (l.191-214), so the finding is about how the result will be
used, not a misstatement.
Settle: either promote the FP32 E arm (the cheap 4-seed × 2,000-epoch version is enough for a
labelled package gap), or pre-register now that REPORT may not cite this campaign as evidence for
"close to full precision". The FP32 row should block any REPORT sentence that refers to the thesis.
It does not need to block STUDY.

**B3. The sd_diff proxy used to size A − NB comes from a different comparison.**
Attack: the number of A/NB pairs is sized from the epoch-1,000 paired sd of A − D (l.797-799).
A − D changes the optimizer on otherwise identical binary models. A − NB changes the weight
quantizer, and NB starts at a higher init EBOPs, can prune weights to 0 bits and follows a
different PID trajectory ([A22], l.1528-1529). Same-seed A/NB trajectories probably decorrelate
more than A/D, so the proxy probably understates sd_diff and undersizes the pairs.
Settle: state the expected direction of the proxy bias next to the table ("probably understates").
Make the second-wave epoch-500 A − NB sd_diff readout (l.1139-1140) the binding input to the "extra
A/NB pairs (cap)" row, with A − D as the prior only.

### (C) suggestions

**C1. Stale text against the tree.** (a) l.233 cites `code/evidence/cpu_gate_final.json`, which
does not exist in `code/evidence/`. The parameter counts (61,951 / 11,653) are in
`cpu_gate_d21.log` and `cpu_gate_d25.log`; repoint the citation. (b) l.134, l.326-327, l.1340 and
l.1500 say patch 0024 / [D25] is "not yet in code" and that the staged tree has 0.01. But
`code/patches/0024-D25-...patch`, `cpu_gate_d25.{json,log}`, `a17_pairing_d25_8seeds.json`,
`regression_*_d25.json` and `static_floors_arms_s1_d25.json` all exist (09:50, one minute before
the STUDY). (c) l.1396-1398 says `static_floors_arms_s1.json` still has B as A07 at 175k and A, D,
F, R as A07, but the file holds the [D21] set (B is E at 250k, A/D/R are E, F is E with learned
PE). The gates are done and the text says they are not; a referee who opens the files will then
distrust the rest of the text.

**C2. The C′ `i_decay_speed` assertion has nothing to check.** `cpu_gate_d25.log`:
`I_DECAY_OK chang0926-cprime-n64-s1 config None quantizers 0 values []`. [A21] (l.1502) and the
fidelity row (l.327) say PREFLIGHT "asserts 0.01 on C′". The SAT path carries no quantizer with
`_i_decay_speed`, so there is no value to assert. Reword to "C′ carries no `i_decay_speed`
quantizers (SAT path); not applicable".

**C3. Sizing-table rounding.** 0.8360 × 1.20 = 1.003 pt, so the "≤ 1.20 pt → 8 pairs" row fails
the ≤ 1.0 pt criterion it defines. The 16-pair row does the same: 0.5328 × 1.88 = 1.002. Exact
thresholds: 1.196 (8), 1.574 (12), 1.877 (16), 2.011 (18), 2.137 (20). Give three figures or mark
the values "≈". The same applies to "sd_diff ≤ 1.20 pt" in Seeds (l.554) and at l.1799.

**C4. Threshold (c) excludes only constant classifiers; it says nothing about tagging quality.**
At about 0.21, the budget claim can be "not falsified" by seeds at 25-35 % accuracy, and those
seeds enter the arm mean. The artifact says so (l.704). The only descriptive separation is the
low-accuracy-outlier count (3 pt below the arm median, l.765-767), which is relative, so an arm
where every seed is weak shows no outliers. Suggest reporting, beside the seed mean, the per-seed
accuracies sorted and the count of seeds above a fixed absolute line (for example 70 %), labelled
descriptive and set now.

**C5. Certification checks reproducibility, not the cost accounting.** The retrace uses the same
code, the same split, the same `ebops_trace_sample` and the same batch as selection (l.619-629).
It catches nondeterminism and serialization faults. It cannot catch an accounting error that both
passes share. The independent check, [A14] against HGQ2's own counter, runs on a REPRO-CHANG
checkpoint, not on an arm checkpoint. Suggest also running [A14] (or the frozen-range
zero/random-input agreement, l.1164) on the selected A-s1 checkpoint at VERIFY.

**C6. Headline conditional.** "binary costs at most |L| pt" (l.788) reads correctly only when
L < 0. If L ≥ 0 the sentence should read "no cost resolved; lower bound +L pt". Pre-register both
forms.

**C7. Binary latent weights under LR 3e-3 without weight decay (arm A).** `binary_absmean` with
Adam defaults at 3e-3, restarting 14 times, no latent clip or decay, on a norm-free block, can
either freeze the signs (latent magnitudes grow) or churn them at every restart. Neither shows as a
non-finite loss, and the 10-epoch canary cannot see either. D is the control and the epoch-500
pilot reads it. Suggest logging the per-epoch sign-flip fraction and the latent |w| percentiles for
A and D (cheap, descriptive), so that a stalled-A outcome can be told apart from a recipe effect.

## Method health and statistics, summary

- Arms are matched: the same cache, split, gate, standardization, quantizer [D19], PID, trace [D20],
  seeds and order across A/B/D/F/R. Init is shared, verified at 8 seeds for F. R crosses GPU class
  and batch order, and is labelled a package.
- Baselines: no FP32 or W8A8 (B2). The 79.4 % reference is single-model and non-binding, and it is
  treated as such ([L1]).
- Metric: accuracy for both selection and the primary, AUC as tie-break and sensitivity. This is a
  flagged deviation, consistent end to end.
- Tautology: the PID holds EBOPs at the target by construction, and the artifact reports
  feasibility as a count, not as an achievement (l.653-656). Certification is a determinism check
  (C5).
- Resolving power: stated honestly. At the archived sd a "flat" result means "cannot resolve below
  about 3-4 pt", and the 78.4 % line is stated as unresolvable at that spread.
- Suspicious agreement: none possible yet. The only perfect agreements (arbiter sums against the
  traced totals, and E1 × 2 = E) are labelled as identities or as scaling consequences, not as
  independent checks.

## Verdict

I would approve this STUDY for launch to PREFLIGHT once B1 is reworded. It is the most decisive
item because the plan's only pre-registered defect trigger, the A07-350 attention-state
expectation, can currently fire on a checkpoint that matches the floor exactly.
