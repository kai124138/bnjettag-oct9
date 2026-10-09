# Code surface: every config knob, per code state (Delta, 2026-09-27)

Owner: ml-engineer. Read-only inventory. No code tree was modified, nothing was committed or
launched, and no training or synthesis was run. Every line reference was read from the file
named. Every "exists / missing" claim comes from reading or grepping that file, not from memory.
This file quotes no AUC or accuracy.

## 0. The four code states and their pins

| id | state | where read | pin |
| --- | --- | --- | --- |
| **S** | screen bundle, the lineage `campaigns/2026-09-26-training-batch/STUDY.md` pins | `campaigns/2026-09-22-constituent-screen/study-code.tar.gz`, extracted read-only to the scratchpad (`.../scratchpad/screen-bundle/code/`) | tarball sha256 `26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45`. This matches `bundle-manifest.json` and `final-static-checks.json` (ConfigMap `kai-n8n64-code-26f3cc40a8`). Every `.py` file in it hashes equal to the source manifest `7f9e93075123217af2adc10660cf9cf7dafffb51b9c385c29ee0211b3bff74d7` in `verified-launch-gates.json`, which is the "source sha256 7f9e9307..." the anchor STUDY cites. Package pins recorded there: tensorflow 2.21.0, keras 3.15.0, hgq2 0.1.9, quantizers 1.2.2, numpy 2.5.0, scikit-learn 1.9.0 |
| **Pc** | `publication/code/constituent-study-20260922` | files only (broken worktree, no git) | `diff -rq -x __pycache__` against S prints nothing: **byte-identical to S** |
| **Ph** | `publication/code/hgq2` | files only | no sha (broken worktree). An **older** line than S: `bnhgq2/ablation.py` and `qat.py` differ from S, and there is no `engram.py` (diff in §6) |
| **R** | `bnjettag/code/hgq2` (research tree, pT weighting) | files only; not committed | `bnhgq2/ablation.py`, `ebops_calc.py`, `ebops_target.py`, `extract.py` and `subln.py` are identical to Ph. `train.py` adds `pt_weights` (+ `bnhgq2/pt_weights.py`). The other differences are comments and renames |
| **C** | Chang reference `reference-code/HGQ2-examples/jsc150/` | clone, not edited | commit `6cdc6e34d4cea0fb0f2e3ac502e2bfea01b2a805` (2026-07-02, "feat: lut transformer"). **No LICENSE file at the repo root**, so the license is unknown. Nothing may be lifted until it is known |

The S bundle was frozen by `campaigns/2026-09-22-constituent-screen/freeze_jobs.py:11`, which
tars `research/bnjettag/code/constituent-study-20260922`. The live source of the lineage is
therefore inside the `research/` symlink tree, which this inventory did not enter. Pc is a
byte-identical copy of it.

Pinned HGQ2 check (for the recipe-gap rows below). The hgq2 0.1.9 wheel came from PyPI:
sha256 `749754214b97f2531e1f8e609308755fe857064f47d350e9ffb878fb5017c43c`, unzipped to the
scratchpad and grepped, never imported. It **contains** `QAffinedUnaryFunctionLUT`
(`hgq/layers/activation.py:76`), `QEinsumDenseBatchnorm`, `QDenseT`, `QMultiHeadAttention`,
`BetaPID` (`hgq/utils/sugar/beta_pid.py:95`, defaults `i=2e-3, warmup=10`), `Dataset` and
`EarlyStoppingWithEbopsThres`. It does **not** contain `StopIf` or `QLinformerAttentionT`.
Chang's `run_train.py:13` imports `StopIf`, so C at HEAD does not import on our pinned HGQ2.
C needs a newer hgq2 than the one we pin.

### Which runner reads a config in each state (this decides whether a knob is live)

- **S / Pc screen path:** `run_study.py train` → `run_engram.validate_cfg` (`run_engram.py:111-130`) → `run_engram.load_cache` (`:177-211`) → `ablation.run_training` (`bnhgq2/ablation.py:320-505`) with `run_engram.builder_for` (`:159-175`) → `ablation.matching_initialization` (`:61-115`) → `qat.build_qat_model` (`bnhgq2/qat.py:329-527`). `bnhgq2/train.py` and `ebops_target.BudgetMonitor` are **not** on this path. S uses only a few loader helpers from `train.py` (`load_train_data`, `macro_ovr_auc`, `_softmax`). `bnhgq2/config.load_config` (with its `REQUIRED_*` and weight-list checks) is **never called** on this path.
- **Ph / R ablation path:** `run_ablation.py` (`prepare` | `train`) → the older `ablation.run_training` (AUC-only selection, live-model validation, 15-layer binary gate).
- **Ph / R stage path:** `run_stage.py train` → `bnhgq2/train.train` (Keras `fit`, callbacks, `BudgetMonitor`). The pre-conference, budget-pilot and pT-weighting configs run here.

**Consequence for the designer.** A key read only on the `train.py` path is *inert* in the S
runner, which is the lineage the anchor pins. §1 marks every knob live (L) or inert (—) in S.
A method whose only knob is inert in S needs code, even though the key "exists".

## 1. Knob table

Count: **127 leaf keys**. 119 were observed across 220 config JSONs (S configs and
reference_configs, Ph configs, R configs, confirmation configs), and 8 more are read by code but
set by no config (`arch.pair_bias`, `arch.pair_bias_hidden`, `quant.act_recalib_epochs`,
`train.max_files`, `train.lr_schedule`, `train.lr_cycle_epochs`, `train.lr_min_frac`,
`train.ebops.threshold`). Two more keys, `checkpoint` and `reference_npz`, apply only to
rebuild (port) configs. Line numbers are S unless marked. States: S = S/Pc, Ph, R.

### 1a. `arch`

| key | type / allowed values (values seen) | default | read at (S) | S live? | states |
| --- | --- | --- | --- | --- | --- |
| n_part | int (8, 16, 32, 64) | required | qat.py:348; run_study.py:61,110; run_engram.py:183,201 | L | S Ph R |
| n_feat | int (3) | required | qat.py:348; run_engram.py:112 (must be 3), 201 | L | S Ph R |
| features | list of suffixes (only `[pt, etarel, phirel]`) | absent = all 16 (train.py:270) | ablation.py:46; prepare_cache.py:91; run_engram.py:112 (**must equal** `[pt,etarel,phirel]`) | L (fixed) | S Ph R |
| d_model | int (16, 32) | required | qat.py:348 | L | S Ph R |
| n_heads | int (1, 2, 4); head dim is `E = D // H` (qat.py:350) | required | qat.py:349 | L | S Ph R |
| n_layers | int (1, 2) | required | qat.py:349; ablation.py:252 | L | S Ph R (Ph/R gate hard-codes 15 layers, so L=2 only, Ph ablation.py:220) |
| ffn_dim | int (32, 64) | required | qat.py:349; ablation.py:80 | L | S Ph R |
| n_classes | int (5) | required | qat.py:349; run_engram.py:203 | L | S Ph R |
| pool | str ("gap") | required by config.py:18-21 only | never read; GAP is hard-coded (qat.py:519) | — | S Ph R |
| ffn_act | str ("relu") | required only | never read; ReLU is hard-coded (qat.py:512) | — | S Ph R |
| norm | "subln" \| "none" (only "none" seen) | "subln" | qat.py:371-374 | L | S Ph R |
| norm_placement | str ("per_linear") | required only | never read by qat | — | S Ph R |
| pos_enc | "learned" \| "none" | required | qat.py:351-352, 468 | L | **S only**. In Ph/R, qat.py:462 adds `AddPositional` unconditionally, so `"none"` is **silently ignored** |
| softmax_free | bool (false) | required only | never read | — | S Ph R |
| input_std | bool (true) | false (train.py:295) | train.py path only; S always standardizes (ablation.py:51-52, prepare_cache.py:102-103) | — | S Ph R |
| pair_bias | bool | false | qat.py:380; rejected in S by run_engram.py:116 | blocked | S Ph R |
| pair_bias_hidden | int | 8 | qat.py:381 | blocked | S Ph R |

