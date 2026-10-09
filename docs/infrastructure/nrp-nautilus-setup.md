---
title: NRP / Nautilus — Setup & Workflow Notes
status: current
date: 2026-09-20
---

# NRP / Nautilus — Setup & Workflow Notes

## Canonical WSL access, checked October 1, 2026

The Mac-to-WSL lab migration excluded `.kube` configuration and credentials. Older
notes saying access was already configured describe the Mac environment, not proof
of authentication on the PC. The canonical WSL installation now has `kubectl` and
`kubectl-oidc_login` in `~/.local/bin` and a fresh public NRP template at
`~/.kube/config`, with context `nautilus` and namespace `cms-ml`.

Authentication remains separate from installing the config. The current NRP template
uses Authentik, which connects to institutional sign-in through CILogon. For this
remote WSL session, the documented `--grant-type=device-code --skip-open-browser`
flow lets Kai complete UCSD verification in his own browser, including through
Parsec, without a callback listener or exporting Mac credentials. See the
[current NRP access instructions](https://nrp.ai/documentation/userdocs/start/getting-started/)
and `local/2026-10-01-execution/nrp-config-repair.json`. Successful authentication
and namespace access still require a live read-only check; a config file alone does
not establish either.

On October 1 at 05:13 UTC, institutional device authentication and a read of the
exact b5 Job in `cms-ml` succeeded. Evidence is in
`campaigns/2026-10-01-recovery/captures/cluster-20261001T0513Z/`. The client was
then matched to the observed server version, `v1.34.11`, using the official binary
and published checksum; the installation receipt is
`local/2026-10-01-execution/kubectl-server-match.json`.

For this remote WSL process, Windows subprocesses ran in background session 0;
calling `Start-Process` there did not establish a visible Parsec browser window.
A temporary on-demand task under the same signed-in Windows account opened the
fresh device URL in interactive session 1. Its browser title and foreground
activation were verified from that session, and the temporary task was removed.
Future login requests must use a fresh URL and verify the interactive desktop;
browser-launch success alone does not prove cluster authentication.

Mulder is a separate access path. It requires Kai's explicit permission and the
UCSD-verified connection he establishes through his MacBook. Use
`nrp_doctor.py status` for NRP-only checks; `all` also attempts Mulder and must not
be used without that authorization and connection. The earlier Homebrew commands
below remain the Mac setup reference.

My working reference for connecting to and using the NRP Nautilus cluster. This uses the current **kubelogin** login flow and replaces the older "download a config with a token baked in" method (the one that kept throwing `401 Unauthorized` and needing a re-download).

**Namespace:** `cms-ml` — the Duarte group's *shared* namespace (Russell added me).

---

## One-time setup

**1. Install kubectl**
```
brew install kubectl
```

**2. Install the kubelogin plugin** — the binary must end up named `kubectl-oidc_login` on your PATH. Pick one:
- krew (recommended): `kubectl krew install oidc-login`
- Homebrew tap: `brew install int128/kubelogin/kubelogin`
  - ⚠️ NOT plain `brew install kubelogin` — that's a *different* (Azure) tool with the same name.
- Manual: download the release from int128/kubelogin, rename to `kubectl-oidc_login`, move into your PATH.

Verify: `kubectl oidc-login --version`

**3. Download the Nautilus config** to `~/.kube/config`:
```
mkdir -p ~/.kube
curl -o ~/.kube/config -fSL "https://nrp.ai/config"
```
This config already wires up oidc-login, so there's nothing else to configure.

**4. Set the context and log in** — the first kubectl command opens a browser for CILogon:
```
kubectl config use-context nautilus
kubectl get nodes
```
Pick **UC San Diego**, log in with UCSD creds. Your account is created on first login.

**5. Namespace access** — students can't self-add. Russell (or Javier) adds you to `cms-ml` at https://nrp.ai/namespaces. Verify:
```
kubectl get pods -n cms-ml
```
`No resources found` = you're in (just no pods of your own yet).

**6. (Optional) Make cms-ml the default** so you stop typing `-n`:
```
kubectl config set-context --current --namespace=cms-ml
```

**Why kubelogin is better:** the access token auto-refreshes (expires ~30 min, renews automatically), so no more manually re-downloading the config when it dies.

---

## Everyday commands

```
kubectl get pods -n cms-ml                       list pods
kubectl create -f mypod.yaml -n cms-ml           create a pod from yaml
kubectl describe pod <pod> -n cms-ml             details / events (debugging)
kubectl logs <pod> -n cms-ml                     logs  (add -f to follow live)
kubectl exec -it <pod> -n cms-ml -- /bin/bash    shell into a running pod
kubectl delete pod <pod> -n cms-ml               delete a pod
kubectl oidc-login clean                         force token refresh (e.g. after joining a new namespace)
```
Replace `<pod>` with the real pod name — no angle brackets.

---

## Minimal test pod

`kai-test-pod.yaml`:
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: kai-test-pod
spec:
  restartPolicy: Never
  containers:
  - name: kai-test
    image: ubuntu:22.04
    resources:
      limits:
        memory: 200Mi
        cpu: 200m
      requests:
        memory: 200Mi
        cpu: 200m
    command: ["sh", "-c", "echo connected && sleep 3600"]
```

Run **one command at a time**:
```
kubectl create -f kai-test-pod.yaml -n cms-ml
kubectl get pods -n cms-ml
```
Wait until `kai-test-pod` shows `Running`, then shell in:
```
kubectl exec -it kai-test-pod -n cms-ml -- /bin/bash
```
You land at `root@kai-test-pod:/#`. Type `exit`, then clean up:
```
kubectl delete pod kai-test-pod -n cms-ml
```

---

## Gotchas I actually hit (and fixes)

- **`zsh: parse error near '\n'`** — left the literal placeholder `<namespace>` in the command. `<` is a redirect operator in zsh. Fix: replace `<namespace>` with the real name (`cms-ml`), no angle brackets.

- **`Error from server (NotFound): pods "wait" not found`** (also `"for"`, `"to"`, etc.) — zsh doesn't treat `#` as a comment by default, so pasted inline `# comments` got passed to kubectl as pod names. Fixes: don't paste comments, **or** add `setopt interactive_comments` to `~/.zshrc` so `#` is ignored even in pasted blocks.

- **`unable to upgrade connection: container not found`** on exec — ran `exec` before the pod finished starting (`ContainerCreating` = still pulling the image). Fix: wait for `Running` before exec.

- **Multi-line pastes** — run kubectl commands one at a time (or use the `setopt` fix). Pasting a whole block can chain failures.

- **`Forbidden`** — authenticated but not a member of that namespace. Get added at nrp.ai/namespaces.

- **`401 Unauthorized` / token errors** — `kubectl oidc-login clean`, then re-run any kubectl command.

---

## Scheduling, GPU pools and job shape

**This section is the single source of truth for how jobs get scheduled.** The runbook and
the `nrp-training-run` skill point here; don't restate these rules in either, or they drift.
Node/quota figures below were read live on **2026-09-17**.

Everything here is also enforced mechanically — prefer the tool over doing it by hand:

```
python3 nrp-lab/nrp_doctor.py status            # quota, our jobs, why our pods are Pending
python3 nrp-lab/nrp_doctor.py lint <job.yaml>   # check a manifest BEFORE kubectl apply
python3 nrp-lab/nrp_doctor.py all               # + mulder health, one call
```

Known-bad nodes and failure signatures (observations, dated) live in
`.claude/memory/cluster-inventory.md`, kept by the `cluster-ops` agent; `lint` warns
when a manifest fails to exclude a known-bad node.

`lint` exits non-zero on an error, so it can gate a launch. If the tool and this section
ever disagree, this section is right and the tool is a bug.

### GPU resource names are not uniform

Nautilus does not expose every GPU as the same Kubernetes resource:

| GPU class | resource to request | namespace quota (`cms-ml`) |
| --- | --- | --- |
| 3090, 4090, L40, L40S, A10, L4, A5000, A4000, V100, 2080-Ti | `nvidia.com/gpu` | none — effectively unlimited |
| A100 (all variants) | `nvidia.com/a100` | 24 |
| A40 | `nvidia.com/a40` | none |
| H100 / H200 / GH200 | `nvidia.com/h100` etc. | **0 — banned** |

**A pod requesting `nvidia.com/gpu: 1` can never land on an A100.** All 40 A100 nodes in the
cluster advertise `nvidia.com/gpu` as `0` or absent; the GPUs are behind `nvidia.com/a100`.
Adding `NVIDIA-A100-*` to an affinity list does nothing on its own — the *resource request*
has to change too. Same for A40 (`nvidia.com/a40`), which is why other groups' A40-pinned
pods sit Pending for days without affecting us.

Check before assuming:
```
kubectl get nodes -o custom-columns='PRODUCT:.metadata.labels.nvidia\.com/gpu\.product,GPU:.status.allocatable.nvidia\.com/gpu,A100:.status.allocatable.nvidia\.com/a100'
```

### preferred vs required affinity

- `preferredDuringSchedulingIgnoredDuringExecution` is **soft**. If nothing matches it is
  silently ignored and you never hear about it. A preference for a GPU we hold no quota on
  (H100/H200) is simply dead weight.
- `requiredDuringSchedulingIgnoredDuringExecution` is **hard** and is the dominant
  scheduling constraint. A narrow required list is the most common reason our own jobs
  sit Pending.

### Pool policy

Round-7 Decision 3 stands: **right-size the ask and prefer the abundant mid-tier.** Our
models are ~19k parameters on a ~0.6 GB resident dataset — data-bound, not FLOP-bound. A
wide required list (Decision 3 used 20 products) with a mid-tier preference schedules
fastest. Leaving A100s to people who need them is also good cluster manners.

Narrowing the required list is allowed **only** for a controlled timing comparison, where
mixing GPU models would confound the measurement. A narrowed pool is a per-job exception,
never the new default, and it must get a `decisions.md` entry saying why and when it ends.
Cost of getting this wrong, measured: the Sept-12 ablation pinned to 4090/L40S/L40 only —
25 nodes, 20 Ready — and index4 sat Pending **34 hours** without ever scheduling.

### Concurrency is ours, not the cluster's

`parallelism` on an Indexed Job is the ceiling on how many of our runs execute at once, and
it is a number we choose. Namespace limits are `pods 200` and `a100 24`; generic-GPU runs
are not quota-capped at all. If throughput feels low, **check `parallelism` first** — the
cluster is rarely the binding constraint.

The pre-r14 pattern was one single-GPU Job YAML per variant, applied in bulk, letting the
scheduler place as many as it could. The current pattern is one Indexed Job with a
`parallelism` cap. Both are fine; only the second one can silently throttle you.

**Sizing it:** start from `min(completions, free nodes matching your required list)`. Back
off only if you'd be the clear majority of the namespace's running GPU pods — `cms-ml` is
shared with the rest of the group. Etiquette means not camping idle GPUs; it does not mean
serializing a campaign that the cluster has room for.

### Indexed Job failure limits

Current pattern for a multi-run campaign:

```yaml
completionMode: Indexed
completions: 12
parallelism: 10
backoffLimitPerIndex: 3      # retries for ONE index
maxFailedIndexes: 6          # how many indexes may fail before the JOB dies
podFailurePolicy:
  rules:
    - action: Ignore         # eviction is not our bug; don't spend a retry on it
      onPodConditions:
        - type: DisruptionTarget
```

`backoffLimitPerIndex` and `maxFailedIndexes` interact, and getting them wrong kills work
that was fine. Worked example: `kai-batch0917-screen-e100` ran 12 indexes with
`backoffLimitPerIndex: 1` and `maxFailedIndexes: 2`. Indexes 1-3 failed, tripping
`MaxFailedIndexesExceeded`, and **all 12 runs died** — including ones that had not started.
Without a `podFailurePolicy`, a Nautilus preemption also burns a retry, so two evictions can
end an index that never had a real error.

The older single-Job form (`backoffLimit: 0` or `2` plus `activeDeadlineSeconds`) is
**legacy** — still valid for a one-off run, but campaigns use the Indexed form above.
Note NRP batch Jobs have no universal 6 h limit; set `activeDeadlineSeconds` deliberately
or leave it off.

### Recovering a dead campaign (the Job is disposable; the PVC is the state)

When an Indexed Job dies — `MaxFailedIndexesExceeded`, deadline, a bad node — **the work
is not lost**, and you do not restart from epoch 0. On 2026-09-17 `kai-batch0917-screen-e100`
died at 0/12 complete; its relaunch resumed A00 from epoch 60 and A01 from 39.

How the training code makes that true (`bnhgq2/ablation.py`):

- Every epoch, the checkpoint is written to a temp path and `os.replace`d into place, then
  `latest.json` is atomically repointed. Two complete generations are kept. A partial
  write can never become `latest.json`.
- On start, it follows `latest.json` -> `checkpoints/<leaf>/state.json` and **refuses to
  resume unless** `state.config_sha256 == sha256(config)` and
  `state.code_sha256 == $BNHGQ2_CODE_SHA256` (`Resume config mismatch` /
  `Resume code mismatch`). Drift fails loudly; it never silently trains on the wrong
  history.

So the recovery recipe is: **new Job name, everything else identical.**

1. Same immutable ConfigMap (it carries `BNHGQ2_CODE_SHA256`; the code the pods run must
   be byte-identical or the guard refuses).
2. Same config JSONs, same `--root` on the PVC, same arm names -> same
   `runs/<arm>/` directories.
3. Fix only the *Job shape* (parallelism, retry limits, pool, excluded nodes). The Job
   template is immutable, so this is always a new object; give it a new name (`-r2`,
   `-r3`) and keep the old one as the record.
4. Before applying: confirm the old job has **no pods left** (`kubectl get pods
   -l app=<label>`), or two writers will race for the same `runs/<arm>/`.
5. `kubectl create --dry-run=server` the manifest — one derived from a live dump carries
   `controller-uid` / `job-name` template labels that the API rejects.
6. If you must kill a relaunch that went wrong, do it while `ready=0`; running pods lose
   at most the current epoch either way.

Confirm it worked from the pod log, not W&B: `[train] <arm> ... resume_epoch=60`.

### GPU utilization floor: pack small runs, one GPU per pod is not a given

For Chang and Delta production, also apply the dated
[GPU selection policy](gpu-selection-policy.md): benchmark fast schedulable products, choose
the earliest measured finish time, and tune each product's pack size. The 40% floor is a
sustained-utilization check, not a speed ranking. Existing A10 pilot manifests are history.

NRP requires a pod holding a GPU to average **above 40% GPU utilization**; the alert
looks back 3 hours (so pip-install startup counts against you), deletion by admins is a
recorded violation, and three violations flag the account. Alert text, 2026-09-20.

One BNJetTag arm cannot meet that alone. The models are ~19k parameters and
kernel-launch-bound: one Python core at 100%, the GPU at 27-39%, ~1 GB of GPU memory, and
epoch time that tracks the node's CPU rather than the GPU model. A faster GPU makes the
percentage *lower*.

So a campaign of small arms runs **several arms per GPU pod**: index `k` of the Indexed
Job starts its pack of arms as background processes, forwards SIGTERM to them, and exits
nonzero if any arm failed so the index retries and every arm resumes from `latest.json`.
This is Job shape only — same ConfigMap, code sha, configs and `runs/<arm>/` — so it goes
through the recovery recipe above. Size `cpu` at about 2 per arm and `memory` at about
6 Gi per arm; start at 3 arms per pod and measure with `nvidia-smi` in every pod. Put arms
with similar remaining epochs in the same pack: the last arm left in a pod is back under
the floor. Reference generator: `local/continuation-20260920/build_packed.py`.

"Switch to a CPU-only request" (the alert's other suggestion) is unmeasured for this
trainer; do not assume it fits a process timeout.

**Checked, not remembered (2026-09-26).** `nrp_doctor.py lint` rule `PACK` requires every
GPU Job to carry a `bnjettag.io/arms-per-pod: "<k>"` label (or annotation) and warns when
`cpu` is under about 2 per arm or `memory` under about 6 Gi per arm; `k = 1` needs a
`bnjettag.io/single-arm-justified: "<why>"` annotation. The PreToolUse hook in
`.claude/hooks/pre-kubectl-lint.py` runs lint before any `kubectl apply`, so a manifest
that forgets the floor is caught at launch, not by an alert three hours later.

### Diagnosing a Pending pod

`kubectl describe` truncates the scheduler message at ~1 KB, and empirically the
single-node reasons (`1 node(s) had untolerated taint ...`) come first, so the large
buckets that actually matter are what gets cut off. Read the pod condition instead — it is
not truncated:

```
kubectl -n cms-ml get pod <pod> \
  -o jsonpath='{.status.conditions[?(@.type=="PodScheduled")].message}' \
  | tr ',' '\n' | grep -v 'untolerated taint'
```

Read the dominant bucket:

- **`Insufficient nvidia.com/gpu` (or `/a100`, `/a40`) dominant** → the cluster is genuinely
  saturated for that class. Wait, or widen the pool.
- **`didn't match Pod's node affinity/selector` dominant** → *our* required list is the
  problem. Fix the manifest; waiting will not help.

Pending is normal for minutes. Pending for hours with affinity dominant is a config bug,
not friction — treat it as one.

---

## Shared namespace etiquette

`cms-ml` is the **whole Duarte group's** namespace, so most pods you see belong to other people (training sweeps, `*serverdep` volume web-servers, the `mpt-*` monitoring stack).

- **Prefix your resources** so they're obviously yours (others use `zh-`, `tn-`, `rino-`, `ajd-`… → I use `kai-`).
- **Only touch your own pods.** Never delete — and never *force*-delete — someone else's.
- **Containers are stateless.** Anything not on a persistent volume is gone when the pod restarts. Don't run never-ending `sleep` jobs (it can get you banned).

---

## Remote / headless machines (lxplus, Mulder)

No local browser → the auto-login won't open a window. Use the device-code flow:
```
--grant-type=device-code --skip-open-browser
```
It prints a URL to paste into your laptop's browser. Easiest is to do interactive work from your **laptop**, where the browser just opens.

---

## Next steps

1. **Persistent Volume (PVC)** — claim storage so code, data, and training outputs survive pod restarts.
2. **Get code + data onto the volume** — clone BNJetTagKai and stage the training data.
3. **GPU pod** mounted to the volume — request a GPU, pull the repo, run training.
4. **(Optional) Docker image** with my deps (qkeras / tensorflow / hls4ml) so I don't reinstall every time.
5. **Pods vs Jobs** — interactive pods for dev/testing; batch jobs for long training runs.
