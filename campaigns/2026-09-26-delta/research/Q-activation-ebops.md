# Family Q — activation quantization and hardware-cost (EBOPs) control

Physics-researcher, 2026-09-26. Every card is a delta from the anchor (`campaigns/2026-09-26-
training-batch/STUDY.md`, arm A: A07-N64 = d32/h4/L1/FFN32, learned PE, `binary_absmean`
weights, `act_calib="free"` activation widths from an 8-bit init, per-tensor granularity,
`BetaPID` at 350k EBOPs target, `stop_on_target=false`, `selection="max_auc"`, 90/10 split,
validation-only checkpoint selection). Code paths read: `docs/conventions/quantization-and-
cost.md`, `bnjettag/code/hgq2/bnhgq2/qat.py`, `ebops_target.py`, `ebops_calc.py`, `train.py`,
`ablation.py`, `reference-code/HGQ2-examples/jsc150/model.py`, and the local HGQ2 install
(`~/hgq2/HGQ2/src/hgq/layers/softmax.py`, `~/hgq2/HGQ2/src/hgq/quantizer/internal/
fixed_point_quantizer.py`, `~/hgq2/HGQ2/src/hgq/quantizer/config.py`).

**What the anchor already does, so cards below are read as deltas, not as new mechanisms:**
`qat.py` implements three activation-width policies behind `quant.act_calib`: `frozen` (static
first-batch-MSE-calibrated grid, `_static_act`), `trainable` (fixed total width, trainable
integer/fractional split via a `Constant` width constraint, `_trainable_act`), and `free`
(fully learnable KIF integer+fractional bits with a `MonoL1`/`MeanMonoL1` regularizer,
`_free_act`, `qat.py:279-302`) — the anchor uses `free`. Granularity is `tensor` (scalar grid)
or `channel` (`heterogeneous_axis` set to the last one or two axes, `qat.py:386-389`) — a config
switch already implemented. `ebops_target.py` implements `BudgetMonitor`: it runs `resolve_budget`
once after calibration to turn a `target_ratio` or an absolute `pid.target_ebops` into a fixed
threshold (`ebops_target.py:54-82`), then every epoch recomputes EBOPs via `compute_ebops`
(native `hgq.utils.trace_minmax`, `ebops_calc.py`), logs `budget_met`, and saves the best
feasible checkpoint under one of two selection rules, `max_auc` (highest val macro-AUC among
budget-feasible epochs) or `min_ebops` (lowest EBOPs among budget-feasible epochs),
(`ebops_target.py:138-151`); `stop_on_target` can end training early the epoch the budget is
first met (`ebops_target.py:152-155`). The anchor's controller is `BetaPID`
(`hgq.utils.sugar.BetaPID`, imported `bnjettag/code/hgq2/bnhgq2/ablation.py:19,253` and
`train.py:141-145`), a closed-loop P(I)(D) block whose gains the STUDY cites as `[D5]`
(p=1.0, i=0.05, d=0); a SECOND, open-loop controller also exists in this codebase — a piecewise
`beta_schedule` + `BetaScheduler` + `ParetoFront` (`train.py:106-163`), which the anchor does NOT
use but which Q04/Q05 discuss explicitly. Softmax internals in the anchor use fixed static
tables (`_static_act`/`_table`, `qat.py:434-454`), not a learned width, but ARE still traced into
the EBOPs total by `QSoftmax`'s own `_compute_ebops` (see Q08).

---

### Q01 — Per-channel free activation width

**Mechanism.** Same `_free_act` KIF quantizer as the anchor, but `heterogeneous_axis` includes
the channel axis (`act_granularity: "channel"`, already switched via `axes` in `act_iq`,
`qat.py:386-389`), so each channel of a datalane gets its own trainable (i, f) instead of one
scalar per tensor. The `MeanMonoL1` regularizer (`qat.py:266-277`) keeps the width penalty's
scale invariant to the number of channels, so the EBOPs pressure per channel matches the
per-tensor case.

**Why it could matter for binary weights here.** With ±1 weights, the only place precision
lives is the activation grid; a single scalar width per tensor forces every channel that feeds
a binary matmul to share one grid even if channels carry very different dynamic ranges (e.g.
a positional-encoding-shifted channel vs. a raw feature channel). Per-channel width lets the
optimizer spend bits where they buy AUC and starve channels that don't need them, which is a
free win specifically because binary weights already contribute the smallest possible amount of
information per multiply-add — the activation grid is the only lever left, so its granularity
matters more here than in a mixed-precision-weight model.

**Primary source.** Sun, "Tutorial on HGQ and Alkaid" (FastML 2026) documents heterogeneous
per-element/per-channel HGQ2 bitwidths as the framework's default mode; batch 2026-09-17
(logged in `research-log.md`, cited in `docs/conventions/quantization-and-cost.md:15-16`)
already tested tensor vs. channel granularity in our own pipeline. Date accessed: 2026-09-26.

**Published effect.** No prior number from the tutorial's own benchmark that isolates
per-channel vs. per-tensor at fixed EBOPs on a comparable model; our own 2026-09-17 batch is the
only source with a granularity ablation and its result belongs in the tried-already inventory,
not invented here.

**Knob or code change.** Config-only: `quant.act_calib="free"`, `quant.act_granularity="channel"`
(`qat.py:384-389`). T0 tier — no code change, already wired.

**Hazards.** `compute_ebops` (`ebops_calc.py`) traces the model's actual quantizer bitwidths via
`trace_minmax`, so per-channel widths ARE reflected correctly in EBOPs — this is not a blind
spot. The hazard is downstream: per-channel widths on an einsum feeding a binary matmul may
force hls4ml/HGQ2's HLS backend to unroll per-channel fixed-point types, which can turn a
shared-width adder tree into channel-specific bit-slicing logic — more LUTs even at equal total
EBOPs, and a risk that some channels' integer bits grow enough to reintroduce DSP-eligible
multiply widths in the *input* quantizer of a downstream 8-bit dense head. No DSP risk in the
binary layers themselves (weight side is untouched).

**Tried here?** Leave to `inventory/tried-already.md` (batch 2026-09-17 tested tensor vs.
channel granularity); cite its outcome there, not asserted here.

**Combines with.** Q02 (a further granularity step); Q04 (controller behavior may differ under
more free parameters, since more sites need PID pressure to shrink).

**Testable prediction (A07-N64, 350k).** Channel granularity should reach a *higher* validation
macro-AUC than tensor granularity at the same 350k EBOPs ceiling (more freedom to allocate the
same bit budget), at the cost of a larger EBOPs-fraction-per-epoch(convergence) variance.

---

### Q02 — Per-value (fully heterogeneous) activation width

**Mechanism.** Extend `heterogeneous_axis` in `_free_act` to every axis of the datalane tensor
(sequence position AND channel, or all axes for a 2D tensor), so each individual activation
*value* in a fixed tensor shape gets its own trainable (i, f) — the "HGQ per-value" mode the
brief names, one width per weight/activation element rather than per channel.

**Why it could matter for binary weights here.** Sequence position matters here in a way it may
not for a generic CNN: our transformer's per-particle activations (pre-attention Q/K/V, FFN
hidden) differ systematically by particle rank if particles are pT-sorted, so a per-position
width (not just per-feature-channel) could track that structure. This is the natural endpoint of
Q01, tested to see whether the extra freedom keeps paying off or just adds optimizer surface.

**Primary source.** HGQ2 docs / Sun tutorial describe fully heterogeneous per-element bitwidths
as the general case that per-tensor and per-channel are restrictions of; no paper-specific
number for a transformer of our scale. Date accessed: 2026-09-26.

**Published effect.** No prior number — HGQ-LUT (arXiv:2604.22293) documents "per-element HGQ
quantization with zero-bit pruning" applied to its L-LUT inputs/outputs, but on a different
architecture (LUT-native neurons, not a binary-weight transformer) and a different dataset
family (16-feature jet task); not directly comparable (`literature/hls4ml-fpga-triggers/
2604.22293_hgq_lut.md`).

**Knob or code change.** Config: `act_granularity` needs a new value (e.g. `"element"`) that
passes `axes=(-2, -1)` (or all non-batch axes) unconditionally rather than only for the shared
stream quantizer (`stream_iq`, `qat.py:425-426` already does this for one site). Estimated
T1 change: ~10-20 lines in `act_iq`/`_free_act` call sites, plus a shape-compatibility check
since some einsum outputs vary in T (particle count) across batches only if masking is used
(ours is fixed N=64, so shape is static — low risk).

**Hazards.** `compute_ebops` correctly totals per-element bitwidths since `trace_minmax` reads
whatever bitwidth tensor the quantizer reports — no EBOPs blind spot. Real hazard: a fully
per-element grid on a (T, D) or (T, T, H) tensor multiplies the number of trainable width
parameters by T (64) or T² (4096) per site; MonoL1 regularization pressure per parameter may
need re-tuning (weaker per-element, since the same total EBOPs penalty is now spread over many
more parameters) or width-sharing structure collapses to typical per-channel behavior anyway.
On hardware, per-element widths on an attention score tensor (T×T) risk exploding the HLS
resource count regardless of EBOPs, since each element may synthesize its own bit-width literal
in the unrolled dataflow — a case where EBOPs and LUT count diverge sharply.

**Tried here?** Not found in the inventory as of this writing; flag as untried.

