# R4 gradual-EBOP model: HLS and Vivado synthesis — 2026-09-17

Status: **stopped; manual handoff requested.** Local and Linux C simulation passed on 4,096 jets, but three HLS attempts failed in the Vitis frontend. No RTL or Vivado synthesis result exists. See [manual commands](../MANUAL_RUNBOOK_TRAINING_AND_R4_SYNTHESIS.md).

This study synthesizes the original trained R4 model. It is **not a frozen-backbone recovery experiment** and does not replace its classifier or retrain weights.

## Intent and operating point

Determine the actual logic, DSP, memory, throughput and pre-route timing of `ebops-n8-20260912-ablation-r4-gradual-w1a8-s1`. EBOPs are a training cost proxy, not a LUT or latency measurement. RF=1 is chosen to test the whole-jet II=1 objective; that II must be read from the top-level report.

| Item | Value |
|---|---|
| Training | 1,000 epochs completed; best feasible validation-AUC checkpoint |
| Selected epoch | 959 (zero-based) |
| Native checkpoint EBOPs | 349,550, remeasured |
| Checkpoint SHA256 | `212c0cf2e41727b5b65548517887b2afedb7806fbc7b38da39422c1c991d72e6` |
| Architecture | N=8, input features pt/etarel/phirel, d_model=32, heads=4, layers=2, FFN=64, five outputs |
| Weights | Binary signs with each layer's learned absmean scale |
| Activations | Learned per-tensor widths; initial A8 does not describe final widths |
| Normalization / position / pooling | No normalization; learned positional table; global average pooling |
| HLS | Vitis HLS 2023.2; xcvu13p-flga2577-2-e; 2.5 ns; RF=1; Latency; io_parallel |
| Vivado | 2023.2 OOC; xczu7ev-ffvc1156-2-e; 2.5 ns; four threads |
| Input contract | Already standardized using the training-only input_std.json; preprocessing is outside the synthesized core |
| Output contract | Five logits; output argmax/classification interface is outside the synthesized core |

A tiny VU13P synthesis probe failed with `Common 17-345`: no Synthesis/device license. The xczu7ev probe passed. Therefore Vivado results are **xczu7ev proxy results**, not VU13P implementation, fit, or routed timing. HLS continues to target VU13P without that license. XDC is read before synth_design, then opt_design runs, with reports at both stages. HLS uses its generated 27% clock uncertainty; OOC uses the historical clock-only XDC (no additional explicit uncertainty).

```mermaid
flowchart LR
 A[Selected R4 checkpoint] --> B[Preserve learned activation grids]
 B --> C[QAT versus export gate]
 C --> D[Local C simulation: 4096 jets]
 D --> E[Linux C simulation on Mulder]
 E --> F[Vitis HLS: VU13P, RF1]
 F --> G[Vivado OOC: xczu7ev proxy]
 G --> H[Post-synth and post-opt reports]
```

## Method 1 — preserve the learned activation grids

The legacy exporter read only integer precision and rebuilt each projection at eight bits. That would synthesize a different model. The adapter copies each effective `(k,i,f)` directly from the trained quantizer, checks homogeneous grids, and verifies the copy. Signed KIF has total width `k+i+f`; negative integer or fractional counts remain valid fixed-point scaling choices.

```python
for destination, value in zip((q._k, q._i, q._f), source_quantizer.kif):
    destination.assign(np.broadcast_to(np.asarray(value), destination.shape))
```

All 15 actual binary kernel signs match the checkpoint. Small float32/float64 scale differences are recorded in `export/verification.json`. Attention and softmax grids use the existing portable full-KIF copying path. All source attention grids are per-tensor in this configuration.

| Projection input | Trained and exported k, i, f | Total bits |
|---|---|---|
| input_proj | 1, 2, 4 | 7 |
| bit_block_0_attn_Wq | 1, 0, 0 | 1 |
| bit_block_0_attn_Wk | 1, 0, 0 | 1 |
| bit_block_0_attn_Wv | 1, 0, 1 | 2 |
| bit_block_0_attn_Wo | 1, -1, 2 | 2 |
| bit_block_0_ffn_fc1 | 1, 0, 1 | 2 |
| bit_block_0_ffn_fc2 | 1, 0, 1 | 2 |
| bit_block_1_attn_Wq | 1, 0, 0 | 1 |
| bit_block_1_attn_Wk | 1, 0, 0 | 1 |
| bit_block_1_attn_Wv | 1, 0, 0 | 1 |
| bit_block_1_attn_Wo | 1, 0, 0 | 1 |
| bit_block_1_ffn_fc1 | 1, 0, 0 | 1 |
| bit_block_1_ffn_fc2 | 1, 0, 0 | 1 |
| head_fc1 | 1, 0, 3 | 4 |
| head_fc2 | 1, 1, 4 | 6 |

## Method 2 — retain scale and bias, with explicit approximation

The binary contraction uses pure ±1 weights, followed by the learned layer scale and bias. The legacy `exact` beta mode stores scale and bias with 16 fractional bits, so its name does **not** mean exact reproduction of float32 QAT. The input projection folds the positional table into its bias. This is tested against the checkpoint before synthesis.

Affine input carry grids use the source fractional precision and a conservative analytic sum bound: `fanin * 2**i`, plus folded input bias where present. This avoids the older blanket seven-fractional-bit bottleneck. Q/K/V fan-in counts only the contracted model dimension, not the output head axis.

