# BNJetTag Lab — CLAUDE.md

Binary `{−1,+1}`-weight transformer jet tagger for the CMS L1 trigger via hls4ml to FPGA.
`SYSTEM.md` is how research runs here. Rules that can be checks are checks; the rest is below.

## Loop and execution model (JFC)

`campaigns/<date>-<slug>/`: STUDY → PREFLIGHT → RUN → VERIFY → REPORT, one artifact per phase;
context moves only through artifacts and the append-only logs. The main session is the
**orchestrator**: it spawns agents from `.claude/agents/`, reads verdicts, commits, advances; it
never writes pipeline code, reads full arrays or makes figures. Per phase: EXECUTE (owner, plan
first) → `/review <id> <PHASE>` → CHECK (PASS / ITERATE via fixer / ESCALATE; a regression
trigger spawns investigator) → COMMIT → ADVANCE. Reviewers, plot-validator, arbiter run on opus.
Jev (`jev-lab` MCP) is advisory, never a verdict (`SYSTEM.md` §4). Kai is needed for
publication-ready claims and anything outward; inside an approved campaign its BRIEF governs; the rest runs under the
standing grant. Methodology: `docs/methodology/`; conventions: `docs/conventions/`.

## Rules that are not yet checks

- **Never invent a number.** Recompute from `.npz` or csynth JSON, or quote the source. Every
  number carries metric, split, n, status. Validation and ROC-test AUC never meet unlabelled.
  No comparison across N or input sets unless that is the point.
- **No gap without seeds and an interval.** Inside the spread is flat. Nothing from the lab pod
  or the local kernel is quotable.
- **Binary is the thesis; ternary a baseline.** Train on NRP, synthesize on `mulder`; the home
  PC (4060 Ti) runs exploration and the autopilot, never quotable numbers.
- **Log question-first**, newest on top: `experiment-log.md` (Question / Design / Result /
  Interpretation / Ops), `decisions.md`, `research-log.md` (date, URL), `cluster-inventory.md`
  (each ends with a **Check** line), all in `.claude/memory/`; pre-2026-09-08 archive frozen.
- **Taste goes on a contact sheet**; Kai's letter goes to `docs/style/CHOICES.md`, never re-asked.
- **Outward text** is plain, impersonal, passes `tools/prose_lint.py`, no assistant trace.
  Figures: `docs/style/bnjettag.mplstyle` + `tools/plot_check.py`; schematics TikZ.
- **Secrets.** Never print, paste or commit a key.

## Checks

- `.claude/hooks/pre-kubectl-lint.py` blocks `kubectl apply|create|replace -f` failing
  `nrp_doctor.py lint` (rule PACK: 40 % GPU floor). Launches go through `tools/run_handoff.py`.
- GPU products: `docs/infrastructure/gpu-selection-policy.md`. `tools/brief.py` at session start;
  `tools/index.py build|check` keeps this context under 150 lines.

Ignore `research/`, `publication*/`, `sessions/`, `__pycache__/`, `.claude/retired/`.

@RULES.md
@.claude/memory/project-context.md
@.claude/memory/index-head.md
