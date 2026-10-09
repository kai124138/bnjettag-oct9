## 2026-09-28 16:01 PDT — critical-reviewer PREFLIGHT review: 2026-09-26-training-batch (gate v4, SCOPED to the gate v3 fixes; Kai 2026-09-28 "A10 only, launch once the fixes pass a quick check")
VERDICT: PASS. Both v3 Category A findings are fixed and verified by number. The fingerprint gate, exit-10 path, K=3 OOM fallback and readout-b partial handling are implemented as described. The bundle is unchanged at 42abed4b. Three B items are procedural text, not code or manifests. Cluster-ops must copy them into RUN.md with the A2 rule, before `kubectl apply` (B1) or before the fallback or readout is used (B2, B3).

Checked:
- PREFLIGHT.md at aaf42f2. That commit landed during this review and added 8 lines at l. 1079-1092 (cluster-ops record: fingerprint ConfigMap created and read back, live lint of the 10 Jobs). Lines before 1079 are unchanged.
  - "PREFLIGHT gate v3 fixes": l. 754-1095.
  - Superseded-text notes: l. 564-591, 1383-1391 and 1453-1458.
- review/PREFLIGHT_critical_v3.md and review/PREFLIGHT_validators_v4.txt.
- STUDY.md: change log l. 378, l. 1578-1592 and l. 1736-1748.
- decisions.md, top two entries.
- All 10 Job JSONs, parsed.
- configmap-fp-e9511d1a.json; fingerprint/fingerprint_check.py (all 125 lines); rss_rule_epoch10_20.awk; freeze.py l. 570-640.
- code/tree: run_pack.py l. 55-95, 175-195 and 255-267; ablation.py l. 393-410, 610-625, 700-715 and 905-950.
- code/evidence: fingerprint_cpu_42abed4b.log, wrapper_gate_v3_test.log and the four dry_readout_*gatev3* logs.
- Delta REGRESSION_TICKET.md §1 and §8, and Delta RUN.md l. 325-360.

**Read-only breach, disclosed and undone.**
- I ran `python3 manifests/freeze.py --help`. freeze.py has no argument parser, so any argv without `--jobs-only` runs the full freeze. It rewrote `manifests/bundle-manifest.json` and `bundle-manifest-42abed4b.json`: their `jobs` field gained the fp ConfigMap and the six fallback Jobs.
- I restored both with `git checkout --`. `git status --short` of the campaign is now empty.
- By-product: the full freeze also rewrote the tarball, `configmap.json`, `configmap-42abed4b.json`, the 10 Jobs, `readout-a-job.json` and `cache-job.json`. All came back byte-identical (git clean). So a full re-freeze reproduces 42abed4b, not only `--jobs-only`.

Recomputed (CPU, file-level or synthetic; nothing here is a result):
- **Bundle.** `shasum -a 256 manifests/chang0926-code.tar.gz` gives 42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0.
  - `freeze.py --jobs-only` on a scratch copy of the campaign printed `BUNDLE_SHA256 42abed4b… (unchanged, not rewritten)` and `MANIFEST_SHA256 041f981a…`.
  - It asserts `on_disk == rebuilt == BUNDLE_42` (freeze.py `jobs_only`).
  - The shasums of every `manifests/*.json` and `fingerprint/*` were identical before and after the run (`JOBS_ONLY_IDEMPOTENT`).
- **Fingerprint sha chain.** These four all give e9511d1aeb39c7c8e48cc7dbc148ac623f3b2d9844d108da38f1ecfa2bdff1f1:
  - `git show 2d86bc9:campaigns/2026-09-26-delta/code/fingerprint_check.py`;
  - `manifests/fingerprint/fingerprint_check.py`;
  - the decoded `data['fingerprint_check.py']` of `configmap-fp-e9511d1a.json` (`immutable: True`);
  - the `sha256sum -c` literal in each of the 8 GPU scripts.
- **A2 awk**, on synthetic logs:
  - rss10 2000, rss20 2145 → `OK projection_mib 3378` (2145 + 145/10 × 85 = 3,377.5), exit 0.
  - A second `==== ARM_ATTEMPT` followed by a 90 MiB/epoch series → `STOP rss10 3000 rss20 3900 projection_mib 11550` (3900 + 900/10 × 85 = 11,550), exit 1. The count was reset by the header.

