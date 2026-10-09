---
id: 2026-10-08-discovery-350k
date: 2026-10-08
type: discovery
status: superseded by PROPOSAL.md v2 (Kai, 2026-10-08: train on NRP, full data, revised metric and confirmation)
---

# Discovery campaign proposal: keeping the binary N=64 tagger accurate at 350k EBOPs

## 1. Goal

Find a training or architecture change that keeps the binary-weight N=64 tagger (the pilot
program's E model: d 24, 2 heads, 1 block, FFN 32, `binary_absmean` weights, 8-bit learned
activations, pT ≥ 2 GeV gate, features pt/etarel/phirel) accurate when the EBOPs controller
squeezes it to a 350,000 EBOPs target.

Why this goal. The lab's target is the Chang/Sun MHA-64 row, 77.9 % at 350k EBOPs
(arXiv:2510.24784 Table 1 as transcribed in `docs/chang-vs-bnjettag.md`; their own split; their
MHA-64 attention collapsed to a Deep Set). The pilot program's internal reads put 350k binary
checkpoints at 0.236-0.405 validation accuracy and unsqueezed or 5M checkpoints at 0.65-0.66
(`campaigns/2026-10-05-pilot-program/STUDY.md` §9; pilot reads, not results). The accuracy
loss appears when the budget is enforced. The pilot program (on NRP, R1 16/24 arms complete)
tests five explanations (controller input, headroom, attention starvation, squeeze timing,
prunability). This campaign tests remedies from the binary-transformer literature, which the
pilot does not:

| Lever | Source | Status in the literature |
| --- | --- | --- |
| Distillation from a full-precision or larger-budget teacher | BiT (arXiv:2205.13016), BiBERT direction-matching distillation (arXiv:2203.06390); quantized FPGA precedent: Bezio, ATLAS HLT Deep Sets (CERN Indico 1496673) | abstract-level |
| Learned weight scales / elastic binarization | BiT; BiViT (arXiv:2211.07091) | abstract-level |
| Attention-specific treatment of the softmax distribution | BiBERT Bi-Attention; BiViT softmax-aware binarization | abstract-level |
| Staged training (start from a less constrained network) | BinaryBERT ternary weight splitting (arXiv:2012.15701) | abstract-level |
| Linear attention | Chang/Sun Linformer-64, 79.8 % at 350k (arXiv:2510.24784) | summary-level |

Candidates will be chosen from these and from the evidence the baseline produces. Arms the
pilot already runs (q,k,v bit floor, warmup timing, budget ladder, NB weights) are not repeated.

## 2. Primary metric

```
python3 campaigns/2026-10-08-discovery-350k/eval/score.py <run dir>
```

Prints one number: the **best feasible validation top-1 accuracy** of the run. **Higher is
better.** A checkpoint is feasible when its traced EBOPs ≤ 350,000, its EBOPs are above the
architecture's 0-bit floor, its validation accuracy exceeds the run's non-degeneracy threshold
(majority-class rate + 5 SE, recomputed from y_val), and `certify_ebops.py` certifies its EBOPs
(relative tolerance 1e-6). Among feasible checkpoints the frozen key is (accuracy, macro AUC,
−EBOPs, −epoch). These are the pilot program's definitions (`readout_pilot.py`,
`certify_ebops.py`, `nondegenerate_threshold.py`), copied into `eval/` and frozen by sha256.
With no feasible checkpoint, or a failed certification or input check, the command prints
`INVALID: <reason>` and exits non-zero; it never prints a number in that case.

What it measures: how accurate the binary model can be while meeting the resource target, at
the end of one 500-epoch learning-rate cycle, on a validation split. What it does not
establish: accuracy after full 7,000-epoch training; test-set accuracy; FPGA resources,
latency or post-route LUTs (EBOPs is a proxy; HGQ notes LUTs are not linear in EBOPs);
whether attention is used (reported as a secondary measurement); anything quotable (home-PC
numbers are never quotable, CLAUDE.md).

Secondary measurements (recorded, not ranked): validation macro-OvR AUC; min traced EBOPs;
epoch the budget was first met; attention entropy at the selected checkpoint
(`analysis/attn_entropy.py`); activation widths; wall time; GPU-hours.

## 3. Evaluation protocol (frozen before the baseline is scored)

- Code: the pilot program's frozen training tree (bundle 98dd2875), copied into this campaign's
  `code/` and made its own Git repository; candidates are branches. The pilot's files are not
  touched.
