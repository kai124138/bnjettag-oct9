# STUDY arbiter v4: 2026-09-27-delta-screen (Delta wave 2)

Arbiter, fresh context, 2026-09-27. Re-review, iteration n = 4.
Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (1,681 lines, working tree after fixer v3,
commit 0b11518) with `plan.md`, `budget.py` (v4), `screen_null.py` (§1-§17), `rank_sim.py`,
`research/screen-design-literature.md`. Inputs read: `review/STUDY_physics_v4.md` (+
`physics_v4_twomode.py`), `review/STUDY_critical_v4.md`, `review/STUDY_constructive_v4.md` (+
`constructive_v4_modes.py`), `review/STUDY_validators_v4.txt`, `review/STUDY_arbiter_v3.md`,
`review/STUDY_fixer_v3.md`, `docs/methodology/06-review.md` §6.1-§6.8, `.claude/memory/decisions.md`
top entries, `campaigns/2026-09-26-delta/delta.json` (pairing fields). No plot-validator file
(STUDY has no figures).

**§6.5 warning, iteration 4.** This is the fourth panel iteration. The fixer's pass produces
iteration 5, where the panel tier warns strongly. The fix list below is built to be closed in
one pass. It **removes more rules than it adds**: the compute pause, its default, its three
budget rows, its four options and a Falsifier item go. One estimator, one simulation block and
one readout line come in. Since v2, each round's added machinery has produced the next round's
B items, so simplification is the priority.

## Validator lines

`STUDY_validators_v4.txt`: no mechanical STUDY validator exists. `prose_lint` on STUDY.md scores
0, "reads human" (24,788 words). No line is A-marked, so nothing becomes Category A by the
validator rule. No plot-validator file exists at STUDY.

## Independent checks (arbiter)

- **`screen_null.py` re-run** (`uv run --with numpy,scipy`, seed 20260927, 9.7 s). §13: 4.284 /
  6.585 (n 4) and 6.733 / 12.290 (n 3). §14: P(pause) 0.000 / 0.106 / 0.629 / 0.889 / 0.991
  (8 seeds). §15: false "yes" 0.099-0.108 (equal / unequal spread), two-mode 0.036-0.082 at
  n 4; power 0.214 / 0.087 / 0.051 / 0.026 (m 11) and 0.077 / 0.030 / 0.016 / 0.007 (m 37);
  multipliers 2.168 / 2.136. Recovery 5M 0.57 at 1.3 pt and 0.52 at 1.4 pt; 350k 0.50 at 3.0 pt.
  §16: 0.77 → 0.87 and 0.57 → 0.69 (5M). §17: 0.038 / 0.121 / 0.104 and 0.312 / 0.738 / 0.948.
  All of these match the STUDY and all three reviewers.
- **`budget.py` re-run.** (4, 4): 302 runs, 176,000 run-epochs, 1,112.2 / 1,959.0 pod-hours,
  318 certifications. Packable today: 240 (212 + 8 + 20 + 0), 142,000 run-epochs. Extension:
  390 runs in both families. Pause: 286 / 270 / 254 runs. [DK18]: 84 runs, 366.5 pod-hours.
  All match.
- **Reviewer scripts re-run.** `physics_v4_twomode.py` gives per-run-mode recovery 0.284 /
  0.193 / 0.140 against 1.000 seed-shared, at q 0.1 / 0.33 / 0.5. `constructive_v4_modes.py`:
  in both mechanisms P(pause) is 0.96 and median sd_rep is 2.67 pt. Recovery is 1.00 (shared)
  and 0.19 (independent), and the median interaction sd is 0.30 / 2.57 pt. In the Gaussian
  rows the interaction sd equals σ√(1 − ρ) at every ρ. Both reviewers' numbers reproduce.
- **Arbiter simulation, 5M** (scratch, seeded 20260927, design arithmetic, not quotable).
  Setup: per-run two-mode seeds (jump 5.4 pt, within-mode sd 0.3 pt), m 37, three +1-pt cells,
  top 12, n 4, s_int = the two-way cell × seed residual sd. The last column is recovery for
  families whose s_int is at most 1.3:

  | q | per-run sd | median s_int | recovery | recovery when s_int ≤ 1.3 |
  | --- | --- | --- | --- | --- |
  | 0.02 | 0.81 pt | 0.81 pt | 0.78 | 0.78 |
  | 0.05 | 1.21 pt | 1.20 pt | 0.55 | 0.61 |
  | 0.10 | 1.65 pt | 1.64 pt | 0.28 | 0.55 |

  At a matched sd the Gaussian §15 rows give 0.92 (0.8 pt) and 0.63 (1.2 pt), so two-mode seeds
  cost recovery at the same sd (phys B2 holds). A 5M label at s_int ≤ 1.3 still meets the
  ≥ 0.5 criterion in these rows.
