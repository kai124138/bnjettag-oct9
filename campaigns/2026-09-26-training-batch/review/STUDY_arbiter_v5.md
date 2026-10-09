# STUDY arbiter v5: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-27. Artifact `STUDY.md` at 355fb23 (1,800 lines; unchanged at HEAD
d419b2d), `plan.md`, `code/` (patches 0001-0024 at d419b2d), `code/evidence/`. Reviews v5
(diff-scoped, caa009d..355fb23): `STUDY_physics_v5.md`, `STUDY_critical_v5.md`,
`STUDY_constructive_v5.md`. Validators `STUDY_validators_v5.txt`: `prose_lint` score 0,
`E1-TRACE-PENDING` 0, no A line. No figures at STUDY, so no plot-validator file. Earlier arbiter
`STUDY_arbiter_v4.md`. Read `06-review.md` §6.1-6.8 and `decisions.md:80-100` (Kai, 08:40).
Iteration **5** (strong-warn tier, §6.5).

## Independent checks made by the arbiter

- **Outlier rule (crit B1, cons B1).** STUDY l. 761-766: "more than 3 pt below its arm's seed
  median". On the cited R14 seeds 67.18 / 72.64 / 67.21 % (ROC-test, n = 260,000, recomputed by
  critical and physics) the median is 67.21 and 0 of 3 seeds are flagged. The rule is blind
  whenever half or more of the seeds are low. The defect is in arbiter v4's prescribed wording,
  not in the fixer's execution; this file therefore prescribes verbatim text, checked on that case.
