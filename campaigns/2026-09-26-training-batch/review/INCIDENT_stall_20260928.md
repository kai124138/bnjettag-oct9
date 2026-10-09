# INCIDENT — pilot stall, 2026-09-28 ~01:00–01:35 UTC (`kai-chang0926-pilot-77f1ca`)

Investigator, read-only (kubectl get/describe/logs/exec-read; W&B API read). Nothing was
restarted, patched, applied or deleted. Written 2026-09-28 ~05:30 UTC. Diagnostic telemetry,
not results.

## 0. LIVE: the same stall is happening again now

At 05:22–05:23Z (in-pod reads) the 3 surviving arms have filled the pod's memory limit again:

- `/sys/fs/cgroup/memory.current` 38,653,706,240 B, `memory.max` 38,654,705,664 B (36 GiB);
  `memory.pressure full avg10=53.24`, `some avg10=77.81`.
- `nvidia-smi`: 0 % utilization, 13,263 MiB. `ps`: A-s1 (pid 25446) and A-s2 (pid 25645) in
  state `D`; RSS D-s1 17.2 GB, A-s1 10.3 GB, A-s2 10.2 GB. Load average 29.4 on 12 CPUs.
- W&B `system.proc.memory.availableMB` 40–171 MB from ~05:03Z. A-s1 epoch 148 took 362.3 s
  (its previous epochs took ~133 s).
- Last heartbeats (`activation_widths.jsonl` mtime): A-s1 05:21:10, A-s2 05:17:27, D-s1 05:16:12.
  If nothing progresses, the watchdog sweeps at ~05:46–05:51Z. A-s1 and A-s2 are on attempt 1,
  so after that sweep each has **one** attempt left. D-s1 is on attempt 0.

What to do about it is the caller's decision, not the investigator's.

## 1. Mechanism (`run_pack.py`, shipped bundle 77f1ca4e, identical to `code/tree/run_pack.py`)

- Progress = `heartbeat_age()` (l.65–68): `time.time()` minus the newest mtime of
  `runs/<arm>/latest.json` and `runs/<arm>/activation_widths.jsonl`. Only if neither file exists
  does it fall back to time since the attempt started.
  `activation_widths.jsonl` gets one fsync'd record per epoch (`ablation.py`, shipped, end of the
  epoch body), so in practice the heartbeat is "time since the last completed epoch".
  `latest.json` only changes every 25 epochs, at a checkpoint.
- Timeout: `STALL_SECONDS = 1800` (`BNJ_STALL_SECONDS`, not set in the manifest). The runner
  polls every 5 s. When an arm is stale it sends SIGTERM, then blocks in `child.wait(120)`
  before sending SIGKILL. That blocking wait is serial, so it delays the checks on the other arms.
- Retries: `RETRIES = 2` (3 attempts per arm, counted across the whole life of the pod), with a
  30 s `RETRY_DELAY` before each relaunch. This also blocks the loop.

## 2. Why four arms stalled together: the pod's memory cgroup filled (established)

**Cause.** Every arm's resident memory grows linearly, by roughly 80–95 MB per epoch. At about
00:58Z the 5 resident arms together reached the pod's 36 GiB limit
(`resources.limits.memory: 36Gi`). There is no swap, and anonymous memory cannot be reclaimed.
So the kernel evicted file-backed pages instead (Python, TF and CUDA code) and faulted them back
in over and over. Every process in the pod crawled and the GPU sat idle. This was a stall, not an
OOM: `memory.events oom_kill 0`, `max 642`.

**Evidence** (W&B `system.proc.memory.rssMB` / `availableMB`, per run; pod stdout; PVC mtimes):

| arm | RSS 20:56Z | RSS ~23:57Z | slope (MB/epoch) | RSS ~00:57Z |
| --- | --- | --- | --- | --- |
| A-s1 | 2,156 | 7,132 | ~92 | 7,982 |
| A-s2 | 2,152 | 6,865 | ~92 (2nd life 02:02→05:03: ~88) | 7,967 |
| D-s1 | 2,160 | 7,004 | ~90 | 7,995 |
| E1-s1 | 2,106 | 8,189 | ~92 | 9,363 |
| C′-s1 | 2,143 | 4,909 | ~78 | 5,019 |

- Sum at ~00:57Z ≈ 38.3 GB, against `memory.max` 38.65 GB.
- `availableMB` dropped to 713–842 at 23:57, 182–218 at 00:27, and **1 MB from 00:58:46Z**.
- The slope per epoch is about the same for every arm, whatever the model size (params 12.8k to
  31.7k) and whatever the s/epoch (132 to 310 s). The growth is a fixed amount per epoch.
- The pod log's `nvidia-smi` line shows 100 % utilization through 01:02:13Z, then **0 % from
  01:03:13Z** (99 % in a single sample at 01:19:14), with memory frozen at 21,250 MiB.
