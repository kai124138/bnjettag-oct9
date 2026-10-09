(a) CPU gate kai-pilot1005-cpugate-b3fb22: PASS (launch conditions L1-L3). (b) R1, 23 GPU pilots + readout, after GATE_RESULT PASS: ITERATE (A1-A3).

# PREFLIGHT critical review v1: pilot program R1, bundle b3fb22c8, 2026-10-05

Reviewer: critical-reviewer, solo (06-review §6.2, PREFLIGHT tier). Scope: launch readiness of the
CPU gate (`handoffs/rh-305a7de984052719d93f30c6`), the 23 R1 GPU Jobs and the R1 readout
(`rh-3ae4fd83…`), plus STUDY.md's pre-registration as it bears on R1. Everything was checked
read-only. Nothing was submitted and no campaign file other than this one was written. Local runs
went into a scratch rebuild of the tree (`<scratchpad>/crv1/tree`), not `code/tree`. Every local
number is a home-PC engineering check, and none of them is quotable.

## Checks run (reproduced, not taken from the campaign logs)

| check | result |
| --- | --- |
| sha256 of the 10 patches vs `patches/PATCHES.json` | all 10 equal. 0032/0033 are byte-equal to `2026-10-02-chang-option-c/patches/` (`f475c69e…`, `23536dfe…`). 0036/0037 are byte-equal to `dev/patches/` (`9edd3a6c…`, `0b469b52…`) |
| `build_tree.py --out <scratch>/crv1/tree` (42abed payload → PATCHES.json order) | `TREE_MATCHES` |
| tarball `manifests/pilot1005-code.tar.gz` | sha256 `b3fb22c8…23fb`, 293,484 B, 391 files. Every file is byte-equal to `code/tree`, no tree file is missing from the tar, and all 391 match `bundle-manifest.json` |
| `configmap.json` and the `source-configmap.json` of all 25 handoffs | payload sha256 `b3fb22c8…` in all of them; name `kai-pilot1005-code-b3fb22c825` |
| PREPARED.json vs files | 25/25: `job_json_sha256` and `record_sha256` match the files, the rh- ID is the record-sha prefix, and job names match. `manifests/<key>-job.json` differs from the handoff `job.json` only by the run_handoff init container, run-id label, handoff annotations and volume (diffed for cpugate) |
| `tools/run_handoff.py validate` (validate_dir is read-only, run_handoff.py:268-276) | 25/25 `VALID` |
| `nrp-lab/nrp_doctor.py lint` on 6 job.json (cpugate, readout, w150-s1, a07-350k, nb-s1, noc-s1), live node map | all `OK`, notes only. The RTX 3090 pool is now **47** nodes (PREFLIGHT.md:109 says 48). GPU Jobs: "no activeDeadlineSeconds … fine if deliberate" (see A2) |
| 0034 | test-only: one env key in `tests/test_run_pack.py` `setup()` (`BNJ_CAMPAIGN_DIR=str(tmp)`), the fix in REGRESSION_TICKET.md |
| 0041 | one condition in `run_engram.validate_cfg` (patch lines 11-16). `binary_absmean` behaviour is unchanged. `run_study.py:103` calls `validate_cfg`, so without it NB would have failed at start (PREFLIGHT.md:42-45 is correct) |
| 0036/0037 on A/A07 | code read: NB code paths are gated on `is_nb(cfg)` / `kbiw`. The floor is gated on `attn_bit_floor(cfg)`, which returns None when the key is absent (`floor_at` passes confs through). Evidence: `dev/evidence/a_unchanged_combined.log` SAME for A-s1, A-s3, A07-350-s1, C′, E1, F; `a_unchanged_0037.log` SAME for A-s1, A07-350-s1, C′, R (see B3) |
| 23 configs vs STUDY.md:78-89 and PROGRAM.json `r1_launch` | flattened diff of every config against A350-C at the same seed (A07 rungs against A07-350k). Each arm differs only in its registered column: noC drops `pid_input`/`pid_traced_integral`/`campaign.amendment`; H2 changes `target_ebops`; H4 changes `pid.warmup` 50/150; NB changes `quant.weight` to `kbi_learnable`; H3 adds `attn_bit_floor {1, [q,k,v]}` and its `zero_floor_ebops` 269,830. s1 vs s2 differ only in seed and `order_seed`. Arch, budget, (c), warmup and seed match the PREFLIGHT table (PREFLIGHT.md:173-195) row by row |
| 23 GPU Jobs (script over every job.json) | one arm per pod (pack `[[index]]`, completions = parallelism = 1); affinity `NVIDIA-GeForce-RTX-3090`; NotIn includes `hcc-nrp-shor-c6017.unl.edu` and both `KNOWN_BAD_NODES` (nrp_doctor.py:40-43) plus 2 historical nodes; `single-arm-justified` annotation present; fingerprint gate `--expect 11559681` with `FINGERPRINT_GATE_FAIL` exit; `BNJ_RSS_GATE_LIMIT_MB=8192` window 5:105; `run_pack.py "$PACKS" 500`; `BNJ_STAGE=pilot-r1`; `automountServiceAccountToken: false`; every container on `python@sha256:4d1caded…`; bundle and manifest sha asserted; monitor only on (c) arms; each script references only its own `r1/runs/<name>`; 23 distinct names. No `activeDeadlineSeconds` (A2) |
| output paths | No file outside this campaign (and `superseded-1f7c4e/`, never launched) references `pilot-program-20261005`. The cpugate and readout use `test ! -e "$OUT"` |
| threshold (c) | recomputed from the counts at training-batch PREFLIGHT.md:519: n 62,000, p_maj 0.20288709677419356, SE 0.0016150697714716518, threshold **0.2109624456315518**. Equals gate_check.py:41 and readout_pilot.py:54 |
| arithmetic in STUDY/PREFLIGHT | headrooms E 78,474 / 178,474 / 328,474 / 578,474 / 828,474 / 1,828,474 / 4,828,474; A07 6,947 / 156,947 / 656,947 / 1,656,947 / 4,656,947; H3 80,170. C-s1 entropy mean 0.739877. 500 × 30.85 s = 4.28 h. 23 × 6 h = 138. All match |
| citations | gpu-benchmark VERIFY.md:109 (RTX 3090 klow A07 K=1: s/epoch 30.85, util 61.6/74.3, peak 8,484/24,576 MiB, 0.623 cores) and :141 (host RSS peak 2,413 MB). Header at VERIFY.md:96 and :128 |
| **local, final tree** (home PC, TF 2.21/hgq2 0.1.9, gate exports; not quotable) | `pytest --collect-only` **166**. Full suite **164 passed, 2 skipped** (both `analysis/test_attn_entropy.py:142`), 576 s, `gate_check.py pytest` **PASS**. `pair_nb.py` NB_PAIRED_OK seeds 1-8 (15 kernels each), `gate_check nb-pairing` **PASS**. `cpu_gate.py` **PREFLIGHT_ALL_PASS 23 production 0 pilot_only 23**; PAIRED_INIT_OK A07 s1 (5), E s1 (12), E s2 (6); floors re-traced 171,526 / 343,053 / 269,830; warmup 50/150 give first feedback at 60/160 with span 10; `gate_check cpu-gate` **PASS** |
| a26 on H3, NB, A models (synthetic, matching_initialization → save → `load_checkpoint` → `analyze` + `zero_bit_fractions`) | all three load, names match, entropy finite, zero-bit status `defined` |
| readout certification path | **fails**: see A1 |

