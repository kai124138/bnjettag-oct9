# plan.md — 2026-09-29-gpu-benchmark

## Phase 1 (STUDY) — experiment-designer, 2026-09-29 ~06:00Z

Artifact: `STUDY.md` (status `designed`), about one page. Then the experiment-log stub. No code,
no manifests, no PREFLIGHT edits (ml-engineer builds the harness in parallel).

Inputs read: `docs/infrastructure/gpu-selection-policy.md`; `decisions.md` 2026-09-28 (Kai,
GPU rule); Chang STUDY Arms (l. 606-619), Budget symbols (l. 1464-1471), RUN.md pilot-b telemetry
(l. 693-757, 853-1019); `chang0926/packs.json`, `index.json`, configs (epochs, batch); Delta STUDY
gate 7 (l. 446-449), Budget (l. 906, 916-920); Delta RUN.md canary entries (l. 402-526);
`delta/code/manifests/delta_w2_{t0,cells}_packs.json` (index sha 8a6f262f); GATES.md l. 1400-1403;
`canary_k.py` (k_rule); `bnhgq2/ablation.py` (`is_traced_epoch` l. 483-489, `remote` l. 747).

Counts recomputed here (design arithmetic, not results):
- Chang wave 1: E {A,B,D,F} 32 runs × 7,000 = 224,000 run-epochs; A07 {C, A07-350} 16 × 7,000 =
  112,000; R 8 × 1,000 = 8,000 at batch 256 (configs `train.batch`, `train.epochs`).
- Delta W2 packable: 248 runs = pack files; E base class 56 runs, 32,000 run-epochs (H 500 ×48,
  1,000 ×8); A07 base class 192 runs, 114,000 (500 ×176, 1,000 ×4, 1,500 ×4, 2,000 ×8); 88 runs in
  variant classes planned at their base class's K (`k_class_unmeasured`), 8 of them M006 (Deep Sets).

Design points found on paper:
1. Fluid formula alone underestimates when packs <= GPUs (Chang: 13 packs). Add the critical-path
   term H_max × s; evaluate the real packs by LPT (Graham bound brackets it).
2. K per product/class chosen by projected finish, not throughput alone (latency vs throughput).
3. R (batch 256) and Delta variant classes are not measured by E/A07 phases: labelled assumptions.
4. A10 baseline is mixed-pack and above the 90 % rule (97.9 % / 92.3 %); cross-check with Delta's
   pure E-k4 / A07-k2 canaries (different bundle). Flag an A10 harness control.
5. Screen validity check at zero GPU cost: A10 pilot-b K=5 pod, s over epochs 2-21 vs 481-500.
6. Delta A07 on 24 GB cards is out under frozen Delta STUDY gate 7 unless Kai overrides.
7. Schedulable GPUs: quota headroom, campaign cap, capacity probe (fingerprint sweep).
8. New products carry a certification delay (110-epoch canary) that A10 does not.

Failed / rejected approaches:
- First STUDY draft ran to 192 lines against a ~120-line cap; the sections were compressed and each design catch was cut to one
  labelled line. Nothing was dropped from the brief's list.
- Considered and not used: the throughput term alone as the projection (it is 10.3 d against a physical 11.3 d for Chang E on A10 at
  G = 7). A 481-500 window for the screen-validity check was also dropped because that window does not exist until about 19:40Z, after
  the decision.

