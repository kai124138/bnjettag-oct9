# PREFLIGHT — pilot program, round 1 (build half), 2026-10-05

**Status: build half only. Everything is prepared offline. Nothing has been submitted.** No
`kubectl apply|create` was run, and no file under `campaigns/2026-10-02-*` was edited. Every handoff
brief carries `scientific_gate: pending`, so `run_handoff.py launch --submit` refuses all 25 records
as written. All local runs on the home PC are engineering checks only, and none of their numbers are
quotable. Review has not run yet: critical-reviewer at PREFLIGHT. The launch half (deadlines,
smoke, submission) belongs to cluster-ops.

Governing documents:
- `docs/PILOT_PROGRAM.md` and `.claude/memory/decisions.md` (Kai, 2026-10-05 10:08 JST).
- `STUDY.md` and `PROGRAM.json` (drafts, read at 10:47 JST: 23 R1 runs).
- The orchestrator's scope change of about 10:30 JST: fold in 0036/0037, add NB and H3 at 350k
  (seeds 1–2), and check the NB pairing at seeds 1–8.
- Base: `campaigns/2026-10-02-chang-option-c/` (bundle `6919462c…`, read only).

Plan: [plan-build.md](plan-build.md). `plan.md` holds the STUDY plan.

## 1. What changed vs bundle 6919462c

No git repository exists at the lab root, so each code change is one patch with a SHA-256. Each
patch is also one commit in a scratch git tree. `build_tree.py` applies them in the order of
[patches/PATCHES.json](patches/PATCHES.json) to the 42abed payload, and the result reports
`TREE_MATCHES` against `code/tree`.

| order | patch | SHA-256 | content | in the run_study manifest set? |
| --- | --- | --- | --- | --- |
| 1–2 | 0032, 0033 | `f475c69e…`, `23536dfe…` | option (c), byte copies (unchanged) | yes (as before) |
| 3 | 0034-test-run-pack-env | `92d5802a…` | `tests/test_run_pack.py` `setup()` adds `BNJ_CAMPAIGN_DIR=str(tmp)`; the fix from REGRESSION_TICKET.md | no |
| 4 | 0036-nb-arm | `9edd3a6c…` | NB arm (`quant.weight: kbi_learnable`); byte copy of `dev/patches`; owner: the other ml-engineer, see `dev/README.md` | yes |
| 5 | 0037-attention-bit-floor | `0b469b52…` | H3 `quant.attn_bit_floor`; byte copy of `dev/patches` | yes |
| 6 | 0035-pilot-configs | `223671de…` | `campaigns/pilot1005/`: generate.py, 23 configs, index, per-arm packs, config_map, cpu_gate.py (pilot), monitor_p.py, copies of certify/threshold/floors; `tests/test_pilot1005.py` | no |
| 7 | 0038-pilot-stage | `a2fa4650…` | `bnhgq2/wandb_util.py`: stages `pilot-r1/2/3`, group suffix `-pilot-rN`; test | yes |
| 8 | 0039-readout-pilot | `d6239518…` | `campaigns/pilot1005/readout_pilot.py`; `tests/test_readout_pilot.py` | no |
| 9 | 0040-gate-check | `9f49364a…` | `gate_check.py` (gate pass/fail), `pair_nb.py` ([A22] seeds 1–8); test | no |
| 10 | 0041-nb-validate-cfg | `f30cb789…` | `run_engram.validate_cfg` accepts `kbi_learnable`; runner-path test for NB and H3 | yes |

Full hashes: `patches/PATCHES.json`. The 19-arm build of this morning (bundle `1f7c4e0f…`) is
superseded and was never launched. Its patches are in `patches/superseded-19arm/` and its outputs in
`superseded-1f7c4e/`.

**0041 is a defect fix found in this build.** `run_study.train` calls `run_engram.validate_cfg`,
which rejected every weight type except `binary_absmean` (`run_engram.py:114`). The NB arm would
have failed before its first epoch on the GPU. The dev smoke runs called `ablation.run_training`
directly, so they never reached this check. The fix is one condition. The new test
`tests/test_pilot_variants_runner.py` trains NB and H3 for 3 epochs through the runner's own builder
(`run_engram.builder_for`) and observer (`engram.diagnostic_observer`). It also checks that the
real pilot configs validate and that `int8_absmax`, `none` and `kbi_learned` are still rejected.

**Configs** (`generate.py`, never hand-edited). Each arm starts from a config that is rebuilt and
checked byte for byte against the file on disk:
- with (c): `chang1002c-a-n64-s<s>` (E) or `chang1002c-a07-350-n64-s1` (A07);
- without (c): `chang0926-a-n64-s<s>` (PID keys absent, the historical in-training input).

The only scientific changes are `train.ebops.pid.target_ebops` (H2), `train.ebops.pid.warmup` (H4),
`quant.weight` (NB), and `quant.attn_bit_floor` with its own `zero_floor_ebops` (H3). Identity fields
are `name`, `experiment.arm`, `experiment.group` (`chang-n64-20261005`), `campaign.study`,
`campaign.revision_of` and `campaign.pilot`. The generator asserts that every other flattened key is
unchanged (exhaustive per-row diff in `config_map.json`). The H1 pair differs only in
`pid_input`/`pid_traced_integral` (and `campaign.amendment`/identity), which a test asserts.
`freeze_p.py` refuses to build unless the 23 rows equal `PROGRAM.json` `r1_launch`, including
`config_extra`.

**H4 warmup.** `train.ebops.pid.warmup` is hgq2 0.1.9 `BetaPID.warmup`: an integer number of
zero-based **epochs**.
- For `epoch < warmup` beta is re-applied at `init_beta` (1e-7) and no cost is read.
- At `epoch == warmup` the integral is seeded so that beta stays at `init_beta`.
- Option (c) also requires epoch `warmup − 1` to be traced (`ablation.pid_traced_only`), so the legal
  values are 1, 10, 20, …

The values 50 and 150 are legal (w150 superseded: w100 since K1, patch 0043, §3c). The first feedback step comes at epoch 60 or 160, with span 10,
verified by `cpu_gate.py` and by a test. `monitor_p.py` is `monitor_c.py` with the PID canary moved
to that first feedback step (`CANARY_PID_FIRST`). For warmup 1 it is the registered epoch-10,
span-9 check.

**Floors** (0-bit, structural traces; not results). Values:
- E: 171,526.
- A07: 343,053.
- NB: 171,526 (dev `static_floor_a_nb.json`).
- H3 q,k,v at 1 bit: 269,830 (dev `static_floor_a_h3.json`).

Every target is above its floor. The lowest headroom is A07 at 350k, 6,947 (2.0 % of target),
flagged `FLAG_LOW_HEADROOM`. E at 250k has 78,474 and H3 has 80,170. `cpu_gate.py` re-traces each
distinct arch/quant floor and must reproduce the configured value.

## 2. Tests run (home PC, CPU, `~/venv-hgq2` with TF 2.21 / hgq2 0.1.9; pytest 8.4.2 from a scratch `--target` dir)

pytest was not in `~/venv-hgq2`, so it was installed with
`uv pip install --python ~/venv-hgq2/bin/python --target <scratchpad>/pytestlib pytest==8.4.2` and
run with that directory on `PYTHONPATH`. The venv was not modified. The gate's environment was
reproduced by exporting the same variables the Job exports:
`BNJ_DATA_ROOT=/data/chang-n64-20260926`,
`BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot-program-20261005/r1`,
`BNJ_CAMPAIGN_DIR=<tree>/campaigns/pilot1005`, `BNJ_STAGE=pilot-r1`,
`CUDA_VISIBLE_DEVICES=-1`, `WANDB_MODE=disabled`.

| check | tree | result |
| --- | --- | --- |
| `tests/test_run_pack.py`, `BNJ_CAMPAIGN_DIR` = real campaign dir (the gate condition) | 6919462c (base) | 6 failed, 1 passed: reproduces the gate incident ([evidence/test_run_pack_repro.log](evidence/test_run_pack_repro.log)) |
| same | base + 0034 | 7 passed; also 7 passed with the variable unset |
| full suite `tests analysis`, gate exports | 19-arm tree (superseded) | 141 passed, 2 skipped (both `analysis/test_attn_entropy.py:142`), 143 collected, 477 s ([evidence/pytest_full_local.log](evidence/pytest_full_local.log)); `gate_check.py pytest` PASS on its junit |
| full suite, gate exports | final tree (b3fb22c8) | 166 collected, 164 passed, 2 skipped; `gate_check pytest` PASS (§2a) |
| `cpu_gate.py` (pilot) on all configs | 19-arm configs | PREFLIGHT_ALL_PASS 19; PAIRED_INIT_OK E s1 (10 arms), E s2 (4), A07 s1 (5); floors re-traced 171,526 / 343,053 ([log](evidence/cpu_gate_pilot_local_pre-armid.log)) |
| `cpu_gate.py` (pilot) on all configs | final 23 | PREFLIGHT_ALL_PASS 23; `gate_check cpu-gate` PASS (§2a) |
| `pair_nb.py`, [A22] NB vs A initial kernels | final tree | NB_PAIRED_OK seeds 1-8, 15 kernels each; `gate_check nb-pairing` PASS (§2a) |
| new unit tests (generator, monitor warmup, readout on synthetic run dirs, stages, gate checks, runner path) | final tree | 26 + 3 passed (see §2a for the full run) |
| `build_tree.py` | final | `TREE_MATCHES` |
| `run_handoff.py validate` | 25 handoffs | 25 VALID |
| `nrp_doctor.py lint` (live node map via read-only `kubectl get nodes`) | 25 Jobs | exit 0, 25 OK, 0 WARN, 0 ERROR; RTX 3090 pool 48 nodes at 10:55 ([lint.log](lint.log)). **Corrected 2026-10-05 (review v1 C3):** the live pool was 47 nodes at the review and at the re-lint after the fixes ([evidence/fixes-v1/lint-and-validate.log](evidence/fixes-v1/lint-and-validate.log)) |
| gate script fail-fast logic (`GATE_TRAP`, `gate_fail`) extracted and run in bash | — | a failing command prints `GATE_RESULT FAIL exit=1 …` last with exit 1; `gate_fail` prints its reason last with exit 1; the success path prints `GATE_RESULT PASS` with exit 0 |
| Jev `lab_check_protocol` | config-derived `evidence/protocol-r1-from-configs.json` | structural_valid true, no findings; `baseline_path` refused (no frozen snapshot exists: STUDY is not PASS, so `lab_freeze_protocol` has not run). A direct field diff of the config-derived arms against the 19-arm `protocol-r1.json` found 0 differences in batch, lr, arch, target, option_c, warmup and regime. Advisory. |

### 2a. Final-tree local runs

Filled 2026-10-05 by the fixer (review v1 B2). Home PC, CPU, `~/venv-hgq2` (TF 2.21.0), pytest 8.4.2 from a
scratch `--target` dir. The tree was rebuilt by `build_tree.py --out <scratch>` (`TREE_MATCHES`), and the
gate's exports were set (script: [evidence/final-tree-b3fb22/run.sh](evidence/final-tree-b3fb22/run.sh)).
Each check ran the same command and the same `gate_check.py` mode as the gate Job. Engineering checks only; no
number here is quotable.

