# STUDY physics review, v2

Reviewer: physics-reviewer (fresh context). Artifact: `campaigns/2026-09-26-training-batch/STUDY.md`
(v1 as revised by the fixer after `review/STUDY_arbiter_v1.md`). Phase: STUDY, so there are no results;
the checks apply to the plan.

## Figures

No figure exists at STUDY and the artifact cites none. Three are pre-registered (Falsifier, "Figures"):

| figure (planned) | status against the spec |
| --- | --- |
| Per-class ROC on ROC-test, log mistag axis, seed band (sd ddof=1, seed count in legend), caption "ROC-test, n = 260,000" | spec correct: log axis, split, n and seed count all named. Must state k (feasible, non-diverged seeds) when k < 8 |
| A-B-C accuracy-versus-EBOPs ladder with paired-gap intervals | spec correct (paired, not unpaired bars). Undefined if B has no feasible seed, which the arithmetic in A1 makes likely; say what is drawn then |
| Interim-readout figures, "validation, n = 62,000" | spec correct |

## What I verified

- Archived N=64 seed spread: recomputed from `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz`
  (keys `y`, `score`, `meta`; y shape 260,000 × 5). W1A8 held-out top-1 accuracy 67.18 / 72.64 / 67.21 %,
  mean 69.01 %, sd (ddof=1) 3.14 pt; FP32 79.42 / 78.83 / 79.10 %, mean 79.11 %, sd 0.30 pt; n = 260,000,
  3 seeds, archived. Matches STUDY.md line 67 exactly.
- Interval algebra: 2.365/√8 = 0.836; 2.571/√6 = 1.05; 3.182/√4 = 1.59; 0.5/0.836 = 0.60 pt and
  0.5/1.05 = 0.48 pt; binomial SE √(0.79·0.21/62,000) = 0.16 pt; 558,000/2,790 = 200 steps; 172.8 s ×
  7,000 = 14.0 d; 30 s × 7,000 = 58.3 h and 48/6 × 58.3 = 467 pod-hours. All correct.
- Paper: Table 1 of `literature/.../2510.24784_...pdf` gives Deep Sets (HGQ) N=64 79.4 %, Linformer
  79.8 %, MHA 77.9 %, MLP Mixer [18] 79.7 %; §3 states the 350,000 EBOPs PID target and the MHA N=64
  collapse into a Deep Set. Quoted correctly.

## Findings

### (A) must resolve

**A1. At 350k EBOPs the fixed 10-bit softmax output makes A07 N=64 feasible only by removing the
attention branch. The design can compute this now; it treats it as unknown and gates it with a check
that cannot detect it.**

Attack. The A·V product is priced by HGQ as Σ over MACs of bw_attn · bw_V
(`reference-code/HGQ2/src/hgq/layers/ops/einsum.py:61-64`, `QEinsum._compute_ebops`). In our model the
softmax output quantizer is fixed, `k0=0, i0=1, f0=9, trainable=False` (10 bits;
`bnjettag/code/constituent-study-20260922/bnhgq2/qat.py:440-441, 496-502`), and V enters through
`stream_iq`, one learned width per (head, e) channel shared over particles (`qat.py:431-432`). Shape
arithmetic for A07 at N=64 (d 32, 4 heads, e 8; my computation from the layer shapes, a lower bound
over the einsum layers only, excluding softmax tables, head and bias terms):

| term | MACs | EBOPs with every learnable width at 1 bit |
| --- | ---: | ---: |
| dense inputs (input_proj, Wq, Wk, Wv, Wo, fc1, fc2), binary weights | 399,360 | 399,360 |
| Q·K scores | 131,072 | 131,072 |
| A·V (10-bit attention × V) | 131,072 | **1,310,720** |
| total | | **≈ 1.84M (5.3 × 350k)** |

Calibration: the same arithmetic at the 8-bit init gives ≈ 22.1M against the traced 24,816,782
(`campaigns/2026-09-23-confirmation/n64-full-preflight-result.json`), within about 11 %, so the model
of the accounting is right to that level. Each live V channel costs 10 × 64 × 64 = 40,960 EBOPs, so
even with the rest of the network free, at most 8 of 32 V channels can sit at 1 bit under 350k; with
the dense layers carrying any signal, far fewer. Arm E (d 24, 2 heads, e 12): A·V at 1-bit V is 983k,
2.8 × target. Arm B (175k) is tighter still. The screen plateau at 4.63M with β still rising
(`review/STUDY_investigation_350k.md`) is consistent with this.

Consequences for the design:
- [A7] computes the floor with "every trainable activation width at its lower bound". The lower bound
  is 0 bits, so the A·V, Q·K and dense terms all vanish and the floor is near zero. [A7] will pass
  trivially and cannot detect the case that matters: feasible only by pruning V (and most of the
  network) to 0 bits.
