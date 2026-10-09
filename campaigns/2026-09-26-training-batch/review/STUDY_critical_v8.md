# STUDY critical review v8: 2026-09-26-training-batch

Critical reviewer, panel mode, fresh context, 2026-09-27. Artifact `STUDY.md` at fba27d5 (2,281
lines). Scope per `review/STUDY_arbiter_v7.md` "v8 scope": check that fixes 1-9 landed verbatim
at every listed site. Diff read: `git diff d157fb9 fba27d5 -- campaigns/2026-09-26-training-batch/STUDY.md`
(1 file, +116 / −40). Fixer change-log entry l. 254-280. No verdict; the arbiter issues it.

## Validators (verbatim, `review/STUDY_validators_v8.txt`)

```
Desktop/bnjettag/campaigns/2026-09-26-training-batch/STUDY.md  —  score 0, reads human
  32696 words · 831 sentences · mean 25 words (σ=22.0) · 17% bullets · 0 em-dashes
Diff since v7 review (d157fb9):  1 file changed, 116 insertions(+), 40 deletions(-)
```

No red flag. No figures at STUDY, so there is no `plot_check.py` output.

## Fix landing, by arbiter v7 fix number

Each site was read at fba27d5. The fixer's change-log line numbers (l. 259-280) were checked one by
one with `sed -n`, and every range shows the text it names.

