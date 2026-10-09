Verdict: PASS. P2 and P3a close v2 A1 (the definition) and the B items in scope. The controller-error metric can be computed from `activation_widths.jsonl` for all 24 arms. Two cheap pre-data text items remain, and neither needs a new bundle: B1, a transient-free controller-error window, and B2, a 3-value gap in the four-class partition.

# STUDY constructive review v3: pilot program, 2026-10-06

Reviewer: constructive-reviewer, panel iteration 3 (06-review §6.2). The scope is P2 and P3a of [A4], per `review/STUDY_arbiter_v2.md` Question 4. Read-only except for this file.

**Inputs**
- `STUDY.md`, sha256 `11005dfb…eac44` ([A4] 06:13 JST).
- `protocol-r1.json`, sha256 `62a50e14…fc9a`.
- `review/STUDY_constructive_v2.md` and `review/STUDY_arbiter_v2.md`.
- From the frozen tree `code/tree/`: `bnhgq2/ablation.py`, and the 24 configs under `campaigns/pilot1005/configs/`.
- `freeze_p.py`, the diag heredoc at :126-190 and the readout at :465-495.

No pilot data exists. Every count below is a code fact or arithmetic on frozen configs. None of them is a result.

## 1. Do the fixes close v2 A1 and the B items?

| v2 item | [A4] text | status |
| --- | --- | --- |
| A1, controller error empty for (c) arms | STUDY.md:210-215. The filter is traced epochs (ratio not None) with `epoch ≥ warmup`, applied the same way to noC and (c) arms. It reports the median and max of `ebops_in_training_over_traced` and of `ebops / target_ebops`. The frozen `controller_error` field is declared not read. The protocol mirror is `protocol-r1.json:700` | **closed as a definition.** The implementation is arbiter Q2 or a VERIFY recompute (§2). See B1 for what the definition still measures |
| A1 addendum, a target-tracking ratio for noC on the same footing | `ebops / target_ebops`, with E-unc-C excluded | **closed** |
| B1, §11 deadline text and A07 margin | STUDY.md:360, :368-371: 20,800 s, a run budget of about 20,080 s, 680 s at 38.8 s and 4,655 s at 30.85 s. A deadline hit is an integrity stop. The protocol mirror is `protocol-r1.json:677` | **closed** |
| B2, a26 on `checkpoints/epoch-0475` | This is in arbiter Q2, the readout re-preparation, but not in the STUDY §5 diag list (STUDY.md:202-209). `grep 0475 STUDY.md` returns nothing | **open in text only** (C1) |
| C1, qkv1 t_uniform is None | STUDY.md:207-209 | **closed** |
| C2, E-unc-C reads `share_of_total` only | STUDY.md:209 | **closed** |

**The P2 rule. I checked it as follows.**
- **Healthy.** `best_feasible_val_acc ≥ 0.50` is in the single definition (STUDY.md:175-181). The same term is in the entropy-only failure (:189-191), so the two stay disjoint. It appears in the production early stop (:327-328) and in protocol `:633`, `:662`, `:692`.
- **W ordering** (STUDY.md:274-277).
  - Accuracy comes after the three counts and before entropy. So when every 350k arm is 0/2 healthy, which is the likely case per STUDY.md:75-77, a low-entropy, low-accuracy qkv1 arm can no longer win W on entropy alone. That was the phys A1 concern.
  - "null = 0" is harmless. A null `best_feasible_val_acc` occurs only without a best-feasible checkpoint, which means `feasible_any` is false: a `nondegenerate_best` without `feasible_any` is an integrity stop (STUDY.md:163-164). So two arms that tie on the `feasible_any` count carry the same number of nulls over their 2 seeds, and the null-as-0 term cannot break such a tie by itself.
- **R3 on seeds 2-4** (STUDY.md:286-287). This matches the Prec qualification (:302-303), so R3 can no longer spend 3 pods on a Prec that cannot qualify.
- **E-unc-C** (STUDY.md:249-254, :342-343; protocol `:625`, `:667`). It is judged without its entropy. An entropy of at least 0.95 at acc ≥ 0.50 routes to stop 2 as "E cut uncalibrated", which comes before stop 3 in the order. Every outcome of E-unc-C therefore leads to exactly one action.

## 2. Is the controller-error metric computable from the frozen bundle's output?

**Yes, for all 24 arms, from `activation_widths.jsonl` alone.** It needs no `pid_telemetry` and no code change.
- **Fields.** Every epoch's record carries `epoch`, `ebops`, `target_ebops` and `ebops_traced` (`ablation.py:1103`, :1135-1139). When `d20` is set it also carries `ebops_in_training_over_traced` (:1118-1120). On an untraced epoch, `ebops` and the ratio are null (:1137-1139). So "ratio not None" and "`ebops` not None" select the same epochs.
- **d20 and regime B.** All 24 configs set `train.ebops_trace_sample`, which makes `d20` true (`:898`), and `ebops_trace_every` 10. So the noC arms log the same fields as the (c) arms. noC lacks only `pid_telemetry`, which the definition does not use.
- **Warmup.** `pid.warmup` is explicit in every config: 1, or 50 and 100 for rows 16-17 and 18-19. The code default of 10 (`ablation.py:574`) therefore never applies. "`epoch ≥ warmup` from the row's config" is well defined.
- **Target.** No pilot config has `experiment.target_schedule`, so `target_ebops`, which is the final target, equals `training_target_ebops` on every epoch (`ablation.py:163-168`).
- **Where the file is.** It is in each run directory, which the diag reads at `freeze_p.py:131`. It is also in every snapshot, because it is in `SELECTED_FILES` (`ablation.py:1248`). Both routes the STUDY names are therefore available: the Q2 re-preparation and the VERIFY recompute.
- **Records per arm.** Under the [A4] filter, over epochs 0-499 with traced epochs 0, 9, 19, …, 499:
  - warmup 1: 50 records (9-499);
  - w50: 45 records (59-499);
  - w100: 40 records (109-499).

  The filter is the same for A350-noC and A350-C, so H1 is compared on identical epochs.

