# STUDY review, critical-reviewer, v4: 2026-09-26-training-batch

Panel mode, re-review (n = 4). No verdict; the arbiter decides. Artifact: `STUDY.md` (1,655 lines,
143,549 bytes, mtime 2026-09-27 09:23), `plan.md`, `code/` (patches 0001-0023, `tree/`) and
`code/evidence/` (CPU traces on synthetic samples, not results). Earlier findings:
`review/STUDY_arbiter_v3.md` #1-#18 and my `STUDY_critical_v3.md` (A1, C1-C6). Kai's launch-gate
answers (`decisions.md`, 2026-09-27 08:40: [D19] and [D21] confirmed, 8-10 pods, H and NB as a
second wave) are treated as decided. Bar for iteration 4: a new A or B only if it changes the
design, a number, or what a result can claim.

Validator output, verbatim (`review/STUDY_validators_v4.txt`):

```
Desktop/bnjettag/campaigns/2026-09-26-training-batch/STUDY.md  —  score 0, reads human
  23282 words · 569 sentences · mean 24 words (σ=18.3) · 17% bullets · 0 em-dashes
plan.md present: yes; E1-TRACE-PENDING tokens: 0
```

No A lines. STUDY has no figures, so `plot_check` does not apply.

## Recomputed or verified in this session

- **E1 floors** (`code/evidence/static_floors_fix6_a07_e_e1.json`, entry `e1-probe-n64-s1`, sample
  "synthetic standard normal, n=256, seed=0"): zero 85,763, one 533,435, attn_narrow 282,371,
  attn_full 392,963, headroom_at_zero_floor 264,237.
  - Headroom at 350k: 350,000 − 85,763 = 264,237; 350,000 − 533,435 = −183,435;
    350,000 − 282,371 = 67,629; 350,000 − 392,963 = −42,963.
  - At 250k: 164,237; −283,435; −32,371; −142,963.
  - E1 × 2 = 171,526 = the E zero floor (`e-probe-n64-s1`).
  - All match STUDY:99-101, 323-329, 343-347, 1256-1261.
- **A07 and E paper-rule sums** (same file): A07 605,197 / 801,805; E 368,134 / 478,726;
  `weights_only_rule` equals the zero floor for all three. These match STUDY:345-346.
- **CPU gate** (`code/evidence/cpu_gate_d21.log`, last line): `PREFLIGHT_ALL_PASS 58 production 56
  pilot_only 2`.
  - A-s1: params 31,735, kernel_bias_pos 6,253, zero_floor 171,526 (retraced 171,526).
  - A07-350-s8: params 61,951, kernel_bias_pos 11,653, zero_floor 343,053.
  - F-s1: zero_floor 171,526, retraced 171,526.
  - E1: zero_floor 85,763. C′: zero_floor 4,580,398.
  - Parameter counts match STUDY:190.
- **Pilot pod.** `pilot_packs.json` = `[[0, 1, 24, 48, 56, 57]]`. Mapped through `index.json`:
  0 A-s1 (E, 350k), 1 A-s2, 24 D-s1 (E), 48 A07-350-s1 (A07, floor 343,053), 56 C-PRIME-s1
  (current quantizer, 5M, floor 4,580,398), 57 E1-s1 (d24, h1, floor 85,763). This matches
  STUDY:857-860.
- **Production packs** (`packs.json`): eight blocks, each `[s, 8+s, 16+s, 24+s, 32+s, 48+s]`,
  which is A, B, C, D, F and A07-350 at seed s. R is packed as `[40-43]` and `[44-47]`, so there
  are 10 pods. This matches [D16] and STUDY:838-846.
- **Config keys** (`chang0926-{a,r,c}-n64-s1.json`):
  - `train.ebops_trace_sample: train_full` and `train.ebops_reload_check: stored`.
  - `experiment.nondegenerate` = {zero_floor_ebops 171,526 (A, R) / 343,053 (C), se_multiple 5}.
  - `arch.pos_enc_none_consume_rng: true` on A and R. C has none, since it has a learned PE.
  - epochs 7,000 / 1,000 and batch 2,790 / 256.
  - `order_seed` 2026092601 at s = 1.
  - **No `quant.i_decay_speed` key** (see C2).
- **[A17]** (`a17_pairing_d21_8seeds.json`): A, B, D and R against F are `paired: true` at all 8
  seeds. In every case `only_in_f` = `pos_enc/pos_table`, `differing_shared` is empty and there
  are 15 shared variables.
