---
title: how is the bianry, the -1 and the +1 represented?
date: 2026-09-01
updated: "2026-09-05T12:32:43"
project: bnjettag-training-results
cwd: /Users/kaiyamaguchi/Downloads/bnjettag-training-results
model: claude-opus-5
git_branch: main
session_id: f03f3428-a33a-42e4-8bf7-fdb7d538071e
turns: 4
tool_calls: 49
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-training-results
---

# how is the bianry, the -1 and the +1 represented?

> [!abstract]- Session at a glance
> **4** turns · **49** tool calls · spans **37** min · `claude-opus-5`
>
> **Tools** Bash ×48, ToolSearch ×1

---

## You · 14:44

how is the bianry, the -1 and the +1 represented?

---

## Claude · 14:47

Chased it through all four representations. Short answer: **the ±1 never exist as a stored ±1 during training, and in firmware they're a 2-bit signed fixed-point constant, not a literal bit.** The effective weight is always `w_eff = β · sign(w − mean(w))` — one sign per weight, one float β per tensor.

## 1. Training (QAT) — latent float32, ±1 only in the forward pass

`bnjettag/code/hgq2/bnhgq2/qat.py:57-64`:

```python
alpha = ops.mean(w); wc = w - alpha
beta  = ops.mean(ops.abs(wc)) + 1e-6
ws    = wc / ops.stop_gradient(beta)
q     = ops.where(wc >= 0.0, 1.0, -1.0)   # strict bipolar, never 0
wq    = ws + ops.stop_gradient(q - ws)    # STE: forward = q
return wq * beta                          # in {-beta, +beta}
```

The stored trainable variable is a full-precision latent kernel. Each forward pass centres it, takes the sign, and multiplies by the per-tensor absmean β; the backward is straight-through onto the latent. So during training the ±1 is a *function of* the weights, never the weights themselves.

Two deliberate details there: the tie rule is `>= 0 → +1` (never 0 — `sign(0)=0` would make it ternary and void the thesis), and `ws` divides by a `stop_gradient(beta)`, which is what removed the 1/β gradient explosion that NaN'd A4 training.

## 2. Export — int8 `q` + float β

`binarize.py:absmean_binarize` re-does the same math on the trained latents and returns `(q int8, beta float, alpha float, n_zero int)`. α is only the centring threshold and is discarded; β is kept separately. `n_zero` is a gate — `np.sign` here *could* emit 0 on an exact tie, so the export checks `total_sign_zeros == 0` rather than relying on construction. `port.py:36` then casts `q` to float32 ±1 into the HGQ2 graph.

Inside HGQ2 the layer carries `QuantizerConfig("kbi", "weight", k0=1, b0=1, i0=1, SAT_SYM)` — a **1-bit** config kept purely so EBOPs and hls4ml report 1 bit; the actual ±1 pass through it bit-identically (a stock HGQ2 1-bit quantizer would round to the grid {−1,0,+1} and collapse everything to zero, which is why the custom binarizer exists).

## 3. Firmware — `ap_fixed<2,2>`, and why 2 and not 1

From the shipped n8-s3 W1A8 project (`results/synthesis/runs/ba72a91a/.../firmware/`):

```c
typedef ap_fixed<2,2> input_proj_weight_t;      // defines.h
input_proj_weight_t w3[96] = {1, -1, 1, -1, ...};
```

All 15 weight arrays are pure ±1 — `Min -1.0`, `Max 1.0`, `Number of zeros 0` in every header.

**Why 2 bits for a 1-bit weight:** two's-complement `ap_fixed<1,1>` spans {−1, 0} — there is no +1 in a signed 1-bit type. The narrowest signed fixed-point that holds both ±1 is 2 bits, whose grid is {−2,−1,0,+1}; the model only ever uses two of the four codes. The information content is 1 bit; the container is 2.

One honest caveat: only the Dense-family layers (`input_proj`, `fc1`, `fc2`, `head_fc1/2`) got the narrow `ap_fixed<2,2>` typedef. The 13 `einsum_dense` layers (Wq/Wk/Wv/Wo) are declared `model_default_t` = `ap_fixed<24,12>` and print `-1.000000000000` — same values, wider container, because hls4ml assigned them the default type. Both families measure **0 DSP** at the fx8 point regardless (RESEARCH.md §6.2), so Vitis folds the ±1 either way.

