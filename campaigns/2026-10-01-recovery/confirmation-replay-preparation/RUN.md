# Confirmation diagnostic run — 1 October 2026

Status: **Failed before input checks, model loading or inference**. The init handoff
passed; the main container exited1 at06:47:50Z, and the Job became Failed at06:48:41Z.
No retry was submitted. The [failure ticket](REGRESSION_TICKET.md) records the required
startup fix. [Observation 02](../captures/confirmation-replay-20261001T0645Z/observation-02/receipt.json)
and [full terminal logs](../captures/confirmation-replay-20261001T0645Z/final-logs/receipt.json)
preserve the failure.

At startup, [Observation 01](../captures/confirmation-replay-20261001T0645Z/observation-01/receipt.json)
records the init container running. No scientific result was produced.

Job `kai-confirm1001-replay-a02s3-r1`, UID `e78483f4-b74c-4fed-b7fa-e4b771e762a3`,
owns Pod `kai-confirm1001-replay-a02s3-r1-mjbzz`, UID
`ea50754f-c194-4a9f-9b4f-eeb12a4628bd`, assigned to `gpu-15.nrp.mghpcc.org`.
The final handoff is `rh-a15040ccc47283093ee9c734`, full record SHA-256
`a15040ccc47283093ee9c734e1ccb95448fad927f5bb791deb0137608e2aa41d`.
The source ConfigMap UID is `9b604d02-eac4-41c1-8967-5b345499738a`; the handoff
ConfigMap UID is `358d68ae-e8b8-40ce-a760-7a63ea16ede2`.

The [independent preparation review](REVIEW.md) passes. The separate final review
agent reached its service usage limit. The operator completed a
[deterministic identity audit](FINAL_IDENTITY_REVIEW.md) against the independently
reviewed candidate; no execution, data, config, helper or source field changed.
This is disclosed as an operator audit, not a second independent agent review.
[Authorization](../../../local/2026-10-01-execution/confirmation-replay-authorization.json)
records the existing task and one-GPU allowance. No additional permission was requested.

Action-time lint passed and the launcher exited zero after creating the two immutable
ConfigMaps and Job. The [event ledger](handoffs/rh-a15040ccc47283093ee9c734/events/)
preserves pre-create intent. The launcher was not replayed. Admission emitted the
existing init CPU/memory ratio warnings; creation and scheduling succeeded. The Pod
also received init ephemeral-storage defaults of request0/limit50Gi; actual objects
are preserved. This addition must remain disclosed during reception, with exact
comparison against the reviewed handling of the same admission defaults.

The reviewed scope is one A10, 4 CPU, 16 GiB RAM, 12 GiB main ephemeral storage,
30-minute Job deadline and backoff0. It performs four full-validation inference
passes on one retained A02-s3 artifact, across three loads and two serial processes.
No training, optimizer restore, source checkpoint write, tolerance change or automatic
retry is performed. Original source member bytes and recovered config are unchanged
inside a separately identified diagnostic envelope. New outputs belong only under
`/data/confirmation-20260923/diagnostics/replay-a02s3-20261001-r1` and its immutable
provenance directory. Writable PVC access supports those outputs; source nonmutation
is enforced by commands and before/after checks rather than a read-only mount.

A successful replay means that the historical failure was not reproduced under the
recorded diagnostic runtime. It cannot establish the original runtime or authorize
resume. A mismatch will preserve the original tolerance and comparisons. Scientific
interpretation, training repair and production gates remain pending.

## r2 preparation — 2 October 2026

Status: prepared, **not launched**. Pending handoff `rh-50efbf03d0ead6e50675dff9`
passed `nrp_doctor lint` ([record](live-lint-rh-50efbf03.json)); cluster status is in
[live-resources-rh-50efbf03.json](live-resources-rh-50efbf03.json) (exit 1 from warnings on
the already-captured b5 and r1 failed Jobs only; nothing of ours running or pending).
Final handoff `rh-dccc5c324f444ad1271599ca` carries the cleared diagnostic gate and the
[r2 authorization](../../../local/2026-10-02-execution/confirmation-replay-r2-authorization.json).
r1 reviewed candidate files are kept in `candidate-r1/` and `CANDIDATE-r1.json`.
Final validation, final lint and submission were stopped by the session permission
classifier as a shared-cluster action and are left to Kai.
