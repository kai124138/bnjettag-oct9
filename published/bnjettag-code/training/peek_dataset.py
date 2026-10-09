#!/usr/bin/env python3
"""Look at the HLS4ML LHC jet data with your own eyes.

The .h5 files are containers holding several named arrays; nothing is human-readable
until you print it. This prints one jet's constituents as a labelled table, so the
16 stored features (and the absent 17th, j1_pdgid) are visible directly.

    .venv-hgq2/bin/python bnjettag/code/training/peek_dataset.py              # jet 0
    .venv-hgq2/bin/python bnjettag/code/training/peek_dataset.py --jet 7      # a specific jet
    .venv-hgq2/bin/python bnjettag/code/training/peek_dataset.py --rows 20    # more particles
    .venv-hgq2/bin/python bnjettag/code/training/peek_dataset.py --cols pt etarel phirel
    .venv-hgq2/bin/python bnjettag/code/training/peek_dataset.py --structure  # what's in the file
"""
from __future__ import annotations

import argparse
import glob
import sys

import h5py
import numpy as np

DEFAULT = "data/val/jetImage_7_150p_0_10000.h5"
LABELS = ["gluon", "quark", "W", "Z", "top"]


def open_file(path: str):
    if path == DEFAULT:
        found = sorted(glob.glob("data/val/*.h5"))
        if not found:
            sys.exit("no files in data/val/ — is the tarball extracted?")
        path = found[0] if not glob.glob(DEFAULT) else DEFAULT
    return path, h5py.File(path, "r")


def show_structure(h, path: str) -> None:
    print(f"\n{path}\n" + "-" * len(path))
    print("This one file is a container holding these arrays:\n")
    for k in h:
        d = h[k]
        print(f"  {k:<22} {str(d.shape):<20} {d.dtype}")
    names = [n.decode() for n in h["particleFeatureNames"][:]]
    ncol = h["jetConstituentList"].shape[-1]
    print(f"\n  particleFeatureNames lists {len(names)} names, "
          f"jetConstituentList stores {ncol} columns.")
    if len(names) > ncol:
        print(f"  -> the last {len(names) - ncol} name(s) label nothing: "
              f"{', '.join(names[ncol:])}")


def show_jet(h, jet: int, rows: int, cols: list[str] | None) -> None:
    names = [n.decode() for n in h["particleFeatureNames"][:]]
    arr = np.asarray(h["jetConstituentList"][jet])        # (150, 16)
    ncol = arr.shape[-1]
    names = names[:ncol]                                   # drop names with no column

    jf = [n.decode() for n in h["jetFeatureNames"][:]]
    jets = np.asarray(h["jets"][jet])
    onehot = [jets[jf.index(c)] for c in ("j_g", "j_q", "j_w", "j_z", "j_t")]
    truth = LABELS[int(np.argmax(onehot))]
    jpt = jets[jf.index("j_pt")]
    jmass = jets[jf.index("j_mass")]

    real = arr[np.any(arr != 0, axis=-1)]
    idx = list(range(ncol)) if not cols else [
        names.index(c if c.startswith("j1_") else f"j1_{c}") for c in cols]

    print(f"\nJet {jet}: truth = {truth}   jet pT = {jpt:.1f} GeV   "
          f"mass = {jmass:.1f} GeV")
    print(f"{len(real)} real constituents (of 150 slots; the rest are zero padding)\n")

    hdr = f"{'#':>3} " + " ".join(f"{names[i].replace('j1_',''):>10}" for i in idx)
    print(hdr)
    print("-" * len(hdr))
    for r in range(min(rows, len(real))):
        print(f"{r:>3} " + " ".join(f"{real[r, i]:>10.3f}" for i in idx))
    if len(real) > rows:
        print(f"... {len(real) - rows} more constituents (use --rows)")
    print(f"\nEvery column above is a number computed from that particle's "
          f"four-momentum.\nThere is no column saying what the particle IS.")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", default=DEFAULT)
    ap.add_argument("--jet", type=int, default=0)
    ap.add_argument("--rows", type=int, default=12)
    ap.add_argument("--cols", nargs="*", default=None,
                    help="feature names to show, e.g. pt etarel phirel")
    ap.add_argument("--structure", action="store_true",
                    help="show what arrays the file contains, then exit")
    a = ap.parse_args()

    path, h = open_file(a.file)
    with h:
        if a.structure:
            show_structure(h, path)
        else:
            show_jet(h, a.jet, a.rows, a.cols)


if __name__ == "__main__":
    main()
