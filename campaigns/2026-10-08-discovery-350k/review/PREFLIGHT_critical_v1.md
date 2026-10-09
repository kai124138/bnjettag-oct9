---
campaign: 2026-10-08-discovery-350k
phase: PREFLIGHT (build half), wave 1 only
reviewer: critical-reviewer (solo)
date: 2026-10-08
artifact: PREFLIGHT.md (status "built and tested locally; not reviewed; nothing submitted")
verdict: ITERATE
---

# PREFLIGHT critical review v1, wave 1

Scope: the training Jobs `kai-d350-baseline-e-350k-s1-a1` and `kai-d350-reference-e-5m-s1-a1`,
their score Jobs, and the glue that turns a finished Job into a recorded score. This review was
read-only: nothing was submitted and no kubectl call was made.

**Verdict: ITERATE.** One A finding and three B findings. The training Jobs are what PREFLIGHT
says they are. The configs differ from the pilot only in identity keys and the reference target.
The evaluator reuses the pilot's code byte for byte. The ROC-test set cannot be reached from any
code path. The defect is in the evaluate glue. An INVALID score, a designed outcome of PROPOSAL §5,
never reaches the record as INVALID: the harness records it as "evaluation failed". Two smaller
paths can also turn a valid run into a permanent INVALID. All four fixes are small, and none of
them touches training code or configs.

## 1. Configs and the binary-model definition: as stated

I recomputed a flattened diff of both d350 configs against
`campaigns/2026-10-05-pilot-program/code/tree/campaigns/pilot1005/configs/pilot1005-h1-e-350k-c-s1.json`:
- **Baseline.** Only `name`, `experiment.arm`, `experiment.group`, `campaign.study`,
  `campaign.revision_of` and `campaign.pilot.{round,arm,hypothesis}` differ.
- **Reference.** The same keys, plus `train.ebops.pid.target_ebops` and `campaign.pilot.budget`,
  both 350000 → 5000000.
- **Reference against the pilot's own E-5M rung** (`pilot1005-h2-e-5m-c-s1`). Only identity keys
  differ.

This matches `configs/README.md:91-99`. The binary-model definition is unchanged:
`quant.weight = binary_absmean`, d_model 24, 2 heads, 1 layer, FFN 32, `act_bits` 8, pT gate 2.0,
features pt/etarel/phirel. The selection settings are also unchanged:
`selection_metric = val_categorical_accuracy` and `cost_before_auc = False`, so the runner's key
`ablation.py:387-395` equals readout_pilot's `key` (`eval/readout_pilot.py:96-98`).

The stop epoch is not a config key. The Job script passes `run_pack.py "$PACKS" 1000`
(baseline job.json, `args[0]`). Neither the LR schedule nor the target depends on
`train.epochs = 7000`:
- `training_target` (`ablation.py:163-168`) has no `target_schedule` in these configs;
- `chang_cosine_restarts` (`ablation.py:128-146`) has period 500, so epoch 1,000 is a cycle
  boundary.

Zero-based epochs 499 and 999 are traced (`ablation.py:516-522`, k = 10).

The Job diff against the pilot's r2e Job (`manifests-98dd28-r2e/r1-h1-e-350k-c-s1-job.json`)
contains only what PREFLIGHT §3 lists:
- bundle sha, ConfigMap, BNJ_RUN_ROOT, BNJ_CAMPAIGN_DIR, BNJ_STAGE and the W&B tags;
- stop 1000 and deadline 47,000 s;
- the added node `hcc-chase-shor-c4715.unl.edu`;
- labels and annotations;
- the run_handoff init container added by `prepare`.

The podFailurePolicy and `backoffLimitPerIndex: 1` are identical to the pilot's.

## 2. Evaluator against PROPOSAL §4

**Byte copies.** sha256 recomputed. The four copies equal the pilot tree's files, and
`eval/MANIFEST.json` lists exactly these hashes, plus score.py at `672128ab…8c0a`.

**Conditions.** score.py implements each condition of §4:

| PROPOSAL §4 condition | score.py | readout_pilot equivalent |
| --- | --- | --- |
| traced, EBOPs ≤ target, above the 0-bit floor | `feasible_points` :158-163 | `read_arm` :128, :147 |
| acc > threshold, threshold = THRESHOLD_C | :163, with the threshold re-derived from y_val :258-261 | :149-151 |
| selection key (acc, AUC, −EBOPs, −epoch) over epochs < stop | `readout.records(run, stop)` :242; `max(feas, key=readout.key)` :263 | :76-98 |
| runner choice must equal the recomputed one | :264-271 (stricter: also compares acc, AUC and EBOPs) | :160 (epoch only) |
| certification | `cert.certify_checkpoint` :280-284 (CERTIFIED only) | `certify_ebops.py` :75-98 |
| INVALID on failure, no number | `need()` raises Invalid; stdout prints `repr(score)` only when status is valid and code is 0 (:354-355) | n/a |

