# STUDY arbiter v6: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-27. Artifact `STUDY.md` at 54bf3e7 (2,046 lines; unchanged at
HEAD 09e0d8c), `plan.md`, `code/tree`, `code/evidence/`, `manifests/pilot-job.json`. Reviews v6:
`STUDY_physics_v6.md`, `STUDY_critical_v6.md`, `STUDY_constructive_v6.md`. Validators
`STUDY_validators_v6.txt`: `prose_lint` score 0, `E1-TRACE-PENDING` 0, no A line. No figures at
STUDY, so no plot-validator file. Earlier arbiter `STUDY_arbiter_v5.md`. Read `06-review.md`
§6.1-6.8, `docs/conventions/`, `decisions.md` top entry (Kai, second set). Iteration **6**
(strong-warn tier, §6.5).

## Independent checks made by the arbiter

- **Survivor bias in the second-wave headlines (phys A1).** `grep -n "survivor\|upper estimate"`
  hits only the arm summary (l. 769-771), the A − 79.4 paragraph (l. 855-857) and l. 45. The
  weight-type headline (l. 922-929) and the precision-package headline (l. 979-985) have no such
  clause; both allow 6 or 7 pairs (l. 971-974, l. 993). The general "Paired gaps" bullet
  (l. 772-775) states the count but not the one-sided failures, so the wave-1 paired gaps
  (A − R, A − D, A − B, A − F, C − A07-350) share the defect (§6.3.2). Fact confirmed.
- **Entropy (phys B1).** No entropy code in `code/tree/bnhgq2` (grep). The QAT model is functional
  (`qat.py:537, 615`); the softmax layer is named `{blk}_attn_softmax` (`qat.py:574`) on both
  branches (the fp32 branch passes `name=name`, `qat.py:513-518`); a probe sub-model pattern
  exists (`qat.py:662`); checkpoints reload with `keras.models.load_model(..., compile=False)`
  (`ablation.py:299`). Entropy is therefore computable offline from any saved `.keras` by a
  sub-model on that layer's output. Pilot outputs go to `/data/chang-n64-20260926/pilot` on the
  `kai-data` PVC (`manifests/pilot-job.json`), so the epoch-500 snapshot survives pod exit.
- **Quantizer variables on FP32-E (crit B4).** `_table(i0, f0)` is a `kif` quantizer
  (`qat.py:358-360`), used on the fp32 softmax (`qat.py:517`). HGQ2's `kif` `build` creates `k`,
  `i`, `f` weights unconditionally (`~/hgq2/HGQ2/.../fixed_point_quantizer.py:371-394`). That
  local tree is **v0.2.0**, not the pinned 0.1.9; the fact is probable, not proven on the pin.
  Either way the check as worded ("no quantizer variables in any layer") is unsafe; the fix
  asserts on the pinned build.
- **`binary_gate` (crit B6).** `ablation.py:582` calls `binary_gate(model, cfg)` unconditionally;
  `:340-341` assert the binary layer set and two symmetric values. `grep binary_gate STUDY.md`
  returns nothing, so the gap covers NB ([A22]) as well as FP32-E.
- **K=7 rule (crit B1, cons B1).** l. 1319-1326 gate the wave-1 join on "7 × the canary's measured
  peak GPU memory per process"; the wave-1 canary runs at K=6; [D15] decides on s_e at K=6. The
  NB row (l. 1866) has the same "K=7 fits" wording. Confirmed.
- **"Close" claim string (crit B2).** l. 979-980 claim "is close to"; l. 985-987 decide only
  "resolved cost" / "not resolved"; Scope l. 276-278 licenses citing A − FP32-E "as evidence on
  the thesis's 'close to full precision' claim". Confirmed: no rule outcome maps to "close".
- **|U| clause against the Holm verdict (cons B2).** l. 925-928 (arbiter v5 fix 2, my wording) and
  l. 983 add "at least |U| pt" on the unadjusted interval while the verdict is Holm-adjusted
  (l. 964-966, 985-986). With three family members, an unadjusted p in about (0.017, 0.05) gives
  U < 0 and a "not falsified" verdict. Confirmed; the defect at l. 925-928 is in v5's prescribed
  text.
