# STUDY arbiter v7: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-27. Artifact `STUDY.md` at 5c49230 (2,205 lines; working tree
equal). Reviews v7: `STUDY_physics_v7.md`, `STUDY_critical_v7.md`, `STUDY_constructive_v7.md`.
Validators `STUDY_validators_v7.txt`: `prose_lint` score 0, no A line. No figures at STUDY, so no
plot-validator file. Earlier arbiter `STUDY_arbiter_v6.md`. Read `06-review.md` §6.1-6.8 and the
conventions rows of the artifact. Iteration **7** (strong-warn tier, §6.5).

## Independent checks made by the arbiter

- **Holm m under dropouts (phys B1).** `grep -n -i holm STUDY.md`: no sentence fixes m when a
  member drops, in either family. Wave 1: l. 960-962 ("a rung with fewer than 6 is reported as
  counts only", m unstated). Wave 2: l. 969-978, dropout routes at l. 1041-1042 (NB), 1090-1091
  (H), 1075 and 1079-1081 (FP32-E). Confirmed for both families (§6.3.2 extension to wave 1).
- **Plausibility gate (phys B2, phys C1, cons C1).** l. 1079-1083 as quoted. The archived
  79.1 ± 0.3 % print at l. 1082 contradicts l. 350 ("Used to size the seed spread only; never a
  comparand") and l. 1493 ("no number here sits beside Round 14"). Origin: arbiter v6 fix 4, my
  text. The 79.4 % limb compares a validation seed mean (n = 62,000, max over checkpoints) with a
  single-model ROC-test number from another pipeline; the exit ("found or ruled out") is open.
- **[A26] definition (crit B1).** `code/analysis/attn_entropy.py:12-18` defines the primary as
  row-renormalized `p = q / sum q`, raw value beside it; `:64-72` implement it. STUDY l. 1942-1948
  defines the un-renormalized quantity. Confirmed contradiction with code.
- **W&B group (crit B2, cons B3).** STUDY l. 1476-1477 vs `code/patches/0026-*.patch` l. 49
  (`"-canary"` suffix on the config group), l. 69-70, test l. 143 (`...-wave2-canary`).
  Contradicts code for wave 2 and STUDY l. 1418-1419, 1469. Confirmed.
- **Imputation pair count and label (cons B1, B2, phys C4).** l. 993-996 and 1063-1066 as quoted:
  "8 − (partner-only)" includes seeds failed in both arms; "worst-case imputation" contradicts
  "least extreme value" two sentences earlier. The general Paired-gaps bullet l. 828-830 prints
  "one-sided failure counts" only, so a both-failed seed is uncounted there too (§6.3.2).
  Origin: arbiter v6 fix 1, my text.
- **DSP-free comparand (phys B3).** `pdftotext -layout` of the cited PDF, Table 1: DSP = 0 for
  every row except Deep Sets (QKeras), including Deep Sets (HGQ) 64 at 79.4 %, MHA-64 and
  Linformer-64. STUDY quotes the accuracy column only; [L7] (l. 1984) bars a DSP statement from this
  campaign, but Bearing (l. 310-326) does not say that the comparand is already DSP-free.
  Confirmed.
- **Budget claim (phys B4).** l. 880-887 already word it as a count and say "does not mean the
  model tags well" (arbiter v4 #4). The residual, a sentence naming what the claim can catch, is
  not in the text. Finding stands; the fix is one sentence.
- **Paired AUC gaps (phys B5).** Per-class AUCs per arm sit beside the macro (l. 1487) and
  per-class AUC under 0.7 is called out (l. 1492), so a class collapse is not hidden. Paired
  macro-AUC and per-class AUC gaps for A − NB and A − FP32-E are not pre-registered (arbiter v6
  #21 left them optional). The thesis axis is AUC, so a competing group would show them (§6.3
  Q3). Finding stands.
- **Extra-pair cap timing (phys B6).** The wave-2 epoch-500 packet carries sd_diff, pair count
  and n only, "not the A − NB mean gap or its sign" (l. 1022-1026); v5 fix 3 set the cap deadline
  "any time before the wave-2 epoch-500 readout" (Kai row l. 2019). A cap set before that
  blinded readout is not post hoc, so the "before the wave-2 canary" part is refuted by the
  artifact. Resolving power at 8 pairs is stated (l. 1034-1038, 3.7 pt). Residual: the
  half-width at the cap once set.
- **Gate counts (phys C6).** `cpu_gate_d25.log:119` 58 / 56 / 2; `cpu_gate_shipped_77f1ca4e.log:55`
  26 / 24 / 2. l. 1398 does not say which bundle. Confirmed.
- **v6 fix sites, by my own read at 5c49230:** l. 562-565 (fix 5), 825-830, 985-997, 1059-1067,
  1076-1077 (fix 1), 1047-1057 (fix 3), 1079-1083 and 1460-1462 (fix 4), 1121-1122 ("softmax
  tap" gone), 1154-1158 (separate panels), 1277-1281 (pilot pending clause), 1438-1446 (fix 2),
  1494-1497 (fixes 5, 6, 9), 1874-1875 and 1940-1941 (fix 6), 1910-1916 (fix 8), 1929-1933
  (fix 7), 1942-1951 ([A26]), 2107-2112 and 2119-2122 (DECISION blocks). Pass line
  `code/evidence/pytest_shipped_77f1ca4e.log:65-73`, `71 passed, 2 skipped`.

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | [A26] STUDY definition (un-renormalized) contradicts the script's primary (row-renormalized); unit-test clause false for C′ as written | crit B1 | B | **B** | Case 3; confirmed in code. Only item bearing on the pilot (epoch-500 readout wording). Fix 1 |
| 2 | FP32-E plausibility gate: 79.4 % limb compares validation with an external ROC-test number, likely fires on an honest FP32-E, no exit criterion; archived 79.1 % printed beside FP32-E against l. 350 and l. 1493 | phys B2, phys C1, cons C1 | B, C, C | **B** | Case 2, with physics: the open exit can leave the thesis-axis interval unreported, and the print contradicts two conventions lines. Origin: arbiter v6 fix 4. Fix 2 |
| 3 | Holm family size m under dropouts unspecified (second wave; also first wave) | phys B1 | B | **B** | Case 3; confirmed at both families. m chosen after numbers would be a forking path. Fix 3 |
| 4 | Imputation pair count "8 − (partner-only)" includes both-failed seeds; Paired-gaps bullet omits the both-failed count | cons B1 | B | **B** | Case 3; confirmed; n beside an interval must be the n it used. Origin: arbiter v6 fix 1. Fix 4 |
| 5 | "Worst-case imputation" labels a surviving-minimum imputation | cons B2, phys C4 | B, C | **B** | Case 2, with constructive: the label implies a bound it is not, in the thesis-favourable direction, and contradicts its own sentence. Origin: arbiter v6 fix 1. Fix 4 |
| 6 | W&B group sentence hard-codes the wave-1 canary group | crit B2, cons B3 | B, B | **B** | Case 1; confirmed against patch 0026. Fix 5 |
| 7 | Bearing omits that the comparand rows are already DSP = 0 | phys B3 | B | **B** | Case 3; confirmed from Table 1. REPORT framing guard, one paragraph. Fix 6 |
| 8 | Paired macro-AUC and per-class AUC gaps not pre-registered for A − NB, A − FP32-E | phys B5 | B | **B** | Case 3. Partial coverage (per-arm per-class AUCs) shows the remaining ask is small, not that the finding is wrong. Fix 7 |
| 9 | Budget claim can fail almost only by controller or training failure; say so | phys B4 | B | **B** | Case 3. v4 #4 demoted the wording; the residual sentence is absent. Fix 8 |
| 10 | Extra-pair cap should be set before the wave-2 canary; smallest resolvable gap at the cap | phys B6 | B | **C** (required, residual) | Timing refuted by l. 1022-1026 (blinded packet) and v5 fix 3; resolving power already stated at 8 pairs (l. 1034-1038). Residual: record the half-width at the cap in the Kai row. Fix 9 |
| 11 | NB Kai row, last column: "decided at the canary", "K=8 does not fit" | crit C1, cons C3 | C | C (required) | Fix 9 |
| 12 | Second-wave Cost bullet: K=6 count inside a K=4 projection | crit C2, cons C2 | C | C (required) | Fix 9 |
| 13 | Citations: `certify_ebops.py:89-90` → `:89-91`; "top of decisions.md" | crit C3, cons C4b | C | C (required) | Fix 9 |
| 14 | Stale change-log line numbers; old run-id sentence before its amendment | crit C4, cons C4a, C4c | C | C (required) | Fix 9 |
| 15 | Gate count "58 and 56 now" names no bundle | phys C6 | C | C (required) | Fix 9 |
| 16 | Entropy confounded by zero-padded keys (no mask) | cons C5 | C | C (optional, recommended before wave-1 VERIFY) | Script change, descriptive. Fix 9 |
| 17 | Step counts beside epoch-matched gaps; "consistency check"; one pairing logic; per-kernel scale note; `certify_ebops.main()`; readout bundle shas | phys C2, C3, C5, C7, cons C6, C7 | C | C (optional) | Fix 9 |

## Earlier A and B findings (arbiter v6), by name

| v6 # | finding | status | evidence (arbiter's read at 5c49230) |
| --- | --- | --- | --- |
| 1 (A) | survivor bias in headlines and Paired gaps | **resolved** | l. 825-830, 985-997, 1059-1067, 1076-1077 verbatim; two defects inside the prescribed text are #4, #5 above (new B, not a v6 carry-over) |
| 2 | K=7 join on memory only | **resolved** | l. 1438-1446 (i)-(iii), "no scaling of the K=6 s_e"; l. 1409-1411; Kai rows l. 2020, 2022 col. 3; DECISION l. 2111-2112. Residual col. 4 wording is #11 |
| 3 | "close" claim, no margin | **resolved** | l. 1047-1050, 317, 324-326; "close" only in "never ... as a verdict" |
| 4 | L > 0 branch hides sign | **resolved** | l. 1055-1057, investigator route |
| 5 | \|U\| against Holm verdict | **resolved** | l. 985-986 ('falsified'), 1053-1055 ('resolved cost') |
| 6 | FP32-E plausibility | **resolved** as prescribed; the prescribed text is defective, #2 above | l. 1079-1083, 1460-1462 |
| 7 | quantizer-variable check | **resolved** | l. 562-565, 1497, 1688-1691, 2107-2110, 1938-1939 |
| 8 | `binary_gate` for FP32-E and NB | **resolved** | l. 565, 1874-1875, 1940-1941, 1497 |
| 9 | pairing count | **resolved** | l. 1929-1933; `n_shared` 15 (critical, `a17_pairing_d25_8seeds.json`) |
| 10 | config hygiene | **resolved** | l. 1913-1916 |
| 11 | conventions rows | **resolved** | l. 1494-1496 |
| 12 | entropy not implemented | **resolved** (script, tests, pass line `pytest_shipped_77f1ca4e.log:65-73`); definition text stale, #1 |

## Regression triggers (§6.7), checked independently

STUDY is the origin phase; no result exists. Selection on held-out or changed after results: not
met (validation selection; the plausibility and Holm-m rules are fixed here before any wave-2
number). Val/ROC AUC > 0.01, single-seed headline, cross-N series, gap < sd at < 3 seeds: not met
(no numbers). Reload > 1e-7 / TF32: not met. EBOPs not remeasured: not met (certification rule
l. 1288-1296). Binary > 2 values: not met (`binary_gate` on binary arms; exemptions l. 1497).
DSP / C-sim / C-synth: not applicable ([L7]). Per-class AUC hidden: not met (l. 1487, 1492).
Byte-identical arms / different `y`: not met (l. 1491). Failed validation or tautological
comparison: not met; the budget claim is not tautological (degenerate collapse is reachable, v3
#1), #9 only asks the text to say what it screens. [D] replaced without dated amendment: not
met ([D24], [D26] DECISION blocks amended with dates). Outward mismatch: not applicable.
**No trigger met.**

## Validation target (§6.8) and competing group

No arm is bound at VERIFY (l. 1489); correct. FP32-E has no binding reference, which is why #2
removes the 79.4 % limb from a gate that withholds a result. Competing group: they would show the
paired AUC gaps on the thesis axis (#7 → fix 7) and say that the comparand is already DSP-free
(#7 → fix 6). Nothing else missing that STUDY does not name as a limitation or Kai row.

## Disputed facts for the investigator

None.

## Dismissals

None. #10 is a partial rebuttal with evidence (l. 1022-1026, v5 fix 3), not a dismissal; its
residual is a required C.

## Motivated-reasoning check

#5 (a "worst-case" label on a non-worst-case imputation), #7 (a small A − NB readable as DSP
support) and #3 (m left open, so a larger m that shields A − NB from falsification could be picked
later) lean thesis-favourable by default. #2 in its current form can withhold the thesis-axis
interval indefinitely. All are fixed in text before any number exists. Three of the nine B are
defects in text I prescribed at v6 (fixes 1 and 4); the fixes below replace that text rather than
patch around it.

## Bearing on the pilot, wave-1 production, wave 2 and REPORT

- **Pilot:** #1 only, and only the epoch-500 readout wording (the script already computes the
  renormalized quantity). Deadline: before the pilot's epoch-500 readout (about 16-26 h after
  launch). No pod, bundle or ConfigMap change.
- **Wave-1 production, substantively:** none. No item changes a wave-1 arm, seed, target, pod
  composition, K, selection rule or certification rule.
- **Wave-1 VERIFY wording:** #3 (first-wave family clause), #4 (Paired-gaps both-failed count).
- **Wave 2 / VERIFY / REPORT:** #2, #3 (second-wave clause), #4, #5, #6 (wave-2 canary W&B
  group), #7, #8, #9.
- **Procedurally:** all nine B block wave-1 production through Kai's condition 3 (STUDY PASS
  before wave-1 production). The pass is text-only (about 1 agent-hour, no code), and v8 is a
  landing check, so it should clear before the pilot's canary timing exists.

