# PREFLIGHT — 2026-09-29-gpu-benchmark, build half (ml-engineer; rebuilt by the fixer after critical review v1)

Date: 2026-09-29. Status: **rebuilt for STUDY Amendment 1 (fixer v1, 2026-09-29), nothing applied**; critical v2 PASS, its B and C items addressed by fixer v2 (change log below). Launches since 09:30:27Z are in `RUN.md`. Telemetry tooling only; nothing here is a result.

- **Governing design.** STUDY.md [D1]-[D6] with Amendment 1 (2026-09-29: the orchestrator's routes for review v1 A1, A2 and B1-B6). K_low follows [D2]. The remaining STUDY-against-build mismatches are listed in "Alignment with STUDY.md".
- **Code sha.** Repo HEAD `165793d`; the working tree is dirty (the whole campaign directory is untracked; see "Code sha").
- **Bundle.** 42abed4b, unchanged.
- **ConfigMaps.** `kai-chang0926-code-42abed4b5d` and `kai-chang0926-fp-e9511d1aeb` exist and are unchanged. The driver payload is `kai-gpubench-driver-5ede0778f7` (driver sha256 `5ede0778…`), created by the fixer at 08:38:07Z and verified on the live object ("Fixer v1 rebuild", at the end). The v1 ConfigMap `kai-gpubench-driver-4d2dcd7d9c` is orphaned: no Job mounts it.
- **Generator.** `python3 code/gen_bench.py`: 16 Jobs, two per product for eight products (the seven candidates and the A10). It reads the newest `code/evidence/node_survey_*.json` and defaults to `--k-low-rule study-d2`. It is fed by `code/node_survey.py`.
- **Notebook.** `plan.md` § Phase 2, § Fixer v1 and § Fixer v2.

## Change log (fixer v2, 2026-09-29 ~09:45-10:05Z; `review/PREFLIGHT_critical_v2.md`, PASS with B1-B6)

Made after the first K_low applies (09:30-09:36Z, `RUN.md`), before either A10 Job is applied and before any summary runs on benchmark
data. The driver (`5ede0778…`), its ConfigMap and the 14 non-A10 manifests are byte-identical; B2 (the staged apply) is the orchestrator's.

| finding | change | evidence |
| --- | --- | --- |
| B1 | Rule 5's thread-mask check reads only sampler rows with `proc_epochs_done` ≥ 1, so a row taken between `Popen` and the arm's own pin (the whole allowed set) no longer excludes a phase. | `test_rule5_thread_mask_skips_pre_pin_rows` (a pre-pin row passes; a post-pin escape still excludes) |
| B3 | STUDY Am. 1, "Critical v2 B3": at most one A10 re-run, into a fresh directory; the first complete attempt counts, others are listed, never pooled; `verify_interrupted` is not a FAIL; "A10 baseline not measured". The summary implements it (`a10_rules`, `verify_interrupted_arms`), beyond the STUDY line the review asked for. | `test_a10_attempts_and_baseline_check`, `test_phase_without_phase_result` |
| B4 | Open item 5: a live watcher is a precondition of applying either A10 Job; the apply order carries it. | "Open items" 3 and 5; "Fixer v1 rebuild" apply order |
| B5 | The 3-h premise is withdrawn; NRP's 40 % floor is an accepted risk, stated per Job shape without an invented utilization. | "Deadlines" |
| B6 | STUDY Am. 1, "Critical v2 B6": the counted A10 s at E K=4 / A07 K=2 more than 10 % above Delta's slowest pure-pack canary arm (114.455 s / 90.73 s) is flagged and goes to Kai. | `test_a10_attempts_and_baseline_check` |
| C1 | A phase without `phase_result.json` runs the pin checks from the arm logs (every arm `ARM_CPUS … OK` on one list of 2K CPUs), else it keeps no R. | `test_phase_without_phase_result` |
| C2, C3, C6, C7 | STUDY: memory is capped per pod only (up to 32 GiB per arm); the "2.13 h" label; two [L1] lines. | STUDY l. 43-45, [L1], Am. 1 B5 |
| C4 | The anti-affinity and the pinning-check route are decided (`decisions.md` 2026-09-29, orchestrator); the stale flags are withdrawn. | "Alignment" 10, "Where I am not sure" |
| C5 | The two A10 Jobs, only they, also exclude the pilot-b nodes `gpu-17.nrp.mghpcc.org` and `hcc-nrp-shor-c5805.unl.edu` (28 of 30 A10 nodes remain). Regenerated from the 07:39:45Z survey: 16 of 18 files byte-identical, the A10 pair changed only in those two `NotIn` values and one annotation; lint OK, server dry-run accepted. | `code/evidence/lint_dryrun_a10_fixer_v2.log`, `gen_bench.log`, `plan_check.log` (new check `pilot_nodes`) |

Evidence rewritten in place (the fixer-v1 copies are in git at `8a61db2`): `test_bench.log` (`ALL_PASS 24 SKIPPED 1`), `gen_bench.log`,
`plan_check.log`, `bench_summary_cpu_gate.log` (the fixer-v1 table reproduced byte for byte, plus the A10 status row).

## Change log (fixer v1, 2026-09-29; `review/PREFLIGHT_critical_v1.md`)

| finding | change | evidence |
| --- | --- | --- |
| A1 | The A10 is the eighth product, in the same benchmark: `kai-gpubench-a10-krule` (E 4, A07 2) and `kai-gpubench-a10-klow` (E 3, A07 1), both carrying the yield-to-anchor rule. The pilot telemetry is a labelled cross-check. STUDY Amendment 1. | `code/evidence/gen_bench.log`, `plan_check.log`; `test_a10_baseline_jobs` |
| A2, B6 | Two Jobs per product, K_rule and K_low; each pod requests 2 CPU and 8 Gi × its own largest K. Each phase's arms are pinned to exactly 2K CPUs, the first 2K of the allowed set: the arm pins itself before any import, checks the mask the kernel reports, prints `ARM_CPUS` and exits 14 on a mismatch. Steady cgroup cores ÷ K per phase in `PHASE_DONE` and in the summary; rule 5. [D6] per Job shape. The fixer added a required pod anti-affinity among the pinned benchmark pods (accepted by the orchestrator, `decisions.md` 2026-09-29). | `cpu_gate_pod.log`, `cpu_gate_negative.log` 3g, `test_bench.log` |
| B1 | Q falls back to `containerStatuses[].state.*.startedAt`; tested on a real finished pod. | `test_pod_facts_completed_pod` |
| B2 | Completion is checked against `stop_after`; exit codes decide outcomes (OOM = exit 7 only); non-ok arms are listed per phase; a host OOM kill is named. | `test_classify_exit_codes_win`, `test_pool_completion_against_stop_after` |
| B3 | Rule 6: a verification FAIL on any arm excludes the product, across both Job directories; the FAIL text (the replay deltas) is kept. | `test_summary_rules_2_5_6_across_both_job_dirs` |
| B4 | The pod header logs `CPU_MODEL`, `CPU_COUNTS`, `LSCPU` and `HOST_MEM`; the driver logs `POD_CPUS` and the pinned physical cores. One node per Job shape is STUDY [L1]. | `test_deadline_formula`, `test_generated_script_is_valid_bash` |
| B5 | Per-Job runtime between the two A10 bounds, in `bench_plan.json` and the `expected-runtime` annotation. A phase under 40 % mean utilization is a finding, never an exclusion. | `code/evidence/runtime_arithmetic.log` |
| C3, C6 | Pod logs are read in time order; any mismatch sets `fingerprint_ok` False; a product-level flag says whether a mismatch value repeats. | `test_summary_rules_2_5_6_across_both_job_dirs` |
| also | The CPU gate's copy loop no longer takes `plan.json` for a phase directory. `code/plan_check.py` makes the v1 plan check reproducible. | `cpu_gate_bench.sh`, `plan_check.log` |

v1 evidence and manifests were moved, not deleted: `code/evidence/v1/`, `manifests/superseded-v1/`.

## What was built

| file | sha256 | role |
| --- | --- | --- |
| `code/bench_driver.py` | `5ede0778…` | the benchmark driver, shipped in its own ConfigMap. `arm` pins itself to `--cpus`, then runs one config; `pod` runs one Job's phases, pins each phase to 2K CPUs and runs the 60 s sampler |
| `code/gen_bench.py` | `a8635a98…` (fixer v2; was `23de1784…`) | writes the 16 Jobs, the driver ConfigMap and `manifests/bench_plan.json`. `--probe PRODUCT:K:N` writes the [D4] probe. Deterministic (`GENERATOR_IDEMPOTENT`) |
| `code/node_survey.py` | `7e34b02c…` | live node list → `code/evidence/node_survey_<UTC>.json`; this build reads `node_survey_20260929T073945Z.json` (07:39:45Z) |
| `code/bench_summary.py` | `cd5f5b64…` (fixer v2; was `f43b4d7d…`) | analysis. `bench`: the benchmark, per Job directory, rules 1-3, 5 and 6, and the A10 rules of STUDY Am. 1, critical v2 B3 and B6; `a10`: the pilot cross-check, with offset windows for falsifier (i); `probe`: G_obs and Q_p |
| `code/plan_check.py` | `bf539e94…` (fixer v2; was `741a6190…`) | static checks on the 16 manifests and the generator's idempotence |
| `code/make_synthetic_cache.py` (`da914d7d…`), `code/cpu_gate_bench.sh` (`5479036e…`), `code/test_bench.py` (`8ae77069…`, fixer v2; was `ad9c657c…`) | | CPU gate and unit tests |
| `manifests/kai-gpubench-<slug>-{krule,klow}.json` ×16, `configmap-bench-driver-5ede0778.json`, `bench_plan.json` | | generated, never hand-edited |

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
  production's are measured the same way. One difference is that W&B's background process competes for CPU in
  production and not here: a small bias, in one direction (the benchmark is slightly faster). Since STUDY Amendment 1 a
  second departure is named: production arms float under the pod's CFS quota over the node's CPUs (`run_pack.py` sets no
  affinity), while the benchmark pins each phase's arms to exactly 2K CPUs, with the pod quota still applying. The
  direction of that bias is not established: SMT siblings and no migration to idle CPUs could make the benchmark slower.
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

Before any of this, the arm pins itself to the `--cpus` list the pod passes (STUDY Amendment 1), checks the mask the kernel
reports and prints `ARM_CPUS`; nothing else in the arm path changed.

On a GPU, `CHECKPOINT_VERIFICATION_PASS` so far appears in this repository only on the Delta bundle: both surviving arms of
the Delta A07 canary (A10, c5813; `campaigns/2026-09-27-delta-screen/logs/canary-a07-rep-c-s{1,2}-20260929T0608Z.log`). No
42abed4b log shows it from a GPU yet. Here it runs on every product; a FAIL is recorded (exit 6), the phase continues, and
STUDY rule 6 (Amendment 1) excludes the product.

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

## CPU build/reload gates (`code/cpu_gate_bench.sh`, on driver `5ede0778…`)

Setup: pinned CPU environment (tensorflow 2.21.0, keras 3.15.0, hgq2 0.1.9, quantizers 1.2.2, numpy 2.5.0, scikit-learn
1.9.0, h5py 3.14.0, hls4ml 1.3.0, wandb 0.28.0) via `uv run --with`, on a fresh 42abed4b extraction. The pod environment is
copied: threads, TF32 off, `BNJ_RSS_GATE_LIMIT_MB=8192`, `WANDB_MODE=disabled`. The machine is Darwin arm64, which has no
`os.sched_setaffinity`: the arms cannot pin here, and each gate log says so in its header.

`run_engram.load_cache` needs the full 620,000-row split (l. 216-219), so a tiny cache cannot pass it. The gate therefore
builds a **full-size synthetic cache** (random, seed 0, 466 MB, `make_synthetic_cache.py`; the same array digests as the v1
gate), loads it through the real loader with every hash check, and slices it afterwards to 11,160 / 1,240 rows. The slicing
is the only test-only step, behind `--test-rows`.

**1. One arm, A s1, `--stop-after 2`** (`code/evidence/cpu_gate_arm_a-s1.log`):
```
ARM_MANIFEST_SHA 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42 expected 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42 OK
[epoch 1/7000] EBOPs=9605779 target=350000 above_floor=9434253 feasible=0 degenerate=0 beta=1e-07 val_AUC=0.508496 val_accuracy=0.210484 seconds=13.3 checkpoint=- ebops_trace_seconds=3.79 ebops_trace_over_epoch=0.286 loss=2.581331 ...
[epoch 2/7000] EBOPs=untraced in_training_ebops=9681043 target=350000 beta=1e-07 val_AUC=0.484001 val_accuracy=0.197581 seconds=7.9 checkpoint=epoch-0002 ...
CHECKPOINT_VERIFICATION_PASS {"index": 0, "name": "chang0926-a-n64-s1", ...}
WANDB_IMPORTED False
ARM_DONE chang0926-a-n64-s1 exit 0 wall_seconds 33.9 utc 2026-09-29T08:32:44Z
```
The EBOPs, AUC, accuracy and loss equal the v1 gate's (`code/evidence/v1/cpu_gate_arm_a-s1.log`): on CPU the arm path is
deterministic, and the driver change did not touch it. There are 0 `wandb` files under the run root.

**2. Pod mode: three phases, an injected OOM, and the pin plumbing** (`code/evidence/cpu_gate_pod.log`; arm logs, phase
results, samples, plan and summary in `code/evidence/cpu_gate_pod/`). The allowed set is injected as 0-9
(`--test-allowed-cpus`, refused in a pod):
```
POD_CPUS allowed_n 10 allowed 0-9 pod_cpu_request na ...
PHASE_CPUS p1-E-k2 pin pinned pinned 0-3 n 4 physical_cores None allowed_n 10 allowed 0-9
ARM_STARTED p1-E-k2 chang0926-a-n64-s1 pid 12140 cpus 0-3 2026-09-29T08:32:44Z
ARM_STARTED p1-E-k2 chang0926-a-n64-s2 pid 12152 cpus 0-3 2026-09-29T08:32:46Z
PHASE_DONE p1-E-k2 wall_seconds 57.1 outcomes {"ok": 2} steady_cores na per_arm na pairs 0 pinned 0-3 2026-09-29T08:33:41Z
ARM_EXIT p2-A07-k2 chang0926-c-n64-s2 7 outcome oom epochs 0 verification none 2026-09-29T08:33:48Z
ARM_OOM_RECORDED p2-A07-k2 chang0926-c-n64-s2 (no retry; the phase continues)
PHASE_DONE p2-A07-k2 wall_seconds 72.2 outcomes {"ok": 1, "oom": 1} steady_cores na per_arm na pairs 0 pinned 0-3 2026-09-29T08:34:54Z
PHASE_CPUS p3-E-k1 pin pinned pinned 0-1 n 2 physical_cores None allowed_n 10 allowed 0-9
PHASE_DONE p3-E-k1 wall_seconds 40.1 outcomes {"ok": 1} steady_cores na per_arm na pairs 0 pinned 0-1 2026-09-29T08:35:34Z
BENCH_DONE cpu-gate phases 3 samples 18 2026-09-29T08:35:34Z
```
Each arm log opens with `ARM_CPUS unavailable requested 0-3 (no sched_setaffinity on this platform; allowed under
--test-cpu only)` (`0-1` in phase 3). `steady_cores na`: macOS has no cgroup, and a 2-epoch phase has no steady window.

**3. Negative paths** (`code/evidence/cpu_gate_negative.log`). Each exits before any work and creates no directory:

| case | result |
| --- | --- |
| used bench root | `BENCH_ROOT_NOT_EMPTY`, exit 11 |
| used arm directory | `ARM_ROOT_NOT_EMPTY`, exit 11 |
| names not the first K of the class | `BENCH_PLAN_ERROR`, exit 2 |
| test flags with `KUBERNETES_SERVICE_HOST` set | `BENCH_TEST_FLAGS_REFUSED`, exit 2 |
| no `--test-cpu` on a GPU-less machine | `AssertionError: Training requires GPU`, exit 1 |
| `--cpus 0-3` without `--test-cpu`, where the arm cannot pin | `ARM_CPUS unavailable`, exit 14, before any import |

**4. Unit tests** (`python3 code/test_bench.py`, stdlib only; `code/evidence/test_bench.log`): `ALL_PASS 21 SKIPPED 1`.
- Kept from v1, updated to the two-Job shape: the steady formula, R, CPU cores from `usage_usec`, K_rule and the caps, both
  K_low rules, the plan validation, the probe's shape and summary, the offset windows, the benign OOM line, and the sampler
  row with a fake `nvidia-smi` and cgroup.
- New:
  - `test_a10_baseline_jobs` (A1): E 4 / 3 and A07 2 / 1 come from the [D2] rule; both A10 Jobs carry the yield rule and the
    four exclusions;
  - `test_deadline_formula` (A2, B4, B5): per-Job deadlines (L40: pod 26,400 and 14,400 s), both runtime bounds, the
    header's CPU lines, Guaranteed QoS, the anti-affinity, and no "unused CPU" claim in the annotation;
  - `test_generated_script_is_valid_bash`: `bash -n`, and the header's CPU lines run under `set -euo pipefail`;
  - `test_classify_exit_codes_win` (B2): exit 6 with an OOM line is `verify_fail`, exit 1 with one is `crash`, and a SIGKILL
    while `oom_kill` rose is `host_oom_kill`;
  - `test_pool_completion_against_stop_after` (B2): every arm stopped at epoch 15 gives no R;
  - `test_pod_facts_completed_pod` (B1): the lab's own finished pod (`campaigns/2026-09-20-status/cluster.json`, Ready False,
    PodCompleted) gives Q through `startedAt` (85 s from a synthetic Job creation);
  - `test_summary_rules_2_5_6_across_both_job_dirs` (A2, B3, C3, C6): rule 5 at 2.5 cores per arm, rules 2 and 6 on every
    row of the product across its K_rule and K_low directories, a repeating mismatch value, time-ordered pod logs, an
    unconfirmed pin, and a low-utilization finding that excludes nothing;
  - `test_cpu_list_and_phase_selection` and `test_pod_mode_gives_each_arm_2k_cpus` (A2 plumbing, every platform): the arms
    of a K=2 phase are launched with exactly the first 4 CPUs of the allowed set, the K=1 arm with the first 2; on Linux
    the injected set is the process's own, so the arms' real pinning succeeds in any cpuset;
  - `test_arm_refuses_unpinnable_outside_the_cpu_gate`: exit 14, and test flags refused in a pod;
  - `test_pinning_k2_phase_arms_see_4_cpus` (A2, the kernel's view): **skipped on darwin** (no `sched_setaffinity`). It runs
    unmodified on Linux: every arm of a K=2 phase must print `ARM_CPUS n=4 requested X seen X OK`.

## Node survey and K per product

Source: `code/evidence/node_survey_20260929T073945Z.json`, from the live node list at 07:39:45Z (cluster-ops' re-run; a list
call). Its schedulable counts equal the 06:55:31Z build read on all seven candidates; generating from it changes only the
survey annotation (review v1, C5).
- **Schedulable**: Ready, not cordoned, no NoSchedule/NoExecute taint, and not excluded.
- **Excluded hostnames** (in every Job, the A10's included): `hcc-nrp-shor-c6017.unl.edu`, `k8s-chase-ci-07.calit2.optiputer.net`,
  `nautilus-ext-gpu01.fullerton.edu` (nrp_doctor `KNOWN_BAD_NODES`) and `ren-gp-argo-01.madren.org`. The two A10 Jobs, and only
  they, also exclude the Chang pilot-b nodes `gpu-17.nrp.mghpcc.org` and `hcc-nrp-shor-c5805.unl.edu` (fixer v2, critical v2 C5;
  both pilots confirmed there read-only at 09:47Z), so 28 of the 30 schedulable A10 nodes remain; the tables below count by allocatable, before it.
- **Resource keys**: each product's key was read from the nodes' nonzero allocatable. The A10 uses `nvidia.com/gpu`.
- **Card MiB**: from the `nvidia.com/gpu.memory` label. For the A10 the label (23,028) equals the in-pod `nvidia-smi` figure.
- **Quota** (the fixer's read, 08:41Z): `requests.nvidia.com/a100` 23 / 24; pods 115 / 200. There is no quota on `nvidia.com/gpu`,
  `rtxa6000` or `a40`.

Rules (`gen_bench.py`):
- **K_rule** = floor(0.90 × card MiB / per-process MiB). The per-process figures are A10 peaks under TF allow_growth: E 4,350
  and A07 8,446 MiB (training-batch RUN.md, "Takeover check"). STUDY [D2] cites 4,354 for E; no K changes on any card.
- **K_run** = min(K_rule, node cap, 16 names). The node cap is the largest K that some schedulable node holds at 2 CPU and
  8 Gi per arm, after reserving 2 CPU and 16 Gi per node for daemons.
- **K_low, per STUDY [D2]**: the class's A10 K (E 4, A07 2), or K_run − 1 where K_run ≤ that. For the A10 itself this gives
  E 3 and A07 1.
- **Pod request**, per Job (STUDY Amendment 1): 2 CPU and 8 Gi × the largest K of that Job's two phases (rule PACK). Inside
  the pod, every phase's arms are pinned to 2K CPUs.

| product (key) | card MiB | nodes all / schedulable | E: K_rule, K_run, K_low | A07: K_rule, K_run, K_low | predicted peak at K_run, E / A07 | run-epochs, both Jobs |
| --- | ---: | --- | --- | --- | --- | ---: |
| L40 (`nvidia.com/gpu`) | 46,068 | 17 / 6 | 9, 9, 4 | 4, 4, 2 | 85.0 % / 73.3 % | 399 |
| L40S (`nvidia.com/gpu`) | 46,068 | 4 / 2 | 9, 9, 4 | 4, 4, 2 | 85.0 % / 73.3 % | 399 |
| RTX 4090 (`nvidia.com/gpu`) | 24,564 | 4 / 3 | 5, 5, 4 | 2, 2, 1 | 88.5 % / 68.8 % | 252 |
| RTX 3090 (`nvidia.com/gpu`) | 24,576 | 49 / 30 | 5, 5, 4 | 2, 2, 1 | 88.5 % / 68.7 % | 252 |
| RTX A6000 (`nvidia.com/rtxa6000`) | 49,140 | 8 / 5 | 10, **9**, 4 | 5, 5, 2 | 79.7 % / 85.9 % | 420 |
| A40 (`nvidia.com/a40`) | 46,068 | 3 / 2 | 9, 9, 4 | 4, 4, 2 | 85.0 % / 73.3 % | 399 |
| A100-SXM4-80GB (`nvidia.com/a100`) | 81,920 | 22 / 16 | 16, 16, 4 | 8, 8, 2 | 85.0 % / 82.5 % | 630 |
| **A10, the baseline** (`nvidia.com/gpu`) | 23,028 | 35 / 30 | 4, 4, 3 | 2, 2, 1 | 75.6 % / 73.4 % | 210 |

The 16 Jobs (`manifests/bench_plan.json`; slack = allocatable CPU − the 2-CPU reserve − the pod's request, over the nodes
that can hold the pod; allocatable is capacity, not free capacity):

| Job | phases | pod request | can hold | CPU slack | deadline s, pod / Job | run-epochs |
| --- | --- | --- | ---: | --- | --- | ---: |
| `kai-gpubench-l40-krule` | p1-E-k9, p2-A07-k4 | 18 CPU, 72 Gi | 6 | 0 | 26,400 / 48,000 | 273 |
| `kai-gpubench-l40-klow` | p3-E-k4, p4-A07-k2 | 8 CPU, 32 Gi | 6 | 10 | 14,400 / 36,000 | 126 |
| `kai-gpubench-l40s-krule` | p1-E-k9, p2-A07-k4 | 18 CPU, 72 Gi | 2 | 8 | 26,400 / 48,000 | 273 |
| `kai-gpubench-l40s-klow` | p3-E-k4, p4-A07-k2 | 8 CPU, 32 Gi | 2 | 18 | 14,400 / 36,000 | 126 |
| `kai-gpubench-geforce-rtx-4090-krule` | p1-E-k5, p2-A07-k2 | 10 CPU, 40 Gi | 3 | 16 | 16,200 / 37,800 | 147 |
| `kai-gpubench-geforce-rtx-4090-klow` | p3-E-k4, p4-A07-k1 | 8 CPU, 32 Gi | 3 | 18 | 12,000 / 33,600 | 105 |
| `kai-gpubench-geforce-rtx-3090-krule` | p1-E-k5, p2-A07-k2 | 10 CPU, 40 Gi | 29 | 0 (12-CPU nodes), 8-48 | 16,200 / 37,800 | 147 |
| `kai-gpubench-geforce-rtx-3090-klow` | p3-E-k4, p4-A07-k1 | 8 CPU, 32 Gi | 29 | 2 (12-CPU nodes), 10-50 | 12,000 / 33,600 | 105 |
| `kai-gpubench-rtx-a6000-krule` | p1-E-k9, p2-A07-k5 | 18 CPU, 72 Gi | 5 | 0 | 28,800 / 50,400 | 294 |
| `kai-gpubench-rtx-a6000-klow` | p3-E-k4, p4-A07-k2 | 8 CPU, 32 Gi | 5 | 10 | 14,400 / 36,000 | 126 |
| `kai-gpubench-a40-krule` | p1-E-k9, p2-A07-k4 | 18 CPU, 72 Gi | 2 | 24, 40 | 26,400 / 48,000 | 273 |
| `kai-gpubench-a40-klow` | p3-E-k4, p4-A07-k2 | 8 CPU, 32 Gi | 2 | 34, 50 | 14,400 / 36,000 | 126 |
| `kai-gpubench-a100-sxm4-80gb-krule` | p1-E-k16, p2-A07-k8 | 32 CPU, 128 Gi | 16 | 90, 218 | 46,200 / 67,800 | 504 |
| `kai-gpubench-a100-sxm4-80gb-klow` | p3-E-k4, p4-A07-k2 | 8 CPU, 32 Gi | 16 | 114, 242 | 14,400 / 36,000 | 126 |
| `kai-gpubench-a10-krule` | p1-E-k4, p2-A07-k2 | 8 CPU, 32 Gi | 30 | 114 | 14,400 / 36,000 | 126 |
| `kai-gpubench-a10-klow` | p3-E-k3, p4-A07-k1 | 6 CPU, 24 Gi | 30 | 116 | 10,800 / 32,400 | 84 |

Caps and shapes:
- **The one binding cap is A6000 E, 10 → 9.** The largest schedulable A6000 node has 20 allocatable CPUs, and K=10 at 2 CPU
  per arm would request all 20. The name pool (16) meets the A100's E K_rule exactly and does not cut it. Memory is not
  binding anywhere at the largest K.
- The 3090's "can hold" is 29, not 30: `suncave-11` has 31.2 Gi, less than 32 + 16 Gi (and 40 + 16 Gi).
- The split changes only the pod shapes. The K_low pods (8 CPU; 6 on the A10) fit a 20-CPU L40 or A6000 node with 10 CPUs of
  slack, where the 18-CPU K_rule pods need an otherwise idle node. [D6] now judges each shape on its own (B6).

## Deadlines, the 6-hour window ([D6]) and the expected runtime (B5)

A Job's `activeDeadlineSeconds` counts from Job creation, so time spent Pending counts against it. Two levels:
- **The pod's `activeDeadlineSeconds`** bounds the run from pod start: 1,800 s + Σ over the Job's two phases of (K × 21 ×
  A10 cost per run-epoch × 2.5 + 15 s × K + 900 s), rounded up to 600 s. The A10 cost per run-epoch is E 28 s and A07 44 s:
  RUN.md's 138.8 s/epoch at K=5 gives 27.8, and the K=3 pack gives 42.9.
- **The Job's** is the 21,600 s [D6] window plus the pod bound: a backstop only.
- **[D6] itself** has no Kubernetes field. It is an annotation, and cluster-ops enforces it by hand, per Job shape since
  Amendment 1: no pod Running 6 h after that Job's apply means "not practical" for that shape; its sibling is judged on its own.

Expected compute per Job (`code/evidence/runtime_arithmetic.log`; arithmetic from A10 telemetry, not a measurement), between
the STUDY's two A10 bounds: the product no faster per GPU than an A10 (K × 21 × E 28 / A07 44 s), and every process at the
A10's upper per-process 140 s whatever K (21 × 140 s per phase, 1.63 h per Job):
- 11 Jobs: at most 1.63 h of compute, 2.13 h with the 1,800 s header allowance (at the throughput bound with the header they take
  1.25 h, the A10 K_low, to 1.83 h, the 24 GB K_rule; fixer v2, critical v2 C3);
- the L40, L40S and A40 K_rule Jobs: 2.50 h, 3.00 h with the header;
- the A6000 K_rule Job: 2.75 h, 3.25 h with the header;
- the A100 K_rule Job: 4.67 h, 5.17 h with the header;
- all 16: 97,692 s = 27.14 GPU-h at the throughput bound, equal to v1's 90,804 s plus the A10's 6,888 s (the split added no
  phase); 32.88 GPU-h at the larger bound per Job; 40.88 GPU-h with the header allowance; 141 arm-runs.

**NRP's 40 % floor, an accepted risk (fixer v2, critical v2 B5).** The brief's premise, that a Job under 3 h mostly escapes
NRP's rolling 3-h 40 % window, is withdrawn. NRP's alert looks back 3 h, so a pod shorter than that is judged over its whole life,
pip-install start-up included; deletion by admins is a recorded violation, and three violations flag the account
(`docs/infrastructure/nrp-nautilus-setup.md:281-283`). Per Job shape:
- **Estimate: none.** A lifetime mean would need each product's phase utilization, measured nowhere yet, and the header's real
  length, known only as its 1,800 s allowance. Any figure would be invented.
- **Exposure, by shape.** The header runs at about 0 % GPU, so it weighs most in the shortest pods. Those are the K_low pods on cards
  faster than the A10, at 1.25-1.67 h with the header even at the A10's throughput bound. The K_rule pods are longer: at that
  bound the A100 and A6000 ones (5.17 h, 3.25 h) run past 3 h and are judged on their last 3 h, and the 46 GB ones reach 3.00 h.
- **Accepted** for these 16 one-off Jobs, recorded at the orchestrator's direction after the first K_low applies (09:30-09:36Z,
  `RUN.md`). An NRP alert or an admin deletion of a benchmark pod goes into `RUN.md` as an incident.
- **A pod NRP flags, most likely a K_low pod, is a finding, not an exclusion.** A phase it cuts short keeps no R (Amendment 1,
  B2). A phase under 40 % mean GPU utilization in the steady window is likewise a finding (`findings` in the summary), never an
  exclusion (Amendment 1, B5).

## Arm table (STUDY.md rows → Jobs → phases → configs)

Every Job has two phases, one pod, no job index, `stop_after` 21, and run root
`/data/chang-n64-20260926/gpu-bench/<slug>-<shape>/<phase>/runs/<name>`. Phase ids are unique per product: p1 and p2 in the
K_rule Job, p3 and p4 in the K_low Job. The K_low phases reuse the first K_low names of the class. Each phase cell gives the
phase id, the config names, and (in brackets) the bundle index rows.

| STUDY row | K_rule Job: phase 1 (E) | phase 2 (A07) | K_low Job: phase 3 (E) | phase 4 (A07) |
| --- | --- | --- | --- | --- |
| L40 | `kai-gpubench-l40-krule`: p1-E-k9: A s1-s8, B s1 [0-8] | p2-A07-k4: C s1-s4 [16-19] | `kai-gpubench-l40-klow`: p3-E-k4: A s1-s4 [0-3] | p4-A07-k2: C s1-s2 [16-17] |
| L40S | `kai-gpubench-l40s-krule`: as L40 | as L40 | `kai-gpubench-l40s-klow`: as L40 | as L40 |
| 4090 | `kai-gpubench-geforce-rtx-4090-krule`: p1-E-k5: A s1-s5 [0-4] | p2-A07-k2: C s1-s2 [16-17] | `kai-gpubench-geforce-rtx-4090-klow`: p3-E-k4: A s1-s4 [0-3] | p4-A07-k1: C s1 [16] |
| 3090 | `kai-gpubench-geforce-rtx-3090-krule`: as 4090 | as 4090 | `kai-gpubench-geforce-rtx-3090-klow`: as 4090 | as 4090 |
| A6000 | `kai-gpubench-rtx-a6000-krule`: p1-E-k9: A s1-s8, B s1 [0-8] | p2-A07-k5: C s1-s5 [16-20] | `kai-gpubench-rtx-a6000-klow`: p3-E-k4: A s1-s4 [0-3] | p4-A07-k2: C s1-s2 [16-17] |
| A40 | `kai-gpubench-a40-krule`: as L40 | as L40 | `kai-gpubench-a40-klow`: as L40 | as L40 |
| A100 | `kai-gpubench-a100-sxm4-80gb-krule`: p1-E-k16: A s1-s8, B s1-s8 [0-15] | p2-A07-k8: C s1-s8 [16-23] | `kai-gpubench-a100-sxm4-80gb-klow`: p3-E-k4: A s1-s4 [0-3] | p4-A07-k2: C s1-s2 [16-17] |
| A10 (baseline) | `kai-gpubench-a10-krule`: p1-E-k4: A s1-s4 [0-3] | p2-A07-k2: C s1-s2 [16-17] | `kai-gpubench-a10-klow`: p3-E-k3: A s1-s3 [0-2] | p4-A07-k1: C s1 [16] |

The A07-350 names are in the pool but no phase reaches them (the largest A07 K is 8). `train.epochs` is unchanged (7,000),
so the last-epoch trace rule never fires inside 21 epochs. The traced one-based epochs are exactly 1, 10 and 20, as [D1]
requires. The pilot-b logs are no longer an arm; they are the labelled cross-check under "Analysis script".

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
  generated and linted for shape only, and regenerated for this build: `code/evidence/probe-example/`, L40 at K=9 with
  N=10, and 3090 at K=1 with N=3. A probe pod carries no pinned-pod label, so the benchmark's anti-affinity never blocks it.

## Manifests: build-time lint

`python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-*.json`
(`code/evidence/lint_gpubench_build.log`, 08:33:13Z): **0 ERROR**, exit 1 on warnings. Every manifest notes "single
(non-Indexed) Job … fine here" and "[rule PACK] k arms per pod declared" (k = the Job's largest K).

12 Jobs carry one WARN each, the same WARN each time:
```
WARN   required pool = 1 products / <n> nodes cluster-wide  <-- narrow; expect queueing
```
(n = 22 A100, 3 A40, 4 4090, 17 L40, 4 L40S, 8 A6000; both Jobs of each). This is acceptable because pinning one product is
the point of the benchmark: the controlled timing comparison that the setup doc's Pool policy allows, logged in
`decisions.md` (2026-09-29), ending when the benchmark Jobs are deleted. The two A10 and the two 3090 Jobs lint `OK` (lint
counts 35 and 48 nodes).

Lint counts every labelled node with GPUs, tainted or not. The schedulable counts are in the survey table.

The example probes, regenerated for this build (their header carries the CPU lines;
`code/evidence/lint_probe_example.log`): 0 ERROR and 3 WARN, as in v1.
- `backoffLimitPerIndex=0` (both): intended, since a probe pod is never retried.
- The narrow pool (L40).

Other properties of the Job shape (`code/evidence/plan_check.log`, from `python3 code/plan_check.py`: 16 × `PLAN_OK`,
`PLAN_CHECK_ALL_OK`, then `GENERATOR_IDEMPOTENT`):
- No W&B key: `WANDB_MODE=disabled`; no secret env; no `BNJ_STAGE`.
- Retries: `backoffLimit: 0` with no `podFailurePolicy`, so a preempted pod fails the Job rather than being re-run.
- Resources: requests equal limits, integer CPUs (Guaranteed QoS), 2 CPU and 8 Gi × the Job's largest K.
- A required pod anti-affinity on the label `bnjettag.io/gpu-bench-pinned` over `kubernetes.io/hostname` (the fixer's
  choice, accepted by the orchestrator in `decisions.md` 2026-09-29).
- The two A10 Jobs, and only they, carry `bnjettag.io/yield-to-anchor` and `bnjettag.io/baseline`, and (fixer v2, critical v2 C5) the two
  Chang pilot-b nodes in their hostname `NotIn`, with `bnjettag.io/pilot-nodes-excluded` (plan_check `pilot_nodes`).
- The last command is `exec python … bench_driver.py pod`. The driver becomes PID 1 and its SIGTERM handler stops the arms
  within the 180 s grace; bash as PID 1 would ignore SIGTERM.
- Every script passes `bash -n`. Each embedded `BENCH_PLAN` validates against the bundle index, and every named config's
  sha256 equals its index row. Each product has two Jobs, with phase ids p1-p4 once each.

## Code sha

- Repo HEAD `165793ddb7213034a55fd127816953ab4738ad35`, re-read by the fixer. **Dirty**: `campaigns/2026-09-29-gpu-benchmark/`
  is untracked in full, including every file listed under "What was built" and `code/evidence/*`.
- The frozen inputs are committed and unchanged: `chang0926-code.tar.gz` sha256 `42abed4b…` (asserted by `gen_bench.py`)
  and the fingerprint payload sha256 `e9511d1a…` (asserted).
- The driver ConfigMap is built from `code/bench_driver.py` sha256
  `5ede0778f716cb9299ca82c64547fb993c93d775572d33463a0fef4cbf676c45`; the pod checks the same sha with `sha256sum -c`.
- The commit must include the campaign directory, or this sha does not describe the shipped driver.
- The anchor cache the benchmark reads: `x_train 420ac79d…`, `x_val 7b56c1b2…`, `y_train a5269398…`, `y_val 63049d9b…`
  (training-batch PREFLIGHT l. 518). Each arm prints the digests it loaded (`BENCH_CACHE`), and the summary reports
  `cache_matches_anchor`.

## Analysis script, the exclusion rules and the A10 cross-check

`code/bench_summary.py bench --root <dir> --plan manifests/bench_plan.json` reads each Job's copied PVC directory
(`<slug>-<shape>/`). Per product × class × K (one phase):
- **s and R** (STUDY [D1], the headline): s is each arm's (9 × median untraced + median traced)/10 over epochs 2-21, the
  slowest arm of the phase; R = K × 3600 / s, given only if all K arms completed `stop_after` (21) epochs (B2). A row
  without R says why (`no_R_reason`).
- **Beside them:** the same formula on pooled medians (the brief's form), and total elapsed per run-epoch.
- **Memory:** peak GPU memory (pod and per process) against 0.90 × memory.total.
- **Utilization and CPU:** GPU utilization over all samples and over the steady window (K arms live, all past epoch 1, none
  at the last); steady cgroup cores and cores ÷ K against 2 per arm; the pinned list, whether every arm confirmed it
  (`ARM_CPUS … OK`), and whether every thread of every arm stayed on it (the sampler's per-thread `Cpus_allowed_list`, read
  only on rows with `proc_epochs_done` ≥ 1: an earlier row can predate the arm's own pin; fixer v2, critical v2 B1).
- **No `phase_result.json` (fixer v2, critical v2 C1):** a deletion or the deadline during the last arm's `verify_selected` leaves none. The
  pin checks then run from the arm logs, and pass only if every arm printed `ARM_CPUS … OK` on one list of 2K CPUs; otherwise the
  phase keeps no R (`no_R_reason` says so) and no pin failure is asserted.
- **Verification cut short (STUDY Am. 1, critical v2 B3):** an arm with all 21 epochs, no `CHECKPOINT_VERIFICATION` line and no `ok` outcome
  is listed in `verify_interrupted_arms`, a finding, never a rule-6 FAIL.
- **The A10 rules (STUDY Am. 1, critical v2 B3 and B6; `a10_rules`):** an A10 Job's attempts are ordered by the `BENCH_POD` stamp. The first
  complete one counts; the rows of any other are labelled "B3: … listed, never pooled; out of T". The counted A10 s at E K=4 and
  A07 K=2 carries `baseline_check` against Delta's slowest canary arm, and more than 10 % above it is a finding that sends the
  headline comparison to Kai. A missing class or check adds one "A10 baseline" row saying "A10 baseline not measured" or
  "check not run".
- **Outcomes (B2):** the driver's classification, exit code first; an OOM is exit 7 only. `non_ok_arms` lists every arm that
  did not end `ok` (crash, stalled, verify_fail, killed, host_oom_kill, cpu_pin_failed) with its exit code and epochs.
  OOM-looking lines in an arm that carried on are only counted (`oom_lines_seen`).
- **Node (B4):** node, CPU model, core counts, `lscpu`, host RAM, and the pod's allowed CPU set.
- **Queue (B1):** Q from apply (Job creation → Running, from `job.json` and `pod.json`; Running = Ready, else the container's
  `startedAt`, since a finished pod carries Ready False), plus creation → PodScheduled.
- **Exclusions:** rule 1 per phase; rules 2 and 6 product-wide across both Job directories; rule 5 per phase; rule 3 for a
  Job listed in `--plan` with no data ("not practical for this pod shape, or not run").
- **Findings (B5):** a phase under 40 % mean GPU utilization in the steady window; a phase whose CPU budget could not be
  verified. Recorded, never an exclusion.
- **Fingerprint (C3, C6):** pod logs read in time order (the `BENCH_POD` stamp); any mismatch sets `fingerprint_ok` False; per
  product, the number of mismatching pods and whether their value repeats (architecture-deterministic) or scatters (a node
  fault).

Tested on:
- the CPU-gate output (`code/evidence/bench_summary_cpu_gate.log`): s is undefined by construction (stop_after 2); the
  injected OOM is flagged under rule 1 and listed as a non-ok arm; every phase is flagged under rule 5 because the arms could
  not pin on macOS; the 16 Jobs show as rule 3 rows; `cache_matches_anchor False` on the synthetic cache;
- synthetic two-directory fixtures (`code/test_bench.py`).

**The A10 cross-check** (STUDY [L2]; since Amendment 1 not the baseline). `bench_summary.py a10` on the saved pilot logs gives
the same figures as v1, field by field (`code/evidence/a10_baseline_summary.{log,json}` and `a10_offset50_summary.{log,json}`
against `code/evidence/v1/`). It is a **mixed-pack** reading: run_study.train, W&B on, several architectures per pod, K=5 at
97.9 % and K=3 at 92.3 % of card memory, both over the 90 % rule. Telemetry, not a result:

| pack | class (by `params=`) | s [D1] (slowest arm) | s pooled | class share, run-epochs/GPU-h | pack total |
| --- | --- | --- | --- | ---: | ---: |
| K=5, c5805 | E (A s1, A s2, D s1) | 140.4 | 140.5 | 76.9 | 128.5 |
| K=5 | C′ | 228.4 | 228.4 | 15.8 | |
| K=5 | E1 | 100.6 | 100.6 | 35.8 | |
| K=3, gpu-16 | A07 (A07-350 s1, C s1) | 132.5 | 132.2 | 54.3 | 97.9 |
| K=3 | F (E + PE) | 82.9 | 82.9 | 43.4 | |

A class share of a mixed pack is never the A10's R: the A10's R comes from its benchmark Jobs. Delta's pure-pack A10
canaries on the same [D1] basis (`code/evidence/a10_delta_canary_crosscheck.{log,json}`; Delta bundle 705a554b, W&B on): E at
K=4, per arm 114.45, 112.43, 111.70 and 111.46 s; A07 at K=2, 90.73 and 90.37 s. The slowest arms, 114.455 s (114.45 at two
decimals) and 90.73 s, anchor the one-sided check of STUDY Am. 1, critical v2 B6 (fixer v2).

The pilot inputs: K=5 `*pilotb5-42abed-0-20260929T0305Z.log` with `pilotb5-qqjmt-full-20260929T0305Z.log`; K=3
`*pilotb3-42abed-0-20260929T0305Z.log`, the attempt with `resume_epoch=0`, whose epochs 1-21 ran in pod c7tg4
(`pilotb3-42abed-c7tg4-full-20260929T0015Z.log`, outside the 0305Z glob).

**Falsifier (i) machinery.** `bench_summary.py a10 --offset 50` reads epochs 52-71 (traced 60 and 70), letting later attempts
replace re-run epochs, and flags a window that mixes attempts (`code/evidence/a10_offset50_summary.log`). It reports
`pack_arms_with_window_data` because C′ has no epochs 52-71 in the saved logs. The verdict itself is read at decision time,
on the then-latest window.

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

## Alignment with STUDY.md (the STUDY governs, with Amendment 1)

**Aligned in the build:**
- [D2] K_low, the A10's included; [D1] s on the slowest arm and R = K × 3600 / s as the headline.
- The 2-21 window with traced epochs 1, 10, 20; queue from apply, with the `startedAt` fallback.
- [D4] probe generator and analysis; [D6] two-level deadline and annotation, per Job shape.
- Exclusion rules 1-3, 5 and 6 in the summary; falsifier (i) windows; cache digests; W&B off.
- Amendment 1: the A10 in the same benchmark, with the yield rule; two Jobs per product; 2K pinned CPUs per phase; the node's
  CPU and RAM in every pod header; per-Job runtime; low utilization as a finding.

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
7. **[D6] enforcement.** It is manual (cluster-ops, 6 h after each Job's apply); no Kubernetes field expresses it.
8. **Not built:** T(p) and the longest-first pack scheduling (the REPORT's analysis; the summary supplies s, K, R and Q), and
   the certification canary of rule 4. The STUDY's v1 "Full" variant is now partly built: the A10 has its benchmark Jobs, and
   each product has two Jobs, but they are two pod shapes, not replicates of one shape.
9. **Budget.** Amendment 1 states it from this build: 27.1 GPU-h at the throughput bound, 32.9 at the larger bound per Job,
   40.9 with the header allowance (`code/evidence/runtime_arithmetic.log`).
10. **Pod anti-affinity** among the pinned benchmark pods: the fixer's implementation choice, since accepted by the
    orchestrator (`decisions.md` 2026-09-29) and recorded in Amendment 1 (fixer v2, critical v2 C4: was "pending the orchestrator").
11. **CPU pinning against production.** Production arms float under a CFS quota over the node's CPUs; benchmark arms are
    pinned to 2K specific CPUs (the orchestrator's decision, Amendment 1). The direction of the bias is not established,
    and it may run opposite to the W&B bias above; the `POD_CPUS` and `pinned_physical_cores` records let the REPORT name it.

## Where I am not sure

```
DECISION: a required pod anti-affinity on bnjettag.io/gpu-bench-pinned (per node) among the benchmark pods; the fixer's
choice, not the orchestrator's. Why: on a node without the kubelet's static CPU manager the allowed set is the node's
shared pool, so a product's K_rule and K_low pods on one node would both pin the same first CPUs. Cost: a product's two
Jobs need two nodes to run at once; on L40S and A40 (2 schedulable nodes each) the second waits while one node is busy.
ALTERNATIVES: none (accept the overlap); preferred anti-affinity (no guarantee); apply each K_low Job only after its K_rule
Job ends. Rollback: remove the podAntiAffinity block in gen_bench.job(), regenerate, plan_check, lint, dry-run; the
driver ConfigMap is unaffected.   CONFIDENCE: MEDIUM-HIGH   FLAG FOR HUMAN: NO (decided: accepted by the orchestrator,
decisions.md 2026-09-29)
DECISION: pin to the first 2K CPUs of the allowed set (orchestrator). On a static-CPU-manager node these are the pod's own
CPUs; on a shared-pool node they are the node's lowest-numbered CPUs, which the node's daemons and other tenants also use,
and 2K CPUs may be K physical cores with their SMT siblings. The POD_CPUS line (allowed_n against pod_cpu_request) and
pinned_physical_cores in each phase record let the REPORT tell the regimes apart.   ALTERNATIVES: none taken.
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO (recorded)
DECISION: the kernel-level pinning test cannot run on this Mac (no sched_setaffinity). Route (a): run `python3
code/test_bench.py` unmodified on an authorized Linux host (under a minute, no GPU). Route (b): the first benchmark pod,
where every arm must print `ARM_CPUS n=<2K> ... OK`; bench_summary flags any arm that does not (rule 5), and an arm whose
mask differs exits 14 before any work. Recommendation: (b), which needs no new grant and checks the real nodes; cluster-ops
confirms it on the first phase of the first pod.   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO (decided: route (b), the
orchestrator, decisions.md 2026-09-29; staged apply per critical v2 B2, RUN.md)
DECISION: node reserve 2 CPU / 16 Gi, so A6000 E runs K=9.   ALTERNATIVES: K=10 at 20 CPU on 20-CPU nodes (cannot
schedule past DaemonSet requests); 1.8 CPU per arm (changes the per-arm CPU the STUDY fixes).   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
DECISION: E names A s1-s8 then B s1-s8 (brief), so seeds repeat past K=8.   ALTERNATIVES: none within the index (8 seeds
per arm).   CONFIDENCE: HIGH   FLAG FOR HUMAN: YES (STUDY wording "seeds 1..K")
DECISION: a CHECKPOINT_VERIFICATION FAIL is recorded (exit 6) and the phase continues; STUDY rule 6 (Amendment 1) then
excludes the product.   ALTERNATIVES: fail the pod.   CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
DECISION: stall watchdog 3,600 s per arm (run_pack uses 1,800 s).   ALTERNATIVES: 1,800 s (may kill a healthy arm during
epoch 1 at K=16).   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
DECISION: pod deadline margin x2.5 on A10 cost per run-epoch.   ALTERNATIVES: x2, x3.   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
DECISION: the runtime's per-process bound uses 140 s per epoch (the upper A10 figure; pilot-b K=5 [D1] 140.4 s).
ALTERNATIVES: 105 s (an all-epoch median, not a [D1] s).   CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```

## Open items for cluster-ops

1. **Driver ConfigMap: done.** `kai-gpubench-driver-5ede0778f7` was created by the fixer (2026-09-29T08:38:07Z); its live
   payload hashes to the driver sha ("Fixer v1 rebuild", below). The two frozen ConfigMaps are unchanged. The v1 ConfigMap
   `kai-gpubench-driver-4d2dcd7d9c` is mounted by no Job; deleting it is optional (the orchestrator's call).
2. **Server dry-runs: done** on all 16 Jobs. Re-check at launch, and regenerate if anything moved: `code/node_survey.py`,
   `code/gen_bench.py`, `code/plan_check.py`, lint, dry-run. The A100 quota was 23/24 at 08:41Z.
3. **Apply order, with three constraints** ("Fixer v1 rebuild", below): the A100 K_low Job only after the A100 K_rule pod
   has terminated; both A10 Jobs last, only with the live watcher running (Open item 5) and while no Chang pilot-b pod is
   Pending; a product's two Jobs need two nodes to run at once (anti-affinity).
4. **[D6] per Job:** a Job with no Running pod 6 h after its own apply is deleted, and its PodScheduled message is kept.
   Its sibling is judged on its own shape.
5. **A10 operating note: carry into RUN.md verbatim at the first A10 apply.**
   > **A10 benchmark Jobs `kai-gpubench-a10-krule` and `kai-gpubench-a10-klow`: Kai's priority rule, pilots first.**
   > **Precondition: a live watcher** (fixer v2, critical v2 B4). Neither A10 Job is applied unless the orchestrator's local
   > watcher is running. It polls every 150 s and appends one heartbeat line per poll to a log. If it stops, both A10 Jobs are
   > deleted. Apply each only while no Chang pilot-b pod is Pending. While either Job has a pod, check at every watcher poll:
   > `kubectl -n cms-ml get pods -l campaign=chang-n64-20260926 --field-selector=status.phase=Pending -o custom-columns=NAME:.metadata.name,APP:.metadata.labels.app`.
   > If any APP starts with `kai-chang0926-pilot-b`, delete the A10 benchmark Job at once
   > (`kubectl -n cms-ml delete job kai-gpubench-a10-krule`, and `kai-gpubench-a10-klow`) and record the time. A deleted or
   > incomplete A10 Job is re-run at most once, into a fresh `gpu-bench/a10-<shape>/` root after the old one is moved aside,
   > never deleted; it never resumes. Which attempt counts, and what the headline says without one: STUDY Amendment 1, critical v2 B3.
6. **Pinning, live check,** on the first phase of the first pod: the pod log's `POD_CPUS` and `PHASE_CPUS` lines, and
   `ARM_CPUS n=<2K> … OK` at the top of every arm log. An arm whose mask differs exits 14 (`cpu_pin_failed`); stop and report
   if any does.
7. **At the end of each Job**, before the 7-day TTL, into `logs/<slug>-<shape>/`:
   - `kubectl -n cms-ml get pod <pod> -o json > logs/<slug>-<shape>/pod.json` and
     `kubectl -n cms-ml get job kai-gpubench-<slug>-<shape> -o json > logs/<slug>-<shape>/job.json` (Q from apply needs both);
   - copy `/data/chang-n64-20260926/gpu-bench/<slug>-<shape>/` (plan.json, samples.csv, bench_result.json, pod-*.log,
     p*/phase_result.json, p*/logs/);
   - then `python3 code/bench_summary.py bench --root logs --plan manifests/bench_plan.json`.
8. A manual re-run of a Job needs its `gpu-bench/<slug>-<shape>` directory moved aside, never deleted. Otherwise the pod
   exits 11 (`BENCH_ROOT_NOT_EMPTY`) before any work.
9. PVC footprint: about 10 MB per arm at 21 epochs (the v1 estimate); 141 arm-runs (`bench_plan.json`), so about 1.4 GB.
10. For [D4] at decision time: `python3 code/gen_bench.py --probe <PRODUCT>:<K>:<cap>`, lint, dry-run, apply. At 30 min,
    save `kubectl get pods -l app=kai-gpuprobe-<slug>-k<K> -o json` and the Job JSON, then run `bench_summary.py probe`.

## nrp_doctor.py lint at launch — cluster-ops

> **Superseded for the v1 build (fixer v1, 2026-09-29).** This lint, the dry run below, the driver ConfigMap under
> "ConfigMaps", "No A10, …", "Blockers" and "Apply order" describe the v1 build (7 Jobs, driver `4d2dcd7d`; now in
> `manifests/superseded-v1/`). The 16 rebuilt Jobs are in "Fixer v1 rebuild" at the end. The node survey re-run and the
> occupancy, PVC, quota and pod-count reads below still stand.

Run between 2026-09-29T07:39Z and 07:48Z (right before the dry-runs below), from repo root:
`python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-*.json`. Verbatim:

```
== campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a100-sxm4-80gb.json :: kai-gpubench-a100-sxm4-80gb ==
  WARN   required pool = 1 products / 22 nodes cluster-wide  <-- narrow; expect queueing
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  note   [rule PACK] 16 arms per pod declared.

== campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a40.json :: kai-gpubench-a40 ==
  WARN   required pool = 1 products / 3 nodes cluster-wide  <-- narrow; expect queueing
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  note   [rule PACK] 9 arms per pod declared.

== campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-geforce-rtx-3090.json :: kai-gpubench-geforce-rtx-3090 ==
  note   required pool = 1 products / 48 nodes cluster-wide
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  note   [rule PACK] 5 arms per pod declared.
  OK

== campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-geforce-rtx-4090.json :: kai-gpubench-geforce-rtx-4090 ==
  WARN   required pool = 1 products / 4 nodes cluster-wide  <-- narrow; expect queueing
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  note   [rule PACK] 5 arms per pod declared.

== campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-l40.json :: kai-gpubench-l40 ==
  WARN   required pool = 1 products / 17 nodes cluster-wide  <-- narrow; expect queueing
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  note   [rule PACK] 9 arms per pod declared.

== campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-l40s.json :: kai-gpubench-l40s ==
  WARN   required pool = 1 products / 4 nodes cluster-wide  <-- narrow; expect queueing
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  note   [rule PACK] 9 arms per pod declared.

== campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-rtx-a6000.json :: kai-gpubench-rtx-a6000 ==
  WARN   required pool = 1 products / 8 nodes cluster-wide  <-- narrow; expect queueing
  note   single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here
  note   [rule PACK] 9 arms per pod declared.

(rules: docs/infrastructure/nrp-nautilus-setup.md -> 'Scheduling, GPU pools and job shape')
```

**0 ERROR, 6 WARN, exit 1** — identical in kind and count to the ml-engineer's build-time run (`lint_gpubench_build.log`); only the live node counts behind each "N nodes cluster-wide" figure could have moved between the two runs, and none did (cross-checked against the fresh survey below: schedulable counts 6/2/3/30/5/2/16 are the same 6/2/3/30/5/2/16 as `node_survey_20260929T065531Z.json`).

**Answering the six WARNs (one answer covers all of them).** Each says the same thing: pinning one GPU product per Job narrows the pool to that product only, so queueing is expected. This is the pre-registered exception in the setup doc's "Pool policy" ("Narrowing the required list is allowed only for a controlled timing comparison, where mixing GPU models would confound the measurement"), taken deliberately for this benchmark and logged at `.claude/memory/decisions.md` 2026-09-29 (`## 2026-09-29 (ml-engineer, staged, NOT applied) — GPU-product benchmark …`, confirmed present at l. 11 by `grep` this session). It ends when the seven benchmark Jobs are deleted; nothing here becomes a standing pool exception. The 3090 manifest gets a `note`, not a `WARN`, because lint's own threshold is 30 schedulable-counted nodes and the 3090's raw count (48, `nrp_doctor`'s own `gpu_resource_map()` count) clears it — see "Node survey re-run" below for why the *fresh* raw count differs by one node and why that does not change the note/WARN split.

**Server-side dry run**, one Job at a time (the hook that gates `kubectl create -f` cannot resolve a shell loop variable in `-f $var`; see "Tooling note" below — each command below used the literal path). All seven, verbatim, no ERROR, no rejection, nothing created:

```
$ kubectl create --dry-run=server -f manifests/kai-gpubench-l40.json
job.batch/kai-gpubench-l40 created (server dry run)
$ kubectl create --dry-run=server -f manifests/kai-gpubench-l40s.json
job.batch/kai-gpubench-l40s created (server dry run)
$ kubectl create --dry-run=server -f manifests/kai-gpubench-geforce-rtx-4090.json
job.batch/kai-gpubench-geforce-rtx-4090 created (server dry run)
$ kubectl create --dry-run=server -f manifests/kai-gpubench-geforce-rtx-3090.json
job.batch/kai-gpubench-geforce-rtx-3090 created (server dry run)
$ kubectl create --dry-run=server -f manifests/kai-gpubench-rtx-a6000.json
job.batch/kai-gpubench-rtx-a6000 created (server dry run)
$ kubectl create --dry-run=server -f manifests/kai-gpubench-a40.json
job.batch/kai-gpubench-a40 created (server dry run)
$ kubectl create --dry-run=server -f manifests/kai-gpubench-a100-sxm4-80gb.json
job.batch/kai-gpubench-a100-sxm4-80gb created (server dry run)
```

This closes the first half of Open item 1: the API server accepts the pod-level `activeDeadlineSeconds` on all seven (the structure ml-engineer flagged as never having been sent to a real server). The other flagged structure — the probe's Indexed `backoffLimitPerIndex: 0` / `maxFailedIndexes: N` — was **not** exercised here: no probe manifest has been generated yet ("not generated for production" per the build half; the two lint-only examples in `code/evidence/probe-example/` are shape checks, not this campaign's [D4] probe). Whoever generates the real probe at decision time should dry-run it the same way before applying.

## ConfigMaps — cluster-ops

> The driver ConfigMap below is v1 (`4d2dcd7d`), now mounted by no Job; the rebuilt driver's is `kai-gpubench-driver-5ede0778f7`
> ("Fixer v1 rebuild"). The checks of the two frozen ConfigMaps still stand, and were repeated at 08:38Z.

**Created**, 2026-09-29T07:35:38Z (server `creationTimestamp`), `kubectl create -f manifests/configmap-bench-driver-4d2dcd7d.json` (create, not apply): `configmap/kai-gpubench-driver-4d2dcd7d9c created`. It did not exist before this call (`get` returned `NotFound` immediately beforehand).

Verified on the live object (`kubectl get configmap kai-gpubench-driver-4d2dcd7d9c -o json`), not just the local manifest:
- name `kai-gpubench-driver-4d2dcd7d9c`; labels `{campaign: gpu-bench-20260929, user: kai}`; `immutable: true`.
- annotation `bnjettag.io/bench-driver-sha256` = `4d2dcd7d9cebf85d1da985122053741a18046e3b48bafdbf1082b06877c40c22`.
- the live `data['bench_driver.py']` payload, decoded and hashed in-session, sha256s to the **same** `4d2dcd7d9cebf85d1da985122053741a18046e3b48bafdbf1082b06877c40c22` — matching the annotation, the local `manifests/configmap-bench-driver-4d2dcd7d.json`, and `code/bench_driver.py` on disk (all four independently hashed this session; all four equal).

**Existing ConfigMaps, verified unchanged** — annotation *and* live payload hash, not annotation alone:
- `kai-chang0926-code-42abed4b5d` (created 2026-09-28T07:54:54Z, untouched by this session). Annotations: `bnjettag.io/bundle-sha256: 42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0`, `bnjettag.io/manifest-sha256: 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42`. The tarball lives in `binaryData['hgq2.tar.gz']`, not `data` (its `data` key list is empty — that's normal for this ConfigMap, not a defect). Base64-decoded live in-session: 198,452 bytes, sha256 `42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0` — **exact match** to both the annotation and the `code_sha` STUDY.md and the PREFLIGHT build half cite. `immutable: true`.
- `kai-chang0926-fp-e9511d1aeb` (created 2026-09-28T22:49:15Z, untouched). Annotations: `bnjettag.io/fingerprint-sha256: e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1`, `bnjettag.io/expect: chang0926-a-n64-s1 initial_ebops 11559681`. Live `data['fingerprint_check.py']`, hashed in-session: sha256 `e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1` — **exact match**. `immutable: true`.

Both are the exact ConfigMaps every `kai-gpubench-*` pod's `sha256sum -c` step checks (`/cmcode/hgq2.tar.gz` against `42abed4b…`, `/cmfp/fingerprint_check.py` against `e9511d1a…`, read directly from each manifest's embedded script in the "What was built" table). Corroborating, not load-bearing: both running pilot pods (`pilotb3`, `pilotb5`) print `MANIFEST_SHA_OK 041f981a9d…` against this same ConfigMap, so it has already been exercised live on a GPU today.

## cluster-ops (2026-09-29)

Read-only diagnosis session, 2026-09-29T07:2x-07:5xZ. Nothing here is a result. **No Job was applied** (rule 5 of the
brief); the only cluster-mutating action this session is the ConfigMap create above. `kai-chang0926-pilotb3-42abed-0-vqxc7`
and `kai-chang0926-pilotb5-42abed-0-qqjmt` were touched only by a read-only `exec ls` / `exec df` (below); neither was
deleted, scaled, or had any file written into its run root.

### Node survey re-run

`cd campaigns/2026-09-29-gpu-benchmark/code && python3 node_survey.py` (live `kubectl get nodes -o json`, a list call,
never a single-node get) → `code/evidence/node_survey_20260929T073945Z.json`, read 2026-09-29T07:39:45Z, 532 nodes cluster-wide
(same total the build-time survey and today's stale `as-jet-train` PodScheduled message both see independently).

| product (resource key) | raw nodes | schedulable | can-hold this Job's pod | allocatable cpu/mem on schedulable nodes | taints seen on the excluded ones |
| --- | ---: | ---: | ---: | --- | --- |
| L40 (`nvidia.com/gpu`) | 17 | 6 | 6 | 20 cpu / 503.3 Gi, uniform | 11× `nautilus.io/reservation=csu-tide:NoSchedule` |
| L40S (`nvidia.com/gpu`) | 4 | 2 | 2 | 28 cpu / 503.6 Gi | 1× `nautilus.io/issue=1731:NoSchedule` (bak-hpc2); 1× not-Ready virtual node (`swan-interlink`, no GPU-memory label, several `virtual-node.interlink/*` + `node.kubernetes.io/not-ready` taints) |
| RTX 4090 (`nvidia.com/gpu`) | 4 | 3 | 3 | 28 cpu / 251.5-755.5 Gi | 1× `Ready=Unknown` + `node.kubernetes.io/unreachable` |
| RTX 3090 (`nvidia.com/gpu`) | 49 | 30 | 29 | 12-60 cpu / 31.2-503.6 Gi | mostly per-campus `nautilus.io/reservation=<school>:NoSchedule` (csusb, cogrob ×8, suncave-head/-5) and 3× `Ready=Unknown`/cordoned; plus our own 2 exclusions (below) |
| RTX A6000 (`nvidia.com/rtxa6000`) | 8 | 5 | 5 | 20 cpu / 251.5 Gi, uniform | `nautilus.io/testing`, `nautilus.io/reservation=sdccd`, 1× `Ready=Unknown` |
| A40 (`nvidia.com/a40`) | 3 | 2 | 2 | 44 / 60 cpu, 503.3-503.6 Gi | 1× `nautilus.io/issue=1731:NoSchedule` (bak-hpc1) |
| A100-SXM4-80GB (`nvidia.com/a100`) | 22 | 16 | 16 | 124-252 cpu / 471.6-1007.3 Gi | `nautilus.io/hardware=large-gpu` ×3, `nautilus.io/reservation=mizzou` ×2 / `=nrp-llm` ×1, 1× cordoned+upgrading |

"Can-hold" replicates `gen_bench.py`'s own ceiling test (`NODE_RESERVE_CPU, NODE_RESERVE_MEM_GI = 2, 16`, confirmed at
`gen_bench.py:73`) against each product's own Job's `resources.requests` (read from the manifest, not assumed): L40/L40S/A40/A6000
18 cpu + 72 Gi, 4090/3090 10 cpu + 40 Gi, A100 32 cpu + 128 Gi. **This is a static capacity ceiling, not a live free-capacity
read** — it says a pod of this shape fits on the node's declared allocatable resources minus the fixed daemon reserve; it
says nothing about what else is already running there. All seven schedulable/can-hold counts are byte-identical to
`node_survey_20260929T065531Z.json` (06:55:31Z, the build-time read): 6, 2, 3, 30, 5, 2, 16 in the order above — nothing
moved in the 44 minutes between reads, so open item 2's "regenerate if anything moved" does not fire.

**3090 raw-node discrepancy, resolved, not a real change.** The fresh survey counts 49 raw 3090-labelled nodes; the
build-time survey and this session's own `nrp_doctor.py lint` both say 48. Cause: `suncave-0` carries the
`nvidia.com/gpu.product=NVIDIA-GeForce-RTX-3090` label but offers **zero** nonzero `nvidia.com/*` allocatable (`gpus {}`
in the raw dump) and is `Ready=Unknown`/cordoned. `node_survey.py` counts every labelled node ("raw nodes" above);
`nrp_doctor.gpu_resource_map()` (what `lint`'s "N nodes cluster-wide" uses) counts only nodes offering a nonzero GPU
resource, so it excludes `suncave-0`. Both tools are self-consistent; the schedulable count (30) and can-hold count (29)
are unaffected either way.

**CPU slack after the 2-CPU reserve is the real constraint, not the ceiling test above** (task hint: "18 CPU / 72 Gi on
20-CPU L40 and A6000 nodes is tight" — confirmed, and one more case found beyond the hint):

| product | pod cpu request | schedulable-node cpu | slack after 2-cpu reserve |
| --- | ---: | --- | --- |
| L40 | 18 | 20 (all 6 nodes) | **0** — any other pod already on the node blocks this one |
| RTX A6000 | 18 | 20 (all 5 nodes) | **0** — same |
| RTX 3090 | 10 | 12 (14 of the 29 can-hold nodes: the `suncave-*` fleet) / 20-60 (the rest) | **0 on the suncave nodes**, 8-48 elsewhere — the pool is wide enough that this matters less |
| L40S | 18 | 28 | 8 |
| RTX 4090 | 10 | 28 | 18 |
| A40 | 18 | 44 / 60 | 26 / 42 |
| A100 | 32 | 124 / 252 | 92 / 220 |

Zero slack does not mean the pod cannot schedule — `gen_bench.py` already capped A6000 E at K=9 (not the K_rule 10) for
exactly this reason — it means the node must currently be running **nothing else** for our pod to fit, which the next
check partially probes.

### What is, and is not, visible about current occupancy

We can list pods only in `cms-ml`; other namespaces' pods on the same physical nodes are invisible from here (confirmed
again this session: `kubectl get pods` inside `cms-ml` works, there is no cluster-scope pod list). So the count below is
a **lower bound** on real occupancy, not free capacity. Cross-referencing the 287 live `cms-ml` pods'
`spec.nodeName` against each product's can-hold node list (all "other user" pod name prefixes match the setup doc's
etiquette section — `zh-`, `tn-`, `rino-`-style, `raunav-`, `mtx-`, `ft-legs-`, `mpt-`, `tpdm-`, `bbtautauserverdep`, `eflm-serverdep`,
`hhbbvvserverdep` — none of it ours):

| product | can-hold nodes | of which ≥1 cms-ml pod visible right now |
| --- | ---: | ---: |
| L40S | 2 | 0 |
| RTX A6000 | 5 | 0 |
| A40 | 2 | 1 (`k8s-usra-01...`: two long-running `*serverdep` pods) |
| RTX 4090 | 3 | 2 |
| L40 | 6 | 1 (`rci-tide-gpu-05.sdsu.edu`: 3 pods, incl. 2 `*serverdep`) |
| A100 | 16 | 4 (training jobs, e.g. `zh-mpmv2-rino-*-train-*`) |
| RTX 3090 | 29 | 9 |

A visible occupant does not prove the node is full (a `*serverdep` pod's own cpu request may be small), and an empty row
does not prove the node is free (another namespace could hold it). Read as a soft signal only.

**One weak, indirect, third-party data point on A40 specifically** (not ours, not part of this campaign, offered because
it is the only visible neighbor evidence for any of the seven products): three long-Pending `as-jet-train-gqt30-h-cfg-*-a40-*`
pods (4d22h old at first read this session), each requesting `nvidia.com/a40` (the correct resource key, so this is not the
resource-name confusion the setup doc warns about). One pod's `PodScheduled` message, read via jsonpath: dominant bucket is
`307 node(s) didn't match Pod's node affinity/selector` (expected — only 3 nodes cluster-wide carry the A40 label at all);
`1 Insufficient nvidia.com/a40` is not a large bucket by count, but there are only 2 A40 nodes schedulable for anyone in the
first place, so a single-digit "Insufficient" count is not informative either way at this pool size. Read as: **someone
else's A40 request has not scheduled in almost 5 days; this is not proof our A40 Job will queue, but it is not a
reassuring sign, and it is the only outside evidence we have.**

### No A10, node exclusions, run root, PVC — all 7 manifests

> v1 (7 manifests). Since STUDY Amendment 1 the two A10 Jobs request the A10, with the yield rule; `code/plan_check.py`
> checks the product pin, the four exclusions and the run root on all 16.

Read every `manifests/kai-gpubench-*.json` directly (not the prose descriptions of them) this session:

- **No A10.** Resource key + pinned product per manifest: L40/L40S/4090/3090 → `nvidia.com/gpu` with `NVIDIA-L40` /
  `NVIDIA-L40S` / `NVIDIA-GeForce-RTX-4090` / `NVIDIA-GeForce-RTX-3090` respectively; A6000 → `nvidia.com/rtxa6000`
  / `NVIDIA-RTX-A6000`; A40 → `nvidia.com/a40` / `NVIDIA-A40`; A100 → `nvidia.com/a100` / `NVIDIA-A100-SXM4-80GB`. None
  requests `NVIDIA-A10` or a bare `nvidia.com/gpu` with no product pin. Confirmed on all 7, not a sample.
- **Node exclusions.** Every one of the 7 has exactly the same `kubernetes.io/hostname NotIn` list — `hcc-nrp-shor-c6017.unl.edu`,
  `k8s-chase-ci-07.calit2.optiputer.net`, `nautilus-ext-gpu01.fullerton.edu`, `ren-gp-argo-01.madren.org` — no manifest is
  missing any of the four, none adds an extra one. `nrp_doctor.py`'s `KNOWN_BAD_NODES` today holds only the Fullerton entry
  (`2026-09-17 UnexpectedAdmissionError: GPU is lost`), which is why `lint` above raised no missing-exclusion WARN; the other
  three come from `node_survey.py`'s own wider list (`C6017` — "Delta REGRESSION_TICKET 2026-09-28" — plus
  `PILOT_B_BAD`), which the manifests correctly also honor even though `nrp_doctor.py lint` cannot itself check them yet.
  c6017 in particular is confirmed excluded on all 7 by direct inspection, not inferred from the lint pass.
- **Run root.** Every manifest's pod script sets `BR=/data/chang-n64-20260926/gpu-bench/<slug>` (`<slug>` = l40, l40s,
  geforce-rtx-4090, geforce-rtx-3090, rtx-a6000, a40, a100-sxm4-80gb) and refuses to start if `$BR/samples.csv` exists or
  any `$BR/p[0-9]*` directory exists (`BENCH_ROOT_NOT_EMPTY`, exit 11) — confirmed in the embedded script of all 7, not just
  one.
- **PVC check, read-only, via the running pilot pod** (never touched its own process, only `exec`'d a shell command
  alongside it):
  ```
  $ kubectl -n cms-ml exec kai-chang0926-pilotb3-42abed-0-vqxc7 -- ls -la /data/chang-n64-20260926/
  drwxr-xr-x  5 root root    4 Sep 28 23:26 .
  -rw-r--r--  1 root root 8424 Sep 27 17:50 cache_manifest.json
  drwxr-xr-x  3 root root    2 Sep 27 17:50 n64
  drwxr-xr-x  4 root root    2 Sep 27 20:53 pilot
  drwxr-xr-x  4 root root    2 Sep 28 23:26 pilot-b
  ```
  **No `gpu-bench/` directory exists yet** — every one of the 7 run roots is clean; none of the seven Jobs would trip
  `BENCH_ROOT_NOT_EMPTY` right now.
  ```
  $ kubectl -n cms-ml exec kai-chang0926-pilotb3-42abed-0-vqxc7 -- df -h /data
  Filesystem ... Size  Used Avail Use%
  csi-cephfs-node@...                                          100G   34G   67G  34%   /data
  ```
  67 Gi free of 100 Gi (34% used). The build half's own estimate for all seven Jobs together is about 1-2 GB — not a
  constraint.

### Quota and pod count

`kubectl -n cms-ml get resourcequota -o json`, read between 2026-09-29T07:39Z and 07:48Z:

```
a100-limit      requests.nvidia.com/a100   used=23  hard=24
gh200-limit     requests.nvidia.com/gh200  used=0   hard=0
h100-limit      requests.nvidia.com/h100   used=0   hard=0
h200-limit      requests.nvidia.com/h200   used=0   hard=0
reached-quota   pods                       used=123 hard=200
```
A100 is at **23/24 — one free quota unit** (matches the build half's 05:55Z read; unchanged 1h45m later). H100/H200/GH200
remain hard-banned at 0, consistent with the setup doc. `nvidia.com/gpu`, `rtxa6000` and `a40` carry no quota object at
all (confirmed by absence, not inferred).

**Pod count, reconciled rather than left as two numbers.** `kubectl -n cms-ml get pods` lists **287** rows: 36 Pending +
87 Running + 158 Succeeded + 6 Failed. The `reached-quota` "pods" object counts only non-terminal pods — 36 + 87 = **123**,
exactly its reported `used`. A `nrp_doctor.py status` call about a minute later read **122/200**: one pod transitioned
out of Pending/Running (most likely a Succeeded/Failed completion elsewhere in the namespace, not ours — our own two pods
were unchanged Running throughout, confirmed by `nrp_doctor.py status`'s own pod-age readout) in the gap between the two
reads; this is normal churn in a 280-pod shared namespace, not a discrepancy to chase. If all seven benchmark pods reach
Running simultaneously, the namespace's pod count moves to about 129-130/200 — nowhere near the 200 hard cap, not a
blocker.

### Blockers

> v1.

**None.** Zero lint ERROR, zero dry-run rejection, both ConfigMap payloads byte-verified against the shas the Jobs
check, no A10 anywhere, all four node exclusions present on all 7 manifests, all 7 run roots clean on the PVC, 67 Gi
free. Queue risks to carry into RUN.md, not blockers: the A6000/L40 zero-CPU-slack nodes, the A100's single quota unit
(first tenant to request it after this read gets it — a lost race means the Job controller's pod creation is denied at
admission; no pod object is ever created, so nothing counts against `backoffLimit`, and the controller keeps retrying
creation on its own until the quota frees or [D6]'s 6 h expires — see STUDY exclusion rule 3 / [D6] for what happens if
nothing schedules within 6 h), and the generally narrow per-product pools (2-6 schedulable nodes for five of the seven
products).

### Apply order (not executed — recommendation only)

> v1, superseded by the 16-Job order in "Fixer v1 rebuild".

Most-likely-to-schedule-soon first, A100 last, from the schedulability table plus the CPU-slack and visible-occupancy
reads above (a judgment call combining several soft signals — see "Where I am not sure"):

1. **3090** — widest pool by far (29 can-hold nodes, most with real CPU slack, only 9/29 show a visible cms-ml occupant).
2. **L40S** — only 2 can-hold nodes, but both fully clear of any visible cms-ml pod and 8 cpu of slack.
3. **RTX 4090** — 3 can-hold nodes, 18 cpu slack each, though 2 of 3 already show a visible cms-ml pod.
4. **RTX A6000** — 5 can-hold nodes, all clear of any visible cms-ml pod, but 0 cpu slack (tight).
5. **L40** — 6 can-hold nodes, 5 of 6 clear, also 0 cpu slack (tight).
6. **A40** — only 2 can-hold nodes, 1 already visibly occupied, plus the weak outside evidence of a 4d22h-Pending A40
   pod elsewhere in the namespace.
7. **A100 last** — 16 can-hold nodes with abundant slack, but gated on the single remaining quota unit; per the brief's
   ordering instruction it is applied last regardless (see the quota-timing note below).

```
kubectl create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-geforce-rtx-3090.json -n cms-ml
kubectl create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-l40s.json -n cms-ml
kubectl create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-geforce-rtx-4090.json -n cms-ml
kubectl create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-rtx-a6000.json -n cms-ml
kubectl create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-l40.json -n cms-ml
kubectl create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a40.json -n cms-ml
kubectl create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a100-sxm4-80gb.json -n cms-ml
```

Each of these 7 has already passed both `nrp_doctor.py lint` and a server-side dry run in this session (above); re-lint
only if any manifest is edited before applying (owned rule: "lint again after any edit").

### Tooling note

A `for f in manifests/kai-gpubench-*.json; do kubectl create --dry-run=server -f "$f" ...; done` loop was blocked by
`.claude/hooks/pre-kubectl-lint.py` with `file not found from ...: $f` — the hook's regex reads the literal command text
before shell expansion, so it cannot resolve a loop variable. Not a bug worth fixing here: every dry run above was re-run
as its own `kubectl` invocation with the literal path, and none of those was blocked (each returned the API server's
`created (server dry run)` line directly, rc=0) — consistent with the hook passing a WARN-only manifest through, though
its own stderr was not captured in this session's tool output. Worth knowing for whoever next scripts a multi-manifest
dry run.

### Where I am not sure

```
DECISION: apply order 3090 / L40S / 4090 / A6000 / L40 / A40 / A100, ranked by can-hold node count, cpu slack after the
2-cpu reserve, and visible-cms-ml-occupancy as a lower bound (soft signals, none individually decisive).
ALTERNATIVES: order strictly by can-hold count alone (would swap A6000 and L40's position only, both 0-slack and both
narrow); wait for the STUDY's own [D4] probe instead of this static read.   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO —
informational ordering only, nothing breaks if applied in a different order.

DECISION: A100 applied last, per the brief's explicit instruction.   OBSERVATION (not a deviation): the single remaining
A100 quota unit is a race against the rest of the Duarte group, not a queue — applying A100 last means the 6 other Jobs'
apply time is exactly the window in which another tenant could take that unit first, more so than if it were applied
first. Not resolved here; flagging the tension for whoever actually applies.   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES.

DECISION: the A40 third-party pod's PodScheduled message is reported as weak/ambiguous evidence, not as proof of A40
contention.   CONFIDENCE: LOW (on the A40-saturation question itself, not on the read of the message, which is verbatim).
FLAG FOR HUMAN: NO — informational, gates nothing.
```

No cluster incident occurred this session (no manifest lint ERROR, no dry-run rejection, no bad-node signature, nothing
that changed `docs/infrastructure/nrp-nautilus-setup.md` or `nrp_doctor.py`), so nothing was appended to
`.claude/memory/cluster-inventory.md`. `.claude/memory/experiment-log.md`'s Ops-pointer for this campaign belongs to
whichever session writes `RUN.md`, not to this PREFLIGHT contribution.


## Fixer v1 rebuild: ConfigMap, lint, dry-run, apply order (2026-09-29, 08:30-08:45Z)

Nothing applied: no Job exists (`kubectl -n cms-ml get jobs -l campaign=gpu-bench-20260929`: "No resources found", 08:41Z).
The one cluster-mutating action is the driver ConfigMap create below. The running pilot Jobs were read, never touched.

**Driver ConfigMap, created and verified.** `kubectl -n cms-ml create -f manifests/configmap-bench-driver-5ede0778.json` →
`configmap/kai-gpubench-driver-5ede0778f7 created` (server `creationTimestamp` 2026-09-29T08:38:07Z; a `get` just before
returned NotFound). On the live object: `immutable: true`; labels `{campaign: gpu-bench-20260929, user: kai}`. The
annotation `bnjettag.io/bench-driver-sha256`, the live `data['bench_driver.py']` payload hashed in-session, the local
manifest's payload and `code/bench_driver.py` all hash to `5ede0778f716cb9299ca82c64547fb993c93d775572d33463a0fef4cbf676c45`.
The frozen ConfigMaps' live payloads, re-hashed: `kai-chang0926-code-42abed4b5d` `binaryData['hgq2.tar.gz']` `42abed4b5d2e3e91…`
and `kai-chang0926-fp-e9511d1aeb` `data['fingerprint_check.py']` `e9511d1aeb39c7c8…`, both `immutable: true`, creation times
unchanged (2026-09-28T07:54:54Z, 22:49:15Z).

**Lint** (`code/evidence/lint_gpubench_build.log`): 0 ERROR, 12 WARN (each "required pool = 1 products / n nodes
cluster-wide <-- narrow; expect queueing"), 4 OK (both A10 and both 3090 Jobs), exit 1. The WARN is answered as in v1: the
Pool-policy exception for a controlled timing comparison (decisions.md 2026-09-29), which ends when the benchmark Jobs are
deleted.

**Server-side dry run**, one literal-path command per Job (the lint hook reads the command text and cannot resolve a loop
variable). All 16 returned `job.batch/<name> created (server dry run)`:
```
kai-gpubench-geforce-rtx-3090-klow    kai-gpubench-geforce-rtx-3090-krule   kai-gpubench-geforce-rtx-4090-klow
kai-gpubench-geforce-rtx-4090-krule   kai-gpubench-l40s-klow                kai-gpubench-l40s-krule
kai-gpubench-l40-klow                 kai-gpubench-l40-krule                kai-gpubench-rtx-a6000-klow
kai-gpubench-rtx-a6000-krule          kai-gpubench-a40-klow                 kai-gpubench-a40-krule
kai-gpubench-a100-sxm4-80gb-krule     kai-gpubench-a100-sxm4-80gb-klow      kai-gpubench-a10-krule
kai-gpubench-a10-klow
```
The API server accepts the pod-level `activeDeadlineSeconds` and the required `podAntiAffinity` on all 16.

**State at 08:41Z, read-only.** `requests.nvidia.com/a100` 23 / 24; pods 115 / 200. Chang pods:
`kai-chang0926-pilotb3-42abed-0-vqxc7` Running on gpu-17.nrp.mghpcc.org and `kai-chang0926-pilotb5-42abed-0-qqjmt` Running on
hcc-nrp-shor-c5805.unl.edu; no pilot-b pod Pending.

**Apply order** (a recommendation, not executed): small pods on wide pools first, the 18-CPU pods on zero-slack nodes later,
the A100 pair in sequence, the A10 pair last.

| # | Job | why here |
| ---: | --- | --- |
| 1-2 | `geforce-rtx-3090-klow`, `-krule` | 29 nodes can hold either pod |
| 3-4 | `geforce-rtx-4090-klow`, `-krule` | 3 nodes, 16-18 CPUs of slack |
| 5-6 | `l40s-klow`, `-krule` | 2 nodes; the pair runs at once only if both are free (anti-affinity) |
| 7-8 | `rtx-a6000-klow`, `l40-klow` | 8-CPU pods on 20-CPU nodes: 10 CPUs of slack |
| 9-10 | `rtx-a6000-krule`, `l40-krule` | 18-CPU pods with 0 slack after the reserve: they need an otherwise idle node |
| 11-12 | `a40-klow`, `-krule` | 2 nodes; cluster-ops' only outside evidence, a third-party A40 pod Pending for almost 5 days, is not reassuring |
| 13 | `a100-sxm4-80gb-krule` | one free `a100` quota unit; at G ≤ 1, [D3] leans to the high K |
| 14 | `a100-sxm4-80gb-klow` | **only after the A100 K_rule pod has terminated.** Applied together, its pod creation is denied at admission while the unit is held, and its [D6] clock would already be running |
| 15-16 | `a10-krule`, `a10-klow` | **last, only with the live watcher running and while no Chang pilot-b pod is Pending** (Open item 5) |

```
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-geforce-rtx-3090-klow.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-geforce-rtx-3090-krule.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-geforce-rtx-4090-klow.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-geforce-rtx-4090-krule.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-l40s-klow.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-l40s-krule.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-rtx-a6000-klow.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-l40-klow.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-rtx-a6000-krule.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-l40-krule.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a40-klow.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a40-krule.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a100-sxm4-80gb-krule.json
# only after the A100 K_rule pod has terminated:
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a100-sxm4-80gb-klow.json
# last, only with the live watcher running and while no Chang pilot-b pod is Pending (Open item 5):
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a10-krule.json
kubectl -n cms-ml create -f /Users/kaiyamaguchi/Desktop/bnjettag/campaigns/2026-09-29-gpu-benchmark/manifests/kai-gpubench-a10-klow.json
```

Each of these 16 passed `nrp_doctor.py lint` and a server-side dry run in this session; lint again after any edit.

**Fixer v2 (critical v2 C5, 09:53Z).** The two A10 manifests were regenerated with the pilot-b nodes in their `NotIn`
(`gen_bench.py --survey code/evidence/node_survey_20260929T073945Z.json`, first in a scratch mirror). The other 16 generated files
are byte-identical, including every manifest applied so far (3090 K_low sha256 `16a600f4…` unchanged). Then:
- `nrp_doctor.py lint` on both A10 manifests: `OK` each, rc 0;
- `kubectl -n cms-ml create --dry-run=server -f <literal path>`: `job.batch/kai-gpubench-a10-krule created (server dry run)` and
  `job.batch/kai-gpubench-a10-klow created (server dry run)`;
- `plan_check.py`: 16 × `PLAN_OK`, `GENERATOR_IDEMPOTENT`, `PLAN_CHECK_ALL_OK`.

Evidence: `code/evidence/lint_dryrun_a10_fixer_v2.log`, `plan_check.log`. Nothing was applied or deleted.
