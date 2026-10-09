#!/usr/bin/env python3
"""Trigger-first variant: build the 48x36 BNJetTag poster from the Winchester template, VERIFIED numbers only.

Layout (2026-08-23, after the poster meeting; text revised after an independent review pass):
Abstract -> BitLinear/BitNet figure + "Linear vs BitLinear" -> Goals -> Dataset and evaluation |
Model and training + architecture schematic -> Tagging efficiency | Which jets pay -> the
Level-1 trigger (what it is, what it demands) -> why binary weights help (+ EBOPs figure) ->
firmware flow | zero DSPs -> resources and device fit (+ where the LUTs go) -> open problems ->
conclusions + references.

Every number is read from RESEARCH.md (gated 2026-08-23) / results/r14/hls_r14_fit.md /
roc-results; no internal project terminology on the poster; American spelling (the abstract
and goals are the user's own text). Writes a NEW pptx; the template is left untouched.

Inputs:
  template  ~/Downloads/PosterPresentations.com-36x48-Template-Winchester.pptx
  figures   results/r14/figures/fig_r14_auc_vs_n_poster.png, fig_r14_pareto_poster.png
            (make_r14_plots.py with POSTER=1), fig_lut_attribution_n8.png (make_lut_attribution.py),
            docs/figures/bnjettag-architecture.svg (rasterized here with PyMuPDF),
            bitnet-arch.png (Wang et al., arXiv:2310.11453, Fig. 2), ByMaurizio.png (M. Pierini)
"""
from __future__ import annotations
import copy, os, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
BN = os.path.join(REPO, "bnjettag")
SRC = os.path.expanduser("~/Downloads/PosterPresentations.com-36x48-Template-Winchester.pptx")
DST = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/Downloads/BNJetTag-poster-2026-08-23-trigger-first.pptx")
FIGDIR = os.path.join(BN, "results/r14/figures")
TMP = os.path.join(os.environ.get("TMPDIR", "/tmp"), "bnjettag_poster_build")
os.makedirs(TMP, exist_ok=True)

def rasterize_svg(svg, png, width_px=6000):
    import pymupdf
    doc = pymupdf.open(svg); page = doc[0]
    z = width_px / page.rect.width
    page.get_pixmap(matrix=pymupdf.Matrix(z, z), alpha=False).save(png)
    return png

ARCH_PNG = rasterize_svg(os.path.join(REPO, "docs/figures/bnjettag-architecture.svg"), os.path.join(TMP, "arch.png"))
BITNET_PNG = os.path.join(REPO, "bitnet-arch.png")
TRIGGER_PNG = os.path.join(REPO, "ByMaurizio.png")
AUC_PNG = os.path.join(FIGDIR, "fig_r14_auc_vs_n_poster.png")
PARETO_PNG = os.path.join(FIGDIR, "fig_r14_pareto_poster.png")
LUT_PNG = os.path.join(FIGDIR, "fig_lut_attribution_n8.png")
for p in (BITNET_PNG, TRIGGER_PNG, AUC_PNG, PARETO_PNG, LUT_PNG):
    assert os.path.exists(p), p

prs = Presentation(SRC)
slide = prs.slides[0]
S = {i: sh for i, sh in enumerate(slide.shapes)}
HDR_SRC, BODY_SRC = S[1], S[0]
INK = RGBColor(0x1A, 0x1A, 0x1A); ACC = RGBColor(0x0B, 0x53, 0x94); MUTED = RGBColor(0x55, 0x5F, 0x66)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
FONT = "Arial"

def set_text(shape, blocks, size=24):
    tf = shape.text_frame; tf.word_wrap = True
    for p in list(tf.paragraphs)[1:]:
        p._element.getparent().remove(p._element)
    first = tf.paragraphs[0]
    for r in list(first.runs):
        r._r.getparent().remove(r._r)
    for i, blk in enumerate(blocks):
        text, bold, color, sz = (tuple(blk) + (None,) * 4)[:4]
        para = first if i == 0 else tf.add_paragraph()
        run = para.add_run(); run.text = text
        f = run.font; f.name = FONT; f.bold = bool(bold); f.size = Pt(sz or size); f.color.rgb = color or INK
    return shape