**No number for INVALID.** No code path prints a number for an INVALID run. The outer handler
(:348-353) catches failures in `write_report` too.

**Uses beyond the pilot.** score.py calls `certify_checkpoint` directly, not `certify_ebops.main`.
That is a faithful reuse, but it skips `main`'s `apply_keras_compat()` and TF32 setting
(:121-122):
- compat is still applied, because `hooks['load_arrays']` → `run_engram.load_cache` →
  `runtime()` (`code/run_engram.py:100-106,180`) runs before certify and replay (:276);
- TF32 does not apply on CPU.

**The 1e-3 CPU-replay tolerance** (score.py:57, :285-288). The logged accuracy is already the
prediction of the serialized file, reloaded on the GPU (`ablation.py:1011-1026`). The replay
therefore measures only GPU-versus-CPU kernel differences, with TF32 off in training
(`NVIDIA_TF32_OVERRIDE=0`). 1e-3 is 62 of 62,000 jets. A larger disagreement needs many
near-tied jets, or a quantizer boundary flip that cascades. The second can happen under WRAP
overflow, but it is rare.
- **False INVALID.** Judged low but unmeasured. The lab's only evidence is certification, not
  accuracy: CPU certification of GPU-trained checkpoints agreed exactly, relative difference 0.0,
  2 runs / 4 files (`campaigns/2026-09-26-training-batch/READOUT_epoch500.md:138-144`). A wrong
  score cannot slip through the tolerance unnoticed: the reported score is the logged value, and
  1e-3 is a twentieth of the 0.02 screening margin (§5).
- **The larger risk** is what happens after a replay mismatch: see B2 and B3.

## 3. Validation/test separation: holds by code, not by mount

- The cache's `data_info.json` (pilot capture) lists only `x_train`, `y_train`, `x_val` and
  `y_val`.
- `run_engram.load_cache` reads only those four arrays (`code/run_engram.py:197-198`).
- score.py, certify_checkpoint, nondegenerate_threshold and attn_entropy.analyze (given `x_val`)
  never open a test path.
- `certify_ebops.main`, which imports `evaluate_roc`, is not called.

The training and score Jobs mount the whole `kai-data` PVC read-write (job.json volumes), as the
pilot did. So separation rests on code, not on permission (C3).

## 4. Job safety

- **Run root.** `/data/discovery-350k-20261008/attempts/<arm>-a<n>`, guarded by asserts:
  - `prepare_attempt.py:133-134` refuses `PILOT_PVC_ROOT`;
  - `prepare_attempt.py:168-169` asserts the run root and the stop epoch in the script.
- **No pilot file written.**
  - run_study and run_pack write only under `BNJ_RUN_ROOT` (`run_study.py:55,107`;
    `run_pack.py:73,88`).
  - The fingerprint check reads the anchor cache only.
  - `freeze_p.py` is loaded with a pinned sha and has no module-level writes (the writes at
    :204-207 are inside the `DIAG_PY` string).
  - The handoff init container writes `/data/run-handoffs/rh-<id>`, a directory of its own.
- **Deadline and GPU bound.**
  - Pod `activeDeadlineSeconds` 47,000 = 47 s × 1,000 epochs (PROPOSAL §8).
  - One GPU, `backoffLimitPerIndex` 1. `harness.gpu_bound` (`tools/harness.py:439-462`) gives
    1 × 2 × 47,000 / 3,600 = 26.1 GPU-h per run.
  - Two runs come to 52.2 GPU-h, within the wave-1/search cap of 90 (240 − 90 − 60;
    `stage_cap` :631-636).
  - Score Jobs request no GPU, so their bound is 0.
- **BNJ_STAGE.** Read only by `wandb_util.run_stage` (:73-79), `stage_run_id` (:82-86) and
  `stage_group` (:89-94), via `ablation.py:955-961` and `run_study.py:105-106`. A search of the
  lab's tools (run_handoff, nrp_doctor, harness) finds no other reader.
  `cfg.campaign.production` is False (cpu_gate prints `production 0`, `evidence/cpu_gate.log:9,13`).
  So the only effect is the W&B id and group, as BRIEF:27-29 states.

