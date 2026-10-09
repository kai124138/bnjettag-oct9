---
title: Principles
status: current
date: 2026-09-26
---

# 1. Scope and principles

This methodology says *what* each phase must produce, not *how*. Agents choose tools, write
code and make judgement calls within these constraints.

**Quality bar: publication-ready.** Every artifact must meet the standard "would Russell,
Javier, or a referee approve this?" Not "good enough to move on".

**Default posture: the strongest defensible result.** When three seeds are affordable, do
not report one. When a matched baseline exists, run it. When the spec is silent, prefer the
choice that makes the claim harder to attack. Downscoping is for genuine constraints
(quota, a broken toolchain), not for avoiding work, and it is recorded as a dated decision.

**Design principles**

- **Artifacts over memory.** Each phase produces a self-contained file. Later phases and
  reviewers read files, never conversation history.
- **Review at every gate.** STUDY, VERIFY and REPORT get a panel; PREFLIGHT and RUN get the
  scripts and one critical eye. Skipping review is a process failure.
- **Claim ≤ evidence.** A number carries metric, split, n and status or it does not exist.
  A gap carries seeds and an interval or it is flat. A projection is labelled a projection.
- **Conventions over encoded physics.** Operational knowledge lives in `docs/conventions/`
  and is consulted at STUDY, VERIFY and REPORT; agents update it when they learn something.
- **Checks over prose.** A rule that can be a script or a hook becomes one
  (`tools/`, `.claude/hooks/`). Prose rules are the ones that could not be.
- **The orchestrator does not do the work.** The main session spawns agents, reads
  summaries and verdicts, commits, and advances. It never writes pipeline code, never
  reads full arrays, never produces figures.
- **Binary is the thesis.** Ternary and W8A8 are baselines. Every campaign states how it
  bears on the thesis: binary weights map to LUT logic, not DSPs, at a measurable cost in
  tagging efficiency.
- **Nothing from scratch compute is quotable.** The lab pod, the laptop kernel, a screen
  under 100 epochs, and a single seed produce hypotheses, not results.
