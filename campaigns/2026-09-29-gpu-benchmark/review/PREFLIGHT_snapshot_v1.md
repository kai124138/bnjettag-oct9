# PREFLIGHT — 2026-09-29-gpu-benchmark, build half (ml-engineer)

Date: 2026-09-29. Status: **built, nothing applied**. Telemetry tooling only; nothing here is a result.

- **Governing design.** STUDY.md [D1]-[D6]. The orchestrator ruled on 2026-09-29 that the pre-registered STUDY governs,
  so K_low follows [D2]. STUDY was `designed` at build time. The remaining STUDY-against-build mismatches are listed in
  "Alignment with STUDY.md".
- **Code sha.** Repo HEAD `165793d`; the working tree is dirty (the whole campaign directory is untracked; see "Code sha").
- **Bundle.** 42abed4b, unchanged.
- **ConfigMaps.** `kai-chang0926-code-42abed4b5d` and `kai-chang0926-fp-e9511d1aeb` exist and are unchanged. The new
  driver payload is `kai-gpubench-driver-4d2dcd7d9c` (driver sha256 `4d2dcd7d…`); cluster-ops creates it (placeholder
  section at the end).
- **Generator.** `python3 code/gen_bench.py`. It reads the newest `code/evidence/node_survey_*.json` and defaults to
  `--k-low-rule study-d2`. It is fed by `code/node_survey.py`.
- **Notebook.** `plan.md` § Phase 2.

## What was built

| file | sha256 | role |
| --- | --- | --- |
| `code/bench_driver.py` | `4d2dcd7d…` | harness, shipped in its own ConfigMap. `arm` runs one config; `pod` runs one product's phases and the 60 s sampler |
| `code/gen_bench.py` | `bb09d7aa…` | writes the 7 Jobs, the driver ConfigMap and `manifests/bench_plan.json`. `--probe PRODUCT:K:N` writes the [D4] probe. Deterministic (`GENERATOR_IDEMPOTENT`) |
| `code/node_survey.py` | `173452b4…` | live node list → `code/evidence/node_survey_20260929T065531Z.json` (read 06:55:31Z) |
| `code/bench_summary.py` | `6f77e185…` | analysis. `bench`: the benchmark; `a10`: the pilot baseline, with offset windows for falsifier (i); `probe`: G_obs and Q_p |
| `code/make_synthetic_cache.py`, `code/cpu_gate_bench.sh`, `code/test_bench.py` | | CPU gate and unit tests |
| `manifests/kai-gpubench-<slug>.json` ×7, `configmap-bench-driver-4d2dcd7d.json`, `bench_plan.json` | | generated, never hand-edited |

## W&B off without touching the compute path: `remote=False`

`bench_driver.py arm` calls the frozen `ablation.run_training(cfg, arrays, info, out, remote=False, stop_after=21,
model_builder=run_engram.builder_for(info), epoch_observer=engram.diagnostic_observer())`. These are the same arguments as
`run_study.py:135-137`, except `remote`. The following was checked by reading `bnhgq2/ablation.py` in the 42abed4b extraction:

- l. 746 `wandb_run = None`; l. 747-756 is the only `if remote:` block (import wandb, `run_stage`, `wandb.init`).
- Every later W&B use is guarded by `wandb_run`: l. 758-761 (pause at start), l. 942-949 (per-epoch log, summary, and
  the artifact at `remote_every_epochs`), l. 951-953 (pause), l. 990-999 (end of training), and `record_divergence` l. 412
  (called at l. 776, 807, 834 with `wandb_run`).
- `remote` appears nowhere else. l. 947 is the config key `remote_every_epochs`, inside the guarded block.
- `seconds=` is `elapsed`, taken at l. 874, **before** any W&B call, in both modes. So the benchmark's epoch times and
  production's are measured the same way. The only difference is that W&B's background process competes for CPU in
  production and not here: a small bias, in one direction (the benchmark is slightly faster).
- The remaining W&B imports in the tree are all inside functions this path never calls: `train.py:180, 360, 504, 532`,
  `ebops_target.py:190`, `run_engram.validate_tracking_destination`. The CPU gate confirms `WANDB_IMPORTED False` with
  wandb 0.28.0 installed.

`run_study.train` preconditions (run_study.py), against the harness:

| run_study.py | what | bench_driver `arm` |
| --- | --- | --- |
| 98-100 | TF32 disabled and asserted; GPU asserted | same; the GPU assert is skipped only under `--test-cpu`, which is refused in a pod |
| 101-102 | config by index row | by name; config file sha256 == index `config_sha256` (stronger) |
| 103 | `run_engram.validate_cfg` | same |
| 104-106 | `validate_tracking_destination`, `run_stage` | **not called** (W&B off by design) |
| 107-112 | run dir, DIVERGED check | `<run-root>/runs/<name>`; refuses a non-empty directory (exit 11), so a run can never resume |
| 114-121 | SIGTERM handler, `run.lock`, `BNHGQ2_CODE_SHA256` = `manifest()`, `source_manifest.json` | same, plus manifest == `041f981a…` (exit 13 otherwise) |
| 122-126 | `contract`, `cost_contract.json`, static-infeasible refusal, `run_engram.load_cache` | same (every array hash; the 620,000-row split); then prints `BENCH_CACHE` with the digests the loader computed |
| 135-139 | `run_training(remote=True)`, `Diverged` → exit 3 | `remote=False`, exit 3; `ResourceExhaustedError` → `ARM_OOM`, exit 7 |
| 148-150 | COMPLETE rename, `verify_selected` | same; an `AssertionError` from it prints `CHECKPOINT_VERIFICATION_FAIL`, exit 6 (recorded, not raised) |

