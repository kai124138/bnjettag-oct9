---
id: 2026-09-26-code-line-merge
date: 2026-10-01
type: engineering
status: design-review-pending
amends: STUDY_v2.md
source_inventory: inventory_20261001.json
implementation: pending-design-pass
---

# Code compatibility merge: design v3

The original `STUDY.md` remains the September 26 record. This amendment describes the
files actually present on October 1. It authorizes no training or synthesis. Its
engineering checks cannot clear Chang K1, Delta production, or any numerical result.

This version resolves the v2 arbiter findings A1–A3 and B1–B3. Design PASS permits
the already authorized local implementation; historical scientific validation remains
a distinct dependency with explicit applicability and evidence. No training-code edit
has occurred. The original study and v2 remain immutable review inputs.

## Question, null, and scope

Can the GitHub-facing pipeline preserve its public interfaces while incorporating the
research tree's missing functionality and loading historical checkpoints without
changing their outputs? The null is compatibility: for a fixed config, checkpoint,
preprocessing record, input, and environment, the merged implementation returns the
same outputs within maximum absolute difference 1e-7. Any regression falsifies the
compatibility claim and prevents retirement of the corresponding old entry point.

**[D1] Destination:** the existing `publication/code/hgq2` directory in the canonical
WSL lab. The research tree is a comparison input, and becomes a retained reference
only once the applicable gates pass. Do not create a second editing checkout, delete
source records, or mutate frozen campaign bundles. The orchestrator verified the
publication code against remote `origin/main` at commit `6da5003` on October 1; existing
local changes in two publication result documents are outside this merge.

**[D2] Scientific invariants:** model graphs, quantizers, default schedules, split and
row-order algorithms, validation selection, and cap feasibility are unchanged. Optional
pT weighting retains the original implementation exactly and remains disabled when its
config block is absent or `enable` is false. No new default weighting is introduced.

## What the file inventory establishes

`python3 campaigns/2026-09-26-code-line-merge/inventory_sources.py` produces the attached
inventory using file hashes, parsed Python ASTs, JSON metadata, and checkpoint file
metadata. It imports no training packages and computes no scientific result.

| Inventory item | Observed count and scope |
| --- | --- |
| Union of included relative file paths | 175 |
| Same-path files with differing bytes | 29 |
| Different Python files with only docstring changes | 11 |
| Different Python files with AST changes beyond docstrings | 17 |
| Different JSON files with only formatting changes | 1, `configs/layer-configs-da13.json` |
| Research-only included paths | 66: 38 configs, 15 Python files, 13 other files |
| Publication-only included paths | 73: 63 configs/indexes, 10 Python files |
| Byte-identical included paths | 7 |
| Model configs requiring CPU build coverage | 100: 38 research and 62 publication |

The inventory excludes symlinks and path components `__pycache__`, `.git`, `wandb`,
`outputs`, and `slack`; it therefore excludes generated figures, analysis output tables,
runtime logs, and caches. Counts include individual nested files rather than counting a
whole directory as one difference. The original “135 paths” is a dated `diff -rq`
observation with different counting scope, not a current substantive-change count.

The 17 AST differences are not 17 independent physics changes. Most are names, paths,
imports, CLI contracts, and tracking behavior. `qat.py`, `build.py`, `data.py`,
`binarize.py`, serialization compatibility helpers, and related graph modules differ
only in documentation; `ablation.py`, `ebops_target.py`, `ebops_calc.py`, `subln.py`,
`extract.py`, and `weight_grid_audit.py` are byte-identical. These are observations about
the named source trees, not proof of equivalence to every frozen campaign bundle.

The old study's assertion that the publication pipeline itself contains Engram and the
later constituent/Chang/Delta extensions does not describe these current files.
Those campaigns use separate frozen code and patches. **[D3]** Preserve those campaign
inputs and their consumers; do not claim this merge imports or validates those
extensions. A later integration must name the exact additional source manifest and
receive its own review. Existing campaign reproducibility depends on its recorded
bundle, never on silently substituting the new default pipeline.

## Implementation contracts

Each item below is an explicit merge choice. No bulk directory replacement is permitted.

