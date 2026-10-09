# BNJetTag experiment inventory — 22 September 2026

This is an organizational summary of the experiments found in the research tree, archived research record, lab logs, and saved September status snapshots. Numbers are quoted from those sources; this inventory does not rerun inference or query live training. Status means **last recorded status**, with the observation date preserved. A configuration file alone is not evidence of training.

The project asks how much five-class jet-tagging performance a binary-weight transformer can retain while reducing arithmetic and FPGA resources. The work has progressed through training-recipe repair, precision/capacity studies, hardware implementation, explicit EBOP budgets, architecture/attention changes, classifier refinement, and memory augmentation.

## 1. Campaign map

| Campaign | Training or experimental scope | Recorded outcome |
|---|---|---|
| Early binary/ternary/precision work | Legacy private two-class data; binary, ternary, FP32, W8A8, activation precision and softmax alternatives | Historical experiments exist; not comparable numerically with the later public five-class task |
| Rounds 1–4, June | 10 + 10 + 6 + 4 architecture/recipe jobs; size, normalization, pooling, position encoding, activation function, LR, warmup and seed repeats | Completed; LR tuning explained several apparent architecture wins |
| Round 5, July | Public five-class data, top-10 × 16 features; eight runs across FP32/W8A8/W1A8/W1A6/W1A4 | Completed and held-out predictions verified |
| HGQ2 “FINAL” campaign, July | Large model, five precision arms × three seeds = 15 runs; native quantization-aware training | Completed; learned activation-grid scales repaired severe A4 degradation |
| Round 7 and 7b, July | Small/tiny × five precisions × three seeds = 30 runs; then 12 tiny-model LR probes and 15 retuned tiny runs | Completed; recipe mattered at small scale and binary weights had a larger capacity penalty |
| Round 8, July | Standardized-input and norm-free comparisons; four arms × three seeds = 12 evaluated runs | Completed; established standardized, norm-free model family |
| Round 10, July | Pairwise-invariant attention bias, six trained seeds, compared with archived baseline | Completed; AUC essentially flat and rejection improvement not statistically established |
| Round 11, July | Capacity ladder and matched normalization controls; archived record reports 54 jobs | Completed; binary gap narrowed with capacity but remained against matched W8A8 |
| Round 12 | Distillation code/configs/job definitions | Historical implementation found; completed result not established by the reviewed sources |
| Round 13, August | Four LR probes plus a 1,500-epoch free-activation-width budget sighter | Probes/sighter completed; later matched stages were not launched in the reviewed record |
| Round 14 / pre-conference, August | N = 8/16/32/64 × five precisions × three seeds = 60 runs; three L1 features | Completed; all 60 held-out AUCs reproduced |
| Softmax precision / device fit, August | 6-bit/4-bit probability-grid configurations; trained 4-bit result and hardware characterization | Trained 4-bit result verified; hardware result is a pre-route proxy-device measurement |
| Initial N8 EBOP pilot, September 10 | Control + 75%/50%/25% budgets; 101-epoch design, seed 1 | Three completed; 50% arm failed before its first completed epoch; 75% met budget, 25% missed |
| Resource-priority retry, September 10–11 | Stronger budget penalty, constant LR, stop on reaching 50% budget | Completed after eight epochs; 847,982 EBOPs, recorded validation AUC 0.79728 |
| Standalone long-budget run, September 11 | One N8 seed, 1,000 epochs, 350k target | Launch and intermediate training verified; separate final outcome not recovered in this inventory |
| R0–R6 EBOP ablations, September 12–20 | Seven seed-1 runs × 1,000 epochs, N8 and 350k final ceiling | All seven training runs completed; final selected-checkpoint held-out coverage is not equally current |
| Frozen-output studies, September 16 | Validation-fitted output corrections; frozen-backbone 4-/8-bit classifier refits | Completed CPU fitting/evaluation; small held-out improvements, no FPGA timing measurement |
| A00–A11 architecture/budget study, September 17 onward | 12 seed-1 runs; 100-epoch screen, then continuation to 1,000 | September 21 snapshot: 2/12 reached 1,000; 5/12 had a feasible checkpoint |
| B00–B04 attention study, September 18 onward | Five N16 arms × seeds 4/5/6 = 15 runs; 400-epoch screen, then continuation | September 21 snapshot: 13/15 reached 1,000; 0/15 feasible |
| E00–E03 Engram pilot, September 18 onward | Four N16 seed-1 runs; 100-epoch screen, then continuation | Latest saved snapshot: E00 at 675; E01–E03 at 1,000 but final reload validation failed; 0/4 feasible |
| Matched N8/N64 screen, September 22 | 25 source setup names deduplicated to 19 configurations × two N values = 38 cases; 37 GPU arms | Submitted and initial progress verified; one E07/N64 case statically infeasible; no completed comparative result in reviewed evidence |

