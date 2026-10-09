# REGRESSION_TICKET — 2026-09-27-delta-screen, canary NaN at epoch 0 (2026-09-28)

Investigator, 2026-09-28. Diagnosis and scope only; nothing was fixed. Nothing here is quotable:
every number below is either an integer cost from `ablation.compute_ebops` used as a
fingerprint, or a CPU sanity value. None of them is a result.

## 1. Origin

**Finding.** The GPU memory canary (`kai-delta0926-canary-0-6cnrd`, node
`hcc-nrp-shor-c6017.unl.edu`, NVIDIA A10, bundle e6fc6cd9) ran `delta0926-w2-rep-a-t350000-s{1..5}`.
Every arm stopped in epoch 0 with `ARM_DIVERGED ... "nonfinite training metrics"`, loss nan,
`train_categorical_accuracy` 0.2013-0.2016, exit 3. The logs are
`logs/canary-0-6cnrd-20260928T0947Z.log` and the orchestrator scratch `canary2.log`. The
accuracy is the class-0 frequency, which is what argmax returns on NaN logits. So the logits
were NaN for almost every batch of the epoch.

**Answer: the NaN does not come from code or config.** It comes from GPU-side numerics in the
canary pod on node c6017, which is candidate (d). Candidates (a), (b) and (c) are excluded by
the evidence below. The bad state is already present before the first optimizer step. The
pre-training `initial_ebops` trace (`ablation.py` `run_training`: `initial = traced_ebops(model)`,
full train split, batch 2,048) gives wrong values on c6017, and they change between runs of the
same seed:

| arm (seed) | canary GPU c6017 (e6fc6cd9) | anchor GPU c5825 (77f1ca4e pilot) | CPU, this investigation (all trees) |
|---|---|---|---|
| rep-A / A s1 | 1,368,402 (E-k4), 8,287,058 (E-k5) | 11,559,681 | 11,559,681 |
| rep-A / A s2 | 7,938,898 | 11,295,521 | 11,295,521 |
| rep-A s3 / s4 | 7,906,130 / 8,180,562 | not run | not run |

On a healthy stack this trace is deterministic to the integer: the GPU value on c5825 equals
the CPU value for both seeds. On c6017 it is off by 30-88 % and gives two different values for
s1 on the same pod. A model that is already wrong at init and then trains to NaN in its first
epoch fits a device or stack that returns corrupt values.

**Phase that introduced it: RUN**, meaning the execution environment of the canary pod. No
code phase introduced it. There is also a **PREFLIGHT gap**: no gate checks, before arms start,
that a GPU pod reproduces a known integer fingerprint. PREFLIGHT gates 7 and 8 test memory and
diagnostics invariance, but a NaN run passes neither and fails neither. The CPU gates
(`gate_cpu_bundle_e6fc6cd9.json`, invariance 19/19) could not catch it by construction.

**Not yet separated inside (d):** whether this node is bad (GPU, driver, ECC) or the
`pip install` of 2026-09-28 resolved a different CUDA stack. `requirements-training.txt` pins
`tensorflow[and-cuda]==2.21.0`, but TF 2.21.0 declares its nvidia-* libraries as ranges
(PyPI: `nvidia-cudnn-cu12>=9.3.0.75,<10.0`, `nvidia-cublas-cu12>=12.5.3.2,<13.0`, ...). No pod
logged `pip freeze` or the driver version. PyPI upload times show no nvidia-* cu12 release
between the anchor pilot install (2026-09-27 ~20:51Z) and the canary install
(2026-09-28 ~09:36Z). The newest are cudnn 9.26.0.51 on 09-10, a 9.27 dev build on 09-18 (pip
skips pre-releases) and nccl 2.32.3 on 09-22. A stack change is therefore unlikely but not
disproved. The node is the leading suspect: c6017 is the only variable that is confirmed
different (the anchor ran on c5825).

### Evidence (commands and outputs)

