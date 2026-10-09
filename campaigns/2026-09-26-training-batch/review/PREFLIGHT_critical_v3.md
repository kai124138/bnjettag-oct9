## 2026-09-28 01:17 PDT (08:17Z) — critical-reviewer PREFLIGHT review: 2026-09-26-training-batch (regime-B pilot pods pilot-b-k5, pilot-b-k3 and readout-b5/b3), iteration 3
VERDICT: ITERATE. There are two Category A findings. Both are fixed without a re-freeze: regenerate the manifests and amend two texts. The bundle, the ConfigMap and every code sha stay as they are. (A1) The pilot-b pods may land on any of four GPU classes and prefer L40. STUDY and Kai's decision put wave 1 on A10 and bind the 14-day rule to this pilot's s_e. (A2) The operational canary rule is not operational. It has no formula, and as worded (a projection to the terminal epoch) it would stop a healthy pod: I recomputed a 102,878 MB projection from the post-fix series.

If the orchestrator counts this as the third failed gate under the solo tier, the one question for Kai is this: may pilot-b run on any of the four canary classes, or must it run on A10 as his 2026-09-27 wave-1 decision says?

Checked:
- PREFLIGHT.md at ad18a3c, "Regime B addendum" l. 742-1177, including the cluster-ops block l. 1057-1099.
- review/PREFLIGHT_validators_v3.txt; review/INCIDENT_stall_20260928.md; RUN.md l. 1-120, 205-255, 376-440.
- STUDY.md l. 351-377, 800-810, 1425-1575, 1695-1760, 1878-1885.
- plan.md l. 905-925 and 1060-1140.
- decisions.md, the top 5 entries and the [D15] entry l. 156-172.
- manifests/{pilot-b-k5,pilot-b-k3,readout-b5,readout-b3}-job.json, configmap.json, configmap-42abed4b.json and freeze.py l. 106-107.
- In code/tree, which is identical to the extracted bundle: run_pack.py (all 267 lines), bnhgq2/ablation.py l. 455-500 and 580-960, run_study.py l. 94-195, and restore_checkpoint l. 290-315.
- campaigns/chang0926/{pilot_b_k5_packs.json, pilot_b_k3_packs.json, index.json}.
- code/evidence: leak_probe_*, cpu_gate_shipped_42abed4b_full.log, cpu_gate_shipped_f2107a04_full_rerun.log, a17_pairing_shipped_42abed4b_8seeds.log, trace_floors_42abed4b.log, regression_trace_every_absent_42abed4b.log, dry_readout_b{5,3}_42abed4b.log and pytest_shipped_42abed4b.log.

