# Decisions

The earlier decision log was absent at this path in the canonical WSL workspace.

## 2026-10-08 (later) — Discovery campaign policy: authority vs operations; elapsed, agent calls, runtime

Kai, direct (policy batch before signing campaign 2026-10-08-discovery-350k):
1. BRIEF.md holds two blocks: `authority` (Kai's commitments, permissions, protected commands;
   bound to APPROVAL.json) and `operations` (agent-adjustable inside authority ranges; validated by
   `harness.py validate`; no re-approval). Edits beyond the ranges still need Kai.
2. Elapsed time: warn at 6 days, progress-review notice at 8 days, no automatic stop
   (`elapsed_behavior: review`).
3. Headless agent calls: one enforced limit of 40, warning at 30, replacing the PROPOSAL §8 prose
   counts. At the limit pending agent tasks wait; monitoring, evaluation and recording continue.
   Models and access unchanged (gpt-6.1-sol via ChatGPT login; Claude via Claude Code).
4. Runtime factor: default 1.3, maximum 3.0 (kept); above 1.5 a handoff needs recorded timing
   evidence and a reason and Kai is notified, without pausing; the smallest justified factor is used.
   All GPU-hour and reserve checks still apply.
5. Concurrent GPU Jobs: 4, described as the lab's conservative setting while E's utilization is
   unmeasured (not an NRP Job maximum); measure utilization during wave 1.
6. Unchanged: 240 GPU-h (a submission control backed by Kubernetes Job deadlines, not a measured
   consumption ceiling), 90/60 reserves, candidate and repair limits, K3, the pilot r3 PVC-rename
   hold, separate production approval, local-only notifications.

Check: `python3 tools/harness.py validate campaigns/2026-10-08-discovery-350k` VALID; rule map in
docs/agent-harness.md §9; containment regression check in tools/tests/test_policy_d350.py.

## 2026-10-08 07:01 JST — Operating model: autonomous research engineer; reserved approvals; first local harness

Kai, direct (session 2026-10-08):
1. **Target operating model** as written in `docs/agent-harness.md` §3: within an approved
   campaign the agent researches, implements, launches, monitors, diagnoses, repairs, relaunches,
   evaluates and picks the next step (PROCEED / INVESTIGATE FURTHER / STOP THIS BRANCH), notifying
   without pausing. Either Claude Code or Codex operates it from shared on-disk state.
2. **Reserved for Kai:** publication-ready scientific claims, public releases, external messages
   sent on his behalf. **Not reserved:** logging measurements internally, preserving verified
   results with provenance, notifications through an approved channel. Internal recording stays
   automatic.
3. A reviewer disagreement may be resolved with documented reasoning. A failed numerical or
   authorization check cannot be waived to continue.
4. Proceed with the smallest local implementation and synthetic tests (`tools/harness.py`,
   `tests/test_harness.py`). Existing live-campaign holds (pilot program K3, the r3 PVC rename)
   are unchanged. RULES.md and CLAUDE.md are not yet rewritten (rollout stage 5).

Check: `python3 -m unittest tests/test_harness.py` passes; no cluster object touched.

## 2026-10-07 07:29 JST — Relaunch R1's 23 stopped arms with the memory gate off; alerts plan

Kai, direct ("do this bro"; "i will turn on the wandb noti myself"):
1. Relaunch the 23 R1 arms killed by the RSS-gate horizon bug, from their epoch-100 checkpoints,
   with `BNJ_RSS_GATE_LIMIT_MB` unset (env only; bundle 98dd2875 and configs unchanged). New Job
   names, one solo critical review, inside the 144 GPU-h R1 cap. Record:
   `local/2026-10-07-execution/r1b-relaunch-approval.json`.
2. Kai enables W&B run finished/failed alerts himself.
3. Next code version: the memory check warns instead of killing (kill only near the pod limit),
   and the training script sends a W&B alert at run end.
4. Later: a read-only watcher on the home PC once Kai picks a phone channel.

Check: relaunched pods log a resume from epoch 100 (or the restart is reported); no gate line kills a pilot.

## 2026-10-05 15:21 JST — Kai's answers on the pilot STUDY panel (K1–K4)

