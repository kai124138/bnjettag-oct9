# STUDY review, critical-reviewer, v3: 2026-09-26-training-batch

Panel mode, re-review (n = 3). No verdict; the arbiter decides. Artifact: `STUDY.md` (1,086
lines, mtime 2026-09-27 01:34), `plan.md`, `code/` (patches 0001-0014, patched `tree/`) and
`code/evidence/` (CPU traces on synthetic samples, not results). Earlier findings:
`review/STUDY_arbiter_v2.md` #1-#19 and my `STUDY_critical_v2.md` (A1, B1, B2, C1-C4).
Scope, as briefed for iteration 3: new findings only where they change the design or its numbers.

Validator output, verbatim (`review/STUDY_validators_v3.txt`):

```
Desktop/bnjettag/campaigns/2026-09-26-training-batch/STUDY.md  —  score 0, reads human
  14534 words · 365 sentences · mean 22 words (σ=16.4) · 18% bullets · 0 em-dashes
```

No A lines. No mechanical STUDY validator exists. STUDY has no figures, so `plot_check` does not apply.

## Recomputed or verified in this session

- **Floors, from the evidence JSONs** (every entry, `name / target / init / 0-bit / 1-bit-alive / headroom / status`):
  - `static_floors_trace_step2.json`:
    - a07-current: 350,000 / 24,816,782 / 4,580,398 / 4,580,398 / −4,230,398 / STATIC_INFEASIBLE;
    - a07-chang: 13,182,317 / 343,053 / 1,005,741 / 6,947 / FEASIBLE;
    - e-chang: 8,965,267 / 171,526 / 619,198 / 178,474;
    - e-current: 2,701,439;
    - f-chang: 343,053 / 1,005,741 / 6,947.
  - `static_floors_arms_s1.json`: A, C, D, F and R at seed 1 all have a 343,053 floor and a
    6,947 headroom at 350k (C: 4,656,947 at 5M).
  - This file's `b` entry is still A07 at 175,000 (STATIC_INFEASIBLE, −168,053). It was built from
    the pre-fix text, which STUDY:536-541 admits; the regeneration is routed.
  - Every STUDY value matches: 6,947, 178,474, 78,474 (250k − 171,526) and 3,474.
  - Ratios: 343,053 / 350k = 0.980; 1,005,741 / 350k = 2.87; 4,580,398 / 350k = 13.09.
  - Screen check: 4,630,276 / 4,580,398 = 1.0109, which STUDY rounds to 1.1 %. 5M / 4,580,398 =
    1.0916, rounded to 9.2 %. Both correct.
- **Timing.** `campaigns/2026-09-22-constituent-screen/live-status.json:206` gives
  `const0922-a07-n64-s1-fast50-fp32` `last_epoch_wall_seconds` 100.09056520462036. Projections:
  - 7,000 × 100.09 s = 8.11 d;
  - scaled to 558,000 train jets: × 558/496 = 112.60 s, and 7,000 epochs = 9.12 d;
  - R: 1,000 × 112.6 s = 31.3 h per run, × 2 pods = 62.6 pod-hours;
  - 8 × 9.12 d × 24 = 1,751 pod-hours;
  - P = 2: ceil(48/12) = 4 waves × 9.12 d = 36.5 d;
  - pilot: 500 × 112.6 s = 15.6 h.

  Every value matches STUDY:484-506.
- **Fig. 2 macro means.**
  - Linformer: (0.941 + 0.921 + 0.972 + 0.968 + 0.964) / 5 = 0.9532.
  - MHA: (0.930 + 0.911 + 0.963 + 0.956 + 0.954) / 5 = 0.9428.
  - Both match STUDY:116 and `research-log.md:2011, 2013`.
- **McNemar reach** (two-sided exact, STUDY:432): 4-0 gives 2·0.5⁴ = 0.125; 5-0 gives 0.0625; 6-0
  gives 0.03125; 7-0 gives 0.0156. Correct.
- **[A20] gate.** `code/evidence/cpu_gate_final.log:59` reads `PREFLIGHT_ALL_PASS 56`.
  `cmp regression_base.json regression_patched.json` reports the files as byte-identical, so the old
  path is unchanged by the opt-in patches.
