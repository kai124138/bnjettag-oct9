#!/usr/bin/env python3
"""Register the era-2 dataset in W&B as versioned `dataset` artifacts (lineage).

Two artifacts in one job_type=dataset run:
  * hls4ml-lhc-jet-5class-val   — the local held-out val split (`data/val/*.h5`):
    per-file sha256 REFERENCES (nothing uploaded; the 1.1 GB stays local/Zenodo),
    per-file jet counts, and the DATASET.md facts (n=260,000 total, the
    jetImage_9_150p_40000_50000.h5 chunk absent from the tarball, class balance).
    Asserts n == 260,000 — the same gate roc_final.py applies at eval time.
  * hls4ml-lhc-jet-5class-train — reference-only pointer at the Zenodo train
    tarball NRP pods fetch in-pod (URL + expected byte size, nothing local).

Training runs `use_artifact` the val artifact for lineage. Re-run after any change
to data/val/ — an unchanged directory produces no new version.

Usage:  .venv-hgq2/bin/python bnjettag/code/training/log_dataset_wandb.py \
            [--data data/val] [--dry-run]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "hgq2")))
from bnhgq2 import wandb_util as wbu  # noqa: E402

EXPECT_N = 260000
ZENODO_TRAIN_URL = ("https://zenodo.org/records/3602260/files/"
                    "hls4ml_LHCjet_150p_train.tar.gz?download=1")
ZENODO_TRAIN_BYTES = 2725115104  # measured 2026-07-07 (job YAML preflight gate)
MISSING_CHUNK = "jetImage_9_150p_40000_50000.h5"


def inspect(data_dir: str) -> dict:
    import h5py
    files = sorted(glob.glob(os.path.join(data_dir, "*.h5")))
    if not files:
        sys.exit(f"[fatal] no .h5 files in {data_dir}")
    per_file, total = {}, 0
    for fp in files:
        with h5py.File(fp, "r") as hf:
            n = int(hf["jets"].shape[0])
        per_file[os.path.basename(fp)] = {"n_jets": n, "sha256": wbu.sha256(fp),
                                          "bytes": os.path.getsize(fp)}
        total += n
        print(f"[data] {os.path.basename(fp)}: n={n}")
    if total != EXPECT_N:
        sys.exit(f"[fatal] n={total} != expected {EXPECT_N} — refuse to register a "
                 f"wrong/partial split (same gate as roc_final.py)")
    print(f"[data] total n={total} over {len(files)} files — OK")
    return {"files": per_file, "n_total": total, "n_files": len(files)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--data", default=os.path.abspath(
        os.path.join(HERE, "..", "..", "..", "data", "val")))
    ap.add_argument("--dry-run", action="store_true",
                    help="inspect + checksum only, no W&B")
    a = ap.parse_args()

    info = inspect(a.data)
    meta = {
        "source": "HLS4ML LHC Jet dataset (150 particles), Zenodo record 3602260",
        "split": "val (the project's ROC-test set)", "era": 2,
        "n_jets": info["n_total"], "n_files": info["n_files"], "n_classes": 5,
        "classes": ["j_g", "j_q", "j_w", "j_z", "j_t"],
        "note": (f"{MISSING_CHUNK} is absent from the tarball itself, hence "
                 f"n=260,000 not 270,000 (DATASET.md, measured 2026-08-01)"),
        "shape": "jetConstituentList (n, 150, 16); pipeline consumes top-10 by pT",
    }
    if a.dry_run:
        print(json.dumps({**meta, **info}, indent=1))
        return
    if not wbu.wandb_enabled():
        sys.exit("[fatal] WANDB_API_KEY not set (use --dry-run to just inspect)")
    import wandb
    run = wandb.init(**wbu.init_kwargs(name="register-dataset", job_type="dataset",
                                       tags=["dataset", "era2"], config=meta))
    val = wandb.Artifact("hls4ml-lhc-jet-5class-val", type="dataset",
                         metadata={**meta, "files": info["files"]})
    for fn in info["files"]:
        val.add_reference("file://" + os.path.join(os.path.abspath(a.data), fn),
                          name=fn)
    run.log_artifact(val, aliases=["latest"]).wait()
    print(f"[wandb] dataset artifact hls4ml-lhc-jet-5class-val:{val.version} committed")

    train = wandb.Artifact(
        "hls4ml-lhc-jet-5class-train", type="dataset",
        metadata={"source": ZENODO_TRAIN_URL, "bytes": ZENODO_TRAIN_BYTES,
                  "note": "fetched in-pod by NRP jobs (PVC-free); reference only"})
    train.add_reference(ZENODO_TRAIN_URL.split("?")[0], checksum=False)
    run.log_artifact(train, aliases=["latest"]).wait()
    print(f"[wandb] dataset artifact hls4ml-lhc-jet-5class-train:{train.version} committed")
    wandb.finish()


if __name__ == "__main__":
    main()
