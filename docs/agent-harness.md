---
title: Agent harness — current setup and target operating model
status: draft
date: 2026-10-08
---

# Agent harness

How the BNJetTag lab runs research with agents today, the operating model it is moving to, and
the open gaps between the two. Written 2026-10-08 from a working session with Kai. Every file
named here is a link, so a section can be corrected at its source.

**Status labels used below.** **Current**: exists and runs today, verified in the repository.
**Agreed**: Kai accepted it in the 2026-10-08 session. **Proposed**: a recommendation not yet
decided. **Open**: needs a decision. Token figures are estimates, not measurements.

**This document does not change any rule.** [`RULES.md`](../RULES.md), [`CLAUDE.md`](../CLAUDE.md)
and [`SYSTEM.md`](../SYSTEM.md) govern until they are rewritten in stages (§7). Existing holds
on named campaigns (pilot program K3, the r3 PVC rename) stay until Kai revises them.

---

## 1. The meta-rule documents

| # | File | What it controls |
| --- | --- | --- |
| 1 | [`CLAUDE.md`](../CLAUDE.md) | Loaded into every session: loop, prose rules, checks |
| 2 | [`RULES.md`](../RULES.md) | Plan block, report shape, act-or-ask table, launch-and-leave, code freeze |
| 3 | [`SYSTEM.md`](../SYSTEM.md) | The JFC design and why; §7 open decisions |
| 4 | [`AGENTS.md`](../AGENTS.md) | Machine and access rules, run provenance; read by Codex |
| 5 | [`docs/methodology/`](methodology/) | Principles, phase protocol, review protocol, templates |
| 6 | [`docs/conventions/`](conventions/) | Metric, quantization, synthesis and figure rules |
| 7 | [`.claude/agents/`](../.claude/agents/) | The 13 agent definitions |
| 8 | [`.claude/settings.json`](../.claude/settings.json), [`.claude/hooks/pre-kubectl-lint.py`](../.claude/hooks/pre-kubectl-lint.py) | Session brief hook, kubectl lint hook |
| 9 | [`.claude/memory/decisions.md`](../.claude/memory/decisions.md) | Every rule-changing decision |
| 10 | [`docs/PILOT_PROGRAM.md`](PILOT_PROGRAM.md) | The current research plan |

Location-bound files: `CLAUDE.md` (root or `.claude/`), `AGENTS.md` (root, for Codex),
everything under `.claude/`. All other meta documents can move; Kai chose to keep them where
they are (Agreed, 2026-10-08).

---

## 2. Current setup

### 2.1 Pipeline and campaign flow (Current)

```
STUDY.md → PREFLIGHT.md → run_handoff.py → NRP Job (cms-ml) → RUN.md
   → .npz / W&B → VERIFY.md → /review panel → REPORT.md → Kai gate → record
Pipeline: bnhgq2 train → convert_final.py → mulder_csynth.sh → parse_csynth.py
```

Pipeline code: [`bnjettag/code/hgq2/`](../bnjettag/code/hgq2/). Campaigns:
[`campaigns/`](../campaigns/).

### 2.2 Agents and checks (Current)

```
Kai ──► main session (orchestrator: spawns agents, reads verdicts, never writes pipeline code)
          │
          ├─► phase owners: experiment-designer → ml-engineer / cluster-ops → results-analyst → paper-writer
          │      writes:       STUDY.md          PREFLIGHT.md, RUN.md      VERIFY.md         REPORT.md
          │
          ├─► /review panel after each phase: physics, critical, constructive reviewers → arbiter
          │      verdict: PASS / ITERATE (fixer) / ESCALATE (Kai)
          │
          └─► checks: kubectl lint hook, run_handoff.py, plot/prose/claims validators
                         │
                         ▼
               NRP Kubernetes Jobs (cms-ml) ──► results on PVC / W&B
```

| Role | Agent file | Model (frontmatter) |
| --- | --- | --- |
| STUDY owner | [`experiment-designer.md`](../.claude/agents/experiment-designer.md) | opus |
| Code, configs, build half of PREFLIGHT | [`ml-engineer.md`](../.claude/agents/ml-engineer.md) | opus |
| Launch half of PREFLIGHT, RUN, incidents | [`cluster-ops.md`](../.claude/agents/cluster-ops.md) | sonnet |
| VERIFY owner | [`results-analyst.md`](../.claude/agents/results-analyst.md) | opus |
| REPORT, outward text | [`paper-writer.md`](../.claude/agents/paper-writer.md) | opus |
| Literature, physics questions | [`physics-researcher.md`](../.claude/agents/physics-researcher.md) | sonnet |
| Review panel | [`physics-reviewer.md`](../.claude/agents/physics-reviewer.md), [`critical-reviewer.md`](../.claude/agents/critical-reviewer.md), [`constructive-reviewer.md`](../.claude/agents/constructive-reviewer.md), [`arbiter.md`](../.claude/agents/arbiter.md), [`plot-validator.md`](../.claude/agents/plot-validator.md) | opus |
| Helpers | [`investigator.md`](../.claude/agents/investigator.md), [`fixer.md`](../.claude/agents/fixer.md) | sonnet |