### 1b. `quant`

| key | allowed (seen) | default | read at (S) | S live? | states |
| --- | --- | --- | --- | --- | --- |
| weight | "binary_absmean" \| "none" \| "int8_absmax" \| "kbi_learnable" (config.py:40) | required | qat.py:353-356; run_engram.py:114 (**must be** binary_absmean) | L (fixed) | S Ph R |
| act_bits | int (4, 6, 8, 32) | required | qat.py:354 | L | S Ph R |
| act_calib | "frozen" \| "trainable" \| "recalib" \| "free" (qat.py:362) | "frozen" | qat.py:361; run_engram.py:114 (**must be** free) | L (fixed) | S Ph R |
| act_bw_l1 | float (1e-8) | 1e-8 | qat.py:364 → `_free_act` MonoL1 on i and f | L | S Ph R |
| beta0 | float (0, 1e-7, 1e-4) | 0.0 | qat.py:365, 462 (`LayerConfigScope(beta0=)`) | L | S Ph R |
| act_granularity | "tensor" \| "channel" | "tensor" in qat.py:391, but indexed directly (required) in ablation.py:85 | qat.py:391-395 | L | S Ph R |
| softmax_out_bits | int (4, 6, 8, 10) | max(act_bits, 10) | qat.py:440 | L | S Ph R |
| softmax_out_i | int (0, 1) | 1 | qat.py:441 | L | S Ph R |
| act_recalib_epochs | list[int] | [] | train.py:396 only | — | S Ph R |
| act_policy | str (descriptive) | — | never read | — | S Ph R |
| calib_n | int (8192) | — | never read; the calibration batch is fixed at 4096 (qat.py:543) | — | S Ph R |

### 1c. `train`

| key | allowed (seen) | default | read at (S) | S live? | states |
| --- | --- | --- | --- | --- | --- |
| data | path | required by config.py | train.py:279; S reads the cache instead | — | S Ph R |
| validation_split | float (0.2 only) | 0.20 (train.py:285) | prepare_cache.py:33,100; but prepare_cache.py:36-37,92,101 and run_engram.py:207 **hard-assert 496,000/124,000** | L (fixed) | S Ph R |
| split_seed | int (1) | required in S | prepare_cache.py:94; run_engram.py:184 | L | S Ph R |
| order_seed | int (20260912 only) | required in S | ablation.py:388 (per-epoch permutation), run_engram.py:184 | L | S Ph R |
| epochs | int (50, 101, 1000) | required | ablation.py:381; run_study.py:143 | L | S Ph R |
| batch | int (256 only) | 256 (train.py:405) | ablation.py:159 | L | S Ph R |
| lr | float (2e-5, 1e-4, 2e-4) | required | ablation.py:122-123 | L | S Ph R |
| warmup_epochs | int (0, 1) | required in S | ablation.py:120-122 | L | S Ph R |
| decay_epochs | int (0, 49, 100, 999) | required in S | ablation.py:120,123 (poly) | L | S Ph R |
| decay_power | float (1.0) | 1.0 | ablation.py:123 | L | S Ph R |
| beta2 | float (0.98) | 0.98 (train.py:342) | ablation.py:142 (indexed, required) | L | S Ph R |
| weight_decay | float (0.01) | 0.01 | ablation.py:143 (indexed) | L | S Ph R |
| clipvalue | float (1.0) | 1.0 | ablation.py:143 (indexed) | L | S Ph R |
| clip_mode | "value" \| "norm" | "value" | train.py:341 only (S always clipvalue) | — | S Ph R |
| clipnorm | float | 1.0 | train.py:345 only | — | S Ph R |
| es_patience | int (0, 15) | 10 | train.py:383 only | — | S Ph R |
| jit_compile | bool (false) | Keras default | train.py:351; S hard-codes False (ablation.py:145, 162) | — | S Ph R |
| val_batch | int (1024, 4096) | 1024 | ablation.py:402; run_study.py:128 | L | S Ph R |
| wandb_project | str | env | ablation.py:371; run_engram.py:136 | L | S Ph R |
| max_files | int | none | train.py:266 only | — | S Ph R |
| lr_schedule | "poly" \| "cosine_restarts" | "poly" | train.py:187-198, 387 only | — | S Ph R |
| lr_cycle_epochs | int | 0 | train.py:388 only | — | S Ph R |
| lr_min_frac | float (relative floor) | 0.0 | train.py:389 only | — | S Ph R |

### 1d. `train.ebops` and `train.ebops.pid`

| key | allowed (seen) | default | read at | S live? | states |
| --- | --- | --- | --- | --- | --- |
| enable | bool | false | train.py:119; ebops_target.py:63 | — (S always runs PID) | S Ph R |
| monitor_widths | bool | false | train.py:323 | — | S Ph R |
| controller | "pid" \| "none" \| "schedule" | "schedule" (ebops_target.py:58) | train.py:124; ebops_target.py:58 | — (S hard-codes `BetaPID`, ablation.py:355) | S Ph R |
| beta_schedule | list of [epoch, beta, kind] \| null | null | train.py:129-132 | — | S Ph R |
| threshold | float | from pid.target_ebops | train.py:135 | — | S Ph R |
| front_dir, metrics, sides | str, list, list | "front", [val_macro_auc, ebops], [1,-1] | train.py:134-145 (ParetoFront) | — | S Ph R |
| selection | "max_auc" \| "min_ebops" (ebops_target.py:101-103); configs also carry "max_accuracy", which only S's generator writes | "max_auc" | ebops_target.py:101 | — (S uses `experiment.selection_metric`) | S Ph R |
| stop_on_target | bool | false | ebops_target.py:104 | — | S Ph R |
| target_ratio | float in (0,1] | none | ebops_target.py:66-72 | — | S Ph R |
| pid.target_ebops | float (250k, 350k, 500k, 5M, 869,591) | required | ablation.py:127, 354; run_study.py:37 | L | S Ph R |
| pid.init_beta, p, i, d, warmup, log, min_beta, max_beta, damp_beta_on_target | floats / int / bool (seen: 1e-7, 1.0, 0.05, 0.0, {0,1,10}, true, 1e-10, 1e-3, 0.0) | hgq2 BetaPID defaults | ablation.py:355 `BetaPID(**pid)`: the whole block is splatted | L | S Ph R |

