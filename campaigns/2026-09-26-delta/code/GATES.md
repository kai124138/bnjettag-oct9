# GATES.md — new-files gates (generator, classification, manifest, modules, CPU gate)

**GPU policy update, 2026-09-28 (Kai):** the A10-only canary text below documents the earlier
generator and launched A10 measurements. New product candidates and production manifests follow
[the GPU selection policy](../../../docs/infrastructure/gpu-selection-policy.md). Use
`manifest_wave2.py --gpu-product <exact-node-label> --out <new-directory>` for a product-specific
planning canary. The resulting production Jobs remain PLANNING until a full pack-size,
throughput, utilization, fingerprint and certification gate is recorded for that product.
Freeze those packs with `campaigns/2026-09-27-delta-screen/bundle/freeze_delta.py
--packs-dir <new-directory> --out-dir <new-bundle-directory>`; fill the generated Job's bundle
placeholders from that new bundle and re-lint. The baseline K=4/5/3 canary is only the first
measurement on a larger card. A product-specific `k_result.json` needs a reviewed
`gpu_policy_certified: true` and matching `gpu_product` after the K search before production
templates cease to be PLANNING.

Laptop, CPU only, synthetic inputs. Nothing here is a result. The EBOPs figures are initialization
traces on synthetic data.

**Environment:** `uv run --python 3.12 --no-project` with the bundle's `requirements-cpu.txt` pins:
- tensorflow 2.21.0, keras 3.15.0, hgq2 0.1.9 (wheel sha256 749754214b97...c43c);
- quantizers 1.2.2, numpy 2.5.0, scikit-learn 1.9.0, h5py 3.14.0, hls4ml 1.3.0;
- plus pytest.

**Trees:**
- Bundle: `study-code.tar.gz`, sha256 26f3cc40...5a45.
- "Full tree": `code/apply.sh` = tarball + patches 0001-0024 + `newmods/` (APPLY_ALL_PASS).

## 1. Generator (`gen_atlas.py`) and classification (`classify_series.py`), v4

atlas.json sha256 6fbd4b5d8edadbca3817b8ef6a03dad1a714b0f6bc97b370429a6210da3c3711.

**Base: still the stand-in** `const0922-a07-n64-s1-fast50-fp32.json`.
- The anchor tree (training-batch code, 72a1290) is staged, but it has no arm-A config and no final sha.
- The [D21] arms, `drift_replicas`, always-on keys and value maps are as in v3.

**New in v4:**
- `hw_labels` is copied into every index row.
- Every run name carries the wave token, e.g. `atlas0926-standin-w3-rep-c-t5000000-s1` (B1-v3).
- `gen_atlas.py` raises if any two names collide. Result: `n_run_names` 566, `run_names_unique` true; the W2 and W3 replica names are now distinct.
- `--help` has the [D21] wording (C1).

Strict run:

```
tier=screen stand_in_base=True base_sha256=5d802cddeebe atlas_sha256=6fbd4b5d8eda
cells by wave (incl. drift replicas): {'W2': 296, 'W3': 268}
status: {'needs_patches': 374, 'placeholder_pending_anchor': 96, 'ready_on_base': 96} configs written: 566
```

That generator status is provisional. `classify_series.py --tree <apply.sh build>/code` then runs the full
tree's own validator (`run_engram.validate_cfg` → `atlas_keys.validate` → `strict_keys`, patch 0022) on every
written config and rewrites `status`. The validator is the ground truth:

```
series status: {'ready_on_base': 96, 'refused_by_key': 232, 'runnable_on_series': 160, 'placeholder_pending_anchor': 78}
REFUSED arch.attn_kind: attn-linformer (blocked on [A20]) / attn-relu-over-n (blocked on [A20]) :: M004,M005,M053,M054,M056,M059,M060
REFUSED arch.derived_features: derived-input-features (blocked on [A3]/[A4]) :: M040,M067,M080,M081,M085,M086,M087,M091,M092,M093,M095
REFUSED arch.mask_gated_keys: gated-key-mask (blocked on [A3]/[A4]) :: M039,M077,M079
REFUSED data.std_scope: std-real-slots (blocked on [A3]/[A4]) :: M041
REFUSED quant.act_f0: act-init-f0 (blocked on [A20]) :: M012,M099,M100
REFUSED quant.act_granularity: act-granularity-element (blocked on [A20]) :: M011,M065,M096,M097,M098,M102
REFUSED quant.ebops_group_weight: ebops-group-weight (blocked on [A20]) :: M008,M057
REFUSED quant.pre_quant_shift: pre-quant-shift (blocked on [A20]) :: M026,M066
REFUSED quant.qk_min_bits: qk-stream-min-bits (blocked on [A20]) :: M007,M055
REFUSED quant.softmax_table_min_bits: softmax-table-min-bits (blocked on [A20]) :: M003,M051,M052
REFUSED train.lr_warmup_epochs: lr-schedule-variants (blocked on [A1]) :: M030
```

**Status by entry:**
- **ready_on_base** (14 entries, 96 cells): M001, M002, M009, M010, M013, M015, M042-M044, M046, M058, and the replicas REP-A, REP-A07-350, REP-C.
- **runnable_on_series** (33 entries, 160 cells): M006, M016-M025, M027, M034-M037, M045, M047-M050, M061-M064, M082-M084, M088-M090, M094, M101.
- **refused_by_key** (41 entries, 232 cells): the key and slug of each refusal are listed above and stored per row in `series_refusal`.
- **placeholder_pending_anchor** (19 ids, 78 cells):
  - M031, M032, M033, M038, M068-M076, M078, M103: the validator refuses an anchor key (`train.lr_cycle_epochs`, `train.lr_m_mul`, `train.optimizer`, `arch.pt_gate_gev`).
  - M028, M029 and the teachers P-T1, P-T2: the validator accepts, but the atlas reads the key with anchor semantics (`train.lr` as the cosine peak; the teachers need the anchor base).

**Caveats:**
- "runnable_on_series" means the validator accepts the config. It does not say the cell runs; §4 says which ones build and step.
- 11 runnable entries need the P-T1/P-T2 teacher artifact.
- M018 fails the binary gate (§4).

## 2. Wave-2 manifest (`manifest_wave2.py`) and lint, v4

The packer refuses an unclassified index. It packs only `ready_on_base` and `runnable_on_series` rows:

```
packs=32 arms=188 unpacked=108 K=6
  excluded placeholder_pending_anchor [arch.pt_gate_gev]: 1 entries M038
  excluded placeholder_pending_anchor [train.lr_cycle_epochs]: 1 entries M032
  excluded placeholder_pending_anchor [train.lr_m_mul]: 1 entries M031
  excluded placeholder_pending_anchor [train.optimizer]: 1 entries M033
  excluded placeholder_pending_anchor [None]: 2 entries M028,M029
  excluded refused_by_key [arch.attn_kind]: 2 entries M004,M005
  excluded refused_by_key [arch.derived_features]: 1 entries M040
  excluded refused_by_key [arch.mask_gated_keys]: 1 entries M039
  excluded refused_by_key [data.std_scope]: 1 entries M041
  excluded refused_by_key [quant.act_f0]: 1 entries M012
  excluded refused_by_key [quant.act_granularity]: 1 entries M011
  excluded refused_by_key [quant.ebops_group_weight]: 1 entries M008
  excluded refused_by_key [quant.pre_quant_shift]: 1 entries M026
  excluded refused_by_key [quant.qk_min_bits]: 1 entries M007
  excluded refused_by_key [quant.softmax_table_min_bits]: 1 entries M003
  excluded refused_by_key [train.lr_warmup_epochs]: 1 entries M030
  H=500: 29 pods, arms per pod [6 x 28, 4]
  H=1000: 2 pods, arms per pod [6, 6]
  H=2000: 1 pods, arms per pod [4]
```

**Packing caveats:**
- **Packed but not ready:** M018 (4 arms; fails the binary gate, §4) and M027, M035, M036 (12 arms; need the P-T1 teacher). Exclude them, or build the teacher first, before any launch.
- **Unchanged from v3:** the manifest placeholders (ConfigMap, bundle sha, W&B project, deadline) and the two runtime gaps (packs format; hard-coded output root).
- **Replica pods:** the replicas now have wave-unique names, which fixes B1-v3's directory collision. The output root is still shared by all waves.

Lint, offline (`KUBECONFIG=/nonexistent/kubeconfig`, JSON manifest), exit 2:

```
  ERROR  NO product in the required list is reachable: the pod requests nvidia.com/gpu but every listed product needs a different resource name. This job can never schedule.
  WARN   required-list product(s) match no node in the cluster (typo, or the hardware is gone): NVIDIA-GeForce-RTX-4090, ... (the 16 products of the 09-22 screen list)
  WARN   parallelism=10 but completions=32: at most 10 run at once. This is a self-imposed ceiling, not a cluster limit.
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 6 arms per pod declared.
```

The ERROR and the first WARN are the empty-node-map artefact (the check runs after it has been disabled).
The orchestrator re-lints with cluster access.

## 3. New modules: CPU tests (`tests/`, synthetic, a few steps)

```
13 passed, 190 warnings in 10.36s
```

| test file | tests | what is asserted |
| --- | --- | --- |
| test_deepsets.py | 3 | the builder gives exactly two symmetric non-zero values per binary layer, on the expected layer set; permutation invariance (atol 1e-5); one Adam step through `ablation.make_epoch_step`, weights move, gate holds; save/reload within 1e-7 and equal EBOPs; dims validation |
| test_bop.py | 4 | the exact flip rule on a hand-made case; no flip below tau; gamma/tau required; on the stand-in (N=8): same `optimizer.variables` length as Adam, flips happen, binary gate holds, per-layer mean \|w-alpha\| within 5 %, Adam variables move. gamma/tau values are test-only |
| test_linformer.py | 2 | E, F kernels (N, k) binary; scores (B, H, N, k); gradient reaches E; one step; gate; EBOPs finite; save/reload within 1e-7 |
| test_diags.py | 4 | entropy ratio = 1 for uniform and 0 for one-hot; masked keys renormalized; ablation changes outputs and the model is restored after the context; distinct sign rows on a known matrix; the sign of `input_proj.qkernel` equals the diagnostic's q; the latent context changes outputs and restores the binary forward (gate holds) |

## 4. CPU build / one-step / reload gate (`gate_cpu.py`), v4, full tree (tarball + 0001-0024)

**Set gated:**
- M004, M006 and M020 explicitly;
- one config (seed 1, first target) per entry the validator accepts (ready_on_base and runnable_on_series);
- the three W2 replicas.

**The harness now mirrors the runner's step** (`ablation.run_training`, full tree):
- the optimizer comes from `ablation.atlas_optimizer_for`, so Bop is exercised;
- it passes `input_std` (synthetic data: mu 0, sigma 1), the reflection signs for augmentation, and the LatentEMA;
- it calls `qat.set_atlas_epoch`.
- A config the validator refuses prints `GATE_REFUSED`.
- A KD or warm-start config prints `GATE_NEEDS_TEACHER`, because the runner loads a teacher artifact that does not exist yet.
- An earlier run of this harness passed KD cells against a zero teacher; that masking is removed.