**Combines with.** Q01 (finer step of the same idea); Q14 (per-element grids make 0-bit
per-element pruning natural, i.e. structured sparsity via width collapse).

**Testable prediction (A07-N64, 350k).** Per-element width should match or marginally beat
per-channel (Q01) on validation macro-AUC at 350k, but the marginal AUC gain per added
trainable-width parameter should be small — most of the benefit is expected to already be
captured by Q01.

---

### Q03 — Activation width initialization: Chang's (i0=2, f0=7) split vs. our MSE-calibrated split

**Mechanism.** Chang's `get_model` (`reference-code/HGQ2-examples/jsc150/model.py:277-296`) sets
the ACTIVATION-side quantizer scope (`scope1`) to `kif`, `place='datalane'`, `overflow_mode=
'wrap'`, `f0=bw_a` (7 in the jsc150 recipe, per `docs/chang-vs-bnjettag.md:146`'s "b0=7/f0=7"
notation, where the `b0=7` half of that cell is the SEPARATE weight-side `kbi` scope, `scope0`,
not the activation width — the two `7`s in that table cell are two different parameters, not one
number). Activation `i0` is not set in `scope1`; `hgq.quantizer.config.QuantizerConfig`'s own
default for `i0` is **2**, not 0 (`~/hgq2/HGQ2/src/hgq/quantizer/config.py:249`, verified
2026-09-26 — an earlier draft of this card wrongly assumed 0), and `k0` defaults `True` (one
sign bit). So Chang's activation init is **total width 1+2+7 = 10 bits**, WIDER than our
`act_bits=8` default (`_static_act`'s arithmetic, `qat.py:238-241`, gives `k0+i0+f0 = act_bits`
identically, i.e. 8 total). **Chang's activation init is not narrower than ours — it is wider by
2 bits at the start**, the opposite of this card's original framing; correct that before
scheduling it.

**The real deltas, restated.** (a) *Total init width*: Chang starts at 10 bits (2 integer, 7
fractional, 1 sign), we start at 8 (integer split MSE-calibrated, fractional = 8−1−i); both then
shrink under L1/MonoL1 pressure, so Chang's optimizer has FURTHER to travel to reach a given
EBOPs target purely from a wider starting point, not a narrower one. (b) *Split*: Chang starts
every activation at a fixed `i=2` (not calibrated) and lets both `i` (up to 12) and `f`
(regularized down) move via gradient descent; our anchor instead MSE-calibrates `i` from a real
batch BEFORE training starts (`calibrate_activations`, `qat.py:535-568`), so we start closer to
the eventual range and Chang starts from a fixed, uncalibrated guess. (c) *Overflow mode*: Chang
uses `wrap` (values exceeding the current range alias rather than saturate — safe only because
`i` is learned and `trace_minmax` pins the final range before export); our `_free_act`/
`_static_act` use `SAT` throughout (`qat.py:238-241, 298-299`) so the trained grid is guaranteed
deployable without a wrap-induced training/inference mismatch. This card is really "wider,
uncalibrated, WRAP init vs. narrower, calibrated, SAT init" — three simultaneous differences,
not a single width-magnitude comparison.

**Why it could matter for binary weights here.** Starting every activation width's integer part
at 0 (Chang's choice) means the very first forward passes at N=64 (initial EBOPs 24.8M,
`campaigns/2026-09-26-training-batch/STUDY.md:57`) likely wrap/alias badly until `i` grows —
survivable under WRAP+gradient descent in Chang's own recipe, but our stack's default is SAT
specifically because an untested WRAP interaction with the binary-weight STE's already-STE'd
gradient path is a new failure mode this comparison would surface, not one we've ruled out.