### 1e. `train.pt_weights` (R only)

| key | allowed (seen) | default | read at (R) | S live? |
| --- | --- | --- | --- | --- |
| enable | bool | false | R train.py:301-303 | — (not in S or Ph) |
| n_bins | int (100) | 100 | R train.py:327 → pt_weights.py:53 | — |
| cap | float \| null (5.0, null) | null | same | — |
| class_weight | null \| dict | null | same | — |
| plot | bool | true | R train.py:333 | — |

pT weighting exists only on the R `train.py` (Keras `fit`) path. Putting it into S needs
`ablation.make_epoch_step` (ablation.py:149-184) to take a per-sample weight vector (about 15
lines) plus a cache column for jet pT.

### 1f. `experiment`

| key | allowed (seen) | default | read at (S) | S live? | states |
| --- | --- | --- | --- | --- | --- |
| seed | int (1-6) | required | ablation.py:327 (init seed; the data order does **not** depend on it) | L | S Ph R |
| group | str | required | ablation.py:371 | L | S Ph R |
| arm | str | — | Ph run_ablation.py:71 (output dir); S uses `index.json` | — | S Ph R |
| selection_metric | "val_macro_auc" \| "val_categorical_accuracy" | "val_macro_auc" | ablation.py:270-275; run_engram.py:118 (**must be** accuracy) | L (fixed) | **S only** (Ph/R select on AUC) |
| target_schedule | list of [epoch, budget] | [] | ablation.py:126-131 (PID target per epoch; feasibility uses the final target, :409) | L | S Ph R |
| recovery_after_epochs | int (800) | none | ablation.py:425-428 (freezes i/f after the first feasible epoch ≥ N) | L | S Ph R |
| distillation.{teacher_artifact, temperature, coefficient} | str, float, float | none | ablation.py:153-155, 174; **rejected** by run_engram.py:120; teacher logits are supplied only by Ph run_ablation.py:79-103 | blocked | S Ph R |
| remote_every_epochs | int (25) | required in S | ablation.py:462 | L | S Ph R |
| checkpoint_every_epochs | int (1) | — | **read nowhere** (grep over S; set by generate_configs.py:50 and run_engram.py:87). The full checkpoint is written every epoch (ablation.py:456) | — | S Ph R |
| source_arm | str | — | read nowhere (confirmation provenance) | — | configs only |

### 1g. `hls` (export only; no training effect)

| key | seen | read at |
| --- | --- | --- |
| backend | "Vitis" | convert.py (hls4ml config) |
| part | "xcvu13p-flga2577-2-e" | convert.py:65; convert_binary.py:818 |
| clock_ns | 2.5 | convert.py:66 |
| rf | 1, 256 | convert.py:41 (default 1); convert_binary.py:582 (default 256) |
| io | "io_parallel" | convert.py:63 |

The strategy is a CLI flag in the converters, not a config key.

### 1h. `engram_study` (S only; Ph/R have no `engram.py`)

| key | allowed | read at (S) |
| --- | --- | --- |
| module | null \| spec dict. Its **presence** (even with `module: null`) sets `cost_first = True` (ablation.py:421), which reorders tie-breaks to accuracy → −EBOPs → AUC → −epoch | run_engram.py:164; run_study.py:29 |
| module.bins | 4 \| 8 \| 16 | engram.py:43 (validate_spec) |
| module.table_size | 16..65536 | engram.py:45 |
| module.heads | 1 \| 2 \| 4 | engram.py:45 |
| module.orders | [1] \| [2] \| [2,3] | engram.py:47 |
| module.gate | "none" \| "hard" | engram.py:49 |
| module.value_bits, key_bits, query_bits, gate_bits | int 4..12 | engram.py:52 |
| module.input_bits / input_integer | must be 16 / 6 | engram.py:54 |
| module.residual_bits | ≥ 24 | engram.py:56 |
| module.hash_seed | int 0..1,048,576 | engram.py:58 |
| module.insert_after | layer name (seen: `bit_block_0_add_attn`) | engram.py:275-283 |
| memory_lr_multiplier | (0, 100] | ablation.py:141; run_engram.py:123 |
| memory_weight_decay | must be 0 | run_engram.py:123 |
| max_logical_table_bytes, max_replicated_table_bytes | > 0 | run_study.py:33-36; run_engram.py:127 |
| cost_convention | must be "native_hgq2_plus_custom_estimate" | run_engram.py:125 |
| wandb_entity, wandb_project_access | non-empty; must be "PRIVATE" | run_engram.py:129, 133-157 |
| question, status | text | provenance |

### 1i. `constituent_study` (S configs only)

`protocol`, `aliases`, `source_config_sha256`, `pair`, `equal_arithmetic_budget_within_pair`,
`test_set_used`, `tf32_enabled`, `validation_execution`. These are provenance: no code reads
them. They still enter `config_sha256` (ablation.py:343, `digest_json(cfg)`), so editing them
blocks a resume.

### 1j. Top level

`name` (the W&B run id is sha256(name)[:12], ablation.py:369), `era` (2; never read). Rebuild
configs only: `checkpoint`, `reference_npz`.

### 1k. Hard-coded constants a designer might take for knobs (all need code)

- The data order is independent of seed (ablation.py:388 uses only `order_seed`). The anchor [D9] wants the order derived from the seed, which is a generator change (set `order_seed` per seed), not code.
- The optimizer is always `Adam` with β₁ 0.9 (ablation.py:142). There is no optimizer-type key.
- Loss is CE + coefficient·KD + `model.losses` (the HGQ β·EBOPs and MonoL1 terms), ablation.py:171-176. There is no label smoothing and no class weights.
- Stream (attention score and context) input quantizers are `act_iq(6, axes=(-2,-1))` (qat.py:431-432). The softmax internals are fixed: exp input `_static_act(max(ab,10), 6)`, inv input `k0 i4 f8`, tables `i1 f11` (qat.py:453-460).
- Biases are float (`_dummy("bias")`, qat.py:398-399). The head is GAP → head_fc1 (D, ReLU) → head_fc2 (C) (qat.py:518-524).
- The calibration batch is 4096 rows (qat.py:543). The PID/EBOPs trace sample is `xt[:256]` (ablation.py:332).
- Pack runner: 15 s stagger, and an arm with no checkpoint for 30 min is killed (run_pack.py:39, 53).

## 2. Named arms already in the vocabulary

