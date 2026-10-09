#!/usr/bin/env python
"""Trigger-style working points from the stored ROC score arrays (Round 14 + Gamma).

For every (block, arm, seed) .npz -- y one-hot (260000, 5), score (260000, 5),
class order g, q, W, Z, t (verified against the "auc_per_class" field of the npz
meta record) -- compute per class, one-vs-rest:

  (a) signal efficiency TPR at fixed mistag rate FPR = 1% and FPR = 10%
  (b) background rejection 1/FPR at fixed signal efficiency TPR = 0.5 and 0.7

per seed, then seed mean +/- sample sd (ddof=1) over the 3 seeds.  Rejection is
computed per seed as 1/FPR and then averaged (NOT 1/mean-FPR).

Interpolation: sklearn roc_curve, then linear interpolation on the monotone ROC
after de-duplication (for TPR@FPR keep the last point of each FPR plateau, i.e.
the maximum TPR at that FPR; for FPR@TPR keep the first point of each TPR
plateau, i.e. the minimum FPR at that TPR).  If the interpolated FPR at a TPR
target falls below the smallest nonzero FPR on the curve (including exactly 0),
it is clamped to that finite minimum (~1/n_neg) and the cell is flagged as a
lower bound on rejection.

Gate: before a file is used, its per-class and macro one-vs-rest AUCs are
recomputed with sklearn roc_auc_score and asserted against the per-seed row of
the sibling roc_auc.md table to 1e-4.

Inputs  (66 files, enumerated explicitly -- the _dl/, _ckpt_dl/ and
r14-localeval/ stores are out of scope):
  bnjettag/roc-results/r14/n{8,16,32,64}/{FP32,W8A8,W1A8,W1A6,W1A4}-s{1,2,3}.npz
  bnjettag/roc-results/r15-gamma/{sm6i0,sm4i0}/W1A8-s{1,2,3}.npz
    (labelled W1A8-sm6 / W1A8-sm4, N=8)

Outputs:
  bnjettag/results/r14/working_points_r14.json
  bnjettag/results/r14/working_points_r14.md
"""

import datetime
import json
import re
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score, roc_curve

ROOT = Path(__file__).resolve().parents[3]
ROC_ROOT = ROOT / "bnjettag" / "roc-results"
OUT_DIR = ROOT / "bnjettag" / "results" / "r14"

CLASSES = ["g", "q", "W", "Z", "t"]
ARMS_R14 = ["FP32", "W8A8", "W1A8", "W1A6", "W1A4"]
SEEDS = [1, 2, 3]
FPR_TARGETS = [0.01, 0.10]
TPR_TARGETS = [0.5, 0.7]
N_EXPECTED = 260_000
AUC_TOL = 1e-4

# ---------------------------------------------------------------- enumeration
# (block_name, arm_label, npz_dir, npz_file_stem_prefix)
ENTRIES = []
for N in (8, 16, 32, 64):
    for arm in ARMS_R14:
        ENTRIES.append((f"N={N}", arm, ROC_ROOT / "r14" / f"n{N}", arm))
for tag, label in (("sm6i0", "W1A8-sm6"), ("sm4i0", "W1A8-sm4")):
    ENTRIES.append(("Gamma (N=8)", label, ROC_ROOT / "r15-gamma" / tag, "W1A8"))

BLOCK_ORDER = ["N=8", "N=16", "N=32", "N=64", "Gamma (N=8)"]


# ---------------------------------------------------------------- md AUC gate
def parse_per_seed_table(md_path):
    """Return {run_name: {'per_class': [g,q,W,Z,t], 'macro': float}} from the
    '## Per-seed' table of a roc_auc.md file."""
    rows = {}
    in_per_seed = False
    for line in md_path.read_text().splitlines():
        if line.startswith("## "):
            in_per_seed = line.startswith("## Per-seed")
            continue
        if not (in_per_seed and line.startswith("|")):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 11 and re.match(r"^[A-Za-z0-9]+-s\d+$", cells[0]):
            rows[cells[0]] = {
                "per_class": [float(cells[i]) for i in range(4, 9)],
                "macro": float(cells[9].strip("*")),
            }
    return rows


def check_auc(npz_path, y, score, md_rows, run_name):
    """Recompute per-class + macro OvR AUC; assert vs the md row to AUC_TOL."""
    ref = md_rows.get(run_name)
    if ref is None:
        raise AssertionError(f"{npz_path}: run {run_name!r} not found in roc_auc.md")
    per_class = [roc_auc_score(y[:, k], score[:, k]) for k in range(5)]
    macro = float(np.mean(per_class))
    for name, got, want in zip(CLASSES, per_class, ref["per_class"]):
        if abs(got - want) > AUC_TOL:
            raise AssertionError(
                f"{npz_path}: AUC({name}) recomputed {got:.6f} vs stored {want:.4f}"
            )
    if abs(macro - ref["macro"]) > AUC_TOL:
        raise AssertionError(
            f"{npz_path}: macro AUC recomputed {macro:.6f} vs stored {ref['macro']:.4f}"
        )
    return macro