**Primary source.** `reference-code/HGQ2-examples/jsc150/model.py:277-296` (`get_model`);
`docs/chang-vs-bnjettag.md:146` (side-by-side table, already logged). Date accessed: 2026-09-26
(code already in this repo's `reference-code/`).

**Published effect.** No AUC number isolates the init-width choice alone in Sun et al.
(arXiv:2510.24784); their Table 1 reports the endpoint (79.4% at N=64, 350k EBOPs target) with
init folded into the whole recipe, not ablated.

**Knob or code change.** Three independent knobs, and they should be varied one at a time to keep
this card interpretable: (1) init total width — currently `_free_act` inits from `act_bits=8`
(calibrated split); a Chang-style arm would init at 10 total bits (`i0=2` fixed, `f0=7`) instead.
(2) `i0` calibration — currently `_free_act` receives a calibrated `i0` from
`calibrate_activations`; a Chang-style arm would force a fixed `i0=2` at build time and skip
calibration for the free-width sites. T0-T1 (bypass the calibration call for `act_calib="free"`
sites). (3) `overflow_mode` — currently hardcoded `SAT` in `_free_act`/`_static_act`
(`qat.py:238,298`); a WRAP arm needs a new branch, T1 (a handful of lines, since `QuantizerConfig`
already accepts `overflow_mode` as an argument).

**Hazards.** No EBOPs accounting issue either way — `compute_ebops` traces whatever widths and
overflow behavior the quantizer currently reports, at any point in training; init strategy and
overflow mode are both fully visible to EBOPs. DSP risk unaffected (activation width, not weight
width). The real hazard is entirely a training-stability one, specific to combining WRAP with
our STE stack: WRAP is only safe if the learned range converges before deployment (Chang's own
recipe relies on this), and our binary-weight STE already routes one extra bounded-but-nonzero
gradient path (`bitnet_binary_ste`, `qat.py:43-65`) through every activation site's input — an
untested interaction, not a known-safe one.

**Tried here?** Not found in the inventory.

**Combines with.** Q04 (controller cards) — a wider, uncalibrated init changes how far the EBOPs
trajectory has to travel before widths stabilize, independent of the controller's gains.

**Testable prediction (A07-N64, 350k).** Isolating the calibration only (fixed `i0=2` vs.
calibrated `i0`, both at the SAME total init width, SAT overflow held fixed in both arms so this
stays a one-variable test): the calibrated-`i0` arm should reach a stable EBOPs trajectory in
fewer epochs than the fixed-`i0` arm, with validation macro-AUC at the selected 350k checkpoint
within noise of each other. Isolating total init width instead (8 vs. 10 bits, both calibrated):
the wider (10-bit) init should take LONGER to reach 350k (more compression required) with final
AUC within noise, since both should converge to the same width budget by the selected checkpoint.

---

### Q04 — β controller variants: PID gains vs. the existing piecewise β schedule

**Mechanism, corrected against the actual code (`ablation.py:253`, `train.py:106-163`).** Two
DISTINCT, already-implemented controller mechanisms exist side by side in this codebase, and
this card compares them rather than inventing a new one: (1) **`BetaPID`**
(`hgq.utils.sugar.BetaPID`, imported `ablation.py:19`, `train.py:142`) — the anchor's mechanism,
a closed-loop P(I)(D) controller that adjusts β every epoch from the measured EBOPs error against
a FIXED `target_ebops` (resolved once by `resolve_budget`, `ebops_target.py:54-82`); the anchor's
gains are p=1.0, i=0.05, d=0 (STUDY `[D5]`). (2) **`beta_schedule` + `BetaScheduler`**
(`train.py:124-127,141-146`) — an open-loop PIECEWISE schedule of β values by epoch (e.g.
`[[0, 0.0, "constant"], [300, 1e-9, "log"], [600, 1e-3, "constant"]]`), paired with `ParetoFront`
which admits a checkpoint only when the epoch's measured `ebops <= threshold` and the point is
non-dominated on (val_macro_auc↑, ebops↓) (`train.py:127-134`); `threshold` here is a FIXED
scalar the whole time — **there is no moving target_ebops anywhere in this code path**; what is
"gradual" is β's schedule, not the target (this corrects the framing in the version of this card
before code was read). This card is: re-tune PID gains (P/I/D, including a nonzero D the anchor
doesn't use), AND/OR run the piecewise-`beta_schedule`+`ParetoFront` path instead of PID at the
same fixed 350k threshold, as two alternative already-existing controllers.

**Why it could matter for binary weights here.** With binary weights, EBOPs is driven almost
entirely by activation bitwidths (the weight term of the HGQ2 EBOPs formula is pinned at 1 bit
per multiply operand, `_binary_kq`, `qat.py:228-232`); the controller therefore has a much
narrower lever (activation widths only) to hit the target than in Chang's per-weight learned
setting, which may make either controller more prone to oscillation or slow convergence — gain
retuning (PID) or schedule shape (piecewise) is plausibly load-bearing specifically because of
the binary constraint, not incidental.

**Primary source.** PID control of a regularization weight to a target, and piecewise-scheduled
regularization weights, are both standard control/optimization patterns, not paper-specific; the
HGQ2/Alkaid tutorial (Sun, FastML 2026) presents the general EBOPs-target-via-β pattern. No
arXiv paper isolates gain or schedule choice for a binary-weight model. Date accessed:
2026-09-26.

**Published effect.** No prior number for either controller in isolation on our model. The
2026-09-15 campaign (`campaigns/2026-09-15-ebops-accuracy-eval/`) is most plausibly the
`beta_schedule` path — inferred from the two mechanisms this code exposes and from
`docs/conventions/quantization-and-cost.md:34`'s wording ("the gradual-schedule arm, 2026-09-15")
— but the campaign directory contains only an eval script, a Pareto-scatter plot, and a job
manifest, none of which name `beta_schedule` or `pid` directly (checked by grep, 2026-09-26); its
run configs were not located in this pass, so this attribution is **inferred, not confirmed**.
Confirm against the actual run configs before treating this as settled; its outcome belongs in
the tried-already inventory regardless.

**Knob or code change.** Config-only for both: `train.ebops.pid.{p,i,d}` and `init_beta`
(`ebops_target.py:65-79` validates these for the PID path); `train.ebops.beta_schedule` (a list
of `[epoch, beta, interp_kind]` triples, `train.py:124-127`) for the piecewise path — mutually
exclusive per `ebops_target.py:63-64`'s explicit check ("choose only one of BetaPID and
beta_schedule"). T0 tier, both already wired.

**Hazards.** No EBOPs accounting change either way (β only weights the training loss;
`compute_ebops` is control-independent and traces the model's ACTUAL widths regardless of how β
got there). Hazard is entirely about **feasibility and selection semantics**, and the two paths
differ here: PID + `BudgetMonitor` explicitly reports "no feasible checkpoint" if the target is
never met (`ebops_target.py:149`, gated on `logs["budget_met"]`); the piecewise path's
`ParetoFront` instead accumulates a FRONT of non-dominated checkpoints and its `enable_if` simply
never admits any if the threshold is never met — an empty front, not a labelled failure, and the
documented pitfall ("do not report the unconstrained best (the gradual-schedule arm,
2026-09-15)", `docs/conventions/quantization-and-cost.md:34`) is specifically about a caller
mis-reading an empty/near-empty front as if it had a valid entry. Any Q04 arm using the
`beta_schedule` path must re-check for this failure mode explicitly, not assume `BudgetMonitor`'s
safety net applies.

**Tried here?** **Most plausibly yes, the `beta_schedule`/`ParetoFront` path** — 2026-09-15
(`campaigns/2026-09-15-ebops-accuracy-eval/`), inferred (not confirmed; see Published effect)
with the documented "unconstrained best" reporting pitfall as its outcome; read that campaign's
run configs (not just its eval/plot scripts) to confirm the mechanism before scheduling this card.

**Combines with.** Q06 (selection rule interacts with how noisy the controller's approach to
target is — PID's closed loop is expected to hover near target with less variance than a
piecewise schedule tuned for a different run); Q07 (the ladder needs a controller choice at
every rung, and it need not be the same choice at each rung).

**Testable prediction (A07-N64, 350k).** PID with a higher integral gain (or added derivative
damping) should increase the fraction of seeds reaching a *feasible* checkpoint (the STUDY's
stated null, "fewer than 6 of 8 seeds feasible") relative to the anchor's own PID gains, without
moving the selected-checkpoint AUC much. The piecewise path, re-run at exactly 350k with the
2026-09-15 schedule shape, should reproduce that campaign's feasible/infeasible outcome — if it
does not, the difference (STUDY vs. that campaign) is itself worth reporting.

---

### Q05 — Genuinely moving EBOPs target (new mechanism, not the existing β schedule)

**Mechanism, and why this is a NEW card, not Q04 relabeled.** Code inspection
(`ebops_target.py:54-82`, `train.py:106-163`) shows the existing "gradual" machinery
(`beta_schedule`) schedules **β** (the loss weight), against a **fixed** `threshold`/
`target_ebops` throughout training — there is no code path anywhere in `bnhgq2` where the
target itself moves. This card is the proposal to build that: ramp `target_ebops` down from the
initial measured EBOPs (24.8M at N=64) to 350k over a fraction of training, i.e. the ceiling
`BudgetMonitor` checks against (`ebops_target.py:81`, currently set once by `resolve_budget`)
would need to become a function of epoch.

**Why it could matter for binary weights here.** A hard 350k ceiling from epoch 0 may force the
free-width optimizer to compress activations before the binary-weight STE's own training
dynamics have stabilized (the STE already introduces a bounded-but-nonzero gradient distortion,
`bitnet_binary_ste`, `qat.py:43-65`); a moving target that starts loose and tightens could let
weight training settle first. This is a genuinely different mechanism from Q04's β schedule: Q04
changes HOW HARD the pressure is at a fixed goalpost; this card changes WHERE the goalpost is.

**Primary source.** No external paper specifies target-annealing for an EBOPs-style budget;
internal precedent is limited to the ADJACENT (not identical) `beta_schedule` mechanism, whose
2026-09-15 run is the closest analogue and the reason this card should be scheduled cautiously,
not as a repeat.

**Published effect.** No prior number — this exact mechanism (moving ceiling) has not been run
here; the 2026-09-15 result is for the DIFFERENT (β-schedule, fixed-ceiling) mechanism and must
not be quoted as if it evaluated this card.

**Knob or code change.** Requires a real code change to `BudgetMonitor`: `self.target`
(`ebops_target.py:97`) would need to become a callable-of-epoch rather than a scalar, and
`resolve_budget` would need a schedule spec analogous to `beta_schedule`'s `[epoch, value, kind]`
triples. T1-T2 tier: ~40-60 lines, plus a regression test that a schedule whose final value is
350k and whose interpolation is "constant" from epoch 0 reduces byte-identically to the current
hard-target behavior (a required equivalence check before this is trusted).

**Hazards.** Same EBOPs-accounting non-issue as every card here — `compute_ebops` measures
actual widths at every epoch regardless of what the target is doing, so a moving target is
measured correctly. The hazard, learned from the ADJACENT 2026-09-15 incident even though the
mechanism differs, is entirely about **selection semantics under a target that isn't yet at its
final value**: `stop_on_target`/checkpoint-saving logic (`ebops_target.py:104-106,152-155`) must
key off the FINAL target only, and any intermediate "feasible at the current (loose) target"
epoch must not be saved as if it met the eventual 350k ceiling — the exact class of error the
existing convention warns against (`docs/conventions/quantization-and-cost.md:34`), applied to a
new mechanism that doesn't exist yet, so the guard must be built in from the start, not patched
in after a repeat of the incident.

**Tried here?** **No — this exact mechanism (moving ceiling) is untried.** The 2026-09-15
`beta_schedule` run is adjacent, not this; read it for the general shape of what goes wrong with
"gradual" EBOPs control, but do not treat it as evidence for or against this specific card.

**Combines with.** Q04 (an orthogonal lever on the same convergence problem — worth comparing,
not combining, in a first pass, since combining two novel controller mechanisms in one arm makes
either failure unattributable).

**Testable prediction (A07-N64, 350k).** A target that starts loose and tightens to 350k should
increase the fraction of seeds reaching a feasible final checkpoint relative to the anchor's
hard-350k-from-epoch-0 PID (same logic as Q04's prediction, different mechanism), with final
selected-checkpoint AUC within noise of the anchor's — both should converge to the same 350k
ceiling by training's end.

---

### Q06 — Cost-first selection (`min_ebops`) vs. `max_auc`

**Mechanism.** `BudgetMonitor.selection` already supports two values (`ebops_target.py:101-103`,
`:138-148`): `max_auc` (the anchor: highest val macro-AUC among budget-feasible epochs) and
`min_ebops` (lowest EBOPs among budget-feasible epochs, tie-broken by later epoch,
`ebops_target.py:139-140`). This card runs the anchor recipe with `selection="min_ebops"`
instead.

**Why it could matter for binary weights here.** Because binary weights already fix the
weight-side EBOPs term, `min_ebops` selection under a 350k *ceiling* (not a fixed point) will
tend to pick the epoch with the narrowest activation widths that still clears the budget check
— potentially a much smaller effective EBOPs than 350k, trading AUC for headroom. This directly
tests whether "iso-EBOPs" comparisons to Chang's numbers (STUDY `[L2]`) should use `max_auc` (as
now) or should instead report the Pareto front rather than a single selection rule.

**Primary source.** `docs/conventions/quantization-and-cost.md:31-33`: "Rule of record: the
checkpoint with the highest validation macro-OvR AUC among checkpoints at or under the budget…
If no checkpoint is feasible, say 'no feasible checkpoint'; do not report the unconstrained best
(the gradual-schedule arm, 2026-09-15)." This convention already exists and this card is
proposing to deliberately break it in one labelled arm for comparison, not to change the rule of
record.

**Published effect.** No prior number under `min_ebops` on our own model; not found in
tried-already as of this writing.

**Knob or code change.** Config-only: `train.ebops.selection: "min_ebops"`
(`ebops_target.py:101`). T0 tier, already wired.

**Hazards.** No EBOPs accounting difference (same `compute_ebops` call every epoch,
`ebops_target.py:123`). The hazard is purely interpretive: a `min_ebops` arm's headline AUC
number is not comparable to the anchor's `max_auc` number without stating the selection rule
explicitly — exactly the convention's own warning. No DSP risk beyond the anchor's (binary
weights, zero DSP thesis unaffected by selection rule, which only changes which *checkpoint* is
kept, not what the model computes).

**Tried here?** Not found; flag as untried.

**Combines with.** Q07 (a Pareto sweep is the generalization of running both selection rules
at several targets); Q04/Q05 (selection rule and controller behavior jointly determine how many
feasible epochs exist to select from).

**Testable prediction (A07-N64, 350k).** `min_ebops` selection should land at a measured EBOPs
noticeably below 350k (the budget is a ceiling, and the controller likely overshoots downward
once feasible) with a validation macro-AUC below the `max_auc` arm's — a real Pareto trade, not
free.

---

### Q07 — EBOPs target ladder as a Pareto sweep

**Mechanism.** Run the identical anchor recipe at multiple `target_ebops` values —
175k/350k/700k/1.4M/5M — to trace an accuracy-vs-cost curve rather than a single point. The
STUDY's arms B (175k) and C (5M) already instantiate the two ends of exactly this ladder
(`campaigns/2026-09-26-training-batch/STUDY.md:88-91`); this card is the request to fill in the
middle (700k, 1.4M) and treat the whole set as one Pareto object rather than independent single-
target arms.

**Why it could matter for binary weights here.** A single-point iso-EBOPs comparison to Chang's
79.4% (STUDY's whole question) cannot distinguish "binary weights are worse at this budget" from
"binary weights have a different knee in the curve" — the ladder is the only way to know whether
our architecture's AUC-vs-EBOPs curve crosses theirs, runs parallel below it, or converges at
high budget. This is a combination/read-out card more than a new mechanism: every point reuses
Q01-Q06's machinery unchanged, varying only `pid.target_ebops` (or `target_ratio`).

**Primary source.** Sun et al. (arXiv:2510.24784) report only the single 350k target with no
accuracy-vs-EBOPs Pareto plot (`research-log.md:536`, already logged as an absence); the ladder
concept itself is standard multi-objective optimization practice, not paper-specific here.

**Published effect.** No prior Pareto curve exists in the reference paper to compare against —
this is explicitly the gap `[L2]`/`research-log.md:536` names.

**Knob or code change.** Config-only per point: `pid.target_ebops` (or `target_ratio`) value,
5 configs total, reusing arm A's config as a template. T0 tier per point; the "combination" is
in how experiment-designer schedules and reads out the set (DELTA.md's job, not this card's).

**Hazards.** Same accounting as every EBOPs card — `compute_ebops` is target-independent, so
each point is measured consistently. The Pareto-curve hazard is entirely about **fair
comparison across points**: a lower target may fail to converge for more seeds (STUDY's own
null hypothesis framing, "fewer than 6 of 8 seeds feasible" — arm B at 175k is the STUDY's own
stated stress case, `STUDY.md:89`), so the curve must report a feasible-seed-count alongside AUC
at each point, not just a mean that silently drops infeasible seeds.

**Tried here?** Arms B and C of the anchor STUDY already occupy the two endpoints; the middle
targets (700k, 1.4M) are untried as of this writing.

**Combines with.** Everything in this family — the ladder is the read-out axis for Q01-Q06 and
Q10-Q14 alike (each could in principle be re-run at every rung, though Delta's budget will
likely restrict combinatorics to the anchor's single 350k rung for most cards).

**Testable prediction (A07-N64).** AUC should rise monotonically with target EBOPs across the
ladder with diminishing returns above ~1.4M (approaching the FP32/unconstrained ceiling), and
the seed-feasibility rate should fall as the target tightens below 350k (arm B's stress case).

---

### Q08 — Softmax output bits / attention-probability precision

**Mechanism.** The anchor fixes softmax's output precision via `sm_out_bits` (default
`max(ab, 10)`, i.e. at least 10 bits regardless of the activation-width target, `qat.py:434-
437`) and both the exp/inv intermediate tables and post-softmax attention-probability quantizer
(`attn_iq`, `qat.py:489-492`) at STATIC widths, not part of the `free`-width EBOPs pressure. This
card asks what happens if `sm_out_bits`/`attn_iq` are (a) swept as a fixed grid (6/8/10/12 bits)
or (b) folded into the `free`-width/MonoL1 machinery so the controller can shrink them too.

**Why it could matter for binary weights here — corrected against the HGQ2 source.** Reading
`hgq.layers.softmax.QSoftmax._compute_ebops` directly (not just our wrapper) shows softmax IS
priced in EBOPs, contrary to a first-pass reading of our own docstring comment ("fixed softmax
tables remain fixed", `ebops_target.py:4-5`, which describes their WIDTH being frozen, not their
absence from the total): the layer computes `substract_ebops` (the stable-softmax max-subtraction,
costed from the input or exp-table bits), `accum_ebops` (the sum over the softmax axis, scaled by
the number of terms), and `mult_ebops = sum(exp_bits * inv_bits)` — i.e. the reciprocal
multiply — and sums all three into the layer's own `_ebops`, which `compute_ebops`'s
`per_layer` loop collects like any other layer (`ebops_calc.py:21-23`, gated only on
`enable_ebops`, which `QSoftmax` sets from the global config, `softmax.py:35-38`). Separately,
`attn_iq`/`sm_out_bits` feed the POST-softmax `_attn_ctx` QEinsum's multiply term directly
(`qat.py:489-495`), which is unambiguously traced as ordinary matmul EBOPs. **So: sweeping
`sm_out_bits` WILL move the reported 350k total in both places** — this reverses the hazard and
prediction from an earlier draft of this card, which wrongly treated softmax as untracked.

**What genuinely IS a blind spot, restated precisely.** The blind spot is not "softmax is
untracked" — it is the SAME accumulator gap named in `[L2]` applied to softmax's internals:
`accum_ebops`'s summation over the softmax axis and `_attn_ctx`'s A·V accumulation both sum
`T` (or `T²`) terms, and EBOPs' multiply/accumulate formula prices the OPERAND widths, not the
GROWING accumulator width that summing many terms actually requires in hardware (the same gap
Q13 quantifies exactly for the binary matmuls). Softmax is not specially exempt; it inherits the
family's one real gap.

**Primary source.** `hgq.layers.softmax.QSoftmax._compute_ebops`, read directly from the local
HGQ2 install (`~/hgq2/HGQ2/src/hgq/layers/softmax.py:134-155`) — verified 2026-09-26. `hgq.layers`
import site: `qat.py:30`.

**Published effect.** No prior number for our model isolating this sweep; the reference paper's
own EBOPs total presumably also includes their softmax's cost by the same HGQ2 mechanism, but
their softmax implementation details are unstated in the parts of Table 1 we have read (STUDY
`[L2]:558`, "fixed 10-bit softmax output … as a quantified limitation" — that line is about the
DIFFERENCE in implementation choice, not about softmax being untracked in either paper's EBOPs).

**Knob or code change.** Config: `quant.softmax_out_bits`, `quant.softmax_out_i` already exist
as config keys (`qat.py:434-435`); sweeping them is T0. Folding softmax into the free-width
EBOPs machinery (b) is a real code change: `_static_act`/`_table` calls in `softmax()`
(`qat.py:439-454`) would need to become `_free_act` calls, T1-T2.

**Hazards.** No EBOPs blind spot for this specific knob (corrected above) — the accumulator gap
that DOES apply here is the same one `[L2]`/Q13 already name, not a softmax-specific one. DSP
risk, corrected: `QSoftmax`'s exp/inv steps are LOOKUP TABLES (`exp_oq_conf`/`inv_oq_conf =
_table(...)`, `qat.py:453-454`), not a division/CORDIC circuit — the resource risk from widening
`sm_out_bits` is BRAM/LUT table depth (`_table`'s `(i0, f0)` sets the table's addressable range),
not DSP-eligible division logic; a wider table is a bigger ROM, not a multiplier.

**Tried here?** Not found; flag as untried.

**Combines with.** Q09 (LUT-native softmax internals are an alternative to widening/narrowing
the same tables); Q13 (the accumulator-gap correction applies identically to softmax's
`accum_ebops` term and to the binary matmuls — one metric should cover both).

**Testable prediction (A07-N64, 350k).** Narrowing `sm_out_bits` below 10 should measurably hurt
validation macro-AUC (softmax probabilities are the attention weights) AND measurably LOWER the
reported EBOPs total (both effects move together, since this knob is fully traced) — a real
Pareto trade along this one axis, not an invisible one.

---

### Q09 — LUT-implemented nonlinearities (QAffinedUnaryFunctionLUT / HGQ-LUT)

**Mechanism.** Chang's non-transformer branches (`get_transformer`, `get_llformer`,
`reference-code/HGQ2-examples/jsc150/model.py:194,198`) replace a pre-attention bounding
nonlinearity with `QAffinedUnaryFunctionLUT('tanh')` — a trained affine-plus-lookup-table
approximation of tanh, synthesized directly as an FPGA LUT rather than computed arithmetically.
HGQ-LUT (arXiv:2604.22293) generalizes this to whole "L-LUT" neurons: any small function of a
few multi-bit inputs, trained as a tiny tanh MLP at GPU speed, compiled to physical K-input
LUTs, with a differentiable LUT-count surrogate replacing EBOPs for those layers specifically
(`literature/hls4ml-fpga-triggers/2604.22293_hgq_lut.md`, "Method" section).

**Why it could matter for binary weights here — corrected against the anchor's actual config.**
The A07-N64 anchor is `norm="none"` (STUDY `[L2]:613`, "a binary-weight, norm-free ReLU
transformer"; STUDY.md:83,155,461 all confirm `norm none` in every arm of the training-batch
STUDY), i.e. the anchor has ALREADY dropped `PSubLN` entirely (`qat.py:377-380`'s identity
passthrough) — there is no SubLN in this delta to replace. The 58%-of-DSPs/40%-of-LUTs SubLN
figure belongs to the ARCHIVED n8 model (Round 14), not to A07-N64; citing it here without that
label would misattribute an archived cost to the current anchor. The correct framing of this
card is therefore **adding** a bounding nonlinearity to an already norm-free model — exactly
what Chang's `get_transformer` does (`QAffinedUnaryFunctionLUT('tanh')` immediately before
attention, `model.py:194,198`) instead of using either SubLN or nothing. This is a genuinely
open question for the anchor: does a cheap LUT-tanh bound recover any of the range-control
benefit normalization would have given, at a much smaller resource cost than SubLN would have
cost if it were present?

**Why it could matter for binary weights here (HGQ-LUT specifically).** HGQ-LUT's own numbers
(5,667 LUT / 0 DSP at parity accuracy vs. HGQ at 10,182 LUT on the 16-feature jet task; a
LUT-native GNN at 39,765 LUT vs. 244,515 for HGQ at −1.4 accuracy points on the 64-particle task)
show LUT-native training reaching 0 DSP **without any binary weight constraint at all** — a
direct existence proof that 0-DSP is achievable by a different mechanism than ours, and a
genuine threat to the "binary weights are the/a route to 0 DSP" framing if their LUT budget at
comparable accuracy undercuts ours. This is flagged, not resolved, here.

**Primary source.** `reference-code/HGQ2-examples/jsc150/model.py:194,198` (code, in this repo);
arXiv:2604.22293 (Sun et al., HGQ-LUT, FastML 2026), full dossier at
`literature/hls4ml-fpga-triggers/2604.22293_hgq_lut.md`. Date accessed: 2026-09-05 (dossier),
re-read 2026-09-26.

**Published effect.** HGQ-LUT, 16-feature jet task: 5,667 LUT / 0 DSP / 9.2 ns at parity accuracy
with HGQ at 10,182 LUT / 36.3 ns (dossier, "The numbers that matter to us", table not
re-verified page-by-page in this pass — flagged in the dossier itself as HTML-extracted, needing
PDF re-check before print citation). **Not comparable to our numbers**: different dataset
(16-feature, not our (N,3) L1-realistic convention), different model family (LUT-native
dense/GNN, no transformer, no binary weights), no BitNet-style transformer reported in this
paper at all.

**Knob or code change.** Genuinely new module: `QAffinedUnaryFunctionLUT` (or the full L-LUT
layer type) is not imported anywhere in our `bnhgq2` package today. T2 tier: import the layer
from `hgq.layers`, decide where it sits in the block (added before attention, before the FFN, or
both — the anchor is norm-free, so this is an ADDITION, not a replacement of anything currently
present), and verify it composes with the binary-weight einsum layers (`bitnet_binary_ste` is
entirely separate machinery — no conflict expected, but unverified). Estimate: 50-100 lines plus
a build/reload gate.

**Hazards.** HGQ-LUT explicitly uses a **different resource surrogate than EBOPs** for its L-LUT
layers (`literature/hls4ml-fpga-triggers/2604.22293_hgq_lut.md`, "Resource surrogate": a
differentiable LUT-count formula, not the multiply/accumulate EBOPs sum). If we adopt any
L-LUT-style layer, `compute_ebops`/`trace_minmax` (`ebops_calc.py`) will almost certainly NOT
account for it correctly — either reporting zero (if the layer doesn't register `enable_ebops`)
or a meaningless multiply-based estimate for a lookup-table operation. Any EBOPs number quoted
for a model containing an L-LUT layer needs an explicit caveat or a parallel LUT-count metric,
per `docs/conventions/quantization-and-cost.md:23-25`'s rule that augmented cost conventions are
"never presented as native HGQ2 totals." DSP: LUT-native layers are 0-DSP by construction (no
multiply-accumulate at all), so this card is DSP-safe, but it also does not exercise or validate
our specific "binary weights -> 0 DSP" claim — it is an alternative mechanism to the same
headline number.

**Tried here?** Not found in the inventory.

**Combines with.** Q08 (a LUT-native softmax internal is the same idea applied to softmax's
exp/reciprocal instead of a bounding nonlinearity).

**Testable prediction (A07-N64, 350k).** Adding a LUT-tanh bound before attention (to the
already norm-free anchor, not replacing anything) should modestly IMPROVE validation macro-AUC
relative to the plain norm-free anchor (some range control is plausibly better than none, at
near-zero added multiply-accumulate cost) while adding a small, separately-reported LUT-count
figure that is NOT part of the anchor's 350k EBOPs total (per the Hazards section, this layer
type needs its own resource surrogate, not an EBOPs entry).

---

### Q10 — Softmax-free / cheap attention alternatives

**Mechanism.** Replace the softmax nonlinearity in attention with a cheaper FPGA primitive:
ReLU-attention or sigmoid-attention (element-wise nonlinearity instead of a normalized
exponential, no division), a base-2 exponent approximation of softmax (bit-shift instead of a
true exponential, exploiting binary floating-point structure), or a fixed-constant
normalization (divide by a static value instead of the row-sum, trading exactness for removing
the reciprocal entirely).

**Why it could matter for binary weights here.** Softmax's `inv_iq_conf` reciprocal step
(`qat.py:449-452`) is the single non-multiply-accumulate, non-additive operation in an otherwise
add/multiply-only (binary-weight matmul + ReLU) network — removing it removes the one place a
division-like primitive could force non-LUT hardware (a CORDIC or DSP-based reciprocal in some
HLS backends) regardless of how narrow the surrounding activations are. This is a genuinely
binary-weight-relevant card: it is the last non-additive/non-multiplicative operation standing
between this architecture and an all-adder-tree design.

**Primary source, located and verified by search 2026-09-26 (not yet in `literature/INDEX.md`).**
(1) Wortsman, Lee, Gilmer, Kornblith, "Replacing softmax with ReLU in Vision Transformers,"
arXiv:2309.08586 — ReLU-attention divided by sequence length approaches softmax-attention's
scaling behavior on ImageNet-21k ViTs; NOT jet tagging, NOT a binary-weight model, NOT FPGA. (2)
Ramapuram et al., "Theory, Analysis, and Best Practices for Sigmoid Self-Attention,"
arXiv:2409.04431 — sigmoid replacing the softmax normalization; same transfer caveats. (3)
Stevens, Venkatesan, Dai, Khailany, Raghunathan, "Softermax: Hardware/Software Co-Design of an
Efficient Softmax for Transformers," DAC 2021, arXiv:2103.09301 — base-2 exponent replacement +
low-precision softmax + online normalization; a search-summary characterization of its
efficiency numbers was seen but NOT independently verified against the paper (no WebFetch of
this specific source in this pass, same rule as A2Q's abstract-only numbers, Q13) — no number
from it is quoted here. None of these three papers target hls4ml, CMS L1, or a binary-weight
model; all are transfer candidates for the MECHANISM only, not for any number.

**Published effect.** ReLU-attention (2309.08586) and sigmoid self-attention (2409.04431): both
report accuracy comparable to softmax at ViT/ImageNet scale (exact numbers not extracted in this
pass — read the papers before citing a specific accuracy delta). Softermax (2103.09301): **no
number quoted** — an efficiency claim was seen in a search summary but not fetched/verified
against the paper itself in this pass; a dossier or direct fetch is required before any number
from this source is cited outward.

**Knob or code change.** T2 tier: `softmax()` (`qat.py:439-454`) would need a new branch
(`quant.attn_kind: "softmax"|"relu"|"sigmoid"|"const_norm"`) replacing `QSoftmax` with a
`keras.layers.ReLU`/`Activation('sigmoid')` plus a normalization step, and every downstream
`attn_iq`/`ctx` quantization site would need re-deriving since the numeric range of a
ReLU-attention output differs fundamentally from a softmax output (no longer sums to 1 per row).
Estimate 80-150 lines including calibration changes.

**Hazards.** `compute_ebops` would correctly re-trace whatever multiply/add operations remain
(a ReLU-attention path is fewer distinct operation types than softmax, likely fewer traced
EBOPs terms) — no blind spot expected there, but the *comparison* to the anchor's EBOPs total
would mix "same operations, different width" cards with "structurally different operation count"
in one number, which needs a footnote just like weight-type changes do (STUDY's own `[L2]`
pattern). DSP risk: this card is specifically aimed at REDUCING DSP/CORDIC risk from softmax's
reciprocal, so it is a candidate DSP *improvement*, not a hazard, if the accuracy cost is
acceptable — but accuracy risk is real and unquantified (no primary source with a number).

**Tried here?** Not found; the primary sources are now located (see above) but not yet read past
abstract/search-summary level — a dossier pass on all three is the natural next step before
scheduling code.

**Combines with.** Q08 (this card removes Q08's object entirely rather than tuning its
precision); Q09 (a LUT-native reciprocal is an alternative solution to the same reciprocal-cost
problem without removing softmax's semantics).

**Testable prediction (A07-N64, 350k).** ReLU- or sigmoid-attention should reduce validation
macro-AUC relative to the anchor (softmax's competitive normalization is doing real work in a
5-class jet task with within-jet particle competition for attention mass) — direction: AUC down,
EBOPs-per-synthesized-LUT ratio improved (untested claim, no source).

---

### Q11 — Input quantizer bit-width matched to L1 Puppi candidate precision

**Mechanism.** Set the model's input quantizer (`iq` on `input_proj`, currently governed by the
same `act_iq`/`_free_act` machinery as every other datalane, `qat.py:395-411`) to a FIXED width
matching whatever precision L1 PUPPI candidates actually arrive at from Correlator Layer 2,
rather than letting the input width float under the same EBOPs pressure as internal
activations — on the reasoning that upstream precision is a hard external constraint, not a
tunable one.

**Why it could matter for binary weights here.** If PUPPI candidates arrive at, say, 16 bits
per feature (an unverified prior below), no amount of internal activation-width compression can
recover information already lost or preserved at the input; conversely, if our input quantizer
currently trains BELOW the true input precision (throwing away resolution the front-end already
provides for free, since it costs nothing extra upstream), that is compression we're paying an
AUC cost for without a matching hardware saving anywhere but the very first layer.

**Primary source searched.** CMS "Reconstructing jets in the Phase-2 upgrade of the CMS Level-1
Trigger with a seeded cone algorithm" (arXiv:2310.08062) — fetched 2026-09-26 and read for this
number; **it does not state per-feature PUPPI candidate bit widths**, only that Layer 1 transmits
candidates to Layer 2 over 3-6 links at 25 Gb/s per detector region and that the deregionizer
truncates to a fixed 128-particle list. A companion CMS TWiki/CDS search for "Particle Flow and
PUPPI in the Level-1 Trigger at CMS for the HL-LHC" (arXiv:1808.02094) was located but not read
in full in this pass. Our own `2402.01876` dossier (the source of our (N,3) L1-realistic input
convention, `literature/hls4ml-fpga-triggers/2402.01876_ultrafast_jet_classification_hl_lhc.md`)
was re-checked in this pass and states no per-feature input precision either — its relevance is
the (N,3) feature CHOICE, not a bit-width. A different published L1 tagger, WOMBAT
(arXiv:2505.05532, jet substructure/boosted-Higgs tagging), was checked directly by fetching the
abstract/paper (2026-09-26): **it does NOT state a 16-bit (or any specific) FPGA deployment
precision** — an earlier draft of this card attributed a "16 bit precision... deployment on the
FPGA" quote to WOMBAT from a search-result snippet without verifying the source, and that
attribution is WRONG; the quote's true source was not re-identified in this pass (candidates
from the same search included an "L1Phase2NNPuppiTau" CMS TWiki page, not re-checked here). Do
not cite WOMBAT for an input precision number.

**Published effect.** **No PUPPI-specific number found and no substitute proxy verified in this
pass.** State plainly: we do not have a citable per-field PUPPI bit-width, or even a verified
labelled proxy from a different tagger, as of this search. The exact spec most likely lives in
the CMS Phase-2 L1T TDR (CERN-LHCC-2020-004), the correlator firmware's GitHub dataformat
headers, or the CMS TWiki "L1Phase2NNPuppiTau" page turned up by the same search (unchecked) —
none was fetched and confirmed in this pass. This card cannot be scheduled with a real target
width until a genuinely sourced number is found; do not substitute an unverified search snippet
as a placeholder.

**Knob or code change.** Config-only once the number is known: pin the `input_proj` iq_conf to
a static `_static_act(N, i0)` at the sourced width instead of `act_iq()`
(`qat.py:395-411`'s `dense_einsum` for `name="input_proj"`). T0-T1 depending on whether a
per-layer override already exists (needs ml-engineer's code-surface check).

**Hazards.** No EBOPs blind spot — a static input width is traced exactly like any other static
quantizer. The hazard is entirely upstream-mismatch risk: if we pin a wrong width (because the
real number wasn't found), we either (a) throw away real resolution the trigger provides for
free, understating achievable AUC, or (b) train at a resolution the trigger cannot actually
deliver, overstating deployable AUC — a genuine transfer-legitimacy issue, not a hazard to EBOPs
or DSP specifically.

**Tried here?** Not found.

**Combines with.** Nothing else in this family directly; it is an input-side constraint that
should gate what Q01-Q07 sweep over for the input layer specifically, once sourced.

**Testable prediction.** None — this card cannot generate a directional prediction until the
primary-source bit-width is found; flag to sweep-mode as an open search item rather than predict
blind.

---

### Q12 — Channel pruning via 0-bit widths (a measurement card, not a bound-relaxation ask)

**Mechanism, corrected against the HGQ2 quantizer source.** The `free`-width quantizer's
integer/fractional bit bounds ARE already negative-capable (`ic=MinMax(-8, 12)`,
`fc=MinMax(-8, 16)`, `qat.py:301`), and `hgq.quantizer.internal.fixed_point_quantizer`'s own
`fbits` property is `ops.relu(self.i + self.f)`
(`~/hgq2/HGQ2/src/hgq/quantizer/internal/fixed_point_quantizer.py:437`, verified 2026-09-26) —
i.e. total reported width is CLAMPED to zero once `i+f` goes negative, so **0-bit collapse under
MonoL1 pressure is already reachable in the anchor's own config, with no bound relaxation
needed.** The card as originally framed ("relax the bounds to allow pruning") is unnecessary; the
real open question is whether the anchor's 350k-EBOPs training ACTUALLY drives any channel to
this state, and if so, whether hls4ml/HGQ2's export and HLS conversion path elides a 0-bit
datalane as removed logic or merely synthesizes a 0-width (still-present) wire.

**Why it could matter for binary weights here.** Combined with per-channel granularity (Q01),
this is potentially a way to shrink the *effective* model size (fewer active channels feeding
binary matmuls) on top of shrinking each surviving channel's activation width — two
complementary compression axes from the same regularizer family, and specifically attractive for
a binary-weight model because pruning a channel removes an entire column of ±1 weights (and
their adders) rather than reducing weight precision, which is not a lever this design has at
all otherwise (weight width is fixed at 1 bit by the thesis).

**Primary source.** HGQ-LUT (arXiv:2604.22293) documents exactly this pattern for its L-LUT
inputs/outputs: "individually quantized and can go to 0 bits (pruned)"
(`literature/hls4ml-fpga-triggers/2604.22293_hgq_lut.md`, "Method"), on a different layer type
(L-LUT, not a plain HGQ2 KIF datalane) — the mechanism is documented there for a related but
distinct quantizer family, not for our exact `_free_act` KIF path; whether stock HGQ2's KIF
quantizer supports true 0-bit collapse (vs. just very small width) needs verification against
the HGQ2 source, not assumed here.

**Published effect.** No prior number for a plain (non-L-LUT) HGQ2 KIF quantizer collapsing to
0 bits; HGQ-LUT's number is for a different layer type and not directly transferable.

**Knob or code change.** No config change needed to REACH the pruning regime (it's already
possible under the anchor's own bounds); the actual work is a MEASUREMENT script, T0-T1: read
`width_snapshot`'s `bits`/`i`/`f` values (`ebops_target.py:35-51`) from the anchor's saved
`activation_widths.jsonl` history at the selected 350k checkpoint and count near-zero-width
channels/sites. Then, separately, verify (T0 investigation) whether HGQ2's `trace_minmax`/HLS
export path actually treats a 0-bit datalane as "channel removed" or merely as "width 0, still
synthesized as a wire" — if the latter, any pruning the anchor already does buys nothing on
hardware even though `compute_ebops` would correctly show near-zero EBOPs contribution for that
channel (the multiply term scales with bitwidth, so 0 bits -> ~0 EBOPs, which IS captured).

**Hazards.** EBOPs is NOT a blind spot here — a channel driven to 0 bits correctly shows ~0
EBOPs contribution via the multiply-term formula in `compute_ebops`. The hazard is the reverse
of the usual one: EBOPs may show a *real* saving that the actual HLS synthesis does not realize,
if hls4ml still allocates a wire/register for a 0-bit signal rather than eliding the channel
entirely — a case to check against synthesis, not assume from EBOPs. No DSP risk (activation
side only).

**Tried here?** Not found as a measurement; the mechanism that would produce it (free-width
training under MonoL1) IS already the anchor's own recipe — this card asks whether it already
happened, not whether to enable something new.

**Combines with.** Q01/Q02 (per-channel or per-element granularity is a PREREQUISITE for
individual channels to be prunable at all — under tensor granularity the whole tensor shares one
width and cannot selectively collapse); Q03 (a lower init width reaches the pruning-eligible
regime with less required compression).

**Testable prediction (A07-N64, 350k).** Re-reading the anchor's OWN `activation_widths.jsonl`
at the selected checkpoint (no new training needed): under tensor granularity (the anchor's
actual setting), 0-bit collapse of an ENTIRE site is unlikely (one bad channel would drag the
whole tensor's shared width down, which the optimizer should avoid) — so the anchor itself is
predicted to show NO fully-collapsed sites, and this card's real yield is confirming that
per-channel granularity (Q01) is a precondition for Q12 to matter at all, not that Q12 will
change the anchor's own reported AUC.

---

### Q13 — Accumulator-aware quantization (A2Q / A2Q+)

**Mechanism.** A2Q (Colbert et al., "A2Q: Accumulator-Aware Quantization with Guaranteed
Overflow Avoidance," arXiv:2308.13504, an extended version of arXiv:2301.13376) constrains the
L1-norm of a layer's weights, scaled to a target accumulator bit width, during training — a
weight-normalization-style penalty that provably bounds the accumulator's required width and,
as a side effect, induces unstructured weight sparsity. A2Q+ (arXiv:2401.10432) improves the
accuracy-at-fixed-accumulator-width trade further. Both target exactly the accumulator, the
component our EBOPs formula excludes.

**Why it could matter for binary weights here.** This is the paper that directly answers
`[L2]`'s stated gap: "EBOPs leaves out the accumulator, which is the whole cost of a ±1 adder
tree" (`campaigns/2026-09-26-training-batch/STUDY.md:44, 597`). A2Q's mechanism is a WEIGHT
penalty (L1-norm constrained by target accumulator width), which is orthogonal to binarization
in general but has a specific tension with our thesis: our binary weights are UNCONSTRAINED in
magnitude before absmean-binarization (`bitnet_binary_ste`, `qat.py:43-65`) — every weight
contributes equally (±β) to every accumulation regardless of the latent weight's magnitude, so
A2Q's core lever (shrinking the effective L1 norm to bound accumulator growth) has no natural
analogue in a model where every effective weight is already ±β by construction. Applying A2Q's
actual mechanism would mean constraining which/how many inputs are summed (sparsity), not
weight magnitude, since magnitude is already fixed post-binarization.

**Primary source.** Colbert, Yuan, Franco, "A2Q: Accumulator-Aware Quantization with Guaranteed
Overflow Avoidance," arXiv:2308.13504 (an expanded version of the earlier arXiv:2301.13376,
"Quantized Neural Networks for Low-Precision Accumulation with Guaranteed Overflow Avoidance");
Colbert et al., "A2Q+: Improving Accumulator-Aware Weight Quantization," arXiv:2401.10432.
Retrieved via web search 2026-09-26; abstracts and summary read, full paper not fetched in this
pass — flag for a dossier if this card advances.

**Published effect.** WebFetch of the arXiv abstract page (2026-09-26) returned only the
aggregate abstract claim ("up to a 2.3x reduction in resource utilization... 99.2% of the
floating-point model accuracy") with NO table or figure number attached and no confirmation of
which benchmark (CNN vs. transformer) it applies to — **per this campaign's own rule ("never
invent a number... quote with its table/figure or say so"), this number is NOT quotable outward
from what was retrieved in this pass.** A full-PDF read (not done here) is required before any
A2Q number appears in a STUDY or REPORT.

**Knob or code change.** Not directly portable as a knob: A2Q's constraint applies to a
CONTINUOUS weight-magnitude representation during training (an L1-norm-bounded reparametrization
of the weight update), which our latent weights `_kernel` (pre-binarization) DO have — so the
mechanism could in principle apply to the LATENT weights before `bitnet_binary_ste` collapses
them, constraining how the latent distribution evolves even though the forward pass ends at ±β.
This is a genuinely new regularizer on `_kernel` in `BitQEinsumDense`/`BitQDense`
(`qat.py:72-109`), T2 tier, ~40-80 lines, and its effect on binarized-forward training dynamics
is unverified — a real research question, not a drop-in port.

**A cheaper alternative that closes the same gap without a training method.** For a ±1-weight
layer specifically (unlike A2Q's general-magnitude setting), the accumulator width needed to sum
`n` products of a `b`-bit activation by a ±1 weight WITHOUT overflow is exactly computable in
closed form and requires no training change at all: each product has magnitude bound by the
activation's own range, so summing `n` of them needs `b_acc = b_act + ceil(log2(n))` bits (fan-in
`n` doubles the needed headroom by one bit each time it doubles) — no L1-norm constraint is
needed because the weight magnitude is already fixed at exactly 1 by the thesis itself. This is a
~20-line POST-HOC metric addable to `compute_ebops`'s `per_layer` loop (`ebops_calc.py:15-24`):
for every binary layer, read its fan-in and its input quantizer's `bits`, compute
`b_act + ceil(log2(fan_in))` per accumulation, and report an "accumulator-inclusive EBOPs"
number ALONGSIDE (never replacing) the native total, per
`docs/conventions/quantization-and-cost.md:23-25`'s rule that augmented conventions are reported
as their own quantity. **This closes `[L2]`'s stated gap directly and exactly for our specific
weight type, and is a smaller, more certain deliverable than porting A2Q's training method** —
recommend this as the near-term action item from this card, with A2Q itself as a longer-shot
follow-up only if the closed-form correction alone isn't judged sufficient.

**Hazards.** This is the single card in the family that most directly addresses whether "EBOPs
as computed by our `compute_ebops` would reflect the change": **it would not, at all — for A2Q
as a training method.** The closed-form correction above, by contrast, is entirely computable
from what `compute_ebops` already traces (widths, fan-in) plus one added formula — it is a
reporting fix, not a hazard.
`compute_ebops`/`ebops_calc.py`'s formula has no accumulator term (per the file's own docstring
distinguishing it from the "HGQ-v1 Eq.5 convention" and per the extensive accumulator-ambiguity
discussion already logged, `research-log.md:1897-2025`). Any accumulator-width benefit from A2Q
would be REAL on hardware (smaller adder trees, less overflow risk) but INVISIBLE to every
EBOPs number Delta reports — exactly the blind spot `[L2]` names, and this
card is the one place in Delta that would require a SEPARATE, augmented cost metric (per
`docs/conventions/quantization-and-cost.md:23-25`'s rule that such metrics are reported as their
own quantity, never as a native EBOPs total) to be evaluated honestly. No DSP risk from A2Q
itself (it reduces accumulator width, which if anything reduces DSP/adder-tree resource use);
the risk is entirely in mis-reporting its benefit as an EBOPs improvement when EBOPs cannot see
it.

**Tried here?** Not found; genuinely new to this codebase.

**Combines with.** Every other card in this family, in the sense that ANY EBOPs number reported
alongside an A2Q arm needs the accumulator-width correction stated separately — this card is as
much a measurement-methodology proposal as a training-recipe proposal.

**Testable prediction (A07-N64, 350k).** No AUC-direction prediction — A2Q's mechanism does not
obviously map onto post-binarization weights. The concrete, checkable prediction is instead
about accounting: if A2Q's accumulator-width penalty is applied to the latent kernel, the
model's REPORTED 350k EBOPs should be UNCHANGED (the accumulator term isn't in the formula) even
if the true synthesized accumulator width shrinks — i.e. this card predicts a case where EBOPs
and true hardware cost diverge, which is itself the testable claim.

---

### Q14 — Fixed-width recovery (freeze widths, then fine-tune)

**Mechanism.** Two-phase training: run the anchor's `free`-width EBOPs-pressured phase to
convergence (as now), then FREEZE every activation quantizer's learned (i, f) at their final
values (turn off `width_trainable`, `ebops_target.py:48-49`'s flag already exists to detect this
state) and continue training for additional epochs with only the model weights (latent kernels)
trainable, no further width search and no further EBOPs pressure — recovering any accuracy the
width-search phase's compression cost, now that the grid is fixed.

**Why it could matter for binary weights here.** The `free`-width search and the ±1 weight
binarization are both non-stationary, noisy training signals happening simultaneously (STE
through the binarizer, STE through the rounding quantizer, AND a moving activation grid all at
once); separating "find the width" from "fit the weights to that width" is a standard
two-phase QAT pattern (calibrate-then-fit, which our OWN `frozen`/`calib` `act_calib` mode
already does at initialization, `calibrate_activations`, `qat.py:535-568`) applied instead at
the END of width search rather than only the start — potentially recovering AUC lost to
simultaneous optimization of two moving targets.

**Primary source.** No single paper is the source of this exact pattern; it is the general
"quantize-then-fine-tune" QAT convention (traceable to BinaryConnect/early QAT practice already
in our index, `literature/qat-binary-nn-foundations/1511.00363_binaryconnect.md`) applied at the
end of an HGQ2-style width search rather than a fixed grid from the start. Our own
`act_calib="recalib"` mode (`qat.py:355-356`, "frozen but the train stage re-runs calibration at
act_recalib_epochs") is the closest existing precedent in this codebase and should be checked
against this card's mechanism before treating it as new (it is close but not identical: recalib
re-DOES calibration mid-training on a still-frozen grid type, this card freezes an already-FREE
learned grid).

**Published effect.** No prior number; our own `recalib` mode's outcome (if it has been run)
belongs in the tried-already inventory and should be checked first.

**Knob or code change.** Config/train-loop: after the EBOPs target is met (or at a fixed epoch),
set every free-width quantizer's `_i`/`_f` variables non-trainable (mirrors `_assign_if`'s
write path, `qat.py:571-582`, but toggling trainability rather than value) and continue the
optimizer with those variables excluded. T1 tier: a callback similar to `BudgetMonitor` that,
on `stop_on_target`-style trigger, walks `model.layers` and freezes width variables
(`ebops_target.py:98-100`'s `width_trainable` check shows exactly which variables to target).
Estimate 40-60 lines.

**Hazards.** No EBOPs blind spot for the frozen-width phase — once widths stop changing,
`compute_ebops` reports a constant total for the remainder of training, and that total IS the
real structural cost (no accumulator issue different from any other card here). The hazard is
schedule/budget: this doubles the effective training length (search phase + recovery phase)
against a recipe budget that is already the Sun et al. 7,000-epoch regime — a real cost to the
"~100 methods, code ready to run" scope Delta is building toward, worth flagging to
experiment-designer for the wave/budget-tier decision rather than resolved here. No new DSP
risk (weight-side dynamics unaffected; widths only get MORE fixed, not less).

**Tried here?** Check `recalib` mode's usage in the inventory before treating as untried; the
mechanism is adjacent but not identical (see Primary source, above).

**Combines with.** Q04/Q05 (a controller/schedule card determines WHEN width-search converges,
which sets when this card's freeze point should trigger); Q07 (each rung of the EBOPs ladder
could independently get a fixed-width recovery phase).

**Testable prediction (A07-N64, 350k).** A frozen-width recovery phase (added epochs, no further
EBOPs pressure) should recover some validation macro-AUC relative to the `max_auc`-selected
checkpoint from the free-width phase alone, at unchanged EBOPs (width is frozen, so
`compute_ebops` cannot move) — direction: AUC up, EBOPs flat, at the cost of additional wall-
clock training epochs.

---

## Omitted and why

- **Per-value width for the WEIGHT side** (rather than activations) is omitted as its own card:
  our weights are pinned binary by thesis (`_binary_kq`, `qat.py:228-232`), so any per-value
  weight-width idea is a ternary/multi-bit-weight baseline, not a Q-family (activation/cost)
  card — it belongs in family B (binarization) if Delta wants it, not here.
- **QSoftmax's exact internal HGQ2 implementation details** (whether `stable=True` already uses
  a max-subtraction trick that itself has a cost) were not traced line-by-line in `hgq.layers`
  source in this pass; Q08/Q10 flag softmax as a blind spot but do not fully resolve HGQ2's own
  internal softmax cost accounting — a follow-up read of the HGQ2 source itself, not this repo's
  `qat.py` wrapper, is needed before Q08's code-change estimate is trusted.
- **A dossier-depth read of ReLU-attention (2309.08586), sigmoid self-attention (2409.04431), and
  Softermax (2103.09301)** (Q10) was not done in this pass — arXiv IDs are now verified by search
  and logged below, but their numbers are search-summary level only and need a full read before
  outward citation.
- **The exact per-field bit width of L1 PUPPI candidates** (Q11) was searched and NOT found in
  the sources checked in this pass (arXiv:2310.08062 read in full; arXiv:1808.02094 and the
  2402.01876 dossier checked and confirmed silent on this number). A prior draft of this card
  wrongly attributed a "16-bit deployment precision" quote to WOMBAT (arXiv:2505.05532); a direct
  fetch of WOMBAT in this pass found NO such statement there — that attribution has been removed,
  and the quote's real source (possibly the CMS "L1Phase2NNPuppiTau" TWiki page from the same
  search, unchecked) is still unresolved. This is the single most load-bearing missing number in
  this file for deployment-reality reasoning and should be a priority follow-up search against
  the CMS Phase-2 L1T TDR (CERN-LHCC-2020-004) or the correlator firmware's GitHub dataformat
  headers, not guessed or attributed on a search snippet alone.
- **A dossier-depth read of A2Q/A2Q+** (Q13) was not done in this pass (abstract/WebFetch level
  only, which returned no table-level numbers); no A2Q number is quoted in the final card. The
  closed-form accumulator-width correction added to Q13 (`b_act + ceil(log2(fan_in))`) requires
  no dossier and is recommended as the near-term action instead of porting A2Q's training method.
- **Whether the anchor's `beta_schedule`/`ParetoFront` path (2026-09-15) or `BetaPID` (the
  training-batch STUDY) was used for any specific prior run** needed a code read
  (`ablation.py`, `train.py`) to disambiguate; both mechanisms exist and are now correctly
  attributed to Q04/Q05 rather than conflated as one "controller" card.
- **Whether HGQ2's KIF quantizer treats `fbits=0` as true hardware elision or a still-synthesized
  zero-width wire** (Q12) was not resolved from the Python source alone (`fbits =
  relu(i+f)` confirms the REPORTED width goes to zero; the HLS/hls4ml EXPORT behavior for that
  case was not traced in this pass) — flagged as the open half of Q12's measurement.
- **Combinatorial "package" cards** (e.g. "Q01 + Q04 + Q07 together") are left to
  experiment-designer's DELTA.md, per the brief's schema — each card here is a single delta from
  the anchor, and combos are the catalogue's job, not this file's.

## Log lines to append

- 2026-09-26 — A2Q: Accumulator-Aware Quantization with Guaranteed Overflow Avoidance, Colbert
  et al., arXiv:2308.13504 (expands arXiv:2301.13376) — https://arxiv.org/abs/2308.13504 —
  addresses the `[L2]` EBOPs-excludes-the-accumulator gap in general, but its L1-norm-bounded
  weight-magnitude mechanism has no analogue post-absmean-binarization (our effective weights
  are fixed-magnitude ±β already); for OUR specific ±1 weight type the accumulator width is
  exactly computable in closed form (`b_act + ceil(log2(fan_in))`) without A2Q's training
  method — a cheaper fix than porting the paper. WebFetch of the abstract page returned no
  table-level numbers; none quoted.
- 2026-09-26 — A2Q+: Improving Accumulator-Aware Weight Quantization, Colbert et al.,
  arXiv:2401.10432 — https://arxiv.org/abs/2401.10432 — successor to A2Q; same non-transfer
  caveat as above; not read past the title/abstract level.
- 2026-09-26 — CMS, "Reconstructing jets in the Phase-2 upgrade of the CMS Level-1 Trigger with
  a seeded cone algorithm," arXiv:2310.08062 — https://arxiv.org/html/2310.08062 — fetched and
  read looking for L1 PUPPI candidate per-feature bit widths; **not found** in this source
  (states link bandwidth and the 128-particle deregionizer truncation only); the search for this
  number should continue elsewhere (CMS Phase-2 L1T TDR CERN-LHCC-2020-004, or correlator
  firmware dataformat headers) before Q11 is scheduled.
- 2026-09-26 — WOMBAT: Design and FPGA Implementation of a DNN L1 Trigger System for Jet
  Substructure ID and Boosted H→bb Tagging, arXiv:2505.05532 — https://arxiv.org/pdf/2505.05532
  — fetched directly to check a search-snippet claim of "16-bit FPGA deployment precision";
  **that claim is NOT present in this paper's abstract/text as retrieved.** Logged as a
  correction: do not cite WOMBAT for an input/deployment bit-width; the snippet's true source is
  still unidentified.
- 2026-09-26 — Wortsman, Lee, Gilmer, Kornblith, "Replacing softmax with ReLU in Vision
  Transformers," arXiv:2309.08586 — https://arxiv.org/abs/2309.08586 — ReLU-attention (divided
  by sequence length) approaches softmax-attention scaling on ImageNet-21k ViTs; candidate
  mechanism for Q10 (removes the one non-multiply-accumulate op in our attention block); not a
  jet-tagging, binary-weight, or FPGA source — mechanism transfer only, no number transferred.
- 2026-09-26 — Ramapuram et al., "Theory, Analysis, and Best Practices for Sigmoid
  Self-Attention," arXiv:2409.04431 — https://arxiv.org/abs/2409.04431 — sigmoid replacing
  softmax normalization; same Q10 candidacy and same non-transfer caveat as above.
- 2026-09-26 — Stevens, Venkatesan, Dai, Khailany, Raghunathan, "Softermax: Hardware/Software
  Co-Design of an Efficient Softmax for Transformers," DAC 2021, arXiv:2103.09301 —
  https://arxiv.org/abs/2103.09301 — base-2 exponent + low-precision softmax + online
  normalization; closest hardware-motivated precedent for Q08/Q10; reported efficiency numbers
  are search-summary level only, not verified against the paper's tables in this pass.
- 2026-09-26 — `hgq.layers.softmax.QSoftmax._compute_ebops`, local HGQ2 install
  (`~/hgq2/HGQ2/src/hgq/layers/softmax.py:134-155`) and `hgq.quantizer.internal.
  fixed_point_quantizer`'s `fbits = relu(i+f)` (`fixed_point_quantizer.py:437`) — primary-source
  code reads (not a paper) that corrected Q08 (softmax IS priced in EBOPs) and Q12 (0-bit
  collapse is already reachable under the anchor's own bounds) from an earlier, wrong reading of
  our own wrapper's docstring; logged since both corrections change what two cards claim.
- 2026-09-26 — Chang jsc150 reference code, `reference-code/HGQ2-examples/jsc150/model.py`
  (`get_model`, lines 277-296) — re-read for width-initialization values; corrected to
  activation-side `i0=0 (default), f0=7, WRAP` (likely 8 total bits, matching our default, not
  "7-bit vs. 8-bit") to ground Q03; `docs/chang-vs-bnjettag.md:146`'s "b0=7/f0=7" cell conflates
  the separate weight-side (`kbi b0=7`) and activation-side (`kif f0=7`) parameters — re-verified
  against the source file directly rather than quoted from the doc alone.
- 2026-09-26 — `bnjettag/code/hgq2/bnhgq2/train.py:106-163` and `ablation.py:19,253` — primary-
  source code read distinguishing `BetaPID` (closed-loop, fixed target) from `beta_schedule`/
  `BetaScheduler`/`ParetoFront` (open-loop piecewise β, also fixed target/threshold); corrected
  Q04 (both are real, distinct, already-implemented mechanisms) and Q05 (a genuinely MOVING
  target_ebops does not exist in this codebase yet — it is new code, not the 2026-09-15 arm).
