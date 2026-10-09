---
title: Methodology
status: current
date: 2026-09-26
---

# Methodology

How a BNJetTag campaign is run, reviewed and gated. Adapted on 2026-09-26 from the JFC
framework (Moreno et al., arXiv:2603.20179; github.com/jfc-mit/jfc, `src/methodology`),
which was written for a collider analysis. What was kept: phases that each leave one
artifact, context passed only through artifacts and an append-only log, a review panel of
independent fresh-context reviewers with an arbiter, programmatic validators whose red flags
cannot be downgraded, phase regression, evidence-based review, and one human gate. What was
changed: five phases instead of seven, no blinding (a classifier study has no signal region),
the human gate at "number enters the record / anything goes outward", validators as scripts
under `tools/`, and conventions written for jet tagging, quantization and FPGA synthesis.

| file | what it answers |
| --- | --- |
| `01-principles.md` | the quality bar and the design principles |
| `03-phases.md` | what each of the five phases must produce, and its gate |
| `06-review.md` | classification, review tiers, reviewer framing, regression triggers, the human gate |
| `appendix-checklist.md` | per-artifact checklists and the experiment-log minimum |
| `templates/` | skeletons for STUDY, PREFLIGHT, RUN, VERIFY, REPORT |
| `../conventions/` | what an experienced analyst knows: metrics, quantization and cost, synthesis, figures |

Reading guide. Starting a campaign: `03-phases.md` and the STUDY template. Spawning a
reviewer: `06-review.md` and the agent's definition in `.claude/agents/`. Writing the
report: `appendix-checklist.md`. The orchestrator loop itself is in `CLAUDE.md`.