- **A07-350 expectation (phys B1).** `static_floors_arms_s1_d25.json`, `chang0926-a07-350-n64-s1`,
  `one.per_layer`: `input_proj` 6,144, `ffn_fc1` 65,536, `ffn_fc2` 65,536, `head_fc1` 1,024,
  `head_fc2` 160. The post-pool head costs 32 EBOPs per input channel at 1 bit, against 2,048 for a
  per-constituent channel. l. 711-714 ("at most three 1-bit `input_proj` or d32 dense input channels
  in total", mismatch = defect) can fire on a floor-consistent checkpoint. The pilot applies it to
  A07-350-s1 at epoch 500 (l. 1018-1019).
- **C′ `i_decay_speed` gate (crit B3, phys C2, cons C1).** `cpu_gate_d25.log:116`:
  `I_DECAY_OK chang0926-cprime-n64-s1 config None quantizers 0 values []`. STUDY l. 327, 1341, 1502
  and `decisions.md:33` pre-register "PREFLIGHT asserts ... 0.01 on C′", a value no C′ quantizer
  carries.
- **[D25] staging.** Patch 0024 is committed at d419b2d; STUDY l. 326-327, 1340, 1500 still say
  "not yet in code" / "staged tree still has 0.01". Stale in the other direction (arbiter v4 fix 12's
  conditional now resolves to "stands").
- **`budget_met` (crit C6).** `ablation.py:711` per-epoch `budget_met = int(feasible)` (a)-(c);
  `:779` `result['budget_met'] = measured['total'] <= final_target` and `:806` pushes it to the W&B
  summary. STUDY l. 612-613 says W&B `budget_met` means (a)-(c): wrong for the summary. k is defined
  by the "no accuracy number" class (l. 630-641), not by any `budget_met` field, so no number moves
  today; the text still invites the wrong read. C, required.
- **Stale citations (phys C1).** `code/evidence/cpu_gate_final.json` (STUDY l. 233) does not exist
  (`ls code/evidence/`); l. 1396-1398 says `static_floors_arms_s1.json` still holds B at A07 175k,
  which the d25 file no longer does.
- **Sizing table (phys C3, crit C3, cons C4).** Thresholds 1.196 (8), 1.574 (12), 1.877 (16),
  2.011 (18), 2.137 (20) pt (critical, scipy). The rows "≤ 1.20" and "≤ 1.88" fail their own
  criterion by rounding; "1.20" also at l. 554, 1799; "1.2 pt" trigger at l. 812, 1139.
- **Orchestrator's claim** (no remaining B changes a config, seed, target, pilot composition or
  what is trained): **confirmed**. Every fix below is STUDY or `decisions.md` text. The extra-pairs
  option was already a Kai row; the fence below narrows it. Pilot composition (l. 979-983, job
  indices `[0, 1, 24, 48, 56, 57]`) is untouched. Physics C7 (sign-flip logging) would touch code
  and is routed as an optional ml-engineer item, not a STUDY fix.

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Low-accuracy-outlier count (median-relative) flags 0 of 3 on its own motivating R14 case | crit B1, cons B1, phys C4 | B, B, C | **B** | Case 1/2; recomputed (0 of 3). Arbiter v4 #11 not resolved; keeps B. Fix 1 |
| 2 | Extra A seeds 9..n not fenced from first-wave numbers; wave-2 epoch-500 readout is an unblinded look with discretionary add/stop; Kai row timing ("blocks wave 2", read at wave-1 epoch 1,000) | crit B2, cons B3, cons C5 | B, B, C | **B** | Case 1. A later sizing decision could move A's k/8, mean and A − 79.4. Fix 3 |
| 3 | sd_diff proxy (A − D) probably understates A − NB; wave-2 readout should bind | phys B3 | B | **B** | Case 3; NB prunes to 0 bits and runs its own PID path ([A22]). Merged into fix 3 |
| 4 | A − NB headline "costs at most \|L\| pt" inverts meaning when L > 0 | cons B2, crit C2, phys C6 | B, C, C | **B** | Case 2, with constructive: the pre-registered headline is the sentence a reader keeps, and L > 0 is a reachable branch. No independent evidence lowers it. Fix 2 |
| 5 | [A21]/[D25] gate asserts "0.01 on C′", which no C′ quantizer carries | crit B3, phys C2, cons C1 | B, C, C | **B** | Case 2, with critical: a pre-registered PREFLIGHT gate that cannot pass as written would be waived at PREFLIGHT. `cpu_gate_d25.log:116` settles the fact. Fix 5 |
| 6 | A07-350 expectation counts the post-pool head as "d32 dense input channels"; can flag a correct checkpoint | phys B1 | B | **B** | Case 3; verified on the d25 JSON. The only pre-registered defect trigger, evaluated in the pilot. Fix 4 |
| 7 | No evidence on the thesis's first axis (no FP32/W8A8); REPORT use not restricted | phys B2 | B | **B (text)**; arm stays Kai option | Case 3. The scope sentence (l. 212-214) says what is not measured, but nothing bars REPORT from citing the campaign for "close to full precision". Fix 6. Running FP32 E is Kai's (compute) |
| 8 | [D25] text stale at HEAD (patch 0024 committed) | crit C4, cons C1, phys C1(b) | C | C (required, with fix 5) | Verified. Fix 5 |
| 9 | `cpu_gate_final.json` absent; `static_floors_arms_s1.json` description stale | phys C1(a,c) | C | C | Verified. Fix 7 |
| 10 | W&B summary `budget_met` is raw; k source unstated | crit C6 | C | C (required) | Verified at `:711, :779, :806`. Fix 7 |
| 11 | Sizing-table rounding and granularity | phys C3, crit C3, cons C4 | C | C (required, with fix 3) | Verified arithmetic |
| 12 | `xfm` folded into the E floor sentence | crit C1, cons C2 | C | C | key_dim 16 vs 12; untraced |
| 13 | Figure lines 79.8 / 77.9 unnamed | crit C5 | C | C | |
| 14 | "Smallest resolvable" is a 95 % half-width, not an 80 %-power gap | cons C3 | C | C | |
| 15 | Two numbering schemes in amendment tags | cons C6 | C | C | |
| 16 | Certification checks determinism, not accounting; run [A14] on selected A-s1 | phys C5 | C | C (optional) | Adds a VERIFY step; cheap; fixer may add one sentence |
| 17 | Absolute accuracy line beside the mean | phys C4 | C | C (optional) | Largely covered by fix 1 (best-seed reference, range) |
| 18 | Sign-flip fraction and latent \|w\| logging for A and D | phys C7 | C | C (optional, ml-engineer) | Touches code; descriptive; not a STUDY fix |

## Earlier A and B findings (arbiter v4), by name

