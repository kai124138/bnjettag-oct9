# STUDY critical review v10: 2026-09-26-training-batch

Critical-reviewer, panel mode, fresh context, 2026-09-28. Iteration 10 (ESCALATE tier). The scope
follows `review/STUDY_arbiter_v9.md` §Verdict, "Scope of v10": a landing check of fixes 1-4, plus
landing checks of the three dated amendments committed since v9. This is not a fresh review of the
whole file. No verdict is given here; the arbiter issues it.

Artifact: `STUDY.md` at HEAD 4e85e9f (2,658 lines; `git status --short STUDY.md` is empty). Diff
`git diff 2e0cac0 HEAD -- STUDY.md`: 400 insertions, 95 deletions, over 5 commits (96b95f2 fixer v9;
9884773 + 11764b4 arm-C readout; cc36f7c 42abed4b corrections; 22e8692 gate-v3 text pass). Code:
`code/tree` compared with `manifests/chang0926-code.tar.gz`, whose sha256 is
42abed4b5d2e3e9197d36a5031754cfde342fc7b0d03f7bb0106ce16c2e258c0. `ablation.py`, `run_pack.py`,
`ebops_calc.py` and `campaigns/chang0926/generate.py` have the same sha256 in the extracted tarball
and in the tree (1c73c27f…, dff2ec81…, 398e2dc1…, d1e0b094…), so every tree line cited below is also
a line of the bundle.

## Validators (verbatim)

`review/STUDY_validators_v10.txt`:

```
Desktop/bnjettag/campaigns/2026-09-26-training-batch/STUDY.md  —  score 0, reads human
  38412 words · 1012 sentences · mean 25 words (σ=23.6) · 16% bullets · 2 em-dashes
Diff since v9 review (2e0cac0):  1 file changed, 400 insertions(+), 95 deletions(-)
```

`prose_lint` scores 0 and flags nothing. STUDY has no figures, so `plot_check` does not apply.
No `.npz` or csynth report exists at STUDY. The recomputations in this review are the s_e, T_run
and denominator arithmetic and the code-line resolutions below.

## Regression trigger named by arbiter v9 ("[D] replaced without a dated amendment")

**Cleared.** Arbiter v9 required the fix-1(a) paragraph to be committed before any regime-B pod
was applied. It was committed in 96b95f2 at 2026-09-27T15:08:51-07:00. RUN.md (8c1cbaf) records
pilotb5 and pilotb3 applied at 2026-09-28T23:05:57Z, which is about 32 h later.

## Arbiter v9 fixes: landing table (line numbers at HEAD 4e85e9f)

