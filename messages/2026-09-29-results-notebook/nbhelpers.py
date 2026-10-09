"""Loaders, recomputes and figures for results_summary.ipynb (2026-09-29).

Every number the notebook shows is read here, at run time, from a saved file: the .npz
prediction arrays (AUC and accuracy are recomputed from them), the csynth JSON and Vivado
reports, saved JSON records and saved pod logs. Nothing is typed in by hand. Each loader
records the files it read, so the notebook can list its inputs with size and modification
time.

AUC convention (verify-roc skill): macro one-vs-rest over the five classes g, q, W, Z, t,
sklearn roc_auc_score per class on softmax scores. The 2026-09-12 ablation arrays hold raw
logits, so softmax is applied first; that reproduces the stored values exactly, and raw
logits do not.

Style: the house file, then the talk variant that docs/conventions/figures.md names for slides
(docs/figures/style/bnjettag-c-poster.mplstyle). plot_check: allow-fontsize. The one relative
size used here ("small") sets the provenance lines and direct labels one step under the axis
labels; every absolute size comes from the two style files.
"""
from __future__ import annotations

import csv
import json
import re
import textwrap
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.font_manager import FontProperties  # noqa: E402
from scipy import stats  # noqa: E402
from sklearn.metrics import roc_auc_score, roc_curve  # noqa: E402

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
FIG_DIR = HERE / "figures"
CLASSES = ["g", "q", "W", "Z", "t"]

# One palette for the whole notebook (the house cycle). The precision variants keep these
# colours on every figure; telemetry and single-family plots use black and grey.
VARIANT_COLOR = {"FP32": "#243746", "W8A8": "#0072B2", "W1A8": "#009E73",
                 "W1A6": "#D55E00", "W1A4": "#CC79A7"}
INK, GREY = "#000000", "#8C8C8C"

LOADED: dict[str, tuple[int, str]] = {}


# ----------------------------------------------------------------------------------------
# bookkeeping and metrics
# ----------------------------------------------------------------------------------------
def src(rel) -> Path:
    """Resolve a repo-relative path and record it as an input of this run."""
    p = Path(rel)
    p = p if p.is_absolute() else REPO / p
    st = p.stat()
    LOADED[str(p.relative_to(REPO))] = (
        st.st_size, time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)))
    return p


def read_json(rel):
    return json.loads(src(rel).read_text())


def softmax(z):
    z = np.asarray(z, dtype=np.float64)
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def macro_auc(y, p) -> float:
    return float(roc_auc_score(y, p, average="macro"))


def class_aucs(y, p) -> list[float]:
    return [float(roc_auc_score(y[:, c], p[:, c])) for c in range(y.shape[1])]


def top1(y, p) -> float:
    return float((np.asarray(p).argmax(1) == np.asarray(y).argmax(1)).mean())


def t_interval(d, conf=0.95):
    """Mean, lower, upper and sd (ddof=1) of paired differences; Student t, df = n - 1."""
    d = np.asarray(d, dtype=float)
    m, sd = d.mean(), d.std(ddof=1)
    h = stats.t.ppf(0.5 + conf / 2, df=len(d) - 1) * sd / np.sqrt(len(d))
    return dict(mean=m, lo=m - h, hi=m + h, sd=sd, n=len(d), lower=int((d < 0).sum()))


def fmt_int(x) -> str:
    return f"{int(round(x)):,}"


def pct(x, nd=2) -> str:
    return f"{100 * x:.{nd}f} %"


def md_table(headers, rows) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "|".join("---" for _ in headers) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def sources_table() -> str:
    rows = [(f"`{k}`", f"{v[0]:,}", v[1]) for k, v in sorted(LOADED.items())]
    return md_table(["file read by this run", "bytes", "modified (local time)"], rows)


# ----------------------------------------------------------------------------------------
# style and saving
# ----------------------------------------------------------------------------------------
def apply_style():
    """House style, then the talk variant the figure conventions name for slides and posters."""
    plt.style.use(str(REPO / "docs/style/bnjettag.mplstyle"))
    plt.style.use(str(REPO / "docs/figures/style/bnjettag-c-poster.mplstyle"))


def save(fig, name: str, provenance: str) -> Path:
    """Stamp the provenance lines below everything drawn, write .png and .svg, close the figure."""
    FIG_DIR.mkdir(exist_ok=True)
    fig.canvas.draw()
    bb = fig.get_tightbbox(fig.canvas.get_renderer())  # inches, all decorations included
    w, h = fig.get_size_inches()
    width = max(40, int(bb.width * 72 / (0.56 * FontProperties(size="small").get_size_in_points())))
    text = "\n".join(textwrap.fill(par, width) for par in provenance.split("\n"))
    fig.text(bb.x0 / w, (bb.y0 - 0.12) / h, text, ha="left", va="top", fontsize="small", color="#333333")
    for ext in ("png", "svg"):  # no creation date in the SVG, so an unchanged figure stays byte-identical
        fig.savefig(FIG_DIR / f"{name}.{ext}", bbox_inches="tight",
                    metadata={"Date": None} if ext == "svg" else None)
    plt.close(fig)
    return FIG_DIR / f"{name}.png"


def label_points(ax, xs, ys, labels, pad_pt=10.0):
    """Direct labels beside scatter points, pushed apart vertically so none overlap, with a
    leader line whenever a label had to move off its point; a label that would run past the
    left edge of the axes goes on the right of its point instead."""
    fig = ax.figure
    fig.canvas.draw()
    px = ax.transData.transform(np.column_stack([xs, ys]))
    font_px = FontProperties(size="small").get_size_in_points() * fig.dpi / 72.0
    placed, top = {}, -np.inf
    floor = ax.get_window_extent().y0  # no label may hang below the x axis
    for i in np.argsort(px[:, 1]):
        half = 0.6 * font_px * (labels[i].count("\n") + 1)  # half the label's height, in pixels
        placed[i] = max(px[i, 1], top + half + 0.1 * font_px, floor + half + 0.2 * font_px)
        top = placed[i] + half
    left_edge = ax.get_window_extent().x0
    for i, text in enumerate(labels):
        width = 0.56 * font_px * max(len(line) for line in text.split("\n"))
        right = px[i, 0] - pad_pt * fig.dpi / 72.0 - width < left_edge
        dy = (placed[i] - px[i, 1]) * 72.0 / fig.dpi
        # the leader starts at the label's near end, not its centre, so it never crosses a neighbour
        leader = (dict(arrowstyle="-", color=GREY, lw=1.2, shrinkA=0, shrinkB=6, relpos=(0.0 if right else 1.0, 0.5))
                  if abs(dy) > 1 else None)
        ax.annotate(text, (xs[i], ys[i]), xytext=(pad_pt if right else -pad_pt, dy), textcoords="offset points",
                    ha="left" if right else "right", va="center", fontsize="small", arrowprops=leader)