Each row lists the knobs an arm sets relative to its base (flattened JSON diff, provenance keys
omitted). Script: scratchpad `tools/cfgdiff.py`. Files: Ph `configs/` unless noted.

### 2a. pre_conference (Ph `generate_pre_conference.py`; R names `r14-l1x3-*`). Base `pre_conference-n8-w1a8`

Base: d32/h4/L2/FFN64, learned PE, norm none, `act_calib trainable` (fixed-width trainable
scale), `act_bits 8`, 101 epochs, lr 2e-5, warmup 1 + poly 100, batch 256, β₂ 0.98, wd 0.01,
clipvalue 1, es_patience 15, split 0.2, no ebops block, hls rf 256. Stage path (`train.py`).

| arm | delta |
| --- | --- |
| n{8,16,32,64}-w1a8 | `arch.n_part` only |
| -w1a6 / -w1a4 | `quant.act_bits` 6 / 4 |
| -fp32 | `quant.weight none`, `act_bits 32` |
| -w8a8 | `quant.weight int8_absmax` (in fact a static fixed<8,3> weight grid, see §4) |

### 2b. post_conference softmax (`generate_softmax_precision.py`). Base `pre_conference-n8-w1a8`

| arm | delta |
| --- | --- |
| softmax-sm4i0-n8 | `softmax_out_bits 4`, `softmax_out_i 0` |
| softmax-sm6i0-n8 | `softmax_out_bits 6`, `softmax_out_i 0` |

### 2c. post_conference budget pilots (`gen_ebops_n8.py`; R `ebops-n8-20260910-*`). Base `post_conference_budget_pilot-control`

Control against `pre_conference-n8-w1a8`: `act_calib free`, `act_policy learned_per_tensor_width`,
`act_bw_l1 1e-8`, `beta0 0`, `es_patience 0`, and an ebops block with `enable true`,
`controller none`, `monitor_widths true` (no pressure). Stage path.

| arm | delta vs control |
| --- | --- |
| b25 / b50 / b75 | `controller pid`, `target_ratio` 0.25 / 0.5 / 0.75, `beta0 1e-7`, pid {init_beta 1e-7, p 1, i 0.05, d 0, warmup 10, log, min 1e-10, max 1e-3, damp 0} |
| costfirst-b50 | `controller pid`, `pid.target_ebops 869591`, init/min β 1e-4, max β 1e-2, warmup 0, `beta0 1e-4`, `selection min_ebops`, `stop_on_target true`, `metrics [ebops]`, `sides [-1]`, lr 1e-4, warmup 0, decay 0, jit false |
| extended_budget350k (R `e1000-b350k`) | pid as b25 but `target_ebops 350000`, `selection max_auc`, `stop_on_target false`, epochs 1000, decay 999, jit false, `beta0 1e-7` |

### 2d. post_conference_budget350k ablations (`gen_ebops_ablation.py`; R `ebops-n8-20260912-ablation-r*`). Base `extended_budget350k` + `{act_granularity tensor, softmax 10/1, split_seed 1, order_seed 20260912, val_batch 1024, experiment{seed 1, checkpoint_every 1, remote_every 25}}`. Ablation path (`run_ablation.py`)

| arm | delta vs that base |
| --- | --- |
| tensor_quantization | none (the control) |
| channel_quantization | `act_granularity channel` |
| reduced_feedforward | `ffn_dim 32` |
| attention_probability_8bit | `softmax_out_bits 8` |
| gradual_budget | `experiment.target_schedule [[0,1e6],[250,7.5e5],[500,5e5],[750,3.5e5]]` |
| fixed_width_recovery | `experiment.recovery_after_epochs 800` |
| knowledge_distillation | `experiment.distillation {teacher_artifact "", T 2, coefficient 0.5}`. Ph ships an empty teacher. R's r6 names `.../BNJetTag-EBOPs-N8/model-ebops-n8-20260910-control-w1a8-s1:v0` |

### 2e. batch20260917 a00-a11 (S `reference_configs/`, Ph `configs/batch20260917/`). Base a00

a00 against extended_budget350k: `act_granularity channel`, softmax 10/1, `selection_metric
val_categorical_accuracy`, hls rf 1, seeds/split as 2d, project `BNJetTag-Batch20260917`.
N=8, 1000 epochs, lr 2e-5.

| arm | delta vs a00 |
| --- | --- |
| a01 | `act_granularity tensor` |
| a02 | `ffn_dim 32` |
| a03 | `ffn_dim 32`, `act_granularity tensor` |
| a04 | `ffn_dim 32`, `n_part 16` |
| a05 | `ffn_dim 32`, `n_part 32` |
| a06 | `ffn_dim 32`, `n_part 16`, `d_model 16` |
| a07 | `ffn_dim 32`, `n_part 16`, `n_layers 1` |
| a08 | `ffn_dim 32`, `n_part 16`, `n_heads 2` |
| a09 | `ffn_dim 32`, `n_part 16`, `target_ebops 500000` |
| a10 | `ffn_dim 32`, `n_part 16`, `target_ebops 250000` |
| a11 | `ffn_dim 32`, `target_ebops 500000` |

### 2f. batch20260918 b00-b04 × seeds 4-6. Reference a04 (`batch20260918/index.json`)

| arm | delta vs a04 (besides group and seed) |
| --- | --- |
| b00 | none (a04 replication) |
| b01 | `n_heads 1` |
| b02 | `pos_enc none`. This works in S (and the 0918 bundle, whose `launch/preflight-result.json` records `positional_table_absent: true`). It is **silently ignored in Ph/R** qat.py:462 |
| b03 | `softmax_out_bits 8` |
| b04 | `target_schedule [[0,525k],[100,420k],[200,350k]]` |

### 2g. engram E00-E07 (S `reference_configs/engram/`, generator `run_engram.py:63-97`). Base batch20260917-a04-s1

All arms: `engram_study` block present, `selection max_accuracy`, project
`BNJetTag-Engram-Experimental`, group `engram-screen`. Default memory spec (run_engram.py:56-60):
bins 8, table 512, heads 1, orders [1], gate hard, value/key/query 8, gate 4, input 16/6,
residual 24, insert after `bit_block_0_add_attn`, hash seed 17.

| arm | delta |
| --- | --- |
| E00 | `module null` (two-block reference) |
| E01 | `n_layers 1`, `module null` |
| E02 | `n_layers 1`, default spec with `gate none` |
| E03 | `n_layers 1`, default spec |
| E04 | `n_layers 2`, default spec |
| E05 | `n_layers 1`, `value_bits 4`, `key_bits 4` |
| E06 | `n_layers 1`, `bins 4`, `table_size 64` |
| E07 | `n_layers 1`, `orders [2]`, `table_size 257`. Statically infeasible at N=64 (`static_infeasible.json`, estimated 838,272 structural bitops, above 350k) |

### 2h. const0922-* (S `generate_configs.py`, 38 configs = 19 variants × N ∈ {8, 64})

