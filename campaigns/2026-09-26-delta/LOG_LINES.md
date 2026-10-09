# LOG_LINES — method atlas (collected for the orchestrator; nothing here has been appended)

Collected 2026-09-27 by experiment-designer from the "Log lines to append" sections of the eight
campaign files that carry one: `research/THEORY.md`, `research/{B,R,Q,A,P}-*.md`,
`inventory/tried-already.md` and `inventory/code-surface.md`. (The brief says seven; eight files have
the section, so all eight are here.) Every line below is copied byte for byte from its file: the text is unchanged.
Grouping is by target log. Deduplication: an exact-duplicate check over all 52 bullet lines found
none. Lines about the same primary source, worded differently, are kept and cross-referenced in the
overlap table at the end, so the orchestrator can keep one. Notes by the collector are in
*[collector note]* lines **outside** the copied text and are not to be appended.

Newest-on-top order is the orchestrator's job; the order here is by source file.

## 1. `.claude/memory/research-log.md`

### From `research/THEORY.md` (THEORY)

- 2026-09-26 — THEORY for method atlas (`campaigns/2026-09-26-method-atlas/research/THEORY.md`).
  Primary sources fetched and read in the relevant sections: Helwegen et al. 2019 Bop/inertia
  https://arxiv.org/abs/1906.02107; Liu et al. 2021 Adam/weight decay/FF ratio
  https://arxiv.org/abs/2106.11309; Nagel et al. 2022 QAT oscillations
  https://arxiv.org/abs/2203.11086; Anderson & Berg 2017 binary geometry
  https://arxiv.org/abs/1705.07199; BiBERT https://arxiv.org/abs/2203.06390; BinaryBERT
  https://arxiv.org/abs/2012.15701; Martinez et al. real-to-binary
  https://arxiv.org/abs/2003.11535. Abstract level only: Yin et al. STE
  https://arxiv.org/abs/1903.05662, IR-Net https://arxiv.org/abs/1909.10788, BiT
  https://arxiv.org/abs/2205.13016, ReActNet https://arxiv.org/abs/2003.03488, Zhai et al.
  entropy collapse https://arxiv.org/abs/2303.06296, Dong et al. rank collapse
  https://arxiv.org/abs/2103.03404, SGDR https://arxiv.org/abs/1608.03983, Keskar et al.
  https://arxiv.org/abs/1609.04836. Transfer: all are ImageNet CNNs or BERT/LLMs; none is
  a small norm-free transformer on 3-feature jets or under EBOPs. Direction only.
- 2026-09-26 — HGQ arXiv:2405.00645v3 §3.3 Eq. 11 fetched (closes the INDEX "known gap" in
  part): EBOPs = Σ b_i·b_j + Σ max(b_k, b_l), accumulators not discussed, 0-bit = pruned.
  https://arxiv.org/abs/2405.00645. Our per-layer counting rule verified on
  `bnjettag/results/ebops-n8-20260910/analysis/3bynw2ra/artifact/activation_widths.jsonl`
  epoch 0 (every shape formula exact; the sum equals the logged 1,739,182). A literature note
  for HGQ is still missing.
- 2026-09-26 — Derived, flag for the record: binary weights pinned at 1 bit leave the EBOPs
  penalty only structured (channel) pruning. At N=64 A07, scores + ctx are 76 % of the traced
  initial 24.8M EBOPs, and six d×d layers at a 1-bit mean input width already cost 393,216 >
  350k. Reference points, not a floor ([A7] stays unmeasured). With the fan-in-3 binary
  `input_proj` and one β, only 8 input directions are expressible. The attention-entropy
  diagnostic needs log(n_valid) normalization under the unmasked pT gate.

### From `research/B-binarization.md` (B cards)

- 2026-09-26 — Bulat & Tzimiropoulos, "XNOR-Net++: Improved Binary Neural Networks," BMVC 2019,
  arXiv:1909.13863 (accessed 2026-09-26). Per-channel/learned scale factor for binary conv nets;
  relevant as the per-channel-β candidate (B03) but breaks our SCORE_FOLD/EXPLICIT_SCALE fold
  table by turning a scalar multiply into a per-channel one — abstract-level read only, no table
  number carried.
