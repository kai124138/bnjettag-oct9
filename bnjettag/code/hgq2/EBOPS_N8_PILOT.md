# N=8 binary-weight EBOPs pilot — 2026-09-10

Four matched runs, seed 1, in W&B project **BNJetTag-EBOPs-N8**, entity
`kayamaguchi-uc-san-diego`, group `ebops-n8-20260910`. These are four independent
Nautilus Jobs, grouped in W&B; no W&B sweep agent or notebook is required.

| Arm | Activation initialization | Width learning | EBOPs controller |
|---|---|---|---|
| control | 8 bits | free per tensor | beta = 0 |
| b75 | 8 bits | free per tensor | BetaPID, target = 75% of initial EBOPs |
| b50 | 8 bits | free per tensor | BetaPID, target = 50% of initial EBOPs |
| b25 | 8 bits | free per tensor | BetaPID, target = 25% of initial EBOPs |

All use binary absmean weights, N=8 particles, inputs pt/etarel/phirel,
d_model=32, 4 heads, 2 blocks, FFN=64, and the round-14 full-data 101-epoch
recipe. Early stopping is disabled in every arm so compression can continue.
All four retain activation-width MonoL1=1e-8: the control has no EBOPs penalty,
but still has task gradients, width L1, and optimizer weight decay.

Targets resolve once after training-data activation calibration and are recorded
as absolute numbers in each run's `ebops_budget.json`. All arms start with the
same seed, data split, and width initialization. The PID starts at beta=1e-7,
warms up for 10 epochs, and uses p=1, i=0.05, d=0 with beta bounded to
[1e-10, 1e-3]. These are pilot settings, not previously validated hyperparameters.

The softmax probability operand entering attention context and softmax table
quantizers remain fixed. The pilot tests the existing `_free_act` path, which
controls 21 per-tensor input quantizer sites (42 trainable i/f variables).
Widths are not required to decrease monotonically. A target may be infeasible
at acceptable accuracy, or may not be reached within this training schedule.

## Code

- `configs/gen_ebops_n8.py`: generates the four config JSONs.
- `bnhgq2/ebops_target.py`: resolves budgets, records raw and effective widths,
  remeasures each epoch, and saves the highest-validation-AUC feasible model.
- `bnhgq2/train.py`: opt-in wiring of HGQ2 `BetaPID`; ordinary configs keep their
  existing callback behavior. Metrics reach W&B after all producers run.
- `check_ebops_target.py`: finite-gradient, beta-gradient, cost sensitivity,
  controller response, checkpoint gating and reload checks. `--integration`
  additionally runs two tiny synthetic training smokes in the cluster CPU pod.
- `../jobs/training/variants/gen_ebops_n8_jobs.py`: creates a content-addressed,
  immutable ConfigMap and job YAMLs using the existing R14 setup recipe.
- `../jobs/training/variants/launch_ebops_n8.py`: checks successful CPU preflight
  before submitting the four GPU jobs. Jobs have backoffLimit=0 to avoid automatic
  duplicate training runs; each has a six-hour deadline and requests one GPU.

## Reproduce the launch

From the research repository root:

```bash
.venv-hgq2/bin/python bnjettag/code/hgq2/configs/gen_ebops_n8.py
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py prepare
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py preflight
# After the CPU preflight succeeds:
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py train
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py status
```

Launch files are under `bnjettag/results/ebops-n8-20260910/launch/`. Existing Jobs
are not restarted by applying them again. To repeat the experiment, generate new
run/job identities rather than merging histories into these runs.

## Outputs and interpretation

Each run uploads a commit-checked W&B `model-<run-name>` artifact containing:

- `train_meta.json` and `input_std.json`;
- `activation_widths.jsonl`: every epoch's effective bits, raw i/f, per-layer cost;
- `ebops_budget.json`: initial cost, target, selected checkpoint's remeasured cost,
  widths, budget status, and code SHA256;
- `model_best.keras`: best feasible model for a target arm, best-AUC model for
  the control;
- `model_unconstrained.keras`: best-AUC checkpoint in target arms, explicitly
  separate from budget selection;