No log saved in this repository shows `CHECKPOINT_VERIFICATION_PASS` from a GPU. (The grep covered local files only; a
Delta pause on the PVC may have printed it.) Here it runs on every product, and a FAIL is a finding, not a crash.

## Config builds

The benchmark draws names from four arms of the bundle's campaign index: E = A s1-s8 then B s1-s8 (index rows 0-7, 8-15);
A07 = C s1-s8 then A07-350 s1-s8 (rows 16-23, 48-55). The configs are read by name from the extracted tree, never copied.
Checked with a full-key diff of all eight seeds (`code/evidence/config_diff.log`):

- B differs from A only in `train.ebops.pid.target_ebops` 350000 → 250000 (plus name, arm and question): same
  architecture and compute.
- A07-350 differs from C only in `target_ebops` 5000000 → 350000 (plus name, arm, question).
- Seeds differ only in `seed`, `order_seed` and names.

The bundle's own `campaigns/chang0926/cpu_gate.py --only a,b,c,a07-350` was re-run on a fresh extraction with the pinned CPU
environment (`code/evidence/cpu_gate_configs_42abed4b.{log,json}`). It builds each config, runs the binary gate, the traced
EBOPs, one training step at batch 2,790, and a save/reload within atol = rtol = 2e-6, with EBOPs re-traced equal:

```
CONFIG_PREFLIGHT_PASS chang0926-a-n64-s1 params 31735 kernel_bias_pos 6253 initial_ebops 9429139 reload_max_abs_diff 0.0 zero_floor 171526 floor_retraced 171526 production 1
CONFIG_PREFLIGHT_PASS chang0926-b-n64-s1 params 31735 kernel_bias_pos 6253 initial_ebops 9429139 reload_max_abs_diff 0.0 zero_floor 171526 floor_retraced 171526 production 1
CONFIG_PREFLIGHT_PASS chang0926-c-n64-s1 params 61951 kernel_bias_pos 11653 initial_ebops 13805846 reload_max_abs_diff 0.0 zero_floor 343053 floor_retraced 343053 production 1
CONFIG_PREFLIGHT_PASS chang0926-a07-350-n64-s1 params 61951 kernel_bias_pos 11653 initial_ebops 13805846 reload_max_abs_diff 0.0 zero_floor 343053 floor_retraced 343053 production 1
PREFLIGHT_ALL_PASS 32 production 32 pilot_only 0
```

Across all 32 configs:
- Parameters as printed: A and B 31,735 (16 configs); C and A07-350 61,951 (16 configs).
- `reload_max_abs_diff 0.0` on every config.
- 32 × `TRACE_EVERY_OK … k 10 epochs 7000 traced_epochs 701`.

## CPU build/reload gates (`code/cpu_gate_bench.sh`, on driver `4d2dcd7d…`)

Setup: pinned CPU environment (tensorflow 2.21.0, keras 3.15.0, hgq2 0.1.9, quantizers 1.2.2, numpy 2.5.0, scikit-learn
1.9.0, h5py 3.14.0, hls4ml 1.3.0, wandb 0.28.0) via `uv run --with`, on the 42abed4b extraction. The pod environment is
copied: threads, TF32 off, `BNJ_RSS_GATE_LIMIT_MB=8192`, `WANDB_MODE=disabled`.

`run_engram.load_cache` needs the full 620,000-row split (l. 216-219), so a tiny cache cannot pass it. The gate therefore
builds a **full-size synthetic cache** (random, seed 0, 466 MB, `make_synthetic_cache.py`), loads it through the real loader
with every hash check, and slices it afterwards to 11,160 / 1,240 rows. The slicing is the only test-only step, behind
`--test-rows`.

