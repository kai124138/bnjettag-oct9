# Confirmation campaign — 2026-09-23

This directory records the staged confirmation campaign requested on 2026-09-23. The campaign uses the immutable constituent-study bundle `26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45` and the committed N8/N64 caches on the `kai-data` PVC.

## 1. Deterministic checkpoint evaluation

Cluster job `kai-confirm-eval-a02-a11-0923-r4` completed successfully. Each checkpoint was independently loaded twice, and both validation and held-out logits were byte-identical across reloads (maximum absolute difference `0.0`). The evaluator mirrors the trainer's five binary one-vs-rest AUC calculations. Historical validation replay allows `1e-6` for runtime/kernel differences; observed AUC differences were `3.92e-7` for A02 and `-3.53e-8` for A11, with exact accuracy replay.

| Arm | Selected epoch (zero-based) | eBOPs | Held-out accuracy | Held-out macro AUC |
| --- | ---: | ---: | ---: | ---: |
| A02 | 912 | 349,298 | 60.7850% | 0.860432 |
| A11 | 788 | 479,462 | 62.3335% | 0.873813 |

Full confusion matrices, per-class AUCs, checkpoint hashes, prediction hashes, and replay deltas are in `evaluation-results.json`. The raw completed-job log is `evaluation-r4.log`.

## 2. Full-run policy

Every active confirmation run is configured for 1,000 epochs. Intermediate validation metrics, eBOP measurements, and checkpoints are recorded for analysis but never stop a run or decide whether another run starts. Final candidate selection happens only after the declared runs finish.

The queue uses exactly one GPU and keeps three training processes resident at a time. It advances the least-complete runs in 20-epoch chunks so TensorFlow releases host memory periodically. Those process restarts are operational boundaries only: each run automatically reloads its exact model, optimizer, PID, and epoch state and continues toward epoch 1,000.

Historical two-epoch canaries and 50-epoch screens remain in this directory as provenance for work already performed. They are not part of the active execution policy.

The N8 checkpoint-compatible config files still contain an inherited `constituent_study.protocol` string describing the source 50-epoch study. That field is provenance and must remain byte-identical so the existing checkpoints pass their resume hash guard. The executable settings are `train.epochs: 1000`, `stop_on_target: false`, and the unified queue's empty `decision_rungs` list.

## 3. A00/A02/A03 N8 seed confirmation

Six fresh 1,000-epoch runs cover seeds 2 and 3 for A00, A02, and A03. Training batch size remains 256 so these runs preserve the optimizer recipe being confirmed. Validation batch size is 4,096. Three independent training processes share each GPU, which raises utilization without changing the scientific batch definition.

CPU preflight job `kai-confirm-preflight-0923-a257d6` passed all six configs, including model construction, serialization/reload, initial eBOP tracing, data hashes, and deterministic initialization evidence.

GPU canary job `kai-confirm-canary-0923-a257d6` completed two epochs for all six runs. Both GPUs were NVIDIA A10s. Excluding the first startup and final teardown sample, measured utilization was 97–99%, with a 99% median across eight minute samples. All processes exited zero and the trainer's selected-checkpoint reload verification passed. See `canary-utilization.json` and `canary-results.json`.

Full continuation job `kai-confirm-full-0923-a257d6` resumed every run from epoch 2. It used two GPUs with three runs per GPU and wrote one checkpoint per epoch under `/data/confirmation-20260923/architecture/runs` before the one-GPU policy replaced it.

### 2026-09-24 recovery

The original full job was interrupted after a 36 GiB pod was OOM-killed. Its retry watchdog also compared fresh processes with old checkpoint timestamps and prematurely terminated retries. Every committed checkpoint remained valid. A temporary recovery advanced the runs further before being stopped at the user's request to keep the campaign on one GPU.

The N8-only recovery job `kai-confirm-onegpu-0924-05af9c-r2` used exactly one NVIDIA A10. Three processes at a time shared that GPU and measured 99% training utilization. It preserved every committed checkpoint while recovering from the original job's interruption. The unified N8/N64 queue supersedes this job and resumes the same N8 checkpoint directories.

The two source digests have different documented scopes: `7f9e9307...` covers all top-level study scripts plus `bnhgq2`, while `345a057a...` covers the direct trainer plus `bnhgq2`. Both come from the same immutable bundle whose archive SHA-256 is `26f3cc40...`.

## 4. A07/E02/E05 N64 confirmation

The six A07/E02/E05 N64 configs cover seeds 2 and 3 at a separate 5,000,000 eBOP budget. Each uses 1,000 epochs, batch size 256, validation batch size 4,096, and no intermediate decision gate. CPU preflight job `kai-confirm-n64-preflight-0924-fe8029` passed all six configs, including model construction, serialization/reload, initialization evidence, data hashes, and initial eBOP tracing.

## 5. Unified one-GPU queue

Active job `kai-confirm-onegpu-0924-e0c0a3-r2` contains all 12 confirmations: six N8 runs and six N64 runs. Every config declares 1,000 epochs, the queue contains no decision rungs, and three processes share one NVIDIA A10 on `gpu-06.nrp.mghpcc.org`. N8 runs resume their committed checkpoint state; N64 runs begin from epoch zero. The first three N64 processes started successfully, each committed its epoch-1 checkpoint, and steady samples measured 99–100% GPU utilization. See `full-run-launch-status.json`. Held-out data remain evaluation-only and never select checkpoints.
