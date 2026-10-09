# Poster speech — one continuous script

Personal preparation notes; **not part of the scientific record.** Companion to the A0 portrait
poster (`BNJetTag-FastML-poster-A0-portrait.pptx`, built by
`bnjettag/code/plots/build_poster_portrait.py`). Every number below is the number printed on the
poster, and every number on the poster traces to `RESEARCH.md` §5/§6/§7 or
`results/r14/hls_r14_fit.md`.

Read straight through: about **seven minutes** at a normal pace. For the two-minute version, read
only the paragraphs marked **[short]**. Stage directions in brackets are not spoken.

---

## Opening — who and why *[short]*

Hi, I'm Kai — this is work with Russell Marroquin, Javier Duarte and Daniel Diaz at UC San Diego,
and Chang Sun at Caltech.

The LHC collides protons forty million times a second, and almost none of it is interesting. The
Level-1 trigger is the first cut. It runs in FPGAs, it has to decide on every single collision
within a few microseconds, and it throws away 99.75% of events before software ever sees them. So
anything you want to run there has to be accurate enough to keep the signal, small enough to share
a chip with the rest of the trigger, and fast enough to keep up with 40 megahertz.

What we built is a transformer jet tagger whose weights are all ±1 — one bit each. The question
this poster answers is what that buys you on the FPGA, and what it costs you in tagging
efficiency.

## Why ±1 *[short]*

[Point at the BitLinear figure, top left.]

The idea is here. This is a BitLinear layer, from the BitNet paper. A normal linear layer
multiplies floating-point activations by floating-point weights. A BitLinear quantizes its input
to a fixed number of bits with a per-tensor scale γ, multiplies by weights that are only ±1, and
dequantizes by β·γ. The BitNet block is just a standard transformer block with every Linear
swapped for a BitLinear.

[Point across to "Why binary weights help", right column.]

And the reason that matters is over here. The chip we target, a Virtex UltraScale+ VU13P, has
12,288 DSP multiplier slices but 1.7 million look-up tables. A conventionally quantized 8-bit
network spends a DSP on nearly every multiply, and DSPs are the resource you run out of first.
When the weight is ±1, the multiply is a sign flip — an add or a subtract — so the whole matrix
multiply becomes an adder tree in logic. It isn't just cheaper: it moves onto a completely
different, far more abundant resource, and it leaves the DSPs free for everything else in the
trigger.

One thing to be clear about: the weights are binary from the first epoch. This is
quantization-aware training with a straight-through estimator, not post-training quantization.

## What we trained it on

Public HLS4ML jet dataset — five balanced classes: gluon, light quark, W, Z and top. 880,000
simulated jets; 620,000 for training, and a completely separate 260,000-jet held-out set that
never touches training or model selection. Every number on this poster is measured on that set.

The important constraint is the input. We give the network only what a Level-1 trigger actually
has: the N highest-pT constituents, with three features each — pT, and the position relative to
the jet axis, eta-rel and phi-rel. Nothing else.

The model itself is small. Two encoder layers, model width 32, four heads, feed-forward width 64,
no normalization layers, learned positional encoding, mean pooling, five-class head. Every weight
in it is binary — 17,664 of them. Activations are 8, 6 or 4 bits, with the ranges learned during
training. The baselines are the identical network in FP32, and in conventional 8-bit, W8A8.

## What binarization costs *[short]*

[Point at the AUC table.]

So what does it cost. We measured it rather than assumed it, and there are four things to say.

First, the three trigger-level features are enough for the task at all: FP32 reaches 0.913 macro
AUC at N = 16, and 0.949 at N = 64.

Second, binary stays close at short sequences. At N = 16 it gives up 0.017 AUC against full
precision — 0.8956 against 0.9128 — and that gap sits well outside both the seed spread and the
bootstrap uncertainty. It's a real difference, not noise.

