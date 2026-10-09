# Greater than the Sum of its LUTs: Scaling Up LUT-based Neural Networks with AmigoLUT

- **Full author list + affiliations (transcribed directly from the primary PDF, verbatim, this session):**
  - **Olivia Weng** — University of California San Diego (oweng@ucsd.edu)
  - **Marta Andronic** — Imperial College London
  - **Danial Zuberi** — University of California San Diego
  - Jiaqing Chen — Arizona State University
  - Caleb Geniesse — Lawrence Berkeley National Laboratory
  - George A. Constantinides — Imperial College London
  - Nhan Tran — Fermi National Accelerator Laboratory
  - Nicholas J. Fraser — AMD Research and Advanced Development, Dublin, Ireland
  - **Javier Mauricio Duarte** — University of California San Diego
  - **Ryan Kastner** — University of California San Diego
- **UCSD confirmation:** 4 of 10 authors (Weng, Zuberi, Duarte, Kastner) are affiliated with UC San Diego. **Javier Mauricio Duarte is a co-author** — this is Duarte-lab prior art, not merely lab-adjacent. Ryan Kastner (UCSD CSE, Kastner Research Group) is the other UCSD PI; the paper's PDF is hosted on his own lab site (kastner.ucsd.edu). **Correction to the brief's premise: the task description names "Olivia Weng et al." as the possible UCSD connection — confirmed correct, and the connection is stronger than "possibly": Duarte is a direct co-author.**
- **Venue / Year:** FPGA 2025 (ACM/SIGDA Int'l Symp. on Field Programmable Gate Arrays), Feb 27–Mar 1, 2025, Monterey, CA. ACM ISBN 979-8-4007-1396-5/25/02. DOI: **10.1145/3706628.3708874**. 11 pages.
- **No arXiv preprint found** (checked this session) — available via ACM DL (https://dl.acm.org/doi/10.1145/3706628.3708874), author-hosted PDF (https://kastner.ucsd.edu/wp-content/uploads/2025/01/admin/fpga25-amigoLUT.pdf, full text read directly this session), UC eScholarship (https://escholarship.org/uc/item/6v04460t), and Imperial Spiral (https://spiral.imperial.ac.uk/entities/publication/a1279586-22c1-439c-8a09-eae46948ffd5).
- **Code:** https://github.com/KastnerRG/amigolut
- **Topic area:** LUT-native neural networks for FPGAs

## TL;DR
LogicNets-style (and PolyLUT-, NeuraLUT-style) LUT-native NNs die on fan-in: LUT usage grows exponentially with per-neuron fan-in, so the *only* way to get more accuracy is more fan-in/depth, which "presents a poor tradeoff because we get minimal accuracy increase at the cost of exponential increases in LUT usage as well as decreases in throughput" (own abstract paraphrase). AmigoLUT instead **ensembles many small, independently-trained LUT-native models** (LogicNets, PolyLUT, or NeuraLUT as interchangeable "base models") and combines their outputs, so accuracy scales **linearly** with LUT count (number of ensemble members) rather than exponentially with fan-in. Key engineering contribution: a **hybrid I/O quantization scheme** (shared coarse 6-bit input quantizer feeding each ensemble member's own LUT6 fine requantizer, plus an output-requantization layer so member outputs can be summed cheaply) that avoids the naive per-member unique-quantizer blowup while avoiding the accuracy loss of fully-shared quantizers. Evaluated ensembling strategies: averaging, bagging, AdaBoost — **averaging wins** on JSC, MNIST, and HGCal (CMS high-granularity calorimeter compression).

## (a) Mechanism
An **ensembling method layered on top of the existing family**, not a new base architecture: each ensemble member is itself trained exactly as its underlying method prescribes (LogicNets/PolyLUT/NeuraLUT's own from-scratch co-training recipe — Brevitas QAT, fixed a-priori sparsity), independently initialized/trained (for averaging — their best method) or via bagging/AdaBoost resampling; AmigoLUT's own novel contribution is entirely in the **hardware mapping of the ensemble** (shared/hybrid quantizers, Fig. 7) and the **ensembling-strategy choice**, not in how any individual member is trained.

## (b) What it explicitly does NOT do
- **Inherits, does not remove, the base-method training constraint.** AmigoLUT does not consume an arbitrary pretrained network any more than LogicNets/PolyLUT/NeuraLUT do — it takes N independently-trained *instances of those same constrained architectures* and combines them.
- **MLP-only** (via its base models); no attention/sequence-model mention.
- **Explicitly does not (yet) achieve higher peak accuracy or lower LUT count than the contemporary single-model state of the art** — own words (§1, verbatim): *"Although AmigoLUT does not achieve higher accuracy or lower LUT usage than state-of-the-art work [PolyLUT-Add, DWN], our results show that, for certain lower accuracy benchmarks, AmigoLUT increases throughput and reduces LUT usage by over an order of magnitude."* I.e. AmigoLUT's value is in the **low-accuracy/small-model regime and in F_max/throughput**, not in beating PolyLUT-Add/DWN's best accuracy-per-LUT Pareto points (confirmed directly in their own Table 4, where PolyLUT-Add and DWN both out-resource AmigoLUT's best-accuracy configurations on JSC).

## (c) Exact published jet-tagging numbers — Table 4, primary PDF, verbatim (target **xcvu9p-flgb2104-2-i**, Vivado 2020.1, Out-of-Context, `Flow_PerfOptimized_high`; "JSC" dataset, sourcing not specified as CERNBox vs. OpenML in this paper)

| Model | Accuracy | LUT | FF | DSP | BRAM | Latency | F_max | Area×Delay |
|---|---|---|---|---|---|---|---|---|
| **AmigoLUT-NeuraLUT-XS (4 models)** | 71.1% | 320 | 482 | 0 | 0 | 3.5 ns | **1,445 MHz** | 1,120 |
| **AmigoLUT-NeuraLUT-XS (16 models)** | 72.9% | 1,243 | 1,240 | 0 | 0 | 5.0 ns | 1,008 MHz | 6,215 |
| **AmigoLUT-NeuraLUT-S (32 models)** | 74.4% | 42,742 | 4,717 | 0 | 0 | 9.6 ns | 520 MHz | 4.10×10⁵ |
| LogicNet-L | 73.1% | 36,415 | 2,790 | 0 | 0 | 6 ns | 390 MHz | 2.18×10⁵ |
| PolyLUT [JSC-M Lite operating point] | 75%* | 12,436 | 773 | 0 | 0 | 5 ns | 646 MHz | 62,180 |
| NeuraLUT [JSC-2L] | 72% | 4,684 | 341 | 0 | 0 | 3 ns | 727 MHz | 14,052 |
| PolyLUT [JSC-XL] | 75% | 236,541 | 2,775 | 0 | 0 | 21 ns | 235 MHz | 4.97×10⁶ |
| NeuraLUT [JSC-5L] | 75% | 92,357 | 4,885 | 0 | 0 | 14 ns | 368 MHz | 1.29×10⁶ |
| PolyLUT-Add | 75% | 36,484 | 1,209 | 0 | 0 | 16 ns | 315 MHz | 5.84×10⁵ |
| PolyLUT-Add | 72% | 895 | 1,649 | 0 | 0 | 4 ns | 750 MHz | 3,580 |
| DWN | 73.7% | 134 | 106 | 0 | 0 | 3.7 ns | 1,361 MHz | 496 |
| DWN | **76.3%** | 6,302 | 4,128 | 0 | 0 | 14.4 ns | 695 MHz | 90,749 |

`*` **Flagged discrepancy:** this row (12,436 LUT / 773 FF / 5 ns / 646 MHz) is PolyLUT's own JSC-M-Lite operating point, which **PolyLUT's own Table IV and NeuraLUT's own Table III both report at 72% accuracy, not 75%.** AmigoLUT's Table 4 appears to have a transcription error here; **trust 72%** (see PolyLUT/NeuraLUT briefs).

All resource/latency/F_max numbers above cross-checked against PolyLUT's, NeuraLUT's, and NeuraLUT-Assemble's own independently-published tables (this session) — they agree on every field except the flagged accuracy cell.

All of MNIST, JSC, and HGCal ensembling results, plus diversity-metric analysis (Disagreement/Error/DER, Tables 1–2), are in the primary PDF; HGCal is a CMS-specific autoencoder-compression regression task (EMD metric), not a classification accuracy, and not further detailed here since it's off-topic for jet tagging.

## Verdict
**OCCUPIES / lab-internal adjacent.** This is the most institutionally proximate paper in the whole survey — co-authored by Javier Duarte (whose hls4ml/JSC task and lab lineage underlies this entire family, and who is a standing collaborator in the CMS-ML/BNJetTag ecosystem) and Ryan Kastner, both UCSD. It should be **quoted and positioned respectfully and precisely** in any design document: AmigoLUT is explicitly an ensembling *wrapper*, not a new base architecture, and its own text is candid that it does not beat PolyLUT-Add/DWN on peak accuracy-per-LUT — its contribution is throughput/F_max and low-accuracy-regime LUT scaling. **ORTHOGONAL** to "compile a given trained transformer": it ensembles multiple independently-co-trained small MLP-family LUT-native models; there is no attention/sequence capability anywhere in it or its base models, and no mechanism to ingest an externally-pretrained checkpoint of any kind, let alone ours.

## Citation
```bibtex
@inproceedings{weng2025amigolut,
  author    = {Weng, Olivia and Andronic, Marta and Zuberi, Danial and Chen, Jiaqing and Geniesse, Caleb and Constantinides, George A. and Tran, Nhan and Fraser, Nicholas J. and Duarte, Javier Mauricio and Kastner, Ryan},
  title     = {Greater than the Sum of its {LUTs}: Scaling Up {LUT}-based Neural Networks with {AmigoLUT}},
  booktitle = {Proceedings of the 2025 ACM/SIGDA International Symposium on Field Programmable Gate Arrays (FPGA '25)},
  pages     = {25--35}, year = {2025},
  doi       = {10.1145/3706628.3708874}
}
```