```
GATE_REFUSED atlas0926-standin-w2-m004-t350000-s1 atlas0926-standin-w2-m004-t350000-s1: config key arch.attn_kind is refused: attn-linformer (blocked on [A20]) / attn-relu-over-n (blocked on [A20])
GATE_PASS atlas0926-standin-w2-m006-t350000-s1 params 20742 build 0.38s step 1.08s save_reload 0.24s wall 1.78s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m020-t5000000-s1 params 12788 build 1.65s step 1.81s save_reload 0.60s wall 4.17s max_abs 0 opt BopAdam
GATE_PASS atlas0926-standin-w2-m001-t350000-s1 params 12788 build 1.33s step 1.57s save_reload 0.46s wall 3.48s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m002-t350000-s1 params 12788 build 1.22s step 1.60s save_reload 0.43s wall 3.38s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m006-t350000-s1 params 20742 build 0.26s step 0.91s save_reload 0.23s wall 1.51s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m009-t350000-s1 params 10740 build 1.03s step 1.48s save_reload 0.40s wall 3.03s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m010-t1400000-s1 params 12788 build 1.64s step 1.63s save_reload 0.54s wall 3.99s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m013-t350000-s1 params 7148 build 1.29s step 1.58s save_reload 0.47s wall 3.51s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m015-t350000-s1 params 7148 build 1.27s step 1.60s save_reload 0.44s wall 3.49s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m016-t350000-s1 params 7444 build 1.48s step 1.89s save_reload 0.50s wall 4.07s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m017-t5000000-s1 params 12788 build 1.61s step 1.63s save_reload 0.50s wall 3.96s max_abs 0 opt Adam
GATE_FAIL configs/W2/M018-t5000000-s1.json AssertionError: Binary gate failed
GATE_PASS atlas0926-standin-w2-m019-t5000000-s1 params 12788 build 1.64s step 1.66s save_reload 0.52s wall 4.05s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m020-t5000000-s1 params 12788 build 1.64s step 1.64s save_reload 0.51s wall 4.03s max_abs 0 opt BopAdam
GATE_PASS atlas0926-standin-w2-m021-t5000000-s1 params 12788 build 1.62s step 1.67s save_reload 0.51s wall 4.04s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m022-t5000000-s1 params 12797 build 1.67s step 1.76s save_reload 0.52s wall 4.22s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m023-t5000000-s1 params 12788 build 1.64s step 1.66s save_reload 0.52s wall 4.09s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m024-t5000000-s1 params 12820 build 1.66s step 1.66s save_reload 0.52s wall 4.11s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m025-t5000000-s1 params 13049 build 1.70s step 1.77s save_reload 0.53s wall 4.29s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w2-m027-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w2-m034-t5000000-s1 params 12788 build 1.66s step 1.75s save_reload 0.51s wall 4.22s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w2-m035-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w2-m036-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w2-m037-t5000000-s1 params 12788 build 1.64s step 1.65s save_reload 0.51s wall 4.09s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m042-t350000-s1 params 4196 build 1.20s step 1.55s save_reload 0.43s wall 3.49s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m043-t350000-s1 params 8812 build 0.72s step 1.67s save_reload 0.45s wall 3.17s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m044-t5000000-s1 params 19947 build 3.04s step 3.00s save_reload 0.94s wall 7.41s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m045-t350000-s1 params 9726 build 1.37s step 1.75s save_reload 0.48s wall 3.97s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m046-t5000000-s1 params 10740 build 1.62s step 1.64s save_reload 0.51s wall 4.16s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m047-t350000-s1 params 7148 build 1.25s step 1.53s save_reload 0.43s wall 3.60s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m048-t350000-s1 params 7112 build 1.40s step 1.66s save_reload 0.47s wall 3.93s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m049-t350000-s1 params 20945 build 1.42s step 1.93s save_reload 0.47s wall 4.22s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m050-t350000-s1 params 7148 build 1.31s step 1.54s save_reload 0.44s wall 3.70s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w3-m058-t350000-s1 params 10740 build 1.02s step 1.47s save_reload 0.39s wall 3.30s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m061-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m062-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m063-t5000000-s1 needs prerequisite teacher artifact 'teacher-int8-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m064-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m082-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m083-t5000000-s1 params 5220 build 1.56s step 1.66s save_reload 0.51s wall 4.13s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w3-m084-t5000000-s1 params 12788 build 1.73s step 1.68s save_reload 0.53s wall 4.38s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m088-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m089-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m090-t5000000-s1 params 5220 build 1.55s step 1.62s save_reload 0.50s wall 4.13s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m094-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m101-t350000-s1 params 10022 build 1.63s step 2.32s save_reload 0.60s wall 5.00s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-a-t350000-s1 params 7148 build 1.33s step 1.55s save_reload 0.45s wall 3.84s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-a07-350-t350000-s1 params 12788 build 1.67s step 1.67s save_reload 0.52s wall 4.34s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-c-t5000000-s1 params 12788 build 1.63s step 1.66s save_reload 0.51s wall 4.29s max_abs 0 opt Adam
GATE_SOME_FAILED 37/50
```

2 min 42 s wall.

**Outcome:**
- **M004:** refused by the validator, naming attn-linformer, as expected.
- **M006:** passes at 20,742 parameters. That is the Deep Sets body, not the A07 12,788.
- **M020:** passes with **BopAdam** at 12,788 parameters. An optimizer adds no parameters, so the count equals the C base it runs on. The optimizer class is the evidence that Bop is wired.
- **M018 FAILS the binary gate after one step. This is a real defect in patch 0003 (ste-variants, `clip_identity`), not a harness issue:**
  - the forward `wg + stop_gradient(q*beta - wg)` leaves float rounding;
  - after one step each layer shows 4-6 distinct values within an ulp of ±beta;
  - e.g. `bit_block_0_attn_Wq`: -0.15526286, -0.15526284, -0.15526283, 0.15526283, …;
  - the slug test passes because it does not step and then gate;
  - suggested fix (patches engineer): return `stop_gradient(q*beta) + (wg - stop_gradient(wg))`, which is exact in the forward.
- **11 entries NEED_TEACHER:** M027, M035, M036, M061-M064, M082, M088, M089, M094.
- **Everything else, 37 configs: GATE_PASS**, with bit-identical reloads (`max_abs 0`).

## 4b. Gate re-run after the 0003 fix (v5)

- **Tree:** apply.sh rebuilt with 0003 re-exported (sha256 2dfafdff...) (APPLY_ALL_PASS).
- **Configs gated:** one config per entry the validator accepts. Results are in `code/gate_results.json`, and the per-row `gate_v5` field is in index.json.

```
GATE_PASS atlas0926-standin-w2-m001-t350000-s1 params 12788 build 1.46s step 1.71s save_reload 0.45s wall 14.03s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m002-t350000-s1 params 12788 build 1.20s step 1.49s save_reload 0.41s wall 3.19s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m006-t350000-s1 params 20742 build 0.27s step 0.89s save_reload 0.23s wall 1.47s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m009-t350000-s1 params 10740 build 1.02s step 1.46s save_reload 0.39s wall 2.98s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m010-t1400000-s1 params 12788 build 1.59s step 1.61s save_reload 0.50s wall 3.86s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m013-t350000-s1 params 7148 build 1.27s step 1.51s save_reload 0.43s wall 3.36s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m015-t350000-s1 params 7148 build 1.27s step 1.52s save_reload 0.43s wall 3.37s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m016-t350000-s1 params 7444 build 1.47s step 1.86s save_reload 0.49s wall 3.99s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m017-t5000000-s1 params 12788 build 1.60s step 1.60s save_reload 0.50s wall 3.90s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m018-t5000000-s1 params 12788 build 1.64s step 1.63s save_reload 0.51s wall 3.99s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m019-t5000000-s1 params 12788 build 1.64s step 1.65s save_reload 0.51s wall 4.02s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m020-t5000000-s1 params 12788 build 1.64s step 1.63s save_reload 0.51s wall 4.00s max_abs 0 opt BopAdam
GATE_PASS atlas0926-standin-w2-m021-t5000000-s1 params 12788 build 1.61s step 1.64s save_reload 0.50s wall 4.00s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m022-t5000000-s1 params 12797 build 1.68s step 1.75s save_reload 0.52s wall 4.21s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m023-t5000000-s1 params 12788 build 1.64s step 1.66s save_reload 0.51s wall 4.08s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m024-t5000000-s1 params 12820 build 1.62s step 1.64s save_reload 0.51s wall 4.03s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m025-t5000000-s1 params 13049 build 1.68s step 1.77s save_reload 0.52s wall 4.25s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w2-m027-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w2-m034-t5000000-s1 params 12788 build 1.61s step 1.67s save_reload 0.51s wall 4.05s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w2-m035-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w2-m036-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w2-m037-t5000000-s1 params 12788 build 1.61s step 1.65s save_reload 0.51s wall 4.04s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m042-t350000-s1 params 4196 build 1.20s step 1.51s save_reload 0.43s wall 3.42s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m043-t350000-s1 params 8812 build 0.73s step 1.53s save_reload 0.44s wall 3.00s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m044-t5000000-s1 params 19947 build 3.05s step 2.98s save_reload 0.93s wall 7.34s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m045-t350000-s1 params 9726 build 1.37s step 1.76s save_reload 0.50s wall 3.97s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m046-t5000000-s1 params 10740 build 1.65s step 1.74s save_reload 0.51s wall 4.24s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m047-t350000-s1 params 7148 build 1.25s step 1.50s save_reload 0.43s wall 3.61s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m048-t350000-s1 params 7112 build 1.39s step 1.66s save_reload 0.47s wall 3.89s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m049-t350000-s1 params 20945 build 1.40s step 1.88s save_reload 0.47s wall 4.14s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m050-t350000-s1 params 7148 build 1.31s step 1.54s save_reload 0.44s wall 3.69s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w3-m058-t350000-s1 params 10740 build 1.02s step 1.46s save_reload 0.39s wall 3.26s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m061-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m062-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m063-t5000000-s1 needs prerequisite teacher artifact 'teacher-int8-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m064-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m082-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m083-t5000000-s1 params 5220 build 1.54s step 1.63s save_reload 0.50s wall 4.06s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w3-m084-t5000000-s1 params 12788 build 1.66s step 1.66s save_reload 0.52s wall 4.27s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m088-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m089-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m090-t5000000-s1 params 5220 build 1.50s step 1.61s save_reload 0.50s wall 4.01s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m094-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m101-t350000-s1 params 10022 build 1.68s step 2.13s save_reload 0.55s wall 4.85s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-a-t350000-s1 params 7148 build 1.34s step 1.60s save_reload 0.48s wall 3.88s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-a07-350-t350000-s1 params 12788 build 1.68s step 1.71s save_reload 0.55s wall 4.40s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-c-t5000000-s1 params 12788 build 1.69s step 1.68s save_reload 0.52s wall 4.36s max_abs 0 opt Adam
GATE_SOME_FAILED 36/47
```

- **M018 now passes.** The step is followed by `ablation.binary_gate`, which requires exactly two symmetric
  non-zero values per binary layer.
- **Nothing else moved.** The other 35 passing entries are identical to v4 in every field compared:
  parameter count, EBOPs before and after the step, step loss/CE/KD/accuracy, and optimizer class.
  v4's 37 passes counted M006 and M020 twice.
- **Totals:** 36 pass, 11 need a teacher, and 0 fail.

**Wave-2 packs (v5)**, re-linted offline with exit 2 (the empty-node-map artefact, as in §2; WARN parallelism 10 of 30):

```
packs=30 arms=176 unpacked=108 K=6
  after P-T1 (teacher-fp32-a07): 2 packs, 12 arms, entries M027,M035,M036 (not in the Job manifest)
  needs a teacher, other waves (not packed here): M061,M062,M063,M064,M082,M088,M089,M094
  H=500: 27 pods [6 x 26, 4]; H=1000: 2 pods [6, 6]; H=2000: 1 pod [4]
```

- **Teacher-dependent cells:** the packer moves every cell whose entry gated as GATE_NEEDS_TEACHER into
  `after_teacher` in `manifests/atlas_w2_packs.json`, with the dependency stated. Those cells need P-T1
  (`teacher-fp32-a07`, ATLAS.md §3.4). They are not in the Job manifest.
- **W3 teacher dependencies:** M061-M064, M082, M088, M089 and M094. M063 needs P-T2 (`teacher-int8-a07`); the rest need P-T1.
- **M018** is in the main packs.

## 4c. Review v4 items (B1-v4, B2-v4, C1-v4), final regeneration

- **atlas.json** sha256 8b1c3aa6b1b584236345ba7d2ed54f6f518d1b0548440cad913b7aa891481265 (the M006, M020 and
  M071 notes changed; no schema change). The strict generator is unchanged: 566 configs, and the status and
  classification counts equal §1.
- **Tree:** `apply.sh`, tarball plus 0001-0024 (APPLY_ALL_PASS).

**C1-v4.** `gate_cpu.py --one-per-arm` gates one config per (entry, base arm), at seed 1 of that arm's
first cell, so every architecture a packed cell runs on is built. The run writes `code/gate_results.json`,
61 pairs:

```
GATE_PASS atlas0926-standin-w2-m001-t350000-s1 params 12788 build 1.56s step 1.84s save_reload 0.47s wall 13.72s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m001-t5000000-s1 params 12788 build 1.41s step 1.65s save_reload 0.46s wall 3.63s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m002-t350000-s1 params 12788 build 1.24s step 1.60s save_reload 0.42s wall 3.40s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m002-t5000000-s1 params 12788 build 1.24s step 1.63s save_reload 0.42s wall 3.44s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m006-t350000-s1 params 20742 build 0.30s step 0.98s save_reload 0.25s wall 1.66s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m006-t5000000-s1 params 20742 build 0.27s step 0.96s save_reload 0.24s wall 1.59s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m009-t350000-s1 params 10740 build 1.06s step 1.56s save_reload 0.40s wall 3.17s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m009-t5000000-s1 params 10740 build 1.06s step 1.59s save_reload 0.40s wall 3.22s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m010-t1400000-s1 params 12788 build 1.66s step 1.73s save_reload 0.53s wall 4.12s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m013-t350000-s1 params 7148 build 1.32s step 1.71s save_reload 0.46s wall 3.68s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m015-t350000-s1 params 7148 build 1.30s step 1.64s save_reload 0.44s wall 3.57s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m015-t5000000-s1 params 12788 build 1.67s step 1.72s save_reload 0.53s wall 4.14s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m016-t350000-s1 params 7444 build 1.51s step 1.96s save_reload 0.52s wall 4.21s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m016-t5000000-s1 params 13180 build 1.85s step 2.10s save_reload 0.58s wall 4.81s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m017-t5000000-s1 params 12788 build 1.60s step 1.71s save_reload 0.51s wall 4.07s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m018-t5000000-s1 params 12788 build 1.63s step 1.72s save_reload 0.51s wall 4.13s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m019-t5000000-s1 params 12788 build 1.66s step 1.75s save_reload 0.52s wall 4.21s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m020-t5000000-s1 params 12788 build 1.64s step 1.72s save_reload 0.53s wall 4.19s max_abs 0 opt BopAdam
GATE_PASS atlas0926-standin-w2-m021-t5000000-s1 params 12788 build 1.64s step 2.15s save_reload 0.76s wall 4.87s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m022-t5000000-s1 params 12797 build 1.85s step 2.11s save_reload 0.57s wall 5.03s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m023-t5000000-s1 params 12788 build 1.73s step 1.76s save_reload 0.53s wall 4.37s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m024-t5000000-s1 params 12820 build 1.63s step 2.27s save_reload 0.77s wall 5.04s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m025-t5000000-s1 params 13049 build 1.97s step 2.09s save_reload 0.73s wall 5.45s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w2-m027-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w2-m034-t5000000-s1 params 12788 build 2.16s step 1.78s save_reload 0.52s wall 5.11s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w2-m035-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w2-m036-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w2-m037-t5000000-s1 params 12788 build 1.82s step 2.16s save_reload 0.64s wall 4.97s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m042-t350000-s1 params 4196 build 1.30s step 1.65s save_reload 0.49s wall 3.95s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m042-t5000000-s1 params 5220 build 1.80s step 1.92s save_reload 0.58s wall 5.07s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m043-t350000-s1 params 8812 build 0.97s step 2.06s save_reload 0.58s wall 4.25s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m043-t5000000-s1 params 14964 build 1.16s step 1.90s save_reload 0.54s wall 4.32s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m044-t5000000-s1 params 19947 build 3.69s step 3.68s save_reload 1.72s wall 9.76s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m045-t350000-s1 params 9726 build 2.07s step 3.84s save_reload 1.23s wall 8.15s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m045-t5000000-s1 params 15102 build 3.79s step 2.42s save_reload 0.74s wall 7.93s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m046-t5000000-s1 params 10740 build 1.80s step 1.81s save_reload 0.76s wall 5.12s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m047-t350000-s1 params 7148 build 1.72s step 2.33s save_reload 1.01s wall 5.63s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m047-t5000000-s1 params 12788 build 1.97s step 2.66s save_reload 0.62s wall 6.12s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m048-t350000-s1 params 7112 build 1.82s step 1.97s save_reload 0.56s wall 5.02s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m048-t5000000-s1 params 12716 build 2.03s step 2.19s save_reload 0.60s wall 5.66s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m049-t350000-s1 params 20945 build 2.13s step 2.23s save_reload 0.52s wall 5.67s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m049-t5000000-s1 params 35033 build 2.07s step 2.30s save_reload 0.73s wall 5.82s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m050-t350000-s1 params 7148 build 1.60s step 2.22s save_reload 0.67s wall 5.45s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-m050-t5000000-s1 params 12788 build 2.36s step 2.41s save_reload 0.66s wall 6.79s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w3-m058-t350000-s1 params 10740 build 1.42s step 2.04s save_reload 0.52s wall 5.96s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w3-m058-t5000000-s1 params 10740 build 1.44s step 2.13s save_reload 0.52s wall 5.11s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m061-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m062-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m063-t5000000-s1 needs prerequisite teacher artifact 'teacher-int8-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m064-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m082-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m083-t5000000-s1 params 5220 build 1.81s step 1.86s save_reload 0.75s wall 5.07s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w3-m084-t5000000-s1 params 12788 build 2.50s step 2.93s save_reload 0.78s wall 7.22s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m088-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER atlas0926-standin-w3-m089-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m090-t5000000-s1 params 5220 build 2.37s step 2.67s save_reload 0.65s wall 7.16s max_abs 0 opt Adam
GATE_NEEDS_TEACHER atlas0926-standin-w3-m094-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS atlas0926-standin-w3-m101-t350000-s1 params 10022 build 2.97s step 4.14s save_reload 0.71s wall 8.94s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-a-t350000-s1 params 7148 build 2.07s step 2.06s save_reload 0.68s wall 6.72s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-a07-350-t350000-s1 params 12788 build 2.25s step 2.58s save_reload 0.63s wall 6.94s max_abs 0 opt Adam
GATE_PASS atlas0926-standin-w2-rep-c-t5000000-s1 params 12788 build 3.00s step 2.10s save_reload 0.57s wall 7.10s max_abs 0 opt Adam
GATE_SOME_FAILED 50/61
```

- **Totals:** 61 pairs, 50 PASS, 11 NEEDS_TEACHER, 0 FAIL; 4 min 42 s wall.
- **The 9 arm-C 5M cells the reviewer listed all pass** with `max_abs 0`. Their parameter counts (C cell):

  | entry | params |
  | --- | --- |
  | M015 | 12,788 |
  | M016 | 13,180 |
  | M042 | 5,220 |
  | M043 | 14,964 |
  | M045 | 15,102 |
  | M047 | 12,788 |
  | M048 | 12,716 |
  | M049 | 35,033 |
  | M050 | 12,788 |

  These equal the reviewer's independent run.

**B1-v4.** The committed `annotate_index.py` writes each row's `gate` (the outcome of its (entry, base arm)
from `gate_results.json`, or null if the row is not gate-eligible) and `depends_on`. `depends_on` is read
from each config's teacher or warm-start artifact, so it covers non-gated rows: 60 rows, 56 of them
`teacher-fp32-a07` and 4 `teacher-int8-a07`. The script also refreshes `patch_status` from the ledger:
- attn-linformer: `written; wiring blocked-on-[A20]`;
- body-deepsets: `gated-on-tarball`;
- bop-optimizer: `gated-on-tarball`.

`classify_series.py` no longer writes the absolute build path, so its output is deterministic. Reproduction
from scratch (gen → classify → annotate, same gate_results.json):

```
INDEX_BYTE_IDENTICAL   (cmp <scratch>/index.json configs/index.json)
CONFIGS_IDENTICAL      (diff -rq, every config file)
configs/index.json sha256 b28f8862c1a0335b9e4a2ff2b27be62a325c55133fda5790200dbfe5c8e9e3f1
```

**B2-v4.** Packs, `unpacked` and `after_teacher` are keyed by the unique, wave-qualified run `name`, and the
packer asserts the names are unique. Check: 176 packed names, 176 unique, all present in the index, plus 12
after-P-T1 names. The packs file now states the open pre-launch gap (WIRING.md): `run_pack.py` wants row
numbers, and the output root is hard-coded. The ledger's generator row carries the same gap.

**Manifest:** 30 packs, 176 arms, and after P-T1 2 packs, 12 arms (M027, M035, M036), as in §4b.
The offline re-lint gives exit 2, with the same empty-node-map ERROR and the WARN parallelism 10 of 30.

**BLOCKED.md l. 5** now reads "patches 0025+" (C3-v4).

## 5. Where I am not sure

```
DECISION: null for train.clipvalue / train.weight_decay admitted as "Keras default, off"; every other null refused.
ALTERNATIVES: refuse all nulls (M033, M069, M070, M074 would be refused as well)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES (the S runner hands None straight to Adam; not checked by a run)
```
(The v1 drift-replica decision is resolved: the replicas now come from atlas.json `drift_replicas`.)
```
DECISION: order_seed inherited from the base (20260912), flagged order_seed_pending_D9 in every config.
ALTERNATIVES: invent f(s) (refused: [D9] does not define f)
CONFIDENCE: HIGH   FLAG FOR HUMAN: YES
```
```
DECISION: teacher "beta bounds at their minimum" read as init_beta = max_beta = min_beta of the base.
ALTERNATIVES: only max_beta = min_beta; or a pid.target of 1e12 alone
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: Bop flip = reflect the latent about its mean (keeps |w - alpha| and so beta).
ALTERNATIVES: latents set to +-1 (Bop as published: beta becomes 1 - alpha^2, which changes activation scales against the Adam anchor)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES (it defines what M020 measures)
```

## Re-run after the ATLAS fix (orchestrator, 2026-09-27 01:4x) — superseded by §1-§4 v4 above

- `python3 gen_atlas.py` (strict, stand-in base) against atlas.json sha256 e736d1b2ddfb...: exit 0.
  562 cells (W2 292, W3 268 incl. drift replicas, + prereq): needs_patches 370, placeholder_pending_anchor 92,
  ready_on_base 92, refused_unfilled 8 (M020, M071: Bop gamma/tau null until DR-22 sources them). 554 configs
  written; `configs/` replaced wholesale by the regenerated set.
- `python3 manifest_wave2.py`: 50 packs, 288 arms, K=6 (H=500: 46 pods, last pod 2 arms; H=1000: 2 pods [6, 2];
  H=1500: 1 pod [4]; H=2000: 1 pod [4]); 4 cells unpacked (the refused Bop cells).
- `nrp_doctor.py lint` **with cluster access** (read-only node query): no ERROR. WARN parallelism=10 of 50
  completions (the pod-count decision, K2). The offline ERROR recorded above is the empty-node-map artefact.
  Not applied; placeholders (ConfigMap, bundle sha, W&B project, deadline) remain for cluster-ops.


## 6. Anchor tree 77f1ca4e (2026-09-27): Delta rename, real base, floors, gate, packs, canary

This section supersedes §1-§5 for launch. §1-§5 ran on the tarball stand-in. Everything here ran on
the laptop CPU with synthetic inputs, and nothing in it is a result.

### Trees

- **Anchor tree.** `apply_anchor.sh` with `ANCHOR_BUNDLE` set to the 77f1ca4e bundle, plus
  `patches-anchor/0001-0038` and `newmods/`: `APPLY_ANCHOR_ALL_PASS`.
  - The bundle has sha256 77f1ca4e9fe3f67ef276ec9b7c401c174812fcb2e88b7ef572040ad2e26f2a94.
  - It was recovered with `git show HEAD:campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz`
    and its sha was checked.
  - A fresh rebuild equals the development tree (`diff -r` empty).
- **Tarball tree.** `apply.sh` plus `patches/0001-0025`: `APPLY_ALL_PASS`. A fresh rebuild equals it.
- **The anchor bundle moved today.** The training-batch campaign re-froze
  `manifests/chang0926-code.tar.gz` at 15:07.
  - The new bundle has sha256 e90327d4... and is not committed.
  - It adds `train.ebops_trace_every 10` to every arm config ([D15] regime B).
  - It is not used here. `generate_delta.py` falls back to the 77f1ca4e ConfigMap payload
    (`configmap-77f1ca4e.json`, sha checked).
  - **Before launch, the series must be rebased onto the regime-B bundle** (WIRING.md).

### Rename

- `gen_atlas.py` is now `generate_delta.py`. It reads `delta.json` (sha256 f4ad2571...9204).
- The provenance block is `delta_study`.
- Run names are `delta0926-<wave>-<run_id>`.
- Groups are `delta-20260926-w2` and `-w3`, and `-w4` for the confirm tier.
- `train.wandb_project` is `BNJetTag-Delta`.
- Job names are `kai-delta0926-*`. Packs files are `delta_w2_*_packs.json`.
- `classify_series.py` imports `bnhgq2.delta_keys`.
- `gate_cpu.py` calls `ablation.delta_optimizer_for` and `qat.set_delta_epoch`. Without them it fails;
  it does not fall back.
- `tests/conftest.py` imports `generate_delta`.
- No new-files script contains the string `atlas`.

### Base

Each cell is the anchor's own arm config at the cell's seed:
`code/campaigns/chang0926/configs/chang0926-{a,a07-350,c}-n64-s<seed>.json` in the bundle.

- **Provenance.** Every index row carries its config's sha256 as `anchor_config_sha256`. Seed-1 shas:
  A 9e05bc2b...e447, A07-350 44edb194...c135, C 60ef2984...f01.
- **order_seed.** order_seed = 20260926 × 100 + s (anchor generate.py:37). This is asserted on every
  file read. The teachers' seed 101 has no anchor file, so the formula is applied and the row is
  flagged `seed_outside_anchor_configs`.
- **Removed block.** The anchor's `campaign` block is dropped.
- **Split.** Every cell keeps `train.split_seed` 1 and `train.validation_split` 0.1 (asserted), so the
  350k and 5M cells read the anchor's gated 90/10 cache `/data/chang-n64-20260926`.
- **Anchor-owned keys.** The generator fails if a Delta entry sets `train.ebops_trace_every`,
  `split_seed`, `validation_split` or `order_seed`.

Generator output:

```
tier=screen base=anchor pilot bundle 77f1ca4e (campaigns/2026-09-26-training-batch/manifests/configmap-77f1ca4e.json), per-seed arm configs delta_sha256=f4ad2571667a
cells by wave (incl. drift replicas, placebos): {'W2': 312, 'W3': 268}
status: {'needs_patches': 442, 'ready_on_base': 140} configs written: 582
flags: {'amended_replica_seed': 8, 'cache_not_built': 96, 'covered_by_anchor_study': 4, 'floor_untraced': 34, 'pending_study_pass': 16, 'placebo': 8, 'pos_enc_none_without_consume_rng': 16, 'seed_outside_anchor_configs': 2, 'teacher_definition_provisional': 2}
```

The 582 configs are W2 312 (252 single, 32 baseline, 20 replica, 8 placebo), W3 268 and 2 teachers.

`wave2_amendments.json` is pending STUDY PASS (STUDY commit 9f9deeb). It adds:
- P-350: arm A, 350k, H 500, seeds 1-4;
- P-5M: arm C, 5M, H 500, seeds 1-4;
- rep-A and rep-C at seeds 1-8, with horizons 1,000 and 2,000 from delta.json.

The placebo's no-op is `delta_study.placebo`, a provenance key that training does not read.

### Zero floor

This changes what a number means; see the decisions.md line in PLAN_newfiles.md.

