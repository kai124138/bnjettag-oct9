# PLAN_rebase.md — ml-engineer (patches), 2026-09-27

Owner protocol step 1: plan first. Crash notes at the bottom, updated as each step lands.
Brief: orchestrator, 2026-09-27 (rename atlas → Delta in the series; rebase onto the anchor
bundle 77f1ca4e; unblock the 12 blocked slugs + wire attn-linformer). No commits to project
repos, no launch, CPU builds and a few steps only. `campaigns/2026-09-26-training-batch/` is
read-only.

## Trees

| name | what | sha |
| --- | --- | --- |
| tarball | `campaigns/2026-09-22-constituent-screen/study-code.tar.gz` (= public `code/constituent-study-20260922`) | 26f3cc40…5a45 |
| anchor | `campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz`, ConfigMap `kai-chang0926-code-77f1ca4e9f` (= `code/tree` + `code/analysis`, checked by `diff -r`) | 77f1ca4e…2a94, manifest f7d4003f… |

## Job 1 — rename in the tarball series

The pristine tarball has no `atlas` string (grep, 2026-09-27), so every `atlas` in
`patches/*.patch` and `newmods/*.py` is Delta content. Method: a fixed, ordered text map
applied to the patch files and newmods (script in scratch, `rename.py`), then re-apply on a fresh
extraction, commit per patch, `git format-patch` again (hunk headers regenerated).

Map (identifiers first, then prose): `atlas_keys` → `delta_keys` (module, file path, imports);
`atlas_study` → `delta_study`; `atlas_optimizer_for` → `delta_optimizer_for`; `_atlas_binarize`
→ `_delta_binarize`; `atlas_binary_options` → `delta_binary_options`; `init_atlas_scales`,
`set_atlas_epoch`, `_atlas_build`, `atlas_cfg`, `AtlasDiagnostics`, `atlas_diagnostics`,
`atlas_ede_t`, `_atlas` → `delta` forms; keras package `bnhgq2_atlas` → `bnhgq2_delta`;
`atlas.json` → `delta.json`; `ATLAS` (doc) → `DELTA.md`; "method atlas"/"method-atlas"/"atlas"
(prose) → "Delta". `0001-atlas-keys-registry.patch` → `0001-delta-keys-registry.patch`.

Pass: `apply.sh` (tarball sha checked) APPLY_ALL_PASS; `grep -ri atlas <build>/code` empty;
invariance gate 7/7 (pyenv.sh: 1 thread, TF_DETERMINISTIC_OPS=1, PYTHONHASHSEED=0); all slug tests.

Not mine (new-files owner), listed as a blocking forward pointer: `gen_atlas.py`,
`gate_cpu.py` (its `getattr(ablation, 'atlas_optimizer_for', …)` silently falls back to Adam
after the rename), `classify_series.py`, `annotate_index.py`, `manifest_wave2.py`,
`tests/conftest.py`, `key_registry.json`, `configs/`. The strict validator refuses the old
`atlas_study` block by design; no dual acceptance.

## Job 2 — rebase onto the anchor bundle

Base = extracted bundle (not `code/tree`), `git init`, renamed newmods copied, then
`git apply --3way` of the renamed series; resolve 0012/0013/0014/0020 by hand; export to
`patches-anchor/` with `apply_anchor.sh` (bundle sha 77f1ca4e checked).

Flagged decisions (each recorded below with the outcome):
1. 0024 Bop vs [A2] `train.optimizer`: BopAdam's non-binary Adam follows the anchor's
   `optimizer_for` hyperparameters for the configured `train.optimizer` (adam_ours or
   adam_default), or the pair is refused. Decision recorded after reading anchor l.170-195.
2. 0023 Deep Sets under [A20]: activation quantizers from the anchor's `act_iq` factory with
   `overflow = quant.act_overflow` (the brief: "under [A20] WRAP quantizers").
3. 0012 latent EMA vs [A15] cadence / [A6] snapshots: shadow saved in every checkpoint leaf the
   anchor writes and restored by `restore_checkpoint`; tested save → restore.
