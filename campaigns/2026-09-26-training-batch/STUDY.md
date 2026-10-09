---
id: 2026-09-26-training-batch
date: 2026-09-26
type: training-batch
status: frozen
question: What seed-mean ROC-test top-1 accuracy does the binary-weight N=64 tagger (Chang-sized architecture d24, 2 heads, 1 block, FFN 32, no PE [D21]; activation, softmax-output and softmax-table quantizers matched to Chang's code, [D19]) reach when trained with the Sun et al. recipe (7,000 epochs, batch 2,790, LR 3e-3 cosine restarts every 500 epochs, pT >= 2 GeV constituent gate, no sample weights) to a 350k EBOPs target, does it reach that budget non-degenerately in at least 6 of 8 seeds, what is its distance to the published single-model 79.4 % Deep Sets (HGQ) row of arXiv:2510.24784, and does that recipe beat our own recipe at the same target? Second wave (Kai request, 08:40, 2026-09-27): at iso-EBOPs (350k), does the binary arm A lose accuracy against the same model with learned-width HGQ weights (arm NB), and where does Sun et al.'s own xfm model on our split (arm H) sit against both? FP32-E (2026-09-27, Kai request (second set)): what is A − FP32-E, A binary at 350k against the same E model in unconstrained FP32 (arm FP32-E, a labelled package, not iso-EBOPs)?
supersedes: 
superseded_by: 
code_sha: bundle 42abed4b5d2e...c258c0, manifest 041f981a...bd42 (ConfigMap kai-chang0926-code-42abed4b5d; regime B, leak-fixed; see PREFLIGHT.md)
wandb: BNJetTag-ChangRecipe / chang-n64-20260926
results: 
---

**Frozen 2026-09-28 (Kai).** After STUDY review iterations 1-10 (ESCALATE at the cap, answered by Kai: K1-K3) and the post-escalation landing check v11 (`review/STUDY_critical_v11.md`), Kai froze this STUDY with the C items listed in the change-log entry "after STUDY v11 landing check" disclosed, not fixed, and accepted removing arm B from the K1 fire list (B's ratio is a descriptive caveat on A - B). Any further change is a dated amendment decided by Kai (`.claude/memory/decisions.md`, 2026-09-28).

**Dated GPU amendment, 2026-09-28 (Kai).** The A10-only restriction below records the already-running regime-B pilots and the earlier production plan; it no longer governs future launches. For production, select the fastest schedulable GPU product by the measured throughput, utilization, memory and matched-product gates in [the GPU selection policy](../../docs/infrastructure/gpu-selection-policy.md). The A10 pilot timings cannot certify another product: repeat the timing/memory canary and fingerprint/EBOP checks on each chosen product. Keep paired arms at each seed on one product, record that product, and recalculate the 14-day projection. The model, recipe, selection and analysis rules remain frozen. Existing pilot Jobs and their manifests retain their historical A10 assignment.

Change log.
- v1 (2026-09-26): first design, reviewed in `review/STUDY_*_v1.md`.
- v1, revised after `review/STUDY_arbiter_v1.md` (ITERATE, 2026-09-26): the primary question
  is descriptive (accuracy reached and distance to 79.4 %, not a test of binary weights) (#1);
  arm H and an in-house non-binary arm are pre-registered follow-ups and Kai decisions (#2);
  resolving power stated at the same-N archived sd, with a pre-registered consequence [D13]
  (#3); tie-break order enforced by [A13] (#4); reference uncertainty quantified in [L1] (#5);
  comparand fixed at 79.4 % unconditionally (#6); attention diagnostic split into Q/K, V and
  entropy (#7); pairing, infeasibility, divergence and stability rules (#8); [A13]-[A19]
  added (#9, #11, #13, #15, #25); expected [D15] branch and pod count as a Kai decision (#10);
  epoch-matched A1000 − R and D1000 − R (#12); [D1] rationale dropped (#14); C items #16-#27.
  Fixer completion pass (`review/STUDY_fixer_v1.md`): A − F pairing stated in Seeds (#15);
  [A16] and "Where I am not sure" point to `review/STUDY_investigation_350k.md`, and the 5M
  wording (#27) now says the reason is recorded and post hoc; "Downstream use" names the
  method-atlas wave 0 anchor.
- v1, revised after `review/STUDY_arbiter_v2.md` (ITERATE, 2026-09-27), design amendments dated
  2026-09-27:
  - **[D19] quantizer amendment** (#1-#3): every arm uses Chang's activation, softmax-output and
    softmax-table quantizers (WRAP datalane, 0 bits reachable; tables kbi `SAT_SYM`, ≥ 4 bits).
    Reason: under our current quantizer (SAT with k = 1, fixed 10-bit softmax output, fixed
    softmax tables) every 350k and 175k arm has a static EBOPs floor above its target
    (A07 4,559,008; traced 4,580,398, amended after [A7] trace 2026-09-27). Recorded as a zero-GPU finding ("Static floor of the current quantizer").
    [A7] rewritten, [A20] added, [L8] added, fidelity rows added.
  - Timing basis re-sourced per run and per N (#4); expected [D15] branch is now "fits 14 days
    single-wave"; the pod count is the binding Kai decision.
  - Canary becomes canary plus epoch-500 feasibility pilot with a pre-registered rule (#5, #6);
    [D13] defined when fewer than 2 A seeds are feasible. Orchestrator addition: C′-s1 replaces
    F-s1 in the pilot pod, so the pilot reads both branches of [D19]; fallback if [A20] needs an
    HGQ2 pin change.
  - Arm B moves to the E architecture at 250,000 EBOPs, [D6] amended (#9); A − B dropped.
  - Stability claim is a count rule; McNemar p reported outside the Holm family (#7).
  - Width quantity and Deep-Set wording (#8); survivor bias carried to A − 79.4 (#10); Fig. 2
    per-class AUCs added (#12); arm H FLAG inherits [D19] (#11); C items #13-#18.
- v1, **amended after [A7] trace (2026-09-27)**, before review v3. Source: ml-engineer's CPU
  trace on a synthetic sample (`code/evidence/static_floors_trace_step2.json`,
  `static_floors_arms_s1.json`; not results) and `plan.md` "ml-engineer code plan".
  - Traced floors replace the arbiter arithmetic everywhere it was stated as the floor: current
    quantizer A07 4,580,398 (arbiter 4,559,008); [D19] A07 343,053 / 1,005,741 (0-bit /
    1-bit-alive; arbiter 326,656 / 989,344), E 171,526 / 619,198 (arbiter 163,328 / 611,000),
    F 343,053. A07 headroom at 350k is 6,947 EBOPs (was 23,344), E 178,474 (was 186,672).
    Derived ratios recomputed (screen minimum 1.1 % above the old floor, 5M 9.2 % above it).
  - [A20] builds on the pinned `hgq2==0.1.9`; the C′-only fallback is not triggered.
  - "Live sign-only channel" corrected: a SAT channel at its floor is billed 1 bit and outputs
    exactly 0 at inference.
  - New pre-registered EBOPs trace sample [D20] (the 256-jet per-epoch trace is replaced) and
    certification of the selected checkpoint's EBOPs.
  - Pilot composition restated for regeneration; B = E architecture at 250,000; patch 0011
    adopted for A − F pairing, [A17] checked at all 8 seeds.
  - Primary architecture moved to a before-production Kai row with a designer recommendation
    (E); A07 stays the default primary until Kai answers. Pilot rules updated.
- v1, revised after `review/STUDY_arbiter_v3.md` (ITERATE, iteration 3, 2026-09-27), fixer pass
  on the orchestrator's instruction; Kai's launch-gate answers of 2026-09-27 08:40 PDT
  (`.claude/memory/decisions.md`) folded in:
  - **Non-degeneracy condition** (#1): a checkpoint is feasible only if (a) traced EBOPs ≤
    target, (b) EBOPs above the arm's traced 0-bit floor > 0 and (c) validation top-1 accuracy >
    p_maj + 5 · √(p_maj (1 − p_maj) / 62,000), p_maj computed at PREFLIGHT. Applied to selection,
    budget claim, recipe branches, the epoch-500 sd gate and the pilot. "EBOPs above the 0-bit
    floor" is reported beside every EBOPs number.
  - **[D21] 350k ladder moves to E as a unit** (#2), Kai-confirmed 2026-09-27: A, B, D, F and R
    on E (F = E + learned PE); C stays A07 at 5M; the former A07 arm A becomes the descriptive arm
    **A07-350**. The former arm E is now arm A. 56 runs, 7 arms, 40 on E. Holm set, pairing,
    ladders, pods and the pilot rewritten. Dated amendments in place: [D1], [D4], [D6], [D13],
    [D16], [D18], [D19], [D20], [A7], [A14], [A17], [A20], [L2]; [A21] added.
  - Paper's ≥ 1-bit attention rule: fidelity row corrected, zero-GPU static finding added, [L2]
    sentence (#3). [D20] made a named PREFLIGHT gate [A21] (#5). Softmax tax beside every
    distance to 79.4 (#4). Stability and recipe-on-feasibility wording (#6, #7). Paired
    resolving power at zero correlation (#8). REPRO-CHANG xfm-n64 in the architecture FLAG (#9).
    One-head arm E1 enters the pilot only if [A7] traces it feasible (#10; E1 trace placeholder,
    filled in the 2026-09-27 final pass below). C items #11-#18. The per-sentence "amended after [A7] trace" tag is
    kept only in tables and [D]/[A] entries.
  - Kai decisions recorded in "Where I am not sure": [D19] and [D21] confirmed, 8-10 pods in one
    wave, arms H and NB requested (second wave, designed separately).
- v1, **amended 2026-09-27 (Kai request, 08:40)**, experiment-designer: arms **H** (Sun et al.'s
  jsc150 `xfm` on our split, [D23]) and **NB** (arm A with learned-width kbi weights, [D22]) are
  pre-registered as a **second wave** [D24], launched when their code passes the CPU gates
  ([A22]-[A24]), same seeds, cache and schedule. New: section "Second wave: arms H and NB";
  weight-type claim and second-wave Holm family {A − NB, H − NB} (Falsifier); H − A reported as
  the algebraic sum, no p; H has no binding reference (§6.8 row); confound 12; Seeds pairing;
  evaluations; figures; Budget "Second wave" (16 runs, 72 in total, 4 pods, cheap version NB
  only); [L9], [L10]; decision table and FLAG blocks. Question, Null and Bearing gain only the
  A − NB comparison. The E1 trace placeholders were untouched in this pass.
- v1, **amended 2026-09-27, final pass before review v4**, experiment-designer. Sources: `plan.md`
  ("ml-engineer code plan, part 2"), `code/evidence/static_floors_fix6_a07_e_e1.json`,
  `trace_cost_cpu.json`, `cpu_gate_d21.log`, `a17_pairing_d21_8seeds.json` (CPU, synthetic, not
  results).
  - E1 trace placeholders filled (9 in the body): E1 0-bit 85,763, 1-bit-alive 533,435, narrow
    282,371, full 392,963; headroom at 350k +264,237 / −183,435 / +67,629 / −42,963. Arbiter's A07
    and E paper-rule sums confirmed exactly; only the softmax term splits per head. E1-s1 is in
    the pilot, B-s1 is not (pilot pod A-s1, A-s2, D-s1, A07-350-s1, C′-s1, E1-s1). E1 is the only
    traced architecture feasible at 350k under the narrow datalane reading; that rule stays a Kai
    row.
  - [D25] `i_decay_speed` 1e-3 as jsc150 (`quant.i_decay_speed: 0.001`); fidelity row added,
    [A21] updated.
  - Trace-cost risk to the expected [D15] branch (≈ 15.1 d at the prior if the CPU ratio holds)
    with a pre-registered canary rule; nothing pre-approved.
  - `nondegenerate_threshold.py` named as the PREFLIGHT computation of p_maj + 5 · SE.
  - Checked, no change needed: [D21] and A07-350 at 8 seeds (7 × 8 = 56) were already stated;
    `cpu_gate_d21.log` (`PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`) and
    `a17_pairing_d21_8seeds.json` (A, B, D, R paired with F at 8 seeds) predate [D25] and are
    re-run under it. The CPU re-run under [D25] is done (`cpu_gate_d25.log`,
    `a17_pairing_d25_8seeds.json`; note added by arbiter v5 fix 5).
- v1, revised after `review/STUDY_arbiter_v4.md` (ITERATE, iteration 4, 2026-09-27), fixer pass.
  Text only; no design, arm, seed, target or selection change. Edits, by arbiter fix:
  - #1 certification failure: Selection rule "EBOPs certification" (blocks VERIFY for the arm;
    unresolved = "no accuracy number" in k, both EBOPs per seed; same `ebops_trace_sample` and
    `ebops_trace_batch`); "No feasible checkpoint" and "Arm summary" bullets.
  - #2 H on the traced clone: "H, defined [D23]"; H fidelity row "EBOPs for selection"; [A23]
    per-epoch bullet and new CPU unit tests; Kai row "H trace protocol".
  - #3 budget-claim demotion: Question; Falsifier "Budget claim" (count wording, threshold (c)
    printed, about 0.21, per-seed accuracy beside the count); pilot A rule. No new floor.
  - #4 attribution: "Paper's ≥ 1-bit attention rule", Primary measurement, [L2] (2-head E
    architecture, any weight type; A − NB unaffected).
  - #5 figures: primary-measurement figure and recipe-ladder paired-gap panel (Falsifier, Figures).
  - #6 A − NB headline (lower 95 % bound first; Sloot prior) and #8 resolution (smallest
    resolvable gap printed; sizing formula and table; epoch-500 sd_diff readout > 1.2 pt to Kai):
    Falsifier, weight-type claim; Budget, second wave; Kai row "extra A/NB pairs (cap)".
  - #7 second-wave epoch-500 rule for NB and H: Budget, second wave.
  - #9 stability: feasible-degenerate and low-accuracy-outlier counts (3 pt below the arm median,
    descriptive) beside the divergence count.
  - #10 scope sentence in "Bearing on the thesis"; Kai rows "FP32 E arm" and #11 "NB in wave-1
    seed blocks".
  - #12 C items: [D25] reworded as a PREFLIGHT gate (fidelity row, [D25], [A21]; patch 0024 not in
    `code/patches/` when this pass ran) and logged in `decisions.md`; [D20] "PID signal" and [A21]
    cite `ablation.py:698-703`; stale "not staged" [D20] text (confound 10, [D20], [A21]); selection
    sentence and W&B `budget_met` semantics; [A19] sensitivity matches the code; [A17] body cites
    the 8-seed evidence; F floor cites `cpu_gate_d21.log`; pilot wall time with and without the
    trace (15.6 h / about 26 h); init EBOPs named by sample, PREFLIGHT value = in-pod epoch-0
    trace ([A20]); "confirmed exactly" replaced where it was an identity; ROC figure split by
    budget; A07 minimal-path sentence spelled out (2,048 + 2,048 + 4,096); binary scale factor in
    EBOPs ([L2]); WRAP-overflow label rule (threshold left to the designer); A − A07-350 Holm note
    (move is a designer question); tag "Kai request, 08:40" kept only on the change log, the
    second-wave header, [D22]-[D24] and the frontmatter question; superseded FLAG block shortened; Kai rows say what they
    block; per-run selected epoch and cycle index added to the figures.
  - Designer follow-up (experiment-designer, 2026-09-27), the two items the fixer left open:
    physics v4 C6, WRAP-overflow label threshold set at 0.1 % of a quantizer's ROC-test values,
    descriptive only (Falsifier, attention-state paragraph); arbiter v4 #25, A − A07-350 moved out
    of the Holm family and reported as an interval with no p, Holm now across four secondary gaps
    (Falsifier, comparisons table, [D21], conventions row).
- v1, revised after `review/STUDY_arbiter_v5.md` (ITERATE, iteration 5, 2026-09-27), fixer pass.
  Text only, arbiter's verbatim wording; no design, arm, seed, target, pilot or selection change.
  New tags read "arbiter v5 fix N" (one scheme, C #15). Edits, by arbiter fix, in the order applied:
  - fix 5 (#5, #8) [D25] and the C′ gate: fidelity rows "WRAP range update" and `i_decay_speed`,
    [D25] body, [A21] ("set by patch 0024 (staged, tree ac5a5c86; ...); PREFLIGHT re-asserts on
    the shipped tree"; C′ carries no key and records an empty set, `cpu_gate_d25.log:116`); note
    in the [A7]-trace change-log entry that the [D25] CPU re-run is done; one-line dated
    correction appended to the [D25] entry's Check line in `decisions.md`.
  - fix 4 (#6) A07-350 expectation: Falsifier "A07-350" (per-constituent layers only, 2,048 EBOPs
    per 1-bit input channel; post-pool head reported separately); mismatch clause there and in the
    pilot's A07-350-s1 bullet. No other "d32 dense" site in that sense (l. 175 stays).
  - fix 1 (#1) stability: seed range, low-accuracy count against the arm's best seed, A-against-D
    discordant counts; median reference dropped ("All are descriptive").
  - fix 2 (#4, C #14) A − NB headline, both branches of L; "the 95 % half-width" label.
  - fix 3 (#2, #3, #11) Resolution paragraph after the sizing table (formula governs; proxy a prior;
    wave-2 epoch-500 packet binds, no mean gap or sign; extra A seeds enter A − NB only); table rows
    1.19 / 1.57 / 1.87 / 2.01 / 2.13 pt; 1.20 → 1.19 pt in Seeds and "Where I am not sure";
    second-wave epoch-500 rule; Kai row "extra A/NB pairs (cap)" status. "1.2 pt" in the v4
    change-log entry left as history.
  - fix 6 (#7) Scope: REPORT-use restriction on "close to full precision".
  - fix 7 (C #9, #10, #12, #13, #16): reference-table source `cpu_gate_d25.log`; [A7] arms file
    holds the [D21] set; `budget_met` semantics and k's source; `xfm` taken out of the "any weight
    type" sentence (three sites) with the key_dim 16 clause; figure lines named Linformer and MHA;
    optional #16 ([A14] on the selected A-s1 at VERIFY) added under "EBOPs certification". #18
    (sign-flip logging) is code, left to ml-engineer.
  - "Where I am not sure": Kai's second set of answers (`decisions.md`, 2026-09-27): pilot starts
    now under arbiter v5's conditions (new row); paper-rule variant, arm B and base-architecture
    rows Kai-confirmed defaults; H β control and H trace protocol Kai-confirmed defaults;
    second-wave pods: overlap Kai-confirmed, about 14 pods (also the second-wave "Overlap" bullet,
    its FLAG block and the pod-count row); FP32 E arm "Kai-added 2026-09-27, 8
    seeds; to be designed" (the experiment-designer adds the arm; the Scope sentence "An FP32 E arm
    is a Kai option" is left for that pass).
- v1, **amended 2026-09-27, Kai request (second set)**, experiment-designer: arm **FP32-E**
  added (`decisions.md` 2026-09-27, "FP32 E arm added, 8 seeds, full 7,000 epochs"). Design
  addition, no change to any wave-1 arm, seed, target, pilot or selection rule; 80 runs (was 72).
  Edit sites (line numbers after this pass, at 54bf3e7):
  - frontmatter `question:` (l. 6); Question (l. 225); Null, H0-precision (l. 248);
    Bearing, A − FP32-E sentence (l. 269); Scope rewritten (l. 274; the v5 "Kai option"
    sentence, formerly l. 247).
  - Second wave: arms-table row (l. 482); Total 24 / 80 (l. 484); "FP32-E, defined [D26]"
    (l. 488-521); pairing-table rows A vs FP32-E, NB vs FP32-E (l. 588-589).
  - Confound 12, A − FP32-E bullet (l. 645); Seeds pairing sentence (l. 669).
  - Arms, Total sentence (l. 349).
  - Selection rule: rule (b) floors clause (l. 718); evaluations bullet (l. 806).
  - Falsifier: intro (l. 813); second-wave Holm family (l. 915); "Precision package" paragraph (l. 979);
    figures line (l. 1067).
  - Budget, second wave: Runs (l. 1277); Pods (l. 1284); canary (l. 1300); FP32-E
    bullet with the wave rule, pods, cost, epoch-500 rule and cheap version (l. 1318); W&B
    names (l. 1348).
  - Conventions rows: Seeds and intervals (l. 1358), Validation checks 1-6 (l. 1361),
    quantization checks 1-4 (l. 1367), seeds ≥ 3 (l. 1371), binary is the thesis
    (l. 1372), W&B group (l. 1376).
  - Decision labels: [D24] amendment (l. 1534); [D26] (l. 1554); [A25] (l. 1773).
  - Where I am not sure: second-wave pods row (l. 1861); FP32 E arm row (l. 1864); NB in
    wave-1 seed blocks row (l. 1866); DECISION block [D26] (l. 1950).
- v1, revised after `review/STUDY_arbiter_v6.md` (ITERATE, iteration 6, 2026-09-27), fixer pass.
  Text only, arbiter's verbatim wording; no change to any wave-1 arm, seed, target, pilot or
  selection rule; wave-1 pod composition changes only after a measured K=7 re-canary. New tags
  read "arbiter v6 fix N". Line numbers after this pass (line numbers at 99f0a2d):
  - fix 1 (#1) survivor bias: "Paired gaps" bullet (l. 818-820); A − NB headline (l. 978-987);
    precision-package headline (l. 1046-1057); A/FP32-E feasibility counts with McNemar
    (l. 1066-1067).
  - fix 2 (#2) K=7 re-canary: Budget, FP32-E launch rule (l. 1410-1416; the K=8 clause points to
    the same re-canary); Overlap bullet (l. 1381-1382, NB at K=7, neighbourhood); Kai rows FP32 E
    arm (l. 1983) and NB in wave-1 seed blocks (l. 1985); [D26] DECISION block (l. 2075).
  - fix 3 (#3, #4, #5, #19, #21 part): precision claim string and both headline branches
    (l. 1036-1046), "at least |U| pt" gated on the Holm verdict in both headlines (l. 975-976,
    l. 1043-1044); Scope (l. 316-317); Question (l. 265) and frontmatter `question:` (l. 6);
    Bearing (l. 309). Null carried no "close"; unchanged.
  - fix 4 (#6) FP32-E plausibility line (l. 1069-1073); FP32-E epoch-500 rule prints FP32-E's
    and A's seed-mean validation accuracy (l. 1431-1433).
  - fix 5 (#7) quantizer-variable check: FP32-E "Checks replacing the binary gate" (l. 554-557),
    conventions row "Validation checks 1-4" (l. 1460), [D26] body (l. 1651-1654), [D26]
    DECISION block (l. 2071-2073); [A25] bullet on the pinned hgq2 0.1.9 (l. 1901-1902).
  - fix 6 (#8) `binary_gate`: [A25] bullet (l. 1903-1904), [A22] bullet (l. 1837-1838),
    conventions row "Validation checks 1-4" cites both (l. 1460).
  - fix 7 (#9) [A25] pairing count `n_shared == 15` (l. 1891-1896; confirmed in
    `code/evidence/a17_pairing_d25_8seeds.json`).
  - fix 8 (#10) [A25] stripped keys listed and the PREFLIGHT diff (l. 1876-1879).
  - fix 9 (#11) conventions rows Configurations, Cost accounting, Selection under a budget
    (l. 1457-1459).
  - fix 10 (#12) [A26] attention-entropy readout (l. 1905-1914; script and tests by ml-engineer,
    in parallel); "softmax tap" replaced (l. 1111-1112); pilot readout prints entropy as
    "pending" if [A26] is not ready (l. 1267-1271).
  - fix 11 (C items): [D24] DECISION block amended (l. 2084-2085); second-wave Cost bullet
    (l. 1386); Holm price of the third member (l. 965-968); second-wave Launch gate with [A25],
    per-arm launch and the expected gate line (l. 1363-1371); splices in the stability paragraph
    (l. 940-941) and at the `i_decay_speed` sites (l. 434, 435 (neighbourhood), 1636-1637,
    1808); second-wave figure puts A − FP32-E and NB − FP32-E in their own panel (l. 1146-1148);
    designer [D26] entry in `.claude/memory/decisions.md`. Optional C items (per-class paired
    AUC gaps, decomposition stack, FP32-E band) not applied.
  - C item, rename relayed from the Delta session: `campaigns/2026-09-26-method-atlas/` is now
    `campaigns/2026-09-26-delta/` (Kai, 2026-09-27, `decisions.md`); "Downstream use"
    (l. 323-329) and the [A22] citation (l. 1820). Change-log history (l. 28) keeps the old name.
- v6, text pass after PREFLIGHT gate v2 (`review/PREFLIGHT_critical_v2.md`, PASS with B flags,
  2026-09-27; fixer), no design change (line numbers at 5c49230):
  - flag 2: W&B run-id rule amended to sha256(stage + NUL + config name)[:12], group by
    `BNJ_STAGE`, production manifests set `BNJ_STAGE=production` (patch 0026) (l. 1473-1480);
  - decision 6: CPU→GPU certification re-run rule, four conditions, cited from
    `decisions.md` (Budget, pilot, l. 1288-1296; Selection rule "EBOPs certification", l. 799-801);
  - flag 3: CPU dry run of the whole readout before epoch 500 (l. 1297-1301);
  - flag 4: replay-check re-run on the original GPU class after a cross-class re-create (l. 1302-1306).
- v1, revised after `review/STUDY_arbiter_v7.md` (ITERATE, iteration 7, 2026-09-27), fixer pass:
  arbiter v7 fixes 1-9; no change to any arm, seed, target, pod, K, selection or certification
  rule. Text only, arbiter's verbatim wording; new tags read "arbiter v7 fix N". Line numbers at
  fba27d5:
  - fix 1 (#1, applied first) [A26] definition, row-renormalized primary, raw value and row sums
    beside it, tests on the primary with the pytest pass line (l. 2018-2024); "(row-renormalized,
    [A26])" in the attention-state list (l. 1186) and, by neighbourhood, the pilot readout (l. 1345).
  - fix 2 (#2) plausibility gate replaced in full: four-item record closes it, 79.4 % limb and the
    archived FP32 print removed (l. 1144-1151).
  - fix 3 (#3) Holm m under dropouts: first-wave paragraph after "counts only." (l. 1004-1009; the
    A − A07-350 sentences now open the next paragraph), second-wave paragraph after "(arbiter v6
    fix 11)." (l. 1028-1033); conventions row "Seeds and intervals" (l. 1560).
  - fix 4 (#4, #5) both-failed count in "Paired gaps" (l. 863-866); pair count and
    'surviving-minimum imputation' label in the A − NB headline (l. 1048-1053) and the
    precision-package headline (l. 1123-1128).
  - fix 5 (#6) W&B stage group per wave, patch 0026 `stage_group` (l. 1547-1549).
  - fix 6 (#7) Bearing: comparands already DSP = 0 in Table 1 (l. 346-352).
  - fix 7 (#8) paired macro-AUC and per-class AUC gaps: weight-type claim (l. 1102-1105),
    precision package (l. 1140-1143), second-wave figure text (l. 1223-1224).
  - fix 8 (#9) budget claim screens controller failure, divergence, collapse (l. 923-926).
  - fix 9 (C items): (a) Kai row extra A/NB pairs (l. 2095); (b) Kai row NB in wave-1 seed
    blocks (l. 2098); (c) second-wave Cost (l. 1486); (d) `certify_ebops.py:89-91` (l. 1363)
    and the decisions.md entry name (l. 833-834, l. 1358-1359); (e) superseded run-id sentence
    (l. 1542); (f) "(line numbers at 99f0a2d)" on the v6 fixer entry (l. 210), and by
    neighbourhood "at 54bf3e7" on the FP32-E designer entry (l. 187) and "at 5c49230" on the
    PREFLIGHT gate v2 entry (l. 247); (g) gate counts per bundle (l. 1468-1470). Optional C items
    (cons C5 real-key entropy, phys C2, C3, C5, C7, cons C6, C7) not applied.
- v1, revised after `review/STUDY_arbiter_v8.md` (ITERATE, iteration 8, 2026-09-27), fixer pass:
  arbiter v8 fixes 1-5; pilot composition amended (fix 2); no change to any arm, seed, target,
  batch, selection or certification rule; production packing left to Kai. Arbiter's
  verbatim wording, applied in the order 2, 3, 1, 4, 5 (line numbers at 1115121):
  - fix 2 (#2) dated pilot amendment at the end of the pilot "Pod." bullet (l. 1374-1394); canary
    stability rule read per pod (l. 1469); Kai row "pod count" status cell (l. 2158); new
    row "wave-1 packing after the A10 out-of-memory" (l. 2159).
  - fix 3 (#3) collapse label after the entropy bullet (l. 1217-1228); pilot readout attention
    state names the label (l. 1412-1413).
  - fix 1 (#1) FP32-E distance worded FP32-E − 79.4 (l. 1178-1179).
  - fix 4 (#4) 80 %-power detectable gap in "Not falsified" (l. 1113-1119); "Resolution" readout
    packet (l. 1100-1101); Kai row "extra A/NB pairs (cap)" (l. 2167).
  - fix 5 (required C): (a) gate-count parenthetical (l. 1536-1541); (b) v7 entry "Line numbers at
    fba27d5:" (l. 256-257); (c) first Holm copy, Direction sentence deleted (l. 1028); (d) second
    copy, step-down order (l. 1049-1050); (e) Table 1 rows (l. 364-365); (f) per-class ROC legends
    (l. 1246-1247, l. 1267-1268); (g) primary figure caption (l. 1237-1239) and beside A − 79.4 (l. 961-963);
    (h) attention-state figure (l. 1258-1260). Optional C items (fix 6) not applied.
- v1, revised after `review/STUDY_arbiter_v9.md` (ITERATE, iteration 9, 2026-09-27): [D15] branch
  executed, Kai-decided (regime B: [D20] trace every 10 epochs; second pilot under regime B; K=5
  wave-1 packing, about 27 pods at peak); physics v9 B1-B3; no change to any arm, seed, target,
  batch, epoch count, selection metric or certification rule; selection restricted to traced
  epochs. Fixer pass; arbiter's verbatim wording; slots T, C and P filled from patch 0027 as
  staged in `code/tree` (`bnhgq2/ablation.py`, working tree read 2026-09-27) and `plan.md`
  'ml-engineer, regime B'. Line numbers at the working tree after this pass, this entry included
  (base c2f5447; line numbers at 96b95f2):
  - fix 1(a) core paragraph "[D15] branch executed" after "Trace-cost risk" (l. 1393-1459):
    slot T (l. 1403-1415: traced iff (e + 1) % 10 == 0 or last
    epoch; no epoch-1 trace, so the canary pair is the pre-training trace and epoch 10 [corrected
    in the entry "after the regime-B freeze 42abed4b": epoch 0 is traced, 701 / 101 traces, the
    canary pair is epoch 1 against epoch 10]), slot C
    (l. 1419-1429), slot P (l. 1430-1440: in-training EBOPs between traces,
    traced on traced epochs, split assertion) and its continuation (l. 1442-1448).
  - fix 1(b) fidelity rows (l. 535, l. 536); confound 10 (l. 779);
    Selection rule (l. 854); [D20] "On each traced epoch" (l. 1919), "PID
    signal" = slot P (l. 1934-1946), "once per traced epoch" (l. 1949); [D20] DECISION block
    (l. 2490, l. 2499).
  - fix 1(c) Symbols s_e (l. 1332); "Illustrative projections" head (l. 1340);
    "[D15] branch (measured 2026-09-27)" (l. 1360); [D15] (l. 1881); launch-policy FLAG block
    (l. 2467, l. 2474); the prior label "(prior, superseded; pod-hours = pods × T_run from
    the regime-B canary)" at l. 1351, 1353, 1390, 1480, 1710, 1717, 1736, 1761, 1762, 2339, 2347, 2468, 2481.
  - fix 1(d) canary traced-epoch rule (l. 1613); Reports (l. 1605); Outputs (l. 1640);
    Phase 1 window (l. 1540); "Trace-cost risk" s_e window (l. 1380).
  - fix 1(e) regime-B pilot amendment (l. 1526-1539); Phase 2 duration (l. 1542); resume
    rule (l. 1642).
  - fix 1(f) Pods (l. 1461); GPU classes (l. 1475); [D16] (l. 1885); "Pod count"
    (l. 1482).
  - fix 1(g) Kai rows "pod count" (l. 2339), "wave-1 packing" (l. 2340), new row "[D15] branch
    after the canary" (l. 2341).
  - fix 1(h) "closed by Kai's K=5 packing" at l. 1713, 1748, 1759, 2350, 2352; "Pods, second wave" memory sentence (l. 1754); second-wave
    cost labels as in (c).
  - fix 1, neighbourhood (sites the arbiter did not list, same regime-B fact): H paragraph (l. 702),
    H fidelity row (l. 724), Selection certification (l. 899),
    Pods seed-block note (l. 1471), "Expected branch" default (l. 1365),
    stability ratio (l. 1615), overhead bullet (l. 1639), [D14] (l. 1663),
    overlap count (l. 1709), wave-2 clone cost (l. 1718), wave-2 canary (l. 1722),
    [D20] certification (l. 1932), [D23] (l. 1979), [A21]
    (l. 2168), [A23] (l. 2217), Kai row "H trace protocol"
    (l. 2346), H DECISION (l. 2419), pod-count DECISION (l. 2481).
  - fix 2 (#3) canary sources after the Stability list (l. 1619-1627; the 77f1ca4e line-number
    note and the patch-0027 log line, `ablation.py:838-842`, added for accuracy); "(from the W&B history)" (l. 1379).
  - fix 3 (#4) confound 9 (l. 768-774); Pods "one GPU class (confound 9)" (l. 1466).
  - fix 4 (required C): (a) l. 1170; (b) l. 1152. Optional C (fix 5) not applied.
- v1, amended 2026-09-27 (constraint-active readout for arm C; source
  `campaigns/2026-09-27-delta-screen/review/STUDY_physics_v3.md` B2; registered before any arm-C
  data exists, C-s1 first runs in the regime-B K=3 pilot pod, not yet launched): new
  pilot-rules bullet "C, constraint-active readout" (l. 1605-1630): fraction of traced epochs over
  5M, selected EBOPs / 5M, β at its [D5] lower bound on the last N = 10 traced epochs; "constraint
  slack" iff the β condition holds; at VERIFY the label applies when k ≥ 5 of 8 seeds. The same
  three quantities are reported for C′-s1. Descriptive only: no change to any arm, seed, target,
  selection rule, certification, gate or Holm member. Base 96b95f2; line numbers at 9884773.
- v1, corrected after the regime-B freeze 42abed4b (2026-09-28; source `plan.md` 'Stall incident
  fix and re-freeze to 42abed4b' and 'ml-engineer, regime B', PREFLIGHT 'Regime B addendum',
  `review/INCIDENT_stall_20260928.md`, `RUN.md` 'Stopped 2026-09-28T05:31Z'). Text and citations
  only: no change to any arm, seed, target, batch, epoch count, selection rule, falsifier,
  certification or Holm member. Line numbers with this entry included (line numbers at cc36f7c):
  - slot T (l. 1439-1455): epoch 0 is traced (`is_traced_epoch` `epoch == 0`, `ablation.py:489`); 701
    traces per 7,000-epoch run and 101 for R (was 700 / 100); the canary pair is the traced end
    of epoch 1 against epoch 10 (was `initial_ebops` against epoch 10); same correction in the
    canary stability bullet (l. 1689-1691) and a bracketed note in the v9 entry (l. 308).
  - `ebops_trace_every: 10` is in `generate.py:57`, `TRACE_EVERY_OK` 58 / 58; the "not yet in
    generate.py" caveat removed (l. 1452-1455).
  - counter denominators 701 / 101 (l. 1469-1470); arm-C readout (i): 51 at the epoch-500 readout (e =
    0, 9, ..., 499; `initial_ebops` still excluded) and 701 in production, was 50 / 700 (l. 1651-1653).
  - citations re-cited by content to `code/tree` at 42abed4b (sha of `bnhgq2/ablation.py` equal
    in the frozen tarball): slot T/C/P (l. 1439-1493) and the [D20] PID-signal copy (l. 2035-2045), log
    line (l. 1696-1699), H assertion (l. 737), Selection (l. 919-920), [A19] (l. 984), binary gate (l. 1904, l. 2365),
    [D25] (l. 2091), [A21] (l. 2261-2262, 2269), H port sites (l. 2317, l. 2347), FP32-E PID (l. 2344). Citations that
    describe the screen bundle labelled "screen bundle 7f9e9307" instead of moved: confound 8
    (l. 799), Selection tie-break (l. 898), [A13] (l. 2184), [A15] (l. 2196). Other change-log entries untouched but for the l. 308 note.
  - leak fix and gates: `ValidationReloader` in slot C (l. 1463-1468); new pilot bullet "Host memory"
    (l. 1713-1731): `run_pack` heartbeat per attempt, `POD_STALL` not charged, `POD_MEM`; the RSS
    projection gate (process epochs 5-104, baseline + slope × `train.epochs` ≤ 6,144 MiB, else
    exit 5, not retried); cluster-ops' operational canary rule at epochs 10 and 20.
  - regime-A pilot stopped 2026-09-28T05:31Z on Kai's decision, no epoch-500 snapshot,
    descriptive only; its certification and regime comparison apply only if resumed to 500 on
    77f1ca4e (l. 1575-1584); canary-sources note (l. 1696-1699).
  - DECISION R-B5 recorded as accepted, stdout format only (l. 1702-1706).
- v1, text pass after PREFLIGHT gate v3, Kai 2026-09-28 (`review/PREFLIGHT_critical_v3.md` A1, A2,
  flag 4; `.claude/memory/decisions.md` 2026-09-28 top entry). Operational only: no change to any
  arm, seed, target, batch, selection rule, falsifier, certification or Holm member.
  - regime-B pilot pods (l. 1583-1588): A10 only, node hcc-nrp-shor-c6017 excluded, a pre-arm GPU
    fingerprint gate on arm-A s1 `initial_ebops` (value in PREFLIGHT), and the K=3 OOM fallback
    (the arm alone or at K=2, same bundle and run root).
  - epoch-10/20 memory rule (l. 1741-1748): prose replaced by the formula
    rss20 + (rss20 − rss10)/10 × 85 > 6,144 MiB, projected to process epoch 105, not 7,000.
- v1, text pass 2026-09-28 (ml-engineer, coordinator brief; `.claude/memory/decisions.md` 2026-09-28
  top entry): per-arm memory 6 → 8 GiB. Operational only: no change to any arm, seed, target, batch,
  selection rule, falsifier, certification or Holm member.
  - Host-memory bullet (l. 1748-1760): gate limit and the epoch-10/20 rule's limit 6,144 → 8,192 MiB
    [corrected 2026-09-28, arbiter v10 orchestrator note (2), attribution fixed after STUDY v11
    landing check: 8,192 applies to the c7bae4a manifests only; the running K=3 pod stays at 6,144
    until its swap; see that entry].
    The incident-leak fill epoch is recomputed from that bullet's own numbers:
    (8,192 − 2,106..2,160) / (80..95) MB/epoch ≈ epoch 64-76 (was 48 at 6 GiB).
  - Why: 6,144 came from rule PACK's "about 6 Gi per arm", not a measurement. The only GPU RSS
    telemetry on this code is Delta canary v2, E-k4 on an A10: slope 0.45-0.63 MB/epoch over epochs
    5-100 and baseline 2,288-2,303 MB (`campaigns/2026-09-27-delta-screen/RUN.md`, a3a3362).
    It is telemetry with Delta's patches on top of 42abed4b, not a result. It projects to about
    6.5-6.7 GB at epoch 7,000: over 6,144, under 8,192.
  - l. 1538 (rule PACK's "about ... 6 Gi of host memory per arm") is unchanged; it describes rule PACK.
- v1, amended 2026-09-28 (Kai, STUDY v10 ESCALATE; `review/STUDY_arbiter_v10.md` K1-K3 and fixer
  items F1-F7; `.claude/memory/decisions.md` 2026-09-28 top entry). Fixer pass, minimum change.
  Kai: K1 = (b), K2 = FP32-E on the 701 slot-T epochs, K3 = A − NB stays at 8 pairs, no extras.
  No change to any wave-1 arm, seed, target, batch, epoch count, selection metric, falsifier,
  certification or Holm member; FP32-E's candidate grid changes before any FP32-E data. Line
  numbers at the working tree after this pass, this entry included (base c7bae4a; line numbers at 725acba):
  - K1: slot P (3), regime-A measurement (F7) and pointer to the rule (l. 1554-1562); [D20]
    PID-signal cross-reference (l. 2202-2204); pilot rule 'Regime-B PID input rule' (l. 1717-1743),
    arbiter's (b) text verbatim plus three additions (B has no pilot run, so its r is read in
    production; the 5M form of the offset for C and C′; F 17,847 and C 465,695 by the same formula), (c) staged unapplied by ml-engineer, (d),
    declined options, and the regime-A arithmetic on which it would already fire (offsets 11.8-12.7 %
    of A/D headroom and 10.1 % of E1's, recomputed from the RUN.md medians; E1 − D 0.0203); 'not
    attributable' wording on the A rule (l. 1699-1701) and A07-350-s1 rule (l. 1714-1716);
    launch sentence (l. 1810-1812); Kai row (l. 2607).
  - K2: FP32-E Selection (l. 746-751); A vs FP32-E table row (l. 834); confound 12 (l. 899-901);
    evaluations (l. 1067-1068); conventions row (l. 2058); [D26] (l. 2266-2268); [A25] selection
    bullet, routed to ml-engineer as a wave-2 code item (l. 2508-2513); Kai row FP32 E arm
    (l. 2616); DECISION [D26] and ALTERNATIVES (l. 2709-2714).
  - K3: 'Resolution' (l. 1253-1264), extra-pair rule declined, sizing table kept as record;
    precision package (l. 1317-1318); second-wave epoch-500 rule (l. 1987-1990); Kai row closed
    with the half-width and 80 %-power gap at 8 pairs (l. 2615).
  - F1 T_run per pod class (l. 1581-1594). Deviation: `packs.json` has four E pods at K=5 and three
    at K=4, so the K=4 E pods are named as their own class, timed from the K=5 s_e as an upper
    bound, not a measurement; the A07 pods at K=4 are untimed. F2 arm-C slack (l. 1795-1800, C′
    l. 1806). F3 package label (l. 834, l. 899): Kai chose K2(i), so the restriction is written
    as a dated amendment, not the '7,000 against 701' wording. F4 A − NB headline (l. 1210-1214). F5
    matched traced-epoch table (l. 1744-1749; E1-s1 and C′-s1 added where regime-A epochs exist)
    and pointer (l. 1684-1685). F6 change-log shas (l. 305, l. 355); Pods paragraph (l. 1596-1605):
    'A lost pod costs ...' and 'R ... crosses GPU type' deleted, prior-plan label moved, pod
    classes named as in F1 (the arbiter's 'K=5 for the E arms' corrected); RSS gate indexing
    (l. 1861-1863). F7 in K1 above.
  - Memory (orchestrator): 8,192 MiB split from the running pod (l. 1861-1882): the running K=3 pod
    (applied 23:05Z from 4dbf6b6) stays at 6 GiB per arm and 6,144 MiB, gate and manual rule, until
    it is swapped to the 8 GiB manifest before process epoch 105; the Pending K=5 pod is deleted and
    re-applied from the 8 GiB manifest, recorded in RUN.md by cluster-ops; the ml-engineer entry above
    is annotated (l. 389-391). Figure list (l. 1398): 'R crosses GPU type' → 'may cross'.
- v1, revised after STUDY v11 landing check (`review/STUDY_critical_v11.md`, 2026-09-28), fixer
  pass, minimum change; line numbers at the working tree after this pass, this entry included
  (line numbers at 30fad23). No change to any arm, seed, target, batch, selection rule, falsifier,
  certification, Holm member or Kai answer.
  - B1, route (i): 'Regime-B PID input rule' (l. 1752-1761): B removed from the K1 fire list, which is
    now (A, D, F, A07-350, C); B's r is read at production epoch 500 and reported beside every
    A − B and budget-ladder number as a descriptive caveat, offset 250k × (1 − r^−0.9) against
    B's headroom 78,474; it fires nothing and stops no pod. This reverts the previous fixer's own
    addition ("B has no pilot run, so its r is first measured in production and the clause reads
    it there", entry above): arbiter v10's fire list did not include B.
  - B2: memory split re-attributed at l. 390-392 and l. 1896-1899 (was "Kai, STUDY v10 ESCALATE"): 6,144 MiB
    to Kai, PREFLIGHT gate v3 escalation (`decisions.md` 2026-09-28); 8,192 MiB to the ml-engineer
    sizing entry (`decisions.md` 2026-09-28, per-arm memory 6 → 8 GiB, c7bae4a); the running/new
    split to arbiter v10 orchestrator note (2).
  - C8: the A07-350 wind-up clause (l. 1755-1757) names its source for untraced-epoch EBOPs: W&B
    `ebops_in_training` (value `model_ebops(model)`, float; `code/tree/bnhgq2/ablation.py:492-495`,
    `:783`, `:894`), not stdout `in_training_ebops=` (`saved_ebops`, `:791`, `:933`). The W&B key is
    `ebops_in_training`; `model_ebops` is the function that computes it.
  - Disclosed, not fixed (v11 C items, for a freeze to cite): C1 wind-up clause says "an A07 run",
    meaning A07-350; C2 C′ threshold (41,960 of 419,602) not printed; C3 K=4 E pods timed from the
    K=5 s_e as an upper bound rests on an unstated monotonicity assumption; C4 "untimed until then"
    does not say whether A07 packs 7-10 launch or wait without a K=4 A07 s_e; C5 "about 5.2 pt"
    is 5.14 pt at 1.156, and "near epoch 48 at 6 GiB" is epochs 42-50 by the bullet's numbers;
    C6 tense: the Pending K=5 pod was already re-applied (RUN.md, 23:45:43Z, `-qqjmt`); C7 the
    ml-engineer entry's "l. 1748-1760" pointer is stale (history); C9 "iso-EBOPs comparison"
    lists C (5M), whose target is not A's; "arms compared at their nominal targets" is meant.

# What does a binary-weight N=64 tagger reach under the Sun et al. recipe at 350k EBOPs, and how far is it from their 79.4 %?

**Question.** Arm A trains the binary-weight N=64 tagger, sized as Chang's `xfm` (arm A
architecture "E": d24, 2 heads, 1 block, FFN 32, no PE [D21]), with the Sun et al. recipe to a
350,000-EBOPs target. In how many of 8 seeds does it reach 350k above the 0-bit floor and above
chance (a feasible checkpoint, Selection rule (a) to (c); the count rule asks for at least 6)?
Non-degenerate means not a constant classifier; it does not mean the model tags well. What seed-mean held-out (ROC-test,
n = 260,000) top-1 accuracy does it reach, and what is its distance, with a 95 % interval, to
the published single-model 79.4 % Deep Sets (HGQ) N=64 row of arXiv:2510.24784 Table 1?
Secondary: does the recipe beat our own recipe (arm R) at the same architecture, input set,
split and target?

Second wave ([D24]): at 350k EBOPs, is arm A's
seed-mean ROC-test accuracy below that of arm NB, the same E model, recipe, quantizers and seeds
with learned-width HGQ (kbi) weights in place of binary weights? The gap A − NB is binary
against learned-width weights at **iso-EBOPs** (not iso-cost, [L2]). Arm H (Sun et al.'s own
`xfm` model, ported, on our split and selection rule) places their pipeline against NB and A;
H − NB and H − A are descriptive. Arm FP32-E [D26] (2026-09-27, Kai request (second set)) is the
same E model, recipe and seeds in unconstrained FP32: what is A − FP32-E? A − FP32-E is a
labelled package (weight type, activation quantizers and the 350k budget move together), not
iso-EBOPs.

Why the primary is E and not our A07 (d32, 4 heads) [D21]: under the [D19] quantizer the softmax
internals of A07 alone cost at least 343,053 EBOPs (traced, CPU, synthetic sample, not a
result), which leaves 6,947 EBOPs above the 0-bit floor at 350k. At 1 bit one input channel of
`input_proj` or of any d32 dense layer costs 2,048 EBOPs, and one Q·K (head, key-channel) pair
costs 4,096 (`code/evidence/static_floors_trace_step2.json`, `a07-chang`, `one.per_layer`).
Data-dependent attention logits need at least one `input_proj` input channel, one Wk input
channel and one Q·K pair: 2,048 + 2,048 + 4,096 = 8,192 > 6,947. **At 350k a feasible
A07 checkpoint cannot carry data-dependent attention and has at most 3 per-constituent input
bits (6,947 / 2,048 = 3.4).** That is a fact of the floor, not an outcome, so A07 at 350k is kept
only as the descriptive arm A07-350, with that attention state pre-registered (Falsifier). E's
floor is 171,526 (headroom 178,474 at 350k); the same minimal attention path costs 1,536 +
1,536 + 4,096 = 7,168 EBOPs in E, 4.0 % of its headroom.

**Null.** H0-budget: fewer than 6 of 8 A seeds have a feasible, non-degenerate checkpoint at
350k. H0-recipe: A − R = 0. H0 for each secondary ladder: the paired or unpaired gap is 0. The
distance A − 79.4 is descriptive: it is reported with its interval and has no null, because
the reference is one external model whose own uncertainty is unknown ([L1]).
H0-weight (second wave): A − NB = 0; H0 for H − NB: the
unpaired gap is 0. H0-precision (FP32-E, 2026-09-27, Kai request (second set)): A − FP32-E = 0.

**Bearing on the thesis.** The thesis says binary weights keep tagging efficiency close to
full precision. No first-wave arm varies the weight type (the second wave does,
below), so the first wave does not measure the cost of binary weights. It measures what this binary pipeline reaches under the Sun et al.
recipe, with Chang's activation and softmax quantizers [D19], at matched native HGQ2 EBOPs
(iso-EBOPs, not iso-cost: EBOPs leave out the accumulator, which flatters a ±1 design, [L2]),
and the gap between it and their HGQ models at equal EBOPs. At 350k the softmax floor takes 49 %
of E's budget (171,526) and 98 % of A07's (343,053); the Deep Sets comparand pays no softmax.
Our A07 architecture at 350k is data-independent in its attention by construction (above), so
it is reported, not used for the primary. The gap mixes weight type with model family, head,
backend, standardization and selection. Attributing it to binary weights needs a matched
non-binary arm.

The first wave (56 runs) varies no weight type; the
second wave does. **A − NB** is the one thesis-bearing comparison: binary against learned-width
HGQ weights on the same E model, recipe, [D19] quantizers, seeds and data at the same 350k
EBOPs target. It is iso-EBOPs, not iso-cost: EBOPs leave out the accumulator and adder tree,
which flatters binary ([L2]), so a small A − NB supports "binary loses little accuracy at equal
EBOPs", not "binary loses little accuracy at equal LUT". NB is learned-width, not FP32, so A − NB
is not the thesis's "close to full precision" gap either. H − NB and H − A do not bear on the
thesis: they compare Sun et al.'s pipeline with ours. **A − FP32-E** [D26] (2026-09-27, Kai request
(second set)) bears on the "close to full precision" axis for this model, as an interval and never as a "close" verdict: binary weights with learned-width
activations at 350k against the same E model unquantized and unconstrained. It is a package, not
iso-EBOPs, and not the cost of binary weights alone (A − NB carries that at iso-EBOPs). Every
row of arXiv:2510.24784 Table 1 except the Deep Sets (QKeras), Deep Sets M (QKeras) and Deep
Sets L (QKeras) rows reports DSP = 0, including the 79.4 %
Deep Sets (HGQ) comparand, MHA-64 and Linformer-64, so the published comparands at this budget
are already DSP-free in synthesis. A − NB therefore most likely compares two DSP-free designs; a
hardware advantage of binary would have to show in LUT or latency, which this campaign does not
measure ([L7]). REPORT does not read a small A − NB or A − FP32-E as support for the DSP claim
(arbiter v7 fix 6).

Scope (amended 2026-09-27, arbiter v4 #10; amended 2026-09-27, Kai request (second set)): this
campaign does not measure the cost against W8A8, nor the A8 → A6 → A4 activation ladder;
activations here are learned-width under WRAP. Kai added the FP32 E arm (FP32-E [D26]), so REPORT
may cite the A − FP32-E interval as evidence bearing on the thesis's 'close to full precision'
axis, printing the interval and never the word 'close' as a verdict, **only for the E
architecture at N=64 under this recipe**, worded as the labelled package of [D26] (binary at 350k
against unconstrained FP32), never as the cost of binary weights alone, and never for A07, other N
or other recipes. A − NB is cited only as an iso-EBOPs gap against learned-width weights (arbiter
v5 fix 6).

**Downstream use.** `campaigns/2026-09-26-delta/` (Delta, formerly the method atlas; renamed by
Kai 2026-09-27, `decisions.md`) treats this study as its wave 0 anchor: every Delta method is
measured against arm A, paired to it at the same seed where shapes allow
(`campaigns/2026-09-26-delta/BRIEF.md`, "The anchor (wave 0)"). Under [D21] (Kai-confirmed
2026-09-27) arm A is the E architecture at 350k under [D19]; the A07 probe at 350k is arm
A07-350, and C (A07 at 5M) is the A07 anchor at 5M. The Delta BRIEF has to say so (routed to
the Delta owner, not edited from here). If arm A has no non-degenerate feasible
checkpoint (pilot rule or production), the anchor falls back to the arm Kai names.

## Reference table

| reference | value (metric, split, n, status) | source |
| --- | --- | --- |
| Round-14 record, same configuration | **none.** Round 14 is archived (no EBOPs target, 101 epochs, no pT gate, 80/20 split, different architecture). Not a comparand. | `.claude/memory/decisions.md` 2026-09-26; `.claude/memory/project-context.md` "Current vs archived" |
| Sun et al., Deep Sets (HGQ), N=64 | 79.4 % top-1 accuracy, test set n = 260,000, **one model, no seed interval**, 350k EBOPs target via PID on β; selection rule and split not stated | PDF `literature/jet-tagging-transformers/2510.24784_submicrosecond_transformers_jet_tagging_fpga.pdf`, Table 1 (pdftotext lines 249-264), §3 (lines 155-158) |
| Sun et al., band at N=64 | Linformer 79.8 %, MHA 77.9 % (per §3, the attention block "collaps[ed] ... into a Deep Set"), same labels as the row above. MLP Mixer 79.7 % is quoted from their ref. [18] and is not stated to be trained at 350k EBOPs | same PDF, Table 1; §3 lines 174-176 |
| Sun et al., per-class OvR AUC at N=64 | Linformer g 0.941, q 0.921, W 0.972, Z 0.968, t 0.964 (arithmetic macro mean 0.9532); MHA g 0.930, q 0.911, W 0.963, Z 0.956, t 0.954 (0.9428). **Read from figure legend, one model, our arithmetic macro mean** (the paper states no macro value). Test set n = 260,000. Deep Sets AUCs are not published | same PDF, Fig. 2 panel (d) legends; `.claude/memory/research-log.md` 2026-08-04 (https://arxiv.org/abs/2510.24784); means recomputed 2026-09-27 |
| Our run of Chang's own code (HGQ weights, **not binary**), xfm N=64 | 80.56 % test accuracy at 348k EBOPs; xfmt N=64 80.85 % at 318k. `xfmt` is the post-paper LUT/QDenseT Linformer (k=4), not the paper's Linformer, and both runs used the **open-loop β `PieceWiseSchedule`**, not the paper's PID. **Single seed 42, unverified, and selected on test accuracy (circular)**. Context only: it shows the open-loop-β recipe works on our infrastructure with float-latent HGQ weights, not the PID recipe of [D5]. Never a comparand | `_attic/repro-chang/repro-chang/comparison.md` lines 3-4, 12, 23, 27 |
| Our binary N=64 under any EBOPs target | **no verified number exists.** This design establishes it. Initial EBOPs of the A07 N=64 architecture under the current quantizer: 24,816,782 (12,788 parameters), a trace at initialization and not a result. Under [D19] the same A07 counts 61,951 parameters and E 31,735 (Keras `count_params`); the trainable kernel, bias and PE set is 11,653 for A07 and 6,253 for E. The rise is quantizer width variables (mostly per-element softmax-output widths), not weights | `campaigns/2026-09-23-confirmation/n64-full-preflight-result.json`; [D19] counts `code/evidence/cpu_gate_d25.log` (was the absent `cpu_gate_final.json`, arbiter v5 fix 7), `static_floors_trace_step2.json` |
| Archived Round 14, N=64, **context for sd only** | Binary W1A8 69.0 ± 3.1 % (seeds 67.18 / 72.64 / 67.21 %); FP32 79.1 ± 0.3 %. Held-out top-1 accuracy, ROC-test n = 260,000, 3 seeds, sd ddof = 1, **archived** (no EBOPs target, no pT gate, 80/20 split, different recipe and architecture). Used to size the seed spread only; never a comparand | recomputed 2026-09-26 from `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz` |

Seed spread for resolving power: no N=64 spread exists under any EBOPs target or recipe. Two
bounds bracket it, both order-of-magnitude only:
- **Lower bound, different N and different recipe.** N=8 W1A8, 8 seeds: held-out accuracy sd
  0.0019 (pt-weighting BASE, `.claude/memory/experiment-log.md` 2026-09-26). That arm is a
  Round-14-style unconstrained recipe: 101 epochs (decay 100), early stopping patience 15,
  batch 256, LR 2e-5, no EBOPs block (`campaigns/2026-09-25-pt-weighting/VERIFY.md` header;
  `bnjettag/code/hgq2/configs/ptw-n8-20260925-base-w1a8.json`). It is not a 1,000-epoch
  EBOPs-constrained run (corrected 2026-09-27), so it is a weak lower bound here: it differs in
  N, recipe, epoch count and budget.
- **Upper bound, same N, archived.** N=64 binary W1A8, Round 14, 3 seeds: held-out accuracy
  sd 0.0314 (table above). Binary at N ≥ 32 was unstable across seeds in Round 14
  (`docs/chang-vs-bnjettag.md`, "seed variance ×75.8"), so the N=64 spread may sit near this
  bound.

## Arms

All arms: N = 64; input set pt, etarel, phirel with the pT gate [D7]; split 90/10 [D8];
binary `binary_absmean` weights; activation, softmax-output and softmax-table quantizers per
[D19] (Chang's WRAP datalane quantizers, learned, 0 bits reachable, per channel; tables kbi
`SAT_SYM` ≥ 4 bits), config keys per [A20], widths initialized at `f0` for 8 fractional-plus-
integer bits with `i` tracked (`act_policy learned_per_tensor_width`, `act_granularity channel`,
`act_bw_l1 1e-8`, `beta0 1e-7`; the EBOPs trace sample is the [D20] key, which replaces the
inert `calib_n`), norm `none`, pool `gap`, ReLU FFN; our BetaPID [D5] with `stop_on_target
false`; no sample, class or pT weights; no distillation, Engram module, target schedule,
recovery freeze or early stopping (`es_patience 0`); TF32 off, `jit_compile false`; the same
`split_seed` for every run; `experiment.seed = s` and `order_seed = f(s)`, identical across
arms at seed s [D9]. Everything else is copied field for field from
`code/configs/const0922-a07-n64-s1-fast50-fp32.json` in the screen bundle, except the fields in
the table, the tie-break override [A13] and the stale fields rewritten under [A18].

Architecture "E" (primary, [D21], Kai-confirmed 2026-09-27): d_model 24, 2 heads, 1 block, FFN
32, no PE [D18]; 0-bit floor 171,526 (traced). Architecture "A07": d_model 32, 4 heads, 1 block,
FFN 32, learned positional encoding [D1]; 0-bit floor 343,053 (traced).

| arm | optimizer [D3] | LR schedule [D2] | batch | epochs | EBOPs target | architecture | seeds | runs | question it answers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **A** | Chang: Adam defaults | Chang cosine restarts, peak 3e-3 | 2,790 | 7,000 | 350,000 | **E** | 1-8 | 8 | primary: the recipe on our binary model at the paper's budget |
| **B** | Chang | Chang | 2,790 | 7,000 | **250,000** | E | 1-8 | 8 | budget ladder, lower limit (Kai: "some at a lower EBOPs limit"); A − B is target only [D6] |
| **C** | Chang | Chang | 2,790 | 7,000 | **5,000,000** | **A07** | 1-8 | 8 | budget ladder on A07, our current N=64 target (Kai: "the way it's implemented", reading 1) |
| **D** | **ours**: β₂ 0.98, weight decay 0.01, clipvalue 1.0 | Chang | 2,790 | 7,000 | 350,000 | E | 1-8 | 8 | stability control: the Chang schedule on our optimizer |
| **F** | Chang | Chang | 2,790 | 7,000 | 350,000 | **E + learned PE** | 1-8 | 8 | positional-encoding knob on the primary architecture (first arm to cut) |
| **R** | ours | **ours**: warmup 1 + linear decay 999, peak 2e-5 | **256** | **1,000** | 350,000 | E | 1-8 | 8 | recipe package control (Kai: "the way it's implemented", reading 2) |
| **A07-350** | Chang | Chang | 2,790 | 7,000 | 350,000 | **A07** | 1-8 | 8 | descriptive: "our A07 at the paper's budget: attention data-independent by construction"; A07 target rung with C |

Total: 7 arms × 8 seeds = **56 runs** (48 on the Chang schedule, 8 on ours); 40 on the E
architecture (A, B, D, F, R), 16 on A07 (C, A07-350). The former A07 arm A is A07-350; the former
arm E is now arm A ([D21]). The second wave adds H, NB and FP32-E, 24 runs, **80 in total**
(section "Second wave: arms H and NB"; FP32-E amended 2026-09-27, Kai request (second set)).

What each comparison varies (one knob per comparison, except the package arms):

| comparison | varies | pairing / test |
| --- | --- | --- |
| A vs B | EBOPs target only (350k vs 250k, E) | paired by seed (same shapes, same init, same order) |
| C vs A07-350 | EBOPs target only (5M vs 350k, A07) | paired by seed (same init, same order) |
| A vs D | optimizer only (β₂, weight decay, clip), on E | paired by seed |
| A vs F | positional encoding only, on E | paired by seed (t, df 7, sign count) if the PREFLIGHT `kernel_hashes` comparison [A17] shows that only `pos_table` differs at every seed; otherwise unpaired, Welch |
| A vs A07-350 | architecture package (d_model 24→32, heads 2→4, learned PE) at 350k | unpaired; Welch; labelled a package, dominated by the headroom difference (178,474 against 6,947); interval only, outside the Holm family (amended 2026-09-27, arbiter v4 #25) |
| D vs R | schedule package: batch, LR shape and peak, epochs (optimizer shared), on E | paired by seed index (same init; data order differs because the batch differs) |
| A vs R | the whole recipe package (optimizer plus schedule), on E | same as D vs R; this is the secondary question |

The ladder A → D → R separates the recipe: A−D is the optimizer, and D−R is the schedule,
batch and epoch package. The epoch-matched gaps A1000 − R and D1000 − R (A and D evaluated on
their best-feasible checkpoint as of epoch 1,000, [A6]) separate "more epochs" from "the
schedule and batch".

Fidelity to the Sun et al. recipe ("Chang code" is `reference-code/HGQ2-examples/jsc150/`):

| field | Chang code | paper | ours (A) | matched? |
| --- | --- | --- | --- | --- |
| optimizer | `Adam()` defaults (`run_train.py:97`) | not stated | Adam defaults [D3] | yes |
| LR schedule | cosine restarts 3e-3, 500 epochs, α 1e-6 (`run_train.py:93`) | not stated | [D2] | yes |
| batch, epochs | 2,790, 7,000 (`:67`, `:104`) | not stated | 2,790, 7,000 | yes |
| β control | open-loop `PieceWiseSchedule` 2e-8 → 3e-7 → 3e-6 (`:90`) | PID on β (§3) | PID [D5] | paper, not code |
| β0 | 0 (`model.py`, `LayerConfigScope(beta0=0)`) | not stated | 1e-7 | no |
| weight type and init | HGQ `kbi`, transformer weights `b0=4, f0=4`, `SAT_SYM` (`model.py:186`; `get_model` default `b0=7`) | HGQ mixed precision | binary `binary_absmean` | no (the object of study) |
| activation init width | `f0=7` fractional bits, integer bits in [0, 12] (`get_model(..., 7, 7, ...)`, `run_train.py:76`; `ic=MinMax(0,12)`) | not stated | 8-bit init, stated as an `f0` with `i` tracked under WRAP-trainable [A20] | no |
| activation overflow mode and attention minimum width | kif datalane default `overflow_mode='WRAP'` (`hgq/quantizer/config.py:131-136`); 0 bits reachable; a datalane `QuantizerConfigScope(..., bc=Min(1))` above the attention input is commented out (`jsc150/model.py:193`) | **stated, ambiguous**: "the attention layer which is constrained to at least one bit to disable pruning" (§3, pdftotext l. 168-170; MHA-64 collapsed "despite the bitwidth constrained to at least one bit", l. 175-176); the Fig. 3 caption says **weight** bitwidths (l. 226-228) | WRAP, trainable [D19], 0 bits reachable in Q, K, V (was SAT with k = 1, never below 1 bit) | code yes; paper ambiguous (activation ≥ 1 bit in attention would not match, see "Paper's ≥ 1-bit attention rule") |
| softmax output into A·V | `QuantizerConfig(place='datalane')`, learned, WRAP (`hgq/layers/attn/mha.py:69`) | not stated | learned datalane [D19] (was fixed 10 bits, `qat.py:496-499`) | yes |
| softmax exp input and tables | exp input datalane, SAT per tensor (HGQ2 0.1.9 `mha.py:69` default); exp and inv tables kbi `SAT_SYM`, trainable, `bc=Min(4)` (`jsc150/model.py:186-188`) | not stated | the same [D19], exp input kept SAT (1 bit per score entry at its floor; amended after [A7] trace, 2026-09-27) (was exp input `_static_act(10, 6)`, tables `_table(1, 11)`, fixed, `qat.py:452-459`) | yes |
| weight pruning | HGQ weights prune per weight to 0 bits | not stated | binary 1 bit per weight; only input-channel pruning through 0-bit activations | no (the object of study) |
| activation width granularity | per position, value-wise (`homogeneous_axis=(0,)`, `model.py:181`) | value-wise | per channel (`act_granularity channel`) | no |
| input quantizer | `kif` datalane scope, `ic=MinMax(0,12)` | not stated | [D19] WRAP datalane, trainable, per channel (was the SAT `iq`, `qat.py:75-78`); traced in PREFLIGHT [A7] | overflow mode yes; granularity no |
| architecture (arm A, [D21]) | d24, h=2, key_dim 16, FFN 32, no PE, tanh LUT, batchnorm, 32/32/32 head (`model.py:178-210`) | one head | d24, h=2, key_dim 12 (= 24/2), FFN 32, no PE, norm-free ReLU, our head [D18] | partly |
| pT gate | `X *= X[..., :1] >= 2` (`data.py:22-26`) | not stated | [D7] | yes |
| standardization | train + validation (`data.py:28-31`) | not stated | train only | no ([L3]) |
| split | `val_size=0.1` | 620,000 train, 260,000 test | 90/10 [D8] | yes |
| backend | JAX, TF32 on, float16 inputs | not stated | TensorFlow, TF32 off | no ([L3]) |
| selection | `val_accuracy`, `ebops < 5e5` Pareto front | not stated | [D11], ≤ target | no |
| WRAP range trace sample | `trace_and_save`: `trace_minmax` over the full train and validation sets, once after training | not stated | [D20]: full training split every 10 epochs (regime B), train only (amended after [A7] trace, 2026-09-27) | no (validation kept out of the range fit) |
| WRAP range update during training | per-batch `i` tracking in training mode, one `trace_and_save` after training | not stated | per-batch `i` tracking (`i_decay_speed` 1e-3 under [D25], set by patch 0024: staged, tree ac5a5c86, `chang0926-a-n64-s1.json:40`, `cpu_gate_d25.log` `I_DECAY_OK` 0.001 on every [D19] config; PREFLIGHT re-asserts it on the shipped tree [A21]) plus a `trace_minmax(reset=True)` on the live model every 10 epochs [D20], regime B; between traces `i` follows the per-batch tracking (slot P; arbiter v9 fix 1) | no (the reset every 10 epochs pins `i` to the full-split range on traced epochs, which changes training dynamics relative to Chang) |
| `i_decay_speed` (per-step decay of a WRAP quantizer's `i` in training: i ← max(i − i_decay_speed, i_batch)) | 1e-3 on every quantizer (`get_model` scope0, q_type and place "all", `model.py:278-286`, HGQ2-examples 6cdc6e3) | not stated | 1e-3 on every [D19] quantizer that carries it [D25] (amended 2026-09-27): patch 0024 sets it through `quant.i_decay_speed: 0.001` (staged, tree ac5a5c86; `chang0926-a-n64-s1.json:40`; `cpu_gate_d25.log` `I_DECAY_OK` 0.001 on every [D19] config), and PREFLIGHT re-asserts 0.001 on the listed arms on the shipped tree; C′ has no WRAP quantizer, so it carries no key and records an empty set (`cpu_gate_d25.log:116`) [A21] | yes once the [A21] gate passes |

**Static floor of the current quantizer (zero-GPU finding, 2026-09-27).** Arbiter arithmetic
(`review/STUDY_arbiter_v2.md`, "Independent checks"), calibrated to the 24,816,782 init trace
within 0.09 %, confirmed by the CPU trace of [A7] (traced column). Under our current quantizer
(`bnjettag/code/constituent-study-20260922/bnhgq2/qat.py`: SAT with k = 1, so each channel costs
at least 1 bit; softmax output fixed at 10 bits; exp input 10 bits and tables 12 bits, fixed):

| architecture | dense + head | Q·K | A·V | softmax internals | static floor (arbiter) | traced [A7] | traced vs 350k |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| A07 | 400,544 | 131,072 | 1,310,720 | 2,716,672 | 4,559,008 | **4,580,398** | 13.1× |
| A07, softmax output 1 bit (config only) | 400,544 | 131,072 | 131,072 | 2,716,672 | **3,379,360** | not traced | 9.7× (arbiter) |
| E | 251,064 | 98,304 | 983,040 | 1,358,336 | 2,690,744 | **2,701,439** | 7.7× |

Traced column amended after [A7] trace (2026-09-27): `static_floor.py`, native HGQ2
`trace_minmax`, 256 synthetic jets (the floor depends on widths only), CPU, not a result
(`code/evidence/static_floors_trace_step2.json`). The traced softmax internals of A07 are
2,738,062; the gap to the arbiter (+21,390 for A07, +10,695 for E) is the `QUnaryFunctionLUT`
table term Σ 2^b_in · b_out · 1e-4 (`hgq/layers/activation.py:63-67`), which the arbiter
omitted. The same tool's init trace of A07 gives 24,816,782, equal to the confirmation preflight.

Every 350k and 250k arm is `STATIC_INFEASIBLE` under that quantizer (E at 250k against its
2,701,439 floor); only a 5M target clears it.
The two partial remedies fail: narrowing the softmax output alone leaves the fixed tables
(2.74M traced) and the 1-bit SAT dense inputs (400k) above every target but 5M; a Linformer projection
shrinks Q·K, A·V and the softmax (H·T·k instead of H·T²) but not the SAT dense floor. The 2026-09-22
screen's lowest A07-N64 EBOPs, 4,630,276 (W&B, seed 1, not a result), sits 1.1 % above the
traced floor, so the screen plateau is the quantizer's floor, and the 5M N=64 confirmation
target sits 9.2 % above it. Hence [D19].

Under [D19] (same evidence file, CPU, synthetic sample, not a result): 0-bit floor A07 **343,053** (arbiter 326,656), E **171,526** (arbiter 163,328);
A07 without PE traced 343,053, so the PE costs no EBOPs, and F (E + learned PE) traces at E's
171,526 (`code/evidence/cpu_gate_d21.log`, F-s1 `zero_floor` and `floor_retraced`; CPU, not a
result; re-run on the shipped tree at PREFLIGHT [A7]); 1-bit-alive floor (every learnable width at 1 bit) A07
**1,005,741** (arbiter 989,344), E **619,198** (arbiter 611,000). The former open risk is settled:
the softmax exp input is SAT per tensor (jsc150's MHA default in HGQ2 0.1.9, kept for fidelity
under [D19]), so it costs 1 bit per score entry at its floor (H·T·S = 16,384 for A07, 8,192 for
E), plus the LUT table term (13 for A07, 6 for E). All residuals are named terms. Headroom above
the 0-bit floor: A07 at 350k **6,947** (0-bit floor / target 0.980; 1-bit-alive floor / target
2.87); E at 350k 178,474 (0.490; 1.77), at 250k 78,474, at 175k 3,474; A07 at 175k negative
(`STATIC_INFEASIBLE`). A one-head E ("E1", d24, 1 head, pilot-only) is traced (amended
2026-09-27, `code/evidence/static_floors_fix6_a07_e_e1.json`, CPU, synthetic sample, not a
result): 0-bit floor **85,763**, 1-bit-alive floor 533,435; headroom above the 0-bit floor
264,237 at 350k (1.48 × E's) and 164,237 at 250k; the 1-bit-alive floor is 183,435 above 350k.
Only the softmax term splits per head (E1 × 2 = 85,763 × 2 = 171,526 = E, residual 0 including
the LUT table term); Q·K and A·V do not, because H · (d/H) is constant at fixed d_model, so E1's
score and context terms equal E's (98,304 each at 1 bit). A WRAP exp input (not jsc150's choice) would lower the A07 floor to
326,669 (headroom 23,331); it is a Kai option in the [D19] FLAG, not the default.

**Paper's ≥ 1-bit attention rule (zero-GPU finding, 2026-09-27).** Sun et al. state that the
attention layer is "constrained to at least one bit to disable pruning" (fidelity row); whether
that bound acts on weights only or also on the attention activations is ambiguous in the paper,
and Chang's code has the datalane form commented out. Under a datalane reading, the relevant
floor is the 0-bit floor plus the attention streams at 1 bit. Traced floors (amended 2026-09-27:
`static_floor.py` modes `attn_narrow` and `attn_full`, patch 0018,
`code/evidence/static_floors_fix6_a07_e_e1.json`; CPU, synthetic sample, not results). The
arbiter's A07 and E sums reproduce the traced totals, as sums of the trace's own per-layer terms
must (an identity, not a check); the independent prediction that held is E1's per-head split. A weights-only reading adds nothing: binary kernels are fixed at 1 bit and a dense
with a 0-bit input costs 0 EBOPs, so that floor equals the 0-bit floor.

| arm architecture | narrow reading (Q·K and A·V streams ≥ 1 bit) | full reading (plus Wq, Wk, Wv inputs) | vs 350k (headroom narrow / full) | vs 250k (narrow / full) |
| --- | ---: | ---: | --- | --- |
| A07 (A07-350, C) | 605,197 | 801,805 | infeasible either way (−255,197 / −451,805) | −355,197 / −551,805 |
| E (A, B, D, R; F expected equal) | 368,134 | 478,726 | infeasible either way (−18,134 / −128,726) | −118,134 / −228,726 |
| E1 (d24, 1 head, pilot-only) | 282,371 | 392,963 | feasible under the narrow reading only (+67,629 / −42,963) | −32,371 / −142,963 |

Under the paper's rule read as a datalane constraint, no arm of the 56-run design is feasible at
350k; E1 (pilot-only) is the only traced architecture feasible at 350k, and only under the
narrow reading. The 2-head E architecture under [D19] (any weight type, including NB) reaches
350k only because the Q·K and A·V streams may prune to 0 bits, which the
paper's protocol may not have allowed; `xfm` (key_dim 16) is expected to be at least as constrained, traced at [A7] (arbiter v5 fix 7). E's narrow-reading floor is softmax 171,526 + scores 98,304 +
context 98,304 = 368,134, all activation × activation terms with no weight factor, so A − NB is
unaffected (both arms share that floor). [D19] follows the code, as Kai asked ("replicate his
code"); a "paper-rule variant" is a Kai option ("Where I am not sure"), not the default.

## Second wave: arms H and NB (amended 2026-09-27, Kai request, 08:40)

Kai asked for both arms on 2026-09-27 08:40 PDT (`.claude/memory/decisions.md`). Both need new
code, so they are a **second wave** [D24]: each launches when its code passes the CPU gates
([A22]-[A24]) and the wave-1 pilot A rule has passed, with the same seeds (1-8), the same gated
90/10 cache (same file sha256, same `split_seed`), the same `order_seed = f(s)` and the same
Chang schedule as arm A. Pairing with A then holds whenever they launch. Status of both:
"Kai-added 2026-09-27; second wave".

| arm | weights | architecture | optimizer, schedule, batch, epochs | β control | EBOPs target | seeds | runs | ROC-test evaluations per run | question it answers |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **NB** | **kbi learned width** (jsc150 weight quantizer, [D22]) on every kernel A binarizes | E (as A) | as A (Chang, [D2]-[D4]) | PID [D5], as A | 350,000 | 1-8 | 8 | 2 (primary, [A19] sensitivity), as every wave-1 run | A − NB: binary against learned-width weights at iso-EBOPs |
| **H** | kbi learned width, jsc150 as written | Sun et al.'s `xfm` (`get_transformer`), ported [D23] | Chang (his `run_train.py`, identical to A's [D2]-[D4]) | PID [D5] (flagged; alternative his open-loop `PieceWiseSchedule`) | 350,000 | 1-8 | 8 | **1** (primary only, Kai) | H − NB, H − A: their pipeline against ours |
| **FP32-E** [D26] (2026-09-27, Kai request (second set)) | **float** (`quant.weight: "none"`) | E (as A) | as A (Chang, [D2]-[D4]) | **none** (β ≡ 0, no PID) | **none** (unconstrained) | 1-8 | 8 | 2 (primary, [A19] sensitivity) | A − FP32-E, NB − FP32-E: the labelled precision package |

Total: **24 runs** in the second wave (H, NB, FP32-E); with the first wave's 56, **80 runs**
(amended 2026-09-27, Kai request (second set); was 16 and 72). No descriptive arm is added by
default (the open-loop H variant is a Kai option, 8 runs).

**FP32-E, defined [D26]** (2026-09-27, Kai request (second set)). Arm A at seed s (E, Chang
optimizer, schedule, batch 2,790, 7,000 epochs, data, split, order, `norm none`, TF32 off, seeds
1-8) with `quant.weight: "none"`, which builds the fp32 skeleton of `build_qat_model`
(`qat.py:396`). Quantizers **off** (HGQ2 `dummy`, identity): every weight quantizer; every dense
and einsum input datalane quantizer (`input_proj`, Wq, Wk, Wv, Wo, fc1, fc2, head_fc1, head_fc2);
both Q·K stream quantizers and the A·V stream on V; the softmax output into A·V; the softmax
exp-input and inv-input quantizers. **Not off:** the softmax exp and inv lookup-table outputs,
fixed `kif` at i0 1, f0 20, SAT, non-trainable (`_table(1, 20)`); they are part of the package
label. Biases are float, as in every arm. Consequences: no width variables, so no `act_bw_l1` or
MonoL1 terms, `i_decay_speed` records an empty set (as C′), no WRAP overflow fraction, and the
attention-width state is undefined (attention entropy is still reported).
- **Target and controller.** FP32 has nothing to prune, so the EBOPs controller is **off**: β ≡ 0,
  no EBOPs loss term, no PID step, no target, and no [D20] trace. The [D24] canary checks "β
  moving" and "traced EBOPs falling" do not apply to FP32-E (finite loss and epoch-10 train loss
  below epoch 1 stay). Interim readouts give validation metrics only, labelled "unconstrained".
- **Budget and non-degeneracy.** No budget claim: FP32-E has no target. Rules (a) and (b) are
  **not evaluated** (switched off by config, [A25]); a `compute_ebops` reading of 0, or any
  number that makes (a) and (b) pass vacuously, is not an acceptable way through them. Rule (c)
  stays, with the same p_maj threshold. For FP32-E, "feasible" means (c) only.
- **Selection.** *Amended 2026-09-28 (Kai, STUDY v10 ESCALATE, K2; pre-data, FP32-E not
  launched):* highest validation top-1 accuracy over the 701 slot-T epochs (zero-based e = 0,
  (e + 1) % 10 == 0, last; the same grid as A) that meet (c); tie-break validation macro AUC, then
  earlier epoch (−EBOPs drops out). [A19] sensitivity as every arm. The candidate grid is matched
  to A's; the package keeps only the feasibility filter ((c) against (a)-(c)). Was: all 7,000
  epochs that meet (c). Declined: keeping all 7,000 and naming the difference.
- **Certification** reduces to reload determinism: the reloaded selected checkpoint reproduces
  the logged validation accuracy and predictions within 1e-7 (TF32 off). `certify_ebops.py` may
  not pass FP32-E on an EBOPs identity.
- **Checks replacing the binary gate:** no quantizer variables except the two fixed,
  non-trainable softmax tables per block (`kif`, k0 0, i0 1, f0 20, SAT; asserted unchanged from
  init), and float kernels (asserted at the selected checkpoint). `binary_gate` is skipped for
  FP32-E ([A25]).
- **Pairing with A.** Same seed, same E shapes, `arch.pos_enc_none_consume_rng: true`. Paired by
  seed (t, df 7, sign count) if the [A25] `kernel_hashes` gate shows equal latent kernels at init
  at all 8 seeds after `matching_initialization`; otherwise Welch for all. The layer classes
  differ (`QEinsumDense`/`QDense` against `BitQEinsumDense`/`BitQDense`), so [A25] also confirms
  that the variable paths match for the copy to apply.
- **What it does not carry:** an EBOPs number. FP32-E is reported as "FP32, unconstrained" with
  no EBOPs, LUT or DSP figure.

**NB, defined [D22].** Arm A at seed s with one change: every kernel that A quantizes with
`binary_absmean` is quantized instead with HGQ2's learned-width `kbi` weight quantizer, copied
from Sun et al.'s `xfm` weight scope (`jsc150/model.py`: `get_model` scope0 kbi, `i0` 0, MonoL1
1e-8 on the width variables, `i_decay_speed` 1e-3; `get_transformer` weight scope `SAT_SYM`,
`b0` 4; per-weight granularity). The resolved values are dumped from a built jsc150 `xfm` on the
pin and copied, not paraphrased ([A22]). Widths are trainable and a weight can reach 0 bits
(pruned), which binary weights cannot. Biases, activation, softmax-output, exp-input and table
quantizers ([D19]), architecture E, head, `norm none`, optimizer, schedule, batch, epochs, PID
block, [D20] trace, selection rule, W&B project, data cache and seeds are A's. Expected 0-bit
floor: E's 171,526 (at 0-bit activations every weight term vanishes), labelled expected and
traced at PREFLIGHT [A7] before NB's canary. The binary gate (two symmetric nonzero values per
layer) does not apply to NB; its replacement check is the per-layer weight-width distribution
(fraction at 0 bits, mean bits) at the selected checkpoint and a test that no NB kernel is on
the static int8 grid ([A22]).

**H, defined [D23].** Model: jsc150 `xfm` (`get_transformer`: d24 input dense with fused
batchnorm and ReLU, tanh LUT, `QMultiHeadAttention` 2 heads, key_dim 16, FFN 32 → 24, global
average pool, 32/32/32 head, value-wise activation widths, weights kbi `SAT_SYM` b0 4, tables
`bc=Min(4)`, `beta0=0`) at N = 64 with 3 features. It is the only jsc150 transformer that builds
on the pinned `hgq2==0.1.9`: `xfmt` and the paper's Linformer need `QLinformerAttentionT`, which
the pin lacks. REPRO-CHANG ran this model (80.56 % test accuracy at 348k; single seed 42,
test-selected, unverified, JAX, open-loop β; context only). Everything outside the model is ours
so that ROC-test is identical to A's: our gated 90/10 cache, train-only standardization, stable
pT sort, float32 inputs, our ROC-test loader [A11], seeds 1-8 for init and `order_seed = f(s)`
for batch order, the Selection rule with non-degeneracy (H's own traced 0-bit floor in (b), the
same p_maj threshold in (c)), certification, divergence rule and W&B. H's training dynamics stay
his: per-batch `i` tracking, no per-epoch reset of the live model. Its EBOPs for selection are
the [D20] quantity, traced on a per-epoch **clone** of the live model over the full training
split (train only, `trace_minmax(reset=True)`); the traced clone is the candidate that is saved,
selected, certified and evaluated (flagged; alternative: the live-model reset trace A uses).
H's validation accuracy, validation macro AUC and test (c) are computed on the reloaded traced
clone, and H's BetaPID reads the clone's traced EBOPs, with the same per-epoch assertion as
`ablation.py:861-866` (42abed4b), so selection, control and the evaluated file use one model (amended
2026-09-27, arbiter v4 #2; [A23] unit test). Under regime B ([D15] branch executed
2026-09-27; arbiter v9 fix 1) the clone is traced on the traced epochs of slot T only, and H's PID
input between traces and its assertion follow slot P ([D20]). H's 0-bit floor has no number yet: REPRO-CHANG's 348k shows only that it is below 350k; it is traced
at PREFLIGHT [A7].

**H β control (pre-registered, flagged).** H uses our PID block [D5] at 350k, the paper's stated
method and the controller of A and NB, so H − NB does not also carry a controller difference.
Sun et al.'s code uses an open-loop `PieceWiseSchedule` (2e-8 → 3e-7 → 3e-6); the only evidence
that `xfm` trains under either controller is REPRO-CHANG under the open-loop schedule. The PID
has never run on `xfm`, so the second-wave canary checks that β moves from its initial 1e-7 by
epoch 10. `StopIf(ebops < 1e4)` is dropped: under the PID it cannot fire, and under either
controller it cannot fire if H's traced 0-bit floor exceeds 1e4 (checked at PREFLIGHT).

**H fidelity to Sun et al.'s code** (rows that differ from their `run_train.py` / `data.py`):

| field | their code | H | reason |
| --- | --- | --- | --- |
| backend | JAX, `tensorfloat32` matmul | TensorFlow, TF32 off | job-YAML pins (training-environment convention; no JAX pin), confound 9 |
| HGQ2 version | 0.1.10.dev (REPRO-CHANG venv) | 0.1.9 (pin) | job-YAML pins |
| data | `150c-*.h5`, features `[5, 8, 11]`, standardization on train + val, float16 | our gated cache, train-only standardization, float32 | identical ROC-test with A; [A23] confirms the feature mapping |
| seed | hard-coded 42 | init seed s, `order_seed = f(s)` | 8 seeds, order shared with A at s |
| β control | open-loop `PieceWiseSchedule` | PID [D5] at 350k | flagged above |
| stop | `StopIf(ebops < 1e4)` (absent from the pin) | none | cannot fire (above) |
| EBOPs for selection | in-training `FreeEBOPs`; `trace_and_save` on train + val after training | [D20] trace on a per-epoch clone (every 10 epochs under regime B, arbiter v9 fix 1), train only; validation metrics, test (c) and the PID read the reloaded clone | same feasibility quantity as A |
| selection | `ParetoFront` (val acc > 0.5, EBOPs < 5e5), test-selected in REPRO-CHANG | Selection rule, non-degeneracy, ≤ 350k | same rule as every arm |
| loop | `model.fit` | wrapped loop: candidate save and reload, resume, divergence isolation | [A23] |

**Pairing and comparisons (second wave).**

| comparison | varies | pairing / test |
| --- | --- | --- |
| A vs NB | weight quantizer only (binary `binary_absmean` against kbi learned width), on E, same recipe and target | paired by seed (t, df 7, sign count) if the [A22] `kernel_hashes` gate shows equal latent kernels at init at all 8 seeds; otherwise Welch for all |
| H vs NB | Sun et al.'s model and loop against ours, weight quantizer matched (both kbi), same data, split, recipe, controller, target and selection | unpaired (different shapes, different init); Welch; seed index and batch order shared; per-pair correlation descriptive |
| H vs A | everything in H − NB plus the weight type | reported as the algebraic sum (H − NB) + (NB − A) with its Welch interval; **no p-value** (not independent of the other two) |
| A vs FP32-E (2026-09-27, Kai request (second set)) | a package: weight type (binary against float), activation and softmax quantizers ([D19] learned-width WRAP against identity, softmax tables learned against fixed 21-bit), the 350k target with the PID and β term against none, the [D20] reset trace every 10 epochs (regime B), the width regularizers, and the feasibility filter ((a)-(c) against (c) only); both select on the same 701 slot-T epochs (Kai, STUDY v10 ESCALATE, 2026-09-28, K2); on E, same recipe | paired by seed if the [A25] gate passes at all 8 seeds, otherwise Welch; in the second-wave Holm family |
| NB vs FP32-E (2026-09-27, Kai request (second set)) | the same package with learned-width weights in place of binary | paired by seed directly when both pair with A; interval only, **no p-value**: over common seeds it equals (A − FP32-E) − (A − NB) |

Every second-wave table carries a GPU-class column: A − NB and H − A cross waves and may cross
GPU type (as R does); H and NB at the same seed share a pod.

## Confounds held fixed

Named one by one; each is identical across all 56 runs unless the arms table says otherwise.

1. **Input set and pT gate.** The same gate on train, validation and ROC-test sets for every
   arm, including R. The gate changes the input distribution, so no arm here may be compared
   with an ungated run (Round 14, N=8, the 5M confirmation runs).
2. **Split.** The same 90/10 permutation (one `split_seed`) for every run; n_train 558,000,
   n_val 62,000. The validation jets are identical across runs.
3. **Standardization.** `input_std` statistics come from the train split after the gate, so
   they are identical across runs because the split is.
4. **Normalization.** `norm none` in every arm. Nothing crosses a SubLN boundary (the
   historical W1-vs-W8 confound).
5. **Activation quantizer policy and init width.** The same [D19] quantizer in every arm;
   only the EBOPs target moves the widths, so A − R, A − B, C − A07-350 and A − D stay one-knob
   or package comparisons on the same quantizer.
6. **β controller.** The same PID block in every arm; only `target_ebops` differs (B at 250k,
   C at 5M).
7. **Data order.** The same `order_seed = f(s)` at seed s. R differs only because its batch
   differs.
8. **Initialization.** The same `experiment.seed` gives the same init for the same shapes (A,
   B, D, R on E; C and A07-350 on A07). `matching_initialization` (`ablation.py:61-78` in the screen bundle 7f9e9307; `:70-87` at 42abed4b) copies
   every equal-shape `kernel`, `bias` and `pos_table` by variable path. F (E + learned PE) shares
   A's kernels at seed s only if the no-PE E configs (A, B, D, R) consume the PE's RNG draw
   (`arch.pos_enc_none_consume_rng`, patch 0011); [A17] checks this at all 8 seeds and decides
   whether A − F is paired. A07 differs from E in shape, so A − A07-350 is unpaired.
9. **Numerics.** TF32 off and `jit_compile false` everywhere, so the checkpoint reload passes
   within 1e-7. Same-seed runs may sit in different pods (K=5 wave-1
   packing, Kai 2026-09-27; K=3 for the A07 pod). Every wave-1 pod runs on the A10 class, so
   every same-seed paired comparison stays within one GPU class. Pairing rests on TF32 off,
   `jit_compile false` and seeded data order, not on co-residency. This is also why a pilot
   checkpoint may resume into production at a different K. A run re-created on another class is
   flagged in the GPU-class column that every paired table carries. R, and any wave-2 pairing
   with wave 1 (A − NB), may cross pods and are covered by the same column (arbiter v9 fix 3).
10. **Selection and cost measurement.** The same rule and the same `compute_ebops` trace in
    every arm: the full training split (n = 558,000, the same rows in every run) under [D20]
    (was 256 train jets; staged in patches 0015, 0016 and 0023, the shipped tree is PREFLIGHT
    gate [A21]). Under regime B (Kai, 2026-09-27) the trace runs every 10 epochs in every traced
    arm, wave 2 included.
11. **Epoch budget.** R's 1,000 epochs is part of its package. A−R and D−R are package
    comparisons and are labelled so; they are never read as "the optimizer" or "epochs
    alone".
12. **Second wave.** What besides the variable of
    interest differs, and how each is handled:
    - A − NB: the weight quantizer only. Held fixed: architecture, biases, [D19] activation and
      softmax quantizers, recipe, PID, [D20] trace, cache, seeds, order and (if the [A22] gate
      passes) the latent-kernel init. Not held fixed: the wave (launch date, code sha, GPU class).
      The NB code is opt-in, and [A22] requires A's configs to reproduce byte for byte under the
      new tree, so the code sha changes nothing in A's build; GPU class is a column, TF32 is off
      in both. What NB can do that A cannot (prune weights to 0 bits, spend several bits on one
      weight) is the object of study, not a confound.
    - H − NB: a package. Architecture (key_dim 16 against 12, tanh LUT, fused batchnorm, 32/32/32
      head), value-wise against per-channel activation widths, jsc150's layer `beta0` 0 (under the
      PID both start from its initial β 1e-7; [A23] confirms), and the training loop (no per-epoch live reset trace, [D20] on a clone) all move together; weight
      quantizer, data, split, standardization, recipe, controller, target and selection are
      held. It is labelled "Sun et al.'s model and loop against ours", never "the architecture".
    - H − A: the H − NB package plus the weight type; descriptive only.
    - A − FP32-E (2026-09-27, Kai request (second set)): a package [D26]. Moves together: weight
      type, activation and softmax quantizers (fixed 21-bit softmax tables remain in FP32-E), the
      350k target with PID and β term, the [D20] reset trace every 10 epochs (regime B), the width
      regularizers and the feasibility filter. Held fixed (the candidate grid added 2026-09-28,
      Kai, STUDY v10 ESCALATE, K2): the 701 slot-T selectable epochs, architecture, biases, optimizer, schedule, batch,
      epochs, cache, split, order, seeds and (if the [A25] gate passes) the latent-kernel init.
      Not held fixed: wave, code sha and GPU class when FP32-E runs in the second wave (a column,
      as for NB). It is labelled "binary at 350k against unconstrained FP32", never "the weight
      type". NB − FP32-E is the same package with learned-width weights.

## Seeds

8 per arm (seeds 1-8). No N=64 seed spread exists, so this design produces the first one. The
95 % half-width on a seed mean with 8 seeds is t(0.975, 7)/√8 · sd = 2.365/2.828 · sd =
**0.836 · sd**; on a paired gap it is 0.836 · sd_diff. Checks: at sd = 0 the interval is
zero-width; for identical arms the paired gap is 0 with an interval around 0. At k = 6
feasible seeds (the claim floor) it is t(0.975, 5)/√6 · sd = **1.05 · sd**.
Pairing: A, B and D are paired by seed; C and A07-350 are paired by seed; R is paired by seed
index; A − F is paired (t, df 7, sign count) only if the PREFLIGHT `kernel_hashes` comparison
[A17] shows that only `pos_table` differs at every seed, otherwise Welch; A − A07-350 is Welch.
Second wave: A − NB is paired by seed if the [A22]
kernel-hash gate passes at all 8 seeds, otherwise Welch; H − NB is Welch (8 against 8, half-width
t(0.975, ≈ 14) · √(2/8) · sd = 1.07 · sd, **3.4 pt** at the archived 3.14-pt spread); H − A is
reported as the sum of the two, no p. At zero pair correlation A − NB resolves no better than
the 3.7 pt below; a ±1.0-pt paired half-width needs sd_diff ≤ 1.19 pt at 8 pairs.
FP32-E (2026-09-27, Kai request (second set)): A − FP32-E is paired by seed if the [A25] gate
passes at all 8 seeds, otherwise Welch; NB − FP32-E is paired directly, interval only, no p.
After 14 restarts to LR 3e-3 same-seed trajectories may decorrelate, so the report gives the
per-pair seed correlation of the accuracies beside every paired interval. The resolving power
of a paired gap rests on sd_diff, which is unmeasured: at zero pair correlation sd_diff ≈ √2 · sd,
so at the archived spread below the resolvable paired gap is about 0.836 · √2 · 3.14 = **3.7 pt**,
and a "flat" paired result (A − R, the Holm set) reads "cannot resolve below about 3-4 pt", not
"no effect".

Resolving power at the two sd bounds above:
- N=8 sd 0.19 pt (different N and recipe, 101 epochs, unconstrained): half-width ±0.16 pt at
  8 seeds.
- Archived N=64 binary sd 3.14 pt (same N, Round 14, sizing only): half-width **±2.63 pt**
  at 8 seeds, ±3.3 pt at k = 6. At that spread the distance A − 79.4 is known only to a few
  points, and any 1-pt statement is inside the interval: the 78.4 % descriptive line cannot be
  resolved, and the expected outcome at that spread is "straddles".
- To keep the half-width within ±0.5 pt the N=64 accuracy sd must stay at or below 0.6 pt
  at 8 seeds, or 0.48 pt at k = 6.

The epoch-500 readout [D13] gives the first estimate of that sd (validation, n = 62,000,
arm A). It is an early estimate after one cosine cycle and may understate the terminal
spread. Pre-registered consequence: if arm A's epoch-500 validation accuracy sd exceeds
0.6 pt, the result goes to Kai before epoch 1,000 with three options: continue as a
descriptive measurement, add seeds, or stop. The sd is computed over A seeds with a feasible,
non-degenerate checkpoint at epoch 500 (Selection rule); if fewer than 2 are, it is
**undefined**, and that is itself reported to Kai before epoch 1,000 with the same options. The
seed-mean validation accuracy is reported beside the sd, and the readout also goes to Kai if
that mean fails the non-degeneracy threshold (c), because collapsed seeds agree closely. The
readout still never selects a checkpoint or an arm.

## Selection rule (pre-registered, validation only)

Per run, among every traced epoch (regime B, every 10 epochs; [D15] branch executed) whose
freshly traced native HGQ2 EBOPs (trace sample [D20]) is at
or under that arm's target (≤, not <; Chang's `ebops < 5e5` is **not** used): take the checkpoint with the
highest **validation top-1 accuracy** (n_val = 62,000). Ties break in this order: higher
validation macro-OvR AUC, then lower EBOPs, then earlier epoch (key: accuracy → val AUC →
−EBOPs → −epoch). This is `checkpoint_selection_key` in `bnhgq2/ablation.py` with
`cost_before_auc=False`; the screen configs would run it with `cost_before_auc=True`
(`ablation.py:421` in the screen bundle 7f9e9307, `cost_first = bool(cfg.get('engram_study'))`), which puts −EBOPs before
val AUC, so [A13] enforces the stated order. This checkpoint is the runner's
`model_best.keras` at the terminal epoch, and the held-out set is evaluated on it.

- **Non-degeneracy (pre-registered 2026-09-27, arbiter v3 #1).** Under [D19] every arm's 0-bit
  floor is below its target, and the 0-bit state is a constant classifier (every WRAP channel
  outputs 0, [A20] test), so "EBOPs ≤ target" alone is met by a dead network. A checkpoint is
  **feasible** only if all three hold:
  - (a) its traced EBOPs ([D20] sample) is ≤ the arm's target;
  - (b) EBOPs − the arm's traced 0-bit floor > 0 (floors: E-family 171,526, F included (traced
    171,526, `cpu_gate_d21.log`); A07 343,053; second wave: NB expected 171,526 and H with no number yet, both
    traced at PREFLIGHT [A7] before their canary; FP32-E: (a) and (b) not evaluated, [D26]);
  - (c) its validation top-1 accuracy > p_maj + 5 · √(p_maj (1 − p_maj) / 62,000), where p_maj is
    the majority-class fraction of the gated `y_val`. The formula is fixed here; its value is
    computed at PREFLIGHT from the gated split by
    `campaigns/chang0926/nondegenerate_threshold.py` [A21] and recorded before the canary, and no threshold
    is set after any pilot number exists.

  A checkpoint that meets (a) and fails (b) or (c) is **feasible, degenerate**: counted
  separately per arm, never carrying an accuracy. The runner selects among checkpoints that meet
  (a) to (c): `model_best.keras` is updated only on an epoch that meets all three
  (`ablation.py:817-827, 846-847`, 42abed4b), so a degenerate checkpoint is never selected. In the per-epoch history
  (`ablation.py:879`) `budget_met` means (a) to (c); in the W&B run summary and `train_meta.json`
  it is the raw (a) test on the delivered checkpoint (`:965`, `:992`), including the
  `model_min_ebops.keras` fallback. k is counted from the selection tag (`selection` ≠
  `minimum_ebops_no_feasible_checkpoint`), the divergence record and the certification record,
  never from a `budget_met` field. The per-epoch `ebops_budget_met` is the raw (a) test (amended
  2026-09-27; arbiter v5 fix 7). The same test applies
  to the [A19] sensitivity checkpoint and to the A1000 and D1000 snapshots. Beside every EBOPs
  number the report gives **EBOPs above the 0-bit floor** (the usable budget). In the rest of
  this document "feasible" means (a) to (c).

- **EBOPs certification.** Before any ROC-test
  evaluation, every checkpoint that will be evaluated (primary, [A19] sensitivity, A and D
  epoch-1,000 snapshots) is reloaded and retraced with `trace_minmax(reset=True)` on the same
  full training split as [D20]. It is certified if the retraced EBOPs equals the EBOPs logged
  when the checkpoint was selected (relative difference ≤ 1e-6) and is ≤ the target.
  Certification uses the same `ebops_trace_sample` and `ebops_trace_batch` as the per-epoch trace
  (under regime B, the traced-epoch trace; arbiter v9 fix 1) (`certify_ebops.py`). A mismatch is a pipeline defect, never a reason to reselect: it blocks
  VERIFY for that arm until ml-engineer resolves it without reselecting; if unresolved, the seed
  counts as "no accuracy number" in k and both EBOPs values (logged and retraced) are reported per
  seed (amended 2026-09-27, arbiter v4 #1). A CPU certification mismatch follows the CPU→GPU
  re-run rule at the `.claude/memory/decisions.md` entry '2026-09-27 (orchestrator, PREFLIGHT gate
  v2)' (four conditions; Budget, pilot,
  "Certification check"; amended 2026-09-27, `review/PREFLIGHT_critical_v2.md`). No checkpoint
  is ever retraced on validation or ROC-test data; `predict` runs on the ranges as saved.
  Certification checks determinism, not accounting: at VERIFY, [A14] (our `compute_ebops`
  against HGQ2's own counter) also runs on the selected A-s1 checkpoint (arbiter v5 fix 7,
  optional C #16).

- **No feasible checkpoint.** If a run has none, it has **no accuracy number**. The runner's
  fallback, `model_min_ebops.keras` (selection `minimum_ebops_no_feasible_checkpoint`), is
  reported as "no feasible checkpoint" and never as the arm's result. A run whose best (a)
  checkpoint is degenerate is reported as "feasible, degenerate", also without accuracy. A seed
  whose selected checkpoint fails certification unresolved is reported as "certification failed",
  also without accuracy.
- **Divergence.** The runner raises on a non-finite loss or AUC. That run is a recorded
  outcome (divergence epoch, and the best feasible checkpoint before it if one exists). It is
  never relaunched with a changed LR, seed or config, and never dropped. A diverged run's
  pre-divergence best-feasible checkpoint is **not** evaluated for the arm mean or the paired
  gaps: a diverged seed counts as "no accuracy number", the same as an infeasible one. Its
  divergence epoch and pre-divergence validation metrics are reported.
  Infeasible, feasible-degenerate, diverged and certification-failed seeds form one class, "no
  accuracy number": wherever this document says "feasible" or "feasible and not diverged" for a
  mean or a paired gap, those seeds are excluded (amended 2026-09-27, arbiter v4 #1).
- **Arm summary.** Seed mean ± sample sd (ddof=1) over seeds that are feasible, not diverged
  and certified, with k/8 stated beside it. A claim needs k ≥ 6. That mean carries a survivor
  bias: the dropped seeds are plausibly the weakest, so it is an upper estimate of the arm.
- **Paired gaps** use seeds that are feasible and not diverged in **both** arms, with that
  count stated beside the interval. The feasibility and divergence rates are outcomes of
  their own, per arm, and between two paired arms they are compared with an exact paired
  test (McNemar exact, on the discordant seeds). Beside every paired gap the report prints the
  one-sided failure counts (seeds with an accuracy number in one arm only, per arm) and the
  both-failed count (seeds with no accuracy number in either arm); with fewer
  than 8 pairs every paired gap is labelled 'among k surviving pairs' (arbiter v6 fix 1; arbiter
  v7 fix 4).
- **Feasibility is the cost outcome.** Under the PID and the ≤ target filter the selected
  checkpoint's EBOPs sits at or just under the target by construction, so the report gives
  the feasible count, the feasible-degenerate count, the remeasured EBOPs and the EBOPs above
  the 0-bit floor, and does not present "reached 350k" as more than that count.
- **Winner's curse on validation.** The binomial SE of one checkpoint's validation accuracy
  near p = 0.79 is about 0.16 pt at n_val = 62,000 (0.12 pt at 124,000). The maximum over up
  to 7,000 checkpoints is therefore biased upward on validation. Held-out is untouched by
  selection, so the report gives the validation − held-out accuracy gap per run.
- **Sensitivity (labelled, not primary).** Among checkpoints that meet (a) to (c), the one with
  the highest validation macro-OvR AUC (ties: lower EBOPs, earlier epoch; the house rule in
  `quantization-and-cost.md`) is kept [A19] (`ablation.py:849-855`, 42abed4b) and evaluated on ROC-test
  beside the primary, labelled "AUC-selected sensitivity" (amended 2026-09-27 to match the code).
- **Interim readouts** at the end of epochs **500, 1000, 2000, 4000 and 7000** (one-based;
  each is the last epoch of a cosine cycle, with the LR at its 1e-6 floor). A readout reports
  the best-feasible-as-of-E snapshot [A6]: validation accuracy, validation macro AUC, EBOPs,
  feasible, feasible-degenerate and diverged counts per arm, and at epochs 500 and 1,000 the
  median EBOPs / target and EBOPs above the 0-bit floor per arm. **Validation only.** Interim readouts never select a checkpoint or an arm.
  The only consequence of a readout is the epoch-500 sd report to Kai (Seeds, [D13]). R reads
  out at 500 and 1000.
- **The held-out ROC-test set (n = 260,000)** is touched only after the terminal epoch, on
  checkpoints already fixed by validation. The terminal epoch is 7,000 (R: 1,000) unless it
  was changed before launch under [D15]. The evaluations, all pre-registered here, none of
  which selects anything:
  - every run: the primary selected checkpoint, and the AUC-selected sensitivity checkpoint
    [A19] (two evaluations);
  - A and D only: the best-feasible-as-of-epoch-1,000 snapshot ([A6], the same rule
    restricted to epochs ≤ 1,000), giving A1000 − R and D1000 − R (a third evaluation).
  - second wave: NB as every run above (primary and
    [A19] sensitivity); H **one** evaluation, the primary selected checkpoint (Kai). H's terminal
    epoch is 7,000 like A's, and the same [D15] epoch applies if it was changed before launch.
    FP32-E (2026-09-27, Kai request (second set)) as NB (two evaluations), selected under the
    reduced rule of [D26]: rule (c) only, on the 701 slot-T epochs (K2, 2026-09-28), no target,
    certification by reload determinism.

## Falsifier

Three claims carry a pass or fail: the budget claim, the recipe claim and the
optimizer-stability claim. Each is decided by its rule below. A fourth, the weight-type claim
(A against NB), belongs to the second wave and its own Holm family (below), as does, since
2026-09-27 (Kai request (second set)), the precision package A − FP32-E [D26]. The budget and stability claims
are count rules with no p-value in the decision. The recipe claim is the only claim with a
p-value (paired t on A − R), so Holm across the claims covers the recipe claim alone; Holm
also covers the secondary gaps (below).

**Budget claim:** "arm A (E architecture) reaches a feasible, non-degenerate checkpoint at 350k
in at least 6 of 8 seeds under this recipe."
- **Falsified** if fewer than 6 of 8 A seeds are feasible (a to c, Selection rule) and not
  diverged. The feasible-degenerate count is reported beside it. Under the current quantizer
  the static floor (A07 4,580,398, E 2,701,439, traced) is above 350k, so the claim as first
  designed was falsified before any GPU time ("Static floor of the current quantizer"); under
  [D19] E's traced 0-bit floor is 171,526, 178,474 below 350k, so the claim is decided by
  training.
- **Not falsified** otherwise, and worded as a count, not as "supported": "k/8 A seeds reached
  350k above the 0-bit floor and above chance (threshold (c) printed, about 0.21 on the gated
  `y_val`)", with each feasible seed's validation accuracy printed beside the count.
  Non-degenerate means not a constant classifier; it does not mean the model tags well. (The
  0.21 is review arithmetic on the ROC-test class fractions, n = 260,000, arbiter v4; the value
  used is computed at PREFLIGHT [A21]. Amended 2026-09-27, arbiter v4 #4; no new floor.) The
  claim does not test tagging quality: with 178,474 EBOPs of headroom a pass is expected, and the
  claim screens for controller failure (the PID never landing), divergence and degenerate
  collapse under budget pressure (arbiter v7 fix 8).

**A07-350 (descriptive, pre-registered expectation).** At 350k a feasible A07 checkpoint cannot
carry data-dependent attention (≥ 8,192 EBOPs needed, 6,947 available) and has at most 3
per-constituent input bits (Question). Expected attention state for every feasible A07-350
checkpoint: Q·K logits independent of the jet (at most position-dependent through the PE), at
most three 1-bit input channels in total across the per-constituent layers (`input_proj`,
`bit_block_0_attn_Wq`, `_Wk`, `_Wv`, `_Wo`, `bit_block_0_ffn_fc1`, `_fc2`; 2,048 EBOPs per input
channel at 1 bit in each, from `static_floors_arms_s1_d25.json` `one.per_layer`: 6,144 / 3 and
65,536 / 32); the post-pool head (`head_fc1`, 32 EBOPs per input channel at 1 bit, and
`head_fc2`) is reported separately and is not part of the expectation (amended 2026-09-27,
arbiter v5 fix 4). The report states whether each feasible A07-350 checkpoint matches this; a
mismatch in the attention logits or the per-constituent layers is a pipeline defect in the floor
accounting, sent to ml-engineer. C − A07-350 is the A07 target rung and A − A07-350 the labelled
architecture package.

**Primary measurement (descriptive, no pass or fail).** When the budget claim holds, the
report gives A's seed-mean ROC-test accuracy and the distance **A − 79.4 pt** with its 95 %
t-interval and k, and beside it: external reference single-model with no interval; its noise
is unpublished, [L1] puts its scale at about 1 pt or more (arbiter v8 fix 5g). Beside every
distance to 79.4 % the report states the softmax tax: of A's
350,000 EBOPs, 171,526 (49 %) is the E softmax floor, usable budget 178,474 (A07-350: 343,053,
98 %, usable 6,947); the Deep Sets comparand pays no softmax. It also states that the 2-head E
architecture under [D19] (any weight type, including NB) reaches 350k only
because the Q·K and A·V streams may prune to 0 bits, which the paper's protocol may not have
allowed ("Paper's ≥ 1-bit attention rule"); `xfm` (key_dim 16) is expected to be at least as constrained, traced at [A7] (arbiter v5 fix 7); A − NB is unaffected (shared floor). When k < 8 the distance is labelled an **upper estimate**: the dropped seeds
(infeasible or diverged) are plausibly the weakest, so the survivor bias of the arm mean
carries into the distance. The comparand is fixed now at 79.4 % (Deep Sets, HGQ) because the paper's
attention N=64 model collapsed into a Deep Set at this budget and input set (§3), so Deep Sets
is the published model at 350k and 3 features that attention actually reached. The
distances to Linformer 79.8 % and MHA 77.9 % are reported beside it in every outcome, whatever
the attention diagnostic shows. A pre-registered descriptive line sits at 78.4 % (1.0 pt
below 79.4 %): the report says whether the interval lies above it, below it, or straddles it.
That line is a description of where our number falls, not a test of binary weights, because
the reference's own uncertainty is at the scale of the line ([L1]). Beside the accuracy
distance, the report gives the per-class ROC-test AUC distances of A to Linformer and MHA at
N=64 (reference table, Fig. 2 legends; one model, read from the legend) and the macro distance
to their arithmetic means 0.9532 and 0.9428.

**Recipe claim:** "the Sun et al. recipe beats ours at 350k" (both on E).
- Supported if the 95 % interval of A − R lies above 0; falsified if it lies entirely below
  0; flat if it covers 0 (at zero pair correlation "flat" means "cannot resolve below about
  3-4 pt", Seeds). Paired over seeds feasible (a to c) in both arms.
- **R not feasible** (fewer than 6 of 8 R seeds feasible, a to c) while A meets the budget
  claim: reported as "R did not reach 350k non-degenerately in 1,000 epochs", with the A1000
  and D1000 feasible counts beside it and the exact paired test on feasibility. This is a
  statement about how fast widths fall under a small LR, not a tagging comparison: the word
  "beats" is not used, and no accuracy gap is reported for fewer than 6 paired seeds.
- Both not feasible: no recipe statement beyond the two feasibility counts.
- Expected branch for R, stated in advance: none. The old expectation ("R infeasible") came
  from the 50-epoch A07 screen at LR 2e-4 under the old quantizer, which plateaued at that
  quantizer's static floor; no dynamic evidence exists for E under [D19] at any LR, and the
  pilot does not run R.
- A1000 − R and D1000 − R are reported beside A − R, descriptive, labelled "epoch-matched".

**Optimizer-stability claim:** "Chang's optimizer verbatim does not diverge more often than
ours on binary weights" (A against D, both on E). Decided by a count rule on the marginal
divergence counts: falsified if the number of diverged A seeds exceeds the number of diverged D
seeds by at least 4 (for example 4 of 8 against 0). A smaller difference is reported as a count
and the outcome reads "not falsified at this resolution (8 seeds)"; the report never calls the
optimizer "safe". Beside the count the report
gives the exact McNemar p on the discordant seed pairs, **two-sided**, as a description outside
the Holm family (reach: 4-0 gives p = 0.125, 5-0 0.0625, 6-0 0.031, 7-0 0.016). The count rule
sees only non-finite failures (divergence, Selection rule), while the Round-14 N=64 binary
instability that motivates the claim showed as finite low-accuracy seeds (67.18 / 72.64 /
67.21 %, reference table). Beside the divergence count the report therefore gives, per arm, the
feasible-degenerate count, the seed range (max − min of selected-checkpoint
validation accuracy over seeds with an accuracy number, n = 62,000) and a low-accuracy count:
seeds more than 3 pt below the arm's best seed; and, for A against D (paired by seed), the
discordant counts: seeds where A is more than 3 pt below D at the same seed, and the converse. A
median reference is not used: it misses the case where half or more of the seeds are low
(Round-14: 0 of 3 flagged against the median, 2 of 3 against the best seed, range 5.46 pt). All
are descriptive and not in the decision rule (amended 2026-09-27, arbiter v4 #11; arbiter v5
fix 1).

Secondary gaps (C − A07-350, A − B, A − D, A − F) are reported with 95 % intervals and
Holm-adjusted across those four. They are descriptive ladders and carry no pass or fail claim.
Each is paired over seeds feasible (a to c) in both arms; a rung with fewer than 6 is reported as
counts only.

Family size under dropouts (fixed 2026-09-27, before any wave-1 or wave-2 number; arbiter v7
fix 3): m is the number of members whose gap is reported at VERIFY. A member reported as counts
only, for any reason, leaves the family and m falls by one. A member whose gap is first reported
after VERIFY is reported with its interval and no p, and the adjusted p-values already issued do
not change. m is printed beside every adjusted p.

**A − A07-350** (labelled architecture package, Welch) is reported with its 95 %
interval and k, **outside the Holm family and with no p-value** (amended 2026-09-27, arbiter v4
#25): its sign is fixed by construction (A07-350 has no data-dependent attention, Falsifier
"A07-350"), so a test would spend power on a foregone gap. C − A07-350 stays in: it is the
one-knob A07 target rung, and its size, not only its sign, is the open question.

**Second wave.** The second-wave comparisons form
**their own Holm family**, {A − NB, H − NB, A − FP32-E} (A − FP32-E added 2026-09-27, Kai
request (second set); NB − FP32-E is outside it, interval only, no p), separate from the first wave's four Holm-adjusted secondary gaps
and the recipe claim. Reason: they launch later and may land after wave 1's VERIFY, and a
first-wave family reopened by later arms would change adjusted p-values already reported. H − A
is not in the family: it equals (H − NB) + (NB − A) by construction (06-review §6.4), so it is
reported as that sum with its Welch interval and no p-value. A third member costs power on
A − NB: tested first at α/3 instead of α/2, and not testable once A − FP32-E has the smaller p
and fails; the direction makes A − NB harder to falsify, and the choice is fixed before any number
(arbiter v6 fix 11).

Family size under dropouts (fixed 2026-09-27, before any wave-1 or wave-2 number; arbiter v7
fix 3): m is the number of members whose gap is reported at VERIFY. A member reported as counts
only, for any reason, leaves the family and m falls by one. It leaves the Holm step-down order as
well. A member whose gap is first reported
after VERIFY is reported with its interval and no p, and the adjusted p-values already issued do
not change. m is printed beside every adjusted p. Direction: a smaller m makes the remaining
members easier to falsify, which is against the thesis in the second wave.

**Weight-type claim:** "at 350k EBOPs (iso-EBOPs, not iso-cost, [L2]) binary weights do not cost
accuracy against learned-width weights on the same model and recipe" (A against NB).
- **Headline** (amended 2026-09-27, arbiter v4 #8; first sentence amended 2026-09-28, arbiter v10
  F4): every A − NB statement registered for REPORT leads, in its first sentence, with the
  resolvable gap: the 80 %-power detectable gap at the realised n (paired t, α = 0.05 two-sided,
  noncentral t, at the measured sd_diff; 'Not falsified' below). The report then gives the lower
  95 % bound L of A − NB (amended 2026-09-27, arbiter v5 fix 2): If L ≤ 0: 'at 350k EBOPs (iso-EBOPs), binary
  costs at most |L| pt of top-1 accuracy against learned-width weights on this model (n pairs,
  95 %)', adding 'and at least |U| pt' only when U < 0 and the verdict below is 'falsified';
  otherwise the interval is printed and labelled 'unadjusted 95 %' (arbiter v6 fix 3). If L > 0:
  'at 350k EBOPs (iso-EBOPs), no accuracy cost of binary weights is resolved; A exceeds NB by at
  least L pt (n pairs, 95 %)'. The claim verdict below sits beneath it. The words 'at most |L| pt'
  are used only when all 8 pairs survive. With 6 or 7 pairs the headline reads '... among k
  surviving pairs' and prints the A-only and partner-only failure counts beside it, with one
  pre-registered sensitivity line: each A-only failed seed is imputed at the lowest ROC-test
  accuracy among the surviving A seeds and paired with its partner's actual ROC-test accuracy;
  partner-only failures stay excluded; the interval is recomputed over 8 − (partner-only) −
  (both-failed) pairs; seeds failed in both arms are excluded and counted beside it. The
  surviving-A minimum is used, not p_maj, because it is the least extreme value that does not
  assume a failed binary seed did better than every surviving one. The sensitivity line is
  labelled 'surviving-minimum imputation, not a worst case and not a measurement' and does not
  change the verdict (arbiter v6 fix 1; arbiter v7 fix 4).
  Prior, stated now: the direct-neighbour result (Sloot, FastML 2026; `.claude/memory/research-log.md`
  2026-09-01) has HGQ learned-width above binary on AUC (0.9276 against 0.9178; different task,
  16 high-level features, MLP; never tabulated beside ours), so the expected direction is A ≤ NB,
  and a wide interval is not support.
- **Resolution** (amended 2026-09-27, arbiter v4 #6, #7). The report prints beside the interval
  the 95 % half-width (arbiter v5 fix 2) at the measured paired sd_diff,
  t(0.975, n − 1)/√n · sd_diff at n pairs. Sizing is pre-registered as a formula before any
  number exists: from the wave-1 epoch-1,000 readout (validation, n = 62,000), the paired sd of
  A − D over feasible seeds is the sd_diff proxy, and the pairs needed for a ±1.0-pt half-width
  are the smallest n with t(0.975, n − 1)/√n · sd_diff ≤ 1.0 pt. It sizes a floor, not a
  guarantee (an epoch-1,000 sd may understate the terminal spread, Seeds). Table (arithmetic):

  | proxy sd_diff | pairs for ±1.0 pt |
  | --- | --- |
  | ≤ 1.19 pt | 8 (as designed) |
  | ≤ 1.57 pt | 12 |
  | ≤ 1.87 pt | 16 |
  | ≤ 2.01 pt | 18 |
  | ≤ 2.13 pt | 20 |

  The formula governs; the table is illustrative, with thresholds rounded down (8 pairs ≤ 1.19
  pt, 12 ≤ 1.57, 16 ≤ 1.87, 18 ≤ 2.01, 20 ≤ 2.13). The A − D proxy probably understates the
  A − NB sd_diff (NB can prune weights to 0 bits and follows its own PID path, so same-seed A and
  NB decorrelate more than A and D); it is a prior only. The second-wave epoch-500 readout was
  the binding input for extra pairs, which are declined (K3, below); that readout packet carries the paired A − NB validation sd_diff over
  feasible pairs, the feasible-pair count, the n the formula gives at max(proxy, measured
  sd_diff), and the 80 %-power detectable gap at 8 pairs and at that n, at the same sd_diff
  (noncentral t; arbiter v8 fix 4); it does not carry the A − NB mean gap or its sign.
  *Amended 2026-09-28 (Kai, STUDY v10 ESCALATE, K3):* A − NB is fixed at **8 pairs, with no
  extra pairs**, and the wide interval is reported as it is. The sizing formula and table above
  are kept as the record; the extra-pair rule (n read off the formula up to a Kai cap, A seeds 9
  to n, extra pairs appended after the 8-pair launch; arbiter v5 fix 3) is **declined**, and so
  are caps at 12 or 16. The epoch-500 packet stays descriptive: it sets no pair count. A stop on
  A − NB is reported as 'stopped at epoch 500' with the interim sd_diff.
- **Falsified** if the 95 % interval of A − NB lies entirely below 0 and its Holm-adjusted p
  (second-wave family) is below 0.05. Paired over seeds feasible (a to c) and not diverged in
  both arms, count stated, if [A22] pairs them; otherwise Welch.
- **Not falsified** otherwise, worded "not falsified at this resolution"; the report never says
  "binary costs nothing". There is no non-inferiority pass condition: at zero pair correlation
  and the archived spread the resolvable paired gap is about 3.7 pt (Seeds). The gap detectable
  with 80 % power (paired t, α = 0.05 two-sided, 8 pairs, noncentral t) is 1.16 · sd_diff: about
  5.2 pt at zero pair correlation and the archived spread (sd_diff = √2 · 3.145 pt), 1.4 pt at
  sd_diff = 1.19 pt and 1.2 pt at sd_diff = 1.0 pt (arithmetic). The Sloot prior is about 1 pt of
  AUC on a different task, not an accuracy prediction; a cost of that order is detectable at 8
  pairs only if sd_diff comes in at or below about 0.86 pt (1.0 / 1.16; arbiter v9), so 'not falsified at this resolution' is the expected
  outcome and the report says so (arbiter v8 fix 4). A 1.0-pt
  descriptive line (the scale of the 78.4 % line) is marked, and the report says whether the
  interval lies above −1.0 pt, below it, or straddles it; that line is a description, not a test.
- **Feasibility is its own outcome.** NB can prune weights to 0 bits and A cannot, so their
  feasible, feasible-degenerate and diverged counts are reported side by side with the exact
  McNemar test on the discordant seeds. If fewer than 6 of 8 NB seeds (or of the paired seeds)
  are feasible, no accuracy gap is reported, only the counts.
- Beside the gap, the report gives NB's weight-width distribution (fraction of weights at 0
  bits, mean bits per layer) and both arms' attention state and EBOPs above the 0-bit floor, so
  a gap can be read against where each arm spent its budget.
- Beside the accuracy gap, descriptive and outside the Holm family: the paired ROC-test
  macro-OvR AUC gap and the five per-class AUC gaps, each a 95 % interval over the same seeds
  (paired, or Welch where the accuracy gap is Welch; n = 260,000 per run), and per class the
  signal efficiency at mistag 10⁻² per arm (arbiter v7 fix 7).

**Precision package (FP32-E, added 2026-09-27, Kai request (second set)):** 'binary weights with
learned-width activations at 350k EBOPs cost no top-1 accuracy against the same E model in
unconstrained FP32, at this recipe' (package; A against FP32-E; not iso-EBOPs, [D26]). The report
prints the interval and never issues 'close' as a verdict (arbiter v6 fix 3).
- **Headline:** the lower 95 % bound L of A − FP32-E first. If L ≤ 0: 'binary weights with
  learned-width activations at 350k EBOPs cost at most |L| pt of top-1 accuracy against the same
  E model in unconstrained FP32 at this recipe (package, n pairs, 95 %)', adding 'and at least |U|
  pt' only when U < 0 and the verdict below is 'resolved cost'; otherwise the interval is printed
  and labelled 'unadjusted 95 %'. If L > 0: 'A exceeds FP32-E by at least L pt (package, n pairs,
  95 %)', and the result goes to the investigator before REPORT, with checks of FP32-E's selection
  epoch, train and validation curves, the [A25] pairing record and the byte-equal `y` check.
  Expected direction A ≤ FP32-E (one arm carries a budget); a wide interval is not support. The
  words 'at most |L| pt' are used only when all 8 pairs survive. With 6 or 7 pairs the headline
  reads '... among k surviving pairs' and prints the A-only and partner-only failure counts beside
  it, with one pre-registered sensitivity line: each A-only failed seed is imputed at the lowest
  ROC-test accuracy among the surviving A seeds and paired with its partner's actual ROC-test
  accuracy; partner-only failures stay excluded; the interval is recomputed over 8 −
  (partner-only) − (both-failed) pairs; seeds failed in both arms are excluded and counted beside
  it. The surviving-A minimum is used, not p_maj, because it is the least extreme value that does
  not assume a failed binary seed did better than every surviving one. The sensitivity line is
  labelled 'surviving-minimum imputation, not a worst case and not a measurement' and does not
  change the verdict (arbiter v6 fix 1; arbiter v7 fix 4).
- **Resolved cost** if the 95 % interval lies entirely below 0 and its Holm-adjusted p
  (second-wave family) is below 0.05; otherwise "not resolved at this resolution". No
  non-inferiority pass condition; the 1.0-pt descriptive line is marked as for A − NB.
- **Resolution at 8 pairs:** half-width 0.836 · sd_diff; ±1.0 pt needs sd_diff ≤ 1.19 pt. At the
  archived sizing spreads (N=64 binary 3.14 pt, FP32 0.3 pt, Round 14, sizing only) and zero pair
  correlation the paired half-width is about 2.6 pt, and Welch about 2.6 pt. No extra pairs are
  run for any comparison (A − NB stays at 8 pairs, K3, 2026-09-28); FP32-E adds no seeds.
- Fewer than 6 FP32-E seeds passing (c), or fewer than 6 pairs: counts only, no gap.
- A's and FP32-E's feasible, feasible-degenerate, diverged and certification-failed counts side
  by side, with the exact McNemar test on the discordant seeds (arbiter v6 fix 1).
- NB − FP32-E: paired interval, no p, same package label with learned-width weights.
- Beside the accuracy gap, descriptive and outside the Holm family: the paired ROC-test
  macro-OvR AUC gap and the five per-class AUC gaps, each a 95 % interval over the same seeds
  (paired, or Welch where the accuracy gap is Welch; n = 260,000 per run), and per class the
  signal efficiency at mistag 10⁻² per arm (arbiter v7 fix 7).
- Plausibility (pipeline check, not a result): if FP32-E's seed-mean validation accuracy at its
  selected checkpoints is below A's, FP32-E goes to ml-engineer before REPORT. The check is closed
  by a written record of four items: FP32-E's selected epochs, its train and validation curves,
  the [A25] pairing record and the byte-equal `y` check. If none shows a defect, A − FP32-E is
  reported with the trigger and that record beside it. An evaluation, pairing or `y` defect is
  fixed and FP32-E re-evaluated without reselecting; a training-side defect makes A − FP32-E
  counts only, with the defect named. Any distance of FP32-E to 79.4 % is a ROC-test descriptive
  distance at VERIFY, worded as FP32-E − 79.4 (the same descriptive form as A − 79.4), and triggers
  nothing (arbiter v7 fix 2; arbiter v8 fix 1).

**H (descriptive, no pass or fail).** H − NB (Welch, in the family) and H − A (the sum, no p) are
reported with 95 % intervals and k. H has **no binding reference** at VERIFY (06-review §6.8):
the paper's MHA-64 77.9 % is a one-head model that collapsed into a Deep Set, and REPRO-CHANG's
80.56 % is one seed, selected on test accuracy, unverified and never a comparand. H − 77.9 and
H − 80.56 are printed as descriptive distances, with those labels. H's k/8 feasible count and its
attention state are reported in every outcome. If H has fewer than 6 feasible seeds, the report
gives counts only; that outcome says the ported pipeline under our PID and selection rule does
not reach 350k non-degenerately, not that Sun et al.'s result fails.

Required diagnostic beside every accuracy number: **attention state** at the selected
checkpoint, three numbers. The width quantity is defined per channel as the magnitude bits
`relu(i+f)` together with the sign bit `k`; both are reported. Under the [D19] WRAP quantizer
a channel at `relu(i+f) = 0` outputs 0 and costs 0 EBOPs ([A20] unit test), a true zero, and
"0 bits" below means that. (Under the old SAT quantizer with k = 1, a channel at its floor,
i = ic.min and f = fc.min, is billed 1 bit by EBOPs but outputs exactly 0 at inference in HGQ2
0.1.9 (`FixedPointQuantizerBase.call`, `where(k+i+f > 0, ...)`; unit test
`test_channel_floor[SAT]`): silent and over-billed, not a live sign-only channel. The C′ pilot
arm reports such channels as "silent, billed 1 bit".) Beside the attention state, the report
gives the per-quantizer WRAP overflow fraction (values outside the traced range) on validation
and on ROC-test at the selected checkpoint ([L8]). A ROC-test overflow fraction above a
threshold labels that checkpoint's EBOPs "train-range EBOPs; deployment range wider". Threshold,
fixed 2026-09-27 before PREFLIGHT and before any pilot number (physics v4 C6): **0.1 % (10⁻³) of a
quantizer's values** (jets × constituents × channels) on ROC-test, in any one quantizer. Rationale:
a wrapped value is a full-range error, not a clip, and the range is traced on the full training
split [D20], so a same-distribution held-out set should overflow only in the far tail; 10⁻³ is
far above the counting floor at n = 260,000 jets. The label is descriptive: it selects, gates
and blocks nothing.
- the fraction of Q and K activation channels at 0 bits (Q/K at 0 bits gives constant
  logits, a uniform softmax and a mean pool of V: the Deep-Set collapse);
- the fraction of V activation channels at 0 bits (V at 0 bits removes the attention branch;
  the remaining path is Deep-Set-class: φ, mean pool, ρ, position-aware through the learned
  PE in F and A07-350);
- the mean attention entropy over the validation jets (n = 62,000) as a fraction of log 64
  (row-renormalized, [A26]) (near 1 means uniform attention, a Deep Set, even when every width is ≥ 1 bit, which is the
  paper's collapse).

Collapse label (fixed 2026-09-27, before the pilot's epoch-500 readout; arbiter v8 fix 3): a
checkpoint is labelled 'Deep-Set-class' if every head meets at least one of
(i) all Q channels or all K channels at 0 bits, (ii) all V channels at 0 bits, (iii)
row-renormalized entropy / log 64 ([A26], no key mask) at least 0.99. Constant logits give a
uniform row over all 64 slots, padding included, so the unmasked [A26] value is 1 for that
collapse. For FP32-E only (iii) applies. A07-350 is Deep-Set-class by construction (Falsifier,
'A07-350'); its measured label is printed beside that expectation, and a disagreement is
reported, not relabelled. Every arm summary and every gap that reports an arm's accuracy
(including A's k/8 summary, A − 79.4, the recipe claim, the four Holm secondary gaps,
A − A07-350, C − A07-350, A − NB, A − FP32-E and H − NB) prints per arm the count of seeds whose
selected checkpoint carries the label. The label is descriptive, like the overflow label: it selects, gates and
blocks nothing.

Widths come from `activation_widths.jsonl`; entropy from one validation forward pass [A26]
(arbiter v6 fix 10). The diagnostic describes the model. It does not change the comparand.

Figures (pre-registered, made at REPORT):
- primary measurement (amended 2026-09-27, arbiter v4 #10): per-seed A ROC-test accuracies with
  the seed mean and 95 % t-interval (k in the legend), horizontal lines at 79.4 % (comparand),
  78.4 % (descriptive line), 79.8 % (Linformer) and 77.9 % (MHA) (single-model, external;
  arbiter v5 fix 7), caption "ROC-test, n = 260,000, external
  references single-model with no interval; their noise is unpublished, [L1] puts its scale at
  about 1 pt or more";
- recipe ladder (amended 2026-09-27, arbiter v4 #10): a paired-gap panel for A − D, D − R, A − R,
  A1000 − R and D1000 − R (Δ accuracy with its t-interval and n_pairs), GPU-class note in the
  caption (R may cross GPU type, confound 9);
- per-class ROC on ROC-test with a log mistag axis and the seed band (sd, ddof = 1, seed count
  in the legend, k stated when k < 8), arms A and R (E, 350k) named in the legend, caption
  "ROC-test, n = 260,000"; A07-350 (350k) and C (5M) in a separate panel with each arm's EBOPs
  above the 0-bit floor in the legend, so budgets are not mixed on one axis (amended 2026-09-27); the legend prints each arm's
  per-class ROC-test AUC as seed mean ± sd (ddof = 1, k) (arbiter v8 fix 5f);
- per run, the selected epoch and its cosine-cycle index, and the best-feasible validation
  accuracy per cycle (14 points per Chang-schedule run; R has no restarts and reports its
  selected epoch only), labelled "validation, n = 62,000" (amended
  2026-09-27);
- two accuracy-versus-EBOPs ladders, E (B at 250k, A at 350k) and A07 (A07-350 at 350k, C at 5M),
  each rung labelled with its EBOPs above the 0-bit floor, so 350k and 5M do not read as
  comparable capacities; beneath each, a paired-gap panel (Δ accuracy with its t-interval and
  n_pairs), not unpaired error bars on the accuracy axis; k in the legend when k < 8; a rung with
  no feasible seed is drawn as an empty marker at its target labelled "no feasible checkpoint
  (0/8)", and feasible-degenerate seeds are counted in the label, never omitted;
- attention state per arm at the selected checkpoint (fraction of Q/K and of V channels at 0
  bits, entropy / log 64 (row-renormalized, [A26]); widths at the selected checkpoint from
  `activation_widths.jsonl`, entropy on validation, n = 62,000; the 0.99 collapse cut drawn),
  with A07-350's pre-registered expectation marked;
- validation − held-out accuracy per run (winner's curse);
- interim-readout figures labelled "validation, n = 62,000".
- second wave: a paired-gap panel for A − NB (Δ accuracy,
  t-interval, n_pairs, the 1.0-pt descriptive line marked) beside the Welch intervals of H − NB and
  H − A, labelled "second wave, ROC-test, n = 260,000", GPU class in the caption; a per-class ROC
  figure with A, NB and H named; the legend prints each arm's per-class ROC-test AUC as seed
  mean ± sd (ddof = 1, k) (arbiter v8 fix 5f); attention state for H and NB added to the per-arm figure; NB's
  per-layer weight-width distribution (fraction at 0 bits, mean bits) at the selected checkpoint;
  a per-class paired AUC-gap panel for A − NB and, separately, A − FP32-E (arbiter v7 fix 7).
  FP32-E (2026-09-27, Kai request (second set)): A − FP32-E and NB − FP32-E in a paired-gap
  panel of their own, separate from the A − NB panel (iso-EBOPs and package gaps never share a
  panel; arbiter v6 fix 11), labelled "package: 350k against unconstrained FP32"; FP32-E in the per-class ROC figure
  and, entropy only, in the attention figure; no EBOPs position for FP32-E on any EBOPs axis.

## Budget

**Symbols.**
- s_e: seconds per epoch per process at K processes per pod. Measured by the canary
  (mean over zero-based epochs 10-29, two whole trace cycles, trace epochs included; a median
  would exclude the trace epoch; regime B, arbiter v9 fix 1), and split into a train-step part and a per-epoch overhead part
  (save, reload, validation predict, `compute_ebops`).
- T_run = 7,000 · s_e (R: 1,000 · s_e,R).
- Pod-hours (Chang schedule) = (48 / K) · T_run.
- Pod-hours (R) = (8 / K_R) · 1,000 · s_e,R.
- Wall clock = ceil(runs / (P · K)) · T_run, for P pods.

**Illustrative projections, not measurements.** Superseded as the basis by the measured canary
([D15] branch executed, below). Kept as the registered prior. Batch 2,790 on a 558,000-jet train split is
200 steps per epoch, against about 2,180 at batch 256.
- At s_e = 30 s: T_run = 58.3 h (2.4 d); 48 runs at K=6 on 8 pods ≈ 467 pod-hours.
- At s_e = 60 s: T_run = 116.7 h (4.9 d); ≈ 933 pod-hours.
- At the A07-N64 prior, with no speed-up from the larger batch: the 2026-09-22 screen logged
  **100.09 s** for one epoch of `const0922-a07-n64-s1-fast50-fp32`
  (`campaigns/2026-09-22-constituent-screen/live-status.json`, `last_epoch_wall_seconds`; one
  packed epoch, batch 256, n_train 496,000; the number of co-packed processes is not in that
  field; unverified ops number). Scaled to 558,000 train jets: 112.6 s. T_run = 8.1 d
  unscaled, **9.1 d scaled**. 48 runs at K=6 on 8 pods ≈ 8 × 9.1 d ≈ 1,750 pod-hours
  (prior, superseded; pod-hours = pods × T_run from the regime-B canary).
- R: 1,000 epochs at 112.6 s (same prior, scaled; a projection) is 31.3 h per run; 8 runs at
  K_R = 4 on 2 pods ≈ 63 pod-hours (prior, superseded; pod-hours = pods × T_run from the regime-B canary).
- Other fields in the same file belong to other arms and are not used for A07: 83.53 s is
  E02 at N=8, 189.68 s is A02 at N=64.
- Under [D21] 40 of the 56 runs are the smaller E architecture. No E timing exists at any
  batch, so the A07 prior is kept for every arm; for E it is a projection that probably
  overstates s_e, and the canary measures it.

**[D15] branch (measured 2026-09-27).** The prior expected 'fits 14 days'; the K=6 canary
measured 17.4-17.8 d for A and D, and the branch fired (see '[D15] branch executed'). The per-epoch
overhead (save, reload, 62,000-jet validation predict, the [D20] trace) does not shrink with the
batch, and batch 2,790 is unmeasured. Under [D20] the trace is a forward pass over 558,000 jets,
so the overhead is larger than the prior assumes. Pre-approved default ([A21]): **one**
full-split trace per epoch on the live model (regime A; under regime B one per traced epoch, see
'[D15] branch executed'); the post-reload check compares the stored `i`,
`f`, `k` and EBOPs of the reloaded candidate with the saved ones and does not trace again. The
canary measures the trace's share of s_e. No pre-approved change shrinks the trace sample: if it
breaks the 14-day rule, that is the [D15] Kai branch.

**Trace-cost risk to the expected branch (amended 2026-09-27).** On CPU a full-split reset trace
costs about 0.66 × one training pass, for E and for A07 alike (`code/evidence/trace_cost_cpu.json`:
0.657 and 0.664 on 16,740 synthetic rows; laptop, not the GPU number, not a result), and
`trace_minmax` runs eagerly per batch, so the GPU ratio may be worse. If the ratio carries over,
s_e rises by up to about 1.66 ×: at the 112.6 s prior (the 100.09 s A07 basis scaled to 558,000
rows) that is about 187 s, T_run ≈ 7,000 × 187 s ≈ 15.1 d, over the 14-day rule. The expected
branch "fits 14 days" therefore holds only if the trace and reload-check overhead add at most
53 % to the prior (172.8 / 112.6 = 1.53). Pre-registered rule: the canary reads
`ebops_trace_seconds` and `ebops_trace_over_epoch` (patch 0023) (from the W&B history) over the
s_e window (Symbols) and projects
T_run = 7,000 × measured s_e with the trace included. If T_run ≤ 14 d, launch as designed. If
T_run > 14 d, production does not launch and the case goes to Kai; [D20] forbids shrinking the
trace sample without him, and no option is pre-approved. Options put to him: a full-split trace
every k epochs, with candidates saved every epoch but the feasibility test applied only on traced
epochs (never on the in-training EBOPs, which would break [D20]) and the certification retrace of
the selected checkpoint unchanged; a different `train.ebops_trace_batch`; accepting T_run > 14 d;
and the [D15] options below (terminal epoch at a restart boundary, the cheap version). The trace
is outside the pre-approved "overhead > 50 % of s_e" changes ([A15] cadence, W&B and width-record
writes), which may not alter it. The pod count is answered (Kai,
2026-09-27): 8-10 pods, one wave, about 9 d at the A07 prior (prior, superseded; pod-hours = pods × T_run from the regime-B canary); P = 2 (4 waves, about 36 d) and
the cheap version were declined.

**[D15] branch executed (2026-09-27, Kai-decided; `.claude/memory/decisions.md` entry
'2026-09-27 (Kai, [D15] branch after the canary)'; arbiter v9 fix 1).** The K=6 canary on an
A10 (`RUN.md`, "Canary (epoch 10)" and "Canary — W&B history pull"; telemetry, not results)
measured a mean of 219.65 / 219.37 / 215.16 s per epoch for A-s1 / A-s2 / D-s1 over epochs
1-10 (T_run 17.8 / 17.8 / 17.4 d), 163.88 s for E1-s1 (13.3 d) and 293.6 s for C′-s1 over epochs
1-5 (23.8 d). The [D20] trace took a median 0.42 of each A or D epoch (30 epoch samples). The
single-wave T_run exceeded 14 d, so the registered branch fired and production did not launch.
Kai chose the option registered above as "a full-split trace every k epochs", with k = 10
(**regime B**). Declined: accepting about 18 d, and K=3 with about 22 pods. Under regime B:
(1) the [D20] full-split reset trace runs on the traced epochs only, which are
[slot T, patches 0027-0031, bundle 42abed4b] zero-based epoch e is traced iff
e == 0, (e + 1) % k == 0 or e + 1 equals the run's epoch count (`is_traced_epoch`,
`code/tree/bnhgq2/ablation.py:483-489`; k is `train.ebops_trace_every`, validated at `:461-480`),
with k = 10: the ends of epochs 1, 10, 20, ..., 7,000 in one-based numbering, 701 traces per
Chang-schedule run and 101 in R (`tests/test_trace_every.py::test_key_semantics`; `plan.md`,
'Which epochs are traced'). The ends of epochs 1, 10, 500, 1,000, 2,000, 4,000 and 7,000 (canary, readouts,
A1000 / D1000, R's terminal epoch) are traced, and a snapshot cadence that is not a multiple of k
is refused (`:477-479`), so every 500-epoch snapshot falls on a traced epoch. The end of epoch 1
**is** traced (the `epoch == 0` clause, `:489`, added on the coordinator's request; `plan.md`,
'Which epochs are traced'). It is not needed to initialize the ranges: the full-split reset trace
before training (`initial_ebops`, `:714-718`, unchanged from regime A) does that. The canary
comparison pair is therefore the traced end of epoch 1 (zero-based 0) against the traced end of
epoch 10 (zero-based 9), not `initial_ebops` against epoch 10. The key `ebops_trace_every: 10` on every
[D20] config is set by `code/tree/campaigns/chang0926/generate.py:57` (patch 0029), and the full
CPU gate on the 42abed4b extraction prints `TRACE_EVERY_OK` for 58 of 58 configs (50 with
`traced_epochs 701`, 8 with 101; `code/evidence/cpu_gate_shipped_42abed4b_full.log`);
(2) the feasibility test (a)-(c) is applied only on traced epochs, and only a traced epoch that
meets (a)-(c) can become `model_best.keras`. An untraced epoch is recorded as "untraced", never
as feasible or infeasible. The `model_min_ebops.keras` fallback and the [A19] sensitivity copy
use traced epochs only. [slot C, bundle 42abed4b] a candidate is still saved, reloaded and validated every epoch
(`ablation.py:795-805`; `plan.md` DECISION R-B2), so the [A12] non-finite validation check runs
every epoch, but an untraced candidate is never selectable: the budget test, feasibility,
`model_best`, `model_best_auc_feasible` [A19], `model_min_ebops`, `model_unconstrained` and the
recovery freeze are evaluated only when the epoch is traced (`:817-818`, `:838-858`). The
candidate is reloaded into one validation model per run (patch 0031, `ValidationReloader`,
`:589-608`, used at `:764`, `:797`: `load_model` at the first epoch of a process, `load_weights`
of each later candidate into the same model), tested equal to a fresh load byte for byte
(`tests/test_memory_leak_fix.py`); this is the leak fix of `review/INCIDENT_stall_20260928.md`
(PREFLIGHT, 'Regime B addendum'), and what is validated is still the serialized file. Epoch
counters such as `feasible_degenerate_epochs` count traced epochs only (`:829-832`; 701 per
Chang-schedule run, 101 for R), and are reported with that denominator. The checkpoint cadence is
unchanged: a full checkpoint every 25 epochs (`campaigns/chang0926/generate.py:133`;
`ablation.py:922-926`), a boundary snapshot every 500 (`generate.py:134`; `ablation.py:928-931`),
the W&B artifact every 500 (`generate.py:135`). The selected file is written at the traced epoch
itself (`ablation.py:847`), and the next 25-epoch checkpoint carries it (`plan.md`, (c));
(3) between traces, BetaPID reads [slot P, bundle 42abed4b] the in-training EBOPs of the last training step: hgq2 0.1.9
`BetaPID.on_epoch_end` reads the stored `layer.ebops`, which no trace overwrites on an untraced
epoch (`model_ebops`, `ablation.py:492-495`, read at `:783`; `plan.md`, (a)). On a traced epoch
the trace runs before `pid.on_epoch_end` (`:788-789`, `:860`), so the PID reads the traced EBOPs,
as in regime A. The PID input is therefore a 9:1 mixed series of in-training and traced values
(`plan.md` DECISION R-B1), and between traces the controller holds the in-training EBOPs, not
the traced value, at target. The every-epoch assertion cited as `ablation.py:698-703` (`:729` in
the tree before patch 0027) is split: on a traced epoch the PID EBOPs equals the traced total
within 1e-6 relative (`:861-866`), on an untraced epoch it equals the in-training total
(`:867-871`). The controller stays our [D5] BetaPID; jsc150 uses a fixed β schedule, so only the
number, not the controller, matches its `FreeEBOPs`. Both the in-training and the traced
EBOPs are logged at every traced epoch, and the pilot readout reports their ratio per run.
Measured under regime A (one epoch of drift, all runs 23-36 % above target; RUN.md, 'In-training
vs traced EBOPs', telemetry): in-training / traced median 1.072-1.092 for A, D, E1 and 1.000 for
C′. At a constant ratio r the integral term settles traced EBOPs near T · r^−0.9 (arithmetic,
hgq2 0.1.9 `PID.__call__`, p 1, i 0.05, no anti-windup). The near-target regime-B value is
unmeasured (arbiter v10 F7). *Amended 2026-09-28 (Kai, STUDY v10 ESCALATE, K1 = (b);
`.claude/memory/decisions.md` 2026-09-28 top entry):* a threshold on this mismatch is
pre-registered before any regime-B epoch-500 number exists; it is stated in full in the pilot
rules ('Regime-B PID input rule'), and it is evaluated at the pilot's epoch-500 readout from the
in-training / traced ratio on traced epochs;
(4) [slot P, continued] between traces each WRAP datalane quantizer follows HGQ2's in-training
tracking, i ← max(i − i_decay_speed, i_batch) per training step (hgq2 0.1.9
`FixedPointQuantizerKIF.call`; `plan.md`, (b)), with `i_decay_speed` 1e-3 [D25]; on a traced
epoch the full-split reset trace of [D20] resets the live model's ranges (`traced_ebops`,
`ablation.py:703-704`, `ebops_calc.py:20-21`, called at `ablation.py:788-789`), and training
continues from them. C′ has no WRAP quantizer. The reset every 10 epochs remains a deviation from
jsc150, which never traces during training (fidelity row 'WRAP range update');
(5) certification of every evaluated checkpoint (Selection rule) is unchanged: a full-split
reset retrace, relative difference ≤ 1e-6, same `ebops_trace_sample` and `ebops_trace_batch`;
(6) regime B applies to every arm that has a [D20] trace, in wave 1 and wave 2 (NB, and H on its
clone), so confound 10's "same rule in every arm" holds. FP32-E has no trace ([D26]);
(7) the epoch count (7,000; R 1,000), the restart period, the LR peak and batch 2,790 are
unchanged. Nothing is truncated.
The 14-day rule now binds on the regime-B canary: T_run = 7,000 × s_e, with s_e measured over
whole trace cycles (Symbols). The arithmetic from the measured split (RUN.md: trace 90.61 s,
remainder 127.45 s) gives s_e ≈ 136.5 s and T_run ≈ 11.1 d at K=6. Kai's figure of about 9 d at
K=5 is also arithmetic. Neither is a measurement. If the regime-B canary's T_run exceeds 14 d,
production does not launch, and the case goes back to Kai.
T_run is evaluated per production pod class as the largest T_run of its arms, and the wave's
T_run is the largest over its pod classes (arbiter v10 F1). The classes, from `packs.json` /
`packs_meta.json` (`arms_per_pack` [5, 5, 5, 5, 4 × 9]): E pods at K=5 (four pods), from the K=5
pilot pod's s_e; E pods at K=4 (three pods, the same E arms with one fewer co-resident process),
also from the K=5 pilot pod's s_e, taken as an upper bound, not a measurement; A07 pods (C,
A07-350; K=4, four pods) from an s_e measured at their production K over the Symbols window, or
at K=3 if they are packed at K=3. The K=3 pod's s_e is not taken for K=4, so the A07 pods at
K=4 are untimed until then. R (K=4, two pods) runs 1,000 epochs. If the A07 pods exceed 14 d
while the E pods pass, production of the A07 pods waits for Kai (K=3 or K=2 on more pods, or stop
the A07 arms). Beside the 136.5 s E arithmetic, the A07 arithmetic from RUN.md (C′-s1, regime A,
epochs 0-4: mean train step plus validation 163.3 s, mean trace 130.4 s): 163.3 + 130.4 / 10 ≈
176.3 s, T_run ≈ 14.3 d, above the 172.8 s bound. It is a projection, with constructive v10 B3's
caveats: five epochs including epoch 0, C′ is SAT and not [D19] WRAP, K=6 under contention with
five other arms, and A07-350 has no timing (out of memory).

**Pods (prior A10 packing; superseded for future launches by the dated GPU amendment above).** Wave 1 was planned on the A10 class in 13 pods (Kai, 2026-09-27, [D15] branch executed): K=5
for the E arms (four pods; the remaining E runs in three pods at K=4), K=4 for the A07 pairs and
R (`packs.json`; arbiter v10 F6, with the K=4 E pods named). Six arms per seed do not fit one K=5
pod, so same-seed runs may sit in different pods;
the production pod map is fixed at PREFLIGHT from the regime-B pilot's measured peak GPU memory
per process (the A07 arms from the K=3 pod).
Each same-seed comparison runs on one GPU class (confound 9); the GPU class of every run is
recorded in its evaluation JSON and shown in a GPU-class column of every paired table. (Prior
plan, superseded by the K=5 packing above:) That makes 8 pods for the Chang schedule and 2 pods for R
(K_R = 4, packed separately because its epoch count differs). If the canary shows K=6 does
not fit in GPU memory at batch 2,790, the block splits into two pods of K=3 (A, B, D and C, F,
A07-350), giving 16 pods (the seed-block layout in this paragraph is the prior plan, superseded
by the K=5 packing in its first sentence; arbiter v9 fix 1). Arms per pod are declared in `bnjettag.io/arms-per-pod`, with about 2
CPU and 6 Gi of host memory per arm (rule PACK, 40 % GPU floor, 3 h lookback, 3 strikes).
The former A100 ban and A10-only wave-1 restriction are superseded by the dated GPU amendment.
Use the selected, certified product per seed's comparison block, with a resource request and K
measured for that product. Node counts are capacity and not live free GPUs. No
C-synthesis on `mulder` in this campaign.

**Pod count (Kai, 2026-09-27 08:40 PDT, `.claude/memory/decisions.md`).** 8-10 pods in one wave
(10 with R), about 9 d at the A07 prior (prior, superseded; pod-hours = pods × T_run from the regime-B canary); the canary refines it. Kai's original brief ("a couple
of pods") is recorded with its date in `plan.md` ("Kai's brief"). If the canary moves the
single-wave projection above 14 days, [D15] applies. Superseded 2026-09-27 by Kai's packing (K=5
on the A10 class, about 13 wave-1 pods, about 27 at peak with wave 2 and Delta).

**Timing canary and feasibility pilot** (phase 2; pre-registered here; one pod):
- **Pod.** One pod with K=6: **A-s1, A-s2** (E), **D-s1** (E), **A07-350-s1**, **C′-s1** and
  **E1-s1** (E with `n_heads 1`, d24, pilot-only like C′). Amended 2026-09-27: [A7] traced E1
  feasible with real headroom, so **E1-s1 is in the pilot and B-s1 is not** (job indices
  `[0, 1, 24, 48, 56, 57]`, `pilot_packs.json`). E1 floors (CPU, synthetic sample, not results;
  `code/evidence/static_floors_fix6_a07_e_e1.json`): 0-bit 85,763, 1-bit-alive 533,435,
  headroom at 350k 264,237; per-head additivity confirmed for the softmax term only (E1 × 2 = E).
  E1 is the only traced architecture feasible at 350k under the narrow datalane reading of the
  paper's ≥ 1-bit attention rule (282,371, headroom 67,629); that rule stays a Kai row, not the
  default. Batch 2,790, on the GPU class production will use (not A100). W&B on, into
  the canary group. Every run except C′ is under [D19]. **C′** is A07 with the Chang recipe
  (optimizer, schedule, batch as arm C) on our **current** quantizer (SAT with k = 1, fixed 10-bit
  softmax output, fixed tables) at a 5,000,000 target; static floor 4,580,398 traced, so 5M sits
  9.2 % above it. C′ and E1 are **not among the 56 runs**; C′ reads the declined branch of
  [D19], E1 the one-head option. All six use the [D20] trace sample. The pilot configs are
  regenerated under [D21] before the canary; the pod generated from the v3 text (with E-s1,
  E-s2 and A07 A-s1, A-s2) must not ship. B-s1 to B-s8 are the E-architecture configs with
  `target_ebops 250000` and every other field equal to A at the same seed (0-bit floor 171,526,
  headroom 78,474). [A20] builds on the pinned `hgq2==0.1.9`, so the C′-only fallback below is
  not triggered.
  *Amended 2026-09-27 (arbiter v8 fix 2; `RUN.md`; `.claude/memory/cluster-inventory.md` entry
  'K=6 pack, batch 2,790, two of six N64 arms OOM repeatedly on a 23 GiB A10 (2026-09-27)'):* on
  an A10 (23,028 MiB) the K=6 pilot pod lost A07-350-s1 to out-of-memory on all three attempts
  (`ARM_FAILED_AFTER_RETRIES`), C′-s1 trained only on its third attempt, and the resident arms
  used 18.8-22.6 GiB. K=6 does not fit at batch 2,790 on that class, so the registered branch
  'If K=6 does not fit in GPU memory, repeat the canary at K=3' applies. (1) A07-350-s1 re-runs
  in a separate pod at K=3 on the same GPU class, batch 2,790, stage pilot, W&B canary group,
  with C-s1 and F-s1 (the fallback seed block that holds A07-350). The pod launches once the
  full-set CPU gate on the shipped bundle ([A21]) has passed for C and F; the pods holding
  A07-350 or C wait for Kai's packing answer in any case, so the wait delays nothing. No
  batch is lowered: batch 2,790 is part of the recipe in the question. (2) The canary rules
  apply per pod: the K=6 pod's canary covers the arms that trained in it, and A07-350-s1's
  canary (stability, s_e, peak GPU memory per process) and its epoch-500 readout (the
  A07-350-s1 rule below) come from the K=3 pod. (3) Wave-1 pods that hold A07-350 or C launch
  only after the K=3 pod's A07-350-s1 epoch-500 readout exists and, on a mismatch with the
  A07-350 expectation, after ml-engineer has fixed the floor-accounting defect; other wave-1
  pods launch under the rules registered here. (4) The [D15] packet to Kai carries s_e and peak GPU memory per
  process from both pods, the pod count at K=3 (16 seed-block pods and 2 R pods, against the
  8-10 answered) and the GPU classes whose memory holds the measured peak; production packing
  and any restriction of GPU classes are Kai's decision. (5) If C′-s1 is lost to out-of-memory,
  the C′ report to Kai reads 'no pilot data (out of memory at K=6)', not 'infeasible'.
  *Amended 2026-09-27 ([D15] branch executed, Kai-decided; arbiter v9 fix 1):* a second pilot
  runs under regime B on the same seeds: a K=5 pod with A-s1, A-s2, D-s1, C′-s1 and E1-s1, and the
  K=3 pod of (1) above (A07-350-s1, C-s1, F-s1), which now runs under regime B. Both are built on
  the patch-0027 bundle after its PREFLIGHT addendum ([A21] re-asserted, full-set CPU gate,
  [A17]). Both pilot-b pods run on NVIDIA A10 only (Kai, 2026-09-28) and exclude node
  hcc-nrp-shor-c6017 (GPU NaN, `campaigns/2026-09-27-delta-screen/REGRESSION_TICKET.md`,
  2026-09-28). Each pilot-b pod runs a GPU fingerprint gate before any arm starts: anchor arm-A
  s1's `initial_ebops` must equal the verified integer recorded in PREFLIGHT ('Regime B
  addendum'), or no arm starts. If an arm goes out of memory in the K=3 pod, the registered
  fallback is to relaunch that arm alone or at K=2 on the same bundle and run root.
  The K=6 regime-A pod is descriptive only; it was stopped on 2026-09-28T05:31Z on Kai's
  decision (host-memory leak, `review/INCIDENT_stall_20260928.md`), with checkpoints A-s1 and
  A-s2 at epoch 125, D-s1 at 150, E1-s1 at 75 and C′-s1 at 25 and **no epoch-500 snapshot**
  (`RUN.md`, 'Stopped 2026-09-28T05:31Z'). The pilot rules above (canary,
  A rule, certification check, A07-350-s1 rule, C′ rule) are applied to the regime-B pods, and
  those gate production. The certification check also runs on the regime-A pod's snapshots, and
  a mismatch in either pod stops production, only if those runs are resumed to epoch 500 on
  77f1ca4e (`readout-a-job.json` is kept for that; PREFLIGHT, 'Regime B addendum'). The regime
  comparison, the same arm and seed under
  A and B at epoch 500, is reported descriptively, under the same condition: traced EBOPs, the number of feasible traced
  epochs, the ratio of in-training to traced EBOPs, β, and best-feasible validation accuracy
  (never quoted). It selects nothing, triggers nothing, and does not reopen the regime choice. A
  return to regime A is a Kai decision. The matched traced-epoch table in the Phase 2 rules
  ('Regime A/B table at matched traced epochs', arbiter v10 F5) needs no resume. Regime-A pilot checkpoints cannot resume into production
  (`code_sha256` and `config_sha256` differ under patch 0027). Regime-B pilot checkpoints may
  resume if both shas match the production bundle.
- **Phase 1, canary (stability checks at epoch 10; timing over zero-based epochs 10-29, Symbols).** Timing and stability, as below. Then the same pod
  continues without restart.
- **Phase 2, feasibility pilot (to the end of epoch 500, one cosine cycle).** About 19 h at the
  regime-B arithmetic (500 × 136.5 s at K=6; K=5 unmeasured), a projection. **Validation only, never quoted, never selects an arm or a checkpoint, and does
  not switch the primary default.** Rules, evaluated once at the end of epoch 500 on each run's
  best-feasible-as-of-500 snapshot (or its minimum EBOPs if none meets (a)), with "feasible"
  meaning (a) to (c) of the Selection rule:
  - **A:** if neither A pilot seed has a checkpoint at 350k above the 0-bit floor and above
    chance (threshold (c) printed; non-degenerate means not a constant classifier, not that the
    model tags well) by epoch 500, production waits for Kai with the options: re-target from the traced [A7] floors, a one-head
    or Linformer primary, or stop. (The v2 clause "median A EBOPs > 3 × target" stays dropped: it
    sits above the 1-bit-alive floor and a near-empty model passes it.) If the regime-B PID input
    rule below fires, a failed A rule is reported as "not attributable (regime-B PID input)"
    (Kai, STUDY v10 ESCALATE, 2026-09-28).
  - **Reported per run** (A, D, A07-350, E1): the fraction of the headroom in use,
    (EBOPs − 0-bit floor) / headroom (A and D: (EBOPs − 171,526) / 178,474; A07-350:
    (EBOPs − 343,053) / 6,947; E1: (EBOPs − 85,763) / 264,237), feasible / feasible-degenerate /
    diverged, the attention state (Q/K and V channels at 0 bits, entropy row-renormalized [A26],
    and the collapse label, arbiter v8 fix 3), and the
    best-feasible validation accuracy (descriptive, never quoted, selects nothing). Entropy
    comes from the [A26] offline script on the retained epoch-500 snapshot; if that script and
    its CPU tests are not ready by the epoch-500 readout, the readout prints entropy as
    "pending, computed from the retained epoch-500 snapshot", and the entropy is filled in
    before wave-1 production. No pilot pod is restarted for it (arbiter v6 fix 10).
  - **A07-350-s1** reports whether its attention state matches the pre-registered expectation
    (Falsifier, "A07-350"); a mismatch in the attention logits or the per-constituent layers goes
    to ml-engineer as a floor-accounting defect (arbiter v5 fix 4). If the regime-B PID input rule
    below fires, a failed A07-350-s1 rule is reported as "not attributable (regime-B PID input)"
    (Kai, STUDY v10 ESCALATE, 2026-09-28).
  - **Regime-B PID input rule** (amended 2026-09-28, Kai, STUDY v10 ESCALATE, K1 = (b);
    `review/STUDY_arbiter_v10.md` K1; pre-registered before any regime-B epoch-500 number).
    Readout, per pilot-b run with a [D20] trace (A-s1, A-s2, D-s1, E1-s1, C′-s1, A07-350-s1, C-s1,
    F-s1), from the in-training / traced ratio r on traced epochs (slot T; both values are logged
    there, slot P (3)): median r over traced epochs 100-500, the implied traced offset
    350k × (1 − r^−0.9) (5M × (1 − r^−0.9) for C and C′), and its share of the arm's headroom.
    **Threshold.** The rule fires if, for any run, the implied traced offset exceeds 10 % of that
    arm's headroom (A/D 17,847; E1 26,424; A07-350 695; by the same formula, arithmetic, F 17,847
    and C 465,695), or the per-arm median r differ by more than 0.02 between any two arms of an
    iso-EBOPs comparison (A, D, F, A07-350, C), or an A07 run's in-training EBOPs stays above
    350k on every untraced epoch of the last cycle while its traced EBOPs sit within 1 % of its
    floor (the A07-350 wind-up of arbiter v10 case 5, reading 1; under reading 2 this clause does
    not fire; untraced in-training EBOPs are read from W&B `ebops_in_training`, the float
    `model_ebops(model)` of `code/tree/bnhgq2/ablation.py:492-495`, logged at `:783` and `:894`,
    not from the stdout `in_training_ebops=` field, which prints `saved_ebops` at `:791`, `:933`).
    B has no pilot run and is not in the rule: its r is read at production epoch 500 and reported
    beside every A − B and budget-ladder number as a descriptive caveat (offset
    250k × (1 − r^−0.9), share of B's headroom 78,474); it fires nothing and stops no pod.
    If the rule fires, production waits for Kai, who chooses at the epoch-500 readout between
    **(c)** the PID reads traced EBOPs only and holds β between traces (re-freeze and a new pilot)
    and **(d)** each arm's setpoint is scaled by its measured r (feasibility stays at the traced
    target; `config_sha256` changes); and a failed A rule or A07-350-s1 rule is reported as "not
    attributable (regime-B PID input)" beside the registered options. (c) is prepared now by
    ml-engineer as a **staged, unapplied patch**, so a choice at epoch 500 does not start from
    zero; it enters only as a dated amendment before any affected pod is applied. Declined (Kai,
    2026-09-28): (a) report only; (c) now; (d) now. **Expected:** on the regime-A medians (RUN.md,
    'In-training vs traced EBOPs'; telemetry, far from target) the rule would already fire: the
    implied offsets are 22,658 / 21,753 / 21,147 EBOPs for A-s1 / A-s2 / D-s1 (11.8-12.7 % of
    the A/D headroom; arbiter v10 gives 12-15 %) and 26,654 for E1-s1 (10.1 % of E1's), and
    E1 − D is 1.0920 − 1.0717 = 0.0203 > 0.02 (arithmetic from the RUN.md medians). So (b) in
    practice means "measure r near target under regime B, then choose (c) or (d) at epoch 500".
    Descriptive readout; it selects nothing and does not stop the running pilot-b pods.
  - **Regime A/B table at matched traced epochs** (arbiter v10 F5; descriptive, zero GPU,
    selects nothing). In the pilot-b readout: A-s1, A-s2 and D-s1 (and, where regime-A epochs
    exist, E1-s1 to epoch 88 and C′-s1 to epoch 47) at the one-based traced epochs 10, 20, ..., 120,
    under regime A (W&B history, which traced every epoch; RUN.md) and regime B (pilot-b): traced
    EBOPs, in-training EBOPs, r, β, feasible yes / no. It replaces most of the regime comparison
    in the 'Pod.' bullet above, which needs a regime-A resume that nobody plans.
  - **Certification check.** Each feasible best-as-of-500 snapshot is reloaded and retraced
    on the full training split; the retraced EBOPs must equal the logged value (relative
    difference ≤ 1e-6). A mismatch stops production until ml-engineer fixes it.
    *Amended 2026-09-27 (`review/PREFLIGHT_critical_v2.md`, decision 6; rule pre-registered at
    the `.claude/memory/decisions.md` entry '2026-09-27 (orchestrator, PREFLIGHT gate v2)' before
    the readout Job is applied; arbiter v7 fix 9d):* the epoch-500
    readout certifies on CPU. (1) A CPU certification that disagrees with the logged EBOPs is
    re-run exactly once on the GPU product RUN.md records for that pilot pod; that GPU result is
    final. (2) The re-run is allowed only when `stored_ebops == logged_ebops`; a stored mismatch
    is a defect at once, whatever the `EBOPS_MISMATCH` label says (`certify_ebops.py:89-91`).
    (3) The GPU readout manifest is produced by `manifests/freeze.py` and named before use.
    (4) Any CPU/GPU disagreement is reported in RUN.md and VERIFY.md, and production's final
    certification runs on the training GPU class.
  - **Before the pilot reaches epoch 500** (amended 2026-09-27, `review/PREFLIGHT_critical_v2.md`
    flag 3): a CPU dry run of the whole readout, `certify_ebops.main()` and
    `analysis/attn_entropy.py` end to end, on a synthetic cache and run root. `main()` has never
    run end to end. A defect found there needs a new bundle and ConfigMap for the readout Job
    only; no pilot run's `code_sha256` changes.
  - **Replay check after a cross-class re-create** (amended 2026-09-27,
    `review/PREFLIGHT_critical_v2.md` flag 4): if a pod is re-created on a different GPU class,
    the epoch-500 replay check (`verify_selected`, AUC and accuracy at atol 1e-7) may fail
    without real data loss. Such a failure is re-run on the original GPU class before it is
    called a defect; RUN.md records the GPU product per pod.
  - **D:** reported as above; no rule of its own.
  - **C′ (one seed, descriptive only, no falsification):** reports whether C′-s1 has a
    feasible checkpoint at or under 5,000,000 by epoch 500, its minimum EBOPs, and that minimum
    divided by the 4,580,398 traced static floor, plus the attention state with Q/K and V
    channels at their SAT floor labelled "silent, billed 1 bit". Rule: if C′-s1 is infeasible
    at epoch 500, the report to Kai says the alternative "add C′ at 5M" is not supported by the
    pilot; if feasible, it says C′ is a viable 8-seed arm, near its floor. C′ goes into
    production only if Kai adds it.
  - **C, constraint-active readout (pre-registered 2026-09-27, before any arm-C data exists;
    descriptive only; source `campaigns/2026-09-27-delta-screen/review/STUDY_physics_v3.md` B2).**
    Under [D19] the A07 0-bit floor is 343,053 (traced), so C's 5,000,000 target is about 14.6×
    the floor; 5M was set against the old quantizer's 4,580,398 floor. If BetaPID stops pushing,
    C is an effectively unconstrained binary A07. Three quantities, per C run:
    (i) the fraction of traced epochs (slot T; the pre-training `initial_ebops` trace excluded)
    whose traced EBOPs is > 5,000,000, the complement of test (a); denominator 51 at the
    epoch-500 readout (zero-based e = 0, 9, 19, ..., 499), 701 in production;
    (ii) the selected checkpoint's traced EBOPs / 5,000,000 (pilot: the best-feasible-as-of-500
    snapshot, or the `model_min_ebops.keras` fallback if none is feasible, labelled as such;
    production: the certified primary checkpoint);
    (iii) whether β, read as logged at the end of each traced epoch, sits at its [D5] lower bound
    1e-10 (relative difference ≤ 1e-6) on every one of the last **N = 10 traced epochs** of the
    window (100 training epochs: ends of epochs 410-500 at the pilot, 6,910-7,000 in production).
    N = 10 is a designer choice, not a derived number. (β at a traced epoch was set at that
    epoch's `on_epoch_begin` from the preceding epoch's EBOPs, an in-training value under regime B.)
    **Rule:** a run is "constraint slack" iff (iii) holds **and** no traced epoch in the same
    last-10 window exceeds 5,000,000; if (iii) holds and m > 0 of them exceed it, the run is
    labelled "β at floor (integral wound up), 5M exceeded on m of 10" (arbiter v10 F2). (i) and
    (ii) are reported beside it and decide nothing. The pilot applies it to C-s1 at the epoch-500 readout (regime-B K=3 pod) as a
    single-seed indication to Kai, not a label. At VERIFY every arm-C number carries
    "constraint slack in k of 8 seeds", and when k ≥ 5 it is labelled "constraint slack (5M does
    not bind under [D19])". The readout selects nothing, gates nothing and triggers nothing:
    feasibility (a)-(c), certification, the A07-350-s1 rule and C − A07-350 in the Holm family
    are unchanged.
    **C′:** the same three quantities, the same N and the same rule (with the F2 clause) are reported for C′-s1 at
    epoch 500 (5M sits 9.2 % above its 4,580,398 traced floor, so it is expected to bind; this is
    reported, not assumed), with (i) taken over the EBOPs series its runner applies test (a) to
    and that series named in the readout; descriptive only, beside the C′ rule above.
  - The pilot's result goes to Kai; production launches only if the A rule and the
    certification check pass and, if the regime-B PID input rule fired, Kai has chosen (c) or (d)
    (Kai, STUDY v10 ESCALATE, 2026-09-28).
- **Fallback if [A20] needs an HGQ2 pin change.** If the ml-engineer finds that Chang's
  quantizer set cannot be built on the pinned `hgq2==0.1.9`, a pin change is a
  training-environment convention change and is Kai's decision. Until he decides, the pilot pod
  runs **C′-only arms**: C′-s1 to C′-s6 at K=6 on the current code path, the same schedule,
  epoch 500, validation only, with the C′ rule above applied per seed and reported as a count.
  Those checkpoints resume into production only if Kai adds C′ and `config_sha256` and
  `code_sha256` match; once [A20] lands, `code_sha256` changes, so they probably cannot.
- **Reports** s_e, split into train-step and overhead; the trace time is reported per traced
  epoch and amortized over the cycle; peak GPU memory per process; in-pod
  `nvidia-smi` utilization (mean, median, p10); host RAM peak and CPU cores; bytes per epoch
  of `activation_widths.jsonl`; checkpoint size; and `df` on the `kai-data` PVC, whose free
  space has not been measured.
- **Stability** (the canary fails on any of these):
  - loss finite at every epoch, and epoch-10 train loss below epoch-1 train loss, for A and D;
  - β at epoch 10 differs from its initial 1e-7 (PID moving);
  - traced EBOPs ([D20] sample) (regime B: both ends are traced epochs of slot T, zero-based 0
    and 9) at the end of epoch 10 below that at the end of epoch 1, for every arm that trained in the pod (per-pod reading, arbiter v8 fix 2). The
    ratio epoch-10 / epoch-1 (under regime B too, both traced, slot T) is reported beside the screen's A07-N64 trajectory under the old
    quantizer, 24,816,782 at zero-based epoch 0 and 7,610,858 at epoch 9, ratio 0.31
    (`review/STUDY_investigation_350k.md`; W&B, seed 1, LR 2e-4, not a result).

  Sources (arbiter v9 fix 2): train loss, `ebops_trace_seconds` and `ebops_trace_over_epoch` are
  read from the W&B run history (`ablation.py:754-755`; the per-arm log line at `:783` prints none
  of them; line numbers in bundle 77f1ca4e, which the K=6 regime-A pod ran until it was stopped on
  2026-09-28T05:31Z; bundle 42abed4b (patch 0027)
  adds train loss and both trace fields to the log line, `ablation.py:934-937`, `:941`, so the regime-B
  pods' canary can also be read from the arm log). A check whose input cannot be read counts as a
  canary fail for that arm, not a pass.
  DECISION R-B5 (`plan.md`, accepted): the three fields are printed on every [D20] epoch line, with
  or without `ebops_trace_every`. With the key absent, records, checkpoints and EBOPs are
  byte-identical to 77f1ca4e, and the stdout epoch line gains the three trailing fields
  (`code/evidence/regression_trace_every_absent_42abed4b.{json,log}`). Accepted, since it is stdout
  format only.
  The K=6 pod's canary was read from W&B on 2026-09-27 (`RUN.md`, 'Canary — W&B history pull'):
  train loss finite and falling from epoch 1 to epoch 10 for A-s1, A-s2 and D-s1, and a trace
  share with a median of 0.42. C′-s1 had no epoch-10 read and is recorded as not evaluated.

  The LR is at least 2.99e-3 through epoch 10, so the canary sits on the first peak. The same
  peak returns at every restart, and the canary cannot cover those ([L4]).
- **Host memory (regime-B pods; after the stall incident, `review/INCIDENT_stall_20260928.md`;
  PREFLIGHT, 'Regime B addendum'; bundle 42abed4b).** The regime-A pod's arms grew by about
  80-95 MB of host RSS per epoch until the pod's memory cgroup filled. Fixes and gates, all CPU-tested,
  none yet proven on a GPU:
  - the validation model is loaded once per run (`ValidationReloader`, slot C, patch 0031);
  - `run_pack` (patch 0030) gives each attempt a fresh heartbeat clock (`run_pack.py:85-90`), does
    not charge a pod-wide stall (`POD_STALL`, `:197-199`) to the per-arm retry budget (a separate
    budget of 2 applies, `plan.md` DECISION R-B7), and prints `POD_MEM` (cgroup memory and each
    live arm's RSS) every poll (`:151`);
  - the RSS projection gate (`BNJ_RSS_GATE_WINDOW=5:105`; `ablation.py:632-679`, stepped at
    `:938-940`): a least-squares fit of host RSS over zero-based process epochs 5-104; verdict at
    the end of the 105th process epoch: baseline + slope × `train.epochs` must be ≤ the per-arm
    limit L in the manifest; otherwise `RSS_GATE_FAIL.json` and exit 5, which `run_pack` does not
    retry (`run_pack.py:224-225`; `plan.md` DECISION R-B8). L per pod (6,144 MiB: Kai, PREFLIGHT gate
    v3 escalation, `decisions.md` 2026-09-28; 8,192 MiB: ml-engineer sizing entry, `decisions.md`
    2026-09-28 'per-arm memory 6 → 8 GiB', c7bae4a; the running/new split: arbiter v10,
    orchestrator note (2), and RUN.md '8 GiB swap timing'): the **running** K=3 pod
    `kai-chang0926-pilotb3-42abed` (applied 2026-09-28T23:05Z from the 4dbf6b6 manifests) runs at
    6 GiB per arm with `BNJ_RSS_GATE_LIMIT_MB=6144`, so L = 6,144 MiB until it is swapped to the
    8 GiB manifest before process epoch 105; the Pending K=5 pod is deleted and re-applied from
    the 8 GiB manifest (RUN.md, '8 GiB swap timing', 'Pods still Pending'; cluster-ops records the
    re-apply in RUN.md, and until then that pod's L is the one it was applied with); the **new**
    manifests (c7bae4a: the re-applied K=5 pod, the swapped K=3 pod, the fallbacks, the readouts
    and production) set
    8 GiB per arm and `BNJ_RSS_GATE_LIMIT_MB=8192`, L = 8,192 MiB;
  - operational canary rule (coordinator, 2026-09-28; formula after PREFLIGHT gate v3, Kai
    2026-09-28): cluster-ops reads `POD_MEM` and the per-arm RSS (` host_rss_mb=` on the arm
    log) at the ends of process epochs 10 and 20 and stops the pod if, for any arm,
    rss20 + (rss20 − rss10)/10 × 85 > L, the per-arm limit of that pod as above: 6,144 MiB for the
    running K=3 pod until its swap, 8,192 MiB under the new manifests. The projection runs only to
    process epoch 105, where the RSS gate gives its verdict; the rule exists because a leak the
    size of the incident's would fill the per-arm limit before that verdict (near epoch 48 at
    6 GiB, near epochs 64-76 at 8 GiB). It is not
    projected to epoch 7,000 because a two-point difference ten epochs apart, extended 700×,
    turns RSS noise into a stop (`review/PREFLIGHT_critical_v3.md` A2).
  These are operational: they select nothing and change no arm, seed, target or rule.
- **If K=6 does not fit in GPU memory**, repeat the canary at K=3. Memory prior: three A07
  N=64 processes at batch 256 used 3,849 of 23,028 MiB on one A10
  (`.claude/memory/experiment-log.md` 2026-09-24). Batch 2,790 raises activation memory per
  step roughly 11× (2,790/256 = 10.9), so the K=3 fallback is not unlikely.
- **If per-epoch overhead exceeds 50 % of s_e**, the pre-approved changes are the [A15]
  cadence change and moving W&B and width-record writes off the epoch path. None of them may
  touch the per-epoch candidate save, reload, validation and feasibility test that feed
  selection (under regime B the feasibility test runs on traced epochs only, and the candidate
  cadence is slot C). The canary is re-run after any such change.
- **Outputs.** The projected finish date (from s_e as redefined in Symbols, regime B), and the pod-hours from the formulas above.
- **Canary and pilot checkpoints** may be resumed into production only if `config_sha256` and
  `code_sha256` match. Regime-A pilot checkpoints do not match (patch 0027); see the regime-B
  amendment.

**Launch policy [D15].**
- **Single-wave T_run ≤ 14 days** (s_e ≤ 172.8 s): launch as designed, all runs to 7,000.
- **Single-wave T_run > 14 days:** do **not** launch the full set. Report to Kai with
  options: a terminal epoch at the largest restart boundary (2,000 or 4,000) that fits, fewer
  pods in waves, or the cheap version. Nothing is truncated silently, and the 500-epoch
  restart period and 3e-3 peak are never changed to save time.

**Resume.** Relaunch under a new Job name, with the same ConfigMap, code sha, configs,
`--root` and arm names. The trainer refuses to resume on a `config_sha256` or `code_sha256`
mismatch; confirm `resume_epoch=N` in the pod log. `podFailurePolicy` is Ignore on
DisruptionTarget (the 2026-09-17 incident). `activeDeadlineSeconds` is set deliberately to
cover T_run plus margin, or left unset; either way it is stated in PREFLIGHT.md.
`nrp_doctor` flags any pod silent for more than 2 h.

**Checkpoint cadence [D14].**
- Resume checkpoint every 25 epochs, keeping the latest two generations. This is a code
  change, not a setting [A15]: the runner writes the full checkpoint every epoch.
- The candidate save, reload and validation stay every epoch; they make the selected file the
  evaluated one. Under regime B the candidate cadence is the one slot C states ([D15] branch
  executed, arbiter v9 fix 1).
- A boundary snapshot at every 500 epochs (the best-feasible-as-of-E model and state).
- `model_best.keras`, `model_min_ebops.keras` and `model_unconstrained.keras` as the runner
  keeps them.
- W&B: scalars every epoch. The `resume-<name>` checkpoint artifact is uploaded only at the
  500-epoch boundaries, replacing the screen's `remote_every_epochs 25`, which would make 280
  versions per Chang-schedule run and 40 per R run (48 × 280 + 8 × 40 = 13,760 across the 56 first-wave runs).
- Optionally, a Pareto front on (validation accuracy, EBOPs), for descriptive plots only and
  never for selection.
- If the canary shows the per-epoch width records would exceed the PVC budget, write
  per-channel widths to `activation_widths.jsonl` every 25 epochs and scalars every epoch.

**Cheap version** (offered beside the full one; declined by Kai 2026-09-27). Arms A, D and R (on E), 4 seeds each (12 runs; 2
Chang-schedule pods at K=4 plus R packed with them or in 1 pod), terminal epoch 2,000 (four
restart cycles).
- **It answers:** whether binary weights survive LR 3e-3; whether N=64 reaches 350k under
  this recipe; and the recipe's effect against ours.
- **Cost:** 8 Chang-schedule runs × 2,000 epochs = 16,000 run-epochs, against 48 × 7,000 = 336,000 in the full design (about 1/21), plus 4 R runs against 8.
- **Loss:** the 95 % half-width is t(0.975, 3)/√4 · sd = 1.59 · sd, against 0.836 · sd.
  There are no budget or architecture ladders, and the terminal epoch is 2,000, not 7,000.

**Second wave ([D24]).**
- **Runs.** 24 (H, NB and FP32-E, seeds 1-8); 80 with the first wave (amended 2026-09-27, Kai
  request (second set); was 16 and 72).
- **Launch gate.** Each arm launches when its code passes the CPU gates ([A22] NB, [A23] H,
  [A25] FP32-E) and its second-wave PREFLIGHT section is reviewed, and only after the wave-1
  pilot A rule has passed (or Kai has named the anchor). Each arm launches on its own gates; any
  subset that passes launches. Before launch, PREFLIGHT records that the cache sha256,
  `split_seed` and `order_seed = f(s)` generator are byte-identical to wave 1's; a mismatch stops
  the launch, because pairing with A rests on them. Expected gate line once FP32-E joins: if
  FP32-E is in the wave-1 gate, `PREFLIGHT_ALL_PASS 66 production 64 pilot_only 2` (the full wave-1 set, 58
  and 56, `cpu_gate_d25.log:119`, plus FP32-E's 8 configs, [A25]; the shipped bundle 77f1ca4e
  was gated only on the `--only A,D,A07-350,C-PRIME,E1` subset, 26 / 24 / 2,
  `cpu_gate_shipped_77f1ca4e.log:55`, so B, C, F and R are not gated on a shipped bundle until
  the full-set gate on the production bundle passes, a PREFLIGHT prerequisite of wave-1
  production, [A21]; arbiter v8) (arbiter v7 fix 9g); otherwise a second-wave gate line of the same form,
  with FP32-E's 8 configs counted in its production total (arbiter v6 fix 11).
- **Pods.** Seed-pair blocks at K=4: pod j holds H and NB at seeds 2j − 1 and 2j (4 pods), so H
  and NB at one seed share a GPU (K=6 with FP32-E, 2026-09-27, Kai request (second set); see
  "FP32-E" below). H runs under TensorFlow with the job-YAML pins ([A23]), so it
  needs no JAX pods; it has its own runner, so the pack runner launches two runner kinds, each
  under [A12] isolation. If only one arm passes its gates, it launches alone as 2 pods at K=4
  (seeds 1-4, 5-8), and the other follows under the same rule.
- **Overlap with wave 1 (Kai-confirmed 2026-09-27, second set).** If the second wave starts while wave 1 runs, 14 pods run at
  once (10 + 4), above the earlier 8-10; Kai confirmed the overlap (superseded 2026-09-27: about
  13 + 4, about 27 at peak with Delta; Kai, [D15] branch executed). Alternatives: wait for wave 1 to finish (about 9 d later at
  the A07 prior (prior, superseded; pod-hours = pods × T_run from the regime-B canary)); or, if NB's gates pass before wave-1 production launches, add NB-s to wave-1
  pod s (K=7; same GPU as A-s, A − NB then crosses no GPU type), subject to a K=7 re-canary as in
  FP32-E's launch rule (below) passing (i) to (iii) with NB-s in slot 7 (arbiter v6 fix 2)
  (closed by Kai's K=5 packing, 2026-09-27; no slot 7 exists; reopening it is a Kai decision).
- **Cost (projections, not measurements).** No H timing exists (REPRO-CHANG's job YAML reads
  "wall time unknown → 48 h ceiling", `_attic/repro-chang/jobs/repro-chang/kai-repro-chang-xfm-n64.yaml:10`,
  and its completion time is not recorded). At the A07-N64 prior (112.6 s per epoch, scaled):
  T_run 9.1 d; 16 runs at K=4 on 4 pods (24 runs at K=6 with FP32-E, same pods) ≈ 4 × 218.9 h ≈ **876 pod-hours** (K=4 projection; K=6 s_e from the second-wave canary) (arbiter v7 fix 9c) (prior, superseded; pod-hours = pods × T_run from the regime-B canary). The full-split
  clone trace (every 10 epochs under regime B) adds to H's overhead.
- **Second-wave canary** (epochs 1-10, s_e window per Symbols, one pod, K=4: H-s1, H-s2, NB-s1, NB-s2, plus FP32-E-s1 and
  -s2 at K=6 when FP32-E is in the second wave, traced-EBOPs and β checks not applied to FP32-E [D26]; W&B group
  `chang-n64-20260926-wave2-canary`): the wave-1 stability checks (finite loss, epoch-10 train
  loss below epoch 1, traced EBOPs falling, read at slot T's traced epochs under regime B) plus **β moving from its initial 1e-7 by epoch 10 for
  H** (the PID has never run on `xfm`); s_e split into train step and overhead; peak GPU memory;
  and a certification retrace of each epoch-10 candidate (relative difference ≤ 1e-6). No
  separate feasibility pilot: interim readouts at 500, 1000, 2000, 4000 and 7000 are validation
  only, as in wave 1, and go to Kai. The [D15] 14-day rule applies to the second wave on its own
  canary.
- **Epoch-500 rules (second wave; amended 2026-09-27, arbiter v4 #6, #9).** At the end of epoch
  500, validation only: if no NB seed (respectively no H seed) has a feasible, non-degenerate
  checkpoint (Selection rule (a) to (c)), that arm goes to Kai with the options continue, H on the
  open-loop schedule (H only), or stop; nothing else is decided on that readout. The paired A − NB
  validation sd_diff is read out at the same epoch, descriptively (Falsifier, weight-type claim,
  'Resolution'); it sets no pair count and triggers no Kai packet: A − NB stays at 8 pairs with no
  extras (Kai, STUDY v10 ESCALATE, 2026-09-28, K3; was: it set the extra pairs, and above 1.19 pt
  the packet went to Kai, arbiter v5 fix 3).
- **Cheap version.** NB alone, 8 seeds (8 runs, 2 pods at K=4, ≈ 438 pod-hours at the same
  prior (prior, superseded; pod-hours = pods × T_run from the regime-B canary)). It keeps the thesis-bearing A − NB and drops H − NB and H − A.
- **FP32-E (2026-09-27, Kai request (second set)).** 8 runs, 7,000 epochs.
  - *Launch gate and wave.* FP32-E is in the **second wave** and inherits its gate ([A25] CPU gate
    passed, second-wave PREFLIGHT reviewed, wave-1 pilot A rule passed, cache sha256,
    `split_seed` and order generator identical to wave 1's). Exception, pre-registered: if [A25]
    passes before wave-1 production launches, FP32-E-s joins wave-1 pod s at **K=7** only if a
    K=7 re-canary of one wave-1 pod (epochs 1-10, its six wave-1 runs plus FP32-E-s) shows (i)
    7 × peak GPU memory per process within the production GPU's memory, (ii) a projected wave-1
    T_run = 7,000 × s_e at K=7 of at most 14 d ([D15]), and (iii) FP32-E-s passing the
    finite-loss and epoch-10 train-loss checks; no scaling of the K=6 s_e is accepted in place of
    (ii). Otherwise FP32-E stays in the second wave at K=6 (arbiter v6 fix 2). At most one extra
    arm joins a wave-1 pod unless a K=8 re-canary passes (i) to (iii) at K=8; if NB's gates also pass first, which arm takes slot 7 is the Kai row
    "NB in wave-1 seed blocks" (closed by Kai's K=5 packing, 2026-09-27; no slot 7 exists; reopening it is a Kai decision).
  - *Pods, second wave.* FP32-E-s joins the seed-pair pods at **K=6** (pod j: H, NB, FP32-E at
    seeds 2j − 1 and 2j; 4 pods, about 14 at peak overlap, as Kai confirmed), so NB − FP32-E
    shares a GPU at every seed, subject to the second-wave canary's memory reading (FP32-E-s1 and
    -s2 are added to that canary). If K=6 does not fit, FP32-E runs as 2 extra pods at K=4 (seeds
    1-4, 5-8): 6 second-wave pods, about 16 at peak overlap, above Kai's about 14; that case goes
    to Kai before launch. The second wave's K per pod is set by its canary's
    measured peak GPU memory. RUN.md extrapolates six E-sized processes to about 26,124 MiB,
    above an A10's 23,028 MiB. If the 24 runs do not fit 4 pods on the chosen class, the case goes
    to Kai before launch (ceiling about 27 pods at peak).
  - *Pods, wave 1 at K=7:* still 8 Chang-schedule pods plus 2 R pods; the second wave keeps 4
    pods at K=4 (closed by Kai's K=5 packing, 2026-09-27; no slot 7 exists; reopening it is a Kai decision).
  - *Cost (projections, not measurements).* Packed into existing pods, no extra pod-hours at the
    prior (pod-hours = pods × T_run; T_run 218.9 h at 112.6 s per epoch) (prior, superseded; pod-hours = pods × T_run from the regime-B canary), though a larger K may
    raise s_e. Standalone, 2 pods × 218.9 h ≈ 438 pod-hours (prior, superseded; pod-hours = pods × T_run from the regime-B canary). FP32-E's s_e is lower (no [D20]
    trace); a pack's wall time is set by its slowest process.
  - *Epoch-500 rule:* if no FP32-E seed passes (c) at epoch 500, the arm goes to Kai (continue or
    stop); validation only, nothing else decided. The readout also prints FP32-E's seed-mean
    validation accuracy (validation, n = 62,000, as of epoch 500, never quoted) beside A's
    (arbiter v6 fix 4).
  - *Cheap version:* 4 seeds × 2,000 epochs (8,000 run-epochs against 56,000), half-width 1.59 ·
    sd_diff against 0.836; declined by Kai 2026-09-27 (8 seeds, full 7,000 epochs).
- No C-synthesis on `mulder`.

**W&B.** Project `BNJetTag-ChangRecipe` (new; never `BNJetTagAug`), group
`chang-n64-20260926`, canary group `chang-n64-20260926-canary`. Second wave (amended
2026-09-27): group `chang-n64-20260926-wave2`, canary group `chang-n64-20260926-wave2-canary`;
config names unique per arm and seed (`h-…`, `nb-…`, `fp32e-…`; FP32-E in the wave-1 group if it
joins wave 1). Superseded by the amendment below: The runner's run id is
sha256(config name)[:12], so config names must be unique per arm and seed.
*Amended 2026-09-27 (patch 0026, bundle 77f1ca4e; `review/PREFLIGHT_critical_v2.md` flag 2):*
the run id is sha256(stage + NUL + config name)[:12], with stage = the Job env `BNJ_STAGE`
∈ {pilot, canary, production} (not a config key, so `config_sha256` is unchanged). The W&B
group follows `BNJ_STAGE`: pilot and canary log into the config's group with `-canary` appended
(`chang-n64-20260926-canary` for wave 1, `chang-n64-20260926-wave2-canary` for wave 2; patch 0026
`stage_group`), production into the config's group (arbiter v7 fix 5). A tracked run with no stage is refused (`RUN_STAGE`), so every
production manifest must set `BNJ_STAGE=production`; a production run resumed from a pilot
checkpoint opens a new production-stage W&B run. Config names stay unique per arm and seed
within a stage.

## Conventions compliance

| convention | row | will implement / not applicable because |
| --- | --- | --- |
| `docs/conventions/jet-tagging-metrics.md` | Data and splits | **Deviation, flagged.** Split 90/10, not 80/20, for fidelity to `jsc150/data.py` (`val_size=0.1`): validation n = 62,000 (house records use 124,000), ROC-test n = 260,000 unchanged. Every validation number is labelled with n = 62,000 |
| `jet-tagging-metrics.md` | Metrics | **Deviation, flagged.** The primary metric is held-out **top-1 accuracy**, because the replication target is an accuracy number. Macro-OvR AUC and the five per-class AUCs always sit beside it, and rejection at signal efficiency 0.5 is reported. Selection is on validation **accuracy** rather than validation macro AUC; the tie-break is validation macro AUC |
| `jet-tagging-metrics.md` | Seeds and intervals | Will implement: 8 seeds, mean ± sd (ddof=1). A, B and D are paired by seed with a 95 % t-interval (df 7) and the sign count; C and A07-350 are paired by seed; R is paired by seed index; F is paired with A if [A17] shows shared init at every seed, else Welch; A − A07-350 is Welch. Paired gaps use seeds feasible (non-degenerate) and not diverged in both arms, count stated, with the per-pair seed correlation and GPU class. Holm across the four secondary gaps C − A07-350, A − B, A − D, A − F (A − A07-350 descriptive, no p); among the claims only the recipe claim carries a p-value (Falsifier). Second wave: A − NB paired by seed if [A22] passes at 8 seeds, else Welch; H − NB Welch; own Holm family {A − NB, H − NB, A − FP32-E} (m under dropouts: Falsifier, arbiter v7 fix 3); H − A is their sum, interval only, no p; A − FP32-E paired if [A25] passes at 8 seeds, else Welch; NB − FP32-E paired, interval only, no p (2026-09-27, Kai request (second set)) |
| `docs/methodology/06-review.md` §6.8 | Baseline binding at VERIFY | No arm is bound to 79.4 % at VERIFY: it is an external single-model reference, and A − 79.4 is descriptive. Arm H has **no binding reference** either. MHA-64 77.9 % is a one-head model that collapsed into a Deep Set (H is two-head `xfm`); REPRO-CHANG 80.56 % is one seed, test-selected, unverified and never a comparand. H − 77.9 and H − 80.56 are descriptive distances; H enters VERIFY through H − NB and H − A, not through a Tier-1 check |
| `jet-tagging-metrics.md` | Labelling | Will implement: metric, split, n and status on every number. Interim readouts are labelled "validation, n = 62,000, as of epoch E" |
| `jet-tagging-metrics.md` | Validation checks 1-6 | Will implement at VERIFY. The `y` arrays of the ROC-test set are byte-equal across all 80 runs of both waves (H, NB and FP32-E included; for H this is the check that its ROC-test equals A's) and, as an alignment gate on labels and row order only, byte-equal to `r14/n64/*.npz` (the same held-out files and stable pT sort; the gate changes features, not labels). The per-class label counts are asserted unchanged by the gate on train, validation and ROC-test (it zeroes features, not jets). Per-class AUC under 0.7 is called out |
| `jet-tagging-metrics.md` | Check 3, baseline reproduces the record with the pull | Not applicable: no arm reproduces a recorded configuration. No gated 90/10 N=64 record exists, and R is new too. VERIFY states "no consistency-with-record check possible" instead of leaving the box blank |
| `jet-tagging-metrics.md` | No comparison across input sets or N | Will implement: no number here sits beside Round 14, N=8, or the ungated 5M N=64 confirmation runs. Sun et al.'s numbers are quoted as external, single-model, with "3 features, N=64, HGQ mixed precision" |
| `docs/conventions/quantization-and-cost.md` | Configurations | Will implement: binary weights, activation widths learned from an 8-bit init under the [D19] WRAP datalane quantizer (a deliberate change from the house SAT, fixed-softmax quantizer, dated 2026-09-27; no convention mandates SAT). The arms are not called "W1A8", because widths at 350k will sit far below 8. FP32-E [D26]: float weights, quantizers off except the fixed softmax tables (arbiter v6 fix 9) |
| `quantization-and-cost.md` | Cost accounting | Will implement: native HGQ2 EBOPs remeasured on the selected checkpoint, with zero and random inputs agreeing. Budget type is a soft PID penalty with hard feasibility on acceptance. Amended after [A7] trace (2026-09-27): under WRAP a reset trace sets `i` from its input, so the zero/random-input agreement is checked with the stored ranges frozen (no reset); the remeasurement proper is the [D20] certification retrace on the full training split. FP32-E: no EBOPs, reported as 'FP32, unconstrained' (arbiter v6 fix 9) |
| `quantization-and-cost.md` | Selection under a budget | **Deviation, flagged**, in the metric only: highest validation *accuracy* among checkpoints at or under the budget. "No feasible checkpoint" is stated and never replaced. Cost is reported at the selected checkpoint, never at the final epoch. FP32-E: no budget; selection over the 701 slot-T epochs meeting (c), the same grid as A (Kai, STUDY v10 ESCALATE, 2026-09-28, K2; was all epochs), the feasibility filter a labelled part of the package [D26] (arbiter v6 fix 9) |
| `quantization-and-cost.md` | Validation checks 1-4 | Will implement: the binary gate (two symmetric nonzero values per layer) on every binary arm; NB and H are exempt (learned-width weights, amended 2026-09-27) and carry instead the per-layer weight-width distribution and, for NB, the no-int8-grid test [A22]; FP32-E is exempt and asserts no quantizer variables except the two fixed, non-trainable softmax tables per block (`kif`, k0 0, i0 1, f0 20, SAT; asserted unchanged from init), and float kernels [D26] (2026-09-27, Kai request (second set)); `binary_gate` (`ablation.py:336-343` at 42abed4b, called at `:733`) is skipped for NB ([A22]) and FP32-E ([A25]) (arbiter v6 fixes 5, 6); stored equal to remeasured widths, reload within 1e-7 with TF32 off. The schedule is this campaign's own, labelled "Sun et al. schedule" (R: the record schedule) |
| `docs/conventions/fpga-synthesis.md` | all | Not applicable: no synthesis. EBOPs is the only cost quantity, and no LUT or DSP claim is made ([L7]) |
| `docs/conventions/figures.md` | all | Will implement at REPORT: `docs/style/bnjettag.mplstyle`, `tools/plot_check.py`, provenance captions with seeds and n. The figures are pre-registered in the Falsifier section (per-class ROC with a log mistag axis, seed band and named arms; the E (B, A) and A07 (A07-350, C) accuracy-versus-EBOPs ladders with EBOPs above the floor and paired-gap panels; attention state per arm; validation − held-out per run). Interim-readout figures are labelled validation |
| House rule | metric named with split and n | Yes (above) |
| House rule | seeds ≥ 3 | 8 per arm, H, NB and FP32-E included; the cheap version uses 4, justified as a feasibility and stability answer only; the second-wave cheap version (NB only) keeps 8 |
| House rule | binary is the thesis; ternary a baseline | Every wave-1 arm is binary. H and NB (second wave, amended 2026-09-27) are learned-width comparison baselines, not ternary and not thesis arms; A − NB is worded iso-EBOPs, never iso-cost ([L2]). FP32-E (2026-09-27, Kai request (second set)) is the full-precision reference; A − FP32-E is a labelled package, not iso-EBOPs [D26] |
| House rule | selection rule pre-registered | Yes, including the tie-break, infeasible handling and divergence handling |
| House rule | falsifier stated | Yes: budget, recipe, and optimizer-stability; the distance to 79.4 % is descriptive |
| House rule | no local training or synthesis | Yes: NRP Nautilus only; no `mulder` |
| House rule | W&B group named, never `BNJetTagAug` | `BNJetTag-ChangRecipe` / `chang-n64-20260926`; second wave `chang-n64-20260926-wave2` (FP32-E there unless it joins wave 1) |
| training-environment convention (`SYSTEM.md`) | pins copied from the current job YAML | H runs on the job-YAML pins (TensorFlow 2.21.0, keras 3.15.0, hgq2 0.1.9), not REPRO-CHANG's JAX / hgq2 0.1.10.dev venv [A23]; NB on the same pins |
| House rule | nothing from scratch compute quotable | The canary is ops telemetry, and interim readouts are validation-only and labelled |

## Decision labels

- [D1] Base architecture is A07, copied from `const0922-a07-n64-s1-fast50-fp32.json`: d32, 4
  heads, 1 block, FFN 32, learned PE, norm none. It is the architecture of the current
  full-length N=64 runs (`campaigns/2026-09-23-confirmation`). Amended after review v1: the
  earlier claim that its initial EBOPs (24.8M) is the lowest of the traced plain N=64 arms is
  dropped, because A07 is the only plain transformer that preflight has traced (the other two
  traced configs, E02 and E05, are Engram variants). Amended 2026-09-27 under [D21]: A07 is
  the architecture of C (5M) and of the descriptive arm A07-350; the primary is E.
- [D2] **The Chang LR schedule, exactly as `jsc150/run_train.py` lines 21-37 and 92-93
  implement it**, with e the zero-based epoch, η₀ = 3e-3, α = 1e-6 (absolute), and
  cycle_step = e mod 500:
  - lr(e) = α + ½ (η₀ − α)(1 + cos(π · min(cycle_step / 490, 1)));
  - no warmup and no peak decay (m_mul 1, t_mul 1);
  - checks: lr(0) = 3e-3, lr(490..499) = 1e-6, lr(500) = 3e-3.
  This is not `train.py`'s `cosine_restarts`, which has a warmup and a relative floor.
- [D3] "Chang optimizer verbatim" is `keras.optimizers.Adam()` defaults: β₁ 0.9, β₂ 0.999,
  ε 1e-7, no weight decay, no clipping (`run_train.py` line 97). "Ours" is β₁ 0.9, β₂ 0.98,
  weight decay 0.01, clipvalue 1.0 (screen config).
- [D4] Batch 2,790 and 7,000 epochs for A, B, C, D, F and A07-350 (`run_train.py` lines 67, 104). R keeps the
  record recipe: batch 256, LR 2e-5, warmup 1, linear decay over 999, 1,000 epochs
  (`quantization-and-cost.md` check 4; confirmation configs).
- [D5] β control is our `BetaPID` at the target, with the block verbatim from the screen
  config except `target_ebops`: p 1.0, i 0.05, d 0, warmup 1, init β 1e-7, bounds 1e-10 to
  1e-3, log true, damp 0. This is the paper's stated method (§3, "a PID controller over β").
  Chang's HEAD code uses an open-loop `PieceWiseSchedule` (2e-8 → 3e-7 → 3e-6), which
  post-dates the paper and would not land on a fixed target. Not used.
- [D6] Targets: 350,000 (A, D, F, R, A07-350), 250,000 (B), 5,000,000 (C). Feasible means
  (a) to (c) of the Selection rule (amended 2026-09-27, arbiter v3 #1; was ≤ target).
  Amended 2026-09-27 after arbiter v2 #9: B was A07 at 175,000, which is `STATIC_INFEASIBLE`
  even under [D19] (A07 0-bit floor 343,053 traced > 175,000), and no rung below 350k fits A07. B now
  runs the E architecture at 250,000 (E 0-bit floor 171,526 traced, headroom 78,474; amended
  after [A7] trace, 2026-09-27), paired with E by seed. Amended 2026-09-27 under [D21]: E is
  now arm A, so A − B is the target-only gap in the Holm set. Alternative for Kai: cut B first.
- [D7] **pT gate**, as in `jsc150/data.py` lines 22-26: `X *= X[..., :1] >= 2`. It is applied
  on raw `pt` in GeV, zeroes all three features of a gated constituent, and runs after the
  pT sort and top-64 truncation but before standardization. It applies to train, validation
  and ROC-test alike. Standardization statistics come from the train split only (ours), not
  from train plus validation (Chang). A minor deviation, kept to avoid validation leakage.
- [D8] Split 90/10 with one fixed `split_seed`: n_train 558,000, n_val 62,000.
- [D9] Seeds 1-8. `experiment.seed = s` sets the init; `order_seed` is derived from s and is
  the same across arms. The screen fixed `order_seed = 20260912` for all seeds, so its seeds
  varied the init only; here seeds vary both init and order.
- [D10] No `pt_weights` key, no class weights, no distillation, no Engram module, no
  `target_schedule`, no recovery freeze, `es_patience 0`, `stop_on_target false`. "Off" is
  as in the pt-weighting BASE arm (`campaigns/2026-09-25-pt-weighting`).
- [D11] Selection rule as pre-registered above, with the tie-break order accuracy → val AUC
  → −EBOPs → −epoch enforced by [A13]. Amended after review v1: the rule now also fixes how
  diverged and infeasible seeds enter the mean and the paired gaps, and adds the labelled
  AUC-selected sensitivity.
- [D12] Primary metric: held-out top-1 accuracy, n = 260,000. Macro-OvR AUC and per-class
  AUC always sit beside it.
- [D13] Interim readouts at 500, 1000, 2000, 4000 and 7000 are validation-only and never
  select a checkpoint or an arm. Amended after review v1: one pre-registered consequence. If
  arm A's epoch-500 validation accuracy sd exceeds 0.6 pt, the result goes to Kai before
  epoch 1,000 with the options continue as descriptive, add seeds, or stop. Amended
  2026-09-27: with fewer than 2 feasible A seeds the sd is undefined and that goes to Kai with
  the same options; feasible count and median EBOPs / target are reported at 500 and 1,000.
  Amended 2026-09-27 (arbiter v3 #1): the sd uses feasible, non-degenerate seeds, the seed-mean
  validation accuracy is reported beside it, and a mean failing (c) goes to Kai.
- [D14] Checkpoint cadence as in Budget.
- [D15] The canary and the epoch-500 feasibility pilot come first (Budget). Launch policy:
  14 days single-wave, otherwise report to Kai; never truncate silently. Amended 2026-09-27: the
  [D20] full-split trace may push s_e up to about 1.66 × (CPU ratio 0.66), ≈ 15.1 d at the
  112.6 s prior; the canary's measured T_run (trace included) decides, and T_run > 14 d goes to
  Kai with no pre-approved change (Budget, "Trace-cost risk"). Fired 2026-09-27 (canary 17.7 d);
  Kai chose regime B (trace every 10 epochs); the 14-day rule binds on the regime-B canary.
- [D16] Pods are seed blocks with K=6: A, B, C, D, F, A07-350 (fallback: 2 pods of K=3 per
  block). 8-10 pods in one wave (Kai, 2026-09-27). R is packed
  separately. No A100. Superseded 2026-09-27 by Kai's packing (K=5 on the A10 class, about
  13 wave-1 pods, about 27 at peak with wave 2 and Delta).
- [D17] W&B `BNJetTag-ChangRecipe` / `chang-n64-20260926`.
- [D18] Architecture E (arm A under [D21]; also B, D, R, and F with a learned PE) is "Chang-sized": d24, 2 heads (Chang's `xfm` h=2; the paper's text says one
  head), 1 block, FFN 32, no PE. Its key_dim is d_model/heads = 12, against Chang's 16
  (`model.py:195`). It keeps our norm-free ReLU block and our two-layer head
  (not Chang's tanh lookup table, fused batchnorm or 32/32/32 head); only fields our config
  schema supports change.
- [D19] (2026-09-27, after `review/STUDY_arbiter_v2.md` #1-#3; **Kai-confirmed 2026-09-27 08:40
  PDT**, `.claude/memory/decisions.md`) **Quantizer amendment.** Every arm (all seven, including
  C and A07-350) uses Chang's quantizers: kif `overflow_mode WRAP`, trainable,
  0 bits reachable, for every dense input and the Q, K, V streams; the softmax output into A·V
  learned the same way (HGQ2 `QuantizerConfig(place='datalane')`, `hgq/layers/attn/mha.py:69`);
  the softmax exp input a datalane quantizer; the exp and inv tables kbi `SAT_SYM`, trainable,
  `bc=Min(4)` (`jsc150/model.py:186-188`). Activation granularity stays per channel. Weights
  stay binary. The same quantizer in every arm, so the comparisons stay one-knob or labelled
  packages. It replaces the earlier choice (SAT with k = 1, fixed 10-bit softmax output, fixed
  10-bit exp input and 12-bit tables, `qat.py:279-302, 452-459, 496-499`), whose static floor
  is above every target but 5M ("Static floor of the current quantizer"). The earlier
  quantizer survives only as the pilot arm C′ and the Kai alternative in the FLAG block.
  Implemented under [A20]; flagged for Kai. Amended after [A7] trace (2026-09-27): the exp
  input stays SAT per tensor as in jsc150 (costs 16,384 EBOPs at the A07 floor); WRAP bounds
  are jsc150's (ic MinMax(0,12), fc MinMax(-24,24)), rounding RND_CONV; the softmax output width
  is per element (h, t, s). These are ml-engineer's defaults, confirmed here for fidelity.
- [D20] (amended after [A7] trace, 2026-09-27) **EBOPs trace sample.** Under WRAP the integer
  bits `i` of every activation quantizer are set by `trace_minmax(reset=True)`, so the trace
  sample defines both the model's ranges and the EBOPs used in the feasibility test. The
  screen runner traced 256 training jets every epoch; on a synthetic sample at init (A07 at
  seed 1, the v3 `chang0926-a-n64-s1` config; `code/evidence/wrap_trace_check.py`: exponential
  pT with mean 8 GeV, 10-63 constituents, gated and standardized, 8,192 rows, seed 0; CPU, not a
  result) retracing on 4,096 rows instead
  raised `i` in 6 of 14 WRAP quantizers, changed 2.0 % of logits on rows outside the 256 (0.6 %
  of top-1 predictions), and moved EBOPs from 13,613,261 (first 256 rows of that sample) to 14,307,533.
  Pre-registered:
  - **On each traced epoch** (every 10 epochs, regime B, [D15] branch executed 2026-09-27,
    Kai-decided; arbiter v9 fix 1), the candidate's ranges and EBOPs come from
    `trace_minmax(reset=True)` over
    the **full training split** (n = 558,000, the same rows in every run; a min/max trace
    does not depend on data order), before the candidate is saved; the feasibility test (EBOPs ≤ target) uses that
    EBOPs. The key replaces the inert `calib_n` (ml-engineer names it).
  - **Train only.** Chang's `trace_and_save` also traces the validation set, once after
    training; here validation stays out of the range fit so that validation accuracy carries
    the same wrap behaviour as ROC-test (fidelity row). A retrace on train plus validation is
    reported at VERIFY as a labelled sensitivity (EBOPs and ROC-test accuracy), never for
    selection or feasibility.
  - **Certification** of every evaluated checkpoint before ROC-test (Selection rule). Because
    the PID holds the selected checkpoint at the target, certification must use the same
    sample as the traced-epoch test (regime B); a larger certification sample would fail most selected
    checkpoints and become a second, post-hoc selection.
  - **PID signal** (regime B; arbiter v9 fix 1). Between traces, BetaPID reads
    [slot P, bundle 42abed4b] the in-training EBOPs of the last training step: hgq2 0.1.9
    `BetaPID.on_epoch_end` reads the stored `layer.ebops`, which no trace overwrites on an untraced
    epoch (`model_ebops`, `ablation.py:492-495`, read at `:783`; `plan.md`, (a)). On a traced epoch
    the trace runs before `pid.on_epoch_end` (`:788-789`, `:860`), so the PID reads the traced EBOPs,
    as in regime A. The PID input is therefore a 9:1 mixed series of in-training and traced values
    (`plan.md` DECISION R-B1), and between traces the controller holds the in-training EBOPs, not
    the traced value, at target. The every-epoch assertion cited as `ablation.py:698-703` (`:729` in
    the tree before patch 0027) is split: on a traced epoch the PID EBOPs equals the traced total
    within 1e-6 relative (`:861-866`), on an untraced epoch it equals the in-training total
    (`:867-871`). The controller stays our [D5] BetaPID; jsc150 uses a fixed β schedule, so only the
    number, not the controller, matches its `FreeEBOPs`; the in-training value is logged beside the traced EBOPs as
    `ebops_in_training` (amended 2026-09-27). The regime-A measurement of the ratio and the
    threshold on it (Kai, STUDY v10 ESCALATE, 2026-09-28) are in slot P (3) and the pilot rules
    ('Regime-B PID input rule').
  - **Deployment check** (diagnostic): per-quantizer WRAP overflow fraction on validation and
    ROC-test at the selected checkpoint ([L8]).
  - Amended 2026-09-27 (arbiter v3 #5): the trace runs once per traced epoch on the live model; the
    post-reload check compares stored `i`, `f`, `k` and EBOPs with the saved candidate and does
    not trace again. The reset trace on the live model (every 10 epochs, regime B) changes training dynamics
    relative to Chang's single trace after training (fidelity row "WRAP range update"). Staged
    in patches 0015, 0016 and 0023; the shipped tree is the PREFLIGHT gate [A21].
- [D21] (2026-09-27, after `review/STUDY_arbiter_v3.md` #2; **Kai-confirmed 2026-09-27 08:40 PDT**,
  `.claude/memory/decisions.md`) **The 350k ladder moves to E as a unit.** Arm A is E at 350k
  (d24, 2 heads, 1 block, FFN 32, no PE); B is E at 250k; D (our optimizer) and R (our recipe) are
  on E; F is E + learned PE (so A − F is the PE knob on the primary architecture; first arm to
  cut); C stays A07 at 5M; the former A07 arm A becomes the descriptive arm A07-350 (A07 at 350k,
  8 seeds, paired with C), labelled "our A07 at the paper's budget: attention data-independent by
  construction". Reason: at 350k a feasible A07 checkpoint cannot carry data-dependent attention
  (≥ 8,192 EBOPs needed, 6,947 available) and has at most 3 per-constituent input bits, so the
  budget, recipe and stability claims on A07 would be fixed before training. 56 runs, 7 arms; 40
  on E (a broader reading of Kai's "changed architecture for some of them", which Kai confirmed).
  Holm set: C − A07-350, A − B, A − D, A − F (amended 2026-09-27, arbiter v4 #25: A − A07-350, the package, reported descriptively, no p). The switch was decided on
  static headroom and is never revisited on pilot accuracy. Declined alternatives: A07 primary
  (its claims become feasibility probes of the floor); E1 (one head) as primary.

- [D22] (2026-09-27, Kai request, 08:40; Kai-added, second wave) **Arm NB.** Arm A (E at 350k,
  [D19], Chang recipe, PID, [D20], seeds 1-8) with every kernel A quantizes as `binary_absmean`
  switched to HGQ2 `kbi` learned-width weights, configured as jsc150 `xfm`'s weight quantizer
  (resolved values dumped from a built `xfm` on the pin, [A22]). Everything else A's. Paired by
  seed with A if the [A22] kernel-hash gate passes at 8 seeds. Expected 0-bit floor 171,526
  (E's), traced at PREFLIGHT.
- [D23] (2026-09-27, Kai request, 08:40; Kai-added, second wave) **Arm H.** Sun et al.'s jsc150
  `xfm` (`get_transformer`, 2 heads, d24, key_dim 16) ported to the job-YAML pins [A23], on our
  cache, split, gate, standardization, seeds and order, trained with Adam defaults, [D2], batch
  2,790, 7,000 epochs, our PID [D5] at 350k (flagged; the code's open-loop `PieceWiseSchedule` is
  the alternative), selected by the Selection rule with non-degeneracy on the [D20] trace of a
  per-epoch clone (every 10 epochs under regime B, arbiter v9 fix 1), one ROC-test evaluation per run. Not `xfmt` or the paper's Linformer:
  `QLinformerAttentionT` is absent from `hgq2==0.1.9`.
- [D24] (2026-09-27, Kai request, 08:40) **Second wave.** H and NB launch when each passes its
  CPU gates and the wave-1 pilot A rule has passed, with the same seeds, cache sha256,
  `split_seed`, order generator and schedule as A; 4 pods at K=4 (seed pairs); own Holm family
  {A − NB, H − NB}; H − A as the sum, no p. 16 runs, 72 in total. Amended 2026-09-27, Kai request
  (second set): FP32-E [D26] joins the second wave (24 runs, 80 in total; seed-pair pods at K=6),
  and A − FP32-E joins the family.
- [D25] (2026-09-27, designer, final pass before review v4) **`i_decay_speed` = 1e-3, as
  jsc150.** Every [D19] arm (A, B, C, D, F, R, A07-350; pilot E1; second-wave NB) sets
  `quant.i_decay_speed: 0.001` (H, the ported jsc150 model, keeps its own 1e-3), applied to exactly the quantizers `i_decay_speeds(model)`
  enumerates (`bnhgq2/ablation.py:548-554` at 42abed4b, those carrying `_i_decay_speed`), so the setting and
  the per-run `i_decay_speed.json` record cover the same set. Absent key keeps the HGQ2 default
  0.01 (no-keys path unchanged). C′ (current SAT quantizer, the declined branch of [D19]) does not
  get the key. Set by patch 0024 (staged, tree ac5a5c86; `chang0926-a-n64-s1.json:40`; `cpu_gate_d25.log` `I_DECAY_OK` 0.001 on every [D19] config), and
  PREFLIGHT re-asserts 0.001 on the listed arms on the shipped tree (amended 2026-09-27 after arbiter v4; arbiter v5 fix 5); C′ has no WRAP quantizer, so it carries no key and records an empty set (`cpu_gate_d25.log:116`) [A21]. Reason: Kai asked to keep the conditions the same as Chang's code; [D19] already
  adopts his quantizer set, NB [D22] copies jsc150's 1e-3 and H [D23] is jsc150 at 1e-3, so
  leaving 0.01 on A would add an unrecorded knob to A − NB and H − A. At 200 steps per epoch,
  0.01 lets `i` shrink up to 2 bits per epoch in training, 1e-3 up to 0.2. Expected no effect on
  the static floors (the floor trace is `trace_minmax(reset=True)`; the decay acts only on the
  in-training per-step tracking); checked, not assumed ([A7] retrace under the key). The config
  sha changes, so the 58-config CPU gate, the reload check and the [A17] pairing check are re-run
  before PREFLIGHT, and the gate asserts every recorded value equals 0.001 on every [D19] config.
  Alternative declined: keep 0.01 (the ml-engineer's staged default, a drift from the recipe, not
  a choice).
- [D26] (2026-09-27, Kai request (second set); `.claude/memory/decisions.md`) **Arm FP32-E.** E,
  seeds 1-8, recipe, data, schedule, 7,000 epochs and selection as A, with `quant.weight: "none"`
  (every weight, datalane, Q/K/V stream, softmax-output and softmax exp/inv-input quantizer off;
  softmax exp/inv tables fixed 21-bit) and the EBOPs controller off (β ≡ 0, no target, no PID, no
  [D20] trace). Non-degeneracy reduces to (c); certification to reload determinism. Amended
  2026-09-28 (Kai, STUDY v10 ESCALATE, K2): selection only on the 701 slot-T epochs, the same grid
  as A, with the controller and trace off (was: all 7,000 epochs). Check in
  place of `binary_gate`: no quantizer variables except the two fixed, non-trainable softmax
  tables per block (`kif`, k0 0, i0 1, f0 20, SAT; asserted unchanged from init), and float
  kernels, at the selected checkpoint (arbiter v6 fixes 5, 6). Paired with A
  if [A25] passes at 8 seeds. A − FP32-E in the second-wave Holm family, labelled "binary at 350k
  against unconstrained FP32" (package, not iso-EBOPs); NB − FP32-E interval only. Second wave,
  or wave 1 at K=7 under the rule in Budget. Scope: E at N=64 under this recipe only. Reason: Kai,
  "without it the campaign cannot back the thesis's 'close to full precision' axis".

Constraints for phase 2 (ml-engineer):
- [A1] The screen runner (`bnhgq2/ablation.py`, `learning_rate()` line 118) supports only
  warmup plus poly decay. Implement [D2] exactly, with a unit test at epochs 0, 489, 490,
  499, 500 and 6999.
- [A2] `optimizer_for()` always passes `clipvalue` and `weight_decay`. Add a path with no
  clip and no weight decay for [D3], and assert ε = 1e-7.
- [A3] The pT gate is not in our pipeline. Implement [D7].
  - **Confirm that our `pt` feature is raw GeV.** The suffix match `_pt` is exact, so it
    should not be `ptrel`; check the value range.
  - Confirm the raw 150-particle files are already pT-ordered: Chang slices `[:, :64]`
    without sorting, while we sort by stable argsort on −pT. Report the fraction of jets our
    sort permutes.
  - Gate, then standardize: a gated constituent becomes −shift/scale, not zero, and with
    `pool gap` and no mask it enters the average, as in Chang's code. Confirm our loader does
    the same, and whether any padding mask treats gated and padded constituents differently.
- [A4] Build a new data cache (gated, 90/10). The `/data/constituent-study-20260922/n64`
  cache is 80/20 and ungated, and cannot be reused.
- [A5] On resume, roll `model_best.keras`, `model_min_ebops.keras`,
  `model_unconstrained.keras` and the state's `best_feasible` back to the resume
  checkpoint. Replayed epochs are not bit-exact on GPU, so a ghost trajectory must not
  survive in the selected file.
- [A6] Save a boundary snapshot at every 500 epochs: best-feasible-as-of-E model plus state.
- [A7] (rewritten 2026-09-27.) In CPU preflight, trace every arm under [D19] (and C′ under
  the current quantizer) with HGQ2's own `_compute_ebops` path, and report two floors:
  - the **0-bit floor**: every learnable width at its minimum, with `bits = relu(i+f) + k` for
    SAT quantizers and `relu(i+f)` for WRAP quantizers, and the softmax tables at 4 bits;
  - the **1-bit-alive floor**: every learnable width at 1 bit;
  and, per arm, the channel budget its target leaves above the 0-bit floor. Expected (arbiter
  arithmetic): A07 326,656 / 989,344; E 163,328 / 611,000; C′ (current quantizer) 4,559,008.
  Amended after [A7] trace (2026-09-27), ml-engineer's CPU trace on a synthetic sample, not a
  result: A07 (and A07 without PE) 343,053 / 1,005,741; E 171,526 / 619,198; C′ 4,580,398;
  every residual a named term ("Static floor of the current quantizer"). PREFLIGHT.md records
  these with the code sha of the shipped tree. Amended 2026-09-27 under [D21] (arbiter v3 #3,
  #6, C5): the trace list is A, B, D, R (E), F (E + learned PE, expected equal to E), C and
  A07-350 (A07), C′, and **E1** (d24, 1 head, pilot-only): 0-bit, 1-bit-alive, and the narrow and
  full ≥ 1-bit-attention readings, with per-head additivity confirmed. Amended 2026-09-27
  (`code/evidence/static_floors_fix6_a07_e_e1.json`, CPU, synthetic sample, not a result): E1
  0-bit 85,763 / 1-bit-alive 533,435 / narrow 282,371 / full 392,963; headroom at 350k +264,237 /
  −183,435 / +67,629 / −42,963, at 250k +164,237 / −283,435 / −32,371 / −142,963. Only the
  softmax term splits per head (E1 × 2 = E, residual 0 including the LUT table term); the Q·K and
  A·V terms are 98,304 each in both E and E1. The arbiter's A07 605,197 / 801,805 and E 368,134 /
  478,726 equal the traced totals (sums of the trace's own terms, an identity); the weights-only
  reading equals the 0-bit floor. The E1 trace
  required before E1 enters the pilot is done; `cpu_gate_d21.log` re-traces the E1 zero floor
  (85,763). `static_floors_arms_s1.json` regenerated
  for the [D21] arm set is a PREFLIGHT gate; the CPU file `code/evidence/static_floors_arms_s1_d25.json`
  already holds the [D21] set (A, D, F, R on E at 350,000, B on E at 250,000; arbiter v5 fix 7). For C′ the "1-bit-alive" column equals the 0-bit floor,
  because a SAT channel already costs k = 1 bit; it is reported as "= 0-bit floor (SAT)".
  An arm whose 0-bit floor is at or above its target is `STATIC_INFEASIBLE` and stays in the
  table (the precedent is E07 N=64, 2026-09-22). The traced value and its difference from the
  expected value are recorded in PREFLIGHT.md before the canary.
- [A8] The canary as specified, before any production pod.
- [A9] Report `df` on the `kai-data` PVC in the canary.
- [A10] Job hygiene as in Budget: `podFailurePolicy`, a deliberate deadline, new-Job-name
  resume.
- [A11] A ROC-test evaluator that applies the gate and the train-split standardization
  exactly as in training, with `y` byte-equal across runs.
- [A12] **Failed-arm isolation.** The runner raises on a non-finite loss, and the pack runner
  exits 1 when one arm fails (log, 2026-09-20). With `backoffLimit 0`, one divergence would
  kill all six runs of a seed block. On resume the diverged arm would then replay from its
  last checkpoint, an unrecorded second attempt that contradicts the divergence rule. The pack
  runner must:
  - write `DIVERGED.json` (epoch, last finite metrics) for the failed arm;
  - keep the other arms running, and exit 0 for the pod if the only failures are recorded
    divergences;
  - on every resume, skip any arm that carries the marker.
- [A13] **Tie-break order.** In the screen bundle 7f9e9307, `ablation.py:421` sets `cost_first = bool(cfg.get('engram_study'))`,
  and the screen configs carry a non-empty `engram_study` block (`module: null`), so a
  field-for-field copy would order accuracy → −EBOPs → val AUC → −epoch. Make the runner use
  `cost_before_auc=False` for this campaign: prefer an explicit override, because
  `run_study.py:29`, `check_engram.py:147` and `run_engram.py` index `cfg['engram_study']`
  directly and would fail if the block were dropped. PREFLIGHT adds a unit test that
  asserts the order accuracy → val AUC → −EBOPs → −epoch on a constructed accuracy tie.
- [A14] **EBOPs accounting check.** Compute the EBOPs of a REPRO-CHANG xfm-n64 checkpoint
  with our `compute_ebops` and with HGQ2's own counter, and report the ratio. If our tool
  cannot trace their model, record why and state the accounting difference (1-bit weights,
  A·V product, positional-encoding add, full-training-split trace [D20] (was 256 jets) against
  in-training `FreeEBOPs`) as a quantified limitation in [L2].
- [A15] **Checkpoint cadence.** `save_checkpoint` (`ablation.py:192-213` in the screen bundle 7f9e9307) has no cadence test
  and is called every epoch (`:456`); the config key `experiment.checkpoint_every_epochs`
  exists but the runner never reads it. Wire that key so the full optimizer checkpoint is
  written every 25 epochs, test it with the [A5] resume rollback, and keep the per-epoch
  candidate save, reload, validation and feasibility test unchanged.
- [A16] **Screen history, gate before the canary.** The investigator's answer to "did any
  N=64 arm of the 2026-09-22 screen (target 350,000, 50 epochs) reach a feasible checkpoint,
  and what was each arm's minimum EBOPs and its epoch" (from `activation_widths.jsonl` /
  `ebops_budget.json` under `/data/constituent-study-20260922/fp32/`, or W&B group
  `constituent-20260922-fast50`, plus the EBOPs trajectories of the in-flight A07-N64 5M
  runs) is recorded in PREFLIGHT.md beside [A7]. The investigator's W&B-only answer is in
  `review/STUDY_investigation_350k.md`: no N=64 screen arm logged `budget_met` at any epoch,
  and the lowest logged EBOPs was 4,630,276 (A07-N64, zero-based epoch 46; W&B-logged, seed 1,
  50 epochs, not verified, not a result). The PVC side (`state.json`,
  `activation_widths.jsonl`) was not read; PREFLIGHT confirms it. It does not block PREFLIGHT from starting;
  it blocks the canary and the production launch. The screen ran the old quantizer, whose
  A07 floor (4,580,398 traced) its minimum sits 1.1 % above (amended after [A7] trace, 2026-09-27); it bears on C′ directly and on the [D19]
  arms only as a lower bound on how fast EBOPs falls.
- [A17] **A vs F pairing.** Amended 2026-09-27 under [D21]: F now carries the PE and A (E) has
  none, so the RNG flag `arch.pos_enc_none_consume_rng` (patch 0011) goes on every no-PE E
  config (A, B, D, R) and F builds normally. On the staged [D21] configs A, B, D and R are each
  paired with F at all 8 seeds (`code/evidence/a17_pairing_d21_8seeds.json`: only
  `pos_enc/pos_table` differs, 0 of 15 shared variables differ; CPU, not a result); the re-run
  under [D25] on the shipped tree is the **PREFLIGHT gate** before the canary (amended 2026-09-27
  after arbiter v4). Build A-s1 and F-s1
  through `matching_initialization` and compare `kernel_hashes`. If only `pos_table` differs, A − F is paired by seed (t, df 7,
  sign count); otherwise it is Welch. The result is recorded before the canary and fixes the
  test before any result exists. Amended after [A7] trace (2026-09-27): without patch 0011 the
  F kernels differ from A's at seed 1 (UNPAIRED); with 0011 (`arch.pos_enc_none_consume_rng`,
  F configs only) only `pos_table` differs at seeds 1 and 2 (`code/evidence/a17_pairing_*.json`).
  **Patch 0011 is adopted**: it changes only the RNG draw order of F, so F's shared kernels
  equal A's at seed s, which is what makes A − F a one-knob comparison. The check runs at all 8
  seeds in PREFLIGHT; A − F is paired only if every seed passes, otherwise Welch for all. F is
  traced at A's 0-bit floor (171,526, the PE costs no EBOPs; `cpu_gate_d21.log`, F-s1), re-run at
  PREFLIGHT [A7].
- [A18] **Stale inherited fields.** The generator rewrites or drops `validation_split 0.2`,
  `wandb_project BNJetTag-Engram-Experimental`, `order_seed 20260912` and the
  `constituent_study` block (50-epoch protocol text). PREFLIGHT diffs one generated config
  against the source config and lists every changed field.
- [A19] **AUC-selected sensitivity checkpoint.** `model_unconstrained.keras` is AUC-best but
  not filtered for feasibility, so keep a second copy: the feasible checkpoint with the
  highest validation macro AUC. It never replaces `model_best.keras`.
- [A20] **[D19] quantizer set** (added 2026-09-27). New config keys (for example
  `act_overflow wrap`, `softmax_quant chang`) that switch every dense-input and Q, K, V stream
  quantizer to kif `overflow_mode WRAP`, trainable; the softmax output into A·V to HGQ2's
  `QuantizerConfig(place='datalane')`; the softmax exp input to a datalane quantizer; and the exp
  and inv tables to kbi `SAT_SYM`, trainable, `bc=Min(4)`, as `jsc150/model.py:186-188`. The old
  path stays selectable (C′). Tests:
  - a WRAP channel at `relu(i+f) = 0` costs 0 EBOPs and outputs 0;
  - the binary-weight gate still passes (the amendment touches activations only).
  Under WRAP-trainable `i` tracks the data range (`get_minimal_i`) and only `f` feels the EBOPs
  gradient, so the 8-bit init is stated as an `f0` with `i` tracked, and PREFLIGHT records the
  resulting init EBOPs as the epoch-0 [D20] trace on the real gated training split, in-pod, per
  config (amended 2026-09-27). The CPU values quoted here are synthetic and differ by sample:
  A07 13,613,261 (`wrap_trace_check.py`, first 256 rows of an exponential-pT sample), 13,182,317 (`static_floor.py`,
  256 standard-normal rows) and 14,462,317 (`cpu_gate_d21.log`, A07-350-s8, 4,096-row gate
  sample); E 8,965,267 (`static_floor.py`) and 9,429,139 (`cpu_gate_d21.log`, A-s1). None is the
  PREFLIGHT value. If the quantizer set needs a change to the `hgq2==0.1.9` pin, stop and
  report: the pilot then runs the C′-only fallback (Budget) until Kai decides. Amended after
  [A7] trace (2026-09-27): ml-engineer built [A20] on the pin with no change (patch 0001; unit
  tests pass: a WRAP channel reaches 0 EBOPs and outputs 0); the synthetic init trace of A07
  under [A20] is 13,182,317 (`static_floor.py`, synthetic standard-normal sample, n = 256, seed
  0; CPU, not a result; it differs from [D20]'s 13,613,261 because under WRAP `i` depends on the
  sample). E's init under the same tool is 8,965,267. The trace sample is [D20].
- [A21] **[D20] PREFLIGHT gate** (added 2026-09-27, arbiter v3 #5; amended 2026-09-27 after
  arbiter v4). [D20] is implemented in patches 0015, 0016 and 0023 (`code/tree/bnhgq2/ablation.py:438-450`
  trace sample, `:696-701` opt-in, `:799-800` stored reload check, lines at 42abed4b; the configs carry `train_full` and
  `stored`); the gate re-runs the checks on the shipped tree under [D25]. Before the canary:
  the per-epoch trace runs once on the full training split (n = 558,000) under the [D20] key;
  the post-reload check compares stored `i`, `f`, `k` and EBOPs instead of a second trace;
  `i_decay_speed` [D25]: patch 0024 sets `quant.i_decay_speed: 0.001` (staged, tree ac5a5c86; `chang0926-a-n64-s1.json:40`; `cpu_gate_d25.log` `I_DECAY_OK` 0.001 on every [D19] config), and PREFLIGHT re-asserts 0.001 on the shipped tree on the listed arms (A, B, C,
  D, F, R, A07-350, E1, NB); C′ has no WRAP quantizer, so it carries no key and records an empty set (`cpu_gate_d25.log:116`), from the per-run record (amended 2026-09-27); the
  canary reports the trace's share of s_e; BetaPID reads the traced EBOPs, asserted every epoch
  (`ablation.py:861-866` at 42abed4b). Under regime B the PREFLIGHT addendum for the patch-0027 bundle
  re-asserts this gate with the trace on the traced epochs only (slot T) and the PID input and
  assertion of slot P ([D15] branch executed, arbiter v9 fix 1). The regenerated `static_floors_arms_s1.json` ([A7]) and p_maj for the non-degeneracy
  threshold (c) (Selection rule), computed from the gated `y_val`, are recorded in the same gate.
  p_maj + 5 · SE is computed by `campaigns/chang0926/nondegenerate_threshold.py --cache DIR`
  (staged at `code/tree/campaigns/chang0926/`, the same function the runner uses), run in-pod by
  cluster-ops at PREFLIGHT because the gated 90/10 cache exists only on the PVC (amended
  2026-09-27).

- [A22] **NB code** (2026-09-27). `quant.weight: "kbi_learnable"` is accepted
  by `bnhgq2/config.py:40`, but `qat.build_qat_model` has no branch for it and builds the static
  int8 (W8A8) grid silently (decisions.md, 2026-09-27, method atlas, now Delta). Required before NB's canary:
  - a real branch that builds HGQ2 `kbi` weight quantizers with trainable widths on exactly the
    kernels A binarizes, configured from a dump of a built jsc150 `xfm` weight quantizer on the
    pin (overflow mode, `b0`, `i0`, regularizers, granularity, `i_decay_speed`), recorded in
    PREFLIGHT;
  - the builder **raises** on any `quant.weight` value it has no branch for (no silent default);
  - unit tests: NB kernels carry trainable width variables; a built NB layer takes more than two
    values and is not on the int8 grid; a 0-bit weight costs 0 EBOPs;
  - regression: A's configs (no NB key) reproduce under the new tree byte for byte (init
    `kernel_hashes`, traced EBOPs, epoch-1 loss on the CPU gate sample), so the code sha change
    leaves wave-1 pairing intact;
  - pairing gate (as [A17]): build A-s and NB-s through `matching_initialization` at all 8 seeds
    and compare latent `kernel_hashes`; paired only if they are equal at every seed;
  - NB configs carry `arch.pos_enc_none_consume_rng: true` like every no-PE E config, since the
    pairing gate depends on it;
  - [A7] trace of NB's 0-bit and 1-bit-alive floors, and NB's init EBOPs beside them (kbi `b0` 4
    weights start above A's 1-bit init, so the PID's early phase differs);
  - `binary_gate` is skipped for NB's `kbi` weights and replaced by the no-int8-grid test and the
    per-layer width record (arbiter v6 fix 6).
- [A23] **H port** (2026-09-27). A wrapped training loop, not a callback swap:
  - pins: the job-YAML pins (TensorFlow 2.21.0, keras 3.15.0, hgq2 0.1.9); `KERAS_BACKEND
    tensorflow`; drop `jax.config.update('jax_default_matmul_precision', 'tensorfloat32')`, TF32
    off (confound 9); no JAX pods;
  - `model.py` imports `QLinformerAttentionT` at module top, which the pin lacks: import only
    what `get_transformer` and `get_model` need, and build `get_model('xfm', 7, 7, 1e-8, 64,
    True)` unchanged otherwise; the `beta0` / PID initial-β interaction is recorded;
  - `StopIf` is absent from the pin: drop it, after the [A7] trace shows H's 0-bit floor above
    1e4 (else report);
  - data: our gated 90/10 cache, train-only standardization, stable pT sort, float32, our ROC-test
    loader [A11]; confirm that jsc150's features `[5, 8, 11]` are our pt, etarel, phirel;
  - seeds: `experiment.seed = s` for init (replacing the hard-coded 42), batches from our
    `order_seed = f(s)` generator at batch 2,790 (replacing HGQ2 `Dataset(shuffle=True)`);
  - β: our BetaPID block [D5] at 350k (or an HGQ2 `BetaPID` shown equivalent on a unit test);
    the open-loop path kept selectable for the Kai alternative;
  - per epoch: a clone traced on the full training split under [D20], candidate save and reload
    of the traced clone, validation accuracy and macro-OvR AUC (tie-break) and test (c) computed
    on that reloaded clone, BetaPID fed the clone's traced EBOPs with the per-epoch assertion of
    `ablation.py:861-866` (42abed4b), the Selection rule with non-degeneracy, certification before ROC-test;
    under regime B the clone is traced on the traced epochs only, and the PID input between
    traces follows slot P ([D15] branch executed, arbiter v9 fix 1);
  - CPU unit tests (amended 2026-09-27, arbiter v4 #2): the logged validation accuracy equals a
    fresh-load prediction of the saved clone, and the PID's EBOPs equals the clone's trace;
  - resume every 25 epochs with the [A5] rollback, [A12] divergence isolation, W&B;
  - port-equivalence gate: load the REPRO-CHANG xfm-n64 checkpoint into the TF / 0.1.9 build and
    compare EBOPs (relative difference ≤ 1e-6) and top-1 agreement on a fixed sample; if it does
    not load across versions, record why and run the check on a fresh build instead;
  - [A7] trace of H's 0-bit and 1-bit-alive floors;
  - [A14] (EBOPs accounting against HGQ2's counter) runs on the same model.
- [A24] **Second-wave launch record** (2026-09-27). A second-wave PREFLIGHT
  section records the cache sha256, `split_seed` and order generator equal to wave 1's, the code
  sha, the NB and H floors, the pairing gate result, p_maj (the wave-1 value, unchanged), and the
  second-wave canary outcome. Pods declare two runner kinds under `bnjettag.io/arms-per-pod`
  (rule PACK).
- [A25] **FP32-E runner path** (2026-09-27, Kai request (second set)). Before FP32-E's canary,
  ml-engineer confirms, on `quant.weight: "none"` for the E configs:
  - the build: the fp32 skeleton of `build_qat_model` (`qat.py:396` onward) with the quantizer
    inventory of [D26], and which [D19] keys (`act_policy`, `act_granularity`, `act_bw_l1`,
    `beta0`, `softmax_quant`, `softmax_out_*`, `i_decay_speed`) that path reads, ignores or refuses;
    FP32-E configs carry only keys the path reads; the stripped keys are listed by name (at
    least `act_overflow`, `softmax_quant`, `i_decay_speed`, and any `act_calib` / `act_policy`
    value the fp32 path refuses or ignores), and PREFLIGHT prints the diff of FP32-E-s1 against
    A-s1 (arbiter v6 fix 8); `i_decay_speed.json` records an empty set;
  - `compute_ebops` (`ebops_calc.py:15`): what it returns on this model (0, a number from the
    dummy quantizers and fixed tables, or an error);
  - the PID: `ablation.py:163, 735` (42abed4b) and `ebops_target.py:88-95` read a finite positive
    `target_ebops`, so dropping the EBOPs block probably does not run. Reach by config, or by a
    minimal opt-in switch named as the deliverable: β ≡ 0, no EBOPs loss term, no PID step, the
    [D20] trace skipped, the `ablation.py:861-871` (42abed4b) assertions not tripped;
  - selection: rules (a) and (b) not evaluated, (c) kept; `model_best.keras` updates on (c) with
    the tie-break without −EBOPs; amended 2026-09-28 (Kai, STUDY v10 ESCALATE, K2): only a slot-T
    epoch (`is_traced_epoch`, `ablation.py:483-489`) is selectable, as in A, although the
    controller and the [D20] trace are off, so the FP32-E config needs the same selectable-epoch
    rule with no trace (mechanism, config key or opt-in switch, is ml-engineer's; a wave-2 code
    item, routed to ml-engineer; FP32-E is not launched, so its `config_sha256` change costs
    nothing); the tag is never `minimum_ebops_no_feasible_checkpoint`;
    `budget_met` semantics recorded for W&B and `train_meta.json`;
  - certification: the reload-determinism check of [D26]; `certify_ebops.py` must not pass on an
    EBOPs identity;
  - pairing gate: `kernel_hashes` of FP32-E-s against A-s through `matching_initialization` at
    all 8 seeds, variable paths matched across the float and binary layer classes, with
    `n_shared == 15` (the A kernel and bias set of `a17_pairing_d25_8seeds.json`) and
    `only_in_arm`, `only_in_f` empty at every seed, and `matching_initialization` shown to run on
    an FP32-E config (its `calibrate_activations` and `expected_binary_layers` steps); otherwise
    the gate reports UNPAIRED and A − FP32-E is Welch (arbiter v6 fix 7);
    `arch.pos_enc_none_consume_rng: true`;
  - regression: if code changes, A's configs reproduce byte for byte (as [A22]);
  - CPU gate: the 8 FP32-E configs build, run 2 epochs on the CPU gate sample with finite loss,
    reload within 1e-7 and print a per-config pass line; the gate's production count rises by 8;
  - the [D26] check runs on the pinned hgq2 0.1.9 against the built model's variable list and
    prints the table variables it allows (arbiter v6 fix 5);
  - `binary_gate` (`ablation.py:336-343` at 42abed4b, called at `:733`) is skipped for `quant.weight: "none"`
    and replaced by the [D26] check at the selected checkpoint (arbiter v6 fix 6).
- [A26] **Attention-entropy readout** (2026-09-27, arbiter v6 fix 10; arbiter v7 fix 1; ml-engineer). An offline
  script loads a saved `.keras` (`load_model(compile=False)`), builds a sub-model on each
  `{blk}_attn_softmax` output (`qat.py:574`; both the binary and fp32 branches), runs the
  validation split (n = 62,000), and reports per block and head the mean over jets and query rows
  of −Σ p log p over the 64 keys, divided by log 64, with p the `{blk}_attn_softmax` output as the
  model computes it (quantized tables) divided by its row sum (primary; the fixed-softmax build
  does not emit rows summing to 1, `.claude/memory/decisions.md` entry '2026-09-27 (ml-engineer,
  PREFLIGHT gate v1 fixer + [A26])'); the un-renormalized value −Σ q log q / log 64 and the row-sum
  min / mean / max are printed beside it. CPU unit tests, on the renormalized primary: uniform
  logits give 1 within 1e-6; one-hot logits give about 0
  (`code/evidence/pytest_shipped_77f1ca4e.log:65-73`). Due before the pilot's epoch-500 readout; run at VERIFY on every selected checkpoint. No change to
  the runner or to pilot pods. If the script and its tests are not ready by the pilot's epoch-500
  readout, that readout prints entropy as "pending, computed from the retained epoch-500
  snapshot" (Budget, pilot), and the entropy is filled in before wave-1 production.

Limitations:
- [L1] Sun et al.'s numbers are single models with no seed interval, and their selection
  rule and validation split are unstated. §3 reports the MHA collapse "over several trained
  models", so a row may be the best of several. The comparison is one-sample against a fixed
  number; their own seed noise is unknown. Its scale: our run of their released code moved
  their N=64 rows by +1.05 pt (xfmt-n64 80.85 % against Linformer 79.8 %) and +2.7 pt
  (xfm-n64 80.56 % against MHA 77.9 %), single seed, test-selected, unverified
  (`_attic/repro-chang/repro-chang/comparison.md`). The Deep Sets row was not rerun. Whether
  the pT gate applies to the paper's numbers is not stated (the gate is in the code, not the
  paper, `docs/chang-vs-bnjettag.md`). The reference's uncertainty is therefore at least the
  size of the 1.0-pt descriptive line, which is why A − 79.4 carries no pass or fail.
- [L2] Different model family. Ours is a binary-weight, norm-free ReLU transformer; theirs
  are HGQ per-parameter mixed precision with per-position ("value-wise") activation widths.
  Both EBOPs are native HGQ2, but EBOPs leave out the accumulator, which is the whole cost of
  a ±1 adder tree. Equal EBOPs is therefore not equal LUT. Equal EBOPs is not equal usable
  budget either: the softmax floor takes 49 % of E's 350k and 98 % of A07's, and the Deep Sets
  comparand pays none. The 2-head E architecture under [D19] (any weight type, including NB)
  reaches 350k only because the Q·K and A·V streams may prune to 0 bits, which
  the paper's protocol may not have allowed ("Paper's ≥ 1-bit attention rule"); `xfm` (key_dim 16) is expected to be at least as constrained, traced at [A7] (arbiter v5 fix 7); A − NB is
  unaffected (shared floor). The binary kernels are billed 1 bit through the `_binary_kq` pin
  (`qat.py:228-229`); the per-tensor absmean scale β (one scalar per kernel, `qat.py:56-65`) is
  applied outside that quantizer and is not in native EBOPs, so iso-EBOPs against NB does not
  count that scale on the binary side (amended 2026-09-27, physics v4 C7).
- [L3] Backend and numerics differ: TensorFlow with TF32 off here, JAX with TF32 on there.
  Standardization statistics also differ (train only versus train plus validation).
- [L4] The LR returns to 3e-3 at every restart (14 times). The canary covers only the first
  peak, so later divergence is possible and is recorded, not prevented.
- [L5] R's package differs in batch, LR shape and peak, and epochs at once. A−R and D−R say
  "recipe package", not which ingredient.
- [L6] No result here is comparable with Round 14, N=8, or the ungated 5M N=64
  confirmation runs.
- [L7] No synthesis. No LUT, DSP or latency statement follows from this campaign.
- [L8] Under [D19] activations use WRAP overflow: an out-of-range input at deployment wraps
  rather than saturates. `i` tracks the training data range, but the behaviour on unseen
  inputs is not checked here, since there is no synthesis or C-simulation in this campaign.
  Amended after [A7] trace (2026-09-27): the range is traced on the full training split [D20],
  and the per-quantizer overflow fraction on validation and ROC-test is reported, which
  measures the wrap rate on unseen jets in software; hardware behaviour is still unchecked.
- [L9] (2026-09-27) H is a port, not Sun et al.'s code verbatim: TensorFlow with
  TF32 off, hgq2 0.1.9, our data handling, our PID and our selection rule. H − NB is therefore
  "their model and loop on our infrastructure against ours", and H says nothing directly about
  their published numbers ([L1]).
- [L10] (2026-09-27) A − NB is binary against learned-width HGQ weights, not
  against FP32. NB may prune weights to 0 bits and spend the budget differently from A, so the
  gap mixes "fewer bits per weight" with "where the budget goes"; the weight-width distribution
  and attention state are reported beside it. The second wave may cross GPU types and runs on a
  later code sha than A.

## Where I am not sure

Kai decisions at the pilot and launch gate, in one table (details in the FLAG blocks below).
Kai answered four of them on 2026-09-27 08:40 PDT (`.claude/memory/decisions.md`):

| decision | default | options | status |
| --- | --- | --- | --- |
| [D19] quantizer | full Chang match in every arm, exp input SAT as jsc150 | keep ours and re-target above 4.58M (drops the 79.4 % comparison); add C′ (ours at 5M, 8 runs); exp input WRAP (A07 floor 326,669, headroom 23,331; not jsc150) | **Kai-confirmed 2026-09-27** (default); C′ stays a pilot readout |
| primary architecture [D21] | E primary; D and R on E; F = E + learned PE; A07-350 descriptive; C on A07 at 5M; **40 of 56 runs on the changed architecture** | A07 primary, as v2 (its budget, recipe and stability claims become feasibility probes of the floor); E1 one head (the paper's text; pilot readout, traced 2026-09-27: 0-bit floor 85,763); a Linformer arm (new code) | **Kai-confirmed 2026-09-27**; never switched on pilot accuracy |
| paper-rule variant (≥ 1-bit attention activations) | not run ([D19] follows the code) | run it: only E1 under the narrow reading is statically feasible at 350k (282,371 traced, headroom 67,629, amended 2026-09-27; the only traced architecture feasible at 350k under that reading) | **Kai-confirmed default 2026-09-27** (not run; Kai, second set, 2026-09-27, `decisions.md`) |
| pod count | 8-10 pods, one wave, ≈ 9 d at the A07 prior (prior, superseded; pod-hours = pods × T_run from the regime-B canary) | 2 pods ≈ 36 d (breaks 14 days); cheap version | **Kai answered 2026-09-27: 8-10 pods, one wave**; with the second wave overlapping, about 14 pods (Kai-confirmed 2026-09-27, second set) (superseded by 'wave-1 packing after the A10 out-of-memory' if production runs at K=3; arbiter v8 fix 2); **superseded 2026-09-27** (Kai, [D15] branch): about 13 wave-1 pods at K=5 on the A10 class, wave 2 about 4, about 27 at peak with Delta |
| wave-1 packing after the A10 out-of-memory (arbiter v8 fix 2) | K=3 seed blocks (A, B, D and C, F, A07-350), 16 pods and 2 R pods | K=6 on GPU classes that hold the measured K=6 peak; K=3 on classes that hold the measured K=3 peak | **Kai answered 2026-09-27**: K=5 on the A10 class, pod map at PREFLIGHT from the regime-B pilot's measured memory |
| [D15] branch after the canary (arbiter v9 fix 1) | regime B: [D20] trace every 10 epochs, certification unchanged, second pilot under regime B | accept about 18 d; K=3 with about 22 pods; terminal epoch 2,000 / 4,000; cheap version | **Kai-decided 2026-09-27** (decisions.md); the regime-B canary must pass the 14-day rule |
| regime-B PID input (arbiter v10 K1) | (b) pre-registered threshold, read at the pilot's epoch-500 readout | (a) report only; (c) PID on traced EBOPs only, β held between traces; (d) setpoint scaled by the measured r | **Kai answered 2026-09-28: (b)** (STUDY v10 ESCALATE, `decisions.md`); if it fires, Kai chooses (c) or (d) at epoch 500; (c) staged by ml-engineer, unapplied (Phase 2, 'Regime-B PID input rule') |
| arm B | E at 250,000 [D6] | cut B first | **Kai-confirmed default 2026-09-27** (E at 250,000; Kai, second set, 2026-09-27, `decisions.md`) |
| arm NB [D22] | A with kbi learned-width weights (jsc150 `xfm` weight quantizer) on A's binarized kernels; paired by seed with A if [A22] passes; second wave | – (Kai asked for it) | **Kai-added 2026-09-27; second wave** (launches when [A22] passes) |
| arm H [D23] | jsc150 `xfm` (2 heads, d24), ported to the job-YAML pins, our data and selection, 8 seeds, one ROC-test evaluation; second wave | `xfmt` / paper Linformer (needs `QLinformerAttentionT`, absent from the pin; new code and a pin question) | **Kai-added 2026-09-27; second wave** (launches when [A23] passes) |
| H β control | our PID [D5] at 350k (the paper's method; same controller as A and NB) | the code's open-loop `PieceWiseSchedule` in place of the PID, or as an extra descriptive arm H-OL (8 runs) | **Kai-confirmed default 2026-09-27** (PID at 350k; Kai, second set, 2026-09-27, `decisions.md`) |
| H trace protocol | [D20] trace on a per-epoch clone (his live dynamics kept; validation metrics, test (c) and the PID read the reloaded clone) | live-model reset trace, as A | **Kai-confirmed default 2026-09-27** (clone trace; Kai, second set, 2026-09-27, `decisions.md`); under regime B the clone trace runs every 10 epochs ([D15] branch executed, arbiter v9 fix 1) |
| second-wave pods | 4 pods, K=4, seed pairs (K=6 with FP32-E, [D26]); start after the wave-1 pilot | wait for wave 1 to finish (no overlap, ≈ 9 d later (prior, superseded; pod-hours = pods × T_run from the regime-B canary)); NB joins wave-1 pods at K=7 if its gates pass first; cheap version NB only (8 runs) | **Kai-confirmed 2026-09-27: overlap**, wave 2 runs beside wave 1 at about 14 pods at once (above the earlier 8-10), starting once its code passes the CPU gates (Kai, second set, 2026-09-27, `decisions.md`) |
| base architecture, "the way it's implemented", split, comparand, selection metric, arm F | as designed | see blocks | **Kai-confirmed default 2026-09-27** (base architecture, 90/10 split, 79.4 % comparand, validation-accuracy selection, arm F as designed; Kai, second set, 2026-09-27, `decisions.md`) |
| extra A/NB pairs (cap) | 8 pairs | n from the pre-registered sizing table (Falsifier, weight-type claim, "Resolution"), up to a cap Kai sets; each extra pair adds one A and one NB 7,000-epoch run (declined 2026-09-28; caps at 12 or 16 declined) | **Kai answered 2026-09-28 (STUDY v10 ESCALATE, K3): 8 pairs, no extra pairs**; the wide interval is reported as it is. At the cap of 8 pairs: 95 % half-width 0.836 · sd_diff (±1.0 pt needs sd_diff ≤ 1.19 pt; Seeds) and 80 %-power detectable gap 1.16 · sd_diff (about 5.2 pt at zero pair correlation and the archived spread; 'Not falsified'). Was: open, blocking the extra pairs only (arbiter v5 fix 3; arbiter v7 fix 9a; arbiter v8 fix 4). |
| FP32 E arm (FP32-E [D26]) | FP32-E, 8 seeds, 7,000 epochs, controller off, second wave (seed-pair pods at K=6); wave 1 at K=7 if [A25] passes before wave-1 production and the K=7 re-canary passes (Budget, FP32-E; arbiter v6 fix 2) | cheap: 4 seeds × 2,000 epochs (declined) | **Kai-added 2026-09-27, 8 seeds, full 7,000 epochs; designed 2026-09-27, Kai request (second set)**; selection grid: the 701 slot-T epochs as A (**Kai answered 2026-09-28**, STUDY v10 ESCALATE, K2) ([D26], [A25]; blocks FP32-E's canary on [A25]; Kai, second set, 2026-09-27, `decisions.md`) (closed by Kai's K=5 packing, 2026-09-27; no slot 7 exists; reopening it is a Kai decision) |
| PREFLIGHT, canary and pilot before STUDY PASS | wait for v6 PASS | start now under arbiter v5's conditions (arbiter file committed first, 27ffa29; fix 5 before PREFLIGHT checks [A21]; fix 4 before the pilot's epoch-500 readout; v6 PASS before wave-1 production) | **Kai answered 2026-09-27: start now under arbiter v5's conditions** (Kai, second set, 2026-09-27, `decisions.md`) |
| NB in wave-1 seed blocks | NB as a second wave (Kai, 08:40) | if NB's gates pass before wave-1 production and a K=7 re-canary as in FP32-E's launch rule (Budget, FP32-E) passes (i) to (iii) with NB-s in slot 7 (arbiter v6 fix 2), NB-s joins wave-1 pod s (same GPU, date and pod as A-s; no pod overage) | open; decided at the K=7 re-canary (Kai option). If NB and FP32-E both qualify and a K=8 re-canary does not pass (i) to (iii), Kai names which takes slot 7 (2026-09-27, Kai request (second set); arbiter v7 fix 9b) (closed by Kai's K=5 packing, 2026-09-27; no slot 7 exists; reopening it is a Kai decision) |

```
DECISION: [D19] (2026-09-27) every arm uses Chang's quantizers: WRAP datalane activations and
  Q, K, V streams (0 bits reachable), learned softmax output, softmax exp input datalane, exp
  and inv tables kbi SAT_SYM >= 4 bits. Reason: the current quantizer's static floor (A07
  4,580,398 traced) is above every target but 5M. Applying it to C and R redefines Kai's "the
  way it's implemented" from "our quantizer" to "our target (C) and our recipe (R)"
ALTERNATIVES: keep ours and re-target above 4.58M (drops the 79.4 % comparison); add C' (A07,
  Chang recipe, our SAT quantizer, 5M, 8 runs; 9.2 % above its traced floor); the pilot runs
  C'-s1 as a readout; exp input WRAP instead of jsc150's SAT (A07 0-bit floor 326,669, headroom
  23,331 at 350k; not Chang's code)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: ANSWERED (Kai confirmed the default, 2026-09-27)
```
```
DECISION: [D21] primary architecture = E (d24/h2/L1/FFN32, no PE, Chang-sized) for the whole
  350k ladder: A, B (250k), D, R and F (E + learned PE) on E; C on A07 at 5M; A07-350 as a
  descriptive arm. Reason: at 350k a feasible A07 checkpoint cannot carry data-dependent
  attention (>= 8,192 EBOPs needed, 6,947 available above the 343,053 floor) and has at most 3
  per-constituent input bits; E has 178,474 above its 171,526 floor, and the same minimal
  attention path costs 7,168 there. Context for E, not a comparand: our run of Chang's own
  xfm-n64 (d24, h=2, tables bc=Min(4), the same softmax structure as E) reached 80.56 % test
  accuracy at 348k EBOPs (`_attic/repro-chang/repro-chang/comparison.md`; single seed 42,
  selected on test accuracy (circular), unverified, open-loop beta schedule, HGQ weights). Its
  weights prune per weight to 0 bits, which binary weights cannot, so it shows a 2-head softmax
  floor leaves usable room at 350k, not that binary E will use it. 40 of 56 runs are on the
  changed architecture, a broader reading of Kai's "some with a changed architecture"
ALTERNATIVES: A07 primary, as v2 (the budget, recipe and stability claims become feasibility
  probes of the floor); a00 flagship (d32/h4/L2/FFN64; larger initial EBOPs, e.g. A02-N64
  traced 35,777,122 at epoch 1 in the screen, live-status.json); E1 one head (the paper's text;
  0-bit floor 85,763 traced, headroom 264,237 at 350k, amended 2026-09-27; a pilot readout); a Linformer arm (new code)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: ANSWERED (Kai confirmed, 2026-09-27)
```
```
DECISION: "the way it's implemented" covered twice: C (Chang recipe at our 5M target, on A07)
  and R (our full recipe at 350k, on E [D21]), both on the [D19] quantizer
ALTERNATIVES: C only (brief default; 48 runs), R only, or R at 5M (a second package control);
  C' (our quantizer at 5M), see [D19]
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: arm B = E architecture at 250,000 EBOPs (A07 has no feasible rung below 350k)
ALTERNATIVES: cut B first
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: split 90/10 (n_val 62,000) for fidelity; the cost is selection noise, binomial SE
  of one checkpoint's validation accuracy about 0.16 pt at p = 0.79
ALTERNATIVES: house 80/20 (n_val 124,000; SE about 0.12 pt, closer to existing caches)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: comparand fixed at 79.4 % Deep Sets (HGQ), with distances to Linformer 79.8 % and
  MHA 77.9 % beside it; A − 79.4 reported as a distance with its interval, and 78.4 % kept
  only as a labelled descriptive line
ALTERNATIVES: 0.5-point line (needs sd <= 0.3 point to resolve with 8 seeds); Linformer 79.8 %
  as the comparand (the paper's transformer)
CONFIDENCE: LOW   FLAG FOR HUMAN: YES
```
```
DECISION (superseded 2026-09-27 by [D22]-[D24] and the blocks below; Kai added H and NB): no
  non-binary arm in this campaign (v1 text; see git history for the full block)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: ANSWERED (Kai, 2026-09-27: add both, H and NB)
```
```
DECISION: [D23] arm H = jsc150 `xfm` (get_transformer, 2 heads, d24, key_dim 16), ported to the
  job-YAML pins (TensorFlow, hgq2 0.1.9), on our cache, split, gate, standardization, seeds and
  order; our PID [D5] at 350k; [D20] trace on a clone (every 10 epochs under regime B, arbiter
  v9 fix 1); Selection rule with
  non-degeneracy; one ROC-test evaluation per run; second wave (2026-09-27)
ALTERNATIVES: xfmt / the paper's Linformer (QLinformerAttentionT absent from the pin); the code's
  open-loop PieceWiseSchedule (verbatim code; REPRO-CHANG is the only evidence the model trains,
  single seed, test-selected; then H − NB also carries a controller difference); H-OL as an extra
  8-run descriptive arm; live-model reset trace as A (changes his dynamics)
CONFIDENCE: MEDIUM (model), LOW (beta control)   FLAG FOR HUMAN: YES (beta control and trace protocol)
```
```
DECISION: [D22] arm NB = arm A with A's binarized kernels on HGQ2 kbi learned-width weights,
  configured from a built jsc150 xfm weight quantizer; everything else A's; paired by seed if the
  [A22] kernel-hash gate passes at 8 seeds; second wave (2026-09-27)
ALTERNATIVES: NB weights with a 1-bit minimum (no pruning; isolates "more bits per weight" from
  "pruned weights", but is no longer jsc150's quantizer); NB biases also kbi (as jsc150; two knobs)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES (init width and pruning are Kai's reading of "learned-width")
```
```
DECISION: [D26] FP32-E: E in FP32 (quant.weight none; weight, datalane, stream, softmax-output
  and softmax-input quantizers off; exp/inv tables fixed 21-bit), controller off, (c) only,
  certification by reload determinism; check: no quantizer variables except the two fixed,
  non-trainable softmax tables per block (kif, k0 0, i0 1, f0 20, SAT; asserted unchanged from
  init), and float kernels; A − FP32-E in the second-wave Holm family as a labelled
  package, NB − FP32-E interval only; second wave at K=6, wave 1 at K=7 if [A25] passes first
  and a K=7 re-canary passes (2026-09-27, Kai request (second set); arbiter v6 fixes 2, 5);
  selection on the 701 slot-T epochs as A (2026-09-28, Kai, STUDY v10 ESCALATE, K2)
ALTERNATIVES: FP32-E under the PID at a nominal target (nothing to prune; (a)/(b) vacuous); FP32-E
  with [D19] activation quantizers and float weights (a weight-only float arm, not "full
  precision"); A − FP32-E outside Holm, interval only; 2 standalone pods at K=4; selection over
  all 7,000 epochs (declined 2026-09-28, K2)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO (arm Kai-added; slot-7 contention is the NB row)
```
```
DECISION: [D24] second wave: own Holm family {A − NB, H − NB}; H − A as their sum with an
  interval and no p; weight-type claim falsified only if the A − NB interval lies entirely below 0
  (Holm-adjusted); 1.0-pt line descriptive; 4 pods at K=4 after the wave-1 pilot; amended
  2026-09-27: family {A − NB, H − NB, A − FP32-E}; K=6 with FP32-E (arbiter v6 fix 11)
ALTERNATIVES: one Holm family over wave 1 and wave 2 (adjusted p of wave 1 would change after its
  VERIFY); a non-inferiority margin (not resolvable: about 3.7 pt paired at the archived spread);
  no overlap with wave 1; NB in wave-1 pods at K=7
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: ANSWERED (Kai, 2026-09-27, second set: overlap confirmed, about 14 pods)
```
```
DECISION: selection on validation accuracy, primary metric held-out accuracy (house default is AUC)
ALTERNATIVES: validation macro AUC selection with accuracy reported (house rule; the two rank
  models differently, constituent study 2026-09-16)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: launch policy: single-wave T_run <= 14 days, else stop and report; the prior
  expected 'fits 14 days' (A07-N64 batch-256 prior, 100.09 s per epoch, live-status.json; 9.1 d
  scaled to 558,000 train jets (prior, superseded; pod-hours = pods × T_run from the regime-B canary)); the canary measured
  17.7 d and the branch fired; Kai chose regime B (2026-09-27; arbiter v9 fix 1); amended
  2026-09-27: at risk from the [D20] full-split trace (CPU 0.66 × a training pass; up to about
  1.66 × s_e, ≈ 15.1 d at the prior), holds only if the overhead adds ≤ 53 % to the prior;
  T_run > 14 d on the canary goes to Kai, nothing pre-approved
ALTERNATIVES: 21 days; always launch 7,000 and read out at boundaries
CONFIDENCE: LOW   FLAG FOR HUMAN: ANSWERED (Kai, 2026-09-27, regime B)
```
```
DECISION: 10 pods in one wave (seed blocks: 8 Chang-schedule, 2 R) versus Kai's first "a
  couple of pods"; P = 2 at K = 6 is 4 waves, about 36 d at the A07 prior
ALTERNATIVES: P = 2 at K = 6, 4 waves (4 x T_run, breaks the 14-day rule); the cheap version (12 runs)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: ANSWERED (Kai, 2026-09-27: 8-10 pods, one wave, about 9 d
  (prior, superseded; pod-hours = pods × T_run from the regime-B canary); superseded 2026-09-27 by Kai's packing, K=5 on the A10 class,
  about 13 wave-1 pods, about 27 at peak with wave 2 and Delta; arbiter v9 fix 1)
```
```
DECISION: PID block verbatim from the screen (warmup 1)
ALTERNATIVES: warmup 10 as in the 2026-09-24 N=64 confirmation configs
CONFIDENCE: HIGH (small effect over 7,000 epochs)   FLAG FOR HUMAN: NO
```
```
DECISION: [D20] WRAP ranges and feasibility EBOPs are traced every 10 epochs (regime B; Kai,
  2026-09-27) on the full training split (n = 558,000), train only, on the live model; the post-reload check compares
  stored widths and EBOPs; every evaluated checkpoint is certified by a retrace on the same
  split before ROC-test; PREFLIGHT gate [A21]
ALTERNATIVES: a fixed training subset (e.g. 8,192 or 65,536 rows) per epoch (cheaper, but a
  subset under-covers the ranges, and any larger certification sample would fail checkpoints
  the PID holds at the target); Chang's train plus validation (validation then no longer
  mirrors ROC-test wrap behaviour); a range guard in the quantizer (code change, not jsc150)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: ANSWERED (Kai, 2026-09-27: regime B after the canary's
  T_run 17.7 d; decisions.md)
```
```
DECISION: arm F = E + learned PE [D21], so A − F is the positional-encoding knob on the
  primary architecture; brings the total to 56
ALTERNATIVES: drop F (48 runs; A − A07-350 stays a three-knob package). F is the first arm to
  cut and is not in the pilot
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```

- **Is 350k reachable at N=64 for this model?** A07 starts at 24.8M EBOPs under the current
  quantizer, 13,182,317 under [D19], and E at 8,965,267 under [D19] (synthetic init traces,
  [A20]). Weights are already 1 bit, so the only lever is activation width. Under the current
  quantizer 350k is not reachable at all (static floors 4,580,398 and 2,701,439 traced). Under
  [D19] E's softmax internals cost at least 171,526, which leaves 178,474 EBOPs above the 0-bit
  floor at 350k; A07's cost 343,053, which leaves 6,947, below the 8,192 that data-dependent
  attention needs, so A07-350's attention state is known before training (Falsifier). Whether A
  reaches 350k non-degenerately, and with what accuracy, is dynamic and is what the pilot and
  production measure. Q/K at 0 bits, or uniform attention at nonzero width, is the paper's
  Deep-Set collapse; the attention state is reported beside the budget claim in every outcome.
- **Screen history** is a PREFLIGHT gate item [A16], confirmed on the PVC before the canary;
  the investigator's W&B answer (`review/STUDY_investigation_350k.md`) is that no N=64 screen
  arm reached its target in 50 epochs, with the PID β still rising. Arbiter v2 corrects the
  reading: the A07 minimum (4,630,276) sits 1.1 % above the old quantizer's traced static floor
  (arbiter arithmetic gave 1.6 %), so the screen plateau is that floor, not a truncated descent. The N=64 confirmation target of 5M and its reason are both
  recorded, and the reason is post hoc: the budget was set from the screen endpoints near
  4.6-4.8M (`publication/docs/current-work/CONFIRMATION_RUNS_20260924.md:26`). The 5M target
  first appears on 2026-09-24; `project-context.md` and `decisions.md` date it from 2026-09-10,
  a conflict the investigator flagged and did not resolve. The 5M target sits 9.2 % (traced)
  above the old quantizer's floor, so the 5M N=64 confirmation runs measure a model near its
  minimum widths (`campaigns/2026-09-23-confirmation/UPSTREAM_FEEDBACK.md`).
- The canary is the only timing evidence at batch 2,790. Every wall-clock number above is a
  projection.
- **Second wave.** Four things are unsettled. First, whether
  the PID holds `xfm` at 350k at all (never run; REPRO-CHANG used the open-loop schedule). Second,
  whether the REPRO-CHANG checkpoint loads across hgq2 0.1.10.dev and 0.1.9 for the port gate.
  Third, whether NB's kbi latent kernels share A's init: extra quantizer variables could shift the
  RNG, and then A − NB falls to Welch at about 3.4 pt resolution. Fourth, whether A − NB can
  resolve anything smaller than a few points at 8 seeds: sd_diff is unmeasured, and a ±1.0-pt
  paired half-width needs sd_diff ≤ 1.19 pt. H's 0-bit floor, NB's floor and H's timing do not
  exist yet; PREFLIGHT traces the floors and the second-wave canary measures the timing.
