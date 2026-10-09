---
name: jev-lab
description: Use the BNJetTag Jev tools for failure triage, source ranking, finding classification, abstract screening, claim support, training-method consistency, or a bounded local work loop. Applies in the canonical BNJetTag lab; does not authorize training or replace scientific review.
---

# Jev lab

Use the `jev-lab` MCP server. If it is not loaded, the equivalent CLI is
`python3 tools/jev_lab.py call TOOL --input PATH` (JSON on stdin with `--input -`).
Check `jev_doctor` first when connection health is uncertain; `live=true` spends one
synthetic call. The server reads the existing private local TypeSafe key itself.

Choose the narrow tool that matches the task:

- `jev_triage_logs`: classify supplied failure excerpts without retrying jobs.
- `jev_rank_snippets`: rank explicit `rg` candidates before reading more files.
- `jev_triage_review`: classify findings; include `severity: "A"` when applicable.
- `jev_screen_papers`: score supplied abstracts across three independent dimensions.
- `jev_check_claims`: compare exact wording with its cited source passage.
- `jev_route_task`: recommend a workflow owner, preserving prescribed models.
- `jev_check_methods`: compare method text with the actual lab conventions.

Items have unique alphabetic IDs and either `text` or an explicit `path`, optionally
`start_line` and `end_line`. Claims also require `claim`. Keep source excerpts narrow.
The tools send those excerpts to TypeSafe; do not include secrets. Unknown/missing
answers stay visible. Probabilities are advisory; thresholds are heuristic, not a
lab calibration. Arithmetic and scientific metrics remain in the existing scripts.

For training consistency, build a declared JSON protocol following
`docs/infrastructure/jev-lab.md`. Run `lab_check_protocol`; snapshot it with
`lab_freeze_protocol`; compare proposed changes with the returned `baseline_path`.
A protocol snapshot binds declarations and methodology hashes. It is not a code
freeze, dataset validator, review verdict, scientific clearance, or launch grant.
Use the existing campaign freeze and immutable run handoff at their actual gate.

When the user requests a loop, call `lab_loop_start` with a specific goal, suitable
kind, and proportionate time/iteration/call budgets. Use `lab_loop_next`, perform
the directed local step, save new factual artifacts inside its directory, then
call `lab_loop_record`. Keep every failed approach and finding in those artifacts.

`plan` and `execute` accept `complete` or `blocked`; `review` accepts `pass`,
`iterate`, or `blocked`. A pass requires review and actual check-output evidence.
Use distinct versioned artifact paths for each iteration so earlier evidence is
preserved. Include `loop_id` on every Jev call belonging to that loop so its budget
is enforced. Continue while active; stop at any recorded terminal state. Do not
start a new loop merely to evade a stop or exhausted budget.

Loops are cooperative, foreground local work. They do not spawn models, invoke
arbitrary commands, or watch training jobs. `methods_audit`, `literature_review`,
and `evidence_review` write only loop artifacts. Ordinary local engineering obeys
the user's authorized scope. Research phases still require their owners and
mandatory review panel; local loop acceptance does not advance scientific phases.
No automatic launch, kill, relaunch, resume, active-campaign change, background
monitor, or publication is authorized by these tools. Chang K1's pending choice
and b5 readout cannot be inferred or marked cleared.
