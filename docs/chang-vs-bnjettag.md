# Chang's group vs BNJetTag — a code and method comparison

> **Correction, 2026-08-14.** An earlier version of this document quoted "180–279k LUT" as
> Chang's comparable figure. That mixes their **N=32** (180k) and **N=16** (279k) rows against
> our **N=8** silicon. The matched-N comparand is **MHA-8 = 246k LUT, post-route, 0 DSP,
> 104 ns, II=1**. Reasons 3–5 below were also corrected after a red-team pass; see the change
> note at the end.

Reference: Laatu, **Sun**, Cox, Gandrakota, Maier, Ngadiuba, Que, Luk, Spiropulu, Tapper,
*Sub-microsecond Transformers for Jet Tagging on FPGAs*, **arXiv:2510.24784v1** (26 Oct 2025).
Code: `reference-code/HGQ2-examples/jsc150/`, HEAD `6cdc6e3` — **eight months downstream of the
paper**, and it disagrees with the paper in several load-bearing places.

Full replication analysis: `docs/literature/jet-tagging-transformers/2510.24784_replication-targets_hgq2-examples.md`.
Everything below is sourced from that note, their `model.py`/`run_train.py`, or our own stores.

---

## The short answer to "why is our model so big"

Four reasons, in order of how much they explain:

