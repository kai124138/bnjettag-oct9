# ATLAS review, critical-reviewer, v3 (solo mode, re-review)

2026-09-27 09:22. Artifact at commit 812b1eb: `ATLAS.md`, `atlas.json` (sha256 7e57bf2428bd…0109,
checked), `atlas_spec.py`, `screen_power.py`, `BRIEF.md`, and `code/` (ledger `code/README.md`,
`gen_atlas.py`, `anchor_arms.json`, `configs/index.json`, `patches/0001-0021`, `apply.sh`,
`BLOCKED.md`, `WIRING.md`, `GATES.md`, `newmods/`, `tests/`, `tests_patches/`). Inputs:
`review/ATLAS_critical_v2.md`, `review/ATLAS_fixer_v2.md`, `.claude/memory/decisions.md` (Kai,
launch-gate answers, 2026-09-27 08:40), the training-batch `STUDY.md` at 5d6c3c9 and
`research/DR-22-bop-hyperparameters.md`. Reviewed as a pre-registered queue, not as a STUDY.
`plan.md` has 4 uncommitted orchestrator lines after 812b1eb; they are not part of the reviewed commit.

**VERDICT: ITERATE.** Every v2 A and B finding is resolved, and I checked each one against the
files. [D21] is applied consistently, the non-degeneracy rule matches the anchor STUDY, and the Bop
values match DR-22. One new Category A is in the code. On the only tree that exists (the tarball +
0001-0021), no layer refuses a config whose treatment key nothing reads. As a result, the Linformer,
Deep Sets and Bop configs (and every blocked-slug config) build and pass the CPU gate as the plain
base model. Nothing is launched and nothing has gone outward, so there is no ESCALATE and no
experiment-log warning line.

## What I recomputed

