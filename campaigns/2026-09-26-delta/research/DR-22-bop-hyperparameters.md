# DR-22 — Bop optimizer hyperparameters (γ, τ)

Source: Helwegen, Widdicombe, Geiger, Liu, Cheng, Nusselder, "Latent Weights Do Not Exist:
Rethinking Binarized Neural Network Optimization", NeurIPS 2019, arXiv:1906.02107v2 (fetched
PDF, 12 pp., 2026-09-27). Cross-checked against the official Larq implementation
`larq/larq`, `larq/optimizers.py`, `class Bop` (fetched from `master` branch,
2026-09-27; repo `HEAD` = `3d7de8832a477285bbf3c36252e24fcb9299a959`; latest tag at fetch
time `v0.9.6` = `04ea8153ef10484dab68873cfe3ea37db5615ca4`; the constructor defaults shown
below are unversioned in the file I read — no tag pin was fetched, flagged below).

## 1. Every γ/τ value in the paper, per experiment

**§5.1, Figure 1 — hyperparameter sweep, BinaryNet on CIFAR-10, 100 epochs.**
Two panels, both varying one hyperparameter with the other fixed:
- Left panel: γ ∈ {10⁻², 10⁻³, 10⁻⁴}, τ fixed at 10⁻⁶.
- Right panel: τ ∈ {0, 10⁻⁶, 10⁻⁵}, γ fixed at 10⁻³.
Qualitative finding stated in text: both high γ and low τ increase flip rate and cause
rapid-but-noisy early learning that plateaus low; (γ, τ) = (10⁻², 10⁻⁶) and (10⁻³, 0) are
called out by name as "aggressive" settings whose validation accuracy becomes volatile and,
for τ = 0, deteriorates over time. No single pair is recommended from this sweep; it is
presented purely to show the qualitative γ/τ trade-off, not a working point.

**§5.2 — CIFAR-10 benchmark, BinaryNet/VGG-style (Courbariaux et al. architecture), 500
epochs, batch 50, NVIDIA Tesla V100.**
γ = 10⁻⁴, **decayed by 0.1 every 100 epochs**; τ = 10⁻⁸ (fixed, no decay stated). Adam
(recommended β₁, β₂, ε defaults) used for the real-valued BatchNorm variables only, with
initial LR α = 10⁻². Result: Bop 91.3% top-1 test vs Adam-with-latent-weights baseline
90.9% (baseline itself LR-tuned + Xavier-scaled, per [1]/[8] recipe). — Figure 2, Table
none (numbers stated in prose, §5.2).

**§5.3 — ImageNet, BinaryNet / XNOR-Net / BiReal-Net, batch 1024.**
τ = 10⁻⁸ (fixed, "same optimizer hyperparameters" across all three networks); γ **decayed
linearly from 10⁻⁴ to 10⁻⁶** over training. BinaryNet and BiReal-Net trained 150 epochs,
XNOR-Net 100 epochs. Real-valued variables (scaling factors, first/last layer weights)
use Adam with LR linearly decaying 2.5×10⁻³ → 5×10⁻⁶, β₁=0.9, β₂=0.999, ε=10⁻⁷; XNOR-Net
additionally gets 5×10⁻⁷ L2 on its real-valued first/last layer. Results in **Table 1**:
BinaryNet 41.1%/65.4% (top-1/top-5), XNOR-Net 45.9%/70.0%, BiReal-Net 56.6%/79.4%
(Bop), vs their latent-weight literature baselines 40.1/66.3, 44.2/69.2, 56.4/79.5.

**No other γ/τ values appear** (no ablation table beyond Figure 1; the discussion in §6
proposes γ-decay and layerwise/adaptive τ as *future work*, not as a value used).

## 2. γ decay schedule — explicit statements only

- CIFAR-10 (§5.2): step decay, ×0.1 every 100 epochs, starting from γ=10⁻⁴.
- ImageNet (§5.3): linear decay, 10⁻⁴ → 10⁻⁶ over the full training run (150 or 100 epochs
  depending on network).
- τ is **never decayed** in either benchmark; only γ is scheduled.
- §6 (Discussion) explicitly flags γ-decay-as-learning-rate-analogue and τ-scheduling
  (start high, lower over training) as *unexplored, hypothesised* directions, not
  demonstrated results. Quoting numbers from §6 as "recommended" would be wrong — it is a
  research-agenda paragraph, not a result.

## 3. Larq official defaults (`larq.optimizers.Bop`)

