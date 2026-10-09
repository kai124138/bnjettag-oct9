---
id: 2026-10-08-discovery-350k
date: 2026-10-08
type: discovery
version: 2 (amended 2026-10-08)
status: approved in direction by Kai 2026-10-08 with amendments (§11); terminal approval (APPROVAL.json) pending; no NRP submission has started
---

# Discovery campaign: keeping the binary N=64 tagger accurate at 350k EBOPs (v2, NRP)

v1 (`PROPOSAL_v1_superseded.md`) trained on the home GPU with a reduced training set. Kai's
review on 2026-10-08 moved training to NRP, kept the full dataset, and asked for a defined metric,
honest confirmation and a follow-up stage. This version replaces it.

## 1. Goal and why

Find a training or architecture change that keeps the binary-weight N=64 tagger accurate when
the EBOPs controller squeezes it to 350,000 EBOPs. The model is the pilot program's E model:
d 24, 2 heads, 1 block, FFN 32, binary weights with one fixed absmean scale per tensor, 8-bit
learned activation widths, pT ≥ 2 GeV gate, inputs pt/etarel/phirel.

- Target: Chang/Sun MHA-64, 77.9 % at 350k EBOPs (arXiv:2510.24784 Table 1, transcribed in
  `docs/chang-vs-bnjettag.md`; their split; their MHA-64 attention collapsed to a Deep Set).
- Observed: pilot reads put 350k binary checkpoints at 0.236-0.405 validation accuracy and
  unsqueezed or 5M checkpoints at 0.65-0.66 (`campaigns/2026-10-05-pilot-program/STUDY.md` §9;
  internal pilot reads, not results). The loss appears when the budget is enforced.
- The pilot program tests why (H1-H5). This campaign tests remedies from the binary-transformer
  literature that the pilot does not run: learned weight scales (BiT arXiv:2205.13016, BiViT
  arXiv:2211.07091), distillation from a less constrained teacher (BiT; BiBERT arXiv:2203.06390),
  attention-specific binarization (BiBERT, BiViT), staged training (BinaryBERT arXiv:2012.15701),
  linear attention (Chang/Sun Linformer-64, 79.8 % at 350k). These were read at abstract or summary
  level (`.claude/memory/research-log.md`, 2026-10-08). Before any of them is implemented, its
  methods section and implementation details are read in the paper itself (§6).

## 2. Where it runs

Coordination on WSL (code, literature, campaign state, monitoring, local tests of the automation).
All baseline, candidate and confirmation training on NRP through `tools/harness.py submit`.

| | NRP (RTX 3090, existing setup) | Home RTX 4060 Ti |
| --- | --- | --- |
| Setup | Existing: pilot bundle, run_handoff, code ConfigMap, the N=64 cache on `kai-data` (`/data/chang-n64-20260926/n64/data`). No new environment. | No working GPU environment; a new TensorFlow 2.21 CUDA venv (3-4 GB) with WSL CUDA compatibility unverified. |
| Time per epoch, E model, full data | 31-39 s measured: r2 arm h2-e-500k ran epochs 100→475 in 11,581 s (RUN.md); 38.8 s/epoch measured in pilot review v1 (JOURNAL 2026-10-05 14:25) | Unmeasured. Spec ratio suggests 1.5-3× slower than a 3090 (estimate) |
| Queue | Unknown for a few jobs. Pilot R1: 2 Running, 22 Pending at launch; r2: 15 of 23 complete about 18.5 h after submission (500-epoch arms, some resumed) | None |
| Parallel runs | One GPU per run; a wave runs concurrently | One run at a time |
| Numbers | Quotable after a VERIFY.md | Never quotable (CLAUDE.md) |

NRP wins on every count but queue, which is unknown. Seven 1,000-epoch runs at 39 s/epoch take
about 11 h each; on NRP a wave runs in parallel, while at home they would run back to back for
roughly 5-9 days. The home GPU is used only for local automation tests.

## 3. Training protocol (frozen before the baseline is scored)

- Code: the pilot's frozen training tree (bundle 98dd2875), copied into this campaign's `code/`,
  which becomes its own Git repository; each candidate is a branch from a recorded commit. The
  pilot's files are not touched.
