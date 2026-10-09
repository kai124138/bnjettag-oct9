# STUDY constructive review v9: 2026-09-26-training-batch

Constructive-reviewer, fresh context, 2026-09-27. Artifact `STUDY.md` at c2f5447 (working tree
equal, `git diff --stat c2f5447 -- STUDY.md` empty). Scope, per `STUDY_arbiter_v8.md`: fixes 1-5
landed verbatim at every listed site, with my v8 findings checked by name; a new B only if an
edited sentence is itself wrong. Diff read: `git diff 75ec0cc c2f5447 -- .../STUDY.md`.
`1115121..c2f5447` changes one line (the change-log sha).

## Fix landing, by site (line numbers at c2f5447 = 1115121)

All line numbers in the new v8 change-log entry (l. 281-297) were checked against the tree and match.

| fix | site(s) | landed | note |
| --- | --- | --- | --- |
| 1 FP32-E label | l. 1178-1179 | yes, verbatim | "worded as FP32-E − 79.4 (the same descriptive form as A − 79.4)" |
| 2 pilot amendment | l. 1374-1394; l. 1469; l. 2158; l. 2159 | yes, verbatim, all four sites | Sources resolve: `cluster-inventory.md:30` entry title matches the quoted name exactly; `RUN.md` l. 35/60 (A10, 23,028 MiB), l. 73 (`ARM_FAILED_AFTER_RETRIES`), l. 90 (18.8-22.6 GiB), l. 98 (C′-s1 on third attempt). 16 pods = (A, B, C, D, F, A07-350) × 8 / 3, correct |
| 3 collapse label | l. 1217-1228; l. 1412-1413 | yes, verbatim | Placed after the entropy bullet, before "Widths come from"; pilot readout names the label |
| 4 detectable gap | l. 1113-1119; l. 1100-1101; l. 2167 | yes, verbatim, three sites | Recomputed (`scipy.stats.nct`, df 7, δ·√8): power 0.796 at 1.15, 0.803 at 1.16; 1.16 · √2 · 3.145 = 5.16 pt → "about 5.2"; 1.16 · 1.19 = 1.38 → 1.4; 1.16 → 1.2. Correct |
| 5a gate counts | l. 1536-1541 | yes, verbatim | 58/56 attributed to the d25 full set, 26/24/2 named as the `--only` subset; the 26 + 8 misreading is gone |
| 5b v7 change-log sha | l. 256-257 | yes | "Line numbers at fba27d5:" (verified correct at fba27d5 in my v8) |
| 5c first Holm copy | l. 1028 | yes | Direction sentence deleted from the wave-1 copy only; second copy keeps it |
| 5d step-down clause | l. 1049-1050 | yes | "It leaves the Holm step-down order as well." |
| 5e Table 1 rows | l. 364-365 | yes, verbatim | Three Deep Sets (QKeras) rows named |
| 5f per-class legends | l. 1246-1247; l. 1267-1268 | yes, both figures | |
| 5g reference noise | l. 1237-1239 (caption); l. 961-963 (beside A − 79.4) | yes | The l. 961 copy uses the singular ("external reference ... its noise"), which fits one comparand; faithful |
| 5h attention figure | l. 1258-1260 | yes, verbatim | Split, n and the 0.99 cut now on the figure spec |
| change-log line | l. 281-284 | yes | Carries the arbiter's summary sentence and the sha 1115121 |

## My v8 findings, by name

| v8 | status at c2f5447 | evidence |
| --- | --- | --- |
| B1 FP32-E distance named "A − 79.4" | **resolved** | l. 1178-1179 (arbiter v8 fix 1) |
| C1 gate-count parenthetical (26 + 8 ≠ 66) | **resolved** | l. 1536-1541 (fix 5a) |
| C2 Holm paragraph, both families | **resolved** | (a) l. 1028; (b) l. 1049-1050 (fix 5c, 5d) |
| C3 Table 1 row names | **resolved** | l. 364-365 (fix 5e) |
| C4 10⁻² working point vs Metrics row | not applied; optional per arbiter v8 fix 6 | carries, optional |
| C5 typography (l. 1345 double paren; v7 log "working tree") | **resolved** | l. 1412-1413 now "entropy row-renormalized [A26], and the collapse label, ..."; l. 256-257 |
| Carried optionals (v7 C5 masked entropy, C6, C7; arbiter v7 #16, #17) | not applied; optional | carry |

## What is done well (keep)

- [+] The pilot amendment is dated, cites its evidence by file and entry name, applies a branch
  registered before the failure (K=3 re-canary), and refuses the one remedy that would change the
  arm (a smaller batch). The pilot, production and Kai's packing decision are kept apart.
- [+] The collapse label is fixed before any epoch-500 number exists, is descriptive only, and
  requires a mismatch on A07-350 (collapsed by construction) to be reported, not relabelled. This
  closes the forking path where a collapsed A could have been set beside a Deep Sets comparand
  with no label.
- [+] The detectable-gap sentence says in advance that "not falsified at this resolution" is the
  expected outcome at 8 pairs unless sd_diff comes in near 1 pt. A reader cannot take an
  unresolved A − NB as reassurance.
- [+] The reference's own noise now appears on the figure and beside the headline, not only in
  [L1].
- [+] The change log applies the fixes in the arbiter's order (2 first, since it was time-critical)
  and gives a correct line number for every site.

## Category A

None.

## Category B

None. No edited sentence is wrong. One point checked and not raised: amendment (1) says the K=3
pod launches once the full-set gate "on the shipped bundle" passes for C and F, and fix 5a says
B, C, F and R are "not gated on a shipped bundle until the full-set gate on the production bundle
passes". Both require a full-set gate on the bundle that ships, so they agree.

## Category C

None new. The arbiter v8 fix 6 optional items stay optional: crit C3, crit C5 / cons C4, phys C2,
C4, C5, C6, and v7 #16, #17.

## Disputed facts for the investigator

None.

## Recommendation to the arbiter

All five v8 fixes landed verbatim at every listed site, and every constructive v8 B and required C
is resolved. No new A or B. From the constructive side, nothing stands in the way of STUDY PASS. As
arbiter v8 states, a STUDY PASS does not by itself launch wave-1 production: that still needs the
full-set CPU gate ([A21]), the K=3 pod's A07-350-s1 readout and Kai's [D15] and packing answer.
