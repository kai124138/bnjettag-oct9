# Matched N8 / N64 exploratory screen, 2026-09-22

The requested comparison is constituent count at fixed arithmetic budget. This
campaign starts fresh; it does not resume or replace the ongoing historical runs.
All 12 architecture/budget configurations, five attention variants, and eight
Engram configurations map to 19 distinct configurations after normalizing N and
seed and merging identical controls. Both N8 and N64 are generated: 38 outcomes.
The mapping back to every original name is in `index.json` and each config.

The initial screen uses seed 1, 50 epochs, batch 256, initial learning rate 0.0002,
one warmup epoch and 49 decay epochs. PID warmup is one epoch. The gradual-budget
control reaches its final cap at epoch 10 (transitions at 0, 5, 10). This faster
schedule is common within each pair and is a new exploratory protocol; its results
must not be presented as equal-training comparisons with the historical
1000-epoch runs. The learning rate is ten times the historical value. One seed and
50 epochs do not establish convergence or statistical superiority.

Each pair retains the original absolute arithmetic cap (250k, 350k, or 500k).
Training uses the inherited PID penalty; acceptance is a strict checkpoint cost
check. A soft training penalty cannot guarantee feasibility. The selected result
is maximum validation accuracy among feasible checkpoints. If no checkpoint fits,
the minimum-cost diagnostic is explicitly marked infeasible, never promoted as a
budget-compliant result. The test set is not used.

Engram uses native HGQ2 backbone cost plus the documented structural memory
arithmetic estimate. This is not synthesized hardware cost. Storage is a separate
contract: 64 KiB logical and 2 MiB estimated replicated tables, equal at both N.
The replicated cap is larger than the old N16 pilot's 512 KiB because the read-port
replication estimate grows with constituent count. The E07 N64 hashed-bigram
memory alone costs 838272, above its 350000 cap; it is recorded as statically
infeasible and is excluded from GPU scheduling.

Data use the existing 62 training HDF5 files, stable descending-pT sorting, the
same 496000/124000 train/validation identities, split seed 1 and order seed
20260912. Per-feature standardization is fitted on the training split separately
for each N. Array hashes, label equality and identical split permutation are
checked before model preflight.

The runtime starts from the frozen published Engram source. Cost tracing runs
before validation. TF32 is explicitly disabled, and each epoch is evaluated using
a freshly reloaded saved checkpoint; the selected artifact is copied from that
exact candidate. The first canary exposed a live-versus-loaded inference mismatch:
FP32 restored exact accuracy, but AUC differed by 3.2e-7. Canonical saved-checkpoint
evaluation avoids selecting on a different inference path. Failed canary evidence
is retained separately; corrected runs start fresh with the `fast50-fp32` suffix.
Checkpoint save/reload verification retains the strict 1e-7 metric tolerance; no
historical checkpoint or tolerance is modified. CPU preflight builds and reloads
every configuration. A two-epoch GPU canary then checks the complete training and
export path on both N values with architecture and Engram cases. Canary checkpoints
continue into the same 50-epoch configs after passing.

GPU packs hold two or three independent processes with separate output directories,
optimizer/PID state, and resumable checkpoints. N8 uses seven packs and N64 nine,
for sixteen GPU packs and 37 trained runs. All packs are queued, with up to twelve
GPU pods concurrent; heavier N64 packs go first. This ceiling accounts for ten
older running jobs and other group GPU demand (18 running, 10 pending at inspection). GPU utilization is logged every minute;
an arm that produces no checkpoint for 30 minutes is terminated for retry. The
cluster scheduler determines start times. A few-hour turnaround is a target for
screening, not a guaranteed completion time.

Code/config bundles are immutable ConfigMaps, verified by SHA256. Results live at
`/data/constituent-study-20260922/fp32` on the existing PVC; shared data remain
in the parent directory. W&B remains private in
`BNJetTag-Engram-Experimental`, group `constituent-20260922-fast50`. Job generation,
lint, server dry runs, and launch evidence live in the lab's
`local/constituent-study-20260922/`. No old jobs are cancelled by this campaign.
