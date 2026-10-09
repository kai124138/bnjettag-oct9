---
title: have we used, Grouped-Query Attention (GQA)? and are there papers which already…
date: 2026-09-01
updated: "2026-09-05T12:32:44"
project: bnjettag-training-results
cwd: /Users/kaiyamaguchi/Downloads/bnjettag-training-results
model: claude-opus-5
git_branch: main
session_id: b8d83ef4-af95-499d-9429-febf33e5d557
turns: 4
tool_calls: 25
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-training-results
---

# have we used, Grouped-Query Attention (GQA)? and are there papers which already…

> [!abstract]- Session at a glance
> **4** turns · **25** tool calls · spans **38** min · `claude-opus-5`
>
> **Tools** Bash ×17, WebSearch ×4, WebFetch ×3, ToolSearch ×1

---

## You · 14:44

have we used, Grouped-Query Attention (GQA)? and are there papers which already exists that use Grouped-Query Attention (GQA)

---

## Claude · 14:48

**No — we have never used GQA.** R14 attention is plain multi-head self-attention.

`bnjettag/code/hgq2/bnhgq2/build.py:216-226` builds Wq, Wk, Wv as three separate `QEinsumDense("btd,dhe->bthe")` layers with the *same* output shape `(T, H, E)`:

- `d_model` = 32, `n_heads` = 4 → head dim E = 8, `n_layers` = 2 (`configs/r14-l1x3-n*-w1a*.json`)
- 4 query heads, 4 key heads, 4 value heads — G = H, i.e. the MHA end of the GQA spectrum

Nothing in the tree, `docs/literature/INDEX.md`, or the memory logs mentions GQA, MQA, or KV-head sharing.

## Papers that use GQA