- W&B's own system-metric stream has a gap from 01:19:49 to 01:32:39 in every run, and the
  runner's 60 s `nvidia-smi` cadence stretched to 62–66 s from 01:20Z. Both are symptoms of the
  whole pod slowing down, not causes.
- Last completed epochs (W&B `_timestamp`, the jsonl mtime, and the watchdog ages give the same
  times): A-s1 printed ep.69 ≈ 01:00; A-s2 ep.69 ≈ 01:01; E1 ep.88 01:00:51.75 (jsonl mtime;
  01:00:51 + 1914 s is when it was flagged); C′ ep.47 01:01:06. After that only D-s1 finished
  anything before the kills: ep.70 at 01:19:56 (`seconds=1226.2`), ep.71 at 01:34:02
  (`seconds=845.5`). E1 got as far as saving `validation_candidate.keras` at 01:20:03, then stalled
  again.
- The kills fixed it: at 01:32:53Z the GPU was at 100 % with 4,397 MiB (D-s1 alone), and
  `availableMB` jumped to 25–28 GB at 01:33–01:35. D-s1 then ran at ~140 s/epoch.
  Freed host memory is what un-stuck it; the GPU was not the constraint.
- Counters now (cumulative since pod start, so they include the current episode):
  `workingset_refault_file` 937 M, `pgmajfault` 1.55 M, `file` 66 MB, `anon` 38.45 GB,
  `system_usec` 37 % of CPU time, `cpu.stat nr_throttled 0`.

**Other candidates, ruled out by these data:**
- *PVC/CephFS write stall:* `file_dirty 0`, `file_writeback 0`. No arm was at a checkpoint
  epoch (a multiple of 25) at ~01:00; the last checkpoints were A 0050, E1 0075, C′ 0025, D 0050.
  `/data` is 33 % full.
- *W&B sync blocking:* each `wandb-core` process has ~20 MB RSS. The W&B metric gap is a
  symptom (see above), and W&B only logs after the jsonl heartbeat has been written.
- *Node or GPU event:* the 21,250 MiB of GPU memory stayed allocated throughout, and
  utilization recovered the moment host memory was freed. The node has been up 2d21h and the pod
  has 0 restarts. Node events from 01:00Z have aged out, so this was not checked against events.
- *False positive (long trace or validation on a coincident epoch):* no. D-s1's epochs 70 and 71
  really did take 1226 s and 845 s against a normal ~212 s. The epoch after the one that triggers
  the [D20] trace is ~40 % of a normal epoch, not 30 min.
- *CPU contention:* this is the result of the thrashing, not a separate cause. There is no cgroup
  CPU throttling (`nr_throttled 0`).

**Unknown: which code allocates the ~90 MB/epoch.** Candidates, none of them confirmed:
- the per-epoch `model.save` + `keras.models.load_model(validation_candidate.keras)` +
  `predict` on a fresh model, with no `keras.backend.clear_session()`. Each reload builds a new
  predict function and graph, and TF retains it;
- `trace_minmax` on the full training split (~430 MB float32) at every epoch;
- the per-epoch `epoch_observer` probe.

A discriminating measurement: run two arms in separate pods with no memory pressure, one on
regime A (trace every epoch) and one with `ebops_trace_every: 10`. Compare the
`system.proc.memory.rssMB` slope after ~30 epochs. About 1/10 the slope in regime B means the
trace is the leak; the same slope means the validation reload path is.

## 3. Why D-s1 was untouched

D-s1 was stalled like the others, but it completed epoch 70 during the brief progress window
around 01:19Z (the 99 % GPU sample at 01:19:14). That write refreshed its heartbeat at
01:19:56, so at the 01:30–01:33 sweep its age was about 11–13 min, well under 1800 s. The other
four had last written at 01:00–01:01. Nothing protects D-s1 structurally; which arm escapes is
a matter of timing.

## 4. Retry budget: a design defect, yes (established)

- **Relaunch inherits the stale heartbeat.** `heartbeat_age` reads the same files for a new
  attempt, so a relaunched arm starts already older than `STALL_SECONDS`. E1 attempt 1 was
  launched at 01:34:28 and killed on the very next pass at 01:34:33 (01:00:51.75 + 2022 s).
  It had printed only `RUN_STAGE pilot`. Attempt 2 (`ARM_ATTEMPT 2 01:35:09Z`) was killed at
  2063 s with exit code **−15**, i.e. before `run_study.py` had even installed its SIGTERM handler.
  E1 lost two of its three attempts without running a single epoch.
- **Why A-s1 and A-s2 survived the same check:** loop-order luck. Each relaunch was followed by
  a 30 s `RETRY_DELAY` for the next arm in the loop. That gave A-s1 and A-s2 time to reach
  `restore_checkpoint`, which rewrites `activation_widths.jsonl` and copies the selected files
  (`model_unconstrained.keras` mtimes: A-s1 01:33:52, A-s2 01:34:13). Both happened before the
  next check. E1 was relaunched last and got no such delay.
