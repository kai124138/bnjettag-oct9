## 2026-10-06 — Why do binary-weight networks collapse at 350k EBOPs? (pilot program R1 launched)
Question: Which of H1 controller input, H2/H2′ budget headroom, H3 attention starvation, H4 squeeze timing, H5 weight prunability explains the 350k collapse?
Design: 24 single-arm 500-epoch pilots on RTX 3090, bundle 98dd2875; STUDY [A1]–[A5] pre-registered (protocol snapshot 65e4331b); 3 review rounds, arbiter v3 PASS; CPU gate PASS.
Result: pending (submitted 2026-10-06 06:53 JST; 2 Running, 22 Pending at launch).
Interpretation: none yet. R1 reads are leads only. The readout waits for the PROGRAM.json mirror (Q1/Q3), readout re-prep (Q2), the R2/R3 configs bundle (Q5) and Kai's K-1.
Ops: campaigns/2026-10-05-pilot-program/{RUN.md,JOURNAL.md,STUDY.md,review/}; .claude/memory/decisions.md 2026-10-05.
Check: spend ≤ 144 GPU-h; no readout before Q1–Q5.

## 2026-10-08 — Does the binary N=64 E tagger lose accuracy at 350k EBOPs within 1,000 epochs on full data, and is it regained under continued training? (discovery-350k wave 1 launched)
Question: wave-1 validity check of campaigns/2026-10-08-discovery-350k (PROPOSAL §5). Does the baseline E-350k-C lose accuracy relative to the E-5M reference, and is accuracy at 350k regained under continued training with the existing schedule?
Design: two RTX 3090 Jobs, seed 1, full data (558k/62k), 1,000 epochs, frozen evaluator eval/score.py (best feasible validation top-1), hard GPU bound 26.24 GPU-h each; approval 9496cf63.
Result: pending (submitted 2026-10-08 09:30 UTC; both pods Pending at 09:31).
Interpretation: none yet. The rehearsal scores in evidence/rehearsal-2026-10-08.md are constructed and are not results.
Ops: campaigns/2026-10-08-discovery-350k/{RUN.md,BRIEF.md,HANDOFF.md}; cron tick every 15 min.
Check: `kubectl get jobs -n cms-ml -l campaign=discovery-350k-20261008`; NOTIFY.log.

## 2026-10-05 — Does the option-(c) code pass its CPU gate before any GPU pilot?
Question: Do the full unit suite, the 58-config build/step/reload/floor/trace-cadence gate and the shared-kernel pairing pass on bundle 6919462c (42abed + patches 0032/0033)?
Design: One CPU Job, kai-chang1002c-cpugate-691946 (8 CPU / 24 GiB, 4 h deadline, no GPU), submitted via run handoff rh-bf4170d542600fef18cb189a after a solo critical-reviewer PASS and Kai's approval.
Result: pending (submitted 2026-10-05T00:10:00Z).
Interpretation: none yet. A PASS clears only the engineering gate. Before any pilot, the floor re-trace (B1), amendment gates (B4), the GPU product choice (B5) and Kai's pilot authorization are still needed.
Ops: campaigns/2026-10-02-chang-option-c/RUN.md; review/PREFLIGHT_critical_v1.md; local/2026-10-05-execution/cpugate-approval.json.
Check: VERIFY requires exactly 2 known skips and every 0032/0033 test passed.

## 2026-10-01 — Can the recovered evidence support the next diagnostic and hardware gates?
Question: Recover missing controller histories and the exact current hardware candidate without changing historical runs.
Design: Existing immutable CPU b5 readout, one-A10 no-training confirmation probe, and bounded read-only file transport through the owned readout Pod.
Result: Five raw b5 histories (880,343,029 bytes) match fresh source SHA-256; eight A02 artifacts recovered with exact historical model/config and final stored provenance matches. B5 readout remains Running with partial certification. The confirmation probe failed before input checks/inference because its output parent was absent; no retry or training occurred.
Interpretation: Evidence recovery advanced; no new tagging-performance result, resume clearance or hardware measurement. Option(c) remains selected. B5 wrapper telemetry export remains incomplete because every history exceeded8MiB; raw recovery does not rewrite that failure. Engineering/review agents hit a service usage limit, leaving implementation and scientific review blocked.
Ops: campaigns/2026-10-01-recovery/readout-preparation/RUN.md; confirmation-replay-preparation/REGRESSION_TICKET.md; captures/a02-hardware-evidence-20261001/receipt.json. GitHub main1c9f933340aa9162f13bee7fd2f3bdec4e1a0fbe; two file readbacks match.
Check: Source hashes/stat match; scientific and hardware gates remain pending.

