---
title: nrp-lab — a JupyterLab kernel on a Nautilus GPU
status: current
date: 2026-09-17
---

# nrp-lab — a JupyterLab kernel on a Nautilus GPU

A scratch environment for trying things out interactively: a GPU pod on NRP running
JupyterLab, with our own `bnhgq2` code and the full HLS4ML LHC Jet dataset already
mounted. It exists so that "does this code still run?" and "what does this array
actually look like?" can be answered in a cell instead of a six-hour cluster job.

It is **not** part of the round-14 reproduction path. Nothing computed here is quotable
(see *Guardrails* below).

**Reach for `../local/` first.** Since 2026-09-08 the same notebooks run on the laptop
against the same research tree, with no cluster, no tunnel and no six-hour deadline — and a
measured 3-epoch smoke train is *faster* there (17 s) than it is here (61 s), because at
18,657 parameters a GPU never gets to use its FLOPs. Come to the pod when you need the
cluster's environment specifically: CUDA, the exact numpy pin, or the full train split on the
PVC without downloading it.

---

## Once, before the first session

Two things. First, `kubectl` with the Nautilus context and membership of `cms-ml` — if
`kubectl get pods -n cms-ml` returns something, you are ready. Setup and the usual failure
modes: `../docs/infrastructure/nrp-nautilus-setup.md`.

Second, tell this repo where the BNJetTag research tree is, since that is where the
pipeline code comes from:

```
cd .. && ./setup.sh                       # or: ./setup.sh /path/to/the/tree
```

That makes a gitignored `research` symlink. `export BNJETTAG_REPO=/path/to/tree` works too.

## A session

```
./lab.sh up          # launch the GPU Job, watch it reach Running
./lab.sh sync        # push code/hgq2 from the research tree, seed the notebooks
./lab.sh forward     # hold this terminal open: localhost:8888 -> the pod
./lab.sh url         # in a second terminal: prints the URL including the token
```

Open that URL, and start with `notebooks/00_env_check.ipynb`.

Five notebooks are seeded: `00_env_check`, `01_smoke_train`,
`02_binary_transformer_workbench` (stage-by-stage debugging plus resource profiling) and
`03_einsum_vs_matmul` (a structural check of the attention einsums against `tf.matmul` —
no data, no GPU, so it is the one worth running on the laptop instead). The fifth,
`04_conference_figures_pre_ebops`, rebuilds the fixed-precision Round-14 conference visual
bundle from the authoritative research arrays and reports. Run it locally, where the linked
research tree is present; the pod normally receives pipeline code but not the result stores.

When you are done:

```
./lab.sh pull        # copy notebooks off the PVC back into this folder
./lab.sh down        # delete the Job and give the GPU back
```

`down` deletes only the Job. The venv, the notebooks and everything under
`/data/lab/outputs` stay on the `kai-data` PVC, so the next `up` is a fast start.

Other commands: `status` (which node, which GPU), `logs [-f]`, `shell` (a bash prompt
inside the pod). Every command prints the `kubectl` it is about to run.

---

## What the pod looks like from inside

The `kai-data` PVC (100 Gi, RWX, ~16 Gi used) is mounted at `/data`, which is also the
path the round-14 configs already name — so the configs work unmodified.

```
/data/hls4ml_lhc_jet/train/train/   62 .h5 files, the training split, already extracted
/data/hls4ml_lhc_jet/val/val/       the held-out split used for ROC
/data/lab/venv/                     the Python environment (built once, reused)
/data/lab/repo/bnjettag/code/hgq2/  what `lab.sh sync` pushes; on PYTHONPATH
/data/lab/notebooks/                JupyterLab opens here
/data/lab/outputs/                  BNHGQ2_OUT_ROOT — checkpoints, logs
/data/lab/store/                    BNHGQ2_STORE — per-stage JSON
```

Kernels inherit `KERAS_BACKEND`, `BNHGQ2_TRAIN_DATA`, `BNHGQ2_OUT_ROOT`, `BNHGQ2_STORE`
and `PYTHONPATH`, so a notebook can `import bnhgq2` and call `train(...)` with no path
juggling.

The package pins are copied verbatim from the round-14 training pods
(`tensorflow[and-cuda]==2.21.0`, `keras==3.15.0`, `hgq2==0.1.9`, …). Keep them in step
with `kai-bn14-*.yaml`: an interactive environment that has drifted from the batch
environment is worse than no interactive environment, because it lies.

