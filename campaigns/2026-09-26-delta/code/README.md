# code/ ledger — Delta (2026-09-26-delta; renamed from method-atlas 2026-09-27)

One row per patch slug (38, from delta.json `patches`) plus the generator/manifest row. Owners edit only
their own rows. Status: `gated-on-tarball` (in `patches/`, the series for the public repo, tests
pass on the screen tarball 26f3cc40...5a45) / `gated-on-anchor-42abed4b` (in `patches-anchor/`,
tests pass on the anchor regime-B freeze 42abed4b, ConfigMap `kai-chang0926-code-42abed4b5d`;
superseded 77f1ca4e) /
blocked with reason / written / not started. Rows marked "(patches-anchor only)" depend on anchor
code and do not exist in `patches/`. Pinned env for every test (tensorflow 2.21.0, keras 3.15.0,
hgq2 0.1.9, quantizers 1.2.2, numpy 2.5.0, scikit-learn 1.9.0, h5py 3.14.0, hls4ml 1.3.0), CPU,
1 thread, synthetic inputs. Nothing here is a result.

| slug | owner | status | tests passed | notes |
| --- | --- | --- | --- | --- |
| lr-schedule-variants | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after) | patches-anchor/0027; train.lr_warmup_epochs w: lr*(epoch+1)/w for epochs < w of the first [A1] cosine cycle; M031 m_mul = anchor train.lr_m_mul (no code); needs lr_schedule chang_cosine_restarts |
| beta-schedule-s-runner | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0013-beta-schedule-s-runner.patch; train.ebops.controller "schedule" + beta_schedule via hgq2 PieceWiseSchedule; "pid" unchanged; rebased beside [A1] chang_cosine_restarts |
| softmax-table-min-bits | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); b floor after a push = key (2) / default 4 | patches-anchor/0026; quant.softmax_table_min_bits: [A20] _chang_table Min(4) -> Min(k); needs softmax_quant chang; export refused |
| qk-stream-min-bits | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); i+f >= 1 after init and after the step, V untouched | patches-anchor/0031; quant.qk_min_bits: f := max(f, k - i) on both attn_scores inputs at init and after every optimizer step; under WRAP a post-step projection (i data-tracked) |
| ebops-group-weight | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); per-layer _beta = w x beta; 2-epoch run_training | patches-anchor/0030; quant.ebops_group_weight {attention, rest}: wraps the controller set_beta (PID or 0013 schedule); logged beta is the controller's |
| attn-linformer | new-files (module) + patches-anchor 0033 (wiring) | gated-on-anchor-42abed4b (wiring in patches-anchor only) | 2/2 tests/test_linformer.py; anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after) | wired by patches-anchor/0033 into the qat block loop with the builder's own closures ([A20] quantizers apply); projection_layers adds Elin/Flin; export refused (no hgq2 Linformer layer) |
| attn-relu-over-n | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); attn = max(scores,0)/N exactly; no exp/inv quantizers | patches-anchor/0037; arch.attn_kind relu_over_n: ReLU(scores)/N (no 1/sqrt(E), DELTA.md §12), N power of two; needs softmax_quant chang; export refused |
| body-deepsets | new-files (module) + patches 0023 (wiring) | gated-on-tarball; gated-on-anchor-42abed4b | 3/3 tests/test_deepsets.py; SLUG_TEST_PASS body-deepsets (tests_patches/slug_tests.txt); gate M006 GATE_PASS params 20,742 on tarball + 0001-0024 | wired by 0023 (matching_initialization / expected_binary_layers dispatch on arch.body); anchor 0023 also patches newmods/deepsets.py to follow quant.act_overflow (WRAP) and quant.i_decay_speed; anchor test rebase-0023 PASS |
| act-granularity-element | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); widths (T, D) on projections, (T, H, E) on streams | patches-anchor/0029; quant.act_granularity element: every non-batch axis; LUT tables per channel; export refused |
| act-init-f0 | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); f = 7 on every trainable datalane quantizer, i equal to the unkeyed build | patches-anchor/0028; NEW KEY quant.act_f0 (the anchor has none): f := f0 after calibration, incl. [A20] softmax-internal and A.V inputs |
| pre-block-tanh-lut | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0016-pre-block-tanh-lut.patch; arch.pre_block_act tanh_lut; table kbi SAT_SYM b0 7 i0 0 b>=4 (Chang scope, SAT_SYM not WRAP); table EBOPs traced (synthetic); export refused |
| head-dims | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0015-head-dims.patch; arch.head_dims; head_fc1..k+1; export refused (convert_binary has no deep head) |
| binarizer-center-flag | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0002-binarizer-center-flag.patch; quant.binary_center false; binarize.py matches the forward; export refused by the guard until a convert run (DR-17) |
| ste-variants | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0003-ste-variants.patch; quant.ste {bounded, clip_identity, ede}, quant.ste_ede_period (int; "=horizon" resolved by the generator, validator refuses the string); EDE t 0.1->10 per period (IR-Net), set per epoch; gradients checked in closed form |
| bop-optimizer | new-files (module) + patches 0024 (wiring) | gated-on-tarball; gated-on-anchor-42abed4b | 4/4 tests/test_bop.py; SLUG_TEST_PASS bop-optimizer (tests_patches/slug_tests.txt); gate M020 GATE_PASS opt BopAdam, params 12,788 (an optimizer adds no parameters) | wired by 0024 (ablation.delta_optimizer_for); on the anchor, train.optimizer adam_default gives BopAdam Keras Adam defaults on non-binary variables (PLAN_rebase.md decision 1); anchor test rebase-0024 PASS |
| latent-clip | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0004-latent-clip.patch; quant.latent_clip c; clips binary latents after every optimizer step |
| beta-mode | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0005-beta-mode.patch; quant.beta_mode {absmean, absmean_pow2, learned_pow2}; learned log2 scale init from absmean; gets AdamW decay (log2), see log lines; export refused |
| channel-gain-pow2 | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0006-channel-gain-pow2.patch; quant.channel_gain {layers, mode pow2}; gain 1 at init (forward bitwise equal to base); gate: values {-b_c,+b_c} per channel, a fan-in-3 column may hold one sign; DSP audit pending; export refused |
| pre-quant-shift | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); init forward bitwise equal to the unshifted build; gradient reaches the shift | patches-anchor/0032; quant.pre_quant_shift channel: zero-init ChannelShift before each projection input and the Q/K/V streams; unbilled; export refused |
| init-from-checkpoint | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0008-init-from-checkpoint.patch; experiment.init_checkpoint: file path or $BNHGQ2_ARTIFACT_ROOT/<name>/model.keras; input_std.json beside it must match the cache |
| kd-unblock-s-runner | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0009-kd-unblock-s-runner.patch; experiment.distillation admitted on S; teacher resolved like init_checkpoint and run per batch (sees augmented batches); KD value checked vs numpy |
| kd-attention-map | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0010-kd-attention-map.patch; experiment.distillation.attention_coefficient; KL(teacher||student) on the softmax maps; enters the loss only (logged distillation_loss stays logit KD) |
| latent-ema-eval | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0012-latent-ema-eval.patch; experiment.latent_ema_decay; candidate/model_best carry EMA latents; shadow saved in each checkpoint leaf; rebased: shadow saved at the [A15] cadence / pause, [D20] trace and PID see the EMA latents (PLAN_rebase.md); anchor test rebase-0012 (cadence 25, pause/resume) PASS |
| augment-eta-phi-reflect | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0011-augment-eta-phi-reflect.patch; data.augment {reflect_eta, reflect_phi}; raw-space flip in standardized space; signs from (order_seed, epoch); train batches only |
| pt-gate-threshold | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); 0 refused, null / 2.0 accepted | patches-anchor/0025; 0 lines of training code (anchor [A3] arch.pt_gate_gev); validator refuses 0; generator maps Delta 0 -> null |
| gated-key-mask | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); masked keys get exactly 0 attention; forward bitwise equal when no slot is gated | patches-anchor/0036; arch.mask_gated_keys: KeyPadMask (standardized pT != standardized raw zero, cache input_std) into QSoftmax's native mask; builder_for passes input_std; unbilled; export refused |
| std-real-slots | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); mu/sigma equal the hand computation over real slots | patches-anchor/0034; data.std_scope real_slots: prepare_cache stats over raw pT != 0; std_scope in the cache identity (load_cache, verify) |
| derived-input-features | patches | gated-on-anchor-42abed4b (patches-anchor only) | anchor: slug_tests_anchor.py PASS on E (arm A) and A07-350 (build, gate, 1 epoch = 2 steps, post-step gate, reload <= 1e-7 before/after); hand example; reflection-invariant | patches-anchor/0035; arch.derived_features log_pt/delta_r (+ n_feat 5): after the gate, before std, in prepare_cache and load_eval_set; ln pT := 0 on zeroed slots; new cache; export refused |
| weight-scheme-baselines | patches | gated-on-tarball; on the anchor arms blocked: the [A20] guard (act_overflow/softmax_quant need binary weights) refuses it until [A22] lands (not in 42abed4b) | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0007-weight-scheme-baselines.patch; admits quant.weight none/int8_absmax and quant.layer_weight_override; int8_absmax is the bundle static fixed<8,3> grid; labelled baselines, export refused |
| ternary-absmean | patches | gated-on-tarball; on the anchor arms blocked: the [A20] guard (act_overflow/softmax_quant need binary weights) refuses it until [A22] lands (not in 42abed4b) | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0017-ternary-absmean.patch; LABELLED ternary baseline (b1.58 absmean), own gate, billed 2 bits; binary gate refuses ternary layers |
| hgq-learnable-weights | patches | gated-on-tarball; on the anchor arms blocked: the [A20] guard (act_overflow/softmax_quant need binary weights) refuses it until [A22] lands (not in 42abed4b) | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0018-hgq-learnable-weights.patch; quant.weight hgq_learnable: kbi b0 4 i0 0 SAT_SYM, MonoL1, i_decay 1e-3 (Sun et al. transformer values); labelled baseline |
| accumulator-ebops-metric | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0019-accumulator-ebops-metric.patch; NEW KEY experiment.accumulator_metric; per binary layer b_acc = b_act(max) + ceil(log2 fan_in), beside native EBOPs; no total (cards define none) |
| diag-sign-flips | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0020-diag-sign-flips.patch; NEW KEY experiment.diagnostics ["sign_flips"]: per-layer epoch flip fraction and C2I; init signs persisted for resume |
| diag-attention | new-files | gated-on-tarball (module; post-run script, not wired) | 2/2 (tests/test_diags.py), re-run 2026-09-27 against the tarball tree 0001-0025: tests/ 13/13 | standalone; runs on any bundle checkpoint; gated-key mask needs [A3] to supply the valid mask |
| diag-beta-trajectory | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0021-diag-beta-trajectory.patch; experiment.diagnostics ["beta_trajectory"]: per-layer effective beta and |latent|/absmean histogram |
| diag-input-proj-rows | new-files | gated-on-tarball | 1/1 (tests/test_diags.py) | standalone; runs on any bundle checkpoint |
| diag-latent-binary-gap | new-files | gated-on-tarball | 1/1 (tests/test_diags.py) | standalone; eager calls only |
| screen-collapse-stop | patches | gated-on-tarball; gated-on-anchor-42abed4b | tarball: a+c PASS, E-shape PASS, invariance 7/7; anchor: same slug test PASS, anchor invariance 19/19 on 42abed4b | patches/0014-screen-collapse-stop.patch; NEW KEY experiment.collapse_stop {threshold, patience, after_epoch}; writes COLLAPSED.json, status verified_collapsed; run_pack untouched ([A12]); rebased into 0025 verify_selected and the collapse epoch forces an [A15] checkpoint; anchor test rebase-0014 PASS |
| generate_delta + trace_floors_delta + classify_series + annotate_index + gate_cpu + manifest_wave2 + canary_k (not a slug) | new-files | gated-on-anchor-42abed4b (configs); launch packs PLANNING until the memory canary | anchor tree 42abed4b + patches-anchor/0001-0038 (2026-09-28): 582 configs, validator 582/582 (ready_on_base 140, runnable_on_series 442), train.ebops_trace_every 10 carried on 582/582, diff_outside_declared 0; gate one per (entry, base arm) 142 pairs: 119 PASS (max_abs 0), 15 NEEDS_TEACHER, 8 FAIL ([A20] non-binary guard: M047, M048, M049, P-T1, P-T2; STUDY gate 13); re-gated 2026-09-28 with the tree's patched newmods (sys.path fix): M006 20,750 params; floors 74/81 traced (M006 zero 0 via builder_for + set_floor, self-check on A and A07-350 via both paths); gen -> classify -> annotate byte-identical (GATES.md §7) | base = the anchor's per-seed arm configs from 42abed4b (anchor_arms.json; --anchor-bundle/--anchor-sha); wave2_amendments.json = the frozen wave-2 STUDY 24c3c90 lists; per-pack BNJ_RSS_GATE_LIMIT_MB = 2,100 + 5 x H MiB (STUDY PACK-MEM), pod memory max(6, ceil(limit/1024)) Gi per arm; replica seeds 5-8 at train.epochs 500 (frozen STUDY); packs: t0 8 pods / 20 arms (one horizon and one family per pack), cells 87 pods / 228 arms incl. M006 (parallelism 7 + 3 live t0 = 10); K E 4 (estimate) A07 3 (planning); canary manifests/delta-canary-job.json (one A10 pod: E K=4 rep-A s1-4, E K=5 P-350 s1-4 + rep-A s5, A07 K=3 rep-C s1-3, one horizon per phase, 110 epochs each, projected 8.35-10.43 GPU-hours) |
| run-pack-names-roots (launch gap, not a delta.json slug) | new-files (patch at the end of both series) | gated-on-tarball; gated-on-anchor-77f1ca4e | tarball patches/0025: tests/test_run_pack_delta.py 6/6, invariance 7/7 SAME (INVARIANCE_GATE_PASS); anchor patches-anchor/0038: test_run_pack_delta.py 6/6 + the anchor's test_run_pack.py 2/2; 0038 touches run_pack.py and its test only | run_pack.py: pack entries may be run names; dict-form packs file with run_root / data_root (pack_meta wins) exported as BNJ_RUN_ROOT / BNJ_DATA_ROOT; conflicting env, unknown name, missing run_root refused (exit 2) before any arm starts; tarball 0025 also ports the anchor's BNJ_* roots into run_study.py; legacy list-of-rows unchanged |

