# Dossier — da4ml (arXiv:2507.04535) + the resource bar of arXiv:2510.24784

**Written 2026-08-15 for job-alpha:** decide whether to move the 13 binary EinsumDense layers of
the R14 n8 model from `Strategy='Latency'` (3.18 M LUT @ RF=1, 184 % of VU13P) to
`Strategy='distributed_arithmetic'`, and establish the competitive resource bar.

**Sources.** Both papers were already read in full in this repo — nothing here is re-derived from
a fresh download. Prior notes: `docs/literature/hls4ml-fpga-triggers/2507.04535_da4ml.md` (PDF read
2026-07-24), `docs/literature/compiler-ir-hardware/2507.04535_da4ml_distributed_arithmetic_fpgas.md`,
`docs/literature/jet-tagging-transformers/2510.24784_replication-targets_hgq2-examples.md` (PDF read
2026-08-04). New primary evidence in this dossier comes from the **installed source** in
`.venv-hgq2/` (hls4ml 1.3.0, da4ml 0.5.2, hgq2 0.1.9) and `reference-code/HGQ2-examples`, cited by
file:line.

---

## One-line claim (each paper, in their terms)

- **da4ml** (Sun, Que, Loncar, Luk, Spiropulu; TRETS 19(1) Art. 13, DOI 10.1145/3777387;
  arXiv:2507.04535): a constant-matrix-vector-multiply (CMVM) optimizer that replaces a fixed
  weight matrix with a multiplier-free shared adder graph, removing **all DSPs** and cutting LUTs
  **"by up to a third"** on realistic heterogeneously-quantized networks.
- **2510.24784** (Laatu, Sun, et al., NeurIPS 2025 ML4PS): sub-microsecond transformer jet taggers
  on an XCU250 at **II = 1, 0 DSP, 202–279 k LUT, 44–140 ns**, trained to a shared ~350 k-EBOPs budget.

---

# TARGET 1 — da4ml: algorithm, cost model, constraints

## What they actually did

**Objective (§3–§4).** Minimise adder cost of `yᵀ = xᵀ M` as an adder graph under a delay
constraint `dc` (extra adder depth beyond `depth_min = ceil(log2 d_in)`). Cost of one node
`a ± (b<<s)` is `max(bw_a, bw_b+s) − min(0,s) + 1` full/half adders (**Eq. 1**).

**Two-stage hybrid search.**
1. *Graph decomposition* `M = M₁·M₂`: columns of `M` are vertices, edge weight =
   `min(#nonzero-CSD-digits(v_i ± v_j))`; an approximate **Prim MST** rooted at zero captures
   inter-column correlation.
2. *CSD digit reduction + greedy two-term CSE*: canonical-signed-digit recoding removes ~1/3 of
   nonzero digits on average, then the **most frequent** `a ± b<<s` subexpression is repeatedly
   implemented (frequency weighted by operand bit-overlap; they note choosing most-common rather
   than min-conflict costs "less than 2 %"). `O(N²)`, ~10⁵× faster than Hcmvm [ref 4].

**Exactness.** The transform is *exact* — no approximation of trained weights. Verified
independently on our own emission (pre-R14; see caveat below): GATE2 `max|Δ| = 0.0`.

**Pipelining model — two different answers, and this matters.**
- *hls4ml path (ours):* da4ml emits a **purely combinational** adder-tree C++ function; **Vitis**
  inserts the pipeline registers to meet the clock. hls4ml hardcodes `HWConfig(1, -1, -1)`
  (`hls4ml/backends/vivado/passes/distributed_arithmetic.py:129`), i.e. `latency_cutoff = -1` =
  **da4ml inserts no registers at all**.
- *Standalone / alkaid RTL path:* da4ml itself inserts a register between DAIS ops by a greedy
  local `latency_cutoff` (every adder @1 GHz, every ~5 adders @200 MHz). This is the register-heavy
  path — and the one the companion repo now uses (`latency_cutoff=2` in `jsc150/run_test.py`).

