---
title: Running a round by hand — the full chain, start to finish
status: current
date: 2026-09-17
---

# Running a round by hand — the full chain, start to finish

Written 2026-08-13 for a from-scratch walkthrough: how a BNJetTag training round
actually gets run, typed one command at a time, with nothing automated away.

Round 14 is the worked example. It is the newest round and the right shape for a
fresh start: PVC-free, its own W&B project, 60 training jobs + 4 eval jobs, all
generated. To run *your own* round, copy R14 and change the round label.

Deeper background lives in `nrp-nautilus-setup.md` (cluster access),
`wandb-layout.md` (what W&B is and isn't for), and
`.claude/skills/nrp-training-run/SKILL.md` (the condensed playbook).

---

## The shape of the thing

Nothing about this project trains locally. The chain is:

```
config JSON  ──►  job YAML  ──►  ConfigMap  ──►  k8s Job on Nautilus  ──►  W&B artifact
 (generated)     (generated)      (the code)       (a GPU pod)            (the checkpoint)
                                                                              │
                                        .npz ◄── ROC eval job ◄───────────────┘
                                          │
                                    recompute AUC locally  ◄── THE NUMBER OF RECORD
```

Four facts that explain every design choice below:

1. **Pods are disposable and have no persistent disk.** Round 14 pods are
   `emptyDir`-only. When the pod dies, everything in it is gone. The checkpoint
   survives *only* because training uploads it to W&B as a versioned artifact,
   under a durability gate that treats upload failure as fatal.
2. **Code reaches the pod as a Kubernetes ConfigMap**, not a git clone and not a
   PVC. `code/hgq2/` is tarred, the tarball becomes a ConfigMap, the pod untars
   it to `/work/code`. Hard limit: 1 MB.
3. **The dataset is downloaded fresh from Zenodo inside every pod** (~2.7 GB
   train, ~1.1 GB val). No shared copy. This is why jobs request 16 Gi of
   ephemeral storage.
4. **W&B is provenance, never the number of record.** Every AUC that appears in
   any document is recomputed locally from the `.npz` arrays. The W&B metric is
   there so drift is *detectable*, not so it can be quoted.

---

## Phase 0 — local sanity, no cluster involved

Goal: prove the code builds and the numbers stack is intact, before spending
cluster time.

The venv already exists at `.venv-hgq2` (Python 3.12) with the pinned versions
that mirror the cluster pods exactly:

```
tensorflow[and-cuda]==2.21.0  keras==3.15.0  hgq2==0.1.9  quantizers==1.2.2
scikit-learn==1.9.0  h5py==3.14.0  wandb==0.28.0  hls4ml==1.3.0  numpy==2.5.0
```

Do not upgrade any of them. The TF 2.21 wheel has a broken RPATH for the
`nvidia-*-cu12` libs; the pods work around it with an explicit `LD_LIBRARY_PATH`
over the wheel lib dirs.

Checks:

```bash
cd ~/Downloads/bnjettag-training-results
source .venv-hgq2/bin/activate
cd bnjettag/code/hgq2
python -c "
from bnhgq2.config import load_config
from bnhgq2.qat import build_qat_model
cfg = load_config('configs/r14-l1x3-n16-w1a8.json')
m = build_qat_model(cfg)
print(m.count_params())
"
```

Note: the config's `"train": {"data": "/data/hls4ml_lhc_jet/train/train"}` is a
dead path left from the PVC era. The pod overrides it with the
`BNHGQ2_TRAIN_DATA` environment variable pointing at the freshly-downloaded
Zenodo extract. Don't chase it.

---

## Phase 1 — cluster access

```bash
kubectl config use-context nautilus
kubectl get pods -n cms-ml
```

`cms-ml` is the **whole Duarte group's** namespace, so most pods you see belong
to other people. Prefix everything of yours with `kai-`. Never delete anyone
else's pod.

On `401 Unauthorized`: `kubectl oidc-login clean`, then retry any kubectl
command — it re-opens the browser login.

---

## Phase 2 — the W&B project and the cluster secret

**A W&B project is created automatically by the first `wandb.init()` that names
it.** There is nothing to click in the web UI. Round 14 uses `BNJetTagAug`
(new input representation ⇒ new project); earlier rounds used `bnjettag-final`
and `bnjettag-bitnet`. Entity is always `kayamaguchi-uc-san-diego`.

The project name must agree in **three** places or the chain breaks silently:

| Where | Field |
|---|---|
| `code/hgq2/configs/gen_r14.py` | `train.wandb_project` |
| `code/jobs/training/variants/gen_r14_jobs.py` | `WANDB_PROJECT` in the YAML template |
| `code/jobs/training/variants/gen_r14_roc_jobs.py` | `WANDB_PROJECT` in the eval YAML |

The eval job fetches checkpoints **by artifact name scoped to the project**
(`model-r14-l1x3-n<N>-<variant>-s<seed>`). Rename training but not eval and the
eval finds nothing.

The pods read the key from a Kubernetes secret, not from a file. Check whether
it already exists before creating anything:

```bash
kubectl get secret kai-wandb -n cms-ml
```

It almost certainly does, from earlier rounds. If it must be recreated, note
that `wandb-api-key.txt` is 87 bytes — a 40-char key plus a newline. A baked-in
trailing newline silently poisons every job, and `wandb.init()` is not wrapped in
try/except, so every pod dies at startup. Strip it. Never `cat` or `echo` the
key.

---

## Phase 3 — ship the code as a ConfigMap

```bash
cd ~/Downloads/bnjettag-training-results/bnjettag/code/jobs/training/variants
./make_code_configmap_r14.sh
```

This script *is* the local preflight for round 14. Before it publishes anything
it refuses to proceed unless:

- `bnhgq2/data.py` defines `feature_indices` (the L1 3-feature subset — the exact
  confound round 14 exists to remove),
- `bnhgq2/train.py` uses the `wandb_util` layout,
- exactly 20 `configs/r14-*.json` exist,
- the tarball is under the 1 MB ConfigMap limit.

It prints the tarball md5. **Write it down** — every pod echoes the same md5 back
as `[code] configmap tar md5: <...>`, which is how you prove a pod ran the code
you think it ran.

One ConfigMap per round, and old ones stay frozen so a re-run of an old round is
reproducible. The apply is `--server-side` because the r14 tree overflows
client-side apply's 256 KB annotation cap.

---

## Phase 4 — one job, read the log end to end

Do **not** start with `launch_r14.sh stage1`. That is 36 jobs on a shared
namespace. Start with one:

```bash
kubectl apply -f kai-bn14-l1x3-n16-w1a8-s1.yaml -n cms-ml
kubectl get jobs,pods -n cms-ml | grep kai-bn14
kubectl logs -f <pod-name> -n cms-ml
```

Read the log for these milestones, in order:

| Log line | Means |
|---|---|
| `[code] configmap tar md5: ...` | matches your Phase 3 md5 ⇒ right code |
| `[gate] ...` | the stale-ConfigMap check passed |
| `[gpu] TF sees [...]` | TensorFlow found the GPU |
| `[data] tarball bytes: 2725115104` | the Zenodo download is complete, not truncated |
| epoch lines | actually training |

Common states, and which are actually fine:

- **Pod stuck `Pending`** — normal for minutes, a config bug after hours. Which one it is
  comes from the `PodScheduled` condition, not from `describe` (which truncates). See
  **Scheduling, GPU pools and job shape** in `docs/infrastructure/nrp-nautilus-setup.md`
  for the diagnostic and for why our jobs cannot land on A100 or A40 at all.
- **`ContainerCreating`** — still pulling the `python:3.12` image. Wait for
  `Running` before `exec`.
- **`UnexpectedAdmissionError`** — a node GPU device-plugin race with zero side
  effects. This is exactly why the Job carries a retry allowance (`backoffLimit: 2` on a
  single Job; `backoffLimitPerIndex` on the Indexed campaign form).

Round 14 is 101 epochs at batch 256 with `activeDeadlineSeconds: 21600` (6 h).
A single 19k-parameter model is data-bound, not FLOP-bound — the 2 CPU / 8 Gi
request is deliberate right-sizing, not stinginess.

---

## Phase 5 — scale to the full round

```bash
./launch_r14.sh stage1     # 36 jobs: N ∈ {8,16,32,64} × {fp32, w8a8, w1a8} × 3 seeds
./launch_r14.sh stage2     # 24 jobs: N ∈ {8,16,32,64} × {w1a6, w1a4} × 3 seeds
./launch_r14.sh delete     # tear the round down
```

Stage 1 is the baselines plus the thesis arm; stage 2 is the activation ladder.
Three seeds per arm because no gap between two arms means anything without a
seed spread on it.

The launcher stages in waves of 6 and polls every 120 s, so **it needs the laptop
awake for hours**. Run it under `tmux`, or apply the YAMLs all at once and let
the cluster scheduler self-limit. Either is fine — just record which you used.

Never hand-edit a generated YAML; it will be overwritten. Edit
`gen_r14_jobs.py` and regenerate with `python gen_r14_jobs.py`.

---

## Phase 6 — evaluation (ROC)

Training reports a *validation* AUC. That is a training monitor and is **not**
the number that gets published. The published number is the ROC-test AUC, from
the held-out val split, n = 260,000. Never conflate the two.

Eval is a separate set of CPU-only jobs, one per constituent count — attention
cost goes as N², and at N=64 a serial local eval of 15 models × 260k jets is the
bottleneck, so it farms out to the cluster:

```bash
kubectl apply -f kai-bn14-roc-n8.yaml -n cms-ml
```

**KNOWN GAP:** these jobs mount a ConfigMap named `kai-bn14-roc-code`, and no
script in this repo builds it. It needs a *newer* tree than the frozen
`kai-bn14-code` — specifically `roc_final.py` with `--wandb-log`, the per-model
`input_std` auto-apply, and the `--n-part`/`--features` flags. Build it by
copying `make_code_configmap_r14.sh`, changing the ConfigMap name, and swapping
the gate greps for the three strings the eval pod itself checks (see
`kai-bn14-roc-n8.yaml` lines 38–40). Write that script; don't do it by hand
twice.

Each eval job fetches checkpoints artifact-first from W&B, re-downloads the val
split from Zenodo, asserts n = 260,000, and writes 15 `.npz` files — each holding
`y` (one-hot, N×5) and `score` (softmax, N×5).

---

## Phase 7 — bring it home and verify

Fetch the `.npz` bundle from the `evaluation-r14-l1x3-n<N>` W&B artifact into
`bnjettag/roc-results/r14/n<N>/`, then run the verification gate.

This is the part that is not optional. **No AUC is real until it has been
recomputed locally from the `.npz`.** Follow
`.claude/skills/verify-roc/SKILL.md`: load `y` and `score`, then

```python
roc_auc_score(y, score, multi_class="ovr", average="macro")
```

and check it against whatever the report claims. Same for resources — no LUT or
DSP number is real until parsed from the raw csynth XML.

Input discipline: everything here is the public HLS4ML LHC Jet task (5-class,
macro-OvR, n = 260,000). Never compare these AUCs to anything under
`_attic/`.

---

## Phase 8 — write it down

Append to `.claude/memory/experiment-log.md`, newest on top: the goal, the job
files, the ConfigMap md5, where the artifacts landed, and every deviation from
this document. A run that isn't logged didn't happen.

---

## What comes after

Training and ROC are the first half. The second half is synthesis: checkpoint →
hls4ml → Vitis HLS C-synthesis on `mulder` → the LUT/DSP/latency tables. That
chain has its own playbook in `.claude/skills/hls-mulder/SKILL.md` and does not
touch Kubernetes at all.
