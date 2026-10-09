"""Pilot b5 training curves for a slide. Reads pilotb5-curves.csv (made by parse_pilotb5.py)."""
import os, csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
STYLE = HERE + "/../../../docs/style/bnjettag.mplstyle"
if os.path.exists(STYLE):
    plt.style.use("/home/kaimoe/lab/bnjettag/docs/style/bnjettag.mplstyle")
plt.rcParams.update({"font.size": 9, "axes.labelsize": 9, "legend.fontsize": 8,
                     "axes.spines.top": False, "axes.spines.right": False})

LAB = {"a-n64-s1": "A, seed 1 (E, 350k)", "a-n64-s2": "A, seed 2 (E, 350k)",
       "d-n64-s1": "D, seed 1 (E, 350k, our optimizer)", "e1-n64-s1": "E1, seed 1 (1 head, 350k)",
       "cprime-n64-s1": "C', seed 1 (A07, 5M target)"}
COL = {"a-n64-s1": "#0072B2", "a-n64-s2": "#56B4E9", "d-n64-s1": "#D55E00",
       "e1-n64-s1": "#009E73", "cprime-n64-s1": "#7F7F7F"}
rows = list(csv.DictReader(open(HERE + "/pilotb5-curves.csv")))
arms = list(LAB)
def ser(arm, col, traced=False):
    r = [x for x in rows if x["arm"] == arm and x[col] != ""]
    return [int(x["epoch"]) for x in r], [float(x[col]) for x in r]

fig, ax = plt.subplots(1, 3, figsize=(9, 4.2), constrained_layout=True)
for a in arms:
    c = COL[a]
    ax[0].plot(*ser(a, "val_accuracy"), color=c, lw=1.1, label=LAB[a])
    ax[1].plot(*ser(a, "ebops_traced"), color=c, lw=1.1, marker="o", ms=2)
    ax[2].plot(*ser(a, "beta"), color=c, lw=1.1)
ax[0].axhline(0.203, color="k", ls="--", lw=0.8)
ax[0].axhline(0.211, color="k", ls=":", lw=0.8)
BB = dict(fc="white", ec="none", alpha=0.85, pad=1)
ax[0].text(5, 0.198, "chance 0.203", ha="left", va="top", bbox=BB)
ax[0].text(5, 0.216, "degenerate threshold 0.211", ha="left", va="bottom", bbox=BB)
ax[0].set_ylabel("validation top-1 accuracy")
ax[1].set_yscale("log")
ax[1].axhline(350000, color="k", ls="--", lw=0.8)
ax[1].text(495, 350000 * 0.62, "dashed: 350k target (C': 5M)", ha="right", va="top")
fl = {a: int(float(next(x["floor"] for x in rows if x["arm"] == a and x["floor"] != ""))) for a in arms}
for v in sorted(set(fl.values())):
    ax[1].axhline(v, color="k", ls=":", lw=0.8)
    ax[1].text(495, v * 0.93, f"0-bit floor {v:,}", ha="right", va="top")
ax[1].set_ylabel("traced EBOPs")
ax[2].set_yscale("log")
ax[2].set_ylabel("beta")
for i in range(3):
    ax[i].set_xlabel("epoch")
    ax[i].set_xlim(0, 500)
fig.legend(*ax[0].get_legend_handles_labels(), loc="upper center", ncol=3, frameon=False,
           bbox_to_anchor=(0.5, 1.09))
fig.text(0.5, -0.04, "Validation split, n = 62,000; pilot b5, single seed per arm (A: two), "
         "values read from training logs, not verified.", ha="center", va="top")
for ext in ("png", "pdf", "svg"):
    fig.savefig(HERE + f"/pilotb5-curves.{ext}", dpi=200, bbox_inches="tight")
plt.close(fig)
