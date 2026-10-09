# UPSTREAM_FEEDBACK — 2026-09-23-confirmation

Written 2026-09-27 by the fixer of `campaigns/2026-09-26-training-batch` under
`campaigns/2026-09-26-training-batch/review/STUDY_arbiter_v2.md` finding #19 (category C here,
upstream feedback). Nothing in this campaign's artifacts is edited by this note.

## Finding

The N=64 confirmation runs at the 5,000,000 EBOPs target train the A07 architecture on the
current quantizer (`bnjettag/code/constituent-study-20260922/bnhgq2/qat.py`: SAT activations
with k = 1, so each channel costs at least 1 bit; softmax output fixed at 10 bits; softmax exp
input 10 bits and exp and inv tables 12 bits, fixed). Under that quantizer the static EBOPs
floor of A07 at N=64 is **4,580,398** (full-model CPU trace by ml-engineer, 2026-09-27,
`campaigns/2026-09-26-training-batch/code/evidence/static_floors_trace_step2.json`; synthetic
sample, not a result). The arbiter's hand arithmetic gave 4,559,008 (`STUDY_arbiter_v2.md`,
"Independent checks"); the +0.47 % gap is a table-cost term the arithmetic omitted. Of the
floor, the fixed softmax internals are about 2,716,672 (arbiter arithmetic).

- The 5M target sits about 9 % above that floor (5,000,000 / 4,580,398 = 1.092), so these
  runs measure a model near its minimum widths, not a model with free width to trade.
- The 2026-09-22 screen's lowest A07-N64 EBOPs, 4,630,276 (zero-based epoch 46; W&B, seed 1,
  50 epochs, not a result; `campaigns/2026-09-26-training-batch/review/STUDY_investigation_350k.md`),
  sits 1.1 % above the floor. The screen plateau is therefore the quantizer's static floor, not
  a truncated descent. This corrects investigation caveat 1 ("not evidence of a floor").
- The 5M target was set from those screen endpoints (4.6-4.8M,
  `publication/docs/current-work/CONFIRMATION_RUNS_20260924.md:26`), which is consistent with
  the target having been placed just above the floor.

## What it means for readers of this campaign

Any VERIFY or REPORT of the 5M N=64 runs should state that the target is about 9 % above the
quantizer's static floor, and should not read the reached EBOPs as a trained trade-off. The
full-model CPU trace above is `[A7]` of the training-batch PREFLIGHT (updated 2026-09-27 from
the arbiter's arithmetic to the traced value).