## Patch series (patches owner)

**Update 2026-09-28 (rebase 2; `PLAN_rebase.md` "Rebase 2").** `patches-anchor/0001-0038` now
target the regime-B leak-fixed freeze **42abed4b** (ConfigMap `kai-chang0926-code-42abed4b5d`,
commit 3dabcd2); `apply_anchor.sh` pins that sha (77f1ca4e, e90327d4, f2107a04, ceb174db are
superseded; the 77f1ca4e series is not kept in the repo). Conflicts: 0012 (EMA swap vs regime-B
traced/untraced epochs), 0019 (log block), 0038 (run_pack header/constants, new-files owner's
patch, rebased and tested); 0022 gains `train.ebops_trace_every`. Gates on 42abed4b: anchor
invariance 19/19 SAME (9 arms seed 1, 7 const0922, 12-epoch run_training on A, A07-350, C′
crossing untraced epochs); `validate_cfg` 96/96; `slug_tests_anchor.py` 17/17; tarball slug
tests on the anchor tree 24/24; the anchor's pytest (incl. run_pack, leak fix, trace-every,
0038) 99 passed, 2 skipped; RSS/object-count check `tests_patches/rss_slope_anchor_42abed4b.txt`.
`patches/` (tarball series) is unchanged by this rebase. Rows below that say
gated-on-anchor-42abed4b were re-tested on it.

