# ATLAS review, critical-reviewer, v2 (solo mode, re-review)

2026-09-27. Artifact: `campaigns/2026-09-26-method-atlas/ATLAS.md` (1,153 lines), `atlas.json`
(sha256 e736d1b2…8780, checked), `atlas_spec.py`, `screen_power.py` and `BRIEF.md`. Inputs:
`review/ATLAS_critical_v1.md` and `review/ATLAS_fixer_v1.md` (including Follow-up 1). I also
checked the generator output, `code/configs/index.json`, with `code/anchor_arms.json` and
`code/gen_atlas.py`. Reviewed as a pre-registered queue, not as a STUDY.

**VERDICT: ITERATE.** One Category A. The drift-replica plan that closed v1 B1(c)/(d) exists only
in ATLAS.md §5.2 prose and in `atlas_spec.py` `REP`. `atlas.json` does not carry it. The
generator was re-run from e736d1b2 and built the pre-fix replica plan. Every other v1 A and B
finding is resolved or reduced to a B. No ESCALATE trigger: nothing is launched and nothing has
gone outward. No experiment-log warning line.

## What I recomputed

| check | result |
| --- | --- |
| `python3 atlas_spec.py <scratch>` | `cmp` with `atlas.json`: identical. 103 entries; tier, family and code-tier counts equal ATLAS.md l. 189-194 |
| floor formula (atlas_spec.py:21-55) | A07: 262,144 + 64,512 + 16,384 + 13 = 343,053; 1-bit-alive 343,053 + 400,544 + 262,144 = 1,005,741. E: 131,072 + 32,256 + 8,192 + 6 = 171,526; 1-bit-alive 619,198. Both equal `decisions.md:26-27` (chang0926 code). Asserts hold with the terms off (arbiter 326,656 / 989,344; 163,328 / 611,000) and on (trace) ✓ |
| other derived floors | by hand: M009 85,517 + 200,864 + 65,536 = 351,917; M058 42,758 + 200,864 + 65,536 = 309,158; M055 171,526 + 131,072 = 302,598, h 0.089; M007 474,125; M044 2 × 343,053 = 686,106; M003 (tb 2) 114,189 ✓ |
| A07 headroom | (350,000 − 343,053) / (1,005,741 − 343,053) = 6,947 / 662,688 = 0.0105 ✓ |
| 350k roles (atlas.json) | 18 near-floor → E, 16 floor-family (own architecture), 7 E-base (FF2). The lists at ATLAS.md l. 489-505 match `screen_role_350k` entry by entry. The on-E h range for the near-floor cells is 0.327-0.672, against "0.33-0.67" at l. 496 ✓ |
| run counts from atlas.json | W2 entry runs 284 = 268 @500 + 8 @1,000 + 4 @1,500 + 4 @2,000, which is 156,000; with the replicas (A 500, E 1,000, C 2,000) × 4 seeds the total is 170,000. W3 256 = 236 @500 + 20 @2,000, 158,000 + 12,000 = 170,000 ✓ |
| budget | 344,000 / 514,000 / 684,000 run-epochs ✓. × 112.6 / 3,600 / 6 = 1,793.3 / 2,679.5 / 3,565.7 pod-hours ✓. W2 886.2, teachers 20.9 ✓. Confirm 672,000 → 3,503.1 ✓ |
| wall table (l. 797-801) | by hand from ⌈runs_H / (P·K)⌉ · H: n = 4 gives 32,500 / 13,500; n = 6 gives 46,000 / 15,500; n = 8 gives 61,000 / 18,000 s_e. Days 42.4 / 17.6, 59.9 / 20.2, 79.5 / 23.5 ✓ |
| cheap version | 38 entries, 3 × Σ H + 2 × 3 × 500 = 69,000 ✓; 359.7 pod-hours ✓ |
| §11 "+56,000" | 23 W2 5M-only training levers, 4 × (21 × 500 + 1,500 + 2,000) = 56,000 ✓ |
| `screen_power.py` | runs; k values reproduced by Monte Carlo (200,000 reps): k(8, 0.1/44) = 1.84 → power 0.803; k(4, 0.1/44) = 4.86 → 0.800; k(4, 0.1/11) = 3.03 → 0.799 ✓ |
| §5.1 item 4 | 0.163 / √2 = 0.115 ✓; 1.84 × √2 × 0.6 = 1.56 ✓ |
| generator vs atlas.json | `index.json` records `atlas_sha256` e736d1b2 ✓. 540 entry runs equal the 540 (id, target, seed) cells of atlas.json, with no missing, extra or duplicate cells. Horizons 540/540. Base arm matches `screen_role_350k` at every 350k cell, and C at every 5M cell. 8 refused: M020 and M071, the Bop nulls ✓. **Replicas: see A1-v2** |
| three configs | see A1-v2 context below; delta, target, seed and horizon correct in all three |

