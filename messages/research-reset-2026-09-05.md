# Where the research stands, and what a restart would change — 2026-09-05

**Status:** frozen, dated assessment written the day after FastML 2026. Nothing in it is a new
measurement; every number is quoted from `RESEARCH.md` §5–§6 or the stores named in its §7, and
every external fact carries its source in the research log entry of the same date. It ends with a
menu of arms, not decisions — the decisions are Kai's and go to `.claude/memory/decisions.md`.

---

## 1. Where we stand (the record, in five lines)

1. **Accuracy (Round 14, `(N,3)` inputs, ROC-test macro-OvR AUC, n = 260,000, 3 seeds).** At
   N = 8 the binary W1A8 network reaches 0.8712 ± 0.0016 against FP32 0.8864 ± 0.0005 and W8A8
   0.8862 ± 0.0009; the binary deficit is resolved at every N and grows from ≈0.015 (N ≤ 16) to
   ≈0.035 (N ≥ 32), where binary QAT also becomes seed-unstable (§5).
2. **The zero-DSP claim is complete at the netlist.** The n8 W1A8 model synthesizes to 0 DSP at
   C-synthesis *and* at Vivado synthesis once the β affines and softmax are bound to fabric
   solution-wide; scoping the binding hands 4,096 attention products back to DSP48E2s (§6.4).
3. **One fitting operating point exists.** The retrained 4-bit-softmax-grid arm (AUC
   0.8701 ± 0.0020) folded to II = 48 lands at **1,689,320 CLB LUT = 97.8 % of the VU13P at a DSP
   demand of 0**, meets a 5 ns clock pre-route (WNS +0.647 ns; 240 ns/jet, 1.67 µs latency), and
   fails 2.5 ns. All of this is out-of-context on `xczu7ev`, pre-route, with a 2.2 % margin (§6.3).
4. **The baselines do not fit.** W8A8 at the same architecture: 2,525,842 CLB LUT (146.2 %) and a
   DSP demand of 5,550. The FP32-trained network realized on a 16-bit fixed-point datapath:
   7.2 M csynth LUT and 140,130 DSP (1,140 %), and its Vivado run died on BRAM from an hls4ml
   softmax-table artefact; literal float silicon does not exist in this flow (§6.5).
5. **Open on the record.** N ≥ 16 is not synthesized whole-model; the 2.5 ns clock is unmet by
   every zero-DSP build; no ternary or HGQ-heterogeneous arm exists, and FastML 2026 put both in
   the room (Sloot: ternary beats binary on every axis; HGQ dominates the Pareto at 0 DSP).

**The uncommitted tree.** Everything since commit `8a56106` is the FP32-baseline campaign
(2026-09-02/03) plus poster material: modified `RESEARCH.md`, the three memory logs,
`bnhgq2/convert.py` (+`--weight-width`), `documentation.md`, `INDEX.md`, two poster builders and
the poster speaker notes; untracked `convert_fp32.py`, `weight_grid_audit.py`, three plot builders,
the `runs/40103802/` store, the Sloot literature note, the FP32 design memo, two speeches, the study
guide, and two A0 portrait posters. Debris to drop before any commit: the two
`*.pptx.inspect.ndjson` files and `docs/reports/build_a0_portrait_readable.mjs`. A sensible split is
four commits — FP32 silicon baseline (code + store + memo + RESEARCH.md + logs), Sloot note +
INDEX, poster/speech material, and this memo — but that is Kai's call; nothing was committed today.

---

## 2. Why the LUT count is in the millions

### 2.1 The arithmetic, from the model definition

The n8 network (d_model 32, 4 heads, 2 layers, FFN 64, 8 tokens) performs, per jet:

| term | count |
| --- | --- |
| binary-weight multiply–accumulates (input_proj, Wq/Wk/Wv/Wo ×2, fc1/fc2 ×2, head) | **133,024** |
| activation × activation MACs (QKᵀ and attn·V, both blocks) | 8,192 |

Everything is unrolled in space (`io_parallel`); the folded point reuses hardware 48× in time
but still instantiates every weight. In LUT arithmetic a weight of ±1 costs exactly one add or
subtract of the activation's width, every time it is used: **a {−1,+1} weight has no zero state, so
nothing is ever skipped.** With 8-bit activations that is an 8-bit-and-growing adder per MAC,
which is the ≈8–12 LUT per MAC observed below.

