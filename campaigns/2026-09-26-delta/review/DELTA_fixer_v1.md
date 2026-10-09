# ATLAS fixer v1

2026-09-27. Input: `review/ATLAS_critical_v1.md` (ITERATE: A1, A2, B1-B4, C1-C7). The owner's
reference is `experiment-designer.md`. Artifacts changed:
- `atlas_spec.py`, the single source;
- `atlas.json`, regenerated;
- `atlas_tables.py`;
- `ATLAS.md`, with the §2 and §3.2 tables re-rendered;
- `LOG_LINES.md` §5;
- `plan.md`, one appended section.

New file: `screen_power.py`. The `code/` tree, `BRIEF.md` and anything outside the campaign
directory were not touched. Nothing was launched or committed.

## atlas.json schema changes

Added (existing key names are unchanged):
- **Per entry:**
  - `floor_traced`: an object `{architecture, floor0, floor1_alive, quantizer, trace_arms,
    label}` when the entry's architecture and weight scheme equal a traced config (A07, which
    includes no-PE = F; the pure-E cells). Otherwise null.
  - `screen_role_350k`: a string, or null when the entry has no 350k screen cell.
- **Inside `floor_derived`:**
  - `on_E` `{floor0, floor1_alive, headroom_350000, label}`, for the near-floor 350k cells re-based
    to E.
  - `floor1_note`, for M047 and M049.
  - `floor1_alive` can now be **null** (M047, M049).
- **Top level:**
  - `traced_floors`: A07, E and A07_old_quantizer, plus a label;
  - `architecture_floors`: the §3.2 table rows;
  - `screen_seed_rule`.

Value changes a generator must handle:
- `base["350000"]` is now per-entry text: E default, own-architecture, E, or "no 350k screen
  cell".
- M014: `targets` = [] and `wave` = "confirm-only (offered at K3)". `targets_confirm` = [350000].
- M075, M077 and M078: 350000 was removed from `targets`.
- `anchor` has a conditional clause about the anchor switching its primary arm to E.
- `floor_derived.label` text changed.
- Notes were appended: M009, M010, M014, M027-M029, M040, M044, M047-M050, the M027 packages,
  and the M040 packages and cells.
- `seeds_screen` stays [1, 2, 3, 4]. It is the lower bound, and the wave STUDY extends it to 1-n.
- **Semantic note:** `floor_derived.headroom_by_target["350000"]` is still the
  *own-architecture* h. It is 0.010 for every A07 cell that is re-based to E. The h that applies
  to those 18 cells is in `floor_derived.on_E.headroom_350000`, and `screen_role_350k` says which
  base the cell uses. A generator that gates 350k cells on the old field would drop or
  misclassify them.

## Findings