| Area | Research addition or compatibility requirement | Publication behavior to preserve |
| --- | --- | --- |
| Training | Port `bnhgq2/pt_weights.py` and the optional `train.py` integration; label alignment, train-only bins/weights, class normalization, metadata, and unweighted validation remain exact | Existing graph, checkpoint selection, callbacks, portable output paths |
| Config identities | Retain all 38 research JSON config bytes and full content hashes under their historical filenames; retain all public configs unchanged | All 62 public model configs, descriptive names, batch indexes, explicit teacher requirement |
| Config generators | Port the pT generator and dependencies without overwriting the public EBOP generators; legacy EBOP generation needs a separate namespace or explicit legacy mode | Public `gen_ebops_n8.py`, `gen_ebops_ablation.py`, pre-conference and softmax generators retain their existing outputs |
| Check scripts | Preserve historical checks through explicit config selection/legacy mode or a separately named wrapper; no research script may accidentally import the public renamed generator | Public check scripts and descriptive arm names remain usable |
| Evaluation | Port the pT evaluation/metrics scripts with only reviewed import and explicit-path adaptations; preserve split, label, score dtype, and standardization contracts | Public `evaluate_roc.py` and `estimate_auc_uncertainty.py` stay canonical |
| Conversion | Preserve historical Python imports and CLI names with small compatibility wrappers only where supported; expose `pack_for_mulder` as an alias if legacy callers require it | `convert_binary.py`, `package_hls_project`, public store layout, explicit config/checkpoint probe arguments |
| Tracking and teachers | Historical artifact references are provenance, never rewritten to fabricated new artifact names | W&B defaults disabled unless explicitly online; `--track` remains opt-in; local `--teacher-checkpoint` and versioned teacher resolution remain supported |
| Documentation and artifacts | Preserve original records in place; document canonical entry points and compatibility limitations | No copying old logs, generated plots, checkpoint binaries, or obsolete environment setup into the code merge |

**[D4] Config identity is exact.** `cfg_hash()` includes all non-private config fields,
including name, data path, and tracking project. A renamed public config can have the
same architecture while possessing a different provenance hash. The inventory lists
equal-architecture/quantizer pairs and their remaining changed field paths; it does
not declare them interchangeable checkpoints. Keep a separate alias map with both
original hashes and the precise differences. Never alter historical config or run
records to make the hashes match.

**[D5] Public defaults stay public.** Preserve publication `PROJECT_ROOT`, store/output
paths, tracking opt-in, explicit teacher and checkpoint arguments, and descriptive
entry points. Any historical path assumption must be handled by an explicit argument
or documented compatibility wrapper. Do not restore machine-specific defaults into
the canonical modules. Do not copy `preflight_final.sh` as a current installer: its
default `final-*.json` glob matches no configs here, it covers only one non-recursive
glob, and its success token says nothing about historical reload coverage. The original
`preflight_final.sh` invocation is amended explicitly: this merge uses
`campaigns/2026-09-26-code-line-merge/preflight_merge.py`, implemented after design PASS.
It performs no installation or data-source network probe. Its command accepts
`--capture originals/capture_20261001.json`, `--candidate publication/code/hgq2`,
`--inventory inventory_20261001.json`, `--environment-lock <lock-file>`,
`--phase contracts|build|reload|all`, and `--output <coverage.json>`. Paths are resolved
from the lab root or passed as absolute paths; subprocess source roots are explicit.

## Compatibility evidence and preflight gates

Two comparison arms are the immutable original source inputs and the merged pipeline.
Each receives the same exact config bytes, checkpoint, preprocessing JSON, deterministic
input probe, and dependency environment. This is a software regression design; a seed
ensemble, accuracy comparison, or training experiment is not part of the merge.

The metadata scan found 280 `.keras` files in the explicitly listed local model/result
roots. Adjacent `train_meta.json` identifies 94 distinct `(config, seed)` pairs; 74 files
lack that adjacent config identity. Duplicated download directories and different
checkpoint epochs remain separate entries. No checkpoint tensors were read, no content
identity inferred from a filename, and no reload attempted in the design phase.

Exactly 29 research config hashes have matching checkpoint metadata in this scan.
The nine research configs without an exact-name/hash match are b50, the long-budget
config, and all seven EBOP ablation configs. No public config has an exact public
name/hash checkpoint match in the scanned roots. Many public configs are renamed
counterparts of research configs; that is a mapping task, not evidence of a reload.
The inventory records missing publication cache directories explicitly. Campaign-level
artifacts not scanned here may fill gaps after their provenance is recovered.

## Captured originals and historical references

Before any destination edit, `capture_originals.py` captured the actual working files
listed in the reviewed source inventory. Archives and manifests are mode 0444; every
member was verified against the inventory. Filesystem read-only mode is a workflow
guard, not protection against an administrator changing the bytes. Every execution
must verify the hashes again. The complete record is `originals/capture_20261001.json`.

