# STUDY constructive review, v4 (re-review, iteration 4)

Campaign: `campaigns/2026-09-26-training-batch/`. Artifact: `STUDY.md` (1,655 lines, 23,282 words;
prose_lint score 0, `review/STUDY_validators_v4.txt`). Reviewer: constructive-reviewer, 2026-09-27,
fresh context. Read: `docs/methodology/06-review.md`, `03-phases.md` Phase 1, `review/STUDY_arbiter_v3.md`,
my `review/STUDY_constructive_v3.md`, `.claude/memory/decisions.md` (2026-09-27 entries; Kai's
launch-gate answers treated as decided), experiment-log (newest three entries), research-log
(2026-07-26 deep read of arXiv:2510.24784, https://arxiv.org/abs/2510.24784; 2026-09-01 Sloot,
FastML 2026, https://indico.cern.ch/event/1654479/papers/7189055/files/16211-11_Do_BitNet_Gains_Survive_Syn.pdf).
Code traced: staged tree `code/tree/bnhgq2/{ablation.py,qat.py,config.py}`, generated configs
`code/tree/campaigns/chang0926/configs/*-s1.json`, `pilot_packs.json`. Other reviewers' v4 output
not read.

## Status of my v3 findings

| v3 | finding | status | evidence |
| --- | --- | --- | --- |
| A1 | "feasible" satisfiable by a collapsed network | **Resolved** in text and in code | STUDY l. 544-564; `ablation.py:500-529` (p_maj + k·√(p_maj(1−p_maj)/n), formula matches l. 552), `:660-669` (feasible = budget ∧ above floor ∧ above threshold), `:580-581` (rule fixed at start, asserted on resume); every generated s1 config carries `experiment.nondegenerate` with the arm's floor (a, b, d, f, r 171,526; a07-350, c 343,053; e1 85,763; cprime 4,580,398). Residual framing issue: B3 below |
| A2 | A07-at-350k family floor-bound | **Resolved** by [D21] (Kai-confirmed) | Arms table l. 227-240; A07-350 expectation pre-registered l. 642-649; generated configs a/b/d/f/r are d24/h2 |
| B1 | REPRO-CHANG xfm-n64 unused | **Resolved** | FLAG l. 1497-1502 with "weights prune" caveat |
| B2 | one-head arm | **Resolved** | Traced (l. 323-329), in the pilot (`pilot_packs.json` `[0, 1, 24, 48, 56, 57]`), paper-rule Kai row l. 1469 |
| B3 | [D20] not staged; dynamics; `i_decay_speed` | **Resolved in design and in staged code; [D25] not yet staged** | `ablation.py:438-450, 546-553` (`train_full`), `:639-644` (`stored` reload check), `:698-703` (PID asserted to read the traced EBOPs), `:722-728` (trace-share telemetry); fidelity rows l. 283-284. `i_decay_speed` appears in no config and not in `qat.py` (C1 below) |
| B4 | softmax tax beside 79.4 | **Resolved** | l. 157-158, 653-656, [L2] l. 1431-1434 |
| C1 | parameter count | Resolved | l. 190 |
| C3 | tag repetition | Resolved for the [A7] tag, **recurred** for a new tag | C5 below |
| C4 | ladder labels | Resolved | l. 762-767 |

## Category A check (none found)

Walked against the escalation list: selection is on validation only (`ablation.py:645-650, 683`;
held-out touched after the terminal epoch, l. 610-620); the tautological-feasibility loophole is
closed in text and code (above); no projection is stated as a result (trace cost l. 817-836 and
timings are labelled projections); nothing is selected on held-out; method failures ([D19] floor,
A07 headroom) were remediated, not accepted. [D19] and [D21] are Kai-decided and are not findings.

## What is done well (keep)

- [+] **The non-degeneracy rule is code, not prose.** It is fixed per run at epoch 0 and the
  runner refuses to resume under a different rule (`ablation.py:580-581`); the generated configs
  carry each arm's traced floor. This is the right way to close a §6.3 tautology.
- [+] **The PID reads the same EBOPs that feasibility uses**, enforced by an assertion rather than
  call order (`ablation.py:698-703`), with the in-training value logged beside it. Control and
  acceptance cannot silently drift apart.
- [+] **The trace-cost risk is quantified before launch** (0.66 × a training pass on CPU,
  1.66 × s_e, ≈ 15.1 d at the prior; 7,000 × 187 s = 15.15 d rechecked) and no cheaper trace is
  pre-approved. The canary measures `ebops_trace_over_epoch` in every run (`ablation.py:728`).
- [+] **The paper's ≥ 1-bit rule is carried as an honest limitation** (static table l. 343-353,
  sentence beside every distance to 79.4, [L2]); E1 in the pilot reads the only architecture that
  could run the rule's narrow reading.
