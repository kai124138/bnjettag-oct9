# STUDY critical review v7: 2026-09-26-training-batch

Critical-reviewer, panel mode, fresh context, 2026-09-27. Iteration 7. Scope is binding per
`review/STUDY_arbiter_v6.md` ("v7 scope"): arbiter v6 fixes 1-11 landed as written at every
listed site; fix 10's script and tests exist with a pass line; the text pass after PREFLIGHT gate
v2 (change-log entry "v6, text pass after PREFLIGHT gate v2", STUDY.md:247-254). A new B only
where an edited sentence is itself wrong. No verdict (the arbiter issues it).

Artifact: `STUDY.md` at 5c49230 (2,205 lines; working tree equals 5c49230, `git diff --stat
5c49230 -- STUDY.md` empty). Diff read: `git diff 09e0d8c 5c49230 -- STUDY.md` (222 +, 63 −;
commits 99f0a2d fixer, 5c49230 text pass). Also read: `code/analysis/attn_entropy.py`,
`code/analysis/test_attn_entropy.py`, `code/evidence/pytest_shipped_77f1ca4e.log`,
`code/evidence/a17_pairing_d25_8seeds.json`, `code/patches/0026-*.patch`,
`code/tree/campaigns/chang0926/certify_ebops.py`, `configs/chang0926-a-n64-s1.json`,
`PREFLIGHT.md`, `review/PREFLIGHT_critical_v2.md`, `.claude/memory/decisions.md` (top three
entries).

## Validators (`review/STUDY_validators_v7.txt`, verbatim)

```
Desktop/bnjettag/campaigns/2026-09-26-training-batch/STUDY.md  —  score 0, reads human
  31581 words · 792 sentences · mean 25 words (σ=21.7) · 17% bullets · 0 em-dashes
Diff since v6 review (09e0d8c):  1 file changed, 222 insertions(+), 63 deletions(-)
```

No red flag. No figures at STUDY, so no `plot_check.py` output applies.

## Arbiter v6 fixes, site by site

| fix | site(s) the arbiter listed | landed at (STUDY.md @5c49230) | verbatim? | status |
| --- | --- | --- | --- | --- |
| 1a | "Paired gaps" bullet | 825-830 | yes | landed |
| 1b | A − NB headline; precision-package headline | 985-996; 1059-1067 | yes, both | landed |
| 1c | A/FP32-E feasibility counts + McNemar under "Precision package" | 1076-1077 | yes | landed |
| 2 | Budget FP32-E launch rule | 1438-1446 | yes (K=8 clause re-worded to "a K=8 re-canary passes (i) to (iii) at K=8") | landed |
| 2 | NB Kai row | 2022 | yes | landed; one residual clause, C1 |
| 2 | FP32-E Kai row | 2020 | yes | landed |
| 2 | [D26] DECISION block | 2111-2112 | yes | landed |
| 2 | change-log line | 219-221 | yes | landed |
| 2 (extra) | Overlap bullet, NB at K=7 | 1409-1411 | consistent with fix 2 | landed |
| 3 | precision claim string | 1047-1050 | yes | landed |
| 3 | FP32-E headline, L ≤ 0 / L > 0 branches | 1051-1057 | yes | landed |
| 3 | "at least \|U\|" gated on the Holm verdict, both headlines | 985-986 ('falsified'); 1053-1055 ('resolved cost') | yes | landed |
| 3 | Scope | 324-326 | yes | landed |
| 3 | Question | 276 and frontmatter `question:` l. 6 | yes ("what is A − FP32-E?") | landed |
| 3 | Null H0-precision / Bearing | Null l. 295 has no "close" (unchanged, correct); Bearing l. 317 | aligned | landed |
| 4 | plausibility line | 1079-1083 | yes | landed |
| 4 | FP32-E epoch-500 rule | 1460-1462 | yes | landed |
| 5 | FP32-E "Checks replacing the binary gate" | 562-565 | yes | landed |
| 5 | conventions row "Validation checks 1-4" | 1497 | yes | landed |
| 5 | [D26] body | 1688-1691 | yes | landed |
| 5 | [D26] DECISION block | 2107-2110 | yes | landed |
| 5 | [A25] pinned-0.1.9 bullet | 1938-1939 | yes | landed |
| 5 (sweep) | any remaining "no quantizer variables in any layer" | `grep` returns only the four amended sites (562, 1497, 1689, 2108) | — | none left |
| 6 | [A25] `binary_gate` bullet | 1940-1941 | yes | landed |
| 6 | [A22] `binary_gate` bullet | 1874-1875 | yes | landed |
| 6 | conventions row cites both | 1497 | yes | landed |
| 7 | [A25] pairing count | 1929-1933 | yes | landed |
| 8 | [A25] stripped keys + PREFLIGHT diff | 1913-1916 | yes | landed |
| 9 | conventions rows Configurations / Cost accounting / Selection under a budget | 1494-1496 | yes, all three | landed |
| 10 | [A26] definition | 1942-1951 | yes, plus the arbiter's "pending" fallback | landed; definition stale against the script, B1 |
| 10 | "softmax tap" replaced | 1121-1122 | yes | landed |
| 10 | pilot readout "pending" | 1277-1281 | yes | landed (moot: script and tests exist, below) |
| 11 | [D24] DECISION block | 2121-2122 | yes | landed |
| 11 | second-wave Cost bullet | 1415 | yes | landed; C2 |
| 11 | Holm price sentence | 975-978 | yes | landed |
| 11 | second-wave Launch gate: [A25], per-arm launch, gate line | 1392-1400 | yes | landed; count checked below |
| 11 | splices l. 895-896, l. 393, 1543, 1712 | 950-951; 446-447; 1673-1674; 1845 | fixed, one clause each | landed |
| 11 | second-wave figure, separate panels | 1156-1158 | yes | landed |
| 11 | designer [D26] entry in `decisions.md` with Check line | `decisions.md` entry "2026-09-27 (experiment-designer [D26], logged by fixer after STUDY arbiter v6)", Check line present | — | landed |

