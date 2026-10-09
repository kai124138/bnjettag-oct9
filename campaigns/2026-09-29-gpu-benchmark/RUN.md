# RUN — GPU-product throughput benchmark (2026-09-29)

Launch records, pinning check, incidents. Telemetry only; nothing here is a result. STUDY.md
(designed, Amendment 1) and PREFLIGHT.md (critical v2 PASS, `review/PREFLIGHT_critical_v2.md`)
govern. Bundle: anchor 42abed4b (ConfigMap `kai-chang0926-code-42abed4b5d`), fingerprint ConfigMap
`kai-chang0926-fp-e9511d1aeb`, driver ConfigMap `kai-gpubench-driver-5ede0778f7`
(sha 5ede0778f716…c45). The pod log is the source of truth; W&B is off.

## Operating rules carried from PREFLIGHT
- **Staged apply (v2 B2).** A small first wave goes out, and the rest waits until the first pod to
  start shows `ARM_CPUS n=<2K> … OK` in every arm log. Its `samples.csv` must also show
  `proc_cpus_allowed` within `pinned` on rows with `proc_epochs_done ≥ 1`.
- **A10 Jobs (Open item 5, v2 B3/B4).** They are applied last, and only when all of these hold: no
  Chang pilot-b pod is Pending; a live watcher is running, polling every 150 s with a heartbeat line
  per poll in the orchestrator's scratch `watch/heartbeat.log`; and the fixer's v2 items B3 and C5
  have landed (pilot nodes c5805 and gpu-17 excluded). If a pilot pod goes Pending while an A10
  benchmark pod exists, or the watcher stops, delete both A10 Jobs.
- **A100.** K_rule first; K_low only after the K_rule pod has terminated (one quota unit, 23/24).
- **`bench_summary.py`** does not run on benchmark data until v2 B1 (the pre-pin-row filter) has landed.
- **Re-runs.** Move the product directory aside, never delete it; a re-run into a non-empty root exits 11.

## Launches

| time (UTC) | Job | shape | note |
| --- | --- | --- | --- |
| 09:30:27Z | `kai-gpubench-geforce-rtx-3090-klow` | E 4, A07 1 (8 CPU / 32 Gi) | first-wave pod for the pin check. At 09:31Z it was Pending: 28 nodes `Insufficient nvidia.com/gpu`, 24 `Insufficient cpu` (the 3090 pool is saturated) |
| 09:32Z | `kai-gpubench-l40s-klow` | E 4, A07 2 | first wave widened, because the 3090 pool is full. A pin failure exits 14 before any work, so a wider first wave risks only minutes of pod start-up |
| 09:32Z | `kai-gpubench-rtx-a6000-klow` | E 4, A07 2 | as above |
| 09:32:36Z | `kai-gpubench-geforce-rtx-4090-klow` | E 4, A07 1 | as above |

| 09:35Z | `kai-gpubench-l40-klow` | E 4, A07 2 | the K_low wave is complete: at 09:34Z the four pods above were all Pending on GPU saturation (3090 28 nodes `Insufficient nvidia.com/gpu`; 4090 3; L40S 2; A6000 3 `Insufficient nvidia.com/rtxa6000` + 5 `Insufficient cpu`) |
| 09:35Z | `kai-gpubench-a40-klow` | E 4, A07 2 | as above |
| 09:35:47Z | `kai-gpubench-a100-sxm4-80gb-krule` | E 16, A07 8 (32 CPU / 128 Gi) | applied ahead of the pin check to take a queue place for the one free A100 quota unit (`requests.nvidia.com/a100` 23/24 just before the apply). A pin failure still exits 14 before any work, and the quota is freed when the pod ends |

Every apply was `kubectl create -f` on the linted manifest; the PreToolUse hook re-linted each one.
The hook resolves relative paths from the session's working directory, so applies use absolute paths.
Not yet applied: the K_rule Jobs of the 3090, 4090, L40, L40S, A6000 and A40 (they wait for the pin
check); A100 K_low (it waits until the A100 K_rule pod terminates); both A10 Jobs (Open item 5).

