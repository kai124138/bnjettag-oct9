# PREFLIGHT — Chang option (c) revision and replacement pilot (2 October 2026)

**Status: build half only, prepared offline, nothing submitted.** No `kubectl apply|create`, no
running Job touched, no prior campaign record edited. The scientific gate in every handoff brief
is `pending`, so `run_handoff.py launch --submit` refuses all five records as written. Local tests
are synthetic engineering checks; no number here is quotable. Review (critical-reviewer, then
arbiter) has not run.

Governing documents: [amendment draft](../2026-10-01-chang-traced-pid/AMENDMENT_DRAFT.md) and its
[design PASS](../2026-10-01-chang-traced-pid/REVIEW_DRAFT.md); Kai's decision
`local/2026-10-01-execution/chang-option-c-decision.json`; the original
[STUDY](../2026-09-26-training-batch/STUDY.md); the [GPU policy](../../docs/infrastructure/gpu-selection-policy.md);
the diagnostic, unreviewed [b5 VERIFY](../2026-10-01-recovery/readout-preparation/VERIFY.md). Plan: [plan.md](plan.md).

## 1. What changed in the code

Base: historical bundle `42abed4b…` (patches 0001–0031), re-extracted from
`../2026-09-26-training-batch/manifests/configmap-42abed4b.json`. Then:

- `patches/0032-option-c-pid-traced-only.patch`: byte copy of the staged patch (SHA-256
  `f475c69e…`, as cited by the amendment). It adds `train.ebops.pid_input: traced_only`: the PID
  steps at the start of zero-based epoch `e` only after a traced epoch `e−1`, holds beta, integral
  and previous error otherwise, never reads the in-training cost, and with `per_epoch` adds
  `span × log10(E_traced/T)` to the integral. Spans are 1 (seed, `e=1`), 9 (`e=10`), then 10.
  Gains, bounds, warmup and damping are unchanged.
- `patches/0033-option-c-amendment.patch` (SHA-256 `23536dfe…`), this revision:
  - `pid_traced_integral` must be explicit when `pid_input` is set (no silent default).
  - Input guard: a stepped epoch at or after warmup must consume the most recent trace within
    relative `1e-6`, else the run stops on an assertion.
  - Durable `pid_telemetry.jsonl` per run: fsynced each epoch, truncated to committed epochs on
    resume, and copied into each `snapshots/epoch-EEEE/`. It holds explicit begin/end epoch
    semantics (input consumed, error, span, integral, previous error, beta after the step and at
    epoch end, in-training and traced cost). It also carries monitoring fields that are never
    controller inputs: loss, validation accuracy/AUC, budget/feasible/non-degenerate flags,
    per-block Q/K/V 0-bit channel counts, and attention cost split into softmax and non-softmax.
    Historical runs without the key write no such file.
  - Routing guard: `bnhgq2/train.py` (`train()` entry and `ebops_callbacks`) refuses both keys.
  - W&B stage `pilot-c` (group suffix `-pilot-c`).
  - `campaigns/chang1002c/`: all 58 configs, regenerated from the unchanged `chang0926/generate.py`
    `build()`. The generator first rebuilds every chang0926 config byte-identical to the file on
    disk. The only scientific additions are the two keys; identity/provenance changes are `name`,
    `experiment.arm`, `experiment.group`, `campaign.study`, `campaign.revision_of` and
    `campaign.amendment`. `config_map.json` holds the one-to-one old/new map with both hashes and
    an exhaustive flattened diff per config. Floors, cache spec and production packs are copied
    unchanged. Also `monitor_c.py` (canary, controller audit, at-target report) and a `cpu_gate.py`
    copy with option-(c) cadence assertions.
- `build_tree.py` re-derives `code/tree` from the payload plus both patches: `TREE_MATCHES`.
  Historical checkpoints cannot resume these runs because the config SHA differs (staged test
  `test_slot_p_run_cannot_resume_as_option_c`) and the code SHA differs.

