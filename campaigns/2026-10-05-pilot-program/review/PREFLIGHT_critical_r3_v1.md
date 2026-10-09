verdict_r3: PASS (submit the 8 r3 Jobs), conditional on L1-L6 below. No A finding. B-r3-1 and B-r3-2 are text fixes that change no launched byte. B-r3-3 is a read-only pre-submit check.

# PREFLIGHT critical review, R1 relaunch r3, v1 (2026-10-08)

Scope: PREFLIGHT.md §3d (corrected) and §3e, RUN.md (corrections, r2 incident, r3 section), JOURNAL tail,
`review/REGRESSION_TICKET_r2-resume.md`, `evidence/r3/*`, `PREPARED-r3.json`, `manifests-98dd28-r3/`,
`freeze_p.py`, and `code/tree` (`bnhgq2/ablation.py`, `run_study.py`, `campaigns/pilot1005/readout_pilot.py`).
Nothing here is quotable: these are engineering checks, with no seeds and no intervals. I did not touch the
cluster or the PVC, and I edited no file except this one. The rebuilds ran in a scratch mirror of the campaign:
`tools/` and the two referenced campaigns were symlinked, `handoffs/` started empty, and the real `handoffs/`,
manifests and `PREPARED*.json` were not written.

## L1. Bundle, code and science unchanged; job.json diffs limited. Confirmed (independently)

- **Bundle.** sha256 of `pilot1005-code.tar.gz` is `98dd2875b7c9…0059`, and it is identical in `manifests-98dd28/`,
  `-r2e/` and `-r3/`. `configmap.json` is 369f9de3… and `bundle-manifest.json` is 4b23d5ef…, also identical in all
  three. `freeze_p.py:723` asserts the rebuilt bundle against `--expect-bundle 98dd2875`, and the rebuild from
  `code/tree` passed that assert in my mirror runs, so the tree reproduces the frozen bundle. No file under `code/`
  (excluding `__pycache__`) is newer than 2026-10-06 06:00.
- **Science.** STUDY.md sha256 is 89f96cb6… (= [A5], JOURNAL row 06:30). PROGRAM.json is cca098b1… (= F7, JOURNAL
  row 19:32). `lab_check_protocol` on protocol-r1.json against snapshot 65e4331b returned `structural_valid: true`,
  `drift: []`, `matches_snapshot: true` (protocol 2687a09e). Configs, seeds and the stop epoch sit inside the
  byte-equal bundle.
- **job.json, r3 vs submitted r2e, 8/8.** I ran my own structured diff (scratch `jd.py`). It is the same for all 8:
  - `metadata.name` `-r2` → `-r3`;
  - `activeDeadlineSeconds` 12000 → 18000;
  - the `active-deadline` annotation, where only the number changes (`a.replace('12000','18000') == b` is True);
  - new annotation `bnjettag.io/expected-start-epoch`;
  - NotIn `values[4]` gains `hcc-chase-shor-c4715.unl.edu`;
  - script: exactly the two `ARM_BUDGET_S` / `ARM_DEADLINE` lines.

  Labels, image, resources, env, volumes, podFailurePolicy (Ignore DisruptionTarget; FailJob 10; FailIndex
  [5, 76, 124, 137, 143]) and backoff are identical. Against the original 98dd28 job.json, the only further
  differences are the r2 rss-gate changes: the annotation reads `off`, the export line is removed and the
  `RSS_GATE_FAIL.json` line is removed. This matches `evidence/r3/jobjson-diff-summary.txt`.
- **Briefs vs the r2 pending briefs, 8/8.** Only `purpose` differs, and its start-epoch text is correct per arm.
  `stop_rules` are identical to r2, so stop rule 3 already shows 18000.

## L2. Defaults byte-identical. Confirmed by rerun

I reran three builds in the scratch mirror with `freeze_p.py` 7af952c0:
- **§3c 98dd28 command (20,800 s), scratch `--prepared-out`.**
  - 26/26 `jobs` entries equal `PREPARED.json`.
  - 30 of 55 manifest files are byte-equal: 26 job.json, tarball, configmap, bundle-manifest, and one brief.
  - The other 25 briefs differ only in `approval_ref` and `scientific_gate`. The on-disk briefs are the later
    cleared ones, which is the explanation `defaults-check.log:2` gives.
- **r2e (12,000 s, 19 arms).** All 19 job.json files plus the 3 bundle files are byte-equal to `manifests-98dd28-r2e/`.
- **r3 command (`evidence/r3/freeze-r3-command.txt`).** All 19 files are byte-equal to `manifests-98dd28-r3/`. The
  8 handoff dirs are byte-identical to the campaign's (`diff -r`). `PREPARED-r3.json` equals my record except for
  `manifests_dir`. Its sha256 is 84b4ee89… as stated in §3e:776.