| Side | Files | Archive SHA-256 | Manifest SHA-256 |
| --- | --- | --- | --- |
| research | 102 | `228cbef0340ece68d9fab3bd23536b6e29a1e4088c93de6b30498ab817bd7e64` | `a075c10e801b8a8555c33239ce8b102f30133352fe1c6235aadc3d32f075a52f` |
| publication | 109 | `214c2d1fa174bfcec080945df7606f2592ff05bd0f630621a6fcbef4b686d07f` | `b46b687cd8ece7eacb3ecb7be47d66fac055c8e6015303c64aadc520984b47fb` |

The bundles use the inventory's documented exclusions, preserving every executable
source/config input in the declared merge scope. Baseline subprocesses load only
verified bytes from these archives, via temporary read-only directories removed after
execution. They are reference artifacts, not another active editing checkout. Set
`PYTHONDONTWRITEBYTECODE=1`; redirect outputs to disposable fixture directories.
Captured current code does not establish the source used to train an old checkpoint.

The original study requires checkpoint reload within 1e-7. The precise metric
requirement comes from `docs/conventions/quantization-and-cost.md:43-45`: checkpoint
reload agrees on the metric within 1e-7, TF32 off. These sources do not establish
that every config or every checkpoint filename has a saved validation target.

`metric_reference_inventory_20261001.json` names 204 metadata-file reference candidates
with the field `best_val_macro_auc`, the reported validation `n_val`, config and seed,
and candidate checkpoint paths. These are stored metadata references, not recomputed
results. For example, the pT baseline candidate is
`bnjettag/results/ptw-n8-20260925/checkpoints/base-s1/train_meta.json#best_val_macro_auc`.
Its split is internal validation; the exact dataset and row identities must still be
established. Pareto/front, unconstrained and delivered constrained checkpoints can
share metadata while referring to different selection records. Association must be
proved before declaring a metric reference applicable. The reference inventory also
lists unidentified checkpoints and configs lacking an exact metadata candidate.
Missing evidence does not prove that a config was never run.

**[D6] Preflight produces a coverage matrix with independent gate statuses.** Each
row names the source side, original manifest SHA-256, candidate manifest SHA-256,
full config SHA-256, checkpoint content SHA-256 when used, preprocessing SHA-256,
environment-lock SHA-256, fixture/probe SHA-256, applicability, result, and evidence.
Historical eight-character config hashes are candidate lookup keys only. Use `PASS`,
`FAIL`, `PENDING`, `MISSING`, `UNKNOWN_APPLICABILITY`, `TIMEOUT`, or justified
`NOT_APPLICABLE`; absence cannot become a pass.

1. **Source and interface gate.** Verify both captured manifests, review the file-level
   candidate diff, and exercise the explicit contract fixtures below. Preserve every
   intended public feature and all exact config identities. A mismatch in source bytes
   blocks execution until a new reviewed capture records the changed scope.
2. **CPU build gate.** Validate/build all 100 model config identities, seed 1, on the
   captured originating side and candidate with GPUs/tracking disabled. Compare
   parameter counts, tensor shapes, and normalized layer/connectivity/quantizer
   configurations. Normalization may remove only documented transient object IDs or
   generated build metadata; quantizer values and layer names must not be erased.
   Record each normalized-config hash and any discrepancy. Validate the layer override
   and batch index JSON separately; they are not model configs. Clear models between
   builds. For binary configurations, `bnhgq2.qat.effective_weight_values` must find
   exactly two nonzero symmetric effective values per applicable layer.
3. **Engineering checkpoint gate.** Establish exact checkpoint/config/preprocessing
   mappings, hash checkpoint contents, and compare captured-original versus candidate
   inference in isolated CPU subprocesses. Require finite outputs and maximum absolute
   difference <= 1e-7. Cover every available, attributable historical config/seed
   identity; preserve all unmapped paths as explicit pending rows. Deduplicate only by
   verified content hashes. Probes include zero inputs, fixed-seed nonconstant inputs,
   padded inputs with occupancy 1/half/full, positive/negative/alternating signs where
   supported, and values on either side of representative quantization boundaries
   using `nextafter`. Record generator seed 20261001, shapes, dtype, boundary values,
   occupancy and hashes. No more than 32 examples per shape/probe set are needed; this
   finite suite supports a regression claim, not universal functional equivalence.
   Exercise adapted preprocessing/evaluation entry points with the same fixtures.
