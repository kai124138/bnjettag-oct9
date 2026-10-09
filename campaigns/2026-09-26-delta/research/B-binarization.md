# Family B — Binarization and latent-weight optimization

Written 2026-09-26 for Delta. Anchor = A07-N64 (`campaigns/2026-09-26-training-batch/STUDY.md`):
d32/h4/L1/FFN32, learned PE, `binary_absmean`, learned activation widths from 8-bit init, BetaPID
to 350k EBOPs, norm-free graph (arch.norm='none'), 90/10 split, val-AUC selection. Every card is a
delta from that arm's weight-binarization scheme unless stated otherwise.

**Current scheme, read from source, not memory.** `publication/code/hgq2/bnhgq2/qat.py`
(`bitnet_binary_ste`) and `publication/code/hgq2/bnhgq2/binarize.py` (`absmean_binarize`), both
per-tensor:
```
alpha = mean(W)                      # centered, NOT XNOR-Net/BitNet's uncentered mean(|W|)
wc = W - alpha
beta = mean(|wc|) + 1e-6
q = where(wc >= 0, +1, -1)           # strict bipolar sign, never 0 — hardware has no zero state
ws = wc / stop_gradient(beta)        # bounded backward (avoids 1/beta blow-up at beta->eps)
wq = ws + stop_gradient(q - ws)      # STE, forward = q
effective weight = wq * beta         # in {-beta, +beta}
```
The 2026-08-08 research-log entry already flags the module docstring's "replicates BitNet exactly"
as overstated: BitNet/XNOR-Net use uncentered `mean(|W|)`; ours centers first. This means our
current scheme already does the zero-mean half of what IR-Net's Libra-PB proposes (B06) — the
delta a Libra-PB card would add is the *standardization* (divide by std, not just recenter) and
the power-of-two-rounded scale, not the centering itself. STE is clipped-identity with a bounded
backward via `stop_gradient(beta)` in the denominator (not a plain hard-tanh clip on ±1) — this is
a specific, already-hardened choice (LEDGER 2026-07-07, fixed the A4 NaN), so B04/B05/B08 below are
deltas from *this* STE, not from vanilla BinaryConnect.

β-fold hazard, from RESEARCH.md §6 (verified silicon, not re-derived): the norm-free graph carries
15 explicit β-restore affines; scoping fabric binding to only the DSP-carrying ops still leaves
Vivado demanding 4,096 DSPs (§6.4), and solution-wide fabric binding removes them at a cost of
+705k–759k csynth LUT for shedding 3,621 DSPs (≈195–210 LUT/DSP, §6.4). Any card that turns a
per-tensor scalar β into a per-channel or non-power-of-two vector multiplies that LUT/DSP hazard
by (number of channels); this is stated per card below as "worse", "same", or "better" than that
baseline.

---

### B01 — binary_absmean (current, per-tensor centered absmean)
**Mechanism.** As above: per-tensor centered absmean forward with strict bipolar sign, bounded STE
backward via `stop_gradient(beta)`.
**Why it could matter for binary weights here.** This *is* the anchor's scheme; every other card
is scored against it.
**Primary source.** Wang et al., "BitNet: Scaling 1-bit Transformers for Large Language Models,"
arXiv:2310.11453 (2023). Note: `literature/bitnet-1bit-ternary/2310.11453_bitnet_scaling_1bit_transformers.md`.
Our implementation departs from it (centered, not centered-free; see above).
**Published effect.** Not applicable — this is our own code, not a literature number. BitNet's own
number does not transfer (LLM scale, different architecture; see that dossier).
**Knob or code change.** None — already the anchor.
**Hazards.** Two weight values per layer, exactly. β is a per-tensor scalar; folds per RESEARCH.md
§6 fold table (`binarize.py` EXPLICIT_SCALE/BIAS_FOLD/SCORE_FOLD/LN_KILLED — all "explicit" in the
norm-free graph). This is the reference hazard point (15 affines, 3,621 DSP if unbound, 0 DSP + LUT
premium if solution-wide bound).
**Tried here?** Yes — it is the anchor (A07-N64).
**Combines with.** Every other card in this family is a delta from it.

### B02 — Uncentered per-tensor absmean (BitNet/XNOR-Net convention)
**Mechanism.** Drop the `alpha = mean(W)` centering step: `beta = mean(|W|)`, `q = sign(W)`. This
is what the `binarize.py` docstring claims to replicate but does not.
**Why it could matter for binary weights here.** A one-line ablation of the centering choice
already flagged as a documentation/implementation gap (2026-08-08 log). Tests whether centering
is buying anything at N=64 scale, where per-tensor weight mean may be closer to zero than at LLM
scale (fewer, smaller matrices).
**Primary source.** Rastegari et al., "XNOR-Net," arXiv:1603.05279 (2016); Wang et al., BitNet,
arXiv:2310.11453. Notes: `literature/qat-binary-nn-foundations/1603.05279_xnor_net.md`,
`literature/bitnet-1bit-ternary/2310.11453_bitnet_scaling_1bit_transformers.md`.
**Published effect.** No prior number for this specific ablation — BitNet's own reported numbers
are at LLM scale (billions of params, language modeling loss) and do not transfer to a 3-feature,
N=64-constituent tagger at ~350k EBOPs.
**Knob or code change.** `bitnet_binary_ste`/`absmean_binarize`: delete the `alpha` line. ~3 lines
in `qat.py` and `binarize.py` each; a boolean flag `center: bool` is the clean version, ~10 lines.
**Hazards.** Same as B01 exactly — one fewer subtraction, same {−β,+β} output, same fold class,
same DSP/LUT hazard. Zero deployment delta.
**Tried here?** No — leave to `inventory/tried-already.md`; not found in the two logs read for
this card.
**Combines with.** Any STE variant (B04–B08); orthogonal axis (scale convention vs gradient rule).