- 2026-09-26 — Liu et al., "Bi-Real Net," ECCV 2018, arXiv:1808.00278 (accessed 2026-09-26).
  ApproxSign backward + identity shortcut for 1-bit CNNs; relevant as a backward-only STE
  alternative (B05), zero deployment delta — abstract-level read only.
- 2026-09-26 — Qin et al., "Forward and Backward Information Retention for Accurate Binary Neural
  Networks" (IR-Net), CVPR 2020, arXiv:1909.10788 (accessed 2026-09-26). Libra-PB (balance +
  standardize + power-of-two scale) and EDE (annealed backward); relevant because our current
  centered-absmean scheme is already half of Libra-PB, and the power-of-two scale is the one
  candidate that could cheapen the β-fold hazard rather than just improve accuracy — abstract-level
  read only, table numbers not opened.
- 2026-09-26 — Wu et al., "Estimator Meets Equilibrium Perspective: A Rectified Straight Through
  Estimator" (ReSTE), ICCV 2023, arXiv:2308.06689 (accessed 2026-09-26). Power-function annealed
  backward; relevant as a 2023, more recent alternative to older STE variants — abstract-level
  read only.
- 2026-09-26 — Helwegen et al., "Latent Weights Do Not Exist: Rethinking Binarized Neural Network
  Optimization" (Bop), NeurIPS 2019, arXiv:1906.02107 (accessed 2026-09-26). Optimizer-level
  alternative removing the latent float entirely; relevant as the largest architectural delta in
  this family and the weakest evidence for transfer (designed for W1A1, we run W1A8→W1A4) —
  abstract-level read only.
- 2026-09-26 — Bai et al., "BinaryBERT: Pushing the Limit of BERT Quantization," ACL 2021,
  arXiv:2012.15701 (accessed 2026-09-26). Ternary-weight-splitting two-stage training; relevant as
  a progressive-binarization candidate (B11) but at 110M-parameter BERT scale, a transfer risk
  flagged explicitly — abstract-level read only.
- 2026-09-26 — Liu et al., "BiT: Robustly Binarized Multi-distilled Transformer," ICLR 2023,
  arXiv:2205.13016 (accessed 2026-09-26). Multi-step distillation into binary; relevant as the
  cheapest-to-try idea in the family (reuse an existing FP32/W8A8 checkpoint as teacher) —
  abstract-level read only, GLUE numbers not opened.
- 2026-09-26 — Liu, Shen, Savvides & Cheng, "ReActNet," ECCV 2020, arXiv:2003.03488 (accessed
  2026-09-26). RSign/RPReLU learnable activation shift; relevant as the one card orthogonal to
  every weight-binarization choice in this family, adapted here from W1A1 to W1A8→W1A4 — 69.4%
  ImageNet top-1 W1A1 number does not transfer, cited only for the mechanism.
- 2026-09-26 — Qin et al., "BiBERT: Accurate Fully Binarized BERT," ICLR 2022, arXiv:2203.06390
  (accessed 2026-09-26). Read and omitted from the card set (see "Omitted and why"): overlaps B12/
  B13 without a distinct weight-binarization mechanism.

### From `research/R-recipe.md` (R cards)

- 2026-09-26 — Loshchilov & Hutter, "SGDR: Stochastic Gradient Descent with Warm Restarts,"
  arXiv:1608.03983, https://arxiv.org/abs/1608.03983 — the exact LR-schedule family Sun et
  al.'s code implements (t_mul=1, m_mul=1 special case); relevant for R02/R03 restart-variant
  design; abstract-level CIFAR effect only (3.14%/16.21%), no full-table number fetched, does
  not transfer numerically regardless.
- 2026-09-26 — Foret, Kleiner, Mobahi, Neyshabur, "Sharpness-Aware Minimization for Efficiently
  Improving Generalization," arXiv:2010.01412, https://arxiv.org/abs/2010.01412 — candidate
  flatness-seeking optimizer wrapper (R11); binary-specific caveat (flat in float shadow-weight
  space is not established to imply anything about the thresholded binary weights) is ours, not
  the paper's; their Fig. 1 (read directly) reports 0-40% relative error reduction across
  benchmarks, no single number transfers.
- 2026-09-26 — Liu, Cai, Zhuang, "Sharpness-aware Quantization for Deep Neural Networks,"
  arXiv:2111.12273, https://arxiv.org/abs/2111.12273 — nearest published SAM-for-low-bit
  result (R11), but 4-bit CNN/ViT, not a binary transformer; abstract-level numbers only
  (+1.2% ViT-B/16, +0.9% ResNet-50 top-1 over prior SOTA at 4-bit), no transfer to 1-bit.
