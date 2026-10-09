# C1 methods note: learned per-channel weight scales

Date 2026-10-08. Literature: BiT, BiViT, XNOR-Net. Reading status: the arXiv HTML pages were
read through a fetch tool that returns a model-generated extract, not the raw text. Equations
below are as extracted; equation numbers and sections should be re-checked against the PDF before
anything is quoted outward. Anything marked UNVERIFIED was not obtained.

## 1. Papers

### BiT (Liu et al., arXiv:2205.13016, https://arxiv.org/abs/2205.13016, HTML https://arxiv.org/html/2205.13016)

- Weight binarization (Sec. 3.2): W_B^i = alpha* · Sign(W_R^i − mean(W_R)), with
  alpha* = ||W_R||_1 / n. This is analytic, per-tensor (layer-wise), mean-subtracted. Not learned.
  Gradient: STE; the paper states weights are not gradient-clipped, because a weight outside the
  clip range would get zero gradient and stop learning.
- Activations (Sec. 3.1, Eq. 5-8): two sets. Signed activations: Sign(X), alpha* = ||X||_1/n.
  Non-negative activations (softmax, ReLU): round(Clip(X,0,1)) in {0,1}, alpha* from the entries
  at or above 0.5. alpha* is the l2-optimal analytic scale (Eq. 3-4).
- Elastic binary activation (Sec. 3.3, Eq. 9): X_B = alpha · round(Clip((X − beta)/alpha, 0, 1)).
  alpha and beta are learned (per-layer scalars as extracted; per-tensor vs per-channel not
  confirmed: UNVERIFIED). Initialisation: alpha = alpha* from above, beta = 0.
  Gradients (Eq. 10-11) are piecewise STE: dX_B/dalpha is 0 below beta, (beta−X)/alpha in
  [beta, alpha/2+beta), 1−(X−beta)/alpha in [alpha/2+beta, alpha+beta), and 1 above;
  dX_B/dbeta = −1 in [beta, alpha+beta), else 0.
- Reported effect: the elastic activation is credited with a large GLUE gain (extract says 15.7 %
  over baseline; the exact comparison and conditions UNVERIFIED). Multi-distillation (Sec. 4,
  Alg. 1; W32A32 → W1A2 → W1A1) cuts the GLUE gap to the full-precision model from 20.7 to 10.4
  points (5.9 with augmentation). Attention after softmax is binarized to {0,1} (Table 6).
- Relevance: BiT's weight scale is NOT learned. Only the activation scale/threshold is. BiT is
  therefore evidence for learned activation scales (a different candidate) and for distillation
  (C2), not for C1.

### BiViT (He et al., arXiv:2211.07091, https://arxiv.org/abs/2211.07091, HTML https://arxiv.org/html/2211.07091)

- Base (Sec. 3.1, Eq. 1-3): x_hat = Sign(x), x ≈ alpha · x_hat, alpha = ||x||_1 / n.
- Parameterized Weight Scales, PWS (Sec. 3.3.2): the ordinary scale (Eq. 3) is replaced by a
  learnable parameter "optimized in conjunction with other network parameters via backward
  propagation". Channel-wise ("channel-wise scaling factors can be regarded as the importance of
  each channel"; Fig. 6 shows variation across channels in NesT-T). It multiplies the sign
  output, so no new operation at inference beyond the usual scale.
  Initialisation: not stated in Sec. 3.3.2 (a natural choice is the analytic absmean; UNVERIFIED
  whether the paper does so). Gradient detail: not stated beyond ordinary backprop; the sign
  itself needs an STE (details UNVERIFIED).
- Reported effect: PWS +4.2 % in attention modules and +1.3 % in MLPs, NesT-T on TinyImageNet.
  Setup (Sec. 4.1): Adam, lr 5e-4, 300 epochs (150 per stage with two-stage training), cosine
  schedule with 5-epoch warmup; TinyImageNet, ImageNet; DeiT, Swin, NesT. Ablation conditions
  (which other components were on) UNVERIFIED.
- Other components: Softmax-aware binarization of attention to {0,1} (Sec. 3.2, Eq. 7-13) with
  threshold T = 0.25 · max(a_s), softmax-aware backward; Cross-layer binarization, two-stage
  training (Sec. 3.3.1). These are separate from C1.
- Caveat: image models of far larger size and training length than this tagger; the PWS gain
  is a few percent and was measured in an ablation of that paper only.

### XNOR-Net (Rastegari et al., arXiv:1603.05279, https://arxiv.org/abs/1603.05279)

Full text not obtained (abstract page only; PDF did not render through the tool): UNVERIFIED.
From memory, not verified here: Binary-Weight-Networks approximate each filter W ≈ alpha·B with
B = sign(W) and alpha = ||W||_1 / n, computed per output filter. BiT/BiViT's Eq. 3 is this
formula applied per tensor (BiT) or replaced by a learned channel scale (BiViT).

## 2. Lab's current binarizer

`campaigns/2026-10-08-discovery-350k/code/bnhgq2/qat.py`:
- `bitnet_binary_ste(w, eps)` lines 45-67. alpha = mean(w) over the entire kernel (line 61),
  wc = w − alpha, beta = mean(|wc|) + 1e-6 (line 63), a single scalar per kernel. q = +1 if
  wc >= 0 else −1 (line 65, never 0). ws = wc / stop_gradient(beta); wq = ws + stop_gradient(q − ws)
  (lines 64, 66); returns wq · beta (line 67). Forward value in {−beta, +beta}. Backward:
  (I − 1/n) plus a q · dbeta/dw term; beta is analytic, not a parameter.