### B03 — Per-channel / learned scale (XNOR-Net++)
**Mechanism.** Replace the single per-tensor β with a per-output-channel (or fused weight×activation)
scale, learned by backprop rather than computed analytically from `mean(|W|)`.
**Why it could matter for binary weights here.** Could recover accuracy lost to forcing one scalar
to fit an entire weight matrix, but every one of our matrices is already small (d32/h4/FFN32) —
the per-tensor absmean may already be a good fit; the ablation is cheap to state, expensive to
deploy.
**Primary source.** Bulat & Tzimiropoulos, "XNOR-Net++: Improved Binary Neural Networks," BMVC 2019,
arXiv:1909.13863. Accessed 2026-09-26. No note in `literature/INDEX.md` — gap.
**Published effect.** Abstract only (not table-verified in this session): scale factors learned
discriminatively "significantly more accurate" than analytically-computed XNOR-Net scales, on
ImageNet with binary weights+activations. No number carried without opening the PDF table.
**Knob or code change.** `bitnet_binary_ste` would need a per-channel `beta` (shape (out_dim,)
instead of scalar) as a trainable variable, decoupled from `mean(|wc|)`; touches `qat.py`
(~15–20 lines: new trainable weight, backward through it) and every fold-class entry in
`binarize.py` (β is no longer a Python float).
**Hazards.** This is the one that breaks the cheap fold. `SCORE_FOLD` (Wq/Wk) currently relies on
a single β_q·β_k scalar joining the 1/√d softmax scale (per-tensor, one multiply); a per-channel
β_q vector times a per-channel β_k vector is no longer one scalar the softmax scale can absorb —
it becomes a per-head-dimension rescale that must be applied before or fused into a per-channel
quantizer, i.e., more multipliers, not fewer. On `EXPLICIT_SCALE` layers (input_proj, Wo, fc2,
head_fc2) a per-channel β becomes a per-column affine after the accumulator: a vector multiply per
output column instead of one scalar — additional LUT/DSP proportional to out_dim, worse than B01's
fold-table entry. Weight values remain exactly ±1 (binary constraint holds); only the scale
multiplies.
**Tried here?** No.
**Combines with.** B06 (Libra-PB's standardization is compatible with staying per-tensor, so B03
and B06 are alternatives, not additive, unless the per-channel and power-of-two ideas are merged).
**Testable prediction (A07-N64, 350k EBOPs).** Val-AUC direction: neutral-to-slightly-up (more
scale freedom on tiny matrices with few output channels may not move accuracy much, since B01
already fits d32/FFN32 matrices well); EBOPs unaffected (b_w still 1) but the *fold cost* — not
captured by EBOPs — goes up, so a naive read of EBOPs-vs-AUC would look free when the hardware
cost is not.

### B04 — Clipped-identity STE / hard-tanh (canonical BNN backward)
**Mechanism.** Backward gradient passes through only where `|w| <= 1` (`d sign/dw ≈ 1_{|w|<=1}`),
zero elsewhere — the original Courbariaux/Bengio backward, as opposed to our bounded
`stop_gradient(beta)`-normalized backward.
**Why it could matter for binary weights here.** It is the textbook baseline our STE was
*hardened away from* (LEDGER 2026-07-07: qkeras's `wc/beta` backward blew up at `beta -> eps` and
caused the A4 NaN). A clipped-identity variant sidesteps the 1/beta explosion differently (by
clipping the latent range instead of normalizing by beta) — worth a card because it is the
default in most public BNN code and a plausible fallback if the beta-normalized STE ever
regresses.
**Primary source.** Hubara et al., "Binarized Neural Networks," NeurIPS 2016, arXiv:1602.02830;
STE origin: Bengio, Léonard & Courville, arXiv:1308.3432. Notes:
`literature/qat-binary-nn-foundations/1602.02830_binarized_neural_networks.md`,
`literature/qat-binary-nn-foundations/1308.3432_straight_through_estimator.md`.
**Published effect.** No number transfers — BNN's reported numbers are ImageNet/CIFAR CNNs with
both weights and activations binary (XNOR+popcount inference), not this architecture or dataset.
**Knob or code change.** In `bitnet_binary_ste`, replace `ws = wc / stop_gradient(beta)` +
`wq = ws + stop_gradient(q - ws)` with `wq_grad = clip(wc, -1, 1)` and
`wq = wq_grad + stop_gradient(q*beta - wq_grad)`. ~5 lines in `qat.py`.
**Hazards.** None beyond B01 — same forward, same fold table, same DSP/LUT story. Purely a
backward-pass change; zero deployment delta.
**Tried here?** No — but the *reason not to* (the A4 NaN) is already on file (2026-08-08 log,
LEDGER 2026-07-07); a card revisiting it should read that ledger entry first.
**Combines with.** Any scale scheme (B01–B03); mutually exclusive with B05/B06/B08 (they replace
the same backward slot).
**Testable prediction.** Val-AUC direction: neutral or down at A4/A6 activation widths specifically
(the failure mode this was hardened against was an activation-width regime, not N=64/W1A8 at A8);
at the anchor's activation width, direction is unclear — flag as "needs the A4 ablation, not just
N64-A8," since the known failure was at A4.