Commands: only [`/review`](../.claude/commands/review.md) exists. Skills:
[`jev-lab`](../.claude/skills/jev-lab/), [`nrp-nautilus`](../.claude/skills/nrp-nautilus/),
[`nrp-training-run`](../.claude/skills/nrp-training-run/).

### 2.3 Jev (Current)

Jev is an outside model served by TypeSafe (MCP server `jev-lab`, code [`tools/jev/`](../tools/jev/),
runbook [`docs/infrastructure/jev-lab.md`](infrastructure/jev-lab.md)). It returns typed second
opinions and never a verdict. Its thresholds are "heuristics, not measured calibration"
([`catalog.json`](../tools/jev/catalog.json)). `jev_check_claims` judges only whether a source
passage supports a claim's wording (`supported` / `overstated` / `absent` / `unclear`) and is told
"Do not calculate numbers". Wired in today: `jev_triage_logs` (cluster-ops, investigator),
`jev_check_claims` (critical-reviewer, results-analyst, paper-writer, fixer), protocol and method
checks at STUDY and PREFLIGHT.

### 2.4 Where approvals come from today (Current)

1. **Lab rules ask on purpose.** [`RULES.md`](../RULES.md) §3, §5; K3 in `decisions.md`.
2. **The Claude Code permission check**, separate from lab rules. It denied the PROGRAM.json edit
   (pilot JOURNAL 2026-10-05 15:48), a read-only grep (19:32) and the PVC rename `--apply`
   (2026-10-08 03:51).
3. **Missing automation.** The autopilot authorized 2026-10-05 (`tools/autopilot.py`) was never
   built; no cron entry exists.

Most re-approvals in the pilot program came from run failures (RSS gate stopped 23 of 24 R1 arms;
8 of 23 r2 arms failed in three modes), each turning into a new PREFLIGHT.

### 2.5 RULES.md, section by section (Current)

| § | What it says | Protects against | Problem found 2026-10-08 |
| --- | --- | --- | --- |
| 1 | Five-line plan block before multi-step work | Big, outward or expensive actions unseen | none |
| 2 | Done / Changed / Skipped / Needs you | Buried results, silent skips | "commit shas" with no repo |
| 3 | Act-or-ask table; signed PROGRAM.json counts as approval | Irreversible or public actions, spend creep | PROGRAM.json `signed_at` is null |
| 4 | Launch and leave; no session watches, except the autopilot | Sessions idling on runs | autopilot does not exist |
| 5 | Code frozen once a run starts; a fix is a new PREFLIGHT | Mixed code inside one comparison | assumes commits |
| 6 | How-to answers go in the field guide | Repeated how-to questions | none |
| 7 | Token discipline | Waste, bloated main context | none |

---

## 3. Target operating model (Agreed, 2026-10-08)

Kai's statement, condensed:

- Kai sets the research direction and approves campaign-level objectives, constraints and
  resource limits. The agent recommends the experimental design and owns implementation details.
- For a new direction the agent investigates papers and implementations, explains rationale and
  limitations, and drafts a concise campaign brief with proposed settings and limits.
- Inside an approved campaign the agent researches, writes and tests code, launches, monitors,
  diagnoses, repairs, relaunches, evaluates and selects the next experiment, without asking again
  at each phase. "Run this configuration" uses the existing campaign settings.
- A deterministic failure stops blind retries, not the assignment: investigate, fix, test,
  relaunch within repair and resource limits. Preserve evidence, version changes, never change the
  question, evaluation rules or experimental meaning to make a run pass; when a fix affects
  comparability, rerun the affected comparisons.
- After a pilot the agent chooses PROCEED, INVESTIGATE FURTHER or STOP THIS BRANCH. Inconclusive is
  inconclusive. A passing smoke test is not evidence for the idea.
- Notifications explain evidence, action, remaining budget and uncertainty, and never pause
  authorized work. Ask only when a decision exceeds scope, needs more resources or access, changes
  a reserved setting, or cannot be resolved within limits.
- Verified measurements stay separate from interpretation. Jev is an extra check, not a substitute
  for numerical or implementation verification. Negative results are preserved.
- Claude Code or Codex can operate the same workflow from shared saved state; neither supervises
  the other.
- Ordinary software does idle monitoring; agents are invoked for reasoning or repair. Retries,
  repairs, model usage and compute are bounded. No dummy requests to keep a cache warm.
- Context lives on disk: a concise campaign handoff and current state, not a long chat history.
- Reports focus on theory: papers, hypothesis, how the mathematics maps to the implementation,
  what was tested, what was learned, why the next action.

### 3.1 Layered judgment (Agreed)

```
results (.npz / csynth JSON)
   │
   ▼  1. recompute (code)       → catches a wrong number
VERIFY.md
   │
   ▼  2. Jev check_claims       → catches wording that overstates the numbers
REPORT / decision
   │
   ▼  3. Kai, publication-ready claims only (§6) → catches "true but not what we should claim"
```

### 3.2 The loop (shape Agreed, details §4)

