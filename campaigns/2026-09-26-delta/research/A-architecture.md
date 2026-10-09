# Family A — architecture

Method cards for the architecture axis of Delta. Every card is a delta from the
anchor, arm A of `campaigns/2026-09-26-training-batch/STUDY.md`: A07-N64, `d_model 32, n_heads
4, n_layers 1, ffn_dim 32`, `pos_enc learned`, `norm none`, `pool gap`, `ffn_act relu`, binary
`weight binary_absmean`, `act_bits 8` with `act_policy learned_per_tensor_width` /
`act_granularity channel`, 350k EBOPs target, N=64, pT ≥ 2 GeV gate, 90/10 split. All numbers
for our own pipeline are quoted from `campaigns/2026-09-26-training-batch/STUDY.md` or from
code read directly; none are invented. Sun et al. numbers are quoted from arXiv:2510.24784
Table 1 exactly as STUDY.md already labels them (one model, no seed interval, 350k-EBOPs PID
target, selection rule not stated) — reused here, not recomputed.

**Code-surface note (read directly, not from memory).** `publication/code/hgq2/bnhgq2/build.py`
is the *export* builder (binary-frozen graph → hls4ml); `bnhgq2/qat.py` is the *training* graph.
Config fields accepted by the trainer, from `bnhgq2/config.py:20` and the anchor config
(`publication/code/constituent-study-20260922/configs/const0922-a07-n64-s1-fast50-fp32.json`):
`arch.{n_part, n_feat, d_model, n_heads, n_layers, ffn_dim, n_classes, pool, ffn_act, norm,
norm_placement, pos_enc, softmax_free, input_std}`. `build.py` currently accepts only
`arch.norm ∈ {subln, none}` (raises `ValueError` otherwise, `build.py` "Norm placement" block) —
so a norm variant beyond those two is a trainer-side *and* export-side code change, not
config-only. `pos_enc` toggles `AddPositional` in `qat.py:462`; the export path always drops it
and folds PE into `input_proj`'s bias table (`build.py` "PE + input bias" comment; also
`convert_w8a8.py`/`convert_fp32.py`/`convert_binary.py` all rebuild `with_pos_enc=False`), so
`pos_enc none` is genuinely config-only on both sides. `pool` currently has one code path
(`QGlobalAveragePooling1D`, `build.py` "head" block) — any other pooling is new code on both
sides. The only multiplier-bearing ops in `build.py` are the two `QEinsum` act×act contractions
inside attention (`{blk}_attn_scores`, `{blk}_attn_ctx`); the file's own comment records that
letting a real (non-CSD-2) β sit in-weight at RF=256 inferred 256 real DSPs — the 0-DSP claim
rides on every *weight*-side multiply staying ±1/CSD-2, so any card that adds a second act×act
product (attention pooling, GLU, pairwise features) is scored against that risk explicitly below.

---

### A01 — width/heads ladder at fixed N=64

**Mechanism.** Sweep `d_model ∈ {16, 24, 32, 48}` × `n_heads` a divisor of `d_model` (2 or 4),
`n_layers 1` fixed, `ffn_dim = d_model`, everything else anchor. Chang-sized point (d24, h2) is
covered by arm E of the anchor STUDY; this card is the rest of the ladder around it.

**Why it could matter for binary weights here.** Binary weights have lower per-weight
information content than float weights at the same shape (BitNet, arXiv:2310.11453, motivates
scaling width, not precision, to recover capacity); the anchor's own width (32) was picked
before an EBOPs-budget target existed. A wider/narrower model trades attention head count and
representational width against the same 350k-EBOPs ceiling, so the ladder finds whether the
anchor's width is EBOPs-efficient or arbitrary.

**Primary source.** BitNet, Wang et al., arXiv:2310.11453 (scaling-law argument for width
recovering 1-bit capacity), and the anchor's own arm E (Chang-sized d24/h2), `campaigns/2026-09-26-training-batch/STUDY.md`. Date accessed: 2026-09-27.

**Published effect.** No prior number for this exact ladder; arm E (d24,h2) vs A (d32,h4) is a
designed, not-yet-run comparison in the anchor STUDY ("architecture package," three knobs
changed together — not isolated to width).

**Testable prediction.** Wider d_model (48) beats narrower (16) at fixed EBOPs target only up to the point width itself exhausts the 350k budget; direction: accuracy non-monotone in width, not monotone-increasing.

**Knob or code change.** `arch.d_model`, `arch.n_heads`, `arch.ffn_dim` — config-only on both
train and export sides (`build.py` reads `A["d_model"]` etc. directly, no width-specific branch).

**Hazards.** Wider d_model increases the two act×act QEinsum sizes (T×H×E) linearly in D,
raising II or LUT count under `io_parallel` at fixed T=64; narrower d_model may starve the head
MLP (32/32/32, unchanged across this ladder) causing a bottleneck unrelated to the backbone.
Permutation-invariant: unaffected (no positional dependence introduced).

**Tried here?** Not run; arm E of the anchor STUDY is the nearest point and is itself unrun as
of 2026-09-26 (STUDY at ITERATE per `review/STUDY_arbiter_v1.md`).

**Combines with.** A03 (FFN ratio), A08 (head depth) — width changes interact with both.

---

### A02 — depth: n_layers 2 vs 1, and whether cross-layer weight sharing recovers it

**Mechanism.** Two variants under one card: (a) `n_layers 2` at fixed d_model, doubling block
count; (b) `n_layers 2` with the second block's weights tied to the first's (ALBERT-style
cross-layer sharing), so parameter count matches L=1 while depth doubles.

**Why it could matter for binary weights here.** At L=1 (the anchor), weight sharing is moot —
there is only one block to share. This card is the L=2 baseline plus the sharing variant that
tests whether added depth can be had without added binary-weight EBOPs.

**Primary source.** ALBERT, Lan et al., arXiv:1909.11942: cross-layer parameter sharing.
Mechanism claim (via WebSearch summary of the paper, not a fetched table/figure — flagged as
such, not a quoted number): sharing attention-only parameters costs little accuracy, sharing
FFN-layer parameters costs more, "all-shared" is their adopted default despite the larger drop.
No binary or small-transformer number exists. Date accessed: 2026-09-27.

**Published effect.** No prior number at our scale or precision. ALBERT's own numbers are
GLUE/SQuAD accuracy deltas at BERT scale (110M+ params) — not transferable to a 12.8k-parameter
binary tagger; cited for the *mechanism* (attention-sharing costs little, FFN-sharing costs
more), not the magnitude.

**Testable prediction.** Plain L=2 beats L=1 anchor on accuracy but misses 350k EBOPs at matched width; weight-tied L=2 recovers less accuracy than untied L=2 but stays closer to budget.

**Knob or code change.** `arch.n_layers 2` is config-only (the `for li in range(L)` loop in
`build.py` already handles L>1). Weight-tying across blocks exists nowhere in `qat.py`/`build.py`
— new code, estimated 10-20 lines to alias block-1 kernels/quantizer state into block-2's build
call in the training graph, plus an export-side check that `build.py`'s per-block naming
(`bit_block_{li}`) still produces distinct `QuantizerConfig` objects sharing the same variable.