I read `freeze_p-r3.diff` (b55e7f0e…, matches §3e:793). Both new flags default to empty. `affinity()` appends
`more_bad` only when it is given. The annotation and options keys are added only for tags in `expected_start`.
`--expected-start` asserts that the epoch is a multiple of 25, below 500, and that `--job-suffix` is set.

## L3. The 8 keys, the arms and the start epochs. Confirmed

- **Keys.** `PREPARED-r3.json` `jobs` has exactly 8 keys. They are the 8 failed r2 arms in RUN.md:83-85:

  | arm | `expected_start_epoch` | ticket evidence |
  | --- | --- | --- |
  | h1-e-350k-c-s2 | 0 | ticket §1 |
  | h4-e-350k-c-w100-s2 | 0 | ticket §1 |
  | h4-e-350k-c-w50-s1 | 0 | ticket §1 |
  | h4-e-350k-c-w50-s2 | 0 | ticket §1 |
  | h1-e-350k-noc-s2 | 400 | ticket:50 |
  | h2-e-500k-c-s1 | 475 | ticket:50 |
  | h3-e-450k-c-qkv1-s1 | 200 | ticket:64-65 |
  | h5-e-350k-c-nb-s1 | 175 | ticket:64-65 |

- **Code.** `run_training` (ablation.py:909-914) calls `restore_checkpoint`. That function returns None iff
  `latest.json` is absent (:293-297). If it returns None, an existing `activation_widths.jsonl` or `PID_TELEMETRY`
  raises `History exists without a committed checkpoint`.
  - **Fresh arms.** After the rename, the dir does not exist. `run_study.py:108` recreates it empty, so initialization
    runs (start 0). Without the rename the arm exits 76 again (L5 order).
  - **Resume arms.** `latest.json` names the checkpoint. The sha asserts (:300-302) hold because the config, data
    and code are unchanged; the ticket:65 code_sha256 is e6ff034b, the run_study manifest. History is truncated to
    `epoch < completed_epochs` and must have exactly that many rows (:321-324). The ticket row counts (≥ checkpoint
    epoch) satisfy this:

    | arm | history rows | checkpoint epoch |
    | --- | --- | --- |
    | noc-s2 | 413 | 400 |
    | h2-500k | 499 | 475 |
    | h3-450k | 201 | 200 |
    | h5-nb | 197 | 175 |

    `pid_telemetry` is truncated the same way (:676-684) for option-(c) arms. noc-s2 has no telemetry.
  - **Lock.** The `run.lock` flock (`run_study.py:115-116`) is `LOCK_NB` on a file that may be stale. A stale file is
    harmless. A live holder is not (see B-r3-3).
- **Jev.** `jev_check_claims` (audit jv-df96cc8aa26e4207887742d0dd25bb1a), advisory:

  | claim | source | disposition |
  | --- | --- | --- |
  | c1: 400 / 475 | ticket:44-53 | supported 1.00 |
  | c2: 200 / 175 | ticket:63-65 | supported 0.80 |
  | c4: exit-76 dir state | ticket:28-32 | supported 0.95 |
  | c3: "53-56 GPU-h includes all R1 first-launch spend" | ticket:97-100 | supported 0.69, disposition **review** |

  I checked c3 by hand. It is **overstated**: ticket:99 says "plus an unknown". See B-r3-1.

## L4. Deadline and spend. Deadline adequate; spend arithmetic correct but omits a term (B-r3-1)

- **Deadline.** A fresh arm needs 500 × 22.35 s + about 20 s finalization ≈ 11,195 s of arm time. The rate is from
  the h2-e-500k r2 arm log (ticket:51, n = 1 arm, 499 epochs; the epoch-1 89 s is already in the mean, so the extra
  +90 s in §3e:821 is conservative). At the worst observed setup of 2,215 s (ticket:47, nmsu), the run_pack budget
  is 18,000 − 2,215 − 420 = 15,365 s (recomputed), which leaves about 4,100 s of margin. Fresh r2 E arms completed
  at 10,431-11,459 s container wall (ticket:55). The resume arms need 25-325 epochs. **Adequate.**
- **Spend.** The arithmetic is correct:
  - 8 × (600 + 18,000 + 180) = 150,240 s = 41.73 GPU-h (recomputed: 41.733).
  - 53-56 + 41.73 = 94.73-97.73.
  - With one full disruption replacement per arm, the total is 136.5-139.5.

  B-r3-1 below covers the term this omits.

