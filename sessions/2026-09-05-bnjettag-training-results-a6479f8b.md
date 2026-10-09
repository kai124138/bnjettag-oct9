---
title: okay, i want you to organize everything and figure out where the reseach…
date: 2026-09-05
updated: "2026-09-09T22:19:54"
project: bnjettag-training-results
cwd: /Users/kaiyamaguchi/Downloads/bnjettag-training-results
model: claude-fable-5-1
git_branch: main
session_id: a6479f8b-f5d4-45fa-9543-a5b2ebb86506
turns: 32
tool_calls: 107
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-training-results
---

# okay, i want you to organize everything and figure out where the reseach…

> [!abstract]- Session at a glance
> **32** turns · **107** tool calls · spans **3** days · `claude-fable-5-1`
>
> **Tools** Bash ×64, WebFetch ×20, Write ×13, WebSearch ×8, Edit ×1, ToolSearch ×1
> **Commands** `/effort`
>
> **Files changed**
> - [[docs/reports/research-reset-2026-09-05.md]]
> - [[docs/literature/hls4ml-fpga-triggers/2604.22293_hgq_lut.md]]
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/START-HERE.md`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/theory/README.md`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/theory/01-thesis.md`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/theory/02-model.md`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/theory/03-hardware-mapping.md`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/theory/04-numbers.md`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/theory/05-open-questions.md`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/CODE-MAP.md`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/bn`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/ops/zdot/.zshrc`
> - `/Users/kaiyamaguchi/Downloads/bnjettag-restart/ops/COMMANDS.md`

---

## You · 12:35

okay, i want you to organize everything and figure out where the reseach stands, most of all im concered about the framework diferneces that we have from other HGQ and the LUT-aware trainigs that's become predominant these days and want to figoure out why our LUT count is so high, in the order of millions and want ot shorten that up, but also figure out the licensing issues with VU13P and such and vivado syntehsis, but also be aware of the changes thats coming to HLS4ML. I just finiished attending fastml conference, and i want to sort of take a step back and restart, in someways, my research and figure out more on where we stand and what we can do

---

## Claude · 12:35

I'll start by orienting: reading the living record, the memory logs, and the uncommitted state, then I'll check with the advisor before writing anything.

Reading the notes and the stores done. Now pulling the external facts: the hls4ml developer-forum agenda from yesterday, the HGQ-LUT and FPGN papers, and AMD's current Vivado licence tiers.

Still gathering: reading the Alkaid half of Chang Sun's tutorial, then I'll check the plan with the advisor before writing anything.

Writing the deliverables now: the reset memo in `docs/reports/`, a research-log entry with sources, and an HGQ-LUT literature note.

Done writing. Everything is on disk; here is the picture.

**Where the research stands** (all from `RESEARCH.md` §5–§6, nothing new measured)

- **Accuracy, N = 8:** binary W1A8 0.8712 ± 0.0016 vs FP32 0.8864 ± 0.0005. The deficit is resolved at every N and roughly doubles above N = 16, where binary QAT goes seed-unstable.
- **Silicon:** one fitting zero-DSP operating point exists, the retrained 4-bit-softmax arm at 97.8% of the VU13P LUTs, 0 DSP demand, timing met at 5 ns pre-route. Out-of-context on xczu7ev with a 2.2% margin.
- **Baselines don't fit:** W8A8 at 146% plus 5,550 DSPs demanded. The FP32-trained network on a 16-bit datapath needs 1,140% of the DSPs and its Vivado run died on BRAM.
- **Open flanks FastML put in the room:** no ternary arm, no HGQ-heterogeneous arm, N ≥ 16 never synthesized whole-model, 2.5 ns never met.

**Why the LUT count is in the millions.** It is not a pipeline defect. The n8 model has 133,024 binary MACs, all instantiated, and a ±1 weight with no zero state costs one full adder of activation width every time. That family is only 28% of the fitting design's csynth LUT. The rest is transformer overhead an MLP doesn't carry: β-restore affines 26%, act×act attention 14%, dataflow glue 18%. Per MAC at whole-model scope we are about 27 csynth LUT against Sloot's 21, so comparable to slightly worse, and the whole gap is the non-matmul half. The framework difference versus HGQ is one fact: HGQ reaches 0 DSP by pruning most weights to 0 bits and deleting the operation, while binary keeps every operation and only makes it cheap. That is why Sloot's ternary beat his binary on every axis.

**Licensing.** The 2026-08-23 decision retired the VU13P request; I did not reverse it, only listed what changed. AMD's 2026.1 tiers put Virtex UltraScale+ at Core and above, roughly $1.2–1.8k per year, and the University Program is explicitly unchanged, so the drafted XUP request is still a free route. Both facts come from third-party summaries because AMD's pages timed out twice. Verify against AMD's device table before quoting. Also ask the UCSD L1 group how they build correlator firmware.

