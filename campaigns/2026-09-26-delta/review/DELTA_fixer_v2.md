# ATLAS fixer v2

2026-09-27. Input: `review/ATLAS_critical_v2.md` (ITERATE: A1-v2, B1-v2 to B5-v2, C1-C8), Kai's
launch-gate answers (`.claude/memory/decisions.md`, top entry "2026-09-27 (Kai, launch-gate
answers)", 08:40 PDT, read and verified), `research/DR-22-bop-hyperparameters.md`, and the
coordinator's two inputs from the training-batch session (naming; the non-degeneracy rule,
verified in `campaigns/2026-09-26-training-batch/STUDY.md` l. 386-404 at commit 5d6c3c9).

Changed: `atlas_spec.py`, `atlas.json` (regenerated), `screen_power.py`, `atlas_tables.py` (one
header), `ATLAS.md` (header log, §0, §1, §2, §2.2, §3.1, §3.3, §4, §5.1-§5.4, §7, §8, §11, §12,
and the three rendered tables), `BRIEF.md` (the "Anchor amendment" paragraph only),
`LOG_LINES.md` §5, and `plan.md` (one appended entry). Nothing in `code/` was touched. Nothing was
launched or committed.

**atlas.json sha256: 7e57bf2428bd546acc63e759ae625e3926f48a5df0c233cbd13671283dd30109**
(supersedes e736d1b2…8780).

## Schema changes (additive; no key renamed or removed)

- Top level:
  - `drift_replicas`: `{rule, R4, seeds, W2: [{arm, target, horizon_epochs, serves}], W3: [...]}`.
  - `anchor_arms_after_D21`: the arm meanings the generator must adopt.
  - `screen_seed_rule.gate_ii`: a new sub-key.
- Per entry: `covered_by_anchor_study`, null or `{"350000", "5000000", "related"}` (M006, M047-M050).
- `screen_role_350k` has a fourth value, "near-floor on A07 and on E: …feasibility probe on E"
  (M047, M048, M049).

Value changes a generator must handle:
- `base` texts (below).
- `anchor`, `config_delta_semantics`, `screen_seed_rule.rule`, `traced_floors.*.arms`, and the
  `architecture_floors` labels for the A07 and E rows.
- M020 and M071 `config_delta`: `train.bop_gamma` 1e-4 and `train.bop_tau` 1e-8, no longer null.
- M013 `if_floor_fails`.
- Text in M001, M010, M028, M029, M046, M048, M049, M050, M075, M077, M078, M096-M102.

## Base-text changes (for `code/anchor_arms.json`; the orchestrator edits it, I did not)

The new texts deliberately match **none** of the current `base_text_rules`. The unmodified
`gen_atlas.py` therefore stops with `GenError: M001: no base_text_rules match …` (run with
`--out` into the scratchpad, nothing written) instead of silently building A07 cells.

| old text (count of cells) | new text | rule to add → arm |
| --- | --- | --- |
| `E` (7, FF2 at 350k) | `arm A (E at 350k, Kai-confirmed [D21])` | `^arm A \(E at 350k` → A |
| `E by default (delta applied to arm E); A07 feasibility probe only on Kai's K1 override` (18) | 15 × `arm A (E at 350k, Kai-confirmed [D21]); delta applied to arm A's config; accuracy screen`; 3 × `…; feasibility probe on E, no accuracy reading` (M047-M049) | same rule → A |
| `own A07-derived architecture: feasibility vs arm A (G2), accuracy vs arm E (Welch, cross-architecture)` (16) | `floor family on the A07-350 base (own A07-derived architecture): feasibility vs arm A07-350 (G2), accuracy vs arm A (E; Welch, cross-architecture)` | `^floor family on the A07-350 base` → A07-350 |
| `A07 at 1.4M (new rung; paired to A snapshot seeds, target differs)` (key `1400000` in all 103; 1 cell, M010) | `the 1.4M rung on the A07-350 base (A07 at 1.4M; paired by seed to A07-350's snapshots, target differs)` | `^the 1\.4M rung on the A07-350 base` → A07-350 |
| `C` (5M), `no 350k screen cell` | unchanged | unchanged |

