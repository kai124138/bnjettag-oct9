# Evidence recovery — 2026-10-01

Status: the reviewed one-shot capture establishes terminal Job conditions for
confirmation and Chang b5. An authorized finite read-only reader has now transferred
253 evidence files with verified hashes and completed the local export. Independent
transport review passed and per-arm metadata/log diagnosis is complete. No new scientific result, resume,
readout workload or training launch occurred. Historical records were left unchanged.

## Verified stored identities

`recover.py manifest` verifies the exact compressed bytes in the saved ConfigMaps and every
regular file against the historical manifest, without extracting or executing the payload.
The verification passed for:

| Payload | Archive SHA-256 | Files verified |
| --- | --- | ---: |
| Confirmation training source | `26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45` | 152 |
| Chang pilot b5 / readout source | `42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0` | 250 |

The saved confirmation config/runner ConfigMap content also reproduces its historical
digest `e0c0a349bc34406f366f85f5169b8fdef6a273c11ddb233b6cd758630e620ebd`.
These checks verify stored launch ingredients, not live Job identity or checkpoint validity.
Legacy runs have **context unavailable** under the immutable-handoff workflow unless a
valid record and the matching Job annotation are actually recovered. A job name is no substitute.

## Reviewed live observations and missing evidence

The capture at `2026-10-01T05:13:12.975881Z` authenticated successfully to NRP and
queried the three exact Job names in `cms-ml` with owner selector `user=kai`.
[LIVE_CAPTURE_REVIEW.md](LIVE_CAPTURE_REVIEW.md) records PASS for saved observations
only and verifies all five stored capture hashes against the
[receipt](captures/cluster-20261001T0513Z/receipt.json). No logs were recovered:
both `user=kai,job-name=...` pod queries returned empty lists.

| Job | Observed condition | Limit |
| --- | --- | --- |
| `kai-confirm-onegpu-0924-e0c0a3-r2` | `Failed=True`, reason `FailedIndexes`, transition `2026-09-26T07:24:11Z`; `status.failed=5`, `failedIndexes="0"`. | The status counter does not mean five scientific arms failed. Arm-level diagnosis and checkpoint state were unknown at this capture; the later PVC review below updates them. |
| `kai-chang0926-pilotb5-42abed` | `Complete=True`, reason `CompletionsReached`, completion `2026-09-29T20:52:06Z`; `succeeded=1`. | Kubernetes completion does not certify the five pilot arms or their checkpoints. |
| `kai-chang0926-readoutb5-42abed` | The exact name and `user=kai` query returned an empty list. | Current observed absence does not establish whether the readout previously ran or produced artifacts. |

The immutable-handoff binding annotations are absent from the captured Jobs; legacy
context remains **context unavailable**. No checkpoint validity is inferred. Separate
one-shot captures record [PVC status](captures/access-20261001T0518Z/pvc.json) at
`2026-10-01T05:17:47.601818Z`: `kai-data` is `Bound`, `100Gi`, `ReadWriteMany`.
The [namespace mount query](captures/access-20261001T0518Z/mounts.json) at
`2026-10-01T05:17:48.902193Z` found no pods mounting it. A separately authorized
read-only reader was subsequently created once and exported evidence; its
[run record](reader-preparation/RUN.md) preserves the approval, immutable package,
object identities and transfer receipts. The earlier mount observation remains a
snapshot of its own collection time.

| Work | Latest local evidence | Needed next |
| --- | --- | --- |
| Twelve confirmations | The Job condition establishes failure at `2026-09-26T07:24:11Z`; the new PVC export contains allowlisted logs, metadata and selected-generation files. | Four final selected-checkpoint reload assertions are source-cited in PVC_READOUT_REVIEW.md. Unique causal Job trigger and successful checkpoint/optimizer reload remain unresolved. |
| Chang b5 | The Job condition establishes completion at `2026-09-29T20:52:06Z`; allowlisted terminal and snapshot files have been exported where present. The readout Job is absent from the earlier exact query. | All five committed/snapshot states record500; true certification and entropy outputs are missing. Recover five activation histories and execute the new reviewed diagnostic readout; K1 is not cleared. |
| Data identity | All three actual cache `data_info.json` records were exported; their recorded array hashes and split metadata match historical expectations. | All17 metadata associations pass internal checks; required scientific validation remains. Dataset arrays were neither exported nor rehashed. |

