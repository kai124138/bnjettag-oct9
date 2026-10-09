---
id: 2026-09-27-delta-screen
date: 2026-09-27
type: delta-screen
status: frozen
question: Which W2 single levers raise the binary N=64 tagger's validation accuracy above a same-seed replica within one cosine cycle, and is any of them above the family's do-nothing placebo at family-wise alpha 0.10? Null - none does. Full specification in Question (the ranking and its "ranked" / "descriptive" label; the floor-family package and G2 feasibility check); significance mode in Appendix A.
supersedes:
superseded_by:
code_sha: not fixed. Code base = the anchor's regime-B bundle **carrying the host-memory leak fix and the run_pack heartbeat fix** (`decisions.md` 2026-09-28; anchor incident `review/INCIDENT_stall_20260928.md` §6), not yet frozen, plus the Delta patch series rebased onto it. f2107a04 and e90327d4 predate the fix and are not launchable (f2107a04 `bnhgq2/ablation.py:702` reloads a fresh model every epoch; STUDY arbiter v6) (amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta must not launch on the leaking anchor bundles'), on the regime-A pilot bundle 77f1ca4e today and rebased onto the regime-B bundle ([DK4], [DK13]); ml-engineer records the sha in PREFLIGHT.md. Design inputs - delta.json sha256 f4ad2571667af56ccbd28e4271e315aad36d378575d83b9864ace979b8029204; DELTA.md (2026-09-27, fixer v2); anchor STUDY.md at git 96b95f2 (every anchor STUDY line number refers to it); anchor RUN.md at e620173, except the regime-A canary trace / remainder split (90.61 / 127.45 s), from the "Canary — W&B history pull" in RUN.md at c9c9942
wandb: BNJetTag-Delta / delta-20260926-w2 (run prefix delta0926; BNJ_STAGE per run; never BNJetTagAug)
results:
---

# Delta wave 2: which single methods move the binary N=64 tagger against its own replica at the same seed, in one cosine cycle?

**Dated GPU amendment, 2026-09-28 (Kai).** The former "never A100" and fixed A10/3090 planning pool below are superseded for future launches by [the GPU selection policy](../../docs/infrastructure/gpu-selection-policy.md). Select products from measured run-epoch throughput, queue time, GPU utilization and safe pack size. A100 may be used if quota permits and it wins the same canary. Run E and A07 canaries on every chosen product; keep a cell, its same-seed replica and placebo on one product, preferably one product per family. Regenerate K and manifests per product. Existing A10 canary records are historical. The screen's statistical and launch gates remain in force.

Change log.
- v1 (2026-09-27): first design, experiment-designer. Wave 2 of the pre-registered Delta program
  (`campaigns/2026-09-26-delta/DELTA.md`, `delta.json`). One dated clarification of DELTA §5.1's
  selection wording ([D10]).
- v2 (2026-09-27, fixer after STUDY arbiter v1, ITERATE, 4 A / 19 B). v1 said "nothing loosened";
  that was false (arbiter #4). Every departure from DELTA is now listed here as a dated
  amendment, each with its reason, and each is also marked where it applies. Defaults for the
  arbiter's "what Kai must decide" items are the orchestrator's, labelled [DK1]-[DK12], "default,
  Kai may override at the launch gate" (Where I am not sure).
  - **Amendments against DELTA, dated 2026-09-27:**
    - §5.1 rule 1 (sd_plan source): the replicas' own epoch-500 sd over seeds 1-8 at the Delta sha
      replaces arm A's / arm C's anchor epoch-500 sd over seeds 1-8. Reason: no anchor-production
      seed exists and no [D19] arm C seed exists anywhere; the replicas give the same df (7) at the
      sha the cells run on ([DK2], [DK5]). v1's 2-seed pilot branch S is removed; the pilot sd is
      descriptive only. v1's sentence "as written in DELTA §5.1" was wrong and is deleted.
    - §5.2 ("never raises n"): the replica read can raise or lower n by the §5.1 rule, and a family
      whose sd_rep exceeds a pre-registered ceiling pauses and goes to Kai (Seeds). Reason: the
      read now carries the rule's own input. [The ceiling and the pause are withdrawn in v5.]
    - §5.1 control row and §5.2 drift trigger: the in-wave replica is always the primary control;
      anchor snapshots enter only as the descriptive transfer check g_rep ([DK3]). Reason: no
      anchor-production snapshot exists or is scheduled before this wave reads.
    - §7 wave 2a start condition ("the anchor's epoch-500 snapshots of seeds 1-n exist") and §6.3
      ("Delta waits for the anchor's epoch-500 pilot"), rewritten v3: wave 2 launches after the
      anchor's **regime-B pilot** epoch-500 validation readout (Kai, 2026-09-27, launch gate 1),
      not after anchor-production snapshots and not on a frozen anchor production config ([DK4]).
      Reason: production snapshots at the seeds this wave uses do not exist before production
      reaches epoch 500, and Kai named the regime-B pilot's readout as the start signal.
    - §7 2a/2b ordering: kept, in wave-2 form. The replicas, placebos, teachers and floor family
      (M001-M010) take the first pods; the 2b singles follow in the §7 order (Launch gate 10).
    - §5.3 ranking statistic and cap order: primary = mean g with a family-pooled paired sd
      interval; per-cell lower 80 % bound beside it ([DK6], **Kai-decided 2026-09-27**,
      `.claude/memory/decisions.md` top entry). Reason: `rank_sim.py` (mean-g rank matched or beat
      LCB80 in every row). A DELTA §5.3 amendment records it. [Primary re-decided in v6: median g.]
    - §5.3 ranking-mode family "no": a many-to-one max-t at one-sided α 0.10 plus an A/A placebo
      per family (addition; DELTA has no ranking-mode "no"). Reason: arbiter v1 #1. Its reference
      and sd changed in v3 (below).
    - §3.3 R2 FF2 re-base: FF2 is wave 3 and not run here; the rule is carried forward.
  - **Restored from DELTA verbatim (missing in v1):** G3′ non-inferiority (§5.3), the ⌈3n/4⌉
    arm-A-fails rule with its four consequences (§3.3 R2), R1 static-infeasible removal (§3.3),
    the 12-cell confirm cap (§5.3), K6 and the teacher jobs as K2 items (§7).
  - **Added:** placebo cells P-350 and P-5M; replica seeds 1-8 to epoch 500; sd_rep ceiling
    1.3 pt (withdrawn in v5); non-selecting companion readout and eligible-checkpoint count; missing-pair rule;
    separate floor-family package list (Welch); per-class AUC; the anchor's collapse label;
    always-on patches in the launch gate; anchor-config relabel rule; E packing from the canary.
    Budget regenerated by `budget.py` v2 (302 runs, 176,000 run-epochs at (4, 4)).
- v3 (2026-09-27, fixer v2 after STUDY arbiter v2, ITERATE, 6 A / 10 B). Dated amendments,
  2026-09-27, each marked where it applies:
  - **Regime B** (anchor STUDY 96b95f2 l. 1393-1463; `.claude/memory/decisions.md` "2026-09-27 (Kai,
    [D15] branch after the canary)"): every Delta run traces EBOPs every 10 epochs
    (`train.ebops_trace_every: 10`, anchor patch 0027), and only traced epochs are selectable
    ([DK13], default, Kai may override). Code base = the anchor's regime-B bundle; the Delta patch
    series sits on 77f1ca4e today and will be rebased onto it. Budget and timing from the
    regime-B arithmetic (136.5 s per E epoch at K = 6, anchor l. 1453-1457, a projection).
  - **Launch timing** (Kai, 2026-09-27, `decisions.md` top entry): the wave waits for the anchor's
    regime-B pilot epoch-500 validation readout (launch gate 1). This overrides [DK4]'s "does
    not wait" for that readout.
  - **Pods:** 10 Delta pods, about 27 GPU pods at peak with the anchor's two waves (Kai; anchor
    l. 1483). **Packing:** one rule for every class, the Delta memory canary (90 % of card
    memory); planning E K = 4, A07 K = 3 on 23-24 GB cards, E K = 5 the alternative row ([D16]).
  - **Generator findings** (`campaigns/2026-09-26-delta/code/GATES.md` §6, 2026-09-27): the
    cell-key rule admits the per-cell re-traced `experiment.nondegenerate.zero_floor_ebops` and the
    always-on keys (Arms, Cell configs); M047, M048, M049, P-T1 and P-T2 do not build under the
    anchor's [A20] guard, so they and the teacher-dependent cells wait for a launch gate (X5).
  - **Family test** (arbiter v2 fix 2): the max-t is referenced to the family's placebo
    (d_i = cell − placebo) and uses each cell's own paired sd, critical value simulated for the
    family's n; the v2 replica-referenced pooled rule is withdrawn. Reason: `screen_null.py` §4,
    its achieved false-"yes" rate under unequal spread, two-mode seeds and a common offset
    (Selection rule). [DK7] is updated.
  - **Placebo:** specified as the replica's config with the run-identity and provenance keys
    (`name`, `experiment.arm`, `delta_study.*`, `engram_study.question`) and `train.epochs`
    changed; PREFLIGHT asserts equal `digest_json(cfg)` after deleting those keys and setting
    `train.epochs` to one value, equal init `kernel_hashes` and equal first-step CPU loss (Arms). A
    determinism probe in the canary, both outcomes pre-registered, excluded from s_pool (arbiter
    v2 fix 3). The v3 test switch in the bit-identical outcome is withdrawn in v4.
  - **Replica- and placebo-side losses** lower the family's n uniformly (arbiter v2 fix 4).
  - **G3′** names its bound (two-sided 95 %, own sd, df n_p − 1; default, Kai may override) and
    prints its power (arbiter v2 fix 5); M023 goes to the `mulder` synthesis check whatever G3′
    reads ([DK15], default, Kai may override).
  - **Rank-move flag** threshold set from its simulated null count (arbiter v2 fix 7); **[L1]**
    check replaced (fix 8); sd_rep usable count (fix 9); accuracy-vs-AUC consequence (fix 10);
    pairing efficiency and an unpaired companion (fix 11); split-half as a second, non-selecting
    companion ([DK14], default).
