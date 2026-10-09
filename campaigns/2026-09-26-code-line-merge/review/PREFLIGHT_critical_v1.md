# Provisional critical review — PREFLIGHT v1

Date: 2026-10-01. Verdict: **ITERATE — active implementation; final PREFLIGHT not submitted**.

This is the durable ledger of findings already sent to the owner and orchestrator
during implementation. It records the initially inspected expressions and behavior;
the owner is changing the files, so it does not assert that each defect remains in
the latest working copy. Reported fixes require re-review against a finalized
`PREFLIGHT.md`, one fixed candidate/harness identity and the corresponding evidence.
This is not a final compatibility verdict.

Scope: `publication/code/hgq2` against public base `6da5003` and captured originals;
`preflight_merge.py`, `preflight_worker.py`, inventory and available engineering
metadata against `STUDY_v3.md`. Excluded the two unrelated public result-document
edits. No ML worker, checkpoint-array read or concurrent preflight was launched by
this reviewer. Config/import reproductions used plain Python only. The incomplete
test runner was not itself treated as a defect.

## Findings and resolution evidence required

**A1 — Shared reload output makes comparison tautological.**
The inspected `preflight_worker.py:model_checks` wrote both arms to
`out.parent / (item['id'] + '.npy')`. Original and candidate result files shared that
parent, so the candidate could overwrite the baseline. The parent then loaded the
same path twice before calculating the maximum absolute difference. This could
produce zero even when outputs differed.

Required fix/evidence: unique per-worker output locations, distinct-file assertions,
and verification of each result's recorded content before comparing. A negative
fixture must detect both an overwritten/shared result and a real differing result.
The owner reports these fixes and negative checks are implemented. The orchestrator
reports the first attempt was invalidated before reload comparisons; no result from
that defective comparison path may be accepted. **Pending final re-review.**

**A2 — Filename filtering omits an attributable historical identity.**
The inspected `preflight_merge.py` reload selection required basename
`model_best.keras`. Metadata-only inventory analysis found 206 mapped paths:
203 `model_best.keras` and three `model_unconstrained.keras`. All mapped paths cover
94 config/seed identities and 29 configs; the basename restriction covered only
93 identities and 28 configs, omitting `ebops-n8-20260910-b25-w1a8`, seed 1.

Required fix/evidence: include attributable alternative checkpoint filenames in the
engineering reload coverage. This does not endorse their scientific feasibility.
Every excluded, unidentified or unavailable path must retain an explicit reason;
deliberately excluded mapped paths must not be mislabeled as unknown provenance.
The owner reports alternative filenames are included. Deduplication must preserve
config/checkpoint/preprocessing identity: a selected duplicate lacking preprocessing
must not suppress another attributable copy, and differing preprocessing identities
must not be silently collapsed. **Pending final matrix verification.**

**A3 — Phase-only success uses the full engineering PASS token.**
The inspected finalization emitted `MERGE_ENGINEERING_PASS` whenever its existing
rows passed, including `--phase contracts`, with `scope_complete=false` separately.
`STUDY_v3.md` D6 reserves the engineering PASS for all declared local contract, build
and available mapped-reload requirements. A consumer reading the token alone could
mistake contracts-only success for completion.

Required fix/evidence: unmistakable phase-scoped outcomes; the full token requires
the complete expected local coverage set. Expose observable individual contract
cases, including the declared teacher, tracking, alias and import-order contracts,
instead of relying solely on a broad summary label. Historical metric/width
dependencies remain separately pending. **Pending final re-review.**

**A4 — Execution identities are recorded without all required bindings.**
The inspected runner verified archive and embedded-manifest hashes, but did not
bind `--inventory` to `capture['inventory_sha256']`; its exact-config summary
hardcoded 100 without verifying the declared identity set. Workers propagated
parent-provided config/checkpoint/preprocessing hashes without checking the actual
inputs against them at execution. The harness files were not bound to the attempt,
allowing a modified worker script to be loaded by later subprocess launches.