def roc_points(y_bin, score, grid=600):
    """ROC in the HEP convention: efficiency (TPR) and mistag rate (FPR) on a TPR grid."""
    fpr, tpr, _ = roc_curve(y_bin, score)
    eff = np.linspace(0.02, 1.0, grid)
    mistag = np.interp(eff, tpr, fpr)
    return eff, mistag


# ----------------------------------------------------------------------------------------
# current era: EBOP-constrained N = 8 ablation (seed 1, 1,000 epochs)
# ----------------------------------------------------------------------------------------
ABL_DIR = "campaigns/2026-09-16-accuracy-investigation/remote-results"
ABL_JSON = "publication/results/post_conference/ablation_metrics.json"
ABL_STATUS = "publication/results/post_conference/ablation-training-status-20260920.json"
ARM_NAMES = {
    "tensor_quantization": "Tensor-wise quantization (baseline)",
    "channel_quantization": "Channel-wise quantization",
    "reduced_feedforward": "Reduced feed-forward width",
    "attention_probability_8bit": "8-bit attention probabilities",
    "gradual_budget": "Gradual budget schedule",
    "fixed_width_recovery": "Fixed-width recovery",
    "knowledge_distillation": "Knowledge distillation",
}
ARM_SHORT = {
    "tensor_quantization": "tensor-wise", "channel_quantization": "channel-wise",
    "reduced_feedforward": "reduced FFN", "attention_probability_8bit": "8-bit attn. prob.",
    "gradual_budget": "gradual budget", "fixed_width_recovery": "fixed-width recovery",
    "knowledge_distillation": "distillation",
}


def load_current():
    meta = read_json(ABL_JSON)
    man = read_json(f"{ABL_DIR}/manifest.json")
    by_sha = {r["checkpoint_sha256"]: r for r in man["runs"]}
    lab = np.load(src(f"{ABL_DIR}/labels.npz"))
    y_test, y_val = lab["test"], lab["validation"]
    assert y_test.shape[0] == meta["n_test"] and y_val.shape[0] == meta["n_validation"]
    status = read_json(ABL_STATUS)
    horizon = {r["arm"]: (r.get("latest_epoch_metrics") or {}).get("training_horizon_epochs") for r in status["runs"]}
    status_rec = {r["arm"]: (r.get("status"), r.get("completed_epochs")) for r in status["runs"]}
    full = max(v for v in horizon.values() if v) if any(horizon.values()) else None
    rows = []
    for r in meta["runs"]:
        m = by_sha.get(r["checkpoint_sha256"])
        if m is None:
            rows.append(dict(arm=r["arm"], name=ARM_NAMES.get(r["arm"], r["arm"]), missing=True))
            continue
        d = np.load(src(f"{ABL_DIR}/{m['arm']}.npz"))
        pt, pv = softmax(d["test_logits"]), softmax(d["validation_logits"])
        interim = not m.get("complete", True)
        planned = horizon.get(r["arm"]) or full
        tag = f"selected from an interim snapshot at epoch {m['completed_epochs']:,} of {planned:,}" if interim else ""
        plot_tag = (f"selected from an interim\nsnapshot at epoch {m['completed_epochs']:,} of {planned:,}"
                    if interim else "")
        rows.append(dict(
            arm=r["arm"], interim=interim, snapshot_epochs=m["completed_epochs"], planned_epochs=planned,
            manifest_complete=m.get("complete"), json_status=r["status"], status_file=status_rec.get(r["arm"]),
            name=ARM_NAMES.get(r["arm"], r["arm"]) + (f" ({tag})" if interim else ""),
            short=ARM_SHORT.get(r["arm"], r["arm"]) + (f" ({tag})" if interim else ""),
            plot_label=ARM_SHORT.get(r["arm"], r["arm"]) + (f" ({plot_tag})" if interim else ""),
            file=f"{ABL_DIR}/{m['arm']}.npz", missing=False,
            ebops=r["ebops"], ebops_manifest=m["ebops"]["total"], epochs=r["completed_epochs"],
            sel_epoch=r["selected_epoch_one_based"], status=r["status"],
            test_auc=macro_auc(y_test, pt), test_acc=top1(y_test, pt), test_cls=class_aucs(y_test, pt),
            val_auc=macro_auc(y_val, pv), val_acc=top1(y_val, pv),
            claim_test_auc=r["test_macro_auc"], claim_test_acc=r["test_accuracy"],
            claim_val_auc=r["selected_val_macro_auc"], claim_val_acc=r["validation_accuracy"],
            probs=pt))
    feats = meta["input"]["features"]
    return dict(rows=rows, y_test=y_test, budget=meta["budget_ebops"], n_test=meta["n_test"],
                n_val=meta["n_validation"], n_part=meta["input"]["particles"], features=feats,
                selection=meta["selection"], test_split=meta["test_split"],
                val_split=meta["validation_split"], eval_date=meta["evaluation_date"],
                train_done_date=meta.get("training_completion_date"))


HEAD_NPZ = "campaigns/2026-09-16-accuracy-investigation/head-features/head_test_predictions.npz"
FROZEN_JSON = "publication/results/post_conference/frozen_output_results.json"


def load_head_refit(y_test):
    """Frozen-backbone follow-up on the channel-wise checkpoint: final layer refit at 8 bits."""
    h = np.load(src(HEAD_NPZ))
    fr = read_json(FROZEN_JSON)
    lab = h["labels"]
    assert np.array_equal(lab, y_test.argmax(1)), "head-refit labels differ from the held-out labels"
    y = np.eye(y_test.shape[1])[lab]
    pb, ps = softmax(h["baseline"]), softmax(h["selected"])
    cb = (pb.argmax(1) == lab).astype(float)
    cs = (ps.argmax(1) == lab).astype(float)
    d = cs - cb
    se = d.std(ddof=1) / np.sqrt(len(d))
    z = stats.norm.ppf(0.975)
    ref = fr["frozen_head_refit"]
    return dict(auc=macro_auc(y, ps), acc=cs.mean(), base_auc=macro_auc(y, pb), base_acc=cb.mean(),
                d_acc=d.mean(), lo=d.mean() - z * se, hi=d.mean() + z * se, n=len(lab),
                ebops=ref["ebops"], base_ebops=fr["baseline"]["ebops"], bits=ref["bits"],
                claim_auc=ref["test_macro_auc"], claim_acc=ref["test_accuracy"],
                claim_ci=ref["independent_verification"]["selected_vs_R1_paired"]["ci95"],
                model=ref["model"])