4. **Checkpoint quantizer gates.** Each checkpoint has separate applicability/status
   rows for (a) binary effective-value symmetry, (b) stored versus reloaded quantizer
   state, and (c) stored widths versus remeasured widths. Use
   `bnhgq2.qat.effective_weight_values`, `bnhgq2.qat.act_grid_params`,
   `bnhgq2.ebops_target.width_snapshot`, and the existing selected-checkpoint records
   such as `train_meta.json#ebops_budget.checkpoint_widths` where available.
   `act_grid_after` is a final-training-state record and must not silently stand in
   for selected-checkpoint widths. Engineering state equality is distinct from the
   convention's remeasurement requirement. Remeasurement requires the original
   quantizer/calibration definition, selected-checkpoint identity, and calibration
   input identity; unavailable context leaves that row pending. Any trace that changes
   quantizer state runs on a separate disposable reload and cannot contaminate the
   inference gate. FP32/nonbinary non-applicability is justified separately for binary
   weights and activation widths; nonbinary weights do not imply no quantized activations.
5. **Applicable metric reload gate.** For each established historical selected
   checkpoint/reference pair, name the exact metric, reference field, original split,
   sample count, selected checkpoint and source/data provenance. Retain the 1e-7
   metric tolerance and TF32-off requirement. Synthetic inference cannot satisfy it.
   A candidate reference remains `UNKNOWN_APPLICABILITY` until association is proved;
   an applicable reference lacking inputs remains `PENDING`/`MISSING`. A config with
   no historical run has no invented metric target, but `NOT_APPLICABLE` requires
   evidence. Any scientific replay is a separately authorized NRP dependency subject
   to existing review, immutable handoff and action-time launch authorization. It is
   not a launch step implicitly authorized by this engineering design.
6. **Completion and reporting gate.** Design PASS permits the local implementation
   and its bounded engineering checks while historical dependencies are unresolved.
   The harness emits `MERGE_ENGINEERING_PASS` only if every declared local contract,
   build and available/mapped reload row passes; uncovered historical rows are listed
   alongside it. Missing a required local input emits `MERGE_ENGINEERING_INCOMPLETE`;
   observed mismatches emit `MERGE_ENGINEERING_FAIL`. It never emits the obsolete
   `PREFLIGHT_ALL_PASS`. `PREFLIGHT.md` receives critical review and states exact
   coverage. Full historical compatibility, retirement of uncovered old entry points,
   numerical-result claims and hardware readiness remain unestablished until their
   applicable gates pass. No historical dependency blocks writing a reviewable local
   implementation merely by being pending.

## Executable contract fixtures

Fixtures use fabricated data/epoch records and stub training, conversion, artifact
clients and sockets. They perform no optimizer steps, real-data metric replay, HLS
execution or credential access. Any attempted unstubbed network call fails the row.
The matrix must expose the following separate rows, including ones for unchanged
public behavior that the port could accidentally replace.

| Fixture | Required observation |
| --- | --- |
| Public CLI and dispatch | `run_stage --config --out-dir --seed --skip-convert` reaches the expected stub with exact arguments; legacy wrappers retain documented signatures and argument forwarding |
| Conversion alias | If introduced, `pack_for_mulder(out_dir, tar_path)` has the canonical signature, forwards both paths to `package_hls_project`, and returns the same path |
| Paths and imports | Derived `PROJECT_ROOT`, default store/output roots, explicit paths and environment overrides resolve as before; import public and introduced legacy entry points without invoking execution |
| Tracking | Missing/disabled `WANDB_MODE` returns false before credential lookup; `run_ablation` keeps tracking off without `--track`; online behavior uses only a fake credential/artifact client |
| Teacher/checkpoint arguments | Explicit local `model_best.keras`, wrong basename, absent local/artifact source, and versioned artifact branches preserve original dispatch/rejection; fake clients perform no network operation |
| Generators | Public generators produce unchanged config objects and historical generators reproduce the preserved historical identities; redirect generation into temporary fixture directories and compare every generated config's canonical content hash |
| Callbacks and schedules | Construct callbacks without fitting; fixed epochs around warmup/decay/restart/target boundaries yield the captured configuration and learning-rate/target decisions for the affected code paths |
| Selection | Fabricated candidate rows below/at/above the cap, an infeasible set, and tied monitor values preserve original checkpoint selection, final-target filtering and tie behavior |
| Data/evaluation | Small row-ID fixtures preserve permutation, train/validation separation, normalization, label-to-score alignment, softmax/score dtype and explicit preprocessing arguments; do not report fixture metrics as science |
| pT absent/disabled | Absent block and `enable=false` do not load jet pT or supply sample weights; training and validation fixtures match the captured unweighted path |
| pT enabled uncapped/capped | Both paths reproduce captured research weights; only training rows determine bins and class normalization; validation/selection remain unweighted |
| pT mismatch guard | Deliberately misaligned labels are rejected before weighting/fitting, preserving the original assertion and failure behavior |

