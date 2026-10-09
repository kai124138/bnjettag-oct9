# Family P — physics inputs, data and the L1 trigger context

Method cards P01–P12. Every card is a delta from the anchor (`campaigns/2026-09-26-training-batch/STUDY.md`,
arm A: N=64, features `[pt, etarel, phirel]`, pT ≥ 2 GeV gate applied by zeroing then
standardizing, 90/10 split with one `split_seed`, no class/sample weights, learned PE) unless
stated otherwise. Sources read: `DATASET.md`, `docs/conventions/jet-tagging-metrics.md`,
`reference-code/HGQ2-examples/jsc150/data.py`, `reference-code/HGQ2-examples/jsc150/tools/prepare_data.py`,
`bnjettag/code/hgq2/bnhgq2/data.py`, the full PDF of arXiv:2510.24784 (read directly, not the
dossier note, 2026-09-27), `literature/hls4ml-fpga-triggers/2402.01876_*.md`,
`literature/hls4ml-fpga-triggers/1804.06913_*.md`, plus web fetches: full text of
arXiv:2310.08062 (CMS Correlator Layer-2 latency and seeded-cone jets), the Zenodo 3602260
record page, and a search digest (not a fetch) of arXiv:1808.02094 and the L1Phase2NNPuppiTau
CMS TWiki — all dated 2026-09-27; the digest-only sources are flagged as such in their cards.

---

### P01 — Constituent count N as its own cross-N study

**Mechanism.** N is the number of leading-pT constituents fed to the model (8/16/32/64 in the
anchor family; the dataset itself carries up to 150 non-zero constituents per jet, median 46).
Changing N changes the sequence length the transformer attends over and, at fixed EBOPs budget,
trades per-token precision against context (Sun et al. §3, Fig. 1: LUT falls 279k→180k→47k as N
rises 16→32→64 under a fixed EBOPs target because the optimizer spends the budget on bits, not
tokens).

**Why it could matter for binary weights here.** A binary-weight core cannot buy back accuracy
by adding bits per token the way HGQ's per-parameter/per-position widths do; the only free axis
is context length itself. If macro-AUC keeps rising with N under ±1 weights while EBOPs is
matched, that is evidence the binary core's headroom is in tokens, not bits — the opposite of
the mechanism Sun et al. use.

**Primary source.** Laatu, Sun, Cox et al., "Sub-microsecond Transformers for Jet Tagging on
FPGAs," arXiv:2510.24784, NeurIPS ML4PS 2025, §2.1/§3, Table 1, Fig. 1. Accessed 2026-09-26.

**Published effect.** Top-1 accuracy, held-out test set n=260,000, one model per point (no seed
interval stated), iso-EBOPs=350,000 (PID-controlled target, not measured post hoc), read from
their Table 1: MHA 66.3/72.3/77.0/77.9% at N=8/16/32/64 (the N=64 row is a collapsed attention
block, "consistently collapsing... turning it into a Deep Set," §3 — not a transformer result).
Linformer 66.3/72.8/78.4/79.8%. Their own Fig. 1 caption: "the decrease in accuracy for the full
Transformer models compared to other models at 64 particles is expected due to the fixed
resource budget we enforced during training." No prior number for a binary-weight model at
matched EBOPs across N.

**Knob or code change.** `n_constituents` in the data loader (`jsc150/data.py::get_data`,
arg `n_constituents`) or `n_part` in `bnhgq2/eval_loader.py::load_eval_set`. Zero code change;
a config field.

**Hazards.** N=64 sequence length roughly doubles attention MACs vs N=32 (O(N²) for vanilla
MHA); EBOPs accounting and DSP-free claim must be re-checked at each N since act×act MAC count
scales with N². A cross-N sweep at fixed EBOPs is a confound with P02 (gate) and P06 (standardization
statistics, which are computed over the gated set and shift as N changes the padding fraction).

**Tried here?** Anchor STUDY (`campaigns/2026-09-26-training-batch/STUDY.md`) is fixed at N=64
only; `campaigns/2026-09-22-constituent-screen` ran a matched N8/N64 screen but at screen
schedule (50 epochs, LR 2e-4), not comparable to full-schedule numbers per
`jet-tagging-metrics.md` pitfalls. No full-schedule cross-N series exists yet.

**Combines with.** P02 (gate threshold changes effective occupancy per N), P04 (ordering
matters more at large N where more of the tail is real signal vs padding).

**Testable prediction.** Binary-weight macro-AUC will keep improving from N=8 to N=64 (unlike
the archived R14 W1A8 N=64 regression noted in the anchor STUDY, 69.0±3.1% top-1 accuracy vs
FP32 79.1±0.3%, `roc-results/r14/n64/*.npz`), because the pT gate plus the Chang recipe removes
the noisy small-pT tail the R14 pipeline did not gate.

---

### P02 — pT gate threshold (0 / 1 / 2 / 3 GeV)

**Mechanism.** After selecting the top-N constituents by pT, `data.py` zeroes all three
features (`pt`, `etarel`, `phirel`) for any constituent below the gate: `X *= X[..., :1] >= 2`
(raw pt column, threshold 2 GeV, applied **before** the standardization mean/std are computed,
so gated slots pull the feature statistics toward zero along with real low-pT constituents).
The anchor uses 2 GeV; 0/1/3 GeV are untried variants.

