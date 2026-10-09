---
title: <ide_opened_file>The user opened the file…
date: 2026-09-02
updated: "2026-09-05T12:32:43"
project: bnjettag-training-results
cwd: /Users/kaiyamaguchi/Downloads/bnjettag-training-results
model: claude-opus-5
git_branch: main
session_id: 77f654d8-d19e-427a-a385-53358cef8ee0
turns: 4
tool_calls: 21
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-training-results
---

# <ide_opened_file>The user opened the file…

> [!abstract]- Session at a glance
> **4** turns · **21** tool calls · spans **3** h **18** min · `claude-opus-5`
>
> **Tools** Bash ×17, WebFetch ×2, Skill ×1, ToolSearch ×1
> **Commands** `/explain-well`

---

## You · 12:09

<ide_opened_file>The user opened the file /Users/kaiyamaguchi/Downloads/bnjettag-training-results/bnjettag/code/hgq2/configs/r15-gamma-sm4i0-n8-w1a8.json in the IDE. This may or may not be related to the current task.</ide_opened_file>

is our resrach tehs ame thign as hg12, what chang does, and what is the differnec ei our workand our constract or are we working fo rhte samethign with the l1 trigger

---

## Claude · 12:10

I'll orient in the repo first — what we actually claim, and what we've recorded about HGQ2/Chang Sun.

Short answer: **no — same destination, different mechanism, and we run on his tooling.** You and Chang Sun's group are both building sub-µs, DSP-free jet taggers for the CMS L1 trigger through the hls4ml family of flows. The difference is *how the precision budget is spent*.

## Three things that keep getting collapsed into one

**1. HGQ2, the tool.** Chang Sun's Keras-3 QAT framework. We *train in it* — that was the decision of 2026-07-07 ([decisions.md:646](.claude/memory/decisions.md#L646)), and every Round-14 checkpoint comes out of it. Using someone's framework is not doing their research, the same way using PyTorch isn't doing Meta's research.

**2. HGQ, the method.** The actual scientific content of arXiv:2405.00645: *trainable, per-element bit widths* regularized by EBOPs. The optimizer decides that this weight wants 3 bits and that one wants 6, and a Lagrange term on EBOPs squeezes the whole layout down until it fits a resource budget. Heterogeneous mixed precision, learned.

**We have never turned that knob.** We use HGQ2's layer library with `trainable=False` quantizers and `heterogeneous_axis=()` — flat, static, per-tensor grids ([decisions.md:704-715](.claude/memory/decisions.md#L704)). We borrow HGQ2's bit-exact Keras↔hls4ml guarantee and its EBOPs *metric*, not its mechanism.

**3. Our thesis.** Weights are fixed at 1 bit `{−1,+1}` **a priori, everywhere** — no search, no learned layout. The MAC collapses to a sign-flip and an adder tree. The open research question is then the *other* axis: how far can activations go (A8 → A6 → A4) before efficiency, resources, or latency break ([RESEARCH.md §1](RESEARCH.md)).

So HGQ asks *"what is the cheapest bit-width assignment that keeps the accuracy?"* and we ask *"if you don't get to choose bit widths at all — weights are 1 bit, full stop — what does that cost and does it fit?"* Orthogonal axes. Nobody has measured the intersection, which is a real opening.

## Are we chasing the same target? Yes — and he got there first, differently

arXiv:2510.24784 (Laatu, **Sun**, et al., *Sub-microsecond Transformers for Jet Tagging on FPGAs*) is the closest published system to ours. Same public HLS4ML LHC Jet dataset, same 260k test set, same 5 classes, and Round 14's `(N,3)` inputs with N ∈ {8,16,32,64} deliberately match their regime.

Their Table 1: **every HGQ-trained row is DSP = 0, II = 1**, 47–279k LUT, 44–140 ns, on an XCU250. Their per-class OvR AUCs average to ~0.897 (N=8) → ~0.943 (N=64) for MHA.

Which means the thing to be clear-eyed about:

> **0 DSP is not our unique claim.** They get 0 DSP by shrinking bit widths until multipliers vanish. We get it by binarizing. Both routes are published-viable.

## So what is actually ours

