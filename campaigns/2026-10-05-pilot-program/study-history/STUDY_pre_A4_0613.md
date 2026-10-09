---
id: 2026-10-05-pilot-program
date: 2026-10-05
type: pilot-program
status: draft, amended [A3] pre-data (STUDY panel v1 ITERATE; not frozen)
question: Why does the binary-weight N=64 E transformer (d24, 2 heads) collapse at 350k EBOPs while A07 (d32, 4 heads) stays healthy at 5M, does health follow budget headroom, and which budget and fix are production candidates for A and NB?
code_sha: one training-code tree for R1-R3 (option-(c) tree + 0034-0041; [A3] rule in §7); R1 bundle sha assigned at PREFLIGHT
wandb: BNJetTag-ChangRecipe / group per round (filled at PREFLIGHT)
---

Owner: experiment-designer. Approved program: `docs/PILOT_PROGRAM.md`, `.claude/memory/decisions.md`
(2026-10-05 10:08 JST). This document is written before any pilot of the program exists.
Rule changes after an R1 number exists are dated amendments signed by Kai and labelled post hoc.
**Pilots are directional.** They choose what to run next and which production candidate to put to
Kai. No pilot number is a result, enters `verify.json` or appears in outward text.

**Amendment 2026-10-05 10:46 JST, pre-data (orchestrator).** NB (0036) and the attention bit floor
(0037) join R1 as 4 arms; R2 = recovery bracket + 3 seeds of the most promising 350k variant; R3 =
NB@r_rec when needed; D4 = q,k,v at 1 bit. Earlier text: `study-history/STUDY_v0.md` (sha `a2f4877a…0c4`).

**Amendment [A2] 2026-10-05 14:14 JST, pre-data (`review/PREFLIGHT_critical_v1.md` B4-B6, C1, C4,
C5).** Entropy-only failure stops for Kai (§5, §10); w150 time-limited reading (§6 H4, D3); H2
beyond the ladder (§6); `campaign.production: true` in configs is harmless, tooling reads
production status from `index.json` and `BNJ_STAGE` only (`pilot1005/cpu_gate.py:171`,
`chang0926/evaluate_roc.py:144`), and regenerated configs set it false; NB init EBOPs note (§6 H5).
Text before [A2]: `study-history/STUDY_pre_A2_1046.md` (sha `aebef3f0…536`).

**Amendment [A3] 2026-10-05 14:35 JST, pre-data (experiment-designer; `review/STUDY_arbiter_v1.md`
fix F6, from `review/STUDY_{physics,critical,constructive}_v1.md`).** No pilot data exists: R1 is
not launched, and only the b3fb22 CPU gate is running. Text before [A3]:
`study-history/STUDY_pre_A3_1430.md` (sha `b3c6bc8d…0369`; the panel read `27d43c63…0e86`, and the
14:27 difference is the §4 arm-id alignment, PREFLIGHT C2). Changes, marked `[A3]` below:
- (a) §7, §12: R2/R3 bundles keep R1's training-code tree byte-equal; their configs are built and
  gated before the R1 readout exists.
- (b) §7, §9: NB production = V_bin's configuration with only the weights changed; P350 only when
  V_bin = A350-C; H5 at R2 = NB350-C vs A350-C at matched seeds.
- (c) §9: a candidate qualifies only with ≥ 3 healthy seeds per production arm not used to choose
  it.
- (d) §9: nothing auto-fires; Kai decides every production launch (Prec included). The 0.50 floor
  is internal; the external reference is stated. Production early stop at epoch 500.
- (e) §4, §11: A07-350k-C → A350-C-qkv1-450k (matched-headroom H3); + E-unc-C (E positive control
  and entropy reference); R1 = 24 pods, 144 GPU-h; w150 kept, Kai may switch to w100 (D3).
- (f) §2, §5, §6, §11, §12: text fixes from the three reviews (list in the review files; each is
  marked in place).
- (g) §15: deferred items with costs.

## 1. Question, null, bearing

