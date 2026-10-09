# Design memo — the FP32 silicon baseline (Round 14, N = 8)

**Date:** 2026-09-02 · **Status:** pre-registration — design only, nothing launched ·
**Scope:** `r14-l1x3-n8-fp32`, seed 3, N = 8 only. Explicitly *not* the n16 whole-model gap and
*not* the activation-ladder (W1A6/W1A4) Vivado gap.
**Roles:** this memo is the design; implementation belongs to `ml-engineer`, synthesis to
`.claude/skills/hls-mulder/SKILL.md` on `mulder`. **This experiment uses zero GPU hours** — no
NRP job, no training: the checkpoint already exists.
**Companion records:** realization decision → `.claude/memory/decisions.md` (2026-09-02);
pre-registration → `.claude/memory/experiment-log.md` (2026-09-02). `RESEARCH.md` is not touched
by this memo; §6.5 changes only after the run lands and passes the numbers gate.

---

## 0. The fork, resolved first, because everything else depends on it

`RESEARCH.md` §6.5 ends *"FP32 remains unsynthesized."* Closing that honestly requires knowing
what "FP32 silicon" can mean in this flow. Two candidate readings were on the table:

**(a) literal float** — `float` datatypes through Vitis HLS, floating-point cores in the netlist;
**(b) a wide `ap_fixed` stand-in** — the unquantized-trained network realized on a fixed-point
datapath wide enough to be functionally the float network.

### 0.1 What the flow actually supports for *this* graph — measured today, not assumed

Two scratchpad probes were run locally against the repo's own venv (`.venv-hgq2`,
hls4ml 1.3.0), on the real `r14-l1x3-n8-fp32` architecture built by
`bnhgq2.qat.build_qat_model` with untrained weights (the frontend does not care about weight
values; these probes test parseability, not any physics number):

**Probe 1 — can the FP32 graph enter hls4ml at all?** `build_qat_model(fp32 cfg, seed=3,
with_pos_enc=False)` → 18,275 params, 30 layers, classes
`{QDense, QEinsum, QEinsumDense, QGlobalAveragePooling1D, QSoftmax, ReLU, Add, InputLayer}`.
Conversion attempted three ways — `Precision fixed<24,12>` with `bit_exact=True`, the same with
`bit_exact=False`, and `Precision "float"` with `bit_exact=False`. **All three fail identically
and at the same place:**

```
hls4ml/converters/keras_v3_to_hls.py:144 in __call__  (keras_v3_dispatcher)
AttributeError: 'DummyQuantizer' object has no attribute 'kif'
```

The failure is in `hls4ml/converters/keras_v3/hgq2/_base.py::extract_fixed_quantizer_config`,
which reads `q.quantizer.kif` off every input/output quantizer. In the FP32 build
(`qat.py`, `fp32 = wmode == "none"`) every quantizer is `QuantizerConfig("dummy", …)` →
`hgq.quantizer.internal.base.DummyQuantizer`, which is an identity with `bits = 0` and **no
`kif` property at all**. The dispatcher raises *before* the requested precision or the
`bit_exact` flag is ever consulted.

**The consequence is the memo's central fact: the FP32 checkpoint has no hardware datapath in
this flow.** The fork is therefore *not* "which precision string do we pass". Neither reading
(a) nor (b) is reachable without first materialising a real datapath — either by replacing the
dummy quantizers with genuine fixed-point grids, or by rebuilding the graph in stock (non-`Q`)
Keras layers and letting hls4ml assign a Model-default precision. There is no "just synthesize
the FP32 model" option, and any run spec that claims one is wrong.

**Probe 2 — does the wide-fixed realization actually parse, and does anything blow up?** The
same graph built with real static grids (`quant.weight = int8_absmax`, `quant.act_bits` swept
8 / 12 / 16) converts cleanly at all three widths (38 hls4ml layers each, `bit_exact=True`,
VU13P, 2.5 ns), and — the specific blowup I was worried about — **the attention softmax tables
do not scale with the activation width**: `table_size = 1024`, `inv_table_size = 4096` at 8, 12
and 16 bits alike. So widening the datapath is a frontend-feasible operation on this graph and
does not detonate the softmax LUTs. (Caveat, and an implementation item below: probe 2 widened
*activations* only; the weight grid stayed at the existing 8-bit `_static_w8`. The
`intW_absmax` generalisation is untested and is PREFLIGHT-2.)

### 0.2 What the literature convention is

Entered through `docs/literature/INDEX.md`, one note opened: the starred
`hls4ml-fpga-triggers/fastml2026_sloot_bitnet_survive_synthesis.md` (Sloot, FastML 2026 — same
venue, same VU13P, the closest published apples-to-apples of exactly this comparison). Its
Table 1 carries an unquantized **"Dense MLP"** row synthesized through the same hls4ml → Vitis
C-synthesis flow at **3,651 DSP**, alongside the quantized rows; the note's code read-back
records fixed-point typedefs in every model family it inspects (for their BitNet models,
`ACCUM_PRECISIONS` climbing
`ap_fixed<28,10> → <32,14> → <34,16> → <40,22>`, `mult_t <17,7> → <31,15>`,
`ap_ufixed<28,14>` ReLUs). Nothing in that note — and nothing anywhere in this project's
measured record — is a literal-`float` synthesis. The convention in this literature is that the
unquantized baseline is *named by its model family* ("Dense MLP", "full precision") and
*realized in fixed point*; the paper does not claim float hardware, and neither should we.
This is also the deployment reality: no L1 trigger firmware runs float, so a float netlist would
measure the cost of Vitis floating-point cores rather than the cost of not quantizing our
network.

### 0.3 The decision, and what it means for the §6.5 sentence

**We ship (b): the wide `ap_fixed` realization.** Rationale, in order of weight:

1. **(a) is not reachable at the frontend** for this graph without a stock-Keras rebuild that
   the project does not have, and the surrounding ladder (binary, W8A8) is fixed-point — a
   float arm would change the *arithmetic class*, not the precision, and would not be
   comparable to the rung below it.
2. **(b) measures the quantity the ladder is about**: what the unquantized-trained network
   costs when you put it on hardware without quantizing it *for* hardware.
3. It is the published convention (§0.2).

**Honesty requirement — this is the part that must not be fudged.** Under reading (b) the
sentence *"FP32 remains unsynthesized"* stays **literally true**: no float netlist exists and
none will. What this run licenses is a *different, better-defined* statement, and §6.5 must be
rewritten rather than deleted. Proposed replacement wording (recorded here, **not applied**):

