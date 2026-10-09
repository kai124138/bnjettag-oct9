# Tried already: every method this project has run

Inventory for `campaigns/2026-09-26-delta/`, written 2026-09-27. Read-only: no number
here is new. Every number is copied from the file and line cited next to it, with its metric,
split, n and status. A row without a number has a words-only outcome on purpose.

## How to read this file

**Status.** `verified` means a results-analyst gate, a verify-roc pass or a `VERIFY.md` covers
that number. `unverified` means the trainer or an evaluation script recorded it and no gate did.
`failed-with-mechanism` means the method did not do its job and the record names why.
`failed` means it did not do its job and no cause is established. `abandoned` means built or
started, never concluded. `in flight` means running at the last record. `n/a` marks
infrastructure used by every row (no outcome of its own).

**Era.** `archived` = before 2026-09-10 or the Round-14 recipe (no EBOPs target). `current` =
EBOPs-constrained, from 2026-09-10. One row (G4) is current by date but ran the archived recipe;
it says so.

**Splits.** "val" = internal validation, 124,000 jets (20 % of the Zenodo train archive, split
seed 1) unless stated. "held-out" = the Zenodo val archive used as the ROC-test set,
n = 260,000. "val acc" / "held-out acc" = top-1 five-class accuracy. AUC = macro one-vs-rest.
Before 2026-07-01 ("era-1") the dataset was different; era-1 AUCs are not comparable to anything
after it. Rounds 5 to 11 used 16 features per constituent (top-10); Round 14 onward uses
(N, 3) = pT, eta_rel, phi_rel.

**Source keys.**

| key | file |
| --- | --- |
| XL | `.claude/memory/experiment-log.md` (live, newest on top; cited as line + entry date because the orchestrator prepends and lines drift. Entries dated before 2026-09-10 also sit near-verbatim in `.claude/memory/archive/experiment-log.md` at a different offset) |
| DEC | `.claude/memory/decisions.md` |
| RES | `RESEARCH.md` (archived banner, 2026-09-26) |
| PUB | `publication/README.md` |
| ABL | `publication/results/post_conference/ablation_metrics.json` |
| IDX | `publication/docs/current-work/EXPERIMENT_INDEX_20260923.md` |
| TR23 | `publication/docs/current-work/TRAINING_RESULTS_20260923.md` |
| PLAN | `publication/docs/current-work/TRAINING_BATCH_PLAN_WITH_FROZEN_BACKBONE_FOLLOWUP.md` |
| ATT | `publication/docs/current-work/BATCH20260918_ATTENTION_STUDY.md` |
| CONF | `publication/docs/current-work/CONFIRMATION_RUNS_20260924.md` |
| CS | `publication/docs/current-work/CONSTITUENT_SCREEN_20260923.md` |
| ENG | `publication/docs/current-work/ENGRAM_STUDY.md` |
| R4HW | `publication/docs/current-work/R4_HARDWARE_SYNTHESIS.md` |
| ERB | `campaigns/2026-09-20-continuation-packed/engram/hgq2/study/ENGRAM_RESEARCH_AND_RUNBOOK.md` |
| ENGS | `campaigns/2026-09-18-engram-study/STUDY.md` |
| ACC | `campaigns/2026-09-16-accuracy-investigation/README.md` |
| PTWV | `campaigns/2026-09-25-pt-weighting/VERIFY.md` |
| INV | `campaigns/2026-09-26-training-batch/review/STUDY_investigation_350k.md` |
| TB26 | `campaigns/2026-09-26-training-batch/STUDY.md` |
| CHG | `docs/chang-vs-bnjettag.md` |
| RC | `_attic/repro-chang/repro-chang/comparison.md` |

Common current-era recipe (unless a row says otherwise): binary `binary_absmean` weights,
activation widths learned from an 8-bit init, norm-free, D32/H4, ReLU FFN, GAP, Adam β₂ 0.98,
weight decay 0.01, clipvalue 1, batch 256, LR 2e-5 with 1 warm-up + 999 linear-decay epochs,
1,000 epochs, BetaPID P 1 / I 0.05 / D 0, warm-up 10, β init 1e-7 in [1e-10, 1e-3], selection
= best val metric among checkpoints at or under the final target (PLAN:42-56; XL:405, 2026-09-12).

## Tried: 68 rows in ten families

### A. Weights and the binarizer

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | Custom absmean binary STE (`binary_absmean`: β = absmean of the centered latents, `ws = wc/stop_gradient(β)`) | FINAL-campaign build, XL:6293-6302 (2026-07-07); every binary run since | all | all | all | all | "gives exactly {-beta,+beta} with bounded backward" (XL:6301-6302); "All 51 BitLinears binarize to exactly {−1,+1}" (XL:6418, 2026-07-04); 15 binary layers two-valued in each re-measured pilot checkpoint (XL:484, 2026-09-10) | verified (binarization gate, not accuracy) | this is the thesis quantizer | both |
| A2 | Stock HGQ2 1-bit KBI weight quantizer on latent floats | same build, XL:6300-6301 (2026-07-07) | – | – | – | – | "collapses to {-1,0,+1} (4096/4096 -> 0, ternary = STOP)" (XL:6300-6301) | failed-with-mechanism | 1-bit KBI rounding sends latents to zero: the layer becomes ternary, which breaks the thesis | archived |
| A3 | β convention: centered absmean (ours) vs uncentered (BitNet b1 reference) | analysis on r14 n8 W1A8 s3, XL:3064-3070, 3100-3105 (2026-08-08) | 8 | – | 1 checkpoint | none | "below the fx8 noise floor in 14/15 layers; the exception is head_fc2 and it is mechanistically forced" (XL:3064-3065) | verified (as a formula comparison) | never a training arm: β is in the gradient path, so the uncentered form "would have yielded a *different checkpoint*" (XL:3101-3103) | archived |
| A4 | Learnable multi-bit KBI weights (`kbi_learnable`, R13 arm A2, a declared non-binary control) | R13, XL:3763-3765, 3800-3802 (2026-08-01) | 10 (16 feat) | 1,500 planned | 3 planned | 5e5 | built and preflighted; "Stage1 NOT launched — awaiting Kai's go" (XL:3694); can anneal to b=1, "the {-1,0,+1} ternary grid" (XL:3800-3801) | abandoned | superseded by Round 14, launched the same day | archived |
| A5 | Ternary weights (QKeras `BN_TERNARY=1`) | three W&B runs of 2026-06-23, listed in the ternary inventory XL:3658-3682 (2026-09-01) | old dataset | 8-23 of 200 | 3 runs | none | val AUC 0.7638 / 0.6837 / 0.6259 on the old dataset (XL:3665-3669); Round-14 tree: "no ternary models, none ever trained" (XL:3659) | abandoned | not comparable: old dataset, 6,373,633-param model, QKeras `.h5` the HGQ2 path cannot ingest, under-trained (XL:3672-3677) | archived |
| A6 | W8A8 baseline (`int8_absmax`) | Round 14, RES:153-162; also rounds 5, 7, 8, 11 | 8 / 16 / 32 / 64 | 101 | 3 | none | held-out AUC 0.8862 ± 0.0009 (N=8), 0.9124 ± 0.0014 (16), 0.9358 ± 0.0011 (32), 0.9448 ± 0.0011 (64) (RES:159-162); no W8A8 deficit against FP32 is resolved at three seeds (RES:172-177) | verified | – | archived |
| A7 | FP32 baseline | Round 14, RES:159-162; round 8 XL:5113 (2026-07-18) | 8-64 | 101 | 3 | none | held-out AUC 0.8864 ± 0.0005 (N=8) to 0.9486 ± 0.0012 (N=64) (RES:159, 162) | verified | never trained under an EBOPs target in any record | archived |
| A8 | Gradient clipping by global norm (round 5) replaced by clipvalue 1.0 | XL:6303 (2026-07-07) | – | – | – | – | `global_clipnorm` "overflows float32 -> A4 NaN, LR-independent"; clipvalue 1.0 in every run since (XL:6303) | failed-with-mechanism (clipnorm) | float32 overflow of the global norm | archived |