**1. They train to a hardware budget. We don't.**
Their entire method is hardware-cost-aware training: an EBOPs target of **350,000** ("roughly
one Super Logic Region of the XCU250"), enforced by β-weighted regularization, with HGQ learning
per-tensor bitwidths to hit it. Model selection is a **Pareto front over (val_accuracy ↑,
ebops ↓)**. The architecture is *pinned by the budget* — accuracy is the free variable.

We train for accuracy with bitwidths **fixed by the thesis** (1-bit weights, 8-bit activations)
and measure resources afterward. Nothing in our loop ever pushes size down. That is the single
biggest difference, and it is a *method* difference, not a bug.

**2. Their architecture is genuinely smaller.**

| | Chang (`get_transformer`, MHA) | BNJetTag R14 |
|---|---|---|
| encoder blocks | **1** | **2** |
| d_model | **24** | **32** |
| heads | 2 (key_dim 16) | 4 |
| FFN width | **32** (`dim*h`) | **64** |
| head | GAP → 32 → 32 → 32 → 5 | GAP → head → 5 |
| positional encoding | **none** (permutation-invariant) | **learned** |
| activations | `QAffinedUnaryFunctionLUT('tanh')` — a **table lookup** | ReLU |
| norm | `QEinsumDenseBatchnorm` (fused BN) | **norm-free** |

Two blocks instead of one is ~2×. d_model 32 vs 24 is ~(32/24)² ≈ 1.8× on every matmul. FFN 64
vs 32 is 2×. Those compound. Their LUT-based `tanh` is also nearly free on an FPGA in a way ReLU
plus explicit requantization is not.

**3. We are comparing an HLS estimate against their post-route number — and, worse, our
DSP-spending point against their DSP-free ones.**

Their `gather_statistics.py` reads `<top>_post_route_util.rpt` — **post-place-and-route**. Our
numbers are **csynth estimates**. Our own anchor measured csynth over-estimating LUT by
**2.29 / 2.30 / 2.51 / 2.51×** (`_attic/compiler-workstream/adder-graph/e1/POSTSYN.md`). Note
that anchor is csynth → **post-synthesis** (`synth_design -mode out_of_context`), *not*
post-route, on xczu7ev, over four arms of a single layer class — so it is a **lower bound** on
the true deflation, measured on a design class unlike ours.

**The correction that matters more:** every Chang row is **0 DSP**. Our 3,178,720-LUT point
spends **4,133 DSP**. The like-for-like row against a 0-DSP reference is the fabric-multiply
point, **4,376,222 LUT = 253.3 % of VU13P** (`hls_r14.md`). Both must be stated:

| point | LUT | % VU13P | DSP | deflated 2.29–2.51× | vs Chang MHA-8 (246k) |
|---|---|---|---|---|---|
| fx8 | 3,178,720 | 184.0 % | 4,133 | 1.27–1.39M (**73–80 %**) | 12.9× → 5.1–5.6× |
| fabric (**0 DSP**) | 4,376,222 | 253.3 % | 0 | 1.74–1.91M (**101–111 %**) | 17.8× → 7.1–7.8× |

So: the fx8 point may well fit once implemented — **but only if we keep 4,133 DSPs, i.e. only
by giving up the 0-DSP headline.** The configuration the thesis is actually about does **not**
fit even under the most generous deflation. These are two different operating points and must
never be quoted in the same breath.

**4. No fit-oriented configuration has succeeded — and one has already failed.**
All 11 emitted projects are `ReuseFactor: 1, Strategy: Latency`; `hls_r14.md` labels RF=1 "the
max-parallelism reference, **not a fit point**." But we *have* attempted fit once:
`hls_r14_folded.md` (signed off pass 3) tested dataflow + `parallelization_factor` and found
maximum fold lands at 3,198,568 LUT — **0.7 % worse** than RF=1 — while II goes 1 → 48. Its
finding 1 reads "PF-under-DATAFLOW folding does not deliver device fit at whole-model scale."
The routes still untested are **per-layer RF maps**, **Resource mode**, and
**`distributed_arithmetic`**.

**5. There is no baseline synthesis to attribute any of this to binarization.**
The synthesis store contains **only `w1a8` articles** at both hashes — no FP32, no W8A8, at any
N. So no measured statement of the form "binarization cost/saved X LUT on this architecture"
exists. The 3.18M number cannot distinguish "binary is expensive in LUT" from "this
architecture is expensive in LUT", and reason 2 above suggests much of it is the latter.

---

## Their Table 1 is iso-EBOPs, not a scaling study

This matters for reading their N sweep, and it is easy to get wrong.

| # | Model | N | Acc (%) | Latency (ns) | LUT (k) | II | DSP |
|---|---|---|---|---|---|---|---|
| 1 | MHA | 8 | 66.3 | 104 | 246 | 1 | 0 |
| 2 | MHA | 16 | 72.3 | 98 | 279 | 1 | 0 |
| 3 | MHA | 32 | 77.0 | 83 | 180 | 1 | 0 |
| 4 | MHA | 64 | 77.9 | 44 | **47** | 1 | 0 |
| 5–8 | Linformer | 8/16/32/64 | 66.3 / 72.8 / 78.4 / **79.8** | 110 / 103 / 140 / 78 | 230 / 246 / 267 / 202 | 1 | 0 |

Every row shares the same 350k-EBOPs target, so **LUT is roughly pinned and accuracy is the free
variable**. MHA LUT *falls* 279 → 180 → 47k as N goes 16 → 32 → 64 — because the budget forces
the model to shrink as the sequence grows. Their own Fig. 1 caption concedes the N=64 accuracy
behaviour "is expected due to the fixed resource budget we enforced during training."

**Row 4 is disqualified by their own paper** (§3 verbatim): the MHA-64 attention block
"consistently collaps[ed] … turning it into a Deep Set, which explains its vastly different
resource usage." If we ever land near 47k LUT at N=64, we would be reproducing their *failure*.

---

## Accuracy, side by side

Their Fig. 2 per-class OvR AUCs (macro column is **our** arithmetic mean — the paper never
states a macro AUC), against our R14 ROC-test macro-OvR:

| N | Chang MHA | Chang Linformer | **Ours FP32** | **Ours W1A8 (binary)** |
|---|---|---|---|---|
| 8 | 0.8970 | 0.8970 | 0.8864 | 0.8712 |
| 16 | 0.9230 | 0.9256 | 0.9128 | 0.8956 |
| 32 | 0.9430 | 0.9484 | 0.9374 | 0.9052 |
| 64 | 0.9428 | 0.9532 | 0.9486 | 0.9121 |

**Read this carefully.** Our FP32 tracks their numbers closely and *exceeds* their MHA at N=64
(0.9486 vs 0.9428). The binary cost is 1.5–3.2 AUC points on top. So the model is competitive;
binarization is the price, which is exactly the quantity the thesis exists to measure.

**Caveats that must travel with this table:** the paper never says whether Fig. 2 is the float
or the quantized model, so the comparison arm is ambiguous. Same dataset (Zenodo 3602260), same
260k test split, same 5 classes, same OvR construction — the *metric* is the same object. The
*models* differ in depth, width, and quantization.

---

## Training recipe, side by side

| | Chang (`run_train.py`) | BNJetTag R14 |
|---|---|---|
| backend | JAX | TensorFlow/Keras |
| epochs | **7,000** | **101** |
| batch | **2,790** | 256 |
| LR | **3e-3**, cosine restarts every 500 epochs, no peak decay | **2e-5**, 1 warmup + linear decay |
| optimizer | Adam (defaults) | Adam (β₂ = 0.98), wd 0.01, clipvalue 1.0 |
| bitwidths | **learned** (HGQ kbi/kif, b0=7/f0=7, `wrap`) | **fixed**: 1-bit W, 8-bit A |
| β (EBOPs pressure) | open-loop `PieceWiseSchedule` 2e-8 → 3e-6 | n/a — no EBOPs term in the loss |
| selection | **Pareto front (val_acc ↑, ebops ↓)** | best val macro-OvR AUC |
| split | 558k train / 62k val / 260k test | 496k/124k train-val, 260k test |
| pT gate | `X *= X[...,:1] >= 2` — **zeroes low-pT constituents** | none |

Two of these are worth acting on. The **7,000 epochs vs our 101** is a 70× training-budget gap
— our binary-QAT instability at N ≥ 32 (seed variance ×75.8) may simply be under-training. And
the **pT gate is in their code but not their paper**, and not in our pipeline at all; it changes
the effective input distribution.

---

## Synthesis, side by side

| | Chang | BNJetTag |
|---|---|---|
| device | Xilinx **XCU250** (1.728M LUT, 4 SLR) | **VU13P** — same LUT count and fabric class |
| flow | **alkaid/da4ml native RTL** (hls4ml is now opt-in) | hls4ml 1.3.0 → Vitis HLS |
| numbers reported | **post-place-and-route** | **csynth estimate** |
| clock | default 1.0 ns in code; sibling paper closes 200 MHz / 5 ns | 2.5 ns target |
| latency | ns only; cycles recovered from `reg` count in the top-level Verilog | cycles measured, ns estimated |
| strategy | DA adder graphs throughout | `Strategy: Latency, RF=1` everywhere |

**They ship on da4ml by default.** The `distributed_arithmetic` path we found unused in our
installed hls4ml is not an exotic option for them — it is their production flow, and it is how
they reach 0 DSP with LUT counts in the hundreds of thousands.

---

## Answering "should we launch 64 too"

**We already did.** R14 swept N ∈ {8, 16, 32, 64}, 5 variants × 3 seeds = 60 runs, all verified.
We have accuracy at every N they report. The gap is not training — it is that **the only
silicon we have is N=8**, chosen because it was the only one that would complete synthesis.

And note their N=64 is not the clean win it looks like: the MHA row is disqualified by their own
text, and the Linformer row that does reach 79.8 % is a *different architecture* (rank-k
projected attention, k=4, h=1) which we have never implemented.

---

## What this comparison says to do

1. **Run place-and-route on n8.** Potentially a factor ~2.4 on the number that defines our whole
   fit problem, and we have never measured it. Cheapest high-value action available. (Needs the
   licence — see `docs/infrastructure/xup-licence-request.md`.)
2. ~~Turn on `distributed_arithmetic`.~~ **WITHDRAWN 2026-08-14 — already measured, and
   negative.** `experiment-log.md` 2026-07-22: DA emission gave **LUT 4.53M vs 3.91M** for
   plain Latency (the binary dense alone inflated 2.08M → 2.79M, **+34 %**) and **FF 7.10M vs
   1.92M (3.7×)**, bit-exact. Mechanism, recorded there: *"distributed arithmetic has nothing
   to share on dense ±1 matrices — CSD of ±1 is a single nonzero signed digit."* da4ml's
   benefit class is multi-digit few-bit constants — precisely Chang's 4–7-bit heterogeneous
   regime, and precisely not the binary extreme. It is also CMVM-only, so it could never
   touch our four act×act attention einsums.

   **The correct reading of "Chang ships da4ml" is the opposite of what this document
   originally said:** DA pays for *their* quantization scheme and not for ours. It is not a
   lever we failed to pull.
3. **Consider an EBOPs term in training.** This is the deepest difference. Adopting a budget
   target would change what our numbers mean — it makes resources a *constraint* rather than an
   observation — so it is a decision for Kai and Russell, not a defaulted-into change.
4. **Question the 101-epoch budget** against their 7,000, specifically as a candidate explanation
   for the N ≥ 32 binary instability.
5. **Architectural parity is untested.** Their d24 / 1-block / FFN32 is roughly 3–4× less compute
   than our d32 / 2-block / FFN64. Whether *our* binary core at *their* size still holds AUC is
   an unanswered and cheap question.

---

*Written 2026-08-13. Numbers from arXiv:2510.24784 Table 1 and Fig. 2 as transcribed in the
replication note, from `reference-code/HGQ2-examples/jsc150/`, and from `RESEARCH.md` §5–§6 and
`bnjettag/results/r14/`. No number here was recomputed for this document; each is quoted with
its source.*

---

## Change note — 2026-08-14

Corrected after an adversarial review of this document:

0. **The `distributed_arithmetic` recommendation is withdrawn** — measured negative on
   binary weights on 2026-07-22 (+34 % LUT, 3.7× FF). See item 2 of the action list.
1. **Mixed-N comparand.** "180–279k" spanned their N=32 and N=16 rows; the matched-N figure is
   MHA-8 = 246k.
2. **DSP mismatch.** The 3.18M point spends 4,133 DSP and was being compared against 0-DSP
   rows. The matched 0-DSP point is 4,376,222 LUT / 253.3 %, and it does **not** fit even
   deflated.
3. **"We have never tried" was wrong.** The folded/PF study is a fit attempt with a verified
   negative result, dated one day before the original version of this document.
4. **The POSTSYN anchor is post-*synthesis*, not post-route**, and is a lower bound measured on
   one layer class on a different die.
5. **Added:** no FP32/W8A8 R14 synthesis exists, so nothing here is attributable to
   binarization yet.
