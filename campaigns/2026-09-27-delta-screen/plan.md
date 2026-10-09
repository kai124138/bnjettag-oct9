# plan.md — 2026-09-27-delta-screen (Delta wave 2), experiment-designer

**2026-09-28 GPU amendment (Kai):** future launches follow
[the measured GPU selection policy](../../docs/infrastructure/gpu-selection-policy.md).
Earlier A10-only planning and canary records remain dated evidence.

Owner notebook, phase 1 (STUDY.md). Crash-resilient; keep current.

## Inputs read (2026-09-27)
- `docs/methodology/03-phases.md`, `01-principles.md`, every file in `docs/conventions/`.
- `campaigns/2026-09-26-delta/BRIEF.md`; `DELTA.md` §0-§7, §10-§12; `delta.json` (sha256 checked:
  f4ad2571667af56ccbd28e4271e315aad36d378575d83b9864ace979b8029204 = the brief's f4ad2571…9204).
- `campaigns/2026-09-26-delta/code/README.md` (read for structure only; the exclusion list is taken at
  the PREFLIGHT gate, not now); `screen_power.py` (run locally, design arithmetic, output copied below).
- Anchor `campaigns/2026-09-26-training-batch/STUDY.md` at **HEAD dde5ca7** (`git show HEAD:…`; the
  working tree differs by 152 lines and is not the cited version). Line numbers in STUDY.md refer to HEAD.
- Anchor `RUN.md` (pilot telemetry, OOM incident) and `PREFLIGHT.md` l. 492-493, 525-527 (cache
  identity, split_seed 1, y_val sha256, threshold (c)).
- `.claude/memory/decisions.md` l. 77-80 (Kai, direct, 2026-09-27: run the Delta trainings, 10 pods on
  top of the anchor, Bop mirror flip).

## What will be computed (all design arithmetic, nothing quotable) (v1, superseded by fixer v2 and v3)
1. W2 cell counts from `delta.json` (`wave == "W2"`): 49 singles, 71 cells (47 at 5M, 23 at 350k,
   1 at 1.4M); per-seed epochs 39,000. Check: equals DELTA §5.4 (284 entry runs at n = 4).
2. BH family sizes from `screen_power.py`: m = 43 (5M), 19 (350k); k_joint table.
3. Budget by architecture class and seed branch: `budget.py` (this directory), reads `delta.json`,
   E timing 218 s/epoch at K = 6 (RUN.md l. 70-72, telemetry), A07 ratio r in {1, 2} (no measurement).

`screen_power.py` output (2026-09-27, local, design arithmetic): W2 5M m 43 alpha_eff 0.00233,
k_joint 4.83 / 2.50 / 1.83 at n 4 / 6 / 8, sd_d ceiling 0.062 / 0.120 / 0.164 pt; W2 350k m 19
alpha_eff 0.00526, k_joint 3.66 / 2.09 / 1.58, ceiling 0.082 / 0.144 / 0.190 pt. Cheap version (3
seeds) k_joint 10.73 at W2 5M alpha_eff.

## What STUDY.md will contain (v1, superseded by fixer v2 and v3)
Header, question/null/bearing, reference table, arms (cells by role), exclusions with reasons,
prerequisites (P-T1/P-T2, Z-items that gate W2), controls and pairing (read-time rule), confounds,
seeds (both K2 branches), selection rule (anchor HEAD l. 750-862), falsifier, budget (budget.py
output), conventions table, decision labels, where I am not sure.

## Design decisions and why (flagged ones go to "Where I am not sure") (v1, superseded by fixer v1-v3)
- Control per wave × target family at read time; replica primary if the anchor snapshot set is
  incomplete. Reason: anchor production not launched (RUN.md; 17.7 d projection > 14 d rule).
- sd_null substitute = across-seed sd of the replica epoch-500 snapshot when g_rep cannot be formed.
- BH m fixed at delta.json counts; unrun cells enter as p = 1 (tightening).
- Selection rule = anchor runner rule, select among (a)-(c); DELTA §5.1 wording differs only at an
  edge case; dated clarification.
- 5M seed source: none exists (no [D19] C seed anywhere) -> default n = 4 ranking.
- Bop: mirror flip (Kai); tau fixed at 1e-8; |m| measured on C latents at PREFLIGHT, descriptive.
- A07 packing K not chosen here: memory canary per architecture class.

## Tried and failed / dead ends
- DELTA §5.1 cites anchor STUDY l. 386-404 at commit 5d6c3c9 for the non-degeneracy rule; at HEAD
  dde5ca7 the rule is l. 762-788. Cite HEAD.
- The anchor's A07 timing prior (112.6 s, batch 256, old quantizer) is not used: the pilot measured
  E at 218 s at batch 2,790, above the A07 prior, so the prior is not a bound for anything here.

- (fixer v1, 2026-09-27) Two-stage screen (2 seeds for all 43 cells, then 6 more for the top 14;
  170 runs against 172 at one stage n = 4) does NOT beat one stage for "all true effects in the top
  12": `review/two_stage.py` (seed 7, 10,000 reps) one-stage / two-stage 0.99 / 0.89 (σ 0.6, +1 pt),
  0.39 / 0.28 (σ 1.5, +1), 0.69 / 0.48 (σ 3.14, +3). Rejected; do not re-propose.
- (fixer v1) The arbiter-v1 wording for the ranking-mode "no" ("no cell's LCB80 / mean g exceeds the
  placebo's") was tried and fails: under the global null the placebo is one of m + 1 exchangeable
  draws, so P(no) = 1/(m + 1) (0.077 at m = 12, 0.023 at m = 40; `screen_null.py`). A count
  threshold is also powerless (shared replica, arbiter). Used instead: Dunnett-type one-sided max-t
  on the family-pooled paired sd, critical value simulated under the shared-replica null
  (P(no | null) 0.90); the placebo is the null row, rank check and validity flag.

## Fixer v1 (2026-09-27), after STUDY arbiter v1 = ITERATE (4 A, 19 B)
- Inputs: review/STUDY_arbiter_v1.md (whole), the three panel reviews, rank_sim.py, two_stage.py,
  DELTA.md §3.3, §3.4, §5.1-§5.4, §7; anchor STUDY at c2f5447 (collapse label l. 1217-1222, pilot
  amendment l. 1374-1392); anchor RUN.md at e620173 (epochs 1-10 canary, per-process memory).
- Orchestrator defaults written in as [DK1]-[DK12] ("default, Kai may override at the launch gate").
- budget.py v2: placebos, replica seeds 1-8 to 500, planning K_E = 5 with per-slot cost 218/6 kept,
  cheap version with long replicas and placebos, certification count. (4, 4): 302 runs, 176,000
  run-epochs, 1,776.3 / 3,128.7 pod-hours, 8.6 / 14.7 d at P = 10; cheap 129 runs, 79,500.
- New scripts: rank_sim.py (copied from review/), screen_null.py (placebo-wording null, Dunnett
  critical values and calibration, sd_rep ceiling 1.3 pt from the 5M recovery criterion). [superseded v5: ceiling withdrawn; label threshold T from §18]
- Experiment-log stub for this campaign rewritten in place.
- Report: review/STUDY_fixer_v1.md.

## Fixer v2 (2026-09-27), after STUDY arbiter v2 = ITERATE (6 A, 10 B)
- Inputs: review/STUDY_arbiter_v2.md (whole), STUDY_fixer_v1.md, the three v2 panel reviews and
  their scripts; anchor STUDY at 96b95f2 (regime B l. 1393-1463, pilot l. 1505-1545, pods l. 1483);
  decisions.md top entry (Kai: launch gate 1 = regime-B pilot readout; [DK6] signed);
  code/GATES.md §6 (generator engineer, via coordinator: zero-floor and always-on keys, [A20]
  build guard refuses M047-M049 and teachers, planning K E 4 / A07 3).
- screen_null.py v2: sections 4-13 (scenario rows, power, pooled-interval coverage, G3' power,
  rank-move null, rho-hat null, sd_rep ceiling, unpaired companion, placebo check, m 11/37). [superseded v5: §10 withdrawn]
  Sections 1-3 reproduce the v1 output digit for digit (section 13 printed last so the random
  stream of 1-12 is unchanged).
- budget.py v3: regime-B per-slot cost 136.5/6 = 22.75 pod-s; planning K_E = 4; K_E = 5 row;
  "packable today" row. (4,4): 302 runs, 176,000 run-epochs, 1,112.2 / 1,959.0 pod-hours,
  5.4 / 9.2 d; packable today 268 runs, 156,000 run-epochs (superseded by fixer v3: 240 runs,
  142,000 run-epochs, the four uncached cells also left out); cheap 129 runs, 502.4 / 853.1.
- STUDY.md edited in place with a v3 change-log entry (no regression ticket). Experiment-log stub
  rewritten in place. Report: review/STUDY_fixer_v2.md.

## Tried and failed (fixer v2)
- Family test, pooled sd referenced to the placebo (R1): offset-proof (0.10 at 0.707 SE) but
  false "yes" 0.14-0.32 under unequal spread and up to 0.55 under two-mode seeds. Rejected.
- Pooled sd plus a homogeneity gate (largest own sd / s_pool above its null 95th pct, 1.87-2.10)
  falling back to own sd (R3, arbiter option (b)): 0.13-0.16 unequal spread, 0.20 / 0.41 under
  two-mode seeds q 0.1 (m 12 / 40); the gate fires on only 0.16-0.34 of two-mode draws. Rejected.
- Chosen: own-sd max-t against the placebo (R2, arbiter option (a)): 0.099-0.111 at n = 4 in every
  equal/unequal row, 0.038-0.089 two-mode; power drops to 0.20 / 0.07 at sigma 0.6 (m 12 / 40).
  At n = 3 it is not calibrated under two-mode seeds (up to 0.24 at m 40, q 0.33).
- Packing: first drafted E K = 5 by the anchor's rule; replaced by the Delta canary's 90 % rule
  with planning K_E = 4 after the generator engineer's GATES.md §6 and the coordinator's note.
- Adding a section in the middle of screen_null.py shifted the random stream of later sections
  (numbers moved in the 2nd-3rd digit); moved it to the end so all quoted numbers reproduce.

## Fixer v3 (2026-09-27), after STUDY arbiter v3 = ITERATE (0 A, 10 B)
- Inputs: review/STUDY_arbiter_v3.md (whole), STUDY_fixer_v2.md, the three v3 panel reviews and
  constructive_v3_*.py; research/screen-design-literature.md (physics-researcher); GATES.md §6
  "Packs" l. 836-842; rep-C config train.ebops.pid (min_beta 1e-10, max_beta 1e-3); anchor tree
  ablation.py:483-489 (is_traced_epoch traces epoch 0); decisions.md l. 28, 80 (bundles).
- Orchestrator defaults for the arbiter's new Kai items: [DK16] top-k extension in the
  1.0-1.3 pt band; [DK17] feasibility plus descriptive T0/T0a/T1 ranking on a pause; [DK18] 350k [superseded v5: [DK17] withdrawn; [DK16] band read on s_int]
  follow-up of the training-only levers if the 5M constraint is slack. X5 stays a launch gate
  (anchor [A22] being written by the training-batch session).
- screen_null.py v3: §14-§17 appended (§1-§13 identical, diffed); §13 stores its values for reuse.
  rank_sim.py: m = 37 block appended (earlier rows identical, diffed). budget.py v4: packable-today
  240 runs; extension, pause and follow-up rows. [superseded v5: pause rows removed]
- New numbers: ranked m 11 / <= 37 (was 12 / 40); R2 crit 4.28 / 6.59 (n 4), 6.73 / 12.29 (n 3);
  multiplier 2.17 / 2.14; power 0.214 / 0.077 at sigma 0.6; unpaired 2.88 / 3.59; rho-hat null
  -0.34/+0.34, -0.18/+0.18; P(pause) 0.000 / 0.629 / 0.991 at sigma 0.6 / 1.5 / 3.14 (8 seeds). [superseded v5: §14 and P(pause) withdrawn]
- STUDY.md edited in place with a v4 change-log entry; experiment-log stub rewritten in place.
  Report: review/STUDY_fixer_v3.md.

## Tried and failed / dead ends (fixer v3)
- Ceiling criterion at the 5M list's actual m = 37 gives 1.4 pt (recovery 0.57 at 1.3, 0.52 at
  1.4; screen_null.py §15). Not moved: [DK8] 1.3 pt is a pre-registered default and the stricter
  value; recorded as an alternative in the [DK8] row. [superseded v5: [DK8] is the label threshold T, 1.3 / 1.5 pt, §18] [superseded v6: T 1.2 / 1.8 pt, floor and ten-seed rule; by median g 1.2 / 2.1 pt, designer v6]
- Variance-moderated max-t (per-cell variance shrunk toward the family pool, prior df d0 = 3),
  gated by a shape read on the 8 replica seeds (constructive v3 C1, review/constructive_v3_
  moderated.py, constructive_v3_gated.py): at m = 12 false "yes" 0.043-0.111 in every row and
  power 0.196 -> 0.427 at sigma 0.6; at m = 40 power 0.070 -> 0.289 but the 25 %-at-3x row reaches
  0.153 (the shape gate only catches two-mode seeds). Not adopted: it fails the unequal-spread
  row at 5M, and a 350k-only rule would give the two families different tests. The literature
  note does not cover moderation.
- Unpaired Welch test against a placebo at 8 seeds (constructive_v3_placebo8.py): power 0.475 /
  0.300 but false "yes" 0.14-0.18 (unequal spread) and 0.12-0.21 (two-mode). Not adopted.
- First budget.py v4 draft identified H-500 packs by their durations with an integer test that
  dropped the A07 H-500 packs at r = 1 (34,125 s is not a multiple of 500), so the extension was
  released too early (6.3 d instead of 6.7 d). Replaced by tracking (duration, H) per pack.

## Fixer v4 (2026-09-27), after STUDY arbiter v4 = ITERATE (0 A, 8 B); consolidation pass
- Inputs: review/STUDY_arbiter_v4.md (whole), the three v4 panel reviews, physics_v4_twomode.py,
  constructive_v4_modes.py, STUDY_fixer_v3.md. Scope frozen by the orchestrator: the arbiter's
  deletions, cons C2 (appendix), nothing added beyond the fix list, main text under 12,000 words.
- Withdrawn: the compute pause and sd_rep ceiling, [DK17], the four pause options, the three pause
  budget rows and budget.py's pause code, Falsifier (v) (old (vi) is now (v)), the no-family-test
  line, screen_null.py §10 and §14 and their citations. Kept: the A07 memory pause, the
  base-stability pause.
- screen_null.py v4: §10 and §14 no longer print; §10's draws are kept unprinted so every other
  number reproduces digit for digit (diffed against the v3 output; the two §3 label lines are
  reworded). §15 stores its Gaussian
  recovery rows. §18 appended: two-mode seeds (per-run and seed-shared; jump 5.4, within-mode sd 0.3),
  s_int, recovery, [DK16] extension, and the label-threshold rule. Result: T = 1.3 pt (5M), 1.5 pt
  (350k) [superseded v6: 1.2 / 1.8 pt, floor and ten-seed rule; by median g 1.2 / 2.1 pt, designer v6]. Reproduces the arbiter's scratch values: 5M median s_int 0.80 / 1.20 / 1.64 and recovery
  | s_int <= 1.3 0.79 / 0.62 / 0.51 at q 0.02 / 0.05 / 0.1 (arbiter 0.78 / 0.61 / 0.55; the q 0.1
  set is 823 of 20,000 draws); 350k unconditional 0.49 / 0.45 at q 0.33 / 0.5 (arbiter 0.48 / 0.45).
- budget.py v5: pause_keep(), paused= and the [DK17] block deleted; every other output line is
  identical to v4 except the extension band label (diffed).
- STUDY.md: v5 change-log entry; body consolidated (each rule once, [DK] labels as one-liners,
  grouped cells table, significance mode in Appendix A). Words: main 11,957, change log 2,250,
  appendix 555 (prose_lint total 14,762; was 24,788).
- Experiment-log stub rewritten in place. Report: review/STUDY_fixer_v4.md.

## Tried and failed / notes (fixer v4)
- The arbiter's q-grid condition (consecutive median s_int within 0.1 pt) cannot hold everywhere:
  the median jumps where the m x 4 matrix goes from 0 to 1 to 2 low-mode runs (0.19 pt at 5M,
  0.42 pt at 350k, below 1 pt). No q grid removes a jump in the median. Above 1.0 pt the largest
  step is 0.055 (5M) and 0.093 (350k). §18 prints both.
- Threshold rule applied literally ("wherever the conditional set is non-empty"), no minimum set
  size. At 350k, T 1.6-1.9 fail on conditional sets of 1-8 draws (q 0.39-0.44), and T 2.0-3.0 fail
  on sets of 34-18,795 draws at 0.26-0.44, so the small-set failures agree with the large ones.
  At 5M, T 1.4 fails on 201 draws (0.43). A minimum-set-size variant was not added (scope freeze);
  it is in the [DK8] "Where I am not sure" row for Kai.
- Under per-run two-mode seeds the [DK16] extension adds nothing in the band (5M 0.61 / 0.58 / 0.51
  -> 0.61 / 0.56 / 0.49; 350k 0.80 / 0.79 / 0.77 -> 0.80 / 0.78 / 0.74 at q 0.02 / 0.05 / 0.1).
  Reported in the [DK16] row; the rule itself is not changed (a design call for Kai).
- Deleting screen_null.py §10 outright would shift the random stream of §11-§17 (the fixer v2
  lesson); burning its draws unprinted avoided that.

## Fixer v5 (2026-09-28), after STUDY arbiter v5 = ITERATE (1 A, 6 B) and Kai's answers of 2026-09-28
- Inputs: review/STUDY_arbiter_v5.md (whole), arbiter_v5_tstab_gen.py / _tstab.txt / _power.py,
  constructive_v5_robust.py, STUDY_fixer_v4.md, the three v5 panel reviews (C items),
  decisions.md top entry (Kai: median g primary, [DK6] re-decided; freeze after round 6 if only B).
- screen_null.py v5: --seed and --t-only arguments; T rule with the probability floor
  P(s_int <= T | q) >= 0.01 and the minimum over ten whole-script seeds (20260927, 1-9, child
  processes); median-g hits from the existing section-18 draws (no new random numbers); 18b
  (mean vs median g), 18c (mode flag), 15a (detectable effect in pt) appended with fresh draws.
  Sections 1-17 and the section-18 grid reproduce digit for digit (diffed against the v4 output).
  Per-seed T matches review/arbiter_v5_tstab.txt for all 40 values. Result: T = 1.2 pt (5M),
  1.8 pt (350k). Run time 57 s (9 child processes in parallel).
- STUDY.md: v6 change-log entry; cap restored; median g primary; T rule and cascade; [DK16]
  above-band rows and alternative; disclosures; C rows 8-21. Words: main 12,969 (was 11,957),
  change log 2,571, appendix 555. §18d appended last: Gaussian recovery at sigma = T by median g
  0.53 (5M) / 0.61 (350k), against 0.63 / 0.66 by mean g (condition (i) holds, narrowly at 5M).
- Kept on mean g and flagged for re-simulation with median g, not changed (design values, owner's
  call): T conditions (i)/(ii), [DK16] extension recovery, rank-move null counts, rank_sim.py.
- budget.py: re-run, output identical to v5 (T moves labels only).

## Tried and failed / notes (fixer v5)
- A median-g variant of the T rule was not computed: re-deriving T on median recovery would reopen
  the rule the arbiter just fixed (a design change); listed for the owner instead.
- 18b's mean-g column comes from fresh draws and differs from the section-18 grid by at most 0.01
  (5M q 0.05: 0.54 vs 0.55); the STUDY quotes mean g from section 18 and median g from 18b.
- 350k T >= 2.0 under the floor rule fails on worst-q sets of 294-18,795 draws (recovery
  0.38-0.48), not the arbiter's 34-18,795 (those were the v4-rule sets).

## Experiment-designer v6 (2026-09-28): the four mean-g design values re-simulated with median g
- Brief (orchestrator): fixer v5 item 4's routed item. Same seed models, grids, reps and rules; no rule
  changed; mean-g values kept only where labelled as the companion; one v6 change-log line; main text
  +400 words at most. Inputs: review/STUDY_fixer_v5.md item 4, review/STUDY_arbiter_v5.md, decisions.md
  top entry.
- Method: median-g scores from the draws already made (np.median over the same seed axis) in
  screen_null.py sections 8, 15 (rank-move and the Gaussian grid), 16 and 18 (twomode now also returns
  the median-g extension hit), and in rank_sim.py's sim(); printed only in the new screen_null.py
  section 19 and a new rank_sim.py block at the end. Children emit TMSEED lines beside TSEED.
  Verified: the first 401 lines of screen_null.py output and the first 38 of rank_sim.py are
  byte-identical to v5 (diff empty); 5M unconditional median recovery at q 0.1 / 0.33 / 0.5 is
  0.85 / 0.26 / 0.26, as §18b.
- Extension by median g: the top k by 4-seed median g are extended and ordered by 8-seed median g
  (STUDY Seeds (4)); n = 6 column by 6-seed median. Rank-move: primary and companion both ranked by
  median g.
- Results (design arithmetic): T by median g 1.2 pt at 5M (all ten seeds 1.2; condition (i) binds,
  Gaussian 0.52 at 1.2, 0.46 at 1.3) and 2.1 pt at 350k (seeds 2.1-2.7; condition (ii) at q 0.5
  binds at 2.2). The 350k T moves 1.8 -> 2.1, so the [DK16] band is 1.0-2.1 at 350k.
  Rank-move thresholds by the unchanged rule: 350k T 4 / 5 / 6 at r >= 0.9 / 0.7 / 0.5 (was 3 / 5 /
  6); 5M T 12 at r >= 0.95 (was 10), and no grid T for 0.9 <= r < 0.95 (1.2 at T 15; was 15), which
  sends that band to the existing "companion disagrees at the null level" branch [superseded v7:
  label reworded to "rank-move flag not calibrated at this r (§19d)", arbiter v6 B4].

## Fixer v6 (2026-09-28), after STUDY arbiter v6 = ITERATE (1 A: leak launch condition; B1-B6 wording)
- A1-A7 applied as the arbiter specified: `code_sha` (leak-fixed bundle, f2107a04 / e90327d4 not
  launchable), gate 4 (patch 0038 rebased onto the anchor run_pack fix), gate 7 (GPU memory only),
  gate 11, new gate 14 (host-RSS slope <= 5 MB/epoch, one E and one A07 cell, >= 30 epochs), PACK
  memory sentence and Budget wall-clock sentence, Reference row "Anchor arm A" (stopped 05:31Z),
  change log v7. Each changed line carries the v7 amendment tag.
- B1-B6 in the arbiter's wording; Known limitations K1-K7 inserted verbatim before "Where I am not sure".
- Prints added (no draws, run counts or earlier lines changed): `screen_null.py` §19e (design-seed T at
  floor 0.005 / 0.01 / 0.02 / 0.05: 350k median g 2.0 / 2.1 / 2.2 / 2.3, mean g 1.9 / 1.9 / 1.9 / 2.0; 5M
  1.2 throughout, mean g 1.3), with an assert that floor 0.01 equals the rule's design-seed T; lines 1-461
  of the full run are byte-identical to `review/constructive_v6_screen_null_out.txt` (output kept in
  `review/fixer_v6_screen_null_out.txt`). `budget.py` PACK-MEM line: 4.6 / 7.1 / 12.1 GB per arm at H 500
  / 1,000 / 2,000 (baseline 2.1 GB, incident §5; 6 Gi = 6.44 GB); every other line unchanged.
- Not applied (orchestrator scope A/B/K only): arbiter v6 C rows 10-20.
- Noted, not acted on: the anchor tarball now hashes ceb174db (decisions.md 2026-09-28 ml-engineer entry,
  staged, not applied, leak not reproduced on CPU); that entry keeps 6 GiB per arm, true only to H 500.
- prose_lint: score 6 from "robust" in K2, which is the arbiter's verbatim text.

## Status
- [x] experiment-designer v6 re-simulation (median g), STUDY cascade, stub
- [x] orientation, advisor consulted
- [x] budget.py
- [x] STUDY.md
- [x] experiment-log stub

## Orchestrator notes
- 2026-09-27: STUDY review v1 = ITERATE (4 A: ranking-mode falsifier, winner's curse, resolving
  power at 3.14 pt, undeclared DELTA departures; 19 B; E at K=6 exceeds an A10 per the anchor
  canary). Fixer v1 launched with orchestrator defaults (full screen, replica seeds 1-8, replica-
  primary, mean-g ranking, sd ceiling, baselines + teachers, K by memory canary, 10 pods, no tau [superseded v5: the sd ceiling is withdrawn]
  scan, placebo A/A cells), each flagged "Kai may override".
- 2026-09-27: v2 panel in. Physics: approve after A1 (max-t assumes equal variances; false-yes
  0.16-0.28 under heterogeneity), A2 (placebo depends on GPU determinism), A3 (one replica loss
  empties the ranked list). Constructive: same A1; B1 unpaired companion; B2 determinism canary.
  Critical: A1 Kai's [D15] regime B (trace every 10 epochs; "Delta at 10 after this campaign's
  epoch-500 readout"; ~27 pods) ignored; A2 family test vs replica not placebo (offset 0.7 SE ->
  false-yes 0.41); A3 non-inferiority has no power. Kai's timing overrides [DK4]: Delta waits for
  the anchor epoch-500 readout. Arbiter v2 running.

