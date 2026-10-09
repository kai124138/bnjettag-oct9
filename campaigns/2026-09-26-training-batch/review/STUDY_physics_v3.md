# STUDY physics review v3: 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context; earlier reviews, methodology and conventions not read).
Artifact: `campaigns/2026-09-26-training-batch/STUDY.md` (v1 amended after the [A7] trace, 2026-09-27).
There is no compiled PDF beside it.

## Figures

No figures exist at STUDY. The pre-registered figures (STUDY lines 461-467), assessed as a plan:

| figure (planned) | status |
| --- | --- |
| Per-class ROC on ROC-test, log mistag axis, seed band (sd ddof=1), seed count and k in the legend, caption "ROC-test, n = 260,000" | Adequate as planned. The arms it shows are not named (see C1). |
| Accuracy-vs-EBOPs ladders, A07 (A at 350k, C at 5M) and E (B at 250k, E at 350k), "paired-gap intervals", empty marker for 0/8 rungs | The plan does not say how a paired interval goes on an accuracy axis (C1). The empty-marker rule is good. |
| Interim-readout figures labelled "validation, n = 62,000" | Adequate. |
| Missing: attention-state diagnostic (Q/K and V fraction at 0 bits, entropy / log 64) per arm | Not pre-registered as a figure, although it is the number that decides what the A07 arms measured (C2). |
| Missing: validation − held-out accuracy gap per run (winner's curse) | Promised in the text (line 361), no figure (C2). |

## Verified

- Archived Round 14 N=64 W1A8 held-out accuracy: recomputed from `bnjettag/roc-results/r14/n64/W1A8-s{1,2,3}.npz`
  (keys `y`, `score`, `meta`; shapes (260000, 5)). I get 0.67176 / 0.72638 / 0.67207, mean 0.69007, sd (ddof=1)
  0.031446. The artifact says 67.18 / 72.64 / 67.21 %, sd 3.14 pt. Matches.
- Sun et al. Table 1 (pdftotext of the cited PDF): Deep Sets (HGQ) N=64 79.4 %, Linformer 79.8 %, MHA 77.9 %, and
  the 350,000 EBOPs target set by PID on β. Matches.
- Traced floors: `code/evidence/static_floors_arms_s1.json` (A-s1: zero 343,053, one 1,005,741, headroom 6,947,
  0-bit floor / target 0.98015) and `static_floors_trace_step2.json` (a07-current: zero 4,580,398, init 24,816,782).
  Match the text.
- `code/evidence/a17_pairing_{with,without}_0011.json`: without 0011, 8 shared kernels differ at s1 (unpaired);
  with 0011, only `pos_enc/pos_table` differs at s1 and s2. Matches [A17]. Only 2 of 8 seeds are in evidence; the
  STUDY requires all 8 at PREFLIGHT.
- Arithmetic, recomputed with scipy: t(0.975,7)/√8 = 0.8360; t(0.975,5)/√6 = 1.0494; t(0.975,3)/2 = 1.5912;
  0.836 × 3.1446 = 2.63 pt; 7,000 × 112.6 s = 9.12 d; 14 d / 7,000 = 172.8 s; 100.09 × 558/496 = 112.60 s;
  binomial SE at p = 0.79, n = 62,000 = 0.164 pt; Fig. 2 legend means 0.9532 and 0.9428; 6,947 / 2,048 = 3.39
  one-bit d32 channels. All match.

## Findings

### (A) must resolve

**A1. The budget claim can pass by construction under [D19], and so can the epoch-500 sd gate.**
Attack. Under [D19] every activation width can reach 0 bits. The traced 0-bit floor of A07 is 343,053, which
is under 350,000 (`static_floors_arms_s1.json`, `zero.total`). The network with every width at zero is
therefore feasible. That network outputs a constant class, near 20 % accuracy. The PID is log-scaled with β
bounded at 1e-3 (D5), so it can push the model to that point. "A feasible checkpoint in at least 6 of 8 seeds"
then mainly tests whether the run diverges at LR 3e-3; it does not test tagging. The epoch-500 sd rule (the
Kai report fires only if sd > 0.6 pt) has the same weakness: nearly collapsed seeds that predict almost
constant outputs agree closely, so the gate passes quietly exactly when the arm measures nothing. Two
pre-registered gates that pass when the model is dead are the suspicious-agreement pattern.
Evidence. Lines 389-396 (the budget claim is "Supported otherwise") and lines 309-316 (the sd gate). There is no
minimum-performance term anywhere in the Falsifier.
What settles it. Pre-register a performance clause for the budget claim: "feasible" counts only when the
selected checkpoint's validation accuracy is above a stated floor, for example the majority-class rate plus a
margin, or the accuracy of a 3-feature, 1-bit Deep-Set reference. Otherwise demote the budget claim to a
descriptive count. Make the sd gate report the seed-mean accuracy beside the sd, and send it to Kai whenever
that mean is below the same floor.

**A2. As written, the primary arm (A07 at 350k) measures an almost empty network, and so do the recipe and
stability claims.**
Attack. The artifact's own trace leaves A07 6,947 EBOPs above the floor. At 1 bit, `input_proj` costs 6,144 in
total (2,048 per input feature), `head_fc1` 1,024 and `head_fc2` 160 (`static_floors_arms_s1.json`, `one.per_layer`).
The best feasible A07 is roughly: all three input features at 1 bit, about 25 head channels at 1 bit, and every
attention and FFN input at 0 bits. That is a 1-bit Deep-Set pooled through the residual. 343,053 of the
350,000 goes to softmax tables that, with Q/K at 0 bits, compute uniform attention and do no work. A − 79.4
(primary), A − R (recipe claim), A − D (stability) and A − F all sit on this network: 32 of the 56 runs.
The answers are largely fixed before any GPU time. A − 79.4 would be a large negative number explained by
the floor, and A − R would compare which recipe finds the same three 1-bit channels.
Evidence. The STUDY states this itself (lines 74-82, 962-978, "close to a test of the floor") and the designer
recommends E primary, but A07 stays the default.
What settles it. Make E primary (headroom 178,474 at 350k). Move D and R onto E so that the recipe and
stability claims rest on a model that can learn; the STUDY already lists this as a Kai option at +16 runs.
Keep A07 at 350k as a labelled descriptive arm, "our A07 at the paper's budget", or cut it. A physics review
should not leave this to the Kai table: as written, the design cannot answer its own question.

### (B) should address

**B1. The fidelity table misstates the paper on attention pruning.** Line 196 says the paper's activation
overflow and 0-bit reachability are "not stated". Sun et al. §3 (pdftotext, the paragraph beginning "Bitwidths
for the Linformer models") states that "the attention layer ... is constrained to at least one bit to disable
pruning for training stability". It also says MHA-64 collapsed "despite the bitwidth constrained to at least one
bit". Chang's `jsc150/model.py:193` has the datalane `bc=Min(1)` scope commented out, so code and paper differ
here. [D19] follows the code (0 bits reachable in Q, K, V), and the paper's reported rows forbade exactly that.
Under the paper's rule, A07's relevant floor is close to its 1-bit-alive floor, 1,005,741, which makes it
STATIC_INFEASIBLE at 350k. E's attention streams at 1 bit add about 110k (Wq/Wk/Wv inputs) + 98,304 (Q·K) +
98,304 (A·V) to 171,526, about 478k, also above 350k (my arithmetic from the per-layer widths, not traced).
Settle: correct the row, add "binary weights reach 350k at N=64 only because attention may prune to 0 bits,
which the paper's protocol did not allow" to [L2] and to the reading of A − 79.4 and E − 79.4. Optionally trace
an "attention ≥ 1 bit" floor for E at PREFLIGHT.

**B2. Iso-EBOPs against a Deep Sets comparand hides a structural tax.** The comparand (Deep Sets, HGQ) pays no
softmax. Our A07 pays 343,053 (98 % of the budget), and E pays 171,526 (49 %), for softmax tables even when the
attention is uniform. Beside [L2] (accumulator), state this tax as a number in the reading of every distance to
79.4 %.

**B3. [D20] is not in the staged code.** `code/tree/bnhgq2/ablation.py:450` sets `sample = xt[:256]`, and
`compute_ebops` runs on that sample twice per epoch (lines 515, 521). The STUDY pre-registers a full
training-split trace (n = 558,000) for feasibility, the WRAP ranges and certification (lines 765-789). Until that
change lands, feasibility, the ranges and the selected checkpoint all come from 256 jets. The STUDY's own
synthetic check shows this moves EBOPs by 5 % and top-1 on 0.6 % of rows. Make it a named PREFLIGHT gate that
cites this line, and measure the cost of the two 558k-row traces in the canary. The same gap applies to
`static_floors_arms_s1.json`, whose B entry is still A07 at 175,000 (pre-fix). The STUDY acknowledges this at
lines 536-543, and PREFLIGHT must show B regenerated on E at 250k.

**B4. The stability claim defaults to "safe".** Falsified only when A has at least 4 more divergences than D, so
a 3-0 split does not falsify it. At 8 seeds the rule cannot support "Chang's optimizer is safe for binary
weights". It can only fail to falsify it. Name the outcome "not falsified at this resolution (8 seeds)" and never
write "safe".

**B5. "Recipe claim supported on feasibility" when R is infeasible is not a tagging statement.** With 0 bits
reachable, R's infeasibility after 1,000 epochs at LR 2e-5 measures how fast the widths fall under a small LR,
not whether the recipe tags better. Report it as "R did not reach 350k in 1,000 epochs", with the epoch-matched
A1000 and D1000 feasibility beside it, and do not use the word "beats".

**B6. The resolving power for the recipe and secondary gaps rests on an unmeasured sd_diff.** The two bracketing
sds (0.19 pt N=8, 3.14 pt archived N=64) are for single arms. The paired half-width is 0.836 · sd_diff, and after
14 LR restarts to 3e-3 the per-seed correlation may be about zero (the STUDY says so, line 296). Then sd_diff ≈ √2 · sd
and the resolvable paired gap at the archived spread is about 3.7 pt. State that figure beside A − R and the
Holm set, so that "flat" reads as "cannot resolve below ~3-4 pt", not as "no effect".

### (C) suggestions

**C1.** Name the arms in the per-class ROC figure (A, E, and C at minimum). For the ladders, say where the paired
interval sits: a lower gap panel (Δ accuracy with its t-interval and n_pairs) is clearer than bars on the
accuracy axis.

**C2.** Pre-register two more figures: the attention-state diagnostic per arm (fraction of Q/K and V channels at 0
bits, entropy / log 64, at the selected checkpoint), and validation − held-out accuracy per run. Together these
show whether a feasible arm is a Deep Set and how large the winner's curse is.

**C3.** Parameter counts: line 118 gives 12,788 for A07 under the old quantizer. `code/evidence/cpu_gate_final.json`
gives `params_kernel_bias_pos` 11,653 and `count_params` 61,951 under [D19]. Reconcile them so a reader can see
that the trainable weight set did not change, only the quantizer parameters.

**C4.** R packs separately and crosses GPU type relative to A and D (line 510). This is acknowledged and TF32 is
off, so it is only numerics. Keep the GPU-class column in the paired table.

**C5.** Cite the strongest evidence for E in the primary-architecture FLAG. Our run of Chang's xfm-n64 (d24, h=2,
tables `bc=Min(4)`, the same softmax structure as E) reached 80.56 % at 348k
(`_attic/repro-chang/repro-chang/comparison.md`, single seed, test-selected, unverified, context only). Chang's
architecture works at this budget when weights can prune. That row is the reason to expect that E's headroom is
usable and A07's is not.

**C6.** Only seeds 1 and 2 have [A17] pairing evidence. The all-8-seeds requirement is stated; carry it into
PREFLIGHT as a gate, not a note.

## Summary judgement

Stripped of framing, the design produces an honest, well-labelled number with correct interval machinery:
sample sd, paired t with df = k − 1, sign count, survivor bias labelled, Holm on the secondaries, held-out used
only after selection, per-class AUC beside macro. For its primary arm, though, that number is largely set by a
static floor that leaves 6,947 EBOPs of learnable capacity. The budget claim and the epoch-500 gate pass when the
model is dead.

Do not approve as written. It is approvable with E primary, and D and R moved onto E, once a performance clause is
added to the budget claim. The deciding fact is the primary arm's headroom above its traced 0-bit floor: 6,947
EBOPs for A07 against 178,474 for E.
