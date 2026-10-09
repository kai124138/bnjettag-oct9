---
id: 2026-09-26-code-line-merge
date: 2026-10-01
type: engineering
status: engineering-pass
critical_review: review/PREFLIGHT_critical_v2.md
design: STUDY_v3.md
evidence: evidence/preflight_v5.json
---

# Code compatibility preflight

The bounded local engineering gates pass: 217 of 217 rows, comprising 21 contract
checks, 100 paired config builds, and 96 paired checkpoint reload comparisons.
The final executable receipt is [preflight_v5.json](evidence/preflight_v5.json);
[coverage_summary_v5.json](evidence/coverage_summary_v5.json) gives the config-by-config
coverage and unresolved historical rows. [Critical review passed](review/PREFLIGHT_critical_v2.md)
for this bounded engineering claim.

This result permits review of the implemented compatibility changes. It does not
establish full historical metric compatibility, authorize retirement of uncovered
entry points, clear scientific schedules, or establish hardware readiness. No training
step, optimizer update, real-data scientific metric calculation, HLS run, or cluster
submission occurred in this preflight.

## Implementation and preserved inputs

The candidate is the existing `publication/code/hgq2` tree, based on verified public
commit `6da5003`. Only two existing public modules change: `train.py` gains the research
tree's optional pT weighting integration, and `convert.py` gains a legacy callable
alias. The port adds the pT utility and evaluation entry points, six historical command
aliases, historical check scripts and generators, and 38 exact research model configs.
Namespaced historical generators avoid collisions with the existing public generators.
The public paths, tracking opt-in, teacher arguments, defaults, and all 62 existing
model config identities remain unchanged. `COMPATIBILITY.md` records supported entry
points and scope. The two unrelated modified public result documents are outside this
change.

The actual original source bytes were captured before implementation, rather than
reconstructed from a Git revision. [capture_20261001.json](originals/capture_20261001.json)
binds the archives and full file manifests: 102 research files and 109 publication
files. Original workers consumed verified, read-only, disposable copies of those
archives. Candidate and harness hashes were checked throughout execution. Historical
training-source identity is a separate unresolved provenance requirement.

| Input | SHA-256 |
| --- | --- |
| Candidate file manifest | `dfd1f68324dfa4f2f8eb68f8da3875d7209d89c8bb7d43848201abd260dc9de0` |
| Research original manifest | `a075c10e801b8a8555c33239ce8b102f30133352fe1c6235aadc3d32f075a52f` |
| Publication original manifest | `b46b687cd8ece7eacb3ecb7be47d66fac055c8e6015303c64aadc520984b47fb` |
| Reviewed inventory | `555464bc21d4a21a02f67c8d8042cedfd256e47a4b661e3fb1e61537f65472a5` |
| Preflight controller | `cbf9bc98496ef1326ddd3dc7d02b508bdcf76e66cde9790785493edb2e48e2b6` |
| Preflight worker | `250c4e36eb70b51c94e13602b2d9764e9f40a43692942f394fc93e59c1cc1b23` |
| Environment lock | `d8950ec91583cfc77e98c6ed4f437eb692167ab21ef3c1b25178efd038f1fb93` |

The D4 [config identity map](config_identity_map_20261001.json) lists 68 pairs with
matching architecture/quantizer fields, both full normalized-config hashes, both exact
file hashes, and every differing field path. These pairs are not interchangeable
training or checkpoint identities. Historical short config hashes serve only as
lookup keys; exact current config and checkpoint bytes are recorded in each reload row.

## Executed checks

The final command, run from the lab root, was:

```sh
/home/kaimoe/lab/.venvs/preflight-20261001/bin/python \
  campaigns/2026-09-26-code-line-merge/preflight_merge.py \
  --phase all \
  --output campaigns/2026-09-26-code-line-merge/evidence/preflight_v5.json
```

The pinned CPU environment uses Python 3.12.13, TensorFlow 2.21.0 and Keras 3.15.0;
the complete lock is `/home/kaimoe/lab/environment-records/preflight-20261001/requirements.lock`.
The controller disables GPUs, TF32, oneDNN optimization and W&B tracking, limits compute
threads to two, and blocks network access in workers. Each build/reload worker has a
180-second wall limit, 120-second CPU limit and 8 GiB process-group RSS limit; contract
workers have a 30-second wall limit. The controller enforces 90-minute aggregate wall
and child-CPU budgets per invocation and 1 MiB log/file limits. Its counters reset
between attempts; session-wide cumulative child-CPU compliance was not established.
One worker runs at a time.