`experiment.nondegenerate.zero_floor_ebops` is read at run time by the [ND] feasibility rule. If a cell
inherited its arm's value, it could be misjudged. Example: every floor-family M001 cell (A07 with 2
heads) would have carried the A07 floor 343,053 instead of its own 171,526. A checkpoint at 300k EBOPs
would then have been labelled degenerate.

`trace_floors_delta.py` runs the anchor's `static_floor.floors(cfg, with_attn_rule=False)` once per
arch/quant signature:

```
FLOOR_SELFCHECK A stored 171526 retraced 171526 OK
FLOOR_SELFCHECK A07-350 stored 343053 retraced 343053 OK
FLOOR M001 A07-350 zero 171526 one 834214 base 343053 2.83s
FLOOR M002 A07-350 zero 85763 one 748451 base 343053 2.43s
FLOOR M003 A07-350 zero 114182 one 776870 base 343053 3.48s
FLOOR M004 A07-350 zero 41985 one 508065 base 343053 2.49s
FLOOR M005 A07-350 zero 0 one 662688 base 343053 2.09s
FLOOR_NOT_TRACED M006 A07-350 arch.body 'deepsets': static_floor builds qat.build_qat_model only
FLOOR M007 C zero 343053 one 1005741 base 343053 3.87s
FLOOR M008 A zero 171526 one 619198 base 171526 2.67s
FLOOR M008 C zero 343053 one 1005741 base 343053 4.33s
FLOOR M009 A07-350 zero 85507 one 351907 base 343053 2.15s
FLOOR M011 A zero 171526 one 619198 base 171526 3.0s
FLOOR M011 C zero 343053 one 1005741 base 343053 3.96s
FLOOR M012 A zero 171526 one 619198 base 171526 2.61s
FLOOR M012 C zero 343053 one 1005741 base 343053 3.75s
FLOOR M016 A zero 171528 one 619202 base 171526 3.27s
FLOOR M016 C zero 343055 one 1005745 base 343053 4.34s
FLOOR M017 C zero 343053 one 1005741 base 343053 3.62s
FLOOR M018 C zero 343053 one 1005741 base 343053 3.56s
FLOOR M019 C zero 343053 one 1005741 base 343053 3.59s
FLOOR M021 C zero 343053 one 1005741 base 343053 3.68s
FLOOR M022 C zero 343053 one 1005741 base 343053 3.89s
FLOOR M023 C zero 343053 one 1005741 base 343053 3.77s
FLOOR M024 C zero 343053 one 1005741 base 343053 3.53s
FLOOR M025 C zero 343053 one 1005741 base 343053 3.89s
FLOOR M026 C zero 343053 one 1005741 base 343053 3.6s
FLOOR M038 A zero 171526 one 619198 base 171526 2.74s
FLOOR M038 C zero 343053 one 1005741 base 343053 3.78s
FLOOR M039 A zero 171526 one 619198 base 171526 2.98s
FLOOR M039 C zero 343053 one 1005741 base 343053 4.34s
FLOOR M040 A zero 171526 one 622270 base 171526 3.29s
FLOOR M040 C zero 343053 one 1009837 base 343053 5.36s
FLOOR M042 A zero 171526 one 437078 base 171526 3.33s
FLOOR M042 C zero 343053 one 608605 base 343053 5.07s
FLOOR M043 A zero 171526 one 717502 base 171526 3.5s
FLOOR M043 C zero 343053 one 1136813 base 343053 4.59s
FLOOR M044 C zero 686106 one 2004154 base 343053 11.33s
FLOOR M045 A zero 171526 one 621478 base 171526 5.86s
FLOOR M045 C zero 343053 one 1007789 base 343053 7.47s
FLOOR M046 C zero 343053 one 1005741 base 343053 6.22s
FLOOR_ERROR M047 A ValueError: delta0926-w2-m047-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
FLOOR_ERROR M047 C ValueError: delta0926-w2-m047-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
FLOOR_ERROR M048 A ValueError: delta0926-w2-m048-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
FLOOR_ERROR M048 C ValueError: delta0926-w2-m048-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
FLOOR_NOT_TRACED M049 A quant.weight hgq_learnable: learnable weight widths; static_floor holds weights fixed
FLOOR_NOT_TRACED M049 C quant.weight hgq_learnable: learnable weight widths; static_floor holds weights fixed
FLOOR M050 A zero 171526 one 651454 base 171526 4.98s
FLOOR M050 C zero 343053 one 1048749 base 343053 5.44s
FLOOR M051 A07-350 zero 57091 one 719779 base 343053 5.0s
FLOOR M052 A07-350 zero 28545 one 691233 base 343053 4.62s
FLOOR M053 A07-350 zero 20992 one 487072 base 343053 4.76s
FLOOR M054 A07-350 zero 13824 one 479904 base 343053 4.58s
FLOOR M055 A zero 171526 one 619198 base 171526 5.3s
FLOOR M055 C zero 171526 one 834214 base 343053 4.21s
FLOOR M056 A07-350 zero 41985 one 508065 base 343053 3.12s
FLOOR M057 A07-350 zero 171526 one 834214 base 343053 4.22s
FLOOR M058 A07-350 zero 42753 one 309153 base 343053 2.5s
FLOOR M059 A07-350 zero 0 one 662688 base 343053 2.48s
FLOOR M060 A07-350 zero 6912 one 472992 base 343053 2.65s
FLOOR M065 C zero 343053 one 1005741 base 343053 4.89s
FLOOR M066 C zero 343053 one 1005741 base 343053 4.78s
FLOOR M067 C zero 343053 one 1009837 base 343053 4.9s
FLOOR M072 C zero 343053 one 1005741 base 343053 4.67s
FLOOR M073 C zero 343053 one 1005741 base 343053 4.69s
FLOOR M075 C zero 343053 one 1005741 base 343053 4.78s
FLOOR M076 A zero 171526 one 619198 base 171526 4.43s
FLOOR M076 C zero 343053 one 1005741 base 343053 4.84s
FLOOR M077 C zero 343053 one 1005741 base 343053 5.63s
FLOOR M078 C zero 343053 one 1005741 base 343053 5.66s
FLOOR M080 C zero 343053 one 1009837 base 343053 6.2s
FLOOR M081 C zero 343053 one 1009837 base 343053 4.74s
FLOOR M083 C zero 343053 one 608605 base 343053 4.39s
FLOOR M086 C zero 343053 one 610653 base 343053 4.65s
FLOOR M091 C zero 343053 one 610653 base 343053 5.2s
FLOOR M096 A zero 171526 one 619198 base 171526 3.47s
FLOOR M097 A zero 171528 one 619202 base 171526 4.13s
FLOOR M098 A zero 171526 one 621478 base 171526 3.72s
FLOOR M099 A zero 171528 one 619202 base 171526 4.83s
FLOOR M100 A zero 171526 one 621478 base 171526 3.58s
FLOOR M101 A zero 171528 one 621482 base 171526 4.07s
FLOOR M102 A zero 171528 one 621482 base 171526 4.39s
FLOOR_ERROR P-T1 A07-350 ValueError: delta0926-prereq-p-t1-s101: act_overflow/softmax_quant need binary weights and act_calib='free'
FLOORS_WRITTEN 73/81 traced in 307s -> floors_delta.json
```

38 (entry, arm) pairs carry a floor that differs from their arm's.

The trace ran on the pre-amendment scratch index. So `floors_delta.json` `index_sha256` matches no file
in the campaign. The join is by signature. Placebos and the added replica seeds carry their arm's
signature, so they need no trace of their own.

**STUDY amendment needed.** Wave-2 STUDY l. 154-156 fails any key outside the entry's delta, `epochs`
and run identity. Two kinds of key fall outside that list:
- `experiment.nondegenerate.zero_floor_ebops`, a derived key, in 38 (entry, arm) pairs;
- the always-on keys, `experiment.collapse_stop` and `experiment.accumulator_metric`. Cells and replicas
  share them.

The generator records every diff against the same-seed replica, as `diff_vs_replica` and
`diff_outside_declared` (0 rows outside). But the STUDY must admit the derived floor as a declared
diff, or those 38 pairs fail its gate by construction.

These are not traced. They are flagged `floor_untraced` and never packed:
- M006: Deep Sets; static_floor builds only the transformer.
- M049: hgq_learnable weights.
- M047, M048, P-T1 and P-T2: the build itself is refused (see the CPU gate below).

The gated-key-mask entries are traced with the mask key removed, because 0036 does not bill the mask.

### Classification

`classify_series.py` uses the anchor tree's own strict validator:

```
series status: {'ready_on_base': 140, 'runnable_on_series': 442}
```

### CPU gate

`gate_cpu.py --one-per-arm` builds each config through `run_engram.builder_for`, takes one optimizer
step at the config's batch of 2,790, runs the binary gate, then saves and reloads at atol 1e-7.
142 (entry, arm) pairs took 22.6 min:

```
GATE_PASS delta0926-w2-rep-a-t350000-s1 params 31735 build 2.55s step 4.35s save_reload 0.71s wall 27.01s max_abs 0 opt Adam
GATE_PASS delta0926-w2-rep-a07-350-t350000-s1 params 61951 build 2.81s step 6.97s save_reload 0.90s wall 10.96s max_abs 0 opt Adam
GATE_PASS delta0926-w2-rep-c-t5000000-s1 params 61951 build 2.91s step 6.86s save_reload 0.88s wall 10.92s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m001-t350000-s1 params 37375 build 2.46s step 3.91s save_reload 0.73s wall 7.35s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m001-t5000000-s1 params 37375 build 2.63s step 3.58s save_reload 0.57s wall 7.06s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m002-t350000-s1 params 25087 build 2.00s step 2.91s save_reload 0.58s wall 5.75s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m002-t5000000-s1 params 25087 build 2.03s step 2.62s save_reload 0.59s wall 5.49s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m003-t350000-s1 params 61951 build 2.71s step 6.25s save_reload 0.79s wall 10.07s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m003-t5000000-s1 params 61951 build 2.84s step 7.74s save_reload 0.97s wall 11.93s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m004-t350000-s1 params 20171 build 2.92s step 3.07s save_reload 0.79s wall 7.26s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m004-t5000000-s1 params 20171 build 2.46s step 2.64s save_reload 0.77s wall 6.28s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m005-t350000-s1 params 61932 build 2.10s step 2.70s save_reload 0.72s wall 5.83s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m005-t5000000-s1 params 61932 build 2.18s step 2.79s save_reload 0.64s wall 5.97s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m006-t350000-s1 params 20742 build 0.42s step 1.95s save_reload 0.33s wall 3.13s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m006-t5000000-s1 params 20742 build 0.43s step 1.74s save_reload 0.34s wall 2.86s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m007-t5000000-s1 params 61951 build 3.10s step 6.75s save_reload 0.82s wall 11.09s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m008-t350000-s1 params 31735 build 2.36s step 3.61s save_reload 0.71s wall 7.31s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m008-t5000000-s1 params 61951 build 2.92s step 7.08s save_reload 0.99s wall 11.48s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m009-t350000-s1 params 23039 build 1.76s step 2.73s save_reload 0.60s wall 5.60s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m009-t5000000-s1 params 23039 build 1.89s step 2.29s save_reload 0.72s wall 5.39s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m010-t1400000-s1 params 61951 build 3.64s step 7.52s save_reload 0.95s wall 12.75s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m011-t350000-s1 params 74638 build 2.29s step 3.72s save_reload 0.58s wall 7.15s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m011-t5000000-s1 params 116950 build 2.52s step 5.72s save_reload 0.70s wall 9.44s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m012-t350000-s1 params 31735 build 2.09s step 3.61s save_reload 0.60s wall 6.78s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m012-t5000000-s1 params 61951 build 2.80s step 7.33s save_reload 1.17s wall 11.83s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m013-t350000-s1 params 31735 build 2.65s step 3.83s save_reload 0.66s wall 8.26s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m015-t350000-s1 params 31735 build 2.00s step 3.00s save_reload 0.59s wall 6.20s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m015-t5000000-s1 params 61951 build 2.61s step 5.38s save_reload 0.86s wall 9.38s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m016-t350000-s1 params 32033 build 3.06s step 4.33s save_reload 1.04s wall 9.19s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m016-t5000000-s1 params 62345 build 3.33s step 6.50s save_reload 0.81s wall 11.58s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m017-t5000000-s1 params 61951 build 2.55s step 6.29s save_reload 0.87s wall 10.29s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m018-t5000000-s1 params 61951 build 2.87s step 6.16s save_reload 0.90s wall 10.72s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m019-t5000000-s1 params 61951 build 3.08s step 6.19s save_reload 0.82s wall 11.42s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m020-t5000000-s1 params 61951 build 2.51s step 5.86s save_reload 0.71s wall 9.82s max_abs 0 opt BopAdam
GATE_PASS delta0926-w2-m021-t5000000-s1 params 61951 build 2.42s step 7.42s save_reload 1.02s wall 11.45s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m022-t5000000-s1 params 61960 build 3.32s step 8.00s save_reload 0.87s wall 13.00s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m023-t5000000-s1 params 61951 build 3.28s step 6.04s save_reload 1.13s wall 11.34s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m024-t5000000-s1 params 61983 build 2.74s step 6.90s save_reload 1.31s wall 11.88s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m025-t5000000-s1 params 62212 build 2.97s step 9.05s save_reload 0.87s wall 13.90s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m026-t5000000-s1 params 62306 build 2.84s step 5.38s save_reload 0.78s wall 9.98s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w2-m027-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w2-m028-t5000000-s1 params 61951 build 2.60s step 5.84s save_reload 0.76s wall 9.78s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m029-t5000000-s1 params 61951 build 3.14s step 7.98s save_reload 1.24s wall 13.36s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m030-t5000000-s1 params 61951 build 2.96s step 6.20s save_reload 0.68s wall 11.20s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m031-t5000000-s1 params 61951 build 2.66s step 6.40s save_reload 0.74s wall 10.71s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m032-t5000000-s1 params 61951 build 2.88s step 6.93s save_reload 0.74s wall 11.30s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m033-t5000000-s1 params 61951 build 3.63s step 5.52s save_reload 0.86s wall 11.15s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m034-t5000000-s1 params 61951 build 2.65s step 6.37s save_reload 0.79s wall 10.81s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w2-m035-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w2-m036-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w2-m037-t5000000-s1 params 61951 build 2.60s step 7.20s save_reload 1.01s wall 11.48s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m038-t350000-s1 params 31735 build 2.19s step 4.46s save_reload 0.70s wall 8.23s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m038-t5000000-s1 params 61951 build 2.89s step 7.18s save_reload 0.83s wall 11.94s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m039-t350000-s1 params 31735 build 1.99s step 3.45s save_reload 0.60s wall 7.06s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m039-t5000000-s1 params 61951 build 2.81s step 6.96s save_reload 0.74s wall 11.35s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m040-t350000-s1 params 31789 build 2.33s step 3.27s save_reload 0.84s wall 7.96s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m040-t5000000-s1 params 62021 build 2.41s step 6.27s save_reload 0.70s wall 10.47s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m041-t5000000-s1 params 61951 build 2.45s step 4.98s save_reload 0.57s wall 9.02s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m042-t350000-s1 params 28783 build 1.63s step 2.80s save_reload 0.50s wall 5.81s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m042-t5000000-s1 params 54383 build 1.76s step 4.30s save_reload 0.57s wall 7.39s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m043-t350000-s1 params 33399 build 0.93s step 3.08s save_reload 0.52s wall 5.35s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m043-t5000000-s1 params 64127 build 1.26s step 5.46s save_reload 0.61s wall 8.10s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m044-t5000000-s1 params 118270 build 3.95s step 12.71s save_reload 1.05s wall 18.70s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m045-t350000-s1 params 34315 build 1.85s step 2.83s save_reload 0.58s wall 6.11s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m045-t5000000-s1 params 64267 build 2.18s step 5.41s save_reload 0.65s wall 9.05s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m046-t5000000-s1 params 59903 build 2.08s step 4.93s save_reload 0.58s wall 8.62s max_abs 0 opt Adam
GATE_FAIL configs/W2/M047-t350000-s1.json ValueError: delta0926-w2-m047-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M047-t5000000-s1.json ValueError: delta0926-w2-m047-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M048-t350000-s1.json ValueError: delta0926-w2-m048-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M048-t5000000-s1.json ValueError: delta0926-w2-m048-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M049-t350000-s1.json ValueError: delta0926-w2-m049-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M049-t5000000-s1.json ValueError: delta0926-w2-m049-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_PASS delta0926-w2-m050-t350000-s1 params 31735 build 1.92s step 3.20s save_reload 0.53s wall 6.55s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m050-t5000000-s1 params 61951 build 2.17s step 5.33s save_reload 0.68s wall 9.05s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m051-t350000-s1 params 37375 build 2.04s step 3.70s save_reload 0.58s wall 7.45s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m051-t5000000-s1 params 37375 build 2.39s step 3.50s save_reload 1.07s wall 7.95s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m052-t350000-s1 params 25087 build 2.66s step 3.46s save_reload 0.85s wall 8.37s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m052-t5000000-s1 params 25087 build 3.57s step 3.14s save_reload 0.85s wall 8.85s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m053-t350000-s1 params 17099 build 2.47s step 2.37s save_reload 0.71s wall 6.82s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m053-t5000000-s1 params 17099 build 2.61s step 2.50s save_reload 0.76s wall 7.20s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m054-t350000-s1 params 20171 build 2.86s step 3.37s save_reload 0.88s wall 8.81s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m054-t5000000-s1 params 20171 build 2.79s step 2.65s save_reload 0.90s wall 7.85s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m055-t350000-s1 params 31735 build 2.53s step 5.25s save_reload 0.76s wall 10.06s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m055-t5000000-s1 params 37375 build 3.60s step 5.08s save_reload 0.74s wall 11.32s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m056-t350000-s1 params 20171 build 2.83s step 2.59s save_reload 0.76s wall 7.57s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m056-t5000000-s1 params 20171 build 2.69s step 3.47s save_reload 0.80s wall 8.71s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m057-t350000-s1 params 37375 build 2.88s step 4.59s save_reload 0.89s wall 9.85s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m057-t5000000-s1 params 37375 build 2.75s step 4.65s save_reload 0.96s wall 9.84s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m058-t350000-s1 params 16895 build 2.17s step 2.36s save_reload 0.65s wall 8.87s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m058-t5000000-s1 params 16895 build 1.85s step 2.10s save_reload 0.66s wall 5.98s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m059-t350000-s1 params 61932 build 2.55s step 3.25s save_reload 1.08s wall 8.53s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m059-t5000000-s1 params 61932 build 2.39s step 2.56s save_reload 0.70s wall 8.40s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m060-t350000-s1 params 17099 build 2.85s step 2.41s save_reload 0.80s wall 7.57s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m060-t5000000-s1 params 17099 build 2.78s step 3.19s save_reload 0.74s wall 8.75s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m061-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m062-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m063-t5000000-s1 needs prerequisite teacher artifact 'teacher-int8-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m064-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m065-t5000000-s1 params 117211 build 3.23s step 7.77s save_reload 1.15s wall 13.42s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m066-t5000000-s1 params 62567 build 5.07s step 8.35s save_reload 1.23s wall 17.50s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m067-t5000000-s1 params 62053 build 3.41s step 9.19s save_reload 1.04s wall 15.38s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m068-t5000000-s1 params 61951 build 3.22s step 5.45s save_reload 0.90s wall 11.57s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m069-t5000000-s1 params 61951 build 2.85s step 6.27s save_reload 1.20s wall 12.24s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m070-t5000000-s1 params 61951 build 4.06s step 6.23s save_reload 0.86s wall 13.00s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m071-t5000000-s1 params 61951 build 3.08s step 8.70s save_reload 1.24s wall 15.10s max_abs 0 opt BopAdam
GATE_PASS delta0926-w3-m072-t5000000-s1 params 61951 build 4.96s step 8.23s save_reload 1.31s wall 18.20s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m073-t5000000-s1 params 61951 build 4.59s step 9.09s save_reload 1.96s wall 18.95s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m074-t5000000-s1 params 61951 build 4.18s step 8.94s save_reload 1.01s wall 17.84s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m075-t5000000-s1 params 59903 build 4.21s step 9.49s save_reload 1.64s wall 17.73s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m076-t350000-s1 params 31735 build 3.41s step 4.18s save_reload 1.08s wall 11.13s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m076-t5000000-s1 params 61951 build 3.88s step 7.30s save_reload 1.35s wall 15.65s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m077-t5000000-s1 params 59903 build 4.15s step 7.22s save_reload 1.22s wall 16.11s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m078-t5000000-s1 params 59903 build 4.15s step 9.39s save_reload 1.98s wall 17.64s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m079-t5000000-s1 params 61951 build 4.81s step 8.05s save_reload 1.40s wall 17.01s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m080-t5000000-s1 params 62053 build 4.77s step 9.91s save_reload 1.32s wall 19.71s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m081-t5000000-s1 params 62021 build 4.38s step 9.45s save_reload 1.54s wall 18.61s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m082-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m083-t5000000-s1 params 54383 build 4.59s step 8.19s save_reload 1.66s wall 17.23s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m084-t5000000-s1 params 61951 build 5.41s step 9.92s save_reload 1.41s wall 22.86s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m085-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m086-t5000000-s1 params 54421 build 3.57s step 7.06s save_reload 1.28s wall 14.21s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m087-t5000000-s1 params 62021 build 4.40s step 8.17s save_reload 1.87s wall 17.53s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m088-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m089-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m090-t5000000-s1 params 54383 build 6.36s step 8.89s save_reload 1.55s wall 21.57s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m091-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m092-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m093-t5000000-s1 params 54421 build 3.40s step 7.13s save_reload 1.31s wall 13.66s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m094-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m095-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m096-t350000-s1 params 74638 build 2.58s step 6.54s save_reload 1.51s wall 12.71s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m097-t350000-s1 params 74936 build 3.31s step 4.74s save_reload 0.96s wall 11.83s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m098-t350000-s1 params 77218 build 3.20s step 4.19s save_reload 1.23s wall 10.89s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m099-t350000-s1 params 32033 build 5.23s step 6.47s save_reload 1.41s wall 16.16s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m100-t350000-s1 params 34315 build 3.54s step 5.59s save_reload 1.50s wall 16.72s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m101-t350000-s1 params 34613 build 3.43s step 6.41s save_reload 1.36s wall 13.98s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m102-t350000-s1 params 77516 build 3.82s step 6.87s save_reload 1.16s wall 14.32s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m103-t5000000-s1 params 61951 build 4.34s step 6.52s save_reload 0.96s wall 14.75s max_abs 0 opt Adam
GATE_PASS delta0926-w2-p-350-t350000-s1 params 31735 build 2.25s step 3.96s save_reload 0.98s wall 9.45s max_abs 0 opt Adam
GATE_PASS delta0926-w2-p-5m-t5000000-s1 params 61951 build 2.85s step 8.35s save_reload 0.94s wall 14.75s max_abs 0 opt Adam
GATE_FAIL configs/prereq/P-T1-s101.json ValueError: delta0926-prereq-p-t1-s101: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/prereq/P-T2-s101.json ValueError: delta0926-prereq-p-t2-s101: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_SOME_FAILED 119/142
```

- **119 PASS.** Every reload gives `max_abs 0`. M020 runs `BopAdam`, so Bop is exercised.
- **15 NEEDS_TEACHER.** These are KD or warm-start cells; P-T1 and P-T2 are not trained.
- **8 FAIL, all with one cause.** The anchor's [A20] guard (`qat.py:667-669`, bundle 77f1ca4e)
  refuses `act_overflow`/`softmax_quant` unless the weights are binary.
  - It hits M047 (`quant.weight none`), M048 (`int8_absmax`), M049 (`hgq_learnable`) and both teachers.
  - Patch 0007 (weight-scheme-baselines) lets the schemes past the validator but does not relax the
    build guard.
  - As a result, neither prerequisite teacher, none of the three W2 baselines, and no KD cell that
    needs a teacher can run on this tree.
  - **The ledger is contradicted.** README.md lists weight-scheme-baselines as
    `gated-on-anchor-77f1ca4e` with "same slug test PASS". On this tree a non-binary config under the
    Chang quantizers does not build. So that anchor slug test cannot have built one, and the status is
    wrong for any non-binary scheme.
  - This goes to the patches owner. It also needs a design call: what the Chang quantizers mean for a
    float or int8 teacher.
- **Base-arm parameter counts, as printed:**

  | arm | params |
  | --- | --- |
  | rep-A (E) | 31,735 |
  | rep-A07-350 | 61,951 |
  | rep-C | 61,951 |
  | P-350 | 31,735 |
  | P-5M | 61,951 |

  The A07 value equals the anchor PREFLIGHT's 61,951.

### Packs

`manifest_wave2.py` packs for GPU class 24GB (NVIDIA-A10 and RTX-3090). The packs are PLANNING until
the canary runs.

- **K[E] = 4.** This is the estimate floor(0.9 × 23,028 / 4,354), from the anchor's measured
  per-process footprint (RUN.md l. 35-39 and 215-217).
- **K[A07] = 3.** This is the STUDY's planning value. No A07 measurement exists under the Chang
  quantizers: A07-350-s1 ran out of memory, and C′'s 5,172 MiB was taken with the old quantizer.
- **15 other architecture classes** take their base class's K and are flagged `k_class_unmeasured`.

```
t0:    7 pods, 20 arms (rep-A 2x4 at H 1,000; rep-C 3,3,2 at H 2,000; rep-A07-350 3,1 at H 500)
cells: 83 pods, 220 arms, parallelism 7, released at the replica epoch-500 gate
       (floor family first, then long-horizon, then placebos, then singles)
after_teacher: teacher-fp32-a07 12 runs (M027, M035, M036)
unpacked: cache_not_built M009 (N=32), M038 (ungated), M040 (derived features), M041 (real-slot std);
          floor_untraced M006; GATE_FAIL M047, M048, M049, P-T1, P-T2
canary: 1 pod on NVIDIA-A10: E-k5 (rep-A s1-5), then A07-k3 (rep-C s1-3), 10 epochs each
```

- **Pod cap.** Cells parallelism is 7: the 10-pod cap minus 3 t0 pods that keep running past the gate.
  Those are the rep-A pack with seeds 1-4 (H 1,000) and the two rep-C packs holding seeds 1-6
  (H 2,000), at n = 4. The value is in the manifest annotation `bnjettag.io/parallelism`.
  Recompute it if n changes. The lint WARN above was taken before this change and says 10.
