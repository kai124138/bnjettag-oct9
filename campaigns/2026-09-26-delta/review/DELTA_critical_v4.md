# ATLAS review, critical-reviewer, v4 (solo mode, re-review)

Reviewed 2026-09-27 10:25, at commit c3f8a31. Scope:
- `atlas.json`, sha256 6fbd4b5d8edadbca3817b8ef6a03dad1a714b0f6bc97b370429a6210da3c3711. I checked the hash.
- `atlas_spec.py` and `ATLAS.md` §6 lesson 5.
- In `code/`: the `README.md` ledger, `gen_atlas.py`, `classify_series.py`, `manifest_wave2.py`, `configs/index.json`, `gate_results.json`, `manifests/`, `patches/0001-0024`, `apply.sh`, `BLOCKED.md`, `WIRING.md`, `GATES.md` §4/§4b/§5, `PLAN_patches.md` (follow-up sections) and `tests_patches/`.
- `review/ATLAS_fixer_v2.md` "Follow-up v3" and the 2026-09-27 lines in `decisions.md`.

`plan.md` is dirty in the working tree; I did not review it. Everything below is a synthetic CPU check on the stand-in base, and nothing in it is a result.

**VERDICT: PASS.** A1-v3, B1-v3 and B2-v3 are resolved. I re-ran every check myself: 566 names are unique, the refusals match, the gates pass, and the invariance gate is 7/7. The earlier C items are also closed.

There is no new Category A. Three Category B items are open, all on the launch path, and none changes a config, a gate result or the design:
- the committed `index.json` cannot be reproduced;
- the manifest is keyed by run_id, which is not unique across waves;
- the Bop flip rule is not in the M020 row.

They must close before any wave-2 launch, and that launch needs the anchor base in any case. Nothing is launched and nothing has gone outward.

## What I recomputed

| check | result |
| --- | --- |
| `python3 atlas_spec.py <scratch>` | `cmp` against `atlas.json`: identical. 43 entries carry `hw_labels` |
| `python3 code/gen_atlas.py --out <scratch>` (strict) | W2 296, W3 268; `needs_patches 374, placeholder_pending_anchor 96, ready_on_base 96`; **566 written, 0 errors**. `diff -rq` against `code/configs/`: every config file is identical; only `index.json` differs (see B1-v4) |
| `code/apply.sh <scratch>` (full) and `apply.sh <scratch> 0022` | `APPLY_ALL_PASS` for both. 0001-0024 apply cleanly; 0003 sha256 2dfafdff…d1d8 |
| `classify_series.py --tree <scratch>/code` on my scratch index | `ready_on_base 96, refused_by_key 232, runnable_on_series 160, placeholder_pending_anchor 78`. This equals the committed `status_counts`, and every row's `status` equals the committed row. 11 refusing keys, each naming its slug |
| run-name uniqueness | 566 index names, 566 unique (566 lower-cased); 564 W2/W3 config `name` fields unique, plus 2 prereq. Replicas are wave-tagged, e.g. `atlas0926-standin-w3-rep-c-t5000000-s4`. B1-v3 is closed |
| strict keys, full tree | `train.invented_key`: refused, "no code path in this tree reads it". Typo `quant.beta_modee`: refused. `arch.pool='max'`: refused, because an inert key is pinned to the bundle value. M004: refused, `arch.attn_kind … attn-linformer (blocked on [A20])`. M038: refused, `arch.pt_gate_gev … anchor [A3]`. M001, M006, M018 and M020: accepted |
| strict keys, 0022 tree | M004, M006 (`arch.body … not wired in this tree`) and M020 (`train.binary_optimizer …`) are refused; M001 and M018 are accepted. `slug_tests.py --only strict-keys` passes on both trees |
| validator on the runner path | `run_study.py:95` calls `run_engram.validate_cfg(cfg)` before `out = ROOT/'runs'/row['name']` (l. 97), and `validate_cfg` calls `atlas_keys.validate`, then `strict_keys` (`run_engram.py:112`). The refusal fires at run time, not only in the gate |
| READ_KEYS sanity (0022 allow-list, 63 keys) | every leaf occurs as a string literal in some non-`atlas_keys` module of the patched tree. The check is coarse; it shows no key is listed with no read site at all |
| `gate_cpu.py` on M004/M006/M018/M020 (patched tree, pinned env) | `GATE_REFUSED …m004… arch.attn_kind is refused: attn-linformer (blocked on [A20]) …`; `GATE_PASS …m006… params 20742 … opt Adam`; `GATE_PASS …m018-t5000000-s1 params 12788 … max_abs 0`; `GATE_PASS …m020… params 12788 … opt BopAdam`. Equal to GATES.md §4/§4b |
| does the 0003 fix have a test that could fail? | I rebuilt 0001-0002 plus the **old** 0003 from 812b1eb (`wg + stop_gradient(q*beta - wg)`) and ran `slug_tests.py --only ste-variants`: `SLUG_TEST_FAIL ste-variants AssertionError: Binary gate failed`. On the fixed series: `SLUG_TEST_PASS`. The test has resolving power |
| invariance gate (full tree against the stored pristine fingerprint) | `SAME` on 7 of 7 (a00-n8, a01-n64, a07-n64, a08-n64, b02-n64, b04-n8, e03-n8); `INVARIANCE_GATE_PASS`; 60 s |
| slug tests re-run | ste-variants, strict-keys and body-deepsets: `SLUG_TESTS_ALL_PASS` |
| `gate_results.json` | 47 results: 36 pass, 11 needs_teacher, 0 fail, 0 refused. Equal to the ledger row and to GATES.md §4b |
| manifest `atlas_w2_packs.json` | 30 packs, 176 unique cells. Every cell is W2 with status `ready_on_base` or `runnable_on_series`. Packed cells that belong to a teacher-dependent entry (the 11 from `gate_results`): 0. Packed cells with `depends_on`: 0. The 188 eligible W2 cells = 176 packed + 12 in `after_teacher` (M027, M035, M036), with none missing. `unpacked`: 108 (80 refused_by_key, 28 placeholder). pack_meta horizons and arm counts match every pack. The Job has `completions` 30 and is marked TEMPLATE |
| hw_labels against the series' `export_ok=False` registrations | The runtime `REGISTRY` of the full tree has `quant.binary_center, beta_mode, channel_gain, weight, layer_weight_override, arch.head_dims, pre_block_act, arch.body, arch.deepsets_dims`. Every entry whose `config_delta` sets one of these carries a DR-17 label: 0 under-labelled. The extra labels are the non-series keys (Linformer/ReLU-N, key mask). The DSP label is on M024, M025, M065, M066, M067 and M080. B2-v3 is closed |
| 5M-on-C cells the gate never built (see C1-v4) | I gated M015, M016, M042, M043, M045, M047, M048, M049 and M050 at t5000000-s1 on the full tree: **9 of 9 GATE_PASS**, `max_abs 0`. Parameters: 12788, 13180, 5220, 14964, 15102, 12788, 12716, 35033, 12788 |