CONF_EVAL = "campaigns/2026-09-23-confirmation/evaluation-results.json"


def load_confirmation_reported():
    d = read_json(CONF_EVAL)
    out = []
    for r in d["runs"]:
        ho, va, sel = r["held_out"], r["validation"], r["selected"]
        out.append(dict(arm=r["arm"], ebops=sel["ebops"], epoch0=sel["epoch"],
                        ho_acc=ho["categorical_accuracy"], ho_auc=ho["macro_ovr_auc"],
                        va_acc=va["categorical_accuracy"], va_auc=va["macro_ovr_auc"],
                        n_ho=int(np.sum(ho["confusion_matrix"])), n_va=int(np.sum(va["confusion_matrix"]))))
    return dict(rows=out, job=d["job"], scope=d["scope"])


# ----------------------------------------------------------------------------------------
# pT reweighting study (2026-09-25): Round-14 N = 8 W1A8 configuration, 3 arms x 8 seeds
# ----------------------------------------------------------------------------------------
PTW = "bnjettag/roc-results/ptw-n8"
PTW_ARMS = ["BASE", "PTW5", "PTWNC"]


def load_ptw():
    seeds = list(range(1, 9))
    per, bins = {}, {}
    y0 = pt0 = edges = b = None
    for a in PTW_ARMS:
        for s in seeds:
            d = np.load(src(f"{PTW}/{a}-s{s}.npz"))
            y, sc, pt = d["y"], d["score"], d["j_pt"]
            if y0 is None:
                y0, pt0 = y, pt
                # VERIFY.md method: exact held-out sextiles of j_pt, rounded to 1 GeV
                edges = np.round(np.quantile(pt0, [k / 6 for k in range(1, 6)]))
                b = np.digitize(pt0, edges)
            assert np.array_equal(y, y0) and np.array_equal(pt, pt0), f"split differs in {a}-s{s}"
            per[(a, s)] = dict(auc=macro_auc(y, sc), acc=top1(y, sc))
            bins[(a, s)] = [macro_auc(y0[b == i], sc[b == i]) for i in range(6)]
    summ = read_json(f"{PTW}/summary.json")
    arr = {a: {k: np.array([per[(a, s)][k] for s in seeds]) for k in ("auc", "acc")} for a in PTW_ARMS}
    gaps = {}
    for a in ("PTW5", "PTWNC"):
        for k in ("auc", "acc"):
            gaps[(a, k)] = t_interval(arr[a][k] - arr["BASE"][k])
            gaps[(a, k)]["per_seed"] = arr[a][k] - arr["BASE"][k]
    bin_gaps = {a: [t_interval(np.array([bins[(a, s)][i] - bins[("BASE", s)][i] for s in seeds]))
                    for i in range(6)] for a in ("PTW5", "PTWNC")}
    counts = [int((b == i).sum()) for i in range(6)]
    lo_e = [float(pt0.min())] + edges.tolist()
    hi_e = edges.tolist() + [float(pt0.max())]
    claim = {a: summ["arms"][a]["auc"]["values"] for a in PTW_ARMS if a in summ.get("arms", {})}
    meta = json.loads(str(np.load(src(f"{PTW}/BASE-s1.npz"))["meta"]))
    return dict(per=per, arr=arr, gaps=gaps, bin_gaps=bin_gaps, counts=counts, lo=lo_e, hi=hi_e,
                seeds=seeds, n=len(y0), claim=claim, meta=meta)


# ----------------------------------------------------------------------------------------
# archived: Round 14 fixed-precision study (no EBOP target), ROC-test arrays
# ----------------------------------------------------------------------------------------
R14 = "bnjettag/roc-results/r14"
R14_VARIANTS = ["FP32", "W8A8", "W1A8", "W1A6", "W1A4"]
R14_NS = [8, 16, 32, 64]
R14_ROW = re.compile(r"^\|\s*(fp32|w8a8|w1a8|w1a6|w1a4)\s*\|.*\*\*([0-9.]+)±([0-9.]+)\*\*", re.M)


def load_r14(roc_n=8, roc_seed=3):
    per, claims, roc = {}, {}, {}
    for N in R14_NS:
        txt = src(f"{R14}/n{N}/roc_auc.md").read_text()
        claims[N] = {m.group(1).upper(): (float(m.group(2)), float(m.group(3))) for m in R14_ROW.finditer(txt)}
        for v in R14_VARIANTS:
            for s in (1, 2, 3):
                d = np.load(src(f"{R14}/n{N}/{v}-s{s}.npz"))
                y, sc = d["y"], d["score"]
                per[(N, v, s)] = dict(auc=macro_auc(y, sc), acc=top1(y, sc), n=len(y))
                if N == roc_n and s == roc_seed:
                    roc[v] = (y, sc)
    return dict(per=per, claims=claims, roc=roc, roc_n=roc_n, roc_seed=roc_seed)


