# R14 hardware — v5-export silicon (numbers of record)

Written 2026-08-07. Whole-model Vitis HLS 2023.2 C-synthesis on mulder, part
`xcvu13p-flga2577-2-e` (VU13P), target clock 2.5 ns, io_parallel, **Latency strategy,
RF=1** — the max-parallelism reference point (min cycles, LUT above device is expected;
device fit is the standing folding workstream, RESEARCH.md §2). Model:
`r14-l1x3-n8` W1A8 seed 3 (checkpoint `roc-results/r14/n8/_ckpt_dl/w1a8-s3/`),
**export v5** (in-graph β restoration, fx8 β encoding; GATE1 0.998816 / argmax 0.9800,
GATE2 bit-exact; selection rule + policy: decisions.md 2026-08-04; export EBOPs
3,025,884 — never mix with `ebops_r14.json`, which reports 1,739,182 for this same
model: both are trace_minmax, but the export graph adds the 15 β-restore affines
(+1,280,302) and input_proj bias-table bookkeeping (+6,400); the reconciliation is
exact).

## n8 whole model — two measured operating points

| metric | fx8 (DSP mults) | fx8 + `config_op mul -impl fabric` | VU13P total |
| --- | --- | --- | --- |
| estimated clock | 1.825 ns (no timing flags) | 2.287 ns — 18 Vitis Timing-Violation flags, see note | — |
| latency | 164 cyc = 299 ns (est) / 410 ns (target) | 146 cyc = 334 ns (est) / 365 ns (target) | — |
| initiation interval | 1 | 1 | — |
| **DSP** | 4,133 (33.6 %) | **0 (0 %) — zero in all 106 instances and every expression row** | 12,288 |
| LUT | 3,178,720 (184.0 %) | 4,376,222 (253.3 %) | 1,728,000 |
| FF | 1,704,976 (49.3 %) | 1,444,585 (41.8 %) | 3,456,000 |
| BRAM_18K | 512 (9.5 %) | 512 (9.5 %) | 5,376 |
| URAM | 0 | 0 | 1,280 |

**DSP attribution (fx8 point, instance table of `myproject_csynth.rpt`, 106 instances;
sums exactly to the 4,133 total):** every binary matmul (`einsum_dense` ×13 —
input_proj, Wq/Wk/Wv/Wo, fc1, fc2 — and both head `dense_latency` QDenses) = **0 DSP**;
all four act×act attention einsum instances (QKᵀ and attn·V, 2 per block) = **0 DSP**;
`normalize` (the 15 v5 β-restore affines, fx8 γ constants) = 3,621; `softmax_stable` =
512 (64 instances × 8). The fabric-mul point moves those 4,133 constant/table
multiplies into LUT fabric (measured trade: +1.20M LUT, −0.26M FF, −18 cycles) — the
first whole-model synthesis of this stack with zero DSPs anywhere. (Context, NOT
like-for-like: the FINAL-campaign *large*-model attention-core probe at RF=64/II=64
used 820 DSP on its own — `results/synthesis/hls_resource_table_final.md`.)

**Timing note (fabric point).** The estimated 2.287 ns is under the 2.5 ns target, but
Vitis flags 18 `Timing Violation` entries — the top module plus exactly the 16
fabric-ized multiply module classes (14 `normalize`, 2 `softmax`): the estimated
period exceeds the 2.5 − 0.68 ns clock-uncertainty budget. The fx8 point carries no
flags. Cycles (146) and II (1) are unaffected; quote the fabric-point ns figures with
this caveat until a post-route or eased-clock check. Evidence: `SummaryOfViolations`
blocks in `csynth_rf1_fabric/csynth.xml`; the modification itself is durable at
`csynth_rf1_fabric/build_prj.tcl:153` (`config_op mul -impl fabric`) + `build_opt.tcl`.

## The W8A8 baseline (added 2026-08-25)

The same n8 graph at conventional 8-bit precision (`r14-l1x3-n8-w8a8` s3; export = the trained
HGQ2 graph, GATE1 exact, C-sim ≥0.997 but not bit-exact — AUC-neutral; store
`runs/9cc6e336/w8a8-s3-r14n8/`), RF=1/Latency, same part and clock, C-synthesis: **LUT 6,419,238
(371.5%) / FF 2,307,117 / DSP 1,384 / BRAM_18K 512 / 148 cyc / II 1 / est 1.825 ns**. Weight
matmuls: 5,013,220 LUT + 872 DSP (vs 1,630,567 + 0 binary). Vivado OOC
(xczu7ev, 2.5 ns, harvested 2026-08-25): post-opt **2,525,842 CLB LUT (146.2% of the VU13P) /
1,702,754 registers / DSP used 1,721, demand 5,550** (`[Synth 8-3323]`) — vs demand **0** for
every binary zero-DSP build; fit-ladder row 9 (`hls_r14_fit.md`); store
`runs/9cc6e336/w8a8-s3-r14n8/postsyn_xczu7ev/`.

## Not synthesized

- **n16** (`r14-l1x3-n16` w1a8-s1): export gates PASSED (GATE1 0.997384 / argmax
  0.9763, GATE2 bit-exact, export EBOPs 7,351,926) but the rf1 Latency csynth died
  after 17.7 h wall with no report (killed/OOM; the known big-Latency-design
  pathology — constraints_map.md). No n16 resource/latency number exists; levers:
  per-layer RF maps / Resource-mode routes (fit workstream).
- n32 / n64: not attempted (exports expected worse; out of probe scope).

## Provenance

Raw reports: `results/synthesis/runs/38a20c62/w1a8-s3-r14n8/csynth_rf1/` (fx8) and
`csynth_rf1_fabric/` (fabric-mul) — `csynth.xml`, `myproject_csynth.rpt`,
`csynth_report.json` (the same XMLs live in the W&B `synthesis-*` artifacts under
their run names).
Export gates: `.../export_verify.json` (incl. the full β-encoding `gate1_ladder`),
`csim_verify.json`; pre-v5 state preserved as `*.pre-v5-2026-08-04.json`.
n16 export gates: `results/synthesis/runs/2ae656b6/w1a8-s1-r14n16/`. Mulder work dirs:
`~/bnjet_r14/`. W&B: `synthesis-r14n8_w1a8s3_fx8_rf1{,_fabricmul}` artifacts +
job_type=hls runs, project `BNJetTagAug`, lineage `wandb_run: r14-l1x3-n8-w1a8-s3`.
Normed-guard regression: the FINAL-campaign *large* `final-w1a8-s1` (subln) rebuilt
under v5 → gate outputs float-identical to its stored 2026-07-08 record (score corr
0.974917488, argmax 0.897705) — `regress_normed_v5_final-w1a8-s1.log` (scoped to the
gate outputs; the variable-count difference vs the July record — 6,946,535 vs
6,380,717 — is reproduced bit-for-bit by pre-v5 code at fe173ed, i.e. predates v5).
Independent verification (results-analyst, 2026-08-07): every cell of this table
re-derived from the raw XML/rpt/JSON — `verification_hls_r14_2026-08-07.txt`.
