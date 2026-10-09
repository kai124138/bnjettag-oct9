# Sample weighting study — working log

Read this file at the start of each sample-weighting task. Add a short dated entry after each task so the next session can continue without reconstructing the conversation. Keep measured results linked to their source files; do not put unverified performance claims here.

## Goal

Understand Russell's `log(Pt)` weighting proposal, reproduce the distribution and weight plots with this project's data, then decide whether and how to use the weights in a controlled training run.

## Russell's proposed method (unverified in this project)

- Use `np.log(Pt)` and 100 equal-width bins (`101` edges).
- Count signal (`y == 1`) and background (`y == 0`) jets in each bin.
- Compute each bin's factor as `(signal_count + 0.5) / (background_count + 0.5)`.
- Assign background jets a sample weight of `1`; assign signal jets their bin's factor.
- Also compute balanced class weights from overall class counts. Whether both factors are intended to be combined needs confirmation.
- Russell's examples include a two-panel count/ratio plot and a histogram of assigned jet weights. This project's formula-based diagnostics are now available; agreement with his original data/grouping remains unverified.

## Ground rules for the study

- Identify the actual dataset, `Pt` column, labels, and train/validation/test split before calculating anything.
- Label every table and plot with the split used. Keep the full-dataset diagnostic separate from training-only weight calculations.
- Derive ratios and class weights from training data only for any training run; do not use validation or test labels to choose weights.
- Keep one weight per jet aligned with its feature row and label.
- Do not modify the training pipeline during the distribution-only task.
- Save reproducible code, tables, figures, and run settings. Record their paths below.

## Current status

2026-09-26 — All 24 ptw-n8 models evaluated on the held-out split with jet pT; results and figures published as §4.5 of the results repo. See the newest session entry.

2026-09-24 — Distribution notebook executed; ten per-bin CSVs and twenty plots are indexed in [README.md](README.md). Review package and draft question prepared in [RUSSELL_REVIEW.md](RUSSELL_REVIEW.md). No classifier changes or training runs. The project's five-class target leaves Russell's binary signal/background grouping unresolved. See [HANDOFF_FOR_ASTRA.md](HANDOFF_FOR_ASTRA.md) for the transfer brief.

## Next task

Share the selected illustrative top-versus-rest plots/table and draft question with Russell; use his reply to fix the grouping and weighting objective, then define a matched unweighted/weighted training comparison. Do not treat the presentation choice as the selected training policy.

## Open questions for Russell

1. Is the objective to emphasize signal-rich low-`Pt` bins, to match the signal/background `Pt` distributions, or something else?
2. Should the `Pt` factors and balanced class factors both affect training? If so, should they be multiplied?
3. Were 100 bins and the `0.5` offset selected after a stability check?

## Session entries

Add newest entries first. Include date, action, source data/split, output paths, verification, decisions, and next step.

### 2026-09-26 — Pt-flat test re-scoring (analysis only, not yet in the public repo)

- Re-scored the 24 held-out arrays (public repo `bnjettag/roc-results/ptw-n8/`) with per-jet test weights that give every class the all-class held-out log(pT) shape (same formula, 100 bins, no cap, fit on the held-out set; one weight set shared by all models). Weighted macro OvR AUC (sklearn sample_weight): base 0.8642 ± 0.0017, ptw5 0.8680 ± 0.0016, ptwnc 0.8668 ± 0.0011. Paired ptw5 − base +0.0038 [+0.0021, +0.0055], 8/8 seeds higher; ptwnc − base +0.0026 [+0.0007, +0.0044], 8/8. Per class (ptw5): g +0.018, q +0.002, W −0.004, Z −0.000, t +0.003.
- Reading: once pT stops being a free hint in the test sample, the weighted models are better. The ranking depends on whether the target sample shares the training spectra. The script was run inline and still needs to be saved and added to the repo before publishing.


### 2026-09-26 — Held-out evaluation of all 24 models; public results repo §4.5