**hls4ml.** 1.3.0 is current and we are on the surviving side of the planned Vivado-backend and Keras 2 retirement. 1.4.0 is blocked on a softmax consolidation that touches exactly our two softmax findings, so re-gate before any cross-version comparison. One of our three upstream defects, the ThresholdedReLU fall-through, was fixed on main by PR 1534 on 2026-08-28. The other two are unfiled, and a 90-day stale-issue auto-close is about to switch on.

**The restart menu** is in the memo as eight arms. The cheapest decisive pair is A plus C: a ternary comparison baseline at n8, and β constrained to powers of two so the 26% affine family becomes shifts. Six training runs and two synthesis chains test both framework-level explanations of the LUT count without abandoning the binary thesis.

**Files written:** `docs/reports/research-reset-2026-09-05.md` (the memo), a dated research-log entry with every URL, a literature note for HGQ-LUT, and one INDEX line.

**Nothing committed.** The tree carries the whole FP32-baseline campaign plus poster material uncommitted. The memo lists a four-commit split and two debris files to drop first.

---

## You · 18:11

but are we able to decrease the amount of LUTS or no? and also, we ahve to consider what is "binary" about our work and the extent that our research is original

---

## Claude · 18:12

**Can the LUT count come down? Yes, but not by the lever the thesis is named after, and no number can be promised before an arm runs.** The conversion-level levers are exhausted: every one was measured and closed, and four cost-model projections were each killed by the measurement they predicted. What is left is training-recipe changes, and the record shows what each one touches:

- **β as powers of two.** The 15 affines are 26% of the fitting design's csynth LUT, as much as the binary matmuls themselves. Shifts instead of constant multiplies would remove most of that family. The unknown is the AUC cost of quantizing β.
- **Narrower activations.** The A4 arm already measured −57% on the scores einsum when both operands went to 4 bits. The adder width in the binary matmuls scales the same way. This arm failed the fidelity gate only because β was restored through the narrow grid, so it depends on the β lever first.
- **A zero state in the weights.** Ternary or pruned binary deletes adders outright. This is the mechanism behind Sloot's ternary beating his binary, and it caps at the matmul family's 28%.
- **A smaller model.** The MAC count multiplies every family. This is the one lever guaranteed to work, at an unknown AUC price.
- **RTL emission instead of Vitis HLS.** The dataflow glue is 18% and is a Vitis artefact. Alkaid's ternary-adder fusion is an RTL-only optimization. Unmeasured for us.

The honest ceiling: deleting the binary matmuls entirely would still leave 72% of the design. Tens of percent are plausible from β plus A4 plus sparsity together. An order of magnitude needs a smaller model or a different mapping.

**What is actually binary.** The weights of the 13 matmuls, each with one real β per tensor. Nothing else is: activations are 8-bit, the attention products are 8×8 multiplies, β restoration is 15 constant multiplies, softmax is tables plus multiplies. In the fitting design the 1-bit part is 28% of the LUTs. The zero-DSP result is also not binary alone. The binary matmuls draw 0 DSP natively, but all 4,133 DSPs at C-synthesis belong to the non-binary parts, and the whole-model zero needs a solution-wide fabric binding. "Binary-weight transformer" is accurate. "Binary network" is not, and we should stop implying it.

**Originality, as the record and our 55-paper index show it.** Binary weights giving 0 DSP is not new: FINN-era BNNs, LUTNet, and now Sloot in hls4ml all have it, and HGQ reaches 0 DSP by a different route at a tenth the LUTs. BitNet's absmean STE is Microsoft's. What nobody else has:

- A binary-weight transformer with attention taken through hls4ml to a Vivado netlist on trigger-native inputs. Sloot is an MLP at C-synthesis. The transformer papers are multi-bit.
- The finding that a C-synthesis DSP count of zero does not survive technology mapping unless the binding is solution-wide.
- That β restoration is structural in a norm-free transformer, where in an MLP it folds away for free.
- The mechanism by which weight-grid density, not nominal width, decides DSP inference, shown on a controlled pair.
- Binary QAT destabilizing at long sequences.

The weak flank is the framing. Against W8A8 the regime argument holds, but the real competitor is a pruned heterogeneous network, and against that a dense binary core is dominated at every scale anyone has measured. The defensible thesis after FastML is not "binary is best" but the controlled comparison nobody has run: binary versus ternary versus HGQ-pruned weights in one transformer, one flow, at the netlist stage. That is arms A, B and C of the memo, and it is a paper whether binary wins or loses.

---

## You · 18:14

but if only the beta per tesnor is the binary, then doesnt that mean that were just forcing the model to use LUTs over DSP instead of having a sustainable new strcutre

---

## Claude · 18:15

Mostly yes, and it is worth saying plainly.

