# plan.md — 2026-09-26-method-atlas (orchestrator notebook)

Crash-resilient notes. Newest at the bottom.

## Reading of Kai's request (2026-09-26, ~23:55)

- "Use Chang's method" + "design we can do in the future, agents do deep research on theory and
  ideas, code ready to run for ~100 methods incl. combos, theory part down, for now".
- Read as: **no launch now.** The earlier voice note ("launch 40-60 trainings") is reference for
  the recipe; the launch belongs to `campaigns/2026-09-26-training-batch/` (wave 0, STUDY v1
  ITERATE). Stated at the top of the reply so Kai can correct it.

## Shape (advisor-reviewed)

1. Parallel: ml-engineer code-surface inventory; tried-already inventory; physics-researcher ×5
   families (B binarization, R recipe, Q activation/EBOPs, A architecture, P inputs) + THEORY.md;
   fixer on the Chang STUDY (arbiter v1 fixes).
2. experiment-designer: ATLAS.md — ~100 entries (singles + pre-registered combo packages),
   code tiers T0 config-only / T1 small change / T2 new module, two budget tiers (screen = one
   cosine cycle, 500 epochs, validation-only, not quotable; confirm = full recipe, ≥ 6-8 seeds),
   budget in the Chang STUDY's symbols so its canary is the cost oracle. Not a STUDY: each wave
   spawns its own STUDY via /new-experiment.
3. ml-engineer: generator + patch set in `code/`, generated configs, CPU build/reload gates,
   manifests linted, not applied. Report ready vs not ready honestly.
4. Log stub (experiment-log), decisions.md line (two-tier structure), research-log lines from
   the cards. Commit locally; no push.

## Decisions for Kai (to surface in the reply)

- `publication/` is a broken worktree (gitdir points to the pre-migration path); where atlas code
  lands long-term intersects the code-line-merge campaign.
- Pod count / launch of wave 0 and screens: at the launch gate.

## Status

- 2026-09-26 23:5x: BRIEF.md written; nine agents launched.
- 2026-09-27 00:05: Chang STUDY fixer done (15/15 A+B resolved). Peer session bnjettag-0b owns
  campaigns/2026-09-26-training-batch/ (committed our STUDY edits in 9eddc86, running v2 review).
  This session does not edit or commit that campaign; it owns method-atlas only.
- 2026-09-27 ~00:20: code-surface inventory in. Peer (bnjettag-0b) confirms: anchor [A]
  constraints become a patch series on the screen tarball (sha256 26f3cc40...5a45) under
  campaigns/2026-09-26-training-batch/code/; the resulting sha is the atlas base, messaged when
  fixed, after STUDY v2 passes. **Design risk from their v2 panel:** every 350k softmax-attention
  arm may have a static EBOPs floor above target (10-bit fixed softmax output; SAT k=1 channels
  never below 1 bit). The atlas must treat "floor reduction" (learnable/Chang-matched softmax
  output quantizer, Linformer / softmax-free, width floor 0) as a prerequisite family, and every
  350k method is conditional on a floor below target.
- Consequence for atlas code: method patches are written and unit/CPU-gated against the screen
  tarball now (on its current recipe), then rebased onto the anchor sha when it lands. "Ready"
  is reported per method in two columns: gated-on-tarball, gated-on-anchor (pending).
- 2026-09-27: research in: B (14), R (14), P (12), A (16), THEORY.md (M1-M7). THEORY [derived]:
  at A07-N64, six d×d layers at mean input width 1 bit already cost 393,216 EBOPs (> 350k), a
  reference point, not the floor; agrees with the peer's static-floor finding. Theory asks for
  every attention lever at two targets (350k and 5M). Waiting on Q and tried-already.
- 2026-09-27: all inputs in (Q 14 cards; tried-already 68 methods, 12 failed with mechanism).
  Correction sent to peer: anchor STUDY:102 "1,000 epochs" sd 0.0019 is from a 101-epoch,
  es_patience 15, unconstrained config (ptw-n8-20260925-base-w1a8.json:35,46), verified here.
  experiment-designer launched on ATLAS.md + atlas.json + LOG_LINES.md.
