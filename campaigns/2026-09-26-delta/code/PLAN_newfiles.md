# PLAN_newfiles.md — ml-engineer (new files only), method atlas, 2026-09-27

Crash-resilient notebook for the new-files half of `code/`. The other ml-engineer owns
`code/patches/` (patches to existing bundle files). Nothing here is a result; no AUC or
accuracy is quoted. No commit, push, launch, or cluster contact.

## Inputs read

BRIEF.md (with the anchor amendment [D19]), ATLAS.md §1, §3.4, §5, §12, atlas.json (103
entries, 38 slugs; the interface), inventory/code-surface.md, the screen bundle extracted to
the scratchpad (`atlas-newfiles/bundle/code`, tarball sha256 26f3cc40...5a45, verified with
`shasum -a 256` before extraction), cards B10 (Bop) and A09/A10 (Deep Sets, Linformer),
`reference-code/HGQ2-examples/jsc150/model.py:77-104` at 6cdc6e34 (topology read for dims
only; no LICENSE, nothing lifted), `nrp-lab/nrp_doctor.py` lint rules,
`campaigns/2026-09-22-constituent-screen/{freeze_jobs.py,screen-job.json,canary_packs.json}`.

## Facts found during orientation (primary evidence)

- `campaigns/2026-09-26-training-batch/code/tree` is byte-identical to the screen bundle
  (`diff -rq -x __pycache__` prints nothing, 2026-09-27). `grep -rl act_overflow` over the
  Desktop tree and the scratchpad finds nothing. The coordinator reports the anchor patch
  series as staged there; it is **not present on disk at generation time**. The generator
  therefore runs on the stand-in base `const0922-a07-n64-s1-fast50-fp32.json`, labelled in
  every output.
- Announced anchor keys (coordinator, 2026-09-27; decisions.md "chang0926 code"):
  `quant.act_overflow`, `quant.softmax_quant`, `arch.pt_gate_gev`, `train.validation_split`,
  `experiment.cost_before_auc`, `arch.pos_enc_none_consume_rng`. Only `arch.pt_gate_gev`
  matches an atlas placeholder name. `quant.act_f0`, `train.lr_cycle_epochs`,
  `train.optimizer`, and `train.lr` read as the cosine peak have no announced counterpart
  and stay placeholders with status `pending-anchor-PASS`.
- [D9] says `order_seed = f(s)`, but the anchor STUDY never defines f. Not invented:
  the base value is inherited and every config is flagged `order_seed_pending_D9`.
- `nrp_doctor.py lint` calls `kubectl get nodes` (cmd_lint -> gpu_resource_map). To lint
  without contacting the cluster, the manifest is JSON (no kubectl parse) and lint runs with
  `KUBECONFIG` pointing at a nonexistent file, so the resource-name check is disabled and
  says so.

## What gets built (in this order)

1. `gen_atlas.py` + `key_registry.json`: atlas.json + base -> `configs/<wave>/<id>-t<target>-s<seed>.json`,
   `configs/index.json`. Per run: target -> `train.ebops.pid.target_ebops`, seed ->
   `experiment.seed`, H -> `train.epochs`, `=horizon` substituted, unique `name` /
   `experiment.arm`, group `atlas-<wave>-screen`, provenance block `atlas_study` (enters
   `digest_json(cfg)`). Drift replicas (ATLAS §5.2) as typed rows; teachers P-T1/P-T2 under
   `configs/prereq/` flagged blocked. Confirm tier behind `--tier confirm`.
   Hard failures: unknown key not registered by one of the entry's own slugs and not an
   anchor placeholder. Refusals (no config written, index row `refused_unfilled`): null or
   placeholder-string values, except whitelisted Keras-default nulls.
2. `manifest_wave2.py` -> `manifests/wave2-screen-job.json`, `manifests/wave2-packs.json`:
   K=6 per pod, packed per horizon, cpu 12 / 36Gi, label `bnjettag.io/arms-per-pod: "6"`;
   ConfigMap name, bundle sha and activeDeadlineSeconds left as marked placeholders.
   Lint offline, output pasted in GATES.md.
3. Modules under `code/newmods/` (importable as `newmods.*` with the bundle on PYTHONPATH):
   `deepsets.py`, `bop.py`, `linformer.py`, `diag_attention.py`, `diag_input_proj_rows.py`,
   `diag_latent_binary_gap.py`; tests under `code/tests/` (synthetic, CPU, a few steps).