Status 2026-09-29 ~07:10Z: STUDY.md written (125 lines, prose_lint score 0), status `designed`. Experiment-log stub prepended.
The verbatim quote was diffed against policy l. 43-47 (VERBATIM_OK). The budget is reconciled with the code's deadline model: per Job
2-7 h between the A10 per-process bound (2.5-3.3 h) and the A10 throughput bound (1.9-7 h), about 20-30 GPU-h. The A100 Job may end
after the 18:15Z readout.
Most likely to be amended in phase 2: [D2] K_low (ml-engineer's code may use another definition) and [D4] the G_p probe
(Kai may prefer the G-curve fallback). Self-check: every number carries a path and line; arithmetic re-run (R 129.6, 10.29 d,
11.25 d; K_rule 9/4, 10/5, 4/2; estimator limit u + t/10); no PREFLIGHT or code touched.

Phase 2 notebook: `plan-preflight.md` (ml-engineer). Its code defaults to K_low = max(1, K_run // 2) (`code/gen_bench.py:24`);
STUDY [D2] differs on 4090/3090 E and on A100 (`code/evidence/k_low_rules.log`). Flagged to the orchestrator, not resolved here.

### ml-engineer, 2026-09-29 ~06:00-08:00Z — PREFLIGHT build half (artifact: `PREFLIGHT.md`, sections up to "Open items")

Plan (kept in order):
1. `code/bench_driver.py`. W&B off through the frozen `ablation.run_training(remote=False)`, with `run_study.train`'s
   preconditions kept.
2. CPU gate on a full-size synthetic cache, since `run_engram.load_cache` needs 620,000 rows.
3. `code/node_survey.py` from the live node list.
4. `code/gen_bench.py`: 7 Jobs and the driver ConfigMap; lint.
5. `code/bench_summary.py`, tested on the A10 pilot logs.
6. PREFLIGHT, then the decisions.md entry.

Done. Gate logs are in `code/evidence/`.
- `cpu_gate_arm_a-s1.log` and `cpu_gate_pod.log`: PASS, including the injected OOM; `cpu_gate_negative.log`: all six
  refusals.
- `test_bench.log`: `ALL_PASS 8`; `lint_gpubench_build.log`: 0 ERROR.
- `plan_check.log`, `cpu_gate_configs_42abed4b.log`.

Decisions taken in the build (PREFLIGHT "Where I am not sure"):
- K_low = max(1, K_run // 2) (brief), against STUDY [D2]'s A10 K. `--k-low-rule study-d2` switches it; flagged.
- The node cap reserves 2 CPU and 16 Gi, so A6000 E runs K=9; flagged.
- Names are distinct within a phase, and phases 3-4 reuse the first K_low names.
- Stall watchdog 3,600 s; deadline x2.5 on A10 cost.

Failed or rejected approaches:
- Going through `run_study.train`: it refuses WANDB_MODE other than online (`run_engram.py:141-142`) and would share W&B
  ids across products. Rejected per the brief.
- A tiny cache through `run_engram.load_cache`: impossible (l. 216-219). Replaced by a full-size synthetic cache, sliced
  after loading under `--test-rows`.
- First gate run: the uv environment lacked `hls4ml==1.3.0`, which `bnhgq2/subln.py:106` imports. The pin was added.
- `bash -c` as PID 1 would ignore SIGTERM. The driver is `exec`'d so its handler stops the arms.
- The first unit-test run failed on import order: `bench_driver` drops its own directory from `sys.path` by design.

(This section moved here from `plan-preflight.md`, which no longer exists.)

Update ~07:30Z, after the orchestrator ruled that the STUDY governs:
- **K_low follows [D2]**, now the default (`--k-low-rule study-d2`). 24 GB E runs 4 and the A100 E 4 / A07 2; the half
  rule is kept for comparison.
- **Bug found and fixed.** A Job's `activeDeadlineSeconds` counts Pending time, so a single Job deadline could kill a late
  benchmark. The runtime bound moved onto the pod, and the Job carries the 6-h [D6] window plus that bound.
- **Added:**
  - [D1] s on the slowest arm, as the headline;
  - exclusion rules 1-3 in the summary;
  - `--offset` windows for falsifier (i);
  - the [D4] probe (`gen_bench.py --probe`, `bench_summary.py probe`);
  - `BENCH_CACHE` digests, checked against the anchor cache.
- The driver's sha changed to `4d2dcd7d…`, so the whole CPU gate was re-run: all PASS. Unit tests: `ALL_PASS 11`.
- Mismatches left for the orchestrator are in PREFLIGHT "Alignment with STUDY.md":
  - seeds past K=8;
  - the node reserve;
  - m_E 4,350 against 4,354;
  - card memory from labels;
  - the 60 s utilization window;
  - the probe's duration;
  - [D6] enforced by hand;
  - T(p) not built.

Update ~07:45Z, after the advisor review:
- The summary's OOM flag is now the driver's classification only (phase_result.json). OOM-looking lines in an arm
  that finished are counted as `oom_lines_seen` and do not trigger rule 1.
- A regression test was added: `ALL_PASS 12`. The summary evidence was regenerated.
- Added for cluster-ops: `kubectl create --dry-run=server` before the apply.
- Note: the designer's pointer to `plan-preflight.md` above refers to this section; that file no longer exists.

### cluster-ops, 2026-09-29 ~07:20-07:50Z — PREFLIGHT cluster-ops half (artifact: `PREFLIGHT.md`, the two placeholder sections + a new dated "cluster-ops (2026-09-29)" section)

Inputs read: `docs/infrastructure/gpu-selection-policy.md`, `STUDY.md`, `PREFLIGHT.md`'s build half (including the two
placeholder sections addressed to cluster-ops), `docs/infrastructure/nrp-nautilus-setup.md`, `.claude/memory/cluster-inventory.md`,
`nrp-lab/nrp_doctor.py`, `code/node_survey.py` (read, not edited).

Order followed: (1) create + verify the driver ConfigMap byte-for-byte, and byte-verify (not just annotation-verify) the
two pre-existing ConfigMaps' live payload hashes — advisor caught that the first pass had checked annotations only,
`kai-chang0926-code-42abed4b5d`'s tarball is `binaryData`, not `data`; (2) `nrp_doctor.py lint` on all 7 manifests, then a
server-side dry run of each, one `kubectl` invocation per manifest (see "Tooling note" in PREFLIGHT — a `for` loop's `-f
$var` cannot be resolved by the PreToolUse lint hook, which reads command text, not the shell's expansion); (3) re-ran
`code/node_survey.py` live and reconciled its per-product counts against the ml-engineer's 06:55:31Z read and against
`nrp_doctor.py lint`'s own (differently-defined) node count for the 3090; (4) read every manifest's resource key, node
exclusion list and run-root path directly (not the PREFLIGHT prose describing them), then checked the PVC read-only
through `pilotb3`'s `exec` and cross-checked cms-ml's own resourcequota/pod-count/A100-quota numbers, reconciling two
slightly different pod-count reads instead of leaving them unexplained; (5) advisor's second pass added one more read:
a third-party A40 pod's `PodScheduled` message, as the only outside evidence available for any of the seven products.

Failed / rejected approaches:
- A single `for f in manifests/kai-gpubench-*.json; do kubectl create --dry-run=server -f "$f"; done` — blocked by the
  lint hook (`file not found from ...: $f`); replaced by one invocation per manifest with a literal path.

Not done, flagged rather than decided (see PREFLIGHT "Where I am not sure"): whether A100 should be applied first
rather than last given the single-unit quota race (the brief fixed "A100 last"; the tension is flagged, not resolved);
the A6000-vs-L40 relative order (both 0 cpu-slack, both narrow, a genuine tie broken only by the visible-occupancy
signal). No cluster incident occurred, so nothing was added to `cluster-inventory.md`; no Job was applied.

### Fixer v1, 2026-09-29 ~08:05-08:55Z — `review/PREFLIGHT_critical_v1.md` (ITERATE: A1, A2, B1-B6)

Routes decided by the orchestrator (within Kai's policy), implemented here: A1 route (a), the A10 in the same benchmark
(K_rule E 4 / A07 2, K_low E 3 / A07 1, yield-to-anchor rule); A2, equal CPU per arm enforced plus a split by pod shape
(two Jobs per product, 2K pinned CPUs per phase, rule 5 at cores/K > 2.1); B1-B5 as specified; C3, C6 one-liners.

Done, in this order (evidence in `code/evidence/`; the v1 copies moved to `code/evidence/v1/` and `manifests/superseded-v1/`):
1. `bench_driver.py` (sha `5ede0778…`): `--cpus` self-pinning before any import, verified against the kernel's mask
   (`ARM_CPUS`, exit 14 on a mismatch); per-phase first-2K selection from the allowed set, logged (`POD_CPUS`,
   `PHASE_CPUS`, `phase_result.json`); steady cores ÷ K in `PHASE_DONE`; per-thread `Cpus_allowed_list` in the sampler;
   exit codes decide outcomes (OOM = exit 7 only; `host_oom_kill` from the cgroup's `oom_kill`); test flags
   `--test-allowed-cpus`, `--test-arm-stub`, refused in a pod.
2. `gen_bench.py`: 16 Jobs (the A10 added), per-Job pod shape and deadlines, both runtime bounds, the header's CPU/RAM
   lines, the yield rule on the A10 Jobs, a required pod anti-affinity among the pinned pods (the fixer's choice).
3. `bench_summary.py`: B1 `startedAt` fallback; B2 completion at `stop_after` and `non_ok_arms`; rules 5 and 6; rules 2
   and 6 product-wide across both Job directories; time-ordered pod logs and the repeat flag (C3, C6); node CPU facts;
   B5 findings. `node_survey.py`: the A10's role label. `plan_check.py`: new, reproducible plan check.
4. Tests `ALL_PASS 21 SKIPPED 1`; CPU gate PASS (arm values equal v1's); `plan_check` all OK and idempotent; lint 0 ERROR
   (12 narrow-pool WARN); the driver ConfigMap `kai-gpubench-driver-5ede0778f7` created 08:38:07Z, live payload hash equal;
   16/16 server dry-runs accepted; A10 cross-checks recomputed (pilot figures equal v1's; Delta canaries on the [D1] basis).
5. STUDY Amendment 1 (tagged in place, one block at the end, prose_lint 0); PREFLIGHT rebuilt (build half in place, the
   cluster-ops v1 sections marked superseded, a new "Fixer v1 rebuild" section); the experiment-log entry updated with
   the bracketed "was" pattern.

Failed or rejected on the way:
- Pinning in the parent: `taskset` (needs util-linux in the image), `preexec_fn` (unsafe with the sampler thread alive),
  `sched_setaffinity(child_pid)` after `Popen` (races the child, and sets the main thread only). Chosen: the arm pins
  itself before importing anything, so every later thread inherits the mask.
- The kernel-level pinning test cannot run here: darwin has no `sched_setaffinity`, and no container runtime is installed.
  `mulder` was not used: a shared group box, not authorized for this. The test skips loudly and runs unmodified on Linux.
- First draft of the plumbing test injected CPUs 6-15, which on a Linux box would try to pin CPUs outside its cpuset;
  it now injects the process's own allowed set (advisor).
- A summary fixture wrote `ARM_CPUS` before the attempt header; the parser rightly ignored it (the real order is header,
  then `ARM_CPUS`). Another fixture did not discriminate C6 (the mismatching log also sorted last by name); a case with
  name order against time order was added.
- The gate's copy loop `p*` also matched `plan.json` (an empty directory instead of the plan, in v1's evidence too); the
  glob is now `p[0-9]*`, and this run's evidence copy was repaired by hand.
- The STUDY amendment's first draft used "harness" (prose_lint score 12); replaced, score 0.
- The runtime premise "every Job under 3 h" does not hold at the pessimistic bound for the A6000 and A100 K_rule Jobs
  (3.25 h, 5.17 h with header); recorded as measured, not restated.

### Fixer v2, 2026-09-29 ~09:40-10:05Z — `review/PREFLIGHT_critical_v2.md` (PASS; B1, B3-B6, C1-C8)

Context: by the time this started, the orchestrator had applied the six non-A10 K_low Jobs and the A100 K_rule (09:30-09:36Z,
`RUN.md`). No A10 Job was applied and no summary had run. So every applied manifest had to stay byte-identical, not only the 3090
K_low. B2 (staged apply) is the orchestrator's.

Done, in this order (evidence in `code/evidence/`):
1. B1: `bench_summary.samples_for` counts thread masks only on proc rows with `proc_epochs_done` ≥ 1. The rules-2/5/6 fixture
   now carries `proc_epochs_done`. New test with a pre-pin row (passes) and a post-pin escape (still excluded).
2. C1, B3, B6 in `bench_summary.py`:
   - `pin_from_arm_logs`: with no `phase_result.json`, the pin checks run from the arm logs, else R is withheld;
   - `verify_interrupted_arms`;
   - `a10_rules`: which A10 attempt counts, the B6 check, and "A10 baseline not measured".

   Two new tests. Three mutations (B1 filter off, C1 withholding off, attempts ordered by directory name) each fail exactly
   their own test.
3. C5:
   - `gen_bench.PILOT_NODES`, added to the A10 Jobs' hostname `NotIn` with one annotation; the pilots were confirmed read-only
     on gpu-17 and c5805 at 09:47Z.
   - Regenerated first in a scratch mirror, then in place, from the 07:39:45Z survey: 16 of 18 files byte-identical, the A10
     pair changed only in those two values and the annotation.
   - `plan_check.py` gained `pilot_nodes` (it fails the old A10 manifests): 16 × PLAN_OK, idempotent.
   - Lint OK × 2; server dry-run accepted × 2.
4. Tests `ALL_PASS 24 SKIPPED 1`. The summary re-run on the CPU-gate output reproduces the fixer-v1 table plus the A10 status row.
5. STUDY: Am. 1 B3 and B6 (pre-registered before either A10 Job is applied), B5/C3 corrected, C2 memory clause, C4, [L1] C6/C7;
   prose_lint 0.
6. PREFLIGHT: fixer v2 change log, shas, exclusions, "Deadlines" (B5 accepted risk), "Analysis", "Alignment" 10 and "Where I am
   not sure" (C4), Open items 3 and 5 (B4), the apply order, and a fixer v2 lint and dry-run note.
7. `decisions.md` C8 bracket, inline. The experiment-log entry quotes no number that changed, so it is not edited.

Decisions taken, flagged in the handback:
- B3 counts per Job attempt, not per phase. That is the brief's and the reviewer's reading ("only a complete run counts"). A deleted
  attempt's complete phase is listed, never counted.
- B6 uses the source value 114.455 s; 114.45 is its two-decimal rendering.
- B3's summary code goes beyond the STUDY-only line the review asked for, so that the summary cannot emit two uncounted rows for
  one A10 phase.

Failed or rejected on the way:
- A per-shape lifetime-mean utilization for B5: rejected, because no product's phase utilization and no real header length has
  been measured, so the number would be invented.
- Reading the B6 anchors from the evidence JSON at run time: rejected, because a regenerated file could move a pre-registered
  threshold. They are hard-coded, with the path cited.
- Filtering the pilot nodes out in `plan_product`: rejected, because it would change `bench_plan.json` and the node counts. Only
  the `NotIn` values and an annotation change.
- The first summary re-run on `code/evidence/cpu_gate_pod/` gave blank rows. That copy stores the arm logs flat in `p*/`, not in
  `p*/logs/`, and the fixer-v1 code gives the same blanks on it. The layout was restored in a scratch copy; the evidence copy was
  left as it is.

### results-analyst, 2026-09-29 ~17:20-18:30Z — Phase 4 VERIFY (artifacts: `VERIFY.md`, `verify.json`)

Inputs: STUDY.md (Am. 1, [D1]-[D6], rules 1-6, critical v2 B3/B6), PREFLIGHT.md, RUN.md (16 Jobs resolved 17:18Z: 9 complete,
7 "not practical now"), `code/bench_summary.py` (sha256 `cd5f5b64…`, fixer v2, B1 filter in place) = the pre-registered analysis.

Data provenance (done):
- PVC `/data/chang-n64-20260926/gpu-bench/` = 1.5G, 1,678 files; copied read-only through the pilot pod
  `kai-chang0926-pilotb5-42abed-0-qqjmt` with GNU tar, **excluding** `*.keras`, `*.npz`, `activation_widths.jsonl`,
  `checkpoints/` (784 files, 1,565,906,836 bytes): model/checkpoint/prediction payloads that `bench_summary.py` never reads
  and that the STUDY says are not read ("the benchmark's validation lines are not read"). Copied: 894 files, 2,468,457 bytes,
  every size equal to the PVC inventory (`data/pvc_inventory_full.tsv`, all 1,678 files with size and mtime). Local copy
  chmod a-w. Reason: keep the tar light on the GPU-priority pilot pod (the brief allows "tar of small files").
- The PVC `pod-<pod>.log` is the driver's tee; the saved kubectl log in `logs/<job>/` is byte-identical plus two leading
  lines (`BENCH_POD … <stamp>`, `HOSTNAME_NODE`), checked with `diff` on all 9. `bench_summary.py` needs the BENCH_POD stamp
  (B3 attempt order), so the analysis root uses the kubectl log.

Plan:
1. `code/verify_bench.py` (new; the only script that writes numbers): builds `data/bench-root/<slug>-<shape>/` from symlinks
   (PVC copy's plan.json, samples.csv, bench_result.json, p*/; `logs/<job>/` job.json, `<pod>.pod.json` as pod.json,
   `<pod>.log` as `pod-<pod>.log`) for the 9 completed Jobs; the 7 deleted ones enter through `--plan` as rule-3 rows.
2. Calls `bench_summary.summarize_bench(root, manifests/bench_plan.json)` unchanged (imported, not copied), saves its rows
   (`data/bench_summary.json`) and its table (`data/bench_summary.log`, also by the CLI for a reviewer to rerun).
3. Reproduction check, independent parse (own regex) of every arm log and samples.csv: s [D1] slowest arm, per-arm s, R,
   wall per run-epoch, peak GPU memory and fraction, steady utilization, cores/K, thread-mask union, OOM/NaN, verification,
   fingerprint; ✓/✗ against bench_summary and against RUN.md's quoted telemetry (PHASE_DONE walls and cores/arm; A100 pin
   check 95.3 % / 72,709 MiB / 88.8 %).
4. Q per Job: completed = apply → container startedAt (B1 fallback) via bench_summary; deleted = never Running, lower bound
   apply → deletion (deletion times from RUN.md l. 89-91, 114-117), labelled.
5. B3 attempt rule and B6 one-sided check as bench_summary's `a10_rules` computes them.
6. T(p) per campaign by the STUDY formula (l. 53-58) on G ∈ {1, 4, 8, 10, 13, 16} (brief's grid plus Delta's 10-pod cap),
   K per [D3] (earlier T among non-excluded K at each G), [A1] (Delta A07 only on ≥ 45 GB: A6000, A100; A10 shown only as a
   labelled reference), [A2] (R not timed: out of T), C_p = 110 × s/3600 + canary queue for non-A10 products. Tie set T ≤ 1.10
   × min T per G. G where the ranking flips. G_p unmeasured: stated.
7. verify.json from the same script; VERIFY.md tables emitted by the script into `data/verify_tables.md` and pasted, not retyped;
   `tools/verify_check.py`; experiment-log Result line.

Failed / rejected on the way:
- First `kubectl exec` (~17:20Z) failed on the laptop's DNS loss ("no route to host"); retried after connectivity returned.
- A full 1.5 GB tar through the pilot pod: rejected (see provenance).

Status ~18:50Z (results-analyst): done. `VERIFY.md` and `verify.json` (1,098 rows, every field non-empty) are rendered by
`code/verify_bench.py` from `code/verify_template.md`; `tools/verify_check.py VERIFY.md`: ok (no finding); `tools/prose_lint.py`:
score 0. Every printed number has a verify.json row except identifiers (dates, product and CPU model names, line numbers,
G labels), checked by a reverse scan. Additions to the plan, made after seeing no result:
- a100 quota snapshot (`data/resourcequota_snapshot.json`, 18:28:07Z: 23/24) as the [D4] quota term (advisor);
- static allocatable ceilings (the `gen_bench.py:142-150` formula, reproducing `bench_plan.json` on all 16 shapes) and a
  [D4]-capped view, because the 4090's pool (3 schedulable nodes) may not reach G = 13-16 (it can, by allocatable, for the
  K pair T picks);
- break-even G tables, since G_p is unmeasured and pools differ;
- LPT pack check for Chang (the formula is a lower bound when G does not divide the packs; leaders unchanged at the grid G);
- the [D2] memory check table (per-process peaks larger than the A10's on every other card).

Failed / rejected on the way (Phase 4):
- `kubectl exec` failed at ~17:20Z on the laptop's DNS loss ("no route to host"); retried after 18:09Z, fine.
- A full 1.5 GB tar through the pilot pod: rejected (PVC inventory kept instead; 2.5 MB copied).
- The PVC tee `pod-<pod>.log` as bench_summary's pod log: rejected; it lacks the `BENCH_POD` stamp B3 orders attempts by.
- First T draft marked the 4090 at G = 16 above its static ceiling: an artefact of equal-T K pairs (4/2 and 4/1 both on the
  critical path) and of comparing G, not min(G, packs), with the ceiling. Fixed: equal T prefers the pair within its
  ceiling, and the mark uses min(G, pack count or cap).
- `verify_check.py` reads "Delta" as the word "delta" (a gap word): number-bearing prose lines say "campaign (b)" instead.
- Falsifier (i) not evaluated: its window is "the latest … before the decision" (advisor; STUDY l. 92-93).
- Advisor (final review): the smaller-shape ceiling is loose for a mix of E and A07 pods. Replaced by an exact joint ceiling
  (per-node packing of the K pair's pods by dynamic programming, at most the campaign's packs per class). Result: the 4090's
  pairs reach 13 (4/2) and 16 (4/1) on empty nodes, so no leader changes; the A6000 at G = 16 caps at 13. Added the [D5]
  unit-of-choice sentence (both Chang units pick the same product at every grid G) and the two-part null verdict (rejected at
  every assumed G; not resolvable at the G that can actually schedule).