`anchor_arms.json` edits needed with them:
- `arms.A.delta` := E's (`arch.d_model` 24, `arch.n_heads` 2, `arch.pos_enc` none).
- New `arms["A07-350"]` = {350000, {}}.
- `D` := E + the optimizer delta.
- `F` := {d_model 24, n_heads 2} (E + learned PE).
- `B` unchanged. `E` may stay as an alias of A.
- Delete `replicas_by_wave`.
- `gen_atlas.py` (ml-engineer) reads `atlas["drift_replicas"]` in place of it, with the arm,
  target and horizon per row.
- The `--confirm-350k-base` default E → A.
- The teachers' `base_arm: 'A'` label (gen_atlas.py about l. 380/393) → A07-350. The config
  itself is A07 already, because the teacher delta is applied to the base config, not to arm A.

Checked in the scratchpad with a patched copy of the generator (those edits only; `code/` untouched):
- 566 configs written (W2 296, W3 268, prereq 2) and 0 refused. The refusals were the 8 Bop nulls.
- Replicas by (wave, arm, target, horizon) × 4 seeds: W2 A 350k 1,000; A07-350 350k 500; C 5M 2,000;
  W3 A 500; A07-350 500; C 2,000. This equals §5.2.
- Spot checks:

  | config | d_model / heads / PE | base |
  | --- | --- | --- |
  | M011-t350000 | 24 / 2 / none | arm A |
  | M001-t350000 | 32 / 2 / learned | A07-350 |
  | M010-t1400000 | 32 / 4 / learned | |
  | M096-t350000 | 24 / 2 / none | |
  | M049-t350000 | 24 / 2 / none | |

  M020-t5000000 carries `bop_gamma` 1e-4 and `bop_tau` 1e-8.

## Findings