# Experiment log

The earlier memory log was absent at this path in the canonical WSL workspace.
This entry records the October 1 work; historical campaign records remain in place.

## 2026-10-01 — What evidence survived the failed confirmation queue and completed b5 pilot?

Question: Recover the missing saved logs/checkpoints and distinguish terminal progress
from checkpoint certification and full scientific completion.

Design: Execute the explicitly authorized frozen recovery-only reader once; independently
verify its bounded transfer and export; inspect metadata/logs without loading models or
arrays. Preserve historical records and separately record the selected Chang remedy.

Result: 253 files (63,514,020 bytes) recovered with independent transport PASS, including
all 17 current state/model/optimizer generations and five b5 epoch-500 snapshot states.
The reader exited zero without restart. Confirmation progress is 280–318/1,000 epochs;
logs show selected-checkpoint reload failures but do not uniquely identify the final
Job-triggering arm. Actual b5 certification/entropy outputs are absent at the expected
paths; activation histories were outside the initial recovery scope. No new scientific
metric or checkpoint reload was computed.

Interpretation: Missing evidence is substantially recovered. Resumability and complete
b5 interpretation remain unverified. Kai explicitly selected option (c), traced-cost PID,
at recorded time 06:00:02.706672Z; K1 remains triggered pending readout, dated amendment,
new frozen revision, preflight and replacement pilot. Production remains blocked.

Ops: campaigns/2026-10-01-recovery/PVC_TRANSPORT_REVIEW.md; PVC_READOUT_REVIEW.md;
reader-preparation/RUN.md; local/2026-10-01-execution/chang-option-c-decision.json.
Reviewed public reconciliation is main commit 7f66b7e184e021403bc167f45b2dd317bcd3d6b6;
all four remote files were read back exactly. Draft code PR1 remains unmerged.

Check: Verified byte/hash chain and source-cited metadata inventory; no scientific gate
clearance or current-candidate hardware claim. New b5 readout preparation is in progress.

## 2026-10-01 — Is a bounded read-only PVC export route ready for authorization?

Question: Recover saved evidence when no existing pod mounts kai-data, without
changing its contents or treating recovery as a scientific launch.

Design: Freeze a campaign-local reader, receiver and guarded adapter with exact
17-run/cache/log/checkpoint scope, immutable code, read-only PVC, no GPU, 2 GiB
source-read budget, 30-minute reader runtime and 35-minute Job deadline.

Result: Independent engineering preparation PASS, 11 Python 3.12 tests, a tiny
synthetic end-to-end transfer and live manifest lint pass. Source-byte accounting
and pending-approval guard findings were fixed before the final cbb3dec6 bundle.
Preparation SHA is 8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a.

Interpretation: The concrete package is ready for Kai's action-time approval of
the recovery-only adapter and handoff exception. Actual PVC readability, scheduling,
artifacts, checkpoint validity and all scientific gates remain unproven. No approval
record, workload, forwarding process or training operation was created.

Ops: campaigns/2026-10-01-recovery/reader-preparation/PREPARATION.md, ACTIVE.json,
REVIEW.md and live-lint-cbb3dec6.json. Superseded frozen drafts remain in place.

Check: Frozen payload and manifest hashes independently verified; actual source-byte
limits, invalid approval rejection and transfer integrity exercised with fixtures.

## 2026-10-01 — Can the public status be updated from the recovered Job evidence?

Question: Replace stale unknown cluster status with reviewed observations while
preserving the established scientific record.

Design: Reconcile the four public status files against the saved exact-Job and PVC
captures, independently review the changes, and publish only that file allowlist.

Result: Independent operational review PASS. Main commit
932e0fe855fbdc9ca40af07d9d28bf3d23ccfcd5 publishes the four reviewed files. The remote
changed-file set and every published byte match the local plan. Scientific values
and all 16 earlier source records remain unchanged; draft compatibility PR 1 stays
open and unmerged. No new cluster workload was launched.