Each variant is a deduplicated source config (aliases in `index.json`). Generator deltas on
every config: `n_part` → 8 or 64; epochs 50, lr 2e-4, warmup 1, decay 49; `pid.warmup 1`;
`selection max_accuracy`; `selection_metric val_categorical_accuracy`; `checkpoint_every 1`,
`remote_every 25`; seed 1; project `BNJetTag-Engram-Experimental`; group
`constituent-20260922-fast50`. It adds an `engram_study` block (with `module null` for
non-Engram arms, which switches on `cost_first`), a 2 MiB replicated cap, and the
`constituent_study` provenance block. `b04` gets `target_schedule [[0,525k],[5,420k],[10,350k]]`.
The variants are a00, a01, a02 (aliases a02/a04/a05/b00/E00), a03, a06, a07 (a07/E01), a08,
a09 (a09/a11), a10, b01-b04, e02-e07. The **anchor's base is `const0922-a07-n64-s1-fast50-fp32`**:
12,788 parameters, initial EBOPs 24,816,782 at init (`campaigns/2026-09-23-confirmation/n64-full-preflight-result.json`,
an initialization trace, not a result).

### 2i. confirm0923 / confirm0924 (`campaigns/2026-09-23-confirmation/configs*`)

| family | delta vs the same-variant const0922 config |
| --- | --- |
| confirm0923-{a00,a02,a03}-s{2,3}-e1000 (N=8) | epochs 1000, lr 2e-5, decay 999, `pid.warmup 10`, `val_batch 4096`, seed 2/3, `experiment.source_arm`, group `confirmation-20260923-architecture` |
| confirm0924-{a07,e02,e05}-n64-s{2,3}-e1000-5m | as above, plus `target_ebops 5000000`, group `confirmation-20260924-n64-full`, protocol text |

## 3. Chang-recipe gaps

"Chang code" is C at `6cdc6e34`. Columns S, Ph and R say whether the element is realizable
**on the runner that state uses for EBOPs-constrained binary training**: yes (config only),
code (a code change is needed), or n/a.

