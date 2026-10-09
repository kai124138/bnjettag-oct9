---
date: 2026-10-01
status: design-only; artifact recovery and converter work pending
scope: current-candidate hardware preparation
---

# Current-candidate hardware validation plan

The preferred first article is the registered 350k A02 seed-1 selected checkpoint,
`batch20260917-a02-s1`. Its historical evaluation identifies an exact model digest and
PVC path, but the model bytes, final-generation provenance and learned channel grids
are not yet bound to a local hardware package. The present converter also has a
per-channel precision gap. **No current candidate is ready for Mulder.** This plan
records read-only source inspection; it contains no new model evaluation, synthesis,
implementation, launch or hardware result.

## Candidate and exact recovery target

A02 has N=8, three features (`pt`, `etarel`, `phirel`), d_model=32, four heads,
two layers, FFN=32, no normalization, learned position encoding and global average
pooling. Its config requests binary absmean weights and channel activation granularity.
The initial `act_bits: 8` is not its final learned precision. The registered target is
350,000 eBOPs. This is a small, already selected constrained article; it is not a
hardware-optimal selection or a seed-averaged performance claim. Do not substitute an
A11 500k model, a later confirmation seed, or the old R4 model.

The [historical evaluation result](../2026-09-23-confirmation/evaluation-results.json),
lines 8–10 and 72–76, records generation `epoch-1000`, selected epoch 912 (zero-based),
and selected-state cost 349,298 eBOPs. The evaluator reads `best_feasible` and
`model_best.keras` from that generation; it does not independently retrace this cost.
The [frozen evaluator](../2026-09-23-confirmation/evaluate_a02_a11.py), lines 25–28,
109–119 and 140–155, supplies the path association below. Its embedded ConfigMap
script was checked byte-for-byte against the local script.

| Identity | Recorded value / status |
| --- | --- |
| Selected checkpoint SHA-256 | `b2d5e8940b5132d782de20bc9aab09ec7e37d1543472e7566627b33d66ec6e45` |
| Exact historical PVC checkpoint | `/data/batch20260917/n8/runs/batch20260917-a02-s1/checkpoints/epoch-1000/model_best.keras` |
| Local selected-checkpoint path | No matching local checkpoint association established by this inspection; current PVC presence remains unobserved. |
| Historical run root, abbreviated `R` below | `/data/batch20260917/n8/runs/batch20260917-a02-s1` |
| Config byte SHA-256 | `95380e213a3c9ac8d71b2878aa74d5fb4f114500f78149415f6cc873d8836bbe` |
| Trainer config identity | `4894feab863dc2bc282866312632cda6f11db0bf3645ef012a270801c6779378` (`json.dumps(sort_keys=True)`, default separators) |
| Merge inventory config identity | `10e3b4b1b35ec09ef57face686c72bd718e30592a9ba462b8b16065da956b08e` (compact sorted JSON); same config bytes, different serialization. |
| Historical training/evaluation source archive | `ddd3761d2a566790b42a1c55c036727df624e58a6f65305c1aeca3d05365584d` |
| Epoch-100 data identity, final-generation verification pending | `2d3e895c4a538a5eea84442ab1a481822bf47dc815dd52b5943fae8842775af7` |

The config exists locally at
`publication/code/hgq2/configs/batch20260917/batch20260917-a02-s1.json` and
`campaigns/2026-09-20-continuation-packed/arch/hgq2/configs/batch20260917/batch20260917-a02-s1.json`.
Both agree with the config member in the original archive. The archive survives in
`campaigns/2026-09-17-training-batch/launch/code-configmap.json`, binaryData
`hgq2.tar.gz`; its decoded 162,924 bytes match the archive digest above. This is an
available historical source identity, not a reconstruction from the merged tree.

The [epoch-100 PVC inventory](../2026-09-20-continuation-packed/pvc-state-before.json),
lines 4842–4852, binds this run, config, data and source before continuation.
The [evaluation job](../2026-09-23-confirmation/evaluation-job-r4.yaml), lines 42–50,
also uses that exact archive. Recover final `state.json` to close the remaining
epoch-1000 provenance link; do not extrapolate the earlier metadata to the final file.

The next bounded read-only recovery should request these exact historical paths:

