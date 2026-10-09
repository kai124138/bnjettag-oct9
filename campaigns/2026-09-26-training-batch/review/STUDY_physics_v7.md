# STUDY physics review v7: 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context; read only the artifact, the files it cites, and the
paper PDF). Phase: STUDY. No results exist, so the checks apply to the plan: arms, seeds,
intervals, planned figures.

## Figures

There is no compiled PDF beside `STUDY.md` and no PNG is cited, so no figure exists yet.
Each pre-registered figure (STUDY.md l. 1124-1159) was checked as a plan against the figure
checklist:

| figure (planned) | status |
| --- | --- |
| Primary measurement: per-seed A ROC-test accuracy, seed mean, 95 % t-interval, k in legend, lines at 79.4 / 78.4 / 79.8 / 77.9 | plan OK: split and n in caption; external lines labelled single-model |
| Recipe ladder: paired-gap panel A − D, D − R, A − R, A1000 − R, D1000 − R | plan OK: paired Δ with t-interval and n_pairs, GPU class in caption (see C2 on epoch vs step matching) |
| Per-class ROC, ROC-test, log mistag axis, seed band | plan OK: log mistag axis; band stated as sd ddof = 1 with seed count; budgets split into separate panels |
| Per-run selected epoch, cycle index, best-feasible val accuracy per cycle | plan OK: labelled validation, n = 62,000 |
| Accuracy vs EBOPs ladders (E: B, A; A07: A07-350, C) with paired-gap panels | plan OK: EBOPs above the 0-bit floor on rungs; empty-marker rule for 0/8 |
| Attention state per arm (Q/K, V at 0 bits, entropy / log 64) | plan OK |
| Validation − held-out per run | plan OK |
| Interim-readout figures | plan OK: labelled validation |
| Second wave: A − NB paired panel; H − NB, H − A Welch; FP32-E package panel kept separate; per-class ROC with A, NB, H, FP32-E | plan **incomplete**: no per-class paired AUC gap for A − NB or A − FP32-E (the "optional C items ... not applied", l. 241-242). A macro or accuracy gap can hide one collapsed class. Carried into B5 |

## Verified in this review

- Round-14 N=64 sizing numbers (reference table, l. 350). Recomputed from
  `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz` (`y`, `score` shape (260000, 5)).
  W1A8 top-1 accuracy is 67.18 / 72.64 / 67.21 %, mean 69.01, sd 3.145 with ddof = 1 (2.568 with
  ddof = 0, so the artifact uses the right sd). FP32 is 79.42 / 78.83 / 79.10 %, 79.11 ± 0.297.
  `y` is byte-equal across seeds. Matches the artifact.
- Threshold (c) is "about 0.21" (l. 883-887). ROC-test class fractions are
  0.2016 / 0.1941 / 0.2009 / 0.2011 / 0.2023, so p_maj + 5·√(p(1−p)/62,000) = 0.2104. Matches.
- Static floors (`code/evidence/static_floors_fix6_a07_e_e1.json`): A07 zero / one / narrow /
  full = 343,053 / 1,005,741 / 605,197 / 801,805, headroom 6,947. E = 171,526 / 619,198 /
  368,134 / 478,726, headroom 178,474. E1 = 85,763 / 533,435 / 282,371 / 392,963. All match.
  E's whole 0-bit floor is the one term `bit_block_0_attn_softmax` (171,526), so the "softmax
  tax" (l. 302, 905) is exactly the floor. The 1-bit per-channel costs in E are input_proj
  4,608 / 3 = 1,536 and Wk 36,864 / 24 = 1,536, which gives the minimal attention path
  1,536 + 1,536 + 4,096 = 7,168 (l. 288).
- `cpu_gate_d25.log:119` `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`, and every A
  config has `zero_floor 171526`, `I_DECAY_OK ... 0.001`. Matches l. 110-114.
- Paper (pdftotext of the cited PDF): Table 1 lists MHA-64 77.9, Linformer-64 79.8 and Deep Sets
  (HGQ)-64 79.4; 620,000 train and 260,000 test (§3); PID over β; attention "constrained to at
  least one bit", stated in the text next to Fig. 3 (weight bitwidths). Matches the reference
  table.
- REPRO-CHANG 80.56 % at 348k and 80.85 % at 318k (`_attic/repro-chang/repro-chang/comparison.md`):
  matches, including "selected on max test accuracy".