**For 72% of the design, it is literally a directive.** The 4,133 DSPs at C-synthesis all belong to the β affines and the softmax. Shedding them cost 1.2 million csynth LUT through `config_op mul -impl fabric`. That is a resource swap, not a structure. The record already calls the scoped variant "a resource swap", and the same word applies to the solution-wide one. Vivado does not even honour the swap unless the binding covers everything.

**For the 28% that is the binary matmuls, it is structural, but not new.** No multiplier exists there, so no directive is needed: a ±1 weight turns a MAC into a conditional add or subtract. That is the same primitive Vitis reaches on its own for any weight with two or three signed digits. We measured this: the W8A8 article's weight layers drew 872 DSPs for 17,664 multiplies, because HGQ2's converged 5-bit grid is mostly strength-reducible. HGQ's pruned 0-bit and 1-bit weights sit at the same end of that continuum. Binary is the extreme point of a spectrum every low-precision flow already lives on, not a different category.

**The famous BNN structure is not in our model.** XNOR and popcount replace arithmetic only when both operands are binary. Ours is binary times 8-bit, which is an adder tree, the same hardware as any narrow constant multiply. So the "new structure" argument of the binary-network literature does not transfer to a binary-weight-only design.

**And we removed the structure BitNet had.** BitNet's SubLN absorbs β and its per-token activation scaling is dynamic. We went norm-free to make the export bit-exact, and that is what manufactured the 15 affines. The model as built is a vanilla transformer with a per-tensor scalar constraint on its weights, plus a repair stage for that scalar.

**What a sustainable structure would look like.** Three candidates, none measured:

- **A scale-free binary transformer.** ReLU is homogeneous, so the FFN's β folds into the residual scale. The Q and K β already fold into the softmax table. If every branch entering a residual stream is constrained so its β product equals one fixed power of two of that stream, β never materializes anywhere except once at the logits, exactly as Sloot's MLP fold. That is a training-time constraint, and it deletes the 26% family by construction rather than by directive.
- **Binary activations somewhere.** That is the only route to XNOR and popcount logic. A4 already cost 1.8 AUC points, so A1 on the whole stream is not credible. Binarizing one internal site, such as the attention scores, is the experiment that would test it.
- **LUT-native packing.** Binary weight rows against 4-bit activations are exactly what fits a 6-input LUT. That is where the HGQ-LUT and Alkaid line becomes relevant to us rather than a competitor.

If none of those is pursued, the honest description of the current work is a controlled measurement of what binary weights buy a transformer at the netlist stage, with the answer being "the multipliers, and nothing else". That is a real result. It is not a new architecture, and the writing should stop suggesting it is.

---

## You · 18:17

okay, i want ot restart thigns over, and so can u just create a separte folder, with everything duplicated, but then edit so that i am able to naviagte the theory and the code, and the structure directly, and have a certain system that allows me ot input the bash commands and controlling nrps easily

---

## Claude · 18:17

I'll start by measuring what "everything" is (sizes, ignored dirs) and reading the existing NRP and mulder playbooks so the command system reuses their exact procedures, then check the plan with the advisor before building.

Plan confirmed. Building now: cloning into a sibling folder, overlaying the working tree, symlinking the heavy directories, then the navigation layer and the `bn` command system.

Almost done. Fixing the one broken example (the model builder returns a tuple), then a final review.

The restart tree is built and verified. Nothing in the original folder changed, and nothing was committed, launched, or shipped.

**Where it is and how it was made.** `~/Downloads/bnjettag-restart`, a sibling of the original. It is a git clone of the original (history kept, objects hardlinked) with the uncommitted working tree copied on top, so it carries the same 28 modified and untracked entries the original had this afternoon. The heavy ignored directories are symlinks back to the original: the two venvs, `data`, `reference-code`, and the bulk of `_attic`. The Claude auto-memory folder was copied to the new project key, so the standing grants and preferences carry over. The tree is about 5 GB on disk.

**What is new in it.**

- `START-HERE.md` is the tree with three entrances: theory, code, operations. Every node is one line and a link.
- `theory/` holds five short notes: the thesis and its honest state, what is actually binary in the model, how weights become adders and DSPs become zero, the two AUCs and the provenance rule, and the open questions with the eight arms. They link to the record and the code anchors rather than restating numbers.
- `CODE-MAP.md` is the pipeline as one call chain from config JSON to the tables of record, with file and line anchors.
- `bn` is the command system. `./bn help` lists it. Subcommands cover the cluster, the synthesis box, the ROC numbers gate, the memory logs, and a shell with the venv and `k` on the path and the paste gotcha fixed. Deletes refuse anything not named `kai-`. The W&B key is checked but never printed.
- `ops/COMMANDS.md` is the copy-paste sheet with every `bn` command beside the raw command it runs.
- `CLAUDE.md` and `README.md` carry a provenance stamp, and the new tree's decisions log records the restart.

