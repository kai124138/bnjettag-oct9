# BNJetTag — The Research (living document)

> **ARCHIVED, 2026-09-26.** Everything in this document predates the EBOP target (enforced
> from 2026-09-10: N = 8 at 350k, N = 64 at 5M; lower EBOPs is better). Round 14 trained
> without a cost constraint, so its numbers are not the current state of the project and are
> not compared against the constrained runs. Current work: `publication/README.md`
> (post-conference section), `publication/results/post_conference/`,
> `publication/docs/current-work/`, and `campaigns/` from 2026-09-10 on. The sections are kept
> intact because §7 maps every number to its source, and §6 is still the only verified
> hardware measurement.

**The single source of truth for what this project claims, what it has measured, and what
is still open.** Updated only from verified numbers (recomputed from `.npz` / csynth
reports / logs — sources in [§7](#7-where-every-number-comes-from)). Layout and workflow:
[README.md](README.md).

*Scope, set 2026-08-13: this document covers Round 14 — the L1-realistic `(N, 3)` input
campaign — and nothing before it. Every earlier round, together with its results, reports,
figures, and job specifications, was moved intact to `_attic/` and is no longer part of the
active record. The full pre-reorganization document is preserved at
`_attic/superseded-root-docs/RESEARCH-2026-08-13-full.md`; no number changed.*

**Reading rule, always in force.** *Validation AUC ≠ ROC-test AUC.* Val AUC is the
training-time monitor; ROC-test AUC is measured on the held-out set. Every number below is
labeled.

---

## 1. Thesis and abstract

**Thesis.** A transformer jet tagger whose attention and feed-forward weights are constrained
to binary `{−1,+1}` (BitNet-style, 1-bit) can run in the CMS Level-1 trigger's FPGAs using
essentially **no DSP multipliers** — the binary multiply–accumulate reduces to sign-flips and
LUT adder trees — at a modest, measurable cost in tagging efficiency. Two axes are measured:
**(a)** tagging efficiency vs full-precision and conventional 8-bit baselines, and **(b)** how
aggressively activations can be quantized (A8 → A6 → A4) before efficiency, resources, or
latency degrade.

**Abstract (as submitted).**
> The LHC collides protons at a rate of 40 million collisions per second. To filter the
> massive amount of data for interesting physics, the real-time trigger systems inside
> detectors at the LHC necessitate smart and sophisticated triggers that are 1) efficient
> enough to simultaneously reject large backgrounds and keep enough signal, 2) compact enough
> to meet hardware constraints, and 3) fast enough to meet the latency requirements. We
> present a particle jet tagger based on a binary-weight, BitNet-style 1-bit transformer, in
> which the attention and feed-forward weights are constrained to {−1, +1}. Because binary
> weights reduce multiply–accumulate operations, the model's matrix multiplications can be
> mapped onto the FPGA's lookup-table and logic fabric rather than its scarce DSP resources,
> targeting a maximally compact and low-latency trigger. The model is trained and validated
> on data simulating the conditions of the LHC and converted into high-level synthesis using
> the hls4ml hardware-software codesign tool. This work evaluates the tagging efficiency of a
> 1-bit transformer model — comparing it against the vanilla version, and explores how
> aggressively it can be quantized before its tagging efficiency, resource consumption, and
> latency degrades.

---

## 2. Where things stand

*Archived (pre-EBOP-target, Round 14); see the note at the top.*

Round 14 is complete on the accuracy axis. On silicon the zero-DSP mechanism is established
and verified at Vivado synthesis, the device-fit question is measured to its floor for the
trained grids, and the first fitting zero-DSP point exists as a structure-only build whose
trained counterpart is in training (2026-08-23).

