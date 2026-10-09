# RUN: discovery-350k-20261008

Owner: orchestrator. The approval is `APPROVAL.json` (Kai, 2026-10-08T09:22:59Z; authority sha256
9496cf63…ac79). Policy: BRIEF.md. Monitoring: cron `harness.py tick` every 15 min, writing to
`cron.log`.

## Wave 1, submitted 2026-10-08 09:30 UTC (18:30 JST)

| Job | Handoff | Stage | Bound (GPU-h) | Deadlines (pod / Job) | Observed 09:31 UTC |
| --- | --- | --- | --- | --- | --- |
| kai-d350-baseline-e-350k-s1-a1 | handoffs/rh-adce3a6b9ad29ca7ab6f1f81 | wave1 | 26.24 | 47,000 / 94,000 s | Job Running, pod Pending (unscheduled) |
| kai-d350-reference-e-5m-s1-a1 | handoffs/rh-e066021d9a5e350f0bc0ffe4 | wave1 | 26.24 | 47,000 / 94,000 s | Job Running, pod Pending (unscheduled) |

- Code: code/ commit 43e8326c, training manifest e6ff034b, code ConfigMap kai-d350-code-6107b771d6.
  Handoff ConfigMaps kai-rh-adce3a6b…, kai-rh-e066021d… are present on the cluster.
- Committed GPU-h after submission: 52.49 of the wave-1 + search cap of 90.
- Pre-submission check: first scheduled cron pass at 09:30:01 UTC returned `idle` (read the cluster; no
  campaign Jobs yet).
- Utilization of the E model at one arm per GPU is to be measured once the pods run (the job logs
  GPU_SAMPLE every 60 s).

## Incident, 2026-10-08 ~10:08 UTC: both wave-1 Jobs failed at admission on k8s-3090-01.usd.edu

- **What happened.** After about 38 min Pending, all three pods (baseline twice, reference once)
  were scheduled onto `k8s-3090-01.usd.edu` and failed with `UnexpectedAdmissionError: Allocate
  failed due to device plugin GetPreferredAllocation rpc failed ... unable to get device link
  information`. The node was then tainted and the pods evicted (TaintManagerEviction).
  Both Jobs: Failed, reason FailedIndexes (backoffLimitPerIndex 1, so 2 pods for the baseline).
  No training ran, so the GPU time used was about zero.
- **Classification.** Infrastructure, a faulty GPU device plugin on one node. The code and
  configs are not implicated. This is the same failure class as the lab's existing exclusion of
  `nautilus-ext-gpu01.fullerton.edu` ("GPU is lost").
- **Harness action (automatic, within the signed limits).** At the 10:15 pass the baseline was
  relaunched as `kai-d350-baseline-e-350k-s1-a2`, resuming from attempt 1's run directory, which is
  empty. That is infrastructure relaunch 1 of 2. The reference relaunch is queued for the next pass.
- **Correction (operations, no re-approval).** BRIEF `operations.extra_excluded_nodes` =
  ["k8s-3090-01.usd.edu"]. It applies to handoffs prepared from 10:24 UTC on, including the
  reference relaunch. The already-submitted a2 handoff does not carry it.
- **Node status.** Unknown: reading node objects is forbidden for this account.

### Follow-up, 10:30-10:50 UTC: harness defects found by the incident (fixed, tested, recorded)

1. **Duplicate events.** After Kubernetes deleted the evicted pods, the 10:30 pass treated both
   finished Job indexes as new failures. That queued 2 investigate tasks, never run and now
   cancelled, and charged 2 repairs, now reset. Fix: a finished Job index is acted on once
   (`state.handled`). Test: `test_finished_index_not_handled_twice_when_records_change`.
2. **Relaunch limit per Job name.** Infrastructure relaunches were counted per Job name. Each
   relaunch gets a new name, so the per-arm limit of 2 could never be reached. Fix: counted per arm
   (`bnjettag.io/arm`). Counters moved to `baseline-e-350k-s1`: 1 and `reference-e-5m-s1`: 1.
3. **Exclusion not passed to the builder.** The new exclusion did not reach the Job builder, and
   the builder's self-check refused the 10:30 reference relaunch at preparation. Nothing was
   submitted. Fix in `tools/d350_common.py`.
4. **Unmeasurable finished Jobs held full reservations.** Finished attempt-1 Jobs without pod
   records still held their full 26.24 GPU-h reservations. The 10:45 budget check therefore refused
   the reference relaunch, with 78.73 committed. Fix: a finished Job with
   `podReplacementPolicy: Failed` is counted at its lifetime bound, GPUs × parallelism × (end −
   start): 0.66 and 0.64 GPU-h for the two attempt-1 Jobs. Committed after the fix: 27.54. Test:
   `test_finished_job_without_pod_records_counts_its_lifetime_bound`.
5. **Claims held after task errors.** A task error left the task claimed for its full 1-hour
   lease. Fix: `tick` releases the claim, and the saved steps are kept.

The cron entry was paused from 10:33 to 10:44 UTC while these were fixed and tested. The live
corrections are recorded in LEDGER.jsonl as type `correction`.

- **Baseline attempt 2** (`kai-d350-baseline-e-350k-s1-a2`) was scheduled at about 10:18 onto
  `k8s-3090-01.usd.edu`, the node that had failed, and passed admission this time. At 10:45 it was
  training: FINGERPRINT_OK, 4.4 GB GPU memory, instantaneous utilization 0-100 %, about 45 % mean
  over the first 11 one-minute samples.
- **Reference attempt 4** (`kai-d350-reference-e-5m-s1-a4`) excludes that node. It resumes attempt
  1's run directory.
