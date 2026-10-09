---
title: Artifact checklists
status: current
date: 2026-09-26
---

# Appendix: artifact checklists

Each unchecked box is a Category A review finding unless the artifact says why it does not
apply.

## STUDY.md

- [ ] question and null, one sentence each, with the bearing on the thesis
- [ ] reference table (two or three prior results, each with its source file)
- [ ] arms table: every difference between arms stated; only the manipulated variable differs
- [ ] seeds: count, and what gap they resolve given the measured sd
- [ ] selection rule, on validation only, written before any run
- [ ] falsifier
- [ ] budget: arms × epochs, GPU-hours, arms per pod, wall time from a benchmark, W&B group
- [ ] conventions compliance table, one row per applicable convention
- [ ] decision labels `[D]`, constraints `[A]`, limitations `[L]`
- [ ] "where I am not sure"

## PREFLIGHT.md

- [ ] configs generated, generator named, none hand-edited
- [ ] CPU build for every config with parameter counts
- [ ] reload gate within 1e-7, TF32 off
- [ ] `PREFLIGHT_ALL_PASS` and the smoke run
- [ ] code sha and ConfigMap name
- [ ] `nrp_doctor lint` output for every manifest, warnings read
- [ ] packing benchmark: K per pod, measured utilisation

## RUN.md

- [ ] launch record path
- [ ] jobs, nodes, W&B group
- [ ] per-arm final state (epochs, checkpoint id)
- [ ] every resume and incident, with the `cluster-inventory.md` entry and its Check line

## VERIFY.md

- [ ] every number recomputed, command shown, source artifact named
- [ ] every number labelled: metric, split, n, status
- [ ] selection applied as pre-registered; selected checkpoint named
- [ ] seed sd and a paired interval on every gap
- [ ] per-class AUC; accuracy beside AUC
- [ ] eBOPs remeasured; binary layers verified binary
- [ ] hardware: parsed resources, II, latency, Fmax, C-sim fidelity; estimate vs implemented
- [ ] baseline vs record, with the pull
- [ ] `tools/verify_check.py` clean
- [ ] a verdict per STUDY claim

## REPORT.md

- [ ] interpretation limited to what VERIFY.md supports
- [ ] equations defining every metric used
- [ ] resolving power statement
- [ ] limitations with evidence of attempts
- [ ] every figure: style kit, provenance caption, `plot_check` clean, read as an image
- [ ] every number traceable to a VERIFY.md line
- [ ] change log if any phase regressed
- [ ] `prose_lint` clean; `pdf_check` clean if a PDF; `bib_check` clean if citations
- [ ] outward text marked "draft until the gate"

## Experiment log minimum

An entry per campaign at each phase transition, question-first, plus: failed approaches
with their mechanism; every parameter choice with its reason; every bug and its fix; every
launch with its job name pointing at RUN.md. An empty log at the end of a phase is a process
failure.