```
A1 Floor tables and h stale against the CPU trace; M009/M055/baselines/§0/§3.2/§3.3/§4/§11 wrong — RESOLVED
  changed: atlas_spec.py:1-66 (softmax_floor adds exp_in·H·T·S and lut_term ⌊13H/4⌋; dense terms × b_w;
           asserts: exp/LUT off = arbiter 326,656/989,344 and 163,328/611,000; on = trace 343,053/1,005,741 and
           171,526/619,198; TRACED dict incl. old-quantizer A07 4,580,398; TRACE_LABEL cites evidence JSONs,
           staged at 72a1290, not results); M047-M050 arch weight bits; floors-per-entry block rewritten
           (floor_traced, on_E, roles); ARCH_FLOORS table; atlas_tables.py fl() null-safe, floors.md render.
           ATLAS.md: §0 anchor para + conditional "if the anchor makes E primary", floor table (A07 326,656/989,344
           → 343,053/1,005,741 traced; E 163,328/611,000 → 171,526/619,198; old A07 4,559,008 → 4,580,398 traced),
           formula + substitution, consequence bullet (23,344 / h 0.035 → 6,947 / h 0.010; 7,328 > 6,947);
           §3.2 table re-rendered, substitution text (M009 347,808 → 351,917 > 350k; "only single that fits"
           → "no single fits"; M058 307,104 → 309,158; baselines M048 3,809,549, M050 1,048,749, M047/M049 n/a);
           §3.3 R1-R4 rewritten (R2 default E / A07 feasibility probes; R3 "holds"; R4 441k → 419,602 traced);
           §4 (h 0.035 → 0.010 / E 0.399); §11 near-floor and training-only decisions; FF2 "h 0.42" → 0.399;
           Z01 and DR-18 (answered), DR-01 (answered in part).
  verified: python3 atlas_spec.py <scratch> → asserts pass; A07 343,053 = 262,144 + 64,512 + 16,384 + 13;
            E 171,526 = 131,072 + 32,256 + 8,192 + 6; N=32: 85,517 + 200,864 + 65,536 = 351,917;
            M055 h 0.089 (near-floor), on E h 0.229; M048 on A07 h 0.002, on E 0.081
  propagated: M001 163,328 → 171,526, M002 81,664 → 85,763, M003 97,792 → 114,189, M004 h 0.67 → 0.66,
            M007 457,728 → 474,125, M044 653,312 → 686,106, M042 h 0.09 → 0.026, M043 0.03 → 0.009,
            M055 294,400 → 302,598, M056 56,320 → 58,381 (spec text); 3 rendered tables; 11 prose places in
            ATLAS.md (§0 ×3, §3.1 Z01, §3.2, §3.3, §4, §2.2 FF2, §8 DR-01/DR-18, §11 ×2). grep for the old values
            (0.035, 23,344, 326,656, 989,344, 163,328, 611,000, 0.417, 0.42, 307,104, 440,992, 294,400, 56,320,
            97,792, 81,664, 457,728, 653,312, 81,408, 343,040, 6,960) (ATLAS.md, atlas.json) returns only the
            intended historical mention in M009's tried text ("it was 347,808 before…").
  neighbourhood: every derived floor in the file recomputed from the one formula (25 architecture rows);
            every A07-architecture 350k cell classified by h (18 near-floor → E, 16 floor-family, 7 E-base);
            no-PE cells on E found to duplicate (M075, M077, M078 350k dropped; gate × mask square on E stated);
            M048 on E still near-floor → feasibility probe on E; C5 ("pessimistic") removed with §0.
  pre-registration: A07 350k cells are feasibility probes (G2, EBOPs split, attention state; no G3); 350k accuracy
            cells default to arm E, Kai may override at K1 (§3.3 R2, §0, §7 K1, §11).

A2 Screen cannot resolve +0.3 pt; power check after the wave it should gate — RESOLVED
  changed: ATLAS.md §5.1 "Why 4 screen seeds" → K2 seed rule (sd_plan = √2 · epoch-500 sd of C / E, max with
           sd_null; n = smallest of {4, 6, 8} with k(n, q/m)·sd_plan ≤ 0.3 pt; else ranking mode at n = 4 default,
           or n = 8 with δ_res if Kai buys it; k table per family; factorial σ ceilings; confirm δ_res); §5.1 table
           rows seeds/control/multiplicity; Z14 row given the K2 consequence; §5.2 "Replicas first"; §5.3 G3
           (iii) dropped as a gate, sign count with exact sign p descriptive; significance vs ranking mode;
           "Zero advances" bullet; packages ⌈3n/4⌉; factorial blocks; cap = selection mechanism in ranking mode;
           §5.4 formulas in n with 4-seed lower bound and 8-seed upper bound; §7 2a/K2/K3; §10 seeds and
           falsifier ("unresolved", not "flat"); §11 decision. atlas_spec.py: budget(n), REP per horizon,
           wall(n); atlas.json screen_seed_rule. New screen_power.py.
  verified: python3 screen_power.py . → m = 44 / 20 / 31 / 11; k(4) at W2 5M = 4.86 (review: 4.97 at m 47),
            k(8) = 1.84, sd_d ceiling 0.163 pt; FF1 k 0.86, FF2 1.14; δ_res(8) = 1.56 pt at sd 0.6 pt,
            8.15 pt at 3.14 pt. atlas_spec.py: RE n=4 344,000 (W2 170,000, W3 170,000, teachers 4,000),
            n=6 514,000, n=8 684,000; pod-hours 1,793.3 / 2,679.5 / 3,565.7; wall P2/P10 42.4/17.6,
            59.9/20.2, 79.5/23.5 d.
  propagated: 336,000 → 344,000 (lower bound) / 684,000 (upper); 1,751.6 → 1,793.3 / 3,565.7; 844.5 → 886.2 (W2);
            162,000 → 170,000 (W2); 43.7 d → 42.4 d; 33,500 → 32,500 · s_e; cheap 70,500 → 69,000, 367.5 → 359.7,
            39 → 38 entries; "4 seeds" and "3 of 4" in §5.1, §5.3, §10, §11, K2, FF1/FF2 headers; LOG_LINES.md §5
            (experiment-log stub and decisions draft). 2 files in the campaign, 14 places in ATLAS.md.
  neighbourhood: packages' "3 of 4" and FF2's "3 of seeds 1-4" rules generalized to n; cheap version (3 seeds)
            declared ranking-only; confirm falsifier given δ_res,confirm.

B1 Control undefined under anchor branches (a-f) — RESOLVED
  changed: ATLAS.md §3.3 R2: (a) fallback C: floor-family k_base = arm A's feasible count, else 0 from the pilot;
           rescue reads k_e ≥ 3 and k_e − k_base ≥ 2; M013 runs as a feasibility probe on A07, not dropped; M014 has
           no screen cell. (b) FF2-style rule for A under the K1 override (< ⌈3n/4⌉ of seeds 1-n feasible → re-pair to
           E; the pilot rule cannot guard, 1,005,741 < 1,050,000). (c) replicas run to the longest paired horizon
           (W2: A 500, C 2,000, E 1,000; W3: A 500, E 500, C 2,000), switch applies at every horizon (§5.2;
           atlas_spec REP). (d) E replica budgeted in W2. (e) R4: in-wave C′ replica (seeds 1-n, to 2,000) is the
           primary control, replacing the C replica. (f) M010: G3 does not apply, ladder point only (§3.3, §4,
           M010 pairing/prediction/note in atlas_spec).
  verified: atlas_spec.py regenerates; W2 runs 284 + 12 replicas, W3 256 + 12; runs by horizon match §5.4.
  propagated: budget numbers as in A2 (the replica change is part of those totals).
  neighbourhood: every other anchor-branch path checked for its control: E failure at 350k (drops to 5M, K3),
            base-stability re-base on E (arm E with arm D's optimizer, proposed to Kai), cheap version
            (anchor snapshots declared as long-horizon controls).

B2 Retries without "why different"; H1 not caught by G1; M014 horizon — RESOLVED
  changed: atlas_spec.py WHY_LR note on M028, M029 (vs H1: batch 2,790, cosine to 1e-6 per cycle, EBOPs term;
           H1's batch and STE version not in the inventory, so no cause claimed); WHY_WS note on M027 and
           M061, M062, M064 (vs F1/C3/C4: 5M screen target, squeeze ×0.38 of the traced 13.18M init, 350k only at
           confirm). ATLAS.md §5.3 G1: H1-type degradation (best epoch ≤ 20; ≥ 5 pt below for 10 consecutive
           epochs within 100; EBOPs still ≥ 50 % of epoch 1) counts toward "unstable" and base stability; why
           F1-shaped runs do not trigger it; stated as conservative at 350k. M014: not screenable at any
           H ≤ 2,000 (β reaches 3e-7 of 3e-6 at 2,000); targets [] and confirm-only, offered at K3 (§2, §4, §5.3
           G0, §7).
  verified: rendered singles/combos tables carry the notes (note column added to the singles table).
  propagated: M014 in 7 ATLAS.md places; cheap version recount (M014 excluded).
  neighbourhood: every other entry with a longer horizon checked (M015, M031, M032 and packages: treatment
            onset reachable at their H); other retries of recorded failures: M001, M002, M005, M009 and M035 state
            why they differ; M042-M044 and M046 cite only the old quantizer / N=16 era as the difference (not
            changed here; the owner may add a line).

B3 M040 gets free inputs at iso-EBOPs — RESOLVED
  changed: atlas_spec.py NOHW note on M040 and every entry whose combo_of holds M040 (M067, M080, M081, M085-M087,
           M091-M093, M095); M040 prediction says the iso-EBOPs match excludes the off-model features; ATLAS.md §6
           lesson 5 lists them as not hardware candidates.
  verified: `[e for e in entries if 'M040' in combo_of]` = the 10 IDs above, each note carries the label.
  propagated: none needed beyond the notes and §6.
  neighbourhood: other input-path entries checked: M038 (gate) and M041 (standardization) change caches but
            add no off-model computation beyond the existing affine (J11); M037 is training-only.

Post-advisor edits (ATLAS.md only, no regeneration needed):
- §0: the anchor-switch conditional was reworded. The deltas stay stated against A07, and the
  design is invariant to the switch.
- §0: the old-quantizer 1-bit-alive floor is shown, 4,580,398 traced.
- R2: M013 is covered when arm E fails.
- G1: the claim about squeeze speed became a ratio.
- §1: the sentence now names the new fields.

B4 Near-floor default unpriced in §11 — RESOLVED (by A1)
  changed: ATLAS.md §11 near-floor decision restated with traced h 0.010 and 7,328 > 6,947; recommends E as the
           default (now pre-registered in §3.3 R2).
```