### 2.2 Where the LUTs are (C-synthesis attribution of the fitting build — csynth, not netlist)

`results/synthesis/runs/ba72a91a/w1a8-s3-r15gamma-sm4i0-pf1scoped/csynth_pf1scoped/myproject_csynth.rpt`,
parsed with `code/hgq2/parse_families.py`; total 3,837,485 csynth LUT (fit-ladder row 7). The
Vivado run stored for this build has no hierarchical utilization report, so **no per-family netlist
number exists**; the post-opt total is 1,689,320 (ratio 0.44 to csynth, never applied per family).

| family | instances | csynth LUT | share | what it is |
| --- | ---: | ---: | ---: | --- |
| `einsum_dense` (the 13 binary matmuls) | 13 | 1,060,057 | 27.6 % | ±1 adder trees; ≈8.0 LUT per binary MAC at II = 48 (≈12.3 at RF = 1: 1,630,567) |
| `normalize` (the 15 β-restore affines, fabric-bound) | 15 | 1,001,839 | 26.1 % | constant multiplies + bias adds + requantization, in LUTs because the DSP binding is off |
| `einsum` act × act (QKᵀ, attn·V) | 4 | 525,408 | 13.7 % | real 8 × 8 and 8 × 4 multipliers, ≈64 LUT per MAC |
| `thresholded_relu` | 3 | 158,919 | 4.1 % | hls4ml parser fall-through (a ~49-bit compare); Vitis constant-propagates it, so the fix measured Δ = 0 |
| softmax bodies + loops | 4 | 94,934 | 2.5 % | the two rolled `softmax_stable` processes |
| dataflow processes, adds, and/or glue, head, pooling | — | 286,899 | 7.5 % | pf1 dataflow schedule |
| top-level own logic (FIFOs, interconnect, expressions) | 1 | 709,429 | 18.5 % | the ≈+585 k glue that cancels folding's module savings (§6.2) |

Three readings follow. **(a)** The binary matmuls are 28 % of the design; deleting them outright would still leave
2.78 M csynth LUT — the non-matmul part alone is ≈72 % of the fitting design, so no lever
confined to the weight layers can move the fit question by more than a quarter.
**(b)** The β-restore affines cost as much as the matmuls they follow. That is structural to a
norm-free transformer — nothing absorbs β, so it is restored in-stream 15 times — and it is the
single family whose cost is set by a *training-recipe choice* (β is a free real per tensor) rather
than by physics. **(c)** The act × act attention is the only part that scales as N², and it is
untouched by weight binarization.

### 2.3 Per-MAC comparison to the FastML 2026 benchmark (stage-matched ratios, not a table)

Two scopes, each labeled, because they answer different questions. **Matmul family only:** the
13 binary `einsum_dense` modules cost ≈8.0 csynth LUT per binary MAC at II = 48 and ≈12.3 at
RF = 1 — the price of a ±1 weight is one adder of activation width. **Whole model:** the fitting
build is 3,837,485 csynth LUT over 141,216 MACs (133,024 binary + 8,192 act × act) ≈ 27 LUT per
MAC (RF = 1 fabric ≈ 31; RF = 1 with its 4,133 DSPs ≈ 22.5). Sloot's BitNet-binary MLP
(64-32-32 on 16 features, 4,096 MACs) reports 87.3 k csynth LUT on the same part and flow — ≈21
per MAC, whole model. So at whole-model scope we are comparable to slightly worse per MAC, and
the whole of that gap is the non-matmul half; we are 34× larger in MAC count. The millions are
therefore not a pipeline defect (every conversion-level lever was measured and closed, §6.4) —
they are the product of a dense, unpruned 133 k-MAC network realized in adders, carrying a
transformer's β-restore, attention and dataflow overhead that an MLP does not have.

### 2.4 What would actually shorten it (levers ranked by the share they touch)

