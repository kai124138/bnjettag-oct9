# DRAFT for RESEARCH.md — Round 14 (l1x3 constituent-count sweep)

*Draft prepared 2026-08-03 by `paper-writer`. Not spliced into `RESEARCH.md`; the main
session places it after §5″ and adds the §8 rows listed at the end. Numbers audit at the
bottom of this file.*

---

## 5‴. Tagging efficiency — Round 14 (l1x3: L1-realistic 3-feature inputs, N ∈ {8,16,32,64})

**A different input representation, so a self-contained table.** Rounds 5–8 and the FINAL
campaign use the 16-feature Zenodo constituent record. Odagiu et al. (arXiv:2402.01876)
argue that a Level-1 tagger only has the constituent four-vector, i.e. **(pT, η_rel, φ_rel)**;
the other 13 columns are offline-style re-encodings of the same information. Chang's group
uses that 3-feature set, so our 16-feature numbers are not input-matched to theirs. Round 14
(`l1x3`) therefore moves to **(N, 3)** inputs and sweeps the constituent count
N ∈ {8, 16, 32, 64}.

**These numbers are `l1x3`. They are comparable to each other and to Odagiu/Chang-style
3-feature baselines, and must never be placed in the same comparison as any 16-feature table
in §2.** Data, split and metric are unchanged (public HLS4ML LHC Jet
5-class, held-out `val/`, **ROC-test macro one-vs-rest AUC, n = 260,000**) — only the input
columns differ.

**Design (pre-registered 2026-08-01, decisions.md).** Features resolved by exact suffix
(`pt` ≠ `ptrel`), subset applied *after* the pT sort so particle ordering is untouched.
Recipe = the r8-`small` recipe verbatim (d_model 32, 2 layers, 4 heads, FFN 64, norm-free,
`input_std`, 101 epochs, LR 2e-5, early stop 15, trainable activation calibration) — the
**only** change vs rounds 7/8 is the input set, so input-set and N effects stay attributable.
Grid: N ∈ {8,16,32,64} × {FP32, W8A8, W1A8, W1A6, W1A4} × seeds {1,2,3} = 60 runs, W&B
project `BNJetTagAug`, runs `r14-l1x3-n<N>-<variant>-s<seed>`. Selection: best val macro-OvR
per run; **reporting metric is ROC-test macro-OvR, seed mean ± sample std over 3 seeds**, with
an uncertainty interval required before any cross-arm claim. All 60 models passed the
`verify-roc` gate (60/60 recomputed from their `.npz` against the stored tables, 2026-08-03).

### Accuracy

ROC-test macro-OvR AUC (l1x3, n = 260,000), **mean ± sample std over 3 seeds**:

| N | FP32 | W8A8 | W1A8 (the model) | W1A6 | W1A4 |
| --- | --- | --- | --- | --- | --- |
| 8  | 0.8864 ± 0.0005 | 0.8862 ± 0.0009 | **0.8712 ± 0.0016** | 0.8689 ± 0.0020 | 0.8534 ± 0.0012 |
| 16 | 0.9128 ± 0.0013 | 0.9124 ± 0.0014 | **0.8956 ± 0.0002** | 0.8910 ± 0.0009 | 0.8693 ± 0.0021 |
| 32 | 0.9374 ± 0.0017 | 0.9358 ± 0.0011 | **0.9052 ± 0.0079** | 0.9022 ± 0.0009 | 0.8833 ± 0.0013 |
| 64 | 0.9486 ± 0.0012 | 0.9448 ± 0.0011 | **0.9028 – 0.9251 †** | 0.9136 ± 0.0061 | 0.9073 ± 0.0010 |

† **N = 64, W1A8 is quoted as a seed range, not a mean.** Its three seeds are 0.9028 /
0.9251 / 0.9084; every pairwise seed difference excludes zero under a paired test-set
bootstrap by 30–60× the test-set noise, so the spread is genuine **training instability**,
not evaluation noise. One high outcome and two low ones over 3 draws has no meaningful mean —
the arithmetic mean (0.9121) and its sd (0.0116) are recorded for completeness but are
provisional and should not be used in a comparison. The same caution applies more mildly at
N = 32 (range 0.8976 – 0.9134, sd 0.0079). All other arms have seed sd ≤ 0.0021 and are
safely quotable as mean ± sd.