Jev `jev_check_claims` (audit `jv-d8887a0d26aa49e0b102073701795646`, advisory):

| claim | Jev | checked by hand |
| --- | --- | --- |
| c1: validate_cfg rejected every weight type except binary_absmean | overstated (0.54) | supported (patch lines 11-16; `run_study.py:103` calls it) |
| c2: dev/README.md:55-57, A unchanged for 9 configs | overstated (0.76) | **overstated** (B3) |
| c3: VERIFY.md:109 utilization/peak/cores | supported (0.82) | supported |
| c4: VERIFY.md:141 RSS 2,413 MB | supported (0.43) | supported (column "host RSS peak, MB", VERIFY.md:128) |

A fifth claim (threshold, training-batch PREFLIGHT.md:519) was refused by Jev because the line
exceeds its excerpt limit. It was recomputed above instead.

## (a) CPU gate: PASS

The gate script (rh-305a… job.json) is fail-fast:
- An `EXIT` trap prints `GATE_RESULT FAIL exit=… line=…` unless a result was already printed.
- `gate_fail` prints its reason and exits 1.
- The header failures (sha256sum -c, pip, manifest sha) exit nonzero under `set -e`.
- `GATE_RESULT PASS` is printed only after all four `gate_check.py` modes pass.

`gate_check.py pytest` requires all of the following:
- 0 failures and 0 suite errors;
- exit 0;
- exactly 2 skips, both at `analysis/test_attn_entropy.py:142`;
- exactly 166 collected;
- every test passed in the 10 REQUIRED files (gate_check.py:32-38, 57-91).

