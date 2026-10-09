---
title: what do u think about pyrtlnet
date: 2026-09-01
updated: "2026-09-09T22:19:54"
project: bnjettag-training-results
cwd: /Users/kaiyamaguchi/Downloads/bnjettag-training-results
model: <synthetic>
git_branch: main
session_id: ad9e21eb-62d2-4048-89c6-2bfa3e4bf229
turns: 4
tool_calls: 44
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-training-results
---

# what do u think about pyrtlnet

> [!abstract]- Session at a glance
> **4** turns · **44** tool calls · spans **4** h **29** min · `<synthetic>`
>
> **Tools** Bash ×36, WebFetch ×3, WebSearch ×2, AskUserQuestion ×1, Skill ×1, ToolSearch ×1
> **Commands** `/hls-mulder`

---

## You · 14:37

what do u think about pyrtlnet

---

## Claude · 14:39

Looked it up — it's [UCSBarchlab/pyrtlnet](https://github.com/UCSBarchlab/pyrtlnet), and I'd call it a genuinely nice teaching artifact that is not useful to you as tooling.

**What it actually is.** A two-layer dense MNIST net (12×12 → 18 → 10), trained in TensorFlow, **int8 LiteRT-style quantized** — not binary — then re-implemented three times: LiteRT reference, NumPy + fxpmath, and PyRTL at the gate level. All three must produce bit-identical output. It emits Verilog, simulates under Verilator, and runs on a Pynq-Z2 (Zynq-7020). ~12 stars, explicitly readability-over-performance, no published resource or latency numbers. Its own README lists the limits: two layers only, no conv or transformer, incomplete batching, full hardware reset between inferences.

**The one idea worth stealing** is the discipline, not the code: three independent implementations at three abstraction levels forced to agree exactly. That's the right way to catch a quantization bug that hides in the gap between "the model I trained" and "the thing on the chip." Your QAT → hls4ml csim → csynth chain plays exactly that role, so you already have the property — pyrtlnet just makes it the headline feature.

**Why it doesn't touch BNJetTag.** It's off-thesis (int8, not {−1,+1}), there's no attention, no initiation-interval or pipelining story, wrong device class next to your VU13P, and hls4ml is the flow the FastML/L1-trigger audience reads. Building an RTL path in PyRTL would cost you months and buy you a harder sell. If a hand-written XNOR/popcount datapath ever becomes interesting, that's the compiler/adder-graph workstream, which is out of scope in this tree anyway.

**One thing that might actually matter:** there's a separate IEEE paper, *"Hardware-Accelerated 1-Bit Quantization Using PyRTL for Efficient Neural Network Design"* — uses the PyRTL language for XNOR-style BNNs, distinct from this repo. It's paywalled and I couldn't get the abstract, so I have no numbers and won't guess at authors. If you ever write a related-work paragraph on binary-NN hardware flows outside hls4ml, that one's worth a proper dossier pass. Say the word and I'll run it.

Logged the finding with dates and URLs in `.claude/memory/research-log.md`.

Sources:
- [UCSBarchlab/pyrtlnet (GitHub)](https://github.com/UCSBarchlab/pyrtlnet)
- [pyrtlnet reference documentation](https://pyrtlnet.readthedocs.io/en/latest/)
- [Hardware-Accelerated 1-Bit Quantization Using PyRTL (IEEE Xplore)](https://ieeexplore.ieee.org/document/10941946/)

---

## You · 14:41

can u try vivado syntehsis on the ternary models that we have

---

## Claude · 14:50

I checked before running anything, and the premise doesn't hold: **there are no ternary models in this tree.** Here's what's actually there.

**Round 14 has never had a ternary arm.** The weight-quantizer whitelist in `bnjettag/code/hgq2/bnhgq2/qat.py:360` is `none | binary_absmean | int8_absmax | kbi_learnable`. Census of every config in `code/` and `results/`: 31 `binary_absmean`, 6 `int8_absmax`, 5 `none`, zero ternary. No ternary job YAML, no ternary entry in `results/synthesis/runs/`.

**Ternary models do exist — but only from the QKeras era.** Three finished W&B runs, all 2026-06-23, in project `Old dataset runs`, each carrying a `bitnet/noNorm_train_bitnetJetTagModel.h5`:

| run | id | val AUC | epoch |
|---|---|---|---|
| `paper-ternary-…-clipON` | i7ac0cfg | 0.7638 | 23 |
| `fixed-max-ternary-…-nowu-esauc` | jhs8p7z5 | 0.6837 | 16 |
| `fixed-max-ternary-…-wu3-esauc` | hsf37nir | 0.6259 | 8 |

Job YAMLs are in `_attic/legacy-archive/…/kai-bn-train-paper-ternary.yaml` (flag `BN_TERNARY=1`).

**Three independent reasons I can't just point csynth at them:**

1. **Scale.** They're D256 / 8 heads / 8 layers / FFN 1024 — **6,373,633 parameters**. Round 14 is `d_model=32`, `n_heads=4`, `n_layers=2`, `ffn_dim=64`. That's ~200× the parameters, and r14n16 at RF=1 already SIGKILLed Vitis at 112.5 GB of 125 GB. It won't complete, and if it did it wouldn't fit a VU13P.
2. **Toolchain.** QKeras-era `.h5`. The HGQ2 `convert_final.py` export path can't ingest it, and the QKeras HLS code lives in `_attic`.
3. **Comparability.** Old dataset, different input representation, stopped at epochs 8–23 of 200, and those are *validation* AUCs — not ROC-test. Nothing about them can sit next to a Round-14 number.

(Terminology: "Vivado synthesis" here means Vitis HLS C-synthesis on mulder — bitstream place-and-route is out of scope. mulder is up and idle, 64 cores; I've launched nothing.)

Getting a ternary number worth having is a new experiment, not a synthesis run. Logged the inventory in `.claude/memory/experiment-log.md`.
