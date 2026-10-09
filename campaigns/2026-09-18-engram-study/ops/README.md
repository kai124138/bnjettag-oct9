# Engram pilot operations

## Outcome — 2026-09-19 20:00 UTC (supersedes the snapshots below)

Job `kai-engram-screen-e100-a10364ed` is **Failed** (`FailedIndexes`): indexes 2,3
(E02, E03) completed with reports; indexes 0,1 (E00, E01) exhausted
`backoffLimitPerIndex`. **All four arms trained to cumulative epoch 100**; their
`epoch-0100` checkpoints and W&B resume artifacts were committed first. No arm met the
350k EBOPs budget, so the selected checkpoint is `model_min_ebops.keras`.

The failure is the post-training reload check at `run_engram.py:275`
(`AssertionError: Not equal to tolerance rtol=0, atol=1e-07`). It is not a node lottery:
Turing/Volta GPUs (2080 Ti, V100) reproduce the logged accuracy exactly, while every
Ampere/Ada GPU (L40, L40S, A10, 3090, RTX 5000 Ada) returns one identical, different
value (|Δacc| 1.3e-4–2.7e-4, i.e. 16–33 of 124,000 jets), including in the pod that
trained the model. TF32 arithmetic in the fresh `load_model`+`predict` path is the
working hypothesis and is **not yet tested**. Separately, `atol=1e-7` on macro AUC is
tighter than cross-architecture FP32 reproducibility (E01 on a 2080 Ti: accuracy exact,
AUC off by 1.5e-6). Per-pod evidence: `finalize-failure-diagnosis.json`.

Prepared, **not submitted**: `gpu-job-finalize-r1.json`
(`kai-engram-finalize-e100-a10364ed-r1`) — same immutable bundle, configs and output
roots; indexes 0,1 only; resumes at epoch 100, so it only runs the finalize step; adds
`NVIDIA_TF32_OVERRIDE=0`; requires `NVIDIA-L40` (the class that produced both selected
checkpoints); one attempt per index. Lint shows two deliberate WARNs (narrow pool,
backoff 0); server dry-run passed; the old Job has no active pods. If it fails, the
assertion precedes every report write, and the remaining route is a source change, which
alters `source_manifest` and therefore needs a new output root — the scientific owner's
decision.

## Execution snapshot — 2026-09-18 18:35 UTC (historical)

The user removed the low-key constraint. The existing Job
`kai-engram-screen-e100-a10364ed` was patched **in place from parallelism 1 to 4**.
Live lint and server dry-run passed. The Job UID, original start time, 24-hour
deadline, four arms, configurations, immutable bundle, project, and cumulative
100-epoch target are unchanged. The frozen bundle manifest records the original
submission; `gpu-job.json` and `freeze_bundle.py` now specify parallelism 4.

All four indexes are submitted. E00 pod `kai-engram-screen-e100-a10364ed-0-bt22w`
continues Running on `rci-tide-gpu-02.sdsu.edu`, with epoch 42 observed. Its existing
UID and training progress were preserved by the patch. E01 `...-1-pzjjg`, E02
`...-2-s79c4`, and E03 `...-3-rzgjv` are Pending for available cluster resources;
the scheduler reports 83 nodes with insufficient generic GPUs, 39 with
insufficient CPU, and 9 with insufficient memory. They will start as capacity
becomes available without another submission.

`parallel4-verification.json` contains the full scheduler conditions and identity
checks. `launch-status.json` records the timestamped current execution policy.

## Original submitted pilot — historical 2026-09-18 snapshot

The scientific audit and hypotheses were completed before submission. The final
immutable code bundle is `a10364eda9f4e5b8fbdfe1b4eadbae7b60006362bc9f493cafb056e74dedc792`.
The ConfigMap bytes were rehashed after upload and match exactly.

CPU Job `kai-engram-preflight-a10364ed-r2` **succeeded** with all 11 synthetic
correctness groups, all four production models, full cache hash verification, and
literal `PREFLIGHT_ALL_PASS`. Production parameter counts: E00 16,875; E01 9,716;
E02 26,101; E03 42,485. The first CPU job encountered a node-local stalled PVC
read; its pod was confirmed gone before the same-bundle replacement ran all gates.
Both CPU/GPU generators now exclude the affected node. The original incident and
replacement evidence are preserved separately in this folder.

[The separate W&B project](https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-Engram-Experimental)
was created with verified `PRIVATE` access; an anonymous project read was denied.
No invitations, public reports, or publication steps were performed.

GPU Job `kai-engram-screen-e100-a10364ed` has been submitted. Its first E00 pod,
`kai-engram-screen-e100-a10364ed-0-n2tsm`, scheduled on
`k8s-haosu-19.sdsc.optiputer.net` and is Running. The bundle hash check passed and
the GPU gate passed on an RTX 2080 Ti. **Physics epoch 1 completed and its durable
`epoch-0001/model.keras` checkpoint was verified.** Its runtime source hash matches
`source_manifest.json`. The intended private W&B run `10dd9f63e913` reports
`completed_epochs: 1`, `screening_target_epochs: 100`, and accuracy-based selection.
Consult `launch-status.json` and `first-epoch-verification.json` for the timestamped
latest state. The campaign is ongoing; this startup verification does not establish
a memory accuracy gain or hardware improvement.

