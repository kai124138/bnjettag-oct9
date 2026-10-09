---
title: Phases
status: current
date: 2026-09-26
---

# 3. The five phases

A campaign is `campaigns/<YYYY-MM-DD>-<type>/` (in the lab repo until the migration runs:
`local/<date>-<type>/`). One artifact per phase, written from the template in
`templates/`. A phase does not begin until the previous artifact exists on disk and its
review verdict is PASS.

| phase | artifact | owner | review tier |
| --- | --- | --- | --- |
| 1 design | `STUDY.md` | experiment-designer | panel (physics + critical + constructive → arbiter) |
| 2 preflight | `PREFLIGHT.md` | ml-engineer, cluster-ops | scripts (`nrp_doctor lint`, build gates) + critical |
| 3 run | `RUN.md` | cluster-ops | self + scripts; critical on request |
| 4 verify | `VERIFY.md` + `verify.json` | results-analyst | `verify_check` + plot-validator, then panel → arbiter |
| 5 report | `REPORT.md` | paper-writer | plot-validator + `prose_lint` + `pdf_check` + `bib_check`, then panel → arbiter |

## The owner protocol (JFC's executor, adopted 2026-09-26)

JFC runs every phase through one generic executor with a per-phase template. Here the six
owner agents are the templates; what they share is this protocol, taken from JFC's
`executor.md` with its collider-specific checks translated. Every owner follows it.

1. **Plan first.** Write `plan.md` beside the artifact before doing anything: what will be
   computed, which scripts, which figures, what the artifact will contain. Keep it current as
   you go; it is the crash-resilient notebook. Record every approach that was tried and
   failed, with the reason, so nobody retries it; the experiment-log Result line points to
   `plan.md` for them.
2. **Self-check before handing off,** against `appendix-checklist.md` for the artifact, and:
   - every "will implement" row in STUDY.md's conventions table is addressed;
   - every `[D]` label is implemented **as stated**, not replaced by an approximation. If a
     committed input cannot be found, stop and report it; never substitute a derived value;
   - no circular selection: no checkpoint, threshold or arm chosen on the split it is then
     evaluated on;
   - every failed validation has documented remediation attempts;
   - every figure is referenced in the text, every heading has prose.
3. **Anti-fabrication (non-negotiable).** No parameter, checkpoint or threshold adjusted after
   seeing the result so that it matches a reference or looks better; every choice has a prior
   justification. No seed, arm or variation dropped because its number was inconvenient; a
   large spread is the spread. No interval smoothed, truncated or narrowed for appearance.
4. **Formula verification.** Every equation in an artifact has a source or a derivation. Check
   it by substituting known values (an AUC in [0.5, 1], an eBOP count of the right order, a
   resource fraction under 100 % of the VU13P) and in one limiting case (identical arms give
   Δ = 0 and an interval around 0).
5. **Flag uncertain decisions** in `plan.md` and the artifact's "where I am not sure":

   ```
   DECISION: …   ALTERNATIVES: … (with their numbers)
   CONFIDENCE: HIGH | MEDIUM | LOW   FLAG FOR HUMAN: YES | NO
   ```

   MEDIUM and LOW go to Kai at the human gate. An agent that decides everything with high
   confidence is overconfident.

6. **Protocol check (STUDY, PREFLIGHT).** Express the training protocol as JSON and run
   `lab_check_protocol`; freeze it with `lab_freeze_protocol` when STUDY passes, and check
   PREFLIGHT configs against that snapshot with `baseline_path`. The snapshot is a declaration
   check, not a campaign freeze or a launch grant (`docs/infrastructure/jev-lab.md`).

What is not adopted, and why: JFC's "commit frequently" (the orchestrator commits here),
its session logs under `logs/` (`plan.md` does that job), its all-opus rule (a global
setting, not an agent; this lab keeps cheap models for finding and opus for judging), and
its RAG corpus queries (there is no corpus; literature goes through physics-researcher).

## Phase 1: design → STUDY.md

The founding document. It is reviewed before any compute is spent.

Required content:

- **Question and null.** One sentence each. How the answer bears on the thesis.
- **Reference table.** Two or three prior results this campaign will be compared against:
  the round-14 record for the same configuration, and any literature result from
  `literature/INDEX.md` with the same input set. A number in this table carries its source.
- **Arms.** Matched: only the manipulated variable differs. Same N, same input set, same
  split, same schedule, same initialisation where shapes permit. State every difference.