**Question.** Every collapsed pilot is the E family (d24, 2 heads, 1 block) at 350k EBOPs (uniform
attention, degenerate or weak checkpoints); the only healthy one is A07 (d32, 4 heads) at 5M. Does
health follow budget headroom within E (the E ladder) and across architectures (the A07 ladder),
which single 350k fix helps, and which budget and variant are production candidates?
**Null.** No single tested factor (controller input, budget headroom, attention width, squeeze
timing, binary weights) changes health at 350k.
**Bearing.** Every paper tier needs A − NB at 8 paired seeds (`docs/ROADMAP.md` §5). This program
qualifies a production candidate by a rule fixed here; Kai decides the launch (§9).

Prior state. Every number below is a single seed on validation (n = 62,000), pilot telemetry,
and never quoted. At 350k every head is at entropy/log 64 = 1.000000 (b5 `VERIFY.md` §6;
`READOUT_epoch500.md` table (2)). A-s1 is degenerate, and the A-s2 and D-s1 best checkpoints
are weak (0.320871 and 0.405371). C-s1 (A07, 5M) has heads 0.622127, 0.913695, 0.543640 and
0.880046, with val acc 0.664726, on its `model_best` at zero-based epoch 19, 4,880,224 EBOPs
(READOUT:122). These come from the 42abed code, without option (c), on A10.

`[A3]` Related work (phys C3): attention degradation in binarized transformers is documented
(BiBERT, BinaryBERT, BiT, Q-ViT); the collapse here is different, 0-bit Q/K *activations* priced
out by an EBOPs controller. EBOPs-matched is not resource-matched (1-bit weights map to LUT logic);
no DSP or LUT claim rests on this program (phys C4).

## 2. Hypotheses and predictions

Static floors, from a synthetic CPU trace, not a result
(`campaigns/2026-10-02-chang-option-c/code/tree/campaigns/chang1002c/static_floors.json`):

| arch | params | 0-bit floor | ≥1-bit attention, narrow | full (+ Wq/Wk/Wv inputs) | all activations 1-bit (`one`) |
| --- | --- | --- | --- | --- | --- |
| E (d24, 2 heads) | 31,735 | 171,526 | 368,134 | 478,726 | 619,198 |
| A07 (d32, 4 heads) | 61,951 | 343,053 | 605,197 | 801,805 | 1,005,741 |

