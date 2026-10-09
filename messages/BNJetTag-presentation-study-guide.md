# BNJetTag Presentation Study Guide

Companion to `BNJetTag-FastML-poster-A0-portrait-readable.pptx`.

This is a learning guide, not the scientific record. When a number matters, the sources of record are `RESEARCH.md`, `bnjettag/results/r14/hls_r14_fit.md`, and the verified result tables named at the end.

## How to use this guide

Study in three passes:

1. Read **The story in plain English** until you can explain the project without jargon.
2. Learn **The poster, section by section** and the **numbers to know cold**.
3. Answer the **practice questions** aloud without looking. If an answer takes more than about 30 seconds, simplify it.

Do not try to memorize every table cell. Memorize the argument, the headline numbers, and the limits of the claim.

---

## The story in one sentence

We built a small transformer jet tagger with binary `{−1,+1}` weights, measured the accuracy it gives up, showed that its weight multiplications can be implemented with zero FPGA DSP slices, and found a retrained 4-bit-softmax version that falls below the nominal VU13P LUT count in pre-route cross-part synthesis—although it is not yet a deployable Level-1 trigger.

## The story in plain English

The Large Hadron Collider produces far more collision data than can be permanently stored. The first filtering stage, the Level-1 trigger, therefore has to make extremely fast decisions in FPGA hardware.

Neural networks can help decide whether a particle jet looks like a gluon, light quark, W boson, Z boson, or top quark. The problem is that ordinary neural networks rely on many multiplications. On an FPGA, these often consume specialized multiplier blocks called DSPs, which are limited and must be shared with the rest of the trigger.

This project asks whether a transformer can use binary weights—only `−1` or `+1`—so that multiplication by a weight becomes a sign choice and an add or subtract. That moves the binary matrix multiplications into general LUT logic and can leave the DSP blocks free.

The tradeoff is not free. Compared with the full-precision model, the binary model loses about 0.015–0.017 macro AUC for short input sequences and 0.032–0.036 for longer ones. It also becomes unstable across training seeds at larger constituent counts.

On hardware, zero DSP demand was achieved and verified at Vivado synthesis. The first zero-DSP designs were still too large in LUTs. The important hardware lever was reducing the attention softmax output from a 10-bit grid to 4 bits. After retraining with that grid, the model retained its accuracy within a preset tolerance and synthesized below the nominal VU13P LUT count. The remaining problems are actual target-part place-and-route, throughput, timing closure after routing, integration, and board validation.

---

## A 60-second explanation

> “The Level-1 trigger at the LHC has to filter collisions in fixed-latency FPGA logic. We built a small transformer jet tagger in which every learned linear weight is either minus one or plus one. That matters because multiplying by a binary weight can become add/subtract logic in LUTs instead of using scarce DSP multiplier slices. On a held-out set of 260,000 jets, the binary model loses 0.017 macro AUC versus FP32 at 16 constituents. We then converted the model through hls4ml, Vitis HLS, and Vivado. The binary core uses no DSPs, and with explicit fabric binding the whole model can reach zero DSP demand. The first trained-grid zero-DSP designs exceeded the nominal VU13P LUT budget. A retrained 4-bit-softmax version retained accuracy at 0.8701 plus or minus 0.0020 and synthesized below the nominal LUT count. But this is still an out-of-context, pre-route result on a different part; the fitting design has II equals 48 and 1.67 microsecond latency at 200 MHz, so it is promising rather than deployable.”

---

## The poster, section by section

### 1. Abstract: what question is the project answering?

The project measures three things:

- The accuracy cost of using binary weights.
- Whether binary matrix multiplication really avoids DSP slices after synthesis.
- Whether the complete design is small and fast enough for trigger hardware.

The key word is **measure**. The work does not assume that fewer bit operations automatically means a smaller real FPGA design.

Short version to say:

> “We measured the accuracy, resource, and timing consequences of putting a binary-weight transformer jet tagger into FPGA firmware.”

### 2. Linear versus BitLinear

A normal linear layer computes roughly:

`output = weight matrix × input + bias`

The weights are ordinary real-valued numbers, so the operation contains many general multiplications.

A BitLinear layer keeps full-precision latent weights during training but uses their trained signs in the forward pass. Its hardware-facing weights are strictly `{−1,+1}`. It also quantizes the activations and later restores scale using factors usually described as `β` and `γ`.

