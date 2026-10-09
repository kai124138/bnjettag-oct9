# Do BitNet Gains Survive Synthesis? An Implementation-Aware Benchmark of Low-Precision FPGA Inference for Jet Classification

- **Author:** Dorian Sloot (Atominstitut, TU Wien; Marietta Blau Institute for Particle Physics, Austrian Academy of Sciences)
- **Venue / Year:** 7th Fast Machine Learning for Science Conference (FastML 2026)
- **Indico:** https://indico.cern.ch/event/1654479/papers/7189055/files/16211-11_Do_BitNet_Gains_Survive_Syn.pdf
- **Code:** https://github.com/nairods/fastml_bitnet_benchmark
- **Topic area:** hls4ml / FPGA triggers — BitNet-in-hls4ml benchmark
- **★ load-bearing:** the first independent BitNet-vs-HGQ-vs-QKeras head-to-head we have logged, under one HLS flow, on our FPGA part, at our conference.

## TL;DR
A controlled benchmark of low-precision MLPs for FPGA jet classification on the OpenML
`hls4ml_lhc_jets_hlf` 16-feature dataset (binary q/g vs W/Z/t task), 64–32–32 topology,
3 seeds, all synthesized through hls4ml/Conifer to Vitis HLS **C-synthesis** on a VU13P at
5 ns, II = 1. Conclusion: BitNet-style learned scaling beats naïve binary/ternary QKeras on
accuracy, but **HGQ dominates the neural Pareto frontier** (AUC 0.9276 at 8.0k LUT / 0 DSP vs
BitNet binary 0.9178 at 87.3k LUT / 0 DSP), and an unrolled BDT has the lowest latency.
The stated moral: "theoretical operation-count reduction alone is insufficient to predict
synthesised FPGA efficiency."

## Summary
Model families: dense MLP, QKeras 7-bit, HGQ, QKeras binary, QKeras ternary, BitNet binary,
BitNet-1.58 ternary, XGBoost BDT. Identical features, preprocessing, 64/16/20 stratified split,
seeds 42–44, synthesis constraints. Metrics: accuracy, AUC, signal efficiency at 1% FPR,
latency in cycles, LUT, DSP.

Table 1 (mean ± sd over 3 seeds, C-synthesis estimates, VU13P, 5 ns, II = 1):

| Model | AUC | ε_S @1% FPR | Cycles | LUT [10³] | DSP |
| --- | --- | --- | --- | --- | --- |
| Dense MLP | 0.9350 ± 0.0003 | 0.5996 | 13.0 | 182.9 | 3651 |
| QKeras 7-bit | 0.9342 ± 0.0002 | 0.5948 | 9.7 | 139.3 | 981 |
| HGQ | 0.9276 ± 0.0002 | 0.5711 | 6.7 | **8.0** | 0 |
| QKeras binary | 0.8981 ± 0.0004 | 0.4827 | 21.7 | 60.6 | 0 |
| QKeras ternary | 0.9103 ± 0.0002 | 0.5023 | 14.7 | 35.7 | 0 |
| BitNet binary | 0.9178 ± 0.0001 | 0.4994 | 12.0 | 87.3 | 0 |
| BitNet-1.58 | 0.9254 ± 0.0008 | 0.5439 | 10.0 | 80.7 | 0 |
| BDT (unrolled) | 0.92075 | 0.5612 | 4.0 | 74.1 | 0 |

Explicitly out of scope, per its own limitations paragraph: constituent-level representations,
trigger-native datasets, other devices, and **place-and-route**.

## What the released code actually does (read 2026-09-01, `bitnet_layers.py`, `hardware_benchmark/bitnet.py`, `scripts/synthesize_bitnet_hls4ml_patched.py`)
- Binarization is the same absmean rule we use: `alpha = mean(W)`, `beta = mean(|W|)`,
  `q = sign(W - alpha)`, STE via `w + (q*beta - w).detach()`. `torch.sign` — no bipolar tie rule,
  so a zero state is possible in principle (they do not gate on it; we do).
- Activations: **dynamic per-sample** `gamma = Q_b / max|x|` at training time (BitNet absmax),
  not our static per-tensor grid.
- **β is not in their hardware datapath at all.** `predict_folded_logits` keeps a running
  `cumulative_scale = Π β_l`, pre-divides each layer's bias by it, and applies one scalar
  `output * cumulative_scale` on the logit. ReLU positive-homogeneity makes this exact for an MLP,
  and for a binary sigmoid task the final scalar is monotone → invisible to AUC and ε_S@FPR.