**Update 2026-09-27 (rename, anchor rebase, unblock; `PLAN_rebase.md`).**
- **Rename.** Every Delta identifier in `patches/`, `newmods/` and `tests_patches/slug_tests.py`
  is renamed atlas -> Delta (`bnhgq2/delta_keys.py`, `delta_study`, `delta_optimizer_for`,
  `_delta_binarize`, `delta_binary_options`, `init_delta_scales`, `set_delta_epoch`,
  `DeltaDiagnostics`, keras package `bnhgq2_delta`); `0001-delta-keys-registry.patch`. Same
  numbering, one slug per patch. The rebuilt tree equals the old tree with the same text map
  applied; `grep -ri atlas` on it is empty. Invariance 7/7 (`tests_patches/invariance_gate.txt`),
  slug tests 24/24 (`slug_tests.txt`, `slug_results.json`). `patches/` still applies to the
  screen tarball (= public `code/constituent-study-20260922`), sha-checked by `apply.sh`.
- **Anchor series.** `patches-anchor/0001-0024` = the same 24 patches rebased onto the anchor
  pilot bundle 77f1ca4e (conflicts in 0012, 0013, 0014, 0019, 0024 resolved; anchor keys in the
  strict allow-list; Deep Sets under WRAP; Bop under `adam_default`); `0025-0037` = the twelve
  formerly blocked slugs plus the attn-linformer wiring. `apply_anchor.sh <dir>` checks the
  bundle sha and applies them. Invariance with every Delta key absent: 19/19 SAME (9 anchor arms
  at seed 1, 7 const0922 configs, 2-epoch run_training on A, A07-350, C′) after 0024 and after
  0037 (`tests_patches/invariance_gate_anchor.txt`). On the anchor tree: the 24 tarball slug
  tests PASS (`slug_tests_on_anchor.txt`) and `slug_tests_anchor.py` (13 slugs + 4 rebase
  decisions) PASS (`slug_tests_anchor.txt`).
