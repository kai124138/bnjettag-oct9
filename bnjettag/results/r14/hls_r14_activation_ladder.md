# R14 n8 activation ladder in silicon — W1A8 / W1A6 / W1A4

**2026-08-14. NEW MEASUREMENTS.** Whole-model Vitis HLS 2023.2 C-synthesis on mulder, part
`xcvu13p-flga2577-2-e`, target 2.5 ns, `io_parallel`, `Strategy: Latency`, **RF=1**. Model
`r14-l1x3-n8`, **seed 3 for all three arms** (fixed deliberately so activation bits are the
only variable). Export v5, β encoding fx8.

These are **C-synthesis estimates, pre-place-and-route.** They are not post-route numbers and
must never be compared directly against post-route figures from other groups.

> **Fidelity caveat, load-bearing — read before quoting any of this.** The W1A6 and W1A4
> exports **fail GATE1**. Resource and latency numbers below describe the exported graph
> faithfully; they do **not** carry an accuracy claim, because the exported graph is
> measurably not the trained network. See §3.

---

## 1. The measured table

| metric | W1A8 (fx8) | **W1A6 (new)** | **W1A4 (new)** | W1A8 fabric-mul | VU13P |
|---|---|---|---|---|---|
| LUT | 3,178,720 (184.0 %) | **2,922,005 (169.1 %)** | **2,828,076 (163.7 %)** | 4,376,222 (253.3 %) | 1,728,000 |
| FF | 1,704,976 | **1,521,470** | **1,080,158** | 1,444,585 | 3,456,000 |
| **DSP** | 4,133 | **4,389** | **512** | 0 | 12,288 |
| BRAM_18K | 512 | **512** | **512** | 512 | 5,376 |
| URAM | 0 | 0 | 0 | 0 | 1,280 |
| latency (cycles) | 164 | **167** | **145** | 146 | — |
| II | 1 | **1** | **1** | 1 | — |
| est. clock | 1.825 ns | **1.825 ns** | **1.825 ns** | 2.287 ns | — |

Deltas vs the W1A8 fx8 reference:

| | LUT | DSP | cycles |
|---|---|---|---|
| W1A6 | **−8.1 %** | **+256** | **+3** |
| W1A4 | **−11.0 %** | **−3,621** | **−19** |

Synthesis cost: W1A4 **4 h 57 m**, peak 42.3 GB. W1A6 completed in the following slot. Both
run serialized on an otherwise idle box; neither came close to the 125 GB wall that killed
n16 (112.5 GB).

## 2. The finding: at A4 the β affines leave the DSPs

Per-class attribution from each run's top-level Utilization/Instance table:

| class | W1A8 LUT / DSP | W1A6 LUT / DSP | W1A4 LUT / DSP |
|---|---|---|---|
| `einsum_dense` ×13 (binary matmuls) | 1,630,567 / **0** | 1,496,330 / **0** | 1,345,481 / **0** |
| `einsum` ×4 (act×act attention) | 715,776 / **0** | 617,472 / **0** | 541,184 / **0** |
| **`normalize` ×15 (β affines)** | 258,364 / **3,621** | 268,548 / **3,877** | **437,716 / 0** |
| `softmax_stable` ×64 | 179,200 / **512** | 163,840 / **512** | 119,808 / **512** |
| `thresholded_relu` ×3 | 164,160 / 0 | 152,576 / 0 | 141,344 / 0 |

**At W1A4, every DSP in the design is softmax.** All 15 β affines bound to LUT fabric instead.

The mechanism was predicted before this run: Vitis binds a constant multiply to DSP48 unless
the constant is cheap in canonical-signed-digit form, and the A8 design contained its own
control — `config38` (β = 0.140625, **2 CSD terms**) was the *only* `normalize` at 0 DSP,
while its 3-term neighbours all took 256 DSP each. Narrowing the activations narrows the β
container (`ap_ufixed<4,-2>` and similar), pushing every affine below the binding threshold.

**The trade is favourable.** A4's affines cost 437,716 LUT at 0 DSP against A6's 268,548 LUT
at 3,877 DSP: **+169,168 LUT to shed 3,877 DSP ≈ 44 LUT per DSP.** Compare the brute-force
route on the A8 design — `config_op mul -impl fabric` — which cost **216 LUT per removed
DSP** and +1,197,502 LUT overall. Reaching low DSP through activation precision is roughly
**5× cheaper in LUT** than forcing it through a synthesis flag.

## 3. Export fidelity degrades with activation precision — GATE1

Measured on 4,096 real jets, per article:

| arm | csd2 | csd3 | fx8 (shipped) | **exact (ceiling)** | argmax (fx8) | GATE1 (bar 0.997) |
|---|---|---|---|---|---|---|
| W1A8 | 0.98385 | 0.99692 | 0.99882 | **0.99926** | 0.9800 | **PASS** |
| W1A6 | 0.94020 | 0.99548 | 0.99518 | **0.99623** | 0.9543 | **FAIL** (marginal) |
| W1A4 | 0.97434 | 0.98267 | 0.98340 | **0.98343** | 0.9153 | **FAIL** |

Read the **exact** column: that is β carried with *no encoding loss whatsoever*, and it still
falls 0.99926 → 0.99623 → 0.98343. **This is not a β-encoding problem** — a better encoding
cannot recover it. The norm-free export itself loses fidelity as the activation grid narrows,
because β is reinstated *through* that grid at each carry site.

