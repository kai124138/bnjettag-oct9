# Research log (literature; newest on top; date = date read, 2026-10-05 unless noted)
Status flag: "abstract-level" = only abstract/summary fetched, not full text. Do not quote numbers beyond what is stated.

- 2026-10-08 | Qin et al., BiBERT (ICLR 2022): binarized-BERT loss from information degradation and forward/backward direction mismatch; Bi-Attention + direction-matching distillation. https://arxiv.org/abs/2203.06390 (abstract-level)
- 2026-10-08 | Liu et al., BiT (NeurIPS 2022): two-set binarization, elastic binary activation with learnable parameters, progressive multi-distillation. https://arxiv.org/abs/2205.13016 (abstract-level)
- 2026-10-08 | Bai et al., BinaryBERT (ACL 2021): irregular binary loss landscape; ternary weight splitting initialisation. https://arxiv.org/abs/2012.15701 (abstract-level)
- 2026-10-08 | He et al., BiViT (ICCV 2023): long-tailed softmax attention breaks plain binarization; softmax-aware binarization, learnable weight scales. https://arxiv.org/abs/2211.07091 (abstract-level)
- 2026-10-08 | Wang et al., BitNet (2023): BitLinear, 1-bit weights trained from scratch. https://arxiv.org/abs/2310.11453 (abstract-level)
- 2026-10-08 | Sun et al., HGQ (v3 Dec 2025): EBOPs = sum of multiplier width products + adder max widths; loss L + beta*EBOPs + gamma*sum(bits), gamma 2e-8; LUTs not linear in EBOPs. https://arxiv.org/abs/2405.00645 (HTML, first ~80 %, tool summary)
- 2026-10-08 | Odagiu et al., Ultrafast jet classification at the HL-LHC (MLST 2024): Deep Sets / interaction nets N<=32 on hls4ml jets; no N=64. https://arxiv.org/abs/2402.01876 (tool summary; table numbers unverified)
- 2026-10-08 | Bezio, Distilled Deep Sets for ATLAS HLT jet preselection on FPGA (conference abstract; teacher -> quantized student). https://indico.cern.ch/event/1496673/contributions/6637985 (abstract only)
- 2026-10-05 | Cheng et al., Assessing Parameter Redundancy in Transformers for Jet Tagging (Aug 2026), hourglass FFN, ParT/MIParT, no quantization; not a threat. https://arxiv.org/abs/2608.16061 (abstract-level)
- 2026-10-05 | PHAT-JeT (aaronw5/phat-jet-hw), HGQ2 -> da4ml -> Verilog, VU13P; N=64 74.58 % in-budget, 167k LUT, 96.6 ns, da4ml ESTIMATES not post-route; "NeurIPS 2026 submission 28409" per repo README. Competitor for the HGQ-transformer slot, not binary. https://github.com/aaronw5/phat-jet-hw (README summary only)
- 2026-10-05 | Koski et al., Transformer for Jet Tagging on Versal AI Engines (FCCM 2026, 16 Jun 2026), integer-only, AIE. https://arxiv.org/abs/2606.17500 (abstract-level)
- 2026-10-05 | Zheng, Sun, ... Que, JetFormer (23 Jan 2026), JetClass + hls4ml 150P, JetFormer-tiny for FPGA, HGQ+da4ml; hardware numbers not seen. https://arxiv.org/abs/2601.17215 (abstract-level)
- 2026-10-05 | Krause, Wang, Winterhalder, BitHEP (v1 Apr 2025, rev Feb 2026; SciPost Phys 20, 038, 2026), BitNet on q/g, SMEFT, calo sim; no hardware. https://arxiv.org/abs/2504.03387 (abstract-level)
- 2026-10-05 | Laatu, Sun, ... Spiropulu, Sub-microsecond Transformers for Jet Tagging on FPGAs (v1 Oct 2025; NeurIPS ML4PS 2025), HGQ2, XCU250, EBOPs 350k, Linformer-64 79.8 %, 78 ns, 202k LUT (search/summary); attention bitwidth >=1 bit; summaries show no seeds/error bars; post-route per repo note docs/chang-vs-bnjettag.md (gather_statistics.py reads post_route_util.rpt). https://arxiv.org/abs/2510.24784 ; https://neurips.cc/virtual/2025/123054
- 2026-10-05 | Schaefer et al. (CMS), Jet Tagging with DeepSets at the HL-LHC L1T (29 Sep 2025, rev Nov 2025). https://arxiv.org/abs/2509.24371 (abstract-level)
- 2026-10-05 | Rai, Prisha, Kumar, BitParT 1-bit ParT, top-tagging reference dataset, FP attention (v1 10 Aug 2025); no hardware numbers seen. https://arxiv.org/abs/2508.07431 (abstract-level)
- 2026-10-05 | Que, Sun, ... Luk, Spiropulu, JEDI-linear (21 Aug 2025; ICFPT 2025), <60 ns, 0 DSP, up to 6.2x fewer LUT than prior GNNs. https://arxiv.org/abs/2508.15468 (abstract-level)
- 2026-10-05 | Sun, Ngadiuba, Pierini, Spiropulu, Fast Jet Tagging with MLP-Mixers on FPGAs (5 Mar 2025; MLST 6, 035025). https://arxiv.org/abs/2503.03103 (abstract-level)
- 2026-10-05 | PolyLUT-Add (2406.04910); NeuraLUT (2403.00849); PolyLUT (2309.02334); LUT-DNN architecture/connectivity paper (2601.09773): LUT-based JSC networks. https://arxiv.org/abs/2403.00849 ; https://arxiv.org/abs/2309.02334 ; https://arxiv.org/abs/2406.04910 ; https://arxiv.org/abs/2601.09773 (abstract-level)
- 2026-10-05 | Odagiu et al., Ultrafast jet classification at the HL-LHC (arXiv Feb 2024; MLST Jan 2024 issue), Deep Sets / IN / JEDI-net, hls4ml 150P, O(100) ns. https://arxiv.org/abs/2402.01876 (abstract-level)
- 2026-10-05 | Que et al., LL-GNN (arXiv Sep 2022; ACM TECS Mar 2024). https://arxiv.org/abs/2209.14065
- 2026-10-05 | Ngadiuba et al., Compressing DNNs on FPGAs to binary and ternary precision with hls4ml (arXiv Mar 2020; MLST 2, 2021). https://arxiv.org/abs/2003.06308
- 2026-10-05 | Jet-tagging transformer hls4ml support: Jiang et al. 2402.01047 (Ultra Fast Transformers on FPGAs), 2409.05207 (Low latency transformer inference with hls4ml). https://arxiv.org/abs/2402.01047 ; https://arxiv.org/abs/2409.05207
