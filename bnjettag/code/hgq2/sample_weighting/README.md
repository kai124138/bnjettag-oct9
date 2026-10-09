# Distribution-only jet Pt diagnostics

Start with [what to show Russell](RUSSELL_REVIEW.md): a map of the outputs, a recommended two-figure/one-table package, a draft question, and the path to a controlled training comparison.

Executed notebook: [pt_distribution_diagnostics.ipynb](pt_distribution_diagnostics.ipynb).
Run from the research root with `.venv-hgq2/bin/python bnjettag/code/hgq2/sample_weighting/execute_notebook.py`.
For another environment, install [requirements-analysis.txt](requirements-analysis.txt) first. The runner uses its invoking Python interpreter.

Jet Pt is the `j_pt` column (GeV). The five classes have no single native binary target, so each class is treated separately as signal against the other four. This choice does not define a multiclass training-weight policy.

Full diagnostic: **880,000 jets**, the union of all 62 train HDF5 files (620,000 jets) and all 26 held-out `val` files (260,000 jets). The extracted filenames and sizes match both local archives. “Full” is limited to these available archives.

Training only: **496,000 jets**, using the trainer’s default seed 1 and 20% internal validation fraction. The first 124,000 rows of the seeded train-archive permutation are internal validation; the remainder are training. The archive called `val` is the separate ROC-test sample. Other seeds require regeneration.

Each table contains exactly 100 rows, with split and binary grouping, natural-log Pt boundaries, GeV boundaries, both class counts, and `(signal_count + 0.5)/(background_count + 0.5)`. Edges are fitted separately on each output split. Histograms show the weights jets would receive: background 1, signal its bin ratio. Balanced class factors are recorded for reference but not applied.

All bin totals, hypothetical-weight histogram totals, endpoint assignment, row alignment, valid Pt/labels, split partition, archive coverage, and CSV round trips passed. All 44 pre-existing HGQ2 Python source files matched their pre-task SHA-256 hashes. No classifier was imported and no training ran.

## Tables and figures

| Dataset split | Signal vs. rest | 100-bin CSV | Counts and ratio | Hypothetical weights |
|---|---|---|---|---|
| full_dataset_diagnostic | j_g | [CSV](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_g_vs_rest__bins.csv) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_g_vs_rest__counts_ratio.png) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_g_vs_rest__hypothetical_weights.png) |
| full_dataset_diagnostic | j_q | [CSV](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_q_vs_rest__bins.csv) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_q_vs_rest__counts_ratio.png) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_q_vs_rest__hypothetical_weights.png) |
| full_dataset_diagnostic | j_w | [CSV](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_w_vs_rest__bins.csv) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_w_vs_rest__counts_ratio.png) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_w_vs_rest__hypothetical_weights.png) |
| full_dataset_diagnostic | j_z | [CSV](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_z_vs_rest__bins.csv) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_z_vs_rest__counts_ratio.png) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_z_vs_rest__hypothetical_weights.png) |
| full_dataset_diagnostic | j_t | [CSV](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_t_vs_rest__bins.csv) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_t_vs_rest__counts_ratio.png) | [PNG](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_t_vs_rest__hypothetical_weights.png) |
| training_only_seed1 | j_g | [CSV](outputs/training_only_seed1/training_only_seed1__j_g_vs_rest__bins.csv) | [PNG](outputs/training_only_seed1/training_only_seed1__j_g_vs_rest__counts_ratio.png) | [PNG](outputs/training_only_seed1/training_only_seed1__j_g_vs_rest__hypothetical_weights.png) |
| training_only_seed1 | j_q | [CSV](outputs/training_only_seed1/training_only_seed1__j_q_vs_rest__bins.csv) | [PNG](outputs/training_only_seed1/training_only_seed1__j_q_vs_rest__counts_ratio.png) | [PNG](outputs/training_only_seed1/training_only_seed1__j_q_vs_rest__hypothetical_weights.png) |
| training_only_seed1 | j_w | [CSV](outputs/training_only_seed1/training_only_seed1__j_w_vs_rest__bins.csv) | [PNG](outputs/training_only_seed1/training_only_seed1__j_w_vs_rest__counts_ratio.png) | [PNG](outputs/training_only_seed1/training_only_seed1__j_w_vs_rest__hypothetical_weights.png) |
| training_only_seed1 | j_z | [CSV](outputs/training_only_seed1/training_only_seed1__j_z_vs_rest__bins.csv) | [PNG](outputs/training_only_seed1/training_only_seed1__j_z_vs_rest__counts_ratio.png) | [PNG](outputs/training_only_seed1/training_only_seed1__j_z_vs_rest__hypothetical_weights.png) |
| training_only_seed1 | j_t | [CSV](outputs/training_only_seed1/training_only_seed1__j_t_vs_rest__bins.csv) | [PNG](outputs/training_only_seed1/training_only_seed1__j_t_vs_rest__counts_ratio.png) | [PNG](outputs/training_only_seed1/training_only_seed1__j_t_vs_rest__hypothetical_weights.png) |

## Provenance and checks

- [Split inventory](outputs/dataset_split_inventory.csv)
- [Per-file manifest and input-array hashes](outputs/source_split_file_manifest.csv)
- [Full/training verification and unapplied class factors](outputs/full_and_training_only_verification.csv)
- [Full/training run settings, versions, source hashes, and artifact paths](outputs/full_and_training_only_run_settings.json)

Russell’s original data, binary grouping, and exact figure styling are unavailable. These figures reproduce the recorded numerical method, not a verified pixel-for-pixel or same-dataset comparison. Applying signal/background to signal weights does not generally match the two Pt distributions. Before a future experiment, confirm the grouping, ratio objective/direction, whether class factors are multiplied, sparse-bin stability, and treatment outside the training Pt range.