| fix | site | landed | evidence |
| --- | --- | --- | --- |
| 1(a) | core paragraph "[D15] branch executed" | yes | l. 1438-1512. Canary numbers match arbiter v9 l. 16-21 (219.65 / 219.37 / 215.16 s; 17.8 / 17.8 / 17.4 d; 163.88 s, 13.3 d; 293.6 s, 23.8 d; trace share 0.42 over 30 samples) |
| 1(a) slot T | traced epochs | yes, cited, correct | `ablation.py:483-489` is `is_traced_epoch`: `k is None or epoch == 0 or (epoch + 1) % k == 0 or epoch + 1 == cfg['train']['epochs']`. `:461-480` is `ebops_trace_every`, and `:477-479` refuses a snapshot cadence that is not a multiple of k. `generate.py:57` has `'ebops_trace_every': 10`. The gate log has `TRACE_EVERY_OK` on 58 configs: `traced_epochs 701` ×50 and `101` ×8 (grep on `code/evidence/cpu_gate_shipped_42abed4b_full.log`). Recomputed: 1 + 7,000/10 = 701 and 1 + 1,000/10 = 101. All of epochs 1, 10, 500, 1,000, 2,000, 4,000 and 7,000 (one-based) are traced |
| 1(a) slot C | candidate cadence | yes, cited, correct | save, reload and validate on every epoch at `:795-805`. Budget and feasibility exist only on traced epochs: `:817-818` (`budget_met = … if traced else None`; `feasible = … if traced else False`). `model_min_ebops`, `model_unconstrained`, `model_best`, the [A19] copy and the recovery freeze, all gated on traced/feasible, are at `:838-858`. Degenerate counter `:829-832`. Checkpoint every 25 epochs at `generate.py:133`, `ablation.py:922-926`. Snapshot every 500 at `generate.py:134`, `:928-931`. `model_best` write at `:847`. `ValidationReloader` at `:589-608`, instantiated at `:764` and called at `:797` |
| 1(a) slot P | PID input and assertions | yes, cited, correct | `model_ebops` at `:492-495`, read at `:783` before the trace. Trace at `:788-789`, `pid.on_epoch_end` at `:860`. The traced-epoch assertion (1e-6 relative) is at `:861-866`, the untraced-epoch equality at `:867-871`. The WRAP reset on traced epochs is `traced_ebops` at `:703-704`, which calls `compute_ebops` → `trace_minmax` (`ebops_calc.py:15-21`) |
| 1(b) | [D20] "On each traced epoch", PID signal, "once per traced epoch", DECISION block, fidelity rows, Selection, confound 10 | yes | l. 2038, 2053-2065, 2068, 2609-2620, 580-581, 899-900, 823-824 |
| 1(c) | s_e, "Illustrative projections" head, "[D15] branch (measured)", [D15], FLAG block, prior labels | yes | l. 1377-1378, 1385-1386, 1405-1406, 2000-2001, 2585-2593. Every 1,750 / 63 / 876 / 438 / 218.9 h plan figure carries "(prior, superseded; …)" (l. 1395-1397, 1836, 1854-1855, 1880-1881) |
| 1(d) | canary traced pair, Reports, Outputs, Phase-1 window, Trace-cost s_e window | yes | l. 1703-1705, 1695-1696, 1759, 1604, 1424-1425 |
| 1(e) | regime-B pilot amendment, Phase 2 duration, resume rule | yes, then amended | Landed verbatim in 96b95f2. cc36f7c then amended it with its own dated change-log entry (regime-A stopped, conditional certification), and 22e8692 did the same (A10, c6017, fingerprint, K=3 OOM fallback). Neither is a landing miss. Amendment at l. 1579-1602. Phase 2 at l. 1606-1607: recomputed 500 × 136.5 s = 68,250 s = 18.96 h ("about 19 h"). Resume at l. 1760-1762 |
| 1(f) | Pods, GPU classes, [D16], Pod count | yes | l. 1514-1517, 1528-1530, 2004-2005, 1535-1536. See C3 for stale remainders |
| 1(g) | Kai rows | yes | l. 2458-2460 |
| 1(h) | K=7 closures, second-wave memory sentence | yes | Overlap alternative, FP32-E launch exception, "Pods, wave 1 at K=7", Kai rows "FP32 E arm" and "NB in wave-1 seed blocks" all carry "(closed by Kai's K=5 packing …)"; memory sentence l. 1874-1877 |
| 1(i) | change log | yes, sha missing | l. 298-352. The entry says "the sha is added at the orchestrator's commit" (l. 305), but no sha was ever added. See C1 |
| 2 | canary sources, "(from the W&B history)" | yes | l. 1709-1723, 1424. It correctly labels `:754-755` / `:783` as 77f1ca4e lines and adds the 42abed4b log fields (`:934-937`, `:941`; checked: `ebops_trace_seconds`, `ebops_trace_over_epoch`, `loss=` on the epoch line) |
| 3 | confound 9, Pods "one GPU class" | yes, verbatim | l. 811-817, l. 1519 |
| 4a | sd_diff ≤ about 0.86 pt | yes | l. 1215. Recomputed 1.0 / 1.16 = 0.862 |
| 4b | packet list "and" | yes | l. 1196-1198 |

The s_e arithmetic in 1(a) holds: 127.45 + 90.61 / 10 = 136.51 s, and 7,000 × 136.51 s = 955,570 s
= 11.06 d. The Symbols window, zero-based epochs 10-29, contains exactly two traced epochs (19 and
29), so it covers two whole cycles as stated.

## Amendments since v9: landing checks

**Arm-C constraint-active readout (9884773, 11764b4).** It landed as dated (l. 1660-1686), and it
carries a source and a "descriptive only" clause. Denominator recomputed: traced zero-based epochs
in 0-499 are e = 0 and e = 9, 19, …, 499, giving 1 + 50 = 51; production gives 701. The last-10
window, one-based 410, 420, …, 500, has ten members. The β bound 1e-10 matches
`chang0926-c-n64-s1.json` `min_beta` 1e-10 (target 5,000,000, `ebops_trace_every` 10). The 5M /
343,053 ratio is 14.58, stated as "about 14.6×". C′'s 5M / 4,580,398 is 1.0916, stated as "9.2 %
above". Correct.

