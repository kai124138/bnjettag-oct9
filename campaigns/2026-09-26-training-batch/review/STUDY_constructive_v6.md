# STUDY constructive review, v6 (diff-scoped, iteration 6)

Campaign `campaigns/2026-09-26-training-batch/`. Artifact `STUDY.md` at 54bf3e7 (2,046 lines).
Scope, per `review/STUDY_arbiter_v5.md`: check my v5 findings against the fixer's edits, and
review the new arm FP32-E [D26] at the sites listed in the last change-log entry (l. 184-206).
Diff `git diff ed73976 54bf3e7 -- STUDY.md`. A new B only if it changes a number, a claim or the
design, or if an edited sentence is itself wrong. Reviewer: constructive-reviewer, 2026-09-27,
fresh context. Read: arbiter v5, my v5, the STUDY sections at every listed site,
`.claude/memory/decisions.md` l. 69, `code/tree/bnhgq2/qat.py:358-560`, `code/evidence/` listing.
Other reviewers' v6 output not read.

## Status of my v5 findings, by name

| v5 | finding | status | where (line numbers at 54bf3e7) |
| --- | --- | --- | --- |
| B1 | outlier count blind to its motivating case | **Resolved** | l. 896-903: range, count against the arm's best seed, A-against-D discordant counts; Round-14 check (0 of 3 against median, 2 of 3 against best, 5.46 pt) printed |
| B2 | A − NB headline wrong when L > 0 | **Resolved** (one residual shared with the new FP32-E headline, B2 below) | l. 924-928 |
| B3 | wave-2 readout unblinded; extra A seeds unfenced | **Resolved** | l. 950-963: packet carries sd_diff, pair count and n, not the mean gap or sign; n read off the formula; seeds 9..n enter A − NB only; l. 1311-1315; Kai row l. 1863 |
| C1 | [D25] stale; "0.01 on C′" | **Resolved** | l. 393-394, 1543-1544, 1712-1713; `decisions.md:69` correction appended. Residual splice at l. 1712, C4 |
| C2 | `xfm` in the attribution sentence | **Resolved** | l. 855-857 ("expected to be at least as constrained, traced at [A7]") |
| C3 | "smallest resolvable" is a half-width | **Resolved** | l. 934-935 |
| C4 | sizing table reads as steps | **Resolved** | l. 950-951; rows 1.19 / 1.57 / 1.87 / 2.01 / 2.13 |
| C5 | timing of the extra-pairs decision | **Resolved** | "appended after the 8-pair launch and do not delay it"; Kai row l. 1863 |
| C6 | two tag schemes | **Resolved** for new tags ("arbiter v5 fix N") |

Also confirmed: `cpu_gate_final.json` replaced by `cpu_gate_d25.log` (l. 300; file present in
`code/evidence/`); arms-file sentence (l. 1609-1610); `budget_met` semantics and k's source
(l. 728-733); Linformer / MHA named (l. 866-867); no "1.20 pt" outside change-log history.

## Category A

None. No selection on held-out, no projection stated as a result, no tautological comparison.
FP32-E selects on validation over (c)-passing epochs and is evaluated once on ROC-test.

## What is done well (keep)

- [+] **[D26] describes the code path that exists.** `qat.py:396` sets `fp32 = wmode == "none"`;
  datalane quantizers become `_dummy("datalane")` (`qat.py:500`), and the FP32 softmax uses dummy
  exp/inv inputs with `_table(1, 20)` outputs (`qat.py:517`), which is exactly the "not off: fixed
  21-bit tables, SAT, non-trainable" clause (STUDY l. 493-495). The guard at `qat.py:417-419`
  refuses `act_overflow`/`softmax_quant` without binary weights, and `i_decay_speed` requires WRAP
  (`qat.py:428-432`), so "FP32-E configs carry only keys the path reads" and "records an empty
  set" in [A25] are the right things to check.