- 2026-09-26 — Izmailov, Podoprikhin, Garipov, Vetrov, Wilson, "Averaging Weights Leads to
  Wider Optima and Better Generalization" (SWA), arXiv:1803.05407,
  https://arxiv.org/abs/1803.05407 — candidate for R08; raises the re-thresholding-before-
  export question for binary weights specifically, which the paper does not address
  (continuous-weight setting only); their Fig. 4/5 (read directly, PreResNet-164/VGG-16 on
  CIFAR-100) show a qualitatively wider basin, no portable accuracy number.
- 2026-09-26 — Goyal, Dollár, Girshick, Noordhuis, Wesolowski, Kyrola, Tulloch, Jia, He,
  "Accurate, Large Minibatch SGD: Training ImageNet in 1 Hour," arXiv:1706.02677,
  https://arxiv.org/abs/1706.02677 — source of the linear LR-scaling rule (R06) and gradual
  warmup (R04); their Table 1 (read directly): gradual warmup at batch 8k matches the batch-256
  baseline within 0.14 points top-1 error (23.74%±0.09% vs. 23.60%±0.12%); constant warmup is
  worse than no warmup at all (25.88%±0.56% vs. 24.84%±0.37%). ImageNet/ResNet-50, full
  precision; no jet or binary transfer, mechanism only.
- 2026-09-26 — Dillon, Kasieczka, Olischläger, Plehn, Sorrenson, Vogel, "Symmetries, Safety,
  and Self-Supervision" (JetCLR), arXiv:2108.04253, https://arxiv.org/abs/2108.04253 — the
  primary source for physics-aware jet augmentation (R13: rotation, pT-scaled η-φ smearing);
  their setting is contrastive pre-training on top-tagging, not our supervised 5-class task, so
  no accuracy number transfers, only the augmentation definitions.
- 2026-09-26 — Hinton, Vinyals, Dean, "Distilling the Knowledge in a Neural Network,"
  arXiv:1503.02531, https://arxiv.org/abs/1503.02531 — canonical logit-distillation source for
  R09; MNIST/speech, full precision, abstract-level claim only, no transfer, mechanism only.
- 2026-09-26 — Zagoruyko & Komodakis, "Paying More Attention to Attention," arXiv:1612.03928,
  https://arxiv.org/abs/1612.03928 — attention-map/feature distillation source for R09's
  attention variant; CNN spatial activation-map matching, not transformer softmax(QKᵀ)
  attention weights — flag this distinction if R09's attention-map variant is picked up.
- 2026-09-26 — Müller, Kornblith, Hinton, "When Does Label Smoothing Help?," arXiv:1906.02629,
  https://arxiv.org/abs/1906.02629 — for R10; abstract states label smoothing hurting a
  *subsequent* distillation step, directly relevant if R09 and R10 are ever combined in a
  later wave; specific figure/section for the claim not identified in this session.
- 2026-09-26 — Kingma & Ba, "Adam: A Method for Stochastic Optimization," arXiv:1412.6980,
  https://arxiv.org/abs/1412.6980 — the optimizer Sun et al.'s code calls with framework
  defaults (R01, `run_train.py:97`); orientation only, no jet/binary number.
- 2026-09-26 — Loshchilov & Hutter, "Decoupled Weight Decay Regularization," arXiv:1711.05101,
  https://arxiv.org/abs/1711.05101 — the mechanism behind our optimizer's decoupled weight
  decay (R07, `bnhgq2/train.py:389-390`); abstract-level claim only, no jet/binary number.
- 2026-09-26 — Smith, "Super-Convergence: Very Fast Training of Neural Networks Using Large
  Learning Rates," arXiv:1708.07120, https://arxiv.org/abs/1708.07120 — source for the
  one-cycle policy (R05); CIFAR/ImageNet, full precision, no jet/binary number transfers.
- 2026-09-26 — Szegedy, Vanhoucke, Ioffe, Shlens, Wojna, "Rethinking the Inception
  Architecture," arXiv:1512.00567, https://arxiv.org/abs/1512.00567 — introduces label
  smoothing (R10, §7); ImageNet, full precision, no jet/binary number transfers.
