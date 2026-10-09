# REGRESSION TICKET: R1 relaunch r2, resume premise false for 17 of 23 arms

Opened 2026-10-08 by investigator. Campaign `campaigns/2026-10-05-pilot-program`, bundle 98dd2875, Jobs `kai-p1005r1-*-98dd28-r2` (submitted 2026-10-07 07:56 JST, `--no-rss-gate`). Nothing here is quotable (engineering evidence, no seeds, no intervals). Cluster and code were read-only. One CPU pod `kai-p1005-r2-inspect` (ubuntu:22.04, PVC `kai-data` mounted readOnly, 100m CPU) was created for `ls`/`grep`/`cat` and deleted afterwards; the cms-ml pod quota (200/200) delayed it by about 25 minutes.

Notation: **OBSERVED** = read from the PVC, pod log or Job/pod object in this session. **EXPECTED** = what PREFLIGHT 3d / JOURNAL 2026-10-07 07:40 / RUN.md state. **INFERRED** = derived, not directly seen.

## Trigger

4 arms exit 76 (`RuntimeError: History exists without a committed checkpoint`, `bnhgq2/ablation.py:914`), 2 arms exit 124 (11,581 s), 2 arms lost both pods at init. 15 of 23 Jobs Complete.

## Root finding (one cause behind all three failure modes)

**EXPECTED** (PREFLIGHT 3d "Resume path", JOURNAL 07:40, RUN.md r2 table): all 23 arms resume from `checkpoints/epoch-0100`, E arms finish in about 2.2-2.5 h, and the readout marks every r2 arm "resumed at epoch 100".

**OBSERVED**: only 6 of the 23 arms had any R1 state on the PVC. The other 17 started from epoch 0 in r2.

- R1 arm logs (`r1/logs/*-98dd28-0.log`, hostname of Indexed Job pods is `<job>-0`, so one file per arm) exist for 7 arms only: ctl-e-unc-c-s1, h1-e-350k-c-s1, h2-e-750k-c-s1, h3-e-350k-c-qkv1-s1 (the completed one), h3-e-350k-c-qkv1-s2, h3-e-450k-c-qkv1-s1, h5-e-350k-c-nb-s1.
- `RSS_GATE_FAIL.json` exists in exactly 6 run dirs (ctl, h1-s1, h2-e-750k, h3-qkv1-s2, h3-450k, h5-nb-s1), mtimes 2026-10-05 22:27:58Z to 23:11:51Z. The RSS gate therefore killed 6 arms, not 23.
- The other 17 R1 Jobs (`kubectl get jobs`): `failed: 2`, `failedIndexes: 0`, Failed condition at 22:52:54Z-22:53:12Z for 15 of them (a 18 s window, Jobs started 21:49-21:53Z), no arm log, no run-dir content from R1 (their `config.json`/`initialization.json` carry r2 times, 2026-10-06 23:xxZ to 2026-10-07 00:5xZ). Cause of the two R1 pod failures per Job is **not observed** (R1 pods are gone; only `h3-e-350k-c-qkv1-s2-98dd28-0-h8khk` remains). The synchronized 22:53Z end points to one external event, not to the RSS gate.
- r2 arm logs (`r1/logs/*-98dd28-r2-0.log`), first `[train] ... resume_epoch=` line per arm:
  - `resume_epoch=100` (restored from epoch-0100): ctl-e-unc-c-s1, h1-e-350k-c-s1, h2-e-750k-c-s1, h3-e-350k-c-qkv1-s2, h3-e-450k-c-qkv1-s1, h5-e-350k-c-nb-s1.
  - `resume_epoch=0` (fresh initialization): the other 17 (list in section 4).

Consequences: (a) the exit-76 guard fired because a node loss interrupted a fresh run, not a resume; (b) the 12,000 s E-arm deadline was sized for 400 remaining epochs and is too short for a fresh 500-epoch E arm at the observed 22-23 s/epoch; (c) RUN.md "Incident 2026-10-06 ... 23 of 24 arms killed by the RSS gate", "~18 GPU-h" and the readout marking "resumed at epoch 100" are wrong for 17 arms.

## 1. The four exit-76 arms

Arms: h1-e-350k-c-s2, h4-e-350k-c-w100-s2, h4-e-350k-c-w50-s1, h4-e-350k-c-w50-s2. Run dir `/data/chang-n64-20260926/pilot-program-20261005/r1/runs/pilot1005-<arm>`.