## Method 3 — repair a zero-valued quantizer fusion

A block-1 FFN quantizer learned signed KIF(1,0,0), whose representable values are {−1,0}. Its input is ReLU, so `Q(ReLU(x)) = 0` for every input. In hls4ml 1.3.0, `FuseFixedPointQuantizer` forces a zero-width unsigned grid to width one without adjusting integer width. This changes its values to {0,0.5} and introduces a spurious nonzero branch.

Layer tracing located the first substantive mismatch at `bit_block_1_ffn_fc2`: the reference contraction was zero, but C simulation produced 0 or 0.5. A guarded post-parse repair restores the signed saturating cast at the ReLU output:

```python
# Only when the original successor grid is exactly KIF(1,0,0).
p.width, p.integer, p.signed = 1, 1, True
p.rounding_mode = RoundingMode.RND_CONV
p.saturation_mode = SaturationMode.SAT
```

This preserves the trained computation. It does not train, prune by heuristic, or alter the learned weights. Synthesis may subsequently remove logic whose output is provably constant. A standalone C++ regression passed all 20 boundary cases and reproduced the broken 0.5 output in seven cases.

## Verification and limits

| Check | Result |
|---|---|
| Original checkpoint → export, 4,096 internal-validation jets | Score correlation 0.999982880; argmax agreement 99.951172% (2 changed decisions) |
| Export → local C simulation, 4,096 jets | Bit-exact; maximum and mean difference 0 |
| ReLU zero-grid C++ regression | 20/20 passed |
| Native checkpoint cost | Exactly 349,550 EBOPs |
| Linux C simulation | Passed: 4,096 jets, maximum difference 0, exact equality |
| Hardware resources / II / timing | Unavailable: HLS compiler failed before RTL generation |

The original-to-export gate requires score correlation >=0.997 and argmax agreement >=0.995. Export-to-C simulation requires exact equality. These tests establish sample-based fidelity, not a proof for every possible input; the zero-grid repair itself follows the quantizer's range algebra. Reported agreement is not full held-out tagging accuracy, and export effects on the full held-out AUC have not been evaluated here.

Tool/library versions: `{"hgq2": "0.1.9", "hls4ml": "1.3.0", "keras": "3.15.0", "numpy": "2.4.6", "quantizers": "1.2.2", "tensorflow": "2.21.0"}`. Local NumPy differs from the training runtime; the Linux replay checks the compiled C model independently of TensorFlow.

## Execution and resource limits

The detached supervisor runs Linux compilation/replay, HLS, and OOC serially. It checks for other vendor-tool work before starting, uses a lock, and bounds memory, wall time and output disk growth. It signals only its own subprocess groups. Temporary files are in the isolated home work directory because Mulder's system filesystem is full. Training GPU jobs are not used for synthesis. There is no automatic place-and-route or bitstream generation.

Sources and exact limits are in `runner/`; status is machine-readable and stage-labeled. Archive hash: `4aac36b59641a12ee2abc4f271ff06949dae099406daf5b19696ee0e7f085e93`. Preserve raw `.rpt`, `.xml`, logs, constraints and verification JSON beside any parsed results.

## Files and reproduction

- `prepare_export.py`: learned-grid adapter, source-kernel audit, fidelity gates and zero-grid repair.
- `source/`: immutable selected checkpoint, config, state, standardization and fixed validation sample.
- `export/verification.json`, `learned_grids.json`: numerical and precision audit.
- `export/hls_prj_rf1.tar.gz`: gated HLS project.
- `remote_csim.py`: fresh Linux compilation replay against all 4,096 reference outputs.
- `tests/zero_grid_regression.cpp`: boundary regression.
- `trace-before-zero-grid-fix.json` and failed verification: retained failure evidence.
- `runner/`: bounded remote synthesis chain.

The export adapter imports the existing pipeline from `publication/code/hgq2`; it does not mutate the legacy converter or any training checkpoint. Reproduction command:

```bash
KERAS_BACKEND=tensorflow WANDB_MODE=disabled CUDA_VISIBLE_DEVICES=-1 \
OMP_NUM_THREADS=2 TF_NUM_INTRAOP_THREADS=2 TF_NUM_INTEROP_THREADS=1 \
PYTHONPATH=publication/code/hgq2 research/.venv-hgq2/bin/python \
  local/synthesis-r4-gradual-20260917/prepare_export.py --csim
```

Primary reference: [hls4ml model-wise precision propagation](https://fastmachinelearning.org/hls4ml/advanced/precision.html), which explains bit-exact propagation and its floating-point limits. Installed source, generated code, and measured replay results are the implementation evidence for this experiment.

Launch packaging note: the first supervisor attempt rejected a macOS AppleDouble archive entry before any compilation or synthesis. Repacked with Python tarfile, omitted native libraries, updated the hash, and retained failed-attempt evidence. The accepted source archive is the one hashed above.

## Final handoff status

The last supervisor (PID3197707) exited failed at18:05:56UTC, so no process needed termination when execution was handed back to the user. Splitting the interface port pragma and explicit C linkage were diagnostic attempts; neither fixed the Vitis frontend failure. Local `prepare_export.py` reproduces the numerical export; the two additional pragma/linkage edits are in the current generated project and its archive/verification metadata, not automatically applied by that script. Original archive and failed projects remain on Mulder under attempts/. No new job was submitted after the handoff request.