- **Arbiter simulation, 350k** (m 11, one +1-pt cell in the top 3, same seed model).
  - At q 0.33 / 0.5, median s_int is 2.56 / 2.72 pt and recovery is 0.48 / 0.45. That is below
    0.5 while s_int is below the 3.0-pt Gaussian criterion.
  - So the 350k Gaussian criterion does not hold under per-run two-mode seeds. This bears on
    phys C4 and is folded into fix 2.
- **Crit B1 checked against `delta.json`.** M006 "unpaired (Welch): no shared attention tensors";
  M009 "unpaired (Welch): different inputs; crosses N by design, labelled"; M046 "paired if [A17]
  shows only pos_table differs, else Welch". The STUDY's own Arms table (l. 321, 324, 360)
  carries the same pairing. The 5M ranked list is defined at l. 899-901 as "the paired
  single-lever list … m ≤ 37", and l. 904-905 puts Welch cells outside it. The paired bound is
  therefore 35, or 34 if M046's [A17] check fails. Confirmed.
- **Pause cost (crit B2, cons B1).** From `budget.py`, the pause saves 16 runs (350k), 32 runs
  (5M) or 48 runs (both) of 302. In pod-hours that is 50.5 / 101.1 / 151.6 at r = 1 (1,112.2
  against 1,061.7 / 1,011.1 / 960.6). The gate's effect is on labels, not on compute.
- **Grep for the cascade** (`pause|ceiling|DK17|DK8|paused|branch taken only if`). Hits:
  - STUDY l. 6, 32, 56, 126-128, 158-163, 176-177, 391-393, 595-597, 710, 734-767, 769-779,
    946-947, 1083-1084, 1105, 1115-1117, 1161-1163, 1220-1221, 1292-1294, 1347-1348, 1375-1377,
    1409, 1448-1453, 1511-1516, 1573, 1583-1594, 1621-1622, 1666.
  - `plan.md` l. 73, 84, 114, 119, 122, 128-129, 153.
  - `budget.py` l. 39, 63-78, 184-185, 247-253.
  - `screen_null.py` l. 2, 19, 40, 51-57, 134, 234, 270.
  - Experiment-log stub l. 12.
  - Not part of this cascade: l. 517 (A07 memory pause) and l. 618 (base-stability pause) are
    different rules and stay.