## ml-engineer, PREFLIGHT build half (2026-09-28)

Plan (written before any build):
1. `code/apply_anchor.sh` into scratch (pins 42abed4b), then `bundle/freeze_delta.py` tars the
   untouched `code/` tree plus `code/campaigns/delta0926/` = `index.json` (all 582 rows, byte-identical:
   packs pin its sha and run_pack launches by row position), `configs/W2/**` only (briefed: what the
   pods need), the three `delta_*_packs.json`, `canary_k.py`. Deterministic tar as the anchor's
   `freeze.py` (PAX, mtime/uid/gid 0, sorted, gzip mtime 0 level 9). Asserts: each packed name
   resolves to a shipped file with its `config_sha256`; `sha(index) == packs.index_sha256`;
   `rss_gate_limit_mb == 2100 + 5 H`; base64 < 1 MiB. Freeze run twice, shas equal.
2. Manifest sha re-derived with the Delta `run_study.manifest()` globs (top level, `bnhgq2/`,
   `newmods/`), confirmed by `run_study.manifest()` under the pins from a fresh extraction.
3. Every check runs from a fresh extraction of the tarball, never the build tree.
4. Re-run (<= 15 min): manifest sha; pytest run_pack (gate 4) and diags (gate 9); validate_cfg on
   every W2 config (strict keys); gate_cpu on base replicas, placebos, M020, M006; placebo identity
   assertion (new script, none existed); cache-identity check against the anchor's n64 cache config;
   horizon truncation LR / traced-epoch check (gate 5) if time. Cited not re-run: 142-pair gate,
   invariance 19/19, slug tests, floors (GATES.md §7), tied to this bundle by git log.

