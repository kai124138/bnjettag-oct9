# PREFLIGHT — 2026-09-27-delta-screen (delta0926 wave 2), build half

**GPU policy amendment, 2026-09-28 (Kai):** future Delta production is selected by
[the GPU selection policy](../../docs/infrastructure/gpu-selection-policy.md). The A10 canary
and A10-only manifests below are historical or planning artifacts. Before production, benchmark
and certify E and A07 on the chosen GPU product, regenerate K and the Jobs for that product,
and re-run lint and the paired-product gate. The frozen statistical launch gates remain active.
Generate product-specific planning manifests with `code/manifest_wave2.py --gpu-product ...
--out ...` and freeze their packs with `bundle/freeze_delta.py --packs-dir ... --out-dir ...`.
Do not treat the generated baseline K=4/5/3 canary as a full throughput or utilization
certificate for a 40/48/80-GB card.

Date: 2026-09-28. Owner: ml-engineer (build sections). cluster-ops appends the lint, ConfigMap and
cluster sections and owns RUN.md. Scope: the Delta wave-2 code bundle, the CPU gates against the
frozen STUDY's launch gates 1-14, and the memory canary as the next step. Nothing was applied to
the cluster and nothing was committed. Everything below ran on a laptop CPU with synthetic
inputs, so none of it is a result.

> **Superseded 2026-09-28 (gate 15):** bundle 705a554b, ConfigMap `kai-delta0926-code-705a554b8d`, manifests `manifests/delta-canary-v2-job.json` and `manifests/discrim-*.json`; see "Gate 15 and the re-frozen bundle" at the end. The text below is the e6fc6cd9 record.

- **Code sha.** See "Code sha" below: Delta code at git **aea3e6f** (clean), the anchor bundle
  42abed4b at 3dabcd2; the bundle directory and this file are new and uncommitted.
- **Bundle (ConfigMap payload) sha256:**
  **e6fc6cd921d574f7ac153d597341b8f1c36db088f7cc9c91f5d59401c8d967fb**. The file is
  `bundle/delta-code.tar.gz`: 334,471 bytes, base64 445,964 bytes, 576 files.
- **`run_study.manifest()` sha256** (the pods' `__MANIFEST_SHA256__`, the trainer's `code_sha256`):
  **300be87bf0cde5fba95c7b9cf0798718475e2b2dd6a230ee44a58a22fa8d467c**.
- **ConfigMap:** `kai-delta0926-code-e6fc6cd921`, immutable, key `hgq2.tar.gz`. The payload is
  `bundle/configmap.json`.
- **Generator:** `bundle/freeze_delta.py`. It never submits. Regenerate with it; never
  hand-edit the JSONs.

## Bundle

**Build.**
- `campaigns/2026-09-26-delta/code/apply_anchor.sh` extracts the anchor bundle.
  - It checks the anchor sha: `ANCHOR_BUNDLE_SHA_OK 42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0`.
  - It copies `newmods/`.
  - It applies `patches-anchor/0001-0038` with `git apply --3way`: 38 `APPLIED` lines, then
    `APPLY_ANCHOR_ALL_PASS`.
- `freeze_delta.py` tars that `code/` tree unchanged. It adds
  `code/campaigns/delta0926/` (= `BNJ_CAMPAIGN_DIR`, WIRING.md "Launch path"), which holds:
  - `index.json`: byte-identical to `code/configs/index.json`, sha256 f7b6e5b9…9288, all 582 rows.
    The packs pin this sha, and `run_pack.py` launches by row position.
  - `configs/W2/*.json`: the 312 wave-2 configs.
  - the three PLANNING packs files: `delta_canary_packs.json` (3 packs, 12 arms),
    `delta_w2_t0_packs.json` (7, 20) and `delta_w2_cells_packs.json` (83, 220).
  - `canary_k.py`.
- Tar format as in the anchor's `freeze.py`: PAX, mtime/uid/gid 0, sorted members, gzip mtime 0
  level 9.

**What the freeze asserts** (it fails loudly otherwise):
- every W2 config hashes to its row's `config_sha256`;
- every name in the three packs resolves to a shipped W2 file;
- `index_sha256` in each packs file equals sha(index.json);
- no pack mixes horizons;
- every pack's `rss_gate_limit_mb` = 2,100 + 5 × `train.epochs` (erratum 2026-09-28);
- base64 < 1,048,576.

**Size.** The payload fits in one ConfigMap (446 KB of the 1 MiB limit). The anchor's
single-key ConfigMap approach is used unchanged; no split was needed.

**Deterministic.** Two freezes gave the same sha, `e6fc6cd9…67fb`: one from the scratch build
tree, one from a second, independent `apply_anchor.sh` run. The base64 payload in
`configmap.json` decodes to the same sha. A fresh extraction differs from the build tree only by
the added `campaigns/delta0926/` (`diff -rq`).

**Manifest sha.** The freeze re-derives it with the Delta `run_study.manifest()` globs: top level,
`bnhgq2/` and `newmods/`. That differs from the anchor's `freeze.py`, which has no `newmods/`.
`run_study.manifest()` run in the extraction under the pins (tensorflow 2.21.0, keras 3.15.0,
hgq2 0.1.9, quantizers 1.2.2, numpy 2.5.0, scikit-learn 1.9.0) prints the same value:
`RUN_STUDY_MANIFEST 300be87bf0cde5fba95c7b9cf0798718475e2b2dd6a230ee44a58a22fa8d467c`.

**What the bundle contains, and what it does not.**
- **W2 configs only.** The W3 rows (268) and prereq rows (2) of `index.json` name files that are
  not shipped. None of them is in a pack. **Do not run `run_study.py preflight` on this bundle**:
  it iterates every index row.
- **Canary bundle, not the production bundle.** The packs are PLANNING (K E = 4 estimated,
  K A07 = 3 planned).
  - After the canary writes `k_result.json`, `manifest_wave2.py --k-result` rewrites the packs
    JSON. That gives a new bundle sha and a new ConfigMap name.
  - The code manifest sha 300be87b… stays the same as long as no `.py` changes.
  - So gate 11's stable identity is the manifest sha, not the bundle sha.
  - Production needs a re-freeze with `freeze_delta.py` after `k_result.json` exists.