- **Forward pointer (new-files owner, blocking any pack):** the generator and its outputs
  (`gen_atlas.py`, `configs/`, `index.json`, `key_registry.json`, `classify_series.py`,
  `annotate_index.py`, `manifest_wave2.py`, `gate_cpu.py`, `tests/conftest.py`) still use the
  old names; the strict validator refuses `atlas_study` by name, and `gate_cpu.py`'s
  `getattr(ablation, 'atlas_optimizer_for', ...)` would silently test Adam instead of Bop.
  `slug_tests.delta_cfg` maps the old block to `delta_study` for its three generated-config tests
  and asserts that the raw file is refused. Regenerate on the anchor arm-A base.


**Update 2026-09-27 (review A1-v3).** `patches/0022-strict-keys` makes `run_engram.validate_cfg`
refuse, naming the key, any config key no code path in the applied tree reads (bundle-read keys,
provenance keys, inert bundle keys pinned to their bundle values, and registered keys are
accepted; unwired-module and blocked-slug keys are refused with the slug named). On the
0001-0022 tree M004, M006 and M020 are refused (`tests_patches/strict_keys_at_0022.txt`); an
invented key is refused on every tree; all 38 const0922 configs and the 12 confirmation configs
pass. `0023-body-deepsets` and `0024-bop-optimizer` wire the new-files engineer's
`newmods/deepsets.py` and `newmods/bop.py` (copied into the build by `apply.sh`, added to the
source manifest); M004 (Linformer) stays refused, blocked on [A20]. Tests on the full tree: 24/24
(`slug_tests.txt`, incl. strict-keys, body-deepsets, bop-optimizer), invariance gate 7/7. The
body-deepsets and bop-optimizer rows above belong to the new-files engineer and were not edited:
with 0023/0024 applied both modules are wired (build, one step, reload, binary gate tested).

`apply.sh <build-dir>` re-extracts the screen tarball (sha256 checked), commits it in a throwaway
repo and applies `patches/0001-0024` with `git apply --3way` (after copying `newmods/`); 0001 is the key registry
(`bnhgq2/delta_keys.py`, one validator hunk and one export guard), not a slug. Tests in
`tests_patches/` (run with `tests_patches/pyenv.sh`, 1 thread, deterministic ops): the invariance
gate (`gate_invariance.py` + `compare_fp.py`, result `invariance_gate.txt`), per-slug tests
(`slug_tests.py`, results `slug_results.json`, `slug_tests.txt`). Formerly blocked slugs: `BLOCKED.md` (all built in `patches-anchor/`).
New key names this series sets (no Delta entry names them): `experiment.collapse_stop`,
`experiment.accumulator_metric`, `experiment.diagnostics`. Synthetic CPU checks only; nothing is a result.