## Adjudication of v4 findings

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | The pause / "descriptive" label / [DK16] band read sd_rep, the total across-seed sd of the replica. The ranking orders cell means, so any seed-level term shared at seed s (and the replica's per-seed noise) cancels. What limits the ranking is the cell × seed interaction, σ√(1 − ρ). At the archived two-mode spread the gate pauses with P ≈ 0.96 in two cases with recovery 1.00 and 0.19 | phys B1 / cons B1 (merged, as instructed) | B / B | **B** | Case 1 on the finding, Case 2 on the estimator. Physics proposes s_pool ≤ √2 · 1.3. Constructive proposes s_int, the two-way residual sd of the family's cell accuracy matrix. **Sided with s_int.** The order of the means depends only on the cell × seed interaction, and s_int measures exactly that (df (m − 1)(n − 1) = 30 / 108 at m 11 / 37, the design grid; against 7). It is what `screen_null.py` §15 simulated at ρ = 0, where σ is the interaction sd, so thresholds carry over with no √2 conversion. s_pool also contains the replica's per-seed noise, which the order never sees. Physics' side-by-side print is kept, with s_int added. Reproduced (Independent checks) |
| 2 | Ranking fidelity, the extension rows and the ceiling are simulated with Gaussian seeds only. The only measured spread is two-mode, and at matched sd two-mode seeds cost about a third of the recovery | phys B2 | B | **B** | Case 3, reproduced and extended. The arbiter's 350k rows show the Gaussian 3.0-pt criterion failing (0.45-0.48 at s_int 2.6-2.7). So after fix 1 the label thresholds must come from the stricter of the Gaussian and two-mode rows. Phys C4 (the per-family ceiling) is absorbed here |
| 3 | The floor-family G2 is posed as a live question (frontmatter l. 6, Question l. 189-196), but the Selection rule (l. 871-879) declares it not a finding for every traced entry. [DK17] keeps the floor family in the paused branch "so that the floor-family G2 answers exist" (l. 754-755, 1584-1585). M001 sits 0.5 EBOPs under the trigger | phys B3 / crit B3 / cons C3 | B / B / C | **B** | Case 2, sided with B: a pre-registered question that the design itself says has no informative answer is an internal contradiction in the question, and the question is the artifact's contract. The [DK17] half goes away with fix 1. The question rewrite stays. Cons C3's wording, "expected from floor arithmetic" rather than "by construction", is adopted in the same edit, since A07-350 itself has not produced a run (l. 232) |
| 4 | M006 and M009 (Welch by `delta.json`) sit inside the "paired" 5M ranked list. The paired bound is 35, not 37. M009 crossing N inside one ranked order is the "one series across N" pattern | crit B1 | B | **B** | Case 3, confirmed from `delta.json` and the Arms table (Independent checks). Same defect class as v3 #4 |
| 5 | The pause default is close to a full launch (36 of 44 5M cells and 20 of 23 at 350k run). The box, [DK8] and Falsifier (v) say "pauses before its cells launch". The Falsifier has no reading for the likely branch. l. 1056-1058 ("lists go to Kai at K3a") contradicts l. 758 ("not a K3a ranking") | crit B2 | B | **B** | Case 3, confirmed from `budget.py` (pause kept-cell lists) and the cited lines. Resolved mainly by fix 1: with no compute pause the family test is read in every family, and the list always reaches K3a with its label. The residual is the Falsifier / K3a text (fix 1(e)). The "cut m, priced" alternative is not required. With the pause gone the arbiter takes the critic's own second option, an explicit statement of what a "descriptive" list feeds, which the critic named as sufficient |
| 6 | "Mechanism not exercised" for M003, M007, M008, M011, M012 is inferred from rep-C, but these cells change the constraint the controller sees (M007 floor 474,125; M008 group weight 0.1 in the controller input) | crit B4 | B | **B** | Case 3. Confirmed at l. 438-439 (M007 floor) and l. 612-614. The fix applies the existing rule to each cell's own seeds, so no new machinery |
| 7 | A paused family reads no family test, although the own-sd max-t is calibrated at any σ and its inputs run anyway | cons B2 | B | **B**, closed by fix 1 | Case 3. Correct: the §15 rows are scale-invariant (0.099-0.108). With no compute pause and no "no test" branch, the test is read in every family. Fix 1 deletes l. 946-947 |
| 8 | Two-mode seeds are treated only as a calibration nuisance; a lever that moves seeds between modes is not separable from a within-mode shift in mean g at n = 4 | cons B3 | B | **B**, minimal fix | Case 3. Factually correct (one mode change moves a 4-seed mean by 5.4 / 4 = 1.35 pt). It stands at B under §6.5.1. The arbiter sets its fix scope: one pre-registered readout line (fix 6). Its last bullet ("is the low mode seed-shared") is answered by fix 1's side-by-side sd_rep / s_int / ρ̂. Within-mode g is not added (Dismissals) |
| 9 | Pairing "hint" from three 3-seed correlations is uninformative; call it "no information on ρ" | phys C1 | C | C | |
| 10 | Determinism probe does not cover pack composition; word check (iv)'s flag "pack-composition effect or nondeterminism, not separated" | phys C2 | C | C | Take the wording route, not a second probe |
| 11 | "Contradicted" null count uses BH m 19 / 43 while the ranked lists are 11 / 35 | phys C3 / crit C3 | C / C | C | Case 1. Use crit C3's form: "≤ 0.025 · (cells read)", printed at the read |
| 12 | 350k ceiling borrowed from 5M | phys C4 | C | absorbed into fix 2 | |
| 13 | Packable-today m (9 at 350k; ≤ 32 at 5M, where M006 and M009 are already among the five cells not packable today, so fix 4 does not lower it further) | phys C5 / crit C2 | C / C | C | Case 1. One sentence at l. 1175-1184; with crit C2, say either that top-k stays fixed at 16 / 6, or that it scales as the nearest integer to 16m/37 and 6m/11 at the actual m. Pick one |
| 14 | Constraint-rule thresholds 0.8 / 0.9 without rationale; β compared with 1e-10 without tolerance | crit C1 | C | C | |
| 15 | n_p used for two pair types (cell − replica, cell − placebo) | crit C4 | C | C | Use n_p and n_d |
| 16 | [L7] slack-form label lets a lever go to confirm without the 350k follow-up; name the decider | crit C5 | C | C | "Kai at K3" |
| 17 | Frontmatter `question:` is about 230 words | cons C1 | C | C, done with fix 3 | Put "In one line" (l. 145-147) in the frontmatter |
| 18 | Significance-mode machinery in the main line; move to an appendix | cons C2 | C | C, optional | Allowed if the fixer has budget; a move, not a rewrite. Not required for PASS |
| 19 | Record the init-vs-order factorial as the follow-up if a seed-shared low mode appears | cons C4 | C | C | One line in [L]-list or "Where I am not sure" |

None of the three reviewers raised a Category A, and the arbiter finds none. No B item is raised
to A. No finding is dismissed as a whole. The one partial dismissal (within-mode g, row 8) is
below with its three fields.

## Earlier A and B findings (arbiter v3), by name

| v3 # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 (B) | placebo "only `name`" | **resolved** | Question l. 181-182, change log l. 84-87 and [DK7] l. 1336-1340 all carry the key set and the assertion. Arms l. 269-272 has the assertion. The only "run name" left is the W&B run name at l. 267, which is correct (critic's grep; arbiter read l. 255-282) |
| 2 (B) | one family-test reference; probe scope | **resolved** | l. 920-921 "the family's placebo, in every case". Two readings of the placebo row only, l. 948-958. Probe per class (E, A07), two pods, 21 epochs, traced set named, l. 518-529. sd-0 rule at l. 1079-1081. 4.43 / 6.79 / 0.261 survive only in the change-log withdrawal line (l. 103-105) |
| 3 (B) | packable today 268 → 240 | **resolved** | `budget.py` re-run prints 240 (212 + 8 + 20 + 0), 142,000 run-epochs; STUDY l. 1179-1184 and [DK1] l. 1452. Gates 3 and 13 agree (l. 465-467, 490-494, 557-558) |
| 4 (B) | long-horizon cells out of the ranked list | **resolved as asked; residual is v4 #4** | l. 899-906, 911-912, 959-966, [L8] l. 1432-1435, Arms l. 280-282 agree; §13 / §15 re-simulated at m 11 / 37 and reproduced. The Welch-cell residual is v4 #4 |
| 5 (B) | rank-move r centred per cell | **resolved** | l. 985-989. T values 3 / 5 / 6 (350k) and 10 / 15 (5M) reproduced from the §15 null counts |
| 6 (B) | literature note | **resolved** | `research/screen-design-literature.md` exists and is cited with its owner at l. 1657-1681. Each of §1-§5 is applied or answered. Research-log lines are present (critic: `research-log.md` l. 23-39) |
| 7 (B) | floor-family null rate, numeric trigger | **resolved as asked; residual is v4 #3** | Rates at l. 189-193 and 867-871 reproduced (§17). Trigger 171,526.5 at l. 871-875. The question / [DK17] contradiction is v4 #3 |
| 8 (B) | 5M constraint-active readout | **resolved at family level; residual is v4 #6** | Controls l. 601-614, Falsifier (vi) l. 1084-1086, [L7] l. 1428-1431, [DK18] priced (84 runs reproduced) |
| 9 (B) | pause as a likely branch | **resolved as asked; superseded by v4 #1 / #5** | P(pause) printed (box l. 158-160, Seeds l. 745-748, reproduced); [DK17] default priced; 0.19-pt bracket labelled (l. 236, 775-777). Fix 1 withdraws the compute pause |
| 10 (B) | ranking-mode n rule | **resolved** | [DK16] l. 708-730, 1570-1581, with five limits; extension priced (390 runs, 1,390.3 / 2,439.3 pod-hours, reproduced) and recovery from §16 (reproduced). Fix 1 moves its band from sd_rep to s_int; the rule itself stays |
| 11-26 (C) | crit C1-C8, phys C1-C4, cons C1/C3/C5/C7/C8 | **applied** | Critic's table rows 11-26 cite a line for each. Arbiter spot checks: l. 142 → 0.023 attributed to the simulation (l. 206-208); "95 % at equal spread" l. 916; `plan.md` v1 tags (critic l. 18, 30, 36); 51-per-cycle l. 823-830 |

## Regression triggers (§6.7), each checked

| trigger | status | evidence |
| --- | --- | --- |
| selection on held-out, or changed after results | not met | validation only (l. 818-851, 1033-1034); no result exists. Fix 1 changes a labelling rule before any run, with a dated amendment |
| val AUC vs ROC-test AUC > 0.01 | not met | no ROC-test evaluation ([D5]) |
| single-seed / < 100-epoch / lab-pod headline against the record | not met | the screen is never quotable; the Reference table has no comparand (l. 224-239) |
| comparison across N, input sets, splits or schedules as one series | **pattern present in the design, no result; origin STUDY** | M009 (N = 32) inside the paired 5M ranked list (v4 #4). Origin phase is this STUDY and no result exists, so no earlier phase re-runs and no investigator is needed. Fixed in this iteration (fix 4), same treatment as v3 #4 |
| gap smaller than seed sd with < 3 seeds | not met | n ≥ 4; n_p ≥ 3 for any reading (l. 852-859) |
| reload outside 1e-7, TF32 on | not met | l. 677, 1257 |
| eBOPs not remeasured on the selected checkpoint | not met | certification l. 847-851 |
| binary layer with > 2 values | not met | conventions check 1, l. 1257 |
| DSP / C-sim / C-synthesis | not applicable | l. 1258 |
| per-class AUC < 0.7 hidden | not met | l. 1007-1009 |
| byte-identical arms / different y arrays | not met; watch | y_val sha asserted (l. 579-583); the placebo's bit-identical reading is pre-registered (l. 948-958), not hidden |
| failed validation without remediation; tautological comparison as validation | not met | nothing has run; the placebo check (iv) is read by a pre-registered rule |
| STUDY [D] label replaced without dated amendment | not met now; **watch in fix 1** | [D8] carries dated v2 / v4 amendments (l. 1292-1294). Fix 1 must amend [D8] and [DK8] with a dated v5 entry, and delete [DK17] with a change-log line saying so |
| outward numbers ≠ VERIFY | not applicable | none |
| suspiciously good | not applicable | no results |

No trigger requires an investigator or a `REGRESSION_TICKET.md`.

## §6.8 validation target

No binding comparand, correctly, for a never-quotable screen (Reference table l. 222-239). The
stand-ins for reproduction are the placebo, g_rep and the pilot context (l. 1250). They are
unchanged.

## Motivated reasoning

- **Re-keying the gate could read as "we moved the rule so the wave does not pause."** Checked,
  and it does not hold:
  - the pause saved at most 48 of 302 runs (151.6 of 1,112.2 pod-hours at r = 1), so it never
    protected compute;
  - the threshold values are not loosened, and fix 2 tightens the 350k one;
  - s_int is the quantity the recovery criterion was simulated on (ρ = 0);
  - a lever that changes mode probability inflates s_int, so the error runs toward
    "descriptive";
  - the change is made before any run, with a dated amendment.

  The arbiter's two-mode rows show that the label keeps its meaning: at 5M, recovery for
  s_int ≤ 1.3 is 0.78 / 0.61 / 0.55.
- **A 3.0-pt 350k criterion that holds only under Gaussian seeds** would label "ranked" a list
  whose recovery is 0.45-0.48 under the only seed structure ever measured. Fix 2.
- **"Structural, by construction" asked as a question.** The artifact poses G2 and disowns it
  in the same file. Fix 3.
- Checked and not found:
  - no interval is inflated (the ranking interval uses the simulated multiplier on paired
    seeds; the unpaired companion is labelled non-selecting);
  - no selection rule moved after results;
  - G3′ failure is not read as inferiority (l. 889-891);
  - the "no" is not claimed as absence (l. 929-930).

## Competing-group question

A group running this screen next month would have three things this STUDY lacks:
- a noise gate on the quantity that limits the ranking (fix 1);
- label thresholds that hold under the seed structure they measured (fix 2);
- a ranked list whose membership is stated once (fix 4).

Each is a text change or one simulation block. None needs a GPU, and none has a justification
for being absent.

## Disputed facts for the investigator

None. Every fact was settled from the artifact, `delta.json`, `budget.py`, `screen_null.py`, the
two reviewer scripts or the arbiter's seeded simulations. The line or path is cited above.

## Dismissals

| item | cost (agent-hours) | why the conclusion does not depend on it | when |
| --- | --- | --- | --- |
| Cons B3's "within-mode paired g beside mean g" | about 0.5 (text now, a few lines at VERIFY) | At n = 4 a within-mode mean rests on 1-3 seeds per mode, so its interval is undefined or df ≤ 1. It changes no list, test or label. The n_low count that fix 6 adds carries the mode information that n = 4 can support | at confirm (Delta wave 4, 8 seeds), where the confirm STUDY can pre-register it if n_low shows mode shifts here |
| Crit B2's "priced cut-m row with a simulation" | about 1 (a `budget.py` row and a §16-style block) | The row was an option inside the compute pause, which fix 1 withdraws. The critic offered an explicit statement of what a descriptive list feeds as an equal alternative, and fix 1(e) requires that statement | not planned; if Kai asks at the launch gate for a smaller m at more seeds, it is priced then |

## Verdict: **ITERATE** (iteration 4; the next pass is iteration 5, strong warning)

No Category A. Eight B items are open (rows 1-8; rows 5 and 7 close mainly through fix 1). All were verified
against the artifact, so none can be downgraded (§6.5.1). PASS needs no unresolved B, and a
fix without re-review is a process failure (§6.5). The C items do not need a re-review of their
own.

### Fix list for the `fixer`, in priority order

Add a **v5 change-log entry, dated 2026-09-27**. Make fix 1 a dated amendment of [D8] and [DK8],
and record that [DK17] is withdrawn. Every changed number or rule cascades to the grep sites
listed under Independent checks. Change-log entries v1-v4 (l. 17-143, including l. 32, 56, 126-128)
are not rewritten. Where they name a withdrawn rule, they get only an annotation of the form
already used at l. 89 ("withdrawn in v5"). The withdrawal itself is recorded in the v5 entry
(§6.6 audit trail).

**Rules the fixer may delete outright** (the deletion is the fix; no replacement text beyond
fix 1):
- the compute pause and "pauses before its cells launch" everywhere: box l. 158-163, Question
  l. 176-177, Seeds l. 745-765 (the "pause is a likely branch" and "on a pause" paragraphs),
  guard wording l. 766-767, Falsifier (v) l. 1083-1084;
- **[DK17]** entirely: the Decision-labels bullet l. 1375-1377 and the DECISION block
  l. 1583-1594;
- the four pause options (cut m, raise n, cheap version, feasibility only) at l. 763-765 and in
  the [DK17] block;
- the three pause budget rows, l. 1115-1117 and 1161-1163; the Counts sentence "with both
  families paused ([DK17]): 254" (l. 393); `budget.py`'s `pause_keep`, the `paused=` parameter
  and the "[DK17] pause default" block (l. 39, 63-78, 184-185, 247-253);
- the false-pause / false-pass sentence at l. 741-744 and every citation of `screen_null.py`
  §10 and §14; §10 and §14 may be deleted from the script;
- l. 946-947 ("A family paused at the ceiling reads no family test");
- "(4, 4) is the branch taken only if both families pass the ceiling" (l. 128, 162-163,
  391-392, 779, 1105, 1450-1451, 1621-1622): (4, 4) becomes the design;
- `plan.md` l. 114 ([DK17] clause) and l. 122 (the P(pause) line), tagged superseded as for v1.

Do **not** delete the A07 memory pause (l. 517) or the base-stability pause (l. 618). They are
different rules.

1. **(B, v4 #1 + #5 + #7) Labels read the interaction sd at the n = 4 readout; sd_rep
   decides no ranking-mode question.**
   (a) sd_rep keeps one role: the significance-mode seed rule (l. 695-707, DELTA §5.1 input).
   It is still printed before any cell launches. It no longer sets a ceiling, a pause, a label
   or the [DK16] band. Rewrite l. 595-597 and 734-744 to say so. [DK2]'s reason (l. 1319-1321)
   becomes: the df-7 seed-rule input, plus the replica partners at seeds 5-8 for the extension.
   (b) Define **s_int**, fixed now: the residual sd of the two-way (cell, seed) decomposition of
   the family's ranked-list validation accuracy matrix. Use only cells with complete pairs;
   placebo and replica are excluded. df = (m − 1)(n − 1). It reads no effect size and no cell
   order. Print sd_rep, s_int, s_pool and ρ̂ side by side in every family header.
   (c) **Label rule:** if s_int ≤ the family's label threshold (fix 2), the list is labelled
   "ranked". Otherwise it is labelled "descriptive: recovery below 0.5 at this spread" and cites
   the recovery row at the measured s_int. The family test is read in every family, labelled or
   not, with the "a 'no' is not evidence of absence" sentence.
   (d) **[DK16] band read on s_int** at the same readout: s_int < 1.0 pt, n = 4; 1.0 ≤ s_int ≤
   the family's label threshold (fix 2), the top-k extension. Above it, no extension (constructive script:
   0.16 → 0.20 at 3.14 pt). The extension is already released after the n = 4 readout
   (l. 710-711, 1165), so this costs nothing in time.
   (e) Falsifier and K3a: in every family the ranked or descriptive list goes to Kai at K3a with
   its label, the winner's-curse note and the companion flags (keep l. 1056-1058; it is now
   true). Add one sentence on what a "descriptive" list can support at K3a: nomination with the
   label, never a resolved gap. The wave's "no" (l. 1047-1053) exists in every family.
   (f) Rewrite l. 809-811: the ranking's resolution is set by n and the cell × seed interaction
   sd σ√(1 − ρ) (s_int), not by σ. Also rewrite the box (l. 158-163), the "Expected outcome"
   paragraph (l. 769-779), [D8] (l. 1292-1294), [DK8] (l. 1347-1348, 1511-1516, now "label
   threshold"), [DK16] (l. 1371-1374, 1570-1581), [DK1] (l. 1448-1453), the "Other rows" n_5M
   block (l. 1621-1625), the cheap version (l. 1220-1221: its label reads s_int on 3 seeds, df
   2(m − 1)), l. 1666, `plan.md` l. 73, 84, 119, 128-129, 153, and the experiment-log stub l. 12.
   (g) One caveat sentence, once: a lever that changes mode probability inflates s_int, and the
   error runs toward "descriptive".
2. **(B, v4 #2, absorbs phys C4) Two-mode rows and label thresholds that hold under them.**
   Add one block to `screen_null.py`, adapted from `review/physics_v4_twomode.py` and
   `review/constructive_v4_modes.py`. Two seed structures (per-run mode, seed-shared mode; jump
   5.4 pt, within-mode sd 0.3 pt, q ∈ {0.02, 0.05, 0.1, 0.33, 0.5}). For both families (5M:
   m 37, 3 × +1 pt, top 12; 350k: m 11, 1 × +1 pt, top 3; n 4), print the median s_int,
   recovery, recovery conditional on s_int ≤ threshold, and the [DK16] extension recovery. The
   arbiter's scratch values (5M conditional 0.78 / 0.61 / 0.55 at q 0.02 / 0.05 / 0.1; 350k
   unconditional 0.48 / 0.45 at q 0.33 / 0.5) must be reproduced by the script, not quoted from
   this file.
   **Threshold rule, fixed now:** each family's label threshold T is the largest 0.1-pt value
   that meets two conditions:
   (i) Gaussian recovery at σ = T is at least 0.5 (§15 grid);
   (ii) over the per-run two-mode q grid, recovery conditional on s_int ≤ T is at least 0.5
   wherever that conditional set is non-empty.
   The q grid must be fine enough that consecutive median s_int values differ by at most
   0.1 pt. The rule may return 1.4 pt at 5M, since the Gaussian criterion already allows it,
   and that is acceptable. The 350k value is expected below 3.0 pt. The script decides both.
   Label the Gaussian table (l. 797-806) and the §16 extension rows "optimistic under per-run
   two-mode seeds", and quote the two-mode rows beside them.
3. **(B, v4 #3, with cons C1 and C3) Floor-family question.** Rewrite the frontmatter
   `question:` (l. 6) as the "In one line" sentence (l. 145-147) plus pointers, and the
   Question section's floor-family bullet (l. 189-196):
   - the informative floor-family quantity is the cross-architecture accuracy package against
     A (Welch, a package, not a single lever);
   - G2 is a feasibility count, "rescue expected from floor arithmetic" for every traced entry;
   - M001 is printed as "borderline (171,526 against 171,526.5)".

   Use "expected from floor arithmetic" in place of "structural, by construction" at
   l. 871-879 and the box (l. 153).
4. **(B, v4 #4) Ranked-list membership stated once.** M006 and M009 at 5M, and M046 if its
   [A17] check fails, go to the Welch list beside the floor-family package. The 5M ranked list
   is "at most 35 paired cells". State once, at Families (l. 896-908), that the design values
   stay at the simulated m = 37 and that every read re-simulates at the actual m (the existing
   convention). Do not re-simulate at 35. Change "up to 37" / "at most 37" / "m ≤ 37" to 35 at
   the box l. 150, Counts l. 388-389, Families l. 901, Lists l. 959-961 and the fidelity-table
   caption l. 797-798. Leave the design values at 37 labelled "design grid m = 37".
5. **(B, v4 #6) Per-cell constraint label.** Apply the rep-C slack rule (a)-(c) (l. 604-610) to
   each of M003, M007, M008, M011 and M012 at 5M on its own usable seeds, with the same ⌈3k/4⌉
   count. "Mechanism not exercised" is set by the cell's own seeds. "Constraint slack at 5M"
   stays a family label read on rep-C. Update l. 612-614, [DK18] (l. 1596-1598) and the stub.
   Apply crit C1 in the same edit: one line of rationale each for 0.8 and 0.9, and a stated
   tolerance on the β comparison.
6. **(B, v4 #8) One mode readout line, descriptive.** Adopt constructive's rule as written, at
   the replica epoch-500 gate on the 8 replica values, before any cell runs:
   - the family is "two-mode" if the largest gap between consecutive sorted values exceeds 3×
     the pooled within-cluster sd, with at least 2 seeds on each side;
   - the gap's midpoint is then fixed as the mode threshold;
   - per cell, n_low of n is printed beside mean g, with the replica's and the placebo's
     beside it.

   No decision reads it. It is the "is the low mode seed-shared" readout together with fix 1(b)'s
   side-by-side print. Within-mode g is not added (Dismissals).
7. **(C, apply before commit)** rows 9-19: phys C1, C2, C3, C5; crit C2, C3, C4, C5; cons C1
   (done in fix 3), C2 (optional), C4.

The fixer's report lists, for each grep site above, "changed" or "unaffected because …" (§6.7
cascade).

## What Kai must decide (at the launch gate; not a STUDY blocker)

The fixer writes each as a "Where I am not sure" row with its cost.

1. **Label thresholds per family** (fix 2): the script's values, against keeping one number
   for both families. This changes only labels, never what runs.
2. **The [DK16] extension, now read on s_int** (fix 1(d)): +88 runs, 1,390.3 / 2,439.3
   pod-hours at r = 1 / 2 in both families, if both land in the band. The alternative is n = 6
   for every cell of the family.
3. **Whether he wants a compute touchpoint at the replica gate.** With the pause withdrawn,
   sd_rep is printed before the cells launch and no rule reads it for ranking mode. The full
   (4, 4) design runs: 302 runs, 1,112.2-1,959.0 pod-hours, 240 packable today. If he wants
   the option to stop or cut the wave on a very large sd_rep, that becomes his call at that
   read, not a pre-registered branch.
4. **[DK18]:** if rep-C shows the 5M constraint slack, the training-only levers either get the
   350k follow-up (84 runs, 366.5 pod-hours) or go to confirm with the slack label. After crit
   C5, Kai decides that at K3.
5. **X5, the non-binary path** under the anchor's [A20] guard (M047-M049, teachers, KD cells): a
   design call for the patches owner and Kai.
6. **Carried defaults:** [DK1]-[DK5], [DK7], [DK9]-[DK16], [DK18], restated after fix 1
   ([DK8] as a label threshold, [DK17] withdrawn). [DK6] and the launch readout are already
   Kai-decided (`decisions.md`, "2026-09-27 (Kai, direct)").