- [+] **A − NB is worded correctly**: iso-EBOPs not iso-cost, learned-width not FP32 ([L10]), no
  non-inferiority claim, "not falsified at this resolution", own Holm family, H − A as an
  algebraic sum with no p. Rechecked: 1.0/0.836 = 1.20 pt; H − NB Welch t(0.975, 14)/2 = 1.07·sd
  = 3.37 pt at 3.1446 pt; 0.836·√2·3.1446 = 3.72 pt.
- [+] **[D25]** removes an unrecorded knob from A − NB and H − A before it could exist.
- [+] **A07-350's attention state is pre-registered with a defect rule** (mismatch goes to
  ml-engineer as a floor-accounting defect, l. 646-648): a descriptive arm turned into a check of
  the floor accounting.

## Category B

### B1. Size the second wave from the first wave's measured spread (the thesis comparison is otherwise fixed at an unknown resolution)

- **Current state.** A − NB, the one thesis-bearing comparison, is fixed at 8 pairs (l. 499-503).
  At zero pair correlation and the archived spread it resolves about 3.7 pt; ±1.0 pt needs
  sd_diff ≤ 1.20 pt. Wave 2 launches only after the wave-1 pilot passes and its code gates pass
  ([D24], l. 981-985), so by the time NB starts, wave-1 production will be at or near its
  epoch-500 and epoch-1,000 readouts, which give the first N=64 sd for A and the first paired
  sd_diff on this architecture and recipe (A − D, same init, same order). The STUDY uses the
  epoch-500 sd only for a Kai report on wave 1 ([D13]); it does not use it to size wave 2.
- **Improved state.** Pre-register now, with the formula fixed before any number exists (the
  pattern arbiter v3 enforced for fix 1): at the wave-1 epoch-1,000 readout (validation,
  n = 62,000), take the paired sd of A − D over feasible, non-degenerate seeds as the sd_diff
  proxy, and set the number of A/NB pairs n as the smallest n with t(0.975, n−1)/√n · sd_diff ≤
  1.0 pt, capped at a stated maximum. Regime table (review arithmetic):

  | measured sd_diff | pairs for ±1.0 pt |
  | --- | --- |
  | ≤ 1.20 pt | 8 (as designed) |
  | ≤ 1.57 pt | 12 |
  | ≤ 1.88 pt | 16 |
  | ≤ 2.01 pt | 18 |
  | > ~2.1 pt | no affordable n; the report states in advance that A − NB cannot resolve 1 pt |

  Two constraints to state: pairing needs extra A seeds (9..n), each a full 7,000-epoch run, so the
  cap and the extra A seeds are a Kai row; and the STUDY's own caveat applies (an epoch-1,000 sd may
  understate the terminal spread, l. 522-523), so the rule sizes a floor, not a guarantee. The lab
  already sizes the method-atlas screen from the anchor's epoch-500 sd (`decisions.md`,
  2026-09-27, method atlas K2), so this is house practice, not a new idea.
- **Why.** §6.3 Q4: "can it separate the arms at the gap it claims, given the measured sd?" The
  design is the one place in the campaign where the sd will have been measured before the
  thesis-bearing arm launches; leaving n at 8 regardless wastes that.
- **Effort.** Low (text and one Kai row); compute medium to high if the rule adds seeds.

### B2. Lead the A − NB report with the bound the data put on the cost of binary, and state the directional prior

- **Current state.** Weight-type claim: falsified if the interval lies below 0, otherwise "not
  falsified at this resolution" with a 1.0-pt descriptive line (l. 708-717). At a 3.7-pt
  resolution the likely outcome is "not falsified" whatever the true gap, and a reader skimming
  will take away the thesis-favourable sentence.
- **Improved state.** Pre-register the headline sentence as the lower 95 % bound: "at 350k EBOPs
  (iso-EBOPs), binary costs at most |L| pt of top-1 accuracy against learned-width weights on this
  model (n pairs, 95 %)". "Not falsified" stays as the claim verdict beneath it. Add one sentence of
  prior: the direct-neighbour result (Sloot, FastML 2026, research-log 2026-09-01) found HGQ
  learned-width above binary on AUC (different task, 16 HLF features, MLP; never tabulated beside
  ours), so the expected direction is A ≤ NB and a wide interval is not support.
