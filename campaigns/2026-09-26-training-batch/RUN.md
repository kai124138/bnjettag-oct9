# RUN — 2026-09-26-training-batch (pilot)

Nothing here is quotable. Launch record only; telemetry below is diagnostic, not a result.
W&B project `BNJetTag-ChangRecipe`, group `chang-n64-20260926-canary`
(https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe). ConfigMap
`kai-chang0926-code-77f1ca4e9f` (bundle sha `77f1ca4e9fe3f67ef276ec9b7c401c174812fcb2e88b7ef572040ad2e26f2a94`,
manifest sha `f7d4003f49584c701aec1cfefb4c0c9a3591c41d7d2fda94dd5a293d00eaaa36`). Authorized by Kai
2026-09-27 (`.claude/memory/decisions.md` top entries); PREFLIGHT gate v2 = PASS
(`review/PREFLIGHT_critical_v2.md`, commit `cdf3487`). Readout job and production are **out of
scope for this record** — not launched.

## Launch

```
$ kubectl apply -f campaigns/2026-09-26-training-batch/manifests/pilot-job.json -n cms-ml
job.batch/kai-chang0926-pilot-77f1ca created
```
2026-09-27T20:51:32Z. Pre-apply live lint (identical to the PREFLIGHT-recorded lint, re-run
immediately before this apply, exit 0, no WARN):
```
$ python3 nrp-lab/nrp_doctor.py lint campaigns/2026-09-26-training-batch/manifests/pilot-job.json
== campaigns/2026-09-26-training-batch/manifests/pilot-job.json :: kai-chang0926-pilot-77f1ca ==
  note   required pool = 4 products / 109 nodes cluster-wide
  note   no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate)
  note   [rule PACK] 6 arms per pod declared.
  OK
exit=0
```
Pre-apply `nrp_doctor.py status`: quota `requests.nvidia.com/a100 20/24`, no admission errors,
nothing of ours pending; one pre-existing WARN unrelated to this campaign
(`kai-confirm-onegpu-0924-e0c0a3-r2`, stale-failed-Job check, `cluster-inventory.md` 2026-09-26 —
not touched here).