- `BitQEinsumDense` (lines 74-91) and `BitQDense` (lines 95-110) call it on `self._kernel`:
  einsum or matmul with the binarized kernel, then bias (line 84 / 103), activation. The input
  quantizer `iq` is applied before the matmul. The 1-bit KBI `kq_conf` is kept only so EBOPs and
  hls4ml report 1-bit weights (docstring lines 14-16).
- Export re-binarizes the latent with `binarize.py`, same math, to emit {−beta, +beta}
  (docstring lines 17-21). Any new scale must be mirrored there.

So: per-tensor, analytic, mean-subtracted absmean (BiT form), fixed, STE. The same form as BiT's
weight rule; BiViT's PWS departs from it by making the scale a trained, per-channel parameter.

## 3. Implementation options in HGQ2 terms

All options keep weights in {−1,+1} times a scale, with the scale applied after the binary
contraction (output-channel axis), so the matmul stays additions and subtractions.

- Option A (recommended): a new trainable weight `s` of shape (out_channels,) (for einsum
  kernels, the output axes of the equation) in `BitQEinsumDense`/`BitQDense`. Forward: y =
  (x · sign_ste(w)) · s, with sign_ste the existing STE without the beta factor, then bias.
  Initialise s = per-channel absmean of centered latent (equivalently beta broadcast; start
  identical to the current model, so the first-step output is unchanged). Gradient to s is the
  ordinary product rule; gradient to w stays STE. Add a positivity or floor constraint on s
  (e.g. s = softplus or abs + eps) to avoid sign flips that would make the {−1,+1} claim
  ambiguous.
- Option B: per-channel analytic absmean (XNOR style), not learned. Cheap control: separates
  the effect of per-channel resolution from the effect of learning.
- Option C: keep the per-tensor beta and learn a per-channel multiplier m initialised to 1.
  Equivalent to A in function; easier to compare because m = 1 reproduces the baseline exactly.
- Inference cost: one multiply per output channel by a constant (or, if merged, into the next
  layer's input quantizer scale or the bias path where it is a power of two). Nothing is free
  if the scale is arbitrary-precision: it needs a fixed-point constant at a stated width, and
  that product is a new multiplier counted by resource/EBOPs. Per PROPOSAL §6, EBOPs and
  certification must count it: the scale vector must be quantized to a stated bit width (the
  constant's bits times the accumulator width), added to the EBOPs total by the normal
  computation, and shown in the csynth path. The EBOPs computation is a protected component,
  so the counting has to come through a layer the existing tracing already sees (a separate
  scaling quantized layer) and not through an edit of that code. If the scale cannot be
  folded or counted, the candidate does not pass.
- Folding: a per-channel scale before a LayerNorm or the model's PSubLN (subln.py) may be
  absorbed or cancelled; this must be checked per layer, because layers followed by a
  scale-invariant normalization gain nothing. Relevant to where C1 can help at all.

## 4. Why it could address the failure, and what would argue against it

Mechanism (hypothesis, not established): with a single per-tensor beta, every output channel has
the same dynamic range after the binary matmul, so the controller that narrows the activation
quantizers at 350k EBOPs must pick one range to fit channels of unequal magnitude. Narrow
widths then clip the large channels or flush the small ones to zero. A per-channel scale lets
the network equalize channel magnitudes before the quantizer, so a narrower grid loses less.
BiViT's Fig. 6 reports channel-scale variation in a trained model, which is the premise.

Observations that would argue against it:
- Baseline per-channel output magnitudes (pre-quantizer) are already near uniform, so there is
  nothing for the scale to equalize.
- The accuracy drop coincides with attention entropy approaching uniform while activation widths
  stay wide (PROPOSAL §6 falsifier). Then the loss is in the attention/softmax path, not weight
  scaling.
- Layers followed by a normalization that cancels the scale (section 3, folding).
- The learned scales stay at their initial values within seed spread, or C1 does not beat the
  baseline at 5M.
- A gain only from option C against option B would show learning matters; a gain from B alone
  would show resolution only. No gain from either closes the idea.

## 5. Recommended C1 specification outline

- Files that may change: `code/bnhgq2/qat.py` (new layer variants or an option on
  `BitQEinsumDense`/`BitQDense`; config flag `weight_scale: per_tensor|per_channel_learned`,
  default per_tensor = byte-identical baseline), `binarize.py` (export mirror), the config
  generator for the candidate, and a new test file. Nothing else.
- Protected: `eval/`, cache/split/data code, EBOPs computation and tracing, validation labels,
  existing tests (PROPOSAL §6), and the baseline default path.
- Behaviour: Option A or C as above; s shape per output channel; init so the model is
  functionally identical to the baseline at step 0; s constrained positive; s excluded from
  weight decay; s quantized to a fixed-point type of stated width in the forward pass so what
  is trained is what is counted; the scale appears as a counted multiplier in EBOPs.
- Tests (CPU, local): (1) flag off gives identical outputs and parameter count to the baseline;
  (2) at init, flag on gives outputs equal to baseline within 1e-6; (3) effective weights before
  the scale are exactly {−1,+1}, no zeros; (4) gradient reaches both latent w and s, finite;
  (5) EBOPs with the flag on exceeds baseline by the expected scale-multiplier count, computed
  independently; (6) export re-binarization plus scale reproduces trained predictions
  (correlation about 1.0, as the existing fidelity gate); (7) save/load round-trip.
- Controls (design, for the campaign): option B and option C alongside A, same seeds.
- Acceptance: all tests pass; scale cost counted and reported with bit width; at 350k EBOPs the
  validation accuracy gap to the baseline reported with seeds and an interval, labelled split
  and n (inside the spread is flat); no quotable number from the local kernel or home PC;
  certification on mulder before any claim. The EBOPs budget compared must include the scales.
- Stop: if folding shows the scale cancels in most layers, or the scale cannot be counted
  without touching protected code, report and do not implement.