### The seven items, by name

1. **A1: RESOLVED.** Parsed from each JSON:
   - All 8 GPU Jobs (k5, k3, fb48, fb16, fb32, fb16-32, fb48-16, fb48-32) have exactly two required expressions: `nvidia.com/gpu.product In ['NVIDIA-A10']` and `kubernetes.io/hostname NotIn [hcc-nrp-shor-c6017.unl.edu, k8s-chase-ci-07.calit2.optiputer.net, nautilus-ext-gpu01.fullerton.edu, ren-gp-argo-01.madren.org]`.
   - `preferredDuringScheduling…` is None in all 8.
   - `nrp_doctor.py` `KNOWN_BAD_NODES` = {nautilus-ext-gpu01.fullerton.edu}, which is in the list.
   - readout-b5 and readout-b3 carry the same NotIn list.
   - Lint gives "required pool = 1 products / 35 nodes" for each.
2. **A2: RESOLVED.**
   - Formula: PREFLIGHT l. 853 and STUDY l. 1741-1748 match the v3 fix. 105 − 20 = 85, so for a linear leak the projection equals rss(105). It stops at a slope of about (6,144 − 2,150)/105 ≈ 38 MiB/epoch, which meets the in-code gate's upper coverage of about 40 MiB/epoch without a gap.
   - Reader: `host_rss_mb` is `VmRSS/1024`, which is MiB (`ablation.py:614-619`), printed on the `[epoch` line (`:940-941`). The N-th `[epoch` line after the last `==== ARM_ATTEMPT` (written by `run_pack.py:77`) is process epoch N, which is the in-code window's count.
   - Log path: `$RUN-$POD.log` matches `run_pack.py:75` (`HOSTNAME` = pod name). `ARM_STARTED` `$3` is the run name (`:79`). `POD_MEM … rss_mib` exists for the fallback read (`:151-152`).
   - Timing: 10 × 150 s = 25 min. Commands and the Job-not-pod stop action are stated (l. 862-885).
3. **Fingerprint gate: RESOLVED as specified.**
   - In all 8 GPU scripts, `FP=0` is initialised before `python … || FP=$?`, so a pass does not trip the `[ "$FP" != 0 ]` test.
   - The order is MANIFEST_SHA_OK → GPU_GATE_PASS → READY.json → sha check → fingerprint → run_pack (string index checked in all 8).
   - `--run chang0926-a-n64-s1 --expect 11559681` appears once per script. The CPU log shows `FINGERPRINT 11559681 expected 11559681`, a mismatch exits 9 and no GPU exits 8.
   - The wrapper test log ends `WRAP_TESTS_ALL_PASS`. Its cases: fp mismatch → exit 9 with run_pack not called; 5/5 epoch-0 divergences → exit 10; 4/5 → 0; 5/5 at epoch 3 → 0; tampered /cmfp → FAILED with run_pack not called.
   - The `DIVERGED.json` key `divergence_epoch_zero_based` exists (`ablation.py:402`).
   - podFailurePolicy in all 8: `[Ignore on DisruptionTarget, FailJob onExitCodes train In [10]]`. `restartPolicy: Never`, `backoffLimitPerIndex: 2`, `podReplacementPolicy: Failed`.
   - The gate is a healthy integer on an A10 GPU too: Delta canary-v2 on c5925 and the c5809 discriminator log `FINGERPRINT 11559681 expected 11559681`.
   - Limitation: see B1.
4. **K=3 OOM fallback: RESOLVED, with a procedural gap (B2).**
   - Six Jobs have inline packs `[[48]]`, `[[16]]`, `[[32]]`, `[[16, 32]]`, `[[48, 16]]` and `[[48, 32]]`. freeze.py asserts they are a subset of the K=3 pack.
   - Each carries the same env, RSS gate, stage, run root, bundle literal and fingerprint as K=3.
   - Resources: 2 CPU / 6 Gi at K=1, 4 CPU / 12 Gi at K=2. `single-arm-justified` is on the three K=1 Jobs.
   - The script diff against k3 is only the `fallback_packs.json` line, the two guards per arm and `PACKS=`.
   - The guard cases pass in the wrapper test (`fb_live`, `fb_nockpt`, `fb_ok`).
   - The delete-first reasoning holds: run_pack exits within one poll of the last arm, and the pod is re-created.
