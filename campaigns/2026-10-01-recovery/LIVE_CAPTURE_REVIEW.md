# Live capture review

Date: 2026-10-01. Verdict: **PASS — saved observations only**.

Reviewed `captures/cluster-20261001T0513Z/receipt.json`, all five sanitized JSON
captures, `recovery-manifest.json`, `REPORT.md` and `RECOVERY_REVIEW_v2.md`.
No remote request, workload, model/array read, ML execution or collector change was
performed by this reviewer.

## Integrity and collection scope

Independently recomputed **5/5 stored SHA-256 values**, all matching the receipt.
The directory contains exactly the five reported captures and the receipt; the
capture files are regular files under that directory. Receipt SHA-256:
`c29c16132fd07d5e7b2ad46f19d4533452b601ac2a0add70d9ea7988b3aa93e4`.
Its recorded collection time is `2026-10-01T05:13:12.975881+00:00`.

All five recorded operations exited zero and exactly match the approved queries:
explicit context `nautilus`, namespace `cms-ml`, owner selector `user=kai`, and the
three allowlisted Job names. There are three Job reads and two pod reads, with no
logged `logs`, `exec`, mutation or submission operation. Both observed Jobs have the
expected name, namespace and owner label; their UIDs match the receipt's ownership
checks. The absent readout Job has no invented UID and dependent collection was
skipped.

The current collector hash matches the independently reviewed and operator-reported
executed identity, `23b0f0aa781e8955332c650244ec450a06ef1d9d73a8647119e2852aaa3a0f1d`.
The receipt records commands and source/stored hashes but does not itself embed that
collector hash. Raw stdout was not retained, so this review reproduces stored hashes,
not the raw-source hashes or the sanitization transformation from original bytes.
The saved objects contain the limited metadata/status projection; they are not full
Job specifications or immutable launch records.

## Supported observations

| Capture | Supported statement |
| --- | --- |
| `kai-confirm-onegpu-0924-e0c0a3-r2.job.json` | UID `1a00632f-62d5-4bd0-aa4e-4a9afb13c54f` has `Failed=True` and `FailureTarget=True`, reason `FailedIndexes`, transition time **2026-09-26T07:24:11Z**; `failedIndexes="0"`. This establishes the Job failure condition, not its underlying arm/error diagnosis. |
| `kai-chang0926-pilotb5-42abed.job.json` | UID `d1821ce8-49fd-4389-95ba-a59bc78ec4f8` has `Complete=True` and `SuccessCriteriaMet=True`, reason `CompletionsReached`, completion/transition time **2026-09-29T20:52:06Z**; `succeeded=1`, `completedIndexes="0"`. This establishes Kubernetes Job completion, not success/certification of every pilot arm. |
| Both `.pods.json` captures | The collector's filtered, UID-bound pod lists are empty at collection. No container logs were recovered through this capture. This does not explain why matching pods are unavailable. |
| `kai-chang0926-readoutb5-42abed.job.json` | The exact name/owner selector returned an empty list; the receipt records `job_observed_absent`. This is observed absence in that query, not evidence that the readout never ran, was deleted, or produced no outputs. |

The confirmation `status.failed=5` is a Kubernetes status counter; it is not evidence
that five scientific arms, or all twelve confirmations, failed. The b5 Job annotations
describe intended packing, fingerprint and RSS gates, not evidence that those checks
passed. Neither terminal condition validates a checkpoint or recovers the PVC's
per-run state.

## Findings and remaining evidence

No A or B finding blocks these bounded observations.

**C1 — Update the pre-capture report wording.** At review, `REPORT.md` still said live
terminal evidence was unavailable and requested terminal Job states as missing.
Link this capture/review and replace those statements with the exact observations
above, while preserving the outstanding log/PVC/artifact requirements. This is a
reporting correction, not new execution authorization.

Outstanding evidence remains the actual arm logs, all confirmation pointers and
their preserved generations, five b5 terminal outcomes/snapshots or actual failure
markers, actual readout certification/entropy outputs, and cache/run source-data
identities. Checkpoint integrity/recoverability and scientific outcomes remain
unestablished. The capture does not recover a valid immutable handoff record or its
binding, so legacy context remains unavailable under that workflow. Synthetic
`dry_readout_b5*` fixtures remain excluded.

Chang K1 is not cleared. The complete b5 readout and Kai's (c)/(d) decision remain
pending. This PASS makes no decision about PVC access, resume, readout submission,
training, new launches or scientific advancement.
