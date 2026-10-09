# Conditional memory for BNJetTag: research and executable experiment

**18 September 2026. Status: experimental training implementation. No measured jet-accuracy improvement or FPGA result.**

The objective is **higher categorical accuracy at a constrained computational cost**, followed by reducing cost while retaining accuracy. The useful Engram hypothesis here is that a small learned memory can recover capacity removed from a transformer. Simply adding a memory to the existing model cannot, by itself, reduce its arithmetic.

This document accompanies [the runner](../code/hgq2/run_engram.py), [the memory layer](../code/hgq2/bnhgq2/engram.py), [eight configurations](../code/hgq2/configs/engram/index.json), and [correctness checks](../code/hgq2/check_engram.py). The implementation is an **Engram-inspired physics adaptation**, not a reproduction of DeepSeek's model. Its deployment parameters include multi-bit memory tables in addition to binary backbone projections.

## 1. Research findings that affect the experiment

### DeepSeek Engram: what transfers and what does not

Engram hashes compressed token n-grams into learned embeddings, then gates retrieved information using the current hidden state. It supplements attention; it does not require an attention KV cache. In the paper's Figure 5 experiment, a 12-layer MoE trained on 100B tokens has validation loss 1.808; the reference with 1.6B memory parameters reaches 1.768. The best single insertion is layer 2 (1.770). These are **language-model losses**, not jet accuracies. Removing the short convolution has a smaller effect than removing contextual gating. Table 5 gives memory embeddings a 5× learning-rate multiplier and zero weight decay. Table 4's host-memory throughput experiment uses an H800 with 512 sequences, so it does not establish the feasibility of off-chip memory in our trigger. [Paper, §§2, 6.2, 6.4 and Appendix A](https://arxiv.org/html/2601.07372v1).

**Design inference:** test a small memory after the first attention residual, keep a gate ablation, and test memory-specific optimization. There is no basis for transferring the paper's parameter allocation optimum directly to our small binary transformer.

### The official implementation is a demonstration, not a complete training stack

The official `engram_demo_v1.py` uses PyTorch, a tokenizer compression map, deterministic multi-head addresses, embeddings, projected keys/values, and a short depthwise convolution. Its attention and MoE are mocked. It performs address construction through NumPy and constructs tensors on the CPU; a direct copy does not provide our TensorFlow GPU integration. The demo also applies a signed square root before its gate sigmoid, whereas the displayed paper equation uses a normalized dot product directly. That difference must be specified in any reproduction. [Official source](https://raw.githubusercontent.com/deepseek-ai/Engram/main/engram_demo_v1.py).

**Design inference:** implement only the mechanism we can test within the existing Keras/HGQ2 stack. Do not import an external tokenizer, unverified pretrained table, or the mocked transformer. Our gate is explicitly different and quantized; the reference demo is not being advertised as reproduced.

### HGQ-LUT is particularly relevant to our actual objective

HGQ-LUT describes trainable LUT-Dense and LUT-Conv operations, heterogeneous quantization, a LUT resource surrogate, and a da4ml implementation path. Its particle-level jet study includes a three-feature configuration, but uses 32 particles and a 2 GeV particle threshold; this differs from our current 16-constituent input contract. It uses classification accuracy. Its hardware table is therefore not a direct substitute for our baseline. [HGQ-LUT, §§III–V, especially V-D](https://arxiv.org/html/2604.22293v1).

The installed **hgq2 0.1.9** contains `hgq.layers.table.QDenseT`. Local source inspection found that it trains per-input/output nonlinear mappings with sub-networks, reduces their outputs by summation, and supplies its own `_compute_ebops` formula. That is a different memory mechanism from this module's direct address/gather. The availability of the training layer alone does not verify our hls4ml/Vitis export route.

**Recommendation:** compare a separate, properly exported HGQ-LUT experiment if direct conditional memory is promising or if its table bandwidth becomes limiting. For an FPGA accuracy/resource objective, that comparison is more relevant than copying a larger language-model memory.

### LogicNets and PolyLUT explain why fewer multiplies is insufficient

LogicNets jointly designs low-precision, sparse networks and circuits around limited fan-in; its implementation includes a jet-substructure example. The important lesson is that a small arithmetic count does not imply a small truth table. Address width and connectivity are hardware design variables. [LogicNets paper](https://arxiv.org/abs/2004.03021), [authors' implementation](https://github.com/Xilinx/logicnets).

PolyLUT uses multivariate polynomials during training and maps the resulting quantized functions to lookup-based inference. The internal training representation and deployed hardware operations can differ substantially. [PolyLUT paper](https://arxiv.org/abs/2309.02334), [authors' implementation](https://github.com/MartaAndronic/PolyLUT).

**Design inference:** report logical bits, read demand, and a replication scenario separately from arithmetic. Do not count a table lookup as a free improvement over a multiplication-heavy model.

### Jet structure matters more than linguistic analogy

Particle Transformer incorporates pairwise particle interactions as attention biases. Its reported improvements concern its own datasets and architecture, but it provides physical motivation for interaction features. [Particle Transformer](https://arxiv.org/abs/2202.03772).

**Design inference:** constituent-rank neighbors are not necessarily spatial neighbors. Start with each particle's joint `pt/etarel/phirel` bins; use rank bigrams as an explicitly order-dependent control. A future pairwise-memory experiment should test selected physical neighbors or a pairwise attention bias, including feature construction and neighbor-selection costs. It should not inherit a sequence-language assumption without testing it.

### Conversion support must be demonstrated separately

hls4ml documents frontend-dependent layer coverage, special HGQ2 operators, and an extension API for custom layers. Generic Keras operations are not automatically supported. [Keras frontend](https://fastmachinelearning.org/hls4ml/frontend/keras.html), [extension API](https://fastmachinelearning.org/hls4ml/advanced/extension.html).

Our address/gather/gate module has **no HLS lowering yet**. The binary export path explicitly rejects it, preventing an accidental export that omits the learned memory. A future converter must preserve input quantization, boundaries, masking, table values, gate rounding, and accumulation behavior.

## 2. Findings from our code

The working September implementation is in `publication/code/hgq2`. The older `research` symlink differs: it lacks the newer positional-encoding switch and several matched-initialization checks. This experiment uses the September code directly and records the SHA-256 of the runner and all `bnhgq2` Python sources, plus dependency versions. It does not modify that older research checkout or copy the pipeline into a new directory.

Relevant code paths are:

| Code | Consequence for this study |
|---|---|
| `bnhgq2/qat.py:build_qat_model` | Full-jet attention computes fresh Q/K/V; no autoregressive KV cache. |
| `bnhgq2/ablation.py:matching_initialization` | Backbone kernels and calibrated grids are preserved before adding memory. |
| `bnhgq2/ablation.py:make_epoch_step` | Existing data order, training objective and activation-width optimization are reused. |
| `bnhgq2/ebops_calc.py:compute_ebops` | Uses HGQ2 tracing; ordinary custom Keras layers would otherwise be absent from the total. |
| `bnhgq2/ablation.py:save_checkpoint/restore_checkpoint` | Preserves model, Adam variables, PID state and committed epoch history. |
| `code/launch/prepare_batch_cache.py` | Supplies train-only normalization, immutable arrays, and input/label hashes. |
| `convert_binary.py:build_export` | Existing exporter reconstructs a backbone graph; it must reject unsupported memory. |

The current campaign uses five classes, three input features, and a 350,000 native-EBOP target. **Native HGQ2 EBOPs are already a proxy, not measured LUTs or latency.** Adding our custom estimate changes the total's convention, so the runner reports both components explicitly.

## 3. Implemented module

### Input keys

The network continues to receive the shared standardized inputs. Inside the memory module:

1. Quantize the three features to signed 16-bit fixed point with six magnitude integer bits and nine fractional bits, saturating with round-to-even.
2. Exclude padding using the quantized standardized value corresponding to physical `pt=0`.
3. Fit seven quantile boundaries per feature for eight bins, using only the first 4,096 rows of the already shuffled training split. Freeze and serialize them.
4. Form a joint code `64 * pt_bin + 8 * eta_bin + phi_bin`.

With eight bins and a 512-row table this is an exact nine-bit tuple address. There are **no hash collisions** in this primary arm, although discretization intentionally merges continuous inputs. The 64-row variant uses four bins per feature and an exact six-bit tuple address.

The encoder records duplicate bin thresholds and how many positive-pt constituents its quantization merges with padding on its fitting sample. This limitation is part of the experiment. It does not alter the backbone inputs. Clipped tails and bin-boundary sensitivity should be checked before promoting a finalist.

For rank n-grams, the implementation combines earlier constituent codes **within the same jet** and hashes them. Boundary positions and windows containing padding are masked. The engine supports `[2]` and `[2,3]`; the default screen uses `[2]` because the conservative address-cost estimate for `[2,3]` already exhausts the default budget when combined with the rest of the module. More hashing is not assumed to be beneficial.

### Values and context gate

The memory stores a learned value vector with the backbone width. Gated variants also store a key vector. Both are trained directly in that space: there is no online dense key/value projection. This changes the parameterization relative to the language-model design; it is not claimed to be equivalent to its low-rank projected embeddings.

The implemented equations are:

```text
v = quantize(mean_of_masked_table_values, value_bits)
k = quantize(mean_of_masked_table_keys, key_bits)
q = quantize(current_hidden_state, query_bits)
g = quantize_unsigned(clip(0.5 + sum(q * k) / (4 * D), 0, 1), gate_bits)
output = hidden_state + quantize(g * v, value_bits)
```

Ungated variants use `output = hidden_state + v`. The division is a power-of-two scale for supported dimensions. All rounding and saturation are in the training forward path using straight-through gradient surrogates. The dot product accumulates in TensorFlow float32 during this research implementation; the resource ledger reserves a fixed-width accumulation estimate. Final bit-exact hardware accumulation still needs an explicit lowering and verification.

Memory is inserted after `bit_block_0_add_attn`, giving the gate access to the first attention result before the first FFN. The short convolution, RMS normalization, multi-branch architecture, tokenizer normalization, and pretrained language tables are omitted deliberately. Their benefit on jets has not been established.

Values start at zero, so **adding memory initially leaves the backbone output exactly unchanged**. Keys start with bounded random values. Value gradients are available immediately; key learning starts once the value path becomes nonzero. Quantized tables are multi-bit parameters: this is a binary-backbone/multi-bit-memory model, not an all-binary model.

### Optimization and checkpointing

The whole backbone and memory train jointly. `MemoryAdam` applies a real 5× learning-rate multiplier to table updates and excludes tables from weight decay. Backbone Adam updates and the original learning-rate schedule remain intact. Scaling gradients alone would not implement this multiplier correctly under Adam, so the multiplier is applied at the optimizer update step. The multiplier is configurable and is a starting hypothesis, not a tuned optimum for jets.

Each checkpoint must satisfy both memory caps and the augmented arithmetic target. Selection is lexicographic: **validation accuracy, lower augmented cost, validation macro-AUC, earlier epoch**. Existing non-Engram experiments retain their previous ordering. An infeasible run remains visible and retains a minimum-cost checkpoint; it is not described as budget-feasible.

The PID sees the fixed module estimate together with dynamic backbone EBOPs. The constant memory estimate contributes no width gradient; the backbone's existing differentiable resource objective must make room for it. This is why larger memory can force worse backbone quantization even if its table storage is inexpensive.

## 4. Resource contract

`engram_result.json` separates:

- `native_hgq2_backbone_ebops`: the native trace excluding the new custom layer.
- `custom_estimated_bitops`: the new, explicitly approximate structural arithmetic estimate.
- `selection_cost`: their sum, used for this study's selection/PID.
- Logical table storage, vector reads per jet, bits read per jet, and a replication scenario.

The estimate charges `b1*b2` for a product, accumulator width for an addition, input width for a comparison, and a conservative `64*64` bit-operation allowance per hashed word. These are **design assumptions**, not calibrated equivalences to the HGQ2 cost model. Hash cost is especially sensitive to the eventual constant-multiply/modulo implementation. The ledger explicitly lists unpriced quantizer, mask, control, wiring and physical memory-layout operations.

For `N=16`, `D=32`, the default gated 512-row 8-bit key/value tables contain **32 KiB** of logical data. They need 16 independently addressed key/value vector reads per jet. If key and value are packed together and a replicated ROM supplies two arbitrary reads per cycle, an illustrative whole-jet II=1 implementation uses eight copies: **256 KiB before block sizing and routing overhead**. This is a replication scenario, not a resource guarantee. Banking without replication cannot generally guarantee conflict-free arbitrary addresses.

The default caps are 64 KiB logical and 512 KiB under that replication scenario. The runner rejects an oversized module before training. All terms are inspectable in `cost_contract.json`; no measured hardware claim is derived from them.

## 5. Experiment matrix and promotion

All default arms use 16 constituents, `D=32`, FFN width 32, four attention heads, identical split/order seeds, a full 1,000-epoch schedule, and a 350k **augmented** selection target. E00 is the existing two-block configuration under the same study protocol. E01 is its one-block control. The module itself preserves constituent permutation equivariance in tuple mode; **the full backbone is not claimed permutation invariant**, since its positional table and position-dependent input biases remain present.

| Arm | Blocks | Memory | Main comparison |
|---|---:|---|---|
| E00 | 2 | None | Existing-capacity reference |
| E01 | 1 | None | Accuracy lost/gained by removing a block |
| E02 | 1 | Exact 512-row tuples, ungated, 8-bit values | Cheap conditional capacity |
| E03 | 1 | Same tuples, context gate, 8-bit key/value | Does the gated package earn its extra cost? |
| E04 | 2 | Same module as E03 | Memory with two blocks under the shared proxy budget |
| E05 | 1 | Same as E03, 4-bit key/value | Precision versus storage/arithmetic |
| E06 | 1 | Exact 64-row tuples, four bins/feature | Smaller memory and coarser discretization |
| E07 | 1 | Hashed rank bigrams, 257 rows, gate | Does constituent order add useful information? |

The authorized private pilot runs only E00–E03, seed 1, at cumulative epoch 100, serially with a 24-hour whole-job deadline. Read the prospective [hypotheses, audit, interpretation plan and abstract](ENGRAM_HYPOTHESES_AND_ABSTRACT.md) before interpreting results. E03 versus E02 changes capacity, scaling, rounding and cost allocation together; it does not isolate dynamic gating. E04 also reallocates precision under the shared budget and is not a pure added-capacity control. E05/E06 are possible later precision/storage comparisons; E07 is a lower-priority order-dependent mechanism test. A 100-epoch pause preserves the full 1,000-epoch schedule and leaves roughly 90% of the starting learning rate.

For a future promotion decision, prioritize accuracy among feasible checkpoints. Compare E03 against **both** E01 and E00 on identical validation jets and training prefixes. A recovery relative to E01 alone does not prove an advantage over the original model. Possible follow-ups include longer matched training, seeds 2 and 3, static-gate controls and lower cost targets. These require a separate decision; the pilot does not automatically launch them.

The runner saves validation logits and supports a paired, class-stratified bootstrap accuracy difference. Its intervals reflect finite validation-sample uncertainty conditional on the selected checkpoints. They do not account for repeated architecture search or seed variability. Use validation to select finalists and a separately held-out test set for final evaluation. This runner never loads the test split.

The resource summary reports a Pareto set within matching input hashes, labels, seed and training prefix. Read the memory dimensions too: an arithmetic Pareto point can still be unattractive in physical hardware.

## 6. Commands

Use the project's pinned training environment (`requirements-training.txt`). The checked local interpreter is `research/.venv-hgq2/bin/python` resolved through the existing symlink; in the GPU job, use its installed Python. Run the commands below from `publication/code/hgq2` with that environment activated.

```bash
# Show commands without importing TensorFlow or starting work.
python run_engram.py --help

# Existing seed-1 configurations are already in configs/engram/.
# Generate confirmation seeds into a fresh directory when needed.
python run_engram.py plan --seeds 2 3 --out /work/engram-configs-confirm

# Small synthetic correctness checks, permitted on CPU.
python run_engram.py preflight --out /tmp/engram-preflight

# On a GPU: adapt /work/n16/data to the existing September shared cache.
# This must contain READY.json, data_info.json, and four hashed .npy arrays.
python run_engram.py train --config configs/engram/engram-e00-s1.json \
  --data-cache /work/n16/data --out /work/engram/e00-s1 --stop-after 100
python run_engram.py train --config configs/engram/engram-e01-s1.json \
  --data-cache /work/n16/data --out /work/engram/e01-s1 --stop-after 100
python run_engram.py train --config configs/engram/engram-e02-s1.json \
  --data-cache /work/n16/data --out /work/engram/e02-s1 --stop-after 100
python run_engram.py train --config configs/engram/engram-e03-s1.json \
  --data-cache /work/n16/data --out /work/engram/e03-s1 --stop-after 100

# Resume the same run at a later cumulative epoch, preserving Adam/PID state.
python run_engram.py train --config configs/engram/engram-e03-s1.json \
  --data-cache /work/n16/data --out /work/engram/e03-s1 --stop-after 200

# Summarize only after equivalent prefixes are available for comparisons.
python run_engram.py summarize --root /work/engram --out /work/engram/summary.json
python run_engram.py compare --baseline /work/engram/e00-s1 \
  --candidate /work/engram/e03-s1 --out /work/engram/e03-vs-e00.json
```

For the authorized pilot, add `--track` and explicitly set `WANDB_MODE=online`, `WANDB_ENTITY=kayamaguchi-uc-san-diego`, and `WANDB_PROJECT=BNJetTag-Engram-Experimental`. The operator must first create and verify this separate PRIVATE project. The runner refuses an absent/nonprivate project or an environment override that redirects tracking. Epochs include memory/gate diagnostics, and the same W&B run receives final review artifacts after checkpoint evaluation. No message, cluster job, or hardware synthesis is submitted by this runner. Omitting `--stop-after` runs/resumes to the configured final epoch. A new seed, source/dependency change or config change needs its own output directory.

Do **not** launch these configs with `run_ablation.py` or the generic batch runner: the new entrypoint provides the memory builder and rejects incorrect cache identities. The underlying training function rejects a memory config without that builder. The production runner requires the canonical 496,000/124,000 shared train/validation split, including hashes of **labels as well as inputs**. Older caches missing identity fields must be rebuilt through the current cache preparation script; do not edit their metadata to bypass checks.

## 7. Artifacts and remaining evidence

Each run retains the existing atomic checkpoint generations and adds:

| File | Purpose |
|---|---|
| `source_manifest.json` | Code and runtime-version identity; prevents resuming against changed sources. |
| `cost_contract.json` | Cost convention, module ledger and explicit hardware limitations. |
| `initialization.json` | Matched backbone evidence and training-only tokenizer fit. |
| `engram_result.json` | Reloaded checkpoint cost, accuracy/AUC, provenance and occupancy. |
| `validation_predictions.npz` | Paired input-aligned validation comparison. |
| `memory_tables.npz` | Quantized inference table values; not an HLS binary. |
| `memory_tokenizer.json` | Frozen bin edges and padding threshold. |
| `tracking_destination.json` | Verified private W&B entity/project when tracking is enabled. |

The preflight checks table-address equivalence against an independent NumPy implementation, jet boundaries, padding, tuple permutation equivariance, nonzero finite gradients, rounding/saturation, serialization, all eight graph insertions, binary projection preservation, custom cost visibility, optimizer behavior, private-destination guardrails, nonmutating diagnostics, and interrupted/uninterrupted training agreement. Its synthetic accuracies are deliberately not presented as jet-tagging results.

The next evidence needed is GPU validation accuracy at equal training prefixes and actual attained costs. If that is favorable, implement fixed-point table/gate lowering and verify C/RTL numerics, whole-jet II, memory resources and timing. The current implementation is ready for that **training experiment**, not for FPGA deployment. No source reviewed establishes that Engram improves this particular jet tagger, and no such improvement is claimed here.