4. `gate_cpu.py`: build via `ablation.matching_initialization`, one `make_epoch_step`
   step, save, reload, logits within 1e-7 and EBOPs equal, timed. Run on the stand-in,
   the replicas and the 11 T0 entries (one config each).
5. `WIRING.md`, ledger rows in `README.md`, `GATES.md`.

## Decisions

```
DECISION: whitelist null for train.clipvalue and train.weight_decay (Keras-default "off", code-surface §3 row 1); every other null refused.
ALTERNATIVES: refuse all nulls (would refuse M033, M069, M070, M074 whose nulls are meaningful)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES (the S runner passes None straight to Adam; unverified by running)
```
Superseded (2026-09-27 ~01:30): the replica and arm-E decisions first written here were replaced by
`anchor_arms.json` (`arms`, `base_text_rules`, `replicas_by_wave` copied from ATLAS.md §5.2) after the
fixer regenerated atlas.json. The current decision blocks are in GATES.md §5.

```
DECISION: order_seed inherited from the base (20260912 on the stand-in), flagged per config.
ALTERNATIVES: invent f(s) (refused: anti-fabrication)
CONFIDENCE: HIGH   FLAG FOR HUMAN: YES ([D9] needs f defined by the anchor)
```

## Tried and failed (append as it happens)