- Data: local `data/train` (62 files, 620,000 raw jets), the pilot's cache build (N=64, pT gate
  2 GeV, input standardisation), split_seed 1, 90/10: validation 62,000 jets (the pilot's).
- Training subset: a fixed fraction F of the 558,000 training jets, same indices for every run.
  F is the largest of {1/5, 1/10} for which a three-epoch timing run projects a 500-epoch run at
  ≤ 3 h on the RTX 4060 Ti; chosen and frozen before the baseline.
- Training: the pilot's E-350k-C configuration (`pilot1005-h1-e-350k-c-s1`: PID controller,
  option (c), warmup 1, batch 2,790, LR 3e-3 cosine with restarts every 500 epochs), stopped at
  epoch 500. Search seed 1.
- Baseline: that configuration unchanged. Reference: the same model at a 5,000,000 EBOPs target
  (secondary, not ranked), to show what an unsqueezed run reaches under this protocol.
- Protocol validity check: if the baseline does not lose accuracy relative to the reference
  (baseline score ≥ reference − 0.05, or baseline ≥ 0.50), the cheap protocol does not reproduce
  the problem. The search stops and that finding is reported.
- Test data: `data/val` (the 260,000-jet ROC-test set) is not read during the search. It is read
  once at the end, for the baseline and the best confirmed candidate only.
- Confirmation (reserved before the search): the best valid candidate and the baseline rerun
  with seeds 2 and 3 (4 runs). A candidate counts as a confirmed lead only if all three of its
  seeds beat all three baseline seeds; otherwise the result is labelled inconclusive.
- Protected from candidate edits: `eval/` (score, certification, threshold), the cache and split
  code, the EBOPs computation and tracing, validation labels, existing tests. Allowed: model,
  quantizer and training-loop code under `code/bnhgq2/` and new configs, with new tests. Changes
  must keep binary weights, N=64 inputs and the 350k target. Any change to a scientific setting
  (batch size, LR, epochs, data fraction) is a hypothesis-level change recorded in the idea
  record, never a silent repair.
- If the evaluator is found to be wrong: comparisons under that version stop, the defect is
  documented, and the baseline is rescored under a corrected version before anything else.

## 4. Execution environment

Home PC, RTX 4060 Ti 8 GB under WSL2. A new virtual environment from the pilot's
`requirements-training.txt` (TensorFlow 2.21 with CUDA, Keras 3.15, HGQ2 0.1.9), about 3-4 GB of
packages from PyPI; no current local environment can train on the GPU. Runs go through
`tools/harness.py submit` (budget check, approval, reservation) to `run_handoff.py`, with the
local kubectl substitute running each job on this GPU; the substitute is extended to run jobs in
the background so ordinary monitoring code, not a model, watches them. Codex: the CLI bundled with
the VS Code ChatGPT extension (`codex-cli 0.162.0-alpha.2`, ChatGPT login), model gpt-6.1-sol,
`--sandbox workspace-write`, confined to the candidate's directory. Roles: Claude Opus plans,
researches, reviews diffs and interprets; Codex implements; executable checks decide validity.

## 5. Limits

| Resource | Limit | Basis |
| --- | --- | --- |
| Candidate attempts after the baseline | 5 (failed attempts count) | default |
| GPU time, total | 36 GPU-h on the 4060 Ti, enforced by `harness.py submit` for submitted runs | baseline + reference + 5 candidates + 4 confirmation = 11 runs × ≤ 3 h, plus margin |
| Of which reserved for confirmation | 12 GPU-h | 4 runs × 3 h |
| Per-run deadline | 4 h (pod `activeDeadlineSeconds` 14,400) | 33 % above the 3 h target |
| Elapsed time | 5 days from confirmation | sequential runs on one GPU |
| Codex invocations | 15 | ≤ 3 per candidate |
| Claude subagent invocations | 25 | planning, review and interpretation per attempt |
| Repairs | the harness's existing limit (3 per failure class), at most 6 in total | existing policy |
| ROC-test evaluations | 2 (baseline, best confirmed candidate) | final only |

Stop early if: the validity check fails; the evaluator is found defective; a limit is reached;
or a candidate is confirmed (all three seeds above all three baseline seeds), in which case
remaining attempts are not spent.

## 6. What this does not change

The pilot program's K3 hold, the r3 PVC rename and all other named holds stay in force. No
cluster job is launched; runs are local and labelled exploratory. Notifications stay in the
local log. Nothing is merged into the production code line or published.