`nb-pairing` requires NB_PAIRED_OK for seeds 1-8 and `NB_PAIRING_ALL_OK 8` (gate_check.py:110-117).
pair_nb.py exits 1 on any mismatch (pair_nb.py:62-64).

Resources: CPU 8 / 24 GiB, requests equal limits, ephemeral 12 GiB, `CUDA_VISIBLE_DEVICES=-1`,
`WANDB_MODE=disabled`, deadline 14,400 s, backoff 0, token automount off. Writes go only to the new
`cpu-gate-b3fb22-r1` and the run_handoff record. Locally, every mode except `threshold` (it needs
the cache) passes on the rebuilt tree.

Launch conditions:
- **L1.** The submitted record is the `--gate-cleared` re-preparation (a new rh- ID). Diff its
  `record.json` against `rh-305a…/record.json`. Only `brief.scientific_gate`, `brief.approval_ref`
  and the identity fields derived from them may differ. Bundle `b3fb22c8…`, manifest `e6ff034b…`,
  image digest, script, resources and OUT must be byte-equal.
- **L2.** `--approval-ref` cites a dated, saved Kai authorization. decisions.md 2026-10-05 10:08
  item 1 ("new sha, PREFLIGHT and CPU gate rerun") qualifies once this review is cited.
- **L3.** This PASS covers bundle b3fb22c8 only. Fix A1 by a manifest change to the readout
  handoff (option 1 below), which keeps the bundle. If A1 or any other finding is instead fixed in
  code, the bundle changes and the gate must run again under a new name and output path.

## (b) R1 after GATE_RESULT PASS: ITERATE

### A1. The readout's certification step cannot import; every non-degenerate arm becomes `cert_fail`

`campaigns/pilot1005/certify_ebops.py:120` runs `from evaluate_roc import targets`. The import is
unconditional, at the top of `main()`. The only `evaluate_roc.py` in the tree is
`campaigns/chang0926/evaluate_roc.py`. The script puts only its own directory and the tree root on
`sys.path` (lines 44-45), and the readout Job exports `PYTHONPATH=/work/code` (readout job.json
script).

Reproduced on the rebuilt tree with the Job's PYTHONPATH:
`ModuleNotFoundError: No module named 'evaluate_roc'`, exit 1. With
`PYTHONPATH=/work/code:/work/code/campaigns/chang0926` it runs (`CERTIFICATION_ALL_PASS 0 0` on an
empty run root).

The consequences follow from the code:
- The readout sets CERT=1 and `certify-snapshot-0500.json` is never written.
- `readout_pilot.py:182` makes `cert_ok` false for every arm whose `nondegenerate_best` is true, so
  that arm gets status `cert_fail` (line 199-200).
- Every row is then not `healthy`, the integrity rule "status ≠ complete count == 0" fails, and the
  program stops (STUDY §10).
- Worse, the arms that look most promising are exactly the ones lost.

The file is byte-identical to `chang1002c/certify_ebops.py`, so option (c)'s readout had the same
defect. It was never run. `tests/test_certify.py` imports `evaluate_roc` from chang0926, so the
suite cannot catch it.

Fix, either:
1. Manifest only, keeping b3fb22: in the readout handoff, set
   `PYTHONPATH=/work/code:/work/code/campaigns/chang0926`. Pilot1005 stays first on `sys.path`.
2. Code: import `targets` only in terminal mode, or copy it. This needs a new bundle and a gate
   rerun.

Either way, add a CPU dry run of the whole readout script before R1 launches. Run a26, certify,
monitor_p and readout_pilot on 1-2 synthetic run directories, or on a 3-epoch CPU run of an NB, H3
and noC config with `stop_after`. The pieces are unit-tested, but the chain is not.