**Benchmarks.** Random 4-bit & 8-bit matrices; HGQ-trained JSC jet MLP (16-64-32-16-16-5), SVHN
LeNet, muon-tracking MLP, MLP-Mixer particle tagger. Target VU13P, Vitis/Vivado 2023.2, II = 1.
**Every benchmark weight matrix is HGQ heterogeneous multi-bit. None is binary or ternary.**

## The numbers that matter to us

| Benchmark | LUT reduction vs Latency | DSP | FF (DA vs Latency) | Source |
|---|---|---|---|---|
| JSC jet MLP | ~10 % | → 0 | 1,502 vs 1,497 (≈equal) | their Table 5 |
| SVHN LeNet | ~25 % | → 0 | 20,048 vs 27,853 (**DA lower**) | their Table 7 |
| Muon tracking MLP | ~10 % | → 0 | 5,547 vs 6,043 (**DA lower**) | their Table 8 |
| MLP-Mixer tagger | marginal | → 0 | — | their Table 9 |
| Standalone RTL @200 MHz | — | → 0 | 3,113 vs 1,502 (**3× FF**) | their Table 10 |

- **"Up to a third" appears in the Abstract and §2.2 and is the *upper* end, not the typical case.**
  The realistic-network tables cluster at ~10–25 %. Flag this if it is ever quoted at us.
- **There is no binary or ternary weight test anywhere in the paper.** The only extreme-low-bit
  statement is that for a network with **1-bit inputs** they *skip da4ml entirely* in favour of
  conditional-accumulation logic.
- **§4.3 states the failure mode in their own words:** on uncorrelated columns "the algorithm would
  usually produce trivial decomposition, where M₁ is a shuffled form of M and M₂ is a shuffled
  identity." A ±1 matrix has exactly **one** nonzero CSD digit per weight, so stage 2 has no digits
  to reduce and (empirically, on our matrices) no two-term subexpressions to share.
- **Metric caveat:** these are top-1 accuracy / MSE-resolution benchmarks on other datasets. **No
  number in this table is comparable to our 5-class macro-OvR ROC-test AUC**, and no LUT figure of
  theirs is comparable to ours (their stage is csynth for these tables; see Target 2 for the
  post-route mismatch). Nothing here may be placed beside one of our numbers.

## Expected LUT change on *our* binary matrices — prediction, not measurement

**Predicted: between 0 % and a LUT *increase*.** The mechanism argument is architecture-independent:
both da4ml wins (CSD digit reduction, pairwise two-term CSE) are null at ±1, and Vitis's Latency
path already emits the minimal sign-flip adder tree.

Two supporting data points, both **pre-R14 (`_attic` scope) and both on Dense, not EinsumDense** —
cite as context only, never as an R14 result, never into `RESEARCH.md`:
- `experiment-log.md` 2026-07-22 + its 2026-07-24 correction: 15 binary **Dense** layers, R8,
  16 feat / N=10, **da4ml 0.5.2** — dense LUT 2,457,312 → 2,786,772 = **+13.4 %** same-variant
  (whole-model +16 %); FF ×6.95 on the dense block. Bit-exact (`max|Δ| = 0.0`).
- `_attic/compiler-workstream/adder-graph/counting_results.json` (compiler workstream, per the
  workstream-separation rule): pairwise CSE on the real ±1 matrices saves 69 % of *adds* but is
  statistically identical to a random null (710 vs 705.6 ± 4.8) → generic birthday sharing, no
  learned structure to harvest.

**Why the prior negative does not settle the R14 question by itself.** It is a different layer type
on a different code path: the main DA pass explicitly **declines EinsumDense**
(`distributed_arithmetic.py:105-107`, `match` returns `False`), which is handled by a *separate*
pass (`:355-393`) that solves each sub-kernel and **accumulates** cost from 0.0. Different
decomposition granularity, different scale, different matrices. The mechanism predicts the same
sign; the magnitude must be measured.