| check | result |
| --- | --- |
| `python3 atlas_spec.py <scratch>` | `cmp` with `atlas.json`: identical. 103 entries (50 singles, 53 combos); roles 350k: own-arch 16, near-floor-E 15, E-base 7, near-floor-E-probe 3 |
| `python3 screen_power.py .` | m = 43 / 19 / 31 / 11 (W2 5M, W2 350k, W3 5M, W3 350k); k_joint(4/6/8) W2 5M 4.83 / 2.50 / 1.83, W2 350k 3.66 / 2.09 / 1.58, W3 5M 4.33 / 2.33 / 1.73, W3 350k 3.04 / 1.84 / 1.43; v1-rule joint power 0.434-0.487. All equal the ATLAS.md §5.1 table |
| m by hand from atlas.json | W2 5M: 43 singles + 4 baselines (excluded) = 47 cells; W2 350k: 7 floor-family + 12 near-floor-on-A singles = 19 (M050 baseline and the 3 probes out); W3 5M 31 packages (15 FF1 cells separate); W3 350k 9 + 2 = 11 (7 FF2 separate) ✓ |
| `python3 code/gen_atlas.py --out <scratch>` (strict) | `cells by wave (incl. drift replicas): {'W2': 296, 'W3': 268}`; `status: {'needs_patches': 374, 'placeholder_pending_anchor': 96, 'ready_on_base': 96} configs written: 566`; errors none. `diff -rq` against `code/configs/`: identical, index.json included |
| index vs atlas.json | 540 entry cells = 540 (id, target, seed) cells of atlas.json, 0 missing, 0 extra, 0 duplicate; horizons 0 mismatches; base arm vs `base[target]` through `anchor_arms.json` `base_text_rules`: 0 mismatches. Entry cells by (target, arm): 5M C 372; 350k A07-350 64 (floor family); 350k A 60 near-floor + 28 FF2 + 12 probes; 1.4M A07-350 4 |
| drift replicas (index, kind drift_replica, × 4 seeds) | W2: A 350k @1,000; A07-350 350k @500; C 5M @2,000. W3: A @500; A07-350 @500; C @2,000. Equal to `atlas.json` `drift_replicas` and to §5.2 |
| `code/apply.sh` (scratch, full and `0`) | `APPLY_ALL_PASS` both; 0001-0021 apply cleanly with `--3way` (1.3 s) |
| invariance gate (`pyenv.sh gate_invariance.py` on pristine and patched, `compare_fp.py`) | 7/7 `SAME`, `INVARIANCE_GATE_PASS` (2 min 53 s for both trees). My pristine fingerprint also equals the stored `tests_patches/fingerprint_pristine.json` (`INVARIANCE_GATE_PASS`) |
| `tests/` (pytest, pinned env) | `13 passed` on the patched tree and `13 passed` on the bare tarball, equal to GATES.md §3 |
| ledger vs files (38 slugs) | 38 rows, 0 missing, 0 extra. 20 "gated-on-tarball" patch rows: each has `patches/NNNN-<slug>.patch`, a `SLUG_TEST_PASS` line in `slug_tests.txt` (`SLUG_TESTS_ALL_PASS`) and a key in the `E-shape-sweep` block of `slug_results.json`. 12 "blocked" rows: no patch file, and a design note in BLOCKED.md. 3 new-files "gated" diagnostics: 2 + 1 + 1 = the 4 tests of `test_diags.py`. 3 "written" rows: linformer 2, deepsets 3, bop 4 tests, all passing |
| three configs (flattened diff vs the replica of the base arm, same seed) | **ready_on_base, E at 350k**: `W2/M043-t350000-s2` vs `W2/REP-A-t350000-s2`: `arch.ffn_dim` 64 vs 32, `train.epochs` 500 vs 1,000 (replica horizon) ✓. **needs_patches**: `W2/M011-t350000-s2`: `quant.act_granularity` element vs channel ✓; `W2/M020-t5000000-s2` vs `W2/REP-C-t5000000-s2`: `train.binary_optimizer` bop, `bop_gamma` 1e-4, `bop_tau` 1e-8, epochs 500 vs 2,000 ✓. **drift replica**: `W2/REP-A-t350000-s2` vs `W2/REP-A07-350-t350000-s2`: `d_model` 24/32, `n_heads` 2/4, `pos_enc` none/learned, epochs 1,000/500; `REP-C-t5000000` vs `REP-A07-350`: target 5,000,000/350,000, epochs 2,000/500 ✓ |
| `anchor_arms.json` vs STUDY 5d6c3c9 l. 184-190 | A = E (d24, 2 heads, no PE) at 350k; B = E at 250k; C = A07 at 5M; D = E + ours (β₂ 0.98, wd 0.01, clipvalue 1.0); F = E + learned PE; A07-350 = A07 at 350k ✓. R, H and NB are absent; no atlas cell uses them as a base |

## Re-review of v2 findings

- **A1-v2 (replicas not in atlas.json): RESOLVED.**
  - `atlas.json` carries `drift_replicas`, with the rule, the R4 branch, the seed rule (n_W3 ≤ n_W2) and one row per arm.
  - `gen_atlas.py` reads that key. `anchor_arms.json` no longer has `replicas_by_wave`, and its `_about` says so.
  - I regenerated the configs: 566 written, 0 refused. The replica tuples equal §5.2 (table above).
  - The v2 fix expected 8 refused. After the Bop γ/τ were set, it is 0, which the fixer notes.
- **B1-v2 (joint power): RESOLVED.** Gate (ii) is now mean Δ ≥ δ/2, and n is sized by k_joint.
  - I reran `screen_power.py`; every k_joint in the §5.1 table matches.
  - The fixer's claim that k_joint and k_t differ by at most 0.03 holds: the largest gap is 1.68 vs 1.65, unadjusted at n = 4.
  - Consequence to note: at α_eff the new gate (ii) almost never binds. The rule is effectively the BH t test alone. That is now stated at §5.1 ("a t test that rejects at α_eff almost always has a mean above δ/2").