## 2. Tests

| check | where | result |
| --- | --- | --- |
| `tests/test_option_c_amendment.py`, 15 tests, real hgq2 0.1.9 `BetaPID` with model hooks replaced by a scalar plant, no model, no training | laptop, `~/venv-hgq2/bin/python -m unittest` | 15/15 OK ([log](evidence/unittest_option_c.log)) |
| covered: step schedule and spans; seeding leaves beta at 1e-7; held epochs freeze state; inputs equal traces, never in-training; per_epoch integral and HGQ2 beta formula; resume at an untraced epoch 25 replays exactly; input guard; explicit key; telemetry truncation; attention summary; routing guard (both functions and `train()`); pilot-c stage; 58-config map/hash/index identity with the historical rows; pilot packs; the monitor's canary/audit and fault injection | | |
| run_study manifest SHA over the tree with the pinned versions | laptop | `7ab48738…`, equal to the freeze computation |
| full pytest suite (the staged tree recorded 100 passed, 2 skipped; plus the amended 0032 tests and a new run_training telemetry/resume test), `cpu_gate.py` on 58 configs (build, one step, reload, floors re-traced, trace cadence, option-(c) schedule), A/B/D/R–F pairing at seeds 1–8 | **not run**; prepared as the CPU gate Job below | pending |

## 3. What would be launched

Bundle `6919462cf050c5dca664baec694f36081f05d8c4075a0d299b28af8ce4eb9da3` (243,904 bytes, 326
files), ConfigMap `kai-chang1002c-code-6919462cf0`, manifest SHA
`7ab48738fc4d916ad2b8398b1d35a6076413013d8af33b9a69afcd941a60544f`. Image
`python@sha256:4d1caded…` (digest receipt `local/2026-10-01-execution/python-readout-image.json`).
Data: existing cache `/data/chang-n64-20260926/n64/data` (558,000/62,000, 2 GeV gate), identity
from the exported `data_info.json`. Fingerprint ConfigMap `kai-chang0926-fp-e9511d1aeb` is reused
(expect `initial_ebops 11559681` for A-s1); the handoff tool does not create it, so its presence
must be confirmed at launch. Hashes: [PREPARED.json](PREPARED.json).

| order | Job | handoff | shape | arms | output |
| --- | --- | --- | --- | --- | --- |
| 1 | `kai-chang1002c-cpugate-691946` | `handoffs/rh-c1240347631f771a2c30e37d` | CPU 8 / 24 GiB, 12 GiB ephemeral, 0 GPU, 4 h deadline, backoff 0 | all 58 configs | `/data/chang-n64-20260926/option-c-20261002/cpu-gate-691946-r1` |
| 2 | `kai-chang1002c-pilotc1-691946` | `handoffs/rh-bab8196fef09fc61f0d0ebfe` | 1 × NVIDIA-A10, 8 CPU, 32 GiB, 24 GiB ephemeral | A-s1, A-s2, D-s1, E1-s1 | `/data/chang-n64-20260926/pilot-c-20261002/runs/<name>` |
| 2 | `kai-chang1002c-pilotc2-691946` | `handoffs/rh-116f7a74b05138e8868da52b` | 1 × A10, 4 CPU, 16 GiB | A07-350-s1, C-s1 | same root |
| 2 | `kai-chang1002c-pilotc3-691946` | `handoffs/rh-d69b333e85e8706272f18a61` | 1 × A10, 4 CPU, 16 GiB | F-s1, C′-s1 | same root |
| 3 | `kai-chang1002c-readoutc-691946` | `handoffs/rh-caef4f8962a5f02a8603a62c` | CPU 8 / 24 GiB, 4 h | all eight | `…/pilot-c-20261002/readout-epoch-0500-691946-r1` |