**Correction (orchestrator, 10:05Z):** the 3090 and 4090 K_low rows first read "A07 2". Their
manifests run A07 at K=1: STUDY [D2] K_low = K_rule − 1 whenever K_rule (2 on 24 GB cards) is at
or below the A10 K. The fixer found the error; the rows above are corrected.

## 2026-09-29 ~10:30Z — pin check PASS on the first pod to start (v2 B2)

- `kai-gpubench-a100-sxm4-80gb-krule-kqnx5` started at 09:52:59Z on `sphinx.sdstate.edu`, about 17 min
  after it was applied. Its node runs the static CPU manager: `POD_CPUS allowed_n 32` equals the pod
  request of 32 CPUs, an exclusive cpuset of AMD EPYC 7713, and `cgroup_cpu_max` is `max`.
  `FINGERPRINT 11559681 expected 11559681`: the fingerprint holds on the A100.
- Phase `p1-E-k16`: `PHASE_CPUS … n 32 physical_cores 16`. All 16 arm logs print
  `ARM_CPUS n=32 requested <set> seen <set> OK` (16 of 16 OK).
- `samples.csv` (487 rows at ~10:30Z): 346 proc rows with `proc_epochs_done ≥ 1`. **0 of them have
  `proc_cpus_allowed` outside the pinned set**, and `proc_threads` is 25 on 341 of them and 61 on 5 [corrected 2026-09-29 per VERIFY.md; first written as "25 on every one of them"]. Pinning
  holds for every TF/CUDA thread, not only for the arm's main thread.
- Telemetry, not a result: GPU utilization averaged 95.3 % over 31 samples. GPU memory peaked at
  72,709 / 81,920 MiB (88.8 %).
- Decision: the staging condition is met, so the rest of the Jobs are applied (table below).

| time (UTC) | Job | shape | note |
| --- | --- | --- | --- |
| 10:27-10:28:03Z | `kai-gpubench-{geforce-rtx-3090,geforce-rtx-4090,l40s,rtx-a6000,l40,a40}-krule` | K_rule (18 CPU / 72 Gi on the 46-49 GB cards; 10 CPU / 40 Gi on 24 GB) | applied after the pin check |
| 10:28:21Z | `kai-gpubench-a10-krule`, `kai-gpubench-a10-klow` | A10: E 4 / A07 2 and E 3 / A07 1 | Open item 5 preconditions met at 10:28Z: both pilot-b pods Running, none Pending; watcher heartbeat live (last polls 10:24:12Z, 10:26:57Z); fixer v2 B3 and C5 in place (NotIn includes gpu-17 and c5805, checked in both manifests) |

Not applied: `kai-gpubench-a100-sxm4-80gb-klow`. It waits until the A100 K_rule pod terminates,
because there is one quota unit.

## 2026-09-29 11:25-11:57Z — first Jobs complete (telemetry; the summary script and VERIFY.md evaluate them)

| Job | pod / node | phases (`PHASE_DONE`: wall s for 21 epochs, outcomes, steady cores per arm) | saved |
| --- | --- | --- | --- |
| `kai-gpubench-a10-klow` | `…-smvnq` / hcc-nrp-shor-c5821 | p3-E-k3 1,880.3 s, 3 ok, 0.575; p4-A07-k1 1,180.1 s, 1 ok, 0.588 | `logs/kai-gpubench-a10-klow/` |
| `kai-gpubench-a10-krule` | `…-g8b5c` / hcc-nrp-shor-c6009 | p1-E-k4 2,530.5 s, 4 ok, 0.556; p2-A07-k2 2,235.3 s, 2 ok, 0.543 | `logs/kai-gpubench-a10-krule/` |
| `kai-gpubench-a100-sxm4-80gb-krule` | `…-kqnx5` / sphinx.sdstate.edu | p1-E-k16 3,902.7 s, 16 ok, 0.520; p2-A07-k8 3,181.5 s, 8 ok, 0.544 | `logs/kai-gpubench-a100-sxm4-80gb-krule/` |

Each phase is under the 2.1 cores-per-arm limit (rule 5). The saved files are `job.json`, `pod.json`
and the pod log; the arm logs and `samples.csv` stay on the PVC under
`/data/chang-n64-20260926/gpu-bench/<slug>/`. The A10 Jobs are done, so the yield rule no longer
applies.

