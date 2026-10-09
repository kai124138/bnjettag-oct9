# Recovery collector review

Date: 2026-10-01. Verdict: **ITERATE**.

Reviewed `recover.py`, `test_recover.py`, `recovery-manifest.json`, `REPORT.md`, and
the specific historical producer paths cited below. No collector edits, remote
access, ML execution, model/array loading or scientific recomputation. Synthetic
adversarial checks used only temporary files and mocked subprocess calls.

Validation: `python3 -m unittest discover -s campaigns/2026-10-01-recovery -p
'test_recover.py' -v` passed **10/10** tests. These tests do not cover the failures
below.

## Required fixes

**A1 — Known credential forms survive the sanitizer.**
`recover.py:40-45` redacts a generic authorization value before its Bearer rule.
For a synthetic `Authorization: Bearer <fixture-token>` header, the first rule
removes only `Bearer`, leaving the token behind; the second rule then cannot match.
A JSON object with a quoted `api_key` field also remains unchanged because the key's
closing quote prevents the generic pattern from matching. Local probes confirmed
both tokens remain, without printing or reading any real credential. The latter
also defeats the explicit JSON-copy refusal at lines 267-272. The documented
“not universal” limitation does not justify these ordinary forms that the intended
rules specifically cover.

Fix: consume the whole authorization scheme/value before generic key-value
redaction, and inspect recognized credential fields structurally in JSON (or
correctly handle quoted keys/values). Preserve valid JSON for sanitized metadata;
refuse credential-bearing byte-for-byte exports. Add synthetic regression tests for
Bearer headers, quoted JSON credential keys, and a representative Kubernetes status
message. Keep the source/derivative hashes and non-universal limitation.

**A2 — Failed Job reads silently disable UID binding.**
At `recover.py:195-203`, a failed/unavailable Job query produces `job=None`, then
`uid=None`. `owned_pod` treats that value as permission to accept any owner UID at
lines 136-141. A mocked failed Job query followed by a matching-name/label pod
caused **six log requests** across the three allowlisted Jobs. A failed read does
not establish that the Job is absent, so the report's “if the Job still exists its
UID must match” guarantee is not enforced.

Fix: distinguish a successful, empty Job listing from an unavailable/malformed Job
response. Do not collect logs with downgraded binding after a failed query. Record
the ownership state and unresolved UID in the receipt. Any intentional orphan-pod
recovery must be explicit and retain the owner UID as unverified historical context;
it cannot be presented as matching a recovered Job. Test failed queries, malformed
responses, an observed different UID and a positively matched UID.

**A3 — The copied checkpoint pointer can disagree with the copied generation.**
`recover.py:285-293` copies `latest.json`, then separately rereads its live source
to choose the generation. A local mocked copy advanced the source pointer between
those operations: the resulting export contained `latest.json` pointing to
`epoch-0001`, but only `checkpoints/epoch-0002/state.json`. The exporter completed
and wrote its ordinary receipt. This is relevant to an authorized live mount:
`campaigns/2026-09-26-training-batch/code/tree/bnhgq2/ablation.py:259-263` advances
the pointer atomically and removes old generations during training.

Fix: select the generation from the exact accepted pointer bytes retained in the
export, not a later source read. Record its hash and generation together. If that
generation disappears or changes during copying, retain explicit incomplete/changed
evidence rather than substituting the new generation. Do not follow a refused
pointer. Add a synthetic pointer-advance regression and ensure failure paths still
write a receipt describing partial evidence.

**B1 — The narrow export omits available terminal and provenance records.**
The per-run allowlist at `recover.py:285` excludes `source_manifest.json`,
`input_std.json`, `COMPLETE.json`, `TRAINING_COMPLETE.json`, `VERIFIED_COMPLETE.json`
and `screen_result.json`. These are directly relevant to the stated recovery
questions: the historical producer writes the source manifest at
`code/tree/run_study.py:119-121`, distinguishes completed training from verified
completion at lines 148-149 and 191-193, and writes preprocessing identity at
`code/tree/bnhgq2/ablation.py:724`. Omitting them can make useful evidence appear
unavailable even when the authorized export contains it.

Fix: add the relevant exact filenames to the same seventeen approved run paths,
with existing credential/path checks and per-file present/missing/refused receipts.
Record terminal markers as evidence, not clearance to resume or as an immutable
launch record. Add a temporary-directory fixture exercising present terminal,
source and preprocessing records; update the report's coverage description.

## Checks that passed and scope limits

The three exact Job names are hard-coded at `recover.py:19-23`; every remote request
uses explicit `--context` and namespace `cms-ml`. Context absence prevents cluster
requests. The collector issues only Job/pod `get` and container `logs`; no submission,
exec/cp, mutation, resume, background monitor or credential-extraction operation is
implemented. Matching live Job UID checks work when that UID is actually obtained.

The bundle verifier rejects traversal, links/special files, duplicate raw member
names, digest mismatches and file-inventory mismatches without extraction or
execution. The existing manifest test verified both stored payloads. Local PVC
paths reject traversal and existing symlink components; checkpoint leaves are
restricted to a single accepted name, destination directories must be new, and
outputs under the source root are refused. These are ordinary filesystem workflow
guards, not protection against a concurrent actor changing filesystem paths.

The report correctly distinguishes metadata matches from rehashed arrays/checkpoint
validity, synthetic readout fixtures from real terminal outcomes, and legacy inputs
from immutable launch context. Missing context remains unavailable. Chang K1,
Kai's (c)/(d) choice, terminal b5 readout and any new launch remain pending. No
scientific or launch authority is granted by this review.