## 5. Findings

### A1. A real INVALID is recorded as "evaluation failed", never as INVALID (blocking)

The chain:
- `score.py` exits 2 on INVALID (:340) and 3 on an internal error (:345). The score Job runs it
  with `exec` (`prepare_score.py:133`), and `backoffLimit` is 0.
- So every INVALID ends as a **Failed** Job.
- `tools/evaluate_d350.py:63-65` exits 2 on `Failed`, with "score job … failed" on stderr. It
  neither reads nor saves the log; the log is saved only on `Complete`, at :69-70.
- The INVALID branch at :72-74 is reachable only from a `Complete` Job, which exits 0. score.py
  never prints INVALID with exit 0, so the branch is dead.
- The harness (`tools/harness.py:795-806`) therefore takes the `returncode != 0` path: "evaluation
  … failed; no score recorded". It records no `evaluation valid: False` event and queues no
  interpret step.

Consequences:
- PROPOSAL §9 says "An INVALID result is recorded as INVALID", and §5 builds the
  baseline-INVALID and reference-INVALID branches on that. The real path does neither.
- The harness test (`tests/test_harness.py:444`) simulates an evaluate command that prints
  INVALID with exit 3. That is not what evaluate_d350 does against a real Job.

**Condition.** On `Failed`, evaluate_d350 fetches the log and saves it under `evidence/scores/`.
If the last line starts with `INVALID`, it prints that line and exits 3. Only a log with no
INVALID line is an evaluation failure, exit 2. Add a test that runs evaluate_d350 with a stubbed
kubectl returning a Failed Job whose log ends in `INVALID: no feasible checkpoint …`.

### B1. A non-finite attention entropy turns a valid score into INVALID

- `attn_entropy.analyze` returns NaN for a head whose softmax rows all sum to zero
  (`eval/attn_entropy.py:69`, `:130`, `a['sum']/a['rows']` with rows = 0).
- `score.entropy` returns that `heads` list unchanged in its failure branch (score.py:144-145).
- `write_report` serializes with `allow_nan=False` (:302). The ValueError reaches the outer
  `except Exception` (:351-353), which prints `INVALID: internal error ValueError`, exit 3, and
  writes no score.json.

The docstring at :149 says the secondary "never changes the score". A head whose output
activation width the controller drives to 0 bits is plausible at 350k, and attention collapse is
the very failure this campaign studies. The pilot readout treats this case as a recorded problem
(`readout_pilot.py:101-105,173-174`), not as a crash.

**Condition.** Replace non-finite head values by `null` with a reason before the report is
written, and add a test with a NaN head.

### B2. A first score.json fixes the result for good, including transient failures

- `write_report` refuses any rerun whose primary result differs from the existing
  `RUN_DIR/score.json` (:303-306).
- An internal error that happens after `score_run` starts writes an INVALID score.json (:341-347):
  an import error, a memory error, the `ValueError` of a cache read.
- `prepare_score` never passes `--out` (:133), so a second score attempt `-s2` writes to the same
  path and reports INVALID forever.
- `evaluate_d350` has no path to a second score attempt at all: `st['submitted']` fixes s1,
  :44 and :60.

This also blocks the remedy BRIEF:30-32 names for a replay mismatch: re-checking it as a possible
evaluator defect cannot produce a valid score at that path.

**Condition.** Do two things:
- write the score to `RUN_DIR/score-s<k>.json`, so the refusal applies within one score attempt;
- give evaluate_d350 an explicit second score attempt, reserved for internal-error and
  evaluator-suspect INVALID reasons and recorded with its reason.

The idempotence test still applies within an attempt.

### B3. An INVALID reason is not classified, so the wave-1 validity check can misread one

- PROPOSAL §5 reads a baseline INVALID as "no qualifying checkpoint in 1,000 epochs" and a
  reference INVALID as "protocol or evaluator suspect".
- score.py has 22 reasons. Only "no feasible checkpoint in epochs < stop" (:266) is a scientific
  outcome.
- Most others are infrastructure or evaluator states: snapshot missing after a deadline kill,
  CPU replay mismatch, certification mismatch, an existing score.json, internal error.
- Nothing in the glue or the brief maps a reason to a class. The interpret agent gets only the
  string.
- The 47,000 s deadline leaves about 16 % over the slowest measured rate, 38.8 s/epoch
  (PROPOSAL §2). A deadline kill near epoch 1,000 therefore gives "snapshot epoch-1000 missing".
  An agent could read that as "baseline does not qualify".

