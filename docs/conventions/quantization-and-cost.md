---
title: Quantization and cost
status: current
date: 2026-09-26
---

# Quantization and cost

Applies whenever an arm is quantized, budgeted by eBOPs, or selected under a cap.

## Configurations

- Naming: W1A8 = binary weights {−1,+1}, 8-bit activations; W1A6, W1A4 push activations;
  W8A8 and FP32 are baselines. Binary is the thesis; ternary is a comparison, not a subject.
- Activation widths are learned (HGQ2) from an initial width; granularity is per-channel or
  per-tensor and is an arm variable, not a default (batch 2026-09-17 tested both).
- Reference model at N=8: 18,657 parameters (pt-weighting preflight), ≈19k in general.

## Cost accounting

- Cost is **native HGQ2 effective bit operations (eBOPs)** measured on the selected
  checkpoint. Zero-input and random-input measurements must agree (EBOPs pilot 2026-09-10).
- Custom or augmented cost conventions (Engram memory tables: logical vs replicated memory
  caps, arithmetic cap) are reported as their own quantity and never presented as native
  HGQ2 totals (decision 2026-09-18).
- Budgets used so far: 250k / 350k / 500k eBOPs at N=8 (`post_conference_budget350k-*`
  configs), 5M at N=64. State the budget and the cap type (soft penalty vs hard feasibility).

## Selection under a budget

- Rule of record: the checkpoint with the highest **validation** macro-OvR AUC among
  checkpoints at or under the budget (`ablation_metrics.json`, `selection`). If no checkpoint
  is feasible, say "no feasible checkpoint"; do not report the unconstrained best (the
  gradual-schedule arm, 2026-09-15).
- Never mix final-epoch cost with best-checkpoint AUC. Report cost at the selected
  checkpoint.

## Required validation checks

1. Every binary layer holds exactly two nonzero, symmetric effective values (verified on the
   pilot: 15 layers).
2. Stored widths match the remeasured widths.
3. Checkpoint reloads within 1e-7 on the metric with TF32 off; the evaluated candidate is
   the saved one (constituent study 2026-09-22: a 3.2e-7 AUC drift was a TF32 effect and was
   fixed by turning it off, not by loosening the tolerance).
4. Schedule is the committed one (1000 epochs, batch 256, LR 2e-5 for the record; a screen
   uses its own and is labelled).

## Pitfalls, with the incident

- A cost-first arm can miss the ceiling entirely and silently save the unconstrained
  best-AUC checkpoint (25 % arm, EBOPs pilot).
- Resource penalties are soft: a run can end infeasible; acceptance must be strictly
  budget-filtered.
- Packing several arms per GPU changes nothing in the experiment but everything in the
  Job shape; check the code sha per pod.