### B. Activation quantization

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B1 | Fixed activation ladder A8 / A6 / A4 (static per-tensor, MSE-calibrated, trainable calibration) | Round 14, 60 runs, RES:143-182 | 8 / 16 / 32 / 64 | 101 (ES 15) | 3 | none | held-out AUC W1A6 0.8689 ± 0.0020 (N=8) to 0.9136 ± 0.0061 (N=64); W1A4 0.8534 ± 0.0012 to 0.9073 ± 0.0009 (RES:159-162); A8→A4 step resolved at N ≤ 16; at N = 32 the two uncertainty estimates disagree (RES:169-171). Round 5 (large D256, 16 feat): W1A6 0.8307, W1A4 0.7329, seed-averaged (XL:6469-6470, 2026-07-03) | verified | A4 costs most where classes are already hard | archived |
| B2 | Frozen vs trainable activation-grid scales ("A4 rescue") | FINAL campaign, XL:6095-6103 (2026-07-07) | 10 (16 feat) | 40 (end of schedule) | 1 probe + cohort | none | W1A4 best val AUC 0.76257 trainable vs 0.5825 / 0.6049 frozen, "+16–18 pts" (XL:6097-6098) | unverified (val) | frozen grids cannot follow the drift at 4 bits; "grids moved at 12/83 sites" (XL:6099) | archived; trainable grids are the default since |
| B3 | Learned activation widths (HGQ free KIF quantizer, `_free_act`, MonoL1, init on the A8 grid) | introduced R13, XL:3761-3763 (2026-08-01); default in every EBOPs run from the 2026-09-10 pilot, XL:491-493 | 8 on | – | – | – | the only lever the PID acts on; a source edit that removed `_free_act` was caught by CPU preflight before launch (XL:443-446, 2026-09-11) | n/a | – | current |
| B4 | Channel-wise vs tensor-wise learned widths (`quant.act_granularity`) | R1 vs R0 (ablations, XL:405, 2026-09-12); A00 vs A01 and A02 vs A03 (batch20260917, PLAN:81-84) | 8 | 1,000 | 1 per arm | 350k | held-out: channel 58.7431 % acc / 0.850795 AUC at 317,890 vs tensor 57.4758 % / 0.844527 at 348,526 (ACC:13-14); val acc A00 59.80 % vs A01 58.25 %, A02 61.08 % vs A03 59.44 % (TR23:25-28) | unverified; single seed per arm, no interval | same sign in all three pairs; the regularizer averages per site (MeanMonoL1) so adding channels does not raise aggregate γ (XL:411) | current |
| B5 | Fixed-width recovery (R5: freeze learned grids after epoch 800 once feasible, keep training weights) | ablations, XL:405 (2026-09-12) | 8 | 1,000 | 1 | 350k | held-out 56.9404 % acc / 0.840727 AUC at 349,390 (ACC:18); selected checkpoint at one-based epoch 205 (ABL:101) | failed-with-mechanism (as a test of the treatment) | the selected checkpoint precedes the epoch-800 freeze, so the number does not measure the freeze; the treatment itself is unmeasured | current |

