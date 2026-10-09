---
title: local — running the notebooks on this laptop
status: current
date: 2026-09-14
---

# local — running the notebooks on this laptop

The same notebooks as `nrp-lab/`, on the machine you are sitting at. No Kubernetes, no
tunnel, no six-hour clock. This is the right place to debug; the pod is the right place to
check that what you debugged still behaves in the cluster's environment.

```
./setup-local.sh              # register the kernel (train split)
./setup-local.sh --data val   # ... or against the val split, if train isn't downloaded yet
```

Then in VS Code: **Select Kernel → Jupyter Kernel… → BNJetTag (local)**.

Five notebooks. The first three in order: `00_env_check` (is the kernel what you think it
is), `01_smoke_train` (does training run), `02_binary_transformer_workbench` (inspect the
real binary transformer stage by stage, debug gradients and activations, and measure
compute, memory, and latency; smoke training is opt-in).
`03_einsum_vs_matmul` stands alone — it checks the attention einsums against the `tf.matmul`
spelling on numbers, parameter count and MACs, and needs no data, so it runs anywhere in
seconds. `04_conference_figures_pre_ebops` rebuilds the fixed-precision Round-14 conference
figures from the linked research tree, with an explicit firewall against the later enforced
EBOPs-target runs. Not *Python Environments…* — that picks a bare interpreter with none of the variables below. If the
kernel isn't listed, reload the window so VS Code rescans kernelspecs.

If it is still not listed after a reload, check the kernelspec's *format* rather than
re-running setup: ipykernel 7 writes `kernel_protocol_version` and
`metadata.supported_encryption` into `~/Library/Jupyter/kernels/bnjettag-local/kernel.json`,
and VS Code's Jupyter extension drops any kernel carrying them — silently, so
`jupyter kernelspec list` still shows it and everything looks fine. `setup-local.sh` strips
both keys for exactly this reason.

## Why this works without editing a single notebook

The notebooks never hardcode a path. They read `PYTHONPATH`, `BNHGQ2_TRAIN_DATA`,
`BNHGQ2_OUT_ROOT` and `BNHGQ2_STORE` from the environment, which on the pod were exported by
the container in `kai-lab.yaml`. `setup-local.sh` writes the same variables into a Jupyter
kernelspec, pointed at local paths. Selecting the kernel is the whole configuration step.

| | pod | here |
| --- | --- | --- |
| code | `/data/lab/repo/bnjettag/code/hgq2` (pushed by `lab.sh sync`) | the research tree, directly |
| data | `/data/hls4ml_lhc_jet/train/train` on the PVC | `<research tree>/data/train` |
| outputs | `/data/lab/outputs` | `local/outputs/` (gitignored) |
| device | one cheap-tier NVIDIA GPU | the CPU |

## The W&B guardrail is inverted here — read this once

The pod was safe because it mounted **no** W&B secret: `wandb_enabled()` returned False and a
scratch run physically could not reach the record.

**That protection does not exist on this laptop.** `~/.netrc` holds a W&B credential, so
`wandb_enabled()` returns True, and with no environment override `resolve_project()` falls
through to entity `kayamaguchi-uc-san-diego`, project **`bnjettag-final`** — a real project.
An unguarded notebook run here would write into it.

So the kernelspec sets two independent layers, and both matter:

- `WANDB_MODE=offline` — nothing is transmitted,
- `WANDB_PROJECT=bnjettag-lab` — and if it ever were, not into the real project.

If you run the pipeline from a plain terminal instead of this kernel, you get neither. Export
them yourself, or use the kernel.

## What is still not local, and is not going to be

- **Full training.** Round 14 is 101 epochs over 62 files. The measured 3-epoch smoke over 2
  files takes 17 s of training here; the real thing is ~1000× that work on a CPU. Rounds run
  as batch Jobs on Nautilus. That has not changed.
- **Vitis HLS synthesis.** Linux only, and it wants far more RAM than this machine has.
  `mulder` still does it.
- **Anything quotable.** This environment is drifted from the cluster on one package —
  **numpy 2.4.6 here against the cluster's 2.5.0**, because `da4ml 0.5.2` is installed in the
  research tree's venv and numba pins numpy ≤ 2.4. Deliberate, documented in
  `../docs/infrastructure/home-pc-cluster-recreation.md` as KNOWN TRAP 2, and reason enough
  on its own that numbers from here are for debugging only. The rule is unchanged:
  `RESEARCH.md` numbers come from cluster Jobs, recomputed through `verify-roc`.

## Getting the data

The val split is already in the research tree. The train split is Zenodo record 3602260,
`hls4ml_LHCjet_150p_train.tar.gz` (~2.7 GB) — extract it to `<research tree>/data/train` as a
flat directory of `.h5` files, matching the layout `data/val` already uses.

Until it is there, `./setup-local.sh --data val` registers a kernel named **"BNJetTag (local,
VAL-as-train)"**. The substitution is in the display name on purpose: training on the
evaluation split is fine for a smoke test and fatal for anything else, so it should be
visible in the kernel picker rather than buried in a variable.