def clone(src, left, top, width, height, name):
    el = copy.deepcopy(src._element); src._element.getparent().append(el)
    new = [sh for sh in slide.shapes if sh._element is el][0]
    new.left, new.top, new.width, new.height = Inches(left), Inches(top), Inches(width), Inches(height)
    new.name = name; return new

def header(left, top, text, width=10.99, shape=None):
    h = shape or clone(HDR_SRC, left, top, width, 0.82, f"hdr_{text[:14]}")
    if shape is not None:
        h.left, h.top, h.width, h.height = Inches(left), Inches(top), Inches(width), Inches(0.82)
    set_text(h, [(text, True, None, 38)]); return h

def body(left, top, width, height, blocks, size=24):
    b = clone(BODY_SRC, left, top, width, height, f"body_{top:.1f}_{left:.0f}")
    set_text(b, blocks, size=size); return b

def picture(path, left, top, width):
    return slide.shapes.add_picture(path, Inches(left), Inches(top), width=Inches(width))

def table(left, top, width, height, rows, font=22, bold_col=None, acc_col=None, bold_rows=(0,)):
    t = slide.shapes.add_table(len(rows), len(rows[0]), Inches(left), Inches(top), Inches(width), Inches(height)).table
    for i, row in enumerate(rows):
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = v
            for para in c.text_frame.paragraphs:
                if j: para.alignment = PP_ALIGN.CENTER
                for r in para.runs:
                    r.font.name = FONT; r.font.size = Pt(font); r.font.bold = bool((i in bold_rows) or (bold_col is not None and j == bold_col and i > 0))
                    if acc_col is not None and j == acc_col and i: r.font.color.rgb = ACC
    return t

def replace_in_runs(shape, pairs):
    """Substring replacement inside existing runs (keeps the template's bullet formatting)."""
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            for a, b in pairs:
                if a in r.text: r.text = r.text.replace(a, b)

for i in (3, 5, 8, 10, 12):                       # unused empty template placeholders
    S[i]._element.getparent().remove(S[i]._element)

C1, C2, C3, C4 = 0.50, 12.50, 24.55, 36.55
W = 10.99
set_text(S[16], [("A Binary-Weight Transformer for Real-Time Particle Jet Tagging at the LHC", True, WHITE, 64)])
set_text(S[14], [("University of California, San Diego  ·  kaimoe123@icloud.com", False, WHITE, 28)])

# =============================================================== column 1
set_text(S[1], [("Abstract", True, None, 38)])                       # S[0] keeps the abstract (as submitted)
S[0].top, S[0].height = Inches(5.95), Inches(7.45)
for p in S[0].text_frame.paragraphs:
    for r in p.runs: r.font.name = FONT; r.font.size = Pt(23)

picture(BITNET_PNG, C1 + 0.10, 13.55, W - 0.20)                      # 10.79 wide -> 3.86 tall
body(C1, 17.45, W, 1.25, [
 ("Left: a BitLinear layer — the activation is quantized (per-tensor scale γ), multiplied by 1-bit weights, and "
  "dequantized by β·γ. Right: the BitNet block is the standard transformer block with every Linear replaced by a "
  "BitLinear. Adapted from Wang et al. [1]; our network omits the LayerNorm shown and uses ReLU in place of GELU.",
  False, MUTED, 17)], size=17)

header(C1, 18.75, "Linear vs BitLinear — what changes")
body(C1, 19.65, W, 3.90, [
 ("A standard linear layer multiplies floating-point activations by floating-point weights. A BitLinear layer "
  "quantizes its input to a fixed number of bits using a per-tensor scale γ, multiplies by weights that are only ±1, "
  "and dequantizes the result by β·γ — the output is the same number after quantize → multiply → dequantize. The "
  "multiply a Linear needs for every weight becomes a sign choice followed by an add, which is what lets it leave "
  "the DSPs (next column).", False, None, 21),
 ("On a CPU or GPU the arithmetic still runs in 32-bit floating point: the bits are simulated by rounding every value "
  "to the grid it would have in hardware. On an FPGA the bit-widths are real — we set them. The ±1 weights are "
  "trained, not post-quantized: a straight-through estimator (the rounding is treated as the identity in the "
  "backward pass) carries the gradient through.", False, None, 21),
], size=21)

