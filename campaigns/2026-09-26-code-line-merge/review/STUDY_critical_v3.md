# Critical review — STUDY v3

Date: 2026-10-01. Verdict: **PASS — design only**.

Reviewed `STUDY_v3.md`, `plan.md`, the v2 critical and arbiter reports,
`originals/capture_20261001.json`, its archives/manifests, and
`metric_reference_inventory_20261001.json`. Applied the methodology and conventions
read for v2, including `quantization-and-cost.md:43-45`. This review used source and
metadata inspection plus content hashing only: no ML runtime, checkpoint tensors,
dataset arrays, scientific recomputation, network or cluster access. No validator
report was supplied; no figure check applies.

## Resolution of earlier findings

| Finding | Evidence and resolution |
| --- | --- |
| Critical A1: historical metric scope | **RESOLVED.** `STUDY_v3.md:161-176` cites the actual metric convention and distinguishes reference candidates from applicable selected-checkpoint references. Lines 225-245 retain the 1e-7 metric tolerance and TF32-off requirement, leave unresolved associations/inputs pending, and separate local implementation from authorized NRP replay. `plan.md`, “v3 remediation and execution handoff,” carries the same distinction. No universal validation target is invented for every config. |
| Critical A2: executable original source bytes | **RESOLVED.** `STUDY_v3.md:143-159` names actual source bundles and requires hash verification before baseline execution. Independently checked archive and manifest SHA-256, 0444 modes, exact inventory membership, every member size/hash, and embedded manifest equality: **102 research and 109 publication source files passed**. Each archive additionally contains its embedded `SOURCE_MANIFEST.json`. Baselines must use these captured bytes, and the design correctly distinguishes them from historical training-source provenance. |
| Constructive A1 / arbiter A3: learned widths | **RESOLVED in design.** Lines 211-224 provide separate binary, stored/reloaded-state and stored-versus-remeasured-width rows; name existing checkers and selected-checkpoint references; prohibit using final-training widths as selected widths; and retain missing calibration/provenance as pending. State equality does not substitute for remeasurement. |
| Critical B1 and constructive B1: preflight and interfaces | **RESOLVED in design.** Lines 109-118 explicitly replace the old shell invocation with `preflight_merge.py` and specify its interface. Lines 247-268 require executable CLI/import/path/tracking/teacher/generator/alias fixtures, including no credential lookup when tracking is disabled. Lines 197-198 retain the binary gate. Lines 235-245 define distinct engineering pass, incomplete and failure outcomes without claiming historical validation. |
| Physics B1: selection/evaluation behavior | **RESOLVED in design.** The fixture table separately tests callback/schedule boundaries, cap feasibility, ties, preprocessing, row order, label-score alignment and dtype using fabricated inputs and stubbed execution. |
| Physics B2: probe content | **RESOLVED in design.** Lines 199-210 specify deterministic nonconstant, zero/padded, sign and quantization-boundary probes, with hashes and generation parameters; adapted preprocessing/evaluation entry points are included. The finite-suite limitation is explicit. |
| Critical C1 and consolidated C suggestions | **RESOLVED.** Lines 286-297 define enforceable local execution limits and exhaustion reporting. Lines 178-198 require full provenance and normalized graph/quantizer comparisons. The fixture table separates absent/disabled/enabled capped/uncapped pT behavior and a deliberate label mismatch. |

## Evidence and remaining execution obligations

Independently hashed all **204** referenced metadata files and checked config, short
hash, seed, metric-field presence and sample-count fields against the reference
inventory. All matched; every reference remains `PENDING_PROVENANCE`. These are
metadata checks, not recomputed metric results or proof that a reference belongs to
a candidate checkpoint. The inventory retains **71** configs without exact metadata
hash candidates. Short hashes and architecture aliases remain lookup aids; full
source/config/checkpoint/preprocessing identities are required for execution rows.

There are **no unresolved A or B design findings and no new findings**. The harness,
fixtures, CPU builds, reload comparisons and `PREFLIGHT.md` still have to be produced
and reviewed. A required local check may not disappear from the matrix because it
is inconvenient or lacks an artifact. Pending historical rows remain explicit, and
an engineering pass cannot retire uncovered entry points.

Applicable conventions are implemented as design commitments or explicitly deferred
with their applicability/provenance requirements intact. Scientific reference tables,
seed intervals and pulls are not required for this engineering comparison because
it makes no performance claim; captured originals and the coverage matrix supply
the comparison standard. The revised design provides the recoverable inputs and
interface checks an independent reviewer would request, and limits both positive
and negative claims to the evidence available. Artifact recovery was attempted and
recorded rather than assumed impossible. No result in this review needs a physics pull.

This design PASS supports advancement to the already authorized bounded local
implementation after the panel/arbiter gate. It certifies no completed compatibility
test, historical scientific validation, Chang/Delta clearance, cluster launch,
numerical result or hardware readiness.