4. 0014 collapse stop vs [A12] DIVERGED/exit 3 and 0025 `verify_selected`: COLLAPSED.json,
   exit 0; checked that the post-run verification tolerates a collapsed run.
5. 0022 strict keys: every key the 58 anchor configs carry is accepted; each added key is
   grepped as read by the anchor code (or pinned inert).

Anchor invariance: new `gate_invariance_anchor.py` mirroring the anchor `cpu_gate.py` build
call; configs = the anchor's generated arm configs (`campaigns/chang0926/configs/*.json`, 58) and
the 7 const0922 configs; pristine anchor extract vs anchor + series; fields as the tarball gate
(config digest, init kernel hashes, model JSON, EBOPs, predictions, one optimizer epoch).
Synthetic n ≥ 2·batch (batch 2790) so the epoch has ≥ 2 optimizer steps; configs unmodified.
Coverage decided after timing one arm (all 58 if affordable, else one seed per arm).

## Job 3 — unblock 12 slugs + wire linformer (anchor series only, 0025+)

Order smallest first. Before code: (a) does the anchor's `lr_alpha`/`lr_alpha_epochs` already
implement a warm-up? (b) does the anchor cache carry the gate mask, or only standardized x?
Each slug: opt-in key registered in `delta_keys` (moved out of the refused set), unit test,
post-step binary gate where weights are touched, build + one step + reload ≤ 1e-7 on the arm A
(E) and A07-350 configs. Hazards stated in the ledger: qk-min-bits under WRAP acts on f only
(i data-tracked); ebops-group-weight must act through both PID and the 0013 schedule controller.

## Next rebase (anchor production sha)

Written in README / at the end of this file once Job 2 is done.

## Crash notes

- 2026-09-27: plan written; anchor bundle extracted to scratch `rb/anchor0` (diff -r = code/tree
  + analysis/).
- 2026-09-27: Job 1 done. Rename = ordered text map (scratch `rb/rename.py`) over patches,
  newmods, slug_tests; `git am` on a fresh tarball extraction, `git format-patch` again;
  0001 renamed `0001-delta-keys-registry.patch`. The renamed tree equals the old `apply.sh`
  tree with the same map applied (`diff -r` empty); `grep -ri atlas` on the tree: 0 files.
  Invariance 7/7 SAME vs the stored pristine fingerprint and vs a pristine fingerprint
  regenerated today (which itself equals the stored one). Slug tests: 21/24 on the first run;
  strict-keys, body-deepsets, bop-optimizer failed because the generated configs (new-files
  owner) still carry `atlas_study`, refused by name. `slug_tests.delta_cfg` now moves that
  provenance block to `delta_study` and strict-keys asserts the raw file is refused; 3/3 PASS.
- 2026-09-27: Job 2 rebase done by cherry-pick onto a commit holding the anchor bundle on top of
  the pristine tarball commit (shared history, real 3-way merges). Conflicts: 0012, 0013, 0014,
  0019, 0024 (0020 applied cleanly here); resolutions and decisions in "Rebase record" below.
  Strict allow-list and Deep Sets overflow squashed into 0022 / 0023. Exported to
  `patches-anchor/0001-0024`; `apply_anchor.sh` (sha 77f1ca4e checked) reproduces the dev tree.
- 2026-09-27: Job 3 code done: 0025-0037 on the anchor branch (one slug each, smallest first),
  exported to `patches-anchor/`; `apply_anchor.sh` reproduces the dev tree. Tests in
  `tests_patches/slug_tests_anchor.py`; anchor invariance in `tests_patches/gate_invariance_anchor.py`.

## Rebase record (0001-0024 onto 77f1ca4e)

Method: scratch repo = tarball commit -> anchor bundle commit (so 3-way merges have the tarball
blobs) -> newmods commit -> `git cherry-pick` of the 24 renamed commits. Clean: 0001-0011,
0015-0018, 0020-0023. Conflicts, all context conflicts in regions both series edit:

| patch | anchor region | resolution |
| --- | --- | --- |
| 0012 latent-ema-eval | `save_checkpoint` (anchor `SELECTED_FILES` loop); epoch loop ([D20] in-training EBOPs read + `traced_ebops`); [A15] cadence block | EMA arrays written in every leaf the anchor commits (cadence, pause, last epoch); `swap_in` after the [D20] in-training read and before the trace, so the trace, the PID ([D20] assert), the stored-EBOPs reload check, feasibility, candidate and selection all see the EMA latents (as on the tarball); `swap_out` unchanged |
| 0013 beta-schedule-s-runner | anchor `chang_cosine_restarts` inserted at the same place | both functions kept |
| 0014 screen-collapse-stop | `run_study.train` moved its verification into 0025's `verify_selected` | status `verified_collapsed` and `VERIFIED_COMPLETE.json` on collapse now set inside `verify_selected`; **plus** the [A15] cadence condition gains `or state.get('collapsed')`, so the collapse epoch is committed (otherwise a re-invocation would resume from an older leaf with no collapse record and train on) |
| 0019 accumulator-ebops-metric | [ND] and [D20] log blocks | both kept, anchor's first |
| 0024 bop-optimizer | `initial = traced_ebops(model)` ([D20]) | anchor line kept with `delta_optimizer_for` |

Flagged decisions (each can move a number on the cells that set the key; none acts when the
key is absent, which the invariance gate checks):

1. **Bop with [A2] `train.optimizer`.** Every anchor arm config says `adam_default` and carries
   no `beta2` / `weight_decay` / `clipvalue`, so the tarball `bop_optimizer_for` (reads them)
   would KeyError. `delta_optimizer_for` now builds `BopAdam(learning_rate=lr)` with Keras Adam
   defaults on the non-binary variables for `adam_default` (asserted beta_2 0.999, eps 1e-7, no
   decay, no clip, as `optimizer_for`), and the tarball path for `adam_ours`. Bop's own rule on
   the binary latents is unchanged. Test `rebase-0024-bop-adam-default` (incl. pause/resume).
2. **Deep Sets under [A20].** `newmods/deepsets.py` is patched in the anchor series (0023) to
   pass `overflow = quant.act_overflow` to `qat._free_act` (WRAP: i data-tracked, 0 bits
   reachable) and to apply `quant.i_decay_speed` via `qat.set_i_decay_speed`, as the
   transformer builder does. `quant.softmax_quant` has no effect on this body (no attention).
   The tarball copy of `deepsets.py` is unchanged (it has no `overflow` argument to pass).
   Test `rebase-0023-deepsets-wrap`.
3. **Latent EMA under [A15]/[D20].** See the table. Hazard kept from the tarball log line: under
   WRAP the trace re-tracks i on the EMA weights before `swap_out`; training then continues
   from those i values (re-tracked by the next training forward). Test
   `rebase-0012-latent-ema-cadence` (25-epoch cadence, pause at epoch 1, resume to 3).
4. **Collapse stop under [A15]/0025.** See the table; exit stays 0 (not [A12] DIVERGED / exit 3);
   `VERIFIED_COMPLETE.json` makes `run_pack` skip the arm. Test `rebase-0014-collapse-cadence`.
5. **Strict allow-list (0022).** Every key the 58 anchor configs carry passes: 20 anchor keys
   moved to `READ_KEYS` (each grepped as read by the anchor runner: [A1] lr_*, [A2] optimizer,
   [A3] pt_gate_gev, [A6] snapshot_every_epochs, [A13] cost_before_auc, [A15]
   checkpoint_every_epochs (was pinned inert at 1), [A17] pos_enc_none_consume_rng, [A19]
   keep_auc_selected_feasible, [A20] act_overflow / softmax_quant, [D20] ebops_trace_sample /
   ebops_trace_batch / ebops_reload_check, [D25] i_decay_speed, arbiter-v3 nondegenerate.*);
   the generator's `campaign` block is provenance. `cache_configs/*.json` are not run configs
   (prepare_cache never calls validate_cfg) and are not checked. Final tree (0001-0037):
   `run_engram.validate_cfg` accepts 96/96 (58 anchor arm configs, all seeds, + 38 const0922).