## 4. The multiply — add/subtract, *not* XNOR-popcount

This is W1A8: activations are `ap_fixed<8,2>`, not binary. XNOR+popcount (Courbariaux 1602.02830) needs binary *activations* too, and we don't do it anywhere in the tree — the only XNOR mentions in the repo are literature notes. Here `±1 × a = ±a`, so each MAC is a conditional negate-and-accumulate: pure LUT logic, no multiplier. That's the mechanism behind the 0-DSP claim.

## 5. Where β actually lives

Not in the weight array. It's restored by a separate shift-add affine after each matmul (export v5, `restore_beta` in `build.py`), encoded as an fx8 constant. Those 15 affines are what cost 3,621 of the 4,133 DSPs at the fx8 RF=1 point; `config_op mul -impl fabric` pushes the whole design to **0 DSP** at +1.20M csynth LUT.

---

## You · 14:51

https://indico.cern.ch/event/1654479/papers/7189055/files/16211-11_Do_BitNet_Gains_Survive_Syn.pdf


read this paper, and tell me how it relates to our work

---

## Claude · 15:01

Read it, and cloned the released code (`github.com/nairods/fastml_bitnet_benchmark`) to check what the paper's central claim actually rests on. It's a direct neighbour: **FastML 2026, same VU13P, same question as our poster** — if that's your meeting, this is the paper in the room.

## What it is

Dorian Sloot (TU Wien / MBI). A controlled benchmark of low-precision **MLPs** on the OpenML `hls4ml_lhc_jets_hlf` set — 16 engineered features, binary q/g vs W/Z/t — fixed 64–32–32 topology, seeds 42–44, everything through hls4ml/Conifer to Vitis HLS **C-synthesis** on a VU13P at 5 ns, II=1. His Table 1:

| | AUC | ε_S@1% FPR | Cycles | LUT [10³] | DSP |
|---|---|---|---|---|---|
| Dense MLP | 0.9350 | 0.600 | 13.0 | 182.9 | 3651 |
| QKeras 7-bit | 0.9342 | 0.595 | 9.7 | 139.3 | 981 |
| **HGQ** | 0.9276 | 0.571 | 6.7 | **8.0** | 0 |
| QKeras binary | 0.8981 | 0.483 | 21.7 | 60.6 | 0 |
| QKeras ternary | 0.9103 | 0.502 | 14.7 | 35.7 | 0 |
| BitNet binary | 0.9178 | 0.499 | 12.0 | 87.3 | 0 |
| **BitNet-1.58** | 0.9254 | 0.544 | 10.0 | 80.7 | 0 |
| BDT (unrolled) | 0.9208 | 0.561 | 4.0 | 74.1 | 0 |

Moral: "theoretical operation-count reduction alone is insufficient to predict synthesised FPGA efficiency" — implementation details, especially **scaling-factor realisation**, decide whether the gains survive.

## The most useful thing I found is in his code, not his paper

`hardware_benchmark/bitnet.py` — **β never enters his hardware datapath.** `predict_folded_logits` keeps a running `cumulative_scale = Π β_l`, pre-divides each layer's bias by it, and applies one scalar `output * cumulative_scale` on the logit. ReLU positive-homogeneity makes that exact for a plain MLP, and on a binary-sigmoid task the final scalar is monotone — so it's invisible to AUC and to ε_S@FPR.

That's not a contradiction of his paper (his "scaling-factor realisation" *is* this fold), but it reframes it for us: **the β cost doesn't vanish, it moves.** His `ACCUM_PRECISIONS` climb `ap_fixed<28,10> → <32,14> → <34,16> → <40,22>` layer by layer — 10→22 integer bits — with `mult_t` up to `<31,15>` and ReLU to `ap_ufixed<28,14>`. That's consistent with 1/Πβ dynamic-range growth being pushed downstream, and plausibly where BitNet's +27k LUT over QKeras binary goes. (My inference; he gives no reason for those widths.)