| lever | touches | mechanism | what it needs |
| --- | ---: | --- | --- |
| **Sparsity** — a zero state in the weights (ternary, or binary with pruning) | 27.6 % | a zero weight instantiates nothing in an unrolled matmul; HGQ's converged per-weight widths peak at 0 and 1 bit, i.e. most weights pruned — this is why Sloot's ternary is cheaper than his binary (`else 0`) | a QAT arm; export unchanged |
| **β as a power of two, or folded into the next grid** | 26.1 % | shift instead of constant multiply; or absorb β into the following activation quantizer's step | training-recipe change + export change; Q/K β already folds into the softmax scale |
| **Narrower activations (A4)** once β is absorbed | 27.6 % + 13.7 % | adder width halves; measured −57 % on the scores einsum at 4 × 4 | the A6/A4 arms exist but fail GATE1 *because* β is restored through a narrow grid (§6.5) |
| **Smaller model** (d_model 16, 1 layer, 2 heads) | all matmul terms | MAC count is the multiplier on everything | a training sweep; the AUC cost is the unknown |
| **RTL emission (Alkaid) instead of Vitis HLS** | glue 18.5 %, adders | ternary-adder fusion (−20–30 % on adder trees, RTL-only), affine-arithmetic width narrowing, no dataflow FIFOs, no csynth 2× over-estimate | the hls4ml → Alkaid bridge; Vivado still needed for OOC numbers |

Not a lever: da4ml / distributed arithmetic on ±1 matrices (measured +21.9 % LUT; there are no
shared sub-expressions in a binary column, `docs/literature/…/2507.04535_da4ml.md`); softmax table
tricks (the tables live in BRAM); approximate multipliers (no hls4ml path, untrained error).

---

## 3. How our stack differs from HGQ and from LUT-aware training

**What we run.** HGQ2's layer library with every quantizer *frozen*: weights pinned to 1 bit
(`kbi`, `trainable=False`, `heterogeneous_axis=()` = one width per tensor) and binarized in the
forward pass by the BitNet absmean straight-through estimator; activations static 8/6/4-bit
per-tensor grids, MSE-calibrated, with a trainable scale; EBOPs traced for reporting but with
`beta0 = 0`, i.e. **no resource pressure in the loss**. Export is bit-exact through hls4ml 1.3.0's
HGQ2 front end (`bnhgq2/build.py`, `qat.py`).

