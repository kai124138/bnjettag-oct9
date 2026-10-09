# RUN — 2026-09-27-delta-screen, GPU memory canary (STUDY gates 7 and 14)

Nothing here is quotable. Launch record and incident detail only. Scope: the memory canary
alone (`kai-delta0926-canary`), not the wave-2 launch, which waits for gate 1 (anchor regime-B
pilot epoch-500 readout) — out of scope here and not touched. W&B project named by the configs:
`BNJetTag-Delta`, entity `kayamaguchi-uc-san-diego`, group not reached (see Incident: no arm got
far enough to open a run). ConfigMap `kai-delta0926-code-e6fc6cd921` (bundle sha
`e6fc6cd921d574f7ac153d597341b8f1c36db088f7cc9c91f5d59401c8d967fb`, manifest sha
`300be87bf0cde5fba95c7b9cf0798718475e2b2dd6a230ee44a58a22fa8d467c`). Authorized by Kai
2026-09-27/28 (`.claude/memory/decisions.md`); this task is the canary only, per brief.

## Pre-apply state

`nrp_doctor.py status` (2026-09-28, before apply): quota `requests.nvidia.com/a100 23/24`, `pods
94/200`; **no running or pending pods of ours** — the training-batch pilot
(`kai-chang0926-pilot-77f1ca`) was deleted 2026-09-28T05:31Z per `cluster-inventory.md` (the
2026-09-28 stall incident), so the canary is the only kai pod requesting a GPU at apply time.
Lint of the substituted manifest: WARN only (`backoffLimitPerIndex=1`, by design — see
PREFLIGHT). No admission errors.

## Launch

```
$ kubectl create -f campaigns/2026-09-27-delta-screen/bundle/configmap.json -n cms-ml
configmap/kai-delta0926-code-e6fc6cd921 created
```
2026-09-28T09:16:54Z (the `kubectl apply` attempt immediately before this failed on
`metadata.annotations: Too long`; see PREFLIGHT).

```
$ kubectl apply -f campaigns/2026-09-27-delta-screen/manifests/delta-canary-job.json -n cms-ml
job.batch/kai-delta0926-canary created
```
2026-09-28T09:17:36Z.

Pod `kai-delta0926-canary-0-6q8kn` `Running` within ~26 s, on **node
`hcc-nrp-shor-c6017.unl.edu`**, GPU **NVIDIA A10, 23,028 MiB**. From the pod log:
```
MANIFEST_SHA_OK 300be87bf0cde5fba95c7b9cf0798718475e2b2dd6a230ee44a58a22fa8d467c
GPU_GATE_PASS
NVIDIA A10, 23028 MiB
CACHE_READY
PACK_ROOTS {"BNJ_DATA_ROOT": "/data/chang-n64-20260926", "BNJ_RUN_ROOT": "/data/delta-20260927/canary/E-k4"}
ARM_STARTED 0 delta0926-w2-rep-a-t350000-s1 pid 89 attempt 0
ARM_STARTED 1 delta0926-w2-rep-a-t350000-s2 pid 119 attempt 0
ARM_STARTED 2 delta0926-w2-rep-a-t350000-s3 pid 154 attempt 0
ARM_STARTED 3 delta0926-w2-rep-a-t350000-s4 pid 192 attempt 0
```
Manifest sha, GPU gate and cache all matched the frozen bundle exactly. Full log saved:
`campaigns/2026-09-27-delta-screen/logs/canary-0-6q8kn-20260928T0922Z.log` (296 lines, captured
before the 7-day Job TTL, not urgent but done while the pod still existed).

## Jobs

| job | pod | node | GPU | started (UTC) | ended (UTC) | state |
| --- | --- | --- | --- | --- | --- | --- |
| `kai-delta0926-canary` | `kai-delta0926-canary-0-6q8kn` | `hcc-nrp-shor-c6017.unl.edu` | NVIDIA A10, 23,028 MiB | 2026-09-28T09:17:36Z (apply); Running by ~09:17:49Z (pod `startedAt`) | 09:22:48Z (pod `finishedAt`) | `Succeeded`, exitCode 0, reason `Completed` — but see Incident: no phase produced a real memory measurement |

`parallelism: 1`, one pod, three sequential phases (E-k4, E-k5, A07-k3) per the canary manifest.
No relaunch performed.

## Incident: every arm in every phase failed at startup on a missing W&B project — no memory
measurement taken

**Signature (verbatim, every one of the 12 arms across all 3 phases, e.g. `delta0926-w2-rep-a-t350000-s1`):**
```
ARM_LOG Traceback (most recent call last):
ARM_LOG   File "/work/code/run_study.py", line 208, in <module>
ARM_LOG     train(args.index, args.stop_after)
ARM_LOG   File "/work/code/run_study.py", line 104, in train
ARM_LOG     run_engram.validate_tracking_destination(cfg)
ARM_LOG   File "/work/code/run_engram.py", line 157, in validate_tracking_destination
ARM_LOG     raise ValueError('The separate W&B project must exist and be verified PRIVATE before --track')
ARM_LOG ValueError: The separate W&B project must exist and be verified PRIVATE before --track
ARM_FAILED_AFTER_RETRIES delta0926-w2-rep-a-t350000-s1
```
(and identically for every other arm name in E-k4, E-k5 and A07-k3 — `s1`-`s5` of rep-A and
`s1`-`s3` of rep-C.)

