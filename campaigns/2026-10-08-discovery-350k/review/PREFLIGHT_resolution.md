# PREFLIGHT resolution after review v2 (orchestrator, 2026-10-08)

Two review rounds were run, which is the campaign's cap (PROPOSAL §5 and harness design §4.4).
Review v2 listed four checkable conditions for PASS. Each was applied and checked here instead of
in a third review. Nothing was waived. No numerical or authorization check is affected, because
no score exists yet.

| v2 condition | Change | Checked by |
| --- | --- | --- |
| 1. B2: pass `--score-attempt` to score.py | `tools/prepare_score.py`: the score Job command adds `--score-attempt k` for k ≥ 2, so attempt-1 handoffs keep their form. | `tools/tests/test_evaluate_d350.py::test_evaluator_failure_then_valid_second_attempt`. The attempt-1 job.json has no flag, the attempt-2 job.json contains `--score-attempt 2`, and a valid second attempt is recorded as score_attempt 2. |
| 2. Committed evaluate test with a stubbed kubectl | `tools/tests/test_evaluate_d350.py`, 4 tests. They run the real prepare tools and `harness.py submit` on a throwaway copy, with a stub kubectl. | `python3 -m unittest campaigns/2026-10-08-discovery-350k/tools/tests/test_evaluate_d350.py`: 4 OK. Cases: a scientific INVALID from a Failed Job; an evaluator failure followed by a valid second attempt; diverged, not retried; a killed score Job retried once, then an evaluation failure. |
| 3. B4: divergence | A separate class, `diverged`, in `eval/INVALID_REASONS.json`, never retried. PROPOSAL §5 defines its handling: evidence against a candidate; for the baseline or reference, the validity check cannot be evaluated, so it goes to Kai. | `eval/tests` 34 passed (the class-table test asserts four classes and the diverged prefix). |
| 4. B5: stale text | PREFLIGHT.md handoff table and bundle row, PROPOSAL §4 INVALID wording, prepare_score docstring and handoff brief strings. | Read back. Current score handoffs: rh-18ad2899…, rh-23967107… (VALID; lint OK with the live node map). |

Found while applying these: a score-Job setup failure, which happens before score.py runs, printed an
unclassified `INVALID:` line, which would have counted as evaluator. It now prints
`INVALID[infrastructure]: score job setup failed …`.

C10-C14 (minor, in v2) are carried as known issues in BRIEF.md and HANDOFF.md where they affect
operation. None blocks wave 1.