The orchestrator prepared `/home/kaimoe/lab/.venvs/preflight-20261001/bin/python`
with Python 3.12.13 and the current job pins. Its lock and validation record are under
`/home/kaimoe/lab/environment-records/preflight-20261001`. Record that lock's hash in
the preflight artifact. CPU execution uses `CUDA_VISIBLE_DEVICES=-1`,
`WANDB_MODE=disabled`, `KERAS_BACKEND=tensorflow`, `OMP_NUM_THREADS=2`,
`TF_NUM_INTRAOP_THREADS=2`, `TF_NUM_INTEROP_THREADS=1`,
`TF_ENABLE_ONEDNN_OPTS=0`, and `NVIDIA_TF32_OVERRIDE=0`.

## Budget, stop conditions, and convention compliance

This phase uses file inspection only. Implementation preflight uses bounded CPU model
builds and inference; no optimizer steps, data downloads, training, HLS conversion,
cluster resources, or new W&B runs. A failing config, missing committed input,
serialization mismatch, or unexpected network attempt stops the corresponding gate
and creates an explicit remediation entry. Do not loosen tolerances to pass.

Run one worker subprocess at a time, with at most two compute threads and one
TensorFlow inter-op thread as specified above. The parent enforces a 180-second wall
time and 120-second CPU-time limit per build/reload worker, 30 seconds per interface
fixture worker, and an 8 GiB resident-memory ceiling including worker descendants.
Use a process-group RSS watchdog rather than a small virtual-address limit, which
can reject TensorFlow address reservations. The session has a 90-minute wall budget
and a 90-minute aggregate child-CPU budget. Log at most 1 MiB per row, without
array dumps. On timeout/memory/budget exhaustion, stop the worker group, retain its
partial log, mark the row `TIMEOUT` or `PENDING` with reason, and stop further launches
when the aggregate budget is exhausted. These are local engineering execution limits,
not scientific stopping rules. A continuation must record any revised limits; it
cannot conceal the incomplete first attempt.

| Convention | Treatment |
| --- | --- |
| Binary quantization and native cost | Per-checkpoint binary, state reload and stored-versus-remeasured width rows; missing remeasurement context stays pending; no new cost claim |
| Config, schedule, split and checkpoint selection | Exact config identities retained; scientific behavior unchanged |
| Checkpoint reload, TF32 off, 1e-7 | Original study output/reload gate and conventions metric gate cited separately; named applicable references retain the tolerance |
| Scientific metrics, intervals, seed ensembles | Not applicable to engineering counts; established metric-reference replay is a separately authorized NRP dependency, not assumed for every config |
| HLS fidelity and synthesis | Existing interfaces preserved; actual synthesis requires a separate selected-checkpoint handoff and mulder run |
| Figures and outward prose | No figures; outward text must pass prose lint and the existing publication review |
| Provenance and launch handoff | Original frozen runs remain immutable; no launch in this campaign phase |

## Where uncertainty remains

DECISION: preserve public defaults and port optional research behavior explicitly.
ALTERNATIVES: bulk-copy research modules, which would remove known public CLI and
tracking contracts. CONFIDENCE: HIGH. FLAG FOR HUMAN: NO.

DECISION: keep campaign-specific frozen code authoritative until a separately scoped
integration. ALTERNATIVES: claim all later campaign code has merged based on the old
study wording. CONFIDENCE: HIGH. FLAG FOR HUMAN: NO.

DECISION: implement and certify the declared local engineering coverage while reporting
applicable pending historical gates and unknown reference associations separately.
ALTERNATIVES: defer all implementation until all historical references are recovered.
CONFIDENCE: MEDIUM. FLAG FOR HUMAN: YES if a partial engineering merge is to be
presented as the final canonical migration. Partial coverage is never a full PASS.

Current verdict: v3 design re-review pending; implementation not started; scientific
results and hardware status unchanged.
