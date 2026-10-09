---
campaign: 2026-10-08-discovery-350k
phase: PREFLIGHT (build half), wave 1 only
reviewer: critical-reviewer (solo), scoped re-review, round 2 of 2
date: 2026-10-08
previous: review/PREFLIGHT_critical_v1.md (ITERATE: A1, B1, B2, B3)
verdict: ITERATE
---

# PREFLIGHT critical review v2, wave 1

Scope: only whether the v1 findings are resolved, and whether the fixes introduced new problems.
This review was read-only apart from this file. Nothing was submitted and no kubectl call was made.

**Verdict: ITERATE.** A1, B1 and B3 are resolved. B2 is resolved inside score.py but not in the
glue. The score Job never passes `--score-attempt` to score.py, so a second score attempt writes to
`score-s1.json` again. That defeats the retry in the one case it exists for: a transient failure
followed by a valid rescore. The fix is one argument and one test. The fixes also introduced two
smaller problems, B4 and B5, which are documentation and semantics. Neither touches training code.

## 1. Checks on each v1 finding

### A1. INVALID recorded as "evaluation failed": resolved

`tools/evaluate_d350.py`:
- :84-90: the log is read and saved as `evidence/scores/<run>.s<k>.log` on Complete **or** Failed.
- :32, :91-94: the parser handles `INVALID[<class>]: <reason>`. The class is taken from the line,
  or from `eval/INVALID_REASONS.json` by prefix (:43-48); an unmatched reason is evaluator.
- :113-117: an evaluator or infrastructure result gets exactly one more attempt
  (`MAX_SCORE_ATTEMPTS = 2`, :31). A scientific result is printed with exit 3 (:122-123).
- :110-111, :119-121: a Failed Job with no INVALID line is infrastructure. It gets one retry, then
  exit 2.

`tools/harness.py`:
- :795-800: an output starting with `INVALID` is recorded as
  `{'type': 'evaluation', 'valid': False, 'reason': last}`, never as a measurement.
- :815-824: the interpret step is still queued.
- The class reaches the record only inside the `reason` string. That is acceptable.

Two qualifications:
- **No committed test.** v1 asked for a stubbed-kubectl test of evaluate_d350. No test file
  references it (`grep -rl evaluate_d350` finds only the tool itself). The rehearsal on a scratch
  copy is described in PROPOSAL.md:358-359, but no rehearsal log is saved under `evidence/`. I
  accept the fix from the code; the test is a condition (§3).
- **The last line is parsed literally** (:90). A valid score followed by any later stderr line
  would be read as "does not end with a score" and retried as evaluator. Two such results would
  lose a valid score as INVALID[evaluator]. This is a C finding (C10). Taking the last line that
  matches the score-or-INVALID pattern would remove it.

### B1. Non-finite attention entropy: resolved

- `eval/score.py:159-163`: non-finite head values become `None` (JSON null), with
  `n_heads_excluded` and `excluded_reason`.
- :164-166: if no head is finite, the mean is `None` with a reason.
- Tests: `test_nan_head_is_null_and_mean_is_over_finite_heads` (:416) and
  `test_nan_head_does_not_invalidate_a_valid_score` (:427).
- Residual (C11): any other non-finite value in the report still reaches `allow_nan=False` (:325)
  and gives INVALID[evaluator]. An example is a NaN replay AUC. The result can still never become
  scientific, so this is recorded only.

### B2. A first score file fixes the result for good: **not resolved in the glue**

The evaluator part holds:
- score.py writes `RUN_DIR/score-s<K>.json` (:357), with K from `--score-attempt` (:346-348).
- The same-attempt refusal is kept (:326-329).
- Tests: `test_second_attempt_writes_its_own_file_and_leaves_the_first` (:439) and
  `test_same_attempt_different_result_still_refused` (:452).

The glue part:
- evaluate_d350 passes `--score-attempt k` to prepare_score (:53).
- prepare_score uses k only for the Job name and record key (:119-120, :178).
- **The command line it writes into the Job does not pass the attempt** (`tools/prepare_score.py:133`):

```
exec python -u {dc.EVAL_DIR}/score.py {run_dir} --stop-epoch {stop} --expect-target {target} --cache {cache} --code /work/code
```