6. **newmods rename.** `newmods/*.py` (new-files owner) got the same text map (prose, and the
   keras package `bnhgq2_atlas` -> `bnhgq2_delta` in bop.py); `pytest tests/` (13 tests) passes
   against the renamed tarball tree. Coupling: anchor 0023 patches `newmods/deepsets.py` after
   `apply_anchor.sh` copies it, so an edit to `deepsets.py` by its owner can stop anchor-0023
   from applying; re-export 0023 when that happens.

Semantics chosen in 0025-0037 that change what a number means (for decisions.md): see "Log
lines to append" at the end of this file.

## Anchor invariance (what it covers)

`gate_invariance_anchor.py`, pristine anchor extract vs `apply_anchor.sh` tree, 1 CPU thread,
`TF_DETERMINISTIC_OPS=1`, `PYTHONHASHSEED=0` (pyenv.sh): the 9 anchor arms at seed 1 (A, A07-350,
B, C, C′, D, E1, F, R; unmodified generated configs; one epoch of 3 optimizer steps at the
config's own batch on n = max(512, 2·batch + 20) synthetic jets, i.e. 5,600 at batch 2,790), the 7 const0922 screen configs, and a 2-epoch `run_training` for A,
A07-350 and C′ (epochs 2, batch 128, val_batch 256 on both sides, the anchor's own
regress_train.py procedure; records minus wall-clock fields, selected checkpoints, files).
Seeds 2-8 were not run (about 40 s per A07 config per side on this laptop); the seed changes
only the RNG stream, not the code path.

## Next rebase (anchor production sha)

The peer says only the W&B run-id derivation changes (wandb_util / run_study / run_engram
remote path). No Delta patch edits `wandb_util.py` (0014 has it as one context line, the
`log_files_artifact` import at the end of `run_training`).

**Seen 2026-09-27 (read only, not rebased onto):** the training-batch working tree
`code/tree/` is dirty with more than a run-id change: `bnhgq2/ablation.py` +82/-13 adds
`train.ebops_trace_every` ([D20] "regime B": full-split trace only every k epochs,
`is_traced_epoch`), plus `wandb_util.py` and `run_study.py` edits. If that lands in the
production bundle, expect conflicts in the epoch-loop hunks of 0012 (EMA swap around the trace),
0014 (cadence) and 0019/0020 (log blocks), and two decisions: whether the EMA swap and the
candidate save happen on untraced epochs, and `train.ebops_trace_every` into the strict
allow-list (0022). Re-read the new bundle's diff before assuming a clean apply. Procedure:
1. Record the new bundle sha256 and manifest sha from the training-batch PREFLIGHT.md (read only).
2. `ANCHOR_BUNDLE=<new tar.gz> ANCHOR_SHA256=<sha> code/apply_anchor.sh <scratch>`; on a clean
   apply, update the two defaults in `apply_anchor.sh` and go to step 4.
3. On a failed apply: in a scratch repo commit tarball -> new bundle -> newmods, cherry-pick the
   37 commits (`git am` of `patches-anchor/` onto the old bundle gives them), resolve, re-export
   with the same numbering (`NNNN-<slug>.patch`); record each conflict in this file.
4. Gates, all must pass: `gate_invariance_anchor.py` pristine-new vs patched-new with the same
   arguments as above (`compare_fp.py` -> INVARIANCE_GATE_PASS); `slug_tests.py` and
   `slug_tests_anchor.py` on the patched-new tree (SLUG_TESTS_ALL_PASS,
   ANCHOR_SLUG_TESTS_ALL_PASS); the strict validator over every generated arm config of the new
   bundle (new keys go to READ_KEYS only after a grep shows the runner reads them).
5. Update README.md status to `gated-on-anchor-<sha8>` and the log lines.

## Log lines to append

For `.claude/memory/decisions.md` (newest on top; the orchestrator appends once):

- 2026-09-27 (ml-engineer, staged, not shipped) — Delta patch series renamed atlas -> Delta
  (`delta_keys`, `delta_study`, `delta_optimizer_for`, `_delta_binarize`,
  `delta_binary_options`, `init_delta_scales`, `set_delta_epoch`, `DeltaDiagnostics`, keras
  package `bnhgq2_delta`; `0001-delta-keys-registry.patch`). Pure text map; the tarball tree
  equals the old tree with the map applied, invariance 7/7, slug tests 24/24. The strict
  validator refuses the old `atlas_study` block by name, so every generated config must be
  regenerated by the renamed generator (new-files owner). **Check:** `code/apply.sh <dir>`;
  `grep -ri atlas <dir>/code` empty; `tests_patches/invariance_gate.txt`.
- 2026-09-27 (ml-engineer, staged, not shipped) — Delta series rebased onto the anchor pilot
  bundle 77f1ca4e (`code/patches-anchor/0001-0024`, `code/apply_anchor.sh` checks the sha).
  Choices that change what a number means on the cells that set the key: Bop with
  `train.optimizer adam_default` gives the non-binary variables Keras Adam defaults (no decay, no
  clip); latent-EMA shadows are saved at the [A15] cadence and the [D20] trace, PID and
  stored-EBOPs check see the EMA latents; a collapse forces a checkpoint at the collapse epoch
  and reports `verified_collapsed` through 0025 `verify_selected`; Deep Sets activations follow
  `quant.act_overflow` (WRAP) and `quant.i_decay_speed`. With no Delta key the anchor
  reproduces itself bitwise. **Check:** `PLAN_rebase.md` "Rebase record";
  `tests_patches/gate_invariance_anchor.py` + `compare_fp.py`.
- 2026-09-27 (ml-engineer, staged, not shipped) — twelve Delta slugs unblocked and attn-linformer
  wired on the anchor tree only (`patches-anchor/0025-0037`). Semantics fixed here:
  `train.lr_warmup_epochs` is linear over epochs 0..w-1 of the first cosine cycle only;
  `quant.act_f0` sets f on every trainable datalane quantizer incl. the [A20] softmax-internal
  and A.V inputs; `act_granularity element` = every non-batch axis on projections and Q/K/V
  streams, LUT tables stay per channel; `ebops_group_weight` group "attention" =
  `bit_block_<i>_attn_*` incl. the softmax tables, logged beta stays the controller's;
  `qk_min_bits` is a post-step projection f >= k - i (i data-tracked under WRAP), Q/K only;
  `pre_quant_shift` shifts are unbilled float adds; `std_scope real_slots` and
  `derived_features` are cache identities; ln pT := 0 on zeroed slots; the key mask is
  "standardized pT != standardized raw zero" from the cache's train-split stats; relu_over_n is
  ReLU(scores)/N without 1/sqrt(E) (DELTA.md §12) and needs the Chang A.V quantizer; a gate
  value of 0 is refused (ungated is null). **Check:** `tests_patches/slug_tests_anchor.py`;
  `BLOCKED.md` table.
- 2026-09-27 (finding) — the anchor's `campaigns/chang0926/evaluate_roc.py` calls
  `load_eval_set` without `derived_features`; a Delta ROC-test evaluator for M040-family cells
  must pass it, or the 5-feature models get 3-feature inputs. **Check:** `grep -n derived_features
  <evaluator>`.

# Rebase 2 — onto the regime-B leak-fixed freeze 42abed4b (2026-09-28)

Brief (coordinator, 2026-09-28): bundle sha256 42abed4b5d2e…c258c0, manifest 041f981a…bd42,
ConfigMap `kai-chang0926-code-42abed4b5d`, commit 3dabcd2 (training-batch anchor patches
0027-0031; read only). Superseded: e90327d4, f2107a04, ceb174db, 77f1ca4e. No commits, no launch.

Plan:
1. Diff 77f1ca4e -> 42abed4b (done, read only): ablation.py (regime B `train.ebops_trace_every`,
   epoch 0 traced; `ValidationReloader` load_weights leak fix; RSS gate from env, exit 5),
   run_pack.py (heartbeat per attempt, POD_STALL, POD_MEM, exit 5 not retried; pack format
   unchanged: list of row lists, `packs_meta.json` is documentation read by no code),
   run_study.py (verify_selected skips when no traced epoch yet), wandb_util, tests, configs
   (+ `train.ebops_trace_every: 10` on every arm).
2. Scratch repo: tarball -> 77f1ca4e -> newmods -> `git am patches-anchor/0001-0038` (the
   current files, incl. new-files 0038) ; branch tarball -> 42abed4b -> newmods -> cherry-pick.
3. Expected conflicts / decisions: 0012 (EMA swap vs traced / untraced epochs and the reloaded
   validation model), 0014 (cadence), 0019/0020 (log blocks), 0022 (`train.ebops_trace_every`
   into READ_KEYS), 0038 (run_pack `launch`/`main` rewritten by the anchor).
4. Gates: anchor invariance pristine-42abed4b vs patched (same coverage as before; configs now
   regime B); `slug_tests.py` + `slug_tests_anchor.py` on the new tree; 0038's tests + the
   anchor's run_pack tests; new CPU RSS-slope check (>= 30 epochs, `ablation.host_rss_mb`) on E
   and A07-350 baseline vs Delta always-on keys, and on E with latent-EMA, KD (stub teacher),
   diag-sign-flips; report MB/epoch; check no Delta patch catches exit 5 / bypasses the gate.
5. [A22] not in this freeze: weight-scheme-baselines / ternary / hgq-learnable stay refused on
   the anchor arms by the [A20] guard.

## Rebase 2 record (0001-0038 onto 42abed4b, 2026-09-28)

Method as rebase 1: scratch repo tarball -> 77f1ca4e -> newmods -> `git am` of the then-current
`patches-anchor/0001-0038` (branch old); tarball -> 42abed4b -> newmods -> cherry-pick. Clean:
everything except the three below. `apply_anchor.sh` now pins 42abed4b; its rebuild equals the
dev tree (`diff -r` empty).

| patch | anchor change | resolution |
| --- | --- | --- |
| 0012 latent-ema-eval | regime B `traced = is_traced_epoch(...)` at the trace site; `ValidationReloader` | both kept: `traced` decided, then `swap_in`, then the trace only if traced; candidate save, reload (now `load_weights` into the one validation model) and validation on EMA latents every epoch; `swap_out` after validation. On an untraced epoch the logged in-training EBOPs are the live-weight value of the last training step (the stored `layer.ebops`, which `swap_in` does not change) while the candidate carries EMA kernels; untraced epochs are never selected, so no selection uses that pair |
| 0019 accumulator-ebops-metric | regime-B log nulling block | both kept (anchor's first); accumulator bits are logged every epoch (a closed form of widths, not a trace) |
| 0038 run-pack-names-roots (new-files) | run_pack header, POD_* constants, `EXIT_MEMORY_GATE = 5`, launch() entry dict | both kept; `EXIT_BAD_PACK = 2` beside `EXIT_MEMORY_GATE = 5`; `launch` keeps the anchor's `started_wall` / `pod_stalls` / `rss_mib` and 0038's `env={**os.environ, **CHILD_ENV}` (so `BNJ_RSS_GATE_LIMIT_MB` reaches every child). Pack format check: the anchor's `main` still reads `packs[JOB_COMPLETION_INDEX]` as a list of row numbers; `packs_meta.json` is read by no code; so 0038's `resolve_pack` (names, dict form, run_root/data_root) is the only format change and the legacy list is unchanged |
| 0022 strict-keys | `train.ebops_trace_every` on every arm | added to READ_KEYS (read by `ablation.ebops_trace_every`) |

0014 (collapse) applied cleanly: the forced checkpoint `or state.get('collapsed')` is still on
the [A15] cadence line, and `verify_selected`'s new early return (no traced epoch yet) cannot
meet a collapse (epoch 0 is traced, so a candidate exists before any collapse can fire).
RSS gate: no Delta patch catches `SystemExit` / `BaseException` (grep of `patches-anchor/`), the
collapse stop exits 0 before the gate window only by stopping the run, and 0038 passes the
environment through to children, so the gate reaches Delta cells unchanged.

Gates on 42abed4b (CPU, 1 thread, deterministic ops, pinned env; synthetic; not results):
- anchor invariance, pristine vs 0001-0038, every Delta key absent: 19/19 SAME
  (`tests_patches/invariance_gate_anchor.txt`; run_training now 12 epochs so it crosses
  untraced epochs 1-8 and 10 with traced 0, 9, 11);
- `validate_cfg` accepts 96/96 (58 arm configs, 38 const0922);
- `slug_tests_anchor.py` 17/17; `slug_tests.py` on the anchor tree 24/24 (after a harness fix:
  `delta_cfg` reads `configs/` (anchor base, regenerated by the new-files owner, batch 2,790) on
  the anchor tree and `configs-standin/` on the tarball tree, batch capped at 256 for CPU; the
  Bop test compares optimizer variable counts on the same architecture); the three affected
  tests also pass on the tarball tree;
- the anchor's own pytest on the patched tree (incl. test_run_pack, test_run_pack_delta,
  test_memory_leak_fix, test_trace_every): 99 passed, 2 skipped.

RSS / leak check (`tests_patches/rss_slope_anchor.py`, 60 epochs per case, run_training on the
arm config with batch 256 and 512/256 synthetic jets, regime B trace every 10, each case in its
own process; `rss_slope_anchor_42abed4b.txt`). Host RSS slope, MB/epoch over epochs 5-59
(macOS phys_footprint) / live Python objects per epoch / object change end-of-epoch 21 -> 51:
E anchor 2.837 / 0.2 / +11; E always-on 0.869 / 0.2 / +11; A07-350 anchor 0.805 / 0.2 / +11;
A07-350 always-on 0.473 / 0.2 / +11; E latent-EMA 2.264 / 0.2 / +11; E KD stub teacher
1.971 / 0.2 / +11; E diag-sign-flips 0.953 / 0.2 / +9. Every Delta case is at or below its
reference in RSS slope and equal in object growth, so no Delta key adds per-epoch host growth
visible at this resolution. The macOS RSS moves in allocator steps of tens of MB and a 60-epoch
CPU run cannot resolve the anchor gate's ~0.55 MB/epoch budget (the anchor reference itself fits
0.8-2.8 MB/epoch here, run to run: an earlier concurrent 60-epoch run gave 3.5); the gate verdict
belongs to the Linux GPU canary. First run (concurrent with the invariance gate, RSS only):
E anchor 3.496, E always-on 1.957, A07 anchor 3.641, A07 always-on 0.835, EMA 0.331, KD -0.705,
sign flips 0.419 MB/epoch.