### B05 — Bi-Real ApproxSign (piecewise-quadratic backward)
**Mechanism.** Replace the backward indicator with a piecewise-quadratic function that more
tightly approximates `d(sign)/dw` near zero than clipped-identity, plus (in the original paper)
an identity shortcut connecting pre-sign activations across blocks — the shortcut is an
activation-path change, not part of this card's weight-binarization scope.
**Why it could matter for binary weights here.** A closer backward approximation than clipped-
identity could reduce gradient mismatch without touching forward values or β at all.
**Primary source.** Liu et al., "Bi-Real Net," ECCV 2018, arXiv:1808.00278. Accessed 2026-09-26.
No note in `literature/INDEX.md` — gap.
**Published effect.** ImageNet top-1 with ResNet-18-family 1-bit CNN (both weights and
activations binary); exact table number not opened in this session (abstract states qualitative
gain over vanilla STE, no percentage). Flag as "no prior number carried."
**Knob or code change.** Swap the backward slot in `bitnet_binary_ste` for the ApproxSign
piecewise-quadratic derivative in place of the current bounded-STE gradient; ~10 lines, same
insertion point as B04.
**Hazards.** None beyond B01 — backward-only, forward and β unchanged, zero deployment delta.
**Tried here?** No.
**Combines with.** Mutually exclusive with B04/B06/B08 (same backward slot); combines with B03/B06
(forward-side scale changes) since it only touches gradients.
**Testable prediction.** Val-AUC direction: neutral-to-up, smaller effect size than in Bi-Real's
CNN setting because our activations are already 8-bit (not binary) — ApproxSign was designed for
a fully-binary (W1A1) regime; at W1A8 the forward/backward mismatch it targets is a weight-only,
milder problem.

### B06 — IR-Net Libra-PB (balanced + standardized weight binarization)
**Mechanism.** Two changes to the forward quantizer versus plain absmean: (1) explicitly maximize
information entropy by balancing (zero-mean, already partly true of B01's centering) *and*
standardizing (divide by std, not just recenter) the latent weights before applying `sign`; (2) a
scale factor constrained to a power of two, computed once per layer, so the hardware multiply
becomes a bit-shift.
**Why it could matter for binary weights here.** Directly targets the exact question our
`binarize.py` docstring got wrong: what "balanced" binarization should mean. The power-of-two
scale claim is the one candidate in this family that the paper states *improves* the hardware
cost of the scale factor rather than just being a training trick.
**Primary source.** Qin et al., "Forward and Backward Information Retention for Accurate Binary
Neural Networks" (IR-Net), CVPR 2020, arXiv:1909.10788. Accessed 2026-09-26. No note in
`literature/INDEX.md` — gap.
**Published effect.** Abstract only (not table-verified this session): "consistently outperforms
state-of-the-art quantization methods" on CIFAR-10/ImageNet; no percentage carried without
opening the PDF table — flag as pending if this card is promoted.
**Knob or code change.** `bitnet_binary_ste`: add `wc = wc / (std(wc) + eps)` after centering
before computing `beta`/`sign`; round `beta` (or a derived scale) to nearest power of two via
`2**round(log2(beta))`, straight-through on the rounding. ~10 lines in `qat.py`, mirrored in
`binarize.py`'s export path (must match exactly, per the existing "export == train" invariant).
**Hazards.** The power-of-two constraint is the good case for the fold table: a shift is free in
fixed point and folds into any downstream quantizer's binary point without a multiplier — this is
the one candidate that could make the `SCORE_FOLD`/`EXPLICIT_SCALE` affines *cheaper* than B01's
current scalar multiply, if hls4ml/HGQ2's fixed-point quantizer treats a shift specially (unverified
in our stack; state as a hypothesis, not a fact). Weight values remain exactly {−1,+1}; the standard-
ization only changes which threshold the sign is taken around, still per-tensor scalar, so no new
multiplier count versus B01 on that axis.
**Tried here?** No.
**Combines with.** B07 (EDE) is IR-Net's own backward half — natural pair, published together.
**Testable prediction.** Val-AUC direction: up, smallest for the standardization half (our
matrices are small enough that mean(|wc|) is probably already a reasonable per-tensor scale);
if power-of-two rounding is implemented, expect a small EBOPs-neutral LUT/DSP win at export that
val-AUC alone will not show — must be checked at synthesis, not from the `.npz`.

