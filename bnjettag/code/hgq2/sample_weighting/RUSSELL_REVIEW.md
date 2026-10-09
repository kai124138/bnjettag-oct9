# What to show Russell

2026-09-24 — Review of existing distribution-only outputs. No new training or classifier changes.

## What exists

The 20 graphs are diagnostics, not 20 training experiments. Five classes (`g`, `q`, `W`, `Z`, `t`) were each treated separately as signal against the other four, because no binary grouping has been selected.

| Output family | Jets | Contents | Purpose |
|---|---:|---|---|
| `outputs/full_dataset_diagnostic/` | 880,000 | Five groupings × two figures and one CSV | Discuss the method with Russell; includes held-out data |
| `outputs/training_only_seed1/` | 496,000 | Five groupings × two figures and one CSV | Training-only diagnostic for the existing seed-1 split; a future policy is still undecided |

For each grouping, `counts_ratio.png` shows jet counts versus natural-log Pt above and `(signal_count + 0.5)/(background_count + 0.5)` below. `hypothetical_weights.png` counts jets by the weight they would receive: background 1, signal its bin ratio. `bins.csv` records the same calculation in 100 rows, including log-Pt and GeV boundaries and both counts. The histogram is not a performance plot or a weighted Pt distribution.

The full [README index](README.md) links every file. The [notebook](pt_distribution_diagnostics.ipynb) is the reproducible calculation; the manifest/settings/verification files are supporting provenance.

## Recommended initial package: two figures and one table

Use the **full-dataset top-versus-rest** example. It illustrates the complete calculation and signal weights both below and above 1. This presentation choice does not select top as the future training signal or imply that this grouping matches Russell's data.

1. [Count/ratio figure](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_t_vs_rest__counts_ratio.png) — lead with this: it shows the input distributions and resulting factors.
2. [Hypothetical-weight histogram](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_t_vs_rest__hypothetical_weights.png) — shows how those factors translate to weights across jets; the background spike is at 1.
3. [Matching 100-bin CSV](outputs/full_dataset_diagnostic/full_dataset_diagnostic__j_t_vs_rest__bins.csv) — attach as supporting numerical detail.

Caption: **Full available dataset, 880,000 jets. Illustrative signal = top (`j_t`); background = g/q/W/Z. Natural-log Pt, 100 equal-width bins, +0.5 smoothing. No balanced-class multiplier. Distribution diagnostic only; no weighted training.**

The table was rechecked: 177,945 signal + 702,055 background = 880,000 jets across exactly 100 bins. Both figures were visually inspected. Of the signal jets, 140,082 receive a hypothetical weight below 1 and 37,862 above 1 (one has weight exactly 1). Thus “emphasize signal-rich bins” does not mean every signal jet is upweighted. Empty bins also have ratio 1 from the smoothing and contribute no jets.

## Draft message

> I reproduced your log(Pt), 100-bin, +0.5 calculation on our jet data. Attached are the full-dataset plots and table for top versus the other four classes, as an illustrative grouping. For our g/q/W/Z/t classifier, which classes should be signal/background, and should we retain all five outputs? Is the goal to emphasize signal-rich Pt regions or match the Pt distributions? I applied (S+0.5)/(B+0.5) to signal and kept background at 1—is that direction intended, and should balanced class factors also multiply these weights?

Draft only; nothing has been sent to Russell.

## Path to the next training runs

1. Confirm grouping, goal, five-class versus binary task, and whether class factors are combined. Agree on the evaluation metric that expresses the goal.
2. Regenerate the diagnostic for that exact policy using only each run's training rows. Check sparse-bin behavior and extreme weights; fix any normalization/capping choices and range policy before training. The existing seed-1 tables are candidates only if that split and grouping are retained. Never use the full-dataset ratios in training.
3. Implement one aligned weight per jet, carrying Pt through the same file order, permutation, and split as features and labels. Verify alignment and weighted-loss behavior before launching anything. Keep validation/test evaluation unweighted for the baseline comparison unless a separate weighted metric is deliberately defined.
4. Run an unweighted baseline and the agreed weighted treatment with the same architecture, inputs, splits, seeds, optimizer recipe, training budget, and model-selection rule. Use matched seeds for follow-up runs. Evaluate the agreed metric, per-class behavior, and Pt dependence; reserve ROC-test evaluation for the fixed comparison.

No weighting benefit has yet been measured. The next task is to resolve the scientific policy from Russell's reply, then specify the controlled experiment.
