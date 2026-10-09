#!/usr/bin/env python3
"""Where the logic goes: LUTs by module family for one synthesized n8 build.

Reads the per-instance Utilization table of a stored `myproject_csynth.rpt` through
`code/hgq2/parse_families.py` (the project's family parser, self-tested 8/8) and the
top-level `csynth_report.json`, groups the families into poster-readable buckets, and
draws ONE horizontal bar chart (single series, direct labels). Numbers are C-synthesis
(high-level-synthesis) estimates — the only stage with a per-module breakdown; the
figure therefore shows SHARES with the absolute count as a secondary label and says so.

Default build: the scoped-binding + 4-bit-softmax-operand folded build
(results/synthesis/runs/38a20c62/w1a8-s3-r14n8-beta1sm4i0/csynth_beta1sm4i0/), the point
that fits the VU13P LUT budget at Vivado post-opt (RESEARCH.md §6.3).

Usage: python make_lut_attribution.py [--build <dir with myproject_csynth.rpt + csynth_report.json>] [--out <stem>]
"""
from __future__ import annotations
import argparse, json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, "code", "hgq2"))
import parse_families as pf  # noqa: E402

DEFAULT_BUILD = os.path.join(REPO, "results/synthesis/runs/38a20c62/w1a8-s3-r14n8-beta1sm4i0/csynth_beta1sm4i0")

# family (parse_families keying) -> poster bucket
BUCKETS = [
    ("Binary linear layers (±1 weights)",            ["einsum_dense", "dense_latency"]),
    ("β rescaling (dequantization) in LUT logic",    ["normalize"]),
    ("Attention activation×activation (QKᵀ, softmax·V)", ["einsum(actxact)"]),
    ("Activation requantization",                    ["thresholded_relu"]),
    ("Softmax",                                      ["softmax", "Loop_VITIS_LOOP_408_1_proc", "Loop_VITIS_LOOP_408_1_proc111"]),
    ("Residual adds, pooling",                       ["add", "global_pooling1d_cl"]),
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", default=DEFAULT_BUILD)
    ap.add_argument("--out", default=os.path.join(REPO, "results/r14/figures/fig_lut_attribution_n8"))
    a = ap.parse_args()
    rpt = os.path.join(a.build, "myproject_csynth.rpt")
    fam, rows, trusted = pf.load(rpt)
    assert trusted, "rpt instance table required (xml fallback can double-count)"
    total = json.load(open(os.path.join(a.build, "csynth_report.json")))["LUT"]
    lut = {k: v["LUT"] for k, v in fam.items() if k != "(top-level)"}
    used = set()
    vals = []
    for label, keys in BUCKETS:
        s = sum(lut.get(k, 0) for k in keys); used.update(keys); vals.append((label, s))
    rest = sum(v for k, v in lut.items() if k not in used)      # and/or gates, dataflow Block_* processes
    modules = sum(v for _, v in vals) + rest
    glue = total - modules                                      # FIFOs, expressions, multiplexers (top-level rows)
    vals.append(("Inter-layer buffers & control (FIFOs, multiplexers)", glue + rest))
    assert abs(sum(v for _, v in vals) - total) < 2, (sum(v for _, v in vals), total)
    vals.sort(key=lambda t: t[1], reverse=True)

    labels = [l for l, _ in vals]; nums = [v for _, v in vals]; shares = [100 * v / total for v in nums]
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    ink, blue, muted = "#1a1a1a", "#0b5394", "#555f66"
    y = range(len(vals))[::-1]
    ax.barh(list(y), shares, color=blue, height=0.62)
    for yi, sh, n, lab in zip(y, shares, nums, labels):
        ax.text(sh + 0.6, yi, f"{sh:.0f}%  ({n/1e3:,.0f}k)", va="center", ha="left", fontsize=19, color=ink)
    ax.set_yticks(list(y)); ax.set_yticklabels(labels, fontsize=20, color=ink)
    ax.set_xlabel("share of the design's LUTs (%), N = 8, 1-bit weights / 8-bit activations", fontsize=16, color=muted)
    ax.set_xlim(0, max(shares) * 1.30)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.tick_params(axis="x", labelsize=15, colors=muted); ax.xaxis.grid(True, color="#dddddd", lw=0.8); ax.set_axisbelow(True)
    ax.text(0, -0.27, f"Shares from the high-level-synthesis report of the fitting build ({total:,} LUTs in total); the same design is 1,694,625 LUTs after Vivado logic synthesis — shares, not absolute counts.",
            transform=ax.transAxes, fontsize=10.5, color=muted, ha="left", va="top")
    fig.tight_layout()
    for ext in ("png", "pdf"):
        fig.savefig(f"{a.out}.{ext}", dpi=220 if ext == "png" else None, bbox_inches="tight")
    print("wrote", a.out + ".{png,pdf}"); print("total", total)
    for l, n, s in zip(labels, nums, shares): print(f"  {s:5.1f}%  {n:>10,}  {l}")

if __name__ == "__main__":
    main()