Recomputed (CPU, synthetic or file-level; nothing here is a result):
- **Bundle.** `shasum -a 256 manifests/chang0926-code.tar.gz` gives 42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0. The payloads of `configmap.json` and `configmap-42abed4b.json` (byte-identical, `cmp`) both decode to 198,452 bytes with the same sha. The object is `kai-chang0926-code-42abed4b5d`, `immutable: true`, with annotations bundle 42abed4b… and manifest 041f981a…. The cluster read-back is cluster-ops' record (PREFLIGHT l. 1059-1067); I did not re-query the cluster.
- **Extraction against the tree.** A fresh extraction has 250 files. `diff -rq` of `code/` against `code/tree` (with `analysis/` excluded, and `__pycache__` and `.pytest_cache` ignored) is empty, and `analysis/` against `code/analysis` is empty. The campaign's `git status --short` is empty.
- **Manifest sha.** I rebuilt it from the 30 top-level and `bnhgq2/*.py` files of the extraction, with the pins of `requirements-training.txt`. The result, **041f981a9d5b8c3a7affb175d82de0ca2df9bc6261a172f67cb365c88b4bbd42**, equals the `test "$MSHA" = …` literal in all four Job scripts and PREFLIGHT l. 831.
- **Tests.** I ran them in the fresh extraction on CPU with the pinned uv env: `pytest tests/test_run_pack.py tests/test_memory_leak_fix.py tests/test_trace_every.py tests/test_wandb_stage.py` gives **28 passed**. The producer's full log ends `93 passed, 2 skipped` (`pytest_shipped_42abed4b.log`).
- **CPU gate.** `cpu_gate_shipped_42abed4b_full.log`: `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`, with 0 `GATE_FAIL`. There are 58 `TRACE_EVERY_OK` lines, 50 with `traced_epochs 701` and 8 with 101. The 117 sorted `CONFIG_PREFLIGHT_PASS`/`I_DECAY_OK`/`PREFLIGHT_ALL_PASS` lines diff empty against `cpu_gate_shipped_f2107a04_full_rerun.log`, so the builds did not change from f2107a04 to 42abed4b.
- **[A17] and [A7].** [A17] shows 32 `PAIRED`, 0 unpaired, and `MANIFEST 041f981a…` printed. [A7] shows 9 `STATIC_FEASIBLE`. The absent-key regression gives 4× `records_files_ebops_identical True`.
- **Leak probe**, recomputed with np.polyfit over rss_mb[5:105]. `leak_probe_f2107a04_prefix_B_115ep.json` gives slope 3.237 ± 0.050 MB/epoch, baseline 1,437 and projection 24,096 (FAIL). `leak_probe_42abed4b_B_115ep.json` gives slope **0.004 ± 0.200**, baseline 1,883 and projection 1,911 (PASS), with a residual sd of 57.8 MB. Both match PREFLIGHT l. 813-814.
- **Two-point projection** (epoch 10 against epoch 20, extended to 7,000). The post-fix series has RSS 1,881 → 2,026 MB (Δ 144 MB), which projects to **102,878 MB**. The pre-fix series has Δ 28 MB, which projects to 20,691 MB. The two-point form therefore reads the fixed code as far worse than the leaking code (A2).
- **Pack indices.** `pilot_b_k5_packs.json` is `[[0, 1, 24, 56, 57]]`, which index.json maps to a-n64-s1, a-n64-s2, d-n64-s1, cprime-n64-s1 and e1-n64-s1. `pilot_b_k3_packs.json` is `[[48, 16, 32]]`, which maps to a07-350-n64-s1, c-n64-s1 and f-n64-s1. Each readout's `--only` list and `--indices` match its pod.

Category A: validator output, verbatim (review/PREFLIGHT_validators_v3.txt). For pilot-b-k5: "note required pool = 4 products / 108 nodes cluster-wide / note no activeDeadlineSeconds (NRP has no universal 6 h cap — fine if deliberate) / note [rule PACK] 5 arms per pod declared. / OK / exit=0". For pilot-b-k3 the output is the same with "3 arms", OK, exit=0. For readout-b5 and readout-b3: "note no required GPU product list — widest possible pool (good) / note single (non-Indexed) Job — per-index limits N/A; backoffLimit/activeDeadlineSeconds is the legacy pattern and is fine here / OK / exit=0". No validator raised a red flag. The two Category A findings below are the reviewer's.

### Answers to the brief

1. **Leak fix and protection.**
   - The fix is real on CPU: the slope falls from 3.237 to 0.004 MB/epoch, and I recomputed both. Only the incident's first candidate was tested, however. On GPU the leak was 80-95 MB/epoch, and this 30× gap leaves open whether the GPU leak is the same mechanism.
   - The RSS gate (`ablation.py:655-679`) resolves slopes of about 0.2 MB/epoch (1 SE on the noisiest series) against a threshold of about 0.55. It stops leaks between about 0.55 and about 35-45 MB/epoch before they fill the pod. At K=5 the pod has 30 GiB against about 10.75 GB of starting RSS. A leak of 40 MB/epoch per arm fills it near process epoch 100, so the verdict at 105 comes only just in time.
   - Above about 40 MB/epoch, and at incident scale (90 MB/epoch, a fill near epoch 44 at K=5), only the operational rule stands between the pod and a repeat POD_STALL cycle. That rule is a manual read, and as registered it is ill-posed (A2).
   - Verdict on protection: sufficient for the pilot **once A2 is fixed**. The combination is then complete across leak sizes, bounded, and cannot write a wrong number. It rests on a person reading the logs at epochs 10 and 20, and no mechanical stop covers the large-leak case. For production, the unbuilt per-epoch hard stop at 0.9 × limit (plan.md l. 1123-1127) is needed (flag 7).