These counts must not be summed into one total: controls can be reused, continuations preserve run identities, and failed launches/retries are not new scientific replicates. Round 14 is the same campaign as the pre-conference study. September's R0–R6 labels are separate from historical “Round 4,” etc. The old planned B queue is also distinct from the B00–B04 campaign actually executed.

## 2. What methods we have tried

| Method family | Concrete interventions | What the evidence supports |
|---|---|---|
| Weight precision | FP32, W8A8, binary absmean weights with straight-through gradients; legacy ternary comparisons | Strong matched FP32/W8/binary results exist; no trained Round-14 ternary comparator was found |
| Activation quantization | A8/A6/A4; frozen versus trainable calibration scales; learned widths; tensor versus channel granularity | Frozen calibration hurt low-bit training; learned grids recovered accuracy; per-channel widths are a useful constrained candidate |
| Optimizer/recipe | LR ladders, warmup, decay, longer schedules, repeats at matched seeds | Early architecture rankings were often confounded by LR; a recipe tuned for one size did not transfer automatically |
| Input representation | Private two-class → public five-class; 16 → three features; input standardization; N sweeps | Changes in data/features define separate comparisons; standardization was a major improvement in the older regime |
| Architecture | Width, depth, FFN width, heads, CLS versus mean pooling, GELU/ReLU, position encoding, normalization placement/type/removal | Norm-free standardized models became the reference; smaller FFNs and fewer blocks are under active budget study |
| Attention | Softmax-free legacy arms; 10→8/6/4-bit probability operands; fewer heads; no position table; pairwise physics bias | Probability precision affects hardware; pairwise bias did not establish an AUC gain; new N16 attention arms did not meet 350k in saved status |
| Cost-constrained training | Differentiable EBOP penalty, PID-controlled coefficient, relative/absolute targets, gradual tightening, freeze widths and recover | Budget control can reach lower costs, but targets and categorical accuracy must be checked on the same saved checkpoint |
| Distillation | Frozen teacher logits and CE + temperature-scaled KL; September R6 used T=2 and coefficient 0.5 | R6 completed; final-epoch validation AUC 0.844425 at 344,430 EBOPs is recorded, but final selected held-out accuracy needs refreshing |
| Classifier refinement | Identity/bias/vector-scaling candidates, accuracy-oriented offsets, 4-/8-bit final-layer refit on cached features | Rounded offsets and an 8-bit final head gave modest verified single-seed held-out gains |
| Engram-inspired memory | Discretized constituent tuples, trainable value table, optional key/context gate; table size/precision and hashed rank-bigrams | Initial ungated memory screen was promising; final pilot remains over budget and failed reload validation; expanded variants are in the new screen |
| FPGA mapping | Binary sign/add logic, scale restoration, fabric/DSP binding, reuse/token folding, distributed arithmetic, precision narrowing, fixed-point FP32-baseline export | Binary matmuls can use zero DSP; whole-model LUT, timing, and nonbinary operations remain separate constraints |

## 3. Established precision baseline: Round 14

All arms use top-N constituents with pt, relative eta and relative phi. The reference is D32, four heads, two blocks, FFN64, no normalization, standardized input. Five precision settings were trained with three seeds each on the 101-epoch recipe. There is no enforced EBOP ceiling in this campaign.

Held-out macro one-vs-rest AUC; mean ± sample standard deviation across three seeds:

| N | FP32 | W8A8 | W1A8 | W1A6 | W1A4 |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.8864 ± 0.0005 | 0.8862 ± 0.0009 | 0.8712 ± 0.0016 | 0.8689 ± 0.0020 | 0.8534 ± 0.0012 |
| 16 | 0.9128 ± 0.0013 | 0.9124 ± 0.0014 | 0.8956 ± 0.0002 | 0.8910 ± 0.0009 | 0.8693 ± 0.0021 |
| 32 | 0.9374 ± 0.0017 | 0.9358 ± 0.0011 | 0.9052 ± 0.0079 | 0.9022 ± 0.0009 | 0.8833 ± 0.0013 |
| 64 | 0.9486 ± 0.0012 | 0.9448 ± 0.0011 | 0.9121 ± 0.0116 | 0.9136 ± 0.0061 | 0.9073 ± 0.0009 |

Binary has a resolved deficit versus FP32 at each N. W8A8 tracks FP32 closely. Longer binary sequences show substantial seed variation; three seeds do not resolve every step-to-step trend or every precision difference. These are AUCs, not categorical accuracies. Source: [active research record](../../RESEARCH.md), sections 3–5.

The archived work established why this reference exists: native HGQ2 QAT avoided a separate reconstruction loss; learning grid scales repaired low-bit calibration; input standardization and matched norm-free controls changed earlier comparisons; capacity ladders showed why small binary models can lose substantially more performance than large ones. Sources: [full historical research record](../../_attic/superseded-root-docs/RESEARCH-2026-08-13-full.md) and [archived experiment log](../../.claude/memory/experiment-log.md).

## 4. Seven completed 350k EBOP ablations

Common setup: N8, three features, binary weights, initial A8 learned widths, D32/two blocks/four heads, 496,000 training and 124,000 internal-validation jets, seed 1, 1,000 epochs. Checkpoint selection maximizes validation AUC subject to <=350,000 EBOPs.

The following is the September 16 checkpoint evaluation on the separate 260,000-jet held-out archive. It is newer than the September 15 README table. All seven training loops subsequently completed by September 20, but R6's displayed held-out result remains an interim-checkpoint evaluation.

| ID | Change | Held-out accuracy | Held-out AUC | Checkpoint EBOPs |
|---|---|---:|---:|---:|
| R0 | Tensor-wise reference | 57.4758% | 0.844527 | 348,526 |
| R1 | Channel-wise activation grids | 58.7431% | 0.850795 | 317,890 |
| R2 | FFN64 → FFN32 | 58.3131% | 0.853526 | 329,838 |
| R3 | Attention probability operand 10 → 8 bits | 57.3435% | 0.845380 | 340,174 |
| R4 | Target 1M → 750k → 500k → 350k, in four 250-epoch stages | 57.5085% | 0.846941 | 349,550 |
| R5 | Freeze learned widths at first feasible epoch at/after 800; continue fitting | 56.9404% | 0.840727 | 349,390 |
| R6 | Frozen-teacher distillation | 56.9123% | 0.841338 | 348,366 |

R1 has the largest observed uncorrected categorical accuracy in this evaluated set; R2 has the largest observed AUC. These are single-seed rankings, not established superiority across training seeds. R4 eventually became feasible: the older “no feasible checkpoint” entry is obsolete. The separate September 11 long run is not R0; R0 was freshly initialized for the matched resumable ablation protocol.

Protocol: [seven-arm design](../../bnjettag/code/hgq2/EBOPS_ABLATION_1000.md). Evaluation and completion evidence are listed in the source map below.

## 5. Completed frozen-backbone/output experiments

These were actual fitting and evaluation experiments, separate from the later proposed F-series.

| Method | What was fitted | Held-out result | Limit |
|---|---|---|---|
| Class-specific output offsets | R2's five logits; fitted/selected using two internal-validation subsets; selected 10-fractional-bit constants | 59.0600% accuracy; +0.3169 percentage points versus original R1, paired 95% interval [0.1629, 0.4709] | Native R2 backbone is 329,838 EBOPs; total exported correction cost/timing unmeasured |
| Frozen final-layer refit | R1's final 32×5 weights, fitted on 100,000 training events and quantized to 8 bits | 59.1396% accuracy, 0.855957 AUC, 322,510 native EBOPs; +0.3965 points versus original R1, interval [0.3191, 0.4740] | Mixed precision: 14 earlier weight layers binary, final head 8-bit; hardware unmeasured |