**Why it could matter for binary weights here.** A ±1-weight, norm-free network has no
learnable per-channel scale to absorb a shift in input statistics; because the gate changes
the standardization mean/std (gate happens pre-normalization), raising or lowering the
threshold changes what "zero" means to every downstream binary layer, not just how much padding
there is. This is a bigger effect for us than for a full-precision net with per-layer batchnorm.

**Primary source.** `reference-code/HGQ2-examples/jsc150/data.py`, lines 22-31 (verbatim gate
and order-of-operations); Laatu, Sun, Cox et al., arXiv:2510.24784, §2.1/§3 (read in full,
2026-09-27) — "Chang's method" per BRIEF.md, name-checked to author S. Chang / C. Sun's HGQ
paper [30] in their references, not a separate publication of this exact data pipeline.

**Published effect.** No prior number isolating the gate threshold, and no pT-gate mentioned
anywhere in the paper text at all (confirmed by a full read of §§1-4, references and figure
captions, 2026-09-27) — §2.1 states only "The input to the model is a sequence of particles,
with a maximum number of (8, 16, 32, 64) particles sorted by pT... Each particle has three
features: pT, η, and ϕ." No gate, no standardization-order statement. The 2 GeV threshold and
its pre-standardization order-of-operations are read from `jsc150/data.py` code only, never
from the paper. Note also: the paper's three features are literally "pT, η, ϕ," not the
jet-frame-relative `etarel`/`phirel` the anchor recipe and `data.py` actually use (see P05) —
a discrepancy between the paper's stated method and the code we inherited, flagged, not
resolved here.

**Knob or code change.** One line in `data.py`/`bnhgq2/data.py` gate expression, threshold as a
config field (currently hard-coded `>= 2`); estimate 3-5 lines to parameterize plus a config
field.

**Hazards.** None for hardware (the gate is host-side preprocessing, before the FPGA boundary);
hazard is purely statistical — a lower threshold pushes more low-pT junk into standardization
denominators already known to be heterogeneous (DATASET.md: per-feature std spans ~2,979× before
any gating).

**Tried here?** Not tried; only threshold=2 GeV (the anchor default) exists in any config found.

**Combines with.** P03 (mask vs zero-fill — the gate as written *is* zero-fill, so this card is
a special case of P03 with the fill value hard-coded to 0); P01 (interacts with N: at large N
more of the tail is below any reasonable gate).

**Testable prediction.** Raising the gate to 3 GeV lowers macro-AUC (removes real low-pT
constituents from the g/q classes that need multiplicity information most), and lowering it to
0/1 GeV very slightly raises AUC but increases the fraction of near-zero standardized inputs,
which for ±1 weights risks more STE dead zones at the first binary layer.

---

### P03 — Masking vs zero-fill for gated/padded slots

**Mechanism.** The current pipeline treats "below threshold" and "structurally absent" (jet has
fewer than N real constituents) identically: multiply by zero, then standardize. An explicit
mask (a boolean channel, or additive attention-bias masking of padded/gated key positions so
they contribute zero to softmax rather than a learned "zero-but-standardized" embedding) is a
different mechanism: it removes the padding tokens from the attention sum instead of asking the
network to learn that a specific standardized value means "ignore me."

**Why it could matter for binary weights here.** With ±1 weights, the network cannot express a
sharp "if input == pad-value then output 0" gate cheaply; it either wastes capacity learning to
recognize the pad vector or, worse, the pad vector (a fixed z-scored point) drifts as N or the
gate threshold changes (P01, P02), silently changing what the binary weights have converged to
mean. An explicit attention mask sidesteps this in the compute graph rather than in the learned
weights.

**Primary source.** No paper in `literature/INDEX.md` documents masking for this exact pipeline;
this is inferred from `data.py`'s zero-fill order-of-operations (see P02) and from standard
Transformer padding-mask practice (not itself a jet-tagging-specific citation). Flagged: no
domain-specific primary source found for this card; general transformer practice only.

**Published effect.** No prior number.

**Knob or code change.** Add a `key_padding_mask` (or additive bias `-inf` on padded/gated key
positions before softmax) computed from the raw pt column before zeroing; touches the attention
call site in `bnhgq2/qat.py` (per literature/INDEX §3 note on `QMultiHeadAttention`/`QSoftmax`)
and the data pipeline to emit the mask alongside `X`. Estimate 20-40 lines plus a softmax-input
change (masking must survive the table-based `QSoftmax` LUT implementation — see Hazards).