| Paths | Purpose and missing evidence |
| --- | --- |
| `R/checkpoints/epoch-1000/model_best.keras`, `R/checkpoints/epoch-1000/state.json` | Match the selected model digest, epoch and final source/config/data identities. No optimizer or resumability claim is needed for inference. |
| `R/COMPLETE.json`, `R/latest.json`, `R/config.json`, `R/input_std.json` | Confirm terminal/selection association and training-only standardization. The evaluator explicitly consumed these names. Record current pointer separately if it changed. |
| `R/data_info.json`, `R/initialization.json`, `R/activation_widths.jsonl` | Paths recorded in the earlier run inventory; recover if retained. Telemetry aids diagnosis but does not replace selected-model effective grids. |
| `/data/batch20260917/n8/data/x_val.npy`, `/data/batch20260917/n8/data/y_val.npy` | Historical internal-validation cache used by the evaluator. Exact file digests, split/order provenance and standardization association remain to be captured. |
| `/data/confirmation-20260923/eval-a02-a11-r4/results.json`, `/data/confirmation-20260923/eval-a02-a11-r4/batch20260917-a02-s1.npz` | Optional original evaluation evidence. Recorded prediction-file SHA-256 is `155f3105e3ea63c3083e464d857c1c1689e831e4159235afeab517478ab24a4f`. |

Capture names, sizes, byte digests, pointer contents and acquisition times into a new
receipt. Missing files, changed model bytes or conflicting final identities stop this
candidate. No recovery operation is authorized by this plan. The 17-run recovery
already completed concerned different run roots and does not supply this checkpoint.

## What the existing evidence permits

The historical evaluator used CPU inference, TF32 disabled, deterministic operations,
batch 4,096, and 124,000 internal-validation jets. It also evaluated 260,000 held-out
jets, without selecting on them. Its two reloads gave identical logits; the historical
validation-metric tolerance was `1e-6`, while repeat-logit tolerance was `1e-7`
([evaluator](../2026-09-23-confirmation/evaluate_a02_a11.py), lines 41–55, 87–138).
A02's recorded validation-AUC difference from its selected-state value is
`3.920335928109253e-7`. Do not relabel that historical test as a `1e-7` metric gate.
These are prior single-seed observations, not fresh verification of recovered bytes.

The [merge preflight](../2026-09-26-code-line-merge/PREFLIGHT.md), lines 13–24,
passed 217 bounded engineering checks without HLS or real-data scientific validation.
Its [coverage row](../2026-09-26-code-line-merge/evidence/coverage_summary_v5.json)
for A02 says `MISSING_IDENTIFIED_CHECKPOINT`, `UNKNOWN_APPLICABILITY` for historical
metrics and `PENDING_CALIBRATION_REFERENCE` for widths. Its synthetic paired reloads
cannot certify this selected checkpoint, exporter or hardware.

## Export prerequisites and implementation work

The R4 adapter cannot be used by changing a path. Its `scalar_grid` explicitly requires
homogeneous grids and its entry point asserts `r4-gradual`
([prepare_export.py](../2026-09-17-synthesis-r4-gradual/prepare_export.py), lines 41–51,
65–68). In `publication/code/hgq2/convert_binary.py`, lines 260–277 retain only the
maximum integer precision; lines 374–376 rebuild projection grids using the initial
activation width; lines 425–431 also broadcast maxima when copying attention grids.
Thus channel fidelity is unproven even if conversion completes. A02's actual selected
grid values are unknown; channel granularity alone does not prove they differ.

Before any package or access request:

1. Bind the recovered selected checkpoint to the historical source/config/data and
   reproduce its inference in a new, bounded read-only NRP job. Use the historical
   source/runtime first; compare a frozen proposed export source separately. Preserve
   historical metrics and tolerances. A backend or batching discrepancy blocks export
   certification rather than changing the selected model or widening tolerance.
2. On an inference-only copy, record every effective `(k,i,f)` tensor, shape, channel
   axis, rounding and saturation mode, including projection inputs, attention scores,
   softmax tables, context, residual paths and output. Hash this audit and the source
   model. Cost tracing/calibration must not mutate the inference reference: use another
   copy and preserve before/after grid digests. Remeasure cost with the registered
   historical convention; do not describe state cost as hardware resources.
3. Implement and review a channel-preserving adapter. Preserve each learned grid's
   indexing and fixed-point semantics; a maximum, average or uniform eight-bit grid
   changes computation. If hls4ml cannot represent the required tensor directly, design
   an equivalent channel decomposition and prove its numerical correspondence before
   proceeding. No quiet candidate substitution or width homogenization.