The pilot Jobs keep the pilot-b shape: Indexed with one completion, `backoffLimitPerIndex` 2,
DisruptionTarget ignored, epoch-0 all-diverged fails the Job, no active deadline (STUDY Resume).
They also keep the A10 fingerprint gate before any arm, `run_pack.py <pack> 500`, the RSS
projection gate (8,192 MiB, process epochs 5–105), W&B online in `BNJetTag-ChangRecipe`, group
`chang-n64-20261002-c-pilot-c`, the known-bad-node exclusions and token automount off. Added:
`GPU_SAMPLE` lines every 60 s and `MONITOR` lines from `monitor_c.py` every 30 minutes (both
notify-only), then a `FINAL` report per arm.

**Packing.** The eight registered pilot arms are unchanged; only the pods differ. On an A10 the
historical K=5 pod peaked at 22,540 / 23,028 MiB (97.9 %) and the K=3 pod at 21,249 MiB (92.3 %)
(training-batch RUN.md, "GPU memory per process"). Both exceed the policy's 90 % limit. Per-process
peaks there are about 4,350 MiB for E-class arms, 8,446 MiB for A07 WRAP arms and 5,110 MiB for C′.
The predicted pod peaks are therefore 17,400 MiB (75.6 %), 16,892 MiB (73.4 %) and 9,456 MiB (41.1 %).
The first two equal the benchmark's measured A10 shapes, E K=4 (75.7 %) and A07 K=2 (73.4 %).
The eight arms total about 43,750 MiB against 2 × 20,725 MiB usable at 90 %, so three A10 pods is the minimum.

**Expected duration (arithmetic, not a measurement).** At the benchmark's A10 rates
(`2026-09-29-gpu-benchmark/VERIFY.md`: E K=4 114.10 s/epoch, A07 K=2 96.56 s/epoch), 500 epochs
take about 15.8 h for pod 1 and 13.4 h for pod 2. Pod 3 has an unmeasured mix; the slowest
historical pilot-b arm (138.5 s/epoch) bounds it at about 19 h. The cadence-adjusted canary
(one-based epoch 11) arrives about 20–25 minutes after arms start.

**Launch commands (only after section 5 is settled).** Re-prepare the record with the gate
cleared, which yields a new `rh-` ID, then submit through the supported launcher. It runs
`nrp_doctor lint`, checks object identity and uses `create`:

```sh
python3 campaigns/2026-10-02-chang-option-c/freeze_c.py --only cpugate \
  --gate-cleared '<reviewed gate record>' --approval-ref '<exact dated Kai authorization>'
python3 tools/run_handoff.py launch campaigns/2026-10-02-chang-option-c/handoffs/rh-<NEW_ID> \
  --submit --approval-ref '<exact dated Kai authorization>'
```

Repeat for `pilotc1,pilotc2,pilotc3` after the CPU gate passes, and for `readoutc` after all three
pilot pods pause at epoch 500 or record a terminal marker.

## 4. Stop rules and expected outputs

Registered guards in the frozen bundle (`existing-runner-guard`): divergence or non-finite metrics
(arm-isolated by `run_pack`), the RSS projection gate (exit 5, not retried), the GPU fingerprint
mismatch (no arm starts), epoch-0 all-diverged (Job fails), the new PID-input assertion, and the
pause at epoch 500. Notify-only, for the operator and Kai; the monitor never kills:

- `CANARY_LOSS`, `CANARY_TRACE`, `CANARY_PID_E11` FAIL. These are the STUDY canary with the
  amendment's cadence change: at one-based epoch 11 the arm must show a step with span 9 on the
  epoch-10 trace and a beta change matching the HGQ2 formula. A FAIL, or `CONTROLLER_AUDIT FAIL`,
  means stop advancement and stop the pod at a checkpoint only with Kai.
- `NOTIFY_DEGENERATE_UNDER_BUDGET` (budget met while accuracy is at or below the registered
  threshold, or the cost is not above the 0-bit floor), `NOTIFY_ATTENTION_QK_ZERO_BIT`
  (jet-independent logits under WRAP; under SAT the `bits` field counts the sign bit, so C′ cannot
  read 0 here), `NOTIFY_BETA_AT_BOUND`, and GPU memory above 90 %.