**What HGQ is** (Sun, FastML 2026 tutorial; HGQ2 paper, FPGA'26). Every weight *and* every
activation carries its own trainable bitwidth; the EBOPs surrogate (Σ bits_w × bits_a over all
operations) is added to the loss with a scheduled β, so the optimizer prunes (0 bits), snaps to
powers of two (1 bit), and keeps width only where the loss demands it. The resulting weight
histogram "is usually very sparse and peaked at 0/1 bit". Bit-exactness is enforced by construction
(quantize at layer inputs), da4ml then turns each constant matrix into a shared adder graph. Model
coverage now includes MHA and Linformer attention (table-lookup or online softmax), RNN/GRU/SNN, and
the LUT-Dense/LUT-Conv layers of HGQ-LUT.

**What "LUT-aware training" means in 2026.** HGQ-LUT (arXiv:2604.22293, same group, same VU13P,
same jet datasets) relaxes each neuron into a small fan-in function trained as a tiny MLP and
compiled to physical K-LUTs, with the LUT count as a differentiable surrogate, at ordinary GPU
training speed (≈200× faster than NeuraLUT-Assemble). On the 64-particle × 16-feature jet task a
LUT-native GNN lands at 39,765 LUT / 0 DSP versus 244,515 for plain HGQ, at a 1.4-point accuracy
cost; on the 16-feature task HGQ-LUT is 5,667 LUT at 9 ns. The wider field (FPGN, DLGN/LUTN,
DWN, NeuraLUT-Assemble) is converging on the same idea — learn the LUT contents and the wiring —
and is still MNIST-class outside the Caltech line. **None of it supports transformers or attention
yet** (HGQ-LUT names transformers as future work), and none of it studies binary weights.

**The difference that matters.** Both stacks reach 0 DSP. Theirs gets there by *removing
operations* (pruning to 0 bits) and shrinking the survivors; ours gets there by making every
operation cheap (an adder) while keeping all of them. At the model sizes where W8A8 still fits —
Sloot's MLP, the HGQ-LUT benchmarks — that makes binary strictly dominated. Our counter has always
been regime: at our architecture W8A8 demands 146 % of the part and 5,550 DSPs, so *something* must
give. The honest restatement of the thesis after FastML is: **binary weights are one way to delete
the DSP demand of a transformer tagger; the open question is whether a dense binary core can ever
beat a sparse heterogeneous one on LUTs, or whether the right design is binary-with-a-zero-state
(ternary) under HGQ-style width pressure.** The three arms in §6 are the experiments that settle
it. A further, cheaper observation: the code to run the never-turned knob already exists —
`qat.py` carries `act_calib: "free"` (trainable, MonoL1-regularized activation widths) and the
`beta0` EBOPs term from Round 13; only a config and a run are missing.

---

## 4. Licensing: VU13P, Vivado, and what changed since the 2026-08-23 decision

**Standing decision (2026-08-23, mentor via Kai).** The licence request was retired; the flow of
record is out-of-context `synth_design` + `opt_design` on the licensed `xczu7ev`, percentages
against the VU13P's 1,728,000 LUTs, no place-and-route. This memo does not reverse that; it lists
what has changed so the call can be remade with current facts.

**What the small part cannot answer.** The fitting margin is 2.2 % pre-route on a different die;
place-and-route is impossible by construction (the zero-DSP netlists exceed `xczu7ev`'s 230,400 LUTs
by 7.4–9.2×); the 5 ns timing closure is pre-route; and a referee who has read arXiv:2510.24784
(post-P&R numbers on the real part) will ask. The FastML room did.

**AMD's 2026.1 licence model (in force since June 2026).** Vivado moved to five tiers. From the
third-party summaries available (AMD's own pages timed out twice today — verify against AMD's
device table before quoting): **Basic** is free and covers 7-series, Spartan/Artix UltraScale+,
selected Zynq UltraScale+ MPSoCs, selected Kintex and Kria; **Core**
(≈$1,200–1,800 per year) adds RFSoC *and Virtex UltraScale / UltraScale+*, so **the VU13P starts at
Core**; Pro adds Versal; Enterprise (perpetual, ≈$4.4–5.5 k) and Gold are unchanged. Linux support
was restored to Basic after the May backlash. **The AMD University Program is explicitly unchanged**
— the XUP donation route drafted in `docs/infrastructure/xup-licence-request.md` (2026-07-26, never
sent) is still open and still free.

**Three routes, in order of cost.** (1) Send the XUP request as drafted (free; weeks; a donated
licence is usually device-complete). (2) Ask the UCSD CMS Level-1 group how they build their
correlator firmware — CMS trigger firmware for the VU13P is built somewhere under a licence that
covers it, and that is a question for the group, not a fact this memo has. (3) A Core subscription
at ≈$1.2–1.8 k/year. Two constraints on all three: mulder runs Vivado 2023.2 and hls4ml 1.3.0 lists
Vitis HLS 2022.2–2024.1 as supported ("> 2024.1 less tested"), so a 2026.x licence may need a
second Vivado install kept apart from the HLS flow; and a VU13P run of the fitting netlist is a
multi-hour, multi-tens-of-GB job — the FP32 OOC took 3 h 44 m to fail — so it should be planned as a
single pre-registered run with LUT, DSP *and* BRAM gates, per the 2026-09-03 correction.

---

## 5. hls4ml: what is changing, and where we sit

From the hls4ml developers' forum at FastML (2026-09-04) and the open pull requests:

- **1.3.0 (March 2026) is the current release; we are on it.** Vitis HLS 2022.2–2024.1 supported.
- **1.4.0 (in preparation)** adds backends (Coyote accelerator, Google XLS vendor-agnostic
  (System)Verilog, possibly VitisUnified), SNN support, PQuantML and QKeras-v3 interfaces, sparse
  CNNs, and — the item that touches us — a **"consolidation of softmax fixes"** blocking the
  release: PRs 1476 (types and overflows in stable softmax), 1428 (softmax bit-width inference),
  1494 (softmax update) and **1531 (use HGQ's *trained* softmax lookup tables in the generated
  HLS)**. Our two softmax findings — the table sized as 2^width(`softmax_inp_norm_t`) that blew the
  FP32 BRAM, and the 10-bit softmax output that never tracked `act_bits` — sit exactly in that
  code, so the 1.4.0 softmax may change our emitted firmware and must be re-gated (GATE2 bit-exact)
  before any number is compared across versions.
- **Retirements:** the Quartus removal PR is ready for merge; oneAPI becomes Altera HLS; and the stated medium-term
  plan is to **drop the Vivado HLS backend and Keras 2 / QKeras 2 parsing**. We are Keras 3 + HGQ2 +
  Vitis on every path, so we are on the surviving side; the 2510.24784 replication material and
  anything QKeras-era is in `_attic/` and stays there.
- **Policy:** AI-authored contributions are allowed with full human review and human-only
  attribution; a **90-day stale-issue auto-close** is about to be switched on. Of our three
  verified upstream defects, **one is already fixed on `main`**: PR #1534 (merged 2026-08-28,
  "Keras frontends: stop silently misparsing unsupported layer configurations") rewrote the ReLU
  branch of `keras_v3/core.py` so a plain `ReLU()` now parses as `Activation/relu` — the
  ThresholdedReLU fall-through is gone in 1.4.0, which means the `thresholded_relu` family
  (158,919 csynth LUT here; Δ = 0 after Vitis constant propagation, §6.4) will not appear in
  firmware emitted by the next release, and 1.3.0 and `main` no longer emit the same netlist for
  our graph. The other two — the HGQ2 front end rejecting `DummyQuantizer`
  (`_base.py::extract_fixed_quantizer_config`) and the softmax table sized by
  `softmax_inp_norm_t` width — are not on the tracker (searched today) and need filing with repros
  while the softmax consolidation is still open.
