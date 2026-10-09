# Family R — training recipe, optimization and regularization

Method cards for the training-recipe axis of Delta. Anchor = arm A of
`campaigns/2026-09-26-training-batch/STUDY.md`: A07-N64 (d_model 32, 4 heads, 1 block, FFN 32,
learned positional encoding, `binary_absmean` weights, activation widths learned from an
8-bit init, `act_policy learned_per_tensor_width`, our BetaPID with `stop_on_target false`,
pt/etarel/phirel input with the pT ≥ 2 GeV gate, 90/10 split, validation-only selection),
trained with the Sun et al. recipe (Adam defaults, cosine restarts peak 3e-3/500 epochs,
batch 2,790, 7,000 epochs) to a 350,000-EBOPs target. Every card's testable prediction is a
direction for arm A's seed-mean ROC-test top-1 accuracy (n = 260,000) and/or 350k-EBOPs
feasibility rate under this exact setup, per `STUDY.md`'s falsifiers. No number in this file is
from memory: recipe facts are file:line from `reference-code/HGQ2-examples/jsc150/{run_train,
data}.py` or `bnjettag/code/hgq2/bnhgq2/train.py`; published effects are quoted from arXiv PDFs
fetched in this session (§ table/figure named) or marked "no prior number transfers here" /
"abstract only, no table verified" where the full PDF table was not read.

---

## R00 — Recipe as implemented (Sun et al. code, file:line; not a card, reference only)

| element | value | source |
| --- | --- | --- |
| optimizer | `keras.optimizers.Adam()`, framework defaults | `run_train.py:97` |
| LR schedule | hand-written cosine restarts, peak 3e-3, period 500 epochs, `t_mul=1.0`, `m_mul=1.0`, floor `alpha=1e-6` over the last 10 epochs of each cycle | `run_train.py:21-37` (function), `:92-94` (`LearningRateScheduler(...)`) |
| batch size | 2,790 (CLI default `--batch-size`) | `run_train.py:67` |
| epochs | 7,000 | `run_train.py:104` (`model.fit(..., epochs=7000, ...)`) |
| pT gate | zero every constituent with column-5 (pT) < 2 GeV: `X *= X[..., :1] >= 2` | `data.py:25-26` |
| split | `val_size=0.1` default arg; shuffle then `n_train = int(0.9 * len(X))` → 558,000 train / 62,000 val (620,000 train+val file), 260,000 held-out test | `data.py:7` (default), `:36` (shuffle), `:40-43` (split), `:13-15` (test file load) |
| selection | `ParetoFront` over `(val_accuracy ↑, ebops ↓)`, checkpointing only when `val_accuracy > 0.5 and ebops < 5e5`; early stop `StopIf(ebops < 1e4)` — a two-objective front with a post-hoc pick, not a single best-val checkpoint (arm A instead uses validation-only selection, `STUDY.md` reference table) | `run_train.py:83-89` (`ParetoFront`, `enable_if`), `:91` (`StopIf`) |
| β (EBOPs regularizer) schedule | open-loop `PieceWiseSchedule([(0,2e-8,'linear'), (2000,3e-7,'log'), (7000,3e-6,'constant')])` — code disagrees with the paper's stated "PID controller over β" (§3); arm A instead uses our BetaPID (`STUDY.md`) | `run_train.py:90` |

