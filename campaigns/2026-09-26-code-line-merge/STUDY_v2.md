---
id: 2026-09-26-code-line-merge
date: 2026-10-01
type: engineering
status: design-review-pending
amends: STUDY.md
source_inventory: inventory_20261001.json
implementation: pending-design-pass
---

# Code compatibility merge: dated design amendment

The original `STUDY.md` remains the September 26 record. This amendment describes the
files actually present on October 1. It authorizes no training or synthesis. Its
engineering checks cannot clear Chang K1, Delta production, or any numerical result.

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
glob, and its success token says nothing about historical reload coverage.

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

**[D6] All gates are required and recorded per input, not as one inferred PASS.**

1. **Source gate:** archive original hashes and review a file-level diff before editing.
   Confirm the merged tree retains every intended public feature and the exact config
   identities; syntax/static import checks must pass for all new wrappers.
2. **CPU build gate:** validate and build all 100 model config identities in the pinned
   environment, seed 1, with TensorFlow GPU visibility disabled and W&B disabled.
   Record config SHA-256, originating side, parameter counts, graph shape, and failures.
   `layer-configs-da13.json` and `batch20260918/index.json` are separately validated
   non-model JSON; trying to build them as models is a harness error. Clear models
   between builds. Compare original versus merged counts and shapes.
3. **Engineering checkpoint gate:** establish exact checkpoint/config/preprocessing
   mappings, hash each selected checkpoint at execution, and run original versus
   merged inference in isolated CPU subprocesses with TF32 off. Use deterministic
   synthetic probes covering each input shape; record only aggregate differences and
   hashes, not arrays in logs. Require finite outputs and maximum absolute difference
   <= 1e-7. Cover all available historical config/seed identities, not one convenient
   checkpoint. Duplicate paths may be deduplicated only by verified content hash.
4. **Historical metric gate:** the existing requirement to reproduce saved validation
   metrics within 1e-7 on the original split remains binding. Synthetic inference is
   only an engineering gate and cannot certify that requirement. Replay occurs only
   in the approved pinned NRP execution context with exact data/split identity; it is
   outside the no-science local task. Missing checkpoints, labels, references, or
   source bundles remain `MISSING`/`PENDING`, never PASS. A config with no historical
   run may be `NOT_APPLICABLE` only with evidence that no checkpoint was expected.
5. **Optional pT path gate:** verify original-versus-merged train-only row alignment,
   weighting output, disabled-path behavior, and unweighted validation via bounded
   synthetic fixtures without optimizer steps. No metric gain is claimed. A future
   real-data smoke must follow the existing campaign schedule and launch safeguards.
6. **Completion gate:** critical review of `PREFLIGHT.md` with its machine-readable
   matrix; resolve every mismatch before marking the merge fully validated. Do not
   turn a successful static/build gate into a `PREFLIGHT_ALL_PASS` claim while any
   required checkpoint or historical metric gate is pending.

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

| Convention | Treatment |
| --- | --- |
| Binary quantization and native cost | Preserve graph/quantizer code; check binary symmetry where applicable; no new cost number is computed |
| Config, schedule, split and checkpoint selection | Exact config identities retained; scientific behavior unchanged |
| Checkpoint reload, TF32 off, 1e-7 | Engineering and historical-metric gates recorded separately as stated above |
| Scientific metrics, intervals, seed ensembles | Not applicable to static inventory/build counts; scientific replay remains pending NRP work |
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

DECISION: certify the locally available engineering coverage and report missing
historical gates without claiming full merge completion. ALTERNATIVES: recover every
missing checkpoint/data reference before making any compatibility claim.
CONFIDENCE: MEDIUM. FLAG FOR HUMAN: YES if a partial engineering merge is to be
presented as the final canonical migration. Partial coverage is never a full PASS.

Current verdict: design review pending; implementation not started; scientific
results and hardware status unchanged.
