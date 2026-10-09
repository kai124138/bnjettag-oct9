# Physics/engineering review of STUDY_v3

Date: 2026-10-01  
Verdict: **PASS — design only.**

Scope: reviewed `STUDY_v3.md` against the stated BNJetTag compatibility thesis and this reviewer's v2 findings. No implementation, arrays, training, or experiments were inspected or executed. Artifact assertions about captures and reference inventories were assessed as design inputs, not independently verified results.

Both prior B findings are resolved in the design:

- **Selection/evaluation coverage:** the required contract rows now compare callback and schedule boundaries, cap feasibility, final-target filtering, ties, row permutation and separation, normalization, label/score alignment, dtype, and explicit preprocessing. The pT fixtures separately cover absent/disabled, capped/uncapped, train-only normalization, unweighted validation/selection, and misalignment rejection. These are observable checks that require no optimizer steps.
- **Probe specification:** gate 3 now names deterministic nonconstant, zero, occupancy/padding, supported sign, and quantization-boundary probes, records their construction and hashes, and exercises adapted preprocessing/evaluation entry points. The explicit finite-suite limitation is appropriate.

The prior C suggestions are also incorporated: normalized graph/connectivity/quantizer comparisons supplement counts and shapes; coverage rows identify both source manifests, full config, checkpoint, preprocessing, environment, and probe hashes. Short historical config hashes remain lookup keys only.

No changed physics or selection is proposed. D2 preserves graph/quantizer behavior, schedules, splits, row order, checkpoint selection, and feasibility; optional pT behavior retains its original semantics and defaults. The new fixtures test those contracts rather than introducing a new metric or selection rule. Applicable historical metric replay remains distinct from synthetic inference, and unknown reference associations cannot become PASS. Captured current sources are explicitly not asserted to be historical training sources.

**A — must fix:** none for design approval.  
**B — should fix:** none outstanding from this review.  
**C — suggestions:** none additional.

This PASS permits the stated bounded engineering implementation and checks. It does not establish implemented equivalence, historical metric reproduction, hardware readiness, or authority to retire uncovered entry points or launch scientific work. Those claims remain dependent on the recorded gates and their evidence.