Also tested: identity, bias-only and vector scaling, accuracy-oriented bias sweeps, alternative constant precision, two ridge strengths and 4-bit final weights. The 4-bit head lost validation accuracy; the weaker ridge candidate did not converge within its fitting budget. The channel model's selected output correction did not improve held-out accuracy.

The two successful refinements are alternatives. Their mutual accuracy difference was not resolved by the paired interval. Intervals above describe held-out event variation conditional on one trained checkpoint, not training-seed robustness. Separately, the trainer was updated to log validation categorical accuracy and support accuracy-based checkpoint selection for new studies.

## 6. Architecture and budget study: A00–A11

Seed 1 throughout. All twelve completed the 100-epoch screen and were later authorized to continue to 1,000, superseding the initial selective-promotion plan. Selection now prioritizes validation categorical accuracy under the final budget. Default D32/two blocks/four heads; exceptions are explicit below.

| Arm | N | FFN | Grid | Other change | Target | Feasible val accuracy in September 21 snapshot |
|---|---:|---:|---|---|---:|---:|
| A00 | 8 | 64 | Channel | Reference | 350k | 58.77% |
| A01 | 8 | 64 | Tensor | Granularity | 350k | 58.25% |
| A02 | 8 | 32 | Channel | Smaller FFN | 350k | 60.55% |
| A03 | 8 | 32 | Tensor | Smaller FFN + tensor grids | 350k | 59.44% |
| A04 | 16 | 32 | Channel | More constituents | 350k | None |
| A05 | 32 | 32 | Channel | More constituents | 350k | None |
| A06 | 16 | 32 | Channel | D16 | 350k | None |
| A07 | 16 | 32 | Channel | One block | 350k | None |
| A08 | 16 | 32 | Channel | Two heads | 350k | None |
| A09 | 16 | 32 | Channel | Relaxed budget | 500k | None |
| A10 | 16 | 32 | Channel | Tighter budget | 250k | None |
| A11 | 8 | 32 | Channel | Relaxed budget | 500k | 62.38% |

The five feasible checkpoint costs were A00 349,322; A01 344,270; A02 342,832; A03 346,222; A11 453,439. A02 is the highest recorded feasible validation accuracy among the 350k arms in this snapshot. Training prefixes differ and only A03/A04 had completed 1,000; this is not a final held-out ranking. A11 belongs in a separate 500k comparison.

The September 20 efficiency report used the earlier common 100-epoch checkpoint, when none was feasible. Its A03 efficiency ranking and the later A02 feasible-accuracy ranking answer different questions. The proposed Accuracy–Cost Index is a descriptive utility, not a hardware measurement; its study-normalized scores cannot rank different campaigns against each other.

## 7. Attention study: B00–B04

N16/D32/two blocks/FFN32/channel grids, 350k budget, seeds 4/5/6. Fifteen runs completed a 400-epoch screen and then continued toward 1,000.

| Arm | Change from B00 | Observations at the common 400-epoch screen |
|---|---|---|
| B00 | Reference | Mean validation accuracy 33.07% ± 6.25 percentage points |
| B01 | Four → one attention head | Lowest mean cost, 465,514 EBOPs; mean accuracy 33.68% ± 0.94 points |
| B02 | Remove learned position table | Highest observed mean accuracy, 39.03% ± 4.64 points; 722,239 mean EBOPs |
| B03 | 8-bit attention probabilities | Mean accuracy 35.35% ± 5.09 points |
| B04 | Target 525k → 420k → 350k at cumulative epochs 0/100/200 | Mean accuracy 35.06% ± 5.42 points |

Spreads are sample standard deviations over three seeds. None had a feasible checkpoint at 400 epochs. At the September 21 continuation snapshot, 13 had reached 1,000; B02/s6 was at 989 and B03/s6 at 867. Still none had a feasible checkpoint. The one-head and no-position-table observations do not establish a successful 350k model.

