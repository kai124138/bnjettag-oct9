---
id: 2026-09-26-code-line-merge
date: 2026-09-26
type: engineering
status: scratch
question: Can the two pipeline lines, bnjettag/code/hgq2 (research tree; pt-weighting, 24-run eval) and publication/code/hgq2 (GitHub; Engram, constituent study, post-conference configs), be merged into one tree whose CPU build and checkpoint-reload gates pass for every existing config?
supersedes: 
superseded_by: 
code_sha: research 8a56106 (+ uncommitted); publication 39d643c
wandb: 
results: 
generated: stub written 2026-09-26 by the integration session; the diff below is diff -rq output, not a judgement
---

# Merge the two pipeline lines into one

**Question.** Since 2026-09-08 the pipeline has been edited in two places. The research tree
carries pT weighting (bnhgq2/pt_weights.py, train.py) and the EBOPs pilot; the publication
tree carries Engram, the constituent study and the post-conference configs. 135 paths differ.

**Design.** Owner ml-engineer, reviewer newton. Merge into `publication/code/hgq2` (the
GitHub-facing tree) file by file with the research tree's changes on top. Gate, per the
constituent-study criterion: every config in both trees builds on CPU, reloads its saved
checkpoint within 1e-7, and `preflight_final.sh` reports PREFLIGHT_ALL_PASS. No cluster launch.
Falsifier: any config that built before and fails after.

**Result.** none yet.

**Interpretation.** none yet.

**Ops.** none yet.

## Scope: `diff -rq -x __pycache__` on 2026-09-26 (research vs publication)