**Corrections after the 42abed4b freeze (cc36f7c).** These landed. Slot T now includes epoch 0,
matching the code at `:489`. The canary pair (traced ends of epochs 1 and 10) is consistent in
slot T (l. 1448-1462) and in the stability bullet (l. 1703-1705). The regime-A stop record at
l. 1589-1591 matches RUN.md l. 480-496: A-s1 and A-s2 at epoch 125, D-s1 at 150, E1-s1 at 75, C′-s1
at 25, no epoch-500 snapshot. The RSS gate text (l. 1736-1740) matches `ablation.py:632-679`: a
polyfit over `rss[5:105]`, projection = intercept + slope × `total_epochs`, and exit
`RSS_GATE_EXIT = 5` (`:611`). `run_pack.py:49` `EXIT_MEMORY_GATE = 5` is not retried (`:224-225`).
The heartbeat per attempt (`run_pack.py:85-90`), `POD_STALL` (`:197-199`) and `POD_MEM` (`:151`)
are cited correctly.

**Gate-v3 text pass (22e8692).** This landed at l. 1583-1588 and l. 1741-1748. The formula at
l. 1744, rss20 + (rss20 − rss10)/10 × 85 > 6,144 MiB, projects to process epoch 20 + 85 = 105, the
RSS gate's verdict epoch. That matches the top decisions.md entry (Kai, 2026-09-28). The
fingerprint gate's integer is left to PREFLIGHT, which gives 11,559,681 (PREFLIGHT l. 797, 820,
827). The CPU run in `code/evidence/fingerprint_cpu_42abed4b.log` exits 8 (`GPU_FINGERPRINT_NO_GPU`)
by design, so the value is the ticket's GPU value, as PREFLIGHT states.

## Findings

### Category A

None.

### Category B

Neither B touches the pilot-b pods already applied (2026-09-28T23:05:57Z). Both bind at the
production launch decision, which follows the pilot's epoch-500 readout.

