---
campaign: 2026-10-08-discovery-350k
phase: PREFLIGHT (build half)
owner: ml-engineer
date: 2026-10-08
status: built and tested locally; not reviewed; nothing submitted
---

# PREFLIGHT, build half

The pipeline for wave 1 is built. Two training handoffs and two score handoffs are prepared
offline: the baseline E-350k-C and the reference E-5M, 1,000 epochs each, one RTX 3090 per run.
They have not been submitted. The training code is the pilot's frozen tree, unchanged; only a
campaign directory with two generated configs was added. The pilot's CPU gate passes on both
configs, and the copied tree's full test suite passes on CPU.

The most important limitation is lint. `nrp_doctor.py lint` returns ERROR on both GPU Jobs when
run offline, because without `kubectl get nodes` it cannot see that RTX 3090 nodes exist. The
pilot's own r3 Job, which linted rc=1 with cluster access, fails the same way under the same
offline shim. A clean lint of these Jobs therefore still has to happen with cluster access.
`run_handoff.py launch --submit` runs that lint itself before it creates anything.

Other open items:
- the W&B run-id behaviour of re-attempts (§8);
- a CPU-replay tolerance chosen without data (§6);
- `eval/` and `tools/` are not under git (§8).

The next step is the critical review of this artifact.

## 1. Code

`code/` is its own git repository on branch `main`.

| commit | content |
| --- | --- |
| `90be22ed9dc6eff13c7dc911c801f401325e47d4` | base: pilot bundle 98dd2875. A byte copy of `campaigns/2026-10-05-pilot-program/code/tree`: 393 files, with `__pycache__`, `.pytest_cache` and `.git` excluded. |
| `d4f665929965878adca8e53a9ed6564c28a77f52` | `campaigns/d350/`: the generator, two configs, index, packs, `config_map.json`, byte copies of the pilot's `cpu_gate.py` and `monitor_p.py`, and `tests/test_d350.py` |

How the copy was verified:
- Every file's sha256 equals `manifests-98dd28/bundle-manifest.json`: 393 of 393, nothing extra
  or missing, mode bits preserved.
- The pilot's own `freeze_p.build_tarball`, run on the copy, reproduces bundle sha256
  `98dd2875b7c902bb881562a7acbf00f7cf266a369a74528b6fb8471e0cdc0059`.
- The per-file manifest is in `code/SOURCE.json`.
- The run_study code manifest sha of the d350 bundle is `e6ff034bfc44…a8e3`, the same value as
  the pilot's. The training code is unchanged; the added files are outside the hashed set
  (top-level `*.py` and `bnhgq2/*.py`).

The code is taken from a commit (`git archive`), never from the working tree.

| bundle | sha256 | ConfigMap |
| --- | --- | --- |
| training, commit d4f6659 | `36ce60986d541308cd355ffb266203f9bce326a660d88b6adacae3e42cec4b56` | `kai-d350-code-36ce60986d` |
| score: commit d4f6659 + `eval/` as `d350_eval/` (after review v1/v2 fixes) | `c0e30499c3bc34f3…` (see `attempts/score-*-s1.json`) | `kai-d350-score-c0e30499c3` |

## 2. Configs and their differences

`code/campaigns/d350/generate.py` produces both configs. They are linked from `configs/`; see
`configs/README.md` for the full table.
- **Baseline:** `d350-baseline-e-350k-s1` (sha256 `0e3c5454…b609`). The training settings equal
  `pilot1005-h1-e-350k-c-s1`. Only identity keys differ: name, arm, W&B group, study,
  revision_of, and `campaign.pilot` round/arm/hypothesis.
- **Reference:** `d350-reference-e-5m-s1` (sha256 `c0b65395…049b`). The same, plus
  `train.ebops.pid.target_ebops` 5,000,000 and `campaign.pilot.budget` 5,000,000. The generator
  also asserts that it equals the pilot's own `pilot1005-h2-e-5m-c-s1` apart from identity keys.
