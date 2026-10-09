# Wave 1 interpretation (2026-10-09)

Interpretation step for stage `wave1` under PROPOSAL.md v2 (§5, §7). Inputs: LEDGER.jsonl
(evaluation and measurement records), STATE.json (measured GPU-h), evidence/scores/*.result.json.
No VERIFY.md exists yet, so every number below has status "unverified" (LEDGER line 13) and
nothing here is quotable.

## 1. Measured (copied from the records, not recomputed here)

### Baseline, kai-d350-baseline-e-350k-s1-a2 (seed 1, target 350,000 EBOPs, stop epoch 1,000)

| Item | Value | Source |
| --- | --- | --- |
| Primary score | `INVALID[scientific]: no feasible checkpoint in epochs < 1000` | LEDGER line 10; evidence/evaluate-11499a7559fd500b/evaluate-output.txt |
| Score attempt | 1 (class scientific: no second attempt allowed, PROPOSAL §5) | evidence/scores/baseline-e-350k-s1-a2.json |
| Secondary measurements | none recorded; score.py writes no `secondary` block for an INVALID run | evidence/scores/baseline-e-350k-s1-a2.s1.result.json |
| Run directory | `/data/discovery-350k-20261008/attempts/baseline-e-350k-s1-a1/runs/d350-baseline-e-350k-s1` (a2 resumed into a1's run root, `resume_from` in attempts/baseline-e-350k-s1-a2.json; a1 never started, 0 pod records) | result.json, attempts json, STATE.json |
| GPU-h measured | 6.265278 | STATE.json resources |

### Reference, kai-d350-reference-e-5m-s1-a4 (seed 1, target 5,000,000 EBOPs, stop epoch 1,000; control, not ranked)

| Item | Value | Source |
| --- | --- | --- |
| Primary score | 0.6497741935483871 (best feasible validation top-1 accuracy, validation, n = 62,000, unverified) | LEDGER line 13 |
| Selected checkpoint | epoch 30 (one-based), traced EBOPs 3,260,614, CERTIFIED (relative difference 0.0), val macro AUC 0.8864449110426327 | result.json `selected`, `certification` |
| CPU replay | accuracy difference 0.0 (tolerance 0.001) | result.json `cpu_replay` |
| Non-degeneracy threshold | 0.2109624456315518 (majority rate 0.20288709677419356 + 5 SE) | result.json |
| Epoch 500 | val acc 0.4045967741935484, EBOPs 5,174,723, not feasible (above target) | result.json `secondary.at_epoch.500` |
| Epoch 1,000 | val acc 0.3641129032258065, EBOPs 5,034,020, not feasible (above target) | result.json `secondary.at_epoch.1000` |
| Best feasible accuracy by window (one-based epochs) | 1-200: 0.6497741935483871; 201-400: 0.5289677419354839; 401-600: 0.49256451612903224; 601-800: 0.5235161290322581; 801-1000: 0.5271935483870968 | result.json |
| Feasible epochs / with accuracy ≥ 0.50 | 49 / 22 (as counted by score.py) | result.json |
| Budget first met | epoch 10 (one-based); minimum traced EBOPs 3,132,715 | result.json |
| Attention entropy at the selected checkpoint | mean 0.778037074155873 (heads 0.9905140305755553, 0.5655601177361906) | result.json |
| Mean activation bits at the selected checkpoint | 3.472907566993271 | result.json |
| GPU-h measured | 6.904722 | STATE.json resources |

## 2. Rules applied

- Reference valid, baseline `INVALID[scientific]`. PROPOSAL §5, "Baseline INVALID": the binary
  model does not meet the budget non-degenerately at this horizon; with a valid reference this
  shows the problem. Candidates are compared with the baseline by qualification ("qualifies where
  the baseline does not"); numerical comparison only among valid runs.
- Validity check (§5): it fails only if the baseline's score is within 0.05 of the reference's or
  the baseline reaches 0.50. The baseline has no score and no feasible checkpoint, so neither
  condition holds. The protocol shows the problem at 1,000 epochs; the check passes.
- §7: accuracy at 350k was not regained under continued training with the existing schedule (no
  feasible checkpoint at all), so C1 and C2 are the first candidates. C2 still needs its methods
  reading (BiT, BiBERT distillation) and the reference checkpoint, so C1 is next.

## 3. Interpretation (not a measurement; seed 1 only, no interval)

- The reference's score comes from epoch 30, at 3.26M EBOPs, i.e. before the controller had held
  the model at its target for long. From epoch 201 on its best feasible accuracy per window stays
  between 0.49 and 0.53, and at epochs 500 and 1,000 the run sits just above its 5M target with
  validation accuracy 0.40 and 0.36. So under this protocol the 5M run also loses most of its early
  accuracy while the controller holds it near the target. The pilot reads quoted in PROPOSAL §1
  (5M checkpoints at 0.65-0.66) are matched only by this early checkpoint.
- The small rise from the 601-800 window to the 801-1,000 window (0.5235 to 0.5272) is recovery
  under continued training with the existing schedule. It is not attributed to the learning-rate
  restart; no run isolates the restart.
- Consequence for the question: the accuracy loss looks less specific to the 350k budget than §1
  assumed. This is one seed of a control run and does not change the progression rule, which is
  explicit. It is recorded because it bears on how a C1 or C2 result should be read: a technique
  that only helps at narrow widths may not address a loss that also happens at 5M.
- What cannot be evaluated from wave 1: the C1 falsifier in PROPOSAL §6 ("the baseline's accuracy
  drop coincides with attention entropy going to uniform while activation widths stay wide") needs
  baseline secondary measurements, which do not exist for an INVALID score. Whether the baseline
  never reached 350k or reached it only with degenerate accuracy is not recorded in the score
  output either; the run's traced records on the PVC would say, and VERIFY should read them.
- Runtime: both 1,000-epoch runs took 6.3-6.9 measured GPU-h, against about 11 h expected at
  39 s/epoch (§8). Not examined further; it bears on the search allocation only favourably.

## 4. For Kai (not blocking; the protocol decides the next step without asking)

- The reference's late-run accuracy (0.36-0.40 at epochs 500 and 1,000, not feasible) is a result
  about the protocol itself and may deserve a pilot-level look.
- The C2 teacher is, by the protocol's definition, the reference's best checkpoint: the epoch-30
  model (sha256 44fbd774…b0e4), not a late-run model.