- Data: the full pilot cache: N=64, pT gate 2 GeV, split_seed 1, 90/10, so 558,000 training and
  62,000 validation jets. No reduced-data protocol (see §3.1).
- Training: pilot configuration `pilot1005-h1-e-350k-c-s1` (PID controller, option (c), warmup 1,
  batch 2,790, LR 3e-3 with cosine restarts every 500 epochs), stopped at **epoch 1,000**: the
  first squeeze to the budget, one learning-rate restart, and a second cycle at the budget.
- Why 1,000 epochs and not 500: the pilot's controller reaches the budget near epoch 500
  (`docs/PILOT_PROGRAM.md`), so a 500-epoch run measures accuracy at the moment of arrival. The
  restart is where a binary network can re-escape a bit-width drop (`bnhgq2/train.py`, comment on
  cosine restarts), and it is the pilot's deferred "restart-crossing" question (pilot STUDY:470).
  A technique that slows the squeeze also needs the second cycle to reach the budget at all.
- What 1,000 epochs can establish: whether a technique keeps or recovers accuracy at 350k
  through one restart. It cannot establish 7,000-epoch accuracy; §5 stage B and the reserved
  production run address that.
- Comparisons only at equal horizons: the primary score is a maximum over checkpoints, which
  grows with the number of epochs, so a 1,000-epoch run is never ranked against a 2,000-epoch run.
- Test data: the 260,000-jet ROC-test set is not read during the search; it is read once at the
  end for the baseline and the best supported candidate.

### 3.1 Why not the reduced-data, 500-epoch protocol

With a training fraction F, each epoch has 200·F optimizer updates (558,000 / 2,790 = 200 at
full data; 40 at F = 1/5). The learning rate follows a per-epoch cosine (`ablation.chang_cosine_restarts`)
and the PID controller is stepped once per epoch on the traced full-split EBOPs, so both
schedules are unchanged in epochs. Per optimizer update they run F⁻¹ times faster: the model would
reach the budget after 20,000 updates instead of 100,000. That protocol asks a different
question, "does the technique survive a squeeze that is fast relative to learning", and
reproducing the baseline's degradation in it would not show that its candidate rankings carry
over to full training. It is not used.

## 4. Primary metric

```
python3 campaigns/2026-10-08-discovery-350k/eval/score.py <run record dir>
```

**Definition (chosen and frozen now):** the validation top-1 accuracy of the best feasible
checkpoint anywhere in the run up to the stop epoch, selected by the frozen key (accuracy, macro
AUC, −EBOPs, −epoch). **Higher is better.**

A checkpoint is feasible when all of these hold:
- its traced EBOPs ≤ 350,000 and above the 0-bit floor;
- its accuracy exceeds the run's non-degeneracy threshold (majority-class rate + 5 SE from y_val);
- `certify_ebops.py` certifies its EBOPs (relative tolerance 1e-6).

These definitions come from the pilot's `readout_pilot.py`, `certify_ebops.py` and
`nondegenerate_threshold.py`, copied into `eval/` and protected by sha256. If no checkpoint is
feasible, or an input check fails, the command prints `INVALID[<class>]: <reason>` and exits
non-zero (classes in §5).

**Why this definition and not end-of-cycle accuracy.** The deliverable is a model that meets the
budget, and production selects that model as the best feasible checkpoint (the frozen
accuracy-first rule of the training-batch campaign). End-of-cycle accuracy measures stability,
not what would be deployed. The risk of a maximum is that it rewards a brief accurate moment, so
stability is recorded beside it and enters the progression rules (§5). Secondary measurements, all
recorded and not ranked:
- feasible accuracy at epochs 500 and 1,000;
- number of feasible epochs with accuracy ≥ 0.50;
- validation macro AUC;
- epoch the budget was first met;
- attention entropy at the selected checkpoint (`analysis/attn_entropy.py`);
- activation widths;
- GPU-hours.

What the score does not establish: test accuracy, FPGA resources or latency (EBOPs is a proxy,
HGQ notes LUTs are not linear in EBOPs), whether attention is used (secondary), 7,000-epoch
behaviour.

## 5. Stages and progression

