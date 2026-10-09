# STUDY physics review v1 (fresh-context referee)

- Artifact: `campaigns/2026-10-05-pilot-program/STUDY.md`, sha256 `27d43c63…0e86` (325 lines, amendment A2 14:14 JST).
- Also read, as cited data: `campaigns/2026-10-02-chang-option-c/code/tree/campaigns/chang1002c/static_floors.json`
  and `campaigns/2026-10-05-pilot-program/dev/README.md` (NB floor table). Both are structural traces on a
  synthetic sample, not results.
- I did not read the methodology or conventions. Every number below is quoted from those files or is
  arithmetic on them, and is labelled as such.
- Grades: A = must fix before launch; B = should fix; C = note.

Verdict: **ITERATE.** R1 is a reasonable mechanism screen. The automatic production trigger, though,
can commit 960 GPU-h on evidence that is partly the evidence used to select the candidate. It can also
fire at a budget that has no L1 argument behind it. Finally, "useful" has no physics reference.

---

## A (must fix before launch)

**A1. The production trigger reuses selection seeds as confirmation seeds (§7.3-7.4, §9.1).**
W and V_bin are chosen as the best of 6 (or 5) arms on seeds 1-2. Take the case W = NB. V_bin then
gets only seed 3, and P350's "V_bin healthy on every seed run at 350k (n ≥ 3)" is satisfied by seeds
1, 2 and 3, two of which are the seeds that won the selection. The binary arm is the thesis arm, and it
would reach 960 GPU-h on **one** independent confirmation seed. Even with fully fresh seeds, 3/3 has a
Clopper-Pearson 95 % lower bound of 0.292 (the STUDY's own §6 arithmetic, recomputed). So the trigger
allows a production launch where the true healthy rate could be near 0.3. Each production arm runs 8
seeds, so many production seeds would then be collapsed.
*Fix:* count only seeds not used to choose W or V_bin, and require ≥ 3 fresh healthy seeds for each
production arm. Alternatively, let P350 always stop for Kai when W = NB.

**A2. Prec can auto-launch at a budget that does not fit the thesis (§8, §9.2, D6 CONFIDENCE LOW).**
The thesis is about an L1-sized cost of about 350k EBOPs. r_rec can be any bracket rung up to 5M,
which is 14× that cost, and §9 would then launch 16 pods × 7,000 epochs there without asking. The
artifact makes no case that 1M, 2M or 5M EBOPs is still L1-deployable: no LUT, latency or II estimate,
and no reference design at that budget. A Prec production answers a different question (D6 says so).
*Fix:* Prec always stops for Kai, or §9 pre-registers an upper bound on r_rec with a stated
hardware justification.

**A3. "Useful accuracy" has no physics reference (§5, §9, D5).**
The 0.50 production floor comes only from earlier internal pilots ("above every 350k pilot checkpoint,
below the 5M/unconstrained 0.65-0.66"). The artifact quotes no external anchor. Two are missing: the
accuracy Chang/Sun et al. report at 350k EBOPs on this dataset and N, and an in-lab full-precision or
learned-width reference on the same split. A physics referee will ask what fraction of the
learned-width performance at the same cost the binary tagger keeps. The floor should be expressed
against that number, and the source line should be quoted. Without that reference, "healthy, ≥ 0.50"
can launch production on a tagger that is far from useful for a trigger. This gate commits 960 GPU-h,
so the anchor must be fixed before data exists (§12 forbids changing it afterwards).
*Fix:* add the reference value (source, metric, split, n) to §9 and state the floor relative to it.
A background rejection at a fixed signal efficiency would also be the more trigger-relevant metric
alongside top-1. If no reference exists yet, say so and make P350 stop for Kai.

---

## B (should fix)

**B1. Uniform attention is mean pooling, not failure. A no-attention control is missing.**
A head at entropy 1.0 averages over the constituents, so a "collapsed" one-block transformer is a
Deep-Sets-style mean-pool tagger with a binary MLP. Mean-pool and Deep Sets taggers are competitive
baselines for jet tagging. `healthy` therefore measures whether attention is used, not whether the
tagger is good. The entropy-only stop (§5) partly guards against this, but the deeper question is not
asked: at 350k, does a binary mean-pool model (attention removed, budget given to the MLPs) reach the
accuracy of the "collapsed" transformer, or exceed it? If it does, the 350k collapse is the
optimizer pricing out a block that buys nothing at this budget. That is a design finding, not a
training pathology, and it changes what H1-H5 are explaining. *Suggest:* one extra R1 pod (23 → 24,
within the cap). Also state how padded constituents are handled: is attention masked, and is
entropy normalised by log 64 or by log n_real? A mask-free uniform head averages zero-padding, which
is a different physics statement.

**B2. The static floors offer a third, discriminating prediction that is not registered.**
`static_floors.json` gives, for E: 0-bit 171,526, attention-narrow 368,134, and all activations
1-bit-alive (`one`) 619,198. For A07 the values are 343,053, 605,197 and 1,005,741. H2 and the H3
corollary both point to E 500k / A07 1M (§2 admits they cannot be told apart in R1). A
"whole-network starvation" alternative instead predicts the first rung ≥ `one`: **E 750k, A07 2M**
(arithmetic on the floors and the registered rungs). The R1 ladders can separate that alternative
from the attention-only explanation at no extra cost. Register it as an H2′ row now. The
cross-architecture H2 test also assumes that *absolute* headroom is the relevant variable. A07 has
about twice the parameters (61,951 vs 31,735, `static_floors.json`), so headroom per quantized site
or relative headroom predicts a different A07 rung. State which scaling is meant and why, or the
A07 test checks one arbitrary scaling.

**B3. Single-seed ladders cannot support or refute monotonicity (§4 rows 3-4, §6 H2, §7.1).**
The prior state shows that health at a fixed configuration is bimodal across seeds: A-s1 is
degenerate while A-s2 is non-degenerate, at the same 350k. With one seed per rung, a non-monotone
ladder or a recovery rung that is off by one is the expected outcome of seed noise. H2's
"supported" and "refuted" rows are then too strong for R1. In addition, r1 is the lowest rung where
seed 1 alone is healthy, so one lucky seed at a low rung puts the R2 bracket below the true
transition. R2 checks only {below r1, r1} and never the rung above. *Suggest:* in R1, H2 reads
"descriptive" only. Alternatively, r1 requires two consecutive healthy rungs, or the R2 bracket is
{r1, rung above}.

**B4. All the 350k mechanism tests share one control, and multiplicity is not considered (§6).**
H3, H4 (two arms) and H5 are each "supported" only if A350-C is 0/2. If H1 is true (A350-C healthy),
none of the mechanism hypotheses can be tested at 350k, and the design should say what it then
learns. If instead every arm has a true healthy rate of 0.5, the pattern "2/2 vs 0/2" occurs with
probability 1/16 per comparison. Across about 5 comparisons against the same control,
1 − (15/16)^5 = 0.276 (arithmetic on a hypothetical rate, not data). Moreover, W is the argmax
across these arms. State the family-wise reading, or label every R1 "supported" as a lead for R2,
not a finding.

**B5. The H3 arm changes headroom as well as attention (§4 row 7).**
With q, k, v floored at 1 bit, the zero floor rises to 269,830 and the headroom falls to 80,170,
against 178,474 for A350-C (STUDY §4 and §2 arithmetic). The rest of the network gets less than half
the budget. "Refuted" (qkv1 unhealthy) is therefore confounded with starving the FFN and embedding.
§2 also says that "R2's direct H3 arm separates" H2 from H3, but §7 gives qkv1 seeds 3-5 only if it
is W. Nothing guarantees H3 ≥ 3 seeds in R2. *Suggest:* either guarantee the H3 seeds, or drop the
claim that R2 separates them. A qkv1 arm at a matched headroom (budget raised by
269,830 − 171,526 = 98,304 to 448,304) would remove the confound.

**B6. 500 epochs measures the low-LR tail of one cycle, not production behaviour (§3, §14 last bullet).**
The study itself notes that b5 first met the budget 259-389 epochs after the start (§4 row 6), so at
most about 110-240 on-budget epochs are judged. Those epochs fall in the low-LR half of cosine cycle
1. D-s1 regrew attention after epoch 400. Production runs 7,000 epochs, which is 14 cycles, with 13
warm restarts at peak 3e-3 that can revive or destroy attention. Nothing in the program checks
whether health at epoch 500 predicts health at 7,000. *Suggest:* add `first_feasible_epoch` (number
of epochs at budget) to the readout, which H5 already takes by hand. Extend at least the
production-candidate arm through one restart (to 1,000 epochs) before the trigger, or state that
the trigger assumes health is stable across restarts.

**B7. H5 tests prunability and initialisation, not "binary per se" (§6 H5, C5).**
NB can drive weights to 0 bits, and binary cannot. In the dev floor table, NB with all activations
alive and 0-bit weights costs 368,134, against 619,198 for binary with all activations alive
(`dev/README.md` NB table). At 350k, NB can therefore buy alive activations with weight sparsity,
which is a qualitatively different region and not a cleaner version of the same network. The 4-bit
initialisation adds a second difference. A positive H5 then says "a ternary/pruned-capable weight
fixes it", which bears on the ternary baseline. Name it that way. A one-pod NB arm with a 1-bit
initial width would separate the trajectory effect.

---

## C (notes)

- **C1. The thesis paragraph confounds architecture and budget.** The collapsed pilots are the E
  family (d24, 2 heads) at 350k, and the healthy one is A07 (d32, 4 heads) at 5M (STUDY §1 prior
  state). "A 5M-budget network trained normally" should name the architecture. The E ladder is what
  actually makes the contrast.
- **C2. A07 at 350k is arithmetic, not an experiment.** Its headroom is 6,947 (§2). Label that pod a
  sanity check of the floor model.
- **C3. Related work.** Binarised and low-bit transformers have a documented attention-degradation
  failure (BiBERT, Qin et al., ICLR 2022; BinaryBERT, Bai et al., ACL 2021; BiT, Liu et al., NeurIPS
  2022; Q-ViT, Li et al., NeurIPS 2022). This collapse is different (0-bit Q/K *activations* priced
  out by an EBOPs controller), and the STUDY should say so in one line, because a referee will ask.
- **C4. EBOPs comparability.** The thesis compares to Chang/Sun at the same EBOPs. A 1-bit weight
  costs one EBOP per activation bit, but on an FPGA it maps to LUT add/sub logic and not to a
  multiplier. EBOPs-matched does not have to mean resource-matched. That is out of scope here, but
  the no-DSP claim should not rest on this program.
- **C5. H4 tests only timing.** Squeeze *rate* (PID gain) is the obvious alternative and is not
  tested. The LR-phase confound is already recorded (A2/B5).

Checked and correct: the headroom arithmetic in §2, the H2 rung mapping, and the CP bounds
(0/3 upper 0.708, 3/3 lower 0.292).
