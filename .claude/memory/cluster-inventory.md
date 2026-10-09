## 2026-10-10 — Pilot R1 r3: CPU helper pod kai-p1005-r3-rename-helper left running for Kai's rename-aside
CPU-only Pod (alpine:3.19, 100m/128Mi, PVC kai-data read-write at /data, deadline 7200 s) created 2026-10-09 20:41 UTC to run evidence/r3/pvc-rename-aside-r3.sh. Dry run printed 4 PLAN lines and DRY_RUN_OK; nothing on the PVC changed; no r3 Job submitted. nrp_doctor lint does not cover Pod kinds (reports "no Job manifest found"). Kai runs `--apply`, then the pod is deleted.
Check: `kubectl get pod kai-p1005-r3-rename-helper -n cms-ml` is gone after Kai's apply, and `ls -d .../r1/runs/*r2-partial-*` shows 4 dirs before any r3 Job is submitted.

- 2026-10-08 10:08 UTC | k8s-3090-01.usd.edu (RTX 3090): UnexpectedAdmissionError (device plugin GetPreferredAllocation: unable to get device link information) for 3 pods of campaign discovery-350k wave 1, then taint eviction. Excluded for new handoffs via campaigns/2026-10-08-discovery-350k/BRIEF.md operations.extra_excluded_nodes. **Check:** kubectl -n cms-ml get events --field-selector reason=UnexpectedAdmissionError; candidate for nrp_doctor known-bad list.

## 2026-10-08 — Pilot R1 r2: 8 of 23 arms failed (exit 76 resume, exit 124 deadline, pods lost at init)
Jobs kai-p1005r1-*-98dd28-r2 (bundle 98dd2875, submitted 2026-10-07 07:56 JST): 15 Complete, 8 Failed; R1 16/24 complete. Exit 76 `History exists without a committed checkpoint` (ablation.py:914) after a first pod lost at init: h1-e-350k-c-s2, h4-e-350k-c-w100-s2, h4-e-350k-c-w50-s1, h4-e-350k-c-w50-s2. Exit 124 at 11,581 s of a 12,000 s pod deadline: h1-e-350k-noc-s2, h2-e-500k-c-s1. Both pods Init:ContainerStatusUnknown, never trained: h3-e-450k-c-qkv1-s1, h5-e-350k-c-nb-s1 (node hcc-chase-shor-c4715.unl.edu seen for h3-e-450k and the w50-s1 pods). Resume restoration not observed in pod logs for completed arms; failed for the 4 exit-76 arms. Cause pending: campaigns/2026-10-05-pilot-program/review/REGRESSION_TICKET_r2-resume.md. Source: campaigns/2026-10-05-pilot-program/RUN.md.
Check: no relaunch of the 8 before the ticket names the cause and a new PREFLIGHT sha exists; the deadline for 124 arms and the node c4715 init losses are sized in that PREFLIGHT.

## 2026-10-06 — Pilot R1: RSS gate projected to epoch 7,000 on 500-epoch pilots; 23/24 arms killed at epoch 104
Bundle 98dd2875, Jobs kai-p1005r1-*-98dd28 on RTX 3090 (ry-gpu-01.sdsc and others). Each arm's host-RSS slope (~0.85 MB/epoch, baseline ~2.56 GB) was projected to epoch 7,000 (~8.5 GB > 8,192 MB limit) although the pilots stop at epoch 500 (~3.0 GB). Exit 5 is final by design, so no retries. One arm (h3-e-350k-c-qkv1-s1) completed. About 18 GPU-h spent. E at one arm per 3090 measured 15.4 s/epoch untraced (telemetry).
Check: superseded for pilots by Kai's 2026-10-07 gate-off relaunch (r2); for production, the gate horizon must equal the run's stop epoch; production sizes host memory for ~0.85 MB/epoch × 7,000.

## 2026-10-05 — Option-(c) CPU gate: 6 run_pack unit tests failed in the pinned image
`kai-chang1002c-cpugate-691946` (CPU, prp-gpu-2.t2.ucsd.edu): pytest 6 failed / 110 passed / 2 skipped, all in tests/test_run_pack.py. Every fake arm failed rather than the targeted one. Root cause pending (investigator; campaigns/2026-10-02-chang-option-c/REGRESSION_TICKET.md). Job left to finish its 58-config steps as evidence.
Check: no pilot launches on bundle 6919462c; the fix gets a new sha, PREFLIGHT and gate identity.