- [+] **Package, labelled as a package.** Confound 12 (l. 645-652) lists what moves together
  (weight type, activation and softmax quantizers, budget with PID and β, the [D20] reset
  dynamics, width regularizers, selection domain) and what is held; the label "binary at 350k
  against unconstrained FP32, never the weight type" is carried into the Scope, [D26], the
  figures and the conventions table.
- [+] **The decomposition is recoverable.** NB − FP32-E = (A − FP32-E) − (A − NB) over common seeds
  (l. 589, 994), so the report can split the package into the iso-EBOPs weight-type share (A − NB)
  and the budget-plus-activation share with learned-width weights (NB − FP32-E). That is the
  strongest thing this arm adds.
- [+] **No vacuous gate.** (a) and (b) are switched off by config, and a `compute_ebops` reading of
  0 may not pass them (l. 503-506); certification may not pass on an EBOPs identity (l. 511-512);
  no EBOPs position for FP32-E on any axis (l. 520-521, 1069).
- [+] **Scope restriction is precise** (l. 274-280): E, N=64, this recipe only; never the cost of
  binary weights alone.
- [+] **Resolution arithmetic checks.** At sd 3.14 and 0.3 pt, zero correlation: sd_diff 3.154,
  paired half-width 0.836 · 3.154 = 2.64 pt; Welch se 1.115, Welch-Satterthwaite df ≈ 7.1,
  half-width ≈ 2.63 pt (review arithmetic). "About 2.6 pt" both ways (l. 989-991) is right, and
  it correctly implies pairing buys nothing when one arm's spread dominates.
- [+] **FP32-E is in the second-wave canary** at K=6 (l. 1300-1301), with the traced-EBOPs and
  β checks explicitly not applied.

## Category B

### B1. The wave-1 K=7 join rule for FP32-E checks memory only; the [D15] 14-day projection was made at K=6

- **Current state.** Budget, FP32-E, "Launch gate and wave" (l. 1319-1326): "FP32-E-s joins
  wave-1 pod s at K=7 only if 7 × the canary's measured peak GPU memory per process fits the
  production GPU's memory". The wave-1 canary runs at K=6 (l. 1131, 1150), and [D15] (l. 1100-1130,
  1237-1243) decides "launch as designed" from T_run = 7,000 × s_e measured at K=6. The same
  section already flags the expected branch as marginal (about 15.1 d against 14 d if the CPU trace
  ratio holds; bound s_e ≤ 172.8 s).
- **Problem.** A seventh process on the same GPU slows the six already there, including A, the
  primary arm. The rule lets wave-1 pod composition change after the [D15] projection without a
  throughput reading, so a wave that passed the 14-day rule at K=6 can break it at K=7, and the
  remedies [D15] offers (terminal epoch at a restart boundary, fewer pods) touch A's 7,000
  epochs. That is a design change to the primary arm made on an unmeasured quantity.
- **Improved state.** Add to the join condition: "and the projected wave-1 T_run at K=7 is ≤ 14 d,
  from a K=7 throughput reading (canary epochs at K=7, or the K=6 s_e scaled by 7/6 as a
  GPU-bound upper estimate); otherwise FP32-E stays in the second wave." The same "fits" wording
  sits in the Kai row "NB in wave-1 seed blocks" (l. 1866, adjudicated in v5); the one sentence
  should cover both slot-7 options.
- **Why.** The primary arm's run length is the one thing an optional reference arm must not
  put at risk; FP32-E has a clean second-wave home at K=6.
- **Effort.** Low (one sentence).

### B2. "And at least |U| pt" is read off the unadjusted interval while the verdict is Holm-adjusted

- **Current state.** Precision package headline (l. 981-984): "cost at most |L| pt ... adding
  'and at least |U| pt' when U < 0"; verdict (l. 986-987): "Resolved cost if the 95 % interval
  lies entirely below 0 and its Holm-adjusted p (second-wave family) is below 0.05; otherwise
  'not resolved at this resolution'." The A − NB headline (l. 925-928, arbiter v5 fix 2 verbatim)
  has the same structure against its "Falsified" rule (l. 964-966).
