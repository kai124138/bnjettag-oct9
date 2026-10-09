Verdict: PASS for the R1 launch on bundle 98dd2875. One A finding: the controller-error field of `readout_diag.json` is empty for every option-(c) arm. Fixing it needs only a re-prepared readout handoff (no bundle change, no CPU gate) or a VERIFY-time recompute. No new code bundle is warranted.

# STUDY constructive review v2: pilot program, 2026-10-05

Reviewer: constructive-reviewer, panel iteration 2 (06-review §6.2). Written 2026-10-06. Read-only
except for this file.

**Inputs**
- `review/STUDY_constructive_v1.md` and `review/STUDY_arbiter_v1.md`.
- `STUDY.md`, sha256 `95c9b61f…7294`.
- `PROGRAM.json`, sha256 `cca098b1…1dee` (unsigned).
- `PREFLIGHT.md` §3b, `JOURNAL.md`.
- `PREPARED.json`, with bundle `98dd2875b7c9…0059` and status `offline_prepared_not_submitted`.
- `manifests-98dd28/readout-job.json` (job `kai-pilot1005-r1ro-98dd28`, handoff `rh-deccad51…`).
- The frozen tree `code/tree/` (`bnhgq2/ablation.py`, `bnhgq2/ebops_target.py`, `bnhgq2/qat.py`,
  `analysis/attn_entropy.py`, `campaigns/pilot1005/{index.json,configs/}`).
- HGQ2 0.1.9 (`requirements-training.txt:4`, the local venv source).
- `evidence/fixes-v1/readout_diag_harness.{py,log}` and the readout dry-run logs.

No number below is a result. The counts are code facts, computed by running the frozen tree's own
`is_traced_epoch` and `pid_step_epochs` on the frozen configs. The other numbers are quoted with
their file:line.

## 1. Adopted items: are they in the frozen bundle as intended?

| v1 item (arbiter fix) | intended | in 98dd28 | status |
| --- | --- | --- | --- |
| B1 → qkv1-450k (F2 i) | E, 450k, (c), w1, s1 | `configs/pilot1005-h3-e-450k-c-qkv1-s1.json`: budget 450,000, warmup 1, pid_input traced_only, variant qkv1. It is index row 22 and readout `--indices 22`. `f2_config_diff.log`: it differs from qkv1@350k only in budget and identity | **as intended** |
| A4 → E-unc-C (F2 ii) | E, (c), w1, no binding budget | `pilot1005-ctl-e-unc-c-s1.json`: target 100,000,000, warmup 1, (c). It is index row 23 and part of the STUDY §6 positive-control stop (STUDY.md:208-210, :293) | **as intended** |
| B3 → w100 (F2 iii, K1) | w150 → w100 | rows 16-17 have warmup 100. No w150 config remains | **as intended** |
| A3 → a26 on `model_unconstrained.keras` (F5) | every E row + A07-5M | The readout manifest runs `attn_entropy.py --indices i --checkpoint …/snapshots/epoch-0500/model_unconstrained.keras` for rows 0-9, 13 (A07-5M) and 14-23. It skips A07-500k/1M/2M (rows 10-12). The index order matches the `--indices` values. The checkpoint is the highest val-AUC **traced** epoch (`ablation.py:1053-1055`), and it is in `SELECTED_FILES` (`ablation.py:32`), so every snapshot carries it. `best_auc_point` (epoch and AUC) is recorded beside it, which is needed to read it. a26 uses the full validation split (`attn_entropy.py:233`, `n_val` default all) | **as intended** |
| A2 items 1-4, 6 → `readout_diag.json` (F5) | t_uniform (Q **or** K), t_budget, site order, cost split, NB width | See §2. Items 1-4 and 6 are correct by code reading. The file is written after `readout.json` and is excluded from the Job exit status (`READOUT_DIAG_DONE … not part of the Job exit status`). It is flagged `descriptive_only: true` and `rule_input: false` | **as intended** |
| A2 item 5 → controller error | median and max over post-feedback epochs, noC vs C | Empty for every (c) arm. See A1 | **not as intended** |
| B4 → A07-5M positive control | stop if unhealthy | STUDY.md:123, :208-210; stop rule 3 at :293 | **as intended** |

## 2. Code facts behind the "as intended" rows

