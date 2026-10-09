#!/usr/bin/env python3
"""Held-out and internal-validation evaluation of the ptw-n8-20260925 study (24 models).

Arms base / ptw5 / ptwnc x seeds 1-8, N=8, l1x3 inputs (pt, etarel, phirel), W1A8.

Held-out ROC-test set: the 260,000-jet `val` archive, loaded with data.load_eval_set
(n_part=8, features pt/etarel/phirel), exactly as roc_final.py does. Each model gets its own
input_std.json (train-split stats), is loaded with roc_final.load_final_model (the train.py
contract), and its logits are softmaxed in float64 (roc_final.softmax64). One .npz per model:
  y      (N x 5 float32 one-hot)       -- same key convention as roc-results/r14/n*/*.npz
  score  (N x 5 float32 softmax)
  j_pt   (N float32, jets[j_pt] GeV, same sorted files and row order; labels asserted equal)
  meta   (json string)

Internal validation: rebuilds each seed's 20 % split (default_rng(seed).permutation over the
training archive in the trainer's row order, first 20 %), applies the checkpoint's input_std, and stores the true
label and argmax prediction (int8) per jet under <out>/internal-val/, plus the validation AUC
recomputed from the scores as a check against train_meta.json's best_val_macro_auc.

Usage: python eval_ptw_n8.py --ckpt <checkpoints> --val-dir <val .h5 dir> --train-dir <train .h5 dir> --out <store>
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import sys

import h5py
import numpy as np

HGQ2 = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, HGQ2)

from bnhgq2.data import CLASS_LABELS, CLASS_NICE, apply_input_std, load_eval_set  # noqa: E402
from roc_final import load_final_model, macro_ovr_auc, predict_in_batches, softmax64  # noqa: E402

ROOT = os.environ.get("BNJETTAG_ROOT", os.path.abspath(os.path.join(HGQ2, "..", "..", "..")))
CKPT = os.path.join(ROOT, "bnjettag", "results", "ptw-n8-20260925", "checkpoints")
VAL_DIR = os.path.join(ROOT, "data", "val")
TRAIN_DIR = os.path.join(ROOT, "data", "train")
FEATURES = ["pt", "etarel", "phirel"]
N_PART = 8
ARMS = {"base": "BASE", "ptw5": "PTW5", "ptwnc": "PTWNC"}
SEEDS = range(1, 9)


def load_jet_pt(data_dir):
    """jets[j_pt] and one-hot labels in load_eval_set's row order (same sorted glob)."""
    pts, ys = [], []
    for fp in sorted(glob.glob(os.path.join(data_dir, "*.h5"))):
        with h5py.File(fp, "r") as hf:
            jets = hf["jets"][:]
            jn = [n.decode() if isinstance(n, bytes) else str(n) for n in hf["jetFeatureNames"][:]]
        pts.append(jets[:, jn.index("j_pt")].astype("float32"))
        ys.append(jets[:, [jn.index(l) for l in CLASS_LABELS]].astype("float32"))
    return np.concatenate(pts), np.concatenate(ys)