# ----------------------------------------------------------------------------------------
# archived hardware: C-synthesis (Vitis HLS) and Vivado OOC reports
# ----------------------------------------------------------------------------------------
SYN = "bnjettag/results/synthesis/runs"
BUILD_SHORT = {  # plain labels for slides; text only
    "40103802/fp32-s3-r14n8-w16/csynth_rf1": "FP32-trained, 16-bit datapath",
    "40103802/fp32-s3-r14n8-w8/csynth_rf1": "FP32-trained, rounded to W = 8",
    "9cc6e336/w8a8-s3-r14n8/csynth_rf1": "W8A8",
    "38a20c62/w1a8-s3-r14n8/csynth_rf1": "W1A8, constant multiplies on DSPs",
    "38a20c62/w1a8-s3-r14n8/csynth_rf1_fabric": "W1A8, multiplies moved to fabric",
    "794e925f/w1a6-s3/csynth_rf1": "W1A6",
    "5f839ab5/w1a4-s3/csynth_rf1": "W1A4",
    "38a20c62/w1a8-s3-r14n8-pf1fab/csynth_pf1fab": "W1A8 folded, fabric",
    "38a20c62/w1a8-s3-r14n8-pf1scoped/csynth_pf1scoped": "W1A8 folded, scoped fabric",
    "38a20c62/w1a8-s3-r14n8-beta1sm4i0/csynth_beta1sm4i0": "folded, 4-bit softmax, not retrained",
    "ba72a91a/w1a8-s3-r15gamma-sm4i0-pf1scoped/csynth_pf1scoped": "folded, retrained for 4-bit softmax",
}
BUILDS = [  # (report dir, label, family, group); text only, every number comes from the report
    ("40103802/fp32-s3-r14n8-w16/csynth_rf1", "FP32-trained, 16-bit fixed-point datapath", "FP32", "ladder"),
    ("40103802/fp32-s3-r14n8-w8/csynth_rf1", "FP32-trained, rounded to W = 8 after training (9-bit weight type)", "FP32", "ladder"),
    ("9cc6e336/w8a8-s3-r14n8/csynth_rf1", "W8A8", "W8A8", "ladder"),
    ("38a20c62/w1a8-s3-r14n8/csynth_rf1", "W1A8, constant multiplies on DSPs (default binding)", "W1A8", "ladder"),
    ("38a20c62/w1a8-s3-r14n8/csynth_rf1_fabric", "W1A8, multiplies bound to fabric", "W1A8", "ladder"),
    ("794e925f/w1a6-s3/csynth_rf1", "W1A6", "W1A6", "ladder"),
    ("5f839ab5/w1a4-s3/csynth_rf1", "W1A4", "W1A4", "ladder"),
    ("38a20c62/w1a8-s3-r14n8-pf1fab/csynth_pf1fab", "W1A8 folded, fabric binding", "W1A8", "folded"),
    ("38a20c62/w1a8-s3-r14n8-pf1scoped/csynth_pf1scoped", "W1A8 folded, scoped fabric binding", "W1A8", "folded"),
    ("38a20c62/w1a8-s3-r14n8-beta1sm4i0/csynth_beta1sm4i0", "W1A8 folded, 4-bit softmax operand, not retrained", "W1A8", "folded"),
    ("ba72a91a/w1a8-s3-r15gamma-sm4i0-pf1scoped/csynth_pf1scoped", "W1A8 folded, retrained on the 4-bit softmax grid (r15-gamma)", "W1A8", "folded"),
    ("38a20c62/w1a8-s3-r14n8-pf1sm1df/csynth_pf1sm1df", "W1A8 folded dataflow (pf1 sm1)", "W1A8", "other"),
    ("38a20c62/w1a8-s3-r14n8-pf2sm2df/csynth_pf2sm2df", "W1A8 folded dataflow (pf2 sm2)", "W1A8", "other"),
    ("38a20c62/w1a8-s3-r14n8-da13/csynth_da13", "W1A8 da13 (closed lever)", "W1A8", "other"),
    ("38a20c62/w1a8-s3-r14n8-relufix/csynth_relufix", "W1A8 relufix (closed lever)", "W1A8", "other"),
]


def load_csynth():
    rows = []
    for rel, label, fam, grp in BUILDS:
        d = read_json(f"{SYN}/{rel}/csynth_report.json")
        av = d["avail"]
        clk = float(d["target_clock_ns"])
        rows.append(dict(dir=rel, label=label, short=BUILD_SHORT.get(rel, label), family=fam, group=grp, part=d["part"],
                         LUT=d["LUT"], FF=d["FF"], DSP=d["DSP"], BRAM=d["BRAM_18K"], URAM=d["URAM"],
                         LUT_pct=100 * d["LUT"] / av["LUT"], FF_pct=100 * d["FF"] / av["FF"],
                         DSP_pct=100 * d["DSP"] / av["DSP"], BRAM_pct=100 * d["BRAM_18K"] / av["BRAM_18K"],
                         lat_cyc=d["LatencyWorst"], lat_us=d["LatencyWorst"] * clk / 1000.0, clk=clk,
                         est_clk=float(d["estimated_clock_ns"]), II=d["IntervalMin"], avail=av))
    return rows


def load_vivado(avail_lut):
    rows = []
    base = REPO / SYN
    for rpt in sorted(base.glob("*/*/postsyn_*/post_*_util.rpt")):
        stage = "post-opt" if rpt.name.startswith("post_opt") else "post-synth"
        if stage == "post-synth" and (rpt.parent / "post_opt_util.rpt").exists():
            continue
        txt = src(rpt).read_text()
        # utilisation rows: | name | used | fixed | prohibited | available | util% |
        lut = re.search(r"^\|\s*CLB LUTs\*?\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)", txt, re.M)
        dsp = re.search(r"^\|\s*DSPs\s*\|\s*(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*(\d+)", txt, re.M)
        dev = re.search(r"^\|\s*Device\s*:\s*(\S+)", txt, re.M)
        clk = None
        for f in [rpt.parent / "clock.xdc"] + sorted(rpt.parent.glob("*.tcl")):
            if f.exists():
                m = re.search(r"create_clock\s+-period\s+([\d.]+)", src(f).read_text(errors="replace"))
                if m:
                    clk = float(m.group(1))
                    break
        demand = None  # Vivado's own DSP demand line when the proxy part overflows
        for f in sorted(rpt.parent.glob("vivado*")):
            hits = re.findall(r"\[Synth 8-3323\] Resources of type DSP have been overutilized\. Used = (\d+)",
                              src(f).read_text(errors="replace"))
            if hits:
                demand = int(hits[-1])
        wns = None
        tim = rpt.parent / rpt.name.replace("_util", "_timing")
        if tim.exists():
            m = re.search(r"WNS\(ns\)\s+TNS\(ns\).*\n\s*-+.*\n\s*(-?[\d.]+)", src(tim).read_text())
            wns = float(m.group(1)) if m else None
        build = str(rpt.parent.relative_to(base))
        rows.append(dict(build=build, stage=stage, device=dev.group(1) if dev else "?",
                         LUT=int(lut.group(1)) if lut else None, LUT_avail=int(lut.group(2)) if lut else None,
                         DSP=int(dsp.group(1)) if dsp else None, DSP_avail=int(dsp.group(2)) if dsp else None,
                         DSP_demand=demand,
                         LUT_vu13p_pct=100 * int(lut.group(1)) / avail_lut if lut else None,
                         clk=clk, wns=wns))
    return rows


# ----------------------------------------------------------------------------------------
# telemetry: Chang-recipe (Sun et al.) regime-B pilots, per-arm logs
# ----------------------------------------------------------------------------------------
CHANG_LOGS = "campaigns/2026-09-26-training-batch/logs"
CHANG_STUDY = "campaigns/2026-09-26-training-batch/STUDY.md"
CHANG_FILE = re.compile(r"^chang0926-(?P<arm>.+)-n(?P<n>\d+)-s(?P<seed>\d+)-(?P<rest>.+)\.log$")
STAMP = re.compile(r"(\d{8}T\d{4,6})Z")
EPOCH_LINE = re.compile(r"^\[epoch (\d+)/(\d+)\] (.*)$")
KV = re.compile(r"(\w+)=(\S+)")


