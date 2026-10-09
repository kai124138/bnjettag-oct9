# Constructive review — STUDY v2

Date: 2026-10-01. Verdict: **ITERATE**.

Scope: `STUDY_v2.md`, the September 26 `STUDY.md`, inventory implementation,
quantization/cost conventions, and the source interfaces cited below. This is a
design review, not a model reload, numerical verification or permission to launch.
No pipeline edits, model arrays or network operations were used.

The amendment makes a useful, bounded compatibility study. In particular, D3 keeps
frozen campaign code authoritative, D4 preserves exact config identity, and gates
3/4 distinguish synthetic inference agreement from historical metric replay. The
explicit missing-data states prevent a build-only result from becoming a full PASS.
The following changes make those commitments executable without adding a physics
experiment.

## A1 — Account explicitly for learned-width validation

`docs/conventions/quantization-and-cost.md`, Required validation checks 1–3,
requires symmetric binary effective values, agreement between stored and
remeasured widths, and checkpoint metric reload within 1e-7 with TF32 off.
`STUDY_v2.md:181` mentions binary symmetry, and gates 3/4 cover reloads, but no
gate or explicit pending state covers the stored-width check. Identical graph
shapes and a finite synthetic output difference do not establish that learned
quantizer state was restored faithfully.

Add per-checkpoint applicability/status columns for binary effective-value and
stored/reloaded width checks to D6's matrix. Preserve the original convention's
test; identify its existing checker where available. If execution requires the
original NRP context, mark it PENDING with gate 4. FP32/nonbinary cases should
carry a justified NOT_APPLICABLE. This requires no new cost target, performance
claim, or training run. Full completion remains blocked until applicable checks
are satisfied.

## B1 — Exercise the compatibility interfaces, beyond parsing source

D5 and the implementation table commit to preserving portable defaults, legacy
aliases, argument handling, and opt-in tracking. Gate 1 (`STUDY_v2.md:131–133`)
requires syntax/static import checks, which can pass when an alias has the wrong
signature or a wrapper discards an explicit path. Concrete contracts include:

- `publication/code/hgq2/bnhgq2/convert.py:103`: `package_hls_project(out_dir, tar_path)`;
  its legacy alias must forward both arguments and return the same path.
- `publication/code/hgq2/run_stage.py:225`: parser/dispatch behavior, including
  `--config`, `--out-dir`, `--seed`, and `--skip-convert`.
- `publication/code/hgq2/bnhgq2/wandb_util.py:19`: missing or disabled
  `WANDB_MODE` returns false before any credential-file lookup.
- `publication/code/hgq2/bnhgq2/config.py:13`: project root derives from the
  module location, while explicit paths remain explicit.

Add bounded runtime contract checks for the interfaces actually changed or
wrapped. Stub expensive conversion/training and network dependencies; exercise
parser/dispatch and argument forwarding, import the alias, and assert disabled
tracking does not attempt credential lookup or network access. These checks
implement D5; they do not require training, HLS, external credentials, or another
scientific campaign.

## C1 — Make pT controls easy to audit in the matrix

Gate 5 already requires alignment, weighting-output, disabled-path and unweighted
validation checks. Name separate rows for absent config, `enable=false`, enabled
uncapped weights and enabled capped weights. The original integration at
`bnjettag/code/hgq2/bnhgq2/train.py:299–327` aligns labels before applying the same
permutation and takes only the training partition for weighting. Include an
intentional label mismatch to demonstrate that this guard still rejects it.
This is clarification of the accepted gate, not an additional experiment.

## Required review questions

1. Applicable conventions: accounted for except A1's missing width-check status.
2. Reference rigour: original source/config/checkpoint/preprocessing is the correct
   engineering reference. Full source and checkpoint hashes, rather than filename
   aliases, are explicitly required by D4 and gate 3. No accuracy reference table
   or seed ensemble is needed for a software-equivalence claim.
3. A competing implementation would have executable interface contract evidence;
   B1 closes that gap. It would also expose the quantizer-state check in A1.
4. Uncertainty: honest. Exact paired inputs and a fixed 1e-7 maximum difference
   address engineering equivalence; missing metric replay cannot be hidden behind
   synthetic tests or a wider interval.
5. Limitations: the inventory documents attempted coverage and concrete missing
   identities. Unknown checkpoints are not accepted as equivalent by name. Local
   preparation can proceed after design PASS while those gates remain pending.
6. Result context/pulls: no physics result is claimed. Future historical metric
   replay retains its original split/reference/tolerance requirement in gate 4.

Resolve A1 and B1 in the design, then re-review. C1 can be incorporated while
preparing the matrix. No new physics experiment or numerical threshold is requested.