- `γ` describes the activation quantization scale.
- `β` is the per-tensor weight scale, based on the absolute mean of the latent weights.
- Multiplication by `+1` keeps a value; multiplication by `−1` flips its sign.
- A dot product can therefore become an adder/subtractor tree instead of a bank of general multipliers.

This is **quantization-aware training**, not post-training quantization. During training, fake quantization makes the forward pass see the values that hardware will represent. A straight-through estimator lets gradients pass through the non-differentiable rounding operation.

Important distinction: this is binary `{−1,+1}`, not ternary `{−1,0,+1}` or BitNet b1.58.

### 3. Goals

The four goals on the poster are:

1. Map binary matrix multiplications to LUT logic instead of DSP slices.
2. Measure the efficiency loss against FP32 and W8A8 baselines.
3. Test 8-, 6-, and 4-bit activation choices.
4. Check Level-1 requirements: resource use, sub-microsecond latency, and II = 1.

Outcome:

- Goals 1–3 were measured.
- Goal 4 is not fully met. The fitting point is II = 48 with 1.67 microsecond latency at a 5 ns clock.

### 4. Dataset and evaluation

The public HLS4ML LHC jet dataset has five balanced classes:

- Gluon (`g`)
- Light quark (`q`)
- W boson
- Z boson
- Top quark (`t`)

There are 880,000 simulated jets in the splits used here:

- 620,000 in the dataset's training split.
- A 20% portion of that training split—124,000 jets—is used for validation during training.
- A separate 260,000-jet split is held out from training and model selection and is used for the reported test AUC.

Each jet contains up to 150 particle constituents. The study keeps the highest-`pT` `N` constituents, with `N ∈ {8,16,32,64}`, and uses only three Level-1-realistic features per constituent:

- `pT`: transverse momentum.
- `ηrel`: pseudorapidity relative to the jet axis.
- `φrel`: azimuthal angle relative to the jet axis.

The metric is **macro one-vs-rest ROC AUC**. For each of the five classes, the model is evaluated as “this class versus the other four”; the five AUC values are then averaged equally. AUC measures ranking quality across all thresholds. A value of 0.5 is random ranking and 1.0 is perfect ranking.

Three independent training seeds are used per configuration. The reported table values are seed means. Seed-to-seed variation is especially important for the longer binary models.

Never mix up:

- **Validation AUC:** used to monitor training and select the checkpoint.
- **Held-out ROC-test AUC:** the final value quoted on the poster.

### 5. Model and training

Architecture:

- Two transformer encoder layers.
- Model width 32.
- Four attention heads.
- Feed-forward width 64.
- Learned positional encoding.
- Mean pooling.
- Five-class output head.
- No normalization layers.
- 17,664 learned binary weights across all linear layers.

Every learned linear layer is binary, including the input projection and output head. The attention operations `QKᵀ` and `softmax × V` are not binary weight operations; they multiply activations by activations.

Training recipe:

- Quantization-aware training with HGQ2.
- Adam optimizer.
- One warm-up epoch followed by linear learning-rate decay.
- Peak learning rate `2×10⁻⁵`.
- Batch size 256.
- Up to 101 epochs.
- Early stopping with patience 15 on validation AUC.
- Three seeds per configuration.

Variant notation:

- `FP32`: full-precision weights and activations.
- `W8A8`: 8-bit weights, 8-bit activations.
- `W1A8`: 1-bit weights, 8-bit activations.
- `W1A6`: 1-bit weights, 6-bit activations.
- `W1A4`: 1-bit weights, 4-bit activations.

The later **Gamma** run is different: it keeps the W1A8 network but retrains the attention softmax output on a narrower 6-bit or 4-bit grid. Do not confuse Gamma's “4-bit softmax” with making every activation in the network 4-bit.

### 6. Validity checks

The result chain has several checks:

- Three seeds per accuracy configuration.
- Final AUC measured only on the held-out 260,000-jet set.
- Exported graph checked against the trained model.
- Export/reference score correlation at least 0.997 for the accepted main exports.
- hls4ml C-simulation checked against the exported graph.
- Resource claims checked at Vivado synthesis rather than trusted from C-synthesis alone.