Two noise sources were quantified for every comparison: seed-to-seed training variance
(3 seeds, t-interval, df = 2) and finite-test-set variance at fixed weights (paired
multinomial bootstrap, B = 400). Test-set-only sd of a single model's macro AUC is
**≈ 0.0004**; seed sds range 0.0002 – 0.0116. **Every comparison in this campaign is
seed-limited, not statistics-limited** — adding test jets would not sharpen any of them.

**What round 14 establishes (all ROC-test, l1x3, this table only):**

- **The binary penalty is real at every constituent count.** W1A8 sits below FP32 by
  **−0.0152 (N=8), −0.0172 (N=16), −0.0322 (N=32), −0.0365 (N=64)**, seed-paired; each is
  resolved against both the seed spread and the test-set bootstrap.
- **FP32 improves monotonically with N**, including the last step: n32→n64 is **+0.0112**
  and n16→n32 is **+0.0246**, both resolved. There is no FP32 turnover at 64 constituents.
- **W1A4 gains from 32 → 64 constituents: +0.0240**, resolved. More constituents still help
  the most aggressively quantized arm.
- **At N = 16, 8-bit activations beat 6-bit by +0.0046** (W1A8 − W1A6), resolved. This is the
  only activation-ladder step in the campaign that is resolved at 3 seeds.
- **W8A8 is indistinguishable from FP32 at N = 8 and N = 16** (Δ = −0.0002, −0.0004).

**Observations that are not yet claims** (recorded so they are not lost, but explicitly
unresolved at 3 seeds — see `results/r14/uncertainty_r14.md`):

- *Gap growth with N.* The binary-vs-FP32 point gaps rise monotonically
  (0.015 → 0.017 → 0.032 → 0.037), which is suggestive, but **no single step-to-step increase
  survives the seed spread** (n16−n8 −0.0020, n32−n16 −0.0150, n64−n32 −0.0043; all seed CIs
  straddle zero). This is an observed pattern, not a measured scaling. Resolving the
  n64−n32 step would need ≈ 30 seeds per arm unless the N = 64 binary instability is fixed
  first.
- *A W8A8 deficit at large N.* Point deficits vs FP32 are −0.0016 (N=32) and −0.0038 (N=64),
  and at N = 64 all three W8A8 seeds fall below all three FP32 seeds — but both seed CIs
  include zero, so **this is not established** and is not reported as a finding. It is the
  cheap follow-up: ≈ 8–10 seeds per arm would settle it.
- *W1A8 vs W1A6 at N = 64 — a positive null.* The two are indistinguishable (Δ = −0.0015,
  sign not established), with the point estimate favouring the **lower**-precision arm. Read
  plainly, this is evidence that at large constituent counts the binding constraint is weight
  binarization, not activation precision: **sub-8-bit activations cost little at large N**.
  It is not merely an absence of evidence, but it is also not a resolved ordering.

Multiplicity caveat: ~30 pairwise contrasts exist in this 20-arm grid. The claims above
(binary penalty at each N, FP32 scaling, W1A4 32→64, W1A8−W1A6 at N=16) survive with margin;
the borderline ones would not survive a multiplicity correction and are therefore parked in
the list above rather than promoted.

### EBOPs — pre-synthesis screening only

EBOPs are computed with HGQ2 `trace_minmax` over an 8,192-jet calibration set
(`convention: hgq2_trace_minmax` — never mixed with the HGQ-v1 Eq. 5 convention). They are
**a screening proxy for arithmetic cost, not a resource claim**: only Vitis HLS C-synthesis
numbers (§6, §6′, §6″) are quotable as resources. EBOPs here are seed-identical by
construction, because every traced bitwidth equals its configured width. FP32 arms have no
EBOPs entry (unquantized; the measure is undefined for them).

| N | W1A4 | W1A6 | W1A8 | W8A8 |
| --- | --- | --- | --- | --- |
| 8  | 0.85 M | 1.28 M | 1.74 M | 9.19 M |
| 16 | 2.32 M | 3.50 M | 4.82 M | 19.65 M |
| 32 | 7.15 M | 10.83 M | 15.03 M | 44.63 M |
| 64 | 24.38 M | 36.98 M | 51.67 M | 110.80 M |

Paired with the AUC table, the accuracy-vs-EBOPs frontier reads:

| EBOPs | arm | ROC-test macro-OvR | on frontier? |
| --- | --- | --- | --- |
| 0.85 M | n8 W1A4 | 0.8534 | yes (cheapest point) |
| 1.28 M | n8 W1A6 | 0.8689 | yes |
| 1.74 M | n8 W1A8 | 0.8712 | yes |
| 3.50 M | n16 W1A6 | 0.8910 | yes |
| 4.82 M | n16 W1A8 | 0.8956 | yes |
| 9.19 M | n8 W8A8 | 0.8862 | no — dominated by n16 W1A6 at 2.6× fewer EBOPs |
| 10.83 M | n32 W1A6 | 0.9022 | yes |
| 15.03 M | n32 W1A8 | 0.9052 | yes |
| 19.65 M | n16 W8A8 | 0.9124 | yes — first 8-bit point to take the frontier |
| 36.98 M | n64 W1A6 | 0.9136 | marginal (+0.0012 over n16 W8A8, within noise) |
| 44.63 M | n32 W8A8 | 0.9358 | yes |
| 110.80 M | n64 W8A8 | 0.9448 | yes (most accurate point measured) |

**Pareto statement.** *Binary owns the low-EBOPs region.* Up to ≈ 15 M EBOPs every point on
the accuracy-vs-EBOPs frontier is a binary-weight model, and the cheapest 8-bit arm
(n8 W8A8, 9.19 M) is dominated outright by n16 W1A6 at 2.6× fewer EBOPs. **Past ≈ 20 M EBOPs
the ordering reverses and W8A8 dominates**: n16 W8A8 (19.65 M, 0.9124) is the first 8-bit
frontier point, and no binary arm at any N reaches it at lower cost. The one apparent
exception, n64 W1A6 at 36.98 M (0.9136), exceeds n16 W8A8 by 0.0012 — smaller than that arm's
own seed sd (0.0061) — and should be treated as a tie, not a frontier win. The n64 W1A8 arm
(51.67 M) is off the frontier at any reading of its seed range.

Interpretation for the thesis: at this input representation, the binary advantage is a
**budget-regime** advantage. In the EBOPs range a Level-1 tagger actually lives in, binary
{−1,+1} weights buy the accuracy per unit of arithmetic; if the budget is opened up far
enough that 32–64 constituents at 8 bits fit, 8-bit wins on accuracy. Whether that ordering
survives contact with real LUT/DSP/latency numbers is a synthesis question, not an EBOPs
question, and is open.

### Open items from round 14

1. **N = 64 binary training instability** (W1A8 seed range 0.0223 wide) — a training problem
   to fix, not a number to average. Nothing at N = 64 in the binary column is settled until it
   is.
2. **W8A8-vs-FP32 at N = 32/64** — ≈ 8–10 seeds per arm would resolve it; cheap.
3. **C-synthesis of the best small binary configurations** — EBOPs screening points at the
   n16/n32 binary arms; only csynth can turn that into a resource/latency claim.

---

## Numbers audit (for `results-analyst`)

Every figure in the draft above, with its source. Metric for all AUCs: **ROC-test macro
one-vs-rest AUC (public HLS4ML LHC Jet 5-class), l1x3 3-feature inputs, n = 260,000
held-out jets, seed-averaged over 3 seeds unless marked.** No validation AUC appears. No
No 16-feature number appears.