2. **run_pack against the incident's mechanism.** Each of the incident's mechanisms is addressed:
   - Stale heartbeat on relaunch (§4): `heartbeat_age` takes the maximum of the mtimes and `started_wall` (`run_pack.py:85-90`).
   - One budget covering pod-wide events: `POD_STALL` is not charged to the per-arm budget and has its own budget of 2 (`:198-204`, `:228-236`).
   - Serial blocking wait: `terminate` gives one shared 120 s grace (`:156-171`).
   - Relaunch into a full cgroup: `POD_RELAUNCH_WAIT` (`:243-248`).
   - Memory visibility: `POD_MEM` on every poll (`:142-153`).
   - Stall kills exit 143, because run_study's SIGTERM handler (`run_study.py:114`) makes them non-zero, so they reach the retry paths. Exit 5 is not retried within the pod (`:224-227`).

   Two residual issues:
   - The exit-5 guarantee holds per pod, not per Job (flag 3).
   - A stall in which fewer than half of the live arms are stale (for example 2 of 5, if the others limp along as D-s1 did) takes the charged per-arm path, which has no free-memory check (`:205-208`, `:237-239`). Killing the bloated arms frees their memory, so this is minor (C).
3. **Regime-B semantics.** Correct as implemented.
   - `is_traced_epoch` (`ablation.py:483-489`) covers e = 0, (e + 1) % 10 == 0 and the last epoch. That gives 701 traces and 101 for R (the gate prints them).
   - Every selection write is guarded by `traced`: `model_min_ebops`, `model_unconstrained`, `model_best`, `model_best_auc_feasible` and the recovery freeze (`feasible` is False when untraced) (`:810-846`). The degeneracy counters count traced epochs only.
   - The PID assertion is split. On a traced epoch the PID EBOPs equals `cost` within 1e-6 relative. On an untraced epoch `pid._ebops == in_training_ebops` must hold exactly, and the 115-epoch CPU probe exercised that about 100 times without a failure.
   - Checkpoint cadence 25 against trace cadence 10 is safe. `restore_checkpoint` runs no retrace on resume (only sha asserts and `load_model`), so a resume from an untraced checkpoint (25, 75, …) continues on in-training ranges exactly as an uninterrupted run does. Traced epochs are defined by absolute epoch, so a resume does not shift them. 500 is a multiple of 10 and of 25, and `ebops_trace_every` refuses a snapshot cadence that is not a multiple of k (`:477-479`).
4. **Manifests.**
   - The ConfigMap, `BNJ_STAGE=pilot-b`, `BNJ_RUN_ROOT=/data/chang-n64-20260926/pilot-b`, the sha literals and `BNJ_RSS_GATE_*` are all correct in both pods.
   - `test_wandb_stage.py` passes in my run (28/28), which includes `test_pilot_b_cannot_collide_with_pilot`.
   - Memory is 30 Gi for K=5 and 18 Gi for K=3, 6 GiB per arm against a measured start RSS of 2,106-2,160 MB (incident §2).
   - **GPU class fails (A1).**
   - **K=5 VRAM fits by measurement.** The exact K=5 set was co-resident on an A10 at **21,094 MiB of 23,028** (RUN.md:212-217). Per process that is 4,354 × 3 + 2,830 + 5,172 = 21,064 MiB, which leaves a 1,934 MiB (8.4 %) margin. The brief's "about 22 GB" is the K=6 figure with A07-350 attempts in the pod; STUDY l. 1553-1554 gives 18.8-22.6 GiB for that pod. TF's BFC allocator does not return memory, so these steady-state figures already include each process's peak up to that point, and regime A traced every epoch, so the trace peak is included. Regime B adds no GPU allocation: the reloader keeps one small model.
   - Caveats on K=5: C′'s 5,172 MiB was read on its third attempt, and no peak after about epoch 10 was observed. PREFLIGHT does not cite this evidence (flag 5).
   - **K=3 VRAM has not been measured.** Two A07 [D19] arms (C and A07-350, 61,951 params each) sit beside F, A07-350 went OOM at K=6, and no fallback is registered for an A07-350 OOM at K=3 (flag 4).
