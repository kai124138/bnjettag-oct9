# Batch CPU preflight / cache protocol

The cache preparation reads the existing 62-file training dataset once at N=32, then derives N=8/16/32 from the same sorted constituent order and shuffled event IDs. Each N has independently computed train-only normalization. All three caches have 496,000 training and 124,000 internal-validation events, with labels preserved. N=8 must be byte-identical to the old ablation cache before any READY marker is written.

Cache roots: `/data/batch20260917/n8/data`, `/data/batch20260917/n16/data`, `/data/batch20260917/n32/data`. Each contains the four `.npy` arrays, `data_info.json` with all four hashes and source/split/normalization metadata, and an atomic `READY.json` committed after readback verification. Preparation holds an exclusive `prepare.lock`; consumers validate under a shared lock. No old experiment outputs are modified.

An initial preflight using code SHA `d58bbb3885454019a465eb282e1971302af4732b637375224d039dab107f41d8` completed raw loading but exposed a remote-filesystem bottleneck: NumPy saves of feature-major non-contiguous arrays emitted approximately 8-KiB writes. After roughly one minute, only 5 MB of the 47.6-MB N8 training array had been written; `/proc` showed 630 writes and disk wait. The job was stopped before any READY marker, with logs and job provenance preserved under `attempt-d58bbb38/`.

The serialization fix converts arrays to C-contiguous memory only immediately before `np.save`, after all normalization calculations and hashes. This preserves scientific values and avoids many small filesystem calls. Synthetic checks verified that deriving each top-N input from the N32 read preserves the canonical loader's array layout and float32 normalization statistics. The public helper `publication/code/launch/prepare_batch_cache.py` and local helper are byte-identical.

The revised immutable code SHA is `ddd3761d2a566790b42a1c55c036727df624e58a6f65305c1aeca3d05365584d`, ConfigMap `kai-batch0917-code-ddd3761d2a`. It includes the serialization fix and explicit parameter-count fields in model preflight evidence. The revised Job is limited to 2 CPUs, 8 GiB RAM, zero GPUs, and 1800 seconds. Pinned training package versions are preserved; the CPU installation omits TensorFlow's CUDA extra and mounts no credentials. Require successful Job completion and literal `PREFLIGHT_ALL_PASS` before GPU training.

## Final status

The revised Job completed successfully at 2026-09-17T15:21:45Z after 12m07s, printing `BATCH_CACHES_ALL_PASS` and `PREFLIGHT_ALL_PASS`. All twelve model builds/gradient steps/save-reloads passed, as did probability-precision variation, tensor/channel initialization equivalence, checkpoint/config/code guards, and resume-versus-uninterrupted model/optimizer/PID checks. Synthetic smoke testing took 228.89 seconds. Parameter counts and complete structured evidence are in `preflight-result.json`; these synthetic EBOPs are not achieved trained-budget results.

All three caches passed readback hash verification; labels and permutation hashes agree across N. N8 matches the previous cache byte-for-byte. The bulk-write fix reduced N16 and N32 preparation (including verification) to 8.33 and 8.57 seconds. Both CPU attempt Jobs and the superseded code ConfigMap were removed. The final immutable ConfigMap remains for the authorized GPU workers. No old experiments were modified.
