# Campaign brief: discovery-350k-20261008

The protocol is `PROPOSAL.md` (v2, amended 2026-10-08, §11). This brief holds the
machine-readable limits that `tools/harness.py` enforces. Kai approves with
`python3 tools/harness.py approve campaigns/2026-10-08-discovery-350k --by Kai` at a terminal,
which writes `APPROVAL.json` bound to the exact block below. Any later edit to the block voids
that approval, and submissions are refused until Kai approves again.

## Question and hypothesis

Which training or architecture change keeps the binary-weight N=64 E tagger's validation accuracy
when the EBOPs controller squeezes it to 350,000 EBOPs? Wave 1 (baseline E-350k-C and reference
E-5M, seed 1, 1,000 epochs, full data) is run and interpreted before any candidate compute.

## Objectives and reserved settings

- Primary score: `eval/score.py`, best feasible validation top-1 accuracy (PROPOSAL §4).
- Reserved to Kai: publication-ready claims, public releases, external messages, any 7,000-epoch
  production run (K3), and any change to the binary-model definition, N=64, the 350k target, the
  data split or the evaluator outside the protocol's evaluator-defect rule.
- Repairs may change only the training-loop and build files listed in `repair_paths`. They may
  not change configs, quantizers, data, EBOPs code or tests. A scientific change is a new
  hypothesis on its own branch, not a repair.

## How scientific settings are protected during repair

- `repair_paths` admits only training-loop and build files. A repair that edits a config, a
  quantizer, data, EBOPs or evaluator file is refused, and the workspace is restored.
- `repair_test_command` (`tools/repair_check_d350.py`) first re-runs the CPU gate for the repaired
  arm and compares every field with the frozen fingerprint `settings/wave1-fingerprint.json`
  (listed in `frozen_files` below, checked before every submission). The fields cover the learning rate at the schedule
  landmarks, optimizer, one training step at the configured batch size, parameters, initial
  kernels, EBOPs and the 0-bit floor, quantizer decay speeds and trace cadence. Any difference is
  refused as a scientific-setting change. Then the copied test suite must pass.
- The fingerprint does not cover the PID gains or data handling beyond one training step.
- `scientific_settings` (a per-key JSON check) is empty, because no config file is editable in a
  repair. `interpret_command` is empty, because the interpretation step uses the configured
  runner (`runner: claude`); that key is used only by the simulated runner in tests.

## Candidate implementation (keys fixed before approval)

A queued `implement` task runs these steps, each saved so that a resumed task continues after the
last one finished:
1. A branch `cand-<node>` is created from the parent node's recorded commit.
2. Codex (`implement_runner`, gpt-6.1-sol, workspace-write sandbox) receives the node's
   specification.
3. The diff is checked against `candidate_paths` and `candidate_protected`. A modified existing
   test is also refused.
4. Claude (`review_runner`) reviews the diff against the specification and the protocol, and
   writes a verdict. Only PASS continues.
5. `candidate_check_command` runs:
   - the copied test suite;
   - the wave-1 settings fingerprint, unchanged;
   - the CPU gate for the new config, which must pass and is then frozen as the candidate's own
     fingerprint;
   - certification coverage for added inference operations.
6. The change is committed, `candidate_prepare_command` builds a versioned handoff, and it is
   submitted through `harness.py submit --stage search`.

## GPU-hour accounting, stated exactly

240 GPU-h is the campaign maximum. The mechanism (`gpu_bound_mode: "hard"`):
- **Per Job (enforced by Kubernetes, not by the home PC).**
  - Every campaign training Job carries a Job-level `activeDeadlineSeconds` of twice its pod
    deadline (1,000 epochs: 94,000 s). Kubernetes ends all of the Job's pods at that time:
    retries, and pods replaced after ignored disruptions, alike.
  - With `parallelism: 1` and `podReplacementPolicy: Failed`, at most one pod holds a GPU at a
    time. So the Job's GPU time ≤ 1 GPU × (Job deadline + 180 s termination grace + 300 s
    controller margin). For 1,000 epochs that is 26.24 GPU-h.
  - `harness.py submit` refuses any GPU Job without these properties.
- **Campaign (enforced by `harness.py submit` before every submission).** The new Job's bound,
  plus committed use, must fit the stage cap (240 minus later-stage reserves). Committed use is
  the measured use of finished Jobs plus the bound of every unfinished one.
  - Harness relaunches and repairs are new Jobs and are reserved the same way.
  - So the GPU time of all campaign Jobs submitted through the harness stays at or below 240 GPU-h,
    provided Kubernetes enforces Job deadlines as documented. That has not yet been observed on
    NRP for this campaign: it is a submission control backed by Kubernetes deadlines, not a
    measured consumption ceiling.
- **If the guarantee fails anyway.** A Job's measured use above its bound means the guarantee did
  not hold. The monitor then stops all further submissions and reports it (test
  `test_measured_use_above_the_bound_stops_submissions`).

Residual risks:
- Kubernetes ending a Job later than the 480 s allowed (180 s grace plus 300 s margin).
- GPU Jobs created outside `harness.py submit`. A hook blocks direct submission from Claude Code
  sessions, and the Codex sandbox has no cluster access, but Kai's own terminal is not covered.
- The Job deadline also counts queue time. A Job queued for long loses its retry allowance, and
  one queued past 26 h is ended before it starts, using no GPU time. Both are a cost to the
  experiment, not to the budget.

## Known issues carried into the run

- `BNJ_STAGE=production` in the Job only keys the W&B run ID. It is not the K3 production run.
  A re-attempt of the same config appends to the earlier attempt's W&B run. The PVC records the
  score reads are per attempt and unaffected.