So every score Job, including `-s2`, writes `score-s1.json`. The case B2 is about runs as follows:
1. Attempt s1 ends in an internal error and writes an INVALID `score-s1.json`.
2. Attempt s2 computes a valid score.
3. score.py refuses it with "score file exists with a different primary result" (:329).
4. The run ends as INVALID[evaluator]. Under PROPOSAL §5 (:136-138), comparisons then stop.

This is exactly `test_same_attempt_different_result_still_refused`, reached through the Job. The
scratch rehearsal could not catch it, because a fake kubectl never runs score.py. Its "killed score
Job → retry → score" case passes only because a killed pod writes no file. A grep confirms that
no `--score-attempt` reaches the Job script.

The two re-prepared s1 handoffs behave correctly, because K defaults to 1:
- `handoffs/rh-3e9bfde2cdb78591f50eb073` (`kai-d350-sc-baseline-e-350k-s1-a1-s1`);
- `handoffs/rh-af994dc3b92cb79600c08de6` (`kai-d350-sc-reference-e-5m-s1-a1-s1`, `--expect-target 5000000`).

I decoded their ConfigMap tarball. It ships `d350_eval/score.py` at sha256 `9fddbdd67eea…`,
`INVALID_REASONS.json` at `5224c4db…` and `MANIFEST.json` at `22dca835…`. All three equal
`eval/MANIFEST.json` and the working files, recomputed. The two handoffs share bundle `5105469d7fae…`.
Only every s2 handoff is wrong.

### B3. Unclassified INVALID reasons: resolved, with one new semantic problem (B4)

- `eval/INVALID_REASONS.json` maps each reason that score.py emits to exactly one class. I checked
  each `need`/`Invalid` string in score.py:100-329 by hand, plus the two gap strings of
  `readout_pilot.records` (:81, :92) and the setup-trap line. The test
  `test_every_reason_score_can_emit_maps_to_exactly_one_class` (:486) enforces this.
- `classify` (score.py:77-85) returns evaluator on a miss or an ambiguous match.
- PROPOSAL.md:132-140: only the scientific class enters the branches.
- `eval/tests/test_score.py` passes 34 tests. I re-ran it in
  `/home/kaimoe/lab/.venvs/preflight-20261001`: 34 passed, 16.96 s.

### C1 and C2 (relaunch): resolved

`tools/relaunch_d350.py`:
- :50-61: a relaunch without a code change pins `relaunch-<arm>-a<n>` to the failed commit. For the
  `infra`, `relaunch` and `deadline` classes it tries `--resume-from`, and falls back to a fresh
  run if prepare_attempt refuses.
- :41-48: a repair commits on `repair-<arm>-a<n>` from the detached failed commit and starts fresh.
- :34-37: the HEAD check still refuses a workspace that is not at the failed commit.
- The resume refusals in prepare_attempt (:115-127) all come before any file is written. So the
  fresh fallback cannot collide with half-written files through `write_same`.

The harness wiring holds:
- The `{cls}` argument comes from `detail.class`, or the task name for a relaunch
  (`harness.py:979-981`).
- `workspace_command` runs for repair, investigate and relaunch (:872-893). So the HEAD check
  passes before an infrastructure relaunch.
- `tools/workspace_d350.py:22-24` refuses a dirty tree and checks out the failed commit detached.

## 2. New problems introduced by the fixes

### B4. "DIVERGED.json present" as scientific contradicts the scientific definition

- PROPOSAL.md:135-136 defines scientific as "the run trained and was read correctly, but no
  checkpoint meets the four conditions".
- A diverged run is not read at all: score.py rejects it at :247, before any record or feasibility
  check.
- `run_pack.py:219-222` treats divergence as an arm outcome, and earlier snapshots (epoch 500)
  exist. The run may therefore have held a feasible checkpoint before it diverged.
- Under the orchestrator decision, a diverged baseline would enter the "Baseline INVALID" branch
  (PROPOSAL.md:144), which reads "does not meet the budget non-degenerately at this horizon".
  That claim was never tested.

Divergence can reasonably be a scientific outcome. It is a different one, though. The decision also
changed the frozen evaluator's meaning without a matching PROPOSAL change.

