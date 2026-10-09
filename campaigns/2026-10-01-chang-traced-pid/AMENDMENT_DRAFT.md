# Chang traced-cost PID amendment — 1 October 2026

**Draft for design review; no implementation or launch authorization.** Kai chose “(c) Feed traced cost directly into the PID controller.” The [decision record](../../local/2026-10-01-execution/chang-option-c-decision.json) was saved at `2026-10-01T06:00:02.706672+00:00`. The missing complete historical b5 readout remains a prerequisite to finalizing this amendment and advancing its freeze/pilot gates. K1 remains triggered and uncleared; production remains blocked.

The proposal changes the controller's feedback signal and update cadence. It preserves the registered scientific comparison, target budgets, data, selection and statistical rules. The original [STUDY](../2026-09-26-training-batch/STUDY.md), especially slots T/P and Phase 2 (lines 1533–1589 and 1720–1847), supplies all unchanged requirements.

## Source and configuration boundary

Use the historical archive `42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0` as the immutable baseline, with patches 0001–0031 already included. Review and apply a **copy** of [staged patch 0032](../2026-09-26-training-batch/code/patches-staged/0032-option-c-pid-traced-only.patch) only in the new campaign revision inside the canonical lab. Do not move that patch, alter the old campaign tree, incorporate the unrelated engineering merge, or rebuild an archive under its historical identity. This supersedes the old plan's instruction to apply 0032 in the historical tree (lines 1258–1265).

Regenerate the existing **58 logical configurations: 56 production and two pilot-only**. Record a one-to-one old/new config map, all hashes and an exhaustive field diff. The only scientific config additions are explicit `train.ebops.pid_input: traced_only` and `train.ebops.pid_traced_integral: per_epoch`; dated names, group and output provenance must be listed separately. Preserve all arm/seed identities, target values, order seeds, 50 schedules of 7,000 epochs and eight R schedules of 1,000 epochs. No NB/H/FP32-E integration, C′ production expansion or architecture change is included.

Preserve the gated, stable-pT-sorted N64 data and 558,000/62,000 split, train-only normalization, quantizers and dependency pins, WRAP `i_decay_speed=0.001`, C′'s SAT path, optimizer, LR schedules and the existing trace/selection/snapshot cadence. Every checkpoint candidate still saves/reloads/validates each epoch; only traced candidates may enter feasible or minimum-cost selection. Primary and AUC-sensitivity roles remain separate.

Give the new bundle, manifest, ConfigMap, run root, run IDs, Jobs and handoff new identities. Historical regime-A/B checkpoints **cannot initialize or resume a (c) run**: both code/config mismatch guards must reject them, and bypassing those guards would create a hybrid scientific trajectory. Only a checkpoint produced under the identical new frozen code/config may later resume. Preserve all old runs and snapshots as evidence.

## Controller contract proposed for review

Adopt the staged `ablation.run_training` route. The separate `bnhgq2/train.py` callback route currently ignores the new key (old plan lines 1253–1256): reject this configuration there, or make routing validation fail before any run. Do not silently broaden the controller implementation to a second training path.

Keep `p=1.0`, `i=0.05`, `d=0`, warmup 1, initial beta `1e-7`, bounds `1e-10`–`1e-3`, log error and zero damping. With zero-based epoch `e` and trace interval 10:

- Run the existing reset/full-training trace at epoch ends `0, 9, 19, …` and the terminal end. On each traced end, the saved PID input must equal that trace within the registered relative `1e-6` tolerance. Untraced ends never overwrite it with the in-training cost.
- At epoch begin, the warmup branch runs at `e=0`; the integral is seeded by HGQ2 at `e=1`. Further PID updates occur at `e=10, 20, …`. Between updates, beta, integral and previous-error state stay fixed. The last terminal trace has no following update.
- Use the explicit staged **per_epoch** convention. For an update after span `D`, add `D × log10(E_traced/T)` to the integral, through the staged extra `D−1` copies plus HGQ2's normal call. The first seeded step has span 1, the next has span 9, then normally 10. The newest trace supplies the error for the whole elapsed span: this is a rectangular integration convention, not reconstructed errors for the intervening epochs. Integral time units are preserved; historical dynamics are not.
- Keep proportional gain unscaled. Do not switch to `per_step`, lower gains, add anti-windup, adjust targets using ratios, or fit parameters without a separately reviewed amendment. Reject unsupported modes, derivative gain and warmup/trace combinations. Persist and audit `pid_stepped`, `pid_step_span`, `pid_integral`, beta, PID input, genuine in-training cost and traced cost with explicit epoch semantics.