Headroom (budget − 0-bit floor). E: 250k 78,474; 350k 178,474; 500k 328,474; 750k 578,474;
1M 828,474; 2M 1,828,474; 5M 4,828,474. A07: 500k 156,947; 1M 656,947; 2M 1,656,947; 5M 4,656,947.
`[A3]` qkv1 (zero floor 269,830, `dev/README.md`): 350k 80,170; 450k 180,170 (≈ A350-C's 178,474).
(Arithmetic on the floors.) `[A3]` The variable is **absolute** headroom in EBOPs (phys B2): the
controller prices bits in EBOPs, not per site; A07 has about twice the parameters, so a per-site
scaling would predict a higher A07 rung. That scaling is not tested.

| # | hypothesis | prediction if true | prediction if false |
| --- | --- | --- | --- |
| H1 | The controller's input error causes the collapse | A@350k with (c) is healthy; without (c) it is not | (c) is unhealthy on both seeds |
| H2 | The fixed binary floor leaves too little headroom | health is monotone up each ladder; A07 recovers at the smallest A07 rung whose headroom ≥ E's at its recovery rung (E 250k→A07 500k; 350k, 500k or 750k→1M; 1M→2M; 2M→5M; 5M→beyond the ladder) | no E rung healthy (E-unc healthy), or A07 ≥ 2 rungs from the prediction |
| H2′ `[A3]` | Whole-network starvation: every activation needs ≥ 1 bit | first healthy rung ≥ `one`: E 750k, A07 2M | E healthy below 619,198 or A07 below 1,005,741 |
| H3 | Attention is starved first (Q/K/V go to 0 bits) | a 1-bit Q/K/V floor makes A healthy where it is otherwise not; static corollary: E transition at 500k (first rung ≥ 368,134), A07 at 1M (≥ 605,197) | `[A3]` the floored arm at matched headroom (qkv1-450k) is unhealthy while A350-C is too |
| H4 | The squeeze comes too early | a PID warmup of 50 or 150 is healthy where warmup 1 is not | both warmups do worse than warmup 1, while reaching the budget |
| H5 `[A3]` | Binary weights cause it; tested with **learned-width (prunable) weights** (NB) | NB healthy at 350k where A350-C is not | NB count below A350-C's |

`[A3]` H2 and the H3 corollary predict the same rungs in the likely case (E 500k, A07 1M); H2′
predicts E 750k, A07 2M. The ladders separate H2′ from the other two. H2 vs H3 is separated only by
the matched-headroom arm A350-C-qkv1-450k (1 seed, a lead). R2 has no guaranteed H3 arm.
A positive H5 reads "a learned-width weight that can be pruned to 0 bits fixes it" (phys B7): NB
with 0-bit weights and 1-bit activations costs 368,134, against 619,198 for binary (`dev/README.md:64`);
this bears on the ternary baseline, not on "binary per se". H4 tests timing only, not squeeze rate
(phys C5).

## 3. Common setup (all rounds)

Recipe as in training-batch `STUDY.md`: Chang optimizer and cosine restarts (peak 3e-3, cycles
of 500), batch 2,790, [D19] quantizers, [D20] trace sample, `split_seed` 1, `order_seed = f(s)`.
Data: cache `/data/chang-n64-20260926/n64/data`, `data_info.json` sha256 `c6d058f5…e228` (from the
option-(c) handoff `record.json`), N = 64, features pt/etarel/phirel, train 558,000, validation
62,000. Regime B: trace every 10 epochs. Each pilot run stops at **epoch 500**, the end of the
first cosine cycle. Product: **RTX 3090, one arm per GPU, one product per round.** Option (c) means
`train.ebops.pid_input: traced_only`, `pid_traced_integral: per_epoch`; "no (c)" means the keys are
absent. PID warmup is `train.ebops.pid.warmup`, 1 by default; under (c) the allowed warmups are 1,
10, 20 and so on (`ablation.py:535-541`).

## 4. R1, broad sweep (fixed, 24 pods)

| # | arm id | hyp | arch | budget | (c) | warmup | seeds | pods | reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | A350-noC | H1 | E | 350k | no | 1 | 1, 2 | 2 | H1 control: the 42abed controller, on the new sha and the 3090 |
| 2 | A350-C | H1, H2 | E | 350k | yes | 1 | 1, 2 | 2 | H1 treatment; s1 is the E ladder's 350k rung; baseline for H3-H5 |
| 3 | E250k-C, E500k-C, E750k-C, E1000k-C, E2000k-C, E5000k-C | H2, H2′ | E | 250k-5M | yes | 1 | 1 | 6 | E ladder; a 1-seed locator for E's recovery rung |
| 4 | `[A3]` A07-500k-C, A07-1000k-C, A07-2000k-C, A07-5000k-C | H2, H2′ | A07 | 500k-5M | yes | 1 | 1 | 4 | A07 ladder. A07-5000k-C s1 is also the **pipeline positive control** (C-s1's configuration on the new sha) |
| 5 | A350-C-w50 | H4 | E | 350k | yes | 50 | 1, 2 | 2 | squeeze held past the Q/K collapse at ep0 29-39 (b5 `VERIFY.md` §6) |
| 6 | A350-C-w150 | H4 | E | 350k | yes | 150 | 1, 2 | 2 | 3× later; first feedback at epoch 160 leaves 340 epochs (local cpu_gate, not quotable), against 259-389 for b5 to first meet (a) (`recovery/readout-preparation/analysis/rules-b5.txt:13, :56, :116`; C′-s1 and E1-s1 never met it, :179, :227). Timing and LR phase are confounded. D3 |
| 7 | A350-C-qkv1 | H3 | E | 350k | yes | 1 | 1, 2 | 2 | `quant.attn_bit_floor {bits 1, sites q,k,v}`; headroom 80,170 |
| 8 | NB350-C | H5 | E | 350k | yes | 1 | 1, 2 | 2 | `quant.weight: kbi_learnable`; zero floor 171,526 (= A's) |
| 9 | `[A3]` A350-C-qkv1-450k | H3 | E | 450k | yes | 1 | 1 | 1 | matched-headroom H3 arm (180,170 vs 178,474); replaces A07-350k-C (headroom 6,947, predicted unhealthy by every hypothesis) |
| 10 | `[A3]` E-unc-C | control | E | none (PID target ≥ init EBOPs, or the EBOPs term off; ml-engineer records which) | yes | 1 | 1 | 1 | E positive control with no budget, and the only measured E entropy reference for the 0.95 cut |

24 pods (cap 24). Matched: rows 1 and 5-8 differ from A350-C only in the listed column; row 9
changes the floor and the budget together at matched headroom. Rows 9-10 are not ladder rungs and
not W or V_bin candidates. `[A3]` If E-unc-C cannot be expressed as config alone, it is dropped by a
further pre-data amendment, R1 is 23 pods, and the a26 entropy on `model_unconstrained.keras`
(F5, `readout_diag.json`) is the E reference instead.
`[A3]` D3: w150 is registered. **Kai may switch the two w150 configs to w100 before the R1 bundle
is frozen (F2).** Recorded: ____ (date, decisions.md ref). Until filled, R1 is as registered.

## 5. Readout (one row per run; the shared `readout.json`)

Exactly these fields: `arm`, `hypothesis`, `arch`, `budget`, `option_c`, `warmup`, `seed`, `epochs_done`,
`feasible_any`, `min_traced_ebops`, `best_feasible_val_acc`, `best_feasible_val_auc`, `nondegenerate_best`,
`attn_entropy_norm_mean`, `status`. Definitions, on validation (n = 62,000) and traced epochs 1-500:

- `feasible_any`: at least one traced epoch meets (a) traced EBOPs ≤ budget and (b) EBOPs above the
  row's `zero_floor_ebops` > 0 (`[A3]` 269,830 for qkv1 arms, `readout_pilot.py:127`; training-batch
  `STUDY.md:995-1012`). For E-unc-C, (a) holds by construction.
- `nondegenerate_best`: the runner's best-feasible checkpoint exists and meets (a), (b) and (c): val
  acc > 0.2109624456315518 (`PREFLIGHT.md:519`, p_maj + 5·SE; labels sha `e593f51f…7617`). True
  while `feasible_any` is false is an integrity failure.
- `best_feasible_val_acc` / `_auc`: top-1 accuracy and macro-OvR AUC of that checkpoint, selected
  by accuracy, then AUC, then −EBOPs, then −epoch (the frozen rule); null if none exists.
- `attn_entropy_norm_mean`: mean over heads of the row-renormalized entropy / log 64
  (`analysis/attn_entropy.py`, [A26]) on the best-feasible checkpoint, else `model_min_ebops`.
  Uniform = 1.0. `[A3]` The model has no attention mask, so zero-padded constituents are attended
  keys, and the normaliser is log 64 (keys), not log n_real (`attn_entropy.py:25`, phys B1).
- `status`: `complete` means epochs_done = 500, no divergence, certification pass for the
  selected checkpoint, and (if `option_c`) CONTROLLER_AUDIT PASS. Otherwise `failed`, `diverged`,
  `cert_fail` or `audit_fail`.

**Healthy** = `status == complete` AND `feasible_any` AND `nondegenerate_best` AND
`attn_entropy_norm_mean < 0.95`. Why 0.95: under WRAP a 0-bit Q gives identically zero logits, so
collapsed heads sit at exactly 1.000000 with per-jet sd 0.0 (every b3/b5 collapsed head). The only
working reference, C-s1, has mean 0.739877 and a highest head of 0.913695. With 2 heads, one
uniform head passes only if the other is below 0.90. The cut is calibrated on A07 only: every local
2-head E checkpoint (A-s2, D-s1, F-s1, all 350k) is at 1.000000, and no E checkpoint at a high
budget exists. E-unc-C `[A3]` is the designed E reference.

**Entropy-only failure** `[A3]` (this definition is used verbatim everywhere): a row with
`status == complete`, `feasible_any`, `nondegenerate_best`, `best_feasible_val_acc ≥ 0.50` and
`attn_entropy_norm_mean ≥ 0.95`. It is **not read as unhealthy**: the program stops for Kai (§10)
before any derivation (§7-9) or judgement (§6). Why 0.50 and not (c): a non-degenerate uniform row
at 0.236-0.405 is the documented 350k collapse (A-s2 0.320871, both heads 1.000000).
`[A3]` A row that is complete, feasible, non-degenerate, with acc in (0.2110, 0.50) and entropy
≥ 0.95 is **unhealthy** and is not an entropy-only failure; it cannot refute H2 (H2 reads
"inconclusive" when the E row that would refute it is such a row).

`[A3]` Descriptive only, never a rule input: `readout_diag.json` (F5) gives per arm t_uniform,
t_budget (first traced epoch meeting (a)), site order, cost split, controller error, NB
`weight_bits_mean`, a26 on `model_unconstrained.keras` (E rows, A07-5000k-C), and a26 plus val acc on
the epoch-500 snapshot.

## 6. Judging (directional; counts carry a Clopper-Pearson 95 % interval)

With 2 seeds, 2/2 against 0/2 is the only separating pattern; 0/2 has upper bound 0.842, 3/3 lower
bound 0.292, 0/3 upper bound 0.708. Paired val-acc differences are listed per seed; with ≥ 3 matched
non-null seeds a 95 % t-interval (df = n − 1) is added. Comparisons always use matched seeds.
`[A3]` **Every R1 verdict is a lead for R2, never a finding** (phys B4): about 5 comparisons share
the A350-C control, and at a true per-arm healthy rate of 0.5, P(some 2/2 vs 0/2) = 1 − (15/16)^5 =
0.276 (arithmetic on a hypothetical rate). R1 verdicts are "lead", "not supported at n = 2" (or
n = 1), "no separation" (equal counts, including 0/n vs 0/n) or "inconclusive". If A350-C is not
0/2, H3-H5 have no separating pattern at 350k and read inconclusive. No rule consumes these verdicts.

| hyp | round | lead | not supported | otherwise |
| --- | --- | --- | --- | --- |
| H1 | R1 | A350-C 2/2 and A350-noC 0/2 | A350-C 0/2 (at n = 2) | inconclusive |
| H2 | R1 (descriptive, n = 1 per rung) | both ladders monotone and the A07 recovery rung equals the prediction | E unhealthy at 5M on a criterion other than the §5 entropy-only failure or the low-acc uniform band, while E-unc-C is healthy; or A07 ≥ 2 rungs from the prediction. `[A3]` No healthy A07 rung = "beyond 5M", which counts ≥ 2 rungs from a prediction ≤ 1M | inconclusive (1 rung off; non-monotone; E first healthy at 5M, so the A07 prediction is beyond the ladder; A07 500k healthy reads "≤ 500k") |
| H2′ | R1 (descriptive) | first healthy E rung 750k and A07 rung 2M | E healthy at ≤ 500k or A07 at ≤ 1M | inconclusive |
| H3 | R1 | qkv1 2/2 and A350-C 0/2; or qkv1-450k healthy and A350-C 0/2 (1-seed lead) | `[A3]` qkv1-450k unhealthy and A350-C 0/2 (1-seed lead) | qkv1@350k failing reads "inconclusive (headroom-confounded)"; the ladder entropy transition is reported, never judged |
| H4 | R1 | a warmup arm 2/2 while A350-C 0/2 | both warmups strictly below A350-C, `feasible_any` on all 4 warmup rows | no separation; a w150 row without `feasible_any` reads "inconclusive (time-limited)", w50 can still lead |
| H5 | R1 → R2 `[A3]` (NB350-C vs A350-C, matched seeds) | NB healthy on all matched seeds, A350-C on none | NB count strictly below A350-C's | no separation; "budget, not binary" is not read from any count |

`feasible_any` false reads "time-limited" for w150 only; for every other arm it is unhealthy
(crit C3). H5 reading context (not a criterion): NB's weights start at 4 bits, so its initial EBOPs
are higher (12,362,587 vs 8,913,043, `dev/README.md:63-64`, text :66-70; synthetic trace) and its
squeeze trajectory differs; the H5 read lists `min_traced_ebops` and t_budget beside the counts.

**Positive controls** `[A3]` (cons B4, cons A4). A07-5000k-C s1 and E-unc-C s1 must be healthy. If
either is not (any reason, including entropy-only), the program stops for Kai before any judgement
or derivation: the sha, the product, the readout or the architecture is suspect, not the budget.

## 7. R2, zoom in (rule; ≤ 10 pods)

`[A3]` **Code rule (crit A1).** R2 and R3 configs are generated now by the same `generate.py`, with
only round, seed, budget and arm changed (F9): E rungs × seeds 2-4, the 6 variants × seeds 3-5, NB
at each E rung above 350k × seeds 1-3. They are bundled, byte-diffed, CPU-gated (cpu_gate +
pair_nb) and PREFLIGHT-reviewed **before the R1 readout Job writes `readout.json`**. The R2/R3
bundle must be byte-equal to the R1 bundle outside
`campaigns/pilot1005/{configs,packs,index.json,config_map.json,r1_packs.json}`, by a file-by-file
diff. Any other diff, or configs not ready before the R1 readout, stops the program for Kai.

Computed by the autopilot from the R1 readout, after the entropy-only and positive-control checks:
1. **r1** = the lowest E rung (A350-C s1 counts as 350k) whose seed-1 row is healthy. r1 is a 1-seed
   locator; R2's 4-seed bracket is the measurement. If no E rung is healthy: **stop**, notify Kai
   (characterization pivot; ROADMAP §4).
2. **Bracket** = {the rung below r1, r1}; {250k, 350k} if r1 = 250k. Each rung is brought to seeds
   {1,2,3,4} with (c) and warmup 1 (5-6 pods). `[A3]` The 350k rung's new rows are named A350-C, so
   they count for V_bin = A350-C and for H5.
3. **W**, the most promising 350k variant among A350-noC, A350-C, A350-C-w50, A350-C-w150,
   A350-C-qkv1 and NB350-C: by healthy count, then `nondegenerate_best` count, then `feasible_any`
   count, then lower mean entropy, then the order A350-C > A350-noC > qkv1 > NB > w50 > w150.
   Accuracy is not a criterion. W gets seeds {3,4,5} at 350k, minus seeds step 2 launches (≤ 3 pods).
4. **The other side at s3** (1 pod). V_bin is the best binary variant by the same order, NB
   excluded. If W = NB, V_bin gets seed 3; otherwise NB350-C gets seed 3.

After R2: **r_rec** = the lowest bracket rung with ≥ 3 of 4 seeds healthy (undefined if none).

## 8. R3, conditional (≤ 3 pods)

Runs only if P350 (§9) is not qualified after R2, r_rec > 350k, and A at r_rec is healthy in ≥ 3
of 4 seeds: **NB@r_rec**, seeds 1-3, (c), warmup 1. Otherwise R3 is skipped.

## 9. Production candidate (Kai decides) `[A3]`

The rule computes and qualifies a candidate. **Nothing auto-fires**: every production launch,
P350 or Prec, stops for Kai with the readout (K3; until Kai answers, this reading holds). Each
candidate is a matched pair (crit A2): **NB production = A's configuration with only `quant.weight`
changed.**
- **P350** = (350k, A350-C) and NB350-C. P350 is a candidate only when V_bin = A350-C. Any other
  V_bin goes to Kai with the readout, with no candidate.
- **Prec** = (r_rec, (c), warmup 1) as A, and NB@r_rec.

**Qualified** (phys A1): each production arm has ≥ 3 healthy seeds **that were not used to choose
it**, and every one of those rows has `best_feasible_val_acc ≥ 0.50`. Seeds 1-2 of the 350k
variants chose W and V_bin and do not count; for Prec, seed 1 chose r1 and does not count, so A at
r_rec needs seeds 2-4 healthy and NB@r_rec 3/3. Otherwise the candidate is reported **unqualified**.
Under the R2 caps one P350 side usually has a single fresh seed (the other side at s3); the
pre-built seeds 3-5 configs (F9) let Kai order a top-up of ≤ 2 pods (≤ 12 GPU-h; V_bin = A350-C implies W ∈ {A350-C, NB350-C}) if he chooses.
At 3/3 the Clopper-Pearson lower bound is 0.292; qualification is a screen, not a rate.

**The 0.50 floor is internal-only**, a screening floor between every 350k pilot checkpoint
(0.236-0.405) and the 5M or unconstrained ones (0.65-0.66, early or unsqueezed checkpoints); it is
not a physics reference. The external reference is Chang/Sun et al. (arXiv:2510.24784, Table 1):
at a 350k EBOPs target and N = 64, MHA-64 77.9 % and Linformer-64 79.8 % top-1 **test** accuracy
(held-out 260k split; learned-width weights, 7,000 epochs; seeds and run count not reported;
transcribed in `docs/chang-vs-bnjettag.md:100-101, :132, :149`, `.claude/memory/research-log.md:9`,
not recomputed). The paper reports that MHA-64's attention collapsed to a Deep Set
(`chang-vs-bnjettag.md:107-110`). Pilot values are validation at epoch 500, so they are never
compared with these numbers; the reference is context for Kai's decision.

Guards, all required before Kai is asked to launch: every row read is `complete` and the readout
integrity checks pass; the handoffs are listed in `PROGRAM.json` and Kai signed them; a production
PREFLIGHT critical PASS; the spend projection on the R1-measured rate (§11) fits the ceiling Kai
sets; RTX 3090.
**What launches on Kai's go:** two Jobs, A and NB at the chosen budget, seeds 1-8, 7,000 epochs,
regime B, one arm per GPU, 16 pods. Selection and analysis follow the frozen training-batch rules
(validation selection; ROC-test touched once, at production VERIFY).
**Production early stop** (pre-registered): a readout at production epoch 500 with the §5 health
rule. If either arm has fewer than 6/8 healthy seeds, both Jobs stop; an entropy-only row stops for
Kai. This bounds the loss to about 500/7,000 of production. Health after the first LR restart is
not measured by any pilot; Kai's decision carries that risk (phys B6).

## 10. Stop rules (the autopilot stops, notifies and launches nothing further)

Checked in this order:
1. Integrity: a row with `status` ≠ complete (`diverged` included, even at 250k where it may be a
   real outcome; Kai reads it), a Job with backoff exhausted, a missing or unexpected row; the
   threshold is not 0.2109624456315518, the labels sha differs, or `nondegenerate_best` without
   `feasible_any`.
2. An entropy-only failure (§5) in any round: stop, notify Kai with the row, derive nothing from that
   readout. Kai rules on the cut for that architecture (a dated, post hoc amendment) or ends the
   program.
3. `[A3]` A positive control (A07-5000k-C s1, E-unc-C s1) not healthy.
4. `[A3]` The R2/R3 configs were not gated before the R1 readout, or a bundle differs from R1's
   outside the §7 paths.
5. Product and utilization: a pod not on an RTX 3090, or GPU utilization < 40 % at 30 min.
6. A cap reached or projected over (§11).
7. Scientific: no E rung healthy (§7.1); A350-noC 2/2 while A350-C 0/2 ((c) harmful); after R2/R3,
   a candidate qualified or not (§9) always goes to Kai.
8. No rule matches, or a named handoff is a placeholder. An AI session may draft; it never launches.

## 11. Spend caps (RTX 3090 GPU-h, pod running time)

`[A3]` Basis: **38.8 s/epoch, an upper bound** (gpu-benchmark `VERIFY.md:109`, A07, K = 1, total
elapsed per run-epoch over n = 1 × 20 epochs; training-only rate 30.85 s). E and NB at K = 1 on the
3090 are unmeasured; R1 measures them (`epoch_seconds` in the JSONL).

| round | pods | GPU-h cap | basis |
| --- | --- | --- | --- |
| R1 | 24 | 144 | 6 h deadline per pod; 500 × 38.8 s = 5.39 h; retries only for non-deadline infrastructure failures, counted against the cap |
| R2 | ≤ 10 | 60 | same |
| R3 | ≤ 3 | 18 | same |
| production | 16 | decided at the gate (K4) | 7,000 × R1-measured s/epoch of the chosen arm × 16. Bounds: 960 at 30.85 s, 1,207 at 38.8 s |

Pilots total 222 GPU-h (about 250 approved, decisions.md 2026-10-05 10:08 item 5). With production
the program is 1,182 to 1,429 GPU-h against about 1,200 approved, so the production ceiling and
the production Job deadline are set at the gate from R1's measured rate. Pods in flight ≤ 24.

## 12. Not allowed

- No pilot or readout reads the ROC-test (held-out) set; selection uses validation only. Pilot
  numbers are never quoted, compared in a claim, or put in `verify.json`.
- No threshold, rung, seed or rule changes after an R1 number exists, except by a dated amendment
  signed by Kai and labelled post hoc.
- No code, config or manifest edit to a live round. A fix is a new PREFLIGHT and a new sha.
- `[A3]` No comparison across GPU product or training-code tree inside a judgement row. All rounds
  share R1's training-code tree (§7 code rule); any other code difference stops the program.
- No number from the home PC enters any rule.

## 13. Conventions compliance

| convention | status |
| --- | --- |
| jet-tagging-metrics: validation selection, labels, matched seeds, intervals | will implement (§5-6); the N=64 line uses 90/10 (n_val 62,000) and accuracy-first selection, as frozen in training-batch, not the 80/20 AUC default (ROADMAP §7.2) |
| quantization-and-cost: native EBOPs at the selected checkpoint, "no feasible checkpoint" | will implement (certification in `status`) |
| fpga-synthesis, figures | not applicable |

## 14. Where I am not sure (all FLAG FOR HUMAN: YES)

```
D1 DECISION: healthy needs attn_entropy_norm_mean < 0.95, calibrated on A07 only; entropy-only
   failure stops for Kai; E-unc-C [A3] is the E reference.  ALTERNATIVES: < 0.99; per-head max; no
   entropy term.  CONFIDENCE: MEDIUM
D2 DECISION: r1 and r_rec use healthy.  ALTERNATIVES: feasible + non-degenerate only.  CONFIDENCE: MEDIUM
D3 DECISION: H4 warmups 50 and 150.  ALTERNATIVES: 50 and 100 (w100 leaves 390 epochs from first
   feedback, ep 110); unconstrained-then-squeeze (new code).  CONFIDENCE: MEDIUM
>> KAI DECISION PENDING (D3, K1): keep w150 | switch to w100 before the F2 freeze. Recommended: w100
>> (the bundle is rebuilt anyway). Recorded: ____ -- until filled, R1 is as registered (w150).
D4 DECISION: H3 = q,k,v at 1 bit; [A3] plus the matched-headroom arm at 450k.  ALTERNATIVES:
   + softmax_out (368,134) or 2 bits (564,742), statically infeasible at 350k.  CONFIDENCE: HIGH
D5 DECISION [A3]: qualification = >= 3 fresh healthy seeds per arm and val acc >= 0.50 (internal).
   ALTERNATIVES: floor 0.40; floor relative to an in-lab learned-width reference.  CONFIDENCE: MEDIUM
D6 DECISION [A3]: nothing auto-fires; Kai decides P350 and Prec (K3 asked, recommended approve).
   CONFIDENCE: HIGH
D7 DECISION: production handoffs built after R2 for the candidate; Kai signs them.  CONFIDENCE: MEDIUM
D8 DECISION: production seeds 1-8 (pairing with frozen training-batch, [A17] checked at 1-8).
   ALTERNATIVES: fresh seeds 9-16.  CONFIDENCE: MEDIUM
D9 DECISION [A3]: Prec's fresh-seed rule excludes seed 1 (it chose r1); either positive control
   unhealthy stops for Kai.  ALTERNATIVES: count all r_rec seeds; report controls only.  CONFIDENCE: MEDIUM
```
- The epoch-500 cut does not see the first LR restart; a late recovery (D-s1 re-grew attention
  after epoch 400) would be missed. E's speed and utilization at one arm per GPU are unmeasured.

## 15. Deferred, with costs `[A3]` (arbiter estimates, agent-hours)

- **Per-epoch entropy observer** (cons B5): ~2.5 ah, a pytest-count change (`gate_check.py:32`) and a
  gate rerun. It changes the training path, which would break the §7 code rule. Next code bundle.
- **No-attention (mean-pool) control** (phys B1): ~3-4 ah for the architecture path, a gate, 1 pod; R1
  has no free pod. The first post-program follow-up.
- **NB with 1-bit initial weights** (phys B7, cons C1): ~2 ah, a gate, 2 pods. R3 or post-program if H5
  reads "NB ≤ binary"; `readout_diag.json` item 6 quantifies the confound meanwhile.
- **R2 bracket including the rung above r1** (phys B3): +3-4 pods (≤ 24 GPU-h), over the R2 cap. Not
  adopted; H2 in R1 is descriptive instead.
- **A guaranteed 3-seed H3 arm in R2** (cons B2): 3 pods (18 GPU-h), over the R2 cap. Not adopted;
  qkv1-450k gives a 1-seed matched read.
- **E-unc-C as code** (cons A4 fallback): ~1.5 ah plus a test, only if config cannot express it (§4).
- **Squeeze-rate (PID gain) arm** (phys C5) and **restart-crossing pilots to 1,000 epochs** (phys B6):
  not costed by the arbiter; not in this program.