| Gate | Result and scope |
| --- | --- |
| Source/interface contracts | PASS, 21 rows: exact config bytes; public and legacy imports/CLI/path/tracking; teacher dispatch; callback and schedule boundaries; delivered-checkpoint and final-target filtering; data/evaluation wiring; pT absent, disabled, actively capped, uncapped and misaligned-label cases; public-first and legacy-first generator import order; nine generator comparisons |
| CPU config builds | PASS, all 100 exact config identities, each built from its captured originating source and from the candidate at seed 1; normalized graph, parameter count, input/output shape and quantizer state comparisons passed |
| Non-model JSON | PASS, separate structural/byte-preservation receipt for the 13-entry layer override and 15-entry batch index; every indexed config and the reference config exists, names and seeds agree; HLS applicability remains pending |
| Engineering checkpoint reload | PASS, 96 distinct config/seed/checkpoint/preprocessing content tuples, covering 206 mapped paths and 94 config/seed names across 29 research configs |
| Synthetic inference comparison | PASS, maximum absolute output difference 0.0 across the 96 original/candidate pairs; required tolerance <= 1e-7; 24 deterministic float32 examples per identity, seed 20261001 |
| Binary effective values | PASS for applicable binary layers; nonbinary weight rows are explicitly not applicable, without treating their activation widths as exempt |
| Stored/reloaded graph and quantizer state | PASS for mapped engineering comparisons; equality of state is distinct from width remeasurement |
| Stored versus remeasured widths | PENDING original selected-checkpoint/calibration references and input identity |
| Historical metric reload | UNKNOWN_APPLICABILITY pending selected-checkpoint/reference/source/data association; no metric target was invented |

Probe inputs include zero, fixed nonconstant, padding, signs, and adjacent float32
values around representative quantization boundaries. Original and candidate workers
use the same recorded preprocessing. Only `shared_object_id` is removed when normalizing
serialized model graphs. Each worker verifies config, checkpoint and preprocessing
hashes before and after use. Original predictions are saved separately, hashed before
candidate execution, and checked for overwrite; file paths must differ. This finite
regression suite is not a claim of universal functional equivalence or accuracy.

The precision coverage is 48 W1A8, 12 W1A4, 12 W1A6, 12 W8A8 and 12 FP32 content
identities. Three mapped `model_unconstrained.keras` identities are included alongside
93 `model_best.keras` identities. Inclusion does not certify budget feasibility or
scientific checkpoint selection.

The non-model JSON check is reproducible with
`python3 campaigns/2026-09-26-code-line-merge/validate_auxiliary_configs.py`;
its receipt is [auxiliary_configs_v1.json](evidence/auxiliary_configs_v1.json).
Five targeted, non-ML controller regression tests passed and were independently
repeated in critical review: nonzero exit despite nested PASS, timeout propagation,
separate prediction paths/unchanged baseline, reused-output rejection, exception
receipts, and unique identities including preprocessing. The final candidate/controller/
worker bytes remained unchanged after the static review closure.

## Missing historical coverage

The scoped inventory has 74 checkpoint paths without an established exact attributable
config identity. They remain explicit `UNKNOWN_APPLICABILITY` rows in the compact
summary. Nine research configs lack mapped checkpoint evidence: b50, the standalone
long-budget config, and all seven EBOP ablations r0–r6. All 62 exact public config
identities lack an exact named/hash checkpoint match in the scoped roots. Renamed public
configs are not silently certified by research counterparts. These are inventory gaps,
not evidence that the configurations were never run.

The 204 metadata-reference candidates in
[metric_reference_inventory_20261001.json](metric_reference_inventory_20261001.json)
still require association to the selected checkpoint, original source, dataset and
row identities. Where an actual reference is established, historical metric replay
retains the <= 1e-7 tolerance with TF32 disabled; synthetic output equality cannot
replace it. Stored activation state also cannot replace the original calibration and
selected-width references required for remeasurement. Frozen Chang, Delta and Engram
extensions are outside these two source trees and remain separate campaign inputs.

## Failed attempts and review status

Earlier receipts remain preserved in [the evidence index](evidence/README.md).
The first full attempt was invalidated after identifying shared prediction paths that
could overwrite the baseline. Later partial attempts were superseded while correcting
worker-exit aggregation, immutable input binding, timeout/exception receipts and
preprocessing identity. None supplies the final reload claim. The phase-only contracts
receipt likewise supplies no full-run certification. Regression fixtures now exercise
the observed controller defects.

The final run started at 01:27:18 UTC and finished at 01:36:37 UTC on October 1. Its
559.729 seconds include a pause of approximately 116 seconds for static review; these
times are operational receipts, not a throughput comparison. Earlier interrupted
attempts retain last-persisted elapsed times, which are lower bounds. Final cumulative
child CPU across the earlier attempts was not recorded and is not reconstructed as an
exact measurement. This is a limitation against the design's session aggregate budget;
the per-invocation limit cannot be reported as a measured cross-attempt CPU total.

Design approval is [STUDY_arbiter_v3.md](review/STUDY_arbiter_v3.md).
The separate [contract review](review/PREFLIGHT_contracts_v3.md) and
[final critical review](review/PREFLIGHT_critical_v2.md) passed. Scientific replay,
the full approved schedules, seed-matched uncertainty evaluation and successful
synthesis of current constrained hardware candidates remain separate requirements.
