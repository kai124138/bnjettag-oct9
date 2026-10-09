# Pilot program R1 — build plan (ml-engineer, build half of PREFLIGHT), 2026-10-05

Written 10:14 JST as `plan.md`; the experiment-designer's STUDY plan replaced that file at 10:18, so
the build plan lives here. Governing: `docs/PILOT_PROGRAM.md`, decisions.md (Kai 2026-10-05 10:08),
`STUDY.md` (draft) §3-5, `PROGRAM.json` (draft) definitions, base tree
`campaigns/2026-10-02-chang-option-c/` (read only). Nothing here launches.

## Change units

No git repository at the lab root, so each code change is one patch file with a SHA-256 (made as
one commit in a scratch git repo over the tree), applied in order by `build_tree.py` on the
historical 42abed payload + 0032 + 0033 (byte copies, hashes asserted). The bundle SHA-256 is the
code identity in PREFLIGHT. 0036/0037 are taken by the parallel NB / attention-floor build (`dev/`),
so this build uses 0038/0039 and the R1 bundle is 42abed + 0032 + 0033 + 0034 + 0035 + 0038 + 0039.

| patch | content | manifest-hashed set (top-level *.py, bnhgq2/*.py)? |
| --- | --- | --- |
| 0034-test-run-pack-env | `tests/test_run_pack.py` setup(): `BNJ_CAMPAIGN_DIR=str(tmp)` | no |
| 0035-pilot-configs | `campaigns/pilot1005/`: generate.py, 19 configs, index, per-arm packs, floors copy, cpu_gate.py, monitor_p.py, certify/threshold copies; `tests/test_pilot1005.py` | no |
| 0038-pilot-stage | `bnhgq2/wandb_util.py`: stages `pilot-r1/2/3` (group suffix `-pilot-rN`); test | yes |
| 0039-readout-pilot | `campaigns/pilot1005/readout_pilot.py`; `tests/test_readout_pilot.py` | no |

0038 is needed because the W&B group must be `chang-n64-20261005-pilot-r1`: the group is
`experiment.group` + `STAGE_GROUP_SUFFIX[BNJ_STAGE]`, and an explicit group overrides `WANDB_GROUP`.

## Arms and H4 warmup

19 arms as STUDY §4 / PROGRAM.json r1_launch (ids A350-noC, A350-C, E250k-C … A07-5000k-C,
A350-C-w50, A350-C-w150). `train.ebops.pid.warmup` is hgq2 0.1.9 `BetaPID.warmup`, an integer
count of zero-based epochs: beta is held at `init_beta` for `epoch < warmup`, the integral is seeded at
`epoch == warmup`, feedback starts at the next step. Option (c) requires epoch `warmup − 1` traced,
so legal values are 1, 10, 20, …; 50 and 150 are legal (first feedback at epochs 60 and 160, span 10).

## Readout (readout_pilot.py) follows STUDY §5 and PROGRAM.json definitions

Inputs: run dirs (`activation_widths.jsonl`, snapshot `epoch-0500/state.json`, `latest.json`,
`nondegenerate_rule.json`, `DIVERGED.json`), a26 JSON (`analysis/attn_entropy.py`), certify JSON
(`certify_ebops.py --snapshot 500`), per-(c)-arm controller JSON (`monitor_p.py --json`). Stdlib only,
unit-tested on synthetic run dirs. Top level adds `threshold_c`, `labels_sha256` and `arms`, because
PROGRAM.json's integrity checks read the first two.

## Steps

1. 0034 + local reproduction with BNJ_CAMPAIGN_DIR exported (done 10:15).
2. 0035 generator + local cpu_gate (desktop CPU, not quotable).
3. 0038, 0039 + tests. 4. Full pytest with the gate's exports. 5. freeze_p.py, handoffs, lint.
6. PREFLIGHT.md.

## Tried and dropped

- Patch numbers 0036/0037 for stage/readout: collide with dev/ (NB, attention floor). Renumbered.
- `BNJ_STAGE=production` with group `chang-n64-20261005-pilot-r1` (no code change): rejected, it
  labels pilot runs as production in the run-id key.
- Fingerprint gate on a pilot1005 config: kept the reviewed `chang1002c-a-n64-s1` reference instead
  (same check as the option-(c) pilots; the integer depends on arch/quant/seed only).
