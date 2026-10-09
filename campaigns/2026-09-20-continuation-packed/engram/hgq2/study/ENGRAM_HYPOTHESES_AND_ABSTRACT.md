# Engram-inspired jet memory: prospective pilot

Prepared 2026-09-18, before pilot training. This document records the intended comparisons and interpretation before observing their results. It is an internal prospective plan, not an externally registered study. The operator freezes this document with the training code and records its SHA256.

## Objective and audit verdict

Prioritize classification accuracy within the allowed computation and storage budgets; then seek lower attained cost while preserving accuracy. The immediate question is whether a small, quantized lookup memory can compensate for removing one transformer block in the existing binary jet tagger.

**Verdict:** the forward model, train-only tokenization, initialization, optimizer, checkpointing, and exploratory comparisons form a coherent training experiment, subject to the preflight checks. There is no theorem or existing jet result guaranteeing improvement. The experiment is ready for a bounded pilot, not an FPGA performance claim. The audit exposed measurement and interpretation limitations; they are made explicit below rather than assumed away.

This is an **Engram-inspired adaptation**, not a reproduction of DeepSeek Engram. Our jet classifier performs a complete forward pass over 16 constituents and has no autoregressive attention KV cache. Such a cache stores a sequence's previous attention keys and values during generation; it is unnecessary for this task. The proposed memory instead stores learned, persistent table parameters. Its keys and values serve a different purpose and do not require an attention KV cache. See the [research and implementation review](ENGRAM_RESEARCH_AND_RUNBOOK.md) for the primary literature and code audit.

## What the module computes

Each constituent has standardized `pt`, `etarel`, and `phirel`. Training-only quantile boundaries discretize these three values into eight bins each. The default address `64 * pt_bin + 8 * eta_bin + phi_bin` selects one of 512 rows exactly, without hashing collisions. This is a joint description of **one constituent**, not a pairwise interaction or a linguistic n-gram. Cross-constituent context can enter the gate through the preceding attention layer. Padding is masked.

The ungated module adds a retrieved 32-dimensional value vector to the first attention residual. The gated module also retrieves a key vector and computes

```text
q = fixed_point_quantize(hidden)
g = quantize_4bit_unsigned(clip(0.5 + dot(q, key) / (4 * 32), 0, 1))
output = hidden + quantize(g * value)
```

Keys, queries, and values use the explicitly specified fixed-point grids in the implementation. The gate has step 0.125. Therefore, when `abs(dot(q, key)) < 8`, it rounds to 0.5; round-to-even also sends the two boundary ties to 0.5. A numerically valid gate can consequently remain nearly constant. The model still has a lookup residual in that case, but an accuracy improvement would not establish useful context-dependent gating.

Values start at zero, preserving the matched backbone's initial predictions exactly. Value gradients can begin immediately; gradients into keys require nonzero values. Straight-through quantization is a surrogate optimization method, not the exact derivative of a discrete lookup system. The memory optimizer applies a real 5× update learning rate, with zero table weight decay and normal Adam state/resume behavior. These are design choices borrowed in spirit from the reference, not proven optima for jet tagging.

## Bounded pilot

Only E00–E03, seed 1, are launched. E04–E07 remain unlaunched follow-up configurations. Every pilot arm stops at cumulative epoch 100 on the existing 1,000-epoch learning-rate schedule. Thus roughly 90% of the starting learning rate remains at the stop: this is an early optimization screen, not a converged comparison.

| Arm | Backbone | Memory | Comparison and question |
|---|---|---|---|
| E00 | Two blocks | None | Reference at the same training prefix and cost target |
| E01 | One block | None | Versus E00: what changes when one block is removed? |
| E02 | One block | 512-row ungated values | Versus E01: does the lookup residual recover accuracy within the budget? |
| E03 | One block | 512-row gated keys and values | Versus E02: is the entire gated design worth its extra capacity and estimated cost? |

Common settings include input contract, training/validation arrays and order, seed, batch size, optimizer schedule, binary backbone scheme, channelwise precision search, and a 350,000 augmented-cost target. E01–E03 share matched backbone initialization. E00 uses the same initialization procedure and seed at its own depth; all equal-shaped variables across depths are not guaranteed identical because random initializers follow graph construction order. Reduced depth also changes optimization and representational capacity. The existing cache contains 496,000 training and 124,000 validation jets. Its four arrays are rehashed before training; the physics test set is never loaded. Tokenizer calibration uses only the fixed first 4,096 shuffled training examples.

Operational scope: one additional GPU at a time, a 24-hour deadline for the whole indexed GPU job, durable separate output directories, and private W&B project `kayamaguchi-uc-san-diego/BNJetTag-Engram-Experimental`. There is no automatic full-length continuation, broader sweep, hardware synthesis, report sharing, or publication. A deadline or failed arm means an incomplete pilot, not a negative scientific result.

## Prospective hypotheses and expectations

**H1 — replacement capacity.** E02 or E03 may recover some accuracy lost by E01 relative to E00. Lookup tables offer a cheap way to learn localized responses in constituent feature space; their usefulness depends on whether those responses complement the remaining attention and FFN. Conversely, a removed block's interactions may be irreplaceable by this memory. An under-budget memory arm with higher validation accuracy than E01 is a promising screening observation. Recovery to E00, at equal or lower attained cost, is a stronger observation. No numerical gain is forecast.

**H2 — gated design tradeoff.** E03 may improve accuracy over E02 if context-dependent modulation is useful. It may instead remain approximately a constant-gain residual or lose accuracy because its larger fixed cost leaves less budget for backbone precision. E03 versus E02 changes keys, capacity, scaling, rounding, and compute allocation together; it does **not** isolate a causal benefit from gating alone. Nonconstant gate measurements plus better accuracy are suggestive, not a mechanism proof. A later static-0.5 control and a matched-budget/precision control would be needed for that narrower claim.