**1. One arm, A s1, `--stop-after 2`** (`code/evidence/cpu_gate_arm_a-s1.log`):
```
ARM_MANIFEST_SHA 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42 expected 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42 OK
BENCH_CACHE {"x_train": "f7dc3cb254b8c32210b86d0ee490280f7d03d43ab02b2043d4c186e4177ad10d", "x_val": "6045efc877e7cdd34101af91aa2f03ca0959d6c318c9abb6ed60f49fd6bd4315", "y_train": "e54e08956a11d795783456c5ba9c9811b0b4ac954617299fcd9536b674d83c17", "y_val": "474ae3658cdf83005d5eb78e9aceef96a51c4406a49c2bcde8c39249011458d2"}
[train] chang0926-a-n64-s1 params=31735 resume_epoch=0 initial_ebops=9515667
[epoch 1/7000] EBOPs=9605779 target=350000 above_floor=9434253 feasible=0 degenerate=0 beta=1e-07 val_AUC=0.508496 val_accuracy=0.210484 seconds=12.5 checkpoint=- ebops_trace_seconds=3.84 ebops_trace_over_epoch=0.308 loss=2.581331 host_rss_mb=998
[epoch 2/7000] EBOPs=untraced in_training_ebops=9681043 target=350000 beta=1e-07 val_AUC=0.484001 val_accuracy=0.197581 seconds=6.2 checkpoint=epoch-0002 ebops_trace_seconds=0.00 ebops_trace_over_epoch=0.001 loss=2.572640 host_rss_mb=1757
CHECKPOINT_VERIFICATION_PASS {"index": 0, "name": "chang0926-a-n64-s1", ... "status": "verified_canary", ... "reload_ebops_check": "stored", ...}
WANDB_IMPORTED False
ARM_DONE chang0926-a-n64-s1 exit 0 wall_seconds 31.4 utc 2026-09-29T07:21:03Z
```
The `CHECKPOINT_VERIFICATION_PASS` line is abridged here; it is complete at line 12 of the log. The post-stop check, all
in `run_study.verify_selected`:
- reload the selected checkpoint;
- stored EBOPs equal to the recorded value;
- validation replay, AUC and accuracy within **atol 1e-7**, rtol 0.

Other checks from this run:
- `params=31735` is the pilot's A s1 value.
- The first gate run, on driver `9ee0e675`, printed the same EBOPs, AUC and loss (deterministic on CPU). This log
  replaced that one.
- Everything lands under the given run root; there are 0 `wandb` files.

**2. Pod mode: three phases and an injected OOM** (`code/evidence/cpu_gate_pod.log`; arm logs, phase results, samples
and the summary are in `code/evidence/cpu_gate_pod/`):
```
PHASE_DONE p1-E-k2 wall_seconds 52.1 outcomes {"ok": 2} 2026-09-29T07:21:55Z
ARM_EXIT p2-A07-k2 chang0926-c-n64-s2 7 outcome oom epochs 0 verification none 2026-09-29T07:22:02Z
ARM_OOM_RECORDED p2-A07-k2 chang0926-c-n64-s2 (no retry; the phase continues)
ARM_EXIT p2-A07-k2 chang0926-c-n64-s1 0 outcome ok epochs 2 verification PASS 2026-09-29T07:22:57Z
PHASE_DONE p2-A07-k2 wall_seconds 67.1 outcomes {"ok": 1, "oom": 1} 2026-09-29T07:23:02Z
PHASE_DONE p3-E-k1 wall_seconds 40.1 outcomes {"ok": 1} 2026-09-29T07:23:42Z
BENCH_DONE cpu-gate phases 3 samples 17 2026-09-29T07:23:42Z
```

**3. Negative paths** (`code/evidence/cpu_gate_negative.log`). Each exits before any work and creates no directory:

| case | result |
| --- | --- |
| used bench root | `BENCH_ROOT_NOT_EMPTY`, exit 11 |
| used arm directory | `ARM_ROOT_NOT_EMPTY`, exit 11 |
| names not the first K of the class | `BENCH_PLAN_ERROR`, exit 2 |
| test flags with `KUBERNETES_SERVICE_HOST` set | `BENCH_TEST_FLAGS_REFUSED`, exit 2 |
| no `--test-cpu` on a GPU-less machine | `AssertionError: Training requires GPU`, exit 1 |

**4. Unit tests** (`python3 code/test_bench.py`, stdlib only; `code/evidence/test_bench.log`): `ALL_PASS 12`.
- Formula checks:
  - steady state: u = t gives t, and (9 × 130 + 245)/10 = 141.5 = u + trace/10;
  - R = K × 3600 / s;
  - CPU cores from `usage_usec` deltas: 120 s of CPU in 60 s = 2.0 cores;
  - K_rule and the caps; both K_low rules;
  - deadlines: pod 39,000 s; Job 60,600 s.
- The Job shape: no `podFailurePolicy`, `WANDB_MODE=disabled`, last line `exec python`.
- The probe Job's shape.
- Parsing:
  - a resumed attempt is ignored at offset 0 and replaces re-run epochs at offset 20;
  - the traced epochs are 1, 10, 20;
  - there are 18 untraced epochs per arm.
- The exclusion flags. A logged `CUDA_ERROR_OUT_OF_MEMORY` line in an arm that finished all 21 epochs is **not** an
  OOM; a failed allocation that ended the arm is.
- The probe's G_obs and Q_p.
- The sampler row, with a fake `nvidia-smi` on PATH and a fake cgroup v2 directory.

Not verifiable here: everything GPU-side.
- nvidia-smi and compute-app pids: the pilot pods show `ARM_STARTED` pids equal to the `nvidia-smi` pids.
- cgroup v2: the pilot `POD_MEM` lines read `/sys/fs/cgroup/memory.current`.
- Per-process memory on non-A10 cards, and the fingerprint on sm_89 / sm_80 cards (TF build info lists sm_80 and sm_89
  SASS).

## Node survey and K per product