Why this matters: one attempted optimization appeared to have zero DSPs at HLS but Vivado later inferred 4,096 DSPs. The workflow caught and retracted that claim. The rule is now: **a zero-DSP claim requires netlist-level Vivado confirmation**.

### 7. Tagging-efficiency results

Held-out macro one-vs-rest AUC, averaged over three seeds:

| N | FP32 | W8A8 | Binary W1A8 | W1A4 |
|---:|---:|---:|---:|---:|
| 8 | 0.8864 | 0.8862 | 0.8712 | 0.8534 |
| 16 | 0.9128 | 0.9124 | 0.8956 | 0.8693 |
| 32 | 0.9374 | 0.9358 | 0.9052 | 0.8833 |
| 64 | 0.9486 | 0.9448 | 0.9121† | 0.9073 |

`†` means the N = 64 W1A8 result has large seed variation and should be discussed as a seed range, not as a stable central result. Its seed values are approximately 0.9028, 0.9084, and 0.9251.

What the table means:

- At N = 16, W1A8 loses `0.9128 − 0.8956 = 0.0172` AUC versus FP32.
- The W1A8 deficit is 0.015–0.017 at N ≤ 16 and 0.032–0.036 at N ≥ 32.
- W8A8 is statistically indistinguishable from FP32 through N = 32 with the available seeds.
- Reducing all activations from 8 to 4 bits costs another 0.018–0.026 AUC at N ≤ 16.
- Longer sequences improve FP32 performance, but binary training becomes much less stable at N = 32–64.

Do not say “the binary gap grows at every step” as a statistically resolved claim. The broad low-N versus high-N difference is visible, but three seeds are insufficient to resolve each step separately.

At a trigger-style 1% mistag rate, the loss is also visible in signal efficiency. At N = 16, for example:

- Z: FP32 0.480 → W1A8 0.390.
- Top: FP32 0.469 → W1A8 0.365.

This is often easier to interpret than AUC: for those classes, binarization costs roughly 9–10 percentage points of signal efficiency at that working point.

### 8. Which jet classes lose the most?

Per-class one-vs-rest AUC at N = 16:

| Model | Gluon | Quark | W | Z | Top |
|---|---:|---:|---:|---:|---:|
| FP32 | 0.8784 | 0.8930 | 0.9358 | 0.9202 | 0.9364 |
| Binary W1A8 | 0.8531 | 0.8793 | 0.9179 | 0.9015 | 0.9263 |

At N = 16:

- Gluon loses the most: about 0.025 AUC.
- Top loses the least: about 0.010 AUC.

At N = 32–64, W and Z suffer larger deficits and carry much of the seed instability.

### 9. The Level-1 trigger

Proton bunches cross every 25 ns, or 40 million times per second. Level-1 is the first hardware trigger stage. It must make decisions with fixed and predictable latency, using FPGAs, while reducing the event rate before software processing.

Two timing terms are essential:

- **Latency:** time from one input entering the design until its output appears.
- **Initiation interval (II):** number of clock cycles before the next input can enter.

These are not the same. A deeply pipelined design can have long latency but II = 1. At a 5 ns clock:

- II = 1 means a new input every 5 ns.
- II = 48 means a new input every `48 × 5 ns = 240 ns`.
- 333-cycle latency means `333 × 5 ns = 1.665 µs`, rounded to 1.67 µs.

The 25 ns collision spacing is not the FPGA clock period. Trigger logic often uses a faster internal clock.

The poster's 99.75% rejection and 100 kHz flow are Run-2/3-style context from the trigger diagram. If asked about Phase-2, state that it is a different trigger era and do not mix the budgets.

### 10. Why binary weights help on an FPGA

The nominal VU13P resource count used for comparison is:

- 1,728,000 LUTs.
- 12,288 DSP slices.

LUTs are flexible logic elements. DSP48 slices are specialized arithmetic blocks optimized for multiplication and accumulation.

Binary weights do not make computation disappear. They change its form:

- Ordinary weight multiplication tends to need general multipliers.
- Multiplication by `±1` becomes sign control plus addition/subtraction.
- The binary weight layers therefore use LUT-based adder trees and no DSPs.

This trades DSP demand for LUT demand. “Zero DSP” is not the same as “small.” In fact, the first zero-DSP designs were too large in LUTs.

