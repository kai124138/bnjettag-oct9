---
title: <ide_opened_file>The user opened the file…
date: 2026-09-02
updated: "2026-09-05T12:32:42"
project: bnjettag-training-results
cwd: /Users/kaiyamaguchi/Downloads/bnjettag-training-results
model: claude-opus-5
git_branch: main
session_id: 6e136540-fb33-45a9-a02f-1c42477f27df
turns: 2
tool_calls: 5
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-training-results
---

# <ide_opened_file>The user opened the file…

> [!abstract]- Session at a glance
> **2** turns · **5** tool calls · spans **1** min · `claude-opus-5`
>
> **Tools** Bash ×5

---

## You · 12:08

<ide_opened_file>The user opened the file /Users/kaiyamaguchi/Downloads/bnjettag-training-results/bnjettag/code/hgq2/configs/r15-gamma-sm4i0-n8-w1a8.json in the IDE. This may or may not be related to the current task.</ide_opened_file>

do we use flash attentionbtw?

---

## Claude · 12:08

No — there's no FlashAttention anywhere in the pipeline, in either the QAT path or the HLS path.

Attention is built explicitly from quantized primitives in both places:

- **Training/QAT** — [qat.py](bnjettag/code/hgq2/bnhgq2/qat.py): `BitQEinsumDense` for Q/K/V/O, `QEinsum` for the two act×act contractions, `QSoftmax(stable=True, input_scaler=1/√E)`.
- **Export/HLS** — [build.py:13-17](bnjettag/code/hgq2/bnhgq2/build.py#L13-L17): the same composition, chosen deliberately over native `QMultiHeadAttention` because MHA "cannot express this model's SubLN-inside-Wo."

The only `MultiHeadAttention` string in the tree is a key-remapping shim in [compat.py:10-11](bnjettag/code/hgq2/bnhgq2/compat.py#L10-L11) for an hls4ml/hgq registration mismatch — not an attention implementation. Grep for `flash`, `sdpa`, `scaled_dot_product`, `xformers` returns nothing.

It also wouldn't buy anything here. FlashAttention is an IO-aware GPU kernel that tiles QKᵀ to avoid writing the N×N score matrix to HBM; our N is 8–64 tokens, so the score matrix is at most 64×64 per head and there's no memory-bandwidth problem to solve. And the FPGA target needs the score matrix materialized explicitly anyway — each intermediate carries its own fixed-point grid (the softmax exp-LUT with 1/√d_head folded in, the calibrated softmax-output grid feeding the ctx einsum), which is exactly the structure a fused flash kernel destroys. hls4ml has no flash backend either.
