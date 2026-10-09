# Training results snapshot — 21 September 2026, 17:39 PDT

Checkpoint read completed: 2026-09-22T00:39:42.715826+00:00.

Internal-validation values copied from durable trainer state; not recomputed from saved predictions. Running jobs can advance during the snapshot. Epochs in the table are completed epochs; stored selected-point epoch indexes are zero-based. No significance or held-out superiority claim.

| Run | Completed epochs | Budget | Best feasible accuracy | Best feasible AUC | Best feasible EBOPs |
|---|---:|---:|---:|---:|---:|
| batch20260917-a00-s1 | 761 | 350,000 | 58.77% | 0.8502 | 349,322 |
| batch20260917-a01-s1 | 780 | 350,000 | 58.25% | 0.8473 | 344,270 |
| batch20260917-a02-s1 | 663 | 350,000 | 60.55% | 0.8580 | 342,832 |
| batch20260917-a03-s1 | 1000 | 350,000 | 59.44% | 0.8563 | 346,222 |
| batch20260917-a04-s1 | 1000 | 350,000 | — | — | — |
| batch20260917-a05-s1 | 681 | 350,000 | — | — | — |
| batch20260917-a06-s1 | 612 | 350,000 | — | — | — |
| batch20260917-a07-s1 | 994 | 350,000 | — | — | — |
| batch20260917-a08-s1 | 545 | 350,000 | — | — | — |
| batch20260917-a09-s1 | 887 | 500,000 | — | — | — |
| batch20260917-a10-s1 | 622 | 250,000 | — | — | — |
| batch20260917-a11-s1 | 534 | 500,000 | 62.38% | 0.8736 | 453,439 |
| batch20260918-b00-s4 | 1000 | 350,000 | — | — | — |
| batch20260918-b00-s5 | 1000 | 350,000 | — | — | — |
| batch20260918-b00-s6 | 1000 | 350,000 | — | — | — |
| batch20260918-b01-s4 | 1000 | 350,000 | — | — | — |
| batch20260918-b01-s5 | 1000 | 350,000 | — | — | — |
| batch20260918-b01-s6 | 1000 | 350,000 | — | — | — |
| batch20260918-b02-s4 | 1000 | 350,000 | — | — | — |
| batch20260918-b02-s5 | 1000 | 350,000 | — | — | — |
| batch20260918-b02-s6 | 989 | 350,000 | — | — | — |
| batch20260918-b03-s4 | 1000 | 350,000 | — | — | — |
| batch20260918-b03-s5 | 1000 | 350,000 | — | — | — |
| batch20260918-b03-s6 | 867 | 350,000 | — | — | — |
| batch20260918-b04-s4 | 1000 | 350,000 | — | — | — |
| batch20260918-b04-s5 | 1000 | 350,000 | — | — | — |
| batch20260918-b04-s6 | 1000 | 350,000 | — | — | — |
| engram-e00-s1 | 561 | 350,000 | — | — | — |
| engram-e01-s1 | 1000 | 350,000 | — | — | — |
| engram-e02-s1 | 1000 | 350,000 | — | — | — |
| engram-e03-s1 | 1000 | 350,000 | — | — | — |

Architecture: 5/12 have a feasible checkpoint; 2/12 Kubernetes indexes succeeded. Attention: 0/15 feasible; 13/15 indexes succeeded, remaining runs at 989 and 867 completed epochs. Engram: 0/4 feasible; E01–E03 reached 1,000 epochs but their job indexes failed; E00 at 561.

Engram COMPLETE.json is written by the inner trainer before the outer runner reloads and checks selected-checkpoint metrics. Therefore its presence does not establish successful end-to-end validation. E01 original-pod traceback confirms an AUC reload mismatch at the outer assertion (absolute tolerance 1e-7). E02/E03 failed-attempt logs also showed metric comparison mismatches in the earlier live diagnostic.

Engram E02 final-epoch logged validation accuracy 54.55%, AUC 0.8322 at 380,009 augmented-cost EBOPs; E03 52.55%, 0.8203 at 440,525. Both exceed 350,000. Their augmented accounting is not identical to the public native-only cost convention. These are provisional training measurements, not successfully verified final exports.

Raw evidence: [checkpoint snapshot](checkpoints.json), [compact summary](summary.json), [Kubernetes status](cluster.json).