# ---------------------------------------------------------- working-point math
def working_points(y_bin, s):
    """One-vs-rest working points for one class of one seed.

    Returns (tpr_at_fpr {target: tpr}, rej_at_tpr {target: 1/fpr},
    clamped {target: bool})."""
    fpr, tpr, _ = roc_curve(y_bin, s)

    # TPR at fixed FPR: last point of each FPR plateau = max TPR at that FPR.
    last = np.r_[np.nonzero(np.diff(fpr))[0], fpr.size - 1]
    tpr_at_fpr = {t: float(np.interp(t, fpr[last], tpr[last])) for t in FPR_TARGETS}

    # FPR at fixed TPR: first point of each TPR plateau = min FPR at that TPR.
    first = np.r_[0, np.nonzero(np.diff(tpr))[0] + 1]
    min_pos_fpr = float(fpr[fpr > 0].min())  # ~1/n_neg, the finite floor
    rej_at_tpr, clamped = {}, {}
    for t in TPR_TARGETS:
        f = float(np.interp(t, tpr[first], fpr[first]))
        clamped[t] = f < min_pos_fpr  # includes f == 0 exactly
        rej_at_tpr[t] = 1.0 / max(f, min_pos_fpr)
    return tpr_at_fpr, rej_at_tpr, clamped


