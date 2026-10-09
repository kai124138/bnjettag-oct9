# RUN — 2026-09-25-pt-weighting

Nothing here is quotable. Launch record: `research/bnjettag/results/ptw-n8-20260925/launch/`.
W&B group: https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-Weights/groups/ptw-n8-20260925
(the six p1 runs are temporarily in project `BNJetTagAug`, same group name; see incidents).

Written 2026-09-26 by results-analyst from the operations paragraphs of the research tree's
`research/.claude/memory/experiment-log.md` (entries 2026-09-25 "Pt-weighting N8 study
LAUNCHED" and 2026-09-26 "held-out ROC-test eval"), the launch record, the concatenated pod
logs `results/ptw-n8-20260925/pod_logs_all.txt`, and each checkpoint's `train_meta.json`.
No cluster-ops agent ran during the campaign; this is a reconstruction, not a live log. Every
number on this page (epochs, times, utilisation) is operational and none is a result.

## Launch record (`launch/`, listed 2026-09-26)

| file | what |
| --- | --- |
| `launch_manifest.json` | project, entity, group, ConfigMap `kai-ptw-n8-code-aad983805c`, code sha256 `aad983805c…`, per-file sha256, arm settings, packs, resources (10 CPU / 28 Gi after resubmit), pool, `epochs: 101`, `es_patience: 15`, `resume: none` |
| `configmap.json`, `hgq2.tar.gz` | the shipped code (immutable ConfigMap; `bnhgq2/pt_weights.py` and `train.py` sha re-checked in every pod) |
| `preflight.yaml`, `preflight.log`, `preflight-attempt1-aad98380.log` | CPU preflight job `kai-ptw-n8-0925-preflight-aad98380`: `PREFLIGHT_ALL_PASS` (params 18,657 all arms) + `PTW_SMOKE_PASS`; attempt 1 failed (matplotlib missing) |
| `benchmark.yaml`, `benchmark.log`, `benchmark-attempt1.log` | GPU packing benchmark `kai-ptw-n8-0925-bench-k6-aad983` (W&B off, seeds 1–2 × 3 arms on an RTX 4090); attempt 1 died from a bash errexit bug in the poll loop |
| `kai-ptw-n8-0925-k6-p{1..4}.yaml`, `training-jobs.yaml` | the four submitted job manifests (as resubmitted at 10 CPU / 28 Gi with `WANDB_PROJECT=BNJetTag-Weights`) |
| `submitted-p1-14cpu-36gi/` | p1 as actually submitted (14 CPU / 36 Gi, project BNJetTagAug) |
| `old-bnjettagaug/` | p2–p4 manifests from the first (never-scheduled) submission, project BNJetTagAug |
| `submitted_at.txt` | three stamps: 02:16:18Z (unlabelled in the file; p1 per the log), 02:33:52Z (unlabelled in the file; the log puts the first p2–p4 resubmit at 02:45Z, so this stamp is not assigned here), 03:56:40Z "p2-p4 resubmitted with WANDB_PROJECT=BNJetTag-Weights" |
| `startup_status.txt` | `kubectl get jobs,pods` at ~03:57Z: p1 Running on `hcc-nrp-shor-c5834.unl.edu`, p2–p4 Pending |
| `p1-startup.log` | p1 pod log through fit start |
| `p1_move_plan.json` | pending plan to move the six p1 runs from BNJetTagAug to BNJetTag-Weights (W&B UI only) and copy their artifacts |

## Jobs

All four pods landed on an NVIDIA GeForce RTX 4090 (24,564 MiB). Only p1's node hostname is in
the record (`startup_status.txt`); for p2–p4 the pod logs give the GPU and its PCI bus id only.
Times are the `[setup]`, `[pack] started` and `[done]` stamps in `pod_logs_all.txt`.

| job | arms (index → arm) | node | started (UTC) | state |
| --- | --- | --- | --- | --- |
| `kai-ptw-n8-0925-k6-p1` | 0 base-s1, 1 ptw5-s1, 2 ptwnc-s1, 3 base-s2, 4 ptw5-s2, 5 ptwnc-s2 | `hcc-nrp-shor-c5834.unl.edu`, RTX 4090 bus c1:00.0 | setup 02:17:35Z, fit 02:27:59Z | done 05:32:26Z; whole-pod GPU-util mean 87.5 % (n = 2319 samples); 14 CPU / 36 Gi; W&B project BNJetTagAug |
| `kai-ptw-n8-0925-k6-p2` | 0 base-s3, 1 ptw5-s3, 2 ptwnc-s3, 3 base-s4, 4 ptw5-s4, 5 ptwnc-s4 | hostname not captured; RTX 4090 bus 01:00.0 | setup 05:03:09Z, fit 05:15:00Z | done 08:30:50Z; GPU-util mean 89.8 % (n = 2471); 10 CPU / 28 Gi; BNJetTag-Weights |
| `kai-ptw-n8-0925-k6-p3` | 0 base-s5, 1 ptw5-s5, 2 ptwnc-s5, 3 base-s6, 4 ptw5-s6, 5 ptwnc-s6 | hostname not captured; RTX 4090 bus 81:00.0 | setup 07:40:53Z, fit 07:54:54Z | done 11:13:02Z; GPU-util mean 88.3 % (n = 2524); 10 CPU / 28 Gi; BNJetTag-Weights |
| `kai-ptw-n8-0925-k6-p4` | 0 base-s7, 1 ptw5-s7, 2 ptwnc-s7, 3 base-s8, 4 ptw5-s8, 5 ptwnc-s8 | hostname not captured; RTX 4090 bus c1:00.0 | setup 05:32:33Z, fit 05:45:15Z | done 08:58:24Z; GPU-util mean 88.7 % (n = 2449); 10 CPU / 28 Gi; BNJetTag-Weights |

Every job reached `[done]`; all 24 `[pack] <run> OK` lines are present. Wall time per pod
about 3 h 05 m to 3 h 18 m for six packed runs (first epoch ~145 s, then ~120 s per epoch
per run, ~61 ms/step). Benchmark before launch: util mean 94.6 % / median 98 %, 5.0 GiB GPU
memory, 18.4 GiB RAM peak, 5.9 CPU cores for K = 6.

## Per-arm final state

Schedule: 101 epochs requested, EarlyStopping on validation macro AUC with patience 15 and
restore-best-weights; the committed checkpoint is `model_best.keras` (W&B artifact
`model-ptw-n8-0925-<arm>-s<seed>`). `best epoch` is `train_meta.json` `best_epoch` (0-based;
the Keras "Restoring model weights from the end of the best epoch" line in the pod log is
1-based, so 74 here is 75 there). Checkpoints fetched 2026-09-26 to
`results/ptw-n8-20260925/checkpoints/<arm>-s<seed>/` (`model_best.keras`, `input_std.json`,
`train_meta.json`); the log records `best_val_macro_auc` + `best_epoch` matching the pod logs
24/24, params 18,657 every arm. All runs stopped normally: no crash, no resume, no restart.

| arm | seed | epochs completed | checkpoint id / sha | note |
| --- | --- | --- | --- | --- |
| base | 1 | 90 of 101 (ES) | run `p02fd5f7` (BNJetTagAug); best epoch 74 | |
| base | 2 | 88 of 101 (ES) | run `tv02q49a` (BNJetTagAug); best epoch 72 | |
| base | 3 | 101 of 101 | run `3449ai23`; best epoch 86 | |
| base | 4 | 79 of 101 (ES) | run `46d6gb1f`; best epoch 63 | |
| base | 5 | 100 of 101 (ES) | run `tgtyawcb`; best epoch 84 | |
| base | 6 | 101 of 101 | run `19nzx756`; best epoch 92 | |
| base | 7 | 87 of 101 (ES) | run `btxv1r52`; best epoch 71 | |
| base | 8 | 75 of 101 (ES) | run `6xm7pukl`; best epoch 59 | |
| ptw5 | 1 | 94 of 101 (ES) | run `yfkz2s8j` (BNJetTagAug); best epoch 78 | |
| ptw5 | 2 | 55 of 101 (ES) | run `oh4slz8q` (BNJetTagAug); best epoch 39 | earliest stop of the 24 |
| ptw5 | 3 | 101 of 101 | run `mauhr40m`; best epoch 94 | |
| ptw5 | 4 | 65 of 101 (ES) | run `xwmdzsln`; best epoch 49 | |
| ptw5 | 5 | 73 of 101 (ES) | run `194a8sx8`; best epoch 57 | |
| ptw5 | 6 | 83 of 101 (ES) | run `27put61d`; best epoch 67 | |
| ptw5 | 7 | 82 of 101 (ES) | run `rulagnqf`; best epoch 66 | |
| ptw5 | 8 | 71 of 101 (ES) | run `zjp971lg`; best epoch 55 | |
| ptwnc | 1 | 101 of 101 | run `jn36pt11` (BNJetTagAug); best epoch 87 | |
| ptwnc | 2 | 66 of 101 (ES) | run `b8ba8ap0` (BNJetTagAug); best epoch 50 | |
| ptwnc | 3 | 88 of 101 (ES) | run `0vdhhae6`; best epoch 72 | |
| ptwnc | 4 | 93 of 101 (ES) | run `hndvd8ju`; best epoch 77 | |
| ptwnc | 5 | 87 of 101 (ES) | run `rezh4mvm`; best epoch 71 | |
| ptwnc | 6 | 78 of 101 (ES) | run `eillqsh1`; best epoch 62 | |
| ptwnc | 7 | 100 of 101 (ES) | run `soalo2yt`; best epoch 84 | |
| ptwnc | 8 | 101 of 101 | run `hauh2xqg`; best epoch 98 | |

Run ids without a project note are in `BNJetTag-Weights`. Five runs reached epoch 101; the
other nineteen ended by early stopping (patience 15 after the best epoch), which is the
schedule as designed, not a failure. The gate for this phase ("every arm reached its committed
epoch count or its failure is recorded") is met on that reading: the committed count is
"101 or early stop".

Weighted arms logged `pt_weights ON` (train split only; seed 1: ptw5 effective sample
fractions W 0.69, Z 0.70; ptwnc W 0.36, Z 0.33). `pt_weights.json` and the weight PNGs are
not in the model artifact; the post-run `[aux]` upload put them on each run's files.

## Incidents and resumes

No resume happened and none was possible (`resume: none` on the train.py path; a killed pod
would have lost all six of its runs). Neither `cluster-inventory.md` (lab tree) nor the
research tree has an entry specific to this campaign; the lab inventory's rule-PACK entry
(added 2026-09-26) covers the per-arm CPU/memory sizing that incident 3 is about.

| when (UTC) | what | `cluster-inventory.md` entry | Check line |
| --- | --- | --- | --- |
| 2026-09-25 (before launch) | CPU preflight attempt 1 (`preflight-attempt1-aad98380.log`) failed: `matplotlib` missing from the pinned pod deps, so the weighted arms would have died at the weight plot after the data download. Fixed by pinning `matplotlib==3.11.0` in the pod pip line; no code change; attempt 2 `PREFLIGHT_ALL_PASS` + `PTW_SMOKE_PASS`. | none | prose only |
| 2026-09-25 (before launch) | GPU benchmark attempt 1 (`benchmark-attempt1.log`) died from a bash `errexit` bug in the utilisation poll loop. Fixed (`set +e` in the util-logger subshells); attempt 2 completed. | none | prose only |
| 2026-09-26 02:32Z → 02:45Z | p2–p4 Pending (FailedScheduling in a busy pool; queued, not failed) 15 min after submission at 14 CPU / 36 Gi. Deleted (never started) and resubmitted at 10 CPU / 28 Gi (benchmark peak 5.9 cores, 18.4 GiB; pool nodes have only 20–28 allocatable CPU per 4 GPUs). p1 left at 14/36. | rule PACK entry (2026-09-26) is the general lesson; no incident entry | `[rule PACK]` in `nrp-lab/nrp_doctor.py` for the sizing; the queueing itself is prose only |
| 2026-09-26 ~03:57Z | W&B project correction: study project is `BNJetTag-Weights` (created via SDK, no dummy runs). p2–p4 (still Pending) deleted and resubmitted with `WANDB_PROJECT=BNJetTag-Weights` (env outranks `train.wandb_project`; parsed YAML diff = project only). p1 left running, so its six runs and their `model-<leaf>` artifacts are in `BNJetTagAug` under the same group name. Move is UI-only and artifacts must be copied separately (`p1_move_plan.json`, status PENDING as of the record). | none | prose only |
| 2026-09-26 (eval) | Checkpoints for s1–s2 were fetched from `BNJetTagAug`, s3–s8 from `BNJetTag-Weights` (log 2026-09-26). Consumers that look up `model-<leaf>` by project will not find p1's six models until the copy exists. | none | prose only |
