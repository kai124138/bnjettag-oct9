# Read-only reader run — 2026-10-01

Status: one authorized Job and immutable ConfigMap created; 253 files transferred
with verified hashes and exported locally. The reader exited zero and the Job
completed; independent transport and metadata/log reviews are complete. No training, resume, scientific readout
or hardware claim follows from this workload.

Kai authorized the requested single recovery workload and adapter, allowing one GPU
if needed. The already reviewed CPU-only package was retained because this transport
does not require a GPU. The actual approval is
[recovery-reader-approval.json](../../../local/2026-10-01-execution/recovery-reader-approval.json),
reference `Kai-20261001-one-recovery-workload`, timestamp
`2026-10-01T05:39:11.948998+00:00`, SHA-256
`3d8f38b47b0a1d3203bc9d83a6560f7007a59173c9d375e9d31c603682be0362`.
It grants the named read-only bootstrap exception and reviewed campaign adapter;
it does not select Chang option (c)/(d) or authorize training.

The submitted preparation SHA-256 is
`8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a`.
Frozen source, manifests, brief and [review](REVIEW.md) remain unchanged. Their pending
annotation records the original preparation state. Actual action-time authorization
is established separately by the dated approval and
[durable submission intent](submissions/8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a/intent.json),
which binds the approval hash and was written before creation.

| Object | Name | UID |
| --- | --- | --- |
| Job | `kai-recovery-ro-1001-cbb3dec6a6` | `5acf637b-db47-42a0-a3b4-fbd5c2f012f0` |
| Immutable ConfigMap | `kai-recovery-ro-1001-cbb3dec6a6-code` | `d5bde464-7cdf-400c-81ae-ae5a428fa1a8` |
| Reader Pod | `kai-recovery-ro-1001-cbb3dec6a6-hdxjb` | `09bf9a9f-405e-42b7-b8df-cde90e236fe9` |
| Existing PVC | `kai-data` | `c5be55ec-3362-40a9-b283-f8d0750dcf95` |

Objects are in namespace `cms-ml`, context `nautilus`. The Pod's controller owner UID
matches the created Job. Create responses are preserved as
[Job receipt](submissions/8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a/job.json.created.json)
and [ConfigMap receipt](submissions/8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a/configmap.json.created.json).
The [05:43 observation](../captures/reader-run-20261001T0540Z/observation-03/pods.json)
records the Running Pod; additional captures are in
[`reader-run-20261001T0540Z`](../captures/reader-run-20261001T0540Z).

The first adapter invocation supplied the frozen directory to `--preparation`.
That option requires its `preparation.json` file. The directory read failed before
any cluster operation or submission intent. The corrected invocation created the
ConfigMap and Job once; this was not a second submission or relaunch.

Admission added `NVIDIA_VISIBLE_DEVICES=void` to the Pod container. The frozen
receiver rejects any environment addition, so this observed difference requires
explicit handling and focused review before accepting the transfer. The submitted
Job template did not request that environment value or a GPU. No receiver or frozen
source change is made by this run record.

A separate [local receiver wrapper](local-receiver-fix/README.md) has been prepared
for exactly this observed Pod environment value. Its three local captured-object
and adversarial tests and [independent review](local-receiver-fix/REVIEW.md) pass. It preserves original
preparation/server hashes and delegates all other checks to the frozen receiver.

The finite bounds remain 30 minutes for the reader and 35 minutes for the Job, zero
retries, 2 GiB of allowlisted source bytes, and read-only PVC access. Source mutation,
missing evidence, transfer failure or deadline expiry must remain explicit. Successful
startup alone does not establish recovery or clear any scientific gate.

## Verified transfer and local export

The reviewed local receiver exited zero. Its
[transfer receipt](../captures/reader-run-20261001T0540Z/transfer-localfix-01/transfer-receipt.json)
records `transfer_verified_evidence_requires_review`, 253 files and 63,514,020 bytes,
with HTTP 204 acknowledging the reader's finish request. That acknowledgement is
distinct from the subsequent terminal Kubernetes observation.

The [transport manifest](../captures/reader-run-20261001T0540Z/transfer-localfix-01/transport-manifest.json)
has 403 allowlisted entries: 216 copied files, 37 sanitized logs and 150
missing-or-disappeared paths. Optional checkpoint variants are included in the
allowlist, so the missing count is not a failed-run count. Accepted files comprise
118 JSON files, 37 logs, 81 opaque Keras files and 17 opaque optimizer NPZ files.
No model or array was loaded. The three recovered cache identity records match the
historical expected metadata; their dataset array bytes were not rehashed.

The existing `recover.py export-pvc --checkpoints` command also exited zero and wrote
[export-receipt.json](../captures/pvc-20261001T0555Z/export-receipt.json) at
`2026-10-01T05:54:31.733342+00:00`. It has no interruption, preserves the same accepted
file/byte counts, and explicitly leaves checkpoint validity and terminal clearance
unestablished. Both receipt layers are retained; original PVC log hashes come from
the transport layer because the local mirror already contains sanitized derivatives.

| Receipt | SHA-256 |
| --- | --- |
| Transport manifest | `1ce0c4fd969f03b84e1753c7274611d0e17669caaf22874b7baa0bcba862a41f` |
| Verified transfer | `ef5cf9a7316b8c068299dcca5297d28eae699658f931a64dc0fb4c7904ab90f1` |
| Existing exporter receipt | `f2527c2327a0be249a1b2de268f1df258fb06dd345466aca935f794ea20a268b` |

The [terminal capture](../captures/reader-run-20261001T0540Z/observation-05-terminal/receipt.json)
preserves the same Job and Pod UIDs. The Pod is `Succeeded`, exit code 0, restart
count 0; its container ran from `05:41:50Z` to `05:54:10Z`, a duration of 12 minutes
20 seconds. The Job records `Complete=True` at `05:54:59Z`. The orchestrator stopped
the local port-forward with exit code 0; no remote kill or deletion was issued.

Independent [transport review](../PVC_TRANSPORT_REVIEW.md) passed; [per-arm metadata/log diagnosis](../PVC_READOUT_REVIEW.md) is complete. Full scientific readout remains pending. These
operational counts do not certify all required historical artifacts or clear a
scientific decision.
