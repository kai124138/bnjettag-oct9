# PREFLIGHT — 2026-09-26-training-batch (chang0926), build half

**GPU policy amendment, 2026-09-28 (Kai):** A10-only pilot records below remain historical.
Future production must use [the GPU selection policy](../../docs/infrastructure/gpu-selection-policy.md),
with a per-product timing/memory canary, utilization readout, matched seed blocks, resource-key
check and regenerated manifest. Earlier A10-only review verdicts certify the already-launched
pilot manifests; they do not certify a future production GPU choice. Production PREFLIGHT is open.

Date: 2026-09-27. Scope: the gated N=64 cache job and the one-pod pilot (canary epochs 1-10, the
same pod on to epoch 500). Wave-1 production and wave 2 are **not** in this PREFLIGHT.
Authority: Kai, 2026-09-27 (`.claude/memory/decisions.md`, top entry), under the conditions in
`review/STUDY_arbiter_v5.md` §"What Kai must decide". Owner: ml-engineer (build sections).
cluster-ops appends the live-cluster sections and owns RUN.md.

**Re-freeze, 2026-09-27 (PREFLIGHT gate v1, `review/PREFLIGHT_critical_v1.md`, ITERATE; ml-engineer
as fixer).** Bundle c5d6f02a, ConfigMap `kai-chang0926-code-c5d6f02a83` and manifest ac5a5c86 are
**superseded before any pilot pod**. The epoch-500 post-pause check in that bundle fails by
construction under [D20] (flag 1), and the trainer refuses to resume across a `code_sha256`
change, so a pilot started on it could never be finished by a fixed bundle. The ConfigMap
`kai-chang0926-code-c5d6f02a83` already exists in the cluster (immutable); it stays, unused.
Its payload is kept as `manifests/configmap-c5d6f02a.json`. Everything below refers to the
new bundle unless it says c5d6f02a.

- **Code sha.** Shipped code = `code/tree` (screen bundle 26f3cc40 + patches **0001-0026**) plus
  `code/analysis/` (the [A26] script and its tests, shipped as non-training files).
  **Committed (updated 2026-09-27 after gate v2):** everything listed below is in **15506d7**
  (code, patches 0025-0026, `code/analysis/`, manifests, evidence, this file) and **6278d24**
  (the ConfigMap cluster record and `review/PREFLIGHT_validators_v2.txt`); the campaign's
  `git status` was empty at 6278d24, and gate v2 found HEAD 6278d24 equal to the shipped bundle.
  The text that follows, kept for the record, was written before that commit: repo HEAD
  99f0a2d, `code/tree` last committed at d419b2d (0001-0024), the working tree dirty, and the
  bundle built from it. Dirty at that time, all part of this re-freeze:
  - modified: `code/tree/bnhgq2/ablation.py`, `code/tree/bnhgq2/wandb_util.py`,
    `code/tree/run_engram.py`, `code/tree/run_study.py`;
  - new: `code/tree/tests/test_post_pause_check.py`, `code/tree/tests/test_wandb_stage.py`,
    `code/patches/0025-*.patch`, `0026-*.patch`, and `code/analysis/` (never committed so far);
  - `manifests/`: freeze.py, the regenerated outputs, new `readout-job.json` and
    `configmap-c5d6f02a.json`;
  - new evidence: `code/evidence/cpu_gate_shipped_77f1ca4e.{log,json}` and
    `pytest_shipped_77f1ca4e.log`;
  - this file, and `.claude/memory/decisions.md` (new top entry).

  `review/PREFLIGHT_validators_v1.txt` is untracked (not mine, not shipped). Unrelated dirty
  files elsewhere in the repo are not in the bundle. After the orchestrator's commit, check the
  bundle sha below, not the git sha: `freeze.py` rebuilds the bundle byte for byte from
  `code/tree` + `code/analysis`.
  - `apply.sh` (bundle 26f3cc40 + 0001-0026) today: `APPLY_MATCHES_TREE`.
  - Bundle (ConfigMap payload) sha256:
    **77f1ca4e9fe3f67ef276ec9b7c401c174812fcb2e88b7ef572040ad2e26f2a94**
    (`manifests/chang0926-code.tar.gz`, 186,427 bytes, 245 files). It is deterministic: two
    `freeze.py` runs gave the same sha. The tarball extracted to scratch passes `sha256sum -c`,
    and `diff -r` against `code/tree` and `code/analysis` shows no difference.
  - `run_study.manifest()` sha256 (the `code_sha256` the trainer records and checks on resume):
    **f7d4003f49584c701aec1cfefb4c0c9a3591c41d7d2fda94dd5a293d00eaaa36**. Printed by
    `run_study.manifest()` on the extracted bundle under the pins (tensorflow 2.21.0, keras
    3.15.0, hgq2 0.1.9, quantizers 1.2.2, numpy 2.5.0, scikit-learn 1.9.0). It equals
    `freeze.py`'s re-derivation from the file hashes and `requirements-training.txt`. It hashes the
    top-level and `bnhgq2/` `*.py` files and those versions. `analysis/*.py` is **outside** it
    (listed under `analysis_files_outside_manifest` in `bundle-manifest.json`), so the entropy
    script can change without touching a run's `code_sha256`; any such change still needs a new bundle.
- **ConfigMap.** `kai-chang0926-code-77f1ca4e9f`, `immutable: true`, key `hgq2.tar.gz`,
  annotations bundle-sha256 77f1ca4e... and manifest-sha256 f7d4003f..., in `manifests/configmap.json`
  (base64 payload decodes to 77f1ca4e..., checked locally). **Created and verified** 2026-09-27 by
  cluster-ops (immutable `true`, annotation and independently decoded payload sha 77f1ca4e...;
  record in "ConfigMap create and verify" below).
  Payload holds the 58 configs, `index.json`, `packs.json`, `pilot_packs.json`,
  `canary_packs.json`, `cache_configs/n64.json`, and `analysis/attn_entropy.py`,
  `analysis/test_attn_entropy.py`.
- **Cache stays valid, no rebuild.** `run_engram.load_cache` (`run_engram.py:176-221`) checks
  `READY.json`, the split/gate keys (`n_part`, `features`, `split_seed`, `order_seed` when not
  null, `pt_gate_gev`, `validation_split`), the four array hashes, dtypes, shapes, labels and the
  558,000 / 62,000 split. It never reads `code_sha256`: `grep -n code_sha256 run_engram.py` has
  no hit. The cache's `data_info.json` records the c5d6f02a manifest sha ac5a5c86 as provenance
  only. `cache-job.json` is regenerated (new name `kai-chang0926-cache-77f1ca`) but does **not**
  need to be applied: the pilot pod only requires `READY.json`.
  - **Do not rebuild the cache** (gate v2 flag 6, 2026-09-27). Each run's
    `state['data_sha256'] = digest_json(data_info)` (`ablation.py:591`, checked on resume at
    `:297`), and `data_info` embeds the cache's own `code_sha256` ac5a5c86
    (`prepare_cache.py:137`). A rebuild under 77f1ca4e would change `data_sha256` and block any
    pilot→production resume. `kai-chang0926-cache-77f1ca` stays unapplied while that resume is an
    option.
- **Generator.** `manifests/freeze.py` (never submits). Outputs: `chang0926-code.tar.gz`,
  `configmap.json`, `cache-job.json`, `pilot-job.json`, **`readout-job.json`** (new),
  `bundle-manifest.json` (per-file sha256). It asserts:
  - 58 index rows, each config file hashing to its `config_sha256`;
  - `pilot_packs.json` = `[[0, 1, 24, 48, 56, 57]]`; `packs.json` 10 packs;
  - `cache_configs/` holds only `n64.json`, and `cache_configs/n64.json` agrees with all 58 run
    configs on `n_part`, `features`, `pt_gate_gev`, `validation_split` and `split_seed`, with
    `order_seed_in_cache` false;
  - manifest sha = `EXPECTED_MANIFEST` (f7d4003f...);
  - base64 payload < 1 MB;
  - `export BNJ_STAGE=pilot` in the pilot script.

  Regenerate with it; never hand-edit the JSONs.

### Patches of this re-freeze (each with a CPU test; synthetic data, not results)

| patch | fixes | change | test | result |
| --- | --- | --- | --- | --- |
| 0025 | gate v1 flag 1 (A) | New `ablation.selected_checkpoint_ebops(cfg, loaded, xt)`. Under `ebops_reload_check: "stored"` it returns the file's stored per-layer EBOPs (no trace, so `predict` runs on the saved ranges). Otherwise it retraces with reset on `ebops_trace_sample(cfg, xt)` at `ebops_trace_batch(cfg)`; with neither key that is `xt[:256]` at batch 2048, the screen call unchanged. Used at the old `run_study.py:151` (the block moved into `run_study.verify_selected`, which `train` calls after its GPU/TF32 asserts) and at `run_engram.py:281`. `screen_result.json` gains `reload_ebops_check` | `tests/test_post_pause_check.py`: tiny WRAP config, `train_full`, `i_decay_speed` 0.001, `stop_after=2`, then `verify_selected`. The stored and retrace variants both print `CHECKPOINT_VERIFICATION_PASS`; a wrong logged value raises; the no-key path equals `compute_ebops(xt[:256])` | 4 passed. The pre-fix 256-row retrace of the same checkpoint gives 95,388 against the logged 110,972 (`POST_PAUSE_TEST` line), so the test would have caught flag 1 |
| 0026 | gate v1 flags 3, 6 (B, C); PREFLIGHT flagged decisions 3, 4 | In `bnhgq2/wandb_util`: `run_stage()` reads `BNJ_STAGE` ∈ {pilot, canary, production}; `stage_run_id` = sha256(stage + NUL + name)[:12]; `stage_group` = config group + `-canary` for pilot/canary, the config group for production. Used in `ablation.run_training` (remote) and in `run_engram`'s `resume='must'` review path. A tracked run with no stage is refused; `run_study.train` prints `RUN_STAGE <stage>` before any work | `tests/test_wandb_stage.py`: the id is deterministic within a stage and distinct across stages and from the old sha256(name) id; the group follows the stage, wave-2 suffix included; an unset or unknown stage is refused; `run_training(remote=True)` with wandb stubbed passes the stage id, `resume='allow'` and the `-canary` group | 4 passed |

**Other `[:256]` sites, from a grep of the tree (`grep -rn ":256\]" --include=*.py`):**
- `ablation.py:446` is `ebops_trace_sample`'s own no-key default (the screen).
- `ablation.py:544` is the engram epoch-observer diagnostic sample, not a cost check.
- `train.py:331` belongs to the legacy `bnhgq2/train.py` trainer, which this campaign does not run.
- The rest are tests.

`run_study.py:73/80` (preflight stage) traces the same 32-row sample on both sides of the save.
No other retrace-then-assert against a logged full-split value remains.