- **Accuracy, all 60 runs verified.** Binary (W1A8) costs a resolved macro-AUC deficit against
  FP32 at every constituent count (+0.015 at N = 8 to +0.036 at N = 64). With three seeds the
  step-to-step growth of that deficit and any W8A8 deficit are *not* individually resolved and
  are not claimed ([§5](#5-tagging-efficiency--round-14-l1-realistic-n-3-inputs)). Binary reaches
  0.896 macro-OvR AUC at N = 16 and 0.905–0.912 at N = 32–64, at 5.3× (N = 8) to 2.1× (N = 64)
  fewer checkpoint EBOPs than W8A8 at matched N.
- **Silicon, n8: the DSP claim is complete and verified at Vivado synthesis.** With the β
  affines and softmax bound to fabric, the whole model synthesizes at **0 DSP at C-synthesis and
  at Vivado synthesis** — at RF=1 (II=1, 146 cycles) and folded (II=47, 329 cycles). No
  multiply Vivado infers on the netlist originates in a binary matmul. At the trained grids the
  binding must stay solution-wide: scoping it to the DSP-carrying modules hands the 4,096
  attention-context products back to DSPs at the netlist ([§6.4](#64-what-the-measurements-teach)).
- **Device fit, measured at Vivado post-`opt_design` (part xczu7ev, pre-route).** The two
  trained-grid zero-DSP points miss the VU13P LUT budget: 2,108,743 CLB LUT (122.0%) at II=1 and
  1,948,063 (112.7%) folded; every conversion-level lever was measured and closed. Narrowing
  the attention-softmax operand from 10 to 4 bits on the scoped-binding build gives the **first
  measured zero-DSP point under budget — 1,694,625 CLB LUT, 98.1% of the VU13P** — as a
  structure-only characterization — and its TRAINED counterpart now exists and confirms it:
  the retrained 4-bit-grid network holds the accuracy (0.8701 ± 0.0020, −0.0011 vs the control)
  and synthesizes to **1,689,320 CLB LUT = 97.8% at 0 DSP**, meeting a 200 MHz clock pre-route
  (WNS +0.65 at 5 ns; 240 ns/jet, 1.67 µs) — the first fitting zero-DSP operating point
  ([§6.3](#63-device-fit-measured-at-vivado-synthesis)).
- **Open.** Clock: the zero-DSP points fail the 2.5 ns constraint pre-route, but the fitting
  design meets a 5 ns constraint (WNS +0.56 ns, 0 DSP, 91.6% of the VU13P; 240 ns/jet, 1.67 µs
  latency) — a pre-route, out-of-context statement; the W8A8 baseline is now measured at C-synthesis (6.42M LUT + 1,384 DSP vs binary's 3.18M + 4,133;
  its weight layers 872 DSP vs binary's 0; §6.5) and at the Vivado netlist (post-opt 2,525,842 CLB LUT = 146.2% of the VU13P, DSP demand 5,550 vs 0 for every binary zero-DSP build; §6.5); the FP32 arm now has a staged silicon number too — the FP32-*trained* network on an `ap_fixed<16,·>` datapath (W* selected on ratified fidelity bars, confirmed on 3 seeds) C-synthesizes to 7,215,326 LUT + **140,130 DSP = 1,140% of the VU13P**, i.e. infeasible at RF=1, and its Vivado OOC failed on BRAM capacity (`[Synth 8-5834]`, 24,768 RAMB18 vs the xczu7ev's 624) from an hls4ml exact-softmax-table artifact, not from the network's arithmetic; literal float silicon does not exist in this flow and is not planned (§6.5); the exported graphs' AUCs are now measured
  (all five synthesized articles AUC-equivalent to their trained networks, Δ ≤ 0.00033;
  `results/r14/export_roc_auc.md`); n16 and above are not
  synthesized whole-model (the RF=1 run died at 17.7 h; its DSP attribution is C-synthesis only).

---

## 3. The model

BitNet-style transformer classifier, trained natively in the HGQ2 QAT stack
(`bnjettag/code/hgq2/bnhgq2/`); configuration of record
`bnjettag/code/hgq2/configs/r14-l1x3-n<N>-<variant>.json`.

- **BitLinear layers** — weights binarized to `{−1,+1}` by an absmean quantizer
  (Sign(W−α)·β), trained with the straight-through estimator, full-precision shadow weights
  during training.
- **Activations** quantized to 8, 6, or 4 bits, static per-tensor, MSE-calibrated over 8,192
  jets with trainable calibration.
- **Architecture (the r8 `small` recipe, verbatim):** d_model 32, 2 layers, 4 heads, FFN 64,
  learned positional encoding, mean-pool over particles (permutation-invariant), 5-class
  head. **Norm-free** (`norm: none`), with input standardization on.
- **Recipe:** Adam (β₂ = 0.98), 1 warmup epoch + linear decay over 100, weight decay 0.01,
  grad-clip by value 1.0, batch 256, peak LR 2e-5, 101 epochs, early-stop patience 15 on
  val AUC.
- **Variant arms:** FP32, W8A8, W1A8, W1A6, W1A4 — 3 seeds each, at each N.
- **Hardware-cost metric:** EBOPs (Effective Bit-Operations, HGQ / arXiv:2405.00645) as the
  synthesis-free cost axis, computed by HGQ2 `trace_minmax` over the trained checkpoints,
  alongside the measured C-synthesis and Vivado out-of-context numbers of §6. Method notes: `bnjettag/results/ebops.md`.

**Synthesis target throughout:** Vitis HLS 2023.2, `xcvu13p-flga2577-2-e`, 2.5 ns clock,
`io_parallel`; the Vivado out-of-context runs of §6.3 are on `xczu7ev-ffvc1156-2-e`, with every
percentage still against the VU13P.

---

## 4. The data

| | **Public HLS4ML LHC Jet dataset (150 particles)** |
| --- | --- |
| Source | Zenodo record 3602260; arXiv:1804.06913 + 1908.05318 |
| Task | **5-class**: g / q / W / Z / t (balanced classes, no reweighting — matches published baselines) |
| Input | **Top-N constituents by pT × 3 features** — p_T, η_rel, φ_rel — for N ∈ {8, 16, 32, 64} |
| Val AUC meaning | **Macro one-vs-rest AUC** (5 classes), `validation_split=0.20` of train/ |
| ROC-test set | The dataset's own `val/` split (**n = 260,000**) — a true never-seen held-out set |

The three features are the ones a Level-1 trigger will actually provide (Odagiu et al.,
arXiv:2402.01876), which is also the convention Chang's group uses — so these results are
input-matched to that literature.

---

## 5. Tagging efficiency — Round 14: L1-realistic (N, 3) inputs

*Archived (pre-EBOP-target, Round 14); see the note at the top.*

**The input change.** Round 14 replaces the 16 stored constituent features with the three a
Level-1 trigger will actually provide — p_T, η_rel, φ_rel — and sweeps the constituent count
N ∈ {8, 16, 32, 64}. Everything else is the r8-`small` recipe verbatim (d_model 32, 2 layers,
norm-free, input_std, 101 epochs); the only variable is the input set. **These numbers carry
the `l1x3` label wherever they appear next to 16-feature results.** Design pre-registered in
decisions.md (2026-08-01); W&B project `BNJetTagAug`; 60 runs, 3 seeds/arm.

**ROC-test macro one-vs-rest AUC** (held-out split, n = 260,000; seed mean ± sample std;
verified 2026-08-04 by recomputation from `roc-results/r14/n<N>/*.npz`, 60/60 exact):

| N | FP32 | W8A8 | W1A8 (binary) | W1A6 | W1A4 |
| --- | --- | --- | --- | --- | --- |
| 8 | 0.8864 ± 0.0005 | 0.8862 ± 0.0009 | 0.8712 ± 0.0016 | 0.8689 ± 0.0020 | 0.8534 ± 0.0012 |
| 16 | 0.9128 ± 0.0013 | 0.9124 ± 0.0014 | 0.8956 ± 0.0002 | 0.8910 ± 0.0009 | 0.8693 ± 0.0021 |
| 32 | 0.9374 ± 0.0017 | 0.9358 ± 0.0011 | 0.9052 ± 0.0079 | 0.9022 ± 0.0009 | 0.8833 ± 0.0013 |
| 64 | 0.9486 ± 0.0012 | 0.9448 ± 0.0011 | 0.9121 ± 0.0116 † | 0.9136 ± 0.0061 | 0.9073 ± 0.0009 |

**Uncertainty.** Two estimates are on record — the σ_total table
(`results/r14/uncertainty_r14.md`: seed spread ⊕ paired test-set bootstrap ×200) and the
seed-paired t-interval pass of 2026-08-03 (df = 2; experiment log) — and they agree on every
resolved claim except one, noted below; where they differ the conservative verdict is adopted. Test-set noise is ≈0.0004,
so every comparison is seed-limited. **Resolved:** the binary (W1A8) deficit against FP32 at
every N (+0.0152 / +0.0172 / +0.0322 / +0.0365); W1A8 − W1A6 at N = 16 (+0.0046); the A8 → A4
step at N ≤ 16 (at N = 32 the σ_total table calls it RESOLVED, +0.0220 ± 0.0047, but the
three-seed t-interval [−0.0008, +0.0447] marginally includes zero — the one disagreement).
**Not resolved at three seeds, and therefore not claimed:** the step-to-step growth of the
binary gap (+0.0020 / +0.0150 / +0.0043 per step in the FP32 − W1A8 convention — consistent in
sign, not individually resolved); any W8A8 deficit against FP32 (at N = 64 the seed-mean gap
FP32 − W8A8 is +0.0038 and the σ_total table calls it RESOLVED, but the three-seed t-interval is
[−0.0018, +0.0095]); W1A8 vs W1A6 and the A4 step at N = 64. About 10 seeds
would settle W8A8 at N = 64 and about 30 the gap-growth steps. **† N = 64 W1A8 is a seed range,
not a mean:** 0.9028 / 0.9084 / 0.9251 — the seed-pair bootstrap intervals all exclude zero,
i.e. real training instability rather than evaluation noise.

**Per-class cost of binarization** (seed-mean one-vs-rest AUC, FP32 → W1A8, same arrays,
`roc-results/r14/n<N>/roc_auc.md`). At N = 8 and 16 the gluon class pays the most (−0.023 /
−0.025) and top the least (−0.007 / −0.010); at N = 32 and 64 the W and Z classes pay the most
(−0.046 / −0.048 and −0.063 / −0.070) and carry the binary seed instability (W1A8 per-class seed
sd up to 0.023 at N = 64), while top stays within −0.014 at every N (−0.0133 at N = 32). Binarization costs most
where the classes were already hardest to separate and least where the substructure is
distinctive; at long sequences it is the two-prong W/Z taggers that destabilize. At
trigger-style working points the same pattern is sharper (`results/r14/working_points_r14.md`,
verified 2026-08-24): at N = 16 binarization costs 3–10 signal-efficiency points at a 1% mistag
rate (Z 0.480 → 0.390, t 0.469 → 0.365), while at N = 64 the W/Z working points collapse —
W efficiency at 1% mistag 0.660 ± 0.011 → 0.209 ± 0.105, Z rejection at 50% efficiency
519 ± 60 → 32 ± 26 — with seed scatter so large that no single-seed number may be quoted. N = 16 values:
FP32 g 0.8784 / q 0.8930 / W 0.9358 / Z 0.9202 / t 0.9364 vs W1A8 g 0.8531 / q 0.8793 /
W 0.9179 / Z 0.9015 / t 0.9263.

**Findings.** (1) The three L1 features carry the task: FP32 reaches 0.9128 at N = 16 and
0.9374–0.9486 at N = 32–64 (the pre-Round-14 16-feature results are outside this document's
scope and are not compared here). (2) Binary holds at short sequences. (3) *New result:* binary
QAT destabilizes at long sequences — the seed-mean deficit is 0.015–0.017 at N ≤ 16 and
0.032–0.036 at N ≥ 32 (no interval is on record for the pooled difference; the individual steps
are unresolved, above), the binary seed variance grows ×75.8 (corrected per-N statistic), and
the weakest N = 32/64 seeds mostly peak mid-training (best epochs 57, 49 and 40 for n32-s1,
n32-s3, n64-s1; n64-s3 at 99 — `train_meta.json` of the checkpoints) and degrade afterwards
(W&B validation curves). (4) *Cost:* at matched N, W1A8 needs **5.28× (N = 8),
4.08× (16), 2.97× (32), 2.14× (64)** fewer checkpoint EBOPs than W8A8 (HGQ2 `trace_minmax` over
the trained checkpoints, `results/r14/ebops_r14.json`; the ratio falls with N because the
act×act attention terms, identical across arms, grow as N²). Two caveats on EBOPs as a cost
axis: checkpoint EBOPs omit the 15 β-restore affines the silicon carries (the n8 W1A8 export
graph has 3,025,884 EBOPs against the checkpoint's 1,739,182, +74%), and EBOPs carries no
accumulator term (`results/ebops.md`). Figures: `results/r14/figures/fig_r14_{auc_vs_n,pareto}.*`.

---

## 6. Hardware — Round 14: export v5, n8 silicon, and the device-fit campaign

*Archived (pre-EBOP-target, Round 14); see the note at the top.*

*(Export and RF=1 silicon 2026-08-04/07, verified by results-analyst 2026-08-07,
`results/r14/verification_hls_r14_2026-08-07.txt`; folded points 2026-08-12, verified
`results/r14/hls_r14_folded.md`; fit campaign 2026-08-14 → 23, numbers of record
`results/r14/hls_r14_fit.md`, verified 2026-08-23 by the numbers-gate pass recorded there.)*

**Stage discipline, in force for every number in this section.** A C-synthesis (csynth)
estimate, a Vivado post-synthesis count and a post-`opt_design` count are three different
quantities and never share a table. Every Vivado number here is an out-of-context run on part
**xczu7ev** and **pre-place-and-route**; percentages are against the VU13P's 1,728,000 CLB
LUTs. This flow — constrained `synth_design` plus `opt_design`, utilisation and timing reported
at both stages — is the hardware result of record for the project (agreed 2026-08-23); no VU13P
licence or place-and-route step is planned. "DSP = N" states whether N is the utilisation
report's *used* count (capped at the part's 1,728) or the synthesis log's *demanded* count.

### 6.1 Export v5 and its gates

Round 14 exposed a latent norm-free export defect: the exporter re-derived the β-carry-site
activation grids from measured ranges ("wide enough to never clip") while the trained
checkpoints *saturate* those grids deliberately — the export was a functionally different
network (GATE1 score correlation 0.839, argmax agreement 74%; n16, n = 4,096 jets).

**Export v5** restores every β in-graph via its own shift-add affine (6L+3 affines) and applies
every trained activation/attention grid verbatim; the β-constant encoding is measured per
article (csd2/csd3/fx8/exact ladder, stored in `export_verify.json`) with **fx8 shipped**
under the pre-registered ≥ 0.997 rule (decisions.md 2026-08-04).

**Gates.** GATE1 **0.9988** (n8-s3) / **0.9974** (n16-s1) — score correlation, n = 4,096 jets,
argmax agreement 0.980 / 0.976; GATE2 hls4ml C-sim **bit-exact** (n = 128) on both. Normed
exports are unaffected (`results/r14/regress_normed_v5_final-w1a8-s1.log`). Export EBOPs drop
33–48% versus the pre-v5 widened grids. The exported graphs' own ROC-test AUCs were
measured 2026-08-24 (`results/r14/export_roc_auc.md`): every synthesized article is
AUC-equivalent to its trained network (Δ between −0.00033 and +0.00000).

### 6.2 C-synthesis operating points (n8-s3 whole model, Vitis HLS 2023.2, VU13P target, 2.5 ns)

**RF=1, Latency strategy — the max-parallelism reference, not a fit point**
(`results/r14/hls_r14.md`):

| Point | Cycles | Est. period | II | csynth LUT | DSP |
| --- | --- | --- | --- | --- | --- |
| fx8, RF=1 Latency | 164 | 1.825 ns (0 timing flags) | 1 | 3,178,720 (184.0%) | 4,133 |
| + `config_op mul -impl fabric` (solution-wide) | 146 | 2.287 ns (18 flags, see note) | 1 | 4,376,222 (253.3%) | **0** |

At the fx8 point every binary matmul (`einsum_dense` ×13, both head QDenses) and all four
act×act attention einsum instances are already **0 DSP**; the 4,133 DSPs are the 15 β-restore
affines (3,621) plus softmax (512). Binding those to fabric takes the design to 0 DSP (+1.20M
csynth LUT). *Timing note:* Vitis flags 18 Timing-Violation entries — the top module (listed twice) plus
the 16 fabric-ized multiply module classes (14 `normalize`, 2 `softmax_stable`) — the period
estimate exceeds the 2.5 − 0.68 ns clock-uncertainty budget; cycles and II are unaffected.

**Folded (dataflow, per-layer parallelization factor) points** (`results/r14/hls_r14_folded.md`):

| Point | Cycles | II | csynth LUT | DSP | Note |
| --- | --- | --- | --- | --- | --- |
| pf1 (max fold), DSP-carrying | 339 | 48 | 3,198,568 (185.1%) | 3,637 | 10 timing flags |
| pf2 | 265 | 32 | 4,166,195 (241.1%) | 3,653 | misses 2.5 ns (est 2.685 ns) |
| pf1 + solution-wide fabric (`pf1fab`) | 329 | 47 | 4,216,272 (244.0%) | **0** | 28 flags |

Folding shrinks the folded modules (e.g. `einsum_dense` −35%) but the dataflow glue
(FIFOs, process logic, ≈+585k LUT) cancels it: pf1 lands within 0.7% of the RF=1 reference
while the interval rises 1 → 48. These are deployable-class points answering a different
question from the RF=1 reference and are never tabulated as improvements of it.

### 6.3 Device fit, measured at Vivado synthesis

The fit question is decided at Vivado synthesis, not at csynth: csynth over-estimates this
design class's LUTs by roughly 2×, and — as §6.4 shows — a csynth DSP count of zero does not
survive technology mapping unless the binding is explicit. All rows below except the
DSP-carrying baseline (row 1: constraint applied after synthesis, no `opt_design`): Vivado 2023.2,
`synth_design -mode out_of_context` with the 2.5 ns constraint applied *before* synthesis
(timing-driven), then `opt_design`; part xczu7ev; pre-route.

| Build (n8-s3, export v5 fx8) | Stage | CLB LUT | % VU13P | DSP used / demanded | WNS @ 2.5 ns | Thesis point? |
| --- | --- | --- | --- | --- | --- | --- |
| RF=1 fx8, DSP-carrying (non-timing-driven run, no opt_design) | post-synth | 1,869,030 | 108.2% | 1,728 / 8,229 | +0.164 (post-hoc STA) | no — DSP-assisted |
| RF=1 + solution-wide fabric (II=1, 146 cyc) | post-opt | **2,108,743** | **122.0%** | **0 / 0** | −0.967 (post-synth −0.145) | **yes — misses by 380,743** |
| folded pf1 + solution-wide fabric (II=47, 329 cyc) | post-opt | **1,948,063** | **112.7%** | **0 / 0** | −1.922 (post-synth −1.982) | **yes — misses by 220,063** |
| folded pf1 + *scoped* fabric binding (II=47, 330 cyc) | post-opt | 1,797,874 | 104.0% | 1,728 / **4,096** | −2.076 | **no — resource swap (§6.4)** |
| folded pf1 + scoped binding + softmax operand `ap_ufixed<4,0>` (II=48, 333 cyc) | post-opt | **1,694,625** | **98.1%** | **0 / 0** | −1.943 | **fits — structure-only build (see below)** |

Calibration, per design and per stage (never pooled): post-opt / csynth = 0.482 (RF=1
fabric), 0.462 (pf1fab), 0.442 (the narrowed build); the DSP-assisted baseline is 0.588 at
post-synth because 6,501 of its demanded DSP sites were fabric-mapped on the small part.
Timing-driven synthesis alone added +99,234 LUT on the RF=1 fabric design over a
non-timing-driven run; `opt_design` recovers 0.1–1.8% (0.10% RF=1 fabric, 1.24% pf1fab, 1.82%
scoped, 1.42% narrowed), never more. LUT-as-Memory on the
folded points (99,751–105,679) is SRL shift registers from the dataflow schedule, not a
BRAM spill (BRAM ≈7% used) — a part-utilisation caveat, not a discount on the gap.

**The fitting point is a characterization build, not yet an operating point.** Its context
einsum takes the attention softmax output at `ap_ufixed<4,0>` instead of the trained
`ap_ufixed<10,1>`; that grid was forced on the export (`convert_final.py
--force-softmax-out-bits 4`), so the C-simulation is deliberately *not* bit-exact to the trained
network and no accuracy attaches. Against the scoped build it saves 126,928 csynth LUT
(−121,344 of it in the two context einsums, −29.6% of that family; −5,632 in narrower dataflow
FIFOs; +48 in the two softmax loop processes; every other module instance byte-identical) and, decisively, removes the DSP inference:
Vivado maps 10-bit × 8-bit attention products onto DSP48E2s but leaves 8-bit × 4-bit products in
fabric. The margin is 33,375 LUT (1.9%), on the small part, pre-route — "fits at post-opt,
out-of-context, xczu7ev" is the whole claim. The trained counterpart — the same grid set in
QAT (`quant.softmax_out_bits = 4`, `softmax_out_i = 0`; a 6-bit arm as fallback), N = 8, W1A8, 3
seeds each — is training; under the pre-registered rule (ship the narrowest arm whose one-sided
95% upper bound on ΔAUC vs W1A8 is ≤ 0.005) it becomes either the first fitting zero-DSP
operating point with an AUC, or evidence that the frontier above is the result.

**Clock.** At the 2.5 ns constraint every zero-DSP point fails timing pre-route (post-opt WNS
−0.97 to −1.94 ns on the zero-DSP points, implying ≈3.5–4.4 ns; the scoped DSP-carrying build is
−2.08 ns); only the DSP-assisted baseline shows non-negative slack, and that from a
non-timing-driven run. **Constrained at 5.000 ns, the fitting design meets timing** (same RTL,
out-of-context on xczu7ev, post-opt WNS +0.557 ns with 0 failing endpoints, DSP 0, 1,583,181 CLB
LUT = 91.6% of the VU13P; `hls_r14_fit.md` row 6): one jet every 48 cycles = 240 ns and a
333-cycle latency = 1.67 µs at 5 ns, pre-route. The 2.5-ns and 5-ns runs are different
timing-driven netlists of the same RTL and are both kept; neither replaces the other. A
place-and-route run is not possible by construction: the zero-DSP netlists exceed the licensed
part's 230,400 CLB LUTs by 7.4–9.2×.

**The trained grids (2026-08-23/24): the fit question is answered.** Both retrained arms hold the
accuracy — 6-bit softmax grid 0.8706 ± 0.0017, 4-bit 0.8701 ± 0.0020 ROC-test macro-AUC against
the W1A8 control's 0.8712 ± 0.0016 (drops +0.0006 / +0.0011, one-sided 95% upper bounds +0.0029 /
+0.0035, both inside the pre-registered ≤ 0.005 bar; arrays `roc-results/r15-gamma/`, verified by
recomputation). The narrowest passing arm (4-bit — the grid of the characterization build) was
exported (fidelity 0.99805 vs its own checkpoint, C-sim bit-exact, trained `ap_ufixed<4,0>` in the
firmware), folded, scope-bound and synthesized: C-synthesis 3,837,485 LUT / 0 DSP / II 48 — within
0.03% of the characterization build — and at Vivado post-`opt_design` **1,689,320 CLB LUT = 97.8%
of the VU13P at a DSP demand of zero**. **This is the first fitting zero-DSP operating point**, with
its accuracy attached: −0.0011 vs the trained-grid control, −0.016 vs FP32 at N = 8. Caveats as
everywhere in this section: xczu7ev, out-of-context, pre-route, a 2.2% margin; timing at 2.5 ns is
not met (WNS −1.85), but **the same RTL constrained at 5.000 ns meets timing pre-route** —
post-opt WNS +0.647 ns with 0 failing endpoints at DSP 0 and 1,583,565 CLB LUT (91.6%): one jet
per 48 cycles = 240 ns, 333-cycle latency = 1.67 µs at 200 MHz (`hls_r14_fit.md` rows 7–8).

### 6.4 What the measurements teach

**Zero DSP at C-synthesis does not mean zero DSP on silicon (Vivado run of 2026-08-19, read 2026-08-20).** Scoping
the fabric binding to the two DSP-carrying functions (`nnet_batchnorm.h::normalize`,
`nnet_activation.h::softmax_stable`) lowers the folded point from 4,216,272 to 3,963,344
csynth LUT with csynth still reporting DSP = 0 — but Vivado then **demands 4,096 DSPs**
(`[Synth 8-3323] Resources of type DSP have been overutilized. Used = 4096, Available = 1728`,
`vivado_run.log:81820`): the 10-bit-unsigned ×
8-bit-signed products of the attention context einsum, exactly its MAC count at N = 8, are
re-inferred as DSP48E2s once HLS emits them as a plain `*`. The 150,189 post-opt LUT that build
"saves" (1,797,874 vs 1,948,063) are bought with multipliers the thesis point does not use; the
solution-wide binding remains the zero-DSP point of record at the trained grids. Rule adopted:
every zero-DSP claim is verified at Vivado synthesis, never at csynth alone; the A6/A4 ladder
rows and the n16 attribution, both csynth-only, are labelled "csynth attribution".

**Where the LUT lives** (per-module-family attribution of the stored reports; n8-s3): the 15
β-restore affines carry the fabric premium (+705k–759k csynth LUT for shedding 3,621 DSPs,
≈195–210 LUT per DSP); the four act×act attention einsums cost 645k–949k at the folded point
depending on whether the solution-wide directive reaches them (+303,104 = 37.0 LUT/MAC of pure
penalty, identical at RF=1); the saturating requantisation casts ≈155 LUT per element
(164,160); softmax shrinks ≈74% under folding (368,128 csynth LUT at RF=1 fabric → ≈95k at the folded
fabric points: 71,218 in the two rolled softmax body processes plus 23,668 in their loop
processes; the two `softmax_stable` shells alone are ≈12k). The binary
matmuls themselves (`einsum_dense`, 1,630,567 at RF=1 / 1,060,056 folded) are untouched by
every binding choice.

**Conversion-level levers, all measured and closed** (one lever per build, GATE1 identical,
GATE2 bit-exact, emitted firmware inspected; report `docs/reports/job-alpha-fit-campaign-2026-08-17.pdf`
with dated addenda): distributed arithmetic on the 13 binary einsums (+21.9% csynth LUT, ×2.94
FF — retained only because it shrinks the Vitis front end 4.15×); the hls4ml ReLU-parse fix
(Δ = 0 LUT — Vitis constant-propagates the threshold; kept as a correctness fix); folding alone
(+0.6%); folding plus fabric (closes ≈42% of the RF=1 gap); `opt_design` (0.1–1.8%); scoped
binding (resource swap, above). Four cost-model projections made during the campaign were each
killed by the measurement they predicted; projections have no standing on this design class.

### 6.5 The activation ladder in silicon, and what is not measured

W1A6 and W1A4 n8 articles were exported and C-synthesized at RF=1 (2026-08-14;
`results/r14/hls_r14_activation_ladder.md`, not yet independently verified, so its LUT numbers
are not quoted here). Their exports **fail the GATE1 correlation bar** (0.99518 / 0.98340, argmax agreement
0.9543 / 0.9153, n = 4,096) — the fidelity loss is intrinsic to restoring β through a narrow
activation grid, not to the β encoding. The per-jet drift is however ranking-preserving: the
exported graphs' own held-out AUCs, measured 2026-08-24, are 0.86991 (W1A6, −0.00019 vs its
trained network) and 0.85325 (W1A4, −0.00008) — so a measured accuracy now attaches to that
silicon after all (`results/r14/export_roc_auc.md`); neither article has been through Vivado. Noted for the record: at A4 the β affines leave the
DSPs natively at csynth (a csynth attribution; after §6.4 it has no netlist standing until
checked).

**Not measured, stated plainly (and, for n16, accepted as the standing scope — decision
2026-08-24):** n16 and above are not synthesized whole-model (the rf1
Latency run died at 17.7 h without a report; the n16 DSP attribution exists at csynth only);
the W8A8 version of the same graph is NOW measured at C-synthesis (2026-08-25, RF=1, same part
and clock): **6,419,238 LUT (371.5% of the VU13P) + 1,384 DSP + 512 BRAM_18K**, 148 cycles at
II = 1 — against the binary fx8 reference's 3,178,720 LUT (184.0%) + 4,133 DSP. The 13
weight-matmul layers: W8A8 5,013,220 LUT + 872 DSP vs binary 1,630,567 LUT + **0 DSP** (Vitis
DSP-maps only ~5% of the 17,664 8-bit weight multipliers (872) at this stage and LUT-maps the rest; the Vivado
OOC — the netlist-level DSP demand — settles it). Settled 2026-08-25 — the Vivado OOC of the W8A8
RTL (xczu7ev, 2.5 ns, flow of record): post-opt **2,525,842 CLB LUT (146.2% of the VU13P) with
a DSP demand of 5,550** (`[Synth 8-3323]`; used caps at the part's 1,728) against **0 demanded**
by every binary zero-DSP build. Schedule-matched (II = 1) it needs 1.20× the LUTs of the
solution-wide-fabric binary build plus the DSPs; against the shipped folded operating point
(a different schedule) 1.50× (fit-ladder row 9, `results/r14/hls_r14_fit.md`). The FP32
arm is no longer absent from silicon, but what exists is a *staged, fixed-point realization*
of it — see the block below. Labels:
stages as marked — C-synthesis for the resource/latency figures above, Vivado post-opt (xczu7ev OOC, pre-route) for the netlist numbers; the W8A8 article's C-sim passes 0.997 but is not bit-exact (AUC-neutral,
+0.000175 paired); store `runs/9cc6e336/w8a8-s3-r14n8/`. Every
exported graph now has a measured ROC-test AUC (§6.1), and the fitting design meets a 5 ns
clock pre-route (§6.3).

**The FP32 baseline in silicon — C-synthesis only, and what the label means (2026-09-02/03;
design memo `docs/reports/fp32-silicon-baseline-design-2026-09-02.md` with AMENDMENT A1 and
CORRECTION C1; numbers-gate pass 2026-09-03).** The FP32 article is **not synthesizable as
float in this flow**: the unquantized checkpoint carries no datapath, and hls4ml's HGQ2
frontend rejects its dummy quantizers. Literal floating-point silicon does not exist here and
is not planned. What is measured instead is the **FP32-*trained* network realized on an
`ap_fixed<W,·>` datapath**, with W chosen as the narrowest grid meeting the ratified fidelity
bars against the float export: **W\* = 16** (per-class ε_S @ 1% FPR and per-class ΔAUC upper
bounds at n = 32,768, 99% level per A1's multiplicity rule R1; the binding bar clears by
2.7–2.9× and the choice is confirmed on **all three FP32 seeds** — s1/s2/s3 corr 0.999995 /
0.999998 / 0.999995, argmax 0.9993 / 0.9994 / 0.9991). W = 12 fails R1; W = 16/20/24 are
indistinguishable, so W\* = 16 is the cheapest rung on a converged plateau. Selecting the
narrowest passing rung is conservative *against* the thesis (a cheaper FP32 baseline makes the
binary advantage smaller, not larger).

C-synthesis, n8-s3, RF = 1 Latency, Vitis HLS 2023.2, part xcvu13p, 2.5 ns — the same
part/clock/schedule as every other row in this table; percentages are against the VU13P
(1,728,000 LUT / 3,456,000 FF / 12,288 DSP / 5,376 BRAM_18K):

| Build (n8-s3, RF=1) | Stage | csynth LUT | FF | DSP | BRAM_18K | Cycles (II) |
| --- | --- | --- | --- | --- | --- | --- |
| **FP32-trained, `ap_fixed<16,·>` realization (W\* = 16)** | C-synth | 7,215,326 (417.6%) | 16,817,368 (486.6%) | **140,130 (1,140.4%)** | 12,544 (233.3%) | 165 (1) |
| FP32-trained, `ap_fixed<8,·>` realization (width-only control, fails the fidelity bars) | C-synth | 7,562,029 (437.6%) | 4,447,110 (128.7%) | 24,824 (202.0%) | 512 (9.5%) | 152 (1) |
| W8A8 article (comparator, above) | C-synth | 6,419,238 (371.5%) | 2,307,117 (66.8%) | 1,384 (11.3%) | 512 (9.5%) | 148 (1) |

**W\* = 16 is infeasible at RF = 1, on DSP alone: 140,130 DSP = 1,140% of the VU13P** (4,561%
per SLR), against 202% for the W = 8 control and 11% for the W8A8 article. This is stated first
because it, not the LUT count, is the binding failure. (LUT is non-monotone in W — the W = 8
control shows *more* LUT than W = 16 because at W = 16 Vitis absorbs the constant-weight
multiplies into DSPs instead of fabric.)

**Vivado OOC: attempted and failed, on BRAM capacity.** The netlist stage was run on the W\* = 16
RTL in the flow of record (Vivado 2023.2, `synth_design -mode out_of_context`, licensed part
**xczu7ev**) and terminated with `ERROR: [Synth 8-5834] Design needs 24768 RAMB18 which is more
than device capacity of 624` — 624 RAMB18 being the **xczu7ev's** capacity, not the VU13P's
(5,376, which the demand also exceeds by 4.6×). The run died after 3 h 44 m (wall time from the
mulder log, transcribed in memo C1.1; the local store holds only the error excerpt, so the OOC
part is inferred from the 624-RAMB18 capacity line plus the §6.3 flow of record). The cause is
localized and is **a realization artifact, not a property of the FP32 network's arithmetic**:
all 12,544 BRAM_18K of the C-synthesis estimate sit in the 64 `softmax_stable` instances (196
each, against 8 each at W = 8) and none in `einsum_dense`, because hls4ml sizes the exact
softmax table as 2^width(`softmax_inp_norm_t`) — that type widens `ap_fixed<10,7>` → `ap_fixed<16,7>`
and `exp_table_size` goes **1,024 → 65,536** (read from the emitted `firmware/parameters.h`).
It is fixable by bounding the inp_norm width or overriding the table, but any such fix changes
the bit-exact contract and is therefore a re-run decision. Consequence recorded for the flow:
the OOC was gated on LUT only; DSP and BRAM gates are both binding on this design class and
must be pre-registered in future.

**What the FP32-W8 vs W8A8 DSP contrast may and may not be used for.** The width-only W = 8
control needs 24,824 DSP where the W8A8 article needs 1,384 — 17.9× whole-model, 27.9× on
`einsum_dense` alone, with the act×act attention einsums identical to 0.04% in LUT and softmax
DSP identical (512) in all three builds. The gap is real and is not a pipeline defect (same
part, clock, RF and flags; W applied exactly; a controlled pair — block-0 `Wq`, same shape,
same input type, same 24-bit weight container — gives 144 DSP for W8A8 against 3,072 for the
control, differing only in weight *values*). **It is not, however, an equal-precision
comparison and must never be quoted as one.** The two arms are not weight-width-matched: the
W8A8 article's emitted per-layer weight typedefs are `ap_fixed<6,1>` throughout (6-bit, 5
fractional — HGQ2's *converged* grid under a nominal 8-bit budget, which hls4ml's bit-exact
frontend narrows to), while the PTQ control's are `ap_fixed<9,1>` (9-bit, 8 fractional; 8-bit
at `input_proj` and `head_fc2`). The eight attention arrays carry no per-layer typedef in
hls4ml 1.3.0 and take the same 24-bit `model_default_t` container in *both* arms — so at exactly
the layers where the DSP gap lives, the container is identical and what differs is the realized
grid density of the values (5 versus 8 fractional bits). The contrast therefore conflates **grid provenance (QAT vs
PTQ) with ≈3 bits of realized weight width**, and that split **cannot be decomposed from
anything on disk**. A width-matched PTQ arm is in preparation to resolve it; until it exists,
no ratio between these two rows is a precision statement. **Nothing about the W8A8 article's own
measured numbers changes** — it is not mislabelled, and its rows above stand as written.

**Stage labels for this block:** every FP32 resource/latency figure above is **C-synthesis
(estimate)**, not a netlist count; the only netlist-stage outcome for the FP32 arm is the failed
xczu7ev OOC. Fidelity figures are local C-sim at n = 32,768 against the float export, not
ROC-test AUC on the 260,000-jet split. Stores: `results/synthesis/runs/40103802/`.

---

## 7. Where every number comes from

Durable copies are versioned W&B artifacts (`model-<leaf>`, `evaluation-*`, `synthesis-*`)
per `docs/infrastructure/wandb-layout.md`.

| Claim | Source (relative to `bnjettag/`) |
| --- | --- |
| **ROC-test AUCs (§5)** | `roc-results/r14/n{8,16,32,64}/roc_auc.md`; recomputable from `roc-results/r14/n<N>/*.npz` (verified 2026-08-04, 60/60 exact); durable: W&B artifacts `evaluation-r14-l1x3-n<N>` + 60 `model-*` artifacts, project `BNJetTagAug` |
| **EBOPs + uncertainty verdicts (§5)** | `results/r14/ebops_r14.json` (HGQ2 trace_minmax, 48 ckpts); `results/r14/uncertainty_r14.{json,md}` (incl. the 2026-08-04 Q4 correction); figures `results/r14/figures/` |
| **Export-v5 gates + n8 silicon (§6)** | `results/synthesis/runs/38a20c62/w1a8-s3-r14n8/{export_verify,csim_verify,ebops}.json` (incl. the β-encoding `gate1_ladder`; pre-v5 state preserved as `*.pre-v5-2026-08-04.json`) + `csynth_rf1{,_fabric}/{csynth.xml,myproject_csynth.rpt,csynth_report.json}` (+ `csynth_rf1_fabric/build_prj.tcl`, `build_opt.tcl`); parsed numbers-of-record table `results/r14/hls_r14.md`; independent recompute `results/r14/verification_hls_r14_2026-08-07.txt`; normed-guard regression `results/r14/regress_normed_v5_final-w1a8-s1.log`; n16 export gates (silicon not synthesized): `results/synthesis/runs/2ae656b6/w1a8-s1-r14n16/`; W&B `synthesis-r14n8_w1a8s3_fx8_rf1{,_fabricmul}`, project `BNJetTagAug` |
| **Folded / dataflow operating points** | `results/r14/hls_r14_folded.md`; raw reports under `results/synthesis/runs/38a20c62/w1a8-s3-r14n8-pf{1sm1,2sm2,4sm4}df/` (the `2ae656b6` n16 folded leaves carry gates and tarballs only, no csynth report) |
| **Device-fit ladder, calibration, Beta lessons (§6.3–6.4)** | numbers of record `results/r14/hls_r14_fit.md`; raw Vivado reports `results/synthesis/runs/38a20c62/w1a8-s3-r14n8/postsyn_xczu7ev{,_fabric,_fabric_v2}/`, `…-pf1fab/postsyn_xczu7ev/`, `…-pf1scoped/postsyn_xczu7ev/` (incl. `vivado_run.log`), `…-beta1sm4i0/{csynth_beta1sm4i0,postsyn_xczu7ev}/` (`post_{synth,opt}_{util,timing}.rpt`, `synth_ooc.tcl`, `clock.xdc`); per-family parser `code/hgq2/parse_families.py`; dead-lever builds `…-da13/` (csynth), `…-relufix/` (csynth_report.json), `…-da13rf/` (exported, not synthesized); the baseline's 8,229-DSP demand line is excerpted in `…/w1a8-s3-r14n8/postsyn_xczu7ev/vivado_log_excerpt_dsp_demand.txt` (full log on mulder) and the DA 4.15× front-end figure is held in mulder logs, transcribed in the experiment log (2026-08-15); the two 2026-08-14/15 RF=1 runs `postsyn_xczu7ev{,_fabric}/` carry `post_synth_*` and `synth_ooc.tcl` only, `_fabric_v2/` uses `synth_ooc2.tcl`; frozen report `docs/reports/job-alpha-fit-campaign-2026-08-17.{tex,pdf}` (Addenda 1–3); narrative `.claude/memory/experiment-log.md` 2026-08-14 … 2026-08-23 |
| **Per-class AUC (§5)** | `roc-results/r14/n{8,16,32,64}/roc_auc.md` (seed-averaged per-class rows, generated by `roc_final.py` from the same `.npz`) |
| **Working points (§5)** | `results/r14/working_points_r14.{json,md}` (TPR@FPR∈{1%,10%}, rejection@TPR∈{0.5,0.7} per class/arm/N + the Gamma arms; script `code/plots/make_working_points.py`; gate-verified 2026-08-24) |
| **Exported-graph AUCs (§6.1, §6.5)** | `results/r14/export_roc_auc.{json,md}` (script `code/hgq2/export_roc_eval.py`; GATE1-reproduction arbiter per article; independently re-derived for n8 W1A4 to <1e-6; 2026-08-24) |
| **EBOPs ratios per N (§2, §5)** | `results/r14/ebops_r14.json` (`models.<run>.ebops`, seed-identical); export-graph EBOPs `results/r14/hls_r14.md` |
| **Uncertainty verdicts (§5)** | `results/r14/uncertainty_r14.{json,md}` (σ_total) + the 2026-08-03 seed-paired t-interval pass, `.claude/memory/experiment-log.md` |
| **FP32 silicon baseline, staged (§2, §6.5)** | C-synthesis of record `results/synthesis/runs/40103802/fp32-s3-r14n8-w{16,8}/csynth_rf1/{csynth_report.json,myproject_csynth.rpt,csynth.xml}` (re-derived 2026-09-03, incl. per-family attribution and the emitted `hls_prj_rf1/firmware/{defines.h,parameters.h}`); realization grids `…/realization.json`; failed Vivado OOC `runs/40103802/postsyn-fp32-w16-n8-rf1/vivado_log_excerpt_bram_failure.txt` (full log on mulder); W* selection ladder `runs/40103802/fp32-s3-r14n8-ladder.json` (+ `-s{1,2}-` seed confirms and `fp32-s{1,2,3}-r14n8-w16/`); driver `code/hgq2/convert_fp32.py`; design memo `docs/reports/fp32-silicon-baseline-design-2026-09-02.md` (AMENDMENT A1 + addendum, CORRECTION C1) |
| **FP32-W8 vs W8A8 DSP gap and its width label (§6.5)** | per-family parse `code/hgq2/parse_families.py` over the three `csynth_rf1` stores (`40103802/fp32-s3-r14n8-w{8,16}/`, `9cc6e336/w8a8-s3-r14n8/`); emitted weight typedefs in each store's `defines.h` (`ap_fixed<6,1>` W8A8 vs `ap_fixed<9,1>` PTQ control) and weight arrays `firmware/weights/w*.h`; diagnostic narrative `.claude/memory/experiment-log.md` 2026-09-03 (+ the numbers-gate pass at the top of that file) |
| **Activation-ladder exports (§6.5)** | `results/synthesis/runs/5f839ab5/w1a4-s3/` and `794e925f/w1a6-s3/` (`export_verify.json` GATE1, `csim_verify.json`); `results/r14/hls_r14_activation_ladder.md` (C-synthesis, unverified) |
| **Gamma training arms (§6.3)** | `code/hgq2/configs/gen_r15_gamma.py` → `r15-gamma-sm{4,6}i0-n8-w1a8.json`; `code/jobs/training/variants/gen_r15_gamma_jobs.py` (+ ROC `gen_r15_gamma_roc_jobs.py`); ConfigMap `kai-bn15-code` md5 `1449a4b4…8314`; W&B group `r15-gamma`, project `BNJetTagAug` |
| **pT sample re-weighting study, N=8 W1A8, 3 arms × 8 seeds (2026-09-25)** | `roc-results/ptw-n8/roc_auc.md` + `summary.json`; recomputable from `roc-results/ptw-n8/{BASE,PTW5,PTWNC}-s{1..8}.npz` (24 arrays, n = 260,000; recomputed 2026-09-26 by newton rounds, 24/24 exact to 4 dp); scripts `code/hgq2/sample_weighting/`; checkpoints `results/ptw-n8-20260925/checkpoints/`; campaign record `campaigns/2026-09-25-pt-weighting/` (lab repo `local/` until the workspace merge). The falsifier and the pT-sextile analysis were written after the results; the study confirms its numbers, it is not a pre-registered test. |
| Model + training configuration | `code/hgq2/configs/r14-l1x3-n<N>-<variant>.json`; job specs `code/jobs/training/variants/kai-bn14-*.yaml` |
| Design pre-registration and round rationale | `.claude/memory/decisions.md`, 2026-08-01 and 2026-08-04 entries |
| EBOPs method | `results/ebops.md` |
| HGQ2 + hls4ml layer support / constraints | `results/hgq2/constraints_map.md` |

Verification procedure: `.claude/skills/verify-roc/SKILL.md`. **Anything not traceable to
this table is not a project claim.**

---

## 8. Literature anchors

- **BitNet** (arXiv:2310.11453) — the 1-bit transformer training method we adapt
  (+ b1.58 ternary, 2402.17764; a4.8 activations, 2411.04965).
- **Sub-microsecond Transformers for Jet Tagging on FPGAs** (arXiv:2510.24784) — the
  closest published system: full-precision-ish transformers through hls4ml into L1-trigger
  latency. Our differentiator is the 1-bit weight core and its DSP-free mapping.
- **Odagiu et al.** (arXiv:2402.01876) — the source of the `(N, 3)` L1-realistic input
  convention used throughout Round 14.
- **HGQ** (arXiv:2405.00645) — the EBOPs cost metric and the HGQ2 QAT stack.
- **hls4ml** (arXiv:1804.06913) — the codesign tool and the trigger-ML program it anchors.
- **HLS4ML LHC Jet dataset** (arXiv:1804.06913 + 1908.05318, Zenodo record 3602260) — the
  public benchmark that makes our numbers comparable to published taggers.

Annotated notes and PDFs: [`docs/literature/`](docs/literature/INDEX.md).
