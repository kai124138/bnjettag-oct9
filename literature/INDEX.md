# Literature index

55 papers, one annotated note each. **This file is the entry point.** Find the paper here,
then open its one note. Do not read the tree.

★ = load-bearing: cited in `RESEARCH.md`, or a direct threat to our claim.

Notes follow a fixed shape — metadata, `## TL;DR`, `## Summary`, `## Relevance to BNJetTag`.
PDFs are gitignored; fetch with `./download_papers.sh`. Upstream *code* is in
`../../reference-code/`.

---

## 1 · BitNet & 1-bit / ternary quantization
*The training method we adapt.*

| arXiv | Paper | Why it matters to us |
| --- | --- | --- |
| ★ [2310.11453](bitnet-1bit-ternary/2310.11453_bitnet_scaling_1bit_transformers.md) | BitNet | The BitLinear layer we implement — 1-bit weights trained from scratch, not post-quantized |
| ★ [2402.17764](bitnet-1bit-ternary/2402.17764_era_of_1bit_llms_1p58.md) | BitNet b1.58 | Ternary {−1,0,+1}. Our comparison baseline, not our thesis |
| ★ [2411.04965](bitnet-1bit-ternary/2411.04965_bitnet_a4p8_4bit_activations.md) | BitNet a4.8 | Prior art for pushing activations to 4 bits — our A4 arm |
| [2504.12285](bitnet-1bit-ternary/2504.12285_bitnet_b1p58_2b4t_technical_report.md) | BitNet b1.58 2B4T | First open native 1-bit LLM at 2B scale; evidence 1-bit trains stably |
| [1605.04711](bitnet-1bit-ternary/1605.04711_ternary_weight_networks.md) | Ternary Weight Networks | Pre-LLM ternary with one scale factor; ancestor of the absmean quantizer |
| [1612.01064](bitnet-1bit-ternary/1612.01064_trained_ternary_quantization.md) | Trained Ternary Quantization | Learns asymmetric scales per layer — the α/β question in our quantizer |

## 2 · QAT & binary-NN foundations
*Why the gradient works at all.*

| arXiv | Paper | Why it matters to us |
| --- | --- | --- |
| ★ [1308.3432](qat-binary-nn-foundations/1308.3432_straight_through_estimator.md) | Straight-Through Estimator | The STE our binary backward pass depends on |
| [1511.00363](qat-binary-nn-foundations/1511.00363_binaryconnect.md) | BinaryConnect | Binary weights + full-precision shadow weights — our training setup |
| [1602.02830](qat-binary-nn-foundations/1602.02830_binarized_neural_networks.md) | Binarized Neural Networks | Binary weights *and* activations → XNOR+popcount |
| [1603.05279](qat-binary-nn-foundations/1603.05279_xnor_net.md) | XNOR-Net | Real-valued scaling factors rescue accuracy — why β exists |
| [1805.06085](qat-binary-nn-foundations/1805.06085_pact.md) | PACT | Learnable activation clipping threshold; compare to our trainable calibration |
| [1902.08153](qat-binary-nn-foundations/1902.08153_lsq.md) | LSQ | Learned step size — the other way to train an activation grid |
| [2004.03333](qat-binary-nn-foundations/2004.03333_binary_neural_networks_survey.md) | Binary NN survey | Orientation; use for related-work breadth |
| [2103.13630](qat-binary-nn-foundations/2103.13630_quantization_survey.md) | Quantization survey | Orientation; the standard taxonomy reference |

## 3 · hls4ml & FPGA triggers
*The deployment path and its published baselines.*