def scores_for(model, X):
    raw = predict_in_batches(model, X, 8192)
    assert raw.ndim == 2 and raw.shape[1] == 5
    rowsum = raw.astype(np.float64).sum(axis=1)
    if raw.min() >= -1e-6 and np.allclose(rowsum, 1.0, atol=1e-3):
        raise AssertionError("model output already a simplex; roc_final would not re-softmax")
    return softmax64(raw).astype("float32")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "bnjettag", "roc-results", "ptw-n8"))
    ap.add_argument("--ckpt", default=CKPT, help="dir holding <arm>-s<seed>/model_best.keras")
    ap.add_argument("--val-dir", default=VAL_DIR, help="held-out archive (26 .h5 files)")
    ap.add_argument("--train-dir", default=TRAIN_DIR, help="training archive (62 .h5 files)")
    ap.add_argument("--skip-val", action="store_true")
    a = ap.parse_args()
    os.makedirs(os.path.join(a.out, "internal-val"), exist_ok=True)

    X, y = load_eval_set(a.val_dir, n_part=N_PART, features=FEATURES)
    assert len(X) == 260000 and y.shape == (260000, 5), (X.shape, y.shape)
    jpt, ypt = load_jet_pt(a.val_dir)
    assert np.array_equal(ypt, y), "j_pt rows not aligned with labels"
    print(f"[data] held-out n={len(X)} X{X.shape}; j_pt aligned", flush=True)

    if not a.skip_val:
        # load_eval_set applies the same sorted-file order, pT sort, truncation and feature
        # subset as train.load_train_data; the two were checked array-equal on this archive.
        Xt, Yt = load_eval_set(a.train_dir, n_part=N_PART, features=FEATURES)
        assert len(Xt) == 620000, len(Xt)
        print(f"[data] train archive n={len(Xt)}", flush=True)

    val_rows = {}
    for s in SEEDS:
        if not a.skip_val:
            idx = np.random.default_rng(s).permutation(len(Xt))
            nval = int(len(Xt) * 0.20)
            Xv, Yv = Xt[idx[:nval]], Yt[idx[:nval]]
        for arm, key in ARMS.items():
            d = os.path.join(a.ckpt, f"{arm}-s{s}")
            tm = json.load(open(os.path.join(d, "train_meta.json")))
            st = json.load(open(os.path.join(d, "input_std.json")))
            assert tm["seed"] == s and tm["config"] == f"ptw-n8-20260925-{arm}-w1a8"
            model = load_final_model(os.path.join(d, "model_best.keras"))
            score = scores_for(model, apply_input_std(X, st["mu"], st["sigma"]))
            macro, per = macro_ovr_auc(y, score)
            label = f"{key}-s{s}"
            meta = dict(label=label, key=key, arm=arm, seed=s, variant="w1a8",
                        weight_bits=1, act_bits=8, n_part=N_PART, features=FEATURES,
                        config=tm["config"], config_hash=tm["config_hash"],
                        params=tm["params"], best_epoch=tm["best_epoch"],
                        best_val_macro_auc=tm["best_val_macro_auc"],
                        auc=macro, auc_per_class=dict(zip(CLASS_NICE, per)), n=int(len(y)),
                        checkpoint=f"W&B artifact model-ptw-n8-0925-{arm}-s{s}",
                        metric="roc_test_auc_macro_ovr", heldout="val archive (260,000 jets)",
                        extra_keys="j_pt = jets[j_pt] GeV, same row order",
                        date=datetime.date.today().isoformat())
            np.savez_compressed(os.path.join(a.out, f"{label}.npz"), y=y.astype("float32"),
                                score=score, j_pt=jpt, meta=json.dumps(meta))
            line = f"[eval] {label:9s} heldout macro={macro:.4f}"
            if not a.skip_val:
                sv = scores_for(model, apply_input_std(Xv, st["mu"], st["sigma"]))
                vmacro, _ = macro_ovr_auc(Yv, sv)
                lab, pred = Yv.argmax(1).astype("int8"), sv.argmax(1).astype("int8")
                np.savez_compressed(os.path.join(a.out, "internal-val", f"{label}.npz"),
                                    label=lab, pred=pred,
                                    meta=json.dumps(dict(label=label, seed=s, n=int(len(lab)),
                                                         split="default_rng(seed).permutation, first 20 % of the 620,000-jet train archive",
                                                         val_macro_auc_recomputed=vmacro,
                                                         best_val_macro_auc_train_meta=tm["best_val_macro_auc"])))
                acc = float((lab == pred).mean())
                val_rows[label] = dict(val_auc=vmacro, train_meta=tm["best_val_macro_auc"], val_acc=acc)
                line += (f"  val macro={vmacro:.5f} (train_meta {tm['best_val_macro_auc']:.5f},"
                         f" d={vmacro - tm['best_val_macro_auc']:+.1e}) val acc={acc:.4f}")
            print(line, flush=True)
            del model
    if val_rows:
        json.dump(val_rows, open(os.path.join(a.out, "internal-val", "val_check.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