```
Files research/beta_convention_check.py and publication/beta_convention_check.py differ
Files research/bnhgq2/__init__.py and publication/bnhgq2/__init__.py differ
Files research/bnhgq2/binarize.py and publication/bnhgq2/binarize.py differ
Files research/bnhgq2/build.py and publication/bnhgq2/build.py differ
Files research/bnhgq2/compat.py and publication/bnhgq2/compat.py differ
Files research/bnhgq2/config.py and publication/bnhgq2/config.py differ
Files research/bnhgq2/convert.py and publication/bnhgq2/convert.py differ
Files research/bnhgq2/data.py and publication/bnhgq2/data.py differ
Files research/bnhgq2/gold.py and publication/bnhgq2/gold.py differ
Files research/bnhgq2/monolith.py and publication/bnhgq2/monolith.py differ
Files research/bnhgq2/port.py and publication/bnhgq2/port.py differ
Files research/bnhgq2/qat.py and publication/bnhgq2/qat.py differ
Files research/bnhgq2/store.py and publication/bnhgq2/store.py differ
Files research/bnhgq2/train.py and publication/bnhgq2/train.py differ
Files research/bnhgq2/verify.py and publication/bnhgq2/verify.py differ
Files research/bnhgq2/wandb_util.py and publication/bnhgq2/wandb_util.py differ
Files research/check_ebops_ablation.py and publication/check_ebops_ablation.py differ
Files research/check_ebops_target.py and publication/check_ebops_target.py differ
Files research/configs/gen_ebops_ablation.py and publication/configs/gen_ebops_ablation.py differ
Files research/configs/gen_ebops_n8.py and publication/configs/gen_ebops_n8.py differ
Files research/configs/layer-configs-da13.json and publication/configs/layer-configs-da13.json differ
Files research/convert_fp32.py and publication/convert_fp32.py differ
Files research/convert_w8a8.py and publication/convert_w8a8.py differ
Files research/export_roc_eval.py and publication/export_roc_eval.py differ
Files research/parse_csynth.py and publication/parse_csynth.py differ
Files research/parse_families.py and publication/parse_families.py differ
Files research/probe_pf_dataflow.py and publication/probe_pf_dataflow.py differ
Files research/run_ablation.py and publication/run_ablation.py differ
Files research/run_stage.py and publication/run_stage.py differ
Only in publication/configs: batch20260917
Only in publication/configs: batch20260918
Only in publication/configs: generate_pre_conference.py
Only in publication/configs: generate_softmax_precision.py
Only in publication/configs: post_conference_budget350k-attention_probability_8bit-w1a8.json
Only in publication/configs: post_conference_budget350k-channel_quantization-w1a8.json
Only in publication/configs: post_conference_budget350k-fixed_width_recovery-w1a8.json
Only in publication/configs: post_conference_budget350k-gradual_budget-w1a8.json
Only in publication/configs: post_conference_budget350k-knowledge_distillation-w1a8.json
Only in publication/configs: post_conference_budget350k-reduced_feedforward-w1a8.json
Only in publication/configs: post_conference_budget350k-tensor_quantization-w1a8.json
Only in publication/configs: post_conference_budget_pilot-b25-w1a8.json
Only in publication/configs: post_conference_budget_pilot-b50-w1a8.json
Only in publication/configs: post_conference_budget_pilot-b75-w1a8.json
Only in publication/configs: post_conference_budget_pilot-control-w1a8.json
Only in publication/configs: post_conference_budget_pilot-costfirst-b50-w1a8.json
Only in publication/configs: post_conference_extended_budget350k-w1a8.json
Only in publication/configs: post_conference_softmax-sm4i0-n8-w1a8.json
Only in publication/configs: post_conference_softmax-sm6i0-n8-w1a8.json
Only in publication/configs: pre_conference-n16-fp32.json
Only in publication/configs: pre_conference-n16-w1a4.json
Only in publication/configs: pre_conference-n16-w1a6.json
Only in publication/configs: pre_conference-n16-w1a8.json
Only in publication/configs: pre_conference-n16-w8a8.json
Only in publication/configs: pre_conference-n32-fp32.json
Only in publication/configs: pre_conference-n32-w1a4.json
Only in publication/configs: pre_conference-n32-w1a6.json
Only in publication/configs: pre_conference-n32-w1a8.json
Only in publication/configs: pre_conference-n32-w8a8.json
Only in publication/configs: pre_conference-n64-fp32.json
Only in publication/configs: pre_conference-n64-w1a4.json
Only in publication/configs: pre_conference-n64-w1a6.json
Only in publication/configs: pre_conference-n64-w1a8.json
Only in publication/configs: pre_conference-n64-w8a8.json
Only in publication/configs: pre_conference-n8-fp32.json
Only in publication/configs: pre_conference-n8-w1a4.json
Only in publication/configs: pre_conference-n8-w1a6.json
Only in publication/configs: pre_conference-n8-w1a8.json
Only in publication/configs: pre_conference-n8-w8a8.json
Only in publication: check_extended_training.py
Only in publication: check_resource_priority.py
Only in publication: convert_binary.py
Only in publication: estimate_auc_uncertainty.py
Only in publication: evaluate_roc.py
Only in publication: fold_binary_transformer.py
Only in publication: measure_pre_conference_ebops.py
Only in publication: record_synthesis_metrics.py
Only in research/bnhgq2: documentation.md
Only in research/bnhgq2: pt_weights.py
Only in research/configs: ebops-n8-20260910-b25-w1a8.json
Only in research/configs: ebops-n8-20260910-b50-w1a8.json
Only in research/configs: ebops-n8-20260910-b75-w1a8.json
Only in research/configs: ebops-n8-20260910-control-w1a8.json
Only in research/configs: ebops-n8-20260910-costfirst-b50-w1a8.json
Only in research/configs: ebops-n8-20260911-e1000-b350k-w1a8.json
Only in research/configs: ebops-n8-20260912-ablation-r0-baseline-w1a8.json
Only in research/configs: ebops-n8-20260912-ablation-r1-channel-w1a8.json
Only in research/configs: ebops-n8-20260912-ablation-r2-ffn32-w1a8.json
Only in research/configs: ebops-n8-20260912-ablation-r3-prob8-w1a8.json
Only in research/configs: ebops-n8-20260912-ablation-r4-gradual-w1a8.json
Only in research/configs: ebops-n8-20260912-ablation-r5-recovery-w1a8.json
Only in research/configs: ebops-n8-20260912-ablation-r6-distill-w1a8.json
Only in research/configs: gen_ptw.py
Only in research/configs: gen_r14.py
Only in research/configs: gen_r15_gamma.py
Only in research/configs: ptw-n8-20260925-base-w1a8.json
Only in research/configs: ptw-n8-20260925-ptw5-w1a8.json
Only in research/configs: ptw-n8-20260925-ptwnc-w1a8.json
Only in research/configs: r14-l1x3-n16-fp32.json
Only in research/configs: r14-l1x3-n16-w1a4.json
Only in research/configs: r14-l1x3-n16-w1a6.json
Only in research/configs: r14-l1x3-n16-w1a8.json
Only in research/configs: r14-l1x3-n16-w8a8.json
Only in research/configs: r14-l1x3-n32-fp32.json
Only in research/configs: r14-l1x3-n32-w1a4.json
Only in research/configs: r14-l1x3-n32-w1a6.json
Only in research/configs: r14-l1x3-n32-w1a8.json
Only in research/configs: r14-l1x3-n32-w8a8.json
Only in research/configs: r14-l1x3-n64-fp32.json
Only in research/configs: r14-l1x3-n64-w1a4.json
Only in research/configs: r14-l1x3-n64-w1a6.json
Only in research/configs: r14-l1x3-n64-w1a8.json
Only in research/configs: r14-l1x3-n64-w8a8.json
Only in research/configs: r14-l1x3-n8-fp32.json
Only in research/configs: r14-l1x3-n8-w1a4.json
Only in research/configs: r14-l1x3-n8-w1a6.json
Only in research/configs: r14-l1x3-n8-w1a8.json
Only in research/configs: r14-l1x3-n8-w8a8.json
Only in research/configs: r15-gamma-sm4i0-n8-w1a8.json
Only in research/configs: r15-gamma-sm6i0-n8-w1a8.json
Only in research: EBOPS_ABLATION_1000.md
Only in research: EBOPS_N8_PILOT.md
Only in research: README.md
Only in research: bnjettag
Only in research: check_ebops_costfirst.py
Only in research: check_ebops_long.py
Only in research: convert_final.py
Only in research: ebops_r14.py
Only in research: fold_r14n8.py
Only in research: log_hls_wandb.py
Only in research: mulder_csynth.sh
Only in research: preflight_final.sh
Only in research: roc_final.py
Only in research: sample_weighting
Only in research: uncertainty_r14.py
Only in research: wandb
```