- **Seeds.** At least three for any claim; at least eight when the expected gap is under
  0.005 in AUC (the seed sd at N=8 W1A8 is about 0.0015). Say what the seeds can resolve.
- **Selection rule, pre-registered.** For example "the checkpoint with the highest
  validation macro-OvR AUC among those at or under the eBOP budget". Never selected on the
  held-out set. Written before any run exists.
- **Falsifier.** The result that would make the claim false.
- **Budget.** Arms × epochs, GPU-hours, arms per pod (rule PACK), expected wall time from a
  benchmark, W&B project and group.
- **Conventions compliance table.** One row per applicable convention in `docs/conventions/`:
  "will implement" or "not applicable because …".
- **Decision labels.** Binding choices as `[D1]`, `[D2]`, …; a later phase may not replace one
  silently. Constraints `[A]` and known limitations `[L]` likewise.
- **Where I am not sure.** Judgement calls the human should see.

Gate: arbiter PASS.

## Phase 2: preflight → PREFLIGHT.md

Everything that can fail on a CPU fails here, not on a GPU.

Required content: configs generated by the generator, not hand-edited; every config builds
on CPU with the parameter count recorded; every arm's checkpoint reloads within 1e-7 with
TF32 off; `preflight_final.sh` reports `PREFLIGHT_ALL_PASS`; the 2-file/3-epoch smoke ran;
the code sha and ConfigMap name; the pasted output of `nrp_doctor.py lint` on every
manifest (the hook enforces it at launch anyway); the packing benchmark (K arms per pod,
measured GPU utilisation above 40 percent).

Gate: all scripts green, critical reviewer PASS.

## Phase 3: run → RUN.md

Operations, kept out of the science record. Required content: launch record, job names,
nodes, W&B group, per-arm final state (epochs completed, checkpoint ids), every resume and
incident with a pointer into `cluster-inventory.md` (each incident there ends with a Check
line). Nothing in RUN.md is quotable.

Gate: every arm reached its committed epoch count or its failure is recorded with cause.

## Phase 4: verify → VERIFY.md

The numbers gate. Required content:

- Every number recomputed from the raw artifact (`.npz`, csynth JSON, `ebops.json`) with
  the recompute command, and labelled: metric, split, n, status (single seed / seed-averaged).
- Selection applied exactly as pre-registered; the selected checkpoint named.
- Seed spread (sample sd, ddof=1) and a paired interval on every gap; per-class AUC; accuracy
  beside AUC, never instead of it; pT-binned metrics where the question is about tails.
- Cost: native HGQ2 eBOPs remeasured on the selected checkpoint (zero and random inputs
  agree); binary layers verified to hold exactly two nonzero symmetric values.
- Hardware, when synthesised: parsed csynth resources (LUT, FF, DSP, BRAM), II, latency,
  Fmax; C-simulation fidelity against the exported model; what is an estimate and what is
  implemented.
- Consistency with the record: the baseline arm reproduces the recorded value for the same
  configuration within the seed spread, with the pull stated.
- `verify.json` beside VERIFY.md: one row per quoted number (`claim`, `quantity`, `value`,
  `metric`, `split`, `n`, `seeds`, `status`, `source`). REPORT.md, figures and PI updates read
  numbers from it, never from prose. Required for campaigns started after 2026-09-26.
- `tools/verify_check.py` clean; a verdict per claim in STUDY.md; what was falsified.

Gate: arbiter PASS. Then the human decides what enters the record.

## Phase 5: report → REPORT.md

Required content: interpretation against the thesis; what is open; figures through the
style kit with provenance captions; the equations defining the metrics used; a resolving
power statement ("with eight seeds this design resolves ΔAUC ≥ 0.002"); limitations with
evidence of what was tried; a change log at the top, append-only; every number traceable to a
`verify.json` row. Outward text (README section, PI update, note) is drafted here and only
leaves after the human gate.

Gate: arbiter PASS, then Kai.

## Iteration and regression

On ITERATE, the **fixer** agent resolves each listed finding with the minimum effective
change, propagates every changed number to every copy of it, and reports RESOLVED / PARTIALLY
RESOLVED / CANNOT RESOLVE per finding; a fresh panel then re-reviews. Findings the fixer
cannot resolve (a design change, a cluster or mulder run) go back to the phase owner. On a
regression trigger (§6.7 of `06-review.md`) the investigator writes `REGRESSION_TICKET.md`,
the fixer executes it, artifacts get new versions (`STUDY_v2.md`) rather than overwrites, and
downstream phases re-run only where their inputs changed. Kai sees the ticket before the
fixer executes it.