**Hazards.** hls4ml's table-based QSoftmax (exp/inv LUTs, per the Sun-et-al replication note)
was not designed with a runtime mask input; adding one may require an extra multiplexer per key
position, which costs LUTs and could reintroduce a per-position irregularity that breaks
token-axis folding (the same objection raised against Sun et al.'s per-position bitwidths,
`2510.24784` dossier, "What threatens us" #3). This is the main hazard: masking done wrong
un-does the thing that lets us fold identical token instances.

**Tried here?** Not tried; no mask-based variant found in any config or code path searched.

**Combines with.** P02 (mask value vs gate threshold), P01 (fraction of masked slots scales with
N since occupancy is fixed by physics, not N).

**Testable prediction.** Explicit masking raises macro-AUC over zero-fill-then-standardize most
at small N (8/16), where the masked/gated fraction is largest, and the gap shrinks toward zero
by N=64.

---

### P04 — Constituent ordering (pT-sorted vs ΔR-sorted vs random)

**Mechanism.** The anchor and `bnhgq2/eval_loader.py::load_eval_set` sort constituents by
descending pT (`np.argsort(-const[:,:,pt_col], axis=1, kind="stable")`) before truncating to N
and before applying learned positional encoding (PE). An alternative orders by ΔR to the jet
axis (physically closer particles first) or leaves the dataset's native (random/reconstruction)
order.

**Why it could matter for binary weights here.** The anchor's positional encoding is **learned**
(arm A07: "learned PE"), which means the network is asked to associate a position index with a
pT rank, not a physical location; a ±1-weight PE table has very little representational budget
(one bit per weight) to encode a smooth pT-rank-to-embedding map. ΔR ordering ties position to
geometry, which may need less precision to represent because geometric proximity is closer to
what the attention mechanism should be learning to use anyway (softmax over geometric neighbors).

**Primary source.** No paper found that ablates ordering for a binary-weight jet transformer
specifically; the pT-sort convention itself is inherited from `jsc150/data.py`/Sun et al.
(arXiv:2510.24784, "pT-sorted" per §2.1) and from Odagiu et al. (arXiv:2402.01876), who study
Deep Sets/Interaction Networks (both order-invariant by construction, so ordering is a
non-issue for them — this is a hazard flag, see below, not a transferable result).

**Published effect.** No prior number; Odagiu et al.'s permutation-invariant baselines make
ordering moot for their models, so there is no ordering ablation to borrow even qualitatively.

**Knob or code change.** Sort key in `data.py`/`eval_loader.py` (currently hard-coded to the pT
column); add a `sort_by` config field selecting among pt/deltaR/none. Estimate 10-15 lines
(deltaR requires computing distance to the jet axis, already available as constituent feature
index 13, `deltaR`, per DATASET.md's particle feature list — no new physics quantity needed).

**Hazards.** None for HLS/DSP; ordering choice interacts with position encoding (family R) and
must be reported alongside whichever PE variant is used, since PE is what makes ordering visible
to the model at all — an order-invariant pooling (no PE) makes this card moot.

**Tried here?** Not tried; only pT-sorted order found in any config.

**Combines with.** Family R (positional encoding cards): this card is only meaningful paired
with a specific PE choice, and "combines with" is bidirectional — a PE card should name which
ordering it assumes.

**Testable prediction.** ΔR ordering raises macro-AUC over pT ordering specifically at N ≤ 16 (where
learned PE has fewer positions to fit and physical adjacency is a stronger prior than pT rank).

---

### P05 — Feature set: L1-realistic 3-feature vs full 16-feature dataset columns

**Mechanism.** The dataset stores 16 constituent features per particle (px, py, pz, e, erel, pt,
ptrel, eta, etarel, etarot, phi, phirel, phirot, deltaR, costheta, costhetarel — DATASET.md).
The anchor (Chang's recipe) uses 3: `[pt, etarel, phirel]`. Adding features (e.g. `deltaR`,
`ptrel`) gives the network redundant-but-cheap-to-compute derived quantities; removing to a
different 3 (e.g. `[ptrel, etarel, phirel]`, dropping absolute pT) changes whether the network
sees jet-frame-relative-only information.

**Why it could matter for binary weights here.** More input features means more first-layer
±1-weight columns per token, which is compute we control directly (unlike attention, which
scales with N²); this is the cheapest axis to add capacity on if 3 features is genuinely
starving the binary core, and the cheapest axis to cut if input width, not depth, is the
current DSP/LUT driver.

**Why it does NOT map to a real L1 candidate.** What is confirmed from a primary source: a
Correlator-Layer-2 PUPPI candidate list is used for L1 tau identification by taking "the 10
highest transverse-momentum particles and particle ID [one-hot encoded] within a cone of
ΔR < 0.4" (L1Phase2NNPuppiTau, CMS TWiki summary of the Correlator design, accessed
2026-09-27) — establishing that particle ID (one-hot) is carried per-candidate on real
hardware, which no card in this family adds (not stored in the HLS4ML LHC Jet dataset).
**Not confirmed from a primary source in this pass:** a full candidate-field list (PUPPI
weight, charge, z0) — a direct WebFetch of arXiv:2310.08062 (full HTML, 2026-09-27) returned
the latency figures below but did not enumerate PUPPI candidate fields or bit precision; Kreis
et al. arXiv:1808.02094 was not fetched at all in this pass (search-only). The fuller field
list (pt, eta, phi, PUPPI weight, particle ID, charge/z0) matches the task brief's candidate
description, not a source read here — stated as an open item, not a citation, until a primary
TDR or the Correlator Layer-2 firmware paper is read directly. What IS solid regardless of that
gap: none of the dataset's 16 offline-reconstruction features (`erel`, `costhetarel`,
groomed-jet-frame angles) are things any L1 candidate — real or idealized — carries, so no
feature-set choice explored here makes the input L1-realistic in candidate-content, only in
count-and-kinematics (Odagiu et al., 2402.01876, is the source of the 3-feature convention we
inherit; Sun et al. 2510.24784 §2.1, read in full 2026-09-27, uses the same 3-feature-per-particle
count but literally "pT, η, ϕ," not jet-frame-relative quantities — see P02's note on this
discrepancy).