```
A1-v2 Drift-replica plan absent from atlas.json; generator built the pre-fix plan — PARTIALLY RESOLVED
  changed: atlas_spec.py: DRIFT dict replaces the bare REP (REP now derived from it, asserted equal to the
           old {W2: 500/1000/2000, W3: 500×2/2000}); atlas.json top-level `drift_replicas` (arm, target,
           horizon, purpose; R4 rule: C → C′ primary, A/A07-350 not run; seeds 1-n, n_W3 ≤ n_W2).
           Under [D21] arm names: W2 A(E)@1,000, A07-350@500, C@2,000; W3 A@500, A07-350@500, C@2,000
           (same horizons as fixer v1's A07@500 / E@1,000 / C@2,000). ATLAS.md §5.2 names the key.
  verified: patched generator copy (scratch) → REP-* by (wave, arm, horizon) equal §5.2; 296 + 268 + 2 = 566,
            0 refused (was 558 + 8 refused). Budget printout identical to before (344,000 / 514,000 / 684,000
            run-epochs; walls 32,500 / 13,500 s_e at n = 4).
  propagated: none needed (no number changed).
  neighbourhood: every other base arm a replica pairs to (FF1 all-low = C, FF2 all-low = A, floor-family
            k_base = A07-350, M015 on A at 1,000, M031/M032 on C) has a replica row.
  remains / route to: ml-engineer, gen_atlas.py reads `drift_replicas` and `replicas_by_wave` is deleted;
            orchestrator, anchor_arms.json [D21] arms and rules (table above); then regenerate code/configs
            (index.json and code/GATES.md still pin e736d1b2).

B1-v2 K2 rule sized n for gate (i) alone; the joint power at 0.3 pt was about 0.45 — RESOLVED
  changed: gate (ii) mean Δ ≥ δ → mean Δ ≥ δ/2 (δ = 0.3 pt stays the MDE target; δ_res mode: δ_res/2).
           n sized by k_joint(n, α_eff), the gap with 80 % power for (i) and (ii) together.
           screen_power.py rewritten: exact k_t (noncentral t), Monte Carlo k_joint (200,000 reps, seed 20260927),
           the v1 rule's joint power printed for the record.
           ATLAS.md §5.1 (rule text, table, items 2-5), §5.3 G3 (ii), and the 0.3 pt paragraph;
           §11 block 2; atlas.json screen_seed_rule.rule and gate_ii; LOG_LINES §5 (both texts).
  verified: python3 screen_power.py . — v1 rule joint power 0.434 / 0.461 / 0.476 at n = 4 / 6 / 8 (W2 5M, m 43);
            the review gave 0.432 / – / 0.475 at m 44. k_joint vs k_t differ ≤ 0.03 (1.68 vs 1.65,
            unadjusted, n = 4), so the n a given sd selects barely moves.
  propagated: 4.86 → 4.83 (k(4) W2 5M), 1.84 → 1.83, 3.72 → 3.66, 1.60 → 1.58 (W2 350k), 0.115 → 0.116 pt,
            1.56 → 1.55 pt, 8.15 → 8.12 pt, 10.86 → 10.73 and 2.30 → 2.32 (cheap version), the W3 5M
            k(4) 4.32 → 4.33 and the W3 350k k(4) 3.03 → 3.04, and FF ceilings now listed for n = 4 / 6 / 8:
            18 values in ATLAS.md (§5.1 table and items 4-5, §5.4 cheap version, §11), 1 file; no copy
            outside the campaign quotes them.
  neighbourhood: factorial blocks use the same (ii) floor (§5.3); confirm tier kept on k_t (it has no gate (ii));
            packages' ⌈3n/4⌉ rule unaffected.

B2-v2 screen_power.py counted m by a note substring — RESOLVED
  changed: m counted per (entry, target) cell from tier and screen_role_350k; baselines excluded at both targets
           (comparands, no advance decision, now stated in §5.1 and §5.3 G3); probes and M010 excluded.
  verified: W2 5M 44 → 43, W2 350k 20 → 19 (M050 leaves), W3 5M 31, W3 350k 11 (unchanged).
  propagated: ATLAS.md §5.1 table (m and α_eff: 0.0050 → 0.0053 at W2 350k).
  neighbourhood: FF2 cells (factorial-cell) were never in the W3 350k package family and are not now.

B3-v2 screen_role_350k said "accuracy screen" for the M047-M049 probes — RESOLVED
  changed: fourth role near-floor-E-probe (atlas_spec ROLE and role logic); base text says "feasibility probe on E".
  verified: roles 350k: own-arch 16, near-floor-E 15, E-base 7, near-floor-E-probe 3 (= M047, M048, M049).
  neighbourhood: every other near-floor cell has on-E h ≥ 0.10 (0.229-0.672).

B4-v2 Control gaps under fallbacks — RESOLVED
  changed: ATLAS.md §3.3 R2 "If arm A fails at 350k": floor-family cells fall back to G2 only; FF2 → C at 5M.
           R4 now lists survivors from atlas.json: 40 singles/baselines with a 5M cell, M061-M095 and M103 at
           5M, FF2 on C′ at 5M; dropped M001-M006, M009, M051-M060, M010, M013, M014.
           §2.2 FF2 says FF2 goes to C′ under R4. M013 if_floor_fails → "350k only: on arm A (E) by default; a
           feasibility probe on A07-350 (vs its k_base) if arm A fails at 350k; dropped under R4".
  verified: survivor list computed from atlas.json targets and if_floor_fails.
  neighbourhood: combos carry the combo() default if_floor_fails "drop" even when they are not floor crosses
           (M061-M095, M103). R4 is stated from targets and family, not from that field. Owner: the default
           could be made accurate; not changed here (no behaviour depends on it).

B5-v2 n per wave × target vs packages needing singles on the same seeds — RESOLVED
  changed: §5.1 item 2 and screen_seed_rule: n_W3 ≤ n_W2 at the same target; a W3 family that would need more
           runs at n_W2 (ranking mode if n_W2 does not qualify); no single is extended. Budget unchanged.
```

**Anchor re-base on [D21] (job 2).** Kai's answers are verified at `decisions.md`, top entry.
The names follow the coordinator and the anchor STUDY changelog (l. 72-74 at 5d6c3c9):
- arm A = E at 350k;
- A07-350 = A07 at 350k, descriptive;
- C = A07 at 5M;
- B = E at 250k;
- D and R on E;
- F = E + learned PE.