The unchanged gains isolate the feedback remedy and retain the registered recipe. `per_step` would reduce the effective integral action roughly tenfold and can place convergence beyond epoch 500. **Neither choice is established stable.** Existing synthetic examples contain fast-response failures in both modes; the historical response fits are confounded by training drift, cover only early high-LR history and give a “not established” verdict for `per_epoch,p=1` (old plan lines 1200–1238 and 1288–1337). There is no new fit or stability claim here. Clamped beta has no anti-windup; infeasible arms still need the registered floor/rule treatment.

One canary check must follow the new cadence: the old epoch-10 beta-movement check (STUDY lines 1860–1865) precedes the first non-seeding PID update under (c). Keep epoch-10 finite/falling-loss and traced-cost checks unchanged, but evaluate controller movement at **one-based epoch 11** (`e=10`), after the epoch-10 trace. Require the recorded update, span 9, correct traced input and HGQ2 formula; initial integral seeding or rounding differences do not demonstrate feedback action. Confirm this schedule in CPU fixtures before the pilot. The later timing, RSS and stop rules remain in force.

## Required gates, in order

| Gate | Required evidence before advancement |
| --- | --- |
| Historical closure and design | Complete the original b5 CPU certification, entropy, attention/floor readout, genuine in-training/traced telemetry, both-A-seed assessment, C′ constraint quantities and registered matched regime-A/B table, alongside the existing b3 evidence. Resolve missing inputs explicitly; copied checkpoints and stored-cost checks do not certify them. Review this dated amendment and the unchanged-gain pilot risk. |
| Implementation and all-58 audit | Implement only the reviewed controller, generator/provenance and routing guard changes. Check every generated config against its old logical identity. Re-run the full CPU suite and applicable STUDY A1–A21 gates on a fresh extraction of the candidate freeze, including LR boundary values, optimizer, preprocessing, binary weights, WRAP/SAT semantics and selection/tie/sensitivity rules. Historical 100-pass/2-skip evidence is a baseline, not a new pass. |
| Controller and persistence | Exercise the actual training route with bounded CPU fixtures: input equality, untraced hold, warmup, spans, terminal trace, finite checks and PID logs. Verify uninterrupted versus resumed execution across an untraced checkpoint and the epoch-500 LR boundary; retained selections roll back to the committed generation. Reject old code/config resumes. Re-run absent-key compatibility against exact 42abed for both historical trace regimes. |
| Floors, pairing and identity | Re-trace every registered arm's zero-bit, one-bit-alive and narrow/full attention floors with HGQ2's own path, including E1/C′. Record deviations from historical references; retain `STATIC_INFEASIBLE` rows. Re-run A/B/D/R versus F shared-kernel pairing at all eight seeds; only the positional table may differ, otherwise apply the registered Welch fallback for all. Recheck the initialization fingerprint, exact cache identity and fixed non-degeneracy threshold from the same validation labels; do not borrow a synthetic fingerprint or re-estimate the threshold from pilot outcomes. |
| Readout and supported handoff | End-to-end CPU fixtures must cover feasible primary and sensitivity certification, min-cost fallback, entropy and missing-input failure. Freeze actual working contents with the supported campaign mechanism; prepare the factual brief, hash-verified handoff and `nrp_doctor` lint. Record selected GPU product, resource limits, durable telemetry and original stop/retry rules. Any pilot launch needs its scoped authorization; a design pass supplies none. |
| Fresh replacement pilot | Run the registered eight logical pilots from initialization: A-s1/s2, D-s1, C′-s1, E1-s1, A07-350-s1, C-s1 and F-s1. Keep full training schedules in configs and stop at the epoch-500 boundary. Apply the cadence-adjusted canary above, plus RSS/failure isolation and timing gates; choose product/packing under the current measured-resource policy, repeat product-specific fingerprint/cost/memory/timing checks and recalculate the 14-day production projection. Each paired seed comparison uses the matched product. |
| Replacement readout and production decision | Require real epoch-500 snapshot-role inventory, CPU full-train cost certification with registered tolerance/adjudication, entropy/collapse and Q/K/V widths, headroom, feasibility/degeneracy, both A seeds, A07 expectation and C/C′ constraint-active quantities. Audit actual PID input/hold behavior throughout the pilot. Report beta saturation and oscillation evidence without retrospective threshold fitting. Re-review scientific and operational gates before a production decision. |