4. Audit all binary kernels as exactly `{-1,+1}`, zero sign count zero, and signs equal
   to the QAT effective kernel after separating the learned absmean scale. Preserve
   scales, biases and learned position folding. The converter's `beta_mode="exact"`
   still uses 16 fractional bits for constants (lines 459–466); audit its finite
   precision separately. Carry widths need channel-aware fan-in bounds, not new
   empirical clipping. Audit generated fallback types, including `fixed<24,12>`, for
   unintended truncation. Binary MAC weights do not imply zero DSP use for the full
   attention/scale circuit.
5. Fix the gate sample before evaluation: first 4,096 jets of the verified historical
   internal-validation cache, already training-standardized, float32 shape `(4096,8,3)`;
   record cache/sample hashes and index order. No held-out calibration or reselection.
   The proposed inherited R4 export acceptance is score correlation at least 0.997
   and argmax agreement at least 0.995; report maximum/mean logit difference and changed
   decisions as well. Review these tolerances before execution. This permits a bounded
   numerical realization error and is not a claim of exact QAT equivalence or full
   held-out performance. Failed gates stop, with no threshold adjustment after results.
6. Require export-to-C simulation exact equality on all 4,096 five-logit outputs,
   plus targeted fixed-point boundary checks for any new adapter behavior. Check the
   R4 ReLU zero-grid failure where applicable: signed KIF `(1,0,0)` after ReLU is zero,
   and a fusion producing `{0,0.5}` is invalid. Its historical repair must be conditioned
   on each actual channel/grid and reviewed again. Preserve separate QAT and export
   reference outputs. Repeat C simulation after every generated-source/interface edit.

Future CPU preparation belongs in a reviewed NRP handoff, with no optimizer steps,
network-dependent analysis or source-run writes. An initial proposed budget is one
CPU worker, four CPU cores, 12 GiB RAM and a 60-minute wall limit, with an explicit
stop rather than automatic extension. No such worker was run for this document.

## Toolchain and package contract

Keep three identities separate: historical model source `ddd376…`, the merge candidate
manifest `dfd1f68324dfa4f2f8eb68f8da3875d7209d89c8bb7d43848201abd260dc9de0`, and the
future adapter/export package (not yet created). Hash all consumed files, compatibility
patches, installed library sources/wheels, generated C++, headers, Tcl, constraints,
sample/reference bytes and gate reports. A Git revision alone is insufficient.

The historical archive pins TensorFlow 2.21.0, Keras 3.15.0, HGQ2 0.1.9, quantizers
1.2.2, hls4ml 1.3.0, NumPy 2.5.0, scikit-learn 1.9.0 and h5py 3.14.0. The old R4 export
used NumPy 2.4.6. The merge CPU lock is
`/home/kaimoe/lab/environment-records/preflight-20261001/requirements.lock`, digest
`d8950ec91583cfc77e98c6ed4f437eb692167ab21ef3c1b25178efd038f1fb93`.
None is a substitute for recording the future export and Linux replay environments.
Record Python/OS/compiler versions, library locks and applied patches; distinguish
requested package pins from observed installed versions.

Use a fresh source-only HLS package, top `myproject`, Vitis backend,
`xcvu13p-flga2577-2-e`, 2.5 ns, RF=1 at every layer, `Latency`, `io_parallel` and
`bit_exact=True`. Preserve generated clock uncertainty. Inspect project settings and
actual generated types rather than trusting the config alone. Inputs are standardized
features and outputs five logits; preprocessing and argmax are outside this core.

Reject archives containing absolute/traversal paths, links, AppleDouble entries,
native `.so` files or stale synthesis/RTL/report directories. The generic packager
excludes only `csynth_report.json`, so it is insufficient without this clean-package
check. Supply a full archive/member manifest, gate JSON, `csim_inputs.npy`, separate
QAT/export reference outputs and source/config/model hashes. Linux compilation must
rebuild its own library. The existing `remote_csim.py` is applicable to this N8/five-
output interface only after its hard-coded top/library conventions are verified.

## Serialized Mulder stages, after prerequisites and explicit approval

Kai's explicit permission and a UCSD-verified route through his MacBook are required.
Do not SSH from WSL, obtain Mac credentials or contact either machine for this plan.
The existing setup note is historical context, not evidence that access, installed
tools, disk space or licenses are currently available. An access request should name
the reviewed package hash, exact stages, resource bounds, stop rules and durable
outputs. Artifact recovery and the per-channel converter gate must be closed first.

