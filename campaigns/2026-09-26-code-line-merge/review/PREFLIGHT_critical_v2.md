# Final critical review — PREFLIGHT v2

Date: 2026-10-01. Verdict: **PASS — bounded local engineering compatibility only**.

Reviewed `PREFLIGHT.md`, `STUDY_v3.md`, the final controller/worker, the complete
`evidence/preflight_v5.json`, compact coverage, config identity map, auxiliary JSON
receipt, prior-attempt index and the proposed publication summary
`publication/docs/current-work/CODE_COMPATIBILITY_20261001.md`. This review closes
the provisional findings in `PREFLIGHT_critical_v1.md`. No remaining A or B finding
blocks the stated engineering claim.

## Independent evidence

The final receipt has **217 unique passing rows: 21 contracts, 100 paired builds,
and 96 paired reload tuples**. Its SHA-256 is
`ef11f6c832b17479c7341b3d24b5b3aebcf9f006e2d2924b8839c9bf21851115`.
The candidate manifest is
`dfd1f68324dfa4f2f8eb68f8da3875d7209d89c8bb7d43848201abd260dc9de0`;
controller and worker hashes match the final receipt and the independently inspected
static closure. Captures, inventory association, environment lock and current
candidate files were independently hash-checked.

The durable independent check is
[`PREFLIGHT_independent_audit_v5.json`](PREFLIGHT_independent_audit_v5.json).
The exact 100 originating-side/config identities match the declared inventory.
Original/candidate parameter counts, shapes, normalized graph hashes and quantizer
state agree; worker results are successful, not merely nested PASS records.
Independent reconstruction from inventory and content/preprocessing hashes yields
exactly the same 96 reload tuples, representing 94 config/seed names and 206 mapped
paths; the 74 unmapped paths also match exactly.

After the owner's workers finished, this reviewer loaded **all 96 saved output
pairs using NumPy only**. Paths and underlying files were distinct, output hashes
matched, shapes/dtypes agreed, and all values were finite. Independent subtraction
in float64 found **maximum absolute difference 0.0 for every pair**, agreeing with
the recorded results and the required <= 1e-7 engineering tolerance. No model was
reloaded, no scientific dataset was read, and no model execution was repeated.
Each checked row and its files/hashes are retained in the independent audit.

The 68 D4 alias-map pairs were separately checked against config bytes in the
captured archives: both exact file hashes, both full normalized hashes, matching
architecture/quantizer fields, and every differing field path agree. The compact
summary binds this map by hash. Both auxiliary JSON receipt hashes match captured
public bytes and the inspected static validator. The five controller regression
tests passed during independent static closure; their unchanged code did not
justify another run. Fixture design is additionally reviewed in
`PREFLIGHT_contracts_v3.md`, including actual final-target admission logic.

## Prior findings resolved

| Finding | Resolution and evidence |
| --- | --- |
| **A1: shared output overwrote the original** | Worker output uses a directory unique to its result path (`preflight_worker.py:124`); parent checks separate files and content hashes and snapshots the original before candidate execution (`preflight_merge.py:91`, `:200`). Negative regression coverage rejects shared paths/corruption. All 96 independent comparisons above confirm actual isolation. |
| **A2: mapped alternative checkpoints omitted** | Filename restriction is removed. The complete reconstructed tuple set includes the three mapped `model_unconstrained.keras` identities, including b25, plus 93 `model_best.keras` identities. Full config, seed, checkpoint and preprocessing content determine deduplication/IDs (`preflight_merge.py:271`); 74 unmapped paths remain explicit. |
| **A3: phase-only run emitted full PASS** | `preflight_merge.py:293` emits `MERGE_ENGINEERING_PHASE_PASS` for partial phases. The final receipt has phase `all`, complete expected coverage and `scope_complete=true`. The evidence index identifies old contracts-only and superseded receipts without treating them as current certification. |
| **A4: unbound inputs/harness and historical provenance overclaim** | Capture/inventory association is checked (`preflight_merge.py:113`); both script identities are checked around every worker. Workers check actual config/checkpoint/preprocessing bytes before and after use (`preflight_worker.py:100`, `:135`). Candidate end rehash remains in place, and outer failures retain invalid receipts. Full current hashes are recorded while short metadata hashes remain lookup associations, explicitly not original training-source proof. |
| **A5: stale result or nonzero worker could pass** | Fresh evidence destinations are required (`preflight_merge.py:31`); `process_outcome` and `comparison_status` require successful top-level worker outcomes (`:35`, `:43`). Tests cover nonzero exit despite nested PASS, TIMEOUT propagation, reuse refusal and durable exception receipts. Final worker records all exit successfully. |
| **B1: missing legacy callable** | `publication/code/hgq2/convert_final.py:5` supplies `run_convert_final`; the final core fixture asserts identity with the canonical callable (`preflight_worker.py:196`). |
| **B2: generator namespace collision** | Legacy imports use `configs.legacy` (`publication/code/hgq2/configs/legacy/gen_ebops_ablation.py:7`). Final public-first/legacy-first fixtures compare outputs without hiding the collision through isolated imports (`preflight_worker.py:385`); both orders and nine generator comparisons pass. |
| **B3: limit and incomplete-result reporting** | Per-worker file/log limits use `RLIMIT_FSIZE`, group RSS is watched, and timeout/nonzero outcomes propagate. Aggregate exhaustion emits INCOMPLETE; exceptions preserve partial rows as INVALID (`preflight_merge.py:52`, `:86`, `:138`, `:303`). Earlier defective attempts are retained and excluded from the final claim. Session accounting limitation is stated below. |

## Execution accounting and claim boundary

**C1 — Budget wording/accounting clarification, resolved in reporting.** The controller's wall and child-CPU
counters start inside each invocation (`preflight_merge.py:134`), whereas the design
describes session-wide 90-minute aggregate budgets. Thus the implemented limit is
per invocation, not a persisted cross-attempt budget. The recorded attempts span
01:13:06–01:36:37 UTC, **23 minutes 31 seconds**, but final cumulative child CPU
across attempts was not retained. The partial CPU snapshot is explicitly not final.
Neither an exact cumulative CPU total nor blanket session-budget compliance is
established. `PREFLIGHT.md:77` and `:147`, plus the compact coverage's timing fields,
now state this limitation explicitly. No model rerun is warranted to repair unavailable
past accounting. Any future continuation needs a persistent session ledger before
making a session-budget compliance claim.

This limitation does not change the fixed-byte, independently reproduced comparisons
or their resolving power at the stated engineering tolerance. The final report and
outward summary accurately distinguish them from historical scientific validation:
nine research configs, all 62 exact public config identities and 74 checkpoint paths
retain missing or unknown historical coverage. An architecture alias and an
eight-character lookup hash do not establish historical training identity.

The real convention's applicable metric reload tolerance of <= 1e-7 with TF32 off
remains in force. The 204 stored metadata reference candidates still require exact
selected-checkpoint/source/data/split association; synthetic output equality does
not satisfy that metric gate. Selected-checkpoint calibration/width remeasurement
also remains pending. Seed ensembles, uncertainty comparisons and hardware synthesis
are not replaced by engineering counts. Frozen campaign implementations remain
authoritative. This PASS does not retire uncovered entry points, clear Chang/Delta,
authorize cluster execution, or establish full historical or hardware compatibility.