| fix | v7 # | sites prescribed | landed at (fba27d5) | verbatim | status |
| --- | --- | --- | --- | --- | --- |
| 1 | 1 | [A26] body; attention-state list after "as a fraction of log 64" | l. 2014-2024; l. 1185-1186; also pilot readout l. 1345 (fixer, by neighbourhood) | yes | **landed** |
| 2 | 2 | plausibility gate, replace in full | l. 1144-1151 | yes | **landed**; one edited sentence mislabels a quantity, B1 below |
| 3 | 3 | after "counts only." (wave 1); after "(arbiter v6 fix 11)." (wave 2); conventions row | l. 1004-1009; l. 1028-1033; l. 1560 | yes (identical paragraphs) | **landed** |
| 4 | 4, 5 | Paired-gaps bullet; A − NB headline; precision-package headline | l. 863-866; l. 1048-1053; l. 1123-1128 | yes | **landed** |
| 5 | 6 | W&B group sentence | l. 1547-1549 | yes | **landed** |
| 6 | 7 | Bearing, after "(A − NB carries that at iso-EBOPs)." | l. 346-352 | yes | **landed** |
| 7 | 8 | weight-type claim; precision package; second-wave figure text | l. 1102-1105; l. 1140-1143; l. 1223-1224 | yes | **landed** |
| 8 | 9 | end of "Not falsified" budget bullet | l. 923-926 | yes | **landed** |
| 9a | 10 | Kai row extra A/NB pairs | l. 2095 | yes | **landed** |
| 9b | 11 | NB Kai row col. 4 | l. 2098 | yes | **landed** |
| 9c | 12 | second-wave Cost | l. 1486 | yes | **landed** |
| 9d | 13 | `:89-91`; decisions.md entry name at two sites | l. 1363; l. 833-834, l. 1358-1359 | yes | **landed** |
| 9e | 14 | superseded run-id sentence | l. 1542 | yes | **landed** |
| 9f | 14 | sha on the v6 fixer entry | l. 210 (99f0a2d); fixer also added l. 187 (54bf3e7) and l. 247 (5c49230) | yes | **landed** |
| 9g | 15 | gate counts per bundle | l. 1468-1470 | yes | **landed**; wording misleads, C1 below (the fixer's open question) |

Residual old text, by grep on fba27d5: "worst-case" 0 hits; "8 − (partner-only) pairs" 0;
"top of `.claude/memory/decisions.md`" 0; "89-90" 0; "79.1" 0 (l. 383 and l. 1133 keep only the
archived sizing sd, labelled "sizing only", which v7 did not ask to remove); "or below 79.4" 0;
"ruled out" 0; "decided at the canary" 0; "K=8 does not fit" 0. No listed site was missed.

### Evidence behind the landed text

- **Fix 1.** `code/analysis/attn_entropy.py:12-18` defines `p = q / sum_s q` as primary and prints
  the raw value and the row-sum min / mean / max (`:64-71`, `:117-120`, `:131-135`, `:300`
  `A26_ROWSUM`). STUDY l. 2018-2022 now match. `code/evidence/pytest_shipped_77f1ca4e.log:65-73`:
  `test_uniform_logits_give_one` and `test_one_hot_logits_give_zero` pass for `a`, `cprime` and
  `fp32`, last line `71 passed, 2 skipped in 79.75s`. The decisions.md entry exists by that exact
  name: `.claude/memory/decisions.md:27` "2026-09-27 (ml-engineer, PREFLIGHT gate v1 fixer + [A26])".
- **Fix 5.** `code/patches/0026-*.patch:68` defines `stage_group(group, stage)`; `:33` and `:96`
  call it on `cfg['experiment']['group']`, so the wave-2 canary group is the config group plus
  `-canary`, as l. 1547-1549 now say.
- **Fix 8.** 350,000 − 171,526 = 178,474, the A/D headroom stated at l. 916 and l. 1343.
- **Fix 9d.** `code/tree/campaigns/chang0926/certify_ebops.py:89` computes `stored_equal`, and
  `:90-91` assign `STORED_MISMATCH` after `EBOPS_MISMATCH`, so `:89-91` is the right span.
  `.claude/memory/decisions.md:11` is "2026-09-27 (orchestrator, PREFLIGHT gate v2)".
- **Fix 9f shas.** All three are commits (`git cat-file -t`). One reference checked at each:
  `git show 5c49230:.../STUDY.md` l. 1473-1480 is the run-id amendment (flag 2); `99f0a2d` l.
  818-820 is the "Paired gaps" bullet (fix 1); `54bf3e7` l. 225, 248, 269 are the Question,
  H0-precision and Bearing A − FP32-E sentences. All three match.
- **Fix 2, second v6 site.** The FP32-E epoch-500 rule (l. 1530-1533) prints FP32-E's validation
  mean beside A's (n = 62,000, labelled, never quoted), with no 79.4 % and no Round-14 number.
  This agrees with the fix-2 constraint.

## Earlier A and B findings (arbiter v7 #1-#9), by name

| v7 # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 | [A26] definition contradicts the script | **resolved** | l. 2018-2024 against `attn_entropy.py:12-18`; tests on the primary, `pytest_shipped_77f1ca4e.log:65-73` |
| 2 | plausibility gate: 79.4 % limb, archived 79.1 % print, open exit | **resolved** (see B1 on one label) | l. 1144-1151; four-item closing record; 79.1 absent from the section |
| 3 | Holm m under dropouts, both families | **resolved** | l. 1004-1009, 1028-1033, 1560 |
| 4 | both-failed seeds in the pair count and the Paired-gaps bullet | **resolved** | l. 864-865, 1048-1049, 1123-1125 |
| 5 | "worst-case imputation" label | **resolved** | l. 1052, 1127 |
| 6 | W&B group hard-coded to the wave-1 canary | **resolved** | l. 1547-1549; patch 0026:68 |
| 7 | Bearing omits DSP = 0 comparands | **resolved** | l. 346-352; l. 1570 (no LUT or DSP claim, [L7]) agrees with it |
| 8 | paired macro and per-class AUC gaps | **resolved** | l. 1102-1105, 1140-1143, 1223-1224 |
| 9 | budget claim screens only controller or training failure | **resolved** | l. 923-926 |

Required C items #10-#15 landed (table above). Optional C items (#16, #17) were not applied, and
the change log records this at l. 279-280. That is allowed by v7.

## Findings

### Category A

None.

### Category B

**B1. Fix 2 names FP32-E's distance to 79.4 % with A's label (l. 1150-1151).** The landed text
reads: "Any distance of FP32-E to 79.4 % is a ROC-test descriptive distance at VERIFY, worded as
A − 79.4, and triggers nothing". Read literally, it tells VERIFY to label FP32-E's distance
"A − 79.4". That is also the name of the registered A-arm quantity (l. 319, l. 943, l. 1083). The
result would be two different numbers under one label, which breaks the Labelling row (l. 1562)
and CLAUDE.md's rule that every number carries its metric and identity. The intended reading,
"in the same descriptive form as A − 79.4", is clear from context, so the arbiter can close this
in one line. It is still an edited sentence that is wrong as written, which is the v8 bar for a
new B. The text is the arbiter's own, prescribed verbatim, so the fixer applied it correctly.
*Fix:* replace "worded as A − 79.4" with "worded as FP32-E − 79.4, in the form of A − 79.4".
*Impact:* VERIFY wording only. It touches no arm, seed, pilot or wave-1 production.

### Category C

**C1 (required; the fixer's open question). l. 1468-1470, gate counts.** The expectation
`PREFLIGHT_ALL_PASS 66 production 64 pilot_only 2` is **not a defect**. It equals the full wave-1
set, 58 configs (56 production + 2 pilot-only; `cpu_gate_d25.log:119`; the bundle payload holds
the 58 configs, PREFLIGHT.md:60), plus FP32-E's 8. The shipped-bundle line 26 / 24 / 2 comes from
a different gate: `cpu_gate.py --only A,D,A07-350,C-PRIME,E1` (PREFLIGHT.md:164). By `grep` of
`cpu_gate_shipped_77f1ca4e.log`, that run covers A × 8, D × 8, A07-350 × 8, C′-s1 and E1-s1, and
none of B, C, F or R. So the two numbers are not comparable, and 66 is the right target for a
full-set gate.

The edited parenthetical is still misleading. It says neither that 26 / 24 / 2 is an `--only`
subset nor that B, C, F and R are absent from it. It also places "plus FP32-E's 8 configs" after
the 26, which invites the reading 26 + 8. Physics v7 C6 had given the purpose of fix 9g as "so
that B, C, F and R are not assumed gated", and the landed text does not meet that purpose.
*Fix:* rewrite the parenthetical as "(the full set, 58 and 56, `cpu_gate_d25.log:119`, plus
FP32-E's 8 configs, [A25]; the shipped bundle 77f1ca4e was gated only on the `--only
A,D,A07-350,C-PRIME,E1` subset, 26 / 24 / 2, `cpu_gate_shipped_77f1ca4e.log:55`, so B, C, F and R
are not yet gated on a shipped bundle)".

**C2. The fixer's own v7 change-log entry has no sha (l. 257-258: "Line numbers in the working
tree after this pass").** This repeats the pattern fix 9f cured. The numbers are correct at
fba27d5 (all checked). *Fix:* "(line numbers at fba27d5)".

**C3 (optional). Entropy tag at two figure sites.** l. 1216 ("entropy / log 64", wave-1
attention figure) and l. 1228 (FP32-E "entropy only") do not carry "(row-renormalized, [A26])".
v7 listed only l. 1117; the fixer also tagged l. 1345. [A26] governs the definition, so this is
cosmetic.

**C4 (optional). First-wave copy of the m paragraph (l. 1004-1009)** ends with "which is against
the thesis in the second wave". v7 prescribed it verbatim. It is not a defect, but in the
first-wave family (descriptive ladders, l. 1000) the direction sentence does not apply. Consider
"(second wave only)" if the paragraph is edited again.

**C5 (optional). Working point.** Fix 7 prints per-class signal efficiency at mistag 10⁻²
(l. 1104-1105, 1142-1143). The Metrics row (l. 1559) registers rejection at signal efficiency
0.5. Neither is wrong. If REPORT carries only one, it should say which.

## For the orchestrator, outside v8 scope (not a STUDY finding)

[A21] (l. 1917-1918) requires PREFLIGHT to re-assert `i_decay_speed` 0.001 "on the shipped tree on
the listed arms (A, B, C, D, F, R, A07-350, E1, NB)". No `cpu_gate_shipped_*` log covers B, C, F or
R: both shipped-bundle gates (c5d6f02a and 77f1ca4e) ran the `--only` subset. PREFLIGHT.md
records no pending full-set gate: `grep -n -i 'production bundle\|full gate\|B, C, F'` returned
nothing. `review/PREFLIGHT_critical_v2.md:13` reviewed only the subset line. This is a PREFLIGHT
prerequisite before wave-1 production: a full-set gate (no `--only`) on the bundle that ships
production, which prints `58 / 56 / 2`, or `66 / 64 / 2` with FP32-E. It does not affect the
pilot. It should go to the PREFLIGHT owner as a tracked item.

## Competing-group question

Within v8 scope, nothing new. The two items v7 named (paired AUC gaps, DSP-free comparands) have
landed (fixes 6 and 7).

## Disputed facts

None.