1. **The mechanism, not the outcome.** Binary weights → LUT/logic, structurally, at any width — versus a learned bit-width layout that happens to land under the DSP threshold.
2. **The regime argument.** Their design is iso-EBOPs at 350k — a budget they chose. Our motivation is that the conventional baseline *doesn't fit*: the vanilla W8A8 netlist demands **5,550 DSPs = 146.2% of the VU13P** ([RESEARCH.md §6.5](RESEARCH.md)). When nothing fits, "weights are 1 bit" stops being an aesthetic choice.
3. **Synthesis depth — this is your sharpest edge.** Their code reads post-route reports, but the papers in this space overwhelmingly stop at C-synthesis estimates. We found a case where a csynth `DSP = 0` became a **Vivado demand of 4,096 DSPs** the moment fabric binding was scoped rather than solution-wide ([RESEARCH.md §6.4](RESEARCH.md)). That failure mode is invisible to anyone who stops one stage earlier.
4. **β is structural for us, free for them.** In a plain MLP, ReLU homogeneity folds every BitNet scale factor into one scalar on the logit. Our graph has residual adds and a softmax and no LayerNorm to absorb scale, so β must be restored in-stream — 6L+3 affines, 3,621 of the original 4,133 DSPs. That's a transformer-specific result nobody else has had to solve.

## The objection you should expect