- A pack never mixes horizon, cache, architecture class or phase.
- Replicas are in t0, and placebos and cells are in the cells phase. So a placebo never shares a pod
  with its replica (asserted).
- `run_pack.resolve_pack` was run against the real index. It resolved every packed name to its row,
  file and data_root: t0 7 packs / 20 arms, cells 83 / 220, canary 2 / 8 (RESOLVE_OK).

### Canary

Files: `manifests/delta-canary-job.json`, `delta_canary_packs.json`, `canary_k.py`.

- The recorded canary was one pod on NVIDIA-A10, with `BNJ_STAGE=canary`; a new-product canary
  is generated on its selected product with a separate run root and Job name.
- `BNJ_ARM_RETRIES=0`, so an OOM is recorded as a measurement, not retried.
- A background `nvidia-smi` sampler runs every 10 s, per GPU and per process.
- `canary_k.py` computes k_accepted:
  - with no OOM and the pod peak within 90 %: min(floor(0.9 × card / per-process peak), k_tested);
  - otherwise: one less.
- The output goes to `/data/delta-20260927/canary/k_result.json`. Copy it to `code/k_result.json` and
  run `manifest_wave2.py` again.
- Smoke test on a synthetic CSV: E at K = 5 with a 21,800 MiB pod peak gives k_accepted 4. An OOM line
  gives k_tested − 1.

### Lint, offline

Run with `KUBECONFIG=/nonexistent/kubeconfig`; exit code 2:

```
== manifests/delta-w2-t0-job.json :: kai-delta0926-w2-t0 ==
  ERROR  NO product in the required list is reachable: the pod requests nvidia.com/gpu but every listed product needs a different resource name. This job can never schedule.
  WARN   required-list product(s) match no node in the cluster (typo, or the hardware is gone): NVIDIA-A10, NVIDIA-GeForce-RTX-3090
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 4 arms per pod declared.
== manifests/delta-w2-cells-job.json :: kai-delta0926-w2-cells ==
  ERROR  NO product in the required list is reachable: the pod requests nvidia.com/gpu but every listed product needs a different resource name. This job can never schedule.
  WARN   required-list product(s) match no node in the cluster (typo, or the hardware is gone): NVIDIA-A10, NVIDIA-GeForce-RTX-3090
  WARN   parallelism=10 but completions=83: at most 10 run at once. This is a self-imposed ceiling, not a cluster limit.
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 4 arms per pod declared.
== manifests/delta-canary-job.json :: kai-delta0926-canary ==
  ERROR  NO product in the required list is reachable: the pod requests nvidia.com/gpu but every listed product needs a different resource name. This job can never schedule.
  WARN   required-list product(s) match no node in the cluster (typo, or the hardware is gone): NVIDIA-A10
  WARN   backoffLimitPerIndex=1: one blip kills an index. Suggest 3.
  note   [rule PACK] 5 arms per pod declared.
(rules: docs/infrastructure/nrp-nautilus-setup.md -> 'Scheduling, GPU pools and job shape')
```

- On each manifest, the ERROR and the first WARN come from the empty node map, as in §2.
- The canary's `backoffLimitPerIndex=1` is deliberate: it retries a pod blip but never an arm.
- The ConfigMap name, bundle sha and manifest sha stay as placeholders for cluster-ops.
- `bash -n` passes on all three headers.

### Launch-gap patches

**Tarball: `patches/0025-run-pack-names-roots`.**
- It ports the anchor's `BNJ_DATA_ROOT` / `BNJ_RUN_ROOT` / `BNJ_CAMPAIGN_DIR` roots into
  `run_study.py` and `run_pack.py`.
- It lets packs use run names and the dict form.
- `tests/test_run_pack_delta.py`: 6/6.
- Invariance gate against the stored pristine fingerprint: 7/7 SAME, `INVARIANCE_GATE_PASS`.

**Anchor: `patches-anchor/0038-run-pack-names-roots`.**
- It adds run names and dict-form packs to `run_pack.py`. The roots were already driven by the
  environment in 77f1ca4e.
- Tests: 6/6. The anchor's own `tests/test_run_pack.py` passes 2/2, so legacy row lists are unchanged.
- 0038 changes only `run_pack.py` and its test. No builder or trainer imports `run_pack`, so the anchor
  invariance fingerprint cannot move.

### Reproduction

Starting from the same `floors_delta.json`, `gate_results.json` and `wave2_amendments.json`, gen →
classify → annotate into scratch reproduces the outputs: `CONFIGS_IDENTICAL`, `INDEX_BYTE_IDENTICAL`.
configs/index.json has sha256 f8f5f786...afc.

### ConfigMap size

The `apply_anchor.sh` tree plus `campaigns/delta0926/` (index, 582 configs, packs, canary_k.py) tars to
424,368 bytes. Base64 of that is about 566 KB, under the 1 MiB ConfigMap cap.

### Stand-in set

`configs-standin/` holds 566 configs, regenerated with `--standin` on the tarball base, for
`tests_patches/slug_tests.py`.

That file's `delta_cfg` still reads `configs/W*/...`, which now holds anchor configs. Its tarball tests
will refuse the anchor keys in them. The patches owner needs to repoint it to `configs-standin/`.


## 7. Anchor bundle 42abed4b (2026-09-28): leak-fixed regime B, frozen wave-2 lists, RSS gate per horizon, canary

This section supersedes §6 for launch. §6 stays as the 77f1ca4e record. Everything here ran on the
laptop CPU with synthetic inputs, and nothing in it is a result.

### Tree and base

- **Tree.** `apply_anchor.sh` (it now pins 42abed4b) applied to the training-batch
  `manifests/chang0926-code.tar.gz`, plus `patches-anchor/0001-0038` and `newmods/`:
  `ANCHOR_BUNDLE_SHA_OK 42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0`,
  `APPLY_ANCHOR_ALL_PASS`. The patches owner rebased the series; see PLAN_rebase.md "Rebase 2 record".
- **Bundle identity.** ConfigMap `kai-chang0926-code-42abed4b5d`, manifest 041f981a…bd42, commit
  3dabcd2 (training-batch PREFLIGHT.md "Current freeze: 42abed4b").
- **Base configs.** `anchor_arms.json` now names 42abed4b. It tries the tarball first, then
  `configmap-42abed4b.json`. `--anchor-bundle` and `--anchor-sha` select another bundle.
- **What changed in the anchor.** Between 77f1ca4e and 42abed4b the arm configs differ only by
  `train.ebops_trace_every: 10`.
  - Every one of the 582 configs carries that key from its base, checked by script (0 of 582
    differ).
  - No Delta entry may set it; the generator refuses one that does.
  - qat.py, static_floor.py and ebops_calc are unchanged.
- **Floors re-traced** on the 42abed4b tree. The self-check passes (A 171,526, A07-350 343,053).
  73 of 81 signatures were traced, with the same signatures and the same zero floors as §6.

### Frozen wave-2 lists

`wave2_amendments.json` has status `frozen`. It cites the wave-2 STUDY at commit 24c3c90 (status
frozen):
- Arms l. 298-310: P-350 and P-5M, seeds 1-4, H 500. They are the replica's config with only the
  identity keys, `delta_study` and `train.epochs` changed.
- Drift replicas l. 358-364: rep-A and rep-C at seeds 1-8.
- Seeds l. 576-577: n = 4.

These rows are flagged `study_frozen_list`.

### Configs, classification and gate

```
tier=screen base=anchor bundle 42abed4b (campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz), per-seed arm configs delta_sha256=f4ad2571667a
cells by wave (incl. drift replicas, placebos): {'W2': 312, 'W3': 268}
status: {'needs_patches': 442, 'ready_on_base': 140} configs written: 582
series status: {'ready_on_base': 140, 'runnable_on_series': 442}
```

- `diff_outside_declared` is empty on all 582 rows. The frozen STUDY's diff classes (4) and (5)
  admit the re-traced floor and the always-on keys.
- CPU gate: `gate_cpu.py --one-per-arm`, 142 (entry, arm) pairs, 11.7 min. Lines, verbatim:

```
GATE_PASS delta0926-w2-rep-a-t350000-s1 params 31735 build 1.64s step 2.68s save_reload 0.49s wall 11.48s max_abs 0 opt Adam
GATE_PASS delta0926-w2-rep-a07-350-t350000-s1 params 61951 build 1.87s step 3.94s save_reload 0.54s wall 6.52s max_abs 0 opt Adam
GATE_PASS delta0926-w2-rep-c-t5000000-s1 params 61951 build 1.84s step 4.25s save_reload 0.63s wall 6.88s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m001-t350000-s1 params 37375 build 1.77s step 2.59s save_reload 0.45s wall 5.01s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m001-t5000000-s1 params 37375 build 1.60s step 2.09s save_reload 0.44s wall 4.28s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m002-t350000-s1 params 25087 build 1.49s step 1.97s save_reload 0.41s wall 4.01s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m002-t5000000-s1 params 25087 build 1.49s step 1.77s save_reload 0.41s wall 3.82s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m003-t350000-s1 params 61951 build 1.77s step 4.33s save_reload 0.50s wall 6.76s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m003-t5000000-s1 params 61951 build 1.81s step 3.66s save_reload 0.49s wall 6.17s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m004-t350000-s1 params 20171 build 1.70s step 1.77s save_reload 0.45s wall 4.13s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m004-t5000000-s1 params 20171 build 1.70s step 1.80s save_reload 0.46s wall 4.15s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m005-t350000-s1 params 61932 build 1.45s step 1.56s save_reload 0.42s wall 3.61s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m005-t5000000-s1 params 61932 build 1.46s step 1.47s save_reload 0.39s wall 3.52s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m006-t350000-s1 params 20742 build 0.28s step 1.35s save_reload 0.23s wall 2.04s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m006-t5000000-s1 params 20742 build 0.26s step 1.22s save_reload 0.23s wall 1.89s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m007-t5000000-s1 params 61951 build 1.74s step 4.04s save_reload 0.49s wall 6.48s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m008-t350000-s1 params 31735 build 1.46s step 2.56s save_reload 0.44s wall 4.71s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m008-t5000000-s1 params 61951 build 1.75s step 4.04s save_reload 0.48s wall 6.51s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m009-t350000-s1 params 23039 build 1.23s step 1.77s save_reload 0.41s wall 3.67s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m009-t5000000-s1 params 23039 build 1.24s step 1.56s save_reload 0.42s wall 3.44s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m010-t1400000-s1 params 61951 build 1.76s step 4.13s save_reload 0.51s wall 6.65s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m011-t350000-s1 params 74638 build 1.50s step 2.00s save_reload 0.42s wall 4.22s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m011-t5000000-s1 params 116950 build 1.76s step 4.05s save_reload 0.50s wall 6.57s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m012-t350000-s1 params 31735 build 1.47s step 2.64s save_reload 0.43s wall 4.84s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m012-t5000000-s1 params 61951 build 1.78s step 3.90s save_reload 0.49s wall 6.47s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m013-t350000-s1 params 31735 build 1.47s step 2.69s save_reload 0.44s wall 4.93s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m015-t350000-s1 params 31735 build 1.46s step 1.95s save_reload 0.42s wall 4.16s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m015-t5000000-s1 params 61951 build 1.76s step 3.63s save_reload 0.49s wall 6.18s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m016-t350000-s1 params 32033 build 1.76s step 2.80s save_reload 0.50s wall 5.41s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m016-t5000000-s1 params 62345 build 2.09s step 3.55s save_reload 0.55s wall 6.56s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m017-t5000000-s1 params 61951 build 1.76s step 3.67s save_reload 0.50s wall 6.29s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m018-t5000000-s1 params 61951 build 1.78s step 3.29s save_reload 0.50s wall 5.97s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m019-t5000000-s1 params 61951 build 1.80s step 3.41s save_reload 0.52s wall 6.12s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m020-t5000000-s1 params 61951 build 1.80s step 3.51s save_reload 0.49s wall 6.20s max_abs 0 opt BopAdam
GATE_PASS delta0926-w2-m021-t5000000-s1 params 61951 build 1.76s step 3.03s save_reload 0.49s wall 5.69s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m022-t5000000-s1 params 61960 build 1.80s step 3.49s save_reload 0.50s wall 6.19s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m023-t5000000-s1 params 61951 build 1.80s step 3.66s save_reload 0.50s wall 6.39s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m024-t5000000-s1 params 61983 build 1.77s step 3.73s save_reload 0.50s wall 6.43s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m025-t5000000-s1 params 62212 build 1.83s step 3.83s save_reload 0.50s wall 6.61s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m026-t5000000-s1 params 62306 build 1.82s step 3.47s save_reload 0.52s wall 6.25s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w2-m027-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w2-m028-t5000000-s1 params 61951 build 1.76s step 3.18s save_reload 0.51s wall 5.83s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m029-t5000000-s1 params 61951 build 1.79s step 3.42s save_reload 0.49s wall 6.16s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m030-t5000000-s1 params 61951 build 1.78s step 3.25s save_reload 0.50s wall 6.02s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m031-t5000000-s1 params 61951 build 1.77s step 3.80s save_reload 0.49s wall 6.55s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m032-t5000000-s1 params 61951 build 1.87s step 3.97s save_reload 0.50s wall 6.83s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m033-t5000000-s1 params 61951 build 1.78s step 3.32s save_reload 0.50s wall 6.12s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m034-t5000000-s1 params 61951 build 1.77s step 3.81s save_reload 0.52s wall 6.61s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w2-m035-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w2-m036-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w2-m037-t5000000-s1 params 61951 build 1.77s step 3.91s save_reload 0.49s wall 6.60s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m038-t350000-s1 params 31735 build 1.48s step 2.53s save_reload 0.44s wall 4.96s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m038-t5000000-s1 params 61951 build 1.78s step 3.87s save_reload 0.49s wall 6.66s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m039-t350000-s1 params 31735 build 1.50s step 2.65s save_reload 0.45s wall 5.13s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m039-t5000000-s1 params 61951 build 1.78s step 3.84s save_reload 0.50s wall 6.66s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m040-t350000-s1 params 31789 build 1.48s step 2.63s save_reload 0.44s wall 5.10s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m040-t5000000-s1 params 62021 build 1.79s step 4.03s save_reload 0.50s wall 6.86s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m041-t5000000-s1 params 61951 build 1.79s step 3.68s save_reload 0.50s wall 6.52s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m042-t350000-s1 params 28783 build 1.36s step 2.39s save_reload 0.44s wall 4.75s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m042-t5000000-s1 params 54383 build 1.50s step 3.52s save_reload 0.50s wall 6.06s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m043-t350000-s1 params 33399 build 0.84s step 2.48s save_reload 0.43s wall 4.33s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m043-t5000000-s1 params 64127 build 0.98s step 3.77s save_reload 0.50s wall 5.78s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m044-t5000000-s1 params 118270 build 3.31s step 7.92s save_reload 0.87s wall 12.74s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m045-t350000-s1 params 34315 build 1.64s step 2.13s save_reload 0.47s wall 5.01s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m045-t5000000-s1 params 64267 build 1.86s step 3.63s save_reload 0.54s wall 6.60s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m046-t5000000-s1 params 59903 build 1.78s step 3.29s save_reload 0.49s wall 6.20s max_abs 0 opt Adam
GATE_FAIL configs/W2/M047-t350000-s1.json ValueError: delta0926-w2-m047-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M047-t5000000-s1.json ValueError: delta0926-w2-m047-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M048-t350000-s1.json ValueError: delta0926-w2-m048-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M048-t5000000-s1.json ValueError: delta0926-w2-m048-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M049-t350000-s1.json ValueError: delta0926-w2-m049-t350000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/W2/M049-t5000000-s1.json ValueError: delta0926-w2-m049-t5000000-s1: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_PASS delta0926-w2-m050-t350000-s1 params 31735 build 1.51s step 2.55s save_reload 0.46s wall 5.05s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m050-t5000000-s1 params 61951 build 1.84s step 3.83s save_reload 0.51s wall 6.83s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m051-t350000-s1 params 37375 build 1.62s step 2.76s save_reload 0.46s wall 5.51s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m051-t5000000-s1 params 37375 build 1.64s step 2.07s save_reload 0.43s wall 4.80s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m052-t350000-s1 params 25087 build 1.53s step 1.79s save_reload 0.41s wall 4.33s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m052-t5000000-s1 params 25087 build 1.52s step 1.77s save_reload 0.42s wall 4.30s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m053-t350000-s1 params 17099 build 1.62s step 1.66s save_reload 0.45s wall 4.34s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m053-t5000000-s1 params 17099 build 1.62s step 1.64s save_reload 0.45s wall 4.33s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m054-t350000-s1 params 20171 build 1.70s step 1.72s save_reload 0.46s wall 4.51s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m054-t5000000-s1 params 20171 build 1.70s step 1.75s save_reload 0.47s wall 4.56s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m055-t350000-s1 params 31735 build 1.47s step 2.25s save_reload 0.43s wall 4.81s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m055-t5000000-s1 params 37375 build 1.64s step 2.15s save_reload 0.44s wall 4.90s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m056-t350000-s1 params 20171 build 1.72s step 1.75s save_reload 0.46s wall 4.57s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m056-t5000000-s1 params 20171 build 1.70s step 1.72s save_reload 0.46s wall 4.53s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m057-t350000-s1 params 37375 build 1.62s step 2.20s save_reload 0.44s wall 4.93s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m057-t5000000-s1 params 37375 build 1.63s step 2.19s save_reload 0.44s wall 4.93s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m058-t350000-s1 params 16895 build 1.29s step 1.44s save_reload 0.41s wall 3.82s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m058-t5000000-s1 params 16895 build 1.28s step 1.41s save_reload 0.41s wall 3.79s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m059-t350000-s1 params 61932 build 1.43s step 1.49s save_reload 0.38s wall 3.99s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m059-t5000000-s1 params 61932 build 1.43s step 1.46s save_reload 0.38s wall 3.95s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m060-t350000-s1 params 17099 build 1.62s step 1.67s save_reload 0.45s wall 4.44s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m060-t5000000-s1 params 17099 build 1.62s step 1.65s save_reload 0.46s wall 4.43s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m061-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m062-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m063-t5000000-s1 needs prerequisite teacher artifact 'teacher-int8-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m064-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m065-t5000000-s1 params 117211 build 1.84s step 4.01s save_reload 0.52s wall 7.07s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m066-t5000000-s1 params 62567 build 1.90s step 4.35s save_reload 0.54s wall 7.66s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m067-t5000000-s1 params 62053 build 1.80s step 3.84s save_reload 0.50s wall 6.99s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m068-t5000000-s1 params 61951 build 1.79s step 3.46s save_reload 0.50s wall 6.62s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m069-t5000000-s1 params 61951 build 1.81s step 3.40s save_reload 0.51s wall 6.60s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m070-t5000000-s1 params 61951 build 1.80s step 3.28s save_reload 0.50s wall 6.43s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m071-t5000000-s1 params 61951 build 1.79s step 3.23s save_reload 0.51s wall 6.41s max_abs 0 opt BopAdam
GATE_PASS delta0926-w3-m072-t5000000-s1 params 61951 build 1.84s step 3.30s save_reload 0.52s wall 6.52s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m073-t5000000-s1 params 61951 build 1.82s step 3.33s save_reload 0.52s wall 6.57s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m074-t5000000-s1 params 61951 build 1.81s step 3.29s save_reload 0.51s wall 6.51s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m075-t5000000-s1 params 59903 build 1.80s step 3.81s save_reload 0.50s wall 7.02s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m076-t350000-s1 params 31735 build 1.51s step 2.34s save_reload 0.43s wall 5.25s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m076-t5000000-s1 params 61951 build 1.80s step 4.00s save_reload 0.51s wall 7.14s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m077-t5000000-s1 params 59903 build 1.82s step 3.75s save_reload 0.51s wall 7.17s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m078-t5000000-s1 params 59903 build 1.83s step 3.50s save_reload 0.52s wall 6.79s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m079-t5000000-s1 params 61951 build 1.83s step 3.59s save_reload 0.51s wall 6.88s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m080-t5000000-s1 params 62053 build 1.83s step 3.54s save_reload 0.51s wall 6.90s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m081-t5000000-s1 params 62021 build 1.83s step 3.65s save_reload 0.51s wall 7.00s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m082-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m083-t5000000-s1 params 54383 build 1.57s step 3.28s save_reload 0.51s wall 6.20s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m084-t5000000-s1 params 61951 build 1.83s step 4.36s save_reload 0.53s wall 7.78s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m085-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m086-t5000000-s1 params 54421 build 1.55s step 3.36s save_reload 0.50s wall 6.28s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m087-t5000000-s1 params 62021 build 1.83s step 3.78s save_reload 0.52s wall 7.13s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m088-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m089-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m090-t5000000-s1 params 54383 build 1.57s step 3.27s save_reload 0.50s wall 6.23s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m091-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m092-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m093-t5000000-s1 params 54421 build 1.59s step 3.22s save_reload 0.50s wall 6.19s max_abs 0 opt Adam
GATE_NEEDS_TEACHER delta0926-w3-m094-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_NEEDS_TEACHER delta0926-w3-m095-t5000000-s1 needs prerequisite teacher artifact 'teacher-fp32-a07' (P-T1/P-T2 not trained)
GATE_PASS delta0926-w3-m096-t350000-s1 params 74638 build 1.50s step 2.50s save_reload 0.45s wall 5.32s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m097-t350000-s1 params 74936 build 1.89s step 2.37s save_reload 0.49s wall 5.76s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m098-t350000-s1 params 77218 build 1.61s step 2.18s save_reload 0.48s wall 5.18s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m099-t350000-s1 params 32033 build 1.77s step 2.38s save_reload 0.49s wall 5.60s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m100-t350000-s1 params 34315 build 1.59s step 2.44s save_reload 0.48s wall 5.50s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m101-t350000-s1 params 34613 build 1.90s step 2.68s save_reload 0.55s wall 6.13s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m102-t350000-s1 params 77516 build 1.90s step 2.63s save_reload 0.55s wall 6.08s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m103-t5000000-s1 params 61951 build 1.79s step 3.78s save_reload 0.54s wall 7.13s max_abs 0 opt Adam
GATE_PASS delta0926-w2-p-350-t350000-s1 params 31735 build 1.51s step 2.46s save_reload 0.44s wall 5.49s max_abs 0 opt Adam
GATE_PASS delta0926-w2-p-5m-t5000000-s1 params 61951 build 1.79s step 3.77s save_reload 0.51s wall 7.11s max_abs 0 opt Adam
GATE_FAIL configs/prereq/P-T1-s101.json ValueError: delta0926-prereq-p-t1-s101: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_FAIL configs/prereq/P-T2-s101.json ValueError: delta0926-prereq-p-t2-s101: act_overflow/softmax_quant need binary weights and act_calib='free'
GATE_SOME_FAILED 119/142
```

- **119 PASS.** Every reload gives `max_abs 0`.
  - M020 runs `BopAdam`.
  - Parameter counts as printed: rep-A 31,735; rep-A07-350 61,951; rep-C 61,951; P-350 31,735;
    P-5M 61,951.
- **15 NEEDS_TEACHER.**
- **8 FAIL on the [A20] non-binary guard,** as in §6: M047, M048, M049, P-T1, P-T2. The STUDY's
  gate 13 holds these back; the PLAN_rebase.md rebase 2 plan puts the fix under [A22].
- **Reproduction.** gen → classify → annotate into scratch: `CONFIGS_IDENTICAL`,
  `INDEX_BYTE_IDENTICAL`. configs/index.json has sha256 f7b6e5b9…9288.

### Host-memory RSS gate per horizon

**The anchor's gate** (42abed4b `ablation.rss_gate_from_env`):
- It is set by Job env only.
- It fits host RSS over process epochs 5-104.
- It passes iff baseline + slope × `train.epochs` ≤ `BNJ_RSS_GATE_LIMIT_MB`; on FAIL it exits 5,
  and the arm is not retried.

**The rule, per pack** (a pack never mixes horizons): `BNJ_RSS_GATE_LIMIT_MB = 2,100 + 5 × H` MiB.

| H | gate limit (MiB) |
| --- | --- |
| 500 | 4,600 |
| 1,000 | 7,100 |
| 1,500 | 9,600 |
| 2,000 | 12,100 |

- **Source.** This is the frozen STUDY's PACK-MEM line (Budget l. 920-925): host memory per arm is at
  least 2.1 GB plus slope × H, at the gate-14 slope limit of 5 MB/epoch.
- **Why a per-horizon limit.** With the measured start-of-run RSS of 2,106-2,160 MB (anchor
  PREFLIGHT), the gate then fails any arm steeper than about 4.9 MB/epoch at every horizon, which
  is gate 14's bound. A single 6,144 MiB limit would do otherwise: it would admit 8 MB/epoch at
  H 500 and fail 2 MB/epoch at H 2,000.
- **Pod memory per arm** is max(6 Gi, ceil(limit / 1,024) Gi) = 6 / 7 / 10 / 12 Gi. That way the
  cgroup holds whatever the gate admits.
- **Job sizing.** Each Job's pods are sized for its largest pack. t0 and cells are 8 CPU and 36 Gi
  (the A07 H 2,000 packs: 3 × 12 Gi). The canary is 10 CPU and 36 Gi.
- **How the limit reaches the arms.** Each production pod exports its own pack's limit from
  `pack_meta[JOB_COMPLETION_INDEX].rss_gate_limit_mb`, and the header prints `RSS_GATE_LIMIT_MB`.
  run_pack (0038) passes the environment to every child.
- **Checks.**
  - For every packed run, the pack's limit equals 2,100 + 5 × the config's `train.epochs`
    (RESOLVE_OK below).
  - The header line was run in bash against pack 0: it prints `RSS_GATE_LIMIT_MB 4600 window 5:105`.
- **Finding: gate 14's env name does not exist.** STUDY gate 14 names `BNJ_RSS_GATE_MB_PER_EPOCH` = 5.
  No code reads that variable; the anchor reads only `BNJ_RSS_GATE_LIMIT_MB` and
  `BNJ_RSS_GATE_WINDOW`. The per-horizon limit above is how the 5 MB/epoch bound is realized.

### Memory canary

**Files.** `manifests/delta-canary-job.json` (`kai-delta0926-canary`), `manifests/delta_canary_packs.json`,
`canary_k.py`.