## 8. Engram-inspired memory: E00–E07

The N16 pilot maps discretized constituent features to a small trainable table. Eight bins for each of three features give a collision-free 512-row tuple address. E02 retrieves a value vector; E03 adds a key and context-dependent quantized gate. The backbone remains binary, while memory values/keys are multibit. Memory and backbone train jointly, with 5× table LR and no table weight decay.

| Arm | Method | Original N16 pilot status |
|---|---|---|
| E00 | Two-block reference | 675 completed epochs in latest saved snapshot |
| E01 | One-block control | 1,000 epochs; final metric-reproduction check failed |
| E02 | One block + ungated memory | 1,000 epochs; final check failed |
| E03 | One block + gated memory | 1,000 epochs; final check failed |
| E04 | Two blocks + gated memory | Configured follow-up; no original N16 training result found |
| E05 | Four-bit memory | Configured follow-up; no original N16 training result found |
| E06 | Smaller 64-row tuple table | Configured follow-up; no original N16 training result found |
| E07 | Hashed constituent-rank bigrams | Configured follow-up; no original N16 training result found |

At the common 100-epoch screen, E02 recorded 61.03% validation accuracy at 533,092 augmented-cost operations, versus E01's 56.10% at 566,719. This was promising but over budget. At epoch 1,000, E02 logged 54.55% accuracy / 0.8322 AUC / 380,009 cost; E03 logged 52.55% / 0.8203 / 440,525. No pilot arm recorded a feasible 350k checkpoint.

E01–E03 failed the outer saved-checkpoint metric comparison. Their COMPLETE.json files establish completed training loops only. E02/E03 prediction exports left from the 100-epoch screen are historical, not verified 1,000-epoch results. The latest publication snapshot is September 22 at 06:46 UTC. E04–E07 subsequently enter the new N8/N64 screen, which is a separate protocol and does not complete their original N16 pilot designs.

Cost is native HGQ2 backbone EBOPs plus custom estimated memory arithmetic; logical/replicated storage is a separate constraint. This convention is not interchangeable with native-only costs, and no Engram HLS implementation or measured FPGA advantage exists in these records.

## 9. New matched N8/N64 screen

Submitted September 22 at 07:46 UTC; initial progress saved at 07:57 UTC. It covers all 12 architecture/budget source configurations, five attention variants and eight Engram designs. After normalizing N/seed and merging equivalent controls there are 19 distinct setups, 38 cases, and 37 trainable GPU arms. E07/N64 is statically rejected: memory arithmetic alone is 838,272 against its 350k ceiling.

This is fresh seed-1 training for 50 epochs, LR 2e-4, one warmup epoch, 49 decay epochs and one-epoch PID warmup. Paired N8/N64 arms have the same absolute 250k/350k/500k cap and data identities. Gradual targets reach the final cap at epoch 10. Engram storage caps are 64 KiB logical / 2 MiB estimated replicated tables at both N values.

The initial canary exposed live-versus-reloaded metric disagreement. Corrected runs disable TF32 and select from freshly reloaded saved candidates, retaining the strict 1e-7 check. This change does not retroactively validate old Engram outputs. The short schedule is ten times the historical learning rate; compare N8 and N64 within this campaign, not as equal-training replacements for the old 1,000-epoch studies. No completed campaign result was present in the reviewed launch evidence.

Protocol and exact source-name mapping: [study README](../../bnjettag/code/constituent-study-20260922/README.md) and [38-case index](../../bnjettag/code/constituent-study-20260922/index.json).

## 10. Hardware work already attempted