A conventional W8A8 version was later synthesized in the same cross-part flow. At Vivado post-optimization it demanded 2,525,842 LUTs, or 146.2% of the nominal VU13P count, and 5,550 DSPs. The comparable binary zero-DSP designs demand zero DSPs, though schedule and timing constraints must be stated when comparing LUT counts.

### 11. From training to firmware

The tool flow is:

`Keras + HGQ2 QAT → hls4ml C++ → Vitis HLS RTL/Verilog → Vivado synthesized netlist`

- **Keras/HGQ2:** trains the quantized network.
- **hls4ml:** converts the neural network into high-level-synthesis C++.
- **Vitis HLS:** compiles C++ into RTL hardware logic.
- **Vivado:** synthesizes and optimizes the RTL into a technology-mapped FPGA netlist.

C-synthesis estimates are useful for iteration and module attribution, but they are not final silicon resource counts. On this design they can overestimate LUTs by about a factor of two and can miss DSPs that Vivado later infers.

The reported Vivado resource results have an important caveat: synthesis was performed out of context on a ZU7EV because that was the licensed device, while percentages are calculated against the nominal VU13P resource count. Therefore “98% of VU13P” means a **cross-part nominal resource comparison**, not a successful implementation on a VU13P.

### 12. Zero-DSP implementation

Initial N = 8 operating points:

| Operating point | Latency | II | DSPs |
|---|---:|---:|---:|
| Fully parallel | 164 cycles | 1 | 4,133 |
| All multipliers bound to LUT fabric | 146 cycles | 1 | 0 |
| Time-multiplexed/folded LUT design | 329 cycles | 47 | 0 |

The 4,133 DSPs in the first row do not come from binary weight multiplication:

- 3,621 come from the `β` rescale operations.
- 512 come from softmax.

Binding multipliers to fabric removes that demand, but the binding must cover the whole solution. A narrower directive still let Vivado infer 4,096 DSPs in the attention context products. This is the main reason Vivado verification is part of the claim.

### 13. Resources, the 4-bit-softmax result, and the deployment gap

The trained-grid zero-DSP designs miss the nominal VU13P LUT count:

| Design | II | DSPs | Vivado LUTs | Nominal VU13P comparison |
|---|---:|---:|---:|---:|
| Fully parallel, trained grid | 1 | 0 | 2,108,743 | 122.0% |
| Folded/time-multiplexed, trained grid | 47 | 0 | 1,948,063 | 112.7% |

Why did folding help less than expected? It shrank some compute, but FIFOs, multiplexers, control, and other dataflow plumbing grew. In the resource attribution, that plumbing is about 24% of LUT use.

Approximate LUT attribution in the characterization design:

- Binary linear layers: 28%.
- `β` scaling: 26%.
- Dataflow plumbing: 24%.
- Attention context products: 14%.
- Requantization: 4%.
- Softmax: 2%.
- Adds and pooling: 2%.

The key lever was the attention softmax output grid. Reducing it from 10 bits to 4 bits:

- Shrinks the attention context products.
- Changes an 8-bit × 10-bit-style multiplication into an 8-bit × 4-bit multiplication that Vivado leaves in LUT logic instead of remapping to DSP48s.

#### Why the poster shows several similar LUT numbers

These are different experiments and must not be mixed:

1. **1,694,625 LUT = 98.1%:** structure-only 4-bit-softmax characterization at the 2.5 ns synthesis constraint. The 4-bit grid was forced onto a model trained for the old grid, so this row has no accuracy claim.
2. **1,689,320 LUT = 97.8%:** retrained Gamma 4-bit-softmax model at the 2.5 ns synthesis constraint. It has an accuracy claim and zero DSP demand, but it misses 2.5 ns timing before routing with WNS about −1.85 ns.
3. **1,583,565 LUT = 91.6%:** the same retrained Gamma RTL synthesized under an easier 5.0 ns constraint. It has zero DSP demand and meets pre-route timing with WNS +0.647 ns. Because timing constraints change optimization, its LUT count differs from the 2.5 ns run.

Gamma accuracy:

- Original N = 8 W1A8 control: 0.8712 ± 0.0016.
- 6-bit-softmax retraining: 0.8706 ± 0.0017.
- 4-bit-softmax retraining: 0.8701 ± 0.0020.
- Drop of the selected 4-bit arm: 0.0011 AUC.
- One-sided 95% upper bound on the drop: 0.0035, inside the pre-registered tolerance of 0.005.

