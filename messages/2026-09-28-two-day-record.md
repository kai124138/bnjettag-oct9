# Record: 26–28 September 2026 (pT reweighting, the Sun et al. recipe replication, Delta)

Kept by the training-batch orchestrator session for Kai; status at 2026-09-29 00:35 UTC.
Slides: https://claude.ai/artifact/KLBFApeTBQULwDZBH2gtyk (private; download as PPTX or PDF from
the page; slide source kept beside this file in `2026-09-28-two-day-deck/`). Only the pT-reweighting
numbers are verified; every other number is design arithmetic, a CPU trace or pod telemetry.

## 1. pT reweighting, N=8 (campaign 2026-09-25-pt-weighting): done, verified

- 24 runs, 3 arms × 8 seeds: BASE (no weights), PTW5 (pT weights capped at 5), PTWNC (no cap). W1A8, N=8,
  101-epoch schedule. Launched 2026-09-25, held-out evaluation and VERIFY 2026-09-26.
- Seed mean ± sd, held-out split, n = 260,000:
  - macro AUC: BASE 0.8711 ± 0.0013, PTW5 0.8603 ± 0.0019, PTWNC 0.8587 ± 0.0020;
  - top-1 accuracy: BASE 0.6234 ± 0.0019, PTW5 0.6080 ± 0.0037, PTWNC 0.6050 ± 0.0038.
- Paired gaps, 95 % intervals:
  - PTW5 − BASE AUC −0.0108 [−0.0124, −0.0093], lower on 8/8 seeds;
  - PTWNC − BASE AUC −0.0125 [−0.0148, −0.0101], lower on 8/8;
  - accuracy −0.0154 and −0.0184, lower on 8/8.
- Binned by jet pT (post hoc), both ends of the range gain and the centre loses. The word "only"
  for the top bin is not supported.
- The primary metric and the binning were fixed after the results, so VERIFY confirms the numbers,
  not a pre-registered test. Source: `campaigns/2026-09-25-pt-weighting/VERIFY.md`.
- Open: the figure-axis and "post hoc" wording fix in the public results repo (`~/Desktop/bnjettag_results`
  ff4c3a0) is committed locally and waits for your `git push`.

## 2. How Sun et al. get 79.4 % at N=64 (question answered 2026-09-26)

- Deep Sets (HGQ), arXiv:2510.24784 Table 1: 64.7 % at N=8; 79.4 %, 44 ns, 191k LUT and 0 DSP at N=64.
  One model per row, no seeds.
- Three mechanisms:
  - accuracy rises with N for every model family;
  - LUT stays flat because every row is trained to the same 350k EBOPs, with per-position bit widths
    and da4ml adder graphs;
  - latency is set by depth, not N.
- Their code also drops constituents below 2 GeV, which the paper does not state. The Deep Sets model is
  unpublished. Notes: `docs/chang-vs-bnjettag.md`, `literature/jet-tagging-transformers/2510.24784_*`.

## 3. The Sun et al. recipe on the binary N=64 tagger (campaign 2026-09-26-training-batch): pilot running

- **Asked (09-26, Saturday night):** launch 40–60 trainings with their recipe (7,000 epochs, batch 2,790,
  LR 3e-3 with cosine restarts every 500, pT ≥ 2 GeV cut, no weights) at 350k EBOPs, with some lower
  targets, some "our way" and some architecture changes.
- **Frozen design (STUDY.md, frozen 09-28):** 7 arms × 8 seeds = 56 runs:
  - A = E at 350k with their recipe; B = E at 250k; C = A07 at 5M;
  - D = E on our optimizer; F = E plus learned PE; R = E on our recipe;
  - A07-350 is descriptive only;
  - E is d24, 2 heads, 1 block, FFN 32, no PE.

  The second wave has 24 runs: NB (learned-width weights), H (their `xfm` model) and FP32-E.
- **Caught before production:**
  - 350k was unreachable under our quantizer (A07 floor 4,580,398 EBOPs, CPU trace), so we switched to
    their quantizer set;
  - a host-memory leak of about 80–95 MB/epoch/run killed the first pilot; fixed;
  - a reload check at the epoch-500 pause could never pass; fixed;
  - GPU node c6017 produces NaN (found by Delta); excluded, with a fingerprint check in every pod;
  - the every-epoch EBOPs trace took 42 % of each epoch, so EBOPs is now traced every 10 epochs.
- **Pilot:**
  - the first pilot (old setup) was stopped 09-28 05:31 UTC by the leak;
  - the second pilot's 5-run pod (A-s1, A-s2, D-s1, C′-s1, E1-s1) runs on an A10 since 09-29 00:11 UTC;
  - its 3-run pod (A07-350-s1, C-s1, F-s1) is waiting for an A10 and resumes at epoch 25.
- **Next:**
  - the epoch-500 readout, around 19:00–21:00 UTC on 09-29 (projected). You pick the controller fix
    (c) or (d) if the pre-registered trigger fires; on the first pilot's numbers it would;
  - then production on 13 A10 pods, about 11 days per run (projected);
  - second-wave code is not written yet.
- **Details:** `campaigns/2026-09-26-training-batch/ONBOARDING.md`. Session summary:
  `sessions/2026-09-28-training-batch-orchestrator.md`.

## 4. Delta (campaigns 2026-09-26-delta and 2026-09-27-delta-screen): frozen, waiting

- A queue of 103 methods (50 singles, 53 combinations) tested against the recipe anchor, in waves 0–4.
  It was renamed from "method atlas" on 09-27. Wave 2 (the single-method screen, 500 epochs) is
  STUDY-frozen, and 38 methods have code.
- It launches at 10 pods after the anchor pilot's epoch-500 readout. Three non-binary baselines wait
  on the shared learned-weight code.
- Branch `delta-methods` on `kai124138/BinaryTransfomerJettager` is pushed and not merged.
- Run by the second session, now named `bnjettag-ae`. Details: `campaigns/2026-09-26-delta/ONBOARDING.md`.

## 5. Decisions you made

Full text: `.claude/memory/decisions.md`.

- **27 Sep:**
  - their quantizers; the ladder on E; 8–10 pods; add H and NB;
  - pilot in parallel with the review; wave-1 defaults confirmed; wave 2 overlaps; add FP32-E;
  - trace every 10 epochs; a second pilot pod; about 27 pods at peak.
- **28 Sep:**
  - stop the first pilot;
  - pilot pods on A10 only;
  - the controller trigger is pre-registered and the fix is chosen at epoch 500; FP32-E on the same
    701 epochs; A − NB at 8 pairs;
  - freeze STUDY; arm B out of the trigger.

## 6. What cost time

- Worth it: five problems caught, each of which would have wasted the full run.
- Overhead:
  - ten STUDY review rounds, mostly wording after about round 4;
  - four rate-limit stops;
  - a full A10 pool;
  - three code re-freezes.
- Net: two days in, a pilot is running rather than the 40–60 runs asked for.

## 7. Other loose ends

- The 24 Sep confirmation job (N8 at 350k, N64 at 5M) is dead since about 09-26. It is resumable and was
  not relaunched, because its runner kills the whole pod on one run's exit.
- `decisions.md` and `project-context.md` date the N64 5M target to 09-10; it first appears on 09-24.
- The memory logs (`.claude/memory/decisions.md`, `experiment-log.md`, `review-reports.md`) hold uncommitted
  edits from both sessions.