The original submission used four seed-1 arms, one GPU at a time, cumulative epoch 100 of the
1,000-epoch schedule, and a 24-hour whole-job deadline. Results/checkpoints live
under `kai-data:/data/engram-study-20260918/runs/<arm>/` and the private W&B project.
No automatic promotion or synthesis is scheduled.

Evidence: `bundle-manifest.json`, `remote-bundle-verification.json`,
`preflight-complete.log`, `preflight-job-complete.json`, `synthetic-preflight.json`,
`production-preflight.json`, `private-project-verification.json`,
`submitted-gpu-job.json`, `current-gpu-pod.json`, and `launch-status.json`.

Prepared 2026-09-18. This directory is the operator's separate pilot launcher. The
scientific owner must finish the theoretical audit and hypotheses before code is
frozen or any remote job is created.

The current launcher uses E00–E03, seed 1, cumulative epoch 100 of the existing 1,000-epoch
schedule, up to four GPUs concurrently, and a 24-hour whole-job deadline. There is
no automatic promotion, synthesis, publication, or invitation workflow.

## Isolation and live readiness

- W&B: `kayamaguchi-uc-san-diego/BNJetTag-Engram-Experimental`. A read-only GraphQL
  check on 2026-09-18 returned no existing project. Create with `access: "PRIVATE"`
  only after the handoff, then require an authenticated PRIVATE response and an
  anonymous read denial before training. `WANDB_QUIET` is a log preference; privacy
  comes from the verified project access setting.
- Durable output: `kai-data` PVC at `/data/engram-study-20260918/`.
- Shared immutable input: `/data/batch20260917/n16/data/`. Metadata was read live
  from our current training pod and shows 496,000 training and 124,000 validation
  jets, 16 constituents, `[pt, etarel, phirel]`, split seed 1, order seed 20260912,
  and all four array SHA256 hashes. Final CPU preflight rehashes every array.
- Raw input recorded by that cache: `/data/hls4ml_lhc_jet/train/train` (62 files).
- Runtime: `python:3.12`, pinned `publication/requirements-training.txt`. GPU jobs
  use TensorFlow 2.21.0 with CUDA dependencies; CPU preflight omits only CUDA extras.
- Live doctor at approximately 09:07 PDT: 46/200 namespace pods, A100 quota 6/24.
  Existing campaigns had 16 active jobs' pods total, including one pending; new
  pilot requests only one generic GPU and does not alter those workloads.
- Excludes the inventory's Fullerton failed GPU and the newly observed
  `k8s-chase-ci-07.calit2.optiputer.net`: `UnexpectedAdmissionError`, `no healthy
  devices present; cannot allocate unhealthy devices nvidia.com/gpu`. Existing
  failed pod evidence was captured without changing its campaign.

## Concrete sequence after audit handoff

Run from the repository root:

```bash
python3 local/engram-study/ops/freeze_bundle.py
python3 nrp-lab/nrp_doctor.py lint local/engram-study/ops/preflight-job.json
python3 nrp-lab/nrp_doctor.py lint local/engram-study/ops/gpu-job.json
kubectl -n cms-ml create --dry-run=server -f local/engram-study/ops/code-configmap.json
kubectl -n cms-ml create --dry-run=server -f local/engram-study/ops/preflight-job.json
kubectl -n cms-ml create --dry-run=server -f local/engram-study/ops/gpu-job.json
kubectl -n cms-ml create -f local/engram-study/ops/code-configmap.json
kubectl -n cms-ml create -f local/engram-study/ops/preflight-job.json
```

Require successful CPU Job completion, `ENGRAM_PREFLIGHT_PASS`, four
`PRODUCTION_BUILD_PASS` lines with parameter counts, and literal
`PREFLIGHT_ALL_PASS`. Verify the immutable ConfigMap bundle SHA against the local
bundle manifest. Copy the preflight evidence home before proceeding.

```bash
python3 local/engram-study/ops/private_project.py --create-private
python3 nrp-lab/nrp_doctor.py status
kubectl -n cms-ml create -f local/engram-study/ops/gpu-job.json
```

The project helper only uses the existing API key in memory, never prints it, and
does not change access on a pre-existing non-private project. GPU startup repeats
the read-only privacy check. Indexed arms share no output directories; every arm
uses the run lock and immutable identity/resume checks already in the trainer.

Monitor Job status, per-pod scheduler/failure conditions, logs, and the private
W&B project. The CPU and GPU job names contain the immutable bundle hash. Preserve
the bundle and ConfigMap for exact resumption; do not modify configs or source to
resume the same output root. Re-running a rung is a deliberate new Job name with
the same immutable bundle, config and output paths, after confirming no other
writer is active.

After the four arms reach 100 epochs, copy reports and prediction files home and
run the scientific owner's validation comparisons. This is an early optimization
screen. It is not evidence of final accuracy or synthesized hardware benefit.

W&B API references: [project access documentation](https://docs.wandb.ai/guides/hosting/iam/access-management/restricted-projects/).
The live GraphQL schema exposes `UpsertModelInput.access: String`; read access via
`project(name: ..., entityName: ...) { name access }`. The installed SDK's
`upsert_project` helper lacks an access parameter, so the helper uses a narrow
GraphQL mutation for private creation and verifies its result independently.