---

## Small sample

`bnhgq2.train.train` already takes `smoke=True`, which caps a run to **3 epochs over 2
`.h5` files** with no warmup. That is the small-sample switch — use it rather than
inventing a separate reduced path, because it exercises the same code the real jobs run.
`load_train_data(..., max_files=N)` is the finer knob when you only want data.

---

## Checking the cluster, and checking a job before you launch it

`nrp_doctor.py` lives here because it needs nothing but `kubectl`:

```
python3 nrp-lab/nrp_doctor.py status            # quota, our jobs, why our pods are Pending
python3 nrp-lab/nrp_doctor.py lint <job>.yaml   # check a manifest BEFORE kubectl apply
python3 nrp-lab/nrp_doctor.py mulder            # ssh, disks, Vitis, running synthesis
python3 nrp-lab/nrp_doctor.py all               # both machines, one call
```

In a Claude session, `/ops` runs `all` through the `cluster-ops` agent, which also
diagnoses anything stuck and records new incidents in
`.claude/memory/cluster-inventory.md`.

`status` answers "why is nothing running" in one call instead of a dozen — it separates the
two cases that look identical from the outside: genuine cluster saturation, versus our own
required GPU list being too narrow to schedule anywhere.

`lint` is the pre-launch gate. It catches the mistakes that have actually cost runs: a GPU
product pinned in affinity that our resource request can never reach, a `parallelism` far
below `completions`, and failure limits tight enough that a couple of bad indexes take down
a whole campaign. It exits non-zero on a fatal error, so it can gate a launch script. It
reads the cluster live rather than hardcoding node facts, so it does not go stale.

The rules it enforces are written once in
`docs/infrastructure/nrp-nautilus-setup.md` -> "Scheduling, GPU pools and job shape". If the
tool and that section disagree, the section is right and the tool is a bug.

## Guardrails

**No W&B.** The pod deliberately does not mount the `kai-wandb` secret, so
`wandb_util.wandb_enabled()` returns `False` and scratch runs cannot appear in
`BNJetTagAug` beside the round-14 record. `WANDB_MODE=offline` is set as a second
layer. If you ever do want tracking from here, add the secret *and* set
`WANDB_PROJECT=bnjettag-lab` — never the real project.

**Nothing here is a result.** Numbers from this pod are for checking that code runs.
Anything that goes into `RESEARCH.md` or `docs/reports/` still comes from a cluster job
and is recomputed from the `.npz` arrays through the `verify-roc` skill.

---

## Choices, and why

**A `Job` with a 6-hour deadline, not a `Deployment` or a bare pod.** Nautilus reaps
idle GPU pods, and the project's convention is batch Jobs
(`.claude/skills/nrp-training-run/SKILL.md`). Making the 6 hours explicit means a
forgotten session returns its GPU on its own. Being killed costs one `lab.sh up`,
because nothing lives in the pod.

**The venv lives on the PVC.** The cold build was measured at **41 minutes** on 2026-09-08
(CephFS write throughput, not download speed); a warm start reaches JupyterLab in about two
and a half minutes, nearly all of it importing TensorFlow over CephFS. Reinstalling on every
start would make the environment too annoying to use. The cost is that imports
come over CephFS and the first `import tensorflow` in a fresh kernel is slow. If the
venv is ever corrupt, `./lab.sh shell` then `rm -rf /data/lab/venv` and restart — it
rebuilds. The fallback design, if CephFS import latency turns out to be intolerable, is
to install into the pod's `emptyDir` each start with the pip cache on the PVC.

**Cheap GPUs only.** The affinity block asks for the mid-tier (A10, L4, 2080 Ti, A40,
A5000, 3090, V100) and prefers it strongly. A `d_model=32` model does not need a
flagship, and a notebook should not sit on one while it idles.

**Code is pushed, not cloned, and not vendored here.** `lab.sh sync` tars
`bnjettag/code/hgq2` out of the *research tree* onto the pod. That tree stays the single
source of truth; this repo holds the environment, and the PVC copy is disposable. Re-run
`sync` after editing code — the notebook will not see the change otherwise, and you will
need to restart the kernel.

**Notebooks are seeded, never clobbered.** `sync` copies a starter notebook only if it
is not already on the PVC. `pull` brings your edited versions back here so they can be
committed. `build_notebooks.py` regenerates the starters from plain Python.