Pod `kai-chang0926-pilot-77f1ca-0-2ffxx` scheduled and `Running` within ~16 s of apply, on
**node `hcc-nrp-shor-c5825.unl.edu`**, GPU **NVIDIA A10, 23,028 MiB**. From the pod log:
```
MANIFEST_SHA_OK f7d4003f49584c701aec1cfefb4c0c9a3591c41d7d2fda94dd5a293d00eaaa36
GPU_GATE_PASS
NVIDIA A10, 23028 MiB
```
matches the frozen bundle/manifest shas exactly. All 6 `ARM_STARTED` lines present within ~80 s
of pod start, matching the declared pack `[0, 1, 24, 48, 56, 57]`:
```
ARM_STARTED 0 chang0926-a-n64-s1 pid 74 attempt 0
ARM_STARTED 1 chang0926-a-n64-s2 pid 94 attempt 0
ARM_STARTED 24 chang0926-d-n64-s1 pid 115 attempt 0
ARM_STARTED 48 chang0926-a07-350-n64-s1 pid 642 attempt 0
ARM_STARTED 56 chang0926-cprime-n64-s1 pid 1408 attempt 0
ARM_STARTED 57 chang0926-e1-n64-s1 pid 1720 attempt 0
```
Per-arm `RUN_STAGE pilot` confirmed in each arm's own log (`/data/chang-n64-20260926/pilot/logs/
<arm>-<pod>.log` — `run_pack.py` redirects each child's stdout/stderr there and only tails a
crashed arm's log into the pod's own stdout; steady-state per-epoch lines are **not** visible via
`kubectl logs`, only in these per-arm files).

## Jobs

| job | arms (index → arm) | node | started (UTC) | state |
| --- | --- | --- | --- | --- |
| `kai-chang0926-pilot-77f1ca` | 0→A-s1, 1→A-s2, 24→D-s1, 48→A07-350-s1, 56→C′-s1, 57→E1-s1 | `hcc-nrp-shor-c5825.unl.edu` (NVIDIA A10, 23,028 MiB) | 2026-09-27T20:51:32Z (apply); pod Running by ~20:51:48Z | Running, 0/1 completions, as of 21:04 UTC (5/6 arms training, 1 permanently failed — see below) |

`parallelism: 1`, K=6 arms packed on the single pod's one GPU (declared
`bnjettag.io/arms-per-pod: "6"`, `[rule PACK]` lint OK) — the pack shape STUDY specifies for the
pilot, not a choice made at launch time.

## Per-arm state (as of 2026-09-27T21:04 UTC, ~13 min after launch)

| arm (idx) | attempts | epoch reached | s/epoch (obs.) | val_AUC (ep.1→3) | note |
| --- | --- | --- | --- | --- | --- |
| A-s1 (0) | 0 (clean) | 3/7000 | 218.8, 221.1, 216.1 | 0.822→0.892 | training, no errors |
| A-s2 (1) | 0 (clean) | 3/7000 | 219.4, 221.0, 215.8 | 0.835→0.879 | training, no errors |
| D-s1 (24) | 0 (clean) | 3/7000 | 219.5, 221.1, 210.7 | 0.832→0.851 | training, no errors |
| A07-350-s1 (48) | 0, 1, 2 — **all OOM** | 0/7000 | n/a | n/a | **`ARM_FAILED_AFTER_RETRIES`, permanently dropped from this pilot pod** — see incident |
| C′-s1 (56) | 0, 1 OOM; 2 running | in progress | n/a yet | n/a yet | resumed on 3rd (last) attempt after A07-350 freed VRAM; watch for a repeat OOM |
| E1-s1 (57) | 0 (clean) | 3/7000 | 164.7, 180.9, 132.6 | 0.850→0.882 | training, no errors; smallest model (params=19,447) |

Telemetry lines, verbatim, labelled **telemetry, not results** (validation split, no seeds, no
interval, pilot only):
```
[epoch 1/7000] EBOPs=11737590 target=350000 above_floor=11566064 feasible=0 degenerate=0 beta=1e-07 val_AUC=0.821802 val_accuracy=0.525984 seconds=218.8 checkpoint=-
[epoch 2/7000] EBOPs=11622721 target=350000 above_floor=11451195 feasible=0 degenerate=0 beta=1e-07 val_AUC=0.879425 val_accuracy=0.618952 seconds=221.1 checkpoint=-
[epoch 3/7000] EBOPs=9104870  target=350000 above_floor=8933344  feasible=0 degenerate=0 beta=1.18e-07 val_AUC=0.891914 val_accuracy=0.662048 seconds=216.1 checkpoint=-
```
(A-s1; the other clean arms follow the same shape — see per-arm log files on the PVC for full
text.) No `ebops_trace_seconds` / `ebops_trace_over_epoch` line has appeared yet in any arm's
log within this observation window; not recorded because not yet emitted, not because it was
skipped.

GPU: `nvidia-smi` inside the pod, sampled several times over the observation window while 5-6
arms were resident: **100 % utilization**, memory **18.8–22.6 GiB used of 23.0 GiB** — i.e. the
K=6 pack runs at or near the VRAM ceiling of this card even before accounting for the two arms
that OOM'd.

## Incidents and resumes

| when (UTC) | what | `cluster-inventory.md` entry | Check line |
| --- | --- | --- | --- |
| 2026-09-27 ~20:57–21:03 | `A07-350-s1` (idx 48) and `C′-s1` (idx 56) OOM on `RESOURCE_EXHAUSTED` during their attention/softmax quantizer path, K=6 pack on a 23 GiB A10, `batch: 2790`. `A07-350-s1` exhausted all 3 attempts (`RETRIES=2`) and is permanently dropped from this pilot pod (`ARM_FAILED_AFTER_RETRIES`); `C′-s1` survived on its 3rd attempt once `A07-350-s1`'s VRAM was freed. `run_pack.py`'s per-arm retry kept the other 4 arms and the pod alive throughout (does not share the 2026-09-26 `pack_runner_one_gpu.py` whole-container-death failure mode). | "K=6 pack, batch 2,790, two of six N64 arms OOM repeatedly on a 23 GiB A10 (2026-09-27)", `.claude/memory/cluster-inventory.md` | prose only (no lint rule yet checks per-arm GPU VRAM against the pool's smallest card) |

**No relaunch performed or proposed here.** Per instruction, this is diagnose-and-record only;
`A07-350-s1`'s loss is a per-arm gap in the pilot's data, not a dead Job — it does not block the
other 5 arms or the canary read. Whether/how to recover the A07-350 arm (smaller batch for that
arm alone, a higher-VRAM-floor pack, or dropping it from the pilot's read) is a call for whoever
reads the epoch-10 canary, not made here.

## Copy pod logs before Job TTL

`ttlSecondsAfterFinished: 604800` (7 days) on `kai-chang0926-pilot-77f1ca`. Per-arm logs live on
the PVC at `/data/chang-n64-20260926/pilot/logs/*.log` (durable, not lost with the pod), but the
pod's own stdout (`kubectl logs`) is not — copy it into the campaign directory before the pod is
garbage-collected.

## Stall-watchdog caveat

`run_pack.py` prints `ARM_STALLED_NO_PROGRESS <name> <age>s` and SIGTERMs/SIGKILLs an arm whose
heartbeat is older than `STALL_SECONDS`. In the first hour, a slow first epoch (data pipeline
warmup, XLA/graph compile, or GPU contention from 5-6 co-resident arms) can look like a stall
that is not one — do not treat a single `ARM_STALLED_NO_PROGRESS` in the first hour as
conclusive; check whether the arm's log is still advancing before acting on it.

## Canary and projections

The canary is read at **epoch 10** by cluster-ops, per STUDY. Projections below use the
clean-arm epoch-1-3 timings observed above (3 samples per arm, no seeds/interval — projection
only, not a result):

- **A/A-s2/D-s1** (~217-219 s/epoch, mean ≈ 218 s): epoch 10 ≈ 2,180 s (36 min) from arm start;
  **T_run = 7,000 × 218 s ≈ 1,526,000 s ≈ 17.7 days — over STUDY's 14-day rule.** Production at
  this per-epoch cost, for these arms, waits for Kai.
- **E1-s1** (~159 s/epoch, mean of 164.7/180.9/132.6): epoch 10 ≈ 1,594 s (27 min);
  **T_run = 7,000 × 159 s ≈ 1,116,000 s ≈ 12.9 days — under 14 days.**
- **A07-350-s1**: no clean epoch observed (all 3 attempts OOM'd before completing epoch 1); no
  projection possible from this pilot.
- **C′-s1**: only mid-3rd-attempt at time of writing; no completed epoch yet, no projection.

These four numbers do not average to one answer — the pack mixes at least two different
per-epoch costs, and two arms have no timing at all. STUDY v7 PASS and the canary read (epoch
10, all reachable arms) are what production launch actually waits on; this projection is only
early signal that the larger arms may already be over the 14-day budget.

## Canary (epoch 10) — telemetry, not results

Read 2026-09-27, live pod `kai-chang0926-pilot-77f1ca-0-2ffxx`, in-pod per-arm log files
(`/data/chang-n64-20260926/pilot/logs/*.log`), by `kubectl exec`. A-s1, A-s2, D-s1 reached
epoch 10 at ~21:32 UTC; E1-s1 was ahead (epoch 13 by 21:32, checked back to its epoch-10 line);
**C′-s1 had not reached epoch 10 within the 45-minute wait window** (launched 20:51:32Z, checked
through 21:34Z) — it is on its 3rd attempt (resumed after an OOM, `run_pack.py` retry), running
alone-ish at ~275–310 s/epoch (larger 5M-target A07 model, slower per-epoch than the E arms) and
was at epoch 5/7000 when this canary was closed out; **no epoch-10 read exists for C′-s1 in this
canary — reported at epoch 5 only, explicitly incomplete.** A07-350-s1 has no epoch-1 data at all
(OOM'd on all 3 attempts before completing an epoch; already recorded in
`cluster-inventory.md` 2026-09-27).

### s/epoch, epochs 1–10, and the [D20] trace

| arm | s/epoch (mean, ep.1–10) | s/epoch range |
| --- | --- | --- |
| A-s1 | 219.65 | 216.1–225.0 |
| A-s2 | 219.37 | 215.7–225.7 |
| D-s1 | 215.16 | 208.1–224.4 |
| E1-s1 | 163.88 | 132.6–180.9 |
| C′-s1 (ep.1–5 only) | 293.6 | 273.9–311.0 |

**No `ebops_trace_seconds` / `ebops_trace_over_epoch` line appears in any arm's log file through
epoch 10 (or beyond — checked E1 through epoch 13, C′ through epoch 5).** This is not "not yet
emitted": it is structural. `chang0926-a-n64-s1.json`'s `train` block carries
`"ebops_trace_sample": "train_full"`, so [D20] tracing **is configured on** (confirmed by reading
the shipped config, not inferred). But the per-epoch console/file print statement,
`code/tree/bnhgq2/ablation.py:783`, only formats `EBOPs`, `target`, `above_floor`, `feasible`,
`degenerate`, `beta`, `val_AUC`, `val_accuracy`, `seconds` and `checkpoint` — it never includes
`ebops_trace_seconds` or `ebops_trace_over_epoch`. Those two fields are written only into the
`logs` dict at `ablation.py:754-755`, gated on `if d20:`, which goes to W&B, not to the per-arm
`.log` file on the PVC. **Finding: the per-arm log file can never show the [D20] trace share of
s/epoch, regardless of whether the trace is running — the split into train-step vs.
overhead (validation, checkpointing, trace) that STUDY's canary asks for is not recoverable from
this log file at all; it would need the W&B history for these runs (not pulled here — no W&B
query was made, to avoid touching the run data before cluster-ops's own readout) or a print-
statement patch.** The elevated observed s/epoch (≈215–220 s vs. the 112.6 s A07 batch-256 prior,
and above the ≈187 s "1.66×" trace-cost projection in STUDY) is consistent with the trace running,
but that is circumstantial, not the split STUDY specifies.

### EBOPs, floor, β, val accuracy/AUC — epoch 1 vs. epoch 10

| arm | EBOPs ep.1 | EBOPs ep.10 | ep.10/ep.1 | above-floor ep.10 | floor | headroom-frac | β ep.1 → ep.10 | val_AUC ep.1 → ep.10 | val_acc ep.1 → ep.10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-s1 | 11,737,590 | 3,748,891 | 0.319 | 3,577,365 | 171,526 | ×20.0 headroom | 1e-7 → 1.13e-7 | 0.8218 → 0.8782 | 0.5260 → 0.6372 |
| A-s2 | 11,716,777 | 3,968,681 | 0.339 | 3,797,155 | 171,526 | ×21.3 | 1e-7 → 1.15e-7 | 0.8351 → 0.8753 | 0.5682 → 0.6102 |
| D-s1 | 11,780,922 | 3,482,967 | 0.296 | 3,311,441 | 171,526 | ×18.6 | 1e-7 → 1.14e-7 | 0.8321 → 0.8765 | 0.5454 → 0.6197 |
| E1-s1 | 10,685,614 | 3,542,254 | 0.332 | 3,456,491 | 85,763 | ×13.1 | 1e-7 → 1.19e-7 | 0.8499 → 0.8664 | 0.5762 → 0.6238 |
| C′-s1 (ep.1→5 only) | 17,947,790 | 10,471,913 (ep.5) | 0.583 (ep.5/ep.1) | 5,891,515 (ep.5) | 4,580,398 | n/a (target 5,000,000) | 1e-7 → 8.17e-8 (ep.5) | 0.8330 → 0.8860 (ep.5) | 0.5322 → 0.6418 (ep.5) |

Reference trajectory (STUDY, old-quantizer A07-N64 screen, seed 1): ratio epoch-9/epoch-0 = 0.31.
A/A-s2/D/E1's epoch-10/epoch-1 ratios (0.30–0.34) sit in the same band.

**Stability checks against STUDY's canary fail-numbers:**
- **EBOPs epoch 10 < epoch 1, every arm:** pass for A-s1, A-s2, D-s1, E1-s1 (see ratios above).
  Not evaluated for C′-s1 (no epoch-10 data) or A07-350-s1 (no data at all, dropped).
- **β differs from initial 1e-7 at epoch 10 (PID moving):** pass and rising for A-s1, A-s2,
  D-s1, E1-s1 (1e-7 → 1.13–1.19e-7). **Not evaluated for C′-s1** (only to epoch 5): its β fell
  first (1e-7 → 8.02e-8 at ep.4) then ticked up slightly (8.17e-8 at ep.5) — moving, but not yet
  clearly "rising" the way the E arms are; consistent with its much larger 5,000,000 target
  leaving more headroom early. Flagged, not a failure, since C′-s1 has no epoch-10 read here.
- **Loss finite, epoch-10 train loss < epoch-1 train loss (A, D):** **cannot be checked from
  this log.** The per-epoch print at `ablation.py:783` never includes a train-loss field (`loss`,
  `task_loss`, `distillation_loss` are written only to the `logs` dict for W&B, same gap as the
  trace fields). No non-finite value was seen in anything the log does print (EBOPs, val_AUC,
  val_accuracy all finite and numeric at every epoch, every arm, through the read window) — that
  is as far as this artifact supports; it is not the same claim as "train loss finite."

### GPU / host / storage, sampled repeatedly over the window (2026-09-27 21:04–21:34 UTC)

- **GPU:** steady **100 % utilization**, memory **21.08–21.09 GiB of 23.03 GiB** used throughout
  (stable, no growth once C′-s1's 3rd attempt settled) — pod-level peak observed in this window
  is 21,094 MiB.
- **Per-process GPU memory (nvidia-smi `--query-compute-apps`, stable across samples):** A-s1
  (pid 74) 4,354 MiB; A-s2 (pid 94) 4,354 MiB; D-s1 (pid 115) 4,354 MiB; E1-s1 (pid 1720)
  2,830 MiB; C′-s1 3rd attempt (pid 4297) 5,172 MiB.
- **Host RAM:** 503 GiB total, 90 GiB used, 413 GiB available (`free -h`, in-pod).
- **CPU:** 12 cores visible in-pod (`nproc`).
- **Per-arm log file sizes** (bytes, at last read): A-s1 2,032; A-s2 2,032; D-s1 2,067; E1-s1
  2,537 (further ahead); C′-s1 23,529 (includes retry noise from 2 failed attempts);
  A07-350-s1 26,103 (3 failed attempts, no clean epoch).
- **Checkpoint sizes** (`model_min_ebops.keras` / `model_unconstrained.keras` /
  `validation_candidate.keras`, all three the same size per arm): A-s1/A-s2/D-s1 498 KiB each;
  E1-s1 430 KiB; C′-s1 433 KiB.
- **`df -h /data`:** 100 GiB PVC, 33 GiB used, 68 GiB available, 33 % — unchanged from the
  pre-launch read; nothing about this pilot is close to filling `kai-data`.

### Projections

- **T_run = 7,000 × s_e** (measured mean s/epoch over epochs 1–10, or 1–5 for C′): A-s1
  ≈ 1,537,550 s ≈ **17.8 d**; A-s2 ≈ 1,535,590 s ≈ **17.8 d**; D-s1 ≈ 1,506,120 s ≈ **17.4 d**;
  E1-s1 ≈ 1,147,160 s ≈ **13.3 d**; C′-s1 (5-epoch basis only, not a full epoch-10 canary) ≈
  7,000 × 293.6 s ≈ 2,055,200 s ≈ **23.8 d**. **A-s1, A-s2, D-s1 and C′-s1 are all over STUDY's
  14-day rule; only E1-s1 fits.** This confirms and sharpens the epoch-1–3 projection already in
  this file; production at this per-epoch cost, for the E-architecture arms, waits for Kai per
  [D15]/the pre-registered rule.
- **K=3 / K=4 projections: no measured basis exists — not attempted.** This pilot pod has only
  ever run at declared K=6 (currently 4 arms training cleanly + 1 recovering + 1 permanently
  dropped, i.e., 5 processes resident, not a deliberate K=4 pack). Extrapolating s/epoch from K=6
  to K=3/K=4 would assume GPU-contention scaling this pilot does not measure. **Not reported as a
  number; STUDY's own K=3 fallback (if K=6 doesn't fit) is a re-run, not an arithmetic
  projection, and that re-run has not happened.**
- **Whether K=6 fits A10 memory for the E arms alone:** **no — by extrapolation, not measurement,
  and flagged as such.** The three same-size E arms currently resident (A-s1, A-s2, D-s1) each
  use ≈4,354 MiB; E1-s1 (single-head, smaller) uses 2,830 MiB. Six same-size arms at the A-s1/
  A-s2/D-s1 footprint would need ≈6 × 4,354 ≈ 26,124 MiB, already ≈3.1 GiB over the A10's
  23,028 MiB before counting CUDA-context/framework overhead — and the pod is already at
  21,094 MiB with only 3 such arms plus E1 (2,830 MiB) plus C′'s one recovering process
  (5,172 MiB). This is consistent with why A07-350-s1 and C′-s1 (the two largest models in the
  pack) OOM'd at K=6 (`cluster-inventory.md` 2026-09-27), but it also says a K=6 pack of the
  *smaller* E arms alone is not obviously safe either — nobody has run that combination to check
  it directly.

## Canary — W&B history pull (2026-09-27, read-only)

Source: W&B API, project `kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe` (PRIVATE), group
`chang-n64-20260926-canary`, `run.scan_history()` on the 5 target runs
(`chang0926-a-n64-s1`=A-s1, `chang0926-a-n64-s2`=A-s2, `chang0926-d-n64-s1`=D-s1,
`chang0926-cprime-n64-s1`=C'-s1, `chang0926-e1-n64-s1`=E1-s1). No write made. This is the
missing split that the per-arm PVC log files cannot show (see prior section): `ablation.py:754-755`
writes `ebops_trace_seconds` / `ebops_trace_over_epoch` / `loss` (train loss) only into the
`logs` dict passed to W&B, never into the `ablation.py:783` per-epoch print. Fields pulled per
epoch: `epoch_seconds`, `ebops_trace_seconds`, `ebops_trace_over_epoch`, `loss` (train, total),
`task_loss`, `ebops`, `ebops_above_floor`, `target_ebops`, `beta`, `val_auc_0`.
train-step time = `epoch_seconds` − `ebops_trace_seconds` (validation is not logged as a
separate field; this remainder therefore bundles train-step + validation + checkpoint overhead,
not train-step alone).

### A-s1 (epochs 0–9)
| ep | epoch_s | trace_s | trace_frac | train-step+val_s | loss (finite) | EBOPs | above-floor |
|---|---|---|---|---|---|---|---|
| 0 | 218.76 | 78.49 | 0.359 | 140.27 | 2.7120 Y | 11,737,590 | 11,566,064 |
| 1 | 221.09 | 77.24 | 0.350 | 143.86 | 2.2788 Y | 11,622,721 | 11,451,195 |
| 2 | 216.11 | 93.67 | 0.434 | 122.44 | 2.2645 Y | 9,104,870 | 8,933,344 |
| 3 | 221.20 | 87.61 | 0.396 | 133.60 | 2.0321 Y | 8,949,610 | 8,778,084 |
| 4 | 225.01 | 94.22 | 0.419 | 130.78 | 1.9853 Y | 7,266,651 | 7,095,125 |
| 5 | 216.74 | 94.44 | 0.436 | 122.30 | 1.8792 Y | 6,328,804 | 6,157,278 |
| 6 | 216.48 | 88.15 | 0.407 | 128.33 | 1.7240 Y | 5,456,991 | 5,285,465 |
| 7 | 220.35 | 92.19 | 0.419 | 128.15 | 1.6346 Y | 4,811,667 | 4,640,141 |
| 8 | 222.62 | 97.24 | 0.437 | 125.38 | 1.5412 Y | 4,047,622 | 3,876,096 |
| 9 | 218.16 | 95.20 | 0.437 | 122.96 | 1.4551 Y | 3,748,891 | 3,577,365 |
Target 350,000; all EBOPs above floor at ep.9. Train loss finite and monotone-decreasing every
epoch (2.712→1.455).

### A-s2 (epochs 0–9)
| ep | epoch_s | trace_s | trace_frac | train-step+val_s | loss (finite) | EBOPs | above-floor |
|---|---|---|---|---|---|---|---|
| 0 | 219.38 | 79.08 | 0.361 | 140.30 | 2.6230 Y | 11,716,777 | 11,545,251 |
| 1 | 221.01 | 77.03 | 0.349 | 143.98 | 2.3134 Y | 11,753,661 | 11,582,135 |
| 2 | 215.82 | 95.31 | 0.442 | 120.51 | 2.2991 Y | 8,473,706 | 8,302,180 |
| 3 | 222.10 | 87.97 | 0.396 | 134.13 | 1.9224 Y | 8,615,608 | 8,444,082 |
| 4 | 225.69 | 94.80 | 0.420 | 130.89 | 1.9248 Y | 7,007,169 | 6,835,643 |
| 5 | 218.07 | 95.07 | 0.436 | 123.00 | 1.8043 Y | 6,519,024 | 6,347,498 |
| 6 | 216.80 | 88.14 | 0.407 | 128.66 | 1.7325 Y | 5,419,166 | 5,247,640 |
| 7 | 220.97 | 92.39 | 0.418 | 128.58 | 1.6423 Y | 4,894,441 | 4,722,915 |
| 8 | 215.68 | 91.09 | 0.423 | 124.59 | 1.5727 Y | 4,117,096 | 3,945,570 |
| 9 | 218.08 | 94.54 | 0.434 | 123.54 | 1.5080 Y | 3,968,681 | 3,797,155 |
Target 350,000. Train loss finite, decreasing (small blip ep.2→3 in EBOPs, not loss).

### D-s1 (epochs 0–9)
| ep | epoch_s | trace_s | trace_frac | train-step+val_s | loss (finite) | EBOPs | above-floor |
|---|---|---|---|---|---|---|---|
| 0 | 219.51 | 78.44 | 0.358 | 141.07 | 2.6911 Y | 11,780,922 | 11,609,396 |
| 1 | 221.07 | 77.17 | 0.349 | 143.90 | 2.3049 Y | 11,712,062 | 11,540,536 |
| 2 | 210.70 | 87.05 | 0.413 | 123.65 | 2.2881 Y | 9,134,071 | 8,962,545 |
| 3 | 214.43 | 81.37 | 0.380 | 133.06 | 2.0485 Y | 8,950,228 | 8,778,702 |
| 4 | 224.40 | 97.42 | 0.434 | 126.98 | 1.9817 Y | 7,401,908 | 7,230,382 |
| 5 | 210.34 | 100.71 | 0.479 | 109.63 | 1.8582 Y | 6,010,698 | 5,839,172 |
| 6 | 210.26 | 93.86 | 0.447 | 116.40 | 1.6646 Y | 5,519,769 | 5,348,243 |
| 7 | 224.24 | 97.04 | 0.433 | 127.20 | 1.6035 Y | 4,490,378 | 4,318,852 |
| 8 | 208.05 | 107.91 | 0.519 | 100.14 | 1.4477 Y | 4,102,654 | 3,931,128 |
| 9 | 208.62 | 103.42 | 0.496 | 105.20 | 1.4340 Y | 3,482,967 | 3,311,441 |
Target 350,000. Train loss finite, decreasing.

### C′-s1 — epochs 0–4 only (3rd attempt after 2 OOMs; had not reached epoch 10 in the observation
window; consistent with RUN.md's earlier note)
| ep | epoch_s | trace_s | trace_frac | train-step+val_s | loss (finite) | EBOPs | above-floor |
|---|---|---|---|---|---|---|---|
| 0 | 273.90 | 113.00 | 0.413 | 160.89 | 3.6337 Y | 17,947,790 | 13,367,392 |
| 1 | 308.22 | 133.11 | 0.432 | 175.11 | 2.7954 Y | 17,808,464 | 13,228,066 |
| 2 | 292.26 | 149.18 | 0.511 | 143.08 | 2.6566 Y | 12,888,831 | 8,308,433 |
| 3 | 282.79 | 122.48 | 0.433 | 160.31 | 1.9356 Y | 12,538,431 | 7,958,033 |
| 4 | 310.96 | 134.01 | 0.431 | 176.95 | 1.8578 Y | 10,471,913 | 5,891,515 |
Target 5,000,000; above-floor still 5.9M at ep.4 (target not yet met, expected this early on the
larger model). Train loss finite, decreasing. No epoch-5–9 data — no epoch-10 read possible.

### E1-s1 — epochs 0–13 (ahead of the others; reported through ep.9 for parity, full run given)
| ep | epoch_s | trace_s | trace_frac | train-step+val_s | loss (finite) | EBOPs | above-floor |
|---|---|---|---|---|---|---|---|
| 0 | 164.66 | 67.91 | 0.413 | 96.75 | 2.5889 Y | 10,685,614 | 10,599,851 |
| 1 | 180.91 | 85.07 | 0.471 | 95.84 | 2.1060 Y | 10,548,061 | 10,462,298 |
| 2 | 132.60 | 84.16 | 0.635 | 48.45 | 2.1525 Y | 8,332,998 | 8,247,235 |
| 3 | 157.39 | 78.97 | 0.502 | 78.42 | 1.9074 Y | 8,239,031 | 8,153,268 |
| 4 | 179.94 | 81.06 | 0.451 | 98.89 | 1.9164 Y | 6,837,675 | 6,751,912 |
| 5 | 164.81 | 91.73 | 0.557 | 73.08 | 1.8267 Y | 6,277,643 | 6,191,880 |
| 6 | 153.75 | 85.91 | 0.559 | 67.84 | 1.7037 Y | 5,553,108 | 5,467,345 |
| 7 | 160.78 | 78.82 | 0.491 | 81.96 | 1.7002 Y | 4,682,954 | 4,597,191 |
| 8 | 169.64 | 75.83 | 0.447 | 93.80 | 1.5616 Y | 3,942,254 | 3,856,491 |
| 9 | 174.38 | 87.82 | 0.504 | 86.56 | 1.4648 Y | 3,542,254 | 3,456,491 |
Target 350,000. Train loss finite, decreasing (small blip ep.1→2). (ep.10–13 continue the same
pattern in W&B, not tabulated here — not needed for the epoch-10 canary.)

### Trace share and projections — telemetry, not results

- **Median [D20] trace share of epoch, A-s1/A-s2/D-s1 pooled, ep.0–9 (30 values): 0.420.** The
  trace consistently costs ~40–44% of the A-arm epoch, confirming the earlier "circumstantial"
  note in this file — with the split now measured directly from W&B, not inferred.
- **T_run = 7,000 × s_e, measured mean s/epoch pooled over A-s1/A-s2/D-s1, ep.0–9 (218.06 s):
  1,526,400 s ≈ 17.67 days.** Matches the per-arm 17.4–17.8 d already in this file to within
  rounding (pooled vs. per-arm mean).
- **Projection, trace run only every k epochs (k=5, 10, 25) — arithmetic from the measured
  split (mean trace_s = 90.61 s, mean train-step+val_s = 127.45 s over the same 30 epoch-samples),
  amortizing trace cost as `trace_s / k` per epoch. Projection only, not a measurement — no run
  has actually been configured this way:**
  - k=5: s_e ≈ 145.6 s → T_run ≈ 1,019,000 s ≈ **11.8 days**
  - k=10: s_e ≈ 136.5 s → T_run ≈ 955,600 s ≈ **11.1 days**
  - k=25: s_e ≈ 131.1 s → T_run ≈ 917,500 s ≈ **10.6 days**
  All three bring the A-arms under STUDY's 14-day rule; k=5 already does. This is a projection
  from the measured epoch split, not a run of the trace-every-k-epochs configuration.

### GPU memory (W&B system metrics)

W&B's `system.gpu.0.*` stream is **per-pod, not per-process** — all 5 runs (sharing one A10
pod) report the identical pod-wide counter, not a per-run breakdown. Max observed pod-wide
`memoryAllocatedBytes` across the pull: **23,663,017,984 bytes ≈ 22.04 GiB** (97.9–98.0% of the
pod's visible GPU memory), consistent with the in-pod `nvidia-smi` peak (21.09 GiB) and
per-process breakdown already recorded in this file above (`nvidia-smi --query-compute-apps`
is the only per-process source; W&B does not disaggregate by process for a shared-GPU pod).
Max `system.gpu.0.memory` (utilization) 97–100% across all 5 runs' windows — consistent with
the "100% utilization" already logged from in-pod sampling.

## Health check, 2026-09-28 05:12 UTC (read-only, cluster-ops)

Job `kai-chang0926-pilot-77f1ca` still `active=1` on pod `kai-chang0926-pilot-77f1ca-0-2ffxx`,
node `hcc-nrp-shor-c5825.unl.edu` (A10), pod up 8.3h. `nrp_doctor.py status`: no pending, no
admission errors. Read via `kubectl exec` into per-arm logs at
`/data/chang-n64-20260926/pilot/logs/*.log`, `ps aux`, `nvidia-smi`, `df -h /data`.
`kubectl logs` copied to `campaigns/2026-09-26-training-batch/logs/pilot-77f1ca-20260928T0512Z.log`
before the 7-day Job TTL.

**Only 3 of the pilot's 6 arms are alive.** `ps aux` inside the pod shows exactly 3
`run_study.py train` processes (`--index 0`, `--index 1`, `--index 24` — A-s1, A-s2, D-s1);
`A07-350-s1` was already dead (recorded 2026-09-27, unrelated OOM incident).

**Real cause, read from the pod's own `kubectl logs`** (saved to
`campaigns/2026-09-26-training-batch/logs/pilot-77f1ca-20260928T0512Z.log`; per-arm `.log`
files on the PVC do not show this — it is `run_pack.py`'s own stdout): at **2026-09-28
~01:32:30–01:35Z** (≈4h41m after launch), the **stall watchdog fired on four of the five
still-live arms nearly simultaneously** —
```
ARM_STALLED_NO_PROGRESS chang0926-a-n64-s1 1802 s
ARM_STALLED_NO_PROGRESS chang0926-a-n64-s2 1847 s
ARM_STALLED_NO_PROGRESS chang0926-e1-n64-s1 1914 s
ARM_STALLED_NO_PROGRESS chang0926-cprime-n64-s1 1903 s
```
followed by `ARM_EXIT <name> -9 attempt 0` (A-s1, SIGKILL) / `143 attempt 0` (A-s2, E1-s1,
SIGTERM) / `143 attempt 2` (C′-s1, on what was already its 3rd attempt after the earlier OOMs).
This is **not** OOM — no `ResourceExhaustedError` appears anywhere near this window in any of
the four arms' per-arm log files. **A-s1 and A-s2 restarted cleanly** (`ARM_ATTEMPT 1` at
01:33:28Z and 01:33:58Z respectively) from their last checkpoint (`epoch-0050` for both) and
are alive and training now, with **no data loss** — training resumed at epoch 51, matching the
brief's requirement to record any retry/restart, which the first cut of this section omitted.
**C′-s1 and E1-s1 also restarted** but then failed again within the same watchdog window
(`ARM_EXIT chang0926-e1-n64-s1 143 attempt 1` → stalled again at 2022s → `ARM_EXIT ... -15
attempt 2` → `ARM_FAILED_AFTER_RETRIES chang0926-e1-n64-s1` at 01:35:30Z; C′-s1's 3rd/last
attempt from the 2026-09-27 OOM incident was itself consumed by this same stall, so it read
`ARM_FAILED_AFTER_RETRIES chang0926-cprime-n64-s1` at 01:34:28Z) — **both dead because they had
already spent attempts on the 2026-09-27 OOM incident and had no attempts left when the stall
hit, not because of a second OOM.** `D-s1` (idx 24, `ps aux` PID 115, running continuously
since 20:53:46Z, never restarted) was not touched by this stall at all — no
`ARM_STALLED_NO_PROGRESS` line for it anywhere in the pod log.

**This corrects the first draft of this section**, which misread the per-arm `.log` files'
trailing `ResourceExhaustedError` blocks (both from the already-recorded 2026-09-27 OOM
incident, attempts 0/1) as proof of a *third* OOM, and consequently also missed that A-s1/A-s2
were themselves killed and restarted by the same event. It also corrects the 2026-09-27
cluster-inventory entry, which read `cprime-n64-s1` as having "survived on its third attempt"
at OOM — true as of that read, but its third attempt was then separately consumed by this
01:32 stall, which that entry could not have known about.

**Root cause of the stall itself is not established here** — `nrp_doctor.py` and the pod log do
not say why four arms' heartbeats went quiet for ~30–34 minutes at the same time (candidates:
CephFS/PVC I/O contention from near-simultaneous checkpoint writes, though the four arms were
not all at round checkpoint epochs at that time; general host contention; a runner-side false
positive per the existing stall-watchdog caveat below, though this was 4.7h in, not the "first
hour" the caveat is about). Flagged as an open question, not resolved.

| arm | status | restarts | last epoch | s/epoch (recent) | EBOPs (latest) | target | above_floor | crossed target? | β | val_AUC | val_acc |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A-s1 | alive | 1× (stall-killed @ep.50, resumed ep.51, 01:33:28Z) | 145/7000 | ~127–136 s | 440,289 | 350,000 | 268,763 | no | 8.46e-07 | 0.7732 | 0.4326 |
| A-s2 | alive | 1× (stall-killed @ep.50, resumed ep.51, 01:33:58Z) | 145/7000 | ~130–140 s | 475,119 | 350,000 | 303,593 | no | 9.66e-07 | 0.7647 | 0.4520 |
| D-s1 | alive | 0 (running continuously since 20:53:46Z) | 167/7000 | ~127–141 s | 436,569 | 350,000 | 265,043 | no | 1.24e-06 | 0.7690 | 0.4353 |
| C′-s1 | **dead** (`ARM_FAILED_AFTER_RETRIES` 01:34:28Z — attempts spent: 2 on the 2026-09-27 OOM, 3rd consumed by the 01:32 stall, not a 3rd OOM) | — | 47/7000 (last written) | 280–312 s (while alive) | 6,418,622 | 5,000,000 | 1,838,224 | no (never) | 9.03e-08 | 0.8883 | 0.6279 |
| E1-s1 | **dead** (`ARM_FAILED_AFTER_RETRIES` 01:35:30Z — all 3 attempts consumed by the 01:32 stall, no prior OOM for this arm) | — | 88/7000 (last written) | 155–174 s (while alive) | 445,720 | 350,000 | 359,957 | no (never) | 2.70e-07 | 0.8169 | 0.5021 |

None of the 5 traced arms reached its EBOPs target before either dying or the read cutoff — all
still `feasible=0`, `above_floor > 0`.

**GPU / disk (in-pod, 05:12 UTC):** 1× A10, 100% util, 13,259 / 23,028 MiB used (3 live
processes, ~4.4 GiB each) — comfortably inside the 23 GiB card now that 2 of the original 6
processes are gone. `df -h /data`: 33G used / 100G, 68G avail, 33% — no disk pressure.

**Projected wall time to epoch 500 (surviving arms only, current epoch → 500, at each arm's
recent s/epoch; projection, not a result):**
- A-s1: 355 epochs × ~130 s ≈ 46,150 s ≈ **12.8 h** from this read.
- A-s2: 355 epochs × ~136 s ≈ 48,280 s ≈ **13.4 h**.
- D-s1: 333 epochs × ~132 s ≈ 43,956 s ≈ **12.2 h**.
- C′-s1, E1-s1: no projection — both are dead; STUDY's epoch-500 pause point is unreachable
  for these two arms without a relaunch decision (Kai's call, not made here). Checkpoints exist
  for both (`epoch-0025` for C′-s1, `epoch-0075` for E1-s1) per the resume-guard contract in
  the setup doc's "Recovering a dead campaign" — a relaunch would resume from there, not from
  epoch 0.

**Not done here (read-only brief):** no restart, patch, apply or delete. Recorded in
`.claude/memory/cluster-inventory.md` 2026-09-28.

**Correction to this section's "no data loss" claim.** A-s1 and A-s2 replayed epochs 51–69 after
their stall-restart (checkpoint `epoch-0050`, resumed at epoch 51); on resume, W&B rejected those
steps, so **W&B history for epochs 51–69 belongs to the abandoned pre-stall attempt**, while the
on-disk checkpoints/logs for those epochs are the replay. This is a duplication/attribution gap
between W&B and disk for that epoch range, not "no data loss" as first written.

**Correction to this section's "root cause of the stall itself is not established" claim.** The
cause is now established: `review/INCIDENT_stall_20260928.md` traces it to a host-memory leak of
about 80–95 MB per epoch per arm, which reached the pod's cgroup memory limit; the kernel
thrashed page cache with no swap and no OOM kill, and GPU sat at 0 % while the pod was
memory-bound. See `.claude/memory/cluster-inventory.md` 2026-09-28 (top entry) for the full
signature and the two checks proposed against it (not built).

**Regime-A pilot marked descriptive-only.** Per the STUDY regime-B amendment ([D15] branch,
Kai's choice of regime B — [D20] trace every 10 epochs, K=5 wave-1 packing), this regime-A pilot
pod (`kai-chang0926-pilot-77f1ca`, K=6) is descriptive only and does not bind production
decisions; the canary and epoch-500 reads that matter are the regime-B pilot's.

`C′-s1` and `E1-s1` have **no pilot data (regime A)** — both were already dead
(`ARM_FAILED_AFTER_RETRIES`) before this Job was stopped, and this pilot is descriptive-only, so
neither arm carries any regime-A pilot evidence forward.

## Stopped 2026-09-28T05:31Z

Kai decided to stop the pilot: the orchestrator deleted Job `kai-chang0926-pilot-77f1ca` at
2026-09-28T05:31Z, ahead of the watchdog sweep expected at about 05:46Z. Reason: the pod had hit
its 36 Gi memory-cgroup limit again, GPU at 0 %, and no arm could reach the STUDY epoch-500 pause
point.

**Cause:** the same host-memory leak recorded above and in `.claude/memory/cluster-inventory.md`
2026-09-28 (top entry) — established, `review/INCIDENT_stall_20260928.md` — about 80–95 MB per
epoch per arm, reaching the cgroup limit with no swap and no OOM kill, GPU idle at 0 % while
memory-bound. A second defect from the same incident: relaunched arms inherit stale heartbeat
mtimes from before the restart, and the retry budget is charged pod-wide, not per-arm-attempt.

**Checkpoints at stop** (`latest.json`, PVC): A-s1 epoch-0125, A-s2 epoch-0125, D-s1 epoch-0150,
E1-s1 epoch-0075, C′-s1 epoch-0025.

**Saved evidence:** last pod log
`campaigns/2026-09-26-training-batch/logs/pilot-77f1ca-20260928T0531Z-prestop.log`, captured
before deletion.

**Verified gone:** `kubectl get jobs,pods -n cms-ml` at 2026-09-28T05:33:58Z shows no
`kai-chang0926-pilot-77f1ca` Job or pod; only `kai-chang0926-cache-c5d6f0` (Complete, unrelated
cache job) remains in the namespace.

**Not done here:** no relaunch performed or proposed in this entry. Per instruction, this
section is diagnose-and-record only.

## Regime-B pilot: operating rules (gate v4 B1-B3, cluster-ops, 2026-09-28T23:04Z, before apply)

Authorization: Kai, `.claude/memory/decisions.md` 2026-09-28 "A10 only, launch once the fixes
pass a quick check"; PREFLIGHT gate v4 = PASS, `review/PREFLIGHT_critical_v4.md`. Scope: the two
pilot-b Jobs only (`pilot-b-k5-job.json`, `pilot-b-k3-job.json`). The six fallback Jobs and both
readout Jobs are linted (PREFLIGHT.md) but **not applied** in this action, and nothing production.

**B1 — exit-10 recovery (`DIVERGED.json` markers stay on the PVC).**
- The wrapper's epoch-0 check (`PACK_EPOCH0_CHECK` / `POD_EPOCH0_ALL_DIVERGED`) exits 10 only
  when *every* arm of a pod's pack diverged at epoch 0. `podFailurePolicy` treats exit 10 as
  `FailJob` (not retried), and `run_pack.py`'s marker skip (`DIVERGED.json`,
  `VERIFIED_COMPLETE.json`) means a re-applied Job with the same arm names would see those
  markers and skip every arm — silently doing nothing.
- Recovery: before any re-apply after an exit-10 pod, move (never delete) each affected arm's
  `runs/<arm>/DIVERGED.json` into a dated `runs/<arm>/abandoned-<UTC>/` directory on the PVC,
  then re-apply under a new Job name per the setup doc's "Recovering a dead campaign" recipe
  (same ConfigMap/config/root/arm names, Job shape fixed only).
- If only *some* arms of a pack NaN at epoch 0, `E0` is 0 (not all diverged) and the pod is not
  failed by this path — those arms are recorded as ordinary `DIVERGED.json` divergences. Read
  each arm's per-run log for an epoch-0 NaN pattern before assuming a healthy pack.
- The fingerprint gate does **not** catch the c6017 fault (Delta `REGRESSION_TICKET.md` §8: both
  discriminator pods, including one on c6017, passed `FINGERPRINT_OK` cleanly — the gate is a
  single-process init check, but the canary's actual failure mode needs 4-5 concurrent training
  processes sharing one GPU, a condition the single-process gate does not create). That is why
  c6017 stays on the `NotIn` exclusion list in both pilot-b Jobs as a precaution regardless of the
  fingerprint gate's presence, per Kai's decision (§8: "kept ... as a precaution, not because this
  result proves the node itself defective"). The fast signal for this fault class, if c6017's
  exclusion is ever lifted, is the per-arm epoch-0 divergence markers plus the wrapper's loud
  phase failure, not the fingerprint gate.

**B2 — fallback timing (K=3 OOM fallback race).**
- Before applying any `pilot-b-fb*-job.json`, confirm `kubectl -n cms-ml get job
  kai-chang0926-pilotb3-42abed` returns NotFound (the K=3 Job was deleted per PREFLIGHT's OOM
  procedure), then wait at least 15 minutes before applying a fallback.
- The fallback script's own `ARM_STILL_LIVE <run>` guard (PREFLIGHT.md "B, flag 4") reads whether
  the arm's `latest.json` or `activation_widths.jsonl` mtime changed in the last 15 min; applying
  before that window clears risks a false "still live" exit 1, or worse, two writers on the same
  `runs/<arm>/` if the K=3 Job's pod is still finishing a checkpoint write.

**B3 — readout timing.**
- Apply `readout-b5-job.json` or `readout-b3-job.json` only after the corresponding pilot-b Job
  has reached a terminal state (`Complete`/`Failed`, all pods gone) or been explicitly deleted.
- A non-empty `missing=` field in the readout's final `READOUT_JOB_DONE certify_exit=… a26_exit=…
  missing=…` line means "not done" — do not treat a `certify_exit=0` with a non-empty `missing=`
  as a clean readout. A07-350-s1 (the K=3 pod's first arm) gates production packs 7-10: those
  packs do not start until A07-350-s1's readout is unambiguous.

**Also recorded here (not new, from PREFLIGHT, restated for this launch):**
- **Epoch-10/20 RSS stop rule.** Stop the Job (`kubectl -n cms-ml delete job $J`, not the pod) if
  `rss20 + (rss20 - rss10)/10 * 85 > 8192` MiB for any arm. Read at process epochs 10 and 20
  (about 25 and 50 min after `ARM_STARTED` at ~150 s/epoch) using the commands and
  `manifests/rss_rule_epoch10_20.awk` given in PREFLIGHT.md ("B, flag ... epoch-10/20").
  - 2026-09-28 (ml-engineer, coordinator brief): constant 6144 → 8192 MiB with the 8 GiB per-arm
    resize (PREFLIGHT.md 'Per-arm memory 8 GiB'; decisions.md 2026-09-28). A pod still running the
    6 GiB manifests keeps its in-code gate at 6,144 until it is swapped, per the next bullet.
- **8 GiB swap timing (2026-09-28, ml-engineer, coordinator brief; revised per PREFLIGHT gate v5,
  `review/PREFLIGHT_critical_v5.md`, ITERATE on this item only, 2026-09-28T23:50Z).** The
  re-generated `pilot-b-k5/k3/fb*` manifests request K × 8 Gi and export
  `BNJ_RSS_GATE_LIMIT_MB=8192`; Job names, bundle, run root and stage are unchanged. The gate limit
  and pod memory enter no resume sha (PREFLIGHT.md 'Per-arm memory 8 GiB'), so a re-apply on the
  same run root resumes cleanly.
  - **Pods still Pending** when the 8 GiB manifests pass their gate: delete the Job and re-apply
    the 8 GiB manifest. Nothing has started. (Done for the K=5 pod 2026-09-28T23:45Z: see the
    launch table below.)
  - **Pods already scheduled (the running K=3 pod): the swap is unconditional, but not before an
    earliest time (gate v5 A1).** `ablation.py:710-711` raises `RuntimeError('History exists
    without a committed checkpoint')` if the Job is deleted and re-applied before an arm has
    `latest.json` (first checkpoint, `checkpoint_every_epochs: 25`). As of the v5 read (23:38-
    23:45Z) no K=3 arm has `latest.json` yet, only `activation_widths.jsonl`. **A1 — earliest
    swap time:** wait until every arm in the pod (A07-350-s1, C-s1, F-s1) has `latest.json`. C-s1
    and A07-350-s1 are the slowest at 116.7-125.3 s/epoch (v5 live read), so their first 25-epoch
    checkpoint lands at about 2026-09-29T00:22Z. Confirm each arm's `latest.json` from the pod
    before deleting; do not swap on an epoch-20 RSS read alone. **A2 — latest safe time:** the
    deadline is computed from the fastest arm's own measured rate, not a fixed 3-4.4 h window.
    F-s1 is fastest at 72.9-76.0 s/epoch (v5 live read); at that rate F-s1 reaches process epoch
    105 about 2.2 h after its `ARM_STARTED`, around 2026-09-29T01:40Z. A swap timed off the
    original ~3-4.4 h / 104-150 s/epoch estimate is about 1 h late for F-s1 and risks it hitting
    the 6,144 gate (exit 5, not retried) before the swap lands. **Safe window: about
    2026-09-29T00:25Z-01:35Z.** Re-measure the fastest arm's s/epoch at swap time rather than
    trusting this window if it has drifted.
  - **The swap is unconditional (gate v5 B1).** Every arm is expected to be flagged (see the
    `OVER8192` paragraph below), so there is no "if any arm is not OK" branch to evaluate: inside
    the A1/A2 window above, delete the K=3 Job once. `rss_proj7000_epoch20.awk`'s
    `RSS_PROJ7000 ... OK|OVER6144|OVER8192 ... projection_mb` output is **informational only** —
    it does not gate the swap decision and is not evidence for or against the unconditional call.
  - **"Confirm NotFound" means the pod, not just the Job (gate v5 B1).** `kubectl delete job` uses
    background propagation: the Job object goes before its pod terminates. Before re-applying,
    confirm `kubectl -n cms-ml get pods -l job-name=<job>` returns no resources — a bare `get job
    <job>` returning NotFound is not sufficient. The K=3 manifest has no `ARM_STILL_LIVE` guard
    (only the fb* manifests have one); the only other protection against two writers on the same
    `runs/<arm>/` is `run_study.py`'s `run.lock` `flock(LOCK_NB)`, which holds only if the
    `kai-data` storage class honours cross-client flock — not verified.
  - **The K=3 epoch-10/20 reads use 6,144, not 8,192 (gate v5 B2).** `rss_rule_epoch10_20.awk`
    hardcodes `limit = 8192` in its `BEGIN` block and `-v` cannot override that hardcoded value.
    While the K=3 pod is still on the 6 GiB manifest (in-code gate `BNJ_RSS_GATE_LIMIT_MB=6144`),
    read its epoch-10/20 values against 6,144 by hand instead of trusting the awk's built-in
    verdict: `awk -v limit=6144 -f campaigns/2026-09-26-training-batch/manifests/rss_rule_epoch10_20.awk
    <arm log>`, i.e. pass the limit as an awk variable at the call site rather than editing the
    script (the awk itself is unchanged; that edit is ml-engineer's/the fixer's, not this file's).
    Without this override, a Δ of about 420-636 MiB would pass unflagged against the script's
    hardcoded 8,192 in a pod whose cgroup is still 6 GiB/arm.
  - `OVER8192` does **not** predict the 8 GiB verdict. On the four healthy Delta canary v2 GPU arm logs
    (telemetry; Delta's patches on 42abed4b), the epoch-5-20 fit projects to 17,485-27,621 MB, because
    RSS grows fastest early. The same arms fitted over epochs 5-98/99 project to **5.3-6.6 GB
    (gate form), one arm in four over 6,144** (corrected 2026-09-28 per gate v5 B3; the number
    5,329-6,615 MB from `code/evidence/rss_rules_8192_test.log` is the same fit — earlier text in
    this file read "6.5-6.7 GB, over 6,144" as if all four arms exceeded the limit, which is wrong;
    only one of the four does. `freeze.py`'s comments and STUDY.md carry the same correction, but
    fixing those is ml-engineer's/the fixer's task, not this file's). So expect every arm to be
    flagged by the epoch-20 fit regardless, and treat the swap as the likely outcome. A false flag
    costs at most 24 epochs; a missed swap costs a healthy arm stopped by the 6,144 gate at epoch 105.
  - `UNREADABLE` counts as not `OK`.
- **K=3 OOM fallback.** At the first `ARM_FAILED_AFTER_RETRIES` with a CUDA/TF OOM tail in the
  K=3 pod's `ARM_LOG`, delete `kai-chang0926-pilotb3-42abed` immediately (no safe wait — see
  PREFLIGHT.md "B, flag 4"), then apply the matching OOM'd-arm (K=1) and survivors (K=2) fallback
  Jobs from the table there. Not done in this action; recorded here for when it is needed.


## Launched 2026-09-28T23:05:57Z — pilot-b (regime B), two Jobs only

| Job | ConfigMap | Manifest lint | `kubectl apply` | pod | status @23:13Z | node |
| --- | --- | --- | --- | --- | --- | --- |
| `kai-chang0926-pilotb5-42abed` (K=5) | `kai-chang0926-code-42abed4b5d` | OK (PACK 5 arms), `manifests/pilot-b-k5-job.json`, hook-linted on apply | 2026-09-28T23:05:57Z | `kai-chang0926-pilotb5-42abed-0-v2nll` | **Pending** | none yet |
| `kai-chang0926-pilotb3-42abed` (K=3) | `kai-chang0926-code-42abed4b5d` | OK (PACK 3 arms), `manifests/pilot-b-k3-job.json`, hook-linted on apply | 2026-09-28T23:05:57Z | `kai-chang0926-pilotb3-42abed-0-c7tg4` | **Pending** | none yet |

W&B project `BNJetTag-ChangRecipe`, group `chang-n64-20260926-pilot-b`, tags
`chang0926,pilot,pilot-b,regime-b,validation-only`.

Only these two Jobs were applied. The six `pilot-b-fb*` fallback Jobs and both
`readout-b{5,3}-job.json` are linted (PREFLIGHT.md) but **not applied**; nothing production
was touched.

**2026-09-28T23:45Z — K=5 pod swapped to 8 GiB manifest (gate v5, this pod had not started).**
`kai-chang0926-pilotb5-42abed-0-v2nll` was confirmed still `Pending` with no node and no
`containerStatuses` (39 min old; nothing had started). Deleted
`kai-chang0926-pilotb5-42abed`; `kubectl get pods -l job-name=kai-chang0926-pilotb5-42abed`
returned no resources (confirmed NotFound). Re-linted
`manifests/pilot-b-k5-job.json` (`python3 nrp-lab/nrp_doctor.py lint`: OK, rule PACK 5 arms) and
`kubectl apply -f campaigns/2026-09-26-training-batch/manifests/pilot-b-k5-job.json -n cms-ml`
(hook-linted on apply) at 2026-09-28T23:45:43Z: `job.batch/kai-chang0926-pilotb5-42abed created`.
New pod `kai-chang0926-pilotb5-42abed-0-qqjmt`; confirmed spec `resources.requests.memory` =
`resources.limits.memory` = `40Gi` and container env includes `BNJ_RSS_GATE_LIMIT_MB=8192`. Pod
is `Pending` (same A10-saturation diagnosis as the original launch, see below); no node yet.
The running K=3 pod (`kai-chang0926-pilotb3-42abed-0-c7tg4`) was not touched — its swap follows
the A1/A2 window above.

| Job | ConfigMap | Manifest lint | `kubectl apply` | pod | status @23:46Z | node |
| --- | --- | --- | --- | --- | --- | --- |
| `kai-chang0926-pilotb5-42abed` (K=5, 8 GiB) | `kai-chang0926-code-42abed4b5d` | OK (PACK 5 arms), `manifests/pilot-b-k5-job.json`, hook-linted on apply | 2026-09-28T23:45:43Z | `kai-chang0926-pilotb5-42abed-0-qqjmt` | **Pending** (new; old K=5 Job deleted before it ever scheduled) | none yet |

**Scheduling, as of 2026-09-28T23:13Z:** both pods remained `Pending` for ~9 min after apply.
`PodScheduled` condition (read via jsonpath, not `describe`) for both:
```
0/532 nodes are available: ... 275 node(s) didn't match Pod's node affinity/selector, ...
30 Insufficient nvidia.com/gpu, ... preemption: ... 9 Insufficient nvidia.com/gpu.
```
Diagnosis (full detail in `.claude/memory/cluster-inventory.md` 2026-09-28, "chang0926 pilot-b:
both A10-only pods Pending on real A10 saturation, not our manifest"): the 275-node
affinity-mismatch count is expected (only 35 of 532 cluster nodes are A10); the dominant
*diagnostic* signal is `Insufficient nvidia.com/gpu`. Of the 35 A10 nodes, excluding c6017 (our
`NotIn`) and 5 nodes tainted against every tenant leaves 29 eligible — close to the 30 the
scheduler reports as GPU-full, i.e. essentially every eligible A10 node is currently full.
Occupancy is not attributable to a specific tenant from the `cms-ml` namespace (no
cluster-scope node `describe` permission), but this is real cluster-wide contention, not a
manifest problem — no fix applied, no relaunch. Neither pod has a node yet, so the
fingerprint-gate log check, `MANIFEST_SHA_OK`/`ARM_STARTED` check and first-epoch telemetry
could not be read this session; they are still to do once a pod schedules.

**Not yet safe to leave unattended: still needed before this section is closed, and the
next session must re-check pod state before assuming the epoch-10/20 RSS gate is being
watched.** If a pod is still `Pending` when this hands back, whoever picks this up next must
re-spawn to check status; once either pod reaches `Running`, the epoch-10/20 RSS stop rule is
a manual read at about +27 min and +52 min after that pod's `ARM_STARTED` (not automatic —
PREFLIGHT flag P2, "not built") and is the only protection before the in-code gate fires at
epoch 105. A pod that schedules with nobody watching for ~4.5 h risks repeating the
regime-A stall (memory leak ran unread for hours; see `RUN.md` "Stopped 2026-09-28T05:31Z").
- Per pod: node assigned, not `c6017`; fingerprint log line `FINGERPRINT 11559681 expected
  11559681` with no `GPU_FINGERPRINT_MISMATCH`; `MANIFEST_SHA_OK 041f981a…`; `RUN_STAGE
  pilot-b` (via `BNJ_STAGE=pilot-b` in the pod's exported env, confirmed at apply time); every
  arm's `ARM_STARTED`.
- First-epoch telemetry (s/epoch, `ebops_trace_seconds`, loss, EBOPs, `POD_MEM`, per-arm RSS) —
  telemetry only, not a result.
- Projected times to process epochs 10, 20, 105 (RSS gate) and 500, once s/epoch is observed.
- Reminder: pod logs must be saved to `campaigns/2026-09-26-training-batch/logs/` before the
  7-day TTL, regardless of when scheduling clears.

## K=3 pilot (pilotb3) verification and epoch-10/20 read — 2026-09-29T00:16Z (cluster-ops)

**Pods.** `kai-chang0926-pilotb3-42abed-0-c7tg4`, node `gpu-16.nrp.mghpcc.org` (NVIDIA A10,
23,028 MiB per in-pod `nvidia-smi`; not `c6017`, not in `KNOWN_BAD_NODES`), pod start
`2026-09-28T23:22:36Z`. Fingerprint gate (per-arm log, `chang0926-a07-350-n64-s1-...log`):
`FINGERPRINT 11559681 expected 11559681` → `FINGERPRINT_OK chang0926-a-n64-s1`; no
`GPU_FINGERPRINT_MISMATCH`. `MANIFEST_SHA_OK 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42`
(pod stdout). **Correction to the checklist above:** `RUN_STAGE pilot-b` is not a pod-stdout
line; it is printed once into each arm's own per-arm log
(`==== ARM_ATTEMPT 0 ... / RUN_STAGE pilot-b`), confirmed present for `chang0926-a07-350-n64-s1`.
`ARM_STARTED` lines (pod stdout, all attempt 0): `48 chang0926-a07-350-n64-s1 pid 383`,
`16 chang0926-c-n64-s1 pid 531`, `32 chang0926-f-n64-s1 pid 709`, 23:26–23:27Z. No OOM: no
`ARM_EXIT`/`ResourceExhausted`/`OOM`/`ARM_STALLED`/`Killed` in pod logs through 00:16Z (checked
`--since=50m`). Per-process GPU memory (`nvidia-smi --query-compute-apps`, steady since ~23:31Z):
A07-350-s1 (pid 383) 8,446 MiB; C-s1 (pid 531) 8,446 MiB; F-s1 (pid 709) 4,350 MiB — pod total
21,261 / 23,028 MiB. **This is the first K=3 VRAM measurement; A07-350-s1 did not OOM this time**
(it OOM'd at K=6 before). `kai-chang0926-pilotb5-42abed-0-v2nll` was GC'd after the K=5 Job
self-recreated `kai-chang0926-pilotb5-42abed-0-qqjmt` on `hcc-nrp-shor-c5805.unl.edu` (A10,
per in-pod `nvidia-smi`), started ~00:11Z; not otherwise inspected this session (out of scope).

**Epoch-10/20 RSS read**, via `manifests/rss_rule_epoch10_20.awk` against each arm's per-arm
log (`/data/chang-n64-20260926/pilot-b/logs/<run>-kai-chang0926-pilotb3-42abed-0.log`).
**Correction: the awk file's own default `limit` was bumped to 8192 by a later commit
(`c7bae4a`/`11668e9`, for the pending 8 GiB resize) but this pod's actual manifest still runs
`BNJ_RSS_GATE_LIMIT_MB=6144`** (confirmed in the running container's env via `ps aux`); the
`-v limit=6144` override the same commit added was not used on the first pass, so the raw awk
output below reads `limit_mib 8192`. A2 is evaluated here against **6144**, the pod's real
limit, per the coordinator's correction.

| arm | rss10 (MiB) | rss20 (MiB) | slope (MiB/epoch) | A2: rss20+slope×8.5 | limit (pod) | A2 verdict | proj. @ 7000 ep. (report only, not action) |
|---|---|---|---|---|---|---|---|
| A07-350-s1 | 2,470 | 2,482 | 1.2 | 2,584 | 6,144 | OK | 2,482 + 1.2×7000 ≈ 10,882 |
| C-s1 | 2,470 | 2,478 | 0.8 | 2,546 | 6,144 | OK | 2,478 + 0.8×7000 ≈ 8,078 |
| F-s1 | 2,320 | 2,331 | 1.1 | 2,424 | 6,144 | OK | 2,331 + 1.1×7000 ≈ 10,031 |

**A2 stop condition does not trip for any arm** (2,424–2,584 MiB, all well under 6,144). Per
the coordinator's rule change (relayed mid-task, ml-engineer evidence
`code/evidence/rss_rules_8192_test.log`): the 7,000-epoch linear projection over-predicts for
every healthy arm because RSS grows fastest early, so it is **not acted on** — reported only.
No delete issued; no OOM fallback needed. The unconditional swap to the 8 GiB manifest before
process epoch 105 is a separate cluster-ops task, not done here.

**Current process epoch / checkpoint, read at 00:16Z** (arm-log `[epoch` count; `latest.json`
where present): A07-350-s1 epoch 21, no `checkpoints/`/`latest.json` for this arm — its
"latest" state is the mtimes on `model_min_ebops.keras`/`model_unconstrained.keras`/
`validation_candidate.keras` in `runs/chang0926-a07-350-n64-s1/` (last write 00:15Z). C-s1
epoch 20, same pattern, last write 00:16Z. **F-s1 epoch 25** (ahead of the other two — its
process-epoch counter runs faster), and it does have `latest.json` → `{"checkpoint":
"epoch-0025"}` → `runs/chang0926-f-n64-s1/checkpoints/epoch-0025/state.json`:
`config_sha256` present, `data_sha256` present, `code_sha256
041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42` (matches `MANIFEST_SHA_OK`),
`completed_epochs: 25`. **Finding, not acted on: only F-s1 uses the `latest.json →
checkpoints/<leaf>/state.json` pointer scheme in this pilot; A07-350-s1 and C-s1 have no
`checkpoints/` directory at all**, so a dead-job recovery on those two arms would have to key
off the `.keras` file mtimes, not a `state.json`. Not investigated further (in scope only as
telemetry here).

**Telemetry** (not results): s/epoch not separately re-measured this pass (prior K=6 canary
range 208–311 s/epoch is the only measured basis; no K=3-specific s/epoch computed here — the
epoch counts above imply K=3 is faster, consistent with less GPU contention, but not quantified).
`ebops_trace_seconds` not read this pass. Loss/EBOPs/β not read this pass (out of scope for the
RSS-focused read requested).

Full pod log and the three per-arm logs saved to `campaigns/2026-09-26-training-batch/logs/`
(`pilotb3-42abed-c7tg4-full-20260929T0015Z.log` and per-arm `*-20260929T0015Z.log`).

## In-training vs traced EBOPs (regime-A W&B, for STUDY v10) — 2026-09-28

Telemetry, not results. Source: read-only pull from
`kayamaguchi-uc-san-diego/BNJetTag-ChangRecipe`, group `chang-n64-20260926-canary`, this
session (2026-09-28). Available keys (had both `ebops` [traced] and `ebops_in_training`,
plus a precomputed `ebops_in_training_over_traced`): all 5 runs logged both every epoch, no
gaps.

Ratio = in-training / traced, all epochs where both exist:

| Run | epochs | median | p10 | p90 | trend (1st third → last third) |
|---|---|---|---|---|---|
| A-s1 (`c16aff0707b9`) | 1–147 | 1.0772 | 1.0426 | 1.1049 | 1.0837 → 1.0534 (falling) |
| A-s2 (`8560dcb87a4c`) | 1–146 | 1.0739 | 1.0469 | 1.1068 | 1.0798 → 1.0663 (falling) |
| D-s1 (`81df1017a0eb`) | 1–168 | 1.0717 | 1.0478 | 1.1017 | 1.0709 → 1.0713 (flat) |
| E1-s1 (`5fd00a94e508`) | 1–88 | 1.0920 | 1.0548 | 1.1148 | 1.0928 → 1.0935 (flat) |
| C′-s1 (`a4d52dc546a0`, target 5M) | 1–47 | 1.0000 | 0.9906 | 1.0124 | 1.0000 → 1.0002 (flat) |

In-training reads 4–11 % above traced for the 350k-target arms (A, D, E1); for C′ (5M target)
the two track within ~1 %. Near-target check (traced within ±20 % of the arm's target, i.e.
≤420k for A/D/E1, ≤6M for C′): **no epoch in any of the 5 runs reaches that band before the
run stopped.** Minimum traced EBOPs reached: A-s1 431,605 (+23.3 % over 350k), A-s2 475,119
(+35.7 %), D-s1 436,569 (+24.7 %), E1-s1 445,720 (+27.3 %), C′-s1 6,394,253 (+27.9 % over 5M) —
all 5 runs were stopped before their traced EBOPs entered the ±20 % target band, so the
requested "at near-target" comparison cannot be computed from this data; the all-epoch median
above is the only number available.


## Option (c) plant fit: b and τ from regime-A W&B (ml-engineer, 2026-09-28)

These are telemetry figures, not results. They come from a read-only pull of the same four runs as the section above: A-s1 `c16aff0707b9`, A-s2 `8560dcb87a4c`, D-s1 `81df1017a0eb` and E1-s1 `5fd00a94e508`. The script is `code/staged-option-c/evidence/fit_b_tau.py` and its output is `fit_b_tau.log`. The method and caveats are in plan.md under "Option (c), staged". The model is an ARX(1) fit of log10 traced EBOPs on log10 β, with b = −g/(1−a) and τ = 1/(1−a). The intervals are 95 % moving-block bootstrap intervals.

| traced, epochs 40-end, pooled (n 389) | b | τ (epochs) |
|---|---|---|
| ARX, no trend | 0.168 [0.147, 0.204] | 4.21 [2.43, 5.02] |
| ARX + linear trend | 0.30 [0.08, 0.65]; per run 0.17 / 0.58 / 0.84 / 0.88 | 4.48 [2.38, 5.67] |

The verdict against the option-(c) bound b < 0.80 (p 1, i 0.05, D 10) is **not established**. After epoch 40, corr(log β, epoch) is 0.99 or higher in every run, so b cannot be separated from the drift. D-s1 and E1-s1 exceed 0.80 under the trend fit. There are two caveats. First, regime A traced every epoch and never came within 20 % of the 350k target. Second, only LR 3.0e-3 → 2.2e-3 of cycle 1 was observed. No p change has been applied. The conditional values are in plan.md.

## Regime-B K=5 pilot pod: startup verification and epoch-10/20 RSS rule — 2026-09-29 (cluster-ops, read-only)

Job `kai-chang0926-pilotb5-42abed` (8 GiB manifest, `BNJ_RSS_GATE_LIMIT_MB=8192`), pod
`kai-chang0926-pilotb5-42abed-0-qqjmt`, confirmed `Running` since `status.startTime`
2026-09-29T00:11:46Z. Node: `hcc-nrp-shor-c5805.unl.edu` — an A10 (`NVIDIA A10, 23028 MiB`),
not `c6017` and not in `KNOWN_BAD_NODES`.

**Gate checks (pod log, read via `kubectl logs`, not `describe`):**
- `MANIFEST_SHA_OK 041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42` — matches the
  linted manifest sha.
- `GPU_GATE_PASS`.
- `FINGERPRINT 11559681 expected 11559681 chang0926-a-n64-s1` / `FINGERPRINT_OK
  chang0926-a-n64-s1` — no mismatch. (Note: the fingerprint step itself ran ~1m36s of CPU-bound
  work on this pod, PID 76, `python /cmfp/fingerprint_check.py`, actively running throughout —
  not hung; the K=3 pod's fingerprint step took ~1m52s, so this one was somewhat faster, both
  within the same order.)
- `RUN_STAGE pilot-b` confirmed via `BNJ_STAGE=pilot-b` in the container's exported env (read
  from `ps aux` of PID 1).
- Pod spec confirmed now (`kubectl get pod ... -o jsonpath='{.spec.containers[0].resources}'`,
  2026-09-29T00:2Xz): `{"limits":{"cpu":"10","ephemeral-storage":"24Gi","memory":"40Gi",
  "nvidia.com/gpu":"1"},"requests":{same}}` — `requests.memory` = `limits.memory` = `40Gi`, and
  `BNJ_RSS_GATE_LIMIT_MB=8192` present in the container env (from `ps aux` of PID 1).
- All 5 `ARM_STARTED`, staggered ~15s apart:
  ```
  00:15:20.119Z ARM_STARTED 0  chang0926-a-n64-s1       pid 446  attempt 0
  00:15:35.286Z ARM_STARTED 1  chang0926-a-n64-s2       pid 634  attempt 0
  00:15:50.454Z ARM_STARTED 24 chang0926-d-n64-s1       pid 1002 attempt 0
  00:16:05.621Z ARM_STARTED 56 chang0926-cprime-n64-s1  pid 1355 attempt 0
  00:16:20.790Z ARM_STARTED 57 chang0926-e1-n64-s1      pid 1681 attempt 0
  ```
- No OOM, no `Killed`, no `RSS_GATE` fire, no traceback in the pod log as of this check.

**GPU memory per process** (`nvidia-smi --query-compute-apps`, read shortly after all 5 arms
started, ~1 min post-`ARM_STARTED`): each of the 5 training processes reports **1276 MiB**;
`nvidia-smi --query-gpu=memory.used` totalled **5384 MiB** with only 4/5 processes registered at
that sample (5th had just started). This is a **startup** reading under
`TF_FORCE_GPU_ALLOW_GROWTH=true`, not steady state, and is not comparable to the 21,094–23,028
MiB range measured for the same 5-arm set before (that was steady-state usage, not a ceiling).
Whether K=5 fits is not yet established — re-read `nvidia-smi --query-compute-apps` at process
epochs 10 and 20 before drawing that conclusion.

**Epoch-10/20 RSS rule:** not yet evaluated — at the time of this check (pod age ~5 min from
`ARM_STARTED`), no arm had logged its first `[epoch ...]` line yet (all 5 logs on the PVC at
`/data/chang-n64-20260926/pilot-b/logs/<arm>-kai-chang0926-pilotb5-42abed-0.log` still showed
only the `wandb: Syncing run ...` startup lines). A poll loop
(`manifests/rss_rule_epoch10_20.awk`, run against each arm's PVC log via `kubectl exec ... cat
... | awk`) is running to catch process epochs 10 and 20 per arm; this section will be updated
with the `RSS_RULE <arm> OK|STOP rss10 rss20 projection_mib limit_mib` line for each of the 5
arms, s/epoch, `ebops_trace_seconds`, loss-finite check, and traced EBOPs/floor/β once available.
The K=3 pod `kai-chang0926-pilotb3-42abed-0-c7tg4` was read-only for cross-reference only (its
own swap is another cluster-ops task; not touched here) — its epoch-1 log line for
`chang0926-a07-350-n64-s1` shows the expected field shape:
`EBOPs=17136111 target=350000 above_floor=16793058 ... beta=1e-07 val_AUC=0.859625
val_accuracy=0.589048 seconds=206.9 ebops_trace_seconds=87.21 loss=3.241156 host_rss_mb=2425`.

### Telemetry, epochs 1–4/5/6 (read directly off the PVC per-arm logs, ~11–12 min after `ARM_STARTED`) — not results

Traced (epoch 1) fields, all 5 arms, loss finite in every epoch seen so far, no NaN:

| arm | initial_ebops | epoch-1 traced EBOPs | above_floor | target | beta | `ebops_trace_seconds` | seconds (ep.1) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A-s1 | 11,559,681 | 11,652,682 | 11,481,156 | 350,000 | 1e-07 | 108.95 | 223.4 |
| A-s2 | 11,295,521 | 11,602,989 | 11,431,463 | 350,000 | 1e-07 | 101.46 | 230.3 |
| D-s1 | 11,559,681 | 11,948,350 | 11,776,824 | 350,000 | 1e-07 | 99.38 | 230.6 |
| C′-s1 | 24,816,782 | 17,853,582 | 13,273,184 | 5,000,000 | 1e-07 | 164.76 | 315.6 |
| E1-s1 | 10,847,316 | 10,438,573 | 10,352,810 | 350,000 | 1e-07 | 82.02 | 177.3 |

s/epoch (mean of epochs ≥2, since epoch 1 carries the trace overhead) and `T_run = 7000 × s_e`
against the 14-day rule (172.8 s/epoch threshold):

| arm | epochs sampled | s_e (mean, s) | T_run (7000×s_e) | 14-day rule |
| --- | --- | --- | --- | --- |
| A-s1 | 2–5 | 119.8 | 9.70 d | PASS |
| A-s2 | 2–4 | 126.9 | 10.28 d | PASS |
| D-s1 | 2–4 | 129.4 | 10.48 d | PASS |
| C′-s1 | 2 only (315.6→212.9, not yet settled) | pending — only 2 epochs observed, not reported as a rate | — | pending |
| E1-s1 | 2–6 | 87.6 | 7.10 d | PASS |

C′-s1 (the 5M-EBOPs/12,788-param arm) is the slowest to reach each epoch and had logged only 2
epochs at this read; its s_e is not yet stable enough to project and is left pending rather than
guessed.

In-training (untraced) EBOPs at epoch 2 vs the epoch-1 traced value, for reference (matches the
pattern already on record above for the 350k-target arms): A-s1 12,706,391 vs 11,652,682
(+9.0 %), A-s2 12,318,394 vs 11,602,989 (+6.2 %), D-s1 12,642,623 vs 11,948,350 (+5.8 %), E1-s1
11,928,915 vs 10,438,573 (+14.3 %), C′-s1 17,814,613 vs 17,853,582 (−0.2 %, within ~1 %, matching
the earlier note that C′ tracks closer to traced than the 350k arms).

## Takeover check, 2026-09-29T02:47-03:10Z (orchestrator, new session)

Telemetry only, not results. Read-only on both pilot Jobs: nothing deleted, re-applied or resized.
Sources: `kubectl logs`, the per-arm logs on the PVC, `nvidia-smi` in the pods, W&B
`BNJetTag-ChangRecipe` (read-only). Copies of the pod and per-arm logs:
`logs/pilotb5-qqjmt-full-20260929T0305Z.log`, `logs/pilotb3-vqxc7-full-20260929T0305Z.log` and
`logs/<arm>-<job>-0-20260929T0305Z.log` (8 arms).

**K=3 pod after the 8 GiB swap (the checks of ONBOARDING §3.1.1, all met).**
`kai-chang0926-pilotb3-42abed-0-vqxc7` on `gpu-17.nrp.mghpcc.org` (`HOSTNAME_NODE` line; NVIDIA A10,
23,028 MiB; not c6017, not in `KNOWN_BAD_NODES`). Pod start 2026-09-29T00:50:30Z, restarts 0,
requests = limits = 24Gi / 6 CPU. Pod stdout: `MANIFEST_SHA_OK 041f981a…`, `GPU_GATE_PASS`,
`FINGERPRINT 11559681 expected 11559681 chang0926-a-n64-s1`, `FINGERPRINT_OK`, then `ARM_STARTED`
48 A07-350-s1 pid 369, 16 C-s1 pid 486, 32 F-s1 pid 678 (per-arm `==== ARM_ATTEMPT 0` at 00:54:33Z,
00:54:48Z, 00:55:04Z). All three arms log `resume_epoch=25`; no "History exists without a committed
checkpoint". The swap cost A07-350-s1 and C-s1 epochs 26-27 and F-s1 epochs 26-43 (the first
attempt's last epoch lines), plus about 25 min with no pod. All three arms now use the
`latest.json` → `checkpoints/epoch-NNNN` layout (A07-350-s1 and C-s1: epoch-0050, epoch-0075), so
the 00:16Z note that only F-s1 had `checkpoints/` reflected only that the other two had not yet
reached epoch 25. The per-arm log files hold both attempts; read after the last `==== ARM_ATTEMPT`.

**W&B after the resume.** The K=3 runs kept their ids and logged the re-run epochs as out-of-order
steps, which W&B drops (`wandb: WARNING Tried to log to step 42 that is less than the current step
43`, F-s1). For A07-350-s1 and C-s1 (epochs 26-27) and F-s1 (epochs 26-43), W&B holds the first
attempt's values; the per-arm log is the source for those epochs. W&B state at 02:55Z: all eight
pilot-b runs `running`, heartbeats current.

**Epoch-10/20 RSS rule** (`manifests/rss_rule_epoch10_20.awk`, limit 8,192 MiB, process epochs
counted after the last `ARM_ATTEMPT`). The K=5 table was left "to be updated" in the section above.

| pod | arm | rss10 | rss20 | projection to process epoch 105 (MiB) | verdict |
| --- | --- | --- | --- | --- | --- |
| K=5 | A-s1 | 2,373 | 2,392 | 2,554 | OK |
| K=5 | A-s2 | 2,364 | 2,383 | 2,544 | OK |
| K=5 | D-s1 | 2,358 | 2,383 | 2,596 | OK |
| K=5 | C′-s1 | 2,352 | 2,369 | 2,514 | OK |
| K=5 | E1-s1 | 2,366 | 2,390 | 2,594 | OK |
| K=3 (after resume) | A07-350-s1 | 2,351 | 2,364 | 2,474 | OK |
| K=3 (after resume) | C-s1 | 2,361 | 2,366 | 2,408 | OK |
| K=3 (after resume) | F-s1 | 2,239 | 2,247 | 2,315 | OK |

**Preview of the in-code gate at process epoch 105** (`ablation.py:654-678`: least squares over the
process's epochs 5-104, projection = fitted RSS at epoch 5 + slope × 7,000, limit 8,192, exit 5 on
FAIL). A partial fit over the epochs so far over-predicts, because RSS rises fastest early and then
flattens (every arm sits at 2,26x-2,42x MiB and moves by 0-6 MiB over its last 20 epochs). The two
bracketing columns extend each series to epoch 105: "flat" holds the last value, "trend" continues
the slope of the last 30 epochs. Projections in MiB.

| arm | process epochs read | partial-fit slope (MiB/epoch) | partial-fit projection | flat | trend (last-30 slope) |
| --- | --- | --- | --- | --- | --- |
| A-s1 | 67 | 0.78 | 7,817 | 5,231 | 5,993 (0.33) |
| A-s2 | 66 | 0.84 | 8,229 | 4,734 | 5,219 (0.20) |
| D-s1 | 66 | 1.16 | 10,445 | 6,116 | 7,073 (0.40) |
| C′-s1 | 41 | 1.60 | 13,524 | 4,457 | 10,165 (1.15) |
| E1-s1 | 94 | 0.58 | 6,454 | 5,838 | 5,866 (0.11) |
| A07-350-s1 | 54 | 0.49 | 5,786 | 3,585 | 4,254 (0.18) |
| C-s1 | 53 | 0.34 | 4,708 | 3,130 | 3,963 (0.22) |
| F-s1 | 85 | 0.30 | 4,321 | 3,896 | 3,936 (0.05) |

Only C′-s1 projects over the limit, and only if its epoch 12-41 slope held for 64 more epochs; its
last ten epochs moved 2,387 → 2,390. Its gate lands about 06:50Z. The gate's own `RSS_GATE` lines
are the verdict; a read-only watcher polls every 150 s for them. If an arm exits 5, act per
PREFLIGHT P1: let the other arms reach their epoch-500 pause, then delete the Job so
`backoffLimitPerIndex` does not re-run the gate-failed arm.

**GPU memory per process** (`nvidia-smi --query-compute-apps`, about 03:04Z; pid → arm from
`ARM_STARTED`):
- K=3 (gpu-17): A07-350-s1 8,442 MiB, C-s1 8,442, F-s1 4,346; pod 21,249 / 23,028 MiB (92.3 %).
  This matches the c7tg4 pod on gpu-16 (8,446 / 8,446 / 4,350).
- K=5 (c5805): A-s1, A-s2, D-s1, E1-s1 4,350 MiB each, C′-s1 5,110; pod 22,540 / 23,028 MiB
  (97.9 %), about 490 MiB free. No OOM in about 170 min, with 4-9 full-split traces per arm. In
  regime A, E1-s1 held 2,830 MiB; here it holds 4,350. Not acted on (no rule covers it). The
  watcher greps arm logs for `ResourceExhausted`, `out of memory` and `OOM`. The K=4 production
  E pods are sized from Delta's E canary (4,356 MiB per arm), not from this pod.

**Epoch rate and projected times** (mean `seconds=` over each arm's last 30 epochs, which include
three traced epochs; arithmetic, not a measurement of the future):

| arm | epoch at 02:52Z | s/epoch | process epoch 105 (RSS gate) | epoch-500 pause |
| --- | --- | --- | --- | --- |
| F-s1 | 110 | 80.9 | ~03:22Z | ~11:40Z 09-29 |
| E1-s1 | 94 | 96.9 | ~03:12Z | ~13:50Z 09-29 |
| A07-350-s1 | 79 | 130.7 | ~04:46Z | ~18:10Z 09-29 |
| C-s1 | 78 | 130.7 | ~04:48Z | ~18:15Z 09-29 |
| A-s1 | 67 | 138.5 | ~04:22Z | ~19:35Z 09-29 |
| A-s2 | 66 | 138.9 | ~04:25Z | ~19:40Z 09-29 |
| D-s1 | 66 | 138.8 | ~04:25Z | ~19:40Z 09-29 |
| C′-s1 | 41 | 221.2 | ~06:50Z | ~07:05Z 09-30 |

So the K=3 Job is terminal at about 18:15Z on 09-29. The K=5 Job is terminal only when C′-s1
pauses, about 11.5 h after A and D. B3 allows `readout-b5` only once that Job is terminal or
deleted. Its partial mode (PREFLIGHT "B, flag 6") covers a deleted Job with C′-s1 missing, but
C′-s1 is in the K1 fire list.

**K1 preview** (W&B `ebops_in_training` / `ebops` on the traced epochs so far, 0-indexed epochs
0-109, which lie outside the rule's 100-500 window; not the rule's evaluation, which
results-analyst runs at epoch 500). Median r: A-s1 1.088, A-s2 1.066, D-s1 1.054, E1-s1 1.107,
C′-s1 1.000, A07-350-s1 1.049, C-s1 0.979, F-s1 1.071. By the rule's formula (350k × (1 − r^−0.9),
computed from the four-decimal medians), the implied traced offset against the arm's 10 %-of-headroom
threshold is: A-s1 25,665, A-s2 19,425 and F-s1 20,898, each against 17,847; D-s1 16,209 against
17,847, under it; E1-s1 30,522 against 26,424; A07-350-s1 14,778 against 695. The largest
iso-EBOPs spread is A-s1 1.088 against C-s1 0.979, against a 0.02 limit. If these hold to epoch 500, the rule fires, as it would on the regime-A
numbers. Production then waits for Kai's (c)/(d) choice.

**Actions:** none on either Job. Delta's A07 canary was applied at 03:03:42Z (Delta RUN.md), because
the K=3 pilot has been Running since 00:50Z. It uses its own A10 and takes no GPU from the pilots.

**2026-09-29 03:22Z, cross-reference (Delta A07 canary, telemetry).** On an A10, three A07 processes
(Delta rep-C s1-s3, the anchor's arm-C configs plus Delta's always-on diagnostics, bundle 705a554b)
ran out of GPU memory: the third arm hit `RESOURCE_EXHAUSTED` on its first attempt. With two left,
each holds 8,446 MiB and the pod holds 16,906 / 23,028 MiB (73.4 %). This bears on production
packs 7-10 ({C, A07-350} at K=4 on A10, about 34 GB by the per-process figure) and on plan.md R-B3's
fallback "repack at K=3". A pack of three A07 arms does not fit either. The pilot's own K=3 pod
fits because one of its three arms is F, which is E class (4,346 MiB). The STUDY (4) leaves
production packing and the GPU class to Kai at the readout.

**In-code RSS gate verdicts at process epoch 105** (the `RSS_GATE` lines in each arm log; limit 8,192
MiB on both pods, which settles the K=3 pod's limit after the swap; fit over process epochs 5-104):

| arm | time (UTC) | slope (MB/epoch) | baseline (MB) | projection at 7,000 (MB) | verdict |
| --- | --- | --- | --- | --- | --- |
| E1-s1 | ~03:10Z | 0.493 | 2,380 | 5,830 | PASS |
| F-s1 | ~03:20Z | 0.251 | 2,243 | 3,997 | PASS |
| A-s1 | ~04:20Z | 0.482 | 2,386 | 5,760 | PASS |
| A-s2 | ~04:23Z | 0.423 | 2,379 | 5,336 | PASS |
| D-s1 | ~04:23Z | 0.617 | 2,377 | 6,697 | PASS |
| A07-350-s1 | ~04:44Z | 0.244 | 2,359 | 4,068 | PASS |
| C-s1 | ~04:47Z | 0.201 | 2,363 | 3,767 | PASS |
| C′-s1 | ~06:53Z | 0.475 | 2,366 | 5,694 | PASS |

The partial-fit column of the 02:52Z preview over-predicted every one of these projections. Four
of the seven fall between that preview's "flat" and "trend" columns. The other three do not:
E1-s1 is 8 MB below "flat" (5,838), F-s1 is 61 MB above "trend" (3,936), and A-s2 is 117 MB above
"trend" (5,219). The preview is only a bracket; the gate line is the verdict.

**2026-09-29 11:46Z — F-s1 reached its epoch-500 pause (K=3 pod; telemetry).** Pod stdout
`ARM_EXIT chang0926-f-n64-s1 0 attempt 0`. Arm log: `CHECKPOINT_VERIFICATION_PASS` (the in-pod reload
check, stored EBOPs, `ebops_reload_check: "stored"`). `runs/chang0926-f-n64-s1/snapshots/epoch-0500/`
holds `state.json`, `model_best.keras`, `model_best_auc_feasible.keras`, `model_min_ebops.keras` and
`model_unconstrained.keras`. The last traced line reads
`[epoch 500/7000] EBOPs=433344 target=350000 above_floor=261818 feasible=0 degenerate=0 beta=1.96e-05`.
It is quoted here as telemetry only; the readout job and results-analyst evaluate the pre-registered
rules. A07-350-s1 and C-s1 continue in the same pod; the Job ends when both pause (projected ~18:15Z).

**2026-09-29 ~13:50Z — E1-s1 reached its epoch-500 pause (K=5 pod; telemetry).** Arm log:
`CHECKPOINT_VERIFICATION_PASS`. The last traced line reads
`[epoch 500/7000] EBOPs=375397 target=350000 above_floor=289634 feasible=0 degenerate=0 beta=3.77e-06`.
It is quoted as telemetry; the readout evaluates the rules. The K=5 Job ends when C′-s1 pauses,
projected ~07:05Z on 09-30. A-s1, A-s2 and D-s1 are projected at ~19:35-19:40Z today.

## 2026-09-29 16:13Z — K=3 pilot Job complete; readout-b3 applied (B3)

- `kai-chang0926-pilotb3-42abed` Succeeded (pod `…-vqxc7` on gpu-17, restarts 0, no stop rule
  triggered at any point). Pod stdout: `ARM_EXIT` 0 for F-s1, A07-350-s1 and C-s1, then
  `PACK_DONE diverged [] failed []`. The Job ended at about 16:13Z, earlier than the 18:15Z
  projection, because A07-350-s1 and C-s1 ran faster once F-s1 had paused (11:46Z).
- Every arm has one `CHECKPOINT_VERIFICATION_PASS` and `runs/<arm>/snapshots/epoch-0500/state.json`.
  The snapshot contents differ: A07-350-s1 has only `model_min_ebops` / `model_unconstrained`; C-s1
  and F-s1 also have `model_best` and `model_best_auc_feasible`.
- The last traced line per arm (telemetry, validation, n = 62,000; not a result; the readout and
  results-analyst evaluate the rules):
  - A07-350-s1 `EBOPs=381965 target=350000 above_floor=38912 feasible=0 degenerate=0 beta=7.11e-05 val_AUC=0.500000 val_accuracy=0.202597`;
  - C-s1 `EBOPs=4592840 target=5000000 above_floor=4249787 feasible=1 degenerate=0 beta=1.68e-08 val_AUC=0.808829 val_accuracy=0.485919`;
  - F-s1 as recorded at 11:46Z.
- Saved: `logs/pilotb3-vqxc7-final-*.log`, `.pod.json`, and the three final per-arm logs `*-final-*.log`.
- **Readout.** B3 was met: the pilot Job was terminal and its pod Succeeded. `readout-b3-job.json`
  (`kai-chang0926-readoutb3-42abed`, CPU 8 / 24 Gi, ConfigMap `kai-chang0926-code-42abed4b5d`) was
  applied at 16:14:12Z, and the hook linted it. Watch for `READOUT_JOB_DONE certify_exit=… a26_exit=…
  missing=…`: a non-empty `missing=` means the readout is not done. A07-350-s1's readout gates
  production packs 7-10.

## 2026-09-29 ~17:59Z — readout-b3 complete (CPU, K=3 pod's epoch-500 snapshots)

`kai-chang0926-readoutb3-42abed` ran from 16:14Z to about 18:00Z (105 min) on nrp-00.rcac.purdue.edu
and completed. Its gate lines (pod log `readout/b3/readoutb3-pod.log`):
`MANIFEST_SHA_OK 041f981a…`; `READOUT_ARMS only=A07-350-s1,C-s1,F-s1 … missing= none`;
`CERTIFIED` C-s1 primary and auc_sensitivity 4,880,224 = 4,880,224; F-s1 primary and
auc_sensitivity 325,319 = 325,319; `CERTIFICATION_ALL_PASS 4 0`; `A26_DONE`;
`READOUT_JOB_DONE certify_exit=0 a26_exit=0 missing= none`, the clean form (B3). A07-350-s1 has no
best-as-of-500 file to certify, because it had no feasible snapshot. Outputs were copied from the
PVC to `readout/b3/readout-epoch-0500-42abed-b3/`: `certify-snapshot-0500.json` and
`a26-entropy-epoch-0500.json` (sha256 95fb4b26…, as in `A26_WROTE`).

A26 on validation, n = 62,000 (pilot telemetry; results-analyst evaluates the pre-registered rules):
- A07-350-s1 (`model_min_ebops`, no feasible snapshot): H/log N = 1.000 on all 4 heads, row sums
  0.439; Q, K and V 32 of 32 channels at 0 bits ("true zero, 0 EBOPs").
- C-s1: H/log N 0.622 / 0.914 / 0.544 / 0.880; zero-bit Q 0 / 32, K 0 / 32, V 3 / 32.
- F-s1: H/log N = 1.000 on both heads; Q, K and V 24 of 24 channels at 0 bits.

The CPU trace cost in the pod was about 33 min per A07 checkpoint, against PREFLIGHT's laptop
projection of 184 s, using about 1.8 of 8 CPUs. readout-b5 carries the same 4 h deadline; its A/D/E1
checkpoints are E class, so the risk is smaller, but it should be timed.

## 2026-09-29 18:30-18:48Z — K=5 pod: A-s1, A-s2, D-s1 reach the epoch-500 pause (telemetry)

`ARM_EXIT` 0 for A-s1 at 18:30Z and for A-s2 and D-s1 at about 18:48Z; each arm log has one
`CHECKPOINT_VERIFICATION_PASS`. Last traced lines (validation, n = 62,000; not a result; the
readout-b5 certification and results-analyst evaluate the A rule and K1):
- A-s1 `EBOPs=315700 target=350000 above_floor=144174 feasible=0 degenerate=1 val_AUC=0.499199 val_accuracy=0.201919`; its snapshot holds only `model_min_ebops` and `model_unconstrained`;
- A-s2 `EBOPs=336841 target=350000 above_floor=165315 feasible=1 degenerate=0 val_AUC=0.645057 val_accuracy=0.312129`; its snapshot has `model_best` and `model_best_auc_feasible`;
- D-s1 `EBOPs=563100 target=350000 above_floor=391574 feasible=0 degenerate=0 val_AUC=0.666276 val_accuracy=0.315823`; its snapshot has `model_best` and `model_best_auc_feasible`, a feasible checkpoint from before epoch 500.

With four of its five arms paused, **C′-s1 trains alone on the GPU at about 39 s per untraced
epoch** (was about 220 s at K=5). At epoch 339 at 18:54Z, it projects to epoch 500 at about 21:00Z,
not the earlier projection of 07:05Z on 09-30. The partial-readout question put to Kai (a readout at
19:40Z without C′-s1) therefore saves only about 1-2 h. The default holds: readout-b5 is applied
after the K=5 Job is terminal (B3). Logs: `logs/*-kai-chang0926-pilotb5-42abed-0-20260929T1854Z.log`.
