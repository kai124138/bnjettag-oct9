verdict_r1: PASS (24 pilots; conditional on GATE_RESULT PASS of kai-pilot1005-cpugate-98dd28 and launch conditions L1-L4) · verdict_readout: PASS (rh-deccad51; condition L5)

# PREFLIGHT critical review v2: pilot program R1, bundle 98dd2875, 2026-10-06

Reviewer: critical-reviewer, solo (06-review §6.2, PREFLIGHT tier), iteration 2 (solo tiers warn
at 2). Scope: the frozen bundle `98dd2875b7c902bb881562a7acbf00f7cf266a369a74528b6fb8471e0cdc0059`
and its 26 handoffs (`PREPARED.json`): the CPU gate (already submitted 05:58 JST as
`rh-c11b0c23…`, not touched), the 24 R1 GPU Jobs and the R1 readout `rh-deccad51…`. Everything
was checked read-only. Nothing was submitted. The only campaign file written is this one. The
rebuild went to `<scratchpad>/crv2/tree`. Local numbers come from the home PC and are not
quotable.

## Checks reproduced in this review

| check | result |
| --- | --- |
| sha256 of 12 patches vs `patches/PATCHES.json` | 12/12 equal (0042 `0a0fa489…`, 0043 `fc20656f…` appended) |
| `build_tree.py --out <scratch>/crv2/tree` | `TREE_MATCHES` |
| `manifests-98dd28/pilot1005-code.tar.gz` | sha256 `98dd2875…0059`, 294,480 B, 393 files. Byte-equal to `code/tree` in both directions, and all 393 match `bundle-manifest.json` |
| ConfigMap | `configmap.json` name `kai-pilot1005-code-98dd2875b7`, payload sha `98dd2875…` |
| 26 handoffs | `source-configmap.json` payload sha = `98dd2875…` and name match in 26/26. `job_json_sha256`, `record_sha256`, rh-ID prefix and job name match PREPARED.json in 26/26. Each container script is identical to `manifests-98dd28/<key>-job.json` |
| training code vs b3fb22 | `run_study.manifest()` on the rebuilt tree = `e6ff034b…a8e3` (the value every pod asserts). Tar diff b3fb22c8 → 98dd2875: 51 files, 49 under `campaigns/pilot1005/` (configs, packs, index, config_map, r1_packs, generate.py, gate_check.py `N_CONFIGS` 23→24) plus `tests/test_pilot1005.py` and `tests/test_readout_pilot.py`. No training-path file changed |
| 24 configs vs STUDY §4 and PROGRAM.json `r1_launch` | index rows equal the 24 `r1_launch` rows on (arm, hyp, arch, budget, (c), warmup, seed), and 5 `config_extra` entries match. Flattened diff against A350-C at the same seed: noC drops `pid_input`/`pid_traced_integral`/`campaign.amendment` only; the E ladder and E-unc-C change `target_ebops` only (E-unc 100,000,000, above init 9,429,139); w50/w100 change `pid.warmup` only; NB changes `quant.weight` only; qkv1 adds `attn_bit_floor {1,[q,k,v]}` + floor 269,830; qkv1-450k adds both plus target 450,000. The A07 rungs differ from each other only in target, and from `chang1002c-a07-350-n64-s1` only in target, production false and identity. Plus identity/`campaign.pilot.*` keys. Local cpu_gate: w100 first feedback 110, span 10 (`evidence/final-tree-98dd28/cpu_gate.log:72,76`) |
| 24 GPU Jobs (script over every handoff `job.json`) | Indexed, completions = parallelism = 1, pack `[[i]]` with its own name (24 packs). Product `NVIDIA-GeForce-RTX-3090` only. NotIn includes c6017 and both `KNOWN_BAD_NODES`. Pod `activeDeadlineSeconds` 20,800 (none at Job level). `backoffLimitPerIndex` 1. podFailurePolicy: DisruptionTarget Ignore, exit 10 FailJob, FailIndex on [5, 76, 124, 137, 143]. Pre-arm exit 75 only when `el -lt 600`. Fingerprint `--expect 11559681` with `FINGERPRINT_GATE_FAIL`. RSS gate 8192 / 5:105. `run_pack.py "$PACKS" 500`. `BNJ_STAGE=pilot-r1`. Bundle and manifest sha asserted. `automountServiceAccountToken: false`. Train and init containers on `python@sha256:4d1caded…`. 1 GPU. Grace 180 s. 24 distinct `r1/runs/<name>`, each script referencing only its own |
| exit trap (read by hand) | Every container exit is one of 0, 10, 75, 76, 124 or 5, or a kubelet 137/143. Training-phase exits never map to 75. A timeout `--kill-after` 137 past the budget maps to 124. A 75 on the retry exhausts the index. Harness `TRAP_HARNESS ALL_PASS 10` (`evidence/fixes-v1/pod_exit_trap_harness.log`) |
| `run_handoff.py validate` (7 sampled: E500k, E-unc, NB s1, qkv1-450k, A07-5M, readout, the submitted gate rh-c11b0c23) | 7/7 `VALID` |
| `nrp_doctor.py lint` (5 sampled, live node map) | exit 0. GPU Jobs: 1 WARN `backoffLimitPerIndex=1` (deliberate) and the note "no activeDeadlineSeconds" (the lint reads Job level only; the pod level is set, C3). Readout `OK`. The RTX 3090 pool is **48** nodes now (47 at v1) |
| submitted gate record rh-c11b0c23 vs prepared rh-92e3bc71 | record.json differs only in `brief.approval_ref` and `brief.scientific_gate.{reference,status}`; job.json only in handoff identity (annotations, run-id label, handoff ConfigMap). Gate OUT `cpu-gate-98dd28-r1`, `N_CONFIGS = 24` |
| spend arithmetic | 24 × (600 + 20,800 + 180) s = 517,920 s = **143.87 GPU-h** ≤ 144 (PROGRAM.json:51-52; Kai, `local/2026-10-05-execution/r1-98dd28-approval.json`). Terms omitted: see B-new-2 |
| readout Job (rh-deccad51) | PYTHONPATH `/work/code:/work/code/campaigns/chang0926` set after the manifest check, then `READOUT_IMPORT_OK` asserted. `activeDeadlineSeconds` 43,200, `backoffLimit` 0, CPU 8 / 24 Gi, `CUDA_VISIBLE_DEVICES=-1`, token off. `test ! -e` on the new OUT `readout-epoch-0500-98dd28-r1`. Final status (line 197) tests only RO, A26, CERT, MONC. The diag block uses only `&& {…\|\| DIAG=1;} \|\| echo` lists, a heredoc `\|\| DIAG=1` and `sha256sum … \|\| true`, so under `set -e` it cannot abort the script or change the exit. The 45 diag `--indices` match `index.json`, and there are 21 unconstrained probes (20 E + A07-5M) |
| no test data | `run_engram.load_cache` opens only `x_train, y_train, x_val, y_val` (run_engram.py:178-198). a26 reads validation. certify traces train. readout_pilot, monitor_p and diag read run files only. Importing `evaluate_roc` runs only definitions (no data load, chang0926/evaluate_roc.py:30-74). sys.path collisions: none between `campaigns/pilot1005/` and the tree root. The 4 shared names with chang0926 resolve to pilot1005 first |