| check | result | log |
| --- | --- | --- |
| `cpu_gate.py`, 23 configs | `PREFLIGHT_ALL_PASS 23 production 0 pilot_only 23`; `PAIRED_INIT_OK` A07 s1 (5 arms), E s1 (12), E s2 (6); floors re-traced equal to configured (e.g. E 171,526, `cpu_gate.log:7`; A07 343,053, `:49`); `GATE_CHECK cpu-gate PASS`, exit 0 | [cpu_gate.log](evidence/final-tree-b3fb22/cpu_gate.log), [summary.log](evidence/final-tree-b3fb22/summary.log):3-8 |
| `pair_nb.py`, seeds 1-8 | `NB_PAIRED_OK` 1-8, 15 kernels each; `NB_PAIRING_ALL_OK 8`; `GATE_CHECK nb-pairing PASS`, exit 0 | [nb_pairing.log](evidence/final-tree-b3fb22/nb_pairing.log), summary.log:9-19 |
| pytest `--collect-only` | 166 collected (= `gate_check.py:32` `PYTEST_TOTAL`) | summary.log:21 |
| full pytest `tests analysis` | 164 passed, 2 skipped (both `analysis/test_attn_entropy.py:142`), 590 s; `GATE_CHECK pytest PASS`, exit 0 | [pytest.log](evidence/final-tree-b3fb22/pytest.log), [pytest.xml](evidence/final-tree-b3fb22/pytest.xml), summary.log:29-31 |

The `threshold` mode needs the cache and was not run locally. The gate Job runs it as step 1.

## 3. What would be launched

> **Superseded (2026-10-06).** This section describes the b3fb22c8 build (23 GPU Jobs, readout
> deadline 28,800 s, the original rh-IDs). That build is the validated fallback only. The launch
> set is the frozen bundle 98dd2875 in **§3c**: 24 GPU Jobs, pod deadline 20,800 s, readout
> deadline 43,200 s. The text below is kept as written.

- Bundle `b3fb22c825ebd83e5f21c50d4b84d2b79509e4fe396d91bce2e578f3b26823fb` (293,484 bytes, 391 files).
- ConfigMap `kai-pilot1005-code-b3fb22c825`.
- run_study manifest SHA `e6ff034bfc44580a44fc96a27fedcd302f43babbef70169e90802f4ea9a0a8e3`. The pod
  asserts it before any work.
- Image `python@sha256:4d1caded…`, the same as option (c).
- Data: the existing cache `/data/chang-n64-20260926/n64/data`. Its identity comes from the exported
  `data_info.json`.
- New root `/data/chang-n64-20260926/pilot-program-20261005/`, which no earlier campaign writes:
  runs in `r1/runs/<name>`.
- W&B: online, project `BNJetTag-ChangRecipe`, group `chang-n64-20261005-pilot-r1` (`BNJ_STAGE=pilot-r1`).
- Fingerprint ConfigMap `kai-chang0926-fp-e9511d1aeb`, reused. The gate is unchanged: run
  `chang1002c-a-n64-s1`, expect 11,559,681. The handoff tool does not create this ConfigMap.

Hashes: [PREPARED.json](PREPARED.json), [manifests/bundle-manifest.json](manifests/bundle-manifest.json).

**CPU gate** `kai-pilot1005-cpugate-b3fb22`, handoff `handoffs/rh-305a7de984052719d93f30c6`.
- Shape: CPU 8 / 24 GiB, 12 GiB ephemeral, `activeDeadlineSeconds` 14400, backoff 0.
- Output: `/data/chang-n64-20260926/pilot-program-20261005/cpu-gate-b3fb22-r1`.
- It is fail-fast. Steps run cheapest first and the Job stops at the first failure:
  1. threshold (c) re-derived from the cache, must equal 0.2109624456315518 with labels sha
     `e593f51f…7617`;
  2. `cpu_gate.py` on the 23 configs;
  3. `pair_nb.py` at seeds 1–8;
  4. full pytest (`--junitxml`), which must show exactly 166 collected, the 2 known skips, 0
     failures, and every test passed in `test_run_pack`, `test_pid_traced_only`,
     `test_option_c_amendment`, `test_pilot1005`, `test_pilot_stage`, `test_readout_pilot`,
     `test_gate_check`, `test_nb_arm`, `test_attn_bit_floor` and `test_pilot_variants_runner`.
- An `EXIT` trap makes the last line `GATE_RESULT PASS` or `GATE_RESULT FAIL <reason>`. A failure
  exits nonzero, including failures in the header (bundle sha, pip, manifest sha).

**23 GPU Jobs**: Indexed, 1 completion, one arm per pod.
- Product affinity `NVIDIA-GeForce-RTX-3090`; the known-bad nodes are excluded (the historical list,
  c6017, and every `KNOWN_BAD_NODES` entry).
- Resources: CPU 2, memory 10 Gi, ephemeral storage and emptyDir 16 Gi, 1 GPU.
- `backoffLimitPerIndex` 2. DisruptionTarget is ignored. An epoch-0 divergence fails the Job (exit 10).
- Token automount is off.
- Before the arm: the fingerprint gate. Then `run_pack.py packs/<name>.json 500`, with the RSS gate
  at 8,192 MiB fitted over process epochs 5–105.
- Notify-only lines: `GPU_SAMPLE` every 60 s, and for option-(c) arms `MONITOR` every 30 min plus
  `FINAL` from `monitor_p.py`.
- Annotation `bnjettag.io/single-arm-justified` cites `2026-09-29-gpu-benchmark/VERIFY.md:109`:
  RTX 3090 A07 at K=1, GPU utilization 61.6 % overall and 74.3 % steady, 1 arm × 20 epochs, peak
  8,484 / 24,576 MiB. It also states that E at K=1 is unmeasured.

Resource sizing:
- **2 CPU:** measured cores per arm at K=1 on a 3090 is 0.623 (VERIFY.md:109); 2 matches the packing
  recipe.
- **10 Gi memory:** the RSS gate projects to 8,192 MiB, plus about 2 GiB for pip, the monitor and the
  page cache. One arm, so there is no pod-level slack from other arms. The 21-epoch benchmark RSS
  peak was 2,413 MB (VERIFY.md:141).
- **16 Gi ephemeral:** the K=2–4 pods used 24 Gi.

| Job | handoff | arm | hyp | arch | budget | (c) | warmup | seed | 0-bit floor | headroom |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `kai-p1005r1-h1-e-350k-c-s1-b3fb22` | `rh-eb56c43e40ce7acb582d1fcd` | A350-C | H1 | E | 350,000 | yes | 1 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h1-e-350k-c-s2-b3fb22` | `rh-4df2266f8998ca0005822c0e` | A350-C | H1 | E | 350,000 | yes | 1 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h1-e-350k-noc-s1-b3fb22` | `rh-ecf1b25b4545c72bd1265525` | A350-noC | H1 | E | 350,000 | no | 1 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h1-e-350k-noc-s2-b3fb22` | `rh-1610ff70bf0c3da6896c1eeb` | A350-noC | H1 | E | 350,000 | no | 1 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h2-e-250k-c-s1-b3fb22` | `rh-cb9e46a9ea93451dbd1713f1` | E250k-C | H2 | E | 250,000 | yes | 1 | 1 | 171,526 | 78,474 |
| `kai-p1005r1-h2-e-500k-c-s1-b3fb22` | `rh-fd879b0605ce30511bfd3620` | E500k-C | H2 | E | 500,000 | yes | 1 | 1 | 171,526 | 328,474 |
| `kai-p1005r1-h2-e-750k-c-s1-b3fb22` | `rh-0f36af929e6228eb9604c674` | E750k-C | H2 | E | 750,000 | yes | 1 | 1 | 171,526 | 578,474 |
| `kai-p1005r1-h2-e-1m-c-s1-b3fb22` | `rh-34d8cf9a14b935ca59296e0c` | E1000k-C | H2 | E | 1,000,000 | yes | 1 | 1 | 171,526 | 828,474 |
| `kai-p1005r1-h2-e-2m-c-s1-b3fb22` | `rh-ec03aa29c7708a69e7a25fe1` | E2000k-C | H2 | E | 2,000,000 | yes | 1 | 1 | 171,526 | 1,828,474 |
| `kai-p1005r1-h2-e-5m-c-s1-b3fb22` | `rh-205629bd4f7f9dd270fce172` | E5000k-C | H2 | E | 5,000,000 | yes | 1 | 1 | 171,526 | 4,828,474 |
| `kai-p1005r1-h2-a07-350k-c-s1-b3fb22` | `rh-8a035979e88509a2e05b4a65` | A07-350k-C | H2 | A07 | 350,000 | yes | 1 | 1 | 343,053 | **6,947** |
| `kai-p1005r1-h2-a07-500k-c-s1-b3fb22` | `rh-97468a217259aa668dd2136c` | A07-500k-C | H2 | A07 | 500,000 | yes | 1 | 1 | 343,053 | 156,947 |
| `kai-p1005r1-h2-a07-1m-c-s1-b3fb22` | `rh-0e0847b18a85f2131bb03919` | A07-1000k-C | H2 | A07 | 1,000,000 | yes | 1 | 1 | 343,053 | 656,947 |
| `kai-p1005r1-h2-a07-2m-c-s1-b3fb22` | `rh-fb62c47f53a788e502ba07f5` | A07-2000k-C | H2 | A07 | 2,000,000 | yes | 1 | 1 | 343,053 | 1,656,947 |
| `kai-p1005r1-h2-a07-5m-c-s1-b3fb22` | `rh-229f4a462eed7c7ae35fb93a` | A07-5000k-C | H2 | A07 | 5,000,000 | yes | 1 | 1 | 343,053 | 4,656,947 |
| `kai-p1005r1-h4-e-350k-c-w50-s1-b3fb22` | `rh-0dd78d127201b410f4ddc655` | A350-C-w50 | H4 | E | 350,000 | yes | 50 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h4-e-350k-c-w50-s2-b3fb22` | `rh-b0031c99847adb2870dfedb3` | A350-C-w50 | H4 | E | 350,000 | yes | 50 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h4-e-350k-c-w150-s1-b3fb22` | `rh-469038264808dfce8f0d9f86` | A350-C-w150 | H4 | E | 350,000 | yes | 150 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h4-e-350k-c-w150-s2-b3fb22` | `rh-f6882bd06d265212cfd9d455` | A350-C-w150 | H4 | E | 350,000 | yes | 150 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h5-e-350k-c-nb-s1-b3fb22` | `rh-fb842be617ab5bc2f03833b9` | NB350-C | H5 | E | 350,000 | yes | 1 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h5-e-350k-c-nb-s2-b3fb22` | `rh-a3f73460ece7fddc429af8d7` | NB350-C | H5 | E | 350,000 | yes | 1 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h3-e-350k-c-qkv1-s1-b3fb22` | `rh-0bd0a955793b0ff50a726dd0` | A350-C-qkv1 | H3 | E | 350,000 | yes | 1 | 1 | 269,830 | 80,170 |
| `kai-p1005r1-h3-e-350k-c-qkv1-s2-b3fb22` | `rh-fb5e8cc208333618b1a03308` | A350-C-qkv1 | H3 | E | 350,000 | yes | 1 | 2 | 269,830 | 80,170 |

**Readout** `kai-pilot1005-r1ro-b3fb22`, handoff `handoffs/rh-3ae4fd83c0e200766e26c25e`.
- Shape: CPU 8 / 24 GiB, `activeDeadlineSeconds` 28800, backoff 0.
- Steps, each run to completion with its exit code recorded:
  1. `analysis/attn_entropy.py` (a26, validation n = 62,000, on the epoch-500 snapshot checkpoint);
  2. `certify_ebops.py --snapshot 500` (relative 1e-6);
  3. `monitor_p.py --json` on each option-(c) arm's frozen snapshot telemetry;
  4. `readout_pilot.py`.
- `readout_pilot.py` writes `/data/chang-n64-20260926/pilot-program-20261005/r1/readout-epoch-0500-b3fb22-r1/readout.json`
  plus `readout_detail.json`.
- The Job exits nonzero if any step does. readout.json is still written and carries the per-arm
  status.

**readout.json.**
- Per arm, exactly the 15 fields of STUDY.md §5 and PROGRAM.json `readout_fields`, in that order.
  `arm` is the STUDY id (A350-C, NB350-C, A350-C-qkv1, …).