The pilot W&B group is now `chang-n64-20260926-canary`, as STUDY l. 1249 and l. 1468 require. The
tags `chang0926,pilot,canary,validation-only` stay. **STUDY l. 1471-1472** ("The runner's run id
is sha256(config name)[:12]") was out of date; **amended 2026-09-27** by the fixer after gate v2
(STUDY l. 1473-1480: stage + NUL + config name, group by `BNJ_STAGE`, production manifests set
`BNJ_STAGE=production`; config names must still be unique per arm and seed within a stage).

## Configs (the six pilot configs)

Source: `code/evidence/cpu_gate_d25.log` (CPU, synthetic sample; build checks, not results), on
the tree that is byte-identical to the shipped bundle. Tolerance used by the gate:
`atol = rtol = 2e-6` on predictions after save/reload (`cpu_gate.py:97`); the measured max |Δ| is
0.0, so the template's 1e-7 holds too. TF32: not applicable on CPU; in the pod
`NVIDIA_TF32_OVERRIDE=0` and `run_study.train` disables TF32 and asserts it.

| job idx | run | arm | config file | builds on CPU | params (count_params) | kernel+bias+PE | reload max \|Δ\| | `i_decay_speed` record |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | chang0926-a-n64-s1 | A | `chang0926-a-n64-s1.json` | PASS | 31,735 | 6,253 | 0.0 | 0.001 on 14 quantizers |
| 1 | chang0926-a-n64-s2 | A | `chang0926-a-n64-s2.json` | PASS | 31,735 | 6,253 | 0.0 | 0.001 on 14 quantizers |
| 24 | chang0926-d-n64-s1 | D | `chang0926-d-n64-s1.json` | PASS | 31,735 | 6,253 | 0.0 | 0.001 on 14 quantizers |
| 48 | chang0926-a07-350-n64-s1 | A07-350 | `chang0926-a07-350-n64-s1.json` | PASS | 61,951 | 11,653 | 0.0 | 0.001 on 14 quantizers |
| 56 | chang0926-cprime-n64-s1 | C′ (pilot-only) | `chang0926-cprime-n64-s1.json` | PASS | 12,788 | 11,653 | 0.0 | no key, 0 quantizers, empty |
| 57 | chang0926-e1-n64-s1 | E1 (pilot-only) | `chang0926-e1-n64-s1.json` | PASS | 19,447 | 6,253 | 0.0 | 0.001 on 14 quantizers |

Verbatim (`cpu_gate_d25.log`, lines 1-4, 51-52, 99-100, 115-119):

```
CONFIG_PREFLIGHT_PASS chang0926-a-n64-s1 params 31735 kernel_bias_pos 6253 initial_ebops 9429139 reload_max_abs_diff 0.0 zero_floor 171526 floor_retraced 171526 production 1
I_DECAY_OK chang0926-a-n64-s1 config 0.001 quantizers 14 values [0.0010000000474974513]
CONFIG_PREFLIGHT_PASS chang0926-a-n64-s2 params 31735 kernel_bias_pos 6253 initial_ebops 8951051 reload_max_abs_diff 0.0 zero_floor 171526 floor_retraced 171526 production 1
I_DECAY_OK chang0926-a-n64-s2 config 0.001 quantizers 14 values [0.0010000000474974513]
CONFIG_PREFLIGHT_PASS chang0926-d-n64-s1 params 31735 kernel_bias_pos 6253 initial_ebops 9429139 reload_max_abs_diff 0.0 zero_floor 171526 floor_retraced 171526 production 1
I_DECAY_OK chang0926-d-n64-s1 config 0.001 quantizers 14 values [0.0010000000474974513]
CONFIG_PREFLIGHT_PASS chang0926-a07-350-n64-s1 params 61951 kernel_bias_pos 11653 initial_ebops 13805846 reload_max_abs_diff 0.0 zero_floor 343053 floor_retraced 343053 production 1
I_DECAY_OK chang0926-a07-350-n64-s1 config 0.001 quantizers 14 values [0.0010000000474974513]
CONFIG_PREFLIGHT_PASS chang0926-cprime-n64-s1 params 12788 kernel_bias_pos 11653 initial_ebops 24816782 reload_max_abs_diff 0.0 zero_floor 4580398 floor_retraced 4580398 production 0
I_DECAY_OK chang0926-cprime-n64-s1 config None quantizers 0 values []
CONFIG_PREFLIGHT_PASS chang0926-e1-n64-s1 params 19447 kernel_bias_pos 6253 initial_ebops 8742421 reload_max_abs_diff 0.0 zero_floor 85763 floor_retraced 85763 production 0
I_DECAY_OK chang0926-e1-n64-s1 config 0.001 quantizers 14 values [0.0010000000474974513]
PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2
```

**Re-run on the shipped bundle, c5d6f02a (superseded)** (the STUDY [A21] "re-asserts on the shipped tree"): the
tarball was extracted to a scratch directory and `cpu_gate.py --only A,D,A07-350,C-PRIME,E1` run
there on CPU under the pinned versions (`uv run --with` tensorflow 2.21.0, keras 3.15.0, hgq2 0.1.9,
quantizers 1.2.2, numpy 2.5.0, scikit-learn 1.9.0, h5py 3.14.0, hls4ml 1.3.0, wandb 0.28.0; laptop
CPU, synthetic sample, not a result). Output `code/evidence/cpu_gate_shipped_c5d6f02a.log` / `.json`:

```
PREFLIGHT_ALL_PASS 26 production 24 pilot_only 2
```

All 52 `CONFIG_PREFLIGHT_PASS` / `I_DECAY_OK` lines (every seed of A, D, A07-350, plus C′-s1 and
E1-s1) are byte-identical to the matching lines of `cpu_gate_d25.log`. In the same environment,
`run_study.manifest()` on the extracted bundle printed
`MANIFEST_SHA_OK ac5a5c867c6e06957bf17079b210532ee34989276edc51ffc1f539f195d895b2`.

**Re-run on the new shipped bundle 77f1ca4e (2026-09-27, after patches 0025-0026).** Same
procedure: extract `manifests/chang0926-code.tar.gz` to scratch (`sha256sum -c` OK) and run
`cpu_gate.py --only A,D,A07-350,C-PRIME,E1` there. That covers 26 configs: every seed of A, D and
A07-350, plus C′-s1 and E1-s1, so the six pilot configs are among them. Pinned versions as above;
laptop CPU, synthetic sample, not a result. Output `code/evidence/cpu_gate_shipped_77f1ca4e.log` / `.json`:

```
PREFLIGHT_ALL_PASS 26 production 24 pilot_only 2
```

All 53 `CONFIG_PREFLIGHT_PASS` / `I_DECAY_OK` / `PREFLIGHT_ALL_PASS` lines are byte-identical to
`cpu_gate_shipped_c5d6f02a.log` (`diff` empty), so the Configs table above holds for this bundle.
The six pilot rows, verbatim from the new log:

```
CONFIG_PREFLIGHT_PASS chang0926-a-n64-s1 params 31735 kernel_bias_pos 6253 initial_ebops 9429139 reload_max_abs_diff 0.0 zero_floor 171526 floor_retraced 171526 production 1
CONFIG_PREFLIGHT_PASS chang0926-a-n64-s2 params 31735 kernel_bias_pos 6253 initial_ebops 8951051 reload_max_abs_diff 0.0 zero_floor 171526 floor_retraced 171526 production 1
CONFIG_PREFLIGHT_PASS chang0926-d-n64-s1 params 31735 kernel_bias_pos 6253 initial_ebops 9429139 reload_max_abs_diff 0.0 zero_floor 171526 floor_retraced 171526 production 1
CONFIG_PREFLIGHT_PASS chang0926-a07-350-n64-s1 params 61951 kernel_bias_pos 11653 initial_ebops 13805846 reload_max_abs_diff 0.0 zero_floor 343053 floor_retraced 343053 production 1
CONFIG_PREFLIGHT_PASS chang0926-cprime-n64-s1 params 12788 kernel_bias_pos 11653 initial_ebops 24816782 reload_max_abs_diff 0.0 zero_floor 4580398 floor_retraced 4580398 production 0
CONFIG_PREFLIGHT_PASS chang0926-e1-n64-s1 params 19447 kernel_bias_pos 6253 initial_ebops 8742421 reload_max_abs_diff 0.0 zero_floor 85763 floor_retraced 85763 production 0
```

On the same extracted bundle, `run_study.manifest()` printed
`f7d4003f49584c701aec1cfefb4c0c9a3591c41d7d2fda94dd5a293d00eaaa36`, and `pytest tests/
analysis/test_attn_entropy.py` gave `71 passed, 2 skipped` (`code/evidence/pytest_shipped_77f1ca4e.log`).

**Full-set gate on the shipped bundle (for wave-1 production), 2026-09-27.** STUDY [A21] asks for
every listed arm on the shipped tree; the entry above covered only the pilot subset, so B, C, F and
R had not been gated on 77f1ca4e. `manifests/chang0926-code.tar.gz` (sha256 `77f1ca4e9f...`, `shasum -a 256` matched) was
extracted fresh to scratch; `run_study.manifest()` there printed `f7d4003f49584c70...`. Then
`cpu_gate.py` ran without `--only`, over all 58 configs (56 production + 2 pilot-only). Pinned
versions as above; laptop CPU, synthetic sample, not a result. Output
`code/evidence/cpu_gate_shipped_77f1ca4e_full.log` / `.json`, exit 0:

```
PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2
```

All 117 `CONFIG_PREFLIGHT_PASS` / `I_DECAY_OK` / `PREFLIGHT_ALL_PASS` lines are byte-identical to
`cpu_gate_d25.log` (`diff` empty), and the JSON equals `cpu_gate_d25.json` (58 entries; `production 0`
only for `chang0926-cprime-n64-s1` and `chang0926-e1-n64-s1`). The Configs table and the d25 Gates
line therefore hold on the shipped bundle for every arm. [A17] pairing on the same extraction
(`check_pairing.py --arms a,b,d,r --seeds 1,2,3,4,5,6,7,8`): 32 / 32 `PAIRED`, 0 `UNPAIRED`, each
differing from F only by `pos_enc/pos_table` with 0 of 15 shared hashes differing; the JSON equals
`a17_pairing_d25_8seeds.json`. Evidence `code/evidence/a17_pairing_shipped_77f1ca4e_8seeds.json` / `.log`.

The in-pod reload check is separate. At the epoch-500 pause, `run_study.verify_selected` reloads
the selected checkpoint and checks its EBOPs by the config's reload-check method. All six pilot
configs carry `ebops_reload_check: "stored"`, so the check reads the file's stored per-layer EBOPs,
which must equal the logged value exactly, with no retrace (patch 0025). It then re-predicts
validation AUC and accuracy (`atol = 1e-7`, `rtol = 0`) and prints `CHECKPOINT_VERIFICATION_PASS`
per arm. That output belongs to RUN.md and selects nothing. The full-split retrace is the
readout Job's certification step (Manifests (c)).

## Gates

- **CPU build/reload gate** (`campaigns/chang0926/cpu_gate.py`, the campaign's form of the
  preflight): `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2` (`code/evidence/cpu_gate_d25.log:119`,
  JSON `cpu_gate_d25.json`). Every config at `reload_max_abs_diff 0.0`, `floor_retraced` equal to
  the config's `zero_floor`.
- **Unit tests:** `pytest tests/` in the staged tree gave **64 passed**: 56 through patch 0024,
  then 4 for 0025 and 4 for 0026. `analysis/test_attn_entropy.py` gave 7 passed and 2 skipped (the
  main() test runs on the A build only). On the extracted bundle 77f1ca4e: `71 passed, 2 skipped`,
  with the pass lines in `code/evidence/pytest_shipped_77f1ca4e.log`.
- **[A26] entropy script** (`code/analysis/attn_entropy.py`, shipped as `analysis/attn_entropy.py`).
  **[A26] is ready before the epoch-500 readout.**
  - Loading: the script loads a `.keras` file after `run_engram.runtime()` registers the custom
    objects (`load_model(compile=False)`) and builds one sub-model on every `{blk}_attn_softmax`
    output (both branches).
  - Data: it feeds **only `x_val`** (default all 62,000 rows; `n_val_rows` is recorded). The only
    data path is `run_engram.load_cache`, which opens the train/val arrays only, so there is no
    ROC-test path (`test_set_used: false` in the output).
  - Output per block and head: H / log 64 with p = softmax output / row sum (primary;
    `decisions.md` 2026-09-27), the un-renormalized value, and row-sum min/mean/max.
  - Attention state (STUDY): the Q/K and V 0-bit channel fractions, with sign bits and the
    "silent, billed 1 bit" label for SAT channels.
  - CPU tests on tiny checkpoints built with the staged code (A: chang softmax, WRAP; C′: fixed
    softmax, SAT; fp32), each saved and reloaded. Uniform logits give 1 within 1e-6 (pure
    function, reloaded softmax layer, full sub-model). One-hot logits give < 1e-6.
  - Why renormalize: the C′ uniform row sums are 4.0, and its un-renormalized value is 2.67.
  - A main() test runs the readout call on an epoch-500 snapshot layout.
- **Regression, no-new-keys path** (const0922 a00/a07/b02/b03, fresh bundle extract vs staged
  tree): recomputed today from the evidence files, `regression_base.json` ==
  `regression_patched_d25.json` (init level) and `regression_run_training_base.json` ==
  `regression_run_training_patched_d25.json` (2-epoch `run_training`): both **True**.
- **[A7] floors** (`trace_floors.py`, `code/evidence/static_floors_arms_s1_d25.json`, CPU,
  synthetic sample, not results), totals zero / one / attn_narrow / attn_full:
  A, D 171,526 / 619,198 / 368,134 / 478,726; A07-350 343,053 / 1,005,741 / 605,197 / 801,805;
  C′ 4,580,398 in every mode; E1 85,763 / 533,435 / 282,371 / 392,963. Equal to the pre-[D25]
  `static_floors.json` (`plan.md:586-590`).
- **[A17] pairing** (`a17_pairing_d25_8seeds.json`): 32 / 32 PAIRED (A, B, D, R against F, 8 seeds),
  recomputed today.
- **Smoke (2 files, 3 epochs):** did not run. The screen-era smoke does not apply to the gated
  90/10 cache, which exists only on the PVC; the canary (epochs 1-10) is the first run on real data.

## Manifests

All in `campaigns/2026-09-26-training-batch/manifests/`, generated by `freeze.py`. The embedded bash
of all three Jobs passes `bash -n` (checked 2026-09-27 on the 77f1ca4e outputs). The Job names
below are the regenerated ones; c5d6f0 names in the cluster-ops sections belong to the superseded bundle.

**(a) `cache-job.json`, Job `kai-chang0926-cache-77f1ca`.** Not to be applied again: the applied
c5d6f0 Job did the build (see "Cache stays valid" above). (CPU, non-Indexed, `backoffLimit 0`,
`activeDeadlineSeconds 7200` as the screen's data job, 4 CPU / 16 Gi, hostname exclusions).
Sequence: bundle `sha256sum -c` → pip `requirements-cpu.txt` → `MANIFEST_SHA_OK` and
`BNHGQ2_CODE_SHA256=<manifest sha>` exported → 62 raw `.h5` files counted →
`prepare_cache.py --configs /work/code/campaigns/chang0926/cache_configs --root /data/chang-n64-20260926 --raw /data/hls4ml_lhc_jet/train/train --n-parts 64`
(that directory holds only `n64.json`; the top-level `cache_configs/` is the screen's and is not
used) → one `DATA_INFO` line from `data_info.json` (`n_train`, `n_val`, `pt_gate_gev`,
`validation_split`, `split_seed`, `order_seed`, `pt_gate_stats`, `sort_stats`, `y_class_counts`,
`code_sha256`, `array_sha256`) →
`nondegenerate_threshold.py --cache /data/chang-n64-20260926/n64/data --out /data/chang-n64-20260926/n64/nondegenerate_threshold.json`
→ `df -h /data` → `CACHE_JOB_DONE`. It is idempotent: with `READY.json` present,
`prepare_cache.py` only re-verifies.

**(b) `pilot-job.json`, Job `kai-chang0926-pilot-77f1ca`** (GPU; ConfigMap `kai-chang0926-code-77f1ca4e9f`):
- Indexed, `completions 1`, `parallelism 1` (`run_pack.py` reads `JOB_COMPLETION_INDEX`),
  `backoffLimitPerIndex 2`, `podReplacementPolicy Failed`, `podFailurePolicy` Ignore on
  `DisruptionTarget`, **`activeDeadlineSeconds` unset** (deliberate; STUDY §Resume).
- K=6, `run_pack.py pilot_packs.json 500`: pack `[[0, 1, 24, 48, 56, 57]]` = A-s1, A-s2, D-s1,
  A07-350-s1, C′-s1, E1-s1; batch 2,790 comes from the configs; `--stop-after 500`. The canary
  readout is epochs 1-10 of this same pod; there is no separate canary Job.
- `bnjettag.io/arms-per-pod: "6"` on the Job and the pod template; 12 CPU, 36 Gi, 24 Gi
  ephemeral, 1 × `nvidia.com/gpu`.
- Node affinity, required: `NVIDIA-L40`, `NVIDIA-A10`, `NVIDIA-GeForce-RTX-3090`,
  `Tesla-V100-SXM2-32GB` (preferred: L40); hostname NotIn chase-ci-07, fullerton gpu01,
  ren-gp-argo-01. No A100. See flagged decision 1.
- Env: `BNJ_DATA_ROOT=/data/chang-n64-20260926`, `BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot`,
  `BNJ_CAMPAIGN_DIR=/work/code/campaigns/chang0926`, `TF_FORCE_GPU_ALLOW_GROWTH=true`,
  **`BNJ_STAGE=pilot`** (W&B id and group, patch 0026),
  `NVIDIA_TF32_OVERRIDE=0`, `WANDB_MODE=online`, `WANDB_ENTITY=kayamaguchi-uc-san-diego`,
  `WANDB_TAGS=chang0926,pilot,canary,validation-only`; `WANDB_PROJECT` explicitly unset, so the
  project is the configs' `BNJetTag-ChangRecipe` and `validate_tracking_destination` accepts it.
- W&B key: `WANDB_API_KEY` from `secretKeyRef` `kai-wandb` / `WANDB_API_KEY`, as the screen and
  confirmation jobs. The key is not in any file here.
- Runner isolation ([A12], patch 0007, `run_pack.py`): exit 3 = recorded divergence, that arm
  stops and the others continue; any other failure tails the arm log and relaunches that arm
  only, from its own checkpoint, up to `BNJ_ARM_RETRIES` (2); the pod exits 1 only after every
  other arm has finished. `nvidia-smi` utilisation and memory are printed every 60 s.
- Pre-training checks in the pod: `MANIFEST_SHA_OK`, `GPU_GATE_PASS`, cache `READY.json` present
  (else `CACHE_NOT_READY`, exit 1), GPU name and memory, `df -h /data`; per arm `RUN_STAGE pilot`.
- W&B: group `chang-n64-20260926-canary`, run id sha256("pilot" + NUL + config name)[:12].

**(c) `readout-job.json`, Job `kai-chang0926-readout-77f1ca`** (CPU, new; STUDY Budget/pilot
"Certification check" l. 1275-1277 and [A26]; gate v1 flag 4).
- **Who and when.** cluster-ops applies it **after the pilot pod has paused at epoch 500**;
  results-analyst reads it.
- **Header.** Same as the cache Job: bundle `sha256sum -c`, `requirements-cpu.txt`,
  `MANIFEST_SHA_OK f7d4003f...`, `CUDA_VISIBLE_DEVICES=-1`, `WANDB_MODE=disabled`,
  `BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot`.
- **Resources.** 8 CPU / 24 Gi / 12 Gi ephemeral, `backoffLimit 0`, `activeDeadlineSeconds 14400`.
  - **Open for ml-engineer (gate v2 flag 5, 2026-09-27):** the `work` emptyDir has `sizeLimit
    24Gi` (`readout-job.json:108`) but the container's ephemeral-storage limit is 12Gi (`:72`,
    `:77`), so eviction at 12 Gi is the effective cap. Make them agree in `freeze.py` and
    regenerate; a manifest change, not made in this text pass. The readout Job needs a new
    manifest for flag 3 or decision 6 anyway.
- **Trace cost.** The CPU full-split trace cost in the pod is unmeasured. The laptop evidence
  projects about 99 s (E) and 184 s (A07) per 558,000-row trace (`trace_cost_cpu.json`), for at
  most 12 checkpoints.

Sequence:
1. Gate: for each of the six pilot runs, `runs/<name>/snapshots/epoch-0500/state.json` or
   `DIVERGED.json` exists, else `SNAPSHOTS_NOT_READY <name>` and exit 1; cache `READY.json`.
2. `certify_ebops.py --run-root /data/chang-n64-20260926/pilot/runs --cache /data/chang-n64-20260926/n64/data --snapshot 500 --only <six names> --out $OUT/certify-snapshot-0500.json`.
   - Each best-as-of-500 file (`model_best.keras` and, where present,
     `model_best_auc_feasible.keras`) is reloaded fresh and retraced (`reset=True`) on the full
     558,000-row training split at the config's `ebops_trace_batch`.
   - Gate lines: per file `CERTIFIED` / `EBOPS_MISMATCH` / `STORED_MISMATCH` / `ABOVE_TARGET`,
     then `CERTIFICATION_ALL_PASS n 0` or `CERTIFICATION_FAIL n k` (exit 4).
   - Rule (STUDY l. 1285-1287): retraced = logged within relative 1e-6; a mismatch stops
     production until ml-engineer fixes it. A CPU mismatch follows the CPU→GPU re-run rule
     (four conditions; `.claude/memory/decisions.md` top entry, STUDY l. 1288-1296).
   - `certify_ebops.main()` asserts each run's `data_info.json` `train_sha256` equals the cache's.
     The key is present in both: `prepare_cache.py:135` writes it into the cache's `data_info`, and
     `ablation.run_training` copies that dict into the run directory. `main()` itself has not run
     against a real cache (only `certify_checkpoint` is unit-tested, `tests/test_certify.py`).
3. `analysis/attn_entropy.py --indices 0 1 24 48 56 57 --epoch 500 --out $OUT/a26-entropy-epoch-0500.json`
   on validation (n = 62,000).
   - Lines: `A26_ENTROPY <run> <blk> head h H_over_logN ... split validation n 62000`,
     `A26_ROWSUM`, `A26_ZEROBIT`, `A26_WROTE <path> sha256 <sha>`, then `A26_DONE` (or
     `A26_INCOMPLETE k`, exit 1).
   - A run with no feasible snapshot uses `model_min_ebops.keras`, labelled by
     `checkpoint_reason`. A diverged run is skipped (`A26_SKIPPED`).
4. `sha256sum` of both JSONs, then `READOUT_JOB_DONE certify_exit=<c> a26_exit=<a>`. The Job
   fails if either step failed.

`$OUT` = `/data/chang-n64-20260926/pilot/readout-epoch-0500-77f1ca`. The entropy script refuses
to overwrite its output, so a re-run needs the old file moved first.

Build-half lint of the 77f1ca4e outputs (2026-09-27, ml-engineer; verbatim):

```
$ python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-26-training-batch/manifests/configmap.json campaigns/2026-09-26-training-batch/manifests/cache-job.json campaigns/2026-09-26-training-batch/manifests/pilot-job.json campaigns/2026-09-26-training-batch/manifests/readout-job.json
-- campaigns/2026-09-26-training-batch/manifests/configmap.json: no Job manifest found

== campaigns/2026-09-26-training-batch/manifests/cache-job.json :: kai-chang0926-cache-77f1ca ==
  note   no required GPU product list — widest possible pool (good)
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  OK

== campaigns/2026-09-26-training-batch/manifests/pilot-job.json :: kai-chang0926-pilot-77f1ca ==
  note   required pool = 4 products / 108 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 6 arms per pod declared.
  OK

== campaigns/2026-09-26-training-batch/manifests/readout-job.json :: kai-chang0926-readout-77f1ca ==
  note   no required GPU product list — widest possible pool (good)
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  OK

(rules: docs/infrastructure/nrp-nautilus-setup.md -> 'Scheduling, GPU pools and job shape')
exit=0
```

No WARN on any manifest. `git diff` shows the pilot manifest differs from the c5d6f02a one only in
the Job name, the ConfigMap name, the bundle and manifest shas in the script, and
`export BNJ_STAGE=pilot`. The readout Job is a single CPU Job by design, and it sets `activeDeadlineSeconds`.

**[cluster-ops] ConfigMap kai-chang0926-code-77f1ca4e9f, 2026-09-27** (post gate-v1 re-freeze,
pilot/readout not applied — v2 comes first):

Live lint, both manifests, immediately before `create`, exit 0, no WARN:

```
$ python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-26-training-batch/manifests/pilot-job.json
== campaigns/2026-09-26-training-batch/manifests/pilot-job.json :: kai-chang0926-pilot-77f1ca ==
  note   required pool = 4 products / 109 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 6 arms per pod declared.
  OK
exit=0

$ python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-26-training-batch/manifests/readout-job.json
== campaigns/2026-09-26-training-batch/manifests/readout-job.json :: kai-chang0926-readout-77f1ca ==
  note   no required GPU product list — widest possible pool (good)
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  OK
exit=0
```

`pilot-job.json` mounts ConfigMap `kai-chang0926-code-77f1ca4e9f` (grepped from the manifest) and
sets `export BNJ_STAGE=pilot` in the container command; both confirmed by inspection, not
inferred.

ConfigMap create and verify:

```
$ kubectl create -f campaigns/2026-09-26-training-batch/manifests/configmap.json -n cms-ml
configmap/kai-chang0926-code-77f1ca4e9f created
```

`kai-chang0926-code-77f1ca4e9f` did not pre-exist (checked `NotFound` first). Old ConfigMap
`kai-chang0926-code-c5d6f02a83` left in place, confirmed present after the create (`kubectl get cm
kai-chang0926-code-c5d6f02a83 -n cms-ml` → found, untouched). Three checks on the new object:
- `kubectl get cm kai-chang0926-code-77f1ca4e9f -n cms-ml -o jsonpath='{.immutable}'` → `true`.
- `bnjettag.io/bundle-sha256` annotation on the live object → `77f1ca4e9fe3f67ef276ec9b7c401c174812fcb2e88b7ef572040ad2e26f2a94`.
- Decoded payload, independently hashed (not the annotation's own claim): `kubectl get cm
  kai-chang0926-code-77f1ca4e9f -n cms-ml -o json` → `binaryData['hgq2.tar.gz']` base64-decoded
  (186427 bytes) and sha256'd → `77f1ca4e9fe3f67ef276ec9b7c401c174812fcb2e88b7ef572040ad2e26f2a94`
  — equals the manifest's own annotation and the bundle sha quoted throughout this file.

Cache Job **not** re-applied: `load_cache` does not check `code_sha256`, so the gated cache from
`kai-chang0926-cache-c5d6f0` (built against the c5d6f02a bundle, verified above) stays valid for
the 77f1ca4e code. Pilot **not** applied — PREFLIGHT gate v2 first.

**Superseded (c5d6f02a):** the cluster-ops record below is for the old bundle and ConfigMap, kept
as history. Its W&B, secret, cache-job and node-pool facts still hold; its ConfigMap and Job names do not.

<!-- cluster-ops: pre-apply lint re-run, ConfigMap creation and verification output go below. -->
**[cluster-ops]** live lint at apply time (2026-09-27, re-run immediately before `create`/`apply`,
identical to the build-half lint above, exit 0, no WARN on either manifest):

```
$ python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-26-training-batch/manifests/configmap.json
-- campaigns/2026-09-26-training-batch/manifests/configmap.json: no Job manifest found
exit=0

$ python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-26-training-batch/manifests/cache-job.json
== campaigns/2026-09-26-training-batch/manifests/cache-job.json :: kai-chang0926-cache-c5d6f0 ==
  note   no required GPU product list — widest possible pool (good)
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  OK
exit=0

$ python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-26-training-batch/manifests/pilot-job.json
== campaigns/2026-09-26-training-batch/manifests/pilot-job.json :: kai-chang0926-pilot-c5d6f0 ==
  note   required pool = 4 products / 109 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 6 arms per pod declared.
  OK
exit=0
```

The `pre-kubectl-lint.py` hook re-ran this same lint on the `kubectl create`/`apply` calls below;
neither manifest changed since the build-half lint, so the output above is unchanged (the pilot's
109-node note reads 110 nodes live at apply time, noted below — that is cluster drift, not a
manifest change, and lint does not re-derive that count).

**[cluster-ops]** ConfigMap created and verified, 2026-09-27:

```
$ kubectl create -f campaigns/2026-09-26-training-batch/manifests/configmap.json -n cms-ml
configmap/kai-chang0926-code-c5d6f02a83 created
```

Neither the ConfigMap nor the cache/pilot Jobs pre-existed (`NotFound` checked first, no
overwrite). Verified separately, three checks:
- `kubectl get cm kai-chang0926-code-c5d6f02a83 -n cms-ml -o jsonpath='{.immutable}'` → `true`.
- `bnjettag.io/bundle-sha256` annotation on the object reads
  `c5d6f02a83c736c8a3ae5e9a0d99dbf0ff334df58bb24b41aff32e4940a13b3b` (matches the shipped bundle
  sha in the build half).
- `kubectl get cm kai-chang0926-code-c5d6f02a83 -n cms-ml -o jsonpath='{.binaryData.hgq2\.tar\.gz}' | base64 -d | shasum -a 256`
  → `c5d6f02a83c736c8a3ae5e9a0d99dbf0ff334df58bb24b41aff32e4940a13b3b` — **equals** the bundle sha
  in open item 1. ConfigMap name, immutability and decoded payload all confirmed.

## W&B (cluster-ops, 2026-09-27)

- **Project existence/access.** Queried the project the same way the pod does
  (`run_engram.validate_tracking_destination`'s GraphQL path,
  `wandb.sdk.internal.internal_api.Api.execute`, `WANDB_API_KEY` loaded from
  `bnjettag/wandb-api-key.txt` into an env var inline, never printed): first query returned
  `null` — `kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe` did not exist. Created it PRIVATE via
  the `upsertModel` mutation with `access: PRIVATE` (same API surface, one extra field), then
  **re-queried** with the identical `EngramProjectAccess` query used above (not the create call's
  own return): `{'name': 'BNJetTag-ChangRecipe', 'access': 'PRIVATE'}`. The project exists and is
  PRIVATE, confirmed via the pod's own check path.
- **Secret.** `kubectl -n cms-ml get secret kai-wandb -o json` parsed for type and key names
  only (no value read or printed): `type Opaque`, key `WANDB_API_KEY` — matches what the pilot
  manifest mounts (`secretKeyRef.name kai-wandb`, `.key WANDB_API_KEY`). Existence confirmed;
  value not compared (out of scope per task).

## Cache job (cluster-ops, 2026-09-27)

`kubectl apply -f campaigns/2026-09-26-training-batch/manifests/cache-job.json -n cms-ml` at
**2026-09-27 17:47:43 UTC** → `job.batch/kai-chang0926-cache-c5d6f0 created`. Pod
`kai-chang0926-cache-c5d6f0-bhrkh` scheduled immediately on `node-2-11.sdsc.optiputer.net`
(not in `KNOWN_BAD_NODES`, not one of the pilot's excluded hostnames). Job `Complete 1/1`,
duration 2m40s, at **2026-09-27 17:50:26 UTC** — well inside the 7200s `activeDeadlineSeconds`.
No incident; nothing added to `cluster-inventory.md`.

Verbatim from the pod log, in order:

```
MANIFEST_SHA_OK ac5a5c867c6e06957bf17079b210532ee34989276edc51ffc1f539f195d895b2
[raw_load] /data/hls4ml_lhc_jet/train/train N64 once
[raw_loaded] (620000, 64, 3)
[cache_ready] /data/chang-n64-20260926/n64/data seconds 112.38533716099982
BATCH_CACHES_ALL_PASS
DATA_INFO {"array_sha256": {"x_train": "420ac79dcece207aca849f6ca56e6426586023c9e02f38e5d3ac596fa74d79bc", "x_val": "7b56c1b25bc0d9231767f891ec52455ecb7c5656735fcf9d404104fd2c264d31", "y_train": "a5269398e2c6e5f1fc0db98e1a99a8befea619bf0c55531293d02a286c0dd378", "y_val": "63049d9bdcfdc83af97c58bc6579e1def1ec2d9e7a6c30007793badd75217709"}, "code_sha256": "ac5a5c867c6e06957bf17079b210532ee34989276edc51ffc1f539f195d895b2", "n_train": 558000, "n_val": 62000, "order_seed": null, "pt_gate_gev": 2.0, "pt_gate_stats": {"n_jets_all_gated": 0, "n_jets_with_newly_gated": 579636, "n_negative_pt": 0, "n_newly_gated_slots": 5323902, "n_padded_slots": 11277563, "n_slots": 39680000, "pt_gate_gev": 2.0, "pt_max": 1559.19091796875, "pt_nonzero_min": 0.25000011920928955}, "sort_stats": {"n_jets": 620000, "n_jets_top_n_reordered": 0, "n_raw_constituents": 150}, "split_seed": 1, "validation_split": 0.1, "y_class_counts": {"train": [112369, 108329, 112438, 112075, 112789], "val": [12479, 11882, 12499, 12579, 12561]}}
NONDEGENERATE_THRESHOLD {"class_counts": [12479, 11882, 12499, 12579, 12561], "n_val": 62000, "p_maj": 0.20288709677419356, "se": 0.0016150697714716518, "se_multiple": 5.0, "val_accuracy_threshold": 0.2109624456315518, "labels_sha256": "e593f51fad6a19e14c1df783ab762ffd5dfd566b6b1df13ba251a41fa1ad7617", "cache": "/data/chang-n64-20260926/n64/data", "split": "validation (gated 90/10)"}
Filesystem                                                                                                                                                      Size  Used Avail Use% Mounted on
csi-cephfs-node@90a5afad-c313-4e49-9b5f-317100c6930e.nautilusfs=/volumes/csi/csi-vol-9f276e98-3be5-415d-b665-c05c6036f24c/a3a2d703-9f9a-423c-a8bc-89c13d677031  100G   33G   68G  33% /data
CACHE_JOB_DONE
```

**[A3]/[A16] check against STUDY expectations, before the pilot pod:**
- Split 558,000 / 62,000: `n_train` 558000, `n_val` 62000 — **matches** STUDY's 90/10 of the
  620,000-jet `train/train` pool exactly.
- `n_negative_pt` = 0 — **matches**.
- Gate applied before standardization — **confirmed from source, not inferred from stats**:
  `prepare_cache.py:119-126` calls `apply_pt_gate` on `x` before `input_std_stats`/
  `apply_input_std` are computed, and `data_info['standardization']` (`:142`) records literally
  `'after the pT gate, train split only'`.
- **260,000 ROC-test jets: this job does not produce or touch that number, and none is expected
  here.** The cache job reads only `raw = /data/hls4ml_lhc_jet/train/train` (62 files, 620,000
  jets total — the `[raw_loaded]` shape confirms it) and the `DATA_INFO` line carries no test
  count. STUDY (l. 389, 795) puts the 260,000-jet ROC-test set on the separate `val/val` pool (26
  files), "touched only after the terminal epoch" — outside this job's scope by design, not a
  gap. Flagging this so it is not later misread as a missing check.
- `pt_gate_stats.pt_nonzero_min` = 0.25 GeV, below the 2.0 GeV gate — **not a gate failure**:
  confirmed from source (`bnhgq2/data.py:35-57`, `apply_pt_gate`), `pt_nonzero_min` is computed
  at line 55 on `pt[nonzero]` (every nonzero-padding raw-pT slot) **before** the `keep` mask is
  applied at line 57 (`return (X * keep[...])`); it is a pre-gate statistic, consistent with
  `n_newly_gated_slots` (5,323,902) also being counted against the pre-gate array ("newly" gated
  only makes sense relative to padding, not the post-gate result). The gate itself (`pt >= 2.0`)
  is applied correctly; this field just describes the input it acted on.
- `pt_gate_stats.n_jets_all_gated` = 0 (no jet lost all its constituents to the gate);
  `sort_stats.n_jets_top_n_reordered` = 0; `y_class_counts` sums to 558,000 (train) and 62,000
  (val) across 5 classes, roughly even (~20% each) — consistent with the non-degenerate threshold
  computed from it (`p_maj` 0.2029). Nothing off found.

**`NONDEGENERATE_THRESHOLD`, recorded before any pilot pod starts (STUDY Selection rule (c),
[A21]):** `p_maj = 0.20288709677419356`, `se = 0.0016150697714716518`, `se_multiple = 5.0`,
**`val_accuracy_threshold = 0.2109624456315518`** (p_maj + 5·SE), computed on the gated
90/10 validation split (`class_counts [12479, 11882, 12499, 12579, 12561]`, `n_val` 62000).

**`df -h /data`** (from the cache job, immediately after cache build): `100G` size, `33G` used,
`68G` avail, `33%` use. This is the baseline for the PVC-headroom check below; the pilot's own
`df -h /data` line (RUN.md) is the next measurement, after six arms' checkpoints exist.

## Packing benchmark

K = 6 arms per pod planned (STUDY §Pods and §canary; rule PACK sizing 2 CPU and 6 Gi per arm,
so 12 CPU / 36 Gi). Measured GPU utilisation (window, mean / median / p10), peak GPU memory per
process, s_e and host RAM: **left for the canary** (RUN.md). If K=6 does not fit in GPU memory
(an arm OOM that its retries cannot clear), STUDY's fallback is the canary again at K=3; that
needs a regenerated pack and job, not an edit.

## Flagged decisions (orchestrator to confirm or overturn)

1. **GPU classes.** STUDY allows A10, L40, 3090, V100-32GB, 2080 Ti. The pilot requires L40, A10,
   RTX-3090 or V100-SXM2-32GB and **leaves out 2080 Ti** (11 GB): K=6 at batch 2,790 on 11 GB
   would test the card, not K=6 (STUDY's own prior: 3 A07 processes at batch 256 used 3,849 MiB,
   activations about 11× at 2,790). STUDY wants the canary "on the GPU class production will use",
   so production must use the same list or the canary is repeated on the added class.
2. **Pilot run root apart from production.** `BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot`, so a
   production Job on another root never resumes a pilot checkpoint silently. STUDY permits resuming
   pilot checkpoints if `config_sha256` and `code_sha256` match; doing so is then an explicit copy.
3. **W&B run id collision. RESOLVED by patch 0026.** The fix is in the pilot bundle, so the
   pilot's `code_sha256` equals production's and STUDY's "pilot checkpoints may resume into
   production" option stays live.
   - The id is keyed by `BNJ_STAGE`. Production manifests must set `BNJ_STAGE=production`,
     because a tracked run without a stage is refused.
   - A production run resumed from a pilot checkpoint opens a new production-stage W&B run.
   - STUDY text amended 2026-09-27 (l. 1473-1480; above).
4. **W&B group. RESOLVED by patch 0026:** the pilot logs into `chang-n64-20260926-canary` as
   STUDY states. Tags unchanged.
5. **GPU classes for production (gate v1 flag 5).** No production manifest exists yet.
   - Rule for its generator: take `GPU_REQUIRED` from `freeze.py` (L40, A10, RTX-3090,
     V100-SXM2-32GB; no A100, no 2080 Ti). These are the four classes the canary runs on.
   - If a class is added, the canary is repeated on it before production uses it.
   - s_e is read on whichever of the four the pilot lands on. RUN.md names the product
     (`nvidia-smi` line in the pod log).
   - **Superseded 2026-09-28 (Kai, decisions.md top entry; gate v3 A1).** Wave 1 and the regime-B
     pilot run on A10 only. `freeze.py` now has `GPU_REQUIRED = ['NVIDIA-A10']` and no preferred
     class, and s_e is read on A10.
6. **Certification device (new; flagged, not resolved here).** The readout Job runs on CPU, as
   briefed. `certify_ebops.py`'s own docstring says to run it on the training GPU class with TF32
   off: a CPU/GPU rounding difference at a power-of-two boundary can move one integer bit of a
   traced range. STUDY l. 1285-1287 makes a mismatch stop production, so a CPU-only readout could
   stop production falsely.
   - Proposed rule for the orchestrator: the certification JSON records the device (`devices`,
     `tf32`). A CPU `EBOPS_MISMATCH` is re-run on the pilot's GPU product (from RUN.md) before it
     counts as a defect.
   - `STORED_MISMATCH` (the file's stored EBOPs against the log) does not depend on the device,
     so it stands either way.
   - This changes what results-analyst may conclude from a CPU mismatch, not the build.

## Open items before launch (cluster-ops)

1. **Done** 2026-09-27 (cluster-ops; record in "ConfigMap create and verify"; confirmed by
   gate v2). Original item, kept for the record: create the **new** ConfigMap: `kubectl create -f campaigns/2026-09-26-training-batch/manifests/configmap.json -n cms-ml`
   (`create`, not `apply`: it is immutable and sha-named). Verify:
   `kubectl get cm kai-chang0926-code-77f1ca4e9f -n cms-ml -o jsonpath='{.binaryData.hgq2\.tar\.gz}' | base64 -d | shasum -a 256`
   = `77f1ca4e9fe3f67ef276ec9b7c401c174812fcb2e88b7ef572040ad2e26f2a94`. This was done for
   c5d6f02a83, which is superseded; leave that ConfigMap in place.
2. W&B: project `BNJetTag-ChangRecipe` exists under `kayamaguchi-uc-san-diego` with access
   `PRIVATE` (the runner queries it and refuses otherwise); the `kai-wandb` secret is current
   (compare sha256 only, never print the key).
3. Cache job: **done** on c5d6f02a (record below). It is not re-applied for 77f1ca4e, because
   the cache stays valid (see Code sha). The original requirement, for the record: its log shows
   `MANIFEST_SHA_OK ac5a5c86...`, `[cache_ready]` or `[cache_verified]`, `BATCH_CACHES_ALL_PASS`,
   `NONDEGENERATE_THRESHOLD {...}`, `CACHE_JOB_DONE`. Record in RUN.md, verbatim, from the
   `DATA_INFO` line: `n_train` 558,000 and `n_val` 62,000; `pt_gate_gev` 2.0,
   `validation_split` 0.1, `split_seed` 1, `order_seed` null; `pt_gate_stats`
   (`n_negative_pt` must be 0; `pt_nonzero_min`, `pt_max`, `n_newly_gated_slots`,
   `n_jets_all_gated`); `sort_stats.n_jets_top_n_reordered`; `y_class_counts`; and the `df -h /data`
   free space (unmeasured so far).
4. The threshold p_maj + 5 SE (`NONDEGENERATE_THRESHOLD`) is recorded **before the pilot pod
   starts** (STUDY Selection rule (c), [A21]); no threshold after any pilot number.
5. Then the pilot: `kubectl apply -f .../manifests/pilot-job.json -n cms-ml` (Job
   `kai-chang0926-pilot-77f1ca`). Confirm `MANIFEST_SHA_OK f7d4003f...`, `GPU_GATE_PASS`, `RUN_STAGE pilot` in each arm log, the GPU product line, six `ARM_STARTED` lines, and in each
   arm log `[train] <name> params=<n> resume_epoch=0` with params equal to the Configs table.
   Stall watchdog: `run_pack.py` kills an arm whose `latest.json` / `activation_widths.jsonl` is
   older than `BNJ_STALL_SECONDS` (1,800 s, counted from process start before the first write).
   If epoch 1 at K=6 and batch 2,790 takes longer than that, `ARM_STALLED_NO_PROGRESS` in the first
   hour with busy `nvidia-smi` lines is the watchdog, not a hang: report s_e and consult before
   changing `BNJ_STALL_SECONDS` (a knob, not set here). Read the canary at epoch 10 against STUDY's stability list
   (finite loss; A and D epoch-10 train loss below epoch 1; β moved from 1e-7; traced EBOPs at
   epoch 10 below epoch 1 for every arm; trace share of s_e); a canary failure means deleting the
   Job, not letting it run to 500.
6. **[A21]:** the code side passed (`I_DECAY_OK` 0.001 on 14 quantizers for A-s1, A-s2, D-s1,
   A07-350-s1, E1-s1; `chang0926-cprime-n64-s1 config None quantizers 0 values []`), on a tree
   byte-identical to the bundle, and again on 77f1ca4e with identical lines. STUDY fix 5 is
   **committed in 1175889** (2026-09-27 10:28:20 PDT), before the build-half commit a1efbe4 at 10:43
   and the shipped-bundle gate at 10:39. `git show HEAD:STUDY.md` l. 394, 1544 and 1713 read "C′
   has no WRAP quantizer, so it carries no key and records an empty set". Kai condition 2 is
   **met**. The in-pod part of [A21] (the threshold from the gated `y_val`, item 4; each run's
   `i_decay_speed.json`; the trace's share of s_e at the canary) is cluster-ops'.
7. Arbiter v5 conditions:
   - Condition 1 is **met**: the arbiter file was committed in 27ffa29 at 10:04:06 PDT, before
     the first pod at 10:47:43 PDT.
   - Condition 3 is **met** well before the epoch-500 readout: fix 4 (A07-350 expectation) is
     **committed in 1175889** (10:28:20 PDT), and HEAD STUDY l. 838, 844 and 1189 carry
     "per-constituent layers".
   - Condition 4: v6 is ITERATE, so wave-1 production stays unlaunched. The pilot is the only
     launch in scope.
8. **Pod logs before the TTL (gate v1 flag 7).** Every Job here has `ttlSecondsAfterFinished
   604800` (7 days). Within 7 days of each Job finishing, RUN.md must copy:
   - from the pilot pod log: `MANIFEST_SHA_OK`, `RUN_STAGE`, the GPU product line,
     `ARM_STARTED`, the canary epoch lines, and `CHECKPOINT_VERIFICATION_PASS` per arm;
   - each arm's `nondegenerate_rule.json`, and the s_e split (`ebops_trace_seconds`,
     `ebops_trace_over_epoch`);
   - from the readout pod log: the certification and `A26_*` lines, and `READOUT_JOB_DONE`.

   Arm logs on the PVC (`pilot/logs/`) outlive the TTL; the pod stdout does not.
9. **Canary read at epoch 10 (gate v1 flag 8).** cluster-ops reads the canary.
   - At the STUDY priors, epoch 10 comes about 30-60 min after the last `ARM_STARTED`.
     cluster-ops checks the pod then, and again every 30 min until all six arms have logged
     epoch 10.
   - The checks are item 5's list.
   - On a failure, cluster-ops deletes the Job and reports; the pod is not left to run on to 500.

## Pilot — NOT applied (cluster-ops, 2026-09-27)

*(ml-engineer, 2026-09-27: this section is for the superseded c5d6f02a pilot manifest; the
current one is `kai-chang0926-pilot-77f1ca`, and its lint is in the Manifests section. The node-pool
facts below do not depend on the bundle.)*

Per instruction, `pilot-job.json` was **not** applied; PREFLIGHT stops here pending the
critical-reviewer PREFLIGHT gate. Its live lint, run today, verbatim, no WARN, unchanged from the
build-half copy above (manifest untouched since generation):

```
$ python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-26-training-batch/manifests/pilot-job.json

== campaigns/2026-09-26-training-batch/manifests/pilot-job.json :: kai-chang0926-pilot-c5d6f0 ==
  note   required pool = 4 products / 109 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 6 arms per pod declared.
  OK

(rules: docs/infrastructure/nrp-nautilus-setup.md -> 'Scheduling, GPU pools and job shape')
exit=0
```

**Node pool check (excludes A100 and 2080 Ti — the manifest requires L40/A10/RTX-3090/
V100-SXM2-32GB and excludes only 3 named hostnames, not a GPU class), read live 2026-09-27
17:48 UTC:**

```
$ kubectl get nodes -l 'nvidia.com/gpu.product in (NVIDIA-L40,NVIDIA-A10,NVIDIA-GeForce-RTX-3090,Tesla-V100-SXM2-32GB)' | wc -l
110
```

110 nodes carry one of the four required products — this is **capacity** (nodes labelled with
that GPU product and allocatable count), not live free-GPU availability: RBAC blocks per-node
`get` (`kubectl get node <name>` → `Forbidden`, cluster-scope), so no cluster-wide free-GPU count
was obtainable; `nrp_doctor.py status` shows no admission errors on our pods and no other jobs of
ours currently pending, which is the closest live signal. Lint's 109 (read an hour earlier) vs
110 now is ordinary drift, not a manifest problem. Of the 110, 2 are cordoned
(`spec.unschedulable: true`, `suncave-0`, `uicnrp-fiona.evl.uic.edu`) — neither is one of the
pilot's excluded hostnames, so this is ordinary pool churn, not a gate concern for a single 1-GPU
pod (K=6 needs only one pod, one GPU). The manifest's own hostname exclusions
(`k8s-chase-ci-07.calit2.optiputer.net`, `nautilus-ext-gpu01.fullerton.edu`,
`ren-gp-argo-01.madren.org`) were checked: the first two are present in the pool with
`status.allocatable.nvidia.com/gpu` 8 and 5 respectively (allocatable, not confirmed free) and
correctly excluded (the second is the 2026-09-17 `KNOWN_BAD_NODES` entry); `ren-gp-argo-01.madren.org`
is `Ready` but does not carry one of the four required GPU products (absent from the
filtered list above), so its exclusion is precautionary and does not narrow the live pool.
`k8s-haosu-15.sdsc.optiputer.net` (cluster-inventory.md 2026-09-26, two unconfirmed sightings,
not promoted to `KNOWN_BAD_NODES`) is likewise **not** in the product-filtered pool today —
cannot land the pilot regardless of promotion status. `a100` quota is 18/24 used but irrelevant:
A100 is excluded by the manifest, not requested. **A single 1-GPU pod against 110 nodes'
worth of capacity in the required classes is not expected to be a scheduling problem; this is
a capacity read, not a proven-available-right-now read** — if the pilot pod goes `Pending`,
read its `PodScheduled` condition per protocol rather than assuming this check covered it.

**PVC headroom for pilot checkpoints (cadence 25 epochs, [A15]: full optimizer checkpoint every
25 epochs, per-epoch lightweight candidate save unchanged):** no measured per-checkpoint byte
size exists anywhere in the repo's evidence (`active-checkpoints-0924.json` and similar record
only metrics, not file sizes) — **not estimating one from parameter counts** (advisor flagged
this as a guess to avoid). The only real measurement available is the cache job's baseline
`df -h /data`: **100G total, 33G used, 68G avail (33%)**, taken *before* any pilot checkpoint
exists. This is unmeasured headroom for six arms' checkpoints, not a computed answer — the first
real number is the pilot's own `df -h /data` pre-training check (in its startup log) and its
value after the first 25-epoch cadence point, both of which belong in RUN.md. 68G avail against
six ~32K-95K-parameter models (Configs table above) is not expected to be tight, but this is a
qualitative read, not a headroom check — flagging it as **unmeasured, first number from the
pilot's own df**, per the open item, rather than clearing it.

**Nothing here blocks the gate on cluster grounds:** ConfigMap, W&B project/secret and cache job
all pass; the node pool has capacity; the only open item is the PVC-headroom number, which is
by design deferred to the pilot's own log (not a blocker, a pending measurement). ~~The remaining
blockers on the list are non-cluster: STUDY.md fix-5 commit ([A21], orchestrator's), the fix-4
wording commit before epoch-500 (STUDY l. 755-761, orchestrator's), and the critical-reviewer
PREFLIGHT gate itself, which this document is being submitted to.~~ *(Correction, ml-engineer
2026-09-27, gate v1 flag 2: fixes 4 and 5 were already committed in 1175889 at 10:28:20 PDT,
before this section was written; see open items 6-7. The PREFLIGHT gate remains open, and the
ConfigMap and pilot manifest named here are superseded by 77f1ca4e.)*

## Regime B addendum (ml-engineer, 2026-09-27 PDT / 2026-09-28 UTC)

Scope: Kai's [D15] decision (`.claude/memory/decisions.md`, entry "Kai, [D15] branch after the
canary") and the STUDY regime-B amendment at 96b95f2. This adds regime-B builds; it does not
change anything the running regime-A pilot `kai-chang0926-pilot-77f1ca` uses (ConfigMap
`kai-chang0926-code-77f1ca4e9f`, `pilot-job.json`, `readout-job.json`, `cache-job.json`: untouched).
Nothing was applied to the cluster. Everything below is CPU on a laptop with synthetic inputs,
so none of it is a result.

### PREFLIGHT gate v3 fixes (ml-engineer, 2026-09-28; bundle unchanged; nothing applied)

Sources: `review/PREFLIGHT_critical_v3.md` (ITERATE; A1, A2, B flags 3-8); Kai's answer, the top
entry of `.claude/memory/decisions.md` (A10 only; launch after scoped fixes); the Delta
`campaigns/2026-09-27-delta-screen/REGRESSION_TICKET.md` §3 item 2 (GPU fingerprint gate).
Bundle 42abed4b, manifest 041f981a and ConfigMap `kai-chang0926-code-42abed4b5d` are **not**
re-frozen. `python3 manifests/freeze.py --jobs-only` (new mode) re-derives the manifest sha,
rebuilds the tarball in memory and asserts that it and the tarball on disk are both 42abed4b…. It
writes no tarball, `configmap*.json` or `bundle-manifest*.json`, only the Jobs and the fingerprint
ConfigMap below. Its output:
```
BUNDLE_SHA256 42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0 (unchanged, not rewritten)
MANIFEST_SHA256 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42
CONFIGMAP kai-chang0926-code-42abed4b5d (unchanged)
FINGERPRINT_CONFIGMAP kai-chang0926-fp-e9511d1aeb sha256 e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1
PILOT_B_BAD_NODES hcc-nrp-shor-c6017.unl.edu k8s-chase-ci-07.calit2.optiputer.net nautilus-ext-gpu01.fullerton.edu ren-gp-argo-01.madren.org
```
`readout-a-job.json` and `cache-job.json` are not regenerated. A regeneration of readout-a in
memory is byte-identical to the file on disk (`READOUT_A_IDENTICAL True`), so its dry-run evidence
still holds.

**A1: GPU class.** Both pilot-b Jobs have one required term: `nvidia.com/gpu.product In
[NVIDIA-A10]`, plus `kubernetes.io/hostname NotIn` the four hosts above. There is no
`preferredDuringSchedulingIgnoredDuringExecution` key (`grep -c` = 0 in both files). The host list
is the old three, `hcc-nrp-shor-c6017.unl.edu` (Delta REGRESSION_TICKET), and every host in
`nrp-lab/nrp_doctor.py` `KNOWN_BAD_NODES`, which `freeze.py` reads from that file (today only
`nautilus-ext-gpu01.fullerton.edu`, already in the list). Lint reports `required pool = 1 products /
35 nodes cluster-wide` (A10 nodes, live read, 2026-09-28). The readout-b Jobs (CPU) take the same
exclusion list. `freeze.py` `GPU_REQUIRED` is now `['NVIDIA-A10']`, so a production generator that
follows flagged decision 5 also gets A10. Kai's 2026-09-27 wave-1 decision says the same.

**GPU fingerprint gate (Delta gate 15, reused as is).** This is Delta's
`campaigns/2026-09-26-delta/code/fingerprint_check.py` (committed at 2d86bc9), copied
byte-identical to `manifests/fingerprint/fingerprint_check.py`, sha256
`e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1`. It fits without a change: its
reference table already holds `chang0926-a-n64-s1`, and it falls back to `ablation.optimizer_for`
on the pre-Delta anchor tree. It ships as its own immutable ConfigMap, `kai-chang0926-fp-e9511d1aeb`
(`manifests/configmap-fp-e9511d1a.json`, key `fingerprint_check.py`), mounted read-only at `/cmfp`
beside the bundle. The bundle is not touched. In each of the eight pilot-b GPU Jobs (K=5, K=3 and
the six fallbacks), after `MANIFEST_SHA_OK`, `GPU_GATE_PASS` and the `READY.json` check, and
before `run_pack.py`, the script runs:
```
echo 'e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1  /cmfp/fingerprint_check.py' | sha256sum -c -
python -u /cmfp/fingerprint_check.py --run chang0926-a-n64-s1 --expect 11559681 --data-root /data/chang-n64-20260926 --campaign-dir /work/code/campaigns/chang0926 --env-report || FP=$?
if [ "$FP" != 0 ]; then echo "FINGERPRINT_GATE_FAIL exit=$FP node=${NODE_NAME:-na}; no arm started"; exit "$FP"; fi
```
The script builds anchor arm A s1 from the extracted 42abed4b tree (`PYTHONPATH=/work/code`), with
the same call sequence as `ablation.run_training`, and runs the pre-training `initial_ebops` trace
(full train split, batch 2,048). On a mismatch it prints `GPU_FINGERPRINT_MISMATCH <value>` and
exits 9; with no GPU it exits 8. No arm starts in either case. `--env-report` logs the driver, the
GPU, the TF build and `pip freeze`. `NODE_NAME` comes from the downward API (`spec.nodeName`). A
fingerprint failure counts against `backoffLimitPerIndex: 2`, so a replacement pod may land on
another A10. cluster-ops reads the node from `ENV_REPORT` and adds it to the exclusion list if the
failure repeats there.

**Expected integer, checked on CPU against 42abed4b by this owner:**
- `code/evidence/fingerprint_cpu_42abed4b.log` (cwd on line 2). Setup:
  - the script ran from `manifests/fingerprint/`, with `PYTHONPATH` set to a fresh extraction of
    `manifests/chang0926-code.tar.gz` (sha256 42abed4b…);
  - the pinned CPU env was `campaigns/2026-09-26-delta/code/tests_patches/pyenv.sh`;
  - the anchor cache was rebuilt locally from the 62 raw train files with that tree's
    `prepare_cache.py` and `cache_configs/n64.json`. x_train sha256 is `420ac79d…`, the value
    recorded for the PVC cache `/data/chang-n64-20260926`.

  Output lines:
  ```
  FINGERPRINT 11559681 expected 11559681 chang0926-a-n64-s1
  FINGERPRINT_OK chang0926-a-n64-s1
  FINGERPRINT 11295521 expected 11295521 chang0926-a-n64-s2
  FINGERPRINT_OK chang0926-a-n64-s2
  GPU_FINGERPRINT_MISMATCH 11559681        (--expect 1: exit 9)
  GPU_FINGERPRINT_NO_GPU                   (no --allow-cpu, CPU-only: exit 8)
  ```
- The expected integer is **11,559,681**. It equals the ticket's value for anchor A-s1 on
  77f1ca4e / GPU c5825, and it is what the Jobs pass as `--expect`. It is a check integer, not a
  result.

**Epoch-0 divergence of a whole pack is a pod-level failure (wrapper only; no bundle change).**
After `run_pack.py` returns, the wrapper reads every arm's `DIVERGED.json` in the pack. It prints
`PACK_EPOCH0_CHECK <run>=<divergence_epoch_zero_based|None> …`. If every arm diverged at zero-based
epoch 0, it prints `POD_EPOCH0_ALL_DIVERGED node=… run_pack_exit=…` and exits 10. A new
`podFailurePolicy` rule, `onExitCodes In [10] → FailJob`, placed after the DisruptionTarget
`Ignore` rule, stops the Job. Without it a replacement pod would skip every arm (`DIVERGED.json`
is terminal) and complete "successfully". Otherwise the wrapper exits with `run_pack`'s own code.
`run_pack.py` itself still treats the K divergences as K outcomes (production item P4 below).

**Shell test of the wrapper** (the Jobs' scripts verbatim from `GPU_GATE_PASS` on, with stub
`python`/`nvidia-smi`; `code/evidence/wrapper_gate_v3_test.{py,log}`; not a result):
- fingerprint exit 9 → exit 9, `run_pack` not called;
- 5/5 arms diverged at epoch 0 → exit 10;
- 4/5 at epoch 0 → exit 0;
- 5/5 diverged at epoch 3 → exit 0;
- `run_pack` exit 1 → exit 1;
- a tampered `/cmfp` file → `sha256sum -c` FAILED, `run_pack` not called;
- the fallback guards below.

It ends `WRAP_TESTS_ALL_PASS`.

**A2: epoch-10/20 RSS stop rule (cluster-ops reads it; RUN.md gets it at launch).**
- **Formula, per arm:** stop the pod if `rss20 + (rss20 − rss10) / 10 × 85 > 8,192` MiB (was 6,144;
  8 GiB per-arm resize, 2026-09-28, see 'Per-arm memory 8 GiB' below).
  - `rssN` is the `host_rss_mb=` field (MiB, `VmRSS` of the arm process) on the N-th `[epoch` line
    of that arm's **current process**, counted after the last `==== ARM_ATTEMPT` header in its log.
  - The projection reaches process epoch 105, where the in-code RSS gate gives its verdict. It does
    not project to 7,000: projected that far, the healthy post-fix CPU series reaches 102,878 MB
    (gate v3 recomputation).
  - The stop threshold is Δ(10→20) above about 631-641 MiB at rss10 of 2.1-2.2 GB
    (rss10 + 9.5 Δ > 8,192). The incident's rate (about 900 MB per 10 epochs) trips it. A post-fix
    CPU-sized Δ of 145 MB passes.
- **Who and when:** cluster-ops, at process epochs 10 and 20 of each arm.
  - That is about 25 and 50 min after the arm's `ARM_STARTED`, at the canary's roughly 150 s/epoch.
    Add about 2 min for the fingerprint gate before the first `ARM_STARTED`.
  - The verdict needs the epoch-20 line.
  - A replacement or relaunched process starts its own count.
- **Commands** (from the repo root; `$J` is `kai-chang0926-pilotb5-42abed` or `-pilotb3-42abed`; the
  first line picks the newest pod, and its jsonpath form was checked read-only against `cms-ml`):
  ```
  POD=$(kubectl -n cms-ml get pods -l job-name=$J --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1:].metadata.name}')
  kubectl -n cms-ml logs $POD | grep -E 'FINGERPRINT|ARM_STARTED|ARM_EXIT'
  for RUN in $(kubectl -n cms-ml logs $POD | awk '/^ARM_STARTED/{print $3}' | sort -u); do
    kubectl -n cms-ml exec $POD -c train -- cat /data/chang-n64-20260926/pilot-b/logs/$RUN-$POD.log \
      | awk -v arm=$RUN -f campaigns/2026-09-26-training-batch/manifests/rss_rule_epoch10_20.awk
  done
  kubectl -n cms-ml logs $POD | grep '^POD_MEM' | tail -3
  kubectl -n cms-ml exec $POD -c train -- nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader
  ```
  - Each arm prints one line, `RSS_RULE <run> OK|STOP|PENDING|UNREADABLE rss10 … rss20 …
    projection_mib … limit_mib 8192`, and exits 1 on STOP or UNREADABLE.
  - If `host_rss_mb` is `na`, apply the same formula to the arm's `rss_mib=` in two `POD_MEM` lines
    about 10 epochs apart. If both are unreadable, count the arm as STOP (STUDY's canary convention).
- **Stop action:** `kubectl -n cms-ml delete job $J`. Delete the Job, not the pod; otherwise
  `backoffLimitPerIndex: 2` re-creates the pod. Record the stop in RUN.md and
  `cluster-inventory.md`.
- The same read supplies gate v3 flag 5's per-process GPU peak under regime B
  (`--query-compute-apps`, recorded in RUN.md).
- **awk check at 8,192** (re-run 2026-09-28; synthetic logs with rss10 = 2,150; macOS `/usr/bin/awk`,
  POSIX like the pod's `mawk`; `code/evidence/rss_rules_8192_test.{py,log}`; not a result):
  - Δ 145 → OK, 3,528; Δ 470 → OK, 6,615; Δ 630 → OK, 8,135;
  - Δ 650 → STOP, 8,325; Δ 900 → STOP, 10,700;
  - a second `ARM_ATTEMPT` resets the count → OK, 3,528;
  - 12 epochs → PENDING; `na` → UNREADABLE, exit 1.
  - The four healthy Delta canary v2 GPU arm logs (telemetry) → OK, 2,490-2,654.
  - The 6,144 run (Δ 470 → STOP, 6,465 and the rest) is superseded.

**B, flag 5: K=5 VRAM fits, by measurement.**
- The exact K=5 set (A-s1, A-s2, D-s1, E1-s1, C′-s1) was co-resident on an A10 in the regime-A
  pilot, with a pod peak of **21,094 MiB of 23,028 MiB** (RUN.md l. 212-217).
- Per process (`--query-compute-apps`): A-s1, A-s2 and D-s1 at 4,354 each; E1-s1 at 2,830; C′-s1
  at 5,172 (third attempt). The margin is 1,934 MiB.
- Regime B adds no GPU allocation.
- Caveats: C′'s figure comes from its third attempt, and no peak after about epoch 10 was observed.
  The `--query-compute-apps` read above re-measures it under regime B.

**B, flag 4: registered fallback for an OOM in the K=3 pod** (A07-350-s1, C-s1, F-s1; the two A07
[D19] builds have no measured per-process GPU figure).
- **Trigger:** an arm of `kai-chang0926-pilotb3-42abed` ends `ARM_FAILED_AFTER_RETRIES` with a CUDA
  or TF `ResourceExhausted`/OOM in its `ARM_LOG` tail. An allocator OOM is not exit 3 or 5, so
  `run_pack` first retries it twice in the pod.
- **Action:** at the first `ARM_FAILED_AFTER_RETRIES` with an OOM tail, delete the K=3 Job:
  `kubectl -n cms-ml delete job kai-chang0926-pilotb3-42abed`.
  - Do not wait for the other two arms to pause. There is no safe window: `run_pack` exits 1 within
    one 5 s poll of the last arm's exit, and `backoffLimitPerIndex: 2` with `podReplacementPolicy:
    Failed` re-creates the pod at once, which relaunches the OOM'd arm beside the others.
  - The two surviving arms are stopped mid-run. Each resumes from its own last checkpoint (every 25
    epochs), so at most 24 epochs are redone.
- **Then apply one OOM'd-arm Job and one survivors' Job** (every file is linted, none applied):

  | OOM'd arm | OOM'd arm alone (K=1; 2 CPU / 8 Gi) | survivors together (K=2; 4 CPU / 16 Gi) |
  |---|---|---|
  | A07-350-s1 (48) | `pilot-b-fb48-job.json` (`kai-chang0926-pilotbfb48-42abed`) | `pilot-b-fb16-32-job.json` (C-s1 + F-s1) |
  | C-s1 (16) | `pilot-b-fb16-job.json` | `pilot-b-fb48-32-job.json` (A07-350-s1 + F-s1) |
  | F-s1 (32) | `pilot-b-fb32-job.json` | `pilot-b-fb48-16-job.json` (A07-350-s1 + C-s1) |

  - If two arms OOM'd, run each alone (two K=1 Jobs) and the third alone as well.
  - The K=1 Jobs carry `bnjettag.io/single-arm-justified`.
  - Any other split: add the index list to `FALLBACKS` in `freeze.py` (the indices must be in the K=3
    pack), run `python3 manifests/freeze.py --jobs-only`, then lint.
- **Same bundle, run root and stage:**
  - ConfigMap `kai-chang0926-code-42abed4b5d`, `BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot-b`,
    `BNJ_STAGE=pilot-b`, the RSS gate env, A10 only, c6017 excluded, and the fingerprint gate.
  - The pack is written inline to `/work/fallback_packs.json`. `run_pack` reads
    `CAMPAIGN / <absolute path>`, which resolves to that path, so no bundle change is needed.
  - The arm resumes from its own last checkpoint. The code sha is unchanged, so
    `restore_checkpoint` accepts it.
- **Guards in the fallback script, before the fingerprint gate:**
  - `ARM_STILL_LIVE <run>`, exit 1, if the arm's `latest.json` or `activation_widths.jsonl` changed
    in the last 15 min (the K=3 Job was not deleted).
  - `ARM_NO_CHECKPOINT <run>`, exit 1, if the arm has history but no `latest.json`. An arm that
    OOM'd before its first checkpoint (epoch 25) would otherwise raise at `ablation.py:710`.
    cluster-ops then renames `runs/<run>` aside (never deletes it) and re-applies. The W&B id is
    deterministic, so the fresh start logs into the same W&B run from step 1; RUN.md notes this.
- **Record** the fallback pod's per-process GPU peak (`--query-compute-apps`) in RUN.md. It is the
  A07 figure the K=4 production packing still lacks (plan.md R-B3).
- Lint below. Not applied.

**B, flag 6: the readout-b Jobs no longer halt on a missing arm (wrapper only; no bundle change).**
- For each run of its pod, `readout-b5` and `readout-b3` count the arm if it has
  `snapshots/epoch-0500/state.json` or `DIVERGED.json`, as before.
- Otherwise the Job prints `READOUT_MISSING <run> RSS_GATE_FAIL|NO_TERMINAL_MARKER` and leaves the
  run out of `certify_ebops.py --only` and `attn_entropy.py --indices`.
- It stops only if no arm has a snapshot (`READOUT_NOTHING_PRESENT`, exit 1).
- A partial readout writes to `…/readout-epoch-0500-42abed-b{5,3}-partial-<UTC time>`, so a later
  full readout does not hit `attn_entropy`'s no-overwrite guard. A full readout keeps the old
  directory name.
- The last line is `READOUT_JOB_DONE certify_exit=… a26_exit=… missing=…`.
- `readout-a` (77f1ca4e) is unchanged.
- Dry runs on the 42abed4b tarball, with the same builder and runner as below:
  - The layout was rebuilt with `dry_readout_build.py` on the 42abed4b and 77f1ca4e extractions,
    and each case ran through `dry_readout_run.py`. The case script is
    `code/evidence/dry_readout_gatev3_cases.sh`. CPU, synthetic, not results.
  - **b5, full** (`dry_readout_b5_gatev3.log`):
    `READOUT_ARMS … missing= none`, `CERTIFICATION_ALL_PASS 6 0`, `A26_DONE`,
    `READOUT_JOB_DONE certify_exit=0 a26_exit=0 missing= none`,
    `DRY_RUN_EXIT kai-chang0926-readoutb5-42abed 0`.
  - **b3, negative path on 42abed4b** (`dry_readout_b3_gatev3_mismatch.log`; F-s1 planted at
    logged = traced + 1,000 by the builder). This closes gate v3's note that the mismatch path had
    only run on f2107a04:
    `EBOPS_MISMATCH chang0926-f-n64-s1 snapshot500_primary 10429606 10428606`,
    `CERTIFICATION_FAIL 3 1`, `READOUT_JOB_DONE certify_exit=4 a26_exit=0 missing= none`,
    `DRY_RUN_EXIT kai-chang0926-readoutb3-42abed 1`.
  - **b5, partial** (`dry_readout_b5_gatev3_partial.log`). E1-s1's epoch-500 snapshot was moved
    aside and `RSS_GATE_FAIL.json` planted; D-s1's snapshot was moved aside with no marker:
    `READOUT_MISSING chang0926-d-n64-s1 NO_TERMINAL_MARKER`,
    `READOUT_MISSING chang0926-e1-n64-s1 RSS_GATE_FAIL`,
    `READOUT_ARMS only=chang0926-a-n64-s1,chang0926-a-n64-s2,chang0926-cprime-n64-s1 indices= 0 1 56`,
    `CERTIFICATION_ALL_PASS 4 0`, `A26_DONE`, output in `readout-epoch-0500-42abed-b5-partial-<UTC>`,
    `READOUT_JOB_DONE certify_exit=0 a26_exit=0 missing= chang0926-d-n64-s1 chang0926-e1-n64-s1`,
    `DRY_RUN_EXIT … 0`.
  - **b5, nothing present** (`dry_readout_b5_gatev3_none.log`): five `READOUT_MISSING` lines,
    `READOUT_NOTHING_PRESENT`, `DRY_RUN_EXIT … 1`.

**Production items (open; they do not block the pilot; each needs a bundle change or a decision):**
- **P1 (gate v3 flag 3).** A gate-failed arm is re-run in a re-created pod.
  - `backoffLimitPerIndex: 2` with `podReplacementPolicy: Failed` re-creates a pod whose `run_pack`
    exited 1. That includes a pod where an arm hit `RSS_GATE_FAIL`.
  - In the new pod, `run_pack.py` skips only `DIVERGED.json` and `VERIFIED_COMPLETE.json` (l. 184
    of the 42abed4b tree, the `marker = next(...)` line in `main()`). `RSS_GATE_FAIL.json` is not
    skipped, so a gate-failed arm resumes from its last checkpoint, restarts the window and runs
    about 105 more epochs, up to twice.
  - The same holds for `ARM_FAILED_AFTER_POD_STALLS` and `ARM_FAILED_AFTER_RETRIES`.
  - Cost: GPU hours. No wrong number results.
  - Fix in the next bundle: add `RSS_GATE_FAIL.json` to the skip list. For the pilot, cluster-ops
    deletes the Job after the first `ARM_MEMORY_GATE_FAILED` once the other arms have paused.
- **P2 (gate v3 flag 7).** An automatic per-epoch stop at RSS > 0.9 × the per-arm limit (plan.md
  l. 1125) is **not built**.
  - The pilot relies on the epoch-10/20 read above; thirteen unattended production pods cannot.
  - Building it needs a new bundle, which breaks pilot→production resume, so decide before pilot-b
    launches if resume is wanted.
- **P3 (R-B8, open).** Gate the production arms with the same RSS gate, or trust the pilot-b
  slopes; the orchestrator decides. Related: a production process resumed with fewer than 105
  epochs left never gets a verdict.
- **P4 (Delta ticket §3 item 2, second half).** `run_pack` in the bundle should treat a pack-wide
  epoch-0 divergence as a pod failure (`PHASE_EXIT_NONZERO`), not as K recorded divergences. For
  the pilot, the wrapper check above covers it.
- **P5.** The cross-class resume rule (v2 flag 4) is retired for the pilot by the A10 pin. It stays
  open for production if a class other than A10 is ever added.

**Lint** (`python3 nrp-lab/nrp_doctor.py lint`, ml-engineer, local, live cluster read; exit 0 each):
```
== campaigns/2026-09-26-training-batch/manifests/pilot-b-k5-job.json :: kai-chang0926-pilotb5-42abed ==
  note   required pool = 1 products / 35 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 5 arms per pod declared.
  OK
exit=0
== campaigns/2026-09-26-training-batch/manifests/pilot-b-k3-job.json :: kai-chang0926-pilotb3-42abed ==
  note   required pool = 1 products / 35 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 3 arms per pod declared.
  OK
exit=0
== campaigns/2026-09-26-training-batch/manifests/pilot-b-fb48-job.json :: kai-chang0926-pilotbfb48-42abed ==
  note   required pool = 1 products / 35 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  OK
exit=0
== campaigns/2026-09-26-training-batch/manifests/pilot-b-fb48-16-job.json :: kai-chang0926-pilotbfb48-16-42abed ==
  note   required pool = 1 products / 35 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 2 arms per pod declared.
  OK
exit=0
== campaigns/2026-09-26-training-batch/manifests/readout-b5-job.json :: kai-chang0926-readoutb5-42abed ==
  note   no required GPU product list — widest possible pool (good)
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  OK
exit=0
== campaigns/2026-09-26-training-batch/manifests/readout-b3-job.json :: kai-chang0926-readoutb3-42abed ==
  note   no required GPU product list — widest possible pool (good)
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  OK
exit=0
```
Added after the fallback table was completed (same run, same live read):
```
== campaigns/2026-09-26-training-batch/manifests/pilot-b-fb16-job.json :: kai-chang0926-pilotbfb16-42abed ==
  note   required pool = 1 products / 35 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  OK
exit=0
== campaigns/2026-09-26-training-batch/manifests/pilot-b-fb32-job.json :: kai-chang0926-pilotbfb32-42abed ==
  note   required pool = 1 products / 35 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  OK
exit=0
== campaigns/2026-09-26-training-batch/manifests/pilot-b-fb16-32-job.json :: kai-chang0926-pilotbfb16-32-42abed ==
  note   required pool = 1 products / 35 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 2 arms per pod declared.
  OK
exit=0
== campaigns/2026-09-26-training-batch/manifests/pilot-b-fb48-32-job.json :: kai-chang0926-pilotbfb48-32-42abed ==
  note   required pool = 1 products / 35 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 2 arms per pod declared.
  OK
exit=0
```
The fingerprint ConfigMap is not a Job; lint prints `no Job manifest found` and exits 0.
`bash -n` passes on all ten embedded scripts. `freeze.py --jobs-only` run a second time rewrote
every file byte-identically (`shasum` of `manifests/*.json` and `fingerprint/*` unchanged:
`IDEMPOTENT`). `git diff` is empty for the tarball, `configmap.json`, `configmap-42abed4b.json`,
`bundle-manifest{,-42abed4b}.json`, `readout-a-job.json` and `cache-job.json`.
`bundle-manifest.json` / `bundle-manifest-42abed4b.json` are left stale on purpose (no re-freeze).
Their `jobs` field lists the four pilot-b/readout-b Jobs of 3dabcd2 and does not list the fallback
Jobs or the fingerprint ConfigMap. The Job names themselves are unchanged.

**For cluster-ops (placeholders; not filled by the ml-engineer):**
- [x] Create `manifests/configmap-fp-e9511d1a.json` in `cms-ml`, then read back `immutable: true`
  and the sha256 of `data['fingerprint_check.py']` (must be e9511d1a…):
  **[cluster-ops] 2026-09-28:** created in cms-ml; read-back `immutable=true`; decoded
  `fingerprint_check.py` sha256 e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1 (exact).
  `kai-chang0926-code-42abed4b5d` confirmed present and unchanged. (Recorded by the orchestrator from
  the cluster-ops report.)
- The fingerprint ConfigMap must exist **before** any pilot-b or fallback Job is applied;
  otherwise the pod stays in `ContainerCreating` on the missing `/cmfp` volume.
- [x] Live `nrp_doctor.py lint` of the Jobs, 2026-09-28 (before apply): OK / exit 0 on all 10
  (pilot-b-k5, pilot-b-k3, readout-b5, readout-b3, six pilot-b-fb*), required pool "1 products /
  35 nodes"; output in `review/PREFLIGHT_validators_v4.txt`. All 8 pilot-b GPU Jobs verified to require
  NVIDIA-A10 only, exclude hcc-nrp-shor-c6017 and the KNOWN_BAD_NODES hosts, mount both ConfigMaps,
  and run the fingerprint gate before run_pack. A10 capacity read: 35 nodes, 279 GPUs (capacity, not
  free). The hook re-lints at apply time.
- [ ] At launch, copy the A2 rule and commands into RUN.md.

**Files this fix touched** (uncommitted at write time; none is in the bundle):
- modified: `manifests/freeze.py`, `pilot-b-k5-job.json`, `pilot-b-k3-job.json`,
  `readout-b5-job.json`, `readout-b3-job.json`, and this file;
- new: `manifests/fingerprint/fingerprint_check.py`, `manifests/configmap-fp-e9511d1a.json`,
  the six `manifests/pilot-b-fb{48,16,32,16-32,48-16,48-32}-job.json`,
  `manifests/rss_rule_epoch10_20.awk`, `code/evidence/fingerprint_cpu_42abed4b.log`,
  `wrapper_gate_v3_test.{py,log}`, `dry_readout_*gatev3*.log` and `dry_readout_gatev3_cases.sh`;
- `plan.md` also has an uncommitted change, which did not come from this fix.

### Per-arm memory 8 GiB (ml-engineer, 2026-09-28; bundle 42abed4b unchanged; nothing applied)

Coordinator brief, 2026-09-28; decision in `.claude/memory/decisions.md` (2026-09-28, top entry).
The 6,144 MiB per-arm limit came from rule PACK's "about 6 Gi per arm" guidance, not from a
measurement. The limit is resized; the gate's form, window and exit code are unchanged.

- **GPU telemetry behind it** (not a result; Delta's patches sit on top of 42abed4b, so this is not
  this bundle's measurement): Delta canary v2, phase E-k4 (arm A, E at 350k), K=4 on an A10,
  epochs 99-100, no non-finite loss (`campaigns/2026-09-27-delta-screen/RUN.md`, entry "canary v2
  stopped to yield", commit a3a3362; arm logs `logs/canary-v2-E-k4-s{1..4}.log`).
  - Delta's record: slope 0.49 / 0.63 / 0.45 / 0.45 MB/epoch over epochs 5-100, host RSS
    2,288-2,303 → 2,409-2,428 MB, GPU peak 17,425 / 23,028 MiB, median 104.3-104.5 s/epoch.
    Delta's own gate projected to its H = 1,000, not 7,000.
  - The in-code gate form recomputed on those logs (least squares over list indices 5 to 98-99,
    which is short of the 5-104 window; `code/evidence/rss_rules_8192_test.log`): slope
    0.475 / 0.606 / 0.432 / 0.420 MB/epoch, fitted baseline 2,374-2,389 MB, projection at 7,000
    of 5,712 / 6,615 / 5,398 / 5,329 MB. Arm s2 would **FAIL at 6,144** and passes at 8,192.
    All four pass at 8,192.
  - At 8 GiB and a 2.1-2.2 GB baseline the gate admits a slope of about 0.85-0.87 MB/epoch (was
    about 0.55).
- **Manifests** (`python3 manifests/freeze.py --jobs-only`; it asserts bundle 42abed4b on disk and
  on rebuild, and manifest 041f981a…):
  - `PER_ARM_MEMORY_GI = 8`, so `RSS_GATE_LIMIT_MB = 8192`. The generator adds no overhead: pod
    memory is exactly K × 8 Gi, request = limit.
  - Sizes: `pilot-b-k5` 40Gi, `pilot-b-k3` 24Gi, `pilot-b-fb48/fb16/fb32` 8Gi each,
    `pilot-b-fb16-32/fb48-16/fb48-32` 16Gi each.
  - All eight scripts export `BNJ_RSS_GATE_LIMIT_MB=8192 BNJ_RSS_GATE_WINDOW=5:105`.
  - The two annotations `per-arm-memory` and `rss-gate` now say 8Gi and 8192.
  - Otherwise unchanged: A10-only affinity, the `NotIn` list (c6017 and the KNOWN_BAD_NODES hosts),
    the fingerprint gate before `run_pack`, Job names, bundle, ConfigMaps, run root and stage.
  - `readout-b{5,3}-job.json` and `configmap-fp-e9511d1a.json` are regenerated byte-identical.
  - K=5 at 40 Gi is 4 Gi more than the regime-A K=6 pod (36 Gi), which did schedule.
- **Lint** (`code/evidence/lint_42abed4b_8gib.log`): `nrp_doctor.py lint` rc=0 and `OK` on all eight
  `pilot-b-*-job.json` (PACK 5, 3 and 2 arms declared, K=1 justified); `bash -n` passes on all eight
  scripts. The hook re-lints at apply time.
- **Resume is unaffected: neither the gate limit nor pod memory enters a sha.** Bundle 42abed4b line numbers:
  - `bnhgq2/ablation.py:35-36`: `digest_json(value)` = sha256 of `json.dumps(value, sort_keys=True)`.
  - `ablation.py:296-298`: the resume asserts compare `state['config_sha256']` with `digest_json(cfg)`,
    `state['data_sha256']` with `digest_json(dataset_info)`, and `state['code_sha256']` with env
    `BNHGQ2_CODE_SHA256`. `:716-717` writes the same three at the first start.
  - `cfg` is the config file, `json.loads((CAMPAIGN / 'configs' / row['file']).read_text())`
    (`run_study.py:102`). `dataset_info` is the cache's `data_info.json` (`run_engram.py:182`).
  - `BNHGQ2_CODE_SHA256` is `run_study.manifest()['sha256']` (`run_study.py:117-118`, re-asserted
    against the saved `source_manifest.json` at `:119-120`). `manifest()` hashes the top-level and
    `bnhgq2/` `*.py` files and six package versions (`run_study.py:26-32`), and nothing else.
  - The gate reads `BNJ_RSS_GATE_LIMIT_MB` and `BNJ_RSS_GATE_WINDOW` from the env only
    (`ablation.py:645`, `:648`). Its state (`limit_mb`, the RSS series) lives in the local
    `rss_gate` (`:765`). It goes only to stdout, the epoch line (`:938-940`), and
    `RSS_GATE_FAIL.json` (`:675-677`), never into `state`, `state.json` or a checkpoint.
  - Pod memory is a Kubernetes resource and is not read by the code.
  - So a Job re-applied with the 8 GiB manifest on the same run root passes all three resume asserts.
    It resumes from the last 25-epoch checkpoint, and the gate window restarts in the new process.
- **A2 rule** now at 8,192 (above), re-tested. The epoch-20 terminal-projection read for pods
  already running on the 6 GiB manifests is in RUN.md, 'Regime-B pilot: operating rules'
  (`manifests/rss_proj7000_epoch20.awk`, tested in the same log).
- Files: `manifests/freeze.py`, the eight `manifests/pilot-b-*-job.json`,
  `manifests/rss_rule_epoch10_20.awk`, new `manifests/rss_proj7000_epoch20.awk`, new
  `code/evidence/rss_rules_8192_test.{py,log}` and `lint_42abed4b_8gib.log`, this file, RUN.md,
  STUDY.md and `.claude/memory/decisions.md`. All uncommitted. No bundle file changed.

### Current freeze: 42abed4b (stall-incident fixes). f2107a04 and ceb174db are superseded before any pod.

The regime-A pilot was stopped at 05:31Z on 2026-09-28 (Kai), after the stall in
`review/INCIDENT_stall_20260928.md`. Its checkpoints on the PVC are A-s1 and A-s2 at epoch-0125,
D-s1 at 0150, E1-s1 at 0075 and C′-s1 at 0025, with **no epoch-500 snapshot**. So
`readout-a-job.json` is not time-critical: it would stop at `SNAPSHOTS_NOT_READY` today. Its dry
run (below) is kept for whenever those runs reach epoch 500 on 77f1ca4e.
The coordinator ruled that the leak fix blocks the regime-B freeze. The bundle was re-frozen on
2026-09-28 with two more patches:

- **0030 `run_pack.py`.**
  - The heartbeat age is now `now - max(latest.json and activation_widths.jsonl mtimes, this
    attempt's wall-clock start)`, so a relaunch never inherits stale mtimes (E1 was killed 5 s
    and 20 s after launch).
  - A pod-wide stall is logged as `POD_STALL`. It means at least 2 live arms and at least half of
    them past `BNJ_STALL_SECONDS` in one sweep. Those arms are stopped together, with one shared
    120 s grace. They are **not** charged to the per-arm retry budget; a separate
    `BNJ_POD_STALL_RETRIES` budget (default 2) applies. They are relaunched only when the cgroup
    has the arm's last RSS free; until then `POD_RELAUNCH_WAIT` repeats, until another arm exits.
  - Every poll (5 s) prints `POD_MEM`: cgroup `memory.current`, `memory.max`, free, `memory.pressure`
    full avg10, and each live arm's RSS summed over its process group. That is about 2.6 MB of pod
    stdout per day, so kubelet log rotation (10 MiB by default) drops early lines from
    `kubectl logs`. The per-arm logs on the PVC are unaffected.
  - Exit 5 (RSS gate) is not retried and counts as failed.
  - Tests: `tests/test_run_pack.py`, 7 passed (2 old, 5 new); `tests/test_memory_leak_fix.py`, 10 passed.
- **0031 `bnhgq2/ablation.py`.**
  - `ValidationReloader`: one validation model per run. Epoch 1 calls `load_model`; every later
    epoch calls `load_weights` from the saved candidate into the same model. So one model and one
    predict function live for the whole run, instead of a new model, graph and predict function
    per epoch.
  - Variables, `stored_state_ebops` and predictions equal a fresh `load_model` byte for byte, epoch
    after epoch (`tests/test_memory_leak_fix.py`). A 4-epoch run gives the same records as the
    fresh-load path. The absent-key regression against 77f1ca4e is unchanged (below).
  - RSS canary gate, projection form (coordinator correction, 2026-09-28; Delta adopts the
    same gate). It is set by Job env only, so config shas are unchanged:
    `BNJ_RSS_GATE_LIMIT_MB=6144 BNJ_RSS_GATE_WINDOW=5:105` on both pilot-b pods. *[Superseded 2026-09-28: 8 GiB / 8192, see 'Per-arm memory 8 GiB' above.]*
    **Exact gate:**
    - Host RSS (Linux `VmRSS` of the arm's process, read at the end of every epoch) is fitted
      against epoch by least squares over this process's epochs 5 to 104 (100 epochs, counted
      from the epoch the process started or resumed at).
    - At the end of process epoch 105 it computes
      `projection = baseline + slope × train.epochs` (7,000; R 1,000), where baseline is the
      fitted RSS at process epoch 5.
    - PASS iff `projection ≤ 6,144 MiB` (8,192 since 2026-09-28), the per-arm memory limit in the manifest. With a baseline
      of about 2.2 GB this means a slope of about 0.55 MB/epoch or less.
    - Every arm prints `RSS_GATE <arm> PASS|FAIL slope_mb_per_epoch … baseline_mb … projection_mb …
      at_epoch … limit_mb 6144`. On FAIL it writes `RSS_GATE_FAIL.json` (the whole series) and exits 5.
    - The epoch line gains ` host_rss_mb=` only when the gate is set.
    - A resume restarts the window. The pilot pauses at 500, so every arm is gated long before
      then.
- *[Superseded 2026-09-28: 8 GiB / 8192, see 'Per-arm memory 8 GiB' above.]* **Per-arm memory stays 6 GiB (30 Gi K=5, 18 Gi K=3).** Measured start-of-run RSS was 2,106-2,160
  MB per arm (incident §2, W&B `rssMB` at 20:56Z, about 5 min after launch). The projection gate
  admits an arm only if its fitted RSS stays within this 6 GiB to the terminal epoch. The same
  6 GiB therefore holds for production, provided every production arm passes the same gate (run it
  in production too, or rely on the pilot-b slopes: orchestrator's call).

**CPU test at the gate's bar: a leak is reproduced and removed. The GPU magnitude is not
reproduced.** The same probe (`code/evidence/leak_probe.py B 115`) was run on both trees: the
whole `run_training` loop, regime B, chang0926-a-n64-s1, synthetic 4,000 train / 2,000
validation rows, macOS CPU, `phys_footprint` after `gc.collect()`. The gate formula was applied
to epochs 5-104, projected to 7,000 epochs at 6,144 MiB. This is not a result.
```
pre-fix  (f2107a04): slope_mb_per_epoch 3.237 baseline_mb 1437 projection_mb_at_7000 24096 limit 6144 FAIL
post-fix (42abed4b): slope_mb_per_epoch 0.004 baseline_mb 1883 projection_mb_at_7000 1911  limit 6144 PASS
```
(`leak_probe_f2107a04_prefix_B_115ep.{json,log}`, `leak_probe_42abed4b_B_115ep.{json,log}`.)
The pre-fix series climbs steadily (1,445 → 1,781 MB, epochs 5-110). The post-fix series is flat
within ±60 MB of noise, and the Python object count is flat in both. Earlier single-operation probes
at larger scales, under heavy load, could not resolve slopes below about 10 MB/iteration. So:
- on CPU the per-epoch reload path leaks about 3 MB/epoch, and `ValidationReloader` removes it;
- the 80-95 MB/epoch seen on the GPU pods was **not** reproduced here, so whether the GPU leak is
  the same mechanism is still unproven. **The GPU proof is the pilot-b RSS gate at process epoch
  105** (fitted slope and projection per arm).

The per-epoch ` host_rss_mb=` on the arm logs tells the causes apart. A step at each traced
epoch (0, 9, 19, ...) points at the trace. A uniform slope points at a per-epoch path.
A leak as large as the incident's fills 6 GiB near epoch 48 (8 GiB near epochs 64-76 after the
2026-09-28 resize), before the verdict. It would
show as `POD_STALL` with `POD_MEM` lines, and it would not use up the retries.

**New shas.** Bundle `42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0` (198,452
bytes, 250 files). `run_study.manifest()` is `041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42`.
ConfigMap `kai-chang0926-code-42abed4b5d`, payload `manifests/configmap.json` = `configmap-42abed4b.json`.
The 77f1ca4e payload is kept. The `configmap-f2107a04.json` / `bundle-manifest-f2107a04.json`
pair is superseded and was never applied. Also superseded: ceb174db (manifest 33e9bf7b, the first
slope-form gate), whose payload was deleted unused. `bash code/apply.sh` (patches 0001-0031) ends
`APPLY_MATCHES_TREE`. A fresh extraction equals `code/tree` + `code/analysis`. `freeze.py` run
twice gives the same sha. Jobs: `kai-chang0926-pilotb5-42abed`, `kai-chang0926-pilotb3-42abed`,
`kai-chang0926-readoutb5-42abed`, `kai-chang0926-readoutb3-42abed`, and
`kai-chang0926-readouta-77f1ca` (unchanged; its embedded script is byte-identical to the one dry-run).

**Gate behaviour worth knowing.**
- Exit 5 reaches `run_pack`. `rss_gate_step` raises `SystemExit(5)` inside `run_training`.
  `run_study.train` catches `BaseException`, marks the W&B run crashed and re-raises with a bare
  `raise` (`run_study.py:140-147`). No wrapper around `train()` changes the code, so the arm exits
  5 and `run_pack` does not retry it.
- A process that resumes with fewer than 105 epochs left before its pause or end never gets a
  verdict, because the window restarts with each process. This does not matter for the pilot (it
  pauses at 500). Production resumes near the end are not gated.
- The builder's new `MISMATCH_OFFSET = 1000` was never re-run from scratch; the f2107a04 negative
  test edited F-s1's `state.json` in place. The 42abed4b b3 run used F-s1 restored to logged = traced.

**Code sha, 42abed4b (corrected 2026-09-28, PREFLIGHT gate v3 flag 8).** Committed: the bundle,
`code/tree`, the patches, the evidence and the manifests are in **3dabcd2**; the cluster record is in
**ad18a3c**; `git log -- code/tree` ends at 3dabcd2 and `git status --short code/` is empty. The gate v3
fixes (section "PREFLIGHT gate v3 fixes" above) change no bundle file; the files they touch are
listed there and are uncommitted until the orchestrator commits them. The list below is what 3dabcd2
had to contain, kept for the record (written before that commit):
- `code/tree/run_pack.py`, `code/tree/bnhgq2/ablation.py`, `code/tree/tests/test_run_pack.py`, and the
  new `code/tree/tests/test_memory_leak_fix.py`;
- `code/patches/0030-*.patch`, `0031-*.patch`;
- `manifests/freeze.py`, `chang0926-code.tar.gz`, `configmap.json`, `configmap-42abed4b.json`,
  `bundle-manifest.json`, `bundle-manifest-42abed4b.json`, and the five regenerated Job manifests;
- `code/evidence/leak_probe.py`, `leak_micro.py`, the modified `dry_readout_build.py` and
  `dry_readout_run.py`, and every `*42abed4b*` and `leak_probe_*` evidence file;
- `plan.md`, this file, and `.claude/memory/decisions.md`.

**Gates on a fresh extraction of 42abed4b** (pinned versions as below; cwd recorded on line 1 of
each log; CPU, synthetic, not results):
- Full `cpu_gate.py`, no `--only` (`code/evidence/cpu_gate_shipped_42abed4b_full.{log,json}`): exit 0,
  ```
  PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2
  ```
- pytest `tests/ analysis/test_attn_entropy.py`: `93 passed, 2 skipped`. That is the 78 of f2107a04
  plus 5 new `test_run_pack.py` and 10 `test_memory_leak_fix.py` (`pytest_shipped_42abed4b.log`).
- [A17] `check_pairing.py --arms a,b,d,r --seeds 1..8`: 32 / 32 `PAIRED`, each differing from F only
  by `pos_enc/pos_table`, 0 of 15 shared differing; `MANIFEST 041f981a…` printed in the extraction
  (`a17_pairing_shipped_42abed4b_8seeds.{log,json}`).
- [A7] floors, `trace_floors.py`: all nine arms `STATIC_FEASIBLE`, the same numbers as on f2107a04
  (e.g. `ARM_FLOOR a07-350 zero 343053 … headroom 6947 STATIC_FEASIBLE`; `trace_floors_42abed4b.log`).
- Absent-key regression (`regress_trace_every.py` in the extraction against
  `regression_trace_every_absent_77f1ca4e.json`; `regression_trace_every_absent_42abed4b.{json,log}`,
  four `ABSENT_KEY_REGRESSION … records_files_ebops_identical True` lines). Per
  config, `records_sha`, `record_keys`, the EBOPs series and every file hash are equal: a-s1
  55c44118…, C′-s1 dbeaec23…, const0922-a07 63a41009…, const0922-b03 2ec3db02…. The epoch lines
  are identical for the two screen configs, and identical after removing the three B2 fields for
  the two chang0926 configs, as on f2107a04 (DECISION R-B5). So the reloader leaves every record,
  checkpoint and EBOPs of the absent-key path unchanged.
- Lint (`nrp_doctor.py lint` on the 42abed4b manifests, exit 0 each; `code/evidence/lint_42abed4b.log`): pilot-b-k5 `OK` (PACK 5 arms),
  pilot-b-k3 `OK` (PACK 3 arms), readout-a / readout-b5 / readout-b3 `OK`. `bash -n` passes on all five scripts.
  Both pilot-b scripts export `BNJ_RSS_GATE_LIMIT_MB=6144 BNJ_RSS_GATE_WINDOW=5:105`. *[Superseded 2026-09-28: 8 GiB / 8192, see 'Per-arm memory 8 GiB' above.]*
- Epoch-500 readout dry runs on the 42abed4b tarball (same synthetic layout and runner as below;
  F-s1 restored to logged = traced for a clean positive run):
  - readout-b5 (`code/evidence/dry_readout_b5_42abed4b.log`):
    ```
    chang0926-code.tar.gz: OK
    MANIFEST_SHA_OK 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42
    CERTIFICATION_ALL_PASS 6 0
    A26_DONE
    READOUT_JOB_DONE certify_exit=0 a26_exit=0
    DRY_RUN_EXIT kai-chang0926-readoutb5-42abed 0
    ```
  - readout-b3 (`code/evidence/dry_readout_b3_42abed4b.log`):
    ```
    MANIFEST_SHA_OK 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42
    CERTIFIED chang0926-c-n64-s1 snapshot500_primary 14598422 14598422
    CERTIFIED chang0926-f-n64-s1 snapshot500_primary 10428606 10428606
    CERTIFIED chang0926-a07-350-n64-s1 snapshot500_primary 14598422 14598422
    CERTIFICATION_ALL_PASS 3 0
    READOUT_JOB_DONE certify_exit=0 a26_exit=0
    DRY_RUN_EXIT kai-chang0926-readoutb3-42abed 0
    ```
  - readout-a: unchanged. It uses the 77f1ca4e ConfigMap, its embedded script is byte-identical
    to the one dry-run below, and it passed (`CERTIFICATION_ALL_PASS 6 0`, exit 0).
  - The mismatch path was exercised on f2107a04 (below). `certify_ebops.py` is byte-identical in
    42abed4b.

The sections below were written for f2107a04. The configs, `certify_ebops.py`,
`attn_entropy.py` and `evaluate_roc.py` are byte-identical in 42abed4b. The f2107a04 shas,
ConfigMap and Job names in them are superseded by the ones above.

### Answers for STUDY slots T, C, P

In `plan.md`, "ml-engineer, regime B", subsection "Answers for the STUDY amendment", (a)-(e),
plus DECISION R-B1 to R-B5. In short:
- **Traced epochs (slot T).** Zero-based e is traced iff e == 0, (e + 1) % 10 == 0, or it is the
  last epoch. That gives 701 traces per 7,000-epoch run and 101 for R. The ends of epochs 1, 10,
  500, 1,000, 2,000, 4,000 and 7,000 are traced (`ablation.py:483-489`, asserted in
  `tests/test_trace_every.py::test_key_semantics`). The canary pair is the end of epoch 1
  against the end of epoch 10. **STUDY at 96b95f2 must be corrected** (l. 1403-1410 say there is
  no epoch-0 trace, 700 / 100 traces, and a canary of `initial_ebops` against epoch 10).
- **PID input.** On untraced epochs BetaPID reads the in-training EBOPs of the last training
  step. On traced epochs it reads the traced value. Asserted per epoch type (`ablation.py:766-777`).
- **Selection.** The budget, feasibility, all four selected files, the non-degeneracy counters
  and the recovery freeze run only on traced epochs (`ablation.py:721-765`). The candidate is
  still saved, reloaded and validated every epoch.
- **Pods (P).** `packs.json` has 13 wave-1 pods. The E arms {A, B, D, F} run at K=5 in 7 pods
  (5, 5, 5, 5, 4, 4, 4). The A07 pairs {C, A07-350} run at K=4 in 4 pods, which wait for the K=3
  pilot's A07-350-s1 epoch-500 readout. R runs **alone** in 2 pods at K=4. This is what STUDY
  says, so no pod correction is needed. The K=4 A07 figure is provisional: no A07-350
  per-process memory exists yet (plan.md R-B3).

### Code sha

- **Bundle** `manifests/chang0926-code.tar.gz` sha256
  `f2107a042b8c6b45d14b7626ac9d23a8b6c3abcd14156ec31644a3a517c5438e` (191,320 bytes, 249 files).
  `run_study.manifest()` = `12c76954a4d25826a9ad11d12c62adf63b94868d8a66d82f8e1115064d62dd38`.
- **ConfigMap** `kai-chang0926-code-f2107a042b`, payload `manifests/configmap.json` and the
  sha-named copy `manifests/configmap-f2107a04.json` (plus `bundle-manifest-f2107a04.json`).
  The 77f1ca4e payload is kept as `configmap-77f1ca4e.json`; it is byte-identical to
  `configmap.json` at HEAD (sha256 19c7f33e...).
- **Contents.** `code/tree` (26f3cc40 + patches 0001-0029) + `code/analysis/`. `bash code/apply.sh`
  ends `APPLY_MATCHES_TREE`. A fresh extraction of the tarball equals `code/tree` + `code/analysis`
  (`diff -rq`, `__pycache__` excluded: empty). `freeze.py` re-run reproduces the same bundle sha
  (deterministic).
- **Historical (f2107a04, superseded before any pod; never applied).** At write time the working
  tree was dirty and uncommitted (repo HEAD 340c33b). The current bundle 42abed4b is committed in
  3dabcd2; see "Code sha, 42abed4b" above.
  - Modified: `code/tree/bnhgq2/{ablation,wandb_util}.py`, `code/tree/run_study.py`,
    `code/tree/tests/test_wandb_stage.py`, `code/tree/campaigns/chang0926/{cpu_gate.py,
    generate.py, index.json, packs.json, cache_configs/n64.json, config_diff_a_s1.json}`, all 58
    `configs/chang0926-*.json`, `manifests/{freeze.py, chang0926-code.tar.gz, configmap.json,
    bundle-manifest.json}`, `plan.md`, and this file.
  - New: `code/patches/0027-0029`, `code/tree/tests/test_trace_every.py`,
    `code/tree/campaigns/chang0926/{packs_meta.json, pilot_b_k3_packs.json, pilot_b_k5_packs.json}`,
    the regime-B manifests and payloads listed here, and the evidence files below.
  - The commit must include all of these, or the sha does not describe the shipped code.

### Config builds and CPU gates (fresh extraction of f2107a04; pinned tensorflow 2.21.0, keras 3.15.0, hgq2 0.1.9, numpy 2.5.0 via `uv run --with`)

- **Full `cpu_gate.py`**, no `--only`, run in the extracted bundle (`code/evidence/cpu_gate_shipped_f2107a04_full_rerun.{log,json}`,
  cwd recorded on line 1), exit 0, 0 `GATE_FAIL`:
  ```
  PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2
  ```
  Every config has `reload_max_abs_diff 0.0` (tolerance `atol = rtol = 2e-6`) and `floor_retraced`
  equal to its `zero_floor`, and prints `TRACE_EVERY_OK ... k 10 epochs 7000 traced_epochs 701
  snapshot_every 500` (R: 1,000 epochs, 101). The 175 PASS lines equal those of the earlier
  f2107a04 run. With the `TRACE_EVERY_OK` lines removed, they equal `cpu_gate_shipped_77f1ca4e_full.log`.
  The builds are therefore unchanged by regime B.
  Parameters as printed (seed 1): A, B, D, R 31,735; F 33,271; C, A07-350 61,951; C′ 12,788;
  E1 19,447.
- **pytest** `tests/ analysis/test_attn_entropy.py` in the extraction: `78 passed, 2 skipped`
  (`pytest_shipped_f2107a04_rerun.log`). This includes `test_trace_every.py` and
  `test_wandb_stage.py::test_pilot_b_cannot_collide_with_pilot` (232 W&B ids, one per stage in
  {pilot, pilot-b, production, legacy} for each of the 58 names; all distinct; group
  `chang-n64-20260926-pilot-b`).
- **[A17] pairing**, `check_pairing.py --arms a,b,d,r --seeds 1,...,8`: 32 / 32 `PAIRED`, each
  arm differs from F only by `pos_enc/pos_table`, with 0 of 15 shared tensors differing. The JSON equals
  `a17_pairing_d25_8seeds.json` (`a17_pairing_shipped_f2107a04_8seeds_rerun.{log,json}`).
- **[A7] static floors**, `trace_floors.py`: all nine arms `STATIC_FEASIBLE`
  (`trace_floors_f2107a04_rerun.log`), e.g.
  ```
  ARM_FLOOR a zero 171526 one 619198 attn_narrow 368134 attn_full 478726 target 350000 headroom 178474 STATIC_FEASIBLE
  ARM_FLOOR a07-350 zero 343053 one 1005741 attn_narrow 605197 attn_full 801805 target 350000 headroom 6947 STATIC_FEASIBLE
  ARM_FLOOR e1 zero 85763 one 533435 attn_narrow 282371 attn_full 392963 target 350000 headroom 264237 STATIC_FEASIBLE
  ```
- **Absent-key regression** (`regress_trace_every.py`, 3 epochs of `run_training` on synthetic
  rows, key removed; `regression_trace_every_absent_f2107a04.log`). The 77f1ca4e reference
  reproduces in a fresh extraction of the committed tarball (`REFERENCE_REPRODUCED True`).
  ```
  ABSENT_KEY_REGRESSION chang0926-a-n64-s1 records_files_ebops_identical True epoch_lines_identical False epoch_lines_identical_after_removing_B2_fields True
  ABSENT_KEY_REGRESSION chang0926-cprime-n64-s1 records_files_ebops_identical True epoch_lines_identical False epoch_lines_identical_after_removing_B2_fields True
  ABSENT_KEY_REGRESSION const0922-a07-n64-s1-fast50-fp32 records_files_ebops_identical True epoch_lines_identical True epoch_lines_identical_after_removing_B2_fields True
  ABSENT_KEY_REGRESSION const0922-b03-n8-s1-fast50-fp32 records_files_ebops_identical True epoch_lines_identical True epoch_lines_identical_after_removing_B2_fields True
  ```
  The per-epoch jsonl records, every variable of every saved `.keras` file, the state files and
  the EBOPs are byte-identical to 77f1ca4e. **Not byte-identical:** the stdout epoch line of
  [D20] configs has three extra trailing fields, `ebops_trace_seconds=… ebops_trace_over_epoch=…
  loss=…` (brief item 2, physics v9 B2), with or without the key. Flagged as DECISION R-B5 in
  plan.md; the orchestrator confirms or overturns it (the alternative is to gate the fields on
  the key and re-freeze).

### Arm table (STUDY arms → configs → job index → regime-B pack)

| Arm | Configs (`code/tree/campaigns/chang0926/configs/`) | Job indices | Production pack (`packs.json`) | Regime-B pilot |
|---|---|---|---|---|
| A | `chang0926-a-n64-s{1..8}.json` | 0-7 | 0-6 (seed-ordered E blocks) | s1, s2: K=5 pod |
| B | `chang0926-b-n64-s{1..8}.json` | 8-15 | 0-6 | none |
| C | `chang0926-c-n64-s{1..8}.json` | 16-23 | 7-10 (A07 pairs, after K=3 readout) | s1: K=3 pod |
| D | `chang0926-d-n64-s{1..8}.json` | 24-31 | 0-6 | s1: K=5 pod |
| F | `chang0926-f-n64-s{1..8}.json` | 32-39 | 0-6 | s1: K=3 pod |
| R | `chang0926-r-n64-s{1..8}.json` | 40-47 | 11-12 (R only, K=4) | none |
| A07-350 | `chang0926-a07-350-n64-s{1..8}.json` | 48-55 | 7-10 | s1: K=3 pod |
| C′ (pilot only) | `chang0926-cprime-n64-s1.json` | 56 | none | s1: K=5 pod |
| E1 (pilot only) | `chang0926-e1-n64-s1.json` | 57 | none | s1: K=5 pod |

Every one of the 58 configs carries `"ebops_trace_every": 10`.

### Manifests, f2107a04 generation (SUPERSEDED; historical, do not copy)

**Superseded 2026-09-28.** The Job names, ConfigMap and `sha256sum -c` literal in this table and
the lint block below are the f2107a04 ones, never applied. The current Jobs are
`kai-chang0926-pilotb5-42abed`, `-pilotb3-42abed`, `-readoutb5-42abed`, `-readoutb3-42abed` on
`kai-chang0926-code-42abed4b5d`, plus the gate v3 fingerprint ConfigMap and fallback Jobs; see
"PREFLIGHT gate v3 fixes" at the top of this addendum.

| File | Job | ConfigMap | What |
|---|---|---|---|
| `pilot-b-k5-job.json` | `kai-chang0926-pilotb5-f2107a` | `kai-chang0926-code-f2107a042b` | GPU, K=5, `pilot_b_k5_packs.json` `[[0, 1, 24, 56, 57]]` = A-s1, A-s2, D-s1, C′-s1, E1-s1; `--stop-after 500`; 10 CPU / 30 Gi |
| `pilot-b-k3-job.json` | `kai-chang0926-pilotb3-f2107a` | `kai-chang0926-code-f2107a042b` | GPU, K=3, `[[48, 16, 32]]` = A07-350-s1, C-s1, F-s1; `--stop-after 500`; 6 CPU / 18 Gi |
| `readout-b5-job.json` | `kai-chang0926-readoutb5-f2107a` | `kai-chang0926-code-f2107a042b` | CPU epoch-500 readout of the K=5 pilot-b pod |
| `readout-b3-job.json` | `kai-chang0926-readoutb3-f2107a` | `kai-chang0926-code-f2107a042b` | CPU epoch-500 readout of the K=3 pilot-b pod |
| `readout-a-job.json` | `kai-chang0926-readouta-77f1ca` | **`kai-chang0926-code-77f1ca4e9f`** | CPU epoch-500 readout of the regime-A pilot on the code that trained it (manifest check `f7d4003f`); five runs, since A07-350-s1 has no regime-A snapshot |

Both pilot-b pods: `BNJ_STAGE=pilot-b` (W&B id sha256("pilot-b" NUL name)[:12], group
`chang-n64-20260926-pilot-b`, tags `chang0926,pilot,pilot-b,regime-b,validation-only`),
`BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot-b`, and bundle `sha256sum -c` against f2107a04.
Their W&B ids and run directory cannot collide with the regime-A pilot's (`pilot`,
`/data/chang-n64-20260926/pilot`). The readouts write to `.../pilot-b/readout-epoch-0500-f2107a-b{5,3}`
and `.../pilot/readout-epoch-0500-77f1ca-a`. `bash -n` passes on all five embedded scripts.

**Lint (ml-engineer, local run of `nrp-lab/nrp_doctor.py lint`, exit 0 for each):**
```
== pilot-b-k5-job.json :: kai-chang0926-pilotb5-f2107a ==
  note   required pool = 4 products / 109 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 5 arms per pod declared.
  OK
== pilot-b-k3-job.json :: kai-chang0926-pilotb3-f2107a ==
  note   required pool = 4 products / 109 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 3 arms per pod declared.
  OK
== readout-a-job.json :: kai-chang0926-readouta-77f1ca ==   OK (CPU, single Job)
== readout-b5-job.json :: kai-chang0926-readoutb5-f2107a == OK (CPU, single Job)
== readout-b3-job.json :: kai-chang0926-readoutb3-f2107a == OK (CPU, single Job)
```
**Cluster-ops (2026-09-28T07:54-07:56Z, applied by cluster-ops).**

- **ConfigMap.** `kubectl create -f manifests/configmap-42abed4b.json -n cms-ml` at 07:54:51Z ->
  `configmap/kai-chang0926-code-42abed4b5d created`. Live read-back: `immutable: true`,
  `binaryData['hgq2.tar.gz']` decodes to 198,452 bytes, sha256
  `42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0` — matches the bundle sha
  above exactly. `kubectl -n cms-ml get configmap | grep kai-chang0926-code` at 07:58Z shows three
  total: `kai-chang0926-code-42abed4b5d` (new), `kai-chang0926-code-77f1ca4e9f`,
  `kai-chang0926-code-c5d6f02a83` — both older ones left untouched. `f2107a042b` and `ceb174db48`
  are not on the cluster (per the addendum, f2107a04 was never applied and ceb174db's payload was
  deleted unused), consistent with this listing; not applied here either.
- **Live-lint re-run**, `nrp_doctor.py lint` on the two pilot-b Jobs (post-freeze, current tree):
  ```
  == pilot-b-k5-job.json :: kai-chang0926-pilotb5-42abed ==
    note   required pool = 4 products / 107 nodes cluster-wide
    note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
    note   [rule PACK] 5 arms per pod declared.
    OK
  == pilot-b-k3-job.json :: kai-chang0926-pilotb3-42abed ==
    note   required pool = 4 products / 107 nodes cluster-wide
    note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
    note   [rule PACK] 3 arms per pod declared.
    OK
  ```
  Both jobs reference `kai-chang0926-code-42abed4b5d` (checked via the manifest's `volumes[].configMap.name`,
  not just the Job name suffix), set `BNJ_STAGE=pilot-b` and `BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot-b`.
  Node affinity `requiredDuringSchedulingIgnoredDuringExecution` allows only
  `NVIDIA-L40`, `NVIDIA-A10`, `NVIDIA-GeForce-RTX-3090`, `Tesla-V100-SXM2-32GB` — no A100, no 2080 Ti.
  Embedded startup `sha256sum -c` check: both scripts contain the literal
  `42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0` exactly once
  (`grep -c` on each file = 1); neither script contains `f2107a04` or `ceb174db` anywhere
  (`grep -l` on both files = no match) — the pods will not fail their bundle check on startup.
  - *Note (ml-engineer, 2026-09-28, gate v3 A1):* the four-class affinity above describes the
    manifests as they were at 07:56Z. They were regenerated: the pilot-b Jobs now require
    `NVIDIA-A10` only, with no preferred class, and exclude c6017. See "PREFLIGHT gate v3 fixes",
    which also holds the GPU fingerprint gate, the A2 epoch-10/20 RSS rule with its commands, and
    the K=3 OOM fallback Jobs.
- **PVC headroom.** No running pod currently mounts `kai-data` (regime-A pilot stopped; checked
  `kubectl -n cms-ml get pods`, no `kai-*` pod in Running state touching `/data`). Ran a short
  read-only debug pod (`kai-df-check-42abed`, `image: python:3.12`, PVC mounted `readOnly: true`,
  no GPU request, not a Job manifest so out of `nrp_doctor.py`'s Job-lint scope) to read `df -h /data`,
  then deleted it immediately after capture:
  ```
  Filesystem ... Size  Used Avail Use% Mounted on
  csi-cephfs-node@... 100G   34G   67G  34% /data
  ```
  67 Gi free of 100 Gi (34% used), read 2026-09-28T07:55Z. Pod deleted; no other object touched.
- **Not done (per brief): neither pilot-b Job was applied.** PREFLIGHT gate v3 comes first.

### CPU dry run of the epoch-500 readout

`code/evidence/dry_readout_build.py` builds a synthetic layout: a gated cache of the real shape
(558,000 / 62,000 × 64 × 3) and epoch-500 snapshot directories for the regime-A roots (the
77f1ca4e configs) and the regime-B roots (the f2107a04 configs). Each `model_best.keras` is the
production initializer after one full-split trace, and `target_ebops` is raised to 1e9 so an
untrained model can certify. F-s1 under `pilot-b` deliberately logs traced + 1, to exercise
`EBOPS_MISMATCH`. `dry_readout_run.py` then runs each readout Job's own bash script unchanged,
except for path substitution, the removed `pip install` line (a pinned `uv` interpreter instead),
and a `sha256sum` shim. So the bundle sha check, `MANIFEST_SHA_OK`, the snapshot gate,
`certify_ebops.main()`, `analysis/attn_entropy.py` and the exit logic run as written.
The synthetic models for both roots are built with the f2107a04 tree. readout-a loads and
retraces them with the 77f1ca4e code. Patches 0027-0029 touch no layer or quantizer file.
Fix made here: the runner's "unsubstituted /data path" guard fired on the cache's own
`n64/data/` subdirectory, so it had never completed. It now matches only an absolute `/data/`.

- **readout-a on the 77f1ca4e tarball** (`code/evidence/dry_readout_a.log`), for the regime-A
  pilot's epoch-500 readout. That pilot is stopped, with no epoch-500 snapshot yet (see top). Done:
  ```
  old.tar.gz: OK
  MANIFEST_SHA_OK f7d4003f49584c701aec1cfefb4c0c9a3591c41d7d2fda94dd5a293d00eaaa36
  CERTIFICATION_ALL_PASS 6 0
  A26_DONE
  READOUT_JOB_DONE certify_exit=0 a26_exit=0
  DRY_RUN_EXIT kai-chang0926-readouta-77f1ca 0
  ```
- **readout-b5 on the f2107a04 tarball** (`code/evidence/dry_readout_b5.log`):
  ```
  chang0926-code.tar.gz: OK
  MANIFEST_SHA_OK 12c76954a4d25826a9ad11d12c62adf63b94868d8a66d82f8e1115064d62dd38
  CERTIFICATION_ALL_PASS 6 0
  A26_DONE
  READOUT_JOB_DONE certify_exit=0 a26_exit=0
  DRY_RUN_EXIT kai-chang0926-readoutb5-f2107a 0
  ```
- **readout-b3 on the f2107a04 tarball, first run** (`code/evidence/dry_readout_b3_plus1.log`):
  `CERTIFICATION_ALL_PASS 3 0`, `READOUT_JOB_DONE certify_exit=0 a26_exit=0`, exit 0. The planted
  F-s1 mismatch (logged = traced + 1: `CERTIFIED chang0926-f-n64-s1 snapshot500_primary 10428607
  10428606`) is **inside** `certify_ebops.REL_TOL = 1e-6` at about 1e7 EBOPs (9.6e-8), so it was
  certified by design and the mismatch path was not exercised. For scale, the same tolerance allows
  0.35 EBOPs at 350k (so a difference of 1 fails) and 5 EBOPs at 5M. The builder now plants +1,000.
  The negative re-run is below.
- **readout-b3 negative test on the f2107a04 tarball** (`code/evidence/dry_readout_b3_mismatch.log`),
  **PASS by design**. F-s1's snapshot `state.json` was edited in place to logged = traced + 1,000
  (the builder's new `MISMATCH_OFFSET`; the layout was not rebuilt):
  ```
  CERTIFIED chang0926-c-n64-s1 snapshot500_primary 14598422 14598422
  EBOPS_MISMATCH chang0926-f-n64-s1 snapshot500_primary 10429606 10428606
  CERTIFIED chang0926-a07-350-n64-s1 snapshot500_primary 14598422 14598422
  CERTIFICATION_FAIL 3 1
  READOUT_JOB_DONE certify_exit=4 a26_exit=2
  DRY_RUN_EXIT kai-chang0926-readoutb3-f2107a 1
  ```
  The mismatch is reported, and certification exits 4 and the Job exits non-zero, as intended.
  `a26_exit=2` is `attn_entropy.py` refusing to overwrite the first run's output file (its
  no-overwrite guard), not a failure of the entropy code, which completed in the first run.

### Coordinator question: which series feasibility test (a) reads for C and C′

Answered in `plan.md`, "Coordinator question: C and C′ constraint-active readout". Test (a)
reads the full-split traced EBOPs of traced epochs, `cost['total']` (`ablation.py:694-695, 723`).
In `activation_widths.jsonl` and in W&B this is key `ebops`. Under regime B the key is null or
absent on untraced epochs, and `ebops_traced` flags which epochs were traced. The outcome of the
test is `budget_met` / `ebops_budget_met`. β is key `beta`, logged every epoch. The selected
checkpoint's EBOPs is `best_feasible.ebops` in the snapshot `state.json` and `logged_ebops` /
`retraced_ebops` in the readout's certification JSON. The SAT build (C′) changes none of this.
No code change was needed.

### Regime-A readout after the stop

The regime-A pilot stopped at 05:31Z on 2026-09-28 with checkpoints at 0125 / 0125 / 0150 / 0075 /
0025 (A-s1, A-s2, D-s1, E1-s1, C′-s1) and no epoch-500 snapshot. `readout-a-job.json` gates on
`snapshots/epoch-0500/state.json` or `DIVERGED.json` for all five runs, so it would stop at
`SNAPSHOTS_NOT_READY`. It becomes applicable only if those runs are resumed on the 77f1ca4e
ConfigMap (the code that trained them) to epoch 500. A resume on 42abed4b is refused by
`restore_checkpoint`, because the code sha differs. Orchestrator's call.