- 2026-09-27: anchor re-based ([D19], training-batch arbiter v2, verified l. 45-58, 186-225):
  Chang quantizers (WRAP datalane, learned softmax out, tables SAT_SYM >= 4 bits). Old-quantizer
  floor A07 4,559,008 (350k infeasible); Chang-matched 0-bit A07 326,656 / E 163,328. BRIEF.md
  amended; designer told to re-base cards and trace every atlas architecture's floor in wave 1.

## experiment-designer (ATLAS.md, atlas.json, LOG_LINES.md), 2026-09-27

Plan (owner protocol step 1; crash notes):
- Inputs read: BRIEF, plan, THEORY, tried-already, code-surface, cards B/R/Q/A/P, anchor STUDY
  (working tree, v2 with [D19]) and review/STUDY_arbiter_v2.md "Independent checks".
- Anchor moved: [D19] (WRAP datalane, learned softmax output, trainable tables). Old-quantizer
  floors (4,559,008 for A07) apply only to the C' branch. D19 floors (arbiter arithmetic, not
  traced): A07 326,656 / 989,344; E 163,328 / 611,000. Softmax floor formula
  16·H·T·S + 4·(H·T·S − H·T) reproduces both; used for derived floors of new architectures,
  labelled "to be traced at W1".
- Entries generated from one spec script (scratchpad `atlas_spec.py`) -> atlas.json, entry
  table and budget totals, so ATLAS.md counts equal atlas.json counts.
- Tiers from code-surface §1 (S runner live keys), not from cards. Anchor-introduced keys
  ([A1] [A2] [A3] [A20]) are a separate sub-tier T0a with placeholder names.
- Screen: 4 seeds, horizon 500 by default, longer where the treatment starts at a restart or
  later; paired vs anchor [A6] snapshot of A (350k), C (5M) or E; BH q = 0.10 within wave;
  Holm at confirm. KD/warm-start need a new teacher on the gated 90/10 train split.
- Contradictions routed to deep research (Q03 i0 default 2 vs 0; A vs Q cards on granularity;
  Q04 2026-09-15 attribution; Q05 "moving target does not exist" is wrong for S).
- No shared log touched; stub goes in LOG_LINES.md.
- 2026-09-27 designer status: ATLAS.md, atlas.json (103 entries, 38 patch slugs), atlas_spec.py,
  atlas_tables.py, LOG_LINES.md written; self-check passed (103 table rows = 103 JSON entries, no
  orphan IDs, every slug documented, budget strings equal the spec output). Advisor review items
  applied: in-wave replicas as the factorial all-low cells, FF2 and 5M base fallbacks, tier legend,
  teachers on the [D19] quantizers, M015 onset = logged freeze epoch. No shared log touched.
- 2026-09-27: ATLAS.md + atlas.json (103 entries, 38 slugs) done; integrity checked (IDs unique,
  slugs match §12, combo refs valid, atlas_spec.py regenerates atlas.json byte-identically).
  Peer's staged anchor code traced floors on CPU (decisions.md 2026-09-27 "chang0926 code"):
  A07 0-bit 343,053 (headroom ~6,947 at 350k), E 171,526; sent to reviewer and engineers.
  Launched: critical-reviewer solo on ATLAS; ml-engineer (patches to existing files, 20 slugs
  now, 12 blocked on [A1]/[A3]/[A20]); ml-engineer (new files: generator, manifest template,
  body-deepsets, bop, linformer, diag scripts, gate runner). Logs appended from LOG_LINES.md
  (experiment-log 2 stubs, decisions 1 entry, research-log 1 entry). STUDY.md pointer added so
  tools/index.py lists the campaign; index rebuilt.

## fixer v1 on ATLAS (critical review v1 = ITERATE), 2026-09-27

- Resolved A1, A2, B1-B4 in `atlas_spec.py` (single source), `atlas_tables.py`, ATLAS.md, and
  `LOG_LINES.md` §5. New file `screen_power.py`. Report: `review/ATLAS_fixer_v1.md`.
