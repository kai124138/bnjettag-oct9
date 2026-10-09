# Training launch record — 17 September 2026

**Latest status: failed, execution handed back to the user.** The Indexed Job reached MaxFailedIndexesExceeded at16:34UTC; no batch Pods remain. A00 has60saved epochs and A01has39. The rest of this launch record describes the historical submission. Use [the manual runbook](../../MANUAL_RUNBOOK_TRAINING_AND_R4_SYNTHESIS.md) and single-arm generator for deliberate restarts.

- Job: `kai-batch0917-screen-e100`, namespace `cms-ml`.
- Persistent outputs: `/data/batch20260917/n{8,16,32}/runs/batch20260917-aXX-s1/`.
- Code archive SHA: `ddd3761d2a566790b42a1c55c036727df624e58a6f65305c1aeca3d05365584d`.
- ConfigMap: `kai-batch0917-code-ddd3761d2a`, immutable; keep until all resumptions finish.
- At most2 worker Pods, oneGPU/4CPU/12GiB RAM each. Replacement policy waits for failure before replacement. Batch72-hour deadline, per-training-process23-hour timeout, one retry per index, abort after more than2 failed indices. No service-account token mounted.
- Models, optimizer/PID state, selected checkpoints and epoch history persist on PVC; W&B checkpoint artifacts upload every25epochs.
- A00 and A01 both passed first-real-epoch/checkpoint verification; GPU/model startup and W&B credentials verified. See `wandb-snapshot.json` for the latest private numerical monitoring values and `public-progress.json` for the redacted public snapshot.
- Preflight: all12 configurations build, receive finite gradients and save/reload; matching-channel/tensor initialization,8-bit-softmax variant, one-layer gates, seed2resume/uninterrupted equality, combined-variant resume, no-op rung retries, config/code hash rejection all passed. `preflight-result.json` and `preflight-summary.json` are synthetic checks, not physics results.
- N8 cache is byte-identical to the previous experiment. N8/N16/N32 share event/label/split hashes with train-only standardization perN. A slow noncontiguous-array write was fixed only during serialization; data values/hashes unchanged. First failed I/O attempt retained in `attempt-d58bbb38/`; both CPU Jobs were removed, no GPU was spent on preparation.

## Progress hub and publication scope

Public hub: https://github.com/kai124138/BinaryTransfomerJettager/tree/main/docs/current-work

Live W&B: https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-Batch20260917

W&B project is private; an asynchronous question asks whether to keep it private for Russell's existing/granted access or make only this batch project public. No visibility change was made. The public GitHub page is a timestamped snapshot, not an autonomous updater. It exposes runstate/epoch progress and plans/configs; private numerical progress is excluded pending sharing choice.

Automatic approval rejected the broad initial GitHub payload (additional resultrecords, runtime/operationalcode, provenance). A reduced hub/plan/config-only publication was approved and pushed. Runtime fixes, tests, detailed frozen-head results and code-manifest remain locally available but uncommitted/unpublished in `publication/`; do not accidentally stage them with `git add -A`. The complete original public-document draft is preserved under `../full-publication-draft/`.

The local `publication/code/analysis/update_current_work.py` supports authenticated W&B, explicitly suppliedJSON and anonymous public W&B. Anonymous fetch of this private project fails closed and preserves existing snapshots. Its15 tests and7 launch tests passed. No scheduled GitHub Action or credentials were installed.

## Continue / monitor

```sh
kubectl get job,pods -n cms-ml -l app=kai-batch0917-screen
kubectl logs -n cms-ml job/kai-batch0917-screen-e100 --tail=30
```

Do not change the config or code archive for a resumed run. For later screening rungs, generate a new outer job specifying selected actual indexes and `run_batch_screen.py --stop-after 200` or400; the underlying config remainsepochs1000,decay999. Use the same perN root and immutable archive. For final1000 completion use `run_ablation.py train` without `--benchmark-epochs`. No B/F/H jobs have launched.