- **[A17].**
  - `a17_pairing_with_0011.json`: seeds 1 and 2 are paired; the only difference is `pos_enc/pos_table`.
  - Without 0011, eight shared kernels differ at seed 1.
  - Matches STUDY:875-881.
- **Q/K/V stream granularity under [D19]** (patched `code/tree/bnhgq2/qat.py`):
  - `stream_iq()` at l. 486-487 is `act_iq(6, axes=(-2, -1))`, "shared over particles and batch".
    On q/k/v of shape (b, t, h, e) the quantizer is therefore per (h, e) and shared over t.
  - Dense inputs are per d-channel (`dense_einsum`, l. 463).
  - The softmax output into A·V is per element (h, t, s) (l. 569-571).
  - This fixes the per-channel prices used in new finding A1.

## Earlier A and B findings (arbiter v2), by name

| # | finding | status | evidence in STUDY v3 |
| --- | --- | --- | --- |
| 1 (A) | static floor above every 350k/175k target under our quantizer | **Resolved** | [D19] l. 750-764; old-quantizer floor table, traced, l. 210-237; budget falsifier l. 391-395; FLAG l. 949-960 |
| 2 (A) | fixed softmax internals; half-fix risk | **Resolved** | Softmax output, exp input and tables are all in [D19] and [A20] (l. 889-903). The fidelity rows are at l. 196-199. The traced residual (the LUT table term) is named at l. 222-227 |
| 3 (A) | matched A07 is feasible only as an almost fully pruned model; pre-register the floors; B infeasible | **Resolved as written. New A1 below**: the traced headroom (6,947) changes what "almost fully pruned" means | l. 74-82, [A7] l. 813-826, [D6] l. 708-714 |
| 4 (A) | timing mis-sourced | **Resolved** | l. 484-506 cite 100.09 s with file and field. 83.53 s is relabelled as E02-N8 and 189.68 s as A02-N64 (l. 492-493). The expected branch is "fits 14 days" (l. 495), and the pod count is binding (l. 503-506). The stub `experiment-log.md:25-27` is updated |
| 5 (B) | 336,000 run-epochs with no dynamic evidence; pilot | **Resolved** | Canary plus epoch-500 pilot, l. 526-579. Dropping the 3× clause is justified at l. 553-556: 1,050,000 exceeds the 1,005,741 floor, so the clause would pass any model |
| 6 (B) | [D13] undefined at k < 2; far-from-budget report | **Resolved at the arbiter's minimum** | l. 313-316, 365-369, [D13] l. 733-738. There is no threshold at epoch 1,000, and the arbiter did not require one |
| 7 (B) | stability: count rule versus McNemar and Holm; sidedness | **Resolved** | l. 383-387 and 427-432. The count rule on marginal counts decides; exact McNemar is two-sided and outside Holm. The p values are checked above |
| 8 (B) | width quantity; Deep-Set wording | **Resolved** | l. 437-456: `relu(i+f)` and `k` are defined; a WRAP zero is a true zero; the SAT floor channel is "silent, billed 1 bit"; the Deep-Set-class wording is fixed |
| 9 (B) | arm B | **Resolved** | [D6] l. 708-714: B is E at 250,000, paired with E. The Holm set is C−A, E−B, A−D, A−F, F−E (l. 434). Ladders at l. 463-464 |
| 10 (B) | survivor bias carried to A − 79.4 | **Resolved** | l. 400-401 |
| 11 (B) | arm H FLAG inherits [D19] | **Resolved** | l. 1012-1013 |
| 12 (B) | Fig. 2 per-class AUCs | **Resolved** | l. 116 (means recomputed above); per-class distances at l. 409-412 |
| 13-18 (C) | labels, canary number, 13,760, Kai's brief, empty markers, GPU class and other items | **All applied** | l. 117; l. 594-597; l. 637; `plan.md:139-147`; l. 465-466; l. 510, 297, 665, 938-947, 103-107 |
| 19 (C) | upstream feedback | **Applied** | `UPSTREAM_FEEDBACK.md:13-23` carry the traced values; STUDY l. 235-236 wrongly say it is stale (C3) |

My v2 findings map onto these: A1 is #4, B1 is #5 and #6, B2 is #7, C1-C4 are #13, #14, #15 and #16. All are resolved.

