---
title: Review protocol
status: current
date: 2026-09-26
---

# 6. Review protocol

Review is mandatory at every phase gate. Self-review is acceptable only for RUN.

## 6.1 Classification

- **(A) Must resolve.** Blocks advancement.
- **(B) Should address.** Weakens the study. Fixed before PASS.
- **(C) Suggestion.** Style, clarity. Applied before commit, no re-review.

Red flags from `tools/plot_check.py`, `tools/verify_check.py`, `tools/prose_lint.py`,
`tools/pdf_check.py` and `tools/bib_check.py`, and every RED FLAG the plot-validator records
in `review/<PHASE>_plots_v<n>.md`, are Category A. The arbiter may not downgrade them: they
are objective checks, there is no judgement call.

## 6.2 Tiers

| phase | tier | who |
| --- | --- | --- |
| STUDY | panel | physics-reviewer + critical-reviewer + constructive-reviewer in parallel, then arbiter |
| PREFLIGHT | scripts + 1 | `nrp_doctor lint`, build and reload gates; critical-reviewer (solo) |
| RUN | self | cluster-ops self-check; critical-reviewer (solo) on request or when an incident recurs |
| VERIFY | panel + scripts | `verify_check`; plot-validator (runs `plot_check`, then reads every figure); then the panel; then arbiter |
| REPORT | panel + scripts | plot-validator, `prose_lint`, `pdf_check`, `bib_check`; then the panel; then arbiter |

Scripts and the plot-validator run first, so the panel and the arbiter see their output.
The plot-validator runs `plot_check` on every figure script, then opens every rendered
figure and lists each by name with PASS or its violations. It runs wherever figures exist
(VERIFY, REPORT); STUDY has none.

The physics-reviewer receives only the thesis paragraph and the artifact, with the figures,
arrays and compiled PDF the artifact cites. It does not read this methodology, the
conventions, or earlier reviews. It is the referee who never saw our rules. The
critical-reviewer and the constructive-reviewer read everything, including the conventions
and the experiment log. The arbiter reads the artifact, every review, the validator and
plot-validator output, the previous arbiter file on a re-review, and the conventions.

Model: the reviewers, the plot-validator and the arbiter run on opus. The other agents keep
the lab rule "cheap models find, expensive models judge" (`SYSTEM.md`). JFC runs every agent
on opus, but that is a global setting, not an agent definition, so the rule that JFC's
version wins where it overlaps does not reach it.

Rounds (`/rounds`) are the critical-reviewer alone over an interval, outside the phase gates.
Iteration caps and where ITERATE goes: §6.5.

Jev assists the tiers but never decides them: reviewers run `jev_check_claims` on quoted
numbers, the arbiter may run `jev_triage_review` on finding categories, and the
investigator runs `jev_triage_logs`. A category A finding stays A whatever Jev says, unless
independent evidence shows it wrong (§6.5.1). See `SYSTEM.md` §4, "Jev in the loop".

## 6.3 Reviewer framing

The key question: **what would a knowledgeable referee ask for that is not here?** Check
completeness against the outside world, not only internal consistency. Before concluding,
every reviewer answers:

1. Is every applicable convention implemented or justified as not applicable?
2. Does the reference table exist, and does the study match its reference results' rigour
   (seeds, split, matched arms)?
3. If a competing group published the same comparison next month, what would they have
   that we do not?
4. Are the uncertainties honest in both directions? Too few seeds understates; a claim of
   "consistent" behind a huge seed spread overstates. Inflation counts too: an unpaired
   interval where the arms share seeds, or an interval so wide that every check passes,
   is not conservatism. Does the design have resolving power: can it separate the arms at
   the gap it claims, given the measured sd?

   An answer of "no" to 1, 2 or 4, or a non-empty answer to 3, without justification is
   Category A.
5. Were limitations accepted without evidence of an attempt? "Single seed" without a quota
   reason is B. "Exploratory, 50 epochs" without a plan to confirm is B. The study should
   show the best result it could get, not the minimum that passes.
6. Does every result have context: a comparison to the recorded value for the same
   configuration, with a pull?

### 6.3.1 Evidence-based review