The β-schedule delta (open-loop code vs. paper's stated PID vs. our BetaPID) is a target-schedule
question, not a recipe-optimizer question — see "Omitted and why" below; it belongs with family Q.

---

### R01 — Sun et al. verbatim optimizer (Adam, framework defaults)

**Mechanism.** `keras.optimizers.Adam()` called with no arguments — Keras 3 defaults
(β₁ 0.9, β₂ 0.999, ε 1e-7, no weight decay, no gradient clipping) — compiled with
`SparseCategoricalCrossentropy(from_logits=True)` and `steps_per_execution=4`.
**Why it could matter for binary weights here.** Binary STE training keeps a full-precision
shadow weight per {−1,+1} parameter; Adam's per-parameter second-moment estimate rescales the
STE gradient, which is already a biased proxy for the true (non-differentiable) sign function.
Unclipped Adam on a shadow-weight/STE stack is exactly the setting BinaryConnect and BitNet
both stabilize with clipping or extra normalization elsewhere in their pipelines — Sun et al.
use none, so any instability shows up here first.
**Primary source.** Kingma & Ba, "Adam: A Method for Stochastic Optimization," arXiv:1412.6980
— https://arxiv.org/abs/1412.6980 (2014, ICLR 2015). Accessed 2026-09-27.
**Published effect.** No prior number transfers here — Adam's original paper reports no jet
tagging or binary-weight results; the only "published effect" for this exact call is arm A's
own run, which does not exist yet (`STUDY.md` reference table).
**Knob or code change.** Already the anchor's optimizer in arm A per `STUDY.md`; upstream fact:
`reference-code/HGQ2-examples/jsc150/run_train.py:97` (`opt = keras.optimizers.Adam()`),
compiled at line 100. No code change needed; this card documents what arm A already runs.
**Hazards.** No gradient clipping: a single divergent step can corrupt the STE shadow weights
irrecoverably (no clip to bound it), which is exactly the instability arm D (our optimizer, with
clipvalue 1.0) is a control for.
**Tried here?** Live as arm A, unresolved (`STUDY.md` status: designed, no result yet,
`.claude/memory/experiment-log.md` 2026-09-26).
**Combines with.** R07 (our optimizer, the ablation partner via arm D).
**Testable prediction (A07-N64, 350k EBOPs).** Direction: lower feasibility rate (fewer than
8/8 seeds reach a checkpoint under target) than arm D, because unclipped Adam gives STE
training no protection against divergent steps. Compute multiplier: 1× (already the arm A run).

### R02 — Sun et al. verbatim LR schedule (cosine restarts, no decay of peak)

**Mechanism.** A hand-written schedule, not Keras's built-in `CosineDecayRestarts`:
`cosine_decay_restarts_schedule(3e-3, first_decay_steps=500, t_mul=1.0, m_mul=1.0, alpha=1e-6,
alpha_steps=10)`, driven by `LearningRateScheduler` so the "step" argument is the **epoch
index** (`run_train.py:21-37, 92-94`). `t_mul=1.0` means every restart cycle is the same
length (500 epochs, 14 cycles over 7,000 epochs); `m_mul=1.0` means the peak LR never decays
across restarts — cycle 14 restarts to the same 3e-3 peak as cycle 1.
**Why it could matter for binary weights here.** A ±1-weight layer's loss surface is a union of
2^n flat cells (BinaryConnect's weight-noise-as-regularizer framing, general discussion, not a
specific section quoted here); a full-strength LR restart late in training can flip weights
across cell boundaries that a decaying schedule would have frozen, which is either useful
exploration or late-training instability — arm A vs arm B/C (EBOPs ladder) can't distinguish
this from budget effects, but arm A vs arm F (no PE) partially isolates architecture from
schedule.
**Primary source.** Loshchilov & Hutter, "SGDR: Stochastic Gradient Descent with Warm
Restarts," arXiv:1608.03983 — https://arxiv.org/abs/1608.03983 (2016, ICLR 2017). Accessed
2026-09-27.
**Published effect.** Abstract only (full-text table not read in this session): "new
state-of-the-art results at 3.14% and 16.21%" test error on CIFAR-10 and CIFAR-100 — an
image-classification result, not jet tagging; no prior number transfers to our metric.
**Knob or code change.** Already implemented as arm A's schedule per `STUDY.md`; source is
`run_train.py:21-37` (function) and `:92-94` (`LearningRateScheduler(cosine_decay_restarts_
schedule(...))`). No change needed to run arm A as specified.
**Hazards.** None specific to HLS/EBOPs (LR schedule affects only the training loop, not the
exported graph); risk is purely training-time seed variance, which is what arm A's 8 seeds are
sized to catch.
**Tried here?** Live as arm A, unresolved.
**Combines with.** R03 (restart-variant ladder), R04 (warmup).
**Testable prediction.** Direction: seed-to-seed accuracy variance for arm A is higher at the
epoch-500/1000 readouts (right after a restart) than at readouts mid-cycle, because m_mul=1.0
repeatedly re-injects full-strength noise. Compute multiplier: 1× (arm A, already designed).

### R03 — SGDR restart-period and peak-decay variants (t_mul > 1, m_mul < 1)

**Mechanism.** Two independent knobs on R02's schedule: `t_mul` > 1 lengthens each successive
restart cycle (e.g. 500 → 1000 → 2000 epochs); `m_mul` < 1 decays the peak LR at each restart
(e.g. ×0.7 per cycle) — the "peak-LR ladder" Kai's brief names. Both are drop-in edits to the
two default arguments in `cosine_decay_restarts_schedule` (`run_train.py:22`, currently
`t_mul=1.0, m_mul=1.0`).
**Why it could matter for binary weights here.** If R02's flat prediction (late-training
instability from undamped restarts) is confirmed, `m_mul<1` is the direct fix: it keeps the
warm-restart's escape-from-local-minimum benefit early while damping the late-training risk of
flipping settled binary weights. `t_mul>1` trades fewer, longer explorations for the same total
epoch budget.
**Primary source.** Same as R02: Loshchilov & Hutter, arXiv:1608.03983 —
https://arxiv.org/abs/1608.03983, which defines `T_mult` (our `t_mul`) and the restart-decay
extension in its main text. Accessed 2026-09-27.
**Published effect.** Not fetched here beyond the abstract: no specific per-variant ablation
table was read in this session, so no `T_mult`/peak-decay number is quoted. Abstract-level
headline only (3.14%/16.21% CIFAR-10/100 test error, R02) — that number is for their best
overall configuration, not isolated to the restart-period or peak-decay knobs this card
proposes; no jet-tagging or binary-weight number exists regardless.
**Knob or code change.** Two float arguments in the schedule constructor; ~2-line change to
`run_train.py:22` (or its ported equivalent in our config). Needs a decision on values (this
card proposes `m_mul ∈ {0.7, 0.85}`, `t_mul ∈ {1.5, 2.0}` as a first ladder, not yet a config).
**Hazards.** None for HLS/EBOPs (training-time only, same as R02).
**Tried here?** Not tried; no config exists for this variant.
**Combines with.** R02 (base schedule it modifies), R04 (warmup layers on top cleanly), R07
(our optimizer, since the two axes — schedule shape and optimizer stability — are orthogonal).
**Testable prediction.** Direction: `m_mul=0.85` raises arm-A-style 350k feasibility rate
(fewer late-epoch divergences) at little or no accuracy cost, versus the unmodified R02
schedule. Compute multiplier: 1× (schedule-only change, same epoch/step count).

### R04 — Linear warmup before the main schedule

**Mechanism.** Ramp the LR linearly from ~0 (or a small floor) up to the target peak over the
first `k` epochs or steps, before handing off to whatever decay/restart schedule follows. Not
present in the Sun et al. code (`run_train.py` starts every restart cycle, including cycle 1,
at the peak 3e-3 with no ramp); our own recipe (arm R) *does* warm up — `warmup 1 [epoch] +
linear decay 999` at batch 256, peak 2e-5 (`STUDY.md`, arm R row).
**Why it could matter for binary weights here.** Early-training STE gradients are the noisiest
(shadow weights start unbinarized-random); a warmup delays full-strength updates until the
binarization statistics settle, which is the textbook Adam/large-batch justification (Goyal et
al., below) and plausibly matters more for a binary-shadow-weight scheme than a normal one.
**Primary source.** Goyal, Dollár, Girshick, Noordhuis, Wesolowski, Kyrola, Tulloch, Jia, He,
"Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour," arXiv:1706.02677 —
https://arxiv.org/abs/1706.02677 (2017), §5.1 and Table 1. Accessed 2026-09-27.
**Published effect.** Their Table 1 (ResNet-50/ImageNet, mean ± std over 5 trials, top-1
validation error): baseline kn=256, no warmup, 23.60% ± 0.12%; large-batch kn=8k with gradual
warmup 23.74% ± 0.09% (within 0.14 points of baseline); large-batch kn=8k with no warmup
24.84% ± 0.37%; large-batch kn=8k with constant warmup 25.88% ± 0.56% (constant warmup is
worse than no warmup at all — their §5.1 text, "actually degrades results"). ImageNet, full
precision, non-jet; no number transfers to our metric, but the qualitative finding — gradual
warmup, not any warmup, is what closes the gap — is the one worth carrying over.
**Knob or code change.** A short prepended ramp in the LR schedule function; ~5-line change to
whatever wraps `cosine_decay_restarts_schedule`. Our own `bnhgq2/train.py` recipe already
implements a 1-epoch warmup (docstring at line 15, "warmup 1ep + poly decay") for the
non-Chang recipe, so the code pattern exists and is portable.
**Hazards.** None for HLS/EBOPs.
**Tried here?** Not tried on the Chang (batch 2,790, 7,000-epoch) schedule specifically;
tried in spirit on our own r5-derived recipe (`bnhgq2/train.py:15`, "warmup 1ep").
**Combines with.** R02/R03 (the schedule it prepends to), R06 (large-batch scaling, same
paper, designed to be used together).
**Testable prediction.** Direction: adding a 1-cycle-length warmup (~500 epochs) before arm A's
first restart raises 350k-target feasibility rate at cycle 1, with a smaller effect at later
cycles (warmup only touches the start). Compute multiplier: 1× (schedule-only).

