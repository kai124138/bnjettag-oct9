# PREFLIGHT critical review v1 — 2026-09-29-gpu-benchmark (solo gate, build half)

Reviewer: critical-reviewer (solo mode). Date: 2026-09-29 00:52 PDT (07:52Z).
Scope: `STUDY.md` (designed), `review/PREFLIGHT_snapshot_v1.md` (build half only; the live cluster half is not reviewed),
`code/` (bench_driver, gen_bench, bench_summary, node_survey, test_bench, cpu_gate_bench.sh, evidence/),
`manifests/kai-gpubench-*.json` (7) and `manifests/configmap-bench-driver-4d2dcd7d.json`.
Every number below is telemetry or arithmetic, never a result.

**VERDICT: ITERATE.** The harness is a faithful copy of `run_study.train`'s compute path. The manifests are correct on
every item the brief lists (products, keys, exclusions, retries, deadlines, roots, gate order) and reproducible; their
per-phase CPU shape is A2. Two Category A problems remain. (A1) The A10 baseline decides the headline question, but
it is not measured the way the candidates are. The lab's own A10 logs put the translation error at 23 % (E) and
46 % (A07), against a 10 % tie margin, all in the candidates' favour. (A2) The STUDY's held-fixed "2 CPU per arm"
holds in only one of the four phases per product, and the excess differs by product.

## Checked, and recomputed

- The bundle tarball hashes to `42abed4b5d2e…c258c0`. I extracted it fresh to scratch. `diff -rq` against
  `training-batch/code/tree` differs only by `analysis/`, so the review read the bundle itself.
- Compute path: bundle `run_study.py:94-195` and `bnhgq2/ablation.py:483-489, 682-1001`, plus `run_engram.py:100-221`
  and `wandb_util.run_stage`, all read against `bench_driver.py:138-213`.
- Pod header: every exported variable diffed against `training-batch/manifests/pilot-b-k5-job.json`.
- Re-ran `test_bench.py` on a scratch copy: `ALL_PASS 12`.
- Re-ran `gen_bench.py` on a scratch copy with `--survey node_survey_20260929T065531Z.json`. All 7 Jobs,
  `bench_plan.json` and the ConfigMap came out **byte-identical** (`cmp`). The ConfigMap payload hashes to `4d2dcd7d9ceb…0c22`,
  which equals the driver file.