- **One budget covers unrelated causes and pod-wide events.** C′-s1 spent 2 attempts on its own
  VRAM OOM (2026-09-27) and its last on this pod-wide memory stall. A stall that hits every live
  arm in one sweep is a pod-level condition. Charging it to each arm's budget, and relaunching
  into the same full cgroup, cannot succeed.

## 5. Regime-B pods and production

The regime-B pods and production would hit this too, unless the leak is the trace alone
(inferred from the arithmetic below; the leak source is not yet measured).

- Every manifest gives 6 GiB per arm: pilot 36Gi/6, `pilot-b-k3` 18Gi/3, `pilot-b-k5` 30Gi/5.
  Neither B pod is launched (`kubectl get jobs`).
- Baseline ~2.1 GB plus ~90 MB/epoch reaches 6 GiB after ~48 epochs per arm (pooled across arms
  sharing the pod). The pause at epoch 500 needs ~47 GB per arm; 7,000 epochs would need ~630 GB
  per arm.
- If the leak is the per-epoch validation reload, regime B leaks at the same rate. If it is the
  trace, regime B leaks at about a tenth of the rate: ~6.6 GB/arm at epoch 500, still over 6 GiB.
- No pilot or production configuration reaches epoch 500 under the current limits without the
  leak fixed. Raising `memory` only buys epochs linearly; it is a stopgap, not a fix.

## 6. Minimal fix, owners, mechanical checks

- **ml-engineer (code), the root fix.** Find the allocation with the measurement in §2, and stop
  per-epoch memory growth. Candidate fixes: `keras.backend.clear_session()`-safe reload, reuse of
  one validation model with `set_weights`, or releasing the trace's retained graph. Gate on a CPU
  or GPU run of ≥30 epochs where the RSS slope is ≤5 MB/epoch.
- **ml-engineer (code), `run_pack.py`.**
  - `heartbeat_age` = now − max(file mtimes, wall-clock start of the attempt).
  - Don't charge an arm's retry budget when ≥50 % of live arms are stalled in the same sweep:
    log `POD_STALL` and do not relaunch into a full cgroup.
  - Every poll, print `memory.current/memory.max` from `/sys/fs/cgroup` and each child's RSS.
    Refuse a relaunch while available memory is below one arm's RSS.
- **cluster-ops (manifest/ops).**
  - Stopgap only: memory limit, or fewer arms per pod.
  - `nrp_doctor.py lint` rule **PACK-MEM**: `limits.memory / arms-per-pod` ≥ a declared per-arm
    RSS ceiling (baseline + slope × stop-after), like the PACK GPU floor. It fails today
    (6 GiB < ~47 GB).
  - A health probe that alerts on `memory.pressure full avg60 > 10`.
- **Mechanical checks that would have caught it:** the PACK-MEM lint rule, and a
  PREFLIGHT/canary gate on the RSS slope (W&B `rssMB` epochs 1→10, fail if >5 MB/epoch). The
  epoch-10 canary data already showed ~90 MB/epoch.

## Corrections owed elsewhere (not edited here)

- RUN.md "Health check" and the `cluster-inventory.md` 2026-09-28 entry say A-s1 and A-s2
  restarted "with **no data loss**". That is wrong. Both had reached epoch 69 and rolled back to
  `epoch-0050`, so 19 epochs were replayed (~70 GPU-min each).
- On resume, W&B rejected steps 51–69 (`Tried to log to step 51 that is less than the current
  step 69/70`). W&B history for those steps is therefore the **abandoned** trajectory, while the
  PVC jsonl and checkpoints hold the replay. Anything pulled from W&B for A-s1/A-s2 epochs 51–69
  does not match the PVC.
- Both documents say the cause is "not established". It is now established: the pod's memory
  cgroup filled because of per-epoch RSS growth (§2).

Side note, not this cause: `activation_widths.jsonl` grows ~480 KB/epoch (A-s1 70 MB at
~ep.148, so ~3.4 GB at 7,000 epochs). `restore_checkpoint` reads, parses and rewrites the whole
file on every resume.

## Sources
- Pod stdout: `campaigns/2026-09-26-training-batch/logs/pilot-77f1ca-20260928T0512Z.log`, lines
  600–1195.
- Per-arm logs: `/data/chang-n64-20260926/pilot/logs/*.log`. File mtimes:
  `/data/chang-n64-20260926/pilot/runs/*/`.
- In-pod `/sys/fs/cgroup/{memory,cpu,io}.*`, `ps`, `nvidia-smi` at 05:21–05:23Z.
- W&B `BNJetTag-ChangRecipe` group `chang-n64-20260926-canary`, `history(stream='events')` and
  `scan_history(['_timestamp','epoch'])`.
- Code: the shipped bundle extracted from `manifests/configmap-77f1ca4e.json`
  (sha256 77f1ca4e…a94, verified). `run_pack.py` in it is identical to `code/tree`. `ablation.py`
  and the configs in `code/tree` have since been modified (regime B), so all line references
  here are to the shipped copy.