```
Kai ──approves──► campaigns/<id>/BRIEF.md   (goal, hard caps, reserved settings; agent drafts it)
                      │
                      ▼  main reference
             orchestrator (Claude Code or Codex) ──► agents ──► launch jobs itself
                      ▲                              │
              watcher wakes it on events             ▼
                      │                         results / failures
                      └──── layered judgment ◄───────┘
                                │
                                ▼
                 PROCEED / INVESTIGATE / STOP / repair+relaunch → notify Kai (non-blocking)
```

### 3.3 Bounded autonomy

The agent acts alone inside a box that code enforces: a **charter** (the brief), **enforcement**
(scripts that refuse out-of-scope launches and spend whatever the model decides), a **wake-up**
(the watcher), and a **judge** (deterministic checks first, model opinions after).

---

## 4. Proposed implementation (Proposed; routine defaults chosen by the agent)

### 4.1 Campaign state on disk

| File | Written by | Purpose |
| --- | --- | --- |
| `BRIEF.md` | agent drafts, Kai approves | Question, hypothesis, objectives, hard caps (GPU-h, model tokens, repair attempts), reserved settings. Approval is not stored here: Kai's approval is `APPROVAL.json`, bound to this block's hash |
| `STATE.json` | watcher and agents | Machine state: phase, jobs, spend so far, attempts per failure class, lock holder |
| `HANDOFF.md` | each agent session at exit | Under 60 lines: where things stand, last decision and why, next action, open uncertainties. The first file any Claude or Codex session reads |
| `STUDY.md` … `REPORT.md` | as today | Phase artifacts |
| `NOTIFY.log` | watcher and agents | Every notification sent, append-only |

Concurrency default: one writer at a time through a lock entry in `STATE.json` with an expiry,
taken by whichever tool (Claude Code or Codex) is working. Work is split by lock, not by tool.

### 4.2 Watcher (ordinary software)

A Python script on cron (home PC): `kubectl get jobs/pods` for the campaign's labels, compares
with `STATE.json`, writes the new state, sends a notification on change, and on a failure or
completion starts one headless agent session (`claude -p …` or `codex exec …`, chosen in
`BRIEF.md`) pointed at `HANDOFF.md`. It never edits code or launches jobs itself. Zero model tokens
while nothing changes. Note: `codex` is not on this machine's PATH (checked 2026-10-08).

### 4.3 Failure handling defaults

| Failure class | Example (pilot r2) | Default action |
| --- | --- | --- |
| Infrastructure | pod lost at init; node disruption | relaunch from latest checkpoint, same bundle, at most 2 per arm |
| Deadline | exit 124 at 11,581 s | diagnose speed vs deadline; relaunch with a corrected deadline in a new versioned bundle |
| Deterministic | exit 76, "History exists without a committed checkpoint" on every attempt | no retry; investigate, fix, test on CPU, new bundle, relaunch; at most 3 repair attempts per failure class; affected comparisons rerun |
| Out of bounds | budget or attempt cap reached | stop the branch, notify, ask |

Kubernetes `podFailurePolicy` can enforce the infrastructure vs deterministic split in the
manifest (Ignore on `DisruptionTarget`, FailJob on a reserved exit code); NRP and lint support
are unverified.

### 4.4 Review by consequence

One critical-reviewer at PREFLIGHT (before code freezes), the full panel only at VERIFY and REPORT
for quotable claims, at most 2 ITERATE rounds per phase. After the cap the agent decides with
written reasoning or marks the item inconclusive; Kai is asked only if scope changes.

### 4.5 Token estimates

Anchors: pilot STUDY ≈ 9.6k tokens, PREFLIGHT ≈ 19k, 17 review files ≈ 63k (bytes / 4); the three
agents run in this session used 59k, 71k and 111k tokens.

**Today's loop, one campaign like the pilot program**

| Step | What runs | Estimate | Why |
| --- | --- | --- | --- |
| STUDY | designer (opus) | 100–150k | reads methodology and conventions (~15k) plus prior campaigns |
| Review, per round | 3 reviewers + arbiter (opus) | 300–500k | each reads STUDY + PREFLIGHT (~30k) + methodology; the pilot ran ~5 rounds |
| PREFLIGHT | ml-engineer (opus) | 150–400k | builds, tests, re-reads a 19k PREFLIGHT |
| Launch | cluster-ops (sonnet) | 50–100k | |
| Each incident | cluster-ops + investigator + fixer + review | 300–500k | the pilot had 2 plus relaunch prep |
| Watching by a polling session | every 10 min | ~1M per 6 h round | each wake-up re-reads ~30k of context |
| VERIFY + REPORT | results-analyst, paper-writer + panel | 300–600k | |
| **Total** | | **≈ 3–5M** | review ≈ 40 %, incidents ≈ 25 % |

**Cheapest version of the loop**

```
Kai ──► BRIEF.md (~1k tokens: goal, hard caps, reserved settings)
          │
          ▼
  [script] cap check + lint + run_handoff          0 tokens   (code enforces the box)
          │
          ▼
  NRP Jobs ──► [script] watcher on cron            0 tokens   (kubectl get, STATE.json, notify)
          │            │
          │            └─ only on a state change ──► wakes Claude or Codex (headless)   ~50–100k per event
          ▼
  results ──► 1. recompute scripts                 0 tokens
              2. Jev check_claims                  ~1–2k (TypeSafe API, not the Claude quota)
              3. one opus reviewer / arbiter       ~100–200k, only for quotable claims
```