## v3 findings, by name

- **A1-v3 (unread keys silently ignored): RESOLVED.**
  - 0022 refuses by name any key that no code path reads. At 0022, M004, M006 and M020 are refused; on the full tree an invented key and M004 are refused.
  - 0023 and 0024 wire Deep Sets and Bop. The evidence is that M006 builds 20,742 parameters, not the A07 12,788, and M020 trains with `BopAdam`.
  - The index status now comes from the tree's own validator (`classify_series.py`), and the packer refuses an unclassified index (`manifest_wave2.py:81-82`).
- **B1-v3 (replica run-name collision): RESOLVED.** Names carry a wave token, and I found 566 of 566 unique. `index.json` records `run_names_unique: true`. A residual one layer up is B2-v4.
- **B2-v3 (per-row hardware labels): RESOLVED.** Details are in the table above. The wording on M006 is stale (C2-v4).
- **C1-v3 through C5-v3: closed or unchanged as stated.**
  - The `--help` text now carries the [D21] mapping.
  - `base["1400000"]` is on M010 only.
  - The §0 E row names F.
  - M038 writes an explicit `pt_gate_gev: null`.
  - The pre-[D19] quantizer in the gates is a stated limitation.

## Category A

Not applicable. There are no figures and no outward prose, and I found no new A.

## Category B

**B1-v4. The committed `configs/index.json` cannot be regenerated by the pipeline `WIRING.md` documents.**
- Where: `code/configs/index.json`, `runs[*]`.
  - `gate_v5` (566 rows) and `depends_on` (44 rows: 40 `teacher-fp32-a07`, 4 `teacher-int8-a07`) are written by no script in `code/`. A grep of `gen_atlas.py`, `classify_series.py`, `manifest_wave2.py` and `gate_cpu.py` finds neither field written into rows.
  - `patch_status` is stale for three slugs in 100 rows. The committed index has `attn-linformer: "written"`, `body-deepsets: "written"` and `bop-optimizer: "written"`. The current ledger gives `written; wiring blocked-on-[A20]`, `gated-on-tarball` and `gated-on-tarball`. The ledger was edited after the index was generated.
- Impact:
  - Today, no consumer reads these fields: the packer takes teacher dependency from `gate_results.json`.
  - A wave STUDY or PREFLIGHT that cites `index.json` cites a file that the documented pipeline (gen → apply → classify → gate → manifest) would not reproduce.
  - This is the one-table-updated, other-stale pattern.
- Fix:
  - Have one committed step write `gate_v5` and `depends_on` into the index. For example, `classify_series.py --gate gate_results.json`, or a small `annotate_index.py` listed in WIRING.md's pipeline row.
  - Regenerate after the ledger edit, so that gen → classify → annotate reproduces the committed index byte for byte.