## Category A (new)

**A1. At 350k the traced headroom makes A07's model class a static certainty. STUDY states it as
"may", and the default design still puts 32 runs and three of its four claims on that
configuration.** (STUDY:74-82, 391-396, 437-456, 962-978, 1065-1072; evidence
`static_floors_trace_step2.json` a07-chang "one" block; `qat.py` l. 463, 486-487, 569-571)

Per-channel prices at 1 bit, from the traced 1-bit-alive per-layer values and the quantizer axes:

| path | price |
| --- | ---: |
| input_proj input channel | 6,144 / 3 = **2,048** |
| each d32 dense input channel (Wq, Wk, Wv, Wo, fc1, fc2) | 65,536 / 32 = **2,048** |
| one alive Q·K (h, e) pair (stream per (h, e), shared over t) | 131,072 / 32 = **4,096** |

Data-dependent attention logits need three things:

- the embedding to see the data: one input_proj channel, 2,048. Without it,
  `h = bias + PE` is data-independent.
- one Wq or Wk input channel, 2,048.
- one matching Q·K (h, e) pair, 4,096.

That is **8,192 > 6,947**. Using the attention output then adds a V path of about 4,100 (a Wv
input, a sparse per-element ctx and a Wo input), for about 12,300 in total. A nonlinear φ
(fc1 + fc2, one hidden unit) costs 4,096 on top of the embedding channel. So:

- **every feasible A07 checkpoint at 350k is statically attention-free with respect to the
  data**. At most, logits depend on position through the PE.
- every feasible checkpoint carries at most 3 bits of per-constituent information in total
  (6,947 / 2,048 = 3.4).

This is new since arbiter v2. At the arbiter's 23,344 headroom, the ~12,300 attention path fit;
at the traced 6,947 it does not. The arbiter's reason for keeping A07 as the default primary
therefore no longer holds as stated.

Consequences the STUDY does not draw:

- **Diagnostic wording (l. 81, 437-456).** The "Required diagnostic" presents the attention
  state as an outcome, and "may be a Deep-Set-class model" is written as uncertain. For A, D, F
  and R at 350k, both are known before training: Q/K data-dependence is impossible. The
  downstream atlas BRIEF already says "attention is dead by construction, so A07 350k cells
  are feasibility probes" (`campaigns/2026-09-26-method-atlas/BRIEF.md:39-41`), so the two
  artifacts disagree on the same fact.
- **Budget claim (l. 391-396).** It is "decided by training" only in the narrow sense of
  whether the optimizer prunes to within 6,947 EBOPs of an empty network. Supported, it means
  "8 seeds pruned to ≤ 3 input bits". The text does not say so.
- **Recipe claim (A − R, l. 414-424).** It becomes a race to the floor. The expected branch is
  already "R infeasible" (l. 421-424), so the recipe claim would be "supported on feasibility":
  Chang's recipe prunes a 13.2M-EBOPs init to an almost empty network faster than ours. That
  is not the question in the frontmatter ("does that recipe beat our own recipe"), and the
  stability claim (A vs D) is measured on the same degenerate model.
- **A − F ladder rung (l. 174, 434).** It is near-degenerate. The PE reaches the output only
  through a nonlinearity (fc1 + fc2, 4,096) or attention (dead). Through mean pool alone it is
  a constant. F − E then measures headroom (6,947 against 178,474), not "d_model and heads".
- **E-primary option (l. 970-973).** The designer's own option keeps the recipe and stability
  claims on A07 ("because D and R are A07"). Even if Kai picks E, two of the three claims stay
  on the degenerate configuration. Adding D and R on E is priced (+16 runs) but offered only
  as an extra.
- **Cost.** A, D and F are 24 × 7,000 = 168,000 of the 336,000 Chang-schedule run-epochs.

**Impact.** Half the compute and three of four claims (budget, recipe, stability) sit, by
default, on a configuration whose model class is fixed before training. The text calls it
uncertain, and a sibling artifact already treats it as settled. This changes the design's
numbers and what its claims mean.