DECISION: ship W2 configs only (312) with the full 582-row index. ALTERNATIVES: all 582 configs
(fits, ~424 KB tar per GATES §6; lets `run_study.py preflight` iterate every row). Chosen per brief;
the preflight stage must not be run on this bundle.
DECISION: this bundle is the canary / gate-14 bundle. Packs are PLANNING; after `k_result.json` the
packs change, so production needs a re-freeze (new bundle sha and ConfigMap, same code manifest sha).

Outcome (ml-engineer, 2026-09-28): bundle e6fc6cd9…67fb (334,471 B, base64 445,964 B, 576 files), manifest
300be87b…467c, ConfigMap kai-delta0926-code-e6fc6cd921; freeze deterministic across two independent
apply_anchor builds. Re-run on the extraction: manifest sha, pytest run_pack 29 passed, diags/bop/linformer
10 passed, strict keys 312/312, key diff 0 outside, placebo 8/8, diag on/off 2/2, horizon 27 OK (function
level), cache identity 252 OK, gate_cpu 7/7. PREFLIGHT.md has the gate table.
Tried and found: running Delta scripts from `campaigns/2026-09-26-delta/code/` shadows the tree's
`newmods/` (script dir first on sys.path); `newmods/deepsets.py` differs from the 0023-patched copy, so the
GATES §7 M006 line (20,742 params) was built on the unpatched module; from the bundle it is 20,750. Run gate
and floor scripts from a copy outside that directory (done here) or with `python -P`.