Amended 2026-10-08 after Kai's review (§11 lists the amendments).

**Stage A, discovery** (seed 1, 1,000 epochs). Wave 1 is the baseline (E-350k-C unchanged) and
the reference (E at a 5,000,000 target, not ranked). It runs and is interpreted before any
candidate compute is committed. Then up to three candidates, more only if the search allocation
(§8) allows.

**Results without a score.** Every run evaluates to a score or to `INVALID[<class>]: <reason>`.
INVALID is never turned into a number: not zero, not the threshold, and it is never left out of a
summary. The class comes from the frozen table `eval/INVALID_REASONS.json`:
- **scientific**: the run trained and was read correctly, but no checkpoint meets the four
  conditions. Only this class enters the qualification branches below.
- **diverged**: the run's training diverged (`DIVERGED.json`). This is its own outcome, not "does
  not qualify", because a run that diverged late may have had a feasible checkpoint before.
  - A diverged candidate is evidence against that implementation at these settings, recorded as
    "diverged". The branch stops unless the divergence is traced to a fault that the repair
    policy covers.
  - A diverged baseline or reference means the wave-1 validity check cannot be evaluated. That
    is outside the approved scope to resolve, so it goes to Kai with the evidence.
  - No score attempt is repeated for a diverged run.
- **evaluator**: certification, CPU-replay or manifest mismatch, or an internal error. One more
  score attempt is made. If it is INVALID again, comparisons stop under that evaluator version
  (§3).
- **infrastructure**: a missing snapshot or record, a truncated run, or a killed score Job. One
  more score attempt is made. If it fails again, the run goes to the repair policy.