Kai, direct: "w100. approve 24 pods / 144 GPU-h. yes, production waits for my go. decide the
spend ceiling at the production gate. after round 1 launches, stop and give me a short status."
- K1 (D3): the H4 long-warmup arm is **w100**, not w150.
- K2: R1 is **24 pods, 144 GPU-h** (adds A350-C-qkv1-450k and E-unc-C, drops A07-350k).
- K3: **no automatic production launch.** The rules qualify a candidate; Kai decides.
- K4: the production spend ceiling is decided at the production gate on R1's measured s/epoch.
- Session instruction: after R1 launches, stop and report a short status.

Check: STUDY.md §4/§9/§11 and PROGRAM.json reflect K1–K3; no production handoff is submitted
without a dated Kai go.

## 2026-10-05 10:08 JST — Pilot program approved; autopilot authorized; CPU-gate test fix approved

Kai, direct ("yeah i approve them bro go ahead"), approving `docs/PILOT_PROGRAM.md` §6 and the
CPU-gate fix:
1. **Test fix:** the one-line `BNJ_CAMPAIGN_DIR` override in `tests/test_run_pack.py`
   (`campaigns/2026-10-02-chang-option-c/REGRESSION_TICKET.md`), with a new sha, PREFLIGHT and
   CPU gate rerun.
2. **Pilot program:** hypotheses H1–H5; rounds R1–R3 on RTX 3090, one arm per GPU, epoch 500;
   then production of A and NB, 8 seeds, 7,000 epochs.
3. **Decision rules** go in `campaigns/2026-10-05-pilot-program/PROGRAM.json`. Kai signs the
   drafted file before the autopilot acts on it.
4. **RULES amendments:** §4 lets the autopilot poll job state and start pre-signed steps;
   §3 counts launches listed in a signed PROGRAM.json as approved.
5. **Spend:** about 1,200 GPU-h on RTX 3090s (about 250 for pilots, about 960 for production).
6. **Home PC:** this machine (RTX 4060 Ti 8 GB, i5-13600K) may run local exploration and hosts
   the autopilot. Its numbers are never quotable. This supersedes "nothing heavy on this laptop".
7. **Dates** in program records use local time, JST (UTC+9).

Check: the autopilot launches only handoffs listed in the signed PROGRAM.json; every action is
in `local/autopilot/log.jsonl` and the campaign JOURNAL.md.

## 2026-10-05 — Kai's answers on the 2026-10-04 session questions

Kai, direct, in session (answers to `local/2026-10-04-session/SESSION.md` §5):

1. **Option (c) CPU gate approved**, conditional on a solo critical-reviewer PASS of
   `campaigns/2026-10-02-chang-option-c/PREFLIGHT.md`. This covers `kai-chang1002c-cpugate-691946`
   only; the GPU pilots and readout are not yet approved.
2. **Delta A07 product rule [A1] (≥45 GB) dropped.** `docs/infrastructure/gpu-selection-policy.md`
   governs product choice for A07 as for E. Kept: NRP's 40 % GPU-utilization floor (rule PACK),
   the policy's 90 % GPU-memory ceiling, one product per cell/replica/placebo block and per
   Chang seed pair, the 10-Delta-pod cap. A07 measured K=2 on a 24 GB A10 at 73.4 % memory
   (canary telemetry, delta-screen RUN.md:506-508), so 24 GB cards are eligible at K=2.