## Verdict

**ITERATE** (STUDY panel, iteration 7 → fixer, then v8). No A; nine B (#1-#9), all STUDY text.
**Strong warning (§6.5, iteration 7; ESCALATE at 10).** Not ESCALATE: no disputed A, no
falsified claim, no resource wall.

v8 scope: reviewers check that fixes 1-9 landed verbatim at every listed site and that no listed
site was missed. A v8 restatement of an item adjudicated here or earlier is closed by citing the
evidence recorded in this file or its predecessors (a line, a code path, a table), not by citing
the adjudication. A genuinely new B on text unchanged since v6 is judged on its merits (case 3);
the physics-reviewer does not see earlier reviews, so this scope cannot bind it, only the arbiter's
reading of it.

## Ordered fixes (fixer; experiment-designer if CANNOT RESOLVE)

1. **(#1, deadline: before the pilot's epoch-500 readout) [A26] definition.** At l. 1945-1948
   replace "reports per block and head the mean over jets and query rows of −Σ p log p over the 64
   keys, divided by log 64, from the quantized softmax output as the model computes it. CPU unit
   tests: uniform logits give 1 within 1e-6; one-hot logits give about 0." with "reports per
   block and head the mean over jets and query rows of −Σ p log p over the 64 keys, divided by
   log 64, with p the `{blk}_attn_softmax` output as the model computes it (quantized tables)
   divided by its row sum (primary; the fixed-softmax build does not emit rows summing to 1,
   `.claude/memory/decisions.md` entry '2026-09-27 (ml-engineer, PREFLIGHT gate v1 fixer +
   [A26])'); the un-renormalized value −Σ q log q / log 64 and the row-sum min / mean / max are
   printed beside it. CPU unit tests, on the renormalized primary: uniform logits give 1 within
   1e-6; one-hot logits give about 0 (`code/evidence/pytest_shipped_77f1ca4e.log:65-73`)." At
   l. 1117 after "(n = 62,000) as a fraction of log 64" add "(row-renormalized, [A26])".
2. **(#2) Plausibility gate.** Replace l. 1079-1083 in full with: "Plausibility (pipeline check,
   not a result): if FP32-E's seed-mean validation accuracy at its selected checkpoints is below
   A's, FP32-E goes to ml-engineer before REPORT. The check is closed by a written record of four
   items: FP32-E's selected epochs, its train and validation curves, the [A25] pairing record and
   the byte-equal `y` check. If none shows a defect, A − FP32-E is reported with the trigger and
   that record beside it. An evaluation, pairing or `y` defect is fixed and FP32-E re-evaluated
   without reselecting; a training-side defect makes A − FP32-E counts only, with the defect
   named. Any distance of FP32-E to 79.4 % is a ROC-test descriptive distance at VERIFY, worded as
   A − 79.4, and triggers nothing (arbiter v7 fix 2)." No archived Round-14 number and no
   validation number is printed beside 79.4 % or beside FP32-E's gap.
3. **(#3) Holm m under dropouts, both families.** After l. 962 ("... reported as counts only.")
   and after l. 978 ("(arbiter v6 fix 11).") add the same paragraph: "Family size under dropouts
   (fixed 2026-09-27, before any wave-1 or wave-2 number; arbiter v7 fix 3): m is the number of
   members whose gap is reported at VERIFY. A member reported as counts only, for any reason,
   leaves the family and m falls by one. A member whose gap is first reported after VERIFY is
   reported with its interval and no p, and the adjusted p-values already issued do not change.
   m is printed beside every adjusted p. Direction: a smaller m makes the remaining members easier
   to falsify, which is against the thesis in the second wave." In the conventions row "Seeds and
   intervals" (l. 1488), after "own Holm family {A − NB, H − NB, A − FP32-E}" add "(m under
   dropouts: Falsifier, arbiter v7 fix 3)".
4. **(#4, #5) Imputation count and label, three sites.** Paired-gaps bullet l. 828-830: replace
   "Beside every paired gap the report prints the one-sided failure counts (seeds with an accuracy
   number in one arm only, per arm)" with "Beside every paired gap the report prints the one-sided
   failure counts (seeds with an accuracy number in one arm only, per arm) and the both-failed
   count (seeds with no accuracy number in either arm)". At l. 993-994 and l. 1063-1064 replace
   "the interval is recomputed over the 8 − (partner-only) pairs." with "the interval is
   recomputed over 8 − (partner-only) − (both-failed) pairs; seeds failed in both arms are
   excluded and counted beside it." At l. 995-996 and l. 1065-1066 replace "labelled 'worst-case
   imputation, not a measurement'" with "labelled 'surviving-minimum imputation, not a worst case
   and not a measurement'".
5. **(#6) W&B group.** At l. 1476-1477 replace "pilot and canary log into
   `chang-n64-20260926-canary`, production into the config's group." with "pilot and canary log
   into the config's group with `-canary` appended (`chang-n64-20260926-canary` for wave 1,
   `chang-n64-20260926-wave2-canary` for wave 2; patch 0026 `stage_group`), production into the
   config's group."
6. **(#7) DSP-free comparand.** In Bearing, after "(A − NB carries that at iso-EBOPs)." add: "Every
   row of arXiv:2510.24784 Table 1 except Deep Sets (QKeras) reports DSP = 0, including the 79.4 %
   Deep Sets (HGQ) comparand, MHA-64 and Linformer-64, so the published comparands at this budget
   are already DSP-free in synthesis.
   A − NB therefore most likely compares two DSP-free designs; a hardware advantage of binary
   would have to show in LUT or latency, which this campaign does not measure ([L7]). REPORT does
   not read a small A − NB or A − FP32-E as support for the DSP claim (arbiter v7 fix 6)."
7. **(#8) Paired AUC gaps.** Add a bullet under the weight-type claim (after l. 1045) and under
   "Precision package" (after l. 1078): "Beside the accuracy gap, descriptive and outside the Holm
   family: the paired ROC-test macro-OvR AUC gap and the five per-class AUC gaps, each a 95 %
   interval over the same seeds (paired, or Welch where the accuracy gap is Welch; n = 260,000 per
   run), and per class the signal efficiency at
   mistag 10⁻² per arm (arbiter v7 fix 7)." In the second-wave figure text (l. 1154-1158) add: "a
   per-class paired AUC-gap panel for A − NB and, separately, A − FP32-E."
8. **(#9) Budget claim.** At the end of the "Not falsified" bullet (after "no new floor.)", l. 887)
   add: "The claim does not test tagging quality: with 178,474 EBOPs of headroom a pass is expected,
   and the claim screens for controller failure (the PID never landing), divergence and
   degenerate collapse under budget pressure (arbiter v7 fix 8)."
9. **C items, apply now.** (a) Kai row 'extra A/NB pairs (cap)' (l. 2019), last cell: append "When
   the cap is set, the row records the 95 % half-width at the cap at the proxy sd_diff." (b) NB Kai
   row l. 2022 col. 4: "decided at the canary" → "decided at the K=7 re-canary"; "K=8 does not fit"
   → "a K=8 re-canary does not pass (i) to (iii)". (c) l. 1415: after "≈ **876 pod-hours**" add
   "(K=4 projection; K=6 s_e from the second-wave canary)". (d) l. 1293 `certify_ebops.py:89-90` →
   `:89-91`; l. 800 and l. 1289 "the top of `.claude/memory/decisions.md`" → "the
   `.claude/memory/decisions.md` entry '2026-09-27 (orchestrator, PREFLIGHT gate v2)'". (e) l.
   1470-1471: prefix "Superseded by the amendment below: " to "The runner's run id is sha256(config
   name)[:12] ...". (f) Fixer change-log line numbers: add "(line numbers at 99f0a2d)". (g) l. 1398:
   "(58 and 56 now" → "(58 and 56 in `cpu_gate_d25.log:119`; the shipped bundle 77f1ca4e gate reads
   26 / 24 / 2, `cpu_gate_shipped_77f1ca4e.log:55`". Optional: cons C5 real-key entropy companion
   line (script change, before wave-1 VERIFY); phys C2 step counts, C3 "consistency check", C5 one
   pairing statement, C7 scale note; cons C6 `certify_ebops.main()`, C7 both shas.
   Change-log line: "arbiter v7 fixes 1-9; no change to any arm, seed, target, pod, K, selection
   or certification rule".