## The cost model — usable pre-synthesis, but the unit is NOT LUTs

hls4ml stores da4ml's solved cost on the layer and **never reads it back**:
`node.attributes['da_kernel_cost'] = sol.cost` (`distributed_arithmetic.py:136` for Dense;
`:379` / `:390` for EinsumDense, summed over sub-kernels). It is therefore a **free per-layer
estimate available seconds after `convert_from_keras_model()`, with no Vitis and no mulder.**

**Unit, confirmed from installed da4ml 0.5.2 source** (`da4ml/cmvm/core/state_opr.py:70`):

```python
return float(ceil(n_accum / carry_size)), float(ceil(n_accum / adder_size))   # (latency, cost)
```

with `n_accum = k + i + f` (`:67`) and `HWConfig = (adder_size, carry_size, latency_cutoff)`
(`da4ml/trace/fixed_variable.py:25-28`). hls4ml passes `HWConfig(1, -1, -1)`, so `adder_size = 1`
and `carry_size → 65535`:

- **`sol.cost` = Σ over adder nodes of the accumulator bit-width = full-adder *bits*, not LUTs.**
- `sol.latency` = 1.0 per adder ⇒ **adder depth levels, not nanoseconds and not clock cycles.**

**Scope this claim precisely.** `CombLogic.cost` sums `op.cost` over *all* ops, and not every op is
an add — `fixed_variable.py:295` costs a table lookup as `2**max(b_in-5,0) * ceil(b_out/2)`
(LUT-flavoured) and `:327` costs a multiply as `min(cost0*b1, cost1*b0)` (bit-products). The
add-only reading is exactly right **for the DA CMVM path**, because the traced graph is
`inp @ kernel (+ bias)` and nothing else (`distributed_arithmetic.py:129-135`). If a table or an
act×act op ever enters the trace, `sol.cost` becomes a mixed-unit quantity.

Do not print `da_kernel_cost` as a LUT count. The nearest bridge we own is the **pre-R14
compiler-workstream** calibration `LUT = 0.923 × (naive bit-adds) + 3,412`, R² = 0.987
(`_attic/compiler-workstream/adder-graph/counting_summary.md`) — but it was fitted on the *Latency*
naive tree, so applying it to a DA graph is an extrapolation, and its own registered gate FAILED
(max residual 24.1 %), demoting it to **ranking and first-order sizing only**. The paper gives no
LUT-fidelity figure for `sol.cost`; all its resource claims are measured Vivado numbers.

## Constraints (all from installed hls4ml 1.3.0 source)

| Constraint | Evidence |
|---|---|
| **`reuse_factor` must be 1** — otherwise a hard exception | `:110-112` `raise Exception(f'Layer {name} has rf = {rf} != 1, but has strategy = DA.')` |
| Backends: **Vitis / Vivado** (+ OneAPI, separate pass) | `assert backend in ('vitis','vivado')` `:139`, `:376` |
| Layers: Dense, Conv1D, Conv2D (one pass); **EinsumDense on a dedicated pass** | `:102-107`, `:355-393` |
| `DACombinational` is **io_parallel only** | `:422-424` raises on io_stream |
| Dense/Conv under io_stream get a wrapper (supported) | `:146-148` |
| **Tunable knob: `DA_HARD_DC` env var, default 2**; solver `{'hard_dc': dc, 'search_all_decompose_dc': True}` | `:127-128`, `:384-385` |
| **II unchanged.** RF = 1 ⇒ II = 1 for the layer; DA swaps MAC for a combinational adder graph. Cycle latency is set by **Vitis** pipelining that graph's depth, not by da4ml. | `HWConfig(1,-1,-1)` ⇒ `latency_cutoff=-1` ⇒ no da4ml registers, `:129` |

