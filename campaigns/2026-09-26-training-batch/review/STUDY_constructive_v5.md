# STUDY constructive review, v5 (diff-scoped, iteration 5)

Campaign `campaigns/2026-09-26-training-batch/`. Artifact `STUDY.md` at 355fb23. Scope, per
arbiter v4: `git diff caa009d 355fb23 -- STUDY.md`, mapped by the fix numbers in the newest
change-log entry (l. 114-145). A new A or B is raised only where it changes a number, a claim or
the design. Reviewer: constructive-reviewer, 2026-09-27, fresh context. Read: `review/STUDY_arbiter_v4.md`,
my `review/STUDY_constructive_v4.md`, the diff, `.claude/memory/decisions.md` (2026-09-27 entries),
`.claude/memory/research-log.md` 2026-09-01 (Sloot, FastML 2026). Checked in code:
`code/patches/0024-*`, `code/tree/bnhgq2/qat.py:420`, `code/tree/campaigns/chang0926/configs/chang0926-a-n64-s1.json:40`.
Other reviewers' v5 output not read.

## Status of my v4 findings, by name

| v4 | finding | status | where |
| --- | --- | --- | --- |
| B1 | size wave 2 from wave-1 sd | **Landed** | l. 794-813; table arithmetic rechecked (1.196 / 1.574 / 1.877 / 2.011 / 2.137 pt); Kai row l. 1629. Residuals: B3, C3, C4 below |
| B2 | A − NB headline as lower bound; Sloot prior | **Landed, one branch undefined** | l. 787-793; Sloot 0.9276 / 0.9178 matches research-log l. 457. Residual: B2 below |
| B3 | "non-degenerate" means about 21 %, not "tags" | **Resolved** | Question l. 53-55; Falsifier l. 701-706; pilot A rule |
| B4 | FP32 E arm as Kai option | **Resolved** | Scope l. 212-214; Kai row "FP32 E arm" |
| B5 | wave-2 epoch-500 rule | **Resolved** | Budget, second wave, "Epoch-500 rules" |
| B6 | NB in wave-1 seed blocks | **Resolved as a Kai row** (arbiter #13) | Kai row "NB in wave-1 seed blocks" |
| C1 | stale "not staged" [D20]; [D25] not staged | [D20] **resolved**; [D25] **now stale in the other direction** (C1 below) | confound 10, [D20], [A21] |
| C2 | PID signal still asked | **Resolved** | [D20] "PID signal" cites `ablation.py:698-703` |
| C3 | selection sentence vs code; W&B semantics | **Resolved** | l. 609-614 |
| C4 | Holm carries A − A07-350 | **Resolved** | l. 293, 769-775; reason stated (sign fixed by construction) |
| C5 | tag repetition; superseded FLAG block | **Resolved** | tag kept where the arbiter allowed; FLAG block shortened to three lines |
| C6 | Kai rows by what they block | **Resolved** | table l. 1617-1631 |
| C7 | selected epoch and cycle index | **Resolved** | Figures, per-run bullet |

## Category A

None. No selection on held-out, no projection stated as a result, no tautological comparison
added by the edits.

## What is done well (keep)

- [+] **Certification failure now has an outcome** (l. 619-641): a mismatch blocks VERIFY for the
  arm, is never a reason to reselect, and an unresolved seed joins one "no accuracy number" class
  with infeasible, degenerate and diverged seeds. Certification uses the same trace sample and
  batch as the per-epoch test, which closes the post-hoc second-selection route.
- [+] **H is one model end to end** (l. 449-453, [A23]): validation metrics, test (c) and the PID
  all read the reloaded traced clone, with a unit test that a fresh load reproduces the logged
  accuracy. That is the right test, not a prose promise.
- [+] **The budget claim reads as weak when it is weak** (l. 701-706): a count, the ~0.21
  threshold labelled as review arithmetic on ROC-test fractions, each seed's accuracy printed,
  and the sentence that "non-degenerate" is not "tags well".
- [+] **The attribution fix is correct for E** (l. 395-399): the 368,134 narrow floor is
  activation × activation (softmax 171,526 + scores 98,304 + context 98,304), and A − NB shares
  it. The residual on `xfm` is C2.
- [+] **A − A07-350 out of Holm with its reason**, and C − A07-350 kept in because its size is
  open (l. 769-775). Honest use of the family.
- [+] **WRAP-overflow label threshold fixed before any pilot number** (l. 848-855) and declared
  descriptive; binary scale factor β disclosed as outside native EBOPs ([L2]).
- [+] **Scope sentence** (l. 212-214) says plainly that no FP32/W8A8 cost and no activation
  ladder are measured.

## Category B

### B1. The low-accuracy-outlier count cannot see its own motivating case (arbiter v4 #11 not achieved)

- **Current state.** l. 762-768: an outlier is a seed "more than 3 pt below its arm's seed
  median". The same paragraph cites the Round-14 N=64 binary seeds 67.18 / 72.64 / 67.21 % as the
  failure the count must see.
- **Check.** Applied to those three seeds: median 67.21 %; 67.18 is 0.03 pt below it, 72.64 is
  above. **Zero of three flagged.** A median reference fails whenever half or more of the seeds
  are low, which is exactly the Round-14 pattern (two low, one good).
- **Improved state.** Keep it descriptive, outside the decision rule, but use a reference that
  survives a majority of low seeds: (i) per arm, seeds more than 3 pt below the arm's **best**
  seed (Round-14: 2 of 3 flagged), with the per-arm max − min beside it; and (ii) because the
  stability claim is A against D and they are paired by seed, a paired indicator: seeds where A is
  more than 3 pt below D at the same seed, and the converse, as a discordant count beside the
  McNemar count.
- **Why.** Arbiter #11 was raised to B because the claim could not detect its motivating failure;
  the fix as worded still cannot. The fixer used the arbiter's own wording, so this is a
  correction of the fix, not of the fixer.
- **Effort.** Low (text).

### B2. The A − NB headline sentence is wrong on one outcome branch

- **Current state.** l. 787-790: "binary costs at most |L| pt ... against learned-width weights".
- **Problem.** Correct only when L ≤ 0. If the whole interval lies above 0 (A better than NB),
  |L| is a lower bound on binary's advantage and the sentence states the reverse. Pre-registered
  headline text should cover every branch.
- **Improved state.** "If L ≤ 0: binary costs at most |L| pt ... If L > 0: no cost is resolved;
  A exceeds NB by at least L pt (n pairs, 95 %, iso-EBOPs, not iso-cost)."
- **Why.** The headline is the sentence a reader keeps; it must not flip meaning on a
  plausible outcome.
- **Effort.** Low.

### B3. The wave-2 epoch-500 sd_diff readout is an unblinded interim look with discretionary stop / extend on the thesis comparison; extra A seeds are not fenced off from A's own numbers

- **Current state.** l. 810-813 and the second-wave "Epoch-500 rules": the paired A − NB
  validation sd_diff at epoch 500 goes to Kai above 1.2 pt with the [D13] options continue /
  add seeds / stop. [D13]'s wave-1 packet puts the seed mean beside the sd (l. 572-580); for a
  paired gap the same packet would show the direction of A − NB. Extra A seeds 9..n (l. 810-811)
  are not stated to be excluded from A's arm summary, the k/8 budget count, the recipe claim or
  A − 79.4.
- **Improved state.** (i) The wave-2 readout packet carries sd_diff, the feasible-pair count and
  the n the sizing table gives, **not** the mean A − NB gap; the added-pairs n is read
  mechanically off the formula, capped by Kai's cap, not chosen. (ii) A "stop" on A − NB is
  reported as "stopped at epoch 500" with the interim validation sd_diff, never silently dropped.
  (iii) One sentence: "A seeds 9..n enter only A − NB; A's arm summary, budget count, recipe claim
  and A − 79.4 use seeds 1-8."
- **Why.** Sample size or stopping chosen after seeing an interim gap on the thesis-bearing
  comparison is the first thing a referee will question; variance-only re-estimation is the
  accepted form. Without (iii), a sizing decision can move a primary number.
- **Effort.** Low (text).

## Category C

- **C1. [D25] is now stale in the other direction.** `code/patches/0024-D25-opt-in-quant.i_decay_speed-*.patch`
  exists, `qat.py:420` implements the key, `chang0926-a-n64-s1.json:40` carries
  `"i_decay_speed": 0.001`, and `decisions.md` logs patch 0024 as staged (tree ac5a5c86). l. 326,
  327, 1340-1341 and 1500-1502 still say "not in the staged tree". Per the arbiter's
  conditional, say "set by patch 0024 (staged); PREFLIGHT re-asserts on the shipped tree".
  Also: STUDY asserts "0.01 on C′", while `decisions.md` says C′ has no WRAP quantizer, so no
  key is recorded there; the assertion is vacuous or fails. Reword as "C′: no WRAP quantizer,
  empty record". Low.
- **C2. `xfm` in the attribution parenthesis is untraced.** l. 395-396, 722 and [L2] extend the
  E-floor argument to "Sun et al.'s `xfm`". `xfm` has key_dim 16 against E's 12 (l. 319, 533), so
  its Q·K and A·V terms are larger (the scores term scales with key_dim: 98,304 = 2·64·64·12;
  review arithmetic by analogy, not traced), and H's floor has no number yet (l. 452-453). The
  direction is safe, but it is stated as fact. Reword: "on E, any weight type including NB;
  `xfm` (key_dim 16) is expected higher, traced at [A7]". Low.
- **C3. "Smallest A − NB the design resolves" is a half-width, not a detectable gap.** l. 795-796
  prints t(0.975, n − 1)/√n · sd_diff. A true gap of that size is detected about half the time;
  80 % power at df 7 needs about (2.365 + 0.896)/2.365 = 1.38 × that. Label it "95 % half-width"
  or give the 80 %-power figure beside it. The L-bound headline is already the correct statement. Low.
- **C4. Sizing table reads as steps.** Between rows (sd_diff 1.2-1.57) n = 9, 10 or 11 suffices;
  say "the formula governs; the table is illustrative". Low.
- **C5. Timing of the extra-pairs decision.** Kai row l. 1629 says it "blocks wave 2 (read at the
  wave-1 epoch-1,000 readout)"; the launch gate (l. 1107-1110) launches wave 2 after the wave-1
  epoch-500 pilot rule. Either wave 2 waits for epoch 1,000 of production (about 2 days at the
  187 s/epoch projection) or extra pairs are appended later as seeds 9..n. Say which. Low.
- **C6. Two numbering schemes in in-text tags.** "arbiter v4 #10" marks the scope sentence
  (l. 212, fix-list #10) and the figures (l. 870, 874, adjudication #10); the epoch-500 rule cites
  "#6, #9" (adjudication) while the change log calls it #7 (fix list). Use one scheme. Low.

## Disputed facts for the investigator

None.

## Recommendation to the arbiter

No A. Three text-only B (B1 corrects the #11 fix, B2 and B3 tighten the #8 and #6/#7 fixes). None
needs a new trace, config or Kai decision; all are one-paragraph edits.
