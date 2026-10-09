# Local receiver admission compatibility

Status: [independent review PASS](REVIEW.md); three focused tests and a synthetic full-CLI transfer pass. This
client makes no remote call and does not change the running Job, submitted handoff,
original receiver, runtime code or global launcher.

The captured readout Pod's `record-run-handoff` init container has admission-added
`requests.ephemeral-storage="0"` and `limits.ephemeral-storage="50Gi"`. The submitted
Job template omits these fields. The init container has already exited zero. The
main container retains the requested 12 GiB ephemeral limit. This is a larger
admission-added init storage limit, not a requested setting or a claim of zero
resource impact. Evidence is `captures/readout-run-20261001T0625Z/observation-02/pod.json`.

`receive_local.py` requires the original reviewed receiver's SHA-256
`29421107d2a9507e701d76561eed4620a65979fd8bb3bc34f83f424eb85ae1c5`.
It removes only those two exact fields from a copy of the actual Pod for validation,
then delegates all handoff, Job, Pod-owner/UID, execution, resource, mount, image,
ConfigMap and transport checks to the unchanged receiver. Job-template or main
container storage changes, other init resources/values and other execution changes
still fail. The receipt preserves the actual captured Pod hash, actual admitted
resources, validation-copy hash and wrapper/original hashes.

Use the same receiver CLI after review, replacing its executable path with this
wrapper. `--handoff` remains the exact final `rh-b6ae7a233d366d7b15d5120e` directory;
all four captured objects, explicit Job/Pod UIDs, log and new output path are required.
No artifact overwrites are allowed. Tests use only the actual captured JSON and
adversarial mutations; no model, array, log stream or remote action is involved.