### C. EBOPs targets and controllers

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | No EBOPs term in the loss (cost measured afterwards) | every run before R13: "the EBOPs term was OFF in every run this project has ever done" (XL:3760, 2026-08-01); all of Round 14 | 8-64 | 101 | 3 | none | W1A8 needs 5.28× (N=8), 4.08× (16), 2.97× (32), 2.14× (64) fewer checkpoint EBOPs than W8A8 (RES:204-206); n8 W1A8 checkpoint 1,739,182 EBOPs, export graph 3,025,884 (+74 %) (RES:208-209) | verified | checkpoint EBOPs omit the β-restore affines and any accumulator term (RES:207-210) | archived |
| C2 | Open-loop β PieceWiseSchedule + Pareto-front admission (R13 sighter: 1,500 epochs, batch 1024, 3 cosine cycles of 500, warm-up 5) | R13 stage 0/0b, XL:3685-3716, 3779 (2026-08-01) | 10 (16 feat) | 300 (LR probes), 1,500 (sighter) | 1 | 5e5 | 11 admitted points under 5e5; selected val AUC 0.75509 at 487,838 EBOPs vs 0.89775 unconstrained best of the same run at epoch 207 (XL:3687-3689) | unverified (val, one seed); stage 1 abandoned (XL:3694) | budget reachable, at a large accuracy cost; the matched binary-vs-multi-bit comparison never ran. The only run in the record with cosine restarts | archived |
| C3 | BetaPID on relative budgets 75 / 50 / 25 % of initial EBOPs, plus a β = 0 control | 2026-09-10 pilot, XL:491-501, 481-486 | 8 | 101 | 1 | 1,304,386.5 / 869,591 (XL:477) / 434,795.5 | control 1,780,910 EBOPs, val AUC 0.8716604564; 75 % feasible at 1,263,790, val 0.8700535576; 25 % missed (final 1,062,318; saved checkpoint unconstrained, val 0.8629018714); 50 % failed before its first epoch (XL:482-486) | unverified (val quoted from `train_meta.json`, not recomputed) | 25 %: "Stronger 25% beta grows while LR decays; schedule limitation is a hypothesis" (XL:486). 50 %: A10 XLA/Triton GEMM autotuning `NOT_FOUND` (XL:482), bypassed later with `jit_compile=false` (XL:574) | current |
| C4 | Cost-first PID: β0 1e-4, max 1e-2, constant LR 1e-4, min-EBOPs selection, stop at the first feasible epoch | 2026-09-10 retry, XL:573-576, 474-479 | 8 | 8 of max 101 | 1 | 869,591 | 847,982 EBOPs at epoch 8; selected val AUC 0.7972819476 vs 0.8516248187 at 1,276,686 one epoch earlier (XL:477-479) | unverified | "immediate budget stop leaves accuracy recovery untested"; β, LR, schedule and selection changed together, so β's effect is not isolated (XL:479) | current |
| C5 | Absolute 350k target, standard PID, 1,000 epochs, `stop_on_target=false` (standalone run) | XL:457-472, 417-429 (2026-09-11) | 8 | 1,000 | 1 | 350k | first compliant epoch 141 (XL:421); selected epoch 1,000 at 344,430 EBOPs, val AUC 0.8536 (PUB:63) | unverified; no held-out evaluation exists | – | current |
| C6 | Same recipe as the reference arm of the seven-arm matched set (R0, tensor-wise widths) | ablations, XL:404-415 (2026-09-12) | 8 | 1,000 | 1 | 350k | held-out 57.4758 % acc / 0.844527 AUC at 348,526 (ACC:13) | unverified | reference for B4, B5, D1, E2, H5 | current |
| C7 | Gradual budget schedule | R4 (1M → 750k → 500k → 350k, XL:405); B04 (525k at 0 → 420k at 100 → 350k at 200, ATT:21); screen B04 (transitions at epochs 0 / 5 / 10, XL:81-82, 2026-09-22) | 8; 16; 8 and 64 | 1,000; 1,000; 50 | 1; 3 (s4-6); 1 | 350k final | R4 held-out 57.5085 % / 0.846941 at 349,550 (ACC:17). B04 never feasible; final val acc 36.33 % ± 2.71 pp at 721,193 (TR23:52). Screen N=8 val 63.41 % / 0.8788 at 600,329, infeasible (CS:29); N=64 9,211,753 (IDX:50) | R4 unverified; B04 and screen failed | at N=16, relaxing early pressure did not avoid the squeeze; the screen is 50 epochs | current |
| C8 | Target level ladder | A09 500k and A10 250k at N=16; A11 500k at N=8 (PLAN:90-92) | 16; 8 | 1,000 | 1 | 250k / 500k | A09, A10 never feasible (TR23:34-35). A11 feasible at 479,462, val acc 62.62 % / AUC 0.8749 (TR23:36); held-out 62.3335 % / 0.873813 (CONF:14) | unverified | at N=16 neither a looser nor a tighter target changed feasibility. A11 is not a 350k result (CONF:16) | current |
| C9 | BetaPID toward 350k in the matched N=8 / N=64 screen (LR 2e-4) | constituent screen, INV:9-14, 46-70; IDX:34-86 | 8 and 64 | 50 | 1 | 350k (A09 500k, A10 250k) | 0 of 18 N=64 arms feasible; lowest EBOPs ever logged 4,630,276 (A07, epoch 46), 13.2× the target (INV:11-14). N=8 half: no row reached its budget, A06 closest at 386,219 (IDX:86); A00-A03 endpoints 632,846-699,566 at N=8 (IDX:66-69) and 9,161,276-10,800,700 at N=64 (IDX:38-41) | failed-with-mechanism (truncation; not a floor) | truncated run: β ended at 1.8e-5 against a 1e-3 maximum and was still rising; "It shows 350k was not reached, not that it cannot be" (INV:82-85) | current |
| C10 | Separate post hoc N=64 target of 5M | confirmations, CONF:20-26 (2026-09-24) | 64 | 1,000 | 2 (s2, s3) × 3 arms | 5M | runs hold at 4.74-5.01M, zero rows ≤ 350k (INV:86-91) | in flight | "set from the endpoints of the runs it will judge ... not a pre-registered target" (CONF:26) | current |