- Floors: the SAT exp-input term (H·T·S; H·T·k for Linformer) and the LUT term (⌊13·H/4⌋ per
  block, a two-point fit) were added. The formula now asserts equality with the trace (A07
  343,053 / 1,005,741; E 171,526 / 619,198) and keeps an assert for the arbiter values with the
  terms off. The baselines are weight-bit-aware. The traced values are cited to the evidence
  JSON, staged at 72a1290 (not the final anchor sha).
- 350k default: A07 cells are feasibility probes. The accuracy cells default to arm E,
  overridable at K1. The floor family is read by G2 against arm A and for accuracy against arm E
  (Welch). The 350k cells of M075, M077 and M078 are dropped (no-PE is a no-op on E).
- Screen seeds: n in {4, 6, 8} is set at K2 from Z14, with ranking mode at 4 as the default
  fallback. The budget is 344,000 run-epochs at n = 4 and 684,000 at n = 8 (was 336,000 at 4).
- M014 is confirm-only. It has no screen cell (`targets` []).
- Tried and dropped: none of the edits failed. A first draft of the M009 text carried
  hand-typed numbers (85,507 / 351,907), which were wrong by the LUT term. They were corrected
  to the computed 85,517 / 351,917 before regeneration.
- Not touched: `BRIEF.md` (orchestrator's), `code/`, shared logs. The experiment-log and
  decisions.md copies are listed for the orchestrator in the fixer report.
- 2026-09-27: ATLAS critical v1 = ITERATE (A1 floors stale vs trace; A2 screen cannot resolve
  +0.3 pt with 4 seeds under BH over 47 cells; B1-B4). Fixer running. Peer: B is now E at 250k,
  E may become the anchor primary; staged anchor tree sha 5b606b61...306b @ 72a1290, not final.
- 2026-09-27: new-files engineer done: 538 configs (W2 280, W3 256, prereq 2) on a stand-in base
  (const0922-a07-n64-s1-fast50-fp32, not launchable), 48 packs K=6, 13 module tests pass, CPU gate
  15/15 (build 0.75-3.25 s, step ~1.6 s, save+reload ~0.5 s). Refused: M006, M020, M071 (params
  unset); M074/M103 missing A2 (sent to fixer). Offline nrp_doctor lint exits 2 on an empty node
  map (tool artefact; re-lint with cluster access before any apply). run_pack.py expects index
  rows, packs list run IDs; output root hard-coded to /data/constituent-study-20260922.
- Follow-up 1 (generator findings): M074/M103 got [A2]; the registry sweep found 0 misses; M006
  dims are set from jsc150/model.py:88-100 in the deepsets.py dict form; Bop γ/τ stay null with
  a note (no source value read; DR-22). atlas.json sha256 e736d1b2...8780.
- 2026-09-27 01:4x: fixer v1 + follow-up done (atlas.json e736d1b2...; M074/M103 A2; M006 dims from
  jsc150 model.py:88-100; Bop gamma/tau left null, DR-22 researcher sourcing them). Generator re-run
  strict: 554/562 configs; manifest 50 packs / 288 arms K=6; lint with cluster access: no ERROR,
  WARN parallelism 10. Logs and BRIEF propagated to the fixer's numbers.
- 2026-09-27: DR-22 done (research/DR-22-bop-hyperparameters.md): paper §5.2 CIFAR-10 gamma 1e-4
  (x0.1/100 ep), tau 1e-8; §5.3 ImageNet gamma 1e-4 -> 1e-6 linear, tau 1e-8; Larq Bop defaults
  tau 1e-8, gamma 1e-4 (commit 3d7de883). Neither transfers as-is; a scan seed only. Apply to
  M020/M071 after ATLAS v2 review (not mid-review), labelled "scan seed, Larq default".
- 2026-09-27 ~02:10-04:10: rate-limit cutoff (session limit) killed the v2 reviewer (review file
  written before cutoff: ITERATE, A1-v2 drift replicas not in atlas.json; B1-B5 v2) and the
  patches engineer mid-series.
- 2026-09-27 08:40: Kai confirmed [D19] Chang quantizers and [D21] E primary at 350k (arm A = E,
  B = E at 250k, A07 at 350k descriptive, C = A07 at 5M), 8-10 pods, add H and NB arms
  (decisions.md top). Atlas anchor = E at 350k. Resumed patches engineer; fixer v2 launched
  (v2 findings + E re-base + Bop scan-seed values from DR-22).
- 2026-09-27: fixer v2 (review/ATLAS_fixer_v2.md). Anchor re-based on Kai's [D19]/[D21] answers:
  arm A = E at 350k, A07-350 descriptive (floor-family base and k_base), C = A07 at 5M, F = E + PE;
  NB covers M049 at 350k (new per-entry field covered_by_anchor_study). drift_replicas now in
  atlas.json (W2: A@1,000, A07-350@500, C@2,000; W3: A@500, A07-350@500, C@2,000; budget
  unchanged). Gate (ii) = mean gap >= delta/2 and n sized by k_joint for the whole rule; m counted per
  cell from the role field, baselines excluded (W2 5M 44 -> 43, W2 350k 20 -> 19); n_W3 <= n_W2.
  M047-M049 350k role = feasibility probe on E. B4 fallbacks (arm A fails, R4 survivors, M013).
  Anchor non-degeneracy rule inherited in §5.1 (anchor STUDY l. 386-404 @ 5d6c3c9). Bop gamma 1e-4,
  tau 1e-8 (DR-22 scan seed). New base texts match none of the old anchor_arms.json rules on
  purpose (the unmodified generator raises; checked in scratch). A patched generator copy in the
  scratchpad (drift_replicas read, [D21] arms) wrote 566/566 configs, 0 refused, replicas as §5.2.
  Tried and dropped: none failed. atlas.json e736d1b2... superseded by the sha in the fixer report.
- 2026-09-27: fixer v2 done (atlas.json 7e57bf24...; drift replicas in json; gate (ii) mean >= delta/2;
  m per cell; arm A = E at 350k [D21] everywhere; A07-350 descriptive; Bop gamma 1e-4 / tau 1e-8
  scan seed; non-degeneracy rule inherited from STUDY 5d6c3c9 l. 386-404). Log copies updated.
  Generator engineer resumed to read drift_replicas + new base texts and regenerate. Next: critical v3.
- 2026-09-27: patches engineer done: 20 slugs as 21 patches (0001 key registry atlas_keys.py);
  invariance gate bitwise on 7/7 const0922 configs (1 thread, TF_DETERMINISTIC_OPS=1; 69 s);
  21/21 slug tests (423 s), also on E shapes (bundle quantizers). 12 slugs blocked (BLOCKED.md).
  Trial rebase onto anchor 72a1290: 0012/0013/0014/0020 conflict. Export refused for 6 slugs
  until an HLS path exists (DR-17). decisions.md entry appended for both engineers.
- 2026-09-27: generator v3: 566 configs strict (0 refused) from atlas 7e57bf24; [D21] arms in
  anchor_arms.json; replicas from atlas.json drift_replicas; gate 15/15 on tarball and on the
  atlas-patched tree. Live lint: no ERROR, WARN parallelism 10/51. Committed 812b1eb (campaign
  dir only). critical-reviewer v3 (design + code-ledger honesty) launched.
- 2026-09-27: critical v3 = ITERATE. Design resolved (A1-v2..B5-v2). A1-v3 (code): unwired keys
  silently ignored, so M004/M006/M020 and blocked-slug configs gate as the base model; B1-v3 W2/W3
  replica run-name collision; B2-v3 per-row hardware labels missing. Routed: patches engineer
  (strict key refusal + wire Deep Sets/Bop outside [A2]); fixer (hw_labels + C items); then the
  generator engineer (status split, manifest packs only runnable rows, wave token in run names).
- 2026-09-27: fixer follow-up v3 (critical v3 B2, C2-C4): per-entry `hw_labels` (DSP audit; DR-17 no-export
  from the patch series' export_ok=False keys, incl. FF2 M097-M102; not-in-series attention/body/mask;
  derived features); base["1400000"] only on M010; §0/§3.2 E row names F; M038 null-gate note. atlas.json
  6fbd4b5d…3711; budget and m unchanged. code/configs needs regenerating (pins 7e57bf24).
- 2026-09-27: fixer v3 follow-up (atlas 6fbd4b5d; hw_labels on 43 entries). Patches 0022 strict
  keys (unread key -> raise naming key+slug), 0023 Deep Sets wired (M006 20,742 params), 0024 Bop
  wired outside [A2]'s optimizer_for; invariance 7/7 bitwise, 24/24 slug tests. Generator engineer
  on the final pass (validator-based status, wave token in run names, manifest runnable-only).
- 2026-09-27: generator v4: 566 configs; validator-based status: ready_on_base 96 cells/14
  entries, runnable_on_series 160/33, refused_by_key 232/41, placeholder_pending_anchor 78; run
  names unique with wave token; manifest 32 packs/188 arms; gate on full tree 37 pass, 1 refused
  (M004 expected), 1 FAIL (M018: patch 0003 clip_identity leaves 4-6 values per layer after one
  step), 11 need teacher. Earlier gate harness used optimizer_for (Bop never exercised) and a zero
  teacher; fixed. Patches engineer on the 0003 fix + post-step binary gate in every weight test.
- 2026-09-27: 0003 fixed (forward exactly q*beta; post-step binary gate in every weight test;
  invariance 7/7; 24/24). Gate v5: 36 pass, 11 need teacher, 0 fail (M018 passes). Wave-2 Job
  30 packs / 176 arms; after-P-T1 list 2 packs / 12 arms (M027, M035, M036). Live lint: no ERROR.
  Committed c3f8a31. critical-reviewer v4 launched.
- 2026-09-27: critical v4 = PASS (no A). Open before any wave-2 launch: B1-v4 index regenerable,
  B2-v4 manifest keyed by unique run name + WIRING launch gap in ledger, B3-v4 Bop flip rule is a
  Kai decision (K2). C: arm-C 5M gate for 9 entries (reviewer gated, all pass), M006/ATLAS
  "not in series" wording, BLOCKED.md l.5. Generator engineer + fixer closing B1/B2/C and B3 note.
- 2026-09-27: fixer follow-up v4 (critical v4 PASS; C2-v4 Deep Sets/Bop wiring labels, B3-v4 Bop flip rule as a K2 Kai decision in M020/M071). atlas.json 8b1c3aa6…1265.
- 2026-09-27: v4 items closed (index regenerable byte-identically via gen + classify + annotate;
  packs keyed by unique run name; 61 entry x arm gate pairs: 50 pass, 11 need teacher, 0 fail;
  Bop flip rule a K2 decision). Final atlas.json 8b1c3aa6. Orchestrator re-check: atlas_spec
  regenerates identically; strict gen exit 0, configs identical; live lint no ERROR.
- 2026-09-27 (Kai): renamed "method atlas" -> Delta (reads as the ATLAS detector); run the Delta
  trainings (10 pods on top of the anchor, Bop mirror flip); commit to GitHub as Kai
  (BinaryTransfomerJettager, public, main 39d643c; push to a branch). Chang's runs stay with the
  training-batch session. git mv done; decisions.md entry; memories saved; peer told.
  Public repo code/constituent-study-20260922 == screen bundle (152/152 sha256), so the tarball
  series applies there directly. Plan: fixer rename -> ml-engineers (rename identifiers, rebase on
  pilot c5d6f02a, unblock 12 slugs, real arm-A base, launch gaps) + wave-2 STUDY/review ->
  PREFLIGHT -> launch after pilot epoch-500; paper-writer builds the public branch in parallel.
- 2026-09-27 14:10: rate limit (reset 12:10) cut the rename fixer mid-way; resumed. Peer: anchor
  pilot LAUNCHED 20:51Z (job kai-chang0926-pilot-77f1ca, ConfigMap kai-chang0926-code-77f1ca4e9f,
  bundle 77f1ca4e, supersedes c5d6f02a), one A10 23 GB; telemetry (not results) arm A (E@350k)
  ~218 s/epoch at K=6 -> epoch 500 ~30 h out; A07-350-s1 OOM at K=6 on the A10 (dropped).
  Consequences for Delta: rebase target is 77f1ca4e; K per pod must respect A10 VRAM for A07-size
  cells (arm C 5M and A07-350 cells), e.g. K<=5 or a >= 24 GB product list; screen H=500 at
  ~218 s/epoch is ~30 h per run (telemetry).
- 2026-09-27 (fixer, rename): Delta design-side rename done (report review/DELTA_rename.md). git mv ATLAS.md/atlas_spec.py/atlas_tables.py/review/ATLAS_* -> DELTA/delta; atlas.json removed, delta.json regenerated (only renamed strings differ; byte-identical twice). Gap statistic Δ/δ/δ_res -> g/g₀/g_res (ASCII g_0); JSON key atlas_id -> delta_id. Constants BNJetTag-Delta, delta-20260926-w2/w3/w4, delta0926 in the design text; code/ untouched (ml-engineer renames generate_atlas.py, atlas_keys, config names). Lines above keep the old names as history.
- 2026-09-27: design rename done (delta.json f4ad2571; review/DELTA_rename.md); committed locally.
  Launched: ml-engineer (code rename + rebase onto anchor pilot 77f1ca4e + unblock 12 slugs +
  Linformer wiring); experiment-designer (wave-2 STUDY in campaigns/2026-09-27-delta-screen/);
  paper-writer (public branch delta-methods in a scratch clone, docs only, not pushed).
- 2026-09-27: PUSHED docs commit d436e69 to kai124138/BinaryTransfomerJettager branch
  delta-methods (Kai-authorized; authored as Kai noreply, no trailer; docs/delta/ + catalogue;
  prose_lint 0; no training-batch numbers; floors as shape arithmetic without the fitted LUT term:
  d32h4 343,040, d24h2 171,520). Public names: A07 -> d32h4, E -> d24h2; slugs
  beta-schedule-runner, kd-constrained-runner; teachers teacher-{fp32,int8}-d32h4. The code commit
  must use these names. Compare: https://github.com/kai124138/BinaryTransfomerJettager/compare/main...delta-methods
- Wave-2 STUDY v1 panel: physics ITERATE-level (A1 ranking null, A2 selection bias); critical 4 A;
  constructive 1 A. Arbiter running.
- 2026-09-27: code rename + rebase done (patches/ tarball series renamed, invariance 7/7, 24/24;
  patches-anchor/ 0001-0037 on bundle 77f1ca4e, anchor invariance 19/19, anchor slug tests 17/17;
  all 38 slugs gated, 13 anchor-only; export refused for 7 new slugs). decisions.md appended.
  Generator engineer launched (rename, real anchor base, run_pack fix, memory-canary packing).
  Wave-2 STUDY v2 panel running.
- 2026-09-27 evening: generator done on the real anchor base (bundle 77f1ca4e arm configs; 582
  configs incl. placebos and replica seeds 1-8 pending STUDY PASS; validator accepts all; gate 142
  pairs: 119 PASS, 15 NEEDS_TEACHER, 8 FAIL). BLOCKER: [A20] guard refuses non-binary weights under
  Chang quantizers (M047-M049, P-T1, P-T2 fail) -> asked the peer how FP32-E/NB build; routed to the
  STUDY fixer as a launch gate. zero_floor re-traced per signature (38 pairs). run_pack fixed
  (0025/0038). K planning E 4 / A07 3 on A10; memory canary manifest written. Anchor tarball
  re-frozen to e90327d4 (regime B) -> rebase needed before launch.
- 2026-09-28 05:31Z (peer): anchor regime-A pilot STOPPED on Kai's decision. Host memory grows
  ~80-95 MB/epoch/arm in the chang0926 runner/trainer (suspects: per-epoch validation-model reload,
  full-split trace); fills a 36Gi pod at ~4 h of K=5; no run reaches epoch 500 at 6 GiB/arm. Also
  run_pack.py relaunch defect (stale heartbeat mtimes, pod-wide retry budget). Any Delta code on
  c5d6f02a / 77f1ca4e / e90327d4 has the leak: DO NOT launch long runs on it. Fix + memory-growth
  canary gate (fail > 5 MB/epoch) land in the regime-B freeze; Delta rebases on that sha. Delta's
  run_pack patch 0038 will conflict with the anchor's run_pack fix at rebase. The regime-B pilot
  (Delta's start signal) launches only after the fix, so Delta's start moves out.
- 2026-09-28: wave-2 STUDY FROZEN (Kai's round-6 rule; review/STUDY_frozen_check.md). DELTA.md
  amendments block (l. 49-72, commit 4a0d82d); public mirror pushed (cc8abe2 on delta-methods).
  Peer told: 5 MB/epoch gate is ~7x too loose at 7,000 epochs. index.py now lists designed/frozen.
  Waiting on: leak-fixed regime-B bundle (peer PREFLIGHT), regime-B pilot epoch-500 readout, [A22].
  Then: rebase patches-anchor (0012/0014/0019/0020 + 0038), host-memory canary (canary_k.py needs
  an RSS slope), PREFLIGHT, cluster-ops packing from the memory canary, launch at 10 pods.
- 2026-09-28: peer pinned leak-fixed regime-B bundle 42abed4b (manifest 041f981a, ConfigMap
  kai-chang0926-code-42abed4b5d, commit 3dabcd2; CPU leak 3.237 -> 0.004 MB/epoch; RSS gate env
  BNJ_RSS_GATE_LIMIT_MB, window epochs 5-105; run_pack heartbeat/retry fix; trace every 10 incl. 0).
  Superseded: e90327d4, f2107a04, ceb174db, 77f1ca4e. Rebase engineer resumed onto 42abed4b with
  RSS-slope checks for Delta's per-epoch additions. [A22] not in this freeze.
- 2026-09-28 09:17Z canary run 1 failed instantly (W&B project BNJetTag-Delta missing; Job showed
  Succeeded; wrapper now exits 7 on any phase failure). Project created PRIVATE (verified via the
  pod's own check). Re-applied 09:28Z; Pending on GPU saturation; Running ~09:40Z on
  hcc-nrp-shor-c6017 (A10). First POD_MEM: ~2.05 GB RSS per rep-A arm at K=4 (telemetry). Watch
  running to completion (~8-10 GPU-h projection). After it: k_result.json -> K per class, re-freeze
  the bundle with the fixed configs/packs, PREFLIGHT gate 7/14 results, solo critical PREFLIGHT gate;
  wave launch still waits for gate 1 (regime-B pilot epoch-500 readout) from the training-batch session.
- 2026-09-28 ~10:59 local: discriminators done (both Complete): c6017 and c5809 both FINGERPRINT
  11,559,681 = expected; ECC 0; pip freeze identical. So c6017 is healthy single-process; the canary
  NaN occurred with 4 processes on one GPU (concurrency-only fault, cause open). Gate 15 cannot catch
  that; per-arm epoch-0 divergence + wrapper exit 7 is the fast signal. Fresh cluster-ops launching
  canary v2 (W&B disabled, anti-affinity c6017, bundle 705a554b). Open before wave launch: W&B run-id
  collision with the c6017-era runs (same names).
- 2026-09-28 20:07Z canary v2 (W&B disabled) refused at start: tracked configs require
  WANDB_MODE=online. Collision resolved by reading the code: 42abed4b keys W&B ids by BNJ_STAGE
  (stage_run_id = sha256(stage\0name)[:12]), so production never appends to canary runs; the only
  overlap (canary-stage rep-A s1-s4 from the c6017 attempt) is accepted and labelled in RUN.md.
  Relaunching canary v2 with WANDB_MODE=online.
- 2026-09-28 23:23Z: anchor regime-B K=3 pilot pod Running (A07-350-s1, C-s1, F-s1); K=5 pod Pending.
  Anchor resizes its per-arm RSS gate to 8 GiB from Delta's measured slope. Delta's per-pack limit
  (2,100 + 5 x H MiB) already covers the measured 0.45-0.63 MB/epoch: at H 2,000 the projection is
  about 2.4 GB + 1.3 GB = 3.7 GB against 12,100 MiB. No Delta change needed.
- 2026-09-29 ~00:15Z: both anchor regime-B pilot pods Running (K=3 since ~23:23Z, K=5 since ~00:12Z).
  Projected epoch-500 readout ~19:00-21:00Z 2026-09-29 (telemetry projection). Training-batch STUDY
  frozen; at the readout Kai may choose PID-input option (c) -> anchor patch 0032 + new bundle ->
  one more Delta rebase. Delta canary A07-k3 phase (rep-C s1-s3) launched on one A10 to finish
  gates 7/14.