- **B2-v2 (m by note substring): RESOLVED.**
  - `is_accuracy_cell` now counts by tier and `screen_role_350k`.
  - The m values match my hand count.
- **B3-v2 (probe roles): RESOLVED.**
  - M047, M048 and M049 carry the fourth role, and their base text says "feasibility probe on E".
  - The generator routes them to arm A: 12 probe cells.
- **B4-v2 (fallback controls): RESOLVED.**
  - §3.3 R2 "If arm A fails at 350k" covers the floor family (G2 only), M013 and FF2 (→ C at 5M).
  - R4 lists the survivors.
  - M013 `if_floor_fails` now reads "350k only: on arm A (E) by default; a feasibility probe on A07-350 … dropped under R4".
- **B5-v2 (n per wave): RESOLVED.** n_W3 ≤ n_W2 at the same target is in §5.1 item 2, in `screen_seed_rule` and in `drift_replicas.seeds`.

**[D21] consistency.**
- `grep` finds "Kai may override at K1" only in the header log line that records its removal (ATLAS.md:36).
- There is no "A07 arm A" and no "arm A (A07" anywhere in ATLAS.md, atlas.json, BRIEF.md or code/.
- Every unqualified "arm A" in ATLAS.md is E: l. 90, 122, 144, 459, 525, 547, 625 and 1155.
- All base texts resolve through `base_text_rules` with 0 mismatches. The strict generator would have stopped on an unmatched text.

**Non-degeneracy.** The rule matches the STUDY at 5d6c3c9 l. 386-404 clause by clause, and so does the "feasible, degenerate" handling. ATLAS.md §5.1 l. 653-673 carries:
- (a) traced EBOPs ≤ target;
- (b) EBOPs − the arm's traced 0-bit floor > 0;
- (c) validation accuracy > p_maj + 5·√(p_maj(1 − p_maj)/62,000).

The atlas adds three sound extensions:
- Z01 gates the untraced architectures at both targets.
- G1's collapse level is raised if (c) exceeds 0.25.
- p_maj is shared across cells. That holds: the pT gate acts on constituents, and n_val = 62,000 in every arm (STUDY l. 308).

**Bop.** M020 and M071 carry `bop_gamma` 1e-4 and `bop_tau` 1e-8, labelled "scan seed, not tuned for this setup (DR-22)". This agrees with DR-22 on every point:
- DR-22 l. 58-61: the Larq defaults `threshold=1e-8`, `gamma=1e-4` at commit 3d7de883…, `optimizers.py` l. 314-316.
- DR-22 l. 167-169: paper §5.2 and §5.3.
- DR-22 l. 178: "use 1e-8/1e-4 only as a scan seed".

## Category A

**A1-v3. No layer refuses a config whose treatment key the tree does not read. The CPU gate passes
Linformer, Deep Sets and Bop configs as the unmodified base model.**

Where:
- `patches/0001-atlas-keys-registry.patch`: `atlas_keys.validate` iterates `REGISTRY` only.
- `code/gate_cpu.py`.
- `code/gen_atlas.py`: the status `needs_patches`.
- `code/manifest_wave2.py` l. 11: "Only rows with a written config are packed".
- The ledger rows `attn-linformer`, `body-deepsets` and `bop-optimizer`.

Evidence. All runs are on my scratch build of `apply.sh` 0001-0021.
- `run_engram.validate_cfg` accepts a config with `train.totally_bogus_key` added (`bogus key ACCEPTED`). It also accepts M020, M006, M004, M024 and M011.
- `gate_cpu.py` on the patched tree:
  ```
  GATE_PASS atlas0926-standin-m020-t5000000-s1 params 12788 …
  GATE_PASS atlas0926-standin-m006-t350000-s1 params 12788 …
  GATE_PASS atlas0926-standin-m004-t350000-s1 params 12788 …
  GATE_ALL_PASS 3/3
  ```
  12,788 is the A07 transformer's parameter count (GATES.md l. 175). The "Deep Sets" config builds the transformer, the "Linformer" config builds full attention, and the "Bop" config trains with Adam.