### D. Architecture

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| D1 | FFN width 64 → 32 | R2 vs R1 (XL:405); A02 / A03 vs A00 / A01 (PLAN:81-84) | 8 | 1,000 | 1 per arm | 350k | R2 held-out 58.3131 % / 0.853526 at 329,838: highest held-out AUC of the seven, lower accuracy than R1 (ACC:15). Val acc A02 61.08 % vs A00 59.80 %; A03 59.44 % vs A01 58.25 % (TR23:25-28). A02 held-out 60.7850 % / 0.860432 at 349,298 (CONF:13) | unverified; single seed | the only architecture change that is feasible at 350k and positive in both pairs | current |
| D2 | N = 16 at 350k (D32 / F32 / L2 / H4, channel widths) | A04 (PLAN:85); B00 reference, seeds 4-6 (ATT:17) | 16 | 1,000 | 1; 3 | 350k | A04 never feasible; latest val 41.50 % / 0.7087 at 721,198 (TR23:29). B00 34.94 % ± 7.05 pp / 0.6702 ± 0.0687 at 721,212 (TR23:48) | failed | "the current record does not attribute that degradation to a single cause" (TR23:40). Attention scales as N²D (PLAN:94); unconstrained archived N=16 W1A8 costs 4,819,784 EBOPs vs 1,739,182 at N=8 (ACC:28) | current |
| D3 | N = 32 at 350k | A05 (PLAN:86) | 32 | 1,000 | 1 | 350k | never feasible; latest 46.96 % / 0.7660 at 2,486,562 (TR23:30) | failed | cost never approached the target | current |
| D4 | Embedding D32 → D16 | A06 at N=16 (PLAN:87); screen A06 at N=8 / 64 | 16; 8 and 64 | 1,000; 50 | 1 | 350k | A06 never feasible, 38.00 % / 0.6721 at 498,373 (TR23:31). Screen N=8 val 60.54 % / 0.8584 at 386,219, the closest N=8 arm (CS:38; IDX:86); N=64 45.30 % / 0.7764 at 7,207,292 (IDX:42) | failed (feasibility) | – | current |
| D5 | One transformer block (L = 1) | A07 at N=16 (PLAN:88); screen A07 at N=8 / 64; N=64 confirmations at 5M | 16; 8 and 64; 64 | 1,000; 50; 1,000 | 1; 1; 2 | 350k; 350k; 5M | A07 N=16 closest to target at 362,195, never feasible, 38.32 % / 0.6988 (TR23:32, 40). Screen N=8 61.12 % / 0.8660 at 411,302 (CS:36); N=64 57.95 % / 0.8619 at 4,634,372, the lowest N=64 cost (IDX:43). Confirmations running (CONF:22-23) | failed at 350k; N=64 at 5M in flight | base architecture of the 2026-09-26 anchor (TB26:92) | current |
| D6 | Fewer heads (H = 2; H = 1) | A08 H2 at N=16 (PLAN:89); B01 H1 at N=16, seeds 4-6 (ATT:18); screen B01 at N=8 / 64 | 16; 8 and 64 | 1,000; 50 | 1; 3; 1 | 350k | A08 never feasible, 35.18 % / 0.6647 at 550,390 (TR23:33). B01 lowest attention-arm cost, 465,004, still infeasible, 35.99 % ± 2.05 pp (TR23:49, 54). Screen B01 N=8 crashed at 33/50 (IDX:75); N=64 56.03 % / 0.8563 at 5,195,955 (IDX:47) | failed (feasibility) | fewer heads at fixed D do not cut Q/K/V projection cost in proportion (PLAN:94; ATT:23) | current |
| D7 | No positional encoding | B02 at N=16, seeds 4-6 (ATT:19); screen B02 at N=8 / 64 | 16; 8 and 64 | 1,000; 50 | 3; 1 | 350k | B02 never feasible, 30.17 % ± 8.76 pp / 0.6235 ± 0.1074; seed 6 ended at 20.08 % and 0.5000 AUC (TR23:50, 54). Screen N=8 62.61 % / 0.8731 at 637,091 (CS:30); N=64 50.60 % at 9,219,798 (IDX:48) | failed (feasibility); largest seed spread | the table is not a large cost term (B02 721,193 vs B00 721,212, TR23:48, 50); converters had to be taught PE-free models (XL:195, 2026-09-18; ATT:43) | current |
| D8 | Upstream "learned" positional encoding | era-1 finding, XL:6924-6935 (2026-06-27) | – | – | – | – | trains 0 parameters: `Embedding(N,D)(tf.range(N))` on a constant is folded into a fixed random offset (XL:6929-6931) | failed-with-mechanism | fixed with a genuinely trainable table; PE is now conditional on `arch.pos_enc` (XL:189-190, 2026-09-18) | archived |
| D9 | Size / capacity ladders | era-1 tiny / small / medium / large (XL:6808-6905); round 7 small 19,201 / tiny 5,345 params × 5 variants × 3 seeds (XL:5566-5577); round 11 d32-d128 (XL:4431-4441) | 10 (16 feat) | – | 1-3 | none | round 11, matched norm-free arms: "binary is dominated at EVERY scale measured", ΔAUC −3.29 (d32) to −0.45 (d128) points, held-out (XL:4435-4441); W8A8 retention 96-106 % at every scale (XL:4647) | verified (round-11 gate) | the binary deficit is a capacity effect; no intermediate precision fits and keeps rejection (XL:4647-4649) | archived |
| D10 | Norm variants: SubLN inside BitLinear, RMSNorm, shared norm, norm-free | era-1 ablations (XL:6886-6889); round 7 no-norm (XL:5287); round 8 (XL:5112-5118) | 10 (16 feat) | – | 3 | none | era-1: norm structure about neutral (XL:6889). Raw inputs: removing norm cost about 9 val points (XL:5287-5288). Standardized inputs: W1A8 norm-free 0.8902 ± 0.0067 vs W1A8 SubLN 0.8763 ± 0.0035 held-out; "SubLN actively HURTS binary under conditioned inputs" (XL:5113-5118) | verified (round-8 gate) | SubLN also costs DSPs or 4.3× norm LUT on fabric (J3). Norm-free has been the default since | archived |
| D11 | CLS pooling, GELU, softmax-free attention | era-1 rounds 1-2, XL:6855-6889 (2026-06-28) | old dataset | – | 1-3 | none | single-run gains of +0.013 to +0.014 at a too-hot LR (XL:6886-6887); on seed repeats the CLS gain was "a lucky single draw" (XL:6866-6867); stacked combinations gave nothing (XL:6868-6869) | verified (log re-extraction) | noise; peak LR dominated every architecture knob (XL:6855, 6821) | archived |
| D12 | Pairwise-invariant attention bias (ParT-style ΔR², kT², m²_ij through a binary MLP into pre-softmax scores) | round 10, XL:4809-4817, 4722-4734 (2026-07-24/25) | 10 (16 feat) | – | 6 | none | held-out AUC 0.8907 ± 0.0050 vs flagship 0.8902 ± 0.0067, "FLAT"; rejection gain Welch p = 0.43, "NOT separable from seed noise" (XL:4725-4728) | verified (6-seed gate) | the 3-seed +0.16-point reading was seed luck; do not promote (XL:4733-4734) | archived |

### E. Attention and softmax precision

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| E1 | Softmax output grid 10 → 6 → 4 bits (`softmax_out_bits`, `softmax_out_i = 0`) on the Round-14 recipe (Job Gamma) | r15-gamma, XL:1695-1712, 1610-1630, 1555-1567 (2026-08-23/24) | 8 | 101 | 3 | none | held-out AUC 6-bit 0.8706 ± 0.0017, 4-bit 0.8701 ± 0.0020 vs W1A8 control 0.8712 ± 0.0016 (RES:334; XL:1556, 1611); "the 10-bit softmax output grid was over-provisioned" (XL:1564) | verified (verify-roc) | the 4-bit arm gave the first fitting zero-DSP point, 1,689,320 CLB LUT = 97.8 % at 0 DSP (RES:84-86). Never re-run under an EBOPs target | archived |
| E2 | 8-bit attention probabilities (`softmax_out_bits = 8`, `softmax_out_i = 1`) under 350k | R3 at N=8 (XL:405); B03 at N=16, seeds 4-6 (ATT:20); screen B03 at N=8 / 64 | 8; 16; 8 and 64 | 1,000; 1,000; 50 | 1; 3; 1 | 350k | R3 held-out 57.3435 % / 0.845380 at 340,174, below R1 (ACC:16). B03 never feasible, best attention-arm mean, 39.02 % ± 4.60 pp / 0.6999 ± 0.0273 at 688,438 (TR23:51). Screen N=8 crashed at 35/50 (IDX:77); N=64 8,646,668 (IDX:49) | unverified; failed feasibility at N ≥ 16 | R3 was killed from outside at epoch 810 and resumed (XL:350-362, 2026-09-14). Not the same experiment as E1: different integer bit, under a target | current |
| E3 | Fixed softmax cost (observation used when a 100k target was considered) | 100k feasibility snapshot, XL:401-402 (2026-09-12) | 8 | – | – | 100k considered, never launched | "Each current model reports 42583 EBOP per fixed softmax =85166 for 2 blocks, already 85% of 100k target" (XL:402) | n/a | a floor any low target must clear; E1 is the only measured way down | current |