- **Why.** Honest framing: a gap hidden behind a wide interval is the §6.3.3 pattern; the bound is
  the number a referee would quote.
- **Effort.** Low.

### B3. State what "non-degenerate" means numerically: about 21 % accuracy, "not constant", not "tags"

- **Current state.** The budget claim and the pilot A rule read "reaches 350k non-degenerately"
  (l. 119-121, 632-633, 884). The threshold is left symbolic until PREFLIGHT.
- **Evidence.** Class fractions of the ROC-test labels (`bnjettag/roc-results/r14/n64/FP32-s1.npz`,
  `y`, n = 260,000; review arithmetic, used only as a proxy for the gated `y_val`, which is drawn
  from the training files): 0.2016, 0.1941, 0.2009, 0.2011, 0.2023; p_maj 0.2023, threshold
  0.2023 + 5·√(0.2023·0.7977/62,000) = **0.2104**. A model with one live 1-bit input channel and a
  mean pool will clear that bar.
- **Improved state.** One sentence beside the budget claim: "non-degenerate means validation
  accuracy above about 21 % (p_maj + 5 SE, value fixed at PREFLIGHT), i.e. not a constant
  classifier; it does not mean the model tags well. The accuracy of every feasible seed is
  reported beside the count." Same sentence at the pilot A rule.
- **Why.** The rule closed a tautology; its name now invites a stronger reading than it supports.
- **Effort.** Low.

### B4. Offer an FP32 E arm as a Kai option (the thesis's own reference on this recipe)

- **Current state.** The thesis compares binary with full precision (project context, axis (a));
  neither wave has an FP32 arm; [L10] notes NB is not FP32 and stops there. Nothing in "Where I am
  not sure" offers one.
- **Available.** The builder already has the path: `quant.weight: "none"` builds float weights and
  float activations on the same skeleton (`qat.py:374-376, 396`; accepted by `config.py:40`).
- **Caveat (not traced).** The runner's budget path on an unquantized model is unconfirmed: what
  `compute_ebops` returns, and whether ND rule (b) (EBOPs − floor > 0) would mark every checkpoint
  "degenerate" if EBOPs is 0. An FP32 arm needs the ND key absent or a float-specific rule;
  ml-engineer confirms.
- **Improved state.** A Kai row: "FP32 E (no quantizers, no EBOPs target, Chang schedule, 8
  seeds; cheap version 4 seeds to 2,000 epochs). A − FP32 is a labelled package (binary weights
  plus the 350k budget against float, unconstrained)." Not a default.
- **Why.** §6.3 Q3: a referee or advisor reading "binary stays close to full precision" will ask
  for the full-precision number on the same model, split and recipe; Round-14's FP32 79.1 % is
  archived and not comparable ([L6]).
- **Effort.** Low for the row; medium to confirm the runner path; 8 runs of compute.

### B5. Give the second wave an epoch-500 rule, as wave 1 has

