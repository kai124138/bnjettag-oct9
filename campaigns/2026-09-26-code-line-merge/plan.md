# Code-line merge plan — 2026-10-01

Status: v3 design passed; compatibility implementation complete; final v5 engineering
checks and final critical review passed; historical/scientific/hardware gates
remain explicit dependencies.

This work preserves the original 2026-09-26 `STUDY.md` and records a dated design
amendment. The canonical lab is `/home/kaimoe/lab/bnjettag`. The two source trees named
in that study are the only pipeline trees inspected. No training, scientific metric
recomputation, checkpoint-array inspection, synthesis, or cluster mutation is planned
for the inventory phase.

1. Inventory regular source/config files in both named trees. Record relative paths,
   content hashes, added/deleted/differing status, Python AST equivalence where valid,
   and config identities. Exclude caches, runtime logs, and generated plot/data outputs
   from substantive-source counts; state exclusions explicitly.
2. Inspect substantive changes and classify research features to port, publication
   features to preserve, aliases, and incompatible defaults/serialization contracts.
3. Inventory checkpoint paths, file sizes, and associated metadata only. Do not load
   arrays or infer that a checkpoint exists from an old reference.
4. Write versioned study amendments and `inventory_20261001.json`, with explicit CPU
   build, engineering reload, applicable historical metric and unknown-evidence states.
   Hand off for design review; preserve previously reviewed versions.
5. Only after design PASS, implement the reviewed merge in the existing GitHub-facing
   tree and write `PREFLIGHT.md`. Preserve frozen campaign code/configs and original
   checkpoint identities. Require CPU config builds and original-versus-merged
   checkpoint inference agreement at maximum absolute difference <= 1e-7, TF32 off.

No figures are required. Counts in the inventory describe files, not physics results.

## Decisions and uncertainties

DECISION: preserve the original dated study and add a versioned amendment.
ALTERNATIVES: overwrite the original study and lose the historical diff context.
CONFIDENCE: HIGH. FLAG FOR HUMAN: NO.

DECISION: target `publication/code/hgq2` only after review, as the original study states.
ALTERNATIVES: choose another canonical code path, which requires updating campaign
consumers and repository ownership consistently.
CONFIDENCE: MEDIUM. FLAG FOR HUMAN: YES, if the existing destination is unavailable
or disagrees with the actual maintained remote repository.

## Attempts and outcomes

- Read `AGENTS.md`, `CLAUDE.md`, `SYSTEM.md`, the original study, and phase methodology.
- The lab root has no Git metadata. A root `git status` failed with “not a git
  repository”; no Git state or lineage has been inferred from that failure.
- `.claude/agents` definitions were not found in the supplied tree; the phase-owner
  protocol in `docs/methodology/03-phases.md` is used directly.
- Generated `inventory_20261001.json` with the reproducible, metadata-only
  `inventory_sources.py`: 175 included paths; 17 common Python files with AST changes
  beyond docstrings; 100 model config identities; 280 checkpoint paths and 94 metadata
  config/seed identities; exact checkpoint-hash metadata matches for 29 research
  configs. These are file/config counts, not physics results.
- Wrote `STUDY_v2.md`: public paths and tracking contracts retained; optional pT
  functionality ported only after review; exact historical configs retained.
  The v2 critical/arbiter review found its historical metric scope overgeneralized:
  the convention requires 1e-7 metric reload, but does not establish a saved target
  for every config or checkpoint. This is corrected in v3, without deleting v2.
- Orchestrator verified publication code against remote `6da5003`; its two pre-existing
  result-document modifications remain outside scope. The pinned CPU environment is
  available, but no ML imports or builds have been executed by this design phase.
- AST comparison including docstrings initially labelled every common Python change
  substantive; removing only docstrings resolved eleven as documentation-only.
  The inventory reports both comparisons so the original count is not hidden.

## v3 remediation and execution handoff

- Read the physics, critical, constructive and arbiter v2 reviews; arbiter verdict
  ITERATE. No pipeline implementation or ML execution occurred during remediation.
- A1 RESOLVED in design: cite `quantization-and-cost.md:43-45`; identify 204
  metadata-reference candidates in `metric_reference_inventory_20261001.json`;
  actual selected-checkpoint association, dataset identity and historical source
  remain pending. No reference is invented for unrun/unknown configs. Design PASS
  permits local engineering implementation; applicable metric replay is a separately
  authorized dependency with the unchanged tolerance, not an implicit NRP launch.
- A2 RESOLVED: `capture_originals.py` produced read-only content-addressed archives
  of 102 research and 109 publication files, preserving actual working bytes. Every
  member hash was checked against the reviewed inventory; full manifest/archive
  hashes are in `originals/capture_20261001.json`. Baselines will load only those
  verified captures into disposable read-only subprocess inputs.