### R05 — One-cycle policy / super-convergence

**Mechanism.** A single up-then-down LR cycle over the whole training run (LR rises from a low
floor to a high peak over roughly the first 45% of training, then anneals below the floor for
the remainder), typically paired with an inverse cycle on momentum. Different from SGDR (R02):
one cycle total, not repeated restarts.
**Why it could matter for binary weights here.** Super-convergence's claimed mechanism is
large transient LR acting as a regularizer that lets the optimizer cross saddle regions fast;
for a 2^n-flat-cell binary loss surface this is a plausible fit, but it also means one shot at
the "large-LR" phase — no restarts to recover from a bad crossing, unlike SGDR.
**Primary source.** Smith, "Super-Convergence: Very Fast Training of Neural Networks Using
Large Learning Rates," arXiv:1708.07120 — https://arxiv.org/abs/1708.07120 (2018). Accessed
2026-09-27.
**Published effect.** Their Table/Fig. results on CIFAR-10/ImageNet with Resnet/WideResnet
show equal or better final accuracy in far fewer epochs than standard schedules — an
image-classification result at full precision; no jet-tagging or binary-weight number exists.
**Knob or code change.** Replaces `cosine_decay_restarts_schedule` wholesale; ~15-line new
schedule function plus a momentum-cycle counterpart if using SGD (not applicable to Adam
directly — would need to cycle β₁ instead, an extra design choice this card flags but does not
resolve).
**Hazards.** None for HLS/EBOPs; training-loop only.
**Tried here?** Not tried.
**Combines with.** Competes with, rather than combines with, R02/R03 (mutually exclusive
schedule choices for the same training run).
**Testable prediction.** Direction: one-cycle reaches the 350k EBOPs target in fewer total
epochs than arm A's 7,000-epoch, 14-restart schedule, but at higher seed-to-seed variance
(only one large-LR excursion, no restart to recover a bad one). Compute multiplier: <1× if run
for fewer epochs at equal step count; 1× if matched to 7,000 epochs for a controlled comparison.

### R06 — Large-batch linear LR scaling rule

**Mechanism.** Scale peak LR linearly with batch size relative to a reference batch/LR pair
(`LR_new = LR_ref × batch_new / batch_ref`), combined with warmup (R04) to avoid early
divergence. Sun et al.'s batch 2,790 / peak 3e-3 is itself an instance of this rule relative to
some smaller reference the paper does not state.
**Why it could matter for binary weights here.** Relevant only if Delta explores batch
sizes other than 2,790 (e.g. testing whether a smaller batch, cheaper per step, can be
compensated by the scaling rule) — this card exists to make that scaling principled rather than
ad hoc, not because binary weights change the rule's mechanism.
**Primary source.** Goyal et al., arXiv:1706.02677 — https://arxiv.org/abs/1706.02677 (as R04),
§2.1 "Linear Scaling Rule": `η = 0.1 · kn/256` where `k` is worker count and `n=32` is the
fixed per-worker sample size. Accessed 2026-09-27.
**Published effect.** Their Table 1 (quoted in full under R04): gradual-warmup linear scaling
at kn=8,192 matches the kn=256 baseline within 0.14 points top-1 error (23.74% ± 0.09% vs.
23.60% ± 0.12%). ImageNet/ResNet-50, full precision; no number transfers to our metric or
batch-size range (our arm A batch is 2,790, well inside their tested 256–8,192 span).
**Knob or code change.** A one-line derived LR given a chosen batch size; no code beyond
computing the peak-LR argument already exposed at `run_train.py:68` (`--learning-rate`).
**Hazards.** None for HLS/EBOPs.
**Tried here?** Not tried as a rule; arm A (batch 2,790) and arm R (batch 256) in `STUDY.md`
already differ in both batch and peak LR simultaneously, so no isolated test of the rule
exists in that design.
**Combines with.** R04 (warmup, same source paper, designed as a pair).
**Testable prediction.** Direction: if arm R's batch-256 peak LR (2e-5) were rescaled by the
linear rule to batch 2,790 (implying peak ≈2.18e-4), the rescaled run would track arm A's
accuracy trajectory more closely than arm R's own (unscaled) 2e-5 does, at the same
step-equivalent point. Compute multiplier: 1× (a rescaled arm-R-shaped run, same step count).

### R07 — Our Adam variant: β₂ 0.98, decoupled weight decay 0.01, clipvalue 1.0