```
class Bop(Optimizer):
    def __init__(self, threshold: float = 1e-8, gamma: float = 1e-4, name: str = "Bop", **kwargs):
```
`threshold=1e-8`, `gamma=1e-4` — source: `larq/larq` `larq/optimizers.py`, lines 314-316
of the fetched file (fetched from `master`, commit `3d7de8832a477285bbf3c36252e24fcb9299a959`;
I did not pin to a released tag, so these are the current-`master` defaults, not
necessarily what shipped in a specific PyPI release — flag this if an exact release
citation is needed later). These match the paper's CIFAR-10 τ and initial γ exactly
(τ=10⁻⁸, γ=10⁻⁴), i.e. Larq's constructor defaults are literally the CIFAR-10 §5.2
starting values with no built-in decay schedule (decay is left to the caller via a
`LearningRateSchedule` object, per `_get_decayed_hyper`, lines 326-331). The docstring
itself carries a caveat we should keep: "Note that the default `threshold` is not optimal
for all situations. Setting the threshold too high results in little learning, while
setting it too low results in overly noisy behaviour" (lines 284-286) — Larq is not
claiming these are tuned for anything but a starting point.

Larq's update rule (`_resource_apply_dense`, lines 332-341) implements the flip as
`var_t = sign(-sign(var * m_t - threshold) * var)`, which is algebraically the same
condition as Algorithm 2 (`|m_i| > τ` and `sign(m_i) == sign(w_i)` ⇒ flip) written as a
single sign expression rather than a masked select, and it flips to the literal negation
`-var` (no latent, no scale) exactly as the paper's Algorithm 2 does — confirming Larq's
Bop has no `alpha`/`beta` bookkeeping at all, unlike our re-implementation (§5).

## 4. Which setting is closest to our case