Config spot-checks. Each was diffed against the replica of its own base at the same seed:
- `W2/M001-t5000000-s2.json` (ready_on_base, C): the only non-label diff is `arch.n_heads` 2 vs 4. It has `target_ebops` 5,000,000, `experiment.seed` 2 and `train.epochs` 500 ✓.
- `W2/M011-t350000-s3.json` (needs_patches, E): the only diff is `quant.act_granularity` `element` vs `channel`. The base is d24 / h2 / no PE, with target 350,000, seed 3 and 500 epochs ✓.
- `W2/M042-t350000-s1.json` (E-based 350k, ready_on_base): `arch.d_model` 16 on E (h2, no PE), with target 350,000, seed 1 and 500 epochs ✓.
- `W2/M015-t350000-s2.json`: E base with 1,000 epochs and `recovery_after_epochs` 500 ✓.

## Re-review of v1 findings

**A1 (floors stale vs trace): RESOLVED.**
- The formula reproduces the trace exactly (above).
- The LUT term is labelled a fit to two traced points in three places: `atlas_spec.py:9`, ATLAS.md l. 82-83, and `floor_derived.label`. It is bounded at ≤ 13 per block and "moves no class boundary". That holds: the nearest margins are M009 at 1,917 EBOPs over 350k and M055 at h 0.089 against 0.10, where 13 EBOPs shifts h by < 1e-4.
- M009, M055, the baselines, §0, §3.2, §4 and §11 are all corrected.
- The grep for old values finds them only in the dated history in `plan.md` and in the arbiter-history sentence at BRIEF.md l. 35.
- One labelling nit remains (C1).

**A2 (screen cannot resolve +0.3 pt): RESOLVED IN PART; the residual is carried as B1-v2.**
- K2 rule, §5.1 l. 609-651: sd_plan is √2 · epoch-500 sd of C or E over seeds 1-8, and max with sd_null once the replicas are read. n is chosen from {4, 6, 8}. α_eff = q/m. The ranking fallback at n = 4 and the δ_res option are declared.
- The zero-advance outcome is at l. 747-752. Replicas run first (l. 669-673). Gate (iii) is now descriptive, and Z14 has a consequence (l. 414).
- Two points remain. The joint power of gates (i) + (ii) (B1-v2). The m count in `screen_power.py` (B2-v2).

**B1 (controls under anchor branches):**
- (a) Fallback C: RESOLVED, l. 522-528, with k_base defined and M013 kept.
- (b) Production A short: RESOLVED, l. 529-533.
- (c) and (d), long-horizon replicas and the W2 E replica: **resolved in prose and in `atlas_spec.py` only, not in atlas.json or the generated configs → A1-v2.**
- (e) R4: RESOLVED, l. 541-545, with the C′ in-wave replica as primary.
- (f) M010: RESOLVED, l. 547-548 and the atlas.json note.
- Residual gaps: see B4-v2.

**B2 (retries, H1, M014): RESOLVED.** M028 and M029 carry a "why different" note. G1 has the H1-type test, with the EBOPs-ratio condition separating it from the lesson-2 squeeze (l. 703-721). M014 is confirm-only (`targets` []).

**B3 (M040 free inputs): RESOLVED.** Ten IDs carry the NOHW note, as the fixer lists.

**B4 (§11 near-floor unpriced): RESOLVED.** §11 l. 1066-1073 uses h 0.010 and 7,328 > 6,947.

**Brief item (2), consistency of the E default:**
- §0 l. 97-107, §3.3 R2, §4 l. 575-589, §5.1 control row l. 605, §7 K1 and §11 all say the same thing: A07 350k cells are feasibility probes, and 350k accuracy cells default to E.
- `base["350000"]` agrees for all 41 cells.
- One exception: B3-v2.

## Category A

**A1-v2. The drift-replica plan is not in `atlas.json`. The generated configs build the pre-fix plan, so the W2 350k default base has no in-wave replica.**

Where: `atlas_spec.py:579` (`REP` is used only for the budget); ATLAS.md §5.2 l. 655-662;
`code/anchor_arms.json` `replicas_by_wave` (W2 ["A", "C"], W3 ["A", "C", "E"], "500 epochs");
`code/gen_atlas.py:351-364`; `code/configs/index.json`.