### A2. Nothing bounds R1 spend

- None of the 23 GPU Jobs has `activeDeadlineSeconds`, at Job or pod level (job.json spec;
  PREFLIGHT.md:252-255, P2; lint note).
- `backoffLimitPerIndex: 2` allows 3 pod attempts per arm (freeze_p.py:378).
- The R1 cap is 138 GPU-h = 23 × 6 h exactly (STUDY.md:197; PROGRAM.json `caps`), with no slack for
  retries, pip, the fingerprint gate or traced epochs. The benchmark's total elapsed per run-epoch
  for A07 K=1 is 38.8 s (VERIFY.md:109), so 500 × 38.8 s = 5.4 h.
- STUDY.md:203-204 says running pods "end by their Job deadline … set by cluster-ops", and the
  autopilot that would enforce caps is not built (JOURNAL.md:11).

As prepared, a stalled or crash-looping arm can run up to 3 × its run time, and no mechanism stops
it. freeze_p.py has no deadline option for GPU Jobs. Setting one therefore changes the manifests and
the handoff IDs, so the diff needs a re-review.

Fix: set a pod-level `activeDeadlineSeconds` in the template. It counts from pod start, not Job
creation, which removes P2's queue-time concern. Make deadline-exceeded and the RSS-gate exit
terminal for the index (a `podFailurePolicy` FailIndex rule), or show that
deadline × (backoffLimitPerIndex + 1) × 23 ≤ 138 GPU-h. Record the arithmetic in PREFLIGHT §3.

### A3. The design the 23 pods implement has not passed its STUDY gate

- STUDY.md:5 reads "draft … not reviewed, not frozen". 06-review §6.2 requires the STUDY panel
  (physics + critical + constructive → arbiter) before downstream phases.
- `lab_freeze_protocol` has not run (PREFLIGHT.md:111).
- PROGRAM.json still has `signed_by_kai: false`, `mode: dry-run`, `bundle_sha` as a PLACEHOLDER,
  and placeholder handoffs and job names in the `gate` and `r1_launch` steps.
- PREFLIGHT's "Open before any launch" (PREFLIGHT.md:285-290) lists Kai's signature but not the
  STUDY panel.

R1 must not launch until the STUDY panel passes (or Kai records a waiver in decisions.md), the
protocol snapshot is frozen and re-checked with `baseline_path`, and PROGRAM.json is filled with
the cleared rh- IDs and signed. This review does not substitute for the panel. The STUDY findings
below (B4-B6) are inputs to it.

### B (fix before PASS)

- **B1. PROGRAM.json integrity reads a field the readout does not write.**
  `definitions.integrity[2]` compares `bundle_sha` with `$program.bundle_sha`, but readout.json's
  top level is `bundle_sha256` (readout_pilot.py:250; PREFLIGHT.md:212). Depending on the
  autopilot's handling, this fails closed or errors every round. Rename one of them.
- **B2. PREFLIGHT §2a is empty.** PREFLIGHT.md:113-115 says "(filled below when the runs finish)",
  and lines 102, 104, 105 and 106 point to it. The session ended at about 10:55 (JOURNAL.md:25), so
  the final-tree full pytest, cpu_gate on the 23 configs and NB pairing at seeds 1-8 have no
  evidence in the campaign. `PYTEST_TOTAL = 166` (gate_check.py:32) is described as "measured
  locally at freeze", with no log. This review's local runs (table above) supply engineering
  evidence: 166 collected, 164 passed / 2 skipped, cpu_gate 23 PASS, NB pairing 8/8. The owner
  should rerun them, put the logs in `evidence/` and fill §2a.
- **B3. dev/README.md:53-57 overstates the A-unchanged evidence.** It claims SAME for A-s1, A-s2,
  A-s3, A07-350-s1, C′-s1, C-s1, E1-s1, F-s1 and R-s1, for "0036 alone, 0037 alone and combined".
  - There is no 0036-alone log.
  - The combined log has 6 configs (A-s1, A-s3, A07-350-s1, C′, E1, F).
  - A-s2 and C-s1 appear in no log, and A-s2 is an R1 seed.
  - Jev: overstated, 0.76.

  The identity for A/A07 is still supported, by the combined log and by local PAIRED_INIT_OK across
  arms. Correct the text, or rerun `check_a_unchanged.py` on the final tree with A-s2 and C-s1
  added (a few minutes of CPU).
