# Missing b5 readout preparation

Status: offline preparation only. No submission or scientific gate clearance.

Purpose: recover the registered pilot certification and entropy evidence missing
from the actual b5 output directory. The completed source-cited metadata review establishes all five
epoch-500 snapshot states present; it does not certify their selected checkpoints.
Source: ../PVC_READOUT_REVIEW.md and ../pvc-readout-status-20261001.json.

Kai has now selected option (c), recorded in
`local/2026-10-01-execution/chang-option-c-decision.json` at
`2026-10-01T06:00:02.706672Z`. This preparation remains a diagnostic readout of the
original b5 snapshots; it does not apply the option-(c) patch to the historical bundle.
Production still needs the dated amendment, all required checks, new freeze and
replacement pilot. K1 is triggered and is not cleared by this decision.

1. Read the original b5 readout Job, immutable 42abed source manifest and registered
   readout rules. Preserve the original bundle bytes and historical output paths.
2. Verify the recovered actual Chang cache `data_info.json`, and inspect the supported
   handoff schema. Separate the readout prerequisite from unresolved K1 / production
   gates. If that distinction cannot be represented honestly, report the exact schema
   blocker rather than setting a broad scientific gate to cleared.
3. Prepare a new distinct Job and output identity for the same five registered arms
   and unchanged certification/entropy computations. Retain the existing CPU route,
   8 CPU / 24 GiB shape and four-hour stop unless inspected source establishes a
   reviewed reason to change them. User allowance for one GPU does not establish
   numerical equivalence to the registered CPU/TF32-disabled certification route.
4. Use the current handoff adapter offline with the preserved historical bundle and
   actual recovered cache identity. Make no training or model mutation; allow only
   the new readout outputs and the supported immutable provenance record. Preserve
   missing/unknown source association explicitly.
5. Validate exact code/config/data/output identities and manifests, document resource
   and gate applicability, and request independent review. Report a concrete prepared
   record or a precise blocker to the orchestrator before any launch decision.

No original Job, original output, frozen source or recovered evidence is overwritten.
No production clearance, training resume or hardware conclusion is inferred from
this preparation. The separate explicit option-(c) decision does not alter historical
readout semantics.

Implementation scope clarified: unchanged registered CPU certification/entropy plus exact five-history recovery, then separately reviewed registered full-rule analysis. Root approved bounded JSON/JSONL log export from this same finite Job; no second reader or export server. Ten synthetic tests and 18 existing handoff tests pass; independent diagnostic preparation review PASS. Final action-time scoped brief identity remains to be prepared and validated.
