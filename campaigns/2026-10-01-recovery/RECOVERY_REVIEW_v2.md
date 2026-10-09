# Recovery collector re-review

Date: 2026-10-01. Verdict: **PASS — bounded engineering collector review**.

Reviewed `recover.py`, `test_recover.py`, `FIXES.md`, `REPORT.md`, the unchanged
allowlisted manifest, and the original `RECOVERY_REVIEW.md`. Collector SHA-256:
`23b0f0aa781e8955332c650244ec450a06ef1d9d73a8647119e2852aaa3a0f1d`.
No collector/pipeline edits, remote access, model or array loading, ML execution,
scientific recomputation, or real credential access occurred.

Validation command:

```sh
python3 -m unittest discover -s campaigns/2026-10-01-recovery -p 'test_recover.py' -v
```

**21/21 tests passed.** Independently repeated the original redaction, unavailable
Job and advancing-pointer regressions using fabricated strings/files and mocked
subprocesses. These independent checks also passed; no fixture token was printed.

| Previous finding | Resolution and evidence |
| --- | --- |
| A1: ordinary credential forms survived sanitization | **RESOLVED.** `recover.py:43-79` handles complete authorization scheme/value pairs before generic redaction and sanitizes parsed JSON structurally. Independent checks confirmed removal of synthetic Bearer-header and quoted API-key values, including a Kubernetes-style status message, while serialized JSON remains valid. The exporter detects credential-bearing parsed JSON at lines 351-359 and refuses byte-for-byte export. The suite verifies refused pointers are not followed. |
| A2: unavailable Job reads disabled UID binding | **RESOLVED.** `owned_pod` now requires a nonempty matching UID (`recover.py:170-175`). Valid Job responses require one observed UID; failed/malformed reads and successful absence have distinct receipt states and skip dependent queries (lines 247-260). The independent failed-Job fixture made exactly four mocked calls: one local context check and three Job reads, with no pod/log requests. Suite tests additionally cover positive and mismatching UID bindings and observed absence. |
| A3: copied pointer and selected generation could disagree | **RESOLVED.** `recover.py:390-405` selects only from accepted exported pointer bytes and records that pointer's SHA-256 with the generation. In the independent race fixture, the live pointer advanced to `epoch-0002` after capture; the export consistently retained `epoch-0001`, its state and its pointer hash, without substituting the newer generation. File/directory stability and incomplete generation states are recorded (lines 304-316 and 407-428). A `finally` receipt preserves partial evidence on interruption (lines 437-444); disappearance/change cases are covered by the suite. |
| B1: terminal/source/preprocessing records omitted | **RESOLVED.** `recover.py:385-387` includes all six named missing records within the existing seventeen approved run paths. The independent fixture verified byte-exact copies of `source_manifest.json`, `input_std.json`, `COMPLETE.json`, `TRAINING_COMPLETE.json`, `VERIFIED_COMPLETE.json` and `screen_result.json`; the suite also checks their receipts. |

No unresolved A/B findings or new findings remain in this bounded review. Exact
Job names, explicit context, namespace `cms-ml`, read-only `get`/`logs` operations,
new-output requirements, and traversal/symlink checks remain in place. The report
now describes the actual UID requirement, pointer preservation, expanded artifact
coverage and partial-evidence limitations consistently with the code.

This PASS validates the reviewed collector's engineering behavior; it does not
assert that live evidence has been collected, that a mounted source is an atomic
snapshot, or that a checkpoint is valid/recoverable. Sanitization remains a bounded
set of rules, and filesystem checks do not protect against a concurrent adversary.
Unbound orphan logs are deliberately unavailable through this tool.

Legacy launch context remains unavailable without a valid immutable record and its
Job binding. Chang K1 has fired; its resulting (c)/(d) choice and complete b5 readout
remain pending. No scientific gate, resume, new workload, cluster launch or outward
publication is cleared by this review.