header(C1, 23.65, "Goals", shape=S[2])
S[13].left, S[13].top, S[13].width, S[13].height = Inches(C1), Inches(24.55), Inches(W), Inches(4.20)
for p in S[13].text_frame.paragraphs:
    for r in p.runs: r.font.size = Pt(22)
replace_in_runs(S[13], [
 ("LUT/logic instead of scarce DSPs", "look-up tables (LUTs) and logic instead of its scarce DSP multiplier slices"),
 ("FP32 and conventional W8A8 baselines, on L1-realistic inputs",
  "full-precision (FP32) and conventional 8-bit (W8A8) baselines, using only the inputs a Level-1 trigger can provide"),
 ("against FP32 and conventional W8A8 baselines", "against full-precision (FP32) and conventional 8-bit (W8A8) baselines"),
 ("on L1-realistic inputs", "using only the inputs a Level-1 trigger can provide"),
])

header(C1, 28.85, "Dataset and evaluation")
body(C1, 29.75, W, 4.25, [
 ("Public HLS4ML LHC jet dataset [2, 3] (Zenodo 3602260): simulated LHC jets in five balanced classes — gluon, light "
  "quark, W, Z, top. 880,000 jets: 620,000 for training (124,000 of them held out for validation) and a separate test "
  "set of 260,000 jets never used for training or model selection (the 'held-out' set), on which every efficiency "
  "below is measured.", False, None, 21),
 ("Each jet is stored as up to 150 constituents. We keep the N highest-pT constituents (N = 8, 16, 32, 64) with the "
  "three features a Level-1 trigger can provide [4] — pT and the position relative to the jet axis, ηrel and φrel — "
  "and nothing else.", False, None, 21),
 ("Metric: area under the ROC curve (AUC), one-vs-rest for each class and averaged over the five classes ('macro'), "
  "on the 260,000 held-out jets, mean over 3 training seeds.", False, None, 21),
], size=21)

# =============================================================== column 2
header(C2, 5.11, "The Level-1 trigger: what it is, what it demands")
picture(TRIGGER_PNG, C2, 6.00, W)                                     # -> 3.36 tall
body(C2, 9.40, W, 0.55, [("CMS data flow (figure: M. Pierini).", False, MUTED, 17)], size=17)
body(C2, 10.00, W, 4.15, [
 ("Proton bunches collide every 25 ns (40 MHz). The Level-1 trigger — FPGAs, not software — must decide for every "
  "collision within a few microseconds, in fixed-latency logic with no option to stall, and rejects 99.75% of events "
  "before the High-Level Trigger sees them.", False, None, 20),
 ("A tagger that lives there must be small enough to share a device with everything else, fast enough to keep up with "
  "40 MHz, and predictable. Two numbers therefore matter besides accuracy: latency, and the initiation interval II — "
  "how many clock cycles before the next jet can enter (II = 1: one jet per clock cycle). Every synthesis number on "
  "this poster targets a 2.5 ns (400 MHz) clock — ten cycles per 25 ns bunch crossing.", False, None, 20),
], size=20)

header(C2, 14.25, "Why binary weights help in the trigger")
body(C2, 15.15, W, 3.05, [
 ("The VU13P has 12,288 DSP multiplier slices but 1.7 million look-up tables (LUTs). At the 8-bit precisions a "
  "conventional quantized network uses, most of its multiplies land on DSPs, and DSPs are the first resource to run out.",
  False, None, 21),
 ("With weights in {−1, +1} a multiply is a sign flip — an add or a subtract — so a matrix multiplication becomes "
  "adder trees in logic. The binary core is not merely cheaper: it moves onto a different, far more abundant resource "
  "and frees the DSPs for everything else in the trigger.", True, ACC, 21),
], size=21)

