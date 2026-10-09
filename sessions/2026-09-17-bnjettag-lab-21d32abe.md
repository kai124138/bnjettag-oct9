---
title: <ide_opened_file>The user opened the file…
date: 2026-09-17
updated: "2026-09-26T16:35:54"
project: bnjettag-lab
cwd: /Users/kaiyamaguchi/Desktop/bnjettag-lab
model: claude-fable-5-1
git_branch: main
session_id: 21d32abe-d0d3-47bc-9e79-5fe8993f7059
turns: 18
tool_calls: 142
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-lab
---

# <ide_opened_file>The user opened the file…

> [!abstract]- Session at a glance
> **18** turns · **142** tool calls · spans **9** h **59** min · `claude-fable-5-1`
>
> **Tools** Bash ×135, Monitor ×4, AskUserQuestion ×1, Skill ×1, ToolSearch ×1
> **Commands** `/explain-well`, `/config`, `/update-config`, `/model`

---

## You · 10:47

<ide_opened_file>The user opened the file /Users/kaiyamaguchi/Desktop/bnjettag-lab/publication/code/hgq2/bnhgq2/qat.py in the IDE. This may or may not be related to the current task.</ide_opened_file>

why is there so little computing in the nrp now a days, i used to run like 50 runs at once, i swear to god, what is the issue right now and what can we do?

---

## Claude · 10:47

I'll look at the actual cluster state rather than guess.

The 12-run batch from today (`kai-batch0917-screen-e100`) shows **Failed 0/12**. Let me find out why, and why the whole namespace is backed up.

Two separate problems. Let me get the full picture on each.

That confirms a hypothesis. Let me compare the old and current launch patterns.

Good catches. Let me check the three things I hadn't.

Here's what's actually happening. Three separate things, and only one of them is the cluster's fault.

## 1. You are throttling yourself — this is the main answer

