# STUDY physics review, v6: 2026-09-26-training-batch

Reviewer: physics-reviewer (fresh context). Artifact: `STUDY.md` (2,046 lines, status `designed`,
last amendment "Kai request (second set)": arm FP32-E [D26], 80 runs). No compiled PDF sits beside
the artifact. At STUDY no result exists, so the checks apply to the plan: arms, seeds, the planned
intervals and the pre-registered figures.

## Figures

No figure exists yet. Each pre-registered figure (Falsifier, "Figures", l. 1035-1069) is listed
below with its status and its spec checked against the figure checks.

| figure (pre-registered) | status | spec check |
| --- | --- | --- |
| Primary measurement: per-seed A ROC-test accuracy, seed mean, 95 % t-interval, lines at 79.4 / 78.4 / 79.8 / 77.9 % | not made; spec checked | split, n and k in the caption and legend; external lines labelled single-model. OK. FP32-E is not drawn (C6) |
| Recipe ladder: paired-gap panel A − D, D − R, A − R, A1000 − R, D1000 − R | not made; spec checked | paired Δ with a t-interval and n_pairs; GPU class in the caption. OK |
| Per-class ROC on ROC-test, log mistag axis, seed band (sd, ddof = 1), A and R named; A07-350 and C in a separate panel | not made; spec checked | log mistag axis, split and n, ddof and k all specified; budgets not mixed on one axis. OK |
| Per run: selected epoch, cycle index, best-feasible validation accuracy per cycle | not made; spec checked | labelled "validation, n = 62,000". OK |
| Two accuracy-versus-EBOPs ladders (E: B, A; A07: A07-350, C) with paired-gap panels | not made; spec checked | EBOPs above the 0-bit floor on each rung; infeasible rungs drawn as empty markers; degenerate seeds counted. OK |
| Attention state per arm (Q/K and V at 0 bits, entropy / log 64), FP32-E entropy only | not made; **spec not backed by code** | no softmax or entropy tap exists in `code/tree`, and the fp32 branch records no taps at all (`bnhgq2/qat.py:471-472, 488-489, 503-505`). See B1 |
| Validation − held-out accuracy per run | not made; spec checked | OK |
| Interim readouts | not made; spec checked | labelled validation. OK |
| Second wave: paired-gap panel A − NB (1.0-pt line), Welch H − NB and H − A, plus A − FP32-E and NB − FP32-E | not made; spec checked | an iso-EBOPs gap (A − NB) and a package gap (A − FP32-E) share one Δ axis, which invites the comparison the text forbids (C5) |
| Second wave: per-class ROC with A, NB, H, FP32-E named | not made; spec checked | OK (inherits the log axis and band spec) |
| NB per-layer weight-width distribution | not made; spec checked | OK |

## Verified

- Round-14 N=64 sizing numbers (reference table, l. 301), recomputed from
  `bnjettag/roc-results/r14/n64/{W1A8,FP32}-s{1,2,3}.npz` (keys `y`, `score`; 260,000 × 5):
  W1A8 67.18 / 72.64 / 67.21 %, mean 69.01 %, sd 3.145 pt (ddof = 1); FP32 79.42 / 78.83 / 79.10 %,
  mean 79.11 %, sd 0.297 pt. These match the artifact's 69.0 ± 3.1 and 79.1 ± 0.3.
- Threshold (c), "about 0.21" (l. 828-832): the ROC-test class fractions from the same file are
  0.2016 / 0.1941 / 0.2009 / 0.2011 / 0.2023, so p_maj = 0.2023 and p_maj + 5·√(p_maj(1 − p_maj)/62,000)
  = 0.2023 + 0.0081 = 0.2104. This matches the artifact. The PREFLIGHT value on the gated `y_val`
  is still to come.
- Interval arithmetic: t(0.975,7)/√8 = 0.836; t(0.975,5)/√6 = 1.05; 0.836·√2·3.14 = 3.71 pt;
  Welch H − NB 1.07·sd, which is 3.37 pt; the sizing table (8 / 12 / 16 / 18 / 20 pairs at
  1.196 / 1.574 / 1.877 / 2.011 / 2.137 pt) is correct and conservatively rounded down;
  A − FP32-E at the archived spreads gives √(3.14² + 0.30²)·0.836 = 2.64 pt paired at zero
  correlation and 2.63 pt Welch. The artifact's "about 2.6 pt" holds. The McNemar reach values
  (0.125 / 0.0625 / 0.031 / 0.016) are correct.