Changes:
- **K1 wording removed everywhere.** §0 rewritten, and the K1 point now reads "settled; only the
  anchor's fallback C remains".
- **§3.3 R2.** The override branch is closed, and the floor family's k_base is A07-350.
- **§11.** The A07 block is Kai-confirmed, FLAG NO.
- **Rest of ATLAS.md:** §4, §5.1, §5.2 (the base-stability proposal is now anchor arm D; no new
  run), §7 wave 0/2a/4, Z01, Z14, the §0 floor table labels and the FF2 text.
- **atlas_spec.py:** the M001 prediction ("than A07-350"), M010 (ladder A07-350 to C), and
  M028/M029/M048/M050 (predictions against "the base arm" or C instead of A). The M046
  name/note/tried now reads "at 350k the PE contrast is anchor A vs F; pre-[D21] F = A07 without
  PE". In M075/M077/M078 the notes and ladders say no-PE is a no-op on arm A.
- **Pre-[D21] trace arm names.** TRACED labels them. The traced numbers are unchanged
  (A07 343,053 / 1,005,741; E 171,526 / 619,198).

H/NB overlap, recorded in `covered_by_anchor_study`, the M049 note, §2, §5.4, §7 and §8 DR-02:
- **M049 at 350k is covered by NB.** It is the same weight scheme on arm A. The cell stays in the
  budget as an upper bound, and the wave-2 STUDY drops it if NB's epoch-500 snapshot exists by K2.
  It is never a separate confirm cell, and its patch is NB's `kbi_learnable` item.
- **Related, not covered:** M049 at 5M, M047, M048, M050 and M006 (H is the xfm-n64 transformer,
  not Deep Sets). No entry was deleted.
- **K6** is updated. The §5.4 plausible confirm wave keeps n_c = 12 (9 survivor cells + M048 at 2
  targets + M049 at 5M).

**Bop (job 3).** M020 and M071 are set to γ = 1e-4 (undecayed) and τ = 1e-8, labelled "scan
seed, not tuned for this setup (DR-22)".
- Sources: arXiv:1906.02107 §5.2 and §5.3, and Larq `Bop` defaults at larq/larq `master` commit
  3d7de8832a477285bbf3c36252e24fcb9299a959, `optimizers.py` l. 314-316, with DR-22's caveat that
  this is a master commit, not a tagged release.
- The note adds that the wave STUDY measures the anchor's |m| distribution and may pre-register a
  τ scan before launch.
- Also updated: `config_delta_semantics`, §8 DR-22 (answered) and the §12 closing paragraph.

**Non-degeneracy (coordinator input b).**
- §5.1 has a new validity paragraph and table row. It cites STUDY.md l. 386-404 at 5d6c3c9:
  - (a) EBOPs ≤ target;
  - (b) EBOPs above the traced 0-bit floor;
  - (c) validation accuracy > p_maj + 5·√(p_maj(1 − p_maj)/62,000).
- The atlas inherits the rule at both tiers:
  - "feasible" means (a)-(c) in G2, k_base, the ⌈3n/4⌉ rules, Z14 and every Δ_s, and the
    degenerate count is reported;
  - (b) needs each architecture's traced floor, so Z01 gates the cells of the untraced
    architectures at both targets;
  - p_maj is the anchor's value (same validation jets).
- Consistency with G1: the collapse level (≤ 0.25) and (c) are separate tests. If p_maj puts the
  (c) threshold above 0.25, the collapse level is raised to it. No p_maj value is quoted.

**C items.**
- None is marked apply-now.
- C2 (FF runs hard-coded at n = 4) was resolved as a side effect of B1: parameterized by n.
- C5 (BRIEF arithmetic) was resolved by the BRIEF rewrite: 326,656 + 16,384 + 13 = 343,053 and
  163,328 + 8,192 + 6 = 171,526.