- v4 (2026-09-27, fixer v3 after STUDY arbiter v3, ITERATE, 0 A / 10 B). Numbers regenerated by
  `screen_null.py` v3 (§14-§17 appended; §1-§13 reproduce digit for digit), `rank_sim.py` (an
  m = 37 block appended; earlier rows unchanged) and `budget.py` v4. Dated amendments, 2026-09-27,
  each marked where it applies:
  - **One family-test reference** (arbiter v3 fix 2): the family test is referenced to the
    placebo (d = cell − placebo) in every case. The v3 switch to a replica reference with a
    no-offset assumption when the stack is bit-identical is withdrawn, with its critical values
    (4.43 / 6.79) and its 0.261 / 0.258 offset row. The determinism probe and the placebo's own
    epoch-500 hashes now decide only how the placebo row is read. The probe runs per architecture
    class (E and A07), in two pods of one GPU product, for 21 epochs (launch gate 7). Placebo
    check (iv) states what happens when every per-seed placebo g is 0.
  - **Packable today** (fix 3): the four cells whose Z10 cache is not built (M009, M038, M040,
    M041) are also left out, as `code/GATES.md` §6 "Packs" does: 240 runs, not 268. Launch gates 3
    and 13 now say the same thing: a missing cache holds back only its own cells.
  - **Long-horizon cells out of the ranked list** (fix 4): M015 (350k and 5M), M031 and M032 form
    their own list "horizon H ≠ 500", outside the ranking order, s_pool and the family test, and
    are reported against the replica at their H; [L8] rewritten to match. The ranked list and the
    family test now hold the same cells: m = 11 at 350k and at most 37 at 5M (was 12 / 40). Every
    m-dependent design value was re-simulated at m = 11 / 37 (`screen_null.py` §13, §15;
    `rank_sim.py` m = 37 block).
  - **Rank-move r** (fix 5): computed on primary and companion values centred per cell, which is
    what `screen_null.py` §8 simulates. The T thresholds are unchanged; their null counts are
    restated at m = 11 / 37.
  - **Floor-family G2** (fix 7): null false-rescue rates printed (`screen_null.py` §17); a numeric
    trigger for "structural, by construction" (traced floor ≤ ½ of A07's 343,053).
  - **5M constraint active** (fix 8): a pre-registered readout on rep-C at the epoch-500 gate with
    a fixed rule; if slack, the 5M family is labelled "constraint slack at 5M" and the
    training-only levers are re-screened at 350k on arm A in a follow-up wave ([DK18], default).
  - **Pause is a likely branch** (fix 9): P(pause) printed (`screen_null.py` §14); the default on
    a pause is feasibility plus a descriptive ranking of the T0/T0a/T1 singles at n = 4 ([DK17],
    default); (4, 4) is the branch taken only if the ceiling passes. [Withdrawn in v5: the pause,
    [DK17], §14 and the ceiling; the 0.19-pt label below stays.] The 0.19-pt lower bracket is
    labelled "101 epochs, early stopping, archived Round-14 recipe".
  - **Ranking-mode n rule** (fix 10): n = 4 below sd_rep 1.0 pt; in 1.0-1.3 pt, seeds 5-8 for the
    top 16 H-500 cells at 5M and the top 6 at 350k ([DK16], default), the placebos stay at 4
    seeds and the family test at n = 4. [Band re-keyed to s_int in v5; "pause" above it
    withdrawn in v5.]
  - **Literature** (fix 6): `research/screen-design-literature.md` (physics-researcher, requested
    by the orchestrator 2026-09-27) is cited and its points are applied or answered in "Where I
    am not sure".
  - **C items applied:** replica loss no longer costs the family test a seed (crit C1); 51 traced
    epochs per cycle is the expectation (C2); pins c9c9942 and both bundle shas (C3, cons C7);
    [L1](a) epoch-500 readouts labelled uncertified (C4); placebos launch in both readings (C5);
    "95 % at equal spread" (C6); slot-second note (C7); `plan.md` v1 tagged superseded (C8); "a
    'no' is not evidence of absence" beside every family-test answer (phys C1); half-width row at
    ρ = −0.5 (phys C2); 0.023 attributed to the simulation (phys C3); forest plot shows d and g
    for a named cell (phys C4); variance-moderated max-t recorded in `plan.md` dead ends (cons
    C1); review-cycle references moved out of the body (cons C3).
- v5 (2026-09-27, fixer v4 after STUDY arbiter v4, ITERATE, 0 A / 8 B; a consolidation pass).
  Numbers regenerated by `screen_null.py` v4 (§18 appended; §10 and §14 withdrawn, §10's draws kept
  unprinted so every other number reproduces digit for digit; two §3 label lines reworded) and
  `budget.py` v5 (pause code and rows deleted; every other row unchanged). Dated amendments, 2026-09-27, each marked where it
  applies:
  - **Compute pause withdrawn** (arbiter v4 #1, #5, #7): the sd_rep ceiling, the pause, its budget
    rows, its four options, the no-family-test line and Falsifier (v) are deleted (old (vi) is now
    (v)); **[DK17] is withdrawn**; [D7], [D8] and [DK8] are amended. The full (4, 4) design runs
    whatever sd_rep reads. Reason: the pause saved at most 48 of 302 runs (`budget.py` v4: 254
    with both families paused), and sd_rep is the total seed sd, while the ranking is limited by
    the cell × seed interaction. sd_rep keeps one role, the significance-mode seed-rule input.
  - **Labels read s_int** at the n = 4 readout (#1): "ranked" if s_int ≤ T, else "descriptive";
    the family test is read in every family; the [DK16] band is 1.0 pt ≤ s_int ≤ T. [DK8] is now the
    label threshold T: 1.3 pt at 5M, 1.5 pt at 350k [T replaced in v6], from a fixed rule over
    Gaussian and per-run two-mode rows (#2, `screen_null.py` §18). The Gaussian ranking and extension rows are labelled
    optimistic under per-run two-mode seeds, with the two-mode rows beside them.
  - **Floor family** (#3): the question names the Welch package as the informative quantity; G2 is a
    feasibility check labelled "rescue expected from floor arithmetic" (was "structural, by
    construction"); M001 is printed as borderline.
  - **Ranked-list membership** (#4): M006 and M009 at 5M (and M046 if its [A17] check fails) move to
    the Welch list; the 5M ranked list holds at most 35 paired cells; design values stay at the
    design grid m = 37 and every read re-simulates at the actual m.
  - **Per-cell constraint label** (#5) for M003, M007, M008, M011, M012 on their own seeds, with a
    rationale for 0.8 and 0.9 and a tolerance on the β comparison (crit C1).
  - **Mode readout** (#6): two-mode test on the 8 replica values; n_low per cell, descriptive.
  - **C items:** pairing record "no information on ρ" (phys C1); check (iv) flag wording (phys C2);
    "contradicted" count ≤ 0.025 · (cells read) (phys C3, crit C3); packable-today m 9 / ≤ 32 and
    top-k fixed at 16 / 6 (phys C5, crit C2); n_p and n_d (crit C4); Kai decides the [L7] slack
    form at K3 (crit C5); frontmatter question shortened (cons C1); significance mode moved to
    Appendix A (cons C2); init-vs-order factorial named as the follow-up (cons C4).
  - **Consolidation, no rule changed beyond the above:** each rule is stated once and pointed to;
    the Arms table drops the config-delta and code columns (`delta.json` holds them); the [DK]
    labels are one-liners, with costs and alternatives only in "Where I am not sure".
- v6 (2026-09-28, fixer v5 after STUDY arbiter v5, ITERATE, 1 A / 6 B, and Kai's answers of
  2026-09-28, `.claude/memory/decisions.md` top entry). Numbers regenerated by `screen_null.py` v5
  (§1-§17 and the §18 draws reproduce digit for digit at the design seed; the T rule changed; §18b,
  §18c and §15a appended, printed last). Dated amendments, 2026-09-28, each marked where it applies:
  - **Confirm cap restored** (arbiter v5 #1, A): the DELTA §5.3 cap, dropped in the v5
    consolidation, is back in the Selection rule, in median-g order.
  - **[DK6] re-decided by Kai:** the primary ranking statistic is the **median of the n paired
    gaps** (median g); mean g is shown beside it, and mean g and n_low are the stability readouts.
    The family test and its calibration are unchanged (own-sd t of d = cell − placebo; it does not
    read the ranking statistic). Design values simulated with mean g are listed for re-simulation
    in "Where I am not sure" [re-simulated: "Median-g re-simulation" below].
  - **[DK8] T rule replaced** (#2, #3): condition (ii) is read only where P(s_int ≤ T | q) ≥ 0.01,
    and T is the minimum over ten RNG seeds. T = 1.2 pt at 5M, 1.8 pt at 350k (was 1.3 / 1.5) [350k
    T 2.1 pt by median g, next bullet].
  - **[DK16]** above-band two-mode rows disclosed and "extend above T at 350k" priced (#4).
  - **Disclosures:** the family test's detectable effect in pt (#6); why the seed-shared recovery
    is 1.00 (#7); the mode readout's operating characteristics (C row 20).
  - **C items** (arbiter v5 rows 8-21): resolution sentence, box q values, "at most 11", four scope
    half-lines, reflow, rare-high mode, s_int interval, confirm metric, EBOPs column, M001 label,
    Welch SE sentence, s_int under a lost replica seed.
  - **Median-g re-simulation** (experiment-designer, 2026-09-28; fixer v5's routed item, no rule
    changed): T, the [DK16] extension rows, the rank-move thresholds and the fidelity table
    re-scored by median g from the same draws (`screen_null.py` §19, `rank_sim.py` v6 block; earlier
    output byte-identical). T 1.2 pt (5M, unchanged), 2.1 pt (350k, was 1.8); rank-move T at 350k 4 /
    5 / 6 (was 3 / 5 / 6), at 5M 12 for r ≥ 0.95 (was 10) and none for 0.9 ≤ r < 0.95 (was 15).
  - **Freeze (Kai, 2026-09-28):** if STUDY review round 6 finds only new Category B items, the
    design is frozen and launched with them disclosed as known limitations; any Category A still
    blocks.
- v7 (2026-09-28): fixer after STUDY arbiter v6 (ITERATE, 1 A): the 2026-09-28 leak decision
  carried into `code_sha`, gates 4, 7, 11, new gate 14, PACK, Budget and the Reference table; B
  wording corrections B1-B6; 'Known limitations at freeze' added (Kai's freeze rule). Prints added,
  no draw, run count or earlier line changed: `screen_null.py` §19e (the design-seed T per floor,
  B2) and one `budget.py` PACK-MEM line (A5).
- Erratum (2026-09-28, before launch, orchestrator): gate 14 named `BNJ_RSS_GATE_MB_PER_EPOCH`, which no code reads (generator report, `campaigns/2026-09-26-delta/code/GATES.md` §7). The anchor's gate reads `BNJ_RSS_GATE_LIMIT_MB` (baseline + slope × train.epochs ≤ limit over epochs 5-105, exit 5). The 5 MB/epoch criterion is unchanged and is enforced per pack as limit = 2,100 + 5 × H MiB, the PACK-MEM line of `budget.py`. A name correction, not a rule change.

**In one line.** Which W2 single levers raise the binary N=64 tagger's validation accuracy
above a same-seed replica within one cosine cycle, and is any of them above the family's
do-nothing placebo at family-wise α 0.10? Null: none does.

**What this wave can and cannot say** (read this if nothing else).
- It can: rank at most 11 paired single-lever H-500 cells on A (350k) and at most 35 on C (5M) by
  median paired gap g at n = 4 (mean g beside it), each list labelled "ranked" or "descriptive"
  by the cell × seed interaction sd s_int it measures (Selection rule, "Label"); say at
  family-wise one-sided α 0.10 whether any cell is above the family's placebo; report Welch,
  long-horizon and baseline cells apart; count floor-family feasibility; say whether the 5M target binds (rep-C readout).
- It cannot: produce a quotable number (validation, one cycle, n = 4); call a gap flat (a
  declared deviation, Conventions); resolve g0 = 0.3 pt (Appendix A); predict the 7,000-epoch
  outcome.
- The only measured N=64 spread is 3.14 pt (archived, sizing only), and its seeds are two-mode.
  What n = 4 resolves then depends on whether the low mode is set by the seed, which pairing
  removes, or drawn per run, which it does not. Recovery of three true +1-pt cells in the 5M top
  12 is 1.00 in the first case, because in that model the cell × seed interaction is the
  within-mode sd, 0.3 pt, by construction. In the second, at q 0.1 / 0.33 / 0.5 (per-run sd 1.65 /
  2.56 / 2.72 pt), it is 0.28 / 0.19 / 0.14 by mean g and 0.85 / 0.26 / 0.26 by median g, the
  primary (`screen_null.py` §18, §18b). The median hides a lever that changes the low-mode
  probability; mean g and n_low read that. The design measures s_int, ρ̂ and n_low instead of
  assuming either case, and labels the list by s_int.
- The family test is calibrated and nearly powerless: at 50 % power it sees one cell about
  1.65-4.10 pt above the placebo at 350k and 2.50-6.25 pt at 5M, at σ 0.6-1.5 pt (§15a). A "no" is
  not evidence of absence.

**Question.** For each W2 cell run here (68 cells from 46 single entries, Arms), at its horizon H,
in best-feasible, non-degenerate **validation top-1 accuracy** (n = 62,000, gated 90/10 split,
traced epochs only), paired by seed with the same base config's drift replica (primary control,
[DK3]):
- **Ranking.** Where does the cell rank in its family by median paired gap g, and is the family's
  list "ranked" or "descriptive" at the interaction sd it measures? Does any ranked cell lie above
  the family's placebo at family-wise one-sided α 0.10 (many-to-one max-t on each cell's own
  paired sd, critical value simulated; it resolves only multi-pt effects, box)? The list is
  declared, "ranked, not advanced".
- **Significance mode** (not expected to arm): Appendix A.
- **Floor family (7 entries at 350k).** The informative quantity is each entry's
  cross-architecture accuracy against A, a Welch package (the A07-derived architecture plus the
  entry, against E), not a single-lever gap. G2 (k_e ≥ 3 and k_e − k_base ≥ 2 against A07-350) is
  a feasibility count; for every traced entry a rescue is expected from floor arithmetic (Selection
  rule, G2).

**Null.** Every cell's paired gap g is 0 (the entry does not move the base arm within H epochs),
and every floor-family entry has k_e − k_base ≤ 1. The wave's "no" and its rate under the null:
Falsifier.

**Bearing on the thesis.** The screen does not measure the cost of binary weights and produces no
quotable number. It picks which single levers (binarization, recipe, activation widths and EBOPs
control, architecture, inputs) are worth an 8-seed, 7,000-epoch confirm (Delta wave 4), where the
thesis-bearing comparisons against the anchor's non-binary arms are made (A − NB at iso-EBOPs,
A − FP32-E as a labelled package; anchor STUDY l. 396-408). The labelled non-binary baselines
M047-M050 are screen-level comparands only. **Tuning asymmetry:** 46 levers are screened for the
binary model and the baselines run once, untuned, at the binary recipe, so confirm either gives
the matched non-binary arm the same recipe-level winners (M028-M034 apply to any weight scheme)
or labels the gap "binary tuned, baseline not". Confirm restates the metric in macro AUC or
working-point efficiency before any thesis claim.

## Reference table

No number below is compared with a screen number; every reference is context or sizing.

| reference | value (metric, split, n, status) | source |
| --- | --- | --- |
| Round-14 record | **none**: archived, other split, recipe and architecture, no EBOPs target | `project-context.md`; anchor STUDY l. 438 |
| Anchor arm A (E at 350k), the 350k base | **no verified number.** The regime-A pilot `kai-chang0926-pilot-77f1ca` (one A10, K = 6) is descriptive only; it was stopped 2026-09-28T05:31Z for a host-memory leak of about 80-95 MB per epoch per arm (anchor `RUN.md` 'Stopped 2026-09-28T05:31Z'; incident §2) (amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta must not launch on the leaking anchor bundles'). The **regime-B pilot**, whose epoch-500 readout is launch gate 1, has not launched as of anchor 96b95f2; its epoch 500 is about 19 h after start (500 × 136.5 s; projection) | anchor `RUN.md` l. 60, 68-82 (e620173); anchor STUDY l. 1526-1545 |
| Anchor arm C (A07 at 5M) and A07-350 | **no run exists** under anchor [D19]: C-s1 and A07-350-s1 (OOM ×3 at K = 6) run in the anchor's K = 3 pilot pod, no epoch complete; anchor production has not launched | anchor STUDY l. 1393-1463, 1505-1539; anchor `RUN.md` l. 73, 98, 230-236 |
| E timing, regime B (projection) | ≈ 136.5 s per epoch per process at K = 6 = 127.45 + 90.61 / 10 from the regime-A canary split: "Neither is a measurement" | anchor STUDY l. 1453-1457; anchor `RUN.md` at c9c9942 |
| A07-class timing (indication only) | C′-s1 (old quantizer, not [D19]) 293.6 s per epoch, epochs 1-5, K = 6, A10, regime A | anchor `RUN.md` l. 162 (e620173) |
| Per-process GPU memory (E) | 4,354 MiB (A-s1, A-s2, D-s1, regime A); six ≈ 26,124 MiB > the A10's 23,028 MiB | anchor `RUN.md` l. 215-217, 244-252 (e620173) |
| Seed spread, sizing only | archived N=64 binary W1A8, held-out top-1 accuracy sd 3.14 pt (3 seeds, ROC-test n = 260,000, archived recipe; two-mode: 67.18 / 72.64 / 67.21 %); **never a comparand**. Lower bracket: N=8 W1A8, 8 seeds, held-out sd 0.19 pt, **101 epochs, early stopping, archived Round-14 recipe**, no EBOPs target | anchor STUDY l. 444, 447-458; `.claude/memory/experiment-log.md` "What has this project already tried" |
| Single-checkpoint measurement noise | binomial SE ≈ 0.16 pt at n_val = 62,000 near p = 0.79 (√(0.79 · 0.21 / 62,000) = 0.00164) | anchor STUDY l. 941-944 |
| Non-degeneracy threshold (c) | p_maj 0.20289 + 5 · SE 0.001615 = **0.21096** validation accuracy, from the gated y_val (class counts 12,479 / 11,882 / 12,499 / 12,579 / 12,561) | anchor `PREFLIGHT.md` l. 493, 525-527 |
| External context only | Sun et al. Deep Sets (HGQ) N=64, 79.4 % top-1, test n = 260,000, one model; never set beside a screen number | anchor STUDY l. 439 |

## Arms

**Base arms** (anchor STUDY l. 480-488, [D21] Kai-confirmed 2026-09-27):
- **A** = E at 350,000 EBOPs: d_model 24, 2 heads, 1 block, FFN 32, no PE, norm none, GAP, ReLU
  FFN, `binary_absmean`, anchor [D19] quantizers, Sun et al. recipe (Adam defaults, cosine restarts
  peak 3e-3 every 500 epochs, batch 2,790), pT ≥ 2 GeV gate, 90/10 split, BetaPID; traced 0-bit
  floor 171,526.
- **C** = A07 at 5,000,000: d_model 32, 4 heads, learned PE, otherwise as A; traced 0-bit floor
  343,053.
- **A07-350** = A07 at 350,000, descriptive: floor-family k_base and M010's seed partner (G2
  counts at two targets are not a contrast), never an accuracy base (traced headroom 6,947).
- **Placebo cells (A/A): P-350** = arm A's replica config at seeds 1-n_350, **P-5M** = arm C's at
  seeds 1-n_5M, both H 500: the replica's config at the same seed with only `name`,
  `experiment.arm`, `delta_study.*` and `engram_study.question` changed, none read by training
  (`bnhgq2/ablation.py:171-175, 375`; no no-op key exists in `delta.json`, and `BNJ_STAGE` is a
  closed set), plus `train.epochs` (launch gate 5)
  (`campaigns/2026-09-26-delta/code/generate_delta.py:588-603`). `name` enters `digest_json(cfg)`,
  `config_sha256`, the W&B run name and the Keras model name, not the seed or data order
  (`ablation.py:35, 597, 623, 658-659`). *PREFLIGHT assertion* (X2/Z13): at every seed, equal
  `digest_json(cfg)` after deleting those keys and setting `train.epochs` to one value, equal init
  `kernel_hashes`, equal first-step CPU loss. A placebo is packed like a cell (never in its
  replica's pod; the same GPU-product rule, [D17]), selected and certified like one, and is not
  in BH m, the family test's m cells,
  s_pool or s_int; it is the test's reference and a row in the forest plot, and it launches
  whatever the determinism probe finds.

**Cell configs.** The base arm's config at seed s plus the entry's `config_delta` (and
`extra_delta`), plus the always-on diagnostics the replicas also carry, with `epochs` = H.
PREFLIGHT prints each cell's key diff against its replica; a key outside these classes fails:
(1) the delta; (2) `epochs`; (3) run identity and provenance; (4) the re-traced
`experiment.nondegenerate.zero_floor_ebops` (38 (entry, arm) pairs differ from their arm's value;
`code/GATES.md` §6 "Zero floor"); (5) `experiment.collapse_stop` and
`experiment.accumulator_metric` (visible only against anchor configs). Amendment dated 2026-09-27
(generator engineer); `diff_outside_declared` must be empty.

**Identical across every run** (not in any "varies" column): N = 64 (except M009), input set
pt/etarel/phirel with the 2 GeV gate (except M038, M040), the anchor's gated 90/10 cache and
split_seed 1, `experiment.seed = s` and `order_seed = f(s)` at seed s, the Sun et al. schedule for
H epochs (except M028-M032), Adam defaults (except M020, M033), BetaPID with the anchor gains
(except M013) at the family target, anchor [D19] quantizers with `i_decay_speed` 1e-3 (anchor
[D25]), the [D20] full-training-split EBOPs trace under **regime B** (`train.ebops_trace_every:
10`, anchor patch 0027; BetaPID reads the in-training EBOPs between traces and the traced value on
traced epochs; [DK13]), `norm none`, TF32 off, `jit_compile false`, the selection rule and the
diagnostics set.

**Cells.** Rendered from `delta.json` (sha above), which holds each entry's name, `config_delta`,
`extra_delta`, `code_changes` and `anchor_patches_required`; roles are `screen_role_350k` and
`base` (DELTA §3.3 R2). Seeds 1-n_350 for every 350k and 1.4M cell, 1-n_5M for every 5M cell.
"FF" = floor family: own A07-derived architecture, G2 against A07-350, accuracy against A (Welch
package).

| entries | 350k cell | 5M cell (on C) | H | pairing |
| --- | --- | --- | ---: | --- |
| M001, M002, M004, M005 | FF | yes | 500 | paired-if-hash |
| M003 | FF | yes | 500 | paired |
| M006 (Deep Sets body), M009 (N = 32, crosses N) | FF | yes | 500 | Welch |
| M008, M011, M012, M038, M039 | on A | yes | 500 | paired |
| M016, M040, M042, M043, M045 | on A | yes | 500 | paired-if-hash |
| M013 | on A | – | 500 | paired |
| M015 | on A | yes | 1,000 | paired |
| M007, M017-M026, M028-M030, M033, M034, M037, M041 | – | yes | 500 | paired |
| M044 | – | yes | 500 | paired-if-hash |
| M046 (at 350k the PE contrast is anchor A vs F) | – | yes | 500 | paired if [A17], else Welch |
| M031, M032 | – | yes | 1,500, 2,000 | paired |
| M027 / M035, M036 | – | deferred (X1) | 500 | Welch / paired |
| M010 | – | 1.4M on A07 (ladder, no G3) | 500 | paired |
| M047, M048 / M049 (baselines) | probe, no G3 | comparand | 500 | paired / paired-if-hash |
| M050 (baseline) | G3 report, no advance | comparand | 500 | paired |

**Drift replicas** (DELTA §5.2): the base arm's config at the Delta sha, on Delta pods, one run per
seed, to the longest horizon that pairs with it ([A6] snapshots give shorter ones). Seeds above n
stop at 500 and are the extension's partners ([DK2], [DK16]).

| replica | config | target | horizon | seeds | serves |
| --- | --- | --- | ---: | --- | --- |
| rep-A | arm A (E) | 350,000 | 1,000 (seeds above n_350: 500) | 1-8 | 350k cells, probes, P-350; M015 at 350k |
| rep-A07-350 | A07-350 | 350,000 | 500 | 1-n_350 | floor-family k_base; M010's seed partner |
| rep-C | arm C (A07) | 5,000,000 | 2,000 (seeds above n_5M: 500) | 1-8 | every 5M cell, P-5M; M015 (1,000), M031 (1,500), M032 (2,000) |

**Counts.** 68 cells: 23 at 350k (12 accuracy cells on A, of which 11 at H 500 form the ranked
list and M015 the long-horizon list; M050 with a G3 report and no advance; 3 feasibility probes;
7 floor-family cells), 1 at 1.4M (M010), 44 at 5M on C (40 with a G3 test: at most 35 paired
H-500 cells in the ranked list, M006 and M009 in the Welch list, M015, M031, M032 in the
long-horizon list; 4 baselines); plus P-350 and P-5M. Runs at n = 4: Budget.

**Prerequisite jobs** (DELTA §3.4; never paired; selected on validation accuracy): **P-T1** FP
teacher (A07-N64, `quant.weight none`, anchor [D19] activation and softmax quantizers, no EBOPs
pressure, 2,000 epochs, seed 101; Z15 first) and **P-T2** (as P-T1 with `int8_absmax`, for W3
M063). They gate only M027, M035, M036 and W3's M061-M064 ([DK9]).

## Excluded from this wave, each with its reason

- **X1, teacher-dependent: M027, M035, M036** (5M) join by a dated, reviewed amendment once P-T1
  has a selected checkpoint and Z15 has passed (BH: Appendix A), noting a mild leakage: teachers and
  students are selected on the same 62,000 validation jets.
- **X2, code not gated on the anchor tree.** A cell runs only if every slug in its `code_changes`
  and every anchor patch it requires is gated on the **anchor tree** in
  `campaigns/2026-09-26-delta/code/README.md` at PREFLIGHT, and Z13 (every Delta patch off
  reproduces the anchor's regime-B configs byte for byte: `digest_json(cfg)`, init
  `kernel_hashes`) and the placebo assertion pass there. PREFLIGHT lists every excluded cell with
  its slug and README line (indication only: on 2026-09-27, 12 slugs are blocked on anchor [A1],
  [A3], [A4] or [A20]). **Always-on patches** (`diag-attention`,
  `screen-collapse-stop`, `accumulator-ebops-metric`, the `diag-*` readout patches; `code/README.md`
  l. 42-48, gated on the tarball only) must be gated on the anchor tree at the same gate; if one
  fails, the whole wave waits (launch gate 9).
- **X3, M049 at 350k** is dropped if the anchor's arm NB has an epoch-500 snapshot at launch (DELTA
  §2 l. 221-229); NB has not launched. M049 at 5M is not covered and runs (subject to X5).
- **X4, no Z01 trace.** Rule (b) needs the cell's own traced 0-bit floor. Z01 (`static_floor.py`)
  runs on every generated cell config; a delta can move the floor without changing the layer list
  (M007: 474,125 on A07). Entries without a traced floor today: M001-M007, M009, M016, M040,
  M042-M045, M047-M050. A cell whose trace is missing at launch is excluded like X2. **R1
  (restored from DELTA §3.3):** a 350k cell runs only if its 0-bit floor (traced, else derived) is
  below 350,000; floor-reduction entries (M001-M006, M009) are then dropped and the others keep
  their 5M cell (already applied: M007 and M044 run at 5M only). Any cell whose traced floor is ≥
  its own target is removed.
- **X5, non-binary weights do not build on the anchor tree** (`code/GATES.md` §6 "CPU gate"): the
  anchor's [A20] guard (`qat.py:667-669`) refuses M047, M048, M049 and both teachers, hence M027,
  M035, M036 and W3's KD cells. They wait for launch gate 13; this STUDY does not design that path.
  M050 builds and runs.
- **K6 (DELTA §7): the baselines M047-M050 run** ([DK9]), subject to X5; they are comparands,
  never in a ranked list.
- **Not in W2 by construction:** M014 (confirm-only); every package and factorial cell (wave 3).

## Prerequisites and launch gate

Nothing launches before all of these hold (DELTA §7 K1/K2), except that a missing Z10 cache or Z01
trace (gate 3) and the non-binary path (gate 13) hold back only their own cells:
1. **The anchor's regime-B pilot epoch-500 validation readout exists** (Kai, 2026-09-27,
   `decisions.md` top entry), and on it the **anchor pilot A rule** (anchor STUDY l. 1547-1551)
   passed or Kai named the anchor. If neither A pilot seed is feasible and non-degenerate by epoch
   500, DELTA §3.3 R2 applies (Controls, "Arm A fails at 350k"); under fallback C every 350k
   accuracy cell and probe is dropped. Launch does not wait for anchor-production snapshots or a
   frozen production config (amendment against DELTA §7 wave 2a, [DK4]).
2. **K2 answers recorded:** the [DK] defaults, which Kai may override here, and the canonical tree
   for the patch series (DELTA §7 K2).
3. **Wave-1 zero-GPU items** (DELTA §3.1): Z01 traces (X4); Z10 caches (gated N=32 for M009,
   ungated for M038, derived features for M040, real-slot standardization for M041), each with
   split_seed 1 and `y_val` byte-equal to the anchor's (sha256 63049d9b…7709, anchor
   `PREFLIGHT.md` l. 492); Z11 unit tests (M015 freeze, M030-M032 schedules, the EDE period, the
   collapse stop); Z13; Z15 before the teachers. **A missing cache or trace holds back only the
   cells that need it** (the four caches are not built as of 2026-09-27); those cells are listed in
   PREFLIGHT.md and the rest of the wave does not wait. This is the one statement of that rule.
4. **`run_pack.py` open item** (`code/README.md`): it expects index rows, not names, and it and
   `run_study.py` hard-code the output root `/data/constituent-study-20260922/fp32`. PREFLIGHT
   resolves it; the design does not change. Patch 0038 is rebased onto the anchor's `run_pack.py`
   fix (heartbeat age from the attempt start; no relaunch into a full cgroup; incident §4, §6) and
   `tests/test_run_pack_delta.py` passes on the rebased tree (`decisions.md` 2026-09-28)
   (amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta must not launch on the leaking anchor
   bundles').
5. **Horizon truncation** ([D18]): at `epochs` = H, 1,000, 2,000 and 7,000 the base config gives
   the same per-epoch LR, PID inputs and traced-epoch set for epochs 1..H (CPU, a few steps at each
   restart boundary and at H). M031 and M032 differ by design.
6. **Bop measurement** ([D15]): the |m| distribution of C's binary latents (A's for reference) over
   a few hundred steps at γ = 1e-4, with the flip fraction at τ = 1e-8. Descriptive.
7. **Memory and timing canary per architecture and GPU class** ([D16], [DK11]; GPU memory; host
   memory is gate 14 (amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta must not launch
   on the leaking anchor bundles')): epochs 1-3 in the
   first pod of each class (E, A07, each new architecture); K is accepted only if peak GPU memory
   stays ≤ 90 % of the card and nothing runs out of memory (`code/canary_k.py`; Budget). If A07 at
   K = 3 still runs out of memory on 23-24 GB cards, A07-class packs go to ≥ 45 GB products only;
   if none is available, the 5M family and the floor family pause and go to Kai (batch 2,790 is not
   lowered). **Determinism probe**, per class (E and A07): one config at one seed in two pods of one
   GPU product for 21 epochs, so the traced path runs twice (epochs 1, 10, 20, 21 staged; 10, 20,
   21 committed; PREFLIGHT prints the set); weight hashes and losses compared every epoch. Training
   sets only `keras.utils.set_random_seed` (`ablation.py:597`, `train.py:261`), so bit-identity is
   not expected but not known. The probe sets the expectation for the placebo row only.
8. **Diagnostics-on invariance.** Z13 certifies the Delta patches off; replicas and cells carry the
   always-on diagnostics on. PREFLIGHT checks on CPU that diagnostics on and off give identical
   loss, traced EBOPs and kernel hashes over the first steps; if not, g_rep carries the difference,
   labelled.
9. **Always-on patches gated on the anchor tree** (X2); if one fails, the whole wave waits.
10. **Order of launch** (DELTA §7 2a/2b). At t = 0 the replicas, teachers and canaries; at the
    replica epoch-500 gate the floor family M001-M010, then the placebos and the 2b singles in the
    DELTA §7 order (T2 last), long-horizon cells first. At P = 10 all of it is released within one
    schedule (`budget.py`).
11. **Code base** ([DK4], [DK13]; frontmatter): the leak-fixed regime-B bundle (gate 14) plus the
    Delta series, rebased from 77f1ca4e before this gate; f2107a04 and e90327d4 are not launchable
    (amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta must not launch
    on the leaking anchor bundles'). If anchor production ships on another sha, nothing is re-run:
    the bases are labelled "rep-A / rep-C at config sha X", and waves 3 and 4 state their pairing.
12. **Pods and quota** ([D1], [A3]): cluster-ops checks quota and capacity at PREFLIGHT.
13. **Non-binary path under [A20]** (X5): those cells enter the packs only after a non-binary scheme
    passes the CPU build / one-step / reload gate on the frozen bundle; until then PREFLIGHT lists
    them with the failed gate line.
14. **Host-memory growth canary** (`decisions.md` 2026-09-28; anchor incident §6): on the gate-11
    bundle, one E and one A07 Delta cell run ≥ 30 epochs with the anchor's RSS gate
    (`BNJ_RSS_GATE_LIMIT_MB` = 2,100 + 5 × H MiB per arm, window epochs 5-105; erratum 2026-09-28) or W&B `system.proc.memory.rssMB`; host-RSS slope ≤ 5 MB per
    epoch per arm. If it fails, the wave waits. PREFLIGHT records the bundle sha and the result for
    E and A07 (the decision's Check line) (amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta
    must not launch on the leaking anchor bundles').

## Controls and pairing

**The control is the in-wave drift replica, always** ([D6] as amended, [DK3]; amendment against
DELTA §5.1's control row and §5.2's drift trigger, 2026-09-27): at every horizon, the replica at
the same seed, Delta sha, Delta pod. A family is one wave × target (350k, 5M; M010 is a ladder
point). Reason: no anchor-production snapshot exists. Where anchor-production [A6] snapshots (or
regime-B pilot snapshots resumed into production with matching `config_sha256` and `code_sha256`,
anchor l. 1641-1643) exist at a used horizon, **g_rep** = replica − anchor per seed is reported
with its seed count and 95 % interval, descriptively; it never replaces the replica.

**Pairing conditions.** Every paired comparison uses the anchor's gated 90/10 cache
(`/data/chang-n64-20260926/n64/data`, split_seed 1, `y_val` sha256 63049d9b…7709, `x_val` sha256
7b56c1b2…4d31); it is never rebuilt under the Delta sha, and the Z10 caches assert byte-equal
`y_val`. Pairing type per cell is the `delta.json` rule; for paired-if-hash the [A17]-style
`kernel_hashes` comparison is run at PREFLIGHT and recorded before any result. Labels: floor-family
accuracy "cross-architecture"; M009 "crosses N"; M038, M040 "crosses input set".

**Replica epoch-500 readout**, per family, before any cell of the wave starts (rep-A for 350k,
rep-C for 5M; seeds 1-8):
- **sd_rep** ([D7], [DK2], [DK5]): the ddof-1 sd of the replica's best-feasible-as-of-500
  validation accuracy over its feasible, non-degenerate, certified seeds, with k_rep (of 8) beside
  it. Its one role is the significance-mode seed rule (Appendix A); it sets no label, band or
  launch decision in ranking mode.
- **Mode readout** (descriptive, no decision reads it): sort the 8 values; the family is
  "two-mode" if the largest gap between consecutive values exceeds 3× the pooled within-cluster sd
  of the two groups it separates, with at least 2 seeds on each side. The gap's midpoint is then
  fixed as the mode threshold, and every run's value below it counts as low mode (per-cell n_low,
  Readout). The flag is weak where mean-g recovery falls: false flag 0.071 under Gaussian seeds,
  power 0.067 / 0.102 / 0.214 / 0.510 / 0.801 at per-run q 0.02 / 0.05 / 0.1 / 0.2 / 0.33
  (`screen_null.py` §18c), so "not two-mode" is not read as "Gaussian".
- the base-stability count, the arm-A feasibility count and the 5M constraint readout below.

**5M constraint active** (rule fixed now; [DK18]). The 5M target is 14.6× C's traced floor and was
set against the old quantizer's floor (anchor STUDY l. 559-565, 1497); whether BetaPID pushes at 5M
is not known. Per usable seed, three numbers: (a) the fraction of traced
epochs 251-500 whose traced EBOPs exceeds 5,000,000; (b) the selected checkpoint's EBOPs /
5,000,000; (c) the fraction of epochs 251-500 at which the logged controller β is at `min_beta` =
1e-10 within |log10 β − log10 1e-10| ≤ 0.01 (rep-C config `train.ebops.pid`: `init_beta` 1e-7,
bounds 1e-10 / 1e-3, `log: true`). A seed is **slack** if (a) = 0, (b) ≤ 0.8 and (c) ≥ 0.9. Why
0.8: a selected checkpoint at ≤ 80 % of the target sits ≥ 1,000,000 EBOPs under it, so the target
does not bound the selection. Why 0.9: the controller applied no pressure over the second half of
the cycle except brief excursions. **Family label** on rep-C: "constraint slack at 5M" if at least
⌈3k/4⌉ of its k usable seeds are slack. **Cell label:** the same rule on each of M003, M007, M008, M011 and M012 at
5M on its own usable seeds (these change the constraint the controller sees: M007's floor 474,125,
M008's group weight in the controller input); a cell whose own seeds meet it is labelled
"mechanism not exercised". Nothing is held back: the labels and the follow-up ([DK18]) change,
not what trains.

**Base stability** (DELTA §5.2). A replica with more than a quarter of its seeds 1-n diverged,
collapsed or H1-type degraded by epoch H (G1 definitions) is not a valid control; the family
pauses and goes to Kai. Default proposals: at 350k a replica of anchor arm D (E with our
optimizer); at 5M, M103 (arm D's optimizer on C) moves into this wave as the base.

**Arm A fails at 350k** (restored from DELTA §3.3 R2): fewer than ⌈3n/4⌉ of rep-A's seeds 1-n_350
feasible (non-degenerate, certified) at H, checked at the replica epoch-500 gate and again at 1,000
for M015. Then (1) the arm-A cells keep their 5M cell, their 350k cells are not launched, and the
350k question goes to Kai at K3 with the counts; (2) the floor family is read for G2 only; (3) M013
runs as a feasibility probe on A07-350; (4) FF2 re-bases to arm C at 5M (wave 3, carried forward).
**A stable replica with fewer than 3 feasible seeds at H** (possible at 5M) supports no G3
reading: G0-G2 only, no list, the family goes to Kai.

**Replica-side and placebo-side losses.** A replica seed s ≤ n lost at the horizon (infeasible,
degenerate, diverged, collapsed or certification-failed) removes seed s from every pair g of the
family (n_p drops uniformly; the header says so) but not from the family test, whose pairs d =
cell − placebo (count n_d) do not contain the replica; a lost placebo seed lowers n_d only, and the
critical value is re-simulated (`screen_null.py` §13 at n = 3; essentially no power). A seed lost
only at a longer horizon affects only the long-horizon cells. Seeds 5-8 cannot substitute for a
lost seed s ≤ n. Below 3 usable seeds the family has no ranking and goes to Kai. The
incomplete-pairs list and its survivorship label apply to cell-side losses only.

## Confounds held fixed

What differs between a cell and its replica besides the entry's delta, and how it is held:
1. **Code sha, wave, date:** shared by cell and replica (the anchor's differ: g_rep); Z13 and launch
   gate 8 hold the code.
2. **GPU product** ([D17]): recorded per run, a GPU-class column in every paired table.
3. **Data:** identical cache, split, gate, standardization (M009, M038, M040, M041 by design).
4. **Horizon truncation:** launch gate 5.
5. **Initialization and data order:** same seed, same init for equal shapes (anchor STUDY l.
   761-766; shape-changing entries are paired-if-hash); `order_seed = f(s)`.
6. **Quantizers and cost trace:** anchor [D19], [D20], [D25] everywhere; only the entries about
   them change the path (M003, M007, M008, M011, M012, M016, M017-M026, M047-M050).
7. **EBOPs controller and target:** same per family; M008 and M013 change the controller or its
   input by design; M010 changes the target.
8. **Selection, certification, numerics:** one rule for every run; TF32 off, `jit_compile false`,
   reload within 1e-7.
9. **Packing:** K differs by class ([D16]); bit-identity across packs is not assumed, and the
   per-pair seed correlation is printed beside every paired interval.
10. **Architecture class:** 350k near-floor deltas are applied to E (DELTA §3.3 R2); the floor
    family runs on A07-derived architectures (Welch package against A).
11. **Pod and pack placement:** a cell or placebo is never in its replica's pod; the placebo
    measures what pod, pack and run identity alone do to g (Falsifier (iv)).
12. **Relaunch:** a run killed and resumed by `run_pack.py` restarts from its last 25-epoch
    checkpoint while its pair may have run continuously; recorded, not controlled.

## Seeds

**Seeds 1-n per family**, `experiment.seed = s`, `order_seed = f(s)` (the anchor's convention);
n_350 for the 350k family, P-350, M010 and rep-A07-350; n_5M for the 5M family and P-5M; rep-A and
rep-C run seeds 1-8. **Ranking mode, n = 4 in both families**; only the significance-mode seed rule
can set another n (Appendix A; not expected).

**Top-k extension** ([DK16], default; band read on s_int, Selection rule "Label"). If a family's
s_int at the n = 4 readout is < 1.0 pt, n stays 4. If 1.0 ≤ s_int ≤ T (the family's label
threshold), the top 16 cells of the 5M ranked list and the top 6 of the 350k list by median g run
seeds 5-8 at H 500, paired with replica seeds 5-8, which already ran to epoch 500 ([DK2]). Above T,
no extension. k stays 16 / 6 whatever the actual m (the Budget rows are at these k). Limits: (1)
H-500 cells only (the replica seeds 5-8 stop at 500); (2) the placebos and the family test stay at
seeds 1-4, on which the extended cells were selected; (3) an extended cell's seeds-5-8 mean g, with
its own-sd interval (df 3), is printed as the selection-free estimate; (4) extended cells are
ordered among themselves by 8-seed median g and placed above the rest, which keep their n = 4
order; the header names them, and the pooled interval is re-simulated at VERIFY for the mixed n;
(5) a lost replica seed among 5-8 removes that seed from the extension only. Recovery by median g
(`screen_null.py` §19c; mean g, the companion, §16, in brackets), Gaussian seeds, **optimistic
under per-run two-mode seeds**: 5M at σ 1.0 pt 0.71 at n = 4, 0.81 extended, 0.83 at n = 6 for
every cell (0.77 / 0.87 / 0.90); 350k at σ 1.0 / 1.5 pt 0.86 / 0.70, 0.94 / 0.80, 0.92 / 0.76
(0.89 / 0.74, 0.96 / 0.85, 0.95 / 0.82). §16 draws no replica term: that cancels for mean g, not
for median g, so its median rows are optimistic for the primary (paired-model n = 4 at σ 1.0: 0.66
at 5M, 0.84 at 350k, §19a). Under per-run two-mode seeds (§19b, median g), among
draws in the band the extension adds nothing (5M 0.98 / 0.97 / 0.96 at n = 4 against 0.98 / 0.97 /
0.95 extended; 350k 0.99 / 0.98 / 0.95 against the same; q 0.02 / 0.05 / 0.1); above the band,
where the rule does not extend, it adds at 350k (0.61 → 0.71 at q 0.33, 0.54 → 0.67 at q 0.5) and
less at 5M (0.26 → 0.34, 0.26 → 0.29). Cost: Budget.

**What n = 4 resolves.** Each paired gap carries a 95 % t-interval on its own sd, half-width
t(0.975, 3) / √4 · sd_d = 1.59 · sd_d:

| sd_d | source | half-width at n = 4 |
| --- | --- | --- |
| 0.3 pt | illustration | ±0.48 pt |
| 0.85 pt | the anchor's 0.6-pt referral line × √2 | ±1.35 pt |
| 4.44 pt | √2 · 3.14 pt, the archived spread (sizing only) | ±7.1 pt |
| 1.04 pt | stress case: σ 0.6 pt at ρ = −0.5 (sd_d = σ√(2(1 − ρ))) | ±1.65 pt |
| 5.44 pt | stress case: σ 3.14 pt at ρ = −0.5 | ±8.65 pt |

The 0.16-pt binomial SE is not a lower bound on the seed sd: every seed is scored on the same jets.

**Ranking fidelity**, Gaussian seeds (`rank_sim.py`, design grid m = 37, n = 4; P(all three true
cells in the top 12), chance 0.028; median-g rank, the primary / mean-g rank / LCB80 rank, the two
companions, all three scored on the same draws, `rank_sim.py` v6 block; +1 and +3 pt are
illustrations, not an expected yield). **Optimistic under per-run two-mode seeds** (next table).

| σ (per-run seed sd) | +1 pt, ρ = 0 | +1 pt, ρ = 0.5 | +3 pt, ρ = 0 | +3 pt, ρ = 0.5 |
| --- | --- | --- | --- | --- |
| 0.6 pt | 0.96 / 0.99 / 0.97 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| 1.5 pt | 0.37 / 0.47 / 0.40 | 0.62 / 0.73 / 0.65 | 0.99 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| 3.14 pt | 0.13 / 0.16 / 0.14 | 0.21 / 0.26 / 0.22 | 0.63 / 0.74 / 0.66 | 0.87 / 0.94 / 0.90 |

Two-mode rows (low mode 5.4 pt below, within-mode sd 0.3 pt, P(low) q; 5M as above, 350k one
+1-pt cell in the top 3 of 11; n = 4). Mean g from `screen_null.py` §18; median g, the primary,
from §18b (separate draws; its mean-g column agrees within 0.01):

| q | per-run sd | 5M, mode per run: mean g / median g | 350k, mode per run: mean g / median g | either family, mode set by the seed |
| --- | --- | --- | --- | --- |
| 0.02 | 0.81 pt | 0.79 / 0.99 | 0.92 / 1.00 | 1.00 |
| 0.05 | 1.21 pt | 0.55 / 0.96 | 0.81 / 0.99 | 1.00 |
| 0.10 | 1.65 pt | 0.28 / 0.85 | 0.66 / 0.95 | 1.00 |
| 0.33 | 2.56 pt | 0.19 / 0.26 | 0.49 / 0.61 | 1.00 |
| 0.50 | 2.72 pt | 0.14 / 0.26 | 0.45 / 0.53 | 1.00 |

Under Gaussian seeds the median costs recovery (5M 0.77 → 0.66 at σ 1.0, 0.57 → 0.46 at σ 1.3;
350k 0.89 → 0.84, 0.79 → 0.73; §18b). q > 0.5 (a rare high mode, the shape of the
archived three values) is not in `screen_null.py`. Two review checks with the same model
(`review/physics_v6_rarehigh.py`, seed 606; critical v6 own check 2, seeds 20260927 / 1 / 2) give,
at 350k and T 2.1 pt, median-g recovery among draws with s_int ≤ T of 0.51-0.53 at q 0.6, 0.61-0.63
at q 0.67, 0.77-0.87 at q 0.75-0.8 and 0.98 at q 0.9; mean g, the companion, 0.39 / 0.46 / 0.55 at
q 0.67 / 0.8 / 0.9. At 5M (T 1.2 pt) the set is empty below q 0.9 and recovers 1.00 above. The
median-g T holds under a rare high mode; the mean-g companion does not, so a median / mean
disagreement mark (Ranking) is expected there. Review scripts, design arithmetic.

At a matched sd, per-run two-mode seeds cost mean-g recovery against the Gaussian rows (5M: 0.79
against 0.92 at 0.8 pt, 0.55 against 0.63 at 1.2 pt, §15, §18). **The ranking's resolution is set
by n, the cell × seed interaction sd σ√(1 − ρ) and the shape of the seed distribution; s_int
estimates the second, the §18 rows bound the third.** Any seed-level term
shared by every configuration at seed s (the replica's term, and a mode set by the seed) cancels
from the order of the means and sets only the zero line; that is why the seed-shared column is
1.00 at any per-run sd, and why the label reads s_int, not sd_rep.

## Selection rule (pre-registered, validation only)

Inherited from the anchor ([D10]; anchor STUDY l. 852-968, regime-B amendment l. 1393-1463;
[DK13]).
- **Eligible epochs are traced epochs only.** Epoch e (zero-based) is traced iff e == 0,
  (e + 1) % 10 == 0 or e + 1 is the last epoch: **51 traced epochs in the first cycle** expected
  from the staged patch 0027 (`is_traced_epoch`, `bnhgq2/ablation.py:483-489`), 50 on the committed
  anchor text (96b95f2 l. 1403-1410); PREFLIGHT prints the count on the frozen bundle and every
  denominator uses it. An untraced epoch is validated ([A12]) but never selectable.
- **Per run, the best-feasible-as-of-H checkpoint:** among traced epochs 1..H whose freshly traced
  native HGQ2 EBOPs ([D20]) is (a) ≤ the cell's target and that meet (b) EBOPs − the cell's own
  traced 0-bit floor > 0 and (c) validation top-1 accuracy > 0.21096, the highest **validation
  top-1 accuracy**; ties by validation macro-OvR AUC, lower EBOPs, earlier epoch ([A13]); the
  runner's `model_best.keras` at H, or the [A6] snapshot at H. Floors for (b): E 171,526, A07
  343,053, others their Z01 trace.
- **Degenerate and missing.** A checkpoint meeting (a) but not (b) or (c) is "feasible,
  degenerate" and carries no accuracy; infeasible, degenerate, diverged, collapsed and
  certification-failed seeds form one class, "no accuracy number". The runner's
  `model_min_ebops.keras` fallback is "no feasible checkpoint", never a result.
- **Certification** ([D11]; anchor STUDY l. 893-909): every selected checkpoint is reloaded and
  retraced on the full training split before its accuracy is read; it counts only if the retraced
  EBOPs equals the logged value (relative difference ≤ 1e-6) and is ≤ the target (CPU→GPU re-run
  rule, `decisions.md`). A mismatch is a pipeline defect, never a reason to reselect.
- **Pairs** (DELTA §5.3; [D10]). g_s = acc(cell, s) − acc(replica, s) over the n_p seeds usable in
  both; d_s = acc(cell, s) − acc(placebo, s) over n_d seeds. n_p is printed beside every g. G3
  needs n_p ≥ 3. A cell with 3 ≤ n_p < n goes to the "incomplete pairs" list with its G1/G2
  counts, its survivor mean g ("survivors only, an upper estimate") and the anchor's
  surviving-minimum imputation (labelled imputed). n_p < 3: no accuracy reading.
- **G0-G3 in order** (DELTA §5.3 l. 770-861). G0 treatment measured (M015 onset = the logged
  freeze epoch, the first feasible traced epoch ≥ 500). G1 stability (divergence; collapse =
  validation accuracy ≤ 0.25 for 10 consecutive epochs after epoch 20, stopped by
  `screen-collapse-stop`; H1-type degradation from the per-epoch logs). G2 feasibility (k_e with the
  degenerate count; traced headroom 350,000 − the cell's floor and h beside k_e and k_base). **G2
  for the floor family:** rescue = k_e ≥ 3 and k_e − k_base ≥ 2, exact McNemar p descriptive,
  with the rule's null false-rescue rate beside it (`screen_null.py` §17: 0.038 / 0.121 / 0.104 per
  entry at a shared feasibility rate p of 0.25 / 0.5 / 0.75; at the observed k_base, 0.31 / 0.74 /
  0.95 at p_e 0.5 / 0.75 / 0.9 for k_base 0 or 1). An entry whose traced floor is ≤ ½ of A07's,
  171,526.5 EBOPs, is labelled **"rescue expected from floor arithmetic"**: M001 171,526
  (0.5 EBOPs under the trigger; labelled with the others), M002 85,763, M003 114,182, M004
  41,985, M005 0 and M009 85,507 (M006 once traced).
  Each has ≥ 178,474 EBOPs of headroom against A07-350's 6,947, which is necessary, not sufficient
  (A07-350 has not yet run; (c) is not guaranteed). For them G2 is a feasibility check, not a
  finding. G3 accuracy: median g and mean g; the median with [min g_s, max g_s], the
  order-statistic interval, 87.5 % on the population median at n = 4 (75 % at n = 3); 95 % t-interval on mean g on the cell's own sd, df
  n_p − 1; the family-pooled interval (Ranking); lower 80 % bound; per-pair correlation; one-sided
  paired-t p or Welch; sign count descriptive.
- **G3′, non-inferiority** (restored from DELTA §5.3): for M023, and M024/M025 when read for cost,
  and floor-family entries at 5M, the question is whether the lower 95 % bound on g exceeds
  −0.3 pt. **Bound** (DELTA l. 844-845 does not say which side; default): the lower limit of the
  two-sided 95 % t-interval on the own paired sd, df n_p − 1. **Power** (`screen_null.py` §7,
  g = 0, ρ = 0, n = 4): P(pass) 0.074 / 0.041 / 0.031 at σ 0.6 / 1.5 / 3.14 pt; 0.80 only at σ ≈
  0.10 pt. A failed G3′ is reported **"non-inferiority not shown at this n"**, never "inferior". M023 goes to the zero-GPU `mulder` synthesis check (K5)
  whatever G3′ reads ([DK15]). The same cells also get the G3 report and ranking.
- **Lists, defined once, never interleaved.** Per family: (1) **the ranked list**, the paired
  single-lever cells at H = 500: at 350k the 12 accuracy cells on A minus M015 (at most 11, m = 11
  if every paired-if-hash check passes); at 5M the
  G3 cells on C that run, minus the long-horizon and the Welch cells (**at most 35 paired
  cells**). The family test's m cells are the same set. (2) **Welch list**, "cross-architecture
  package" or "unpaired": at 350k the floor-family accuracy against A (its SE equals the paired SE
  at ρ = 0 and is √2 larger at ρ = 0.5; with df about 2(n − 1) against n − 1 its interval is not
  wider at n = 4 unless ρ > 0, so a paired power row overstates it only if pairing helps, ρ̂); at 5M M006, M009 ("crosses N") and
  M046 if its [A17] check fails; any paired-if-hash cell whose check failed. (3) **"Horizon H ≠
  500"**: M015 at 350k and 5M (H 1,000), M031 (1,500), M032 (2,000), each against the replica at
  its H with its own-sd interval, not ranked, not in s_pool, s_int or the family test ([L8]). (4)
  **Incomplete pairs.** Baselines are comparands below the lists (G0-G3, no advance); probes and
  M010 get G2 only. *Design values* are simulated at the **design grid m = 11 / 37**
  (`screen_null.py` §13, §15, §18; `rank_sim.py`); every read re-simulates at the actual m and n_p /
  n_d vector. Packable today the ranked lists hold 9 (350k; M038, M040 wait for caches) and at most
  32 (5M; M038, M040, M041).
- **Cap** (DELTA §5.3; order amended by [DK6]): at most 12 confirm cells per confirm wave, taken in
  median-g order from the ranked lists; Kai picks at K3/K3a; nothing advances automatically into
  GPU time.
- **Ranking** ([DK6], **Kai-decided 2026-09-27, re-decided 2026-09-28**,
  `.claude/memory/decisions.md` 2026-09-28; amendment against DELTA §5.3). Cells ranked by **median g**, the median of the cell's n_p paired g_s; the median with
  [min g_s, max g_s], the order-statistic interval, 87.5 % on the population median at n = 4 (75 %
  at n = 3): one low-mode run
  in a cell or in the replica moves a 4-seed mean by 1.35 pt and the median much less (Seeds,
  two-mode rows). Beside it, **mean g**, with an interval on the family-pooled paired sd s_pool
  (pooled over the ranked cells only). The shared replica leaves n − 1 independent df in the
  replica term, so t(0.975, Σ(n_p − 1)) covers 0.94 / 0.93; the interval uses the simulated
  multiplier, 2.17 / 2.14 at design grid m = 11 / 37 for n = 4 (`screen_null.py` §15), labelled
  **"95 % at equal spread"**, since it under-covers a high-variance cell, whose own sd is printed
  beside it. The per-cell lower 80 % bound (DELTA's rule) and its rank are shown too. Mean g and
  n_low are the stability readouts: mean g credits a lever that lowers the low-mode probability,
  which the median hides. Per family, Kendall τ of median-g against mean-g ranks; a cell in the
  top 12 (5M) or top 3 (350k) by one and not the other is marked for K3a, with no threshold.
- **Label** ([DK8] as amended v6). **s_int** = the residual sd of the two-way (cell, seed)
  decomposition of the family's ranked-list validation accuracy matrix at the n = 4 readout, cells
  with complete pairs only, on the family's n_p seeds (a lost replica seed drops that column from
  every cell), placebo and replica excluded; df (m − 1)(n − 1), 30 / 108 at the design grid. It
  reads no effect size and no cell order. Every family header prints sd_rep, s_int with its 90 %
  chi-square interval, s_pool and ρ̂ side by side. If **s_int ≤ T**, the list is labelled
  "ranked"; otherwise "descriptive: s_int above T, where at least one seed model gives recovery
  below 0.5", citing the recovery rows at the measured s_int (median g §19a Gaussian, §19b per-run
  mode; mean g §15, §18, §18b). Above T recovery can still exceed 0.5: 350k Gaussian 0.50-0.55 up
  to 2.7 pt (§19a); per-run low mode, families with s_int > T, 5M 0.95 / 0.85 at q 0.05 / 0.1 and
  350k 0.89 / 0.61 / 0.54 at q 0.1 / 0.33 / 0.5 (§19b). n_low and the mode readout say which case
  applies; no rule reads them. **T = 1.2 pt at 5M and
  2.1 pt at 350k** (`screen_null.py` §19a): per RNG seed, the largest 0.1-pt value at which (i)
  Gaussian recovery by median g at σ = T is ≥ 0.5 (§15 grid) and (ii) under per-run two-mode seeds,
  median-g recovery among draws with s_int ≤ T is ≥ 0.5 at every q of the grid where
  P(s_int ≤ T | q) ≥ 0.01; T is the minimum of that value over ten seeds of the whole script
  (20260927, 1-9). Scored by mean g, the companion, the same rule gives 1.2 / 1.8 pt (§18). A lever that changes the probability of the low mode adds
  cell-specific seed structure and inflates s_int, so that error runs toward "descriptive". The
  family test is read in every family, whatever the label.
- **Family test** (`screen_null.py` §4-§5, §13, §15). *Reference:* the family's placebo, in every
  case. It does not read the ranking statistic, so [DK6]'s re-decision leaves it and its
  calibration unchanged. *Statistic:* each cell's own-sd t_i = mean d_i / (sd(d_i) / √n_d,i), df n_d,i − 1.
  *Critical value:* the one-sided α 0.10 quantile of max_i t_i under the null, simulated for the
  family's actual m and n_d vector (design grid, n = 4: 4.28 at m = 11, 6.59 at m = 37; n = 3:
  §13). *Answer:* "some cell above the placebo" if max t_i exceeds it; those cells are named,
  "above the placebo at family-wise α 0.10, not advanced", each with its own sd beside s_pool and
  its g beside d (a cell can sit above the placebo with a negative g). Every answer in VERIFY and
  REPORT carries "a 'no' is not evidence of absence". *Calibration* (P(false "yes") per family,
  n = 4, design grid m = 11 / 37, §15): 0.103 / 0.101 at
  equal spread; 0.099-0.108 with one cell at 3× or 25 % of cells at 2-3× the run sd; 0.036-0.082
  under two-mode seeds; 0.099-0.102 under a common offset (it cancels in d); 0.099 / 0.097 with a
  near-deterministic placebo. At n = 3 (cheap version, or after a placebo loss) 0.100-0.105 under
  equal and unequal spread but 0.063-0.232 under two-mode seeds: **not calibrated under two-mode
  seeds at n = 3**, labelled so wherever read. *Power* (one true +1-pt cell named, §15): 0.214 /
  0.087 / 0.051 / 0.026 at σ 0.6 / 1.0 / 1.5 / 3.14 pt (m = 11) and 0.077 / 0.030 / 0.016 / 0.007
  (m = 37). The effect one named cell needs for 50 % / 80 % power (§15a): at m = 11, 1.65 / 2.40 pt
  (σ 0.6), 4.10 / 5.95 pt (σ 1.5), 8.55 / 12.40 pt (σ 3.14); at m = 37, 2.50 / 3.55, 6.25 / 8.85,
  and 13.05 pt / above the 16-pt grid edge. *Own sd*, because a pooled sd reached a false "yes" of 0.14-0.55 (§4; [DK7]). *Not
  used:* a count of positive lower bounds (null 95th percentile 13 of 19 and 28 of 43 under the
  shared replica), and "no cell exceeds the placebo" (P(no | null) 0.084 / 0.026, §15).
- **Two readings of the placebo row** (the family test is the same in both). The probe (launch gate
  7) sets the expectation; the placebo's own epoch-500 weight hashes fix the reading per family.
  *Bit-identical:* at every seed where placebo and replica ran on the same GPU product, their
  hashes are equal; the row reads "pod, pack and identity check passed: offset measured zero on
  this product", and its rank is not read. *Divergent:* any such seed with different hashes; the
  per-epoch loss difference and the first differing epoch are printed, and the placebo is read as
  the in-family null draw. Seeds on different products are reported with their g in both readings.
  Its rank among the cells is printed, never tested. The placebo reading lists relaunches.
- **Winner's curse, non-selecting companions.** For every run: (1) **last-epoch**, accuracy at the
  last feasible, non-degenerate traced epoch ≤ H (logged, not certified); (2) **split-half**
  ([DK14]): selected on one fixed half of the validation jets (31,000, split seed recorded at
  PREFLIGHT), read on the other. Each cell gets a companion g, interval and rank for each, and per
  family Kendall τ against the primary; neither changes the list. **Rank-move flag:** a ranked cell is flagged if its rank moves by more than T
  places between the primary and the last-epoch companion, both ranked by median g. T is set from
  the correlation r of primary and companion values centred per cell, pooled over the ranked cells
  (what §8 and §15 draw): the smallest grid T whose null flag count at the lower edge of r's band is
  ≤ 1.0 (median-g ranks, §19d). At 350k T = 4 if r ≥ 0.9, 5 if 0.7 ≤ r < 0.9, 6 if 0.5 ≤ r < 0.7
  (null 0.6 / 0.9 / 0.9); at 5M T = 12 if r ≥ 0.95 (0.9). Below those r no grid T keeps the count
  at or under one (at 5M 1.2 at T = 15, r = 0.9; 5.0 at r = 0.7; design grid m = 37), so τ is
  printed and the family goes to Kai labelled "rank-move flag not calibrated at this r (§19d)". Crossing the 12th-rank line is marked, not flagged;
  flagged cells go to Kai. The companions are mitigations, not a correction (Literature); the
  seeds-5-8 mean of an extended cell is the one selection-free estimate.
- **Readout per cell** (validation only, never quotable): top-1 accuracy, macro AUC, the five
  per-class AUCs (any under 0.7 called out), feasible / degenerate / diverged counts, n_p, n_d,
  eligible traced-epoch count, both companions, own sd beside s_pool, **n_low of n** (runs below
  the mode threshold, if the family is two-mode) beside median g and mean g with the replica's and
  placebo's,
  EBOPs, accumulator EBOPs (Z03), EBOPs above the floor, headroom and h, the mechanism diagnostic,
  the constraint readout (a)-(c) for the five EBOPs-pressure cells at 5M, the anchor's collapse
  label (descriptive, anchor STUDY l. 1269-1274, with its seed count), GPU product, per-pair
  correlation, relaunched (yes / no, epoch restored from) per run; a pair with exactly one side
  relaunched is marked. Per family: sign concordance of g across the two targets of each two-target entry,
  and a flag to Kai for any cell in the top 12 by median g in accuracy and outside it by median g
  in validation macro AUC, or the reverse.
- **Pairing efficiency.** The only record on ρ (archived, N=8, three cross-arm seed correlations
  −0.34, −0.79, −0.56, each on 3 seeds; `.claude/memory/experiment-log.md` l. 2277-2279) carries no
  information on ρ: at 3 seeds a sample r piles up near ±1 under ρ = 0. Per family the pooled
  cell-replica ρ̂ (cells centred per cell) is printed with its null 95 % interval, ±0.34 / ±0.18
  (§15). An **unpaired companion** (each ranked cell against the 8 replica seeds, own-sd Welch
  max-t, one-sided α 0.10, critical 2.88 / 3.59, §15) never changes the list or the test; if ρ̂ is
  below its null interval, the report says "pairing did not help here".
- **The ROC-test set is never touched**; no screen number enters any record (DELTA §5.1).

Clarification ([D10], dated 2026-09-27): DELTA §5.1 tests (b)-(c) on the most accurate (a)
checkpoint; the runner selects among checkpoints meeting (a)-(c) (96b95f2 l. 879-882). This STUDY
uses the runner's rule; they differ only in an edge case.

## Falsifier

Nothing is "falsified" at a screen (DELTA §10); confirm does that. What would revise the claims
this wave supports:
- **The wave's "no"**, per family: no cell's own-sd t against the placebo exceeds the family's
  simulated critical value: "no cell resolved above the placebo at this resolution", which sees
  only multi-pt effects (50 % power at 1.65-6.25 pt, σ 0.6-1.5; Selection rule) (significance
  mode: Appendix A). It is read in every family, ranked or descriptive. Under the global null it is
  returned with probability 0.90 at equal spread, 0.89-0.90 under unequal spread, 0.92-0.96 under
  two-mode seeds and 0.90 under a common offset (n = 4, §15), about 0.81 for the wave. A "no" is
  not evidence of absence (power: Selection rule). **In every family** the list goes to Kai at K3a
  (at most 12 cells go to confirm, Selection rule "Cap") with its label, the winner's-curse note
  and the companion flags, and Kai may cut wave 3 (DELTA
  §5.3). A "descriptive" list supports nomination with its label, never a resolved gap.
- **Per cell, directional.** A cell predicted "up" in `delta.json` whose 95 % own-sd interval on g
  lies entirely below 0 is reported "prediction contradicted at screen, not advanced", with the
  list's expected null count, ≤ 0.025 · (cells read), printed at the read (overdispersed by the
  shared replica). A floor-family entry predicted to raise 350k feasibility with k_e ≤ k_base is
  "contradicted at screen" (McNemar exact p descriptive). A cell whose mechanism diagnostic moves
  against its prediction is flagged "mechanism not confirmed" even if it ranks high.
- **Design validity.** (i) A replica unstable in more than a quarter of its seeds, rep-A failing
  ⌈3n/4⌉, or a replica with fewer than 3 feasible seeds at H: Controls. (ii) g_rep on ≥ 3 seeds with
  a 95 % interval excluding 0 or |mean| > 0.3 pt: the family's gaps are labelled "measured at the
  Delta sha, transfer to the anchor sha not shown" (descriptive; the replica stays primary). (iii)
  An unresolved certification mismatch on any replica seed: that family's control is incomplete.
  (iv) **Placebo check:** two-sided paired t of placebo − replica on its own sd (df n_p − 1) at α
  0.05; if it fires, the g column and zero line are labelled "zero line not calibrated" and go to
  Kai before any use. False flag 0.050; it detects an offset with probability 0.5 / 0.8 at 1.25 /
  1.85 pt (σ 0.6), 3.05 / 4.55 (1.5), 6.55 / 9.55 (3.14) (`screen_null.py` §12). If every per-seed
  placebo g is 0, it passes ("offset measured zero on this product"). If the probe found a product
  bit-identical, any nonzero per-seed placebo g on that product flags on its own as
  "pack-composition effect or nondeterminism, not separated" (the probe does not vary pack
  composition), and the family is in the divergent reading. (v) The 5M constraint does not bind on
  rep-C (Controls): the 5M family is labelled "constraint slack at 5M" and [DK18] applies.
- **Formula check.** The placebo's expected g is 0 (divergent reading: its interval covers 0 in
  about 95 % of families; bit-identical: g = 0 on same-product seeds, not a red flag). An exactly
  zero per-seed g_rep would mean the runs did not vary, a red flag.

## Budget

**Counts and run-epochs** (`budget.py` v5, reads `delta.json`; design arithmetic): per seed the
350k family (with M010) needs 12,500 cell-epochs and the 5M family 25,000; each placebo adds 500
per seed; rep-A adds 4,000 + 500 · n_350, rep-A07-350 500 · n_350, rep-C 4,000 + 1,500 · n_5M;
the teachers 4,000 once. Run-epochs = 14,000 · n_350 + 27,000 · n_5M + 12,000. E-class runs are the
16 cells on arm A, P-350 and rep-A; everything else is A07-class. The three excluded teacher cells
would add 1,500 · n_5M.

**Timing basis, a labelled projection.** A GPU-throughput-bound per-slot cost of 136.5 / 6 = 22.75
pod-seconds per run-epoch; **K = 3, 4, 5 and 136.5 s are not measured** (Reference table). A07 is
r × 22.75 with r ∈ {1, 2} as illustrations (C′-s1 gives r ≈ 1.35 against E's regime-A 218 s,
anchor `RUN.md` l. 70-72, 162). The regime-B pilot and the canaries measure s_e, K and r before
launch; PREFLIGHT restates the table.

**Pod-hours and wall clock at P = 10 pods** ([D1]). Pod-hours = Σ run-epochs × pod-seconds per
run-epoch / 3,600; they are slot-seconds, so billed GPU-pod-hours (empty slots included) are
higher. The wall clock is a pack schedule (`budget.py`): packs of equal class and horizon, E at K =
4, A07 at K = 3, longest first; replicas and teachers at t = 0; cells and placebos when every
replica has reached epoch 500 (12.6 h at r = 1, 19.0 h at r = 2); the extension when the last H-500
pack ends. It excludes the wait for launch gate 1. The wall clock assumes gate 14 passed and no
relaunch (amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta must not launch
on the leaking anchor bundles').

| (n_350, n_5M) | runs | run-epochs (E / A07 / total) | certifications | pod-hours r = 1 / 2 | wall clock r = 1 / 2 |
| --- | ---: | --- | ---: | --- | --- |
| **(4, 4), the design** | **302** | 42,000 / 134,000 / 176,000 | 318 | 1,112.2 / 1,959.0 | 5.4 / 9.2 d |
| (4, 4) + extension, both families ([DK16]) | 390 | 54,000 / 166,000 / 220,000 | 406 | 1,390.3 / 2,439.3 | 6.7 / 11.6 d |
| (4, 4) + extension, 5M only | 366 | 42,000 / 166,000 / 208,000 | 382 | 1,314.4 / 2,363.5 | 6.6 / 11.6 d |
| (4, 4) + extension, 350k only | 326 | 54,000 / 134,000 / 188,000 | 342 | 1,188.1 / 2,034.9 | 5.9 / 9.7 d |
| (6, 4) | 354 | 61,000 / 143,000 / 204,000 | 372 | 1,289.2 / 2,192.8 | 5.9 / 10.3 d |
| (8, 4) | 406 | 80,000 / 152,000 / 232,000 | 426 | 1,466.1 / 2,426.7 | 6.7 / 11.1 d |
| (4, 6) | 392 | 42,000 / 188,000 / 230,000 | 414 | 1,453.5 / 2,641.5 | 6.6 / 11.6 d |
| (4, 8) | 482 | 42,000 / 242,000 / 284,000 | 510 | 1,794.7 / 3,324.0 | 8.0 / 14.7 d |
| (6, 6) | 444 | 61,000 / 197,000 / 258,000 | 468 | 1,630.4 / 2,875.3 | 7.2 / 12.6 d |
| (8, 8), upper bound | 586 | 80,000 / 260,000 / 340,000 | 618 | 2,148.6 / 3,791.7 | 9.5 / 16.6 d |
| packable today, (4, 4) | 240 | 32,000 / 110,000 / 142,000 | 256 | 897.4 / 1,592.5 | 4.5 / 7.9 d |

The (6, ·) and (·, 6) rows are the n = 6 alternative to the extension; n = 8 rows arise only in
significance mode (Appendix A). **Packable today** (`code/GATES.md` §6 "Packs", l. 836-842): M006
(no traced floor), M047-M049 and both teachers (X5), and the four uncached cells M009, M038, M040,
M041 (gate 3) are left out: 212 cell, 8 placebo, 20 replica and 0 teacher runs, matching the
generated packs (220 cell-phase arms in `manifests/delta_w2_cells_packs.json`, 20 replicas in
`delta_w2_t0_packs.json`). **Check:** 176,000 × 22.75 / 3,600 = 1,112.2; the placebos add 8 runs,
4,000 run-epochs and 25.3 / 37.9 pod-hours at r = 1 / 2, and about 0.3 d of wall clock (5.1 / 9.0
d without them); replica seeds 5-8 add the same pod-hours and no wall clock. **Alternative, E at
K = 5** (the anchor's wave-1 packing): same pod-hours and wall clock at (4, 4); the replica gate
moves to 15.8 h at r = 1.

**Arms per pod** ([D16], [DK11]): the Delta memory canary for every class (launch gate 7).
Planning values on 23-24 GB products (A10, 3090): **E at K = 4** (floor(0.9 × 23,028 / 4,354); K =
5 is 21,770 MiB = 94.5 % of an A10, accepted only if the measured peak fits), **A07 at K = 3**; K =
5-6 on ≥ 45 GB products; the old A100 exclusion is superseded by the GPU amendment above. The anchor packs its wave 1 at
K = 5; the Delta keeps the 90 % rule because its pods carry diagnostics and mix more classes. Rule
PACK: about 2 CPU per arm; host memory per arm ≥ baseline + slope × H (anchor incident §6
PACK-MEM): at the gate-14 limit of 5 MB per epoch and a 2.1-GB baseline, about 4.6 GB at H 500
(6 Gi suffices), 7.1 GB at H 1,000 and 12.1 GB at H 2,000 (rep-C, M032), so replica and
long-horizon pods are sized at PREFLIGHT from the measured slope (`budget.py`, PACK-MEM line)
(amended v7, 2026-09-28, `decisions.md` 2026-09-28 'Delta must not launch
on the leaking anchor bundles'); 40 % GPU floor, `bnjettag.io/arms-per-pod`,
`nrp_doctor.py lint` on every manifest.

**Cheap version** (the fallback; DELTA §5.4; [DK1]). The 38 T0/T0a/T1 singles with a screen cell,
3 seeds, one target each (350k where the entry has one; 1.4M for M010; else 5M), no baselines or
teacher cells, the placebos and one replica per base (rep-A to 1,000, rep-C to 2,000) at 3 seeds:
114 + 6 + 9 = 129 runs, **79,500 run-epochs**, 502.4 / 853.1 pod-hours at r = 1 / 2, 2.8 / 4.5 d
(`budget.py`). It is a
ranking; its label reads s_int on 3 seeds (df 2(m − 1)) against the family's T, labelled
"threshold simulated at n = 4"; its family test is the same at n = 3 (not calibrated under two-mode
seeds). **The choice is coverage, not resolution:** the full screen adds the T2 entries, the
baselines, the 5M cells of two-target entries and the df-7 replica sd; 3 → 4 seeds changes a
cell mean's SE by √(4/3) = 1.15. (DELTA's 69,000 run-epochs had two replicas; the third, the longer
replicas and the placebos add 1,500, 6,000 and 3,000.)

**Certification cost, outside the table.** [D11] retraces every selected checkpoint on the full
training split (558,000 jets): one per cell, placebo and teacher run, one per replica readout
horizon (the certification column), plus the three teacher cells when they join. The epoch-500
readouts of M015, M031 and M032 used by [L1](a) are not certified and are labelled "uncertified,
[L1] only"; companion values are not certified. Retraces run as cluster CPU Jobs on NRP Nautilus
(`certify_ebops.py`), never on the laptop; PREFLIGHT states their CPU-hours from one timed retrace
per class.

**Not spent here.** No C-synthesis on `mulder`; no training or synthesis on the laptop; no ROC-test
evaluation.

## Conventions compliance

| convention | row | will implement / not applicable because |
| --- | --- | --- |
| `jet-tagging-metrics.md` | Data and splits | Deviation inherited from the anchor, flagged: 90/10 split, validation n = 62,000 (house records use 124,000), labelled on every number. ROC-test not used |
| `jet-tagging-metrics.md` | Metrics | Deviation inherited from the anchor: validation top-1 accuracy is primary and the selection metric, macro-OvR AUC beside it and the first tie-break; per-class AUCs per cell; working-point rejection is confirm-tier (Z09) |
| `jet-tagging-metrics.md` | Seeds and intervals | n ≥ 4 per cell, paired by seed (or Welch) with a 95 % t-interval on the own sd, sign count and per-pair correlation. The 8-seed rule for gaps under 0.005 is met only at confirm. **Deviation, declared:** the convention reads an interval covering zero as flat (l. 44-45); this screen never calls a gap flat, because at n = 4 the half-width is ±1.35-7.1 pt (Seeds) |
| `jet-tagging-metrics.md` | Labelling | "validation top-1 accuracy, n = 62,000, screen, as of epoch H, not quotable" on every number; validation and ROC-test never share a column |
| `jet-tagging-metrics.md` | Validation checks 1-6 | 1 recompute at VERIFY; 2 n = 62,000 asserted; 3 reproduction probably unavailable, the placebo, g_rep and the pilot epoch-500 values stand in; 4 selection on validation only; 5 per-class AUCs; 6 `verify_check.py` |
| `jet-tagging-metrics.md` | No comparison across N or input sets | Only M009 (crosses N, Welch list) and M038, M040 (input set), by design, labelled |
| `jet-tagging-metrics.md` | Pitfalls | Cross-axis: floor-family and Welch cells in their own list. Screen vs full schedule: never compared. Validation vs held-out: no held-out number. Cost is read on the selected checkpoint; the companion carries its own epoch's EBOPs |
| `quantization-and-cost.md` | Configurations; cost | W1 binary except the labelled baselines M047-M050; anchor [D19] widths. Native HGQ2 EBOPs on the selected checkpoint, accumulator EBOPs beside it, never in its place |
| `quantization-and-cost.md` | Selection under a budget | **Deviation, inherited from the anchor, flagged:** the rule of record selects on validation macro-OvR AUC; this screen selects on accuracy (AUC the first tie-break) among checkpoints ≤ target, above the 0-bit floor and above chance; "no feasible checkpoint" when none; accuracy-vs-AUC concordance reported |
| `quantization-and-cost.md` | Pitfalls; checks 1-4 | Over-target and fallback checkpoints are "no feasible checkpoint"; acceptance by rule (a) and certification; code sha per pod; key diff at PREFLIGHT. Binary gate (two nonzero symmetric values per binary layer, per channel for M024/M025); stored vs remeasured widths; reload within 1e-7; the schedule labelled a screen |
| `fpga-synthesis.md` | all | Not applicable: no synthesis; `hw_labels` carried; no LUT, DSP or latency statement |
| `figures.md` | all | At REPORT: forest plots of g per family ("validation, n = 62,000, screen, not quotable") with n_p, per-seed points, GPU class, the placebo row; marker = median g with its order-statistic interval; mean g with its own-sd 95 % t-interval and the pooled '95 % at equal spread' interval, each named; per-seed points; the family test as a t_i panel against the re-simulated critical line, placebo named; a named cell shows d and g; long-horizon and Welch lists in their own panels; a per-cell EBOPs column beside g; the style kit and `tools/plot_check.py` |
| House rules | seeds, pre-registration, falsifier, compute, W&B | n ≥ 4 (3 in the cheap version); selection written before any run; Falsifier above; NRP Nautilus only, CPU gates only locally, no `mulder`; `BNJetTag-Delta` / `delta-20260926-w2`, canary group `delta-20260926-w2-canary`, `BNJ_STAGE` per run |

## Decision labels

[D], [DK], [A] and [L] labels below are this STUDY's; [DK] labels are the orchestrator's defaults,
"Kai may override at the launch gate", with their costs and alternatives in "Where I am not sure",
except [DK6], which Kai decided. Labels written "anchor [..]" or bare elsewhere ([A6], [A12],
[A13], [A17], [A19], [A20], [D19], [D20], [D21], [D25]) are the anchor STUDY's (96b95f2); the
anchor's trace-cost branch is always "anchor [D15]", and bare [D15] is this STUDY's Bop setting.

- **[D1]** 10 Delta pods on top of the anchor (Kai, 2026-09-27; [A3]). **[D2]** Bop flip
  mirror, w ← 2α − w, keeping β (patch 0024; Kai). **[D3]** Run the Delta trainings (Kai; full screen
  by default, [DK1]). **[D4]** Bases A, A07-350, C (anchor [D21], Kai-confirmed 2026-09-27 08:40
  PDT). **[D5]** Validation only. **[D6]** Control: the in-wave replica, always (amended v2).
- **[D7] sd_rep** (amended v2; amended v5, 2026-09-27): the replica's epoch-500 sd over seeds 1-8,
  the significance-mode seed-rule input only.
- **[D8] Seed rule** (amended v2 and v4; amended v5, 2026-09-27): significance mode as Appendix A;
  ranking mode n = 4 in both families, with the [DK16] extension read on s_int. The compute pause
  at an sd_rep ceiling is withdrawn in v5.
- **[D9]** BH m fixed at 43 / 19 (Appendix A). **[D10]** Selection rule inherited from the anchor
  runner, traced epochs only, with the dated clarification. **[D11]** Certification before reading.
  **[D12]** Exclusions X1-X5, R1 restored. **[D13]** Teachers run here first ([DK9]). **[D14]**
  Training-only levers at 5M on C ([DK10]). **[D15]** Bop γ = 1e-4, τ = 1e-8 ([DK12]). **[D16]**
  Packing by the Delta memory canary (amended v3; [DK11]). **[D17]** GPU product per family, else
  per pair. **[D18]** Horizon-truncation check (launch gate 5).
- **[DK1]** full W2 screen; **[DK2]** replica seeds 1-8 to epoch 500; **[DK3]** always
  replica-primary; **[DK4]** launch without anchor-production snapshots; **[DK5]** seed-rule input =
  the replicas' sd; **[DK6]** median-g ranking, mean g beside it (Kai-decided 2026-09-27; re-decided
  2026-09-28, amended v6; was mean g); **[DK7]** placebos and the placebo-referenced own-sd family
  test; **[DK8]** label threshold T per family (amended v5, 2026-09-27, was the sd_rep ceiling;
  amended v6, 2026-09-28, floor and ten-seed rule); **[DK9]** baselines and teachers run; **[DK10]** training-only levers
  at 5M; **[DK11]** packing by canary; **[DK12]** no Bop τ scan; **[DK13]** regime B; **[DK14]**
  split-half companion; **[DK15]** M023 to `mulder` whatever G3′ reads; **[DK16]** top-k extension
  on the s_int band; **[DK17]** withdrawn in v5 (the pause default); **[DK18]** 350k follow-up if
  the 5M constraint is slack.
- **[A1]** The Delta series is rebased on the anchor tree; code sha fixed at PREFLIGHT; Z13 is a
  hard gate. **[A2]** The `run_pack.py` item is resolved at PREFLIGHT. **[A3]** About 27 GPU pods in
  `cms-ml` at peak (anchor wave 1 about 13 at K = 5, wave 2 about 4, Delta 10; anchor l. 1459-1463,
  1483); checked at PREFLIGHT. **[A4]** The former A100 ban is superseded; check live quota, scheduling and the product canary before use.
- **[L1]** One cosine cycle (H = 500) may not predict the 7,000-epoch outcome; the screen only
  nominates (no transfer number exists in the literature, §1). Attempted, zero GPU: (a) the
  long-horizon cells are read at their epoch-500 snapshot ("uncertified, [L1] only") and at their H
  against the replica at the same epoch; at 5M the order of M015, M031, M032 and rep-C at 500 is
  compared with the order at each H (a count of order changes over 4 configurations, not a test);
  (b) when anchor-production snapshots exist, the rank correlation of epoch 500 against 7,000;
  (c) seed-rank persistence of the replicas, labelled "not a test of [L1]".
- **[L2]** Gaps are measured at the Delta sha; transfer to the anchor is tested at confirm (and
  read through g_rep).
- **[L3]** The anchor pilot sd has df 1 and is descriptive; sd_rep has df ≤ 7 and is a point
  estimate in the seed rule.
- **[L4]** Timing is arithmetic, not measured (Budget). **[L5]** EBOPs is not silicon.
- **[L6]** Winner's curse: the best of at most 51 traced epochs is biased upward; the bias cancels in
  a pair only if cell and replica fluctuate alike with the same number of eligible checkpoints,
  which fails for M018-M020, M028, M029, M032, M034, M008 and M011-M013 (bias of the order of g0,
  sign set by the lever). The companions, eligible-epoch count and rank-move flag are the check; at
  5M the rank-move flag is calibrated only at r ≥ 0.95, and below that the companions and the
  eligible-epoch count are the check.
- **[L7]** The training-only levers (M017-M037) are screened at 5M on A07 only ([D14]); their
  transfer to 350k on E is not tested. A training-only lever sent to confirm is confirmed at 350k on
  arm A as well, or its transfer is labelled untested. If rep-C shows the constraint slack at 5M, no
  training-only lever goes to confirm on its 5M screen alone: it goes after the 350k follow-up
  ([DK18]) or, if Kai decides so at K3, with the label "screened with the constraint slack".
- **[L8]** The placebos run at H = 500 only, so the long-horizon cells have no placebo at their
  horizon: list (3) of the Selection rule.

## Known limitations at freeze

Frozen under Kai's rule of 2026-09-28 (`decisions.md`): STUDY review round 6 left these as
Category B; they are disclosed, not fixed, and VERIFY reads every list with them.

- **K1. The 350k label threshold depends on a constant.** T = 2.1 pt is where
  P(s_int ≤ T | q 0.5) crosses the 0.01 floor, not where recovery crosses 0.5: T is 2.0 / 2.1 /
  2.2 / 2.3 pt at floor 0.005 / 0.01 / 0.02 / 0.05 (design seed). A 350k list with s_int between
  2.0 and 2.3 pt carries its label by that choice. Labels only; nothing that runs depends on T.
- **K2. The label reads a non-robust spread; the ranking is robust.** s_int counts every
  low-mode run; median g discards it. Under a per-run low mode a "descriptive" list can recover
  0.85-0.95 (5M) by median g (Label, §19b). A robust s_int (median-polish residuals, MAD-scaled)
  with T re-derived was not adopted.
- **K3. The primary has only an order-statistic interval.** Median g carries [min g_s, max g_s]
  (87.5 % at n = 4, 75 % at n = 3); the "95 % at equal spread" and own-sd intervals belong to
  mean g.
- **K4. The 5M rank-move flag is calibrated only at r ≥ 0.95** (§19d, m 37: null count 1.2 at
  T 15, r 0.9). Below that the companions and the eligible-epoch count are the winner's-curse
  check, and the absence of a flag is not evidence of no rank movement. Running the flag on
  mean-g ranks (T 10 / 15) was not adopted.
- **K5. The rare high mode is checked only by review scripts** (`review/physics_v6_rarehigh.py`;
  critical v6), not in `screen_null.py`; the median-g label holds there, the mean-g companion
  recovers 0.39-0.55.
- **K6. Relaunches are recorded, not controlled.** A resumed run replays from its last 25-epoch
  checkpoint; its pair may not have.
- **K7. v6 moved outcomes without changing rule text.** Scoring by median g raised the 350k T
  from 1.8 to 2.1 pt (looser) and left the 5M rank-move band 0.90-0.95 uncalibrated (was T 15).

## Where I am not sure

Each block is an orchestrator default ("Kai may override at the launch gate") with its cost, or an
item the STUDY arbiter left to Kai. Already answered by Kai (`decisions.md` entries of 2026-09-27
and 2026-09-28): launch gate 1 (the regime-B pilot readout); [DK6] (median g primary, mean g with
its family-pooled interval and LCB80 beside it); and the freeze: if STUDY review round 6 finds only
new Category B items, the design is frozen and launched with them disclosed as known limitations,
while any Category A still blocks. Costs are the Budget rows (`budget.py`).

**Median g in the design values** (v6): the [DK8] T rule, the [DK16] extension rows, the rank-move
thresholds and the fidelity table are scored by median g, from the same draws as their mean-g rows
(`screen_null.py` §19, `rank_sim.py` v6 block). The ranking interval belongs to mean g; the family
test does not read the ranking statistic.

```
DECISION: [DK8] label threshold T per family from the screen_null.py rule (amended v6), scored by
  median g, the primary (§19a): 1.2 pt at 5M, 2.1 pt at 350k. It changes only the "ranked" /
  "descriptive" label, never what runs. Cost: none. Per-seed T (seeds 20260927 / 1-9):
    median g     5M 1.2 / 1.2 1.2 1.2 1.2 1.2 1.2 1.2 1.2 1.2   350k 2.1 / 2.1 2.7 2.1 2.3 2.1 2.1 2.6 2.6 2.1
    mean g       5M 1.3 / 1.2 1.3 1.3 1.2 1.2 1.3 1.3 1.3 1.3   350k 1.9 / 1.9 1.9 1.8 1.9 1.9 1.9 1.9 1.9 1.9
    v5 rule      5M 1.3 / 1.0 1.1 1.1 0.9 1.2 1.2 1.1 1.1 1.2   350k 1.5 / 1.3 1.2 1.1 1.4 1.2 1.3 1.4 1.4 1.4
  (mean g: §18, the companion; v5 rule: any non-empty conditional set, mean g, where one draw of
  20,000 could veto or pass a T.) By median g at the design seed, condition (i) binds at 5M
  (Gaussian 0.52 at 1.2 pt, 0.46 at 1.3) and condition (ii) at q 0.5 binds at 350k (at 2.2-2.7 pt
  sets of 338-9,126 draws recover 0.45-0.50, just under 0.5; at 2.1 pt the set, 113 draws, recovers
  0.48 and sits under the floor). Those near-0.5 rows are why the 350k seeds spread 2.1-2.7; the
  ten-seed minimum absorbs the seed noise, not the floor: at the design seed the 350k median-g T is
  2.0 / 2.1 / 2.2 / 2.3 pt at floor 0.005 / 0.01 / 0.02 / 0.05 (mean g 1.9 / 1.9 / 1.9 / 2.0; critical
  v6 own check 1; `screen_null.py` §19e); a 350k s_int of 2.0-2.3 pt is labelled by the floor
  constant (Known limitations).
  Consecutive median s_int differ by <= 0.1 pt above 1.0 pt (0.055 / 0.093) and cannot below it
  (0.186 / 0.421: the low-mode count in the m x 4 matrix jumps); no T candidate lies there
ALTERNATIVES: the mean-g T 1.2 / 1.8 pt (§18); the v5 values 1.3 / 1.5 pt (one seed, v5 rule);
  one T for both families (1.2 pt); the mean-g Gaussian-only limits (1.4 / 3.0 pt, §15); 350k T
  1.8-2.0 pt (mean-g or floor-0.005 value)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: [DK16] top-k extension when 1.0 <= s_int <= T at the n = 4 readout (top 16 at 5M, top 6
  at 350k, seeds 5-8). Cost if both families land in the band: +88 runs, 1,390.3 / 2,439.3
  pod-hours at r = 1 / 2 against 1,112.2 / 1,959.0 (Budget). Gaussian recovery gain by median g
  0.71 -> 0.81 at 5M, sigma 1.0 (§19c, no replica term, optimistic for median g; paired-model
  n = 4 0.66, §19a; mean g 0.77 -> 0.87, §16); under per-run two-mode seeds
  the gain is nil in the band and appears above it at 350k (Seeds)
ALTERNATIVES: extend above T at 350k (the "+ extension, 350k only" Budget row: 326 runs,
  1,188.1 / 2,034.9 pod-hours); n = 6 for every cell of the family (the (6, 4), (4, 6), (6, 6)
  rows); n = 4 always
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES   (the GPU cost is Kai's)
```
```
DECISION: no compute touchpoint at the replica gate. sd_rep is printed before the cells launch and
  no ranking-mode rule reads it; the full (4, 4) design runs (Budget: 302 runs, 1,112.2-1,959.0
  pod-hours, 240 packable today; budget.py). The withdrawn pause saved little (change log v5)
ALTERNATIVES: Kai stops or cuts the wave at that read on a very large sd_rep, as his call at the
  read, not a pre-registered branch
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: [DK18] if rep-C shows the 5M constraint slack: 5M results labelled "constraint slack at
  5M" (cells by their own seeds, Controls) and the 18 training-only levers (M017-M026, M028-M034,
  M037) re-screened at 350k on arm A in a follow-up wave with its own STUDY: indicatively 84 runs,
  58,000 E run-epochs, 366.5 pod-hours, 2.6 d at P = 10 (budget.py). Kai decides at K3 between the
  follow-up and confirm with the slack label ([L7])
ALTERNATIVES: label only; move them to 350k in this wave (changes [DK10] before the readout
  exists); lower the 5M target (a DELTA design change)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: X5: M047-M049, P-T1, P-T2 and the teacher-dependent cells wait for a non-binary path under
  the anchor's [A20] guard (launch gate 13); the training-batch session is writing it as anchor
  [A22]; the rest of the wave does not wait
ALTERNATIVES: another quantizer for the baselines and teachers (changes what the comparand
  means); drop them from wave 2
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES   (a design call for the patches owner and Kai)
```
```
DECISION: [DK1] full W2 screen (Budget, (4, 4) row)
ALTERNATIVES: the cheap version (Budget; coverage, not resolution)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES   (Kai said "run the Delta trainings", not which)
```
```
DECISION: [DK2] rep-A and rep-C at seeds 1-8 to epoch 500 (+8 runs, no wall-clock change; cost as
  the placebos, Budget "Check"): the df-7 seed-rule input and the replica partners for [DK16]
ALTERNATIVES: replicas at seeds 1-n only (no extension partners, df 3 at 5M)
CONFIDENCE: HIGH   FLAG FOR HUMAN: YES
```
```
DECISION: [DK3] replica-primary; [DK4] launch without anchor-production snapshots (relabel "at
  config sha X" if needed); [DK5] seed-rule input = the replicas' sd
ALTERNATIVES: anchor-primary or waiting for production (unbounded delay); the pilot's 2-seed sd
CONFIDENCE: HIGH / MEDIUM / HIGH   FLAG FOR HUMAN: YES   (amend DELTA §5.1, §5.2, §6.3, §7 2a)
```
```
DECISION: [DK7] placebos P-350 and P-5M (+8 runs; Budget "Check"), launched whatever the probe
  finds; family "no" = own-sd max-t against the placebo (Selection rule)
ALTERNATIVES: a pooled sd, replica- or placebo-referenced, with or without a homogeneity gate
  (false "yes" 0.13-0.55 in the scenario rows, §4-§5); variance-moderated max-t (plan.md dead
  ends); no ranking-mode "no"
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES
```
```
DECISION: [DK9] baselines M047-M050 run as comparands; teachers first. [DK10] training-only levers
  at 5M on C. [DK11] K per class from the canary (E 4, A07 3 planning). [DK12] Bop at the DR-22
  seed, no tau scan. [DK13] regime B. [DK14] split-half companion. [DK15] M023 to mulder whatever
  G3' reads
ALTERNATIVES: drop the baselines or defer the teachers; levers at 350k on A or at both targets
  (+56,000 run-epochs, DELTA §11); E at K = 5; a tau scan (m rises to 45); regime A; split-half
  as primary; DELTA as written for M023 (G3' would almost never pass, Selection rule)
CONFIDENCE: MEDIUM ([DK11], [DK12] LOW; [DK13] HIGH)   FLAG FOR HUMAN: YES
```

**Other rows, not flagged.** BH m fixed at 43 / 19 with p = 1 for unrun cells (Appendix A;
tightening). Best-of-H primary with two non-selecting companions and a rank-move flag whose T follows
the observed centred r (a fixed T gives several null flags per family at 5M, §15). Certification of
every selected checkpoint (318 retraces at (4, 4); tightening over DELTA).

**Also uncertain.** The anchor pilot A rule (launch gate 1) and rep-A's ⌈3n/4⌉; A07's cost ratio r
and memory at batch 2,790; how many cells X2 leaves out; the regime-B s_e; 51 or 50 traced epochs;
which placebo reading applies; whether the 5M target binds; whether anchor [A22] arrives in time
(X5); and whether the seeds are two-mode here with a seed-shared low mode (s_int against sd_rep,
ρ̂, n_low). **Follow-up if a seed-shared low mode appears:** `order_seed = f(s)`
ties init and data order to one seed (Dodge et al. 2020), so a small factorial on replica seeds
(init fixed with order varied, and the reverse) is the follow-up that finds which one sets the
mode; a separate campaign.

**Literature.** `research/screen-design-literature.md` (physics-researcher, requested by the
orchestrator 2026-09-27; not re-checked against the sources): §1 multi-fidelity screening gives no
transfer number for H 500 against 7,000 ([L1]; the extension adds seeds at one horizon, so it does
not lean on successive halving); §2 heavy-tailed or two-mode seeds (Picard 2021) are why the test
uses own sd and the ranking carries two-mode rows, and init and order variance are one term here
(Dodge et al. 2020; Bouthillier et al. 2021 cited from its abstract only); §3 the companions are
mitigations, not a correction (Cawley & Talbot 2010; Dwork et al. 2015); §4 the own-sd max-t
extends Dunnett (1955) to unequal variances, and variance moderation was not adopted (`plan.md`);
§5 nondeterminism (Pham et al. 2020; Zhuang et al. 2022) is measured in launch gate 7 and the
placebo readings. The note's research-log lines are the orchestrator's to add.

## Appendix A. Significance mode (not armed for this wave)

**Not armed for this wave.** It arms in a family only if the replica sd at the epoch-500 gate is at
or below the thresholds below, 0.044-0.134 pt, which is under every spread this project has
recorded: the archived N=64 spread is 3.14 pt, the anchor's referral line is 0.6 pt, and even the
weak lower bracket (N=8, 0.19 pt, another N and recipe; Reference table) is above every n = 8
threshold. It shows only that sub-1-pt spreads occur in this code base.

**When it would arm** ([D8] as amended, [DK2], [DK5]; DELTA §5.1 l. 681-735 with the dated
amendment in the change log; k_joint from `screen_power.py`, run 2026-09-27, design arithmetic).
The input is sd_rep (Controls; df ≤ 7) at the Delta sha, with sd_plan = √2 · sd_rep, or
max(√2 · sd_rep, sd(g_rep)) if g_rep exists on ≥ 3 seeds at 500 (not expected). The anchor pilot's
2-seed sd (A-s1, A-s2, df 1) is printed beside it, descriptive only. An sd_rep on k_rep ≤ 6 seeds is
labelled "on k_rep of 8 seeds, survivors only" and cannot by itself raise n.
- **350k** (m = 19, α_eff = 0.10 / 19 = 0.00526): n_350 is the smallest n in {4, 6, 8} with
  k_joint(n, α_eff) · sd_plan ≤ 0.3 pt; k_joint 3.66 / 2.09 / 1.58, i.e. sd_rep ≤ 0.058 / 0.102 /
  0.134 pt for n = 4 / 6 / 8.
- **5M** (m = 43, α_eff = 0.00233): k_joint 4.83 / 2.50 / 1.83, i.e. sd_rep ≤ 0.044 / 0.085 /
  0.116 pt.
- **If no n qualifies**, the family runs in ranking mode at n = 4 (Seeds), unless Kai buys n = 8
  with g_res = k_joint(8, α_eff) · sd_plan as the MDE target and gate (ii) at g_res / 2, declared
  before the family's cells launch (DELTA §5.1 item 3); for example g_res(8) = 1.58 · √2 · 0.6 =
  1.34 pt at 350k at a 0.6-pt spread. Costs: Budget, the (8, ·) and (·, 8) rows.
- **The read can raise or lower n** (amendment against DELTA §5.2 "never raises n"). If n rises,
  replica seeds up to the new n continue to their long horizon and the family's cells run at seeds
  1-n.

**Thresholds when armed.**
- **Advance:** BH-adjusted one-sided p ≤ 0.10 within the family and mean g ≥ g0 / 2 = 0.15 pt
  (g0 = 0.3 pt, the MDE target n is sized for), or g_res / 2 if Kai bought g_res. G3′ cells ask the
  non-inferiority question instead (Selection rule). "The wave's no": no cell advances in either
  family ("no entry resolved at g0 in this family"). A "contradicted" call needs the BH-adjusted
  one-sided p in the opposite direction ≤ 0.10.
- **Multiplicity** ([D9], tightening): BH m fixed at the `delta.json` counts, 19 at 350k (the 12
  accuracy cells on A and the 7 floor-family cells) and 43 at 5M (`screen_power.py`); it differs
  from the family test's m because BH treats every counted entry. Cells counted in m that do not run
  (X1, X2, X4, X5) enter with p = 1; a cell that runs later under a dated amendment is tested at the
  fixed first-discovery threshold q / m and never reopens this wave's decisions. Placebos are not in
  m.