Expected outputs per arm: `activation_widths.jsonl`, `pid_telemetry.jsonl`, checkpoints every 25
epochs, `snapshots/epoch-0500/` (with frozen telemetry), W&B run `pilot-c` keyed. The readout
writes `certify-snapshot-0500.json` (registered 1e-6), `a26-entropy-epoch-0500.json` (entropy
and Q/K/V widths, validation n = 62,000) and `controller-<run>.json` per arm. Each
`controller-<run>.json` holds the canary, the full input/hold audit, and at-target counts:
budget met, feasible, degenerate-under-budget, Q/K all-0-bit epochs, beta at bound, and the last
traced accuracy, threshold and attention state. A missing arm makes the readout exit nonzero.

## 5. Open before any launch

1. **Launch authorization.** None is recorded for the CPU gate, the pilot or the readout. The design
   PASS supplies none, and K1 and production stay blocked.
2. **The b5 readout says the pilot's main risk is not the PID input.** Its VERIFY (diagnostic,
   unreviewed) finds every 350k head exactly uniform from about epoch 40. A-s1 met the budget as a
   near-constant classifier, E1 stalled at 356,745 against 350,000, and C′ never reached 5M. It
   estimates the regime-B mixed-cost offset at 1.5–5.7 % of headroom and says this cannot explain
   those failures. Option (c) removes that offset and nothing else. The prepared pilot therefore
   tracks accuracy, degeneracy and attention width every epoch and reads entropy at epoch 500, but
   only as notify-only reports, because no registered rule stops on them. Kai should decide whether
   to run this pilot as the test of (c) alone, or first adopt a pre-registered stop/readout
   criterion on degenerate-under-budget and attention collapse. That criterion must be written
   before any pilot outcome exists.
3. **GPU product.** A10 is prepared because the per-process memory, fingerprint and certification
   for these exact arms were measured on it, it matches the historical pilot-b product for the
   regime comparison, and no new product canary is needed. The benchmark's leader at two or more
   GPUs is the RTX 4090 (E K=4 55.41 s/epoch, A07 K=2 48.29 s/epoch, about 2× faster). It would
   first need the 110-epoch product canary from `SCIENTIFIC_GATES.md`. The same three-pod packing
   fits its 24 GiB. Kai's choice of product is still pending.
4. **Prerequisites the amendment lists and this build does not supply.** These are an independent
   review of b5 VERIFY, including the open C′ "silent channel" inconsistency; the matched regime-A/B
   table (needs a read-only W&B pull); the CPU gate result; and fingerprint, floor and certification
   checks on the selected product. A review of this PREFLIGHT is also needed (critical-reviewer,
   arbiter).
5. **Lint.** `offline_lint.py` runs the unchanged `nrp_doctor.py lint` on the five final handoff
   `job.json` files. It replays the GPU product-to-resource map from the 2026-09-29T07:39:45Z node
   survey through a stub `kubectl` that answers nothing else. Result: exit 0, all five OK, notes
   only (A10 pool 35 nodes in that snapshot; rule PACK 4/2/2 arms). Log:
   [lint-offline.log](lint-offline.log), receipt [lint-offline.json](lint-offline.json). All five
   records pass `run_handoff.py validate` and offline `launch` ([log](handoff-validate.log)). The
   launcher repeats a live lint at submission.

## Files

`plan.md`, `build_tree.py`, `freeze_c.py`, `offline_lint.py`, `patches/`, `code/tree/`,
`manifests/` (tarball, ConfigMap, Jobs, briefs, bundle manifest), `handoffs/rh-*`, `PREPARED.json`,
`evidence/unittest_option_c.log`, `lint-offline.{log,json}`, `handoff-validate.log`.