**Mechanism.** `AdamW`-style call with `beta_1=0.9, beta_2=0.98, weight_decay=0.01,
clipvalue=1.0` (`bnjettag/code/hgq2/bnhgq2/train.py:389-394`). Lower β₂ (0.98 vs Adam's default
0.999) shortens the second-moment memory, decoupled weight decay regularizes shadow weights
directly rather than through the gradient, and `clipvalue` bounds every per-parameter gradient
component (chosen over `global_clipnorm`, which the module docstring says "overflows float32 on
this deep-SubLN stack and NaNs A4 regardless of LR" — `train.py:16-17`).
**Why it could matter for binary weights here.** This is the stability control arm A's card
(R01) is compared against directly (arm D in `STUDY.md`): the hypothesis is that unclipped
Adam is unsafe for STE/binary shadow weights and this variant is the fix already in production
use for our non-Chang recipe.
**Primary source.** Loshchilov & Hutter, "Decoupled Weight Decay Regularization,"
arXiv:1711.05101 — https://arxiv.org/abs/1711.05101 (2019, ICLR) for the weight-decay
decoupling; the β₂/clipvalue values themselves are project-internal tuning, not from a paper —
cited to the file, not a source. Accessed 2026-09-27.
**Published effect.** No external number applies to the specific (β₂=0.98, wd=0.01,
clip=1.0) triple. AdamW's own paper's specific table was not fetched in this session; abstract
only: decoupling weight decay from the gradient update "substantially improves Adam's
generalization performance" on CIFAR-10 and ImageNet. Full-precision, non-jet result regardless.
**Knob or code change.** Already implemented; arm D in `STUDY.md` runs it against the Chang LR
schedule. No new code.
**Hazards.** None for HLS/EBOPs (optimizer choice does not touch the exported graph).
**Tried here?** Live as arm D, unresolved. The clipvalue-over-clipnorm choice itself was
resolved empirically 2026-07-07 (`train.py:17`, "verified — LEDGER 2026-07-07") on a different
(non-Chang, non-N64) recipe; that verification does not transfer without re-checking at N=64.
**Combines with.** R01 (the ablation pair, arm A vs arm D), R03/R06 (schedule-shape and
LR-scaling axes are independent of this optimizer choice).
**Testable prediction.** Direction: arm D reaches 350k-target feasibility in at least as many
seeds as arm A (R01), with lower seed-to-seed accuracy spread, because clipping and shorter
second-moment memory both damp the largest gradient outliers. Compute multiplier: 1× (arm D,
already designed).

### R08 — EMA / Polyak averaging and SWA of weights

**Mechanism.** Two related but distinct techniques: **EMA** maintains a shadow copy of every
weight updated as `w_ema ← α·w_ema + (1−α)·w_train` every step, used at inference instead of the
raw trained weights. **SWA** instead averages a small number of checkpoints collected at
constant or cyclic LR late in training. Neither exists in our code today (no `ema` or `swa`
hits in `bnhgq2/train.py`).
**Why it could matter for binary weights here.** Both are built for continuous weights;
averaging {−1,+1} shadow weights produces a non-binary intermediate that must be re-thresholded
before export, and *what* gets exported — the average's sign, or the average of already-signed
checkpoints — is a real design choice this card does not resolve. If it helps at all, it likely
helps the float shadow-weight statistics settle, not the exported binary weights directly.
**Primary source.** EMA: Polyak & Juditsky (1992, not on arXiv; standard optimization
reference, cited via its use in Tarvainen & Valpola, "Mean Teachers," arXiv:1703.01780 —
https://arxiv.org/abs/1703.01780, 2017). SWA: Izmailov, Podoprikhin, Garipov, Vetrov, Wilson,
"Averaging Weights Leads to Wider Optima and Better Generalization," arXiv:1803.05407 —
https://arxiv.org/abs/1803.05407 (2018, UAI). Accessed 2026-09-27.
**Published effect.** SWA's own numeric accuracy table (their Table 1, CIFAR/ImageNet, several
architectures) was not read in full in this session, so no specific point-gain is quoted;
their §3.4 (Fig. 4/5, PreResNet-164 and VGG-16 on CIFAR-100, read directly) shows SWA
converging to a measurably wider, flatter basin than SGD with lower test error along the
SWA→SGD line segment, confirming the mechanism, not a portable number. Abstract: SWA gives
"notable improvement in test accuracy" over SGD on CIFAR-10/100/ImageNet with several
architectures, no digits in the abstract itself. Full-precision, non-jet, non-binary
regardless; no transfer claimed. No published EMA/SWA number exists for a binary-weight
transformer or this dataset.
**Knob or code change.** EMA: a shadow-variable update in the training loop, ~10-15 lines, plus
a re-thresholding/re-export step for the binary weights specifically (not in any upstream
code). SWA: checkpoint collection + averaging script, ~20 lines, same re-thresholding problem.
**Hazards.** Re-thresholding an averaged shadow weight can silently change which weights are
{−1,+1} versus their last training-time sign, which is a correctness risk for HLS parity checks
(the exported model must match what was evaluated) — flag for ml-engineer if pursued.
**Tried here?** Not tried; no code exists.
**Combines with.** R01/R02/R07 (any optimizer/schedule; EMA/SWA are wrappers around whichever
is chosen).
**Testable prediction.** Direction: EMA of the float shadow weights, re-thresholded at export,
gives a small ROC-test accuracy gain over the raw final checkpoint at the same 350k target,
because it reduces evaluation variance from whichever restart-cycle phase training happened to
end on (R02). Compute multiplier: ~1.02× (one extra weight-copy update per step; negligible).

### R09 — Knowledge distillation (logit, feature, and attention-map)

**Mechanism.** Train the binary student against a teacher's outputs in addition to (or instead
of) the hard labels. Three granularities: **logit distillation** (soft-label KL divergence
against a teacher's temperature-scaled softmax, Hinton et al.); **feature distillation**
(match intermediate activations, e.g. FFN outputs, to the teacher's, usually with a learned
projection since widths differ); **attention-map distillation** (match the teacher's
softmax(QKᵀ/√d) maps directly, meaningful only if the student keeps a comparable attention
structure). A natural teacher here is our own FP32 or W8A8 checkpoint at the same architecture.
**Why it could matter for binary weights here.** This is the highest-leverage untried lever in
this family: distillation is specifically documented to help low-bit students in general
(BitPart, arXiv:2508.07431, our own literature — binarizes only FFN+head, leaves attention
full precision, an implicit soft distillation path from the untouched teacher-precision
attention onto the binarized rest). A full-binary student, including binarized attention, has
no such internal crutch, so an external teacher signal may matter more, not less.
**Primary source.** Hinton, Vinyals, Dean, "Distilling the Knowledge in a Neural Network,"
arXiv:1503.02531 — https://arxiv.org/abs/1503.02531 (2015) for logit distillation. Zagoruyko
& Komodakis, "Paying More Attention to Attention" (attention transfer), arXiv:1612.03928 —
https://arxiv.org/abs/1612.03928 (2017) for feature/attention-map distillation — note this
paper's "attention" is a CNN spatial-activation map, not a transformer's softmax(QKᵀ) map; the
attention-map variant of this card borrows the name, not a verified transformer-specific
method from this source. Jet-tagging-specific: `literature/jet-tagging-transformers/2311.14160_
jet_tagging_distillation.md` (already indexed, arXiv:2311.14160,
https://arxiv.org/abs/2311.14160). Accessed 2026-09-27.
**Published effect.** Hinton et al., abstract-level only (full table not read in this session):
distillation recovers most of a larger model's accuracy in a much smaller one on MNIST/speech,
full precision, non-jet. The jet-tagging distillation paper (2311.14160) is the one primary
source in family scope for this dataset family, but its own dossier is not yet written in this
Delta — the number it reports has not
been verified against our metric definition here and must not be quoted until that dossier
exists.
**Knob or code change.** A teacher forward pass added to the training loop (teacher frozen,
`training=False`), a combined loss `L = (1−λ)·CE(y, student) + λ·KD(teacher, student)` at some
temperature — new loss function, ~40-60 lines, plus teacher-checkpoint loading. Feature/
attention variants add a projection layer per matched tensor pair, another ~20-40 lines.
**Hazards.** None for HLS/EBOPs at inference (the teacher is training-time only and is not
exported); training cost roughly doubles per step (teacher forward pass every batch).
**Tried here?** Not tried; no distillation code exists in `bnhgq2` (a `distill` string appears
only in a comment about a run-file consumer, `train.py:549`, not an implementation).
**Combines with.** R01/R02/R07 (any optimizer/schedule), R12 (label smoothing — both soften the
target distribution and should not obviously be stacked without checking interaction).
**Testable prediction.** Direction: logit distillation from an FP32 A07-N64 teacher raises
arm-A-recipe binary accuracy at 350k EBOPs, with the largest gain on the classes where the
binary/FP32 gap is currently largest (per-class breakdown owed by results-analyst once arm A
has a result). Compute multiplier: ~2× per step (teacher forward pass every batch) plus one
full FP32 training run to produce the teacher, amortized across all distillation experiments.

### R10 — Label smoothing (and loss-function variants)

**Mechanism.** Replace one-hot targets with `(1−ε)` on the true class and `ε/(K−1)` spread over
the rest (`K=5` here), softening `SparseCategoricalCrossentropy`. Related loss variants in the
same family: focal loss (down-weight easy examples) and class-balanced CE — neither used here
since Kai specified no class/sample weights for this batch.
**Why it could matter for binary weights here.** A binary-weight, low-capacity model is more
prone to overconfident wrong predictions on hard jets (fewer effective decision boundaries than
a continuous-weight model of the same shape); label smoothing directly targets logit
overconfidence, independent of the {−1,+1} constraint itself.
**Primary source.** Szegedy, Vanhoucke, Ioffe, Shlens, Wojna, "Rethinking the Inception
Architecture," arXiv:1512.00567 — https://arxiv.org/abs/1512.00567 (2015) — introduces label
smoothing (§7). Müller, Kornblith, Hinton, "When Does Label Smoothing Help?,"
arXiv:1906.02629 — https://arxiv.org/abs/1906.02629 (2019, NeurIPS) — the more relevant paper,
since it specifically studies label smoothing's *interaction with distillation*, directly
relevant if R09 and R10 are ever combined. Accessed 2026-09-27.
**Published effect.** Müller et al., abstract (verbatim, read directly): "if a teacher network
is trained with label smoothing, knowledge distillation into a student network is much less
effective" — the specific figure/table number for this finding was not identified in this
session, so only the abstract claim is quoted. CIFAR/ImageNet, full precision; non-jet,
non-binary; no transfer claimed.
**Knob or code change.** `SparseCategoricalCrossentropy` → a smoothed variant; ~5-10 lines
(Keras's `CategoricalCrossentropy(label_smoothing=ε)` requires one-hot targets, a small data
pipeline change from the current sparse-label path).
**Hazards.** None for HLS/EBOPs (loss function is training-time only).
**Tried here?** Not tried.
**Combines with.** R09 — combine only with the Müller et al. warning noted: do not smooth the
labels used to train a *teacher* destined for R09 distillation.
**Testable prediction.** Direction: label smoothing (ε≈0.1) improves arm-A-recipe held-out
macro-OvR AUC calibration (lower confident-wrong rate) with a small or neutral effect on raw
top-1 accuracy. Compute multiplier: 1× (loss-function-only change).

### R11 — Sharpness-aware minimization (SAM) / flatness-seeking for binary weights

**Mechanism.** Replace the standard gradient step with SAM's two-step rule: perturb weights
toward the direction that locally maximizes loss (an ascent step of radius ρ), compute the
gradient there, then descend from the *original* weights using that gradient — seeking minima
that are flat in a neighborhood, not just low.
**Why it could matter for binary weights here.** Flat-minima arguments are usually made for
continuous weight spaces; a ±1-weight space has no continuous neighborhood to be flat *in* once
weights are binarized, so SAM as published would have to operate on the float shadow weights
before the sign() thresholding, and it is not established that "flat in shadow-weight space"
implies anything about robustness of the thresholded binary weights. This is a real
binary-specific caveat, not a generic transfer assumption.
**Primary source.** Foret, Kleiner, Mobahi, Neyshabur, "Sharpness-Aware Minimization for
Efficiently Improving Generalization," arXiv:2010.01412 —
https://arxiv.org/abs/2010.01412 (2021, ICLR; read directly, §§1-3). Directly on-topic for
low-bit nets: Liu, Cai, Zhuang, "Sharpness-aware Quantization for Deep Neural Networks,"
arXiv:2111.12273 — https://arxiv.org/abs/2111.12273 (2021; abstract read directly, author
list corrected here after checking the abs page) — applies SAM-style flatness-seeking to
quantized (4-bit, not full binary) CNN and ViT weights. Accessed 2026-09-27.
**Published effect.** SAM (their Fig. 1, read directly): a per-task error-reduction scatter
across CIFAR-10, CIFAR-100, ImageNet, five finetuning tasks, SVHN, Fashion-MNIST and
noisy-CIFAR — points span roughly 0-40% *relative* error reduction from switching to SAM, no
single headline percentage-point number; full precision throughout. Sharpness-aware
quantization (SAQ), abstract (read directly): "SAQ outperforms AdamW by 1.2%" top-1 accuracy
on 4-bit ViT-B/16 (ImageNet), and their 4-bit ResNet-50 "surpasses the previous SOTA method by
0.9%" top-1 — 4-bit weights, CNN/ViT, not our 1-bit transformer; no number transfers directly.
**Knob or code change.** SAM wraps the optimizer with a two-pass gradient computation
(perturb-then-descend); a Keras-compatible SAM optimizer wrapper is a well-known ~40-60 line
pattern, applied on top of whichever base optimizer (R01 or R07) is chosen. The perturbation
radius ρ is a new hyperparameter needing its own small scan.
**Hazards.** None for HLS/EBOPs (SAM only changes the training-time update rule, not the
exported graph); doubles the per-step gradient computation cost.
**Tried here?** Not tried; no SAM code exists in `bnhgq2`.
**Combines with.** R01/R07 (wraps either optimizer), R08 (EMA/SWA and SAM are both
flatness-oriented and are typically not combined without checking for redundant effect).
**Testable prediction.** Direction: SAM on the float shadow weights, re-thresholded at export,
reduces seed-to-seed accuracy variance for arm A more than it changes the mean, because its
effect is on generalization robustness, not capacity. Compute multiplier: ~2× per step (two
forward-backward passes per update).

### R12 — Dropout / stochastic depth

**Mechanism.** Dropout zeroes a random subset of activations each step (applied to FFN or
attention-output activations here, not to the binary weights themselves); stochastic depth
randomly skips whole encoder blocks during training (irrelevant at L=1 block in the current
anchor — this card is a placeholder for any multi-block architecture card in family M).
**Why it could matter for binary weights here.** No dropout exists anywhere in
`bnhgq2/train.py` or `model.py` today. A 1-block, d=32 binary transformer is already
low-capacity; dropout's usual purpose (fighting overfitting in over-parameterized nets) may not
apply, and randomly zeroing activations interacts with the *learned* per-tensor activation
bitwidths (`act_policy learned_per_tensor_width`) in an unstudied way — zeroed activations
still cost a quantization grid slot even though they carry no information that step.
**Primary source.** Srivastava, Hinton, Krizhevsky, Sutskever, Salakhutdinov, "Dropout: A
Simple Way to Prevent Neural Networks from Overfitting," JMLR 15(1) (2014) — no arXiv ID
(pre-dates arXiv ML norm; cited via JMLR). Huang, Sun, Liu, Sedra, Weinberger, "Deep Networks
with Stochastic Depth," arXiv:1603.09382 — https://arxiv.org/abs/1603.09382 (2016), for the
block-skipping variant. Accessed
2026-09-26.
**Published effect.** Both papers report full-precision CNN gains (CIFAR/ImageNet); no
transformer, no jet, no binary-weight number exists for either.
**Knob or code change.** A `Dropout` layer after FFN/attention output; ~2-5 lines in
`model.py`. Stochastic depth needs L>1 blocks to mean anything — not applicable to the current
1-block anchor architecture without an architecture card from family M first.
**Hazards.** Interaction with `learned_per_tensor_width` activation quantization (above) is
untested; flag for ml-engineer before running if this card is picked up.
**Tried here?** Not tried; no dropout layer exists in the current model code.
**Combines with.** Any optimizer/schedule card in this family; depends on an L>1 architecture
card (family M) for the stochastic-depth half specifically.
**Testable prediction.** Direction: dropout on FFN activations has a small or negative effect
on arm-A-recipe accuracy at this model scale (1 block, d=32, 12,788 parameters) because the
model is capacity-constrained already, not overfitting-constrained. Compute multiplier: 1×
(adds negligible per-step cost).

### R13 — Physics-aware jet augmentation (η-φ rotation/reflection, pT smearing, constituent
dropout)

