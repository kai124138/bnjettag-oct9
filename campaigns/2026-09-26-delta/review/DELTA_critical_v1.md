# ATLAS review, critical-reviewer, v1 (solo mode)

2026-09-27. Artifact: `campaigns/2026-09-26-method-atlas/ATLAS.md` (910 lines), `atlas.json`
(103 entries), `atlas_spec.py`, `BRIEF.md`, plus the inputs they name. Reviewed as a
pre-registered queue, not as one experiment. Prose not reviewed.

**VERDICT: ITERATE.** Two Category A findings: the floor tables are stale against the CPU trace
that now exists, and the screen advance rule cannot resolve its own +0.3 pt threshold at any
plausible paired sd. Both can be fixed in `atlas_spec.py` and §5 without redesign. No ESCALATE
trigger: nothing has gone outward or launched, and the trace is not disputed. No
experiment-log warning line.

## What I recomputed

| check | result |
| --- | --- |
| `python3 atlas_spec.py <scratch>` | regenerates `atlas.json` byte-identical (`cmp` clean); 103 entries (50 singles, 53 combos); tier and family counts equal ATLAS.md l. 147-151 |
| arbiter-v2 floors (`review/STUDY_arbiter_v2.md` l. 45-58) | `atlas_spec.py:31-44` asserts A07 (326,656, 989,344), E (163,328, 611,000) and dense+head 400,544 / 251,064. Same formula, same inputs. ✓ |
| other derived floors | hand-checked M001 826,016; M042 592,208 (dense+head 134,480 + 2·65,536 + 326,656); M045 991,392; M040 993,440; M009 81,408 / 347,808; Linformer 39,936 / 506,016. All match the arbiter formula ✓ (but see A1: the formula is now known to be short) |
| FF1 cells | the 15 `atlas.json` cells equal the full set of E = −ABCD with ≥ 1 high factor (2-high ×10, 4-high ×5); the all-low cell is the C replica. Resolution V ✓. 1 + 3 + 5 + 10 = 19 parameters, 64 − 19 = 45 residual df ✓ |
| FF2 cells | the 7 cells equal D = ABC (6 two-high + ABCD). I = ABCD, resolution IV, aliases AB=CD, AC=BD, AD=BC ✓. 11 parameters, 21 df ✓ |
| single-knob factors | each factor maps to one method (M019 sets `quant.ste` and its period, M040 sets `n_feat` and `derived_features`; each is one method) ✓ |
| run-epochs | W2 162,000 (296 runs; 280 at H 500 incl. 8 replicas, 8 at 1,000, 4 at 1,500, 4 at 2,000); W3 170,000 (280 runs); teachers 4,000; **336,000** = 48 × 7,000 ✓ |
| pod-hours | 336,000 × 112.6 / 3,600 / 6 = **1,751.6** ✓; W2 844.5, W3 886.2, teachers 20.9 ✓ |
| confirm | 12 × 8 × 7,000 = **672,000** run-epochs; × 112.6 / 3,600 / 6 = **3,503.1** pod-hours ✓; 96 runs over 12 slots at P = 2 is 8 waves × 9.12 d = 73.0 d; over 60 slots at P = 10 it is 2 waves, 18.2 d ✓ |
| screen wall | P = 2: 16,500 + 15,000 + 2,000 = 33,500 · s_e = 43.7 d; P = 10: 7,000 + 4,500 + 2,000 = 13,500 · s_e = 17.6 d ✓ (upper estimate, as stated) |
| s_e basis | `constituent-screen/live-status.json:206` 100.0906 s for `const0922-a07-n64-s1-fast50-fp32` (l. 197); × 558,000 / 496,000 = 112.60 s ✓. ATLAS.md:591-595 labels it batch 256, unverified, K unknown, batch 2,790 unmeasured, matching the anchor STUDY l. 436-439 ✓ |
| pT-weighting number (§9) | `campaigns/2026-09-25-pt-weighting/VERIFY.md:281` held-out macro AUC −0.0108 [−0.0124, −0.0093], 8/8 ✓ |
| traced floors (new input) | `campaigns/2026-09-26-training-batch/code/evidence/static_floors_arms_s1.json`: A07 0-bit 343,053 (softmax only), 1-bit-alive 1,005,741, headroom 6,947; E 171,526 / 619,198; F equals A07. Per layer at 1 bit: input_proj 6,144, head 1,024 + 160. Status: CPU trace on synthetic input (n = 256, seed 0), staged, not committed. A design input, not a result |
| power of the §5.3 rule | Monte Carlo, `uv run --with numpy,scipy`; see A2 |