| arXiv | Paper | Why it matters to us |
| --- | --- | --- |
| ★ [FastML 2026](hls4ml-fpga-triggers/fastml2026_sloot_bitnet_survive_synthesis.md) | Do BitNet Gains Survive Synthesis? | **Same venue, same VU13P.** BitNet vs HGQ vs QKeras in one HLS flow: HGQ wins the Pareto, ternary beats binary — the objections we must answer |
| ★ [2604.22293](hls4ml-fpga-triggers/2604.22293_hgq_lut.md) | HGQ-LUT | **What "LUT-aware training" means in 2026, on our part and datasets.** LUT-native neurons trained at GPU speed; 0 DSP by deleting operations, not by cheapening them — no transformer, no binary weights |
| ★ [1804.06913](hls4ml-fpga-triggers/1804.06913_fast_inference_dnn_fpga_particle_physics.md) | hls4ml | The tool we synthesize through, and the dataset paper |
| ★ [2402.01876](hls4ml-fpga-triggers/2402.01876_ultrafast_jet_classification_hl_lhc.md) | Ultrafast jet classification | **Source of our (N,3) L1-realistic input convention** — Round 14 is input-matched to it |
| [2006.10159](hls4ml-fpga-triggers/2006.10159_autoqkeras_heterogeneous_quantization.md) | QKeras / AutoQKeras | The QAT library our earlier rounds used |
| [2409.05207](hls4ml-fpga-triggers/2409.05207_low_latency_transformer_hls4ml.md) | Low-latency transformers on FPGA | Transformers through hls4ml before the sub-µs paper |
| [2102.11289](hls4ml-fpga-triggers/2102.11289_ps_and_qs_quantization_aware_pruning.md) | Ps and Qs | Pruning × quantization interaction at the extremes |
| [2101.05108](hls4ml-fpga-triggers/2101.05108_fast_cnn_fpga_hls4ml.md) | Fast CNNs with hls4ml | CNN support; resource-model background |
| [2008.03601](hls4ml-fpga-triggers/2008.03601_garnet_gnn_fpga_particle_reco.md) | GarNet | Sub-µs GNN firmware; a non-transformer point of comparison |
| [2507.04535](hls4ml-fpga-triggers/2507.04535_da4ml.md) | da4ml | Multiplier-free adder graphs in hls4ml — the DSP-elimination alternative to ours |

## 4 · Jet tagging & transformers
*The models we binarize, and who might scoop us.*

| arXiv | Paper | Why it matters to us |
| --- | --- | --- |
| ★ [2510.24784](jet-tagging-transformers/2510.24784_submicrosecond_transformers_jet_tagging_fpga.md) | Sub-µs Transformers for Jet Tagging | **The closest published system.** Our differentiator is the 1-bit core and its DSP-free mapping |
| ★ [2508.07431](jet-tagging-transformers/2508.07431_bitpart.md) | 1-bit quantization in top taggers | **Nearest competitor.** Binarizes only FFN + head, leaves attention full-precision — we go further |
| ★ [1908.05318](jet-tagging-transformers/1908.05318_jedi_net.md) | JEDI-net | Interaction networks; co-source of our benchmark dataset |
| [2202.03772](jet-tagging-transformers/2202.03772_particle_transformer.md) | Particle Transformer (ParT) | The transformer family we binarize; JetClass dataset |
| [1902.08570](jet-tagging-transformers/1902.08570_particlenet.md) | ParticleNet | The particle-cloud framing behind permutation-invariant pooling |
| [1810.05165](jet-tagging-transformers/1810.05165_energy_flow_networks.md) | Energy Flow Networks | Deep Sets for jets; IRC-safe by construction |
| [2508.15468](jet-tagging-transformers/2508.15468_jedi_linear.md) | JEDI-linear | O(N) instead of O(N²) — relevant to our N-scaling problem |
| [2407.08682](jet-tagging-transformers/2407.08682_miart.md) | MIParT | ParT follow-up with wider interaction attention |
| [1902.09914](jet-tagging-transformers/1902.09914_ml_landscape_top_taggers.md) | ML landscape of top taggers | The community benchmark; use for baseline breadth |
| [2201.08187](jet-tagging-transformers/2201.08187_lorentznet.md) | LorentzNet | Lorentz-equivariant GNN |
| [2211.00454](jet-tagging-transformers/2211.00454_pelican.md) | PELICAN | Permutation-equivariant, Lorentz-invariant |
| [2310.16121](jet-tagging-transformers/2310.16121_nanopelican.md) | 19 Parameters Is All You Need | Extreme parameter economy — a different route to the same budget |
| [2405.14806](jet-tagging-transformers/2405.14806_lgatr.md) | L-GATr | Geometric-algebra transformer |
| [2311.14160](jet-tagging-transformers/2311.14160_jet_tagging_distillation.md) | Jet tagging distillation | Knowledge distillation for efficient taggers |
| — | [Replication targets for 2510.24784](jet-tagging-transformers/2510.24784_replication-targets_hgq2-examples.md) | What to reproduce from the sub-µs paper + its HGQ2 example code |

