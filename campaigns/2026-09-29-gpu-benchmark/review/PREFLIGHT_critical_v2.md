# PREFLIGHT critical review v2 — 2026-09-29-gpu-benchmark (solo gate, scoped to the v1 findings)

Reviewer: critical-reviewer (solo mode). Date: 2026-09-29 02:25 PDT (09:25Z).

**Scope (the brief).** This gate asks two things:
- whether fixer v1 resolved the v1 findings: A1, A2, B1-B6, and the C items the fixer claims (C3, C5, C6, C7; C4 noted);
- whether the fixes introduced a new Category A.

Settled items were not re-reviewed.

**Read:**
- `STUDY.md` (Amendment 1);
- `PREFLIGHT.md` (the build half and "Fixer v1 rebuild");
- `code/`: `bench_driver.py` 5ede0778…, `gen_bench.py`, `bench_summary.py`, `test_bench.py`, `plan_check.py`, `cpu_gate_bench.sh`;
- `code/evidence/`;
- the 16 `manifests/kai-gpubench-*-{krule,klow}.json`, `configmap-bench-driver-5ede0778.json` and `bench_plan.json`;
- the two 2026-09-29 entries at the top of `decisions.md`.

Everything below is telemetry or arithmetic, never a result.

**VERDICT: PASS.** All v1 A and B findings are resolved except v1 B5. The fixes introduce no new Category A.

The launch bundle is sound:
- the driver, the 16 manifests and the ConfigMap regenerate byte-identical;
- the compute path is unchanged;
- the yield rule's selector matches the live pilot pods.

Six B items remain. Each is tied to the step before which it should be done:

| step | items |
| --- | --- |
| at the first apply | B2 (stage the apply; read the sampler) |
| before either A10 Job is applied | B3 (a defined outcome if the A10 measurement is lost), B4 (a live watcher) |
| before any apply | B5 (the NRP 40 % floor, estimated or accepted on record) |
| before `bench_summary.py` runs on any benchmark data | B1 (the rule-5 thread-mask filter), B6 (the baseline anchor) |

B1's fix is specified below. It can therefore be applied before any result is read, and the pre-registration stays intact.

## Checked, and recomputed

**The driver and the ConfigMap.**
- **Driver sha.** `5ede0778f716…c45` is the same in four places: `code/bench_driver.py`, the ConfigMap manifest payload, the live ConfigMap's `data['bench_driver.py']` (hashed from `kubectl get configmap kai-gpubench-driver-5ede0778f7 -o json` at 09:05Z; `immutable: true`) and the live annotation.
- **Driver diff, v1 (`4d2dcd7d`, extracted from `manifests/superseded-v1/`) → v2.** The arm path gained only the pin prelude and the stub exit (`bench_driver.py:266-271`). Everything else is additive: the CPU helpers, the sampler fields, the per-phase CPU record, and `classify` by exit code.

**The CPU gate, arm A s1** (`cpu_gate_arm_a-s1.log` against `v1/cpu_gate_arm_a-s1.log`; synthetic cache, CPU, not quotable). The logged values are identical in both logs:

| epoch | EBOPs | above_floor | val_AUC | val_accuracy | loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 9,605,779 | 9,434,253 | 0.508496 | 0.210484 | 2.581331 |
| 2 | `in_training_ebops` 9,681,043 | — | 0.484001 | 0.197581 | 2.572640 |

Two fields differ, and the PREFLIGHT claims neither equal:
- `checkpoint_sha256`: `8f9d8cac…` (v1) against `36bfbf77…` (v2);
- `host_rss_mb`: 998 / 1,757 (v1) against 1,398 / 1,864 (v2).

**Tests and regeneration.**
- `test_bench.py`, my re-run: `ALL_PASS 21 SKIPPED 1 (test_pinning_k2_phase_arms_see_4_cpus)`.
- `gen_bench.py --survey node_survey_20260929T073945Z.json`, re-run in a scratch mirror of the repo: all 18 files come out **byte-identical** (`cmp`): the 16 Jobs, `bench_plan.json` and the ConfigMap.

