# PLAN_patches.md — ml-engineer (patches to existing files), 2026-09-27

Owner protocol step 1: plan first. Crash notes at the bottom.

## Scope (from the orchestrator's brief)

- Write now against the screen tarball (sha256 26f3cc40...5a45): 20 slugs, one patch each.
- Blocked on the anchor series ([A1]/[A3]/[A4]/[A20]): 12 slugs, design notes only in `BLOCKED.md`.
- The other ml-engineer owns NEW files (generator, new modules, diag scripts). I create only
  `bnhgq2/atlas_keys.py` (the single registry the brief asks for) plus tests outside the series.
- I do not touch `campaigns/2026-09-26-training-batch/` (read-only for BLOCKED.md), do not
  commit to any project repo, do not launch.

## Mechanics

1. `atlas-dev/` in the scratchpad: extract tarball, `git init`, commit pristine `code/`.
2. One commit per slug; `git format-patch` -> `code/patches/NNNN-<slug>.patch`.
3. `code/apply.sh`: re-extract tarball, check sha256, `git init` in a temp build dir,
   `git apply --3way` each patch in order.
4. Env: `uv run --no-project --python 3.12 --with tensorflow==2.21.0 --with keras==3.15.0
   --with <hgq2-0.1.9 wheel, sha256 7497542...c43c> --with quantizers==1.2.2 --with numpy==2.5.0
   --with scikit-learn==1.9.0 --with h5py==3.14.0` (pins from `requirements-cpu.txt` in the bundle,
   which equal the job YAML pins recorded in code-surface §0).

## Key registry

`bnhgq2/atlas_keys.py`: one `REGISTRY` dict {dotted key: (slug, validator)}, `get(cfg, key,
default)`, `validate(cfg)`, `export_blockers(cfg)`. `run_engram.validate_cfg` gets one hunk
calling `atlas_keys.validate(cfg)`; the two existing rejections (weight scheme, distillation)
consult the registry. Each slug appends its own block to the registry (end of file).

## Opt-in rule

Every default path keeps the same Python ops in the same order, so the TF graph and every
number are identical. Layer options ride in a `binary` kwarg on `BitQEinsumDense`/`BitQDense`,
serialized only when non-empty, so saved `.keras` configs of existing models are unchanged.

## Per-slug design (key names from atlas.json entries' config_delta)

| slug | key(s) | where | mechanism |
| --- | --- | --- | --- |
| binarizer-center-flag | quant.binary_center (bool, default true) | qat STE, binarize | skip alpha centering |
| ste-variants | quant.ste {bounded, clip_identity, ede}; quant.ste_ede_period (int epochs) | qat STE + epoch loop | clip_identity: grad 1{|wc|<=1}; EDE: k·tanh(t·ws) surrogate, t from 0.1 to 10 over each period (IR-Net), set per epoch via a non-saved tf.Variable |
| latent-clip | quant.latent_clip (float > 0) | ablation epoch_step | clip binary latents to [-c, c] after each apply_gradients |
| beta-mode | quant.beta_mode {absmean, absmean_pow2, learned_pow2} | qat STE, binarize | pow2 rounding of absmean with STE; learned log2 scalar per layer, initialized from absmean after matching init |
| channel-gain-pow2 | quant.channel_gain {layers: "all_binary" or [names], mode: "pow2"} | qat, ablation.binary_gate, binarize | per-output-channel 2^round(s), s init 0 (forward identical at init); gate per channel |
| init-from-checkpoint | experiment.init_checkpoint (path or artifact name under $BNHGQ2_ARTIFACT_ROOT) | ablation.matching_initialization | copy kernel/bias/pos_table by path+shape into reference and model before calibration |
| kd-unblock-s-runner | experiment.distillation {teacher_artifact, temperature, coefficient} | run_engram.validate_cfg, ablation | admit; teacher model loaded and run on the fly inside the step (works with augmentation) |
| kd-attention-map | experiment.distillation.attention_coefficient | ablation epoch_step | KL(teacher attn || student attn) over keys, mean over b,h,t; probe model on the softmax layers |
| latent-ema-eval | experiment.latent_ema_decay | ablation | per-step EMA of binary latents; candidate saved/evaluated with EMA latents swapped in; shadow saved beside the checkpoint |
| augment-eta-phi-reflect | data.augment {reflect_eta, reflect_phi} | ablation epoch_step | per-jet sign flips in raw space, applied in standardized space (x -> -x - 2mu/sigma); host RNG from (order_seed, epoch); train only |
| weight-scheme-baselines | quant.weight none/int8_absmax admitted; quant.layer_weight_override {layer: scheme} | run_engram.validate_cfg, qat, ablation | labelled baselines/teachers; binary gate covers only binary layers |
| ternary-absmean | quant.weight "ternary_absmean" | qat, ablation.binary_gate | b1.58 absmean ternary, labelled ternary gate |
| hgq-learnable-weights | quant.weight "hgq_learnable" | qat build branch | HGQ kbi learnable weight widths (Sun et al. transformer values: b0 4, i0 0, SAT_SYM, MonoL1) |
| head-dims | arch.head_dims list | qat head, ablation.expected_binary_layers + matching assert | head_fc1..k hidden + head_fc{k+1} logits |
| pre-block-tanh-lut | arch.pre_block_act "tanh_lut" | qat block | hgq2 QAffinedUnaryFunctionLUT('tanh') before Wq/Wk/Wv and before fc1 |
| beta-schedule-s-runner | train.ebops.controller "schedule" + train.ebops.beta_schedule | ablation.run_training | hgq2 PieceWiseSchedule behind the PID interface; "pid"/absent unchanged |
| screen-collapse-stop | experiment.collapse_stop {threshold, patience, after_epoch} | ablation epoch loop, run_study status | stop and record COLLAPSED.json; exit 0 (not a failure), so run_pack is untouched |
| accumulator-ebops-metric | experiment.accumulator_metric true | ebops_calc, ablation logs | b_acc = b_act + ceil(log2 fan_in) per binary layer |
| diag-sign-flips | experiment.diagnostics contains "sign_flips" | ablation (observer composition) | flip fraction and flip-flop ratio per layer per epoch |
| diag-beta-trajectory | experiment.diagnostics contains "beta_trajectory" | ablation (observer composition) | beta per layer and |wc|/beta histogram |