## 5 · LUT-native neural networks
*The rival philosophy: put the whole neuron in a truth table.*

| Ref | Paper | Why it matters to us |
| --- | --- | --- |
| [2004.03021](lut-native-nn-fpga/2004.03021_logicnets.md) | LogicNets | The seed paper of the family |
| [1807.08716](lut-native-nn-fpga/1807.08716_nullanet.md) | NullaNet | The "neuron as truth table" idea LogicNets credits |
| [1904.00938](lut-native-nn-fpga/1904.00938_lutnet.md) | LUTNet | Precursor; LUT as the compute primitive |
| [2309.02334](lut-native-nn-fpga/2309.02334_polylut.md) | PolyLUT | Polynomial per neuron; fewer layers, lower latency |
| [2406.04910](lut-native-nn-fpga/2406.04910_polylut_add.md) | PolyLUT-Add | Widens fan-in without exponential LUT cost |
| [2403.00849](lut-native-nn-fpga/2403.00849_neuralut.md) | NeuraLUT | A whole sub-network hidden inside one LUT |
| [2504.00592](lut-native-nn-fpga/2504.00592_neuralut_assemble.md) | NeuraLUT-Assemble | Fixes NeuraLUT's fan-in wall |
| [2501.01511](lut-native-nn-fpga/2501.01511_treelut.md) | TreeLUT | GBDTs, not NNs — the cheapest baseline in this space |
| FPGA'24 | [CompressedLUT](lut-native-nn-fpga/2024_compressedlut_fpga24.md) | Lossless LUT compression |
| FPGA'25 | [AmigoLUT](lut-native-nn-fpga/2025_amigolut_fpga25.md) | Scaling LUT-native NNs by ensembling |

## 6 · Compilers, IR & hardware generation
*Background for the adder-graph / compiler workstream (parked in `_attic/`).*

| arXiv | Paper | Why it matters to us |
| --- | --- | --- |
| [1909.04509](compiler-ir-hardware/1909.04509_unrolling_ternary_neural_networks.md) | Unrolling Ternary NNs | Closest prior art for adder-graph optimization on ternary weights |
| [2507.04535](compiler-ir-hardware/2507.04535_da4ml_distributed_arithmetic_fpgas.md) | da4ml | Distributed arithmetic replacing constant matrix-vector multiply |
| [1612.07119](compiler-ir-hardware/1612.07119_finn_binarized_nn_fpga.md) | FINN | The original binarized-NN FPGA framework |
| [2408.15561](compiler-ir-hardware/2408.15561_cgra4ml.md) | CGRA4ML | RTL-generating alternative to HLS, explicitly positioned against hls4ml |
| [2508.15468](compiler-ir-hardware/2508.15468_jedi_linear_gnn_fpga.md) | JEDI-linear (hardware view) | The firmware side of the linear GNN |
| [2512.06177](compiler-ir-hardware/2512.06177_pytorch_to_calyx.md) | PyTorch → Calyx | An open compiler toolchain to synthesizable RTL |

---

## Known gap

**HGQ (arXiv:2405.00645)** is cited in `RESEARCH.md` as the source of the EBOPs metric and
the HGQ2 QAT stack, but has no note here. It is the one load-bearing reference without one.
