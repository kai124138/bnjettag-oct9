---
title: what is a particle transfomrer
date: 2026-09-08
updated: "2026-09-09T22:19:54"
project: bnjettag-training-results
cwd: /Users/kaiyamaguchi/Downloads/bnjettag-training-results
model: claude-opus-5
git_branch: main
session_id: 3428cd29-a0a9-4fe9-9ce3-19706bd2cf1d
turns: 2
tool_calls: 11
status: done
tags:
  - claude-code
  - session
  - project/bnjettag-training-results
---

# what is a particle transfomrer

> [!abstract]- Session at a glance
> **2** turns · **11** tool calls · spans **5** min · `claude-opus-5`
>
> **Tools** Bash ×10, Skill ×1
> **Commands** `/explain-well`

---

## You · 12:00

what is a particle transfomrer

---

## Claude · 12:02

**Particle Transformer (ParT)** — Qu, Li & Qian, ICML 2022 ([arXiv:2202.03772](https://arxiv.org/abs/2202.03772); note at `docs/literature/jet-tagging-transformers/2202.03772_particle_transformer.md`) — is a transformer that treats a jet as an unordered *set* of its constituent particles and injects **pairwise particle-interaction physics directly into the attention scores**. It's the architecture family our tagger descends from, and the paper that released **JetClass** (100M jets, 10 classes).

**Mechanism (L2).** Each constituent becomes one token. Standard self-attention gives you scores `QKᵀ/√d`. ParT's one structural addition is a bias term:

```
A_h = softmax( Q_h K_hᵀ / √d  +  U_h )
```

`U` is built from physically motivated features of every *pair* of particles (angular separation Δ, k_T, momentum fraction z, pair mass m² — log-scaled in the paper), pushed through a small MLP into an `(H, T, T)` tensor and added to the pre-softmax logits of every block. At our scale — T = 16 particles, d_model 32, H = 4 heads — `Q, K, V` are each `(16, 32)`, the score matrix is `16×16` per head, and `U` would be `(4, 16, 16)`. Attention alone asks "which particles should talk to each other"; the interaction bias tells it, before it decides, which pairs are *kinematically* close. That's what beat ParticleNet.

**Anchor — how this relates to us.** BNJetTag is a small, binarized member of this family: transformer over jet constituents, `RESEARCH.md` §3 — d_model 32, 2 layers, 4 heads, FFN 64, 3 features (p_T, η_rel, φ_rel), N ∈ {8,16,32,64}. The lines you have selected, `qat.py:376–387`, are exactly the attention machinery — the `einsum` and `softmax` helpers; if the interaction bias were enabled, `U` would be added to the scores immediately before that `softmax` call. At N = 16 binary reaches **0.8956 ± 0.0002** ROC-test macro-OvR AUC vs **0.9128 ± 0.0013** FP32 (l1x3 inputs, 3-seed mean ± sd, `RESEARCH.md` §5) — a resolved +0.0172 deficit.

**The edge — three ways we are *not* ParT** (this gets blurred constantly):

1. **No interaction bias in Round 14.** The code path exists (`arch.pair_bias`, `PairFeatures` → `pair_fc1/fc2`, `qat.py:399` and `:497`) but is absent from every `r14-l1x3-*.json` config, so it's off. Our attention is plain.
2. **Pooling:** we mean-pool over particles; ParT uses class-attention pooling.
3. **Positional encoding:** we add a *learned table* over pT-ranked slots. ParT has none — it is permutation-invariant by construction, and we are not (the pooling is; the network isn't). Worth knowing before a PI asks.

And ParT itself is not a trigger model — it's full precision at ~100 constituents, an accuracy reference, never a deployment target. The nearest published thing to what we do is BitPart ([2508.07431](https://arxiv.org/abs/2508.07431)), which binarizes only FFN + head and leaves attention full precision.

Want me to write this into your study notes (`docs/reports/BNJetTag-presentation-study-guide.md` is uncommitted and looks like the right home)?