| Number(s) | Source file |
| --- | --- |
| All 20 seed-averaged macro AUCs + sds in the accuracy table | `bnjettag/roc-results/r14/{n8,n16,n32,n64}/roc_auc.md`, "Seed-averaged" section (verified this session by recompute from the `.npz`; identical to the recomputed table in `bnjettag/results/r14/uncertainty_r14.md`) |
| n64 W1A8 per-seed 0.9028 / 0.9251 / 0.9084; range; mean 0.9121 ± 0.0116 | `bnjettag/roc-results/r14/n64/roc_auc.md` per-seed table; `uncertainty_r14.md` §Q6 (range-not-mean instruction) |
| n32 W1A8 range 0.8976 – 0.9134, sd 0.0079 | `bnjettag/roc-results/r14/n32/roc_auc.md`; `uncertainty_r14.md` §Q6 |
| Binary penalties −0.0152 / −0.0172 / −0.0322 / −0.0365 and "Real" verdicts | `uncertainty_r14.md` verdict rows 1a–1d |
| FP32 n32→n64 +0.0112; n16→n32 +0.0246 (Real) | `uncertainty_r14.md` rows 2a, 2b |
| W1A4 n64−n32 +0.0240 (Real) | `uncertainty_r14.md` row 5c |
| W1A8 − W1A6 at n16 +0.0046 (Real) | `uncertainty_r14.md` row 4b |
| W8A8 − FP32 −0.0002 (n8), −0.0004 (n16), −0.0016 (n32), −0.0038 (n64); all unresolved | `uncertainty_r14.md` rows 3a–3d |
| Gap-growth steps −0.0020 / −0.0150 / −0.0043, all unresolved | `uncertainty_r14.md` rows 1e–1g |
| W1A8 − W1A6 at n64 = −0.0015, sign not established | `uncertainty_r14.md` row 4a + Guidance paragraph |
| Test-set-only sd ≈ 0.0004; seed sd range 0.0002 – 0.0116; bootstrap B = 400; t = 4.303 (df 2) | `uncertainty_r14.md` §Method and §Scale of the two noises |
| Seed-pair bootstrap CIs at n64 all exclude 0; instability 30–60× test-set noise | `uncertainty_r14.md` §Q6 |
| Seeds needed: ≈ 8–10 (W8A8 n64), ≈ 30 (gap-growth step) | `uncertainty_r14.md` §What more seeds would buy |
| All 16 EBOPs values, `hgq2_trace_minmax`, calib n = 8,192, features (pt, etarel, phirel) | `bnjettag/results/r14/ebops_r14.json` (fields `ebops`, `convention`, `calib_n`, `features`) |
| Frontier ordering and domination statements | derived by sorting the EBOPs table against the AUC table above; no new measurement |
| Design: features, r8-small recipe (d32/2L/4H/ffn64, norm-free, 101 ep, LR 2e-5, es 15), grid, seeds, W&B project `BNJetTagAug`, run naming, selection rule | `.claude/memory/decisions.md`, 2026-08-01 "Round 14 pre-registration" entry |
| 60/60 `verify-roc` pass | `.claude/memory/experiment-log.md`, 2026-08-03 "R14 ROC-TEST EVAL + VERIFY-ROC COMPLETE" entry |
| Odagiu et al. arXiv:2402.01876 3-feature rationale | `.claude/memory/decisions.md` 2026-08-01 entry; `DATASET.md` "A note on 3 features" |

**Proposed §8 rows** (for the main session to add when splicing):

| Claim | Source (relative to `bnjettag/`) |
| --- | --- |
| **ROUND-14 l1x3 ROC-test AUCs (§5‴)** | `roc-results/r14/{n8,n16,n32,n64}/roc_auc.md`; recomputable from `roc-results/r14/<N>/*.npz` (verified 2026-08-03, 60/60 exact); W&B project `BNJetTagAug`, artifacts `evaluation-r14-l1x3-n<N>` |
| **ROUND-14 uncertainty verdicts (which l1x3 differences are real)** | `results/r14/uncertainty_r14.md` (seed t-intervals df=2 + paired test-set bootstrap B=400, 2026-08-03) |
| **ROUND-14 EBOPs screening table** | `results/r14/ebops_r14.json` (HGQ2 `trace_minmax`, calib n=8,192; screening proxy only — not a resource claim) |
| **ROUND-14 design / pre-registration** | `.claude/memory/decisions.md` 2026-08-01 entry; configs `code/hgq2/configs/gen_r14.py`; jobs `code/jobs/training/variants/gen_r14_jobs.py` |

**Two things for the lead to check before splicing:**

1. `bnjettag/roc-results/r14/n64/roc_auc.md` carries the **wrong header**: it says "FINAL
   campaign" and `source: recomputed from roc-results/synthesis/*.npz`, whereas the other three
   stores correctly say "ROUND 14 (l1x3, N=…)" and point at `roc-results/r14/n<N>/*.npz`. The
   numbers in it match the independently recomputed n64 row in `uncertainty_r14.md`, so the
   values are believed correct and are used above — but the provenance line should be
   corrected in the store before this section is published.
2. The 2026-08-03 experiment-log entry quotes a few sds that differ in the last digit from the
   store tables (e.g. n8 FP32 ±.0006 vs ±.0005; n16 W1A8 ±.0003 vs ±.0002; n64 W1A6 ±.0050 vs
   ±.0061) and one central value (n8 W1A4 .8533 vs .8534). This draft uses the
   `roc_auc.md` / `uncertainty_r14.md` values throughout, which agree with each other; the log
   entry appears to be a rounding/transcription artifact and may want a dated correction note.