- **Problem.** With three members in the family, an unadjusted p between about 0.017 and 0.05
  gives U < 0 (headline: "costs at least |U| pt") and a verdict of "not resolved" or "not
  falsified". The headline is the sentence a reader keeps, and it would assert a nonzero cost
  that the pre-registered verdict denies. The branch is reachable, and on A − NB it sits on the
  thesis comparison.
- **Improved state.** In both headlines: "adding 'and at least |U| pt' when U < 0 and the verdict
  below is 'resolved cost' (FP32-E) / 'falsified' (A − NB); otherwise the interval is printed and
  labelled 'unadjusted 95 %'." Alternatively print Holm-consistent (simultaneous) intervals for
  the family. For FP32-E, also make the L > 0 branch symmetric with A − NB: "A exceeds FP32-E by at
  least L pt" (a reachable branch if FP32-E's selection or tables misbehave, see C2).
- **Why.** Any sentence tied to an interval bound should match the rule that decides the claim.
  The A − NB site is the arbiter's own v5 wording; it is listed so the arbiter can decide whether
  it is closed by citation or gets the same one-clause fix.
- **Effort.** Low (one clause at two sites).

## Category C

- **C1. Holm coupling, stated once.** The family is now {A − NB, H − NB, A − FP32-E}. Under
  step-down Holm, if A − FP32-E has the smallest p (the expected case: one arm carries the budget)
  and passes α/3, A − NB is tested as in the old two-member family; if A − FP32-E does not pass,
  A − NB cannot pass either. Adding one sentence under "Second wave" (l. 914-920) states the
  price. The DECISION block already lists "outside Holm, interval only" as the alternative, so no
  change of design is asked. Low.
- **C2. No plausibility check on the reference arm.** If the FP32 path misbehaves (dummy
  quantizers, 21-bit tables, controller-off selection over 7,000 epochs), A − FP32-E is
  meaningless and nothing pre-registered flags it. Add a descriptive pipeline check, not a
  result: FP32-E's seed-mean validation accuracy below A's, or below the external 79.4 % HGQ
  reference at 350k, goes to ml-engineer before FP32-E enters REPORT. Say also that the archived
  N=64 FP32 79.1 ± 0.3 % (l. 301; ungated, 80/20) is sizing context only, not a check. Low.
- **C3. Second-wave cost bullet still reads "16 runs at K=4 on 4 pods"** (l. 1295-1299) beside the
  FP32-E bullet's "packed, no extra pod-hours, though a larger K may raise s_e". Make the first
  bullet say 24 runs at K=6 (or "16 runs; FP32-E below"), so the two do not read as different
  plans. Low.
- **C4. Duplicated splice at l. 1712:** "patch 0024 sets it (`quant.i_decay_speed: 0.001`; set by
  patch 0024 (staged, ...)" says it twice. Low.
- **C5. The Question presupposes the sign** (l. 226: "how far is A below it?"). The Falsifier
  states the expected direction (l. 984); the Question can read "what is A − FP32-E?". Low.
- **C6. Figure: stack the decomposition.** In the paired-gap panel (l. 1067-1069), place A − NB and
  NB − FP32-E beside A − FP32-E (same seeds) so the reader sees which share is the weight type and
  which is the budget. The numbers are already pre-registered; this is presentation only. Low.

## Disputed facts for the investigator

None.

## Recommendation to the arbiter

No A. My five v5 items are resolved at every listed site. The FP32-E design is sound and well
labelled; two text-only B: B1 (the K=7 join rule must also pass the [D15] throughput projection,
because it touches the primary arm's pod) and B2 (the "at least |U|" clause must follow the Holm
verdict; new at the FP32-E site, shared with fix 2's A − NB wording). Neither changes an arm,
seed, target or selection rule. Six C, all low.