Our case: a small binary-weight transformer (not BinaryNet/XNOR/BiReal, no binary
activations — ours are W1A8, i.e. only the weights are `{-1,+1}`), Adam already running on
every non-binary variable, Bop confined to the binary latents only, on the anchor's
batch 2,790 / 7,000-epoch / cosine-restart schedule (BRIEF, wave-0 anchor A07-N64). The
paper gives no parameter count for its BNNs, so no weight-count comparison to our anchor
is possible from this source; what can be said is architecture: none of the paper's three
benchmarks (Fig. 1 sweep, CIFAR-10 §5.2, ImageNet §5.3) was run on a transformer, on W1A8
(the paper's BNNs are W1A1 throughout — see the transfer caveats below), or under anything
resembling our schedule (batch 2,790 vs. their 50/1024; 7,000 epochs with cosine restarts
vs. their 500/150/100 epochs with plain step or linear decay).

Both full benchmarks (CIFAR-10 §5.2 and ImageNet §5.3) actually agree on τ=10⁻⁸ and start
γ at 10⁻⁴ — identical to the Larq constructor defaults; the only thing that differs
between them is the *shape* of the γ decay (step ×0.1/100 epochs vs. linear over the run).
So "which paper setting is closest" is close to a non-question at the level of the raw
numbers: τ and γ₀ are the same triple everywhere in the source. What does not transfer is
the schedule, because γ is a per-step EMA rate — its effective averaging horizon is
≈1/γ *steps*, not epochs — and the paper's epoch-denominated decay schedules were tuned
for batch sizes (50, 1024) that are 1-2 orders of magnitude off our batch 2,790, so the
same epoch-based decay implies a very different step-based decay for us. Any schedule we
port must be recalibrated in steps, not copied in epochs.

τ is worse: the paper is explicit that "the threshold... introduces a dependency on the
absolute magnitude of the gradients" (§6, Discussion) — it is not a normalized quantity.
Our `g` in `bop.py` is the bounded-STE pseudo-gradient after the optimizer's `clipvalue`
(bop.py lines 17-18), which is not the same gradient pipeline the paper trained under
(different loss scale, different clip, different architecture). τ=10⁻⁸ carries no
guarantee of being in the right units for our `m`. **No paper τ or γ value should be
quoted as validated for our setup**; treat 10⁻⁸/10⁻⁴ (paper's and Larq's shared starting
pair) as a scan seed only, and have the wave STUDY measure the empirical `|m|` distribution
on the anchor's binary latents (a few hundred steps, Adam-only or with a provisional τ=0)
before fixing τ, since that tells us the native scale of `g` in this pipeline rather than
assuming the paper's scale applies.

## 5. Semantics check against our `bop.py`

Our re-implementation (`campaigns/2026-09-26-delta/code/newmods/bop.py`, read
2026-09-27):
```
m = (1 - gamma) * m + gamma * g_t          # line 77
alpha = mean(variable); q = sign(variable - alpha)   # lines 78-79 — current binary weight
flip if |m| > tau and sign(m) == q                    # line 80
w_i <- 2*alpha - w_i on flip                          # line 81
```
Matches the paper's Algorithm 2 / Eq. (5)-(6): `m_t = (1-γ)m_{t-1} + γg_t` (Eq. 5) and
"flip if `|m_i| > τ` and `sign(m_i) == sign(w_i)`" (Algorithm 2's pseudocode). Note a small
inconsistency in the paper itself: Eq. (6) is stated with `|m_t^i| ≥ τ` (non-strict) while
Algorithm 2's pseudocode uses `|m_i| > τ` (strict); our code uses strict `>` (bop.py line
80), matching Algorithm 2, not Eq. 6. The two forms only disagree exactly at `|m|=τ`, a
measure-zero case in practice — flagged for completeness, not consequential. The paper's
`sign(w_i)` (as used in Algorithm 2 and Eq. 6) is the *current* binary
weight before this update (`w_{t-1}` in Eq. 6's own notation) — exactly what our `q =
sign(variable - alpha)` computes from the latent each step, since our forward pass defines
the binary weight the same way (BitNet-style `bipolar_sign(w - alpha)`). One deliberate
deviation, called out in our own docstring (bop.py lines 12-16): the paper's Bop has *no*
latent weight and *no* magnitude at all — flipping literally negates `w_i` in `{-1,+1}`
space (Algorithm 2: `w_i ← -w_i`). Our re-implementation keeps a real-valued latent and
reflects it about the mean (`w_i ← 2α - w_i`) so that `beta = mean|w-α|` (our layer scale)
survives the flip to first order. This is a genuine, acknowledged extension beyond the
paper's Bop (which has no scale/beta concept because it operates on plain `{-1,+1}`, not
BitNet's affine-then-binarize scheme) — not an error, but it means "Bop" in our pipeline
is Bop's flip *rule* applied inside a latent-weight/beta scheme the paper explicitly
argues against needing (§3, "Latent Weights Do Not Exist"). Flag for the wave STUDY:
this hybrid has not been validated against the paper's no-latent Bop, so its behaviour at
the paper's γ/τ values is not guaranteed to transfer even qualitatively — the flip
condition is byte-for-byte the same, but the state (`m` lives in Adam's momentum slot,
confirmed lines 20-22/76) and the update's effect on `beta` are our own addition.

## Transfer caveats (do not drop these when citing)

- Paper's BNNs are **W1A1** (binary weights *and* activations) on CIFAR-10/ImageNet conv
  nets; our anchor is a **transformer, W1A8** (binary weights, 8-bit activations). Bop's
  γ/τ tuning was never exercised on a transformer or on this activation width.
  Gradient noise characteristics driving the γ/τ trade-off could differ.
- Scale and optimizer context differ: paper trains **only BatchNorm scalars** with Adam
  alongside Bop; we train a much larger set of non-binary variables (norm scales, biases,
  learned activation widths, PE) with Adam alongside Bop on the binary latents only.
- No batch-2790/cosine-restart/EBOP-target training regime (our anchor, per
  `campaigns/2026-09-26-training-batch/STUDY.md`) appears anywhere in the paper; γ-decay
  interacting with cosine LR restarts on the Adam side is untested territory the paper
  itself never modeled (its γ decay is a plain step or linear schedule, no restarts).

## Log lines to append (research-log.md; not appended by this agent — BRIEF forbids it)

- 2026-09-27 — DR-22 (Bop hyperparameters): arXiv:1906.02107 (Helwegen et al., NeurIPS
  2019) gives γ/τ only for CIFAR-10 (§5.2: γ=1e-4 decayed ×0.1/100ep, τ=1e-8, 500ep,
  batch 50) and ImageNet (§5.3: γ linear 1e-4→1e-6, τ=1e-8 fixed, batch 1024); Figure 1
  is a qualitative sweep (γ∈{1e-2,1e-3,1e-4}, τ∈{0,1e-6,1e-5}), not a recommendation.
  Larq `larq.optimizers.Bop` defaults (fetched `master`,
  `3d7de8832a477285bbf3c36252e24fcb9299a959`) are τ=1e-8, γ=1e-4, undecayed — equal to the
  paper's CIFAR-10 starting values. Both full benchmarks (CIFAR-10, ImageNet) share the
  same τ=1e-8/γ₀=1e-4 pair — the only difference is decay shape (step vs. linear), tuned
  for batches (50, 1024) far from our 2,790. None of this transfers directly: paper is
  W1A1 conv nets, ours is a W1A8 transformer; γ's horizon is per-step so epoch-based
  decay must be recalibrated in steps; τ is an absolute gradient-magnitude threshold
  (paper's own §6 caveat) and our `g` (bounded-STE, post-clipvalue) is not in the paper's
  units. Recommend: use 1e-8/1e-4 only as a scan seed, and measure the anchor's own `|m|`
  distribution before fixing τ. Full detail:
  `campaigns/2026-09-26-delta/research/DR-22-bop-hyperparameters.md`.