> The FP32 article is not synthesizable as float in this flow — the unquantized checkpoint
> carries no datapath (hls4ml's HGQ2 frontend rejects its dummy quantizers). What is measured
> instead is the FP32-trained network realized on an `ap_fixed<W*,I*>` datapath chosen as the
> narrowest grid that reproduces the float network to within [bar] (paired ΔAUC [x] at 4,096
> jets): [numbers], stage-labelled. Literal floating-point silicon remains unmeasured and is
> not planned.

Reading (a) therefore needs no caveat because it is not shipped; reading (b) needs the label
above **wherever the number is quoted**, exactly as the W8A8 article carries "GATE2 not
bit-exact (AUC-neutral)".

**The booby trap the run spec must disarm.** `bnhgq2/convert.py` hardcodes `bit_exact=True` and
sets `"Precision": "fixed<24,12>"` as a Model fallback. If a future implementation makes the
FP32 graph parse (e.g. by stripping the `Q` wrappers) without pinning the realization, hls4ml
will silently emit an **unlabelled `ap_fixed<24,12>` netlist that gets written down as "FP32"** —
precisely the dishonest closure. The realization grid must be explicit, materialised in the
exported Keras model, and read back out of the emitted `defines.h` before any number is
recorded (PREFLIGHT-4 / falsifier F6).

---

## 1. The question

**Does the unquantized (FP32-trained) N = 8 tagger, realized at the narrowest fixed-point width
that is functionally the float network, demand materially more FPGA silicon than the measured
W8A8 baseline — enough to change §6.5's "the vanilla model does not fit" statement — or has the
silicon cost already saturated at 8 bits?**

"Materially more" is defined before the run as: **≥ 1.25× the W8A8 csynth LUT
(6,419,238 → ≥ 8.0M) or ≥ 1.25× the Vivado DSP demand (5,550 → ≥ 6,940)**. Below that, the
answer is "no".

The question has a real "no" and the "no" is publishable: if the FP32 realization lands on top
of W8A8, the finding is that *8 bits already is the vanilla cost of this network*, the top rung
of the ladder collapses into the one below it, and the paper says so.

## 2. The null

**H0: precision above 8 bits buys the netlist nothing.** Under H0 we expect the FP32 article at
its shipped width to land within ±25% of fit-ladder row 9 on csynth LUT, within the same DSP
class at C-synthesis, and at a Vivado DSP demand not materially above 5,550 — i.e. the FP32 row
would be a duplicate of the W8A8 row and would add no information to §6.5.

Corollary null, which the fidelity ladder tests for free: **H0': the narrowest width that is
functionally the float network is W\* ≤ 8**, in which case there is no distinct FP32 article at
all and the correct action is to say so in §6.5 rather than to synthesize anything.

## 3. The arms

No training is involved: every arm inherits its weights from a stored checkpoint, so the
training knobs (`BN_VARIANT`/`quant.weight`, `BN_ACT_BITS`, `BN_N_PART`, `BN_TERNARY`,
`BN_SOFTMAX_FREE`, `d_model`, LR, seed) are fixed by the artifact and are **identical across
arms except where the "varies" column says otherwise**. `arch` and `train` blocks of
`r14-l1x3-n8-fp32.json` and `r14-l1x3-n8-w8a8.json` were diffed today and are **equal**; the
`quant` blocks differ only in `weight` (`none` vs `int8_absmax`) and `act_bits` (32 vs 8).

| Arm | New compute? | Checkpoint | Realization (the variable) | RF / Strategy | Part / clock | Seed | Stage | Purpose |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **R9** (reference, already measured) | none | `w8a8-s3` | QAT-trained 8-bit grids | 1 / Latency | VU13P 2.5 ns (csynth), xczu7ev OOC | s3 | csynth + OOC | fit-ladder row 9 — the comparator |
| **R1/R7** (reference, already measured) | none | `w1a8-s3`, `gamma-sm4i0-s3` | binary fx8 | 1 / Latency; 1(pf1) | same | s3 | csynth + OOC | the thesis rows |
| **L0–L4** (fidelity ladder) | **local only, free** | `fp32-s3` | PTQ static grids at **W ∈ {8, 12, 16, 20, 24}** ← *the only knob that moves* | 1 / Latency | VU13P 2.5 ns (convert only) | s3 | convert + C-sim, **no synthesis** | selects W\*; prices the realization |
| **A1** (the run) | mulder | `fp32-s3` | PTQ static grids at **W\*** | 1 / Latency | VU13P 2.5 ns; xczu7ev OOC | s3 | csynth (+ OOC, conditional) | the FP32 silicon row |
| **A2** (control) | mulder, optional | `fp32-s3` | PTQ static grids at **W = 8** | 1 / Latency | same | s3 | csynth | separates width from network+provenance |
| **A3** (fallback only) | mulder | `fp32-s3` | W\*, **folded pf1** | pf1 / dataflow | same | s3 | csynth (+ OOC) | used only if A1 RF=1 is infeasible — **different schedule, labelled** |

**Everything not in the "Realization" column is identical across L0–L4, A1 and A2**: the same
checkpoint (`fp32-s3`), the same architecture, the same `input_std.json`, the same PE-fold
export mechanism, the same 4,096-jet gate set and 128-jet C-sim set, RF = 1, Strategy Latency,
`io_parallel`, part `xcvu13p-flga2577-2-e`, 2.5 ns, hls4ml 1.3.0, `bit_exact=True`,
`fix_relu_saturation` ON, `widen_accum` OFF, `fix_relu_parse` OFF, Vitis HLS 2023.2 on mulder.

**The 2×2-minus-one that makes the comparison interpretable:**

```
R9 = (w8a8 network, QAT grids,  W=8 )
A2 = (fp32 network, PTQ grids,  W=8 )
A1 = (fp32 network, PTQ grids,  W=W*)

A1 − A2  =  the pure precision-width effect   (network and pipeline held fixed)
A2 − R9  =  the network + grid-provenance effect (width held fixed)
```

Without A2, any A1-vs-R9 difference is a mixture of three changes and the ladder's top rung
means nothing. A2 is the arm that tells them apart; the cheap version bounds it structurally
instead of measuring it (§7), and says so.

## 4. Confounds, named individually

**Held fixed, with the evidence:**

1. **Normalization — the confound that already bit this project.** `arch.norm = "none"` in both
   configs; the `arch` blocks are equal by diff (checked 2026-09-02). No SubLN boundary is
   crossed by the FP32-vs-W8A8 comparison. This must be re-verified in PREFLIGHT-1 by
   config diff, not by memory.
2. **Architecture:** `d_model 32`, 4 heads, 2 layers, `ffn_dim 64`, `pool gap`, `ffn_act relu`,
   `pos_enc learned`, `softmax_free false`, `n_part 8`, `n_feat 3` — equal by the same diff.
3. **Input contract:** the same three L1 features and the checkpoint's own `input_std.json`
   (round-8 contract), applied identically in every arm's gate data.
4. **`pos_enc` handling:** the same blocker and the same fix in every arm — rebuild without
   `AddPositional`, fold the trained (1,T,D) table into `input_proj`'s `bias_axes='td'` bias.
   The fold is an exact constant-add identity in float.
5. **Synthesis knobs:** RF = **1** — note the config's `hls.rf` is **256** and *must be
   overridden*, as it was for W8A8; Strategy Latency; `io_parallel`; part
   `xcvu13p-flga2577-2-e`; 2.5 ns.
6. **Realization flags matched to `convert_w8a8.py`:** `bit_exact=True`,
   `fix_relu_saturation` ON, `widen_accum` **OFF** (accumulator widening is the binary DSP-0
   trick; this baseline exists to measure real multipliers), `fix_relu_parse` OFF, biases raw.
7. **Toolchain and host:** hls4ml 1.3.0; Vitis HLS 2023.2 on mulder; Vivado 2023.2 OOC on
   xczu7ev with the 2.5 ns constraint `read_xdc`'d before `synth_design`, then `opt_design`.
8. **Gate data:** the same 4,096 `data/val` jets (GATE1, extended C-sim, EBOPs) and the same
   128 for GATE2.
9. **Seed:** s3 in every arm, matching the comparator.

**Cannot be held fixed — controlled or labelled:**

10. **Different trained weights.** The FP32 article is a different network from the W8A8 one
    (`hls_r14_fit.md` rule 6 already says this for row 9). Controlled by **A2**; label stays.
11. **Grid provenance: post-training calibration vs QAT.** R9's grids were *trained*; the FP32
    article's must be *calibrated after training* — there is no other way to give an
    unquantized checkpoint a datapath. This is a difference in kind, not degree. Controlled by
    **A2**; labelled wherever quoted.
12. **Vivado part xczu7ev ≠ VU13P**, out-of-context, pre-route — the standing §6 caveat, shared
    by every arm, so it does not bias the comparison.
13. **Schedule.** A1 is designed to be II = 1 like R9 (148 cycles). If the tool returns
    II ≠ 1, the comparison is *not* schedule-matched and must be labelled exactly as row 7 vs
    row 9 already are. A3 (folded) is by construction a different schedule.
14. **Weight-grid width.** If the `intW_absmax` generalisation lands late, a variant where
    activations widen but weights stay 8-bit is **not** the FP32 article and must not be
    shipped as one (falsifier F6).

## 5. Seeds and the selection rule, fixed in advance

**Seeds.** One seed, **s3**, matched to the W8A8 comparator. Justification for going below the
three-seed floor: this is a **deterministic resource measurement of a fixed article**, not a
statistical estimate — LUT/DSP counts carry no seed noise, and the whole silicon axis of the
record (binary s3, W8A8 s3) is single-seed and seed-*matched* rather than seed-averaged.
**No ±σ may ever be attached to these LUT/DSP numbers.** The accuracy axis of this arm is
already a three-seed number in `RESEARCH.md` §5 (FP32 N = 8: 0.8864 ± 0.0005) and is not
re-derived here.

**Checkpoint selection, fixed before the run:**
`bnjettag/roc-results/r14/n8/_ckpt_dl/fp32-s3/model_best.keras` — the *same artifact* behind the
§5 AUC row (best epoch by validation AUC inside the 101-epoch budget, as trained). No
retraining, no re-selection, no seed shopping. If the local copy is absent it is re-fetched from
the W&B `BNJetTagAug` artifact, and its hash recorded.

**Width selection, fixed before the run:** ship the **narrowest** W on the pre-registered ladder
{8, 12, 16, 20, 24} that meets **all three** bars below. If none does, extend one step at a time
to 28 then 32, recording every rung; if 32 fails, that is falsifier F4 and nothing is
synthesized.

**Calibration inputs, fixed before the run.** The grids that define each rung are produced by
the existing `calibrate_activations` MSE machinery at `act_bits = W`, and the data it sees is a
free parameter that must not be chosen after seeing a rung's fidelity. Pinned now:
**calibration set = the config's own `quant.calib_n = 8192` jets from `data/val`**, per the
`act_policy = static_per_tensor_mse_calibrated` contract that both configs already carry;
weight grids from the `intW_absmax` absmax rule on the ported kernels. **Every rung's grids are
frozen before any GATE2 score is computed**, and no re-calibration is permitted after a rung
fails — a failing rung is recorded and the ladder moves up. The 4,096-jet gate set that scores
the rungs is drawn from the same `data/val` store as the calibration jets; that overlap is
recorded as a caveat rather than corrected, because it is identical to the W8A8 comparator's
practice and changing it would break comparability.

**Gate bars, fixed before the run:**

- **GATE1 — structural port only** (export graph, dummy quantizers still intact, vs the trained
  FP32 model on 4,096 standardized jets). There is **no quantization on this path** — the export
  is the trained function up to the float reassociation of `(bias + pos)` — so the expectation is
  `corr_scores = 1.000000`, exactly as `convert_w8a8.py` measured for its own port. Mirroring
  that driver's reasoning verbatim: **anything below 0.9999 is a porting bug, not a pass, and
  aborts without writing artifacts.** The recorded policy threshold stays 0.997 for continuity
  with the record; the abort bar is 0.9999. Also required: `weight_port_max_abs_diff == 0.0`.
- **REALIZATION step** (separate and labelled): apply the width-W static grids to produce the
  hardware article. Its error is *not* charged to GATE1 — it is the thing being priced, and it
  shows up at GATE2.
- **GATE2 — C-sim vs the FLOAT export** (not vs the requantized intermediate), n = 128 for the
  headline plus the extended 4,096-jet characterization that `convert_w8a8.py` already
  implements. Bars: `corr_scores ≥ 0.999`, `argmax_agreement ≥ 0.999`, and
  **|paired Δ macro-OvR AUC| ≤ 0.0005** on the 4,096 gate jets. Report *both* residues: C-sim vs
  float export (the honest realization cost) and C-sim vs the requantized Keras model (which
  should be near-bit-exact under `bit_exact=True`; if it is not, the hls4ml port is broken and
  that is a separate defect from the realization).
  **Bit-exactness is not expected and is not required** — the binary path's bit-exactness is a
  property of ±1 arithmetic. The only comparable measurement on record is W8A8's residue
  (GATE2 corr 0.9998325, max|Δ| 0.173828125, paired ΔAUC **+0.000175** at 4,096), so the 0.0005
  bar is ≈3× the one measured precedent, and `RESEARCH.md` §5 records ROC-test noise ≈0.0004.
  **Open item for `uncertainty-analyst` before launch:** confirm that 0.0005 on a paired 4,096-jet
  comparison is the right resolvable bar, or replace it with their number. **Open item for
  `physics-researcher`:** confirm macro-OvR AUC (not ε_S @ 1% FPR, which
  `results/r14/working_points_r14.md` also carries) is the quantity this fidelity bar should be
  powered on. Neither sign-off was obtained in this session; both are prerequisites to launch.

## 6. Falsifiers

A design with no falsifier is a demonstration. These are pre-registered; each names the action.

- **F1 — the null holds.** A1 csynth LUT < 1.25× R9's 6,419,238 **and** A1's Vivado DSP demand
  < 1.25× R9's 5,550. → Report "the silicon cost saturates at 8 bits for this network"; the FP32
  rung merges into the W8A8 rung in §6.5; do **not** dress it up as a win.
- **F2 — the control moves.** A2 differs from R9 by more than ±10% csynth LUT. → The
  network + grid-provenance axis is *not* negligible, and **no** A1-vs-R9 sentence may be
  written without it. The comparison becomes explicitly between-network and is labelled as such.
- **F3 — no DSPs where DSPs were expected.** A1's `einsum_dense` family reports 0 DSP at csynth.
  → Vitis LUT-mapped even the wide multipliers; the DSP narrative must be restated at the
  netlist stage only (precedent: §6.4's csynth-0 → Vivado-4,096, and R9's own csynth 1,384 →
  demand 5,550). Report as found; do not force.
- **F4 — no faithful width exists.** No W up to 32 meets the GATE2 bars. → The wide-`ap_fixed`
  realization does **not** represent the FP32 function for this graph; reading (b) is wrong, the
  FP32 rung stays open, and §6.5's sentence stands unchanged.
- **F5 — W\* ≤ 8.** The narrowest faithful width is 8 bits or less. → There is no distinct FP32
  article; the honest §6.5 statement is that 8 bits *is* the vanilla realization of this network.
  **A1 does not get cancelled — it collapses into A2** (one csynth at W = 8, the ~2 h class):
  "the cost saturates at 8 bits" is a *resource* claim, and §6.4's standing lesson is that
  resource claims on this design class are measured, never inferred. The run gets smaller, not
  cancelled.
- **F6 — run integrity.** The emitted `defines.h` shows `model_default_t = fixed<24,12>` on
  weight/accumulator typedefs instead of the pinned realization grids, or the weight typedefs
  are still 8-bit while activations widened. → hls4ml fell back to `convert.py`'s default
  precision (§0.3) or the weight generalisation did not take; the run is measuring the fallback,
  not the design. **Abort, rebuild, do not record.**
- **F7 — the run tells us something other than what we asked.** A1 returns II ≠ 1, or its
  latency class differs from R9's 148 cycles by more than a schedule-explicable margin. → The
  arms are not schedule-matched; the resource comparison is between different schedules and is
  labelled like row 7 vs row 9, or the arm is re-run at a matched schedule.

## 7. Cost, and the cheap version

**GPU / NRP: zero jobs, zero GPU-hours.** No training. This is entirely a local + mulder
experiment.

| Item | Where | Predicted cost | Basis |
| --- | --- | --- | --- |
| L0–L4 fidelity ladder (5 conversions + C-sims + paired AUC) | **local laptop** | free; hours of wall-clock at most, no cluster | probe 2 converted three widths in one session today |
| A1 csynth, RF = 1 | mulder | **≥ 2 h 17 m, ≥ 43.8 GB peak** — and expected worse, since a wider datapath is a bigger design | W8A8 csynth measured 2 h 17 m / 43.829 GB (experiment log 2026-08-25) |
| A1 Vivado OOC 2.5 ns (**conditional**) | mulder | **≥ 7 h 30 m, ≥ 37 GB** | W8A8 OOC measured 7 h 30 m / 37,888 MB |
| A2 control csynth | mulder | ≈ 2 h, same class as R9 | same width, same graph size |
| A3 folded fallback | mulder | folded builds are the 127-GB memory class — treat as a separate authorization | prior folded-run experience recorded in the fit campaign |

**Target stage: csynth **and** Vivado OOC, with the OOC conditional.** Parity with the W8A8
record *requires* the OOC: R9's headline numbers (146.2% of the VU13P, DSP demand 5,550) are
Vivado post-`opt_design` numbers, and §6.4's standing rule is that every DSP claim is verified at
Vivado, never at csynth alone. A csynth-only FP32 row can only be compared to R9's *csynth*
cell and must be labelled "csynth attribution", exactly like the A6/A4 ladder and n16 rows.
Parity therefore costs the extra ≥ 7 h 30 m.

**Pre-registered OOC gate:** proceed to Vivado only if A1's csynth completes **and** its csynth
LUT ≤ 2× R9's, i.e. **≤ 12,838,476**. Above that, record csynth-only with the "csynth
attribution" label and do not start a run that the precedent says will not land.

**The cheapest version that still answers the question** (recommended first commitment):
**L0–L4 locally (free) + A1 csynth only.** That yields a stage-labelled FP32 csynth row and
answers the headline question against R9's csynth cell; it also resolves F5 and F4 before any
mulder time is spent. The full version adds A2's csynth (the confound control) and A1's OOC
(parity with R9's netlist numbers). If only one of those two can be afforded, **buy A2** — a
netlist number for an uninterpretable comparison is worth less than an interpretable one.

## 8. Feasibility, specified here rather than improvised on the box

Written into the spec because the precedent for improvising is bad: the n16 RF=1 Latency run
**died at 17.7 h with no report**.

**PREFLIGHT-0 (done, 2026-09-02):** the FP32 graph does not parse — recorded in §0.1. Any spec
that assumes it does is void.
**PREFLIGHT-1:** re-diff the `arch`/`train` blocks of the fp32 and w8a8 configs; assert
`arch.norm == "none"` in both. Abort on any difference.
**PREFLIGHT-2:** the `intW_absmax` weight-grid generalisation (probe 2 widened activations only).
Build at each ladder width and assert, from the emitted `defines.h`, that **weight typedefs
widened too**.
**PREFLIGHT-3:** checkpoint present and hash-recorded; `input_std.json` alongside it.
**PREFLIGHT-4 — predicted-size sanity check, before anything ships to mulder.** From the local
hls4ml project at W\*, record and compare against R9's stored project
(`runs/9cc6e336/w8a8-s3-r14n8/hls_prj_rf1`, **2.9 MB** unpacked, **400 KB** tarball): project
directory size, tarball size, weights-file count and total weight-element count, and the
emitted `defines.h` typedef census. **If the tarball exceeds 10× R9's (4 MB) or the weight
typedefs disagree with W\*, stop and diagnose — do not ship.** This is the check that catches
F6 before it costs a synthesis.
**PREFLIGHT-5 — fingerprint the untouched paths.** Any change to `qat.py`/`build.py` needed for
the weight-width generalisation must be proved inert on the binary and w8a8 default builds by
the 2026-08-19 sha256-over-variables pattern (pre-edit vs post-edit identical), as was done for
the `with_pos_enc` kwarg (5/5 PASS).

**On the box:**
- **Serialize.** One heavy job at a time (A6 rule 5). mulder is currently idle (load ≈1.1, no
  Vitis/Vivado processes, 118 GB RAM free) — verify again at launch, do not assume.
- **memwatch + RSS sampler** on every run, as for W8A8. **Memory kill wall: 90 GB RSS** (of the
  118 GB available), leaving headroom on a shared box.
- **Wall-clock abort threshold: 7 h 00 m for A1 csynth** (≈3× the W8A8 comparator's 2 h 17 m).
  At the wall, kill, harvest whatever per-module reports exist as diagnostics only, and report
  the abort. **Do not repeat the 17.7-hour n16 death.** For the conditional OOC: **12 h**
  (≈1.6× the W8A8 OOC's 7 h 30 m).
- **Disk, on a home mount at 97% with 1.5 TB free.** The Vitis solution directory — not the
  project — is the large object, and it is already in the ignored-artifacts manifest. Build
  under the usual scratch path; sample `du` alongside memwatch; **hard stop if the build
  directory passes 200 GB**; on completion tar the project, delete `.autopilot` intermediates,
  and fetch back only `myproject_csynth.rpt`, `csynth.xml`, `csynth_report.json`, the tcl,
  `defines.h`, memwatch and the stdout tail (the tracked set from the 2026-08-24 store policy).

**Named fallback if RF = 1 csynth is infeasible:** **A3 — folded pf1 at W\***. It is *not* a
substitute for A1 and must never be tabulated as one: folding changes the schedule (the
existing folded points run II = 47/48 against RF=1's II = 1), so an A3 number compares only to
the project's other folded points, and against R9 it carries the same "different schedule"
label that separates fit-ladder **row 7 from row 9** today. If A3 is used, the §6.5 sentence
gets a schedule qualifier as well as a realization qualifier.

## 9. Concrete run spec (for `ml-engineer`)

Not a launch authorization. Nothing here goes to mulder before PREFLIGHT-0…5 pass, the
`uncertainty-analyst` and `physics-researcher` sign-offs in §5 land, and Kai authorizes.

```
Driver          : new convert_fp32.py, modelled on convert_w8a8.py (do not modify
                  convert_final.py or convert_w8a8.py; binary path must fingerprint unchanged)
Config          : bnjettag/code/hgq2/configs/r14-l1x3-n8-fp32.json
Checkpoint      : roc-results/r14/n8/_ckpt_dl/fp32-s3/model_best.keras  (+ input_std.json)
Seed            : 3
Export          : build_qat_model(cfg, seed=3, with_pos_enc=False); port all variables by
                  name; fold (1,T,D) pos table into input_proj bias_axes='td'  -> GATE1
Realization     : build a SECOND graph with LIVE quantizers at width W and port into it.
                  PORT KERNELS AND BIASES BY NAME ONLY, then set quantizer state by
                  calibration — do NOT whole-layer set_weights as convert_w8a8 does: the
                  variable counts differ by construction (the 2026-08-19 fingerprint gate
                  recorded 87 vars for the fp32 build vs 213 for the w8a8-class builds), so
                  a whole-layer port SystemExits on the count mismatch.
                  acts: MSE-calibrated static per-tensor via calibrate_activations at
                  act_bits=W on calib_n=8192 data/val jets; weights: intW_absmax, the
                  _static_w8 rule generalised                              -> the labelled step
Ladder (local)  : W in {8, 12, 16, 20, 24} (extend 28, 32 only if needed)  -> GATE2 per rung
Ship            : W* = narrowest rung passing corr>=0.999, argmax>=0.999, |dAUC|<=0.0005
hls4ml          : bit_exact=True, io_parallel, Strategy=Latency, ReuseFactor=1  (OVERRIDE the
                  config's hls.rf=256), part xcvu13p-flga2577-2-e, clock 2.5 ns,
                  fix_relu_saturation ON, widen_accum OFF, fix_relu_parse OFF, biases raw
Store           : results/synthesis/runs/<cfg_hash>/fp32-s3-r14n8-w<W*>/
                  { export_verify.json, realization.json, csim_verify.json, ebops.json,
                    convert.json, hls_prj_rf1[.tar.gz], csynth_rf1/, postsyn_xczu7ev/ }
mulder          : csynth first (abort 7h / 90GB / 200GB disk); OOC 2.5 ns only if csynth
                  LUT <= 12,838,476; OOC abort 12h
Controls        : A2 = same pipeline at W=8 (csynth) — full version only
Fallback        : A3 = folded pf1 at W*, labelled different-schedule
EBOPs           : last, after both gates (trace_minmax must not run before them)
```

## 10. What this memo does not do

It does not launch anything, does not write code, and does not touch `RESEARCH.md`. It does not
address the n16 whole-model gap or the W1A6/W1A4 Vivado gap — both remain open and out of scope
here. It records one decision (`decisions.md`, 2026-09-02) and one pre-registration
(`experiment-log.md`, 2026-09-02) so that the selection rule, the gate bars and the falsifiers
are on record ahead of any number.

---

### Provenance of every figure quoted above

| Figure | Source |
| --- | --- |
| W8A8 csynth 6,419,238 LUT / 1,384 DSP / 148 cyc / II 1 | `results/r14/hls_r14_fit.md` row 9; `RESEARCH.md` §6.5 |
| W8A8 Vivado post-opt 2,525,842 CLB LUT (146.2%), DSP used 1,721 / demanded 5,550 | `hls_r14_fit.md` row 9; experiment log 2026-08-25 |
| W8A8 run cost 2 h 17 m / 43.829 GB (csynth); 7 h 30 m / 37,888 MB (OOC) | experiment log 2026-08-25 |
| W8A8 GATE1 1.000000; GATE2 corr 0.9998325, max abs diff 0.173828125, paired dAUC +0.000175 | experiment log 2026-08-24; `runs/9cc6e336/w8a8-s3-r14n8/` |
| binary fx8 RF=1 3,178,720 LUT (184.0%) / 4,133 DSP / 164 cyc | `RESEARCH.md` §6.2; `hls_r14_fit.md` row 1 |
| fit-ladder row 7 (shipped operating point) 3,837,485 csynth / 0 DSP / II 48 / post-opt 1,689,320 (97.8%) | `hls_r14_fit.md` row 7 |
| FP32 / W8A8 / W1A8 ROC-test AUC at N=8: 0.8864 ± 0.0005 / 0.8862 ± 0.0009 / 0.8712 ± 0.0016 | `RESEARCH.md` §5 |
| ROC-test noise ~0.0004 | `RESEARCH.md` §5 |
| n16 RF=1 Latency died at 17.7 h without a report | `RESEARCH.md` §6.5 |
| W8A8 project 2.9 MB unpacked / 400 KB tarball | `du` on `runs/9cc6e336/w8a8-s3-r14n8/`, 2026-09-02 |
| Sloot FastML 2026: unquantized "Dense MLP" row at 3,651 DSP; ap_fixed accumulator ladder | `docs/literature/hls4ml-fpga-triggers/fastml2026_sloot_bitnet_survive_synthesis.md` |
| `DummyQuantizer` has no `kif`; all three conversion attempts fail at the dispatcher | local probe, 2026-09-02 (§0.1) |
| wide grids convert at 8/12/16 act bits; softmax `table_size` 1024 / `inv_table_size` 4096 at every width | local probe, 2026-09-02 (§0.1) |
| mulder idle, load ~1.1, 118 GB RAM free, home mount 97% used / 1.5 TB free | task briefing, 2026-09-02 |

---

## AMENDMENT A1 — 2026-09-02, written BEFORE any synthesis was launched

This amendment is dated and appended rather than folded into §5 silently, per the repo rule that
frozen documents are corrected with dated notes. **It exists before the measurement it selects.**
Nothing had been synthesized when it was written; mulder was idle.

The pre-registered §5 selection rule is superseded in **five** ways, each traceable to a sign-off:

1. **Gate n: 4,096 → 32,768** (uncertainty sign-off). At n = 4,096 the paired 95% half-width is
   2.5e-4–4.4e-4, up to 0.9× the 0.0005 bar itself; a test at the bar was near a coin flip. The
   32,768 set nests the 4,096 set, and Δ is reported at both n. The §5 justification that "0.0005
   is ≈3× the measured precedent" is **struck**: that precedent (W8A8 GATE2, +0.000175 at n = 4,096)
   is itself 1.4σ, i.e. consistent with zero. Its "AUC-neutral" conclusion stands (95% upper bound
   ≈4e-4); its use as a *scale* does not.
2. **Statistic form: point estimate → paired-bootstrap upper bound** (uncertainty sign-off). A rung
   must PROVE fidelity, not merely fail to disprove it. Under first-pass selection a point-estimate
   rule is biased toward too-narrow W*.
3. **Per-class bars ADDED** (physics sign-off, calibrations ratified by uncertainty):
   per-class |ΔOvR-AUC| ≤ 0.0015 (0.9–1.7× the measured per-class seed sd — one training fluctuation)
   and per-class |Δε_S @ 1% FPR| ≤ 0.010 absolute (ratified as a deployment CEILING, and recorded as
   loose: calibrated like the AUC bar it would be ≈0.007). Macro AUC alone is bulk-weighted and blind
   to shoulder clipping — the realization step here is an MSE-calibrated static-grid step, so this is
   the live failure mode, not a hypothetical.
4. **`argmax_agreement` bar: 0.999 → 0.98** (physics sign-off). As pre-registered the bar REJECTED the
   W8A8 realization already accepted on the record (measured 0.98779). It is bulk-dominated and is
   explicitly NOT a working-point guard.
5. **Multiplicity rule ADDED** (uncertainty sign-off). Within a rung the 11 bars are an
   intersection-union test — size ≤ α, no correction. ACROSS rungs, "ship the first that passes" is
   repeated opportunity to falsely declare equivalence, so:
   **R1** — evaluate every bound at 1 − 0.05/K, K = rungs evaluated (K = 5 ⇒ **99%** bounds);
   **R2** — monotone confirmation: W* passes AND the next rung up passes.

### The `no_tie_plateau_straddling_1pct` check is VOID and must not fail any rung

Pre-registered in §5 and implemented in the ladder, it is **arithmetically unsatisfiable by any model
at this split** and condemns the unquantized float reference itself (all five classes, every width).
`0.01 × n_bkg` is not an integer for any class (g 260.21, q 264.69, W 261.38, Z 262.43, t 262.01), so
no threshold realizes FPR = 0.01 exactly; the flagged `fpr_jump` is exactly ONE background jet, with
`unique_fraction = 1.0` and `tie_fraction_signal = 0` in all 50 rows — there are no ties anywhere in
the ladder. The rows that read `straddles = false` are the buggy ones (non-bracketing threshold pick),
not the good ones.

**Replacement statistic**, applied hereafter: `J(c) = n_bkg(c) × fpr_jump` = background jets tied at
the working-point threshold. Structural flag J ≥ 2 anywhere in FPR ∈ [0.5%, 2%] (an integer test, no
sampling error, valid at any n); deployment flag when the achievable FPR step exceeds r·f_target
(r ≈ 5–10%). "Some threshold realizes f exactly" is unachievable at any finite n and must never be a bar.
**Applied to the ladder: J = 1 for every class, arm and rung — no plateau exists; the check is inert here.**

### Selection of record: W* = 16

| rung | eff@1% up99 | per-class AUC up99 | verdict |
|---|---|---|---|
| W=12 | **0.011536 (W)** | 0.000357 | **FAILS R1** |
| W=16 | 0.003386 (Z) | 0.000217 | **PASSES, ≥3.0× margin** |
| W=20 | 0.002657 (Z) | 0.000182 | passes (satisfies R2) |
| W=24 | 0.002634 (Z) | 0.000182 | passes |

W=12 passes the bars exactly as written at 95%, but its worst bar sits at 91% of the limit and it fails
under R1; its status flips on the third decimal (bar 0.010 → 0.009, or level 95% → 99%). W=16 passes
every bar with ≥3.0× margin and R2 holds. The eff bar would have to tighten 3.0×, or the AUC bar 6.9×,
to move W* off 16.

**Null results, recorded as plainly as the positive one.** W=16, W=20 and W=24 are **not
distinguishable** at n = 32,768 (eff bounds 0.00261/0.00207/0.00205; corr agreeing to six digits) —
W=16 is simply the cheapest rung on a converged plateau, which is *why* the choice is robust. And the
W=16 realization penalty (eff bound 0.0026) is **smaller than the seed-to-seed training spread in the
same quantity** (sd 0.0022–0.0070): the realization step costs less than changing the random seed.

**Do not report** the W=12 g-class efficiency being numerically identical to the reference as evidence
that g is unusually safe. It is a discrete-estimator coincidence — the same two background jets bracket
the working point, it coexists with a bootstrap sd of 0.00178, class Z is likewise exactly identical at
W=16, and the g delta is non-monotone in width (all deltas are 1–3 signal jets).

### Conservatism, stated in advance

The narrowest-passing-rung rule is conservative **against** the thesis: a narrower W* yields a
*cheaper* FP32 baseline and therefore a *smaller* claimed binary advantage. Selecting W = 16 rather
than 24 cannot inflate the comparison in our favour.

### Standing caveats

- The entire ladder is **seed 3**. Realization deltas are deterministic given weights, so no seed
  interval attaches to them, but W* is demonstrated for one trained model. A csim confirm at W = 16
  on s1 and s2 (~1 min each at n = 32,768) is recommended before W* is treated as general.
- Realization score arrays were not persisted — only summary JSON. The ratification validated the
  bootstrap machinery and its 1/√n scaling on real stored arms rather than recomputing the
  realization bootstrap itself.
- The per-class eff bar 0.010 is a **ceiling, not a tight equivalence bar**. A 2.4%-relative bar on
  g (0.0024 abs) is enforceable at n = 32,768 (margin 1.7×); ~0.6–0.7% relative would need the
  260,000-jet store (~7 min/rung, local csim).

### A1 addendum — 2026-09-02, later the same day (seed caveat CLOSED; two provenance corrections)

**The seed caveat above is closed.** W* = 16 was re-run at n = 32,768 on FP32 seeds 1 and 2 (local
convert + C-sim; the checkpoints were already at `roc-results/r14/n8/_ckpt_dl/fp32-s{1,2}/`).
Both PASS every ratified bar, at the 99% level per R1:

| seed | corr | argmax | macro ΔAUC up99 | worst per-class ΔAUC up99 | worst per-class Δε@1% up99 | J |
|---|---|---|---|---|---|---|
| s1 | 0.999995 | 0.99933 | 0.000014 (35×) | g 0.000046 (33×) | W 0.003737 (2.7×) | 1 |
| s2 | 0.999998 | 0.99942 | 0.000015 (33×) | W 0.000030 (50×) | W 0.003422 (2.9×) | 1 |
| s3 | 0.999995 | 0.99911 | 0.000058 (9×) | q 0.000250 (6×) | Z 0.003489 (2.9×) | 1 |

GATE1 exact on both new seeds (corr 1.000000000000, `weight_port_max_abs_diff` 0.0). Containment
re-verified from the firmware, not from a driver flag: all 17,664 weight elements per seed exactly
representable at 16 fractional bits, 0 overflow. The binding bar on every seed is the per-class
ε_S @ 1% FPR one, with a seed-stable margin of 2.7–2.9×; the *worst class* is not seed-stable
(W, W, Z), consistent with these deltas being 1–3 signal jets rather than a structural class weakness.
R2 was not re-checked per seed — it stands on s3. **W* = 16 is not seed-3-specific.**

**Two corrections to the A1 table above, both immaterial at 6–50× margins, neither changing any verdict:**
1. A1's "up99" column is not a direct percentile — it is the stored 95% bound Gaussian-rescaled about
   the bootstrap mean by z(.995)/z(.975) = 1.3142. That route reproduces the direct percentile to
   within 0.2–0.9% (W16 eff Z: 0.003386 rescaled vs 0.003489 direct; W12 eff W: 0.011536 vs 0.011547).
   The direct percentile is slightly LARGER, i.e. A1 was mildly anti-conservative; W=12 still fails
   and W=16 still passes under either route.
2. A1's per-class-AUC up99 column mixes levels: the W=20 / W=24 entry 0.000182 is the 95% value
   (its rescaled 99% is 0.000218).

---

## CORRECTION C1 — 2026-09-03, after the first two C-syntheses and the failed OOC

Dated correction, not a silent rewrite. Two things in this memo are now known to be wrong, and one
measured outcome must never be quoted the way the memo set it up.

### C1.1 §0.1 probe 2 reached the WRONG CONCLUSION about softmax tables

§0.1 recorded that widening "does not detonate the softmax LUTs", on the evidence that `table_size`
(1024) and `inv_table_size` (4096) are width-invariant. **Those measurements are correct; the
conclusion drawn from them is not.** The probe read the two table fields that do not scale and never
read `exp_table_size`, which does: it is sized 2^width(`softmax_inp_norm_t`), and that type is
`ap_fixed<10,7>` at W = 8 but `ap_fixed<16,7>` at W = 16, so `exp_table_size` goes **1,024 → 65,536**.
A field-selection miss, not a sweep-coverage miss.

**Consequence, measured:** all 12,544 BRAM_18K of the W16 build sit in the 64 softmax instances
(196 each, vs 8 each at W8); einsum_dense uses zero BRAM. This is the direct cause of the Vivado OOC
failure — `[Synth 8-5834] Design needs 24768 RAMB18 which is more than device capacity of 624`,
after 3 h 44 m (wall time from the mulder chain log; not re-derivable from the local store, whose
`memwatch.log` belongs to the separate C-synthesis job). It is a realization artifact of hls4ml's exact softmax table under a
widened `softmax_inp_norm_t`, **not** a property of the FP32 network's arithmetic. It is fixable
(bound the inp_norm width, or override the table), but any fix changes the bit-exact contract and is
therefore a re-run decision, not a patch.

### C1.2 The W = 16 rung is infeasible at RF = 1, on DSP alone

Measured: **140,130 DSP = 1,140% of the VU13P** (4,561% per SLR), against 202% for the W = 8 control
and 11% for the W8A8 article. The OOC was gated on LUT (≤ 12,838,476, which passed at 7,215,326);
**no DSP or BRAM gate was pre-registered, and both are binding.** Any future gate on this design class
must include all three.

### C1.3 The A2 control's 18× DSP gap is HONEST — but is NOT an equal-precision contrast

The W = 8 control needs 24,824 DSP where the W8A8 article needs 1,384 (17.9× whole-model, **27.9× on
`einsum_dense` alone**; every other family is flat, and act×act einsum LUT agrees to 0.04%). The
pipeline is **not** defective: W* is applied exactly, flags/part/clock/RF match, and the effect is
entirely in constant-weight multiplies. Two gates explain it:
- **Container width.** All eight attention weight arrays take the hls4ml frontend fallback
  `model_default_t` (24-bit at W8, 28-bit at W16) — present *identically in both arms*. Layers with a
  container ≤ 9 bits draw 0 DSP regardless of value density; only the 24-bit attention layers are
  DSP-eligible at W = 8.
- **Value strength-reducibility.** With the container held at 24 bits, the fraction of weights whose
  odd mantissa has ≥ 4 set bits predicts measured DSP/multiply to 0.98–1.17×. Distributions over all
  17,664 weights: W8A8 (QAT) 35 distinct values, 83.1% with ≤ 2 set bits; fp32-W8 (PTQ) 227 distinct,
  34.3%; fp32-W16 (PTQ) 14,321 distinct, 0.5%.
- **Controlled pair for the record:** `config5` (block-0 attn Wq) — same shape, same input type
  `ap_fixed<8,3>`, same 24-bit container, same RF/part/clock — **144 DSP (W8A8) vs 3,072 DSP (fp32-W8).
  Only the weight values differ.**

**The label this forces.** W8A8's *realized* attention weight grid is **5 fractional bits,
`ap_fixed<5,0>` on all eight attention arrays** (firmware-verified 2026-09-03; an earlier draft of
this correction said "6-bit / 5 fractional" — the fractional width 5 is confirmed and is the
load-bearing quantity since it fixes the lattice, but the realized TOTAL width is 5, not 6: absmax
0.4375 fits `ap_fixed<5,0>`. The "6-bit" figure is the named `ap_fixed<6,1>` typedef hls4ml emits for
the DENSE layers, a different set of arrays. No measured number changes.) —
HGQ2's converged width under a nominal 8-bit budget, which hls4ml's bit-exact frontend narrows to
because that is all the trained grid uses. The A2 control's is **modal, not uniform** — `ap_fixed<9,1>` on 5 of 7 named layers, with
`input_proj` at `ap_fixed<8,0>` (8 frac) and `head_fc2` at `ap_fixed<8,1>` (7 frac); W8A8's
`ap_fixed<6,1>` IS uniform across all 7 (numbers-gate correction, 2026-09-03). Note further that on
the eight attention arrays where the entire DSP gap lives, BOTH arms take the same 24-bit
`model_default_t` container, so the operative difference there is realized grid density (5 vs 8
fractional bits of value), not the container. Nothing about the
W8A8 article's own measured numbers changes, and it is not mislabelled — but the 18× **conflates grid
provenance (QAT vs PTQ) with ~3 bits of realized weight width**, and that split **cannot be decomposed
from anything on disk**. Confound #14 is live, in a direction this memo did not anticipate.
Until a weight-width-matched PTQ arm exists, the A2−W8A8 contrast must never be quoted as an
equal-precision comparison.


### C1.4 — 2026-09-03: the width-matched control exists and is in synthesis

`fp32-s3-r14n8-wm-w5a8` realizes the FP32-trained network at **W = 5 weights / A = 8 activations**
(not W = 6 — `intW_absmax` gives f = W here, so W = 6 would have been one bit too fine). Activations
were deliberately held at 8 bits because both comparators feed the einsums with 8-bit operands;
coarsening them would have reintroduced the very confound this arm removes.

Grid match against the W8A8 article, from emitted firmware on the eight attention arrays:

| 8,192 elements | W8A8 QAT (target) | fp32 W5A8 (matched) | fp32 W8 (unmatched A2) |
|---|---|---|---|
| frac bits / realized type | 5 / `ap_fixed<5,0>` ×8 | **5 / `ap_fixed<5,0>` ×8** | 8 / `ap_fixed<8,0>` ×8 |
| distinct values (pooled) | 28 | **27** | 199 |
| ≤2 set bits | 86.87% | **87.44%** | 33.39% |
| ≥4 set bits | 0.00% | **0.00%** | 33.78% |

Container (`model_default_t` = `ap_fixed<24,12>`) and all six activation `*_iq_t` types are identical
across the three arms, and `softmax_inp_norm_t` stays `ap_fixed<10,7>` so the C1.1 BRAM blowup is not
triggered. EBOPs 5,995,950 vs 9,188,526 for BOTH W8A8 and fp32-W8 — the two comparators being equal
is independent confirmation that only weight width moved.

**This arm is a RESOURCE-COMPARISON CONTROL, not an operating point, and fails every fidelity bar**
(corr 0.864, argmax 0.757, |Δmacro AUC| up99 0.0375 = 75× the limit, worst per-class Δε@1% 0.186 = 19×).
That is expected: the loss is the 5-bit lattice, not a port defect (quant-only ΔAUC −0.035494 of the
total −0.035364). It must never enter an accuracy table. W* = 16 remains the FP32 realization of record.

**Reading the result when csynth lands:** `W5A8 − W8A8` = pure grid provenance (QAT vs PTQ) at equal
realized width, equal container, equal activation operands. `W8 − W5A8` = the ~3-bit width effect this
correction called inseparable. Per C1.2, gate on LUT **and** DSP **and** BRAM.
