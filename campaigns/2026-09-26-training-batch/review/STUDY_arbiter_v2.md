# STUDY arbiter v2: 2026-09-26-training-batch

Arbiter, fresh context, 2026-09-27. Artifact `STUDY.md` (711 lines, fixer pass after arbiter v1 plus
the method-atlas fixer pass `review/STUDY_fixer_v1.md`) and `plan.md`. Reviews v2:
`STUDY_physics_v2.md`, `STUDY_critical_v2.md`, `STUDY_constructive_v2.md`. Validators
`STUDY_validators_v1.txt`, `_v2.txt` (no mechanical STUDY validator; `prose_lint` score 0, no A lines).
No plot-validator file (STUDY has no figures). Earlier arbiter `STUDY_arbiter_v1.md`; investigator
`STUDY_investigation_350k.md`. Read `docs/methodology/06-review.md` §6.1-6.8,
`docs/conventions/quantization-and-cost.md` (no SAT or train-equals-deploy mandate found by grep).

## Independent checks made by the arbiter

- **Our quantizers** (`bnjettag/code/constituent-study-20260922/bnhgq2/qat.py`):
  - `_free_act` (l. 279-302): kif, `k0=1`, `overflow_mode="SAT"`, trainable, `ic=MinMax(-8,12)`,
    `fc=MinMax(-8,16)`; used for every dense input (`act_iq`, l. 388-396) and for Q, K, V into the
    einsums (`stream_iq`, l. 431-432, per (head, channel), shared over particles).
  - Softmax output into A·V (`attn_iq`, l. 496-499): kif `k0=0, i0=sm_out_i, f0=sm_out_bits-sm_out_i`,
    SAT, `trainable=False`, per tensor. l. 440-443 only require `sm_out_bits - sm_out_i >= 1`, so
    `softmax_out_bits 1, softmax_out_i 0` is legal by config.
  - Weights `_binary_kq` (l. 228-232): 1 bit, fixed. Bias `_dummy` (float).
- **HGQ2 0.1.9** (`.venv-hgq2/.../hgq/quantizer/internal/fixed_point_quantizer.py:93-97`):
  `bits = b + k` in SAT, `b` otherwise; `b = relu(i + f)` (l. 435-437); `k` is updated only in the
  WRAP-and-trainable tracing branch (l. 402-421). `quantizer.py:86-88` `bits_` uses `bits`, and
  `QEinsum._compute_ebops` (`layers/ops/einsum.py:61-64`) and `QDense._compute_ebops`
  (`layers/core/dense.py:70-80`) price with `bits_`. So each SAT channel of ours costs at least 1 bit
  in EBOPs; a WRAP channel can cost 0. Both reviewers are right on the mechanism.
- **Chang's quantizer** (`reference-code/HGQ2-examples/jsc150/model.py:183-195`): datalane scope sets
  only `homogeneous_axis`; `QMultiHeadAttention` defaults `softmax_oq_conf = QuantizerConfig(place='datalane')`
  (`hgq/layers/attn/mha.py:69`), and `kif_datalane_default` is `overflow_mode='WRAP'`
  (`hgq/quantizer/config.py:131-136`). Chang's activations and softmax output are learned and can
  reach 0 bits. The paper's "at least one bit" constraint (pdftotext l. 169, 227) is on the **weight**
  bitwidths of the attention layers (Fig. 3 is "weight bitwidths"); other layers prune freely, and
  HGQ weights prune per weight to 0 bits, which binary weights cannot.