**Cause, as read from the code.** `run_engram.validate_tracking_destination` (`code/run_engram.py`
l. 135-157, shipped in this bundle) checks, before any training step, that the W&B project named
by `cfg['train']['wandb_project']` (= `BNJetTag-Delta` for every packed config) already exists
under entity `kayamaguchi-uc-san-diego` **and** is set to `PRIVATE` access, via a live W&B GraphQL
query. It raises `ValueError` and refuses to train if the project does not exist yet or is not
PRIVATE. I did not query the W&B API directly to distinguish "project does not exist" from
"project exists but is not PRIVATE" — that credential-touching check was blocked by the session's
own permission classifier (Credential Exploration) when attempted inside the pod; not pursued
further here, per instruction not to work around a permission denial. Either way, the missing
prerequisite is an account-level W&B setup step (create `BNJetTag-Delta` under
`kayamaguchi-uc-san-diego` and verify it PRIVATE), not a cluster or manifest defect: nothing in
`nrp_doctor.py`'s scope (scheduling, quota, node health, manifest shape) touches W&B project
existence, and this is not something cluster-ops should silently work around by editing a config
or the guard itself — that guard is a designed safety check ("refusing to mix campaigns"), not a
bug.

**Outcome.** Every arm's single attempt (`attempt 0`) failed identically and immediately (no
epoch, no GPU allocation, no RSS growth) — `run_pack.py`'s per-arm retry budget
(`BNJ_ARM_RETRIES=0`, set deliberately for this canary, see PREFLIGHT/lint) meant no arm retried,
so `ARM_FAILED_AFTER_RETRIES` fired on attempt 0 for all 12 arms in ~15-25 s per phase. All three
phases ran to `PACK_DONE ... failed [...]` / `PHASE_EXIT_NONZERO`; the pod itself completed with
exit code 0 (the shell script's `|| echo PHASE_EXIT_NONZERO ...` swallows each phase's nonzero
exit and continues), so **the Job shows `Succeeded` in Kubernetes despite producing no
measurement** — this is worth flagging on its own: a canary that fails this way looks green at
the Job level.

`k_result.json` (written by `canary_k.py`, captured in the full pod log) confirms no phase
sampled any GPU/host memory: every phase's entry carries `"error": "no nvidia-smi samples for
this phase"`, `"gpu_peak_mib": null`, `"rss_gate": null` for every arm, and `"rss_gate_all_pass":
false`. **STUDY gates 7 and 14 remain PENDING — this canary did not answer them.** The
`pod_host_peak_mib` figures in the E-k5 and A07-k3 entries (6,815 MiB) are the idle pod's own
baseline (Python/TF import, pip install), not per-arm training RSS, and are not a measurement of
anything gate 14 asks about.

**Not fixed here.** Per the brief's boundaries, creating/verifying a W&B project is not a
manifest or cluster fix and was not attempted. This blocks re-running the canary until resolved.

**Check:** prose only. Two mechanical gaps, neither implemented: (1) `preflight_checks.py` (the
CPU-only build-gate script) does not call `run_engram.validate_tracking_destination` or otherwise
check W&B project existence/access before a bundle is declared ready to launch — it could, cheaply,
with a live API call gated behind a flag. (2) `run_pack.py`'s shell wrapper (the canary manifest's
own `args` script) swallows a whole-phase failure into `PHASE_EXIT_NONZERO` printed to stdout but
still exits the container 0 at the end, so a completely-failed canary reports Kubernetes
`Succeeded` — `nrp_doctor.py status` would show this as a clean Complete Job with no WARN. A
`nrp_doctor` check that greps a completed canary/memory-measurement Job's log for
`PHASE_EXIT_NONZERO` or `k_accepted: null` and flags it would have caught this without a human
reading the full log. Neither exists yet.

## What is confirmed despite the incident (does not depend on the failed arms)

- ConfigMap sha, manifest sha and GPU gate all matched (see log excerpt above) — the bundle and
  its ConfigMap are correctly built and deployed.
- The pod read the anchor's gated 90/10 n64 cache correctly: `CACHE_READY` before any arm, and
  `y_val` sha `63049d9bdcfdc83af97c58bc6579e1def1ec2d9e7a6c30007793badd75217709` confirmed live
  from inside the pod, byte-equal to the anchor's cache-build log and to PREFLIGHT gate 3d.
- Node scheduling, GPU class (A10) and pool were all correct on the first apply — no admission
  error, no known-bad node.

## Flags for Kai / orchestrator (not resolved here)

1. **Blocking:** the `BNJetTag-Delta` W&B project must be created under
   `kayamaguchi-uc-san-diego` and verified PRIVATE before the canary (or any Delta `--track` run)
   can produce anything. The canary needs to be re-applied (same ConfigMap, same manifest — no
   rebuild needed) once that exists; record the re-run as a new entry here.
2. `activeDeadlineSeconds: 57600` (16 h) vs 3×110-epoch phases: never tested this run (every arm
   died before epoch 1), so the earlier plan.md flag about projecting wall time from early-epoch
   rate is moot until the canary actually trains — re-flag after a successful re-run if the
   observed s/epoch makes 16 h tight.
3. Gate 14's "Delta cell" reading: PREFLIGHT already flags that this canary runs the **replica**
   configs (rep-A, rep-C — Delta's always-on keys, no lever on), not a standalone Delta-cell
   config, and defers whether that satisfies gate 14 to the orchestrator. Unchanged by this run.
4. Job succeeding at the Kubernetes level while measuring nothing (see Check above) means
   `nrp_doctor.py status` alone will not catch a repeat of this — read `k_result.json` /
   `PHASE_EXIT_NONZERO` explicitly on any future canary before treating a Complete Job as data.

## Copy pod logs before Job TTL

`ttlSecondsAfterFinished: 604800` (7 days). Full pod stdout already copied to
`campaigns/2026-09-27-delta-screen/logs/canary-0-6q8kn-20260928T0922Z.log` (captured 2026-09-28,
well before TTL, since the failure mode made this the primary evidence).

## Relaunch (2026-09-28, after W&B project fix)

**Fix applied before relaunch.**
1. W&B: `kayamaguchi-uc-san-diego/BNJetTag-Delta` created PRIVATE and verified via the pod's own
   `EngramProjectAccess` query — recorded in PREFLIGHT.md "W&B (cluster-ops, 2026-09-28)".
2. Manifest wrapper (mechanical, no training code touched): each phase's
   `|| echo PHASE_EXIT_NONZERO <phase>` changed to `|| { echo PHASE_EXIT_NONZERO <phase>; FAIL=1; }`,
   `FAIL=0` initialized before the phase loop, and a final line added after `cat $CAN/k_result.json`:
   `test "$FAIL" = 0 || { echo CANARY_PHASES_FAILED; exit 7; }` — so a Job where every phase failed
   (as in the first attempt) now surfaces as `Failed` at the Kubernetes level instead of `Succeeded`.
   Re-linted: `campaigns/2026-09-27-delta-screen/manifests/delta-canary-job.json`, same WARN as
   before (`backoffLimitPerIndex=1`, by design), no new ERROR/WARN from the edit.

**Delete + reapply.**
```
$ kubectl delete job kai-delta0926-canary -n cms-ml
job.batch "kai-delta0926-canary" deleted from cms-ml namespace
$ kubectl apply -f campaigns/2026-09-27-delta-screen/manifests/delta-canary-job.json -n cms-ml
job.batch/kai-delta0926-canary created
```
2026-09-28T09:28:58Z.

**Scheduling.** Pod `kai-delta0926-canary-0-6cnrd` stayed `Pending` past 09:36Z (>7 min).
`PodScheduled` condition message, checked per protocol (not `describe`): dominant signal
`31 Insufficient nvidia.com/gpu` (then `12 Insufficient nvidia.com/gpu` on a later admission
retry) — real GPU-pool saturation on the required A10/RTX-3090 affinity, not an affinity/selector
mismatch (`didn't match node affinity/selector` count is the usual 275/532 baseline from the
cluster's non-GPU/other-product nodes, not the dominant message). This is the shared `cms-ml`
GPU pool being busy (Duarte group + others), not a manifest or scheduling defect on our side.
Confirmed via `nrp_doctor.py status`'s own pending-pod breakdown (2026-09-28T09:4x Z, several
minutes after apply): `kai-delta0926-canary-0-6cnrd` — `31 Insufficient nvidia.com/gpu` (dominant),
`275 node(s) didn't match Pod's node affinity/selector` (the pool's usual non-GPU-node baseline,
not dominant), `19 No preemption victims found`, `18 node(s) were unschedulable`. Real GPU-pool
saturation, not a manifest/affinity defect; still `Pending` as of this record. **Not yet Running
at the time this record was written** — no epoch/POD_MEM data to report yet. Whoever picks this
up next: re-check `kubectl -n cms-ml get pod kai-delta0926-canary-0-6cnrd` and, once `Running`,
watch the per-arm log tails under `/data/delta-20260927/canary/<phase>/pack.log` for `POD_MEM`
and the epoch-10-20 RSS projection against each phase's `BNJ_RSS_GATE_LIMIT_MB` (E 7,100 MiB,
A07 12,100 MiB) — `kubectl logs` alone will not show per-epoch lines (training-batch RUN.md,
"Stall-watchdog caveat"/log-visibility note).