## cluster-ops, PREFLIGHT lint half + RUN (memory canary only) (2026-09-28)

Plan (written before apply): this task is only STUDY gates 7/14, the GPU memory canary
(`kai-delta0926-canary`, 1 pod, A10, phases E-k4/E-k5/A07-k3). Wave-2 full launch waits for gate
1 (anchor pilot epoch-500 readout) and is out of scope. Steps: (1) `nrp_doctor status` — confirm
cluster clear of our other pods before applying (2) verify configmap.json's decoded sha256 == the
bundle sha256 in PREFLIGHT and == the tarball on disk (3) fill `__CONFIGMAP_NAME__` /
`__BUNDLE_SHA256__` / `__MANIFEST_SHA256__` into a copy of `delta-canary-job.json` under this
campaign's `manifests/`, lint it, do not touch training settings (4) confirm the pod reads the
anchor's gated 90/10 n64 cache already on `kai-data` (`/data/chang-n64-20260926`) via the
completed cache Job's own log (`kai-chang0926-cache-c5d6f0`), which prints `y_val` sha
`63049d9b…7709` matching PREFLIGHT's gate-3d value; re-confirm from inside the live pod once
running (5) apply ConfigMap then Job, watch to Running, watch for `MANIFEST_SHA_OK`,
`GPU_GATE_PASS`, `CACHE_READY`, `ARM_STARTED` x N per phase; check `POD_MEM` against each phase's
`BNJ_RSS_GATE_LIMIT_MB` (E 7,100 MiB, A07 12,100 MiB) at epoch ~10-20 (6) write PREFLIGHT lint
section and start RUN.md; do not launch anything beyond this one canary Job.