**We cannot use that fold.** Residual adds, a softmax, and no LayerNorm to absorb scale mean β must be restored in-stream — the 6L+3 affines of export v5, which cost 3,621 of the 4,133 fx8 DSPs. So his β is free in multipliers and paid in 40-bit accumulators; ours is paid in affines and then bound to fabric. Same physics, opposite corner of the trade.

Two more code details: his hls4ml is **hand-patched** with an explicit `if (w>0) acc+=x; else if (w<0) acc-=x; else 0;` dense kernel and `ap_int<2>` weights — the manual version of what Vitis infers for us. That `else 0` branch is exactly why his ternary beats his binary on LUT.

## Threats, ranked

**1. Ternary beats binary on every axis in his table** — AUC 0.9254 vs 0.9178, 80.7k vs 87.3k LUT, 10 vs 12 cycles, and ε_S 0.544 vs 0.499. This is the most uncomfortable result for a binary-is-the-thesis project, and someone from that room will lead with it. We have **no ternary arm** in this tree by decision (ternary = comparison baseline only), so we can't rebut with data. It's an open flank, not a refuted objection. Worth a decision on whether that stays true.

**2. HGQ also gets 0 DSP — at a tenth the LUT and a higher AUC.** This is the strongest objection to "binary buys you zero DSP." Our answer has to be regime, not method: in his setup the *dense* baseline fits at 3,651 DSPs, so nothing forces low precision. In ours, the W8A8 baseline demands **5,550 DSPs = 146.2% of the VU13P** (§6.5). The binary question only becomes live where the full-precision design doesn't fit, and his benchmark is deliberately in the regime where it does.

**3. We are not "HGQ + binary" — don't claim it.** `build.py`/`qat.py` use HGQ2's layer library with `trainable=False` on both weight and activation quantizers and `heterogeneous_axis=()`. HGQ's actual mechanism — EBOPs-regularized trainable per-element bit widths, which is what produced his 8.0k-LUT point — is a knob we've never turned. The two axes are orthogonal and compatible; nobody has measured the intersection.

**4. His title's question is decided one stage below where he measured it.** Everything in his Table 1 is a C-synthesis estimate, and he says so in Limitations. §6.4 has our measured case where csynth reported DSP = 0 and Vivado then demanded 4,096 — the 10-bit × 8-bit act×act attention products re-inferred as DSP48E2s. An MLP has no act×act products, so this isn't a prediction that his zero would flip; it's that we can answer his question at a stage he didn't reach, which is a real differentiator for the poster.

**5. Open question I couldn't resolve:** the paper doesn't say whether Table 1's AUC is the software model or the synthesized one. Training uses 8-bit dynamic per-sample absmax activations with no counterpart in the HLS path. His repo *does* have a fidelity harness (`_validate_hls_model` vs `predict_folded`), so the machinery exists — it just isn't stated. That's the gap our GATE1/GATE2 + `export_roc_auc.md` discipline closes.

## Alignments worth having ready

Same part. **His 5 ns clock is exactly where our fitting zero-DSP point closes timing** (post-opt WNS +0.647 ns, 0 failing endpoints, `hls_r14_fit.md` rows 7–8) — convenient. His ε_S@1% FPR is our `working_points_r14.md` metric. And his Limitations paragraph names "constituent-level representations, trigger-native datasets" as excluded — that's Round 14, so we occupy the gap he flagged rather than colliding with him.

One caution: never tabulate his numbers beside ours. Binary q/g-vs-W/Z/t on 16 engineered features with a 3-layer MLP is not our 5-class macro-OvR AUC on (N, 3) constituents with a transformer.

## Logged

- Dossier: `docs/literature/hls4ml-fpga-triggers/fastml2026_sloot_bitnet_survive_synthesis.md`
- `docs/literature/INDEX.md` — new ★ line (count 53 → 54)
- `.claude/memory/research-log.md` — dated entry with both URLs

Not touched: `RESEARCH.md`, the poster, no commit. Two things I'd flag but didn't act on — the poster and speech mention HGQ **only as the training framework**, never as a competing baseline, and there's no ternary line anywhere in them. This paper puts both questions in the room.