- **Trace cost** (`trace_cost_cpu.json`): trace_over_train is 0.6572 (A) and 0.6638 (A07-350).
  - 112.6 × 1.66 = 186.9 s. 7,000 × 186.9 s = 15.1 d.
  - 172.8 / 112.6 = 1.535.
  - These match STUDY:817-824.
- **Resolving-power arithmetic.**
  - Welch factor: t(0.975, ≈ 14) · √(2/8) = 2.145 · 0.5 = 1.07. Then 1.07 · 3.14 = 3.37 pt
    (STUDY:501, "3.4 pt").
  - Paired factor at zero correlation: 0.836 · √2 · 3.14 = 3.71 pt (STUDY:507, "3.7 pt").
  - ±1.0 pt needs sd_diff ≤ 1.0 / 0.836 = 1.196 (STUDY:503, "1.20").
  - k = 6: 1.05 · 3.14 = 3.30 (STUDY:515).
- **Budget arithmetic.**
  - Second wave: 7,000 × 112.6 s = 218.9 h. 4 pods × 218.9 h = 876 pod-hours; 2 pods × 218.9 h
    = 438 pod-hours (STUDY:1000, 1010).
  - W&B versions: 48 × 280 + 8 × 40 = 13,760 (STUDY:965).
  - Cheap version: 16,000 / 336,000 = 1/21 (STUDY:976).
- **Runner semantics** (`code/tree/bnhgq2/ablation.py:612-668`). The per-epoch order is: trace
  on the live model, then `model.save(candidate)`, then reload, then the stored-state check with
  no retrace, then validation `predict` on the reloaded candidate, then
  `feasible = budget_met and nondegenerate` with
  `nondegenerate = above_floor > 0 and val_accuracy > threshold`. `model_best.keras` is updated
  only on `feasible`, and so is the [A19] copy.

## Earlier A and B findings (arbiter v3), by name

| v3 # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 (A) | feasibility satisfiable by a collapsed network; non-degeneracy condition | **Resolved** | STUDY:544-564 (a)-(c), and applied at: budget claim l. 632-640, recipe branches l. 675-680, sd gate l. 525-530 and [D13] l. 1106-1107, pilot l. 881-892. "EBOPs above the 0-bit floor" appears beside every EBOPs number (l. 562-564, 593-594, 606-607, figures l. 763). Implemented: configs `experiment.nondegenerate`; `ablation.py:652-661`. The threshold script is named (l. 555, 1363-1366). |
| 2 (A) | A07-at-350k family floor-bound; move the ladder to E ([D21]) | **Resolved** (and Kai-confirmed) | Arms table l. 227-240; comparisons l. 244-252; [D21] l. 1172-1184; A07-350 expectation pre-registered l. 642-649; Holm set l. 696-699. `index.json` gives E for A, B, D, F, R and A07 for C and A07-350; `packs.json` seed blocks. Expected R branch restated as "none" with a reason (l. 681-684). |
| 3 (B) | paper's ≥ 1-bit rule misstated | **Resolved** | Fidelity row l. 270 "stated, ambiguous" with pdftotext lines and `jsc150/model.py:193`; zero-GPU finding and table l. 332-353, traced (patch 0018); [L2] sentence l. 1433-1434; Kai row l. 1469. |
| 4 (B) | softmax tax beside every distance to 79.4 | **Resolved** | l. 653-656 (49 % / 178,474; A07-350 98 % / 6,947), l. 157-158, [L2] l. 1431-1433. |
| 5 (B) | [D20] not staged; trace protocol and dynamics | **Resolved** | [A21] gate l. 1353-1366; fidelity row l. 283 (live reset changes dynamics); `i_decay_speed` row l. 284 and [D25]; canary trace share l. 813-814, 825-826. Code: patches 0015, 0016, 0023; configs carry `train_full` and `stored`. The STUDY text now understates the staging (C1). |
| 6 (B) | stability wording "never safe" | **Resolved** | l. 690-692. |
| 7 (B) | recipe on feasibility, never "beats" | **Resolved** | l. 675-679, with A1000 and D1000 feasibility beside it. |
| 8 (B) | paired resolving power at zero correlation | **Resolved** | l. 504-509 (3.7 pt; "cannot resolve below about 3-4 pt"), recipe claim l. 673-674. Recomputed above. |
| 9 (B) | REPRO-CHANG xfm-n64 in the architecture FLAG | **Resolved** | FLAG l. 1497-1502 with the full label (single seed 42, test-selected, unverified, open-loop β, HGQ weights) and the caveat that its weights prune. |
| 10 (B) | one-head arm E1, trace before pilot | **Resolved** | Traced (`static_floors_fix6_a07_e_e1.json`, recomputed above); E1-s1 in the pilot, B-s1 out (l. 857-863; `pilot_packs.json` index 57); kept as a Kai row, never primary on pilot accuracy (l. 1468). |
| 11-18 (C) | 175k wording; "to be confirmed"; [A14] softmax item; UPSTREAM sentence; two init samples; stale evidence B; `calib_n`; figures; tag count | **Applied** | l. 305 "350k and 250k"; no "to be confirmed by CPU" remains; [A14] l. 1292-1296 lists no fixed-softmax item; the UPSTREAM stale sentence is gone (only l. 1645 cites the file); samples named at l. 1146-1147 and 1350-1352; the regenerated `static_floors_arms_s1.json` is a PREFLIGHT gate (l. 1263-1266); `calib_n` replaced by the [D20] key (l. 214); figures l. 758-776 name the arms, and include a paired-gap panel, attention state and val − held-out; the tag appears 13 times, all in the change log, tables and [D]/[A] entries. |

