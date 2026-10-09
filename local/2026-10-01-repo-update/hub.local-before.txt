# Current work: full-run confirmation

**Updated 24 September 2026 · 12 confirmations active**

[Full-run confirmation campaign](CONFIRMATION_RUNS_20260924.md) · [Machine-readable status](confirmation-status-20260924.json) · [Complete historical index](EXPERIMENT_INDEX_20260923.md) · [Project results](../../README.md)

The active campaign runs every declared confirmation for **1,000 epochs**. It does not use a 100-epoch or other intermediate promotion decision. Validation metrics, eBOP measurements and checkpoints are recorded throughout training, then final comparisons are made after the declared schedules finish.

## Active execution

**Snapshot: 24 September 2026, 14:45 PDT (21:45 UTC).** Six N8 confirmations and six N64 confirmations share one NVIDIA A10. Three batch-256 processes run at a time, and steady utilization is 99–100%.

| Constituents | Arms | Seeds | Runs | Epoch target | eBOP target |
|---:|---|---|---:|---:|---:|
| 8 | A00, A02, A03 | 2 and 3 | 6 | 1,000 | 350,000 |
| 64 | A07, E02, E05 | 2 and 3 | 6 | 1,000 | 5,000,000 |

The queue advances the least-complete runs in 20-epoch chunks. Each boundary releases TensorFlow host memory and restores the exact model, optimizer, PID and epoch state. It is an operational restart, not a scientific gate. The queue has no intermediate decision rungs, and reaching the cost target does not stop training.

At the snapshot, the N8 runs were at epochs 120–318. The first three N64 runs had each committed two epochs, and the remaining three were queued. These are progress values, not final results.

## Latest held-out evaluation

The selected A02 and A11 seed-1 checkpoints produced byte-identical logits across two independent reloads. Held-out data were used only after checkpoint selection.

| Arm | Selected epoch | eBOPs | Held-out accuracy | Held-out macro-OvR AUC |
|---|---:|---:|---:|---:|
| A02 | 913 | 349,298 | 60.7850% | 0.860432 |
| A11 | 789 | 479,462 | 62.3335% | 0.873813 |

A02 uses the primary 350k target. A11 uses a separate 500k target, so the two values do not establish a same-budget comparison.

## Completed September 23 campaigns

All 27 architecture and attention continuations reached 1,000 epochs. Five of 12 architecture runs recorded a checkpoint within their configured budgets; none of the 15 attention runs recorded a checkpoint within 350,000 eBOPs.

| Campaign | Runs | Finished | Feasible checkpoint |
|---|---:|---:|---:|
| Architecture A00–A11, seed 1 | 12 | 12 | 5 |
| Attention B00–B04, seeds 4–6 | 15 | 15 | 0 |

[Final A/B results](TRAINING_RESULTS_20260923.md) · [Exact recorded metrics](training-results-20260923.json)

## Engram and constituent-count evidence

The four original N16 Engram training loops reached 1,000 epochs. E00 passed outer validation; E01–E03 failed final metric reproduction, and none produced a feasible checkpoint under the augmented 350k target.

The separate matched N8/N64 screen retains all of its 50-epoch, partial and static-rejection records because they document work already performed. It found an interesting N64 memory signal but no feasible checkpoint. That screen is historical evidence and does not control the active full-run queue.

[Original Engram report](ENGRAM_STUDY.md) · [Matched N8/N64 screen](CONSTITUENT_SCREEN_20260923.md) · [Frozen source](../../code/constituent-study-20260922/README.md)

## Evaluation boundaries

- Internal validation selects checkpoints and records accuracy, macro one-vs-rest AUC and eBOPs.
- The 260,000-jet held-out archive evaluates fixed selections and never chooses checkpoints.
- N8 and N64 use separate cost targets and remain separate cost comparisons.
- eBOPs are a computational proxy, not an FPGA resource, latency or timing-closure result.
- Final seed comparisons wait for the full 1,000-epoch schedules.

The retired selective protocol remains available as a dated historical document in [the original batch plan](TRAINING_BATCH_PLAN_WITH_FROZEN_BACKBONE_FOLLOWUP.md). It is not the active execution policy.
