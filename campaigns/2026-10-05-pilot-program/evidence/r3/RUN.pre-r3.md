# RUN — pilot program, round 1 (launched 2026-10-06 06:53 JST)

Nothing here is quotable. The readout, R2, R3 and production are **not** launched; the readout waits
for arbiter v2 Q1–Q5 (STUDY [A5] S1).

| field | value |
| --- | --- |
| bundle | `98dd2875b7c902bb881562a7acbf00f7cf266a369a74528b6fb8471e0cdc0059` (ConfigMap `kai-pilot1005-code-98dd2875b7`) |
| CPU gate | `kai-pilot1005-cpugate-98dd28`: GATE_RESULT PASS 06:47 JST (threshold, cpu_gate, nb_pairing, pytest all 0) |
| reviews | STUDY arbiter v3 PASS; PREFLIGHT critical v2 R1 PASS; S1–S3 grep-checked (JOURNAL) |
| approval | `local/2026-10-05-execution/r1-98dd28-approval.json` (Kai 2026-10-06) |
| cleared records | `PREPARED-cleared-r1-ctl-e-unc-c-s1-r1-h1-e-350k-c-s1-r1-h1-e-350k-c-s2-r1-h1-e-350k-noc-s1-r1-h1-.json` (24 entries; L4 byte rule: 0 violations; 24/24 VALID) |
| submitted | 24/24 single-arm Jobs `kai-p1005r1-*-98dd28`, 06:53 JST, via `run_handoff.py launch --submit` |
| shape | 1 arm per pod, RTX 3090, pod deadline 20,800 s, FailIndex on 5/76/124/137/143, stop at epoch 500 |
| spend cap | 144 GPU-h hard (worst case 143.87; expected about 105–131) |
| state at launch | 2 Running, 22 Pending (3090 queue); namespace pods 118/200 before submit |
| K-1 | accurate uniform-attention rows: current rule stop-for-Kai (not yet ruled) |

Follow-up (fresh session):
```
kubectl get jobs -n cms-ml | grep kai-p1005r1-
kubectl logs job/<name> -n cms-ml --tail=50
```

## Incident 2026-10-06: 23 of 24 arms stopped by the RSS gate at epoch 104 (found 14:19 JST)

- **Outcome:** 23 Jobs Failed, 1 Complete (`h3-e-350k-c-qkv1-s1`, 500 epochs, about 2.9 h, exit 0).
- **How each failed:** `ARM_MEMORY_GATE_FAILED`, then `ARM_RSS_GATE_FINAL`, pod exit 5 (FailIndex,
  final by design, no retry). Elapsed about 2,317–2,766 s per pod.
- **Root cause (configuration, not training):** the RSS gate fits host-RSS growth over epochs
  5–104 and projects it to **epoch 7,000**, the config's full schedule. The pilots stop at
  epoch 500. Example `h1-e-350k-c-s1`: `slope 0.850 MB/epoch, baseline 2563, projection 8514 at
  epoch 7000, limit 8192 → FAIL`. Projected to epoch 500 it is about 2,988 MB, far under the
  limit. The one survivor presumably had a lower slope.
- **Missed by the reviews and the gate:** the CPU gate never runs 100 GPU epochs, and
  PREFLIGHT §3c checked the gate limit, not its horizon.
- **Training telemetry looked normal:** canary and controller-audit monitors PASS, no divergence.
- **Spend:** roughly 23 × about 0.65 h + 1 × about 2.9 h ≈ 18 GPU-h (approximate, from pod
  start/finish times), against the 144 cap.
- **Production implication:** at 0.85 MB/epoch, a 7,000-epoch E run reaches about 8.5 GB host
  RSS, so production would trip the same gate. It needs a higher limit (pods have 10 GiB) or a
  leak fix, and is decided at the production PREFLIGHT.
- **Code and configs untouched (RULES §5).** A fix means a new PREFLIGHT, a new bundle sha (if
  the horizon is in code or config) or new manifests (if it is an env setting), a gate, and new
  Job names. Nothing relaunched; waiting for Kai.

