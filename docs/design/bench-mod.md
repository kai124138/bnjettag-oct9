# Bench: research dashboard mod (design v2, 2026-10-10)

Status: design, not built. Sources: five research reports and one adversarial critique, kept in
the session scratchpad (`research-*.md`, `bench-critique.md`); v1 draft superseded.

## What it is for

A pane and a band inside Claude Code that show, without a model call, where the research
stands and what is waiting on Kai, and that keep three lab rules in view: never invent a number;
no gap without seeds and an interval; code is frozen once a run starts. It also lets Kai ask
"what is this?" mid-conversation and have the answer recorded.

Questions it must answer (recurring in Kai's typed prompts, keyword-grouped, counts not quoted
because the categories overlap): how are we doing; what needs my decision; how does this code or
concept work; why is the tagger stuck; which numbers can I take to a meeting.

## Architecture

The seam is the one the `runs` mod already uses: a Python script prints one JSON snapshot with a
documented schema; the mod only draws it and records session events.

| plane | source | refresh | cost |
| --- | --- | --- | --- |
| file | `tools/bench.py snapshot --json` (stdlib, read-only, offline) | session.start, turn.complete, 60 s while the pane is open | milliseconds; no cluster |
| cluster | existing `runs` mod + `tools/runs_snapshot.py` | only while the Runs pane is open | kubectl, may need OIDC login |
| session | mod hooks: agent.spawn, tool.call, turn.complete | events | none |

The band never calls kubectl; it reads STATE.json and NOTIFY.log, which the harness tick writes.
Model calls happen only on an Explain press, show their model, and run one agent per press.

## Snapshot schema (v0)

- `studies[]`: id, question, phase (from the artifact front matter), status, artifacts{phase:
  path, status}, verdicts[] (from `review/*` front matter), handoff (HANDOFF.md "where things
  stand"), frozen[] (BRIEF `frozen_files`, handoff `status.json`, code sha), gpu_h {spent, cap}
- `gates[]`: study, kind (program-unsigned | approval-void | escalate | hold | queued-for-kai),
  what it commits (GPU-h, jobs, files), source path
- `hypotheses[]`: study, id, statement, prediction, refutation (STUDY decision table), readout rows
  or "awaiting readout"
- `numbers[]`: claim, quantity, value, interval + method as stated, metric, split, n, seeds,
  status, source, code_sha, host, `lead_or_readout`, `in_record` (Kai's mark; absent today)
- `gaps[]`: what the lab cannot show yet, with the reason

Execution status and verification status are separate fields everywhere. A green "finished" is
never shown as "verified".

## v1: band + five tiles

0. **Surface test first.** This session runs in VS Code; the types declare a `vscode` surface
   (Box, Text, Button, Svg, Markdown, no Input), one secondary source says VS Code draws nothing.
   A 30-minute test decides: pane + band, or band + `/bench` command output.

1. **Band.** Active study and phase; count of items waiting on Kai; jobs running/failed from
   STATE.json; GPU-h spent against the cap. Two lines at most; must not hide Claude Code's own
   task or agent list.

2. **Waiting on Kai.** Every gate with what it commits and why it is blocked: unsigned
   PROGRAM.json, APPROVAL hash not matching the BRIEF authority block, ESCALATE verdicts, harness
   notices. Each row has a button that fills (never sends) the matching prompt, such as "review
   the approval for <study>". Nothing approves; `harness.py approve` needs a terminal by design.
   Accept: on the 2026-10-06 state it lists the open items with source paths and raises no false
   gate on the harness campaigns.

3. **Study track** (absorbs the map). For each open study: phases with artifact status, the
   verdict chain, regression tickets, HANDOFF summary, and where each artifact, config, manifest
   and frozen file lives, with a lock mark. A tool.call hook warns, not blocks, on Edit or Write to
   a frozen path; Bash edits bypass it, so enforcement stays with the harness hash checks.
   Accept: phase letters agree with `tools/index.py` on every campaign, disagreements listed.

4. **Hypothesis board.** For a pre-registered study (R1 now; any study with a decision table
   later): each hypothesis with its prediction, its refutation, the matching readout rows, and
   the count against the rule. Shows "awaiting readout" and no verdict until the readout exists;
   live scores before then carry "lead, not readout". This is the view for the open 350k
   collapse question.
   Accept: every label matches a hand reading of STUDY §6; nothing shown as a verdict before the
   readout job's output exists.

5. **Numbers with provenance.** Read-only. Each number opens a card: metric definition, split,
   n, seeds, interval and the method VERIFY.md states (the tile never computes its own), code
   sha, raw file, host, status, lead or readout, in the record or not. Lab-pod and home-PC values
   are not shown here. Matched-comparison guard: two numbers appear side by side only if N, input
   set, epochs, EBOPs budget, split and data hash match; otherwise the card says which differ.
   Accept: shows the pt-weighting AUCs with n and seeds exactly as VERIFY.md states them; refuses
   a difference across N or input set.

6. **Explain.** A button on a selection, a term or a card spawns one read-only tutor agent
   (sonnet, no edit tools); the answer appears in the pane and is recorded: how-to answers to the
   field guide "Asked before", concepts to its Glossary (RULES §6). A concept list from the
   physics survey (train/val/test roles, seed vs test-set error, working points, II and latency,
   STE, EBOPs, csynth vs post-route, emulation vs float, permutation invariance, IRC safety, ...)
   seeds the glossary.

## Deliberately not in v1

- **Number scanner over Claude's replies.** `turn.complete` sees only the final text, the only
  verify.json is GPU telemetry, and the closest existing mod reports about 50 % precision. A
  counter that is mostly wrong is worse than none. Revisit when tile 5 has physics rows, reusing
  the `verify_check.py` matcher.
- **Recompute button.** No metric registry exists; recompute today is a per-study script.
- **Agents tile.** Claude Code already lists agents; `agent.list` carries no model, tool or files.
  v2 could add only what is missing: lab role, study, artifact being written.
- **A separate interactive session from a button.** The API has no call that opens one; a
  background agent is what a mod can start. An Engineer action is a filled prompt that goes
  through the orchestrator, so the fan-out and review rules apply.
- **Generic quick-prompt deck.** Prompt buttons live on the tile whose state they act on.
- **`bench.toml` for other groups.** The schema is the seam; generality is claimed after a second
  group writes an adapter.

## Prerequisites outside the mod

These are lab work, not mod work, and each needs Kai:
1. Physics VERIFY rows in `verify.json` form (only GPU telemetry exists today).
2. An "entered the record by Kai" mark on a number (SYSTEM.md decision point).
3. Binary-collapse logging in the trainer (sign-flip rate per layer, fraction of latent weights
   at the clip, +1/−1 balance): a trainer change, so a new PREFLIGHT, future runs only.

## Build order

surface test → `bench.py snapshot` with tests on the existing campaigns → Study track → Waiting
on Kai → band → Numbers → Hypothesis board (needs the readout output) → Explain.
Each step: `claude plugin validate`, `claude plugin test`, and the acceptance line above.