The trees were rebuilt in scratch (`.../scratchpad/regr/`):
- `pristine` = `2026-09-26-training-batch/manifests/chang0926-code.tar.gz`, sha256 42abed4b… (checked)
- `patched` = `code/apply_anchor.sh` on it, 0001-0038 (`APPLY_ANCHOR_ALL_PASS`)
- `deployed` = `bundle/delta-code.tar.gz` (e6fc6cd9). `diff -rq patched deployed` differs only in `campaigns/delta0926/`
- `a77` = the `hgq2.tar.gz` payload of `manifests/configmap-77f1ca4e.json`, sha256 77f1ca4e… (checked)

Real data: `prepare_cache.py` from the pristine tree with the anchor's `cache_configs/n64.json`,
run on the local 62 raw train files. Result: x_train sha256 `420ac79d…`, the same value recorded
for the PVC cache `/data/chang-n64-20260926`. `load_cache` re-verifies every array hash. Driver:
`scratchpad/regr/repro.py`, which builds with `builder_for`, runs the initial trace over the full
train split at batch 2,048, runs finite checks, then does N per-batch steps at batch 2,790 in
epoch-0 order with the PID and LR set as in `run_training`, checking loss, grads and weights for
finiteness after each step. Env: `tests_patches/pyenv.sh` (tensorflow 2.21.0, keras 3.15.0,
hgq2 0.1.9, CPU).