At 5 ns, the selected design has:

- II = 48.
- One new jet every 240 ns.
- 333-cycle latency = 1.67 µs.
- WNS +0.647 ns before place-and-route.
- Zero failing timing endpoints at this synthesis stage.

This is the strongest result, but the correct conclusion is **promising synthesis point**, not **deployed trigger**.

### 14. Estimated compute efficiency

EBOPs means effective bit-operations. It estimates arithmetic cost from the trained bit widths without running full FPGA synthesis.

At matched N, W1A8 uses fewer estimated bit-operations than W8A8 by approximately:

- 5.28× at N = 8.
- 4.08× at N = 16.
- 2.97× at N = 32.
- 2.14× at N = 64.

EBOPs is useful for comparing trained models, but it is not a resource measurement. It omits important implementation costs such as accumulation details and `β` rescaling. Real Vivado results remain the binding evidence.

### 15. What remains before deployment

Still open:

- Synthesize, place, and route on the actual VU13P.
- Demonstrate post-route timing closure.
- Reduce II from 48 or design enough parallel/time-multiplexed copies for the required input rate.
- Reduce latency if the relevant trigger budget requires it.
- Determine the actual LUT budget available to one tagger inside the full trigger design.
- Synthesize whole models for N ≥ 16.
- Integrate trigger I/O.
- Generate a bitstream.
- Test on a physical board.
- Produce an FP32 hardware baseline if needed.

The current result does not prove that the design fits or operates on the final VU13P system.

### 16. Conclusion

The defensible conclusion is:

> “A binary N = 8 transformer can be synthesized with zero DSP demand. Retraining the attention softmax on a 4-bit grid preserves the observed AUC within the preset tolerance and brings the cross-part, pre-route LUT comparison below the nominal VU13P count. The binary mapping works; full Level-1 deployment is still open.”

---

## Numbers to know cold

| Topic | Number | Meaning |
|---|---:|---|
| Collision spacing | 25 ns / 40 MHz | Rate entering the trigger system |
| Held-out evaluation set | 260,000 jets | Never used for training or model selection |
| Classes | 5 | g, q, W, Z, top |
| Input sizes | N = 8, 16, 32, 64 | Highest-pT constituents |
| Features per constituent | 3 | pT, ηrel, φrel |
| N = 16 FP32 AUC | 0.9128 | Full-precision reference |
| N = 16 W1A8 AUC | 0.8956 | Binary result |
| N = 16 binary cost | 0.0172 AUC | Resolved FP32–W1A8 difference |
| Gamma 4-bit-softmax AUC | 0.8701 ± 0.0020 | Retrained N = 8 result |
| Gamma accuracy drop | 0.0011 | Versus N = 8 W1A8 control |
| Fully parallel zero-DSP size | 2,108,743 LUT / 122.0% | II = 1, does not fit nominal count |
| Folded trained-grid size | 1,948,063 LUT / 112.7% | II = 47, still over nominal count |
| Retrained Gamma, 2.5 ns | 1,689,320 LUT / 97.8%, 0 DSP | Under nominal count, timing not met |
| Retrained Gamma, 5 ns | 1,583,565 LUT / 91.6%, 0 DSP | Timing met pre-route |
| Gamma throughput | II = 48 = 240 ns/jet | Too slow for one input per 25 ns by itself |
| Gamma latency | 333 cycles = 1.67 µs | At 5 ns per cycle |
| Gamma timing | WNS +0.647 ns | Pre-route 5 ns synthesis constraint met |
| W8A8 netlist baseline | 2,525,842 LUT / 146.2%, 5,550 DSP demanded | Conventional 8-bit comparison |
| VU13P nominal resources | 1,728,000 LUT, 12,288 DSP | Comparison budget, not demonstrated placement |

If you forget everything else, remember: **0.017 AUC cost; zero DSPs; 97.8% nominal LUT comparison at 2.5 ns but timing fails; 91.6% at 5 ns with +0.65 ns slack; II 48 and 1.67 µs remain open.**

---

## Distinctions that prevent bad answers

### AUC versus a trigger working point