5. **Readout-b partial handling: RESOLVED for the v3 case, but widened (B3).** Dry-run logs:
   - full: `CERTIFICATION_ALL_PASS 6 0`, `DRY_RUN_EXIT … 0`;
   - mismatch on 42abed4b: `EBOPS_MISMATCH chang0926-f-n64-s1 snapshot500_primary 10429606 10428606`, `CERTIFICATION_FAIL 3 1`, exit 1. This closes v3's note that the mismatch path had run only on f2107a04;
   - partial: D-s1 `NO_TERMINAL_MARKER`, E1-s1 `RSS_GATE_FAIL`, `only=` the other three, `CERTIFICATION_ALL_PASS 4 0`, output under `…-b5-partial-20260928T222216Z`;
   - none: `READOUT_NOTHING_PRESENT`, exit 1.
6. **Stale text: RESOLVED.** The four-class and f2107a04 passages are all labelled:
   - flagged decision 5 "Superseded 2026-09-28" (l. 587-590);
   - the f2107a04 manifest section "SUPERSEDED; historical, do not copy" (l. 1383-1389);
   - the four-class affinity note at l. 1455-1458;
   - l. 1310 "Historical (f2107a04…)".
   The "dirty and uncommitted" claim for 42abed4b is corrected to commits 3dabcd2/ad18a3c (l. 1206-1210). Production items P1-P4 (plus P5) are recorded at l. 983-1007, each with the bundle or decision it needs.
7. **Bundle unchanged: RESOLVED.** See Recomputed. The ConfigMap name is `kai-chang0926-code-42abed4b5d`, and every GPU Job mounts it plus `kai-chang0926-fp-e9511d1aeb`.

Category A: none. Validators, verbatim (review/PREFLIGHT_validators_v4.txt):
- the 8 GPU Jobs: "note required pool = 1 products / 35 nodes cluster-wide / note no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate) / [rule PACK] K arms per pod declared (k5 5, k3 3, fb16-32/fb48-16/fb48-32 2, none on the K=1 Jobs) / OK / exit=0";
- readout-b5/b3: "note no required GPU product list — widest possible pool (good) / note single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here / OK / exit=0".

No red flag.

Not flagged, recorded: the fingerprint ConfigMap was created on the cluster before this gate (aaf42f2, cluster-ops, read back `immutable=true`, sha e9511d1a…). It is inert and immutable, not a pod launch.

### Flags

1. **B, before `kubectl apply` (RUN.md text): exit-10 recovery and the epoch-0 reading rule are not registered.**
   - PREFLIGHT l. 831-838 defines exit 10 but not what follows it. `DIVERGED.json` persists on the PVC and is terminal (`run_pack.py:184`). A re-applied Job then skips every arm and completes.
   - Separately, the wrapper fires only when all K arms diverge. With 4/5 epoch-0 divergences (wrapper test `fp_ok_4of5_div0` → exit 0), four node-caused divergences are recorded as terminal [A12] outcomes and the pod carries on.
   - Delta REGRESSION_TICKET §8 found that gate 15 (this fingerprint gate) "cannot reproduce or catch the canary's fault". The c6017 fault needs concurrent processes, so exit 10 and `ARM_DIVERGED` are the real backstop. The chang PREFLIGHT does not carry that finding.
   - Fix (RUN.md with the A2 rule):
     - After `POD_EPOCH0_ALL_DIVERGED`: rename `runs/<arm>` aside (never delete), add the node to `PILOT_B_BAD_NODES`, run `freeze.py --jobs-only`, lint, then re-apply.
     - Any epoch-0 `ARM_DIVERGED` in a pilot-b pod is a suspected node fault, not an outcome, until reviewed.
     - Cite Delta §8.
