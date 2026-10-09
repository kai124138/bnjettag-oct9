# Matched N8/N64 exploratory screen — 23 September 2026

[Complete experiment index](EXPERIMENT_INDEX_20260923.md) · [Original N16 Engram study](ENGRAM_STUDY.md)

The fresh constituent-count campaign tested 19 distinct architecture, attention and Engram-inspired setups at N=8 and N=64. It used one seed and a new 50-epoch schedule with peak learning rate 2e-4. This is a short exploratory comparison, not an equal-training replacement for the historical 1,000-epoch runs.

**Follow-up update, 24 September:** A07, E02 and E05 at N64 now have seed-2/3 confirmations in the [full 1,000-epoch queue](CONFIRMATION_RUNS_20260924.md) under a separate 5,000,000-eBOP target. There is no intermediate promotion gate.

[Exact results](../../results/constituent_study/results-20260923.json) · [Frozen runtime source and configurations](../../code/constituent-study-20260922/README.md) · [Source manifest](../../results/constituent_study/source_manifest.json)

## Execution result

| Outcome | Cases |
|---|---:|
| Completed all 50 epochs | 28 |
| Stalled/crashed after 33–40 epochs | 7 |
| Completed only the two-epoch canary | 2 |
| Statically infeasible and not scheduled | 1 |
| **Total intended comparisons** | **38** |

The indexed Kubernetes Job ended with 12 successful packs and four failed indexes. A pack can contain multiple independent arms, so pack counts and scientific-run counts differ. The seven partial runs are A01-N8, A02-N8, A08-N8, A09-N8, A10-N8, B01-N8 and B03-N8. E02-N8 and E03-N8 retained only their verified two-epoch canaries. E07-N64 was rejected before scheduling because its fixed memory arithmetic alone is 838,272 operations against a 350k cap.

**No trained case recorded a feasible checkpoint at its configured target.** The tables below therefore show final-epoch diagnostics for completed runs, not budget-compliant selections.

## Completed N8 runs

| Variant | Validation accuracy | Macro-OvR AUC | Selection cost |
|---|---:|---:|---:|
| B04 gradual schedule | **63.41%** | **0.8788** | 600,329 |
| B02 no positional table | 62.61% | 0.8731 | 637,091 |
| E05 four-bit memory | 62.37% | 0.8723 | **418,159** |
| A00 channel/FFN64 | 62.17% | 0.8747 | 696,951 |
| A03 tensor/FFN32 | 62.16% | 0.8727 | 632,846 |
| E04 two-block gated memory | 61.69% | 0.8733 | 648,406 |
| E07 hashed rank-bigram memory | 61.33% | 0.8660 | 491,803 |
| A07 one block | 61.12% | 0.8660 | 411,302 |
| E06 64-row tuple memory | 60.56% | 0.8659 | 430,891 |
| A06 D16 | 60.54% | 0.8584 | 386,219 |

B04 has the strongest completed N8 endpoint. A06 has the lowest final cost but remains 36,219 operations above its 350k target. E05 gives the strongest observed accuracy/cost compromise among the completed memory cases, but it is also infeasible.

## Completed N64 runs

| Variant | Validation accuracy | Macro-OvR AUC | Selection cost |
|---|---:|---:|---:|
| E02 ungated memory | **66.60%** | **0.8997** | 4,720,386 |
| E05 four-bit memory | 66.52% | 0.8988 | 4,816,654 |
| E03 gated memory | 65.46% | 0.8979 | 4,966,751 |
| E04 two-block gated memory | 63.91% | 0.8880 | 9,517,420 |
| E06 64-row tuple memory | 62.56% | 0.8825 | 4,927,819 |
| A07 one block | 57.95% | 0.8619 | **4,634,372** |
| Best other non-memory endpoint | 56.41% | 0.8563 or lower | 5,195,955 or higher |

The memory variants occupy the highest observed N64 accuracy positions. Among setups that completed at both N values, E05 improves by 4.16 percentage points from N8 to N64, E04 by 2.22 points and E06 by 2.00 points. In contrast, the completed non-memory pairs generally perform worse at N64 under this short schedule. This is evidence that warrants follow-up, not proof that memory generally benefits from longer sequences: the study has one seed, a 50-epoch high-LR schedule, incomplete N8 memory controls and no feasible model.

## Interpretation limits

- Values use the 124,000-jet internal-validation split; the held-out archive was not evaluated.
- Cost for Engram cases is native backbone EBOPs plus a structural memory estimate. It is not synthesized hardware cost.
- All N64 endpoints are 4.6–10.8 million operations, far beyond the intended 250k/350k/500k limits.
- Seven N8 comparisons are incomplete, including several direct architecture/attention pairs.
- W&B remains private; publishing these numerical records and frozen source does not change project visibility.

The screen established an interesting N64 memory signal while its original fixed-budget objective failed. The active follow-up explicitly chose a separate 5,000,000-eBOP N64 target and full 1,000-epoch schedules; this historical screen does not stop or promote those runs.

[Return to current work](README.md).