Flagged for Kai (not a decision I can make): `activeDeadlineSeconds: 57600` (16 h) on the Job vs
3 sequential 110-epoch phases; at the training-batch pilot's observed ~220 s/epoch (K=6, N64) the
budget is tight (330 x 110 x 3 ≈ but per-K rate unknown for K=4/5/3) — flagged in RUN.md once
early-epoch rate is read, not edited here (mutable on a live Job, his call). Also flagging: gate
14's "Delta cell" per the brief note is satisfied only by replica configs carrying Delta's
always-on keys, not a standalone Delta-cell-specific canary — noting for Kai to judge sufficiency.

## fixer, REGRESSION_TICKET (canary NaN on c6017) → gate 15, discriminators, canary-v2 (2026-09-28)

Changed (nothing applied, nothing committed):
- new `campaigns/2026-09-26-delta/code/fingerprint_check.py` (gate 15).
- `manifest_wave2.py`: `gate15_lines()` goes into `header()` (every pod), canary root `canary-v2`,
  `NotIn` c6017 on the canary, `NODE_NAME` from the downward API, the canary's `FAIL=1`/exit 7 folded in
  from the hand-edited v1 copy. The t0/cells packs regenerate byte-identical; only the job wrappers and
  the canary packs' run roots change.
- `WIRING.md`: gate-15 bullet and canary-v2 paths.
- `bundle/freeze_delta.py` ships the script. Re-frozen as 705a554b. The e6fc6cd9 files are copied beside
  it with the sha in their names.
- new `manifests/build_gate15_manifests.py` → `delta-canary-v2-job.json`, `discrim-c6017-job.json`,
  `discrim-other-job.json`.
- PREFLIGHT gate 15 row + section; REGRESSION_TICKET §7; regression_log line.

Tried / notes:
- The canary v1 filled copy (e6fc6cd9) had E-k5 = rep-A s1-5 at stage pilot. The current generator has
  P-350 s1-4 + rep-A s5 at H 500. So v2 is regenerated, not the old copy edited.
- Offline lint errors ("NO product reachable") come from having no node list. The online lint is
  cluster-ops'.
- First `--allow-cpu` run from the Delta code dir needed the `sys.path` guard: that dir holds an
  unpatched `newmods/`, the same shadowing as gate_cpu.py.
- Open: the W&B `stage_run_id` collision on canary-v2 (stage canary reused) and the `run_pack.py`
  pod-level epoch-0 rule. Both are routed; see PREFLIGHT "Gate 15".
- `GATES.md` l. 866 and l. 1196 still name `/data/delta-20260927/canary/`. They are the v1 design record
  and are left as they are. WIRING.md and the generator carry `canary-v2`.
