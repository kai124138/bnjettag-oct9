# BLOCKED.md — Delta slugs that needed anchor code

ml-engineer (patches). Written 2026-09-27 as design notes for twelve slugs blocked on the anchor
series ([A1] schedule, [A3]/[A4] pT gate and split cache, [A20] Chang quantizer set) and the
attn-linformer wiring; **updated 2026-09-27 (rebase onto the anchor pilot bundle 77f1ca4e,
ConfigMap `kai-chang0926-code-77f1ca4e9f`)**: all thirteen are now written, one patch each, as
`patches-anchor/0025-0037`. They exist only in `patches-anchor/` (they use anchor code) and are
not in the tarball series `patches/` that goes to the public repo. Procedure, conflicts and
decisions: `PLAN_rebase.md`. Tests: `tests_patches/slug_tests_anchor.py` (results in
`README.md`). The design notes of the first version (line numbers of the staged 72a1290 tree)
are in git history of this file; the table below is what was built.

**Update 2026-09-28:** `patches-anchor/` is rebased onto the regime-B freeze 42abed4b
(ConfigMap `kai-chang0926-code-42abed4b5d`); 0025-0037 re-tested there (slug_tests_anchor 17/17).
Still blocked on the anchor arms: weight-scheme-baselines, ternary-absmean, hgq-learnable-weights
(labelled non-binary baselines M047-M049, teachers P-T1/P-T2) — the anchor's [A20] guard
refuses `act_overflow`/`softmax_quant` without binary weights, and [A22] (non-binary under the
Chang quantizers) is not in 42abed4b. They stay gated on the tarball only.

**Nothing is blocked on anchor code any more.** What still stands between a slug and a claim:
- HLS export: every slug marked "export refused" below is refused by `convert_binary.py`
  through `delta_keys.export_blockers` (DELTA DR-17). No synthesis or DSP claim for them.
- The generator and its configs (new-files owner) still carry the pre-rename names
  (`atlas_study` block, `atlas0926-` run names, `gen_atlas.py`, `gate_cpu.py`'s
  `getattr(ablation, 'atlas_optimizer_for', ...)`, which would silently fall back to Adam). The
  strict validator refuses the old block by name. They must be regenerated on the anchor base
  (arm A config) before any Delta pack is built.
- `run_pack.py` packs format and the hard-coded output root (WIRING.md) are unchanged.

| patch | slug | key(s) | anchor code it uses | mechanism as built | hazard / scope | export |
| --- | --- | --- | --- | --- | --- | --- |
| 0025 | pt-gate-threshold | `arch.pt_gate_gev` (anchor [A3]) | data.apply_pt_gate, prepare_cache, load_cache | no training code; validator refuses 0 (Delta "0 = ungated" is null; the generator maps 0 -> null) | a gate value is a new cache per value; `delta_keys.active_slugs` lists pt-gate-threshold for every config carrying the key (anchor 2.0 included), so do not label cells from it for this key | ok |
| 0026 | softmax-table-min-bits | `quant.softmax_table_min_bits` (int 1-12) | [A20] `_chang_table` bc=Min(4) | Min(4) -> Min(k) on the learned exp/inv tables | needs `softmax_quant: chang` | refused |
| 0027 | lr-schedule-variants | `train.lr_warmup_epochs` (m_mul/t_mul = anchor [A1] keys) | [A1] `chang_cosine_restarts` (no warm-up) | lr * (epoch+1)/w for epochs < w, first cycle only | needs `lr_schedule: chang_cosine_restarts`, w < cycle | ok |
| 0028 | act-init-f0 | `quant.act_f0` (new; the anchor has none) | calibration in matching_initialization | f := f0 on every trainable datalane KIF quantizer (incl. [A20] softmax-internal and A.V input), i as calibrated / data-tracked | Deep Sets refused | ok |
| 0029 | act-granularity-element | `quant.act_granularity: element` | [A20] `act_iq` / `_free_act` | heterogeneous over every non-batch axis on projections and streams; A.V input as channel (already per element); LUT tables as channel | static_floor.py (floor tool) does not model element grids | refused |
| 0030 | ebops-group-weight | `quant.ebops_group_weight {attention, rest}` | BetaPID / 0013 schedule `set_beta` | per-layer `_beta` = controller beta x w[group]; group attention = `bit_block_<i>_attn_*` incl. softmax tables | logged `beta` is the controller's, not per layer | ok |
| 0031 | qk-stream-min-bits | `quant.qk_min_bits` | [A20] WRAP stream quantizers | f := max(f, k - i) on both attn_scores inputs at init and after every optimizer step | under WRAP i is data-tracked, so the floor is a post-step projection on the i of that moment; V and A.V untouched | ok |
| 0032 | pre-quant-shift | `quant.pre_quant_shift: channel` | `dense_einsum`, `dense`, Q/K/V streams | zero-init `ChannelShift` before each input quantizer | not billed in EBOPs; refused with `arch.attn_kind` | refused |
| 0033 | attn-linformer | `arch.attn_kind: linformer`, `arch.linformer_k` | block loop closures ([A20] quantizers apply) | newmods/linformer.py wired; `projection_layers` adds Elin/Flin | refused with pair_bias, attention-map KD | refused |
| 0034 | std-real-slots | `data.std_scope: real_slots` | prepare_cache, load_cache, cache verify | train-split mu/sigma over slots with raw pT != 0 | new cache (std_scope in its identity) | ok |
| 0035 | derived-input-features | `arch.derived_features`, `arch.n_feat` | prepare_cache (after the gate, before std), load_eval_set, validate_cfg | append ln(pT) (0 on zeroed slots) and sqrt(eta^2+phi^2) | new cache; ROC-test evaluators must pass `derived_features` to `load_eval_set` (the anchor's evaluate_roc.py does not) | refused |
| 0036 | gated-key-mask | `arch.mask_gated_keys: true` | QSoftmax native mask; builder_for input_std | `KeyPadMask`: valid iff standardized pT != standardized raw-zero value (train-split stats, same float32 ops as the cache); masked keys get exp = 0 | all-masked jet -> zero attention; mask unbilled; refused with attn_kind | refused |
| 0037 | attn-relu-over-n | `arch.attn_kind: relu_over_n` | [A20] learned WRAP A.V input | ReLU(scores)/N (no 1/sqrt(E), as DELTA.md §12), no exp/inv tables | needs `softmax_quant: chang` and N a power of two; [A26] entropy script and attention-map KD do not apply | refused |