2. **B, before any fallback apply (RUN.md text): the ARM_STILL_LIVE timing and what the guard can see.**
   - `activation_widths.jsonl` is appended with fsync every epoch (`ablation.py:914-917`). An apply right after `kubectl delete job` therefore hits `ARM_STILL_LIVE` for the survivors (mtime under 15 min). Replacement pods then fail until 15 min pass or `backoffLimitPerIndex: 2` is used up. No data harm; the outcome is nondeterministic.
   - PREFLIGHT l. 937-938 says the guard detects "the K=3 Job was not deleted". That holds for the survivors' Job only. The OOM'd arm's files are already stale after its in-pod retries, so the K=1 Job's guard cannot see an undeleted K=3 Job. That K=3 pod would later be re-created and relaunch the same arm into the same run directory.
   - Fix: before applying either fallback, confirm that `kubectl -n cms-ml get job kai-chang0926-pilotb3-42abed` returns NotFound and that no `job-name=` pod is left, then wait 15 min.
3. **B, before readout-b is applied (RUN.md text): the partial readout no longer refuses a premature read.**
   - In the readout-b5/b3 scripts, `NO_TERMINAL_MARKER` (embedded script l. 24) also covers an arm that is still training. The former `SNAPSHOTS_NOT_READY` protection is gone: a readout applied early runs "partial" and exits 0.
   - This matters most for readout-b3, because A07-350-s1's readout gates packs 7-10.
   - Fix:
     - Apply readout-b only after its pilot-b Job is Complete, Failed or deleted.
     - A non-empty `missing=` means that arm's readout has not been done and nothing gated on it advances.
     - Or, optionally, add the fallback's 15-min mtime guard to the readout script. It is a wrapper change only; the bundle is untouched.
4. **C.** `freeze.py` runs the destructive full freeze for any argv without `--jobs-only`, including `--help` (`main()`). This reviewer triggered it (disclosed above). Fix at the next freeze: an argparse guard, and full freeze only on an explicit `--refreeze`.
5. **C.** Exit 9 counts against `backoffLimitPerIndex: 2`, and nothing keeps the replacement pod off the same node. The reliance on cluster-ops at l. 804-807 is stated; this note records that three failures on one node are possible.
6. **C.** The fingerprint process's host RSS in the 6 Gi K=1 fallback pods is unmeasured. It loads the same cache as the arm. The failure mode is a visible 137 before any arm starts, not a silent one.
7. **C.** The awk in the A2 commands runs on cluster-ops' laptop (the pipe is outside `kubectl exec`), so the note at l. 888 about the pod's `mawk` does not apply. The `jobs` field in `bundle-manifest*.json` is stale, as disclosed at l. 1075-1077.

### Earlier findings, by name
- v3 A1: RESOLVED (item 1).
- v3 A2: RESOLVED (item 2).
- v3 flag 3 (exit 5 retried per Job): recorded as P1, with the pilot rule to delete the Job after the first `ARM_MEMORY_GATE_FAILED` (l. 984-994). Accepted.
- v3 flag 4 (K=3 OOM fallback): RESOLVED (item 4), with B2.
- v3 flag 5 (K=5 VRAM evidence): RESOLVED (l. 896-903; RUN.md 212-217 cited; `--query-compute-apps` read at epoch 10).
- v3 flag 6 (readout blocked by one arm): RESOLVED, with B3.
- v3 flag 7 (no mechanical stop): recorded as P2. It is production-only and does not block the pilot.
- v3 flag 8 (stale text): RESOLVED (item 6). This is the first gate in four without a recurrence.
- v3 flags 9-11 (C): not in scope.

### Competing-group question
A group running this pilot would also write down what it does when the fingerprint passes but the pack NaNs at epoch 0. B1 covers that. Nothing else in scope is missing.

Solid:
- The pilot-b and fallback Jobs are A10-only with no preference and exclude c6017 plus the known-bad hosts. They run the e9511d1a fingerprint gate against 11,559,681 before any arm, and fail the Job on a pack-wide epoch-0 NaN.
- The bundle is still 42abed4b, reproduced by both `--jobs-only` and a full freeze.

Next verification: the first `RSS_RULE <arm> OK|STOP` line at process epoch 20 of the K=5 pod (about 50 min after `ARM_STARTED`). It is the first GPU-side evidence that the reload leak is gone under regime B.
