# Arbitration — STUDY v3

Date: 2026-10-01. Verdict: **PASS — design only**.

Inputs: `STUDY_v3.md`, the v2 arbiter findings, and the physics, critical and
constructive v3 reviews. All three reviewers return PASS with no outstanding A or B
findings. The orchestrator performed this adjudication after the attempt to resume
the separate arbiter was rejected by the agent thread limit. The adjudicator did
not author the merge design or any of the three panel reviews.

The three earlier A findings are resolved: metric-reference applicability is
explicit, actual original source bytes are recoverable, and stored-versus-remeasured
width checks remain separate from state equality. The executable interface,
selection/evaluation and deterministic probe requirements resolve the B findings.
Resource limits and complete identity rows resolve the retained C suggestions.
The critical reviewer independently verified all captured source members and the
204 metadata reference candidates. The orchestrator additionally checked both
archive/manifest hashes, archive path safety and embedded manifest equality.

No finding is downgraded or dismissed. The reviewers agree on both advancement and
its limits, and the artifact supports their conclusions. Prose lint passed with
score 2 and no blocking finding; there are no figures or launch manifests to
validate at this design gate.

Advance to the authorized local implementation and bounded engineering preflight
in the existing canonical publication directory. Preserve the exact config bytes,
public defaults, source archives and two unrelated modified result documents.
Record missing historical evidence, failed checks and resource exhaustion without
converting them to PASS. Critical review of the resulting PREFLIGHT is required.

This decision does not certify executed compatibility, historical metric or width
reproduction, retirement of old entry points, Chang or Delta readiness, synthesis,
or any cluster launch. No scientific threshold or schedule changes.