### F. Memory modules (Engram-inspired tables)

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| F1 | E00 two-block reference and E01 one-block control under the Engram protocol | Engram pilot + continuation, ENG:13-14; ENGS:23-25 | 16 | 1,000 | 1 | 350k augmented | latest val E00 33.27 % / 0.6384 at 721,193; E01 33.44 % / 0.6450 at 362,158 (ENG:13-14). Both peaked near epoch 50 at val AUC 0.881 / 0.872 with 2.44M / 1.32M EBOPs, then fell as cost fell (ENGS:23-24) | failed-with-mechanism | budget squeeze: accuracy falls with cost and "once the squeeze had bitten the damage did not reverse" (ENGS:25) | current |
| F2 | E02 ungated exact-tuple memory (512 rows, 8-bit values, added after the first attention residual) | ENG:15, 24; ERB:137 | 16 | 1,000 | 1 | 350k augmented | val 54.55 % / 0.8322 at 380,009, never feasible; selected-checkpoint metric reproduction failed at atol 1e-7 (ENG:15, 47) | failed | reload mismatch unresolved (ENG:47) | current |
| F3 | E03 gated memory (quantized context gate, 8-bit key / value) | ENG:16, 24-30; ERB:138 | 16 | 1,000 | 1 | 350k augmented | val 52.55 % / 0.8203 at 440,525; 96.38 % of training-probe gate values equal 0.5 at the last epoch (ENG:16, 53) | failed-with-mechanism (gate) | the gate stays at its 0.5 initial value; E03 vs E02 changes capacity, scaling, rounding and cost together (ENG:18) | current |
| F4 | E02-E07 in the matched N=8 / N=64 screen (50 epochs, LR 2e-4; memory caps 64 KiB logical / 2 MiB replicated) | constituent screen, CS:11-54; IDX:51-56, 79-84 | 8 and 64 | 50 | 1 | 350k | N=64 val: E02 66.60 % / 0.8997 at 4,720,386; E05 (4-bit) 66.52 % / 0.8988 at 4,816,654; E03 65.46 % / 0.8979; E04 63.91 % / 0.8880; E06 (64 rows) 62.56 % / 0.8825 (IDX:51-55). N=8: E05 62.37 % / 0.8723 at 418,159; E02 / E03 canary only (IDX:79-83). E07 at N=64 statically infeasible, fixed memory arithmetic 838,272 > 350k (IDX:56) | unverified; no feasible checkpoint | logged `ebops` omits the memory arithmetic (`cost/custom_estimated_bitops` = 0 in every row), so E-arm costs are not comparable to A07 (INV:93-96); the N=64 ordering is "consistent with under-training" of the non-memory arms (CS:54) | current |
| F5 | E02 and E05 at N=64 under 5M, seeds 2-3 | confirmations, CONF:22-23 | 64 | 1,000 | 2 | 5M | at the last read, last logged epochs 279-299 of 1,000 (INV:91) | in flight | – | current |

### G. Data and inputs

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| G1 | Input set: top-32 × 16 features → top-10 × 16 → L1-realistic (N, 3) = pT, eta_rel, phi_rel | XL:6709, 6689 (2026-07-01); Round-14 pre-registration DEC:640-660 | 32 → 10 → 8-64 | – | – | none | the 2026-08-04 log reads it as "3-feature L1 input ~free vs 16-feature (fp32 n16 .9128 vs r8 n10 .9161; exceeds at n32+)" (XL:3440); that is a reading, not a result: it crosses input set and N, and RESEARCH.md declines the comparison ("outside this document's scope and are not compared here", RES:197-198) | verified numbers; the cross-input comparison is not a project claim | the (N, 3) set matches Odagiu et al. and Chang's group (DEC:641-645) | archived; every current run uses it |
| G2 | Per-feature input standardization (train-split fit, applied before the model) | round-8 2×2, XL:5708-5761; gate XL:5112-5118 (2026-07-18) | 10 (16 feat) | – | 1 (2×2); 3 (gate) | none | "standardization lifts FP32 +9.1 / binary +12.6-14.0 pts" held-out (XL:5116); the binary-specific mechanism predicted for it was refuted (XL:5734-5738) | verified (round-8 gate) | a general conditioning bug, not a binary pathology. `input_std` is on in every run since; it needs a constant affine in firmware (J11) | archived |
| G3 | Constituent count N ∈ {8, 16, 32, 64}, unconstrained | Round 14, RES:143-205 | 8-64 | 101 | 3 | none | binary gap against FP32 +0.0152 / +0.0172 / +0.0322 / +0.0365, resolved (RES:168-169); N=64 W1A8 seeds 0.9028 / 0.9084 / 0.9251 (RES:178); binary seed variance ×75.8 at N ≥ 32, weak seeds peak mid-training (RES:199-203) | verified | cause of the N ≥ 32 instability open; the named hypothesis is 101 vs 7,000 epochs (CHG:152-155, 208) | archived |
| G4 | Per-class pT sample re-weighting (Option E: each class to the all-class log pT shape, 100 bins, +0.5 smoothing; cap 5 = PTW5, no cap = PTWNC) | `campaigns/2026-09-25-pt-weighting/`; PTWV:262-265, 281, 363 | 8 | 101 (ES 15) | 8 | none | held-out AUC BASE 0.8711 ± 0.0013, PTW5 0.8603 ± 0.0019, PTWNC 0.8587 ± 0.0020 (PTWV:262-264); PTW5 − BASE −0.0108 [−0.0124, −0.0093], lower on 8/8 seeds (PTWV:281) | verified (VERIFY.md): negative | lowers every class, gluon most; gains only at both pT ends, post hoc binning (XL:31, 2026-09-26); without the cap W/Z effective sample falls to 36 % / 33 % (XL:47) | current by date, **archived recipe**: the configs are the Round-14 headline, `epochs` 101, `es_patience` 15, no EBOPs block (`bnjettag/code/hgq2/configs/ptw-n8-20260925-base-w1a8.json:35, 46`) |