header(C2, 18.30, "Model and training", shape=S[4])
body(C2, 19.20, W, 4.30, [
 ("BitNet-style transformer encoder. Every weight in the attention and feed-forward layers, the input projection and "
  "the classifier head is binary, {−1, +1}, with one per-tensor scale β, the mean |W| of the latent weights "
  "(17,664 binary weights).", False, None, 21),
 ("2 encoder layers · model width 32 · 4 heads · feed-forward width 64 · no normalization layers · learned positional "
  "encoding · mean pooling over constituents · 5-class head.", False, None, 21),
 ("Activations are quantized to A = 8, 6 or 4 bits, with the per-tensor fixed-point ranges learned during training "
  "(high-granularity quantization, HGQ2 [5]); baselines: the same network in 32-bit float (FP32) and with 8-bit "
  "weights and activations (W8A8).", False, None, 21),
 ("Quantization-aware training on GPU — Adam optimizer, linear learning-rate decay over 100 epochs, early stopping on "
  "validation AUC, 3 seeds per configuration; the forward pass always sees the rounded values.", False, None, 21),
], size=21)
picture(ARCH_PNG, C2 + 0.25, 23.60, W - 0.50)                          # 10.49 wide -> 5.55 tall
body(C2, 29.20, W, 0.75, [
 ("The network. Blue: ±1 weights with 8-bit activations; orange: activation-only arithmetic; no normalization layers.",
  False, MUTED, 17)], size=17)

header(C2, 30.00, "From trained model to firmware")
body(C2, 30.90, W, 2.65, [
 ("Quantization-aware training (Keras + HGQ2 [5]) → hls4ml [2] converts the trained network, with its trained "
  "bit-widths, to C++ → Vitis HLS (AMD's high-level-synthesis compiler) emits Verilog → Vivado performs "
  "out-of-context logic synthesis on a Zynq UltraScale+ ZU7EV. The resulting counts are compared with the nominal "
  "Virtex UltraScale+ VU13P resource budget; they are not a target-part fit result. Two checks guard every trained-grid number: the exported network "
  "reproduces the trained model's scores (correlation ≥ 0.997 on 4,096 simulated jets; 0.9988 at N = 8), and "
  "hls4ml's own C++ test bench matches it bit-for-bit; resources and timing are read from the Vivado reports.",
  False, None, 19)], size=19)

# =============================================================== column 3
header(C3, 5.11, "Tagging efficiency", shape=S[6])
picture(AUC_PNG, C3 + 0.80, 6.05, 9.40)                               # -> 6.52 tall
table(C3, 12.70, W, 3.35, [
 ["N", "FP32", "W8A8", "Binary W1A8", "W1A4"],
 ["8",  "0.8864", "0.8862", "0.8712", "0.8534"],
 ["16", "0.9128", "0.9124", "0.8956", "0.8693"],
 ["32", "0.9374", "0.9358", "0.9052", "0.8833"],
 ["64", "0.9486", "0.9448", "0.9121 †", "0.9073"]], font=22, bold_col=3, acc_col=3)
body(C3, 16.10, W, 1.20, [
 ("Held-out = a separate test set never used for training or model selection. Macro one-vs-rest AUC, seed mean, n = 260,000 per entry; uncertainty = seed spread combined with a "
  "bootstrap over the held-out set. W1A8 = 1-bit weights, 8-bit activations; W1A4 = 1-bit weights, 4-bit activations. "
  "Seed s.d. ≤ 0.002 except binary at N = 32 (±0.008) and † N = 64, a seed range 0.9028–0.9251, not a stable mean.",
  False, MUTED, 16)], size=16)
body(C3, 17.40, W, 4.20, [
 ("What the numbers say", True, None, 24),
 ("• The three trigger-level features suffice for the task: FP32 reaches 0.913 at N = 16 and 0.949 at N = 64.", False, None, 20),
 ("• Binary stays close at short sequences: at N = 16 it loses 0.017 AUC against FP32 (0.8956 ± 0.0002 vs "
  "0.9128 ± 0.0013) — a gap well outside the seed and bootstrap uncertainty.", False, None, 20),
 ("• Halving the activation width from 8 to 4 bits costs 0.018–0.026 AUC at N ≤ 16 — at least as much as binarizing "
  "the weights did (0.015–0.017).", False, None, 20),
 ("• Binary training becomes unstable at long sequences: at N = 32 and 64 the seed-to-seed variance is ~76× that at "
  "N = 8 and 16, and the weaker runs peak mid-training (best epochs 40–57) and then degrade.", False, None, 20),
], size=20)