Jev `jev_check_claims` (audit `jv-6b20605fa012428396b01a73e4f167ae`, advisory):

| claim | Jev | by hand |
| --- | --- | --- |
| PROGRAM.json:49-53, worst case 143.87 ≤ 144 | supported 0.90 | arithmetic right; bound incomplete (B-new-2) |
| gpu-benchmark VERIFY.md:109, 30.85 s and 38.8 s | supported 0.82 | supported |
| PREFLIGHT.md:288, F2 deadline 20,800 s | **overstated 0.77** | **not supported**: the line says 21,600 (B-new-1) |
| approval file: deadline 20,800, cap 144 | supported 0.82 | supported |

`lab_check_protocol` on `protocol-r1.json`: structurally valid, sha `57e6aa0e…`,
`matches_snapshot false`, and no frozen snapshot exists. The file still names w150 (4 lines), so
it predates K1 (B-new-3).

## v1 findings, by name

| v1 | status | evidence |
| --- | --- | --- |
| A1 readout import | **resolved** | readout script line 22 PYTHONPATH and line 23 assertion. The dry run on this handoff ID (`readout_dryrun/dryrun_final_98dd28_rh-deccad51.log:5,92-94`) shows `READOUT_IMPORT_OK`, `CERTIFIED` ×2 and `CERTIFICATION_ALL_PASS 2 0`. The old env gives `ModuleNotFoundError` (negative control log) |
| A2 spend bound | **resolved** (bound text incomplete, B-new-2) | pod deadline 20,800, FailIndex rules, `backoffLimitPerIndex` 1, the 75-only retry (table above) |
| A3 STUDY gate | **open, not this review's to clear** | STUDY.md:5 reads "draft … STUDY panel v1 ITERATE; not frozen". `review/STUDY_arbiter_v2.md` does not exist. `lab_freeze_protocol` has not run. PROGRAM.json `signed_by_kai false`, `mode dry-run`. Kai's approval file and the PROGRAM `gate` step both require STUDY arbiter v2 PASS before R1 → L2 |
| B1 bundle_sha field | **resolved** | PROGRAM.json integrity uses `bundle_sha256` (`definitions.integrity[2]`, `r1_readout.condition`) |
| B2 §2a empty | **resolved** | PREFLIGHT §2a filled; `evidence/final-tree-b3fb22/` and `final-tree-98dd28/summary.log`: PREFLIGHT_ALL_PASS 24, NB_PAIRING_ALL_OK 8, 166 collected, 164 passed, 2 skipped |
| B3 dev/README overstatement | **resolved** | `fixes-v1/a_unchanged_final_tree_9configs.log`: 9/9 SAME incl. A-s2, C-s1, exit 0 |
| B4 E entropy cut | **resolved in design** | STUDY [A2] entropy-only stop for Kai; E-unc-C positive control in R1; PROGRAM `entropy_only_failure`, `positive_controls` |
| B5 w150 time-limited | **resolved by Kai** (K1 w100); text stale → B-new-3 | configs w100, first feedback 110 |
| B6 H2 beyond ladder | **resolved** | STUDY [A2] amendment (JOURNAL 14:16) |
| C1 production flag | resolved: every config `campaign.production` false; `index.json production_count 0` |
| C2 arm ids | resolved: index `program_arm` = PROGRAM `r1_launch` arms (24/24) |
| C3 pool count | superseded: 48 nodes today (lint) |
| C4 STUDY history | resolved: `study-history/` (3 files) |
| C5 NB init EBOPs | noted in STUDY [A2] |
| C6 zero-bit-only floor re-trace | carried, unchanged (C) |
| L1-L3 (b3fb22 gate) | satisfied: L1-style diff clean for rh-c11b0c23 (table); L3 honoured by a new gate under a new name and OUT |

