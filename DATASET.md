# The Dataset: HLS4ML LHC Jet dataset (150 particles), validation split

Everything below was measured directly from the local files on 2026-08-01 with the
inspection script re-runnable at any time (h5py over `data/val/*.h5`). No number is
quoted from memory or from an external page.

## What we have locally

| Item | Value | Evidence |
|---|---|---|
| Source archive | `data/hls4ml_LHCjet_150p_val.tar.gz` (1.14 GB) | file on disk |
| Extracted files | 26 HDF5 files in `data/val/` | `ls data/val` |
| Jets total | **260,000** (26 × 10,000) | summed `jets` dataset shapes across all files |
| Split held locally | validation split only | filename; the train split is fetched from Zenodo by NRP jobs |

One chunk, `jetImage_9_150p_40000_50000.h5`, is **absent from the tarball itself**
(verified with `tar -tzf`), so the split is 260k rather than the 270k the file
numbering pattern would suggest. This is the same n = 260,000 used as the ROC-test
set throughout `RESEARCH.md`.

## Structure of each file

Each of the 26 files holds 10,000 jets with these datasets (shapes read from
`jetImage_7_150p_0_10000.h5`; all files share the layout):

| Dataset | Shape | Contents |
|---|---|---|
| `jetConstituentList` | (10000, 150, 16) | up to 150 zero-padded particles per jet, 16 features each |
| `jets` | (10000, 59) | jet-level features; the last 6 columns are the one-hot labels |
| `jetFeatureNames` | (59,) | names for the columns of `jets` |
| `particleFeatureNames` | (17,) | names for the constituent features (16 used + `j1_pdgid`) |
| `jetImage`, `jetImageECAL`, `jetImageHCAL` | (10000, 100, 100) | calorimeter-image views; unused by our models |

**Particle features (16):** px, py, pz, e, erel, pt, ptrel, eta, etarel, etarot,
phi, phirel, phirot, deltaR, costheta, costhetarel.

**Jet features (59):** kinematics (`j_pt`, `j_eta`, `j_mass`), a large substructure
set (N-subjettiness τ series, energy correlators C/D/M/N, each in plain and
mMDT-groomed variants, trimmed/pruned/soft-drop masses), `j_multiplicity`, then the
targets `j_g, j_q, j_w, j_z, j_t` and a never-used `j_undef`.

## What the data looks like (measured over all 260,000 jets)

**Class balance** — essentially uniform 5-class; quark is ~4% lighter than the rest:

| j_g | j_q | j_w | j_z | j_t |
|---|---|---|---|---|
| 52,404 | 50,468 | 52,235 | 52,298 | 52,595 |

**Constituent occupancy** — the 150-slot array is mostly padding:

- mean 49.4 non-zero constituents per jet, median 46, range 5–150
- percentiles (5/25/75/95): 22 / 34 / 61 / 89

So 95% of jets have fewer than 89 real particles, and a model reading only the
top-N constituents by pT sees most of the jet even for small N. Our trainer uses
the **top-10 by constituent pT with all 16 features**, i.e. input shape
(batch, 10, 16) — documented and implemented in
`bnjettag/code/hgq2/bnhgq2/data.py`.

**Jet kinematics:**

- `j_pt`: min 159.3, median 1022.1, max 3156.7 GeV — these are ~1 TeV jets
- `j_eta`: −2.62 to 2.66
- `j_mass`: median 86.9 GeV (consistent with the W/Z/top classes), max 448.7 GeV

**Feature scales are wildly heterogeneous:** across the 16 constituent features the
per-feature standard deviation spans a ~2,979× range (GeV-scale momenta vs O(1)
angular/relative features). This is measured and discussed in
`bnjettag/code/hgq2/bnhgq2/data.py` (`apply_input_std`) and it is the
motivation for the opt-in fixed per-feature standardization in front of the model.

## A note on "3 features"

The dataset stores 16 features per particle and our pipeline consumes all 16.
Several constituent-based L1 taggers in the literature use only 3 per particle
(pt_rel, η_rel, φ_rel) on this same dataset; comparisons against those baselines
are therefore not input-matched to ours. (Separately, the opt-in pairwise
attention-bias in `bnjettag/code/hgq2/bnhgq2/qat.py` builds 3 physics features per
particle *pair* — unrelated to the input feature count.)

## Reproducing these numbers

```bash
.venv-hgq2/bin/python _attic/pre-r14/code/training/inspect_dataset.py   # structure, labels, occupancy
```

The script iterates every file in `data/val/`, sums label columns, counts non-zero
constituent rows, and reads shapes/names straight from the HDF5 metadata. Any table
above can be regenerated from it verbatim.