## 2026-10-01 — Diagnostic startup and bounded-history export limitations
Confirmation diagnostic kai-confirm1001-replay-a02s3-r1 failed before inference: exclusive output-leaf mkdir lacked its absent diagnostics parent. Pod exit1/restart0 at06:47:50Z; no retry. Handoff init passed. Required fix/tests/new attempt are recorded in campaigns/2026-10-01-recovery/confirmation-replay-preparation/REGRESSION_TICKET.md; implementation/review agents are unavailable due service usage limit.
B5 CPU diagnostic remains Running. All five activation history files exceeded the frozen8MiB export bound and were refused; a separate read-only recovery verified880343029bytes against source hashes/stat. Preserve original incomplete export status and validate later cert/entropy independently; no automatic PASS from separate transport.
Check: Pending confirmation top-level missing-parent/existing-leaf tests; b5 final receiver/result checks still required. Both immutable Job identities and evidence remain retained.


## 2026-09-29 — Delta A07 canary: K=3 does not fit an A10; stale k_result fields (back-filled 2026-10-04)
`kai-delta0926-canary-a07` pod `-0-tsrq7` on `hcc-nrp-shor-c5813` (A10): seed 3 hit TF RESOURCE_EXHAUSTED before epoch 1; pod exit 7; Job deleted 06:09:28Z before its second pod ran. `k_result.json` fields `per_arm.gpu_peak_mib` and `pod_host_peak_mib` were read from a stale 20:08Z pack.log and must not be used. Source: campaigns/2026-09-27-delta-screen/RUN.md (A07 canary section).
Check: A07 planning K on a 24 GB card is 2, not 3; the failed canary is not a clean K=2 certificate (campaigns/2026-10-01-recovery/SCIENTIFIC_GATES.md:40).

## 2026-09-28 — Delta canary-v2: operator manifest edit broke W&B tracking (back-filled 2026-10-04)
Pod `-0-w4cqm` ran a hand-edited manifest with `WANDB_MODE=disabled`; all E-k4 arms refused to start (`--track requires explicit WANDB_MODE=online`). Re-applied unmodified as `-0-5crk2` on c6013; stopped ~23:2xZ on Kai's call to free the A10 for the anchor pilot. Source: campaigns/2026-09-27-delta-screen/RUN.md:346-428.
Check: launch only the frozen manifest; any edit is a new PREFLIGHT identity.

## 2026-09-28 — Node c6017: epoch-0 NaN with 4–5 processes per GPU (back-filled 2026-10-04)
`hcc-nrp-shor-c6017.unl.edu` (A10) gave wrong, run-to-run varying initial EBOPs (off by 30–88 %) and epoch-0 NaN in every rep-A arm of `kai-delta0926-canary` pod `-0-6cnrd`. Single-process discriminator Jobs on c6017 and c5809 both gave the expected fingerprint 11559681, so the fault needs several processes sharing the GPU. Delta manifests exclude c6017; `nrp_doctor.py` KNOWN_BAD_NODES does not. Source: campaigns/2026-09-27-delta-screen/REGRESSION_TICKET.md; RUN.md:251-303.
Check: every manifest excludes c6017 until Kai decides whether to add it to KNOWN_BAD_NODES.

## 2026-09-28 — Delta canary reported Succeeded with every arm failed (back-filled 2026-10-04)
`kai-delta0926-canary` pod `-0-6q8kn` on c6017: all 12 arms failed at start (W&B project `BNJetTag-Delta` missing or not private), but the shell wrapper swallowed the exits, so the Job showed Succeeded with no measurement. Fixed in the wrapper: `FAIL=1` and `exit 7` (RUN.md:166-172). Still unfixed: `ablation.py:1280` crashes serializing NaN; `run_pack.py` has no rule for a whole pack diverging at epoch 0 (SCIENTIFIC_GATES.md:32). The `stage_run_id` W&B collision was accepted by decision (RUN.md:374-381). Source: campaigns/2026-09-27-delta-screen/RUN.md:57-112, 277-279.
Check: a pack Job's exit code reflects its arms; the two open fixes land under a new PREFLIGHT sha before any Delta cell launches.