Source: `code/evidence/node_survey_20260929T065531Z.json`, from the live node list at 06:55:31Z (a list call; single-node get
is forbidden).
- **Schedulable**: Ready, not cordoned, no NoSchedule/NoExecute taint, and not excluded.
- **Excluded hostnames** (in every Job): `hcc-nrp-shor-c6017.unl.edu`, `k8s-chase-ci-07.calit2.optiputer.net`,
  `nautilus-ext-gpu01.fullerton.edu` (nrp_doctor `KNOWN_BAD_NODES`) and `ren-gp-argo-01.madren.org`.
- **Resource keys**: each product's key was read from the nodes' nonzero allocatable, and each matches the brief's list.
- **Card MiB**: from the `nvidia.com/gpu.memory` label. For the A10 the label (23,028) equals the in-pod `nvidia-smi`
  figure. One L40S node (`swan-interlink`, a not-Ready virtual node) carries no label.
- **Quota** (05:55Z): `requests.nvidia.com/a100` 23 / 24; pods 158 / 200. There is no quota on `nvidia.com/gpu`,
  `rtxa6000` or `a40`.

Rules (`gen_bench.py`):
- **K_rule** = floor(0.90 × card MiB / per-process MiB). The per-process figures are A10 peaks under TF allow_growth: E 4,350
  and A07 8,446 MiB (training-batch RUN.md, "Takeover check"). STUDY [D2] cites 4,354 for E; no K changes on any card.
- **K_run** = min(K_rule, node cap, 16 names). The node cap is the largest K that some schedulable node holds at 2 CPU and
  8 Gi per arm, after reserving 2 CPU and 16 Gi per node for daemons.
- **K_low, per STUDY [D2]**: the class's A10 K (E 4, A07 2), or K_run − 1 where K_run ≤ that.
- **Pod request** = 2 CPU and 8 Gi × the largest K (rule PACK).

| product (key) | card MiB | nodes all / schedulable / can hold the pod | E: K_rule, K_run, K_low | A07: K_rule, K_run, K_low | predicted peak at K_run, E / A07 | pod request | run-epochs | deadline s, pod / Job |
| --- | ---: | --- | --- | --- | --- | --- | ---: | --- |
| L40 (`nvidia.com/gpu`) | 46,068 | 17 / 6 / 6 | 9, 9, 4 | 4, 4, 2 | 85.0 % / 73.3 % | 18 CPU, 72 Gi | 399 | 39,000 / 60,600 |
| L40S (`nvidia.com/gpu`) | 46,068 | 4 / 2 / 2 | 9, 9, 4 | 4, 4, 2 | 85.0 % / 73.3 % | 18 CPU, 72 Gi | 399 | 39,000 / 60,600 |
| RTX 4090 (`nvidia.com/gpu`) | 24,564 | 4 / 3 / 3 | 5, 5, 4 | 2, 2, 1 | 88.5 % / 68.8 % | 10 CPU, 40 Gi | 252 | 25,800 / 47,400 |
| RTX 3090 (`nvidia.com/gpu`) | 24,576 | 48 / 30 / 29 | 5, 5, 4 | 2, 2, 1 | 88.5 % / 68.7 % | 10 CPU, 40 Gi | 252 | 25,800 / 47,400 |
| RTX A6000 (`nvidia.com/rtxa6000`) | 49,140 | 8 / 5 / 5 | 10, **9**, 4 | 5, 5, 2 | 79.7 % / 85.9 % | 18 CPU, 72 Gi | 420 | 41,400 / 63,000 |
| A40 (`nvidia.com/a40`) | 46,068 | 3 / 2 / 2 | 9, 9, 4 | 4, 4, 2 | 85.0 % / 73.3 % | 18 CPU, 72 Gi | 399 | 39,000 / 60,600 |
| A100-SXM4-80GB (`nvidia.com/a100`) | 81,920 | 22 / 16 / 16 | 16, 16, 4 | 8, 8, 2 | 85.0 % / 82.5 % | 32 CPU, 128 Gi | 630 | 58,800 / 80,400 |

Caps:
- **The one binding cap is A6000 E, 10 → 9.** The largest schedulable A6000 node has 20 allocatable CPUs, and K=10 at 2 CPU
  per arm would request all 20. The name pool (16) meets the A100's E K_rule exactly and does not cut it. Memory is not
  binding anywhere at the largest K.
- The 3090's "can hold" is 29, not 30: `suncave-11` has 31.2 Gi, less than 40 + 16 Gi.
- **Also not a cap:** on L40 and A6000 nodes (20 CPU) an 18-CPU pod fits only a node where at most 2 CPUs are already
  requested. Free capacity is invisible to us (a cluster-scope pod list is forbidden).

**The K_low rule changed after the orchestrator's ruling.** The brief's first reading, max(1, K_run // 2), gave the same
K_low for the 46 GB cards and the A6000. It differed on the 24 GB cards (E 2) and the A100 (E 8, A07 4)
(`code/evidence/k_low_rules.log`). Under [D2] the run-epochs change: 24 GB Jobs 210 → 252, A100 756 → 630.

## Deadlines and the 6-hour window ([D6])

A Job's `activeDeadlineSeconds` counts from Job creation, so time spent Pending counts against it. With the STUDY's 6-h
Pending allowance, a single Job-level deadline could kill a benchmark that started late.

The fix, on two levels:
- **The pod's `activeDeadlineSeconds`** bounds the run from pod start: 1,800 s + Σ over the phases of (K × 21 × A10 cost
  per run-epoch × 2.5 + 15 s × K + 900 s), rounded up to 600 s. The A10 cost per run-epoch is E 28 s and A07 44 s:
  RUN.md's 138.8 s/epoch at K=5 gives 27.8, and the K=3 pack gives 42.9.