- **t_uniform's 0-bit test is sound.**
  - `width_snapshot` logs `bits = q.fbits` (`ebops_target.py:56`). In HGQ2 0.1.9, KIF `b = relu(i + f)`
    (`fixed_point_quantizer.py:436-437`) and WRAP `fbits = b + k·[b > 0]` (`:100-103`). So
    `fbits == 0` exactly when the channel outputs 0. The diag's `float(x) == 0.0` test is the
    right test.
  - The site keys `bit_block_<n>_attn_scores__in0/__in1` match `activation_quantizers`
    (`ebops_target.py:29`) and `ATTN_WIDTHS` (`ablation.py:646`).
  - The diag takes Q **or** K per block (`all(any(v) for v in blocks.values())`). That is the v1
    definition, not the stricter `attn_qk_all_zero` flag.
- **qkv1 arms cannot show a t_uniform.** `FlooredKIF.f` is `max(f, m − i)` (`qat.py:378-379`), so
  `b ≥ 1` and t_uniform is `None` by construction. The H3 mechanism read for qkv1 therefore rests
  on `site_order` and `cost_split`. This is correct, and the STUDY could say it in one line (C1).
- **The `last` a26 checkpoint exists.** A pause saves a checkpoint (`ablation.py:1197-1198`,
  `save_checkpoint` → `checkpoints/epoch-0500/model.keras`, `:242-261`). The readout's
  `checkpoints/epoch-0500/model.keras` path therefore exists for a paused arm.

## Grade A

### A1. The controller-error field (diag item 5) is empty for all 22 option-(c) arms

**What is wrong.** The diag filters `ebops_in_training_over_traced` to records with
`pid_stepped == 1`. Under option (c), a stepped epoch e ≥ warmup is one whose epoch e − 1 was traced
(`ablation.py:577-578`). Traced epochs are 0, 9, 19, … (`:522`). Every post-warmup stepped epoch
(10, 20, 30, …) is therefore untraced, and the ratio there is `None` (`:1139`). noC configs log no
`pid_stepped`, so the diag's default of 1 keeps all their traced epochs.

Counts, from the frozen functions run on the frozen configs over epochs 0-499:

| config | records used | of which post-warmup |
| --- | --- | --- |
| A350-C (w1) | 1 (epoch 0) | 0 |
| w50 | 6 | 0 |
| w100 | 11 | 0 |
| A350-noC | 51 | 50 |

So the field compares noC's whole trajectory against C's warmup only. That is exactly the
asymmetry that would mislead the H1 mechanistic read.

**Why the checks passed.**
- The crafted harness put `stepped=1` on a traced post-warmup record (`readout_diag_harness.py:24-29`).
  The real runner never produces that pattern.
- The final dry run printed `n: 0` for every fixture arm (e.g. E500k-C and qkv1-450k) without
  failing.

**Fix (pick one; neither touches the bundle, the GPU handoffs or the CPU gate).**
- (a) **Recommended.** In `freeze_p.py`'s `--diag` heredoc, replace the filter with "traced epoch
  (`ratio is not None`) and `epoch >= warmup` from the row's config", applied the same way to noC
  and C. Then re-prepare **only** the readout handoff (`--only readout`) and add one crafted-harness
  case built from the real stepped/traced pattern.
  - Cost: about 0.5 agent-h.
  - It needs no PROGRAM.json change, because `r1_readout.handoffs` is still
    `PLACEHOLDER:rh-R1-readout` (PROGRAM.json:632). Only the readout ID that fills the placeholder
    changes.
  - The readout runs after R1, so this can land before signature, or during R1 under §3 "ask
    first".
- (b) Leave the manifest unchanged. Record in PREFLIGHT §3b now (pre-data) that item 5 is
  recomputed at VERIFY from the copied `activation_widths.jsonl` with the filter in (a), and that
  the readout's `controller_error` field is ignored. Cost: 0. It is weaker, because the definition
  lives in prose rather than in the frozen readout.

**Also state what the ratio measures.** `ebops_in_training_over_traced` is in-training EBOPs over
traced EBOPs (`:1120`). It measures the drift between the D20 trace and training, not
traced-vs-target tracking. The target-tracking error for (c) arms is already in `monitor_p`'s
`controller-*.json`. noC arms are skipped there because they have no `pid_telemetry` (readout
line 50). For a noC-vs-C comparison on the same footing, add the per-arm median and max of
`ebops / target_ebops` over traced epochs ≥ warmup to the same diag entry. It is one more line in
the same heredoc, at the same cost.

Jev `jev_rank_snippets` (audit `jv-ed24e96163c04c318f5c52b80d40e8ab`, advisory, disposition
"review") ranked `03-phases.md:120-130` (VERIFY recomputes and applies pre-registered rules) and
`06-review.md:118-130` as partial evidence (scores 1.87 and 1.74). By hand, both support writing
the definition down before data, which is what (a) does and (b) does in prose.

