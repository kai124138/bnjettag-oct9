# DRAFT reply to Russell Marroquin — round 14 (l1x3) results

*Draft 2026-08-03 by `paper-writer`. Not sent. Numbers audit at the bottom.*

---

Subject: Constituent-count sweep on the 3-feature L1 inputs

Hi Russell,

Following your point about input matching: we moved to the L1-realistic constituent set —
pT, η_rel, φ_rel only — as in Odagiu et al. (arXiv:2402.01876) and as your group uses, and
re-ran the sweep from scratch on it. The features are taken after the pT sort, so the
particle ordering is unchanged; nothing else in the recipe moved, so the input set is the
only difference from our earlier work. These numbers are not comparable to our 16-feature
tables and we keep them in a separate project for that reason.

The grid is N ∈ {8, 16, 32, 64} constituents × {fp32, w8a8, w1a8, w1a6, w1a4} × 3 seeds,
60 runs on NRP. Everything is in W&B project BNJetTagAug — runs are named
r14-l1x3-n<N>-<variant>-s<seed>, with code, checkpoints and evaluations logged as artifacts,
so you should be able to pull any of it directly.

Headline, ROC-test macro one-vs-rest AUC on the held-out 260k split, seed-averaged over
3 seeds:

  N=8:   fp32 .8864   w8a8 .8862   w1a8 .8712   w1a6 .8689   w1a4 .8534
  N=16:  fp32 .9128   w8a8 .9124   w1a8 .8956   w1a6 .8910   w1a4 .8693
  N=32:  fp32 .9374   w8a8 .9358   w1a8 .9052   w1a6 .9022   w1a4 .8833
  N=64:  fp32 .9486   w8a8 .9448   w1a8 .9028–.9251 (range)  w1a6 .9136   w1a4 .9073

fp32 improves monotonically with N, including 32→64 (+.0112), and 8-bit is indistinguishable
from fp32 at N=8 and N=16. The binary penalty is real at every N: −.015, −.017, −.032, −.037.
The obvious reading is that it grows with N, and I think that is probably what is happening,
but I want to be honest that no single step-to-step increase is resolved at 3 seeds — the
seed spread swallows it, and it would take roughly 30 seeds per arm to settle. Treat the
growth as a pattern, not a measurement.

The other thing worth flagging is that binary training becomes unstable at N=64: the three
w1a8 seeds land at .9028, .9251 and .9084, and the seed-to-seed differences are far outside
evaluation noise, so those are genuinely different models rather than measurement scatter.
That is why I quote a range rather than a mean there. The same effect is present but milder
at N=32. Related, and slightly encouraging: at N=64 w1a8 and w1a6 are indistinguishable,
with the point estimate actually favouring 6-bit — at long sequences the binding constraint
looks like weight binarization, not activation precision.

On cost, we have HGQ2 EBOPs as a pre-synthesis screen only (not a resource claim — that has
to come from C-synthesis). Binary owns the cheap end: every frontier point up to about 15M
EBOPs is a binary model, and the cheapest 8-bit configuration (N=8 w8a8, 9.2M) is beaten
outright by N=16 w1a6 at 3.5M. Past about 20M EBOPs the ordering flips and w8a8 takes the
frontier, starting with N=16 w8a8 at 19.7M.

Next step here is HLS synthesis on the best small binary configurations — the N=16 and N=32
binary arms — to see whether the EBOPs ordering survives real LUT and latency numbers. Happy
to share the arrays or the W&B artifacts if you want to run your own comparison against your
taggers.

Best,
Kai

---

## Numbers audit

Metric for every AUC quoted: **ROC-test macro one-vs-rest AUC (public HLS4ML LHC Jet
5-class), l1x3 3-feature inputs, n = 260,000 held-out jets, mean over 3 seeds** (except the
N=64 w1a8 entry, quoted as a seed range per the uncertainty verdict). No validation AUC, no
No 16-feature number appears.

| Number(s) | Source |
| --- | --- |
| All 20 seed-averaged AUCs in the email table | `bnjettag/roc-results/r14/{n8,n16,n32,n64}/roc_auc.md` (seed-averaged sections; verified by recompute from the `.npz`, 60/60, 2026-08-03) |
| N=64 w1a8 per-seed .9028 / .9251 / .9084 and "report as a range" | `bnjettag/roc-results/r14/n64/roc_auc.md`; `bnjettag/results/r14/uncertainty_r14.md` §Q6 |
| Binary penalties −.015 / −.017 / −.032 / −.037, all "Real" | `uncertainty_r14.md` rows 1a–1d |
| fp32 n32→n64 +.0112 (Real) | `uncertainty_r14.md` row 2a |
| w8a8 ≈ fp32 at N=8, N=16 (unresolved differences of −.0002, −.0004) | `uncertainty_r14.md` rows 3a, 3b |
| Gap growth not resolved; ≈30 seeds needed | `uncertainty_r14.md` rows 1e–1g and §What more seeds would buy |
| N=64 seed differences exceed evaluation noise (all seed-pair bootstrap CIs exclude 0) | `uncertainty_r14.md` §Q6 |
| w1a8 vs w1a6 at N=64 indistinguishable, point estimate favours 6-bit | `uncertainty_r14.md` row 4a + Guidance |
| EBOPs 9.19 M (n8 w8a8), 3.50 M (n16 w1a6), 15.03 M (n32 w1a8), 19.65 M (n16 w8a8) | `bnjettag/results/r14/ebops_r14.json` |
| Frontier / crossover statements | derived by sorting `ebops_r14.json` against the AUC table; no new measurement |
| Design, feature set, run naming, W&B project `BNJetTagAug`, artifact logging | `.claude/memory/decisions.md` 2026-08-01 "Round 14 pre-registration" entry; experiment-log 2026-08-01/08-03 entries |
| Odagiu et al. arXiv:2402.01876 | `.claude/memory/decisions.md` 2026-08-01 entry |

Note: the email deliberately quotes no seed sds and no synthesis/resource numbers — the
former to keep it readable (the full ± table is in the RESEARCH.md draft), the latter because
none exist yet for round 14.
