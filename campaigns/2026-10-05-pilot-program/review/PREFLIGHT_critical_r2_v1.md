verdict_r2: PASS (submit the 23 r2 Jobs), conditional on L1-L3 below. B-r2-1 and B-r2-2 are text-only fixes to PREFLIGHT.md §3d and change no launched byte. They are checked by grep before submission.

# PREFLIGHT critical review, R1 relaunch r2, v1 (2026-10-07)

Reviewer: critical-reviewer, solo (06-review §6.2, PREFLIGHT tier). Scope: PREFLIGHT.md §3d, RUN.md
"Incident 2026-10-06", evidence/r2/*, manifests-98dd28-r2/, PREPARED-r2.json, the 23 handoffs.
Authorization: `local/2026-10-07-execution/r1b-relaunch-approval.json` and decisions.md
2026-10-07 07:29. The approval covers the relaunch with `BNJ_RSS_GATE_LIMIT_MB` unset and new Job
names. It excludes the readout and any change to code or configs. Nothing was submitted or edited
except this file and the review-reports entry. Every number below is an engineering figure and is
not quotable.

## 1. freeze_p.py defaults reproduce 98dd28; the new flags are opt-in. Confirmed

- sha256: `freeze_p.py` = 25de26c0…f338 and `evidence/r2/freeze_p.pre-r2.py` = b5975961…1a62. A
  fresh `diff -u` of the two equals `evidence/r2/freeze_p-r2.diff` (87a2e3ab…a6c) apart from the
  headers.
- The new code sits behind `R2 = {'rss_gate': True, 'job_suffix': ''}` (freeze_p.py:87). The RSS
  export line (:326-327), the RSS_GATE_FAIL exit-5 line (:418-420), the annotation (:592-593) and
  the Job name (:740) all reduce to the old text at the defaults. `OPTS['rss_gate'/'job_suffix']`
  is set only when a flag is passed (:669-672). `--prepared-out` returns before the old PREPARED
  paths (:811-822), so the default branch is unchanged.
- Reproduced independently. The defaults-check log holds only the freeze output and no comparison,
  so I made the comparison.
  - The scratch rebuild `scratchpad/defaults-check/` has 55 files. Against `manifests-98dd28/`:
    all 26 job.json files, the tarball, configmap.json and bundle-manifest.json are byte-equal (30
    files equal).
  - The 25 briefs differ only in `approval_ref` and `scientific_gate`. The frozen dir holds the
    gate-cleared briefs from the 2026-10-06 launch, so this is expected.
  - `scratchpad/PREPARED-defaults-check.json` equals PREPARED.json on bundle, manifest and all 26
    `{job, handoff, record_sha256, job_json_sha256}`. Its options are identical
    (`bounded, diag, pod_deadline_s 20800, readout_deadline_s 43200, readout_pythonpath`).

## 2. Job.json diffs, 23 r2 vs 98dd28. Confirmed

My own flattened diff of all 23 files, script lines compared with the arm tag normalized:

- 4 non-script fields, each in 23/23 files:
  - `/metadata/name`;
  - `/metadata/annotations/bnjettag.io/active-deadline`;
  - `/metadata/annotations/bnjettag.io/rss-gate`;
  - `/spec/template/spec/activeDeadlineSeconds` (20800 → 18000).
- 6 script-line changes, each in 23/23 files:
  - the `ARM_BUDGET_S` line and the `ARM_DEADLINE` echo line, 20800 → 18000;
  - `export BNJ_RSS_GATE_LIMIT_MB=8192 BNJ_RSS_GATE_WINDOW=5:105` removed;
  - the `RSS_GATE_FAIL.json` → exit 5 line removed.
- Nothing else differs. No script contains `RSS_GATE` or `-r2`. This matches
  `evidence/r2/jobjson-diff-vs-98dd28.txt`.
- Exclusion: `manifests-98dd28-r2/` has 23 r1 jobs. The only missing 98dd28 key is
  `r1-h3-e-350k-c-qkv1-s1`. PREPARED-r2.json has 23 jobs and no qkv1-s1.
- Bundle files: tarball, configmap.json and bundle-manifest.json are byte-equal to
  `manifests-98dd28/`. The tarball sha256 is 98dd2875b7c9…0059.
- PREPARED-r2.json (1682f712…3004) has status `offline_prepared_not_submitted` and gate `pending`.
  For each of the 23 entries, `record_sha256` and `job_json_sha256` match the files in
  `handoffs/rh-*`, and the handoff IDs match the §3d table (23/23).
- A handoff job.json differs from its manifest only by the standard run_handoff wrapping:
  run-id label, handoff annotations, init container and handoff volume.
- source-configmap.json is byte-equal to the 98dd28 cleared handoff (checked on 2 arms). The
  records differ from the 98dd28 cleared records only in `job` and `brief`. `data_info_sha256` is
  equal.
- Job names are 34-41 characters, under the 52-character cap.

## 3. Resume path, traced in code/tree. Confirmed

- **Tree equals bundle.** I extracted `manifests-98dd28-r2/pilot1005-code.tar.gz`. `run_pack.py`,
  `run_study.py`, `bnhgq2/ablation.py` and `bnhgq2/wandb_util.py` are byte-equal to `code/tree/`.
- **run_pack guard.** It skips an arm only on `DIVERGED.json` or `VERIFIED_COMPLETE.json`
  (run_pack.py:184-187). No other marker is read.
- **run_study guards.**
  - `mkdir(exist_ok=True)` (:108).
  - Exit 3 only on `DIVERGED.json` (:109-112).
  - `source_manifest.json` must equal `manifest()` (:119-120). The bundle and manifest e6ff034b are
    unchanged, and the Job script re-asserts MSHA.
  - It returns early only on `VERIFIED_COMPLETE.json` (:127-130). That file is written only when
    `completed_epochs == train.epochs` (:192-193), and all 24 configs have `epochs` 7000.
  - `run.lock` is flock LOCK_NB (:115-116). The 98dd28 holders have been dead for more than 16 h.
- **Checkpoint generations.**
  - All 24 configs have `checkpoint_every_epochs` 25 and `snapshot_every_epochs` 500. Of these, 22
    are `pid_input traced_only` and 2 are noc. The 23 relaunched arms are 21 option-(c) and 2 noc.
  - `save_checkpoint` writes `latest.json` (ablation.py:261) and keeps 2 generations (:263-264).
  - In the epoch loop, the checkpoint is saved at :1173-1174 and the gate step runs at :1186-1187.
    The gate reached `len(rss) == end = 105` at zero-based epoch 104, after the epoch-100 commit.
  - The 4 recovered tails show `checkpoint=epoch-0050/0075/0100`, last line `[epoch 104/7000]`,
    then `RSS_GATE … FAIL`, `ARM_EXIT … 5` and `POD_EXIT_FINAL … exit=5`.
- **Restore.**
  - `restore_checkpoint` asserts the config, data and code sha (:300-302), then restores the model,
    the optimizer and SELECTED_FILES (:303-315).
  - It drops snapshots after epoch 100 (:318-320); none exist.
  - It truncates `activation_widths.jsonl` and asserts 100 rows (:321-324). It truncates
    `pid_telemetry.jsonl` the same way when `pid_traced_only` (:326-328, :676-684).
  - Rows for epochs 0-104 were appended (:1148-1153) before the gate fired, so 105 → 100 holds.
  - `run_training` takes the resume branch (:909-911), and the loop runs from epoch index 100
    (:972). `--stop-after 500` pauses with a checkpoint and the epoch-500 snapshot (:1170-1179,
    :1198-1202).
- **Markers.**
  - `RSS_GATE_FAIL.json` is written at ablation.py:877. No `.py` in the tree reads it, apart from
    tests.
  - The only reader was the 98dd28 Job-script line, which r2 removes. After a failure, a stale file
    can no longer relabel it as exit 5.
- **W&B.** `stage_run_id` = sha256(`pilot-r1\0<name>`)[:12] (wandb_util.py:82-86), with
  `resume='allow'` (ablation.py:957-961), so the same run is reused. The note on steps 101-104 in
  §3d.6 is correct.
- Jev `jev_check_claims` (audit jv-33cdb666…, advisory): c1 run_pack skip supported 0.91; c2
  truncation supported 0.80; c3 gate unset supported 0.99; c4 gate after checkpoint supported 0.61
  ("review"; checked by hand above); c5 "OOM is final with 137" **absent 0.80**, which agrees with
  B-r2-1.

## 4. Gate off: 10 Gi is the backstop, and an OOM is final, but not necessarily as 137 (B-r2-1)

`rss_gate_from_env` returns None when the variable is unset (ablation.py:847-849). §3d.7 says "an
OOM kill gives 137". That holds only if the kernel kills the whole container: cgroup-v2
`memory.oom.group`, which is the kubelet default from 1.28 on.

If only the largest process is killed (the arm child), run_pack sees a nonzero exit. That exit is
neither 3, nor 5, nor a pod stall, so run_pack retries the arm in the pod up to `BNJ_ARM_RETRIES`.
The default is 2, and the script does not set it (run_pack.py:39, :237-242). Each retry resumes from
the newest 25-epoch checkpoint. After the retries, run_pack exits 1 (:263). The script's
`exit "$RP"` then goes through `pod_exit` with `ARM_PHASE=train` and exits 76.

Both 137 and 76 are FailIndex, so the arm is final either way and the spend stays inside the
deadline. The record should state both paths, because a 76 after `ARM_FAILED_AFTER_RETRIES` must
not be read as a code failure.

Headroom, from the 4 tails:
- `POD_MEM current_mib` already peaks at 8,450-9,006 of 10,240 at epoch ≤104, while the arm RSS is
  about 2.6-2.8 GB.
- When qkv1-s2's arm exited, current fell 8,953 → 7,322 with `pressure_full_avg10 0.0`. So about
  6-7 GiB of the cgroup charge is not arm RSS, most likely reclaimable page cache. /work is a
  disk-backed emptyDir with no `medium: Memory`.
- The §3d.7 anonymous-memory estimate (≤ about 3.7 GB at epoch 500) is therefore plausible. The
  record should still say that its "well under 10 Gi" covers RSS and not memory.current (C1).
- The 4 A07 arms have no recovered log, so their RSS is unknown. The `RSS_GATE_FAIL.json` files on
  the PVC hold every arm's slope and baseline if anyone wants them.

## 5. Spend. Arithmetic correct; the ~18 GPU-h is an estimate

- 23 × (600 + 18,000 + 180) = 431,940 s = 119.98 GPU-h.
- 126 × 3,600 = 453,600 s. The margin is 21,660 s = 6.02 GPU-h. The ceiling is D ≤ 453,600/23 −
  780 = 18,941 s.
- The estimate of about 18 GPU-h already spent is not a recount. RUN.md gives 23 × ~0.65 h +
  ~2.9 h ≈ 17.9 h. §3d uses 5 still-listed pods (2,335 / 2,322 / 2,322 / 2,822 / 10,438 s), and
  23 × 2,400 + 10,438 = 65,638 s = 18.23 GPU-h.
- The script-level `elapsed_s` in the 4 tails is 2,317-2,766 s. It excludes image pull before T0,
  so the pod times are slightly larger, as expected.
- The 6.02 GPU-h margin covers about 33 % error on the estimate of 18. Retried-attempt pull and
  init, hangs and disruption replacements count against the cap as they occur (B-new-2, v2).
- Only R1 pods count. JOURNAL shows no other GPU job in this campaign.

## 6. Comparability. The instruction is enough for leads-only R1, if it binds the readout (C3)

- The resume restores the model, optimizer, PID and selection state, and the data order is
  per-epoch seeded (ablation.py:988).
- The only difference from an uninterrupted run is a fresh non-bit-exact GPU realization of epochs
  101-104 and later, the same class of variation as any two GPU runs. It adds no systematic bias of
  a known sign.
- Marking each row "resumed at epoch 100 (r2)" and noting the H3 s1 (uninterrupted) / s2
  (resumed) asymmetry is enough for leads-only reads.
- The instruction is now only in PREFLIGHT §3d. It should also be in STUDY or the readout spec
  before the readout is prepared (C3).

## Earlier findings by name (PREFLIGHT critical v2)

- A3 (STUDY not passed): **resolved**. STUDY arbiter v3 PASS (review/STUDY_arbiter_v3.md:1).
- B-new-1 (PREFLIGHT did not describe the frozen set): **resolved**. §3c exists (PREFLIGHT.md:368).
- B-new-2 (bound omits terms): **resolved**. §3c, and §3d repeats that the unbounded terms count
  against the cap.
- B-new-3 (w150 in STUDY): **resolved**. "w150" now appears only in K1 history and reason strings
  (protocol-r1.json:246, 272).
- C1 v2 (A07 margin): revisited below as B-r2-2.

## New findings

### A: none.

### B (text only, PREFLIGHT.md §3d; no launched byte changes)

- **B-r2-1.** §3d.7 says "an OOM kill gives 137". Replace it with both paths: whole-container OOM
  gives 137, and a single-process OOM gives up to 2 in-pod resumes, then 76 (run_pack.py:39,
  :237-242, :263). Both are FailIndex and final.
- **B-r2-2. The A07 margin of 1,760 s (10 %) is overstated.** It applies the benchmark rate
  (38.8 s/epoch, gpu-benchmark VERIFY.md:109, n = 1 × 20 epochs) unadjusted. On the same product,
  the benchmark E rate is 18.0 / 18.8 s/epoch (VERIFY.md:106, 108). The 4 recovered R1 E tails
  average 19.3-19.7 s/epoch over epochs ≈31-104 (n = 73-75 epoch lines each). That is 1.03-1.09×
  the benchmark.
  - At that ratio, A07 needs 39.8-42.5 s/epoch × 400 = 15,940-16,980 s against the run_pack budget
    of about 17,280 s. The margin is 300-1,340 s before resume overhead (cache load, restore, W&B
    reopen, pause verification).
  - If it runs out, an A07 arm ends at 124, final, before the epoch-500 snapshot. The cap still
    holds, but the H2 A07 rows need another approved relaunch. The checkpoints every 25 epochs keep
    the progress.
  - Fix: state this margin. Optionally, propose to Kai a split deadline for a later re-preparation.
    For example, 19 E arms at D = 12,000 (need about 8,000-8,500 s) and 4 A07 arms at D ≥ 24,000
    gives 19 × 12,780 + 4 × 24,780 = 341,940 s = 95.0 GPU-h, inside 126. That would be new
    manifests and needs a re-review. It is not required for this PASS.

### C

- **C1.** §3d.7: say that the 3,684 MB is RSS, and that the cgroup `memory.current` already sits at
  8.3-9.0 GiB, mostly reclaimable (falls to 7.3 GiB when the arm exits; pressure 0.0).
- **C2.** The decisions.md Check is "relaunched pods log a resume from epoch 100". The pod log will
  not show this. `[train] … resume_epoch=100` (ablation.py:937) and `[epoch 101/7000]` go to the
  arm log on the PVC (`<RUN_ROOT>/logs/<name>-<HOSTNAME>.log`, run_pack.py:73-78). run_pack tails
  that log into the pod log only on failure. Verify with the arm log, or W&B steps from 105 on.
  - Also: the cluster-inventory 2026-10-06 Check ("gate horizon equals the stop epoch before any
    relaunch") is superseded by Kai's gate-off decision. Note that there.
- **C3.** Add the comparability marking (each arm "resumed at epoch 100 (r2)"; H3 s1 vs s2) to
  STUDY or the readout spec as a pre-data note, so the readout does not depend on PREFLIGHT.
- **C4.** `evidence/r2/defaults-check-98dd28.log` records the freeze output but not the byte
  comparison. Append the comparison command and result. I reproduced it in §1.
- **C5.** PROGRAM.json `pod_deadline_s` 20,800 ≠ 18,000. This is fine for a manual launch (§3d open
  item 2). Fix it before any autopilot use.

## Tools run (read-only)

- `python3 tools/run_handoff.py validate` on rh-c5c82dd0 (ctl), rh-8f58f76b (A07 5m) and rh-3069fd9e
  (qkv1-s2): all VALID, exit 0. evidence/r2/validate-r2.log: 23 VALID.
- `python3 nrp-lab/nrp_doctor.py lint` on rh-8f58f76b and rh-ac54e6a0 job.json: exit 1, WARN only
  (`backoffLimitPerIndex=1`, deliberate). evidence/r2/lint-r2.log: 23 WARN, 0 ERROR.

## Launch conditions

- **L1.** B-r2-1 and B-r2-2 land in PREFLIGHT §3d (text), checked by grep.
- **L2.** Submit only from a `--gate-cleared` re-preparation with
  `--approval-ref local/2026-10-07-execution/r1b-relaunch-approval.json` and
  `--prepared-out PREPARED-cleared-r2.json`. Under the L4 byte rule each cleared `job.json`/`record.json`
  may differ from PREPARED-r2.json only in `brief.approval_ref`, `brief.scientific_gate` and the
  derived handoff identity. Bundle 98dd2875, manifest e6ff034b, image, script (D = 18,000, no RSS
  lines), resources and podFailurePolicy must be byte-equal.
- **L3.** Exactly the 23 keys. No `r1-h3-e-350k-c-qkv1-s1`, and no readout.

## 06-review §6.3

1. Conventions: unchanged from the 98dd28 freeze, which passed review. The only change is an env
   removal approved by Kai.
2. Reference/rigour: no numbers are produced at PREFLIGHT.
3. A competitor would have resume-equivalence evidence for this code. Here it is argued from code,
   not tested on GPU. The code argument is complete, and the PREFLIGHT tier needs nothing more.
4. Uncertainties: the spend margin and the A07 time margin are stated with their bases (B-r2-2).
5. Limitations: the 19 unrecoverable logs and the uninspected PVC are stated in §3d.
6. Context: N/A at PREFLIGHT.
