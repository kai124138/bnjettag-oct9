# PVC transport and export review

Date: 2026-10-01. Verdict: **PASS — recovered-byte integrity and provenance only**.

Independently audited:

- `captures/reader-run-20261001T0540Z/transfer-localfix-01/`, including its transport
  manifest, transfer receipt and every mirrored file;
- `captures/pvc-20261001T0555Z/`, including its export receipt and every exported file;
- the frozen preparation, local receiver fix, observation-04 identities,
  reader-ready log and observation-05-terminal records.

No remote action, model deserialization, optimizer/array loading, scientific
computation or source modification was performed. Checkpoint/optimizer files were
streamed only into SHA-256 for opaque-byte verification. Parsed data was limited to
provenance/status metadata and pointers; the log sanitizer was checked locally.

## Complete hash chain

All **253 accepted files**, totaling **63,514,020 bytes**, independently match the
reader's stored hashes, transfer receipt, actual mirror files, exporter source
hashes, export receipt and actual exported files. The exact mirror/export file sets
match the accepted paths, with no extra data files, symlinks or leftover partial
files. Counts are **118 JSON, 81 Keras, 17 optimizer NPZ and 37 log files**.

| Record | Independently reproduced SHA-256 |
| --- | --- |
| Transport manifest | `1ce0c4fd969f03b84e1753c7274611d0e17669caaf22874b7baa0bcba862a41f` |
| Transfer receipt | `ef5cf9a7316b8c068299dcca5297d28eae699658f931a64dc0fb4c7904ab90f1` |
| Export receipt | `f2527c2327a0be249a1b2de268f1df258fb06dd345466aca935f794ea20a268b` |

The manifest hash equals both the reader-ready log and terminal reader log and the
transfer receipt's manifest identity. Its bundle and scope hashes match the approved
frozen package. The transfer records HTTP finish **204**; the exporter records no
interruption and explicitly uses this verified local mirror as its source.

The reader classified 216 accepted files as copied and 37 as sanitized log
derivatives. For this capture all 37 recorded source/stored log hashes happen to be
equal; the subsequent export also preserved those bytes. This does not erase their
sanitization provenance. Original PVC source hashes and stability are reader-recorded
observations; this reviewer did not reread the live PVC. All local stored bytes and
the complete transfer-to-export chain were independently checked. Sanitization is
not a universal secret-detection guarantee.

## Selection, coverage and limits

Independently reconstructed the exact **403-row allowlisted scope** from the frozen
manifest: static cache/run metadata, selected checkpoint files, fixed snapshots,
37 matching logs and two named readout files. All paths satisfy the approved
allowlist and bounds. Recorded source bytes equal the independently counted
63,514,020 bytes, below 2 GiB; row count is below 640 and per-file bounds hold.

All **17 accepted `latest.json` pointers** match their recorded pointer hashes and
both transport/export selected generations. All **17 current generations** have
the required `state.json`, `model.keras` and `optimizer.npz` bytes. All five fixed
b5 snapshot directories have their required state metadata. The 22 selection
records report unchanged directories and copied required files; accepted files
report unchanged source state during their individual reads. These observations
do not establish an atomic cross-file snapshot or loadable/resumable checkpoints.

The remaining **150 rows are missing/missing-or-disappeared**, not refused,
corrupted, silently omitted or passed. There are **zero refused rows**. Transport
and export agree on exactly those missing paths. In particular, both named b5
readout JSON files are absent from this scoped capture. Missing optional checkpoint
variants do not establish failure or infeasibility, and missing root-level state
files do not imply missing pointer-selected generation state. Missing observations
do not prove an artifact never existed or that no other path contains one.

All three exported cache metadata records match the frozen manifest's expected
hash maps/count fields. This checks metadata values only: no dataset arrays were
rehash-verified, and no model, calibration or scientific metric was evaluated.

## Execution identity and terminal evidence

Recomputed the complete receiver identity result from the observation-04 objects;
it exactly matches the transfer receipt. It binds Job UID
`5acf637b-db47-42a0-a3b4-fbd5c2f012f0`, Pod UID
`09bf9a9f-405e-42b7-b8df-cde90e236fe9`, the approved PVC and immutable ConfigMap,
and local receiver SHA
`84ccebf8b5aae35e4a576457775aab9eda6cdb9574a804e122d200b25ea2d1cb`.
The exact reviewed `NVIDIA_VISIBLE_DEVICES=void` exception and both actual/validation
Pod hashes remain explicit. Runtime identity remains API/forwarding provenance,
not cryptographic runtime attestation.

All three observation-05-terminal receipt hashes reproduce. The same owner-bound
Pod is `Succeeded`, reader exit **0**, restart count **0**, finished
**2026-10-01T05:54:10Z**. The same Job is `Complete=True`, completion time
**2026-10-01T05:54:59Z**. Its recorded container interval is 12 minutes 20 seconds,
within the reviewed runtime bounds. These are successful recovery-reader outcomes,
not outcomes of the historical training or readout workloads.

No A/B/C findings remain within this transport/export audit. This PASS preserves
evidence for the separate log/metadata interpretation and scientific review. It
does not certify checkpoints, prove original immutable launch context, clear Chang
K1, choose (c)/(d), authorize a readout/resume/training workload or establish hardware
readiness.