AUC summarizes ranking across every threshold. A trigger ultimately chooses a threshold and cares about signal efficiency at a fixed background mistag rate. The poster emphasizes AUC, but working-point measurements exist. Do not pretend that a 0.017 AUC change directly equals 1.7% signal-efficiency loss.

### Latency versus II

Latency is how long one item takes. II is how frequently new items may enter. A design can have a long latency but still have II = 1 if it is deeply pipelined.

### C-synthesis versus Vivado synthesis versus place-and-route

- C-synthesis: early estimate and RTL creation.
- Vivado synthesis/`opt_design`: technology-mapped pre-route netlist and the stage of the reported resource results.
- Place-and-route: physical implementation on the actual FPGA; not yet completed for the target VU13P.

### Nominal fit versus demonstrated fit

The netlist was synthesized for a ZU7EV, then its LUT count was divided by the VU13P's nominal LUT count. That is informative, but it is not proof that the design places, routes, and closes timing on a VU13P.

### W1A4 versus Gamma 4-bit softmax

- W1A4 quantizes activations throughout the network to 4 bits and has a noticeably lower AUC.
- Gamma keeps the broader W1A8 design but narrows the specific attention-softmax output grid to 4 bits and preserves AUC.

### Zero DSP versus efficient overall

The binary core removes DSP demand, but LUT adder trees, scaling, attention arithmetic, and dataflow plumbing can still make the design very large.

---

## Questions you are likely to get

### “What is the main novelty?”

The main contribution is a measured end-to-end binary-weight transformer implementation: accuracy is evaluated on a held-out jet dataset, the exported model is fidelity-checked, and zero DSP demand is verified at Vivado synthesis. The claim is about the binary mapping and its measured tradeoffs, not simply proposing another transformer.

### “Why use a transformer?”

Jets are collections of particle constituents with relationships between them, and attention can model those relationships. Small attention-based jet taggers also have relevant prior work for FPGA triggers. This project isolates the effect of binarizing the transformer's learned linear weights.

### “Why binary weights?”

Because multiplication by `±1` becomes sign selection and addition/subtraction. This lets the learned matrix multiplications use LUT logic and leaves DSP slices free for other trigger functions.

### “Is this post-training quantization?”

No. It is quantization-aware training from the start, with full-precision shadow weights for optimization and binary signs used in the forward computation.

### “Are the attention products also binary?”

No. `QKᵀ` and `softmax × V` multiply activations by activations. They contain no learned weight to binarize and became an important hardware bottleneck.

### “How much accuracy do binary weights cost?”

At N = 16, macro one-vs-rest AUC drops from 0.9128 for FP32 to 0.8956 for W1A8, a resolved loss of 0.0172. The deficit is about 0.015–0.017 for N = 8–16 and 0.032–0.036 for N = 32–64.

### “Why do you use only three input features?”

They are the Level-1-realistic constituent features used in the relevant literature: transverse momentum and angular offsets relative to the jet axis. The point is to evaluate a model on inputs that trigger hardware could realistically provide.

### “Why only three seeds?”

Three seeds are enough to resolve the main W1A8-versus-FP32 deficit at each N, but not enough to claim that every step in the gap's growth is significant. The large variance at N = 32–64 is reported explicitly rather than hidden.

### “What does zero DSP really mean?”

Vivado's synthesized netlist demands zero DSP48 blocks for the stated designs. It does not mean zero multiplication-like work; those operations are being implemented in LUT fabric.

### “Why did the first fully parallel model still use 4,133 DSPs?”

They came from 3,621 `β` scale operations and 512 softmax operations, not from binary weight matrix multiplication. Explicitly binding multipliers to fabric removed them.

### “Why wasn't HLS saying zero DSP enough?”

Because Vivado can remap plain multiplications back into DSP blocks during technology mapping. One scoped-binding build reported zero at C-synthesis but demanded 4,096 DSPs in Vivado. Netlist-level verification is therefore mandatory.

### “What made the design fit below the nominal LUT count?”

Narrowing the attention softmax output grid from 10 to 4 bits. It reduced the size of the context products and prevented Vivado from mapping those products to DSPs. The grid was then retrained so that an accuracy claim could be attached.

### “Did the 4-bit change hurt accuracy?”

The retrained Gamma 4-bit-softmax model scored 0.8701 ± 0.0020 versus 0.8712 ± 0.0016 for the N = 8 W1A8 control. The 0.0011 drop passed the pre-registered tolerance; its one-sided 95% upper bound was 0.0035, below the 0.005 limit.

