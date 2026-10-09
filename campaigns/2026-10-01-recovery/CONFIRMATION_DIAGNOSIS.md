# Confirmation reload diagnosis — 1 October 2026

**Static diagnosis complete; cause and resumability unproven.** Four final exported arm logs fail selected-checkpoint validation replay after committing epoch 300. The failures establish metric disagreement at the original `rtol=0, atol=1e-7` assertion. They do not establish corrupted checkpoints, an optimizer failure, or which arm caused the terminal Kubernetes Job condition.

This review inspected JSON, sanitized logs and source bytes decoded in memory from the immutable confirmation ConfigMap. No model/array was loaded, no scientific metric was recomputed, and no code, tolerance or historical artifact was changed. The [reproduction specification](confirmation-repro-spec.json) records exact identities and a proposed bounded NRP probe; it is not implemented or authorized to launch.

## Observed failures

All rows refer to the `kai-confirm-onegpu-0924-e0c0a3-r2-0.log` suffix under `captures/pvc-20261001T0555Z/confirmation-20260923/architecture/logs/`. Selected epochs are zero-based. Each retained generation's `model_best.keras` hash matches a successful epoch-280 report in the same exported log.

| Run | Selected epoch | Last assertion lines | Recorded disagreement |
| --- | ---: | --- | --- |
| `confirm0923-a02-s3-e1000` | 265 | 613–633 | AUC only; logged absolute difference `2.37121369e-7`. |
| `confirm0923-a03-s3-e1000` | 276 | 638–658 | AUC only; logged absolute difference `1.09834569e-7`. |
| `confirm0924-a07-n64-s2-e1000-5m` | 255 | 1090–1111 | AUC and accuracy; accuracy actual `0.6150161290322581`, expected `0.6152903225806452`. |
| `confirm0924-e02-n64-s2-e1000-5m` | 218 | 2859–2880 | AUC and accuracy; accuracy actual `0.6958709677419355`, expected `0.6958064516129032`. |

A02's successful report names the selected hash and metrics at lines 547–578, then fails at 300 with unchanged selected metadata. E02 has the same selected hash in successful reports at 220, 260 and 280, with replay failures at 240 and 300. Its earlier CUDA illegal-address failure has subsequent training output and is not its final recorded exception. These observations favor investigating execution-dependent replay before assuming bad artifact bytes. The failing root-level selected file was not hashed in the exception block; equivalence to the retained generation is supported by the save logic, not a contemporaneous hash of that failed read.

The saved logs concatenate retries without absolute timestamps for these final assertions. The terminal queue/pod log is absent. `status.failed=5` counts failed pod attempts, not scientific arms; the final Job-triggering arm remains unknown.

## Exact historical behavior

All source line references below are to members of archive **`26f3cc40a8f7c9ff378760c5b0d8ce046508cb4de585f9c4b80ea93653515a45`**, held in [study-configmap.json](../2026-09-22-constituent-screen/study-configmap.json). All 152 regular member hashes match its manifest, and all 22 source-file hashes recorded by the recovered runs match this archive. The current merged tree was not substituted.

- **Selection and save:** `bnhgq2/ablation.py:392–424` traces the live model on the first 256 training rows, saves a candidate, reloads it, retraces and predicts validation with batch 4096. Selection uses the reloaded candidate's metrics. Under these configs, the feasible ordering is accuracy, lower cost, AUC, earlier epoch (`:278–286`, `:421–424`); selected files are byte copies of that candidate. This already avoids a simple live-model versus serialized-model comparison.
- **Final verification:** `run_engram.py:265–277` reads the committed state, loads root `model_best.keras` (or min-cost fallback), traces the same 256 training rows, requires exact selected cost, predicts the same validation array/batch, and asserts both metrics. Reaching line 275 means its cost equality check passed. A matching total cost does not establish identical range state or logits.
- **Metric contract:** `ablation.py:290–297` uses argmax accuracy and `train.py:58–71` uses float64 softmax followed by five binary one-versus-rest AUCs and their mean. `run_engram.py:177–210` requires finite float32 cache arrays, hashes all four train/validation arrays, and checks the 496,000/124,000 split. Neither held-out data nor a new split participates. The same selected checkpoint must be replayed; do not reselect on diagnostic predictions.
- **Generation/optimizer:** `ablation.py:192–246` writes model, optimizer variables, state and selected copies into a temporary generation, then commits it and `latest.json`; two generations are retained. Restore validates canonical config/data/source hashes, restores optimizer slots by count/shape, rolls selected copies back and trims history. `:452–469` commits the epoch before returning at a chunk boundary. Consequently a failed post-chunk assertion can coexist with an epoch-300 pointer. That pointer alone certifies neither metric replay nor optimizer restoration.
- **Queue consequence:** the ConfigMap's `pack_runner_one_gpu.py:97–101,120–121` treats a nonzero child exit as failure even if the target epoch committed, waits for the other children, then exits 1. A later pod attempt reads the higher committed epoch and can advance despite an earlier verification failure. The queue's epoch count is not a scientific checkpoint-validity gate.