def _num(v):
    try:
        return float(v)
    except ValueError:
        return None


def arm_label(arm: str, seed: str) -> str:
    return {"cprime": "C′"}.get(arm, arm.upper()) + f"-s{seed}"


def load_chang():
    study = src(CHANG_STUDY).read_text()
    m = re.search(r"\[D8\][^\n]*?n_val ([\d,]+)", study)
    n_val = int(m.group(1).replace(",", "")) if m else None
    newest: dict[tuple, tuple] = {}
    for p in sorted((REPO / CHANG_LOGS).glob("chang0926-*.log")):
        fm = CHANG_FILE.match(p.name)
        if not fm:
            continue
        st = STAMP.search(fm.group("rest"))
        key = (fm.group("arm"), fm.group("seed"), fm.group("n"))
        rank = (st.group(1) if st else "", p.stat().st_mtime)
        if key not in newest or rank > newest[key][0]:
            newest[key] = (rank, p)
    arms = []
    for (arm, seed, n), (rank, p) in sorted(newest.items()):
        rows, attempts, total, target, verified = {}, 0, None, None, None
        for line in src(p).read_text(errors="replace").splitlines():
            if line.startswith("==== ARM_ATTEMPT"):
                attempts += 1
            if line.startswith("CHECKPOINT_VERIFICATION_PASS "):
                try:
                    verified = json.loads(line.split(" ", 1)[1])
                except ValueError:
                    verified = {"unparsed": True}
            em = EPOCH_LINE.match(line)
            if not em:
                continue
            kv = dict(KV.findall(em.group(3)))
            total = int(em.group(2))
            target = _num(kv.get("target", "nan")) or target
            rows[int(em.group(1))] = dict(  # last occurrence per epoch wins (resumed attempts)
                traced=_num(kv.get("EBOPs", "untraced")), in_training=_num(kv.get("in_training_ebops", "x")),
                val_auc=_num(kv.get("val_AUC", "x")), val_acc=_num(kv.get("val_accuracy", "x")),
                feasible=_num(kv.get("feasible", "x")), degenerate=_num(kv.get("degenerate", "x")))
        ep = np.array(sorted(rows))
        col = lambda k: np.array([rows[e][k] if rows[e][k] is not None else np.nan for e in ep])  # noqa: E731
        arms.append(dict(arm=arm, seed=seed, n_part=int(n), label=arm_label(arm, seed), file=str(p.relative_to(REPO)),
                         epoch=ep, traced=col("traced"), in_training=col("in_training"), val_acc=col("val_acc"),
                         val_auc=col("val_auc"), feasible=col("feasible"), degenerate=col("degenerate"),
                         attempts=attempts, total=total, target=target, verified=verified, copy_stamp=rank[0],
                         pod=(lambda m: f"K={m.group(1)} pod" if m else "?")(re.search(r"pilotb(\d+)", p.name))))
    return dict(arms=arms, n_val=n_val)


READOUT_B3 = "campaigns/2026-09-26-training-batch/readout/b3/readout-epoch-0500-42abed-b3"


def load_readout_b3():
    """The K=3 pod's epoch-500 readout: EBOPs certification and the attention-state readout."""
    cert = read_json(f"{READOUT_B3}/certify-snapshot-0500.json")
    ent = read_json(f"{READOUT_B3}/a26-entropy-epoch-0500.json")
    return dict(cert=cert, ent=ent)


# ----------------------------------------------------------------------------------------
# telemetry: GPU benchmark (2026-09-29) and the Delta A07 memory canary
# ----------------------------------------------------------------------------------------
BENCH = "campaigns/2026-09-29-gpu-benchmark/logs"


def load_bench():
    rows = []
    for p in sorted((REPO / BENCH).glob("*/*.log")):
        txt = src(p).read_text(errors="replace")
        prod = re.search(r"^BENCH_POD \S+ product (\S+)", txt, re.M)
        stop = re.search(r"stop_after (\d+)", txt)
        if not (prod and stop):
            continue
        starts = {m.group(1): (m.group(2), int(m.group(3)))
                  for m in re.finditer(r"^PHASE_START (\S+) class (\S+) k (\d+)", txt, re.M)}
        for m in re.finditer(r"^PHASE_DONE (\S+) wall_seconds ([\d.]+) outcomes (\{[^}]*\}) "
                             r"steady_cores ([\d.]+) per_arm ([\d.]+)", txt, re.M):
            cls, k = starts[m.group(1)]
            wall, ep = float(m.group(2)), int(stop.group(1))
            rows.append(dict(product=prod.group(1), job=p.parent.name, phase=m.group(1), cls=cls, k=k,
                             wall=wall, epochs=ep, ok=json.loads(m.group(3)).get("ok", 0),
                             cores_per_arm=float(m.group(5)), arm_epochs_per_h=k * ep * 3600.0 / wall))
    return rows


DELTA_LOGS = "campaigns/2026-09-27-delta-screen/logs"


def load_delta_canary():
    kfiles = sorted((REPO / DELTA_LOGS).glob("*_k_result.json"))
    if not kfiles:
        return None
    kf = kfiles[-1]
    k = read_json(kf)
    ph = {name: v for name, v in k["phases"].items() if v.get("n_samples")}
    samples = kf.with_name(kf.name.replace("_k_result.json", "_gpu_samples.csv"))
    series = {}
    if samples.exists():
        with open(src(samples)) as fh:
            for row in csv.reader(fh):
                if len(row) >= 6 and row[2] == "gpu" and row[1]:
                    series.setdefault(row[1], []).append((int(row[0]), float(row[5]), float(row[4])))
    return dict(file=str(kf.relative_to(REPO)), phases=ph, series=series, k_by_class=k.get("k_by_class"),
                rule=k.get("rule_fraction"), note=k.get("note"))


CONST_DOC = "publication/docs/current-work/CONSTITUENT_SCREEN_20260923.md"


def load_constituent():
    txt = src(CONST_DOC).read_text()
    counts = re.findall(r"^\|\s*(\*{0,2}[A-Za-z][^|]*?\*{0,2})\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|\s*$", txt, re.M)
    verdict = re.search(r"\*\*(No trained case recorded a feasible checkpoint[^*]*)\*\*", txt)
    return dict(counts=[(a.strip("* "), int(b)) for a, b in counts], verdict=verdict.group(1) if verdict else None)


# ----------------------------------------------------------------------------------------
# figures
# ----------------------------------------------------------------------------------------
STATUS_CURRENT = "Status: verified (recomputed here from saved arrays); this campaign has no VERIFY.md."
PTW_PLAIN = {"PTW5": "pT-weighted, cap 5", "PTWNC": "pT-weighted, no cap", "BASE": "unweighted"}
CHANG_PLAIN = {"a": "E model", "d": "E model, our optimizer", "f": "E model + learned positions",
               "e1": "E model, one head", "a07-350": "A07 model", "c": "A07 model",
               "cprime": "A07 model, old quantizer"}