What was generated, by (wave, arm, target, horizon) × 4 seeds:
- W2: REP-A 350k @500 and REP-C 5M @500.
- W3: REP-A, REP-C and REP-E, all @500.

What §5.2 pre-registers:
- W2: A @500, **C @2,000** and **E @1,000**.
- W3: A and E @500, **C @2,000**.

Totals: the index has W2 292 and W3 268 runs (562 with the 2 teachers). ATLAS.md l. 784-788 gives
W2 296 and W3 268.

The index records `atlas_sha256` e736d1b2, so it was generated after the fix. That contradicts
the fixer's F4 explanation ("the generator run predates that text"). The generator read a stale
`anchor_arms.json`, because atlas.json gives it nothing to read.

Impact:
1. The 60 W2 350k runs on the E base (44 single, 16 baseline) have no in-wave E replica.
   - sd_null for the 350k family cannot be read in W2.
   - The §5.2 "replicas first" gate, and the §5.1 max(sd_plan, sd_null) step for that family,
     cannot run as generated.
   - The drift trigger cannot switch these cells to a replica.
2. M015 @1,000, M031 @1,500, M032 @2,000 and the W3 2,000-epoch cells (M068, M069, M071-M073) have
   no replica beyond epoch 500. This reopens v1 B1(c) in the artifact that builds the runs.
3. The per-wave STUDY "copies its arms from atlas.json" (l. 17-18). It would inherit the same gap.

Fix:
1. `atlas_spec.py` emits `drift_replicas = {"W2": {"A": 500, "E": 1000, "C": 2000}, "W3": {"A": 500,
   "E": 500, "C": 2000}}` into atlas.json from `REP`, with the arm-to-target map and the R4 rule
   "C → C′ as primary".
2. `gen_atlas.py` reads that key instead of `anchor_arms.json`, and `replicas_by_wave` is deleted
   so it cannot drift again.
3. Regenerate.
4. Check: REP-* runs by (wave, arm, horizon) equal §5.2. The runs total W2 296 + W3 268 + 2 = 566,
   with 558 written and 8 refused.
5. atlas.json's sha changes, so every document that pins e736d1b2 (this brief, the fixer note)
   is superseded.

## Category B

**B1-v2 (carried from v1 A2). The K2 rule sizes n for gate (i) alone, but a cell advances on
(i) and (ii) together.** ATLAS.md l. 609-613, 636, 734-736.
When k(n, α_eff) · sd_plan = 0.3 pt and the true Δ is 0.3 pt, gate (ii) ("mean Δ ≥ δ") passes
only about half the time. Monte Carlo (200,000 reps) gives joint power:
- 0.475 at n = 8 (W2 5M);
- 0.432 at n = 4 (W2 5M);
- 0.446 at n = 4 (W3 350k).