- **Files:**
  - `bundle/bundle-manifest.json`: per-file sha256 and size, the manifest file list, and the packs
    summary;
  - `bundle/configmap.json`: the ConfigMap payload;
  - `bundle/delta-code.tar.gz`: the tarball.

## Code sha

- **Repo HEAD: aea3e6f** ("Delta code: W2 configs regenerated on 42abed4b, per-pack RSS gate
  limits, GPU memory canary manifest").
- `git status --short campaigns/2026-09-26-delta` shows only `plan.md` as modified. That file is
  not shipped. `code/` is clean, so aea3e6f describes every shipped Delta file:
  `apply_anchor.sh`, `patches-anchor/`, `newmods/`, `configs/`, `manifests/delta_*_packs.json`,
  `canary_k.py`.
- The anchor tarball `campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz` is sha-checked
  by `apply_anchor.sh`: 42abed4b, committed at 3dabcd2.
- **New and uncommitted:**
  - `bundle/freeze_delta.py`, `bundle/preflight_checks.py`;
  - `bundle/delta-code.tar.gz`, `bundle/configmap.json`, `bundle/bundle-manifest.json`;
  - `bundle/evidence/*`;
  - this file, and the ml-engineer section appended to `plan.md`.

  The commit must include all of them. Check the bundle sha, not the git sha:
  `freeze_delta.py` rebuilds it byte for byte.

## Configs

Params are as printed by `gate_cpu.py` from the extraction (`bundle/evidence/gate_cpu_bundle_e6fc6cd9.log`).
Reload is `keras.models.load_model` (TF32 off) with tolerance atol 1e-7, rtol 0.

| run | config (`campaigns/delta0926/configs/`) | builds on CPU | params | reload max abs diff | optimizer |
| --- | --- | --- | ---: | --- | --- |
| rep-A s1 | `W2/REP-A-t350000-s1.json` | GATE_PASS | 31,735 | 0 | Adam |
| rep-A07-350 s1 | `W2/REP-A07-350-t350000-s1.json` | GATE_PASS | 61,951 | 0 | Adam |
| rep-C s1 | `W2/REP-C-t5000000-s1.json` | GATE_PASS | 61,951 | 0 | Adam |
| P-350 s1 | `W2/P-350-t350000-s1.json` | GATE_PASS | 31,735 | 0 | Adam |
| P-5M s1 | `W2/P-5M-t5000000-s1.json` | GATE_PASS | 61,951 | 0 | Adam |
| M020 5M s1 | `W2/M020-t5000000-s1.json` | GATE_PASS | 61,951 | 0 | BopAdam |
| M006 350k s1 | `W2/M006-t350000-s1.json` | GATE_PASS | **20,750** | 0 | Adam |

Final line: `GATE_ALL_PASS 7/7`.

For every other (entry, arm), see GATES.md §7, "Configs, classification and gate". That run is
`gate_cpu.py --one-per-arm`: 142 pairs on the same tree (apply_anchor.sh 42abed4b +
0001-0038), and nothing under `patches-anchor/` or `newmods/` has changed since (last commit
touching them is a5c9f34, before aea3e6f). Its verdict line:
`GATE_SOME_FAILED 119/142`: 119 PASS, all `max_abs 0`; 15 NEEDS_TEACHER; 8 FAIL.

**Finding: GATES §7's M006 line was built with the wrong Deep Sets module.** GATES §7 prints
`GATE_PASS delta0926-w2-m006-t350000-s1 params 20742`. From the bundle it builds with 20,750.
- **Cause.** `gate_cpu.py` was run from `campaigns/2026-09-26-delta/code/`. Python puts the
  script's own directory first on `sys.path`, so `from newmods.deepsets import …` imported the
  **unpatched** `code/newmods/deepsets.py` (SAT, no `i_decay_speed`). The shipped tree uses the
  copy that anchor patch 0023 edits (WRAP, [A20], [D25]). The two files differ
  (`cmp`: DIFF deepsets.py; the other six newmods are identical).
- **Reproduced** (`bundle/evidence/m006_shadowing_repro.log`). `gate_cpu.py` run from that
  directory with the extraction on PYTHONPATH imports
  `NEWMODS_DEEPSETS_FROM …/2026-09-26-delta/code/newmods/deepsets.py` and prints
  `GATE_PASS delta0926-w2-m006-t350000-s1 params 20742`. Run from a copy outside `code/`, it
  prints 20,750.
- **Why it does not block launch.** M006 is unpacked (`floor_untraced`), so it cannot reach a pod
  from this bundle.
- **What it affects.**
  - The §7 M006 params and gate line (M006 350k and 5M) do not describe the shipped code.
  - `trace_floors_delta.py` lives in the same directory and would trace M006's floor with the same
    wrong module.
  - Before M006 is packed, re-gate and trace it with the script outside that directory (as done
    here, from a copy outside `code/`) or with `python -P`.
- No other entry imports a differing newmods file: bop and linformer are identical.

## Gates (STUDY "Prerequisites and launch gate", 1-14, plus the PREFLIGHT items in the brief)

"Re-run" means it ran here on a fresh extraction of bundle e6fc6cd9. "Cited" means it was not
re-run; the evidence path and tree are given.

| # | gate | status | evidence |
| --- | --- | --- | --- |
| 1 | Anchor regime-B pilot epoch-500 readout; pilot A rule | **PENDING** (GPU, anchor side) | anchor RUN.md; not a build item |
| 2 | K2 answers ([DK] defaults, canonical tree) recorded | **PENDING** (orchestrator / Kai) | not a build item |
| 3a | Z01 floor traces | PASS for packed cells; M006 excluded | GATES.md §7 "Tree and base": 73/81 signatures traced on 42abed4b, equal to 77f1ca4e. M006 `floor_untraced`: unpacked (8 runs) |
| 3b | Z10 caches: anchor gated 90/10 N=64 cache | PASS locally; PVC presence **PASS** (2026-09-29, section "In-pod cache checks") | `preflight_checks.py`: `CACHE_ID_OK packed_runs 252` (240 + the canary's 12). Every packed config has n_part 64, features pt/etarel/phirel, pt_gate 2.0, validation_split 0.1, split_seed 1, no derived features or std_scope, data_root `/data/chang-n64-20260926` = anchor `cache_configs/n64.json`. The cache was built by the anchor (PREFLIGHT l. 512). Every Delta Job checks `n64/data/READY.json` before training |
| 3c | Z10 caches: Delta-only M009 (N=32 gated), M038 (ungated), M040 (derived), M041 (real-slot std) | **NOT BUILT → excluded** | `delta_w2_cells_packs.json` `unpacked`: `cache_not_built (/data/delta-20260927/caches/<key8>)`. 28 runs: M009 8, M038 8, M040 8, M041 4. 268 − 28 = 240 packable, the STUDY count |
| 3d | y_val byte-equal to the anchor's (sha256 63049d9b…7709) | PASS by construction; in-pod confirmation **PASS** (2026-09-29, section "In-pod cache checks") | every packed run reads the anchor's own cache (row above). `run_engram.load_cache` verifies the four array hashes against the cache's `data_info.json` on every load. cluster-ops: read `array_sha256.y_val` from `/data/chang-n64-20260926/n64/data/data_info.json` |
| 3e | Z11 unit tests | Cited | (i) collapse stop: `screen-collapse-stop` + `rebase-0014-collapse-cadence`. (ii) M030-M032 schedules: `lr-schedule-variants`. (iii) EDE period: `ste-variants`. Sources: `tests_patches/slug_tests_anchor.txt` (`ANCHOR_SLUG_TESTS_ALL_PASS`, 17 lines) and `slug_tests_on_anchor.txt` (`SLUG_TESTS_ALL_PASS`), README "Rebase 2" on 42abed4b. (iv) M015 freeze is the anchor's own `experiment.recovery_after_epochs` (no Delta code); anchor pytest 99 passed, 2 skipped (`tests_patches/pytest_anchor_42abed4b.txt`). I did not locate a test specific to it |
| 3f | Z13 invariance (Delta patches off = anchor) | Cited PASS | `tests_patches/invariance_gate_anchor.txt`: 19 × SAME (9 arms, 7 const0922, 3 × 12-epoch run_training crossing traced and untraced epochs), `INVARIANCE_GATE_PASS`. Pristine 42abed4b vs apply_anchor 0001-0038 |
| 3g | Z15 | n/a | teachers not buildable (gate 13) |
| 4 | `run_pack.py` (names, roots, heartbeat fix) | **PASS** (re-run) | `bundle/evidence/pytest_runpack_bundle_e6fc6cd9.log`: `tests/test_run_pack.py tests/test_run_pack_delta.py tests/test_memory_leak_fix.py tests/test_trace_every.py` → `29 passed` |
| 5 | Horizon truncation ([D18]) | **PASS at function level** (re-run); step-level **PENDING** | `preflight_checks.py`: 27 × `HORIZON_OK`. rep-A, rep-A07-350 and rep-C at H ∈ {500, 1,000, 2,000}, each against `train.epochs` ∈ {500, 1,000, 2,000, 7,000} ≥ H, give identical `learning_rate`, `training_target` and `is_traced_epoch` for every epoch 0..H−1 (traced epochs 51 / 101 / 201). Not run: a few `run_training` steps at each restart boundary. This check shows that none of the three functions reads `train.epochs` before H; the RSS gate projection reads it by design |
| 6 | Bop \|m\| / flip-fraction measurement ([D15]) | **PENDING** (descriptive, needs training steps) | not built here |
| 7 | GPU memory canary per class; determinism probe | **PENDING** (GPU) | canary: `code/manifests/delta-canary-job.json` (next step below). Determinism probe (2 pods × 21 epochs per class): **not built**. No manifest exists |
| 8 | Diagnostics on vs off invariance | **PASS** (re-run, first 3 steps) | `preflight_checks.py`: `DIAG_ONOFF_PASS` for rep-A s1 and rep-C s1, removing `collapse_stop`, `accumulator_metric`: equal init kernel hashes, loss, EBOPs trace after each of 3 steps, kernel hashes after. Neither key acts inside a step (collapse stop: epoch-level after epoch 20; accumulator: logging), so this is the build/step half only |
| 9 | Always-on patches gated on the anchor tree | **PASS** | `accumulator-ebops-metric`, `screen-collapse-stop`, `diag-sign-flips`, `diag-beta-trajectory`: gated-on-anchor-42abed4b (README rows; invariance 19/19). The three readout modules `diag-attention`, `diag-input-proj-rows`, `diag-latent-binary-gap` were marked gated on the tarball only. Re-run against this extraction on PYTHONPATH (the modules are byte-identical to the shipped copies): `tests/test_diags.py tests/test_bop.py tests/test_linformer.py` → `10 passed` (`bundle/evidence/pytest_diags_bundle_e6fc6cd9.log`) |
| 10 | Order of launch | n/a for build | t0 packs (replicas) and cells packs (placebos after the replica gate) are separate Jobs; cluster-ops / RUN.md |
| 11 | Code base = leak-fixed regime-B 42abed4b + Delta series | **PASS** | `ANCHOR_BUNDLE_SHA_OK 42abed4b…`, 38 patches applied, `APPLY_ANCHOR_ALL_PASS`. Bundle e6fc6cd9, manifest 300be87b. f2107a04 / e90327d4 / 77f1ca4e are not in the build path |
| 12 | Pods and quota | **PENDING** (cluster-ops) | — |
| 13 | Non-binary path under [A20] | **FAIL, held back as designed** | 8 GATE_FAIL lines verbatim below; not packed. 15 NEEDS_TEACHER: W2 M027, M035, M036 (`after_teacher`, X1); 12 are W3 |
| 14 | Host-memory growth canary (RSS slope ≤ 5 MB/epoch/arm, E and A07) | **PENDING** (GPU); limits PASS | limits per pack, asserted by the freeze: H 500 → 4,600 MiB, 1,000 → 7,100, 1,500 → 9,600, 2,000 → 12,100 (2,100 + 5 × H, erratum 2026-09-28; env `BNJ_RSS_GATE_LIMIT_MB`, window `5:105`). Canary phases: E-k4 7,100, E-k5 7,100, A07-k3 12,100. The result (fitted slope per arm, E and A07) is recorded in RUN.md against bundle e6fc6cd9 / manifest 300be87b |
| 15 | GPU integer fingerprint before any arm (added 2026-09-28, REGRESSION_TICKET; Kai's decision 2026-09-28) | **PENDING** (GPU pods); CPU PASS | `fingerprint_check.py` in every Delta pod after `CACHE_READY`, before `run_pack.py`: rep-A s1 `initial_ebops` must equal 11,559,681, else exit 9. CPU: `bundle/evidence/fingerprint_cpu_bundle_705a554b.log`. Discriminator pods and canary-v2: section "Gate 15" at the end of this file |
| — | Strict keys (`validate_cfg`) on every shipped config | **PASS** (re-run) | `bundle/evidence/strict_keys_w2_bundle_e6fc6cd9.log`: `STRICT_SWEEP {'ok': 312, 'ok_packed': 240, 'ok_unpacked': 72}`, 0 refused |
| — | Cell/replica key diff (Arms "Cell configs" classes) | **PASS** (re-run) | independent recomputation, `bundle/evidence/keydiff_check.{py,log}`: 220 packed non-replica runs (204 single, 8 baseline M050, 8 placebo) against the replica at the same arm and seed. `KEYDIFF_DONE outside_classes 0`. The generator's `diff_outside_declared` is empty on all 548 rows that carry it |
| — | Placebo identity assertion (X2/Z13) | **PASS** (re-run) | `preflight_checks.py`: 8 × `PLACEBO_PASS`. P-350 s1-4 vs rep-A s1-4, P-5M s1-4 vs rep-C s1-4: `digest_json` equal after deleting `name`, `experiment.arm`, `delta_study`, `engram_study.question` and setting `train.epochs` 500; init `kernel_hashes` equal (15 / 16 tensors); first-step CPU loss bit-equal (e.g. `2.5554862022399902 2.5554862022399902`) |
| — | CPU build / one-step / reload per entry × arm | Cited 119/142 + re-run 7/7 | GATES.md §7 and "Configs" above. `gate_cpu.py` never prints `PREFLIGHT_ALL_PASS`, and the full index could not: 8 rows fail by design under [A20]. Equivalent here: 0 GATE_FAIL among packed runs. The anchor's `cpu_gate.py` (which prints the literal) was not run on this extraction |

**Nothing in this table blocks the memory canary.**
- The 8 gate-13 FAIL lines are the designed [A20] hold-back, and none of those runs is packed.
- M006 (the shadowing finding) is unpacked.
- Every PENDING item is GPU-side, PVC-side, or belongs to the orchestrator or Kai.

**Gate-13 lines, verbatim (GATES.md §7):**
```
GATE_FAIL configs/W2/M047-t350000-s1.json ValueError: delta0926-w2-m047-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M047-t5000000-s1.json ValueError: delta0926-w2-m047-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M048-t350000-s1.json ValueError: delta0926-w2-m048-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M048-t5000000-s1.json ValueError: delta0926-w2-m048-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M049-t350000-s1.json ValueError: delta0926-w2-m049-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M049-t5000000-s1.json ValueError: delta0926-w2-m049-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/prereq/P-T1-s101.json ValueError: delta0926-prereq-p-t1-s101: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/prereq/P-T2-s101.json ValueError: delta0926-prereq-p-t2-s101: act_overflow/softmax_quant need binary weights and act_calib='free'
```

**Excluded from this bundle's packs**, from `delta_w2_cells_packs.json` `unpacked` / `after_teacher`:
- M006, `floor_untraced` (gate 3a, X4);
- M009, M038, M040, M041, `cache_not_built` (gate 3c);
- M047, M048, M049, GATE_FAIL [A20] (gate 13, X5);
- M027, M035, M036, `after_teacher` (X1).

**Not re-run here (cited only):**
- the 142-pair gate;
- invariance 19/19;
- both slug-test sets;
- anchor pytest 99/2;
- floors 73/81;
- gen → classify → annotate byte-identity (GATES §7);
- `tests_patches/rss_slope_anchor_42abed4b.txt`.

## Arm table (STUDY arms → configs → Job and pack index)

Job indices are `JOB_COMPLETION_INDEX` = the pack index in that Job's packs file:
- t0 = `kai-delta0926-w2-t0` / `delta_w2_t0_packs.json`;
- cells = `kai-delta0926-w2-cells` / `delta_w2_cells_packs.json`;
- canary = `kai-delta0926-canary` / `delta_canary_packs.json`.

Configs are `campaigns/delta0926/configs/W2/<ID>-t<target>-s<seed>.json`. Seeds are 1-4 unless
stated. The packs are PLANNING, and the indices change when the packs are regenerated from
`k_result.json`.

| STUDY row | target | config | Job: pack indices |
| --- | --- | --- | --- |
| rep-A (drift replica, arm A, H 1,000) | 350k | `REP-A-t350000-s{1..8}` | t0: 0, 1; canary: 0 (s1-4), 1 (s1-5) |
| rep-A07-350 (H 500) | 350k | `REP-A07-350-t350000-s{1..4}` | t0: 2, 3 |
| rep-C (drift replica, arm C, H 2,000) | 5M | `REP-C-t5000000-s{1..8}` | t0: 4, 5, 6; canary: 2 (s1-3) |
| P-350 (placebo) | 350k | `P-350-t350000-s*` | cells: 18 |
| P-5M (placebo) | 5M | `P-5M-t5000000-s*` | cells: 19, 20 |
| FF M001 / M002 / M003 / M004 / M005 | 350k | `M00x-t350000-s*` | cells: 0-1 / 2-3 / 4-5 / 7-8 / 9-10 |
| M001 / M002 / M003 / M004 / M005 | 5M | `M00x-t5000000-s*` | cells: 21-22 / 23-24 / 25-26 / 55-56 / 57-58 |
| M006 (FF + 5M, Welch) | both | `M006-t*-s*` | **unpacked** (floor untraced) |
| M009 (FF + 5M, N=32) | both | `M009-t*-s*` | **unpacked** (cache not built) |
| M010 (A07, ladder) | 1.4M | `M010-t1400000-s*` | cells: 5, 6 |
| M008 / M011 / M012 / M039 | 350k | `M0xx-t350000-s*` | cells: 59 / 64 / 60 / 62 |
| M008 / M011 / M012 / M039 | 5M | `M0xx-t5000000-s*` | cells: 27-28 / 65-66 / 29-30 / 51-52 |
| M038 | both | `M038-t*-s*` | **unpacked** (cache not built) |
| M016 / M042 / M043 / M045 | 350k | `M0xx-t350000-s*` | cells: 67 / 70 / 73 / 78 |
| M016 / M042 / M043 / M045 | 5M | `M0xx-t5000000-s*` | cells: 68-69 / 71-72 / 74-75 / 79-80 |
| M040 | both | `M040-t*-s*` | **unpacked** (cache not built) |
| M013 | 350k | `M013-t350000-s*` | cells: 61 |
| M015 (H 1,000) | 350k / 5M | `M015-t*-s*` | cells: 11 / 12-13 |
| M007, M017-M026, M028-M030, M033, M034, M037 | 5M | `M0xx-t5000000-s*` | cells: M007 26-27, M017 30-31, M018 31-32, M019 33-34, M020 34-35, M021 35-36, M022 37-38, M023 38-39, M024 39-40, M025 41-42, M026 42-43, M028 43-44, M029 45-46, M030 46-47, M033 47-48, M034 49-50, M037 50-51 |
| M041 | 5M | `M041-t5000000-s*` | **unpacked** (cache not built) |
| M044 | 5M | `M044-t5000000-s*` | cells: 76-77 |
| M046 | 5M | `M046-t5000000-s*` | cells: 81-82 |
| M031 (H 1,500) / M032 (H 2,000) | 5M | `M031-…`, `M032-…` | cells: 14-15 / 16-17 |
| M027 / M035, M036 (teacher) | 5M | — | **after_teacher** (X1) |
| M047, M048 / M049 (baselines) | both | `M04x-t*-s*` | **unpacked**, GATE_FAIL [A20] (gate 13) |
| M050 (baseline) | 350k / 5M | `M050-t*-s*` | cells: 63 / 53-54 |

Pack indices overlap across rows (for example cells 26 holds M003-5M and M007) because pods
mix entries of one horizon and class.

**Open item for RUN.md (not fixed here; a `manifest_wave2.py` matter): replica seeds above n are
not stopped at 500 anywhere.** The STUDY's drift-replica table says rep-A runs to 1,000 and
rep-C to 2,000, and seeds above n = 4 stop at 500. Neither the configs nor the Job realizes that
stop:
- The configs of seeds 5-8 carry `train.epochs` 1,000 (rep-A) and 2,000 (rep-C).
- `delta-w2-t0-job.json` runs `python -u /work/code/run_pack.py delta_w2_t0_packs.json` with no
  stop-after argument.
- t0 pack 1 is rep-A s5-8, and pack 6 is rep-C s7-8. Pack 5 **mixes** rep-C s4 (to 2,000) with
  s5-s6 (to 500). A pod-wide `stop_after` cannot split that pack.

As shipped, seeds 5-8 would train to their full horizon unless they are stopped by hand at the
epoch-500 gate. Their RSS gate limits are sized for the full horizon (7,100 / 12,100 MiB).

## Next step for cluster-ops: the memory canary (gates 7 and 14)

> **Superseded 2026-09-28 (gate 15):** bundle 705a554b, ConfigMap `kai-delta0926-code-705a554b8d`, manifests `manifests/delta-canary-v2-job.json` and `manifests/discrim-*.json`; see "Gate 15 and the re-frozen bundle" at the end. The text below is the e6fc6cd9 record.

- **Job.** `campaigns/2026-09-26-delta/code/manifests/delta-canary-job.json` (`kai-delta0926-canary`).
  - One NVIDIA-A10 pod, 10 CPU / 36 Gi.
  - Phases E-k4 (rep-A s1-4), E-k5 (rep-A s1-5) and A07-k3 (rep-C s1-3), 110 epochs each.
  - Output `/data/delta-20260927/canary/k_result.json`.
  - Projection 8.35-10.43 GPU-hours (GATES §7; a projection).
- **It needs:**
  - **ConfigMap `kai-delta0926-code-e6fc6cd921`**, created from `bundle/configmap.json`, immutable.
    Before use, verify the annotation and the decoded payload sha.
  - The placeholders substituted in a copy of the manifest (the generated file stays a template):
    - `__CONFIGMAP_NAME__` → `kai-delta0926-code-e6fc6cd921`;
    - `__BUNDLE_SHA256__` → `e6fc6cd921d574f7ac153d597341b8f1c36db088f7cc9c91f5d59401c8d967fb`;
    - `__MANIFEST_SHA256__` → `300be87bf0cde5fba95c7b9cf0798718475e2b2dd6a230ee44a58a22fa8d467c`.
  - `/data/chang-n64-20260926/n64/data/READY.json` on `kai-data`. The header exits
    `CACHE_NOT_READY` otherwise.
- **After it.**
  1. Copy `k_result.json` to `code/k_result.json`.
  2. Run `manifest_wave2.py --k-result`.
  3. Re-freeze with `freeze_delta.py`: new bundle sha and ConfigMap for t0 and cells, same manifest sha.
- **Open (flag, not resolved here):** STUDY gate 14 says "one E and one A07 Delta **cell**". The
  canary runs the **replica** configs rep-A and rep-C: the same code and the same always-on keys,
  but no Delta lever on. Whether a replica counts as a "Delta cell" for gate 14 is the
  orchestrator's call.
- The t0 and cells Jobs carry the same three placeholders. They are not for this bundle: their
  packs change with `k_result.json`.

## cluster-ops — lint, ConfigMap, cluster sections (2026-09-28)

**Substituted manifest:** `campaigns/2026-09-27-delta-screen/manifests/delta-canary-job.json`,
placeholders filled from PREFLIGHT's own values (`kai-delta0926-code-e6fc6cd921`,
`e6fc6cd921d574f7ac153d597341b8f1c36db088f7cc9c91f5d59401c8d967fb`,
`300be87bf0cde5fba95c7b9cf0798718475e2b2dd6a230ee44a58a22fa8d467c`; verified no `__..__` tokens
remain outside the now-substituted `bnjettag.io/placeholders` annotation text).

`nrp_doctor.py lint` output on the substituted canary manifest, run immediately before apply:
```
== campaigns/2026-09-27-delta-screen/manifests/delta-canary-job.json :: kai-delta0926-canary ==
  WARN   backoffLimitPerIndex=1: one blip kills an index. Suggest 3.
  note   required pool = 1 products / 35 nodes cluster-wide
  note   [rule PACK] 5 arms per pod declared.

(rules: docs/infrastructure/nrp-nautilus-setup.md -> 'Scheduling, GPU pools and job shape')
```
**Not fixed, by design, not a mechanical mistake.** The manifest sets
`BNJ_ARM_RETRIES=0 BNJ_POD_STALL_RETRIES=0` with the comment "an OOM or a stall is the
measurement: never retried" — raising `backoffLimitPerIndex` would let Kubernetes itself retry a
failed index, contradicting the canary's own no-retry design. `[rule PACK]` note is informational
only (5 arms/pod, matches the E-k5 phase's declared K). No ERROR; the pre-apply hook does not
block on WARN.

**ConfigMap.** `kubectl apply -f bundle/configmap.json` failed:
`metadata.annotations: Too long: may not be more than 262144 bytes` — `apply` writes a
`kubectl.kubernetes.io/last-applied-configuration` annotation containing the whole object
(binaryData, ~446 KB base64), over the 256 KiB annotation cap. Used `kubectl create -f` instead
(the ConfigMap is `immutable: true`, no update-in-place is ever needed). Created
`kai-delta0926-code-e6fc6cd921` in `cms-ml`; `kubectl get cm ... -o jsonpath='{.metadata.annotations}'`
confirmed `bnjettag.io/bundle-sha256` = `e6fc6cd921...67fb` and `bnjettag.io/manifest-sha256` =
`300be87b...467c`, matching this file's values exactly.

**Cache confirmation (gate 3b/3d).** `kai-chang0926-cache-c5d6f0-bhrkh` (Completed, the anchor's
cache-build Job) log shows `[cache_ready] /data/chang-n64-20260926/n64/data` and
`DATA_INFO {"array_sha256": {... "y_val": "63049d9bdcfdc83af97c58bc6579e1def1ec2d9e7a6c30007793badd75217709"} ...}`,
byte-equal to the y_val sha named in this file's gate-3d row. Re-confirmed live from inside the
running canary pod (`kubectl exec kai-delta0926-canary-0-6q8kn -- python3 -c "..."` reading
`/data/chang-n64-20260926/n64/data/data_info.json`): same sha,
`63049d9bdcfdc83af97c58bc6579e1def1ec2d9e7a6c30007793badd75217709`, read 2026-09-28T09:21Z. The
canary's own header also printed `CACHE_READY` before starting any arm.

Full launch record, timestamps, node/GPU and the incident: `campaigns/2026-09-27-delta-screen/RUN.md`.

## W&B (cluster-ops, 2026-09-28, after the first canary attempt's incident)

- **Project existence/access.** Queried `kayamaguchi-uc-san-diego/BNJetTag-Delta` the same way
  the pod does (`run_engram.validate_tracking_destination`'s `EngramProjectAccess` GraphQL query,
  `wandb.sdk.internal.internal_api.Api.execute`, `WANDB_API_KEY` loaded from
  `bnjettag/wandb-api-key.txt` into an env var inline, never printed): first query returned
  `null` — the project did not exist, confirming the incident's cause. Created it PRIVATE via the
  `upsertModel` mutation with `access: PRIVATE` (same procedure as `BNJetTag-ChangRecipe`,
  training-batch PREFLIGHT.md l. 481-489), then **re-queried** with the identical
  `EngramProjectAccess` query (not the create call's own return):
  `{'name': 'BNJetTag-Delta', 'access': 'PRIVATE'}`. The project exists and is PRIVATE, confirmed
  via the pod's own check path.
- **Relaunch outcome (still gates 7/14 PENDING).** The W&B fix worked end to end (arms opened
  real W&B runs under `BNJetTag-Delta` this time), but every rep-A arm that reached a terminal
  state diverged to NaN at epoch 0 (training-code/recipe issue, out of scope here), and the pod
  running A07-k3 was killed and the whole Job deleted mid-phase by something other than
  cluster-ops before any outcome was recorded. Gates 7 and 14 remain **PENDING**. Full detail:
  `campaigns/2026-09-27-delta-screen/RUN.md` "Second incident".

## Where I am not sure

- DECISION: ship W2 configs only, with the full 582-row index. ALTERNATIVES: all 582 configs.
  That still fits: GATES §6 measured about 424 KB of tar, about 566 KB base64. It would let
  `run_study.py preflight` iterate the index. I chose W2 only per the brief.
- DECISION: gate 5 is PASS at function level and PENDING at step level; I do not call it a full
  PASS. ALTERNATIVE: a `run_training` smoke on CPU at each restart boundary (epochs 499/500),
  about 500 synthetic epochs per config. That was not affordable in the 15-minute budget.
- M006's GATES §7 record (see "Configs") needs the new-files owner to re-gate and trace M006 with
  the script outside `code/`, before M006 is packed.

## Gate 15 and the re-frozen bundle (fixer, 2026-09-28; prepared, nothing applied)

Source: `REGRESSION_TICKET.md` (epoch-0 NaN on `hcc-nrp-shor-c6017.unl.edu`, code and config cleared on
CPU) and Kai's decision of 2026-09-28 (`.claude/memory/decisions.md`): discriminate the node, gate every
pod, re-run the canary away from c6017. The sections above describe bundle e6fc6cd9 and stay as the
record of what the c6017 canary ran.

- **Gate 15.** `campaigns/2026-09-26-delta/code/fingerprint_check.py`, shipped as
  `/work/code/campaigns/delta0926/fingerprint_check.py`. It follows `run_study.train` →
  `ablation.run_training` (TF32 off, `validate_cfg`, `load_cache`, `set_random_seed`, `builder_for`,
  `delta_optimizer_for`, the initial `compute_ebops` trace on the full train split at batch 2,048) on
  the anchor cache `/data/chang-n64-20260926`, and prints `FINGERPRINT <v> expected 11559681`.
  Mismatch → `GPU_FINGERPRINT_MISMATCH <v>`, exit 9; no GPU visible → exit 8. With `--env-report` it
  first logs `nvidia-smi` (driver, GPU, ECC / retired / remapped counters), `/proc/driver/nvidia/version`,
  TF and Keras versions, `tf.sysconfig.get_build_info()` (CUDA / cuDNN) and `pip freeze`. No
  environment variable is printed.
- **Every Delta pod runs it first.** `manifest_wave2.py` `header()` appends `gate15_lines()`, so the
  t0, cells and canary templates all run it after `CACHE_READY` and before the first `run_pack.py`.
  A failure exits the pod before any `ARM_STARTED`.
- **CPU test** (pinned `tests_patches/pyenv.sh`, local rebuild of the anchor cache, x_train `420ac79d…`;
  a check, not a result). Evidence: `bundle/evidence/fingerprint_cpu_bundle_705a554b.log`.

  | tree | s1 | s2 |
  | --- | --- | --- |
  | pristine anchor 42abed4b (`chang0926-a-n64-s{1,2}`) | 11,559,681 | 11,295,521 |
  | deployed e6fc6cd9 (`delta0926-w2-rep-a-t350000-s{1,2}`) | 11,559,681 | 11,295,521 |
  | new 705a554b (script from its shipped path) | 11,559,681 | 11,295,521 |

  The refusal paths also work: without `--allow-cpu` → `GPU_FINGERPRINT_NO_GPU`, exit 8; `--expect 1` →
  `GPU_FINGERPRINT_MISMATCH 11559681`, exit 9.
- **Bundle re-frozen** with `bundle/freeze_delta.py`. It now ships `fingerprint_check.py` and the
  configs and packs of 1fd9558 (extension replica seeds 5-8 stop at 500, single-horizon t0 packs,
  M006 gate-import fix), plus canary packs whose run roots are `/data/delta-20260927/canary-v2/<phase>`.
  - Bundle sha256 **705a554b8da0395bf015a60743a0ea97304ecb9261c3a43d8619404f5c4c6f98**: 337,511 bytes,
    base64 450,016 bytes (limit 1,048,576; `configmap.json` 450,610 bytes), 577 files.
  - ConfigMap **`kai-delta0926-code-705a554b8d`** (`bundle/configmap.json`, immutable).
  - `run_study.manifest()` sha256 **300be87bf0cde5fba95c7b9cf0798718475e2b2dd6a230ee44a58a22fa8d467c**,
    unchanged: `campaigns/` is outside the manifest. `diff -rq` of the e6fc6cd9 and 705a554b
    extractions differs only under `campaigns/delta0926/`.
  - index sha256 8a6f262f…d3d2. Packs (packs, arms): canary 3 / 12, t0 8 / 20, cells 87 / 228.
  - e6fc6cd9 is kept beside it: `bundle/{delta-code-e6fc6cd9.tar.gz,configmap-e6fc6cd9.json,bundle-manifest-e6fc6cd9.json}`.
  - Re-run on the 705a554b extraction: `preflight_checks.py` → `PREFLIGHT_CHECKS {"cache": true, "diag":
    true, "horizon": true, "placebo": true}` (`bundle/evidence/preflight_checks_bundle_705a554b.log`).
    `gate_cpu`, invariance and pytest were not re-run, because the code tree is byte-identical to e6fc6cd9.
- **Manifests** in `manifests/`, all built by `manifests/build_gate15_manifests.py` from the generated
  template and `bundle-manifest.json`:
  - `discrim-c6017-job.json` (`kai-delta0926-discrim-c6017`): required `kubernetes.io/hostname In
    hcc-nrp-shor-c6017.unl.edu`, A10.
  - `discrim-other-job.json` (`kai-delta0926-discrim-other`): A10, `NotIn` c6017, preferred
    `hcc-nrp-shor-c5825.unl.edu`.

  Each discriminator runs one GPU for at most 1 h (`backoffLimit 0`) and trains nothing. It logs the env
  report, then runs rep-A s1 and s2 twice each as four separate processes, writing logs to
  `/data/delta-20260927/discriminator/<job>-<UTC>/`. It exits 9 if any reading mismatched. It mounts no
  W&B secret. The `imageID` cannot be read inside the pod; cluster-ops reads it with the command in
  the `bnjettag.io/cluster-ops-read` annotation.
  - `delta-canary-v2-job.json` (`kai-delta0926-canary-v2`): the regenerated canary with gate 15 and
    `NotIn hcc-nrp-shor-c6017.unl.edu`. Run root `/data/delta-20260927/canary-v2`. The loud phase
    failure (`FAIL=1`, exit 7) is now in the generator. Phases follow the current packs: E-k4 rep-A
    s1-4 (7,100 MiB), E-k5 P-350 s1-4 + rep-A s5 (H 500, 4,600 MiB), A07-k3 rep-C s1-3 (12,100 MiB).
  - Offline checks: `bash -n` passes on all three wrappers. `KUBECONFIG=/nonexistent nrp_doctor.py lint`
    reports only what an offline run cannot see: "NO product … reachable" and "NVIDIA-A10 matches no
    node", because there is no node list. It also warns `backoffLimitPerIndex=1` on the canary, which
    is kept by design (see the cluster-ops section above). No PACK or known-bad-node finding.
    cluster-ops runs the online lint before apply.
- **Deviations from the ticket's text.** This section amends PREFLIGHT.md in place (the task's instruction)
  instead of the `PREFLIGHT_v2.md` of ticket §6. The discriminators run bundle 705a554b, not e6fc6cd9 (§3
  item 1): its code tree is byte-identical, so a "both fail → stack drift" reading is unaffected.
- **Reading the c6017 discriminator.** `backoffLimit 0` with `activeDeadlineSeconds 3600`: if c6017's GPU
  is occupied, the pod stays Pending and the Job ends DeadlineExceeded without running. That means
  *node busy*, not *node bad*. Re-apply later.
- **Status: PENDING** until the discriminator pods and the canary-v2 log show `FINGERPRINT … expected
  11559681` and `GATE15_PASS` before any `ARM_STARTED`.
- **Open, for cluster-ops / Kai (not fixed here):**
  - **W&B id collision.** `stage_run_id = sha256(stage \0 name)`. canary-v2 reuses stage `canary` for
    rep-A s1-4 and rep-C s1-3, so those arms resume (`resume='allow'`) the c6017 runs in
    `BNJetTag-Delta` that the ticket says to label `invalid-node`. Only `pilot-b` is unused, and there are
    three phases. Before apply, annotate those runs or accept the append. Avoiding the collision needs
    a code change.
  - **Pod-level epoch-0 divergence.** The ticket's rule that all arms of a pack diverging at epoch 0 is
    one pod failure is not implemented. That change belongs in `run_pack.py`, a manifest-sha file; route
    it to the Delta ml-engineer. Gate 15 catches the observed failure earlier.
  - The ConfigMap must be created with `kubectl create -f`, not `apply`, because of the 256 KiB
    annotation cap (cluster-ops section above).

## Discriminator result (cluster-ops, 2026-09-28)

Both Jobs ran to Complete: `kai-delta0926-discrim-c6017` (pod `kai-delta0926-discrim-c6017-g6znq`,
node `hcc-nrp-shor-c6017.unl.edu`) and `kai-delta0926-discrim-other`
(pod `kai-delta0926-discrim-other-z78sn`, node `hcc-nrp-shor-c5809.unl.edu`, not c5825 — the
preferred node was unavailable, `NotIn c6017` still satisfied). Full logs copied:
`logs/discrim-c6017-g6znq-20260928.log`, `logs/discrim-other-z78sn-20260928.log`.

| | c6017 | other (c5809) |
| --- | --- | --- |
| GPU | NVIDIA A10, UUID `GPU-cad1b289-db88-68e2-f44d-178aa90abf3e`, 23,028 MiB | NVIDIA A10, UUID `GPU-e16bd8e9-e8ff-14da-eca9-df94d723829a`, 23,028 MiB |
| Driver | 595.71.05 | 595.91.07 |
| CUDA (nvidia-smi) | 13.2 | 13.2 |
| TF build info | `cuda_version 12.5.1, cudnn_version 9, is_cuda_build true` | identical |
| ECC (SRAM/DRAM correctable+uncorrectable, remapped rows) | all 0 | all 0 |
| pip freeze | `diff` against other node: **identical** | — |
| s1 FINGERPRINT (×2) | `11559681 expected 11559681` both times, `FINGERPRINT_OK` | same |
| s2 FINGERPRINT (×2) | `11295521 expected 11295521` both times, `FINGERPRINT_OK` | same |

**Reading.** Single-process, gate-15-only runs on c6017 are healthy: correct fingerprint,
reproducible across two repeats each of s1 and s2, ECC clean, driver/CUDA/TF stack and pip
freeze identical to the other node. This clears c6017 as "bad" in the single-process sense and
narrows the canary's original epoch-0 NaN to something that only shows up with **4-5 concurrent
training processes sharing the one GPU** (the canary's actual pod shape), which this
discriminator does not exercise. Node exclusion (`NotIn hcc-nrp-shor-c6017.unl.edu`) is kept in
`delta-canary-v2-job.json` as a precaution per Kai's decision, not because this result proves the
node bad — see REGRESSION_TICKET.md §8 and cluster-inventory.md for the concurrency-fault framing.
Both discriminator Jobs deleted after evidence capture (2026-09-28, cluster-ops).


## In-pod cache checks (orchestrator, 2026-09-29T03:00Z; gates 3b and 3d)

Both reads come from the anchor's running regime-B pilot pods, which mount the same `kai-data` PVC
that every Delta Job reads. Neither read writes anything.
- **3b, PVC presence.** Both anchor pilot-b pods (`kai-chang0926-pilotb5-42abed-0-qqjmt`,
  `kai-chang0926-pilotb3-42abed-0-vqxc7`) got past their header's
  `test -f /data/chang-n64-20260926/n64/data/READY.json || { echo "CACHE_NOT_READY"; exit 1; }` and
  are training on that cache. `/data/delta-20260927/` holds `canary`, `canary-v2` and
  `discriminator`.
- **3d, y_val.**
  `kubectl -n cms-ml exec kai-chang0926-pilotb3-42abed-0-vqxc7 -- python3 -c 'import json; d=json.load(open("/data/chang-n64-20260926/n64/data/data_info.json")); print(d["array_sha256"]["y_val"])'`
  returned `63049d9bdcfdc83af97c58bc6579e1def1ec2d9e7a6c30007793badd75217709`, the gate's value
  (63049d9b…7709).