**All 16 manifests, parsed.** Every one passes:
- requests equal limits, at 2 CPU and 8 Gi × K_max;
- the pod deadline equals my recomputation from `gen_bench.py:149-153` (e.g. A10 K_rule raw 14,190 s → 14,400; A10 K_low 10,380 → 10,800; A100 K_rule 45,960 → 46,200);
- the Job deadline is 21,600 s plus the pod deadline;
- `backoffLimit` 0, no `podFailurePolicy`, `restartPolicy: Never`;
- the four hostname exclusions, the product pin and the required anti-affinity;
- the driver sha is checked in the pod script;
- the thread-environment line is identical in all 16, and equal to `pilot-b-k5-job.json`'s: `export OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 OPENBLAS_NUM_THREADS=1`;
- `bnjettag.io/yield-to-anchor` appears on the two A10 Jobs only.

**Runtime arithmetic, recomputed.**
- Aggregate bound: 97,692 s, or 27.14 GPU-h.
- Larger bound per Job: 32.88 GPU-h.
- With the header allowance: 40.88 GPU-h.
- Arm-runs: 141.

All four equal `runtime_arithmetic.log` and STUDY l. 95-98.

**The A10 cross-check** (`a10_baseline_summary.json` and `a10_offset50_summary.json`, v1 against v2). There are 0 value differences on 10 keys × 7 rows in both windows; E `s_d1` is 140.36 and A07 132.48.

**B1 on a real object.** `bench_summary.pod_facts` on the finished pod `kai-batch0917-screen-e100-r3-0-94g6w`, taken from `campaigns/2026-09-20-status/cluster.json` (Ready False, PodCompleted), gives `pod_created_to_running_seconds` 22.0 through `containerStatuses.startedAt`. The test fixture (`COMPLETED_POD`) is a faithful transcription of that pod.

**Live cluster, read-only (09:03Z).**
- `kai-chang0926-pilotb3-42abed-0-vqxc7` is Running on gpu-17 (app `kai-chang0926-pilot-b3`).
- `kai-chang0926-pilotb5-42abed-0-qqjmt` is Running on c5805 (app `kai-chang0926-pilot-b5`).
- The yield rule's exact command returns no rows.
- `kubectl get jobs -l campaign=gpu-bench-20260929` gives "No resources found": nothing has been launched.

**Survey.** Every A10 node has 7-8 GPUs and 124 allocatable CPUs. The two pilot nodes, c5805 and gpu-17, are schedulable for the A10 Jobs.

## Validator output

- **`nrp_doctor.py lint`.** I read the saved build log `code/evidence/lint_gpubench_build.log` (08:33:13Z) and did not re-run it, because it queries the cluster. It shows:
  - 0 ERROR;
  - 12 × `WARN   required pool = 1 products / <n> nodes cluster-wide  <-- narrow; expect queueing`;
  - 4 × `OK` (both A10 Jobs, both 3090 Jobs);
  - `rc=1`.

  The WARN is answered by the narrow-pool exception for a controlled timing comparison (`decisions.md` 2026-09-29). **No red flag.**
- **`test_bench.py`:** `ALL_PASS 21 SKIPPED 1` (my re-run).
- **`plan_check.log`:** 16 × `PLAN_OK`, then `PLAN_CHECK_ALL_OK` and `GENERATOR_IDEMPOTENT`. I did not re-run `plan_check.py` in place, because it rewrites `manifests/`. The scratch regeneration above is the independent check.
- **`plot_check.py` and `prose_lint.py`:** not applicable (a PREFLIGHT, with no figure).

## The v1 findings, by name