| Work | Outcome |
|---|---|
| QKeras reconstruction, then native HGQ2/hls4ml export | Native QAT improved correspondence; trained-grid preservation and explicit learned-scale restoration became essential |
| Large 6.4M-model monolithic/hybrid/per-block synthesis | Whole-design compiler/memory limits prevented a usable large-model result; motivated deployable-size retraining |
| Binary sign/add arithmetic and accumulator fixes | Binary matrix products demonstrated zero DSP; attention, softmax, normalization and learned-scale affines needed separate accounting |
| Global reuse and token/dataflow folding, pipelining/rewind | Measured scheduling/throughput/area tradeoffs; tensor reuse factors alone did not guarantee whole-jet II=1 or LUT reduction |
| Fabric-bound normalization, norm-free models, solution-wide/scoped multiply binding | Reduced DSP use with differing LUT/timing costs; scoped HLS zero-DSP counts could regain DSPs after Vivado mapping |
| Distributed arithmetic / adder sharing / compressed-LUT and factorization studies | DA on pure +/-1 matrices was negative in the archived whole-model test; counting estimates were not substitutes for synthesized results |
| Round-14 softmax precision reduction and retraining | Trained 4-bit probability-grid point retained AUC 0.8701 ± 0.0020 and measured 0 DSP / 1,689,320 CLB LUT at Vivado post-opt in the xczu7ev proxy flow; 97.8% of VU13P LUT capacity, not a VU13P routed implementation |
| W8A8 and FP32-trained fixed-point baseline exports | Hardware comparators measured; FP32-trained fixed-point conversion is not literal floating-point silicon |
| September R4 learned-width export/synthesis | Export fidelity and local/Linux C simulation passed on 4,096 jets; HLS frontend failed before RTL, so no new resource/timing result |
| Proposed H-series: II=1 with 0/1/2.5/5% DSP caps | Planned follow-up; no completed campaign found |

September R4 debugging also repaired a zero-grid ReLU/quantizer conversion error. The later diagnostic identified an unsupported `config_array_partition -maximum_size` directive in the hls4ml/Vitis combination; earlier linkage explanations were superseded. Hardware estimates, proxy-device netlists, and routed hardware must remain separate. Source: [research record, section 6](../../RESEARCH.md) and the lab synthesis evidence below.

## 11. How to keep the experiments organized

Maintain one row per scientific run with campaign/arm/seed, N/features, architecture, precision/granularity, target and cost convention, selection metric, planned/completed epochs, selected checkpoint digest, validation metrics, held-out evaluation date, and hardware stage. Track execution, feasibility and verification separately: “1,000 epochs complete,” “over budget,” and “reload failed” can all be true.

The highest-priority gaps exposed by this inventory are:

1. Refresh the selected-checkpoint evaluation for completed R0–R6, especially R6, and replace stale September 15 summaries while retaining their dates.
2. Obtain one fresh comparable snapshot of the 31 A/B/E continuations; the saved records have different observation times and training prefixes.
3. Resolve original Engram reload failures before treating full-length artifacts as verified results.
4. Analyze the new N8/N64 screen separately, preserving failed/infeasible cases and original aliases.
5. Confirm selected constrained models across seeds, then measure their exported hardware. Existing single-seed accuracy observations and EBOP proxies cannot settle deployment.

## 12. Source map

Research-tree sources above are relative links. The following lab sources are local evidence paths; no remote service was queried for this inventory.

- [Legacy training, ternary inventory, R13 and hardware history](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/.claude/memory/archive/experiment-log.md>)
- [September experiment chronology](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/.claude/memory/experiment-log.md>)
- [September 16 seven-checkpoint evaluation and frozen-output experiments](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/local/accuracy-investigation/README.md>)
- [Frozen-output methods and tested alternatives](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/local/accuracy-investigation/FROZEN_BACKBONE_METHODS.md>)
- [Seven original ablations: completion and final-epoch evidence](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/publication-engram-20260921/results/post_conference/ablation-training-status-20260920.json>)
- [Architecture and attention: September 21 durable checkpoint snapshot](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/local/results-status-20260921/summary.json>)
- [Matched screening-prefix efficiency analysis](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/local/performance-index-20260920/REPORT.md>)
- [Latest original Engram pilot status and failures](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/publication-engram-20260921/docs/current-work/ENGRAM_STUDY.md>)
- [Engram machine-readable evidence](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/publication-engram-20260921/results/engram/status-20260921.json>)
- [Architecture campaign plan](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/publication-engram-20260921/docs/current-work/TRAINING_BATCH_PLAN_WITH_FROZEN_BACKBONE_FOLLOWUP.md>)
- [Attention campaign protocol](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/publication-engram-20260921/docs/current-work/BATCH20260918_ATTENTION_STUDY.md>)
- [September 22 launch progress](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/local/constituent-study-20260922/screen-start-verification.json>)
- [R4 synthesis handoff](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/publication-engram-20260921/docs/current-work/R4_HARDWARE_SYNTHESIS.md>)
- [R4 remote synthesis evidence](</Users/kaiyamaguchi/Desktop/bnjettag-lab/bnjettag-lab 2/local/synthesis-r4-gradual-20260917/remote-evidence/status.json>)