At W1A4, argmax agreement is 0.9153 — roughly **8 % of jets are classified differently** by
the exported graph than by the trained network.

Both arms proceeded to synthesis under the pre-registered rule (decisions.md 2026-08-04):
*"If no rung passes GATE1, ship the best available with GATE1 measured + documented per
article, and no headline fidelity claim."*

**GATE2 (hls4ml C-sim vs export) is bit-exact for both** — corr = 1.0, max|Δ| = 0.0, n = 128.
The hls4ml conversion is faithful; the *export* is where fidelity is lost.

One anomaly: for W1A6, **csd3 (0.99548) beats fx8 (0.99518)**, so the cheapest-passing-rung
rule would select a different, cheaper encoding here than for A8.

## 4. Does anything fit?

Applying the repo's own csynth-overestimate anchor (2.29–2.51×, `_attic/compiler-workstream/adder-graph/e1/POSTSYN.md`).
**That anchor is csynth → post-*synthesis*, not post-route, measured on four arms of one layer
class on a different die. It is a lower bound on the true deflation and its transfer to this
design class is unverified.** No place-and-route has ever been run on this project.

| point | csynth | deflated | verdict |
|---|---|---|---|
| W1A8 fx8 (4,133 DSP) | 184.0 % | 73–80 % | fits, but not DSP-free |
| W1A8 fabric (0 DSP) | 253.3 % | 101–111 % | **does not fit** |
| **W1A6 (4,389 DSP)** | 169.1 % | **67–74 %** | fits, but not DSP-free |
| **W1A4 (512 DSP)** | 163.7 % | **65–71 %** | **fits, and nearly DSP-free** |

**Projected W1A4 at true 0 DSP** *(estimate)*: only softmax's 512 DSP remain; costing them at
the 369 LUT/DSP measured for softmax on the A8 fabric point gives ≈ 3,017,004 LUT = 174.6 %
csynth, deflating to **70–76 %**. So a genuinely 0-DSP W1A4 n8 still projects to fit — and
unlike the A8 fabric route it does not require a +1.2M LUT penalty.

## 5. What this supports, and what it does not

**Supported by measurement:**
- Activation precision, not synthesis flags, is the effective lever on DSP for this design.
  A8 → A4 removes 3,621 DSPs at 44 LUT each; the flag route costs 216 LUT each.
- The binary matmuls and all four act×act attention einsums are **0 DSP at every activation
  precision** — the core thesis claim holds across the ladder.
- W1A4 is smaller *and* faster than W1A8: −11.0 % LUT, −19 cycles, same II=1.
- Export fidelity degrades monotonically with activation precision, and the degradation is
  intrinsic to the norm-free β restoration rather than to β encoding.

**Not supported, and must not be claimed:**
- **No accuracy claim attaches to the W1A6 or W1A4 silicon.** Both exports fail GATE1.
- **Nothing here fits a device yet.** Every "fits" verdict depends on an unverified
  deflation factor. Only place-and-route settles it.
- **Nothing is attributable to binarization.** There is still no FP32 or W8A8 synthesis of
  this architecture at any N.
- The 0-DSP W1A4 point is a **projection**, not a measurement — the fabric variant was not run.

## 6. Next

1. **Fix the norm-free export at low activation precision.** This is now the blocking item:
   a fitting design we cannot vouch for is not a result. The β-through-narrow-grid path is
   the suspect.
2. **Synthesize W1A4 with `-impl fabric`** to measure, rather than project, the true 0-DSP
   point. Cheap — the design completes in ~5 h.
3. **Table-based softmax** would remove the last 512 DSP *and* ~120k LUT, without the fabric
   penalty.
4. **W8A8 n8** remains the missing baseline, though at ~5.3× the EBOPs it may exceed the
   memory wall; a per-layer probe is the fallback.

---

## Provenance

- Configs: `code/hgq2/configs/r14-l1x3-n8-{w1a4,w1a6}.json` — N=8, 3 features (pt, etarel,
  phirel), d32/L2/H4/FFN64, norm-free, input_std.
- Checkpoints: W&B artifacts `model-r14-l1x3-n8-{w1a4,w1a6}-s3:v0`, project `BNJetTagAug`,
  each carrying `model_best.keras` + `input_std.json` + `train_meta.json` (verified present
  before use). Val macro-AUC 0.8525 (a4) / 0.8685 (a6).
- Export: `code/hgq2/convert_final.py --beta-mode fx8 --rf 1`, gates on 4,096 real jets from
  `data/val`, C-sim on 128.
- Synthesis: `code/hgq2/mulder_csynth.sh` on mulder, serialized (never concurrent).
- Stores: `results/synthesis/runs/5f839ab5/w1a4-s3/` and `runs/794e925f/w1a6-s3/`, each with
  `export_verify.json`, `csim_verify.json`, `ebops.json`, and `csynth_rf1/` holding
  `csynth_report.json`, `csynth.xml`, `myproject_csynth.rpt`, `csynth_stdout.log`,
  `memwatch.log`.
- Export EBOPs: 3,025,884 (A8) → 2,376,990 (A6) → 1,769,889 (A4).

*Not yet independently verified by results-analyst. Every number above was read from the
stored `csynth_report.json` / `myproject_csynth.rpt` / `export_verify.json`; the per-class
attribution was parsed from the top-level Utilization/Instance tables.*
