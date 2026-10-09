# STUDY fixer v1: 2026-09-27-delta-screen (Delta wave 2)

Fixer, fresh context, 2026-09-27. Input: `review/STUDY_arbiter_v1.md` (ITERATE; 4 A, 19 B, C items
#24-#32, "what Kai must decide" 1-12). STUDY.md is edited in place with a v2 change-log entry (no
regression ticket, so no new artifact version). Line numbers below are STUDY.md after this pass.
The orchestrator's defaults for the Kai items are written as [DK1]-[DK12], each "default, Kai may
override at the launch gate", listed under "Where I am not sure" → "Defaults Kai may override".

Scripts run (design arithmetic, nothing quotable):
- `python3 budget.py` (v2): (4, 4) 302 runs, 176,000 run-epochs (E 42,000 / A07 134,000),
  1,776.3 / 3,128.7 pod-hours at r = 1 / 2, 8.6 / 14.7 d at P = 10, 318 certification readouts;
  cheap 129 runs, 79,500 run-epochs, 802.4 / 1,362.5 pod-hours, 4.6 / 7.4 d. Every Budget row in
  STUDY.md l. 667-757 copied from this output.
- `python3 screen_null.py` (new): arbiter-v1 placebo wording P(no | null) 0.076 (m 12), 0.023
  (m 40); Dunnett-type critical t (one-sided α 0.10) 2.410 / 2.337 / 2.304 (m 12, n 4 / 6 / 8),
  2.793 / 2.680 / 2.651 (m 40); P(no | null) 0.896-0.904; placebo false-flag 0.034 (m 12), 0.013
  (m 40) at n = 4; recovery grid → ceiling 1.3 pt (5M criterion), 2.7 pt (350k criterion).
- `python3 rank_sim.py` (copied from `review/`): reproduces the constructive table (mean / LCB80
  rank, 3 true effects, top 12 of 43).
- `python3 review/two_stage.py`: one-stage / two-stage 0.99 / 0.89, 0.39 / 0.28, 0.69 / 0.48.
- `python3 tools/prose_lint.py STUDY.md`: score 0, reads human (14,612 words).

## Per finding