**Hazards.** L=2 roughly doubles EBOPs from attention+FFN unless width shrinks to compensate,
directly opposing the 350k target; doubles the two act×act QEinsum sites (more II pressure).
Weight-tying does not reduce EBOPs (activations still flow through the block twice) even though
it reduces stored parameters — a distinction Delta must not blur. Permutation-invariant:
unaffected.

**Tried here?** Not run.

**Combines with.** A01 (width), A12 (residual scaling — deeper binary stacks need it more).

---

### A03 — FFN expansion ratio

**Mechanism.** Sweep `ffn_dim ∈ {16, 32, 64}` at fixed `d_model 32` (anchor uses ratio 1.0,
`ffn_dim == d_model`; standard transformers use ratio 4).

**Why it could matter for binary weights here.** The FFN is two binary linears (`fc1`, `fc2` in
`build.py`); a wider bottleneck may recover a per-weight capacity FFN loses under ±1 kernels
(the same BitNet width argument as A01, applied to the FFN alone rather than the whole model),
at a known EBOPs cost that scales linearly in `ffn_dim`.

**Primary source.** No dedicated FFN-ratio paper for binary transformers found; the general
observation is folklore from the original Transformer (Vaswani et al., ratio 4) — not in our
literature tree, not cited as evidence, only as the reason ratio 4 is a natural comparison
point beyond the anchor's ratio 1. Date accessed: 2026-09-27.

**Published effect.** No prior number for our setting.

**Testable prediction.** ffn_dim 64 (ratio 2) beats ffn_dim 32 (ratio 1, anchor) on accuracy at the cost of EBOPs headroom; ffn_dim 16 (ratio 0.5) is worse than the anchor.

**Knob or code change.** `arch.ffn_dim` — config-only both sides.

**Hazards.** Linear EBOPs and LUT cost in `ffn_dim`; at ratio 4 (`ffn_dim 128`) this is likely
the single largest EBOPs consumer in the model, competing directly with attention for the 350k
budget. No new multiplier type introduced (still binary-weight × quantized-activation), so the
0-DSP argument is undisturbed by width alone. Permutation-invariant: unaffected.

**Tried here?** Not run.

**Combines with.** A13 (GLU — changes what "ffn_dim" costs), A01.

---

### A04 — positional encoding: learned vs none