| v1 | status | evidence |
| --- | --- | --- |
| A1 (A10 unmatched) | **Resolved.** The A10 runs in the same harness at [D2]'s K. Residue: B3, B6 | Jobs `kai-gpubench-a10-{krule,klow}` (E 4/3, A07 2/1). The A10 K_rule pod has the same shape as every candidate's K_low pod: 8 CPU / 32 Gi, E at K=4. Its A07 K=2 matches the 46-80 GB cards' K_low; the 24 GB cards' K_low A07 is K=1. STUDY Am. 1 l. 137-139; the Check is relabelled (l. 56-57); [L2] is on the [D1] basis (l. 122-126) |
| A2 (CPU per arm) | **Resolved.** Two Jobs per product, each phase pinned to 2K CPUs, rule 5. The rule-5 thread check has a start-up race: B1 | `gen_bench.py:167-185`, `bench_driver.py:183-217, 677-696`; STUDY l. 71-72 |
| B1 (Q is None) | **Resolved** | `bench_summary.py:289-299`; 22.0 s on the real pod (above) |
| B2 (outcomes, completion) | **Resolved.** Edge case: C1 | `bench_driver.py:642-657`; `bench_summary.py:201-207, 436-438`; tests `classify_exit_codes_win`, `pool_completion_against_stop_after` |
| B3 (verification FAIL) | **Resolved** | STUDY rule 6 (l. 73-74); `bench_summary.py:465-472`, applied across both Job directories |
| B4 (node CPU) | **Resolved** | `gen_bench.py:254-260` (`CPU_MODEL`, `CPU_COUNTS`, `LSCPU`, `HOST_MEM`); `bench_driver.py:684, 763-766` (`POD_CPUS`, physical cores) |
| B5 (NRP 40 % floor) | **Not resolved; carried as B5** | the premise is contradicted by the setup doc (B5) |
| B6 (rule 3 on the K_max shape) | **Resolved** | the K_low pods request 8 CPU (6 on the A10); [D6] is judged per Job shape (annotation `not-practical-after`, Open item 4) |
| C3, C6 | **Resolved** | `bench_summary.py:276-286, 340-342, 461-464`; the test uses a discriminating order |
| C5 | **Resolved** | the build reads the 07:39:45Z survey; regeneration is byte-identical |
| C7 | **Resolved** | STUDY rule 3 (l. 66-67) checks end times at apply |
| C4 | **Noted** | quota 23/24 at 08:41Z; Open item 2 re-checks it at launch |
| C1, C2 | not claimed; not re-reviewed | — |

## The brief's six checks

**1. Does the pinning code pin what it claims, including on a static-CPU-manager node? Yes.**
- **Where the allowed set comes from.** `allowed_cpus()` (`bench_driver.py:168-180`) reads `os.sched_getaffinity(0)` of the pod driver, which is PID 1 after `exec`. Every Job is Guaranteed: requests equal limits at integer CPU, with one container and no init container (plan_check `shape`). On a static-CPU-manager node the container therefore gets an exclusive cpuset, and that set is what the driver reads.
- **How the pin is taken.**
  - `phase_cpus` (`:183-185`) takes the first 2K CPUs of that set.
  - `pin_self` (`:200-217`) calls `sched_setaffinity(0, …)` before any bundle import (`:266-268`).
  - It re-reads the kernel's mask and fails closed: any difference, or an `OSError`, gives exit 14 before the bundle is imported.
- **On a static node.** A subset of the container's cpuset is always a legal mask. `test_cpu_list_and_phase_selection` covers an allowed set that does not start at 0: {2-5, 8, 10-11} → {2, 3, 4, 5}.
- **Thread inheritance.** At the moment of the pin the arm has only its main thread, because only stdlib modules have been imported. Every later TF, CUDA-driver and OpenBLAS thread therefore inherits the mask. The sampler's per-thread union (`:220-236, 497-505`) is the check on that.
- **Telling the node types apart.** The `POD_CPUS` line (allowed_n against pod_cpu_request) distinguishes a static-manager node from a shared-pool node.
- **What has never been run.** The Linux kernel path has not executed anywhere. The CPU gate ran on Darwin (`ARM_CPUS unavailable`, `cpu_gate_pod.log`), and the kernel test is skipped. See "Route (b)" below.

**2. Do the arms of a phase keep pilot-b's thread environment? Yes.**
- The header line is byte-identical to pilot-b-k5's (`gen_bench.py:230`).
- `launch` (`bench_driver.py:591-608`) passes no `env=`, and pod mode never edits `os.environ`, so every arm inherits the header's values.
- The v1→v2 pod-script diff adds only the four CPU/RAM header lines and the new driver sha.
- The K arms share the same 2K CPUs, which is the same budget as pilot-b's 2K-CPU CFS quota.

**3. Did anything in the compute path change? No.** See the driver diff and the epoch values above.