```
1 Ranking-mode "no" cannot fire under the null (A) — RESOLVED (deviates from the arbiter's wording; see note)
  changed: STUDY l. 89-97 (Null), 632-640 (Falsifier "no"), 575-583 (Ranking mode, family test),
    142-151 (placebo arms P-350, P-5M), 649-659 (placebo validity check (iv)); Figures row (forest
    plot placebo row + Dunnett line); budget.py placebos(); new screen_null.py
  verified: screen_null.py — the arbiter's literal wording ("no cell's LCB80 / mean g exceeds the
    placebo's") gives P(no | null) = 1/(m+1): 0.076 at m = 12, 0.023 at m = 40, worse than v1's
    0.043, because the placebo is one of m+1 exchangeable null draws. Implemented instead: family
    "no" = no cell's t above the Dunnett-type one-sided α 0.10 critical value (pooled paired sd,
    shared-replica null simulated): P(no | null) 0.896-0.904 at m 12 / 40, n 4-8. Power stated
    (P(no | one +1-pt cell) 0.49 / 0.85 / 0.88 at σ 0.6 / 1.5 / 3.14, m 12). Placebos run exactly as
    specified (seeds 1-n, H 500, not in m, never in the replica's pod) and serve as null row, rank
    check and validity flag. Cost +8 runs, +4,000 run-epochs, +40.4 / +60.6 pod-hours.
  propagated: runs 286 → 302 (8 placebos + 8 replica seeds), Budget tables, Counts l. 242-247,
    certification count, Where-I-am-not-sure rows, experiment-log stub; 4 old-number instances
    replaced across 3 files (STUDY.md, experiment-log.md, budget.py); the only remaining "286" is
    the labelled v1 comparison at STUDY l. 720
  neighbourhood: cheap version given the same placebos and "no" (l. 735-749); the per-cell
    "contradicted" list checked (finding 20); the "formula check" (C28) rewritten on the placebo
  remains: the arbiter should confirm the Dunnett line replaces its wording (flagged [DK7])

2 Winner's curse, selection = readout split (A) — RESOLVED
  changed: l. 593-603 (companion readout: last feasible, non-degenerate epoch ≤ H from per-epoch
    logs, own paired interval and rank; eligible-epoch count; Kendall τ; flag at > 5 places (5M),
    > 3 (350k) or across rank 12, flagged cells to Kai; split-half offered as an option);
    l. 885-891 [L6] rewritten naming M018-M020, M028, M029, M032, M034, M008, M011-M013;
    readout list l. 608-617 carries n_p, eligible count, companion value
  verified: text check against arbiter fix 2 (a)-(d); no number involved
  propagated: none needed   neighbourhood: companion uncertified status stated in certification
    paragraph (l. 751-757)

3 Resolving power at the measured spread, stop line (A) — RESOLVED
  changed: l. 502-527 (half-width table adds sd_d 4.44 → ±7.1 pt; ranking-fidelity table from
    rank_sim.py vs chance 0.018); l. 485-493 (sd_rep ceiling 1.3 pt, source, four options, pause
    before launch; guard sentence corrected); [DK8]; box l. 62-73
  verified: t(0.975,3)/2·√2·3.14 = 7.066; C(12,3)/C(43,3) = 0.0178; screen_null.py recovery at
    5M: 0.53 at σ 1.3, 0.48 at 1.4 → ceiling 1.3 pt (350k criterion would give 2.7; stricter used)
  propagated: ceiling in Falsifier (v), [DK8], experiment-log stub   neighbourhood: all four
    sd_d rows recomputed (0.48, 1.35, 7.1)

4 DELTA departures without dated amendments (A; incl. #23) — RESOLVED
  changed: change log l. 16-56 lists every amendment (§5.1 sd source, §5.2 n may rise, §5.1/§5.2
    control, §7 2a start and §6.3, §7 ordering, §5.3 ranking statistic, ranking-mode "no") and
    every restoration; (a) G3′ l. 568-572; (b) ⌈3n/4⌉ rule with four consequences and the
    "stable but < 3 feasible" case l. 408-418, launch gate 1 l. 307-316; (c) sd source amendment,
    "as written in DELTA §5.1" deleted; (d) wave-2a condition amendment, launch gate 1 and [DK4];
    (e) cap l. 591-592; (f) R1 l. 292-298; (g) 2a/2b order launch gate 10; (h) K6 and teachers as
    K2 items l. 256-258, 299-300, [D13], [DK9]
  verified: grep "G3′", "⌈3n/4⌉", "R1", "Cap", "K6" in STUDY.md, each present; "as written in DELTA"
    appears only in the change log's note of its deletion
  propagated: experiment-log stub   neighbourhood: DELTA §3.3 R2 fallback-C text re-read; FF2
    re-base carried forward (wave 3)

5 Missing-pair / survivor rule (B) — RESOLVED
  changed: l. 550-557 (g over seeds usable in both, n_p ≥ 3, n_p printed, incomplete-pairs list
    with survivor mean and the anchor's surviving-minimum imputation labelled); [D10]
  verified: text against DELTA §5.3 l. 772, 813   propagated: none   neighbourhood: G2 k_e
    definition unchanged; lists item (3) l. 584-590

6 Ranking statistic (B) — RESOLVED (default [DK6])
  changed: l. 575-583 mean g primary with family-pooled paired sd; LCB80 descriptive, its rank
    printed; DELTA §5.3 amendment flagged; [DK6]
  verified: rank_sim.py rows (mean ≥ LCB80 in every row)   propagated: question, stub
  neighbourhood: Cap text no longer says "by the lower 80 % bound"

7 E packing at K = 6 breaks the 90 % rule (B) — RESOLVED
  changed: launch gate 7 l. 334-343; Arms per pod l. 725-733; [D16], [DK11]; timing label
    l. 690-700 ("assumes a GPU-throughput-bound per-slot cost of 218 / 6 s; K = 3, 4 and 5 are not
    measured"); budget.py planning K_E = 5 with per-slot cost unchanged
  verified: 6 × 4,354 = 26,124 MiB > 23,028; 5 × 4,354 = 21,770 = 94.5 % > 90 % (20,725), so the
    orchestrator's K = 5 default is recorded with the note that the canary is expected to give
    K = 4 on an A10; budget.py rerun (wall clock 8.6 / 14.7 d)
  propagated: pod-hours unchanged in basis; wall-clock rows regenerated   neighbourhood: A07 K = 3
    fallback (C24) added

8 Always-on patches not in X2 (B) — RESOLVED
  changed: X2 l. 276-281; launch gate 9   verified: code/README.md l. 42-48, delta.json
    always_on_diagnostics   propagated: none   neighbourhood: replicas and placebos included

9 Anchor config not frozen (B) — RESOLVED (default [DK4])
  changed: frontmatter code_sha; launch gate 11 (relabel rule "rep-A / rep-C at config sha X");
    [DK4]   verified: text   propagated: stub   neighbourhood: g_rep wording in Controls

10 Anchor state stale (B) — RESOLVED
  changed: Reference rows l. 118-123 (A07-350-s1 in the K = 3 pilot pod, 1115121; C-s1 scheduled
    there; C′-s1 293.6 s/epoch indication; 4,354 MiB per process); frontmatter says which sha each
    citation uses (dde5ca7 default, c2f5447 / e620173 where stated); collapse label in the readout
    l. 612-615 (anchor STUDY c2f5447 l. 1217-1222); timing basis l. 690-700
  verified: `git show c2f5447:…/STUDY.md` l. 1217-1222, 1374-1392; `git show e620173:…/RUN.md`
    l. 162, 216, 232, 246-247 — each quoted fact found at the cited line
  propagated: none   neighbourhood: [A3] pod count now cites the anchor's K = 3 pod count

11 Question wording vs rule (B) — RESOLVED
  changed: frontmatter question; l. 75-88; one-line version l. 58-60   verified: text matches the
    advance rule l. 573-574   propagated: experiment-log Question line rewritten in place

12 Floor-family package in the advance family (B) — RESOLVED
  changed: l. 224-227, 584-590 (separate "cross-architecture package" list, Welch, SE note, BH m 19
    kept as a tightening)   propagated: none   neighbourhood: confound 13 updated

13 Floor-family feasibility by construction (B) — RESOLVED
  changed: G2 in l. 558-567 (traced headroom and h beside k_e and k_base; "structural, by
    construction" label); readout list   propagated: none

14 Baseline tuning asymmetry (B) — RESOLVED   changed: Bearing l. 98-108   propagated: none

15 Per-class AUC missing from readout (B) — RESOLVED   changed: readout l. 608-609
   neighbourhood: conventions rows 505/508 now consistent

16 Cheap version's long cells uncontrolled (B) — RESOLVED
  changed: l. 735-749; budget.py cheap() rep-A 1,000, rep-C 2,000, placebos
  verified: budget.py cheap: 129 runs, 79,500 run-epochs (70,500 + 6,000 + 3,000), 802.4 / 1,362.5
    pod-hours, 4.6 / 7.4 d   propagated: [DK1] row, stub (2 instances)

17 [D14] has no limitation (B) — RESOLVED   changed: [L7] l. 892-895; [DK10]

18 Conventions rows (B) — RESOLVED
  changed: Selection-under-a-budget row marked as a deviation; check 3 "probably unavailable" with
    stand-ins; Pitfalls rows for both conventions files; Figures row   verified: conventions
    l. 31 and both Pitfalls sections read

19 [L1] accepted without attempt (B) — RESOLVED   changed: [L1] l. 872-877 (rep-A 500 → 1,000,
    rep-C 500 → 1,000 → 2,000 seed-rank persistence; epoch-500 vs 7,000 across anchor arms when
    [A6] snapshots exist)

20 "Contradicted" list without null count (B) — RESOLVED   changed: l. 641-648 (0.025 · m = 0.5
    at 350k, 1.1 at 5M, overdispersed)   verified: rank_sim.py prints 0.48 / 1.07

21 Replica seeds 1-8 option (B) — RESOLVED (adopted as default [DK2])
  changed: replicas table l. 228-240; Seeds l. 468-493; [DK2] row with +4,000 run-epochs, +40.4 /
    +60.6 pod-hours, no wall-clock change; v1's "conflicts with replicas first" removed
  verified: budget.py with extra_to = 4 vs 8: wall clock 8.62 / 14.72 d both   propagated: runs,
    Budget, stub

22 Binomial-SE argument (B) — RESOLVED   changed: l. 495-501 (3.14 pt and 0.6 pt arguments; the
    old argument withdrawn with its reason)

23 K6 and teachers as Kai items (B) — RESOLVED (folded into 4; defaults [DK9])
```