## Authorized PVC evidence transfer

The local receiver's [receipt](captures/reader-run-20261001T0540Z/transfer-localfix-01/transfer-receipt.json)
records 253 verified files totaling 63,514,020 bytes and a successful HTTP 204 finish
acknowledgement. The [transport manifest](captures/reader-run-20261001T0540Z/transfer-localfix-01/transport-manifest.json)
records 403 requested entries: 216 copied files, 37 sanitized logs and 150
missing-or-disappeared paths. Those paths include optional checkpoint variants;
the count is not a number of failed scientific arms. Accepted files comprise 118
JSON, 37 logs, 81 opaque Keras and 17 opaque optimizer NPZ files. None was loaded as
a model or array.

The unchanged exporter completed with `--checkpoints` at
`2026-10-01T05:54:31.733342+00:00`, producing
[the local export receipt](captures/pvc-20261001T0555Z/export-receipt.json) without an
interruption. It records the same accepted files and bytes. Its source is the
verified local mirror; original PVC log hashes remain in the transport manifest.
The three cache metadata comparisons pass; no dataset-array or model validity is
inferred. Independent [transport review](PVC_TRANSPORT_REVIEW.md) passed; [per-arm metadata/log diagnosis](PVC_READOUT_REVIEW.md) is complete. The
[terminal capture](captures/reader-run-20261001T0540Z/observation-05-terminal/receipt.json)
records the same Pod as `Succeeded`, exit code 0 and zero restarts, with container
runtime `05:41:50Z`–`05:54:10Z`. The same Job records completion at `05:54:59Z`.
The local port-forward was stopped; no remote kill or delete was issued.

`code/evidence/dry_readout_b5*` are synthetic test fixtures. The fixture driver explicitly
plants missing snapshots and an RSS failure marker. Its `READOUT_JOB_DONE` and certification
messages are not real b5 outcomes. Only actual cluster/PVC evidence can close this gap.

## One-shot recovery commands

The reviewed capture used the existing cluster access route. Any later authorized
one-shot collection uses a new output directory:

```sh
python3 campaigns/2026-10-01-recovery/recover.py cluster \
  --context APPROVED_EXISTING_CONTEXT \
  --out campaigns/2026-10-01-recovery/captures/cluster-01
```

Replace the context placeholder with the approved existing context name. The collector
checks that named context exists using local `config get-contexts`; it never falls back
to the current default. Cluster requests issue only `get jobs`, `get pods` and `logs` for these exact Jobs in
`cms-ml`, filtered to `user=kai`:

- `kai-confirm-onegpu-0924-e0c0a3-r2`
- `kai-chang0926-pilotb5-42abed`
- `kai-chang0926-readoutb5-42abed`

Logs require a successful Job read with a positively identified UID, followed by a
pod whose Job-owner UID matches it. Failed/malformed/UID-less Job responses stop
that Job's collection. A successful empty listing is recorded separately as
observed absence; it also skips pod/log reads. Orphan-pod recovery is not implemented.
Ownership state and unresolved UIDs are explicit in the receipt.
The collector requests each container's current and previous logs. There is no `exec`,
`cp`, `apply`, `create`, `delete`, background polling or credential lookup. Missing objects
and request failures remain unavailable evidence. Existing output directories are refused.
Saved metadata excludes command/env values and last-applied annotations. Recognized
JSON credential keys are sanitized structurally, preserving valid metadata JSON;
authorization scheme/value pairs are redacted together. Logs are sanitized
derivatives, with source and stored hashes in the receipt; redaction is not a universal
secret detector. Keep raw artifacts private and review derivatives before publication.

When an existing authorized mount or export corresponding to PVC `/data` is available,
the following copies only the manifest's caches, runs, logs and b5 outputs to a new directory:

```sh
python3 campaigns/2026-10-01-recovery/recover.py export-pvc \
  --pvc-root /path/to/authorized/data-export \
  --out campaigns/2026-10-01-recovery/captures/pvc-01 \
  --checkpoints
```

