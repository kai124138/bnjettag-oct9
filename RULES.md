# RULES — how Claude operates here

## 1. Say the plan before doing it

Before any task longer than one step, one block of at most five lines, then start:

```
Goal:     the question or task, one line
Plan:     the steps
Touches:  files, cluster objects, anything outward
Cost:     agents and models, expected wall time
Stops:    when it ends, and what makes it stop early
```

No narration between steps. If the plan changes, one line: `Changed: X, because Y.`

## 2. Report for the physicist directing the research

Write for a physics student directing the work, not for an infrastructure engineer. Open with
what now works and its most important limitation; then the mechanism, the tests, what they
establish and what remains unverified. Define unfamiliar software terms. Plain, precise language;
no decorative symbols, metaphors or fixed status template. Keep a decision separate from its
execution: a queued request is not a started agent, a tested check is not enforced until the
real launch path calls it. Files, paths and commands come after the explanation, once; state
anything that needs Kai in the text. (Kai, 2026-10-08; communication only.)

## 3. Act or ask

| act without asking | ask first |
| --- | --- |
| reading, searching, local edits inside the task | a publication-ready claim |
| validators, lint, scratch compute, smoke tests | anything outward: push, email, Slack, publish, share |
| `kubectl get/logs/describe`; launching a lint-clean manifest for Kai's own work | deleting or overwriting what this session did not create; anyone else's jobs |
| | spend beyond the plan; any code or config change to a campaign past PREFLIGHT |

Launches listed in a PROGRAM.json that Kai signed count as approved (decision 2026-10-05). Inside a
campaign whose `APPROVAL.json` matches its BRIEF authority block, the brief governs: launches,
repairs, relaunches, internal recording and progression within its limits need no further approval
(Kai, 2026-10-08); its holds and reserved items still do.

One question at a time, with a recommended default.

## 4. Long jobs: launch, then leave

- Smoke test, full Job, session ends. Kubernetes handles retries and deadlines.
- No session watches a run. Approved campaigns are monitored by the harness scheduled pass
  (`tools/harness.py tick`, cron on the home PC; docs/agent-harness.md §9). The job reports its
  own end in its log.
- Follow-up in a fresh session: `kubectl get job <name> -n cms-ml` and
  `kubectl logs job/<name> -n cms-ml --tail=50`.

## 5. Code is frozen once a run starts

- No edits to the code, configs or manifests a launched run uses. On failure: write the error
  and diagnosis to `RUN.md` and `cluster-inventory.md`, report, wait; in an approved campaign the
  harness repair policy applies instead (a fix is a new commit and a new handoff). A fix is a new PREFLIGHT
  with a new code sha. Every code change is its own commit before use.
- "Proceed without me" changes nothing: stop and report on failure, never edit code to make
  something pass, never push.

## 6. How-to questions go in the field guide

Answer, then add an entry (date, question, steps, verified commands, newest on top) to "Asked
before" in `docs/field-guide.html`; Artifact-read and republish with `url`
https://claude.ai/artifact/1Qx77jZVjNnS3Ph5oWLxBu (never a new artifact). If a command changes,
update the goal tree and `docs/cheatsheet.md`.

## 7. Tokens

Subagents read in parallel with fresh context and wait on nothing. Cheap models look up,
expensive models judge. A phase ends with its artifact; the next starts in a new session.
Fan-out of more than three agents, or any workflow, is stated (count, models) before it starts.