## Relaunch r2, 2026-10-07 07:56 JST: 23 arms resume from epoch 100 with the memory gate off

| field | value |
| --- | --- |
| approval | `local/2026-10-07-execution/r1b-relaunch-approval.json` (Kai, 2026-10-07) |
| review | `review/PREFLIGHT_critical_r2_v1.md`: PASS (L1 §3d text fixes landed; L2 0 violations vs 98dd28; L3 exactly 23 keys) |
| build | bundle 98dd2875 unchanged; `--no-rss-gate --job-suffix=-r2`; split pod deadline (PREFLIGHT §3d addendum) |
| records | `PREPARED-cleared-r2e.json` (19 E arms, 12,000 s), `PREPARED-cleared-r2a.json` (4 A07 arms, 24,000 s) |
| submitted | 23/23 Jobs `kai-p1005r1-*-98dd28-r2`, 07:56 JST; 23 Pending at +20 s |
| not relaunched | `h3-e-350k-c-qkv1-s1` (completed 500 epochs on 2026-10-06) |
| worst-case spend | 94.98 GPU-h; R1 total worst case about 113 of 144 |
| expected | resume at checkpoint epoch-0100; E arms about 2.2-2.5 h, A07 arms about 4.5-5 h after start |
| readout marking | every r2 arm "resumed at epoch 100 (r2)"; H3 s1 uninterrupted |

The resume line goes to the arm log on the PVC; the pod log shows it only on failure (review C2).
Check it there or from W&B steps 105 onward.

## Incident r2, 2026-10-08: 15 of 23 Jobs Complete, 8 Failed (3 failure modes); diagnosis pending

Observed 2026-10-08 ~02:30 JST with read-only `kubectl get jobs/pods` and `logs --tail`. Jobs `kai-p1005r1-*-98dd28-r2`, submitted 2026-10-07 07:56 JST. Nothing is running. R1 stands at 16/24 complete (15 r2 plus h3-e-350k-c-qkv1-s1 from the first launch).

| mode | arms | evidence |
| --- | --- | --- |
| exit 76 | h1-e-350k-c-s2, h4-e-350k-c-w100-s2, h4-e-350k-c-w50-s1, h4-e-350k-c-w50-s2 | `RuntimeError: History exists without a committed checkpoint` (bnhgq2/ablation.py:914) on both ARM_ATTEMPTs ~01:06Z, after the first pod was lost at init (Init:ContainerStatusUnknown, 137). w50-s1 final pod: `POD_EXIT_FINAL rc=1 phase=train elapsed_s=349 exit=76` |
| exit 124 | h1-e-350k-noc-s2, h2-e-500k-c-s1 | `ARM_DEADLINE_EXCEEDED`, `POD_EXIT_FINAL rc=124 elapsed_s=11581` (pod deadline 12,000 s; run_pack budgets 9,365 / 11,393 s) |
| pods lost at init | h3-e-450k-c-qkv1-s1, h5-e-350k-c-nb-s1 | both pods Init:ContainerStatusUnknown, `train` stuck in PodInitializing, never trained. Node hcc-chase-shor-c4715.unl.edu (h3-e-450k; h4-w50-s1 pods also there). Job condition reason `FailedIndexes` (h5 checked); the DeadlineExceeded wording was not seen in the Job conditions |

- **Checkpoint restoration:** expected from the code read (JOURNAL 2026-10-07 07:40), not observed in pod logs for the completed arms (the resume line goes to the PVC arm log). Observed to FAIL for the four exit-76 arms.
- **Diagnosis pending:** `review/REGRESSION_TICKET_r2-resume.md` (investigator). No cause is stated here.
- **Code, configs and manifests untouched (RULES §5).** Kai authorized a fix and relaunch of the 8 arms on 2026-10-08; that is a new PREFLIGHT with a new code sha, not an edit to the launched run.
