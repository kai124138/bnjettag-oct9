# N8 w1a8: 1,000 epochs with a 350,000-EBOPs budget

User-requested single-run test, 2026-09-11. The user confirmed that 350k means
EBOPs per inference, not samples per epoch. Train from scratch at seed 1 on the
full training dataset, with the same 20% internal validation split as the prior
N8 pilot. Inputs: pt, etarel, phirel. Binary absmean weights; activation widths
start at 8 bits and remain learnable per tensor.

## Registered settings

- 1,000 epochs; batch 256; no AUC early stopping; no stop upon reaching budget.
- Peak LR 2e-5, 1 warmup epoch and 999 linear-decay epochs. Extending the schedule
  avoids having LR become zero near epoch 101 while requesting 1,000 epochs.
- BetaPID absolute target 350,000; beta initial 1e-7, bounds [1e-10, 1e-3],
  p=1, i=0.05, d=0, 10-epoch controller warmup. Same PID as the original pilot.
- Highest validation macro-OvR AUC among epochs whose measured EBOPs <=350,000;
  ties: lower EBOPs, then earlier epoch. Preserve the best unconstrained model
  separately. Missing the budget is recorded as failure to attain the target.
- jit_compile=false, following the prior A10 XLA failure workaround.
- One GPU Job, 48-hour deadline, no automatic retries. No extra arms or seeds.
- W&B project BNJetTag-EBOPs-N8; group ebops-n8-20260911-long-budget;
  run name ebops-n8-20260911-e1000-b350k-w1a8-s1.

## Comparison and limits

Compare the selected checkpoint against seed-1 N8/L1x3 control ed3piak8 and
previous compression histories in ../ebops-n8-20260910/analysis/. The baseline
validation AUC is only a quoted training metric (see its train_meta.json), not a
held-out result. Remeasure EBOPs on the delivered checkpoint and compare AUC and
cost from that SAME checkpoint. Do not attach the unconstrained best AUC to a
lower-cost epoch. The hypothesis that longer training preserves AUC is unproven.
One seed and the changed schedule/budget cannot establish statistical equivalence
or isolate the causal effect of epoch count. No hardware or ROC-test claim.

## Reproduce

From the research root:

```bash
.venv-hgq2/bin/python bnjettag/code/hgq2/configs/gen_ebops_n8.py --long-budget
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py prepare --long-budget
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py preflight --long-budget
# After the CPU preflight finishes; train stage requires PASS markers:
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py train --long-budget
```

The CPU preflight checks data reachability, configuration builds and binary weights,
EBOPs gradients, checkpoint selection, reload, and synthetic trainer paths. An
additional synthetic GPU check exercises this configuration before data download;
it asserts training continues after target attainment and rejects falsely labeled
budget-compliant checkpoints when no epoch is feasible. No local training.

Final checkpoint, width history, metadata and admitted Pareto checkpoints are
uploaded as the committed W&B model artifact by the existing training pipeline.
Launch manifests, source hashes and logs are in launch/.

## Preflight repair

The initial source package 24b22b84 failed the EBOP gradient check: the working
model builder lacked its free-width activation branch and hardcoded beta0=0.
No experiment GPU was submitted with that package. Restored only `_free_act`,
its config selection/validation, and the configured beta0 from the prior successful
cost-first source archive. Other working-tree changes remain intact. Local CPU
checks (no training) confirmed 42 connected width-variable gradients, measured
cost sensitivity and checkpoint reload. Initial cost 1,739,182 matches the prior
pilot. Revised source SHA256:
8ceec939f79440626417381a76c8c438f06152d691395f1a6cbf536a31872a17.
The rejected CPU preflight log is retained in launch/.

## Submission

CPU preflight passed all four required markers. Submitted one GPU job
`kai-ebops-n8-0911-e1000-b350k-s1`, pod suffix `c9spg`, on
`hcc-nrp-shor-c5909.unl.edu` (NVIDIA A10). Source checksum, TensorFlow GPU access,
W&B authentication and `EBOPS_LONG_ALL_PASS` GPU smoke all passed. Full training
dataset download began 2026-09-11 22:29:52 UTC. No scientific result at submission.
`launch/startup_status.json` and `startup.log` hold the latest startup observation;
`watch_startup.py` is a bounded observer that records the run URL and first epoch.
The NRP job continues independently of the observer/laptop.
