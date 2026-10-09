---
title: infrastructure/ — cluster and machine setup
status: current
date: 2026-09-08
---

# infrastructure/ — cluster and machine setup

For learning NRP from scratch, start with the current WSL section of
`nrp-nautilus-setup.md`, then `../cheatsheet.md`. The official
[NRP access guide](https://nrp.ai/documentation/userdocs/start/getting-started/),
[Basic Kubernetes tutorial](https://nrp.ai/documentation/userdocs/tutorial/basic/),
and [kubectl quick reference](https://kubernetes.io/docs/reference/kubectl/quick-reference/)
cover the underlying commands. The reading order and a first read-only exercise are
also in `../field-guide.html`, under **Asked before** (2026-10-03).

| File | What it is |
| --- | --- |
| `nrp-nautilus-setup.md` | Connecting to and using the NRP Nautilus cluster (kubelogin flow, namespace `cms-ml`). |
| `manual-round-runbook.md` | Worked Round 14 example of configs, code packaging, training, W&B, and ROC evaluation. Its old paths and launch commands are examples, not the current supported submission procedure. |
| `run-handoff.md` | Current supported Chang/Delta procedure: freeze actual working bytes, prepare and validate an immutable run record, then submit after the scientific gate and action-time authorization. |
| `wandb-layout.md` | How runs, checkpoints, and artifacts are named and connected. |
| `gpu-selection-policy.md` | Current Chang/Delta rule for selecting a GPU product and pack size by measured training time, safe memory and the 40% utilization floor. |
| `jev-lab.md` | Local advisory decision tools, method checks, and bounded cooperative loops for Claude Code and workspace Codex. |
| `mulder-setup.md` | The Vitis HLS synthesis box: access, toolchain paths, hardware, and the memory/concurrency limits that govern csynth. |
| `home-pc-cluster-recreation.md` | Prompt + prerequisites for recreating the training/synthesis environment on the home PC (Ubuntu 22.04, Vitis HLS 2023.2). |
| `obsidian-session-notes.md` | The hook that mirrors assistant sessions into the vault under `Sessions/` — what it writes, how to backfill, how to turn it off. |

Workflow playbooks (how jobs are actually launched, monitored, and verified) live in
`.claude/skills/`; superseded PVC-era prose runbooks are in
`../../_attic/legacy-archive/archive/nrp-runbooks/`.

## Current home PC remote access

The machine record is `~/HOME-PC.md` on the home PC (kaipc). Its 2026-10-09 section
records mosh over the WSL Tailscale node `kaiypc` (`100.93.120.69`), SSH port 2222,
the Windows login keepalive task, and `vmIdleTimeout=-1`. The
[command cheat sheet](../cheatsheet.md#home-pc-terminal-from-the-mac) gives the Mac
command with `--predict=always` for local typing feedback on a slow connection.
It also records VS Code's built-in local echo, enabled for this WSL connection so
the existing integrated terminal can predict typing while keeping SSH.
The [tmux command](../cheatsheet.md#reconnect-to-the-same-tmux-session) creates or
reattaches a persistent lab terminal, including from Ghostty on the Mac. Mosh,
tmux, systemd, SSH, the locale, firewall state, Windows idle configuration, and
the running login task were rechecked on 2026-10-09; no further system changes
or restart were required. Local encrypted mosh/tmux and detach/reattach tests
passed. A later live Ghostty mosh/tmux connection was observed, with Claude in
the lab folder. Kai reports immediate predicted typing; its underlines clear
after the remote screen update. Direct Tailscale pings measured 129–222 ms.