"Verified", "confirmed", "looks reasonable" without a number, a path or a line are not
acceptable in any review. Acceptable: "BASE-s1 ROC-test macro AUC recomputed 0.87113 from
`roc-results/ptw-n8/BASE-s1.npz` (n=260,000), log claims 0.8711, ✓". A reviewer who cannot
cite evidence for a verified claim has not verified it.

### 6.3.2 Keep looking

One error suggests others. After a finding, check the same file for related issues, check
whether the pattern appears elsewhere, and ask where else the same mistake would live.

### 6.3.3 Adversarial stance

The producing agent is unconsciously motivated to present its work favourably. Challenge:

- "within the seed spread" used to dismiss a gap the design was supposed to resolve;
- "exploratory" or "screen" used to state a number and disown it in the same sentence;
- "will confirm in the next campaign" without a campaign;
- "consistent with the record" when the pull is not computed;
- a selection rule that changed after results existed;
- accuracy quoted where AUC was the selection metric, or the reverse, without saying so;
- a projection (C-synthesis estimate, extrapolated epochs) presented as an implemented result.

### 6.3.4 Tracing a fact

Reviewers and the arbiter cannot spawn agents; none of them has the Agent tool. When a
concern needs more than reading the artifact (more than about three files, a number traced
through scripts, two arrays checked for the same split, an eBOP count recomputed), the
reviewer traces it with Read, Grep and Bash and cites file and line. If it is too large for
one review, the reviewer records it as a disputed fact, with the question, the paths and the
evidence that would settle it; the orchestrator hands it to the investigator, whose answer
is then cited as evidence. Tracing is for substantive concerns, not routine checks, and the
review says why it was needed and what it found.

## 6.4 Review focus by phase

**STUDY.** Question falsifiable? Arms matched? Seeds sufficient for the claimed gap?
Selection rule pre-registered and on validation, never held-out? Budget realistic and
packed? Reference table present with sources? Conventions table complete? Decision labels
present?

**PREFLIGHT.** Every config builds and reloads? Lint clean or every warning read? ConfigMap
sha matches the code sha? Packing benchmark measured, not assumed?

**VERIFY.** Every number recomputed with its command? Labels complete? Selection applied as
pre-registered? Seeds and intervals on every gap? Baseline reproduces the record within the
spread (§6.8)? eBOPs remeasured? Binary layers binary? `verify_check` clean? Every STUDY
claim has a verdict? Numerical self-consistency across VERIFY, REPORT and any README table
(a fix cycle that updates one table and not the others is Category A). Every comparison
algebraically independent? Selection and evaluation on the same split, two arms that agree
to five decimals, or validation AUC equal to held-out AUC means the comparison is
tautological or broken; presenting it as validation is Category A.

**REPORT.** Interpretation follows from VERIFY, not beyond it? Equations define the metrics?
Resolving power stated? Limitations show attempts? Figures pass `plot_check` and the
plot-validator? Prose passes `prose_lint` and reads as Kai's? PDF compiles clean
(`pdf_check`)? Every citation resolves (`bib_check`)? Nothing outward until the gate. Also:

- **Consistency sweep (Category A).** The abstract or summary, the results table, the
  conclusion and any README or PI-update draft give the same value to the precision quoted.
  The headline configuration (N, input set, eBOP target, selection rule) is the same
  everywhere it is called the headline. Counts (n, seeds, arms) match exactly.
- **Narrative (Category B if weak).** Motivation beyond "not done before"; each section
  follows from the last; after the results, what the numbers mean for the thesis; context
  against the recorded and published values; the resolving power sentence.
- **Figure-scrolling test (Category B).** Can the study be followed from the figures alone:
  the design, the headline comparison with its interval, the cost or resources? Name each
  step that has no figure, and each non-trivial method with no schematic.

**Figures (VERIFY and REPORT).** `plot_check` reads the scripts; the plot-validator reads the
rendered images. Every reviewer who looks at a figure also checks that it makes sense, not
only that it is formatted. Category A if seen and not explained in the text: a ROC curve on
the wrong side of the random-guess line (AUC under 0.5; with mistag on the y axis, mistag
above efficiency); an AUC or efficiency outside its range; arms that should differ drawn
identically; a legend or annotation value that differs from the table; error bars that do not
match the stated seed spread or n. "Figures look fine" is not acceptable: every review that
covers figures lists each one with its status and says whether it agrees with the text.