| Saving | How | Estimated cut |
| --- | --- | --- |
| Event wake-up | watcher script; an agent starts only on a state change | ~1M → ~0.1–0.3M per round |
| Code before models | lint, cap check, recompute, `verify_check.py` first | fewer wasted review rounds |
| Review by consequence | §4.4 | ~1.5–2.5M → ~0.4–0.8M |
| Short handoff | agents read `HANDOFF.md` + `BRIEF.md` + needed sections, not all of SYSTEM.md, methodology and PREFLIGHT | ~20–40 % per agent |
| Model tiers | haiku or sonnet for lookups, triage, edits; opus for design, critical review, arbiter | cost per token |

Rough total ≈ 1–2M tokens per campaign. The largest uncertainty is the incident count.

### 4.6 Claude Code and Codex

The lab already has [`AGENTS.md`](../AGENTS.md), `.codex/config.toml` and the jev-lab skill
linked for Codex. Codex Max plan limits are not verified here; treat it as a second budget.
Default: either tool can hold the lock and run any phase; cross-model review (Codex reviewing
Claude's code or the reverse) is available for consequential code changes. Both tools follow
`AGENTS.md`, so rules shared by both belong there and `CLAUDE.md` should import or point to it.

### 4.7 Earlier gate options (superseded by §3, kept for reference)

| Change | What it buys | Cost or risk |
| --- | --- | --- |
| A. Pre-sign failure responses in PROGRAM.json | infrastructure failures restart without Kai | failure types must be classified in advance |
| B. Loosen the §5 code freeze | faster fixes | mixed code within a round breaks comparisons |
| C. Narrow Claude Code allow rules | removes classifier blocks | broad patterns let through PVC mutations |
| D. Build the autopilot | signed steps run unattended | unattended cluster writes, credential lifetime |
| E. Fix run reliability at the source | fewer failures, fewer re-approvals | each fix is a new PREFLIGHT |

| # | RULES.md proposal | Status after §3 |
| --- | --- | --- |
| P1 | Read-only watcher with notifications replacing the §4 autopilot sentence | kept as §4.2 (watcher wakes an agent) |
| P2 | One automatic relaunch for infrastructure failures; others stop | replaced by §4.3 (deterministic failures go to repair) |
| P3 | Exploration mode vs quotable mode | kept, Proposed |
| P4 | Review cap of 2 rounds, then escalate to Kai | replaced by §4.4 (agent decides after the cap) |
| P5 | Define "signed" | kept as the `BRIEF.md` approval line |
| P6 | Git-neutral code identity in §2 and §5 | waits on the git decision (§6) |

---

## 5. Mismatches between the proposal and the operating model

| # | Mismatch | Resolution in this draft |
| --- | --- | --- |
| 1 | P2 stopped and reported deterministic failures | §4.3 repair loop with attempt caps |
| 2 | P4 escalated to Kai after the review cap | §4.4 agent decides; Kai only on scope change |
| 3 | `metrics.md` written by Kai | `BRIEF.md` drafted by the agent, approved by Kai |
| 4 | Codex/Claude split by ownership of directories | split by lock; either tool runs any phase |
| 5 | Wake-up named only headless Claude | watcher starts whichever tool `BRIEF.md` names |
| 6 | No on-disk handoff | `HANDOFF.md` and `STATE.json` per campaign |
| 7 | RULES §2 report shape is operational | add a theory report section (papers, hypothesis, math → code, tests, lessons, next action) |
| 8 | Model usage was estimated, not bounded | token and invocation caps in `BRIEF.md`, counted by the watcher |
| 9 | RULES §3, §5 and CLAUDE.md still require Kai at each step | staged rewrite, §7 |
| 10 | The Claude Code permission check and Codex approval policy still block unattended cluster and PVC actions | Open: needs Kai's settings decision (§6) |

---

## 6. Decisions

**Decided 2026-10-08** ([`decisions.md`](../.claude/memory/decisions.md)):

- **Reserved for Kai:** publication-ready scientific claims, public releases, external messages
  sent on his behalf. **Automatic:** internal measurement logging, preserving verified results
  with provenance, notifications through an approved channel. Layer 3 of §3.1 is therefore Kai
  only for publication-ready claims.
- A reviewer disagreement may be resolved with documented reasoning; a failed numerical or
  authorization check cannot be waived.

**Open:**

- **Notification channel** for the watcher (push, email, Slack, W&B alerts).
- **Unattended permissions.** Which allow rules headless Claude Code and Codex get for kubectl,
  `run_handoff.py` and PVC operations.
- **Git.** Start a root repository, recover history, or keep content-hash bundles only.
- From the 2026-10-08 audit: style file `docs/style/bnjettag.mplstyle` (missing; `plot_check.py`
  rule B cannot pass), the 10 missing slash commands, missing skills (verify-roc, human-repo,
  vitis-mulder), the stale `nrp-training-run` skill (says `kubectl apply`, the hook requires
  `run_handoff.py`), `.claude/memory/project-context.md` (missing; an archive copy exists),
  SYSTEM.md §7 stale items, README `setup.sh`, the `tools/index.py` open-campaign filter that hides
  the pilot program from the session brief.

---

## 7. Staged rollout

### 7.1 State on 2026-10-08 (local only; no live campaign touched)

Code: [`tools/harness.py`](../tools/harness.py). Tests: [`tests/test_harness.py`](../tests/test_harness.py)
(21 tests). Test support: [`tests/support/`](../tests/support/) (local kubectl substitute,
demo task, simulated agent, demo driver). Fixtures: [`tests/fixtures/harness/`](../tests/fixtures/harness/).

**Records.** `observe()` reads a kubectl List of Jobs and Pods and produces one observation per
Job index: status from `completedIndexes` / `failedIndexes` / Job conditions, per-attempt exit code
from the pod's terminated container state, DisruptionTarget from pod conditions, arm from the
`bnjettag.io/arm` annotation (None when absent). Missing pod records leave exit code and GPU time
as None and classify as `unknown`. The harness acts only on indexes Kubernetes has finished with;
an index with failed pods that Kubernetes is still retrying under its pod failure policy is
recorded as `kubernetes_retrying` and gets no harness action.

**Fixtures.** Captured (sanitized copies of saved kubectl records; each file names its source and
the source's sha256): engram 2026-09-18 Indexed Job with policy and FailedIndexes; batch0917
MaxFailedIndexesExceeded with no pod records; batch0918 Complete; confirm-replay 2026-10-01
non-indexed BackoffLimitExceeded. Constructed (edited copies, marked in the tests): an index still
being retried, and node disruptions. No captured record of a disruption exists.

**Submission.** `submit()` requires an `APPROVAL.json` whose `brief_sha256` matches the current
limits block, computes a worst-case GPU-hour bound from the Job (GPUs × attempts × pod
`activeDeadlineSeconds`, or Job deadline × parallelism; a Job with neither is refused), refuses if
committed use plus the bound exceeds `gpu_h_max`, reserves the bound, and calls
`tools/run_handoff.py launch --submit` with the brief's kubectl. Committed use = measured GPU time
of finished Jobs + max(reservation, running estimate) for unfinished ones. Limits of the claim:
only launches made through `submit()` are checked (direct `run_handoff.py` use is not blocked);
pods replaced after disruptions the policy ignores are outside the bound; Jobs not submitted
through the harness are not in the committed total.

**Approval.** `harness.py approve` needs a terminal and the typed campaign id, then writes
`APPROVAL.json` bound to the limits block; any edit to the block invalidates it. This prevents an
agent from approving by editing the brief and prevents stale approvals. It does not prevent a
process running as Kai's user from writing `APPROVAL.json` directly; there is no signature.

**Concurrency and duplicates.** Every STATE.json read-modify-write holds an exclusive `flock` on
`.state.lock` (same machine only). Monitor events have deterministic IDs and are processed once.
Tasks are claimed with a lease; each finished step is saved, so a resumed process continues after
the last saved step. A process that dies during the agent run leaves `agent_started`; the next
holder restores the workspace snapshot and reruns the agent (a second invocation, counted). A
repeated submission of the same Job is skipped by the harness and by run_handoff's cluster lookup;
a crash between submission intent and creation is reported by run_handoff as ambiguous and the
reservation is kept.

**Agents.** Runners: `simulated` (scripted fix, no model), `claude` (`claude -p`, edit permission
limited to Read/Edit/Glob/Grep in the workspace), `codex` (`codex exec --sandbox workspace-write`;
flags unverified). Edits outside `repair_paths` are refused and the workspace restored. A repair is
relaunched only after `repair_test_command` exits 0, as a new handoff with a new Job name.

**Demonstrated.** Local recovery sequence through real run_handoff submission code and the
substitute kubectl: failure (exit 76) → monitor → repair task → agent edit → test → new handoff →
submit → completion → evaluation → measurement and decision in LEDGER.jsonl; replay creates no new
work. Runs: simulated runner (unit tests and demo); real `claude -p` (demo, 2026-10-08: 7 turns,
16 s, reported cost USD 0.23, changed only `code/config.json`); interruption after each step with
alternating holders (unit test); Claude-to-"codex"-holder handover after the agent step (demo; the
second holder ran only harness steps, no Codex CLI). Codex CLI: not installed in WSL; unverified.

**Not built.** External notification delivery; a scheduler that runs `watch` and `step`;
blocking direct `run_handoff.py` submission; cross-machine locking; reading pod logs when the pod is
gone; any live-campaign use.

```
python3 tools/harness.py init <campaign dir> --id <id>
python3 tools/harness.py approve <campaign dir> --by Kai        # terminal only
python3 tools/harness.py watch <campaign dir> [--records saved-list.json]
python3 tools/harness.py step <campaign dir> --holder claude-code --runner claude
python3 tools/harness.py submit <campaign dir> <handoff dir>
python3 -m unittest tests/test_harness.py
python3 tests/support/recovery_demo.py <sandbox> --runner simulated|claude [--resume-with codex]
```

### 7.1b Candidate implementation step (`run_implement` in tools/harness.py, 2026-10-08)

A queued `implement` task, from a dispatched plan, runs these saved steps:
1. `branch`: `cand-<node>` checked out from the parent node's `code_revision`; the workspace
   must be clean.
2. `implement`: `implement_runner` (Codex gpt-6.1-sol) with the specification. A process that
   died mid-run has its partial edits discarded.
3. Path check: `candidate_paths`, `candidate_protected`, and no existing test modified. The tree
   hash is recorded.
4. `review`: `review_runner` (Claude) writes only `evidence/<task>/review.json`, and only PASS
   continues.
5. `check`: `candidate_check_command`, run on the identical tree.
6. `commit`: the committed tree must equal the reviewed tree.
7. `prepare`: `candidate_prepare_command`; the handoff's `bnjettag.io/code-commit` must equal
   that commit.
8. `submit`: `harness.submit --stage search`. It runs only if `evidence/candidate-integration-PASS.json`
   exists, a file written only after the end-to-end demonstration passes.

Any refusal resets the workspace, records an implementation failure (not a scientific result) and
submits nothing. Tests: `tests/test_harness.py` class `Candidate`, with simulated runners.
Demonstration with the real runners: `tests/support/candidate_demo.py`.

### 7.1c Live state

Wave 1 was submitted to NRP on 2026-10-08 at 09:30 UTC (campaign RUN.md). The cron scheduled pass
has been verified.

### 7.2 Needed before deployment on NRP

- A scheduler on the home PC (cron or systemd timer) for `watch` and `step`; a decision on which
  agent CLI it starts and with which permission mode.
- Claude Code: settings allowing the headless agent to edit campaign workspaces without prompts;
  Codex: installation in WSL and its sandbox/approval policy.
- `kubectl get/logs` access from the scheduler's environment with a non-interactive NRP token, and
  how long that token lasts.
- Routing all submissions through `harness.py submit` (for example a hook refusing direct
  `run_handoff.py launch --submit`), so the GPU-hour check is not bypassable by the agent.
- If approvals must resist deliberate forgery: storage the agent cannot write, or a signature.
- Notification channel and its credentials (undecided; local log until then).

### 7.3 Remaining stages

1. ~~Campaign state files and templates~~ (done).
2. ~~Monitor over real record structures~~ (done on captured records; not yet run against the live cluster).
3. ~~Recovery sequence with agent repair~~ (done locally; simulated and Claude CLI).
4. Scheduler and deployment access (§7.2).
5. Rewrite RULES.md §3–§5 and CLAUDE.md to the operating model; update SYSTEM.md and AGENTS.md.
6. First campaign under the new model, with the existing holds left as they are.

---

## 8. Research behind this design (2026-10-08)

Summaries relayed by a web-reading tool; quotes not independently checked; the JFC paper's second
half was not read.

- Anthropic, Claude Code best practices: keep CLAUDE.md short, use hooks for must-happen rules,
  skills for occasional domain knowledge. https://code.claude.com/docs/en/best-practices
- Moreno et al., JFC, arXiv:2603.20179: one mandatory human gate, before full unblinding; expert
  verification of output cannot be shortcut. https://arxiv.org/abs/2603.20179
- Mishra-Sharma, long-running Claude for scientific computing: short CLAUDE.md, progress file with
  failed approaches, reference code as oracle, commits per unit of work, occasional human.
  https://www.anthropic.com/research/long-running-Claude
- get-physics-done: Supervised and Balanced modes. https://github.com/psi-oss/get-physics-done
- Agent Laboratory: errors accumulate across phases without feedback. https://arxiv.org/pdf/2501.04227
- Kubernetes pod failure policy. https://kubernetes.io/docs/tasks/job/pod-failure-policy/
- W&B Automations. https://docs.wandb.ai/models/ref/python/automations
- Anthropic, Claude Code auto mode (approval fatigue, ~93 % of prompts approved).
  https://www.anthropic.com/engineering/claude-code-auto-mode
- Not found: a public HEP repository with a CLAUDE.md that could be opened and verified.

---

## 9. Rule map (campaign 2026-10-08-discovery-350k, checked against the code on 2026-10-08)

**Effect column:**
- *warn*: a line in `NOTIFY.log`; nothing waits.
- *defers*: the action is retried on a later pass.
- *blocks submission*: no new Job is created.
- *holds task*: the task stays queued.
- *terminates*: a running pod or Job is ended. Only Kubernetes does this; the harness never
  deletes, patches or scales an object.

**Who changes it:**
- *Kai, re-approve*: an authority-block key; an edit voids `APPROVAL.json` until
  `harness.py approve` is run again.
- *agent, ops*: an operations-block key the agent may change inside the authority range. It is
  validated and needs no re-approval.
- *external*: an NRP rule, not optional.
- *protocol*: a scientific rule in PROPOSAL.md; a change is a protocol amendment.

Links: [BRIEF.md](../campaigns/2026-10-08-discovery-350k/BRIEF.md) (`authority` / `operations` blocks),
[harness.py](../tools/harness.py), [prepare_attempt.py](../campaigns/2026-10-08-discovery-350k/tools/prepare_attempt.py),
[hook](../.claude/hooks/pre-kubectl-lint.py), [nrp_doctor.py](../nrp-lab/nrp_doctor.py).

### Resources and time

| Rule | Source | Value, where | Effect | Who changes it |
| --- | --- | --- | --- | --- |
| Campaign GPU maximum | Kai | `authority.gpu_h_max` 240; `harness.submit` | blocks a submission when committed use plus the new bound exceeds the stage cap. This is a submission control: it keeps total use at or below 240 GPU-h only if Kubernetes enforces Job deadlines as documented, which is not yet observed on NRP. | Kai, re-approve |
| Stage reserves | Kai | `authority.reserve_gpu_h` confirm 90, follow-up 60; `stage_cap` | blocks earlier-stage submission | Kai, re-approve |
| Per-Job GPU bound | Kai (hard 240) | `authority.gpu_bound_mode` "hard"; Job `activeDeadlineSeconds` = 2 × pod deadline; `gpu_bound` | the Job deadline terminates the whole Job, retries and replacements included (Kubernetes) | Kai, re-approve |
| Bound violated | protocol of the cap | `decide` | stops new submissions; monitoring continues | not configurable |
| Elapsed time | Kai (decision 2026-10-08) | `authority.elapsed_days_max` 8 with `elapsed_behavior` "review"; warning at `operations.elapsed_days_warn` 6 | warn at 6 d; a progress-review notice at 8 d; nothing stops ("stop_new_submissions" is the other supported value) | Kai, re-approve (behaviour); warning: agent, ops |
| Concurrent GPU Jobs | lab's conservative local setting while E's GPU utilization is unmeasured. NRP's policy page limits underutilized pods (below 40 % of requested GPUs) to 4; it sets no general Job count. | `authority.max_concurrent_gpu_jobs` 4; utilization is measured during wave 1 | defers submission | Kai, re-approve |
| Pod deadline | agent default from measurement | `operations.deadline_seconds_per_epoch` 47 (39 s/epoch measured on RTX 3090 × 1.2) × stop epochs × runtime factor; set at preparation | terminates the pod (Kubernetes); the training script stops itself 420 s earlier (`ARM_BUDGET_S`) | agent, ops (new handoffs only) |
| Runtime factor | Kai limit, agent default | `authority.runtime_factor_max` 3.0; `operations.candidate_runtime_factor` 1.3 (or a candidate config's `campaign.runtime_factor`); `operations.runtime_factor_notify` 1.5 | above 1.5: preparation requires a timing-evidence file and a reason, both recorded, and Kai is notified; work is not paused. Above 3.0: refused. The smallest justified factor is used. | max: Kai; default and notice: agent, ops |
| Score Job deadline | agent default | `operations.score_deadline_s` 3,600 | terminates the score pod | agent, ops |
| NRP Job runtime | external | none ("jobs in Nautilus are not limited in runtime", nrp.ai Jobs tutorial) | none | external |

### Retries, repairs and agents

| Rule | Source | Value, where | Effect | Who changes it |
| --- | --- | --- | --- | --- |
| Kubernetes retries | agent default (pilot shape) | Job `backoffLimitPerIndex` 1; `podFailurePolicy`: Ignore DisruptionTarget, FailIndex 5/76/124/137/143, FailJob 10; pre-arm failure within 600 s exits 75 and is retried | Kubernetes; the harness acts only once Kubernetes has finished with an index | regenerate handoffs |
| Infrastructure relaunches | Kai max, agent setting | `authority.infra_relaunches_max` 2; `operations.infra_relaunches_per_key` 2 | after the limit the failure goes to investigation | agent within max |
| Repairs | Kai | `authority.repairs_total_max` 6; `operations.repair_attempts_per_class` 3 | over the limit: branch stopped, other runs unaffected | total: Kai; per class: agent within total |
| Candidate attempts | Kai | `authority.candidate_attempts_max` 5; `dispatch_plan` | refuses further implement actions | Kai, re-approve |
| Agent calls (headless) | Kai (decision 2026-10-08; replaces the PROPOSAL §8 prose counts) | `authority.agent_invocations_max` 40; warning `operations.agent_invocations_warn` 30; `agent_call_allowed` | holds pending agent tasks without losing them; monitoring, evaluation and recording continue | max: Kai; warning: agent, ops |
| Configured models and access | Kai | `codex_model` gpt-6.1-sol via ChatGPT login; Claude through Claude Code; no separately billed API | changing them needs Kai | Kai, re-approve |
| Review rounds | agreed (two rounds, then documented reasoning) | process rule, not code | none in code | protocol |
| Task lease | agent default | `operations.lease_s` 3,600 | an expired claim can be taken over | agent, ops |

### Approval, protection and permissions

| Rule | Source | Value, where | Effect | Who changes it |
| --- | --- | --- | --- | --- |
| Approval | Kai | `APPROVAL.json` `brief_sha256` = hash of the authority block; `require_approval` | blocks submission when missing or stale | Kai at a terminal only |
| Frozen files | protocol | `authority.frozen_files`: evaluator, reason table, fingerprint, check scripts; `submit` | blocks submission if any file changed | Kai, re-approve |
| Repair paths and settings fingerprint | protocol | `authority.repair_paths`; `tools/repair_check_d350.py` vs `settings/wave1-fingerprint.json` | refuses the repair; the workspace is restored and the diff kept | Kai, re-approve |
| Candidate paths and checks | protocol | `authority.candidate_paths` / `candidate_protected`; `tools/candidate_check_d350.py` | refuses the candidate | Kai, re-approve |
| Direct submission | Kai | hook: no `kubectl create/apply` of a Job; no `run_handoff.py launch --submit` of this campaign's handoffs outside the harness | blocks the command (Claude Code sessions only) | hook file |
| Lint | external + lab | `nrp_doctor.py lint` inside `run_handoff`: ERROR blocks, WARN passes. Missing node data → `harness.submit` defers instead of refusing | blocks or defers | lint rules: lab |
| CPU/memory | external (NRP: limits within 20 % of requests) | training: requests = limits = 2 CPU, 10 Gi; score: 8 CPU / 24 Gi | NRP policy | regenerate handoffs |
| GPU product | lab default | RTX 3090 node affinity, 5 excluded nodes | scheduling | regenerate handoffs |
| Memory projection gate | lab (pilot) | `BNJ_RSS_GATE_*` unset in these Jobs: off | none | n/a |
| Duplicate submission | protocol | `run_handoff` cluster lookup plus `harness.submit` resources entry | refuses or returns already-submitted | not configurable |
| Credentials | external | `kubectl oidc-login`; refresh verified without a browser | a monitor failure is reported once; Jobs continue | Kai (login) |
| WSL / cron | Kai's PC | crontab entry (SETUP.md); WSL idle shutdown untested | while down, nothing is monitored; Jobs continue | Kai |
| Interactive permissions | Claude Code | auto-mode check in sessions; headless runner limited to Read/Edit/Write/Glob/Grep; Codex `--sandbox workspace-write` | refuses the tool call | Kai (settings) |

**Pod deadline, expected runtime and reservation for a 1,000-epoch candidate at factor 1.3.**
These are three different numbers. The factor is applied once, in the pod deadline, and the
retry allowance once, in the Job deadline.

| Quantity | Calculation | Value |
| --- | --- | --- |
| Expected runtime | 39 × 1,000 × 1.3 | 50,700 s (14.1 h) |
| Pod deadline | 47 × 1,000 × 1.3 | 61,100 s |
| Job deadline | 2 × 61,100 | 122,200 s; queue time counts against it |
| Reserved at submission | 1 GPU × (122,200 + 180 + 300) s | 34.08 GPU-h |

Stage fit:
- The search cap is 240 − 90 − 60 = 90 GPU-h.
- After wave 1 (expected 2 × 10.8 GPU-h measured), about 68 GPU-h remain. That fits two
  candidate reservations (68.17) only just, so candidates usually run one or two at a time.
- When a candidate finishes, its measured use replaces its reservation.

## 10. How Kai changes a rule

1. Edit the key in [BRIEF.md](../campaigns/2026-10-08-discovery-350k/BRIEF.md):
   - the `json authority` block for commitments, permissions and protected commands;
   - the `json operations` block for allowances and thresholds.
2. Run `python3 tools/harness.py validate campaigns/2026-10-08-discovery-350k`. It prints both
   hashes, whether the approval still matches, and every error: unknown or misspelled keys,
   wrong types, values out of range. Any error blocks new submissions and agent work, and
   monitoring continues.
3. An authority edit voids the approval. Run
   `python3 tools/harness.py approve campaigns/2026-10-08-discovery-350k --by Kai` at a terminal.
4. When it takes effect:
   - harness keys at the next scheduled pass or task;
   - deadline and resource keys only for handoffs prepared afterwards, so regenerate a
     prepared-but-unsubmitted handoff;
   - never for a Job already on the cluster.

   Every submission records the authority and operations hashes in effect (`LEDGER.jsonl`,
   `STATE.json`).

Examples:
- **Deadline allowance (agent, ops).** Set `"deadline_seconds_per_epoch": 50` in operations,
  validate, then prepare the handoff again. The pod deadline becomes 50 × epochs × factor. The
  approval still matches.
- **Advisory threshold (agent, ops).** Set `"agent_invocations_warn": 10`. The warning appears at
  10 calls; nothing waits.
- **Resource limit (Kai).** Set `"gpu_h_max": 300` in authority. `validate` reports that no
  approval matches, and submissions are refused until Kai approves again.
- **Out of range.** Setting `"candidate_runtime_factor": 1.6` while `runtime_factor_max` is 1.5
  is reported by `validate` as an error and blocks submissions until it is corrected or Kai raises
  the maximum.

Tests: `campaigns/2026-10-08-discovery-350k/tools/tests/test_policy_d350.py`, with substituted
cluster operations:
- a normal wave-1 submission passes;
- a lint warning does not block;
- missing node data defers, then the submission succeeds;
- an operations edit needs no re-approval, while an authority edit voids it;
- out-of-range and misspelled keys block;
- runtime-factor allowances come from the configuration;
- an infrastructure failure resumes once without duplicates;
- monitoring failures issue no commands against Jobs;
- a submission stop keeps evaluation running.