### H. Recipe, schedule, selection, distillation

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | Peak-LR sweeps on binary models | era-1 rounds 1-4 (XL:6808-6880); round-7 stage 0 (XL:5762, 5785-5799); round-7b tiny (XL:5275-5279); R13 stage 0 (XL:3707-3711) | various | – | 1-3 | none | era-1: "the peak LR was the hidden lever at EVERY size" (XL:6821). Round 7: lower LR better; at LR ≥ 2e-4 the binary model "peaks at **epoch 2-3** and then degrades: that is straight-through-estimator collapse" (XL:5797-5798). Tiny: 0.7176 val at 5e-5 vs about 0.58 at 2e-5 (XL:5276-5277). R13: lr 5e-5 won at 0.89843 val (XL:3710) | verified (era-1 extraction); others unverified | binary QAT is "LR-**fragile**, not LR-starved" (XL:5799); the optimum moves with model size | archived. Current runs all use 2e-5; the screen used 2e-4 for 50 epochs (XL:81) |
| H2 | Longer training: 101 → 1,000 epochs; continuation of the A/B screens from 100 / 400 to 1,000 | every current run; PLAN:3; TR23:3, 54 | 8-32 | 1,000 | – | 350k | at N=16, "Continuing the campaign to 1,000 epochs did not solve the 350k feasibility problem" (TR23:54) | n/a (policy) | 7,000 epochs never run with binary weights (only H6, with HGQ weights) | current |
| H3 | Early stopping on val AUC (Round 14, patience 15) vs `es_patience 0` under EBOPs pressure | R13 XL:3769-3771; current runs XL:462 | – | – | – | – | "pressure makes val AUC fall by design; ES would truncate the front" (XL:3770) | n/a | – | both |
| H4 | Selection metric: best val AUC under budget (R0-R6) vs best val accuracy under budget (A/B series, confirmations) | ACC:27, 56; PLAN:56 | 8 | – | – | 350k | "The two objectives select different models": R2 had higher val AUC than R1 but lower accuracy (ACC:27) | n/a | accuracy selection was added to `ablation.py` on 2026-09-16 (ACC:56) | current |
| H5 | Knowledge distillation (R6: CE + 0.5·T²·KL, T = 2, teacher = the unconstrained pilot control) | ablations, XL:405, 413 (2026-09-12) | 8 | 898 of 1,000 at evaluation | 1 | 350k | held-out 56.9123 % / 0.841338 at 348,366, selected at one-based epoch 184 (ACC:19, 21; ABL:113, 116): lowest held-out accuracy of the seven arms | unverified; interim | the trainer hung 3 d 18 h on an idle GPU (`campaigns/2026-09-19-ops-incident-r6-hang/STUDY.md:15`); the teacher is the 1,780,910-EBOP β = 0 control (XL:484) | current |
| H6 | Sun et al. full recipe on Sun et al.'s own code, HGQ multi-bit weights (REPRO-CHANG): Adam defaults, LR 3e-3 cosine restarts, batch 2,790, 7,000 epochs | 8 runs xfm / xfmt × N, XL:3349-3362, 3314-3340 (2026-08-04/12); RC:18-27 | 8 / 16 / 32 / 64 | 7,000 | 1 (seed 42) | 350k | held-out acc xfm-n64 80.56 % at 348k, xfmt-n64 80.85 % at 318k; at or above the paper at all 8 points (RC:18-27) | unverified; selected on max held-out accuracy under 350k (RC:12), which is circular | weights are HGQ multi-bit, not binary; repo ≠ paper (h = 2, post-paper Linformer, open-loop β) (RC:8-10) | archived |
| H7 | TF32 off for reload-exact metrics | screen canary, XL:89-92 (2026-09-22) | – | – | – | – | "TF32-off restored accuracy exactly, but AUC still differed3.2e-7"; strict 1e-7 tolerance kept (XL:89-92) | n/a | – | current |

### I. Post-hoc changes on a frozen backbone

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| I1 | Output-logit offset correction (five class offsets; fit on 61,999 val events, select on 62,001) on the R2 checkpoint | accuracy investigation, ACC:30-40 | 8 | – | 1 checkpoint | 350k (backbone 329,838) | held-out 58.3131 % → 59.0600 % with 10-fractional-bit constants; +0.7469 pp [0.6424, 0.8514] vs its own model, +0.3169 [0.1629, 0.4709] vs R1 (ACC:34) | unverified; conditional single-seed event intervals | a class trade: g and W recall rise, q, Z, t fall; R1's own correction did not help (ACC:40) | current |
| I2 | Frozen final-classifier refit, 8-bit head (ridge multinomial on 100,000 train events) on the R1 checkpoint | ACC:44-50 | 8 | – | 1 checkpoint | 350k | held-out 59.1396 % / 0.855957 at 322,510 EBOPs; +0.3965 pp [0.3191, 0.4740] vs R1 (ACC:5) | unverified | mixed precision: 160 weights at 8 bits, so not an all-binary network (ACC:48); vs I1 the interval is −0.0719 to +0.2312 pp, not separated (ACC:50) | current |
| I3 | Frozen head with 4-bit weights; weaker ridge regularizer | ACC:46 | 8 | – | 1 checkpoint | 350k | "The 4-bit candidate lost validation accuracy"; the weaker regularizer "did not converge within 150 iterations and was excluded" (ACC:46) | failed | – | current |

### J. Synthesis-side methods that constrain training choices