CHANG_KEY = ("E: the small binary model (Chang-sized); A07: the wider binary model with learned positions. "
             "Every arm runs the Sun et al. schedule; arm codes as in the training-batch STUDY.md.")


def short_target(t) -> str:
    return f"{t / 1e6:g}M" if t >= 1e6 else f"{t / 1e3:g}k"


def _current_line(cur, rows):
    n_under = sum(r["ebops"] <= cur["budget"] for r in rows)
    lead = "All " if n_under == len(rows) else ""
    return (f"Current era, EBOP-constrained: N = {cur['n_part']} ({', '.join(cur['features'])}), binary weights. "
            f"{lead}{n_under} of {len(rows)} checkpoints at or under {cur['budget']:,} EBOPs. "
            "One seed per arm, so the order is not a ranking.")


def _heldout_line(cur, rows):
    tail = (" Open marker: checkpoint selected from an interim snapshot, not from the end of training."
            if any(r["interim"] for r in rows) else "")
    return (f"Held-out (ROC-test) split: n = {cur['n_test']:,} jets never used in training or checkpoint selection."
            f"{tail} Source: {ABL_DIR}.")


def fig_current_vs_ebops(cur, metric="auc"):
    rows = [r for r in cur["rows"] if not r["missing"]]
    fig, ax = plt.subplots(figsize=(10.0, 5.0))
    x = np.array([r["ebops"] for r in rows])
    if metric == "auc":
        y = np.array([r["test_auc"] for r in rows])
        ax.set_ylabel(f"held-out (ROC-test)\nmacro-OvR AUC\n(n = {cur['n_test']:,})")
    else:
        y = 100 * np.array([r["test_acc"] for r in rows])
        ax.set_ylabel(f"held-out (ROC-test) top-1\naccuracy [%] (n = {cur['n_test']:,})")
    interim = np.array([r["interim"] for r in rows])
    ax.scatter(x[~interim], y[~interim], color=INK, zorder=3)
    if interim.any():
        ax.scatter(x[interim], y[interim], facecolors="white", edgecolors=INK, linewidths=2.5, zorder=3)
    budget = cur["budget"]
    lo = min(x.min(), budget)
    span = budget - lo + 1
    ax.set_xlim(lo - 0.35 * span, budget + 0.06 * span)
    ax.axvline(budget, color=INK, ls="--", lw=1.5)
    ax.text(budget, ax.get_ylim()[1], f"target {budget:,} ", rotation=90, ha="right", va="top", fontsize="small")
    ax.set_xlabel("EBOPs of the selected checkpoint (lower is cheaper)")
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v / 1e3:.0f}k"))
    label_points(ax, x, y, [r["plot_label"] for r in rows])
    name = "fig01_current_auc_vs_ebops" if metric == "auc" else "fig02_current_accuracy_vs_ebops"
    return save(fig, name, f"{STATUS_CURRENT}\n{_current_line(cur, rows)}\n{_heldout_line(cur, rows)}")


def fig_current_roc(cur, best):
    y = cur["y_test"]
    styles = {"g": dict(color=INK, ls="-"), "q": dict(color=INK, ls="--"), "W": dict(color=INK, ls=":"),
              "Z": dict(color=GREY, ls="-.", marker="s", markevery=0.09, ms=8), "t": dict(color=GREY, ls="-")}
    fig, ax = plt.subplots(figsize=(10.0, 5.2))
    for c, cname in enumerate(CLASSES):
        eff, mistag = roc_points(y[:, c], best["probs"][:, c])
        ok = mistag > 0
        ax.plot(eff[ok], mistag[ok], label=f"{cname} vs rest, AUC {best['test_cls'][c]:.3f}", **styles[cname])
    ax.set_yscale("log")
    ax.set_xlim(0, 1)
    ax.set_xlabel("tagging efficiency (TPR), held-out (ROC-test)")
    ax.set_ylabel("mistag rate (FPR),\nheld-out (ROC-test)")
    ax.legend(loc="lower right")
    return save(fig, "fig03_current_roc_best_auc",
                f"{STATUS_CURRENT}\n{best['name']}: the arm with the highest validation AUC ({best['val_auc']:.4f}, "
                f"n = {cur['n_val']:,}), drawn on the held-out (ROC-test) split, n = {cur['n_test']:,}; one seed, single run. "
                f"Current era, N = {cur['n_part']}, {best['ebops']:,} EBOPs (target {cur['budget']:,}). Source: {ABL_DIR}.")


PTW_CAVEAT = ("Metric and comparison were fixed after the results: the arithmetic is verified, "
              "not a pre-registered test (the campaign's VERIFY.md).")


def fig_ptw_gaps(ptw, name="fig05_ptw_paired_gaps"):
    fig, axes = plt.subplots(1, 2, figsize=(13.0, 5.0))
    ns = len(ptw["seeds"])
    for ax, key in ((axes[0], "auc"), (axes[1], "acc")):
        scale = 1.0 if key == "auc" else 100.0
        for j, a in enumerate(("PTW5", "PTWNC")):
            g = ptw["gaps"][(a, key)]
            xs = np.full(len(g["per_seed"]), j) + np.linspace(-0.12, 0.12, len(g["per_seed"]))
            ax.scatter(xs, scale * g["per_seed"], color=GREY, s=45, zorder=2)
            ax.errorbar([j + 0.3], [scale * g["mean"]], yerr=[[scale * (g["mean"] - g["lo"])], [scale * (g["hi"] - g["mean"])]],
                        fmt="o", color=INK, zorder=3)
        ax.axhline(0, color=INK, lw=1.5)
        ax.set_xticks([0.1, 1.1])
        ax.set_xticklabels([PTW_PLAIN[a].replace("pT-weighted, ", "weights, ") for a in ("PTW5", "PTWNC")])
        ax.set_xlim(-0.5, 1.6)
    fig.supxlabel("pT-weighted arm minus the unweighted arm, paired by seed")
    axes[0].set_ylabel(f"Δ macro-OvR AUC\nheld-out (ROC-test)\nn = {ptw['n']:,}")
    axes[1].set_ylabel(f"Δ top-1 accuracy [pp]\nheld-out (ROC-test)\nn = {ptw['n']:,}")
    fig.tight_layout(w_pad=2.0)
    return save(fig, name,
                f"{PTW_CAVEAT}\npT reweighting study: Round-14 configuration (N = 8, W1A8), no EBOP target; verified, "
                f"recomputed here from the saved arrays. Grey: one point per seed ({ns} seeds, paired by seed); black: mean "
                f"with 95 % t-interval (df {ns - 1}). Source: {PTW}.")