## L5. Rename-aside script. Non-destructive and correctly scoped

`evidence/r3/pvc-rename-aside-r3.sh` (sha f268e62f…):
- **Scope.** `ARMS` hard-codes exactly the 4 exit-76 arms. No resume arm is named.
- **Two passes.** A check pass runs over all 4 dirs before any `mv`, and any failure aborts everything
  (`CHECKS_FAILED: nothing renamed`).
- **Refusals.** It refuses a dir that has `latest.json`, `checkpoints/`, `VERIFIED_COMPLETE.json`, `DIVERGED.json`,
  more than 1 `activation_widths` row, or an existing target. It skips with a failure if the dir is missing.
- **The move.** `mv -n` is no-clobber. The result is verified (`test ! -e src && test -d dst`). One UTC timestamp is
  used for all 4. Nothing is deleted. Dry run is the default.
- **Readout.** The renamed dirs (`pilot1005-<arm>.r2-partial-<ts>`) cannot leak into it. `readout_pilot.py:231`
  selects rows from `index.json` by name, and no code under `code/tree` globs `runs/`.
- **Minor (C).** The pod precondition grep covers only these 4 arms, not the 4 resume arms (see B-r3-3). `wc -l`
  counts newlines, so a missing file gives 0 rows and the dir is renamed. That is acceptable, because
  `pid_telemetry` alone would also trip exit 76.

## L6. Readout provenance and document consistency. Mostly consistent (B-r3-2)

- **Marking table.** The §3e marking table (PREFLIGHT:844-853) covers 1 + 4 + 1 + 1 + 1 + 1 + 4 + 11 = 24 arms. It
  matches ticket §4 (4 resumed at 100: ctl, h1-c-s1, h2-750k, qkv1-s2; 11 fresh) and ticket §3 (two r2 pods each
  for h3-450k and h5-nb-s1). "Expected" r3 entries are to be replaced by the observed first `resume_epoch=` line
  (§3e:777-779, :855).
- **Corrections in place.** The §3d banner (:502-508), the struck blanket marking (:701-705, :737-739), and the RUN.md
  corrections (:27-32, :56-60, :72, :85) all agree with the ticket.
- **Earlier findings by name.** B-r2-1 (OOM both paths) is in §3d.7 (:577-580). B-r2-2 (A07 margin) was resolved by
  the split-deadline addendum (:721-739). The r2 review §3 confirmed the resume path from code only. The premise
  failed for 17 of the 23 arms because the PVC was not inspected. §3e now takes its start epochs from the PVC read
  (ticket), which closes that gap.
- **Minor (C).** RUN.md:89 says a relaunch is "a new PREFLIGHT with a new code sha". r3 keeps the code sha; only the
  builder `freeze_p.py` changed. RUN.md:87 still says restoration was "not observed" for the completed arms, but the
  ticket has since observed it. Both are wording only.

## Findings

### A: none.

### B

- **B-r3-1. The R1 worst total omits the unknown R1 first-launch term (text; PREFLIGHT §3e:832-835, RUN.md:97, spend-r3.txt:3).**
  - **The gap.** "53-56" is r2 (45-48) plus 7.7 for the 7 R1 arms that trained. Ticket:99 explicitly excludes "an
    unknown … for 34 pre-arm pod failures on the 17 other Jobs".
  - **Bound.** Those Jobs started 21:49-21:53Z and failed by 22:53:12Z (ticket:19), with parallelism 1. The INFERRED
    upper bound is therefore 17 × about 1.07 h ≈ 18 GPU-h. It is likely much less, since most pods were Pending
    (RUN.md:16).
  - **Corrected worst total.** About 95-116 of 144 before disruption replacements. With one full replacement per r3
    arm it is about 137-157, which can exceed the hard cap.
  - **Fix.** Restate the bound with this term. Add: if more than about 4 disruption replacements occur across the
    r3 Jobs, recount spend before any further R1 launch. This does not block launch, because the expected case
    (about 18-22 GPU-h) is far inside the cap.