### “Why are there two LUT numbers for the trained Gamma design?”

They come from separate timing-driven syntheses of the same RTL. Under the aggressive 2.5 ns constraint it uses 1,689,320 LUTs and misses timing. Under the easier 5 ns constraint it uses 1,583,565 LUTs and meets timing with +0.647 ns slack. Timing constraints change synthesis optimization.

### “Does it fit the VU13P?”

The honest answer is: its pre-route LUT count is below the VU13P's nominal count in a cross-part comparison, but it has not been placed and routed on a VU13P. So it is a promising fitting point, not a demonstrated VU13P fit.

### “Did you meet the Level-1 throughput goal?”

No. The fitting design has II = 48, or one input every 240 ns at 200 MHz, and latency of 1.67 µs. The II = 1 zero-DSP version is 122% of the nominal LUT count and fails the 2.5 ns timing constraint before routing.

### “Why not just use the available DSPs?”

That is a legitimate system tradeoff, but the purpose of the binary design is to free DSPs for the rest of the trigger. The actual amount of LUT and DSP budget available to one tagger must ultimately be decided in the full system design.

### “How does W8A8 compare on hardware?”

In the same cross-part Vivado flow, W8A8 demands 2,525,842 LUTs—146.2% of the nominal VU13P count—and 5,550 DSPs. It is not a fitting baseline. FP32 has not been synthesized.

### “What is still missing?”

Actual VU13P place-and-route, post-route timing, a throughput architecture that meets the required stream rate, N ≥ 16 whole-model synthesis, trigger I/O, bitstream generation, and board testing.

---

## Claims to avoid

Do not say:

- “The design is deployed” or “the design definitely fits the VU13P.”
- “We completed place-and-route.”
- “The model meets II = 1 and sub-microsecond latency.”
- “Binary weights make the whole design tiny.”
- “Every multiplication is binary.”
- “C-synthesis proves zero DSP use.”
- “A 0.017 AUC loss means exactly 1.7% lower signal efficiency.”
- “The binary accuracy gap increases significantly at every N step.”
- “The 4-bit structure-only row proves accuracy.”
- “W1A4 and Gamma 4-bit softmax are the same model.”

Say instead:

- “The retrained design is below the nominal VU13P LUT count in out-of-context, pre-route cross-part synthesis.”
- “Zero DSP demand is verified at Vivado synthesis.”
- “The fitting point is II = 48 with 1.67 microsecond latency at 200 MHz.”
- “The full target implementation remains open.”

---

## Glossary

**AUC:** Area under the ROC curve; measures how well scores rank positives above negatives across thresholds.

**Binary weight:** A learned weight represented as either `−1` or `+1` in the forward/hardware computation.

**Constituent:** A reconstructed particle or detector-level object belonging to a jet.

**DSP / DSP48:** A dedicated FPGA arithmetic block, especially useful for multiplication and accumulation.

**EBOPs:** Effective bit-operations; a bit-width-aware compute estimate, not a measured hardware resource.

**FPGA:** Reprogrammable digital hardware made of logic, memory, routing, and specialized arithmetic blocks.

**Held-out set:** Data not used for training, validation, checkpoint choice, or model selection.

**II:** Initiation interval; cycles between accepting consecutive inputs.

**Jet:** A collimated spray of particles produced by quarks, gluons, or boosted heavy-particle decays.

**Latency:** Cycles or time from an input entering the design to its output appearing.

**LUT:** Look-up table; the FPGA's flexible logic resource.

**Macro one-vs-rest AUC:** Compute one AUC for each class against all other classes, then average the class AUCs equally.

**Out-of-context synthesis:** Synthesizing one module without the complete board or system-level design and I/O.

**Place-and-route:** Assigning logic to physical FPGA locations and routing the connections; needed for a real implementation and post-route timing.

**Quantization-aware training:** Training while simulating low-precision values in the forward pass.

**ROC curve:** True-positive rate versus false-positive rate as the decision threshold changes.

**Straight-through estimator:** Backpropagation approximation that passes gradients through rounding/sign operations.

**WNS:** Worst negative slack. Positive slack means the timing constraint is met at that analysis stage; negative slack means it is missed.