| # | recipe element | what it is in Chang's code | S | Ph | R | smallest change (on S) |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Adam defaults | `keras.optimizers.Adam()` (run_train.py:97): β₁ 0.9, β₂ 0.999, ε 1e-7, no weight decay, no clip | **probably config-only, unverified**: `optimizer_for` passes `beta_2=tr['beta2']`, `weight_decay=tr['weight_decay']` and `clipvalue=tr['clipvalue']` straight through (ablation.py:142-143), so `beta2 0.999, weight_decay null, clipvalue null` should reproduce the Keras defaults. Not checked by running. Anchor [A2] asks for an explicit path plus an ε assert anyway | same (Ph ablation.py:109-116) | same | Explicit `train.optimizer: "adam_default"` branch in `optimizer_for`, ablation.py:134-146, about 8 lines, plus an assert on `optimizer.epsilon == 1e-7` in the CPU gate. Note that R/Ph `train.py:342-347` would crash on `float(None)`; that path is not used here |
| 2 | Cosine restarts, 500-epoch period, peak 3e-3, α 1e-6 absolute, 10 floor epochs | run_train.py:21-37, 92-93: `lr = α + ½(η₀−α)(1+cos(π·min(step/490,1)))`, per epoch, no warmup, t_mul = m_mul = 1 | **code**: `ablation.learning_rate` (ablation.py:118-123) is warmup + poly only | code | code | Add `train.lr_schedule: "chang_cosine_restarts"` with `lr_cycle_epochs 500`, `lr_alpha 1e-6`, `lr_alpha_epochs 10` to `learning_rate()`, ablation.py:118-123, about 10 lines. Unit test at epochs 0, 489, 490, 499, 500, 6999 (anchor [A1]). `train.py`'s existing `cosine_restarts` (train.py:187-198) is a **different** shape: it has warmup and a *relative* floor, is on the wrong path, and must not be reused |
| 3 | Batch 2,790 | run_train.py:67 (`--batch-size` default) | config: `train.batch 2790` (ablation.py:159) | config | config | none. The last partial batch is kept (ablation.py:166-167); Chang's `Dataset` batching was not checked |
| 4 | 7,000 epochs | run_train.py:104 | config: `train.epochs 7000` | config | config | none. Note that `decay_epochs` must not be required by the new schedule branch |
| 5 | pT ≥ 2 GeV gate on train/val/test | data.py:22-26: `X *= X[..., :1] >= 2` on raw `pt` (column 5 of the 16), after the feature select, **before** standardization; the constituent's three features become 0 | **code, absent in every state** (grep for any pT gate: none) | code | code | New `arch.pt_gate_gev` (or a `data` block) applied after the pT sort/truncate and feature subset, before standardization, in `train.load_train_data` (train.py:40-51), `data.load_eval_set` (data.py:57-65; the ROC-test path) and `prepare_cache.py:91-103`, which also records it in `data_info.json` so `load_cache` (run_engram.py:183-186) refuses a mismatched cache. About 6 lines per loader. Requires a new cache ([A4]) |
| 6 | 90/10 split | data.py:7, 40-42 (`val_size=0.1`); train+val = 620,000 jets from the 150-particle *train* files, test = the *val* files | **code**: `validation_split` is honoured at prepare_cache.py:100, but 496,000/124,000 is hard-asserted (prepare_cache.py:36-37, 101; run_engram.py:207-208) | config (Ph `prepare_arrays` is generic, ablation.py:43-57) | config (same) | Replace the literals with values derived from `validation_split` and `n_raw`: prepare_cache.py:36-37, 101 and run_engram.py:207, about 5 lines. Also a new cache |
| 7 | No sample or class weights | none in C | yes (S has no weighting at all) | yes | yes (`pt_weights` absent or disabled) | none |
| 8 | Checkpoint cadence | C keeps no resume checkpoints: `ParetoFront` saves non-dominated epochs with `val_accuracy > 0.5 and ebops < 5e5` (run_train.py:83-89) | S writes a full optimizer checkpoint **every epoch** (ablation.py:456). `experiment.checkpoint_every_epochs` is read nowhere | same | same | Honour `checkpoint_every_epochs` at ablation.py:456 (about 3 lines), with the resume rollback of `model_best` / `model_min_ebops` / `model_unconstrained` / `best_feasible` ([A5], restore_checkpoint ablation.py:218-246, about 15 lines) and 500-epoch boundary snapshots ([A6], about 10 lines) |
| 9 | Chang width init 7/7 | `get_model(model, 7, 7, 1e-8, ...)` (run_train.py:76), in model.py:278-295: weights `kbi b0=7, i0=0, WRAP`, `i_decay_speed 1e-3`, MonoL1 1e-8 on i and f; activations `kif f0=7, ic MinMax(0,12)`, **WRAP**, MonoL1 on f; `beta0 0`. xfm overrides weights to `b0=4, f0=4, SAT_SYM` (model.py:186) | **code** for activations. Our free widths start at `act_bits` total with an MSE-calibrated i (qat.py:542-575, f = bits−1−i), SAT/RND_CONV, `ic MinMax(-8,12)`, `fc MinMax(-8,16)`, MonoL1 on i and f (qat.py:298-302). The weight half is n/a: binary is the object of study | code | code | Add `quant.act_init {"mode": "fixed", "f0": 7, "i0": ?}` plus optional `act_ic`, `act_fc`, `act_overflow` to `_free_act` (qat.py:279-302), and skip `calibrate_activations` in `matching_initialization` (ablation.py:98, 107) when the mode is fixed. About 20 lines. **Hazard:** WRAP overflow in training is not our deploy grid (qat.py docstring 292-293: SAT so that train == deploy), so a WRAP arm needs its own HLS precision check. `beta0 0`, by contrast, is config-only (`quant.beta0`) |
| 10 | tanh LUT activation | `QAffinedUnaryFunctionLUT('tanh')` before the MHA and before the FFN (model.py:194, 198); `table` scope `bc=Min(4)` (model.py:188) | **code** (qat.py uses ReLU only; `ffn_act` is never read) | code | code | The layer exists in hgq2 0.1.9 (activation.py:76). Add `arch.pre_block_act: "tanh_lut"` in the block, qat.py:486 and :509, about 12 lines. **Export:** `convert_binary.py` / `build.py` have no LUT layer, so the HLS path needs new code and its EBOPs accounting of `table` quantizers must be checked. It does not touch the ±1 weights |
| 11 | Fused BN | `QEinsumDenseBatchnorm` everywhere except the last FFN and output layers (model.py:192, 199, 205-207) | **code** | code | code | Hazard for the thesis: a fused BN folds γ/σ into the kernel, so the effective weights stop being ±β. Binary-safe form: a `BitQEinsumDenseBatchnorm` that applies BN as a post-matmul per-channel affine (as build.py does with a frozen `QBatchNormalization` for β, build.py:95-120), with `binary_gate` still checking the kernel only. About 40 lines of training code; export needs the per-channel affine (multipliers, a possible DSP cost, and the 0-DSP headline must be re-checked) |
| 12 | Chang head GAP→32→32→32→5 | model.py:204-208 (three BN+ReLU layers of 32, then a plain dense to 5) | **code**: the head is GAP→D→C (qat.py:519-524) | code | code | `arch.head_dims [32,32,32]`: loop at qat.py:519-524, extend `expected_binary_layers` (ablation.py:249-257), fold/scale classes in binarize.py:28-34 for export, and the head in convert_binary.py. About 25 lines of training code plus export |
| 13 | Key dim decoupled from d_model | `QMultiHeadAttention(h=2, key_dim=16)` with d24 (model.py:195) | **code**: `E = D // H` (qat.py:350) | code | code | `arch.head_dim` (default D//H), qat.py:350 and :487-489, :504, about 4 lines; plus export |
| 14 | β control | open-loop `PieceWiseSchedule 2e-8 → 3e-7 (log, e2000) → 3e-6 (e7000)` (run_train.py:90); the paper's text says PID | S hard-codes `BetaPID` (ablation.py:355-362); `train.ebops.beta_schedule` is inert there | same | same | Honour `controller: "schedule"` in `run_training` with `PieceWiseSchedule` (about 12 lines). Anchor [D5] keeps PID, so this is Delta-only |
| 15 | Selection | `val_accuracy`, Pareto front, `ebops < 5e5` | config: `experiment.selection_metric`. The tie-break order is set by `cost_first = bool(cfg.get('engram_study'))` (ablation.py:421), and every S config has the block | AUC only (Ph ablation.py:301) | AUC only | Explicit `experiment.cost_before_auc` (anchor [A13]), 2 lines; also an AUC-selected feasible copy ([A19]), about 6 lines |
| 16 | Standardization on train+val | data.py:28-31 | ours is train-only (ablation.py:51, prepare_cache.py:102); a deliberate deviation (anchor [D7]) | same | same | none by design |
| 17 | float16 input storage | data.py:11, 33 cast X to float16 after standardizing | we keep float32 | same | same | Not in the brief's list. It is an input quantization of about 11 significand bits, so it could move a number slightly. Opt-in `data.input_dtype float16`, about 3 lines in prepare_cache |
| 18 | Backend and numerics | JAX, `jax_default_matmul_precision tensorfloat32` (model.py:20-23) | TF, TF32 off (run_study.py:90-91) | n/a | n/a | none (deliberate, anchor [L3]) |

**Top gaps for the anchor (all code, all on the S runner):** (2) the Chang cosine schedule; (5)
the pT gate, including the ROC-test loader; (6) the hard-coded 80/20 split asserts; (8) checkpoint
cadence and resume rollback; (15) the explicit tie-break. (1) is probably config-only but
unverified. (9)-(13) matter only for "Chang-architecture" Delta arms and each needs export work
before any HLS claim.

## 4. Binarizer and quantizer options (S `qat.py`, `binarize.py`)

**Weight schemes** (`quant.weight`, dispatched at qat.py:353-356, 405-413, 422-427):

| value | training forward | reported to EBOPs / hls4ml | notes |
| --- | --- | --- | --- |
| binary_absmean | `bitnet_binary_ste` (qat.py:43-65): per-tensor α = mean(W), wc = W−α, β = mean\|wc\| + 1e-6, q = +1 if wc ≥ 0 else −1 (never 0), `ws = wc / stop_gradient(β)`, output `(ws + sg(q − ws))·β` | `_binary_kq` KBI 1-bit, `SAT_SYM`, frozen (qat.py:228-232): **always reports 1 bit, whatever the STE does** | Plain identity STE with **no \|w\| ≤ 1 gradient clip** (the BNN "hard-tanh" STE is not implemented). The backward is bounded by the stop-gradient on β (docstring 51-55). Layers: input_proj, Wq, Wk, Wv, Wo, fc1, fc2 per block, head_fc1, head_fc2 (+ pair_fc1/2). Export re-binarizes with the same math, `binarize.absmean_binarize` (binarize.py:37-45), with fold classes (binarize.py:28-62; every layer is "explicit" when `norm none`) |
| none | float kernel, dummy quantizers | 0 | FP32 baseline |
| int8_absmax | `_static_w8(i0=2)`: frozen fixed<8,3>, `SAT`, RND_CONV (qat.py:305-310) | 8 bits | The name is misleading: there is **no absmax scaling**, only a fixed grid. W8A8 baseline |
| kbi_learnable | **no branch in `build_qat_model`**: it falls into the `else` (w8a8) branch and builds the static int8 grid | 8 bits | Accepted by config.py:40 and named by train.py:559 `_variant`, but not implemented in qat.py in any state. A trap: a config that sets it trains W8A8 silently |

**Activation policies** (`quant.act_calib`, qat.py:357-363, 388-396):

| value | quantizer | trainable | width |
| --- | --- | --- | --- |
| frozen (default) | `_static_act`: KIF k1, SAT, RND_CONV, frozen (qat.py:235-241) | no | fixed `act_bits`; i from MSE calibration on 4096 rows (qat.py:542-575), f = bits−1−i ≥ 1 |
| trainable | `_trainable_act`: KBI with b pinned by `Constant(act_bits−1)`, i trainable in [0, bits−2] (qat.py:244-263) | scale only | fixed |
| recalib | frozen, re-calibrated at `act_recalib_epochs` | no | fixed; **train.py path only** (train.py:396-400), inert in S |
| free | `_free_act`: KIF, SAT, RND_CONV, `ic MinMax(-8,12)`, `fc MinMax(-8,16)`, MonoL1(`act_bw_l1`) on i and f; `MeanMonoL1` when per channel (qat.py:267-302) | width | learned; init = the calibrated `act_bits` grid. **The only policy S accepts** (run_engram.py:114) |

Granularity (`act_granularity`): `tensor` (heterogeneous_axis `()`), or `channel` (last axis;
`(-2,-1)` for 4-D einsum inputs and the attention streams). Softmax output (the attention
probability into A·V): unsigned KIF with `i = softmax_out_i`, `f = softmax_out_bits − i`, frozen
(qat.py:496-499). The softmax internals are fixed (qat.py:453-460).

**What a new STE or scaling variant touches** (for example a clipped STE, per-channel β, a
learned scale, or ReCU/ReActNet-style shifts):
1. `qat.py:43-65`: a new function beside `bitnet_binary_ste`, or a `quant.ste` / `quant.weight_scale` key read at qat.py:353 and passed to `BitQEinsumDense.call` / `BitQDense.call` (qat.py:75-108). About 15-30 lines.
2. `run_engram.validate_cfg` (run_engram.py:114) only admits `binary_absmean`, so relax it or add the new key beside it.
3. `ablation.binary_gate` (ablation.py:260-267) asserts exactly two symmetric values **per tensor** via `effective_weight_values` (qat.py:612-620). A per-channel β legitimately yields 2·C values, so the gate must become per-channel (two values per output channel), about 8 lines. It must keep failing on any zero or any third value per channel (the binary constraint).
4. Export: `binarize.absmean_binarize` / `binarize_checkpoint` (binarize.py:37-83) must reproduce the same q and β. The per-channel β becomes a per-channel affine in build.py (the explicit-scale path, build.py:95-120) and convert_binary.py. Per-channel multipliers are a DSP risk to the 0-DSP headline.
5. EBOPs: `_binary_kq` makes every variant report as 1 bit (qat.py:228-232), so scale multipliers are invisible to native EBOPs. A card must state that limitation.
6. Pairing: `matching_initialization` copies latents by path and shape (ablation.py:61-78), so an STE-only change keeps the same init at the same seed, and it pairs with the anchor.

## 5. Generators, manifests, gates

**Config generators (they write JSON; none submits):**
- S `generate_configs.py`: groups `reference_configs/{batch20260917,batch20260918 (*-s4), engram}` by canonical content, asserts 19 groups, emits const0922 N8/N64 pairs plus `index.json` with per-config sha256, and asserts that pairs differ only in N (lines 73-79).
- S `run_engram.py plan` (`configs()`, lines 63-97): engram E00-E07.
- Ph `configs/generate_pre_conference.py` (`make(N, variant)`), `generate_softmax_precision.py`, `gen_ebops_n8.py` (`make_pilot`, `make_cost_first`, `make_long_budget`), `gen_ebops_ablation.py` (`make_ablation`). R adds `gen_ptw.py`, `gen_r14.py`, `gen_r15_gamma.py`.
- The batch20260917/18 generators are not in S or Ph (the 0918 launch README names `run_batch_screen.py` and `check_batch20260918_preflight.py`). The confirmations use `campaigns/2026-09-23-confirmation/build_n8_configs.py` and `build_n64_confirmation.py`.

**Packing and manifests:**
- `packs.json` / `canary_packs.json` (S): lists of `index.json` row indices per GPU pod. `run_pack.py` takes `JOB_COMPLETION_INDEX` → a pack, launches one `run_study.py train --index` subprocess per arm, and exits 1 if any arm fails (run_pack.py:40-65). That is the failed-arm coupling the anchor's [A12] wants removed.
- `campaigns/2026-09-22-constituent-screen/freeze_jobs.py`: tars the code, builds an immutable ConfigMap `kai-n8n64-code-<sha10>` (lines 11-21), and generates preflight / canary / screen Indexed-Job JSON from a template job with sha256-checked extraction and `BNHGQ2_CODE_SHA256` (lines 23-78). It **never submits**. Evidence: `static-checks.json`, `final-static-checks.json` (manifest lint: 0 errors, 1 warning; server dry run PASS; 38 CPU-preflight models).
- `nrp-lab/nrp_doctor.py lint`: `lint_job` checks required GPU-product reachability, known-bad nodes, `parallelism < completions`, `backoffLimitPerIndex` (suggests 3), `maxFailedIndexes`, a missing `podFailurePolicy` for DisruptionTarget, and rule PACK (the `bnjettag.io/arms-per-pod` label; about 2 CPU and 6 Gi per arm; the 40 % GPU floor). `.claude/hooks/pre-kubectl-lint.py` enforces it on `kubectl apply|create|replace -f`.

**CPU gates that exist:**

| gate | where | what it checks | pass string |
| --- | --- | --- | --- |
| screen preflight | S `run_study.py preflight` (43-83) | cache identity across N; per config: `validate_cfg`, build, `binary_gate`, EBOPs trace, finite predictions, save → reload → predictions within **atol 2e-6 / rtol 2e-6** (lines 71, 74), re-traced EBOPs equal | `CONFIG_PREFLIGHT_PASS <name> params <n>`, `PREFLIGHT_ALL_PASS <shard>` |
| checkpoint verification (end of each run, GPU) | S `run_study.py train` (125-131) | reload the selected checkpoint, re-trace EBOPs equal, recompute validation AUC and accuracy within **atol 1e-7** of the recorded values | `CHECKPOINT_VERIFICATION_PASS` |
| per-epoch candidate reload | ablation.py:397-403 | every epoch is validated on a freshly reloaded `validation_candidate.keras`; EBOPs are equal after reload | assert |
| Engram unit checks | S `check_engram.py` | addressing, masks, gradients, serialization; per arm build/binary/init/cost/reload | `ENGRAM_PREFLIGHT_PASS` |
| confirmation preflights | `campaigns/2026-09-23-confirmation/preflight_confirmation.py`, `preflight_n64.py` | build, reload, initial EBOPs, data hashes, init evidence | `CONFIG_PREFLIGHT_PASS`, `PREFLIGHT_ALL_PASS` (n64-full-preflight.log) |
| Ph/R checks | `check_ebops_target.py` (EBOPs gradients, width movement, PID, reload), `check_ebops_ablation.py` (matched init, variants, schedules; `--integration` is cluster-only), `check_extended_training.py` / R `check_ebops_long.py`, `check_resource_priority.py` / R `check_ebops_costfirst.py` | as named | per script |
| R `preflight_final.sh` | R only | pinned pip install, a HEAD request for the Zenodo tarball, build plus binary gate for `configs/${BNF_CONFIG_GLOB:-final-*.json}`. **No reload check**, and the default glob matches no current R config | `PREFLIGHT_ALL_PASS` |

**Duration of one CPU build + reload gate.** No per-config timing is recorded for the S preflight
(the log carries only TF start stamps). The one recorded wall time: "The revised Job completed
successfully at 2026-09-17T15:21:45Z after 12m07s, printing `BATCH_CACHES_ALL_PASS` and
`PREFLIGHT_ALL_PASS`. All twelve model builds/gradient steps/save-reloads passed ... Synthetic
smoke testing took 228.89 seconds." (`campaigns/2026-09-17-training-batch/launch/cache-preflight-notes.md:15`;
2 CPU, 8 GiB, and the 12m07s includes building the N8/N64 caches). No per-config figure can be
derived from it without timing a run, and none was run here.