**What was proven for real.** `./bn doctor` passes 11 of 11: key, venv through the symlink, all symlinks resolving, kubectl auth on the cluster, ssh to mulder, and the synthesis script present there. `status`, `nrp jobs`, `mulder status`, `roc list`, `roc verify`, `log`, and `shell` all ran. The n8 arrays recompute to the values in the record. The launch, delete, ConfigMap, preflight, ship, synth, and fetch subcommands are transcriptions of the scripts of record but have not been run yet. The commands sheet says so explicitly.

**Two things to know.**

- The venv's `activate` script still exports the original tree's path. Use `.venv-hgq2/bin/python` from the new tree, or `./bn shell`, and it resolves correctly.
- The root debris came along under "everything duplicated": `ByMaurizio.png`, `bitnet-arch.png`, `practice.py`, `solutions.md`, `notes-2026-08-13.md`, `STATUS-2026-08-08.md`, the two `Untitled.*` files, and `files (2)/`. Your call what to keep.

**First two actions in the new folder:** open `START-HERE.md`, then run `./bn doctor`.

---

## You · 11:45

wait so whats our trianing parameters

---

## Claude · 11:45

From the config of record, `bnjettag/code/hgq2/configs/r14-l1x3-n8-w1a8.json` (the other arms differ only in `n_part`, `quant.weight`, and `act_bits`):

**Architecture** (`arch`)

| knob | value |
| --- | --- |
| input | top-N constituents by p_T × 3 features (p_T, η_rel, φ_rel), N ∈ {8, 16, 32, 64} |
| d_model / heads / layers / FFN | 32 / 4 / 2 / 64 |
| norm | none (norm-free), input standardization on |
| positional encoding | learned |
| pooling / classes | mean over particles / 5 |
| parameters | 18,657 at N = 8 (built on CPU just now) |

**Quantization** (`quant`)