- **v5 launch conditions.** 1: arbiter v5 committed at 27ffa29 before any pod (`decisions.md`).
  2: fix 5 landed at 1175889 (10:28:20) before `PREFLIGHT.md` (10:42:40) evaluated [A21]
  (critical, file times); fix 4 landed at 1175889, before any epoch-500 readout. Both met.
  3 (v6 PASS before wave-1 production): **not met** by this verdict.

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Survivor bias: "at most \|L\|" headlines for A − NB and A − FP32-E computed over surviving pairs only; A-side failures are the likely losses (FP32-E passes (c) almost surely) | phys A1 | A | **A** | Case 3. Fact confirmed (grep above). Anti-conservative in the thesis's favour; "a limitation admitted in prose but absent from the uncertainty". No independent evidence lowers it. Extended to the general Paired-gaps bullet (arbiter, §6.3.2). Fix 1 |
| 2 | FP32-E K=7 join to wave-1 pods gated on memory only; [D15] 14-day projection made at K=6; FP32-E gets no GPU canary on that path | crit B1, cons B1 | B, B | **B** | Case 1. The only finding that can change wave-1 production (pod composition, A's T_run, [D15] options). Same wording in the NB slot-7 row. Fix 2 |
| 3 | Precision claim named "close" with no margin; Scope licenses citing it on "close to full precision" | crit B2 | B | **B** | Case 3; confirmed. Thesis-favourable default reading of an unresolved result. Fix 3 |
| 4 | Precision headline L > 0 branch hides the sign and the anomaly | crit B3, cons B2 (part) | B, B | **B** | Case 1. Same class as v5 #4. A resolved A > FP32-E is a pipeline red flag. Fix 3 |
| 5 | "At least \|U\| pt" read off the unadjusted interval while the verdict is Holm-adjusted, at both headlines | cons B2 | B | **B** | Case 3; confirmed. At A − NB the defect is arbiter v5 fix 2's text; it is fixed, not closed by citation. Fix 3 |
| 6 | No plausibility check on the reference arm: an under-trained or broken FP32-E shrinks A − FP32-E toward "close" | phys C3, crit C6, cons C2 | C, C, C | **B** (arbiter) | Motivated-reasoning check: the failure direction favours the thesis and nothing pre-registered catches it short of fix 3's L > 0 branch. One pre-registered line, before any number. Fix 4 |
| 7 | "No quantizer variables in any layer" cannot pass: the fixed `_table(1, 20)` softmax tables are `kif` quantizers with k/i/f variables | crit B4 | B | **B** | Case 3; verified on HGQ2 v0.2.0 source, pin 0.1.9 unconfirmed. A gate that cannot pass as written (v5 #5 class). Fix 5 |
| 8 | `binary_gate` (`ablation.py:582`) not handled for FP32-E; also absent for NB | crit B6 | B | **B** | Case 3; verified. Extended to NB ([A22]). Fix 6 |
| 9 | [A25] pairing gate can pass on a partial intersection of variables; `matching_initialization` on an fp32 reference not shown | phys B2 | B | **B** | Case 3. `a17_pairing_d25_8seeds.json` records `n_shared: 15`; [A25] fixes no count. Fix 7 |
| 10 | FP32-E config hygiene: stripped keys not listed; no PREFLIGHT diff | phys B3 | B | **B** (residual) | Case 3. [A25] l. 1775-1778 already requires the reads/ignores/refuses determination and "only keys the path reads"; what stands is the explicit list and the printed diff. Fix 8 |
| 11 | Conventions rows Configurations, Cost accounting, Selection under a budget not amended for FP32-E | crit B5 | B | **B** | Case 3; l. 1364-1366 confirmed. The table is where compliance is checked. Fix 9 |
| 12 | Attention entropy promised (l. 1005, 1032, 1069, 1186) with no implementation item or test | phys B1 | B | **B** | Case 3; confirmed. Offline script, not a training tap (checks above). Fix 10 |
| 13 | [D24] DECISION block stale ({A − NB, H − NB}, K=4) | phys C1, crit C1 | C, C | C (required) | Contradicts body l. 915 and [D24] l. 1534. Fix 11 |
| 14 | Second-wave Cost bullet "16 runs at K=4" | phys C2, cons C3 | C | C (required) | Fix 11 |
| 15 | Holm price of the third member not stated | cons C1 | C | C (required) | Adding A − FP32-E makes A − NB harder to falsify when A − FP32-E fails or when A − NB has the smallest p (α/3 against α/2); thesis-favourable in direction, pre-registered before any number, so not post hoc; one sentence. Fix 11 |
| 16 | No designer [D26] entry in `decisions.md` | crit C2 | C | C (required) | [D25] precedent. Fix 11 |
| 17 | Second-wave launch gate names only [A22]/[A23]; "two of three pass" rule; expected gate line | crit C3 | C | C (required) | Fix 11 |
| 18 | Splices (fix 1 grammar l. 895-896; fix 5 nesting l. 393, 1543, 1712) | crit C4, C5, cons C4 | C | C | Fix 11 |
| 19 | Question presupposes the sign ("how far is A below it?") | cons C5 | C | C (required, with fix 3) | Fix 3 |
| 20 | Figures: separate iso-EBOPs and package gaps; stack the decomposition; FP32-E band on the primary figure | phys C5, C6, cons C6 | C | C (optional; C5 required) | Fix 11 |
| 21 | Per-class paired AUC gaps; "at this recipe"; scope reminder | phys C3, C4, C7 | C | C (optional) | "at this recipe" folds into fix 3 |

## Earlier A and B findings (arbiter v5), by name

| v5 # | finding | status | evidence (arbiter's line check at 54bf3e7) |
| --- | --- | --- | --- |
| 1 | outlier count median-relative | **resolved** | l. 895-903: range, count against best seed, A-against-D discordant counts, "0 of 3 ... 2 of 3 ... 5.46 pt" (critical recomputed 72.64 / 67.18 / 67.21) |
| 2 | extra pairs unfenced; wave-2 readout unblinded | **resolved** | l. 950-962 verbatim; packet carries sd_diff, pair count, n, not the gap or sign; seeds 9..n A − NB only; Kai row l. 1863 |
| 3 | sd_diff proxy understates A − NB | **resolved** | l. 952-955 "prior only; binding input is the second-wave epoch-500 readout" |
| 4 | A − NB headline inverts when L > 0 | **resolved** as prescribed; new defect in the same sentence is #5 above (Holm vs \|U\|) | l. 924-929 |
| 5 | C′ gate "0.01" | **resolved** | l. 393-394, 1543-1544, 1712-1713; `cpu_gate_d25.log:116` empty record; `decisions.md` correction appended |
| 6 | A07-350 expectation counts the head | **resolved** | l. 836-846, l. 1188-1189; `static_floors_arms_s1_d25.json` per-layer values confirmed by critical |
| 7 | REPORT-use restriction | **superseded** by [D26] (its own condition); the rewritten Scope is finding #3 above | l. 274-281 |

## Regression triggers (§6.7), checked independently

STUDY is the origin phase; no result exists. Selection on held-out or changed after results: not
met (validation only; FP32-E selects on validation over (c)-passing epochs, l. 507-510). Val/ROC
AUC > 0.01, single-seed headline, cross-N series, gap < sd at < 3 seeds: not met (no numbers).
Reload > 1e-7 / TF32: not met (FP32-E certification is reload determinism at 1e-7, TF32 off).
EBOPs not remeasured: not met (certification l. 619-630; FP32-E carries no EBOPs). Binary > 2
values: not met (`binary_gate` on binary arms; FP32-E/NB exemption is fix 6). DSP / C-sim /
C-synth: not applicable. Per-class AUC hidden: not met. Byte-identical arms / different `y`: not
met (`a17_pairing_d25_8seeds.json`; `y` byte-equality across 80 runs pre-registered, l. 1361).
Failed validation or tautological comparison: not met. [D] replaced without dated amendment: not
met; [D24]'s body carries the dated amendment (l. 1534), only its DECISION block is stale (#13).
Outward mismatch: not applicable. **No trigger met.**

## Validation target (§6.8) and competing group

No binding reference for FP32-E: the archived FP32 N=64 79.1 ± 0.3 % is ungated 80/20 and sizing
only. That is correct under §6.8, and it is why fix 4 adds a plausibility line rather than a
Tier-1 check. Competing group: a stated closeness margin or no "close" verdict (fix 3), measured
timing for every packing (fix 2), and a reference-arm sanity line (fix 4). Nothing else missing
that STUDY does not name as a limitation or Kai row.

## Disputed facts for the investigator

None. The HGQ2 0.1.9 `kif` variable fact is settled by fix 5's assertion on the pinned build, so
it does not need the investigator.

## Dismissals

None.

## Motivated-reasoning check

Every open item except #11 and #12 leans thesis-favourable by default: survivor pairs shrink
"at most |L|" (#1); an unresolved package gap reads as "close" (#3); a binary model above FP32 reads
as "no cost" (#4); a headline asserts a cost bound the Holm verdict denies, or omits it (#5); a
broken reference shrinks the gap (#6); the third Holm member lowers A − NB's power (#15). None
needs a number to fix; all are fixed before any number exists.

## Does anything bear on the pilot or on wave-1 production?

- **Pilot:** composition, manifests, ConfigMap and code are unaffected by every finding. The pilot
  **readout** is affected by #12 only: l. 1186 promises entropy at epoch 500, so the fix-10 script
  must exist, with its tests passing, before that readout (about 16-26 h after pilot start); if it
  does not, the readout prints entropy as "pending, computed from the retained epoch-500 snapshot"
  and the fix lands before wave-1 production. No pilot pod is restarted for it.
- **Wave-1 production, substantively:** #2 only (the K=7 join changes wave-1 pods and A's T_run).
  #1's extension to the general Paired-gaps bullet governs wave-1 VERIFY wording, not what trains.
- **Wave-1 production, procedurally:** all A and B items block it through Kai's condition 3
  (v6 PASS before wave-1 production), which this verdict does not meet.
- **Wave 2 / VERIFY / REPORT:** #1, #3-#11 (FP32-E and A − NB analysis and gates).

## Attention entropy: code item or VERIFY computation?

Neither a training-code change nor a VERIFY afterthought. It is an offline readout script
(ml-engineer, about 1 agent-hour) run on saved checkpoints: the pilot's epoch-500 snapshot and,
at VERIFY, each selected `model_best.keras`. No tap in the runner is needed and no pilot pod
changes. It is due before the pilot's epoch-500 readout because the readout promises it
(l. 1186) and the A07-350 expectation (Q·K logits jet-independent) is read beside it.

## Verdict

**ITERATE** (STUDY panel, iteration 6 → fixer, then v7). One A (#1), eleven B (#2-#12), all STUDY
text plus one analysis script. **Strong warning (§6.5, iteration 6).** Arbiter v5's "if v6 finds
only restatements, v6 is the last STUDY iteration" does not apply: Kai added new scope (FP32-E
[D26]) after v5, and ten of the twelve items are in that new text. ESCALATE is not the verdict:
no disputed A, no falsified claim, no resource wall, cap 10.

v7 scope, binding: reviewers check only that fixes 1-11 landed as written at every listed site,
that fix 10's script and tests exist with a pass line, and that no listed site was missed. A new
B only if an edited sentence is itself wrong (a number, a sign, a contradiction with code). A
restatement of an item adjudicated here or in v5 is closed by citation.

## Ordered fixes (fixer; experiment-designer if CANNOT RESOLVE; ml-engineer for fix 10)

1. **(#1) Survivor bias.** (a) Append to the "Paired gaps" bullet (l. 772-775): "Beside every
   paired gap the report prints the one-sided failure counts (seeds with an accuracy number in
   one arm only, per arm); with fewer than 8 pairs every paired gap is labelled 'among k
   surviving pairs'." (b) At the end of the A − NB headline item (after l. 929) and of the
   precision-package headline item (after l. 985) add: "The words 'at most |L| pt' are used only
   when all 8 pairs survive. With 6 or 7 pairs the headline reads '... among k surviving pairs'
   and prints the A-only and partner-only failure counts beside it, with one pre-registered
   sensitivity line: each A-only failed seed is imputed at the lowest ROC-test accuracy among the
   surviving A seeds and paired with its partner's actual ROC-test accuracy; partner-only failures
   stay excluded; the interval is recomputed over the 8 − (partner-only) pairs. The surviving-A
   minimum is used, not p_maj, because it is the least extreme value that does not assume a
   failed binary seed did better than every surviving one. The sensitivity line is labelled
   'worst-case imputation, not a measurement' and does not change the verdict." (c) At l. 971-973
   (A − NB feasibility counts), the same for A against FP32-E: add under "Precision package" (l.
   992): "A's and FP32-E's feasible, feasible-degenerate, diverged and certification-failed counts
   side by side, with the exact McNemar test on the discordant seeds."
2. **(#2) K=7 join.** At l. 1321-1323 replace "only if 7 × the canary's measured peak GPU memory
   per process fits the production GPU's memory; otherwise it stays in the second wave" with
   "only if a K=7 re-canary of one wave-1 pod (epochs 1-10, its six wave-1 runs plus FP32-E-s)
   shows (i) 7 × peak GPU memory per process within the production GPU's memory, (ii) a projected
   wave-1 T_run = 7,000 × s_e at K=7 of at most 14 d ([D15]), and (iii) FP32-E-s passing the
   finite-loss and epoch-10 train-loss checks; no scaling of the K=6 s_e is accepted in place of
   (ii). Otherwise FP32-E stays in the second wave at K=6." In the NB row (l. 1866) replace "the
   canary shows K=7 fits at batch 2,790" with "a K=7 re-canary as in FP32-E's launch rule (Budget,
   FP32-E) passes (i) to (iii) with NB-s in slot 7". In the FP32-E Kai row (l. 1864) replace "the
   canary shows K=7 fits" with "the K=7 re-canary passes"; same in the [D26] DECISION block
   ("and memory fits" → "and a K=7 re-canary passes"). Change-log line: "no change to any wave-1
   arm, seed, target, pilot or selection rule; wave-1 pod composition changes only after a
   measured K=7 re-canary".
3. **(#3, #4, #5, #19, #21 part) Precision claim and both headlines.** l. 979-980 claim →
   "Precision package (FP32-E ...): 'binary weights with learned-width activations at 350k EBOPs
   cost no top-1 accuracy against the same E model in unconstrained FP32, at this recipe'
   (package; A against FP32-E; not iso-EBOPs, [D26]). The report prints the interval and never
   issues 'close' as a verdict." Headline (l. 981-984) → "If L ≤ 0: 'binary weights with
   learned-width activations at 350k EBOPs cost at most |L| pt of top-1 accuracy against the same
   E model in unconstrained FP32 at this recipe (package, n pairs, 95 %)'. If L > 0: 'A exceeds
   FP32-E by at least L pt (package, n pairs, 95 %)', and the result goes to the investigator
   before REPORT, with checks of FP32-E's selection epoch, train and validation curves, the [A25]
   pairing record and the byte-equal `y` check." In both headlines (here and l. 925-926) replace
   "adding 'and at least |U| pt' when U < 0" (or "when the upper bound U < 0") with "adding 'and
   at least |U| pt' only when U < 0 and the verdict below is 'resolved cost' (FP32-E) or
   'falsified' (A − NB); otherwise the interval is printed and labelled 'unadjusted 95 %'". Scope
   l. 276-278: replace "may cite A − FP32-E as evidence on the thesis's 'close to full precision'
   claim" with "may cite the A − FP32-E interval as evidence bearing on the thesis's 'close to full
   precision' axis, printing the interval and never the word 'close' as a verdict". Question
   l. 225-226: "how far is A below it?" → "what is A − FP32-E?". Null H0-precision (l. 248) and
   Bearing (l. 269) aligned to the same wording if they say "close".
4. **(#6) FP32-E plausibility.** Add under "Precision package" (after l. 994): "Plausibility
   (pipeline check, not a result): if FP32-E's seed-mean validation accuracy at its selected
   checkpoints is below A's, or below 79.4 %, FP32-E goes to ml-engineer before it enters REPORT,
   and A − FP32-E is not reported until the cause is found or ruled out. The archived N=64 FP32
   79.1 ± 0.3 % (ROC-test, ungated, 80/20, reference table) is printed beside it as sizing context
   only." Append to the FP32-E epoch-500 rule (l. 1339-1340): "The readout also prints FP32-E's
   seed-mean validation accuracy (validation, n = 62,000, as of epoch 500, never quoted) beside
   A's."
5. **(#7) Quantizer-variable check.** At l. 513, l. 1367, [D26] l. 1554-1560 and the [D26]
   DECISION block, replace "no quantizer variables in any layer and float kernels" with "no
   quantizer variables except the two fixed, non-trainable softmax tables per block (`kif`,
   k0 0, i0 1, f0 20, SAT; asserted unchanged from init), and float kernels". Add an [A25]
   bullet: "the [D26] check runs on the pinned hgq2 0.1.9 against the built model's variable
   list and prints the table variables it allows".
6. **(#8) `binary_gate`.** Add an [A25] bullet: "`binary_gate` (`ablation.py:334-341`, called at
   `:582`) is skipped for `quant.weight: \"none\"` and replaced by the [D26] check at the
   selected checkpoint." Add the same for NB to [A22]: "`binary_gate` is skipped for NB's `kbi`
   weights and replaced by the no-int8-grid test and the per-layer width record." Conventions
   row "Validation checks 1-4" (l. 1367) cites both.
7. **(#9) Pairing count.** In [A25]'s pairing bullet, after "variable paths matched across the
   float and binary layer classes", add "with `n_shared == 15` (the A kernel and bias set of
   `a17_pairing_d25_8seeds.json`) and `only_in_arm`, `only_in_f` empty at every seed, and
   `matching_initialization` shown to run on an FP32-E config (its `calibrate_activations` and
   `expected_binary_layers` steps); otherwise the gate reports UNPAIRED and A − FP32-E is Welch".
8. **(#10) Config hygiene.** In [A25]'s build bullet, after "FP32-E configs carry only keys the
   path reads", add "; the stripped keys are listed by name (at least `act_overflow`,
   `softmax_quant`, `i_decay_speed`, and any `act_calib` / `act_policy` value the fp32 path
   refuses or ignores), and PREFLIGHT prints the diff of FP32-E-s1 against A-s1".
9. **(#11) Conventions rows.** Append to "Configurations" (l. 1364): "FP32-E [D26]: float weights,
   quantizers off except the fixed softmax tables." To "Cost accounting" (l. 1365): "FP32-E: no
   EBOPs, reported as 'FP32, unconstrained'." To "Selection under a budget" (l. 1366): "FP32-E:
   no budget; selection over all epochs meeting (c), a labelled part of the package [D26]."
10. **(#12) Entropy, [A26] (ml-engineer).** Add: "[A26] **Attention-entropy readout.** An offline
    script loads a saved `.keras` (`load_model(compile=False)`), builds a sub-model on each
    `{blk}_attn_softmax` output (`qat.py:574`; both the binary and fp32 branches), runs the
    validation split (n = 62,000), and reports per block and head the mean over jets and query
    rows of −Σ p log p over the 64 keys, divided by log 64, from the quantized softmax output as
    the model computes it. CPU unit tests: uniform logits give 1 within 1e-6; one-hot logits give
    about 0. Due before the pilot's epoch-500 readout; run at VERIFY on every selected
    checkpoint. No change to the runner or to pilot pods." Replace "from one validation forward
    pass with the softmax tap" (l. 1032) with "from one validation forward pass [A26]".
11. **C items, apply now.** [D24] DECISION block (l. 1961-1963): append "amended 2026-09-27:
    family {A − NB, H − NB, A − FP32-E}; K=6 with FP32-E". Cost bullet (l. 1297-1298): "16 runs
    at K=4 on 4 pods (24 runs at K=6 with FP32-E, same pods)". After the Holm-family sentence
    (l. 920): "A third member costs power on A − NB: tested first at α/3 instead of α/2, and not
    testable once A − FP32-E has the smaller p and fails; the direction makes A − NB harder to
    falsify, and the choice is fixed before any number." Second-wave "Launch gate" (l. 1279-1283):
    add [A25] for FP32-E, and "each arm launches on its own gates; any subset that passes
    launches"; name the expected gate line after FP32-E joins ("`PREFLIGHT_ALL_PASS 66 production
    64 pilot_only 2`" if in the wave-1 gate, else a second-wave gate line). Fix splices at
    l. 895-896 ("per arm, the feasible-degenerate count, the seed range ...") and l. 393, 1543,
    1712 (one clause each). Second-wave figure: A − NB and A − FP32-E in separate panels.
    `decisions.md`: append a dated experiment-designer [D26] entry with a Check line. Optional:
    phys C4 per-class paired AUC gaps; cons C6 decomposition stack; phys C6 FP32-E band.