- A key scan of all 566 generated configs finds keys that are neither in the base config nor in the patched `REGISTRY`:
  - `arch.attn_kind`: M004, M005, M053, M054, M056, M059, M060.
  - `arch.body` and `arch.deepsets_dims.*`: M006.
  - `train.binary_optimizer` and `train.bop_*`: M020, M071.
  - The blocked slugs' keys: `quant.softmax_table_min_bits` (M003, M051, M052, M054, M060), `quant.qk_min_bits` (M007, M055, M056, M059), `quant.ebops_group_weight` (M008, M057), `quant.pre_quant_shift` (M026, M066), `arch.mask_gated_keys` (M039, M076-M080), `arch.derived_features` (M040 and its 10 packages and FF1 cells), `data.std_scope` (M041, M079, M080), `quant.act_f0` (M012 and the FF2 cells), and the [A1] and [A2] schedule and optimizer names.
  - On this tree, each of these would train the base model under the entry's name.
- Two exceptions show the pattern can be fixed key by key:
  - `quant.act_granularity: element` (M011) fails loudly, because `qat.py:601` raises "Unsupported act_granularity".
  - `experiment.recovery_after_epochs` (M015) is a real bundle key (`ablation.py:425`).

Mitigations that exist, and why they are not enough:
- Every config is `launchable: False`, and `gate_eligible` is False for these rows.
- The ledger says "not wired (WIRING.md)".
- But `needs_patches` covers two cases: "runnable after `apply.sh`" (the 20 gated slugs) and "needs wiring outside the series" (Linformer, Deep Sets, Bop). For the second case, applying the series is not enough.
- The ledger rows for Deep Sets and Bop say "configs now written", and the wave-2 manifest template packs all 296 W2 rows.

Impact: this is the tautological-validation pattern. An entry run this way reads "flat against the base" because it is the base, and the screen then discards the method. The 0001 docstring claims "every atlas patch is opt-in behind a new config key". The first half holds (absent keys reproduce the bundle, 7/7). The converse, that a present key is honoured or refused, does not. This is the same class as A1-v2: the artifact that builds the runs differs from the design.

Fix. This is narrow and needs no redesign.
1. `atlas_keys.validate` refuses any key present in the config that is in neither the base schema nor `REGISTRY`. At a minimum, register `arch.body`, `arch.deepsets_dims`, `arch.attn_kind`, `arch.linformer_k`, `train.binary_optimizer`, `train.bop_gamma`, `train.bop_tau` and every blocked slug's key with a check that returns "not wired / blocked, see WIRING.md / BLOCKED.md". The wiring then replaces the check.
2. `gen_atlas.py` gets a status that separates `needs_patches` (in 0001-0021) from `needs_wiring` or `blocked`, and `manifest_wave2.py` packs neither.
3. Re-run `gate_cpu.py` on M004, M006 and M020 on the patched tree and expect three REFUSE lines. Re-run the invariance gate and expect 7/7 (the const0922 configs carry no such key).

## Category B

**B1-v3. The W2 and W3 drift replicas share run names, and the runner keys its run directory on the name.**
- Where:
  - `index.json`: 12 duplicate names, for example `atlas0926-standin-rep-c-t5000000-s2` in W2 and in W3.
  - The patched `run_study.py:97`: `out = ROOT / 'runs' / row['name']`.
  - l. 103-104: an assert on `source_manifest.json`.
  - l. 111-113: `ALREADY_VERIFIED` → return.
- Impact: the W3 replica lands in the W2 replica's directory under one output root.
  - At a new code sha it stops on the manifest assert.
  - At the same sha it restores the W2 run and returns.
  - Either way, the W3 drift measurement that §5.2 exists for is lost.
