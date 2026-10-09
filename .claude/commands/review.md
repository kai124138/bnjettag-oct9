---
description: Run the review tier for a campaign phase (validators, plot-validator, panel, arbiter)
argument-hint: <campaign-id> <PHASE>
---

Review phase `$2` of campaign `campaigns/$1/` following `docs/methodology/06-review.md` §6.2.

1. Run the scripts for the tier and save their output to `campaigns/$1/review/$2_validators_v<n>.txt`:
   PREFLIGHT `nrp-lab/nrp_doctor.py lint` on each manifest; VERIFY `tools/verify_check.py`;
   REPORT `tools/prose_lint.py`, `tools/pdf_check.py`, `tools/bib_check.py`.
2. VERIFY and REPORT only: spawn `plot-validator`.
3. Tier:
   - STUDY, VERIFY, REPORT: spawn `physics-reviewer`, `critical-reviewer` and
     `constructive-reviewer` in parallel, then `arbiter` with every review and the validator output.
   - PREFLIGHT, RUN: spawn `critical-reviewer` alone; its verdict goes to `.claude/memory/review-reports.md`.
4. Reviewers use Jev as their definitions say (advisory only). The arbiter may use
   `jev_triage_review` as a second opinion on finding categories.
5. Report the verdict. On ITERATE, spawn `fixer` with the arbiter file and run the review again
   (caps in §6.5). On ESCALATE, stop and tell Kai.

Use `<n>` = one more than the highest existing version for that phase. State the agent count and
models before spawning (RULES §7).