- **Stop epoch.** It is not a config key. The pilot stopped at 500 with `run_pack.py <pack> 500`.
  These Jobs use `run_pack.py <pack> 1000`. `train.epochs` stays 7000, and snapshots stay every
  500 epochs, so `snapshots/epoch-0500` and `snapshots/epoch-1000` are written.

## 3. Handoffs (prepared, not submitted)

`tools/prepare_attempt.py` and `tools/prepare_score.py` build every Job through the pilot's
`freeze_p.py`. They load it read-only, with its sha256 pinned in `tools/pinned.json`, and use its
`header`, `pod_exit_trap`, `pilot_tail`, `pilot_job` and `cpu_job` with the pilot R1 r3 options:
- bounded deadline;
- RSS gate off;
- the r3 node exclusion added to the pilot list;
- podFailurePolicy Ignore DisruptionTarget, FailJob on 10, FailIndex on 5/76/124/137/143;
- backoffLimitPerIndex 1;
- the same image, cache and GPU fingerprint gate.

Compared with the pilot's r2e Job for `pilot1005-h1-e-350k-c-s1`, the generated baseline Job
differs only in:
- name, labels and annotations;
- bundle and ConfigMap;
- `BNJ_RUN_ROOT`, `BNJ_CAMPAIGN_DIR`, `BNJ_STAGE` and the W&B tags;
- the stop epoch (1000) and the deadline (47,000 s);
- the added r3 node exclusion.

Re-running preparation reproduces the same handoff IDs.

| run | Job | handoff | pod deadline |
| --- | --- | --- | --- |
| baseline, attempt 1 (wave1) | `kai-d350-baseline-e-350k-s1-a1` | `handoffs/rh-dbfb5756bfb1252567b6ff4e` | 47,000 s |
| reference, attempt 1 (wave1) | `kai-d350-reference-e-5m-s1-a1` | `handoffs/rh-93b6a83ac87fdde400be0eb4` | 47,000 s |
| score of baseline a1 | `kai-d350-sc-baseline-e-350k-s1-a1-s1` | `handoffs/rh-18ad2899c6fb2645b594aee4` | 3,600 s, CPU only |
| score of reference a1 (`--expect-target 5000000`) | `kai-d350-sc-reference-e-5m-s1-a1-s1` | `handoffs/rh-239671074acfb0b7048c8691` | 3,600 s, CPU only |

Settings that apply to every handoff:
- **Brief.** `approval_ref` is `DISCOVERY-350K-2026-10-08`. The scientific gate is `cleared`,
  with the reference "Kai approval 2026-10-08, campaigns/2026-10-08-discovery-350k/APPROVAL.json".
  APPROVAL.json does not exist yet; it is Kai's terminal step (PROPOSAL §9).
- **Labels.** `campaign=discovery-350k-20261008` and `bnjettag.io/role` (`train` or `score`).
  Training Jobs also carry `bnjettag.io/stage` (`wave1`) and `bnjettag.io/attempt`. Score Jobs
  carry `bnjettag.io/run`.
- **Run root.** `/data/discovery-350k-20261008/attempts/<arm>-a<attempt>`. The run record is
  `<root>/runs/<config name>`. The data cache is the pilot's `/data/chang-n64-20260926/n64/data`,
  with data_info.json sha256 `c6d058f5…e228`, the same as the pilot handoff records.