Export: binarize.py math for center/beta-mode/channel-gain; convert_binary gets one guard
that refuses any atlas key with no HLS path yet (DR-17). No HLS claim is made for any slug.

## Tests (CPU, synthetic, tiny) in `code/tests_patches/`

(a) per-slug mechanism unit test; (b) invariance gate pristine vs full series on const0922
a07-n64 (+ a00-n8, a01-n64, b02-n64, b04-n8): cfg digest, init kernel_hashes, model JSON,
initial EBOPs, predictions, one epoch_step (2 batches) -> loss and all weights hashed;
(c) per slug one keyed config builds, binary gate (or labelled gate), save -> reload within 1e-7.

## Crash notes

- 2026-09-27: tarball extracted to scratchpad/atlas-dev, env import OK (tf 2.21.0, keras 3.15.0).
- Anchor tree `campaigns/2026-09-26-training-batch/code/tree/` read 2026-09-27: `diff -rq`
  against the tarball prints nothing, so its patches are not on disk there yet; key names for
  BLOCKED.md come from decisions.md 2026-09-27 "chang0926 code".
- 2026-09-27 (resumed after a rate-limit cut): 21 patches exported (0001 registry + 20 slugs);
  apply.sh on a fresh extraction reproduces the dev tree exactly; invariance gate 7/7 const0922
  configs identical (69 s); 21 slug tests PASS incl. an E-shape sweep (423 s, 1 CPU thread).
  Fix found by the E sweep: hgq2's build wrapper reads qkernel before extra variables exist
  (beta_log2, channel_gain_log2); squashed into 0005/0006. Rebase probe onto anchor 72a1290 in
  BLOCKED.md.

## Log lines to append

For `.claude/memory/decisions.md` (newest on top; the orchestrator appends once):

