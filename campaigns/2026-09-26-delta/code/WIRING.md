# WIRING.md — where the new files plug in (anchor tree; updated 2026-09-28)

Tree: `apply_anchor.sh` = the leak-fixed regime-B anchor bundle 42abed4b (ConfigMap
`kai-chang0926-code-42abed4b5d`, manifest 041f981a…bd42) + `patches-anchor/0001-0038` + `newmods/`.
The tarball series (`patches/0001-0025`, `apply.sh`) is kept for the public repo and the
stand-in tests only. Nothing here edits a bundle file except through a patch.

## Modules (new-files owner) and the function that calls them

| module | caller in the applied tree | key | what the call does |
| --- | --- | --- | --- |
| `newmods/deepsets.py` | `run_engram.builder_for(...).builder` → `ablation.matching_initialization` dispatch (patch 0023) | `arch.body == "deepsets"` | `deepsets.deepsets_initialization(cfg, sample, seed)`; anchor 0023 patches it after the copy to follow `quant.act_overflow` / `quant.i_decay_speed` |
| `newmods/deepsets.py` | `ablation.expected_binary_layers(cfg)` (0023) | `arch.body` | the Deep Sets binary layer set for `ablation.binary_gate` |
| `newmods/bop.py` | `ablation.delta_optimizer_for(cfg, model)` (0024; also `restore_checkpoint`) | `train.binary_optimizer == "bop"`, `train.bop_gamma`, `train.bop_tau` | `BopAdam`; `optimizer.variables` has Adam's length and order; with `train.optimizer adam_default` the non-binary variables get Keras Adam defaults (PLAN_rebase.md decision 1) |
| `newmods/linformer.py` | `qat.build_qat_model` block loop (anchor 0033) | `arch.attn_kind == "linformer"`, `arch.linformer_k` | Linformer attention with the builder's own [A20] closures; export refused |
| `newmods/diag_attention.py` | post-run, on the selected checkpoint (not wired into run_study) | always-on diagnostic (`delta.json` `always_on_diagnostics`) | `diag_attention.run(model, x_val, y_val, valid)` → `diag_attention.json` beside the run; `valid` from the raw pT column |
| `newmods/diag_input_proj_rows.py` | offline, any `.keras` checkpoint | Z04 / Z08 | `from_model(model, 'input_proj')` (`'ds_phi1'` for Deep Sets) |
| `newmods/diag_latent_binary_gap.py` | offline | Z08 | `run(model, x_val, y_val)`; eager calls only |

## Offline pipeline (new-files owner; CPU; nothing launches)

```
code/apply_anchor.sh <tree>                                              # pins 42abed4b; APPLY_ANCHOR_ALL_PASS
python3 code/generate_delta.py --out <scratch>                          # floors untraced on the first pass
PYTHONPATH=<tree>/code tests_patches/pyenv.sh code/trace_floors_delta.py --index <scratch>/index.json \
    --tree-label "apply_anchor.sh 42abed4b + patches-anchor/0001-0038 + newmods"   # floors_delta.json
python3 code/generate_delta.py                                          # configs/ (+ wave2_amendments.json, frozen STUDY lists)
tests_patches/pyenv.sh code/classify_series.py --tree <tree>/code       # status from the tree's validator
PYTHONPATH=<tree>/code tests_patches/pyenv.sh code/gate_cpu.py --index configs/index.json --one-per-arm \
    --results-out gate_results.json
python3 code/annotate_index.py                                          # gate, depends_on, patch_status
python3 code/manifest_wave2.py [--k-result k_result.json]               # packs + Job templates + canary (PLANNING without k_result)
KUBECONFIG=/nonexistent python3 nrp-lab/nrp_doctor.py lint code/manifests/*.json
python3 code/generate_delta.py --standin --amendments none              # configs-standin/ (tarball tests only)
```

`generate_delta.py` reads the anchor bundle from `anchor_arms.json` `anchor_bundle.paths_tried_in_order`
(the training-batch tarball, then the 42abed4b ConfigMap payload), sha-checked; `--anchor-bundle
<path> --anchor-sha <sha>` points it at another bundle (the regime-B production bundle, next rebase).
Every cell is the anchor's own arm config at the cell's seed, so `train.ebops_trace_every` (regime B)
and every other anchor key are carried from the base, never set by a Delta entry (the generator
refuses a delta that sets `train.ebops_trace_every`, `split_seed`, `validation_split` or `order_seed`).

## Launch path (run_pack.py after patch 0038 / tarball 0025)