**Version history that bites us.** `hls4ml-1.3.0.dist-info/METADATA:30` reads
`Requires-Dist: da4ml<0.6,>=0.5.2; extra == "da"`. **da4ml 0.6.0 is unreachable through hls4ml
1.3.0's `distributed_arithmetic` strategy.** 0.6.0 (13 Mar) reimplements the CMVM optimiser in
**C++ and drops numba** — which would have removed the numpy ≤ 2.4 cap we hit on 2026-07-20 — plus
bitwise trace ops, sorting, a plugin system, and an HLS project-layout reorg
(github.com/calad0i/da4ml/releases). Reaching 0.6.0 means the **standalone/alkaid path**, not
hls4ml — exactly the split the repro-chang env made (`da4ml 0.6.0, alkaid 0.7.1`, experiment-log
2026-08-04).

---

# TARGET 2 — arXiv:2510.24784 as the competitive bar

## Lead finding: most of the requested resource columns are not in the paper

The task asked for LUT, FF, DSP, BRAM, latency in ns **and cycles**, II, clock, device, and
synthesis stage. **The paper publishes five of those.** Verbatim absence list, from our 2026-08-04
full-PDF read: **FF / CLB registers — no. BRAM / URAM — no. CARRY8 — no. Latency in cycles — no.
Clock period targeted — no. Clock achieved / WNS — no. Synthesis stage — no. Per-model EBOPs — no
(only a shared 350 k training target, §3). d_model / n_layers / param count — no. Softmax — never
mentioned.**

## The bar — their Table 1, rows 1–8 (their own firmware; rows 9–20 are quoted prior work)

| Model | N | Acc. (%) | Latency (ns) | LUT (k) | II (clk) | DSP | FF/BRAM/cycles/clock |
|---|---|---|---|---|---|---|---|
| MHA | 8 | 66.3 | 104 | 246 | 1 | 0 | not published |
| MHA | 16 | 72.3 | 98 | 279 | 1 | 0 | not published |
| **MHA** | **32** | **77.0** | **83** | **180** | **1** | **0** | not published |
| MHA | 64 | 77.9 | 44 | 47 | 1 | 0 | **DISQUALIFIED — see below** |
| Linformer | 8 | 66.3 | 110 | 230 | 1 | 0 | not published |
| Linformer | 16 | 72.8 | 103 | 246 | 1 | 0 | not published |
| Linformer | 32 | 78.4 | 140 | 267 | 1 | 0 | not published |
| **Linformer** | **64** | **79.8** | **78** | **202** | **1** | **0** | not published |

Device: **Xilinx XCU250** (§3) — same 1,728,000-LUT, 4-SLR class as our VU13P.

**MHA-64 (47 k LUT) is not an attention result.** §3 verbatim: *"The attention block of the MHA
model with 64 input particles is consistently collapsing … turning it into a Deep Set which
explains its vastly different resource usage."* Never quote 47 k as the bar.

**Table 1 is iso-EBOPs, not a scaling study.** All rows share the 350 k-EBOPs target, so LUT is
approximately pinned and accuracy is the free variable (Fig. 1 caption concedes the N=64 accuracy
drop "is expected due to the fixed resource budget we enforced during training").

**Stage — post-route, but code-derived, not stated.** The paper says only "Vitis HLS and Vivado"
(§3). `gather_statistics.py` reads `output_<top>/reports/<top>_post_route_util.rpt` and
`<top>_post_route_timing.rpt` ⇒ **post-place-and-route**. **Our 3.18 M LUT is a csynth estimate.
These two stages are not comparable**; our own **pre-R14 compiler-workstream** single-layer anchor
had csynth over-estimating LUT by **2.29–2.51×**
(`_attic/compiler-workstream/adder-graph/e1/POSTSYN.md` — one layer, pre-R14, so treat it as an
order-of-magnitude bridge, not a correction factor to apply). Any sentence putting 3.18 M next to
202 k must carry both the stage caveat and the fact that they use 3 features/particle with learned
heterogeneous multi-bit weights while we use uniform ±1.

## Which flow — and it is our flow