Interpretation: The report now records confirmation failure and b5 Job completion
without asserting arm outcomes, valid checkpoints, a completed readout or a cleared
scientific gate. The next evidence step remains authorized read-only file recovery.

Ops: campaigns/2026-10-01-recovery/LIVE_PUBLICATION_REVIEW.md and
local/2026-10-01-execution/live-publish-receipt.json.

Check: Four remote file hashes and the exact changed-file set verified; unrelated
local confirmation and constituent-screen document changes excluded.

## 2026-10-01 — Does restored NRP access recover terminal confirmation and b5 status?

Question: Separate missing client authentication from missing training evidence.

Design: Complete institutional device authentication on the home PC, run the reviewed
read-only collector for the three exact Jobs, and inspect existing kai-data access.

Result: Namespace access succeeded. The confirmation Job records FailedIndexes at
2026-09-26T07:24:11Z; b5 records Complete at 2026-09-29T20:52:06Z. Matching pod lists
were empty and the exact readout-b5 query returned no Job. Five saved derivative
hashes and the Job UID bindings passed independent review. The 100Gi RWX kai-data
PVC is Bound; a separate namespace query found no pod mounting it.

Interpretation: Terminal orchestration states are recovered. The failing arm,
checkpoint validity, all five b5 terminal outcomes and readout contents remain
unknown. Empty current listings establish no deletion cause or execution history.
Chang K1 and Kai's c/d choice remain pending. A finite read-only export route is
being prepared for review; no launch or training-handoff exception is inferred.

Ops: campaigns/2026-10-01-recovery/captures/cluster-20261001T0513Z/receipt.json,
LIVE_CAPTURE_REVIEW.md and captures/access-20261001T0518Z/receipt.json. Client and
server now both v1.34.11; the downloaded client checksum was verified. Browser
launch required the signed-in Windows desktop rather than background session 0.

Check: Successful authenticated API reads; all five stored hashes independently
reproduced. No new cluster workload, training, resume or Mulder connection.

## 2026-10-01 — Can evidence recovery and code compatibility unblock the remaining schedules?

Question: Recover missing confirmation/b5 evidence and complete the independent local
work needed before the remaining scientific and hardware stages.

Design: Prepare a read-only collector restricted to the three recorded Jobs and 17
run paths. Capture both actual code trees, review the merge design, preserve public
defaults and exact configs, and compare original/candidate behavior using bounded
CPU fixtures. No scientific run or synthesis is part of these engineering checks.

Result: The recovery collector has independent PASS with 21 tests. The merge has
bounded engineering PASS: 21 contracts, 100 paired config builds and 96 paired reload
combinations. Independent NumPy comparison of all saved probe pairs found maximum
absolute difference 0.0 within 1e-7. GitHub draft PR 1 contains 61 verified files at
commit e56fd7361f0299c1721aa053506d1eabc092cdba. The training-results update is already
on main at 6da5003809a3ccd371ec6ba83a09276a594ab9ab. No new training result was computed.

Interpretation: Live evidence recovery still needs an NRP context or authorized
artifact export. Chang K1 has fired; b5 readout and Kai's (c)/(d) decision remain
pending. Historical metric/calibration checks and 74 unattributed checkpoint paths
prevent a full migration claim. Current candidates still need successful hardware
validation and a configured trusted Mulder route. Earlier HLS evidence identifies
a compiler crash, not a proven directive-level root cause.

Ops: `campaigns/2026-10-01-recovery/REPORT.md`, `SOURCE_DIAGNOSIS.md` and
`RECOVERY_REVIEW_v2.md`; `campaigns/2026-09-26-code-line-merge/PREFLIGHT.md` and
`review/PREFLIGHT_critical_v2.md`; `local/2026-10-01-execution/STATE.json` and
`publish-receipt.json`. Resource limits were per invocation; cumulative session CPU
compliance was not established and must not be inferred.

Check: Recovery regression suite and independent review PASS; all 217 engineering
rows and saved probe pairs independently checked; remote commit file set and all
61 file contents read back exactly; unrelated local result-document changes preserved.
