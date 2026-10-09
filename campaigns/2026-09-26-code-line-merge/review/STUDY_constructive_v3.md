# Constructive re-review — STUDY v3

Date: 2026-10-01. Verdict: **PASS — design only**.

Reviewed `STUDY_v3.md`, the prior constructive review and `STUDY_arbiter_v2.md`,
against the existing quantization/cost convention. Checked the named quantizer
helper and metadata-field definitions by reading source. No pipeline changes,
checkpoint arrays, runtime compatibility tests or network operations occurred.

| Prior finding | Resolution and evidence |
| --- | --- |
| A1: learned-width validation | **RESOLVED in the design.** D6 gate 4 (`STUDY_v3.md:211–224`) has independent binary symmetry, state reload and stored-versus-remeasured width rows. It preserves remeasurement, requires the selected checkpoint and calibration/input identity, prevents final-state `act_grid_after` from substituting for selected-checkpoint widths, and leaves unavailable context pending. Nonbinary weights and quantized activations have separate applicability. The cited helpers exist at `publication/code/hgq2/bnhgq2/qat.py:585`, `qat.py:605`, and `ebops_target.py:35`; selected-checkpoint widths are recorded at `train.py:462`, separately from final-state grids at `train.py:484`. This confirms available implementation anchors, not successful checks. |
| B1: executable compatibility interfaces | **RESOLVED in the design.** D5 names the replacement `preflight_merge.py` interface. The fixture table (`STUDY_v3.md:257–265`) requires exact CLI dispatch, optional alias signature/forwarding/return value, paths and environment overrides, import behavior, tracking disabled before credential lookup, teacher/checkpoint branches, and generator identities. Training/conversion/artifact clients are stubbed and unexpected network attempts fail. Runtime success remains an implementation/preflight obligation. |
| C1: pT fixture coverage | **RESOLVED in the design.** Separate rows at `STUDY_v3.md:266–268` cover absent/disabled behavior, enabled uncapped/capped weights using training rows only, unweighted validation/selection, and intentional label mismatch rejection. These directly exercise the existing research integration's row-alignment and training-partition behavior. |

The design now provides actionable implementation contracts without turning this
merge into a new training experiment. It also preserves the important distinction
between engineering evidence and historical validation. D6 gates 5/6 name metric
reference applicability, retain the 1e-7 metric tolerance and TF32-off requirement,
and require separately authorized NRP replay when needed. An unavailable reference
is not invented or passed. `MERGE_ENGINEERING_PASS` is explicitly limited to its
declared local coverage; unknown historical rows remain visible, and observed
mismatches produce failure. Full compatibility and retirement of uncovered old
entry points remain unestablished.

The six review questions are satisfied for a design gate: applicable conventions
have explicit checks or pending states; captured original inputs and complete
identity fields supply the engineering reference standard; the previous missing
interface evidence is now an execution requirement; finite probes and fixed paired
input tolerances do not claim universal equivalence; missing historical evidence
has concrete recovery/applicability paths; and no physics result or pull is claimed.
No additional seed study, cost target or performance claim is needed for this scope.

No outstanding A, B or C findings from this review. This PASS permits the already
authorized bounded implementation after the panel/arbiter gate. It does not certify
the implementation, historical metrics, Chang K1, Delta production, hardware, or a
cluster launch. Preflight must report actual execution evidence and remaining gaps.