- 2026-09-27 (ml-engineer, staged, not shipped) — method-atlas patch series `code/patches/0001-0021` on the screen tarball 26f3cc40; every key opt-in, absent keys reproduce the bundle bitwise (7 const0922 configs: cfg digest, init kernel hashes, model JSON, EBOPs, predictions, one optimizer epoch; CPU, 1 thread, TF_DETERMINISTIC_OPS=1). Choices that change what a number means:
  - New trainable scalars (`beta_log2` for `quant.beta_mode learned_pow2`, `channel_gain_log2` for `quant.channel_gain`, LUT scale/bias and table b/i for `arch.pre_block_act`, kbi weight b/i for `quant.weight hgq_learnable`) sit in the weight variables: they get AdamW weight_decay 0.01 and clipvalue 1.0, and `recovery_after_epochs` does not freeze them (it freezes activation i/f only). Left as-is; changing it belongs to the [A2] optimizer hunk.
  - `quant.weight ternary_absmean` (labelled baseline) is billed 2 bits per weight to native EBOPs (kbi b0 2), not log2(3); it has its own ternary gate and the binary gate refuses ternary layers.
  - Pre-block tanh LUT table: kbi SAT_SYM, b0 7, i0 0, b >= 4 (Min(4)), MonoL1 on b and i; SAT_SYM instead of Chang's WRAP so tanh near +-1 cannot wrap.
  - Per-channel binary gate (`quant.channel_gain`): each output channel holds values in {-b_c, +b_c}, one or two of them (a fan-in-3 input_proj column can carry a single sign); zero or a third value fails.
  - EDE STE: T_min 0.1, T_max 10 (IR-Net), restarted every `quant.ste_ede_period` epochs, updated per epoch; `clip_identity` clips the raw centered latent at +-1 and has no beta gradient path.
  - `experiment.latent_ema_decay`: candidate, model_best and the selection use EMA latents; training continues on live latents; the shadow is saved in each checkpoint leaf. Under [A20] WRAP the EBOPs trace would re-track i on the EMA weights (flag at rebase).
  - KD on the S runner: the teacher is resolved as a file path or `$BNHGQ2_ARTIFACT_ROOT/<name>/model.keras`, its `input_std.json` must equal the cache's, and it runs per (augmented) batch; the attention-map term enters the loss while the logged `distillation_loss` stays logit KD.
  - `experiment.accumulator_metric` logs per-binary-layer b_acc = b_act(max) + ceil(log2 fan_in) beside native EBOPs; no accumulator-inclusive total is emitted because the cards define none.
  **Check:** `code/apply.sh <dir>` then `tests_patches/pyenv.sh tests_patches/gate_invariance.py` + `compare_fp.py` -> INVARIANCE_GATE_PASS; `slug_tests.py` -> SLUG_TESTS_ALL_PASS.
- 2026-09-27 (finding, generator-facing): atlas `train.optimizer: "adam"` is not an anchor value (`adam_ours` | `adam_default`, anchor ablation.py l.178); `quant.act_f0` has no anchor key; `arch.pt_gate_gev: 0` makes a gated (pT >= 0) cache in the anchor while `null` is ungated. The anchor already reads `train.lr_t_mul` / `train.lr_m_mul`. New keys with no atlas entry, named by this series: `experiment.collapse_stop`, `experiment.accumulator_metric`, `experiment.diagnostics`. **Check:** `code/BLOCKED.md`.
- 2026-09-27 (finding): hgq2 0.1.9's QLayer build wrapper evaluates `qkernel` (collapse warning) before a subclass's post-build variables exist; any layer option that adds variables after `super().build` must tolerate their absence. **Check:** `slug_tests.py --only E-shape-sweep`.

## Follow-up 2026-09-27 (review A1-v3)

- 0022 strict-keys, 0023 body-deepsets wiring, 0024 bop-optimizer wiring (call sites, not
  optimizer_for). apply.sh copies newmods/ first. Full tree: invariance 7/7 (57 s), 24/24 slug
  tests (467 s). At 0022 only: M004/M006/M020 refused by key name.
- Log line (decisions.md): 2026-09-27 — strict config keys on the screen runner (patch 0022): a
  key no code path reads is refused by name; inert bundle keys are accepted only at their bundle
  value (e.g. `train.es_patience` 0, `train.ebops.selection` max_accuracy,
  `experiment.checkpoint_every_epochs` 1, controller pid|schedule). Deep Sets and Bop are wired
  (0023/0024); Linformer stays refused until [A20]. **Check:** `slug_tests.py --only strict-keys`
  on `apply.sh <dir> 0022` (refuses M004/M006/M020) and on the full series (refuses M004 only).

## Fix 2026-09-27 (GATES.md v4: M018 clip_identity fails the binary gate after training)

- Cause: `wg + stop_gradient(q*beta - wg)` is not exactly q*beta in float32 (measured 10-83 % of
  entries off by an ulp, depending on latent scale). Fixed in 0003 (squashed, series re-exported):
  forward `stop_gradient(q*beta) + (wg - stop_gradient(wg))`, same gradient.
- Checked the other forms numerically (float32, 2e5 draws, latent sd 0.3-40): bundle bounded
  `ws + sg(q - ws)`, EDE `s + sg(q - s)`, round-STE `s + sg(round(s) - s)`, absmean_pow2
  `beta + sg(2^n - beta)`, `pow(2, n)`: 0 inexact. Ternary (q = 0 case) exact by construction.
- Tests: `one_step` now runs 2 optimizer steps and then `ablation.binary_gate`; added to the
  center-flag, channel-gain and E-shape-sweep tests (Bop, EMA and mini_train paths already gate
  after training). The new gate fails on the old 0003 and passes on the fixed one.
- Log line (decisions.md): 2026-09-27 — `quant.ste clip_identity` forward made exactly q*beta
  (patch 0003); before the fix its layers held 4-6 values within an ulp of +-beta after one step.
  **Check:** `slug_tests.py --only ste-variants` (post-step binary gate).
