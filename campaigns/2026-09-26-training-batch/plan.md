# plan.md — 2026-09-26-training-batch (phase 1, experiment-designer)

**2026-09-28 GPU amendment (Kai):** the A10-only pilot/production choices in this notebook
are historical. Future production follows
[the measured GPU selection policy](../../docs/infrastructure/gpu-selection-policy.md),
with a new per-product canary and matched-product comparisons.

Crash-resilient notebook for the STUDY.md design. Newest notes at the bottom.

## What I will look up (done 2026-09-26)

- Methodology: `docs/methodology/03-phases.md` (Phase 1, owner protocol), `01-principles.md`,
  `appendix-checklist.md` (STUDY.md boxes).
- Conventions: all five files in `docs/conventions/`.
- Chang recipe: paper PDF (pdftotext, §2-3, Table 1), dossier `...fpga.md`, replication note
  `2510.24784_replication-targets_hgq2-examples.md`, code `reference-code/HGQ2-examples/jsc150/`
  (`run_train.py`, `data.py`, `tools/prepare_data.py`, `model.py:get_model`),
  `docs/chang-vs-bnjettag.md`.
- Our lineage: `campaigns/2026-09-22-constituent-screen/study-code.tar.gz` (extracted to the
  session scratchpad, read-only): configs `const0922-*-n64-*`, `bnhgq2/ablation.py`
  (runner: selection, checkpointing, LR), `bnhgq2/train.py` (loader, cosine_restarts in the
  Keras path only), `bnhgq2/data.py` (feature suffix match, input_std on train split),
  `bnhgq2/qat.py` (activation width bounds, fixed softmax width).
- Prior records: `.claude/memory/experiment-log.md` (2026-09-26 pt-weighting, 2026-09-24
  confirmation, 2026-09-22 screen, 2026-08-05/12 REPRO-CHANG), `.claude/memory/decisions.md`,
  `campaigns/2026-09-23-confirmation/README.md` + `n64-full-preflight-result.json`,
  `_attic/repro-chang/repro-chang/comparison.md`.
- Cluster facts: coordinator message 2026-09-26 (cluster-ops read-only check).

## Reference results found (each with source)

- Paper Table 1, N=64, test n=260,000, single model each: Deep Sets (HGQ) 79.4 %, Linformer
  79.8 %, MLP Mixer 79.7 %, MHA 77.9 % (collapsed to a Deep Set per §3). PDF text lines 249-264.