§3 says "Vitis HLS and Vivado", so **Table 1 is the hls4ml `distributed_arithmetic` path**, not
alkaid. The repo's migration to native alkaid RTL is commit `93f1455`, *after* the paper. So the
flow is comparable to ours even though the stage is not.

Their settings, **verified by direct grep of the named files** (not second-hand):
`reference-code/HGQ2-examples/jsc150/run_test.py:49-53` — `solver_options={'hard_dc': 2}`,
`hw_config=HWConfig(1, -1, -1)`, `clock_uncertainty=0.0`, `clock_period` and `latency_cutoff` from
argparse (defaults 1.0 ns / 2); `:66-67` shows `--hls4ml` and `--hls4ml-da` are **opt-in flags**,
confirming alkaid is now the default path. `jsc150/test_utils.py:153` sets DA at **Model** level, not
per-layer: `hls_config = {'Model': {'Strategy': 'distributed_arithmetic', 'ReuseFactor': 1,
'Precision': 'fixed<-1,0>'}}`. Plus an undocumented `trace_minmax` calibration over train+val before
conversion. **Convergence worth noting: `hard_dc = 2` and `HWConfig(1,-1,-1)` are exactly what
hls4ml hardcodes/defaults** — their DA tuning is not a secret we are missing.

**But note the difference for us:** they can afford a *global* `Strategy: distributed_arithmetic`
because every layer in their model is CMVM-compatible or DA-declining. We cannot — see gotcha 1.

## The parts CMVM cannot touch — softmax and act×act attention (from code; the paper is silent)

- `hgq/layers/attn/mha.py`: Q/K/V/output projections are **`QEinsumDense`** (`:149`, `:168`,
  `:187`, `:285`) — constant-weight, DA-eligible. But `attention_scores = ops.einsum(...)` (`:521`)
  and `attention_output = ops.einsum(...)` (`:533`) are **raw activation×activation einsums** —
  **not DA-eligible by construction**, in their design as in ours. This is the structural reason DA
  cannot be a whole-model fix for an attention network.
- **The `1/√d_k` scale is folded into softmax, not implemented as a multiplier**:
  `input_scaler=self._inverse_sqrt_key_dim` (`mha.py:336`). Free trick, directly stealable.
- `hgq/layers/softmax.py` `QSoftmax`: implemented as **two table lookups plus an accumulate** — an
  `exp` table (`:49-53`; `stable=True` ⇒ `exp(−x·scaler)` after max-subtraction) and a reciprocal
  table `1/(x+eps)` (`:46-47`) — each with its own input/output quantizer
  (`exp_iq/exp_oq/inv_iq/inv_oq`, output presets `'table'`, `:55-58`).
  `allow_heterogeneous_table=False` by default (one shared table);
  `parallelization_factor=-1` ⇒ fully parallel. **No bit widths are fixed in the layer** — they are
  learned by HGQ, which is why the paper can report 0 DSP without stating any softmax width.
- `jsc150/model.py`: `xfm` = `QAffinedUnaryFunctionLUT('tanh')` (`:194`) → `QMultiHeadAttention(h, 16)`
  (`:195`); `xfmt` = `QLinformerAttentionT(h, 4, d)` (`:230`) with an all-`QDenseT` datapath —
  note `xfmt` is the **post-paper** LUT-transformer variant (HEAD `6cdc6e3`, 2026-07-02), *not* what
  rows 5–8 were synthesised from.

---

## What we can steal