## New findings

### A: none.

### B (text only: no launched byte changes, so no re-review; the orchestrator checks each by grep before launch)

- **B-new-1. PREFLIGHT.md does not describe the frozen launch set.**
  - §3 still lists b3fb22, 23 Jobs, a 28,800 s readout and the old rh-IDs.
  - §3b says the 98dd28 freeze is "blocked", gives the deadline as "21,600 s" (PREFLIGHT.md:288, 299-313), writes the freeze command with `--pod-deadline-s 21600` (:347) and ends at a 149.2 GPU-h worst case over the cap.
  - The frozen manifests use 20,800 s (PREPARED.json `options`; every job.json), as Kai set (approval file).

  Fix: add a §3c "Frozen 98dd2875 (2026-10-06)" that gives:
  - the 24-row table with job names and rh-IDs from PREPARED.json;
  - the cleared gate rh-c11b0c23;
  - the readout rh-deccad51 at 43,200 s;
  - D = 20,800;
  - the arithmetic below;
  - a pointer to this review.

  Mark §3b's 21,600/149.2 text superseded.
- **B-new-2. The 143.87 GPU-h bound omits three terms.** It counts 600 s for a retried first
  attempt, but that window is measured from script start (`T0`). The pod holds the GPU from
  `startTime`, which comes before the image pull and the `record-run-handoff` init container.
  The terms are:
  1. **P1**, the first attempt's pull + init time, for each arm that retries;
  2. an init-container hang that reaches the deadline: no `train` exit code, so no rule matches and it counts as a retry;
  3. DisruptionTarget replacements (Ignore; acknowledged in §3b).

  With only (1), the slack to 144 is 0.133 GPU-h = 480 s, which is 20 s per arm if every arm
  retried. That is pathological, not expected. The expected spend is about 24 × (15,425 to
  19,400 s + pre-arm) ≈ 105 to 132 GPU-h at the VERIFY.md:109 rates. Fix: state the bound as
  143.87 GPU-h + Σ P1 over retried arms + disruption replacements, all counted against the cap
  when they occur (PROGRAM `retries_count_against_cap: true`). It can also go into STUDY §11,
  which still says "6 h deadline per pod". No manifest change.