## Grade B

### B1. PREFLIGHT §3b states the wrong pod deadline, and the A07 margin is thin
- §3b says the F2 build uses D = 21,600 s, and its arithmetic and A07-fit text use 21,600
  (PREFLIGHT.md:288, :299-315, :347).
- The frozen handoffs use 20,800: `PREPARED.json` options give `pod_deadline_s 20800` on every job,
  PROGRAM.json `caps.pod_deadline_s` is 20800, and JOURNAL 05:58 agrees. At 20,800 the worst case
  is 24 × (20,800 + 600 + 180) s = 143.9 GPU-h, so the cap holds.
- The A07 run budget becomes about 20,800 − 300 − 420 = 20,080 s. Against the pessimistic
  500 × 38.8 s = 19,400 s (gpu-benchmark VERIFY.md:109, n = 1 × 20 epochs, total elapsed per
  run-epoch) that leaves about 680 s. At 30.85 s/epoch it leaves about 4,650 s.
- The risk: a deadline kill on A07-5000k-C, the positive control, gives no epoch-500 snapshot. That
  trips stop rule 1, so R1 yields nothing decisive.
- **Fix:** correct the §3b text to 20,800 and state the margin (0 cost). Raising D would change all
  24 GPU handoff IDs before signature (no bundle change, no gate) and break the 144 cap. It is not
  recommended unless cluster-ops judges the 38.8 s bound realistic for 500-epoch runs. That bound
  amortises startup over only 20 epochs, so it overstates the per-epoch cost.

### B2. a26 on the retained epoch-0475 checkpoint: a free two-point entropy slope
- `save_checkpoint` keeps two generations (`ablation.py:262-264`, checkpoint every 25 epochs), so
  `checkpoints/epoch-0475/model.keras` exists at the pause.
- One more `attn_entropy.py --checkpoint` call per arm (about 24 × 1-2 min of CPU, inside the 43,200 s
  readout deadline) gives Δentropy over the last 25 epochs.
- This is the cheapest partial substitute for the deferred epoch observer (cons v1 B5). It shows
  whether a row near the 0.95 cut is still moving, for example D-s1-style late re-growth. That is
  exactly the case most likely to trigger an entropy-only stop for Kai.
- **Cost:** the same readout-only re-preparation as A1(a), plus one diag field. 0 GPU, no gate.
- It stays descriptive and never feeds a rule.

## Grade C

- **C1.** One STUDY line: qkv1 t_uniform is `None` by construction (`FlooredKIF`). For qkv1 arms, H3's
  mechanism is read from `site_order` (V, softmax sites, FFN) and `cost_split`, not from t_uniform.
- **C2.** For E-unc-C, `cost_split.share_of_budget` is relative to 1e8 and so is meaningless. Read
  `share_of_total` only. Text only.
- **C3.** Diag a26 calls reload the validation cache once per process, 46 times. If the readout
  approaches its 12 h deadline after `readout.json` is written, the Job ends `DeadlineExceeded`
  even though the rule inputs are complete. Check this against the measured R1 readout wall time.
  No change now.

## Is a new code bundle worth it?

No. The arbiter deferred cons v1 B5 (the epoch observer) at about 2.5 agent-h plus a gate rerun.
That deferral still holds. Any training-code change now costs:
- a third bundle;
- a CPU gate of about 62 min (b3fb22, JOURNAL 16:14);
- PREFLIGHT critical v3;
- and the reset of the F6a byte-equal baseline that R2/R3 must match.

It would buy only an entropy curve. B2 approximates the end of that curve for free, and A1 and B2
both ride on one readout-only re-preparation.

Nothing else cheap would make R1 more decisive. Its decisiveness is now bounded by n = 2 per arm,
which the STUDY already handles by reading R1 verdicts as leads (STUDY.md:184-190). It is not
bounded by missing instrumentation.

## Summary

| item | grade | pods | GPU-h | change | sharpens |
| --- | --- | --- | --- | --- | --- |
| A1 controller-error filter (+ ebops/target) | A | 0 | 0 | readout handoff only, or a VERIFY rule | H1 |
| B1 §3b deadline text and A07 margin | B | 0 | 0 | text | positive-control risk |
| B2 a26 on epoch-0475 | B | 0 | 0 | the same readout re-prep | D1, entropy-only stop |
| C1-C3 | C | 0 | 0 | text | reading |