- Checkpoints: `bnjettag/results/ptw-n8-20260925/checkpoints/<arm>-s<seed>/` (W&B artifacts; seeds 1–2 BNJetTagAug, 3–8 BNJetTag-Weights). train_meta validation AUC and best epoch match the pod logs for all 24.
- Held-out ROC-test store: `bnjettag/roc-results/ptw-n8/` — 24 `.npz` with `y`, `score`, `j_pt` (row-aligned, labels asserted), `internal-val/` (each seed's rebuilt 20 % split: label + argmax; validation AUC reproduces train_meta to ≤ 7.7e-5), `roc_auc.md`, `summary.json`. Code: [eval_ptw_n8.py](eval_ptw_n8.py), [ptw_n8_metrics.py](ptw_n8_metrics.py).
- ROC-test macro AUC, 8 seeds, mean ± sd (l1x3, N=8, W1A8): base 0.8711 ± 0.0013; ptw5 0.8603 ± 0.0019; ptwnc 0.8587 ± 0.0020. Held-out accuracy 0.6234 / 0.6080 / 0.6050; internal-validation accuracy 0.6242 / 0.6083 / 0.6056.
- Paired vs base: ptw5 −0.0108 [−0.0124, −0.0093], ptwnc −0.0125 [−0.0148, −0.0101], both lower in 8/8 seeds; every class lower, gluon most (−0.028). Cap 5 vs no cap: +0.0016 AUC (not resolved), +0.0030 accuracy (resolved).
- AUC in six fixed pT bins (edges 980, 1006, 1022, 1046, 1106 GeV): in the four central bins weighting is level or lower (ptw5 down to −0.0037, ptwnc down to −0.0055); in the tails it gains (+0.0047 below 980 GeV, +0.0165 above 1106 GeV, where 60 % of jets are gluons). So weighting does not hold performance at fixed pT in the bulk; the tail gain is consistent with removing the pT prior, not tested directly.
- Published as §4.5 of the results repo (commits 64958268 and 40da656c, Figures 6–7). Next: measure the pT dependence of selection efficiency at a fixed working point (what the weighting is for); the checkpoint selection on unweighted validation AUC is a confound worth one control.

### 2026-09-26 — All 24 runs finished; validation AUC summary

- Source: pod logs saved to `bnjettag/results/ptw-n8-20260925/pod_logs_all.txt`; each run's best validation macro-OvR AUC (the checkpoint-selection epoch), 124,000 internal-validation jets per seed, unweighted. This is validation AUC, not ROC-test AUC.
- Mean ± sd over seeds 1–8: base 0.8712 ± 0.0013; ptw5 0.8604 ± 0.0019; ptwnc 0.8588 ± 0.0020.
- Paired by seed: ptw5 − base = −0.0107 ± 0.0007 SE (95% CI −0.0123 to −0.0092; lower in 8/8 seeds). ptwnc − base = −0.0124 ± 0.0009. ptw5 − ptwnc = +0.0016 ± 0.0008 (6/8 seeds). The largest per-class drop is g (−0.028); t has the smallest (−0.005).
- Interpretation pending: the validation set keeps its natural class Pt differences, which the baseline can exploit. The deciding measurement is AUC within Pt bins on the held-out ROC-test set (join j_pt by row order; see the gate-7 note). Seed 1–2 runs are still in W&B BNJetTagAug.


### 2026-09-25 — Matched N=8 training launched on NRP (base / ptw5 / ptwnc x seeds 1-8)

- Replaced the mistaken N=16 config: `r14-l1x3-n16-w1a8-ptw.json` deleted (the entry below links to it). Arms now come from [gen_ptw.py](../configs/gen_ptw.py), which starts from the headline `r14-l1x3-n8-w1a8.json`: `ptw-n8-20260925-{base,ptw5,ptwnc}-w1a8.json`. `base` is unweighted, `ptw5` uses 100 bins with cap 5, and `ptwnc` is the same with no cap. Neither weighted arm uses a class weight, and all three set `jit_compile=false`. The generator asserts that nothing else differs from the headline config.
- Jobs `kai-ptw-n8-0925-k6-p1..p4`. Each pod holds all three arms for two seeds, so a seed-paired comparison always runs on one GPU. Six trainings per GPU. W&B project BNJetTag-Weights, group [ptw-n8-20260925](https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-Weights/groups/ptw-n8-20260925) (p1's runs temporarily in BNJetTagAug, see below). Run names are `ptw-n8-0925-<arm>-s<seed>`. Weights come from each seed's own training split; validation is unweighted.
- In-cluster checks: CPU preflight passed, and a smoke run of all three arms on the real Zenodo data passed, with Pt loading, weights and both plots produced in the pod. The smoke caught a missing `matplotlib` in the pod dependencies (now pinned). Smoke effective sample fraction for 2 files with seed 1: ptw5 g .50 q .90 W .68 Z .74 t .68; ptwnc W .53 Z .54.
- GPU benchmark (RTX 4090, 6 trainings): mean utilization 94.6% over 10 minutes, about 120 s per epoch. Launch record: `bnjettag/results/ptw-n8-20260925/launch/`.
- Not yet in place: AUC per Pt bin needs `j_pt` joined to the held-out predictions. `roc_final.py` stores only `y`, `score` and `meta`. Rows follow the sorted file order of `load_eval_set`, so the join can be done by row order. No ROC/test evaluation has been launched.
- Status 02:32Z 2026-09-26: p1 Running on RTX 4090 hcc-nrp-shor-c5834.unl.edu, epoch 0 done for all 6 runs (~145 s first epoch), pt_weights ON logged for the 4 weighted runs (seed 1 full train split: ptw5 eff W .69 Z .70; ptwnc W .36 Z .33); W&B auth OK. p2-p4 Pending after 15 min (FailedScheduling in a busy pool; queued, not failed).
- Update 02:45Z: p2-p4 (never started) deleted and resubmitted at 10 CPU / 28 Gi (benchmark peak 5.9 cores, 18.4 GiB; pool nodes have only 20-28 allocatable CPU per 4 GPUs); p1 stays at 14/36 (copy in launch/submitted-p1-14cpu-36gi/). p2-p4 still Pending at 02:45Z. p1 in-pod util 5-min means 55.4% (02:32, fit start) then 97.9% (02:42). W&B group has the 6 p1 runs, all running.
- Update 2026-09-26 ~03:57Z (project correction): W&B project for this study is now BNJetTag-Weights (created via SDK create_project, no dummy runs), group https://wandb.ai/kayamaguchi-uc-san-diego/BNJetTag-Weights/groups/ptw-n8-20260925. p2-p4 (Pending, never started) deleted and resubmitted with WANDB_PROJECT=BNJetTag-Weights (generator PROJECT constant; configs/ConfigMap unchanged, env outranks train.wandb_project; parsed YAML diff = project only). p1 left running: its 6 runs (base-s1 p02fd5f7, base-s2 tv02q49a, ptw5-s1 yfkz2s8j, ptw5-s2 oh4slz8q, ptwnc-s1 jn36pt11, ptwnc-s2 b8ba8ap0) and model-<leaf> artifacts are TEMPORARILY in BNJetTagAug. Move after p1 finishes via W&B UI only (no SDK/API move); artifacts do not move with runs and must be copied (get/put). Plan: launch/p1_move_plan.json.
- Next: when all runs finish, fetch the `model-ptw-n8-0925-*` artifacts, then run the held-out ROC with `j_pt`. Compare macro AUC, per-class AUC and AUC in Pt bins, paired by seed.

### 2026-09-25 — Implemented per-class Pt weights (default-off) and chose cap/bins

- Code: [pt_weights.py](../bnhgq2/pt_weights.py) (Russell's variable names and two-panel plot format) and a `train.pt_weights` block in [train.py](../bnhgq2/train.py). When the block is absent, training is unchanged. Weighted config: [r14-l1x3-n16-w1a8-ptw.json](../configs/r14-l1x3-n16-w1a8-ptw.json) (100 bins, cap 5, no class_weight).
- Scan on 496,000 seed-1 training jets: [seed1_cap_bins_scan.json](outputs/weight_settings/seed1_cap_bins_scan.json). Worst-class Pt shape distance 0.38 unweighted; 100 bins + cap 5 gives 0.037 with effective sample g 53%, q 90%, W 69%, Z 70%, t 69%. Fewer bins did not fix the W/Z tails.
- Plots: [cap-5 Pt weights](outputs/weight_settings/seed1_100bins_cap5_13_pt_weights.png), [weight histogram](outputs/weight_settings/seed1_100bins_cap5_14_weight_hist.png), [uncapped for comparison](outputs/weight_settings/seed1_100bins_nocap_13_pt_weights.png).
- Verified: labels from the Pt loader match the trainer's labels row by row; each jet's weight equals its class's bin value; endpoints land in the first and last bins; each class has mean weight 1; a local smoke train (2 files, 3 epochs) ran with weights off and on. No real training run yet.
- Next: matched baseline vs weighted runs on NRP (same seed and recipe), then compare macro AUC, per-class AUC, and AUC across Pt bins.

### 2026-09-25 — Per-class (option E) weight preview, no signal/background needed

- The user pointed out that the data has five classes, not signal/background, so weights must be defined per class. Previewed option E from the seed-1 bin CSVs (all five tables share the same 100 log-Pt edges; checked): each jet of class c gets w = q[b]/p_c[b], where p_c is class c's normalized training Pt histogram and q is the all-class combined shape. Weighted per-class totals remain equal to raw totals (about 100k each), so class balance is unchanged.
- Weight stats per class (min / median / p99 / max; effective sample size as % of jets): g 0.20/0.54/3.18/3.2, 53%; q 0.19/1.01/2.48/30.5, 88%; W 0.66/0.72/5.62/154, 33%; Z 0.65/0.73/5.55/144, 29%; t 0.34/0.96/3.35/10.4, 68%. The W/Z maximum weights come from sparse edge bins and need a cap or coarser binning before training.
- Next: fix the reference shape and cap policy, then implement in `train.py` (default-off).

### 2026-09-25 — Ratio direction check (shape-matching test)

- Using the existing `training_only_seed1` one-vs-rest bin CSVs (no new data pass), computed the total-variation distance between the normalized signal and background Pt histograms (0 = identical shape, 1 = disjoint) under three policies: unweighted; Russell's rule as written (signal × (S+0.5)/(B+0.5)); and the inverse (signal × (B+0.5)/(S+0.5)).
- Results (unweighted → as written → inverse): g 0.475→0.822→0.000; q 0.116→0.223→0.002; W 0.273→0.365→0.009; Z 0.278→0.373→0.010; t 0.344→0.714→0.001. The rule as written roughly doubles the Pt-shape mismatch between signal and background, and the inverse removes it.
- Implication: if Russell's goal is to stop the classifier from using Pt (the usual reason for Pt reweighting), the direction is probably inverted, or the multiclass version should be option E (reweight every class to one common Pt shape). If his goal really is to emphasize signal-rich bins, the rule as written is consistent with that. This is now the main question to put to him.
- Next: send the question with these numbers; in parallel, add default-off Pt/sample-weight plumbing to `train.py`, which is needed under every option.

### 2026-09-25 — Implementation options reviewed before changes

- User requested implementation possibilities before proceeding. Read this log and handoff, and inspected the actual loader/split/fit path in [train.py](../bnhgq2/train.py). Existing labels are already g/q/W/Z/t; the unresolved choice concerns the weight rule, not identifying or relabeling jets.
- Recorded [implementation options](IMPLEMENTATION_OPTIONS.md): one target class, all-class true-label one-vs-rest, grouped classes while retaining five outputs, a separate binary task, or a different Pt-shape-matching objective. Distinguished class-factor multiplication, global/per-class normalization, and sparse-bin treatments. Existing plots illustrate only the single-target assignment.
- Recommended a default-off weighting path retaining the five-class model, with explicit targeted and all-class modes; no policy chosen or code implemented. All-class weighting is an unconfirmed multiclass adaptation, not established Russell intent. Initial comparison should isolate Pt weighting from class-balance effects and use matched baselines/seeds.
- Verified by source inspection: jet Pt is not currently returned by the training loader; X/Y are permuted and split together; fit currently has no sample weights; validation AUC uses separate callback inputs. Future implementation must preserve Pt/X/Y alignment and derive weights after the training split.
- No classifier changes, notebook execution, new results, or training. Next: choose the rule and raw-versus-normalized/class-factor policy (incorporating Russell's reply if available), then implement and verify without launching training until requested.

### 2026-09-24 — Russell review package selected; training next steps clarified

- Read the handoff, log, and README. Added [RUSSELL_REVIEW.md](RUSSELL_REVIEW.md) with an output map, direct links to the selected two figures/one CSV, a concise draft question, and staged preparation for future training; linked it from README.
- Recommend the **full-dataset `j_t` versus rest** count/ratio plot, hypothetical-weight histogram, and matching bin table as one illustrative example. This does not select the training signal. Visually inspected both existing figures and rechecked the CSV: 100 bins; 177,945 signal + 702,055 background = 880,000 jets. The current formula gives 140,082 signal jets weights below 1, 37,862 above 1, and one exactly 1; it does not upweight every signal jet.
- Explained that 20 plots = five groupings × two split families × two plot types, not trained-model results. Full-dataset outputs are discussion diagnostics; future weight derivation must use each run's training subset. No calculations were rerun in the notebook, no classifier changed, no training launched, and no message sent.
- Still unresolved: signal/background grouping, five-class versus binary task, weighting objective/direction, balanced-factor combination, and sparse-bin/range policy. Draft asks the main scientific questions before implementation.
- Next: obtain Russell's reply, define the exact training-only policy and success metric, verify Pt/feature/label/weight alignment, then prepare matched unweighted and weighted runs with the same architecture, data splits, seeds, and training recipe.

### 2026-09-24 — Distribution-only notebook executed

- Created and executed [pt_distribution_diagnostics.ipynb](pt_distribution_diagnostics.ipynb); rerun with `execute_notebook.py` and the pinned `requirements-analysis.txt`. No training or classifier edits; all 44 pre-existing HGQ2 Python source hashes unchanged.
- Identified jet `Pt` as `jets[j_pt]` (GeV), labels `j_g/j_q/j_w/j_z/j_t`. No native binary target: produced five explicitly labelled one-vs-rest diagnostics, pending Russell’s intended grouping. Full available dataset = 620,000 train-archive + 260,000 held-out `val`/ROC-test jets. Trainer seed 1 / 20% internal validation gives 496,000 training and 124,000 internal-validation jets.
- [Output index](README.md): 10 per-bin CSVs and 20 PNGs under `outputs/full_dataset_diagnostic/` and `outputs/training_only_seed1/`. Used `np.log(Pt)`, 100 equal-width bins per split, `(signal+0.5)/(background+0.5)`; hypothetical background weights 1 and signal weights their bin ratios. Balanced class factors recorded but not applied.
- Verified archive member names/sizes (62 train, 26 held-out files), finite positive Pt, one-hot labels/no undefined jets, exhaustive disjoint internal split, row-aligned bin assignment including the maximum edge, all 100-bin sums and hypothetical-weight histogram totals (880,000 full / 496,000 training for every OvR case), and CSV round trips. See [verification](outputs/full_and_training_only_verification.csv), [split inventory](outputs/dataset_split_inventory.csv), and [settings/provenance](outputs/full_and_training_only_run_settings.json).
- Uncertain: Russell’s binary grouping, original dataset/figure settings, ratio objective/direction, combination with balanced factors, sparse-bin stability, and future out-of-training-range handling. “Full” covers the two available archives; no event-ID cross-archive deduplication was possible.
- Next: review the plots and resolve those weighting choices with Russell before defining a training-only experiment; other training seeds need their own derived tables.