**Fix** (the design choice stays Kai's; the text has to be right before he chooses):

1. State the bound as a fact with the arithmetic above:
   - at l. 74-82 and l. 1065-1072: "at 350k a feasible A07 checkpoint cannot carry
     data-dependent attention (≥ 8,192 EBOPs needed, 6,947 available) and has ≤ 3 input bits";
   - at l. 437-456: pre-register the expected attention state for A, D, F and R at 350k.
2. In the primary-architecture row (l. 943) and the FLAG (l. 962-978), make the E-primary option
   complete. Either:
   - move D and R onto E with it (D_E, R_E; this is +16 runs, or a swap for A07-D and A07-R);
   - or state in the Falsifier that on A07 the recipe and stability claims are feasibility races
     to an almost empty network, and say what each outcome would then mean.
3. Say at l. 174 and l. 434 that at 350k A − F is expected to be about 0 by construction, and
   that F − E is dominated by the headroom difference. Alternatively, move F to 5M beside C,
   where the PE can act.
4. Bring the pilot readout and the atlas BRIEF into agreement: record "attention dead by
   construction" in STUDY as the shared fact.

## Category B (new)

None that meet the iteration-3 bar beyond A1. Two items were checked and are not B:

- **The atlas BRIEF headroom.** It is current (6,947 and 343,053 at `BRIEF.md:38-40`), so it
  is not stale.
- **`UPSTREAM_FEEDBACK.md`.** It is updated (l. 13-23); only STUDY's sentence about it is stale (C3).

## Category C (apply before commit; no re-review needed)

- **C1.** STUDY:229 says "Every 350k and 175k arm". No 175k arm remains (B is E at 250k).
  Say "every 350k and 250k arm (E at 250k: 2,701,439 old-quantizer floor)".
- **C2.** STUDY:212 says "to be confirmed by CPU trace at PREFLIGHT [A7]", but the trace is
  done (l. 222). [A14] l. 852 still lists "fixed 10-bit softmax output" as an accounting
  difference, which is wrong under [D19]. Drop it or mark it as C′ only.
- **C3.** STUDY:235-236 says `UPSTREAM_FEEDBACK.md` "still carries" 1.6 % and 4,559,008. It no longer
  does: `UPSTREAM_FEEDBACK.md:13, 19, 23` give the traced 4,580,398, 1.092 and 1.1 %, and cite 4,559,008
  only as the arbiter's hand arithmetic (l. 15). The STUDY sentence is stale; delete it.
- **C4.** Two A07 init EBOPs under [D19] appear, both described as "synthetic, at init":
  - 13,613,261 (STUDY:771, `wrap_trace_check.py`: exponential-pT sample, gated and
    standardized, 256 rows);
  - 13,182,317 (STUDY:903, 1062, `static_floor.py`: standard-normal sample).

  Under WRAP, `i` depends on the sample, so both can be right. Name the sample beside each.
- **C5.** The evidence files are stale on arm B: `static_floors_arms_s1.json` `chang0926-b` is
  A07 at 175k. PREFLIGHT has to record the regenerated E-at-250k entry. For C′ (a07-current),
  the "one" column equals "zero", because SAT k = 1 is already 1 bit. Define that column or
  drop it for C′.
- **C6.** Arms paragraph l. 141-143: the inert `calib_n 8192` remains in the field list next
  to a note saying no code reads it. Drop it from the list, or name the [D20] key that
  replaces it.

## Decision-label traceability

- [D19] is implemented as stated: patch 0001, `qat.py` l. 486-487 and 569-571, and the gate at
  `PREFLIGHT_ALL_PASS 56`.
- [D20] is dated. [D6] and [D13] are amended and dated in the change log (l. 29-63).
- No [D] is replaced silently.
- The exp-input SAT choice (l. 762) is dated and listed as a Kai option.

## Completeness cross-check

- Arms: 7 × 8 = 56 (l. 165); the stub agrees (`experiment-log.md:27`).
- The pilot pod is six processes (l. 528), K = 6.
- Every arbiter v2 fix, 1-10, is present in the text.

## Competing-group question

A group publishing next month would size the architecture so that attention can exist at the
paper's budget. The paper's own collapse to a Deep Set is the cautionary case. Our default
spends half its compute on a configuration where attention cannot exist, and it says only
"may". That is covered by A1 and is not justified in the text; everything else was answered in v2.