- **The Job's** is the 21,600 s [D6] window plus the pod bound: a backstop only.
- **[D6] itself** (no pod Running 6 h after apply means "not practical") has no Kubernetes field. It is an annotation, and
  cluster-ops enforces it by hand.

At A10-like aggregate speed the raw compute per pod is 3.7 h (46 GB), 3.9 h (A6000), 2.2 h (24 GB) and 5.8 h (A100):
25.2 GPU-hours for all seven (`code/evidence/runtime_arithmetic.log`). Add the header and each phase's start-up. This is
arithmetic from A10 telemetry, not a measurement.

## Arm table (STUDY.md rows → Job → phases → configs)

No A10 Job: the A10 row comes from the pilot logs ("Analysis script"). Every Job has four phases, one pod, no job index,
`stop_after` 21, and run root `/data/chang-n64-20260926/gpu-bench/<slug>/<phase>/runs/<name>`. Phases 3 and 4 reuse the
first K_low names of phases 1 and 2. Each phase cell gives the phase id, the config names, and (in brackets) the bundle
index rows.

| STUDY row | Job / manifest | phase 1 (E) | phase 2 (A07) | phase 3 (E) | phase 4 (A07) |
| --- | --- | --- | --- | --- | --- |
| L40 | `kai-gpubench-l40` / `manifests/kai-gpubench-l40.json` | p1-E-k9: A s1-s8, B s1 [0-8] | p2-A07-k4: C s1-s4 [16-19] | p3-E-k4: A s1-s4 [0-3] | p4-A07-k2: C s1-s2 [16-17] |
| L40S | `kai-gpubench-l40s` | as L40 | as L40 | as L40 | as L40 |
| 4090 | `kai-gpubench-geforce-rtx-4090` | p1-E-k5: A s1-s5 [0-4] | p2-A07-k2: C s1-s2 [16-17] | p3-E-k4: A s1-s4 [0-3] | p4-A07-k1: C s1 [16] |
| 3090 | `kai-gpubench-geforce-rtx-3090` | as 4090 | as 4090 | as 4090 | as 4090 |
| A6000 | `kai-gpubench-rtx-a6000` | p1-E-k9: A s1-s8, B s1 [0-8] | p2-A07-k5: C s1-s5 [16-20] | p3-E-k4: A s1-s4 [0-3] | p4-A07-k2: C s1-s2 [16-17] |
| A40 | `kai-gpubench-a40` | as L40 | as L40 | as L40 | as L40 |
| A100 | `kai-gpubench-a100-sxm4-80gb` | p1-E-k16: A s1-s8, B s1-s8 [0-15] | p2-A07-k8: C s1-s8 [16-23] | p3-E-k4: A s1-s4 [0-3] | p4-A07-k2: C s1-s2 [16-17] |
| A10 (baseline) | none | pilot-b K=5 and K=3 logs | | | |

The A07-350 names are in the pool but no phase reaches them (the largest A07 K is 8). `train.epochs` is unchanged (7,000),
so the last-epoch trace rule never fires inside 21 epochs. The traced one-based epochs are exactly 1, 10 and 20, as
[D1] requires.

## G_p probe ([D4])

`python3 code/gen_bench.py --probe PRODUCT:K:N` writes `manifests/kai-gpuprobe-<slug>-k<K>.json` and touches nothing else.
- **Shape.** N pods of the production shape: 2K CPU, 8K Gi and one GPU of the product.
- **What each pod runs.** Only the pod header (pip install, manifest sha, GPU gate, cache READY) and the unchanged
  fingerprint gate, then `PROBE_DONE`.
- **Job settings.** Indexed, so one failed pod does not stop the others. `backoffLimitPerIndex 0`,
  `maxFailedIndexes N`, `Ignore` on DisruptionTarget. Job deadline 3,600 s, pod deadline 1,800 s.