| v4 # | finding | status | evidence (arbiter's own line check) |
| --- | --- | --- | --- |
| 1 | certification failure outcome | **resolved** | l. 622-630 (blocks VERIFY, no reselect, "no accuracy number", both EBOPs), l. 637-641 class; `certify_ebops.py` uses the run's sample and batch (critical, `:12, 82`) |
| 2 | H on traced clone; H PID reads clone | **resolved (text; code gated)** | l. 445-453; [A23] l. 1545-1550 two CPU unit tests. No H code yet; the unit tests are the PREFLIGHT gate |
| 4 | budget-claim demotion | **resolved** | l. 700-706 count wording, threshold printed, per-seed accuracy, "does not mean the model tags well"; pilot A rule l. 1008-1010 |
| 5 | activation×activation floor attributed to binary weights | **resolved** (residual C #12) | l. 721-724 "any weight type ... Q·K and A·V streams may prune"; A − NB shared floor stated |
| 6/7 | A − NB resolution, sizing formula, epoch-500 readout | **resolved as written; new B #2, #3** | l. 795-813, l. 1139-1140, Kai row l. 1629 |
| 8 | lower-bound headline; Sloot prior | **resolved except sign branch (new B #4)** | l. 787-794; Sloot 0.9276 / 0.9178 matches research-log (critical, constructive) |
| 9 | wave-2 epoch-500 rule | **resolved** | l. 1135-1140 NB and H, options named, "nothing else is decided" |
| 10 | pre-registered figures | **resolved** (residual C #13) | l. 869-876 |
| 11 | stability counts only non-finite divergence | **not resolved**, stays B (#1) | l. 761-766; 0 of 3 R14 seeds flagged |
| 12 | scope sentence; FP32 row | **resolved** (new B #7 is the REPORT-use restriction) | l. 212-214; Kai row l. 1630 |
| 13 | NB in wave-1 blocks (Kai option) | **resolved as Kai row** | l. 1631 |

## Regression triggers (§6.7), checked independently

STUDY is the origin phase; no result exists. Selection on held-out or changed after results: not
met (validation only; `ablation.py:664, 683-685`; threshold (c) fixed before any pilot number,
l. 603-607). Val/ROC-test AUC > 0.01, single-seed headline, cross-N series, gap < sd at < 3 seeds:
not met (no numbers). Reload > 1e-7 / TF32: not met (stored-state reload check). EBOPs not
remeasured: not met (certification l. 619-630). Binary > 2 values: not met (`binary_gate`, `:775`).
DSP / C-sim / C-synth: not applicable. Per-class AUC hidden: not met (per-class required).
Byte-identical arms / different `y`: not met (`a17_pairing_d25_8seeds.json`, 8 seeds, 0 of 15
shared variables differing). Failed validation or tautological comparison: not met (the PID
tautology is reported as a count, l. 653-656; the near-trivial (c) threshold carries no claim).
[D] replaced without dated amendment: not met ([D25] dated in STUDY and `decisions.md:22`).
Outward mismatch: not applicable. **No trigger met.**

## Disputed facts for the investigator

None. Every factual disagreement was settled on files cited above.

## Dismissals

None.

## Motivated-reasoning check

Two of the four open B items were thesis-favourable by default: a median-relative outlier count
that reports "0 outliers" on the very bimodal failure it was added to see, and a headline sentence
whose only well-formed branch is the one where binary is worse (so a good outcome would be misread
by the reader, and a stop or add-seeds call at the wave-2 readout could be made after seeing the
gap). Fixes 1-3 close all three. Nothing inflates an interval; pairing is used where arms pair.

## Verdict

**ITERATE** (STUDY panel, iteration 5 → fixer, then v6). No A; six open B (#1-#7, #2 and #3
merged), all text. **Strong warning (§6.5, iteration 5).** Each of the last two rounds found
defects in the previous round's prescribed wording; to stop that loop, this file gives verbatim
replacement text, each sentence checked against the case a reviewer used (below). ESCALATE is not
the verdict: there is no disputed A, no falsified claim, no resource wall, and the cap is 10. One
process question does need Kai (next section).

**One fixer pass closes it.** v6 scope, binding on the panel: reviewers check only that each fix
below landed as written at every listed site and that no listed site was missed; a new B only if
an edited sentence is itself wrong (a number, a sign, a contradiction with code). No new scope.
A v6 finding that restates an item adjudicated here by name (for example the FP32 arm, #7, or the
Kai options) is closed by citation to this file, not re-fixed; the physics-reviewer does not see
earlier reviews (§6.2), so such restatements are expected. If v6 finds only that, v6 is the last
STUDY iteration.

## Ordered fixes (fixer; experiment-designer if CANNOT RESOLVE)

1. **(#1) Outlier count.** At l. 764-766 replace "a low-accuracy-outlier count, defined now: a seed
   whose selected checkpoint's validation accuracy is more than 3 pt below its arm's seed median"
   with: "per arm, the seed range (max − min of selected-checkpoint validation accuracy over seeds
   with an accuracy number, n = 62,000) and a low-accuracy count: seeds more than 3 pt below the
   arm's best seed; and, for A against D (paired by seed), the discordant counts: seeds where A is
   more than 3 pt below D at the same seed, and the converse. A median reference is not used: it
   misses the case where half or more of the seeds are low (Round-14: 0 of 3 flagged against the
   median, 2 of 3 against the best seed, range 5.46 pt)." Keep "Both are descriptive and not in the
   decision rule" (now "All are"). Check: best 72.64; 67.18 and 67.21 are 5.46 and 5.43 below.
2. **(#4) Headline, both branches.** At l. 787-789 replace the quoted sentence with: "If L ≤ 0: 'at
   350k EBOPs (iso-EBOPs), binary costs at most |L| pt of top-1 accuracy against learned-width
   weights on this model (n pairs, 95 %)', adding 'and at least |U| pt' when the upper bound U < 0.
   If L > 0: 'at 350k EBOPs (iso-EBOPs), no accuracy cost of binary weights is resolved; A exceeds
   NB by at least L pt (n pairs, 95 %)'." Label the printed "smallest A − NB the design resolves"
   (l. 795) as "the 95 % half-width" (C #14).
3. **(#2, #3, #11) Extra pairs and the wave-2 readout.** At l. 809-813 (after the table) replace
   "The table is the input ... stop)." with: "The formula governs; the table is illustrative, with
   thresholds rounded down (8 pairs ≤ 1.19 pt, 12 ≤ 1.57, 16 ≤ 1.87, 18 ≤ 2.01, 20 ≤ 2.13). The
   A − D proxy probably understates the A − NB sd_diff (NB can prune weights to 0 bits and follows
   its own PID path, so same-seed A and NB decorrelate more than A and D); it is a prior only. The
   binding input is the second-wave epoch-500 readout. That readout packet carries the paired
   A − NB validation sd_diff over feasible pairs, the feasible-pair count, and the n the formula gives
   at max(proxy, measured sd_diff); it does not carry the A − NB mean gap or its sign. The number
   of extra pairs is read off the formula, capped by the cap Kai sets in the row 'extra A/NB pairs
   (cap)'; it is not chosen. A stop on A − NB is reported as 'stopped at epoch 500' with the
   interim sd_diff. A seeds 9 to n enter A − NB only: A's arm summary and k/8, the budget claim,
   A − 79.4, the recipe claim, the four Holm secondary gaps, A − A07-350 and the stability counts
   use seeds 1 to 8. Each extra A seed trains in the same pod as its NB partner, GPU class stated.
   Extra pairs are appended after the 8-pair launch and do not delay it." At l. 1139-1140 replace
   "above 1.2 pt it goes to Kai with the [D13] options" with "it sets the extra pairs as in
   'Resolution' (Falsifier, weight-type claim); above 1.19 pt the packet goes to Kai". In the table (l. 804-808) change the
   rows to 1.19, 1.57, 1.87, 2.01, 2.13 pt (1.20, 1.88 and 2.14 fail their own criterion). Change
   "1.20 pt" to "1.19 pt" at l. 554, 1799, and "1.2 pt" at l. 127 if it is not
   change-log history (leave change-log entries as written). Kai row l. 1629: status "open; blocks
   the extra pairs, not the 8-pair launch (Kai sets the cap any time before the wave-2 epoch-500
   readout; n is read there)".
4. **(#6) A07-350 expectation.** At l. 711-712 replace "at most three 1-bit `input_proj` or d32
   dense input channels in total" with "at most three 1-bit input channels in total across the
   per-constituent layers (`input_proj`, `bit_block_0_attn_Wq`, `_Wk`, `_Wv`, `_Wo`,
   `bit_block_0_ffn_fc1`, `_fc2`; 2,048 EBOPs per input channel at 1 bit in each, from
   `static_floors_arms_s1_d25.json` `one.per_layer`: 6,144 / 3 and 65,536 / 32); the post-pool head (`head_fc1`, 32 EBOPs per input channel at 1 bit, and `head_fc2`) is
   reported separately and is not part of the expectation". At l. 713-714 and l. 1018-1019, the
   mismatch clause reads "a mismatch in the attention logits or the per-constituent layers". Apply
   the same restriction wherever [D21] or the Question says "d32 dense" in this sense (grep
   "d32 dense"; l. 174 is the per-channel cost statement and stays).
5. **(#5, #8) [D25] and the C′ gate.** At l. 326-327, 1340-1341 and 1500-1502: replace "once patch
   0024 lands", "the staged tree still has the HGQ2 default 0.01", "Not yet in code" and "not in the
   staged tree" with "set by patch 0024 (staged, tree ac5a5c86; `chang0926-a-n64-s1.json:40`;
   `cpu_gate_d25.log` `I_DECAY_OK` 0.001 on every [D19] config); PREFLIGHT re-asserts on the shipped
   tree"; replace "and 0.01 on C′" with "; C′ has no WRAP quantizer, so it carries no key and records
   an empty set (`cpu_gate_d25.log:116`)". Note at l. 111-113 that the CPU re-run under [D25] is done
   (`cpu_gate_d25.log`, `a17_pairing_d25_8seeds.json`). `decisions.md` is append-only: append a dated
   one-line correction to the [D25] entry's Check line (C′: empty record, not 0.01) rather than
   editing l. 33.
6. **(#7) REPORT-use restriction.** Append to Scope (l. 214): "REPORT may not cite this campaign as
   evidence for or against the thesis's 'close to full precision' claim; A − NB is cited only as an
   iso-EBOPs gap against learned-width weights. This holds unless Kai adds the FP32 E arm." FP32 E
   stays a Kai row (default not run).
7. **C items, apply now.** l. 233 cite `cpu_gate_d25.log` (or `cpu_gate_d21.log`) instead of the
   absent `cpu_gate_final.json` (#9); l. 1396-1398 say the arms file holds the [D21] set (#9);
   l. 612-614 (#10): "In the per-epoch history (`ablation.py:711`) `budget_met` means (a) to (c); in
   the W&B run summary and `train_meta.json` it is the raw (a) test on the delivered checkpoint
   (`:779`, `:806`), including the `model_min_ebops.keras` fallback. k is counted from the selection
   tag (`selection` ≠ `minimum_ebops_no_feasible_checkpoint`), the divergence record and the
   certification record, never from a `budget_met` field."; `xfm` sentence at l. 395-397, 721-722,
   1579-1580 (#12): "the 2-head E architecture under [D19] (any weight type, including NB) ...;
   `xfm` (key_dim 16) is expected to be at least as constrained, traced at [A7]"; name the 79.8 % and
   77.9 % lines Linformer and MHA (single-model, external) at l. 872 (#13); one tag scheme (fix-list
   numbers) in new amendment tags (#15). Optional: #16 one sentence adding [A14] on the selected
   A-s1 checkpoint at VERIFY; #18 to ml-engineer as a PREFLIGHT option.

## What Kai must decide (process deviation; not a finding)

Question: may PREFLIGHT, the canary and the epoch-500 pilot start now, in parallel with fixes 1-7
and the v6 check, instead of waiting for STUDY PASS? §6.5 makes fix → advance without re-review a
process failure, so this is his call. The pilot is validation-only, never quoted, selects no arm or
checkpoint and does not switch the primary (l. 1004-1005); fixes 1-3 and 6-7 govern VERIFY/REPORT
and wave 2, which no pilot number reaches.

Recommendation: **yes**, under hard conditions, in order:
1. This arbiter file is committed before the canary or pilot pod starts. It carries the verbatim
   analysis rules, so they are pre-registered before any number exists; that is the whole argument,
   and the fixer may not change their substance after a pilot number exists.
2. Fix 5 (C′ gate text) lands before PREFLIGHT evaluates [A21], and fix 4 (A07-350 expectation)
   lands before the pilot's epoch-500 readout (about 16-26 h after pilot start, l. 1001-1003).
3. The fixer pass and v6 complete, and v6 returns PASS, before wave-1 production launches. No
   exception.
4. Independent of this loop: the Kai table still has rows "open; blocks wave-1 production"
   (paper-rule variant, arm B, base architecture / comparand / selection metric / arm F) and "open;
   blocks wave 2" (H β control, H trace protocol, second-wave pods). STUDY PASS does not launch
   production; Kai answers or confirms those defaults either way.
Alternative: wait for v6 PASS (one fixer pass plus one diff-scoped panel, a few agent-hours) before
anything starts.
