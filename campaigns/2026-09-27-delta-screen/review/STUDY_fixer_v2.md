# STUDY fixer v2: 2026-09-27-delta-screen (Delta wave 2)

Fixer, fresh context, 2026-09-27. Input: `review/STUDY_arbiter_v2.md` (ITERATE, iteration 2; 6 A,
10 B, fix list 1-12, "what Kai must decide"), `review/STUDY_fixer_v1.md`, the v2 panel files and
scripts, anchor STUDY at 96b95f2, `.claude/memory/decisions.md` top entry (Kai, 2026-09-27),
and, from the coordinator mid-task, `campaigns/2026-09-26-delta/code/GATES.md` §6 (verified
there). STUDY.md is edited in place with a v3 change-log entry (l. 61-93); there is no regression
ticket, so there is no new artifact version. Line numbers are STUDY.md after this pass (1,360 lines).

Kai's answers are applied as decisions, not defaults. (1) Launch gate 1 is the anchor's regime-B
pilot epoch-500 validation readout, which overrides [DK4]'s "does not wait". (2) [DK6]: mean g is
primary with a family-pooled spread, and LCB80 is shown beside it. Both were verified in the
`decisions.md` top entry. New defaults, each "default, Kai may override": [DK13] regime B,
[DK14] split-half as a second companion, [DK15] M023 goes to `mulder` whatever G3′ reads.

Scripts run (design arithmetic, nothing quotable):
- `python3 screen_null.py` (v2, sections 4-13 added): sections 1-3 reproduce the v1 output digit
  for digit, and a second full run is identical. The quoted rows are below.
- `python3 budget.py` (v3, regime-B basis 136.5 s per E epoch at K = 6, anchor l. 1453-1457,
  arithmetic; per-slot 22.75 pod-s; planning K_E = 4). At (4, 4): 302 runs, 176,000 run-epochs,
  1,112.2 / 1,959.0 pod-hours at r = 1 / 2, replica gate 12.6 / 19.0 h, and 5.4 / 9.2 d at P = 10.
  Packable today (without M006, M047-M049, P-T1, P-T2) it is 268 runs, 156,000 run-epochs,
  985.8 / 1,744.2 pod-hours and 4.9 / 8.4 d. The K_E = 5 row has the same pod-hours and gate
  15.8 h. The cheap version is 129 runs, 79,500 run-epochs, 502.4 / 853.1 pod-hours, 2.8 / 4.5 d.
- `python3 rank_sim.py`: unchanged output.
- `python3 tools/prose_lint.py STUDY.md`: score 0, reads human (19,839 words).

Family test, achieved P(false "yes") per family at n = 4 (`screen_null.py` §4). m = 12 / 40, for
R0 = the v2 rule (replica-referenced, pooled), R1 = placebo-referenced pooled, R2 = placebo-referenced
own sd (chosen) and R3 = pooled plus homogeneity gate falling back to own sd:

| scenario | R0 | R1 | R2 (chosen) | R3 |
| --- | --- | --- | --- | --- |
| equal spread | 0.101 / 0.101 | 0.100 / 0.101 | 0.102 / 0.099 | 0.102 / 0.101 |
| one cell 3× run sd | 0.150 / 0.157 | 0.151 / 0.162 | 0.105 / 0.102 | 0.143 / 0.141 |
| 25 % of cells 2× | 0.142 / 0.198 | 0.139 / 0.193 | 0.107 / 0.105 | 0.141 / 0.152 |
| 25 % of cells 3× | 0.198 / 0.325 | 0.199 / 0.321 | 0.111 / 0.108 | 0.156 / 0.134 |
| two-mode q 0.1 / 0.33 / 0.5 | 0.359 / 0.172 / 0.082 ; 0.549 / 0.199 / 0.060 | ≈ R0 | 0.053 / 0.038 / 0.042 ; 0.050 / 0.089 / 0.062 | 0.198 / 0.170 / 0.083 ; 0.412 / 0.200 / 0.059 |
| offset 0.5 / 0.707 SE | 0.233 / 0.299 ; 0.235 / 0.306 | 0.101 / 0.099 ; 0.096 / 0.100 | 0.103 / 0.104 ; 0.100 / 0.099 | ≈ 0.10 |
| near-deterministic placebo | 0.097 / 0.097 | 0.094 / 0.095 | 0.098 / 0.098 | 0.097 / 0.096 |
| n = 3 (cheap, or after a loss) | – | – | 0.101-0.110 / 0.095-0.099 equal/unequal; two-mode 0.067-0.122 / 0.080-0.237 | – |
| bit-identical branch (d = g, own sd), no offset / 0.707 SE | – | – | 0.103 / 0.096 ; 0.261 / 0.258 | – |

