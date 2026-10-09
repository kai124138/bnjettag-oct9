---
name: nrp-training-run
description: Run a BNJetTag training experiment on NRP Nautilus end-to-end — create or regenerate the job YAML, preflight, sync code to the PVC, launch, monitor, and bring results home. Use whenever the task involves submitting/monitoring a training or ROC job, adding a new experiment variant, editing kai-bn*-*.yaml job files, or anything mentioning Nautilus, kubectl, the kai-data PVC, or "launch round-N".
---

# NRP training run — the canonical lifecycle

Training NEVER runs locally. This skill turns an experiment idea into a completed run on
NRP Nautilus (namespace **`cms-ml`**) with artifacts back in this folder. Deep background:
`docs/infrastructure/nrp-nautilus-setup.md` (cluster access) and
`docs/infrastructure/manual-round-runbook.md` (the current end-to-end sequence). Superseded
PVC-era prose runbooks are in `_attic/legacy-archive/archive/nrp-runbooks/`.

## Mental model

- Pods are **disposable**. The pipeline is PVC-free: code ships as a **ConfigMap**, the
  dataset is fetched from Zenodo at pod start, and every artifact goes to **W&B**. Anything
  installed in a pod dies with the pod.
- One experiment = one k8s **Job** YAML in
  the canonical tree's `code/jobs/training/variants/` (`kai-bn14-*.yaml`).
  Experiments differ by their **config JSON** (`code/hgq2/configs/r14-*.json`), not by code
  forks: `arch.n_part`, `arch.n_feat`, `quant.weight`, `quant.act_bits`, seed.

## Lifecycle

1. **Create the config.** For a round sweep, edit the generators — `code/hgq2/configs/
   gen_r14.py` for the run configs and `variants/gen_r14_jobs.py` (plus
   `gen_r14_roc_jobs.py`) for the job YAMLs — and **regenerate**. Never hand-edit a
   generated config or YAML; it will be overwritten. For a one-off, copy the newest
   `kai-bn14-*` job and change only the config reference + `metadata.name` + labels.
2. **Local checks (cheap, always):** run `python3 nrp-lab/nrp_doctor.py lint <job>.yaml`
   from the lab repo — it exits non-zero on a fatal manifest error and catches the
   scheduling mistakes that have actually cost us runs (unreachable GPU products,
   throttled `parallelism`, failure limits that let a few bad indexes kill a campaign).
   Then: any embedded Python compiles (`python -m py_compile`); every referenced config
   JSON loads and builds.
3. **Ship the code.** Build the ConfigMap with
   `variants/make_code_configmap_r14.sh` — the ConfigMap is what actually trains, so a
   stale one silently runs old code. Verify it was replaced before launching.
4. **Preflight before launching anything:** run `code/hgq2/preflight_final.sh` in a cheap
   CPU pod; require the literal `PREFLIGHT_ALL_PASS`. It validates dataset access, builds
   every config, and prints the exact param count — record it, don't quote one from
   memory.
5. **Launch:** `kubectl apply -f <job>.yaml -n cms-ml`. Size `parallelism` to the campaign
   and to free capacity in your required pool — see "Concurrency is ours" in the setup doc.
   **Politeness means not camping idle GPUs, not serializing a campaign the cluster has
   room for**; an earlier version of this skill suggested "≤3 concurrent, staged is
   polite", and that got read as a throughput cap, which is where 2026's 2-3 concurrent
   runs came from. Prefer all-at-once (or a high `parallelism`): it survives the laptop
   closing, and the scheduler self-limits. Record what was used.
6. **Monitor:** `kubectl get jobs,pods -n cms-ml`, `kubectl logs -f <pod> -n cms-ml`, and
   W&B project **`BNJetTagAug`**. If a pod is Pending, read the `PodScheduled` condition
   (not `describe`) and follow **Scheduling, GPU pools and job shape** in
   `docs/infrastructure/nrp-nautilus-setup.md` — that section is authoritative for GPU
   resource names, quota, affinity and `parallelism`. Do not restate its rules here.
7. **Evaluate:** after training, apply `kai-roc-r5.yaml` (ROC on the held-out `val/` split);
   it writes `.npz` per model to the PVC.
8. **Bring artifacts home** to the canonical tree's `roc-results/` (and logs if
   needed), then **hand off to the `verify-roc` skill** — no number is real until recomputed.
9. **Log it:** append the run (goal, job files, where artifacts landed, deviations) to
   `.claude/memory/experiment-log.md`, newest on top.

## W&B layout (2026-08-01)

New job YAMLs / generators export `WANDB_ENTITY`, `WANDB_GROUP=<round-stage>`, and
`WANDB_TAGS=<round>,<stage>,<config>` alongside `WANDB_PROJECT`/`WANDB_RUN_NAME`
(see `gen_r13_jobs.py` for the pattern). Checkpoint durability is the versioned
`model-<leaf>` artifact (commit-checked in-pod, fatal on failure); fetch is
artifact-first with run-file fallback. Full layout:
`docs/infrastructure/wandb-layout.md`.

## Gotchas that have actually happened

- **Stale W&B secret kills every job**: `wandb.init()` is not wrapped in try/except. After a
  key rotation, update the `kai-wandb` secret in `cms-ml` and verify (sha256) before launch.
  The key file `wandb-api-key.txt` is a secret — never print or commit it.
- Idle-GPU pods get reaped; use batch **Jobs**, not interactive pods. A one-off run can
  use the legacy single-Job form (`backoffLimit: 0` + `activeDeadlineSeconds`); a
  multi-run campaign uses the Indexed form with `backoffLimitPerIndex`, `maxFailedIndexes`
  and a `podFailurePolicy` that ignores `DisruptionTarget`. Limits and a worked failure
  are in `docs/infrastructure/nrp-nautilus-setup.md`.
- Always confirm the ConfigMap actually got replaced before launching; a silent no-op
  reruns the previous code.
- Input discipline: Round-14 runs train on the `(N, 3)` L1-realistic input set. Their AUCs
  are only comparable to other results at the same N and the same input set — always carry
  the `l1x3` label and the N.
