# THEORY — what Delta is testing

physics-researcher, 2026-09-26 campaign (written 2026-09-27). Organises the ~100 method cards
in `research/<family>.md` by **mechanism**, so each Delta arm tests a named cause of lost
accuracy rather than adding one more trick to a pile. Families: **B** binarization, **R** recipe,
**Q** activation widths / EBOPs, **A** architecture, **P** inputs and data.

## 0. Labels, scope, and what the anchor actually does

Every statement carries one label:
- **[source: …]**: a primary source I fetched or a repo file I read (path:line).
- **[derived: …]**: arithmetic or code-reading on a named file of ours. No training and no
  result: it is a consequence of a rule, and the rule's file is named.
- **[conjecture]**: my reasoning. Each one is a hypothesis for Delta to test, not a finding.

No effect size below comes from memory. Every published number carries its paper, table or
figure, dataset and model. **Transfer warning, applies to every source.** None of the fetched
sources is a ~13k-parameter, 3-feature, norm-free transformer under an EBOPs budget. Most are
ImageNet CNNs (BNN literature) or BERT/LLMs (binary transformers), and several binarize
activations as well as weights. Take their numbers as the direction of an effect only.

**Anchor facts the theory relies on** (as implemented in `published/bnjettag-code/hgq2`; the
anchor's code state is the publication-tree lineage, so ml-engineer confirms these against
`inventory/code-surface.md` before a card depends on them):
- Binarizer: `bitnet_binary_ste` (`qat.py:43-65`). α = mean(W), W_c = W − α, β = mean|W_c|,
  q = +1 if W_c ≥ 0 else −1, effective weight q·β. **One β per tensor**, mean-centred (so
  each tensor is balanced in sign by construction). Backward: identity STE on W_c/sg(β), with
  **no latent clip** and no |w| ≤ 1 gradient cut-off [source: qat.py:43-65].
- The effective scale β is a function of the latent magnitudes, so **layer output scale and
  latent "inertia" are one quantity** [derived: qat.py:61, β = mean|W_c|].
- Norm-free graph: every β is restored by an explicit affine after its own matmul
  [source: binarize.py:14-19]. Biases are float [source: qat.py:405-406]. Learned PE folds
  into `input_proj`'s bias table [source: qat.py:112-118].
- `input_proj` is itself a binary layer, fan-in 3 [source: qat.py:474-475, `dense_einsum` →
  `BitQEinsumDense` when `binary_absmean`].
- Activation widths are learned per channel from an 8-bit init. The softmax output is fixed
  at 10 bits [source: campaigns/2026-09-26-training-batch/STUDY.md, Arms preamble].