Replace the example source with the already approved route. This command does not create
that route. If none exists, access remains a blocker; a new reader workload needs its own
authorization. No Mac connection or credential copying is required.

`recovery-manifest.json` lists all seventeen exact run directories, three exact cache paths
and expected array hashes. Confirmation N8 runs are under
`/data/confirmation-20260923/architecture/runs`; N64 runs are under
`/data/confirmation-20260923/n64-5m-full/runs`. Both use queue logs under
`/data/confirmation-20260923/architecture/logs`. Chang b5 is under
`/data/chang-n64-20260926/pilot-b`. The expected full readout directory is
`/data/chang-n64-20260926/pilot-b/readout-epoch-0500-42abed-b5`.

The exporter selects the confirmation generation from the exact accepted `latest.json`
bytes in the export, recording pointer SHA-256 and generation together. It never
selects a later generation by rereading the live source. It preserves that generation's
`state.json`, `model.keras`, `optimizer.npz` and available selected checkpoints when
`--checkpoints` is supplied. It also
exports Chang epoch-500 snapshot files and current checkpoint generations where present.
It never loads models or arrays. Missing optional checkpoint variants are recorded as missing;
this alone is not failure, because some arms never produced a feasible checkpoint.
Changing/disappearing source files and missing required generation files are explicit
incomplete evidence. Refused pointers are never followed. A partial receipt is written
even when an unexpected error interrupts collection; the export is not an atomic
snapshot or a checkpoint-validity certificate.

The exact run-metadata allowlist includes `source_manifest.json`, `input_std.json`,
`COMPLETE.json`, `TRAINING_COMPLETE.json`, `VERIFIED_COMPLETE.json` and
`screen_result.json`, alongside config/data/state/pointer/divergence/RSS records.
All have present/missing/refused states and source/stored hashes when accepted.
Recognized credential-bearing JSON is refused for byte-for-byte export. Terminal
markers are evidence to review; they cannot authorize a resume, clear K1 or stand in
for an immutable launch record.

Cache metadata comparisons require the original `array_sha256` map and split counts.
Confirmation uses 496,000 training / 124,000 validation rows for each N. Chang uses
558,000 / 62,000 and its 2 GeV gate. The cache's historical code hash is distinct from the
later training bundle hash. Matching metadata does not rehash the array bytes or certify
a checkpoint. Per-run config/data/code hash guards, optimizer state and terminal stability
must pass review before any resume; no automatic resume is provided.

## Gates and validation

Kai explicitly selected **option (c), feeding traced cost directly into the PID**, at
the decision recorded `2026-10-01T06:00:02.706672Z` in
[chang-option-c-decision.json](../../local/2026-10-01-execution/chang-option-c-decision.json).
The (c)/(d) choice is resolved. K1 remains triggered: the full historical b5 readout,
dated option-(c) amendment, required CPU/pairing/fingerprint/floor checks, new freeze
and replacement pilot still precede production. Require all five terminal outcomes,
actual certification and entropy outputs, and the complete pre-registered readout. A successful
readout Job alone is insufficient: the terminal log must have zero certification/entropy
exits and an empty `missing=` list; partial outputs remain partial. If readout-b5 never ran,
the stored manifest is a historical artifact, not authorization to submit it unchanged.

The [reviewed confirmation diagnosis](PVC_READOUT_REVIEW.md) identifies final selected-checkpoint reload assertions in four exported arm logs; the unique chronological Job trigger remains unresolved because causal queue/terminal Pod logs are absent. Copying opaque checkpoint bytes does not certify reloadability.
Any intentional new attempt requires a separate record and the supported handoff process.

Validation: `python3 -m unittest discover -s campaigns/2026-10-01-recovery -p 'test_recover.py' -v`
passed 21 tests after the fixes recorded in `FIXES.md`. Coverage includes stored inventory verification, tampering/path rejection,
ownership and UID binding, command restrictions, credential redaction, immutable output,
cache identity mismatches, missing tooling, empty exports, source-pointer advancement,
changing/disappearing generations, partial receipts, refused pointers and terminal/source/
preprocessing records. The fixtures never contact NRP. The subsequent
[live capture review](LIVE_CAPTURE_REVIEW.md) passed the saved observations above;
it does not validate checkpoints or clear a scientific gate.