- Env without hls4ml: `bnhgq2/subln.py` imports hls4ml at module load; added hls4ml==1.3.0 and wandb==0.28.0 (both in the bundle's requirements) to the uv run.
- BopAdam v1 kept the Bop variables in a Python list attribute: Keras auto-tracked them and they leaked into `optimizer.variables` (91 vs Adam's 82), which would have written model weights into optimizer.npz and broken restore-by-index. Fixed: only string keys are stored.
- Generator v1 parsed the base arm from the first letter of `entry.base[target]`; the fixer's regenerated atlas.json (01:28) uses free text ("own A07-derived architecture: ...", "E by default ..."). Replaced by `base_text_rules` in anchor_arms.json (first match wins; unmatched text is an error).
- Offline lint: `nrp_doctor.py lint` still runs the resource-name check with an empty node map and prints an ERROR; recorded in GATES.md, not worked around.

## Status 2026-09-27 ~01:40

Done: gen_atlas.py (+ key_registry.json, anchor_arms.json), 538 configs + index.json, manifest_wave2.py
(48 packs, K=6), offline lint pasted, six modules in newmods/ with 13 CPU tests passing, gate_cpu.py
15/15, WIRING.md, README.md ledger (created; my rows filled, patches rows left to their owner), GATES.md.

## Log lines to append

- decisions.md: 2026-09-27 (ml-engineer, method atlas, staged, not launched). Bop re-implementation (`code/newmods/bop.py`): a flip reflects the latent about its mean, keeping |w - alpha| and so beta; Bop variables get no weight decay and ignore the LR; the EMA lives in Adam's momentum slot, so optimizer checkpoints keep Adam's layout. This defines what M020/M071 measure. **Check:** `pytest code/tests/test_bop.py` (exact flip rule, variable count equals Adam's).
- decisions.md: 2026-09-27 (ml-engineer, method atlas). Deep Sets body (`code/newmods/deepsets.py`): Sun et al. get_gnn dims re-implemented, norm-free (no fused BN), binary absmean weights, the anchor's activation quantizers, float biases, power-of-two pooling scales. Unpaired against the transformer. **Check:** `pytest code/tests/test_deepsets.py` (binary gate, permutation invariance).
- decisions.md (finding, suggest /log-decision): 2026-09-27. atlas.json M074 and M103 set `train.optimizer` without `A2` in `anchor_patches_required`; gen_atlas.py refuses them. **Check:** `python3 code/gen_atlas.py` exits 2 until fixed.
- decisions.md (finding): 2026-09-27. `nrp_doctor.py lint` without cluster access reports "NO product in the required list is reachable" (ERROR) because the resource-name check runs against an empty node map after printing that it is disabled. **Check:** `KUBECONFIG=/nonexistent python3 nrp-lab/nrp_doctor.py lint <job.json>`.
- experiment-log.md: none (no run, no result).

## 2026-09-27 (afternoon) — rename, real base, launch gaps, packing (orchestrator brief)

Plan (written before the edits; each step checked on disk):
1. Rename every atlas name in the new files (`generate_delta.py`, `delta.json`, `delta_study`, `delta_keys`,
   `delta_optimizer_for`, `BNJetTag-Delta`, `delta-20260926-w2/w3`, `delta0926`, `kai-delta0926-*`); make
   `gate_cpu.py` require `delta_optimizer_for` and `set_delta_epoch`.
2. Base = the anchor's own per-seed arm configs from bundle 77f1ca4e (A, A07-350, C); stand-in only for
   `configs-standin/` (tarball tests).
3. Launch gaps as `patches/0025` and `patches-anchor/0038` (run names, dict packs, roots), with tests.
4. K per architecture and GPU class from the anchor's measured memory, plus a canary manifest.
5. Regenerate, trace floors, classify, gate, annotate, pack, lint; update README rows, GATES.md §6, WIRING.md.

Inputs read (beyond the morning list): `code/PLAN_rebase.md`, `code/patches*/`, `apply_anchor.sh`;
`campaigns/2026-09-26-training-batch/{PREFLIGHT.md, RUN.md}` (read only); the anchor bundle's
`campaigns/chang0926/{generate.py, trace_floors.py, cpu_gate.py, configs/}`, `static_floor.py`, `run_pack.py`,
`run_study.py`, `run_engram.py`; `campaigns/2026-09-27-delta-screen/STUDY.md` (Arms, Drift replicas,
launch gate, Arms per pod, [DK11]); `nrp-lab/nrp_doctor.py` rule PACK.

```
DECISION: zero_floor_ebops re-traced per arch/quant signature (anchor static_floor, CPU) for every cell whose arch or quant section differs from its arm; untraceable cells flagged floor_untraced and not packed.
ALTERNATIVES: inherit the arm's floor (wrong: M001's own floor is 171,526, not A07's 343,053, so feasible checkpoints would read as degenerate); take delta.json floor_derived (delta.json says derived is never a floor)
CONFIDENCE: HIGH   FLAG FOR HUMAN: YES (changes what "non-degenerate" means per cell; decisions.md line below)
```
```
DECISION: the gated-key-mask cells are traced with arch.mask_gated_keys removed (the mask is unbilled in 0036; EBOPs are priced from widths).
ALTERNATIVES: leave them untraced (drops M039/M076-M080 from the packs); trace through builder_for with a synthetic input_std
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
```
```
DECISION: a cell's cache = anchor_arms.json cache.identity_keys (the load_cache checks); equal to arm A's -> the anchor cache /data/chang-n64-20260926, else /data/delta-20260927/caches/<key8>, flagged cache_not_built and not packed until built (STUDY Z10, split_seed 1).
ALTERNATIVES: one shared Delta cache root (cannot hold two pt-gate settings for n64)
CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```
```
DECISION: K per (architecture class, GPU class): canary k_result.json if present; else floor(0.9 x card / measured per-process MiB) (E on A10: 4); else the STUDY planning value (A07 on 24 GB: 3); other architecture classes inherit their base class's K, flagged k_class_unmeasured. Manifests are labelled PLANNING until the canary runs.
ALTERNATIVES: use the C' proxy 5,172 MiB for A07 (gives 4; it is the old quantizer); a constant K
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: YES (the canary decides; [DK11])
```
```
DECISION: wave 2 is split into two Jobs: t0 (replicas, teachers) and cells (released at the replica epoch-500 gate), plus a one-pod canary; placebo no-op is delta_study.placebo (provenance, accepted by the strict validator, part of the run identity).
ALTERNATIVES: one Job with ordered indices (cells would start before the replica gate)
CONFIDENCE: HIGH   FLAG FOR HUMAN: NO
```
```
DECISION: generate against 77f1ca4e (brief), read from the ConfigMap payload when the tarball has moved; --anchor-bundle/--anchor-sha for the regime-B rebase; the base config's train.ebops_trace_every is carried, never set by a delta.
ALTERNATIVES: generate against the uncommitted e90327d4 bundle now (not gated by the series; not what the brief names)
CONFIDENCE: HIGH   FLAG FOR HUMAN: YES (rebase required before launch)
```

Tried and failed:
- The first floor trace refused the gated-key-mask configs (`needs the cache input_std`); these are now traced with the mask removed.
- The first run of the tarball `run_pack` test failed because the laptop has no `nvidia-smi`. The test now puts a fake one on PATH.
- The `apply_anchor.sh` default path failed its sha check because the anchor tarball was re-frozen at
  15:07. The 77f1ca4e copy was recovered from git and used through `ANCHOR_BUNDLE`.
- An unquoted heredoc broke the first GATES.md append, and nothing was written. It was redone from a
  file.

Status at 2026-09-27 ~16:00:
- Done: the rename, the anchor base, `floors_delta.json`, classification, the gate, the packs (t0,
  cells), the canary, 0025 and 0038, the offline lint, WIRING.md, the README rows and GATES.md §6.
- Open:
  - the regime-B rebase;
  - the [A20] guard that blocks the weight baselines and teachers (patches owner);
  - the Z10 caches;
  - memory canaries for classes other than E and A07;
  - the diagnostics-on invariance check (STUDY launch gate 8);
  - `slug_tests.delta_cfg` must be repointed to `configs-standin/`.

## Log lines to append (2026-09-27 afternoon)

- decisions.md: 2026-09-27 (ml-engineer, Delta, staged, not launched). Delta configs are now the anchor's
  own per-seed arm configs (bundle 77f1ca4e: A, A07-350, C). `experiment.nondegenerate.zero_floor_ebops`
  is re-traced per arch/quant signature with the anchor's `static_floor.floors`, so 38 (entry, arm)
  pairs carry their own floor. Examples: M001 171,526 instead of 343,053; M002 85,763; M005 and M059
  0; M044 686,106. Cells that cannot be traced are not packed. This changes which checkpoints count as
  non-degenerate in those cells. **Check:** `code/floors_delta.json` self_check (A 171,526, A07-350
  343,053) and the per-row `floor` in `code/configs/index.json`.
- decisions.md: 2026-09-27 (ml-engineer, Delta). `run_pack.py` accepts run names and dict-form packs
  with `run_root` / `data_root`. This is `patches/0025` (tarball, which also ports the anchor's BNJ_*
  roots) and `patches-anchor/0038`. A legacy list of row numbers behaves as before.
  **Check:** `tests/test_run_pack_delta.py` 6/6 on both trees; tarball invariance 7/7.
- decisions.md (finding, suggest /log-decision): 2026-09-27. On the anchor tree 77f1ca4e the [A20]
  guard (`qat.py:667-669`) refuses Chang quantizers with non-binary weights. So M047, M048, M049 and
  the teachers P-T1 and P-T2 do not build. Without the teachers, M027, M035, M036 and W3's KD cells
  cannot run. **Check:** `gate_cpu.py` GATE_FAIL lines in GATES.md §6.
- decisions.md (finding): 2026-09-27. The training-batch campaign re-froze `chang0926-code.tar.gz` to
  e90327d4 (regime B). The file is uncommitted, and `apply_anchor.sh`'s default now fails its sha
  check. Delta must be rebased onto the regime-B bundle before launch. **Check:**
  `shasum -a 256 campaigns/2026-09-26-training-batch/manifests/chang0926-code.tar.gz`.
- experiment-log.md: none (no run, no result).

## 2026-09-28 — rebase to 42abed4b, frozen wave-2 lists, RSS gate per horizon, canary (orchestrator brief)

Plan:
1. Point `anchor_arms.json` at 42abed4b.
2. Replace the pending amendments with the frozen STUDY (24c3c90) lists.
3. Re-trace the floors, regenerate, classify, gate, annotate.
4. Set the per-pack RSS limit from the horizon.
5. Rewrite the canary as E K=4, E K=5, A07 K=3 at 110 epochs.
6. Rebuild the packs, lint, and update the docs.

All six steps are done; the record is GATES.md §7.

```
DECISION: BNJ_RSS_GATE_LIMIT_MB per pack = 2,100 + 5 x H MiB (4,600 / 7,100 / 9,600 / 12,100); pod memory per arm max(6, ceil(limit/1024)) Gi.
ALTERNATIVES: the anchor's single 6,144 MiB (admits 8 MB/epoch at H 500, fails 2 MB/epoch at H 2,000); 6,144 floored per horizon
CONFIDENCE: HIGH (it is the frozen STUDY's PACK-MEM line; the gate becomes gate 14's 5 MB/epoch bound at every H)   FLAG FOR HUMAN: NO
```
```
DECISION: canary E-k5 runs with BNJ_STAGE=pilot so its W&B run ids differ from E-k4's (same rep-A names, stage set is closed); group suffix -canary for both.
ALTERNATIVES: disjoint seeds (not enough E H-1,000 configs for 4 + 5); W&B off (the runner refuses WANDB_MODE != online)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
```
```
DECISION: one memory size per Job (the largest pack: 36 Gi for 3 x 12 Gi A07 H-2,000 arms), not one Job per memory tier.
ALTERNATIVES: separate cells-h500 / cells-long Jobs (splits the 7-pod budget by hand)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
```

Tried and failed:
- The canary builder's first version picked up the W3 replicas as well, and its horizon assert
  caught it. It now filters to wave W2.

## Log lines to append (2026-09-28)

- decisions.md: 2026-09-28 (ml-engineer, Delta, staged, not launched). Delta configs are regenerated
  on the leak-fixed regime-B anchor bundle 42abed4b. All 582 configs carry
  `train.ebops_trace_every 10` from their base. The validator accepts 582/582. Gate: 119 PASS,
  15 NEEDS_TEACHER, 8 FAIL, the last on the [A20] non-binary guard. The wave-2 lists follow the
  frozen STUDY 24c3c90. **Check:** GATES.md §7; `configs/index.json` sha256 f7b6e5b9…9288.
- decisions.md: 2026-09-28 (ml-engineer, Delta). The RSS gate limit is now set per pack from the
  horizon: `BNJ_RSS_GATE_LIMIT_MB = 2,100 + 5 x H` MiB, following the frozen STUDY's PACK-MEM line.
  Pod memory per arm is max(6, ceil(limit/1024)) Gi. The result is that at every horizon the gate
  fails arms steeper than about 5 MB/epoch. **Check:** the `rss_gate_limit_mb` fields in
  `manifests/delta_w2_*_packs.json`; header line `RSS_GATE_LIMIT_MB`.
- decisions.md (finding): 2026-09-28. STUDY gate 14 names `BNJ_RSS_GATE_MB_PER_EPOCH`, but the anchor
  code reads only `BNJ_RSS_GATE_LIMIT_MB` / `BNJ_RSS_GATE_WINDOW`. **Check:**
  `grep -rn BNJ_RSS_GATE <anchor tree>/code`.
- experiment-log.md: none (no run, no result).

## 2026-09-28 (later) — PREFLIGHT items: extension replica seeds, newmods shadowing

- **Replica seeds above n.** Seeds above n now get `train.epochs` = 500 in their configs. Launching
  with a per-arm stop is not possible: the runner has no per-arm stop key, and a pod-wide
  `--stop-after` is excluded. t0 is repacked with one horizon and one family per pack.
- **newmods shadowing.** `gate_cpu.py` and `trace_floors_delta.py` now drop their own directory from
  `sys.path` and assert that modules come from the tree. M006 was re-gated (20,750 params). Its floor
  is traced through the builder: 0.
- Record: GATES.md §7.1.

```
DECISION: extension replica seeds (rep-A s5-8, rep-C s5-8) carry train.epochs 500.
ALTERNATIVES: per-arm stop key (none exists in the runner); pod-wide --stop-after (excluded by the brief)
CONFIDENCE: HIGH   FLAG FOR HUMAN: YES (if the seed rule raises n these seeds restart at the long horizon)
```
```
DECISION: non-transformer bodies' zero floor = static_floor.set_floor on the runner's builder_for build; validated by equal floors on A and A07-350 through both paths.
ALTERNATIVES: leave M006 floor_untraced (unpacked)
CONFIDENCE: MEDIUM   FLAG FOR HUMAN: NO
```

### Log lines to append (2026-09-28, later)

- decisions.md (finding): 2026-09-28. `gate_cpu.py` run from `campaigns/2026-09-26-delta/code/`
  imported that directory's unpatched `newmods/deepsets.py` instead of the tree's. Fixed by removing
  the script's own directory from `sys.path` and asserting the module origin. M006 is 20,750 params,
  not 20,742, and its zero floor is 0. **Check:** GATES.md §7.1.
- decisions.md: 2026-09-28 (ml-engineer, Delta). Replica seeds above n = 4 are configured to 500
  epochs, following the frozen STUDY. If n rises they restart at the long horizon. **Check:**
  `extension_seed_stops_at_500` rows in `configs/index.json`.
