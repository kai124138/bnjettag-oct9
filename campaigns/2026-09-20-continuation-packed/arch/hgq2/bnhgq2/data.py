"""Eval-set loader — numpy/h5py replica of make_roc.load_eval_set.

MUST stay byte-identical in behaviour to make_roc.py (sorted glob order, stable
argsort on -pT, top-N truncation, float32 casts) so that locally computed scores
align row-for-row with the verified roc-results/reference experiment/*.npz arrays. The label arrays
are compared as an alignment check in verify.py — if they differ, everything stops.
"""
from __future__ import annotations

import glob
import os

import h5py
import numpy as np

CLASS_LABELS = ["j_g", "j_q", "j_w", "j_z", "j_t"]
CLASS_NICE = ["g", "q", "W", "Z", "t"]


def feature_indices(pnames, features):
    """Resolve feature-name suffixes to column indices by EXACT suffix match
    (`pt` != `ptrel`, `etarel` != `etarot`). Raises unless each resolves uniquely.

    pre-conference (L1-realistic inputs): features=["pt","etarel","phirel"] is the
    Odagiu et al. (arXiv:2402.01876) constituent set the L1 field standardized on."""
    idx = []
    for feat in features:
        hits = [i for i, n in enumerate(pnames) if str(n).endswith("_" + str(feat))]
        if len(hits) != 1:
            raise KeyError(f"feature {feat!r}: {len(hits)} suffix matches in {pnames}")
        idx.append(hits[0])
    return idx


def load_eval_set(data_dir: str, n_part: int = 10, features=None):
    """features=None keeps all 16 columns (byte-identical pre-pre-conference behaviour);
    a list of suffixes selects columns AFTER the pT sort and top-N truncation, so
    the particle ordering is identical regardless of the feature subset."""
    files = sorted(glob.glob(os.path.join(data_dir, "*.h5")))
    if not files:
        raise FileNotFoundError(f"no .h5 files in {data_dir}")

    def _names(ds):
        return [n.decode() if isinstance(n, bytes) else str(n) for n in ds]

    Xs, Ys = [], []
    for fp in files:
        with h5py.File(fp, "r") as hf:
            const = hf["jetConstituentList"][:]
            jets = hf["jets"][:]
            jnames = _names(hf["jetFeatureNames"][:])
            pnames = _names(hf["particleFeatureNames"][:])
        missing = [l for l in CLASS_LABELS if l not in jnames]
        if missing:
            raise KeyError(f"{fp}: labels {missing} not in jetFeatureNames")
        lab_idx = [jnames.index(l) for l in CLASS_LABELS]
        pt_col = next((i for i, n in enumerate(pnames) if n.endswith("_pt")), None)
        if pt_col is not None:
            order = np.argsort(-const[:, :, pt_col], axis=1, kind="stable")
            const = np.take_along_axis(const, order[:, :, None], axis=1)
        const = const[:, :n_part, :]
        if features:
            const = const[:, :, feature_indices(pnames, features)]
        Xs.append(const.astype("float32"))
        Ys.append(jets[:, lab_idx].astype("float32"))
    return np.concatenate(Xs), np.concatenate(Ys)


def calibration_batch(X: np.ndarray, n: int = 8192) -> np.ndarray:
    """Deterministic calibration subset: evenly strided rows (spans all files)."""
    if len(X) <= n:
        return X
    idx = np.linspace(0, len(X) - 1, n).astype(np.int64)
    return X[idx]


def input_std_stats(X, eps=1e-6):
    """Per-feature z-score stats over (jets x constituents). Compute on the TRAIN split
    ONLY (reference experiment contract: the hardware receives standardized inputs; standardization is
    offline preprocessing, the reference practice of the HGQ2 examples — input standardization
    2026-07-17)."""
    mu = X.mean(axis=(0, 1))
    sigma = X.std(axis=(0, 1))
    sigma = np.where(sigma < eps, 1.0, sigma)
    return mu.astype("float32"), sigma.astype("float32")


def apply_input_std(X, mu, sigma):
    return ((X - np.asarray(mu, dtype="float32")) / np.asarray(sigma, dtype="float32")).astype("float32")