## C findings

None is marked apply-now in the review, so C5 is the only one resolved, as a side effect of A1.
The rest are listed for the owner:
- C1: M014 "14 AUC points" needs its split (validation, `tried-already.md:89`), and M043 "FFN 32
  beat 64" needs its metric. Open.
- C2: FF2 factor B (M012, f0 = 7) may be a no-op against the anchor's i + f = 7 init. DR-09 must
  close before FF2 is written. Open.
- C3: it is not stated whether FF1 runs as a 2^(4−1) or waits if the P-T1 teacher fails. Open.
- C4: a wave-block term is needed if FF1 is pooled with the wave-2 one-high singles. Open.
- C5: §0 "pessimistic" exp input. **Resolved**: the paragraph was rewritten, and SAT is the
  traced case.
- C6: M038 should carry the label "crosses input set (gate), by design". Open.
- C7: M024 and M025 must not be called binary-only in outward text before the DSP audit. Open;
  the label is already kept in §6.

## Integrity check (re-run after the last edit)

- `python3 atlas_spec.py <scratch>`, then `cmp` against `atlas.json`: identical. A double
  regeneration is also identical.
- 103 IDs, all unique. 103 `| Mnnn |` table rows.
- Every `code_changes` slug is in `patches` (38), and every slug appears in §12.
- Every `combo_of` ID exists. `anchor-arm-F` is the one symbolic reference.
- `atlas_tables.py` output (singles, combos and floors) is present verbatim in ATLAS.md.
- The tier, family and code-tier counts are unchanged, so the §2 counts still hold.