My v3 A1 is arbiter #2, and it is resolved. My C1-C6 are arbiter #11-#16, and they are applied.

## Category A (new)

None.

## Category B (new)

**B1. A selected checkpoint that fails certification has no stated outcome, so it can change k
and the budget claim silently.** STUDY:566-572 says a retrace mismatch "is a pipeline defect
reported at VERIFY, never a reason to reselect". Patch 0019 makes `evaluate_roc.py` refuse
uncertified files (`decisions.md` 2026-09-27, ml-engineer entry). The STUDY does not say what
the seed then is:
- it could count as "no accuracy number", like an infeasible or diverged seed (l. 574-583), which
  lowers k and can take the budget claim below 6 of 8;
- it could block VERIFY until the defect is fixed;
- it could be evaluated anyway, labelled.

The pilot certification check (l. 895-897) exercises the mechanism once, at epoch 500. That
check does not cover a mismatch at the terminal epoch, where certification may run on a different
device or trace batch. The outcome changes the arm mean, every paired gap and the budget count.
**Impact:** undefined handling of a pre-registered gate, and it bears on what the budget claim
can say.
**Fix (one sentence, no regeneration):** pre-register the outcome. Recommended: VERIFY is
blocked for that arm until ml-engineer resolves the mismatch without reselecting. If it cannot
be resolved, the seed counts as "no accuracy number" in k, and the mismatch is reported per seed
with both EBOPs values. Also state that certification runs with the same `ebops_trace_batch` as
the per-epoch trace.

**B2. For arm H, the STUDY does not pin the selection metric to the file that is evaluated.**
STUDY:398-401 says H's traced clone "is the candidate that is saved, selected, certified and
evaluated". [A23] (l. 1402-1404) lists "validation accuracy and macro-OvR AUC" before "a clone
traced on the full training split", and does not say which model the validation pass runs on.
In A's runner, validation runs on the reloaded, reset-traced candidate (`ablation.py:620-641`),
so selection metric and evaluated file agree. H keeps its live model's per-batch `i` by design.
If the port computes validation on the live model and saves the reset-traced clone, then the
accuracy that selects the checkpoint and threshold (c) belong to a different model from the one
certified and evaluated. The [D20] evidence shows that a retrace alone moved 2.0 % of logits and
0.6 % of top-1 predictions (STUDY:1146). **Impact:** H's selected checkpoint and its
non-degeneracy test could be decided on numbers that the evaluated artifact does not reproduce,
and this enters H − NB and H − A.
**Fix (one sentence in [A23] and l. 400):** validation accuracy, validation macro AUC and test (c)
for H are computed on the reloaded traced clone. Add a CPU unit test that the logged validation
accuracy equals a fresh-load prediction of the saved clone.

Both B items are text fixes. Neither needs a regenerated config, a new trace or a Kai decision.

## Category C (apply before commit; no re-review needed)

- **C1. Stale "not staged" text for [D20].** Three places still say the staged runner traces 256
  jets or does not implement [D20]: l. 469, l. 1171 and [A21] l. 1353-1355 (which cites
  `ablation.py:450, 515, 521`). The tree now has the implementation:
  - `ebops_trace_sample()` at `ablation.py:438-450` (line 450 is now the `ValueError`);
  - the opt-in at `:546-549`;
  - the stored reload check at `:639`;
  - the configs carry `train_full` and `stored`.

  Reword [A21] as "implemented in patches 0015, 0016 and 0023; the gate re-runs the check under
  [D25]". Also update [D20]'s "PID signal" bullet (l. 1162-1164): `decisions.md` records that
  BetaPID reads the traced EBOPs.