- **Analysis.** `bench_summary.py probe --job job.json --pods pods.json` gives G_obs (pods Running within 30 min of the
  Job's creation) and Q_p (their median wait).
- **Not generated for production.** The finalists, K and N (the cap) are chosen at decision time. Two examples were
  generated and linted for shape only: `code/evidence/probe-example/`, L40 at K=9 with N=10, and 3090 at K=1 with N=3.

## Manifests: build-time lint (ml-engineer)

`python3 nrp-lab/nrp_doctor.py lint manifests/kai-gpubench-*.json` (`code/evidence/lint_gpubench_build.log`): **0 ERROR**,
exit 1 on warnings. Each manifest notes "single (non-Indexed) Job … fine here" and "[rule PACK] k arms per pod declared".

There is one WARN per manifest except the 3090's, and it is the same WARN each time:
```
WARN   required pool = 1 products / <n> nodes cluster-wide  <-- narrow; expect queueing
```
(n = 22 A100, 3 A40, 4 4090, 17 L40, 4 L40S, 8 A6000). This is acceptable because pinning one product is the point of
the benchmark: the controlled timing comparison that the setup doc's Pool policy allows, logged in `decisions.md`
(2026-09-29), ending when the seven Jobs are deleted. The 3090 (47 nodes counted by lint) gets a note instead.

Lint counts every labelled node with GPUs, tainted or not. The schedulable counts are in the survey table.

The example probes (`code/evidence/lint_probe_example.log`): 0 ERROR; 3 WARN.
- `backoffLimitPerIndex=0` (both): intended, since a probe pod is never retried.
- The narrow pool (L40).

Other properties of the Job shape:
- No W&B key: `WANDB_MODE=disabled`; no secret env; no `BNJ_STAGE`.
- Retries: `backoffLimit: 0` with no `podFailurePolicy`, so a preempted pod fails the Job rather than being re-run.
- The last command is `exec python … bench_driver.py pod`. The driver becomes PID 1 and its SIGTERM handler stops the
  arms within the 180 s grace; bash as PID 1 would ignore SIGTERM.
- Every script passes `bash -n`. Each embedded `BENCH_PLAN` validates against the bundle index, and every named config's
  sha256 equals its index row (`code/evidence/plan_check.log`, which ends `GENERATOR_IDEMPOTENT`).

## Code sha

- Repo HEAD `165793ddb7213034a55fd127816953ab4738ad35`, re-read at handback. **Dirty** (`git status --short`: `?? campaigns/2026-09-29-gpu-benchmark/`,
  ` M .claude/memory/decisions.md`): `campaigns/2026-09-29-gpu-benchmark/` is untracked in
  full. That includes the designer's STUDY.md and plan.md, every file listed under "What was built", and
  `code/evidence/*`. `.claude/memory/decisions.md` also carries this campaign's new entry (the file was already dirty
  from other sessions).
- The frozen inputs are committed and unchanged: `chang0926-code.tar.gz` sha256 `42abed4b…` (asserted by `gen_bench.py`)
  and fingerprint payload sha256 `e9511d1a…` (asserted).
- The driver ConfigMap is built from `code/bench_driver.py` sha256
  `4d2dcd7d9cebf85d1da985122053741a18046e3b48bafdbf1082b06877c40c22`; the pod checks the same sha with `sha256sum -c`.
- The commit must include the campaign directory, or this sha does not describe the shipped harness.
- The anchor cache the benchmark reads: `x_train 420ac79d…`, `x_val 7b56c1b2…`, `y_train a5269398…`, `y_val 63049d9b…`
  (training-batch PREFLIGHT l. 518). Each arm prints the digests it loaded (`BENCH_CACHE`), and the summary reports
  `cache_matches_anchor`.

## Analysis script and the A10 baseline test

`code/bench_summary.py bench --root <dir> --plan manifests/bench_plan.json` reads each product's copied PVC directory. Per
product × class × K:
- **s and R** (STUDY [D1], the headline): s is each arm's (9 × median untraced + median traced)/10 over epochs 2-21, the
  slowest arm of the phase; R = K × 3600 / s, given only if all K arms ran every epoch.