- Parsed all 7 manifests (table under Q2 below).
- Recomputed the [D1] s from raw logs with my own parser (not `bench_summary`):
  - A10 pilot-b K=5 mixed E: A-s1 140.17, A-s2 140.36, D-s1 140.28. The slowest (140.36) matches the PREFLIGHT's 140.4.
  - A10 pilot-b K=3 mixed A07: A07-350-s1 132.14, C-s1 132.48. This matches 132.5.
  - Delta canary-v2 E-k4 on A10 (pure pack): 114.45 / 112.43 / 111.70 / 111.46.
  - Delta A07 canary on A10 (K=2 after s3's start-up OOM): 90.73 / 90.37.
  - Sources: `training-batch/logs/*pilotb{5,3}-42abed-0-20260929T0305Z.log`,
    `delta-screen/logs/canary-v2-E-k4-s{1..4}.log` and `canary-a07-rep-c-s{1,2}-20260929T0608Z.log`.
- `bench_summary.pod_facts` on a pod.json shaped like a finished pod (see B1) returns
  `{'queue_seconds': 5395.0, 'pod_created_to_ready_seconds': None, 'job_created_to_ready_seconds': None}`.

## Validator output

- `nrp_doctor.py lint`: taken from the saved build-time log `code/evidence/lint_gpubench_build.log`. I did not re-run it,
  because it queries the cluster and cluster-ops runs it at launch. The log shows 0 ERROR and one WARN on six manifests:
  `WARN   required pool = 1 products / <n> nodes cluster-wide  <-- narrow; expect queueing`. The WARN is answered by the
  narrow-pool decision (decisions.md 2026-09-29). The log ends `rc=1`.
- `test_bench.py`: `ALL_PASS 12` (my re-run).
- `plan_check.log`: `PLAN_OK` on all 7 Jobs, then `GENERATOR_IDEMPOTENT`.

## The brief's four questions

**Q1. Does the compute path equal `run_study.train` on the same config?** Yes, apart from W&B.
- TF32 is off, through the API (`bench_driver.py:147-148`, as `run_study.py:98-99`) and through `NVIDIA_TF32_OVERRIDE=0` in the header.
- The GPU is asserted (`:150-151`).
- `validate_cfg` is called (`:158`). The config is read from the same `BNJ_CAMPAIGN_DIR`, by name, and its sha256 is checked
  against the index row (`:123-135`), which is stricter than `run_study.py:101-102`.
- The cache comes from `run_engram.load_cache(BNJ_DATA_ROOT/n64/data)`, with every array hashed and the 620,000-row split
  checked (`run_engram.py:177-221`). The data is memory-mapped (`:197`) and moved to the GPU once
  (`ablation.py:199`), the same as in production.
- `stop_after` 21 with `train.epochs` 7,000. Traced epochs are zero-based 0, 9 and 19 (`ablation.py:483-489`), which are
  one-based 1, 10 and 20.
- The same `model_builder` and `epoch_observer` are passed.
- `verify_selected` is the bundle's own function, called with the same arguments (`:198`).
- Thread variables match pilot-b: OMP 2, intra 2, inter 1, OPENBLAS 1; `runtime()`'s `setdefault` keeps the header's values.
- `TF_FORCE_GPU_ALLOW_GROWTH` is set, and the RSS-gate variables are set.
- `remote` gates only `ablation.py:746-756`. Every later W&B use is behind `wandb_run`. `elapsed` is taken at `:874`,
  before any W&B call.
- `validate_tracking_destination` and `run_stage` have no effect on compute: they only read the environment, query W&B
  and raise.
- `BNJ_RUN_ROOT` is not read by the arm path, since `run_study.ROOT` is used only by `train` and `preflight`.
- The one remaining difference is W&B's background process during training, which production has and the benchmark
  does not. The PREFLIGHT notes it (snapshot l. 39-41). It matters only through A1.

**Q2. Manifests.** Every item passes.
- Products and resource keys: L40, L40S, 4090 and 3090 on `nvidia.com/gpu`; A6000 on `nvidia.com/rtxa6000`; A40 on
  `nvidia.com/a40`; A100-SXM4-80GB on `nvidia.com/a100`. No manifest names the A10.
- All four `NotIn` hostnames are present, matching pilot-b plus `KNOWN_BAD_NODES`.
- `backoffLimit` is 0, with no `podFailurePolicy` and `restartPolicy: Never`.
- The fingerprint gate runs before `exec … bench_driver.py pod`, and a failure exits the pod.
- Run roots are `/data/chang-n64-20260926/gpu-bench/<slug>/`. They are disjoint from `pilot/`, `pilot-b/` and
  `/data/delta-20260927/`, and nothing in Chang's tools globs the data root.
- Deadlines: the Job deadline equals 21,600 s plus the pod deadline on all 7 Jobs (e.g. L40: 60,600 = 21,600 + 39,000).
  The pod deadline counts from pod start, and I recomputed its raw value: 38,655 s, rounded to 39,000.
- CPU and memory fit the survey's nodes: 18 CPU on 20-CPU nodes with the 2-CPU reserve, and 32 CPU / 128 Gi on A100
  nodes with 124-252 CPU.

**Q3. Does the summary compute [D1]-[D6]?**
- Implemented as pre-registered:
  - s = (9 × median untraced + median traced)/10 over epochs 2-21, taken on the slowest arm (`bench_summary.py:131-154`);
  - R = K × 3600 / s (`:170`);
  - the 90 % rule on the pod peak (`:219-221`);
  - OOM from the driver's classification (`:308-309`).
- Not working: Q (B1).
- The brief's three "quiet favouring" probes:
  - **60 s sampling against memory peaks: adequate.** Under allow_growth the BFC pool never returns memory, so each
    process's `memory.used` only rises. The evidence: per-process memory is "stable across samples" (Chang `RUN.md`
    l. 212-217), and the Delta A07 canary's 1,009 samples caught its 0.979 pod peak while three processes were alive
    (Delta `RUN.md` l. 537-538). What can be missed is growth in the final minute before the first arm exits. The only
    new work in that minute is `verify_selected`'s reload and predict, at the same `val_batch`.
  - **Slowest arm against median: pre-registered.** Its order-statistic bias grows with K. For a median of 18 epochs at
    a few percent jitter it is well under 1 %. It penalises high K, which is the opposite direction to A2. The pooled
    form is reported beside it (`:173-176`).
  - The CPU per arm does favour some products (A2).

**Q4. Harm to the pilots, production or Delta.** None found.
- No A10 is requested. W&B is off: no secret, `WANDB_MODE=disabled`, `remote=False`, and `sys.modules` is checked
  (`:208-211`).
