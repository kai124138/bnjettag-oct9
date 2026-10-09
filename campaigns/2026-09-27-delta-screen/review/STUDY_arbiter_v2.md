# STUDY arbiter v2: 2026-09-27-delta-screen (Delta wave 2)

Arbiter, fresh context, 2026-09-27. Re-review, iteration n = 2.
Artifact: `campaigns/2026-09-27-delta-screen/STUDY.md` (1,025 lines, commit 9f9deeb) with `plan.md`,
`budget.py`, `screen_null.py`, `rank_sim.py`. Inputs read: `review/STUDY_physics_v2.md` (+
`het_physics_v2.py`), `review/STUDY_critical_v2.md`, `review/STUDY_constructive_v2.md` (+
`constructive_v2_*.py`), `review/STUDY_validators_v2.txt`, `review/STUDY_arbiter_v1.md`,
`review/STUDY_fixer_v1.md`; `docs/methodology/06-review.md` §6.1-§6.8; the conventions rows the
STUDY cites; `.claude/memory/decisions.md` (working tree); anchor
`campaigns/2026-09-26-training-batch/STUDY.md` (HEAD 96b95f2) and `RUN.md`. No plot-validator file
(STUDY has no figures).

## Validator lines

`STUDY_validators_v2.txt`: no mechanical STUDY validator exists; `prose_lint` on STUDY.md score 0,
"reads human" (14,625 words). No A-marked line, so nothing is Category A by the validator rule.

## Independent checks (arbiter)

- **Kai's [D15] decision (verified before relying on it).** Committed source: anchor STUDY at
  HEAD 96b95f2 ("STUDY.md regime-B amendment (dated execution of the [D15] branch, Kai-decided
  2026-09-27)"), l. 1393-1463: "[D15] branch executed (2026-09-27, Kai-decided …)"; regime B = the
  [D20] full-split reset trace every 10 epochs; "the feasibility test (a)-(c) is applied only on
  traced epochs, and only a traced epoch that meets (a)-(c) can become `model_best.keras`"
  (l. 1415-1416); "regime B applies to every arm that has a [D20] trace, in wave 1 and wave 2"
  (l. 1451); the key `ebops_trace_every: 10` comes from patch 0027's config regeneration
  (l. 1411-1414), i.e. not in bundle 77f1ca4e; wave 1 at K = 5 on the A10 class, about 13 pods
  (l. 1459-1463); "about 27 at peak with wave 2 and Delta" (l. 1483, 1709, 1886, 2339). The
  matching entry in `.claude/memory/decisions.md` l. 50-67 (working tree, uncommitted) says
  "Kai chose … Pod ceiling about 27 at peak on cms-ml: wave 1 at about 13 pods (K=5 on the A10
  class), wave 2 at 4, and Delta at 10 after this campaign's epoch-500 readout." Both sources
  agree. This is a Kai decision and overrides any orchestrator default [DK*] it touches.
  The STUDY predates it (fixer commit 9f9deeb precedes 96b95f2): l. 164 "the [D20]
  full-training-split EBOPs trace every epoch", l. 9 and l. 359 code base "anchor pilot bundle
  77f1ca4e", l. 39-40 amendment reason "anchor production waits for Kai ([D15], T_run 17.8 d)",
  l. 119 "waiting for Kai, anchor [D15]", l. 363 and l. 859 "about 24 GPU pods at peak",
  l. 690-700 timing basis 218 s/epoch (regime A, trace share 0.42), [DK4] "Launch does not wait".
- **"This campaign's epoch-500 readout" is ambiguous.** In the anchor STUDY "epoch-500 readout"
  names both the pilot's readout (l. 1269, 1517-1519, 2276, 2351) and production's [D13] interim
  readout at 500 (l. 841, 1868). Since 96b95f2 there are two pilots (regime A and regime B,
  l. 1526-1528). The arbiter does not choose a reading; it goes to Kai (below).
- **Heteroscedastic max-t, reproduced.** `python3 review/het_physics_v2.py`: m = 40, n = 4, crit
  2.793: family false-"yes" 0.095 (equal sd), 0.160 (10 % of cells at 2×), 0.192 (20 % at 2×),
  0.276 (10 % at 3×); placebo flag 0.014 → 0.003. m = 12: 0.099 → 0.124 / 0.136 / 0.153.
  `python3 review/constructive_v2_hetero.py`: 0.103 → 0.156 (one cell 3×), 0.209 (25 % at 3×) at
  m = 12; 0.104 → 0.333 at m = 40; placebo coupled at sd 0.2: flag 0.005 / 0.0015, top-quartile
  rank 0.098 / 0.015 (not uniform). All three reviewers' numbers stand.
