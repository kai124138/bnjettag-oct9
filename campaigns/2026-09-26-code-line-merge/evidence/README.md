# Code merge evidence

The current complete engineering attempt is [preflight_v5.json](preflight_v5.json),
with 217 passing rows. Its compact coverage is
[coverage_summary_v5.json](coverage_summary_v5.json), and the scope and pending
scientific/hardware requirements are in [PREFLIGHT.md](../PREFLIGHT.md).
[Final critical review passed](../review/PREFLIGHT_critical_v2.md). Only this complete
attempt supports the current bounded local compatibility claim.

| Preserved receipt | Status and use |
| --- | --- |
| [contracts_v1.json](contracts_v1.json) | SUPERSEDED_INCOMPLETE_HARNESS; 16 observed rows retained; no global certification |
| [preflight_v1.json](preflight_v1.json) | INVALIDATED_RUNNER_DEFECT; shared output paths could overwrite original predictions |
| [preflight_v2.json](preflight_v2.json) | SUPERSEDED_INCOMPLETE_HARNESS; integrity and semantic fixtures incomplete |
| [preflight_v3.json](preflight_v3.json) | SUPERSEDED_INCOMPLETE_HARNESS; worker top-level status propagation incomplete |
| [preflight_v4.json](preflight_v4.json) | SUPERSEDED_INCOMPLETE_HARNESS; exception receipt, unique preprocessing identity and timeout propagation incomplete |
| [contracts_v3.json](contracts_v3.json) | MERGE_ENGINEERING_PHASE_PASS; 20 contract rows only, before the final ablation filtering fixture |
| [preflight_v5.json](preflight_v5.json) | MERGE_ENGINEERING_PASS; 21 contract, 100 paired build and 96 paired reload rows |
| [auxiliary_configs_v1.json](auxiliary_configs_v1.json) | PASS; two non-model JSON structure/byte-preservation checks; no HLS claim |

Earlier receipts are retained for audit and are not alternative current evidence.
Per-worker requests, results, logs and separate inference arrays live under each
attempt directory. Source captures and local arrays/checkpoints are not publication
payloads.