- `code/evidence/cpu_gate_d25.log:116`: C′ `I_DECAY_OK ... config None quantizers 0 values []`, as
  cited. The log ends `PREFLIGHT_ALL_PASS 58 production 56 pilot_only 2`, so the 8 FP32-E configs
  are not yet in any gate, consistent with [A25] ("the gate's production count rises by 8").
- FP32 build (`qat.py:473-474, 490-491, 499-500, 511-516`): the dummy weight, datalane and stream
  quantizers, the dummy exp and inv inputs and the fixed `_table(1, 20)` outputs match the
  inventory in [D26].
- `code/evidence/a17_pairing_d25_8seeds.json`: A, B and others against F, `n_shared: 15`, only
  `pos_enc/pos_table` differs, `differing_shared: []` at every seed.

## Findings

### (A) must resolve

**A1. The two thesis-bearing headlines are worded as bounds but are computed over surviving
seeds only, which biases them in binary's favour.**
- *Attack.* The weight-type headline (l. 924-929) reads "binary costs at most |L| pt ... (n
  pairs, 95 %)". The precision-package headline (l. 981-985) reads "cost at most |L| pt against
  the same E model in unconstrained FP32". Both are computed over "seeds feasible (a to c) and not
  diverged in both arms" (l. 772-775, 965), and both allow 6 or 7 pairs (l. 974, 993).
  - For FP32-E, (c) is the only filter, and an FP32 model passes it almost surely, so every pair
    that is lost is an **A-side** failure: a binary seed that diverged at a 3e-3 restart, never
    reached 350k, collapsed to a constant classifier, or failed certification.
  - These are the failure modes the Round-14 N=64 binary spread (67.18 / 72.64 / 67.21 %) warns
    about. They are also the seeds on which binary costs the most.
  - Excluding them makes "at most |L|" anti-conservative, which is the direction that favours the
    thesis. A − NB has the same problem whenever A loses more seeds than NB.
  - The artifact already recognises survivor bias for the arm mean (l. 769-771) and for A − 79.4
    ("upper estimate", l. 855-857), but it does not carry that bias into the two gaps the thesis
    will be quoted from.
- *Evidence.* `grep -n "survivor\|upper estimate" STUDY.md` returns only l. 45, 770-771 and
  855-856. The A − NB section (l. 922-977) and the FP32-E section (l. 979-994) have no such
  clause.
- *What settles it.* A text rule, pre-registered before any number exists:
  - the "at most |L| pt" wording is used only when all 8 pairs survive;
  - with 6 or 7 pairs, the headline reads "among k surviving pairs", and the count of A-only
    failures (and NB-only or FP32-E-only failures) is printed beside it;
  - one pre-registered worst-case sensitivity line is added: each A-only failed seed imputed at
    the surviving A minimum (or at p_maj), paired with its partner's accuracy;
  - for A vs FP32-E, the paired feasibility counts are reported as they are for A vs NB (l.
    971-973).

### (B) should address

**B1. The required attention-entropy diagnostic has no implementation item.**
- *Attack.* The diagnostic is "required beside every accuracy number" (l. 1005), is computed
  "from one validation forward pass with the softmax tap" (l. 1032), and FP32-E is promised
  "entropy only" in the attention figure (l. 1069). No [A] constraint asks for the tap.
- *Evidence.* A grep of `code/tree` for entropy, softmax taps or attention probabilities finds
  nothing. `qat.py` records taps only for dense and einsum inputs, and only when `not fp32` (l.
  471-472, 488-489, 503-505). The Deep-Set collapse reading, which is how the paper's MHA-64 failed,
  depends on this number.
- *What settles it.* Add an [A] item that names the softmax-output tap (layer path) for both the
  binary and fp32 builds, with a CPU unit test: a uniform-logit input gives entropy / log 64 = 1,
  and a one-hot logit input gives about 0.

**B2. The [A25] FP32-E pairing gate can pass on a partial intersection of variables.**
- *Attack.* `matching_initialization` (`bnhgq2/ablation.py:70-90`) builds its reference from the
  arm's own config and copies by `v.path`. `QEinsumDense`/`QDense` and
  `BitQEinsumDense`/`BitQDense` can name variables differently.
  - A `kernel_hashes` comparison of A-s against FP32-E-s that looks only at shared paths can
    report "equal" over a subset of the kernels.
  - Separately, `ablation.py:74-76` rewrites the reference quant block and calls
    `calibrate_activations` on the reference. On an fp32 reference the taps are empty, and
    whether that path and the assertion at `:90` (`expected_binary_layers(cfg)`) hold for
    `quant.weight: "none"` is not shown.