Your 12-run screen today was submitted with `parallelism: 1`, raised to `2`. From [launch-record.json:23](local/training-batch-20260917/launch/launch-record.json#L23):

```
"max_concurrent_gpus": 2,
"initial_concurrent_gpus": 1,
"configured_parallelism": 2,
```

So 12 runs went out as an Indexed Job that runs **two at a time**. The September EBOPs ablation is the same shape — `parallelism: 3`, set in [gen_ebops_ablation_jobs.py:110](research/bnjettag/code/jobs/training/variants/gen_ebops_ablation_jobs.py#L110).

The "50 at once" era was a different launch pattern, not a more generous cluster. `research/_attic/pre-r14/jobs/variants/` holds **254 separate single-GPU Job YAMLs** — one file per variant, `kubectl apply` the lot, and the scheduler placed as many as it could find room for. Somewhere between pre-r14 and now, the workflow moved to one Indexed Job with a small `parallelism`, and that number is the ceiling you're feeling.

## 2. Quota is not the constraint — you have room sitting unused

```
requests.nvidia.com/a100    6 / 24      (18 free)
pods                       29 / 200
```

Nobody is capping you at 2. But note: `h100`, `h200`, `gh200` quotas are all hard `0`, and — more importantly — **your jobs exclude A100 entirely.** The required affinity on both kai jobs lists only 4090 / L40S / L40 / A40 / 3090 / A10 / L4 / A5000. So the 18 free A100 slots under your own quota are unreachable by your own manifests. That allowlist does cover 121 nodes, so it's not starving you, but you're leaving the one quota you actually hold on the table.

## 3. Today's batch didn't run slowly — it died

`kai-batch0917-screen-e100` is **Failed, 0/12**, reason `MaxFailedIndexesExceeded`. The manifest sets `backoffLimitPerIndex: 1` and `maxFailedIndexes: 2`. Two indexes failing once each killed the entire 12-run campaign. The pods are already gone, so the logs went with them.

The container has three fail-fast gates before training: `pip install -r requirements-training.txt`, a TF GPU assert, and a `wandb.Api().viewer` auth assert. If W&B shows no runs under `BNJetTag-Batch20260917` from today, it died in a gate — likely the same cause on both indexes, which is exactly the failure mode `maxFailedIndexes: 2` punishes hardest.

## What to do

1. **Raise `parallelism` to 8–12.** Your screen is a ~19k-parameter model; there's no reason to serialize it. Quota and node supply both support it.
2. **Add A100 to the affinity list** (or drop the required list to just `amd64` + preferred). It's 40 more nodes and the only GPU class you hold quota on.
3. **Loosen the failure limits before relaunching** — `backoffLimitPerIndex: 3`, `maxFailedIndexes: 6`, plus a `podFailurePolicy` that ignores `DisruptionTarget`. Nautilus preempts routinely, and right now a preemption counts as a real failure.
4. **Find out why it failed first.** Check W&B for `BNJetTag-Batch20260917` runs today, and `/data/batch20260917` on the PVC. Relaunching 12 indexes into the same unknown gate failure just burns another two hours.

One correction to something you might infer from the pending-pod wall: the 3-day-pending pods in `cms-ml` are `as-jet-*` and `zz-eflm-*`, not yours, and they're stuck on `Insufficient nvidia.com/a40` — a much narrower pin than yours. Cluster contention is real but it is not what stopped you today.

Want me to rebuild the batch manifest with those four changes, and check W&B + the PVC for the actual failure cause first?

---

## You · 11:04

so wait why didnt we want to use a100s are they bad?

---

## Claude · 11:04

Good question — let me check whether that was a deliberate decision or just inherited.

No, they're not bad — and the exclusion was deliberate and documented. But checking this turned up a mistake in what I told you last turn.

## Why A100s were dropped

Three reasons, all recorded:

**1. The model doesn't need one.** From [decisions.md:672-678](.claude/memory/archive/decisions.md#L672) (Decision 3, round-7):

> The r5/r6s job spec (24Gi, 4 cpu, A100/H100-class GPU allowlist) was inherited large-model sizing and was actively blocking round-7: **202/524 nodes rejected on affinity**… Deployable-scale jobs are **data-bound, not FLOP-bound** (resident dataset ≈0.6 GB, peak ≈2 GB).

An 18,657-parameter transformer on a 0.6 GB dataset gets nothing from an 80 GB A100. Your measured epoch time on a 4090 is ~57-64 s ([experiment-log.md:85](.claude/memory/experiment-log.md#L85)).

**2. Demanding A100s made the queue *worse*, not better.** That's the whole point of Decision 3 — the A100-class allowlist was why round-7 sat entirely Pending. The fix was widening 13→20 products and *preferring* the abundant mid-tier.

**3. Cluster manners.** Same entry: "Leaving the A100s to people who need them is also good cluster manners."

There's also a note from 2026-09-12 ([experiment-log.md:81](.claude/memory/experiment-log.md#L81)): "A100 resource hierarchy differs from generic GPU; omitted to avoid narrow queue."

## The correction

That last note is the one that matters, and I glossed it yesterday. I said "add A100 to the affinity list." **That would not have worked.** A100 nodes on Nautilus advertise a *different resource name*:

```
NAME                       PRODUCT                 nvidia.com/gpu   nvidia.com/a100
gp-engine.beocat.ksu.edu   NVIDIA-A100-SXM4-80GB   0                4
gpn-fiona-mizzou-1         NVIDIA-A100-SXM4-80GB   0                4
hcc-nrp-shor-c5226         NVIDIA-GeForce-RTX-4090 (generic gpu)    <none>
```

Your pods request `nvidia.com/gpu: 1`. A100 nodes allocate `0` of that. So an A100 could never schedule your pod no matter what the affinity says — you'd have to change the *resource request* to `nvidia.com/a100: 1`, which is also what makes the 24-unit a100 quota a separate bucket from your normal jobs.

So scratch that item. The "18 free A100 slots" are real but they're a different lane, and entering it means a manifest change plus accepting the slower, more contended queue that Decision 3 already rejected once.

## What that leaves

The A100 point was the weakest of my four suggestions anyway. The real levers are unchanged and all in your own manifest:

1. **`parallelism: 2` → 8-12.** This is the actual throttle. Still the whole answer to "why so little computing."
2. **Widen the mid-tier pool.** Your batch job's required list is 8 products; the round-7 decision that fixed this problem used **20**, preferring A10/L4/2080-Ti/V100. The EBOPs job is narrower still — 4090/L40S/L40 only, which is 25 nodes, and [experiment-log.md:58](.claude/memory/memory/experiment-log.md#L58) records index4 sitting Pending **34 hours** because of it.
3. **`podFailurePolicy` ignoring `DisruptionTarget`**, plus higher `maxFailedIndexes`. Already flagged as open for you to decide at [experiment-log.md:66](.claude/memory/experiment-log.md#L66) — an eviction currently burns a retry.

Item 2 is where your "50 at once" feeling actually lives: widening the pool is what historically unblocked you, and it's the same move Decision 3 made.

Want me to rebuild the batch manifest with a 20-product mid-tier pool, parallelism 10, and the disruption policy — and check W&B for why the 12 indexes died before relaunching?

---

## You · 11:11

okay first lets fix the documentiaton before anythign, analyze whats happenign with our rules, and where those rules are sitting

---

## Claude · 11:11

Right — the A100 mistake was possible because that fact isn't written down anywhere. Let me map where the cluster rules actually live.

Several real problems. Let me pin down the specifics.

Found it. Let me get a second read before I start editing.

Good corrections. Let me verify the A100 claim properly before writing it.

All 40 A100 nodes confirmed: generic `nvidia.com/gpu` is `0` or absent on every one. Let me place the new section.

Now I'll write the canonical section.

Now replace the three copies of the wrong rule with pointers.

Now the logs, per the working agreement.

Documentation is fixed and logged. Here's the analysis you asked for.

## What was wrong with the rules

**One false sentence, copied into three files.** All three said:

> "Cluster quota for `h100/h200/gh200` is 0, so jobs land on A100 / L40S / 4090 / A40 regardless of the YAML's preferences."

It was in [manual-round-runbook.md:185](docs/infrastructure/manual-round-runbook.md#L185), [nrp-training-run/SKILL.md:44](.claude/skills/nrp-training-run/SKILL.md#L44), and `~/.claude/skills/nrp-nautilus/SKILL.md:73`. Two errors:

1. **Jobs cannot land on A100 or A40.** Verified against all 40 A100 nodes today — every one advertises generic `nvidia.com/gpu` as `0` or absent. Those GPUs are behind `nvidia.com/a100`. Our pods request `nvidia.com/gpu: 1`, so an A100 is unreachable regardless of affinity. This is also why my suggestion two turns ago was wrong.
2. **"Regardless of preferences" got over-generalized.** In its original context it was true — the YAML then *preferred* H100/H200 and quota was 0, so the soft preference was moot. But it hardened into "affinity doesn't matter," which is the opposite of the truth for the `required` block. That's what left ablation index4 Pending for 34 hours.

**`backoffLimit` contradicted itself three ways** — `2` in the runbook, `0` in both skills, while live campaigns actually use Indexed `backoffLimitPerIndex` + `maxFailedIndexes`. No document described the Indexed form at all, which is the exact mechanism that killed your 12 runs.

**`parallelism` appeared in no document.** The number actually throttling you was invisible to every doc and every agent reading them.

## Where the rules were sitting — the structural problem

[nrp-nautilus-setup.md](docs/infrastructure/nrp-nautilus-setup.md) is the file named for the cluster, and `CLAUDE.md` points at `docs/infrastructure/` as "how the cluster actually works." It had **zero** scheduling content — 149 lines of kubelogin, zsh quoting, and a test pod. The real rules had scattered into a runbook's troubleshooting list and two skills, where they were *restated* rather than *referenced*. That's the root cause: three copies drift, and nothing tells you which is authoritative.

Worse, the governing decision — round-7 Decision 3, "stop demanding A100s, widen the pool, prefer mid-tier" — lives in [archive/decisions.md:672](.claude/memory/archive/decisions.md#L672), which `CLAUDE.md` marks frozen and read-only. The Sept-12 job then narrowed to 3 products with **no decisions entry at all**. So the operative rule was in a file nobody appends to, and its override was unrecorded.

## What I changed

- **[nrp-nautilus-setup.md](docs/infrastructure/nrp-nautilus-setup.md)** — new "Scheduling, GPU pools and job shape" section, now the single source of truth: the resource-name table, preferred-vs-required, pool policy with the narrowing exception, parallelism-is-yours, the Indexed failure-limit pattern with your batch as the worked example, and the `PodScheduled` diagnostic with its two readings.
- **Runbook + `nrp-training-run` skill** — false rule replaced with pointers; `backoffLimit` reconciled by naming the Indexed form as current and the single-Job form as legacy rather than deleting either.
- **`~/.claude/skills/nrp-nautilus/SKILL.md`** — fixed in place. It loads every session and was teaching the false rule to every agent. Kept self-contained since it's user-wide, not project-scoped.
- **Logged** — `decisions.md` reaffirms Decision 3 and records when narrowing is allowed; `experiment-log.md` carries today's node/quota reads and the three falsified claims.

## Two things for you to decide

**The two skill roots.** `nrp-nautilus` and `vitis-mulder` live in `~/.claude/skills/` — outside git, unreviewable, and they're your cluster knowledge. `CLAUDE.md` says skills come from `.claude/skills/`, which is now not quite true. Moving them in would version them, but they're user-wide and would apply to non-BNJetTag work too. Your call.

**`vitis-mulder` (80 lines) vs repo `hls-mulder` (67 lines) differ** — overlap, not duplication. I didn't diff them in detail; say the word if you want that checked for the same copy-drift problem.

I stopped at docs and logs as you asked — no manifest edits, no relaunch, no W&B check.

---

## You · 12:48

<ide_opened_file>The user opened the file /Users/kaiyamaguchi/Desktop/bnjettag-lab/local/MANUAL_RUNBOOK_TRAINING_AND_R4_SYNTHESIS.md in the IDE. This may or may not be related to the current task.</ide_opened_file>

vitis-mulder (80 lines) vs repo hls-mulder (67 lines) differ — overlap, not duplication. I didn't diff them in detail; say the word if you want that checked for the same copy-drift problem.

The two skill roots. nrp-nautilus and vitis-mulder live in ~/.claude/skills/ — outside git, unreviewable, and they're your cluster knowledge. CLAUDE.md says skills come from .claude/skills/, which is now not quite true. Moving them in would version them, but they're user-wide and would apply to non-BNJetTag work too. Your call.
--> what is the issue with the userwide setting

---

## Claude · 12:48

Let me look at what's actually in those user-wide files before answering.

Good question — and looking at the actual contents, I overstated the case for keeping them user-wide. Let me correct that.

## They aren't actually user-wide knowledge

Your `~/.claude/skills/` has two distinct kinds of thing in it. Most of it is **method** — `principle-fix-root-causes`, `technical-writing`, `unslop`, `interrogate`, ~30 of them. Those are correctly user-wide: they're how you think, they apply to any repo, and they don't go stale.

But `nrp-nautilus` and `vitis-mulder` are **facts about specific infrastructure**:

```
nrp-nautilus:   cms-ml (the Duarte group's namespace), entity kayamaguchi-uc-san-diego,
                the kai-wandb secret, label user=kai
vitis-mulder:   mulder.t2.ucsd.edu, xcvu13p-flga2577-2-e, 2.5 ns / 400 MHz
```

That is not general-purpose knowledge that happens to be useful elsewhere. It's this project's cluster, this group's namespace, this thesis's target part. So "they'd apply to non-BNJetTag work too" — which is what I said — is only true if you're running other jobs in `cms-ml`. If you aren't, there's no upside being paid for here at all.

## Why the location matters

**Facts rot; methods don't.** That's the whole issue. `principle-subtract-before-you-add` will be as true in a year as it is today. "A100s are reachable via `nvidia.com/gpu`" was true-ish once and is false now — and it sat in an unversioned file being loaded into every session, teaching the wrong thing, with:

- **no git history** — `~/.claude` is not a repo. There's no record of when that sentence entered, no diff, no revert. I edited it an hour ago and that edit is equally untracked.
- **no review** — a repo skill goes through a commit you can read. This one changed silently.
- **no propagation** — `nrp-nautilus` (user) and `nrp-training-run` (repo) cover overlapping ground. One is versioned, one isn't. A fix to either never reaches the other. **This is precisely the mechanism that produced the three-copy A100 bug.**

**It also makes the repo's central claim false.** `project-context.md` says this repo *is* the environment — "the pod, the agent team, cluster docs." Someone cloning it gets 12 skills and silently misses the two that explain how to reach the cluster and the synthesis box. `CLAUDE.md` says "skills from `.claude/skills/`", which is now not quite true.

And one practical thing: new laptop, or `~/.claude` wiped, and that knowledge is gone. It's the only copy.

## The honest counter-argument

If you *do* run things in `cms-ml` outside BNJetTag, user-wide means they load without needing this repo open. That's real. The fix isn't to give that up — it's to stop having the only copy be the unversioned one.

## What I'd do

Move both into `.claude/skills/` as the source of truth, then symlink them back:

```
ln -s ~/Desktop/bnjettag-lab/.claude/skills/nrp-nautilus ~/.claude/skills/nrp-nautilus
```

You keep them loading everywhere, and they become versioned, reviewable, and backed up. The `principle-*` skills stay exactly where they are — they're in the right place.

The rule that falls out, which is worth writing into `CLAUDE.md`: **method goes user-wide, verifiable facts go in the repo.** A skill that contains a hostname, a namespace, a part number, or a quota belongs under version control, because those are the things that change under you without telling you.

Want me to do the move and symlink, and diff `vitis-mulder` against `hls-mulder` for the same copy-drift while I'm in there?

---

## You · 12:50

Move both into .claude/skills/ as the source of truth, then symlink them back:

Want me to do the move and symlink, and diff vitis-mulder against hls-mulder for the same copy-drift while I'm in there?--> yes, 

do everything thats good for the system and that allows me to launch jobs smoothly and easily withouot burning tokens or crashing

---

## Claude · 12:50

Let me read all four skills in full before restructuring anything.

`vitis-mulder` already declares `hls-mulder` supersedes it — that pair is deliberately layered, not drifted. Let me check what tooling already exists before I add any.

Found the origin of the low-concurrency habit — line 40 of the skill recommends "staged launcher (≤3 concurrent)... staged is polite." Let me get a review before restructuring.

Starting with the blind spot — I created a restatement an hour ago that my own decision entry forbids.

No remote — repo is local-only, so the ssh username is fine to land. Now the move and symlink.

Now the linter — the piece that actually prevents the next crash.

Now the real test — it must catch today's failure on the actual manifest.

Caught everything — plus a bug I'd missed: `NVIDIA-A40` in that list was always dead weight. Let me verify `status` and that legacy single-Jobs don't false-alarm.

Two real problems: PyYAML isn't installed, so `lint` can't read actual YAML — the main use case. Fixing with kubectl, which is already a hard requirement.

Severity is wrong — a dead entry in a wide list is dead weight, not fatal. Let me fix that and compact the output.

Now wiring it into the docs and fixing the "≤3 concurrent" line that created the habit.

Now the mulder de-duplication — single-homing the five restated facts.

Every fact single-homed. Now CLAUDE.md and the logs.

Final verification of the whole system before I hand back.

Three real issues — one is a bug in the function the whole diagnostic hangs on. Fixing.

The bug was real — before the fix that message would have reported "Insufficient cpu" as dominant and told you to wait. Now checking nothing regressed.

V100/2080-Ti do exist (29 nodes), so the table stands. Final three sentence corrections.

Done. Here's what changed and why it matters.

## The tool — `nrp-lab/nrp_doctor.py`

This is the part that serves "launch smoothly without burning tokens or crashing."

```
python3 nrp-lab/nrp_doctor.py status            # why is nothing running?
python3 nrp-lab/nrp_doctor.py lint <job>.yaml   # before every kubectl apply
```

`status` replaces the ~8 exploratory `kubectl` calls this session spent working out your problem. Critically, it separates the two situations that look identical from outside: real cluster saturation versus your own required list being too narrow — and prints which one you're in.

`lint` is the pre-launch gate, and it exits non-zero so it can block a launch script. Run against the manifest that died today, unprompted:

```
ERROR  maxFailedIndexes=2 with completions=12: 2 bad indexes kill ALL 12 runs...
WARN   1 required-list product(s) unreachable: NVIDIA-A40 (needs nvidia.com/a40)
WARN   parallelism=1 but completions=12: a self-imposed ceiling, not a cluster limit
WARN   backoffLimitPerIndex=1: one blip kills an index
WARN   no podFailurePolicy ignoring DisruptionTarget
```

It reads node facts live from the cluster instead of hardcoding them, so the resource-name check can't rot the way the docs did.

**It found a latent bug nobody had noticed:** `NVIDIA-A40` sits in the required list of both the batch job and `nrp-lab/kai-lab.yaml`, and was never reachable — A40 needs `nvidia.com/a40`. Harmless, but your pool has always been one product smaller than it looked.

**A bug in my own tool, caught in review:** the Pending diagnostic was dropping the *first* reason in the scheduler's message. Since the affinity bucket is often first — the one that matters most — it would have reported the second-largest bucket as dominant and told you to wait when the real answer was "fix your manifest." Fixed and tested both ways.

## Skills moved and versioned

`nrp-nautilus` and `vitis-mulder` now live in [.claude/skills/](.claude/skills/), symlinked into `~/.claude/skills/` so they still load everywhere. Verified each loads exactly once — no collision from the two roots.

I also had to undo my own mistake: an hour ago I patched the user-wide skill with a self-contained copy of the scheduling rules, then wrote a decision saying not to do exactly that. Once it moved into the repo the justification was gone, so it now points at the doc instead.

## The mulder pair — not what I suspected

`vitis-mulder` already declared `hls-mulder` supersedes it. That's deliberate layering, not drift. But five facts were restated in both (the three hls4ml stages, part + clock, licence, `nrpcopy`, after-run checks). Each is now single-homed — machine in `vitis-mulder`, project flow in `hls-mulder` — with pointers instead of copies.

## Where the low concurrency came from

[nrp-training-run/SKILL.md:40](.claude/skills/nrp-training-run/SKILL.md#L40) said *"staged launcher (≤3 concurrent)… staged is polite."* The etiquette kernel is real — don't camp idle GPUs — but it got read as a throughput cap, and that's the origin of your 2–3 concurrent runs. Rewritten: size `parallelism` to free capacity in your pool; politeness is about idling, not serializing.

## Rule, written into CLAUDE.md

**Method goes user-wide; facts go in the repo.** A skill carrying a hostname, namespace, part number or quota is a fact — facts decay, so they need version control. `principle-*` and friends stay where they are.

Logged in `decisions.md` and `experiment-log.md`. Nothing committed, nothing launched, no research-tree generators touched.

One flag: `vitis-mulder` carries your SSH username. Fine now — this repo has no remote — but check it before that ever changes.

The obvious next step is rebuilding the batch manifest with a wide pool, `parallelism` ~10 and sane failure limits, then linting it and finding out why those 12 indexes actually died. Say the word.

---

## You · 14:10

what the fuck is parellelism?

---

## Claude · 14:10

Fair — I've been using that word for four turns without ever defining it. Let me do this properly.

**L2 — working level.** The claim in one sentence:

> `parallelism` is a line in your job YAML that says *how many pods may run at the same time*, and `completions` says *how many must finish in total* — so 12 runs with `parallelism: 2` means Kubernetes runs them two at a time, six waves deep, even when 100 GPUs are idle.

## The mechanism, with your actual numbers

Your batch job says this:

```yaml
completionMode: Indexed
completions: 12      # twelve training runs must finish
parallelism: 2       # ...but only two may be in flight at once
```

`Indexed` means Kubernetes hands each pod a number in an environment variable, `JOB_COMPLETION_INDEX` — 0 through 11. Your container uses it to pick which config to train:

```bash
CONFIG=${CONFIGS[$JOB_COMPLETION_INDEX]}
```

So index 0 trains config 0, index 7 trains config 7. One job spec, twelve different runs.

Now watch what `parallelism: 2` does over time. Say each run takes 4 hours:

```
hours 0-4    [0][1]                  ← 2 running, 10 waiting
hours 4-8    [2][3]
hours 8-12   [4][5]
hours 12-16  [6][7]
hours 16-20  [8][9]
hours 20-24  [10][11]
                                     total: 24 hours
```

With `parallelism: 12`, all twelve start at once and the whole campaign finishes in **4 hours**. Same work, same cluster, same GPUs — 6× the wall-clock, purely from that one number.

Nothing in Kubernetes forces `2`. You wrote it. That's the entire point I've been making: I said "the cluster isn't the constraint," and this is the line of YAML that *is* the constraint.

## Why anyone would set it low

Two legitimate reasons, neither of which applies to you:

- **Rate-limiting something downstream** — hammering a shared database, an API, a license server.
- **Politeness on a shared cluster** — not taking 50 GPUs when colleagues need them.

The second is where yours came from. [nrp-training-run/SKILL.md](.claude/skills/nrp-training-run/SKILL.md) used to say *"staged launcher (≤3 concurrent)… staged is polite."* That advice was about **not camping on idle GPUs**, and it got read as **a cap on throughput**. Those are different things: politeness means giving a GPU back when you're not using it, not refusing to use twelve that are sitting free.

## The anchor — why this cost you today

`parallelism` interacts with the thing that actually killed your batch. From the live spec of `kai-batch0917-screen-e100`:

```
parallelism: 2            backoffLimitPerIndex: 1
completions: 12           maxFailedIndexes: 2
```

`maxFailedIndexes: 2` means *if 2 of the 12 indexes fail, kill the entire job*. Indexes 1–3 failed, and the job died with `MaxFailedIndexesExceeded` — **0 of 12 succeeded**. Runs 4 through 11 never even started; they were still queued behind the `parallelism: 2` gate when the whole thing was torn down.

So the low parallelism didn't just make it slow. It meant that when the early runs hit a problem, everything else was still sitting in the queue where it could be cancelled. High parallelism would have had all 12 already running and most of them likely past the failure point.

That's the interaction `nrp-lab/nrp_doctor.py lint` now flags as an ERROR.

## The edge — where this stops being simple

- **`parallelism` is live-editable**, unlike most of a Job spec: `kubectl -n cms-ml scale job/<name> --replicas=10` works on a running job. You don't have to relaunch to speed one up.
- **Setting it high doesn't guarantee 12 pods run.** It's a ceiling, not a floor. If only 5 nodes in your required GPU pool are free, 5 run and 7 sit `Pending` — which is fine and self-correcting, and exactly what the old "the scheduler self-limits" note meant.
- **Actual `completions` semantics are subtler than I've implied** for non-Indexed jobs, where pods aren't distinguishable and it's just "run this N times." Yours is Indexed, so the mental model above holds.
- **I don't know why indexes 1–3 failed.** The pods and events are gone. The container has three fail-fast gates before training — `pip install`, a TF GPU assert, a W&B auth assert — and W&B would tell us whether any run reached training. That's the check I'd do before relaunching.

---

Want me to add this to the offline KB (`lab ask "what is parallelism"` would then answer instantly, no model call)? And it's a two-word change to unblock the current job — `kubectl scale job/kai-ebops-abl-0912-e1000 --replicas=7` would let its last arm and any requeued ones run at full width instead of 3.

I've read the settings files. `/update-config` came through with no arguments, so tell me what to change — but given where we just landed, here are the two that would actually pay off.

No response requested.

---

## You · 14:52

<ide_opened_file>The user opened the file /Users/kaiyamaguchi/Desktop/bnjettag-lab/local/MANUAL_RUNBOOK_TRAINING_AND_R4_SYNTHESIS.md in the IDE. This may or may not be related to the current task.</ide_opened_file>

so can u fix that and relaunch so that we can finish training as soon as possible

and can we get a it guy agents who stays on top of the kubernetes nrp and mulder configurations and knows everything about it and if something gets falgged or crashes, he logs that and takes record and learnes and saves the info tho his inventory

---

## Claude · 14:52

Two things. Diagnosis first — relaunching 12 runs without knowing why 1–3 died risks repeating today.

Good news: **the work isn't lost.** A00 has 60 saved epochs, A01 has 39, checkpoints + optimizer/PID state persist on the PVC, and resume was preflight-verified. Indexes 1–3 failing 7 pods with `backoffLimitPerIndex: 1` and no `podFailurePolicy` is the signature of preemption burning retries.

ConfigMap is alive and immutable; zero pods remain, so no double-writer risk. Building the fixed manifest.

Pool per round-7 Decision 3: modern mid-tier, Pascal excluded — **156 nodes** vs the 118 it had.

Server dry-run caught inherited controller labels from the live dump. Stripping.

One safety check before applying: confirm it resumes rather than overwrites A00's 60 epochs.

Line 26 uses `args.index`, but the job command passes no `--index`. Checking how it's obtained — this could be the actual root cause.

Resume is safe (`"indexed, resumable"`, index from `JOB_COMPLETION_INDEX`, cumulative epoch target). Launching.

11 pods failed instantly, all on **one node**. Grabbing the reason while the pods still exist — this is the diagnosis I couldn't get before.

**Root cause found** — and it's not preemption:

```
UnexpectedAdmissionError: Allocate failed ... GPU is lost, which is unexpected
node: nautilus-ext-gpu01.fullerton.edu
```

A broken node advertising GPUs it no longer has. It accepts pods and instantly rejects them, burning a retry each time. This is what killed the original job. Acting now before it eats the retry budget.

Now the IT agent, while that runs.

No admission errors on r3 — 12 pods active, starting up. Writing the ops agent and its inventory.

First pod ready, zero failures. Seeding the inventory.

Now closing the loop — the inventory's bad-node list becomes a machine check.

Loop closed. Logging.

**Root cause found, and it was never your config.** A broken node:

```
UnexpectedAdmissionError: Allocate failed ... failed to get nvlink state:
GPU is lost, which is unexpected
node: nautilus-ext-gpu01.fullerton.edu
```

It advertises GPUs its driver can't see — accepts pods, rejects them in seconds, burns a retry each time. With your old `backoffLimitPerIndex: 1` / `maxFailedIndexes: 2`, three rejections killed all 12 runs.

**Raising parallelism is what exposed it.** At 2 concurrent it looked like random failure; at 12, eleven simultaneous rejections on one hostname named the cause in under a minute.

## Training is running

`kai-batch0917-screen-e100-r3` — 12 active, first pod ready, zero failures.

| | old job | r3 |
|---|---|---|
| parallelism | 1–2 | **12** |
| backoffLimitPerIndex | 1 | 3 |
| maxFailedIndexes | 2 | 6 |
| podFailurePolicy | none | ignores evictions |
| pool | 8 products / 118 nodes | 16 / 155, bad node excluded |

Same ConfigMap and PVC root, so it **resumes**: A00 from 60 epochs, A01 from 39, target 100. Verified `run_batch_screen.py` is indexed/resumable and doesn't restart from zero. I'm monitoring it; you'll get told if it goes terminal.

One process catch worth keeping: a server-side dry run rejected the first manifest over `controller-uid` labels inherited from the live job dump. Always dry-run a manifest derived from a live object.

## Your IT guy

**`cluster-ops`** agent ([.claude/agents/cluster-ops.md](.claude/agents/cluster-ops.md)) — owns Nautilus + mulder state, diagnoses Pending/Failed/evicted/rejected, and is told to capture perishable pod evidence *before* GC, which is exactly what was missing yesterday.

**Its inventory** ([.claude/memory/cluster-inventory.md](.claude/memory/cluster-inventory.md)) — known-bad nodes, failure signatures with verbatim error strings (greppable), dated cluster facts. Seeded with today's findings.

**The part that makes it learn rather than just log:** after every incident it must ask *can a machine catch this next time* and implement it. Already done for today —

- bad node → `KNOWN_BAD_NODES` in `nrp_doctor.py`
- `lint` now warns on any manifest that doesn't exclude a known-bad node (verified: r2 warns, r3 clean)
- `status` flags any node currently rejecting our pods and tells you to add it

Inventory holds *observations*; the setup doc holds *doctrine*. Keeping those apart is what stops the inventory becoming a fourth copy of the scheduling rules.

One note: `manual-round-runbook.md` calls `UnexpectedAdmissionError` "a device-plugin race with zero side effects." True for a one-off — but many at once on one node is a broken node, and retrying feeds it. That distinction is now in the inventory.

---

## You · 19:37

can u keep working on the IT guy and get all of the nrp and mulder things setup and make sure taht they work and that all systems are healthy and easily accesible

---

## Claude · 19:39

Mulder check works (root disk full is real). Fixing a `pgrep` double-print, then wiring the `/ops` command, inventory, and docs in one pass.

All systems checked, tooling in place, training progressing.

## State right now

**Nautilus** — `r3`: 4/12 arms passed the 100-epoch rung (verified from pod logs: A00 resumed at epoch 60 → 100; A01, A03, A09 also at 100), 8 running, 0 failed, no admission errors. Monitor re-armed; you'll hear if it goes terminal.

**mulder** — reachable, 118 GiB RAM free, Vitis present. Two real problems:
- **Root `/` is 100% full** (20 KB of 187 G). System-level, not ours. Runners must keep `TMPDIR` under `$HOME` — already the practice, now enforced as an ERROR by the check.
- **R4 synthesis is dead, and the cause was misdiagnosed.** Verbatim, 9× across attempts:
  ```
  ERROR: [HLS 200-642] The 'config_array_partition -maximum_size' command is not supported.
  ```
  hls4ml 1.3.0 emits a directive Vitis 2023.2 removed. The earlier "pragma/linkage" theory was chasing the wrong thing — C-sim on the same export is bit-exact. Fix is a one-line TCL change in the research tree's conversion; flagged, not done (out of this repo's scope).

## What's now accessible

```
python3 nrp-lab/nrp_doctor.py all      # both machines, one call
/ops                                   # same, via cluster-ops, which also diagnoses + records
```

`nrp_doctor.py` gained `mulder` and `all`. `/ops` is registered. Inventory ([cluster-inventory.md](.claude/memory/cluster-inventory.md)) now holds the bad Nautilus node, the mulder disk state, and the R4 signature with its cause. Docs, skills and `CLAUDE.md` point at all of it.

The old failed job `kai-batch0917-screen-e100` is still listed as a record (7-day TTL); harmless.

5/12 done, 7 running, 0 failed. Routine progress — nothing to act on.

7/12 done, 5 running, 0 failed. Still routine.

Re-armed. Last seen: 7/12 done, 5 running, 0 failed.

Unchanged: 7/12 done, 5 running, 0 failed.

---

## You · 20:11

wait how did u save one of the ones that crahsed? make sure to log that tech

---

## Claude · 20:12

Logged in three places. The short version of how it worked:

**Nothing was rescued by hand — the pipeline is built so a dead Job loses nothing.** `bnhgq2/ablation.py` writes an atomic checkpoint every epoch to the PVC (temp file + `os.replace`, `latest.json` pointer, two generations kept), and on start it follows `latest.json` and resumes — but only if `config_sha256` and `code_sha256` (from the ConfigMap's `$BNHGQ2_CODE_SHA256`) match; otherwise it refuses with `Resume code mismatch`. So it can't silently train on the wrong history.

My part was just not breaking those invariants: **new Job name, everything else identical** — same immutable ConfigMap, same configs, same PVC root, same arm names; changed only the Job shape. Plus confirming zero pods remained from the old job (double-writer risk), server-side dry-running the manifest, and killing r2 at `ready=0`. Proof was in the pod log: `[train] batch20260917-a00-s1 ... resume_epoch=60`.

Where it's written:
- [nrp-nautilus-setup.md](docs/infrastructure/nrp-nautilus-setup.md) → new "Recovering a dead campaign" subsection, the 6-step recipe
- `decisions.md` → the technique and why it works
- [cluster-ops.md](.claude/agents/cluster-ops.md) → rule 6: read `runs/<arm>/latest.json` before ever proposing a rerun

Training is still 7/12 done, 5 running, 0 failed.

8/12 done, 4 running, 0 failed.

Re-armed. Last seen 8/12 done, 4 running, 0 failed.

Unchanged: 8/12 done, 4 running, 0 failed.
