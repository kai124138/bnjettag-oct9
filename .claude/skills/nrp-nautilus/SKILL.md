---
name: nrp-nautilus
description: Run and monitor GPU jobs on the NRP Nautilus Kubernetes cluster (namespace cms-ml) — kubelogin/OIDC access, job YAML patterns, ConfigMap code shipping, launch, monitor, and retrieve artifacts via W&B. Use for anything mentioning Nautilus, NRP, kubectl, the cms-ml namespace, a training job YAML, "launch the run", GPU quota, or bringing results back from the cluster.
---

# NRP Nautilus — cluster access and the job lifecycle

Machine- and account-level notes for Kai's NRP Nautilus access. These hold in any folder.

> **A project-local `nrp-training-run` skill supersedes this one.** If the repo you are in
> has `.claude/skills/nrp-training-run/`, follow that — it carries the repo's actual paths,
> generators, and result stores. This file is the fallback for every other folder.

**Namespace:** `cms-ml` — the Duarte group's *shared* namespace at UC San Diego.
Training never runs locally; it runs here.

## Access (already set up on this machine)

- `~/.kube/config` from `https://nrp.ai/config`, context **`nautilus`**, server
  `https://67.58.53.148:443`.
- Auth is the **kubelogin / OIDC** flow via the `kubectl oidc-login` exec plugin, installed
  as `/opt/homebrew/bin/kubectl-oidc_login`. The bare name `kubelogin` is *not* on PATH and
  does not need to be. Note: plain `brew install kubelogin` installs a **different (Azure)**
  tool — the right one is `kubectl krew install oidc-login` or `brew install
  int128/kubelogin/kubelogin`.
- Tokens expire ~30 min and auto-refresh. `kubectl oidc-login clean` forces a refresh —
  needed after being added to a new namespace.
- First command of a session may open a browser for CILogon → pick **UC San Diego**.
- Namespace membership is granted by an admin (Russell/Javier) at https://nrp.ai/namespaces;
  students cannot self-add. `kubectl get pods -n cms-ml` returning `No resources found`
  means you are in.

## Everyday commands

```
kubectl get jobs,pods -n cms-ml                  what's running
kubectl describe pod <pod> -n cms-ml             events / why it's pending
kubectl logs -f <pod> -n cms-ml                  follow a run
kubectl exec -it <pod> -n cms-ml -- /bin/bash    shell in
kubectl apply -f <job>.yaml -n cms-ml            launch
kubectl delete pod <pod> -n cms-ml               clean up
```

## Mental model — how work reaches the cluster

- **Pods are disposable and the pipeline is PVC-free.** Code ships as a **ConfigMap**, input
  data is fetched from its public source (e.g. Zenodo) at pod start, and every artifact goes
  to **W&B**. Anything installed inside a pod dies with the pod.
- Use batch **Jobs**, not interactive pods — idle-GPU pods get reaped. A one-off run uses
  `backoffLimit: 0` with `activeDeadlineSeconds` (172800 for long training). A multi-run
  campaign uses an **Indexed** Job — and there, `parallelism` is a self-imposed ceiling on
  concurrency, so check it first if throughput feels low. Set `backoffLimitPerIndex` and
  `maxFailedIndexes` deliberately: too-tight values let a few bad indexes kill the whole
  campaign, including runs that never started. Add a `podFailurePolicy` with
  `action: Ignore` on `onPodConditions: [{type: DisruptionTarget}]` so a preemption does
  not spend a retry — Nautilus preempts routinely.
- One experiment = one Job YAML. Experiments should differ by a **config file**, not by
  forked code.
- **W&B:** entity `kayamaguchi-uc-san-diego`. Export `WANDB_ENTITY`, `WANDB_PROJECT`,
  `WANDB_GROUP`, `WANDB_TAGS`, `WANDB_RUN_NAME` from the job YAML. Checkpoint durability
  comes from a versioned artifact committed in-pod, fatal on failure.

## Launch discipline

1. Local checks first — YAML parses, embedded Python compiles (`python -m py_compile`),
   every referenced config loads.
2. **Rebuild and verify the ConfigMap before launching.** A stale ConfigMap silently reruns
   the previous code; a `create` that no-ops is the classic failure.
3. Preflight in a cheap CPU pod before spending GPU time — validate data access and config
   construction, and require an explicit pass string in the log.
4. Launch staged (≤3 concurrent, polite, needs the laptop awake) or all-at-once (survives
   laptop close; the scheduler self-limits). Record which you used.

## Gotchas that have actually bitten

- **Stale W&B secret kills every job.** `wandb.init()` is not wrapped in try/except. After a
  key rotation, update the `kai-wandb` secret in `cms-ml` and verify it (sha256) *before*
  launching. Never print or commit the key file.
- **GPU resource names are not uniform, and this is the classic bug.** A pod asking for
  `nvidia.com/gpu: 1` can never schedule on an A100 or A40 — those classes use
  `nvidia.com/a100` / `nvidia.com/a40` and expose 0 generic GPU. Adding the product to an
  affinity list does nothing; the *resource request* must change too.
- **`preferred` affinity is soft and silently ignored; `required` is hard** and is the usual
  reason a job sits Pending for hours. `describe` truncates the scheduler's reason — read
  `{.status.conditions[?(@.type=="PodScheduled")].message}` instead.
- **`parallelism` on an Indexed Job is a self-imposed ceiling.** If throughput feels low,
  check it before blaming the cluster.
- **Rules, quota numbers and the Indexed-Job failure-limit pattern live in one place:**
  `docs/infrastructure/nrp-nautilus-setup.md` -> "Scheduling, GPU pools and job shape" in
  the bnjettag-lab repo. Read it there; do not restate it here, or the two copies drift.
  Fastest path to all of the above: `nrp-lab/nrp_doctor.py status` / `lint <job.yaml>` /
  `all` (adds mulder). Incidents and known-bad nodes: `.claude/memory/cluster-inventory.md`.
- `cms-ml` is shared — label your objects with `user=kai`, clean up finished pods, don't
  camp on GPUs.
- Nautilus has **no Xilinx backend**. FPGA synthesis goes to mulder; see the
  `vitis-mulder` skill.