- 2026-09-26 — Tarvainen & Valpola, "Mean teachers are better role models," arXiv:1703.01780,
  https://arxiv.org/abs/1703.01780 — EMA-of-weights precedent cited for R08 in lieu of the
  non-arXiv Polyak & Juditsky (1992) source; semi-supervised setting, not ours, mechanism only.
- 2026-09-26 — Huang, Sun, Liu, Sedra, Weinberger, "Deep Networks with Stochastic Depth,"
  arXiv:1603.09382, https://arxiv.org/abs/1603.09382 — block-skipping variant for R12; needs
  an L>1-block architecture (family M) before it applies to our current 1-block anchor.

### From `research/Q-activation-ebops.md` (Q cards)

- 2026-09-26 — A2Q: Accumulator-Aware Quantization with Guaranteed Overflow Avoidance, Colbert
  et al., arXiv:2308.13504 (expands arXiv:2301.13376) — https://arxiv.org/abs/2308.13504 —
  addresses the `[L2]` EBOPs-excludes-the-accumulator gap in general, but its L1-norm-bounded
  weight-magnitude mechanism has no analogue post-absmean-binarization (our effective weights
  are fixed-magnitude ±β already); for OUR specific ±1 weight type the accumulator width is
  exactly computable in closed form (`b_act + ceil(log2(fan_in))`) without A2Q's training
  method — a cheaper fix than porting the paper. WebFetch of the abstract page returned no
  table-level numbers; none quoted.
- 2026-09-26 — A2Q+: Improving Accumulator-Aware Weight Quantization, Colbert et al.,
  arXiv:2401.10432 — https://arxiv.org/abs/2401.10432 — successor to A2Q; same non-transfer
  caveat as above; not read past the title/abstract level.
- 2026-09-26 — CMS, "Reconstructing jets in the Phase-2 upgrade of the CMS Level-1 Trigger with
  a seeded cone algorithm," arXiv:2310.08062 — https://arxiv.org/html/2310.08062 — fetched and
  read looking for L1 PUPPI candidate per-feature bit widths; **not found** in this source
  (states link bandwidth and the 128-particle deregionizer truncation only); the search for this
  number should continue elsewhere (CMS Phase-2 L1T TDR CERN-LHCC-2020-004, or correlator
  firmware dataformat headers) before Q11 is scheduled.
- 2026-09-26 — WOMBAT: Design and FPGA Implementation of a DNN L1 Trigger System for Jet
  Substructure ID and Boosted H→bb Tagging, arXiv:2505.05532 — https://arxiv.org/pdf/2505.05532
  — fetched directly to check a search-snippet claim of "16-bit FPGA deployment precision";
  **that claim is NOT present in this paper's abstract/text as retrieved.** Logged as a
  correction: do not cite WOMBAT for an input/deployment bit-width; the snippet's true source is
  still unidentified.
- 2026-09-26 — Wortsman, Lee, Gilmer, Kornblith, "Replacing softmax with ReLU in Vision
  Transformers," arXiv:2309.08586 — https://arxiv.org/abs/2309.08586 — ReLU-attention (divided
  by sequence length) approaches softmax-attention scaling on ImageNet-21k ViTs; candidate
  mechanism for Q10 (removes the one non-multiply-accumulate op in our attention block); not a
  jet-tagging, binary-weight, or FPGA source — mechanism transfer only, no number transferred.
- 2026-09-26 — Ramapuram et al., "Theory, Analysis, and Best Practices for Sigmoid
  Self-Attention," arXiv:2409.04431 — https://arxiv.org/abs/2409.04431 — sigmoid replacing
  softmax normalization; same Q10 candidacy and same non-transfer caveat as above.
- 2026-09-26 — Stevens, Venkatesan, Dai, Khailany, Raghunathan, "Softermax: Hardware/Software
  Co-Design of an Efficient Softmax for Transformers," DAC 2021, arXiv:2103.09301 —
  https://arxiv.org/abs/2103.09301 — base-2 exponent + low-precision softmax + online
  normalization; closest hardware-motivated precedent for Q08/Q10; reported efficiency numbers
  are search-summary level only, not verified against the paper's tables in this pass.