- REPRO-CHANG (our run of Chang's own code, HGQ weights, not binary): xfm-n64 80.56 % at 348k,
  xfmt-n64 80.85 % at 318k. Single seed 42, UNVERIFIED, and selected on test accuracy
  (comparison.md line 12) -> circular; context only. `_attic/repro-chang/repro-chang/comparison.md:23,27`.
- Our binary N64 under any EBOPs target: no verified number exists. The 50-epoch N64 screen at
  350k has no outcome in the artifacts I was given (live-status.json is a launch snapshot:
  A02-N64 epoch 1 at 35,777,122 EBOPs). N64 confirmation runs at 5M: in flight, unverified.
  A07-N64 initial EBOPs 24,816,782, 12,788 params (`n64-full-preflight-result.json`).
- Seed spread: N=8 W1A8 held-out accuracy sd 0.0019 (8 seeds, pt-weighting BASE, 101 epochs
  with ES patience 15, unconstrained; "1000 epochs" here was wrong, corrected 2026-09-27,
  experiment-log 2026-09-26). No N=64 spread under any EBOPs target exists.

## Arms (draft -> final in STUDY.md)

A Chang verbatim (Adam defaults) on A07-N64 at 350k; B = A at 175k; C = A at 5M; D = A with
our optimizer; E = A on Chang-sized arch (d24/h2/L1/FFN32/no PE); F = A with PE removed only;
R = our recipe (batch 256, LR 2e-5 poly, 1000 epochs, our optimizer) at 350k. All: pT gate,
90/10 split, no weights. 7 arms x 8 seeds = 56 runs.

## Decisions I am least sure of (mirrored in STUDY.md "Where I am not sure")

- base architecture A07 (current N64 confirmation arch) vs a00 flagship.
- "the way it's implemented" = target 5M (arm C) vs our recipe (arm R): both included.
- split 90/10 (fidelity) vs 80/20 (house).
- falsifier tolerance 1.0 pt below 79.4 %.
- truncation policy if canary projects > 14 days.

## Failed approaches / dead ends

- `research/bnjettag/results/repro-chang/comparison.md` path in the log does not exist; the
  file is at `_attic/repro-chang/repro-chang/comparison.md` (found by filesystem search).
- The N64 screen outcome (did any N64 arm reach <= 350k in 50 epochs?) is not in the local
  campaign directory; left as an open input for results-analyst / preflight.

## Status 2026-09-26 (end of phase-1 draft)

- STUDY.md written: 7 arms x 8 seeds = 56 runs, sections per template + checklist.
- Line citations into jsc150 verified against the file (run_train.py 21-37, 67, 92-93, 97, 104;
  data.py 22-26); first draft had them off by a few lines, corrected.
- Cheap-version cost first written as "a sixth"; recomputed as 16,000 / 336,000 run-epochs
  (about 1/21), corrected.
- Experiment-log stub prepended (Result: no result yet).
- Advisor review folded in: static EBOPs floor gate [A7], attention-alive diagnostic,
  resume rollback [A5], exact tie-break, validation-only readouts, seed-block pods.
- Second advisor pass folded in: [A12] failed-arm isolation (DIVERGED.json, skip on resume),
  W&B resume artifacts only at 500-epoch boundaries, check-3 "no consistency-with-record check
  possible" row, y-alignment gate against r14 N=64 arrays kept, R-crosses-GPU-type note.

## Fixer pass after review/STUDY_arbiter_v1.md (ITERATE), 2026-09-26

STUDY.md edited in place (ITERATE within the phase, not a regression ticket); change log under
the frontmatter. All 16 required fixes applied (#1-#15 and the C batch #16-#27).
- Recomputed before writing: r14 N=64 held-out accuracy (ddof 1) W1A8 0.6718/0.7264/0.6721,
  sd 0.0314; W1A6 sd 0.0168; FP32 0.7911 ± 0.0030 (matches arbiter). t(.975,7)/√8 = 0.836,
  t(.975,5)/√6 = 1.049, t(.975,3)/2 = 1.591; binomial SE at p 0.79: 0.164 pt (n 62,000),
  0.116 pt (n 124,000). 83 s → T_run 6.7 d; 190-245 s → 15.4-19.8 d.
- Screen bundle sha256 26f3cc40...5a45 recomputed; `ablation.py:278-287, 421-422` confirm the
  tie-break flip. `experiment.checkpoint_every_epochs` exists in configs but is never read
  (only `remote_every_epochs` is), so [A15] wires the existing key.
- [A13] prefers an explicit `cost_before_auc=False` override to dropping `engram_study`:
  `run_study.py:29`, `check_engram.py:147`, `run_engram.py` index `cfg['engram_study']`
  directly and would KeyError.
- Fidelity table: Chang transformer weights are `b0=4, f0=4, SAT_SYM` (`model.py:186`),
  overriding `get_model`'s `b0=7`; activations `f0=7`, `ic=MinMax(0,12)`, `beta0=0`.
- Tried and changed: a Holm family of three with p-values for all three claims; the budget
  claim is a count rule with no natural p-value, and a McNemar-plus-count stability rule was
  unreachable at 4-0 (exact one-sided p 0.0625). Final: budget and stability are count rules;
  Holm over the two p-values (recipe, stability) as a robustness label.
- Disputed fact (screen N=64 at 350k) not settled here: written as PREFLIGHT gate [A16].
- prose_lint: score 0, 0 em-dashes (one "robust" hit reworded).

## Fixer completion pass, 2026-09-27 (report: review/STUDY_fixer_v1.md)

- Audited all 27 arbiter items against STUDY.md; #1-#14 and #16-#26 already in place.
- #15: Seeds section now states the A − F pairing rule ([A17]); it was only in the tables.
- #13/#27: [A16] and "Where I am not sure" point to review/STUDY_investigation_350k.md
  (W&B only; PVC not read). #27 wording corrected: the 5M reason is recorded
  (CONFIRMATION_RUNS_20260924.md:26) and post hoc; date conflict with project-context.md and
  decisions.md (2026-09-10 vs first appearance 2026-09-24) left to Kai, not edited.
- Added "Downstream use": method-atlas treats this study as wave 0 anchor.
- Experiment-log stub Design line: investigator pointer and wave 0 anchor appended.
- Observed a concurrent writer on STUDY.md/plan.md at 00:01-00:02 (model.py:184 → 186 fix);
  my edits were string replacements and applied cleanly.

## ml-engineer code plan (phase 2 staging, 2026-09-27)

Scope from the coordinator brief: stage code only, under `code/`. No PREFLIGHT.md, no
ConfigMap, no cluster, no commit. STUDY.md is being amended in parallel after review v2
(arbiter fix 1 = [D19]/[A20]); this plan builds against the arbiter's fix list and the
current [A1]-[A19].

### Step 1 answer: [A20] on the pinned HGQ2 0.1.9, no pin change needed

Read from the pinned wheel (`.venv-hgq2/.../hgq`, `_version.py` = 0.1.9; same version as
`requirements-training.txt`), not from Chang's 6cdc6e3 code:
- WRAP, trainable KIF datalane quantizer: `FixedPointQuantizerKIF` (`fixed_point_quantizer.py`)
  has the WRAP-trainable branch (i tracked by `get_minimal_i`, i not trainable, f trainable),
  and `bits` = `b` = relu(i+f) when `overflow_mode != 'SAT'`; so a channel can cost 0.
- Learned softmax-output width: our attention is QEinsum + QSoftmax, not QMultiHeadAttention;
  the softmax output enters A·V through `attn_iq` (`qat.py:496-499`). Replacing that fixed
  config with a trainable WRAP KIF datalane config is a config object, available in 0.1.9.
- Learned `place='table'` quantizers with bc >= 4: `QuantizerConfig('kbi', 'table', ...,
  bc=Min(4))`; `hgq.constraints.Min` exists in 0.1.9 (imported by `quantizer/config.py`).
  QSoftmax (0.1.9) forces tables to SAT, RND_CONV, k0=0, so bits = b >= 4.
- Softmax exp input: Chang's MHA default is `QuantizerConfig(place='datalane',
  overflow_mode='SAT')` (0.1.9 `mha.py:69`), forced per-tensor by QSoftmax. SAT keeps k=1, so
  this costs >= 1 bit per score entry (H*T*S), a term the arbiter's 326,656 omits. Traced
  below, not assumed.
- What 6cdc6e3 needs beyond 0.1.9 (`StopIf`, `QLinformerAttentionT`) is a callback and a
  Linformer layer; neither is part of [A20]. Answer: **feasible on the pin**.

## Kai's brief (recorded 2026-09-27, critical v2 C4)

As relayed to the designer by the orchestrator on 2026-09-26 (voice note; no primary copy of
the note exists in the repo; `campaigns/2026-09-26-method-atlas/BRIEF.md:14-19` records the
same brief except the pod count): the Sun et al. recipe ("replicate his code basically", "keep
the conditions the same") on our binary model; N = 64, 7,000 epochs, batch 2,790, LR 3e-3 with
cosine restarts every 500 epochs, pT >= 2 GeV gate, no class or sample weights, EBOPs target
enforced; "some at a lower EBOPs limit", some "the way it's implemented", "some with a changed
architecture"; "a couple of pods".

## Fixer pass after review/STUDY_arbiter_v2.md (ITERATE), 2026-09-27

STUDY.md edited in place; change log entry dated 2026-09-27. Fixes 1-10 applied.
- [D19] added (Chang quantizers in every arm), [A7] rewritten (0-bit and 1-bit-alive floors),
  [A20] added, [L8] added, fidelity rows added, old-quantizer floor block added. Floor numbers
  are the arbiter's arithmetic; I recomputed the softmax floors (326,656 / 163,328), headroom
  (23,344 / 186,672, ratio 8.0) and the ratios to 350k; the dense/Q·K/A·V columns are quoted.
- Timing re-sourced from live-status.json (read myself: a07-n64 100.09 s, e02-n8 83.53 s,
  a02-n64 189.68 s). 112.6 s scaled; T_run 8.1 / 9.1 d; R 31.3 h, ≈ 63 pod-hours; 8 pods
  ≈ 1,750 pod-hours; P = 2 ≈ 36 d. The "83 s → 6.7 d; 190-245 s → 15.4-19.8 d" note in the
  v1 fixer section above is superseded (83 s is N=8, 190 s is A02, 245 s has no source).
- Canary is canary plus epoch-500 pilot; C′-s1 replaces F-s1 (orchestrator addition), with a
  one-seed descriptive C′ rule and a C′-only fallback if [A20] needs a pin change.
- B moved to E architecture at 250,000 ([D6] amended); E − B replaces A − B in the Holm set.
- Stability is a count rule; McNemar two-sided p reach 0.125/0.0625/0.031/0.016 at 4-7 vs 0.
- Fig. 2 per-class AUCs: legend values from research-log 2026-08-04 (pdftotext panel order
  is scrambled; values match the legend strings), means 0.9532 / 0.9428 recomputed.
- Orchestrator correction folded in: the N=8 sd 0.0019 lower bound is the pt-weighting BASE
  arm, 101 epochs, ES patience 15, batch 256, no EBOPs block (VERIFY.md header; config
  ptw-n8-20260925-base-w1a8.json), not 1,000 epochs; STUDY and this plan corrected.
- Written: `campaigns/2026-09-23-confirmation/UPSTREAM_FEEDBACK.md` (#19). Experiment-log top
  entry header and Design line updated. method-atlas BRIEF not edited (another session owns
  it); the needed change is in the fixer's return.
- Seen, not resolved: the concurrent ml-engineer note above says Chang's softmax exp input
  is SAT per tensor (k = 1), which may add a term to the arbiter's 326,656 floor; STUDY keeps
  the arbiter's number labelled "expected, confirmed by [A7]".

### Step 2: [A20] implemented; static floors traced (CPU, synthetic sample; not results)

`static_floor.py` (patch 0002) on a fresh build per mode, native HGQ2 `trace_minmax`, 256
synthetic standard-normal jets (the floor depends on widths only). Every learnable width is
asserted after the final trace. Sanity: the same tool's init trace of A07 under the current
quantizer gives 24,816,782, equal to `campaigns/2026-09-23-confirmation/n64-full-preflight-result.json`.

| arch, quantizer | 0-bit floor | arbiter | 1-bit-alive | arbiter | gap, explained |
| --- | ---: | ---: | ---: | ---: | --- |
| A07, current (SAT, fixed softmax) | 4,580,398 | 4,559,008 | = 0-bit (SAT floor is 1 bit) | - | +21,390 (+0.47 %): the QUnaryFunctionLUT table term sum(2^b_in * b_out) * 1e-4 (exp 20,133 + inv 1,258), `hgq/layers/activation.py:63-67` |
| A07, [A20] | 343,053 | 326,656 | 1,005,741 | 989,344 | +16,397 (+5.0 %): exp-table input is SAT (jsc150's MHA default), so k = 1 bit per score entry, H*T*S = 16,384, plus the LUT term 13 |
| E (d24 h2 FFN32 no PE), [A20] | 171,526 | 163,328 | 619,198 | 611,000 | +8,198 = 8,192 + 6, same mechanism |
| F (A07 no PE), [A20] | 343,053 | - | 1,005,741 | - | PE costs no EBOPs |
| E, current | 2,701,439 | 2,690,744 | = 0-bit | - | +10,695, LUT term |

All residuals are named terms; none unexplained. Consequence: A07 headroom at 350k under [A20]
is **6,947 EBOPs**, not 23,344; B on A07 at 175k stays STATIC_INFEASIBLE; E at 175k has 3,474
headroom, E at 250k has 78,474. Making the exp input WRAP (not jsc150's choice) would lower the
A07 floor to 326,669. FLAG for the designer.

Also found: under the current SAT quantizer, a channel at i = ic.min, f = fc.min is billed
1 bit (k) by EBOPs but HGQ2 0.1.9 inference outputs exactly 0 (`FixedPointQuantizerBase.call`,
`where(k+i+f > 0, ...)`). The reviewers' "sign-only live channel" reading is wrong at inference;
the channel is silent and over-billed (unit test `test_channel_floor[SAT]`).

### Step 3: patch series (code/patches/, applied in code/tree/, rebuilt by code/apply.sh)

Base: screen bundle sha256 26f3cc40...5a45; `run_study.manifest()` on it reproduces the source
sha 7f9e9307...74d7 with the pins (CPU, 2026-09-27). Every key is opt-in; absent keys give the
screen build byte for byte (regression on const0922 a07/b02 N64, a00/b03 N8: EBOPs, kernel
hashes, predictions, widths, LR, config digest identical).

| # | patch | STUDY item | test |
| --- | --- | --- | --- |
| 0001 | `quant.act_overflow` WRAP, `quant.softmax_quant` chang; width records for WRAP/KBI | [A20] | tests/test_a20_quantizer.py |
| 0002 | `static_floor.py` 0-bit / 1-bit-alive floors | [A7] | asserted widths in the tool |
| 0003 | `train.lr_schedule` chang_cosine_restarts (own code from [D2]); `train.optimizer` adam_default | [A1] [A2] | tests/test_schedule_optimizer.py |
| 0004 | `experiment.cost_before_auc`; `experiment.keep_auc_selected_feasible` | [A13] [A19] | tests/test_selection.py |
| 0005 | `arch.pt_gate_gev` in cache, Ph loader, ROC-test loader; split from config; cache without order seed | [A3] [A4] [D8] [D9] | tests/test_pt_gate.py |
| 0006 | `checkpoint_every_epochs` honoured; `snapshot_every_epochs`; ghost snapshots dropped on resume | [A15] [A5] [A6] | tests/test_resume_cadence.py |
| 0007 | DIVERGED.json + exit 3; W&B finished on divergence/crash; run_pack isolation, retry, log tail, skip markers; env roots | [A12] | tests/test_run_pack.py, test_resume_cadence.py |
| 0008 | export of `pos_enc none` (zero PE table) | brief | tests/test_export_no_pe.py |
| 0009 | `campaigns/chang0926/generate.py`: 56 configs, index, seed-block packs, canary, cache spec, A-s1 diff | [A18] arms table | cpu_gate |
| 0010 | `check_pairing.py` | [A17] | UNPAIRED without 0011 |
| 0011 | `arch.pos_enc_none_consume_rng` (F arms) | [A17], FLAG | PAIRED seeds 1, 2 |
| 0012 | `evaluate_roc.py` | [A11] | tests/test_eval_loader.py |
| 0013 | `cpu_gate.py` | CPU gate | PREFLIGHT_ALL_PASS |
| 0014 | `ebops_crosscheck.py` (staged, not run) | [A14] | blocked locally |

Flagged decisions (default taken, designer or Kai to confirm):
- WRAP datalane bounds are jsc150's (ic MinMax(0,12), fc MinMax(-24,24)); rounding stays RND_CONV.
- Softmax output width is per element (h, t, s) under channel granularity (jsc150 per value).
- Softmax exp input stays SAT as in jsc150 (costs 16,384 EBOPs at the A07 floor); WRAP would
  lower the floor to 326,669.
- Learned tables and softmax-internal inputs init at the fixed grids (b 12, i 1; exp i6 f3; inv
  i4 f8), so a fresh [A20] model is forward-identical to the fixed build at init; jsc150 inits
  tables at b0 7, i0 0. MonoL1(act_bw_l1) on table b and i (jsc150: MonoL1 1e-8).
- "8-bit init" = the calibrated i + f = 7 of the current code; under WRAP the sign bit drops and
  i is re-traced, so A07 starts at 13.18M EBOPs (synthetic trace), not 24.8M.
- order_seed = 2026092600 + s. Arm B generated as in current STUDY (A07, 175k,
  STATIC_INFEASIBLE); canary pack as in current STUDY (includes B-s1). Arbiter fixes 3 and 4
  would change both; one dict entry each in generate.py.
- F uses the RNG placeholder (0011) so A-F is paired; without it A-F is Welch.

Not staged (owner elsewhere): job template env (BNJ_DATA_ROOT, BNJ_RUN_ROOT,
BNJ_CAMPAIGN_DIR), podFailurePolicy and deadline [A10]; the cache build on the PVC [A4]; the
PVC read for [A16] and [A3] value ranges (recorded by the cache builder in data_info.json);
the W&B project BNJetTag-ChangRecipe must exist and be PRIVATE before `--track`; the attention
entropy diagnostic (REPORT tool).

### Gates run locally (CPU, synthetic inputs; nothing here is a result)

- Unit tests: `pytest tests/` in the staged tree, 34 passed.
- `campaigns/chang0926/cpu_gate.py` on the final series: 56 `CONFIG_PREFLIGHT_PASS` lines and
  `PREFLIGHT_ALL_PASS 56` (`code/evidence/cpu_gate_final.log`); reload max abs diff 0.0 for
  every config (tolerance 2e-6, re-traced EBOPs equal). Printed params, seed 1:
  A, B, C, D, R `params 61951 kernel_bias_pos 11653`; E `params 31735 kernel_bias_pos 6253`;
  F `params 59903 kernel_bias_pos 9605` (`params` is Keras count_params, which includes
  quantizer width variables). An earlier full run (superseded, same result) predates the 0003
  rewrite, which changed only the schedule's code, equal at every tested epoch.
- Regression (screen configs, patched vs base): identical. `apply.sh` rebuilds `tree/`
  exactly. Source manifest sha of the staged tree: 5b606b61faa6b9f0ba75d39cd834227134f542371ebe1e34a96ff0a8295f306b
  (base 7f9e9307...). Not shipped, not committed.

### FLAG (blocks the canary until the designer answers): WRAP ranges come from 256 jets

`compute_ebops` runs `trace_minmax(reset=True)` on `xt[:256]` every epoch before the candidate
is saved, so every WRAP quantizer's integer bits in the validated and selected checkpoint cover
only those 256 jets; larger validation or held-out activations wrap (sign flip) at inference.
Under SAT this was harmless (i trainable, untouched by tracing). CPU check on A-s1 at init,
synthetic heavy-tailed standardized pT (`code/evidence/wrap_trace_check.py`, not a result):
re-tracing on 4,096 rows instead of 256 raised i in 6 of 14 WRAP quantizers (max +1), changed
the logits of 2.0 % of 4,096 other rows (argmax of 0.6 %), and EBOPs went from 13,613,261 to
14,307,533. Options: make the trace sample a config knob (for example the full train split or
a fixed 8,192 rows; `quant.calib_n 8192` is not read by any code on this path), or add a
range guard. Either raises EBOPs honestly. Not changed silently; STUDY confound 10 also names
the 256-jet trace.

## ml-engineer code plan, part 2 (after review/STUDY_arbiter_v3.md, 2026-09-27)

Scope: arbiter v3 fixes 2, 3, 5, 6 on the code side; patches 0015+ under `code/`. No
PREFLIGHT.md, no ConfigMap, no cluster, no commit. STUDY.md is at da0e4ee (not yet amended
for [D21]); the generator follows the arbiter's fix list and is marked PENDING where STUDY
must confirm. Recovery: a previous attempt was cut off in patch 0017; its three commits
(trace sample, stored reload check, overflow diagnostic) and an uncommitted certification
draft were found in the session scratchpad, rebuilt without bytecode files and re-tested
here before use.

### Fix 6: [A7] floors of E1 and the paper's >= 1-bit attention rule (CPU trace, not results)

`static_floor.py` (patch 0018) gains modes `attn_narrow` (Q.K and A.V datalane streams held
at 1 bit: `*_attn_scores__in0/1`, `*_attn_ctx__in0/1`) and `attn_full` (plus the inputs of
Wq, Wk, Wv); every other width at the 0-bit floor; every width asserted after the final
trace. The weights-only reading adds nothing: kernels are binary (fixed 1 bit) and a dense
with a 0-bit input costs 0 EBOPs, so that floor equals the 0-bit floor. Sample: 256
synthetic standard-normal jets, fresh build per mode, [D19] quantizers.

| arch | 0-bit (= weights-only) | 1-bit-alive | narrow datalane | full datalane |
| --- | ---: | ---: | ---: | ---: |
| A07 (d32 h4) | 343,053 | 1,005,741 | 605,197 | 801,805 |
| E (d24 h2) | 171,526 | 619,198 | 368,134 | 478,726 |
| E1 (d24 h1) | 85,763 | 533,435 | 282,371 | 392,963 |

Headroom (budget minus floor; negative = infeasible):

| arch | budget | 0-bit | 1-bit-alive | narrow | full |
| --- | --- | ---: | ---: | ---: | ---: |
| A07 | 350k | 6,947 | -655,741 | -255,197 | -451,805 |
| A07 | 250k | -93,053 | -755,741 | -355,197 | -551,805 |
| E | 350k | 178,474 | -269,198 | -18,134 | -128,726 |
| E | 250k | 78,474 | -369,198 | -118,134 | -228,726 |
| E1 | 350k | 264,237 | -183,435 | 67,629 | -42,963 |
| E1 | 250k | 164,237 | -283,435 | -32,371 | -142,963 |

- The arbiter's A07 605,197 / 801,805 and E 368,134 / 478,726 are confirmed exactly.
- Per-head additivity: only the softmax term scales with heads (E1 85,763 x 2 = 171,526, residual
  0, including the LUT table term). Q.K and A.V do not: at fixed d_model, H x (d/H) is constant,
  so E1's scores and ctx terms equal E's (98,304 each). The arbiter's E1 projection
  (282,371 / 392,963) is therefore also exact.
- E1 builds (`n_heads 1`, `qat.py:390` E = D // H = 24). Params (Keras count_params, includes
  quantizer width variables): A07 61,951, E 31,735, E1 19,447.
- E1 has real headroom (264,237 at 350k, 1.48 x E's), so E1-s1 takes the pilot slot, not B-s1.
  Under the narrow datalane reading, E1 at 350k is the only feasible arch (67,629 headroom).

## Fixer pass after review/STUDY_arbiter_v3.md (ITERATE, iteration 3), 2026-09-27

STUDY.md edited in place (ITERATE, not a regression ticket); change-log entry added. Pre-edit
copy kept in the session scratchpad only. Kai's launch-gate answers (decisions.md, 2026-09-27
08:40 PDT) arrived mid-pass and are folded in: [D19] and [D21] confirmed, 8-10 pods one wave,
arms H and NB requested (not designed here; experiment-designer, second wave pending code).
- #1 non-degeneracy (a)-(c) in Selection rule, budget claim, recipe branches, [D6], [D13], sd
  gate, pilot; formula fixed, p_maj value computed at PREFLIGHT ([A21]). Mechanics: checked on
  model_best, so the runner's selection is unchanged.
- #2 [D21] written (applied on the orchestrator's instruction, then Kai-confirmed): A, B, D,
  F, R on E (F = E + learned PE); C on A07 at 5M; old A07 arm A is A07-350. Arms table,
  comparisons, confounds 5/6/8, Seeds pairing, Holm set, figures, pods (K=6 block A, B, C, D, F,
  A07-350; K=3 split A, B, D / C, F, A07-350), cheap version, [D1] [D4] [D6] [D16] [D18] [A7]
  [A17] amended. Expected R branch restated as "none" (old argument came from the A07 screen).
- #3 pilot recomposed; E1 conditional; placeholders `[[E1-TRACE-PENDING: ...]]`.
- #4 fidelity row, paper-rule static finding (sums of traced terms, arbiter table), [L2]
  sentence, Kai row. #5 [A21] gate citing ablation.py:450/515/521; fidelity row "WRAP range
  update"; [D20] one trace per epoch. #6 E1 trace: ml-engineer, pending. #7-#10 sentences.
- C #11-#18 applied; per-sentence [A7] tags dropped from running prose (kept in tables, [D]/[A]).
- Recomputed: 0.836·√2·3.1446 = 3.72 pt; 343,053/350k = 0.980, 171,526/350k = 0.490; E path
  1,536 + 1,536 + 4,096 = 7,168 = 4.0 % of 178,474; 6,947/2,048 = 3.39; E init 8,965,267 from
  static_floors_trace_step2.json.
- prose_lint: score 0, 0 em-dashes.
- Not done (routed): generator regeneration for [D21] (A/B/D/R on E with the RNG flag, F with PE,
  A07-350, pilot pod) and the 8-seed [A17] check on the new pair → ml-engineer; [A21] → ml-engineer;
  atlas BRIEF anchor wording → atlas owner; arms H and NB → experiment-designer.

## designer: arms H and NB (Kai request, 08:40; 2026-09-27)

Brief: add Kai's two reference arms as a pre-registered second wave (decisions.md 2026-09-27
08:40 PDT; STUDY arbiter v3). Do not touch `[[E1-TRACE-PENDING: …]]`; no code, no launch, no commit.

Looked up (2026-09-27):
- `reference-code/HGQ2-examples/jsc150/model.py`: `get_transformer` (xfm) = d24 input dense
  (QEinsumDenseBatchnorm, ReLU), tanh LUT, `QMultiHeadAttention(2, 16)`, FFN 32 → 24, GAP,
  32/32/32 head; weights kbi SAT_SYM b0 4 (scope in `get_transformer`), scope0 kbi i0 0, MonoL1
  1e-8 on f and i, i_decay_speed 1e-3; datalane kif WRAP f0 7, ic MinMax(0,12), value-wise
  (`homogeneous_axis=(0,)`); tables bc Min(4); `LayerConfigScope(beta0=0)`. `get_llformer`
  (xfmt) needs `QLinformerAttentionT`; the module imports it at top level.
- `run_train.py`: `KERAS_BACKEND=jax`, seeds hard-coded 42, `Dataset(..., shuffle=True)`,
  `PieceWiseSchedule` β, `StopIf(ebops < 1e4)`, `ParetoFront(val_acc > 0.5, ebops < 5e5)`,
  Adam defaults, cosine restarts (alpha_steps 10 → 490-epoch cosine, = [D2]).
- `data.py`: features `[5, 8, 11]` of `150c-*.h5`, gate `>= 2`, standardization on train + val,
  float16 cast, val_size 0.1.
- HGQ2 0.1.9 on the pin (`.venv-hgq2`, same as `code/tree/requirements-training.txt`):
  QAffinedUnaryFunctionLUT, QEinsumDenseBatchnorm, QMultiHeadAttention, QSum, QAdd,
  QGlobalAveragePooling1D, QDenseT, QSALTAttention, BetaScheduler, PieceWiseSchedule, FreeEBOPs,
  ParetoFront, BetaPID present; **StopIf and QLinformerAttentionT absent** (grep of the wheel).
- Job-YAML pins: TensorFlow 2.21.0, keras 3.15.0, hgq2 0.1.9; no JAX pin; screen jobs set
  `KERAS_BACKEND=tensorflow` (`campaigns/2026-09-22-constituent-screen/screen-job.json`).
- REPRO-CHANG (`_attic/repro-chang/repro-chang/comparison.md`): xfm-n64 80.56 % at 348k, seed 42,
  test-selected, unverified, JAX, hgq2 0.1.10.dev; no wall time recorded (job YAML: "wall time
  unknown → 48 h ceiling").

Decisions (all flagged in STUDY "Where I am not sure"):
- H = xfm (`get_transformer`). xfmt/Linformer cannot build on the pin; the paper's Linformer
  would be new layer code and a pin question.
- H β control = our PID at 350k, the [D5] block (paper's method, same controller as A and NB, so
  H − NB does not also carry a controller difference). Alternative: open-loop PieceWiseSchedule
  (the code; only REPRO-CHANG shows the model trains under it).
- H EBOPs = the [D20] quantity, traced on a per-epoch **clone** (his live dynamics kept, the
  candidate is the traced clone). Alternative: live-model reset trace as A.
- NB = A with only A's binarized kernels switched to kbi learned width, config copied from a
  built jsc150 xfm on the pin. A − NB paired if an [A17]-style kernel-hash gate passes at 8 seeds.
- Multiplicity: second-wave Holm family {A − NB, H − NB}; H − A = (H − NB) + (NB − A) is the
  algebraic sum, reported with its Welch interval, no p (06-review §6.4 independence).
- Weight-type claim: falsifier direction only (A − NB interval entirely below 0, Holm-adjusted);
  1.0-pt "close" line descriptive only, as the 78.4 % line.
- §6.8: H has no binding reference (77.9 % is h = 1 and collapsed; 80.56 % is single-seed,
  test-selected); H − 77.9 and H − 80.56 descriptive.
- Pods: wave 2 = 16 runs, 4 seed-pair pods at K=4 (H-s, H-s+1, NB-s, NB-s+1). Overlap with
  wave 1 gives 14 concurrent pods, above Kai's 8-10: flagged. Cheap version: NB alone, 8 seeds.

Arithmetic (recomputed, scipy): t(0.975,14)·√(2/8) = 1.072, × 3.1446 = 3.37 pt (Welch 8 vs 8 at
the archived sd); paired at zero correlation 3.72 pt; sd_diff for a ±1.0-pt paired half-width
1.20 pt; T_run at 112.6 s = 218.9 h = 9.12 d; 16 runs at K=4 = 876 pod-hours (projection); NB
alone 8 runs at K=4 = 438 pod-hours.

### Fix 5: [D20] as staged (patches 0015-0017, 0019, 0023)

- **Trace sample.** `train.ebops_trace_sample: "train_full"` makes every `compute_ebops` in
  `run_training` (initial, per epoch, final delivered) a `trace_minmax(reset=True)` over the whole
  training split (n = 558,000 expected from the 90/10 gated cache; training rows only, validation
  never enters a range). Replaces `xt[:256]` at the screen's `ablation.py:450` (sample), `:515`
  (per-epoch trace) and `:521` (post-reload retrace). The 256-row `sample` survives only for the
  engram `epoch_observer`, unused here. Absent key: byte-identical to the screen.
- **One trace per epoch.** `train.ebops_reload_check: "stored"` replaces the post-reload second
  trace by a byte comparison of every variable of the reloaded candidate (kernels, PE, every
  quantizer i/f/b/k, each layer's stored `ebops`) and requires the stored per-layer sum to equal
  the traced total. Same reduction as `trace_minmax` (sum of `int(layer.ebops)` over
  `enable_ebops` layers, hgq2 0.1.9 `utils/minmax_trace.py`).
- **BetaPID reads the traced EBOPs, not FreeEBOPs.** hgq2 0.1.9 `BaseBetaPID.get_ebops` sums
  the stored `layer.ebops` of top-level layers; BetaPID has no per-batch hook, and the runner calls
  `pid.on_epoch_end` after the trace, which wrote those values last. Under the key the runner
  asserts `pid._ebops` equals the traced total (rel 1e-6) every epoch and logs the pre-trace
  in-training value (`ebops_in_training`, what FreeEBOPs would report) beside it; the CPU gate
  asserts `model_ebops == traced` on all 58 configs.
- **i_decay_speed.** Every WRAP datalane quantizer of the [D19] set has `i_decay_speed = 0.01`
  (hgq2 `kif_datalane_default`; our `QuantizerConfig` does not set it). jsc150 sets `1e-3` for all
  quantizers (`get_model` scope0, q_type and place "all", `model.py:278-286`, HGQ2-examples
  6cdc6e3). In training, i follows `max(i - i_decay_speed, i_batch)` per step, so ours can shrink
  up to 2 bits per 200-step epoch where Chang's shrinks 0.2; the per-epoch full-split reset trace
  then sets the saved i. Recorded per run (`i_decay_speed.json`, `ebops_budget.json`); NOT
  changed (FLAG below). C-PRIME (SAT) has no WRAP quantizer, so nothing to record.
- **Certification before ROC-test.** `certify_ebops.py`: fresh reload of each checkpoint
  `evaluate_roc.targets` lists (or the epoch-500 snapshot files for the pilot), reset retrace on
  the full training split, CERTIFIED iff retraced EBOPs = logged (rel <= 1e-6), stored sum = logged,
  and <= target. Stored widths alone are not equivalent: they prove the file is the logged one,
  not that the logged number came from a full-split trace (a 256-row run would pass), so the
  retrace stays; the stored sum is recorded beside it. `evaluate_roc.py` refuses a file with no
  CERTIFIED record for its sha256.
- **Train+val sensitivity.** `certify_ebops.py --trainval-dir` retraces a copy on train + val
  (Chang's `trace_and_save` convention), saved outside the run dir; `evaluate_roc.py --trainval-dir`
  evaluates it labelled `__trainval_retrace`, "sensitivity, not primary"; never selects anything.
- **Overflow diagnostic.** `bnhgq2/wrap_overflow.py` counts, per WRAP datalane quantizer, live
  elements whose rounded input falls outside the stored range (0-bit elements reported as pruned);
  `evaluate_roc.py` records it for validation and ROC-test beside every evaluation.
- **Trace cost (CPU, this laptop, synthetic, not the GPU number).** On 16,740 rows, one reset trace
  at batch 2048 takes 0.66 x one training pass at batch 2790 for E (2.96 s vs 4.51 s) and 0.66 x for
  A07 (5.51 s vs 8.29 s). Linear scale to 558,000 rows: E ~99 s trace vs ~150 s training per epoch;
  A07 ~184 s vs ~276 s. `trace_minmax` runs the model eagerly per batch, so on GPU the ratio may be
  worse than on CPU. If the GPU ratio is similar, s_e rises by up to ~1.66x over the screen's (whose
  two 256-row traces were negligible), which bears on the 14-day timing basis. The canary must
  measure the trace share of s_e (patch 0023 logs `ebops_trace_seconds`, `ebops_reload_check_seconds`
  and `ebops_trace_over_epoch` every epoch under the key; the cheap levers are
  `train.ebops_trace_batch` and, if the designer accepts it, a fixed-size trace sample).
  Evidence: `code/evidence/trace_cost_cpu.json`.

### Fix 1 (code side): non-degeneracy condition (patch 0020)

Opt-in `experiment.nondegenerate = {zero_floor_ebops, se_multiple: 5}`. Feasible iff EBOPs <=
target AND EBOPs - zero floor > 0 AND val accuracy > p_maj + 5 * sqrt(p_maj (1 - p_maj) / n_val),
with p_maj and n_val from the class counts of the `y_val` the run uses (fixed at run start in
`nondegenerate_rule.json`, re-checked on resume). Budget met but not both others = "feasible,
degenerate": counted (`feasible_degenerate_epochs`, `first_feasible_degenerate`), never
`model_best`, never the [A19] copy. `ebops_above_floor` is in every jsonl record, W&B log and
`[epoch]` print line, and in each selected point. Naming: under the rule, the per-epoch
record's `budget_met` means non-degenerate feasible and `ebops_budget_met` is the raw EBOPs <=
target test; `ebops_budget.json`'s `budget_met` stays raw (delivered checkpoint EBOPs <= target).
Renaming would touch the no-keys path, so it is documented instead. The threshold **cannot be computed here**: the
gated 90/10 cache exists only after the PVC cache build. `nondegenerate_threshold.py --cache DIR`
prints it at PREFLIGHT (cluster-ops), from the same function the runner uses.

### Fix 2 / 3: [D21] configs and the pilot (patch 0021; PENDING STUDY)

Kai confirmed [D21] on 2026-09-27 (decisions.md); STUDY.md at da0e4ee does not yet carry it, so
the generator is marked PENDING. A07-350 has 8 seeds from arbiter v3 fix 2 (56 = 7 x 8); STUDY
does not yet state it. **Question for the designer: confirm 8 seeds for A07-350.**

| arm | arch | target | optimizer / schedule | quant | 0-bit floor | above-floor headroom | job indices | files |
| --- | --- | ---: | --- | --- | ---: | ---: | --- | --- |
| A | E (d24 h2, no PE, consume_rng) | 350,000 | Chang | [D19] | 171,526 | 178,474 | 0-7 | chang0926-a-n64-s{1..8}.json |
| B | E | 250,000 | Chang | [D19] | 171,526 | 78,474 | 8-15 | chang0926-b-n64-s{1..8}.json |
| C | A07 (d32 h4, learned PE) | 5,000,000 | Chang | [D19] | 343,053 | 4,656,947 | 16-23 | chang0926-c-n64-s{1..8}.json |
| D | E | 350,000 | ours / Chang schedule | [D19] | 171,526 | 178,474 | 24-31 | chang0926-d-n64-s{1..8}.json |
| F | E + learned PE | 350,000 | Chang | [D19] | 171,526 | 178,474 | 32-39 | chang0926-f-n64-s{1..8}.json |
| R | E | 350,000 | ours / ours (1,000 ep) | [D19] | 171,526 | 178,474 | 40-47 | chang0926-r-n64-s{1..8}.json |
| A07-350 | A07 | 350,000 | Chang | [D19] | 343,053 | 6,947 | 48-55 | chang0926-a07-350-n64-s{1..8}.json |
| C-PRIME (pilot only) | A07 | 5,000,000 | Chang | current (SAT, fixed softmax) | 4,580,398 | 419,602 | 56 | chang0926-cprime-n64-s1.json |
| E1 (pilot only) | E, 1 head | 350,000 | Chang | [D19] | 85,763 | 264,237 | 57 | chang0926-e1-n64-s1.json |

Packs: 8 seed blocks `{A, B, C, D, F, A07-350}` (K = 6) plus R on 2 pods (4 each)
(`packs.json`); pilot pod `[0, 1, 24, 48, 56, 57]` = A-s1, A-s2, D-s1, A07-350-s1, C-PRIME-s1,
E1-s1 (`pilot_packs.json`; `canary_packs.json` is the same pod for the `--stop-after 2` canary).
E1-s1 takes the last pilot slot, not B-s1 (fix 6: 264,237 headroom). Every config also carries
the [D20] keys and the non-degeneracy block with its arm's floor from `static_floors.json`
(`trace_floors.py`; `generate.py` refuses a stale entry by an arch+quant signature).
Params (Keras count_params, includes quantizer width variables / kernels+biases+PE):
A, B, D, R 31,735 / 6,253; F 33,271 / 7,789; C, A07-350 61,951 / 11,653; C-PRIME 12,788 / 11,653;
E1 19,447 / 6,253.

### Gates run locally (CPU, synthetic inputs; nothing here is a result)

- `pytest tests/`: 47 passed after 0023 (34 earlier + 13 new: d20 trace 4, reload check 2, overflow 1,
  certify 1, non-degeneracy 5).
- `cpu_gate.py`: 58 `CONFIG_PREFLIGHT_PASS`, `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`
  (`code/evidence/cpu_gate_d21.log`); reload max abs diff 0.0 on every config (tolerance 2e-6);
  PID-read EBOPs = traced, stored reload check = traced, zero floor re-traced = config value.
- [A17] `check_pairing.py --arms a,b,d,r --seeds 1..8`: A, B, D and R each PAIRED with F at all 8
  seeds (only `pos_enc/pos_table` differs, 0 of 15 shared kernels differ).
- No-new-keys regression on const0922 a07/b02 (N64) and a00/b03 (N8), fresh bundle extract vs
  staged tree: init level (EBOPs, kernel hashes, predictions, widths, LR, digest) identical, and a
  2-epoch `run_training` on synthetic rows (per-epoch records minus wall time, every variable of
  every saved checkpoint, file list) identical.
- `apply.sh`: bundle 26f3cc40 + patches 0001-0023 = `tree/` (APPLY_MATCHES_TREE).
- Staged-tree source manifest sha256 (`run_study.manifest()`):
  cb161e21b1c423d3b182279086c54e71700cc834fc52afbeef49d2d09af7d8eb (after 0023; the gate and
  pairing runs predate 0023, which touches only `run_training` logging; tests and the
  run_training regression were re-run after it). Not shipped, not committed.

### FLAGS (designer or Kai)

1. i_decay_speed 0.01 (ours, hgq2 default) vs 1e-3 (jsc150). Drift from the recipe, not
   deliberate; it changes in-epoch range tracking and could move EBOPs and accuracy. Not
   changed; a one-line opt-in quantizer key would realize 1e-3 if the designer wants fidelity.
2. Trace cost: up to ~1.66x s_e if the CPU ratio holds on GPU; the canary measures it.
3. Non-degeneracy threshold: computed in-pod at PREFLIGHT; not available locally.
4. A07-350 seed count (8) and the whole [D21] table await the STUDY amendment.
5. Arms H and NB (Kai, 2026-09-27) are not in this series; they need new code (H port, a real
   `kbi_learnable` path) and are a second wave per the orchestrator default.

### Patch list (0015-0023, each opt-in and separately reviewable)

| # | patch | item |
| --- | --- | --- |
| 0015 | `train.ebops_trace_sample` / `ebops_trace_batch`; PID-reads-traced assert; `ebops_in_training` logged | [D20] |
| 0016 | `train.ebops_reload_check: "stored"` (one trace per epoch) | [D20] |
| 0017 | `bnhgq2/wrap_overflow.py` per-quantizer overflow fraction | [L8]/[D20] |
| 0018 | `static_floor.py` attn_narrow / attn_full modes, headroom at 350k/250k | fix 6 |
| 0019 | `certify_ebops.py`; `evaluate_roc.py` certification gate, overflow on val/ROC-test, train+val sensitivity, pilot rows skipped | [D20] |
| 0020 | `experiment.nondegenerate`; `i_decay_speed` record | fix 1, [D20] |
| 0021 | generator [D21]: 56 production + 2 pilot-only configs, packs, pilot pod, `static_floors.json`, `trace_floors.py`, `nondegenerate_threshold.py` | fix 2, 3 |
| 0022 | `cpu_gate.py` for the [D21] set; `check_pairing.py --arms` | CPU gate, [A17] |
| 0023 | per-epoch trace timing in the log | fix 5 (canary trace share) |

## Fixer pass after review/STUDY_arbiter_v4.md (ITERATE, iteration 4), 2026-09-27

Text only; the change map is the STUDY change-log entry "revised after `review/STUDY_arbiter_v4.md`".
- [D25] conditional: at the time of this pass `code/patches/` ended at 0023 and no generated config
  carried `quant.i_decay_speed`, so the fidelity row, [D25] and [A21] were reworded as the PREFLIGHT
  gate (patch 0024 sets it; PREFLIGHT asserts 0.001 on the listed arms and 0.01 on C′). If 0024
  lands, those lines can return to "set". [D25] logged at the top of `.claude/memory/decisions.md`.
- Line citations checked against the staged tree: `ablation.py:438-450` (trace sample), `:546`
  (d20 opt-in), `:639` (stored check), `:664` (feasible), `:683-685` (model_best), `:686-692`
  ([A19]), `:698-703` (PID assertion), `:711`/`:719` (`budget_met` / `ebops_budget_met`);
  `certify_ebops.py:82, 107` read `ebops_trace_batch`; binary kernel billed 1 bit by `_binary_kq`
  (`qat.py:228-229`), absmean β outside EBOPs (`qat.py:56-65`).
- Sizing table recomputed (scipy t): t(0.975, n−1)/√n = 0.836 / 0.635 / 0.533 / 0.497 / 0.468 at
  n = 8 / 12 / 16 / 18 / 20, so sd_diff ≤ 1.20 / 1.57 / 1.88 / 2.01 / 2.14 pt for ±1.0 pt.
- Not done here, routed: moving A − A07-350 out of the Holm family (arbiter #25) is a design change
  for experiment-designer (a note was added, the family is unchanged); the WRAP-overflow label
  threshold (physics v4 C6) needs a value chosen before PREFLIGHT by experiment-designer.
- Experiment-log top entry for this campaign updated (stale "still traces 256 jets", [D25]
  staging, "arbiter sums confirmed exactly", selection sentence, budget-claim wording). No number
  changed.

## ml-engineer patch 0024: [D25] `quant.i_decay_speed` (2026-09-27; staged, not committed, not shipped)

- `bnhgq2/qat.py`: optional `quant.i_decay_speed` (finite float > 0; raises unless
  `act_overflow == "WRAP"`). After the model is built, `set_i_decay_speed` assigns it to
  `_i_decay_speed` on exactly the quantizers `ablation.i_decay_speeds()` enumerates. It adds no
  variables and draws no RNG. With the key absent, nothing runs, so the HGQ2 default 0.01 stays.
- `generate.py`: `QUANT` gets `'i_decay_speed': 0.001`, so A, B, C, D, F, R, A07-350 and E1 carry
  it (57 configs). C-PRIME (`CURRENT_QUANT`) is unchanged byte for byte. NB and H have no
  generator rows in this series ([A22] not built). NB inherits the key through `QUANT` when its
  row is added, and the gate assertion covers it then.
- `cpu_gate.py` ([A21] assertion): with the key, every recorded value equals float32(0.001)
  (0.0010000000474974513), before and after the training step and after save/reload, and the
  enumerated set covers every `i_decay_speed` weight in the model. Without the key (C-PRIME),
  the record must be empty and the model must have no `i_decay_speed` weight. **Correction to
  the brief's "0.01 for C′":** C′ has no WRAP quantizer, so no quantizer carries the knob
  (`cpu_gate_d21.json` already recorded `{}` for it). The gate therefore asserts "no key, no
  carrier, empty record", not a value of 0.01.
- `tests/test_i_decay_speed.py` (9 tests): key sets every enumerated quantizer; without the key
  the value is 0.01 and the only variables that differ from a keyed build are the
  `i_decay_speed` weights; a SAT config with the key raises; bad values raise; save/reload
  preserves the value.

Gates (CPU, synthetic; not results). Evidence in `code/evidence/*d25*`; `cpu_gate_d21.*` is kept
as pre-[D25]:
- `pytest tests/`: 56 passed (47 + 9).
- `cpu_gate.py`: `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`. `I_DECAY_OK`: 57 configs at
  0.001 on 14 quantizers each; C-PRIME has `config None quantizers 0 values []`. Max reload diff
  0.0 (tolerance 2e-6). Against `cpu_gate_d21.json`, only the `i_decay_speed` field changed.
  Params, initial EBOPs, one-step loss, EBOPs after one step and kernel hashes are identical.
  Params (count_params / kernel+bias+PE): A, B, D, R 31,735 / 6,253; F 33,271 / 7,789; C,
  A07-350 61,951 / 11,653; C-PRIME 12,788 / 11,653; E1 19,447 / 6,253.
- [A7] floor retrace (`trace_floors.py`): every mode (zero / one / attn_narrow / attn_full) of
  every arm equals the pre-[D25] `static_floors.json`. Only `floor_signature` changed, because
  `quant` changed. For example A 171,526 / 619,198 / 368,134 / 478,726; E1 85,763 / 533,435 /
  282,371 / 392,963.
- [A17] `check_pairing.py --arms a,b,d,r --seeds 1..8`: all 32 PAIRED. The evidence JSON is
  equal to `a17_pairing_d21_8seeds.json`.
- No-new-keys regression (const0922 a07/b02/a00/b03; fresh bundle extract vs staged tree): the
  init-level run (`regress.py`) and the 2-epoch `run_training` run (`regress_train.py`) are
  IDENTICAL. The base rerun equals the recorded `regression_base.json` and
  `regression_run_training_base.json`.
- `apply.sh`: bundle 26f3cc40 + 0001-0024 = `tree/` (APPLY_MATCHES_TREE).
- Persistence through training: the runner's per-epoch trace is the same `compute_ebops`
  (HGQ2 `trace_minmax`) the gate calls. `_reset_minmax` only tests whether `_i_decay_speed`
  exists and never writes it. A 2-epoch keyed `run_training` on E1 (synthetic rows) recorded
  0.001, and every saved `.keras` (min_ebops, unconstrained, validation_candidate) reloads with
  0.001 on 14 quantizers.
- Staged-tree `run_study.manifest()` sha256: **ac5a5c867c6e06957bf17079b210532ee34989276edc51ffc1f539f195d895b2**.
  It was cb161e21 before 0024; the same method on the pre-0024 tree reproduces cb161e21. The
  manifest hashes `*.py` only (top level and `bnhgq2/`). Configs are pinned by
  `config_sha256` in `campaigns/chang0926/index.json`.
- Repo HEAD 358c19d. The campaign directory is dirty: `code/patches/0024-*`, 65 files under
  `code/tree/`, `code/evidence/*d25*`, and this file. Not committed.

## Cluster-ops handoff (from the code's point of view)

1. **Env roots.** `run_study.py` / `run_pack.py` default to the 2026-09-22 screen, so set
   these explicitly:
   - `BNJ_DATA_ROOT` (cache at `$BNJ_DATA_ROOT/n64/data`; suggested `/data/chang-n64-20260926`,
     `cache_configs/n64.json` `cache.root_suggestion`);
   - `BNJ_RUN_ROOT` (runs at `$BNJ_RUN_ROOT/runs/<name>`);
   - `BNJ_CAMPAIGN_DIR` = the directory holding `index.json`, `configs/` and the pack files
     (`campaigns/chang0926/` inside the shipped tree).

   `run_study` sets `BNHGQ2_CODE_SHA256` from `manifest()`. `prepare_cache.py` reads that
   variable, so export it for the cache job. Optional: `BNJ_ARM_RETRIES` (2),
   `BNJ_STALL_SECONDS` (1800), `BNJ_STAGGER_SECONDS` (15). The screen template also exports
   `TF_FORCE_GPU_ALLOW_GROWTH=true` and `NVIDIA_TF32_OVERRIDE=0`. The code does not set GPU
   memory growth itself, so K processes per GPU need that variable.
2. **W&B.** Configs name `wandb_project` `BNJetTag-ChangRecipe`, entity
   `kayamaguchi-uc-san-diego`, group `chang-n64-20260926`. `WANDB_PROJECT` / `WANDB_ENTITY` in
   the environment override the config, and `run_engram.validate_tracking_destination` then
   refuses to start. So do not copy the screen template's `WANDB_PROJECT=BNJetTag-Engram-Experimental`:
   set it to `BNJetTag-ChangRecipe` or leave it unset. The same check requires
   `WANDB_MODE=online` and that the project already exists with access `PRIVATE`
   (queried through the W&B API). Create it and verify it before the canary.
3. **Gated 90/10 cache on the PVC** ([A3]/[A4]/[D7]/[D8]):
   - Command: `prepare_cache.py --configs <dir containing only cache_configs/n64.json> --root
     /data/chang-n64-20260926 --n-parts 64 --raw /data/hls4ml_lhc_jet/train/train`. The
     `--configs` default is the old batch20260917 directory.
   - Built-in asserts: 62 raw files; raw shape (N_RAW, 64, 3); float32 finite; one-hot labels;
     split sizes; array sha256 in `data_info.json`; `pt_gate_gev` 2.0, `validation_split` 0.1,
     `split_seed` 1; `order_seed` null.
   - Range checks for PREFLIGHT, read from `data_info.json`:
     - `pt_gate_stats`: `pt_nonzero_min`, `pt_max`, `n_negative_pt` (expect 0: raw GeV, not
       ptrel), `n_newly_gated_slots`, `n_jets_all_gated`;
     - `sort_stats.n_jets_top_n_reordered`: the [A3] fraction our sort permutes;
     - `y_class_counts`.
   - `run_engram.load_cache` re-checks hashes, gate, split and one-hot labels at every start.
4. **Non-degeneracy threshold:** `python campaigns/chang0926/nondegenerate_threshold.py --cache
   /data/chang-n64-20260926/n64/data --out <file>` prints `NONDEGENERATE_THRESHOLD {p_maj, se,
   val_accuracy_threshold = p_maj + 5 SE, class_counts, labels_sha256}`. It refuses a cache whose
   gate, split or seed differs from the configs.
5. **Packs:**
   - canary: `canary_packs.json` = pilot pod `[[0, 1, 24, 48, 56, 57]]` (A-s1, A-s2, D-s1,
     A07-350-s1, C-PRIME-s1, E1-s1), `run_pack.py canary_packs.json 2`;
   - pilot: `pilot_packs.json`, the same pod;
   - production: `packs.json`, 10 packs. Packs 0-7 are the seed blocks {A, B, C, D, F,
     A07-350} (K=6); packs 8-9 are R s1-4 and R s5-8 (K=4). `JOB_COMPLETION_INDEX` selects the
     pack.
6. **Pod resources per arm at batch 2,790** (what the code fixes; GPU memory is not measurable
   here):
   - One process per arm.
   - Each process holds the full gated train split on the GPU (`make_epoch_step` converts `xt`
     and `yt` to tensors): 558,000 x 64 x 3 float32 = 428.5 MB, plus labels and the unused
     teacher zeros (558,000 x 5 x 4 B x 2 = 22.3 MB). That is about 0.45 GB per arm before
     activations at batch 2,790.
   - The [D20] per-epoch trace runs over the full split at `ebops_trace_batch` 2,048.
   - The cache is mmap'd on the host, so page cache is shared across arms.
   - STUDY §Pods: about 2 CPU and 6 Gi host memory per arm (`bnjettag.io/arms-per-pod`, rule
     PACK). The screen template pins `OMP_NUM_THREADS=2`, `TF_NUM_INTRAOP_THREADS=2`,
     `TF_NUM_INTEROP_THREADS=1`.
   - Whether K=6 fits one GPU at batch 2,790 is what the canary measures (STUDY: split to K=3 if
     not).
7. **PREFLIGHT placeholders left for cluster-ops:** `nrp_doctor.py lint` output, ConfigMap name,
   and the shipped bundle sha256. The shipped bundle must contain patches 0001-0024 (manifest
   ac5a5c86).

## Fixer, STUDY arbiter v5 (2026-09-27)

Text-only pass on `STUDY.md`, arbiter v5 fixes 1-7 in the order 5, 4, 1, 2, 3, 6, 7, with the
arbiter's verbatim wording; the change-log entry "revised after `review/STUDY_arbiter_v5.md`"
lists every site. Fix 5 landed first, for PREFLIGHT's [A21] check: C′ carries no
`i_decay_speed` key and records an empty set (`code/evidence/cpu_gate_d25.log:116`), not 0.01.
Checked: `static_floors_arms_s1_d25.json` A07-350 `one.per_layer` (6,144 / 3 = 65,536 / 32 =
2,048; head_fc1 1,024 / 32 = 32); scipy thresholds 1.196 / 1.574 / 1.877 / 2.011 / 2.137 pt,
rounded down; `ablation.py:711, 779, 803, 806` for `budget_met`. Also edited: one dated correction line
under the [D25] Check line in `.claude/memory/decisions.md`; the campaign's experiment-log entry
([D25] text, overlap pods, header). Kai's second set of answers were recorded in "Where I am not
sure". Nothing tried failed. Not done: the FP32 E arm design (experiment-designer); #18
sign-flip logging (ml-engineer option).
Neighbourhood (advisor catch): STUDY second-wave Overlap bullet, its FLAG block and pod-count row updated for Kai's overlap answer; experiment-log Holm list corrected (A − A07-350 out of Holm, per STUDY since the v4 designer follow-up).

## Fixer, STUDY arbiter v6 (2026-09-27)

Text-only pass on `STUDY.md`, arbiter v6 fixes 1-9 and 11 with the arbiter's verbatim wording,
plus fix 10's STUDY text ([A26] entry, "softmax tap" replaced, pilot readout prints entropy as
"pending" if the script is not ready). The [A26] script and its tests are ml-engineer's, written
in parallel, not by this pass. The change-log entry "revised after `review/STUDY_arbiter_v6.md`"
lists every site with post-pass line numbers. Checked: `a17_pairing_d25_8seeds.json` records
`n_shared` 15; `act_overflow` and `act_calib` exist as config keys in `code/tree`; the archived
FP32 79.1 ± 0.3 % is the reference-table row; gate line 66/64 = 58/56 plus [A25]'s 8 configs.
Neighbourhood: the NB K=7 Overlap bullet and the K=8 clause now point to the K=7 re-canary;
frontmatter `question:` and Bearing aligned with fix 3; the fidelity `i_decay_speed` row splice
fixed beside l. 393's. Also: designer [D26] entry in `.claude/memory/decisions.md` (above the
Delta rename entry); Delta rename (relayed) in "Downstream use" and the [A22] citation.
`prose_lint` score 0 after the pass; `E1-TRACE-PENDING` 0. Not edited: the experiment-log
entry (no number changed; three stale wording copies listed for the orchestrator), PREFLIGHT.md,
manifests, code. Nothing tried failed.

## ml-engineer, [A26] and PREFLIGHT gate v1 fixer + re-freeze (2026-09-27)

Plan: (1) finish [A26] from the partial `code/analysis/`; (2) patch 0025 (post-pause check,
flag 1), patch 0026 (W&B id and group by `BNJ_STAGE`, flags 3/6), each with a CPU test;
(3) readout CPU Job (flag 4); (4) one re-freeze; (5) PREFLIGHT build-half text (flags 2, 5, 7, 8).
Done:
- [A26]: the partial script was complete. Added the bundle-path fallback in the test and a main()
  test on an epoch-500 snapshot layout: 7 passed, 2 skipped. The renormalized-entropy definition
  is logged in `decisions.md` (the docstring cited an entry that did not exist).
- 0025: `ablation.selected_checkpoint_ebops`, and `run_study.verify_selected` (the post-pause
  block, callable without a GPU; `train` keeps the GPU/TF32 asserts), used also in `run_engram`.
  4 tests. The legacy 256-row retrace gives 95,388 vs logged 110,972 (synthetic).
- 0026: `wandb_util.run_stage/stage_run_id/stage_group`. A tracked run with no stage is refused.
  4 tests.
- Patches were made as `format-patch` in a scratch repo (0025 = final minus the 0026 hunks);
  `apply.sh` gives `APPLY_MATCHES_TREE`. `pytest tests/` gives 64 passed.
- Freeze: `freeze.py` ships `code/analysis/`, sets `BNJ_STAGE=pilot`, and emits `readout-job.json`.
  Bundle 77f1ca4e..., ConfigMap `kai-chang0926-code-77f1ca4e9f`, manifest f7d4003f....
  - Extracted-bundle gate: `PREFLIGHT_ALL_PASS 26 production 24 pilot_only 2`, lines identical to
    c5d6f02a.
  - Bundle pytest: 71 passed, 2 skipped.
  - Lint: OK on 3 Jobs, no WARN.
Flagged, not resolved: STUDY l. 1442-1443 run-id text (fixer); CPU vs GPU certification device
(PREFLIGHT flagged decision 6). The `attn_entropy.py` docstring's example `--out` path differs
from the readout Job's path; it is only an example, and changing it is not worth a bundle.
Nothing committed, nothing applied.

## 2026-09-27 fixer text pass after PREFLIGHT gate v2 (PASS with B flags)
- STUDY: run-id amendment (l. 1473-1480, patch 0026, `BNJ_STAGE=production` for production);
  CPU→GPU certification re-run rule cited from decisions.md (l. 1288-1296, l. 799-801);
  pre-epoch-500 CPU dry run of the whole readout (l. 1297-1301); cross-class replay re-run rule
  (l. 1302-1306); change-log entry "v6, text pass after PREFLIGHT gate v2".
- PREFLIGHT: commit status (15506d7 / 6278d24), ConfigMap created and verified, open item 1 done,
  do-not-rebuild-cache caveat (`ablation.py:591/:297`, `prepare_cache.py:137`), readout emptyDir
  24Gi vs ephemeral 12Gi noted for ml-engineer (manifest untouched), STUDY line refs re-pointed.
- Not touched: RUN.md, manifests, code, decisions.md (its 0026 bullet still says "fixer amendment
  due"). prose_lint: STUDY and PREFLIGHT score 0. Nothing committed.

## 2026-09-27 fixer pass after STUDY arbiter v7 (ITERATE, nine text-only B)
- STUDY: arbiter v7 fixes 1-9 at the listed sites, fix 1 ([A26] row-renormalized entropy) first;
  line numbers in the new change-log entry (STUDY l. 254-280); fix 1 neighbourhood: pilot readout entropy item (l. 1345). Verbatim arbiter text, reflowed.
  Site choices: fix 3 splits the first-wave secondary-gaps paragraph after "counts only."; fix 7
  figure clause joins the NB weight-width item with a semicolon; fix 6 continues the Bearing
  paragraph. Neighbourhood beyond fix 9f: "(line numbers at 54bf3e7)" on the FP32-E designer
  entry, "(line numbers at 5c49230)" on the PREFLIGHT gate v2 entry.
- Experiment-log header of this campaign tagged "revised after STUDY arbiter v7"; Ops line untouched.
- Open for the designer: l. ~1468 still expects `PREFLIGHT_ALL_PASS 66 production 64` beside a
  shipped-bundle gate of 26 / 24 / 2 (fix 9g text applied verbatim, the 66/64 not touched).
- Not touched: RUN.md, PREFLIGHT.md, manifests, code, decisions.md. prose_lint STUDY score 0.
  Nothing committed.

## 2026-09-27 fixer pass after STUDY arbiter v8 (ITERATE, four text-only B, required C (a)-(h))
- STUDY: arbiter v8 fixes applied in the order 2, 3, 1, 4, 5 at the listed sites; change-log
  entry at STUDY l. 281-297, "(line numbers at the working tree after this pass on fba27d5)";
  the orchestrator replaces that basis with the commit sha at commit. STUDY now 2,353 lines.
- Fix 4 numbers re-checked (scipy noncentral t, df 7, α 0.05 two-sided): power 0.803 at
  1.16 · sd_diff; 1.16 × 4.448 = 5.16, × 1.19 = 1.38, × 1.0 = 1.16 pt.
- Site choices: 5f legends tagged "(arbiter v8 fix 5f)" at both per-class ROC sites; 5g second
  half (no text given) worded "external reference single-model with no interval; its noise is
  unpublished, [L1] puts its scale at about 1 pt or more (arbiter v8 fix 5g)" beside the A − 79.4
  headline; 5c deleted the Direction sentence in the first Holm copy only.
- Experiment-log top entry of this campaign: header tag, Design (pilot amendment, collapse label,
  K=3 pod count, detectable gap). Ops lines untouched.
- Not touched: RUN.md, PREFLIGHT.md, manifests, code, decisions.md. prose_lint STUDY score 0.
  Nothing committed, nothing launched.

## 2026-09-27 fixer pass after STUDY arbiter v9 (ITERATE, iteration 9; regime-B amendment)

Placed before the ml-engineer regime-B section, which was still being written. STUDY.md only
(no RUN.md, PREFLIGHT.md, manifest or code edits; nothing committed or launched).
- Fix 1(a)-(i): the "[D15] branch executed" paragraph after "Trace-cost risk", every listed
  [D20] / Selection / Budget / pilot / Pods / [D15] / [D16] / Kai-row / FLAG site, and the
  change-log entry with line numbers at the working tree (base c2f5447). Slots T, C and P are
  filled from "Answers for the STUDY amendment" below and cited to `code/tree/bnhgq2/ablation.py`
  as staged when read (is_traced_epoch :483-487; split PID assertion :765-775; selection only on
  traced epochs :721-763). These line numbers must be re-checked at the bundle freeze if the tree
  changes again. Cited file: `code/tree/bnhgq2/ablation.py` sha256 a26ea580ae08b9123db80266812428a150e16e31db3d4bf3802fc4d1b1a953f3
  (mtime 2026-09-27 14:57 PDT).
- Slot T consequence: there is no epoch-1 trace, so the canary pair is the pre-training trace
  (`initial_ebops`) and the end of epoch 10 (the arbiter's allowed fallback, stated in STUDY).
  This is a weaker test than epoch 10 against epoch 1 (init EBOPs sit far above any trained
  epoch). Flagged for v10 / Kai; a traced-against-traced pair (epochs 10 and 20) would extend the
  canary, a design change the fixer did not make.
- `ebops_trace_every: 10` was not yet in `campaigns/chang0926/generate.py` when read; STUDY says
  so and leaves the confirmation to the PREFLIGHT addendum.
- Not in STUDY: DECISION R-B3 (packing alpha, 14 pods, R packed with E seed blocks) conflicts with
  STUDY's "about 13 pods" and "R packs separately"; ml-engineer notes it needs the STUDY amendment.
  The fixer did not adopt it (a packing choice, Kai's decision); STUDY fixes the pod map at
  PREFLIGHT from the regime-B pilot's measured memory.
- Fix 2: the verbatim `ablation.py:754-755` / `:783` citations are the 77f1ca4e bundle's; a note
  says patch 0027 adds loss and both trace fields to the log line (`:838-842` as staged).
- Fixes 3 and 4(a)(b): verbatim. prose_lint on STUDY.md: score 0 (2 em-dashes, both the quoted
  RUN.md section title "Canary — W&B history pull").
- Propagated to the campaign's top entry in `.claude/memory/experiment-log.md` (header and Design
  line; Ops lines untouched).

## ml-engineer, regime B (Kai [D15] decision 2026-09-27, decisions.md top entry)

Brief: patch 0027 `train.ebops_trace_every: k` (opt-in), log-line fields (physics v9 B2), regime-B
configs (k = 10 on every [D20] config), K=5 production packs, two regime-B pilot manifests
(K=5 and the arbiter v8 K=3 pod), re-freeze, full gates, CPU dry run of the epoch-500 readout.
Started from HEAD 5276ee0, campaign directory clean. The regime-A pilot `kai-chang0926-pilot-77f1ca`
runs on bundle 77f1ca4e: nothing it uses on the cluster is touched; its local manifests
(`pilot-job.json`, `readout-job.json`) stay as they are.

### Answers for the STUDY amendment (experiment-designer reads these)

**Which epochs are traced.** Zero-based epoch e is traced iff e == 0, (e + 1) % k == 0, or
e + 1 == epochs (the last epoch is always traced, so the delivered selection includes it; 7,000 and
R's 1,000 are multiples of 10 anyway). The epoch-0 trace is **not** needed for initialization (the
full-split reset trace before training, `initial_ebops`, does that, unchanged); it was first left
out and then **added** on the coordinator's request (STUDY slot T, arbiter v9: the canary compares
the traced end of epoch 1 with epoch 10, not the pre-training trace with epoch 10). With k = 10
the traced epochs are 1, 10, 20, ..., 7,000 in one-based numbering: 701 traces in a 7,000-epoch
run, 101 in R, and the ends of epochs 1, 10, 500, 1,000, 2,000, 4,000 and 7,000 are all traced
(`tests/test_trace_every.py::test_key_semantics` asserts that set).

**(a) What BetaPID reads on untraced epochs: the in-training value.** hgq2 0.1.9
`BetaPID.on_epoch_end` sets `_ebops = get_ebops()`, the sum of the stored `layer.ebops`
(`beta_pid.py:163-166`), and `on_epoch_begin` of the next epoch feeds that to the PID. Every
`training=True` call of a quantized layer overwrites `layer._ebops` from its current i/f
(`layers/core/base.py:95-103`). With no trace between the last training step and
`on_epoch_end`, the PID therefore reads the in-training EBOPs of the last step, which is the
number jsc150's `FreeEBOPs` logs (`ebops.py`: the sum of `layer._ebops` over enable_ebops layers).
That option is closer to jsc150, so it is the implemented one, and it needs no plumbing: the code
just does not trace. The stale value from the last trace would need an override of `pid._ebops`
and would feed the PID a number up to 9 epochs old. Caveat for the amendment: jsc150's
`run_train.py:88` uses `BetaScheduler` (a fixed β schedule), not `BetaPID`. The *number* matches
FreeEBOPs; the controller is still our [D5] PID. The runner asserts `pid._ebops ==
model_ebops(model)` (the in-training value, read before any trace) on untraced epochs.
On traced epochs the order is unchanged (trace, then `pid.on_epoch_end`), so the PID reads the
traced value there, as in regime A (see DECISION R-B1).

**(b) WRAP ranges between traces: yes, HGQ2's in-training tracking.** Between two traces each WRAP
datalane quantizer follows i <- max(i - i_decay_speed, i_batch) per training step
(hgq2 0.1.9 `FixedPointQuantizerKIF.call`), with `i_decay_speed` 1e-3 on every [D19] arm ([D25],
`I_DECAY_OK` 0.001 on 14 quantizers) as in jsc150 (`model.py:285`). C′ (SAT) has no WRAP quantizer.
The remaining deviation from jsc150: every k-th epoch `trace_minmax(reset=True)` resets the
ranges of the live model to the full-split min/max, and training continues from those ranges.
jsc150 never traces during training (only `trace_and_save` after it). The reset is what makes the
traced epoch's candidate certifiable, so it stays.

**(c) Checkpoints and selection under k = 10.** Unchanged cadence: full checkpoint every 25 epochs
([A15]), snapshot every 500 ([A6]), W&B artifact every 500. Selection candidacy (all four
`SELECTED_FILES`: `model_best`, `model_best_auc_feasible` [A19], `model_min_ebops`,
`model_unconstrained`), the feasibility test, the non-degeneracy counters and the
`recovery_after_epochs` freeze are evaluated only at traced epochs. The selected file is written
at the traced epoch itself: `shutil.copy2(validation_candidate.keras -> model_best.keras)` in the
run directory, as today. The next 25-epoch checkpoint (e.g. 25 for a selection at 10 or 20) copies
the selected files into `checkpoints/epoch-NNNN/`, and a resume restores them from there. So the
25/10 mismatch costs nothing: the selected checkpoint never depends on a full checkpoint landing
on a traced epoch. The candidate save, reload and validation still run every epoch (STUDY
l. 1325-1327 option text: "candidates saved every epoch but the feasibility test applied only on
traced epochs"), which keeps the [A12] non-finite validation check every epoch. New asserts:
`snapshot_every_epochs % k == 0` (500 % 10 == 0), so every snapshot, and the epoch-500 readout,
falls on a traced epoch.

**(d) Assertions that change.** `ablation.py` PID assertion (the "PID reads traced EBOPs" check,
STUDY cites it as `:698-703`, now `:729-730` in the tree): split by epoch type, traced ->
`pid._ebops == traced total` (unchanged), untraced -> `pid._ebops == in-training total`.
The reload assertion `verified_cost == cost` compares the reloaded file's stored sum with the
live model's stored sum on untraced epochs (the byte-equality check of every variable is
unchanged). `cpu_gate.py` gains a `TRACE_EVERY_OK` line per config (k = 10, snapshot and epochs
divisible, reload check "stored"). Counter semantics: `feasible_degenerate_epochs` now counts
traced epochs only, so its denominator is 701 (not 7,000) for a full run, 101 for R; STUDY reports these
counts and must say so. Config validation: `ebops_trace_every` requires `ebops_trace_sample` and
`ebops_reload_check: "stored"` (a retrace reload check on an untraced epoch would compare a
reset trace with in-training EBOPs).

**(e) Resume chain.** Every regime-B config differs from its 77f1ca4e version by the new key, so
all 58 `config_sha256` change; the bundle and `code_sha256` change too. `data_sha256` is unchanged
(same cache, not rebuilt; the regenerated `cache-job.json` must not be applied, since `data_info`
embeds the cache's own ac5a5c86). Consequences: regime-A pilot checkpoints can never resume into
regime-B production (config and code sha both differ; `restore_checkpoint` refuses). Regime-B pilot
checkpoints of production configs (A-s1, A-s2, D-s1, A07-350-s1, C-s1, F-s1) can resume into
production iff production runs the same bundle and configs and the run directories are copied (or
the root pointed) explicitly; C′ and E1 are pilot-only. A resumed production run opens a new
W&B run (`BNJ_STAGE=production` id).

### DECISION blocks

```
DECISION R-B1: on traced epochs the PID reads the traced EBOPs (order trace -> on_epoch_end kept);
  on untraced epochs it reads the in-training EBOPs. The PID input is a 9:1 mixed series.
ALTERNATIVES: feed the in-training value on every epoch (call on_epoch_end before the trace, or
  override pid._ebops): closest to FreeEBOPs, and a single-quantity PID input, but it removes
  the only point where the PID sees the certified number. No measurement of the in-training /
  traced ratio exists yet (ebops_in_training_over_traced is logged by every [D20] run; the
  regime-A canary pull did not fetch it).
WHY: minimal change to the regime-A order; the traced value is the one the budget is certified
  on. The regime-B pilot logs both quantities every traced epoch, so the ratio is measured
  before production.
```

```
DECISION R-B2: untraced epochs still save, reload and validate the candidate (logged, never
  selectable); the jsonl record carries `ebops_traced` 0/1, `ebops` null, `budget_met` null and
  `ebops_in_training`; W&B gets no `ebops`/`budget_met` key on untraced epochs, so the W&B
  `ebops` curve stays a traced quantity.
ALTERNATIVES: skip validation on untraced epochs (saves the 62,000-row predict and one
  save/reload, about 3 % of s_e by the canary split, and delays [A12] non-finite detection by up
  to 9 epochs); or log the in-training value under `ebops` (mixes two quantities in one column).
WHY: STUDY's own option text keeps candidates every epoch; the saving is small.
```

```
DECISION R-B3 (revised after the coordinator's message: STUDY Pods, R packs separately, about 13
  pods; the first version packed R into E seed blocks on 14 pods): production packs.json, 13 pods,
  provisional until the regime-B pilots' per-process GPU memory is read at PREFLIGHT (STUDY:
  "the production pod map is fixed at PREFLIGHT from the regime-B pilot's measured peak").
  - E Chang arms {A, B, D, F} x 8 = 32 runs in seed order at K=5, chunked 5, 5, 5, 5, 4, 4, 4
    (packs 0-6, launchable without the K=3 readout). Memory: 5 x 4,354 MiB = 21,770 of 23,028 MiB
    on an A10 (RUN.md per-process A/D figure, K=6 pod).
  - A07 arms {C, A07-350} x 8 = 16 runs in seed pairs {C_s, A07-350_s, C_s+1, A07-350_s+1} at
    K=4 (packs 7-10), waiting for the K=3 pod's A07-350-s1 epoch-500 readout (arbiter v8 fix 2
    (3)). Not K=5: 5 x 5,172 MiB (the C' per-process figure, the only A07 number) = 25,860 MiB >
    23,028 MiB. K=4 gives 20,688 MiB by the same figure, but A07-350 OOMed at K=6 and has no
    per-process number yet; if the K=3 pod's peak x 4 does not fit, repack at K=3 (6 pods, 15 in
    total).
  - R s1-4, s5-8 at K=4 (packs 11-12), as STUDY.
  Utilization: packs 4-6 run 4 arms on a K=5-sized pod; the alternative 32 = 6 x 5 + 2 leaves a
  2-arm pod. Same-seed runs of the E arms sit in at most two pods (seeds 5-8 in one pod each);
  all wave-1 pods are A10, so confound 9 holds by class.
  A repack changes only packs.json, which is outside run_study.manifest(): code_sha256 and the
  resume chain are unchanged, only a new bundle and ConfigMap.
ALTERNATIVES (numbers above): R in E seed blocks {A,B,D,F,R}_s at K=5 + A07 at K=3 (14 pods;
  first version, withdrawn: STUDY packs R separately); {A,B,C,D,F}_s at K=5 + A07-350 K=3 + R (13
  pods, but every E pod would hold C and wait); A07 at K=3 (15 pods).
```

```
DECISION R-B4: regime-B pilot stage `BNJ_STAGE=pilot-b`: W&B id sha256("pilot-b" NUL name)[:12],
  group chang-n64-20260926-pilot-b (not -canary: RUN.md pulls the -canary group by run name),
  tags chang0926,pilot,pilot-b,regime-b,validation-only; run root /data/chang-n64-20260926/pilot-b.
ALTERNATIVES: same -canary group with distinct ids only (display names would collide in that group).
```

### Work log (this pass)

Previous ml-engineer (cut off by an API rate limit) left: patches 0027-0029, the regenerated
configs, packs.json (13 pods), `freeze.py` with the regime-B job builders and `main()`, the frozen
bundle f2107a04 (tarball 15:36:45 PDT, after the last `code/tree` edit at 15:36:29), five manifests,
gate/pairing/floor/pytest evidence without a recorded working directory, and the two dry-run
scripts, never run to completion.

Continuation (second ml-engineer, 2026-09-27 PDT / 2026-09-28 UTC), nothing applied, nothing committed:
- Provenance. `bash code/apply.sh` ends `APPLY_MATCHES_TREE`; the tarball extracted fresh equals
  `code/tree` + `code/analysis` (`diff -rq`, `__pycache__` excluded, empty). The committed
  tarball at HEAD is 77f1ca4e (sha checked), extracted beside it for the regime-A checks.
- Alignment (a), slot T: `is_traced_epoch` has `epoch == 0` (`ablation.py:483-489`), and
  `tests/test_trace_every.py::test_key_semantics` asserts 701 traces, `traced[:2] == [0, 9]` and the
  ends of epochs 1, 10, 500, 1,000, 2,000, 4,000, 7,000. The answer above ("Which epochs are
  traced") already says so. STUDY at 96b95f2 still carries the fixer's earlier reading ("no
  epoch-0 trace", 700 / 100 traces, canary = `initial_ebops` against epoch 10) and needs correcting.
- Alignment (b), pods: done in DECISION R-B3 (revised): 13 wave-1 pods, R alone in packs 11-12 at
  K=4. No memory or utilization reason to deviate from STUDY.
- `ablation.py` is now sha256 ee028685... (the fixer cited a26ea580..., 14:57; edited 15:11).
  Current line numbers for STUDY's citations: `is_traced_epoch` :483-489 (STUDY :483-487);
  `ebops_trace_every` validation :461-480; selection and recovery freeze only on traced epochs :721-765 (STUDY
  :721-763); PID assertion split :766-777 (STUDY :765-775); log line :840-844 (STUDY :838-842).
- `freeze.py`: also writes sha-named `configmap-f2107a04.json` and `bundle-manifest-f2107a04.json`
  beside the kept 77f1ca4e pair. Re-run: bundle sha, manifest sha and all five Job names unchanged
  (deterministic).
- Gates re-run on the fresh extraction (evidence `*_rerun.*`): full `cpu_gate.py` (no `--only`),
  pytest, [A17] 8-seed pairing, [A7] floors. The absent-key regression was re-run on f2107a04
  and on a fresh 77f1ca4e extraction (the reference reproduces).
- `dry_readout_run.py` fix: its "unsubstituted /data path" guard fired on the cache's own
  `n64/data/` subdirectory after substitution (false positive; the script never ran). It now
  matches only an absolute `/data/` path.
- Lint: `nrp_doctor.py lint` OK on all five Jobs; `bash -n` OK on all five embedded scripts.
- Superseded evidence: `code/evidence/regression_trace_every_absent.log` and
  `regression_trace_every_absent_patched.json` are the previous agent's run on the pre-freeze
  18db6132 extraction. They are superseded by `regression_trace_every_absent_f2107a04.{log,json}`.
  The `*_f2107a04*` gate, pytest, pairing and floor files without `_rerun` have no recorded
  working directory; the `_rerun` files are the ones to cite.
- Dry-run models: the synthetic snapshot models for both roots are built with the f2107a04
  tree. readout-a loads and retraces them with 77f1ca4e's own code. This is valid because
  patches 0027-0029 touch no layer or quantizer file (`ablation.py`, `run_study.py`,
  `wandb_util.py`, tests, configs, generator only).

```
DECISION R-B5: the three B2 fields (ebops_trace_seconds, ebops_trace_over_epoch, loss) are printed
  on every [D20] epoch line, with or without `ebops_trace_every`. With the key absent, records,
  checkpoints, EBOPs and state are byte-identical to 77f1ca4e; the stdout epoch line is identical
  up to those three trailing fields (regression_trace_every_absent_f2107a04.log).
ALTERNATIVES: print them only when the key is set (two-line change in ablation.py:842-843, then a
  re-freeze: new bundle, ConfigMap, manifest sha, five manifests, all gates again).
WHY: brief item 2 asks for the fields on the per-arm line; the running regime-A pilot is on
  77f1ca4e and never runs this code; the stdout line is read by people, not parsed into a number.
  Not re-cut. Orchestrator to confirm or overturn.
```

### Coordinator question: C and C′ "constraint active" readout (STUDY l. ~1605-1630)

Both C and C′ are [D20] configs (`train.ebops_trace_sample: "train_full"`, so `d20` is on,
`ablation.py:603`), with `ebops_trace_every: 10`, target 5,000,000, `min_beta` 1e-10, and a
non-degeneracy rule (C′ zero floor 4,580,398; C 343,053). C′'s SAT quantizers change nothing
in this path. Feasibility test (a) is `budget_met = cost['total'] <= final_target`
(`ablation.py:723`). On a traced epoch `cost = traced_ebops(model)` (`:694-695`): the
full-split reset trace, `compute_ebops(model, trace_rows=all 558,000 train rows, batch 2048)`
(`:610-611`). On an untraced epoch (a) is not applied (`budget_met = None`).
Series and keys:
- **Traced EBOPs, the series (a) tests:** key `ebops` in `activation_widths.jsonl` (every epoch;
  null on untraced epochs under regime B) and in W&B history (traced epochs only; the key is
  dropped on untraced epochs: set to None at `:811`, filtered at `:847`). The flag is `ebops_traced` (1/0, jsonl and W&B,
  regime B only). The test's own outcome is `budget_met` / `ebops_budget_met`, same null rule;
  `ebops_above_floor` and `nondegenerate` are beside them. Under regime A (the running pilot) every
  epoch is traced, `ebops` is never null and `ebops_traced` is absent. Stdout: `EBOPs=<n>`
  on traced lines, `EBOPs=untraced in_training_ebops=<n>` on the others.
- **Share of traced epochs over 5M:** rows with `ebops_traced == 1` (regime A: all rows),
  `ebops > 5,000,000` (equivalently `budget_met == 0`). The denominator is 701 per 7,000-epoch run
  (51 up to the epoch-500 readout: e = 0, 9, 19, ..., 499).
- **Selected checkpoint's EBOPs:** `best_feasible.ebops` in the snapshot's `state.json`
  (`snapshots/epoch-0500/state.json`; the traced value when selected). The readout's
  `certify-snapshot-0500.json` gives `logged_ebops`, `retraced_ebops`, `stored_ebops` for it.
  Divide by 5,000,000 at readout.
- **β at its lower bound:** key `beta` (jsonl and W&B, logged every epoch in both regimes;
  stdout `beta=`). Take the last 10 rows with `ebops_traced == 1` and compare with
  `min_beta` 1e-10. Under regime B, β on untraced epochs is driven by the in-training EBOPs
  (`ebops_in_training`, `pid_ebops`, logged every epoch). Report β on traced rows only, or say
  which rows were used.
No code change needed: every quantity is already logged per epoch in both regimes.

### Telemetry note (coordinator, regime-A pilot incident 2026-09-28; not a result)

The `run_pack.py` stall watchdog (`ARM_STALLED_NO_PROGRESS`) fired on 4 of 5 arms at about
01:32-01:35 UTC. C′-s1 and E1-s1 exhausted their retries; the retry budget is shared with the
earlier OOM. Details: RUN.md "Health check, 2026-09-28"; the root cause is in
`review/INCIDENT_stall_20260928.md`. With 3 processes left on the A10, s/epoch fell to about
130-135 s from 218 s at 5 processes (pod telemetry relayed by the coordinator, not measured
here). This bears on production K. If the fix lands in `run_pack.py`: edit `code/tree`, add
patch 0030, then `bash code/apply.sh` and `python3 manifests/freeze.py`. New bundle, ConfigMap
and job names follow automatically; `EXPECTED_MANIFEST` in freeze.py changes only if the fixed
file is inside `run_study.manifest()`. Then re-run the gates listed above.
Consequence for `readout-a-job.json`: its snapshot gate needs `snapshots/epoch-0500/state.json` or
`DIVERGED.json` for all five runs. If C′-s1 and E1-s1 have stopped for good (retries
exhausted, no DIVERGED.json), the Job stops at `SNAPSHOTS_NOT_READY` and certifies nothing.
Orchestrator decision: relaunch those arms, or regenerate readout-a with three runs.

### Stall incident fix and re-freeze to 42abed4b (2026-09-28; coordinator: the fix blocks the freeze)

Source: `review/INCIDENT_stall_20260928.md`. The regime-A pilot was stopped at 05:31Z (Kai), with
checkpoints A-s1 and A-s2 at 0125, D-s1 at 0150, E1-s1 at 0075 and C′-s1 at 0025.
- **Leak search on CPU (not reproduced).** `code/evidence/leak_probe.py` (whole `run_training`
  loop) and `leak_micro.py` (one operation per iteration) ran on macOS under load 13-50,
  measuring `phys_footprint`. Pager swings of up to about 800 MB made anything under about
  10 MB/iteration unreadable. Every operation grew by about 2-9 MB per iteration or epoch:
  reload + predict (6,000 and 200,000 validation rows), predict on a fixed model at 62,000,
  the full-split trace, the W&B path offline, and the whole loop (regime A, 22 epochs). None
  came near 80-95 MB. The Python object count stayed flat in every probe. The GPU leak is
  therefore not reproduced here, so no CPU test can prove the fix.
- **Same-scale CPU test at the gate's bar (whole loop, regime B, 4,000 / 2,000 rows, 115
  epochs; gate formula applied to epochs 5-104, projected to 7,000 epochs at 6,144 MiB).**
  Pre-fix f2107a04: slope 3.237 MB/epoch, projection 24,096 MB, FAIL. Post-fix 42abed4b: slope
  0.004, projection 1,911, PASS. So the reload path leaks on CPU too, about 3 MB/epoch, and
  the fix removes it. The GPU's 80-95 MB/epoch is not reproduced.
- **Fix under test (0031).** `ValidationReloader`: one validation model per run, with
  `load_weights` of each epoch's candidate. This is the incident's first candidate (a new model,
  graph and predict function every epoch). Tested equal to a fresh load byte for byte. The
  absent-key regression against 77f1ca4e still holds.
- **Proof on GPU (0031 + freeze.py).** An RSS gate runs on both pilot-b pods, in projection form
  (coordinator correction: a 5 MB/epoch slope gate admits 35 GB/arm by epoch 7,000). It fits RSS
  over process epochs 5-104 and requires baseline + slope × train.epochs ≤ 6,144 MiB, else exit 5.
  That means a slope of about 0.55 MB/epoch or less. The epoch line carries ` host_rss_mb=`, so the
  arm logs tell the causes apart. A step at traced epochs points at the trace (regime B then leaks about
  1/10 of regime A, about 9 MB/epoch, and fails the gate). A uniform slope points at some other
  per-epoch path.
- **`run_pack.py` (0030).** Fresh heartbeat clock per attempt, `POD_STALL` not charged,
  `POD_MEM` every poll, exit 5 not retried.
- Per-arm memory stays 6 GiB. See DECISION R-B8.
- Re-freeze: `apply.sh` ends `APPLY_MATCHES_TREE` with 0001-0031. `EXPECTED_MANIFEST` is now
  041f981a. Bundle 42abed4b, ConfigMap `kai-chang0926-code-42abed4b5d`. f2107a04 (never applied)
  and ceb174db (slope-form gate, gates were running when the correction came, payload deleted
  unused) are superseded. Consequence outside this campaign: Delta's decisions.md entry says it must
  rebase onto the regime-B bundle (it saw an intermediate e90327d4). The bundle to rebase onto is now
  42abed4b, not e90327d4, f2107a04 or ceb174db.

```
DECISION R-B6: fix the leak candidate without a CPU reproduction, and let the pilot-b RSS gate
  prove or refute it on the GPU (a verdict at process epoch 105; the leak as measured would reach
  6 GiB near epoch 48, so a leaking arm may stall before the gate; the gate is for small leaks).
ALTERNATIVES: a GPU diagnostic pod first (two arms, regime A against regime B, no fix, the
  incident's discriminating measurement), then fix; or keras.backend.clear_session() around a
  per-epoch reload (not possible mid-run without rebuilding the live model and optimizer).
WHY: the reloader is semantics-preserving (tested byte-equal) and removes the named candidate.
  The gate turns a wrong guess into a cheap, attributable failure at process epoch 105. A diagnostic pod costs a
  GPU-day and delays the pilot. Orchestrator to confirm or overturn.
```

```
DECISION R-B7: pod-stall policy. At least 2 arms and at least half the live arms stalled in one
  sweep is a pod condition. Those arms are not charged; they have a separate budget of 2, and a
  relaunch waits until the cgroup has the arm's last RSS free. A single stalled arm is charged
  as before.
ALTERNATIVES: never relaunch after a pod stall (pod exits, operator decides); or charge as before.
WHY: the incident's §4-§6 recommendation; a bounded budget prevents an infinite relaunch loop if
  the cause persists.
```

```
DECISION R-B8: projection gate (coordinator, 2026-09-28): least-squares fit of host RSS over
  process epochs 5-104; baseline (fit at epoch 5) + slope x train.epochs <= 6,144 MiB (the
  manifest's per-arm limit), else exit 5. Per-arm memory stays 6 GiB (measured start RSS
  2,106-2,160 MB). The gate is on the pilot-b pods; production memory can stay 6 GiB/arm only if
  production arms pass the same gate or the pilot-b slopes stand in for them.
ALTERNATIVES: a slope threshold (5 MB/epoch; withdrawn, it admits 35 GB/arm at 7,000); a shorter
  window (earlier verdict, noisier slope); gating production too.
WHY: the limit in the manifest is what the kernel enforces; projecting to the terminal epoch tests
  exactly that. A leak as large as the incident's (~90 MB/epoch) fills 6 GiB near epoch 48,
  before the verdict at 105, so it would show as a stall again, now as POD_STALL with POD_MEM
  lines and without charging retries. The gate is there for leaks too small to stall a pilot.
```

- Gates on a fresh extraction of 42abed4b (manifest 041f981a). Full `cpu_gate.py`:
  `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`, lines equal to f2107a04's. pytest: 93 passed,
  2 skipped. [A17]: 32/32 PAIRED, JSON equal to d25. Floors: 9/9 STATIC_FEASIBLE. The absent-key
  regression against 77f1ca4e holds (records, files and EBOPs equal). Lint: 5/5 OK. Dry run
  readout-b5: exit 0. Readout-b3: see PREFLIGHT. Evidence: `code/evidence/*42abed4b*`.
- Not built (flag): the gate's verdict comes at process epoch 105, but a leak the size of the
  incident's fills 6 GiB near epoch 48. A per-epoch hard stop at RSS > 0.9 × limit would turn
  that case into a clean exit 5 before the cgroup fills. It is a small change plus a re-freeze;
  the orchestrator decides.

### Fixer: STUDY corrected after the regime-B freeze 42abed4b (2026-09-28; not committed)

STUDY change-log entry "corrected after the regime-B freeze 42abed4b" (STUDY l. 351-377) lists
every edit: slot T epoch 0 traced, 701 / 101, canary pair epoch 1 vs 10; `generate.py:57` and
`TRACE_EVERY_OK` 58/58 (caveat removed); arm-C (i) denominator 51 / 701; ablation.py citations
re-cited to 42abed4b by content (screen-bundle citations labelled 7f9e9307 instead); leak fix,
`run_pack` changes, RSS projection gate and the epochs-10/20 operational canary rule; regime-A
pilot stopped 05:31Z; DECISION R-B5 accepted. Not changed (flag): `generate.py:57` comment says
"trace at epochs 10, 20, ..." (code, out of scope); STUDY l. 140 and l. 2221 say "epoch-0 trace"
for the pre-training init trace, now ambiguous beside slot T.

### Fixer: STUDY text pass after PREFLIGHT gate v3, Kai 2026-09-28 (not committed)

STUDY change-log entry "text pass after PREFLIGHT gate v3, Kai 2026-09-28" (STUDY l. 378-385):
pilot-b A10 only, c6017 excluded, pre-arm fingerprint gate on arm-A s1 `initial_ebops` (value
pointed to PREFLIGHT, not quoted), K=3 OOM fallback (l. 1583-1588); epoch-10/20 rule as the
formula rss20 + (rss20 − rss10)/10 × 85 > 6,144 MiB to process epoch 105 (l. 1741-1748). Not
changed: PREFLIGHT, RUN.md, code, manifests. The fingerprint value must be added to PREFLIGHT
'Regime B addendum' by its owner; STUDY points there.

### Fixer: STUDY after arbiter v10 ESCALATE, Kai 2026-09-28 (not committed)

STUDY change-log entry "amended 2026-09-28 (Kai, STUDY v10 ESCALATE ...)" (STUDY l. 400-436) lists
every site. K1 = (b): 'Regime-B PID input rule' pre-registered in the Phase 2 pilot rules (thresholds
verbatim from arbiter v10; (c) to be staged by ml-engineer, unapplied), slot P (3) carries the
regime-A ratio (F7). K2: FP32-E selects on the 701 slot-T epochs; [A25] now needs the selectable-epoch
rule with trace and controller off (ml-engineer, wave-2 code item). K3: A − NB fixed at 8 pairs, the
extra-pair rule declined. F1-F7 applied. Memory: 8,192 MiB split from the running K=3 pod (6,144 until
swapped). Deviations from the arbiter's text, flagged for v11: `packs.json` has three E pods at K=4, so
F1/F6 name them as a class timed from the K=5 s_e as an upper bound; arbiter "12-15 % of headroom"
recomputed as 11.8-12.7 % (A/D) and 10.1 % (E1) from the RUN.md medians. Checked: `prose_lint` score 0.
Open for others: ml-engineer stages the (c) patch and the FP32-E selectable-epoch rule; cluster-ops
records the K=5 re-apply at 8 GiB and the K=3 swap in RUN.md; no PREFLIGHT, RUN, code or manifest edit.

## Option (c), staged (ml-engineer, 2026-09-28; Kai K1; not applied, not shipped, not committed)

Source: Kai's K1 = (b) (top entry of `.claude/memory/decisions.md`), `review/STUDY_arbiter_v10.md`
#1-#2. Option (c): under regime B the PID reads only traced full-split EBOPs and holds β between
traces. Today (slot P, 42abed4b) it steps every epoch and reads the in-training EBOPs on untraced
epochs. Staged so that Kai can pick (c) at the epoch-500 readout without writing code then.
`code/tree`, bundle 42abed4b, its ConfigMap and the running pilot-b pods are untouched.

**Where it lives.** `code/patches-staged/0032-option-c-pid-traced-only.patch` (sha256 f475c69e…,
on top of 42abed4b = `code/patches/` 0001-0031) and `code/staged-option-c/code/` = a fresh
extraction of `manifests/chang0926-code.tar.gz` (42abed4b) with 0032 applied. A third fresh
extraction plus `git apply 0032` is `diff -r`-equal to `staged-option-c/code`
(`PATCH_ON_42abed4b_EQUALS_STAGED`). Evidence: `code/staged-option-c/evidence/`.

**What 0032 does** (`bnhgq2/ablation.py` + `tests/test_pid_traced_only.py`; everything is inside
`if pid_input == "traced_only"`):
- New keys `train.ebops.pid_input: "traced_only"` and `train.ebops.pid_traced_integral:
  "per_epoch" | "per_step"`. Both sit beside `pid`, not inside it, because `pid` is splatted into
  `BetaPID(**...)`. Guards raise ValueError for: another value; no `ebops_trace_every` (regime A);
  `d != 0`; an untraced epoch `warmup - 1` (hgq2 seeds the integral only at `epoch == warmup`,
  `beta_pid.py:140-148`); and `pid_traced_integral` without `pid_input`.
- Epoch-begin: `BetaPID.on_epoch_begin(e)` runs iff e < warmup or epoch e − 1 was traced.
  Otherwise it is not called and β stays in the layers. With k 10, 7,000 epochs and warmup 1 the
  steps are at epochs 0 (the warmup branch), 1 (the seed, on the epoch-0 trace), then 10, 20, …,
  6,990, 701 in total. The epoch-6,999 trace drives no step.
- Epoch-end: on untraced epochs `on_epoch_end` is not called. `pid._ebops` and
  `state['pid']['ebops']` therefore keep the last traced value, and this is asserted. The slot-P
  assertion that checks in-training EBOPs is skipped only in this mode. New logs under the key:
  `pid_stepped`, `pid_step_span`, `pid_integral`.
- The step span D (epochs since the previous step) is a pure function of (cfg, epoch). A resume
  from an untraced checkpoint (checkpoint_every 25 against k 10) needs no new state; this is tested.

**Gain scaling: design choice for experiment-designer and Kai.** hgq2 `PID.__call__` adds one
error per call (`beta_pid.py:29`), and β = 10^(p·err + i·I) is clamped only afterwards (`:158`).
- *Integral.* To give the same response per unit time as the per-epoch controller, a D-epoch step
  must add D × the held traced error. That is "per_epoch" (**staged default**): i = 0.05 keeps its
  per-epoch meaning, and the integral stays in the same units as slot P. "per_step" adds it once,
  so the effective per-epoch integral gain is i/10 = 0.005.
- *Proportional.* p = 1.0 is not time-scaled. The sampled loop gain still rises, because the
  plant has 10 epochs to settle between reads. If the plant fully settles within a step,
  e_{n+1} = (1 − bp − bis)·e_n + bp·e_{n−1}, where b = −d log EBOPs / d log β. The loop is stable
  iff bp < 1 and b(p + is/2) < 1. That gives b < 0.800 for per_epoch (s = 10) and b < 0.976 for
  per_step. A slower plant relaxes both bounds.
- *Toy simulation* (`evidence/sim_pid_traced_only.{py,log}`). It drives the real hgq2 `BetaPID`
  and the staged functions on a synthetic first-order log-space plant, so it is **not a result**.
  - It reproduces the arbiter's slot-P stationary point, T·r^−0.9 (median/T 0.927-0.933 against
    0.9331 predicted at r = 1.08, every τ and b).
  - (c)/per_epoch converges to the target (median/T 0.9989-1.001) at about the regime-A speed:
    first within 2 % at epochs 109-319, against 78-284 for regime A. This holds for b ≤ 0.75 at
    every τ, and for b ≥ 1 when τ ≥ 20 (12 of 16 cases).
  - It diverges to max_beta for b ≥ 1 with τ ≤ 5. per_step also diverges at b = 1, τ = 2, and at
    b = 1.5, τ ≤ 5.
  - per_step converges to the target (0.9964-1.001; 13 of 16 cases) but slowly: first within 2 %
    at epochs 1,469-2,849, so the epoch-500 readout would come before convergence.
  - Halving p (illustration only; it is not an arm knob) stabilises b = 1, τ = 2.
  - Default chosen: per_epoch. It is the only mode that reaches the target by the epoch-500
    readout.
  - **Open, and it decides the choice:** b and τ for the real model are unmeasured. The experiment
    that settles them costs no GPU: fit b and τ from the regime-A W&B per-epoch history (`beta`,
    traced `ebops`) and the pilot-b traced epochs. If b·(1 + 0.25) ≥ 1 and τ ≲ 10, p must drop
    (Kai's knob; STUDY has p 1.0). Handed to experiment-designer. Inference, not measured: with
    cosine restarts every 500 epochs (3e-3 → 1e-6), τ is shortest just after each restart. The
    exposure to the fast-plant cases is therefore the first tens of epochs of each cycle,
    epochs 0-50 of a pilot included. Fit b and τ per LR phase, not pooled. The bound is a
    necessary condition on a single-pole toy plant, not a sufficient one on the real model.
- *Anti-windup.* Neither mode adds any. (c) removes the arbiter's reading-1 A07-350 wind-up:
  - Toy, traced floor 343,053, r 1.08: slot P winds up (β at max 1e-3, integral +61.6) and sits on
    the floor. (c) settles at the target with no wind-up.
  - With a truly infeasible target (T = 0.95 × floor) both wind up. The integral grows without
    bound in slot P and in (c)/per_epoch, and more slowly in per_step. Real infeasibility still
    needs the STUDY's arm-C rule, not the controller.

**Absent key is unchanged against 42abed4b** (`evidence/regress_option_c_absent.log`, CPU,
synthetic rows). On a fresh 42abed4b extraction and on staged-option-c, the records, every saved
file's weights, the state and the EBOPs are identical. This holds on regime A (3 epochs; a, cprime,
two screen configs) and on the **pilot-b regime-B shape** (`ebops_trace_every` 10 kept, 12 epochs,
9 of them untraced; a, cprime). The stdout epoch lines are identical apart from the wall-time
fields `ebops_trace_seconds` and `ebops_trace_over_epoch`, the same as in the 42abed4b regression.

**Tests.** `tests/test_pid_traced_only.py` has 7 tests: guards; the production step schedule;
β held and integral unchanged on untraced epochs, and stepped on traced ones (β recomputed from
the hgq2 formula), for both modes; the PID reads the last traced EBOPs, never the in-training
value; a resume across an untraced pause replays exactly; a slot-P checkpoint refuses an (c)
config. Run together with `test_trace_every.py` they give 13 passed. Full suite on
staged-option-c (`evidence/pytest_staged_option_c.log`): `100 passed, 2 skipped, 30738 warnings in
193.18s`, against 93 passed and 2 skipped at 42abed4b. The key is honoured only by
`ablation.run_training`, which is the chang0926 path (`run_study.py:135`). The callback path in
`bnhgq2/train.py:134` does not read the key, so a config carrying it there would run slot-P-style
per-epoch control; no chang0926 config uses that path.

**Re-freeze cost if Kai picks (c) at the epoch-500 readout.**
1. Code: move 0032 into `code/patches/` and apply it to `code/tree`. Add one line to
   `campaigns/chang0926/generate.py` (base `train.ebops` gains `pid_input: "traced_only"`, and
   `pid_traced_integral` if Kai overrides the default). Optionally add a `PID_INPUT_OK` line to
   `cpu_gate.py`. None of this is written yet.
2. Configs: regenerate all 58 (56 production + 2 pilot-only). Every config sha changes, and so
   does `index.json`.
3. Bundle: `manifests/freeze.py` (full mode). This gives a new tarball sha, a new ConfigMap
   `kai-chang0926-code-<sha10>`, a new bundle manifest, and regenerated pilot and production
   Jobs; cluster-ops lints them. The fingerprint integer (arm A s1 `initial_ebops` 11,559,681) is
   set before any PID step, so it should not move, but it must be re-checked on the new bundle.
4. CPU gates on a fresh extraction. At 42abed4b, `cpu_gate.py` full took 24 min (07:02:36 →
   07:26:19 UTC, `code/evidence/cpu_gate_shipped_42abed4b_full.log`) and pytest 169 s (93
   passed). Also rerun the [A17] pairing, static floors, absent-key regression and fingerprint:
   about 1 h of CPU in total.
5. Governance: a dated STUDY amendment before any (c) pod is applied (arbiter v10 regression
   note), then a scoped PREFLIGHT gate.
6. New pilot to its own epoch-500 readout. At the RUN.md projection of 136.5 s/epoch (k = 10;
   RUN.md "Projection, trace run only every k epochs") that is about 19 h; at the ~150 s/epoch
   RUN.md uses for pilot-b, about 21 h. Both exclude queueing, and both are projections, not
   measurements. Total: roughly one extra day before production wave 1, plus the review round.
7. **The running regime-B pilot's checkpoints cannot resume into a (c) run.**
   `restore_checkpoint` asserts `config_sha256 == digest_json(cfg)` ("Resume config mismatch";
   the new key changes the digest) and `code_sha256 == BNHGQ2_CODE_SHA256` ("Resume code
   mismatch"; the bundle sha changes). This is tested in
   `test_slot_p_run_cannot_resume_as_option_c`. A forced resume would still be wrong: its first
   500 epochs ran under slot P, so it would be a hybrid, not a (c) run. Those checkpoints and logs
   remain valid slot-P evidence. Their traced-epoch in-training/traced ratios near the target are
   exactly the per-arm r that option (d) needs.

**Stability evidence: b and τ from regime-A W&B (2026-09-28). Telemetry, not results.**
Script and log: `code/staged-option-c/evidence/fit_b_tau.{py,log}` (read-only pull of
`BNJetTag-ChangRecipe`, group `chang-n64-20260926-canary`: A-s1 `c16aff0707b9` epochs 0-146,
A-s2 `8560dcb87a4c` 0-145, D-s1 `81df1017a0eb` 0-167, E1-s1 `5fd00a94e508` 0-87; no gaps, no
duplicate epochs; `pid_ebops == ebops` asserted on every row).
- *Definition, matching the toy plant.* L_e = log10 traced EBOPs at the end of epoch e; lβ_e =
  log10 β in force during epoch e (W&B `beta` at step e+1). ARX(1) by OLS:
  L_e = a·L_{e−1} + g·lβ_e + c, so τ = 1/(1−a) and b = −g/(1−a) = −d log10 EBOPs / d log10 β at
  equilibrium. Variants: + linear epoch trend (absorbs the compression that is not driven by β);
  first differences. Pooled over runs with per-run intercepts, and per run. 95 % intervals are
  moving-block bootstrap (block 10 epochs, 2,000 reps); they cover sampling noise only, not the
  choice of specification. Windows: e1-40, e40-90, e90-end, e40-end. The traced signal is
  primary, and in-training EBOPs are a sensitivity check.
- *Collinearity.* After epoch 40, corr(lβ_e, e) is 0.990-0.998 in every run. β is a near-monotone
  integral ramp with no excitation of its own, so its effect cannot be separated from the drift.

| traced, e40-end, pooled (n 389) | b [95 % boot] | τ epochs [95 % boot] | per-run b (A-s1, A-s2, D-s1, E1-s1) |
|---|---|---|---|
| ARX, no trend | 0.168 [0.147, 0.204] | 4.21 [2.43, 5.02] | 0.21, 0.13, 0.18, 0.29 |
| ARX + trend | 0.30 [0.08, 0.65] | 4.48 [2.38, 5.67] | 0.17, 0.58, **0.84**, **0.88** |

- The no-trend fit assigns the drift to β, so its tight interval holds only within that
  specification. The trend fit puts D-s1 and E1-s1 above 0.80. The difference form is unusable:
  a ≥ 1 in 1,996 of 2,000 reps on e90-end, and b ranges 0.9-20 per run. Several in-training rows
  have the point estimate outside its own interval, or a significantly negative b (e90-end, trend:
  −0.31 [−0.62, −0.07]), which the plant sign rules out. Both are signs that the specification is
  failing, not estimates.
- e1-40 (fresh-init collapse, ARX): b 1.76 [0.99, 3.73], τ 17.2 [14.2, 33.1]. EBOPs fall about
  17-19× (epoch 0 → 40) while β moves only 1e-7 → 2e-7, so this b credits β with the collapse and is spurious.
  Because τ ≳ D there, the settled-plant bound does not apply. The τ-aware closed-loop spectral
  radius (fitted (a, g) held D = 10, per_epoch s = 10, p 1, i 0.05) is 0.705 [0.633, 1.05].
- τ after epoch 40 is about 2-6 epochs (point estimates; intervals 1.0-6.4). D = 10 is therefore about 2-5 τ, and the settled-plant bound
  b < 0.80 applies roughly as written.
- **Verdict: not established.** Regime-A telemetry neither confirms nor excludes b < 0.80. The
  estimate depends more on the drift specification (0.17 vs 0.30 pooled; 0.84 and 0.88 per run)
  than on the data. The per_epoch default is therefore not shown to be stable at p 1.0.
- **Conditional p (Kai's call; not applied, STUDY keeps p 1.0).** Settled bound p < 1/b − i·D/2
  (and p < 1/b): b 0.80 → p < 1.00; b 1.0 → p < 0.75; b 1.2 → p < 0.58; b 1.5 → p < 0.42. To cover
  the trend fit's worst per-run value (0.88) needs p < 0.89.
- **Caveats.** (1) Regime A traced every epoch and ran far from target (minimum traced 431,605-
  475,119 against 350k; RUN.md 2026-09-28 in-training section), so b is a local slope at β
  1e-7-1.2e-6 and EBOPs 450k-600k, not at target. (2) Only the high-LR head of cycle 1 is observed
  (LR 3.0e-3 → 2.2e-3). The low-LR tail and every post-restart transient of a trained model are
  unobserved, and epochs 0-40 are a fresh-init transient, not a restart. (3) A single-pole plant
  and a necessary condition only.
- **Experiment that settles it** (handed to experiment-designer; no GPU spent here): an
  open-loop β step. Hold β for ≥ 2τ (≥ 15 epochs) at each of two or three levels a factor of about
  3 apart, near target, preferably on a restart and on a late-cycle segment. Alternatively add a
  log-β dither independent of the integral. Pilot-b's slot-P epochs are closed-loop and cannot
  separate b from the drift.

**K2, staged for wave 2 (note only, no code started).** Kai's K2: FP32-E selects only on the same
701 traced (slot-T) epochs as A, even with the controller off. The wave-2 code must make FP32-E's
candidate set `is_traced_epoch(cfg, e)` with k = 10 (epoch 0, every 10th, the last). Any
(model_best / AUC-feasible / lowest) selection on the other 6,299 epochs must be refused. FP32-E
has no config in wave 1 (`campaigns/chang0926/configs/` has none), so this lands with the wave-2
generator and gets its own CPU test: the selected epochs are all in the 701-epoch set.

### Fixer: STUDY after v11 landing check (2026-09-28; not committed)
- B1 route (i): B out of the K1 fire list; B's r is a descriptive caveat on A − B read at production epoch 500 (STUDY l. 1752-1761). Reverts the v10 fixer's own addition; the arbiter must accept the departure from its v10 (b) wording, or B1 goes to Kai as route (iii).
- B2: memory-split attribution corrected at STUDY l. 390-392 and l. 1896-1899.
- C8: wind-up clause cites W&B `ebops_in_training` (`ablation.py:492-495`, `:783`, `:894`); the brief named `model_ebops`, which is the function, not the W&B key.
- C1-C7, C9 listed as disclosed, not fixed, in the STUDY change-log entry (l. 437-463). Nothing tried that failed.

## results-analyst: epoch-500 pilot readout, b3 (K=3 pod), 2026-09-29 (not committed)

Scope: evaluate the pre-registered epoch-500 pilot rules for A07-350-s1, C-s1, F-s1 and write
`READOUT_epoch500.md` section "b3 (K=3 pod)". Pilot numbers are validation-only telemetry, never
quoted; this is a rule evaluation, not a VERIFY.md (no verify.json, no experiment-log Result line).

- **Inputs.** `readout/b3/readout-epoch-0500-42abed-b3/{certify-snapshot-0500.json,
  a26-entropy-epoch-0500.json}`, `readout/b3/readoutb3-pod.log`; final per-arm logs
  `logs/*-kai-chang0926-pilotb3-42abed-0-final-*.log` (committed trajectory = lines after the last
  `==== ARM_ATTEMPT`, plus the first attempt's epochs 1-25, committed at checkpoint 25);
  `snapshots/epoch-0500/state.json` per arm and four `activation_widths.jsonl` records on the PVC
  (read-only `kubectl exec ... cat / sed -n`; extracts with sha256 in `readout/b3/pvc-extract-b3.json`);
  W&B `BNJetTag-ChangRecipe`, group `chang-n64-20260926-pilot-b`, read-only
  (`readout/b3/wandb-history-b3.csv`).
- **Scripts.** `readout/b3/fetch_b3.py` (W&B + PVC extracts, read-only), `readout/b3/rules_b3.py`
  (every computed number; writes `readout/b3/rules-b3.txt`, the file the READOUT cites).
- **Contents.** (1) A07-350-s1 rule; (2) per-run table; (3) C constraint readout (i)-(iii);
  (4) K1 inputs, both windows, pairwise clause, wind-up clause under both readings; (5) what the
  rules cannot decide; commands.
- **Windows.** "Traced epochs 100-500" read one-based (W&B step 100..500, 41 traced epochs), the
  STUDY's convention for readout windows (l. 1781, 1829); zero-based (step 101..500, 40) reported
  beside it.

DECISION: A07-350-s1 has no feasible checkpoint as of epoch 500, so the Falsifier expectation
(stated for feasible checkpoints) is reported "not testable on a feasible checkpoint"; on the
rule's fallback (`model_min_ebops`) the attention-logit half matches and the per-constituent half
exceeds the <= 3-channel bound on a checkpoint above 350k whose per-layer EBOPs reconcile exactly
with the floor; reported as no floor-accounting defect, no ml-engineer routing.
ALTERNATIVES: literal reading, a mismatch on the fallback (12 channel-bits against <= 3) routed
to ml-engineer and, since K1 fires, reported "not attributable (regime-B PID input)"; packs 7-10
would then also wait for an ml-engineer fix.
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES

DECISION: K1 is reported as firing on the K=3 inputs alone (headroom clause, A07-350-s1), since the
rule fires "if, for any run"; the K=5 arms complete the inputs and cannot un-fire it.
ALTERNATIVES: hold the K1 verdict until readout-b5 (the brief's framing).
CONFIDENCE: HIGH   FLAG FOR HUMAN: NO

Done 2026-09-29 (~19:00Z): `READOUT_epoch500.md` section b3 written; `readout/b3/{fetch_b3.py,
rules_b3.py, wandb-history-b3.csv, pvc-extract-b3.json, rules-b3.txt}`; every citation in the READOUT
resolved against its file (153 unique `file:line`), `tools/prose_lint.py` score 0. Found beyond the
brief: A07-350-s1's K1 headroom fire rests on a median r (1.005448) whose order-statistic interval
[1.000098, 1.013212] contains the fire point r* = 1.002210 (`rules-b3.txt:137`), so the margin is not
resolved against the spread of r; the C-s1 against A07-350-s1 pairwise fire is resolved (interval gap
0.048133, `:157`). Stated in the READOUT, section 4, Robustness.
Tried and failed: the first `pvc-extract-b3.json` kept every per-channel width (61,438 lines, the
16,384-channel softmax-output quantizer one value per line); replaced by per-quantizer counts plus
one-line lists for quantizers of 64 channels or fewer. A W&B re-pull was byte-identical to the first.
Not done, by the brief: no VERIFY.md, verify.json or experiment-log Result line (pilot telemetry).