- **Softmax internals** (`hgq/layers/softmax.py:134-160`, `QSoftmax._compute_ebops`): per score entry
  (H·T·S = 16,384 for A07) it charges the exp-table input bits, the accumulation of exp-table output
  bits, and exp × inv table bits. Ours are all fixed (`qat.py:452-459`): exp input `_static_act(10, 6)`
  (SAT, 10 bits), tables `_table(1, 11)` (12 bits). That is 163,840 + 193,536 + 2,359,296 =
  **2,716,672 EBOPs for A07, fixed at every target** (E, H=2: 1,358,336). Neither reviewer counted it.
  Chang's tables are kbi `SAT_SYM`, learned, per element, `bc=Min(4)` (`jsc150/model.py:188`;
  `hgq/quantizer/config.py:184-190`), so his softmax floor is 16·H·T·S + 4·(H·T·S − H·T):
  **326,656 for H=4** (A07), **163,328 for H=2** (E, and Chang's own xfm).
- **Calibration of this accounting model.** At the 8-bit init it gives 22,078,720 (einsum, dense, head)
  + 2,716,672 (softmax) = 24,795,392 against the traced 24,816,782 (`campaigns/2026-09-23-confirmation/
  n64-full-preflight-result.json`), within 0.09 %. At the floor it gives 4,559,008 against the screen
  A07-N64 minimum of 4,630,276 (investigation; W&B, seed 1, not a result), 1.6 % above it. **The screen
  plateau is the static floor of our quantizer**, not a truncated descent (this corrects investigation
  caveat 1), and the 5M N=64 confirmation target sits about 10 % above that floor.
- **Static floor, shape arithmetic** (arbiter, Python; N=64, 3 features; every learnable width at its
  minimum, fixed widths at their values):

  | arch | quantizer | dense + head | Q·K | A·V | softmax internals | floor | vs 350k |
  | --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
  | A07 (d32, H 4, H·E 32, FFN 32) | ours (SAT k=1, softmax out 10 bits, fixed tables) | 400,544 | 131,072 | 1,310,720 | 2,716,672 | **4,559,008** | 13.0× |
  | A07 | ours, softmax out 1 bit (config only) | 400,544 | 131,072 | 131,072 | 2,716,672 | **3,379,360** | 9.7× |
  | E (d24, H 2, H·E 24, FFN 32) | ours | 251,064 | 98,304 | 983,040 | 1,358,336 | **2,690,744** | 7.7× |
  | A07 | Chang datalane (WRAP, 0 reachable) + Chang tables (≥ 4 bits) | 0 | 0 | 0 | 326,656 | **326,656** | 0.93× |
  | E | same | 0 | 0 | 0 | 163,328 | **163,328** | 0.47× |
  | A07, every learnable width at 1 bit ("1-bit-alive") | Chang-matched | 400,544 | 131,072 | 131,072 | 326,656 | **989,344** | 2.8× |
  | E, 1-bit-alive | Chang-matched | 251,064 | 98,304 | 98,304 | 163,328 | **611,000** | 1.7× |

  Physics A1 (einsum part ≈ 1.84M) and constructive A1 (A·V 1,310,720, traced in isolation; E 983,040)
  agree with the einsum columns. **New (case 5):** (i) changing only the softmax output width makes no
  350k arm feasible; the fixed softmax tables alone (2.72M) exceed every target but C's, and the dense
  inputs at 1 bit per SAT channel add 400k; (ii) a Linformer projection shrinks Q·K, A·V and the
  softmax (H·T·k instead of H·T²) but not the dense SAT floor, so under our quantizer it is also
  infeasible; (iii) under a full Chang-matched quantizer A07 has **23,344 EBOPs** left outside the
  softmax at 350k, so the primary arm is feasible only as an almost fully pruned network; E, with two
  heads, keeps 186,672. At 175k (B) the A07 floor is above target under any matched quantizer.
- **Timing (critical A1).** `campaigns/2026-09-22-constituent-screen/live-status.json`
  `last_epoch_wall_seconds`: a07-n64 100.09, a02-n64 189.68, e02-n8 83.53, e03-n64 640.21, a02-n8 749.72.
  83 s is an N=8 arm; "190" is A02-N64, not A07; "245" appears in no timing field (grep). Confirmed.
  At the A07-N64 prior (one packed epoch, batch 256, n_train 496,000; unverified ops number):
  T_run = 7,000 × 100.09 s = 8.1 d, or 9.1 d scaled to 558,000 train jets (112.6 s per epoch); R
  1,000 epochs ≈ 31.3 h per run; epoch 500 ≈ 15.6 h. Batch 2,790 is unmeasured.

## Adjudication table

| # | finding | source(s) | their category | final | rationale |
| --- | --- | --- | --- | --- | --- |
| 1 | Every 350k and 175k arm (A, B, D, E, F, R) has a static EBOPs floor above its target under our quantizers (fixed 10-bit softmax output; SAT k=1 never below 1 bit); only C (5M) is feasible. [A7] as written ("every trainable width at its lower bound") computes ≈ 0 and cannot detect it. Fidelity table lacks softmax-output and overflow-mode rows. | phys A1, cons A1 | A, A | **A** | Case 1, verified in code and by arithmetic above. The primary question has no feasible answer as designed; by STUDY l. 266-267 it is falsified before GPU time. |
| 2 | The fixed softmax internals (exp-input 10 bits, exp and inv tables 12 bits) cost 2,716,672 EBOPs for A07 at every target; the true floor under our quantizer is 4,559,008, and the screen A07 plateau (4,630,276) sits 1.6 % above it. The softmax-output-only remedy (3,379,360) and a Linformer arm under SAT both stay infeasible. Resolution needs Chang's datalane quantizer **and** his learned softmax tables in every arm. | arbiter | none | **A** (part of #1's fix) | Case 5, `hgq/layers/softmax.py:134-160`, `qat.py:452-459`; calibrated against the 24,816,782 trace to 0.09 %. Stated so the fixer does not apply a half-fix. |
| 3 | Even Chang-matched, A07 (4 heads) has a 326,656 softmax floor, leaving 23,344 EBOPs for the rest at 350k, and a 1-bit-alive floor of 989,344: arm A is feasible only as an almost fully pruned model, and B (175k) is statically infeasible. E (2 heads) keeps 186,672. Pre-register the 0-bit and 1-bit-alive floors and co-report the attention state with the budget claim. | phys A1 (1-bit-alive floor), cons A1 option (a); arbiter (softmax part) | A | **A** (with #1) | Case 1 plus case 5. |
| 4 | Per-epoch times behind the expected [D15] branch, R pod-hours and the pod decision are mis-sourced (83 s is N=8; 190 s is A02; 245 s has no source); A07-N64's own 100.1 s is omitted; the expected branch flips to "fits 14 days". Stub `experiment-log.md:13` carries the same. | crit A1 | A | **A** | Case 3, verified. A number without a source feeds a Kai decision ("never invent a number"). Fix is minutes. |
| 5 | Commitment of 336,000 run-epochs with no dynamic-feasibility evidence; stage it with a pre-registered pilot. | cons B4; crit B1 (no consequence when far from budget) | B, B | **B** | Case 1 in substance. Merged with #6. |
| 6 | [D13] epoch-500 sd trigger undefined when k < 2 feasible seeds; no report-to-Kai rule when trajectories sit far above target. | crit B1 | B | **B** | Case 3. |
| 7 | Stability falsifier: at 4-0 the exact McNemar p is 0.125 two-sided (0.0625 one-sided), so it always "fails the multiplicity adjustment"; sidedness unstated; marginal count vs discordant pairs ambiguous. | phys B2, crit B2, cons B2 | B, B, B | **B** | Case 1. Arithmetic checked: 2·0.5^4 = 0.125. |
| 8 | "V at 0 bits … not a Deep Set" is wrong: with the attention branch removed the network is φ → mean pool → ρ, a Deep-Set-class model; and under SAT k=1 a "0-bit" channel is a live sign-only channel. Define the width quantity. | phys B1, cons B1 | B, B | **B** | Case 1. Under the WRAP amendment 0 bits becomes a true zero for those channels; the text must say which quantity is reported. |
| 9 | Arm B (175k) is below any static or 1-bit-alive floor of ours and likely a guaranteed "no feasible checkpoint"; decide its role. | phys B3, cons C1 | B, C | **B** | Case 2: sided with physics, and the arbiter's floor confirms it: B on A07 is statically infeasible even Chang-matched (326,656 > 175,000). Eight 7,000-epoch runs on a known-empty rung is a design error. |
| 10 | Survivor bias carried into A − 79.4: it is an upper estimate when k < 8. | phys B5 | B | **B** | Case 3. One sentence. |
| 11 | Matched non-binary arm should be in-campaign, not a follow-up. | phys B4 | B | **B → resolved as a Kai decision** | Case 2. Arbiter v1 #2 accepted the follow-up with a justification and a FLAG; the critical reviewer confirms it (competing-group answer justified). Required: the arm H / in-house FLAG must note that the in-house arm inherits whatever quantizer [#1] fixes. No further change. |
| 12 | Published per-class AUCs for Linformer and MHA at N=64 (Fig. 2 legends; research-log 2026-08-04) missing from the reference table. | cons B3 | B | **B** | Case 3. Low cost; the house metric is AUC. Label "read from figure legend, one model, our arithmetic macro mean". |
| 13 | [L1] labels: REPRO-CHANG `xfmt` is the post-paper LUT Linformer, and those runs used the open-loop β schedule, not the PID. | crit C1 | C | **C** | |
| 14 | Canary stability checks qualitative; give a number (EBOPs at epoch 10 vs epoch 1). | crit C2 | C | **C** | |
| 15 | W&B artifact count 13,760, not "about 15,700". | crit C3 | C | **C** | Arithmetic checked: 48·280 + 8·40. |
| 16 | Kai's brief ("a couple of pods" etc.) recorded only in STUDY and reviews; record it with its date. | crit C4 | C | **C** | |
| 17 | Figures: ladder undefined if B has no feasible seed; state k in legends when k < 8. | phys (Figures table) | none | **C** | |
| 18 | Record GPU class per run (A1000 − R crosses GPU type); assert per-class label counts unchanged by the gate; per-pair seed correlation; expected R branch; single Kai decision table; atlas anchor fallback. | phys C1-C3, cons C2-C5 | C | **C** | Cons C5 becomes part of fix 1 (cascade to the atlas anchor). |
| 19 | The screen plateau and the 5M confirmation runs sit at or just above our quantizer's static floor (4,559,008): investigation caveat 1 ("not evidence of a floor") is wrong, and the 5M N=64 confirmation measures a model near minimum widths. | arbiter | none | **C here** (upstream feedback) | Not a defect of this STUDY; write it to `campaigns/2026-09-23-confirmation/UPSTREAM_FEEDBACK.md` and the experiment-log. It supports #1 and makes C under the old quantizer a near-floor arm. |

## Earlier A and B findings (arbiter v1), by name

| v1 # | finding | status | evidence |
| --- | --- | --- | --- |
| 1 (A) | descriptive recast, iso-EBOPs | **resolved** | STUDY l. 6, 30-51; "iso-cost" only in negation (l. 47). Will need re-wording once more under fix 1 (the model is pruned by construction). |
| 2 (A) | competing group, arm H | **resolved** | l. 656-665 FLAG with reasons; critical v2 concurs. |
| 3 (A) | resolving power | **resolved, new B (#6)** | l. 187-200, [D13] l. 503-506; trigger undefined at k < 2. |
| 4 (A) | tie-break | **resolved** | l. 204-211, [A13] l. 561-567; code re-verified by the critical reviewer (`ablation.py:278-287, 421`). |
| 5 (B) | reference uncertainty | **resolved** (label nit #13) | [L1] l. 603-612. |
| 6 (B) | comparand fixed | **resolved** | l. 272-279. |
| 7 (B) | attention diagnostic split | **resolved in structure, wording wrong (#8)** | l. 299-310, 695-700. |
| 8 (B) | pairing, infeasibility, divergence, stability | **resolved, new B (#7)** | l. 214-229, 290-294. |
| 9 (B) | EBOPs equivalence | **resolved** | [A14] l. 568-572. Gains weight under fix 1 (WRAP bits exclude k, as in Chang). |
| 10 (B) | expected [D15] branch, pod count to Kai | **not resolved** | l. 332-345: basis mis-sourced (#4). Keeps B, subsumed by A #4. |
| 11 (B) | overhead [A15] | **resolved** | l. 381-384, 573-577. |
| 12 (B) | epoch-matched A1000 − R | **resolved** | l. 120-122, 253-254, 288. |
| 13 (B) | screen history gate | **resolved** | [A16] l. 578-589 with the investigator's answer. |
| 14 (B) | [D1] rationale | **resolved** | l. 460-465. |
| 15 (B) | A vs F pairing | **resolved** | [A17] l. 590-593; l. 113, 183-185. |

## Regression triggers (§6.7), checked independently

No results exist; STUDY is the origin phase of everything found here.
- selection on held-out or changed after results: not met (l. 204-212 validation only; the rule is unchanged by this verdict).
- validation vs ROC-test AUC > 0.01: not met (no numbers).
- single-seed / < 100-epoch / lab-pod headline: not met. The screen (50 epochs) and REPRO-CHANG are labelled context, not results (l. 65, 585-587).
- cross-N / input-set / split / schedule series: not met ([L6]; A−R labelled a package, [L5]).
- gap < seed sd with < 3 seeds: not met (8 seeds).
- reload > 1e-7 or TF32 on: not met (confound 9).
- EBOPs not remeasured / final-epoch cost mixed: not met (l. 230-233, 446).
- binary layer with > 2 values: not met (check committed, l. 447). The WRAP amendment touches activations only; the check still applies.
- DSP / C-sim / C-synth: not applicable ([L7]).
- per-class AUC < 0.7 hidden: not met (l. 441).
- byte-identical arms / different `y`: not met (gate committed, l. 441).
- failed validation without remediation, or tautological validation: **not met, but close**: [A7] as written is a check that passes trivially (floor ≈ 0 at 0-bit lower bounds). Fixed under fix 1 before it can be run; no ticket.
- [D] replaced without dated amendment: not met so far. Fix 1 changes the activation-quantizer decision and must be dated in the change log.
- outward mismatch: not applicable.

Suspiciously good: nothing to check at STUDY.

## Disputed facts for the investigator

None blocking. The floor is settled by code and arithmetic above; the full-model CPU trace in fix 1
confirms it at PREFLIGHT. (Non-blocking, carried from the investigator: the PVC-side screen check of [A16].)

## Dismissals

None.

## Motivated-reasoning check

- **Is the quantizer amendment goalpost-moving?** No. It is made before any result, it increases
  fidelity to the code Kai asked to replicate (`jsc150` uses HGQ2's WRAP datalane default), the
  infeasibility of the current quantizer is recorded as a zero-GPU finding rather than erased, and
  the pilot's only readout is feasibility, never accuracy.
- The design as written would have spent 336,000 run-epochs on a question the code already answers
  (#1). That is the self-serving risk here: "[A7] gates this" deferred a minutes-long computation.
- "Expected branch: report to Kai" rested on the wrong architecture's timing (#4); with the right one
  the 14-day rule passes and the binding constraint becomes Kai's pod count, which the text must say.
- Survivor bias acknowledged for the mean but not carried to the headline distance (#10).

## Can the floor problem be resolved inside Kai's request?

Yes, as a design amendment the owner makes tonight; it does not need ESCALATE.
- Kai asked to "replicate his code basically" and "keep the conditions the same" with "our binary
  model". Chang's activation, softmax-output and softmax-table quantizers are conditions of his code;
  binary weights are what makes the model ours. Matching them keeps binary weights and is the more
  literal reading. The current SAT, fixed-width choice is a house convenience (`qat.py:292-293`,
  "train == deploy"); no convention mandates it (`quantization-and-cost.md`, grep).
- Matching only the softmax output does **not** work (3,379,360 for A07). A Linformer arm does not work
  under SAT either. Under the full match it is not needed for static feasibility, but it is the natural
  architecture change at N=64 (softmax cost H·T·k instead of H·T²; the paper's 79.8 % row) and a Kai
  option; it is new code and not in the minimum set.
- The matched A07 is statically feasible at 350k by 23k EBOPs only. Whether it can reach 350k with any
  accuracy is dynamic, so a short pre-registered pilot is necessary before 336,000 run-epochs.
- Nothing irreversible happens before Kai returns: production pods are held behind his pod-count answer
  (STUDY l. 358-361), and the canary plus pilot is one pod, inside "a couple of pods".
- Applying [D19] to C and R redefines Kai's "the way it's implemented" from "our quantizer" to "our
  target (C) and our recipe (R)"; the FLAG must say so and offer C' (our SAT quantizer, 5M, 8 runs) as
  an option. C' would sit about 10 % above its static floor (#19).

## Verdict

**ITERATE** (STUDY panel, iteration 2 → fixer, then re-review v3). No validator A lines. Four A
findings (#1-#4, one fix cluster plus timing) and eight open B findings. Warn at 3: the next
iteration will be the third.

Required fixes, in priority order (the fixer works from this list; items 1-3 are design changes the
experiment-designer owns, so route any CANNOT RESOLVE there):

1. **(#1, #2, #3, A) Quantizer amendment, dated [D19] in the change log.**
   - Every arm (A-F and R, including C) uses **Chang's quantizers**: kif `overflow_mode WRAP`, trainable,
     0 bits reachable, for every dense input and the Q, K, V streams; the softmax output into A·V
     learned the same way (HGQ2 `QuantizerConfig(place='datalane')`, `hgq/layers/attn/mha.py:69`); the
     softmax exp input a datalane quantizer, and the exp and inv tables kbi `SAT_SYM`, trainable,
     `bc=Min(4)` (`jsc150/model.py:186-188`). Granularity stays per channel for activations (fidelity
     row "no", as now). The same quantizer in every arm, so A−R, A−C and A−D stay one-knob comparisons.
     Add an [A20] for the ml-engineer: config keys (e.g. `act_overflow wrap`, `softmax_quant chang`), a
     unit test that a WRAP channel at `relu(i+f)=0` costs 0 EBOPs and outputs 0, and a note that under
     WRAP-trainable `i` tracks the data range (`get_minimal_i`) and only `f` feels the EBOPs gradient,
     so "8-bit init" is stated as an `f0` with `i` tracked.
   - Record the **old quantizer's static floors** as a zero-GPU finding, labelled "arbiter arithmetic,
     calibrated to the 24,816,782 trace within 0.09 %, confirmed by CPU trace at PREFLIGHT": A07
     4,559,008 (softmax internals 2,716,672), E 2,690,744, A07 with a 1-bit softmax output 3,379,360.
     The old quantizer is STATIC_INFEASIBLE at 350k and 175k; say why the softmax-only and Linformer
     remedies fail.
   - **Rewrite [A7]**: a CPU trace of every arm under [D19] giving the 0-bit floor (learnable widths at
     their minimum, `bits = relu(i+f) + k` in SAT, `relu(i+f)` in WRAP, tables at 4 bits) and the
     1-bit-alive floor, with the channel budget each target implies. Expected: A07 326,656 / 989,344;
     E 163,328 / 611,000. STATIC_INFEASIBLE if the 0-bit floor ≥ target (so B on A07 at 175k is
     STATIC_INFEASIBLE by this arithmetic).
   - State in Question/Bearing and "Where I am not sure" that matched A07 at 350k keeps 23,344 EBOPs
     outside the softmax at its floor, so any feasible A checkpoint is pruned by construction and may be
     a Deep Set; the attention state (#8 wording) is reported beside the budget claim in every outcome.
   - Fidelity table: rows for softmax output width, softmax exp input and tables, activation overflow
     mode, and weight pruning (Chang per weight to 0 bits; ours binary 1 bit, input-channel pruning
     only). Add [L8]: WRAP overflow wraps on out-of-range inputs at deployment; no synthesis here.
   - Cascade: `campaigns/2026-09-26-method-atlas/BRIEF.md` anchor moves with arm A (note there, with
     the fallback if A has no feasible checkpoint); experiment-log stub line 13; `UPSTREAM_FEEDBACK.md`
     in `campaigns/2026-09-23-confirmation/` for #19.
   - "Where I am not sure": a FLAG block for [D19] (default: full Chang match in every arm;
     alternatives: keep ours and re-target above 4.56M, dropping 79.4 %; add C' at 5M on our quantizer),
     and add to the [D1] block that E (two heads) has eight times A07's non-softmax headroom at 350k.
2. **(#4, A) Timing basis.** Replace l. 332-345 and the R projection with per-run, per-N citations:
   A07-N64 100.09 s per epoch (`live-status.json`, `last_epoch_wall_seconds`, one packed epoch, batch
   256, n_train 496,000, unverified ops number); T_run 8.1 d unscaled, 9.1 d at 558,000 train jets;
   R ≈ 112.6 s → 31.3 h per run, 8 runs on 2 pods ≈ 63 pod-hours; Chang schedule 48 runs at K=6 on 8
   pods ≈ 8 × 9.1 d ≈ 1,750 pod-hours. Drop "245", relabel 83 s as N=8 and 190 s as A02-N64 or remove
   them. Expected [D15] branch: **fits 14 days single-wave**, subject to the canary. State the new
   tension: P = 2 at K=6 is 4 waves ≈ 36 d, which breaks the 14-day rule, so "a couple of pods"
   against 8-10 pods against the cheap version is the binding Kai decision. Correct the stub.
3. **(#5, #6, B) Canary becomes canary-plus-pilot; far-from-budget rule.** One pod, K=6, under
   [D19]: A-s1, A-s2, D-s1, E-s1, E-s2 and F-s1 (B-s1 leaves the canary: statically infeasible on A07).
   It runs 10 epochs for timing, then continues to epoch 500 (one cosine cycle; about 15.6 h at the
   batch-256 prior, a projection) as a pre-registered feasibility pilot: validation only, never quoted,
   never selects an arm or a checkpoint. Rule: if neither A pilot seed has a feasible checkpoint at
   epoch 500, or the median A EBOPs exceeds 3× target, production waits for Kai with the options
   (re-target from the traced floors, make E or a Linformer arm primary, stop); the same rule is
   reported for E. Pilot checkpoints resume into production only on `config_sha256` and `code_sha256`
   match. In production, define the [D13] sd trigger when fewer than 2 A seeds are feasible ("undefined,
   report to Kai"), and report feasible count and median EBOPs / target at epochs 500 and 1,000.
4. **(#9, B) Arm B.** B at 175k on A07 is STATIC_INFEASIBLE under [D19] (floor 326,656), and no
   rung below 350k fits A07. To keep Kai's "some at a lower EBOPs limit", default: move B to the E
   architecture at 250,000 (E floor 163,328; paired with E by seed, same shapes and init), so E − B is a
   target-only gap; A − B is dropped from the secondary ladder. Alternative: cut B first. Record as a [D]
   and update the comparisons table and the Holm set.
5. **(#7, B) Stability claim.** Decide it by the count rule on marginal divergence counts; report the
   exact McNemar p (state two-sided) beside it, outside the Holm family. Holm then covers the recipe
   claim alone among the claims (say so), and the five secondary gaps as now.
6. **(#8, B) Width quantity and Deep-Set wording.** Define the reported width (`relu(i+f)` and `k`);
   under [D19] a 0-bit WRAP channel is a true zero. Replace "a different model, not a Deep Set"
   (l. 303-304, 697-700) with "attention branch removed; the remaining path is Deep-Set-class
   (φ, mean pool, ρ; position-aware through the learned PE)".
7. **(#10, B)** Carry "upper estimate when k < 8" to the distance A − 79.4 (l. 270-279).
8. **(#12, B)** Add the Fig. 2 per-class AUCs (Linformer, MHA, N=64) to the reference table with the
   label above, and report per-class AUC distances beside the accuracy distance.
9. **(#11, B)** One sentence in the arm H / in-house FLAG: the in-house arm inherits the [D19] quantizer.
10. **C items #13-#18**, apply before commit, no re-review needed for them.

## What Kai confirms at the launch gate (not an escalation)

- **[D19] quantizer.** Default: full Chang match (WRAP datalane activations, learned softmax output,
  learned tables ≥ 4 bits) in every arm. Alternatives: keep ours and re-target above 4.56M (drops the
  79.4 % comparison); add C' (ours at 5M).
- **Primary architecture** if the pilot rule fires: default A07 stays primary (Kai: architecture changes
  "for some of them"); options E primary, or a Linformer arm (new code).
- **Pod count**, now binding: 8-10 pods ≈ 9 d single wave, or 2 pods ≈ 36 d (breaks the 14-day rule),
  or the cheap version. Plus arm H and the flagged items already listed.