The commands below describe child commands for a **new stage-selectable guarded
runner, still to be implemented and reviewed**. They are not an executable launch
recipe. `BNJET_WORKDIR`, `BNJET_PROJECT`, `BNJET_PYTHON` and `BNJET_DIAGNOSTIC_TCL`
must resolve to the verified new work directory, extracted project, pinned interpreter
and reviewed diagnostic file. Do not use the old supervisor unchanged: it continues
automatically from HLS to Vivado and hard-codes an xczu7ev OOC target.

| Stage | Concrete child command / inspection | Advance condition and bound |
| --- | --- | --- |
| 0: approved environment check | Source `/data/software/xilinx/Vitis/2023.2/settings64.sh`; inspect resolved `vitis_hls`, version, compiler/runtime, available memory/disk and active vendor processes; `sha256sum -c "$BNJET_WORKDIR/package.sha256"`. | Correct immutable package/tool identity, no competing vendor work, fresh directory and sufficient resources. No tool upgrade or installation implicitly allowed. |
| 1: Linux C build | In `BNJET_PROJECT`: `bash build_lib.sh`. | Exit zero and newly produced library; 600 seconds. |
| 2: Linux C replay | `"$BNJET_PYTHON" "$BNJET_WORKDIR/remote_csim.py" --project "$BNJET_PROJECT" --inputs "$BNJET_WORKDIR/export/csim_inputs.npy" --reference "$BNJET_WORKDIR/export/csim_reference.npy"`. | Verified hashes, 4,096 samples, exact equality and maximum difference zero; 600 seconds. |
| 3: frontend diagnostic, if needed | `vitis_hls -f "$BNJET_DIAGNOSTIC_TCL"` on a separate minimal interface fixture preserving candidate port types/dimensions/pragmas. Fixture/Tcl do not yet exist. | At most two serial 600-second probes: baseline and one reviewed isolation change. Preserve logs/IR on failure; no automatic search or full-model promotion from a fixture alone. |
| 4: one full candidate HLS attempt | In the fresh verified project: `vitis_hls -f build_prj.tcl`, with options `reset=0`, `csim=0`, `synth=1`, `cosim=0`, `validation=0`, `export=0`, `vsynth=0`, `fifo_opt=0`. | Gate 2 remains valid after all edits; exit zero, nonempty fresh `myproject_prj/solution1/syn/report/myproject_csynth.xml` and `syn/verilog` RTL; six hours maximum. |
| 5: retain and parse | `"$BNJET_PYTHON" "$BNJET_WORKDIR/parse_csynth.py" "$BNJET_PROJECT/myproject_prj/solution1/syn/report/myproject_csynth.xml"`. | Retain raw XML/rpt, logs, generated code, settings, resource telemetry and RTL hashes beside parsed JSON before any claim. Missing/unknown report fields remain pending. |

All stages run under one lock with no concurrent Vitis/Vivado jobs. Retain the stricter
R4 guard: process-group RSS at most 64 GiB, at least 80 GiB MemAvailable before start,
at least 8 GiB during execution, work directory at most 50 GiB and at least 20 GiB free
disk. Use an isolated work-local TMPDIR, four compute threads at most, and stop only
the runner's own process group on a limit breach. Capture status atomically. A failed
resource guard means stop, not retry with larger limits or interfere with another job.

The R4 failure was a Vitis 2023.2 frontend segmentation fault in
`llvm::collectPragmaObjects` / `DisaggregatePreprocess`, not an evidenced six-hour
timeout or OOM. The first attempt ended after 44.66 seconds; it also reported an
invalid TOP directive. Split interface pragmas and explicit C linkage both failed.
Do not repeat them as known fixes. Preserve compiler IR and the exact command if the
failure recurs; a minimal diagnostic may distinguish interface/pragma handling from
model complexity but does not itself establish a root cause. Work-local temporary
storage addresses the historical disk risk, not a proven compiler defect.

Vivado OOC is a separate future stage requiring a reviewed target and authorization;
it is not part of the initial HLS request. A prior VU13P license probe failed and an
xczu7ev probe succeeded; that does not establish current licensing. Any eventual
xczu7ev OOC result must remain a device-specific proxy, with its own eight-hour/four-
thread bound and clock constraint read before synthesis. No place-and-route or
bitstream is proposed. HLS estimated timing, top-level latency/II and resources must
be reported separately from OOC or routed results; RF=1 alone does not establish II=1.

## Evidence fingerprints and remaining decisions

All hashes below are SHA-256 of the local bytes inspected on 2026-10-01. They identify
evidence and existing reference implementations, not a future approved package.