A reason not in the table counts as evaluator.
- **Baseline INVALID** (no qualifying checkpoint in 1,000 epochs): the binary model does not meet
  the budget non-degenerately at this horizon. If the reference is valid, this shows the problem.
  Candidates are then compared with the baseline by qualification ("qualifies where the baseline
  does not"). Numerical comparison happens only among valid runs.
- **Reference INVALID**: the protocol or the evaluator is suspect. Comparisons stop until the
  cause is found.
- **Candidate INVALID**: the reason is classified first.
  - An implementation or infrastructure failure goes to repair and is not a scientific result.
  - A correct run that never reached the budget, or stayed degenerate, is recorded as "does not
    qualify at this horizon". It may take the slow-starter route only if its traced EBOPs were
    still falling toward the target at epoch 1,000 and its accuracy stayed above 0.50.

**Validity check, after wave 1.** If the baseline's score is within 0.05 of the reference's, or the
baseline reaches 0.50, the protocol does not show the problem at 1,000 epochs. The search then
turns to the conditions under which accuracy is lost, and the change is reported. Accuracy
regained after epoch 500 is described as recovery under continued training with the existing
schedule. It is not attributed to the learning-rate restart without a run that isolates the
restart (for example the same run without a restart).

**After each candidate**, decided without asking:
- **Advance to confirmation**: the valid candidate with the highest score, if it exceeds the
  baseline by ≥ 0.02, or qualifies where the baseline does not.
- **Advance to the follow-up instead, at most once**: a slow-starting candidate. Its score is not
  above the baseline, but its record shows the intended effect. That means its best feasible
  accuracy over epochs 801-1,000 exceeds that over 601-800 by ≥ 0.01, or the mechanism's own
  diagnostic moves the intended way. A diagnostic is evidence about the hypothesis, not a
  diagnosis. An early accuracy deficit alone does not stop a plausible technique.
- **Stop the branch**: valid, more than 0.02 below the baseline, no rising trend and no diagnostic
  sign. Recorded as evidence against this implementation at this horizon.
- **Repair**: implementation or infrastructure failure, under the existing bounded policy.

The margins 0.02 and 0.01 are screening rules chosen before any data. They decide what is worth
confirming. They are not significance thresholds.

**Confirmation.** Fresh seeds 2, 3 and 4 for the advanced candidate and for the baseline. These
seeds are never used for selection.
- **Interval.** With candidate scores c₁..c₃ and baseline scores b₁..b₃: difference
  d = mean(c) − mean(b); SE = √(s_c²/3 + s_b²/3) with sample variances s²; Welch–Satterthwaite
  degrees of freedom ν = SE⁴ / [(s_c²/3)²/2 + (s_b²/3)²/2]; 95 % interval
  d ± t₀.₉₇₅,ν · SE, with t the Student quantile.
- **Labels.** An interval entirely above zero favours the candidate. One that crosses zero is
  inconclusive. One entirely below zero favours the baseline.
- **Reporting.** Every seed's score (or INVALID reason) is reported. If any confirmation seed is
  INVALID, no interval is computed. The result is reported as qualification counts per arm
  (e.g. 3/3 against 1/3) together with the valid scores: it favours the arm whose seeds all
  qualify while at most one of the other arm's do, and is inconclusive otherwise.
- **Discovery and confirmation are reported separately.** The seed-1 advantage is expected to
  shrink, because it was the maximum that was selected.
- **This is exploratory evidence.** With three runs per arm the interval is wide. A result
  favouring the candidate is a lead worth longer training, not a demonstrated improvement.

**Follow-up** (2,000 epochs; four learning-rate cycles). It applies to a candidate favoured or
inconclusive in confirmation with a positive mean difference, or to the one slow-starter.
- Confirmation seeds 2 and 3 of the candidate and of the baseline continue from their 1,000-epoch
  checkpoints to 2,000, if the code resumes to a later stop epoch (the ml-engineer verifies this
  in PREFLIGHT). Otherwise new 2,000-epoch runs are used, with one seed per arm if the reserve
  requires it.
- Question: does the difference persist through more cycles at the budget?
- A 7,000-epoch production run stays Kai's separate approval (K3 unchanged).

**Stop the campaign** when any of these happens:
- the GPU-hour limit or a stage allocation is reached;
- the evaluator is found defective;
- the follow-up finishes;
- the candidate allocation is spent.

## 6. Before implementing a technique

For each candidate the agent:
1. Reads the methods section and implementation details of the primary paper (PDF), not only the
   abstract.
2. Writes, in the idea record, why the technique could address the observed failure and which
   observation would argue against it.
3. Writes a self-contained specification for Codex (gpt-6.1-sol, `codex exec --sandbox
   workspace-write --json -`, confined to the candidate directory).
4. Reviews the diff (Claude Opus), and re-runs the tests and the frozen score independently.

The first two candidates, stated now:

| Candidate | Why it could address the failure | What would argue against it |
| --- | --- | --- |
| C1 learned per-channel weight scales (BiT, BiViT) | All channels of a binarized layer share one fixed scale (`bitnet_binary_ste`: per-tensor absmean). As the controller narrows activation widths, the scale is the remaining way to represent channel magnitudes, and it is frozen. A per-channel scale costs one multiply per output channel, and EBOPs counts it. | The baseline's accuracy drop coincides with attention entropy going to uniform while activation widths stay wide. Or C1 also fails to beat the baseline at 5M. |
| C2 distillation from the reference (5M) run's best checkpoint (BiT, BiBERT) | The 5M model shows that the architecture can reach about 0.65 when unsqueezed. Soft targets from it give the squeezed student information about class similarity that hard labels do not. | The student matches the teacher's outputs on training jets but its validation accuracy at 350k does not move. That points to capacity at the budget (pilot H2), not optimization. |

C2 needs the reference run's checkpoint, so it follows wave 1. Later candidates are chosen from
the evidence and the literature list in §1, after the pilot readout where one is available.

**Protected from candidate edits:**
- `eval/`;
- cache, split and data code;
- the EBOPs computation and tracing;
- validation labels;
- existing tests.

**Allowed:**
- model, quantizer and training-loop code under `code/bnhgq2/`;
- new configs and new tests.

**Certification covers what the candidate adds.** A candidate that adds inference operations
(a per-channel scale multiply, a distillation-only head that is dropped at inference, a
projection) passes a coverage test before its score is accepted:
- the traced EBOPs the controller sees include every added inference operation at its actual
  precision;
- `certify_ebops.py` recomputes the same value;
- a hand count on a one-layer example agrees.

Without coverage the score is INVALID ("certification does not cover …"). Extending the
certification is an evaluator change: the baseline is rescored under the new version and must
reproduce its earlier score exactly before any comparison. Training-only components that do not
exist at inference (a teacher) are excluded from EBOPs, and the coverage test checks that they
are absent from the inference graph.

Every candidate keeps binary weights, N=64 and the 350k target. A change to batch size, learning
rate, epochs or data is a hypothesis-level change recorded in `ideas.json`, never a repair. The
harness now refuses a repair that changes a declared scientific setting (test
`test_repair_that_changes_a_scientific_setting_is_refused`).

## 7. Recommended first experiment

Wave 1 on NRP: baseline E-350k-C and reference E-5M, seed 1, full data, 1,000 epochs, about 22
GPU-h on RTX 3090s, about 11 h plus queue.

It answers two questions before any candidate is ranked:
- **Does the cheap screen show the problem?** This is the validity check.
- **Is accuracy at 350k regained under continued training with the existing schedule?** No
  completed run in the lab answers this. The pilot stops at 500 epochs. A recovery would not by
  itself show that the learning-rate restart is the cause (§5).

The pair is interpreted before candidate compute is committed. If accuracy is regained, candidate
priorities move toward the training conditions. If it is not, C1 and C2 are the first candidates.
C1 is implemented and tested locally while wave 1 runs. C2 starts from the reference's checkpoint.

## 8. Resource limits

240 GPU-h is a maximum, not a spending target. Expected costs use 39 s/epoch for the baseline and
up to 1.3× that for candidates, whose runtime depends on the technique (a teacher forward pass, an
added projection).

| Stage | Expected | Allocation, including failures | How it is held |
| --- | --- | --- | --- |
| Wave 1 (baseline, reference) | 2 × 11 = 22 GPU-h | 35 | shares a cap of 90 with the search |
| Search (≤ 3 candidates; up to 5 only if the allocation allows) | 3 × 14 = 43 | 55 | same cap of 90 |
| Confirmation (3 + 3 fresh seeds) | 3 × 14 + 3 × 11 = 75 | 90 | reserved: `harness.py submit` refuses wave-1 and search submissions that would reach into it |
| Follow-up (2 + 2 continuations, 1,000 → 2,000 epochs) | 2 × 14 + 2 × 11 = 50 | 60 | reserved from all earlier stages |
| **Total** | **≈ 190** | **240** | |

When failures or slow candidates use up the search allocation, fewer candidates are tried. The
reserves are never borrowed and the cap is not raised.

How the check works: before every submission the harness adds the measured GPU time of finished
Jobs, plus, for unfinished ones, the larger of their reservation and their running estimate. It
refuses the submission if that total plus the new Job's worst-case bound exceeds the stage's cap
(240 minus the reserves of later stages). The worst-case bound is GPUs × allowed attempts × pod
deadline, about 26 GPU-h for a 1,000-epoch baseline run and about 34 for a candidate. Because of
that, at most two candidates are outstanding at once, and confirmation may go out in two batches.
Not inside the bound: pods replaced after a disruption the failure policy ignores, and Jobs not
submitted through the harness.

| Other limits | |
| --- | --- |
| Per-run pod deadline | 47 s × stop epoch × runtime factor (1,000 epochs: 47,000 s for the baseline) |
| Elapsed time | 8 days from the first submission |
| Codex calls | 15 |
| Claude subagent calls | 30 |
| Headless agent wake-ups | 20 |
| Repairs | existing policy (3 per failure class), at most 6 in total |
| ROC-test evaluations | 2, final only |

## 9. Execution path, and what depends on Kai's PC and login

**Built and tested locally (2026-10-08)** in `tools/harness.py`, tests in `tests/test_harness.py`:
- **Scheduled pass.** `harness.py tick` makes one monitor pass, then runs at most one task. It is
  run by cron every 15 minutes and skips a pass while another is running.
- **Budget check.** `harness.py submit --stage` checks the stage caps and reservations of §8
  before every submission. A hook refuses any command that runs run_handoff's launch with
  `--submit` on this campaign's handoffs.
- **Retry accounting.** Kubernetes' own retries under the pod failure policy are counted from the
  pod records, and the harness does not add its own. Harness relaunches and repairs are counted
  against the limits.
- **Credential handling.** A failure to read the cluster is classified as credentials, network
  or other. It is reported once in `NOTIFY.log`, and its recovery is reported too. Jobs keep
  running on NRP meanwhile.
- **Evaluation.** Scoring runs as a CPU Job and is collected over later passes. An INVALID result
  is recorded as INVALID.
- **Interpretation.** A queued interpretation step may write only `ideas.json` and `plan/`.

**Verified on this machine:**
- cron is active under systemd.
- `kubectl` and its OIDC plugin are in `~/.local/bin`.
- A read-only `kubectl get` in a cron-like environment (minimal PATH, no browser) refreshed the
  NRP login without interaction. The ID token lasts about 30 minutes and is renewed from a cached
  refresh token.

**Depends on Kai's PC:**
- **WSL must be running.** cron, the monitor and the agents run inside WSL on the home PC. If the
  PC sleeps or WSL is shut down, Jobs keep running on NRP, but monitoring and decisions pause.
  They resume on the next pass without duplicated work.
- **Idle shutdown is unverified.** `.wslconfig` sets no idle timeout, and whether WSL stays up
  with no terminal or VS Code window open was not tested.

**Depends on an interactive login:**
- **Refresh-token lifetime is unknown.** When the refresh token expires, the monitor reports a
  credentials failure once and waits for a manual login (`kubectl get nodes` at a terminal opens
  the browser login).

**Rehearsed on a copy of this campaign (2026-10-08).** A full scheduled repair ran in one `tick`
(585 s), with a fake `kubectl` for object creation and the real read-only node lookup for lint:
1. a constructed exit-76 failure was classified as deterministic;
2. the workspace was checked out at the failed commit;
3. a scripted stand-in agent made a permitted edit;
4. the copied-tree test suite passed;
5. the change was committed on `repair-<arm>-a2`;
6. attempt 2 was prepared, linted and submitted through the budget check.

The evaluate step was rehearsed for each outcome: score Job submission, pending, a score, an
INVALID line, and a failed score Job. A headless `claude -p` ran from a cron-like environment; each
call costs at least about USD 0.13 in fixed context.

**Needs Kai**, only the terminal approval (`SETUP.md`):
- The agent runners need no new Claude Code permissions. The Claude runner is limited to
  Read/Edit/Glob/Grep in the workspace, Codex uses its own workspace-write sandbox, and all
  `kubectl` calls are made by the harness itself.
- The crontab entry is installed by the agent after approval.

## 10. What this does not change

- K3, the r3 PVC rename and the other named holds stay in force.
- This is a separate campaign and launches nothing from the pilot program.
- Notifications stay in `NOTIFY.log`.
- Nothing is merged into the production code line or published.
- `REPORT.md` is written at the end in the established reporting style.

## 11. Amendments (Kai, 2026-10-08)

Recorded before the terminal approval. They are part of the protocol, and the sections above have
been updated to match.
1. 240 GPU-h is a maximum. The allocation includes failures and candidate-specific runtime.
   Fewer candidates are tried rather than raising the cap or using reserves (§8).
2. The first pair is run and interpreted before candidate compute is committed (§5, §7).
3. Within the approved scope I may select candidates, run diagnostics, confirm results and
   perform the follow-up without another routine approval.
4. Confirmation labels and the interval calculation are as in §5. Every seed is reported. The
   result is exploratory evidence, not a proof of improvement.
5. Progression is defined when the baseline, the reference or a candidate has no qualifying
   checkpoint. No score is fabricated and no unsuccessful seed is left out (§5).
6. Recovery after epoch 500 is described as recovery under continued training with the existing
   schedule, not attributed to the restart without an isolating comparison. Diagnostics are
   evidence about hypotheses, not diagnoses (§5).
7. Certification must cover operations a candidate adds at inference, at their actual precision.
   The binary-model definition and the resource constraint are unchanged (§6).
8. Before the first research submission, the scheduled execution path, budget enforcement, retry
   accounting and credential behaviour are finished and tested. What depends on an interactive
   login or on the home PC is stated (§9).
9. Existing holds and the separate production approval are unchanged.