**Condition.** Add a frozen table, in `eval/README.md` and the harness record, that maps every
score.py reason to one of three classes:
- **scientific**: only "no feasible checkpoint";
- **evaluator-suspect**: replay mismatch, certify mismatch, threshold re-derivation mismatch;
- **infrastructure**: everything else.

evaluate_d350 records the class beside the reason. Only the scientific class may enter the §5
branches. A CPU certification mismatch gets the GPU re-run the training-batch STUDY prescribed
(certify_ebops.py:29-31).

### C findings (recorded, not blocking)

- **C1. An infrastructure relaunch builds from `main`, not from the failed commit.**
  `relaunch_d350.py:132,138-140` passes `--branch main`, and `prepare_attempt` resolves the
  *current* main (:93-94). The HEAD check at :128-131 compares the workspace, not the ref used.
  The code is still recorded (the attempt record holds the commit), but it can differ from the
  failed attempt's if main moves while wave 1 runs; confirmation configs go on main. Pass
  `--branch <rec['commit']>`.
- **C2. A relaunch after a deadline kill starts from epoch 0.** relaunch_d350 never uses
  `--resume-from`, which prepare_attempt supports. That costs up to 26 GPU-h again. Use
  `--resume-from` for the deadline class.
- **C3. The PVC is mounted read-write in the score Jobs.** Separation rests on code. Acceptable
  as in the pilot; noted.
- **C4. A re-attempt reuses the W&B run id** (`stage_run_id`). A repair relaunch with a changed
  `code_sha256` in the W&B config may be refused by `wandb.init(resume='allow')` when a config
  key changes. Unverified, and outside wave-1 attempt 1.
- **C5. The resume guard covers only part of the bundle.** The manifest sha covers top-level
  `*.py` and `bnhgq2/*.py` only. A resume across commits that changes `requirements-training.txt`
  passes it.
- **C6. A follow-up rescore at stop 2000 collides with the stop-1000 score.json.** It writes to
  the same `score.json` and would be refused. This needs a per-stop output, and the B2 change
  covers it.
- **C7. The validity check is a single-seed gap.** It is a screening decision. "Within 0.05" is
  not to be reported as a measured gap without seeds and an interval.
- **C8. Recommended cross-check.** The d350 baseline repeats `pilot1005-h1-e-350k-c-s1` (same
  config apart from identity keys, same seed) for epochs 0-499. Comparing its epoch-500 record
  with the pilot's epoch-500 read checks the pipeline. It is not a result.
- **C9. Lint and Jobs not yet run with cluster access.** Cluster lint rc ≤ 1 and a first real
  run of the score Job on the NRP cache are still unverified (PREFLIGHT §4, §8). APPROVAL.json
  does not exist. Both remain preconditions for submission.

## 6. What would make wave 1 uninterpretable

A1 and B3 together. A baseline or reference INVALID would arrive as "evaluation failed", or as an
unclassified reason, and the §5 branches could not be applied correctly. B1 can turn a valid
collapsed-attention baseline into INVALID, which biases the reading toward "does not qualify".
With A1, B1, B2 and B3 fixed, the pair answers the §5 validity question as designed.

## 7. Jev (advisory; audit `jv-d2bcca429c554cba92bafe8532d7cc94`, jev-1.13.0)

Jev's dispositions are quoted with my reading beside them. They are not part of the verdict.

| claim | Jev | my reading |
| --- | --- | --- |
| "An INVALID result is recorded as INVALID" vs evaluate_d350.py:60-74 | supported (0.53), review | Disagree. The branch exists but cannot be reached (A1). |
| CPU certification agreed exactly, READOUT_epoch500.md:138-144 | overstated (0.41), review | Holds for 2 runs / 4 files only; quoted with that n above. |
| "Secondary measurements never change the score", score.py:135-150 | supported (0.66), review | Disagree. The NaN serialization path breaks it (B1). |
| BNJ_STAGE only keys the W&B id and group, wandb_util.py:58-95 | overstated (0.36), review | Confirmed by search; no other reader. |

`lab_check_protocol` was not re-run. PREFLIGHT §7 records `matches_snapshot: false`, because no
frozen STUDY snapshot exists. That is unchanged and stays visible.

## 8. Re-review checklist

Before PASS, each of these is checked by name: A1, B1, B2 and B3, each with its test. C1 and C2
are recommended in the same patch, since they touch the same glue.