- Open for the owner: C1 (§3.2 heading "arbiter formula"; "per block", "fit assumes 4-bit
  tables"), C3 (G2 rescue thresholds do not scale with n), C4 (cheap-version wording: M007/M044
  at 5M, M010 at 1.4M), C6 (keep `launchable: False` until the anchor configs replace the
  stand-in), C7 (M006 "floor n/a until Z01"), and C8 (v1 C1-C4, C6, C7; C2/DR-09 before FF2).
- New for the owner: M027's warm start and M036's attention-map KD at the 350k confirm (arm A, E)
  need an E-shaped teacher, because P-T1 is A07. This is flagged in §11 and not redesigned.

## Integrity check (after the last edit)

- `python3 atlas_spec.py <scratch>` was run twice. Each `cmp` against `atlas.json` is identical.
- IDs: 103, unique. There are 103 `| Mnnn |` table rows.
- Slugs: 31 are used, and all 38 appear in `patches` and in §12.
- Every `combo_of` ref exists. The one symbolic reference is `anchor-arm-F`.
- The `atlas_tables.py` output (singles, combos, floors) is verbatim in ATLAS.md.
- Tier, family and code-tier counts and every budget number are unchanged against the pre-edit
  printout. The only print diffs are the role counts and the arch labels.
- The remaining null deltas are the whitelisted "unset" optimizer fields (M033, M069, M070, M074).

## Copies outside this campaign (the orchestrator updates them; replacement text is in `LOG_LINES.md` §5)

- `.claude/memory/experiment-log.md:11-16` (the atlas stub). It still reads "Anchor = training-batch arm A
  (A07-N64, [D19] quantizers, provisional)" and "350k accuracy cells default to arm E". The
  replacement names E at 350k [D21].
- `.claude/memory/decisions.md`, "2026-09-27 (orchestrator, method atlas)", first bullet (two-tier). It
  still reads "advance by BH plus a +0.3 pt (or declared δ_res) threshold". Replacement: mean gap ≥ 0.15 pt
  (δ/2), with n sized for the whole rule.
- `code/anchor_arms.json`, `code/gen_atlas.py`, `code/GATES.md` and `code/configs/index.json` are in the
  campaign but outside my remit. They pin e736d1b2 and the pre-[D21] arms. Routes: the orchestrator
  (anchor_arms.json) and the ml-engineer (gen_atlas.py reads `drift_replicas`; regenerate).

No record or outward copy (README, RESEARCH.md, messages/) quotes an atlas number.

## Follow-up v3 (2026-09-27; `review/ATLAS_critical_v3.md`, items routed to the atlas owner)

**atlas.json sha256: 6fbd4b5d8edadbca3817b8ef6a03dad1a714b0f6bc97b370429a6210da3c3711**
(this replaces 7e57bf24…0109).

**Schema change (additive).** Each entry gains the field `hw_labels`, a list of strings computed
in `atlas_spec.py` from the entry's merged `config_delta`, so packages inherit their components'
labels. `base["1400000"]` now appears only on M010 (C2); a generator reads `base[str(target)]`
for listed targets only.

```
B2-v3 Hardware-risk labels not carried per row — RESOLVED
  changed: atlas_spec.py hw_labels():
    - "DSP audit required …" when quant.channel_gain is set: M024, M025, M065, M066, M067, M080.
      No atlas entry adds a new act×act multiply; those cards are parked or rejected, §9.
    - "no export path yet (DR-17): the patch series refuses HLS export for …" for every key the
      series registers with export_ok=False. The keys are quant.binary_center, beta_mode,
      channel_gain, arch.head_dims, pre_block_act, quant.weight and layer_weight_override
      (patches 0002, 0005, 0006, 0007, 0015-0018, read from the register() calls; PLAN_patches.md
      "Export"). Entries: M016, M017, M022-M025, M045, M047-M050, M065-M067, M080, and FF2 M097-M102.
    - "no export path yet (DR-17): … (not in the patch series)": attn_kind, Deep Sets body and
      runtime key mask. Entries: M004-M006, M039, M053, M054, M056, M059, M060, M076-M080.
    - "not a hardware candidate until the derived-feature path is costed": M040, M067, M080, and
      M081, M085-M087, M091-M093, M095.
    ATLAS.md §6 lesson 5 is rewritten around the field, and §1 names it.
  verified: the label lists are recomputed from atlas.json (above); 43 entries carry at least one label.
  neighbourhood: every export_ok=False register() call in patches 0001-0021 is mapped. M027 and M063
    carry no label: the teacher's weight scheme is not deployed.
C2 M010's 1.4M base text on all 103 entries — RESOLVED (base["1400000"] emitted only when 1.4M is in targets or targets_confirm).
C3 §0 E row omits F — RESOLVED (§0 table row and the architecture_floors E label: "F = E + learned PE, traced at the anchor PREFLIGHT").
C4 M038 explicit null pT-gate override — KEPT and documented. atlas.json keeps 0 = ungated. The M038 note
   and config_delta_semantics say the generator writes it as an explicit arch.pt_gate_gev null ([A3]:
   null = ungated), which must stay explicit to override the anchor's 2 GeV gate. The generated
   configs/W2/M038-t350000-s1.json has `pt_gate_gev: null`.
C1 (gen_atlas --help wording) — left to the ml-engineer, as instructed. A1-v3 and B1-v3 are code/ items, not mine.
```

