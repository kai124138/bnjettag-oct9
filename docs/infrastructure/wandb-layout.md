---
title: Weights & Biases layout
status: current
date: 2026-09-08
---

# Weights & Biases layout

The definitive description of how this project uses W&B, effective 2026-08-01
(decisions.md entry of the same date). Everything earlier remains valid but
unstructured; nothing on W&B was rewritten retroactively.

## Role

W&B is **provenance and durability, never the number of record**. Training pods are
emptyDir-only, so a run's W&B copy is the only durable home of its checkpoint; but
every AUC quoted anywhere is recomputed locally from the `.npz` arrays
(`verify-roc`), and every resource/latency figure is parsed from the raw csynth XML.
The W&B metric mirrors exist so drift is *detectable*, not so they can be quoted.

## Identity

| Item | Value |
|---|---|
| Entity | `kayamaguchi-uc-san-diego` (env `WANDB_ENTITY` overrides) |
| Projects | `BNJetTagAug` (Round 14, current); `bnjettag-final` and `bnjettag-bitnet` (earlier rounds, frozen) |
| Auth | key in `bnjettag/wandb-api-key.txt` (never print/commit); NRP secret `kai-wandb` |
| Resolution order | env `WANDB_PROJECT` > config `train.wandb_project` > `bnjettag-final` — implemented once in `bnjettag/code/hgq2/bnhgq2/wandb_util.py` |

## Runs

Run name = the leaf `<config>-s<seed>` (unchanged). New structure, all emitted by
`wandb_util.init_kwargs` and set per-job in the YAML generators:

- **group** = the round/stage (env `WANDB_GROUP`, e.g. `r13-stage1`) — one UI group
  per pre-registered arm set.
- **job_type** = `train` | `distill` | `eval` | `hls` | `dataset`.
- **tags** = env `WANDB_TAGS` (comma list: round, stage, config) + per-call tags
  (variant, seed).

Absent env vars reproduce the pre-2026-08 behaviour exactly, so old YAMLs stay valid.

## Artifacts (the durability contract)

| Type | Name | Produced by | Contents |
|---|---|---|---|
| `model` | `model-<leaf>` | `bnhgq2/train.py`, `distill_r12.py` | `model_best.keras`, `train_meta.json`, `input_std.json`, r13 `front.json` + front checkpoints |
| `evaluation` | `evaluation-<run_prefix>` | `roc_final.py eval-all --wandb-log` | the `.npz` arrays + `roc_auc.md` + overlay PNG |
| `synthesis` | `synthesis-<report>` | `log_hls_wandb.py` (local, post-mulder) | raw `csynth.xml` + convert manifest |
| `dataset` | `hls4ml-lhc-jet-5class-{val,train}` | `_attic/pre-r14/code/training/log_dataset_wandb.py` | checksum **references** only (nothing uploaded); n=260,000 asserted |

`wandb_util.log_files_artifact` blocks on the server commit (`.wait()` + manifest
check) and raises on failure — training treats that as fatal (the pod is
emptyDir-only). This replaced the 2026-07-15 hand-rolled 5-retry size-compare
durability gate. Legacy `wandb.save` run-file mirrors are still written
best-effort so pre-overhaul consumers keep working.

## Lineage

`dataset` → (used by) `train` run → `model-<leaf>` → (used by) `eval` run and the
HLS `synthesis` run (via the manifest's `wandb_run` pointer). Checkpoint fetch is
artifact-first with run-file fallback (`wandb_util.fetch_checkpoint`), so all
pre-overhaul checkpoints remain fetchable.

## Val/test side by side

`roc_final.py --wandb-log` backfills `test_macro_auc` into each source training
run's summary, next to its `best_val_macro_auc`. The two are different data and
different evaluations — never conflate them; the backfill exists precisely so a
mismatch between the W&B copy and the published table is visible.

## What W&B deliberately does NOT do here

- **No Sweeps.** Hyperparameter scans stay as pre-registered one-job-per-point
  YAMLs (`gen_*_jobs.py`) — a sweep agent fits NRP batch jobs poorly and would
  bypass the pre-registration discipline. Groups/tags provide the UI comparison.
- **No numbers of record.** See Role above.
- **No W&B on mulder.** Synthesis results are logged locally after
  `fetch_mulder_reports.sh`.
