# Historical b5 readout preparation — 2026-10-01

Status: [preparation review PASS](REVIEW.md), [final identity review PASS](FINAL_IDENTITY_REVIEW.md) and action-time lint PASS. Submitted once; [RUN.md](RUN.md) records execution and [ACTIVE.json](ACTIVE.json) identifies the final immutable handoff. Earlier pending handoffs remain preserved as drafts.

The recovered [source inventory](../PVC_READOUT_REVIEW.md) establishes all five
snapshot states at epoch 500 and missing certification/entropy output paths. This
new diagnostic Job preserves the exact original compressed `42abed4b…` source,
configs and registered CPU commands. It binds 41 actual recovered input files
(configs, preprocessing/cache metadata, state and selected snapshots), checking
hashes before and after readout, including five expected-absent divergence markers. It copies each arm's exact `activation_widths.jsonl`
with source hashes and no scientific arithmetic by the wrapper.

The five arms are A-s1, A-s2, D-s1, C′-s1 and E1-s1; frozen indices are 0, 1, 24, 56
and 57. Certification applies only to feasible primary/AUC selections: A-s1, C′
and E1 having no feasible selection does not mean their fallbacks are certified.
Entropy retains the registered labelled minimum-cost fallback. The original
certification explicitly disables TF32; entropy uses its unchanged CPU-only route.
CPU disagreement is handled by the registered conditional original-product GPU
adjudication, never an automatic rerun from this Job.

The new Job is `kai-chang1001-readoutb5-42abed-r1`, with a new immutable source
ConfigMap of the same name plus `-code`. Durable output is
`/data/chang-n64-20260926/pilot-b/readout-epoch-0500-42abed-b5-recovery-20261001-r1`.
An existing output directory causes refusal. Original Job, source ConfigMap,
checkpoints and readout outputs remain untouched. The normal supported handoff
init verifies actual cache identity and writes its new content-addressed record.
No recovery-only bootstrap exception is needed: the actual cache metadata exists.
The supported adapter requires a writable `/data` mount for provenance and new
outputs; source nonmutation is enforced by exact commands and before/after hashes,
not by a read-only PVC mount.

Resources retain the registered 8 CPU / 24 GiB memory, 12 GiB ephemeral storage,
zero GPUs, four-hour active deadline, backoff zero and token automount false.
TensorFlow/OMP use two threads; inter-op and OpenBLAS use one. The image is official
Python 3.12 pinned to `sha256:4d1caded1f729ae443eb803f26ffde7b61e696aeaef62f099abb6dd6b14257c7`;
[registry receipt](../../../local/2026-10-01-execution/python-readout-image.json)
records verified index/platform metadata. Package versions are captured at runtime;
original pinned requirements and the original package-dependent manifest check
are retained. User allowance for one GPU is not evidence that a changed GPU readout
would preserve the registered semantics.

A bounded log export carries only named JSON/JSONL diagnostics and telemetry, with
run/handoff/Pod identities, hashes and strict begin/chunk/end framing. It exports
no dataset arrays, checkpoints or environment dump. Limits are 8 MiB per file,
48 MiB source bytes and 4 MiB total encoded export, including framing. Missing,
refused, corrupt, duplicate, truncated and over-budget transfers stay explicit;
no incomplete readout gets a success exit. Complete accepted artifacts also remain
under the new PVC output. Kubelet log retention can still lose a stream; receiver
failure is evidence of incomplete recovery, never authority to launch another reader.

The local receiver takes the exact immutable handoff directory, captured Job, its
controller-owned Pod, both immutable ConfigMaps, explicit Job/Pod UIDs and captured
log. It verifies those bindings before exclusive output creation. Admission's sole
allowed extra environment value is `NVIDIA_VISIBLE_DEVICES=void`; other additions
are refused. This is local parsing only, with no network or remote mutation.

Ten synthetic tests cover object identity/admission, source symlinks, byte budgets,
missing outputs, nonzero diagnostic exits, telemetry completeness, gzip expansion,
wrong run identity, duplicate/truncated/corrupt streams and roundtrip transfer. The
18 existing handoff tests also pass under Python 3.12.13. No real model or array was
loaded locally. Final tests/hashes and independent review will be recorded separately.

Kai's original instruction explicitly requests finishing the readout. The scoped
authorization is recorded under `Kai-20261001-execute-finish-readout`. The supported
launcher submitted the final `rh-b6ae7a233d366d7b15d5120e` record after review and
exact-manifest lint. Its cleared gate covers historical readout/B3 readiness only;
the separate production gate remains pending. Do not replay the launcher.

Kai chose **(c), traced cost directly into PID**, as recorded in the authoritative
[decision](../../../local/2026-10-01-execution/chang-option-c-decision.json). This
historical readout does not apply that patch. K1 remains triggered. Completing
certification/entropy and recovering histories supplies inputs; it does not complete
A/C′/K1 rule arithmetic or the matched regime-A/B table. Both A seeds must be evaluated;
the registered A stop occurs if neither has a qualifying checkpoint, not if only one
fails. Full rule analysis, the dated (c) amendment, all required checks, a new freeze
and replacement pilot remain required before production. Historical training's
immutable launch context remains unavailable; this new record cannot recover it.