- **Current state.** Wave 2 has a 10-epoch canary and then "interim readouts ... go to Kai"
  (l. 1006-1009), with no criterion. Both arms run dynamics never run before: NB starts from kbi
  `b0` 4 weights (init EBOPs above A's, [A22]); H runs the PID on `xfm` for the first time
  (l. 408-410). Wave 1 received a pre-registered epoch-500 pilot rule for exactly this reason.
- **Improved state.** Mirror the wave-1 A rule at the wave-2 epoch-500 readout: "if no NB seed
  (respectively H seed) has a feasible, non-degenerate checkpoint by epoch 500, the arm's case goes
  to Kai with options (continue, H on the open-loop schedule, stop)"; nothing else is decided on
  that readout.
- **Why.** 876 projected pod-hours ride on a 10-epoch check; the rule costs nothing and prevents a
  silent 7,000-epoch infeasible arm.
- **Effort.** Low.

### B6. Prefer NB in the wave-1 seed blocks when its gates pass in time, conditional on the canary's memory reading

- **Current state.** Listed as an alternative (l. 993-996, 1476). The default crosses launch date,
  code sha and possibly GPU class for the thesis pair (l. 435-436), and overlap puts 14 pods up
  against Kai's 8-10.
- **Improved state.** State the preference order: if NB's gates pass before wave-1 production and
  the canary shows K=7 fits at batch 2,790, NB-s joins wave-1 pod s (A − NB then shares GPU,
  date and pod; no pod overage); otherwise the default. Do not make it the default before the
  canary: the K=3 fallback is already "not unlikely" (l. 929-932).
- **Why.** Removes the only confounds A − NB carries besides the object of study, at zero run cost.
- **Effort.** Low (text); the decision is at the canary.

## Category C

- **C1. Stale "not staged" sentences.** Confound 10 (l. 469: "the staged code still traces 256"),
  [D20] (l. 1170-1171: "does not implement [D20] yet"), [A21] (l. 1353-1355) and the experiment-log
  stub ("staged code still traces 256 jets") are out of date: `ablation.py:438-450, 546-553,
  639-644` implement `train_full` and `stored`, and `chang0926-a-n64-s1.json` carries them
  (commit fc89f7d). Say "staged in patches 0015-0023; the shipped tree is the PREFLIGHT gate".
  Conversely **[D25] is not staged**: no generated config has `quant.i_decay_speed`, and `qat.py`
  has no reference to it; say so explicitly rather than only "gates re-run under it". Low.
- **C2. PID signal is no longer open.** [D20] l. 1162-1164 asks ml-engineer to state whether
  BetaPID reads the traced EBOPs; the staged runner asserts it does (`ablation.py:698-703`). Low.
- **C3. Selection description vs code.** l. 559-561: "the runner's selection is unchanged:
  model_best has the highest validation accuracy among (a) checkpoints". The code selects among
  (a)-(c) (`ablation.py:664, 683`) and the [A19] copy likewise (`:688`). Outcome-equivalent
  (if the (a)-best fails (c), every (a) checkpoint does), but the sentence is wrong. Also note that
  W&B `budget_met` now means non-degenerate feasible (`:711`), and `ebops_budget_met` is the raw
  test (`:719`), so dashboards are not misread. Low.
- **C4. Holm family carries a foregone comparison.** A − A07-350 (and largely C − A07-350) is
  fixed in sign by construction (A07-350 has no data-dependent attention and at most 3
  per-constituent input bits, l. 642-648). Move it to descriptive; Holm over A − B, A − D, A − F
  and C − A07-350 (or three) gains a little power for the rungs that are open questions. Low.
- **C5. Presentation.** The document grew from 14,534 to 23,282 words since v3. The tag "Kai
  request, 08:40" appears 29 times in running prose, the pattern v3 C3 removed for the [A7] tag;
  keep it on the [D22]-[D24] entries, the second-wave section header and the change log. The
  superseded FLAG block (l. 1537-1549) can shrink to one line pointing at [D22]-[D24]. Low.
- **C6. Which open Kai rows block wave-1 production.** Paper-rule variant, arm B and the
  six-item last row read "open, before production" (l. 1469, 1471, 1477) without saying whether
  the defaults stand if Kai does not answer. Split the table into "blocks wave-1 production",
  "blocks wave 2" and "default stands unless Kai objects". Low.
- **C7. Recoverable information.** `activation_widths.jsonl` already holds every epoch's validation
  accuracy and EBOPs. Report per run the selected epoch and its cosine-cycle index, and plot the
  best-feasible validation accuracy per cycle (14 points per run). It shows whether the seed spread
  is driven by which restart the selection lands in (a symptom, not intrinsic spread), and whether
  7,000 epochs was needed, which is evidence for any future [D15] choice. Low.

## §6.3 answers

1. Conventions: complete; deviations flagged (split, metric, selection metric).
2. Reference table: complete and labelled; REPRO-CHANG now used with its caveats.
3. A competing group would add a full-precision arm on the same model and recipe (B4) and would
   size the thesis comparison from the measured spread (B1).
4. Uncertainties honest in both directions; resolving power stated with its consequence. The
   thesis-bearing comparison can be sized better at no design cost (B1) and reported by its bound
   (B2).
5. Limitations with attempts: the floor, the A07 headroom and the paper's rule were each attacked
   with a trace, not accepted.
6. Context with a pull: not possible (no gated 90/10 N=64 record), stated.

## Disputed facts for the investigator

None blocking. One question for ml-engineer, not the investigator: what `compute_ebops` and the
ND rule do on a `quant.weight: "none"` model (B4), only if Kai takes the FP32 option.