C items (#24-#32), all applied: C24 A07 fallback sentence (launch gate 7); C25 moot (branch S
removed; [L3] rewritten); C26 always replica-primary ([DK3]); C27 certification count 318 from
`budget.py`; C28 formula check rewritten on the placebo (l. 660-664 and l. 520-527); C29 confound 8
list (M016, M017-M026); C30 teacher leakage note in X1; C31 baselines out of the ranked list,
M010 pairing purpose (l. 137-141); C32 coverage-not-resolution framing, two-target sign
concordance and accuracy/AUC rank concordance (readout), prior-art note (Where I am not sure),
two-stage result in `plan.md` dead ends, "can and cannot say" box (l. 62-73). C8 one-line
question and null (l. 58-60).

## Kai items

All twelve are written as [DK1]-[DK12] defaults (STUDY "Where I am not sure" → "Defaults Kai may
override"), each with its cost from `budget.py`.

## CANNOT RESOLVE

None. No finding needs a cluster job. Two items the orchestrator or arbiter should see:
- Finding 1 departs from the arbiter's literal wording for the ranking-mode "no", for the reason
  and numbers above ([DK7]).
- The orchestrator's K = 5 E default conflicts with the STUDY's 90 % rule at the anchor's
  measured footprint on an A10 (94.5 %); kept as the planning value with the canary deciding.

## Record or outward copies for Kai

None. `INDEX.md` and `.claude/memory/index-head.md` carry only the title (regenerated by
`tools/index.py build`); no README, `RESEARCH.md` row or `messages/` draft quotes this campaign.