Checks with numbers behind them:
- **Fix 10 script and tests exist, with a pass line.** `code/analysis/attn_entropy.py` (322
  lines) and `code/analysis/test_attn_entropy.py` (176 lines). `pytest_shipped_77f1ca4e.log:65-71`:
  `test_uniform_logits_give_one` and `test_one_hot_logits_give_zero` PASSED on the `a`, `cprime`
  and `fp32` builds, `test_main_on_snapshot_layout[a]` PASSED; l. 73: `71 passed, 2 skipped in
  79.75s`; the two skips (l. 72) are `main()` on the C′ build, justified in the log. Layer name
  `_attn_softmax` (script l. 75) matches the STUDY's `{blk}_attn_softmax`; load path
  `load_model(path, compile=False)` (script l. 210); normalization `N_KEYS = 64`, `log S`.
- **Fix 7 count.** `a17_pairing_d25_8seeds.json`: `n_shared` 15 and `only_in_arm` [] at a-s1 ...
  a-s8. In that file `only_in_f` is `['pos_enc/pos_table']` at every seed, but there `f` is arm
  F (E + learned PE; STUDY.md:408, 667), so the empty-`only_in_f` condition for FP32-E (no PE on
  either side) is satisfiable. Not a defect.
- **Fix 7 identifiers.** `matching_initialization` (`code/tree/bnhgq2/ablation.py:70`) calls
  `qat.calibrate_activations` (l. 76; defined `qat.py:649`) and `expected_binary_layers` (l. 89;
  defined `ablation.py:325`); `kernel_hashes` is built at `ablation.py:121` and read by
  `campaigns/chang0926/check_pairing.py:27`. Every name in the edited sentence exists.
- **Fix 5 numbers.** `_table` (`qat.py:358-360`): `kif`, `k0=0`, `i0` and `f0` as passed,
  `overflow_mode="SAT"`, `trainable=False`; the fp32 softmax passes `_table(1, 20)` for both
  exp and inv outputs (`qat.py:517`). "k0 0, i0 1, f0 20, SAT" at the four sites is correct.
- **Fix 8 key names.** `act_policy` (l. 30), `act_calib` (l. 32), `act_overflow` (l. 38),
  `softmax_quant` (l. 39), `i_decay_speed` (l. 40) all exist in `chang0926-a-n64-s1.json`.