**Shape.**
- The recorded canary used one A10 pod. Future product-specific canaries use the selected
  product and then extend K until the best safe throughput is measured.
- Three sequential phases of 110 epochs each, so the RSS window 5-105 completes in every arm.
- Each phase uses the replica configs at their own `train.epochs`, so the gate projects to the real
  horizon. Validation only, batch 2,790 from the configs.

| phase | arms | RSS limit (MiB) |
| --- | --- | --- |
| E-k4 | rep-A s1-4 | 7,100 |
| E-k5 | rep-A s1-5 (superseded, §7.1: P-350 s1-4 + rep-A s5, 4,600) | 7,100 |
| A07-k3 | rep-C s1-3 | 12,100 |

**Settings.**
- Each phase has its own run_root under `/data/delta-20260927/canary/<phase>`.
- `BNJ_ARM_RETRIES=0` and `BNJ_POD_STALL_RETRIES=0`: an OOM or stall is the measurement, not retried.
- (Superseded by §7.1: every phase now uses `BNJ_STAGE=canary` with disjoint names.) `BNJ_STAGE=canary`, except E-k5, which used `pilot`. Only four stage values exist, and
  E-k4 and E-k5 share run names; `pilot` gives E-k5 a distinct W&B run id in the same `-canary`
  group.

**Logging.**
- nvidia-smi samples per GPU and per process every 10 s.
- run_pack's stdout, including `ARM_STARTED` pids and `POD_MEM`, is teed to `<phase>/pack.log`.

**Output: `k_result.json`.**
- Per arm: GPU peak (pid from `ARM_STARTED`) and the RSS_GATE line (slope, baseline, projection,
  verdict).
- Per phase: card memory, pod GPU peak, host peak (POD_MEM), OOM flag, k_accepted.
- Per class: `k_by_class`, the largest accepted K.
- The packer reads it through `--k-result`. Until then the manifests are labelled PLANNING.
- Smoke test on synthetic logs: a PASS and a FAIL RSS line parse, pids map to arms, and an OOM gives
  K − 1.

**Expected GPU-hours (projection, not a measurement).** Basis: epochs × K × 22.75 pod-seconds per
run-epoch (STUDY Budget), with A07 × r for r ∈ {1, 2}.

| phase | GPU-hours |
| --- | --- |
| E-k4 | 2.78 |
| E-k5 | 3.48 |
| A07-k3 | 2.09 (r=1) / 4.17 (r=2) |
| **total** | **8.35 / 10.43** |

This excludes pip install, calibration and the epoch-0 traces. `activeDeadlineSeconds` is 57,600
(16 h).

**Not built here.** The gate-7 determinism probe (two pods, 21 epochs, per class) and canaries for
the other architecture classes.

### Packs

The packs are PLANNING: K[E] = 4 (estimate from the measured 4,354 MiB) and K[A07] = 3 (the STUDY's
planning value), on the 24GB class.

```
t0:    7 pods / 20 arms, parallelism 7 (rep-A 4,4 at H 1,000; rep-C 3,3,2 at H 2,000; rep-A07-350 3,1 at H 500)
cells: 83 pods / 220 arms, parallelism 7 = the 10-pod cap minus 3 t0 pods past the epoch-500 gate   [superseded, §7.1]
after_teacher: 12 runs (M027, M035, M036; deferred in the frozen STUDY, X1)
unpacked: cache_not_built M009, M038, M040, M041; floor_untraced M006; GATE_FAIL M047, M048, M049, P-T1, P-T2
RESOLVE_OK delta_w2_t0_packs.json packs 7 arms 20 [(500, 4600, 6), (1000, 7100, 7), (2000, 12100, 12)]
RESOLVE_OK delta_w2_cells_packs.json packs 83 arms 220 [(500, 4600, 6), (1000, 7100, 7), (1500, 9600, 10), (2000, 12100, 12)]
RESOLVE_OK delta_canary_packs.json packs 3 arms 12 [(1000, 7100, 7), (2000, 12100, 12)]
```

The 240 packable runs (220 cells and placebos plus 20 replicas) equal the frozen STUDY's
"packable today" count (Budget).

### Lint, offline

Run with `KUBECONFIG=/nonexistent/kubeconfig`; exit code 2, from the empty node map only (§2):

```
== manifests/delta-w2-t0-job.json :: kai-delta0926-w2-t0 ==
  ERROR  NO product in the required list is reachable: the pod requests nvidia.com/gpu but every listed product needs a different resource name. This job can never schedule.
  WARN   required-list product(s) match no node in the cluster (typo, or the hardware is gone): NVIDIA-A10, NVIDIA-GeForce-RTX-3090
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 4 arms per pod declared.
== manifests/delta-w2-cells-job.json :: kai-delta0926-w2-cells ==
  ERROR  NO product in the required list is reachable: the pod requests nvidia.com/gpu but every listed product needs a different resource name. This job can never schedule.
  WARN   required-list product(s) match no node in the cluster (typo, or the hardware is gone): NVIDIA-A10, NVIDIA-GeForce-RTX-3090
  WARN   parallelism=7 but completions=83: at most 7 run at once. This is a self-imposed ceiling, not a cluster limit.
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 4 arms per pod declared.
== manifests/delta-canary-job.json :: kai-delta0926-canary ==
  ERROR  NO product in the required list is reachable: the pod requests nvidia.com/gpu but every listed product needs a different resource name. This job can never schedule.
  WARN   required-list product(s) match no node in the cluster (typo, or the hardware is gone): NVIDIA-A10
  WARN   backoffLimitPerIndex=1: one blip kills an index. Suggest 3.
  note   [rule PACK] 5 arms per pod declared.
(rules: docs/infrastructure/nrp-nautilus-setup.md -> 'Scheduling, GPU pools and job shape')
```

- `bash -n` passes on all three headers.
- The ConfigMap name, bundle sha and manifest sha stay as placeholders for cluster-ops, from the
  Delta freeze.


### 7.1 Corrections from the PREFLIGHT build half (2026-09-28)

These answer the new-files items in `campaigns/2026-09-27-delta-screen/PREFLIGHT.md`. The bundle
already frozen for the running canary (e6fc6cd9, `campaigns/2026-09-27-delta-screen/bundle/`) is not
touched. The canary and packs described here are the *next* build.

**(1) Replica seeds above n now stop at 500 in their configs.**

The frozen STUDY (l. 358-359) says seeds above n stop at 500, with n = 4 (l. 576-577). Before this
fix, their configs carried 1,000 or 2,000 epochs and the t0 Job passed no stop-after. Now:

- `generate_delta.py` writes `train.epochs` = 500 for rep-A s5-8 and rep-C s5-8. These rows are
  flagged `extension_seed_stops_at_500`.
- The value comes from `wave2_amendments.json` `extension_seed_horizon: 500`, which cites the STUDY.
- The rest of their schedule is never read. STUDY gate 5 already requires the cosine and PID inputs
  for epochs 1..500 to be the same at H 500 and at 1,000 or 2,000.
- The runner, the RSS projection and the pack all see 500, and there is no pod-wide stop.
- **Caveat.** If the seed rule later raises n, those seeds have to be regenerated at the long
  horizon and restarted. A resume with a changed `train.epochs` fails the `config_sha256` check.

**t0 repack.** t0 is repacked so each pack holds one horizon and one replica family. Pack 3 no
longer mixes rep-A07-350 with rep-C. The result is 8 pods / 20 arms:

| family | H | pods (arms) |
| --- | --- | --- |
| rep-A s1-4 | 1,000 | 1 (4) |
| rep-A s5-8 | 500 | 1 (4) |
| rep-A07-350 | 500 | 2 (3, 1) |
| rep-C s1-4 | 2,000 | 2 (3, 1) |
| rep-C s5-8 | 500 | 2 (3, 1) |

- t0 parallelism is 8.
- Three t0 pods run past the epoch-500 gate (rep-A s1-4 and the two rep-C s1-4 pods), so cells
  parallelism stays at 7.

**Canary phases.** The canary phases are rebuilt so each holds one horizon and the names are disjoint
across phases:

| phase | arms | H | RSS limit (MiB) |
| --- | --- | --- | --- |
| E-k4 | rep-A s1-4 | 1,000 | 7,100 |
| E-k5 | P-350 s1-4 + rep-A s5 | 500 | 4,600 |
| A07-k3 | rep-C s1-3 | 2,000 | 12,100 |

- Every phase now runs with `BNJ_STAGE=canary`; the `pilot` workaround is gone.
- The projected GPU-hours are unchanged at 8.35 / 10.43.

**Check.** Every packed run was resolved with `run_pack.resolve_pack`. Each pack holds one horizon,
each limit equals 2,100 + 5 × `train.epochs`, and every replica seed above 4 has `train.epochs` 500:

```
RESOLVE_OK delta_w2_t0_packs.json packs 8 arms 20 one horizon per pack
RESOLVE_OK delta_w2_cells_packs.json packs 87 arms 228 one horizon per pack
RESOLVE_OK delta_canary_packs.json packs 3 arms 12 one horizon per pack
```

**(2) The gate and the floor tracer now import the applied tree, never this directory.**

Python puts a script's own directory first on `sys.path`. This directory holds the UNPATCHED
`newmods/`, and anchor 0023 patches `deepsets.py` after the copy. So the §6/§7 M006 lines (20,742)
were built with the unpatched module.

The fix:
- `gate_cpu.py` and `trace_floors_delta.py` drop their own directory (and `''` when the cwd is this
  directory) from `sys.path`.
- `trace_floors_delta.py` loads `generate_delta.py` by file path.
- Both assert that every imported `newmods.*` or `bnhgq2.*` module comes from the tree.
- `newmods/deepsets.py` is the only newmods file that differs from the tree's copy (`cmp`).
- The full gate was re-run from the scratch cwd (142 pairs, 11.6 min): 119 PASS, 15 NEEDS_TEACHER,
  8 FAIL, the same outcomes as §7.

The lines for every entry that imports a newmods module:

```
GATE_PASS delta0926-w2-m004-t350000-s1 params 20171 build 1.68s step 1.93s save_reload 0.45s wall 4.26s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m004-t5000000-s1 params 20171 build 1.66s step 1.71s save_reload 0.45s wall 4.00s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m006-t350000-s1 params 20750 build 0.27s step 0.89s save_reload 0.23s wall 1.57s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m006-t5000000-s1 params 20750 build 0.27s step 0.87s save_reload 0.23s wall 1.54s max_abs 0 opt Adam
GATE_PASS delta0926-w2-m020-t5000000-s1 params 61951 build 1.80s step 3.90s save_reload 0.52s wall 6.62s max_abs 0 opt BopAdam
GATE_PASS delta0926-w3-m053-t350000-s1 params 17099 build 1.61s step 1.68s save_reload 0.46s wall 4.35s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m053-t5000000-s1 params 17099 build 1.59s step 1.63s save_reload 0.45s wall 4.26s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m054-t350000-s1 params 20171 build 1.69s step 1.72s save_reload 0.45s wall 4.47s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m054-t5000000-s1 params 20171 build 1.67s step 1.72s save_reload 0.46s wall 4.48s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m056-t350000-s1 params 20171 build 1.71s step 1.75s save_reload 0.46s wall 4.58s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m056-t5000000-s1 params 20171 build 1.71s step 1.72s save_reload 0.46s wall 4.55s max_abs 0 opt Adam
GATE_PASS delta0926-w3-m071-t5000000-s1 params 61951 build 1.79s step 3.63s save_reload 0.50s wall 6.77s max_abs 0 opt BopAdam
GATE_SOME_FAILED 119/142
```

- M006 now builds with **20,750** params, matching the bundle and PREFLIGHT.md.
- Bop (M020, M071) and Linformer (M004, M053, M054, M056) give the same counts as before, because
  their modules are byte-equal copies.

**M006 floor.**
- `static_floor.floors` cannot build a Deep Sets body. So `trace_floors_delta.py` now prices
  non-transformer bodies through the runner's own builder (`run_engram.builder_for`) with
  `static_floor.set_floor(model, 'zero', sample)`.
- The self-check runs both paths on arms A and A07-350 and requires them to agree:
  `FLOOR_SELFCHECK A stored 171526 retraced 171526 via_builder 171526 OK`;
  `FLOOR_SELFCHECK A07-350 stored 343053 retraced 343053 via_builder 343053 OK`.
- M006 (350k and 5M share one signature) comes out at **zero floor 0**:
  `FLOOR M006 A07-350 zero 0 ... 20,750 params`, width check 8/8 ok. A Deep Set has no softmax
  tables, so every WRAP datalane reaches 0 bits.
- The [ND] rule for M006 is therefore "EBOPs > 0" plus the accuracy threshold.
- Floors are now traced for 74 of 81 signatures.

**Consequences.**
- M006's 8 runs are now packable in 4 pods (class Deep Sets, planning K 3, `k_class_unmeasured`).
  The cells phase is 87 pods / 228 arms.
- Packable runs rise from 240 to 248. The frozen STUDY's Budget counted 240 with M006 excluded, so
  PREFLIGHT should restate it.
- gen → classify → annotate still reproduces the outputs: `CONFIGS_IDENTICAL`,
  `INDEX_BYTE_IDENTICAL`. configs/index.json has sha256 8a6f262f….
- Lint: exit 2, from the empty node map only. `bash -n` passes on all three headers.