## Appendix: 31 continuation runs, last saved observations

A/B observations: 2026-09-22 00:39 UTC (September 21 PDT). Engram observations: 2026-09-22 06:46 UTC (September 21 PDT). All targets are 1,000 epochs. These are internal-validation checkpoint-state metrics, not freshly evaluated held-out results. Selected-point epoch indices in source JSON are zero-based; the completed-epoch column below is a count.

| Run | Completed epochs | Final cap | Feasible checkpoint | Feasible val accuracy | Feasible val AUC | Feasible cost | Execution/verification |
|---|---:|---:|---|---:|---:|---:|---|
| batch20260917-a00-s1 | 761 | 350,000 | Yes | 58.77% | 0.8502 | 349,322 | Continuation incomplete at snapshot |
| batch20260917-a01-s1 | 780 | 350,000 | Yes | 58.25% | 0.8473 | 344,270 | Continuation incomplete at snapshot |
| batch20260917-a02-s1 | 663 | 350,000 | Yes | 60.55% | 0.8580 | 342,832 | Continuation incomplete at snapshot |
| batch20260917-a03-s1 | 1000 | 350,000 | Yes | 59.44% | 0.8563 | 346,222 | Training complete |
| batch20260917-a04-s1 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260917-a05-s1 | 681 | 350,000 | No | — | — | — | Continuation incomplete at snapshot |
| batch20260917-a06-s1 | 612 | 350,000 | No | — | — | — | Continuation incomplete at snapshot |
| batch20260917-a07-s1 | 994 | 350,000 | No | — | — | — | Continuation incomplete at snapshot |
| batch20260917-a08-s1 | 545 | 350,000 | No | — | — | — | Continuation incomplete at snapshot |
| batch20260917-a09-s1 | 887 | 500,000 | No | — | — | — | Continuation incomplete at snapshot |
| batch20260917-a10-s1 | 622 | 250,000 | No | — | — | — | Continuation incomplete at snapshot |
| batch20260917-a11-s1 | 534 | 500,000 | Yes | 62.38% | 0.8736 | 453,439 | Continuation incomplete at snapshot |
| batch20260918-b00-s4 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b00-s5 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b00-s6 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b01-s4 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b01-s5 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b01-s6 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b02-s4 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b02-s5 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b02-s6 | 989 | 350,000 | No | — | — | — | Continuation incomplete at snapshot |
| batch20260918-b03-s4 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b03-s5 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b03-s6 | 867 | 350,000 | No | — | — | — | Continuation incomplete at snapshot |
| batch20260918-b04-s4 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b04-s5 | 1000 | 350,000 | No | — | — | — | Training complete |
| batch20260918-b04-s6 | 1000 | 350,000 | No | — | — | — | Training complete |
| engram-e00-s1 | 675 | 350,000 | No | — | — | — | Continuation incomplete at snapshot |
| engram-e01-s1 | 1000 | 350,000 | No | — | — | — | 1,000-epoch loop complete; final reload failed |
| engram-e02-s1 | 1000 | 350,000 | No | — | — | — | 1,000-epoch loop complete; final reload failed |
| engram-e03-s1 | 1000 | 350,000 | No | — | — | — | 1,000-epoch loop complete; final reload failed |

Engram caps use the augmented native-plus-memory convention; A/B caps use native HGQ2 EBOPs. “No feasible checkpoint” is an observed outcome, not a missing metric interpreted as zero.
