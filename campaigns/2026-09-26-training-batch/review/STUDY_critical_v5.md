# STUDY critical review v5: 2026-09-26-training-batch

Critical reviewer, fresh context, 2026-09-27. Panel mode, iteration 5, **diff-scoped** per
arbiter v4: `git diff caa009d 355fb23 -- STUDY.md` (265 +, 120 −), mapped by the fix numbers of
the newest change-log entry (STUDY l. 114-149). New A or B raised only where an edit changes a
number, a claim or the design. No verdict (the arbiter issues it).

Note on tree state: HEAD is now `d419b2d` (after `355fb23`), which commits patch 0024, the
[D25] configs (`chang0926-a-n64-s1.json:40` `"i_decay_speed": 0.001`), `qat.py` +31 lines,
`cpu_gate_d25.*`, `a17_pairing_d25_8seeds.json` and a `plan.md` handoff. STUDY.md is unchanged
between `355fb23` and HEAD, so its [D25] text now lags the tree (C4, B3 below).

## Validators (verbatim, `review/STUDY_validators_v5.txt`)

```
Desktop/bnjettag/campaigns/2026-09-26-training-batch/STUDY.md  —  score 0, reads human
  25395 words · 614 sentences · mean 25 words (σ=21.6) · 17% bullets · 0 em-dashes
plan.md present: yes; E1-TRACE-PENDING tokens: 0
Diff since v4 review (caa009d):  1 file changed, 265 insertions(+), 120 deletions(-)
```

No red flag. `tools/plot_check.py`: not applicable (STUDY has no figure scripts).

## Recomputed (review arithmetic, not results)

- Round-14 N=64 binary ROC-test top-1 from `bnjettag/roc-results/r14/n64/W1A8-s{1,2,3}.npz`
  (keys `y`, `score`, `meta`; shapes (260000, 5); n = 260,000; 0 NaN): **67.18 / 72.64 / 67.21 %**,
  matches STUDY l. 762. Median 67.21; seeds > 3 pt below the median: **0** (see B1).
- Sizing table (STUDY l. 802-808), largest sd_diff with t(0.975, n−1)/√n · sd ≤ 1.0 pt:
  n = 8 1.196, 9 1.301, 10 1.398, 11 1.489, 12 1.574, 13 1.655, 14 1.732, 15 1.806, 16 1.877,
  17 1.945, 18 2.011, 19 2.075, 20 2.137 (scipy). Table rows 1.20 / 1.57 / 1.88 / 2.01 / 2.14 are
  correct to rounding; intermediate n are skipped (C3).
- Threshold (c): 0.2023 + 5 · √(0.2023 · 0.7977 / 62,000) = **0.2104**; STUDY "about 0.21" (l. 701-706). Consistent.
- Pilot wall time: 500 × 112.6 s = **15.64 h**; 500 × 1.66 × 112.6 s = **25.96 h**; STUDY l. 1002-1003 "15.6 h / about 26 h". Consistent.
- Narrow floor E: 171,526 + 98,304 + 98,304 = **368,134** (STUDY l. 396-399). Consistent.
- Line citations checked in `code/tree/bnhgq2/ablation.py`: `:546` `d20 = ... 'ebops_trace_sample' is not None`;
  `:664` `feasible = budget_met and nondegenerate`; `:683-685` `model_best` copied only `if feasible`;
  `:686-692` [A19] AUC-feasible copy gated on `feasible`; `:698-703` PID-vs-trace assertion. All
  correct. `qat.py:56-65` absmean ±β, `:228-229` `_binary_kq` 1-bit pin: correct.
  `certify_ebops.py:12, 82` use the run's `ebops_trace_sample` split and `ebops_trace_batch`,
  REL_TOL 1e-6 (`:49`): matches the new certification sentence.
- Sloot prior: `.claude/memory/research-log.md:451-457`, HGQ 0.9276 vs binary 0.9178 AUC, hlf 16
  features, MLP, binary q/g vs W/Z/t: matches STUDY l. 790-794 ("different task").

## Arbiter v4 B findings, by name (adjudication # → change-log fix #)