- **Fix 11 gate line.** `PREFLIGHT.md:144` and `cpu_gate_d25.log` give `PREFLIGHT_ALL_PASS 58
  production 56 pilot_only 2`; 58 + 8 = 66, 56 + 8 = 64. The STUDY's expected line matches.

## Text pass after PREFLIGHT gate v2

| item | STUDY.md | source | status |
| --- | --- | --- | --- |
| flag 2, stage-aware run id | 1473-1480 | patch 0026 l. 64: `key = f"{stage}\0{name}"`, sha256[:12]; `RUN_STAGE` refusal l. 55, 109 | id rule correct; group sentence wrong for wave 2, B2 |
| decision 6, CPU→GPU re-run, four conditions | 1288-1296; Selection rule 799-801 | `decisions.md` top entry, conditions 1-4 | matches verbatim in substance; citation C3 |
| flag 3, readout dry run | 1297-1301 | `PREFLIGHT_critical_v2.md:51` | matches |
| flag 4, replay after cross-class re-create | 1302-1306 | `PREFLIGHT_critical_v2.md`, `decisions.md` top entry | matches |
| change-log refs of the text pass | 249-254 | l. 1473-1480, 1288-1296, 799-801, 1297-1301, 1302-1306 | correct |

## Findings

### Category A

None. Validators clean; every arbiter v6 A and B fix landed at its listed site.

### Category B