**Primary source.** `DATASET.md` (feature list, this repo, measured 2026-08-01); Zenodo record
3602260, "HLS4ML LHC Jet dataset (150 particles)," M. Pierini, J. M. Duarte, N. Tran,
M. Freytsis, Jan. 2020, DOI 10.5281/zenodo.3602260 (fetched 2026-09-27: confirms the dataset's
identity, derivation from Coleman et al. arXiv:1709.08705, and its use as the basis of
arXiv:1804.06913 and arXiv:1908.05318; does NOT itself enumerate per-particle features on the
record page — DATASET.md's 16-feature list is our own measurement from the HDF5 files, not
copied from Zenodo's page text); Odagiu et al. arXiv:2402.01876 (origin of the pt/etarel/phirel
convention, per literature/INDEX.md); Laatu et al. arXiv:2510.24784 §2.1 (read in full,
2026-09-27); CMS Correlator Layer-2 latency and L1 tau candidate content, arXiv:2310.08062
(fetched in full 2026-09-27) and L1Phase2NNPuppiTau CMS TWiki (search digest only, accessed
2026-09-27).

**Published effect.** No prior number for a binary-weight ablation of feature count; DATASET.md
states the round-14 note that "several constituent-based L1 taggers... use only 3 per particle;
comparisons... are therefore not input-matched to ours" when 16 are used — a caution, not a
result.

**Knob or code change.** `features` argument already exists in `eval_loader.py::load_eval_set`
(`feature_indices` resolves named suffixes); a config list. Zero new code for swapping among
existing 16 columns; adding PUPPI-weight/particle-ID analogs is not possible from this dataset
(not stored) — that would require a different dataset entirely (out of scope, flagged).

**Hazards.** More input features = more first-layer weight columns = more EBOPs at the input
layer specifically (input layer is the one place EBOPs cost scales linearly with feature count,
independent of the binary/DSP question elsewhere).

**Tried here?** Full 16-feature runs exist only in the archived Round 14 pipeline (pre-gate,
80/20 split — not comparable per `jet-tagging-metrics.md`); no full-16 run exists under the
Chang recipe (gate + 90/10 + EBOPs target).

**Combines with.** P02 (gate is defined on the pt column specifically, so feature-set changes
must keep pt in the set or the gate needs redefining), P06 (standardization applies per chosen
feature).

**Testable prediction.** Adding `deltaR` and `ptrel` to the 3-feature set raises macro-AUC over
3 features by more at N=8 than at N=64, because at N=8 the 3-feature set already discards the
information a longer sequence would otherwise recover through more tokens.

---

### P06 — Input standardization: scope and order relative to the gate

**Mechanism.** `data.py` computes `scale`/`shift` as the per-feature mean/std over the **gated,
padded** train array (`np.std/mean(X_train_val, axis=(0,1))`, i.e. including the zeroed
below-gate and structurally-absent slots), then applies the same statistics to train, val and
test. `bnhgq2/data.py::input_std_stats` states explicitly this is computed "on the TRAIN split
ONLY... the reference practice of the HGQ2 examples." An alternative computes statistics only
over the **non-gated, real** slots (masking zeros out of the mean/std computation).

