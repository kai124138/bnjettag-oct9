# Recovery reader preparation review

Date: 2026-10-01. Verdict: **PASS — engineering preparation; not launch authorization**.

Reviewed the final `reader.py`, `receive.py`, `launch.py`, `prepare.py`, pure filters,
scope, tests, `README.md`, `PREPARATION.md`, `ACTIVE.json` and frozen package
`frozen/cbb3dec6a6f3e04766b1973b39442ea2f9f16cf28ce3c323600ad037cf3ac75e/`.
No remaining A/B findings block presenting this concrete recovery-only exception
for Kai's approval. No remote calls, workload launches, dataset reads, array/model
loading or scientific calculations were performed by this reviewer.

## Reviewed identities and checks

| Artifact | SHA-256 |
| --- | --- |
| Preparation record | `8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a` |
| Bundle | `cbb3dec6a6f3e04766b1973b39442ea2f9f16cf28ce3c323600ad037cf3ac75e` |
| Job | `c9f2850798723ad3c4de5c53eef156028bcec8ef765ecb46f9a72887483b995d` |
| Immutable ConfigMap | `edcbdab48841b0b969ef8076b241cb8be5c3a8a31cab033605bdb868f67a880a` |
| Tests | `58e975abb5b44999cf684a8273bfb0d65a53e21fdb284933fd7ecd7609f8f05d` |

Independently reproduced every bundle/preparation file hash, mode-0444 payload
permission, ConfigMap-embedded file, current/frozen runtime source equality and the
Job's bundle binding. Frozen `scope.json` is byte-identical to the reviewed recovery
manifest. The exact scope is 17 runs, three cache metadata locations, matching arm
logs, pointer-selected generations, five fixed b5 snapshot directories and two named
readout JSON files. No dataset payload is included.

Independently ran all **11 tests successfully under Python 3.12.13**:

```sh
/home/kaimoe/lab/.venvs/preflight-20261001/bin/python -m unittest discover \
  -s campaigns/2026-10-01-recovery/reader-preparation -p test_reader.py -v
```

Also exercised the actual reader server and receiver together on loopback using a
temporary synthetic PVC and four tiny opaque fixture files. All four transferred
with matching hashes; the accepted pointer retained its selected generation after
the source pointer advanced. An arbitrary filesystem path and unknown blob returned
404; premature finish returned 409; verified completion returned 204 and stopped the
server. No checkpoint library or array loader was used. The tested runtime files
match the final frozen package.

The orchestrator's `live-lint-cbb3dec6.json` records read-only live manifest lint
at **2026-10-01T05:34:39.043408Z**, exit 0, for the exact Job hash above. Its log
contains OK with no errors or warnings. Independently reproduced the log SHA-256
`877dea7b9e14ade722685e812b4dd8b0cd84a15a2f6588a70a0fdf3ee9988dd7`.
This is lint evidence, not execution, permission/readability or scheduling proof;
no submission is recorded.

## Preliminary findings resolved

**A1 — Rejected files bypassed the declared source-byte budget: resolved.** Initially
`Export.copy` charged bytes only after acceptance. The independent counterexample
read two refused 16-byte credential JSONs under a 20-byte budget and reported zero
bytes. The final reader charges each byte as read, bounds reads by the initial file
size, and propagates `BudgetExceeded` to an incomplete staging receipt. Repeating the
original counterexample now charges 16 bytes and refuses the second file before
reading. The suite also checks incomplete-receipt behavior.

**B1 — Pending approval placeholders passed the submission guard: resolved.** The
initial truthiness checks accepted literal pending fields. Final `launch.authorization`
requires `approval_status=approved`, rejects pending/placeholder references, parses an
explicit UTC timestamp, and binds the actual reference, exact preparation hash,
exceptions, operations, context and namespace. Negative cases pass. This remains a
workflow record checked by the operator; it is not cryptographic proof of human
approval or a replacement for Kai's explicit action-time authorization.

## Safety, integrity and execution boundary

`reader.PVC` traverses descriptor-relative paths with `O_NOFOLLOW`, rejecting
traversal, symlinks and special objects. `Export` uses the staged pointer bytes to
select a bounded generation leaf. File and directory stability checks expose changes;
the package explicitly does not promise an atomic multi-file snapshot. Recognized
credential JSON is refused and logs are sanitized, retaining separate source/stored
hashes. Opaque checkpoint bytes are copied without execution. Secret detection is a
limited heuristic, not a general certificate about file contents.

The server binds only `127.0.0.1`, exposes the fixed bundle manifest plus accepted
content-hash blobs, and accepts no client filesystem path. The receiver uses loopback
without redirect handling; it checks captured Job/Pod owner/PVC/ConfigMap identities,
read-only/security/resource settings, manifest scope, path allowlist, byte lengths
and content hashes. It installs files only after transfer verification and checks
the received pointer/generation binding. Fresh private output and incomplete-transfer
receipts prevent accidental reuse. Runtime identity still depends on the authorized
port-forward to the verified Pod; captured API objects are not runtime attestation.

The frozen Job uses the observed PVC UID
`c5be55ec-3362-40a9-b283-f8d0750dcf95`, with read-only PVC and code mounts, no token
automount, root, added capabilities, `fsGroup`, init container or GPU. It requests
100m CPU/256 MiB and limits 1 CPU/512 MiB. Source reads are capped at 2 GiB, files at
640, logs at 128 per directory, with per-file bounds and bounded scratch. The reader
has a 1,800-second deadline, Job deadline 2,100 seconds, zero retries and one-hour
terminal retention. Actual PVC permissions, available evidence and live schedulability
remain operational unknowns; refusal is not permission to widen scope or bounds.

`launch.py` is offline by default. The explicit submission path revalidates prepared
bytes, runs existing lint, requires the exact approval record, checks named context
and live PVC UID, refuses existing objects, and creates a fixed per-preparation
submission ledger before creating the ConfigMap/Job. A previous intent blocks replay;
partial/ambiguous creates require review rather than retry/adoption. The operation
guide restricts subsequent forwarding to local loopback and the observed owner-bound
Pod. This reviewer did not perform live lint or those cluster operations.

The requested training-handoff exception is explicit and justified by the missing
cache identity and the ordinary handoff init's PVC write. It is confined to this
read-only evidence bootstrap and reviewed adapter. **This PASS does not grant that
exception or authorize creation/forwarding.** The exact package still requires Kai's
action-time approval and the applicable manifest/access checks. No global guard,
training launcher, historical brief or scientific rule is changed. Recovered bytes
must be reviewed separately; Chang K1, the b5 readout, (c)/(d), checkpoint validity,
training/resume and hardware readiness remain unestablished.