- admitted Pareto checkpoints and their summary when any exist.

If no epoch meets the target, **no model_best.keras is produced** for that target
arm. The unconstrained model and diagnostic history are still uploaded, with
`budget_met=false`. Reloaded selected checkpoints are remeasured before upload.

W&B logs EBOPs, beta, target, budget status, validation macro-OvR AUC, and each
site's activation width. Validation AUC is a training monitor, not held-out ROC-test
AUC. This pilot does not launch ROC evaluation or hardware synthesis.

Do not feed learned-width checkpoints through an export path that reconstructs a
uniform `act_bits` grid: that would erase the learned widths. Export preservation,
bit-exact validation and synthesis are subsequent work. EBOPs is an HGQ2 resource
proxy; these runs do not change the architectural MAC count or establish LUT usage.

## Cost-priority 50% retry — 2026-09-10

The separate `ebops-n8-20260910-costfirst-b50-w1a8-s1` run tests reaching an
absolute ceiling of **869,591 EBOPs** without imposing an accuracy threshold.
It starts from scratch with the same N8/L1x3 architecture, binary weights,
initial A8 free activation widths, full data split, and seed 1.

Changes from the original 50% pilot:

- BetaPID starts at 1e-4 (1,000x the prior 1e-7); minimum 1e-4, maximum 1e-2.
  No beta warmup; p=1, i=0.05, d=0. The controller can increase pressure while
  above target. The task cross-entropy remains in the loss, with no accuracy
  acceptance threshold; this is resource-dominated training, not pure cost-only loss.
- Constant Adam learning rate 1e-4, no LR warmup or decay; maximum 101 epochs.
  Increasing beta alone does not guarantee proportionally faster width movement,
  particularly with Adam and clipping; the sustained LR also matters.
- `train.ebops.selection="min_ebops"`: choose lowest measured EBOPs, ties choose
  the earlier epoch. AUC is recorded but does not rank checkpoints. The Pareto
  monitor uses only EBOPs. A separate best-AUC checkpoint is diagnostic.
- `train.ebops.stop_on_target=true`: stop at the first epoch measured at or below
  the ceiling, then reload and remeasure the saved model before upload. This is
  an acceptance rule; the optimizer still uses a soft penalty, so 101 epochs can
  end with `budget_met=false`.
- If the target is missed, deliver `model_min_ebops.keras` (cheapest measured
  epoch), not the diagnostic best-AUC model. A feasible checkpoint is delivered
  as `model_best.keras`. Metadata records actual epochs run and the selection rule.
- `train.jit_compile=false` bypasses the XLA/Triton GEMM path that failed the
  original b50 GPU run. A synthetic GPU trainer smoke runs before data download.

Generate and launch only this retry from the research repository root:

```bash
.venv-hgq2/bin/python bnjettag/code/hgq2/configs/gen_ebops_n8.py --cost-first
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py prepare --cost-first
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py preflight --cost-first
# After successful CPU preflight (the launcher verifies its PASS markers):
.venv-hgq2/bin/python bnjettag/code/jobs/training/variants/launch_ebops_n8.py train --cost-first
```

W&B project stays `BNJetTag-EBOPs-N8`; group is `ebops-n8-20260910-costfirst`.
Job: `kai-ebops-n8-0910-costfirst-b50-s1`. Launch files and preflight log:
`bnjettag/results/ebops-n8-costfirst-20260910/launch/`.
`check_ebops_costfirst.py` checks lower-cost/lower-AUC selection, beta response,
stop-on-target, serialization, and (cluster `--integration`) both delivered
checkpoint paths. These are implementation checks, not scientific accuracy or
hardware validation. Severe accuracy loss is an acceptable outcome of this run.


## Long-budget run — 2026-09-11

Single w1a8/N8/seed-1 run: 1,000 epochs, absolute 350,000-EBOPs target,
max-AUC feasible checkpoint selection, no early stopping. Generate and launch
with `--long-budget` on the config generator and launcher. Full registered
settings and comparison rules: [experiment.md](../../results/ebops-n8-long-20260911/experiment.md).
