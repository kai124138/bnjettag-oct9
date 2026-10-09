# STUDY constructive review v8: 2026-09-26-training-batch

Constructive-reviewer, fresh context, 2026-09-27. Artifact `STUDY.md` at fba27d5 (2,281 lines;
working tree equal, `git diff --quiet fba27d5 -- STUDY.md`). Scope, per `STUDY_arbiter_v7.md`: fixes 1-9
landed verbatim at every listed site, with my v7 findings checked by name; a new B only if an
edited sentence is itself wrong. Diff read: `git diff d157fb9 fba27d5 -- .../STUDY.md` (116+, 40-).
Validators v8: `prose_lint` score 0.

## Fix landing, by site (line numbers at fba27d5)

All 27 line numbers in the new change-log entry (l. 235-261) match the tree.

| fix | site(s) | landed | note |
| --- | --- | --- | --- |
| 1 [A26] | l. 2015-2024; l. 1186; l. 1345 | yes, verbatim | `decisions.md:27` entry exists; `pytest_shipped_77f1ca4e.log:65-73` is the entropy tests plus the `71 passed, 2 skipped` line |
| 2 plausibility | l. 1144-1151 | yes, verbatim | 79.4 % limb and archived print gone (`grep 79.1`: only the reference table l. 383, "never a comparand"); exit closed by the four-item record. One wrong token, B1 below |
| 3 Holm m | l. 1004-1009; l. 1028-1033; l. 1560 | yes, verbatim, both families | C2 below (optional) |
| 4 imputation | l. 863-866; l. 1048-1053; l. 1123-1128 | yes, verbatim | count 8 − partner-only − both-failed = survivors + A-only imputed: correct |
| 5 W&B group | l. 1547-1549 | yes | matches patch 0026 `stage_group` as adjudicated at v7 |
| 6 DSP-free | l. 346-352 | yes | checked Table 1 myself (`pdftotext -layout`, lines 246-268): DSP = 0 for every MHA, Linformer, Deep Sets (HGQ) and MLP Mixer row; non-zero only for Deep Sets (QKeras), Deep Sets M (QKeras), Deep Sets L (QKeras). C3 below |
| 7 AUC gaps | l. 1102-1105; l. 1140-1143; l. 1223-1224 | yes | C4 below (optional) |
| 8 budget claim | l. 923-926 | yes | 178,474 matches the A/D headroom at l. 1343 |
| 9a-g | l. 2095; 2098; 1486; 1363, 833-834, 1358-1359; 1542; 210 (+187, 247); 1468-1470 | yes | `certify_ebops.py:89-91` covers `stored_equal` and the status lines; `decisions.md:11` entry name exists; gate lines `cpu_gate_d25.log:119` 58/56/2, `cpu_gate_shipped_77f1ca4e.log:55` 26/24/2 as quoted. 9g wording, C1 below |

## My v7 findings, by name