**EBOPs counting rule, verified.** On `bnjettag/results/ebops-n8-20260910/analysis/3bynw2ra/
artifact/activation_widths.jsonl` epoch 0 (N=8, d32, FFN64, all widths 8), every per-layer
entry equals its shape formula, and the entries sum to the logged total (1,739,182)
[derived: `python3 -c` reading line 1, comparing `per_layer[k]` with the shape formula
for input_proj, Wq, scores, ctx, fc1, fc2, head_fc1, head_fc2 of block 0, all equal; run 2026-09-27]. Weight × activation layers cost N·fan_in·fan_out·b_act·1.
`scores` costs N·N·d·b_q·b_k. `ctx` costs N·N·d·10·b_V (the 10 is the fixed softmax output).
Softmax has its own term, which I did not decompose. The check was at uniform 8-bit widths;
the per-channel form (a sum over input channels) is HGQ Eq. 11 applied, not separately checked. This matches HGQ's definition,
EBOPs = Σ_mult b_i·b_j + Σ_add max(b_k, b_l) [source: Sun et al., HGQ, arXiv:2405.00645v3
§3.3 Eq. 11, https://arxiv.org/abs/2405.00645].

## 1. Where accuracy goes when weights become ±1

### M1 — Capacity per parameter, and the fan-in-3 first layer
- In high dimension, binarization keeps a vector's direction: the angle between a random
  vector and its sign vector tends to arccos √(2/π) ≈ 37° (the extracted text reads "arccos
  2/π ≈ 37°"; the √ was lost in PDF extraction, and 37° fixes it as √(2/π)), and weight·activation dot products
  stay highly correlated. The correlation is **much weaker in the first layer**
  [source: Anderson & Berg, arXiv:1705.07199 (2017) §"Angle Preservation" and Fig. 3,
  https://arxiv.org/abs/1705.07199].
- Our first layer has fan-in 3 (pt, etarel, phirel). A ±1 row over 3 inputs has 2³ = 8 sign
  patterns, 4 up to a global sign. With one per-tensor β, `input_proj`'s 32 output channels
  can therefore point in at most 8 input directions, all of equal gain. They can differ only
  through the float bias (which carries the PE) [derived: combinatorics + qat.py].
- There is no nonlinearity between `input_proj` and Wq/Wk/Wv, so the 8-direction embedding
  composes with the next ±1 layer into small-integer effective coefficients. The per-position
  bias (PE) is the only per-channel freedom. Rank ≤ 3 holds for an FP `input_proj` too: the
  binary-specific loss is **discreteness** of directions and gains, not rank [derived + conjecture].
- Hidden layers have fan-in 32, so 2³² patterns per row: there the angle argument applies and
  the loss is the ≈37° distortion per row, not a lack of expressible directions [conjecture].
- Binary networks buy back capacity with width. The EBOPs budget removes width (M7) [conjecture].
- **Observables.** The number of distinct rows of sign(input_proj kernel) on a checkpoint:
  exists, reading a `.keras` file, no code needed. A labelled non-binary-`input_proj`
  baseline arm, with its gap to the anchor at the same seeds: needs a config knob.
- **Families.** P (more or derived input features raise fan-in), B (per-channel power-of-two
  gain on `input_proj`), A (wider d). An FP or multi-bit first layer is **baseline only**,
  because a layer with more than two weight values breaks the thesis.

### M2 — Gradient mismatch (STE bias)
- The STE is biased and low-variance [source: Bengio, Léonard, Courville, arXiv:1308.3432
  (2013), https://arxiv.org/abs/1308.3432]. A properly chosen STE gives a coarse gradient
  whose expectation correlates positively with the population gradient. A poor choice gives
  instability near some minima [source: Yin et al., ICLR 2019, arXiv:1903.05662,
  https://arxiv.org/abs/1903.05662]. Their analysis is for *activation* quantization, so its
  transfer to our weight STE is by analogy.
- BiBERT names "optimization direction mismatch" in the backward pass as one of two causes
  of the fully binarized BERT's drop [source: Qin et al., ICLR 2022, arXiv:2203.06390 §1, §3.3,
  https://arxiv.org/abs/2203.06390]. IR-Net treats the backward loss with an annealed sign
  approximation (EDE) [source: Qin et al., arXiv:1909.10788 (2019),
  https://arxiv.org/abs/1909.10788].
- Ours is an identity STE with no clip. It has no "dead weight" zone and gives no
  distance-to-threshold information [derived: qat.py:62-64].
- **Observables.** (a) The latent-vs-binary evaluation gap: evaluate a checkpoint with the
  latent float kernels in place of q·β. Helwegen et al. report that latent-weight evaluation
  is *not* better than binary [source: arXiv:1906.02107 §3]. Needs a small eval script.
  (b) The cosine between the STE gradient and the latent-model gradient on one batch. Needs code.
- **Families.** B (clipped or annealed STE, stochastic sign), R (LR magnitude).

### M3 — Latent-weight flips, inertia and oscillation
- Latent magnitude is **inertia**: the larger |w̃|, the stronger the gradient signal needed to
  flip. The optimizer mostly changes inertia, not binary weights. Clipping caps inertia.
  Lowering the LR late in training raises effective inertia [source: Helwegen et al., NeurIPS
  2019, arXiv:1906.02107 §3, https://arxiv.org/abs/1906.02107].
- Their Theorem 1 (the binary trajectory is invariant to LR if the init is rescaled) requires
  a pseudo-gradient independent of |w̃| [source: ibid. §3]. **Ours violates it**: β = mean|W_c|
  scales the forward pass, so inertia and output gain move together [derived: qat.py:61].
  Growing latents in a long run make a layer both louder and stiffer [conjecture].
- Weight decay on latents trades stability for dependence on the init. Flip-flop (FF) ratio
  rises with weight decay. Liu et al. Table 1 (ImageNet top-1, Adam, their ResNet-18-based binary network):
  weight decay 1e-5 → FF 2.33e-3, 61.73 %; 5e-6 → 1.62e-3, 61.89 %; 0 → 2.86e-4, 61.49 %;
  two-step (5e-6 then 0) → 4.50e-4, 63.23 %. Adam revives "dead" weights better than SGD
  [source: Liu et al., ICML 2021, arXiv:2106.11309 §3.2-3.3, Table 1,
  https://arxiv.org/abs/2106.11309].
- In QAT, latent weights oscillate around a decision threshold. A lower LR reduces the
  amplitude but not the frequency. The harm comes through corrupted BatchNorm statistics and
  training noise. Remedies: dampening and iterative freezing [source: Nagel et al., ICML 2022,
  arXiv:2203.11086 §2-4, https://arxiv.org/abs/2203.11086]. We have no BatchNorm, so their
  main harm path is absent. What remains is noise, plus checkpoint-to-checkpoint jitter that
  the per-epoch selection rule can exploit or suffer from [conjecture].
- Our threshold is the tensor mean α, which itself moves as weights update. That is a
  second, collective source of flips that the literature above does not treat [derived: qat.py:59-63].
- **Observables** (none are logged today; they need code, which goes to ml-engineer):
  per-layer FF ratio per epoch (sign snapshot, 12,788 parameters, negligible cost); C2I ratio
  (final sign vs init sign); the latent |w̃|/β histogram; the fraction of latents within one
  Adam step of threshold; the per-layer β trajectory.
- **Families.** R (optimizer, weight decay, LR, restarts, Bop), B (latent clip, dampening,
  freezing, β decoupled from latent magnitude).

### M4 — Loss of scale information
- A real-valued scale beside binary weights recovers much of the accuracy lost to
  binarization (XNOR-Net: one α per filter = mean|W|) [source: Rastegari et al., ECCV 2016,
  arXiv:1603.05279, https://arxiv.org/abs/1603.05279; literature note
  `literature/qat-binary-nn-foundations/1603.05279_xnor_net.md`]. Data-driven per-channel
  rescaling and learnable shifts (RSign, RPReLU) help further [source: Martinez et al.,
  ICLR 2020, arXiv:2003.11535 §4.3, https://arxiv.org/abs/2003.11535; Liu et al., ReActNet,
  ECCV 2020, arXiv:2003.03488, https://arxiv.org/abs/2003.03488].
- We have **one β per tensor**, and no LayerNorm γ to supply a per-channel gain. BitNet's
  SubLN placement gives it one; our norm-free choice removed it [derived: binarize.py:6-19].
  Per-channel output magnitude is therefore set by the input statistics and the ±1 pattern
  alone [conjecture on consequence].
- Learned activation widths set *precision and range*, not *gain*. They cannot stand in for a
  missing per-channel scale [derived: a quantizer is value-preserving within its range].
- **Observables.** The per-channel pre-activation std of each binary layer on validation
  jets; the dead-ReLU channel fraction; the least-squares per-channel α on a probe batch
  against the per-tensor β (a large spread means scale information is being lost). A
  forward-pass script is needed.
- **Families.** B (per-channel α, restricted to powers of two or CSD ≤ 2 digits, see §3),
  A (per-channel gain / RPReLU-type shift), Q.

### M5 — Attention-specific failure
- **Temperature coupling [derived + conjecture].** The logit scale is β_q·β_k·(Q·K of ±1
  projections)/√d_h. Per-head temperature can only move through two per-tensor β's that are
  also inertia (M3). Attention entropy is lower-bounded by a quantity that falls
  exponentially with the spectral norm of the logits. Low entropy goes with instability
  [source: Zhai et al., ICML 2023, arXiv:2303.06296, https://arxiv.org/abs/2303.06296].
  Large β's therefore risk collapse to peaked attention, and small β's give flat attention.
- **Information degradation [source, partial transfer].** BiBERT: binarizing the softmax
  output drives the entropy of the binarized attention to 0. Bi-Attention restores it by
  maximizing entropy [source: arXiv:2203.06390 §3.2]. BiBERT is fully binarized (weights,
  activations, embeddings). Our softmax output stays at 10 bits, so its argument applies only
  as the budget drives the Q/K/V widths toward 1-0 bits (M7).
- **Rank collapse [source, weak transfer].** Pure attention loses rank doubly exponentially
  with depth. Skip connections and MLPs prevent it [source: Dong, Cordonnier, Loukas,
  arXiv:2103.03404 (2021), https://arxiv.org/abs/2103.03404]. We have depth 1, so this
  mechanism is weak for the anchor and matters only for L ≥ 2 A-cards [conjecture].
- **Budget-induced collapse [source + derived].** Sun et al.'s MHA at N=64 and 350k
  "consistently collaps[ed] … turning it into a Deep Set" with **HGQ (non-binary) weights**
  [source: arXiv:2510.24784 §3, quoted in docs/chang-vs-bnjettag.md]. So collapse at this
  budget is not a binary-weight effect. §M7 shows why the counting rule prices attention out
  first. Attributing any collapse of ours to binary weights needs the matched non-binary arm
  that the anchor STUDY pre-registers as a follow-up.
- **Measurement hazard [derived + conjecture].** The pT gate [D7] turns gated constituents
  into one identical standardized vector, with no mask [source: STUDY.md [A3], lines 531-533].
  Entropy "as a fraction of log 64" is then inflated by the padding fraction per jet, not by
  collapse. The diagnostic should be reported against log(n_valid) per jet, or with gated keys
  masked in the diagnostic pass only. With `pos_enc none` (arms E, F) gated tokens are exact
  duplicates. With GAP and no mask, the pooled mean also encodes the count of gated
  constituents, i.e. multiplicity [conjecture: a feature, not only a bug].
- **Observables.** The pre-registered three (Q/K 0-bit fraction, V 0-bit fraction, entropy)
  from `activation_widths.jsonl` and a softmax tap; the n_valid-normalised entropy (needs
  code); per-head logit std; an **attention-ablation delta**, i.e. validation accuracy with
  the attention output replaced by the mean over V. It tests Deep-Set collapse independently
  of widths. Needs a 20-line eval script.
- **Families.** A (Linformer/low-rank, fewer heads, no PE, a Deep-Sets control), Q (softmax
  output bits, Q/K width floors, a per-layer penalty weight), B (a learned temperature scalar
  for Q/K), P (masking gated tokens).

### M6 — Interaction with the norm-free design
- BitNet places LayerNorm (SubLN) to stabilize 1-bit training [source: Wang et al.,
  arXiv:2310.11453, https://arxiv.org/abs/2310.11453; binarize.py:6-12 records our SubLN fold
  plan]. σReparam trains transformers without LayerNorm by controlling spectral norms
  [source: arXiv:2303.06296]. BNN accuracy is sensitive to shifts in the activation
  distribution [source: ReActNet, arXiv:2003.03488 abstract].
- Norm-free and absmean: latent drift (M3) changes β, hence the residual-stream range, hence
  what the learned integer bits must cover. Either the quantizers saturate (SAT clips on
  purpose; see binarize.py:16-19 on the R14 gate-1 failure), or the integer bits grow and
  EBOPs rises [derived: code path; the sign of the net effect is a conjecture].
- **Observables.** The correlation of the per-layer β trajectory with the integer-bit
  trajectory `i` in `activation_widths.jsonl` (exists for the widths; β needs logging); the
  saturation fraction at each quantizer (needs code).
- **Families.** A (a norm layer, which costs LUT and possibly DSP, see §3), B (β as a separate
  power-of-two parameter decoupled from |w̃|), R.

### M7 — Activation-width learning under an EBOPs penalty
- With weights pinned at 1 bit, every weight × activation term is MACs·b_act. The β penalty
  can lower cost **only by narrowing or zeroing activation channels**. A 0-bit channel deletes
  a whole row of MACs [derived: the counting rule in §0]. HGQ weights can instead be pruned
  or narrowed per parameter (0-bit weights are "effectively pruned") [source: arXiv:2405.00645
  §3.3]. Binary therefore pays for cost reduction with **structured width loss**. HGQ pays
  with unstructured sparsity. This is the sharpest binary-specific mechanism in Delta
  [conjecture on its size].
- At N=64 and A07 with every width at 8 bits, the formula gives scores + ctx = 18.87M of the
  24,816,782 traced initial EBOPs (76 %), and weight × activation layers ≈ 3.2M [derived: shape
  arithmetic; the total from campaigns/2026-09-23-confirmation/n64-full-preflight-result.json;
  softmax is the undecomposed remainder]. At 350k: ctx alone is 1,310,720·mean(b_V), and the
  six d×d layers at a 1-bit mean input width are 6·65,536 = 393,216 > 350,000
  [derived]. **These are reference points, not the floor. The floor is [A7] and unmeasured.**
  They say only that a feasible 350k binary A07 at N=64 must zero a large share of channels
  somewhere, and that attention is the cheapest place to find the EBOPs.
- No binary N=64 run has reached 350k. The A07 screen arm plateaued near 4.6M in 50 epochs at
  LR 2e-4 with β still rising [source: review/STUDY_investigation_350k.md; W&B, single seed,
  validation, unverified: context only].
- **Observables.** Per-layer, per-channel 0-bit fractions and the EBOPs split (act × act,
  weight × act, softmax) against epoch, from `activation_widths.jsonl` (exists); the effective
  residual width (channels with b > 0) (derivable from it).
- **Families.** Q (width floors, per-group penalty weights, the β schedule, softmax bits),
  A (Linformer / fewer heads to cut the N² terms; a smaller d with wider bits), P (fewer
  constituents, which cuts N²).

## 2. Why the Sun et al. recipe might matter more for binary than for HGQ weights

- **Steps, not epochs [derived].** At 558,000 train jets, batch 2,790 is 200 steps/epoch, so
  7,000 epochs is 1.40M steps. R (batch 256, about 2,180 steps/epoch, 1,000 epochs) is about
  2.18M steps [numbers from STUDY.md Budget]. The Sun et al. recipe takes **fewer** optimizer
  steps than R. It sees 7× the samples, with a 150× higher peak LR (3e-3 vs 2e-5). Any A − R
  gain is therefore about LR magnitude, batch noise and restarts, not "more updates".
- **Adam defaults [source + conjecture].** Adam's second moment revives dead weights and
  copes with a rugged BNN landscape better than SGD [source: arXiv:2106.11309 §3.2]. Under
  Adam the per-step latent move is ≈ LR-scaled regardless of gradient size, so the ratio
  LR/|w̃| sets the flip propensity [conjecture, grounded in Helwegen §3]. At 3e-3 against the
  latent init scale (init scheme per `inventory/code-surface.md`), flips stay possible throughout training. At 2e-5 far fewer
  signs may move away from their init [conjecture; test: C2I ratio of A vs R].
- **Weight decay (arm D) [source + derived].** Weight decay raises the FF ratio and lowers
  the dependence on init [source: arXiv:2106.11309 Table 1]. With absmean it also **shrinks β
  and so every layer's output gain** [derived: β = mean|W_c|]. A − D therefore tests M3 and M6
  together. The confirming observable, independent of accuracy, is a higher FF ratio and a
  smaller β trajectory in D.
- **Warm restarts [source + conjecture].** SGDR improves anytime performance [source:
  Loshchilov & Hutter, ICLR 2017, arXiv:1608.03983, https://arxiv.org/abs/1608.03983]. For a
  BNN, each restart is a step change in LR relative to accumulated inertia, so it should give
  a burst of flips (exploration). The low-LR end of each cycle re-freezes signs (exploitation)
  [conjecture, via Helwegen §3 and Nagel §2: the amplitude scales with LR]. A restart also
  perturbs the PID β controller and the widths [conjecture]. **Observable:** the FF ratio
  against epoch, with a spike at each 500-epoch boundary; the within-cycle position of the
  best feasible checkpoint (predicted: late in a cycle); whether feasibility is lost after
  each restart.
- **Large batch and flat minima [source + conjecture].** Large batches tend toward sharp
  minima [source: Keskar et al., ICLR 2017, arXiv:1609.04836, https://arxiv.org/abs/1609.04836].
  The binary loss landscape is steeper than the ternary or FP one [source: Bai et al.,
  BinaryBERT, arXiv:2012.15701 v2 2021 §2.2, Fig. 2-3, https://arxiv.org/abs/2012.15701].
  For a BNN, less gradient noise also means fewer spurious flips (a lower FF ratio). The two
  effects pull in opposite directions, so the sign of the batch effect is open [conjecture].
- **Long schedule for widths [conjecture].** The EBOPs descent itself needs time (M7: the
  screen was still descending at epoch 50). With HGQ weights the budget can be met by weight
  pruning early on. Binary must reorganize channel usage, so it plausibly needs a longer
  schedule than HGQ.

## 3. The cost side

- **What EBOPs counts** [source: arXiv:2405.00645v3 §3.3 Eq. 11]: products Σ b_i·b_j and
  explicit additions Σ max(b_k, b_l). Control logic and FIFOs are excluded. The empirical
  relations are "EBOPs ≈ LUT + 55·DSP" on hls4ml for UltraScale+, and LUT ≈ exp(0.985·log EBOPs)
  on da4ml [source: ibid., as fetched; verify the exact wording before citing it in outward
  text].
- **What EBOPs omits for ±1 [derived + source].** A ±1 MAC costs b_act in EBOPs, which is the
  width of one add or subtract. The adder tree's width grows by about log₂(fan-in) bits
  (5 bits at fan-in 32) and is not charged. Equal EBOPs is not equal LUT
  [source: STUDY.md [L2]].
- **Measured on our flow** (archived hls4ml/Vitis csynth of the R14 n8 model; mechanism
  transfers, numbers do not) [source: .claude/memory/research-log.md, 2026-08-15 entry]:
  requantization cost tracks saturated integer bits; the per-tensor β restore mapped to LUT
  only when its CSD/NAF form had ≤ 2 nonzero digits, and 14 of 15 took DSPs; softmax tables
  sit in BRAM and the ctx einsum is pinned by the 10-bit softmax output; the ReLU parser
  fall-through costs a width-independent compare. Distributed arithmetic was **negative** on
  ±1 matrices (LUT and FF both up) [source: experiment-log.md 2026-07-22, summarized in
  docs/chang-vs-bnjettag.md action 2].
- **HGQ-LUT, the rival route to 0 DSP.** It turns each neuron into trained logic LUTs, with
  per-element zero-bit pruning, and has a LUT-count surrogate beside EBOPs. It **deletes
  operations** where we make each one cheaper. It has no transformer or attention support, and
  its cost model has no term that rewards ±1 weights over a pruned 2-bit weight [source: Sun et
  al., arXiv:2604.22293, as summarized in `literature/hls4ml-fpga-triggers/2604.22293_hgq_lut.md`].
  It is not a lever inside a binary attention block. A LUT-Dense *head* (low fan-in) is the only
  crossing point, and it needs Alkaid, not hls4ml, so it is an A-family card of the
  "different toolchain" class [conjecture].
- **A neighbour's measurement.** In one HLS flow on VU13P, ternary BitNet beat binary on AUC,
  LUT and latency [source: Sloot, FastML 2026, as logged in research-log.md 2026-09-01].
  Binary is not automatically the cheaper point.

Consequences for Delta:

| class | examples | EBOPs | FPGA reality |
| --- | --- | --- | --- |
| training-only | recipe, KD, STE variants, Bop, latent clip, restarts, progressive binarization that ends at ±1 | unchanged | free [derived] |
| EBOPs-visible | activation widths, N, d, heads, the act × act terms | charged | roughly tracks LUT [source: HGQ] |
| EBOPs-invisible, LUT-real | accumulator growth, bias adds, requant integer bits, extra affines, norm layers, PE add | not charged | real LUT; possible DSP [source: research-log 2026-08-15] |
| DSP hazard | per-channel scales with arbitrary constants | not charged | DSP unless each scale is a power of two / CSD ≤ 2 [source: same] |
| thesis-breaking | ternary, a multi-bit first layer, per-weight scales | – | baseline only (BRIEF rule) |

How HGQ2 counts a *ternary* layer's zeros (as pruned 0-bit weights, or as 1-bit) is not in
the §3.3 text I fetched [open, §6].

## 4. Mechanism → method → prediction matrix

The cells give the lever, then the predicted sign on **validation top-1 at fixed EBOPs target**
(+ helps, − hurts, 0 neutral, ± budget-dependent), then the diagnostic that confirms the
mechanism **without looking at accuracy**. Every sign is **[conjecture]**; that is what Delta
tests. "Exists" means the diagnostic is in current logs; "code" means it needs ml-engineer work.

| mechanism | B binarization | R recipe | Q widths / EBOPs | A architecture | P inputs |
| --- | --- | --- | --- | --- | --- |
| M1 capacity / fan-in 3 | power-of-two per-channel gain on input_proj: +; distinct sign rows ↑ (checkpoint, exists) | 0 | width floor on the input_proj output: +; 0-bit fraction ↓ (exists) | wider d at fixed EBOPs: ±; effective width (exists) | derived features (log pT, ΔR, pT fraction), fan-in > 3: +; distinct rows ↑, latent-vs-binary gap ↓ (code) |
| M2 STE bias | clipped or annealed STE: + if the instability is in M2; STE/latent gradient cosine ↑ (code) | lower final LR: +; latent-vs-binary gap ↓ (code) | 0 | 0 | 0 |
| M3 flips / inertia | latent clip or dampening or freezing: +; FF ratio ↓ late in training (code) | Adam without decay vs decay (A vs D): + for A; FF ↓, β stable (code); Bop: ±; restarts: + (FF spikes at boundaries, code) | 0 | 0 | 0 |
| M4 scale loss | per-channel α (power of two): +; per-channel std spread explained (code) | 0 | per-channel widths already on; 0 | RPReLU/shift: +; dead-ReLU fraction ↓ (code) | 0 |
| M5 attention | learned Q/K temperature scalar: +; entropy/log n_valid off 0 and 1 (code) | KD with an attention-map term: +; attention-ablation delta ↑ (code) | Q/K/V width floors, or exempting attention from β: ± (+ at 5M, possibly − at 350k because it forces cuts elsewhere); 0-bit fractions (exists) | Linformer / fewer heads / Deep-Sets control: + at 350k; EBOPs split (exists) | masking gated keys: +; entropy normalization (code) |
| M6 norm-free drift | β decoupled from latent magnitude: +; β-vs-`i` correlation ↓ (code) | no weight decay: + (β not shrunk) | 0 | a norm layer: + accuracy, − LUT (not EBOPs) | 0 |
| M7 width vs budget | 0 | long schedule: +; EBOPs reaches target (exists) | per-group penalty weights, width floors, β schedule: ±; 0-bit maps (exists) | cut N² terms: + at 350k, 0 at 5M | fewer constituents: + at 350k if attention survives; EBOPs split (exists) |

## 5. Interactions: which combinations theory says to cross

**Synergy or redundancy (cross these in small factorials, 2×2 at matched seeds):**
1. **KD × progressive binarization.** Two-step training (binarize activations first, then
   weights) and a sequence of teacher-student pairs close the gap more than either alone
   [source: Martinez et al., arXiv:2003.11535 §§3-4; Liu et al., arXiv:2106.11309 Table 1
   two-step rows]. BiT distills successively through lower-precision teachers [source: Liu
   et al., NeurIPS 2022, arXiv:2205.13016, https://arxiv.org/abs/2205.13016]. BinaryBERT
   initializes binary from a half-sized ternary model by ternary weight splitting
   [source: arXiv:2012.15701 Fig. 4]. For us the
   intermediate stage must be FP/HGQ → binary with the final layer at ±1. Prediction:
   synergy, and a larger one at the low budget [conjecture].
2. **Per-channel scale × learned activation widths.** A power-of-two per-channel gain is free
   in hardware (a shift absorbed into the next quantizer's binary point) and changes
   *relative* channel contributions, which widths cannot do [derived]. The widths then have to
   re-adapt to the new ranges. Prediction: synergy, but the order of training matters. Cross
   them [conjecture].
3. **Restarts × latent-weight treatments (clip, weight decay, Bop).** Restarts, weight decay
   and clipping all lower effective inertia (§2, M3), so they should be **partly redundant**.
   Bop has no LR, so cosine restarts do not act on it unless γ or τ is scheduled
   [source: arXiv:1906.02107 §4; conjecture on the redundancy]. Cross restarts × {clip, none}
   and Adam × Bop.
4. **EBOPs target × attention levers.** At 5M attention is affordable; at 350k it is priced out
   (M7). Every A/Q attention card should run at two targets, or its sign is uninterpretable
   [derived + conjecture].
5. **Gate × PE × masking.** Duplicated gated tokens (P) interact with PE removal (A) and with
   the entropy diagnostic. Masking changes both accuracy and the diagnostic [conjecture].
6. **Input features × first-layer scale (P × B, M1).** Both enlarge the set of directions
   `input_proj` can express. They are probably redundant at the margin; cross them.

**Expected additive (main effects suffice; no factorial):** training-only B/R levers that act on
M2/M3 against P levers that act on M1; KD (logit-level) against architecture size; data-order
and split seeds against everything [conjecture]. If a pair flagged additive shows a paired
interaction outside its interval in any wave, promote it to a factorial.

## 6. Open theoretical questions for the deep-research follow-up

1. *Is 350k at N=64 reachable by binary A07 with a nonzero attention branch?* Settle it with
   the [A7] static floor, then the canary's per-channel width trajectory. If the floor needs
   V at 0 bits, every M5 card at 350k is moot.
2. *Is the Sun et al. collapse purely budget geometry?* Settle it with a matched HGQ-weight
   arm on our pipeline at 350k and 5M, with the three attention diagnostics plus the ablation
   delta.
3. *Is `input_proj` (fan-in 3) the binding capacity loss?* Settle it with the distinct-row
   count on trained checkpoints and a labelled non-binary-input_proj baseline at matched
   seeds.
4. *Does the R recipe train signs at all?* Settle it with C2I and FF ratio for A vs R (sign
   snapshots). If C2I ≈ 1 under R, the recipe gap is M3, not capacity.
5. *How does HGQ2 count ternary zeros, and what is the LUT per EBOP for a ±1 layer at fan-in
   32?* Settle it with a trace of a ternary layer, plus single-layer csynth → post-route on
   `mulder`. This decides whether iso-EBOPs comparisons flatter binary, and by how much
   ([L2]).
6. *Does a restart schedule beat one cosine of equal total steps for binary?* Settle it with
   one matched arm; the observable is the FF spikes against the best-checkpoint position.
7. *Does the ordering at the trigger operating point match top-1 and AUC?* For every Delta
   comparison, add the per-class signal efficiency at fixed mistag from the ROC-test `.npz`.
   BitParT's AUC moved by 0.0006 while background rejection fell by about 15 % [source:
   literature/jet-tagging-transformers/2508.07431_bitpart.md, Top Tagging, ParT].
8. *Literature gaps to fill:* a weights-only binary *small* transformer (ViT-scale or smaller)
   with multi-bit activations; Bop or flip-aware optimizers on transformers; sharpness-aware
   training for BNNs; whether BinaryBERT's 2-bit → 1-bit weight cliff (Fig. 1: ≈3.8 pt on
   MRPC, ≈0.9 pt on MNLI-m, BERT, 8-bit activations) has a small-model analogue. The last
   one threatens the binary framing if it transfers.

## Log lines to append

(orchestrator appends to `.claude/memory/research-log.md`, newest on top)

- 2026-09-26 — THEORY for Delta (`campaigns/2026-09-26-delta/research/THEORY.md`).
  Primary sources fetched and read in the relevant sections: Helwegen et al. 2019 Bop/inertia
  https://arxiv.org/abs/1906.02107; Liu et al. 2021 Adam/weight decay/FF ratio
  https://arxiv.org/abs/2106.11309; Nagel et al. 2022 QAT oscillations
  https://arxiv.org/abs/2203.11086; Anderson & Berg 2017 binary geometry
  https://arxiv.org/abs/1705.07199; BiBERT https://arxiv.org/abs/2203.06390; BinaryBERT
  https://arxiv.org/abs/2012.15701; Martinez et al. real-to-binary
  https://arxiv.org/abs/2003.11535. Abstract level only: Yin et al. STE
  https://arxiv.org/abs/1903.05662, IR-Net https://arxiv.org/abs/1909.10788, BiT
  https://arxiv.org/abs/2205.13016, ReActNet https://arxiv.org/abs/2003.03488, Zhai et al.
  entropy collapse https://arxiv.org/abs/2303.06296, Dong et al. rank collapse
  https://arxiv.org/abs/2103.03404, SGDR https://arxiv.org/abs/1608.03983, Keskar et al.
  https://arxiv.org/abs/1609.04836. Transfer: all are ImageNet CNNs or BERT/LLMs; none is
  a small norm-free transformer on 3-feature jets or under EBOPs. Direction only.
- 2026-09-26 — HGQ arXiv:2405.00645v3 §3.3 Eq. 11 fetched (closes the INDEX "known gap" in
  part): EBOPs = Σ b_i·b_j + Σ max(b_k, b_l), accumulators not discussed, 0-bit = pruned.
  https://arxiv.org/abs/2405.00645. Our per-layer counting rule verified on
  `bnjettag/results/ebops-n8-20260910/analysis/3bynw2ra/artifact/activation_widths.jsonl`
  epoch 0 (every shape formula exact; the sum equals the logged 1,739,182). A literature note
  for HGQ is still missing.
- 2026-09-26 — Derived, flag for the record: binary weights pinned at 1 bit leave the EBOPs
  penalty only structured (channel) pruning. At N=64 A07, scores + ctx are 76 % of the traced
  initial 24.8M EBOPs, and six d×d layers at a 1-bit mean input width already cost 393,216 >
  350k. Reference points, not a floor ([A7] stays unmeasured). With the fan-in-3 binary
  `input_proj` and one β, only 8 input directions are expressible. The attention-entropy
  diagnostic needs log(n_valid) normalization under the unmasked pT gate.
