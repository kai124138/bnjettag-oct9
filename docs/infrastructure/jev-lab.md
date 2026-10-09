# Jev tools and bounded lab loops

The canonical implementation is `tools/jev/`, exposed through
`python3 tools/jev_lab.py`. Claude Code discovers the project `.mcp.json` and
`.claude/skills/jev-lab/`; Codex discovers `.codex/config.toml` and
`.agents/skills/jev-lab/`. The latter skill directory links to the same instructions.
Run both clients in `/home/kaimoe/lab/bnjettag`. Restart existing sessions after
configuration changes. Claude Code also has a local registration for this project,
created with its supported `claude mcp add --scope local` command. The shared
definition is kept in `.mcp.json`; no credential is in either registration.
This setup creates no remote service, notification subscription, or background task.

## Runtime and connectivity

The Python runtime is separate from training environments:

```sh
uv venv local/jev-runtime
uv pip install --python local/jev-runtime/bin/python -r tools/jev/requirements.txt
python3 tools/jev_lab.py doctor
python3 tools/jev_lab.py doctor --live
python3 tools/jev_lab.py call jev_triage_logs --input tools/jev/examples/triage.json
```

The key comes from `TYPESAFE_API_KEY` or the existing private `~/.typesafe.env`.
The loader parses only the key assignment; it never executes that file or prints
its contents. No key is written into MCP configuration. Calls use the official
TypeSafe endpoint and SDK with a timeout and no automatic retry. `JEV_MODEL` can
pin a model version. See the [TypeSafe API](https://docs.typesafe.ai/api) and
[coding-agent guide](https://docs.typesafe.ai/introduction/coding-agents).

Seven advisory tools cover logs, snippets, findings, abstracts, claims, workflow
routing, and training method text. `jev_doctor` checks connection health. Every
item uses a stable unique ID and `text`, or an explicit lab `path` with optional
line bounds. `jev_check_claims` also needs `claim`; `jev_rank_snippets` needs `query`.
Sources are not crawled. Credential, runtime, and historical archive paths are
excluded, including symlinks escaping the canonical root.

Rubrics and thresholds live together in `tools/jev/catalog.json`. Thresholds are
heuristics, not measured calibration on lab tasks. Preserve unknown answers and
inspect evidence. Category A findings remain mandatory review. Audit files under
`local/jev-audit/` contain question definitions, hashes, answers, model, actual
token usage, and latency; raw state and credentials are not saved. These are
engineering observations, not quotable physics results. The credential detector
is a workflow safeguard, not a universal secret detector.

## Method consistency

`jev_check_methods` checks narrow semantic rules against the actual authoritative
documents. It does not prove correctness. Pair it with the deterministic tools:

```sh
python3 tools/jev_lab.py call lab_check_protocol --input local/my-protocol-check.json
python3 tools/jev_lab.py call lab_freeze_protocol --input local/my-protocol-check.json
```

The first input has `{"path": "local/my-training-protocol.json"}`. To compare a
candidate with a frozen method, add `baseline_path` using the snapshot returned
by `lab_freeze_protocol`. Snapshots are content-addressed under
`local/jev-protocols/`. They include the declared protocol and hashes of the
methodology documents and Jev rubric catalog, plus actual hashes of any explicitly referenced arm
`config_path` files. Editing a config at the same path therefore appears as drift.
The validator checks dataset identity declarations, split
separation, validation-only selection, cost/checkpoint alignment, metric labels,
paired seeds for claims, declared arm differences, and protocol drift.

Required protocol fields:

- `version: 1`, `purpose`, and `scope: screen | claim`.
- `dataset`: `id`, actual `identity_sha256`, and distinct `train_split`,
  `validation_split`, and `test_split` definitions.
- `inputs`: positive `n_constituents` and the `features` list.
- `arms`: unique `name`, arm `group`, integer `seed`, `quantization`, full
  `schedule`, and `changed_factors` field paths relative to the first arm.
  An arm may explicitly override `inputs`; differences must be declared.
  Optional `config_path` binds the current bytes of that text config into snapshots.
- `schedule`: `epochs`, `batch_size`, `optimizer`, and `learning_rate`.
- `selection`: `split: validation`, `metric`, `rule`, `cost_checkpoint: selected`.
- `metrics`: each has `name`, `split`, actual positive `n`, and `status`.
- Explicit `stop_rules` and durable `outputs` lists.
- For claims, `interval_method`, at least three paired seeds per group, or eight
  if declared `expected_auc_gap` is below the existing convention's threshold.

`tools/jev/examples/protocol-screen.json` is a synthetic engineering fixture.
Its dataset hash and sizes are fictional and must never become a run brief.
Missing real facts block the structural check; do not fill them with guesses.

This snapshot freezes declarations only. It cannot verify actual training config
semantics, dataset bytes, metrics, or correspondence with executed code. Training
still uses the existing campaign freeze, handoff validator, scientific review,
and current launch authorization. `launch_authorized` is always false in this
tool's results because it supplies no launch grant. Chang option (c) is chosen; K1 remains triggered and does not clear
production (decisions.md, 2026-10-01; `AGENTS.md`).

## Shared loop harness

`lab_loop_start` creates a local cooperative loop, shared by both clients. Its
stages are plan, execute, and review. Agents perform the work in their existing
session; these tools never run shell commands, start another model, or poll jobs.

```json
{
  "goal": "Audit a proposed training method against the current conventions",
  "kind": "methods_audit",
  "max_iterations": 3,
  "max_seconds": 1800,
  "max_jev_calls": 12
}
```

Call `lab_loop_next`, perform the requested step, save versioned artifacts under
the returned directory, and call `lab_loop_record`. Plan and execute accept
`complete` or `blocked`; review accepts `pass`, `iterate`, or `blocked`. Pass needs
at least review and check-output evidence. Earlier evidence must still match its
recorded content. Pass records the agent's local acceptance, not an independent
scientific certification. The planned acceptance criteria and required scientific
reviewers remain the agent's responsibility.

Every Jev call within a loop must carry its `loop_id`. Call attempts reserve
budget before network access, including failed attempts. A call without a loop
ID is outside that loop's budget; this is a cooperative workflow guard, not a
global API spending limit. Stops include elapsed time, call/iteration limits,
changed methodology or rubric hashes, repeated unchanged execution evidence, and a recorded
blocker. No stopped or blocked loop is automatically resumed. A new loop is a new
record and requires a new authorized task, not an excuse to evade stop rules.

Events are appended as individually hashed JSON records with a hash chain and a
local file lock. State is reconstructed from the chain. `lab_loop_status` reports
the latest event hash; provide it as `expected_event_sha256` to reject stale
writes. Fresh sessions can continue an active loop with its exact ID. The record
is not signed, and a person who can replace all its files can replace its history.

These loops handle local engineering, methods audits, literature review, and
evidence review. They do not advance the scientific STUDY/PREFLIGHT/RUN/VERIFY/
REPORT pipeline, start training, change active campaign inputs, publish, kill,
resume, relaunch, or create monitors. Mandatory owner/panel reviews and action-time
gates remain in force. An agent's own permissions and the existing hooks apply to
its actual commands; this state machine is not OS or cluster admission policy.

## Prompt for Claude Code or Codex

Use `/jev-lab` in Claude Code or `$jev-lab` in Codex, followed by:

> Run a bounded methods_audit loop in this lab: at most 3 iterations, 30 minutes,
> and 12 Jev calls. Create a deliberately flawed synthetic training-method note
> that selects checkpoints using ROC-test AUC, mixes final-epoch cost with
> best-checkpoint AUC, and claims a gap from one seed without an interval. Label
> it synthetic. Use jev_check_methods to audit it, jev_rank_snippets to locate the
> relevant convention passages, and jev_check_claims to check the note's claims
> against those passages. Keep unknowns visible. Draft a corrected method note
> and recheck it. Save versioned plan, execution, review, and check evidence in
> the loop directory, attach loop_id to every Jev call, and record every stage.
> Stop on the harness bounds. Report actual tool use, findings, and remaining
> uncertainty. This is a local document audit; do not alter campaign inputs or
> start training.