- **Worst-case bound.** One GPU × 2 tries × 47,000 s = 26.1 GPU-h per training run (the
  harness's `gpu_bound` formula). The score Jobs request no GPU.

`run_handoff.py validate` and `launch` without `--submit` return VALID and OFFLINE_VALIDATED for
all four (no cluster calls).

`prepare_attempt.py` options:
- `--stage`, `--stop-epoch` (default 1000), and `--runtime-factor` (deadline 47 s × epochs ×
  factor).
- `--resume-from RUN_NAME`. The code supports resuming to a later stop epoch; a new test, §5,
  checks it. A resume continues the source's run directory to a later stop epoch (follow-up) or
  the same one (relaunch). It is refused unless the code manifest sha and the config equal the
  source's, which `ablation.restore_checkpoint` would also enforce.

Checked in a scratch copy of the campaign:
- resume to 2000;
- relaunch to the same stop;
- refusals: an earlier stop, the wrong arm, an unknown arm, a stop not on a snapshot boundary,
  an attempt id reused with different content, and a resume across a code change;
- factor 1.3 → 61,100 s;
- `prepare_score` refuses a candidate that edits a protected file (`bnhgq2/ebops_calc.py`,
  `ablation.majority_rule`) and accepts one that edits only the training loop.

## 4. Lint output

The lint ran with a failing `kubectl` shim first on PATH. The full log is `evidence/lint.log`.

```
kai-d350-baseline-e-350k-s1-a1      ERROR  NO product in the required list is reachable ...
                                     WARN   required-list product(s) match no node in the cluster: NVIDIA-GeForce-RTX-3090
                                     WARN   backoffLimitPerIndex=1: one blip kills an index. Suggest 3.
                                     note   no activeDeadlineSeconds   rc=2
kai-d350-reference-e-5m-s1-a1       (same three lines)                 rc=2
kai-d350-sc-baseline-e-350k-s1-a1-s1  OK                               rc=0
kai-d350-sc-reference-e-5m-s1-a1-s1   OK                               rc=0
control, pilot r3 kai-p1005r1-h1-e-350k-c-s2-98dd28-r3: same ERROR and WARNs, rc=2
  (rc=1 with cluster access, campaigns/2026-10-05-pilot-program/evidence/r3/lint-r3.log)
```

- **The ERROR.** It comes from offline mode: an empty node map, so nothing looks reachable.
- **The backoffLimitPerIndex WARN.** It is the pilot's accepted setting.
- **The "no activeDeadlineSeconds" note.** It refers to the Job level; the deadline is set at
  the pod level, as in the pilot.

**Unverified:** lint rc ≤ 1 with cluster access.

## 5. CPU gate and tests

Everything ran on the local CPU venv `/home/kaimoe/lab/.venvs/preflight-20261001` (TF 2.21.0,
keras 3.15.0, hgq2 0.1.9, numpy 2.5.0), on a `git archive` of commit d4f6659.

**`cpu_gate.py`** (byte copy of the pilot's, two configs, synthetic inputs, 68 s). Log:
`evidence/cpu_gate.log`. It exits 0, prints `PREFLIGHT_ALL_PASS 2 production 0 pilot_only 2`,
2 `CONFIG_PREFLIGHT_PASS` and 2 `PID_TRACED_ONLY_OK` lines (first feedback at epoch 10, span 9,
701 steps), and `PAIRED_INIT_OK E seed 1 arms 2`. For each config:
- 31,735 params;
- synthetic initial EBOPs 9,429,139;
- reload max abs difference 0.0;
- 0-bit floor 171,526, retraced;
- `TRACE_EVERY_OK k 10`, with 701 traced epochs.

The kernel hashes and LR landmarks equal the pilot's own gate output for
`pilot1005-h1-e-350k-c-s1` (`evidence/final-tree-98dd28/cpu_gate.json`). The one-step loss
differs by 5e-7 (2.5540538 against 2.5540543). The pilot ran in a different local venv; this is
not an issue for a synthetic check.

Not run locally, with the reason:
- **Threshold step.** It needs the N=64 cache, which exists only on the PVC.
- **`pair_nb.py`.** It concerns the pilot's NB arms; this campaign has none.
- **`gate_check.py` cpu-gate and pytest modes.** They are fixed to the pilot's 24 configs and
  166 tests. Their criteria were applied by hand above and below.

**Full suite** (`pytest tests analysis`): 170 collected, **168 passed, 2 skipped**, 0 failed,
583 s. The 2 skips are the pilot's known pair at `analysis/test_attn_entropy.py:142`. The
pilot's count was 164 passed and 2 skipped; the 4 new tests in `tests/test_d350.py` account for
the difference. Evidence: `evidence/pytest.log` and `evidence/pytest.xml`. The new tests cover:
- the generator reproducing the committed configs;
- only the stated keys differing;
- the byte copies;
- **resume to a later stop epoch.** A tiny run paused at 6 and resumed to 9 equals a run taken
  straight to 9: per-epoch records, controller telemetry, selected checkpoints and the snapshot.

## 6. Score

`eval/score.py` implements PROPOSAL §4 by reusing byte copies of the pilot's `readout_pilot.py`,
`certify_ebops.py`, `nondegenerate_threshold.py` and `analysis/attn_entropy.py`. Their sha256 and
that of `score.py` are in `eval/MANIFEST.json` (sha256 `96a8862d…cb0b`). The scorer checks them
before running. `eval/README.md` lists every condition and input check, and states that any
candidate adding inference operations needs its certify_ebops coverage verified before its score
is accepted.

**Tests** (`eval/tests/test_score.py`): **29 passed** in 16 s. They cover:
- the valid path, with every secondary field checked;
- the frozen tie-break (AUC, then lower EBOPs, then the earlier epoch);
- the reference at 5M;
- idempotent reruns;
- 22 INVALID cases, including no feasible checkpoint, degenerate or at-floor epochs, divergence,
  a missing snapshot, a record gap, threshold/labels/floor mismatches, the runner's choice
  differing, a certification failure, CPU-replay disagreement, a split mismatch, tampered eval
  files, a conflicting score.json, and an internal error;
- the real threshold script on a small cache;
- one end-to-end case. The frozen runner trains a tiny model on CPU; the real `certify_checkpoint`
  returns CERTIFIED and the CPU replay matches within 1e-7; a tampered log is then INVALID.

**Pod-layout check.** The score bundle was extracted and `score.py` run from
`code/d350_eval/`. It passed the manifest check and printed one `INVALID: run directory missing`
line, exit 2. The Job's setup trap was exercised in bash: a failure before `score.py` starts
ends the log with `INVALID: score job setup failed exit=<rc> line=<n>`.

**Local CPU timing** (`evidence/cpu_timing.json`). Synthetic E model, 2 TF threads, the same
thread settings as the Job:
- 62,000-row full trace: 37 s, extrapolated to 333 s for the 558,000-row training split;
- 62,000-row predict: 48 s.

This supports the 3,600 s deadline. It was measured on the home CPU, not on an NRP node.

## 7. Protocol and method checks (advisory)

**`lab_check_protocol`** on `protocol-wave1.json`: `structural_valid: true`, no findings, no
drift, `matches_snapshot: false`. No `baseline_path` was given, because this campaign has no
STUDY.md and so no frozen STUDY snapshot. PROPOSAL.md is the design document. Freezing a
snapshot belongs to the design phase.

**`jev_check_methods`** on the method text of §2-§3: see §9.

## 8. Unverified, and where I am not sure

- **Cluster lint** of the GPU Jobs (§4).
- **The Jobs themselves.** None has run on NRP: not the pod scripts, the pip install, the
  fingerprint gate on a 3090, the score Job on the real cache, nor its CPU time there.
- **APPROVAL.json does not exist.** The briefs cite it; submission waits for Kai's terminal
  approval (PROPOSAL §9).
- **W&B run id.** BNJ_STAGE is restricted to the frozen list in `bnhgq2/wandb_util.py`, so these
  Jobs use `production`. That value only keys the W&B run id and gives group suffix ''; it is
  not the K3 production run. The run id is sha256(stage, config name). A *fresh* re-attempt of
  the same arm (new run directory) therefore reuses the earlier attempt's W&B run. Its W&B
  history is then mixed or dropped. The PVC records, which are the score's only input, are
  unaffected, and a `--resume-from` relaunch keeps the same run on purpose. A fix needs a
  `wandb_util` change, which is a code change to the baseline line and needs review.
  `DECISION: BNJ_STAGE=production. CONFIDENCE: MEDIUM. FLAG FOR HUMAN: YES.`
- **CPU-replay gate.** The score is INVALID when the replayed accuracy of the selected
  checkpoint differs from the logged GPU value by more than 1e-3 (62 jets). No GPU-vs-CPU
  measurement at full size exists, so a false INVALID is possible.
  `CONFIDENCE: LOW. FLAG FOR HUMAN: YES.`
- **`eval/` and `tools/` are not under git.** The lab root is not a repository. Their integrity
  rests on `eval/MANIFEST.json`, which the scorer enforces, and on these sha256 values:
  - `tools/d350_common.py` `5617f92a…2834`
  - `tools/prepare_attempt.py` `d00ebbe0…4104`
  - `tools/prepare_score.py` `7ca3705d…0198`
  - `tools/pinned.json`: the pilot `freeze_p.py`, the training-batch `freeze.py`,
    `nrp_doctor.py` and `run_handoff.py`.

  A change to `nrp_doctor.py` (for example to KNOWN_BAD_NODES) makes every preparation refuse
  until the pin is updated, by design.
- **Not built here.** The hook refusing direct `run_handoff.py launch --submit` for this
  campaign's handoffs (PROPOSAL §9) is not built; it is outside my scope (`.claude/`). The
  harness BRIEF/`prepare_command` wiring, `ideas.json`, and confirmation-seed configs (s2-s4)
  are also not built. The confirmation seeds need one generator change and a new commit.
- **Score trust boundary.** The records of non-selected epochs, which feed the secondary
  measurements, are trusted as logged. A candidate edits `run_training`, which writes them.

## 9. Method check result (Jev, advisory; audit `jv-d1fde91970734dd0aa45272f27dcd1e9`, model jev-1.13.0)

The input was a one-paragraph method text: §1-§3 condensed, plus the selection rule. Jev's
dispositions, quoted, with my reading. Jev's answers are not a verdict.

| rule | choice (confidence) | disposition | reading |
| --- | --- | --- | --- |
| selection | consistent (1.00) | suggestion | — |
| comparability | consistent (0.41) | review | Baseline and reference share every setting but the target; low confidence, unresolved. |
| uncertainty | not_applicable (0.25; missing 0.42) | review | Single seed by design (stage A, PROPOSAL §5). The text states no resolving power. Seed spread at this horizon is unknown (PROPOSAL §5 margins). Open. |
| provenance | conflict (0.57) | **mandatory review** | Jev names no specific conflict. The candidate cause is that "frozen tree" and "commit adds configs" sit together, or that the cache has no checksum beyond data_info. Both are documented in §1-§3. The critical reviewer should check this. |
| metrics | conflict (0.35; missing 0.44) | **mandatory review** | The text gave accuracy as the score without macro AUC beside it. The lab rule is accuracy beside AUC, never instead. The score is accuracy-first by PROPOSAL §4, and `score.json` records the selected checkpoint's macro AUC. Whether that satisfies the rule needs review. |
| authority | missing (0.88) | review | Correct: APPROVAL.json does not exist yet (§8). |

## Changes after the PREFLIGHT reviews (orchestrator, 2026-10-08)

Review v1 (ITERATE: A1, B1-B3, C1-C2) and v2 (ITERATE: B2 glue, B4, B5) are in `review/`. Their
fixes:
- `eval/` (score.py `9fddbdd6…`):
  - a NaN attention head no longer invalidates a score;
  - results are written per score attempt (`score-s<k>.json`);
  - INVALID lines carry a class from `eval/INVALID_REASONS.json`: scientific, diverged, evaluator
    or infrastructure.
- `tools/evaluate_d350.py`:
  - reads the score Job's log whether the Job ended Complete or Failed;
  - makes one more score attempt for evaluator and infrastructure classes. `prepare_score.py`
    passes `--score-attempt` from attempt 2 on, and a setup failure is printed as infrastructure.
- `tools/relaunch_d350.py` and `tools/workspace_d350.py`:
  - a relaunch uses the failed attempt's commit;
  - infrastructure and deadline relaunches resume the run, and a code repair starts fresh on a
    repair branch.
- Score handoffs prepared before each fix were never submitted. They are kept under
  `superseded/score-eval-v1..v3/`. Current score handoffs: `rh-18ad2899…` (baseline) and
  `rh-23967107…` (reference); both lint OK with the live node map.
- Tests:
  - `eval/tests` 34 passed;
  - `tools/tests/test_evaluate_d350.py` 4 passed (stubbed kubectl, real prepare tools on a copy);
  - harness 39+ passed.

The resolution against each v2 condition is in `review/PREFLIGHT_resolution.md`.