## Copies outside this campaign, not edited here (for the orchestrator / Kai)

- `.claude/memory/experiment-log.md:13` (the atlas stub) still reads "4 seeds" and "Screen
  336,000 run-epochs (1,751.6 pod-hours…)". The replacement text is in `LOG_LINES.md` §5.
- `.claude/memory/decisions.md:12` still reads "4 seeds … a +0.3 pt and 3-of-4-seeds rule". The
  replacement text is in `LOG_LINES.md` §5.
- `BRIEF.md:35-38` (orchestrator's file, left as written) still quotes the arbiter floors 326,656
  / 989,344 / 163,328 / 611,000 and "23,344 EBOPs outside the softmax". The traced values are
  343,053 / 1,005,741 / 171,526 / 619,198 and 6,947.

## Follow-up 1 (coordinator, generator run on atlas.json; 2026-09-27)

```
F1 M074/M103 set train.optimizer without [A2] in anchor_patches_required — RESOLVED
  changed: atlas_spec.py combo() takes anchor_keys; M074 and M103 pass ["A2"].
  sweep: every config_delta key that code/key_registry.json registers to an anchor patch ([A1] train.lr_cycle_epochs,
         [A2] train.optimizer, [A3] arch.pt_gate_gev, [A20] quant.act_f0) now has that patch in the entry's
         anchor_patches_required, 0 misses across 103 entries (read-only use of the registry).
F2 M006 arch.deepsets_dims was prose — RESOLVED
  changed: {"phi":[64,64],"ctx":64,"phi_post":[64],"rho":[64,32,16],"pool_scale":0.0625}, the dict form that
           code/newmods/deepsets.py dims_for() accepts (it rejects a list). Source: reference-code/HGQ2-examples/
           jsc150/model.py:88-100 (read here: l. 88-89 phi 64/64, l. 90-92 context 64 on a 2^-round(log2 N) sum,
           l. 95 post 64, l. 96 sum × 1/16, l. 97-99 rho 64/32/16, l. 100 out 5); note on M006; DR-23 answered.
F3 M020/M071 Bop gamma/tau null — PARTIALLY RESOLVED (by design)
  no value: card B10 carries none, and arXiv:1906.02107 was not opened this session. No value picked.
  changed: BOP_NOTE on M020 and M071 (null on purpose, the wave STUDY pre-registers from the paper's section/table,
           the generator refuses until then); ATLAS.md §12 and DR-22 say the same; config_delta_semantics restated
           (Bop nulls must be filled; the train.clipvalue / train.weight_decay nulls mean "unset" on the [A2] path).
  remains / route to: physics-researcher (DR-22) for the γ/τ values with section/table; then the M020/M071 deltas.
F4 §5.2 E replica in wave 2 — already RESOLVED in v1 (B1d)
  ATLAS.md §5.2 "Wave 2: A ... C ... E at 350k to 1,000"; atlas_spec REP["W2"] = {500, 1000, 2000}. The generator
  run predates that text if it read "A and C".
```
Integrity re-run: `atlas_spec.py` regenerates `atlas.json` byte-identically. 103 unique IDs. The
38 slugs are all in `patches` and §12. Every `combo_of` ID exists. There are 0 anchor-key misses
and 0 prose placeholders. The rendered tables are present verbatim in ATLAS.md. The tier, family
and code-tier counts are unchanged. `atlas.json` sha256 is
e736d1b2ddfb74a46b811ddf5eda7bd7e7df31b2f4b23713696357d1b40e8780.
Schema: no new keys. Values changed: M006 `config_delta` (a dict instead of a string); M074 and
M103 `anchor_patches_required` (["A2"]); the M006, M020 and M071 notes; `config_delta_semantics`.