header(C3, 21.70, "Which jets pay for binarization?")
table(C3, 22.60, W, 2.30, [
 ["AUC, N = 16", "gluon", "quark", "W", "Z", "top"],
 ["FP32",           "0.8784", "0.8930", "0.9358", "0.9202", "0.9364"],
 ["Binary (W1A8)",  "0.8531", "0.8793", "0.9179", "0.9015", "0.9263"]], font=21, bold_rows=(0,))
body(C3, 24.95, W, 1.30, [
 ("Per-class one-vs-rest AUC (each class against the other four), held-out set, seed mean — an efficiency metric per "
  "class. Gluon jets lose the most (−0.025) and top jets the least (−0.010); at N ≥ 32 the W and Z classes pay the "
  "most and show the largest run-to-run (seed) spread.", False, MUTED, 17)], size=17)

picture(PARETO_PNG, C3 + 1.30, 26.30, 8.40)                            # -> 5.82 tall
body(C3, 32.15, W, 1.20, [
 ("Held-out AUC against a synthesis-free cost estimate (estimated bit-operations, EBOPs [5]; 3-seed mean). At matched "
  "N the binary networks need 5.3× (N = 8) to 2.1× (N = 64) fewer bit-operations than W8A8; bit-operations omit the "
  "accumulators and the β rescales, so this is a proxy, not a measured resource count.", False, MUTED, 17)], size=17)

# =============================================================== column 4
header(C4, 5.11, "FPGA implementation: zero DSPs, whole model", shape=S[7])
body(C4, 5.95, W, 1.20, [
 ("The complete network at N = 8 (Vitis HLS 2023.2, Vivado 2023.2). Cycles and II are from the Vitis HLS schedule at "
  "a 2.5 ns clock; the DSP count is the high-level-synthesis estimate, confirmed on the Vivado-synthesized netlist for "
  "the two zero-DSP rows.", False, None, 19)], size=19)
table(C4, 7.20, W, 3.25, [
 ["Operating point", "Latency (cycles)", "II", "DSPs"],
 ["Fully parallel", "164", "1", "4,133"],
 ["+ every multiplier forced into LUT logic", "146", "1", "0"],
 ["Time-multiplexed (resource-shared), every multiplier in LUT logic", "329", "47", "0"]], font=20, acc_col=3)
body(C4, 10.55, W, 2.60, [
 ("At the bit-widths learned in training the high-level-synthesis estimate already places every binary matrix "
  "multiply and all four attention products (QKᵀ and softmax·V in each layer) on 0 DSPs; the 4,133 DSPs it reports "
  "sit in the β rescaling stages (3,621) and the softmax (512), not in the binary layers. Directing the tool to "
  "build every multiplier from LUTs instead of DSP slices (an HLS resource directive) takes the design to zero DSPs, "
  "confirmed by Vivado on the netlist; restricting that directive to the two DSP-carrying stages is not enough — "
  "Vivado then re-infers 4,096 DSPs for the attention products.", False, None, 18)], size=18)

header(C4, 13.25, "Resources and the deployment gap", shape=S[9])
body(C4, 14.10, W, 1.25, [
 ("The zero-DSP result is established. VU13P fit is not: the counts below come from out-of-context ZU7EV synthesis "
  "before place-and-route and are compared only with the VU13P's nominal LUT count.",
  False, None, 19)], size=19)
table(C4, 15.40, W, 3.45, [
 ["Zero-DSP design", "DSPs", "LUTs (Vivado)", "% of nominal VU13P LUT count*"],
 ["Fully parallel, II = 1", "0", "2,108,743", "122%"],
 ["Time-multiplexed, II = 47", "0", "1,948,063", "113%"],
 ["Time-multiplexed + 4-bit softmax grid*, II = 48", "0", "1,694,625", "98%"]], font=20, acc_col=1)