Required fix/evidence: verify capture/inventory association and the complete reviewed
100-config set; record and hold both harness script identities fixed throughout the
attempt; verify config, checkpoint and preprocessing bytes used by each worker.
The recorded eight-character historical config hash is only a lookup key. Current
config bytes plus metadata association must not become a claim of full historical
training-config/source provenance. The existing `mapping_scope` limitation is useful
and must remain where stronger evidence is missing.

The runner **already rehashed the candidate tree at the end**; this is acknowledged,
not a missing check. A mismatch/assertion must nevertheless finalize an invalid or
incomplete receipt, and affected gates must rerun against one final candidate and
harness identity. **Pending final re-review.**

**A5 — Reused output can be mistaken for a fresh successful worker result.**
The inspected evidence directory allowed reuse, and `run_task` loaded an existing
result file after the worker ended without requiring a successful exit. A stale
result from a previous attempt could therefore survive a failed new subprocess.

Required fix/evidence: refuse existing attempt/evidence destinations or guarantee
fresh exclusive per-attempt artifacts; fail on nonzero worker exit even if a JSON
result exists. Keep interruption/assertion/budget failures in a durable final
receipt. Timeout or missing-input coverage remains incomplete, rather than becoming
a successful comparison or an unexplained configuration mismatch. **Pending review.**

**B1 — Legacy callable alias was missing.**
The initial `convert_final.py` wrapper forwarded the public target's symbols, but
the historical callable `run_convert_final` had been renamed `run_convert_binary`
in the target. The legacy import therefore disappeared.

Required fix/evidence: preserve the callable with the canonical signature and
argument forwarding. The reviewer subsequently observed
`run_convert_final = _impl.run_convert_binary` in the wrapper. Include the historical
name explicitly in the finalized contract evidence. **Implementation observed;
execution evidence pending.**

**B2 — Public and legacy generator imports collided.**
A plain-Python reproduction preloaded public `gen_ebops_n8`, then loaded the legacy
ablation generator after inserting its directory in `sys.path`. Its absolute
`from gen_ebops_n8 import make_long_budget` still resolved through the public entry
in `sys.modules`. The historical r0 config then differed in `train.data` and
`train.wandb_project`.

Required fix/evidence: qualified/isolated legacy imports and public-first plus
legacy-first import-order tests comparing historical config contents. Clearing
`sys.modules` before each generator test would conceal this defect. The reviewer
subsequently observed qualified `configs.legacy` imports; the owner was adding
import-order coverage. **Implementation observed; final evidence pending.**

**B3 — Resource-limit outcomes need faithful evidence.**
The inspected 1 MiB log limit was polled every 0.2 seconds and could be skipped if
the worker had already exited, allowing a fast verbose worker to leave an oversized
log. Aggregate exhaustion/assertions could exit without a finalized status, and
missing worker rows could be converted to generic comparison FAIL rather than
TIMEOUT/PENDING.

Required fix/evidence: bounded log capture with a recorded limit outcome, and durable
incomplete/timeout states on exhaustion or interruption. Preserve the documented
engineering resource limits and failed attempts. These observations were already
sent to the owner; they introduce no new scientific stopping rule. **Pending review.**

## Positive evidence and advancement boundary

At the diff inspection, all **38 research and 62 publication model configs** retained
their captured bytes. `pt_weights.py` was byte-identical to research; the entire
candidate `train.py` AST matched captured research after removing docstrings.
Public `config.py`, `store.py`, `wandb_util.py`, `ablation.py`, `data.py` and `qat.py`
were unchanged. The common layer-config JSON retained its known public formatting.
These observations support the intended semantic preservation but do not substitute
for finalized executable gates.

The owner controls bounded execution. Final critical review must resolve this ledger
against the completed artifact and durable evidence. Pending historical metric or
width prerequisites remain explicit and do not authorize replay, retirement of
uncovered entry points, scientific-result claims, Chang/Delta clearance or launch.