The A stopping condition remains **neither** seed has a qualifying checkpoint; evaluating both seeds does not require both to be feasible (STUDY lines 1725–1731). C′ remains descriptive/pilot-only unless Kai adds it. Pilot validation values select no arm, alter no primary rule and support no performance claim.

Retain the historical K1 ratios and interpretation. Under (c), an in-training/traced ratio different from one does not by itself demonstrate incorrect PID input: verify that the controller consumes the trace and holds between traces. The old slot-P implied-offset model is not a new (c) acceptance threshold. The epoch-500 pilot also does not observe the first trained-model LR restart after that boundary; CPU boundary tests cannot establish its physical stability. Keep later-cycle stability as an explicit limitation under the registered production monitoring/stop rules, not a cleared risk.

## Remaining work and decisions

1. Finish historical readout and independent design review; accept or revise this exact integral/gain convention before implementation is frozen.
2. Implement the bounded patch/routing guard, regenerate/map all 58 configs, and make controller telemetry durable independently of stdout/W&B availability. Audit the real fields needed by the readout.
3. Produce fresh CPU, resume, floors, pairing, fingerprint and readout-fixture evidence; then the reviewed freeze, resource projection, handoff and replacement pilot/readout.
4. Stop advancement on unresolved input/hold defects, certification mismatch, failed registered gates or unexplained instability. Do not repair those by changing gains, tolerances, data or selection during a run.

No repeat (c)/(d) decision is needed. Kai's choice does **not** settle gain tuning, a new open-loop beta-step/dither experiment, an extended restart pilot, retargeting, new arms or a dependency change. Those become explicit user decisions only if proposed after review; none is adopted or launched by this draft. The immediate proposal is the staged `per_epoch`/unchanged-gain candidate subject to the gates above.

## Evidence identities

SHA-256 values below identify sources inspected for this draft; they are not new scientific measurements. Paths for the study, plan and staged evidence are relative to `campaigns/2026-09-26-training-batch/`.

| Source | SHA-256 |
| --- | --- |
| Decision record linked above | `bccbc0adc43ec0063aeae15da7ecfabdb2f6b2fc7c498eb86391d9d6d5a5918b` |
| `STUDY.md` | `7659e1039b4f18e902151bdac5e020571e700a508b1a566c32f13b08d97fd5a9` |
| `plan.md`, staged design/tests and stability limits, lines 1168–1337 | `a8e72a4f3d5708c9103cd8d0bdb2238c92d61ac24ba035432d29166aa216a6ea` |
| `code/patches-staged/0032-option-c-pid-traced-only.patch`, contract lines 30–163 | `f475c69e487ff20f66d8d39e45b89f6775b11354d419b81746b01cd7a25508be` |
| `code/staged-option-c/evidence/pytest_staged_option_c.log` | `78cb5d997433788f7a204040840a36c7cd74e5abc7207552ce9b269fa0683b14` |
| `code/staged-option-c/evidence/sim_pid_traced_only.log` | `e5295ef19ea7c921748468138f4524fca5743a3460e00c9b475c8e4d73e19ede` |
| `code/staged-option-c/evidence/fit_b_tau.log` | `c3ccd5736eefb6e23eaec148f6e9cae7feb960825a295a1e11826146ea8e5876` |
| [Recovered metadata inventory](../2026-10-01-recovery/PVC_READOUT_REVIEW.md) | `e48d42ec05c5d229c17569a76941adb88ff87970085df64ac1cdccdaa99c3d28` |