**Integrity checks** (all rerun after the last edit):
- `atlas_spec.py` regenerates `atlas.json` byte-identically on two runs.
- Budget printout unchanged.
- 103 unique IDs and 103 table rows.
- The 38 slugs appear in `patches` and in §12.
- No bad `combo_of` references.
- The singles, combos and floors tables are verbatim in ATLAS.md; the singles table carries the new M038 note.
- `screen_power.py` m = 43 / 19 / 31 / 11, unchanged.
- The current `code/gen_atlas.py`, output to the scratchpad only, wrote the screen tier (566 configs: W2 296, W3 268) and the confirm tier (1,544). `code/configs` still pins 7e57bf24 and needs regenerating.

## Follow-up v4 (2026-09-27; `review/ATLAS_critical_v4.md` = PASS, items C2-v4 and B3-v4)

**atlas.json sha256: 8b1c3aa6b1b584236345ba7d2ed54f6f518d1b0548440cad913b7aa891481265**
(this replaces 6fbd4b5d…3711). There are no schema changes.

```
C2-v4 M006 label and ATLAS.md §6 lesson 5 said Deep Sets is "not in the patch series" — RESOLVED
  changed: atlas_spec.py NO_EXPORT_OTHER texts now state the training-path status and that no HLS export is written:
             - Deep Sets: wired by patch 0023.
             - Linformer: refused by 0022 until [A20].
             - ReLU/N: blocked.
             - Key mask: blocked on [A3]/[A4].
           Label suffix: "(not in the patch series)" → "; no HLS export written".
           ATLAS.md §6 lesson 5 bullet rewritten the same way. It adds that Bop (0024) is training-only
           and carries no hardware label.
  verified: M006 hw_labels = ["no export path yet (DR-17): Deep Sets body (training path wired by patch 0023); no HLS export written"].
            Neither ATLAS.md nor atlas.json contains "not in the patch series" any more.
B3-v4 Bop flip rule (reflect about the mean) is not the paper's sign flip — RESOLVED (routed to Kai)
  changed: BOP_NOTE, which reaches M020 and M071, now states the Kai decision at K2, before M020 is packed,
           with both options:
             - Option 1 (patch 0024, code/newmods/bop.py): w <- 2*alpha - w. This keeps beta and keeps
               activation ranges comparable with the Adam anchor.
             - Option 2 (arXiv:1906.02107 Algorithm 2): w <- -w with the latents at +-1. Beta becomes
               1 - alpha^2, so the activation scales change against the anchor.
           ATLAS.md §7 K2 list names the decision. Source: code/GATES.md, DECISION block (l. 308-309).
```

**Integrity checks** (all passed):
- `atlas_spec.py` regenerates `atlas.json` byte-identically on two runs.
- The budget printout is unchanged.
- 103 unique IDs and 103 table rows.
- Every slug is in `patches` and in §12.
- No bad `combo_of` references.
- The three rendered tables are verbatim in ATLAS.md.
- `code/configs` still pins the previous `atlas.json` and needs regenerating.