- **Beside them:** the same formula on pooled medians (the brief's form), and total elapsed per run-epoch.
- **Memory:** peak GPU memory (pod and per process) against 0.90 × memory.total.
- **Utilization and CPU:** GPU utilization over all samples and over the steady window (K arms live, all past epoch 1,
  none at the last); cgroup CPU cores against the request.
- **OOM.** An OOM means an arm the driver classified as OOM: exit 7, or a failed exit with an OOM line
  (`phase_result.json`, the sole source in bench mode). OOM-looking log lines in an arm that carried on are only counted,
  as `oom_lines_seen`. TF's allocator can log a failed growth attempt and retry smaller, and such a line must not
  exclude a K.
- **Other telemetry:** host RSS; NaN and verification counts; fingerprint; node; `cache_matches_anchor`.
- **Queue:** Q from apply (Job creation → pod Ready, from `job.json`), plus creation → PodScheduled.
- **Exclusions:** rules 1-2 per phase. Under rule 3, a product listed in `--plan` with no data is reported as "not
  practical, or not run".

Tested on:
- the CPU-gate output (`code/evidence/bench_summary_cpu_gate.log`). There, s is undefined by construction (stop_after 2),
  the injected OOM is flagged under rule 1, the seven real products show as rule 3 rows, and `cache_matches_anchor False`
  on the synthetic cache;
- the saved A10 pilot logs (`code/evidence/a10_baseline_summary.{log,json}`).

The A10 inputs:
- K=5: `*pilotb5-42abed-0-20260929T0305Z.log` with `pilotb5-qqjmt-full-20260929T0305Z.log`.
- K=3: `*pilotb3-42abed-0-20260929T0305Z.log`, using the attempt with `resume_epoch=0`. Its epochs 1-21 ran in pod
  c7tg4, whose log `pilotb3-42abed-c7tg4-full-20260929T0015Z.log` falls outside the 0305Z glob.

The result is a **mixed-pack A10 baseline**: run_study.train, W&B on, several architectures per pod, K=5 at 97.9 % and
K=3 at 92.3 % of card memory, both over the 90 % rule. Telemetry, not a result:

| pack | class (by `params=`) | s [D1] (slowest arm) | s pooled | class share, run-epochs/GPU-h | pack total |
| --- | --- | --- | --- | ---: | ---: |
| K=5, c5805 | E (A s1, A s2, D s1) | 140.4 | 140.5 | 76.9 | 128.5 |
| K=5 | C′ | 228.4 | 228.4 | 15.8 | |
| K=5 | E1 | 100.6 | 100.6 | 35.8 | |
| K=3, gpu-16 | A07 (A07-350 s1, C s1) | 132.5 | 132.2 | 54.3 | 97.9 |
| K=3 | F (E + PE) | 82.9 | 82.9 | 43.4 | |

Consistency check: RUN.md's mean over each arm's last 30 epochs is 138.5-138.9 s (E) and 130.7 s (A07). A pack total is
the sum over arms of 3,600 / each arm's own s; K × 3600 / s is not defined for a mixed pack.

**Falsifier (i) machinery.** `bench_summary.py a10 --offset 50` reads epochs 52-71 (traced 60 and 70), letting later
attempts replace re-run epochs, and flags a window that mixes attempts (`code/evidence/a10_offset50_summary.log`). It
reports `pack_arms_with_window_data` because C′ has no epochs 52-71 in the saved logs. The verdict itself is read at
decision time, on the then-latest window.

## Findings recorded, not fixed (Delta)

1. **An uncommitted edit makes the Delta canary header `WANDB_MODE=disabled`.**
   - Where: `campaigns/2026-09-26-delta/code/manifest_wave2.py:122`, mtime 2026-09-29T03:36:42Z, another session:
     `WANDB_MODE={"disabled" if canary else "online"}`.
   - Why it fails: on the frozen code `run_study.train` calls `run_engram.validate_tracking_destination`, which refuses
     anything but online (42abed4b `run_engram.py:141-142`).
   - Evidence: that refusal is what ended canary-v2 at 20:07Z. All four E-k4 arms failed with `ValueError: --track
     requires explicit WANDB_MODE=online for the private study` (Delta `campaigns/2026-09-27-delta-screen/RUN.md` l.
     353-362).
   - A canary generated from this edit will fail the same way. Not edited.
2. **`campaigns/2026-09-26-delta/code/memory_measurements.json` plans A07 at K=3 on 24 GB.**
   - Where: `planning_k.A07."24GB": 3`, l. 36, committed.
   - The uncommitted diff also adds `NVIDIA-GeForce-RTX-4090` to that 24GB class (l. 58).
   - Against it: the Delta A07 canary (2026-09-29 03:22Z, Delta RUN.md l. 501-516) ran out of memory on an A10 with three
     A07 processes. The third hit `RESOURCE_EXHAUSTED: failed to allocate memory`; the two survivors hold 8,446 MiB each,
     16,906 / 23,028 MiB (73.4 %) in all.
   - By the 90 % rule a 24 GB card holds 2 A07 arms (this build's K_rule). Not edited.

## Alignment with STUDY.md (the STUDY governs)

**Aligned in the build:**
- [D2] K_low; [D1] s on the slowest arm and R = K × 3600 / s as the headline.
- The 2-21 window with traced epochs 1, 10, 20; queue from apply.
- [D4] probe generator and analysis; [D6] two-level deadline and annotation.
- Exclusion rules 1-3 in the summary; falsifier (i) windows; cache digests; W&B off; one Job per product; A10 from
  telemetry.

**Still different, listed rather than chosen:**
1. **E names past eight seeds.** STUDY says "the same configs and seeds 1..K per phase". Per the brief, the E class takes
   A s1-s8 and then B s1-s8. So at K=9 the ninth arm is B s1 (seed 1 again, target 250k), and the A100's K=16 phase
   holds seeds 1-8 twice. The compute is identical; only the seed labels repeat.
2. **Node reserve.** [D2] says "capped so K × (2 CPU, 8 GiB) fits p's nodes". This build reserves 2 CPU and 16 Gi per node
   for daemons, which caps A6000 E at 9 (STUDY's table shows K_rule 10). Without the reserve, K=10 requests all 20
   allocatable CPUs of the A6000 nodes. Changing it means editing the constants `NODE_RESERVE_CPU` / `NODE_RESERVE_MEM_GI` in
   `gen_bench.py` and regenerating.
3. **m_E.** 4,350 (brief, RUN.md Takeover check) against 4,354 (STUDY, RUN.md l. 216): no K differs.
4. **Card memory for the 4090, 3090 and A100.** STUDY reads it in the pod; the build reads the node label, and the pod
   records nvidia-smi's `GPU_INFO`. A disagreement would be a finding.
5. **Utilization window.** "Epochs 2-21" is approximated by 60 s samples in which all K arms are live, past epoch 1 and
   short of the last. A peak between samples can be missed, so rule 1's 90 % test sees the 60 s maxima only.
6. **Probe duration.** [D4] expects a "two-minute fingerprint check". Each probe pod also runs pip install and the header,
   about 5-8 min, and G_obs counts pods Running, not finished.
7. **[D6] enforcement.** It is manual (cluster-ops, at 6 h); no Kubernetes field expresses it.
8. **Not built:**
   - T(p) and the longest-first pack scheduling (the REPORT's analysis; the summary supplies s, K, R and Q);
   - the STUDY's "Full" variant (two Jobs per product on distinct nodes, plus an A10 harness Job);
   - the certification canary of rule 4.
9. **Budget.** STUDY's "3-4 h per Job, about 21-28 GPU-hours" sits against 25.2 GPU-hours raw here. The A100 Job is
   5.8 h raw, and the 46 GB Jobs are 3.7 h plus start-up.

## Where I am not sure

```
DECISION: node reserve 2 CPU / 16 Gi, so A6000 E runs K=9.   ALTERNATIVES: K=10 at 20 CPU on 20-CPU nodes (cannot
schedule past DaemonSet requests); 1.8 CPU per arm (changes the per-arm CPU the STUDY fixes).   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: E names A s1-s8 then B s1-s8 (brief), so seeds repeat past K=8.   ALTERNATIVES: none within the index (8 seeds
per arm).   CONFIDENCE: HIGH   FLAG FOR HUMAN: YES (STUDY wording "seeds 1..K")
DECISION: a CHECKPOINT_VERIFICATION FAIL is recorded (exit 6) and the phase continues.   ALTERNATIVES: fail the pod.
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES (first GPU exercise of the 1e-7 replay)
DECISION: stall watchdog 3,600 s per arm (run_pack uses 1,800 s).   ALTERNATIVES: 1,800 s (may kill a healthy arm during
epoch 1 at K=16).   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
DECISION: pod deadline margin x2.5 on A10 cost per run-epoch.   ALTERNATIVES: x2, x3.   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
```

## Open items for cluster-ops

1. Create the driver ConfigMap from `manifests/configmap-bench-driver-4d2dcd7d.json` (immutable) and confirm the two
   existing ConfigMaps are unchanged. No Job here requests an A10; the pilots keep theirs.
   - Before the real apply, run `kubectl create --dry-run=server -f` on every `kai-gpubench-*.json` and on any generated
     probe. Two structures here have never been sent to an API server: the pod-level `activeDeadlineSeconds`, and the
     probe's Indexed `backoffLimitPerIndex: 0` with `maxFailedIndexes: N`. A server-side dry run creates nothing.
2. Re-check at launch, and regenerate if anything moved: re-run `code/node_survey.py` and `code/gen_bench.py`, then lint.
   - A100 quota was 23/24 at 05:55Z. A full quota makes the Job controller's pod creation fail admission; the Job waits,
     and no retry is spent.
   - Taints, and the schedulable counts: L40 6, L40S 2, 4090 3, 3090 30, A6000 5, A40 2, A100 16.
3. The 18-CPU pods (L40, L40S, A6000, A40) are the likeliest to queue. L40 and A6000 nodes have 20 CPUs, so the pod
   needs a nearly CPU-idle node.
4. [D6]: a Job with no Running pod 6 h after apply is deleted, and its PodScheduled message is kept. The STUDY notes that
   Jobs applied by about 08:00Z on 09-29 end before the regime-B epoch-500 readout.
5. At the end of each Job, before the 7-day TTL:
   - `kubectl get pod <pod> -o json > logs/<slug>/pod.json` and `kubectl get job kai-gpubench-<slug> -o json >
     logs/<slug>/job.json` (Q from apply needs both).
   - Copy `/data/chang-n64-20260926/gpu-bench/<slug>/` (plan.json, samples.csv, bench_result.json, pod-*.log,
     p*/phase_result.json, p*/logs/) into `logs/<slug>/`.
   - Then run `python3 code/bench_summary.py bench --root logs --plan manifests/bench_plan.json`.
6. A manual re-run of a product needs its `gpu-bench/<slug>` directory moved aside, never deleted. Otherwise the pod exits
   11 (`BENCH_ROOT_NOT_EMPTY`) before any work.
7. PVC footprint: an arm directory was 5.4 MB (E) and 8.9 MB (A07) at 2 epochs on 1,240 validation rows. At 21 epochs
   and 62,000 rows, expect about 10 MB per arm; 131 arm-runs in all (`bench_plan.json`), so about 1-2 GB.
8. For [D4] at decision time: `python3 code/gen_bench.py --probe <PRODUCT>:<K>:<cap>`, lint, apply. At 30 min, save
   `kubectl get pods -l app=kai-gpuprobe-<slug>-k<K> -o json` and the Job JSON, then run `bench_summary.py probe`.

## nrp_doctor.py lint at launch — cluster-ops

<!-- PLACEHOLDER (cluster-ops): paste `python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-*.json`
run at launch time and answer every WARN. The build-time run above is the ml-engineer's check, not this section. -->

## ConfigMaps — cluster-ops

<!-- PLACEHOLDER (cluster-ops): the name of the driver ConfigMap as created from manifests/configmap-bench-driver-4d2dcd7d.json
(expected kai-gpubench-driver-4d2dcd7d9c, annotation bnjettag.io/bench-driver-sha256 4d2dcd7d…), and the verification that
kai-chang0926-code-42abed4b5d and kai-chang0926-fp-e9511d1aeb exist unchanged. -->