Next rebase: same procedure as above (section "Next rebase"); default sha in `apply_anchor.sh`.

### Log lines to append (rebase 2)

- 2026-09-28 (ml-engineer, staged, not shipped) — Delta `patches-anchor/0001-0038` rebased onto
  the regime-B leak-fixed freeze 42abed4b (ConfigMap `kai-chang0926-code-42abed4b5d`); latent-EMA
  cells trace, save and validate EMA latents on traced and untraced epochs alike, selection only
  on traced epochs (anchor rule); `train.ebops_trace_every` read and allowed. With no Delta key the
  anchor reproduces itself bitwise (19/19 incl. a 12-epoch run across untraced epochs).
  weight-scheme-baselines / ternary / hgq-learnable stay refused on the anchor arms until [A22].
  **Check:** `code/apply_anchor.sh <dir>` (ANCHOR_BUNDLE_SHA_OK 42abed4b…);
  `tests_patches/invariance_gate_anchor.txt`.
- 2026-09-28 (finding, CPU, not a result) — no Delta key (always-on collapse/accumulator,
  latent-EMA, KD with a per-batch teacher, sign-flip diagnostics) adds per-epoch Python-object
  growth (0.2 objects/epoch in every case, anchor included) or RSS slope above its anchor
  reference over 60 CPU epochs; macOS RSS cannot resolve the 0.55 MB/epoch gate budget, so the
  GPU canary under `BNJ_RSS_GATE_LIMIT_MB` is the check. **Check:**
  `tests_patches/rss_slope_anchor_42abed4b.txt`.