The R2 critical values are 4.41 / 6.75 at n = 4, 6.95 / 12.98 at n = 3, and 4.28 / 6.59 at m = 11 / 37.
R2 names a true +1-pt cell with probability 0.204 / 0.046 / 0.022 at σ 0.6 / 1.5 / 3.14 pt
(m 12) and 0.074 / 0.015 / 0.007 (m 40). For R1 the figures are 0.507 / 0.104 / 0.040 and
0.378 / 0.055 / 0.019.

## Per finding (arbiter priority order)

```
1 (A; v2 #1, #2, #11; v1 #4d, #7, #9, #10) Regime B and Kai's launch timing — RESOLVED
  changed: frontmatter l. 6, 9 (code base = anchor regime-B bundle, the Delta series sits on
    77f1ca4e today and will be rebased; anchor pinned to 96b95f2); change log v3 l. 61-93 with the
    rewritten v2 amendment reason l. 37-42 (v2 [DK6] item l. 45-48); identical-across-runs l. 231-235 (was "trace every
    epoch" → regime B, [DK13]); Selection l. 661-684 (eligible = traced epochs only, 50 per cycle
    per committed anchor l. 1403-1410, 51 if the frozen bundle adds the epoch-0 trace per the
    decisions.md ml-engineer entry, PREFLIGHT prints the count; counters over traced epochs;
    model_best / [A6] per anchor l. 1415-1433; recovery freeze traced-only); companions l. 788-812;
    [L6] l. 1174-1181; launch gate 1 l. 388-401 (Kai's line quoted, regime-B pilot readout, about
    19 h after that pilot starts, a projection; overrides [DK4]); gate 5 l. 415-423 covers
    ebops_trace_every; gate 11 l. 456-460; gate 12 l. 461-463 (24 → about 27 pods); Reference
    rows l. 164-170 rewritten (regime-A vs regime-B pilot, 136.5-s row); Budget l. 922-988 (218 s
    → 136.5 s; 36.3 → 22.75 pod-s); packing stated once in [D16] l. 1085-1090 (see note (f));
    [DK4] l. 1101-1107, [DK11] l. 1125, [A3] l. 1147-1149, [L4], [DK13] l. 1133-1137; every anchor STUDY
    line citation re-mapped from dde5ca7/c2f5447 to 96b95f2 by a line-diff map (e.g. 750-862 →
    852-968, 1268-1272 → 1547-1551, c2f5447 1217-1222 → 1269-1274); the label note l. 1046-1051
    says "anchor [D15]" wherever the anchor's label is meant (C31)
  verified: budget.py v3 output above; anchor 96b95f2 l. 1393-1463, 1483, 1526-1545 read;
    decisions.md top entry read; grep for 218 / 36.3 / 181.7 / 25.2 h / 30.3 h / 8.6 d / 14.7 d /
    1,776 / 3,128 / 802.4 / 1,362 / "24 GPU" / dde5ca7 / c2f5447: only labelled historical copies
    remain (l. 168, 929, 933, 970-971, 1169, 1296)
  propagated: pod-hours 1,776.3 / 3,128.7 → 1,112.2 / 1,959.0; wall 8.6 / 14.7 d → 5.4 / 9.2 d;
    gate 25.2 / 30.3 h → 12.6 / 19.0 h; the whole Budget table (7 rows); cheap 802.4 / 1,362.5,
    4.6 / 7.4 d → 502.4 / 853.1, 2.8 / 4.5 d; placebo and replica-seed increments 40.4 / 60.6 →
    25.3 / 37.9; (4, 8) 2,866.3-5,308.7, 13.0-23.8 d → 1,794.7-3,324.0, 8.0-14.7 d; pods 24 → 27.
    The old values are replaced in 11 places in STUDY.md ([DK1], [DK2], [DK7], [DK11], n_5M row,
    Budget ×4, cheap, gate 12) and in the experiment-log stub (1 entry): 12 instances across 2
    files. Run counts and run-epochs are unchanged (302 / 176,000)
  neighbourhood: every "every epoch", "77f1ca4e", "K = 5", "eligible epoch" and anchor citation
    was grepped and checked; the Controls resume rule now says only regime-B pilot checkpoints
    can match (anchor l. 1641-1643)
  note (f): the first draft adopted the anchor's K = 5 rule for E. The generator engineer's
    GATES.md §6 (canary_k.py applies the 90 % rule to every class; planning E 4 / A07 3), relayed
    by the coordinator, reverses that: [D16] now uses one rule for every class, planning K_E = 4,
    with K_E = 5 as the alternative row, and says once why the Delta does not copy the anchor
    (Budget "Arms per pod" l. 975-988)

2 (A; v2 #3, #4, #8, #16; phys B2, B4; crit C3) Family test calibration — RESOLVED
  changed: screen_null.py §4-§6, §13 (scenario rows as the arbiter listed, for four rules; n = 3;
    bit-identical branch; pooled-interval coverage). STUDY: the family test is placebo-referenced
    with each cell's own sd, rule (a) of fix 2(iii), l. 743-766, with the table of achieved rates
    and the power cost. Families are defined once, l. 722-734 (BH m 19 / 43; test m 11 / ≤ 37,
    with the long-horizon cells, Welch, hash-failed, incomplete-pairs, baselines and probes
    outside; C3, C24). The ranking interval uses the simulated multiplier 2.18 / 2.15 instead of
    the df claim (nominal t covers 0.934 / 0.932, §6), l. 735-742. "By construction" is deleted
    from Null (l. 134-140), the box (l. 99-116), Falsifier (l. 856-865), [DK7] and the stub, and
    each "0.90" now carries the achieved rates. The cheap version at n = 3 is labelled "not
    calibrated under two-mode seeds" (l. 990-999)
  verified: screen_null.py run twice with identical output; the table above. Choice made on the
    evidence: R2 is the only rule whose rate stays within 0.099-0.111 in every equal and unequal
    row at n = 4 and 0.038-0.089 under two-mode seeds; R3 reaches 0.13-0.16 and 0.41, so option (b)
    is rejected. Its cost is power: 0.204 against 0.507 at σ 0.6, m 12. This is printed in the box
    and in [DK7]
  propagated: critical values 2.41 / 2.79 → 4.41 / 6.75 (Selection, stub); "P(no | null) 0.90 by
    construction" → achieved rates (Null, box, Falsifier, [DK7], stub); P(no | +1 pt) 0.49 / 0.85 /
    0.88 → P(true cell named) 0.204 / 0.046 / 0.022 (box, Falsifier, stub). That is 9 instances
    across 2 files (STUDY.md, experiment-log.md)
  neighbourhood: the unpaired companion, rank-move flag, placebo check and G3′ were all
    re-simulated with the same script; the old placebo flag (0.034 / 0.013 against the family
    critical value) was replaced because it was tied to the withdrawn pooled rule

3 (A; v2 #5) Placebo specification and determinism — RESOLVED
  changed: Arms l. 190-210 (mechanism: the replica config with only `name` changed. No no-op key
    exists and the strict validator refuses unknown keys. BNJ_STAGE is a closed set,
    wandb_util.run_stage. `name` enters digest_json(cfg) at ablation.py:35, 623, the W&B id at
    :658-659 and the Keras model name at monolith.py:261, 288, but not the seed. The PREFLIGHT
    assertion: equal digest without name, equal init kernel_hashes, equal first-step CPU loss,
    listed under X2/Z13, l. 338-345). Determinism probe in launch gate 7, l. 425-437, cites
    ablation.py:597, train.py:261 and evaluate_roc.py:115. Both outcomes are pre-registered in
    l. 767-787: bit-identical means d = g with the no-offset assumption and its rates (0.103 / 0.096,
    or 0.261 / 0.258 at 0.707 SE), divergent means divergence printed and placebo as reference.
    The placebo is excluded from s_pool in both. "Uniform under the null" (l. 207-208), the
    exact-zero "red flag" (l. 650-656) and the formula check (l. 890-896) are rewritten. The
    placebo check is now a two-sided own-sd t at 0.05 (false flag 0.050) with detectable offsets
    of 1.25 / 3.05 / 6.55 pt at P 0.5 and 1.85 / 4.55 / 9.55 pt at P 0.8 (§12), l. 881-889
  verified: grep in code/tree (above lines); screen_null.py §4, §12; the generated placebo
    configs diffed against the replicas (P-350-s1 vs REP-A-s1, P-5M-s1 vs REP-C-s1): they differ in
    `name`, `experiment.arm`, `delta_study.*`, `engram_study.question` and `train.epochs` (500 vs
    1,000 / 2,000), not in `name` alone, so the Arms mechanism, the X2 assertion and the cell-key
    class (3) now name exactly those keys (training reads only `engram_study.module` and the
    block's presence, ablation.py:171-175, 375, equal in both)
  propagated: none needed (new text)   neighbourhood: g_rep exact-zero wording kept (different
    configs, so exact zero is still anomalous there)

4 (A; v2 #6) Replica-side losses — RESOLVED
  changed: Controls l. 528-538. A lost replica or placebo seed lowers the family's n uniformly;
    the main list stands at n′; the critical value is re-simulated (n = 3: 6.95 / 12.98, almost no
    power); incomplete-pairs applies to cell-side losses only; seeds above n cannot substitute
  verified: screen_null.py §4 n = 3 rows   propagated: none needed
  neighbourhood: base-stability (> 1/4) and ⌈3n/4⌉ rules read together, no conflict at n = 4

5 (A; v2 #7; v1 #4a) G3′ power — RESOLVED
  changed: l. 708-721. The bound is the two-sided 95 % t-interval on own sd, df n_p − 1 (default,
    Kai may override; DELTA l. 844-845 is silent on the side). Power is printed from screen_null.py
    §7: 0.074 / 0.041 / 0.031 at σ 0.6 / 1.5 / 3.14 pt, and 0.137 / 0.080 / 0.062 one-sided. Power
    reaches 0.80 only at σ ≈ 0.10 pt. The label reads "non-inferiority not shown at this n", never
    "inferior". M023 goes to mulder regardless ([DK15], l. 1140-1142; "Where I am not sure" row)
  verified: §7 reproduces the arbiter's table (0.799 / 0.597 / 0.315 / 0.171 / 0.074 / 0.041 / 0.031)
  propagated: stub   neighbourhood: floor-family G3′ at 5M uses the same bound

6 (B; v2 #10; v1 #6) Ranking primary — RESOLVED (by Kai's decision)
  changed: change log l. 45-48; Ranking mode l. 735-742; [DK6] l. 1110-1112 ("Kai-decided
    2026-09-27, not a default"); "Where I am not sure" preamble and [DK6] row
  verified: decisions.md top entry quoted   propagated: stub

7 (B; v2 #9) Rank-move flag null rate — RESOLVED
  changed: l. 797-808. T is set from the observed primary-companion r via screen_null.py §8,
    targeting about 1 null flag per family. At 350k: T 3 / 5 / 6 at r ≥ 0.9 / 0.7-0.9 / 0.5-0.7.
    At 5M: T 10 / 15 at r ≥ 0.95 / 0.9-0.95. Below that range the flag is replaced by τ and the
    family goes to Kai. The v2 thresholds flagged 6.9-24.4 null cells at 5M
  verified: §8 table   propagated: "Where I am not sure" companion row

8 (B; v2 #12; v1 #19) [L1] — RESOLVED
  changed: [L1] l. 1151-1163. The long-horizon cells and their replicas are compared at 500 against
    their own H (n stated, "a count of order changes, not a test"). The anchor 500 vs 7,000 check
    is kept. Seed-rank persistence is labelled "not a test of [L1]"

9 (B; v2 #13) sd_rep usable count — RESOLVED
  changed: l. 500-507 (k_rep printed; ≤ 6 of 8 labelled, cannot by itself raise n); the ceiling
    false-pause / false-pass rates at 8 and 6 seeds, l. 609-612 (§10) (C21)

10 (B; v2 #14) Accuracy-vs-AUC consequence — RESOLVED
  changed: l. 827-830 (top 12 on one metric and outside it on the other → flagged to Kai)

11 (B; v2 #15) Pairing efficiency — RESOLVED
  changed: l. 831-842. ρ̂ with its null interval −0.32 / +0.33 (m 12) and −0.18 / +0.18 (m 40)
    from §9; the unpaired companion against 8 replica seeds (own-sd Welch max-t, critical values
    2.92 / 3.62, §11) is non-selecting; experiment-log l. 2277-2279 cited as archived, 3 seeds, a
    hint

12 (C, required) #17-#31 — RESOLVED
  0.81 wave-level (box, Null, Falsifier); m 43 vs 40 chance labelled (box, fidelity table); sd
  named in "contradicted" (l. 868-869); sd_rep ceiling rates (l. 609-612); significance mode "not
  expected to arm" (Question l. 127, Seeds l. 616); families once (l. 722-734); forest-plot
  per-cell thresholds or t, interval type and n_p (Conventions figures row); 0.19-pt lower bracket
  and the two-mode note (Reference l. 171, Seeds l. 616-622); power at the ceiling in the box; "cannot
  call a gap flat" declared as a conventions deviation (l. 1026 and the box); companion as a mean
  over the last k traced epochs was considered and not added, with the reason given (l. 810-812);
  "+1 / +3 pt are illustrations" (l. 635-639, box); "anchor [D15]" label note (l. 1049-1051)
```