- The paper's attention widths are "constrained to at least one bit to disable pruning for training
  stability" (§3, pdftotext of the cited PDF, the paragraph before the Table 1 discussion), and
  Chang's `get_transformer` uses HGQ's `QMultiHeadAttention` with learned, per-value datalane widths
  for the softmax output (`reference-code/HGQ2-examples/jsc150/model.py:183-195`, table `bc=Min(4)`).
  The fidelity table (STUDY.md lines 126-142) has no row for either the ≥ 1-bit attention constraint
  or the fixed 10-bit softmax output versus a learned one. Under the paper's ≥ 1-bit constraint our
  arm A would be statically infeasible at 350k (≥ 1.31M from A·V alone). Our recipe's feasibility, if
  it comes, comes from a freedom the paper removed.
- The primary question asks what "the binary-weight N=64 tagger" (a transformer) reaches at 350k. By
  the arithmetic, if arm A meets the budget claim, the selected checkpoints will almost certainly have
  most V channels at 0 bits: the model measured is a binary Deep Set with a vestigial attention block.
  The attention diagnostic would discover this at REPORT; the design should state it now.

What settles it: (1) add to PREFLIGHT a **1-bit-alive floor** per arm (every learnable width at 1 bit,
fixed widths at their values) next to the 0-bit floor, and record the V-channel budget it implies for
350k and 175k; (2) before the canary, choose and write down one of: (a) make the softmax output width
learnable or lower (for example `softmax_out_bits` 2-4) in a labelled arm so attention can survive at
350k, or (b) pre-register that arm A at 350k is expected to be measured as a binary Deep Set, reword
the question and title accordingly, and make the V-at-0-bits fraction a pre-registered outcome; (3) add
the two missing rows to the fidelity table.

### (B) should address

**B1. "V at 0 bits … a different model, not a Deep Set" is wrong.** (STUDY.md lines 303-304 and
695-700.) With V at 0 bits, ctx is zero, Wo adds only its bias, and the network is per-particle
input_proj → per-particle FFN → global average pool → head: that is the Deep Sets form φ → pool → ρ.
Learned PE makes φ position-indexed but keeps the set-sum form (and the inputs are pT-sorted). So the
two collapse routes lead to the same model class, and both support the 79.4 % Deep Sets comparand. Fix
the text and let the diagnostic distinguish "Deep Set by uniform attention" from "Deep Set by V
pruning" without calling the second a non-Deep-Set.

**B2. The optimizer-stability falsifier cannot reach significance.** At 8 seeds, the threshold (A
diverged minus D diverged ≥ 4, for example 4 of 8 against 0) gives an exact McNemar two-sided
p = 2 · 0.5⁴ = 0.125; even 8 against 0 gives 0.0078, and Holm with the recipe claim raises it. Holm-
adjusting this claim is decorative at the threshold stated. Keep it as a count rule and say it
carries no p-value at the threshold, or move it out of the Holm family.

**B3. Arm B's role.** With A1, B at 175k is close to a guaranteed "no feasible checkpoint" or a model
with almost no live channels. Eight 7,000-epoch runs for that are expensive. State before the canary
whether B stays as a ladder rung, is replaced by a target that keeps attention alive, or is cut first
(the artifact already names F as first to cut; B is the stronger candidate).

**B4. The primary question does not bear on the thesis, and the artifact says so.** No arm varies
the weight type (lines 44-51), and the "distance to 79.4 %" mixes weight type, model family, softmax
width policy (A1), head, backend and selection. That is honest. It means the campaign, as designed,
answers "what does this pipeline reach under that recipe", not "what do binary weights cost". A
referee for the thesis would want the matched non-binary arm (arm H or the in-house arm) in the same
campaign, not as a follow-up; that decision is flagged for Kai and should be taken with A1 in view,
since A1 applies to any in-house arm with the same fixed softmax width.

**B5. Survivor bias plus winner's curse bias the distance in one direction.** Both the dropped
infeasible/diverged seeds and max-over-7,000-checkpoint selection push the arm mean up. The held-out
evaluation removes the second on the reported number; the first remains. State that A − 79.4 is an
upper estimate whenever k < 8, beside the interval (lines 225-226 say it for the mean; carry it to the
distance).

### (C) suggestions

- C1. Resolving power is stated at two bounds (±0.16 and ±2.63 pt); the epoch-500 trigger at sd >
  0.6 pt is sensible. Add that at the archived binary N=64 spread the 1.0-pt descriptive line (78.4 %)
  cannot be resolved, so the likely outcome is "straddles", and say that in advance.
- C2. The A1000 − R and D1000 − R comparisons cross GPU type (R packed separately, line 349); record the
  GPU class per run in the evaluation JSON so a reader can see it.
- C3. The ROC-test `y` alignment gate against `r14/n64/*.npz` is a good check; also assert that the gate
  leaves label counts per class unchanged (it should, since it zeroes features, not jets).

## Suspiciously good agreement

Nothing to flag at STUDY: no results exist. The archived sd recompute matching to the stated digits is
expected (it is the same file and the same computation), not suspicious.

## Decision

I would not approve this STUDY yet. What decides it is A1. Shape arithmetic shows that with the fixed
10-bit softmax output, 350k EBOPs at N=64 is reachable only by pruning attention away. The design must
state that 1-bit-alive floor and choose, before the canary, between a softmax width that lets attention
survive and a question reworded as "a binary Deep Set at 350k".