Third, and this is the one that surprised us: halving the activation width from 8 bits to 4 costs
0.018 to 0.026 AUC — at least as much as binarizing all the weights did. The activations turn out
to be at least as expensive as the weights, which is not what you would guess.

Fourth, binary training becomes unstable at long sequences. At N = 32 and 64 the seed-to-seed
variance is about 76 times what it is at N = 8 and 16, and the weaker runs actually peak
mid-training, around epoch 40 to 57, and then degrade. That's why the N = 64 entry carries a
dagger — it's a seed range, 0.903 to 0.925, not a stable mean.

[Point at the per-class table.]

And the cost isn't spread evenly. Per class, at N = 16, gluon jets lose the most — 0.025 — and top
jets the least, 0.010. Binarization hurts most where the classes were already hardest to separate.

## What it buys in silicon *[short]*

[Point at the zero-DSP table.]

Now the hardware, which is really the point of the poster.

The flow is quantization-aware training in Keras with HGQ2; hls4ml converts the trained network,
with its trained bit-widths, to C++; Vitis HLS emits Verilog; Vivado synthesizes it. Two checks
guard every number downstream: the exported network reproduces the trained scores to a correlation
of at least 0.997 — 0.9988 at N = 8 — and hls4ml's own C++ test bench matches it bit-for-bit.

Here is the headline. This is the complete network at N = 8, not a layer. Fully parallel, it's 164
cycles, initiation interval 1 — one jet per clock cycle — and 4,133 DSPs. But look at where those
DSPs are: not one of them is in a binary layer. Every binary matrix multiply, and all four
attention products, are already at zero DSPs. The 4,133 sit in the beta rescaling stages — 3,621
of them — and the softmax, 512.

Direct the tool to build those multipliers out of LUTs instead of DSP slices and you get 146
cycles, initiation interval still 1, and zero DSPs. The whole model. And that's confirmed by
Vivado on the synthesized netlist, not just an HLS estimate.

One detail worth knowing if you try this: the directive has to be global. Restrict it to the two
DSP-carrying stages and Vivado turns around and re-infers 4,096 DSPs for the attention products.

## Where it actually stands *[short]*

[Point at the resources table.]

So zero DSPs is settled. Fit is not, and I want to be precise about that.

Every LUT count here comes from out-of-context synthesis targeting a smaller part — a ZU7EV —
before place-and-route, compared against the VU13P's nominal 1,728,000 LUTs. It is a cross-part
comparison, not a demonstrated fit.

At the precisions learned in training, the zero-DSP designs exceed that count: 122% fully
parallel, 113% time-multiplexed. Narrowing the attention softmax grid to 4 bits and retraining
brings it to 98%. And at the 2.5-nanosecond clock we target, every zero-DSP design fails timing.
At 5 nanoseconds the retrained 4-bit model uses 1,583,565 LUTs — 91.6% of nominal — zero DSPs, and
+0.65 nanoseconds of pre-route slack, and it scores 0.8701 AUC. But it accepts one jet every 240
nanoseconds with 1.7 microseconds of latency, so it is not Level-1 deployable yet.

For scale, we've now measured the conventional 8-bit version of the same network through the same
flow: 2,525,842 LUTs and 5,550 DSPs. More logic than the binary design, and thousands of DSPs on
top of it.

## Close *[short]*

To summarize: a 1-bit transformer jet tagger synthesizes entirely onto FPGA logic — zero DSPs for
the complete N = 8 model — at an accuracy cost of 0.015 AUC against full precision. The retrained
4-bit-softmax version reaches 0.8701 AUC and an out-of-context count below the nominal VU13P LUT
total.

What's left is real work. Place and route on the actual VU13P and close timing there. Get the
latency and the initiation interval down from 1.7 microseconds and one jet per 240 nanoseconds.
Integrate the trigger I/O, build a bitstream, test it on a board. And synthesize the longer
sequences and the FP32 baseline so the comparison is complete.

Happy to go deeper on any part of it.