| v7 | status at fba27d5 | evidence |
| --- | --- | --- |
| B1 both-failed pair count | resolved | l. 863-866, 1048-1050, 1123-1125 |
| B2 "worst-case" label | resolved | l. 1052-1053, 1127-1128: 'surviving-minimum imputation, not a worst case and not a measurement' |
| B3 W&B canary group | resolved | l. 1547-1549 |
| C1 plausibility exit | resolved, except the arm label (B1 below) | l. 1144-1151 |
| C2 Cost pod-hours | resolved | l. 1486 "(K=4 projection; K=6 s_e from the second-wave canary)" |
| C3 NB Kai row col. 4 | resolved | l. 2098 |
| C4a superseded run-id sentence | resolved | l. 1542 |
| C4b "top of decisions.md" | resolved | l. 833-834, 1358-1359 |
| C4c stale change-log line numbers | resolved | l. 187, 210, 247 carry their shas |
| C5 entropy under zero padding | not applied; optional per arbiter v7 (#16, recommended before wave-1 VERIFY) | open, carries |
| C6 `main()` wording, C7 readout bundle shas | not applied; optional per arbiter v7 (#17) | open, carries |

## What is done well (keep)

- [+] Every fix is the arbiter's wording, tagged "arbiter v7 fix N", and the change log records
  every site with a line number that matches the tree. A reviewer can check the pass in minutes.
- [+] Fix 2 is a real improvement, not a patch: the plausibility check now compares like with
  like (validation mean against validation mean, same split, n = 62,000), has a closed exit (four
  named records; evaluation defects fixed without reselecting; training defects make the gap
  counts only), and no longer prints an archived Round-14 number beside a current arm.
- [+] Fix 3 states m before any number and states its direction against the thesis. That removes
  the last forking path in the second-wave family.
- [+] Fix 6 tells the truth about what A − NB can show: both sides are most likely DSP-free, so a
  small gap is not DSP evidence. The Table 1 claim checks out against the PDF.
- [+] Fix 8 says plainly what the budget claim can catch and that it does not test tagging
  quality.
- [+] Fix 4 now uses the n the interval actually uses, and the label no longer claims a bound it
  is not.

## Category A

None.

## Category B

### B1. Fix 2's last sentence gives FP32-E's distance A's name

- **Current state.** l. 1150-1151: "Any distance of FP32-E to 79.4 % is a ROC-test descriptive
  distance at VERIFY, worded as A − 79.4, and triggers nothing (arbiter v7 fix 2)." The sentence is
  about FP32-E's distance, but it names that distance "A − 79.4", which is the wave-1 headline
  quantity (l. 943, l. 1561). Origin: the text arbiter v7 fix 2 prescribed, copied verbatim.
- **Improved state.** "... worded as FP32-E − 79.4, and triggers nothing (arbiter v7 fix 2)."
- **Why.** An edited sentence that labels one arm's number with another arm's name. The house rule
  is that every number carries its own label. Here a VERIFY author following the text could print
  FP32-E's distance under the headline's name. This is the one case the v8 scope admits as a new B.
- **Effort.** Low (one token). No bearing on the pilot or on wave-1 production.

## Category C

- **C1. Gate-count parenthetical (fix 9g), l. 1468-1470.** "(58 and 56 in `cpu_gate_d25.log:119`;
  the shipped bundle 77f1ca4e gate reads 26 / 24 / 2, `cpu_gate_shipped_77f1ca4e.log:55`, plus
  FP32-E's 8 configs, [A25])". The clause "plus FP32-E's 8 configs" now follows 26 / 24 / 2, and
  26 + 8 ≠ 66. Improved: "(66 = 58 + 8 FP32-E configs on the d25 gate, `cpu_gate_d25.log:119`; the
  shipped bundle 77f1ca4e gate covered 26 / 24 / 2, `cpu_gate_shipped_77f1ca4e.log:55`)". Also name the
  bundle the FP32-E gate line is expected on. Low. For the orchestrator, not a STUDY defect: the
  shipped-bundle gate covers 26 configs, not 58. PREFLIGHT or RUN should say which configs
  production is gated on.
- **C2. Holm paragraph, both families (fix 3).** (a) The wave-1 copy (l. 1004-1009) ends "against
  the thesis in the second wave", but the wave-1 family is descriptive, so that sentence does no
  work there. Optional: drop it from the wave-1 copy. (b) "m falls by one" and the fixed-sequence
  clause at l. 1023-1026 ("not testable once A − FP32-E has the smaller p and fails") agree only
  because counts-only means no p. One clause would close it: "a member that leaves the family
  also leaves the sequence". Low.
- **C3. Fix 6 row names.** "Every row ... except Deep Sets (QKeras)": Table 1 also has Deep Sets M
  (QKeras) and Deep Sets L (QKeras) with DSP 548 and 2,458. Improved: "except the three Deep Sets
  (QKeras) rows". The substance is correct. Low.
- **C4. Fix 7 working point vs conventions row.** The new bullets add signal efficiency at mistag
  10⁻² per class. The Metrics conventions row (l. 1558) names only rejection at efficiency 0.5.
  Optional: add the 10⁻² working point to the row so the two agree. Low.
- **C5. Typography.** l. 1345 "entropy (row-renormalized, [A26]))": double closing parenthesis
  inside a parenthetical. Optional rewording: "entropy, row-renormalized [A26])". The v7 change-log
  entry says "Line numbers in the working tree after this pass". It can now read "at fba27d5",
  like its neighbours. Low.
- **Carried optional items (arbiter v7 #16, #17):** my v7 C5 (real-key entropy companion, script
  change, recommended before wave-1 VERIFY), C6, C7; physics C2, C3, C5, C7. Not applied, still
  optional.

## Disputed facts for the investigator

None.

## Recommendation to the arbiter

No A. One B (B1): a one-token fix to text arbiter v7 prescribed, with no bearing on the pilot or on
wave-1 production. Every other v7 fix landed verbatim at every listed site, and every v7
constructive B and required C is resolved at the lines cited. If B1 is fixed, together with C1
(optional, recommended), I see no reason from the constructive side to withhold PASS.