So "resolves +0.3 pt" means about 45 % power at 0.3 pt, not 80 %. The v1 text raised this ("(ii)
caps power at the threshold at ≤ 0.5"), and the fix did not address it. Fix, one of:
- state the joint power;
- size n so that k · sd_plan ≤ δ − z_0.8 · sd_plan/√n, which puts the 80 % point of the joint rule
  at δ;
- make (ii) a floor below δ (for example δ/2), keeping δ as the MDE target.

**B2-v2. `screen_power.py` does not count m as §5.1 says it does.** `screen_power.py:39`; ATLAS.md
l. 614-616, 621.
The filter tests an entry-level note substring ("feasibility probe"), not the cell. The notes of
M047, M048 and M049 describe their 350k cells, so their **5M** cells are also dropped from the
W2 5M family. M050, the fourth baseline, stays in. So "W2 at 5M (singles, baselines), m = 44"
matches neither reading: all four baselines in gives 47, none gives 43.
Impact on k is small: k(4) = 4.86 at m 44, about 4.97 at m 47. It changes neither n nor the
likely ranking-mode outcome. Fix: count per (entry, target) cell from `screen_role_350k` and
`base`, and state whether baselines take a G3 test. §5.3 treats them as comparands, so the
consistent choice is m = 43 at W2 5M, with the baselines reported without an advance decision.

**B3-v2. `screen_role_350k` contradicts the notes and §3.3 for M047, M048 and M049.** atlas.json.
All 18 near-floor cells carry the same role string, "the delta is applied to arm E's config and
paired with arm E (**accuracy screen, G0-G3**)". For these three, the note and ATLAS.md l. 497-499
say "feasibility probe on E, no accuracy reading". Any generator or wave STUDY that reads the role
field would give them a G3 test. Fix: add a fourth role, "near-floor on A07 and on E: feasibility
probe on E", and assign it to these three.

**B4-v2. Control gaps that remain under fallbacks.** ATLAS.md l. 517-521, 537-546; atlas.json M013.
- **Arm E fails at 350k:** l. 517-521 covers only "the E-default cells". The floor-family cells
  (16) read accuracy "against arm E by Welch" (l. 508), so their accuracy reading then has no
  comparator. State that they fall back to G2 feasibility only, or name another comparator.
- **R4 (C′):** every 350k cell becomes `STATIC_INFEASIBLE`. The text does not say what happens to:
  - M013, which is 350k only;
  - FF2, whose E-failure rule re-bases to arm C, but under R4 C is C′.
  l. 122-123 promises that "§3.3 says which entries survive", and it does not.
- **M013 field:** atlas.json has `if_floor_fails` "5M-only" with `targets` [350000]. It has no 5M
  cell to keep. Set it to "feasibility probe on A07 (§3.3)" or "drop under R4".

**B5-v2. n may differ by wave × target, but the packages need their components on the same
seeds.** ATLAS.md l. 636-637, 756-758, and the FF1 augmentation at l. 309-311.
The rule picks n per family. If W3 5M runs n = 6 and W2 5M ran n = 4, the package and component
comparisons ("on the same seeds", ⌈3n/4⌉) and the FF1 one-high augmentation have no singles at
seeds 5-6. Fix: bind n_W3 ≤ n_W2 for families that share a ladder, or pre-register that the
singles a package needs are extended to seeds 1-n_W3 (and budget that).

## Category C

- **C1.** The §3.2 heading (l. 417) still reads "arbiter formula". The LUT fit is applied where
  nothing was traced: at H = 1 (M002, 3 EBOPs) and at 2-bit tables (M003, M051-M054, M060), where
  the true LUT term would be smaller. "Never above 13" is per block (M044 at L = 2 carries 26).
  The impact is bounded, but say "per block" and "fit assumes 4-bit tables".
- **C2.** `screen_power.py:63-64` hard-codes FF1 at 64 runs and FF2 at 32, which is n = 4. Since n
  is now variable, parameterize by n. §5.3 l. 762 correctly says "at 4 seeds".
- **C3.** The G2 rescue thresholds (k_e ≥ 3, k_e − k_base ≥ 2) do not scale with n, while every
  other count rule uses ⌈3n/4⌉.
- **C4.** Cheap version (l. 829-830): "350k on E … for the rest", but M007 and M044 run at 5M and
  M010 at 1.4M.
- **C5.** BRIEF.md l. 38: "adding 16,384 (A07) and 8,192 (E)" gives 343,040 and 171,520. The
  LUT term (13 and 6) is missing. The orchestrator's file; not edited here.
- **C6.** The generated configs sit on the stand-in base: `train.epochs` 500 with `decay_epochs`
  49, `lr` 2e-4 and `batch` 256. They are correctly labelled `launchable: False` and "not for
  launch". The status name `ready_on_base` should not be read as "ready to launch". Keep the
  label until the anchor configs replace the base.
- **C7.** M006 (Deep Sets) is classed as floor-family "trace-only", but no trace exists and its
  derived floor is null. Label it "floor n/a until Z01".
- **C8.** The v1 C1-C4, C6 and C7 are still open (owner list, `ATLAS_fixer_v1.md` l. 158-172).
  C2 (DR-09) must close before FF2 is written.

## The competing-group question

A group running this queue next month would have the replica controls in the machine-readable
spec that builds its runs, so the drift and sd_null measurements the design depends on could not
fall out between prose and generator (A1-v2). They would also quote the power of the rule they
actually apply (B1-v2). Both are fixable in `atlas_spec.py` and `gen_atlas.py` without redesign.

## Decision-label traceability

[D19], [D11], [D13], [A6], [A17] and [A20] are used as in v1. [A2] is now on M074 and M103
(Follow-up F1; 0 anchor-key misses by the fixer's registry sweep, not re-run here). No broken
[D] found.

## What must change before PASS

1. A1-v2: `drift_replicas` in atlas.json; the generator reads it; regenerate and recount.
2. B1-v2 to B5-v2 as above. They may be fixed in the same pass. None needs a redesign.