- **B-new-3 (STUDY; for the STUDY arbiter v2, which gates R1 anyway).** STUDY still registers w150:
  - §4 row 6 and the line "Recorded: ____ … until filled, R1 is as registered (w150)" (STUDY.md:125, 136-137, 347-348);
  - the H4 judging and W-order text (:200, :203, :229-231);
  - `protocol-r1.json`.

  The frozen configs, PROGRAM.json and decisions.md 2026-10-05 15:21 (K1) say w100. Fill
  "Recorded" with the K1 reference, rename w150 → w100 in §4/§6/§7, and restate the
  time-limited reading for w100 (first feedback 110, 390 epochs to 500). Then re-run
  `lab_check_protocol`, and run `lab_freeze_protocol` once STUDY passes.

### C

- **C1.** A07 time fit at D = 20,800. The run_pack budget is about 20,800 − 300 (pre-arm) − 420 = 20,080 s:
  - against 500 × 38.8 = 19,400 s (upper bound, one node, n = 1 × 20 epochs; VERIFY.md:109), the margin is 680 s (3.4 %);
  - against 500 × 30.85 = 15,425 s, it is 4,655 s.

  A deadline kill is FailIndex → `failed` → the R1 integrity check stops the program for Kai.
  That is safe but costly. At the 30-min utilization check, also project `epoch_seconds` × 500
  for the 4 A07 pods.
- **C2.** Readout deadline 43,200 s. On the home PC: certification 336.5 s per trace, at most 48 traces (≈ 4.5 h), and a26 about 45 s per checkpoint (about 69 runs incl. diag). That totals about 5.3 h, and an EPYC pod at 2 threads may be 1.5 to 2× slower. Within the deadline, but not by much. If the deadline falls during diag, readout.json is already written, but the Job reads Failed.
- **C3.** `nrp_doctor lint` does not see pod-level `activeDeadlineSeconds`, so its note is misleading.
- **C4.** PROGRAM.json `r1_launch.condition` still compares the literal `pods_requested: 23`. `handoffs` holds prose, not the rh-IDs, so `none_placeholder` passes vacuously. `r1_readout` keeps PLACEHOLDER handoff/job/output. None of this matters for a manual launch. Fill them before any autopilot use.
- **C5.** Briefs still read "PROGRAM.json not yet signed", which the gate-cleared re-preparation replaces.
- **C6.** Carried from v1 C6: the gate re-traces only the 0-bit floor.

## Launch conditions

- **L1.** `kai-pilot1005-cpugate-98dd28` ends with `GATE_RESULT PASS` (threshold, cpu_gate 24, nb-pairing 8, pytest 166/2 skips).
- **L2.** `review/STUDY_arbiter_v2.md` reads PASS (v1 A3; Kai's approval file and the PROGRAM `gate` step require it), with B-new-3 fixed in STUDY.
- **L3.** B-new-1 and B-new-2 are fixed in PREFLIGHT.md before submission. Text only. Every handoff byte above is unchanged.
- **L4.** Each of the 24 GPU Jobs is submitted from a `--gate-cleared` re-preparation. Its `record.json`/`job.json` may differ from the PREPARED.json record only in `brief.approval_ref`, `brief.scientific_gate` and the derived handoff identity, as checked here for rh-c11b0c23. Bundle `98dd2875…`, manifest `e6ff034b…`, image digest, script (D = 20,800), resources and podFailurePolicy must be byte-equal.
- **L5 (readout).** It runs only after every R1 pod has reached epoch 500 or a terminal marker, from a gate-cleared re-preparation of rh-deccad51 under the L4 rule, with PROGRAM `r1_readout` filled.

## 06-review §6.3

1. Conventions. Validation-only selection; no ROC-test read anywhere in the readout (table). Yes.
2. Every config builds and reloads: local cpu_gate `CONFIG_PREFLIGHT_PASS` 24 with `reload_max_abs_diff 0.0`. The pod gate repeats it (L1).
3. Lint is clean or each warning has been read: the 1 WARN (backoff 1) is deliberate (cap). ConfigMap sha = code sha: yes.
4. Packing: one arm per GPU, as approved (decisions.md 2026-10-05 10:08 item 2). E at K = 1 is unmeasured, and the 30-min utilization check decides.