## Category A

**A1. The floor tables and h values are stale against the trace, and three statements flip.**
`ATLAS.md:48-72, 372-404, 474, 801-802`; `atlas_spec.py:17-20`; every `floor_derived` in `atlas.json`.
The arbiter formula omits the SAT exp-input sign bit (H·T·S per block) and a LUT term (13
EBOPs at A07). The trace adds exactly H·T·S + LUT: A07 343,053 = 326,656 + 16,384 + 13, and
E 171,526 = 163,328 + 8,192 + 6. R3 was pre-registered for this case, so R3 is now the branch
that holds and DR-18 is answered. The atlas still quotes 23,344 EBOPs of headroom and h = 0.035,
and `atlas.json`, which the per-wave STUDYs copy, carries the old values. Re-derived with the
exp term:
- A07 at 350k: headroom 6,947 and h = 6,947 / 662,688 = **0.010**, not 0.035. d16 (M042)
  h 0.088 → 0.026; FFN 64 (M043) 0.029 → 0.009; M040 and M045 0.010.
- **M009, N = 32: the 1-bit-alive floor becomes 347,808 + 4·32·32 = 351,904, which is above
  350k.** The sentence at l. 403-404 ("the only single whose derived 1-bit-alive floor fits
  under 350k"), the §3.2 class "every channel alive at 1 bit" (l. 385) and M009's prediction
  (l. 178) are now false. M058 (N = 32, 2 heads) still fits, at 309,152.
- **M055 (Q/K floor + 2 heads): h 0.105 → 0.089.** It crosses into the near-floor class, so
  R2 now applies to it.
- The E base (FF2): h 0.417 → 178,474 / 447,672 = **0.399**. M001 0.282 → 0.269; M003 0.381 →
  0.356. M007 and M044 stay infeasible.
- **Baselines M047-M050:** floor1 is computed with 1-bit weights (`dense_1bit`), but EBOPs are
  b_w × b_a. With int8 weights (M048) the dense and head part is about 8 × 400,544, so floor1 is
  about 3.8M, not 989,344. M050 adds 7 × 6,144. M047 depends on Z06, and M049 on learned weight
  widths. Their floor and h columns are wrong, not only unverified.

**Answer to the orchestrator's question: does any 350k A07 cell survive?** Under R1, all of
them survive, because 343,053 < 350,000. None of them survives as a method comparison. A
feasible A07 checkpoint has 6,947 EBOPs outside the softmax tables. `input_proj` alone at
1 bit on every channel costs 6,144, and the head costs 1,184, so 7,328 > 6,947: no feasible A07
model keeps even its first layer and head fully alive. Wq, Wk and Wv cost 65,536 each at
1 bit, so attention is necessarily dead. Every A07 350k cell (M008, M011-M016, M038-M040,
M042, M043, M045, the baselines, and M075-M078 at 350k) would compare how a method trains a
remnant of under 7k EBOPs with the softmax tables still billed at 343k.
**Fix (in `atlas_spec.py`, not by hand in ATLAS.md, since the tables render from the JSON):**
(a) add H·T·S to `softmax_floor` (H·T·k for Linformer) and the LUT term behind a flag; add
`floor_traced` beside `floor_derived` for A07, E and F from the evidence JSON. Relabel the
columns "derived (arbiter formula + traced exp-input term)". Re-run and re-render §0, §3.2, §4,
§11 and the M009 and M055 rows. (b) Compute baseline floor1 with the weight-bit multiplier, or
mark it n/a until Z01/Z06. (c) Re-state R2 against the traced h: pre-register that A07-
architecture 350k cells are **not accuracy screens**. Either they default to fallback E (h
0.399), or they are reported only as feasibility counts. Kai may override at K1. The atlas must
state which default applies.

**A2. The screen cannot resolve its own threshold, and the power check comes after the wave it
should gate.** `ATLAS.md:494-505, 541-548, 364, 807-810`.
The rule is BH q = 0.10 within the wave × target (m = 47 in W2 at 5M, 24 at 350k), mean Δ ≥
+0.3 pt, and ≥ 3 of 4 seeds positive. The numbers (scipy):
- The first BH discovery among 47 needs one-sided p ≤ 0.10/47, which is **t ≥ 7.88 at df 3**.
  The 80 %-power MDE at n = 4 is 4.97·sd_d at that α (1.25·sd_d unadjusted). So 0.3 pt is
  resolvable only if sd_d ≤ 0.06 pt, or ≤ 0.24 pt unadjusted.
- Monte Carlo of the whole rule (m = 47, 5 true effects, 1,500 reps): P(advance | Δ = 0.3 pt) =
  0.44 at sd_d 0.1, **0.12 at 0.2, 0.05 at 0.3, 0.017 at 0.5, 0.008 at 1.0**. At Δ = 1.0 pt it is
  0.36 at sd_d 0.5 and 0.05 at sd_d 1.0. The false-advance rate stays ≤ 0.013, so the rule is
  conservative, not liberal. Its failure mode is an expensive empty screen.
- The plausible sd_d: the only same-N binary sd is 3.14 pt (archived R14 N=64 W1A8, 3 seeds,
  held-out; `training-batch/review/STUDY_arbiter_v1.md` #3). sd_d = 3.14·√(2(1−ρ)) is 4.44 /
  3.14 / 1.40 / 0.44 pt at ρ = 0 / 0.5 / 0.9 / 0.99. ATLAS l. 138-139 itself says same-seed pairs
  are never bit-identical (different GPU class and sha), so ρ near 0 is the planning case.
- **(iii) is decorative.** Alone it is a sign test with P(≥ 3 of 4 | H0) = 5/16 = 0.3125, and
  under (i) it is implied almost always. **(ii) caps power at the threshold at ≤ 0.5 by
  construction.** The 0.3 pt rationale (2 × 0.16 pt binomial SE, l. 545-548) sizes the
  threshold against measurement noise on 62,000 jets, not against seed variance.
- The only consequence (l. 503-505, sd_null > 0.19 pt → Kai) is evaluated **before wave 3**,
  after W2's 162,000 run-epochs (844.5 pod-hours) are spent. sd_null comes from 4 replica pairs,
  whose 95 % CI on an sd spans ×0.57 to ×3.73, so it cannot establish sd ≤ 0.19. Z14 (l. 364)
  measures the anchor's epoch-500 sd but has no consequence attached. The cheap version (3 seeds,
  l. 607-613) is weaker still. The factorials do better (effect SE σ/4, about 0.79 pt at σ =
  3.14, 32 vs 32 runs) but still do not reach 0.3 pt.
- Nothing says what happens when zero entries advance. The K3 ranked list by lower 80 % bound
  (l. 560-561) is then the real selection mechanism, and it is not pre-registered as one.
**Minimal pre-registered fix** (§5.1, §5.3, Z14, K2):
1. Give Z14 a consequence at K2, before any W2 pod. Set sd_plan = √2 · sd(epoch-500 validation
   accuracy of arms A and C, the anchor's seeds 1-8, feasible seeds only). This is the ρ = 0
   bound, conservative for cross-sha pairs.
2. n_screen = the smallest n in {4, 6, 8} with MDE_80(n, α_eff) ≤ 0.3 pt. Pre-register α_eff:
   either BH at q = 0.10 with the wave's actual m, or a smaller family (for example BH within a
   code tier or within a family letter).
3. If no n ≤ 8 qualifies, declare before launch the resolvable threshold δ_res = MDE_80(8), and
   raise (ii) to it. Otherwise cut m, or run the screen as a declared ranking (top-k by lower
   80 % bound) with no significance claim.
4. Make (iii) descriptive (report the exact one-sided sign p), or require n of n positive.
5. Run the drift replicas in the first pods of W2 and read sd_null before the other W2 entries
   start.
6. State the zero-advance outcome.
The same rule then carries over to §10's "falsified at confirm" and to the cheap version.

## Category B

**B1. Entries whose control is undefined under the anchor branches.** `ATLAS.md:413-438,
509-519, 490`.
(a) **Fallback C at 5M:** the floor-family 350k cells "run unpaired... feasibility counts
only". G2's rescue needs k_e − k_base ≥ 2 and k_base does not exist, so no advance rule applies.
M013 and M014 are 350k-only and would be dropped silently. State both outcomes.
(b) **A kept by the pilot, but production A seeds 1-4 infeasible at epoch H:** n_p < 3 for every
A07 350k cell, and no re-pairing rule applies. FF2 has one for E (fewer than 3 of seeds 1-4
feasible, l. 278); A has none. The pilot rule (≥ 1 of 2 seeds feasible, median ≤ 3 × target =
1,050,000) would pass even an unpruned 1-bit-alive A07 (1,005,741). Add the FF2-style rule for
A.
(c) **Drift trigger for the long-horizon entries** (M015, M031, M032, M068-M073): the replicas
run only to 500 epochs, so if l. 511-512 switches the primary pairing to the replica, these
entries have no replica control at H = 1,000-2,000. Budget replicas at those horizons, or keep
the anchor snapshot as their control and say so.
(d) **Fallback E in W2:** `atlas_spec.py:419` budgets W2 replicas for A and C only. Under
fallback E the 350k cells pair to E, which has no W2 replica.
(e) **R4 (C′ branch):** "all screens run at 5M against C′" (l. 436). C′ exists only as pilot
seed 1 (anchor STUDY l. 476-480), so no C′ seeds 1-4 [A6] snapshot exists. Require production
C′ seeds 1-4, or an in-wave C′ replica as the primary control.
(f) M010 (1.4M) has no same-target control. Say that G3 does not apply and it is a ladder point
only.

**B2. Retries of recorded failures without stating why they differ, or not caught by G1.**
`ATLAS.md:197-198, 196, 183, 530-536, 514`; `inventory/tried-already.md:147, 128, 90-91`.
- M028 and M029 (1e-3, 3e-4) are both ≥ 2e-4, the H1 collapse range. Neither says what differs
  from H1 (batch 2,790, bounded STE, Adam defaults, restarts). The mechanism note is written
  about the anchor's 3e-3 instead.
- G1's collapse test (≤ 0.25 for 10 epochs after epoch 20) does not catch H1's signature
  ("peaks at epoch 2-3 and then degrades"). The early-peak flag is descriptive only, so an anchor
  base in H1 mode at 3e-3 still counts as a valid control under §5.2's base-stability rule.
  Make the early-peak flag count toward base stability, or define H1-type degradation
  quantitatively.
- M027 (warm start from the unconstrained FP teacher), and M061, M062 and M064, retry the
  "early unconstrained peak, then PID squeeze" pattern (F1, C3, C4; lesson 2 at l. 629-632).
  They do not cite it or say why this time differs.
- M014 at H = 500 runs only the first linear β segment (the note at `atlas_spec.py`, M014: β
  goes from 2e-8 to about 9e-8 by epoch 500, against a 7,000-epoch schedule). The treatment is
  unmeasured, the same G0 class as M015 and M031. Its prediction ("fewer seeds feasible") is
  near-tautological at that horizon. Lengthen H, or park it for the screen.

**B3. M040 gets free inputs at iso-EBOPs.** `ATLAS.md:209`; card P05 hazards.
log pT and ΔR = √(η² + φ²) are computed in `prepare_cache`, outside the model, so HGQ2 never
bills them. The iso-EBOPs comparison is favourable by construction, and on-chip the squares or
tables are uncosted, which is a DSP risk. Mark M040 and its packages (M067, M080, FF1 factor B)
"not a hardware candidate until the derived-feature path is costed". State in the prediction
that the EBOPs match excludes the feature computation.

**B4. The 350k A07 near-floor default is unpriced in §11.** `ATLAS.md:829-832`.
The flagged decision still reasons from h 0.035. With the trace, "run them regardless" means
spending 350k A07 cells on remnants of under 7k EBOPs (A1). Re-state it with the traced h and
recommend fallback E as the default.

## Category C

- C1. `ATLAS.md:183` M014 "about 14 AUC points below its own peak" lacks its split (validation
  per `tried-already.md:89`, 0.75509 vs 0.89775). l. 212 M043 "FFN 32 beat 64" lacks the metric.
- C2. FF2 factor B (M012, f0 = 7) may be close to a no-op against the anchor's "8-bit init, i + f
  = 7" (`decisions.md` chang0926 entry; anchor STUDY l. 174). DR-09 must close before FF2 is
  written, or FF2 may spend a factor on nothing.
- C3. FF1's factor C depends on P-T1. If the teacher job fails, the fraction loses a factor. Say
  whether FF1 then runs as a 2^(4−1) on A, B, D and E, or waits.
- C4. Augmenting FF1 with the five one-high singles from W2 (l. 262-263) mixes waves. Add a
  wave-block term if they are pooled.
- C5. §0 l. 72 still describes the SAT exp input as "pessimistic". It is now the traced case.
- C6. M038 changes the token population. Label it "crosses input set (gate), by design" like
  M040, per §10.
- C7. The M024 and M025 per-channel pow2 gains keep ±1 weights with a post-accumulator shift,
  which is binary-compatible. Keep the "DSP audit before any thesis claim" label, and do not
  describe these as binary-only in outward text until the audit is done.

## The competing-group question

A group running this queue next month would have measured its noise floor before spending
the screen: a replica-seed paired sd at the screen horizon, and a seed count sized from it.
This atlas defers that to after wave 2 (A2). It would also have priced the A07-at-350k cells
from the traced floor rather than arithmetic (A1). Both are fixable here, and neither is
justified as written.

## Decision-label traceability

The atlas relies on the anchor's [D19], [D11], [D13], [A6], [A17] and [A20]. [A6] boundary
snapshots exist every 500 epochs (anchor l. 707), so the 1,000, 1,500 and 2,000 controls are
defined. Using the epoch-500 snapshot as a cross-campaign control does not select within the
anchor, so it does not break [D13]. No broken [D] found.

## What the fixer must change

1. `atlas_spec.py`: add the exp-input term and `floor_traced`, and fix the baseline floor1.
   Re-render. Correct the M009, M055, §0, §3.2, §4 and §11 text. Re-state R2 with the traced h
   and a pre-registered default for the A07 350k cells (A1, B4).
2. §5.1, §5.3, Z14 and K2: add the sd-conditional seed count, α_eff, the δ_res fallback,
   (iii) made descriptive, replicas first, and the zero-advance outcome (A2).
3. §3.3 and §5.2: close the control gaps (a)-(f) (B1).
4. M027-M029, M061/M062/M064 and M014: add the "why different" text; make G1 and base stability
   catch H1-type degradation; fix M014's horizon (B2).
5. M040 and its packages: add the hardware and iso-EBOPs label (B3).