OBSERVED dir contents (identical shape for all four): `activation_widths.jsonl` 1 row (about 463 KB, mtime 00:56:45-46Z), `pid_telemetry.jsonl` 1 row (about 750 B, 00:56:45-49Z), `config.json`/`data_info.json`/`initialization.json` (00:52:55-00:55:17Z), `model_min_ebops.keras` and `model_unconstrained.keras` 0 bytes (00:54:19-21Z), `validation_candidate.keras` about 509 KB, `run.lock` 00:51:43Z, `cost_contract.json`/`source_manifest.json` rewritten 01:06:5xZ by the replacement pod. **No `latest.json`, no `checkpoints/` directory, no `RSS_GATE_FAIL.json`, no `snapshots/`.**

Why `restore_checkpoint` returned None: `restore_checkpoint` (`ablation.py:293-297`) returns None iff `latest.json` is absent. It was absent because **no checkpoint was ever written**: `checkpoint_every_epochs` is 25, and the arm completed 1 epoch. Not a hash mismatch (that path raises an AssertionError, `:300-302`), not a partial write, not a wrong out path (the replacement pod read the same dir and saw the first pod's 1-row history).

Did the lost first pod train? **Yes**, although the API shows `Init:ContainerStatusUnknown` / `train: PodInitializing` (stale status from a node that stopped reporting). Evidence: the shared arm log has `==== ARM_ATTEMPT 0 2026-10-07T00:51:38Z` then `[train] pilot1005-h1-e-350k-c-s2 params=31735 resume_epoch=0 initial_ebops=11295521` and a W&B "Syncing run" line (w100-s2 00:51:37Z, w50-s1 00:51:38Z, w50-s2 00:51:38Z, same pattern). First pod `txncd` had `startTime` 00:47:00Z, so container start plus the 4.5 min setup seen on every pod gives 00:51:3xZ. It wrote epoch 1 (00:56:45Z) and nothing after: the node `hcc-chase-shor-c4715.unl.edu` was lost about 00:57Z. The Job controller created the replacement pod at 00:58:54Z (pod condition `PodFailed` stamped later, 01:02:32Z).

The replacement pods (`8g27s`, `b4xm5`, `j25j2`, `bqkm7`, container start 01:01:12-14Z, also scheduled on c4715) ran ARM_ATTEMPT 0/1/2 at 01:05:2x/01:06:1x/01:06:5x Z: `activation_widths.jsonl` and `pid_telemetry.jsonl` exist, no `latest.json`, so `ablation.py:911-914` raises. Three attempts, `ARM_FAILED_AFTER_RETRIES`, `POD_EXIT_FINAL rc=1 phase=train elapsed_s=349-371 exit=76` (FailIndex). No evidence of two concurrent writers: no file mtime in these dirs lies between 00:56:49Z and 01:06:50Z.

Classification: **lost-pod interference on a fresh start, not a checkpoint-format or hash problem.** The guard worked as designed; its message hides that there is nothing to resume.

## 2. The two exit-124 arms

Both started from epoch 0 (r2 arm log `resume_epoch=0`; no R1 state). Both are valid, resumable runs.

| field | h1-e-350k-noc-s2 | h2-e-500k-c-s1 |
| --- | --- | --- |
| node | hpc-nrp-g1.nmsu.edu | suncave-5 |
| pre-arm time in the pod | 2,215 s (run_pack budget 9,365 s) | 275 s (budget 11,393 s) |
| arm wall time (run.lock to last write) | 00:19:24Z to 02:55:20Z = 9,356 s | 23:48:48Z to 02:58:34Z = 11,386 s |
| last epoch reached (arm log, `activation_widths.jsonl` rows) | 413 of 500 | 499 of 500 |
| newest checkpoint (`latest.json`, state.json `completed_epochs`) | epoch-0400 (epoch-0375 kept) | epoch-0475 (epoch-0450 kept) |
| mean seconds per epoch (arm log `seconds=`, incl. 89 s epoch 1) | 21.96 (n=413) | 22.35 (n=499) |
| resumed from epoch 100? | **No** (resume_epoch=0) | **No** (resume_epoch=0) |
| seconds to epoch 500 | 87 epochs x 21.96 = about 1,910 s from where it died; from its epoch-0400 checkpoint 100 x 21.96 = about 2,200 s plus about 280 s setup | 1 epoch = about 22 s plus about 20 s finalization from where it died; from epoch-0475, 25 x 22.35 = about 560 s plus setup |

INFERRED: a fresh 500-epoch E arm needs about 500 x 22 + 90 + 300 = 11,400-11,700 s of arm wall time, against a run_pack budget of 11,310-11,393 s. h2-e-500k missed by roughly 50 s (about 0.4 %). Completed fresh E arms also ran close to the limit: h5-nb-s2 11,459 s, h2-e-5m 11,110 s, h4-w100-s1 10,431 s (container wall time). The split 12,000 s deadline is the direct cause of both 124s; the 37-minute setup on nmsu made noc-s2 hopeless regardless.

Side observation (log lines only, not a result): noc-s2 epochs 412-413 show `val_AUC=0.500000 val_accuracy=0.202597`, i.e. a collapsed model. It still needs a disposition under the STUDY rules; it is not caused by this ticket.

## 3. The two "never ran" arms (h3-e-450k-c-qkv1-s1, h5-e-350k-c-nb-s1)

The incident table ("never trained") is wrong. Both pods in each Job ran training, although the API shows `Init:ContainerStatusUnknown`.

- OBSERVED arm log: `ARM_ATTEMPT 0 2026-10-07T00:51:37Z` then `resume_epoch=100` (first pod, restored from R1 epoch-0100), and `ARM_ATTEMPT 0 2026-10-07T01:05:21-22Z` `resume_epoch=100` again (replacement pod; the first pod died before its first new checkpoint at epoch 125).
- The second pod then trained about 38 min: h3-450k reached epoch 200 (`latest.json` epoch-0200 written 01:45:05Z, `activation_widths.jsonl` 201 rows, `pid_telemetry.jsonl` 201 rows, last row 01:43:39Z); h5-nb-s1 reached epoch 175 (`latest.json` epoch-0175 at 01:35:03Z, 197 rows, last row 01:43:45Z). The node was lost again about 01:44-01:48Z (Job `FailedIndexes` at 01:48:25Z for h5-nb-s1).
- State intact for resume: checkpoints `epoch-0175`+`epoch-0200` (h3-450k) and `epoch-0150`+`epoch-0175` (h5-nb-s1), each with `model.keras`, `optimizer.npz`, `state.json`; `state.json` `completed_epochs` 200 / 175, `code_sha256` e6ff034b... (equal to the run_study manifest in the Job script), `data_sha256` 61c0150c..., config sha matches the arm. History rows (201 / 197) are at least the checkpoint epochs, so `restore_checkpoint`'s truncation assert (`:324`) holds. No `.epoch-*` temp directory is left. The epoch-0100 checkpoint is gone (two generations kept), so a relaunch resumes from epoch 200 / 175, not 100. A stale `RSS_GATE_FAIL.json` (R1) is present and read by no code in r2 form.

## 4. Restoration observed for the 15 completed r2 arms

Source: first `[train] ... resume_epoch=` line in `r1/logs/pilot1005-<arm>-...-98dd28-r2-0.log`. (The pod log does not show it, as RUN.md notes; the PVC arm log does.)

| arm | resumed from epoch 100 (OBSERVED) | arm | resumed from epoch 100 (OBSERVED) |
| --- | --- | --- | --- |
| ctl-e-unc-c-s1 | **yes** | h2-e-2m-c-s1 | no (resume_epoch=0) |
| h1-e-350k-c-s1 | **yes** | h2-e-5m-c-s1 | no |
| h1-e-350k-noc-s1 | no | h2-e-750k-c-s1 | **yes** |
| h2-a07-1m-c-s1 | no | h3-e-350k-c-qkv1-s2 | **yes** |
| h2-a07-2m-c-s1 | no | h4-e-350k-c-w100-s1 | no |
| h2-a07-500k-c-s1 | no | h5-e-350k-c-nb-s2 | no |
| h2-a07-5m-c-s1 | no | | |
| h2-e-1m-c-s1 | no | | |
| h2-e-250k-c-s1 | no | | |

4 yes, 11 no. All 15 have `latest.json` = epoch-0500, 500 `activation_widths.jsonl` rows, and (option-c arms) 500 `pid_telemetry.jsonl` rows. Fresh 500-epoch runs are what STUDY R1 specifies; they are not defective, but they are not "resumed at epoch 100 (r2)" and cost 25 % more GPU time than planned. W&B step 1-104 clashes (PREFLIGHT 3d item 6) apply to the 4 resumed arms only. Cross-check from pod-log monitor counts (INFERRED, `NOTIFY_*` traced_epochs at the first 30-min tick) agreed with the arm-log result for every arm where both exist.

## 5. Fix candidates

| option | change | code sha | science rules | notes |
| --- | --- | --- | --- | --- |
| **A (recommended)** manifests + PVC state | New Job names (`-r3`), same bundle 98dd2875. (1) The 4 exit-76 arms: move the partial dir aside (`mv runs/pilot1005-<arm> runs/pilot1005-<arm>.aborted-r2`, nothing deleted) so they start fresh; (2) h3-450k (epoch 200), h5-nb-s1 (175), noc-s2 (400), h2-e-500k (475): relaunch as is, they resume; (3) pod deadline for E arms 18,000 s (the first r2 freeze value; A07 24,000 s unchanged); (4) add `hcc-chase-shor-c4715.unl.edu` to the nodeAffinity NotIn list (lost 6 first pods at about 00:57Z and 2 second pods at about 01:44Z; not in the current exclusion list). | none (manifest/handoff only, as in r2 via `freeze_p.py`) | none; configs, seeds, hyperparameters, stop epoch unchanged | Needs Kai for the PVC rename (overwriting/moving what this session did not create) and the usual launch approval. Estimated cost: 4 fresh x about 3.3 h + 2.0 + 2.1 + 0.8 + 0.2 = about 18 GPU-h (INFERRED). |
| B | Make `run_training` restart cleanly when history exists but no checkpoint | new tree, new bundle sha, new PREFLIGHT and CPU gate (about 1 h) | none, but changes resume semantics for production | Not needed for R1; consider for production hardening so the guard reports "no checkpoint ever written" and can self-clean. |
| C | `rm` the two history files in place | none | none | Same effect as A(1) but destroys evidence; not advised. |

Option A touches no science rule. It does mix provenance (11 fresh-from-0 arms, 4 replay-from-100 arms, up to 4 more replay from 175/200/400/475 arms); GPU replay is not bit-exact ([A5]), so the readout must carry the true resume epoch per arm, not a blanket "resumed at epoch 100".

## 6. GPU-h (pod start to train-container end, INFERRED from pod objects and PVC mtimes)

- r2, pods with a recorded end (21 pods): **45.0 GPU-h**. Per-arm range 0.10 h (the four exit-76 replacement pods) to 4.68 h (A07-1m).
- r2, 8 pods whose end is unrecorded (6 first pods, start about 00:47Z, replaced at 00:58:54Z: at most 0.2 h each; 2 second pods, start 01:00:48Z, Job failed 01:48:25Z: at most 0.8 h each): at most 2.8 GPU-h. **r2 total about 45-48 GPU-h.**
- R1 first launch: 6 gated pods at about 0.78 h (pod `h8khk`: 22:25:05Z to 23:12:07Z) = about 4.7 h, plus the completed qkv1-s1 arm about 3.0 h = **about 7.7 GPU-h**, plus an unknown (pods are gone) for 34 pre-arm pod failures on the 17 other Jobs. The RUN.md figure "about 18 GPU-h" assumed 23 gated pods and is not supported.
- **R1 total about 53-56 GPU-h against the 144 GPU-h cap** (about 38 %); the plan's worst case was 113. Plenty of headroom for option A (about 18 GPU-h, worst case 8 arms x 5 h = 40 GPU-h).

## Earliest phase to re-run

PREFLIGHT (new manifests/handoffs, deadline, node exclusion, corrected resume premise in 3d). STUDY and the bundle are unaffected. Documents to correct (by their owners, not by this ticket): RUN.md incident sections (6 gate kills, 17 unobserved R1 failures, resume only for 6 arms), PREFLIGHT 3d resume claim, readout marking text, `cluster-inventory.md` 2026-10-08 entry.

## Open items not resolved here

1. Why 15 R1 Jobs failed twice within one 18 s window at 22:53Z with no arm start (R1 pods gone). Ask cluster-ops to check NRP events/Prometheus if available; r2 launched the same manifests successfully 25 h later.
2. Whether c4715 is persistently unhealthy or one outage; the exclusion list is a manifest choice for Kai.
3. Whether the noc-s2 collapse (val_AUC 0.5) should be resumed or recorded as an outcome.