- Top level: `round`, `bundle_sha256`, `n_arms`, `complete` (every expected arm is present and has
  status `complete`). It also carries `threshold_c` and `labels_sha256`, which PROGRAM.json's
  integrity checks read, and `arms`. Both values are taken from the runs; each is null if absent or
  mixed. The brief's list of top-level fields did not include these two (see flags).

Definitions, as in STUDY §5:
- `feasible_any`: conditions (a) and (b) on some traced epoch below 500.
- `nondegenerate_best`: the runner's best-feasible entry exists in the epoch-500 snapshot state.
  `best_feasible_val_acc` and `best_feasible_val_auc` are taken from that entry. The readout also
  recomputes the selection from `activation_widths.jsonl` with the frozen key (accuracy, AUC,
  −EBOPs, −epoch) and marks the arm `failed` if the two disagree.
- `attn_entropy_norm_mean`: the mean of a26 `entropy_over_log_n` over blocks and heads, on the
  checkpoint a26 chose. The readout checks that this is `model_best` when `nondegenerate_best`, and
  `model_min_ebops` otherwise.
- `status`: `complete`, `diverged`, `failed`, `cert_fail` or `audit_fail`. The arm is marked
  `failed` when any of these hold:
  - the threshold differs from 0.2109624456315518;
  - the labels sha differs from `e593f51f…7617`;
  - the epochs are not contiguous;
  - epochs_done ≠ 500;
  - the a26 output is missing.

**Launch (after review; never from this build).**
1. Re-prepare with the gate cleared:
   `freeze_p.py --only <keys> --gate-cleared … --approval-ref …`. This writes a new rh- ID and a new
   `PREPARED-cleared-<keys>.json`; earlier records are never overwritten (option-(c) review C6).
2. Then run `run_handoff.py launch <dir> --submit --approval-ref …`.

Order: the CPU gate first; the 23 pilots only after `GATE_RESULT PASS`; the readout after every pilot
pod has paused at epoch 500 or recorded a terminal marker.

## 3b. Fixes after review v1 (2026-10-05, fixer; `review/PREFLIGHT_critical_v1.md`, `review/STUDY_arbiter_v1.md` F2-F5, F7, F8)

> **Partly superseded (2026-10-06).** The 98dd28 freeze is no longer blocked: it ran at 05:58 JST
> on 2026-10-06 with `--pod-deadline-s 20800`, not 21,600. Every 21,600 s deadline, the 149.2 GPU-h
> worst case and the freeze command below are struck through and replaced by **§3c**.

**State (as of 2026-10-05 16:14).** There are two builds. Neither launches anything; every brief is `scientific_gate: pending`.
- **b3fb22c8 (fallback).** The bundle is unchanged. The CPU gate `kai-pilot1005-cpugate-b3fb22`,
  handoff `rh-04102f81…`, its ConfigMap and `PREPARED-cleared-cpugate.json` were not touched. The
  23 GPU Jobs and the readout were re-prepared at manifest level with the A1 and A2 fixes. The
  new IDs are in [PREPARED.json](PREPARED.json), and the earlier IDs are under its `superseded` key.
  The §3 table above lists the earlier IDs.
- **F2 bundle `98dd2875b7c902bb881562a7acbf00f7cf266a369a74528b6fb8471e0cdc0059` (24 arms).** It is
  built and checked in scratch only. ~~**The campaign freeze is blocked**~~ (superseded: frozen
  2026-10-06 05:58 JST, see §3c): `freeze_p.py`
  (`check_campaign`) refuses unless the arm table equals PROGRAM.json `r1_launch`. The
  PROGRAM.json edit (B1, [A2], and so F7) was **denied by the Claude Code permission classifier**
  and was not retried. Kai decides how PROGRAM.json gets edited. The 24 `r1_launch` rows that
  PROGRAM.json needs are in
  [evidence/fixes-v1/r1_launch_runs_24_for_PROGRAM.json](evidence/fixes-v1/r1_launch_runs_24_for_PROGRAM.json).

**Code records.** No git exists at the lab root, so each change is a file with a SHA-256.
- `freeze_p.py`: `b5975961…1a62`. Diff:
  [evidence/fixes-v1/freeze_p-fixes-v1.diff](evidence/fixes-v1/freeze_p-fixes-v1.diff). The new
  behaviour is opt-in through flags: `--readout-pythonpath`, `--bounded`, `--pod-deadline-s`,
  `--diag`, `--readout-deadline-s`, `--manifests-dir`, `--expect-bundle`. With no flags it
  reproduces all 25 b3fb22 handoff IDs byte for byte (checked in scratch). With the b3fb22 flags it
  reproduces the 24 re-prepared IDs. It never rewrites a frozen tarball or ConfigMap with
  different bytes. An `--only` re-preparation merges into PREPARED.json, and a new bundle keeps the
  old record as `PREPARED-<sha8>.json`.
- `patches/0042-pilot-r1-24-arms.patch` (`0a0fa489…7a`) and `patches/0043-pilot-r1-h4-w100.patch`
  (`fc20656f…72`) are staged and **not yet in PATCHES.json**. Each was one commit in a scratch git
  tree (`b7f778a`, `d65f9c4`). With both appended, `build_tree.py` gives `TREE_MATCHES`.