- **Common offset and the placebo-referenced test, recomputed** (own numpy, seed 7, 20,000 reps,
  n = 4, pooled sd over cells and placebo as in STUDY l. 576-577). Replica-referenced max-t
  (STUDY rule): P("yes" | null) 0.102 / 0.299 / 0.419 at δ = 0 / 0.5 / 0.707 SE (m 12) and
  0.098 / 0.299 / 0.421 (m 40). Placebo-referenced (d_i = cell − placebo): critical 2.423 /
  2.806, P("yes") 0.097 / 0.096 / 0.100 (m 12) and 0.100 / 0.095 / 0.096 (m 40). Critic A2
  reproduced. The variance of cell − placebo equals that of cell − replica (2σ²), so the switch
  costs no power under the homogeneous model.
- **G3′ power, recomputed** (own numpy, seed 7, 40,000 reps, true g = 0, ρ = 0, n = 4, own sd
  df 3). Two-sided-95 % lower bound (t 3.182): P(pass) 0.80 / 0.60 / 0.32 / 0.17 / 0.074 / 0.039 /
  0.031 at σ 0.10 / 0.13 / 0.20 / 0.30 / 0.6 / 1.5 / 3.14 pt (critic's table). One-sided 95 %
  bound (t 2.353): 0.93 / 0.79 / 0.50 / 0.30 / 0.14 / 0.076 / 0.062. Either reading, G3′ has no
  power at any σ the STUDY expects (l. 495-498); STUDY l. 569 does not say which bound or sd.
- **GPU determinism.** `enable_op_determinism` / `TF_DETERMINISTIC_OPS` appear in the anchor tree
  only in `code/tree/campaigns/chang0926/evaluate_roc.py`; training sets only
  `keras.utils.set_random_seed` (`code/tree/bnhgq2/ablation.py:597`, `train.py:261`). No placebo
  or no-op key exists in `delta.json` (grep "no-op|noop|placebo": only unrelated notes at l. 668,
  6869, 6893, 7050, 7075). The strict validator refuses unknown keys (decisions.md l. 16-17).
  Phys A2 / crit B2 / cons B2 confirmed.
- **Replica-side loss** (phys A3), traced in the text: n_p counts seeds usable in both (l. 550-552);
  "a cell with 3 ≤ n_p < n is not in the main ranked list" (l. 553); base stability pauses only
  above a quarter (l. 403-404; 1 of 4 is not); ⌈3·4/4⌉ = 3 passes (l. 408-409). One lost replica
  seed at n = 4 therefore moves every cell of the family to the incomplete-pairs list and empties
  the main list, with no rule. Confirmed.
- **Cheap version's family test** (arbiter, everyone missed). l. 743 gives the cheap version "the
  same Dunnett 'no'" at n = 3, but `screen_null.py` l. 60 simulates n ∈ {4, 6, 8} only; no n = 3
  critical value, null rate or power is stated.
- **Pairing prior** (cons B1): `.claude/memory/experiment-log.md` l. 2277-2279, "Pairing by seed is
  measured NOT to help: n8 cross-arm seed correlations −0.34, −0.79, −0.56" (archived, 3 seeds).
  Quoted correctly.
- **Label collision** (arbiter, C): the STUDY's own [D15] is Bop γ/τ (l. 822); l. 40 uses bare
  "[D15]" for the anchor's.
- **Reproduced by the panel and not re-run here:** `budget.py` (302 runs, 176,000 run-epochs,
  1,776.3 / 3,128.7 pod-hours, 318 retraces), `screen_null.py` (crit 2.410 / 2.793, P(no | null)
  0.896-0.904), `rank_sim.py`; three reviewers agree to the digit and none contradicts another.

## Adjudication of v2 findings

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Kai's [D15] regime-B decision absent: l. 164 trace every epoch; selection, companion and eligible count assume every epoch eligible; code base 77f1ca4e is the regime-A bundle; amendment reason l. 39-40 and Reference l. 119 stale; launch gate 1 does not name which pilot; timing on 218 s regime-A epochs; 24 vs Kai's 27 pods; E packing rule differs from the anchor's K = 5 on A10 | crit A1 | A | **A** | Case 3, verified in committed anchor STUDY 96b95f2 l. 1393-1463 and decisions.md l. 50-67. The design basis contradicts a recorded Kai decision |
| 2 | Kai's "Delta at 10 after this campaign's epoch-500 readout" vs [DK4] "launch does not wait"; which readout is meant is unstated | crit B1 | B | **B** (folded into fix 1) | Case 3. A Kai line overrides an orchestrator default; the reading of it goes to Kai |
| 3 | Family max-t calibrated for equal variances; the STUDY's own [L6] levers, shape-changing and long-horizon cells are heteroscedastic; FWER 0.15-0.33; two-mode seeds up to 0.54; the placebo flag gets less sensitive as miscalibration grows | phys A1 / cons A1 / crit B3 (+ phys B2, B4) | A / A / B | **A** | Case 2, sided with A: reproduced (Independent checks). "P(no \| global null) = 0.90 per family by construction" (l. 92, 635) is a stated falsifier's calibration contradicted by the STUDY's own text; §6.3 Q4 |
| 4 | Family test is replica-referenced; the placebo, added to measure pod/pack/identity offsets (l. 458-459), never enters it; an offset of 0.7 SE quadruples the false "yes" while the flag catches 6-11 % | crit A2 | A | **A** | Case 3, recomputed: placebo-referenced holds 0.095-0.100 at δ ≤ 0.707 SE vs 0.42 for the STUDY rule, at equal power. No evidence that δ = 0; reviewer protection |
| 5 | Placebo not specified as an A/A cell: no no-op key exists and the strict validator refuses unknown keys; GPU determinism unmeasured; if deterministic, the flag never fires, rank is not uniform, it deflates s_pool, and the "exact zero is a red flag" rule (l. 525-526, 662-663) flags a healthy pipeline | phys A2 / crit B2 / cons B2 | A / B / B | **A** | Case 2, sided with A: after finding 4 the placebo becomes the family test's reference, so its specification is load-bearing; the pre-registered zero-g rule is wrong for a deterministic stack; grep confirms no key and no op determinism |
| 6 | One replica-seed loss at n = 4 empties the main ranked list; no rule fires | phys A3 | A | **A** | Case 3, traced l. 403-409, 550-553. A foreseeable case left undefined invites a post-hoc rule |
| 7 | G3′ restored without power: P(pass \| g = 0) ≤ 0.14 at σ ≥ 0.6 pt; bound and sd unnamed; "not non-inferior" will read as "inferior" | crit A3 | A | **A** | Case 3, recomputed both bound readings. §6.3 Q4, same precedent as arbiter v1 #3 |
| 8 | "95 % interval on the family-pooled paired sd, df = Σ(n_p − 1)" under-covers (0.933) because the shared replica contributes only n − 1 df | crit B4 | B | **B** (folded into fix 2) | Case 3; the reasoning is correct (common replica term) and the fix is the same simulation |
| 9 | Rank-move flag has no null rate; flags 8.5-25 of 40 at 5M under the null | crit B5 | B | **B** | Case 3; same defect as arbiter v1 #20 |
| 10 | [DK6] makes mean g primary by orchestrator default, against arbiter v1 fix 9 ("LCB80 stays primary unless Kai amends DELTA §5.3") | crit B6 | B | **B** | Case 3. DELTA §5.3 is Kai's pre-registration. [DK7] is different, see below |
| 11 | E planning K = 5 violates the STUDY's own 90 % rule (94.5 %) while the anchor runs K = 5 on A10 under regime B | crit B7 / phys C3 / cons C7 | B / C / C | **B** (folded into fix 1) | Case 2, sided with B: two campaigns, one card, two packing rules, unexplained; also earlier #7 |
| 12 | [L1] attempt uninformative: seed-rank persistence of one config at n = 4 is not treatment-rank persistence | phys B1 | B | **B** | Case 3. §6.3 Q5: an attempt that cannot inform is not an attempt |
| 13 | sd_rep read on survivors is biased low; usable count not printed; ≤ 6 of 8 usable should not raise n | phys B3 | B | **B** | Case 3 |
| 14 | Accuracy-vs-AUC rank concordance has no pre-registered consequence | phys B5 | B | **B** | Case 3; selection-metric deviation from the house rule (conventions row l. 774) makes the concordance load-bearing |
| 15 | Pairing efficiency assumed (sd_plan uses ρ = 0; archived record shows negative seed correlations); unpaired-against-8-seeds companion and ρ̂ not reported | cons B1 | B | **B** | Case 3, evidence line verified (experiment-log l. 2277-2279) |
| 16 | Cheap version claims "the same Dunnett 'no'" at n = 3 with no n = 3 critical value, null rate or power | arbiter | – | **B** (folded into fix 2) | Case 5, `screen_null.py` l. 60 |
| 17 | Wave-level "no" is 0.90² ≈ 0.81 under the global null | crit C1 | C | C | |
| 18 | Chance baselines mix m 43 and 40 | crit C2 | C | C | |
| 19 | Dunnett family membership (Welch, incomplete pairs) and per-cell n_p in the simulation unstated | crit C3 | C | folded into fix 2 | |
| 20 | "95 % interval on g lies entirely below 0": name the sd | crit C4 | C | C | |
| 21 | sd_rep ceiling false-pause / false-pass rates at df 7 | crit C5 | C | C | |
| 22 | Significance mode not expected to arm; put ranking first / compress | phys C1 / cons C6 | C / C | C | |
| 23 | Split-half as a second companion | phys C2 | C | C | Already a Kai option (l. 601-603) |
| 24 | Family definitions stated once (BH m 19 vs Dunnett m 12) | phys C4 | C | C | |
| 25 | Forest plot: per-cell thresholds or t, interval type and n_p per bar | phys C5 | C | C | |
| 26 | Lower bound 0.19 pt of the spread bracket; two-mode note | cons C1 | C | C | |
| 27 | Family test power at the ceiling equals α at σ 1.5 | cons C2 | C | C | One sentence in the box |
| 28 | "Cannot call a gap flat" is an undeclared conventions deviation (`jet-tagging-metrics.md` l. 44-45) | cons C3 | C | C | |
| 29 | Companion as mean over last k traced feasible epochs | cons C4 | C | C | Consider with fix 1 (traced epochs) |
| 30 | +1 / +3 pt are illustrations with no prior | cons C5 | C | C | |
| 31 | Bare "[D15]" at l. 40 means the anchor's; the STUDY's own [D15] is Bop | arbiter | – | C | |

**[DK7] (arbiter decision, for the record).** Arbiter v1 fix 1's wording ("no cell exceeds the
placebo") was wrong: under the global null the placebo is one of m + 1 exchangeable draws, so it
returns "no" with probability 1/(m + 1) (0.076 / 0.023, `screen_null.py`, reproduced by the
critical reviewer). The fixer's Dunnett-type max-t substitution is accepted. [DK7] is no longer an
open arbiter item; its calibration is fixes 2-3 below. [DK6] is not the same case: it changes
Kai's DELTA §5.3 rule, not an arbiter wording, and finding 10 stands.

## Earlier A and B findings (arbiter v1), by name

| v1 # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 (A) | ranking-mode "no" cannot fire | **resolved** as to the defect named | Dunnett max-t l. 579-582, 632-638; P(no \| null) 0.896-0.904 under the homogeneous null, reproduced by all three reviewers. The calibration of that "no" (heterogeneity, offset, deterministic placebo) is new: v2 #3-#5, Category A |
| 2 (A) | winner's curse | **resolved in text**, cascade due | companion, eligible count, τ, flag l. 593-603; [L6] l. 886-892 names the cells. Regime B changes the eligible set (v2 #1); the flag has no null rate (v2 #9) |
| 3 (A) | resolving power at 3.14 pt, stop line | **resolved** | ±7.1 pt row l. 509 (t(0.975,3)/2 · 4.44 = 7.07); fidelity table l. 515-519; ceiling 1.3 pt l. 484-491, reproduced by `screen_null.py` (0.53 at σ 1.3) |
| 4 (A) | DELTA departures | **not resolved** in parts (a) and (d) | (b), (c), (e)-(h) present: ⌈3n/4⌉ l. 408-418, sd source l. 26-30, cap l. 591, R1 l. 293-298, order l. 352-358, K6/teachers l. 256-258, 299. (a) G3′ restored l. 568 but powerless (v2 #7). (d) the wave-2a amendment's reason (l. 37-40) is overtaken by Kai's [D15] answer and his "Delta at 10 after this campaign's epoch-500 readout" (v2 #1-#2). Keeps A |
| 5 (B) | missing pairs | **resolved** for cell-side losses | l. 550-557; replica-side loss undefined (v2 #6) |
| 6 (B) | ranking statistic | **not resolved** as specified | fix 9 said LCB80 primary unless Kai amends; STUDY l. 43-45, 575-578, [DK6] made mean g primary. Keeps B (v2 #10) |
| 7 (B) | E packing at K = 6 | **not resolved** | K from canary (l. 335-343), but planning K = 5 violates the 90 % rule (l. 729-731) and the anchor now runs K = 5 on A10 (96b95f2 l. 1459-1463). Keeps B (v2 #11) |
| 8 (B) | always-on patches | **resolved** | X2 l. 278-282, launch gate 9 l. 349-351 |
| 9 (B) | anchor config freeze | **not resolved** | relabel rule l. 359-362 exists, but the code base 77f1ca4e lacks patch 0027 (`ebops_trace_every`), so the relabel fires at launch. Keeps B, fix 1 |
| 10 (B) | anchor state stale | **not resolved** | re-pinned to c2f5447 / e620173 (l. 9, 118-122), stale again after 96b95f2. Keeps B, fix 1 |
| 11 (B) | question vs rule | **resolved** | frontmatter l. 6, l. 75-88 |
| 12 (B) | floor-family package | **resolved** | l. 223-226, 584-590 |
| 13 (B) | structural headroom | **resolved** | l. 563-565 |
| 14 (B) | baseline tuning asymmetry | **resolved** | l. 104-108 |
| 15 (B) | per-class AUC | **resolved** | l. 608-609, 770 |
| 16 (B) | cheap version long cells | **resolved** | l. 739-742; `budget.py` cheap 129 / 79,500 reproduced by the panel |
| 17 (B) | [D14] limitation | **resolved** | [L7] l. 893-896 |
| 18 (B) | conventions rows | **resolved** | l. 770, 774-776 |
| 19 (B) | [L1] attempt | **not resolved** in substance | l. 872-877 adds a seed-rank check that cannot bear on L1 (v2 #12). Keeps B |
| 20 (B) | contradicted null count | **resolved** | l. 644-645 (0.5 / 1.1; `rank_sim.py` 0.48 / 1.07) |
| 21 (B) | replica seeds 1-8 option | **resolved** (adopted [DK2]) | l. 228-240, 916-920 |
| 22 (B) | binomial-SE argument | **resolved** | l. 498-500 |
| 23 (B) | K6 and teachers as Kai items | **resolved** | [DK9] l. 966-970 |

v1 C items #24-#32: applied (fixer list; spot-checked by the critic: C27 318, C29 l. 442-445, C31
l. 137-141, C32 box l. 62-73). C28 (formula-check wording) is reopened by v2 #5.

## Regression triggers (§6.7), each checked

| trigger | status | evidence |
| --- | --- | --- |
| selection on held-out, or changed after results | not met | validation only (l. 529-557); ROC-test never touched (l. 618-619); no results exist |
| val AUC vs ROC-test AUC > 0.01 | not met | no ROC-test evaluation ([D5]) |
| single-seed / < 100-epoch / lab-pod headline against the 1000-epoch record | not met | nothing quotable; Reference table has no comparand (l. 112-126) |
| comparison across N, input sets, splits or schedules as one series | not met | M009, M038, M040 labelled (l. 392-393, 771); floor family in its own list (l. 223-226) |
| gap smaller than seed sd with < 3 seeds | not met | n ≥ 4 (l. 465); n_p ≥ 3 for any reading (l. 552) |
| reload outside 1e-7, TF32 on | not met | TF32 off, reload 1e-7 (l. 450, 777) |
| eBOPs not remeasured on the selected checkpoint | not met | [D11] certification (l. 545-549); regime B keeps certification unchanged (anchor 96b95f2 l. 1449-1450) |
| binary layer with > 2 values | not met | conventions check 1 (l. 777) |
| DSP / C-sim / C-synthesis | not applicable | no synthesis (l. 759-760, 778) |
| per-class AUC < 0.7 hidden | not met | per-class AUCs in the readout (l. 608-609) |
| byte-identical arms / different y arrays | not met at STUDY; watch | y_val sha asserted (l. 385-389). The placebo is designed to be byte-identical in config to its replica; that is intended, and fix 3 pre-registers how a bit-identical outcome is read so it is neither hidden nor misread |
| failed validation without remediation; tautological comparison as validation | not met at STUDY | the placebo's formula check would be tautological under a deterministic stack; fix 3 rewrites it before any result exists |
| STUDY [D] label replaced without dated amendment | not met | every change to DELTA is listed as a dated amendment (l. 25-56); [DK6] is labelled a pending amendment (fix 6 makes it conditional on Kai). The regime-B change is a dated amendment made in fix 1 |
| outward numbers ≠ VERIFY | not applicable | none |
| suspiciously good | not applicable | no results |

No trigger is met. No investigator, no `REGRESSION_TICKET.md`. Kai's [D15] answer is an upstream
decision in a sibling campaign, absorbed here by a dated amendment within this phase; no earlier
phase of this campaign re-runs.

## §6.8 validation target

The Reference table names no binding comparand, which is correct for a never-quotable screen.
Conventions check 3 (reproduction) is stated as probably unavailable, with stand-ins (l. 770).
After fix 1, one stand-in changes: the anchor pilot values used as descriptive context must name
the regime (the regime-B pilot matches the Delta's runs; the regime-A pilot does not).

## Competing-group question

A group running this screen next month would have: the screen at the anchor's production trace
regime and launch timing (fix 1); a family test referenced to the in-family A/A cell and
calibrated under unequal variances, with its achieved error rate printed (fix 2); an A/A cell
whose identity and determinism are verified at PREFLIGHT (fix 3); a rule for replica losses
(fix 4); a stated power for non-inferiority (fix 5). None has a justification for being absent.

## Disputed facts for the investigator

None. Regime B is committed (anchor STUDY 96b95f2 l. 1393-1463) and matches decisions.md
l. 50-67. The one open question, which epoch-500 readout Kai meant, is a question for Kai, not a
fact to trace.

## Dismissals

None.

## Verdict: **ITERATE** (iteration 2)

Six A items (v2 #1, #3, #4, #5, #6, #7, with v1 #4 folded into #1 and #7), ten B items. The next
arbiter pass is iteration 3, which carries the §6.5 warning. Required fixes for the `fixer`, in
priority order. Every changed number cascades: `budget.py` output, both Budget tables, Counts
(l. 242-247), the box (l. 62-73), Null (l. 89-96), Falsifier, [DK] rows, "Where I am not sure",
the certification count, and the experiment-log stub (`.claude/memory/experiment-log.md` l. 11-16).

1. **(A, #1, #2, #11; v1 #4d, #7, #9, #10) Regime B and Kai's launch timing.** Add a dated
   amendment (2026-09-27) citing anchor STUDY 96b95f2 l. 1393-1463 and decisions.md
   "2026-09-27 (Kai, [D15] branch after the canary)".
   (a) Delta trace regime: new default [DK13] = regime B (`ebops_trace_every: 10`, patch 0027),
   to match the anchor; if the designer prefers regime A, give the reason and label every
   anchor-facing comparison "cross-regime". Rewrite l. 164.
   (b) Selection (l. 532-539), companion (l. 593-598), eligible-epoch count and [L6]: eligible =
   traced epochs only (50 per 500-epoch cycle; epoch 500 is traced); counters reported with that
   denominator; [A6] snapshot and `model_best` as in anchor l. 1415-1433.
   (c) Code base: frontmatter `code_sha` and launch gate 11 name the regime-B bundle ("the sha the
   anchor PREFLIGHT addendum for patch 0027 names"), not 77f1ca4e; X2/Z13 and the
   horizon-truncation check (launch gate 5) cover `ebops_trace_every`, including a replica
   configured to 1,000/2,000 and read at 500.
   (d) Launch timing: quote Kai's line "Delta at 10 after this campaign's epoch-500 readout" in
   launch gate 1. Kai's line overrides [DK4]'s "does not wait": the wave waits for an anchor
   epoch-500 readout. Which readout (regime-B pilot, regime-A pilot, or production's [D13]
   readout at 500) goes to Kai as a named item; until he answers, the gate reads "the readout
   Kai names". Rewrite the amendment reason l. 37-40 and Reference rows l. 118-120.
   (e) Budget: rerun `budget.py` with the regime-B per-epoch cost, labelled a projection
   (anchor arithmetic: s_e ≈ 136.5 s at K = 6, from trace 90.61 s + remainder 127.45 s, anchor
   l. 1453-1457; "neither is a measurement"); replace every 218 s row, the replica-gate hours and
   the wall clock.
   (f) Packing: plan E at K = 4 on 23-24 GB cards (the STUDY's own rule) with K = 5 as the
   alternative row, or adopt the anchor's rule (pod map from the regime-B pilot's measured peak
   memory) and say why the 90 % rule is replaced. State which, once, in [D16]/[DK11].
   (g) Pods: 24 → about 27 at peak (Kai) at l. 363, 859, 869, 979.
   (h) Re-pin anchor citations to 96b95f2 (or state the sha per citation).
2. **(A, #3, #4, #8, #16; phys B2, B4, crit C3) Family test calibration.**
   (i) Add rows to `screen_null.py` and print them in the STUDY: one cell at 3× gap sd; 25 % of
   cells at 2× and 3×; two-mode seeds q = 0.1 / 0.33 / 0.5 (constructive model); common offset
   δ = 0.5 / 0.707 SE on every non-replica run; near-deterministic placebo (gap sd 0.1-0.2×);
   n = 3 (cheap version) with its critical value, null rate and power.
   (ii) Primary family test: placebo-referenced many-to-one max-t (d_i = cell − placebo; the
   replica stays the pairing partner for g and for the ranking), critical value simulated for
   the family's actual n_p vector and membership. Pre-register the branch on the determinism
   probe of fix 3: if placebo and replica are bit-identical, d_i = g_i and the test is the
   replica-referenced one with the no-offset assumption stated beside every error rate.
   (iii) Heterogeneity: choose and pre-register one of (a) each cell's own sd (df n_p − 1),
   critical value simulated for the n_p vector; or (b) pooled sd plus a homogeneity gate (ratio
   of largest cell sd to s_pool against its simulated null 95th percentile), falling back to (a)
   when the gate fails. In either case each named cell prints its own sd beside s_pool, and a
   named cell whose own-sd t does not clear the own-sd critical value is labelled "driven by
   variance". Welch cells, hash-failed cells, incomplete pairs and long-horizon cells (M015,
   M031, M032) are either inside with their own-sd t or outside the max-t; say which, once.
   If the fixer cannot choose between (a) and (b) on the evidence of the scenario rows, it returns
   CANNOT RESOLVE to the experiment-designer (§6.5) rather than picking silently.
   (iv) Delete "by construction" (l. 92, 635, box, [DK7], stub) and print the achieved FWER of
   the chosen rule under each scenario row next to every "0.90". Replace the pooled-interval df
   claim (l. 576-577, 565-567) by a simulated quantile or label it "nominal 95 %, simulated
   coverage 0.93".
3. **(A, #5) Placebo specification and determinism.**
   (a) Mechanism: the placebo differs from its replica only in run identity (run name / W&B id),
   no config key; a candidate path is the stage-style identity of patch 0026 (`BNJ_STAGE`, an
   env value outside `config_sha256`, decisions.md l. 103-107). The fixer states whether the run
   name enters `digest_json(cfg)` and picks a mechanism the strict validator accepts.
   (b) PREFLIGHT assertion: placebo and replica at seed s have equal `digest_json(cfg)` apart from
   identity, equal init `kernel_hashes`, equal first-step loss on CPU; list the placebo under
   X2/Z13.
   (c) Determinism probe in the launch-gate-7 canary: the same E config and seed twice on one GPU
   product for about 3 epochs; compare weight hashes and per-epoch losses. Cite the grep (training
   sets only `keras.utils.set_random_seed`, `ablation.py:597`, `train.py:261`; op determinism only
   in `evaluate_roc.py`).
   (d) Pre-register both outcomes: bit-identical → the placebo is a pod/pack/identity check only,
   rank claim dropped, excluded from s_pool, family test per fix 2(ii) branch; divergent → the
   measured divergence printed, placebo read as the in-family null draw. In both cases exclude
   the placebo from s_pool. Rewrite l. 147 ("uniform under the null"), l. 524-526 and l. 660-663
   (exact-zero "red flag") to match; print the placebo's detectable offset in pt.
4. **(A, #6) Replica-side losses.** Pre-register: a replica seed lost (infeasible, degenerate,
   diverged, collapsed, certification-failed) lowers the family's n uniformly; the main list
   stands at that n (stated), the critical value is re-simulated at it, and the incomplete-pairs
   list and survivorship label apply to cell-side losses only. Replica seeds above n cannot
   substitute (cells run seeds 1-n); say so.
5. **(A, #7; v1 #4a) G3′ power.** Name the bound (DELTA's "lower 95 % bound": one- or two-sided)
   and the sd (own, df 3, or pooled). Print P(pass | g = 0) at σ 0.6 / 1.5 / 3.14 pt (own sd:
   0.074 / 0.039 / 0.031 two-sided, 0.14 / 0.076 / 0.062 one-sided) and the σ at which G3′ has
   power (about 0.13-0.2 pt). Label the expected outcome "non-inferiority not shown at this n",
   never "inferior". Add to the Kai list: M023 to the zero-GPU synthesis check on `mulder`
   regardless of G3′ (K5).
6. **(B, #10; v1 #6) Ranking primary.** DELTA's LCB80 is the primary ranking until Kai signs
   [DK6]; mean g with its interval sits beside it. Reword l. 43-45, 575-578 and [DK6] as "pending
   Kai; if unsigned at the launch gate, LCB80 is primary".
7. **(B, #9) Rank-move flag.** Print the expected null flag count per family from a simulation as
   a function of the observed primary-companion correlation, or set the threshold so about one
   null flag is expected per family.
8. **(B, #12; v1 #19) [L1].** Label the seed-rank check "not a test of L1", and add a check that
   bears on it: rank persistence across cells of the long-horizon cells and their replicas
   (M015, M031, M032) at 500 vs their own H, with n stated; keep the anchor epoch-500 vs 7,000
   check.
9. **(B, #13) sd_rep usable count.** Print the usable count beside sd_rep; sd_rep on ≤ 6 of 8
   usable seeds is labelled so and cannot by itself raise n.
10. **(B, #14) Accuracy-vs-AUC concordance consequence.** A cell in the top 12 on one metric and
    outside on the other is flagged to Kai.
11. **(B, #15) Pairing efficiency.** Report the family-pooled cell-replica correlation ρ̂ with its
    null interval, and pre-register the unpaired-against-8-replica-seeds Dunnett as a
    non-selecting companion (never changes the primary list); cite experiment-log l. 2277-2279
    (archived, 3 seeds, a hint).
12. **(C, required before commit)** #17-#31: 0.81 wave-level null; m 40 vs 43 chance baselines;
    name the sd in the "contradicted" rule; sd_rep ceiling false-pause/false-pass sentence;
    ranking mode first, significance mode "not expected to arm"; one-place family definitions;
    forest-plot per-cell thresholds or t; the 0.19-pt lower bracket and two-mode note; power at
    the ceiling in the box; "cannot call a gap flat" as a declared conventions deviation;
    companion as mean over the last k traced feasible epochs (consider); "+1 / +3 pt are
    illustrations"; "anchor [D15]" wherever the anchor's label is meant.

## What Kai must decide (blocks launch, not PASS)

The fixer writes each as a "Where I am not sure" row with its cost. None blocks the STUDY PASS
by itself; the artifact must present them correctly.

1. **Which epoch-500 readout** "Delta at 10 after this campaign's epoch-500 readout" means: the
   regime-B pilot's, the regime-A pilot's, or production's [D13] readout at epoch 500. The last
   means the Delta waits until production reaches epoch 500, about 19 h of wall clock after
   production launches (500 × 136.5 s at K = 6, a projection from the anchor's regime-B
   arithmetic, not a measurement), and production's launch date is not yet projected.
2. **The Delta's trace regime** ([DK13], default regime B to match the anchor).
3. **[DK6]** ranking primary: DELTA's LCB80 (as written) or mean g (a DELTA §5.3 amendment).
4. **[DK7]**, for the record: the Dunnett-type "no" replaces arbiter v1's wording (the arbiter
   accepts it; Kai may still override).
5. **M023** to the synthesis check on `mulder` regardless of G3′ (K5).
6. **Split-half** validation as the primary or a second companion (option at l. 601-603).
7. **Carried from v1:** [DK1]-[DK5], [DK8]-[DK12], with [DK4] now superseded in part by item 1
   and [DK11] updated by fix 1(f)-(g).