**Origin:** Ainslie et al., [arXiv:2305.13245](https://arxiv.org/pdf/2305.13245) — G key/value heads shared across H query heads, interpolating between MHA (G=H) and multi-query attention (G=1). The motivation is *KV-cache memory bandwidth during autoregressive decoding*, not compute.

**In LLMs it's now the default:** Llama 2/3, [Mistral 7B](https://huggingface.co/docs/transformers/en/model_doc/mistral), [Mixtral](https://huggingface.co/docs/transformers/en/model_doc/mixtral), Qwen, Gemma. A variant, [Weighted GQA (arXiv:2407.10855)](https://arxiv.org/html/2407.10855v1), adds learned per-head weights to the grouping.

**On FPGA, one precedent:** [HLSTransform (arXiv:2405.00738)](https://arxiv.org/pdf/2405.00738) — Llama 2 inference through HLS, carrying GQA + RoPE + RMSNorm because it reproduces the Llama 2 architecture. Autoregressive decode, millisecond scale, nothing like an L1 trigger.

**In FPGA jet tagging, nobody uses it.** I full-text checked all three transformers we track: [JetFormer (2601.17215)](https://arxiv.org/html/2601.17215v1) — standard MHA, 2 or 8 heads; [PHAT-JeT (2605.21789)](https://arxiv.org/html/2605.21789v1) — "all transformer-based models use four attention heads … and a single attention layer"; 2510.24784 — its arms are MHA and Linformer, per our own deep-read.

## Why it wouldn't help us

GQA solves a cost our design doesn't have. We run a single-shot encoder over N ≤ 64 particles, fully unrolled, no KV cache, no decode loop, and H = 4 where GQA targets H = 32–128. It would leave the act×act scores/ctx einsums and the softmax untouched (scores stay H_q × T × T × E) — and those are precisely the parts binarization does *not* shrink. Its only effect would be fewer Wk/Wv weights: by config arithmetic, GQA-2 removes 2048 of the 16384 binary weights in the two blocks (12.5%), MQA-1 removes 3072 (18.75%). That is a weight count, not a measured LUT saving — I did not read a per-layer csynth breakdown.

If you want attention cheaper, the published lever in our regime is sequence-axis approximation (Linformer in 2510.24784, patching in PHAT-JeT), not KV-head sharing.

Logged in `.claude/memory/research-log.md`, newest on top.

One flag: a fetch summary claimed JetFormer uses 1-bit ±1 weights with 8-bit activations. That came from a small summarizer model, not the PDF, and our 2026-08-04 log entry records no quantization scheme for it. If it's true, that's a direct competitor — worth a proper dossier before anyone quotes it.

Sources: [2305.13245](https://arxiv.org/pdf/2305.13245) · [2407.10855](https://arxiv.org/html/2407.10855v1) · [2405.00738](https://arxiv.org/pdf/2405.00738) · [2601.17215](https://arxiv.org/html/2601.17215v1) · [2605.21789](https://arxiv.org/html/2605.21789v1) · [Mistral](https://huggingface.co/docs/transformers/en/model_doc/mistral) · [Mixtral](https://huggingface.co/docs/transformers/en/model_doc/mixtral)

---

## You · 14:57

wait tell me more about our design

---

## Claude · 14:58

Here's the design, as it actually exists in the tree.

## The network

`bnjettag/code/hgq2/bnhgq2/build.py`, configured by `configs/r14-l1x3-n<N>-<variant>.json`:

```
input (N, 3)              N ∈ {8,16,32,64}; pT, η_rel, φ_rel — what L1 actually gets
  → input_proj  "btf,fd->btd"   3→32, bias_axes="td"  ← learned PE folded into this bias table
  → 2 × BitBlock:
        Wq, Wk, Wv   "btd,dhe->bthe"    32 → (4 heads × 8)
        scores       "bthe,bshe->bhts"  ← act × act, no weights
        softmax      QSoftmax, 1/√8 folded into its exp-LUT scale
        ctx          "bhts,bshe->bthe"  ← act × act, no weights
        Wo           "bthe,hed->btd"    (4×8) → 32
        + residual
        fc1 32→64 → ReLU → fc2 64→32, + residual
  → GAP over particles (permutation-invariant)
  → head_fc1 32→32 → ReLU → head_fc2 32→5
```

d_model 32, 2 layers, 4 heads, FFN 64 — the r8 `small` recipe verbatim. **17,664 binary weights total** (config arithmetic): 16,384 in the two blocks, 1,184 in the head, 96 in the input projection.

Every weight matrix is a `QEinsumDense` with a `{−1,+1}` kernel pinned by a KBI quantizer (`k0=1, b0=1, i0=1`, `trainable=False`) — it passes ±1 through bit-identically and reports 1 bit to EBOPs. There is no `MultiHeadAttention` layer; attention is composed from the same IR primitives hls4ml's MHA handler would decompose into anyway, because native `QMultiHeadAttention` can't express our norm placement.

## The part that's actually clever: what happens to β

BitLinear is `Sign(W−α)·β`. That per-layer scale β is the whole ballgame for DSP-free mapping — if β rides *inside* the kernel, the operands stop being 2-bit and Vivado infers real multipliers (measured: 256 DSPs at RF=1). So every β is pulled out and disposed of by category (`build.py:69-82`):

| fold class | layers | what happens to β |
| --- | --- | --- |
| `score_fold` | Wq, Wk | β_q·β_k/√d_head folded into the softmax exp-LUT — free, exact |
| `ln_killed` | Wv | dropped (the next norm is scale-invariant) |
| `bias_fold` | fc1, head_fc1 | bias ported as b/β |
| `explicit` | input_proj, Wo, fc2, head_fc2 | CSD-2 constant — 2 signed digits, shift-add, DSP-free |

## Norm-free (export v5), and why it exists

`arch.norm: "none"`. Round 14 exposed a real defect: with no LayerNorm left to absorb anything, the exporter had been re-deriving the β-carry-site activation grids "wide enough never to clip," while the trained checkpoints *deliberately saturate* those grids. The export was a functionally different network — GATE1 score correlation 0.839, argmax agreement 74%.

v5 fixes it by restoring every β in-graph through its own frozen affine (**6L+3 = 15 affines**) and applying every trained grid verbatim. GATE1 recovered to 0.9988 (n8-s3) / 0.9974 (n16-s1), GATE2 hls4ml C-sim bit-exact.

## Where the cost actually lands

This is the finding that matters, and it inverts the naive picture. From the per-module attribution in `RESEARCH.md` §6.4 (n8-s3):

- **The binary matmuls are already 0 DSP** at C-synthesis — all 13 `einsum_dense` plus both head `QDense`. The thesis mechanism works and is verified at Vivado synthesis, not just csynth.
- **The 4,133 DSPs at the fx8 RF=1 point are not weights at all**: 3,621 from the 15 β-restore affines, 512 from softmax. Binding them to fabric gets the whole model to 0 DSP, at +1.20M csynth LUT (~195–210 LUT per shed DSP).
- **The act×act attention einsums cost 645k–949k csynth LUT** and are *identical across every arm* — FP32, W8A8, W1A8 all pay the same. They're weightless, so binarization does nothing for them, and they grow as N².
- Scoping the fabric binding instead of applying it solution-wide hands **4,096 DSPs back** — exactly the ctx-einsum MAC count at N=8 — because Vivado re-infers 10b×8b products as DSP48E2s. Hence the standing rule: every zero-DSP claim is verified at Vivado synthesis, never csynth alone.

The current best point: narrowing the softmax operand from `ap_ufixed<10,1>` to `<4,0>` and retraining gives **1,689,320 CLB LUT = 97.8% of the VU13P at 0 DSP**, AUC 0.8701 ± 0.0020, meeting 5 ns pre-route (240 ns/jet, 1.67 µs). Against it, W8A8 demands 5,550 DSPs and 146.2% of the device.

## Why this connects back to your GQA question

The design's cost is concentrated in exactly the places attention-head restructuring doesn't touch. The weight layers are already free of multipliers; the expensive parts are the weightless einsums, the requantisation casts (~155 LUT/element), softmax, and the β affines. GQA would shave Wk/Wv weight *count* — the cheapest thing in the budget. The lever that would actually move the LUT number is narrowing the attention datapath, which is precisely what the 10→4 bit softmax-operand change did.

Also worth noting for the record: four cost-model projections were made during the fit campaign, and each was killed by the measurement it predicted. On this design class, projections have no standing.

Want me to go deeper on any one of these — the β fold derivation, the accuracy story (binary destabilizes at N ≥ 32 in a specific, per-class way), or the fit campaign's closed levers?