| finding | fix | evidence (home PC, CPU; engineering checks, not quotable) |
| --- | --- | --- |
| A1 / F3 readout import | The readout Job exports `PYTHONPATH=/work/code:/work/code/campaigns/chang0926` and asserts `READOUT_IMPORT_OK evaluate_roc` before any step. pilot1005 stays first on `sys.path` (the script dir, then the tree root) | The Job script was run locally verbatim on synthetic run dirs: random cache in `load_cache` format (620,000 rows); real pilot configs built untrained with widths set by `static_floor.set_floor`; telemetry from `test_option_c_amendment.simulate`. Only the 4 bundle-install lines were dropped, and `/work/code` and `/data/` were remapped. Old env, b3fb22 readout `rh-3ae4fd83`: `ModuleNotFoundError: No module named 'evaluate_roc'`, so E500k-C became `cert_fail` ([log](evidence/fixes-v1/readout_dryrun/dryrun_old_rh-3ae4fd83_negative_control.log)). New env, `rh-6c39eb23`: `CERTIFIED … 368134 368134`, `CERTIFICATION_ALL_PASS 1 0`, and E500k-C, noC, NB and qkv1 all `complete` ([log](evidence/fixes-v1/readout_dryrun/dryrun_new_rh-6c39eb236bb2599f329ac4d2.log)). The final 98dd28 readout is in the row below. a26/controller exit 1 in these runs comes from the arms with no fixture, which is expected. One certification trace on 558,000 rows took 336.5 s on the home CPU |
| A2 / F4 spend bound | GPU Jobs: pod `activeDeadlineSeconds`. run_pack runs under `timeout` = deadline − elapsed − 420 s. An EXIT trap classifies every exit: deadline → 124, RSS gate (`RSS_GATE_FAIL.json`) → 5, a training-phase failure → 76, and a pre-arm failure within 600 s of script start → 75. `podFailurePolicy`: DisruptionTarget Ignore (unchanged); exit 10 FailJob (unchanged); FailIndex on 5, 76, 124, 137, 143 (137/143 = the kubelet deadline kill of PID 1). `backoffLimitPerIndex` 1, so only exit 75 is retried, once | Harness on the extracted bash, 10/10 cases PASS ([log](evidence/fixes-v1/pod_exit_trap_harness.log)). Deadline on the b3fb22 handoffs: 20,800 s. On the F2 build: ~~21,600 s (6 h, arbiter F4)~~ **20,800 s as frozen (superseded; see §3c)**. Arithmetic in §3c |
| B1 PROGRAM `bundle_sha` vs readout `bundle_sha256` | **not done**: PROGRAM.json edit denied (see State) | — |
| B2 / F8 §2a empty | Rerun and logged; §2a filled | [evidence/final-tree-b3fb22/](evidence/final-tree-b3fb22/) |
| B3 / F8 dev/README A-unchanged | Corrected in `dev/README.md`. `check_a_unchanged.py` was rerun on the final F2 tree with A-s2 and C-s1 added: 9/9 SAME, exit 0 | [log](evidence/fixes-v1/a_unchanged_final_tree_9configs.log) |
| C2 arm ids | STUDY §4 rows 3-4 now use the index ids (E250k-C … E5000k-C, A07-500k-C … A07-5000k-C; the designer's [A3] kept them). For b3fb22, PROGRAM.json already matched the index. The F2 ids are A350-C-qkv1-450k, E-unc-C and A350-C-w100 | `generate.py` `program_arm`; scratch freeze arm-table check |
| C3 pool count | 47 nodes (§2 row corrected) | `required pool = 1 products / 47 nodes` in [lint-and-validate.log](evidence/fixes-v1/lint-and-validate.log) and [scratch_98dd28_lint-and-validate.log](evidence/fixes-v1/scratch_98dd28_lint-and-validate.log) |
| F2 rebuild | 0042: A07-350k-C → A350-C-qkv1-450k (E, 450,000, (c), w1, s1; floor 269,830, headroom 180,170). Adds E-unc-C s1: E, (c), w1, **PID `target_ebops` 100,000,000**, above E's initial EBOPs (9,429,139 at s1 on the cpu_gate synthetic sample, `final-tree-b3fb22/cpu_gate.log:7`). Config only: the controller sits at `min_beta` 1e-10, so the budget never binds. Every config gets `campaign.production` false (only `index.json` `production` is read on any path). 0043: w150 → w100 (Kai, D3). No training code changed: the run_study manifest is still `e6ff034b…`, and only `campaigns/pilot1005/` and 2 tests differ | [f2_config_diff.log](evidence/fixes-v1/f2_config_diff.log): every carried config differs from b3fb22 only in `campaign.production`. w150→w100 differs only in warmup and identity. qkv1-450k vs qkv1 differs only in budget and identity. E-unc vs A350-C differs in budget, hypothesis "control", variant and identity |
| F2 local gate (final tree = 98dd28 contents) | `cpu_gate.py`: `PREFLIGHT_ALL_PASS 24 production 0 pilot_only 24`, PAIRED_INIT_OK A07 s1 (4), E s1 (14), E s2 (6), `GATE_CHECK cpu-gate PASS`. `pair_nb.py`: NB_PAIRING_ALL_OK 8, PASS. pytest: 166 collected, 164 passed, 2 skipped, `GATE_CHECK pytest PASS` | [evidence/final-tree-98dd28/](evidence/final-tree-98dd28/) |
| F5 readout_diag.json | Runs after readout.json and never enters the Job exit status or any rule. It holds t_uniform (Q **or** K all 0 bits in every block, from `widths`), t_budget, site order, cost split (`per_layer` grouped: attention non-softmax, softmax tables, ffn, input_proj, head), and controller error (`ebops_in_training_over_traced` over stepped epochs). For NB it adds `weight_bits_mean`. It also holds a26 plus val acc on `checkpoints/epoch-0500/model.keras` for every row, and a26 on the snapshot `model_unconstrained.keras` for every E row and A07-5000k-C. Readout deadline 43,200 s (CPU), because certification is ≤ 2 checkpoints × 24 arms at the home-PC rate of about 5.6 min each | Crafted-record harness 8/8 PASS ([log](evidence/fixes-v1/readout_diag_harness.log)). In the dry run on the intermediate F2 build: `READOUT_DIAG_WROTE … arms 24`, `diag_exit=0` ([log](evidence/fixes-v1/readout_dryrun/dryrun_f2_scratch_rh-20c9ea13.log)). Final build, readout `rh-deccad51`: `READOUT_IMPORT_OK`, `CERTIFIED` E500k-C and E-unc-C, `CERTIFICATION_ALL_PASS 2 0`, and noC, NB, qkv1, qkv1-450k, E-unc-C and E500k-C all `complete`. `READOUT_DIAG_DONE diag_exit=0`. Wall time 26 min for 6 fixture arms ([log](evidence/fixes-v1/readout_dryrun/dryrun_final_98dd28_rh-deccad51.log)) |
| F7 PROGRAM.json reconcile | **not done**: denied (see State) | — |

> **Superseded by §3c (2026-10-06).** Kai set D = 20,800 s (20 s under the first option below), so the
> 21,600 s deadline, the 149.2 GPU-h worst case and the A07 fit at 21,600 no longer describe the
> frozen set. Kept as written, struck through:

~~**F4 spend arithmetic (24 pods, R1 cap 144 GPU-h, Kai 2026-10-05).** The pod deadline D = 21,600 s~~
~~counts from pod start.~~
- ~~Nominal: 24 × 21,600 s = 518,400 s = **144.0 GPU-h**.~~
- ~~Plus one pre-arm retry per arm (exit 75, within 600 s of script start): + 24 × 600 s = 4.0 → 148.0.~~
- ~~Plus the 180 s grace if the in-script timeout fails and the kubelet kills PID 1: + 24 × 180 s =~~
  ~~1.2 → **149.2 GPU-h**.~~
- ~~Not bounded by the Job spec: the image pull and handoff init of a retried attempt (minutes), and~~
  ~~DisruptionTarget replacements (Ignore, as before). Each is counted against the cap when it occurs.~~

~~The honest worst case is therefore 149.2 GPU-h, 5.2 over 144. Two ways to keep a hard 144:~~
- ~~D = 20,820 s, giving 24 × (20,820 + 600 + 180) = 518,400 s = 144.0;~~
- ~~or no pre-arm retry (`backoffLimitPerIndex` 0), giving 24 × 21,780 = 145.2, or D = 21,420 for 144.0.~~

~~A07 fit at D = 21,600: pre-arm about 4-5 min (training-batch ONBOARDING.md:31, an A10 pod). The~~
~~run_pack budget is about 21,600 − 300 − 420 = 20,880 s, against 500 × 38.8 s = 19,400 s (the~~
~~pessimistic bound, gpu-benchmark VERIFY.md:109) or 500 × 30.85 s = 15,425 s. lint WARNs~~
~~`backoffLimitPerIndex=1` on every GPU Job. That is deliberate (retries cost cap); the hook blocks~~
~~only on ERROR.~~

**Re-prepared handoffs.**
- b3fb22 (in PREPARED.json): readout `rh-6c39eb236bb2599f329ac4d2`, GPU Jobs as listed there (e.g.
  `r1-h2-a07-350k-c-s1` `rh-f0d027585275bb9bf3b83945`). 24/24 VALID. nrp_doctor: 0 ERROR,
  23 WARN (backoff 1), 1 OK ([log](evidence/fixes-v1/lint-and-validate.log)).
- 98dd28 (scratch freeze, [log](evidence/fixes-v1/scratch_freeze_98dd28.log)): cpugate
  `rh-92e3bc715b0fb58e4b87dcc0`, readout `rh-deccad5136f005dcb4250764`, and 24 GPU handoffs. 26/26
  VALID. nrp_doctor: 0 ERROR, 24 WARN (backoff 1), pool 47 nodes
  ([log](evidence/fixes-v1/scratch_98dd28_lint-and-validate.log)). The IDs are content addresses.
  The real freeze reproduces them only if the inputs are byte-equal.

**Jev `jev_check_methods`** on a one-paragraph summary of the R1 method (audit
`jv-8cd91468b50b494e878e8ba493cc03a6`; advisory, not a verdict). Jev's labels, with a hand check of each:
- selection: consistent (0.95).
- metrics: conflict (0.55), mandatory review. By hand: the frozen selection key is validation
  accuracy, then AUC, then −EBOPs, then −epoch (`readout_pilot.py` `key`). The readout reports both
  accuracy and AUC on validation n = 62,000, as in STUDY §5. No conflict was found in the text, and
  Jev's reason is unknown.
- provenance: missing (0.93). The data identity is in each handoff (`data_info.json` of the gated
  N64 cache). The summary did not state it.
- authority: missing (0.89). True: PROGRAM.json is unsigned, and the STUDY v2 arbiter has not run (F10).
- comparability: missing (0.58).
- uncertainty: missing (0.38). Pilots are directional by rule (STUDY §6).

**To freeze 98dd28 once PROGRAM.json carries the 24 rows** (done 2026-10-06 05:58 JST; see §3c):
1. Append 0042 and 0043 to `patches/PATCHES.json`.
2. Run `build_tree.py --out <tmp>` and copy `<tmp>/code` to `code/tree`. `build_tree.py` must then
   print `TREE_MATCHES`.
3. Run (superseded: the freeze ran with `--pod-deadline-s 20800`; the exact command is in §3c):
   ```
   # SUPERSEDED, not run: --pod-deadline-s 21600
   freeze_p.py --readout-pythonpath --bounded --diag --pod-deadline-s 21600 \
       --readout-deadline-s 43200 --manifests-dir manifests-98dd28 --expect-bundle 98dd2875
   ```
4. Run lint and validate.
5. A new CPU gate is required on the new bundle (L3), followed by PREFLIGHT critical v2.

## 3c. Frozen bundle 98dd2875 (2026-10-06)

This is the launch set. It replaces §3 (b3fb22, 23 Jobs) and the 21,600 s / 149.2 GPU-h text in
§3b. Sources: [PREPARED.json](PREPARED.json), [PREPARED-cleared-cpugate.json](PREPARED-cleared-cpugate.json),
JOURNAL.md 2026-10-06 05:58 (lines 41-42), and
[review/PREFLIGHT_critical_v2.md](review/PREFLIGHT_critical_v2.md) (B-new-1, B-new-2, C1-C6), which
re-checked every hash below read-only. This section is text only. No handoff, manifest or code byte
changed when it was written.

**Freeze (orchestrator, 2026-10-06 05:58 JST).**
1. `patches/PATCHES.json` now has 12 entries (0042 `0a0fa489…`, 0043 `fc20656f…` appended; 12/12
   sha256 equal in critical v2).
2. `build_tree.py` printed `TREE_MATCHES`.
3. The exact freeze command:
   ```
   python3 freeze_p.py --readout-pythonpath --bounded --diag --pod-deadline-s 20800 --readout-deadline-s 43200 --manifests-dir manifests-98dd28 --expect-bundle 98dd2875
   ```
4. Result:
   - Bundle `98dd2875b7c902bb881562a7acbf00f7cf266a369a74528b6fb8471e0cdc0059`
     (`manifests-98dd28/pilot1005-code.tar.gz`, 294,480 B, 393 files, per critical v2).
   - ConfigMap `kai-pilot1005-code-98dd2875b7`.
   - run_study manifest `e6ff034bfc44580a44fc96a27fedcd302f43babbef70169e90802f4ea9a0a8e3`,
     unchanged from b3fb22, so no training-path file changed.
   - 26 handoffs (CPU gate, 24 GPU Jobs, readout), 26/26 `VALID`.
   - `nrp_doctor.py lint`: 0 ERROR / 24 WARN. Every WARN is `backoffLimitPerIndex=1` on a GPU Job.
     That is deliberate: one pre-arm retry, whose cost counts against the cap. The hook blocks only
     on ERROR. The lint note "no activeDeadlineSeconds" is misleading, because the lint reads the
     Job level only and the deadline is set at pod level (critical v2 C3).
   - The CPU gate and readout IDs equal the scratch freeze in §3b (`rh-92e3bc71…`,
     `rh-deccad51…`). The 24 GPU IDs differ from the scratch ones, as they should: the scratch
     freeze used 21,600 s.

**CPU gate.** `kai-pilot1005-cpugate-98dd28`, submitted at 05:58 JST on 2026-10-06 from the
gate-cleared re-preparation `handoffs/rh-c11b0c23904a7f7b2a629b5f` (prepared record
`rh-92e3bc715b0fb58e4b87dcc0`; approval `local/2026-10-05-execution/r1-98dd28-approval.json`).
Shape as in §3 (CPU 8 / 24 GiB, Job `activeDeadlineSeconds` 14,400, backoff 0), with output
`cpu-gate-98dd28-r1` and `N_CONFIGS = 24`. No `GATE_RESULT` was recorded when this section was
written. The 24 pilots need `GATE_RESULT PASS` (critical v2 L1).

**24 GPU Jobs.** Each is Indexed with 1 completion and one arm per pod, on product
`NVIDIA-GeForce-RTX-3090` with the known-bad nodes excluded. Resources: CPU 2, memory 10 Gi,
16 Gi ephemeral, 1 GPU. Pod `activeDeadlineSeconds` is **D = 20,800 s** (none at Job level), with
grace 180 s and `backoffLimitPerIndex` 1. `podFailurePolicy`: DisruptionTarget Ignore, exit 10
FailJob, FailIndex on [5, 76, 124, 137, 143], so only the pre-arm exit 75 (within 600 s of script
start) is retried, once. Each Job is submitted from a `--gate-cleared` re-preparation under the
byte rule of critical v2 L4. The rh-IDs below are the prepared records, not the cleared ones.

| Job | handoff (prepared) | arm | hyp | arch | budget | (c) | warmup | seed | 0-bit floor | headroom |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `kai-p1005r1-ctl-e-unc-c-s1-98dd28` | `rh-319c97499b4a08c675883d4b` | E-unc-C | control | E | 100,000,000 | yes | 1 | 1 | 171,526 | 99,828,474 |
| `kai-p1005r1-h1-e-350k-c-s1-98dd28` | `rh-11315c1055d4e711402f577f` | A350-C | H1 | E | 350,000 | yes | 1 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h1-e-350k-c-s2-98dd28` | `rh-97d668acad27f2bbb0c2e2d7` | A350-C | H1 | E | 350,000 | yes | 1 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h1-e-350k-noc-s1-98dd28` | `rh-9faf0b5546e99917d4d5bf68` | A350-noC | H1 | E | 350,000 | no | 1 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h1-e-350k-noc-s2-98dd28` | `rh-4e6171f2e742cf8956ccb253` | A350-noC | H1 | E | 350,000 | no | 1 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h2-a07-1m-c-s1-98dd28` | `rh-0c29faa34dcbd03eb8e1aee1` | A07-1000k-C | H2 | A07 | 1,000,000 | yes | 1 | 1 | 343,053 | 656,947 |
| `kai-p1005r1-h2-a07-2m-c-s1-98dd28` | `rh-54e475a4c4655c1d05263f99` | A07-2000k-C | H2 | A07 | 2,000,000 | yes | 1 | 1 | 343,053 | 1,656,947 |
| `kai-p1005r1-h2-a07-500k-c-s1-98dd28` | `rh-426a3d721c92f095abde9e16` | A07-500k-C | H2 | A07 | 500,000 | yes | 1 | 1 | 343,053 | 156,947 |
| `kai-p1005r1-h2-a07-5m-c-s1-98dd28` | `rh-516855215bc3f56ff315ccf6` | A07-5000k-C | H2 | A07 | 5,000,000 | yes | 1 | 1 | 343,053 | 4,656,947 |
| `kai-p1005r1-h2-e-1m-c-s1-98dd28` | `rh-8c2290ab1c4b445207bd3c5d` | E1000k-C | H2 | E | 1,000,000 | yes | 1 | 1 | 171,526 | 828,474 |
| `kai-p1005r1-h2-e-250k-c-s1-98dd28` | `rh-b050368f2bc35fd7e86a97e7` | E250k-C | H2 | E | 250,000 | yes | 1 | 1 | 171,526 | 78,474 |
| `kai-p1005r1-h2-e-2m-c-s1-98dd28` | `rh-9ade87bfd3397f531baa20e6` | E2000k-C | H2 | E | 2,000,000 | yes | 1 | 1 | 171,526 | 1,828,474 |
| `kai-p1005r1-h2-e-500k-c-s1-98dd28` | `rh-ca3aa4d313fc6ad6397b4050` | E500k-C | H2 | E | 500,000 | yes | 1 | 1 | 171,526 | 328,474 |
| `kai-p1005r1-h2-e-5m-c-s1-98dd28` | `rh-0c6a40c4c060bfc9aa91698b` | E5000k-C | H2 | E | 5,000,000 | yes | 1 | 1 | 171,526 | 4,828,474 |
| `kai-p1005r1-h2-e-750k-c-s1-98dd28` | `rh-411a7211dabf0b6ff4abc715` | E750k-C | H2 | E | 750,000 | yes | 1 | 1 | 171,526 | 578,474 |
| `kai-p1005r1-h3-e-350k-c-qkv1-s1-98dd28` | `rh-fc1db900791452bb664af308` | A350-C-qkv1 | H3 | E | 350,000 | yes | 1 | 1 | 269,830 | 80,170 |
| `kai-p1005r1-h3-e-350k-c-qkv1-s2-98dd28` | `rh-de60d48cd7d0c03b9841dae9` | A350-C-qkv1 | H3 | E | 350,000 | yes | 1 | 2 | 269,830 | 80,170 |
| `kai-p1005r1-h3-e-450k-c-qkv1-s1-98dd28` | `rh-923cacfd4cad1b0c07bfe340` | A350-C-qkv1-450k | H3 | E | 450,000 | yes | 1 | 1 | 269,830 | 180,170 |
| `kai-p1005r1-h4-e-350k-c-w100-s1-98dd28` | `rh-44d00149e0ebe980bfea01e5` | A350-C-w100 | H4 | E | 350,000 | yes | 100 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h4-e-350k-c-w100-s2-98dd28` | `rh-92ab33062a3e15024be4f02f` | A350-C-w100 | H4 | E | 350,000 | yes | 100 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h4-e-350k-c-w50-s1-98dd28` | `rh-aeb468333f216eeb6cbaf4b4` | A350-C-w50 | H4 | E | 350,000 | yes | 50 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h4-e-350k-c-w50-s2-98dd28` | `rh-134cdc1f9002b201d569c852` | A350-C-w50 | H4 | E | 350,000 | yes | 50 | 2 | 171,526 | 178,474 |
| `kai-p1005r1-h5-e-350k-c-nb-s1-98dd28` | `rh-86ec9a40b73cc3c8566cd277` | NB350-C | H5 | E | 350,000 | yes | 1 | 1 | 171,526 | 178,474 |
| `kai-p1005r1-h5-e-350k-c-nb-s2-98dd28` | `rh-88950a93c8854c55d64e5c93` | NB350-C | H5 | E | 350,000 | yes | 1 | 2 | 171,526 | 178,474 |

**Readout.** `kai-pilot1005-r1ro-98dd28`, prepared handoff `rh-deccad5136f005dcb4250764`.
CPU 8 / 24 Gi, Job `activeDeadlineSeconds` **43,200 s**, backoff 0, `PYTHONPATH` with
`READOUT_IMPORT_OK` asserted. Output `readout-epoch-0500-98dd28-r1`. It runs only after every R1 pod
has reached epoch 500 or a terminal marker, from a gate-cleared re-preparation, with PROGRAM
`r1_readout` filled (critical v2 L5). **[A5] (arbiter v3 S1)** The R1 readout Job is not submitted
until arbiter v2 Q1-Q5 have landed; Q1 and Q3 land in one PROGRAM.json edit, and the readout is the
Q2 re-preparation, not `rh-deccad51`, unless Kai rules otherwise.

**Spend bound (R1 cap 144 GPU-h, Kai 2026-10-05; PROGRAM.json `pod_deadline_s` 20800).** One
GPU per pod, 24 pods. The per-pod terms that the Job spec bounds:
- 600 s: a retried first attempt (exit 75, measured from script start `T0`);
- 20,800 s: the pod deadline D on the attempt that runs;
- 180 s: the grace period if the in-script timeout fails and the kubelet kills PID 1.

Bounded worst case: 24 × (600 + 20,800 + 180) s = 24 × 21,580 s = 517,920 s = **143.87 GPU-h**.
The slack to 144 GPU-h is 518,400 − 517,920 = **480 s in total**, or 20 s per arm if every arm
retried.

That bound is not complete. The following terms are not covered by the Job spec (critical v2
B-new-2):
1. **Image pull and init on a retried attempt.** The 600 s window starts at script start, but the
   pod holds the GPU from `startTime`, which comes before the image pull and the
   `record-run-handoff` init container. The first attempt's pull and init time adds for each arm
   that retries.
2. **An init-container hang that runs to the deadline.** The `train` container then has no exit
   code, no FailIndex rule matches, and the hang counts as the one retry. Up to D is added for each
   arm where this happens.
3. **Pod replacements after disruption.** DisruptionTarget is Ignore in the failure policy, so a
   replaced pod does not consume the retry and its time is not bounded by the spec.

The bound is therefore stated as **143.87 GPU-h + Σ (pull + init) over retried arms + any
init-hang time + disruption replacements**. Each of these is counted against the cap when it
occurs (PROGRAM `retries_count_against_cap: true`). The orchestrator checks spend at follow-up
(RULES §4) from pod `startTime` and end times.

Expected spend: about **105 to 132 GPU-h**. That is 24 × (15,425 to 19,400 s of training + about
300 s pre-arm), at 30.85 to 38.8 s per epoch × 500 epochs (gpu-benchmark VERIFY.md:109, RTX 3090,
A07 at K=1, n = 1 × 20 epochs). These are planning rates, not results. E is about half the
parameters of A07, and its epoch time at K=1 is unmeasured.

**A07 deadline margin (critical v2 C1).** The run_pack budget is about 20,800 − 300 (pre-arm) − 420
(timeout margin) = 20,080 s. Against 500 × 38.8 s = 19,400 s (the pessimistic rate) the margin is
**about 680 s (3.4 %)**. Against 500 × 30.85 s = 15,425 s it is 4,655 s. A deadline kill is exit
124 → FailIndex → status `failed` → the R1 integrity check stops the program for Kai: safe, but
costly. At the 30-min utilization check, also project `epoch_seconds` × 500 for the 4 A07 pods.

**Readout deadline (critical v2 C2).** 43,200 s (12 h). The home-PC estimate is about 5.3 h:
certification 336.5 s per trace × at most 48 traces (about 4.5 h), plus a26 at about 45 s per
checkpoint over about 69 runs including diag. A CPU pod at 2 threads may be 1.5 to 2× slower, so the
deadline holds but not by much. If it falls during diag, `readout.json` is already written but the
Job reads Failed. These are home-PC engineering timings, not quotable.

**Carried, not blocking a manual launch (critical v2 C4-C6).** PROGRAM.json `r1_launch.condition`
still compares `pods_requested: 23`, its `handoffs` field holds prose, and `r1_readout` keeps
PLACEHOLDER values. All of these must be filled before any autopilot use. The briefs still read
"PROGRAM.json not yet signed", which the gate-cleared re-preparation replaces. The gate re-traces
only the 0-bit floor.

## 3d. R1 relaunch (r2) (2026-10-07)

> **Correction (2026-10-08, review/REGRESSION_TICKET_r2-resume.md §3-§4, PVC arm logs).** The resume
> premise below held for 6 of the 23 r2 arms, not all 23. Only 6 arms had R1 state (`RSS_GATE_FAIL.json`
> in 6 run dirs); the other 17 R1 Jobs failed before any arm started. First `resume_epoch=` line per r2 arm log:
> resumed at epoch 100 and completed: `ctl-e-unc-c-s1`, `h1-e-350k-c-s1`, `h2-e-750k-c-s1`, `h3-e-350k-c-qkv1-s2`;
> resumed at epoch 100, then lost with the node at epoch 200 (`h3-e-450k-c-qkv1-s1`) and 175 (`h5-e-350k-c-nb-s1`);
> started at epoch 0: the other 17. The code-path reading in this section is still correct for an arm that
> has a checkpoint; it does not apply to an arm that never had one. The relaunch of the 8 failed r2 arms is §3e.

Approval: `local/2026-10-07-execution/r1b-relaunch-approval.json` (Kai, 2026-10-07 07:29 JST;
`.claude/memory/decisions.md` top entry). It covers the 23 R1 arms that the RSS gate stopped (RUN.md
"Incident 2026-10-06"), relaunched with `BNJ_RSS_GATE_LIMIT_MB` unset under new Job names. They
resume from their checkpoints and stay inside the 144 GPU-h R1 cap. It does not cover the readout,
R2, R3, production, or any change to training code or configs. `h3-e-350k-c-qkv1-s1` completed and
is not relaunched. **Nothing in this section has been submitted.** The 23 handoffs carry
`scientific_gate: pending`.

**Unchanged.** The bundle is `98dd2875…0059`, rebuilt byte-identical (`--expect-bundle 98dd2875`):
the tarball, `configmap.json` and `bundle-manifest.json` equal `manifests-98dd28/`. The ConfigMap
is `kai-pilot1005-code-98dd2875b7` and the run_study manifest `e6ff034b…`. The configs and their
`config_sha256` are unchanged, and so are `BNJ_STAGE=pilot-r1`, `RUN_ROOT` and the run dirs. Also
unchanged: RTX 3090, the known-bad-node exclusion, CPU 2 / 10 Gi / 16 Gi / 1 GPU, grace 180 s,
`backoffLimitPerIndex` 1, and FailIndex on [5, 76, 124, 137, 143].

### Resume path (read from the frozen tree `code/tree`; the PVC was not inspected)

A relaunched pod **resumes automatically** from the newest committed checkpoint generation. It
does not restart from initialization or refuse, and no marker blocks it.

1. **Output-dir guards.** The GPU Job script has no `test ! -e` on the run dir. Only the CPU gate
   and the readout have one (freeze_p.py `cpugate_tail`, `readout_tail`). `run_pack.py:184-187`
   skips an arm only if `DIVERGED.json` or `VERIFIED_COMPLETE.json` exists. `run_study.py:108`
   runs `mkdir(exist_ok=True)`. `run_study.py:109-112` exits 3 only on `DIVERGED.json`.
   `run_study.py:119-120` requires the stored `source_manifest.json` to equal this tree's manifest,
   which holds because the bundle is the same. `run_study.py:127-130` returns early only on
   `VERIFIED_COMPLETE.json`. That file is written only when `completed_epochs == train.epochs`
   (7,000) (`run_study.py:192-193`), so a killed arm does not have one.
2. **Checkpoint generations.** `experiment.checkpoint_every_epochs` = 25 in all 24 configs.
   `save_checkpoint` keeps two generations (`ablation.py:262-264`) and points `latest.json` at the
   newest (`:261`). The gate step runs after the checkpoint step in the same epoch
   (`ablation.py:1171-1174`, then `:1186-1187`). The gate fired at the end of process epoch 105
   (one-based), and 105 is not a multiple of 25. The newest generation is therefore `epoch-0100`,
   with `epoch-0075` kept. The pod-log tails of 4 of the 23 Jobs show `checkpoint=epoch-0050/0075/0100`,
   last epoch line 104, then `RSS_GATE … FAIL` and exit 5 (`evidence/r2/pod-logs-98dd28/`). The other
   19 logs were no longer retrievable. `restore_checkpoint` (`ablation.py:293-330`) asserts that
   `config_sha256`, `data_sha256` and `code_sha256` (= `BNHGQ2_CODE_SHA256`, set from the same MSHA)
   are equal (`:300-302`). It restores the model, the optimizer and the selected files. It deletes
   snapshots after epoch 100 (none exist, since `snapshot_every_epochs` is 500). It truncates
   `activation_widths.jsonl` to epochs < 100 and asserts exactly 100 rows (`:321-325`).
   `run_training` takes the resume branch (`ablation.py:909-911`), and the loop starts at epoch
   index 100. Epochs 101-105 are retrained.
3. **Markers.** `RSS_GATE_FAIL.json` (`ablation.py:877`) is read by no training or readout code.
   The only reader is the 98dd28 Job script line that maps a nonzero run_pack exit to exit 5 when the
   file exists (pre-r2 freeze_p.py:411-412, `evidence/r2/freeze_p.pre-r2.py`). The file is stale in every killed run dir. In r2 that line is
   dropped, so a later failure is classified as 76 (training phase, still FailIndex) and not
   mislabelled as an RSS-gate stop. `ARM_MEMORY_GATE_FAILED` is a log line only
   (`run_pack.py:224-227`) and leaves no file. No stale final or failed marker makes run_pack skip
   or refuse the arm, so no manifest-level workaround is needed beyond the env change.
4. **Epoch-0 divergence check** (`H.EPOCH0_CHECK`, training-batch freeze.py:310-323). It reads only
   `DIVERGED.json` and fires only if every arm of the pack diverged at zero-based epoch 0. A killed arm
   exited 5, not 3 (`record_divergence` raises `Diverged` → exit 3), so it has no `DIVERGED.json` and
   the check prints `=None` and passes.
5. **pid_telemetry on resume.** For option-(c) arms (21 of 23; both `h1-…-noc` arms have no
   telemetry), `restore_checkpoint` calls `truncate_jsonl(pid_telemetry.jsonl, 100)` and asserts
   exactly 100 rows (`ablation.py:326-328`, `:676-684`). One row is appended per epoch from epoch 0
   (`ablation.py:1152-1153`), so the 105 rows on disk become 100.
6. **W&B run id.** `stage_run_id(cfg['name'], 'pilot-r1')` = sha256(`pilot-r1\0<name>`)[:12]
   (`wandb_util.py:82-86`) does not depend on the Job name. `wandb.init(id=run_id, resume='allow')`
   (`ablation.py:957-961`) reopens the same run, which `run_study.py:141-146` had marked
   `phase: crashed` with exit 1. One known gap: W&B already holds steps 1-104 from the killed
   attempt. The replayed epochs 101-104 log `step=epoch+1` ≤ 104 and W&B drops them as
   non-monotonic, so W&B shows the abandoned values at steps 101-104 and the new trajectory from
   step 105. The PVC files (`activation_widths.jsonl`, `pid_telemetry.jsonl`, snapshots) are
   truncated correctly and are the readout's source. W&B is a monitor only.
7. **Gate off.** With `BNJ_RSS_GATE_LIMIT_MB` unset, `rss_gate_from_env` returns None
   (`ablation.py:847-849`). There is no gate and no `host_rss_mb` on the epoch line. The backstop
   is the 10 Gi container limit. An OOM is final either way: a whole-container kill gives 137, or,
   if only the training process is killed, run_pack resumes the arm up to 2 times in the pod
   (run_pack.py:39, :237-242), then exits 1, which the script maps to 76; both are FailIndex
   (review r2 B-r2-1). "Well under 10 Gi" refers to process RSS; the cgroup counter also holds
   reclaimable page cache (8.3-9.0 GiB at epoch 104 with zero pressure, review r2 C1). From the 4 recovered
   tails, the steepest slope is 2.889 MB/epoch (qkv1-s2, baseline 2,528 MB). The process restarts at
   epoch 100, so 400 more epochs reach about 2,528 + 400 × 2.889 ≈ 3,684 MB, well under 10 Gi.
   These are engineering figures from 4 pod logs, not quotable.

### Builder change (freeze_p.py; no git at the lab root, so the record is a file with a SHA-256)

- `freeze_p.py`: `b5975961…1a62` → **`25de26c0aa471bf2db77b7ce685cf1a77120fb78f05440a6c35965d0e0cff338`**.
  The diff is `evidence/r2/freeze_p-r2.diff` (`87a2e3ab…a6c`), and the pre-edit copy is
  `evidence/r2/freeze_p.pre-r2.py`.
- New opt-in flags:
  - `--no-rss-gate`: no `export BNJ_RSS_GATE_LIMIT_MB=… BNJ_RSS_GATE_WINDOW=…` line, no
    `RSS_GATE_FAIL.json` → exit 5 line, and the `bnjettag.io/rss-gate` annotation becomes `off`.
  - `--job-suffix=-r2`: GPU Job names only.
  - `--prepared-out FILE`: writes a new record and asserts that the file does not exist and is not
    PREPARED.json.
  - `--only` is the existing filter.
- **Defaults are byte-identical.** I re-ran the exact §3c freeze command into a scratch manifests
  dir with a scratch `--prepared-out`. All 26 job.json files equal `manifests-98dd28/`. All 26
  handoff IDs and their `record_sha256` / `job_json_sha256` equal PREPARED.json. No new directory
  appeared under `handoffs/`, and every `PREPARED*.json` kept its sha256
  (`evidence/r2/defaults-check-98dd28.log`).
- The r2 command (`evidence/r2/freeze-r2-command.txt`, log `freeze-r2.log`):
  ```
  python3 freeze_p.py --readout-pythonpath --bounded --diag --pod-deadline-s 18000 --readout-deadline-s 43200 \
    --manifests-dir manifests-98dd28-r2 --expect-bundle 98dd2875 --no-rss-gate --job-suffix=-r2 \
    --prepared-out PREPARED-r2.json --only <the 23 r1-* keys except r1-h3-e-350k-c-qkv1-s1>
  ```
  The output is `manifests-98dd28-r2/` (49 files) and `PREPARED-r2.json`
  (`1682f712…3004`, gate pending). PREPARED.json and every other `PREPARED*.json` are byte-unchanged.

### Checks (offline, read-only)

- **job.json diff vs 98dd28, 23/23** (`evidence/r2/jobjson-diff-vs-98dd28.txt`). The only
  differences are:
  - `metadata.name` (+`-r2`);
  - pod `activeDeadlineSeconds` 20,800 → 18,000;
  - the `active-deadline` annotation (the deadline number);
  - the `rss-gate` annotation (`off`);
  - in the script: the deadline in the two `ARM_BUDGET_S`/`ARM_DEADLINE` lines, the removed
    `export BNJ_RSS_GATE_…` line, and the removed `RSS_GATE_FAIL.json` line.

  Labels, the image, resources, affinity, volumes, the env (`WANDB_API_KEY`, `NODE_NAME`) and the
  failure policy are identical. The deadline is a fourth difference, beyond the name, the identity
  fields and the RSS env lines. It is deliberate (spend, below).
- **Brief diff vs the 98dd28 pending records, 23/23** (`evidence/r2/brief-diff-vs-98dd28-pending.txt`):
  - `purpose` gains one relaunch sentence;
  - `stop_rules[0]` drops "RSS projection gate";
  - `stop_rules[3]` shows the new deadline. Its text still says "RSS gate", because exit 5 stays in
    FailIndex.
- `run_handoff.py validate`: **23/23 VALID** (`evidence/r2/validate-r2.log`).
- `nrp_doctor.py lint`: **0 ERROR / 23 WARN**, the same deliberate `backoffLimitPerIndex=1` WARN as
  §3c. Exit 1 means warnings only, which the hook does not block (`evidence/r2/lint-r2.log`).

| Job | handoff (prepared, gate pending) |
| --- | --- |
| `kai-p1005r1-ctl-e-unc-c-s1-98dd28-r2` | `rh-c5c82dd033ab25fd62f13bc0` |
| `kai-p1005r1-h1-e-350k-c-s1-98dd28-r2` | `rh-2f2eadddb0ffc604ac2e0db0` |
| `kai-p1005r1-h1-e-350k-c-s2-98dd28-r2` | `rh-895dce6f05374b7f16531d02` |
| `kai-p1005r1-h1-e-350k-noc-s1-98dd28-r2` | `rh-b960e5a814d898e663cf1d8a` |
| `kai-p1005r1-h1-e-350k-noc-s2-98dd28-r2` | `rh-2a236958030f8057d7af5ab0` |
| `kai-p1005r1-h2-a07-1m-c-s1-98dd28-r2` | `rh-410f4cdfc089f89d5b4dbe8c` |
| `kai-p1005r1-h2-a07-2m-c-s1-98dd28-r2` | `rh-1d3b5c629cb3b680cd8a2854` |
| `kai-p1005r1-h2-a07-500k-c-s1-98dd28-r2` | `rh-3a6cd4788f118322bf4ac68b` |
| `kai-p1005r1-h2-a07-5m-c-s1-98dd28-r2` | `rh-8f58f76bc17958ef2b424928` |
| `kai-p1005r1-h2-e-1m-c-s1-98dd28-r2` | `rh-a5d6575d64f18fec76d18ec7` |
| `kai-p1005r1-h2-e-250k-c-s1-98dd28-r2` | `rh-63d89c7a9b1678b422e69ce3` |
| `kai-p1005r1-h2-e-2m-c-s1-98dd28-r2` | `rh-0698e9dd1ec04c324147acdc` |
| `kai-p1005r1-h2-e-500k-c-s1-98dd28-r2` | `rh-64570e3430e734a3c76c12a8` |
| `kai-p1005r1-h2-e-5m-c-s1-98dd28-r2` | `rh-0b27060abbeda749aaf5994a` |
| `kai-p1005r1-h2-e-750k-c-s1-98dd28-r2` | `rh-bc7bbbc464d8f4b110ad98c9` |
| `kai-p1005r1-h3-e-350k-c-qkv1-s2-98dd28-r2` | `rh-3069fd9e5bbd49e0a1b26434` |
| `kai-p1005r1-h3-e-450k-c-qkv1-s1-98dd28-r2` | `rh-2cc1ad12623064a3aa632b8e` |
| `kai-p1005r1-h4-e-350k-c-w100-s1-98dd28-r2` | `rh-2082ce6d6e65b73b8be73333` |
| `kai-p1005r1-h4-e-350k-c-w100-s2-98dd28-r2` | `rh-46a92bda7d5a6280784f1cc1` |
| `kai-p1005r1-h4-e-350k-c-w50-s1-98dd28-r2` | `rh-9038831fb3a59b25279843a7` |
| `kai-p1005r1-h4-e-350k-c-w50-s2-98dd28-r2` | `rh-ecd1c02ca4156d4bfea10919` |
| `kai-p1005r1-h5-e-350k-c-nb-s1-98dd28-r2` | `rh-8497c0e1a9e5805c3957640f` |
| `kai-p1005r1-h5-e-350k-c-nb-s2-98dd28-r2` | `rh-ac54e6a0a218ff9c90aebb33` |

### Spend (R1 cap 144 GPU-h)

- **Spent so far.** RUN.md gives about 18 GPU-h. Only 5 of the 24 98dd28 pods are still listed
  (`kubectl get pods`, start to finish): ctl 2,335 s, h1-c-s1 2,322 s, h2-e-750k 2,322 s,
  qkv1-s2 2,822 s, and qkv1-s1 (Complete) 10,438 s. That is consistent with 23 × about 2,400 s +
  10,438 s ≈ 18.2 GPU-h, but it is not a full recount. The cap remaining is about 144 − 18 =
  **about 126 GPU-h**.
- **Bound at the old deadline.** 23 × (600 + 20,800 + 180) s = 496,340 s = 137.87 GPU-h, which is
  over 126.
- **Largest deadline that fits.** 23 × (780 + D) ≤ 126 × 3,600 = 453,600 s, so D ≤ 18,941 s.
- **Chosen: D = 18,000 s.** 23 × (600 + 18,000 + 180) = 23 × 18,780 = 431,940 s =
  **119.98 GPU-h**. The margin to 126 is 21,660 s = **6.02 GPU-h** (942 s per arm). It absorbs the
  uncertainty in the "about 18" already spent. The §3c unbounded terms (pull/init on a retried
  attempt, an init hang, disruption replacements) still count against the cap as they occur.
- **Per-arm need, 400 epochs (100 → 500).**
  - A07 at 30.85-38.8 s/epoch (gpu-benchmark VERIFY.md:109, n = 1 × 20 epochs; planning rate):
    12,340-15,520 s.
  - E: about 20.3 s/epoch wall, from the one complete R1 pod (qkv1-s1, (10,438 − about 300) / 500;
    n = 1; not quotable), so about 8,100 s.
  - The run_pack budget at D = 18,000 is about 18,000 − 300 (pre-arm) − 420 = 17,280 s. The A07
    margin at the pessimistic rate is about **1,760 s (10 %)**, before resume overhead (cache load,
    checkpoint restore, W&B reopen: minutes, unmeasured). That is up from 680 s in §3c.
- **Expected spend.** 19 E × about 8,500 s + 4 A07 × 12,700-15,900 s ≈ 212,000-225,000 s ≈
  **59-63 GPU-h**, so R1 lands at about 77-81 GPU-h of 144. Planning arithmetic, not a result.

### Jev (advisory; engineering record, not a verdict)

- `lab_check_protocol` on protocol-r1.json against snapshot 65e4331b: structurally valid,
  `drift: []`, `matches_snapshot: true` (protocol sha 2687a09e). r2 changes no protocol field.
- `jev_check_methods` on this section's method text (audit `jv-b0e55c9f…`):
  - selection: consistent (0.86).
  - authority: conflict (0.89, mandatory_review). The method text sent to Jev did not cite the
    approval. The approval is `local/2026-10-07-execution/r1b-relaunch-approval.json`, and launch
    still waits for the gate-cleared re-preparation.
  - provenance: conflict (0.46, mandatory_review). Low confidence, but it points at the real point
    below.
  - comparability: missing (0.53). Same point.
  - metrics: missing (0.66). Not applicable, since no metric is claimed here.

  **Comparability note, raised from these flags.** Replayed epochs are not bit-exact on GPU
  (`ablation.py:316-317`). ~~So the 23 r2 arms each carry one resume at epoch 100~~ (corrected
  2026-10-08: only 6 r2 arms resumed at epoch 100; 17 started at epoch 0; see the correction at the
  top of §3d and the per-arm table in §3e), and `h3-e-350k-c-qkv1-s1` ran uninterrupted. Inside H3,
  s1 and s2 differ in this respect. The R1 readout and VERIFY record each arm's true start epoch(s)
  (§3e table), not a blanket "resumed at epoch 100 (r2)". No row is excluded for it.

### Open before submission (Kai / orchestrator)

1. A gate-cleared re-preparation of the 23 under a dated approval reference: the r2 command plus
   `--gate-cleared … --approval-ref local/2026-10-07-execution/r1b-relaunch-approval.json`, with
   `--prepared-out PREPARED-cleared-r2.json` instead of `PREPARED-r2.json`. **Without
   `--prepared-out` it would abort.** The default cleared record name is the sorted keys cut to 80
   characters, and for these 23 keys that equals the existing 98dd28 file
   `PREPARED-cleared-r1-ctl-e-unc-c-s1-…-r1-h1-.json`, so `assert not target.exists()` fires. The
   cleared IDs differ from the table above only in the brief gate fields. The L4 byte rule applies as
   in §3c.
2. `PROGRAM.json` `pod_deadline_s` is 20,800. The r2 Jobs use 18,000. If the autopilot is ever to
   act on the r2 Jobs, PROGRAM.json needs Kai's edit. A manual launch under the approval above does
   not need it.

### 3d addendum (2026-10-07): split pod deadline, adopted by the orchestrator (review r2 B-r2-2 option)

The review found the A07 margin at 18,000 s overstated: about 300-1,340 s before resume overhead,
scaling the benchmark A07 rate by the observed 1.03-1.09x E slowdown. The four A07 arms include
the positive control A07-5000k-C, and a deadline hit there would stop the program. The 18,000 s
handoffs in `PREPARED-r2.json` are **superseded and not submitted**. The submitted build uses two
freeze runs of the same r2 command, with no tool change:
- 19 E arms: `--pod-deadline-s 12000 --manifests-dir manifests-98dd28-r2e --prepared-out PREPARED-cleared-r2e.json`.
  400 epochs at about 19.3-20.9 s/epoch is about 7,700-8,400 s, against about 11,280 s available.
- 4 A07 arms: `--pod-deadline-s 24000 --manifests-dir manifests-98dd28-r2a --prepared-out PREPARED-cleared-r2a.json`.
  400 epochs at 38.8 s/epoch is 15,520 s (x1.09 = 16,917 s), against about 23,280 s available.
- Worst case: 19 x (600 + 12,000 + 180) + 4 x (600 + 24,000 + 180) = 242,820 + 99,120 s =
  341,940 s = **94.98 GPU-h**, against about 126 remaining of 144.
Both builds are gate-cleared with `--approval-ref local/2026-10-07-execution/r1b-relaunch-approval.json`.
The L2 check is done against the 98dd28 job.json files: only the name, deadline, rss-gate
annotation, removed RSS lines and approval/gate/identity fields may differ.
~~Every r2 arm is marked "resumed at epoch 100 (r2)" in the readout and VERIFY.~~ Corrected
2026-10-08: each arm is marked with its observed start epoch(s) per the §3e table. H3 s1 ran
uninterrupted; s2 resumed at epoch 100 (review r2 item 6, C3).

## 3e. R1 relaunch r3: the 8 failed r2 arms (2026-10-08)

Authorization: Kai, 2026-10-08, relayed by the orchestrator ("fix and relaunch the 8 failed R1 r2
arms"; then "Yes do it" to the prepared r3 plan). Approval file (Kai's words):
`local/2026-10-08-execution/r3-relaunch-approval.json` (written 2026-10-08; replaces the planned name
`r1c-relaunch-approval.json`, which was never created). Diagnosis: `review/REGRESSION_TICKET_r2-resume.md`, option A. **Nothing in this
section has been submitted, and the PVC has not been touched.** The 8 handoffs carry
`scientific_gate: pending`.

**Unchanged.** Bundle `98dd2875…0059`: `manifests-98dd28-r3/` tarball, `configmap.json` and
`bundle-manifest.json` are byte-equal to `manifests-98dd28/`. ConfigMap `kai-pilot1005-code-98dd2875b7`, run_study
manifest `e6ff034b…`, configs, seeds, hyperparameters, stop epoch 500, `BNJ_STAGE=pilot-r1`,
`RUN_ROOT`, run dir names and W&B run ids are unchanged. So are RTX 3090, CPU 2 / 10 Gi / 16 Gi / 1 GPU,
grace 180 s, `backoffLimitPerIndex` 1, FailIndex on [5, 76, 124, 137, 143] and the memory gate off as in r2.
No science rule changes.

**What changes vs the submitted r2 Jobs** (`evidence/r3/jobjson-diff-summary.txt`, 8/8 against
`manifests-98dd28-r2e/`): Job name `-r3`, pod deadline 12,000 → 18,000 s (spec, annotation and the two
`ARM_BUDGET_S`/`ARM_DEADLINE` script lines), `hcc-chase-shor-c4715.unl.edu` appended to the hostname
NotIn list, and a new annotation `bnjettag.io/expected-start-epoch`. Brief: `purpose` only (states the
start epoch and the extra exclusion).

### Arms and expected start (PVC state from the ticket §1-§3, read 2026-10-08)

| Job | start | why | handoff (pending) |
| --- | --- | --- | --- |
| `kai-p1005r1-h1-e-350k-c-s2-98dd28-r3` | 0 | exit 76; partial dir moved aside | `rh-0f2fd13cf9427b9236c476ab` |
| `kai-p1005r1-h4-e-350k-c-w100-s2-98dd28-r3` | 0 | exit 76; partial dir moved aside | `rh-2d0a9fdae4332c70b6cb27bc` |
| `kai-p1005r1-h4-e-350k-c-w50-s1-98dd28-r3` | 0 | exit 76; partial dir moved aside | `rh-1c8ddb411cf35ce670f94f75` |
| `kai-p1005r1-h4-e-350k-c-w50-s2-98dd28-r3` | 0 | exit 76; partial dir moved aside | `rh-a4ba7df8ad109f7a5e4b8cf1` |
| `kai-p1005r1-h1-e-350k-noc-s2-98dd28-r3` | 400 | exit 124; `latest.json` epoch-0400 | `rh-a6f537637fadeb20f56b5603` |
| `kai-p1005r1-h2-e-500k-c-s1-98dd28-r3` | 475 | exit 124; `latest.json` epoch-0475 | `rh-6a47740fdd0c708b4b9487fe` |
| `kai-p1005r1-h3-e-450k-c-qkv1-s1-98dd28-r3` | 200 | node lost; `latest.json` epoch-0200 | `rh-cb35860084832f54b9a4bb2d` |
| `kai-p1005r1-h5-e-350k-c-nb-s1-98dd28-r3` | 175 | node lost; `latest.json` epoch-0175 | `rh-6f1b7f90bfdb334624c30aa3` |

`PREPARED-r3.json` sha256 `84b4ee89cf10235cfe778ed0bd9df74486f26416bdc81bcc9d2f6c052fe1a80c`
(per-arm `expected_start_epoch` in `options`). The start epochs come from the PVC read on
2026-10-08. The true start epoch is read from the r3 arm log's first `resume_epoch=` line after the
run; that observed value goes into the readout.

### PVC rename-aside (needs Kai; not run)

`evidence/r3/pvc-rename-aside-r3.sh`. It runs inside a CPU pod with `kai-data` mounted read-write and
renames `runs/pilot1005-<arm>` to `runs/pilot1005-<arm>.r2-partial-<UTC timestamp>` for the 4 exit-76
arms. Nothing is deleted. A dry run (no argument) only checks and prints; `--apply` renames. It refuses
everything if any dir has `latest.json`, `checkpoints/`, a final marker, more than 1 history row, or an
existing target. It was tested on a mock tree in scratch: dry run, apply, refusal and usage paths.
Order: rename (with no pod live for these arms), then submit the 4 fresh Jobs. The 4 resume arms are not touched.

### Builder change (freeze_p.py; no git at the lab root, so the record is a file with a SHA-256)

- `freeze_p.py`: `25de26c0…f338` → **`7af952c081aaef4728d278e2ede2f2e57013552de0c1065619e8ee04515c3a6e`**.
  Diff `evidence/r3/freeze_p-r3.diff` (`b55e7f0e…2065`); pre-edit copy `evidence/r3/freeze_p.pre-r3.py`.
- New opt-in flags, both empty by default:
  - `--exclude-node HOST` (repeatable): adds HOST to the GPU Jobs' NotIn list. The CPU gate and readout are unchanged.
  - `--expected-start TAG=EPOCH,…`: sets the brief purpose clause and the `expected-start-epoch` annotation,
    and records `expected_start_epoch` in `--prepared-out` options. It needs `--job-suffix`.
- **Defaults and r2 reproduce byte for byte** (`evidence/r3/defaults-check.log`). The r3 tool was run with
  scratch manifests and a scratch `--prepared-out` on four builds:
  - the §3c 98dd28 command: 26/26 handoff IDs and shas equal `PREPARED.json`, and all job.json files, the
    tarball, the configmap and the bundle-manifest are byte-equal. The briefs differ only in the gate fields,
    because the on-disk briefs are the later cleared ones.
  - r2 18,000 s: 23/23 entries and 49/49 files equal.
  - r2e cleared: 19/19 entries and 41/41 files equal.
  - r2a cleared: 4/4 entries and 11/11 files equal.
  No new `handoffs/` dir appeared, and every `PREPARED*.json` sha is unchanged.
- r3 command: `evidence/r3/freeze-r3-command.txt`, log `freeze-r3.log`.
- Gate-cleared command, **not run**: `evidence/r3/freeze-r3-cleared-command.txt`. It writes
  `--prepared-out PREPARED-cleared-r3.json`, which does not exist. The default cleared name would be
  `PREPARED-cleared-r1-h1-e-350k-c-s2-r1-h1-e-350k-noc-s2-…-r.json` and is avoided. It runs after the
  r3 review PASS and the approval file.

### Checks (offline)

- `run_handoff.py validate`: **8/8 VALID** (`evidence/r3/validate-r3.log`).
- `nrp_doctor.py lint`: **0 ERROR / 8 WARN**. The WARN is the deliberate `backoffLimitPerIndex=1`, as in
  §3c and §3d (`evidence/r3/lint-r3.log`).

### Deadline: 18,000 s (kept; checked)

All 8 arms are E arms. A fresh 500-epoch arm needs about 300 s setup + 500 × 22.35 s + about 90 s
for epoch 1 + about 20 s finalization ≈ 11,560 s. The rate and overheads are from the ticket §2, r2 arm
logs, n = 1 arm each, not quotable. Take the worst setup observed, 2,215 s on `hpc-nrp-g1.nmsu.edu`.
The run_pack budget is then 18,000 − 2,215 − 420 = 15,365 s. That leaves a margin of about 3,800 s.
It tolerates up to 30.0 s/epoch, 1.34 × the observed rate. The completed fresh r2 E arms ran
10,431-11,459 s container wall. The resume arms have margins of 7,700-14,400 s. The margin is not
thin, so the deadline is not raised (`evidence/r3/spend-r3.txt`).

### Spend (R1 cap 144 GPU-h)

- **r3 worst case:** 8 × (600 + 18,000 + 180) s = 150,240 s = **41.73 GPU-h**.
- **R1 worst total:** 53-56 GPU-h so far (ticket §6, INFERRED from pod objects and PVC mtimes) + 41.73 =
  **94.7-97.7 of 144**.
- **Not capped by the bound:** node-loss replacements (`DisruptionTarget` → Ignore). One full replacement
  per arm would add another 41.73, for 136.5-139.5.
- **Expected:** about 17.9 GPU-h at about 300 s setup, up to 22.2 if every pod sets up for 2,215 s.
  R1 then lands at about 71-78 GPU-h. This is planning arithmetic, not a result.
- **Unknown R1 first-launch term (review B-r3-1):** the 53-56 excludes the pre-arm pod failures of the 17
  R1 Jobs that never trained (ticket:99). INFERRED upper bound 17 × about 1.07 h ≈ 18 GPU-h, likely much
  less (most pods were Pending). Corrected R1 worst total: **about 95-116 of 144** before disruption
  replacements; with one full replacement per r3 arm, about 137-157, which can exceed the cap.
- **Recount rule:** if more than about 4 disruption replacements occur across the r3 Jobs, recount R1
  spend from pod objects before any further R1 launch.

### Readout marking (replaces §3d's blanket marking)

Each R1 arm carries its observed start epoch for every attempt that trained. Source: the first
`resume_epoch=` line per arm log.

| arm | attempts that trained (start epoch) |
| --- | --- |
| `h3-e-350k-c-qkv1-s1` | R1 0, uninterrupted |
| `ctl-e-unc-c-s1`, `h1-e-350k-c-s1`, `h2-e-750k-c-s1`, `h3-e-350k-c-qkv1-s2` | R1 0, r2 100 |
| `h3-e-450k-c-qkv1-s1` | R1 0, r2 100 (two pods), r3 200 (expected) |
| `h5-e-350k-c-nb-s1` | R1 0, r2 100 (two pods), r3 175 (expected) |
| `h1-e-350k-noc-s2` | r2 0, r3 400 (expected). r2 trajectory 400-413 abandoned; `val_AUC=0.500000` at epochs 412-413 is recorded in the r2 arm log `r1/logs/pilot1005-h1-e-350k-noc-s2-…-98dd28-r2-0.log` (the record) and in a copy-aside of the run dir taken before submission (`<run dir>.r2-snapshot-<UTC>`, Kai approval 2026-10-08) (review B-r3-2) |
| `h2-e-500k-c-s1` | r2 0, r3 475 (expected) |
| `h1-e-350k-c-s2`, `h4-e-350k-c-w100-s2`, `h4-e-350k-c-w50-s1`, `h4-e-350k-c-w50-s2` | r3 0 (expected; the r2 1-epoch attempt is moved aside and not part of the run) |
| the other 11 (`h1-e-350k-noc-s1`, 4 × `h2-a07-*`, `h2-e-1m/250k/2m/5m-c-s1`, `h4-e-350k-c-w100-s1`, `h5-e-350k-c-nb-s2`) | r2 0, uninterrupted |

The "expected" entries are replaced by the observed r3 values after the run. GPU replay is not
bit-exact, so the resumed arms are not byte-reproducible; no row is excluded for that.

### Residual risks and open items

1. **A fresh arm can hit exit 76 again.** If a node is lost before that arm's first checkpoint at epoch
   25 (about 9-10 min of training), the arm exits 76 again: the guard sees a history with no checkpoint.
   The c4715 exclusion lowers this risk but does not remove it. The code fix is ticket option B (new bundle).
2. **W&B.** For the 4 fresh arms, the stage-keyed run id reopens the W&B run that holds the
   r2 step 1, and the r3 step 1 is dropped as non-monotonic. Arms h3-450k and h5-nb-s1 replay from 200/175
   over W&B steps that already exist. The PVC files are authoritative; W&B is a monitor only.
3. **`h1-e-350k-noc-s2` showed `val_AUC=0.500000` at epochs 412-413** (ticket §2, log lines, not a
   result). Resuming at 400 follows Kai's list. Whether the collapse counts as the arm's outcome under the STUDY
   rules is still open (ticket open item 3).
4. **`PROGRAM.json` `pod_deadline_s` is 20,800**, as in §3d item 2. A manual launch under Kai's approval
   does not need it.

### Jev (advisory; engineering record, not a verdict)

- `lab_check_protocol` on protocol-r1.json against snapshot 65e4331b: structurally valid, `drift: []`,
  `matches_snapshot: true` (protocol sha 2687a09e). r3 changes no protocol field.
- `jev_check_methods` on this section's method summary (audit `jv-53dbc57662d04c69ba17270c2710ad6e`):
  - authority: conflict (0.59, mandatory_review). This is correct: the dated approval file does not
    exist yet (see above).
  - selection: missing (0.69); comparability: missing (0.71); provenance: missing (0.49). These map to the
    mixed start epochs, handled by the readout-marking table.
  - metrics: missing (0.28). Not applicable; no metric is claimed.
  - uncertainty: not_applicable (0.51).


## 4. Where I am not sure

> **Superseded by §3c (bundle 98dd2875; arbiter v3 S2, 2026-10-06).** P2, P7, P11 and the
> open-before-launch list below describe b3fb22/1f7c4e (23 GPU Jobs, w150, no pod deadline, 8 h
> readout). The live build is §3c: 24 GPU Jobs, w100 (K1), pod deadline 20,800 s, readout
> deadline 43,200 s. Launch conditions are in `review/STUDY_arbiter_v3.md` (L1, S1-S3, L4).

```
P1 DECISION: 0041 changes the training path (run_engram.validate_cfg) to admit NB. It was not in the
   orchestrator's list, and NB could not run without it.
   ALTERNATIVES: return 0036 to its owner for the fix (delays NB; R1 runs 21 arms).
   CONFIDENCE: HIGH that the fix is needed. MEDIUM that nothing else on run_study.train's NB path
   is missing (the runner-path test covers builder, observer, PID and 3 epochs; it does not cover
   run_study.train itself, which needs a GPU).   FLAG FOR HUMAN: YES (dev owner should review 0041)
P2 DECISION: no activeDeadlineSeconds on the 23 GPU Jobs (STUDY §11 says cluster-ops sets it to the
   per-pod basis). activeDeadlineSeconds counts from Job start, including queue time (1.5–2.5 h
   measured for 3090s), so 6 h could kill a healthy A07 arm (500 × 30.85 s ≈ 4.3 h at K=1).
   ALTERNATIVES: set 6 h here; set about 9 h.   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES (cluster-ops)
P3 DECISION: 10 Gi host memory, 2 CPU per single-arm pod.   ALTERNATIVES: 8 Gi (the brief's figure; it
   leaves no room above the 8,192 MiB RSS gate, so the kernel OOM-kills before the gate fires).
   CONFIDENCE: MEDIUM (RSS measured only to 21 epochs at K=1)   FLAG FOR HUMAN: NO
P4 DECISION: E at one arm per RTX 3090 is assumed to clear the 40 % utilization floor. Unmeasured;
   A07 K=1 is 61.6 / 74.3 %, and E is about half the parameters.   CONFIDENCE: LOW
   FLAG FOR HUMAN: YES (the 30-min utilization check decides; repacking needs a new handoff)
P5 DECISION: readout.json top level adds threshold_c and labels_sha256 (PROGRAM.json integrity reads
   them); the brief listed only round, bundle_sha256, n_arms, complete.   CONFIDENCE: HIGH
   FLAG FOR HUMAN: NO
P6 DECISION: status 'failed' also covers internal readout inconsistencies (runner vs recomputed
   selection, a26 checkpoint mismatch, missing a26 entropy). STUDY §5 lists only the five statuses.
   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
P7 DECISION: H4 warmups 50 and 150 (STUDY D3) [superseded: w100 since K1, patch 0043, §3c]. A w150 arm has 350 epochs to reach the budget before
   the pause, squeezing late in the first cosine cycle, so feasible_any false there is time-limited
   (STUDY §6 treats it as inconclusive).   CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES (already in STUDY)
P8 DECISION: A07 at 350k (headroom 6,947, 2.0 %) is generated and launched as STUDY lists it.
   ALTERNATIVES: drop it (a near-certain degenerate rung).   CONFIDENCE: HIGH that it is in the
   design; it is flagged, not removed.   FLAG FOR HUMAN: NO
P9 The NB and H3 floors (171,526 and 269,830) come from dev's structural traces. cpu_gate.py re-traces
   them in the pod, and the local result is in §2a. The H3 floor of 1 bit is an effective-f clamp on KIF,
   not jsc150's KBI bc=Min(1) (dev flag F3).   FLAG FOR HUMAN: YES (dev F3)
P10 The readout's certification runs on CPU. certify_ebops.py says to run it on the training GPU class:
   a rounding difference at a power-of-two boundary could move one integer bit (the option-(c) readout
   made the same choice). A cert_fail on one arm would stop the autopilot.   CONFIDENCE: MEDIUM
   FLAG FOR HUMAN: NO
P11 Readout wall time for 23 arms on CPU (a26 + certification on the 558,000-row split) is not measured.
   The 8 h deadline is a guess from the 8-arm readout-c (4 h deadline).   CONFIDENCE: LOW   FLAG: NO
```

Open before any launch:
1. Review: critical-reviewer on this PREFLIGHT, and a review of 0036/0037/0041.
2. Kai's signature on PROGRAM.json.
3. Cluster-ops' launch half (P2).
4. Presence of the fingerprint ConfigMap.
5. The CPU gate's `GATE_RESULT PASS` (whose output lands under the new program root).

## Files

`plan-build.md`, `build_tree.py`, `freeze_p.py`, `patches/` (+ `PATCHES.json`, `superseded-19arm/`),
`code/tree/`, `manifests/`, `handoffs/rh-*` (25), `PREPARED.json`, `lint.log`, `evidence/`,
`superseded-1f7c4e/`.