| run | tree + config | initial_ebops | first steps at batch 2,790 |
|---|---|---|---|
| (1) | pristine 42abed4b + anchor `chang0926-a-n64-s1` | 11,559,681 | 10/10 finite; loss 2.7733 → 2.7659 |
| (2) | deployed e6fc6cd9 + anchor `chang0926-a-n64-s1` | 11,559,681 | 10/10 finite, identical losses to 6 s.f. |
| (3) | deployed e6fc6cd9 + Delta `REP-A-t350000-s1` | 11,559,681 | 10/10 finite, identical losses |
| (3') | same, **full epoch** via `ablation.run_training(stop_after=1)` | 11,559,681 | `[epoch 1/1000] EBOPs=11706972 … val_AUC=0.847928 val_accuracy=0.580468 … loss=2.704122`, `FULL_EPOCH_OK` |
| (3'') | deployed + Delta `REP-A-t350000-s2` | 11,295,521 | 3/3 finite |
| (4) | 77f1ca4e + its own `chang0926-a-n64-s1` | 11,559,681 | 3/3 finite, identical losses |

For comparison, the anchor's GPU epoch 1 on 77f1ca4e/c5825 read `EBOPs=11737590 val_AUC=0.821802`
(`2026-09-26-training-batch/logs/pilot-77f1ca-20260928T0512Z.log` l. 713). The CPU epoch above is
finite and in the same range. The two are not expected to be bit-equal, because training is not
deterministic across devices.

Static checks that agree with the table:
- **(a) excluded.** `bundle-manifest-77f1ca4e.json` vs `-42abed4b.json`: the code files that
  changed are `bnhgq2/ablation.py`, `run_pack.py`, `run_study.py` and `bnhgq2/wandb_util.py`
  (plus configs and tests). `run_pack.py` is the arm launcher, and the CPU repro does not
  exercise it, so it was read. Anchor 0030 adds only stall-monitor constants
  (`BNJ_POD_STALL_*`, `BNJ_CGROUP_DIR`, `BNJ_PROC_DIR`). Delta 0038 passes
  `env={**os.environ, **CHILD_ENV}` to `Popen`, where `CHILD_ENV` holds only `BNJ_DATA_ROOT` and
  `BNJ_RUN_ROOT` (`PACK_ROOTS` line in the log). No `CUDA_*`, `TF_*`, `XLA_*` or `NVIDIA_*`
  variable is set and no rlimit is set. The `ablation.py` diff adds `ebops_trace_every`/`is_traced_epoch`,
  `ValidationReloader`, the RSS gate and the regime-B branches. All of these run after
  `step(...)` returns. The init path, `make_epoch_step` and the initial trace are byte-identical.
  The loss is NaN at the output of `step`, which is upstream of every 42abed4b change.
- **(b) excluded.** With every Delta key absent, `_delta_binarize` → `bitnet_binary_ste(w)`,
  `init_delta_scales` is a no-op, `delta_optimizer_for` → `optimizer_for`, and `latent_ema` is
  None, so 0012 does not run when off. The two always-on keys, `collapse_stop` and
  `accumulator_metric`, act only after the finite check. 0038 changes only `run_pack.py` roots.
  Runs (2) and (3) are bit-equal to (1).
- **(c) excluded.** A key-by-key diff of `REP-A-t350000-s1.json` against the 42abed4b
  `chang0926-a-n64-s1.json` finds these differences: `campaign.*` (dropped; read only by the ROC
  evaluator, and TF32 is disabled unconditionally in `run_study.train`), `delta_study.*`
  (provenance), `experiment.{arm,group}`, `name`, `engram_study.question`,
  `train.wandb_project`, `train.epochs` 7000 → 1000 (enters only the RSS-gate projection and the
  last-epoch trace), `experiment.collapse_stop` and `experiment.accumulator_metric`. None of these
  enters the forward pass, the loss or the step. Run (3') confirms it.
- **Data excluded.** Same `BNJ_DATA_ROOT` (`/data/chang-n64-20260926`) in both pods, and every
  array hash is verified at load.
- **Manifests.** `pilot-job.json` and `delta-canary-job.json` use the same image (`python:3.12`),
  the same pip line, `NVIDIA_TF32_OVERRIDE=0` and `TF_FORCE_GPU_ALLOW_GROWTH=true`. They differ in
  the RSS-gate env, `BNJ_*_RETRIES=0` and the arm count per pod (anchor 6, canary 4-5), and none
  of these touches numerics.

## 2. Impact trace

| artifact / number | status | why |
|---|---|---|
| canary E-k4 and E-k5 records (`/data/delta-20260927/canary/E-k{4,5}/…`, DIVERGED.json ×9, `k_result.json`) | **must re-run** | produced on the bad pod. The divergences are environment artifacts and do not say anything about rep-A. A recorded divergence is never resumed, so those run dirs cannot be reused. |
| canary A07-k3 (rep-C s1-3), still running or unread in `6cnrd` | **must re-run** | same pod, same node. Treat any value from it as suspect, even if it is finite. |
| STUDY gates 7 (GPU memory, K) and 14 (host RSS slope) | **remain PENDING** | no valid epoch ran. The POD_MEM/RSS samples from 09:44-09:50Z cover a NaN-training process and are not a measurement. |
| gate-7 determinism probe (two pods, 21 epochs) | not yet run; **scope change** | it must include the fingerprint check in §3 so that a bad pod is detected at epoch 0 and is not counted as nondeterminism |
| `RUN.md` "Relaunch outcome" (09:36-09:50Z) | **amend (v2)** | it reads the relaunch as a W&B success. It needs to record the divergence and point to this ticket. |
| `bundle/` e6fc6cd9, ConfigMap `kai-delta0926-code-e6fc6cd921`, W2 configs (582), gate_cpu / invariance / slug evidence | **unaffected** | CPU runs (2), (3) and (3') are bit-equal to pristine 42abed4b on real data. No rebuild is needed. |
| anchor 42abed4b (training-batch regime-B pilot, gate 1) | **unaffected by this finding**, with one warning | the anchor code is cleared. Anchor pods on c6017, or on a drifted stack, would fail the same way. The anchor's cluster-ops should add the same fingerprint gate. |
| any other kai pod that ran on `hcc-nrp-shor-c6017.unl.edu` | **check** | outputs are suspect until the node is cleared. Search `cluster-inventory.md` and the training-batch RUN.md for that node. |
| W&B `BNJetTag-Delta` runs from 6cnrd (e.g. `6751da9bc1cb`) | **label** | tag or annotate them as `invalid-node` and do not delete them |
| outward text | **none** | nothing was published from the canary |

## 3. Scope (for the fixer)

1. **Discriminator job** (cluster-ops, with the Delta ml-engineer as author; one GPU; about 10 min
   of pod time per node). Use the same image, pip line and ConfigMap e6fc6cd9. Add
   the container `imageID` (`kubectl get pod … -o jsonpath='{.status.containerStatuses[*].imageID}'`;
   `python:3.12` is a floating tag, and nodes cache images independently), `pip freeze`, `nvidia-smi -q | grep -E "Driver Version|CUDA Version|Volatile|Retired|Remapped"`
   and `python -c "import tensorflow as tf; print(tf.sysconfig.get_build_info())"`. Then run
   **init plus the initial trace only** (no training; the `repro.py` pattern, with `nbatches` 3)
   for anchor `chang0926-a-n64-s1` and `-s2` on the deployed tree, twice each. Expected:
   **11,559,681** and **11,295,521**, identical on both repeats. Pin one pod to c6017
   (`nodeSelector kubernetes.io/hostname`) and one pod to another A10 node, for example c5825.
   Readings:
   - only c6017 fails → node fault. Exclude it with a `nodeAffinity` `NotIn` on every Delta and
     anchor manifest, log an incident in `cluster-inventory.md` with a **Check** line, and report
     the node to NRP.
   - only c6017 fails but the imageIDs differ → the image, not the node. Pin the image by
     digest in both campaigns' manifests.
   - both fail → stack drift. Pin the nvidia-* wheels to the versions from the c5825 run in
     `requirements-training.txt`. That is a new bundle sha, so rebuild the bundle, re-run the
     CPU gates and apply a new ConfigMap (§6).
   - neither fails → intermittent. Keep the gate in item 2 as the defence and re-run the canary.
2. **PREFLIGHT fingerprint gate (new, "gate 15")**, run in every GPU pod before `run_pack.py`
   starts arms. Build anchor arm-A s1, trace it, and assert `initial_ebops == 11559681`. On
   mismatch, exit non-zero with `GPU_FINGERPRINT_MISMATCH <value>`. Cost: about 2 min of pod time
   per pod. Also have `run_pack.py` treat an `ARM_DIVERGED` at `divergence_epoch_zero_based` 0
   in every arm of a pack as a pod-level failure (`PHASE_EXIT_NONZERO`), not as K separate
   outcomes. Owner: Delta ml-engineer (the canary wrapper and 0038 are Delta's). This touches
   the manifest and wrapper only, not `bnhgq2/`, so config_sha256 and bundle e6fc6cd9 do not
   change unless item 1 forces a pin.
3. **Re-run the canary**: the same manifest plus the gate, excluded from c6017 or pinned to a
   cleared node, with `BNJ_ARM_RETRIES=0` as before. Use new run roots
   (`/data/delta-20260927/canary-v2/…`) and do not delete the old ones. Read `k_result.json` and
   the RSS gate lines.
4. Gates to re-run after the fix: the fingerprint check (item 2) in every pod; STUDY gate 7
   (memory + determinism probe) and gate 14 (RSS slope over epochs 5-105). The build, the
   reload ≤ 1e-7, `verify_check` and the CPU gates are **not** re-run unless item 1 changes the
   bundle.

**Fix owner.** Not the anchor ml-engineer, because the anchor code is cleared. The **Delta
ml-engineer** owns the canary manifest, the wrapper and the fingerprint gate. **Cluster-ops**
owns the node diagnosis and exclusion. If item 1 shows stack drift, the pin in
`requirements-training.txt` goes to the anchor ml-engineer, who owns that file, and it applies
to both campaigns.

**Estimate.** Agent time: about 1.5 h (discriminator manifest and readout 0.5 h; gate and
wrapper change plus a CPU test 0.5 h; canary relaunch record 0.5 h), or about 3 h if a
wheel-pin rebuild is needed. GPU time: discriminator 2 pods × about 0.2 h = about 0.4 GPU-h;
canary re-run 8.35-10.43 GPU-h (the manifest's projection, unchanged); fingerprint gate
overhead about 0.03 GPU-h per pod thereafter.

## 4. Cascade

1. Discriminator (item 1). 2. Fingerprint gate and wrapper (item 2); lint with `nrp_doctor.py`.
3. Canary re-run (item 3), then STUDY gates 7 and 14. 4. Launch gate 1 (the anchor regime-B pilot
readout) stays as it is; this ticket does not change it. 5. Then the wave-2 launch decision.
**Skipped**, because their inputs did not change: STUDY (except a dated amendment adding gate
15), the patch series, the bundle build, the W2 config generation and the CPU gates (unless
item 1 shows stack drift, in which case the bundle rebuild and the CPU gates re-run first).
VERIFY and REPORT do not exist yet.

## 5. Triggers met (`docs/methodology/06-review.md` §6.7)

- **"a failed validation test (build, reload, recompute, a control arm) accepted without
  documented remediation attempts"**: the canary is the control run for gates 7 and 14. Its
  total failure must not be read as a K or memory result, and the earlier attempt was already
  reported as "Complete" while every phase had failed.
- **"arms that should match producing different `y` arrays"**, applied by analogy to the
  fingerprint: the same config, seed and code gave two different `initial_ebops` values on one
  pod (s1: 1,368,402 vs 8,287,058) and disagree with the reference (11,559,681). This is not
  word for word the listed trigger, and it is recorded as the closest match.
- **"Suspiciously … every check passing with no tension"**: every CPU gate passed on e6fc6cd9,
  and none of them could catch a GPU-only defect.
- Not met: TF32 (disabled unconditionally, `run_study.py` l. 98-99), reload tolerance, the eBOP
  remeasurement (no checkpoint exists).

## 6. Version plan

- `RUN_v2.md` (new file; `RUN.md` is not overwritten). Change log: "Canary 6cnrd on
  hcc-nrp-shor-c6017: all rep-A arms diverged at epoch 0 (NaN). initial_ebops was
  non-reproducible and off the CPU/anchor-GPU reference (11,559,681 s1; 11,295,521 s2).
  Origin: GPU environment on that node or stack, not code or config
  (REGRESSION_TICKET.md). Gates 7 and 14 remain pending. Canary re-run under gate 15."
- `PREFLIGHT_v2.md`. Change log: "Added gate 15: GPU integer fingerprint (anchor A s1
  initial_ebops == 11,559,681) in every pod before arms start; pack-level epoch-0 divergence is a
  pod failure; node exclusion list; pip freeze and driver logged in every pod."
- `STUDY.md`: a dated amendment line only (gate 15 added), no re-freeze of the design.
- If item 1 finds stack drift: a new bundle sha and `bundle-manifest` beside the old one,
  `configmap-<sha>.json`, re-run CPU gate evidence under `bundle/evidence/` with the new sha in
  each file name. e6fc6cd9 is kept.
- Nothing is deleted: the old canary run roots, DIVERGED.json files and W&B runs stay and are
  labelled.

Scratch evidence (not quotable, not committed): `/private/tmp/claude-501/-Users-kaiyamaguchi-Desktop-bnjettag/f3113eb2-31b2-4d10-9d44-a725a8196f9e/scratchpad/regr/`
(`repro.py`, `full_delta_s1.log`, `cache/n64/data/data_info.json`).

## 7. Fix (fixer, 2026-09-28; prepared, not applied, not committed)

Kai's decision (2026-09-28): discriminate the node, gate every pod, re-run away from c6017. Detail and
evidence: `PREFLIGHT.md` section "Gate 15".

- **§3 item 2, gate 15.** `campaigns/2026-09-26-delta/code/fingerprint_check.py` runs in every Delta pod
  (`manifest_wave2.py` `header()`) before any arm. It checks rep-A s1 `initial_ebops == 11559681` and
  exits 9 on a mismatch. It logs driver, GPU, TF build and `pip freeze`. CPU: 11,559,681 / 11,295,521 on
  pristine 42abed4b, deployed e6fc6cd9 and new 705a554b.
- **Bundle.** Re-frozen as **705a554b** (ConfigMap `kai-delta0926-code-705a554b8d`, manifest 300be87b
  unchanged). The code tree is identical to e6fc6cd9. It adds the script, the 1fd9558 configs and packs,
  and the canary-v2 run roots. e6fc6cd9 is kept.
- **§3 item 1, discriminator.** `manifests/discrim-c6017-job.json` is pinned to c6017;
  `manifests/discrim-other-job.json` is `NotIn` c6017 and prefers c5825. Each runs s1 and s2 twice in
  separate processes and does no training.
- **§3 item 3, canary re-run.** `manifests/delta-canary-v2-job.json` runs gate 15 first, excludes c6017
  and uses run root `canary-v2`. `delta-canary-job.json` (the c6017 run) is unchanged.
- **Deviations.** PREFLIGHT.md is amended in place rather than a `PREFLIGHT_v2.md` (§6), as the task
  asked. The discriminators use 705a554b, not e6fc6cd9 (§3 item 1). The code is byte-identical, so the
  node-versus-stack reading holds.
- **Not resolved:**
  - `run_pack.py` pod-level epoch-0 divergence (§3 item 2, second half) goes to the Delta ml-engineer.
  - The W&B id collision of canary-v2 with the c6017 runs goes to cluster-ops / Kai (PREFLIGHT "Gate 15", Open).
  - `RUN_v2.md` and the STUDY amendment line are cluster-ops and orchestrator items (§6).

## 8. Discriminator result (cluster-ops, 2026-09-28)

Both discriminator Jobs completed. c6017: node `hcc-nrp-shor-c6017.unl.edu`, GPU A10
`GPU-cad1b289-db88-68e2-f44d-178aa90abf3e`, driver 595.71.05. Other: node
`hcc-nrp-shor-c5809.unl.edu` (the preferred c5825 was unavailable; `NotIn c6017` still holds),
GPU A10 `GPU-e16bd8e9-e8ff-14da-eca9-df94d723829a`, driver 595.91.07. Both: ECC (SRAM/DRAM
correctable + uncorrectable, remapped rows) all 0; TF build info identical
(`cuda_version 12.5.1, cudnn_version 9`); `pip freeze` byte-identical between the two nodes.
Both gave `FINGERPRINT 11559681 expected 11559681` (s1) and `FINGERPRINT 11295521 expected
11295521` (s2), each twice, `FINGERPRINT_OK` every time. Full logs:
`logs/discrim-c6017-g6znq-20260928.log`, `logs/discrim-other-z78sn-20260928.log`.

**Reading: c6017 is healthy single-process.** This does not overturn §1's node-as-leading-suspect
reading; it narrows it. **Gate 15, as specified (init + initial trace, no training, one process),
cannot reproduce or catch the canary's fault**, because the canary's actual failure mode needs
4-5 concurrent training processes sharing one GPU (contention for GPU memory/compute scheduling,
a driver race, or similar) — a condition the single-process discriminator and the single-process
gate 15 do not create. Gate 15 therefore stays valuable as a fast per-pod sanity check
(catches a grossly wrong/uninitialized GPU before any arm starts) but is **not sufficient** to
clear a node for the canary's multi-arm shape. The node exclusion in `delta-canary-v2-job.json`
(`NotIn hcc-nrp-shor-c6017.unl.edu`) is kept per Kai's decision as a precaution, not because this
result proves the node itself defective.

**Fast failure signal going forward (since gate 15 alone cannot catch a concurrency-only
fault):** the per-arm epoch-0 divergence detection (`ARM_DIVERGED`, "nonfinite training
metrics"/"nonfinite validation logits") plus the wrapper's loud phase failure (`FAIL=1`, exit 7,
`PHASE_EXIT_NONZERO <phase>`, `CANARY_PHASES_FAILED`) is what actually surfaces this class of
fault, at the cost of the training attempt itself. Any relaunch must be watched for these markers
in the first few minutes rather than assumed safe once gate 15 passes.

Both discriminator Jobs deleted after evidence capture (cluster-ops, 2026-09-28).