- 2026-09-26 — `hgq.layers.softmax.QSoftmax._compute_ebops`, local HGQ2 install
  (`~/hgq2/HGQ2/src/hgq/layers/softmax.py:134-155`) and `hgq.quantizer.internal.
  fixed_point_quantizer`'s `fbits = relu(i+f)` (`fixed_point_quantizer.py:437`) — primary-source
  code reads (not a paper) that corrected Q08 (softmax IS priced in EBOPs) and Q12 (0-bit
  collapse is already reachable under the anchor's own bounds) from an earlier, wrong reading of
  our own wrapper's docstring; logged since both corrections change what two cards claim.
- 2026-09-26 — Chang jsc150 reference code, `reference-code/HGQ2-examples/jsc150/model.py`
  (`get_model`, lines 277-296) — re-read for width-initialization values; corrected to
  activation-side `i0=0 (default), f0=7, WRAP` (likely 8 total bits, matching our default, not
  "7-bit vs. 8-bit") to ground Q03; `docs/chang-vs-bnjettag.md:146`'s "b0=7/f0=7" cell conflates
  the separate weight-side (`kbi b0=7`) and activation-side (`kif f0=7`) parameters — re-verified
  against the source file directly rather than quoted from the doc alone.
  *[collector note, not to append: this line says activation `i0=0 (default)`; the Q03 card body says `i0` defaults to **2** (`hgq/quantizer/config.py:249`, verified 2026-09-26) and the anchor STUDY fidelity table says `ic=MinMax(0,12)`. The three disagree. Routed to deep research item DR-09 in ATLAS.md; append only after it is settled.]*
- 2026-09-26 — `bnjettag/code/hgq2/bnhgq2/train.py:106-163` and `ablation.py:19,253` — primary-
  source code read distinguishing `BetaPID` (closed-loop, fixed target) from `beta_schedule`/
  `BetaScheduler`/`ParetoFront` (open-loop piecewise β, also fixed target/threshold); corrected
  Q04 (both are real, distinct, already-implemented mechanisms) and Q05 (a genuinely MOVING
  target_ebops does not exist in this codebase yet — it is new code, not the 2026-09-15 arm).
  *[collector note, not to append: this line says a moving `target_ebops` "does not exist in this codebase". That holds for the `train.py` path only: the screen-bundle runner the anchor pins reads `experiment.target_schedule` per epoch (`ablation.py:126-131`, code-surface §1f), and it was run (tried-already C7). Routed to DR-11.]*

### From `research/A-architecture.md` (A cards)

- 2026-09-26 — Wang et al., "Linformer: Self-Attention with Linear Complexity," arXiv:2006.04768,
  https://arxiv.org/abs/2006.04768 — low-rank K/V projection for O(N) attention; full-precision,
  BERT/RoBERTa scale, no binary or FPGA number; transfers as mechanism only (cards A10, A15).
- 2026-09-26 — Lee et al., "Set Transformer: A Framework for Attention-based Permutation-
  Invariant Neural Networks," arXiv:1810.00825, https://arxiv.org/abs/1810.00825 — Pooling by
  Multi-head Attention (PMA), permutation-invariant set pooling; full-precision, generic set
  benchmarks, no binary or FPGA number; transfers as mechanism only (card A07).
- 2026-09-26 — Shazeer, "GLU Variants Improve Transformer," arXiv:2002.05202,
  https://arxiv.org/abs/2002.05202 — gated FFN variants (ReGLU/GEGLU/SwiGLU); full-precision,
  T5/LLM scale, no binary or FPGA number; transfers as mechanism only, and flags a new act×act
  multiply site relevant to the 0-DSP claim (card A13).
- 2026-09-26 — Liu et al., "Bi-Real Net: Enhancing the Performance of 1-bit CNNs...,"
  arXiv:1808.00278, https://arxiv.org/abs/1808.00278 — real-valued shortcut around a binary
  block; ImageNet, 1-bit-weight-and-activation CNNs (our activations are 8-bit, not 1-bit), no
  transformer, no FPGA number; transfers as mechanism only (card A12).
- 2026-09-26 — Zhang & Sennrich, "Root Mean Square Layer Normalization," arXiv:1910.07467,
  https://arxiv.org/abs/1910.07467 — RMSNorm; full-precision Transformer/BERT scale, no binary
  or FPGA number; transfers as mechanism only (card A05).
- 2026-09-26 — Lan et al., "ALBERT: A Lite BERT...," arXiv:1909.11942,
  https://arxiv.org/abs/1909.11942 — cross-layer parameter sharing; BERT scale (110M+ params),
  full precision, no binary or FPGA number; transfers as mechanism only, specifically that
  attention-sharing costs less than FFN-sharing (card A02).
- 2026-09-26 — Que, Sun, et al., "JEDI-linear: Fast and Efficient GNNs for Jet Tagging on
  FPGAs," arXiv:2508.15468, https://arxiv.org/abs/2508.15468 (already noted in
  `literature/jet-tagging-transformers/2508.15468_jedi_linear.md`; re-read for this family) —
  affine-edge, GAP-factored O(N) interaction network, HGQ mixed precision + da4ml synthesis,
  82.4% accuracy / 0 DSP / 79 ns at 64 particles×16 features on VU13P; not a binary-weight
  number, different toolchain — transfers as an architectural mechanism (mean-field pairwise
  approximation) and as evidence that naive O(N²) attention is a real DSP threat at trigger
  scale (card A11).