**`β` rescale:** Per-tensor scale restoration after a binary linear operation; a constant multiply that can consume DSPs or many LUTs.

---

## Active-recall quiz

Try these without looking back.

1. What problem does the Level-1 trigger solve?
2. Why do binary weights reduce DSP demand?
3. What is the difference between W1A4 and Gamma 4-bit softmax?
4. What are the five jet classes?
5. Which three constituent features are used?
6. What does N mean?
7. What is macro one-vs-rest AUC?
8. What is the N = 16 AUC difference between FP32 and W1A8?
9. Why is the N = 64 W1A8 value marked with a dagger?
10. Where did the original 4,133 DSPs come from?
11. Why must zero DSP be verified in Vivado?
12. Why did folding reduce LUTs less than expected?
13. What did narrowing the softmax output accomplish?
14. Why are 1,689,320 and 1,583,565 both correct for the retrained Gamma design?
15. What is II, and what does II = 48 mean at a 5 ns clock?
16. What is the latency of the fitting design at 5 ns?
17. Has the design been placed and routed on a VU13P?
18. What is the strongest conclusion you can defend?

### Answer key

1. It filters the 40 MHz collision stream in fast, fixed-latency FPGA logic before software processing.
2. Multiplication by `±1` becomes sign selection and add/subtract logic in LUTs.
3. W1A4 reduces activations broadly; Gamma narrows only the attention softmax output grid while retaining W1A8 elsewhere.
4. Gluon, light quark, W, Z, and top.
5. `pT`, `ηrel`, and `φrel`.
6. The number of highest-`pT` jet constituents kept as input.
7. One ROC AUC per class versus the other four, averaged equally across five classes.
8. `0.9128 − 0.8956 = 0.0172` AUC.
9. Large seed-to-seed variation makes it better described as a range than a stable mean.
10. 3,621 from `β` rescales and 512 from softmax, not from binary weight layers.
11. Vivado can re-infer DSPs during technology mapping even when HLS estimates zero.
12. Dataflow FIFOs, multiplexers, and control offset much of the compute saving.
13. It reduced LUT cost in attention and prevented DSP inference for the context products.
14. They are separate syntheses of the same RTL under 2.5 ns and 5 ns timing constraints.
15. II is cycles between new inputs; II = 48 at 5 ns means one new input every 240 ns.
16. 333 cycles, or about 1.67 µs.
17. No. The result is out-of-context, pre-route synthesis on a ZU7EV with comparison to nominal VU13P resources.
18. Binary mapping achieves zero DSP demand; a retrained 4-bit-softmax design preserves AUC within tolerance and is below the nominal VU13P LUT count in the stated pre-route cross-part synthesis, while deployment remains open.

---

## Five-minute rehearsal structure

1. **Problem, 30 seconds:** 40 MHz collisions, Level-1 FPGA constraints, need accurate and compact tagging.
2. **Idea, 45 seconds:** binary BitLinear weights turn multiplies into add/subtract logic; explain QAT.
3. **Experiment, 45 seconds:** dataset, three features, N sweep, five precision arms, three seeds, held-out macro AUC.
4. **Accuracy, 60 seconds:** 0.017 AUC loss at N = 16; long-sequence instability; per-class effects.
5. **Hardware, 75 seconds:** hls4ml → Vitis → Vivado; zero DSP verified; first trained-grid designs too large.
6. **Gamma result, 45 seconds:** retrained 4-bit softmax, 0.8701 AUC, zero DSP, nominal LUT comparison below 100%.
7. **Honest ending, 40 seconds:** 5 ns timing clean pre-route, but II = 48 and 1.67 µs; actual VU13P place-and-route and integration remain open.

---

## Source map

- Poster: `docs/reports/BNJetTag-FastML-poster-A0-portrait-readable.pptx`
- Poster preparation notes: `docs/reports/poster-2026-08-23-speaker-notes.md`
- Research record: `RESEARCH.md`
- Hardware fit table: `bnjettag/results/r14/hls_r14_fit.md`
- Accuracy and uncertainty: `bnjettag/results/r14/export_roc_auc.md` and `bnjettag/results/r14/uncertainty_r14.md`
- Trigger working points: `bnjettag/results/r14/working_points_r14.md`
- Compute estimate: `bnjettag/results/r14/ebops_r14.json`

