from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MultipleLocator


OUTPUT_DIR = Path(__file__).resolve().parent

RUNS = {
    "R0": {"ebops": 348_526, "auc": 0.8453, "category": "baseline"},
    "R1": {"ebops": 317_890, "auc": 0.8519, "category": "finished"},
    "R2": {"ebops": 329_838, "auc": 0.8545, "category": "finished"},
    "R3": {"ebops": 340_174, "auc": 0.8463, "category": "interrupted"},
    "R5": {"ebops": 349_390, "auc": 0.8410, "category": "finished"},
    "R6": {"ebops": 348_366, "auc": 0.8420, "category": "interim"},
}

STYLES = {
    "baseline": {"color": "#4D4D4D", "marker": "o"},
    "finished": {"color": "#0072B2", "marker": "o"},
    "interrupted": {"color": "#D55E00", "marker": "D"},
    "interim": {"color": "#CC79A7", "marker": "^"},
}

LABEL_OFFSETS = {
    "R0": (-12, 13, "right"),
    "R1": (10, -3, "left"),
    "R2": (10, -4, "left"),
    "R3": (10, 10, "left"),
    "R5": (-12, -17, "right"),
    "R6": (-12, 8, "right"),
}


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 11,
            "axes.titlesize": 16,
            "axes.labelsize": 12,
            "axes.titleweight": "semibold",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )

    fig, ax = plt.subplots(figsize=(10, 6.25), constrained_layout=False)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.86, bottom=0.24)

    for run, result in RUNS.items():
        style = STYLES[result["category"]]
        edgecolor = "#202020" if run == "R2" else "white"
        linewidth = 1.4 if run == "R2" else 0.9
        ax.scatter(
            result["ebops"],
            result["auc"],
            s=115,
            color=style["color"],
            marker=style["marker"],
            edgecolor=edgecolor,
            linewidth=linewidth,
            zorder=3,
        )

        dx, dy, alignment = LABEL_OFFSETS[run]
        weight = "bold" if run == "R2" else "normal"
        ax.annotate(
            f'{run}  ({result["auc"]:.4f})',
            (result["ebops"], result["auc"]),
            xytext=(dx, dy),
            textcoords="offset points",
            ha=alignment,
            va="center",
            fontsize=10.5,
            fontweight=weight,
            color="#202020",
            zorder=4,
        )

    ax.axvline(
        350_000,
        color="#777777",
        linewidth=1.2,
        linestyle=(0, (4, 3)),
        zorder=1,
    )

    ax.set_xlim(315_000, 352_000)
    ax.set_ylim(0.8390, 0.8565)
    ax.xaxis.set_major_locator(MultipleLocator(5_000))
    ax.yaxis.set_major_locator(MultipleLocator(0.0025))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value / 1000:.0f}k"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _: f"{value:.4f}"))

    ax.grid(axis="both", color="#D9D9D9", linewidth=0.7, alpha=0.8)
    ax.set_axisbelow(True)
    ax.set_xlabel("Effective bit operations (EBOPs)", labelpad=9)
    ax.set_ylabel("Validation macro-OvR AUC", labelpad=9)
    ax.set_title("Validation AUC vs. EBOPs", loc="left", pad=18)
    ax.text(
        0.0,
        1.015,
        "Best reported checkpoint at or below the 350k target",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=10.5,
        color="#555555",
    )

    legend_handles = [
        Line2D(
            [0], [0], marker="o", linestyle="none", markerfacecolor="#4D4D4D",
            markeredgecolor="white", markersize=8, label="Matched baseline"
        ),
        Line2D(
            [0], [0], marker="o", linestyle="none", markerfacecolor="#0072B2",
            markeredgecolor="white", markersize=8, label="Finished variant"
        ),
        Line2D(
            [0], [0], marker="D", linestyle="none", markerfacecolor="#D55E00",
            markeredgecolor="white", markersize=7, label="Interrupted checkpoint"
        ),
        Line2D(
            [0], [0], marker="^", linestyle="none", markerfacecolor="#CC79A7",
            markeredgecolor="white", markersize=8, label="Running / interim"
        ),
        Line2D(
            [0], [0], color="#777777", linewidth=1.2, linestyle=(0, (4, 3)),
            label="350k EBOP target"
        ),
    ]
    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.17),
        ncol=5,
        frameon=False,
        fontsize=9.5,
        handletextpad=0.6,
        columnspacing=1.25,
    )

    fig.text(
        0.12,
        0.025,
        "R4 is not plotted because it has not yet produced a checkpoint at or below 350k EBOPs.",
        ha="left",
        va="bottom",
        fontsize=9.5,
        color="#555555",
    )

    png_path = OUTPUT_DIR / "ebops-auc-scatter-matplotlib.png"
    pdf_path = OUTPUT_DIR / "ebops-auc-scatter-matplotlib.pdf"
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, bbox_inches="tight")
    plt.close(fig)

    print(png_path)
    print(pdf_path)


if __name__ == "__main__":
    main()