## 6. State differences that matter to a method designer

- **Ph/R vs S `ablation.py`:** Ph/R select on AUC only, validate on the live model (not a reloaded one), have a hard-coded 15-layer binary gate (so L=1, A07 and the anchor **fail** there), no `model_builder`/`epoch_observer` hooks, no Engram `MemoryAdam`, and run names hard-coded `-s1` (Ph ablation.py:268).
- **Ph/R vs S `qat.py`:** Ph/R lack `pos_enc` handling (always adds PE) and `with_pos_enc`.
- **R only:** `pt_weights` on the `train.py` path.
- **S only:** `engram.py`, accuracy selection, reload-based validation, `stop_after` screening, `run_study.py` / `run_pack.py` / `prepare_cache.py`.
- **Export gap in S:** `convert_binary.py:405` calls `get_layer("pos_enc")` unconditionally, so a `pos_enc none` checkpoint (anchor arm F, arm E) cannot be exported yet (known since `campaigns/2026-09-18-training-batch/launch/README.md:30-31`).
- **Matching init:** `matching_initialization` builds a reference with `ffn_dim 64`, tensor grids and softmax 10/1 at the same seed, and copies every equal-path, equal-shape latent (ablation.py:61-78). An arm that changes one shape keeps every other weight identical to the anchor at that seed. Its FFN kernels are then fresh, and `equivalent_to_weight_reference` is False for A07 itself (FFN 32).