**4. Can the A10 Jobs compete with a Pending pilot pod unnoticed? At apply, no. Afterwards, only as long as someone is watching.**
- **The selector is right.** All eight pilot-b pod templates carry `campaign=chang-n64-20260926`, with `app` set to `kai-chang0926-pilot-b3`, `-b5`, `-bfb16`, `-bfb32`, `-bfb48`, `-bfb16-32`, `-bfb48-16` or `-bfb48-32`. All eight match the rule's prefix `kai-chang0926-pilot-b`. Matching on APP is correct: the Job and pod names are `kai-chang0926-pilotb…`, without the hyphen, and would not match.
- **The readout Jobs cannot compete.** They request no GPU.
- **After apply, detection is not bounded:** see B4.

**5. Do the deadlines and runtimes hold for each Job shape? Yes, apart from the NRP window (B5).**
- **Per phase.** Each phase's deadline allowance exceeds the per-process bound of 21 × 140 = 2,940 s. The smallest allowance is A07 at K=1: 21 × 44 × 2.5 + 15 + 900 = 3,225 s.
- **Per Job.** The pod deadline is 1.4-2.5 × the upper runtime bound with header. The extremes are the A10 K_low Job (3.00 h against 2.13 h) and the A100 K_rule Job (12.83 h against 5.17 h).
- **The A100 pair** runs in sequence, and the K_low Job's [D6] clock starts at its own apply.

**6. Do summary rules 1-6 compute what the STUDY pre-registers?**
- **Rule 1: yes.** An OOM is the exit-7 outcome (`bench_summary.py:432-433`). A non-finite loss or `diverged` counts (`:434`). The pod peak above 90 % is taken over all samples of the phase (`:263`). "Both K excluded drops the class" is left to the REPORT.
- **Rule 2: yes.** A mismatching pod log in either Job directory excludes every row of the product (`:458-470`). A pod stopped by the gate still produces a row (`:402-407`).
- **Rule 3: yes.** A planned Job with no data is listed (`:476-483`); the 6-h deletion itself is manual.
- **Rule 4:** outside the summary, as the STUDY intends.
- **Rule 5: yes for the STUDY's two conditions** (`:372-376, 379-380, 440-441`). The added thread-mask test (`:377-378`) has a start-up race (B1), and a phase without `phase_result.json` skips the pin checks (C1).
- **Rule 6: yes.** Any FAIL, in either directory, excludes the product (`:465-472`), and the FAIL text is kept.
- **[D1] s and R:** as in v1, except that R now needs every arm at `stop_after` (`:201-207`).

## Route (b), the kernel-level pinning test on the first pod: adequate, on two conditions

The skipped Linux test (`test_pinning_k2_phase_arms_see_4_cpus`, `test_bench.py:382-398`) is weaker than it looks:
- It drives `--test-arm-stub` arms, which exit right after `ARM_CPUS` without importing the bundle (`bench_driver.py:269-271`).
- Even on Linux, route (a) would show only the main thread's mask, never that the TF and CUDA-driver threads inherit it.

The first real pod shows both:
- `ARM_CPUS n=<2K> … OK` in every arm log;
- the sampler's per-thread `proc_cpus_allowed`.

The failure mode is also closed:
- A mask mismatch exits 14 before any import (`bench_driver.py:267-268`).
- Rule 5 keeps an unconfirmed phase out of T.

Route (b) is therefore the stronger check. It needs the two conditions in B2: stage the apply, and read the sampler as well as the logs.

## Category A (must resolve)

None.

## Category B (should address)

**B1. Rule 5's thread-mask check can fire on a start-up race, not only on a pin failure.**
`bench_summary.py:254-255, 271, 377-378`; STUDY l. 71-72; fixture `test_bench.py:489-496`.

*Mechanism.*
- **The check.** `samples_for` builds a union over every `proc` row of the phase (`:254-255`). A union that leaves the pinned list sets `threads_within_pinned` to False (`:271`), and the phase is then excluded as "rule 5: an arm thread ran outside the pinned CPUs; out of T" (`:377-378`).
- **The sampler's order.** Each sample runs in this order:
  - it snapshots the arm list and computes `live` (`bench_driver.py:476-479`);
  - it calls `nvidia-smi` twice (`:484, 494`) and scans /proc (`:495`);
  - only then does it read each live arm's thread masks (`:500`).
