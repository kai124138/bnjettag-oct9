---
title: what do u think about using qronos in our resaerch and waht are the proactical…
date: 2026-09-02
updated: "2026-09-05T12:32:43"
project: bnjettag-training-results
cwd: /Users/kaiyamaguchi/Downloads/bnjettag-training-results
model: claude-opus-5
git_branch: main
session_id: 610d567b-5c78-4860-94d3-88d82f5015d3
turns: 8
tool_calls: 36
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-training-results
---

# what do u think about using qronos in our resaerch and waht are the proactical…

> [!abstract]- Session at a glance
> **8** turns · **36** tool calls · spans **37** min · `claude-opus-5`
>
> **Tools** Bash ×30, WebFetch ×3, WebSearch ×2, ToolSearch ×1

---

## You · 10:49

what do u think about using qronos in our resaerch and waht are the proactical appciations of post aware quantization in pair with QAT, and 4-bit sofmatx

---

## Claude · 10:54

Read the paper, checked what we already have, and logged it. Short version: **worth a conversation, not a port.**

## What Qronos actually is

[arXiv 2505.11695](https://arxiv.org/abs/2505.11695), ICLR 2026. Sequential-rounding PTQ that alternates two steps per weight: **correct** the accumulated error from earlier layers' weight *and activation* quantization, then **diffuse** the residual forward by a least-squares update to the not-yet-quantized weights. Cholesky implementation, composes with Hadamard incoherence processing and scale equalization. Shipped in **Brevitas** (AMD, PyTorch) behind `--qronos`.

Two facts that decide the question for us:

- **Its grid floor is 1.58-bit weight-only.** Tables cover W4/W3/W2 and 1.58-bit, plus W4A4KV4 and W3A3. **W1 is never evaluated.** Llama3/Qwen3 only — no small models, no CNNs, and no QAT interaction anywhere in the paper.
- **Rayan Saab is UCSD Math + HDSI**, Ian Colbert is AMD. This is a paper written down the hall from you.

## My verdict

Not on the critical path. PTQ-to-binary is the exact failure mode BitNet-style native QAT exists to avoid — Qronos's diffusion step works in continuous space, but the final projection onto `{−1,+1}` is too coarse for the correction to buy back what it buys at W2/W1.58. Add the stack mismatch (HGQ2/Keras vs PyTorch/Brevitas) and a code port is the *worst*-value option available. Three better ones, ranked:

**1. Talk to them.** Same campus, and they're a quantization-theory group with an AMD FPGA co-author. Our regime — a 1-bit transformer where the DSP question is settled at the Vivado netlist — is a setting their algorithm has never touched. Cost: one email.

**2. A referee-proof PTQ baseline arm.** "Why not just post-quantize the FP32 model instead of training binary from scratch?" is a question you will get at FastML. Beating the SOTA rounding method answers it far harder than beating RTN. Run Qronos in Brevitas on a PyTorch clone of the tagger **with the alphabet constrained to ±1** so the statement is PTQ-to-binary vs QAT-to-binary; their 1.58-bit numbers stay adjacent evidence, not the arm. Ternary stays off-thesis.

**3. Steal the idea, not the code.** This is the one I'd actually pursue. At 1-bit our weights have no degrees of freedom, but the **15 β-restore affines and the biases do** — and they're already the DSP-carrying part of the design (3,621 of the 4,133 DSPs; softmax is the other 512, [RESEARCH.md §6.2](RESEARCH.md)). A Qronos-style least-squares correction restricted to those affines is a *no-training* repair stage. To be clear about what it's for: it does **not** fix a current problem — export fidelity is AUC-neutral today (Δ ≤ 0.00033 across all five synthesized articles, §6.5). It's the enabler for going *below* the current grids, where the PTQ deltas get large.

## PTQ + QAT paired — you already run the strongest version

The pairing that pays in this project is **PTQ as the cheap screen, QAT as the confirmation**, and the softmax knob is the worked example:

- The 10→4-bit narrowing was implemented on the *export* model only, so GATE1 became a free PTQ probe of exactly what the grid costs: **−0.003968 score-correlation, −1.39 pp argmax** (w1a6-s3 carrier, 4,096 gate jets — not an AUC, and PTQ ≥ QAT cost by construction).
- That said "expensive but not a cliff, worth training." The retrained arm then landed at **0.8701 ± 0.0020 vs the W1A8 control's 0.8712 ± 0.0016** — a −0.0011 drop, one-sided 95% upper bound +0.0035, inside the pre-registered 0.005 bar (§6.3).

PTQ predicted a −1.39 pp argmax hit; QAT recovered it to a −0.0011 AUC drop. That's the whole method in one line, and it's the thing to say out loud at the poster.

Two other pairings worth having in the toolbox: **PTQ-init for QAT** (solve the grids/scales first, fine-tune from there — fewer NRP epochs per arm), and **PTQ-repair after QAT** (the β-affine idea above). The ladder becomes: PTQ probe → affine repair → QAT only if the repair doesn't clear the bar.

## 4-bit softmax

For us this is no longer a proposal — it's the lever that got the design under budget. The retrained 4-bit-grid network is the **first fitting zero-DSP operating point: 1,689,320 CLB LUT = 97.8% of the nominal VU13P, 0 DSP** (§6.3, [hls_r14_fit.md](bnjettag/results/r14/hls_r14_fit.md) row 7), II=48, 240 ns/jet, 1.67 µs, meeting 200 MHz. Mandatory caveats stay glued to it: **Vivado post-`opt_design`, out-of-context on xczu7ev, pre-route**, compared against the nominal VU13P count. It works twice — it shrinks the context-einsum operands *and* it keeps Vivado from inferring DSPs on those products. And because softmax output lives in [0,1], `ap_ufixed<4,0>` gives 16 levels at identical LUT: the binary point is free wiring.

The open question is whether 4 is the floor. Measured: 6-bit 0.8706 ± 0.0017, 4-bit 0.8701 ± 0.0020 — the ladder is nearly flat so far, which is what makes 3-bit tempting and what makes idea (3) interesting: a least-squares affine repair might buy a 3-bit grid without another NRP round.

I've logged the paper in [research-log.md](.claude/memory/research-log.md) with the dates and URLs — no `INDEX.md` note yet, since I've only read the abstract, the HTML v3, and the Brevitas docs. Want me to run a proper dossier on it, or design the ±1-alphabet PTQ baseline arm as a pre-registered experiment?

Sources: [arXiv:2505.11695](https://arxiv.org/abs/2505.11695) · [ICLR 2026 PDF](https://proceedings.iclr.cc/paper_files/paper/2026/file/8d22a09f18d9fc85dcbe6f482e13e1d7-Paper-Conference.pdf) · [Brevitas Qronos docs](https://xilinx.github.io/brevitas/dev/papers/qronos.html) (that exact path 404s today — the API needs checking against the repo branch) · [theory follow-up, arXiv:2508.04853](https://arxiv.org/abs/2508.04853)

---

## You · 10:55

where doe sthe idea of the 4bit grid network come from

---

## Claude · 10:57

It came from our own netlist forensics, not from a paper. The precise moment is the [research-log](.claude/memory/research-log.md) entry of **2026-08-15**, "LUT levers for the NON-matmul 49% of the n8 W1A8 model."

## The setup

Job Alpha had just closed the device-fit question badly: the folded 0-DSP point sat at 112.7% of the VU13P, missing by 220,063 LUT, with every conversion-level lever exhausted by measurement ([decisions.md, 2026-08-19](.claude/memory/decisions.md)). So the question became forensic — where does the non-matmul half of the LUT actually live? That meant per-family attribution of the csynth report rather than the whole-model rollup.

## The decisive observation

It fell out of an experiment we'd already paid for. The **W1A4 activation-ladder arm** narrows every datalane activation 8→4 bits, so it was a free width sweep. Comparing two sibling einsum modules inside the same attention block:

| module | operands | LUT/MAC, A8 → A4 | change |
|---|---|---|---|
| scores einsum | both narrow 8→4 | 63.25 → 27.25 | **−57%** |
| ctx einsum | softmax × V | 111.6 → 104.9 | **−6%** |

The ctx einsum barely moved because `bit_block_*_attn_softmax_t` is `ap_ufixed<10,1,AP_RND_CONV,AP_SAT,0>` in **both** arms (`defines.h:48,102` in each). **The softmax output width does not track `quant.act_bits`.** So at A4 the ctx einsums were 429,568 LUT — 79% of the entire act×act family — pinned by a 10-bit operand that the whole A8→A6→A4 axis had structurally never touched. The log's own words: *"the largest single unexplored non-matmul LUT item."*

Nobody had chosen 10 bits, either. `QSoftmax` has no `oq_conf`; the output type is *derived* by hls4ml's bit_exact pass. It fell out of the converter and stayed there.

Two details fixed the target at 4 with a zero integer bit: the sibling scores module at 4b×4b in the same einsum shape gave a sizing anchor of 27.25 LUT/MAC, and softmax output lives in (0,1], so the integer bit is dead weight — `ap_ufixed<4,0>` buys 16 levels instead of 8 at identical LUT, because the binary point is wiring. The knob turned out to already exist, uncommitted, in [qat.py:383-388](bnjettag/code/hgq2/bnhgq2/qat.py#L383-L388) with default `max(ab, 10)`.

## What the literature contributed: a warning, not the idea

The same scan read four softmax papers and rejected all of them as transfers. I-BERT (integer polynomial exp), Softermax, and NN-LUT all attack the *table* cost — but our exp/inv tables are BRAM-resident at ~0 LUT, and our softmax LUT sits in the max/subtract/multiply/requant datapath, so importing them would trade free BRAM for scarce LUT. Wrong direction.

The one partial transfer was **FQ-ViT (arXiv:2111.13824)**, and only as a caution: 4-bit uniform quantization of post-softmax attention maps collapses DeiT-T to 8.69% top-1, because ~98.8% of ViT-L attention values fall below 1/16. But that skew is a 197-token artifact — mean attention weight 1/197. At N = 8 the mean is 1/8, so the mechanism is far weaker for us by construction. Recorded verdict: *don't assume a narrower softmax output is free; measure it, don't import the number.*

## Then it was measured, and it flipped a closed decision

The project refused to project the saving — explicitly: *"do not quote a projected saving from narrowing the softmax output until it is [measured]."* Good instinct, because a 2-point width power law predicted 60.5 LUT/MAC for the ctx module and the measurement said 104.9 — refuted by 1.7×, so no cost model had standing.

- **BETA-1**, a minimal-diff structure-only build (two lines of `defines.h` changed, nothing else): ctx family −29.6%, whole model −126,928 csynth LUT, then Vivado OOC at **1,694,625 CLB LUT = 98.07% at 0 DSP**. First fit.
- That superseded a *pre-registered closure*. On 2026-08-19 the trained-grid route had been declared closed by measurement (ΔCTX 121,344 < the 223,570 bar). The OOC fit reopened it, because the bar was a csynth projection pushed through another build's ratio while the deciding stage said the point fits.
- **Gamma** then trained the grid: 0.8701 ± 0.0020, **1,689,320 CLB LUT = 97.8% at 0 DSP** ([RESEARCH.md §6.3](RESEARCH.md)).

So the one-line answer: it came from noticing that an already-completed experiment had accidentally left one operand of the biggest remaining LUT family untouched — and the literature's only contribution was telling us not to assume it was free.

---

## You · 10:58

wait what do u call, even the thing that brought or lut count down

---

## Claude · 10:58

Its name in this project is **the softmax grid** — full form, *the attention-softmax output grid*, and the lever is *narrowing* it from 10 bits to 4.

The naming ladder, from most formal to internal shorthand:

| Register | What to say |
|---|---|
| Paper / talk | "narrowing the quantization grid on the attention-softmax output from 10 bits to 4" |
| Field-standard | quantization of the **post-softmax attention map** (FQ-ViT's term) — activation quantization, not weight quantization |
| HLS-level | an **operand width narrowing** on the first operand of the context einsum |
| Internal | "the softmax grid", "the 4-bit softmax grid", "the sm4 knob" |

The concrete object it names is one typedef — `bit_block_{0,1}_attn_softmax_t`, `ap_ufixed<10,1,…>` → `ap_ufixed<4,0,…>` — driven at training time by `quant.softmax_out_bits` / `quant.softmax_out_i`. "Grid" rather than "precision" because what changes is the whole fixed-point lattice: width, binary point, and the rounding/saturation mode together.

The surrounding names, since they show up in the logs: the campaign that designed it was **Job Beta**, described as *grid-narrowing QAT*; the structure-only characterization build was **BETA-1**; the trained model that shipped is **Gamma**, config `r15-gamma-sm4i0-n8-w1a8` (`sm4i0` = softmax grid 4 bits, integer bits 0).

Two things to keep straight when you say it out loud:

1. **It is not W1A4.** W1A4 narrows every datalane activation to 4 bits and costs real AUC (0.8534). Gamma keeps the W1A8 network everywhere and narrows only this one operand. Your study guide already lists "W1A4 and Gamma 4-bit softmax are the same model" as a common confusion.
2. **It is not what got DSPs to zero.** That was a different lever — fabric binding on the β affines and softmax. The softmax grid is the LUT lever; the binding is the DSP lever. The fitting point needed both, in the scoped combination.

---

## You · 11:25

full form, the attention-softmax output grid

where did we get this and show me the raw code

---

## Claude · 11:26

It lives in exactly one place in the graph — the **input quantizer on the first operand of the context einsum** — and then propagates as one typedef into the firmware. Here is the whole chain.

## 1. The object itself — [qat.py:508-531](bnjettag/code/hgq2/bnhgq2/qat.py#L508-L531)

```python
scores = einsum(f"{blk}_attn_scores", "bthe,bshe->bhts", [q, k],
                [stream_iq(), stream_iq()])
...
attn = softmax(f"{blk}_attn_softmax", scores, 1.0 / np.sqrt(E))
attn_iq = _dummy("datalane") if fp32 else \
    QuantizerConfig("kif", "datalane", k0=0, i0=sm_out_i,
                    f0=sm_out_bits - sm_out_i,
                    round_mode="RND_CONV", overflow_mode="SAT",
                    trainable=False, heterogeneous_axis=())
ctx = QEinsum("bhts,bshe->bthe",
              iq_confs=[attn_iq, stream_iq()],
              name=f"{blk}_attn_ctx")([attn, v])
```

`attn_iq` is the grid. `k0=0` (unsigned — probabilities), `i0` integer bits, `f0` fractional bits, `RND_CONV`/`SAT`, `heterogeneous_axis=()` so it's one grid per tensor rather than per element. Note `iq_confs=[attn_iq, stream_iq()]` — the two operands of the context einsum get *different* quantizers, and only the first one is this knob. That asymmetry is the whole story: the second operand (V) is a normal datalane stream that the activation ladder narrows, the first one wasn't.

## 2. The knob, and the line that explains everything — [qat.py:376-388](bnjettag/code/hgq2/bnhgq2/qat.py#L376-L388)

```python
# Softmax OUTPUT grid (Job Beta, 2026-08-19). The ctx-einsum attention operand has
# always been ap_ufixed<max(ab,10),1>; the `max(ab,10)` is exactly why the A8/A6/A4
# ladder never moved this grid (ab in {4,6,8} => max == 10 always). ABSENT =>
# max(ab, 10) => every pre-Beta config is byte/hash-unchanged, for any ab. Set =>
# that exact TOTAL width. `softmax_out_i` is the integer-bit count (default 1 = the
# historical grid); i0=0 is the tighter range for a value bounded in (0,1] and costs
# the same LUTs -- the binary point is a static shift, i.e. wiring, not logic.
_smo = cfg["quant"].get("softmax_out_bits", None)
sm_out_bits = int(_smo) if _smo is not None else max(ab, 10)
sm_out_i = int(cfg["quant"].get("softmax_out_i", 1))
if sm_out_bits - sm_out_i < 1:
    raise ValueError(f"{cfg['name']}: quant.softmax_out_bits={sm_out_bits} leaves "
                     f"< 1 fractional bit at softmax_out_i={sm_out_i}")
```

`max(ab, 10)` with `ab ∈ {4, 6, 8}` is always 10. That single expression is the code-level answer to why W1A8, W1A6 and W1A4 all emit an identical 10-bit softmax operand — and why the ctx einsum only moved −6% across the whole ladder while its sibling moved −57%.

## 3. Setting it — [r15-gamma-sm4i0-n8-w1a8.json](bnjettag/code/hgq2/configs/r15-gamma-sm4i0-n8-w1a8.json)

```json
"quant": {
  "weight": "binary_absmean",
  "act_bits": 8,
  "act_policy": "static_per_tensor_mse_calibrated",
  "calib_n": 8192,
  "act_calib": "trainable",
  "softmax_out_bits": 4,
  "softmax_out_i": 0
}
```

`act_bits` stays 8. This is the file that makes Gamma ≠ W1A4.

## 4. The export-side force — BETA-1's characterization knob, [convert_final.py:659-684](bnjettag/code/hgq2/convert_final.py#L659-L684)

```python
# `force_softmax_out=(bits, i)` overwrites the ctx-einsum attention operand grid on the
# EXPORT model only, AFTER build_export (whose match_attention_to_qat has just copied the
# trained grid in). Two reasons it goes here and not on the QAT model:
#   * a trained checkpoint is loaded whole (load_qat_model), so quant.softmax_out_bits in
#     the config is INERT for an existing checkpoint -- verified 2026-08-19. Forcing must
#     be an explicit assignment or it silently does nothing.
#   * forcing only the export leaves the QAT model as the untouched reference, so GATE1
#     becomes a free post-training-quantization probe of exactly what the narrowing costs,
#     while GATE2 (C-sim vs export) stays bit-exact because both sides carry the narrow grid.
if force_softmax_out is not None:
    _fb, _fi = int(force_softmax_out[0]), int(force_softmax_out[1])
    ...
    for _li in range(A["n_layers"]):
        _q = export_model.get_layer(f"bit_block_{_li}_attn_ctx").iq[0].quantizer
        for _v, _val in ((_q._k, 0), (_q._i, _fi), (_q._f, _fb - _fi)):
            _v.assign(np.full(_v.shape, float(_val), dtype="float32"))
```

`.iq[0]` — index 0, the softmax operand. This is the mechanism behind the PTQ probe I described earlier: it touches the export only, so GATE1 measures the post-training cost of the narrowing while GATE2 stays bit-exact.

## 5. What actually reaches the FPGA

One typedef changes. Gamma's [defines.h:48,102](bnjettag/results/synthesis/runs/ba72a91a/w1a8-s3-r15gamma-sm4i0-pf1scoped/hls_prj_pf1scoped/firmware/defines.h) against a stock W1A8 build:

```c
// stock W1A8 (runs/38a20c62/…-pf2sm2df)
typedef ap_ufixed<10,1,AP_RND_CONV,AP_SAT,0> bit_block_0_attn_softmax_t;

// Gamma sm4i0 (runs/ba72a91a/…-pf1scoped)
typedef ap_ufixed<4,0,AP_RND_CONV,AP_SAT,0>  bit_block_0_attn_softmax_t;
```

Everything else in that block is byte-identical — the exp/inv tables stay `ap_ufixed<12,…>`, the accumulator stays `ap_ufixed<24,7>`. And in `myproject.cpp` that one type does three jobs, which is why the lever pays twice:

```c
123: bit_block_0_attn_softmax_t layer19_out[4*8*8];                    // the buffer
265: nnet::softmax_multidim<bit_block_0_attn_scores_t,
                           bit_block_0_attn_softmax_t, softmax_config19>(...);  // softmax result type
269: nnet::einsum<bit_block_0_attn_softmax_t, bit_block_0_attn_Wv_affine_t,
                 bit_block_0_attn_ctx_t, config24>(layer19_out, layer21_out, layer24_out);  // ctx first operand
```

Line 269 is the one that mattered: `bit_block_0_attn_softmax_t` is literally the first template argument of the context einsum, so narrowing the typedef narrows 256 multiplier operands per block. Lines 189/309/313 are the same three sites in block 1.