Coordinator inputs (GATES.md §6, verified in the file): RESOLVED as text. The cell-key rule
(Cell configs, l. 211-222) admits the re-traced `zero_floor_ebops` (38 pairs; M001 171,526, not
343,053) and the always-on keys `experiment.collapse_stop` and `experiment.accumulator_metric`.
X5 (l. 370-380) and launch gate 13 (l. 464-469) cover M047, M048, M049, P-T1 and P-T2, which the
[A20] guard at `qat.py:667-669` refuses, and through them M027, M035 and M036. They are excluded
from the packs until a non-binary path passes the CPU gate. The code fix is not designed here.
The missing caches for M009, M038, M040 and M041 stay under gate 3. The "packable today" budget
row is in Budget, and a new "Where I am not sure" row records the design call.

Kai items the STUDY now presents, all as defaults he may override: [DK13] regime B; [DK14]
split-half companion; [DK15] M023 goes to mulder regardless; [DK7] for the record (own-sd
placebo-referenced max-t); the X5 non-binary path (a design call for the patches owner and Kai);
and [DK1]-[DK5], [DK8]-[DK12] carried over.

No CANNOT RESOLVE. Nothing needs a Nautilus job or a mulder run to close these findings.

Record and outward copies for Kai: none. `grep -rln` over every `*.md` in the repo (excluding
review/, archive/, research/, publication*, sessions/) for 1,776.3, 3,128.7, "8.6 / 14.7", "2.41
at m", "Dunnett" and "delta-screen" finds only INDEX.md and index-head.md (title rows, regenerated
by `tools/index.py build`), decisions.md (Kai's entry, unchanged), and two plan/code notes in
campaigns/2026-09-26-delta that name the campaign but quote no number. The experiment-log stub was
rewritten in place.
