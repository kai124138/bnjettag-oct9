# STUDY critical review v11: 2026-09-26-training-batch (landing check)

Critical reviewer, panel mode, fresh context, 2026-09-28. No verdict (the arbiter issues it).
Artifact: `STUDY.md` at f6bb75c (identical to the working tree). Line numbers below are at
f6bb75c unless marked; f6bb75c is 725acba with one change-log line merged, so lines after l. 405
are 725acba − 1. Diff reviewed: `git diff 50bf1f9 f6bb75c -- STUDY.md` (194+/58−).
Scope, from the brief: only whether Kai's K1-K3 (`.claude/memory/decisions.md`, 2026-09-28 top
entry), arbiter v10's F1-F7 (`review/STUDY_arbiter_v10.md`) and the 6/8 GiB memory split landed
correctly, plus the fixer's three disclosed departures. A new A or B is raised only where a landed
sentence is wrong or contradicts Kai's answer; everything else is C.

## What I checked, with numbers

- **Pod classes (F1 departure 1).** `code/tree/campaigns/chang0926/packs.json` mapped through
  `index.json` `runs[i].arm/seed`: packs 0-3 are E arms at K=5 (A, B, D, F mixed seeds), packs 4-6
  are E arms at K=4 (A/B/D/F-s6, -s7, -s8), packs 7-10 are C + A07-350 at K=4, packs 11-12 are R at
  K=4. `packs_meta.json` `arms_per_pack` [5,5,5,5,4×9], `wait_for_k3_readout` [7,8,9,10]. So the
  fixer is right and the arbiter's F1 text ("E pods (K=5)") was incomplete. 4 + 3 + 4 + 2 = 13 pods,
  as STUDY l. 1595-1597 says.
- **Thresholds (K1 departure 2).** From `index.json` `target_ebops` / `zero_floor_ebops`:
  A, D, F, R headroom 178,474 → 10 % = 17,847; E1 264,237 → 26,424; A07-350 6,947 → 695;
  C 5,000,000 − 343,053 = 4,656,947 → 465,695; C′ 5,000,000 − 4,580,398 = 419,602 → 41,960;
  B 250,000 − 171,526 = 78,474 → 7,847. The STUDY's F 17,847 and C 465,695 match.
- **Regime-A offsets (K1 "Expected").** From RUN.md l. 705-709 medians (A-s1 1.0772, A-s2 1.0739,
  D-s1 1.0717, E1-s1 1.0920, C′-s1 1.0000), offset = 350,000 × (1 − r^−0.9): 22,658 / 21,753 /
  21,147 / 26,654, so 12.70 / 12.19 / 11.85 % of 178,474 and 10.09 % of 264,237. E1 − D = 0.0203.
  All match STUDY l. 1737-1740. The arbiter's "12-15 %" was high; the fixer's correction to
  11.8-12.7 % is right and disclosed.
- **K3 arithmetic.** t(0.975, 7)/√8 = 0.8360 (STUDY: 0.836). The noncentral-t 80 %-power
  detectable gap at 8 pairs, α 0.05 two-sided, is 1.156 · sd_diff (STUDY: 1.16). At sd_diff =
  √2 × 3.145 = 4.448 (zero correlation) that gives 5.14 pt (STUDY row l. 2614: "about 5.2 pt",
  which uses the rounded 1.16).
- **F1 A07 arithmetic.** (163.3 + 130.4/10) × 7,000 / 86,400 = 14.29 d; the bound is
  14 × 86,400 / 7,000 = 172.8 s; E: 136.5 s → 11.06 d. All match l. 1580-1592.
- **F5 epoch ranges.** E1-s1 to epoch 88 and C′-s1 to epoch 47 match RUN.md l. 708-709 (ranges
  1-88, 1-47).
- **Change-log line citations** (entry l. 400-435, "line numbers at 725acba"), spot-checked
  against `git show 725acba`: l. 746, 1210, 1253, 1554, 1581, 1594, 1717, 1743, 1744, 1795, 1806,
  1861, 1882, 1987, 2508, 2607, 2615, 2616 each open on the cited text. No defect.