- The cost reappears as **accumulator width**: `ACCUM_PRECISIONS` climbs
  `ap_fixed<28,10> → <32,14> → <34,16> → <40,22>` layer by layer (integer bits 10→22),
  `mult_t` `<17,7> → <31,15>`, ReLU up to `ap_ufixed<28,14>`. Consistent with the 1/Πβ dynamic-range growth
  the fold pushes downstream (≈3–4 integer bits per layer), and plausibly where the +27k LUT over QKeras
  binary goes — but they state no reason for those widths, so this is our inference, not their claim.
- hls4ml is **hand-patched**: `nnet_dense` is replaced by an explicit
  `if (w>0) acc += x; else if (w<0) acc -= x; else 0;` kernel, weights forced to `ap_int<2>`.
  The `else 0` branch is what lets BitNet-1.58's zero weights synthesize away — the mechanism
  behind ternary beating binary on LUT in their table.

## Relevance to BNJetTag
Same conference, same FPGA part, adjacent question — but a different regime and one stage shallower.
1. **Ternary beats binary on every axis in their table** (AUC 0.9254 vs 0.9178, 80.7k vs 87.3k LUT,
   10 vs 12 cycles). This tree has no ternary arm by decision, so we cannot rebut with data.
   Open flank; see `decisions.md` on ternary being a comparison baseline only.
2. **HGQ at 8.0k LUT / 0 DSP** is the strongest objection to "binary buys you 0 DSP" — HGQ gets
   0 DSP too, at a tenth the LUT and higher AUC. Our counter is regime, not method: their dense
   baseline *fits* (3,651 DSP), so nothing forces low precision; our W8A8 baseline demands
   **5,550 DSPs = 146.2% of the VU13P** (RESEARCH.md §6.5), so it does not.
3. **We are not "HGQ + binary."** We use HGQ2's layer library with `trainable=False` weight and
   activation quantizers and `heterogeneous_axis=()`; HGQ's actual mechanism — EBOPs-regularized
   trainable per-element bit widths — is a knob we have never turned. The two axes are orthogonal
   and nobody has measured the intersection.
4. **Their title's question is decided one stage below where they measured it.** All their hardware
   numbers are C-synthesis estimates. Our §6.4 has a measured case where a csynth DSP = 0 became a
   Vivado demand of 4,096 DSPs once the fabric binding was scoped rather than solution-wide.
5. **Their β overhead is an MLP artefact; ours is structural.** ReLU homogeneity folds every β to
   one logit scalar in a plain MLP. Our graph has residual adds, a softmax and no LayerNorm to
   absorb scale, so β must be restored in-stream (6L+3 affines) — 3,621 of the 4,133 fx8 DSPs.
   Their fold is free in multipliers and paid in 40-bit accumulators; ours is paid in affines.
6. Alignments worth citing: same VU13P; **their 5 ns clock is where our fitting zero-DSP point
   closes timing** (post-opt WNS +0.647 ns, `results/r14/hls_r14_fit.md` rows 7–8); their
   ε_S@1% FPR is the metric in `results/r14/working_points_r14.md`; their limitations paragraph
   names constituent-level, trigger-native inputs as excluded — that is Round 14.

**Do not tabulate their numbers next to ours.** Binary q/g-vs-W/Z/t on 16 engineered features with a
3-layer MLP is not our 5-class macro-OvR AUC on (N, 3) constituents with a transformer.

## Open question (not answerable from the paper)
Table 1's AUC is not stated to be the software model or the synthesized one. Training uses 8-bit dynamic
per-sample absmax activations that have no counterpart in the HLS path. Their framework does contain a
fidelity harness (`_validate_hls_model` compares the compiled HLS model to `predict_folded` on random
normals; `compare_predictions` can compute candidate-vs-reference AUC), so the machinery exists — the paper
just does not say which model Table 1 reports. Our equivalent discipline is GATE1/GATE2 plus
`results/r14/export_roc_auc.md`, where the exported graph's own ROC-test AUC is measured.

## Cite it for
The scaling-factor-realisation cost of BitNet in hls4ml; an independent BitNet-in-hls4ml datapoint;
the HGQ Pareto point we have to answer; and as the paper whose central question we answer one
synthesis stage further down.
