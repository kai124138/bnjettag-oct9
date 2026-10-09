---
title: how many jobs are running in nrp and mulder by us right now
date: 2026-09-23
updated: "2026-09-26T16:35:54"
project: bnjettag-lab
cwd: /Users/kaiyamaguchi/Desktop/bnjettag-lab
model: claude-opus-5-5
git_branch: HEAD
session_id: 4f038da3-9fe8-42b6-ab80-eb7ed5ec10fd
turns: 2
tool_calls: 7
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-lab
---

# how many jobs are running in nrp and mulder by us right now

> [!abstract]- Session at a glance
> **2** turns · **7** tool calls · spans **1** min · `claude-opus-5-5`
>
> **Tools** Bash ×7

---

## You · 14:59

how many jobs are running in nrp and mulder by us right now

---

## Claude · 15:00

Found the NRP namespace (cms-ml). Now I'm filtering it for running jobs.

You have **0 jobs running on either NRP or mulder** right now.

**NRP (the `cms-ml` namespace):**
- None of your `kai-*` jobs are running. The recent ones finished, failed or are suspended:
  - **Finished:** `kai-batch0917-full-e1000-0920`, `kai-batch0918-*`, the `kai-n8n64` preflight and data jobs.
  - **Failed:** `kai-engram-full-e1000-0920` (1 of 4 finished), `kai-n8n64-screen-0922-26f3cc` (12 of 16 finished).
  - **Suspended:** `kai-n8n64-canary-0922-a2c434`.
- The whole namespace has **13 running jobs**, and they belong to other people:
  - 11 are Raunav's (`ft-legs-*`, `mtx-rand-*`, `eval-anomaly-*`).
  - `hz-aio-f3`.
  - A `phatjet-sonn-snapshot` job that runs on a schedule.
- There are also about 16 long-running server pods (file browsers, Grafana and similar). Those are always on and aren't jobs.

**mulder:**
- Nothing is running under `kayamaguchi`, and there's no Python or training process from anyone. The only thing of yours there is the Claude remote server.
- mulder has neither `squeue` nor `condor_q`, so there's no batch queue to check.

If "us" means the whole lab, not just you, tell me whose usernames or job-name prefixes count and I'll recount.
