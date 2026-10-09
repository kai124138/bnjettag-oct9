# Recovery plan — 2026-10-01

Question: which terminal records and durable checkpoints survive for the twelve-run
confirmation queue and Chang pilot b5?

1. Verify the stored historical ConfigMap bytes and inventory without rebuilding or
   executing their code. Record source paths, hashes, identity scopes and uncertainty.
2. Inventory local real observations separately from synthetic readout tests. Preserve
   historical records; write the audit and recovery manifest in this new campaign.
3. Prepare a one-shot collector restricted to `get` and `logs` for the three exact legacy
   Jobs in namespace `cms-ml`, with `user=kai` ownership checks. Store sanitized metadata,
   current/previous logs and receipt hashes. Missing Jobs/pods mean unavailable evidence.
4. List exact PVC artifacts for an existing authorized mounted/export route. Do not create
   a reader workload, fetch credentials, run archived code, resume, or submit anything.
5. Require actual cache `data_info.json`, per-run metadata, checkpoint state and terminal
   evidence before readout or resume decisions. Chang K1 remains pending b5 plus Kai's
   explicit choice of (c) or (d). Review and any new launch belong to later gated work.

Validation: standard-library unit tests for ownership filtering, archive path/inventory
checks, credential redaction, immutable output creation and missing-evidence handling.
No training, model evaluation, synthesis or new scientific result is part of this audit.
