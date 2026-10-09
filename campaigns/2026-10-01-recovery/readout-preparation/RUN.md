# Historical b5 diagnostic run — 1 October 2026

Status: terminal at `2026-10-01T07:38:25Z`, main exit1 with zero restarts.
Certification and entropy processes both exited0; the final status records the five
telemetry/export omissions. Full rule analysis and scientific review remain pending.

The original user instruction to finish the readout supplies authorization
`Kai-20261001-execute-finish-readout`, recorded in
[the scoped operator record](../../../local/2026-10-01-execution/b5-readout-authorization.json).
The [preparation review](REVIEW.md) and [final identity review](FINAL_IDENTITY_REVIEW.md)
pass. The final record is
`rh-b6ae7a233d366d7b15d5120e`, full SHA-256
`b6ae7a233d366d7b15d5120ec04eb97b6e9dec0f97944fc4d9072bf8ae55f20e`.
Only the historical readout/B3 prerequisite is cleared. K1 and production remain pending;
Kai's chosen option (c) belongs to a separate new revision and replacement pilot.

| Object | Identity |
| --- | --- |
| Job | `kai-chang1001-readoutb5-42abed-r1` |
| Job UID | `d0b7eb2f-baf9-4af2-89b6-de3c33cec225` |
| Pod | `kai-chang1001-readoutb5-42abed-r1-gkzw8` |
| Pod UID | `88911bcc-9e16-4435-acf7-fb0149c0c469` |
| Job creation | `2026-10-01T06:24:25Z` |
| Job start | `2026-10-01T06:25:42Z` |

[Captured objects and hashes](../captures/readout-run-20261001T0625Z/observation-01/receipt.json)
bind the Pod's controller owner to the Job, and both immutable ConfigMaps.
[Launcher events](handoffs/rh-b6ae7a233d366d7b15d5120e/events/)
record intent before creation and successful submission. The operator observed launcher
exit zero after exact final-manifest lint passed. No launcher replay occurred.

The registered CPU procedure uses 8 CPU / 24 GiB, zero GPUs, 12 GiB ephemeral storage,
a four-hour active deadline and no retry. Source archive `42abed4b…` is unchanged;
41 expected input files and five absent divergence markers are bound before/after
execution. The writable PVC supports only new provenance and new diagnostic outputs;
source files are read and checked. Source nonmutation is a workflow/code guarantee,
not a read-only mount claim. Output is exclusively
`/data/chang-n64-20260926/pilot-b/readout-epoch-0500-42abed-b5-recovery-20261001-r1`.

Admission warned that the existing handoff init container's limit/request ratios
exceed its stated 1.2 policy threshold (CPU 1 versus 100m, memory 256 versus 128 MiB).
Creation succeeded and the owner-bound Pod was scheduled. This is a recorded warning,
not an admission denial or authority to alter the running Job. No service account,
RBAC, background monitor, source model update, training or Mulder operation was added.

The final receiver and bounded log export remain hash-bound in the preparation review.
Collect Job/Pod/ConfigMap identities and complete logs before local reception. Missing,
failed or truncated output must remain explicit; certification/entropy and telemetry
alone do not complete the registered A/Cprime/K1 and matched regime-A/B analysis.

## Startup observation

[Observation 02](../captures/readout-run-20261001T0625Z/observation-02/receipt.json)
records the same owned Pod Running with zero restarts. The init completed at
06:26:20Z and the readout began at 06:26:23Z. The
[startup log receipt](../captures/readout-run-20261001T0625Z/startup-logs-receipt.json)
binds the exact `HANDOFF_VERIFIED` and original `MANIFEST_SHA_OK 041f981a…`
markers. CPU TensorFlow initialization logged unavailable CUDA drivers, consistent
with this CPU-only command; no readout result is inferred from startup.

