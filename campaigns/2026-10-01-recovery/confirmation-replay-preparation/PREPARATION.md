# A02-s3 confirmation replay preparation

Status: offline candidate, not submitted. Design/storage adaptation, independent
review, exact live resource/lint checks and action-time scope remain pending.
[CANDIDATE.json](CANDIDATE.json) names the current content-addressed handoff.

The [source diagnosis](../CONFIRMATION_DIAGNOSIS.md) establishes a selected-metric
assertion failure after epoch300. It does not establish corrupted model bytes,
optimizer corruption or the unique Job-triggering arm. This bounded probe uses
only `confirm0923-a02-s3-e1000`'s retained generation-0300 `model_best.keras`, SHA-256
`21bfcd4faac5bceb8f609945ecfe17f975998560f312d7622fb27daf9ba3bf19`.
It never restores optimizer slots, trains, resumes, selects another checkpoint or
changes the historical tolerance.

The original `26f3cc40…` archive has no actual confirmation A02-s3 config, because
historical confirmation configs came from a separate ConfigMap. The supported
handoff requires its declared selected config inside its source archive. This
preparation therefore makes an explicit **new diagnostic repack**, preserving all
152 historical member bytes, embedding the exact original source ConfigMap and
unchanged compressed archive, and adding the exact recovered config plus three
helpers/scope records. The resulting archive has157files and a new identity; it
is never called the historical archive. The original 22-file source-and-version
manifest must still equal `345a057a64c55075282910bdbedbb3c8a1761fe74ebc2c5a8bf12e5ebbb3e3c0`
at runtime. The saved config's canonical hash stays
`a55d9853f0034caf3b7007847a6eed7ff39d717ed57ca16d866cf13f4fc54a26`.
No historical source/config/ConfigMap/output is rewritten.

The [reproduction specification](../confirmation-repro-spec.json) proposed a
read-only PVC. The supported launcher instead requires writable `/data` for its
verified provenance init and new output. This adaptation is explicit and awaits
review: wrapper commands read source paths only, verify model/config/state/cache
metadata before and after, and the unchanged cache loader hashes all four arrays
before inference; the worker rehashes those arrays afterward. Root selected bytes,
if present, must match the committed selected artifact. This is a semantic
source-reading restriction with checks, not kernel-enforced read-only access.
No global handoff change or alternate launch adapter is introduced.

The sequence is fixed: two full-validation predictions on one loaded model, one
prediction after an independent load in that process, then one prediction after a
fresh-process load. Each of the three loads uses `compile=False` and the unchanged
historical trace over the first256training rows. Each prediction uses the original
ordered124,000-row validation cache, batch4096 and metric functions. The exact
selected cost must reproduce; metric assertions retain `rtol=0, atol=1e-7`.
Metric mismatch is recorded so the declared comparisons finish. Identity, cost,
nonfinite or resource failure stops immediately. Four passes mean **not reproduced**,
not fixed, safe to resume or historical runtime reproduced.

Variable and activation-width-state fingerprints bracket tracing and prediction.
New logits remain only in the separate durable diagnostic output; they never enter
log transport. The metadata summary records byte/hash/max-absolute/label comparisons,
per-pass historical assertion verdicts and actual runtime/device settings. No TF32,
JIT, precision, batch or deterministic-kernel switch is changed from the specified
historical environment. Actual loaded-model JIT and dtype policy, TF32 API state,
installed packages, TensorFlow build, GPU/driver and memory are recorded. Historical
image digest, failing-attempt GPU/driver/transitive libraries and warmed/concurrent
training context remain unknown. The new pinned Python3.12 image is not represented
as the unknown historical image.

Proposed Job `kai-confirm1001-replay-a02s3-r1`: exactly one NVIDIA A10,4CPU/16GiB RAM,
12GiB ephemeral storage,30-minute active deadline, backoff0, token automount false,
known-node exclusions retained. One arm is justified by the single-artifact
reproducibility question; this short inference diagnostic is not a training
utilization or GPU-selection certificate. No additional GPU or retry is implied.
Output `/data/confirmation-20260923/diagnostics/replay-a02s3-20261001-r1` must not
already exist. All scientific/resume/production gates remain pending.

Eight named JSON metadata outputs use the reviewed bounded hash/identity-framed
transport pattern (8MiB/file,48MiB source,4MiB total encoded stream). No model,
optimizer, dataset or prediction array is exported in logs. The local receiver
requires the exact handoff, captured Job/owned Pod/two immutable ConfigMaps and
explicit UIDs; missing artifacts stay explicit. Any new admission difference needs
its own reviewed local compatibility handling. Durable complete/partial evidence
remains on PVC if log retention or a guard prevents complete retrieval.

Eight synthetic tests pass: three loads/four predictions, unchanged batch/tolerance,
metric-mismatch continuation, cost/nonfinite stop, source tamper/symlink/root-file
rejection, exact152member/original-archive/config preservation, forbidden training
calls and bounded metadata transport and ordinary single-Job retry policy. They use tiny synthetic arrays only; no real
model/cache or scientific metric was loaded/computed locally. Existing handoff tests
and exact immutable-record validation are recorded alongside final review inputs.
