# Literature check for Delta wave 2 screen design (2026-09-27)

Scope: does the published multi-fidelity screening, seed-variance, selection-bias and
multiplicity literature support the choices STUDY.md makes for this screen — H = 500 of a
7,000-epoch schedule, n = 4-8 seeds, best-feasible-checkpoint selection, a placebo A/A cell, a
Dunnett-type family test? Read via WebSearch/WebFetch on 2026-09-27; no local numbers used, no
comparison to our data (that is a VERIFY/results-analyst question). Rules followed: authors,
year, id/venue, URL, date accessed; no writes to shared logs; no git.

---

## 1. Multi-fidelity / early-stopping screens — does short-horizon predict long-horizon?

**Jamieson & Talwalkar, "Non-stochastic Best Arm Identification and Hyperparameter
Optimization," AISTATS 2016, arXiv:1502.07943.**
(https://arxiv.org/abs/1502.07943, accessed 2026-09-27)
What it says: introduces Successive Halving (SHA) — allocate an equal small budget to all
arms, keep the top 1/η, double the budget, repeat. The guarantee that SHA does not discard a
true winner is proved under an explicit convergence assumption ("Assumption 1"): each arm's
loss sequence converges to a limit, and an envelope function γ(j) bounds how far the loss at
budget j can lie from that limit. **The guarantee is conditional on that envelope holding** —
SHA does not prove anything about arms whose ranking at partial budget crosses their ranking at
full budget outside the assumed envelope. It gives no general rank-correlation number between
partial- and full-budget performance; that possibility is exactly the residual risk the paper's
proof pushes into the assumption.
Implication for [L1]: SHA's own theory is a conditional guarantee, not an empirical
rank-correlation claim, and it is derived for bandit losses, not epoch-500-of-7,000 validation
accuracy on a binary-weight transformer. It does not license treating H=500 as predictive; it
only says *if* curves don't cross by more than γ, ranking is preserved. STUDY.md's [L1]
(H=500 may not predict 7,000; screen only nominates candidates) is the correct posture — it
does not claim the SHA guarantee applies, it flags the assumption as unverified for this model
class and attempts a cheap check instead (long-horizon cells M015/M031/M032 vs replica at 500
and at H). Consistent with SHA's own limits, not stronger than they support.

**Li, Jamieson, DeSalvo, Rostamizadeh & Talwalkar, "Hyperband: A Novel Bandit-Based Approach to
Hyperparameter Optimization," JMLR 2018 / arXiv:1603.06560.**
(https://arxiv.org/abs/1603.06560, https://ar5iv.labs.arxiv.org/html/1603.06560, accessed
2026-09-27)
What it says: Hyperband runs several SHA "brackets" with different (n, budget) trade-offs so
that at least one bracket resembles uniform allocation, hedging against SHA's failure mode. It
reports 5x to >10x speedups over Bayesian optimization on vision and kernel tasks. η = 3 or 4 is
recommended; results are stated as "not very sensitive to η." §4.4.3 gives the explicit
counter-case: when the *identity* of the good hyperparameter changes with the resource level
(their example, tree depth vs. dataset size), "the performance on a smaller resource is not
indicative of that on a larger resource," and Hyperband is explicitly flagged as poorly suited
to that regime.
Implication: Delta wave 2 screens *architecture/training levers*, not a resource-scaling
hyperparameter, so the specific failure mode Hyperband names does not obviously apply — but
the underlying concern (a lever's effect at epoch 500 of a 500-epoch cosine cycle need not be
its effect at epoch 7,000, especially for levers that touch the schedule itself, e.g. LR
levers M028/M029, EMA M034, restart count M032) is a first-cousin of it. STUDY.md's own [L6]
names exactly this set of levers as having a winner's-curse bias that "does not cancel," which
is more specific and more conservative than anything Hyperband claims — consistent, not
weaker.

**Falkner, Klein & Hutter, "BOHB: Robust and Efficient Hyperparameter Optimization at Scale,"
ICML 2018, arXiv:1807.01774.** (https://arxiv.org/abs/1807.01774, accessed 2026-09-27)
Combines Hyperband's early-stopping schedule with a Bayesian model to choose configurations
within a bracket rather than sampling uniformly; reported as at least as robust as Hyperband
and faster to converge. Not directly load-bearing here (Delta's cells are pre-registered, not
adaptively proposed), but it reinforces that even the strongest multi-fidelity methods still
inherit SHA/Hyperband's asymmetric-budget risk — no cited method claims to remove it, only to
manage it with more brackets or a smarter proposal distribution.

**Li, Jamieson, Rostamizadeh, Gonina, Hardt, Recht & Talwalkar, "A System for Massively
Parallel Hyperparameter Tuning" (ASHA), MLSys 2020, arXiv:1810.05934.**
(https://arxiv.org/abs/1810.05934, accessed 2026-09-27)
Asynchronous SHA: promotes/kills arms without waiting for every arm in a rung to finish, for
parallel clusters. Same underlying assumption as SHA. Relevant to Delta only insofar as it
confirms multi-fidelity screening is standard cluster practice at scale; it says nothing new
about rank transfer that changes the read on [L1].

**Domhan, Springenberg & Hutter, "Speeding up Automatic Hyperparameter Optimization of Deep
Neural Networks by Extrapolation of Learning Curves," IJCAI 2015.**
(https://dblp.org/rec/conf/ijcai/DomhanSH15.html, accessed 2026-09-27; IJCAI 2015 pp. 3460-3468;
no independent arXiv id located in this session — cite via the IJCAI proceedings, not a
guessed arXiv number.)
Fits a parametric curve model to the first part of a learning curve and extrapolates
probabilistically whether a configuration could still win, rather than by point extrapolation —
because early curves can mislead and point-rank-at-partial-budget is not trustworthy.
Implication: the strongest direct evidence here that the field treats partial-training ranking
as *probabilistic*, not certain — supports STUDY.md's "ranked, not advanced" language and its
explicit [L1] rank-correlation check rather than assumed transfer.

**Overall for §1:** none of the core multi-fidelity papers offers an empirical
short-horizon/long-horizon rank-correlation number for H=500-predicts-H=7000 in this setting —
that number would have to come from the [L1] check itself. The STUDY's posture (screen
nominates, does not decide; low-power rank check attempted; language kept to "ranked, not
advanced") is the conservative reading these papers support, not an overclaim.

---

## 2. Seed variance and benchmarking methodology

**Bouthillier, Delaunay et al., "Accounting for Variance in Machine Learning Benchmarks,"
MLSys 2021, arXiv:2103.03098.** (https://arxiv.org/abs/2103.03098, accessed 2026-09-27; full
methodological detail not retrievable past the abstract in this session — recommendation
numbers below are as stated in the abstract/search summary, not the appendix, and are flagged
as such.)
What it says (abstract level): comparing two algorithms with a single-seed run each conflates
data-sampling, initialization and hyperparameter variance with the true effect; the paper
models the full benchmarking process and finds these variance sources "impact markedly" the
result; a design that adds more *sources* of variation (not just more seeds of one source) is
reported as reaching a better estimate at much lower compute than naively increasing seed count
of a single source. **Caveat**: the exact seed-count recommendation and the "51x" compute
figure could not be independently verified against the full text in this session (WebFetch
returned only the abstract); if this number is used anywhere quotable, it must be re-fetched
from the PDF or MLSys proceedings page, not taken from this note.
Implication for the STUDY: Delta pairs each cell against a same-seed replica and a placebo,
holding data sampling and hyperparameters fixed within a pair, varying only the lever — this
controls exactly the two "extra" variance sources (hyperparameter, data-sampling) Bouthillier
flags as often conflated with the true effect, which is more disciplined than a typical n-seed
comparison of two independently tuned pipelines. It does not resolve the paper's implied
critique that seed variance alone (which is what Delta's K2 rule sizes n against) is one of
several sources, and the STUDY does not vary data order or hyperparameters across seeds beyond
`order_seed = f(s)` — consistent with, but narrower than, what this paper's ideal estimator
would want.

**Picard, "torch.manual_seed(3407) is all you need: On the influence of random seeds in deep
learning architectures for computer vision," 2021, arXiv:2109.08203.**
(https://arxiv.org/abs/2109.08203, accessed 2026-09-27)
Scans up to 10^4 seeds on CIFAR-10 (fewer on ImageNet). Finding: overall seed-to-seed variance
is not huge on average, but outliers exist — a lucky or unlucky seed can beat or lose to the
mean by a wide margin, i.e. the seed distribution has heavy tails, not just a small sd.
Implication: a direct warning against the STUDY's sd-based sizing (K2 rule, sd_rep ceiling
1.3 pt) if the true seed distribution is heavy-tailed, not Gaussian — Gaussian-sd sizing
under-covers rare draws. STUDY.md flags this indirectly: its own archived seed-spread example is
"two-mode" (67/72/67%), and the family-test section runs explicit "two-mode seed" scenario rows
(own-sd rule near nominal, pooled rule badly inflated). That scenario is the closest match to
Picard's heavy-tail warning, and choosing the cell's own sd over a pooled/Gaussian-assumed sd is
the correct defensive response.

**Dodge, Ilharco, Schwartz, Farhadi, Hajishirzi & Smith, "Fine-Tuning Pretrained Language
Models: Weight Initializations, Data Orders, and Early Stopping," 2020, arXiv:2002.06305.**
(https://arxiv.org/abs/2002.06305, accessed 2026-09-27)
Fine-tunes BERT hundreds of times per GLUE task varying only seed; finds weight init and data
order contribute comparably to out-of-sample variance, and that best-of-many-trials reporting
inflates apparent gains (the more trials, the better the best one looks, for a fixed underlying
distribution).
Implication: two points bear on Delta. (a) It splits "seed" into two mechanisms (init, order)
that Delta's `order_seed = f(s)` collapses into one nuisance parameter tied to
`experiment.seed` — if sd_rep comes back large, the STUDY cannot currently distinguish "the
lever is noisy" from "the seed convention conflates init and order variance." (b) The
best-of-many-trials inflation they measure is structurally the same effect as [L6]'s winner's
curse one level up (their trials are seeds of one config; Delta's [L6] is checkpoints of one
seed) — evidence the [L6] concern is measured, not hypothetical, in a comparable setting.

**Henderson, Islam, Bachman, Pineau, Precup & Meger, "Deep Reinforcement Learning that
Matters," AAAI 2018, arXiv:1709.06560.** (https://arxiv.org/abs/1709.06560, accessed 2026-09-27)
Shows that in deep RL, different random seeds alone (same code, same hyperparameters) can
produce non-overlapping performance distributions across published "better" algorithms;
recommends reporting multiple seeds with explicit statistical tests (bootstrap CI, t-test,
K-S test) rather than a single run, and cautions that many published RL "improvements" are
within seed noise.
Implication: RL is a different failure mode (much higher variance, non-stationary reward) than
supervised jet tagging, so its specific numbers do not transfer, but its general warning —
report several seeds, use a real interval, do not trust a one-seed comparison — is exactly the
practice STUDY.md already enforces (paired t-intervals on the cell's own sd, family-pooled
sd_pool for the ranking interval, explicit refusal to call n=4 results "significant"). No gap
found here.

---

## 3. Winner's curse / selection bias from picking the best checkpoint on the eval set

**Cawley & Talbot, "On Over-fitting in Model Selection and Subsequent Selection Bias in
Performance Evaluation," JMLR 11 (2010): 2079-2107.**
(https://www.jmlr.org/papers/v11/cawley10a.html, accessed 2026-09-27)
What it says: model-selection criteria (e.g., k-fold CV score used to pick hyperparameters) have
non-negligible variance, and optimizing over that variance ("over-fitting in model selection")
biases the *reported* performance of the selected model upward, sometimes by as much as the
difference between two competing algorithms — i.e. the selection bias itself can be the
"finding." Nested (double) cross-validation, with separate inner/outer resampling for selection
vs. evaluation, is the recommended fix.
Implication for [L6]: Delta's "best-feasible-as-of-H checkpoint" selection is structurally the
model-selection step Cawley & Talbot warn about — picking the highest of up to ~50 traced
validation checkpoints per run is a search over checkpoints, and their result says the reported
accuracy of the selected checkpoint is optimistically biased relative to one chosen
independently of that validation set. STUDY.md's [L6] already names this ("winner's curse: the
maximum over up to H checkpoints is biased upward on validation") and sharpens it: the bias
cancels in a paired cell-vs-replica gap only when both have the same eligible-checkpoint count
and epoch-to-epoch fluctuation — a case where the STUDY's local reasoning is more precise than
the cited paper, and the cited paper confirms the concern is a known, quantifiable bias, not
Delta-specific overcaution.
Consistency check: the STUDY does **not** apply nested CV (an independent split for selection
vs. reporting) — it selects and reports on the same validation set, then adds a split-half
companion (select on one half, read on the other) as partial mitigation. That is a lighter
relative of Cawley & Talbot's nested-CV prescription — a single split, not a fold-averaged
loop — so it reduces but does not eliminate the bias their paper describes; STUDY.md correctly
labels it non-selecting/companion-only, not a fix.

**Dwork, Feldman, Hardt, Pitassi, Reingold & Roth, "The Reusable Holdout: Preserving Validity
in Adaptive Data Analysis," Science 349(6248) (2015): 636-638.**
(https://www.science.org/doi/10.1126/science.aaa9375, accessed 2026-09-27)
What it says: repeatedly querying the same holdout set to choose among adaptively generated
analyses invalidates the holdout's statistical guarantees; a differential-privacy-based
"reusable holdout" mechanism (adding calibrated noise to holdout answers) allows many adaptive
queries against one holdout while controlling the false-discovery rate.
Implication: Delta's screen queries the same validation set (n = 62,000) across ~46 cells x up
to 8 seeds x up to 50 checkpoints — the "adaptive, repeated-query" regime Dwork et al. formalize
— and implements no noise-adding or budget-tracking mechanism against it. It compensates
differently: non-quotability of the screen (screen numbers never enter the record, ROC-test
never touched — a firewall against adaptivity leaking into a claim), BH/Dunnett-style
multiplicity correction at the family level (§4), and a confirm wave with fresh runs before
anything is claimed. Different mechanism from the reusable holdout (firewall + re-run, not
noise-calibrated reuse), but targeting the same failure mode Dwork et al. name.

---

## 4. Multiple-comparison handling in method screens

**Dunnett, "A Multiple Comparison Procedure for Comparing Several Treatments with a Control,"
JASA 50(272) (1955): 1096-1121.** (https://www.tandfonline.com/doi/abs/10.1080/01621459.1955.10501294,
https://en.wikipedia.org/wiki/Dunnett%27s_test, accessed 2026-09-27)
What it says: when the only scientifically meaningful comparisons are treatment-vs-control (not
every pairwise treatment-vs-treatment), a many-to-one procedure with a critical value tuned to
that comparison structure has more power than a general procedure (Tukey HSD) that also
protects against comparisons nobody asked for.
Implication: STUDY.md's family-level test is a many-to-one max-t design — each cell's own-sd t
against a shared placebo/replica reference, critical value simulated as the null distribution of
max_i t_i for the family's actual m and n_p — a simulation-based, own-sd generalization of
Dunnett's idea rather than the classical equal-variance closed-form statistic. STUDY.md gives an
explicit reason for the departure: its own Monte Carlo (`screen_null.py`) shows the
pooled-variance version inflates false-positive rate to 0.14-0.55 under unequal or two-mode seed
spread, while the own-sd version stays at 0.04-0.11 — a correct extension of Dunnett's
many-to-one logic to heteroscedastic small-n data the 1955 closed-form tables (common-variance
assumption) do not cover. Separately, BH m is fixed at the `delta.json` counts (19 at 350k, 43
at 5M) for the significance-mode advance rule, distinct from the family-test's own paired-lever
m. This two-tier design (BH for "advance," Dunnett-style max-t for "ranked/flagged") is unusual
but not contradicted by any cited source, each used for the question it's assigned.

---

## 5. GPU non-determinism and run-to-run variance at fixed seed

**Pham, Qian, Wang, Lutellier, Rosenthal, Tan, Yu & Nagappan, "Problems and Opportunities in
Training Deep Learning Software Systems: An Analysis of Variance," ASE 2020 (Distinguished
Paper Award). (https://dl.acm.org/doi/10.1145/3324884.3416545,
https://hvpham.github.io/publication/2020-ASE-Variance, accessed 2026-09-27)
What it says: across six networks and three datasets, identical-config training runs (same
seed, same code) still differ due to library-level nondeterminism (cuDNN, parallel reduction
order, floating point). Even after excluding clearly-diverged/weak models, final accuracy still
differs by up to 10.8% absolute across "identical" runs; implementation-level factors alone
(holding the algorithmic seed fixed) cause up to 2.9% overall accuracy difference, up to 52.4%
per-class accuracy difference, and up to 145.3% difference in time-to-convergence. 83.8% of 901
surveyed practitioners were unaware of this.
Implication: the most important citation for Delta's determinism probe (launch gate 7) and the
placebo branch logic. STUDY.md's placebo design branches on whether the stack is "bit-identical"
(same config+seed -> identical weight hashes on one GPU product) or "divergent," with different
false-positive rates per branch (0.10 vs. 0.26 under a 0.707-SE cross-pod offset). Pham et al.'s
finding — "identical" runs are often not identical, implementation noise alone reaching several
points overall and tens of points per-class — is direct evidence the "bit-identical" branch
cannot be assumed without the probe, and that a cross-pod offset (different GPU
product/driver/library stack between the replica's pod and the cells' pods) is a realistic risk.

**Zhuang, Zhang, Song & Hooker, "Randomness in Neural Network Training: Characterizing the
Impact of Tooling," MLSys 2022, vol. 4, pp. 316-336.**
(https://proceedings.mlsys.org/paper_files/paper/2022/file/427e0e886ebf87538afdf0badb805b7f-Paper.pdf,
accessed 2026-09-27)
What it says: separates randomness into algorithmic factors (init, augmentation, dropout,
shuffling — the seed-controlled kind) versus tooling/system factors (parallel reduction order,
nondeterministic GPU kernels, library version) and shows the tooling component alone is large
enough to be mistaken for a real algorithmic effect if not measured.
Implication: reinforces Pham et al. — Delta's seed convention controls the *algorithmic*
factors Zhuang separates out, but not necessarily the *tooling* factors (GPU product, library
build, pod). The launch-gate-7 determinism probe and the flagged "no common offset between the
replica's pod and the cells' pods" assumption is the correct response to exactly this gap,
given the ~27 concurrent GPU pods this screen uses ([A3]).

---

## Implications for Delta wave 2

- No cited multi-fidelity paper (SHA, Hyperband, BOHB, ASHA, learning-curve extrapolation)
  supplies an empirical H=500-vs-H=7000 rank-correlation number for this model class; the
  STUDY's own [L1] check is the only source of that number, and its "ranked, not advanced"
  language (never "significant," never "predicts long-horizon") is the correct hedge given the
  literature offers no transfer guarantee, only conditional ones (SHA's envelope assumption).
- Picard (2021) and the two-mode-seed scenario rows in `screen_null.py` both point the same way:
  seed distributions here may be heavy-tailed/bimodal, not Gaussian, which is why the family
  test's choice of each cell's **own** sd (not a pooled or assumed-Gaussian sd) is the
  literature-consistent choice, and why n=4 "ranking, not significance" is the right frame at
  this seed count.
- Dodge et al. (2020) is a reason to log, at VERIFY, whether Delta's `order_seed = f(s)`
  conflates weight-init and data-order variance into one nuisance term — not a reason to change
  the design now, but a gap worth a one-line flag if sd_rep comes back large.
- Cawley & Talbot (2010) and Dwork et al. (2015) both confirm the winner's-curse concern in
  [L6] is a known, quantifiable phenomenon, not overcaution; the split-half companion is a
  lighter mitigation than their nested-CV / reusable-holdout prescriptions, and STUDY.md is
  correct to label it a companion, not a fix.
- Pham et al. (2020) and Zhuang et al. (2022) are the strongest direct support for the launch-
  gate-7 determinism probe and for treating "bit-identical" as an empirical branch to test, not
  an assumption — the STUDY already does this; no gap found.
- Dunnett (1955) supports the many-to-one comparison structure; the STUDY's simulated,
  own-sd generalization of it is a reasonable extension to heteroscedastic small-n data that the
  1955 closed-form tables do not cover.
- No source found here threatens or contradicts a STUDY.md design choice; the one open item is
  verifying the exact seed-count/compute-ratio numbers in Bouthillier et al. (2021) against the
  full text (this session only reached the abstract) before those specific numbers are ever
  quoted anywhere.

## Log lines to append (research-log format; not appended per instructions — for the caller to add)

- 2026-09-27 — Jamieson & Talwalkar 2016 (arXiv:1502.07943) and Li et al. Hyperband 2018
  (arXiv:1603.06560): successive-halving/Hyperband guarantees against early-stopping misranking
  are conditional on a curve-envelope assumption, not an empirical transfer number; no
  short-vs-long-horizon rank-correlation figure exists in this literature for our setting —
  supports Delta's [L1] hedge ("ranked, not advanced"). Does not transfer as a number, only as a
  posture.
- 2026-09-27 — Cawley & Talbot 2010 (JMLR 11:2079) and Dwork et al. 2015 (Science 349:636):
  best-checkpoint-on-validation selection is a named, quantifiable optimistic bias (nested CV /
  reusable holdout are the standard fixes); Delta's split-half companion and non-quotable-screen
  firewall are lighter mitigations of the same risk, correctly labelled as companions not fixes.
  Setup differs (general model selection, not epoch-checkpoint selection under EBOPs
  constraints) — supports the concern, not a number.
- 2026-09-27 — Pham et al. 2020 (ASE, dl.acm.org/10.1145/3324884.3416545) and Zhuang et al. 2022
  (MLSys 4:316): identical-seed GPU training runs differ by up to several points overall and
  tens of points per-class from tooling alone; supports Delta's launch-gate-7 determinism probe
  and the placebo's bit-identical/divergent branch as necessary, not precautionary.
- 2026-09-27 — Picard 2021 (arXiv:2109.08203): seed-to-seed variance can be heavy-tailed with
  rare large outliers even when the mean spread is small; consistent with Delta's two-mode-seed
  scenario testing and its choice of own-sd (not pooled-sd) family test.

## Note added 2026-09-27 (after STUDY v4)

§5 quotes the STUDY v3 per-branch false-positive rates (0.10 vs. 0.26 under a 0.707-SE cross-pod
offset). STUDY v4 withdrew branch (i): the placebo is the family-test reference in every case, and
the determinism probe (E and A07, two pods, 21 epochs) only decides how the placebo row is read.
The 0.26 row no longer applies to any pre-registered rule; see `STUDY.md` change log v4 and
`review/STUDY_fixer_v3.md`.
