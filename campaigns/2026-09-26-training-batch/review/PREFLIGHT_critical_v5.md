# PREFLIGHT gate v5 (solo, critical-reviewer): 2026-09-26-training-batch, scoped to the 8 GiB per-arm resize

2026-09-28 16:50 PDT (23:50Z). Scope from the coordinator brief: the one change in commit c7bae4a
(6 to 8 GiB per arm, `BNJ_RSS_GATE_LIMIT_MB=8192`) and the swap of the running K=3 pod. v4 items
(`review/PREFLIGHT_critical_v4.md`) are outside this scope and were not re-checked, except v4 B2 where
it touches the swap.

VERDICT: ITERATE. The manifests, the sha-guard and the sizing are correct. But the swap rule the orchestrator
now applies ("unconditionally before process epoch 105") has no lower bound: done now, it crashes all three
K=3 arms. RUN.md's deadline is also about 1 h late for arm F. Both fixes are RUN.md text. The safe swap
window is about 00:25Z-01:35Z (2026-09-29), so a quick fix cycle loses nothing.

## Live state read (kubectl get/logs/exec cat only; read-only; 23:38-23:45Z)
- `kai-chang0926-pilotb3-42abed-0-c7tg4`: Running on gpu-16.nrp.mghpcc.org, limit 18Gi, `BNJ_RSS_GATE_LIMIT_MB=6144`.
  `kai-chang0926-pilotb5-42abed-0-v2nll`: Pending 32 min. FailedScheduling is taints, CPU and GPU. A10 nodes
  have about 503 GiB allocatable, so 40 Gi does not make scheduling worse.
- Arm progress (arm logs `/data/chang-n64-20260926/pilot-b/logs/<run>-kai-chang0926-pilotb3-42abed-0.log`):
  - c-s1: epoch 4, 121.8-125.3 s/epoch;
  - a07-350-s1: epoch 4, 116.7-124.8 s/epoch;
  - f-s1: epoch 7, 72.9-76.0 s/epoch (epochs 3-7).
  - `latest.json`: none for all three. Every run dir already has `activation_widths.jsonl`.
- Pod cgroup `memory.stat`: `anon 4029964288` (3.75 GiB), `file 7731970048`, `shmem 31473664`. Arm VmRSS is
  2,359,144 / 2,512,528 / 2,528,748 kB, and wandb-core is about 48 MB per arm. VmRSS therefore includes
  file-backed pages. The gate on VmRSS is conservative against non-reclaimable use, and "K × 8 Gi with no
  overhead added" is defensible. Record this so it is not re-argued.

## Items checked

1. **Jobs from `freeze.py --jobs-only`: VERIFIED.** Parsed all eight `manifests/pilot-b-*-job.json`
   (request = limit):

   | Manifest | Memory | K |
   |---|---|---|
   | k5 | 40Gi | 5 |
   | k3 | 24Gi | 3 |
   | fb48, fb16, fb32 | 8Gi each | 1 |
   | fb16-32, fb48-16, fb48-32 | 16Gi each | 2 |

   Every manifest exports `BNJ_RSS_GATE_LIMIT_MB=8192`. Every script contains the tarball sha
   `42abed4b5d2e3e91…` check, the `041f981a9d5b8c3a…` manifest assertion, and `fingerprint_check.py --run`
   before run_pack. `git show c7bae4a --stat`: each job JSON changes 10 lines (2 annotations, 1 args line,
   2 memory values). The diff has no hunk in affinity, the NotIn list, volumes or Job names.
   `code/evidence/lint_42abed4b_8gib.log`: rc=0, `OK` and `BASH_N_OK` on all eight.
2. **Sha-guard: VERIFIED.**
   - `ablation.py:296-298` asserts config, data and code sha (code from env `BNHGQ2_CODE_SHA256`).
   - `run_study.py:26-32` hashes only `*.py` plus six package versions. `:117-120` sets the env from it and
     re-asserts against `source_manifest.json`.
   - The gate reads env only (`ablation.py:645`, `:648`). `rss_gate_from_env` returns a fresh `'rss': []`
     each process (`:651`, called at `:765`). It is appended once per loop epoch (`:664-665`) and the loop
     starts at `state['completed_epochs']`. The window `rss[5:105]` is therefore this process's epochs.
     A resumed process re-fits from its own epochs 5-104.
   - `run_pack.py:77` writes `==== ARM_ATTEMPT` on every attempt, including 0, to the same appended log
     (`HOSTNAME`-named, `:75-76`). Both awks reset correctly after a re-apply.
3. **A2 constant: VERIFIED.** The threshold is rss10 + 9.5Δ > 8,192. At rss10 = 2,100-2,200 this gives
   Δ > 630.7-641.3 MiB. `rss_rules_8192_test.log`: Δ630 → OK 8,135, Δ650 → STOP 8,325, reset OK, PENDING and
   UNREADABLE behave as documented.

   **Epoch-20 finding: VERIFIED.** On the four Delta E-k4 GPU logs, the 5-20 fit projects to 17,485-27,621
   (all OVER8192). The gate-form fit projects to 5,329-6,615, with s2 at 6,615 FAIL at 6,144 and PASS at 8,192.
   The epoch-20 read has no discriminating power, so the unconditional swap is the right call. Its timing is
   wrong: see A1 and A2.
