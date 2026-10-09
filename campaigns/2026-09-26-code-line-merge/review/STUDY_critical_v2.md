# Critical review — STUDY v2

Date: 2026-10-01. Verdict: **ITERATE**. Scope: engineering design only.

Reviewed `STUDY.md`, `STUDY_v2.md`, `plan.md`, the inventory and its generator,
`CLAUDE.md`, `SYSTEM.md`, phase/review methodology, relevant conventions, and the
specific source files cited below. No ML runtime, checkpoint arrays, scientific
recomputation, network, or cluster access. The expected `.claude/agents` definition
and `.claude/memory/experiment-log.md` are absent; no claims depend on their contents.
No earlier arbiter report or validator output was supplied.

## Findings

**A1 — Separate the supported metric convention from the new historical replay scope.**
`STUDY.md:21-25` requires CPU builds, saved-checkpoint reload within 1e-7, and the
preflight script; it forbids cluster launch. There is a genuine additional source:
`docs/conventions/quantization-and-cost.md:43-45` requires reload agreement **on the
metric** within 1e-7 with TF32 off. Therefore it would be wrong to remove that
convention or claim synthetic output agreement certifies it. However,
`STUDY_v2.md:147-153` calls reproducing saved validation metrics on the original split
an existing universal requirement without identifying the metric/reference for any
checkpoint. Neither cited requirement establishes that every inventoried config has
a saved validation reference requiring replay. The proposed NRP replay also differs
from the original no-launch design.

Fix: cite both actual sources and distinguish (1) the engineering output/reload gate,
(2) any applicable metric reload gate with its named reference, split and provenance,
and (3) missing historical evidence. Keep metric tolerances unchanged and pending
when applicable; do not invent reference obligations for configs without historical
runs. State explicitly that design PASS permits the authorized local implementation,
while no full historical validation or scientific-result claim follows. Describe any
NRP work as a separately authorized dependency, not an implicit launch step. Propagate
the distinction to `plan.md:52-54`, the completion gate and conventions table.

**A2 — Preserve executable original inputs before modifying the destination.**
`STUDY_v2.md:110-113` promises immutable original-versus-merged execution, but its
source gate at lines 131-133 only archives hashes. `publication/code/hgq2` is both an
original input and the edit destination. A digest cannot recover the original bytes
after an edit; a remote SHA does not capture working-tree contents.

Fix: require a content-addressed, read-only source/config bundle for each original
tree, including actual working files, before the first edit. Record bundle hashes
and load baseline subprocesses exclusively from those bundles. This is a reference
artifact, not another active editing tree. Keep the captured-original baseline
distinct from the historical training source: missing historical source provenance
still limits the historical compatibility claim.

**B1 — Name the replacement preflight and test the public contracts it promises.**
The preservation decisions at `STUDY_v2.md:83-106` are sound, but the gates at lines
131-157 specify syntax, model builds, checkpoint inference and pT fixtures. Those
checks can pass after a CLI default, generator name or output path has regressed.
For example, the public output default is in `publication/code/hgq2/run_stage.py:30-32`
and tracking opt-in in `publication/code/hgq2/bnhgq2/wandb_util.py:19-23`. The original
`bnjettag/code/hgq2/preflight_final.sh:24-33` also makes a network request, and lines
44-45 only select one non-recursive config glob; v2 correctly rejects blind reuse.

Fix: name the maintained replacement harness and explicitly amend the old script
invocation. Include bounded checks for preserved CLI/import contracts, resolved
default paths, tracking disabled by default, teacher/checkpoint argument behavior,
and generator outputs in temporary directories. Cover binary symmetry as the old
script does at lines 51-55. Define its success token from the declared coverage
matrix, with incomplete coverage reported separately rather than silently skipped.

**C1 — Make the bounded execution budget concrete.**
`STUDY_v2.md:173-177` says bounded execution but supplies no subprocess timeout or
total execution budget. Add a timeout/resource policy and record exhaustion as
incomplete. This is an engineering budget, not a new scientific stopping rule.

## Coverage and reviewer questions

The inventory supports 100 model identities, 280 checkpoint paths and 94 metadata
config/seed identities. Its 29 config-hash matches are **candidates**, not verified
checkpoint provenance: `inventory_sources.py:148-152` matches metadata fields, and
`publication/code/hgq2/bnhgq2/config.py:50-54` defines an eight-hex-character hash.
The design appropriately requires further mapping and checkpoint content hashes.
Keep full config hashes and field differences in the alias map; architecture
agreement must never relabel a historical checkpoint. Unknown/missing identities
must remain visible in the required-coverage matrix. Public-default preservation,
exact research config retention, and keeping campaign bundles authoritative are
appropriate choices; missing artifacts are not a reason to change science.

Applicable conventions are mostly addressed, with A1 and B1 unresolved. Scientific
reference tables, seed ensembles, pulls and accuracy resolving power are inapplicable
to this engineering comparison because it makes no performance claim; original-source
fixtures and the coverage matrix are its references. An independent reviewer would
ask for recoverable baseline inputs and executable interface checks (A2/B1).
Uncertainty is honestly acknowledged, but full historical replay is overgeneralized
(A1). Missing artifacts have an inventory attempt and are not treated as failures or
passes. No numerical result requires a pull in this review.

After these bounded design corrections, implementation can proceed under the existing
authorization. No scientific gate, historical validation claim or cluster launch is
cleared by this review.
