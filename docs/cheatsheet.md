# Cheat sheet — doing it yourself

Every command here is taken from this repo's scripts, skills and runbooks, checked
2026-10-02. Paths are relative to `~/lab/bnjettag` unless they start with `cd`.
`<job>` and `<pod>` are names you read off `kubectl get`.

## Claude on the home PC, driven from the Mac (no SSH typing)

Remote Control, added 2026-10-10. Start once on the home PC, then use
claude.ai/code or the Claude app on the Mac; the Mac can sleep.

```bash
tmux new -s rc
cd ~/lab/bnjettag && claude remote-control --name bnjettag   # Ctrl-b d to detach
claude remote-control --continue                             # reattach, within ~4 h
```

For mod work, start `claude --remote-control bnjettag` inside the mosh/tmux
session below instead: panes in Ghostty when attached, web/phone when away.
The home PC must stay awake. See [Remote Control](https://code.claude.com/docs/en/remote-control).

## Home PC terminal from the Mac

Configured and checked in WSL on 2026-10-09. Install mosh on the Mac with
`brew install mosh` if needed, then connect while Tailscale is running:

```bash
mosh --predict=always --ssh="ssh -p 2222" \
  --bind-server=ssh \
  --server="env LANG=C.UTF-8 LC_ALL=C.UTF-8 /usr/bin/mosh-server" \
  kaimoe@100.93.120.69
```

This connects to the WSL node `kaiypc`. Mosh predicts ordinary echoed keystrokes
locally for immediate typing feedback; server output still depends on the network.
Installing mosh does not change an existing SSH session's transport. The VS Code
local echo settings below provide prediction within the integrated terminal.
The setup and restart checks are recorded in `~/HOME-PC.md`. A live Ghostty
mosh/tmux connection was subsequently observed on 2026-10-09. Kai reports that
typing appears immediately with underlines that clear when the PC's screen
update catches up. Five direct Tailscale pings measured 129–222 ms round-trip.
See [Mosh usage and prediction](https://mosh.org/#usage).

Keep VS Code connected to the same WSL folder for editing. In the separate mosh
session, start Claude with:

```bash
cd ~/lab/bnjettag
claude
```

Connect once per terminal session and leave that window open while working.

To connect and start Claude in the lab folder in one command from the Mac:

```bash
mosh --predict=always --ssh="ssh -p 2222" \
  --bind-server=ssh \
  --server="env LANG=C.UTF-8 LC_ALL=C.UTF-8 /usr/bin/mosh-server" \
  -- kaimoe@100.93.120.69 \
  bash -lc 'cd ~/lab/bnjettag && exec claude'
```

Exiting Claude closes this connection. The folder is `~/lab/bnjettag`.

### Reconnect to the same tmux session

Mosh and tmux were both already installed when rechecked on 2026-10-09. A local
encrypted mosh/tmux UTF-8 test passed, followed by a detach and reattach test
that preserved the lab directory. No additional system changes or restart were
required. A later live Ghostty connection was confirmed with Claude in this tmux
session; typing prediction appears immediately, followed by remote confirmation.

Run this in Ghostty or another Mac terminal with Tailscale connected:

```bash
TERM=xterm-256color mosh --predict=always --ssh="ssh -p 2222" \
  --bind-server=ssh \
  --server="env LANG=C.UTF-8 LC_ALL=C.UTF-8 /usr/bin/mosh-server" \
  -- kaimoe@100.93.120.69 \
  tmux new-session -A -s bnjettag -c /home/kaimoe/lab/bnjettag
```

This creates or reattaches `bnjettag`. Run `claude` to start a new Claude session
there. Detach with `Ctrl+B`, then `D`, and reuse the same command to reconnect.
The programs remain in tmux while WSL stays running; a WSL shutdown ends them.
Use `/ide` inside Claude to connect its diff viewer to the existing VS Code
Remote SSH workspace.

For Ghostty, install missing Mac applications with `brew install --cask ghostty`
and `brew install mosh`. Ghostty uses `xterm-ghostty`, which is absent in the
WSL terminal database; the command uses `xterm-256color` for compatibility.
See [Ghostty installation](https://ghostty.org/docs/install/binary) and
[terminal compatibility](https://ghostty.org/docs/help/terminfo).

### Run mosh in a terminal tab inside VS Code

Keep the Mac VS Code Remote SSH window open at `/home/kaimoe/lab/bnjettag`.
Press `Cmd+Shift+P` and select **Terminal: Create New Integrated Terminal (Local)**.
This new tab starts a shell on the Mac. Run the mosh command above in that tab;
the one-command variant also starts Claude in the WSL lab directory. If mosh is
missing on the Mac, run `brew install mosh` in the local tab first.

The editor uses Remote SSH and this terminal uses mosh against the same WSL files.
Mosh predicts typing locally; application redraws can limit prediction and output
still depends on the network. This Mac workflow has not been tested here. See
[VS Code's local terminal documentation](https://github.com/microsoft/vscode-docs/blob/main/docs/terminal/advanced.md#local-terminals-in-remote-windows).

Keep opening saved files from the existing Remote SSH Explorer or `Cmd+P`.
For Claude's diff viewer, enter `/ide` inside Claude after connecting through
mosh and select the VS Code workspace `/home/kaimoe/lab/bnjettag`. The IDE bridge
for that folder was verified to be listening in WSL; a mosh connection to it has
not been tested. Starting a new Claude session does not transfer an existing
conversation or pending approvals. See
[Claude's external terminal integration](https://code.claude.com/docs/en/vs-code#run-cli-in-vs-code).

### Keep using VS Code's integrated terminal

On 2026-10-09, these settings were enabled for the WSL connection in
`~/.vscode-server/data/Machine/settings.json`:

```json
{
  "terminal.integrated.localEchoEnabled": "on",
  "terminal.integrated.localEchoLatencyThreshold": 0
}
```

This uses VS Code's own local prediction while keeping the SSH connection. It can
apply to an existing terminal without restarting SSH. Claude's interface redraws
may limit prediction; the effect still needs checking in the user's VS Code window.
To undo it, change the enabled value to `"off"`, preserving other settings.
See [VS Code's local echo documentation](https://code.visualstudio.com/docs/terminal/advanced#reducing-remote-input-latency-preview).

### Graphical alternative: Mac interface with PC execution

Kai selected Mac interface with PC execution on 2026-10-09, then clarified a
preference for terminal use. For a graphical alternative, keep the Mac VS Code
window connected through Remote SSH to `/home/kaimoe/lab/bnjettag`. The Claude Code extension
2.1.296 is already installed in WSL. Press `Cmd+Shift+P` and select
**Claude Code: Open in New Tab**, then type in its graphical prompt box.
The interface runs on the Mac and tools run against the WSL workspace; there is
one copy of the lab files. Prompt typing does not need remote terminal echo,
although responses and tool output still depend on the connection. See
[Claude's VS Code guide](https://code.claude.com/docs/en/vs-code).

The extension's **Use Terminal** setting defaults to off. If the command opens
a terminal, uncheck that setting under **Extensions → Claude Code**. The Mac
panel has not been tested here; no extension setting was changed.

To use a browser view of the same existing PC Claude conversation, enter
`/remote-control` inside that Claude session, accept its one-time confirmation,
and open its session URL on the Mac. This keeps tools and files on the PC and
shares that conversation across connected views. An eligible Claude login and
a running PC Claude process are required. Remote Control has not been activated
or tested here. See [Remote Control](https://code.claude.com/docs/en/remote-control).

## Jev tools and method audits

```bash
python3 tools/jev_lab.py doctor --live
python3 tools/jev_lab.py call jev_triage_logs --input tools/jev/examples/triage.json
python3 tools/jev_smoke.py --live
local/jev-runtime/bin/python -m unittest discover -s tests -p 'test_jev_lab.py'
```

Claude Code: `/jev-lab`. Codex in this workspace: `$jev-lab`.
The smoke command makes eight synthetic Jev calls through the real MCP server
and saves its report in `local/2026-10-02-jev-integration/SMOKE.json`.
Protocol snapshots and cooperative loops are local workflow tools; existing
scientific review, immutable handoff, and action-time launch gates still apply.
Tool arguments and a ready-to-run prompt are in
[the Jev runbook](infrastructure/jev-lab.md).

## 0. The mental model in five lines

1. Code lives in `bnjettag/code/hgq2/`. An experiment is a **config JSON**, not a code fork.
2. Code reaches the cluster as a **ConfigMap** (a tarball, under 1 MB). Stale ConfigMap = old code runs.
3. A run is a Kubernetes **Job** YAML, generated by a `gen_*_jobs.py` script. Never hand-edit one.
4. Pods are disposable. Data comes from Zenodo at pod start; checkpoints and metrics go to **W&B**.
5. Training on Nautilus (`cms-ml`), synthesis on `mulder`, nothing heavy on the laptop.

## 1. Cluster access

```bash
kubectl config use-context nautilus     # should already be the current context
kubectl get pods -n cms-ml              # works = you are in
kubectl oidc-login clean                # on "401 Unauthorized": clears the token, next command re-logs in
```

`cms-ml` is the whole group's namespace. Your objects start with `kai-`. Never delete anyone else's.

## 2. Is the cluster healthy for me? (start here)

```bash
python3 nrp-lab/nrp_doctor.py status    # quota, your jobs, hung pods, why pods are Pending
```

Not `mulder` or `all` from this WSL machine: mulder is reached only from the Mac (`AGENTS.md`).

## 3. Launch a training round (the order matters)

```bash
cd ~/lab/bnjettag/bnjettag/code/jobs/training/variants

# a. regenerate configs and job YAMLs after changing the generators
python3 ../../../hgq2/configs/gen_r14.py      # run configs   (r15: the matching gen script)
python3 gen_r14_jobs.py                       # job YAMLs
python3 gen_r14_roc_jobs.py                   # eval YAMLs

# b. lint every manifest (the hook also blocks apply on a lint error)
python3 ~/lab/bnjettag/nrp-lab/nrp_doctor.py lint kai-bn14-*.yaml

# c. W&B secret exists? (never cat or echo the key)
kubectl get secret kai-wandb -n cms-ml

# d. ship the code; WRITE DOWN the md5 it prints
./make_code_configmap_r14.sh                  # r15: ./make_code_configmap_r15.sh

# e. ONE job first, read its log to the epoch lines
kubectl apply -f kai-bn14-l1x3-n16-w1a8-s1.yaml -n cms-ml
kubectl get jobs,pods -n cms-ml | grep kai-bn14
kubectl logs -f <pod> -n cms-ml               # Ctrl-C to stop following; the job keeps running

# f. then the round
./launch_r14.sh stage1                        # r15: ./launch_r15_gamma.sh
./launch_r14.sh stage2
```

Log lines to see in step e, in order: `[code] configmap tar md5:` (matches step d) →
`[gate]` → `[gpu] TF sees` → `[data] tarball bytes: 2725115104` → epoch lines.
If you see all five, close the laptop.

`launch_r14.sh` stages in waves and polls, so it needs the laptop awake. Alternative:
`kubectl apply -f` every YAML at once and let the scheduler queue them.

## 4. Checking on a run (later, from anywhere)

```bash
kubectl get jobs -n cms-ml | grep kai-                  # COMPLETIONS column: 1/1 = done
kubectl get pods -n cms-ml | grep kai-                  # STATUS: Running / Completed / Error / Pending
kubectl logs job/<job> -n cms-ml --tail=50              # last 50 lines
kubectl logs <pod> -n cms-ml --previous --tail=50       # log of the crashed attempt before a retry
```

Why is it Pending? (`describe` truncates the reason, this does not):

```bash
kubectl get pod <pod> -n cms-ml \
  -o jsonpath='{.status.conditions[?(@.type=="PodScheduled")].message}'; echo
```

| status | meaning |
| --- | --- |
| `Pending` for minutes | normal queueing |
| `Pending` for hours | a config bug: usually GPU resource name or `required` affinity |
| `ContainerCreating` | pulling the image, wait |
| `UnexpectedAdmissionError` | harmless node race; the retry allowance covers it |
| `Error` / `OOMKilled` | read `--previous` logs; this is when you open a fresh Claude session |

The training metrics themselves: W&B project `BNJetTagAug`, entity `kayamaguchi-uc-san-diego`.

## 5. Evaluate and bring results home

```bash
kubectl apply -f kai-bn14-roc-n8.yaml -n cms-ml          # one per N; CPU only
```

Training prints **validation AUC** (a monitor). The quotable number is **ROC-test AUC** on
the held-out split, n = 260,000, recomputed from the `.npz` that lands in
`bnjettag/roc-results/`. Known gap: the `kai-bn14-roc-code` ConfigMap has no build script
yet (see `docs/infrastructure/manual-round-runbook.md`, Phase 6).

## 6. Find idle or stuck jobs, and kill them

```bash
python3 nrp-lab/nrp_doctor.py status       # flags HUNG/IDLE pods (silent > 2 h) and FAILED jobs (< 72 h)
kubectl logs <pod> -n cms-ml --tail=20 --timestamps
kubectl exec <pod> -n cms-ml -- nvidia-smi # GPU-Util near 0% = idle
kubectl logs <pod> -n cms-ml > local/<pod>.log   # save evidence first

kubectl delete pod <pod> -n cms-ml         # hung pod: the Job retries with a fresh one
kubectl delete job <job> -n cms-ml         # stop a run for good (deletes its pods too)
./launch_r14.sh delete                     # tear down a whole round
```

Pod = retry, Job = stop. Log the incident in `cluster-inventory.md` with a Check line.

## 7. The GPU notebook (interactive, scratch only, nothing quotable)

```bash
nrp-lab/lab.sh up        # start the pod
nrp-lab/lab.sh status
nrp-lab/lab.sh sync      # push code/hgq2 onto it
nrp-lab/lab.sh url       # notebook link    (forward: port-forward)
nrp-lab/lab.sh shell
nrp-lab/lab.sh pull      # bring edited notebooks back
nrp-lab/lab.sh down      # ALWAYS when done: idle GPUs get reaped and annoy the group
```

## 8. Synthesis on mulder

From the MacBook over the UCSD-verified connection, not from the WSL home PC (`AGENTS.md`).

```bash
ssh mulder                                # on the Mac
df -h ~                                   # home is shared and runs near full
./mulder_csynth.sh <project>.tar.gz       # on mulder; output: <project>/csynth_report.json
```

Target VU13P (`xcvu13p-flga2577-2-e`), 2.5 ns clock. Nothing on mulder is backed up: copy
`csynth.xml` and the JSON home (`bnjettag/results/synthesis/runs/`) as soon as a run lands.
Use `tmux` on mulder for anything long, so a dropped ssh does not kill it.

## 9. Repo checks (cheap, run any time)

```bash
python3 tools/brief.py                          # what's going on: start of a session
python3 tools/prose_lint.py <file.md>           # writing that goes outward
python3 tools/plot_check.py <script.py>         # figure scripts
python3 tools/verify_check.py campaigns/<id>/VERIFY.md
python3 tools/claims.py --unlabeled             # numbers in docs missing metric/split labels
python3 tools/bib_check.py references.bib --online
python3 tools/index.py build                    # refresh INDEX.md
```

## 10. What still makes sense to hand to Claude

| yourself | Claude |
| --- | --- |
| launch, check, logs, delete, lab pod, ssh mulder | writing or changing generators and training code |
| reading W&B curves | recomputing numbers from `.npz` into `VERIFY.md` |
| deciding what goes in the record | review panels, red-team of a claim before it goes out |
| | diagnosing a crash: paste `kubectl logs ... --tail=50` into a fresh session |
