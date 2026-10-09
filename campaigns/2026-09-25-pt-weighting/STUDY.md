---
id: 2026-09-25-pt-weighting
date: 2026-09-25
type: pt-weighting
status: published
question: Does per-class pT sample re-weighting (Option E, cap 5 or no cap) improve the N=8 W1A8 tagger's held-out AUC or its high-pT tails against the unweighted baseline, over 8 seeds?
supersedes: 
superseded_by: 
code_sha: ConfigMap kai-ptw-n8-code-aad983805c (archive sha256 aad983805c…)
wandb: BNJetTag-Weights / group ptw-n8-20260925 (p1 runs temporarily in BNJetTagAug)
results: bnjettag/results/ptw-n8-20260925/, bnjettag/roc-results/ptw-n8/ (research tree); public: bnjettag_results README §4.5
generated: stub written 2026-09-26 from the experiment-log entries of 2026-09-25 and 2026-09-26; numbers below are copied from that log, not recomputed here
---

# Pt sample re-weighting, N=8 W1A8, 3 arms × 8 seeds

**Question.** Whether reweighting every class to the all-class log(pT) shape (Option E, Russell's
+0.5 smoothing; PTW5 = cap 5, PTWNC = no cap) changes held-out macro one-vs-rest AUC, accuracy,
or the high-pT tail relative to the unweighted BASE, on the headline r14-l1x3-n8-w1a8 model.

**Design.** 3 arms × seeds 1–8; only name, pt_weights and jit_compile differ from the headline
config (asserted in configs/gen_ptw.py). K=6 runs per GPU pod, 4 pods. Validation unweighted.
Paired comparison per seed, 95 % t-interval (df 7). Falsifier: PTW arms not lower on 8/8 seeds.

*Amendment 2026-09-26 (newton rounds, flag 8).* Pre-registered before launch (log entry
2026-09-25): the three arms, seeds 1–8, and the cap/bins from the seed-1 train-split scan.
Written after the results (log entry 2026-09-26, and this stub): the primary metric, the
paired-test rule, the falsifier above, and the pT-sextile analysis. This campaign therefore
confirms its numbers; it is not a pre-registered test, and outward text says so.

**Result (copied from the 2026-09-26 log entry; ROC-test n=260,000, seed-averaged, mean ± sample sd).**
BASE 0.8711 ± 0.0013, PTW5 0.8603 ± 0.0019, PTWNC 0.8587 ± 0.0020. Paired vs BASE: PTW5
−0.0108 [−0.0124, −0.0093], PTWNC −0.0125 [−0.0148, −0.0101], lower on 8/8 seeds; per-class AUC
lower 8/8, gluon largest (−0.028). Only the highest-pT sextile (≥1106 GeV, 60 % gluon) gains,
+0.0165 on 8/8. BASE agrees with the r14 n8 W1A8 3-seed value 0.8712 ± 0.0016.

**Interpretation.** pT reweighting as designed lowers overall tagging performance. Corrected
2026-09-26 after VERIFY.md: the gain is not confined to the tail. Both ends gain (bin 1,
< 980 GeV: PTW5 +0.0047 [+0.0020, +0.0074], 8/8; bin 6, ≥ 1106 GeV: +0.0165 [+0.0114, +0.0215],
8/8), the central bins 2–4 lose, bin 5 is flat. The binning is post hoc; bin 6 is the largest of
six comparisons. Open: whether an end-weighted scheme keeps the end gains without the central
loss, and whether the effect holds at N=16.

**Ops.** Launch record bnjettag/results/ptw-n8-20260925/launch/; 24 checkpoints fetched; eval
script sample_weighting/eval_ptw_n8.py; public repo commits 64958268 and 40da656c (bnjettag_results).
