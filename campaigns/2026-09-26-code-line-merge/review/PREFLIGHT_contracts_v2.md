# Static contract-fixture re-review — v2

Date: 2026-10-01. Verdict: **provisional ITERATE — contract fixtures only**.

This re-review is limited to the five findings in `PREFLIGHT_contracts_v1.md`.
It inspects source only; no worker, ML evaluation, array experiment or network
operation was run. Runtime evidence remains with the owner's coordinated run.
This is not the final PREFLIGHT verdict and does not assess parent-runner
provenance, builds, reloads, historical metrics or hardware readiness.

Inspected `preflight_worker.py` SHA-256:
`51d4957ea7b6e8d570d40bb64db88786718292b6c9c4551fd7a2829a0e190593`.
Inspected `preflight_merge.py` SHA-256:
`b60d942927a34915554eab0168a1ee34a51e3f786d83fc21e806e94fee814c28`.

## Resolution of the five prior findings

| Prior finding | Static disposition | Evidence |
| --- | --- | --- |
| 1. Inactive pT cap | Resolved in fixture design | `preflight_worker.py:243` places one observed class-zero training jet in the high-pT bin. Lines 290–296 require different capped/uncapped weight hashes, an occupied bin and its pre-cap ratio above five. The research/candidate pairing remains in the parent. |
| 2. Teacher path/input dispatch | Resolved in fixture design | `teacher_contracts` at line 406 uses distinct training/validation arrays. Lines 436–445 assert the training prediction input, batch/verbosity arguments, exact local or downloaded checkpoint path, `compile=False`, and downstream array/output dispatch. The artifact client remains fake. |
| 3. Candidate aliases silently skipped | Resolved in fixture design | Lines 180 and 190 require the conversion alias and each declared wrapper when `is_candidate` is true. `preflight_merge.py:114` sets that flag from the candidate source path. Signature, callable identity and package-return assertions remain. |
| 4. Target schedule/final-target selection | Partly resolved; A1 below remains | Lines 310–312 exercise actual `ablation.training_target` at each declared boundary. `delivered_contracts` at line 456 exercises actual `train.train` delivery, including at-cap, over-cap rejection, infeasible fallback and minimum-cost checkpoint cases. It does not exercise `ablation.run_training`'s separate final-target feasibility decision. |
| 5. Adapted evaluation entry-point wiring | Resolved for the bounded held-out fixture | `ptw_entry_contract` at line 498 invokes actual pT evaluator `main`, verifies explicit checkpoint/held-out paths, reads checkpoint-specific preprocessing, and checks saved label/score/pT arrays and output path (lines 514–524). Metrics and persistence are stubbed; twelve backing rows are used. `--skip-val` means this fixture does not establish internal-validation dispatch, and no such evidence is credited here. |

## A1 — Original final-target filtering case still lacks executable coverage

The study's Selection fixture explicitly promises final-target filtering. The
original v1 finding identified the distinction inside
`publication/code/hgq2/bnhgq2/ablation.py:252` and `:290`: PID training can use a
temporary scheduled target, while checkpoint feasibility must use the final
target. The new target-boundary helper check and fixed-cap delivery check are
useful, but neither invokes that decision in `ablation.run_training`.

For example, an epoch cost of 750,000 under a temporary target of 1,000,000 and
final target of 350,000 must not enter `best_feasible`. Replacing the actual
feasibility expression with a comparison against `pid.target_ebops` would still
pass the inspected fixtures. This is an executable-coverage gap, not an observed
pipeline defect; the inspected production expression is correct.

Resolve with one bounded fabricated invocation of the actual ablation path, with
model, optimizer step, metrics and persistence stubbed, asserting scheduled PID
target and final-feasible selection separately. Include the at-final-cap case or
retain its established equivalent assertion. Compare the captured original and
candidate under the existing harness. Alternatively record this required row as
explicitly incomplete; do not claim all five findings resolved. This repeats the
original declared selection gate and adds no training experiment.

## Retained positive coverage and limits

Existing absent/disabled/misaligned pT, tracking, public CLI, tie ordering,
fixed-cap admission, dtype, batch ordering and stable constituent-sort assertions
remain. The revised fixtures materially improve clipping, teacher and evaluator
dispatch, mandatory imports, scheduled targets and delivered checkpoint coverage.
No B or C findings are added in this bounded re-review. Runtime PASS, complete
merge compatibility and scientific/hardware validation are separate conclusions.