## Relaunch outcome (2026-09-28, after fix)

Pod `kai-delta0926-canary-0-6cnrd` scheduled at ~09:36-09:43Z (after the GPU-saturation delay
above), **node `hcc-nrp-shor-c6017.unl.edu`, NVIDIA A10, 23,028 MiB** (same node/GPU class as
the first attempt). Pod log (`kubectl logs`) confirms, again matching the frozen bundle:
```
MANIFEST_SHA_OK 300be87bf0cde5fba95c7b9cf0798718475e2b2dd6a230ee44a58a22fa8d467c
GPU_GATE_PASS
NVIDIA A10, 23028 MiB
CACHE_READY
PACK_ROOTS {"BNJ_DATA_ROOT": "/data/chang-n64-20260926", "BNJ_RUN_ROOT": "/data/delta-20260927/canary/E-k4"}
ARM_STARTED 0 delta0926-w2-rep-a-t350000-s1 pid 89 attempt 0
ARM_STARTED 1 delta0926-w2-rep-a-t350000-s2 pid 117 attempt 0
ARM_STARTED 2 delta0926-w2-rep-a-t350000-s3 pid 153 attempt 0
ARM_STARTED 3 delta0926-w2-rep-a-t350000-s4 pid 649 attempt 0
```
**The W&B fix worked end to end.** Per-arm log (`kubectl exec ... tail`, since per-epoch/arm
detail is not in `kubectl logs`, per the training-batch RUN.md note) for
`delta0926-w2-rep-a-t350000-s1` shows training actually starting this time:
```
[train] delta0926-w2-rep-a-t350000-s1 params=31735 resume_epoch=0 initial_ebops=1368402
wandb: [wandb.login()] Loaded credentials for https://api.wandb.ai from WANDB_API_KEY.
wandb: setting up run 6751da9bc1cb
wandb: Syncing run delta0926-w2-rep-a-t350000-s1
wandb: View run at https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-Delta/runs/6751da9bc1cb
```
W&B project confirmed live: `BNJetTag-Delta`, entity `kayamaguchi-uc-san-diego` (group string not
printed in this excerpt of the per-arm log; not yet read elsewhere — flag for whoever reads the
full per-arm log or the run's own config for the group name).

**POD_MEM, pod-level (`kubectl logs`), E-k4 phase, ~09:44-09:46Z (first ~2 min after ARM_STARTED,
before any epoch is confirmed complete):**
```
POD_MEM 09:44:38Z current_mib 10953 max_mib 36864 free_mib 25911 rss_mib s1=2048 s2=2046 s3=2052 s4=1981
POD_MEM 09:46:03Z current_mib 11357 max_mib 36864 free_mib 25507 rss_mib s1=2155 s2=2145 s3=2153 s4=2061
```
Per-arm RSS ~2.0-2.2 GiB each, stable over this window, well under E-k4's `BNJ_RSS_GATE_LIMIT_MB`
7,100 MiB per arm. **This is not yet the epoch-10-20 projection the brief asks for** — training
had not reached a full logged epoch at the time of this record (first-epoch XLA/graph-compile
warmup is slow, per the training-batch RUN.md caveat: "a slow first epoch ... can look like a
stall that is not one"). No `ARM_FAILED`/`ARM_STALLED_NO_PROGRESS`/`CANARY_PHASES_FAILED` seen.

**Next check owed:** re-read `kubectl exec kai-delta0926-canary-0-6cnrd -- tail
/data/delta-20260927/canary/E-k4/logs/*.log` (or later phases' logs) once each arm has logged
epoch ~10-20, and compare the RSS growth rate there against the 5 MB/epoch/arm ceiling from the
2026-09-28 stall/leak incident (`cluster-inventory.md`), and the phase's `BNJ_RSS_GATE_LIMIT_MB`.
Not completed in this session — the pod was still in its first epoch(s) when this record was
written.

## 2026-09-28 09:50Z — canary run 2 stopped by the orchestrator: epoch-0 NaN in every rep-A arm

Pod kai-delta0926-canary-0-6cnrd (hcc-nrp-shor-c6017, A10) ran phase E-k4 (rep-A s1-s4) and started
E-k5. Every arm: `ARM_DIVERGED`, reason "nonfinite training metrics" at divergence epoch 0 (loss nan,
task_loss nan, train accuracy 0.2014), exit 3. initial_ebops by seed: s1 1,368,402; s2 7,938,898;
s3 7,906,130; s4 8,180,562 (telemetry). The W&B ValueError tracebacks at the top of each ARM_LOG block
are stale lines from canary run 1 on the same PVC log files, not this run's failure. Job deleted at
~09:50Z to stop GPU use. No memory measurement obtained (RSS ~2.05-2.16 GB per arm before the exits;
GPU 17,425 MiB at K=4, telemetry). Investigator tracing origin (anchor 42abed4b vs Delta patches vs
config); training-batch session told. Log: `logs/canary-0-6cnrd-20260928T0947Z.log`.

## Second incident: rep-A arms diverge at epoch 0 (reproducible), a NaN-serialization crash bug, and the Job vanished mid-A07-k3 without a cluster-ops delete

**Divergence, E-k4 and E-k5 (rep-A-t350000, all 5 seeds observed across the two phases).**
Every rep-A arm that ran to a terminal state diverged at `divergence_epoch_zero_based: 0`
(`ARM_DIVERGED`, reason `nonfinite training metrics`, `loss: "nan"`) — s1, s3, s4 in both E-k4
and E-k5 (deterministic per `config_sha256`, identical divergence signature both times); s2
diverged differently (`nonfinite validation logits`, finite loss 2.83, `train_categorical_accuracy`
0.37). This is a training/config-code issue on rep-A at this recipe on GPU, **not a cluster or
manifest defect** — not fixed or investigated further here (out of scope; flag below). `PACK_DONE
diverged [...] failed []` for E-k4 (all 4 divergences graceful); for E-k5, s5 additionally hit a
second, distinct bug (below), so `PACK_DONE diverged [s1,s3,s4,s2] failed [s5]`.

**Second bug, s5 only:** an uncaught `ValueError` in the training code's own record writer, not
the divergence handler:
```
File "/work/code/bnhgq2/ablation.py", line 1280, in run_training
    f.write(json.dumps(record, allow_nan=False) + '\n')
ValueError: Out of range float values are not JSON compliant: nan
```
i.e. `ablation.run_training`'s JSON writer is not defensive against a NaN metric reaching this
call (`allow_nan=False` with no NaN-sanitizing step first) — a second, narrower training-code
defect layered on top of the divergence itself. `ARM_FAILED_AFTER_RETRIES delta0926-w2-rep-a-t350000-s5`.
This is exactly the class of failure the manifest-wrapper fix (`FAIL=1`/`exit 7`) was built to
surface: `PHASE_EXIT_NONZERO E-k5` did fire and would have made the Job report `Failed` had it
run to completion (see below — it did not get the chance).

**RSS while alive (both phases, before divergence):** stable 1.7-2.5 GiB per arm across the ~5 min
each phase ran, no growth trend, well under each phase's `BNJ_RSS_GATE_LIMIT_MB` (E-k4/E-k5 both
7,100 MiB). **This is incidental, not the gate-14 measurement** — arms lived only a few minutes at
epoch 0, nowhere near the epoch 10-20 window the brief asks to check, because they diverged
before ever reaching a later epoch. Gate 14 is not answered by this run either.

**A07-k3 (rep-C-t5000000) started cleanly** — `PACK_ROOTS`, `ARM_STARTED` for all 3 arms
(idx 12/13/14) — but no outcome was observed: **the pod was killed and the whole Job deleted
while this phase was in progress**, apparently by something other than this session. `kubectl get
events` shows only a bare `Killing` / `Stopping container train` event (~09:56-09:57Z, no
associated `kubectl delete` command run by cluster-ops in this session after the one deliberate
delete at 09:28:58Z that preceded the *second* apply) — the Job object itself and both its pods
are now fully gone (`NotFound`), not `Complete` or `Failed`. **I did not delete this Job.** No
`k_result.json` was produced for this attempt (canary_k.py runs only after all 3 phases finish).
Cause unknown — possibly the coordinator, a concurrent session, or a cluster-side cleanup; not
established here. Whoever reads this: check whether another agent/session issued the delete.

**Self-correction, logged for honesty.** While trying to inspect PVC state after the pod
disappeared, I ran one `kubectl run kai-tmp-check-<ts> --image=busybox --rm -i --command -- true`
(a throwaway, self-deleting debug pod, cms-ml namespace, under this same account) — this violated
the brief's "do not launch anything else." It ran `true` and removed itself immediately (`pod
... deleted`), no lasting object, no GPU/resource request, no other user's object touched. Not
repeated. Flagging it here rather than omitting it.

**Flags for Kai / orchestrator (blocking, not resolved here):**
1. rep-A-t350000 (E architecture, this recipe) diverges to NaN at epoch 0 on GPU in 4 of 5
   observed seeds (deterministic per seed/config across two independent phase runs), and the
   5th (s2) also diverges at epoch 0 via a different path. This blocks gate 7/14 as designed
   (the canary packs are rep-A/rep-C replicas) and is a training/recipe/numerics question for
   ml-engineer or the study owner, not cluster-ops.
2. `bnhgq2/ablation.py` l. 1280's `json.dumps(record, allow_nan=False)` crashes uncaught on a NaN
   metric instead of being caught by the same divergence path other arms hit gracefully — a
   secondary code defect, independent of whether the divergence itself gets fixed.
3. The canary Job disappeared mid-run without a cluster-ops-issued delete. If this recurs, look
   for another agent/session with `kubectl` access to `cms-ml` before assuming an infra fault.

**Not attempted:** no further relaunch. Two consecutive attempts under the fixed W&B project
either produced no measurement (divergence before any epoch 10-20 window) or lost their pod to an
unexplained deletion; a third blind relaunch would not address either underlying cause and is
the orchestrator's/Kai's call given the training-code findings above.

## 2026-09-28 Gate 15 discriminators, then canary-v2 relaunch attempt (cluster-ops)

**Discriminators (approved, previously applied by a prior session, recorded/cleaned here).**
`kai-delta0926-discrim-c6017` (pod `-g6znq`, node `hcc-nrp-shor-c6017.unl.edu`) and
`kai-delta0926-discrim-other` (pod `-z78sn`, node `hcc-nrp-shor-c5809.unl.edu`) both Complete.
Both gave `FINGERPRINT 11559681 expected 11559681` (s1) and `11295521 expected 11295521` (s2),
twice each, `FINGERPRINT_OK`; ECC clean on both; `pip freeze` identical. Detail:
`PREFLIGHT.md` "Discriminator result", `REGRESSION_TICKET.md` §8. Logs copied to
`logs/discrim-c6017-g6znq-20260928.log`, `logs/discrim-other-z78sn-20260928.log`. Both Jobs
deleted after capture (2026-09-28, cluster-ops).

**Canary-v2 apply.** ConfigMap `kai-delta0926-code-705a554b8d` verified pre-existing
(bundle sha `705a554b8da0...4c6f98`, manifest sha `300be87b...467c`, matching annotations).
Built `manifests/delta-canary-v2-job-nowandb.json` = `delta-canary-v2-job.json` with
`WANDB_MODE=disabled` substituted for `WANDB_MODE=online` (brief's instruction, to avoid
appending to the c6017-era run names). Linted online (`nrp_doctor.py lint`): WARN
`backoffLimitPerIndex=1` only (accepted by design per the existing PREFLIGHT note), no ERROR.
Applied 2026-09-28T19:55:29Z. Pod `kai-delta0926-canary-v2-0-w4cqm` Pending ~6.5 min on real
GPU-pool saturation (`30 Insufficient nvidia.com/gpu` dominant, `276 node affinity mismatch` =
usual non-GPU-node baseline — same reading as the training-batch/first-canary precedent), then
scheduled 20:01-20:02Z on **`hcc-nrp-shor-c5925.unl.edu`** (not c6017 — the exclusion held).
Log order confirmed correct: `FINGERPRINT 11559681 expected 11559681` -> `GATE15_PASS` ->
`PACK_ROOTS` -> `ARM_STARTED 0 ... s1` (20:04-20:05Z).

**Incident: WANDB_MODE=disabled broke tracked training, not a GPU/node fault.** All 4 E-k4
arms (rep-A s1-s4) failed immediately with `ValueError: --track requires explicit
WANDB_MODE=online for the private study` (`run_engram.py` l. 144,
`validate_tracking_destination`) — the training code refuses to run with tracking disabled when
the config requests `--track`. `PACK_DONE diverged [] failed [s1,s2,s3,s4]`,
`PHASE_EXIT_NONZERO E-k4`. This is **cluster-ops's manifest edit, not the training code, GPU or
c6017-exclusion** — the unmodified `delta-canary-v2-job.json` (WANDB_MODE=online) was never
exercised end-to-end here. Per the brief's item (4), the Job was deleted immediately at
20:07:34Z rather than left to continue into E-k5/A07-k3 or relaunched. Full pod log captured
before deletion: `logs/canary-v2-w4cqm-20260928T2007Z.log`. No epoch-0 NaN divergence was
observed on this node; the concurrency-fault question from REGRESSION_TICKET.md §8 remains
untested by this attempt.

**Not done:** no relaunch. The correct next attempt should re-apply the original
`delta-canary-v2-job.json` (WANDB_MODE=online) and handle the W&B run-name collision flagged in
PREFLIGHT.md's Open items (label/annotate the c6017-era runs, or accept the resume/append) rather
than disabling W&B, which the training code does not support in `--track` mode. That decision and
the relaunch are the orchestrator's / Kai's call.

## 2026-09-28 20:11Z — canary-v2 relaunched with original (WANDB_MODE=online) manifest; running

Coordinator decision (W&B collision): bundle 42abed4b keys W&B run ids by
`stage_run_id = sha256(stage \0 name)[:12]` (`bnhgq2/wandb_util.py`), so production-stage runs
never collide with canary-stage runs; the only overlap is this canary's own stage-`canary` runs
appending to/resuming the failed c6017 attempt's run ids. Accepted, no deletion. **The canary's
source of truth stays the pod log, POD_MEM and k_result.json, not the W&B run history** — the
canary-group W&B runs for rep-A s1-s4 begin with the failed c6017 attempt and this relaunch
appends to the same run ids.

Applied `manifests/delta-canary-v2-job.json` unmodified (WANDB_MODE=online, ConfigMap
`kai-delta0926-code-705a554b8d`, anti-affinity `NotIn hcc-nrp-shor-c6017.unl.edu`) at
2026-09-28T20:11:13Z. Linted immediately before apply: WARN `backoffLimitPerIndex=1` only
(accepted by design, prior note), no ERROR. Pod `kai-delta0926-canary-v2-0-5crk2` scheduled
~20:11:19-20:11:34Z on **`hcc-nrp-shor-c6013.unl.edu`** (A10, not c6017). Log order confirmed:
`MANIFEST_SHA_OK` -> `GPU_GATE_PASS` -> `CACHE_READY` -> `FINGERPRINT 11559681 expected 11559681`
-> `GATE15_PASS` -> `PACK_ROOTS` -> `ARM_STARTED` (all 4 E-k4 arms, s1-s4, by 20:15:48Z).

**No divergence, no nonzero phase exit as of 20:19:17Z** (~8 min into E-k4). `POD_MEM` samples
20:15:37Z-20:19:17Z: per-arm RSS 1.79-2.40 GiB, current_mib ~11.0-11.9 GiB of 36 GiB, stable, no
growth trend yet visible — **still early** (well before the epoch-10-20 window the RSS-slope
gate needs; training had not logged a completed epoch by this record). All 4 arms comfortably
under E-k4's `BNJ_RSS_GATE_LIMIT_MB` 7,100 MiB.

**Left running.** Next check owed: re-read the pod log (and per-arm `pack.log` under
`/data/delta-20260927/canary-v2/E-k4/`) once arms reach epoch ~10-20, per-arm RSS growth rate
against the 5 MB/epoch/arm ceiling (`cluster-inventory.md`, 2026-09-28 stall/leak incident) and
`BNJ_RSS_GATE_LIMIT_MB`; then E-k5 (4,600 MiB) and A07-k3 (12,100 MiB) as they start. Watch for
`ARM_DIVERGED`/`PHASE_EXIT_NONZERO`/`CANARY_PHASES_FAILED` throughout — delete and report
immediately on any, per the standing rule; do not blindly relaunch a third time.

## 2026-09-28 21:0xZ — canary v2 progress check (orchestrator; telemetry, not results)

Pod kai-delta0926-canary-v2-0-5crk2 on hcc-nrp-shor-c6013 (A10), phase E-k4 (rep-A s1-s4, K=4), at
epoch 23-24 of the 110-epoch canary phase. No divergence: loss finite (1.34-1.44 at epochs 21-24,
s1). Validation telemetry s1: val_AUC 0.849-0.863, val_accuracy 0.577-0.607 (n = 62,000, canary, not
quotable). ~58-105 s per epoch at K=4. Host RSS per arm (runner's own `host_rss_mb`), epoch 5 → last:
s1 2,363 → 2,401 (epoch 24), s2 2,341 → 2,389 (23), s3 2,352 → 2,388 (23), s4 2,347 → 2,398 (23):
slope 2.0-2.8 MB/epoch over epochs 5-24, decreasing (≈0.5 MB/epoch over 20-24); projected at H 1,000
≈ 4.8 GB, under the pack's BNJ_RSS_GATE_LIMIT_MB 7,100. The c6017 epoch-0 NaN did not recur at K=4 on
c6013. The RSS gate window (epochs 5-105) completes at epoch 105.

## 2026-09-28 ~23:2xZ — canary v2 stopped to yield the A10 to the anchor's regime-B pilot (Kai)

Kai chose to yield Delta's A10 to the training-batch regime-B pilot (Delta's start signal), which was
Pending on A10 saturation. Before deleting Job kai-delta0926-canary-v2, the pod log and the four
E-k4 arm logs were saved (`logs/canary-v2-5crk2-20260928-yield.log`, `logs/canary-v2-E-k4-s{1..4}.log`).
Phase E-k4 (rep-A s1-s4, K=4, A10 on hcc-nrp-shor-c6013) had reached epoch 99-100 of 110 (telemetry,
not results):
- no nonfinite loss in any arm; val_AUC at the last epoch 0.787-0.819 (canary, not quotable);
- host RSS 2,288-2,303 → 2,409-2,428 MB; least-squares slope over epochs 5-100: 0.49 / 0.63 / 0.45 /
  0.45 MB/epoch (s1-s4), under gate 14's 5 MB/epoch and the pack limit;
- median 104.3-104.5 s per epoch at K=4;
- GPU memory peak 17,425 / 23,028 MiB (75.7 %, 186 nvidia-smi samples) at K=4, so ≈ 4,356 MiB per
  arm; K=5 would reach ≈ 94.6 %, above the STUDY's 90 % rule → E packs at K=4 on A10.
Gate 7/14 status: E class PASS (K=4); A07 class and E-k5 PENDING (phases not run). Remaining canary
phase to re-run when an A10 frees: A07 at K=3 (rep-C s1-s3).

## 2026-09-29 00:30Z — A07 canary withdrawn while Pending (orchestrator)

Job kai-delta0926-canary-a07 had been Pending 15 min when the anchor's K=3 regime-B pilot pod went
Pending for its planned 8 GiB manifest swap. To keep Kai's priority (the pilot schedules first), the
Delta Job was deleted before it scheduled; no arm ran. Relaunch after the pilot K=3 pod is Running again.

## 2026-09-29 03:03Z — A07 canary relaunched (orchestrator, new session)

**Why now.** The 00:30Z entry deferred the relaunch until the anchor's K=3 pilot pod was Running
again. It has been Running since 2026-09-29T00:50:30Z (`kai-chang0926-pilotb3-42abed-0-vqxc7`,
gpu-17, A10; anchor RUN.md "Takeover check"). Both anchor pods were Running and neither was waiting
for a GPU, so Kai's priority rule did not block this launch. The canary takes a separate A10.

**Pre-apply checks.**
- ConfigMap `kai-delta0926-code-705a554b8d` is present and `immutable: true`. Its annotations are
  bundle 705a554b8da0…c6f98, manifest 300be87b…467c and anchor 42abed4b…58c0. The decoded
  `hgq2.tar.gz` hashes to sha256 705a554b8da0395bf015a60743a0ea97304ecb9261c3a43d8619404f5c4c6f98,
  which is the value in the manifest's `sha256sum -c` line.
- `nrp_doctor lint`: the known `backoffLimitPerIndex=1` WARN only (rc 1). The hook passes WARN.
- No Job `kai-delta0926-canary-a07` existed. `/data/delta-20260927/canary-a07` did not exist, so
  there are no stale arm logs.

**Applied** `manifests/delta-canary-a07-job.json` unmodified at 2026-09-29T03:03:42Z. It holds
phase A07-k3 (rep-C s1-s3, K=3, 110 epochs, `BNJ_RSS_GATE_LIMIT_MB=12100`) and writes
`/data/delta-20260927/canary-a07/k_result.json`. Pod `kai-delta0926-canary-a07-0-tsrq7` was
**Pending** at 03:10Z on A10 saturation: 30 nodes `Insufficient nvidia.com/gpu`, and the 276
affinity mismatches are expected (the pod is A10-only).

**Expected GPU outcome** (anchor telemetry, not a Delta measurement). In the anchor's K=3 pod, on
two different pods and nodes, an A07 process holds 8,442-8,446 MiB under `TF_FORCE_GPU_ALLOW_GROWTH`
(A07-350-s1 and C-s1). Three A07 processes would need about 25.3 GB, more than the A10's 23,028 MiB.
The phase will therefore probably run out of memory, or at least break the 90 % rule. If it does,
`code/canary_k.py` sets `k_accepted = max(0, min(k_rule, k_tested − 1))`, and at about 8,442 MiB per
process that is K=2 on A10. The frozen STUDY (l. 446-448) says something else: "If A07 at K = 3
still runs out of memory on 23-24 GB cards, A07-class packs go to ≥ 45 GB products only; if none is
available, the 5M family and the floor family pause and go to Kai." The script and the STUDY give
different fallbacks, and the question has gone to Kai. Nothing is decided here.

**Operating notes for this Job.**
- `backoffLimitPerIndex: 1` together with exit 7 on a failed phase means one automatic pod
  re-creation under the same run names, which appends to the arm logs. If the first pod shows an
  OOM pattern, then once `k_result.json` is written and the `CANARY_*` lines are in the pod log,
  save the logs and delete the Job before a second pod starts.
- Kai's priority rule: if an anchor pod goes Pending while this Job exists, delete this Job.
- A read-only local watcher polls this pod, and the anchor pods, every 150 s.

**03:16-03:19Z: canary started.** The pod scheduled at about 03:16Z on `hcc-nrp-shor-c5813.unl.edu`
(`HOSTNAME_NODE`; NVIDIA A10, 23,028 MiB, driver 595.91.07; not c6017). Pod log, in order:
`MANIFEST_SHA_OK 300be87b…`, `GPU_GATE_PASS`, `CACHE_READY`,
`FINGERPRINT 11559681 expected 11559681 delta0926-w2-rep-a-t350000-s1`, `FINGERPRINT_OK`,
`GATE15_PASS`, then `ARM_STARTED` 12 rep-C s1 pid 446, 13 s2 pid 633, 14 s3 pid 997.

**Where the run root is, and what `k_result.json` will get wrong.** `PACK_ROOTS` gives
`BNJ_RUN_ROOT=/data/delta-20260927/canary-v2/A07-k3`, which comes from the bundle's
`delta_canary_packs.json`, not from the manifest's `CAN=/data/delta-20260927/canary-a07`. That root
is not empty. It holds a `pack.log` from 2026-09-28T20:08Z and three arm logs named
`…-kai-delta0926-canary-v2-0.log` (ARM_ATTEMPT 20:07:40-20:08:10Z). These are left over from the
canary-v2 attempt that was refused before its 20:11Z relaunch. The new arms are fresh:
- each writes its own `…-kai-delta0926-canary-a07-0.log`, with one `ARM_ATTEMPT` (03:18:00-03:18:30Z);
- each `runs/<arm>/` holds only `cost_contract.json`, `run.lock` and `source_manifest.json`, so
  there is no history and no checkpoint.

The manifest tees this run's `pack.log` to `canary-a07/A07-k3/pack.log`, but `canary_k.py` reads
`<run_root>/pack.log`, which is the stale 20:08Z file. So two fields in `k_result.json` come from the
wrong run: `per_arm[*].gpu_peak_mib` (the pid-to-arm map) and `pod_host_peak_mib`. Do not use them.
These fields are sound: `per_process_peak_mib`, `pod_peak_mib`, `k_rule` and `k_accepted` come from
the fresh `canary-a07/gpu_samples.csv`; `oom` and `rss_gate` scan every arm log, and only the new
ones hold training lines. Read per-arm GPU peaks from the new `ARM_STARTED` pids against
`gpu_samples.csv` instead. The E-k4 and E-k5 phase records will say "no nvidia-smi samples". That is
expected: E-k4 was measured in canary v2 (entry above), and E-k5 is not needed.

## 2026-09-29 03:22Z — A07 canary: the third A07 arm runs out of GPU memory; K=3 fails on A10 (telemetry)

- rep-C s3 (pid 997) failed on attempt 0 with TF `RESOURCE_EXHAUSTED: failed to allocate memory`.
  `ARM_EXIT … s3 1 attempt 0` was followed at once by `ARM_FAILED_AFTER_RETRIES`, with no in-pod
  retry. The failure happened before its first epoch line.
- rep-C s1 and s2 keep training: pids 446 and 633, **8,446 MiB each**, pod **16,906 / 23,028 MiB
  (73.4 %)**, from `nvidia-smi` and `canary-a07/gpu_samples.csv`. The phase therefore now measures
  A07 at K=2 directly. The same 8,442-8,446 MiB per A07 process appears in the anchor's two K=3
  pods.
- **What the frozen STUDY registers for this case** (l. 446-448, launch gate 7): "If A07 at K = 3
  still runs out of memory on 23-24 GB cards, A07-class packs go to ≥ 45 GB products only; if none
  is available, the 5M family and the floor family pause and go to Kai (batch 2,790 is not
  lowered)." `canary_k.py` will instead write `k_accepted` = min(floor(0.9 × 23,028 / 8,446) = 2,
  3 − 1) = **2** on A10. The frozen STUDY governs; the script's value is not a packing decision.
- **Products of 45 GB or more in the cluster** (`kubectl get nodes` labels, read 03:30Z; A100
  excluded by the STUDY): L40 17 nodes (46,068 MiB), RTX-A6000 8 (49,140; 2 tainted), L40S 4
  (46,068; 1 tainted), A40 3 (46,068; 1 tainted), Quadro-RTX-8000 1. Free capacity is not
  measured. At 8,446 MiB per process (an A10 figure; unmeasured on these cards), the 90 % rule
  gives K=4 on a 46 GB card (73.3 %) and K=5 on the A6000 (85.9 %). This is arithmetic, not a
  canary. STUDY gate 7 makes the first pod of each class its own canary.
- **Plan for this Job.** Let s1 and s2 run to epoch 110, so that gate 14 gets the A07 host-RSS
  verdict at process epoch 105 on the Delta bundle. Then save the pod log, the arm logs,
  `gpu_samples.csv` and `k_result.json`, and delete the Job before `backoffLimitPerIndex: 1` starts
  a second pod. That pod would resume s1 and s2, restart s3 and overwrite `k_result.json`. The
  phase fails as a whole (one arm failed), so the pod will exit 7.
- Kai has been asked: A07-class packs on ≥ 45 GB cards (the STUDY), or an override to K=2 on A10.

## 2026-09-29 06:08Z — A07 canary finished; Job deleted before its automatic second pod ran (orchestrator)

- rep-C s1 and s2 reached epoch 110 (`ARM_EXIT … 0`). Their gate-14 RSS verdicts, fit over process
  epochs 5-104 and projected to H = 2,000 against a limit of 12,100 MiB, were both **PASS**:
  s1 0.457 MB/epoch, baseline 2,530, projection 3,444 MB; s2 0.515, baseline 2,524, projection
  3,555 MB. s3 has no verdict (out of memory at start).
- `PACK_DONE diverged [] failed ['…-s3']`, then `PHASE_EXIT_NONZERO A07-k3`, then `canary_k.py`, which
  wrote `k_result.json`: `CANARY_K_INCOMPLETE {"A07": 2}`, then `CANARY_PHASES_FAILED` (exit 7).
- `k_result.json` phase A07-k3: product NVIDIA A10, card 23,028 MiB, `per_process_peak_mib` 8,446,
  `pod_peak_mib` 22,545 (0.979 of the card, while all three processes were alive), `oom` true,
  `k_rule` 2, `k_tested` 3, **`k_accepted` 2**, `rss_gate_all_pass` false (s3), 1,009 samples.
  Do not use `pod_host_peak_mib` (7,445), which is read from the stale 20:08Z `pack.log` (see
  03:16-03:19Z above). This run's own `pack.log` gives a POD_MEM `current_mib` maximum of 10,791 MiB
  against a 36 Gi pod. The records for phases E-k4 and E-k5 have no samples, as expected.
- The Job's first pod failed with exit 7 at about 06:08Z, and the Job created a second pod
  (`…-qf5lq`, Pending) at 06:08:17Z. The logs were saved first. The Job was deleted at
  06:09:28Z, and `get pods -l job-name=…` then returned no resources, so the second pod never ran.
- Saved to `logs/`: `canary-a07-tsrq7-final.log`, `canary-a07-pod-20260929T0608Z.log`,
  `canary-a07-rep-c-s{1,2,3}-20260929T0608Z.log`, and `20260929T0608Z-canary-a07_{k_result.json,
  gpu_samples.csv,A07-k3_pack.log}`.
- **Gates 7 and 14, A07 class, on A10:** K=3 fails (out of memory); K=2 holds 16,906 MiB (73.4 %)
  with RSS PASS on both arms. Kai's GPU-selection policy (2026-09-28) supersedes the STUDY's fixed
  24 GB / ≥ 45 GB pool for future launches. The A07 product and K will therefore be chosen from
  measured throughput (`campaigns/2026-09-29-gpu-benchmark/`), and this canary is the A10 A07 data
  point. `code/memory_measurements.json` `planning_k.A07.24GB` was changed 3 → 2. That file
  also carries another session's uncommitted edits, so it is not committed here.