### B07 — IR-Net EDE (Error Decay Estimator, progressive sign approximation)
**Mechanism.** Backward half of IR-Net: replace the fixed STE with a temperature-scheduled
function that starts close to identity (wide-support, low bias) early in training and anneals
toward the true sign derivative (narrow-support, low variance) by the end — same family as
soft-sign/tanh annealing.
**Why it could matter for binary weights here.** Addresses a real tension at 7,000 epochs with
cosine restarts (the Sun et al. recipe, per BRIEF.md): each restart re-heats the LR, and a fixed
narrow STE may give unstable gradients right after a restart, while a fixed wide STE never sharpens
enough. A schedule tied to (or restarted with) the cosine LR schedule is a natural pairing worth
flagging even though IR-Net itself did not test cosine restarts.
**Primary source.** Qin et al., IR-Net, arXiv:1909.10788 (as B06). Same primary source, backward
half.
**Published effect.** Same as B06 — abstract-level claim only, no table number carried.
**Knob or code change.** Add a training-step-dependent temperature `t` to the backward function
(e.g., `d(sign)/dw ≈ min(2 - 2*|t*w|, 2/t)` per the paper's schedule) computed from
`optimizer.iterations` or a Keras callback; ~15 lines in `qat.py` plus a callback wiring the
schedule to the epoch count, ideally to each cosine-restart period rather than global step.
**Hazards.** None beyond B01 — backward/training-loop only, forward and β unchanged, zero
deployment delta.
**Tried here?** No.
**Combines with.** B06 (published together, IR-Net's full recipe); interacts with the 500-epoch
cosine-restart schedule (BRIEF.md's recipe) — if adopted, the anneal should probably be restarted
per cosine cycle rather than run once over 7,000 epochs, which is a design choice this card cannot
resolve without a run.
**Testable prediction.** Val-AUC direction: up if restarted with the cosine schedule, roughly flat
or noisy if annealed once over the full 7,000 epochs and cosine restarts fight the anneal's
assumption of monotonically sharpening gradients.

### B08 — ReSTE (Rectified/relaxed STE, power-function backward)
**Mechanism.** Replaces the backward with a power function `f(w) = sign(w)|w|^p` whose exponent
`p` is annealed over training, framed as trading estimation error against gradient stability
rather than picking a single fixed compromise (as clipped-identity or ApproxSign do).
**Why it could matter for binary weights here.** A more recent (2023), theoretically-motivated
alternative to B04/B05/B07's backward choices; the paper's framing (error vs. stability trade-off)
is the most direct hypothesis-generator for *why* our bounded `stop_gradient(beta)` STE works —
worth reading in full before proposing a code change, not just citing.
**Primary source.** Wu et al., "Estimator Meets Equilibrium Perspective: A Rectified Straight
Through Estimator for Binary Neural Networks Training" (ReSTE), ICCV 2023, arXiv:2308.06689.
Accessed 2026-09-26. No note in `literature/INDEX.md` — gap.
**Published effect.** Abstract states "surpasses state-of-the-art methods" on CIFAR-10/ImageNet
"without any auxiliary modules or losses"; no percentage carried without opening the PDF table.
**Knob or code change.** Replace the backward slot with the power-function gradient and an
annealing schedule for `p`; ~10–15 lines, same insertion point as B04/B05/B07.
**Hazards.** None beyond B01 — backward-only, zero deployment delta.
**Tried here?** No.
**Combines with.** Mutually exclusive with B04/B05/B06's EDE half (same backward slot); could be
compared head-to-head against B07 as "which backward schedule wins here" since both are power/
temperature-annealed variants on the same idea.
**Testable prediction.** Val-AUC direction: up relative to B04 (published to beat older STE
variants at CNN scale); magnitude untested at transformer/N=64/EBOPs-budget scale, so treat the
direction claim as weak.

### B09 — Stochastic binarization (probabilistic sign)
**Mechanism.** Sample the binarized weight as `+1` with probability `sigmoid(w)` (or a hard-
sigmoid of the normalized latent) and `-1` otherwise, instead of a deterministic sign; forward is
now noisy per training step, and a straight-through or REINFORCE-style backward is still needed.
**Why it could matter for binary weights here.** BinaryConnect's own ablation found stochastic
binarization sometimes helps small/noisy-gradient regimes and sometimes doesn't beat deterministic
sign; at N=64 with 7,000 epochs, extra per-step noise could either regularize against the
attention-collapse failure mode already on record (2026-08 log, MHA disqualified by its own §3) or
destabilize the 500-epoch cosine restarts.
**Primary source.** Courbariaux, Bengio & David, "BinaryConnect," NeurIPS 2015, arXiv:1511.00363.
Note: `literature/qat-binary-nn-foundations/1511.00363_binaryconnect.md`.
**Published effect.** BinaryConnect's own paper reports stochastic binarization performs
comparably to or slightly better than deterministic on small CNN/MLP benchmarks (Torch7/MNIST-
scale); no number transfers to this dataset or model family.
**Knob or code change.** `bitnet_binary_ste`: replace `q = where(wc >= 0, 1.0, -1.0)` with a
Bernoulli sample of `hard_sigmoid(wc/beta)`, gradient still via the existing STE path; ~8 lines,
plus a training/inference-mode switch (deterministic sign at export, since `binarize.py`'s export
path must stay deterministic — a stochastic export would fail the "export == train" fidelity gate
the codebase already enforces).
**Hazards.** Deployment path is unaffected (export is always deterministic sign, per the existing
`binarize.py`), so the binary constraint and fold table are identical to B01 at inference. The only
risk is a training/export mismatch if the stochastic and deterministic forward diverge in a way the
fidelity gate (corr ~ 1.0, per `qat.py` docstring) does not tolerate.
**Tried here?** No.
**Combines with.** Any STE backward variant (B04–B08); orthogonal to scale scheme (B01–B03, B06).
**Testable prediction.** Val-AUC direction: uncertain sign, plausibly higher variance across seeds
than B01 — this is the one card whose main testable claim is about seed-to-seed spread, not the
mean, so it needs multiple seeds to read at all (per CLAUDE.md's "never report a gap without seeds
and an interval").

### B10 — Bop (Binary Optimizer, latent-weight inertia)
**Mechanism.** Replaces Adam/SGD-on-latent-weights with an optimizer purpose-built for binary
weights: maintain an exponential moving average of the gradient per weight, and flip the sign of
the *binary* weight (not a latent float) once the EMA magnitude crosses a threshold. The paper's
framing: latent weights don't represent "how binary a weight nearly is," they provide training
inertia, and Bop makes that inertia explicit instead of implicit in a float.
**Why it could matter for binary weights here.** Directly addresses a mechanism we already carry
as an unexamined assumption: our current training keeps a full-precision latent kernel and derives
{−1,+1} from it every forward pass (Adam updates the latent). Bop removes the latent weight
entirely, which is a training-loop-level change to how "the same" weight moves, not a forward/
backward-pass tweak — the largest architectural delta in this family.
**Primary source.** Helwegen, Widdicombe, Geiger, Liu, Cheng & Nusselder, "Latent Weights Do Not
Exist: Rethinking Binarized Neural Network Optimization," NeurIPS 2019, arXiv:1906.02107.
Accessed 2026-09-26. No note in `literature/INDEX.md` — gap.
**Published effect.** Demonstrated on CIFAR-10 and ImageNet with weight-and-activation-binarized
CNNs (Bi-Real-Net-style); no percentage carried without opening the PDF table this session.
**Knob or code change.** This is not a quantizer edit — it replaces the optimizer entirely for the
binary-weight variables, keeping Adam (or whatever is used) for everything else (β is a float,
biases are float, activation quantizer parameters are float). Requires a custom Keras optimizer
or per-variable optimizer routing; a rough size estimate is 60–100 lines (a new optimizer class
plus a `qat.py`/`build.py` hook to tag which variables are Bop-controlled) — the largest code
change in this family, not a "smallest change."
**Hazards.** None on the deployment side — the exported weight is still exactly ±1, β unchanged,
fold table identical to B01. All the risk is on the training side (a wrong threshold schedule can
under- or over-flip).
**Tried here?** No.
**Combines with.** Every forward/backward card (B01–B09) is compatible in principle since Bop
replaces the *optimizer*, not the quantizer, but combining it with B03 (per-channel learned β,
itself a float trained by the ordinary optimizer) requires routing two different optimizers over
disjoint variable sets — a real engineering cost, not just a config flag.
**Testable prediction.** Val-AUC direction: uncertain without a run; Bop was designed and validated
for W1A1 (both weights and activations binary) — our activations stay at 8 (then 6, then 4) bits,
so the paper's motivating regime (activation-binarization-induced gradient noise) is only partly
present here. Advisor's caution stands: this is the weakest transfer claim in the set, ranked
accordingly.

### B11 — BinaryBERT ternary-weight-splitting (two-stage ternary→binary)
**Mechanism.** Train a half-width ternary {−1,0,+1} network to convergence first (cheaper
optimization landscape, per the paper's loss-landscape analysis), then algebraically split each
ternary weight into two binary weights via the TWS operator so the doubled-width binary network's
initial forward pass exactly reproduces the ternary network's output; fine-tune from there.
**Why it could matter for binary weights here.** This is the clearest "progressive/two-stage"
candidate in the brief's list. It directly trades parameter count for optimization ease: our
current d32/FFN32 anchor could, in principle, start as a d16/FFN16 ternary network and split to
d32/FFN32 binary — but that changes the architecture shape mid-training, which interacts with
EBOPs accounting and the BetaPID controller (both are keyed to a fixed graph).
**Primary source.** Bai et al., "BinaryBERT: Pushing the Limit of BERT Quantization," ACL 2021,
arXiv:2012.15701. Accessed 2026-09-26. No note in `literature/INDEX.md` — gap.
**Published effect.** GLUE/SQuAD, "only a slight performance drop compared with the full-precision
model while being 24x smaller" (abstract); no GLUE-average number carried without opening Table 2/3
of the ACL paper. Model is BERT-base (110M params), a scale nothing like ours (~thousands of
params) — flagged per the brief's transfer-check requirement even before any number is quoted.
**Knob or code change.** Not a quantizer edit: requires (1) a ternary training config at half
width, (2) the TWS splitting operator (duplicate each ternary weight row/column, redistribute
values per the paper's closed form) applied once at a checkpoint boundary, (3) resuming training
with double-width binary layers. Estimate 80–120 lines across `build.py` (graph surgery) and a new
`tws.py` — the largest single-card code change in this family besides B10.
**Hazards.** The intermediate stage is ternary (three weight values), a labelled deviation from
the binary thesis during training only; the *deployed* end state is binary ±1, so the thesis claim
is not violated at export, only mid-training. Must be stated explicitly in any STUDY that adopts
this, per CLAUDE.md ("ternary is a baseline, not the thesis").
**Tried here?** No.
**Combines with.** B12 (BiT) shares the "start from something less-binarized, refine down" idea;
mutually exclusive with a from-scratch binary run at the same width, since TWS defines its own
architecture doubling.
**Testable prediction.** Val-AUC direction: up relative to from-scratch binary at the *same final
width*, if the ternary-to-binary landscape argument transfers down from BERT scale to N=64/d32 —
but the argument was made at 110M params where loss landscapes are empirically flatter; the
direction claim is speculative at our parameter count, so flag as the weakest-evidence prediction
alongside B10.

### B12 — BiT elastic binarization + multi-step distillation
**Mechanism.** Three combined ideas: (1) a "two-set" binarization scheme separating which weight
values map to which of two learned levels rather than a fixed ±β; (2) an elastic binary activation
function with learned clipping/shift parameters (activation-side, adjacent to B13's RSign/RPReLU);
(3) successively distilling a higher-precision teacher into a lower-precision student in stages
(e.g., FP32 → ternary → binary) rather than training binary from scratch or in one ternary→binary
split.
**Why it could matter for binary weights here.** The distillation-staged idea is the most directly
applicable piece: our own model has no distillation step at all currently. It is also the piece
least entangled with BERT-specific architecture, so the transfer risk is lower than for the
two-set/elastic-activation pieces, which were tuned for BERT's embedding table and LayerNorm-heavy
graph — we run norm-free.
**Primary source.** Liu et al., "BiT: Robustly Binarized Multi-distilled Transformer," ICLR 2023,
arXiv:2205.13016. Accessed 2026-09-26. No note in `literature/INDEX.md` — gap.
**Published effect.** GLUE benchmark, binarized transformer "approaching a full-precision BERT
baseline... within as little as 5.9%" (abstract wording, not a table number); model is BERT-base
scale — flagged as a scale mismatch before any number is used. No table number carried this
session.
**Knob or code change.** The distillation piece: add a teacher (our own FP32 or W8A8 checkpoint,
already trained) and a distillation loss term (logit KL or feature matching) to the existing
training loop; ~40–60 lines in `train.py`/a new `distill.py`, plus a staged training schedule (FP32
→ W8A8 → binary, or ternary → binary) that needs its own STUDY design, not a single config flag.
The two-set/elastic-activation pieces would each need separate, smaller changes if adopted.
**Hazards.** The distillation piece touches only the loss function and training schedule — the
exported weight is still exactly ±1, zero deployment delta. The "two-set" piece, if it means more
than two *effective* weight levels at inference, would violate the binary constraint outright and
must not be adopted verbatim; read the full paper before proposing it as anything but a training-
time idea.
**Tried here?** No.
**Combines with.** B11 (both are staged-precision ideas; BiT's staging is distillation-driven,
BinaryBERT's is architecture-splitting-driven — could be compared or combined: distill *into* a
TWS-split binary network).
**Testable prediction.** Val-AUC direction: up, if a same-architecture FP32 or W8A8 checkpoint
(already trained per the anchor's baselines) is available as a teacher — this is the one card
where "no invented magnitude" is easiest to honor with a concrete, cheap first experiment (reuse
an existing checkpoint as teacher, no new training infrastructure beyond a loss term).

### B13 — ReActNet RSign / RPReLU (learnable activation shift, adapted to 8-bit)
**Mechanism.** Generalizes the activation-side sign/PReLU into RSign (`sign(x - bias)`, learnable
per-channel bias before the sign) and RPReLU (a learnable per-channel shift-and-slope after the
nonlinearity), at "near-zero extra cost" per the paper, to correct for activation distributions
drifting away from where a fixed threshold at zero is optimal.
**Why it could matter for binary weights here.** This is an activation-side idea, adapted here to
our 8-bit (moving to 6/4-bit) activations rather than ReActNet's fully-binary activations: a
learnable per-channel shift before quantization could recover some of what a fixed 8-bit grid
loses, without changing the weight side at all — orthogonal to every other card in this family.
**Primary source.** Liu, Shen, Savvides & Cheng, "ReActNet," ECCV 2020, arXiv:2003.03488.
Note: not in `literature/INDEX.md` — gap; adjacent to `2508.07431` (BitPart) already indexed.
**Published effect.** ReActNet reports 69.4% ImageNet top-1 with both weights and activations
binary (abstract, table-consistent per multiple secondary sources) — a W1A1 CNN number; does not
transfer to our W1A8 (moving toward W1A4) transformer on 3-feature jet constituents.
**Knob or code change.** Add a learnable per-channel bias before each activation quantizer's input
and a learnable per-channel shift/slope after; touches the activation-quantizer wrapper in `qat.py`
(likely near where the 8-bit activation grids are initialized) — estimate 20–30 lines plus wiring
into the learned-activation-width mechanism the anchor already uses.
**Hazards.** Weight-side binary constraint is untouched — this card only ever touches activations.
The learnable shift is an *add*, not a multiply, so it is cheap in fixed point (a bias term); it
does enter the graph before the activation quantizer, so it may interact with `EBOPs` accounting
if the shift changes which activation bit-width the BetaPID controller settles on (an indirect,
not architectural, EBOPs effect).
**Tried here?** No.
**Combines with.** Any weight-side card (B01–B12) — this is the one axis genuinely orthogonal to
the weight-binarization scheme, and the brief explicitly calls it out as such.
**Testable prediction.** Val-AUC direction: up at the anchor's A8 width, larger effect expected at
A4 specifically (RSign/RPReLU exist to fix activation-distribution mismatch, which gets worse as
the activation grid coarsens) — under the PID, expect the controller to spend fewer effective bits
on activations that need the shift less, so the 350k EBOPs constraint may be met at a *lower*
achieved bit-width than without this card, not just a higher AUC at the same width.

### B14 — Ternary baseline: BitNet b1.58 / TWN / TTQ (labelled comparison, not the thesis)
**Mechanism.** {−1,0,+1} weights with one (TWN, b1.58) or two (TTQ) learned scale factors per
layer; the zero state is a genuine third value, not a training artifact — this is the family our
`absmean_binarize` docstring explicitly treats as a STOP condition if it ever appears in a "binary"
layer (`n_zero` must be 0, per `binary_absmean` summary check).
**Why it could matter for binary weights here.** Per CLAUDE.md and the BRIEF, ternary is a
comparison baseline only. Its relevance is as the upper bound Delta measures binary against —
and as the FastML 2026 benchmark's own finding that ternary beat binary on every axis (AUC, LUT,
latency) in a different model/dataset (already on file, 2026-09-01 log) — a standing threat this
Delta does not resolve, only tracks.
**Primary source.** Li, Zhang & Liu, "Ternary Weight Networks," arXiv:1605.04711; Zhu, Han, Mao &
Dally, "Trained Ternary Quantization," arXiv:1612.01064; Ma, Wang, Wei et al., "The Era of 1-bit
LLMs" (b1.58), arXiv:2402.17764. Notes: `literature/bitnet-1bit-ternary/1605.04711_ternary_weight_networks.md`,
`literature/bitnet-1bit-ternary/1612.01064_trained_ternary_quantization.md`,
`literature/bitnet-1bit-ternary/2402.17764_era_of_1bit_llms_1p58.md`.
**Published effect.** Already on file, not re-derived here: FastML 2026 (Sloot), BitNet-1.58
ternary 0.9254 AUC / 80.7k LUT / 0 DSP beats BitNet binary 0.9178 AUC / 87.3k LUT on their OpenML
hlf binary-classification MLP (docs/literature note + 2026-09-01 log) — different dataset (16
engineered features, 2-class), different architecture (MLP, not transformer), same venue/device
class (VU13P) as ours.
**Knob or code change.** Already exists in the codebase as a labelled comparison quantizer path
(per `binarize.py`'s own zero-state STOP-condition language, ternary is the thing binary must
*not* collapse into); would need `inventory/code-surface.md` to state the exact config flag.
**Hazards.** Three weight values per layer — explicitly not the thesis; every card in this family
that risks introducing a zero state (e.g., a badly-tuned annealed STE in B07/B08) must be checked
against `n_zero == 0` at export, exactly as `binarize.py`'s summary dict already does.
**Tried here?** Per the 2026-09-01 log: "no ternary arm by decision" in our own training so far.
**Combines with.** Nothing in this family — it is the alternative to the whole family, kept as a
reference point only.
**Testable prediction.** Not applicable in the "direction for binary" sense — this card's
prediction is about the *comparison*, not a delta: if a ternary arm were run at the same N=64/350k-
EBOPs point, the FastML 2026 pattern (ternary ≥ binary on AUC and LUT) is the standing hypothesis
Delta has not tested at our scale; flagged, not resolved, here.

---

## Omitted and why

- **EMA/SWA of latent weights.** Searched; no binary-weight-specific primary source with a
  published number was found distinct from general EMA/SWA folklore for quantized training. Bop
  (B10) already subsumes the more principled version of "smooth the latent" by removing the
  latent entirely; a plain EMA-of-latent-weights card would duplicate B10's testable prediction
  without a citable primary source. Omitted rather than filled with an uncited claim.
- **Flip-rate regularization** (penalizing how often a binary weight changes sign between steps).
  This appears as a diagnostic/monitoring idea in several BNN papers (including asides in
  Helwegen et al. 1906.02107) but not as a standalone method with its own primary source and
  number; folding it into B10's card (Bop's threshold *is* an implicit flip-rate control) avoids
  inventing a citation.
- **Binary-friendly initialization.** Covered qualitatively inside Bi-Real Net (B05, "a better
  initialization method" is one of its three listed novelties) rather than as its own card — no
  separate primary source proposes initialization alone as the contribution at binary-transformer
  scale.
- **BiBERT** (arXiv:2203.06390, accessed 2026-09-26) — read the abstract; its main contribution
  (Bi-Attention structure, Direction-Matching Distillation) is substantially activation/softmax-
  side and distillation-side, overlapping B12 (BiT) and B13 (activation shifts) without a distinct
  weight-binarization mechanism. Merging it into a 14th card would have diluted the schema's
  "mechanism in two to five sentences" requirement; noted here instead of forced into a card.
- **Soft-sign/tanh temperature annealing as a standalone card.** IR-Net's EDE (B07) and ReSTE (B08)
  are both instances of this family with citable numbers and named methods; a generic "soft-sign
  annealing" card would have duplicated them without adding a distinct primary source.
- **Per-channel weight decay / latent weight clipping as standalone cards.** These are training
  hyperparameters mentioned inside BinaryConnect (already B09's primary source) and Bop (B10)
  rather than independently published methods with their own number; folded into those cards'
  "knob" discussion implicitly rather than split out.

## Log lines to append

- 2026-09-26 — Bulat & Tzimiropoulos, "XNOR-Net++: Improved Binary Neural Networks," BMVC 2019,
  arXiv:1909.13863 (accessed 2026-09-26). Per-channel/learned scale factor for binary conv nets;
  relevant as the per-channel-β candidate (B03) but breaks our SCORE_FOLD/EXPLICIT_SCALE fold
  table by turning a scalar multiply into a per-channel one — abstract-level read only, no table
  number carried.
- 2026-09-26 — Liu et al., "Bi-Real Net," ECCV 2018, arXiv:1808.00278 (accessed 2026-09-26).
  ApproxSign backward + identity shortcut for 1-bit CNNs; relevant as a backward-only STE
  alternative (B05), zero deployment delta — abstract-level read only.
- 2026-09-26 — Qin et al., "Forward and Backward Information Retention for Accurate Binary Neural
  Networks" (IR-Net), CVPR 2020, arXiv:1909.10788 (accessed 2026-09-26). Libra-PB (balance +
  standardize + power-of-two scale) and EDE (annealed backward); relevant because our current
  centered-absmean scheme is already half of Libra-PB, and the power-of-two scale is the one
  candidate that could cheapen the β-fold hazard rather than just improve accuracy — abstract-level
  read only, table numbers not opened.
- 2026-09-26 — Wu et al., "Estimator Meets Equilibrium Perspective: A Rectified Straight Through
  Estimator" (ReSTE), ICCV 2023, arXiv:2308.06689 (accessed 2026-09-26). Power-function annealed
  backward; relevant as a 2023, more recent alternative to older STE variants — abstract-level
  read only.
- 2026-09-26 — Helwegen et al., "Latent Weights Do Not Exist: Rethinking Binarized Neural Network
  Optimization" (Bop), NeurIPS 2019, arXiv:1906.02107 (accessed 2026-09-26). Optimizer-level
  alternative removing the latent float entirely; relevant as the largest architectural delta in
  this family and the weakest evidence for transfer (designed for W1A1, we run W1A8→W1A4) —
  abstract-level read only.
- 2026-09-26 — Bai et al., "BinaryBERT: Pushing the Limit of BERT Quantization," ACL 2021,
  arXiv:2012.15701 (accessed 2026-09-26). Ternary-weight-splitting two-stage training; relevant as
  a progressive-binarization candidate (B11) but at 110M-parameter BERT scale, a transfer risk
  flagged explicitly — abstract-level read only.
- 2026-09-26 — Liu et al., "BiT: Robustly Binarized Multi-distilled Transformer," ICLR 2023,
  arXiv:2205.13016 (accessed 2026-09-26). Multi-step distillation into binary; relevant as the
  cheapest-to-try idea in the family (reuse an existing FP32/W8A8 checkpoint as teacher) —
  abstract-level read only, GLUE numbers not opened.
- 2026-09-26 — Liu, Shen, Savvides & Cheng, "ReActNet," ECCV 2020, arXiv:2003.03488 (accessed
  2026-09-26). RSign/RPReLU learnable activation shift; relevant as the one card orthogonal to
  every weight-binarization choice in this family, adapted here from W1A1 to W1A8→W1A4 — 69.4%
  ImageNet top-1 W1A1 number does not transfer, cited only for the mechanism.
- 2026-09-26 — Qin et al., "BiBERT: Accurate Fully Binarized BERT," ICLR 2022, arXiv:2203.06390
  (accessed 2026-09-26). Read and omitted from the card set (see "Omitted and why"): overlaps B12/
  B13 without a distinct weight-binarization mechanism.