# ------------------------------------------------------------------- compute
def main():
    results = {b: {} for b in BLOCK_ORDER}
    n_checked = 0

    for block, arm, npz_dir, stem in ENTRIES:
        md_rows = parse_per_seed_table(npz_dir / "roc_auc.md")
        arm_out = {
            "source_files": [],
            "tpr_at_fpr": {f"{t:g}": {c: {"per_seed": []} for c in CLASSES} for t in FPR_TARGETS},
            "rejection_at_tpr": {
                f"{t:g}": {c: {"per_seed": [], "clamped_seeds": []} for c in CLASSES}
                for t in TPR_TARGETS
            },
        }
        for seed in SEEDS:
            npz_path = npz_dir / f"{stem}-s{seed}.npz"
            d = np.load(npz_path)
            y, score = d["y"], d["score"]
            assert y.shape == (N_EXPECTED, 5) and score.shape == (N_EXPECTED, 5), npz_path
            assert np.allclose(y.sum(axis=1), 1.0), f"{npz_path}: y not one-hot"
            check_auc(npz_path, y, score, md_rows, f"{stem}-s{seed}")
            n_checked += 1
            arm_out["source_files"].append(str(npz_path.relative_to(ROOT)))
            for k, cls in enumerate(CLASSES):
                t_at_f, r_at_t, clamped = working_points(y[:, k], score[:, k])
                for t in FPR_TARGETS:
                    arm_out["tpr_at_fpr"][f"{t:g}"][cls]["per_seed"].append(t_at_f[t])
                for t in TPR_TARGETS:
                    arm_out["rejection_at_tpr"][f"{t:g}"][cls]["per_seed"].append(r_at_t[t])
                    if clamped[t]:
                        arm_out["rejection_at_tpr"][f"{t:g}"][cls]["clamped_seeds"].append(seed)

        for metric in ("tpr_at_fpr", "rejection_at_tpr"):
            for tgt in arm_out[metric]:
                for cls in CLASSES:
                    v = arm_out[metric][tgt][cls]
                    vals = np.array(v["per_seed"])
                    v["mean"] = float(vals.mean())
                    v["sd"] = float(vals.std(ddof=1))
        results[block][arm] = arm_out
        print(f"[ok] {block:12s} {arm:9s}  3 seeds, AUC gate passed")

    print(f"[gate] {n_checked} files recomputed and matched roc_auc.md to {AUC_TOL:g}")

    today = datetime.date.today().isoformat()
    provenance = {
        "date": today,
        "generator": "bnjettag/code/plots/make_working_points.py",
        "n_eval": N_EXPECTED,
        "n_files": n_checked,
        "class_order": CLASSES,
        "era": 2,
        "sources": [
            "bnjettag/roc-results/r14/n{8,16,32,64}/{FP32,W8A8,W1A8,W1A6,W1A4}-s{1,2,3}.npz",
            "bnjettag/roc-results/r15-gamma/{sm6i0,sm4i0}/W1A8-s{1,2,3}.npz (labelled W1A8-sm6/W1A8-sm4, N=8)",
        ],
        "auc_gate": (
            f"all {n_checked} files: per-class and macro OvR AUC recomputed with sklearn "
            f"roc_auc_score and matched the per-seed roc_auc.md tables to {AUC_TOL:g}"
        ),
        "statistics": "seed mean +/- sample sd (ddof=1) over seeds 1,2,3",
        "rejection_convention": "1/FPR computed per seed, then averaged (not 1/mean-FPR)",
        "fpr_zero_guard": (
            "interpolated FPR below the smallest nonzero FPR on the curve (incl. exactly 0) "
            "is clamped to that finite minimum (~1/n_neg); such cells are lower bounds and "
            "carry clamped_seeds / a dagger in the md"
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = OUT_DIR / "working_points_r14.json"
    json_path.write_text(json.dumps({"provenance": provenance, "blocks": results}, indent=1))
    print(f"[out] {json_path}")

    md_path = OUT_DIR / "working_points_r14.md"
    md_path.write_text(render_md(results, provenance))
    print(f"[out] {md_path}")

    report_drops(results)
    print_table(results, "N=16", "tpr_at_fpr", "0.01")


# ------------------------------------------------------------------ reporting
METRICS = [
    ("tpr_at_fpr", "0.01", "Signal efficiency TPR at mistag rate FPR = 1%", "tpr"),
    ("tpr_at_fpr", "0.1", "Signal efficiency TPR at mistag rate FPR = 10%", "tpr"),
    ("rejection_at_tpr", "0.5", "Background rejection 1/FPR at signal efficiency TPR = 0.5", "rej"),
    ("rejection_at_tpr", "0.7", "Background rejection 1/FPR at signal efficiency TPR = 0.7", "rej"),
]


def fmt_cell(v, kind):
    mark = "†" if v.get("clamped_seeds") else ""
    if kind == "tpr":
        return f"{v['mean']:.3f} ± {v['sd']:.3f}{mark}"
    if v["mean"] >= 1000:
        return f"{v['mean']:.0f} ± {v['sd']:.0f}{mark}"
    return f"{v['mean']:.1f} ± {v['sd']:.1f}{mark}"


def render_md(results, prov):
    L = []
    L.append("# Round 14 — trigger-style working points (ROC-test, era 2)")
    L.append("")
    L.append(f"- generated : {prov['date']} by `{prov['generator']}`")
    L.append(f"- n_eval    : {prov['n_eval']:,} jets per file; classes g, q, W, Z, t (one-vs-rest)")
    L.append("- sources   : " + "; ".join(f"`{s}`" for s in prov["sources"]))
    L.append(f"- gate      : {prov['auc_gate']}")
    L.append(f"- statistics: {prov['statistics']}")
    L.append(f"- rejection : {prov['rejection_convention']}")
    L.append(
        "- † guard   : interpolated FPR fell below the smallest nonzero FPR on the curve "
        "(incl. exactly 0) for at least one seed and was clamped to that finite minimum "
        "(~1/n_neg ≈ 4.8e-6 here), so the cell is a lower bound on rejection."
    )
    L.append("")
    for metric, tgt, title, kind in METRICS:
        L.append(f"## {title}")
        L.append("")
        for block in BLOCK_ORDER:
            L.append(f"### {block}")
            L.append("")
            L.append("| arm | " + " | ".join(CLASSES) + " |")
            L.append("|---" * 6 + "|")
            for arm in results[block]:
                cells = [fmt_cell(results[block][arm][metric][tgt][c], kind) for c in CLASSES]
                L.append(f"| {arm} | " + " | ".join(cells) + " |")
            L.append("")
    return "\n".join(L) + "\n"


def report_drops(results):
    """Largest FP32 -> W1A8 drop: TPR metrics in efficiency points, rejection as a factor."""
    best_tpr, best_rej = None, None
    for block in ("N=8", "N=16", "N=32", "N=64"):
        fp, w1 = results[block]["FP32"], results[block]["W1A8"]
        for metric, tgt, _, kind in METRICS:
            for cls in CLASSES:
                a, b = fp[metric][tgt][cls], w1[metric][tgt][cls]
                if kind == "tpr":
                    d = a["mean"] - b["mean"]
                    if best_tpr is None or d > best_tpr[0]:
                        best_tpr = (d, block, cls, tgt, a, b)
                else:
                    r = a["mean"] / b["mean"]
                    if best_rej is None or r > best_rej[0]:
                        best_rej = (r, block, cls, tgt, a, b)
    d, block, cls, tgt, a, b = best_tpr
    print(
        f"[drop/TPR] largest FP32->W1A8 drop: TPR@FPR={float(tgt):g} , {block}, class {cls}: "
        f"{a['mean']:.3f}±{a['sd']:.3f} -> {b['mean']:.3f}±{b['sd']:.3f} "
        f"(-{d:.3f}, i.e. -{100*d:.1f} efficiency points)"
    )
    r, block, cls, tgt, a, b = best_rej
    print(
        f"[drop/rej] largest FP32->W1A8 rejection loss: 1/FPR@TPR={float(tgt):g}, {block}, "
        f"class {cls}: {a['mean']:.1f}±{a['sd']:.1f} -> {b['mean']:.1f}±{b['sd']:.1f} "
        f"(x{r:.2f} worse)"
    )


def print_table(results, block, metric, tgt):
    print(f"\n{block} — {metric} @ {tgt}:")
    print("| arm | " + " | ".join(CLASSES) + " |")
    for arm in results[block]:
        v = results[block][arm][metric][tgt]
        print(
            f"| {arm} | "
            + " | ".join(f"{v[c]['mean']:.3f} ± {v[c]['sd']:.3f}" for c in CLASSES)
            + " |"
        )


if __name__ == "__main__":
    main()