**Mechanism.** Anchor uses `pos_enc learned` (`AddPositional`, `qat.py:462`, folded into
`input_proj`'s bias table on export, `build.py` "PE + input bias" comment). This card is
`pos_enc none`: the additive term is dropped entirely, both in training and export.

**Why it could matter for binary weights here.** Jet constituents form an unordered set (the
same physics argument behind Deep Sets/EFN, arXiv:1810.05165, and ParticleNet's particle-cloud
framing, arXiv:1902.08570): a learned per-position additive term makes the tagger's output
depend on constituent order, which is not a property of the jet. Removing PE restores exact
permutation invariance and removes 64×32 learned parameters (small, but non-zero EBOPs since
the added bias table is quantized).

**Primary source.** Deep Sets / EFN, Komiske, Metodiev, Thaler, arXiv:1810.05165 (IRC-safety
and set symmetry argument); ParticleNet, Qu & Gouskos, arXiv:1902.08570 (particle-cloud framing).
This exact ablation (PE on/off at fixed architecture) is pre-registered as arm F of the anchor
STUDY, `campaigns/2026-09-26-training-batch/STUDY.md`, "splits E into 'no position' versus
'smaller'." Date accessed: 2026-09-27.

**Published effect.** No prior number for this architecture; arm F is designed, not run.

**Testable prediction.** pos_enc none performs at or above pos_enc learned (anchor) — permutation invariance is not a capacity loss at this N and constituent ordering carries little independent signal.

**Knob or code change.** `arch.pos_enc: none` — config-only on both sides (already a supported
value; `build.py`'s PE-fold path is conditioned on the key being present at all).

**Hazards.** None specific to HLS/DSP — removing a layer only shrinks the graph. The hazard is
purely interpretive: if A04 *hurts* accuracy, it says the model is using position as a proxy
for physical ordering already present in the data (e.g., pT-sorted constituents), which is a
different claim than "attention needs position." Strictly permutation-invariant with PE off,
strictly not with it on.

**Tried here?** Pre-registered, not yet run — arm F of the anchor STUDY (`STUDY.md` arms table).

**Combines with.** A09 (Deep Sets comparator — the natural end state if PE removal plus
attention removal both help), A07 (class token, which reintroduces an order-independent but
still learned token).

---

### A05 — normalisation: none / frozen affine / RMSNorm / SubLN

**Mechanism.** Four points, not one: (i) anchor's `norm none` (identity passthrough, `build.py`
`norm()` function, `norm_kind == "none"` branch); (ii) the anchor's *own* CSD-2 frozen affine
already inserted at every β-carrying site when `norm none` is selected (`build.py` "v5" comment
— this is not optional, it is what replaces LayerNorm's scale-restoration under `norm none`,
already running in every anchor arm); (iii) RMSNorm (Zhang & Sennrich, arXiv:1910.07467) as a
new, *trainable*, norm-free-of-mean-centering alternative; (iv) SubLN, the anchor's *other*
supported value (`PSubLN`, `build.py` `subln.py`) — already flagged in the anchor STUDY as
"the historical W1-vs-W8 confound" (Confound 4) and pinned to `none` for that reason.

**Why it could matter for binary weights here.** A binary linear layer cannot fold a
multiplicative BatchNorm/LayerNorm scale into its own ±1 kernel the way Sun et al.'s
`QEinsumDenseBatchnorm` folds BN into a float kernel (`model.py:37` etc.) — the scale has
nowhere to go but a separate affine, which is exactly what `build.py`'s CSD-2 frozen affine
already is. So "fused BN" (Sun's mechanism) has no binary analogue; the real comparison is
*trainable* affine/RMSNorm/SubLN normalisation versus the anchor's *frozen*, β-derived one.
RMSNorm is a plausible middle point: cheaper than full LayerNorm (no mean-centering step) but
still trainable, unlike the anchor's frozen CSD-2 affine.

**Primary source.** RMSNorm, Zhang & Sennrich, arXiv:1910.07467; SubLN mechanism from
`publication/code/hgq2/bnhgq2/build.py` and `subln.py` directly; the W1-vs-W8 confound from
`campaigns/2026-09-26-training-batch/STUDY.md`, Confound 4. Date accessed: 2026-09-27.

**Published effect.** RMSNorm's own reported wall-clock and task-quality numbers (via WebSearch
summary of the paper, not a fetched table — flagged as such) are full-precision Transformer/
BERT-scale — no binary-weight, no small-model, no FPGA number exists; quoted for mechanism only.
No prior number for SubLN vs RMSNorm vs frozen affine on this model.

**Testable prediction.** A trainable norm (RMSNorm or trainable affine) beats the anchor's frozen CSD-2 affine on accuracy at the same EBOPs target, at some added table/DSP-audit cost.

**Knob or code change.** `arch.norm` currently accepts only `{subln, none}` (`build.py` raises
otherwise) — adding `rmsnorm` or a *trainable* affine is new code on the export side (a new
frozen-vs-trainable branch in `norm()`, plus a new `QuantizerConfig` for RMSNorm's scale) and on
the training side (`qat.py`, wherever `norm` is dispatched) — estimated 30-50 lines given the
existing `PSubLN` as a template.

**Hazards.** SubLN is already excluded from the anchor for the W1-vs-W8 confound reason — this
card must not silently reopen that confound; any SubLN run must be labelled as such and not
compared across weight-width arms. RMSNorm's variance computation is itself a sum-of-squares
reduction across d_model — an added multiply-accumulate per channel, small but not the frozen
CSD-2 shift-add the anchor uses; check whether it is DSP-free at this width (D≤48) before
claiming it inherits the 0-DSP property. RMSNorm also needs a reciprocal square root of the
sum-of-squares — in hls4ml this is realized as a table lookup, the same primitive family as the
softmax `inv` LUT already in `build.py`'s `softmax_confs`, so it adds one more LUT table per
norm site, not a DSP, but a table-sizing question that must be audited the same way. Permutation-
invariant: unaffected (norm is per-position, independent of order).

**Tried here?** `norm none` and `norm subln` both exist in code and are both run somewhere in
the confirmed pipeline; `norm none` is the anchor. RMSNorm and a trainable affine: not tried.

**Combines with.** A12 (Bi-Real shortcuts interact with whatever sits at the shortcut junction),
A02 (deeper stacks need normalisation more).

---

### A06 — pooling: GAP vs max vs weighted (power-of-two) sum

**Mechanism.** Replace the anchor's `QGlobalAveragePooling1D` (`build.py` "head" block) with (a)
max-pooling over the time axis, or (b) a fixed power-of-two-scaled sum (`QSum` with
`scale = 2**-round(log2(N))`, the pattern already used in Sun et al.'s Deep Sets variants,
`model.py:88, 97` — a shift, not a divide, so it stays DSP-free at any N whether or not N is a
power of two).

**Why it could matter for binary weights here.** GAP at N=64 divides by 64, an exact power-of-two
shift — cheap and exact already; there is no accumulator-width problem to fix here (that problem
is specific to non-power-of-two N, e.g. Sun's N=10 case noted in `build.py`'s GAP comment, which
does not apply at N=64). Max pooling changes what the classifier sees (peak-constituent features
rather than an average) and is a genuinely different inductive bias, worth testing on its own
terms rather than as a resource fix.

**Primary source.** Sun et al.'s own `QSum`-based Deep Sets pooling, `model.py:88, 97`
(power-of-two-scaled sum as their pooling primitive; not from a separate paper). Date accessed: 2026-09-27.

**Published effect.** No prior number for max vs GAP vs scaled-sum at this architecture; Sun et
al. never ablate pooling choice against a fixed backbone in the material read.

**Testable prediction.** GAP (anchor) and scaled-sum are statistically indistinguishable (same operation, different framing); max pooling is worse than both because peak-constituent features discard the averaging signal a jet classifier relies on.

**Knob or code change.** `arch.pool` currently has exactly one code path (`build.py` "head"
block hard-codes `QGlobalAveragePooling1D`) — every other pooling choice is new code on both
train and export sides, estimated 15-25 lines each (a new branch keyed on `A["pool"]`, mirroring
Sun's `QSum` pattern for the scaled-sum case; a `keras.layers.GlobalMaxPooling1D` wrap plus a
quantizer config for max).

**Hazards.** Max pooling is a comparison, not a sum — hls4ml must support a max-reduction
primitive over the time axis at whatever bit width the incoming stream carries; check hls4ml
LayerConfig coverage before scheduling (not yet verified here). None of the three candidates
introduces a new multiplier. Permutation-invariant: all three are (sum/mean/max over the set
axis are all order-independent) — this is the one card in this family where every variant keeps
the invariance property untouched.

**Tried here?** Not run; GAP is the anchor's only tested pooling.

**Combines with.** A07 (attention pooling / class token — a strictly more expensive alternative
to this card's cheap options).

---

### A07 — attention pooling (PMA) or class token

**Mechanism.** Replace GAP with either (a) Pooling by Multi-head Attention (PMA), a learned
single seed vector attending over the T=64 constituent embeddings via one more MHA call (Lee et
al., arXiv:1810.00825, "PMA_k(Z) = MAB(S, rFF(Z))", k=1 seed typical), or (b) a prepended class
token carried through the existing attention block(s) and read out at the head, ParT/ViT-style.

**Why it could matter for binary weights here.** Both let the pooling step *learn* which
constituents matter instead of averaging them uniformly — closer to what full attention already
does inside the block, so this asks whether a second, smaller attention operation at the head is
a better use of EBOPs budget than GAP's free reduction.

**Primary source.** Set Transformer, Lee et al., arXiv:1810.00825 (PMA mechanism, permutation
invariant by construction — it is explicitly designed as a set-pooling primitive, not a
sequence one); class-token precedent noted generically in ViT/BERT lineage, not a specific paper
in our tree. Date accessed: 2026-09-27.

**Published effect.** No prior number for PMA or class token on a binary jet tagger; Set
Transformer's own numbers are full-precision point-cloud/set benchmarks (amortized clustering,
counting unique characters), not transferable in magnitude.

**Testable prediction.** PMA or class-token pooling beats GAP (anchor) on accuracy but the added act×act attention site erodes or eliminates the EBOPs headroom the gain would otherwise buy.

**Knob or code change.** New code on both sides: a new learned seed vector (PMA) or a new
concatenated token position (class token) plus one additional `QMultiHeadAttention`/`QEinsum`
call at the head — the existing per-block attention code in `build.py` is the template, but
this is genuinely new graph structure, estimated 60-100 lines including the new quantizer
configs for the extra Q/K/V/scores/ctx sites.

**Hazards.** **Directly against the 0-DSP argument if not built carefully.** This adds a *third*
pair of act×act multiplies (scores + ctx, on top of the two the backbone already has) — the
exact operation `build.py`'s own comment flags as the DSP risk (256 real DSPs when a real,
non-CSD-2 scaler sits in-weight at RF=256). Any PMA/class-token card must keep the added
attention's weights binary and its scaler CSD-2-foldable or it silently reopens the DSP
question the whole thesis rests on. Class token additionally changes T from 64 to 65,
disturbing every downstream shape assumption in `build.py` (T is threaded through every
`output_shape=(T, ...)` call) — a bigger patch than PMA. Permutation-invariant: PMA is (the
seed vector is order-independent by construction); a class token is invariant *among the real
constituents* but the token's own fixed position is a mild asymmetry-breaker, usually treated
as acceptable in the ViT lineage but worth flagging, not assuming.

**Tried here?** Not run.

**Combines with.** A06 (the cheap alternative), A11 (linear-attention forms of the same idea).

---

### A08 — head MLP depth and width

**Mechanism.** Anchor head is GAP → `head_fc1` (D→D, i.e. 32→32) → ReLU → `head_fc2` (D→5)
(`build.py` "head" block — only two dense layers). Sun et al.'s own head depth *varies by model
class and is not consistent*: transformer/SALT use a 3-layer 32→32→32→5 head (`model.py:205-208,
269-272`); the plain GNN uses 64→32→16→5 (`:98-101`); `gnn_table` uses a single 24→5 layer
(`:133-135`); Linformer (`get_llformer`) uses a single 16→5 layer (`:238-239`). This card sweeps
head depth (1, 2, 3 dense layers) and width at fixed backbone.

**Why it could matter for binary weights here.** The head is the cheapest place to add capacity
per EBOP (D×D is small at D=32) if the backbone's binary attention/FFN is the bottleneck on
accuracy. But Sun et al.'s own head depth has no monotone relation to their Table 1 accuracy at
N=64: their *shallowest* head (Linformer, one layer) is their *best* N=64 row (79.8%, per
`STUDY.md`'s reference table), while their 3-layer-headed transformer (MHA, 77.9%) is their
worst. That undercuts, rather than supports, an inference that head depth is load-bearing at
their scale — it argues for treating head depth as an independent knob to test on our own
backbone rather than copying their deepest head on the assumption it helped them.

**Primary source.** `reference-code/HGQ2-examples/jsc150/model.py:98-101, 205-208` (Sun et al.'s
own head shapes, read directly from the code they ran, not from the paper text). Date accessed: 2026-09-27.

**Published effect.** No published ablation isolating head depth from the rest of Sun et al.'s
architecture; their Table 1 numbers (79.4-79.8% at N=64, from `STUDY.md`'s reference table) are
whole-model numbers including their 3-layer head, so the contribution of head depth alone is
not separable from their published numbers.

**Testable prediction.** A third head layer (matching Sun et al.'s deepest head) does not beat the anchor's two-layer head at fixed EBOPs, given no monotone head-depth-to-accuracy relation in Sun et al.'s own Table 1.

**Knob or code change.** `build.py`'s head is currently hard-coded to exactly two dense layers
(`head_fc1`, `head_fc2`) — adding a third layer is a small, mechanical code change on both train
and export sides (duplicate the `head_fc1`/`affine`/`ReLU` block once more), estimated 15 lines.

**Hazards.** Linear EBOPs cost in added head width/depth, competing with the backbone for the
350k budget; no new multiplier type (still binary-weight dense layers). Permutation-invariant:
unaffected (head operates post-pooling, on a per-jet vector).

**Tried here?** Not run; anchor head (2 layers) is the only tested point.

**Combines with.** A01, A03 (all are EBOPs-budget trade-offs against the same ceiling).

---

### A09 — Deep Sets / EFN comparator under binary weights (the threat card)

**Mechanism.** Replace the attention block entirely with Sun et al.'s Deep Sets topology
(`model.py:77-104`, `get_gnn`): per-constituent MLP, a pooled "context" branch added back
per-constituent (`QSum` + broadcast add), then a second per-constituent MLP, then pool, then the
same head. No attention, no Q/K/V, no softmax — an Energy-Flow-Network-style permutation-
invariant architecture (Komiske et al., arXiv:1810.05165) built entirely from binary dense
layers over the constituent axis.

**Why it could matter for binary weights here — this is the threat card.** Sun et al. state
directly (§3, as quoted in `campaigns/2026-09-26-training-batch/STUDY.md` reference table) that
at N=64 their own MHA "collaps[ed] ... into a Deep Set" — their attention model learned to
behave like a Deep Set rather than using genuine pairwise attention. If the same collapse
happens under *binary* weights, a binary Deep Set at equal EBOPs may match or beat binary MHA,
in which case the transformer framing (and the harder problem of binarizing attention) is not
buying anything at N=64, and Delta's harder attention-side cards (A07, A11, A12) matter less
than the head/pooling/Deep-Sets side.

**Primary source.** Sun et al., arXiv:2510.24784, §3 (MHA-collapses-to-Deep-Set finding, quoted
in `STUDY.md`); Deep Sets / EFN, Komiske, Metodiev, Thaler, arXiv:1810.05165 (the IRC-safe,
permutation-invariant construction this architecture instantiates); code at
`reference-code/HGQ2-examples/jsc150/model.py:77-104`. Date accessed: 2026-09-27.

**Published effect.** Sun et al. Table 1, N=64 (as quoted in `STUDY.md`): Deep Sets (HGQ) 79.4%
(the paper's headline row, one model, no interval), vs. their own MHA 77.9% at the same N — i.e.
in *their* (non-binary, mixed-precision HGQ) setting, Deep Sets already beats attention at
N=64. **Caveat: Deep Sets is not their best N=64 row** — Linformer trains higher still at 79.8%
(see A10); Deep Sets is the headline row `STUDY.md` uses as the comparand, not the top of their
own band. This is their number, their metric (test accuracy), their precision scheme (HGQ mixed
precision, not binary) — not comparable to any binary number of ours without a matched run.

**Knob or code change.** No Deep Sets topology exists anywhere in `bnhgq2/` — this is a new
model-building function, not a config flag on the anchor's transformer builder. Estimated
80-120 lines following `build.py`'s existing binary-quantizer helpers (`kq`, `act_q`, `affine`)
but a new graph shape (no attention, a `QSum`-based context branch instead).

**Hazards.** No attention means no act×act QEinsum contractions at all — this architecture is
*more* conservatively DSP-free than the anchor transformer, not less; the only multipliers are
binary-weight × quantized-activation, same as every other card here. Permutation-invariant:
yes, exactly — Deep Sets is invariant by construction (no positional information anywhere in
the graph), a strictly cleaner invariance argument than the anchor's learned-PE transformer.

**Testable prediction.** At binary weights, N=64, 350k EBOPs: Deep Sets accuracy ≥ anchor
(A07) accuracy (direction only, following Sun et al.'s own non-binary finding).

**Tried here?** Not run in our pipeline; Sun et al.'s own code and paper are the only existing
evidence, and it is not our number.

**Combines with.** A04 (PE removal is a step toward this), A06 (pooling choice matters more once
attention is gone).

---

### A10 — Linformer and MLP-Mixer comparators

**Mechanism.** Two O(N)-ish, non-standard-attention alternatives from Sun et al.'s own code: (a)
Linformer-style low-rank projection of the attention sequence dimension before the K/V
projections (`get_llformer`, `model.py:213-241`, using `QLinformerAttentionT(h, 4, d, dropout=0.0)`
at `model.py:230` — projection rank 4 at their N — per Wang et al., arXiv:2006.04768); (b)
MLP-Mixer's token-mixing MLP applied along the constituent axis instead of attention (`get_mlpm`,
`model.py:26-56`, the `'bnc,nN->bNc'` einsum — a dense layer whose input and output axis is the
constituent index itself, i.e. explicitly position-dependent). **Important caveat on (a):** Sun
et al.'s own Linformer (`get_llformer`) is built entirely from `QDenseT` (`model.py:227,
233-234, 238-239`), the table-native dense primitive — the same primitive excluded from this
family under "Omitted and why" (`gnn_t`) because it is architecturally a LUT-native design, not
a binary-weight one. Their 79.8% Linformer row is therefore a table-native model's number, not a
quantized-binary-matmul Linformer's — doubly non-comparable to anything we would build under
this card.

**Why it could matter for binary weights here.** Both replace attention's O(N²) score matrix
with cheaper linear or token-mixing operations, directly relevant to EBOPs budget at N=64
(4096-entry score matrix vs Linformer's N×k or Mixer's N×N-but-fixed-weight token-mix). Linformer
keeps the *K/V→low-rank* structure inside otherwise-normal attention; MLP-Mixer removes
attention altogether.

**Primary source.** Linformer, Wang et al., arXiv:2006.04768 (O(n) self-attention via low-rank
K/V projection, "performs on par with standard Transformer models" at BERT/RoBERTa scale — no
binary, no small-model, no FPGA number); code at
`reference-code/HGQ2-examples/jsc150/model.py:213-241` (Linformer) and `:26-56` (MLP-Mixer); the
MLP-Mixer 79.7% N=64 number in `STUDY.md`'s reference table is explicitly sourced from Sun et
al.'s ref. [18], not their own training run, and is *not* stated to be trained at 350k EBOPs —
a caveat this card inherits. Date accessed: 2026-09-27.

**Published effect.** Sun et al. Table 1 as quoted in `STUDY.md`: Linformer 79.8% at N=64 (their
own trained row, HGQ mixed precision); MLP-Mixer 79.7% (quoted from ref. [18], provenance and
EBOPs-target status unclear). Neither is a binary number and neither is ours.

**Testable prediction.** Neither Linformer nor MLP-Mixer beats the anchor transformer under binary weights at matched EBOPs; MLP-Mixer's position-dependent mixing underperforms the anchor once ordering information is removed by the pT-sort convention.

**Knob or code change.** Neither Linformer's low-rank K/V projection nor MLP-Mixer's token-mix
einsum exists in `bnhgq2/`. Linformer: new low-rank projection matrices (N×k, two of them for K
and V) plus the existing attention machinery downstream — estimated 40-60 lines reusing
`build.py`'s attention helpers. MLP-Mixer: a token-mixing dense layer over the constituent axis
plus the existing FFN-style channel-mixing dense — estimated 40-60 lines, no attention machinery
needed at all (no QSoftmax, no scores/ctx einsums).

**Hazards.** Linformer's low-rank projection matrices are themselves binary-weight linears (no
new multiplier type) but add a third and fourth weight matrix per attention call; k must be
chosen (Wang et al. use k≪n at BERT scale — at our N=64 even k=8-16 may already be large
relative to N, needs an EBOPs-aware sweep, not a fixed borrowed value). MLP-Mixer's token-mix
einsum (`'bnc,nN->bNc'`) is **explicitly position-dependent** — one weight per (input-position,
output-position) pair — so it is **not permutation-invariant**, the same concern as learned PE
(A04), and should be flagged plainly rather than assumed benign; this is a genuine trade against
the physics motivation for permutation invariance in jet tagging.

**Tried here?** Not run in our pipeline.

**Combines with.** A09 (all three are attention alternatives; a wave comparing A09/A10/anchor
head-to-head is a natural single study).

---

### A11 — JEDI-linear-style O(N) interaction/attention (not a general kernelized-attention card)

**Mechanism.** JEDI-linear (Que, Sun, Paramesvaran, Clement, Karakoulaki, Brown, Laatu, Cox,
Tapper, Luk, Spiropulu) does **not** kernelize softmax attention — it replaces JEDI-net's O(N²)
pairwise interaction network with an edge function constrained to be **affine** in its two
inputs, `f_R(I_i, I_j) = W_1 I_i + W_2 I_j + C`, then uses distributivity to rewrite the sum over
all `j` as `W_2 · (global average pool over j) + W_1 I_i + C` (their Eq. 4) — a single pooled
quantity shared by every constituent, replacing the explicit N×N tensor with one GAP-style
reduction plus two affine maps. Applied to our transformer, the analogous move is not "linear
attention" in the usual (kernel feature map) sense; it is closer to A09's Deep Sets topology
than to standard attention at all — worth stating plainly rather than under a misleading label.

**Why it could matter for binary weights here.** The anchor's two act×act QEinsum contractions
(`{blk}_attn_scores`, `{blk}_attn_ctx`) scale with T²·H·E; JEDI-linear's own paper reports that a
full pairwise interaction network at just 30 particles already "consumes 71% of a VU13P/Alveo
U250's DSPs" (per their cited comparison, LL-GNN, arXiv:2209.14065) — direct evidence that
naive O(N²) computation is a real resource threat at trigger scale, not a theoretical one.
JEDI-linear's own design has **no act×act interactions in the final architecture** — global
average pooling is a reduction (sum then a fixed 1/N scale), and all remaining MACs are
weight×activation — the same shape as our own binary-weight matmuls, and reported DSP=0 at up to
128 constituents.

**Primary source.** JEDI-linear: Fast and Efficient GNNs for Jet Tagging on FPGAs, Que et al.,
arXiv:2508.15468 (2025 FPT); read via our own note,
`literature/jet-tagging-transformers/2508.15468_jedi_linear.md`, which itself reflects a WebFetch
of the full text (accessed by that note 2026-07-24). Date accessed (this pass): 2026-09-27.

**Published effect.** 5-class jet classification (g/q/W/Z/t), our note's Table (from the paper,
arxiv.org/html/2508.15468): 64 particles / 16 features: 82.4% accuracy, 79 ns latency, 192k LUT,
**0 DSP**, II=1, on a VU13P; 64p/3feat (our feature convention): 81.8% accuracy, other resource
columns not stated. This is macro-accuracy on a different input convention (16 kinematic
features is their main configuration; the 3-feature row lacks a resource breakdown in the
material read), HGQ mixed-precision weights (per-parameter learned bitwidth, mostly <3 bits per
their Fig. 7), and `da4ml` distributed-arithmetic synthesis — **not a binary-weight number and
not directly comparable to ours** (different weight-precision scheme, different synthesis
toolchain, no per-class AUC reported).

**Testable prediction.** An affine-interaction, GAP-factored reformulation (JEDI-linear's move,
not general linear attention) matches or beats anchor accuracy at equal or lower EBOPs, because
it removes the N×N score matrix that competes hardest for the 350k budget at N=64.

**Knob or code change.** JEDI-linear's affine-edge/GAP-factoring structure does not exist in
`bnhgq2/` — replacing the score/softmax/ctx attention block with an affine map plus a `QSum`-style
global average pool (following the pattern already used in Sun et al.'s `get_gnn`,
`model.py:88-97`, and Delta's own A09 Deep Sets card) is new code, larger than A09 because
it must still route through per-position `I_i` terms rather than A09's simpler pooled-context
add — estimated 60-100 lines, reusing `build.py`'s `QEinsumDense`/`QSum`/`affine` primitives.

**Hazards.** The saving is architectural (dropping true pairwise interaction for a mean-field
approximation), not an implementation trick — JEDI-linear's own framing is explicit that this
trades away "heterogeneous, genuinely pairwise edge embeddings" for a jet-level summary shared
by every particle, architecturally closer to Deep Sets than to attention (their own words, per
our note). That is a real physics trade, not free lunch: if genuine pairwise information (e.g.
ΔR between specific constituent pairs) matters for our 5-class task, this card would remove
exactly that. No new act×act multiplier type (GAP is a reduction, not a product), so it does not
threaten the 0-DSP argument the way A07/A13 do — if anything it strengthens it, per JEDI-linear's
own measured DSP=0 result (different toolchain caveat above notwithstanding). Permutation-
invariant: yes, by construction (the pooled term is symmetric in the constituent index).

**Tried here?** Not run in our pipeline; JEDI-linear is published, independent, at-scale
evidence for the mechanism, not our number.

**Combines with.** A09 (same mean-field/Deep-Sets family — a JEDI-linear-style affine-edge model
sits between the anchor transformer and plain Deep Sets on the "how much pairwise structure
survives" axis), A06 (both rely on a cheap pooled reduction).

---

### A12 — Bi-Real-style real-valued shortcuts and residual scaling

**Mechanism.** Add an identity (or scaled-identity) shortcut connecting the pre-quantization
real-valued activation of one binary block to the corresponding point in the next block, so the
gradient and forward signal have a real-valued path around the ±1 bottleneck, following Bi-Real
Net's core move (Liu et al., arXiv:1808.00278: "connects the real activations ... to activations
of the consecutive block, through an identity shortcut"). Distinct from the anchor's *existing*
residual adds (`build.py`'s `keras.layers.Add` after attention and FFN, already present) in that
Bi-Real's shortcut specifically bypasses the *quantization* step, not just the sub-layer.

**Why it could matter for binary weights here.** Bi-Real Net's whole point is recovering
representational capacity lost to 1-bit *activations* in a 1-bit CNN — our activations are 8-bit
(A8), not 1-bit, so the specific failure mode Bi-Real Net targets (near-zero gradient through a
hard sign function) is less severe here. The mechanism is still worth testing because our
*weights* are 1-bit even though activations aren't, and residual scaling (a learned or fixed
multiplier on the shortcut path, distinct from an unscaled identity) is a cheap, CSD-2-foldable
knob if it helps.

**Primary source.** Bi-Real Net, Liu et al., arXiv:1808.00278 — "the representational capability
of the Bi-Real net is significantly enhanced and the additional cost on computation is
negligible" (ImageNet, 1-bit-weight-*and*-activation CNNs, ECCV 2018) — a different domain
(vision, CNN, ImageNet scale, 1-bit activations) from ours; not directly transferable, cited for
mechanism only. Date accessed: 2026-09-27.

**Published effect.** No prior number for our setting; Bi-Real's own numbers are ImageNet top-1
accuracy for 1-bit CNNs, not applicable in magnitude to a 5-class, N=64, W1A8 transformer.

**Testable prediction.** A CSD-2-scaled Bi-Real shortcut improves accuracy over the anchor's existing plain residual add at L≥2 (A02) but shows no measurable effect at L=1 (the anchor), where the existing add already provides a full-precision-adjacent path.

**Knob or code change.** The anchor already has residual adds around both attention and FFN
(`build.py`, `keras.layers.Add(name=f"{blk}_add_attn"/"_add_ffn")`) — a true Bi-Real-style
shortcut (bypassing quantization specifically, not just the sublayer) would need to tap the
pre-`affine`/pre-quantization tensor and add it further downstream than the existing adds do;
estimated 20-30 lines to rewire the tap points, plus a learned or fixed scale (CSD-2-constrained
if it must stay DSP-free, per the same rule as every explicit-fold β in `build.py`).

**Hazards.** A learned (non-CSD-2) residual scale is exactly the kind of real-valued scaler
`build.py`'s own comments warn inferred 256 real DSPs when left unconstrained — this card must
specify CSD-2 or fixed-power-of-two scaling explicitly or it is a direct regression on the
0-DSP headline. Permutation-invariant: unaffected (shortcuts are per-position, order-independent).

**Tried here?** Not run. The anchor's existing residual adds are the closest tried structure,
already running in every arm of the anchor STUDY, but they are not Bi-Real's quantization-
bypassing shortcut specifically.

**Combines with.** A02 (deeper stacks benefit more from shortcuts), A05 (what sits at the
shortcut junction interacts with normalisation choice).

---

### A13 — gated FFN (GLU variants)

**Mechanism.** Replace the anchor's plain ReLU FFN (`fc1` → ReLU → `fc2`, `build.py` "FFN"
block) with a GLU-style gated FFN: two parallel projections of the input, one passed through a
gate nonlinearity and elementwise-multiplied with the other, then projected back down
(Shazeer's GLU variants, arXiv:2002.05202 — ReGLU, GEGLU, SwiGLU, etc.).

**Why it could matter for binary weights here.** GLU variants "yield quality improvements over
the typically-used ReLU or GELU activations" in Shazeer's own T5-scale, full-precision
experiments — an orthogonal-to-precision architectural change that might recover some of what
binarizing `fc1`/`fc2` costs, independent of any width or depth change.

**Primary source.** GLU Variants Improve Transformer, Shazeer, arXiv:2002.05202 — T5 encoder-
decoder, log-perplexity and downstream benchmark deltas, full-precision, LLM-scale. Date accessed: 2026-09-27.

**Published effect.** No prior number transfers: Shazeer's gains are measured in T5 log-
perplexity at billion-token training scale, full-precision weights — nothing about magnitude
generalizes to a 12.8k-parameter binary tagger at N=64. Cited for mechanism, not magnitude.

**Testable prediction.** GLU beats plain ReLU FFN (anchor) on accuracy at fixed nominal ffn_dim, but the added act×act gate multiply raises EBOPs enough that the gain does not survive re-tuning to the same 350k target.

**Knob or code change.** New code: GLU needs a second parallel projection at `fc1` (elementwise-
multiplied with the gated branch before `fc2`), roughly doubling the `fc1`-equivalent weight
count and adding a new **act×act elementwise multiply** — estimated 30-40 lines in `build.py`'s
FFN block plus a new quantizer config for the elementwise-product output.

**Hazards.** **This is the second-most direct threat to the 0-DSP headline after A07.** The
gate's elementwise product of two *activation* tensors is exactly the kind of act×act multiply
`build.py` currently limits to two sites (scores, ctx) inside attention; GLU adds one more such
site *per FFN, per block* — at L=1 that's one more, at L=2 (A02) that's two more. Every one of
these must be checked for DSP inference the same way the existing two are, not assumed free by
analogy to the binary-weight matmuls around it. Permutation-invariant: unaffected (per-position
gating, no cross-constituent mixing).

**Tried here?** Not run.

**Combines with.** A03 (FFN ratio — GLU's effective width doubles at fixed nominal `ffn_dim`),
A07 (both add new act×act sites — a combined EBOPs/DSP audit is needed if both are tried
together).

---

### A14 — FFN activation: ReLU vs tanh-LUT

**Mechanism.** Replace the anchor's ReLU (`build.py`, `keras.layers.ReLU`) with Sun et al.'s
`QAffinedUnaryFunctionLUT('tanh')` (`model.py:194, 198` — a trained affine-plus-LUT nonlinearity
used before their attention and FFN, not ReLU).

**Why it could matter for binary weights here.** ReLU is free in hls4ml (a comparison, no
table); a LUT-based nonlinearity trades a larger, more expressive activation function for a
lookup-table cost that scales with the table's bit width — a direct, quantifiable resource
trade rather than a capacity argument.

**Primary source.** `reference-code/HGQ2-examples/jsc150/model.py:194, 198` (Sun et al.'s own
tanh-LUT usage, read directly from their code — not from their paper text, which does not
specify this choice in the material read). Date accessed: 2026-09-27.

**Published effect.** No isolated ablation of ReLU vs tanh-LUT exists in the material read; it
is confounded with every other difference between Sun et al.'s architecture and ours in their
Table 1 numbers.

**Testable prediction.** tanh-LUT does not beat ReLU (anchor) on accuracy at this scale, and costs strictly more LUT budget for the table.

**Knob or code change.** `arch.ffn_act` already exists as a config field (anchor:
`"ffn_act": "relu"`) — confirms the trainer supports switching, but whether a LUT-based option
is implemented anywhere in `qat.py`/`build.py` was not verified in this pass; if not, adding one
means porting `QAffinedUnaryFunctionLUT` machinery, estimated 20-30 lines given hgq2 already
ships the layer type (used by Sun et al.'s own code against the same hgq2 version we build on).

**Hazards.** LUT-based nonlinearities have a table-size cost keyed to their input/output bit
width (2^bits entries) — must be sized against the activation grid this model actually uses
(A8, i.e. 8-bit datalanes) or the table dominates LUT budget for no accuracy reason.
Permutation-invariant: unaffected (per-element nonlinearity).

**Tried here?** Not run; `ffn_act relu` is the only value used across every anchor arm so far.

**Combines with.** A13 (GLU's gate nonlinearity is a natural place to also test tanh vs
sigmoid/ReLU variants).

---

### A15 — low-rank factorisation of binary linears

**Mechanism.** Factor a D×D (or D×FFN) binary weight matrix into two smaller binary matrices
D×r and r×D (r ≪ D), following the same low-rank principle Linformer applies to the *sequence*
axis (A10) but here applied to the *feature* axis of any dense layer in the backbone or head.

**Why it could matter for binary weights here.** Every factor stays ±1, so the thesis (all
weights binary) survives factorisation — the framing question is purely about EBOPs/latency:
two small binary matmuls plus an intermediate quantized activation stream of width r versus one
larger binary matmul.

**Primary source.** No dedicated low-rank-binary-factorisation paper is in our literature tree;
the mechanism is generic (matrix factorisation) and its use here is by analogy to Linformer's
sequence-axis low-rank projection (arXiv:2006.04768, A10) rather than a specific citation for
the feature-axis case. Date accessed: 2026-09-27.

**Published effect.** No prior number for this exact use.

**Testable prediction.** Low-rank factorisation of the head or FFN dense layers does not reduce EBOPs at any rank r large enough to preserve anchor accuracy, because the added intermediate activation stream re-adds most of the saved cost.

**Knob or code change.** New code: any factored dense layer needs two `QEinsumDense` calls plus
a new intermediate quantizer config (`act_q` at some new `i0`) for the width-r stream — estimated
20-30 lines per factored site, following `build.py`'s existing `QEinsumDense`/`kq`/`act_q`
pattern closely.

**Hazards.** The intermediate width-r activation stream is a **new EBOPs- and latency-bearing
pipeline stage** — factorisation trades weight count for an extra quantized activation site and
an extra pipeline stage (more latency, not less, unless r is small enough that the two smaller
matmuls' combined EBOPs beat the one larger matmul's). This must be checked arithmetically per
site (D·r + r·D vs D·D, in EBOPs terms) before assuming a saving. No new multiplier type (still
binary-weight matmuls). Permutation-invariant: unaffected if applied to feature-axis weights
only (not the sequence axis).

**Tried here?** Not run.

**Combines with.** A10 (same low-rank principle, sequence axis instead of feature axis — the
two should not both be tried on the same weight matrix without accounting for the interaction).

---

### A16 — Engram-style conditional memory (tried; one-seed epoch-100 pilot exists, no verified benefit)

**Mechanism.** An additive, gated memory module inserted after the first attention residual: a
hashed-address lookup into a learned table, gated by the current hidden state, following
DeepSeek's Engram design (address/gather/gate, not attention, no KV cache) adapted to the binary
backbone with quantized multi-bit memory tables. Four matched pilot arms: E00 two-block
reference, E01 one-block baseline (no memory), E02 one block + ungated memory, E03 one block +
gated memory.

**Why it could matter for binary weights here.** The stated hypothesis was that a small learned
memory could recover capacity removed by the ±1 backbone constraint — but "simply adding a
memory to the existing model cannot, by itself, reduce its arithmetic" (own runbook, quoted
below), so this card is an accuracy lever only, not an EBOPs lever, and its memory tables are
explicitly *not* part of the binary thesis (multi-bit, not ±1).

**Primary source.** DeepSeek Engram paper (as read and quoted in our own runbook), arXiv
reference given there as arxiv.org/html/2601.07372v1; our own adaptation:
`campaigns/2026-09-20-continuation-packed/engram/hgq2/study/ENGRAM_RESEARCH_AND_RUNBOOK.md`; our
own pilot result: `campaigns/2026-09-20-status/ENGRAM_PILOT_RESULTS.md`. Date accessed: 2026-09-27.

**Published effect.** Engram paper's own number (LLM, not jet tagging): Figure 5, a 12-layer MoE
at 100B tokens, validation loss 1.808 baseline vs 1.768 with 1.6B memory parameters (best single
insertion at layer 2: 1.770) — **a language-model loss number, at a scale nothing like ours**,
not comparable to any jet-tagging accuracy.

**Our own number (this is the one that matters here).** Epoch-100 pilot, one seed, 124,000
internal-*validation* jets (not held-out test), from `ENGRAM_PILOT_RESULTS.md`: E00 (two-block)
49.78% accuracy / 0.800 macro AUC / 849,916 EBOPs; E01 (one-block, no memory) 56.10% / 0.841 /
566,719; E02 (ungated memory) **61.03%** / 0.869 / 566,719 backbone + 17,920 memory-bitops
estimate = 533,092 combined; E03 (gated memory) 60.18% / 0.864 / 499,662 + 78,496 = 578,158
combined. **None met the 350,000 combined-cost target.** A paired bootstrap on E02 vs E03 (50,000
resamples) gives +0.845 percentage points (E02 over E03), 95% interval +0.628 to +1.061 — this
interval is validation-sample uncertainty at fixed selected checkpoints, **not a seed interval**;
no second seed exists. The report's own conclusion: "This one-seed pilot does not establish
reproducible superiority," and the memory-cost total is "not a measured native-only cost or FPGA
resource count" (own report). So: at this one seed and this one training prefix, E02/E03
(with memory) *do* beat E01 (without memory) on validation accuracy by a wide margin (+4.9 to
+5.9 points) — a real, recorded signal, not a null result — but it is one seed, one prefix, on
validation (not held-out), against a target neither arm reached, with a custom (non-native)
cost accounting. Report the gain and every one of those qualifiers together; reporting either
alone (a clean win, or "no benefit established") would misstate the record.

**Testable prediction.** At held-out (ROC-test) evaluation across multiple seeds, the E02-style
gated-memory gain over the no-memory E01 control shrinks toward zero relative to its one-seed
validation-only magnitude (+4.9 points), because a single-seed, single-prefix gap of this size
has not been tested against seed variance.

**Knob or code change.** Already implemented: `publication/code/hgq2/run_engram.py`,
`bnhgq2/engram.py`, eight configs (`configs/engram/index.json`), correctness checks
(`check_engram.py`) — opt-in, does not alter legacy config behavior.

**Hazards.** The memory module has **no HLS lowering** — "the binary export path explicitly
rejects it, preventing an accidental export that omits the learned memory" (own runbook) — so
this card cannot go to synthesis as-is regardless of any accuracy finding; its resource-cost
estimates are explicitly "custom estimates" that "must not be presented as historical native
HGQ2 totals" (`decisions.md:66`), and the combined-cost numbers above inherit that caveat
directly. Its memory tables are multi-bit, not ±1 — a labelled non-binary component if ever
built toward deployment. Permutation-invariant: the address/hash construction is over an n-gram
of constituent features in a fixed order (rank bigrams, per the runbook's design inference) —
**not permutation-invariant** as designed; the runbook itself flags this ("constituent-rank
neighbors are not necessarily spatial neighbors").

**Tried here?** Yes — implemented, correctness-checked, and run to epoch 100 on one seed with a
recorded validation-accuracy result (above); not run to a full seed set, not evaluated on
held-out data, not synthesized, and no arm reached the 350k combined-cost target.

**Combines with.** Nothing else in this family cleanly — it is additive to any backbone choice
above, but its lack of an HLS path means it cannot be combined with anything destined for
synthesis without new export work first.

---

## Omitted and why

- **ParT-style pairwise interaction features (U matrix as an attention bias).** BitParT
  (arXiv:2508.07431) is the direct precedent — it explicitly leaves the pairwise interaction
  pathway untouched even while binarizing the FFN and head, and states no hardware rationale for
  that choice, only a physics-fidelity one. A pairwise feature adds an N×N×(feature) tensor
  computed once per jet and consumed by every attention head — this is a genuinely large
  addition (a new O(N²)-times-features computation, not a modification of an existing one) and
  deserves its own dossier-and-cost pass before a card can honestly state a hazard/EBOPs
  estimate. Flagged for a follow-up card, not written speculatively here.
- **Sun et al.'s `gnn_t` / `QDenseT` LUT-native table variant.** This is architecturally a LUT-
  native design (family adjacent to `literature/INDEX.md` §5, LogicNets/PolyLUT lineage), not a
  binary-weight design — mixing it into the binary-weights Delta would blur the "binary is the
  thesis, everything else is a labelled baseline" rule rather than extend it. Left for a
  separate LUT-native family if Delta ever adds one.
- **A full ParT reproduction as a comparator.** Already covered structurally by A09's Deep Sets
  card and the existing `literature/INDEX.md` note on 2202.03772; a full binary ParT rebuild
  (with pairwise interactions, per-head structure at ParT's original scale) is a much larger
  undertaking than a 12-16 card family should absorb as one entry — the interaction-feature
  piece above is the one part of it worth a dedicated future card.
- **BitNet-b1.58 ternary attention weights specifically inside this family.** Ternary is
  already the standing baseline per project rules (`CLAUDE.md`, "Binary is the thesis; ternary
  is a baseline") and is the subject of a separate quantization family in Delta (family B),
  not architecture — including it here would duplicate that family's scope.

## Log lines to append

(To `research-log.md`, dated 2026-09-26, one line per primary source newly consulted for this
family — the orchestrator appends these once.)

- 2026-09-26 — Wang et al., "Linformer: Self-Attention with Linear Complexity," arXiv:2006.04768,
  https://arxiv.org/abs/2006.04768 — low-rank K/V projection for O(N) attention; full-precision,
  BERT/RoBERTa scale, no binary or FPGA number; transfers as mechanism only (cards A10, A15).
- 2026-09-26 — Lee et al., "Set Transformer: A Framework for Attention-based Permutation-
  Invariant Neural Networks," arXiv:1810.00825, https://arxiv.org/abs/1810.00825 — Pooling by
  Multi-head Attention (PMA), permutation-invariant set pooling; full-precision, generic set
  benchmarks, no binary or FPGA number; transfers as mechanism only (card A07).
- 2026-09-26 — Shazeer, "GLU Variants Improve Transformer," arXiv:2002.05202,
  https://arxiv.org/abs/2002.05202 — gated FFN variants (ReGLU/GEGLU/SwiGLU); full-precision,
  T5/LLM scale, no binary or FPGA number; transfers as mechanism only, and flags a new act×act
  multiply site relevant to the 0-DSP claim (card A13).
- 2026-09-26 — Liu et al., "Bi-Real Net: Enhancing the Performance of 1-bit CNNs...,"
  arXiv:1808.00278, https://arxiv.org/abs/1808.00278 — real-valued shortcut around a binary
  block; ImageNet, 1-bit-weight-and-activation CNNs (our activations are 8-bit, not 1-bit), no
  transformer, no FPGA number; transfers as mechanism only (card A12).
- 2026-09-26 — Zhang & Sennrich, "Root Mean Square Layer Normalization," arXiv:1910.07467,
  https://arxiv.org/abs/1910.07467 — RMSNorm; full-precision Transformer/BERT scale, no binary
  or FPGA number; transfers as mechanism only (card A05).
- 2026-09-26 — Lan et al., "ALBERT: A Lite BERT...," arXiv:1909.11942,
  https://arxiv.org/abs/1909.11942 — cross-layer parameter sharing; BERT scale (110M+ params),
  full precision, no binary or FPGA number; transfers as mechanism only, specifically that
  attention-sharing costs less than FFN-sharing (card A02).
- 2026-09-26 — Que, Sun, et al., "JEDI-linear: Fast and Efficient GNNs for Jet Tagging on
  FPGAs," arXiv:2508.15468, https://arxiv.org/abs/2508.15468 (already noted in
  `literature/jet-tagging-transformers/2508.15468_jedi_linear.md`; re-read for this family) —
  affine-edge, GAP-factored O(N) interaction network, HGQ mixed precision + da4ml synthesis,
  82.4% accuracy / 0 DSP / 79 ns at 64 particles×16 features on VU13P; not a binary-weight
  number, different toolchain — transfers as an architectural mechanism (mean-field pairwise
  approximation) and as evidence that naive O(N²) attention is a real DSP threat at trigger
  scale (card A11).