5. **sha chain, gates, pairing and floors.** All hold and were re-derived above: tree = extraction → manifest 041f981a → bundle 42abed4b → ConfigMap payload. The full CPU gate gives 58/56/2 with lines equal to f2107a04. [A17] gives 32/32, [A7] 9/9, and the absent-key regression is identical.
6. **Readout-b jobs and dry runs.**
   - Both logs end `DRY_RUN_EXIT … 0`. b5 shows `CERTIFICATION_ALL_PASS 6 0` (five runs, with A-s1's [A19] copy as the sixth record) and b3 shows `CERTIFICATION_ALL_PASS 3 0`. Both use the 42abed4b tarball, `MANIFEST_SHA_OK 041f981a…` and the correct `--only` and `--indices`.
   - The emptyDir is 12 Gi, equal to the ephemeral-storage limit, which closes v2 flag 5.
   - The negative (mismatch) path was run only on f2107a04, with `state.json` edited in place, and has not been re-run from the builder. `certify_ebops.py` is unchanged, so this is acceptable (C).
   - Open: the snapshot gate blocks every arm when one arm has no snapshot and no `DIVERGED.json` (flag 6).
7. **Pilot-only against production-only blockers.**
   - *Blocks the pilot:* A1 and A2, plus flags 3-5, which should be settled before `kubectl apply`.
   - *Blocks production but not the pilot:*
     - the mechanical hard stop (flag 7);
     - R-B8's open choice between gating production and trusting the pilot-b slopes;
     - the gate never evaluating a production process resumed with fewer than 105 epochs left (PREFLIGHT l. 846-848);
     - the provisional packs.json and the K=4 A07 packing;
     - the cross-class resume rule (v2 flag 4, still not in RUN.md). A1's pin removes that risk for the pilot, not for production.

### Earlier findings, by name
- v2 flag 1 (stale text): **recurred a third time**, as flag 8 below.
- v2 flag 2 (STUDY run-id amendment and `BNJ_STAGE=production`): **RESOLVED** (STUDY l. 1880-1885).
- v2 flag 3 (`certify_ebops.main()` never run end to end): **RESOLVED** (dry runs on 77f1ca4e, f2107a04 and 42abed4b).
- v2 flag 4 (cross-class replay rule in RUN.md): **OPEN**. No such rule is in RUN.md or PREFLIGHT. For the pilot it is retired if A1 pins A10.
- v2 flag 5 (emptyDir against the ephemeral limit): **RESOLVED** (12 Gi / 12 Gi).
- v2 flag 6 (`data_sha256` caveat): **RESOLVED** (PREFLIGHT l. 71-73).
- v2 decision 6, pre-registration: **RESOLVED** (decisions.md 2026-09-27 "CPU certification mismatch is re-run once").
- **v2 "GPU classes: RESOLVED as a recorded rule" is SUPERSEDED.** That ruling (flagged decision 5, four classes, "s_e is read on whichever of the four the pilot lands on") predates Kai's 2026-09-27 wave-1 decision (K=5 on the A10 class). It no longer holds; see A1.

### Flags

1. **A. The pilot-b GPU class contradicts STUDY and Kai's wave-1 decision.**
   - Both pilot-b Jobs require {L40, A10, RTX-3090, V100-SXM2-32GB} and **prefer L40 at weight 100** (`freeze.py:106-107`; the affinity in `pilot-b-k{5,3}-job.json`).
   - STUDY says: "wave 1 is restricted to the A10 class (Kai, 2026-09-27, [D15] branch executed)" (l. 1506, 1520); the pilot runs "on the GPU class production will use" (l. 1539); the K=3 pod runs "on the same GPU class" (l. 1556); "The 14-day rule now binds on the regime-B canary: T_run = 7,000 × s_e" (l. 1500).
   - Impact: if the scheduler finds a free L40, the [D15] launch decision is taken on an s_e from the wrong class (an L40 is faster, so T_run is underestimated). The K=5/K=3 pod map would also rest on VRAM read on a 48 GB card, which says nothing about fit on a 23 GB A10. Neither pod is launched, so nothing is lost yet.
   - Fix: in `freeze.py`, set the pilot-b required list to `['NVIDIA-A10']` with no preferred term. Regenerate the two pilot-b Jobs, re-run `nrp_doctor.py lint`, and record the A10 node count. `freeze.py` and the Job JSON sit outside the tarball, so the bundle, the manifest sha, the ConfigMap and every `code_sha256` stay unchanged. The alternative, keeping four classes, is Kai's call and is not the default. The pin also retires v2 flag 4 for the pilot.
2. **A. The operational canary rule has no operational form, and its registered wording would stop a healthy pod.**
   - The rule exists only as a sentence in STUDY l. 1727-1730 ("stops the pod if the projected terminal RSS exceeds the per-arm limit"). It is absent from PREFLIGHT's addendum and cluster-ops block. It has no formula, no read command and no stated time after launch.
   - Projecting two points ten epochs apart to 7,000 multiplies noise by 700. The post-fix CPU series gives Δ 144 MB over epochs 10 to 20, which projects to **102,878 MB** and would stop a healthy pod. The leaking pre-fix series projects only to 20,691 MB. The terminal-epoch test at 6 GiB fires at Δ ≥ about 5.5 MB per 10 epochs, which is below any plausible RSS noise.
   - Fix (text only, before apply): write the rule into PREFLIGHT (the cluster-ops block) and RUN.md, and correct STUDY l. 1727-1730 with a dated line. The rule's job is the leak that fills the pod before the gate's verdict at 105, so it should project to process epoch 105, not to 7,000.
     - Per arm: stop if `host_rss(20) + (host_rss(20) − host_rss(10))/10 × 85 > 6,144 MiB`, which is roughly Δ > 400-470 MB per 10 epochs at the measured baseline.
     - Pooled alternative: `memory.current + ΣΔ/10 × 85 > memory.max`.
     - The incident's rate (about 900 MB per 10 epochs) trips it; 144 MB of noise does not.
     - Name the reader (cluster-ops), the time (projected from the canary s_e: about 25 and 50 min after the last `ARM_STARTED` at about 150 s/epoch), and the commands (`grep host_rss_mb` on `/data/chang-n64-20260926/pilot-b/logs/*.log`, and `POD_MEM` from `kubectl logs`).
3. **B. "Exit 5 is not retried" holds per pod, not per Job** (PREFLIGHT l. 774, STUDY l. 1725-1726).
   - `run_pack` exits 1 when any arm failed (`run_pack.py:263`). The Job has `backoffLimitPerIndex: 2` and `podReplacementPolicy: Failed`, so the pod is re-created.
   - The new `run_pack` skips only `DIVERGED.json` and `VERIFIED_COMPLETE.json` (`:184`), not `RSS_GATE_FAIL.json`. A gate-failed arm therefore relaunches at attempt 0, resumes from its epoch-100 checkpoint, restarts the window, and runs about 105 more epochs before failing again, up to two more times.
   - The same applies to `ARM_FAILED_AFTER_POD_STALLS` and `ARM_FAILED_AFTER_RETRIES` arms.
   - Impact: GPU hours (about 2 × 105 epochs for one arm on a one-GPU pod) and a second or third `RSS_GATE` line for the same arm. No wrong number results.
   - Fix: either add `RSS_GATE_FAIL.json` to the skip list (a code change and re-freeze, so not now), or record the real behaviour in PREFLIGHT and have cluster-ops delete the Job after the first `ARM_MEMORY_GATE_FAILED` once the other arms have paused.
4. **B. K=3 VRAM has not been measured, and no fallback is registered for an A07-350 OOM.**
   - A07-350 went OOM on all three attempts at K=6. C and A07-350 share the A07 [D19] build, and neither has a per-process GPU figure. C′'s 5,172 MiB comes from the SAT build.
   - STUDY's clause (5) covers a C′ OOM. It does not cover an A07-350 or C OOM at K=3, even though packs 7-10 (16 production runs) wait on this pod's A07-350-s1 readout.
   - Fix: before apply, register what happens if A07-350-s1 or C-s1 goes OOM at K=3. For example: a K=2 or K=1 A07-350-s1 pod on A10 at batch 2,790, with RUN.md recording the per-process peak from `nvidia-smi --query-compute-apps`.
5. **B. PREFLIGHT does not cite the K=5 VRAM evidence.** Add RUN.md:212-217 (21,094 of 23,028 MiB for exactly this set, a 1,934 MiB margin) to the regime-B addendum. Add a cluster-ops read of `--query-compute-apps` at the epoch-10 canary so that peak per process is measured under regime B, as STUDY l. 1508-1509 requires for the pod map.
6. **B. Readout: one arm without a snapshot blocks every arm.** The readout-b5 and b3 gates accept only `snapshots/epoch-0500/state.json` or `DIVERGED.json`. An arm stopped by the RSS gate (`RSS_GATE_FAIL.json`) or by `ARM_FAILED_*` blocks the readout of every arm with `SNAPSHOTS_NOT_READY`. This is a readout-side issue and needs a new readout manifest only, not a code-sha change. Fix: accept `RSS_GATE_FAIL.json` as terminal and drop that arm from `--only`/`--indices`, or state the manual partial-readout procedure.
7. **B (production only). No mechanical stop exists for a large leak.** plan.md l. 1123-1127 flags a per-epoch hard stop at RSS > 0.9 × limit as "not built". For the pilot, A2 fixed is enough, because someone watches at epochs 10 and 20. Thirteen unattended production pods over about 14 days cannot rely on that. Decide before production: build it (a code change and new bundle, which breaks pilot→production resume, so decide before pilot-b launches if resume is wanted), or gate production arms with the same RSS gate (R-B8, still open).
8. **B. Stale text, third recurrence.** PREFLIGHT l. 852 says "The working tree is dirty and uncommitted" for 42abed4b. It is committed in 3dabcd2 and ad18a3c, and the campaign's `git status` is empty. l. 1024-1039 still name `…-f2107a` Jobs and `sha256sum -c against f2107a04`. l. 913-915 disclaims those names, but the table is the part people copy from. Fix: correct l. 852 and relabel the f2107a04 table as superseded. This is the same class of error as v1 flag 2 and v2 flag 1. The producer should grep for "uncommitted", old shas and old Job names at every re-freeze.
9. **C.** The RSS gate treats an unreadable `VmRSS` as "not evaluated" and the arm continues (`ablation.py:667-669`). STUDY's canary convention counts an unreadable input as a fail. On Linux the input is always readable, so this matters little, but it should either be aligned or noted.
10. **C.** The gate's false-FAIL risk on GPU is unknown. On the noisiest CPU series the slope SE is 0.200 against a threshold of about 0.56, so a flat arm fails about 0.3 % of the time with iid noise. Allocator warm-up steps at the first traced epochs (9, 19) would tilt a 100-point linear fit. Before apply, pre-register how an `RSS_GATE FAIL` is read from `RSS_GATE_FAIL.json`: a plateau after the early steps means warm-up; a uniform slope or a step at every trace means a leak (PREFLIGHT l. 825-826 has the idea).
11. **C.** `POD_RELAUNCH_WAIT` prints every 5 s while it waits. Together with `POD_MEM` this speeds up kubelet log rotation, so rely on the PVC arm logs.

### Competing-group question
A group running the same pilot would pin it to the production GPU class, so that the timing and memory decisions they take from it transfer. It would also give its memory kill switch a threshold that does not fire on its own reference data. A1 and A2 are those two gaps. Nothing else in scope is missing.

Solid:
- The regime-B bundle chain was re-derived end to end: tree = extraction (250 files) → manifest 041f981a → bundle 42abed4b → ConfigMap `kai-chang0926-code-42abed4b5d` payload.
- The leak fix removes the CPU-reproducible reload leak (3.237 → 0.004 MB/epoch, recomputed). The regime-B selection semantics are correct and tested (28/28 re-run).
- K=5 fits an A10 by direct measurement of the same five processes (21,094 / 23,028 MiB).
- The readout-b dry runs pass on the shipped tarball.

Next verification: after the manifests are regenerated with the A10 pin, run `nrp_doctor.py lint`, and grep both Job JSONs for `NVIDIA-A10` as the only product and for the absence of a `preferredDuringScheduling` term. Then add the dated epoch-10/20 rule text to the PREFLIGHT cluster-ops block. That is about 20 minutes of work and closes both A findings.