- The score is INVALID if the CPU-replayed accuracy differs from the logged value by more than
  1e-3. That tolerance has not been measured between GPU and CPU. A replay-mismatch INVALID is
  treated as a possible evaluator defect (PROPOSAL §3), not as a result.

## Machine-readable policy

### Authority (approval-bound: commitments, permissions, protected commands)

```json authority
{
  "campaign": "discovery-350k-20261008",
  "gpu_h_max": 240.0,
  "reserve_gpu_h": {
    "confirm": 90.0,
    "followup": 60.0
  },
  "stage_order": [
    "wave1",
    "search",
    "confirm",
    "followup"
  ],
  "gpu_bound_mode": "hard",
  "max_concurrent_gpu_jobs": 4,
  "elapsed_days_max": 8,
  "elapsed_behavior": "review",
  "candidate_attempts_max": 5,
  "repairs_total_max": 6,
  "infra_relaunches_max": 2,
  "agent_invocations_max": 40,
  "runtime_factor_max": 3.0,
  "approval_ref": "DISCOVERY-350K-2026-10-08",
  "namespace": "cms-ml",
  "selector": "campaign=discovery-350k-20261008",
  "notify_channels": [
    "file"
  ],
  "dispatch_actions": [
    "implement",
    "submit",
    "stop",
    "escalate"
  ],
  "runner": "claude",
  "implement_runner": "codex",
  "review_runner": "claude",
  "codex_model": "gpt-6.1-sol",
  "runner_command": null,
  "interpret_command": null,
  "workspace": "code",
  "repair_paths": [
    "bnhgq2/ablation.py",
    "bnhgq2/train.py",
    "bnhgq2/build.py",
    "bnhgq2/store.py",
    "bnhgq2/compat.py",
    "bnhgq2/config.py",
    "run_pack.py"
  ],
  "candidate_paths": [
    "bnhgq2/*.py",
    "campaigns/d350/*.py",
    "campaigns/d350/configs/*.json",
    "campaigns/d350/index.json",
    "campaigns/d350/packs/*.json",
    "campaigns/d350/config_map.json",
    "tests/test_d350_*.py"
  ],
  "candidate_protected": [
    "bnhgq2/data.py",
    "bnhgq2/ebops_calc.py",
    "bnhgq2/ebops_target.py",
    "campaigns/d350/cpu_gate.py",
    "campaigns/d350/monitor_p.py",
    "campaigns/d350/configs/d350-baseline-*",
    "campaigns/d350/configs/d350-reference-*"
  ],
  "interpret_paths": [
    "ideas.json",
    "plan/*",
    "notes/*"
  ],
  "scientific_settings": {},
  "repair_test_command": [
    "/usr/bin/python3",
    "{cdir}/tools/repair_check_d350.py",
    "{job}"
  ],
  "prepare_command": [
    "/usr/bin/python3",
    "{cdir}/tools/relaunch_d350.py",
    "{job}",
    "{attempt}",
    "{cls}"
  ],
  "workspace_command": [
    "/usr/bin/python3",
    "{cdir}/tools/workspace_d350.py",
    "{job}"
  ],
  "evaluate_command": [
    "/usr/bin/python3",
    "{cdir}/tools/evaluate_d350.py",
    "{job}"
  ],
  "candidate_check_command": [
    "/usr/bin/python3",
    "{cdir}/tools/candidate_check_d350.py",
    "{node}"
  ],
  "candidate_prepare_command": [
    "/usr/bin/python3",
    "{cdir}/tools/prepare_candidate_d350.py",
    "{node}",
    "{attempt}"
  ],
  "frozen_files": {
    "settings/wave1-fingerprint.json": "1c1daa9ca35784bf811db57099e4483c1cf5f88308df6bd915e9f03e99d609bb",
    "eval/MANIFEST.json": "edb04f7a556e51d95bae98e9bb169dd7c326daf48fe15643aa7ec2ba5bb8dc7e",
    "eval/score.py": "9fddbdd67eeaa500b434554ecd77bd5ed376c1a69d09b94e5483527e5c186279",
    "eval/INVALID_REASONS.json": "aa33499f83f407b652ea68b206b6e05c75781d3d81c97896be17d8fd0c49d514",
    "tools/repair_check_d350.py": "998daed31bf322c99c35f16e5a2c15b16547bd1333eb5d4f6f24fe98114c3432",
    "tools/evaluate_d350.py": "1ad09d2e0e4ebfe64c1c4229e589372eda0280cd8c740ae37f6d98c6e37b06bd"
  }
}
```

### Operations (not approval-bound; validated against the authority block)

The agent may change these within the ranges the authority block allows. `python3 tools/harness.py validate <campaign dir>` checks both blocks; see docs/agent-harness.md, "How Kai changes a rule".

```json operations
{
  "deadline_seconds_per_epoch": 47,
  "candidate_runtime_factor": 1.3,
  "runtime_factor_notify": 1.5,
  "score_deadline_s": 3600,
  "lease_s": 3600,
  "infra_relaunches_per_key": 2,
  "repair_attempts_per_class": 3,
  "agent_invocations_warn": 30,
  "elapsed_days_warn": 6,
  "kubectl": "/home/kaimoe/.local/bin/kubectl",
  "codex_bin": "/home/kaimoe/.vscode-server/extensions/openai.chatgpt-26.51002.51308-linux-x64/bin/linux-x86_64/codex",
  "extra_excluded_nodes": [
    "k8s-3090-01.usd.edu"
  ]
}
```