def fig_ptw_bins(ptw, name="fig06_ptw_pt_bins"):
    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    xs = np.arange(6)
    for off, a, col in ((-0.12, "PTW5", INK), (0.12, "PTWNC", GREY)):
        g = ptw["bin_gaps"][a]
        m = np.array([t["mean"] for t in g])
        ax.errorbar(xs + off, m, yerr=[m - np.array([t["lo"] for t in g]), np.array([t["hi"] for t in g]) - m],
                    fmt="o", color=col, label=f"{PTW_PLAIN[a]} minus unweighted")
    ax.axhline(0, color=INK, lw=1.5)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{lo:.0f}–{hi:.0f}" for lo, hi in zip(ptw["lo"], ptw["hi"])], rotation=20)
    ax.set_xlabel(r"jet $p_\mathrm{T}$ bin [GeV], held-out (ROC-test) sextiles")
    ax.set_ylabel("Δ macro-OvR AUC\nin the bin, held-out\n(ROC-test)")
    ax.legend(loc="upper center")
    return save(fig, name,
                f"{PTW_CAVEAT} The binning was also chosen after the results: descriptive, not a test.\n"
                f"pT reweighting study: Round-14 configuration (N = 8, W1A8), no EBOP target. About "
                f"{min(ptw['counts']):,}–{max(ptw['counts']):,} jets per bin; mean over {len(ptw['seeds'])} seeds, "
                f"95 % paired t-interval. Source: {PTW}.")


def fig_chang(ch, what="ebops", status=None, name=None):
    arms = ch["arms"]
    ncol = 4
    nrow = int(np.ceil(len(arms) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(14.0, 2.5 * nrow), sharex=True, sharey=True, squeeze=False)
    if what == "ebops":
        floor = min(min(np.nanmin(a["in_training"]), np.nanmin(a["traced"]), a["target"] or np.inf) for a in arms)
        top = max(max(np.nanmax(a["in_training"]), np.nanmax(a["traced"])) for a in arms)
        axes[0, 0].set_ylim(floor / 4.0, top * 2.0)
    for ax, a in zip(axes.flat, arms):
        code = {"cprime": "C′"}.get(a["arm"], a["arm"].upper())
        tgt = short_target(a["target"]) if a["target"] else "?"
        if what == "ebops":
            ok = ~np.isnan(a["in_training"])
            ax.plot(a["epoch"][ok], a["in_training"][ok], color=GREY, lw=2.0, label="in-training estimate")
            ok = ~np.isnan(a["traced"])
            ax.plot(a["epoch"][ok], a["traced"][ok], "o", color=INK, ms=6, label="traced EBOPs (periodic full trace)")
            if a["target"]:
                ax.axhline(a["target"], color=INK, ls="--", lw=1.5, label="EBOPs target")
                last = a["in_training"][~np.isnan(a["in_training"])][-1]
                below = last >= a["target"]  # data above the line: write under it, and the reverse
                ax.text(0.98, a["target"], f"target {tgt}", transform=matplotlib.transforms.blended_transform_factory(
                    ax.transAxes, ax.transData), ha="right", va="top" if below else "bottom", fontsize="small")
            ax.set_yscale("log")
        else:
            ok = ~np.isnan(a["val_acc"])
            ax.plot(a["epoch"][ok], 100 * a["val_acc"][ok], color=INK, lw=2.0)
        ax.text(0.0, 1.04, f"{CHANG_PLAIN.get(a['arm'], a['arm'])}\ntarget {tgt}, seed {a['seed']}",
                transform=ax.transAxes, ha="left", va="bottom", fontsize="small")
    for ax in axes.flat[len(arms):]:
        ax.set_visible(False)
    for ax in axes[-1]:
        ax.set_xlabel("epoch")
    fig.supylabel("EBOPs (log scale)" if what == "ebops" else "validation top-1 accuracy [%]")
    fig.tight_layout(h_pad=1.0)
    if what == "ebops":
        hd, lb = axes.flat[0].get_legend_handles_labels()
        fig.legend(hd, lb, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3)
    order = ", ".join(f"{ {'cprime': 'C′'}.get(a['arm'], a['arm'].upper()) }" for a in arms)
    n_part = arms[0]["n_part"] if arms else "?"
    tot = arms[0]["total"] if arms else "?"
    tail = ("The pre-registered readout at epoch 500, not this plot, decides feasibility." if what == "ebops" else
            f"Validation = the pilots' internal split, n = {ch['n_val']:,}; the readout at epoch 500 decides.")
    lead = status or "Pilot telemetry, not a result"
    return save(fig, name or f"fig0{7 if what == 'ebops' else 8}_chang_pilot_{'ebops' if what == 'ebops' else 'valacc'}",
                f"{lead}: Chang-recipe (Sun et al.) regime-B pilots, N = {n_part}, one seed per panel, "
                f"schedule {tot:,} epochs, newest saved per-arm logs (source: {CHANG_LOGS}). {tail}\n{CHANG_KEY} "
                f"Panels left to right, top to bottom: arms {order}.")


def fig_bench(rows):
    classes = [c for c in ("E", "A07") if any(r["cls"] == c for r in rows)]
    nmax = max(sum(r["cls"] == c for r in rows) for c in classes)
    fig, axes = plt.subplots(1, len(classes), figsize=(14.0, 1.3 + 0.7 * nmax), squeeze=False)
    header = {"E": "E model (small binary model)", "A07": "A07 model (wider binary model)"}
    vmax = max(r["arm_epochs_per_h"] for r in rows)
    for ax, c in zip(axes[0], classes):
        sub = [r for r in rows if r["cls"] == c]
        ypos = np.arange(len(sub))
        vals = [r["arm_epochs_per_h"] for r in sub]
        ax.barh(ypos, vals, color=INK if c == "E" else GREY)
        for yv, v in zip(ypos, vals):
            ax.text(v, yv, f" {v:.0f}", va="center", fontsize="small")
        ax.set_yticks(ypos)
        ax.set_yticklabels([f"{r['product'].replace('NVIDIA-', '').replace('GeForce-', '')}, {r['k']} per GPU"
                            for r in sub])
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="y", visible=False)
        ax.invert_yaxis()
        ax.set_xlim(0, vmax * 1.25)
        ax.set_xlabel("arm-epochs per wall-clock hour")
        ax.text(0.0, 1.03, header[c], transform=ax.transAxes, ha="left", va="bottom")
    fig.tight_layout(w_pad=2.0)
    return save(fig, "fig09_gpu_benchmark_throughput",
                f"Benchmark telemetry, provisional: {len(rows)} phases from the saved pod logs (source: {BENCH}). "
                "K arms of one model share one GPU; rate = K × epochs per arm / phase wall time, start-up included.\n"
                "No product ranking: the benchmark decides on projected finish time at the GPUs that can schedule, "
                "with its gates met (its STUDY.md).")