- **Residual pre-amendment text.** `grep` for "all 7,000", "all epochs", "selection domain",
  "per-epoch reset", "A seeds 9", "extra pair", "cap": the remaining hits are change-log history,
  the "Was:" / "declined" clauses, and l. 792 (H's own training loop, unrelated). No live sentence
  still says FP32-E selects over all 7,000 epochs or that extra A/NB pairs are run.
- **Memory split vs RUN.md.** STUDY l. 1861-1882 (6,144 MiB for the running K=3 pod until its swap
  before process epoch 105; 8,192 MiB under the c7bae4a manifests; the manual epoch-10/20 rule
  uses the pod's own L) agrees with RUN.md l. 561-593 ('8 GiB swap timing', safe window about
  2026-09-29T00:25Z-01:35Z) and RUN.md l. 639-655 (K=5 Job re-applied from the 8 GiB manifest
  2026-09-28T23:45:43Z, pod `-qqjmt`, Pending). Fill epochs: (8,192 − 2,106..2,160)/(80..95) =
  63.5-76.1 → "64-76" is right.
- **(c) staged, unapplied.** `code/staged-option-c/` exists beside `code/tree/`; the running
  bundle is unchanged (not re-hashed here; out of scope).

## Landing table

| item | lands at (f6bb75c) | status |
| --- | --- | --- |
| K1 = (b): threshold, three clauses, (c)/(d) at epoch 500, (c) staged unapplied, declined options | l. 1716-1742; slot P (3) l. 1553-1561; [D20] l. 2201-2203; A rule l. 1698-1700; A07-350-s1 l. 1713-1715; launch l. 1809-1811; Kai row l. 2606 | landed; one defect in the B addition (B1 below) |
| K2: FP32-E on the 701 slot-T epochs | Selection l. 745-750; table l. 833; confound 12 l. 898-900; evaluations l. 1066-1067; conventions l. 2057; [D26] l. 2265-2267; [A25] code item l. 2507-2512; Kai row l. 2615; DECISION l. 2708-2713 | landed, consistent at every site |
| K3: 8 pairs, no extras, wide interval reported | l. 1252-1263, 1315-1316, 1986-1989, Kai row l. 2614 | landed |
| F1 T_run per pod class | l. 1580-1593 | landed; departure 1 correct against `packs.json` |
| F2 arm-C slack | l. 1794-1799; C′ l. 1805 | landed verbatim |
| F3 package label | l. 833, 898-900 | landed, as the K2 amendment (departure 3 follows the arbiter's own conditional) |
| F4 A − NB leads with the resolvable gap | l. 1209-1213 | landed |
| F5 matched traced-epoch table | l. 1743-1748; pointer l. 1683-1684 | landed |
| F6 shas, Pods paragraph, RSS indexing | l. 305, 355; l. 1595-1605; l. 1860-1863 | landed |
| F7 regime-A measurement in slot P | l. 1553-1558 | landed verbatim |
| 6/8 GiB split | l. 389-391; l. 1860-1882 | landed, consistent with RUN.md; one attribution defect (B2) |

## Findings

### Category A

None.

### Category B

**B1. The B clause the fixer added to K1's threshold can fire only after production has launched,
and the consequence it names ("production waits for Kai, who chooses at the epoch-500 readout
between (c) and (d)") can then no longer be carried out.** STUDY l. 1724-1726: "... iso-EBOPs
comparison (A, D, B, F, A07-350, C; B has no pilot run, so its r is first measured in production and
the clause reads it there)". l. 1729-1732: "If it fires, production waits for Kai, who chooses at the
epoch-500 readout between (c) ... and (d) ...". B-s1..s8 sit in production packs 0-6 beside A, D and F
(`packs.json`). A B-driven firing therefore comes after wave 1 is running. Both remedies change
`code_sha256` or `config_sha256`, so a B firing would stop or restart the whole E wave. It could not
make production "wait". Kai's K1 places the choice at the (pilot) epoch-500 readout. The sentence as
landed puts a trigger outside that window and leaves its consequence undefined. The offset clause also
has no form for B's 250k target (the formula names 350k and 5M only; B's 10 % headroom is 7,847).
- *Impact:* a production-time firing has no registered action. Deciding its meaning after B's r is
  seen is post-hoc.
- *Fix (one of these, minimum change):* (i) state that B's r is read at production epoch 500 and
  reported beside every A − B / budget-ladder number as a descriptive caveat. It does not fire the
  rule or stop production. The pilot-time rule then reads only arms with a pilot run. Or (ii) take
  B's r at the pilot as A's (same architecture and floor), labelled an assumption. Or (iii) name the
  production-time consequence explicitly. That would be a Kai choice, so (i) is the fixer-only route.
  In any case, write the offset as T_arm × (1 − r^−0.9).

**B2. The memory split is attributed to Kai, but Kai's recorded answer does not contain it.** STUDY
l. 390 ("[corrected 2026-09-28, Kai, STUDY v10 ESCALATE: 8,192 applies to the c7bae4a manifests
only ...]") and l. 1864-1865 ("L per pod (Kai, STUDY v10 ESCALATE, 2026-09-28; arbiter v10,
orchestrator note (2))"). The decisions.md entry records only K1-K3 and "The running K=3 pod is not
stopped". The 6/8 GiB split comes from arbiter v10's orchestrator note (2). The fixer's own entry
calls it "Memory (orchestrator)" (l. 430). The rule itself is correct (see the RUN.md check above).
The label is wrong, and in this lab a "Kai" label marks a decision that reviewers may not reopen.
- *Fix:* at both sites, give each part its own source: the 6,144 MiB rule for the running pod
  comes from Kai (PREFLIGHT gate v3 escalation, decisions.md 2026-09-28); the 8,192 MiB limit from
  the ml-engineer/coordinator entry (decisions.md 2026-09-28, c7bae4a); the split between them from
  arbiter v10 orchestrator note (2) and RUN.md '8 GiB swap timing'. `grep` of RUN.md finds no Kai
  line on the split itself.

### Category C (for a "freeze with disclosed B" option)

- **C1. Wind-up clause names "an A07 run" (l. 1727).** C (A07 at 5M) satisfies "in-training above
  350k" trivially, so the clause relies only on C's traced EBOPs never sitting within 1 % of 343,053.
  "An A07-350 run" would say what is meant. This wording is the arbiter's and was carried verbatim.
- **C2. C′'s headroom threshold is not printed.** C′-s1 is in the readout list (l. 1718), and "that
  arm's headroom" covers it, but the explicit list stops at C. C′: 419,602 → 41,960.
- **C3. "Taken as an upper bound" (l. 1583-1584)** rests on an unstated assumption: s_e is monotone
  in co-resident count, and the K=5 pilot mix (A, A, D, E1, C′) is at least as heavy as a K=4 E pod.
  Both are plausible, and C′ being an A07 model makes the pilot pod heavier, but it is an assumption,
  not arithmetic. One clause would disclose it.
- **C4. "Untimed until then" (l. 1586)** does not say what happens at launch if no K=4 A07 s_e
  exists. The 14-day branch covers only "exceed 14 d". Packs 7-10 already wait for the K=3 readout.
  STUDY should say whether they launch and are timed over their own Symbols window, or wait.
- **C5. "about 5.2 pt" (l. 2614)** is 5.14 pt at the unrounded 1.156; "about 5.1 pt" is closer.
  Also, "near epoch 48 at 6 GiB" (l. 1881) gives (6,144 − 2,106..2,160)/(80..95) = 41.9-50.5, so
  "near epochs 42-50" matches the 8 GiB form.
- **C6. Tense.** l. 1867-1868 and l. 432-433 say the Pending K=5 pod "is deleted and re-applied".
  RUN.md l. 639-655 records that it already was (23:45:43Z, pod `-qqjmt`).
- **C7. Old ml-engineer change-log line l. 389** still cites "l. 1748-1760" for the host-memory
  bullet, which now sits at l. 1860-1882. It is history, not a live pointer.

- **C8. The wind-up clause names no data source (l. 1726-1728).** It reads in-training EBOPs on
  *untraced* epochs. Slot P (3) (l. 1552-1553) and [D20] (l. 2201) name `ebops_in_training` only
  at traced epochs. Arbiter v10 #9 records that the bundle's stdout `in_training_ebops` prints
  `saved_ebops` (int, filtered), while W&B `model_ebops` (float) is the PID's input. If the
  readout is computed from stdout, it uses the wrong column. Name W&B `model_ebops` per epoch as
  the source until the next bundle fixes stdout.
- **C9. "iso-EBOPs comparison (A, D, B, F, A07-350, C)" (l. 1724-1725)** is the arbiter's wording.
  B (250k) and C (5M) are not at A's target; "arms compared at their nominal targets" is what is
  meant.

## Earlier findings, by name (arbiter v10)

| v10 # | status |
| --- | --- |
| 1 (A, K1) regime-B PID input | resolved by Kai's (b), landed; B1 is a defect in the fixer's B addition only |
| 2 (A, K1) A07-350 wind-up | resolved: third clause of the threshold (l. 1726-1728); C1 wording |
| 3 (B, F1) T_run per pod class | resolved; C3, C4 |
| 4 (B, F2) arm-C slack | resolved |
| 5 (B, F3 + K2) FP32-E grid | resolved at all nine sites |
| 6 (B, F4 + K3) A − NB resolution | resolved |
| 7 (C req., F5) matched table | resolved |
| 8 (C req., F6) stale text | resolved |
| 9 (C, stdout field) | ml-engineer, next bundle; not a STUDY item |
| orchestrator note (2) memory split | resolved in substance; B2 attribution |

## Competing-group question (scoped)

Within this scope, a competing group would have the same controller-input readout. Where our text
falls short is that it would also say what a production-time mismatch does (B1). Nothing else.

## Recommendation (not a verdict)

**One fixer pass** on B1 route (i) and B2 (label edits), with C8 if cheap. None of these edits
changes an arm, seed, target, selection rule or any of Kai's answers. One caveat: route (i) takes B out of the
fire list that the arbiter enumerated in its (b) text, which the change-log calls "verbatim". That
is a departure from the arbiter's wording, not from Kai's answer (Kai's K1 does not name arms), so
the arbiter must accept it explicitly in the same pass. If the arbiter does not, B1 goes to Kai as
route (iii).