- **B4 (STUDY). The entropy cut is calibrated only on A07.** The definition of healthy requires
  `attn_entropy_norm_mean < 0.95` (STUDY.md:112-118). The only working reference is A07 (4 heads;
  mean 0.739877). E has one block and 2 heads (a26 probe: one `bit_block_0`), and no healthy E
  reference exists. If a working E model sits at ≥ 0.95, every E rung is unhealthy. The program
  then stops at §7.1, and H2 reads "refuted (E unhealthy at 5M)" (STUDY.md:130) for a reason that
  is not the hypothesis. Pre-data, either measure a26 on an existing high-budget or unconstrained E
  checkpoint, or pre-register that E5M-C with feasible, non-degenerate and entropy ≥ 0.95 means
  "entropy cut invalid: stop for Kai", not "H2 refuted". D1 already flags the cut. This is the
  concrete failure mode.
- **B5 (STUDY). The H4 w150 arm is likely time-limited and confounded.** Locally, cpu_gate puts the
  first feedback at epoch 160, which leaves 340 epochs to epoch 500. b5 first met (a) 259-389 epochs
  after the start (STUDY.md:86). The squeeze also falls where the first cosine cycle's LR is
  smallest, so timing and LR phase are confounded. STUDY.md:132 pre-registers `feasible_any` false
  as inconclusive, which is honest, but about half of H4's 4 pods may yield no read. Kai should
  decide w150 vs w100 (D3) before data. It costs nothing now.
- **B6 (STUDY). The H2 prediction is undefined if E recovers only at 5M.** E 5M headroom 4,828,474
  is greater than A07 5M headroom 4,656,947, so no A07 rung qualifies (STUDY.md:55 lists only up to
  "2M→5M"). Add the case, e.g. "beyond the ladder → inconclusive".

### C

- **C1.** All 23 configs carry `campaign.production: true` while `index.json` says
  `production: false`. Nothing on the training path reads it, but VERIFY tooling may.
- **C2.** Arm ids differ: STUDY.md:82-83 has "E250-C … E5M-C" and "A07-350-C … A07-5M-C", while
  PROGRAM.json, index `program_arm` and readout `arm` have "E250k-C", "E1000k-C" and "A07-350k-C".
  Align them before the autopilot matches on names.
- **C3.** PREFLIGHT.md:109: the live RTX 3090 pool is 47 nodes today, not 48.
- **C4.** The pre-amendment STUDY text is kept "in scratch only" (STUDY.md:21). Keep a dated copy in
  the campaign for the audit trail.
- **C5.** NB starts with higher EBOPs than A (local synthetic init 12,848,059 vs 9,429,139 at s1,
  not quotable; dev/README.md:64-70), so its early PID phase differs. Note this in the H5 read.
- **C6.** The gate still re-traces only the 0-bit floor (cpu_gate.py:156-164). This carries over
  option-(c) review B1 and is honestly stated (PREFLIGHT.md:76-84).

## Carried from the option-(c) PREFLIGHT review v1

- B1 (floor coverage): still zero-bit only → C6.
- B2 (pytest strictness): **resolved**, gate_check.py:57-91.
- B3 (pod-3 duration): moot, single-arm pods.
- B4 (amendment gates): the threshold recheck is now gate step 1. The rest is superseded by the
  program.
- B5 (product): **resolved**, RTX 3090 by Kai (decisions.md 2026-10-05 10:08 item 2).
- C1 (pairing exit 0 on UNPAIRED): **resolved** for NB, pair_nb.py:62-64.
- C6 (PREPARED-cleared overwrite): **resolved**, per-key file (freeze_p.py:538).

## Answers to 06-review §6.3

1. Conventions: validation-only selection, no ROC-test read. a26 reads `x_val` only
   (attn_entropy.py:8-10). certify traces the train split (certify_ebops.py:155-161). The readout
   reads run files only. Yes.
2. Reference table: STUDY §1-2 cites b5/READOUT. Pilots are directional by rule (STUDY.md:14-15).
3. What a competing group would have: an entropy reference for E (B4), and a time-to-budget
   argument for w150 (B5).
4. Resolving power: 2 seeds can only separate 2/2 from 0/2, and STUDY §6 says so. Honest.