- **The arm's order.** An arm is in the list from `Popen` onward (`:607, 697-699`), but it pins itself only after interpreter start-up, argument parsing and its stdlib imports (`:264-268`).

*The race.* An arm is recorded before its pin only when its start-to-pin time w is longer than δ, the sampler's own lag between the snapshot and the mask read. The phase is then excluded even though:
- every arm printed `ARM_CPUS … OK`;
- cores ÷ K stayed at or under 2.1.

That meets neither of the STUDY's rule-5 conditions. The fixture holds only rows that are already pinned (`test_bench.py:495`), so no test can catch this.

*Size* (arithmetic; neither w nor δ has been measured in a pod):
- **w.** Here, from `Popen` returning to the `ARM_CPUS` line, it measured 21 ms (median of 15 runs; Apple silicon, warm caches). In a pod it is plausibly 40-100 ms, for three reasons:
  - the arm recompiles `bench_driver.py` on every start, because it runs as `__main__`, for which Python writes no bytecode;
  - the pod runs on x86;
  - the arms already running add CPU load.
- **δ.** Two `nvidia-smi` subprocesses plus the /proc scan take plausibly 40-300 ms.
- **The effective window** is max(0, w − δ), so the realistic risk is probably near zero.
- **Upper bounds** (δ = 0), with 60-s sampling over the 141 arm-runs:

| w | chance of ≥ 1 false exclusion (upper bound) |
| ---: | ---: |
| 21 ms | about 5 % |
| 40 ms | about 9 % |
| 100 ms | about 21 % |

These bound the risk from above; they are not estimates of it.

*Why B, not A.*
- It cannot affect data collection.
- Its fix is summary-only and specified here, so it can go in before any result is read.
- What keeps it from C: it is a check beyond the STUDY's rule-5 text, it can exclude a valid phase under a label that asserts a pin failure, and its misfire rate depends on node latencies that nobody has measured.

**`bench_summary.py` must not run on benchmark data until the filter and its test are in.**

*Fix* (summary only; `bench_summary.py` is not in the ConfigMap):
- In `samples_for`, count only `proc` rows with `proc_epochs_done ≥ 1`, i.e. arms that have finished epoch 1, long after `pin_self`. Rows in the steady window only would also do.
- Add a test whose fixture has one pre-pin row (the whole allowed set, `proc_epochs_done` 0) that must not exclude the phase.

No driver, manifest, ConfigMap, lint or dry-run change follows.

**B2. Route (b) needs a staged apply and a sampler read.**
PREFLIGHT l. 529-531 (Open item 6) and l. 904-938 (the apply block).