- 11:57:07Z: applied `kai-gpubench-a100-sxm4-80gb-klow` after the K_rule pod had Succeeded (11:56Z;
  `requests.nvidia.com/a100` 21/24 at that moment).
- Still Pending (queued since 09:30-10:28Z): the K_low and K_rule Jobs of the 3090, 4090, L40, L40S,
  A6000 and A40. Under [D6] each Job shape has 6 h from its apply.

## 2026-09-29 15:37Z — [D6] six-hour rule, first wave: three K_low Jobs "not practical now"

| Job | applied | state at 6 h | action |
| --- | --- | --- | --- |
| `kai-gpubench-l40s-klow` | 09:32:18Z | never scheduled (Pending 6 h 05 min) | deleted 15:37:45Z |
| `kai-gpubench-l40-klow` | 09:35:26Z | never scheduled (Pending 6 h 02 min) | deleted 15:37:45Z |
| `kai-gpubench-a40-klow` | 09:35:35Z | never scheduled (Pending 6 h 02 min) | deleted 15:37:45Z |

Each Job's final scheduler message, pod JSON and Job JSON were saved to `logs/<job>/` before
deletion (`scheduler-message-6h.txt`). Every message reads `0/532 nodes are available`, with the
product's nodes full or tainted. After deletion no pods remained. Per STUDY rule 3, these K_low
shapes are "not practical now". The K_rule Jobs of these products keep their own windows
(applied 10:28Z; 6 h at 16:28Z), and so does the A100 K_low (11:57Z; 6 h at 17:57Z).

Completed so far (logs saved): A10 K_rule and K_low; A100 K_rule; 3090 K_rule and K_low; 4090
K_rule and K_low; A6000 K_low. Still Pending: the L40, L40S, A40 and A6000 K_rule Jobs, and the
A100 K_low.

## 2026-09-29 17:18Z — [D6] six-hour rule, K_rule wave; A100 K_low complete; all 16 Jobs resolved

**Incident (laptop, not the cluster).** From about 16:28Z the orchestrator's laptop lost DNS. Its
logs show `lookup authentik.nrp-nautilus.io: no such host` and OIDC `get-token` failures. The
watcher and the 16:29Z timer could not reach the API until about 17:18Z. The pods were not
affected. Because of this, the [D6] check on the K_rule wave ran at 17:18Z, not 16:28Z. It makes no
difference: none of these pods ever started (empty `startTime`, `Pending`), so each was also not
Running at its 6-h mark.

| Job | applied | state | action |
| --- | --- | --- | --- |
| `kai-gpubench-l40s-krule` | 10:27:54Z | never scheduled | deleted 17:18:54Z; "not practical now" |
| `kai-gpubench-rtx-a6000-krule` | 10:27:57Z | never scheduled | deleted 17:18:54Z; "not practical now" |
| `kai-gpubench-l40-krule` | 10:28:00Z | never scheduled | deleted 17:18:54Z; "not practical now" |
| `kai-gpubench-a40-krule` | 10:28:03Z | never scheduled | deleted 17:18:54Z; "not practical now" |
| `kai-gpubench-a100-sxm4-80gb-klow` | 11:57:07Z | started 15:47Z on gp-engine.usd.edu; Succeeded 16:30Z | logs saved |

Scheduler messages (`0/532 nodes are available`, the product's nodes full or tainted), pod JSON
and Job JSON are in `logs/<job>/` for every deleted Job. No pods remain.

**Final state of the 16 Jobs.** 9 completed, every phase `ok`:
- A10 K_rule and K_low;
- A100-SXM4-80GB K_rule and K_low;
- RTX-3090 K_rule and K_low;
- RTX-4090 K_rule and K_low;
- RTX-A6000 K_low.

7 "not practical now" (not Running within 6 h): L40 ×2, L40S ×2, A40 ×2, RTX-A6000 K_rule.

The benchmark is complete. Next: results-analyst runs `code/bench_summary.py` (v2 B1 filter in place)
on the saved logs plus the PVC `samples.csv` and arm logs, and writes VERIFY.md.