def fig_delta_memory(dc):
    if not dc or not dc["series"]:
        return None
    name, pts = max(dc["series"].items(), key=lambda kv: len(kv[1]))
    ph = dc["phases"].get(name, {})
    t0 = pts[0][0]
    t = np.array([(p[0] - t0) / 60.0 for p in pts])
    used = np.array([p[1] for p in pts])
    card = pts[0][2]
    fig, ax = plt.subplots(figsize=(10.0, 5.0))
    ax.plot(t, used / 1024.0, color=INK, lw=2.5, label="GPU memory used by the pod")
    ax.axhline(card / 1024.0, color=INK, ls="--", lw=1.5, label="card memory")
    if dc.get("rule"):
        ax.axhline(dc["rule"] * card / 1024.0, color=GREY, ls=":", lw=2.5,
                   label=f"packing rule ({100 * dc['rule']:.0f} % of card)")
    i = int(np.argmax(used))
    alive = sum(1 for v in ph.get("per_arm", {}).values() if v.get("rss_gate"))
    ax.annotate(f"peak {used[i]:,.0f} MiB while {ph.get('k_tested', '?')} arms start;\none arm ran out of memory, "
                f"{alive} kept training", (t[i], used[i] / 1024.0), xytext=(t.max() * 0.2, card / 1024.0 * 0.5),
                textcoords="data", fontsize="small", arrowprops=dict(arrowstyle="-", color=GREY, lw=1.0))
    ax.set_xlabel("minutes since the first sample of the phase")
    ax.set_ylabel("GPU memory [GiB]")
    ax.set_ylim(0, card / 1024.0 * 1.12)
    ax.legend(loc="lower center")
    gpu = ", ".join(ph.get("gpu_product", ["?"]))
    return save(fig, "fig10_delta_canary_gpu_memory",
                f"Memory-canary telemetry, not a result: {ph.get('k_tested', '?')} arms of the A07 model (the wider binary "
                f"model) on one {gpu}. Out of memory recorded: {'yes' if ph.get('oom') else 'no'}; arms per GPU accepted by "
                f"the canary: {ph.get('k_accepted')}. Source: {dc['file']}.")


def fig_csynth(rows):
    sel = [r for r in rows if r["group"] in ("ladder", "folded")]
    fig, axes = plt.subplots(1, 2, figsize=(14.5, 1.1 + 0.44 * len(sel)), sharey=True)
    ypos = np.arange(len(sel))
    cols = [VARIANT_COLOR[r["family"]] for r in sel]
    dmax = max(r["DSP"] for r in sel)
    axes[0].barh(ypos, [r["DSP"] for r in sel], color=cols)
    axes[0].set_xscale("symlog", linthresh=10)
    axes[0].set_xlim(0, dmax * 1.4)
    column = matplotlib.transforms.blended_transform_factory(axes[0].transAxes, axes[0].transData)
    for yv, r in zip(ypos, sel):
        axes[0].text(1.03, yv, f"{r['DSP']:,} ({r['DSP_pct']:.1f} %)", transform=column, va="center", fontsize="small")
    axes[0].set_xlabel("DSP slices\n(C-synthesis)")
    axes[1].barh(ypos, [r["LUT_pct"] for r in sel], color=cols)
    for yv, r in zip(ypos, sel):
        axes[1].text(r["LUT_pct"], yv, f" {r['LUT'] / 1e6:.2f}M", va="center", fontsize="small")
    axes[1].axvline(100, color=INK, ls="--", lw=1.5)
    axes[1].set_xlabel("LUTs, % of VU13P\n(C-synthesis)")
    axes[1].set_xlim(0, max(r["LUT_pct"] for r in sel) * 1.3)
    for ax in axes:
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels([r["short"] for r in sel])
    axes[0].invert_yaxis()
    fig.tight_layout(w_pad=8.0)
    return save(fig, "fig04_archived_csynth_dsp_lut",
                f"ARCHIVED (Round 14 and its r15-gamma retrain, pre-EBOP-target), N = 8, seed-3 checkpoints: Vitis HLS "
                f"C-synthesis estimates, part {sel[0]['part']}, target clock {sel[0]['clk']} ns. Not implemented hardware. "
                f"'Folded' builds reuse hardware across clock cycles. Numbers beside the DSP bars: count and % of the VU13P; at the "
                f"LUT bar ends: LUT count. Dashed line: 100 % of the VU13P LUTs. Source: {SYN}.")


def fig_r14_roc(r14, classes=("t", "W")):
    fig, axes = plt.subplots(1, len(classes), figsize=(13.0, 5.2), sharey=True)
    for ax, cname in zip(np.atleast_1d(axes), classes):
        c = CLASSES.index(cname)
        for v in R14_VARIANTS:
            y, sc = r14["roc"][v]
            eff, mistag = roc_points(y[:, c], sc[:, c])
            ok = mistag > 0
            auc = float(roc_auc_score(y[:, c], sc[:, c]))
            ax.plot(eff[ok], mistag[ok], color=VARIANT_COLOR[v], label=f"{v}  AUC {auc:.3f}")
        ax.set_yscale("log")
        ax.set_xlim(0, 1)
        ax.set_xlabel(f"{cname}-tagging efficiency (TPR),\nheld-out (ROC-test)")
        ax.legend(loc="lower right")
        ax.text(0.03, 0.95, f"{cname} vs rest", transform=ax.transAxes, ha="left", va="top")
    np.atleast_1d(axes)[0].set_ylabel("mistag rate (FPR),\nheld-out (ROC-test)")
    fig.tight_layout(w_pad=2.0)
    n = r14["per"][(r14["roc_n"], "FP32", r14["roc_seed"])]["n"]
    return save(fig, "fig11_archived_r14_roc_n8",
                f"ARCHIVED (Round 14, fixed precision, no EBOP target): inputs pt, etarel, phirel, N = {r14['roc_n']}, seed "
                f"{r14['roc_seed']} (the synthesized seed), single run per curve. Held-out (ROC-test) split, n = {n:,}; "
                f"recomputed here from the saved arrays; not comparable to the EBOP-constrained runs. Source: {R14}/n{r14['roc_n']}.")