- The run roots are separate, and run names collide only inside the benchmark root.
- The PVC was at 34 G / 100 G at pod start of pilotb5 (00:11Z), pilotb3 vqxc7 (00:50Z) and the Delta A07 canary
  (03:16Z), from their headers' `df -h /data`. My estimate of the benchmark's footprint is 1.3-2.6 G over 131 arm-runs.
- Pods were at 158 / 200, and the benchmark adds 7. The namespace has no CPU or memory quota.
- The two frozen ConfigMaps are mounted read-only and not modified. The anchor cache is opened `mmap_mode='r'`.
- The A100 Job takes the namespace's last `a100` unit (C4).

## Category A (must resolve)

**A1. The A10 baseline, the comparator of the headline question, is unmatched and unpinned.**
STUDY l. 6, 25, 82-85 and 116-118; `bench_summary.py:335-385`, in particular `:369-370`.

The STUDY asks whether any T(p) is more than 10 % earlier than the A10's. The candidates are measured in the harness:
W&B off, pure packs, K at or under the 90 % rule, and "equal K isolates card speed" (STUDY l. 111). The A10 is read
from pilot-b telemetry: W&B on, mixed packs, K=5 at 97.9 % and K=3 at 92.3 % of memory. [D5] then prices the A10 at
its compliant K (E 4, A07 2). The build computes no R_A10 at that K: `summarize_a10` sets `R_d1 = None`, and its
`class R` (76.9 for E) is a mixed-pack class share that must never be read as R_A10.

The lab's own A10 logs at the compliant K in pure packs show the size of the gap, on the same [D1] formula:

| A10 source | class, K | slowest s [D1] | R = K × 3600 / s |
| --- | --- | ---: | ---: |
| pilot-b telemetry priced at the compliant K (what [L2] implies) | E, 4 | 140.36 | 102.6 |
| Delta canary-v2, pure E-k4 | E, 4 | 114.45 | 125.8 (+23 %) |
| pilot-b telemetry priced at the compliant K | A07, 2 | 132.48 | 54.3 |
| Delta A07 canary, pure A07-k2 | A07, 2 | 90.73 | 79.4 (+46 %) |