The FastML 2026 benchmark by Dorian Sloot (TU Wien — **independent third party, not Chang's group**) puts them head-to-head on our VU13P: **HGQ at AUC 0.9276 / 8.0k LUT / 0 DSP vs BitNet binary at 0.9178 / 87.3k LUT / 0 DSP** ([note](docs/literature/hls4ml-fpga-triggers/fastml2026_sloot_bitnet_survive_synthesis.md)). Same conference as your poster. Its thesis is that BitNet's op-count savings don't survive synthesis, and HGQ dominates the Pareto front.

Your two answers are already written up: (a) *regime* — their dense baseline fits at 3,651 DSPs, so nothing forces low precision; ours doesn't fit at 146%; (b) *stage* — all their hardware numbers are C-synthesis estimates, which is exactly the stage where the DSP question can lie to you. Their ternary-beats-binary row is a genuine open flank, since this tree has no ternary arm by decision.

## Anchor

Our fitting zero-DSP operating point: **1,689,320 CLB LUT = 97.8% of the VU13P at 0 DSP**, trained AUC **0.8701 ± 0.0020**, meeting 5 ns pre-route (WNS +0.65), 240 ns/jet ([RESEARCH.md §6.3](RESEARCH.md)). Their published route to 0 DSP is cheaper in LUT and higher in AUC. Ours answers a different question — *what happens when the bit width isn't yours to choose* — and answers it one synthesis stage further down.

**The edge / where I'd be careful.** Don't put their Fig. 2 AUCs in a table beside ours: the paper never states whether those are the float or quantized model, they apply an unpublished pT gate in preprocessing, their device is XCU250, and every row is pinned to a shared 350k-EBOPs budget so LUT is fixed and accuracy is the free variable. Also, a straight "we're better" framing won't survive a referee — the honest framing is *different mechanism, harsher regime, deeper verification*.

Want me to seed this into the KB (`lab kb add`) so it answers instantly next time, or write it up as the "related work / positioning" paragraph you can say out loud at the poster?

---

## You · 15:22

how did he make a binary bitnet so small

---

## Claude · 15:23

Let me get our own operation counts so the comparison is quantitative rather than hand-wavy.

The EBOPs store lets me verify my op-count arithmetic exactly. Let me sanity-check the framing before I commit to it.

Verified the sharpest claim against the paper itself before using it. Here it is.

## First, disambiguate: that's not Chang

The `BitNet binary` row at 87.3k LUT is **Sloot's** (TU Wien, FastML 2026). Chang Sun has no BitNet model anywhere — his line is HGQ. So the question is really *"how is Sloot's binary net 20× smaller than ours?"*

**Answer: he didn't make BitNet small. He had a small problem.**

## The arithmetic

I reconstructed our op counts from [ebops_r14.json](bnjettag/results/r14/ebops_r14.json) and they close to the digit (9,188,526 EBOPs for W8A8-n8), so these are exact, not estimated:

| | Sloot's BitNet binary | Ours (n8) |
|---|---|---|
| Model | 16 feat → 64 → 32 → 32 MLP | transformer, d=32, 2 layers, 4 heads, FFN 64 |
| Task | binary q/g vs W/Z/t | 5-class macro-OvR |
| Binary weight MACs | **~4,150** (computed from topology) | **133,024** (exact) |
| Activation×activation products | **0** | **8,192** (4,096 scores + 4,096 context) |
| β scale factors | folded free onto the logit | restored in-stream, 6L+3 affines |

**32× the binary arithmetic**, and the model is only ~19k parameters — the size isn't the model, it's that a transformer *reuses* every weight across all 8 tokens while an MLP fires each weight once.

Then the part binarization can't help at all: attention needs `Q·Kᵀ` and `A·V`, which are **activation × activation**. There is no weight to binarize. Those 8,192 products stay real multipliers — and they're precisely what forced our fabric-binding fight (10-bit × 8-bit maps to DSP48E2, 8-bit × 4-bit doesn't, [RESEARCH.md §6.3](RESEARCH.md)). An MLP has zero of these. **That asymmetry is structural and permanent.**

Third: in a plain MLP, ReLU positive-homogeneity lets every BitNet β collapse into one scalar on the output logit — genuinely free. Our graph has residual adds and a softmax and no LayerNorm to absorb scale, so β must come back in-stream. That cost 3,621 of the original 4,133 fx8 DSPs.

**Don't divide the LUT ratio by the MAC ratio.** 32× the ops for 19× the LUT looks like we win per-MAC, but his 87.3k is a **C-synthesis estimate** and our 1,689,320 is **post-`opt_design`**. Our own calibration is 0.442–0.482 post-opt/csynth, and RESEARCH.md says explicitly *never pool it across designs*. If his design calibrates anywhere similar, his real number is ~40k and the true ratio is ~42×, flipping it. The stage-robust statement is: **scale dominates; per-MAC efficiency is unresolvable across stages.**

## The part that should actually bother you

In Sloot's own table, BitNet binary (87.3k) is **bigger** than QKeras binary (60.6k) — same weights, same arithmetic. The likely reason is that the free β fold reappears as accumulator width: his precisions climb `ap_fixed<28,10>` → `<40,22>` layer by layer, and a 40-bit add costs ~40 LUT. *(That mechanism is our inference — he states the widths but never a reason.)*

And HGQ lands at **8.0k LUT, AUC 0.9276** — ten times smaller than BitNet binary at higher accuracy. Now confirmed from the paper itself (arXiv:2405.00645, §3.1.2 and Fig. 4):

> "a sufficiently small *f* will cause the corresponding parameters in the network to vanish, effectively pruning these parameters… the **majority of the weights being quantized to zero bits (pruned)**"

**HGQ's floor is 0 bits. BitNet's floor is 1 bit.** HGQ isn't doing cheaper arithmetic — it's doing *less* arithmetic, because bit-width regularization is unstructured pruning by another name. A weight driven to zero width is a deleted wire. Binary can never do that: every weight is ±1, always present, always an adder. That is why HGQ dominates the Pareto front, and it's the objection to prepare for.

On Chang specifically: his Table 1 LUT figures (47–279k) are **pinned by construction** — every row is trained to a shared 350k-EBOPs budget, so LUT is the input and accuracy the free variable. And his smallest row, MHA at 47k, is disqualified by the paper's own admission that the attention block collapsed into a Deep Set. Don't read 47k as an achievement of the method.

## Anchor

133,024 binary MACs + 8,192 attention products + in-stream β → **1,689,320 CLB LUT, 97.8% of the VU13P, 0 DSP**, AUC 0.8701 ± 0.0020 ([RESEARCH.md §6.3](RESEARCH.md)). The gap to 87k isn't a technique we're missing; it's ~32× the arithmetic on a harder task, measured a stage deeper.

**Edge:** the accumulator-width story is inference, not his claim. The per-MAC comparison genuinely can't be settled without a like-for-like stage. And we've never run HGQ's actual mechanism on our architecture — binary weights *plus* trainable bit-widths on everything else is unmeasured by anyone, and it's the obvious experiment.

Two things I can do next, say the word: seed this into the KB so it's instant next time, or write the missing HGQ dossier — [INDEX.md:108](docs/literature/INDEX.md#L108) flags 2405.00645 as the one load-bearing reference with no note, and I now have the full text extracted.
