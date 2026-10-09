---
title: BNJetTag Lab
status: current
date: 2026-10-08
---

# BNJetTag Lab

The working environment for the BNJetTag project — a 1-bit BitNet `{−1,+1}`-weight
transformer jet tagger for the CMS Level-1 trigger, taken through hls4ml to FPGA.

**`SYSTEM.md` says how research runs here.** `INDEX.md` is one table of every study, document
and code tree (`python3 tools/index.py build`). What lives here:

- **`campaigns/`** — one directory per study (`<date>-<slug>/` with `STUDY.md` → `PREFLIGHT.md` → `RUN.md` → `VERIFY.md` → `REPORT.md`).
- **`local/`** — the notebooks on your own machine, the Jupyter kernel setup, and dated execution and audit scratch directories.
- **`nrp-lab/`** — a JupyterLab kernel on an NRP Nautilus GPU, and `nrp_doctor.py`, the
  manifest linter a hook runs before any `kubectl apply`.
- **`.claude/`** — thirteen agents (six stage owners, five on the review panel, plot-validator and fixer), the skills, the commands, the hooks, the agent memory.
- **`docs/`** — infrastructure docs, the style kit (`style/`), the schematics (`figures/`).
- **`tools/`** — the checks: `plot_check.py`, `prose_lint.py`, `claims.py`, `index.py`, `brief.py`.

The canonical lab is `~/lab/bnjettag` (`AGENTS.md`). The pipeline code is in `bnjettag/code/hgq2`
(research line) and `publication/code/hgq2`; the merge destination is `publication/code/hgq2`
(`campaigns/2026-09-26-code-line-merge/STUDY_v3.md` [D1]), and execution status is recorded in that campaign.

---

## Start — locally

```
./setup.sh                    # link the research tree (default ~/Downloads/bnjettag-training-results)
./local/setup-local.sh        # register the "BNJetTag (local)" Jupyter kernel
```

Open `nrp-lab/notebooks/00_env_check.ipynb` and pick that kernel — or go straight to
`02_binary_transformer_workbench.ipynb`, which lets you inspect the binary transformer
stage by stage, test gradients, and profile compute, memory, and latency using the real
`bnhgq2` functions. That is the whole setup:
the notebooks read their paths from the environment, and the kernelspec supplies them.
`local/README.md` covers the data splits and the W&B guardrail, which behaves differently
here than in the pod and is worth reading once.

## Start — on the cluster

Only when you need the cluster's exact environment; debugging does not.

```
cd nrp-lab
./lab.sh up                   # launch the GPU pod on Nautilus
./lab.sh logs -f              # first start builds the venv on the PVC: 41 min, measured
./lab.sh sync                 # push code/hgq2 from the research tree, seed the notebooks
./lab.sh forward              # hold open: localhost:8888 -> the pod
./lab.sh url                  # second terminal: the URL, with its token
```

Then open `00_env_check.ipynb`. When you're done, `./lab.sh pull` brings your notebooks back
here and `./lab.sh down` returns the GPU.

`nrp-lab/README.md` has the full session guide and the reasoning behind each design choice.

## Layout

```
setup.sh                  links ./research at the BNJetTag research tree
CLAUDE.md                 the working agreement this repo operates under
local/
  setup-local.sh          registers a Jupyter kernel carrying the BNHGQ2_* environment
  README.md               the local path, and what is deliberately still not local
nrp-lab/
  kai-lab.yaml            the GPU Job: JupyterLab, kai-data PVC, cheap-GPU affinity
  lab.sh                  up / status / logs / sync / url / forward / shell / pull / down
  build_notebooks.py      regenerates the starter notebooks from plain Python
  notebooks/              environment, training, model-workbench, einsum, and conference-figure notebooks
docs/infrastructure/      NRP access, W&B layout, mulder, the manual round runbook
.claude/
  agents/                 13 agents — the team
  skills/                 3 playbooks — the recurring workflows
  commands/               1 slash command (`/review`)
  memory/                 live logs (fresh); the history to 2026-09-08 is frozen
```

## The two trees

`lab.sh sync` pushes `code/hgq2` **from the research tree** onto the pod. The pipeline code is
not kept in `nrp-lab/`; it is in `bnjettag/code/hgq2` and `publication/code/hgq2`. Point at a tree with `./setup.sh /path/to/tree` (which
makes a gitignored `research` symlink) or by exporting `BNJETTAG_REPO`.

This means the lab repo is not self-contained by design. The alternative — vendoring a second
copy of the pipeline — buys standalone cloning at the price of two copies that drift silently
apart, which is the more expensive failure.

## What the lab is not

It is a scratch environment. Small samples, smoke runs, three-epoch checks, "what shape is
this array". **No number computed in the pod is quotable.** Anything headed for `RESEARCH.md`
or a report comes from a batch Job on the cluster and is recomputed from the `.npz` arrays
through the `verify-roc` skill.

The pod deliberately mounts no W&B secret, so scratch runs cannot appear in the `BNJetTagAug`
project beside the round-14 record. **On the laptop that protection is configuration rather
than physics** — a credential does exist in `~/.netrc` — so the local kernel pins
`WANDB_MODE=offline` and `WANDB_PROJECT=bnjettag-lab`. See `local/README.md`.