### From `research/P-inputs-data.md` (P cards)

- 2026-09-26 — Laatu, Sun, Cox et al., "Sub-microsecond Transformers for Jet Tagging on FPGAs,"
  arXiv:2510.24784 (accessed 2026-09-27, full PDF read, §§1-4 + references + figures) —
  https://arxiv.org/abs/2510.24784 — for method-atlas family P (N-series, gate, feature-set
  cards P01/P02/P05): confirms §2.1's stated input is "pT-sorted... three features: pT, η, and
  ϕ" with NO pT-gate mentioned anywhere in the text — the gate and its order-of-operations
  relative to standardization come from `jsc150/data.py` code only, not this paper. Also
  surfaces a discrepancy: the paper's stated features are plain η/ϕ, not the jet-frame-relative
  etarel/phirel the anchor recipe's code actually uses.
- 2026-09-26 — Odagiu et al., "Ultrafast jet classification at the HL-LHC," arXiv:2402.01876
  (accessed 2026-09-27, dossier note re-read) — https://arxiv.org/abs/2402.01876 — origin of the
  3-feature (pt, etarel, phirel) L1-realistic input convention (P05); their Deep Sets/Interaction
  Network baselines are permutation-invariant, so the paper has no ordering ablation to transfer
  to P04 — noted as a gap, not a result.
- 2026-09-26 — M. Pierini, J. M. Duarte, N. Tran, M. Freytsis, "HLS4ML LHC Jet dataset (150
  particles)," Zenodo record 3602260 (accessed 2026-09-27, record page fetched directly) —
  https://zenodo.org/records/3602260 — confirms dataset identity and derivation from Coleman et
  al. arXiv:1709.08705, and that it underlies arXiv:1804.06913/1908.05318; the record page does
  NOT itself enumerate per-particle features — DATASET.md's 16-feature list is this repo's own
  HDF5 measurement, not copied from Zenodo text (P05).
- 2026-09-26 — CMS, "Reconstructing jets in the Phase-2 upgrade of the CMS Level-1 Trigger with a
  seeded cone algorithm," arXiv:2310.08062 (accessed 2026-09-27, full text fetched) —
  https://arxiv.org/abs/2310.08062 — confirms total L1 decision latency ≈12.5 μs, ≈5 μs for
  track/calorimeter/muon reconstruction, ≈1 μs per Correlator layer, and their seeded-cone jet
  algorithm closing at 720 ns + 138 ns serial transmission inside the Correlator-Layer-2 budget —
  used in P12 for why a fixed operating point, not integrated AUC, is the deployment-relevant
  figure of merit. Did NOT confirm a PUPPI-candidate field list or bit precision — that claim in
  P05 is flagged as unconfirmed by a primary source in this pass (search digest only for
  arXiv:1808.02094 and the L1Phase2NNPuppiTau CMS TWiki; neither was read in full).

### From `inventory/code-surface.md` (research-log line)

- research-log.md: 2026-09-27. HGQ2-examples jsc150 at `6cdc6e34` imports `StopIf` and uses `QLinformerAttentionT`, and neither is in hgq2 0.1.9 (PyPI wheel sha256 `7497542...c43c`), so Chang's HEAD code needs a newer hgq2 than our pin. There is no LICENSE file in that clone. https://pypi.org/project/hgq2/0.1.9/ (accessed 2026-09-27).

## 2. `.claude/memory/decisions.md`

From `inventory/code-surface.md`:

- decisions.md (finding, suggest `/log-decision`): 2026-09-27. `quant.weight: "kbi_learnable"` is accepted by `bnhgq2/config.py:40` in every state, but `qat.build_qat_model` has no branch for it and builds the static int8 (W8A8) grid instead. Any config that sets it trains W8A8 silently. Check: grep `kbi_learnable` in `qat.py` returns nothing (S, Ph, R).
- decisions.md (finding): 2026-09-27. In `publication/code/hgq2` and `bnjettag/code/hgq2`, `arch.pos_enc: "none"` is ignored (qat.py:462 adds the positional table unconditionally). The batch20260918 b02 runs used a bundle with `pos_enc` support (`positional_table_absent: true` in their preflight), so no past run is affected. The trap applies to reruns from those trees. Check: `grep -n AddPositional publication/code/hgq2/bnhgq2/qat.py`.
- decisions.md (finding): 2026-09-27. In the screen-bundle runner (`ablation.run_training`), the keys `train.lr_schedule`, `train.ebops.{enable,controller,beta_schedule,selection,stop_on_target,target_ratio}`, `train.clip_mode`, `train.es_patience`, `arch.input_std`, `quant.act_recalib_epochs` and `experiment.checkpoint_every_epochs` are inert. Only the `train.py` path, or no code at all, reads them. Check: §1 of `campaigns/2026-09-26-method-atlas/inventory/code-surface.md`.

## 3. `.claude/memory/experiment-log.md`

From `inventory/tried-already.md` (copied with its code fence):

For `.claude/memory/experiment-log.md`, top, in the house format:

```
## 2026-09-27 — What has this project already tried, and which of it failed for a known reason?  (campaigns/2026-09-26-method-atlas; inventory)
Question:        Inventory of every training, architecture, quantization, EBOPs-control, input and recipe method run so far, so the atlas does not re-propose a failed idea without saying why.
Design:          Read-only sweep of the logs, RESEARCH.md, campaign READMEs/STUDYs and publication/docs/current-work; numbers copied with file:line, none recomputed.
Result:          68 tried rows in ten families, 12 failed with a recorded mechanism (campaigns/2026-09-26-method-atlas/inventory/tried-already.md).
Interpretation:  Two record corrections. (1) campaigns/2026-09-26-training-batch/STUDY.md:71 calls the pT-weighting BASE a "1,000 epochs" run; its config bnjettag/code/hgq2/configs/ptw-n8-20260925-base-w1a8.json:35,46 has epochs 101, es_patience 15 and no EBOPs block, so the 0.0019 accuracy sd is from the archived Round-14 recipe, not a constrained 1,000-epoch run. (2) BNJetTagAug is a W&B project name (decisions.md:662); no data-augmentation experiment exists in any record.
Ops-pointer:     —
```

*[collector count: 52 bullet lines in sections 1-2 plus one experiment-log entry in section 3]*

## 4. Same-source overlap (lines kept; pick one when appending)

| primary source | lines that cite it |
| --- | --- |
| BiBERT, arXiv:2203.06390 | THEORY first line (in its list); B cards, last line |
| IR-Net, arXiv:1909.10788 | THEORY first line (abstract-level list); B cards, IR-Net line |
| Bop / Helwegen et al., arXiv:1906.02107 | THEORY first line; B cards, Bop line |
| BinaryBERT, arXiv:2012.15701 | THEORY first line; B cards, BinaryBERT line |
| BiT, arXiv:2205.13016 | THEORY first line; B cards, BiT line |
| ReActNet, arXiv:2003.03488 | THEORY first line; B cards, ReActNet line |
| SGDR, arXiv:1608.03983 | THEORY first line; R cards, SGDR line |
| Bi-Real Net, arXiv:1808.00278 | B cards, Bi-Real line; A cards, Bi-Real line |
| CMS seeded-cone jets, arXiv:2310.08062 | Q cards, CMS line; P cards, CMS line (P adds latency figures; both say no PUPPI bit width) |
| HGQ, arXiv:2405.00645 | THEORY second line only |

## 5. Lines proposed by experiment-designer for ATLAS.md (separate; not from the eight files)

Replacement text, fixer v2 (2026-09-27). Each block replaces the line or entry already in the
shared log (the experiment-log stub at `.claude/memory/experiment-log.md:11-16` and the
two-tier line at `.claude/memory/decisions.md` "2026-09-27 (orchestrator, method atlas)", first
bullet). The orchestrator applies them; nothing here has been appended.