4. **Sizing decision: sound. The gate is resized, not weakened.** The admitted slope is (8,192 − b)/7,000:
   - 0.869 at b = 2,106 and 0.856 at b = 2,200;
   - 0.829 at the GPU-fitted baseline 2,389 (see C2).

   The worst healthy arm (0.606) has about 0.22 MB/epoch of margin. The incident rate still fills 8 GiB
   before epoch 105: (8,192 − 2,160)/95 = 63.5 and (8,192 − 2,106)/80 = 76.1.
5. **Text: mostly consistent.** Two text defects, B1 and B2 below.

## Flags

**A1. `RUN.md` "8 GiB swap timing" and the brief's "swap unconditionally before process epoch 105" give no
earliest time. A swap now crashes every K=3 arm.**
- Live state: no arm has `latest.json`, and all have `activation_widths.jsonl`.
- Code: `ablation.py:710-711` raises `RuntimeError('History exists without a committed checkpoint')` in
  exactly that state.
- The K=3 manifest has no `ARM_NO_CHECKPOINT` guard (only the fb* manifests have one), so run_pack spends
  the retry budget, and the fix needs a manual rename-aside.
- The first checkpoint is at epoch 25 (`checkpoint_every_epochs: 25` in all 58 chang0926 configs).

Fix in RUN.md: swap only after every arm in the pod has `latest.json`. Read it from the pod and
confirm it before the delete. For C and A07 at about 124 s/epoch that is about 00:22Z. Ideally, swap just
after a 25-epoch boundary of the slowest arm to limit replay.

**A2. The RUN.md deadline ("about 3-4.4 h after `ARM_STARTED` at 104-150 s/epoch") is wrong for arm F.**
- f-s1 runs at 72.9-76.0 s/epoch.
- Process epoch 105 comes about 171 + 104 × 75 s ≈ 2.2 h after F's start, near 01:40Z. The brief's "~23:23Z"
  start plus 3 h gives 02:23Z, too late.
- A late swap exposes F to the 6,144 gate. One of the four Delta healthy arms fails that gate. Exit 5 is not
  retried.

Fix: state the deadline from the fastest arm's measured s/epoch (read at swap time), with a wall-clock
bound. The window is about 00:25Z-01:35Z.

**B1. RUN.md still describes a conditional swap, but the action is unconditional.** The text says "If any
arm is not `OK`, delete…" after the epoch-20 read, while its own next bullet says every arm will be flagged.
The brief now applies the swap unconditionally. Fix: state the swap as unconditional, inside the A1/A2 window.
Demote `rss_proj7000_epoch20.awk` to telemetry or drop it.
Also make "confirm NotFound" apply to pods. `kubectl delete job` uses background propagation, so the Job goes
before its pod: `kubectl -n cms-ml get pods -l job-name=kai-chang0926-pilotb3-42abed` must return none. The
k3 manifest has no ARM_STILL_LIVE guard. The only second line is `run.lock` flock `LOCK_NB`
(`run_study.py:115-116`), which holds only if the kai-data storage class honours cross-client flock. That
was not verified here.

**B2. The A2 awk hardcodes `limit = 8192` in BEGIN** (`rss_rule_epoch10_20.awk`, BEGIN; `-v` cannot
override it). The K=3 pod's epoch-10 and epoch-20 reads (about 23:45Z-00:30Z) fall while it still runs at
18 GiB with a 6,144 gate. RUN.md says the in-code gate stays 6,144 until the swap but applies 8,192 to the
operational rule, so Δ ≈ 420-636 MiB would pass unflagged in a pod whose cgroup is 6 GiB/arm.
Fix: say 6,144 for pods still on the 6 GiB manifest (a `-v` limit override, or a note).

**B3. Wrong projection text in `manifests/freeze.py:22-23` and the STUDY v1 change log (text pass
2026-09-28): "projects to about 6.5-6.7 GB at epoch 7,000: over 6,144".**
- From the quoted inputs: 2,288 + 0.45 × 7,000 = 5,438 and 2,303 + 0.63 × 7,000 = 6,713, so 5.4-6.7 GB.
- The gate form gives 5,329-6,615.
- decisions.md and PREFLIGHT correctly say one of four is over 6,144. The STUDY line reads as all four.

Fix: "5.3-6.6 GB (gate form), one of four over 6,144".

**C1.** The "MB" labels on `host_rss_mb` are MiB (`ablation.py:618`, VmRSS kB/1024). The comparison with the
MiB limit is consistent. Only the labels are off.

**C2.** Quote the admitted slope at the GPU-measured baseline: about 0.83 MB/epoch at 2,374-2,389. The quoted
0.85-0.87 assumes the 2.1-2.2 GB W&B start RSS. The live K=3 arms are already at 2,301-2,469.

**C3.** The telemetry is Delta arm A, E at 350k, K=4, with Delta patches on 42abed4b. The pilot-b arms
(A07, C, F, C') are unmeasured until their own gate lines. The decision states this under "Production".

## Recomputed
- Δ threshold 630.7-641.3.
- Admitted slope 0.856-0.869 (0.829 at 2,389).
- Leak-fill epochs 63.5-76.1.
- Delta-input projections 5,438-6,713.
- F epoch-105 time ≈ 2.2 h.
- Manifest table, above.

## Competing-group question
A group running the same pilot would have measured RSS on its own arms before sizing. This campaign sizes
from one Delta K=4 run on a patched tree. That is justified as the only GPU data, and the in-code gate on
every arm checks it.

Next verification: after the swap, each arm's `[train] … resume_epoch=` line in the new pod's log, expected
25 or 50, followed by `RSS_GATE … limit_mb 8192` at that process's epoch 105.