| Source | SHA-256 |
| --- | --- |
| `2026-09-23-confirmation/evaluation-results.json` | `6ddeb30807092a82e8d51bcd64eecda1c46423da13b37ea5705fe7c751739334` |
| `2026-09-23-confirmation/evaluate_a02_a11.py` | `a34a522f38fa18ca77d8162822e405071529578d28a2245e9acb3407c59c46e5` |
| `2026-09-23-confirmation/evaluation-configmap-r4.json` | `d2fa92936f25f7959ad62813047e4efb9ffbcfcedad8b25702f00dbd0e6afa7f` |
| `2026-09-23-confirmation/evaluation-job-r4.yaml` | `e6f35621b5b4d60ecb67f9665e23cdab36584a3a011ca5042d787b9e255f462a` |
| `2026-09-20-continuation-packed/pvc-state-before.json` | `164c09ad120f2fd1f9204ad2b29ebd7e3cc323cb5e450379ff42e0bfbbcd9c50` |
| `2026-09-17-training-batch/launch/code-configmap.json` | `a61f41b98ae1cada0d16ac3bcc48507f5962b8667be99750f27b6b7db390e2e1` |
| `2026-09-26-code-line-merge/PREFLIGHT.md` | `f60e0ab0e6132c8cdb8afc46782f5bd66209cf9aabb3ed0f9e78fc2809b41695` |
| `2026-09-26-code-line-merge/evidence/coverage_summary_v5.json` | `70c31e68c12a072cfb5c79e8253e7dd8385508ea31b3b2991f81f59520b2d0ca` |
| `2026-09-17-synthesis-r4-gradual/README.md` | `cab09a94b6040f4fe7d43084de31ea2b68b70c01884ab4248b262deff240fc96` |
| `2026-09-17-synthesis-r4-gradual/hls-frontend-diagnostics.log` | `5e8631df27c86c94d2e30754b1f12fb1b3d63aabb53a26b72098cd56c81f844b` |
| `2026-09-17-synthesis-r4-gradual/hls-attempt1.log` | `6479276b0d94e131c20bbca04488bc45c95aff37e6d329bab9a42253feb99155` |
| `2026-09-17-synthesis-r4-gradual/prepare_export.py` | `094d3d38841ae8bde1709014b0baf993f08bc36ef2d6d5a9ebe19b70635b9ab0` |
| `2026-09-17-synthesis-r4-gradual/remote_csim.py` | `3f5ebd7e07a676003b385841ee077b15f349a579fa5d0b182e5abf47f3334c35` |
| `2026-09-17-synthesis-r4-gradual/runner/supervise_synthesis.py` | `167e851331782540fcb617c6a05d322f60a409c5559e0886093627560eb88ae0` |
| `2026-09-17-synthesis-r4-gradual/runner/run_synthesis.sh` | `965fa9b04f7ad5067b0c5107e18889002197d64ab20524df041ac7e57d90f8d8` |
| `publication/code/hgq2/convert_binary.py` | `ecf71deb284f0b880db2cb52cdf658157eb46430f63302f237f32225c80f1bd9` |
| `publication/code/hgq2/bnhgq2/convert.py` | `feb693f14b1cad073915f812a7cab43ccfd4d65327898c466c9fba91467207df` |
| `publication/code/hgq2/bnhgq2/build.py` | `847eafb77dfb2310753afe7b143036206fb6e12103795845da2bb5e2d780a5f9` |
| `publication/code/hgq2/bnhgq2/port.py` | `039ed4836e0315659bb8bb93e0f5314e31c572a9b358a9e75329392281fbaa02` |
| `publication/code/hgq2/parse_csynth.py` | `432cadf7044cc73c5c2381d3283d502a0033a54e9cd096e24900b5fba0d14bc0` |

Campaign-relative entries in this table are beneath `campaigns/`. Failure evidence is
at frontend-log lines 5–6 and 21–29, first-attempt lines 83–95 and R4 README lines
134–136. Resource limits are supervisor lines 27–35; the automatic Vivado continuation
is lines 307–312. Generic conversion/packaging semantics are `convert.py` lines 53–68
and 103–110. These references explain why the existing scripts need a bounded new
wrapper and channel audit before reuse.

Remaining work is ordered: recover and bind the exact article; implement/review
channel-preserving export; register and pass the fixed-sample gates; create and review
the stage-only runner/package; then request concrete Mulder access. The numerical
realization tolerance requires design review before use. If faithful channel export
is unavailable, choosing another article or accepting a changed model is a new
scientific decision. No such choice, K1 clearance, hardware readiness, or launch
permission follows from this plan.