**H3 — accuracy/cost frontier.** A memory arm may offer a better measured accuracy/cost tradeoff. Removing a block does not guarantee lower attained EBOPs: the precision controller can spend the released budget on wider activations. A shared 350,000 target primarily tests accuracy under that cap. Demonstrating lower cost at retained accuracy requires reporting actual attained costs and, subsequently, explicitly lower-target runs with replicated seeds. Logical table storage and access bandwidth must also remain acceptable.

**Expected engineering observations.** Exact tuple addressing has no hash collisions, but different continuous inputs deliberately share bins. Low occupied-row count can reveal limited effective capacity; occupancy alone does not measure collisions or generalization. Successful table learning should produce nonzero effective values and residuals. A gate concentrated at 0.5 would be an actionable explanation for weak gating benefit. Large residual-to-hidden ratios, query clipping, or gate saturation would motivate a separately specified numerical revision, not a silent change during this pilot.

## Measurements and cost limits

Rank feasible checkpoints by validation categorical accuracy, then cheaper augmented cost, then macro AUC, then earlier epoch. Report the selected epoch, completed training prefix, budget status, native HGQ2 backbone EBOPs, custom estimated memory bit operations, their sum, logical table bytes, read traffic, and the stated replication scenario. Preserve all arms, including failures and over-budget results.

The memory estimator is **not** HGQ2's native EBOP measure and is not calibrated to synthesized hardware. Its total with native backbone EBOPs is an augmented screening proxy. Addressing, comparisons, gates, residual addition, and read traffic have different hardware implications; the implementation's fixed-width allowances do not establish complete gate-level cost. Do not label a 350,000 augmented total as 350,000 measured native EBOPs. Training uses floating-point dot accumulation; bit-exact accumulation/lowering remains future work.

At N=16 and D=32, E02 uses 16 KiB logical table storage and estimates 17,920 custom bit operations; E03 uses 32 KiB and estimates 78,496. These estimates must be checked against the frozen ledger. A two-read-port packed key/value ROM supplying all 16 constituent reads concurrently would require eight copies: 256 KiB for E03 before block sizing and routing. This is an illustrative access scenario, not a measured BRAM requirement or a proven initiation interval. Enforce the existing 64 KiB logical and 512 KiB replication-scenario caps. Export rejects the unsupported module rather than silently dropping it.

Every epoch also logs gate histograms, mean, standard deviation, fraction equal to 0.5, saturation, query clipping, effective nonzero values, residual nonzero fraction and RMS, and residual/hidden RMS. These are observations on a fixed 256-example training probe, not validation-derived optimization targets or whole-dataset distribution claims. Baselines log the separate cost components too. Final artifacts include selected validation predictions, tokenizer, quantized tables, cost contract, config/source provenance, and private tracking destination.

## Interpretation before any abstract claims

Compare only identical validation hashes, seed, and completed training prefix. Paired bootstrap differences from stored predictions describe finite-sample validation variation conditional on the selected checkpoints. Because the same validation set selected those checkpoints, these intervals are descriptive: they do not establish formal significance, noninferiority, or uncertainty across training seeds. Report differences in percentage points, interval caveats, attained costs, and all four arms together.

| Observed pilot result | Supported interpretation | Next evidence needed |
|---|---|---|
| E02 beats E01, remains feasible | Lookup residual is promising at this early prefix | More seeds and longer matched training |
| E03 beats E02, gate varies | Gated package is promising | Static-gain and matched-allocation controls |
| E03 beats E02, gate nearly constant | Package benefit without demonstrated dynamic gating | Static-0.5 control |
| Memory matches/exceeds E00 at lower attained proxy cost | Candidate empirical frontier improvement | Replication, lower-target sweep, untouched test evaluation |
| Memory improves accuracy but exceeds cap | Accuracy observation, objective not met | Explicitly redesigned or lower-cost arm |
| No benefit at epoch 100 | No early-prefix benefit observed | Convergence checks before rejecting the mechanism |
| All arms miss cap, fail, or stop at unequal prefixes | Pilot cannot answer the constrained comparison | Repair operational cause or preregister revised experiment |

Do not claim a discovery from this pilot alone. Before a results abstract, obtain replicated seeds, converged/equally trained controls, a frozen selection procedure, and one final untouched test evaluation. Before any FPGA efficiency claim, lower and verify the actual address/gather/gate computation, measure synthesis resources, timing, bandwidth and whole-jet initiation interval. E04 is also a budget-reallocation comparison, not a pure added-capacity control; E06 jointly changes discretization and storage.

## Preliminary abstract — proposal language, no results yet

We investigate whether a small quantized lookup memory can preserve classification accuracy when reducing the depth of a binary transformer for jet tagging. Inspired by Engram's separation of learned memory from computation, we map discretized constituent features to trainable value vectors and optionally modulate them using the attention representation. The method operates without an autoregressive key–value cache. A controlled pilot compares a two-block reference, a one-block baseline, and ungated and gated memory variants using identical data, equal training prefixes, and an explicit computational budget. The three one-block variants share matched backbone initialization. Evaluation separates classification accuracy, native backbone EBOPs, estimated memory computation, and storage/access requirements. Gate and residual diagnostics assess whether the learned memory is active and whether modulation is context dependent. The study tests whether lookup capacity can compensate for reduced transformer depth and identifies the additional statistical and hardware validation required to establish an accuracy–efficiency improvement.

Replace proposal language with measured findings only after the corresponding evidence exists. Retain the distinction between estimated computational cost and validated hardware efficiency.