| arb v4 # | finding | fix # | status | evidence |
| --- | --- | --- | --- | --- |
| 1 | certification failure outcome | 1 | **resolved** | l. 622-630 blocks VERIFY, unresolved = "no accuracy number", both EBOPs reported, same sample and batch; l. 643-645 class definition; arm summary "certified" l. 646-647. Code agrees (`certify_ebops.py:12, 82`) |
| 2 | H on the traced clone; H PID reads clone | 2 | **resolved (text)** | l. 445-453, fidelity row l. 473, [A23] per-epoch bullet and two CPU unit tests l. 1545-1550, Kai row l. 1626. No H code exists; the unit tests are the gate |
| 4 | budget-claim demotion | 3 | **resolved** | Question l. 53-55; Falsifier l. 701-706 count wording, threshold printed, per-seed accuracy; pilot A rule l. 1008-1010 |
| 5 | activation×activation floor attributed to binary weights | 4 | **resolved, with a new C** | three sites l. 395-399, 721-724, 1579-1582; the bundling of `xfm` into "E" is loose (C1) |
| 6/7 | A − NB resolution; sizing formula; epoch-500 sd_diff readout | 8 | **resolved, with a new B** | l. 800-819, Kai row l. 1629. Extra A seeds 9..n have no scope rule (B2); table granularity (C3) |
| 8 | lower-bound headline; Sloot prior | 6 | **resolved, with a new C** | l. 787-794; sign of |L| (C2) |
| 9 | wave-2 epoch-500 rule | 7 | **resolved** | l. 1135-1140, NB and H each, options named, "nothing else is decided" |
| 10 | pre-registered figures | 5 | **resolved, with a new C** | l. 870-876; 79.8 / 77.9 lines unnamed (C5) |
| 11 | stability counts only non-finite divergence | 9 | **text present; defective (B1)** | l. 761-766. The prescribed median-relative count returns 0 on the very R14 seeds it cites |
| 12 | scope sentence; FP32 row | 10 | **resolved** | Scope l. 212-214; Kai row "FP32 E arm" l. 1630; NB wave-1 row l. 1631 (#13) |

C items (#3, #14-#28), spot-checked: #3 PID signal l. 1293-1295 cites `:698-703` and `:546`
(correct); #16 selection sentence l. 609-615 matches `:664, 683-685` (correct) but the W&B half is
partly wrong (C6); #19 init EBOPs named by sample l. 1481-1487; #20 "identity" wording l. 382-384,
1393; #21 ROC figure split by budget l. 879-883; #22 A07 path 2,048 + 2,048 + 4,096 l. 176-177;
#25 Holm now four gaps, consistent at l. 293, 768-778, 1157, 1313 (no stale "five" found by grep);
#26 tag count now 7. #14 [D25]: logged in `decisions.md:22-33`; STUDY text stale since `d419b2d` (C4).

## Category A

None.

## Category B

**B1. The low-accuracy-outlier count cannot see its motivating failure mode.** STUDY l. 761-766
(arbiter v4 #11, fix 9). The count is "a seed whose selected checkpoint's validation accuracy is
more than 3 pt below its arm's seed median". On the cited R14 seeds (ROC-test, n = 260,000,
recomputed above) the median is 67.21 % and the count is **0**: two of three seeds are the bad
mode, so the median sits in it and the one good seed (72.64) is 5.4 pt *above*. A median-relative
rule is blind whenever half or more of an arm's seeds fall into the low mode, which is exactly
the R14 pattern the sentence invokes ("therefore gives"). The split differs (the rule is on
validation, the check on ROC-test); the logic is split-independent. This is a defect in the
prescribed rule, not in the fixer's execution. Impact: the stability paragraph claims a
descriptive coverage it does not have. Fix (still descriptive, not in the decision rule): add
per arm the seed range (max − min, validation, n = 62,000), and count seeds more than 3 pt below
the arm's **best** seed, or below the same-seed paired arm (A-s vs D-s); keep the median count if
wanted but state its blind spot in one clause.

**B2. Extra A seeds 9..n have no scope rule.** STUDY l. 810-811, Kai row l. 1629 (arbiter v4
#6/#7, fix 8). "Pairs beyond 8 need extra A seeds (9 to n)". No sentence says whether these
seeds enter A's k/8 budget count, A's seed mean and A − 79.4, the recipe claim, the four Holm
secondary gaps or the stability count. If Kai takes the option, the first-wave headline could be
recomputed on n > 8 seeds trained later, on other pods and dates (the extra-pairs decision is
"read at the wave-1 epoch-1,000 readout", after wave 2's 8 pairs launch at the epoch-500 pilot
gate, l. 1107-1109), which would change a number and break "8 seeds" in every first-wave rule.
Fix: "A seeds 9..n enter A − NB only; every first-wave claim and gap is fixed at seeds 1-8;
extra A and NB seeds of a pair train on the same pod, GPU class stated". And the Kai row's
"blocks wave 2" should read "blocks the extra pairs, not the 8-pair launch".

**B3. The [A21] / [D25] gate asserts a value C′ cannot carry.** STUDY l. 327 (fidelity row),
l. 1341 ([D25]), l. 1502 ([A21]) and `decisions.md:33` (Check line): "PREFLIGHT asserts ... 0.01
on C′". The ml-engineer handoff at HEAD (`plan.md:567-572`) records that C′ has no WRAP
quantizer, so no quantizer carries `i_decay_speed` (`cpu_gate_d21.json` recorded `{}`), and the
gate actually asserts "no key, no carrier, empty record". A pre-registered PREFLIGHT gate whose
stated value cannot occur either fails or gets waived at PREFLIGHT. Fix (text, three sites plus
the decisions.md Check line): "0.001 on every carrier in the listed arms; C′: no key, no carrier,
empty record".

## Category C

**C1.** l. 395-397, 721-722, 1579-1580: "the 2-head E architecture under [D19] (any weight type,
including NB and Sun et al.'s `xfm`)" folds `xfm` into E and its 368,134 floor, but `xfm` has
key_dim 16 against E's 12 (l. 319, 533) and H's floor is untraced (l. 452-454). By arithmetic
(review, if the Q·K and A·V terms scale with key_dim) xfm's would be larger, so the direction holds.
Fix: restrict the sentence to A and NB; "`xfm` is expected to be at least as constrained, traced at [A7]".

**C2.** l. 787-789: "binary costs at most |L| pt" reads wrong if L > 0 (the interval excludes
any cost). Use max(0, −L), and say "no cost resolved" when L ≥ 0.

**C3.** l. 802-808: the table skips n = 9-11, 13-15, 17, 19 (1.30, 1.40, 1.49, 1.66, 1.73,
1.81, 1.95, 2.08), so a proxy of 1.25 reads as 12 pairs when 9 suffice. State that the formula
governs, or list every n from 8 to 20.

**C4.** l. 327, 1339-1341, 1497-1502: "not yet in code", "the staged tree still has 0.01",
"patch 0024 not in `code/patches/`" were true at `355fb23` and are stale at HEAD `d419b2d`
(0024 committed; config l. 40 = 0.001; `cpu_gate_d25.log`, `a17_pairing_d25_8seeds.json` exist).
Per arbiter v4 fix 12's conditional, l. 284-equivalent text now stands; cite the d25 evidence
and note that the "predate [D25], re-run under it" item (l. 111-113) is done on CPU.

**C5.** l. 871-873: the figure's 79.8 % and 77.9 % lines are unnamed; label them Linformer and
MHA-64 (single-model, external) as l. 230 does.

**C6.** l. 612-614: "In the per-epoch log and W&B, `budget_met` means (a) to (c)". True for the
per-epoch history (`ablation.py:711`), false for the W&B run **summary**, where `budget_met` is
the raw (a) test on the delivered checkpoint (`:779`, `:806`), including the
`model_min_ebops.keras` fallback. Same key, two semantics in one W&B run. Fix: name the summary
key as raw, and state that k is counted from `selection != minimum_ebops_no_feasible_checkpoint`
plus the certification record, never from any `budget_met` field.

## Competing-group question (scoped)

Within the diff, nothing a competing group would have that this design lacks beyond what the
v4 panel already routed to Kai (FP32 E arm, extra pairs). B2 is the one edit that could let a
later decision alter a first-wave number.

## Disputed facts

None.