3. **Delta rebase onto option (c): delegated to the orchestrator ("do what is scientifically
   sound").** Ruling: no rebase now; rebase once if and only if (c) becomes the Chang production
   recipe. Reason: Delta's internal comparisons (cell vs replica vs placebo on one code tree) are
   valid on either anchor, which is why SCIENTIFIC_GATES.md:50 is right that a new Chang sha
   does not force a rebase. But Delta's purpose is to find levers for the production tagger, and
   many Delta methods act on activation width and EBOPs, which interact with the PID input
   that (c) changes, so results measured on the 42abed controller may not transfer. Hence
   ONBOARDING.md:99-102 also holds once (c) ships. No Delta cell launches before the option (c)
   epoch-500 readout. If (c) is adopted, rebase once (`code/PLAN_rebase.md`, conflict sites
   0012/0014/0019/0020/0038) under a new PREFLIGHT; if not, Delta stays on 42abed plus its fixes.
   CONFIDENCE: MEDIUM. FLAG FOR HUMAN: YES (Kai can overrule at the (c) readout).
4. **`hcc-nrp-shor-c6017.unl.edu` added to `KNOWN_BAD_NODES`** in `nrp-lab/nrp_doctor.py`.
5. **Context kept low:** CLAUDE.md and RULES.md trimmed (169 → 131 lines with index-head; cap
   150). No rule removed; RULES sections renumbered (field guide now §6, tokens §7).
6. **SYSTEM.md §7:** the two Mac-migration items removed as obsolete in the WSL workspace.

Check: the CPU gate launches only after `review/PREFLIGHT_critical_v1.md` reads PASS; no Delta
manifest uses an A07 product rule other than the GPU policy; no Delta cell before the (c) readout.

## 2026-10-02 — Jev adopted as an advisory tool; JFC scaffolding restored 2026-10-04

Jev (`tools/jev/`, MCP server `jev-lab`) is part of the lab loop, advisory only. The
integration smoke run on 2026-10-02 completed 8 Jev calls on model `jev-1.13.0` with every
check true (`local/2026-10-02-jev-integration/SMOKE.json`, SHA-256
`2cf1ce6b1155d1060d9ba8c5f145da60a101000e2ca0e99165561ca9e91262bb`). On 2026-10-04 the agent
definitions (`.claude/agents/`, 13 roles from SYSTEM.md §4), `/review`
(`.claude/commands/review.md`) and `.claude/settings.json` (kubectl-lint PreToolUse hook,
SessionStart brief, `jev-lab` enabled) were recreated; they had been absent since the
migration. Each agent names the Jev tools it uses. Jev never issues a verdict, never clears a
gate and gives no launch grant.

Check: `python3 tools/jev_lab.py doctor` reports the key available; the hook blocks a bad
manifest; `SYSTEM.md` §4 "Jev in the loop" matches the agent files.

## 2026-10-01 06:00 UTC — Chang option (c): traced cost in the PID

Kai explicitly selected “(c) Feed traced cost directly into the PID controller.”
The source decision is `local/2026-10-01-execution/chang-option-c-decision.json`,
recorded at `2026-10-01T06:00:02.706672Z`, SHA-256
`bccbc0adc43ec0063aeae15da7ecfabdb2f6b2fc7c498eb86391d9d6d5a5918b`.
The (c)/(d) choice is resolved. K1 remains triggered; this choice does not clear
production or authorize substituting modified code into historical b5 evidence.

Finish the historical b5 diagnostic readout, write the dated option-(c) amendment,
repeat required CPU/pairing/fingerprint/floor checks, freeze the new actual inputs
and complete the replacement pilot before production can advance. The original
42abed bundle and snapshots remain unchanged during missing-evidence readout.

Check: the exact user decision is recorded once in the linked source; STATE and
recovery reports distinguish the selected option from pending scientific gates.

## 2026-10-01 — Separate NRP sign-in from user-mediated Mulder access

Kai clarified that Mulder requires his explicit permission and a UCSD-verified
connection through his MacBook; direct access from this WSL environment is not
available. Wait for his permission and established connection. Do not request
exported credentials or attempt to fetch them from the Mac. NRP-only checks must
avoid `nrp_doctor.py all`, which also tries Mulder.

The migration deliberately excluded `.kube` configuration and credentials. The
old NRP skill's claim that access was already configured referred to the Mac setup.
Restore the current public NRP template in WSL and authenticate separately. Kai
offered to use Parsec to complete the NRP institutional verification in his browser;
the documented device-code sign-in was started for a read-only access check.

Check: `local/2026-10-01-execution/nrp-config-repair.json` records public-template
hashes and local adaptations. No Mac or Mulder connection was attempted in this turn.

## 2026-10-01 — Publish the compatibility implementation as a draft

The user requested completion of recovery, Chang resolution, GPU/Delta gates, full
schedules, code merge and hardware validation, following the request to update GitHub.
Preserve the public pipeline's defaults and exact configuration identities while
adding the existing optional pT behavior and historical interfaces. Both original
source trees remain captured, and frozen scientific campaign bundles remain intact.

Publish draft PR 1 after the bounded engineering preflight and independent critical
PASS. Historical metric/calibration evidence and uncovered checkpoint identities
remain pending, so the change is not recorded as a full migration or hardware result.
No Chang branch choice, scientific schedule change or cluster launch is inferred.

Check: `campaigns/2026-09-26-code-line-merge/review/PREFLIGHT_critical_v2.md` and
`local/2026-10-01-execution/publish-receipt.json`; PR 1 is open and marked draft.