**Mechanism.** Three augmentations applied to the input constituent list, each targeting a
physical (approximate) symmetry: **rotation** of all constituents about the jet axis in the
η-φ plane by a random angle; **reflection** of φ (and/or η) since QCD radiation patterns are
not chirally distinguished at this level; **pT smearing**, shifting each constituent's η-φ
position by noise drawn ∝ 1/pT (detector-resolution-motivated); **constituent dropout**,
randomly zeroing a small number of low-pT constituents per jet (distinct from neural-net
Dropout, R12 — this drops *inputs*, not activations).
**Why it could matter for binary weights here.** None of these interact with the {−1,+1}
weight constraint mechanistically; their value, if any, is as a general regularizer for a
low-capacity model trained on a fixed 620k/some-split dataset — relevant because our current
recipe applies none of them (confirmed by grep: no rotation/reflection/smearing/constituent-
dropout code exists in `.claude/memory/archive/experiment-log.md`, and the pT ≥ 2 GeV gate in
`data.py:25-26` is a *hard cut*, not smearing or dropout).
**Primary source.** Dillon, Kasieczka, Olischläger, Plehn, Sorrenson, Vogel, "Symmetries,
Safety, and Self-Supervision" (JetCLR), arXiv:2108.04253 —
https://arxiv.org/abs/2108.04253 (2021) — defines exactly this augmentation set (rotation
about the jet axis, pT-scaled η-φ smearing, and a collinear-splitting augmentation not listed
above) for contrastive jet representation learning. Accessed 2026-09-27.
**Published effect.** JetCLR's own results are for a contrastive *pre-training* objective on
top-tagging (not the public HLS4ML 5-class set, not supervised training), reporting
representation-quality metrics, not a directly comparable supervised accuracy number. No
number transfers to our metric or dataset.
**Knob or code change.** A data-pipeline augmentation step applied per training batch (not
per-epoch, to get a new random augmentation each pass); rotation/reflection ~10-15 lines
(rotate/flip the η,φ columns before the pT gate), smearing ~10 lines, constituent dropout
~10 lines (zero a random low-pT subset, respecting the existing pT gate at `data.py:25-26`).
Augmentation would need to run *after* standardization statistics are fixed from the
unaugmented data, or the scale/shift computed at `data.py:28-29` would itself become
stochastic per epoch — a design detail this card flags but does not resolve.
**Hazards.** None for HLS/EBOPs (input augmentation is training-time only, does not touch the
exported graph or its EBOPs count).
**Tried here?** No augmentation code found: grep of `.claude/memory/archive/experiment-log.md`
for rotation/reflection/smearing/constituent-dropout returns zero hits. `BNJetTagAug` (the
archived W&B project name) is not established here as evidence either way for augmentation
having been tried; its name origin is not traced in this card (Round 14 stage 1 completed
2026-08-01 per the archive, `.claude/memory/archive/experiment-log.md:2643`, which only fixes
one date in the project's history, not the "Aug" naming reason).
**Combines with.** Any optimizer/schedule card; is largely orthogonal to R07-R12.
**Testable prediction.** Direction: rotation+reflection (exact symmetries of the pT/η_rel/
φ_rel input, since the physics is invariant under them) improves arm-A-recipe accuracy or
holds it flat at lower variance; smearing and constituent dropout are less certain in
direction and may need their own scan, since they are approximate-symmetry, not exact-symmetry,
augmentations. Compute multiplier: ~1.05-1.1× (augmentation compute is cheap relative to the
transformer forward/backward pass; no extra pass required).

### R14 — pT sample re-weighting (tried, negative)

**Mechanism.** Per-class sample weighting so each class's training-pT distribution matches the
all-class shape (Option E: per-class reweight to all-class log(pT) shape, +0.5 smoothing, a
weight cap, per-class mean-1 rescale — `bnjettag/code/hgq2/bnhgq2/pt_weights.py`), applied to
the training loss only; validation stays unweighted.
**Why it could matter for binary weights here.** No binary-specific mechanism — this is a
data/loss-reweighting method, independent of weight precision. Included here per Kai's
instruction because it is the one recipe-family method already run to a verified result.
**Primary source.** Project-internal (no external paper cited for this specific reweighting
recipe); implementation at `bnjettag/code/hgq2/bnhgq2/pt_weights.py`, wired into
`train.py` behind `train.pt_weights`.
**Published effect (ours, verified).** N=8, W1A8, 8 seeds, held-out ROC-test macro-OvR AUC
(n=260,000): BASE 0.8711±0.0013, PTW5 (cap-5) 0.8603±0.0019, PTWNC (no cap) 0.8587±0.0020.
Paired PTW5−BASE −0.0108 [95% CI −0.0124, −0.0093], 8/8 seeds lower; every per-class AUC lower
8/8 (gluon worst, −0.028); small gains only in the pT tails (bin 6, ≥1106 GeV: +0.0165, 8/8),
losses in the centre bins.
Source: `.claude/memory/experiment-log.md` 2026-09-26 ("Does pT sample re-weighting help the
N=8 W1A8 tagger?", `local/2026-09-25-pt-weighting`, status verified), cross-checked by results-
analyst and an independent recompute ("newton"), 24/24 arrays reproduced.
**Knob or code change.** Already implemented and default-off (`train.pt_weights` absent ⇒
unchanged path). No new code.
**Hazards.** None beyond the already-measured accuracy cost.
**Tried here? Verified negative** at N=8, W1A8; not tested at N=64 or under the Sun et al.
recipe (arm A/D/etc. in `STUDY.md` all specify "no sample, class or pT weights" — this method
is excluded from the current campaign by design, not by oversight).
**Combines with.** Nothing in this family — it is a closed, negative result, listed for
completeness per the brief, not a candidate for the wave-0 combination grid.
**Testable prediction.** Direction: given the N=8 result generalizes to N=64 (unverified
assumption), pT reweighting would lower arm-A-recipe accuracy versus an unweighted arm at the
same 350k target, with the largest per-class loss on gluon. Compute multiplier: 1× (loss-only
change, already implemented) — not proposed for a run given the existing negative result.

---

## Omitted and why

- **Curriculum over the EBOPs target.** Explicitly a family-Q question (ramping the EBOPs
  budget itself over training, rather than fixing it from step 1 as arm A does) — a full card
  here would duplicate that family. Noted as a link: any curriculum design should specify
  whether it curricula the *target* (Q's territory) or the *training recipe* around a fixed
  target (this family's territory); the boundary is the target schedule, not the optimizer.
- **Ensembling.** Omitted from a full card because its hazard dominates its mechanism for this
  project: an ensemble of N binary models multiplies exported LUT/logic cost by N (there is no
  DSP=0 trick for combining outputs cheaply — a vote or average over N independent 0-DSP cores
  is still N cores), which contradicts the single-fixed-latency-budget deployment constraint
  (CMS Phase-2 L1, one algorithm, one resource envelope) before any accuracy question is asked.
  If pursued, it belongs with a hardware-cost card in whichever family owns resource budgeting,
  not here.
- **Loss-function variants beyond label smoothing** (focal loss, class-balanced CE): omitted
  as separate cards because Kai specified no class/sample weights for this batch, and focal
  loss is itself a form of per-example reweighting by difficulty — the same objection R14's
  verified-negative result raises for pT weighting applies in spirit, untested. Folded into
  R10's "combines with" note instead of a standalone card to keep the family at 14 cards.
- **SGD/Nesterov-momentum baselines**: omitted because neither Sun et al.'s code nor ours uses
  SGD anywhere; Adam (R01) and its decoupled-weight-decay variant (R07) are the only optimizers
  in scope, and a new optimizer family (SGD+momentum) would need its own card family if a
  reason emerged to test it.

## Log lines to append

- 2026-09-26 — Loshchilov & Hutter, "SGDR: Stochastic Gradient Descent with Warm Restarts,"
  arXiv:1608.03983, https://arxiv.org/abs/1608.03983 — the exact LR-schedule family Sun et
  al.'s code implements (t_mul=1, m_mul=1 special case); relevant for R02/R03 restart-variant
  design; abstract-level CIFAR effect only (3.14%/16.21%), no full-table number fetched, does
  not transfer numerically regardless.
- 2026-09-26 — Foret, Kleiner, Mobahi, Neyshabur, "Sharpness-Aware Minimization for Efficiently
  Improving Generalization," arXiv:2010.01412, https://arxiv.org/abs/2010.01412 — candidate
  flatness-seeking optimizer wrapper (R11); binary-specific caveat (flat in float shadow-weight
  space is not established to imply anything about the thresholded binary weights) is ours, not
  the paper's; their Fig. 1 (read directly) reports 0-40% relative error reduction across
  benchmarks, no single number transfers.
- 2026-09-26 — Liu, Cai, Zhuang, "Sharpness-aware Quantization for Deep Neural Networks,"
  arXiv:2111.12273, https://arxiv.org/abs/2111.12273 — nearest published SAM-for-low-bit
  result (R11), but 4-bit CNN/ViT, not a binary transformer; abstract-level numbers only
  (+1.2% ViT-B/16, +0.9% ResNet-50 top-1 over prior SOTA at 4-bit), no transfer to 1-bit.
- 2026-09-26 — Izmailov, Podoprikhin, Garipov, Vetrov, Wilson, "Averaging Weights Leads to
  Wider Optima and Better Generalization" (SWA), arXiv:1803.05407,
  https://arxiv.org/abs/1803.05407 — candidate for R08; raises the re-thresholding-before-
  export question for binary weights specifically, which the paper does not address
  (continuous-weight setting only); their Fig. 4/5 (read directly, PreResNet-164/VGG-16 on
  CIFAR-100) show a qualitatively wider basin, no portable accuracy number.
- 2026-09-26 — Goyal, Dollár, Girshick, Noordhuis, Wesolowski, Kyrola, Tulloch, Jia, He,
  "Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour," arXiv:1706.02677,
  https://arxiv.org/abs/1706.02677 — source of the linear LR-scaling rule (R06) and gradual
  warmup (R04); their Table 1 (read directly): gradual warmup at batch 8k matches the batch-256
  baseline within 0.14 points top-1 error (23.74%±0.09% vs. 23.60%±0.12%); constant warmup is
  worse than no warmup at all (25.88%±0.56% vs. 24.84%±0.37%). ImageNet/ResNet-50, full
  precision; no jet or binary transfer, mechanism only.
- 2026-09-26 — Dillon, Kasieczka, Olischläger, Plehn, Sorrenson, Vogel, "Symmetries, Safety,
  and Self-Supervision" (JetCLR), arXiv:2108.04253, https://arxiv.org/abs/2108.04253 — the
  primary source for physics-aware jet augmentation (R13: rotation, pT-scaled η-φ smearing);
  their setting is contrastive pre-training on top-tagging, not our supervised 5-class task, so
  no accuracy number transfers, only the augmentation definitions.
- 2026-09-26 — Hinton, Vinyals, Dean, "Distilling the Knowledge in a Neural Network,"
  arXiv:1503.02531, https://arxiv.org/abs/1503.02531 — canonical logit-distillation source for
  R09; MNIST/speech, full precision, abstract-level claim only, no transfer, mechanism only.
- 2026-09-26 — Zagoruyko & Komodakis, "Paying More Attention to Attention," arXiv:1612.03928,
  https://arxiv.org/abs/1612.03928 — attention-map/feature distillation source for R09's
  attention variant; CNN spatial activation-map matching, not transformer softmax(QKᵀ)
  attention weights — flag this distinction if R09's attention-map variant is picked up.
- 2026-09-26 — Müller, Kornblith, Hinton, "When Does Label Smoothing Help?," arXiv:1906.02629,
  https://arxiv.org/abs/1906.02629 — for R10; abstract states label smoothing hurting a
  *subsequent* distillation step, directly relevant if R09 and R10 are ever combined in a
  later wave; specific figure/section for the claim not identified in this session.
- 2026-09-26 — Kingma & Ba, "Adam: A Method for Stochastic Optimization," arXiv:1412.6980,
  https://arxiv.org/abs/1412.6980 — the optimizer Sun et al.'s code calls with framework
  defaults (R01, `run_train.py:97`); orientation only, no jet/binary number.
- 2026-09-26 — Loshchilov & Hutter, "Decoupled Weight Decay Regularization," arXiv:1711.05101,
  https://arxiv.org/abs/1711.05101 — the mechanism behind our optimizer's decoupled weight
  decay (R07, `bnhgq2/train.py:389-390`); abstract-level claim only, no jet/binary number.
- 2026-09-26 — Smith, "Super-Convergence: Very Fast Training of Neural Networks Using Large
  Learning Rates," arXiv:1708.07120, https://arxiv.org/abs/1708.07120 — source for the
  one-cycle policy (R05); CIFAR/ImageNet, full precision, no jet/binary number transfers.
- 2026-09-26 — Szegedy, Vanhoucke, Ioffe, Shlens, Wojna, "Rethinking the Inception
  Architecture," arXiv:1512.00567, https://arxiv.org/abs/1512.00567 — introduces label
  smoothing (R10, §7); ImageNet, full precision, no jet/binary number transfers.
- 2026-09-26 — Tarvainen & Valpola, "Mean teachers are better role models," arXiv:1703.01780,
  https://arxiv.org/abs/1703.01780 — EMA-of-weights precedent cited for R08 in lieu of the
  non-arXiv Polyak & Juditsky (1992) source; semi-supervised setting, not ours, mechanism only.
- 2026-09-26 — Huang, Sun, Liu, Sedra, Weinberger, "Deep Networks with Stochastic Depth,"
  arXiv:1603.09382, https://arxiv.org/abs/1603.09382 — block-skipping variant for R12; needs
  an L>1-block architecture (family M) before it applies to our current 1-block anchor.
