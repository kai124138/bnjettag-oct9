"""Per-jet log(Pt) sample weights, adapted from Russell's binary signal/background recipe.

Russell's version (y==1 signal, y==0 bkg) builds 100 log(Pt) bins, counts sig and bkg per
bin, and gives signal jets weights_pt = (sig_counts + 0.5) / (bkg_counts + 0.5). Our data has
five classes (g, q, W, Z, t) and no signal/background split, so the same machinery is applied
per class: every class is reweighted toward ONE common log(Pt) shape (all five classes
together). After weighting, the classes share the same Pt distribution, so the classifier
cannot separate them using Pt alone. With two classes and bkg as the target shape, this is
Russell's ratio inverted: bkg_counts / sig_counts applied to signal.

Variable names (thebins, *_counts, weights_pt, pt_indicies, weights, class_weight_dict) and
the plot layout follow Russell's code so the two can be read side by side.

Config (train.pt_weights; absent or enable=false => training is unchanged):
  "pt_weights": {"enable": true,
                 "n_bins": 100,           # Russell: 100 (101 edges)
                 "cap": 10.0,             # clip weights_pt at this value; null = no cap
                 "class_weight": null,    # "balanced" multiplies in sklearn balanced factors
                 "plot": true}
Weights are computed from the TRAIN split only and are applied to training jets only;
validation / model selection stays unweighted.
"""
from __future__ import annotations

import glob
import json
import os

import numpy as np


def load_train_pt(data_dir: str, max_files: int | None = None):
    """Jet Pt (jets[j_pt], GeV) and one-hot labels in exactly load_train_data's row order
    (same sorted glob, same max_files, same concatenation). The labels are returned so the
    caller can assert row alignment against load_train_data's Y."""
    import h5py
    from .data import CLASS_LABELS

    files = sorted(glob.glob(os.path.join(data_dir, "*.h5")))
    if max_files:
        files = files[:max_files]
    Pts, Ys = [], []
    for fp in files:
        with h5py.File(fp, "r") as hf:
            jets = hf["jets"][:]
            jnames = [n.decode() if isinstance(n, bytes) else str(n)
                      for n in hf["jetFeatureNames"][:]]
        Pts.append(jets[:, jnames.index("j_pt")].astype("float64"))
        Ys.append(jets[:, [jnames.index(l) for l in CLASS_LABELS]].astype("float32"))
    return np.concatenate(Pts), np.concatenate(Ys)


def compute_pt_weights(Pts, y, n_bins=100, cap=None, class_weight=None):
    """One weight per jet. Pts: jet Pt (GeV); y: integer class index (0..4).

    For class c in log(Pt) bin b:
        weights_pt[c][b] = ((all_counts[b] + 0.5) / total_all) / ((class_counts[c][b] + 0.5) / total_class[c])
    i.e. (target fraction in the bin) / (this class's fraction in the bin), with Russell's +0.5
    smoothing. Optional cap, then each class is rescaled to mean weight 1 so the class balance
    (and overall loss scale) is unchanged. Returns (weights, info) where info holds everything
    needed to plot and to record the run."""
    y = np.asarray(y)
    classes = np.unique(y)

    thebins = np.linspace(min(np.log(Pts)), max(np.log(Pts)), n_bins + 1)  # check for right range
    allPts = np.log(Pts)
    all_counts, _ = np.histogram(allPts, bins=thebins)
    total_all = len(allPts)

    class_counts, total_class, weights_pt = {}, {}, {}
    for c in classes:
        classPts = np.log(Pts[y == c])
        class_counts[c], _ = np.histogram(classPts, bins=thebins)
        total_class[c] = len(classPts)
        weights_pt[c] = ((all_counts + 0.5) / total_all) / ((class_counts[c] + 0.5) / total_class[c])
        if cap is not None:
            weights_pt[c] = np.minimum(weights_pt[c], float(cap))

    # Add in the sample weights, 1-to-1 correspondence with training data
    # Sample weight of every jet = its own class's weights_pt at that jet's pT
    weights = np.ones(len(y))
    pt_indicies = np.clip(np.digitize(allPts, bins=thebins) - 1, 0, n_bins - 1)
    for c in classes:
        weights[y == c] = weights_pt[c][pt_indicies][y == c]
        # rescale so each class keeps mean weight 1 (class balance unchanged by Pt weighting)
        scale = weights[y == c].mean()
        weights[y == c] /= scale
        weights_pt[c] = weights_pt[c] / scale

    # compute class weights (Russell passes these as class_weight=; Keras 3 refuses
    # sample_weight + class_weight together, so they are multiplied into the per-jet weights)
    class_weight_dict = None
    if class_weight == "balanced":
        from sklearn.utils.class_weight import compute_class_weight
        cl_weights = compute_class_weight(class_weight="balanced", classes=classes, y=y)
        class_weight_dict = dict(zip(classes.tolist(), cl_weights.tolist()))
        for c in classes:
            weights[y == c] *= class_weight_dict[int(c)]
    elif class_weight is not None:
        raise ValueError(f"pt_weights.class_weight must be null or 'balanced', got {class_weight!r}")

    info = {"thebins": thebins, "all_counts": all_counts, "class_counts": class_counts,
            "weights_pt": weights_pt, "class_weight_dict": class_weight_dict,
            "n_bins": int(n_bins), "cap": cap, "class_weight": class_weight}
    return weights, info


