# STUDY arbiter v8: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-27. Artifact `STUDY.md` at fba27d5 (2,281 lines; `git diff
fba27d5 -- STUDY.md` empty). Reviews v8: `STUDY_physics_v8.md`, `STUDY_critical_v8.md`,
`STUDY_constructive_v8.md`. Validators `STUDY_validators_v8.txt`: `prose_lint` score 0, no A line.
No figures at STUDY, so no plot-validator file. Earlier arbiter `STUDY_arbiter_v7.md`. Also read:
`RUN.md` (the pilot launch record), `docs/methodology/06-review.md` §6.1-6.8, the conventions rows
of the artifact. Iteration **8** (strong-warn tier, §6.5; ESCALATE at 10).

## Independent checks made by the arbiter

- **Pilot as launched (phys B1; physics did not open RUN.md, so it marked the fact disputed).**
  Settled here, not disputed: `RUN.md` l. 73 (A07-350-s1, attempts 0, 1, 2 all OOM,
  `ARM_FAILED_AFTER_RETRIES`, "permanently dropped"), l. 74 and 98 (C′-s1 OOM twice, running on
  its third and last attempt), l. 89-92 (five or six resident arms at 18.8-22.6 GiB of 23.0 GiB on
  the A10), l. 100-104 (no relaunch; recovery left open, with "smaller batch for that arm alone"
  among the options). STUDY carries no amendment: l. 1309-1327 still register six pilot arms,
  l. 1351-1353 the A07-350-s1 epoch-500 rule, l. 1401 a canary stability rule "for every arm"
  that cannot pass with A07-350-s1 absent. STUDY already pre-registers the branch that now
  applies: l. 1295-1297 ("If the canary shows K=6 does not fit in GPU memory at batch 2,790, the
  block splits into two pods of K=3 (A, B, D and C, F, A07-350), giving 16 pods") and l. 1408
  ("If K=6 does not fit in GPU memory, repeat the canary at K=3"). 16 seed-block pods plus 2 R
  pods exceed the 8-10 Kai answered (l. 1302-1306, Kai row l. 2087). The GPU classes allowed
  (l. 1299-1300) include 3090 (24 GiB) and 2080 Ti (11 GiB), at or below the A10 that failed.
  The batch 2,790 is in the question line (l. 6), so a per-arm batch cut changes the arm.
- **Collapse label (phys B2).** `grep -n -i "collaps\|deep.set"`: l. 1180-1187 define the three
  attention numbers and say what "near 1" means, l. 2259-2260 name the collapse; no cut turns
  them into a label, unlike WRAP overflow (0.1 %, l. 1174-1179). Confirmed. On the entropy
  quantity: constant logits give equal quantized softmax values, which the [A26] row
  renormalization makes exactly uniform over all 64 slots, padding included, so the unmasked
  [A26] value is 1 for the constant-logit collapse; the masked companion (cons v7 C5) is not
  needed for this label and stays optional.
- **Power (phys B3).** Recomputed, noncentral t, α = 0.05 two-sided, 80 % power, 8 pairs (df 7):
  detectable paired gap = **1.16 · sd_diff** (`scipy.stats.nct`, power 0.803 at 1.16). At
  sd_diff = √2 · 3.145 = 4.45 pt: **5.2 pt**; at 1.19 pt: 1.4 pt; at 1.0 pt: 1.2 pt. Physics'
  4.4 pt is the normal approximation ((1.96 + 0.84)/√8 · 4.45); its 1.15 pt at sd_diff 1.0
  agrees. STUDY states half-widths (l. 752, 758, 1092) and the sizing formula (l. 1060-1072), not
  a detectable gap. The Sloot prior (l. 1054-1057) is 0.9276 against 0.9178 **AUC**, a different
  task: about 1 pt of AUC, not an accuracy prediction. Finding stands, number corrected.
- **FP32-E label (crit B1, cons B1).** l. 1150-1151 "Any distance of FP32-E to 79.4 % ... worded
  as A − 79.4". A − 79.4 is the registered A-arm quantity (l. 943, 1561). Confirmed; the text is
  mine (arbiter v7 fix 2).
- **Gate counts ([A21], crit C1 and its note to the orchestrator).** `grep` of
  `code/evidence/cpu_gate_shipped_77f1ca4e.log`: config names a × 8, a07-350 × 8, d × 8,
  cprime × 1, e1 × 1 (each printed twice), no b, c, f or r; l. 55 `PREFLIGHT_ALL_PASS 26
  production 24 pilot_only 2`. [A21] requires re-assertion on the shipped tree for B, C, F, R.
  The orchestrator reports a full-set gate on the shipped bundle running now.
- **Table 1 rows (cons C3).** `pdftotext -layout` of the cited PDF: DSP > 0 on the Deep Sets
  (QKeras) rows (626 / 555 / 434), Deep Sets M (QKeras) (548) and Deep Sets L (QKeras) (2,458), zero on every MHA,
  Linformer, Deep Sets (HGQ) and MLP Mixer row. STUDY l. 347 names only "Deep Sets (QKeras)".
  Confirmed; my v7 fix 6 text.
- **v7 fix sites.** Critical and constructive each read every site at fba27d5 and cite lines; I
  re-read l. 1004-1009, 1028-1033, 1048-1053, 1140-1151, 1186, 1345, 1468-1470, 2095, 2098 and
  the fixer change log l. 254-280. All nine v7 B landed verbatim (table below).

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | FP32-E's distance to 79.4 % labelled "A − 79.4" | crit B1, cons B1 | B, B | **B** | Case 1; confirmed at l. 1150-1151. Origin: my v7 fix 2. Bears on wave-2 VERIFY wording only. Fix 1 |
| 2 | Pilot not as registered: A07-350-s1 lost to OOM, no amendment; A07 floor-accounting check has no data; K=6 memory assumption for production broken | phys B1 | B (disputed fact) | **B** (fact settled from `RUN.md`) | Case 3 with case 4 settled by the arbiter: RUN.md l. 73, 89-92, 98. A met pre-registered branch (l. 1295-1297, 1408) with no dated amendment; the canary rule "for every arm" (l. 1401) cannot pass as written. Bears on the pilot (canary read, epoch-500 readout) and on wave-1 production (pods, packing, [D15] packet). Fix 2 |
| 3 | No pre-registered threshold turns the attention diagnostics into a "Deep-Set-class" label | phys B2 | B | **B** | Case 3, on text unchanged since v6: judged on merits. Under [D19] E reaches 350k only by pruning Q·K and A·V (l. 545-548), so collapse is a live outcome for A and NB, and a cut chosen after pilot numbers exist is a forking path (pilot A-s1, A-s2 may resume into production, l. 1417). Deadline: before the pilot's epoch-500 readout. Fix 3 |
| 4 | Resolving power given as a half-width, not as the gap detectable with 80 % power, for A − NB | phys B3 | B | **B** | Case 3; §6.3 Q4 asks for resolving power at the claimed gap. Number corrected by the arbiter (5.2 pt, not 4.4). The proposed new blocking rule is not adopted: "not falsified at this resolution" (l. 1090-1094) and "no non-inferiority pass" already stop a "no cost" claim. Wave 2 and REPORT. Fix 4 |
| 5 | Gate-count parenthetical does not say 26 / 24 / 2 is an `--only` subset; reads as 26 + 8 | crit C1, cons C1 | C, C | C (required) | Case 1. The substantive gap ([A21] not asserted for B, C, F, R on a shipped bundle) is a PREFLIGHT prerequisite of wave-1 production, not a STUDY finding; the ml-engineer gate now running closes it. Fix 5a |
| 6 | Fixer's v7 change-log entry has no sha | crit C2, cons C5 | C | C (required) | Fix 5b |
| 7 | First-wave Holm copy ends "against the thesis in the second wave"; step-down clause | phys C4, crit C4, cons C2 | C | C (required) | Three reviewers; one-line edits. Fix 5c, 5d |
| 8 | Fix 6 names one of three Deep Sets (QKeras) rows | cons C3 | C | C (required) | Confirmed from Table 1; my text. Fix 5e |
| 9 | Per-class ROC legends do not print per-class AUC (seed mean ± sd), so the REPORT legend-against-table check cannot run | phys F1 | C | C (required) | §6.4 makes a legend-table mismatch Category A at REPORT; the spec should enable the check. Fix 5f |
| 10 | Reference's own noise absent beside A − 79.4 and in the primary figure caption | phys C1 | C | C (required) | [L1] (l. 2030-2037) admits it in prose; motivated-reasoning rule: a limitation in prose must reach the figure that shows the distance. Fix 5g |
| 11 | Attention-state figure caption lacks split and n; no cut drawn | phys figure table | C | C (required) | Follows fix 3. Fix 5h |
| 12 | Entropy tag at two figure sites; working point 10⁻² vs rejection at 0.5 in the Metrics row; trigger metric for A and R; χ² interval on the epoch-500 sd; (b) nearly vacuous; duplicated rule text; carried v7 optionals (#16, #17) | crit C3, C5, cons C4, phys C2, C3, C5, C6, C4 (duplication) | C | C (optional) | Fix 6 |

## Earlier A and B findings (arbiter v7), by name

| v7 # | finding | status | evidence (arbiter's read at fba27d5) |
| --- | --- | --- | --- |
| 1 | [A26] definition contradicts the script | **resolved** | l. 2018-2024 against `code/analysis/attn_entropy.py:12-18`; tests on the renormalized primary, `code/evidence/pytest_shipped_77f1ca4e.log:65-73` (`71 passed, 2 skipped`); tag at l. 1186, 1345 |
| 2 | Plausibility gate (79.4 % limb, 79.1 % print, open exit) | **resolved**; one wrong label in the prescribed text is new #1 | l. 1144-1151, four-item record; `grep 79.1` hits only the reference table l. 383 and the sizing sd |
| 3 | Holm m under dropouts, both families | **resolved** | l. 1004-1009, 1028-1033, conventions row l. 1560 |
| 4 | Both-failed seeds in pair count and Paired-gaps bullet | **resolved** | l. 863-866, 1048-1049, 1123-1125 |
| 5 | "Worst-case imputation" label | **resolved** | l. 1052-1053, 1127-1128; `grep worst-case` 0 hits |
| 6 | W&B group hard-coded to wave-1 canary | **resolved** | l. 1547-1549; `code/patches/0026-*.patch:68` `stage_group` |
| 7 | Bearing omits DSP = 0 comparands | **resolved**; row naming incomplete, #8 (C) | l. 346-352; Table 1 |
| 8 | Paired macro and per-class AUC gaps | **resolved** | l. 1102-1105, 1140-1143, 1223-1224 |
| 9 | Budget claim screens only controller or training failure | **resolved** | l. 923-926 |

Required v7 C items 9a-9g landed (l. 2095, 2098, 1486, 1363, 833-834, 1358-1359, 1542, 210, 1468-1470);
9g wording is #5 above.

## Regression triggers (§6.7), checked independently

STUDY is the origin phase; no result exists. RUN.md telemetry (val_AUC, epochs 1-3) is labelled
"telemetry, not results" and selects nothing. Selection on held-out or changed after results: not
met. Val/ROC AUC > 0.01, single-seed headline, cross-N series, gap < sd at < 3 seeds: not met.
Reload > 1e-7 / TF32: not met. EBOPs not remeasured: not met (certification rule l. 1355-1370).
Binary > 2 values: not met. DSP / C-sim / C-synth: not applicable ([L7]). Per-class AUC hidden:
not met. Byte-identical arms / different `y`: not met. **Failed validation accepted without
remediation: not met, conditionally.** The GPU-memory fit is a canary item and it failed for
A07-350-s1; the remediation is pre-registered (l. 1408) but not yet executed or recorded. Fix 2
records it. If wave-1 production launched without fix 2 and the K=3 re-canary, this trigger would
be met. **[D] or registered design replaced without dated amendment: not met, conditionally.** The
pilot composition changed de facto on 2026-09-27; fix 2 is the dated amendment. Outward mismatch:
not applicable. **No trigger met.**

## Validation target (§6.8) and competing group

No arm is bound at VERIFY (l. 1561); correct. A competing group would label a collapsed
transformer as a Deep Set before quoting it against a Deep Sets comparand (#3), would state the
detectable gap of its thesis comparison (#4), and would not report a Deep Sets comparand's
distance without that comparand's own noise (#10). All three are fixed below in text.

## Disputed facts for the investigator

None. Physics B1's fact is settled from `RUN.md` l. 73, 89-92, 98.

## Dismissals

None. Physics B3's proposed blocking rule is not adopted, with evidence (l. 1090-1094), not
dismissed: the finding itself stands and is fixed.

## Motivated-reasoning check

#3 leans thesis-favourable by default: without a cut, a collapsed A can be read as a transformer
beside a Deep Sets comparand. #4 likewise: without a detectable-gap sentence, an unresolved A − NB
reads as reassurance. #2's pressure runs the other way: the easy path is to accept the gap and ship
production on the original 8-10 pod plan, which would launch A07 arms whose only pre-registered
floor-accounting check never ran, into a packing that OOMs. The fixes below close all three before
any number exists. #1 and #8 are defects in text I prescribed at v7.

## Bearing: pilot epoch-500 readout, wave-1 production, wave 2 / REPORT

| # | pilot (canary read, epoch-500 readout) | wave-1 production | wave 2 / VERIFY / REPORT |
| --- | --- | --- | --- |
| 1 FP32-E label | no | no | yes (VERIFY wording) |
| 2 pilot amendment | **yes**: canary rule per pod; A07-350-s1 read from the K=3 pod; C′ wording | **yes**: which pods wait, packing, pod count, GPU classes, [D15] packet (Kai) | no |
| 3 collapse label | **yes**: fixed before the epoch-500 readout (about 30 h after launch at the telemetry 218 s/epoch, near 2026-09-29 03 UTC; projection) | yes (headline counts at wave-1 VERIFY) | yes |
| 4 detectable gap | no | no | yes (wave-2 epoch-500 packet, cap row, REPORT) |

The canary read now in progress may finish before fix 2 lands. It then records A07-350-s1 as "not
read in this pod (OOM), see STUDY amendment 2026-09-27 (arbiter v8 fix 2)", not as a pass or a
fail, and the canary verdict covers the arms that trained.

## A07-350-s1: what the pilot and production do, and who decides

- **Re-run A07-350-s1 in a separate pod at K=3: do it; not a Kai decision.** It is the branch STUDY
  already registered (l. 1408, l. 1295-1297), under the standing grant. The new manifest passes
  `nrp_doctor.py lint` (the hook enforces it) and is recorded in PREFLIGHT.md as an addendum with
  its lint output, at the PREFLIGHT tier (§6.2). Agent cost well under 1 h; GPU cost one pod for
  about 1-1.5 d to epoch 500.
- **Accept the gap for the pilot: not granted here.** The fix is under an hour of agent time
  (§6.5.1), and the A07-350 check is the only pre-registered test of the A07 floor accounting
  before production. If the orchestrator wants it anyway, it is Kai's decision.
- **Change production packing: Kai's decision**, bundled with the [D15] timing breach (218 s/epoch
  at K=6 projects 17.7 d, RUN.md l. 127-129). K=3 gives 16 + 2 pods against the 8-10 he answered;
  keeping K=6 needs a GPU-class restriction to cards that hold the measured peak. Neither is
  decided by an agent.
- **Lower the batch for A07-350 alone (RUN.md l. 103): ruled out.** Batch 2,790 is in the question
  (l. 6); it changes the arm.

## Verdict

**ITERATE** (STUDY panel, iteration 8 → fixer, then v9). No A; four B (#1-#4), all STUDY text.
**Strong warning (§6.5): iteration 8 of 10; ESCALATE at 10.** Not ESCALATE: no disputed A, no
falsified claim, no resource wall reached by the arbiter; the [D15] timing and the packing go to
Kai through the pre-registered [D15] route, not as an escalation of this review.

**PASS is reachable after one fixer pass.** v9 checks landing only: every fix below at its site,
verbatim, and no listed site missed. A v9 restatement of an item adjudicated here or earlier is
closed by the evidence recorded in this file or its predecessors. A STUDY PASS alone does not
launch wave-1 production: that also needs the full-set CPU gate ([A21]), the pilot A rule and
certification, the K=3 pod's A07-350-s1 readout (and any floor-accounting fix) for the pods that
hold A07-350 or C, and Kai's
answer on [D15] and packing.

## Ordered fixes (fixer; experiment-designer if CANNOT RESOLVE)

1. **(#1) FP32-E label, l. 1150-1151.** Replace "worded as A − 79.4, and triggers nothing (arbiter
   v7 fix 2)." with "worded as FP32-E − 79.4 (the same descriptive form as A − 79.4), and triggers
   nothing (arbiter v7 fix 2; arbiter v8 fix 1)."

2. **(#2, deadline: before wave-1 production; the canary sentence as soon as possible) Pilot
   amendment.** At the end of the pilot "**Pod.**" bullet, after "so the C′-only fallback below is
   not triggered.", add:
   "*Amended 2026-09-27 (arbiter v8 fix 2; `RUN.md`; `.claude/memory/cluster-inventory.md` entry
   'K=6 pack, batch 2,790, two of six N64 arms OOM repeatedly on a 23 GiB A10 (2026-09-27)'):* on
   an A10 (23,028 MiB) the K=6 pilot pod lost A07-350-s1 to out-of-memory on all three attempts
   (`ARM_FAILED_AFTER_RETRIES`), C′-s1 trained only on its third attempt, and the resident arms
   used 18.8-22.6 GiB. K=6 does not fit at batch 2,790 on that class, so the registered branch
   'If K=6 does not fit in GPU memory, repeat the canary at K=3' applies. (1) A07-350-s1 re-runs
   in a separate pod at K=3 on the same GPU class, batch 2,790, stage pilot, W&B canary group,
   with C-s1 and F-s1 (the fallback seed block that holds A07-350). The pod launches once the
   full-set CPU gate on the shipped bundle ([A21]) has passed for C and F; the pods holding
   A07-350 or C wait for Kai's packing answer in any case, so the wait delays nothing. No
   batch is lowered: batch 2,790 is part of the recipe in the question. (2) The canary rules
   apply per pod: the K=6 pod's canary covers the arms that trained in it, and A07-350-s1's
   canary (stability, s_e, peak GPU memory per process) and its epoch-500 readout (the
   A07-350-s1 rule below) come from the K=3 pod. (3) Wave-1 pods that hold A07-350 or C launch
   only after the K=3 pod's A07-350-s1 epoch-500 readout exists and, on a mismatch with the
   A07-350 expectation, after ml-engineer has fixed the floor-accounting defect; other wave-1
   pods launch under the rules registered here. (4) The [D15] packet to Kai carries s_e and peak GPU memory per
   process from both pods, the pod count at K=3 (16 seed-block pods and 2 R pods, against the
   8-10 answered) and the GPU classes whose memory holds the measured peak; production packing
   and any restriction of GPU classes are Kai's decision. (5) If C′-s1 is lost to out-of-memory,
   the C′ report to Kai reads 'no pilot data (out of memory at K=6)', not 'infeasible'."
   In the Kai row "pod count" (l. 2087), append to the status cell "(superseded by 'wave-1
   packing after the A10 out-of-memory' if production runs at K=3; arbiter v8 fix 2)".
   At l. 1401, after "for every arm" add "that trained in the pod (per-pod reading, arbiter v8
   fix 2)". In "Where I am not sure", after the "pod count" row, add the row:
   "| wave-1 packing after the A10 out-of-memory (arbiter v8 fix 2) | K=3 seed blocks (A, B, D and C, F, A07-350), 16 pods and 2 R pods | K=6 on GPU classes that hold the measured K=6 peak; K=3 on classes that hold the measured K=3 peak | open; Kai decides with the [D15] packet, from the K=6 and K=3 pods' s_e and peak memory |"

3. **(#3, deadline: before the pilot's epoch-500 readout) Collapse label.** After the entropy
   bullet ending "paper's collapse)." (l. 1187), before "Widths come from", add:
   "Collapse label (fixed 2026-09-27, before the pilot's epoch-500 readout; arbiter v8 fix 3): a
   checkpoint is labelled 'Deep-Set-class' if every head meets at least one of
   (i) all Q channels or all K channels at 0 bits, (ii) all V channels at 0 bits, (iii)
   row-renormalized entropy / log 64 ([A26], no key mask) at least 0.99. Constant logits give a
   uniform row over all 64 slots, padding included, so the unmasked [A26] value is 1 for that
   collapse. For FP32-E only (iii) applies. A07-350 is Deep-Set-class by construction (Falsifier,
   'A07-350'); its measured label is printed beside that expectation, and a disagreement is
   reported, not relabelled. Every arm summary and every gap that reports an arm's accuracy
   (including A's k/8 summary, A − 79.4, the recipe claim, the four Holm secondary gaps,
   A − A07-350, C − A07-350, A − NB, A − FP32-E and H − NB) prints per arm the count of seeds whose
   selected checkpoint carries the label. The label is descriptive, like the overflow label: it selects, gates and
   blocks nothing."
   At l. 1345 replace "entropy (row-renormalized, [A26]))" with "entropy row-renormalized [A26],
   and the collapse label, arbiter v8 fix 3)".

4. **(#4) Detectable gap.** In the "Not falsified" bullet, after "the resolvable paired gap is
   about 3.7 pt (Seeds)." (l. 1092), add: "The gap detectable with 80 % power (paired t, α = 0.05
   two-sided, 8 pairs, noncentral t) is 1.16 · sd_diff: about 5.2 pt at zero pair correlation and
   the archived spread (sd_diff = √2 · 3.145 pt), 1.4 pt at sd_diff = 1.19 pt and 1.2 pt at
   sd_diff = 1.0 pt (arithmetic). The Sloot prior is about 1 pt of AUC on a different task, not an
   accuracy prediction; a cost of that order is detectable at 8 pairs only if sd_diff comes in
   near 1 pt, so 'not falsified at this resolution' is the expected outcome and the report says so
   (arbiter v8 fix 4)." In "Resolution", after "the n the formula gives at max(proxy, measured
   sd_diff);" add "the 80 %-power detectable gap at 8 pairs and at that n, at the same sd_diff
   (noncentral t; arbiter v8 fix 4);". In the Kai row 'extra A/NB pairs (cap)' (l. 2095), after
   "the 95 % half-width at the cap at the proxy sd_diff" add "and the 80 %-power detectable gap at
   the cap (arbiter v8 fix 4)".

5. **Required C, apply now.** (a) l. 1468-1470: replace "(58 and 56 in `cpu_gate_d25.log:119`;
   the shipped bundle 77f1ca4e gate reads 26 / 24 / 2, `cpu_gate_shipped_77f1ca4e.log:55`, plus
   FP32-E's 8 configs, [A25])" with "(the full wave-1 set, 58 and 56, `cpu_gate_d25.log:119`,
   plus FP32-E's 8 configs, [A25]; the shipped bundle 77f1ca4e was gated only on the `--only
   A,D,A07-350,C-PRIME,E1` subset, 26 / 24 / 2, `cpu_gate_shipped_77f1ca4e.log:55`, so B, C, F
   and R are not gated on a shipped bundle until the full-set gate on the production bundle
   passes, a PREFLIGHT prerequisite of wave-1 production, [A21]; arbiter v8)". (b) l. 257-258:
   "Line numbers in the working tree after this pass:" → "Line numbers at fba27d5:". (c) First
   Holm copy only (l. 1008-1009): delete "Direction: a smaller m makes the remaining members
   easier to falsify, which is against the thesis in the second wave." (d) Second copy (l.
   1030): after "m falls by one." add " It leaves the Holm step-down order as well." (e) l. 347:
   "except Deep Sets (QKeras)" → "except the Deep Sets (QKeras), Deep Sets M (QKeras) and Deep
   Sets L (QKeras) rows". (f) Per-class ROC figure specs (l. 1201-1204 and the second-wave per-class ROC, l.
   1221): add "; the legend prints each arm's per-class ROC-test AUC as seed mean ± sd (ddof = 1,
   k)". (g) Primary figure caption (l. 1196-1197): "external references single-model" →
   "external references single-model with no interval; their noise is unpublished, [L1] puts its
   scale at about 1 pt or more"; the same clause beside A − 79.4 where it is headlined (l. 943). (h) Attention-state figure (l. 1215-1216): after "entropy / log 64" add
   "(row-renormalized, [A26]); widths at the selected checkpoint from `activation_widths.jsonl`,
   entropy on validation, n = 62,000; the 0.99 collapse cut drawn". Change-log line: "arbiter v8
   fixes 1-5; pilot composition amended (fix 2); no change to any arm, seed, target, batch,
   selection or certification rule; production packing left to Kai".

6. **Optional C.** crit C3 (entropy tag at l. 1228), crit C5 / cons C4 (10⁻² working point in the
   Metrics row), phys C2 (signal efficiency at mistag 10⁻² for A and R), phys C5 (χ² interval on
   the epoch-500 sd), phys C6 ((b) wording), phys C4 (define duplicated rules once), and the
   carried v7 optionals #16 (masked entropy companion) and #17.
