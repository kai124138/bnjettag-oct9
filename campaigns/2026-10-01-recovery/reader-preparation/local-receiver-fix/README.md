# Local receiver admission compatibility

Status: three focused tests and [independent review](REVIEW.md) PASS. No transfer
was performed during this local fix or its review.

The running Pod has the admission-injected environment value
`NVIDIA_VISIBLE_DEVICES=void`. The frozen receiver rejects every environment addition.
`receive_local.py` permits exactly that one-entry Pod environment list, then delegates
to the original frozen receiver's full identity, mount, resource, security, allowlist
and transfer validation. Any other name, value, extra field, duplicate, `valueFrom`,
`envFrom` or Job-template environment remains rejected.

The wrapper first verifies the original preparation hash and every bound frozen
file. It imports the original client without editing it. The running Job, immutable
ConfigMap, server, frozen brief and original receiver remain unchanged. The transfer
receipt records the local client hash, observed exception and canonical hashes of
the captured Pod and the exact copy used for validation.

Use the same receiver arguments, including `--preparation` pointing to the original
`preparation.json` file and expected preparation hash
`8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a`,
but invoke this `receive_local.py` after independent PASS. [manifest.json](manifest.json)
binds both local files. Three tests passed under Python 3.12.13 against the actual
controlled captured Pod and adversarial environment, identity and security variants.
The tests make no network request and load no model or dataset.