Admission also added an init-container ephemeral-storage request of `0` and limit
of `50Gi`, absent from the requested Job template. The main container retains its
12Gi bounds. The larger init limit is an observed admission change, not a requested
or resource-neutral setting. The separate [local receiver compatibility review](local-receiver-fix/REVIEW.md)
passes for exactly those two fields. The local wrapper preserves actual object hashes
and disclosed admission changes; original Job, helper, source and receiver bytes
remain unchanged. [Observation 03](../captures/readout-run-20261001T0625Z/observation-03/receipt.json)
still records the same Pod Running with zero restarts and no readout result yet.

## Follow-up evidence, 06:57Z

[Observation 04](../captures/readout-run-20261001T0625Z/observation-04/receipt.json)
still records the same Pod Running with zero restarts. The progress log has the first
`CERTIFIED` line for A-s2's primary snapshot. This is partial diagnostic progress;
complete certification, entropy and all registered rules remain pending.

[Interim metadata](../captures/readout-run-20261001T0625Z/telemetry-capture-01/receipt.json)
shows all five historical `activation_widths.jsonl` reads were refused with ValueError.
Read-only source stat confirms regular files from11,757,589 to247,241,686bytes, all
larger than the frozen8MiB per-file bound. The driver did not copy these histories;
that missing-output/telemetry failure must remain explicit in its final status.
No runtime, source, deadline or stop rule was changed to suppress this guard.

A [separate bounded raw-file recovery](../captures/readout-run-20261001T0625Z/telemetry-raw-01/receipt.json)
used read-only `head`, `sha256sum` and `stat` through the same owned Pod, with no new
workload. All five exact historical files,880,343,029bytes, were recovered and matched
against fresh source hashes and unchanged before/after stat. Transfer plus remote
hash read allowance was below2GiB, local streaming used1MiB chunks, and no array/model
or real scientific calculation was loaded. The capture validates opaque bytes only;
JSONL interpretation and scientific review remain pending. This separate recovery does
not rewrite the immutable readout record or manufacture a clean driver completion.

The same read-only path recovered the exact A02 seed-1 hardware model and seven
companion files in [a separate receipt](../captures/a02-hardware-evidence-20261001/receipt.json).
Those historical sources were only read; they are not part of this Job's scientific
readout or immutable input inventory. Their acquisition does not retroactively add
hardware computation to this launch. A02 model/config hashes and final stored source/
config/data identities match the historical association; model/grid/export validation
remains separate.

## Terminal capture for Claude handoff — 08:15Z

The [terminal objects and complete logs](../captures/readout-run-20261001T0625Z/terminal-handoff-20261001T0815Z/receipt.json)
record main exit1 at07:38:25Z and Job Failed at07:38:30Z, with zero restarts.
Logs report `CERTIFICATION_ALL_PASS 4 0`, `A26_DONE` and
`READOUT_JOB_DONE certify_exit=0 a26_exit=0` with telemetry/export omissions.
The reviewed local receiver accepted [six diagnostic JSON files](../captures/readout-run-20261001T0625Z/terminal-handoff-20261001T0815Z/received/transfer-receipt.json),
31,791bytes, with status `transport_verified_scientific_review_pending`.
The separate five raw histories remain available in telemetry-raw-01.
Do not relabel the failed wrapper Job as successful. Review the six diagnostic files
and independently recovered histories together before any scientific gate decision;
Job Failed alone is not a reason to repeat completed certification/entropy.
The public main commit1c9f933 predates this terminal observation and still needs a
reviewed follow-up update. No new launch occurred during this handoff capture.

## Refusal detail fix — 2 October 2026

The five telemetry entries were refused by the frozen 8 MiB per-file guard, not missing;
the driver recorded only `ValueError`. `driver.py` now records a `detail` string with the
observed size and limit for refused histories, export entries and export receipts. The
guard itself is unchanged. The five histories are already recovered byte-exact in
telemetry-raw-01, so no readout rerun is needed for them; review them together with the
six received diagnostic files. 11 of 11 tests pass ([log](tests-refusal-detail.log)).
The terminal record above is unchanged.