## 6.5 Iteration and escalation

Panel tiers (STUDY, VERIFY, REPORT) repeat until arbiter PASS: warn at 3 iterations, warn
strongly at 5, ESCALATE at 10. Solo tiers (PREFLIGHT, and RUN when reviewed): warn at 2,
ESCALATE after 3. The reviewer or arbiter escalates rather than loops.

**ITERATE** goes to the `fixer` agent with the arbiter file (or the solo verdict): minimum
effective change per finding, no refactoring around it, every changed number propagated to
each place that shows it (the cascade, §6.7). Findings the fixer returns as CANNOT RESOLVE
go to the phase owner: experiment-designer for STUDY, ml-engineer or cluster-ops for
PREFLIGHT and RUN, results-analyst for VERIFY, paper-writer for REPORT.

Every ITERATE produces a written re-review. At panel tiers, iteration n writes
`review/<PHASE>_<role>_v<n>.md` for each reviewer (physics, critical, constructive),
`review/<PHASE>_plots_v<n>.md`, `review/<PHASE>_validators_v<n>.txt` and
`review/<PHASE>_arbiter_v<n>.md`. The critical-reviewer and the arbiter receive
`review/<PHASE>_arbiter_v<n-1>.md` and check each earlier A and B finding by name, resolved
or not, with evidence; the physics-reviewer never sees earlier reviews. At solo tiers the
next critical-reviewer report does the same against the previous one in
`.claude/memory/review-reports.md`. New issues continue the cycle. Fix → advance without a
re-review is a process failure.

### 6.5.1 Arbiter dismissal rules

The arbiter may not dismiss a finding as "out of scope" when the fix is under about an hour
of agent time. Re-running an evaluation script with another seed, re-parsing a csynth
report, making a missing figure or propagating a number through existing tables is not out
of scope; it is what iterations are for. When several findings each need an earlier phase
re-run, that is extra motivation to fix them together in one regression or iteration, not a
reason to dismiss each one.

Every dismissal states a cost estimate in agent-hours (not "significant effort"), why the
finding does not change the conclusion, and when it will be addressed. "Requires re-running"
or "out of scope for this phase" without a cost estimate is not acceptable; regression
(§6.7) exists for findings that need upstream work.

