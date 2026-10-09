# Sample weighting study — handoff for Astra

## User objective and workflow

The user wants to understand and potentially implement Russell's `Pt`-dependent sample weighting in the BNJetTag classifier. They want to work **one prompt/task at a time**, document every step, show Russell comparable distribution plots and tables, get his opinion on the unresolved scientific choices, and only then define and run a weighted training experiment. Do not launch training based solely on the exploratory one-vs-rest plots. Keep [LOG.md](LOG.md) current after each task; use the executable notebook for calculations and this short log for state, decisions, artifact paths, and next action.

## Russell's supplied binary method

His example assumes `y == 0` is background and `y == 1` is signal:

1. Compute `np.log(Pt)` (natural log) and 100 equal-width bins using 101 edges from the observed min/max.
2. Count signal and background jets per bin.
3. Calculate `r_bin = (signal_count + 0.5) / (background_count + 0.5)`. The `0.5` smooths sparse bins; it does not change real event counts. The number of bins and offset are choices, not established optima.
4. Initialize one sample weight per jet to `1`; replace **signal** jets' weights with their bin's `r_bin`. Background jets remain at `1`. A bin factor is a lookup value; the model receives one weight per jet. A weight scales the loss contribution, not the number of training repetitions.
5. Separately compute balanced `class_weight` factors from overall class counts and pass both `sample_weight` and `class_weight` to `model.fit` in his pasted code.

Russell described the weights as emphasizing where signal lives. With this ratio applied to signal, signal-rich bins get greater weight; this does **not** generally match the signal and background `Pt` distributions. The desired objective and ratio direction have not been confirmed. His example made a two-panel `log(Pt)` count/ratio plot and a histogram of hypothetical per-jet weights.

Current Keras 3 rejects simultaneous `sample_weight` and `class_weight` arguments for array inputs. If Russell explicitly wants both effects, form one per-jet product and pass only `sample_weight`; do not assume the product is scientifically intended before confirmation. `validation_split` in Keras takes the last fraction before shuffle and carries supplied sample weights into `val_loss`, although validation data do not update model parameters. Derive any training weight formula from the training split only; use an explicit unweighted validation set when comparing held-out performance unless a weighted validation objective is deliberate.

## What was done in this project

The research tree is `/Users/kaiyamaguchi/Downloads/bnjettag-training-results` (also linked as `research` from the lab environment repo). The relevant project uses **five one-hot classes**, `j_g`, `j_q`, `j_w`, `j_z`, and `j_t`; there is no native binary `y == 0/1` target. Jet `Pt` is `jets[j_pt]` in GeV. The existing Keras 3 training path is [train.py](../bnhgq2/train.py): it loads constituent features and five-column labels, permutes with the seed, splits internal validation, and fits a categorical model. It does not currently carry jet `Pt` through that loader, so any eventual weight implementation must align `Pt` with feature rows and labels through the same permutation and split.

The [executed notebook](pt_distribution_diagnostics.ipynb) performed **distribution analysis only**. To avoid inventing a binary target, it created five separately labeled one-vs-rest diagnostics, one class as signal and the other four as background. Outputs use Russell's `np.log(Pt)`, 100 bins, and `+0.5` ratio formula. A [table and figure index](README.md) links **10 CSV tables and 20 PNG figures**: five groupings for the full available dataset and five for the seed-1 training subset, each with a count/ratio plot and hypothetical-weight histogram. The full diagnostic has 880,000 jets: 620,000 train-archive plus 260,000 held-out archive jets. The trainer's seed-1 internal split has 496,000 training and 124,000 internal-validation jets. The notebook verified bin counts, split alignment, input coverage, and artifact round trips; see the [verification CSV](outputs/full_and_training_only_verification.csv) and [run settings](outputs/full_and_training_only_run_settings.json). No classifier files were changed and no training was run.

I independently confirmed the plot files exist and opened the [full-dataset `j_t` count/ratio plot](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_t_vs_rest__counts_ratio.png) and its [hypothetical-weight histogram](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_t_vs_rest__hypothetical_weights.png). They are real graphs. They should not be interpreted as a direct match to Russell's image: his original dataset and binary grouping are unknown, and this diagnostic uses `j_t` versus four other classes. The full-dataset version is for visual comparison only; training must use ratios derived solely from its own training subset.

## Decisions still needed before training

1. Which class or classes are Russell's **signal**, and which are **background** in this five-class project? Is a binary model intended, or should the five-way classifier retain all outputs with a specified per-class weighting policy?
2. Is the objective to emphasize signal-rich low-`Pt` regions, match class `Pt` shapes, improve background rejection at a fixed signal efficiency, or another measured goal? The current ratio direction depends on this answer.
3. Should balanced class factors also be used, and if so, multiplied into per-jet weights? The earlier example prompt suggested multiplication as an implementation route, but this was **not confirmed by Russell**.
4. Are 100 bins and `0.5` stable for sparse bins? How should a future training run handle jets outside the training-derived bin range?

## Immediate next task for Astra

Read [LOG.md](LOG.md) and [README.md](README.md), inspect whichever plots the user wants to share, and help the user select a concise comparison package and question for Russell. Explain clearly that the requested graphs **were generated**, while the five-class grouping prevents choosing a single definitive Russell comparison yet. Do not run training or modify the classifier until the grouping and objective are resolved. After each completed task, add a dated, source-linked entry to [LOG.md](LOG.md).