- **C2. [D25] is not staged, and the text reads as if it were.** There is no `i_decay_speed`
  setter in `qat.py`, `config.py` or `generate.py`, and no generated config carries
  `quant.i_decay_speed`. The only hits are the recorder `i_decay_speeds()`
  (`ablation.py:491-497`), `cpu_gate.py` and a test. The fidelity row (l. 284) says "yes" and
  [A21] says the value "is set to 0.001". State that it is a PREFLIGHT gate and not yet code.
  [D25] is also absent from `.claude/memory/decisions.md`, while the ml-engineer's "Finding, not
  changed: 0.01" is there. Log the reversal.
- **C3. [A17] body is stale.** l. 1317-1319 says the evidence "covers the new pair at no seed", but
  `a17_pairing_d21_8seeds.json` shows A, B, D and R paired with F at all 8 seeds. The change log
  (l. 110-113) says so. Align the body and keep the re-run under [D25] as the gate.
- **C4. F floor already traced.** l. 315-316, 550 and 1328 say "F ... traced at PREFLIGHT [A7]".
  `cpu_gate_d21.log` gives F-s1 zero_floor 171,526 with floor_retraced 171,526. Cite it.
- **C5. [A19] definition differs from the code.** STUDY:599-602 takes the highest-AUC (a)
  checkpoint and then requires (b) and (c). The code (`ablation.py:664-668`) takes the highest-AUC
  checkpoint among those meeting (a) to (c). The two differ when the AUC-best (a) checkpoint is
  degenerate. The sensitivity is labelled, not primary. Pick one and state it.
- **C6. Pilot wall time.** l. 878-879 gives "About 15.6 h" from 500 × 112.6 s. The trace factor
  of the same section (× 1.66) gives about 26 h. Give both, or say that the 15.6 h excludes the
  trace.
- **C7. Three A07 init EBOPs under [D19].** They are 13,613,261 (`wrap_trace_check`, exponential
  pT), 13,182,317 (`static_floor.py`, standard normal) and 14,462,317 (`cpu_gate_d21.log`,
  A07-350-s8, gate sample). E is 8,965,267 (standard normal) against 9,429,139 (gate, A-s1). Say
  which value PREFLIGHT records as "init EBOPs" and on which sample.
- **C8. Threshold (c) is weak by design (arbiter-prescribed, not a finding).** With five roughly
  balanced classes, p_maj + 5 SE ≈ 0.20 + 5 · 0.0016 ≈ 0.208. Have the report print the
  threshold's value beside the budget claim and the feasible counts, so that "reaches 350k
  non-degenerately" is not read as "reaches a useful tagger".

## Decision-label traceability

| label | stated | implemented / status |
| --- | --- | --- |
| [D19] | Chang quantizer set, every arm | `quant_set: chang` on all 56 production configs (`index.json`); C′ `current` |
| [D20] | full-split trace, stored reload check, certification | configs `train_full` / `stored`; `ablation.py:438-450, 546-549, 639`; `certify_ebops.py` (0019). STUDY text lags (C1) |
| [D21] | E ladder, A07-350 descriptive, C on A07 | `index.json` arch per arm; `packs.json` |
| [A17] / patch 0011 | RNG flag on no-PE E configs | `pos_enc_none_consume_rng: true` (A, R); 8-seed pairing passes |
| non-degeneracy | (a)-(c) | `experiment.nondegenerate` in configs; `ablation.py:652-661` |
| [D22]-[D24] | NB, H, second wave | no code yet; declared as second wave with [A22]-[A24] gates. Consistent |
| [D25] | `i_decay_speed` 1e-3 | no code yet; declared as a gate (C2) |

No [D] is replaced without a dated amendment.

## Completeness cross-check

- Arms: 7 × 8 = 56 production configs, plus 2 pilot-only (C′, E1) = 58, as in `index.json` and the
  gate log. The arms table (l. 227-240) agrees.
- Second wave: 16 runs declared, 72 in total; no configs yet (code-gated). The count is consistent.
- Claims: budget, recipe, stability and weight-type (second wave), each with a decision rule. H and
  A07-350 are descriptive.
- Figures: per-class ROC, two ladders with paired-gap panels, attention state, val − held-out and
  interim readouts, plus the second-wave set (l. 758-776).

## Competing-group question

A group publishing next month would have two things we lack:
- a Linformer arm matching the paper's best transformer. It is declared and justified:
  `QLinformerAttentionT` is absent from `hgq2==0.1.9`, and a Linformer is a Kai option (l. 1468, 1473).
- a synthesized resource number. [L7] declares none.

Both are stated limitations, not silent gaps. The iso-EBOPs-versus-iso-cost caveat for A − NB is
stated ([L2], l. 167-169). No unjustified item remains.