Caveat: the Delta logs come from bundle 705a554b (Delta's always-on diagnostics), from other nodes (c6013, c5813),
with W&B state and CPU per arm not established here. They show the scale of the translation error, not the A10
number.

Illustrative arithmetic in the STUDY's own Check scenario (Chang E, G = 7) gives three readings for T(A10):
- 11.25 d, at K=5 with s 138.9 (the STUDY Check, l. 56-57);
- 13.0 d, at K=4 with s 140.36 ([D5] with [L2]);
- 10.6 d, at K=4 with s 114.45.

A candidate at 11.0 d would therefore be more than 10 % earlier, a tie, or slower, depending on which reading is used.

Two inconsistencies in the STUDY itself:
- The Check (l. 56-57) prices the A10 at K=5, while [D5] prices it at K=4.
- The cross-check (l. 118) quotes "median 104.3-104.5 s", which is an all-epoch median, against a [D1] s. On the
  [D1] basis the same logs give 111.5-114.5 s.

Policy item 1 (Kai, `gpu-selection-policy.md:17-19, 30-37`) lists the A10 first among the candidates to run in the
same harness. The "A10 from telemetry" choice comes from the orchestrator's brief (STUDY l. 124, flagged for Kai).

**Fix, a fork (not chosen here):**
- (a) Add an A10 harness Job. The survey already holds NVIDIA-A10 with 30 schedulable nodes. The phases would be E at
  K 4 and 3 and A07 at K 2 and 1, about 3-4 GPU-h. It must carry Kai's yield-to-anchor rule, since the A10s were
  saturated at 03:10Z (Delta `RUN.md` l. 455).
- (b) Keep the telemetry. A1 then stands, and the question goes to Kai as ESCALATE.

Either way, pin T(A10) numerically before any candidate number exists, and fix the Check and the cross-check.

**A2. CPU per arm is not held fixed; the excess differs by product.**
STUDY l. 43 ("identical in every arm: … 2 CPU and 8 GiB per arm"); `gen_bench.py:282-283` and `:163`; Job annotation
`bnjettag.io/per-arm-resources` ("smaller phases leave the rest unused", `gen_bench.py:254-255`); `bench_summary.py:225`.

The pod requests 2 × K_max CPU for all four phases, so only phase 1 runs at 2 CPU per arm. Effective CPU per arm:

| product | p1 E K_run | p2 A07 K_run | p3 E K_low | p4 A07 K_low |
| --- | ---: | ---: | ---: | ---: |
| L40, L40S, A40 (18 CPU) | 2.0 | 4.5 | 4.5 | 9.0 |
| A6000 (18 CPU) | 2.0 | 3.6 | 4.5 | 9.0 |
| 4090, 3090 (10 CPU) | 2.0 | 5.0 | 2.5 | 10.0 |
| A100 (32 CPU) | 2.0 | 4.0 | 8.0 | 16.0 |
| A10 baseline (pilot-b) | 2.0 | 2.0 | — | — |

Where this bites:
- Every A07 figure and the "equal K" E phase get more CPU than production (2 per arm) or the A10 get, and unequally:
  E at K=4 runs at 2.5 CPU per arm on the 24 GB cards and 8.0 on the A100.
- The direction is consistent; the magnitude is unmeasured. The setup doc's "epoch time that tracks the node's CPU"
  (`nrp-nautilus-setup.md:285-288`) describes an older ~19k-parameter trainer. Today's epoch runs as one `tf.function`,
  but the per-epoch save, reload, predict and `gc.collect()` inside `elapsed` (`ablation.py:796-811`) run on the CPU.
- The PREFLIGHT's "Alignment with STUDY.md" does not list this departure. The annotation asserts the extra CPU goes
  unused, and nothing enforces that.
- `bench_summary.py:225` labels `2 * k` as `cpu_request_cores`, but the pod's actual request is 2 × K_max.

**Fix:**
- Minimum: a dated STUDY amendment stating the per-phase CPU, plus a pre-registered rule in `bench_summary`. The
  sampler already records cgroup `usage_usec`. A phase whose steady cores ÷ K exceed 2.0 is labelled "above the
  production CPU budget", and its s is not used in T.
- Full fix: one Job per (product, phase shape) at 2K CPU / 8K Gi. This also clears B6. `sched_setaffinity` is not a
  clean substitute, because of SMT siblings and neighbour load on the chosen cores.
- Any driver change re-hashes the ConfigMap. All 7 manifests must then be regenerated and re-linted.

## Category B (should address)

**B1. Q (apply to Running) comes out None for every product.**
- Where: `bench_summary.py:254-261`; PREFLIGHT snapshot l. 324 and l. 438-443.
- Cause: `pod_facts` needs `Ready=True`, but a finished pod carries `Ready False, reason PodCompleted`. The lab's own
  `campaigns/2026-09-20-status/cluster.json` shows this: pod `kai-batch0917-screen-e100-r3-0-94g6w` has
  `Ready False PodCompleted` and has `containerStatuses[0].state.terminated.startedAt`. Open item 5 saves pod.json
  after the Job ends.
- Result: `job_created_to_ready_seconds` is None (my run above). Only creation to PodScheduled remains, and that misses
  the Job-to-pod gap (A100 quota admission) and the image pull. No test covers `pod_facts`, and the CPU-gate summary
  shows "-" for both Q columns.
- Fix: fall back to `containerStatuses[].state.{running,terminated}.startedAt`, as `summarize_probe` already does
  (`:398-400`), or to the `BENCH_POD … <UTC>` line. Add a test with a Succeeded pod.

**B2. Outcome and exclusion gaps in the summary.**
- Crash, stall and verify_fail outcomes appear in no `excluded` or flag column; a host-memory OOM kill counts as
  `crash`.
- `all_arms_completed` compares against the largest epoch count among the arms (`:164-167`), not against `stop_after`.
  A phase in which every arm was stopped at the same epoch, say by the deadline or a SIGTERM, still gets an R.
- In `classify` (`bench_driver.py:476-479`), exit 6 plus any OOM-looking line becomes `oom`, because the OOM test runs
  before the exit-code test.
- Fix: compare against the plan's `stop_after`, let exit codes win in `classify`, and list every non-ok outcome in the
  row.

**B3. A `CHECKPOINT_VERIFICATION_FAIL` has no pre-registered consequence, yet it would break production on that product.**
- Production's `run_study.train` calls `verify_selected` at every pause (`run_study.py:150, 172-177`). An
  `AssertionError` there becomes a crash, then retries, then `ARM_FAILED_AFTER_RETRIES`.
- Fix: pre-register a FAIL on a product as excluding it from production until resolved, or as routing to Kai. Record
  the replay deltas.

**B4. The node's CPU is not recorded, and one node per product is measured.**
- Policy item 1 says "Record … CPU and host RAM" (`gpu-selection-policy.md:32-33`). The header logs GPU, driver, pip
  freeze and node name, but no CPU model or clock.
- With [L1] and A2, the REPORT cannot tell a slow card from a slow host.
- Fix: add one header line (`lscpu` model, MHz, sockets, threads; `nproc`), carry it into the summary rows, and name
  the node CPU beside each s. For the finalists, consider giving falsifier (ii) a second node.

**B5. The NRP 40 % utilization floor for the benchmark pods themselves is unassessed.**
- Both low-K phases run last. At A10 aggregate cost that is the final 1.2 h on the 46-80 GB cards and 0.9 h on the
  24 GB cards, including A07 at K=1 on the 4090/3090.
- Per `nrp-nautilus-setup.md:281-283`, the alert looks back 3 h, deletion by admins is a recorded violation, and three
  violations flag the account.
- Fix: estimate the trailing window per product, or interleave the phases (E K_run, E K_low, A07 K_run, A07 K_low), or
  record the risk as accepted.

**B6. Rule 3 is decided by the K_max pod shape.** A product whose 18-CPU pod never schedules is declared "not
practical" for every K, even if an 8-CPU K_low pod would schedule at once. The L40 and A6000 nodes have 20 CPUs, so
the pod needs a node on which at most 2 CPU are already requested. The fix is the same as A2's full fix: per-phase
Jobs.

## Category C (suggestions)

- **C1.** s is taken from `seconds=`, which excludes the per-epoch work after `elapsed` (`ablation.py:874`): the
  observer (`:907`), the jsonl write with fsync to the PVC (`:914-917`) and the checkpoint every 25 epochs (`:926`).
  This is the same definition as Chang's s_e, and probably small. Report arm wall time minus the sum of `seconds=` as a
  check.
- **C2.** The per-process GPU memory relies on nvidia-smi reporting container PIDs, which is verified on the A10
  nodes only. Rule 1 uses the pod total, so only telemetry is at risk.
- **C3.** Fingerprint on new architectures: rule 2 excludes the product on any mismatch. That is right operationally,
  because production's gate would refuse too. Still record whether every pod of the product gives the same value
  (architecture-deterministic) or scattered values (a node fault); the [D4] probe gives this for free.
- **C4.** The A100 Job takes the namespace's last `requests.nvidia.com/a100` unit (23/24 at 05:55Z) for up to
  80,400 s. Re-check the quota at apply, as a courtesy to other cms-ml users.
- **C5.** Survey drift for cluster-ops. `code/evidence/node_survey_20260929T073945Z.json` now exists. Regenerating from
  it changes only the `bnjettag.io/node-survey` annotation on all 7 Jobs (verified by diff). The 3090 total is now 49
  nodes.
- **C6.** If a product's directory ends up with two pod logs (a re-run after a fingerprint failure, which Open item 6
  does not ask to move aside), `pod_facts` takes `fingerprint_ok` from whichever log sorts last.
