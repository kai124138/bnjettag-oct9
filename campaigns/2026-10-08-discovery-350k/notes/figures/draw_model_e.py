"""Architecture schematic of BNJetTag model E (binary-weight transformer), Chang-recipe runs.

Every element is checked against code/bnhgq2/qat.py (build_qat_model) and
configs/d350-baseline-e-350k-s1.json; line references are in the report that came with this
script. Source: campaigns/2026-10-08-discovery-350k, config d350-baseline-e-350k-s1. n/a (schematic).

    uv run --with matplotlib python draw_model_e.py
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Rectangle

HERE = Path(__file__).resolve().parent
STYLE = HERE.parents[3] / "docs" / "style" / "bnjettag.mplstyle"
if STYLE.exists():
    plt.style.use(str(STYLE))
plt.rcParams.update({"font.size": 9.5, "mathtext.fontset": "dejavusans",
                     "font.family": "DejaVu Sans", "svg.fonttype": "none",
                     "pdf.fonttype": 42})

# Okabe-Ito based, one meaning per colour
BIN_F, BIN_E = "#CFE3F3", "#0072B2"      # binary-weight layer
ACT_F, ACT_E = "#F4D9E8", "#B0306F"      # activation-only arithmetic
PLN_F, PLN_E = "#EEEEEE", "#555555"      # no-weight plain box
QUA_F, QUA_E = "#E69F00", "#6B4600"      # activation quantizer badge
INK = "#222222"

fig, ax = plt.subplots(figsize=(10, 5.6))
ax.set_xlim(0, 10)
ax.set_ylim(0, 5.6)
ax.axis("off")
fig.subplots_adjust(0, 0, 1, 1)


def box(x0, y0, x1, y1, text, kind="plain", lw=1.2):
    f, e = {"bin": (BIN_F, BIN_E), "act": (ACT_F, ACT_E), "plain": (PLN_F, PLN_E)}[kind]
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0,
                                boxstyle="round,pad=0,rounding_size=0.05",
                                fc=f, ec=e, lw=2.0 if kind == "bin" else lw, zorder=3))
    ax.text((x0 + x1) / 2, (y0 + y1) / 2, text, ha="center", va="center",
            color=INK, zorder=4, linespacing=1.25)


def line(pts, arrow=True, lw=1.1, color=INK, ls="-"):
    xs, ys = zip(*pts)
    if arrow:
        ax.plot(xs[:-1], ys[:-1], color=color, lw=lw, ls=ls, zorder=2, solid_capstyle="butt")
        ax.annotate("", xy=pts[-1], xytext=pts[-2], zorder=2,
                    arrowprops=dict(arrowstyle="-|>", lw=lw, color=color, shrinkA=0,
                                    shrinkB=0, mutation_scale=9, ls=ls))
    else:
        ax.plot(xs, ys, color=color, lw=lw, ls=ls, zorder=2)


def badge(x, y, r=0.075):
    ax.add_patch(Polygon([(x - r, y), (x, y + r * 1.25), (x + r, y), (x, y - r * 1.25)],
                         closed=True, fc=QUA_F, ec=QUA_E, lw=0.9, zorder=5))


def dot(x, y):
    ax.add_patch(Circle((x, y), 0.04, fc=INK, ec=INK, zorder=5))


def plus(x, y, r=0.14):
    ax.add_patch(Circle((x, y), r, fc="white", ec=INK, lw=1.1, zorder=3))
    ax.text(x, y - 0.005, "+", ha="center", va="center", color=INK, zorder=4)


# ------------------------------------------------------------------ input
box(0.10, 3.40, 1.15, 4.90,
    "input\n64 $\\times$ 3\npT, $\\eta_{rel}$,\n$\\phi_{rel}$\npT $\\geq$ 2 GeV\ngate,\nstandardised")
box(1.45, 3.70, 2.30, 4.50, "input\nproj.\n3 $\\to$ 24", "bin")
line([(1.15, 4.10), (1.45, 4.10)])
badge(1.30, 4.10)
ax.text(1.88, 3.50, "no positional\nencoding", ha="center", va="top", color=INK, linespacing=1.2)

# ------------------------------------------------------------------ encoder block frame
ax.add_patch(FancyBboxPatch((2.45, 1.75), 7.45, 3.40, boxstyle="round,pad=0,rounding_size=0.08",
                            fc="none", ec=INK, lw=1.2, ls=(0, (5, 3)), zorder=1))
ax.text(2.50, 5.22, "Encoder block, $\\times$1, no normalisation", ha="left", va="bottom", color=INK)

# bus: input_proj output -> residual branch and Q/K/V taps
line([(2.30, 4.10), (2.62, 4.10)], arrow=False)
line([(2.62, 4.85), (2.62, 3.63)], arrow=False)
dot(2.62, 4.10)
ys = {"q": 4.47, "k": 4.05, "v": 3.63}
names = {"q": "$W_q$: 24 $\\to$ 2$\\times$12", "k": "$W_k$: 24 $\\to$ 2$\\times$12",
         "v": "$W_v$: 24 $\\to$ 2$\\times$12"}
for key, y in ys.items():
    box(3.00, y - 0.17, 4.30, y + 0.17, names[key], "bin")
    line([(2.62, y), (3.00, y)])
    badge(2.81, y)

# attention products
box(4.65, 3.85, 5.55, 4.65, "$Q\\cdot K^{T}$\nact $\\times$ act\n2$\\times$64$\\times$64", "act")
box(5.85, 3.85, 6.95, 4.65, "softmax\nlearned exp/inv\ntables", "act")
box(7.25, 3.85, 8.05, 4.65, "$A\\cdot V$\nact $\\times$ act", "act")
box(8.40, 3.85, 9.05, 4.65, "$W_o$\n2$\\times$12\n$\\to$ 24", "bin")
plus(9.40, 4.25)

line([(4.30, ys["q"]), (4.65, ys["q"])])
badge(4.47, ys["q"])
line([(4.30, ys["k"]), (4.65, ys["k"])])
badge(4.47, ys["k"])
line([(5.55, 4.25), (5.85, 4.25)])
line([(6.95, 4.25), (7.25, 4.25)])
badge(7.10, 4.25)                                     # softmax output (attention weights)
line([(4.30, ys["v"]), (7.65, ys["v"]), (7.65, 3.85)])
badge(6.00, ys["v"])
line([(8.05, 4.25), (8.40, 4.25)])
badge(8.225, 4.25)                                    # context into W_o
line([(9.05, 4.25), (9.26, 4.25)])

# residual 1
line([(2.62, 4.85), (9.40, 4.85), (9.40, 4.39)])
ax.text(6.0, 4.90, "residual", ha="center", va="bottom", color=INK)

# FFN row (right to left)
line([(9.40, 4.11), (9.40, 3.10)])
badge(9.40, 3.60)
box(8.50, 2.50, 9.60, 3.10, "fc1: 24 $\\to$ 32", "bin")
box(7.60, 2.50, 8.20, 3.10, "ReLU")
box(6.25, 2.50, 7.25, 3.10, "fc2: 32 $\\to$ 24", "bin")
plus(5.60, 2.80)
line([(8.50, 2.80), (8.20, 2.80)])
line([(7.60, 2.80), (7.25, 2.80)])
badge(7.425, 2.80)
line([(6.25, 2.80), (5.74, 2.80)])
# residual 2
dot(9.40, 3.75)
line([(9.40, 3.75), (9.78, 3.75), (9.78, 2.05), (5.60, 2.05), (5.60, 2.66)])
ax.text(7.7, 2.10, "residual", ha="center", va="bottom", color=INK)

# ------------------------------------------------------------------ head
line([(5.46, 2.80), (5.00, 2.80), (5.00, 1.35)])
box(4.55, 0.75, 5.45, 1.35, "global avg\npool, 64", "act")
box(5.85, 0.75, 6.90, 1.35, "head fc1\n24 $\\to$ 24", "bin")
box(7.20, 0.75, 7.80, 1.35, "ReLU")
box(8.15, 0.75, 9.15, 1.35, "head fc2\n24 $\\to$ 5", "bin")
box(9.40, 0.75, 9.95, 1.35, "5 class\nscores")
line([(5.45, 1.05), (5.85, 1.05)])
badge(5.65, 1.05)
line([(6.90, 1.05), (7.20, 1.05)])
line([(7.80, 1.05), (8.15, 1.05)])
badge(7.975, 1.05)
line([(9.15, 1.05), (9.40, 1.05)])

# ------------------------------------------------------------------ legend
ly = {1: 2.85, 2: 2.42, 3: 2.02, 4: 1.80}
ax.add_patch(Rectangle((0.10, ly[1] - 0.09), 0.28, 0.18, fc=BIN_F, ec=BIN_E, lw=2.0))
ax.text(0.46, ly[1], "binary weights $\\pm\\beta$\n1 bit, cannot shrink", va="center", color=INK,
        linespacing=1.2)
badge(0.24, ly[2])
ax.text(0.46, ly[2], "activation quantizer\nlearned width per channel,\ncan shrink to 0 bits",
        va="center", color=INK, linespacing=1.2)
ax.add_patch(Rectangle((0.10, ly[3] - 0.09), 0.28, 0.18, fc=ACT_F, ec=ACT_E, lw=1.2))
ax.text(0.46, ly[3], "activation-only arithmetic", va="center", color=INK)
ax.add_patch(Rectangle((0.10, ly[4] - 0.09), 0.28, 0.18, fc=PLN_F, ec=PLN_E, lw=1.2))
ax.text(0.46, ly[4], "no weights, no quantizer", va="center", color=INK)

# ------------------------------------------------------------------ inset
ax.add_patch(FancyBboxPatch((0.10, 0.36), 4.40, 1.30, boxstyle="round,pad=0,rounding_size=0.06",
                            fc="white", ec=BIN_E, lw=1.0, zorder=1))
ax.text(0.20, 1.55, "Inside every binary layer", ha="left", va="center", color=INK,
        fontweight="bold")
box(0.20, 1.12, 0.52, 1.38, "$x$")
line([(0.52, 1.25), (0.90, 1.25)])
badge(0.71, 1.25)
box(0.90, 1.12, 2.70, 1.38, "einsum: $x_q\\cdot q\\,\\beta$", "bin")
line([(2.70, 1.25), (3.05, 1.25)])
box(3.05, 1.12, 3.75, 1.38, "+ bias")
line([(3.75, 1.25), (4.08, 1.25)])
ax.text(4.12, 1.25, "$y$", va="center", color=INK)
ax.text(0.20, 0.99, "diamond: iq, learned-width quantizer (qat.py:79-80)", va="center", color=INK)
ax.text(0.20, 0.82, "$q$ = sign($w$ $-$ mean $w$), $\\beta$ = mean|$w$ $-$ mean $w$| (qat.py:45-67)",
        va="center", color=INK)
ax.text(0.20, 0.65, "float latent kernel, binarized each pass (qat.py:78); float bias",
        va="center", color=INK)
ax.text(0.20, 0.48, "EBOPs counts the kernel as 1 bit (_binary_kq, qat.py:230)", va="center",
        color=INK)

# ------------------------------------------------------------------ footer
ax.text(0.10, 0.15, "Model E as configured in campaigns/2026-10-08-discovery-350k "
        "(d350-baseline-e-350k-s1); schematic, not to scale.", ha="left", va="center", color=INK)

for ext, kw in (("png", {"dpi": 200}), ("svg", {}), ("pdf", {})):
    fig.savefig(HERE / f"model-e-quantization.{ext}", bbox_inches="tight", **kw)
plt.close(fig)