- **Direction:** the coordinators' own list for FastML 2027 includes "LUT-based networks" and
  "reusable processing units for transformers", and the Caltech line (HGQ2 → da4ml → **Alkaid**, a
  numpy-traced compiler emitting Verilog/VHDL with polyhedral scheduling, an hls4ml bridge, and
  RTL-only optimizations such as ternary-adder fusion) is positioned as the next layer beneath or
  beside hls4ml. Its "1-bit LUT packing" is for 1-bit *inputs*, not 1-bit weights.

---

## 6. The restart: a menu of arms

Each arm names its cost and the result that would change the thesis statement. None is launched.

| # | arm | cost | what it settles |
| --- | --- | --- | --- |
| A | **Ternary `{−1,0,+1}` at n8, same recipe, 3 seeds → export → csynth → OOC** (comparison baseline, as the standing decision allows) | 3 GPU runs, 1 synthesis chain | whether a zero state alone recovers the LUT gap and the AUC deficit; if ternary fits with margin and higher AUC, the thesis becomes "1-bit-family weights", not "binary" |
| B | **Binary weights + HGQ's trainable per-element activation widths with EBOPs pressure** (`act_calib: free`, `beta0 > 0` — code exists) | config + 3 runs | the never-measured intersection: does width pressure on activations shrink the adders (≈27 % + 14 % of LUT) without breaking binary QAT |
| C | **β constrained to powers of two (STE on log₂ absmean) so the 15 affines become shifts** | recipe change, 3 runs, 1 export | removes most of the 26 % affine family and unblocks D; the AUC cost of quantizing β is the unknown |
| D | **A4 revisited after C** | 3 runs + synthesis | the activation ladder with β no longer restored through the narrow grid — the fidelity failure of §6.5 was that mechanism |
| E | **Model-size sweep (d_model 16, 1 layer, 2 heads) at n8/n16** | 6–12 runs, no synthesis until one wins | whether a smaller dense binary core holds AUC; MAC count multiplies every family |
| F | **Alkaid RTL emission of the fitting article via the hls4ml bridge, same OOC part** | days of engineering, no training | whether RTL-only optimizations and the absence of dataflow glue move the 97.8 % point, measured, not projected |
| G | **Licence: send the XUP request (drafted) and ask the L1 group; plan one pre-registered VU13P OOC + P&R of the fitting build** | ≈0 to $1.8 k/yr; one multi-hour run | the real-part number and a post-route timing statement — the two things the record cannot currently say |
| H | **File the two remaining hls4ml defects upstream (DummyQuantizer, softmax table sizing); pin 1.3.0 until the 1.4.0 ReLU and softmax changes are re-gated** | hours | protects the bit-exact contract across the coming release |

The cheapest decisive pair is **A + C**: together they test the two framework-level explanations
of the LUT count (no zero state; free real β) with six training runs and two synthesis chains,
and both are consistent with the binary thesis rather than a replacement of it. B is the arm that
answers Sloot's "we are not HGQ + binary" objection directly. G is the only item whose absence a
referee can name without reading the paper.