- **C7.** Rule 3's claim "applied by about 08:00Z … ends before the epoch-500 readout" (STUDY l. 66-67) no longer holds
  if the apply slips. Restate the expected end times against the readout (K=3 terminal about 18:15Z; A and D pause
  about 19:40Z).

## The competing-group question

A group publishing the same comparison next month would have:
- the baseline card measured in the same harness (A1);
- CPU per arm matched to the production shape in every phase (A2);
- the node CPU recorded, with a second node for the finalists (B4);
- a working queue measurement (B1).

None of these is currently justified as not needed.

## Solid

- The driver's compute path equals `run_study.train` apart from W&B (Q1).
- The seven manifests are correct on every item the brief lists (products, keys, exclusions, retries, deadlines,
  roots, gate order) and regenerate byte-identical from the cited survey (Q2); their per-phase CPU shape is A2.
- The 21-epoch window looks representative on the A10: pilot-b E [D1] s over epochs 2-21 is 140.2-140.4, against
  RUN.md's last-30-epoch mean of 138.5-138.9 (0.9-1.3 %). The Delta canaries' 2-21 windows against 82-101 differ by
  0.1 % (E s1) and 0.3-1.0 % (A07). This supports falsifier (i).

## Next verification

The A10 harness Job, which settles A1. If it runs A07 K=2 once in a 4-CPU pod and once in a 9-CPU pod, the same Job
also measures the size of A2 on the baseline card.