*Stage the apply.*
- The apply block creates 14 Jobs back to back, but the pin is checked only "on the first phase of the first pod".
- If the Linux path fails, every pod spends its header before its arms exit 14. The header covers pip install and the fingerprint gate; its allowance is 1,800 s.
- The fix: apply the first Job alone (#1, the 3090 K_low). Confirm the pin on its first phase, then apply the rest.

*Read the sampler, not only the logs.*
- `ARM_CPUS` shows only the main thread's mask.
- Add to Open item 6: after about 5 min of the first phase, read `samples.csv` rows with `kind=proc` and `proc_epochs_done ≥ 1`.
- Check two columns: `proc_cpus_allowed` lies within the phase's pinned list, and `proc_threads` is well above 1. That shows TF's threads exist and inherited the mask. The epoch filter avoids misreading B1's pre-pin rows as a failure.

**B3. No pre-registered outcome if the A10 measurement is cut short or lost.**
STUDY Am. 1 l. 137-139; PREFLIGHT l. 522-528 (Open item 5), l. 917 and l. 935-937.

The situation:
- The yield rule deletes an A10 Job whenever a pilot-b pod is Pending.
- The A10 Jobs are applied last, so candidate data will already exist when any of the choices below is made.

Four things are not pre-registered:
- how many times, and until when, a deleted A10 Job is re-run (Open item 5 says only "re-run later only from a moved-aside root");
- which attempt counts when a deleted attempt completed some phases. Both copies carry the plan slug `a10-krule`, and `summarize_bench` would then emit two rows for one phase;
- how rule 6 treats arms stopped during `verify_selected` (their verification is `none`, and see C1);
- what the headline question becomes if no A10 phase completes at a K by decision time.

v1 A1 asked that T(A10) be fixed by rule before any candidate number exists; each of these is a later choice.

The fix is one STUDY line before either A10 Job is applied, for example:
- a deleted A10 Job is re-run in full from a fresh root until a stated time;
- only a complete run counts, and a deleted attempt's complete phases are a cross-check;
- with no complete A10 phase at a K, the question is reported unanswered at that K and goes to Kai;
- the [L2] telemetry is never promoted to the baseline.

**B4. After apply, the yield rule depends on a watcher that nothing specifies.**
PREFLIGHT l. 522-528; the Job annotation (`gen_bench.py:104-108`).

- **The gap.** Enforcement is "at every watcher poll", but no cadence or owner is stated, and nothing requires a watcher to be running. The pods cannot check for themselves (`automountServiceAccountToken: False`).
- **The existing watcher.** The pilots' 150-s watcher was for the `RSS_GATE` lines (training-batch RUN.md l. 947). All eight of those verdicts are already in (l. 1002).
- **The fix.** Make a live watcher session a precondition of applying either A10 Job. State its cadence (the pilots' 150 s would do) and log each poll in RUN.md. Delete both A10 Jobs if the watcher stops.
- **When the rule becomes moot.** The K=3 pilot Job is terminal at about 18:15Z 09-29 and the K=5 Job at about 07:05Z 09-30 (RUN.md l. 975). After that the rule no longer applies.

**B5. v1 B5 carried: the NRP 40 % floor rests on a premise the lab's own doc does not support.**

The two texts:
- PREFLIGHT l. 274-275: "The brief's premise, that every Job runs under 3 h so NRP's rolling 3-h 40 % window mostly does not apply, holds for 11 of the 16 at the throughput bound."
- `docs/infrastructure/nrp-nautilus-setup.md:281-283`: "NRP requires a pod holding a GPU to average **above 40% GPU utilization**; the alert looks back 3 hours (so pip-install startup counts against you), deletion by admins is a recorded violation, and three violations flag the account."

Why the premise matters more after the split:
- Every K_low pod now holds only low-K phases (E at 4, or 3 on the A10; A07 at 2 or 1) plus the header.
- On cards faster than the A10, the header is a larger share of a shorter pod.

STUDY Am. 1 (l. 147-148) answers only the selection side: a phase under 40 % is a finding, not an exclusion. It does not answer the account side.

The fix, one of:
- a per-Job-shape estimate of the pod-lifetime mean (the header at about 0 %, plus the phases);
- an explicit accepted-risk line that names the three-violation policy, with cluster-ops watching for the NRP mail.

**B6. Nothing checks the pinned harness against production on the baseline.**
PREFLIGHT l. 54-56 and Alignment 11 (l. 473-475); STUDY l. 91-93 and l. 122-126.

**The gap.**
- Pinning is a second departure from production, and its direction is not established.
- For the chosen product, falsifier (ii) compares the production-shaped canary with the screen.
- For the A10, the comparator of the headline, nothing does. [L2] displays the pilot and Delta telemetry beside the harness, but sets no consequence if they disagree.

**Why a check is possible at no cost.** The Delta pure-pack canaries use the same card, class and K as the A10 K_rule phases: [D1] s is 111.5-114.5 s for E-k4 and 90.4-90.7 s for A07-k2. They also carry extra load (W&B on, and Delta's always-on diagnostics). So the pinned harness should not come out slower.

**Fix.** Pre-register a one-sided check before any A10 number is read:
- **The test.** The A10 harness [D1] s is compared with the slowest Delta arm: at E K=4, a harness s more than 10 % above 114.45 s; at A07 K=2, more than 10 % above 90.73 s.
- **If it fires,** the baseline's pinned measurement is flagged, and the headline comparison goes to Kai with both readings.

It costs no GPU time.

## Category C (suggestions)

- **C1.** A phase can lack `phase_result.json` while every arm logged 21 epochs, for example when a deletion or the deadline lands during the last arm's `verify_selected`; the A10 yield makes this likelier. R is then still given, `cpu_pin` is None, and the pin checks at `bench_summary.py:375-380` are skipped. Read `ARM_CPUS` from the arm logs whether or not the file exists, or give no R without it.
- **C2.** STUDY l. 43 says "2 CPU and 8 GiB per arm …, enforced in every phase by pinning". Pinning enforces CPU only.
  - Memory per arm in the smaller phase of each Job is 8 × K_max / K Gi: 18 Gi for A07 at K=4 in the 72 Gi L40 K_rule pod, and 24 Gi for A07 at K=1 in the A10 K_low pod.
  - This is unlikely to change s, since the cache moves to the GPU once, but the sentence overstates what is enforced.
- **C3.** STUDY l. 147-148 labels "the rest 2.13 h" as the throughput bound with header. It is in fact the per-process bound (1.63 h) plus the header. At the throughput bound with header, the A10 K_low Job is 1.25 h and the 24 GB K_low Jobs 1.41 h.
- **C4.** Two items are marked open but are now decided (`decisions.md` 2026-09-29):
  - the anti-affinity is still called "pending the orchestrator" (STUDY l. 142; PREFLIGHT l. 17, 343, 472, 480-486);
  - the route flag is still raised (PREFLIGHT l. 492-496).
- **C5.** The A10 Jobs can land on the pilot nodes, since c5805 and gpu-17 are schedulable 8-GPU, 124-CPU nodes. While the pilots run, a `NotIn` for those two nodes keeps pinned benchmark arms off the anchor's nodes and keeps falsifier (i)'s later pilot windows free of benchmark load. It costs 2 of 30 nodes.
- **C6.** Rule 5 checks only the upper side.
  - **The gap.** On a shared-pool node the pinned CPUs are the node's lowest-numbered ones, and they cannot shed a neighbour's load, so a busy node can starve a phase without any flag.
  - **The fix.** cgroup v2 `cpu.pressure`, or per-arm `/proc/<pid>/schedstat` run delay, in the sampler would show it; that is a driver change. Otherwise, name the effect and its direction under [L1]: a contended node makes a product look slower.
- **C7.** With the anti-affinity, a Job whose sibling holds the product's only free node waits for that node; L40S and A40 each have two schedulable nodes. Such a Q is partly self-inflicted. Label it if the benchmark's Q is ever used in place of the probe's Q_p.
- **C8.** The ml-engineer entry of 2026-09-29 in `decisions.md` says "The exception ends when the seven Jobs are deleted"; there are 16. Append a dated correction, since the log is append-only.

## The competing-group question

A group running the same benchmark next month would have four things we do not:
- **The baseline and candidates under production CPU placement,** or a measured tie between the pinned and the unpinned readings.
  - Pinning is the orchestrator's decision, and it halves the Job count.
  - B6 provides the tie on the baseline at no GPU cost.
- **More than one node per pod shape.** This is disclosed as [L1] and justified by the 10 % tie rule.
- **Contention telemetry on the pinned cores** (C6).
- **A defined outcome if the baseline is lost** (B3).

With B3 and B6 in place, nothing unjustified remains.

## Solid

- **The launch bundle as it stands:**
  - driver 5ede0778, identical in the file, the ConfigMap manifest and the live payload;
  - the 16 Jobs and `bench_plan.json`, byte-identical from the 07:39:45Z survey;
  - lint with 0 ERROR, and 16 server dry-runs (as recorded).
- **The compute path is unchanged** (identical EBOPs, AUC and loss).
- **The A10 is in the same harness at [D2]'s K,** with the same pod shape as the candidates' K_low Jobs.
- **The yield selector** is verified against the live pilot pods.
- **Q from apply** works on a real finished pod.

## Next verification

Apply `kai-gpubench-geforce-rtx-3090-klow` alone (B2). On its first phase, read:
- `ARM_CPUS n=8 … OK` in all four arm logs;
- `samples.csv` `proc_cpus_allowed` within `pinned`, on rows with `proc_epochs_done ≥ 1`.

Then apply the rest.

Before `bench_summary.py` runs on benchmark data, a scoped check of B1's filter and its test.