picture(LUT_PNG, C4, 18.95, W)                                         # -> ~3.6 tall
body(C4, 22.60, W, 0.80, [
 ("Where the logic goes (high-level-synthesis attribution of the resource-characterization build — the only stage with a per-module "
  "breakdown): binary layers 28%, β rescaling 26%, inter-layer buffering and control 24%, attention products 14%.",
  False, MUTED, 16)], size=16)
body(C4, 23.40, W, 4.95, [
 ("Both designs at the bit-widths learned in training exceed the nominal VU13P LUT count (122%, 113%). The one remedy measured so "
  "far: narrowing the softmax output that feeds the attention product from 10 to 4 bits lets Vivado build the "
  "8-bit × 4-bit attention products from LUTs instead of DSP slices and brings the cross-part count below that nominal total (98%)* — "
  "*a resource-characterization build: the 4-bit grid was imposed at export without retraining, so it fixes the LUT "
  "count but carries no accuracy. At the 2.5 ns clock every zero-DSP design fails timing; at 5 ns (200 MHz) the "
  "same design closes pre-route timing with 0.56 ns of margin at 0 DSPs and 92% of the nominal VU13P LUT count: one jet every 48 cycles = "
  "240 ns, 333-cycle latency = 1.7 µs — not yet the sub-microsecond, II = 1 target of Goal 4. Retraining with a "
  "narrower grid is cheap: retrained with the 4-bit grid the network scores 0.8701 ± 0.0020 AUC (6-bit: "
  "0.8706 ± 0.0017) against 0.8712 ± 0.0016 for the 10-bit grid — and the retrained 4-bit network itself "
  "synthesizes to 1,689,320 LUTs (97.8% of that nominal count) at zero DSPs; at 5 ns its cross-part count is "
  "1,583,565 LUTs (91.6%) with 0.65 ns of pre-route margin. This couples measured accuracy to a zero-DSP resource point, not demonstrated VU13P fit.", False, None, 18),
 ("LUT counts: Vivado logic synthesis of the standalone module ('out of context', before place-and-route) on a "
  "smaller Zynq UltraScale+ ZU7EV device, quoted against the VU13P's nominal 1,728,000 LUTs. No VU13P placement, routing, bitstream or board test has been performed. DSP counts in the first table "
  "are high-level-synthesis estimates; the zero-DSP rows are confirmed on the Vivado netlist.", False, MUTED, 16),
], size=18)

header(C4, 28.40, "Open problems", shape=S[11])
body(C4, 29.25, W, 2.05, [
 ("• Synthesize, place and route on the VU13P; then close target-part timing.   • Reduce LUT use, 333-cycle latency "
  "and II = 48; the timing-clean point is 1.7 µs and one jet per 240 ns.   • Integrate trigger I/O, generate a "
  "bitstream and test on a board.   • Synthesize N ≥ 16 and an FP32 baseline.   • W8A8 is now measured: in the same "
  "cross-part flow it demands 2,525,842 LUTs and 5,550 DSPs.", False, None, 17)], size=17)

header(C4, 31.35, "Conclusions and references")
body(C4, 32.20, W, 1.80, [
 ("A 1-bit transformer jet tagger synthesizes entirely onto FPGA logic — zero DSPs, complete model at N = 8, "
  "confirmed at Vivado synthesis — at an accuracy cost of 0.015 AUC against FP32 at N = 8 and 0.017 at N = 16. The "
  "network retrained with a 4-bit softmax grid reaches held-out AUC 0.8701 ± 0.0020 and a zero-DSP ZU7EV out-of-context "
  "count below the nominal VU13P LUT total. It is not yet Level-1 deployable: VU13P place-and-route, target latency and throughput, and board integration remain open.",
  True, ACC, 17),
 ("[1] Wang et al., BitNet, arXiv:2310.11453  [2] Duarte et al., hls4ml, JINST 13 P07027 (2018)  [3] Moreno et al., "
  "JEDI-net, arXiv:1908.05318  [4] Odagiu et al., arXiv:2402.01876  [5] C. Sun et al., HGQ, arXiv:2405.00645  "
  "[6] Laatu, C. Sun et al., sub-µs transformers for jet tagging on FPGAs, arXiv:2510.24784", False, MUTED, 13.5),
], size=17)

prs.save(DST)
print("wrote", DST)