**B1. The 14-day rule does not say whose s_e decides, and the A07 production pods run at a K that
no canary measures.** Sites: l. 1508-1512 (fix 1(a), in the arbiter's own verbatim text: "The
14-day rule now binds on the regime-B canary: T_run = 7,000 × s_e") and Launch policy l. 1764-1769
("Single-wave T_run"). Impact: this changes what production does.
- The A07-sized arms are the slow ones. C′-s1 (A07) measured 293.6 s at K=6 under regime A, 23.8 d.
- The PREFLIGHT pod map (PREFLIGHT l. 1290-1295; `packs.json`) runs {C, A07-350} at **K=4** in 4
  pods. The regime-B pilot measures A07 only at K=3 (A07-350-s1, C-s1, F-s1) and C′ at K=5.
- RUN.md l. 359 already reads the rule as covering "the A-arms" only.
- As written, E-pod timing at K=5 could clear the rule while the A07 pods launch beyond 14 d, or
  launch on a K=3 figure taken for K=4.
- Rough arithmetic, not a measurement: if the A07 trace share were as large as A's 0.42, regime B
  gives 293.6 × (0.58 + 0.042) ≈ 183 s, and 7,000 × 183 s ≈ 14.8 d, above the rule's bound of
  172.8 s.

Fix (fixer, one sentence after l. 1512): "T_run is evaluated per production pod class as the
largest T_run of its arms: E pods at K=5 from the K=5 pod's s_e; A07 pods at their production K. If
that K is not the K=3 pod's K, the A07 pods launch only after a timing read at that K, or on Kai's
acceptance of the K=3 figure." This is underspecification in the fix-1(a) text, so it belongs to
the fixer. It needs Kai only if the arbiter reads the K=4 A07 packing as a new design choice.

**B2. A regime-B pilot that fails the A rule cannot be attributed, and Kai's option list omits the
regime.** Sites: the A rule at l. 1611-1615 (options: "re-target from the traced [A7] floors, a
one-head or Linformer primary, or stop"), and l. 1592-1602 (regime comparison). Impact: this
changes the claim the pilot report makes to Kai, and therefore what production does.
- Arbiter v9's motivated-reasoning section named the risk: between traces the PID holds the
  **in-training** EBOPs at target (slot P, l. 1483-1490). If traced EBOPs sit above in-training
  EBOPs, traced epochs can be infeasible while the PID reports on-target.
- The ratio is reported: fix 1(a)(3) has "the pilot readout reports their ratio per run", and the
  comparison packet (l. 1599) lists it. No rule reads it, though, and the A rule's option list has
  no regime option.
- Arbiter v9 answered the risk with the A/B comparison at epoch 500. cc36f7c made that comparison
  conditional on resuming the regime-A runs "to epoch 500 on 77f1ca4e". That bundle leaks 80-95 MB
  per epoch per arm (incident report), so in practice the comparison will not happen.
- So no registered rule now separates "slot P's mixed PID input made traced epochs infeasible" from "the
  recipe cannot reach 350k". Also, plan.md R-B1 (l. 891-894) records that no in-training/traced
  ratio has been measured.
- A failed A rule would therefore go to Kai with options (re-target, change architecture, stop)
  that treat the regime as innocent.

Fix: pre-register an attribution line in the A-rule readout: per A seed, `ebops_in_training_over_traced`
at the traced epochs of the last cycle, and the count of traced epochs with in-training EBOPs ≤ 350k
< traced EBOPs. If that count is > 0 on the epochs where (a) fails, the report to Kai adds the
option "PID input under regime B (read traced EBOPs every epoch, a smaller k, or regime A on the
fixed bundle)". The rule stays descriptive and selects nothing. This arises from amendment content
(cc36f7c), so per arbiter v9 it is an ESCALATE item unless the arbiter rules that the fixer may
register a descriptive line.

### Category C

**C1. Two change-log entries cannot be resolved from HEAD.** The v9 entry (l. 305) says "the sha is
added at the orchestrator's commit", and it never was (it should read 96b95f2). The cc36f7c entry
(l. 355, "Line numbers with this entry included") names no sha either. Both sets of line
numbers are now off by the 8+ lines added above them (for example, the cc36f7c entry cites "slot T
(l. 1439-1455)", but l. 1439 at HEAD is the paragraph head). Fix: append "(line numbers at 96b95f2)"
and "(line numbers at cc36f7c)".

**C2. l. 845, A − FP32-E package: "the [D20] per-epoch reset dynamics"** is a fix-1 neighbourhood
site that was missed. Fix: "the [D20] reset dynamics (every 10 epochs, regime B)".

**C3. The Pods paragraph (l. 1514-1527) keeps two stale seed-block sentences under the new
first sentence.** "A lost pod costs one seed of every arm rather than every seed of one arm" is
false for the arm-grouped K=5 map (PREFLIGHT l. 1290-1295: E arms {A, B, D, F} in 7 pods). "R against
A or D crosses GPU type" no longer holds when wave 1 is A10-only. The parenthetical "(the
seed-block layout in this paragraph is the prior plan …)" comes after both sentences. Fix: move
the parenthetical to directly after the first sentence, or delete the two sentences.

**C4. RSS gate indexing (l. 1738-1740).** The text reads "process epochs 5-104 … at the end of
process epoch 105", which mixes zero-based fit indices (`rss[5:105]`) with a one-based verdict
epoch. The count is right, but the mixed indexing reads as an off-by-one. Fix: "zero-based process
epochs 5-104; verdict at the end of the 105th process epoch".

**C5. Code note for ml-engineer, not a STUDY edit.** On an untraced epoch the stdout line prints
`untraced in_training_ebops={cost['total']}`, where `cost['total'] = saved_ebops(model)` (`:791`,
`:933`). That function uses int per layer and the `enable_ebops` filter (`:522-526`). The W&B/jsonl
`ebops_in_training` and the PID assertion use `model_ebops` (float, `hasattr(layer, 'ebops')`,
`:492-495`, `:783`, `:870`). The two values share one name but can differ by per-layer truncation
and by the layer filter. Anyone reading the canary or B2's ratio from the arm log would then read a
different number from W&B. Fix: print `model_ebops` in the stdout field, or name it
`stored_ebops`. The next bundle can carry this; there is no reason to rebuild for it.

## Competing-group question (scoped)

A group running the same regime-B design would have two things we do not. First, a measured
in-training/traced EBOPs ratio before committing the PID input: see B2 and the next check below.
Second, a timing read at every production K: see B1. Neither is justified in STUDY at HEAD.

## Next verification (zero GPU)

Pull `ebops_in_training_over_traced` from W&B for the stopped regime-A runs. That is A-s1 and A-s2
to epoch 125 and D-s1 to 150; the field is logged every epoch under [D20], `ablation.py:891-897`.
Regime A resets every epoch, so this ratio covers one epoch of in-training drift where regime B
allows up to nine. It is a lower bound on the B2 risk, and it costs minutes.