The recorded source-and-version digest is `345a057a64c55075282910bdbedbb3c8a1761fe74ebc2c5a8bf12e5ebbb3e3c0`, distinct from the archive hash. It pins TensorFlow 2.21.0, Keras 3.15.0, HGQ2 0.1.9, quantizers 1.2.2, NumPy 2.5.0 and scikit-learn 1.9.0. The saved Job requests `NVIDIA_TF32_OVERRIDE=0`; configs say TF32 disabled. Training compilation explicitly sets `jit_compile=False`, but the final freshly loaded prediction model has no explicit JIT assignment in this path. Actual prediction JIT/dtype policy, runtime TF32 observation, deterministic-op setting and CUDA/driver versions were not captured here. The inspected source does not enable op determinism.

The launch observation records an A10 at `2026-09-24T21:41:31Z`, not the GPU of every subsequent retry. The image is the mutable tag `python:3.12`; its historical digest is unavailable. These limitations prevent claiming a fully reconstructed failing runtime from the source hash alone.

## Causes versus hypotheses

**Established:** post-commit selected-metric replay fails; cost comparison passes; the retained selections previously passed; both small AUC-only and larger accuracy disagreements occur. The known code/config/cache metadata identities agree. No source evidence supports changing the validation split, batch, metric function or tolerance. A `1e-6` allowance used by a different historical A02/A11 evaluator is not this contract and would not cover the N64 accuracy failures.

**Leading hypothesis:** inference/runtime context affects predictions across the freshly loaded models or processes. **Other unresolved hypotheses:** tracing changes quantizer state in ways not detected by total cost; a serialization/state association defect; a different retry's GPU/library context. A specific kernel, TF32, Engram memory, optimizer corruption or data corruption is not established. Failure in both plain-backbone N8/A07 and Engram E02 means an Engram-only explanation is insufficient. Replaying model bytes cannot test optimizer continuation.

## Smallest proposed probe

Use **A02-s3**, the smaller N8 case with a prior passing identical retained artifact. Its selected model is `…/architecture/runs/confirm0923-a02-s3-e1000/checkpoints/epoch-0300/model_best.keras`, hash `21bfcd4faac5bceb8f609945ecfe17f975998560f312d7622fb27daf9ba3bf19`; expected selected cost is 306826 and expected metrics are the unchanged state at lines 4233–4237. Exact config, data, array, source and state identities are in the JSON specification.

On one A10 with the PVC read-only, verify identities and package versions before inference. Compare the root selected-file hash with the committed generation if available. Use the exact historical loader, tracer and metric functions through a separately frozen diagnostic wrapper; never call `train`, `run_training`, `restore_checkpoint` or the queue because those paths write state or can train. No optimizer restoration is needed.

The bounded sequence is four full-validation predictions: two on one loaded object, one on an independent reload in that process, then one fresh-process reload. Each new load gets exactly the original trace before prediction. Record logits and variable/quantizer-state fingerprints around trace/predict, the unchanged assertion verdict and execution settings. No kernel, precision, batch or determinism switch is changed in this first probe.

Identity/cost/nonfinite/resource failures stop immediately; metric mismatch is captured so the predeclared comparisons can finish. Proposed ceiling: one attempt, 30 minutes, no retry or continuation, outputs in a new diagnostic location. A repeatable discrepancy narrows the cause; four passes mean “not reproduced,” not “fixed.” Trained-process history and three-process concurrency remain outside this minimal probe. Any follow-up needs its own reviewed scope. No result authorizes resume or clears a scientific gate.

## Source byte identities

The JSON specification includes full hashes for all four logs, selected artifacts, states/configs/data records and runtime sources. Checkpoint hashes are from verified transport receipts; their model contents were not opened here.

| Archive member or saved source | SHA-256 |
| --- | --- |
| `run_engram.py` | `1d6d64832d7d880aac59826590de7b48ba2cd4bfd4772fc81a2f2c8d594587a2` |
| `bnhgq2/ablation.py` | `059ec886dd293f3f3305aa43b4b9e4ccc516ec77298457c445d7f6de32f0bb48` |
| `bnhgq2/ebops_calc.py` | `57b48827b4ced02c8c5db927e8cbfaf20310c0797ce8d461c16c669f56d0703e` |
| `bnhgq2/train.py` | `154657bb3bb6afa232d78830313583e1c5f74f955084a882dc0da4d90b231118` |
| ConfigMap member `pack_runner_one_gpu.py` | `8617f5a315c47297e6174ea4c9903080bd1253903143fde62c8c8192fc34159b` |
| [Saved Job](../2026-09-23-confirmation/one-gpu-job.json) | `1f93d25a744709b526e2a493028f53a2f421f80fc877e151115078974fb0bb1e` |