## 3. What cheap items remain that change how R1 is read?

### B1. The pinned window is dominated by the initial squeeze, so "max" and "median" do not measure the controller

**What is wrong.** The window starts at the first traced epoch at or after warmup.
- Every pilot starts near E's initial EBOPs: 9,429,139 on the synthetic sample (STUDY.md:145), against a 350k target.
- For w1 the first record is epoch 9. The max of `ebops / target_ebops` will therefore almost surely be an early-squeeze value, roughly the initial-to-budget ratio. It says nothing about tracking.
- The STUDY's own prior puts the first meeting of (a) at epochs 259-389 for b5 (STUDY.md:141). On that prior, about 26-39 of the 50 w1 records precede t_budget, so the median would mostly measure how fast the squeeze ran.
- H1's mechanism is that the noC controller reads the wrong input and then over-squeezes. The quantities that bear on it are:
  - the **undershoot**, `min(ebops / target_ebops)`;
  - the **settled tracking** after the budget is first reached.

  The window as pinned measures neither of these.

**Fix (text now; code with Q2 or at VERIFY, same cost).** Add to STUDY.md:210-215 and to `protocol-r1.json:700`, pre-data:
- the `min` of `ebops / target_ebops` over the same window;
- the median and max of both ratios over a second window: traced epochs with `epoch ≥ max(warmup, t_budget)`, where t_budget is already a diag field (STUDY.md:203). Report n with each statistic. When t_budget is null, the window is empty and reads "never reached".

Keep the existing whole-window statistics for continuity.
- Cost: about 0.1 ah of text. It adds 3 lines to the Q2 heredoc, which is already scheduled, or to the VERIFY recompute.
- Bundle, GPU handoff, gate: none changed.
- It stays descriptive and never feeds a rule.

Jev `jev_rank_snippets` (audit `jv-d2d2fc7af57a41b0ab854e6fbffb402c`, advisory, disposition "review") scored STUDY.md:210-215 at 2.58 ("directly answers") for a transient-free definition. My reading disagrees: the text has no t_budget window and no min. The code reading above stands, and Jev's score is noted, not adopted.

### B2. The four-class partition has a 3-value gap at 0.2110

**What is wrong.** `nondegenerate_best` means acc > 0.2109624456315518 (STUDY.md:163). "Attentive, low-acc" and "low-acc uniform" are defined on acc in **(0.2110, 0.50)** (STUDY.md:194, :197; `protocol-r1.json:633`). On n = 62,000, the achievable accuracies 13,080/62,000 = 0.210968, 13,081/62,000 = 0.210984 and 13,082/62,000 = 0.211000 are non-degenerate but lie in neither interval. That contradicts "exactly one of four classes" (STUDY.md:199-200).

**Fix.** Replace "(0.2110, 0.50)" with "`nondegenerate_best` and acc < 0.50" at :194, :197 and protocol `:633`. It is 0 cost text and needs no code: `readout_pilot.py` computes no classes (arbiter v2 check).

The odds of hitting the gap are small. The fix is free, and it removes a stop-rule-8 "no rule matches" edge case at the autopilot.

## 4. Grade C

- **C1.** Add "a26 on `checkpoints/epoch-0475` (Δentropy over the last 25 epochs)" to the STUDY §5 diag list (STUDY.md:202-205), so the field Q2 adds is registered pre-data like the others. Text only.
- **C2.** Optionally report the B1 ratios as log10, which is the error the PID integrates (`log: True` in every config; `ablation.py:586-589`). A median of a log-ratio is symmetric for over- and undershoot. Text only, not required.
- **C3.** If `attn_entropy_norm_mean` is null (a26 failed), no class applies. Name this an integrity stop at §10.1, so it is not left to stop 8. Text only.

## Is a code change worth it?

**No.**
- B1 rides on the Q2 readout re-preparation, which is already scheduled, or on the VERIFY recompute.
- B2, C1 and C3 are text only.
- None of them touches the training bundle 98dd2875, the 24 GPU handoffs, the CPU gate or the F6a byte-equal baseline.

The v2 reasoning against a third bundle still holds. Nothing raised here needs one.

## Summary

| item | grade | pods | GPU-h | change | sharpens |
| --- | --- | --- | --- | --- | --- |
| B1 undershoot (min) and window from t_budget | B | 0 | 0 | STUDY/protocol text now; Q2 heredoc or VERIFY | H1 mechanism read |
| B2 class gap at 0.2110 | B | 0 | 0 | text | partition and autopilot edge |
| C1-C3 | C | 0 | 0 | text | registration and reading |
