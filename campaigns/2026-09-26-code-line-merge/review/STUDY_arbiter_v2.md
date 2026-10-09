# Arbiter review — STUDY v2

Date: 2026-10-01. Verdict: **ITERATE — design only**.

Reviewed `STUDY_v2.md`, all three `review/STUDY_*_v2.md` reports,
`docs/methodology/06-review.md`, `docs/conventions/quantization-and-cost.md`,
and the inventory generator's source/checkpoint identification code. No v3
artifact was reviewed. No runtime execution, checkpoint arrays, pipeline edits,
network actions or scientific results are part of this review. No validator
report or earlier arbiter report was supplied; no figure check applies.

The physics review's PASS supports the bounded compatibility question and its
separation from physics claims. It does not resolve the recoverable-baseline,
metric-scope and width-validation defects identified by the other reviewers.
The source text supports those findings. Under methodology §6.1 and §6.5.1,
the following A and B findings remain binding before design PASS.

| Finding | Resolution and required revision |
| --- | --- |
| Critical A1: historical metric scope | **Upheld, A.** `STUDY_v2.md`, D6 item 4, asserts universal historical validation replay without naming each applicable metric/reference. The quantization convention's required check 3 does require metric agreement within `1e-7`, TF32 off; synthetic output agreement cannot replace it. Distinguish the local original-versus-merged output gate, applicable historical metric reload with its named metric/reference/split/source, and missing evidence. A config with no historical run does not acquire an invented metric target. Keep applicable missing checks pending and describe any NRP replay as a separately authorized dependency. Propagate this distinction to the completion gate, conventions table and plan. |
| Critical A2: original source bytes | **Upheld, A.** D6 item 1 archives hashes, while the publication original is also D1's edit destination. Capture both actual working source/config trees in content-addressed, read-only reference bundles before edits. Record full manifests and bundle hashes; execute baseline subprocesses from those captured bytes. A Git SHA or file digest cannot replace the missing original bytes. Reference artifacts are permitted within the canonical lab and must not become another active editing tree. Captured current originals remain distinct from historical training provenance. |
| Constructive A1: learned widths | **Upheld, A.** The conventions explicitly require stored widths to match remeasured widths; D6 has no check or applicability state for that requirement. Add per-checkpoint binary-effective-value and width-validation rows, preserving the actual stored-versus-remeasured requirement. Stored-versus-reloaded-state comparison can supply engineering evidence but cannot silently stand in for remeasurement. Identify the checker and required calibration/source context; unavailable prerequisites remain pending. Justify non-applicability for FP32/nonbinary cases separately. |
| Critical B1 and constructive B1: maintained preflight/interfaces | **Upheld and consolidated, B.** Name the replacement preflight harness and explicitly amend the obsolete `preflight_final.sh` invocation. Specify bounded executable tests for changed CLI/import contracts, alias signature and argument forwarding, public/explicit paths, opt-in tracking without credential lookup/network, teacher/checkpoint arguments, and generators writing into temporary directories. Cover binary symmetry and define success from the declared matrix; distinguish complete local engineering coverage from pending historical validation. Syntax, shape and inference checks alone do not cover these promises. |
| Physics B1: selection/evaluation behavior | **Upheld, B.** D2 promises unchanged schedules, selection and evaluation, but fixed-checkpoint inference does not exercise them. Add bounded fabricated-record/fixture checks for affected callback/schedule configuration, budget-feasibility and checkpoint selection, preprocessing, row order, label-score alignment and score dtype. No optimizer step or scientific replay is required for these contract tests. |
| Physics B2: probe content | **Upheld, B.** D6 item 3 specifies deterministic probes only by shape. Declare nonconstant and supported zero/padding, sign and quantization-boundary probes, with generation parameters/hashes. Exercise adapted preprocessing/evaluation entry points. These are finite regression checks, not a universal equivalence proof. |

The C suggestions can be incorporated before commit without a separate review:
concrete CPU subprocess/resource limits and timeout-as-incomplete handling
(critical C1); separate absent/disabled/enabled uncapped/enabled capped pT
fixtures plus deliberate label mismatch (constructive C1); normalized
graph/quantizer configuration comparison and complete source/checkpoint/
preprocessing/environment identities per matrix row (physics C suggestions).
None authorizes training or changes a scientific tolerance.

The reference standard for this phase is paired engineering behavior on identical
inputs, with recoverable originals and explicit coverage. No performance gap,
seed interval or physics reference table is being claimed. The inventory's
metadata hash matches are lookup candidates: its generator has not read checkpoint
content, and the historical short config hash is not sufficient identity evidence.
Missing mappings stay visible; alias similarity does not establish provenance.

Revise these design commitments and obtain written panel re-review before
implementation advancement. After design PASS, the already authorized bounded
local implementation can proceed while applicable unavailable historical checks
remain pending. That PASS will not establish full historical validation, retire
uncovered entry points, clear Chang K1 or Delta gates, authorize a cluster launch,
or establish hardware readiness. No finding is dismissed or downgraded here.