**B1. [A26] definition in STUDY does not match the script's primary quantity.** STUDY.md:1942-1948
defines the readout as "the mean over jets and query rows of −Σ p log p over the 64 keys, divided
by log 64, from the quantized softmax output as the model computes it", with no renormalization.
The script's primary is `p = q / sum(q)` (row-renormalized; `attn_entropy.py:12-18, 64-68`), with
the raw `−Σ q log q / log S` reported beside it (l. 70), and `decisions.md` (entry "2026-09-27
(ml-engineer, PREFLIGHT gate v1 fixer + [A26])") records why: the fixed-softmax build emits rows
summing to 4.0 under uniform logits, raw value 2.67. Read as written, STUDY's own unit-test clause
("uniform logits give 1 within 1e-6", l. 1948) is false for the C′ build, and passes only for the
renormalized quantity (`pytest_shipped_77f1ca4e.log:68`, `[cprime]` PASSED). This is the
pre-registered definition of a quantity the pilot readout prints, so the STUDY must name the one
the code computes. Impact: a reader of VERIFY cannot tell which entropy is primary; A07-350's
attention expectation is read beside it. Fix (one clause, after "divided by log 64"): "with p the
softmax-layer output divided by its row sum (primary; the fixed-softmax build does not emit rows
summing to 1, `decisions.md` 2026-09-27 [A26]); the un-renormalized value and the row-sum
min / mean / max are printed beside it". Routing: a STUDY clause for the fixer, not a code change;
the script's renormalized primary has a logged reason, so the STUDY takes the code's definition.

**B2. W&B group rule hard-codes the wave-1 canary group.** STUDY.md:1476-1477: "pilot and canary
log into `chang-n64-20260926-canary`, production into the config's group". Code: pilot/canary
group = config group + `-canary` (patch 0026 l. 49, 69-70; test l. 143 asserts
`stage_group('chang-n64-20260926-wave2', 'canary') == 'chang-n64-20260926-wave2-canary'`). As
written the sentence contradicts the code for the second wave and STUDY's own second-wave canary
group (l. 1418-1419, 1467). Impact: small (code is right; the text would misroute a reader
looking for wave-2 canary runs). Fix: "pilot and canary log into the config group with
`-canary` appended (`chang-n64-20260926-canary`; wave 2 `chang-n64-20260926-wave2-canary`),
production into the config's group".

### Category C

**C1. Residual pre-fix-2 wording in the NB Kai row.** STUDY.md:2022, last cell: "If NB and FP32-E
both qualify and K=8 does not fit" still uses the memory-only wording fix 2 replaced elsewhere
(Budget l. 1445 now reads "unless a K=8 re-canary passes (i) to (iii) at K=8"). Fix: "and a K=8
re-canary does not pass (i) to (iii)".

**C2. Second-wave Cost bullet reads as if K=6 costs the same as K=4.** STUDY.md:1415: "16 runs at
K=4 on 4 pods (24 runs at K=6 with FP32-E, same pods) ≈ 4 × 218.9 h ≈ 876 pod-hours". The
parenthesis is arbiter v6's prescribed text; the 876 is the K=4 projection, and the FP32-E Cost
sub-bullet (l. 1454-1457) already says "a larger K may raise s_e". Not wrong in substance.
Fix, optional: append "(K=4 projection; K=6 s_e from the second-wave canary)".

**C3. Citations in the decision-6 text.** STUDY.md:1293 cites `certify_ebops.py:89-90`; the label
precedence that masks `STORED_MISMATCH` behind `EBOPS_MISMATCH` is l. 90-91 (l. 89 computes
`stored_equal`). STUDY.md:800 locates the rule "at the top of `.claude/memory/decisions.md`";
that file is newest-on-top, so "top" will drift. Fix: `certify_ebops.py:89-91`; cite the entry by
its heading ("2026-09-27 (orchestrator, PREFLIGHT gate v2)").

**C4. Fixer-pass change-log line numbers are stale.** The fixer entry (STUDY.md:209-243) says
"Line numbers after this pass", but the text pass then added about 10 lines above most sites, e.g.
"Paired gaps" cited l. 818-820, now 828-830; [A26] cited l. 1905-1914, now 1942-1951. Fix:
refresh, or say "at 99f0a2d".

## Earlier findings (arbiter v6), by name

| v6 # | finding | status at 5c49230 |
| --- | --- | --- |
| 1 (A) | survivor bias in both second-wave headlines and Paired gaps | resolved (fix 1, l. 825-830, 985-996, 1059-1067, 1076-1077) |
| 2 (B) | K=7 join gated on memory only | resolved (fix 2, l. 1438-1446, 1409-1411, 2020, 2022, 2111-2112); residual wording C1 |
| 3 (B) | "close" claim with no margin | resolved (l. 1047-1050, 317, 324-326) |
| 4 (B) | L > 0 branch hid the sign | resolved (l. 1055-1057, investigator route) |
| 5 (B) | \|U\| against the Holm verdict | resolved at both headlines (l. 985-986, 1053-1055) |
| 6 (B) | FP32-E plausibility | resolved (l. 1079-1083, 1460-1462) |
| 7 (B) | quantizer-variable check could not pass | resolved at all five sites; no stale site left |
| 8 (B) | `binary_gate` for FP32-E and NB | resolved (l. 1874-1875, 1940-1941, 1497, 565) |
| 9 (B) | pairing count | resolved (l. 1929-1933; evidence count 15 confirmed) |
| 10 (B) | config hygiene | resolved (l. 1913-1916; key names confirmed in A-s1 config) |
| 11 (B) | conventions rows | resolved (l. 1494-1496) |
| 12 (B) | attention entropy had no implementation | resolved: script, tests, pass line (`pytest_shipped_77f1ca4e.log:65-73`); definition text stale, B1 |
| 13-20 (C) | DECISION block, Cost, Holm price, [D26] entry, launch gate, splices, figure | applied (table above); optional C items not applied, as allowed |

## Motivated-reasoning check on the new text

B1 is neutral in direction (it changes which entropy is primary, not a gap). B2 has no bearing on
any number. No edited sentence restores a thesis-favourable default: "close" appears only in
"never ... as a verdict" constructions (l. 317, 324-325, 1050) and in quoted [D26] reason text
(l. 1695), none of which issues a verdict.

## Competing-group question

Unchanged from arbiter v6 ("Nothing else missing that STUDY does not name as a limitation or Kai
row"); the three items it named (no "close" verdict, measured K=7 timing, reference-arm sanity) are
now in the text.

## Bearing on the pilot and wave-1 production

B1 bears on the pilot's epoch-500 readout wording only (the script already computes the recorded
quantity; no pod or bundle change). B2, C1-C4 bear on nothing that trains.