def weight_summary(weights, y, class_names):
    """Per-class weight stats + effective sample size (sum w)^2 / sum w^2 as a fraction of jets."""
    out = {}
    for c, name in enumerate(class_names):
        w = weights[np.asarray(y) == c]
        if len(w) == 0:
            continue
        out[name] = {"n": int(len(w)), "sum": float(w.sum()), "min": float(w.min()),
                     "median": float(np.median(w)), "p99": float(np.percentile(w, 99)),
                     "max": float(w.max()),
                     "eff_frac": float(w.sum() ** 2 / (w ** 2).sum() / len(w))}
    return out


def plot_pt_weights(info, class_names, out_dir, tag):
    """Russell's two-panel figure: counts per log(Pt) bin on top, weights_pt below with a red
    dashed line at 1. Five class lines instead of Signal/Bkg; the black line on top is the
    common target shape (all classes, scaled to one class's size)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    thebins = info["thebins"]
    classes = sorted(info["class_counts"])
    fig, (ax_main, ax_ratio) = plt.subplots(
        2, 1, figsize=(8, 6),
        gridspec_kw={"height_ratios": [3, 1]},
        sharex=True
    )
    fig.subplots_adjust(hspace=0.05)

    # Main panel
    for c in classes:
        ax_main.step(thebins[:-1], info["class_counts"][c], where="post", label=class_names[c])
    ax_main.step(thebins[:-1], info["all_counts"] / len(classes), where="post",
                 color="black", linestyle="--", label="All / %d (target)" % len(classes))
    ax_main.set_ylabel("Events")
    ax_main.legend()

    # Ratio panel
    for c in classes:
        ax_ratio.step(thebins[:-1], info["weights_pt"][c], where="post")
    ax_ratio.axhline(1.0, color="red", linestyle="--", linewidth=1)
    ax_ratio.set_ylabel("weights")
    ax_ratio.set_xlabel(r"$\log(P_T)$")
    path = os.path.join(out_dir, f"{tag}_13_pt_weights.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return path


def plot_weight_hist(weights, y, class_names, out_dir, tag):
    """Histogram of the per-jet weights, one line per class (same colours as the Pt plot)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 4))
    thebins = np.linspace(0, max(weights) * 1.01, 101)
    for c, name in enumerate(class_names):
        ax.hist(weights[np.asarray(y) == c], bins=thebins, histtype="step", label=name)
    ax.axvline(1.0, color="red", linestyle="--", linewidth=1)
    ax.set_yscale("log")
    ax.set_xlabel("weight")
    ax.set_ylabel("Jets")
    ax.legend()
    path = os.path.join(out_dir, f"{tag}_14_weight_hist.png")
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    return path


def save_pt_weights(info, summary, out_dir):
    """pt_weights.json: bins, counts, weights_pt and stats, so the run is reproducible."""
    path = os.path.join(out_dir, "pt_weights.json")
    with open(path, "w") as f:
        json.dump({"n_bins": info["n_bins"], "cap": info["cap"],
                   "class_weight": info["class_weight"],
                   "class_weight_dict": info["class_weight_dict"],
                   "thebins_log_pt": info["thebins"].tolist(),
                   "all_counts": info["all_counts"].tolist(),
                   "class_counts": {int(c): v.tolist() for c, v in info["class_counts"].items()},
                   "weights_pt": {int(c): v.tolist() for c, v in info["weights_pt"].items()},
                   "summary": summary,
                   "computed_from": "train split only"}, f, indent=1)
    return path