### B5. PREFLIGHT.md still describes the superseded score handoffs

- PREFLIGHT.md:96-97 lists `handoffs/rh-75fce91d…` and `handoffs/rh-3b6cc77c…`. Both now sit under
  `superseded/score-eval-v1/`.
- PREFLIGHT.md:54 gives the score bundle as `a02c6d40…`; the shipped bundle is `5105469d7fae…`.
- The front matter still says "not reviewed".
- PROPOSAL.md:103 still says `INVALID: <reason>`, not `INVALID[<class>]: <reason>`.
- prepare_score's own text (docstring :20, brief `outputs` :168) still names `score.json`.
- A launch from the PREFLIGHT table would fail on a missing path rather than use the old
  evaluator, so this is a record defect, not a safety one. The phase artifact must still name what
  is submitted.

### C findings (recorded, not blocking)

- **C10.** evaluate_d350 parses the last non-empty log line literally (:90); see A1.
- **C11.** Other non-finite report fields still give INVALID[evaluator] (score.py:325); see B1.
- **C12.** PROPOSAL.md:139-140 says a second infrastructure failure "goes to the repair policy".
  evaluate_d350 instead prints INVALID[infrastructure] (exit 3), or exits 2 for a twice-killed
  pod. The harness repairs only Failed training Jobs (`harness.py:528-547`). The result is a
  recorded stop, not a repair. Either the text or the code should say the same thing. Jev:
  "overstated" (0.32, review).
- **C13.** The setup-trap line `INVALID: score job setup failed …` (prepare_score.py:47), and the
  "cache not ready" and "run dir missing" exits it covers, are classed as evaluator (unmatched).
  Infrastructure would be more accurate. Both classes get the same retry, so this has no effect on
  the branches.
- **C14.** `submit_score` submits before the state file is written (evaluate_d350.py:76-77,
  :114-115). A crash between the two re-submits the same Job name on the next poll. The effect
  depends on how `h.submit` handles an existing Job; not checked.

## 3. What would make this PASS

All of these can be checked without a third full review:

1. **B2.** `prepare_score.py:133` passes `--score-attempt {args.score_attempt}` to score.py, and
   a test asserts that the `-s2` job.json script contains `--score-attempt 2`. If the flag is
   added only for k > 1, the two s1 handoffs above stay valid. Otherwise they must be re-prepared,
   because `write_same` will refuse the changed bytes.
2. **A1 test.** A committed test runs evaluate_d350 with a stubbed `kubectl`. It must cover a
   Failed Job whose log ends in `INVALID[scientific]: no feasible checkpoint …` (exit 3, one
   attempt), and a Failed Job with an evaluator line followed by a valid s2 (metrics file written).
   The second case would have caught B2.
3. **B4.** One of two changes:
   - PROPOSAL §5 names divergence as its own scientific outcome ("diverged at epoch E; feasibility
     not read") and states how the baseline and reference branches treat it;
   - or DIVERGED.json goes back to a non-scientific class, so it cannot enter the
     "does not qualify" branch.
4. **B5.** PREFLIGHT.md lists the two current score handoffs and bundle `5105469d7fae…`.
   PROPOSAL.md:103 and the prepare_score docstring and brief name the `INVALID[<class>]` line and
   `score-s<K>.json`.

C9 from v1 still applies: lint has not been run with cluster access, and APPROVAL.json does not
exist.

## 4. Jev (advisory; audit `jv-2e3f0f9cd679474c84b00e0c330e5845`, jev-1.13.0)

| claim | source | Jev | my reading |
| --- | --- | --- | --- |
| A second score attempt writes `score-s2.json` | prepare_score.py:129-135 | absent (0.97) | Agree; B2 is open. |
| Only the scientific class, "no checkpoint meets the four conditions", enters the branches | PROPOSAL.md:132-140 | supported (0.91) | The text says so. The table also puts DIVERGED in scientific, which that text does not cover (B4). |
| A second infrastructure failure goes to repair | evaluate_d350.py:112-123 | overstated (0.32), review | Agree; C12. |

`lab_check_protocol` was not re-run. `matches_snapshot: false` (PREFLIGHT §7) stands.