| # | method | where tried | N | epochs | seeds | EBOPs target | outcome as recorded | status | mechanism or reason | era |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| J1 | Distributed arithmetic (da4ml) on the binary matmuls | XL:4998-5006 (2026-07-22); Job Alpha DA13, RES:374-377 | 10 (16 feat); 8 | – | – | – | binary dense LUT +34 %, FF 3.7× (XL:5000-5002); +21.9 % csynth LUT, ×2.94 FF on the 13 binary einsums (RES:376) | failed-with-mechanism (verified) | "CSD of ±1 is one nonzero digit per weight", nothing to share (XL:5003-5005) | archived |
| J2 | Global RF and PF-under-DATAFLOW folding | XL:5218-5222 (2026-07-16); RES:378; CHG:76-79 | 10 (16 feat); 8 | – | – | – | inlined ±1 weights do not fold: RF=10 binary dense identical to RF=8 (XL:5220-5221); maximum fold 0.7 % worse than RF=1 while II goes 1 → 48 (CHG:78) | failed-with-mechanism (verified) | folding does not deliver fit at whole-model scale | archived |
| J3 | SubLN on fabric (BIND_OP kernel remap) | XL:5258-5270 (2026-07-15) | 10 (16 feat) | – | – | – | DSP 6,900 → 1,764 with SubLN 5,136 → 0, but LUT 5.21M → 12.04M, SubLN 4.3× (XL:5260-5263) | failed-with-mechanism (numbers unverified, "pending", XL:5272) | the variance squares are about 36-bit multiplies (XL:5263-5264); the fix was to train norm-free (D10) | archived |
| J4 | Fabric multiply binding: solution-wide vs scoped to the DSP-carrying functions | Jobs Alpha / Beta, RES:348-360 | 8 | – | – | – | scoped binding keeps csynth DSP = 0, but Vivado then "demands 4,096 DSPs" from the attention-context products (RES:352-356) | failed-with-mechanism (verified at Vivado) | rule adopted: every zero-DSP claim is checked at Vivado, never at csynth alone (RES:358-360) | archived |
| J5 | In-graph β restoration (per-layer binary scale as a hardware affine) | export v5 (XL:3237, 2026-08-04); RES:362-365 | 8 | – | – | – | the 15 β-restore affines carry the fabric premium, ≈195-210 LUT per DSP shed (RES:362-365); checkpoint EBOPs omit them (RES:207-209) | verified | per-layer β is a real cost the EBOPs proxy does not count; norm-free carry sites needed an in-graph fix (XL:3279-3310) | archived |
| J6 | Attention token-axis fold (compiler lane E-C) | XL:4501-4507 (2026-07-25); gate XL:4211 | 10 (16 feat) | – | – | – | "THE ATTENTION FLOOR IS A SCHEDULING ARTIFACT": LUT 6.46× smaller, DSP exactly 10× fewer at II = 10 (XL:4501-4505) | verified (gate) | emitter frame only; "No new whole-model number quoted" (XL:4507) | archived |
| J7 | Whole-model synthesis beyond N = 8 | RES:95, 398 | 16 | – | – | – | "the RF=1 run died at 17.7 h"; N ≥ 16 not synthesized whole-model (RES:95) | failed | no silicon exists for N ≥ 16 | archived |
| J8 | Post-target synthesis of the R4 gradual checkpoint (hls4ml 1.3.0 → Vitis HLS 2023.2, VU13P, RF 1) | `campaigns/2026-09-17-synthesis-r4-gradual/`; R4HW:3-18; XL:217-223 (2026-09-17) | 8 | – | 1 checkpoint | 350k | C-sim bit-exact on 4,096 jets on both platforms; HLS failed in the frontend three times (R4HW:3, 13-16) | failed-with-mechanism | "ERROR: [HLS 200-642] The 'config_array_partition -maximum_size' command is not supported" — hls4ml 1.3.0 emits a directive Vitis 2023.2 removed (XL:220-222). No post-target silicon exists | current |
| J9 | hls4ml zero-grid ReLU fusion defect | XL:338 (2026-09-17); R4HW:30 | 8 | – | – | – | signed {−1, 0} after ReLU was emitted as unsigned {0, 0.5}; a guarded signed cast restores it (R4HW:30) | n/a (tool defect, fixed) | any learned-width model with collapsed channels can hit it | current |
| J10 | Exporter coverage for new architectures | PE-free (XL:195; ATT:43); Engram memory (XL:176; ENG:43); mixed-precision heads (PLAN:274) | – | – | – | – | PE-free checkpoints were not exportable at launch; "HLS export rejects unsupported memory" (XL:176); the strict all-binary gate rejects mixed heads (PLAN:274) | n/a (open gap) | a new arm is not a hardware candidate until its export path exists | current |
| J11 | Input-standardization affine in firmware | XL:5754-5757 (2026-07-13) | – | – | – | – | a standardized model needs 16 constant multiplies and 16 adds in front of `input_proj`, 0 DSP in the binary core (XL:5755-5756) | n/a | constraint on any input-transform arm | archived |

## Designed, never run (not "tried")

These exist as plans or code. None has a result; Delta may propose them without a "why it
failed" note, but should cite the plan.

- **The 2026-09-26 anchor study** (TB26:78-107): 7 arms × 8 seeds at N=64, A07 binary, Sun et al.
  recipe at 350k (A), 175k (B), 5M (C), our optimizer (D), Sun-sized architecture d24 / 2 heads /
  no PE (E), A07 without PE (F), our recipe (R). STUDY review v1 = ITERATE. Everything that
  first appears here is untried with binary weights: the pT ≥ 2 GeV constituent gate (not in
  our pipeline, CHG:150), the 90/10 split, 7,000 epochs, batch 2,790, peak LR 3e-3 and Adam defaults. Cosine restarts
  themselves ran once on binary weights: the R13 sighter (C2, LR 5e-5, batch 1024, 16 features)
  is the nearest prior to arm A, and it reached its 5e5 budget "~14 AUC pts below" its own
  unconstrained peak (XL:3690). Also untried: a binary network at the Sun et al. size
  ("Architectural parity is untested", CHG:210).
- **PLAN B-series B01-B14** (PLAN:106-121): activation total-width cap 8 and ranges [2,8], [3,8],
  [2,6] (B01-B04; "proposed semantics, not existing usable config fields", PLAN:123), softmax
  6 bits under a target (B06), gentler PID P 0.5 / I 0.01 (B08), grid freeze at epoch 300 (B09),
  distillation at the S0 architecture (B10), LR 4e-5 (B11), decay power 2 (B12), batch 512
  (B13), weight decay 0.001 (B14). Only B05 (softmax 8 bits) and B07 (target schedule) ran, as
  the executed B03 and B04; the executed B01 (one head) and B02 (no PE) came from PLAN:96, not
  from this table.
- **PLAN F-series on the finalists** (PLAN:133-138): F01-F03 ran only on R1 / R2 (I1-I3), never
  on A02 or A11.
- **PLAN H-series H00-H05** (PLAN:168-173): DSP caps 0 / 1 / 2.5 / 5 % and selective RF 2 / 4.
  Never run; blocked by J8.
- **Engram E04-E07 at N=16** (ENG:34; ERB:139-142).
- **R13 stages 1-2**: the matched binary / multi-bit / β = 0 / fixed-A8 comparison (XL:3694).
- **Ternary at the Round-14 architecture** via a `ternary_absmean` quantizer (proposed XL:3679-3682).
- **A 100k EBOPs target** (considered, XL:401-402; see E3).
- **Weight-width-matched PTQ control `fp32-s3-r14n8-wm-w5a8`**: built and C-simulated, "Ready to
  ship; nothing was run on mulder" (XL:501-526, 2026-09-03).

## Considered and rejected on argument (no run)

- `class_weight=balanced`: left off, factors 0.99-1.03 on near-balanced data (DEC:24).
- Scalar temperature scaling as a top-1 fix: "preserves argmax and cannot improve top-1
  accuracy" (ACC:32).