A reviewer's finding stands, at the category the reviewer assigned, unless independent
evidence (the artifact, code, arrays, or the investigator's answer) shows it wrong. This
holds when the producing agent or an earlier review cycle disputed it. "The executor
explained it" is not evidence, and "too strict" or "minor" is not a reason.

## 6.6 The human gate

Two moments, and the options are the same at both:

- a number moving from a VERIFY.md into the record (`README`, `RESEARCH.md`, a PI update);
- anything pushed outward (a public repo, a message to Russell or Javier, a poster).

Kai receives the compiled artifact (a PDF for a note; the README diff for a repo), the
arbiter's verdict with residual B and C items, and the "where I am not sure" list. He answers
**APPROVE**, **ITERATE** (fix within the phase, re-review, re-present), **REGRESS(N)** (a
fundamental issue traced to phase N; the investigator scopes it; artifacts get new versions),
or **PAUSE** (something external is needed: quota, a licence, an advisor's input).

Human review checklist: do the baseline numbers match the record? Are the arms matched? Do
the seeds resolve the claimed gap? Is anything single-seed or exploratory stated as a
finding? Do the figures say what the text says? Would you send this to Russell as is?

After any regression, the artifact tells one coherent argument for the current study: the
body reads as if the current design was the plan from the start, and the change log at the
top carries the audit trail (what changed, when, why). A REPORT that keeps the old
motivation around new numbers is a patch, not an argument; the re-review checks this.

## 6.7 Regression triggers (classifier and hardware study)

A finding at phase N traceable to an earlier phase is a regression; it is investigated, not
rationalised. Concrete triggers:

- the selection rule was applied on the held-out set, or changed after results existed;
- validation AUC and ROC-test AUC for the same model differ by more than 0.01 without an
  explanation (a split or leakage problem);
- a headline from a single seed, a screen under 100 epochs, the lab pod, or a 50-epoch
  exploratory protocol compared against the 1000-epoch record;
- a comparison across N, input sets, splits or schedules presented as one series;
- a reported gap smaller than the seed sd with fewer than three seeds;
- checkpoint reload outside 1e-7, or TF32 on when off was committed;
- reported eBOPs not equal to the remeasured native cost of the selected checkpoint, or
  final-epoch cost mixed with best-checkpoint AUC;
- a binary layer with more than two nonzero effective weight values;
- DSP > 0 in a layer the claim calls DSP-free; C-simulation disagreeing with the export
  beyond the recorded argmax-change rate; a C-synthesis estimate stated as implemented;
- per-class AUC under 0.7 hidden behind a macro average, or a class collapse;
- arms that should differ producing byte-identical arrays, or arms that should match
  producing different `y` arrays (wrong split);
- a failed validation test (build, reload, recompute, a control arm) accepted without
  documented remediation attempts, or a tautological comparison presented as validation;
- a decision label `[D]` from STUDY.md replaced without a dated amendment;
- an outward document whose numbers differ from the latest VERIFY.md by more than rounding.

Suspiciously good is a trigger too: macro-OvR AUC above 0.95 at N=8 W1A8 (the record is
about 0.87), zero seed variance, validation equal to held-out, or every check passing with
no tension. Ask what could be wrong that the checks would not catch.

Not regression: axis labels, captions, prose. Those are REPORT iteration. Regression may be
triggered at any gate, including the human gate.

Procedure: the review documents the trigger and names the origin phase; the orchestrator
spawns the investigator; `REGRESSION_TICKET.md` names the origin, the affected downstream
artifacts, the scope and the cascade, and the investigator appends a line to the campaign's
`regression_log.md`. The orchestrator shows the ticket to Kai and waits. After he answers,
the fixer executes the ticket, artifacts get new versions, and the affected phases re-run
and re-review with the same panel.

**Cascade (every fix, not only regression).** When a component changes (a selection rule, a
recompute script, an eBOP measurement, a split, a label), every consumer of its output is
traced: each script, table, figure and artifact section that used the old output is re-run,
or the reason it is unaffected is written down. A downstream number that moves outside its
interval, or a ranking that changes, propagates further. Re-running a script is cheap; a
stale table that contradicts the fix is what a referee finds.

**Upstream feedback (non-blocking).** Any agent that finds, at a later phase, something an
earlier phase should have caught writes it to `UPSTREAM_FEEDBACK.md` in the campaign
directory: date, phase found, origin phase, what. The next review gate reads it. It blocks
only if it meets a trigger above.

## 6.8 Validation target rule

When STUDY.md names a reference (the round-14 value for the same configuration, a published
number with the same inputs), that reference is binding. It applies at every tier at VERIFY
and REPORT; STUDY names targets, and PREFLIGHT and RUN produce no numbers to test.

**Tier 1 (Category A).** A baseline arm that deviates from its reference by more than twice
the seed spread, or by more than 0.01 in AUC, is Category A until a quantitative cause is
shown: a bug, a changed split, a changed schedule, or a documented amendment. "Different run
conditions" is a list of possible causes, not an explanation.

**Tier 1b (Category B, A if STUDY.md committed to the recorded protocol).** A deviation
between one seed sd and the Tier 1 threshold with a known directional cause in the protocol:
a short schedule against the recorded 1000-epoch result, or a final-epoch evaluation against
the recorded best-checkpoint value (`docs/conventions/quantization-and-cost.md`). The
reviewer checks three things:

1. Is the recorded protocol feasible within the STUDY.md budget?
2. Did the reference use it?
3. Would it plausibly close the gap, by an amount estimated from the record (the same
   configuration at both schedules, or both checkpoints of the same run)?

If all three are yes, the study runs the recorded protocol as the primary result, or at least
as a documented cross-check, before advancing. "A known limitation of the short schedule" is
not enough when the long schedule is affordable. A deviation with a known cause can be
removed by changing the protocol; a fluctuation cannot.
