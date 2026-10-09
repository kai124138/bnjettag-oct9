# Rehearsals on scratch copies of this campaign (2026-10-08, orchestrator)

None of these touched the cluster. Object creation went to a fake kubectl. Lint used the real,
read-only node lookup where noted.

1. **Scheduled repair, one `harness.py tick`, 585 s.** Real lint.
   - A constructed exit-76 Job and pod record was classified as deterministic.
   - `workspace_d350.py` checked out commit d4f66592.
   - A scripted stand-in agent appended a comment to `bnhgq2/ablation.py`.
   - The copied-tree pytest suite passed.
   - The change was committed by "BNJetTag harness" on `repair-baseline-e-350k-s1-a2`.
   - Attempt 2 was prepared, linted and submitted through the budget check: 3 creates (code
     ConfigMap, handoff ConfigMap, Job).
   - Ledger: a submission entry and a decision entry recording "changed: bnhgq2/ablation.py".
2. **Evaluate step, with the evaluator and glue as fixed after review v1.**
   - A Failed score Job with `INVALID[scientific]` was recorded as INVALID[scientific], exit 3.
   - An evaluator INVALID twice gave two score attempts, then INVALID[evaluator].
   - A killed score Job was retried once, and the second attempt's score was recorded.
3. **Earlier, before the fixes, recorded for the history.**
   - The evaluate step called prepare_score without the run's target, and prepare_score refused
     the reference. Fixed.
   - The relaunch commit failed with git exit 128 because no committer identity was set. Fixed
     with an explicit harness identity.
   - Stale score handoffs blocked re-preparation, because attempt identities are immutable.
     Resolved by archiving under `superseded/`.
4. **Headless `claude -p` from a cron-like environment**: OK, USD 0.13 for a one-word reply.
5. **Non-interactive NRP login refresh in a cron-like environment**: OK. The ID token was renewed
   for 30 minutes from the cached refresh token.

## Readiness rehearsals requested before approval (2026-10-08, later)

6. **Decision path with the configured reasoning runner (headless `claude -p`).** Scratch copy;
   wave 1 submitted through `harness.py submit`, using a fake kubectl for creation and the real
   read-only lint. The finished Jobs and score logs are constructed: baseline 0.3127, reference
   0.6412. These are not measurements.
   - **First run.** The copy's approval said "rehearsal only". The interpreter checked
     provenance and escalated (NEEDS KAI) instead of proceeding. It also found two defects, both
     since fixed: the secondary measurements were not retrievable, and the `ideas.json` protocol
     hashes were stale.
   - **Second run.** The copy was labelled as a rehearsal in its HANDOFF, and the C1 methods note
     was on record.
     - Passes 1-4: score Jobs submitted and pending; no interpretation while only one score
       existed.
     - Pass 5: both scores recorded, and exactly one interpretation queued.
     - Pass 6, 209 s: the interpreter applied the §5 validity check (gap 0.3285, baseline
       below 0.50: the problem is shown) and called the 0.0236 rise from epoch 500 to 1,000
       "recovery under continued training with the existing schedule". It wrote
       `plan/specs/C1.md` and plan `d350-after-wave1-20261008-c1-01` (PROCEED), and the
       dispatcher queued one `implement C1` task.
     - Passes 7-8 (replay): nothing new; the implement task waits with a single notice.
       Agent invocations: 1.
7. **Scientific-setting refusals with this campaign's configuration.** Scripted agent, real
   repair check.
   - **(a)** A batch-size edit in the arm's config was refused as outside the allowed paths.
     The workspace was restored.
   - **(b)** Halving the peak learning rate inside `bnhgq2/ablation.py`, an allowed file, was
     refused by the settings fingerprint: `lr 0.003 -> 0.0015` and `ebops_after_one_step
     9496211 -> 9392275`, in 58 s. The diff was kept as evidence and the workspace restored.
   - No Job was created in either case.
   - Found and fixed along the way: the workspace snapshot included `.git`, whose read-only
     objects blocked a second snapshot; a refused change stayed in the workspace.
