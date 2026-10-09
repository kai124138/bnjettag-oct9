# [A22] weight-type request from the Delta campaign (2026-09-27)

Relayed by the orchestrator from the Delta session (`campaigns/2026-09-26-delta/`, its
`delta.json` M047-M050 and `prerequisite_jobs`; `code/PLAN_patches.md` l. 52-54 and 91-92;
reference implementations in `campaigns/2026-09-26-delta/code/patches/`: 0007
weight-scheme-baselines, 0017 ternary-absmean, 0018 hgq-learnable-weights; the patch numbers
were corrected by the Delta session). This is an input to the [A22]
brief, not a decision. The training-batch STUDY defines NB; Delta reuses whatever [A22] ships
and does not fork it.

Every type runs under the [D19]/[A20] activation and softmax quantizers unchanged. Only the
weight branch differs. Each is a labelled baseline or teacher, never the thesis.

1. `quant.weight: "ternary_absmean"` (M047). BitNet b1.58 absmean ternary {-b, 0, +b} with a
   per-tensor scale. It bills 2 bits per weight to native EBOPs (kbi b0 = 2), not log2 3, and has
   its own labelled ternary gate. The binary gate must refuse ternary layers.
2. `quant.weight: "int8_absmax"` (M048, and teacher P-T2). Static int8 with a per-tensor absmax
   scale on all layers, and no learnable weight widths.
3. `quant.weight: "hgq_learnable"` (M049). HGQ kbi learnable weight widths with Sun et al.'s
   transformer values: b0 4, i0 0, SAT_SYM, MonoL1 on b and i. The kbi b/i variables sit with the
   weights. This overlaps the NB arm; if NB's kbi spec differs, Delta adopts NB's spec and marks
   M049 "covered by NB" at 350k.
4. `quant.layer_weight_override: {"input_proj": "int8_absmax"}` (M050). Binary everywhere except
   `input_proj`, which is static int8.
5. `quant.weight: "none"` with the [A20] quantizers kept (teacher P-T1): float weights on A07-N64
   (d32/h4/L1/FFN32, learned PE), with the [D19] activation and softmax quantizers at their
   initial widths. There is no EBOPs pressure (PID target 1e12, β bounds at the minimum). It runs
   2,000 epochs on the Chang recipe, seed 101, with validation-accuracy selection. It differs from
   the training-batch FP32-E ([A25]), which strips the [A20] keys, so it needs the relaxed guard.
   Delta will re-spec P-T1 to follow [A25] instead if training-batch prefers that.

Required behaviour:
- relax the [A20] guard (`qat.py:667-669` at 77f1ca4e) only for these labelled types and for NB's kbi type;
- any other weight type raises;
- EBOPs accounting bills the real weight bits;
- the binary gate covers binary layers only.