## 7. Recommendation: where to stage method code

Stage a **patch series against the S bundle**, pinned by tarball sha256 `26f3cc40...`, under
`campaigns/2026-09-26-delta/code/`:

```
code/
  BASE.json            bundle path, tarball sha256 26f3cc40..., source sha256 7f9e9307..., pins
  apply.sh             extract the tarball to a build dir, verify sha256, apply patches in order
  patches/0001-*.patch unified diffs, -p1 against the bundle's code/ root
  generate_delta.py    anchor + delta per card -> configs/, index.json, packs.json
  tests/               CPU unit tests (schedule values, tie-break order, per-channel gate, pT gate)
  GATE.md              CPU build/reload gate report (PREFLIGHT_ALL_PASS lines verbatim)
```

Reasons:
1. **It is the pinned lineage.** The anchor STUDY cites source sha `7f9e9307`, and the S bundle's files hash to exactly that. Ph and R are older lines on which A07 fails the 15-layer gate and `pos_enc none` is silently ignored.
2. **The tarball is immutable and sha-verified.** Pc is byte-identical today, but it sits in a broken worktree Kai has not decided on, and the live source is in the `research/` symlink tree (freeze_jobs.py:11). A sha-pinned tarball plus patches reproduces the shipped code without touching either.
3. **Patches are reviewable and reversible,** and they rebase cleanly onto whichever tree Kai makes canonical (see `campaigns/2026-09-26-code-line-merge`).
4. **One series serves wave 0 and Delta.** Order: first the anchor's constraints ([A1] schedule, [A2] optimizer, [A3]/[A4] pT gate + 90/10 cache, [A5]/[A6]/[A15] cadence and rollback, [A12] failed-arm isolation, [A13] tie-break, [A19] AUC copy); then the Delta methods, one patch per mechanism.
5. **Rule for every patch:** opt-in behind a new config key whose absence reproduces the current behaviour byte-for-byte. The gate re-verifies that each existing `const0922-*` config gives an unchanged `digest_json(cfg)` and unchanged init `kernel_hashes`, so screen evidence stays comparable and the "config differs, code does not" rule of the house holds.
6. **Freeze and ship the way the screen did:** `apply.sh` output → tarball → new sha → ConfigMap via a copy of `freeze_jobs.py` (no submit). The CPU gate is `run_study.py preflight` (build, binary gate, trace, reload within 2e-6) plus the new unit tests. `PREFLIGHT_ALL_PASS` is required before any canary.

Kai decisions this does not settle: which tree becomes canonical, and the license of C before
anything is lifted from it verbatim. The Chang-architecture elements (9)-(13) are
re-implementations on our layers; none needs C's source text.

## Log lines to append

- decisions.md (finding, suggest `/log-decision`): 2026-09-27. `quant.weight: "kbi_learnable"` is accepted by `bnhgq2/config.py:40` in every state, but `qat.build_qat_model` has no branch for it and builds the static int8 (W8A8) grid instead. Any config that sets it trains W8A8 silently. Check: grep `kbi_learnable` in `qat.py` returns nothing (S, Ph, R).
- decisions.md (finding): 2026-09-27. In `publication/code/hgq2` and `bnjettag/code/hgq2`, `arch.pos_enc: "none"` is ignored (qat.py:462 adds the positional table unconditionally). The batch20260918 b02 runs used a bundle with `pos_enc` support (`positional_table_absent: true` in their preflight), so no past run is affected. The trap applies to reruns from those trees. Check: `grep -n AddPositional publication/code/hgq2/bnhgq2/qat.py`.
- decisions.md (finding): 2026-09-27. In the screen-bundle runner (`ablation.run_training`), the keys `train.lr_schedule`, `train.ebops.{enable,controller,beta_schedule,selection,stop_on_target,target_ratio}`, `train.clip_mode`, `train.es_patience`, `arch.input_std`, `quant.act_recalib_epochs` and `experiment.checkpoint_every_epochs` are inert. Only the `train.py` path, or no code at all, reads them. Check: §1 of `campaigns/2026-09-26-delta/inventory/code-surface.md`.
- research-log.md: 2026-09-27. HGQ2-examples jsc150 at `6cdc6e34` imports `StopIf` and uses `QLinformerAttentionT`, and neither is in hgq2 0.1.9 (PyPI wheel sha256 `7497542...c43c`), so Chang's HEAD code needs a newer hgq2 than our pin. There is no LICENSE file in that clone. https://pypi.org/project/hgq2/0.1.9/ (accessed 2026-09-27).