- Fix: put a wave token in replica names, for example `rep-w3-c-…`, and add a uniqueness assert over `name` in `gen_atlas.py`.

**B2-v3. Some hardware-risk labels are not carried per row in atlas.json.**
- Where: atlas.json `note`.
  - M024 carries "DSP audit before any hardware claim".
  - M025 (the all-layer pow2 gain) has an empty note, and so do the packages that contain `quant.channel_gain`: M065 and M066 (M067 and M080 carry the M040 label only).
  - ATLAS.md §5 item 5 (l. 957-961) names M024 and M025 but not the packages.
  - The FF2 cells that contain the tanh LUT (M097, M099, M101, M102) or `head_dims` (M098, M100, M101, M102) are not in the "no export path" list, which names M016 and M045. Their notes are empty.
- Impact: a wave STUDY that "copies its arms from atlas.json" does not inherit the "not a hardware candidate" flag for these cells.
- Fix: emit a per-entry `hardware_flags` field from the union of the component flags in `atlas_spec.py`. Combos inherit it.

The binary-thesis check itself passes:
- The only non-binary weight schemes (`ternary_absmean`, `int8_absmax`, `hgq_learnable`, `layer_weight_override`) appear only in the four `baseline`-tier entries, M047-M050. The int8 teacher of M063 is not deployed.
- `channel_gain` keeps two symmetric values per output channel, and its gate refuses a third value (ledger, `slug_results.json`).
- `beta_mode` (M022, M023) is one scalar per layer.

## Category C

- **C1.** `gen_atlas.py --help` still reads `"A07 ..." = arm A's architecture at the entry's own target`, which is pre-[D21] wording. The behaviour follows `anchor_arms.json` and is correct.
- **C2.** `base["1400000"]` carries M010's rung text in all 103 entries. It is harmless because only M010 has the target, but it is noise for a STUDY that copies it.
- **C3.** The E row of the §0 floor table (l. 90, l. 459) lists "also B, D, R", but not F. F = E + learned PE, and the STUDY says "F as traced at PREFLIGHT".
- **C4.** On the stand-in base, M038's `arch.pt_gate_gev: null` equals the base, so M038 and REP-A are the same config apart from labels. It is correctly `placeholder_pending_anchor`, and the null is written explicitly, so it will override the anchor's 2 GeV gate. Keep that assert when the anchor base lands.
- **C5.** Limitation, stated rather than faulted: the invariance gate and the E-shape sweep run on the bundle's old SAT quantizer, not [D19]. "gated-on-tarball" is the honest label, and it must stay until the rebase onto the anchor sha. BLOCKED.md records conflicts in 0012, 0013, 0014 and 0020 there.
- **C6.** Open from v2 and v1, and unchanged: C1, C3, C4, C6 and C7 (fixer v2 owner list), and C2/DR-09, which must close before FF2 is written.

## The competing-group question

A group running this queue next month would have a runtime guard that fails a run whose treatment
key nothing reads. Without it, a "flat" Linformer, Deep Sets or Bop screen cannot be told apart from
the base. That is A1-v3. Everything else a competitor would need is present: the replica controls in
the machine-readable spec, the power of the rule actually applied, and the fallback controls.

## Decision-label traceability

- [D21] and [D19] are applied as Kai confirmed them (decisions.md, 2026-09-27 08:40). [D11], [D13], [A6], [A17] and [A20] are used as in v2. [A1], [A2] and [A3] gate the placeholder rows.
- The anchor's non-degeneracy rule (arbiter v3 #1) is inherited verbatim.
- No broken [D] found.

## What must change before PASS

1. A1-v3: the registry refuses unread keys, and the index status separates `needs_wiring` and `blocked` from `needs_patches`. Then run `gate_cpu` on M004, M006 and M020 and expect REFUSE.
2. B1-v3 and B2-v3 can go in the same pass. None of this touches ATLAS.md's design or its numbers, except B2's labels.