- A3 RESOLVED in design: separate per-checkpoint binary-value, stored/reloaded
  state, and stored-versus-remeasured-width rows. Missing selected-width/calibration
  references remain pending; equality of reloaded state is not remeasurement.
- B findings RESOLVED in design: name `preflight_merge.py`, amend the old shell
  invocation, and specify runtime CLI/import/path/alias/tracking/teacher/generator,
  callback/schedule/selection, data/evaluation and five distinct pT control fixtures.
  State nonconstant/zero/padding/sign/boundary probes and normalized graph checks.
- Execution limits: one worker, two compute threads, 180-second wall/120-second CPU
  limits for build/reload, 30-second contract-worker timeout, 8 GiB process-group RSS,
  and 90-minute aggregate wall/CPU budgets. Limits and exhaustion are recorded in
  the matrix; no scientific stopping rule changes.
- Pending: panel/arbiter v3 re-review, then implementation and `PREFLIGHT.md`.
  Full historical compatibility and retirement of uncovered entry points remain
  uncertified; no Chang/Delta, launch, performance or hardware gate is cleared.

## Implementation begun after v3 PASS

- `review/STUDY_arbiter_v3.md` permits bounded local implementation. All three
  independent panel reviews PASS. Preserve captured baselines and existing unrelated
  publication documents.
- First port: optional pT module/integration, exact historical configs, namespaced
  legacy generators/checks, supported legacy command aliases, and pT evaluation
  entry points with explicit portable paths. No training or science execution.
- Then implement `preflight_merge.py` with bounded source/contract/build/reload workers
  and coverage evidence. Scientific-reference/remeasured-width states stay separate.

### Review-driven implementation corrections

- Restored the legacy `run_convert_final` callable alias and qualified historical
  generator imports; public-first and legacy-first generation are explicit fixtures.
- Stopped the first full attempt before reload certification: shared prediction
  output paths could overwrite baseline arrays. Namespaced outputs, distinct-path
  and file-hash assertions, and regression/overwrite negative fixtures now guard it.
- Preserved attempts v1/v2 as invalidated/incomplete receipts. No reload result from
  those attempts is used. Initial contracts_v1 is superseded; its observed row
  results remain, but it is not a full engineering PASS.
- Added capture/inventory binding, per-use config/checkpoint/preprocessing hash
  checks, script immutability checks, output-directory reuse rejection, nonzero-exit
  failure handling, phase-only success tokens, memory/time/log limits and content
  deduplication that includes preprocessing identity. Mapped unconstrained checkpoint
  files are covered as engineering inputs, without implying scientific feasibility.
- Strengthened semantic fixtures: active pT cap, delivered-checkpoint budget filter,
  target-schedule boundaries, distinct teacher train/validation arrays and load paths,
  explicit pT evaluator paths/preprocessing/label-score-pT wiring. All metrics in the
  entrypoint fixture are stubs and no optimizer step executes.
- Added `publication/code/hgq2/COMPATIBILITY.md` before final candidate capture.

## Final bounded execution

- Final immutable attempt `evidence/preflight_v5.json`: 217/217 rows PASS, comprising
  21 contracts, 100 original/candidate config builds and 96 original/candidate
  checkpoint comparisons. Maximum synthetic output difference 0.0, tolerance 1e-7.
  No optimizer step, scientific metric calculation or HLS execution occurred.
- The 96 content/preprocessing identities cover 206 mapped paths and 94 config/seed
  names across 29 research configs. All 74 unmapped paths and nine missing research
  plus 62 missing exact public config checkpoint identities remain visible in
  `evidence/coverage_summary_v5.json`. Architecture aliases do not clear these gaps.
- `config_identity_map_20261001.json` implements D4 with 68 architecture/quantizer
  pairs, both normalized config and exact-file hashes, and all differing field paths.
- Added a separate static validation receipt for preserved layer-override and batch
  index JSON. Candidate/controller/worker bytes were not modified after final-run
  static closure. Five non-ML controller regression tests passed independently.
- Wrote `PREFLIGHT.md` and evidence index; await final critical verdict before the
  orchestrator publishes the reviewable change. Historical metric/width replay,
  campaign integration, entrypoint retirement and current-candidate hardware validation
  are not certified by this engineering PASS.
- Final critical review clarified an accounting limitation: 90-minute aggregate
  controller budgets reset per invocation. Cross-attempt cumulative child CPU was
  not recorded, so session-wide budget compliance is not certified. This disclosure
  does not alter the frozen comparison inputs or results.
- `review/PREFLIGHT_critical_v2.md` returns PASS for bounded local engineering
  compatibility only. Final report and evidence index now link that review; the
  controller, worker, candidate and terminal receipt remain unchanged.