- Arithmetic re-derived: 0.836·sd and 1.05·sd half-widths; the sizing table 1.196 / 1.574 /
  1.877 / 2.011 / 2.137 pt (printed rounded down); H − NB Welch 1.07·sd, i.e. 3.4 pt; paired
  3.7 pt at zero correlation; winner's-curse SE 0.16 pt; McNemar two-sided 4-0 p = 0.125; W&B
  versions 13,760; cheap version 1/21. All correct.
- Not verified by this review (outside the files I may read): the Sloot prior (0.9276 vs
  0.9178, `research-log.md`), and every `decisions.md` citation for Kai's answers.

## Findings

### (A) Must resolve

None for the wave-1 plan. The statistics are sound: sample sd with ddof = 1 and the seed count;
paired t with df = n − 1 and a sign count; Welch where pairing is not established; every gap
has an interval; per-class AUCs sit beside the macro; resolving power is stated at both sd
bounds, with "flat" defined as "cannot resolve below about 3-4 pt". Selection and evaluation
use separate splits, and ROC-test is touched only after the terminal epoch.

### (B) Should address

**B1. Holm family size under dropouts is not specified. This decides whether wave 2 can be
approved.** The first-wave secondary family {C − A07-350, A − B, A − D, A − F} says "a rung
with fewer than 6 is reported as counts only" (l. 962). The second-wave family
{A − NB, H − NB, A − FP32-E} has three ways to lose a member: NB below 6 feasible (l. 1041),
H below 6 (l. 1090-1092), and A − FP32-E "counts only" (l. 1075) or withheld by the
plausibility gate (l. 1079-1081). No sentence says what m is in any of these cases. The
adjusted p of A − NB, the one thesis-bearing test, depends on m (α/3 vs α/2 on the first step,
l. 975-978). The attack is that once any wave-2 number exists, choosing m becomes a post-hoc
selection. What would settle it: one dated sentence per family, written before the wave-2
canary, fixing m in each dropout case. For example: "a member with no gap leaves the family and
m falls by one", or "m stays 3 and the missing member counts as p = 1".

**B2. The FP32-E plausibility gate depends on the result, compares across splits, and has no
exit criterion** (l. 1079-1083). The rule is: if FP32-E's seed-mean *validation* accuracy is
"below A's, or below 79.4 %", A − FP32-E is not reported until the cause is "found or ruled
out". The 79.4 % clause compares a winner's-curse-inflated validation mean (n = 62,000, max
over 7,000 checkpoints) with a ROC-test number from another pipeline. This project's own FP32
at N=64 sits below that line: 79.11 ± 0.30 % recomputed above (different architecture,
ungated, archived). An honest FP32-E with 6,253 trainable parameters could trip the gate, and
the open-ended "ruled out" wording then leaves the package gap unreported, which also feeds
into B1. What would settle it: keep "below A's" as the pipeline check, since an unconstrained
FP32 model losing to binary at 350k is a real warning sign. Drop the 79.4 % clause, or change
it to "investigate and report with a label". Pre-register what closes the investigation, for
example the checks already listed at l. 1056-1057.

**B3. The bearing on the thesis leaves out that the comparand is already DSP-free.** Table 1 of
arXiv:2510.24784 (pdftotext l. 253-261) gives DSP = 0 for every HGQ row, including the 79.4 %
Deep Sets comparand, MHA-64 and Linformer-64. The artifact quotes the accuracy column only. The
thesis's distinguishing claim ("binary maps to LUT, essentially no DSP") is already met by
learned-width HGQ at 350k in published synthesis. A − NB therefore most likely compares two
DSP-free designs, and any hardware advantage of binary would have to show in LUT or latency,
which this campaign does not measure ([L7]), or in accuracy at iso-EBOPs, where the stated prior
is A ≤ NB. What would settle it: one paragraph in "Bearing on the thesis" stating this. REPORT
should then not read a small A − NB as support for the DSP claim.

