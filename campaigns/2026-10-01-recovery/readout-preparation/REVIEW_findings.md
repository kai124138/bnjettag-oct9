# Readout preparation: preliminary critical findings

Status: **ITERATE — active preparation, no final frozen-package verdict yet**. Review is local and engineering-only; no model/array loading or remote operations.

The original compressed payload is byte-identical to `configmap-42abed4b.json`, SHA-256 `42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0`. All 41 candidate positive input identities match the recovered export receipt. Historical index rows 0, 1, 24, 56 and 57 match the five declared arms and config hashes. Original CPU certification/entropy commands retain their inputs, split and selection semantics. No feasible checkpoint is invented for the three arms without one; K1/production remain pending.

| ID | Finding and minimum correction | Initial resolution |
| --- | --- | --- |
| A1 | `prepare.py` used distribution `hgq`, while original requirements and `run_study.manifest()` use `hgq2`. Runtime metadata lookup would fail before either readout. Use the installed distribution name. | Corrected in current draft. |
| B1 | `driver.export()` could call a partial export emitted, and the terminal `missing=none` ignored missing telemetry and nonzero subprocesses. Enumerate every required artifact, distinguish emitted-complete/incomplete, and derive exit/status from all missing/refused outputs and subprocess outcomes. | Current completion guard and synthetic cases address this. |
| B2 | Aggregate export limit was checked after reading and caught without stopping subsequent reads. Stop at aggregate exhaustion and cap reads by the remaining allowance. | Current draft stops later reads; the small-budget fixture passes. |
| B3 | `receive.validate_objects()` relied on dictionary subset checks. Independent fixtures demonstrate acceptance of an unreviewed init `PYTHONPATH` and a `/data` mount `subPath=other`. Compare sensitive execution/mount/resource fields exactly after the specifically allowed admission normalization; test init environment/arguments and subpaths. | Sent to owner; final recheck pending. |
| B4 | `receive.decode()` accepted a two-file identity/result envelope while silently omitting the nine other expected artifacts. Require all eleven allowed names as accepted or explicit missing/refused entries. | Sent to owner; final recheck pending. |
| B5 | Original entropy code consults five run-root `DIVERGED.json` markers, which are missing in recovered evidence but absent from the positive-input inventory. Bind their expected absence before and after computation so a new marker cannot silently change selection. | Sent to owner; final recheck pending. |
| C1 | Runtime prose claimed both original scripts explicitly disable TF32; only certification does. Keep historical entropy unchanged and describe its CPU-only route accurately. | Corrected in current draft. |

Initial independent checks: nine synthetic transport tests and all 18 existing `tests/test_run_handoff.py` tests pass. These tests perform no scientific computation. Final PASS requires the corrected receiver and complete frozen handoff/brief/authorization reference, targeted regression coverage and lint evidence. This ledger is not scientific clearance, and no repeated user authorization is presumed where the original finish-readout instruction already applies.