- ConfigMap layout the manifests expect (freeze step, cluster-ops or ml-engineer at PREFLIGHT):
  the `apply_anchor.sh` tree as `code/`, plus `code/campaigns/delta0926/` = `configs/index.json`,
  `configs/**` (as `configs/`), `manifests/delta_*_packs.json`, `canary_k.py`. `BNJ_CAMPAIGN_DIR`
  points there; `run_study.py` reads `index.json` and `configs/<file>` from it.
- Packs are dict-form: run **names** (resolved against the unique `index.json` `name`), `run_root`
  `/data/delta-20260927/w2` (canary: `/data/delta-20260927/canary-v2/<phase>`; v1 `canary/` is the c6017 record), per-pack `data_root`
  (the anchor's gated 90/10 cache `/data/chang-n64-20260926`, split_seed 1; or a Delta Z10 cache
  `/data/delta-20260927/caches/<key8>`). `run_pack.py` exports them to each child as
  `BNJ_RUN_ROOT` / `BNJ_DATA_ROOT` and refuses a conflicting environment value (exit 2), an unknown
  name (exit 2) or a dict without `run_root` (exit 2), before any arm starts.
- **RSS gate (anchor 42abed4b).** Each pack carries `rss_gate_limit_mb = 2,100 + 5 x H` (MiB; the frozen
  STUDY's PACK-MEM line) and `mem_gi_per_arm = max(6, ceil(limit/1024))`. The Job header exports
  `BNJ_RSS_GATE_WINDOW=5:105` and `BNJ_RSS_GATE_LIMIT_MB` of the pod's own pack (read from `pack_meta` at
  `JOB_COMPLETION_INDEX`); run_pack (0038) passes the environment to every child; a FAIL exits 5 and is
  not retried. The canary sets the limit per phase on the command line.
- **Memory canary.** `manifests/delta-canary-job.json`: one A10 pod, phases E-k4, E-k5, A07-k3 (replica
  configs, 110 epochs each), nvidia-smi sampler + teed `pack.log` (ARM_STARTED pids, POD_MEM);
  `canary_k.py` writes `/data/delta-20260927/canary-v2/k_result.json`; copy to `code/k_result.json` and rerun
  `manifest_wave2.py` to replace the planning K.
- **Gate 15, GPU fingerprint (2026-09-28, REGRESSION_TICKET of 2026-09-27-delta-screen).** Every Delta pod
  (t0, cells, canary; `manifest_wave2.py` `header()` → `gate15_lines()`) runs
  `campaigns/delta0926/fingerprint_check.py --env-report --data-root /data/chang-n64-20260926` after
  `CACHE_READY` and before the first `run_pack.py`. It builds rep-A s1 as `run_study.train` →
  `ablation.run_training` does, traces `initial_ebops` and prints `FINGERPRINT <v> expected 11559681`;
  mismatch → `GPU_FINGERPRINT_MISMATCH <v>`, exit 9 (no GPU: exit 8), no arm starts. It logs driver, GPU,
  TF/CUDA/cuDNN build and `pip freeze` first. Shipped by `freeze_delta.py` beside `canary_k.py` (outside
  `run_study.manifest()`, so the manifest sha does not move). The canary runs under
  `/data/delta-20260927/canary-v2` and excludes `hcc-nrp-shor-c6017.unl.edu` until the discriminator
  (`2026-09-27-delta-screen/manifests/discrim-*.json`) clears it.
- The Job headers `unset BNJ_DATA_ROOT BNJ_RUN_ROOT`, set `BNJ_CAMPAIGN_DIR` and `BNJ_STAGE`
  (`production`; `canary` for the memory canary, which gives the canary its own W&B id/group), unset
  `WANDB_PROJECT` (configs say `BNJetTag-Delta`), and check `READY.json` of every cache the pod's
  pack reads.

## Open items

- **Superseded (2026-09-28):** the 77f1ca4e regime-A base and the `apply_anchor.sh` default-path note. The
  series and configs now sit on 42abed4b (GATES.md §7).
- **Non-binary path.** M047-M049 and the teachers P-T1/P-T2 do not build under the [A20] guard. This is the
  STUDY's gate 13, fixed by [A22] in the anchor, not in Delta. As long as the teachers cannot run,
  M027/M035/M036 stay `after_teacher`.
- **Z10 caches** for M009, M038, M040, M041 (`/data/delta-20260927/caches/<key8>`, split_seed 1): not built.
- **Other canaries.** The determinism probe (gate 7, two pods × 21 epochs per class) and memory canaries
  for the architecture classes other than E and A07 are not built.
- **Gate-14 env name.** STUDY gate 14 names `BNJ_RSS_GATE_MB_PER_EPOCH`, which no code reads. The
  per-horizon `BNJ_RSS_GATE_LIMIT_MB` realizes the 5 MB/epoch bound.
- `diag_attention.py` is a post-run script; nothing in `run_study` calls it yet.