1. **`da_kernel_cost` as a free pre-synthesis screen — but in two tiers of unequal validity.**
   Convert with `Strategy='distributed_arithmetic'` on the 13 binary EinsumDense layers, then read
   `node.attributes['da_kernel_cost']` per layer (if unpopulated straight after
   `convert_from_keras_model()`, call `.write()` — the codegen pass may sit in the writer flow).
   - **Tier A, valid immediately: `da_kernel_cost` vs `da_kernel_cost` across `DA_HARD_DC` values.**
     Same unit, same convention, same machinery — the dc-scan ranks DA solutions reliably.
   - **Tier B, needs a convention check first: `da_kernel_cost` vs the Latency-path naive bit-add
     count** from `_attic/compiler-workstream/analysis/adder_graph_study.py`. da4ml accumulates
     `k+i+f` per node under its own qinterval propagation (`state_opr.py:64-67`); our script counts
     bit-adds by its own rule. If one counts per-partial-sum width and the other final accumulator
     width, the ratio carries an invisible constant bias. **Verify the two conventions agree on one
     small layer, or report the ratio as convention-dependent.**
   - **Time it, don't assume.** da4ml 0.5.2 is the *numba* implementation (the C++ rewrite is 0.6.0,
     which is unreachable here) and hls4ml forces `search_all_decompose_dc: True`, which searches all
     dc values and multiplies the solve. Convert **one** EinsumDense layer, wall-clock it, then
     extrapolate to 13 before promising a runtime.
2. **Scan `DA_HARD_DC`.** `export DA_HARD_DC=<n>`; default 2. `dc = -1` is **legal and means
   unconstrained** — verified in `da4ml/cmvm/api.py:94-95` (`if hard_dc < 0: hard_dc = int(1e9)`),
   so a `{-1, 2, 4}` scan is safe. The paper's random-matrix study found unconstrained gave the
   lowest LUT; `dc = 2` is their chosen sweet spot. (Note `api.py:98`: `hard_dc >= 6` also switches
   the stage-2 method, so large values are not simply "more search".)
3. **Fold `1/√d_k` into the softmax `input_scaler`** rather than as a datapath multiply (mha.py:336).
4. **`gather_statistics.py` unmodified** against our Vivado projects — 130 lines that parse
   post-route util + timing into exactly the schema we lack (LUT logic/memory split, FF, CARRY8,
   RAMB18/36, URAM, WNS → `actual_period`, cycle latency from `reg` count in the top `.v`). This is
   the single cheapest way to make our numbers stage-comparable to theirs.
5. **Their two-objective `ParetoFront` selection** over (val_accuracy ↑, cost ↓) instead of best-val.
6. **The `_uq1` ablation** (`homogeneous_axis=(0,1)` vs `(0,)`) — the cost of preserving permutation
   invariance, i.e. of keeping per-token instances foldable. Unpublished, cheap, thesis-relevant.

## What threatens us

- **DSP = 0 is already theirs, and it is not binary-specific.** Every HGQ row in their Table 1 —
  including Deep Sets and MLP-Mixer, which have no attention — is 0 DSP **post-route**. Our DSP = 0
  story must be pitched on the *mechanism* (uniform ±1 ⇒ one adder-tree topology, identical foldable
  instances) and not on the outcome.
- **"First transformer for jet tagging on FPGA" is taken** (2510.24784 abstract, Oct 2025). Our claim
  has to be "first *binary-weight*" or the compiler mechanism.
- **Their smaller model reaches macro-OvR ≈ 0.897 (our arithmetic mean of their Fig. 2 per-class
  AUCs — they never state a macro AUC) at 230 k LUT post-route.** Same dataset, same 260 k test jets,
  same OvR construction — but 3 features/particle, N = 8. The stage mismatch explains ~2.3–2.5×, not
  the rest. This is a real competitive gap, not an artefact.
- **da4ml does *not* scoop the thesis, and DA is not our rescue.** Its premise vanishes at ±1. The
  rhetorical risk is a referee asking "did you just use da4ml wrong?" — the answer is the measured
  negative (pre-R14) + their own §4.3 trivial-decomposition clause + the total absence of any binary
  or ternary weight test in their work. What da4ml does *not* attempt — subset-sum / Four-Russians
  block precompute, the affine `2·Σ₊ − Σ_all` ±1 identity, cross-layer Wq/Wk/Wv fusion, token-axis
  folding — is precisely the ±1-native space, and that belongs to the compiler workstream (COMPILER.md),
  not to `RESEARCH.md`.