**B4. The budget claim can almost only fail through a controller or pipeline failure.** It
counts as a pass when k ≥ 6 seeds have EBOPs ≤ 350k, EBOPs above the floor, and validation
accuracy > 0.2104 (verified above). With 178,474 EBOPs of headroom, 7,000 epochs, a PID
without stop-on-target and a "≤ target" filter, a trained model fails this only by divergence,
by a PID that never lands, or by staying at chance. The artifact says honestly that
"non-degenerate ... does not mean the model tags well" (l. 261, 885), but the claim still sits
among the three pass/fail claims. Following the suspicious-agreement check: what failure other
than a bug would this claim catch? If none, the claim text should say so ("a pass is expected by
construction; the claim screens for controller and training failure"). A stronger alternative is
to put a meaningful accuracy line into the claim before the pilot readout, for example a
per-seed validation accuracy stated in advance.

**B5. The metrics that bear on the thesis are not pre-registered as paired gaps.** The thesis
concerns tagging efficiency. The primary metric is top-1 accuracy, justified for the 79.4 %
replication. For the two thesis-bearing comparisons (A − NB, A − FP32-E), macro AUC and the
five per-class AUCs "sit beside" as values (l. 1487), not as paired gaps with t-intervals. The
only operating point at trigger level is rejection at signal efficiency 0.5, and an L1 trigger
works at far lower mistag. A binary-only collapse in one class (q or Z were the weakest classes
in the R14 binary arm: per-class seed means 0.892 / 0.892 recomputed above) could hide behind
the accuracy gap. What would settle it: pre-register, for A − NB and A − FP32-E, the paired
macro-AUC gap and the five per-class AUC gaps (each a t-interval over pairs, outside the Holm
family, descriptive), plus signal efficiency at a fixed low mistag (for example 1e-2 on the log
axis already planned). Add the matching per-class panel to the second-wave figure.

**B6. At the likely spread, A − NB will probably not resolve a cost of "modest" size, and the
remedy is left open.** At zero pair correlation and the archived spread the paired
resolution is about 3.7 pt (l. 725). The sizing rule is sound: it is blinded, reads sd_diff
only, never the mean, and uses a formula stated in advance. But its cap ("extra A/NB pairs
(cap)", l. 2019) is open. If the cap stays at 8, the thesis-bearing outcome most likely reads
"not falsified at this resolution", which says nothing about a 1-pt cost. What would settle it:
Kai sets the cap before the wave-2 canary, and the STUDY states the smallest A − NB gap
resolvable at that cap under the proxy.

### (C) Suggestions

- **C1.** The FP32-E plausibility line prints the archived, ungated, 80/20 FP32 79.1 ± 0.3 %
  beside FP32-E (l. 1082-1083). That contradicts the artifact's own rule at l. 1493 ("no number
  here sits beside Round 14") and [L6]. Drop it, or move it to the Seeds sizing text where it
  already lives.
- **C2.** A1000 − R and D1000 − R are "epoch-matched" (l. 413-416, 938) but not step-matched:
  200 steps per epoch at batch 2,790 against about 2,180 at 256 (l. 1172-1173), so R takes about
  11× more optimizer steps by epoch 1,000. Print the step counts beside these gaps so that
  "more epochs" is not read as "more updates".
- **C3.** l. 500 calls "E1 × 2 = E" for the softmax term "the independent prediction that held".
  HGQ2's softmax EBOPs are linear in H at fixed T and S, so this is close to an identity of the
  counter. Call it a consistency check.
- **C4.** "Worst-case imputation" (l. 996, 1066) imputes failed A seeds at the surviving
  minimum, not at chance. Call it "minimum-survivor imputation". The worst case is p_maj.
- **C5.** The pairing logic differs between arms. R is paired "by seed index" although its data
  order differs (l. 410), while F, NB and FP32-E fall back to Welch for all seeds if the init
  hashes differ. Pairing by a seed index fixed in advance is valid in either case. Pick one
  logic and state it once.
- **C6.** l. 1398 says the gate reads "58 and 56 now", but the shipped-tree gate
  `code/evidence/cpu_gate_shipped_77f1ca4e.log:55` reads `PREFLIGHT_ALL_PASS 26 production 24
  pilot_only 2` (A, D, A07-350 × 8; C′, E1). This is a PREFLIGHT matter. The STUDY sentence
  should say which bundle each count refers to, so that B, C, F and R are not assumed gated.
- **C7.** The binary per-tensor absmean scale is outside native EBOPs ([L2]). For the DSP
  thesis, note that a per-kernel float scale is one multiplier per layer in hardware unless it
  is folded. This matters for REPORT wording, not for this campaign's numbers.

## Verdict

I would approve this STUDY for the pilot and wave-1 production. The plan yields correct numbers
with honest, labelled uncertainty. The wave-2 launch should wait for B1 (Holm family size under
dropouts, fixed and dated before any wave-2 number exists), with B2 close behind, because A − NB
is the only comparison here that bears on the thesis.
