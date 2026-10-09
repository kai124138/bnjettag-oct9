#!/usr/bin/env python3
"""Contact sheet: the same verified panel rendered under each candidate .mplstyle.

Data: publication tree results/pre_conference/auc_per_seed.csv (three seeds, held-out
macro one-vs-rest AUC vs constituent count). Labels and caption copied from
code/analysis/build_figures.py. Only the style differs between panels.

    uv run --with matplotlib,pandas,pillow python contact_sheet.py [path/to/auc_per_seed.csv]

# plot_check: allow-title      (variants A and C carry a title on purpose; the sheet compares styles)
# plot_check: allow-fontsize   (the caption size is derived from each variant's font.size)
"""
import sys
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CANDIDATES = [ROOT / "publication/results/pre_conference/auc_per_seed.csv",                 # unified workspace
              ROOT / "publication-engram-20260921/results/pre_conference/auc_per_seed.csv"]  # lab repo layout
CSV = Path(sys.argv[1]) if len(sys.argv) > 1 else next((c for c in CANDIDATES if c.exists()), CANDIDATES[0])
PRECISIONS = ("FP32", "W8A8", "W1A8", "W1A6", "W1A4")   # fixed order = fixed hue
VARIANTS = [("A", "incumbent", True), ("B", "journal", False), ("C", "poster", True)]

auc = pd.read_csv(CSV)
summary = auc.groupby(["precision", "n_constituents"]).macro_ovr_auc.agg(["mean", "std"])

def panel(letter, name, with_title):
    plt.rcdefaults()
    plt.style.use(HERE / f"bnjettag-{letter.lower()}-{name}.mplstyle")
    fig, ax = plt.subplots(layout="constrained")
    for precision in PRECISIONS:
        d = summary.loc[precision]
        ax.errorbar(d.index, d["mean"], yerr=d["std"], label=precision, marker="o",
                    capsize=plt.rcParams.get("errorbar.capsize", 4) or 4)
    ax.set(xlabel="Number of jet constituents", ylabel="Held-out macro one-vs-rest AUC",
           xticks=[8, 16, 32, 64])
    if with_title:
        ax.set_title("Pre-conference: constituent count and precision")
    ax.legend(ncol=5 if letter != "B" else 3, loc="lower right")
    fig.supxlabel("Three training seeds; error bars show sample standard deviation",
                  fontsize=plt.rcParams["font.size"] * 0.9)
    out = HERE / f"variant-{letter}-{name}.png"
    fig.savefig(out, dpi=180 if letter != "B" else 300, bbox_inches="tight")
    plt.close(fig)
    return out

paths = [panel(*v) for v in VARIANTS]
imgs = [Image.open(p).convert("RGB") for p in paths]
H = 900
imgs = [im.resize((round(im.width * H / im.height), H), Image.LANCZOS) for im in imgs]
pad, head = 40, 70
W = sum(im.width for im in imgs) + pad * (len(imgs) + 1)
sheet = Image.new("RGB", (W, H + head + pad), "white")
draw = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 34)
except OSError:
    font = ImageFont.load_default()
x = pad
for (letter, name, _), im in zip(VARIANTS, imgs):
    draw.text((x, 18), f"{letter}  {name}", fill="black", font=font)
    sheet.paste(im, (x, head))
    x += im.width + pad
sheet.save(HERE / "contact-sheet-auc.png")
print("wrote", HERE / "contact-sheet-auc.png", sheet.size)