| knob | value |
| --- | --- |
| weights | `binary_absmean` for W1 arms; `int8_absmax` for W8A8; `none` for FP32 |
| activations | 8, 6, or 4 bits, static per-tensor, MSE-calibrated on 8,192 jets |
| calibration | `trainable` scale on a fixed-width grid |
| EBOPs pressure `beta0` | 0 in every Round-14 config (HGQ's resource loss never on) |

**Optimizer and schedule** (`train`)

| knob | value |
| --- | --- |
| optimizer | Adam, β₂ = 0.98, weight decay 0.01 |
| peak learning rate | 2e-5 |
| schedule | 1 warmup epoch, then linear decay over 100 epochs (power 1.0) |
| epochs / batch | 101 / 256 |
| gradient clipping | by value, 1.0 |
| early stopping | patience 15 on validation macro-OvR AUC |
| validation split | 20 % of the training set |
| seeds | 3 per arm |

**Compute**

| knob | value |
| --- | --- |
| where | NRP Nautilus, namespace `cms-ml`, one Kubernetes Job per arm and seed, `kai-bn14-*.yaml` |
| resources per job | 1 GPU (lands on A100 / L40S / 4090 / A40), 2 CPU, 8 Gi RAM, 16 Gi ephemeral, 6 h deadline |
| data | fetched from Zenodo inside each pod; artifacts to W&B project `BNJetTagAug` |

Everything is set in the JSON and its generator, never in code or environment variables. Two things worth knowing before a restart: the 2e-5 learning rate came from the pre-Round-14 recipe carried forward verbatim, and the binary arms at N ≥ 32 peak mid-training and degrade afterwards, so the schedule itself is one of the unexamined knobs.

---

## You · 11:45

why is my LUT so high

---

## Claude · 11:46

Because the design instantiates every operation of a dense transformer in fabric, and only a quarter of those operations are the cheap binary ones.

**The count.** At N = 8 the model performs 133,024 binary-weight MACs plus 8,192 activation-times-activation MACs per jet, and `io_parallel` unrolls all of them in space. A ±1 weight has no zero state, so each of the 133,024 costs a full adder of activation width. That alone is about 8 to 12 csynth LUT per MAC, which is the price of an 8-bit adder tree, not a defect.

**Where the fitting build's C-synthesis LUTs sit** (attribution of the stored report):

| family | share |
| --- | --- |
| binary matmuls (13 layers) | 28 % |
| β-restore affines (15 constant multiplies, forced into fabric) | 26 % |
| attention QKᵀ and attn·V (real 8×8 and 8×4 multipliers) | 14 % |
| Vitis dataflow glue (FIFOs, interconnect) | 18 % |
| ReLU parser artefact, softmax, adds, pooling | 14 % |

So deleting the binary matmuls entirely would still leave 72 % of the design. The count is high for three reasons, in order:

1. **It is a transformer, not an MLP.** Attention products scale as N² and cannot be binarized, and a norm-free transformer has nowhere to absorb β, so each of the 15 β constants is restored in-stream. Sloot's MLP folds β to one scalar at the logits for free. That overhead is structural to our graph.
2. **Nothing is pruned.** HGQ reaches a tenth of the LUTs because its per-weight bitwidths converge mostly to 0 bits. Binary forbids that by construction. Every weight is an adder, forever.
3. **The MAC count itself.** Against the FastML benchmark MLP we are 34× larger in operations, at a comparable per-MAC cost.

The Vivado netlist is about 0.44 of the csynth number, which is how 3.8 M csynth becomes 1.69 M real LUTs and 97.8 % of the VU13P. Every conversion-level lever has been measured and closed. What remains is training-side: a zero state in the weights, β as powers of two, narrower activations once β no longer needs restoring, or a smaller model. The full breakdown with counts is `docs/reports/research-reset-2026-09-05.md` §2.

---

## You · 11:46

does dorians research say that his lut count for the bianry model is also in the order of millions

---

## Claude · 11:47

No. Dorian Sloot's binary model is in the tens of thousands, not millions. From his Table 1 (C-synthesis estimates, VU13P, 5 ns, II = 1, three seeds), as recorded in our note `docs/literature/hls4ml-fpga-triggers/fastml2026_sloot_bitnet_survive_synthesis.md`:

| model | LUT | DSP | AUC |
| --- | --- | --- | --- |
| BitNet binary | 87.3 k | 0 | 0.9178 |
| BitNet-1.58 ternary | 80.7 k | 0 | 0.9254 |
| HGQ | 8.0 k | 0 | 0.9276 |
| Dense MLP (unquantized) | 182.9 k | 3,651 | 0.9350 |

The gap to our 3.8 M csynth is about 40×, and it is almost entirely size and structure, not efficiency:

- **His network is a 64-32-32 MLP on 16 engineered features: 4,096 MACs.** Ours is a transformer on constituents with 141,216 MACs. That is 34× in operation count before anything else.
- **Per MAC he is not cheaper.** His 87.3 k over 4,096 MACs is about 21 csynth LUT per MAC, whole model. Ours is about 27 whole-model, and 8 to 12 on the binary matmul family alone. The difference is our non-matmul half.
- **His β overhead is nearly free; ours is a quarter of the design.** A ReLU MLP is homogeneous, so his code folds every β into one scalar at the logits and pays only in accumulator width, roughly 28 to 40 bits. Our graph has residual adds and a softmax and no norm, so β is restored in-stream 15 times.
- **He has no attention.** Our activation-times-activation einsums are 14 % of the LUTs and scale as N².

Two things his numbers do say that bear on us. His binary is *not* the cheap point even in his regime: ternary beats it on LUT, AUC, and latency because a zero weight instantiates nothing, and HGQ beats both by a factor of ten by pruning. And his numbers stop at C-synthesis, one stage above where our fit question is decided.

Never put his table next to ours in a document. Different task (binary q/g vs W/Z/t), different inputs, different model class, different stage.

---

## You · 11:47

why is my LUT so high then

---

## Claude · 11:48

Because you built a model 34 times bigger than his and put it through the same kind of hardware. That is the whole answer in one line, and the arithmetic shows it:

```
Sloot binary MLP:   4,096 MACs  ×  ~21 LUT/MAC  =    87 k csynth LUT
Our n8 transformer: 141,216 MACs ×  ~27 LUT/MAC  = 3,837 k csynth LUT
```

Scale his number by our operation count alone and you already get 3.0 million. The remaining 25 % is the transformer overhead an MLP does not have: β restored in-stream 15 times, real multipliers in attention, dataflow glue.

So the LUT count is not a bug in the flow, not a bad hls4ml setting, and not binary failing to deliver. It is a dense network with 133,024 binary weights, each of which is a full adder in fabric because ±1 has no zero, fully unrolled at II = 1 or 48. The only ways it comes down are to have fewer operations (prune to a zero state, or a smaller model), make each cheaper (narrower activations), or stop paying for β (fold it or make it a shift). Every lever inside the conversion has been tried and measured closed.

The uncomfortable corollary is that "LUT in the millions" is what any 133k-MAC unrolled network costs, binary or not. Binary bought the DSPs. It did not buy the LUTs, and nothing about ±1 ever could.

---

## You · 11:50

so we dindt use an mlp

---

## Claude · 11:50

Correct. We never trained an MLP. The only architecture in Round 14 is a transformer encoder: input projection, two blocks of 4-head self-attention plus a 64-wide feed-forward, mean pooling, and a 5-class head. Every arm, from FP32 to W1A4, is that same graph with different quantizers.

That was a choice, and it is where the two research lines split:

- **Sloot, HGQ-LUT, and the whole LUT-native literature** work on 16 engineered high-level features with small MLPs, a few thousand operations. That is the regime where an 8-bit model already fits and the question is how cheap you can get.
- **We** chose constituent-level inputs, the three features the Level-1 trigger will actually have per particle, and a transformer to combine them. That is what Odagiu's paper and the sub-microsecond transformer paper do. Its justification is accuracy at trigger-native inputs, and the price is 30 times the operations before quantization touches anything.

Both choices are defensible. What is not defensible is comparing across them, which is why the notes say never to tabulate his numbers beside ours.

There is one thing the MLP question does expose. The thesis claim was about the *weights*, but the LUT count is driven by the *architecture*, and we have no measurement of what a binary MLP on the same inputs would cost, or what our transformer buys over it in AUC. That is a missing control: a small MLP on flattened (N, 3) inputs, same recipe, same flow. It would be the cheapest experiment in the whole menu and it answers the question you are circling, which is whether the transformer earns its million LUTs. If it does not, the restart is a different network, not a different quantizer.

---

## You · 11:52

do we use mlp

---

## Claude · 11:52

Two answers, depending on what you mean by MLP.

**As the architecture: no.** The model is a transformer. There is no standalone MLP arm anywhere in Round 14.

**As building blocks inside the transformer: yes, and they are most of the weights.** Each block has a feed-forward sublayer, which is a two-layer MLP (32 to 64 to 32 with ReLU), and the classifier head is another small MLP. Counting the binary MACs at N = 8:

| part | MACs | share |
| --- | --- | --- |
| feed-forward MLPs (fc1, fc2, both blocks) | 65,536 | 49 % |
| attention projections (Wq, Wk, Wv, Wo, both blocks) | 65,536 | 49 % |
| input projection and head | 1,952 | 2 % |

So half the binary matmul cost is literally MLP layers, and the other half is the linear projections attention needs. What makes it a transformer rather than an MLP is the part in between: the QKᵀ and attention-times-V products, which are activation-times-activation and cannot be binarized, plus the softmax. Those are the 14 % of LUTs that scale as N² and the reason β cannot fold away.

If the question behind this is "could we have just used an MLP", the honest answer is that nobody has checked. A binary MLP on the flattened (N, 3) input with the same recipe and the same flow is the missing control, and it is the cheapest experiment on the table.

---

## You · 11:53

why the MACs not reduced even tho im using mlps

---

## Claude · 11:53

Because a MAC count is not a weight count. It is weights times the number of times each weight is used per jet, and in a transformer every layer runs once **per particle**.

The model has only 18,657 parameters. Here is how that becomes 141,216 MACs at N = 8:

| layer | weights | applied to | MACs |
| --- | --- | --- | --- |
| fc1 (32→64) + fc2 (64→32), one block | 4,096 | each of 8 tokens | 32,768 |
| Wq, Wk, Wv, Wo (4 × 32×32), one block | 4,096 | each of 8 tokens | 32,768 |
| × 2 blocks | | | 131,072 |
| input projection + head | ≈1,952 | | 1,952 |
| QKᵀ and attn·V (no weights at all) | 0 | 8×8 pairs × 4 heads × 2 products × 2 blocks | 8,192 |
| **total** | **18,657** | | **141,216** |

The feed-forward MLP inside a block has 4,096 weights, the same as Sloot's entire network, but it runs eight times per jet, once per constituent, and at N = 64 it would run 64 times. Weight sharing across tokens is what makes transformers small in parameters and large in operations. It is the opposite trade from a flat MLP, where every weight is applied exactly once and the MAC count equals the weight count.

Hardware then makes this concrete. With `io_parallel` at RF = 1 the eight per-token copies are eight separate adder trees in fabric. The folded points reuse one copy in time (that is the II = 48), which shrank the matmul modules by 35 %, but the dataflow buffering needed to do it ate the saving. So there is no free way to reclaim the sharing on the chip.

That is the real reason a "small" 18k-parameter model costs millions of LUTs, and it is also why an MLP on the flattened (N × 3) input is the interesting control: it would have more weights than our transformer but far fewer operations, because each weight fires once.

---

## You · 11:56

can u print out the model summary

---

## Claude · 11:58

Model `r14-l1x3-n8-w1a8`, built from the config of record (train-time QAT graph, N = 8). Shapes omit the batch dimension.

| layer | type | output | params |
| --- | --- | --- | ---: |
| input_1 | Input | (8, 3) | 0 |
| input_proj | BitQEinsumDense | (8, 32) | 360 |
| pos_enc | AddPositional | (8, 32) | 256 |
| **block 0** | | | |
| attn_Wq / Wk / Wv | BitQEinsumDense ×3 | (8, 4, 8) | 1,032 each |
| attn_scores | QEinsum (QKᵀ) | (4, 8, 8) | 8 |
| attn_softmax | QSoftmax | (4, 8, 8) | 18 |
| attn_ctx | QEinsum (attn·V) | (8, 4, 8) | 8 |
| attn_Wo | BitQEinsumDense | (8, 32) | 1,064 |
| add_attn | Add (residual) | (8, 32) | 0 |
| ffn_fc1 | BitQEinsumDense | (8, 64) | 2,120 |
| ffn_act | ReLU | (8, 64) | 0 |
| ffn_fc2 | BitQEinsumDense | (8, 32) | 2,088 |
| add_ffn | Add (residual) | (8, 32) | 0 |
| **block 1** | identical to block 0 | | 9,512 |
| gap | QGlobalAveragePooling1D | (32,) | 0 |
| head_fc1 | BitQDense | (32,) | 1,064 |
| head_act | ReLU | (32,) | 0 |
| head_fc2 | BitQDense | (5,) | 173 |
| **total** | | | **18,657** (18,511 trainable, 146 non-trainable) |

How to read it:

- **Every `BitQ*` layer is a binary-weight matmul.** The parameter count is slightly above the weight count because HGQ2 stores the quantizer state alongside the kernel and bias. The kernel itself is 32×32 = 1,024 for a projection, 32×64 = 2,048 for fc1.
- **The heads are inside the einsum shapes.** Wq/Wk/Wv map (8 tokens, 32) to (8 tokens, 4 heads, 8 per head); scores are (4 heads, 8, 8); ctx collapses back to (8, 4, 8) and Wo mixes the heads to (8, 32).
- **The two `QEinsum` layers have no weights** (the 8 parameters are quantizer state). They are the activation-times-activation products that cannot be binarized.
- **No normalization layer anywhere**, which is why β must be restored by affines in the export graph. This summary is the training graph; the exported hardware graph adds 15 `*_affine` layers after each `BitQ*` layer and folds `pos_enc` into the input projection's bias.
- **Per-token reuse is invisible here.** Each block's 9,512 parameters are applied 8 times per jet, which is how 18,657 parameters become 141,216 MACs.

---

## You · 12:06

is the quatioazation awrae training using hgq layers?

---

## Claude · 12:06

Yes, but with HGQ's defining mechanism switched off. Every layer in the summary is an HGQ2 layer, and the QAT runs through HGQ2's quantizers, but we froze the parts that make HGQ "high granularity".

What HGQ2 provides and we use (`bnjettag/code/hgq2/bnhgq2/qat.py`):

- **The layer library.** `QEinsumDense`, `QDense`, `QEinsum`, `QSoftmax`, `QGlobalAveragePooling1D` are HGQ2 classes. `BitQEinsumDense` and `BitQDense` are our subclasses that overwrite the forward pass with the BitNet absmean binarizer (`bitnet_binary_ste`, line 43) and keep a pinned 1-bit `kbi` weight quantizer so EBOPs and hls4ml see 1 bit.
- **The activation quantizers.** Every `datalane` input is an HGQ2 `kif` quantizer with saturation and convergent rounding, exactly the fixed-point arithmetic hls4ml will emit, so training is bit-faithful to the hardware.
- **The bit-exact export path** into hls4ml 1.3.0's HGQ2 front end.
- **EBOPs tracing** for the cost tables.

What HGQ actually is, and what we turned off:

| HGQ mechanism | default in HGQ2 | our setting |
| --- | --- | --- |
| trainable bitwidth per weight and per activation | on | `trainable=False` everywhere |
| per-element granularity | `heterogeneous_axis` unset = every element its own width | `heterogeneous_axis=()` = one width per tensor |
| EBOPs resource term in the loss | `beta0 > 0` with a scheduler | `beta0 = 0` in every Round-14 config |
| pruning to 0 bits as a side effect of the above | automatic | impossible: weights pinned at 1 bit, activations pinned at 8/6/4 |

So the training is "quantization-aware" in the sense that the forward pass sees the exact fixed-point grids the FPGA will run. It is not HGQ training: the widths are chosen by us, per tensor, once, and nothing in the loss pushes them down. This is the point in the Sloot note that says we are not "HGQ + binary", and it is arm B in the reset memo. The trainable-width activation path already exists in the code (`_free_act`, line 266, from Round 13) and only needs a config with `act_calib: "free"` and a nonzero `beta0` to switch on.

---

## You · 12:06

why would we freeze those partS?

---

## Claude · 12:06

Three reasons, and they were reasonable at the time. One of them no longer holds.

**1. The thesis fixes the weight width.** The claim is about `{−1,+1}`. If HGQ were allowed to train the weight bitwidth, it would leave binary immediately: its converged widths go to 0 bits (pruned) or to whatever the loss wants, and the result would be an HGQ network, not a binary one. Pinning weights at 1 bit is the thesis, not an oversight. What that pin also forbids is the zero state, and that is the part worth revisiting: a 1-bit budget that allows 0 is ternary, which is arm A.

**2. Controlled experiments need fixed variables.** Round 14 was designed as a sweep with one variable per axis: N on one, activation width on the other (A8, A6, A4), three seeds each. That only works if the activation width is a knob we set, not a quantity the optimizer chooses. A trained width would give every arm a different, unreproducible grid and the ladder would stop being a ladder. Per-tensor rather than per-element for the same reason: one number per site, readable in a config, verifiable in the emitted firmware.

**3. The pipeline was ported, not designed for HGQ.** The HGQ2 stack was built in July as a bit-exact port of the earlier QKeras model, with static per-tensor grids because that is what QKeras had and what the export gates could verify. The recipe carried into Round 14 "verbatim" so that the only change was the input set. Per-element widths and EBOPs pressure were built later, in Round 13, as an experiment, and Round 14 deliberately did not inherit them.

**What no longer holds.** Reason 1 only justifies freezing the *weights*. Nothing in the thesis requires the activations to be frozen, and the reset memo's own attribution says the activation width sets the cost of the adders and the attention multipliers, about 40 % of the design together. Freezing them was a control decision for Round 14, and the price is that we have never measured the one thing Sloot's paper and HGQ-LUT make the obvious question: binary weights with HGQ-trained activation widths. That is arm B, and the code for it is already there.

---

## You · 12:08

am i using qmultihead attetniton

---

## Claude · 12:08

No. The attention is hand-composed from HGQ2 primitives, not the `QMultiHeadAttention` layer. You can see it in the summary: `attn_Wq`, `attn_Wk`, `attn_Wv` and `attn_Wo` are four separate `BitQEinsumDense` layers with the head axis written into the einsum equation, `attn_scores` and `attn_ctx` are two `QEinsum` layers, and `attn_softmax` is a `QSoftmax`.

Why, from the docstring at the top of `bnjettag/code/hgq2/bnhgq2/build.py`:

- **The projections must be binary.** `QMultiHeadAttention` owns its own Q/K/V/O kernels with stock HGQ2 quantizers. Our binarizer lives in the `BitQEinsumDense` subclass, so the projections have to be our layers.
- **β and the norm placement.** The earlier normed variant put the SubLN inside the output projection, which the stock layer cannot express, and the current norm-free variant needs a β-restore affine after each of the four projections at export. Only the decomposed form gives a place to put them.
- **It is the same hardware either way.** hls4ml's `QMultiHeadAttention` handler decomposes the layer into exactly these primitives, einsum-dense for the projections, einsum for the two products, softmax with the 1/√d folded into the exp table, so the firmware is what the stock layer would have produced, minus the parts we needed to change.

Two consequences worth knowing. The `1/√d_head` scale and the Q and K β values are folded into the softmax's input scale, which is why those two β do not cost affines. And because the block is our own composition, the 2026-08-15 finding that the softmax output width was pinned at 10 bits regardless of `act_bits` was ours to fix, which is what the 4-bit softmax-grid arm did.

---

## You · 12:08

what about qmultiattentionT

---

## Claude · 12:09

Not in anything we run, and not in the HGQ2 version we have installed.

What the installed `hgq2 0.1.9` ships under `hgq/layers/attn/`:

| class | what it is | used by us |
| --- | --- | --- |
| `QMultiHeadAttention` | standard MHA with table-lookup softmax | no |
| `QLinformerAttention` | MHA with the key/value sequence projected down to a fixed length | no |
| `QSALTAttention` | Spatially Aware Linear Transformer attention (arXiv:2510.23641), a conv2d on the attention mask | no |

There is no class with a `T` suffix in that release. The name `QLinformerAttentionT` shows up in our research log from the upstream `HGQ2-examples` code read on 2026-08-15, which tracks a newer HGQ2 than we pin. In that lineage the `T` variants are the token-transposed forms: the sequence axis is projected rather than the feature axis, which is what makes Linformer's cost linear in N. Chang Sun's FastML tutorial lists "MHA, Linformer (table-lookup softmax, or flash attention / online softmax variant)" as current coverage. The only place any of these names touch our tree is `bnhgq2/compat.py`, a shim that repairs the hls4ml handler registration for `QMultiHeadAttention` and `QLinformerAttention` so conversion does not fail on import paths. It does not instantiate them.

Whether one of them matters for the restart: Linformer is the one to look at. Our attention products are the part that scales as N² and cannot be binarized, and the binary arms destabilize at N ≥ 32. A Linformer-style projection would cap that cost at a fixed k, and the sub-microsecond transformer paper we cite has Linformer arms. It would need our binarizer subclassed onto it, the same way `BitQEinsumDense` wraps `QEinsumDense`, and it would need a check that hls4ml 1.3.0 actually converts it on the Vitis backend before any training is spent.