- *Evidence.* The A-vs-F evidence records `n_shared: 15`. [A25] says "variable paths matched"
  but fixes no count.
- *What settles it.* [A25] asserts at every seed that `n_shared == 15` (the A kernel and bias
  set) and that `only_in_arm` and `only_in_f` are empty, and shows that `matching_initialization`
  runs on an FP32-E config. Otherwise the gate reports UNPAIRED and A − FP32-E goes to Welch, as
  pre-registered.

**B3. FP32-E config hygiene is left implicit, and the build refuses A's keys.**
- *Attack.* `qat.py` raises when `act_overflow`/`softmax_quant` are non-default without binary
  weights and `act_calib="free"`, and raises on `i_decay_speed` without WRAP (l. 413-429). An
  FP32-E config generated field for field from A (as [D26] reads, "Arm A at seed s ... with
  `quant.weight: none`") will not build. [A25] says "carry only keys the path reads" but does not
  list them.
- *What settles it.* [A25] names the keys stripped from A's config for FP32-E (at least
  `act_overflow`, `softmax_quant`, `i_decay_speed`, and any `act_calib`/`act_policy` the fp32 path
  ignores), and PREFLIGHT prints the diff of FP32-E-s1 against A-s1. The CPU gate would catch
  this, so it is B, not A.

### (C) suggestions

- **C1. Stale [D24] DECISION block.** L. 1961-1963 still reads "own Holm family {A − NB, H − NB}"
  and "4 pods at K=4". The body (l. 915) and [D24] (l. 1534-1536) now have {A − NB, H − NB,
  A − FP32-E} and K=6. Update the block so a reader of the FLAG table does not get the old
  family.
- **C2. Stale second-wave Cost bullet.** L. 1297-1298 says "16 runs at K=4 on 4 pods ≈ 876
  pod-hours". With FP32-E packed at K=6, it is 24 runs on the same 4 pods, with the same
  pod-hours at the prior (the FP32-E bullet, l. 1335-1338, says so). One clause fixes it.
- **C3. FP32-E is recipe-matched, not tuned.** It runs Chang's HGQ-tuned schedule on a norm-free
  FP32 model with no separate tuning. That is the right choice for a matched package, but REPORT
  should say "at this recipe" beside A − FP32-E, so the gap is not read as against a tuned FP32
  ceiling. As a sanity anchor, the report could print FP32-E's seed mean beside the archived FP32
  N=64 spread. This is context only and not a comparand (different split, gate and architecture).
- **C4. No per-class paired gaps.** Per-class AUCs sit beside every macro number, which is good.
  The A − NB and A − FP32-E gaps are pre-registered on accuracy only. A descriptive per-class
  paired AUC gap (five numbers, t-interval, no p) would show whether a binary cost sits in one
  class, for example q against g.
- **C5. Separate the iso-EBOPs and package gaps in the second-wave panel.** Draw A − NB and
  A − FP32-E in separate panels, or with distinct marker families and a divider, so the figure
  does not invite reading a package gap against an iso-EBOPs gap.
- **C6. Primary-measurement figure.** Adding FP32-E's seed mean and interval as a band would put
  the "close to full precision" reading where readers look first.
- **C7. Scope reminder, already stated and worth keeping visible in REPORT.** No W8A8 arm and no
  A8 → A6 → A4 ladder, and no LUT, DSP or latency ([L7]). This campaign bears on neither thesis
  axis 2 nor the "no DSP" claim. It bears on axis 1 only for E at N=64, at iso-EBOPs (A − NB)
  and as a package (A − FP32-E).

## What could go wrong that the design would not catch

- A07-350's attention state is fixed by the floor. That is disclosed and handled.
- Rule (c) at about 0.21 only excludes constant classifiers, so the budget claim at 6/8 is weak
  evidence of tagging. The artifact says so plainly (l. 827-830).
- The paired designs rest on the kernel-hash gates. The A-vs-F gate records its intersection
  size, but the FP32-E gate does not yet (B2).
- The one place where the design would report a flattering number without flagging it is A1.

## Verdict

Approve for PREFLIGHT and the pilot conditional on A1. A1 is a pre-registered wording and
sensitivity rule, and it decides approval because it governs the sentence the thesis will be
quoted from ("binary costs at most |L| pt"). As written, a binary seed's failure would shrink
that sentence rather than widen it.