- Job Beta trained softmax-grid arms (BETA-0′, BETA-2/3/4): retired 2026-08-19 because the
  conversion lever alone could not close the fit gap (DEC:447-470); the same grids later ran as
  Job Gamma (E1).

## Not found in any record

Keyword search of `experiment-log.md` and `decisions.md` on 2026-09-27 (zero hits, or only
unrelated substring hits): dropout; label smoothing; mixup; weight averaging (EMA, SWA); any
optimizer other than Adam with weight decay (SGD, Lion); curriculum or progressive schedules
other than the target schedules of C7; binary-network STE variants (Bi-Real, ReActNet, IR-Net,
XNOR-style scaling, LSQ, PACT); latent-weight clipping; Linformer, Deep Sets or MLP-Mixer bodies
with binary weights (never implemented, CHG:184); tanh or other LUT activations (the Sun et al.
code uses `QAffinedUnaryFunctionLUT('tanh')`, CHG:43); particle type from the discrete
constituent mass (a dataset finding with no training arm, XL:3026-3040); any EBOPs-constrained
FP32 or W8A8 baseline; any binary N=64 run toward 350k longer than 50 epochs (INV:97-100).

**Data augmentation has never been run.** `BNJetTagAug` is the Round-14 W&B project name, created
because the input set changed (DEC:662), not an augmentation study.

## Lessons for new arms (from the rows above)

1. **Feasibility binds before accuracy at 350k.** Only N=8 has ever produced a feasible
   checkpoint (B4, C5-C8, D1). Every N ≥ 16 arm failed to reach its target: A04-A10, B00-B04 on
   three seeds, E00-E03, and all 18 N=64 screen arms (D2-D7, E2, F1-F3, C9). The only dynamic
   N=64 evidence is a truncated run with β at 1.8e-5 of a 1e-3 maximum (C9), so an N=64 arm at
   350k needs a static-floor gate first and a controller allowed to run long.
2. **A budget squeeze after an early unconstrained peak does not recover** (F1; D2; C3's 25 %
   arm). Gradual schedules did not prevent it at N=16 (C7). Select on validation only, among
   feasible checkpoints, and log the epoch at which the target is first met.
3. **Binary QAT is LR-fragile.** LR ≥ 2e-4 gave STE collapse at epoch 2-3 (H1); architecture
   "wins" at a too-hot LR were noise (D11); a 3-seed gain went flat at 6 seeds (D12). Every
   current-era EBOPs-constrained comparison with a feasible checkpoint is single-seed (B4, D1,
   R0-R6), so a gap below about a point is not interpretable yet.
4. **EBOPs is not silicon.** β-restore affines are uncounted (C1, J5), softmax has a fixed cost
   (E3), DA is negative on ±1 (J1), SubLN on fabric costs 4.3× LUT (J3), scoped binding re-infers
   DSPs (J4), memory cost logs 0 (F4). The one verified free lever, a 4-bit softmax output grid
   (E1), was never run under a target. Nothing without an export path (J10) is a hardware
   candidate, and no post-target silicon exists (J8).
5. **Measure the treatment, not the run.** R5's selected checkpoint predates its freeze (B5); R6
   was evaluated at an interim snapshot (H5); E01-E03 fail reload at 1e-7 (F2); val AUC and val
   accuracy select different models (H4); the N=64 5M target is post hoc (C10).

## Open threads (started, never concluded)

1. **Confirmations in flight.** N=8 A00 / A02 / A03 seeds 2-3 at 350k and N=64 A07 / E02 / E05
   seeds 2-3 at 5M (CONF:20-24). Last read: N=64 at epochs 279-299 of 1,000 (INV:91). No result;
   until they finish, no feasible current-era arm has more than one seed.
2. **E01-E03 reload failure.** Selected-checkpoint metrics do not reproduce at atol 1e-7; cause
   unresolved (ENG:47). The memory cost counter logs 0 (INV:93-96).
3. **No post-target silicon.** J8 is blocked on the hls4ml 1.3.0 directive; the one post-target
   synthesis campaign is unreviewed (DEC:19-20).
4. **Round-14 binary instability at N ≥ 32** is unexplained; the under-training hypothesis
   (CHG:208) is untested. The anchor study would be its first test.
5. **R5 and R6 do not measure their treatments.** R5's selected checkpoint predates the freeze
   (B5); R6 was evaluated at an interim 898-epoch snapshot (H5).
6. **Post-hoc fixes on one seed.** I1 and I2 were never repeated across seeds or on A02 / A11
   (ACC:68; PLAN:131).
7. **Val-AUC reproducibility gap** of up to 8.245e-5 between fresh CPU and historical selection
   values, unresolved (ACC:67).
8. **REPRO-CHANG** has no results-analyst pass, no AUC and no synthesis (XL:3320-3322).
9. **pT weighting follow-ups**: an end-weighted scheme and N=16 (PTW STUDY, Interpretation).
10. **The N=64 5M target date conflict**: memory files say "from 2026-09-10", the target first
    appears on 2026-09-24 (INV:114-119). Flagged by the investigator, not yet corrected.
11. **E1 (4-bit softmax grid) never re-run under an EBOPs target**, although it is the only
    measured way below the fixed softmax cost (E3).
12. **Exporters** for PE-free, memory and mixed-head models (J10).

## Log lines to append

For `.claude/memory/experiment-log.md`, top, in the house format:

```
## 2026-09-27 — What has this project already tried, and which of it failed for a known reason?  (campaigns/2026-09-26-delta; inventory)
Question:        Inventory of every training, architecture, quantization, EBOPs-control, input and recipe method run so far, so Delta does not re-propose a failed idea without saying why.
Design:          Read-only sweep of the logs, RESEARCH.md, campaign READMEs/STUDYs and publication/docs/current-work; numbers copied with file:line, none recomputed.
Result:          68 tried rows in ten families, 12 failed with a recorded mechanism (campaigns/2026-09-26-delta/inventory/tried-already.md).
Interpretation:  Two record corrections. (1) campaigns/2026-09-26-training-batch/STUDY.md:71 calls the pT-weighting BASE a "1,000 epochs" run; its config bnjettag/code/hgq2/configs/ptw-n8-20260925-base-w1a8.json:35,46 has epochs 101, es_patience 15 and no EBOPs block, so the 0.0019 accuracy sd is from the archived Round-14 recipe, not a constrained 1,000-epoch run. (2) BNJetTagAug is a W&B project name (decisions.md:662); no data-augmentation experiment exists in any record.
Ops-pointer:     —
```
