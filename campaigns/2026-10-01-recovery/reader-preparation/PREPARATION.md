# Recovery reader: concrete approval package

Status: [critical engineering review PASS](REVIEW.md); **authorized and submitted once**.
The receiver verified transfer of 253 files and completed the local export. The
reader exited zero and the Job completed; independent transport and metadata/log reviews are complete.
[RUN.md](RUN.md) contains approval, object identities and transfer receipts.
The submitted package is
[`frozen/cbb3dec6a6f3e04766b1973b39442ea2f9f16cf28ce3c323600ad037cf3ac75e`](frozen/cbb3dec6a6f3e04766b1973b39442ea2f9f16cf28ce3c323600ad037cf3ac75e).
[ACTIVE.json](ACTIVE.json) records current hashes and superseded drafts.

| Artifact | SHA-256 |
| --- | --- |
| Preparation record | `8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a` |
| Frozen code/scope/brief bundle | `cbb3dec6a6f3e04766b1973b39442ea2f9f16cf28ce3c323600ad037cf3ac75e` |
| Job manifest | `c9f2850798723ad3c4de5c53eef156028bcec8ef765ecb46f9a72887483b995d` |
| Immutable ConfigMap manifest | `edcbdab48841b0b969ef8076b241cb8be5c3a8a31cab033605bdb868f67a880a` |

The one Job is `kai-recovery-ro-1001-cbb3dec6a6`; its code ConfigMap adds `-code`.
Both are in `cms-ml`. The official Python image is pinned to verified digest
`sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`.
The PVC is the observed `kai-data` UID `c5be55ec-3362-40a9-b283-f8d0750dcf95`.
The adapter rechecks its live UID and refuses an existing Job, ConfigMap or submission
intent; it does not overwrite or adopt them.

The Job requests **100m CPU / 256 MiB RAM**, with **1 CPU / 512 MiB** limits and no
GPU. It mounts the PVC and code read-only, disables token automount and elevated
privileges, and uses bounded ephemeral scratch. It reads at most **2 GiB** of
allowlisted evidence. Runtime is **30 minutes**, with a **35-minute Job deadline**,
zero retries and one-hour terminal retention. Verified completion stops it early.
There are no source writes, permission changes, full dataset exports, model loads,
training steps or readout calculations. No Service, deployment, RBAC or persistent
monitor is created.

The approved recovery-only scope is:

> Authorize this exact finite recovery-only Job and immutable ConfigMap, the reviewed
> campaign-local adapter, and a loopback-only port-forward to export the 17 runs,
> three cache identity records, matching logs and selected checkpoint/readout files.
> For this reader only, allow the read-only bootstrap route instead of the training
> handoff's already-exported cache prerequisite and writable provenance init. Keep
> training and scientific gates pending; allow no resume, training launch or PVC write.

This exception is required by [the handoff rules](../../../docs/infrastructure/run-handoff.md),
which explicitly require separate approval to create a pod for missing cache identity.
The adapter has an offline default. Submission requires `--submit` and an explicit
approved record with a real UTC timestamp, actual Kai authorization reference and
the exact preparation hash. Pending/placeholder records are rejected. A guard
rejection remains a blocker; the global hook and training launcher are unchanged.
Actual authorization is the separate dated record
`local/2026-10-01-execution/recovery-reader-approval.json`, bound to this preparation
hash by the submission intent. The frozen brief and pending annotation remain the
original preparation snapshot; they are not rewritten after approval.

Both adapter and receiver require `--preparation` to name the `preparation.json`
file, not the frozen directory. An initial directory-valued invocation failed before
cluster operations or an intent; the corrected invocation created each object once.

Local validation: **11 focused tests pass under Python 3.12.13**, covering traversal,
symlinks/FIFOs, credential filtering, exact pointer selection, source mutation,
rejected-byte accounting, size/deadline/reuse limits, transfer corruption/truncation,
live object/mount identity and placeholder-approval rejection. Offline invocation of
the exact frozen adapter validates the package and existing `nrp_doctor.lint_job`
with no errors or warnings. No cluster operation is part of these tests.
Independent critical review repeated all 11 tests and passed a tiny synthetic
end-to-end transfer. The [exact frozen manifest also passed live lint](live-lint-cbb3dec6.json)
at 05:34:39 UTC. No real model or dataset was used in the transfer fixture.

The [operation guide](README.md) gives the finite submission, UID-bound forwarding,
receiver and existing-exporter sequence. Hash-verified transport can expose missing
or mismatched evidence; it cannot establish historical launch context, certify a
checkpoint, clear Chang K1, choose (c)/(d), or prove current-candidate hardware success.
