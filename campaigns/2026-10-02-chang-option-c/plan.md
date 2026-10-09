# Chang option (c) revision — plan, 2 October 2026

Owner: ml-engineer (engineering only). Governing documents:
`../2026-10-01-chang-traced-pid/AMENDMENT_DRAFT.md` (critical PASS, design only, `REVIEW_DRAFT.md`),
Kai's decision `local/2026-10-01-execution/chang-option-c-decision.json`, the original
`../2026-09-26-training-batch/STUDY.md`, and `docs/infrastructure/gpu-selection-policy.md`.
Nothing here launches, touches a running Job, or edits a prior campaign record.

## What option (c) changes, and which code is current

Current code: the historical Chang bundle `42abed4b…` (patches 0001–0031, ConfigMap payload in
`../2026-09-26-training-batch/manifests/configmap-42abed4b.json`). The earlier staged tree
`../2026-09-26-training-batch/code/staged-option-c/code` is exactly 42abed + staged patch 0032
(checked: `diff -r` differs only in `bnhgq2/ablation.py` and the new test file).

Patch 0032 (copied here byte-identical, SHA-256 `f475c69e…`) already implements the controller:

- `train.ebops.pid_input: traced_only` (regime B only, `d = 0`, warmup-1 epoch traced);
- the PID is stepped at the start of zero-based epoch `e` only if `e-1` was traced (or `e < warmup`);
  between steps, beta, integral and previous error are held and `on_epoch_end` is not called, so the
  in-training cost never reaches the controller;
- `per_epoch` integral: a step after span `D` adds `D × log10(E_traced/T)` (D−1 extra copies plus
  HGQ2's own call); spans 1 (seed, e=1), 9 (e=10), then 10;
- per-epoch log fields `pid_stepped`, `pid_step_span`, `pid_integral`.

The amendment adds, and this revision implements as patch 0033 on top of 0032:

1. **Explicit convention.** `pid_traced_integral` must be present when `pid_input` is set (no silent
   default); configs carry both keys explicitly.
2. **Routing guard.** `bnhgq2/train.py` (`ebops_callbacks`, the HGQ2-callback route) ignores the keys
   today; it must reject them before any run.
3. **Durable controller telemetry.** A small per-run `pid_telemetry.jsonl` (fsynced each epoch,
   truncated on resume like `activation_widths.jsonl`) with explicit epoch semantics: input consumed at
   the step, error, span, integral, previous error, beta after the step and at epoch end, in-training
   cost, traced cost. The b5 readout showed the full history exceeds any small export bound
   (11.8–247 MB per arm); this file stays in the hundreds of kB at epoch 500.
4. **Input guard.** On a stepped epoch at or after warmup, the PID input must equal the most recent
   trace within relative `1e-6`.
5. **Stage identity.** `BNJ_STAGE=pilot-c` with W&B group suffix `-pilot-c`.
6. **Campaign revision `campaigns/chang1002c/`.** All 58 configs regenerated from the unchanged
   `chang0926/generate.py` `build()`, with new names (`chang1002c-…`), group, campaign provenance and
   the two keys; one-to-one old/new map with hashes and an exhaustive flattened field diff.
   Cadence-adjusted canary reader (`canary_c.py`, β movement at one-based epoch 11).

## Steps

1. Build `code/tree` = fresh sha-checked extraction of 42abed + `patches/0032` + `patches/0033`
   (`build_tree.py`, reproducible; `--check` re-derives and diffs).
2. Synthetic tests runnable locally with `~/venv-hgq2/bin/python` (hgq2 0.1.9 pinned version present):
   real `BetaPID` with model hooks stubbed, no model, no training; generator/map tests; routing guard.
   The existing tiny-training pytest suite and `cpu_gate.py` go to an NRP CPU Job, not the laptop.
3. Freeze (`freeze_c.py`): deterministic tarball, ConfigMap, manifest SHA, Job JSONs for the CPU gate
   and the replacement pilot (3 A10 pods, repacked to the 90 % GPU-memory rule), then
   `tools/run_handoff.py prepare` with a brief whose scientific gate is `pending`.
4. `nrp_doctor.py lint` offline on every Job; `run_handoff.py validate` and offline `launch`.
5. `PREFLIGHT.md`: exact objects, resources, stop rules, outputs, gates still open, decisions for Kai.

## Not in scope

No GPU product selection by fiat (A10 prepared; product choice is flagged), no gain change, no
per_step switch, no new arm, no floors/pairing/fingerprint re-measurement (they need the CPU/NRP
gates listed in PREFLIGHT), no launch.
