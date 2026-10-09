# STUDY constructive review v1: pilot program, 2026-10-05

Reviewer: constructive-reviewer (06-review §6.2, STUDY panel). Artifact: `STUDY.md` (with amendment
A2, 14:14 JST). Also read: `docs/PILOT_PROGRAM.md`, `PROGRAM.json`, `dev/README.md`, `docs/ROADMAP.md`,
`docs/methodology/03-phases.md` and `06-review.md`, `docs/conventions/jet-tagging-metrics.md`, the
experiment log head, `review/PREFLIGHT_critical_v1.md`, and the frozen tree `code/tree` (bundle
b3fb22c8). Read-only. No number below is a result: the floors and headrooms are the STUDY's own
static-trace arithmetic, and the code facts are cited by file:line.

Question asked: under a 24-pod cap at about 6 h per pod, which small additions would make R1 much
more informative? Costs use the STUDY's own basis (§11: 6 h per pod, RTX 3090).

## The leverage point: R2 already needs a new bundle

STUDY §7 says R2 uses "the same bundle as R1", and §12 says "a new sha stops the program". Bundle
b3fb22c8 holds only the 23 R1 configs. `campaigns/pilot1005/configs/` has 23 files,
`pilot1005/index.json` has 23 rows, and `pilot1005/generate.py:1` reads "Generate the pilot-program
round-1 configs". PROGRAM.json `r2_launch` and `r3_launch` expect pre-built handoffs for "seeds 2-4
for every E rung", for variants at seeds 3-5, and for NB at each rung above 350k. None of these
configs exists in the bundle, and the readout reads only `pilot1005/index.json` rows.

So one of two things has to happen before R1 launches (or the program will stop at R2 under its own
§12 rule):
- **(i)** Rebuild the bundle with every R2/R3 config generated now. This is the cleaner route,
  because the training code stays byte-identical and only configs and the index are added.
- **(ii)** Amend §12 to say "same training-code manifest" rather than "same bundle sha".

If (i) is taken, the bundle changes and the CPU gate reruns anyway. The marginal cost of every
"needs a config" item below then drops to roughly zero engineering time. STUDY D3 already says to
switch w150 → w100 "if the bundle is rebuilt for any other reason". This is that reason. (This is
a design-integrity point, so it is graded A1. The critical-reviewer may also raise it.)

## Grade A (would change a referee's mind; cheap)

### A1. Make R2/R3 reachable: generate all pre-built round configs into the R1 bundle now
- **What:** extend `generate.py` to emit, now, the R2 bracket configs (E rungs × seeds 2-4), the W
  candidates (6 variants × seeds 3-5), V_bin/NB s3, and R3 NB@rung × seeds 1-3. Add them to
  `index.json` with `round` set. Alternatively, amend §7/§12 as in (ii) above.
- **Cost:** 0 pods. ml-engineer about 1-2 h, a new bundle sha, a CPU gate rerun (≤4 h, CPU only),
  new handoff IDs, and a PREFLIGHT re-review of the diff. R1 is delayed by about the gate time.
- **Sharpens:** everything after R1. Without it, the program stops at `r2_launch` by its own rule.

### A2. A per-arm trajectory table from logs that already exist (no training-code change)
Every arm already writes the following per epoch, with or without (c):
- `activation_widths.jsonl` holds per-site `widths` (bits, i, f), `per_layer` EBOPs on traced
  epochs, val acc/AUC, `beta`, `ebops_in_training_over_traced`, and for NB `weight_bits_mean` /
  `weight_zero_bits_fraction` (`bnhgq2/ablation.py:1118-1150`).
- (c) arms also get `pid_telemetry.jsonl` with `attn_zero_bits` per block and `attn_qk_all_zero`
  (`ablation.py:654-674`, `:1153-1165`).

None of it reaches the readout. Pre-register a descriptive table (`readout_diag.json`, explicitly
**not** a rule input and not a `readout.json` field, so PROGRAM.json is unchanged) with, per arm:

1. **t_uniform:** the first epoch at which, in every block, the Q input or the K input is at 0 bits
   on all channels. Under WRAP that makes the logits identically 0, so entropy is exactly 1.0 from
   that epoch on (STUDY §5's own argument). This is the "epoch at which entropy hits 1.0" asked
   for, at zero cost.
   - Note: the logged `attn_qk_all_zero` requires Q **and** K both to be zero. Q **or** K is enough
     for uniform attention, so compute from `widths`, not from that flag.
2. **t_budget:** the first traced epoch meeting (a). §6 H5 already asks for this "by hand from each
   run's trace log".
3. **Site order:** the epoch at which each activation site first reaches mean 0 bits, ranked.
   H3 says attention is starved *first*. That is an ordering claim, and the ranking tests it
   directly in all 23 trajectories, not only in the 2 qkv1 rows.
4. **Cost split** at the selected (or min-EBOPs) checkpoint: `per_layer` EBOPs as shares of the
   budget (attention non-softmax, softmax tables, FFN, input_proj, head). This shows what the
   headroom is spent on (H2 mechanism).
5. **Controller error:** the median and max of `ebops_in_training_over_traced` over stepped
   epochs, for noC and C. If the two trajectories match while the health counts differ, or the
   reverse, H1 is read mechanistically and not only from 2/2-vs-0/2.
6. For NB, `weight_bits_mean` at t_budget and at epoch 500 (the C5 confound, quantified).

- **Cost:** 0 pods, 0 GPU-h, no bundle change. It is a stdlib script inlined in the readout Job
  manifest (the arm Jobs already inline Python heredocs). The readout handoff is being re-prepared
  anyway for PREFLIGHT A1 (PYTHONPATH), so this rides on the same manifest revision and the same
  re-review. It could also run locally on the copied JSONL files, as interpretation only and never
  a rule input.
- **Sharpens:**
  - H3: the site order, and t_uniform in qkv1 compared with A350-C.
  - H4: t_uniform − first feedback in w50/w150. If collapse follows the first squeeze by the same
    lag whatever the warmup, timing is not the cause even when counts are 0/2.
  - H1: the controller error.
  - H2: the cost split along the ladder.
  - H5: NB width dynamics.

  It turns 23 binary health bits into 23 mechanisms. With only 2 seeds per arm, the counts can
  only separate at 2/2 vs 0/2 (§6), so this is where most of R1's information will come from.

### A3. Calibrate the 0.95 cut on E for free: run a26 on `model_unconstrained.keras`
§5 (A2) says no working E reference exists, so the entropy-only stop is the most likely
way for the program to halt for Kai. Every run already keeps `model_unconstrained.keras`, the
highest-val-AUC traced checkpoint regardless of budget (`ablation.py:1055-1057`). It is copied into
every snapshot (`SELECTED_FILES`, `ablation.py:32`; `save_snapshot`). `analysis/attn_entropy.py`
already takes `--checkpoint` for one index (`attn_entropy.py:233-236`).

- **What:** in the readout manifest, also run a26 on `snapshots/epoch-0500/model_unconstrained.keras`
  for every E row (the ladder, w50/w150, whose best-AUC epoch may be pre-squeeze, and E5M), plus
  A07-5M. Record its epoch and entropy in `readout_diag.json`.
- **What it tells:**
  - If E's best-AUC checkpoints are non-uniform (for example < 0.9), the cut has an E reference
    before any judgement.
  - If even E5M's best-AUC checkpoint sits at 1.000000, E (1 block, 2 heads, d24) may never attend
    at this schedule. In that case the "collapse" is not caused by the budget, H1-H5 are all moot
    for E, and Kai should know before R2 (ROADMAP §6 "Deep Set" risk).
- **Cost:** 0 pods. About 1-2 min of CPU per checkpoint inside the readout Job, the same manifest
  revision as A2, no bundle change.
- **Sharpens:** D1 (the cut), the B4 entropy-only stop rule, and H2's top rung.
- **Pre-register now:** this is diagnostic only. Any change to the cut still goes through a dated
  amendment signed by Kai and labelled post hoc (§12).

### A4. Use the 24th pod for an unconstrained E positive control
R1 uses 23 of 24 pods. No E run at any budget other than 350k has ever existed (§5 A2), and E5M
still squeezes from an init of about 8.9M (A's init 8,913,043, `dev/README.md` NB floor table).

- **What:** add `E-unc-C-s1`, E with the PID target at or above init (or EBOPs disabled), (c),
  warmup 1, seed 1. Label it the architecture's positive control.
- **Cost:** 1 pod, ≤6 GPU-h (R1 cap 138 → 144, total 1,176 → 1,182 ≤ 1,200). It needs one config,
  so a new bundle. That is free if A1(i) is taken.
- **Sharpens:**
  - D1 (a measured E entropy reference, not borrowed from A07).
  - H2: it fixes the top of the E ladder. If E-unc is unhealthy, "no E rung healthy" is an
    architecture fact, not a budget fact.
  - The §7.1 pivot decision.
- It complements A3: A3 is free but opportunistic, while A4 is the designed control.

## Grade B (worthwhile; cost or confidence is higher)

### B1. Swap A07-350k for a more decisive arm
- A07-350k has headroom 6,947 (1.98 % of target). The generator itself flags it
  (`index.json` `headroom_flag: true`, the only one of the 23).
- Every hypothesis predicts it unhealthy, so its expected information is near zero. It matters
  only when E recovers at 250k (the H2 table, E 250k → A07 500k), and E 350k has collapsed in every
  earlier run (§1).
- **Swap to (recommended):** `A350-C-qkv1` at 450k, s1 (headroom 450,000 − 269,830 = 180,170, about
  equal to A350-C's 178,474).
  - This is the matched-headroom H3 arm. It removes F2's confound ("attention alive, everything
    else starved"). With it, a qkv1 failure can refute H3, where today it only reads "inconclusive".
  - qkv1@450k healthy while A350-C is not means attention starvation, not headroom.
  - qkv1@450k unhealthy while A350-C is also unhealthy means headroom, not attention.
- **Alternative:** A350-C s3, which gives the baseline a third seed so that H3/H4/H5 can use 3/3 vs 0/3
  later.
- **Cost:** 0 net pods. One config, so a new bundle (free under A1(i)). PROGRAM.json `a07_rungs` and
  the H2 A07 rule must drop 350k (a pre-data amendment). H2's A07 read then starts at 500k: if A07
  500k is healthy, "recovers at ≤ 500k" is reported. That is what H2 predicts in the likely case.
- **Sharpens:** H3 vs H2. STUDY §2 admits R1 "cannot tell them apart".

### B2. Fix the stale H3 promise in §2, or make R2 keep it
- STUDY.md:92 says "R2's direct H3 arm separates them". After the 10:46 amendment, R2 (§7) has no
  H3 arm: qkv1 gets seeds only if it wins W.
- Either delete the sentence, or add a rule: if W ≠ qkv1, R2 runs qkv1 at the matched-headroom
  budget (B1) at seeds 1-3.
- **Cost:** the text fix is 0. The rule costs 3 pods (≤18 GPU-h), and the R2 cap (10 pods) is
  already full at bracket 6 + W 3 + other side 1, so it would have to replace the W seeds or raise
  the R2 cap.
- **Sharpens:** H3. It also stops a referee catching a promise the design does not keep.

### B3. Take D3's own default: w150 → w100 on the rebuilt bundle
- w150 leaves 340 epochs from first feedback (ep 160) against b5's 259-389 epochs to first meet (a)
  (§4 row 6, A2). It also sits in the low-LR half of cycle 1, so the most likely w150 outcome is
  "inconclusive (time-limited)".
- w100 leaves 390 epochs (D3).
- **Cost:** 0 pods. Two configs, so a new bundle (free under A1(i)), plus Kai's D3 line.
- **Sharpens:** H4. It turns a likely non-answer into a read.

### B4. Label A07-5M-s1 as the reproduction/positive control
- `jet-tagging-metrics.md` §"Required validation checks" item 3 asks for "Baseline arm reproduces
  the recorded value for the same configuration within the seed spread; state the pull".
  - Jev `jev_rank_snippets` (audit `jv-a3e22f063c3d4845a92b14716b0a3eb0`, advisory) ranked this
    convention line highest for that question (score 2.87, disposition "suggestion"). By hand: it
    applies.
- A07-5M is C-s1's configuration on the new sha and the 3090. C-s1: val acc 0.664726 and head-mean
  entropy 0.739877 (§1; single seed, validation n = 62,000, 42abed code on A10, never quoted).
- **What:** state in §4 and §6 that A07-5M-s1 is the pipeline's positive control. If it is
  unhealthy, or entropy-only, the program stops before any judgement (the new sha, the product or
  the readout is suspect, not binary weights).
- **Cost:** 0 pods, text plus one PROGRAM.json stop condition.
- **Sharpens:** every hypothesis, because it guards against a broken pipeline reading as
  "collapse".

### B5. Log attention entropy per traced epoch (only if the bundle is rebuilt)
- A2's t_uniform is exact only for the 0-bit cause. Entropy can drift to ~1.0 without zero bits.
- `run_training` already takes an `epoch_observer` whose output is merged into the epoch logs
  (`ablation.py:1140-1144`).
- An observer that computes the row-renormalized entropy on a fixed 2,048-jet validation subsample on
  traced epochs (every 10) gives the full curve. It would also catch the D-s1-style late re-growth
  that §14 says the epoch-500 cut misses.
- **Cost:** code (≈ 30 lines plus a test), new bundle and gate rerun, 0 pods, and well under 1 % of
  epoch time at a 1-in-10 cadence (to be confirmed in the CPU gate). It must be shown not to perturb
  training (the a_unchanged check).
- **Sharpens:** H3 and H4 (the timing of collapse relative to the squeeze).

## Grade C (nice to have)

- **C1. The NB init confound (A2 C5).**
  - NB weights start at b0 = 4, so NB's init EBOPs are 12,362,587 against A's 8,913,043
    (`dev/README.md` NB table, structural trace).
  - An NB arm initialised at 1 bit would match A's starting cost (1-bit-alive with 1-bit weights =
    619,198, the same as A). It needs a code path for b0, so a new bundle, plus 2 pods (≤12 GPU-h)
    that R1 does not have.
  - Better: record it as the R3 or post-program follow-up if H5 reads "NB ≤ binary". Until then,
    A2 item 6 quantifies the confound for free.
- **C2.** §7.1 picks r1 from a single seed-1 row. Add one sentence: "r1 is a 1-seed locator; R2's
  4-seed bracket is the measurement". This sets expectations for a non-monotone ladder. Text only.
- **C3.** §11 basis: PREFLIGHT A2 measured 38.8 s per run-epoch total for A07 (500 × 38.8 s = 5.4 h).
  Once A2 is in place, `epoch_seconds` in the JSONL also gives E's 3090 speed per arm, which feeds
  the R2 cap. Note this in §11, for free.

## Summary of costs

| item | pods | GPU-h | code / bundle | hypotheses |
| --- | --- | --- | --- | --- |
| A1 R2/R3 configs in bundle | 0 | 0 | configs only; new bundle + gate | all after R1 |
| A2 trajectory table | 0 | 0 | readout manifest only | H1-H5 |
| A3 a26 on model_unconstrained | 0 | 0 | readout manifest only | D1, H2 |
| A4 E-unconstrained s1 | +1 | ≤6 | 1 config (free under A1) | D1, H2, pivot |
| B1 A07-350k → qkv1@450k | 0 net | 0 net | 1 config (free under A1) | H3 vs H2 |
| B2 §2 H3 sentence / R2 rule | 0 / 3 | 0 / 18 | none / R2 configs | H3 |
| B3 w150 → w100 | 0 | 0 | 2 configs (free under A1) | H4 |
| B4 A07-5M as positive control | 0 | 0 | none | all |
| B5 per-epoch entropy observer | 0 | ≈0 | code + gate | H3, H4 |
| C1 NB 1-bit init | +2 | ≤12 | code | H5 |

If A1(i), A2, A3, A4, B1, B3 and B4 are all adopted, R1 is 24 pods and 144 GPU-h. There is one
bundle rebuild and one gate rerun, which the program needs anyway to reach R2.