**Why it could matter for binary weights here.** Standardization sets the operating point every
downstream ±1-weight layer sees; because zeros are folded into both mean and std today, the
"gated/absent" population (which is large — DATASET.md: mean 49.4 real constituents out of up to
150, and P02's gate removes still more) systematically shrinks the std and shifts the mean
toward zero relative to a real-slots-only statistic. For a network with no per-layer scale
recovery mechanism this changes the effective input dynamic range presented to the sign
function at every binary layer.

**Primary source.** `bnhgq2/data.py` (this repo, `input_std_stats`/`apply_input_std`,
research-log 2026-07-17 per its own docstring); `jsc150/data.py` lines 28-31 (verbatim
order: gate, then `np.std`/`np.mean` over the gated array).

**Published effect.** No prior number isolating this choice; it is not discussed in either
source as an ablation, only stated as the implementation.

**Knob or code change.** A boolean flag in `input_std_stats` to compute over a boolean mask of
real (non-gated) entries instead of the full array; estimate 10 lines (mask construction +
`np.ma` or manual masked mean/std).

**Hazards.** None for hardware — standardization stats are baked into fixed-point constants at
export time either way; hazard is purely about whether the constants match the population the
model will actually see at inference (real L1 candidates are never "zeroed-then-passed-through";
they are absent, i.e. the deployed system's slot-filling convention needs to match whichever
statistic training used).

**Tried here?** Not tried as an ablation; the gated-inclusive statistic is the only one in any
code path found.

**Combines with.** P02, P03 (masked-slots-only standardization is the natural pairing with
explicit masking in P03, since both then treat "absent" consistently in the stats and in the
attention op).

**Testable prediction.** Real-slots-only standardization raises macro-AUC over the current
gated-inclusive statistic, with the largest gap at N=64 (highest absent-slot fraction).

---

### P07 — Input bit-width (the ADC/quantization step before the first binary layer)

**Mechanism.** Standardized floats are cast to `float16` for storage (`data.py` line 33;
`bnhgq2/eval_loader.py` casts to `float32`), then, at the HLS boundary, to a fixed-point input
width set by the model's quantizer, not by data.py. This card is about that fixed-point input
width specifically (e.g. 8-bit vs 6-bit vs 4-bit inputs to the first BitLinear layer), separate
from the weight/activation widths inside the network that the anchor's EBOPs target already
covers.

**Why it could matter for binary weights here.** BNJetTag's two stated axes are tagging
efficiency and how far *activations* can be pushed (A8→A6→A4, per project-context.md); the
**input** width is the first activation in that chain and has not been named as its own axis
anywhere read. If input precision is already the bottleneck (e.g. `etarel`/`phirel` need more
than 4-6 bits of dynamic range to separate g/q at the tails), no amount of internal
activation-width search recovers it.

**Primary source.** No dedicated ablation found; inferred from the A8→A6→A4 framing in
`.claude/memory/project-context.md` and from BitNet a4.8 (arXiv:2411.04965, "prior art for
pushing activations to 4 bits — our A4 arm," per literature/INDEX.md §1), which treats the
first-layer input quantization as part of the same activation ladder for an LLM, not a
constituent-jet input — flagged as a scale mismatch (LLM activation vs a 3-wide physics input).

**Published effect.** No prior number for this exact input-width ablation on this dataset.

**Knob or code change.** Input quantizer bit-width config field at the model's input layer
(wherever the A8/A6/A4 sweep is already implemented per the anchor's "learned activation widths
from 8-bit init" — same mechanism, applied to the input tensor specifically rather than only
internal activations). Estimate: a config value if the mechanism already generalizes to the
input tensor; otherwise a few lines to expose it.

**Hazards.** Input width below internal activation width could make the input the accuracy
floor regardless of what the rest of the network does — a diagnostic hazard (wasted sweep budget
on internal widths) more than an HLS hazard, since narrower input width strictly helps LUT/DSP.

**Tried here?** Not tried as an isolated axis; folded implicitly into whatever the anchor's
"learned activation widths from 8-bit init" already does to the input layer (unconfirmed without
reading the model code — flag for ml-engineer's code-surface inventory).

**Combines with.** P05 (more features at lower per-feature bit-width vs fewer features at higher
bit-width is a capacity-allocation question), P06 (standardization scale determines how much
dynamic range the quantizer must cover).

**Testable prediction.** Macro-AUC degrades sharply below 6-bit input width specifically for the
g/q pair, because that boundary is already the hardest per-class decision at full precision in
every g/q number seen in this pass — Sun et al.'s own per-class AUC at n=8 has g (0.853-0.854)
and q (0.886) as the two lowest of five classes (Fig. 2a, arXiv:2510.24784, read 2026-09-27,
their metric/model/data, not compared numerically to ours here), and the pt-weighting study's
per-class breakdown independently found gluon the most sensitive class to a training-distribution
change (−0.028, largest of five, `.claude/memory/experiment-log.md` 2026-09-26) — two different
perturbations both landing hardest on gluon is the basis for this prediction, not a claim that
either number transfers to a bit-width ablation.

---

### P08 — Train/validation split fraction (90/10 vs 80/20) and the validation-SE argument

**Mechanism.** The anchor STUDY deliberately deviates from the house convention (80/20,
validation n=124,000) to 90/10 (validation n=62,000, `val_size=0.1`) "for fidelity to
`jsc150/data.py`" (anchor STUDY.md line 432). Larger train fraction gives more training data at
fixed total (620,000 train+val); smaller validation fraction gives a noisier model-selection
signal.

**Why it could matter for binary weights here.** Binary-weight training is reported elsewhere
in this repo to have a wider seed spread than full precision (R14 N=64 W1A8: 69.0±3.1% top-1 vs
FP32 79.1±0.3%, anchor STUDY.md line 63) — if the *selection* signal (validation AUC) is itself
noisier from a smaller validation set, seed-to-seed variance in which checkpoint gets selected
compounds with the training variance already documented, potentially inflating the reported
spread for a reason that has nothing to do with the binary weights themselves.

**Primary source.** Anchor STUDY.md itself (`campaigns/2026-09-26-training-batch/STUDY.md`,
lines 76, 136, 147-150, 432, 638-640, "DECISION: split 90/10 ... cost is selection noise,
binomial SE ... ALTERNATIVES: house 80/20 (n_val 124,000; SE about 0.12 pt, closer to existing
caches)"); `jet-tagging-metrics.md` (house 80/20 convention, `n_validation` from
`publication/results/post_conference/ablation_metrics.json`).

**Published effect.** Anchor STUDY.md quotes its own binomial SE estimate for validation
selection noise at 90/10 (n_val=62,000) vs 80/20 (n_val=124,000, "SE about 0.12 pt"); this is
the anchor's own pre-registered number, not an external citation — flagged as such, and it is a
selection-noise estimate, not a measured AUC gap between splits.

**Knob or code change.** `val_size` config field, already exists (`get_data(val_size=0.1)`).
Zero code change.

**Hazards.** None for hardware; a pure statistics/selection-methodology question. Changing split
fraction after seeing results would be a selection-rule violation per `jet-tagging-metrics.md`
check 4 ("selection was on validation; the held-out set was touched once, at the end") — any
split-fraction study must pre-register both arms before touching ROC-test.

**Tried here?** The anchor uses 90/10 by design decision (not an ablation); no matched 80/20 run
at the Chang recipe (gate + EBOPs target) exists to compare against.

**Combines with.** Every other card in this family, since split fraction determines n_train for
all of them; should not be swept simultaneously with anything whose effect size is comparable to
the ~0.12-pt selection-noise estimate above (per `jet-tagging-metrics.md`'s "seed sd... 0.0013 to
0.0016" bar for when 8 seeds are needed).

**Testable prediction.** At matched seed count, 80/20 selection produces a smaller spread in
*which epoch* is selected across seeds than 90/10, but the two splits' seed-averaged held-out
AUC do not differ outside the existing seed-sd (no true accuracy effect, only a selection-noise
effect).

---

### P09 — Physics-motivated augmentation: η-φ frame rotations/reflections

**Mechanism.** The jet-frame relative coordinates (`etarel`, `phirel`) are, by construction,
rotation- and reflection-covariant around the jet axis in a way the underlying physics does not
distinguish (a jet's substructure classification should not depend on an arbitrary azimuthal
rotation of the jet-frame axes, or on a φ→−φ reflection). Augmentation applies a random rotation
angle and/or reflection to `(etarel, phirel)` pairs per jet at train time, expanding the
effective training set without new physics.

**Why it could matter for binary weights here.** Binary-weight training's documented wider seed
spread is consistent with the network locking onto spurious features early (STE gradients are a
biased estimator); augmentation is a well-established variance-reduction and generalization tool
that costs nothing at inference (it only touches the training loop, not the exported model), so
it is one of the few candidate fixes for the seed-spread problem that carries zero hardware risk.

**Primary source.** No paper in `literature/INDEX.md` documents this augmentation for this
dataset specifically; this is a physics-symmetry argument (jet substructure classification is
expected to be azimuthally symmetric and, absent detector charge asymmetries, φ-reflection
symmetric) rather than a citation of a demonstrated result. Flagged: no primary source measuring
this exact augmentation's effect exists in the literature tree searched.

**Published effect.** No prior number.

**Knob or code change.** A data-loader-side transform applied per training batch (rotate/reflect
`etarel`/`phirel` jointly, leave `pt` unchanged); estimate 15-25 lines in the training data
pipeline (must NOT touch the held-out ROC-test evaluator, `bnhgq2/eval_loader.py`, which stays
byte-identical per its own docstring contract).

**Hazards.** None for HLS/hardware (train-time only, model architecture and exported weights are
unaffected by an augmentation policy). Must coordinate with P04 (ordering by pT is rotation
invariant, so this augmentation is compatible with the pT-sort convention without additional
change) and must not touch `etarot`/`phirot` columns (already-rotated dataset columns distinct
from the `etarel`/`phirel` this card augments — DATASET.md's 16-feature list has both; a
careless implementation could double-rotate).

**Tried here?** Not tried; no augmentation code found in any data pipeline searched.

**Combines with.** P08 (an augmentation that effectively multiplies train-set diversity weakens
the case for spending split fraction on train over validation), family Q/O (regularization
methods) as an alternative variance-reduction lever for the same seed-spread problem.

**Testable prediction.** Rotation/reflection augmentation narrows the seed-to-seed spread of
held-out macro-AUC (not necessarily the mean) relative to the un-augmented anchor, most visibly
at N=8 where the model has the least data-effective capacity to average out noise on its own.

---

### P10 — Label/class set: 5-class macro-OvR is fixed; naming what a variant would be

**Mechanism.** The benchmark task is fixed at 5 classes (g/q/W/Z/t, one-hot, macro-OvR AUC per
`jet-tagging-metrics.md`). A variant collapsing classes (e.g. binary quark/gluon vs boosted W/Z/t,
or merging W+Z into a single "vector boson" class) is a **different task**, not a method choice
within this one; it changes what "AUC" even numerically means (a 2-class or 3-class macro-OvR AUC
is not comparable to the 5-class number anywhere in this repo's record).

**Why it could matter for binary weights here.** Not a binary-specific question; recorded here so
Delta does not silently propose a class-set change as if it were a hyperparameter. If a future
study wants "does binary hurt more on the hardest class pair" that is a per-class AUC breakdown
of the existing 5-class task (already required by `jet-tagging-metrics.md` check 5: "a class
under 0.7 is called out"), not a new label set.

**Primary source.** `docs/conventions/jet-tagging-metrics.md` ("Labels are one-hot... Two numbers
are comparable only at the same N, input set, split, schedule and selection rule" — class set is
implicitly part of that list); `DATASET.md` (jet feature columns 53-58: g/q/w/z/t/undef, the
fixed label vector).

**Published effect.** N/A — this card documents a boundary, not a method with an effect size.

**Knob or code change.** None recommended; if pursued, it is a new evaluation script (label
remapping before `roc_auc_score`), not a training change, and it must be reported as a separate
task, never folded into a 5-class comparison table.

**Hazards.** The main hazard is methodological, not hardware: silently reporting a merged-class
AUC next to 5-class AUC would violate the "never invent a number... comparable only at the same...
[class set]" rule directly.

**Tried here?** No class-set variant found in any config or result searched.

**Combines with.** Nothing in Delta; flagged as out of scope for the ~100-method catalogue
unless the orchestrator explicitly wants a second benchmark task.

**Testable prediction.** A merged W+Z ("vector boson") class scores a macro-OvR AUC above
either separate class's five-class per-class AUC (since the model no longer has to resolve the
W/Z confusion at all), which is exactly why that number could not be placed in a 5-class
comparison table — the direction of the effect is what makes it a different task, not a
stronger result.

---

### P11 — pT sample reweighting (tried, verified negative)

**Mechanism.** Per-class inverse-pT-density sample weights (100 pT bins, cap at 5× or no cap) applied
during training loss, intended to flatten the effective pT spectrum the network trains on and
reduce reliance on the raw pT feature as a shortcut for class separation.

**Why it could matter for binary weights here.** No binary-specific mechanism — this is a loss-
weighting change, orthogonal to weight precision; recorded because a naive reading of Delta
brief's candidate list would re-propose it.

**Primary source.** `local/2026-09-25-pt-weighting/` (STUDY→VERIFY chain), logged in
`.claude/memory/experiment-log.md` 2026-09-26 ("Does pT sample re-weighting help the N=8 W1A8
tagger?").

**Published effect (ours, not external).** Held-out macro-OvR AUC, N=8 W1A8, ROC-test n=260,000,
seed-averaged over 8 seeds: BASE 0.8711±0.0013, PTW5 (cap 5) 0.8603±0.0019, PTWNC (no cap)
0.8587±0.0020; paired PTW5−BASE −0.0108 [−0.0124, −0.0093] (95% t-interval, df=7), 8/8 seeds
lower. Per-class: every class worse, gluon most (−0.028); the gain the reweighting scheme
targeted (tails) did appear (bin 1 +0.0047, bin 6 +0.0165, 8/8) but was outweighed by losses in
the pT centre. Source: `.claude/memory/experiment-log.md` 2026-09-26 entry, `VERIFY.md` in
`local/2026-09-25-pt-weighting/`, recomputed independently twice (results-analyst and "newton").

**Knob or code change.** Already implemented: `bnhgq2/pt_weights.py`, `train.pt_weights` config
field.

**Hazards.** None new (mechanism already characterized); flagged here only so Delta does not
re-propose it as untried.

**Tried here?** Yes — verified negative, N=8, W1A8. Not yet tried at N=64 or under the Chang/EBOPs
recipe; the anchor STUDY explicitly leaves "N=16" and "an end-weighted scheme" open
(experiment-log interpretation line).

**Combines with.** P01 (untested at N=64), P08 (reweighting redistributes effective sample count
across pT, which interacts with how much the 90/10 vs 80/20 split fraction matters per class).

**Testable prediction.** An end-weighted scheme (reweight only the extreme pT sextiles, leave the
centre at weight 1) recovers the tail gains (bin 1/6) without the centre loss that made PTW5/PTWNC
net negative — this is the specific untried variant the existing result points to, not a repeat of
PTW5/PTWNC.

---

### P12 — Figure of merit: macro-OvR AUC / top-1 accuracy vs background rejection at fixed signal efficiency

**Mechanism.** This is not a training-time method but a question about what Delta's ~100
methods should be scored on. AUC integrates a ROC curve over every threshold; accuracy uses a
single argmax threshold implied by the softmax; an L1 trigger runs each tagger at one operating
point set by a fixed output rate budget, so the physics-relevant number is signal efficiency at a
fixed background (mistag) rate, or equivalently background rejection (1/mistag) at a fixed signal
efficiency.

**Why it could matter for binary weights here.** `jet-tagging-metrics.md` already names
background rejection at signal efficiency 0.5 as a required-when-asked metric, and states
"accuracy... and AUC... rank models differently" (constituent study 2026-09-16 citation in that
file). A ranking that holds for AUC but flips at the L1 operating point would mean Delta's
~100-method ranking is optimizing the wrong axis; this card does not propose a code change, it
flags that every method card's "published effect" and every future study's headline number should
be paired with a working-point number wherever the `.npz` (`y`, `score`, shape `(n,5)`) is
available, per this campaign's owning-agent brief (BNJetTag physicist role, not restated here).

**Primary source.** `docs/conventions/jet-tagging-metrics.md` ("Background rejection at signal
efficiency 0.5 when a working point is asked for; `publication/results/pre_conference/
working_points.json` has the recorded ones"; "Accuracy... reported beside AUC, never instead of
it... the two rank models differently"). CMS L1 trigger context for why a fixed operating point
is the physically meaningful one: the Phase-2 L1 system runs at a fixed overall decision-latency
budget — confirmed by a full fetch of arXiv:2310.08062 (2026-09-27, "Reconstructing jets in the
Phase-2 upgrade of the CMS Level-1 Trigger with a seeded cone algorithm"): total L1 decision
latency ≈12.5 μs, of which ≈5 μs is charged-track/calorimeter/muon reconstruction and ≈1 μs each
is allocated to the two Correlator layers; their seeded-cone jet reconstruction specifically
closes at 720 ns (first input to first output jet) + 138 ns serial transmission, inside the 1 μs
Correlator-Layer-2 budget. A trigger algorithm runs at one threshold set by the L1 accept rate,
not integrated over all of them, which is the physics reason AUC alone is an incomplete figure
of merit for this deployment target.

**Published effect.** No prior number computed for this campaign; `working_points.json` (if
populated) is the source to read before any card's numbers get compared at a working point rather
than AUC — not read in this pass (out of scope for this family's file-list; flagged for the
figure-of-merit question, not answered with a number here per BRIEF's "no change to the
pre-registered metric of the anchor study").

**Knob or code change.** None — an analysis-time recomputation from stored `(y, score)` arrays,
not a training or architecture change. `roc_curve` per class at the chosen background-rejection
target.

**Hazards.** None for hardware. The hazard is entirely one of interpretation: a Delta ranking
built only on AUC could promote a method that wins on AUC but loses efficiency at the rate the L1
system actually runs at, exactly the flip this family's owning discipline (physicist) is
responsible for catching per this campaign's method-card rules.

**Tried here?** Not computed in this pass; `working_points.json` existence and content unread —
flagged for whoever runs the first per-card comparison to check before quoting AUC alone.

**Combines with.** Every card in every family; this is a scoring-axis question, not a method to
combine with others.

**Testable prediction.** For at least one pair of methods in Delta, the AUC ranking and the
background-rejection-at-fixed-efficiency ranking will disagree (direction unknown in advance;
this is the prediction that the two metrics are not interchangeable for this task, per the
already-cited 2026-09-16 constituent-study precedent where accuracy and AUC already disagreed).

---

## Omitted and why

- **Jet-image (calorimeter-image) inputs.** The dataset carries `jetImage`/`jetImageECAL`/
  `jetImageHCAL` (DATASET.md), but every model in this repo and the anchor recipe is
  constituent-list-based; a CNN-on-images branch is a different architecture family, not an
  input-family delta, and is out of scope for family P (would belong with an architecture family
  if pursued at all).
- **Full 150-constituent, no truncation.** DATASET.md shows up to 150 real constituents per jet;
  running N=150 is a valid point on the P01 axis in principle but is not part of the anchor's
  N∈{8,16,32,64} family and would need its own EBOPs/latency budget reasoning (almost certainly
  infeasible under any L1 latency budget); noted, not carded, to avoid implying it is a live
  candidate.
- **Track-quality / z0 as an added feature.** The real L1 PUPPI candidate carries a z0-adjacent
  quantity for charged particles (per the CMS Correlator sources cited in P05); the public
  HLS4ML LHC Jet dataset does not store this quantity at all, so no feature-set card here can add
  it. This is the clearest single fact establishing that no configuration in family P is fully
  L1-candidate-realistic in content, only in count/kinematics — stated once here rather than
  repeated in every card.
- **Different dataset entirely (e.g. JetClass, arXiv:2202.03772).** Out of scope: the brief and
  every convention file fix the public HLS4ML LHC Jet 5-class set as the benchmark; a
  different-dataset card would not be a "method," it would change the whole study.
- **Domain-adaptation / simulation-vs-data augmentation.** No primary source in the literature
  tree addresses this for the HLS4ML LHC Jet dataset (it is simulation-only, no data comparison
  exists to adapt to); omitted as not applicable to this benchmark.

## Log lines to append

(Dates below follow the task instruction: date 2026-09-26 for every line; sources were fetched
2026-09-27.)

- 2026-09-26 — Laatu, Sun, Cox et al., "Sub-microsecond Transformers for Jet Tagging on FPGAs,"
  arXiv:2510.24784 (accessed 2026-09-27, full PDF read, §§1-4 + references + figures) —
  https://arxiv.org/abs/2510.24784 — for Delta family P (N-series, gate, feature-set
  cards P01/P02/P05): confirms §2.1's stated input is "pT-sorted... three features: pT, η, and
  ϕ" with NO pT-gate mentioned anywhere in the text — the gate and its order-of-operations
  relative to standardization come from `jsc150/data.py` code only, not this paper. Also
  surfaces a discrepancy: the paper's stated features are plain η/ϕ, not the jet-frame-relative
  etarel/phirel the anchor recipe's code actually uses.
- 2026-09-26 — Odagiu et al., "Ultrafast jet classification at the HL-LHC," arXiv:2402.01876
  (accessed 2026-09-27, dossier note re-read) — https://arxiv.org/abs/2402.01876 — origin of the
  3-feature (pt, etarel, phirel) L1-realistic input convention (P05); their Deep Sets/Interaction
  Network baselines are permutation-invariant, so the paper has no ordering ablation to transfer
  to P04 — noted as a gap, not a result.
- 2026-09-26 — M. Pierini, J. M. Duarte, N. Tran, M. Freytsis, "HLS4ML LHC Jet dataset (150
  particles)," Zenodo record 3602260 (accessed 2026-09-27, record page fetched directly) —
  https://zenodo.org/records/3602260 — confirms dataset identity and derivation from Coleman et
  al. arXiv:1709.08705, and that it underlies arXiv:1804.06913/1908.05318; the record page does
  NOT itself enumerate per-particle features — DATASET.md's 16-feature list is this repo's own
  HDF5 measurement, not copied from Zenodo text (P05).
- 2026-09-26 — CMS, "Reconstructing jets in the Phase-2 upgrade of the CMS Level-1 Trigger with a
  seeded cone algorithm," arXiv:2310.08062 (accessed 2026-09-27, full text fetched) —
  https://arxiv.org/abs/2310.08062 — confirms total L1 decision latency ≈12.5 μs, ≈5 μs for
  track/calorimeter/muon reconstruction, ≈1 μs per Correlator layer, and their seeded-cone jet
  algorithm closing at 720 ns + 138 ns serial transmission inside the Correlator-Layer-2 budget —
  used in P12 for why a fixed operating point, not integrated AUC, is the deployment-relevant
  figure of merit. Did NOT confirm a PUPPI-candidate field list or bit precision — that claim in
  P05 is flagged as unconfirmed by a primary source in this pass (search digest only for
  arXiv:1808.02094 and the L1Phase2NNPuppiTau CMS TWiki; neither was read in full).
