# Rename: method atlas → Delta (fixer, 2026-09-27)

Source: `.claude/memory/decisions.md` 2026-09-27 (Kai, direct). Design-side only. Nothing under `code/`
and nothing in `.claude/memory/` was edited. Nothing was committed or launched.

## Files (git mv)
- `ATLAS.md` → `DELTA.md`; `atlas_spec.py` → `delta_spec.py` (now writes `delta.json`); `atlas_tables.py` → `delta_tables.py`
- `review/ATLAS_{critical_v1..v4,fixer_v1,fixer_v2}.md` → `review/DELTA_*.md`, contents untouched
- `atlas.json` removed (`git rm`), and `delta.json` regenerated and added. The old sha256 was 8b1c3aa6…1265. The new sha256 is
  `f4ad2571667af56ccbd28e4271e315aad36d378575d83b9864ace979b8029204`

## Text
The program name was changed to "Delta" (the word) in DELTA.md, BRIEF.md, STUDY.md (`id: 2026-09-26-delta`, `type: delta`;
the question never contained "atlas" and is unchanged), `screen_power.py`, `delta_spec.py`, `delta_tables.py`, `research/*.md`
and `inventory/*.md`. There are 176 replacements. Articles were fixed where "the atlas <noun>" became "the Delta <noun>". I added a dated
"Rename" block at the top of DELTA.md's change log. `plan.md` and `LOG_LINES.md` got appended notes only, and their history lines stay as written.

## Statistic (meaning unchanged)
- Δ → g (with g_s, g_rep, g_package, g_components), δ → g₀, δ_res → g_res, δ_res,confirm → g_res,confirm (DELTA.md).
- ASCII in `delta_spec.py` / `delta.json` / `screen_power.py`: `delta` → `g_0`, `delta_res` → `g_res`. `g_0` was chosen so it cannot be
  read as gate G0.
- ΔR (angular distance, DELTA.md §9 P04 row, research cards) is not the statistic and is left as is.

## delta.json schema changes
- Top-level key `atlas_id` → `delta_id` (value `2026-09-26-method-atlas` → `2026-09-26-delta`). This is the only renamed key.
- No JSON key carried the gap statistic. The change is to the values only, in `screen_seed_rule.rule` and `screen_seed_rule.gate_ii`.
- Also changed in values: `drift_replicas.rule` ("DELTA.md §5.2 ... at the Delta code sha on Delta pods"), `drift_replicas.seeds`,
  `tier_legend.factorial-cell` (DELTA.md). `diff atlas.json delta.json` shows 6 changed lines, and all of them are the renamed strings.
- Unchanged: `config_delta`, `extra_delta` and `config_delta_semantics`, because they hold the config difference and not the gap. Config value `delta_r` is also unchanged.
- `atlas_study`: `delta_spec.py` emits no such block, so nothing was renamed.

## Constants (design text: DELTA.md frontmatter, conventions table row "W&B group named", DECISION block; STUDY.md)
`BNJetTag-MethodAtlas` → `BNJetTag-Delta`; `atlas-20260926-w2/w3/w4` → `delta-20260926-w2/w3/w4`. The prefix `atlas0926` → `delta0926`
appeared only in review history, so no design text changed for it.

## Forward pointers to code not yet renamed (ml-engineer)
- `delta_spec.py:665` comment names `delta_keys.register`. The code in `code/patches` still has `atlas_keys`.
- `inventory/code-surface.md:455` names `generate_delta.py`. The code still has `generate_atlas.py`.
- The same applies to every config, run name, W&B project/group and `index.json` under `code/`.

## Verification
- Before the edit, the spec regenerated the old `atlas.json` byte-identically.
- `python3 delta_spec.py <scratch>` was run twice. `delta.json` is byte-identical between the runs, stdout is identical, and it equals the committed `delta.json`.
- 103 entries, 103 unique IDs. Every `code_changes` slug is in `patches` and in DELTA.md §12. Every `combo_of` ID exists.
- `delta_tables.py` renders singles (52 lines), combos (55) and floors (27). Each table matches DELTA.md verbatim (lines 246, 366, 457 before
  the rename block was added).
- `screen_power.py .` exits 0. Its output matches the pre-rename output apart from the labels (delta → g_0, delta_res → g_res), and every number is identical.

## Residual `grep -rIil atlas campaigns/2026-09-26-delta --exclude-dir=code`
`review/DELTA_critical_v1..v4.md`, `review/DELTA_fixer_v1.md`, `review/DELTA_fixer_v2.md` (history), `LOG_LINES.md` (history
lines plus the appended note), `plan.md` (history lines plus the appended rename note). No design file remains in the list.
Lowercase "delta" is still used for the config difference ("config delta", "delta from the base arm", "attention-ablation delta").
M040's name "Derived features log pT and Delta R" names the physics ΔR, which is not the program.