- **Correction to a prior claim.** `research-log.md` 2026-07-26 records "da4ml is closed-negative."
  That verdict rests on **Dense**-layer evidence at **da4ml 0.5.2** on an R8 model. It should not be
  inherited for R14 EinsumDense without the cheap re-check in "steal" item 1.

## How we'd cite them

> Distributed-arithmetic CMVM optimisation reduces LUTs by roughly 10–25 % on heterogeneously
> quantised networks by sharing signed-digit subexpressions [Sun et al., TRETS 19(1) 13,
> arXiv:2507.04535]; on binary ±1 matrices this premise degenerates, since each weight is already a
> single CSD digit. Sub-microsecond transformer jet taggers have been demonstrated post-place-and-route
> on an XCU250 at 78–140 ns, II = 1, zero DSPs and 202–279 k LUTs [Laatu et al., arXiv:2510.24784];
> that design buys device fit entirely on the precision axis at full spatial parallelism, which a
> uniform {−1,+1} weight constraint forecloses.

## Verdict

- **da4ml (2507.04535): essential** — it is the engine of the strategy we were about to enable, and
  it supplies both the free cost model and the documented reason to expect no win at ±1.
- **2510.24784: essential** as the competitive bar — with the hard caveat that it publishes only
  five resource columns, its stage is post-route (inferred from code) against our csynth, and its
  companion repo has drifted materially past it.

---

## Top 3 gotchas for our integration

1. **`rf != 1` is a hard exception, so DA cannot be set globally on our model.**
   `distributed_arithmetic.py:110-112` raises outright. Their `test_utils.py:153` sets DA at Model
   level with `ReuseFactor: 1` because *their* whole model tolerates it; our attention einsums have
   historically run at RF > 1 to hold DSPs down. **Use the per-layer strategy map** (the pattern
   already exercised on 2026-07-20): DA + RF=1 on the 13 binary EinsumDense layers only, attention
   act×act einsums left on Latency. A global setting will either raise or silently force RF=1
   everywhere and blow up the DSP/LUT budget.
2. **Version pin + toolchain trap.** hls4ml 1.3.0 requires `da4ml<0.6` (`METADATA:30`), so the DA
   strategy runs the **0.5.2 numba** implementation — the same one whose numba dependency capped us
   at numpy ≤ 2.4 on 2026-07-20 and forced a venv downgrade. The C++ rewrite that removes numba is
   0.6.0, reachable only via the standalone/alkaid path, which is *not* the hls4ml flow. Budget the
   solve time (`search_all_decompose_dc: True` searches all dc values) and re-check the numpy pin
   before converting.
3. **The Amdahl bound: DA can only ever touch the CMVM fraction, and `da_kernel_cost` is adder-bits.**
   The act×act einsums (`mha.py:521`, `:533`) and the glue/softmax are **untouchable by construction**
   — no constant operand exists to fold — so they set a floor on any DA-based fit no matter how well
   the CMVM solve goes. **We do not have an R14 n8 per-layer LUT census, and this dossier does not
   state the 13 layers' shapes; both are needed to size the bound and are the next measurement.**
   Separately, never let `da_kernel_cost` be reported as a LUT figure (it is adder-bits) or its
   `latency` as ns/cycles (it is adder depth levels).

## Recommendation for the implementation decision

Do **not** launch a mulder DA synthesis first. In order:
1. Convert **one** binary EinsumDense layer with DA, wall-clock the solve, confirm
   `da_kernel_cost` is populated (call `.write()` if not).
2. Check the adder-bit **convention** against `adder_graph_study.py` on that same layer (Tier B above).
3. Scan `DA_HARD_DC ∈ {-1, 2, 4}` across all 13 layers (Tier A — this ranking is valid regardless).
4. Take the R14 n8 per-layer LUT census to fix the Amdahl bound.

Only if DA adder-bits fall materially below the Latency naive-tree count **and** the untouchable
remainder leaves room under 1,728,000 LUT is a mulder synthesis justified. The mechanism argument
and the pre-R14 Dense measurement both predict it will not.
