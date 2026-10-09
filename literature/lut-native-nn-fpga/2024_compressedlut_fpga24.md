# CompressedLUT: An Open Source Tool for Lossless Compression of Lookup Tables for Function Evaluation and Beyond

- **Authors:** Alireza Khataei, Kia Bazargan — University of Minnesota. **Not Kumm et al.** — the task brief's speculative attribution is incorrect; corrected here. (Note: Martin Kumm is a real, separate FPGA-arithmetic researcher (multiplierless constant-coefficient design, adder graphs) whose work is topically adjacent — e.g. cited inside da4ml/BOPs-adjacent literature we already track — but he is not an author of CompressedLUT.)
- **Venue / Year:** FPGA 2024 (ACM/SIGDA Int'l Symp. on Field Programmable Gate Arrays), March 3–5, 2024, Monterey, CA, doi: 10.1145/3626202.3637575.
- **No arXiv preprint found** this session — ACM DL (https://dl.acm.org/doi/10.1145/3626202.3637575), NSF PAR mirror (https://par.nsf.gov/servlets/purl/10533915), GitHub (https://github.com/kiabuzz/CompressedLUT). Same authors as TreeLUT (University of Minnesota, Bazargan's group).
- **Topic area:** LUT compression primitive — **not a competing neural-network method**, per task scope ("relevant as a primitive, not a competitor").

## TL;DR
A lossless compression scheme for arbitrary constant lookup tables (used for univariate function evaluation generally, e.g. trig/transcendental functions, not specifically neural-network weights) — combines table decomposition, self-similarity detection, higher-bit compression, and multilevel compression, decoded at runtime via addition + arithmetic shift + a few small auxiliary tables. Reports **~60% average table-size compression** and **2.33× higher throughput per slice** vs. conventional (uncompressed) table implementations, beating prior compression schemes TwoTable (~33%) and LDTC (~37%).

## (a) Mechanism
A **post-hoc table-compression algorithm**, not a training method: given any already-computed constant lookup table (from any source — could in principle be applied to an enumerated LUT-native-NN truth table, a GBDT's leaf-value table, or an unrelated math-function table), it finds structure (self-similar sub-blocks, redundant bit patterns) and re-encodes it into a smaller circuit that reconstructs the original values on the fly. This makes it a **primitive that composes with** (rather than competes against) LogicNets/PolyLUT/NeuraLUT/TreeLUT-style methods — it operates one level below "how do you decide what the table contains" and addresses only "how small can the table's hardware footprint be once decided." Directly acknowledged as exactly this kind of composable primitive by NeuraLUT-Assemble's own related-work section (grouping it, together with ReducedLUT, under "post-training hardware optimization" techniques that are "complementary" to network-architecture-level LUT methods).

## (b) What it explicitly does NOT do
- Does not train or design a neural network of any kind, and has no notion of accuracy, fan-in, or model architecture — it is dataset/domain-agnostic table compression.
- No attention/matmul/sequence relevance (not applicable — it's a hardware-encoding technique for constant data, not a model family).
- Not itself evaluated on JSC or any jet-tagging benchmark — it is a generic building block, not benchmarked against classification tasks in the same sense as the other 7 systems in this survey.

## (c) Exact published jet-tagging numbers
**Not applicable / none published** — CompressedLUT is not a classifier and reports no accuracy numbers on any physics dataset.

## Verdict
**ORTHOGONAL**, exactly as scoped by the task — a compression primitive that could in principle be layered onto any of the truth-table-based methods above (including, hypothetically, a future binary-native LUT compiler for BNJetTag, if one were built) to shrink whatever tables it produces, but it says nothing by itself about whether attention/transformers can be compiled to LUT logic, and it does not compete with or occupy the "compile a given trained network" space.

## Citation
```bibtex
@inproceedings{khataei2024compressedlut,
  author    = {Khataei, Alireza and Bazargan, Kia},
  title     = {{CompressedLUT}: An Open Source Tool for Lossless Compression of Lookup Tables for Function Evaluation and Beyond},
  booktitle = {Proceedings of the 2024 ACM/SIGDA International Symposium on Field Programmable Gate Arrays (FPGA '24)},
  year      = {2024},
  doi       = {10.1145/3626202.3637575}
}
```