For `.claude/memory/experiment-log.md`, replacing the atlas stub (house format):

```
## 2026-09-27 — Which of about 100 binarization, recipe, width/EBOPs, architecture and input methods moves the binary N=64 tagger at 350k and 5M EBOPs, beyond the Sun et al. recipe anchor?  (campaigns/2026-09-26-method-atlas; designed)
Question:        Pre-registered queue, not one experiment: for each of 103 entries (50 singles incl. 4 labelled non-binary baselines, 53 combinations incl. the 22 cells of a 2^(5-1) res V and a 2^(4-1) res IV fractional factorial), does it change validation accuracy or 350k feasibility against the anchor's own snapshot at the same seed, and does the named mechanism diagnostic move as THEORY predicts?
Design:          ATLAS.md + atlas.json. Anchor = training-batch arm A = E at 350k (d24, 2 heads, 1 block, FFN 32, no PE; [D19] Chang quantizers and [D21], both Kai-confirmed 2026-09-27); A07 at 350k is the descriptive arm A07-350 (floor-family feasibility reference), C = A07 at 5M; the anchor's second-wave arm NB covers atlas M049 at 350k. W1 zero-GPU (traced floors of every atlas architecture, 0-bit maps, accumulator EBOPs, input_proj rows); W2 singles and W3 combos screened 500 epochs (longer where the treatment starts at a restart), n seeds set at K2 from the anchor's epoch-500 sd (n in {4, 6, 8} sized for the whole advance rule, BH q=0.10 per wave x target plus mean gap >= 0.15 pt, 0.3 pt MDE target; n_W3 <= n_W2; ranking mode at 4 if none qualifies), paired to the anchor [A6] snapshot, anchor non-degeneracy rule inherited; 350k accuracy cells run on arm A; drift replicas A, A07-350, C in atlas.json; W4 confirm 7,000 epochs, 8 seeds, ROC-test once, Holm. Screen 344,000 run-epochs at n=4 to 684,000 at n=8 (1,793.3 to 3,565.7 pod-hours at the labelled 112.6 s/epoch projection, K=6). Bop scan seed gamma 1e-4, tau 1e-8 (DR-22). [fixer v2, 2026-09-27: anchor was A07-N64 at 350k (provisional), gate (ii) was mean gap >= 0.3 pt]
Result:          no result yet
Interpretation:  —
Ops-pointer:     —
```

For `.claude/memory/decisions.md`, replacing the first bullet of "2026-09-27 (orchestrator, method atlas)":

- Method-atlas campaigns run in two tiers. Screen: one Chang cosine cycle (500 epochs; 1,000-2,000 when the treatment starts at a restart), n seeds (4, 6 or 8, set at K2 from the anchor's epoch-500 sd so that the whole advance rule has 80 % power at a +0.3 pt gap under BH q = 0.10 within wave × target, with n_W3 ≤ n_W2 per target; if none qualifies, a declared ranking at 4 seeds with no advance claims), validation only (n = 62,000), paired to the anchor's own [A6] snapshot at the same seed (anchor arm A = E at 350k [D21]; C at 5M), feasible meaning the anchor's non-degeneracy rule, advance by BH plus mean gap ≥ 0.15 pt (δ/2 of the 0.3 pt MDE target, or δ_res/2), sign count descriptive; never quotable. [fixer v1, 2026-09-27: was 4 seeds and a 3-of-4-seeds rule; fixer v2, 2026-09-27: gate (ii) was mean gap ≥ 0.3 pt, which capped the power at a 0.3 pt gap at 0.5] Confirm: the full 7,000-epoch recipe, 8 seeds, ROC-test once, Holm across the confirm wave. Check: every atlas wave STUDY names its tier and cites `campaigns/2026-09-26-method-atlas/ATLAS.md` §5.

---

**Note (2026-09-27, rename).** The program was renamed Delta after these lines were collected (`review/DELTA_rename.md`). The lines above are kept as written; when pasting, read `campaigns/2026-09-26-method-atlas/` as `campaigns/2026-09-26-delta/`, `ATLAS.md` as `DELTA.md`, `atlas.json` as `delta.json`, "method atlas" as Delta, and the gap δ / δ_res as g₀ / g_res.