- **B-r3-2. The noc-s2 abandoned trajectory must be carried into the readout record (text; §3e marking table / risk 3).**
  - **What is lost.** The resume at 400 truncates `activation_widths.jsonl` rows 400-412 on the PVC. Those are the
    only per-epoch file records of the `val_AUC=0.500000` at epochs 412-413.
  - **Why it matters.** E at 350k without (c) collapsing is exactly the H1 outcome (STUDY:122). Replay is not
    bit-exact ([A5]), so the r3 trajectory may not repeat the collapse.
  - **Where the record survives.** The r2 arm log `r1/logs/pilot1005-h1-e-350k-noc-s2-…-98dd28-r2-0.log` keeps the
    epoch lines.
  - **Fix.** In the marking-table row for noc-s2, state "r2 trajectory 0-413 abandoned; val_AUC 0.5 at 412-413 in the
    r2 arm log" and name that log as the record. Optionally, if Kai approves a PVC write, copy (not move) the
    history aside before submission.
  - Whether 0.5 already appears at or before epoch 400 is not known from the ticket. If it does, the checkpoint is
    already collapsed. That is a cheap read of the same log and belongs in the disposition (ticket open item 3).
    This does not block: the resume follows the code's standard semantics and Kai's list.
- **B-r3-3. Pre-submit liveness check for all 8 run dirs (read-only; not in the plan).**
  - **The hazard.** The first r2 pods were lost on c4715 with stale `Init:ContainerStatusUnknown` status (ticket:34,
    :64). That includes the second pods of the two resume arms h3-450k and h5-nb-s1. If any such container were
    still alive on a partitioned node, an r3 pod would share the run dir. The result would be a `LOCK_NB` failure
    (exit 76) or two writers.
  - **Current evidence.** The ticket saw no writes after about 01:45Z 2026-10-07.
  - **Fix.** Just before submission, run
    `kubectl get pods -n cms-ml -o wide | grep -E 'kai-p1005r1-(<8 arms>)-98dd28-r2'`, which must show no
    Running/Unknown pod with a live container. Also run the inspect-pod `find runs/pilot1005-<8 arms> -newermt
    '2026-10-07 02:00Z'`, which must return nothing (excluding r3).

### C

- C1. The annotation and the stop-rules text still say "RSS gate (5)" with the gate off. This is inherited from r2
  and harmless, because exit 5 stays in FailIndex.
- C2. The pending gate `approval_ref` in `PREPARED-r3.json` still carries the 2026-10-05 text ("PROGRAM.json not
  yet signed"). The cleared re-preparation replaces it.
- C3. RUN.md:87 and :89 wording (L6).
- C4. The spend-r3 "need" double-counts the 300 s setup inside the 2,215 s case. This is conservative, and the
  margins are understated by about 300 s.

## Risks (do not block)

1. **A fresh arm loses its node before epoch 25** (about 9-10 min of training) and exits 76 again. This is ticket
   option B territory. The c4715 exclusion lowers the risk; it does not remove it. If it happens, the remedy is the
   same rename-aside plus a new suffix, not a code edit (RULES §5).
2. **noc-s2 collapse** (B-r3-2). It is an outcome question for STUDY, not a launch blocker.
3. **W&B step clashes** for the 4 fresh arms (step 1) and for the h3/h5 replays. The PVC files are authoritative.
4. **PROGRAM.json `pod_deadline_s` 20,800 ≠ 18,000.** This matters only if the autopilot is to act on r3.

## Tools run (read-only on the lab)

- Structured job.json and brief diffs (scratch `jd.py`).
- Scratch-mirror reruns of the r3, §3c and r2e builds.
- `sha256sum`, `diff -r`, `cmp`.
- `lab_check_protocol`.
- `jev_check_claims` (jv-df96cc8a…).

## Launch conditions

- **L1.** Kai's dated approval file `local/2026-10-08-execution/r1c-relaunch-approval.json` exists. It does not
  exist yet (checked).
- **L2.** B-r3-1 and B-r3-2 land in PREFLIGHT §3e as text, checked by grep. No launched byte changes.
- **L3.** The rename script is run by Kai or under his explicit approval. The dry run must print 4 `PLAN` lines and
  `DRY_RUN_OK`; then `--apply` prints `RENAME_ASIDE_DONE`. This happens **before** the 4 fresh Jobs are submitted.
  The 4 resume Jobs may go independently.
- **L4.** The B-r3-3 liveness check is clean for all 8 arms.
- **L5.** Run the gate-cleared re-preparation with exactly `evidence/r3/freeze-r3-cleared-command.txt`, with this
  file as the review reference. It writes `PREPARED-cleared-r3.json`, which does not exist yet. The L4 byte rule
  applies: against `manifests-98dd28-r3/`, only the brief gate and approval fields and the handoff IDs may differ,
  and all job.json files must be byte-equal.
- **L6.** After the run, replace each "expected" start epoch with the first `resume_epoch=` line of its r3 arm log.

## 06-review §6.3

1. Every number above is recomputed or cited to file:line.
2. No quotable result is claimed.
3. Spend and margins are stated with their bases.
4. The Jev dispositions are quoted, and one is overridden by hand (c3).