**B2-v4. The manifest is keyed by `run_id`, and `run_id` is not unique across waves.**
- Where:
  - `manifest_wave2.py:74` (`packs.append([r['run_id'] …])`).
  - The `note` of `atlas_w2_packs.json`: "at freeze time these run_ids map to the shipped index.json row numbers".
  - `index.json`: 12 duplicate run_ids, `REP-{A,A07-350,C}-t…-s{1..4}`, one each in W2 and W3.
  - WIRING.md's last-but-one row records that `run_pack.py` reads row-number lists, not this dict. It also records that `run_pack.py` and `run_study.py` hard-code the constituent-study output root `/data/constituent-study-20260922/fp32`.
- Impact:
  - B1-v3's failure mode survives in the translation step. A freeze-time lookup of `REP-C-t5000000-s1` over all 566 rows is ambiguous.
  - The README ledger's generator row quotes "wave-2 Job 30 packs / 176 arms" without the WIRING caveat that the Job cannot consume these packs as written.
- Fix:
  - Key packs by `name`, which is unique. Alternatively, make `run_id` wave-tagged and assert it unique in `gen_atlas.py`.
  - Carry the WIRING gap (pack format and output root) in the ledger row and on the cluster-ops launch checklist.

**B3-v4. The Bop flip rule that defines M020 is recorded only in GATES.md §5 (FLAG FOR HUMAN: YES), not in the design row.**
- Where:
  - `GATES.md` §5: "Bop flip = reflect the latent about its mean (keeps |w - alpha| and so beta)". The alternative there is "latents set to ±1 (Bop as published …)", and the section says "it defines what M020 measures".
  - `atlas.json` M020 `note` and M071, and the `ATLAS.md:267` row, cite arXiv:1906.02107 and Larq for gamma and tau only. They say nothing about how a flip acts on a latent-plus-absmean binarizer.
- Impact:
  - I do not count this as a broken [D]. The design never specified the realization, and reflection is a defensible reading, since Bop's only action is a sign flip.
  - However, a wave STUDY that copies M020 from `atlas.json` inherits "Bop" without the choice. Any M020 result would then describe an optimizer that is not the published one, and a reader could not tell.
- Fix:
  - Put the flip rule, and the reason it preserves beta, in the M020 and M071 `note` in `atlas_spec.py` and in the ATLAS.md row.
  - Get Kai's answer on the FLAG before M020 is packed. M020 is in W2 and is currently packed.

## Category C

- **C1-v4. The gate covers one base arm per entry.**
  - `gate_cpu.py --one-per-entry` gates seed 1 at the first target only.
  - For 9 entries (M015, M016, M042, M043, M045, M047, M048, M049, M050), that first cell is on arm A (E: d24, 2 heads, no PE). Their packed 5M cells are on C (A07: d32, 4 heads, learned PE): 36 packed cells on an architecture the recorded gate never built.
  - I closed it for now: 9 of 9 GATE_PASS (table above).
  - Make the harness gate one config per (entry, base_arm) so the record covers it (about 5 s each).
- **C2-v4. Stale "not in the patch series" wording for Deep Sets.**
  - Where: M006's `hw_labels`, the "not in the patch series" branch of `atlas_spec.py:667-678` (`NO_EXPORT_OTHER` has `arch.body`), and `ATLAS.md:969-971`.
  - 0023 is now in the series and registers `arch.body` and `arch.deepsets_dims` with `export_ok=False`.
  - The label is still true (there is no export), but it belongs in the "refused by the patch series' export guard" bucket.
- **C3-v4. `BLOCKED.md:5` numbering is stale.** It says the blocked slugs land "as patches 0022+". Numbers 0022-0024 are now taken (strict-keys, body-deepsets, bop-optimizer), so the blocked slugs are 0025+.
- **C4-v4 (carried).** GATES.md §5 has two more open items marked FLAG FOR HUMAN: the null clipvalue/weight_decay admission and the teacher "beta bounds at their minimum" reading. The order_seed item is flagged too, but its confidence is HIGH. They are not new, and they belong on Kai's list with B3-v4.

## Decision-label traceability

- [D21] base-arm mapping: unchanged. The 9 gated A-arm cells and the C cells match `anchor_arms.json`.
- [A1], [A3] and [A20]: refusals name the right blocking label (the `classify_series` output above).
- No `[D]` is broken. The Bop realization (B3-v4) is an undocumented choice where no [D] exists, not a replaced one.

## The competing-group question

A group running this queue next month would have three things we do not.

- A manifest they could launch as written. Ours still needs the run_id → row translation and an output-root patch (B2-v4, WIRING.md).
- A stated Bop variant (B3-v4).
- A gate record per architecture, not per entry (C1-v4).

Each of these is fixable in text or in a few minutes of CPU. None of them undermines the design as a pre-registered queue.

## What must change before launch (not before PASS)

1. B1-v4: a committed annotate step that makes `index.json` reproducible, and a regeneration after the ledger edit.
2. B2-v4: packs keyed by `name`, and the WIRING gap recorded in the ledger row.
3. B3-v4: the Bop flip rule in the M020 and M071 rows, and Kai's answer on the GATES §5 flag.
