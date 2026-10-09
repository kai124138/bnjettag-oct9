# R14 n8 device-fit ladder — Vivado out-of-context synthesis (numbers of record)

**Written 2026-08-23 (Job Gamma), from the Job Alpha (2026-08-14 → 19) and Job Beta
(2026-08-19 → 23) measurements. STATUS: VERIFIED 2026-08-23 by the numbers-gate pass (every
cell re-derived from the raw reports named in §Provenance by an independent results-analyst
agent; two defects it found — the row-2 Logic/Memory split and the missing row-4 post-synth
WNS — are corrected below; the single non-re-derivable cell is the 8,229 DSP demand of row 1,
held in a mulder log; row 9 — the W8A8 baseline, added 2026-08-25 — verified the same day by an independent re-derivation pass, zero mismatches). Quotable with the caveats in §2.**

Model: `r14-l1x3-n8` W1A8 seed 3, export v5 (β in-graph, fx8), io_parallel; Vitis HLS 2023.2
C-synthesis on mulder (target `xcvu13p-flga2577-2-e`, 2.5 ns); Vivado 2023.2
`synth_design -mode out_of_context -top myproject`, **part xczu7ev-ffvc1156-2-e** (the project's synthesis
flow of record, agreed 2026-08-23; no VU13P licence or place-and-route planned), `read_xdc` (2.5 ns) **before** synthesis (timing-driven) and
`opt_design` afterwards unless stated; reports `report_utilization` / `report_timing_summary`
at both stages. **All numbers pre-place-and-route. Percentages are against the VU13P's
1,728,000 CLB LUTs. "DSP used / demanded" = utilisation-report count (capped at the part's
1,728) / `[Synth 8-3323]` demand in the synthesis log (absent ⇒ 0).** A csynth LUT, a
post-synthesis count and a post-`opt_design` count are three different quantities.

## 1. The ladder

| # | Build | Schedule | csynth LUT | csynth DSP | post-synth CLB LUT | post-opt CLB LUT (Logic + Memory) | % VU13P (post-opt) | DSP used / demanded | WNS post-synth / post-opt (ns @ 2.5) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | RF=1 fx8, DSP-carrying — **non-timing-driven** (clock applied after synth; no opt_design) | II=1, 164 cyc | 3,178,720 | 4,133 | 1,869,030 | — | 108.2% (post-synth) | 1,728 / 8,229 | +0.164 (post-hoc STA) / — | DSP-assisted; not a thesis point |
| 2 | RF=1 + solution-wide `config_op mul -impl fabric` (v2 recipe) | II=1, 146 cyc | 4,376,222 | 0 | 2,110,894 | **2,108,743** (2,051,098 + 57,645) | **122.0%** | **0 / 0** | −0.145 / −0.967 | zero-DSP; misses by 380,743 |
| 3 | folded pf1 + solution-wide fabric (`pf1fab`) | II=47, 329 cyc | 4,216,272 | 0 | 1,972,616 (1,865,737 + 106,879) | **1,948,063** (1,848,312 + 99,751) | **112.7%** | **0 / 0** | −1.982 / −1.922 | zero-DSP; misses by 220,063 |
| 4 | folded pf1 + *scoped* `BIND_OP` fabric on normalize + softmax_stable (`pf1scoped`) | II=47, 330 cyc | 3,963,344 | 0 | 1,831,219 (1,717,940 + 113,279) | 1,797,874 (1,692,579 + 105,295) | 104.0% | **1,728 / 4,096** | −2.132 / −2.076 | resource swap, NOT zero-DSP |
| 5 | row 4 + ctx-einsum softmax operand `ap_ufixed<4,0>` (`beta1sm4i0`, **characterization build**) | II=48, 333 cyc | 3,836,416 | 0 | 1,719,096 (1,605,433 + 113,663) | **1,694,625** (1,588,946 + 105,679) | **98.1%** | **0 / 0** | −1.994 / −1.943 | zero-DSP; fits by 33,375 (structure-only) |
| 6 | row 5 RTL, **constraint 5.000 ns** (eased-clock run; separate timing-driven netlist, not a replacement for row 5) | II=48, 333 cyc (240 ns/jet, 1.67 µs at 5 ns) | 3,836,416 | 0 | 1,606,905 (1,493,242 + 113,663) | **1,583,181** (1,477,502 + 105,679) | **91.6%** | **0 / 0** | **+0.506 / +0.557 @ 5.0 ns** | zero-DSP; **timing MET** (0 failing endpoints) |
| 7 | **TRAINED 4-bit arm** `r15-gamma-sm4i0` s3, folded + scoped binding (`runs/ba72a91a/w1a8-s3-r15gamma-sm4i0-pf1scoped/`) — ROC-test AUC 0.8701 ± 0.0020 attached | II=48, 333 cyc | 3,837,485 | 0 | 1,713,850 (1,600,638 + 113,212) | **1,689,320** (1,584,300 + 105,020) | **97.8%** | **0 / 0** | −1.904 / −1.853 | **zero-DSP OPERATING point; FITS by 38,680** |
| 8 | row 7 RTL, **constraint 5.000 ns** (separate timing-driven netlist; not a replacement for row 7) | II=48, 333 cyc (240 ns/jet, 1.67 µs at 5 ns) | 3,837,485 | 0 | 1,607,548 (1,494,336 + 113,212) | **1,583,565** (1,478,545 + 105,020) | **91.6%** | **0 / 0** | **+0.596 / +0.647 @ 5.0 ns** | zero-DSP; **timing MET** (0 failing EP) |
| 9 | **W8A8 BASELINE** — the same n8 architecture exported at conventional 8-bit precision (RF=1; a different network — see rule 6) | II=1, 148 cyc | 6,419,238 | 1,384 | 2,566,809 (2,503,488 + 63,321) | **2,525,842** (2,465,368 + 60,474) | **146.2%** | 1,721 / **5,550** | +0.059 / −1.086 | vanilla baseline; over budget at 1.50× row 7's LUTs, 5,550 DSPs demanded |

Registers post-opt: row 2 1,165,808; row 3 1,230,854; row 4 1,192,800; row 5 1,179,418; row 6 1,179,418; rows 7–8 1,175,192. Row 9 (W8A8): 1,702,754. Row 7's provenance: `runs/ba72a91a/w1a8-s3-r15gamma-sm4i0-pf1scoped/{csynth_pf1scoped,postsyn_xczu7ev}/`; its accuracy: `roc-results/r15-gamma/sm4i0/`. Rows 6–8 re-derived cell-for-cell from the stored reports 2026-08-25 — all cells match.
Ratios post-opt / csynth: row 2 0.482; row 3 0.462; row 5 0.442 (row 1: 0.588 post-synth, inflated by
6,501 fabric-mapped DSP sites). Timing-driven synthesis alone: row 2 post-synth 2,110,894 vs
2,011,660 for the non-timing-driven v1 run of the same RTL (+99,234). `opt_design` recovered
0.10% (row 2), 1.24% (row 3), 1.82% (row 4), 1.42% (row 5).

## 2. Reading rules

1. **Rows 2 and 3 are the zero-DSP points at the trained grids; both miss.** Row 1 is the
   DSP-assisted reference and is never a thesis point. Row 4 is not zero-DSP at the netlist
   (Vivado re-infers the 10-bit × 8-bit attention-context products as DSP48E2s — the log line
   reads `Resources of type DSP have been overutilized. Used = 4096, Available = 1728`); its LUT
   figure is a resource swap and is tabulated only to document the lesson.
2. **Row 5 fits the LUT budget at zero DSP but is structure-only**: the 4-bit softmax grid was
   forced on the export (`convert_final.py --force-softmax-out-bits 4`), the C-simulation is
   deliberately not bit-exact to the trained network, and no accuracy attaches. The trained
   counterpart (`r15-gamma-sm4i0-n8-w1a8`, 3 seeds) is in training as of 2026-08-23.
3. **Part and stage caveats apply to every Vivado cell**: xczu7ev, out-of-context, pre-route;
   LUT-as-Memory exceeds the part's 101,760 LUTRAM sites on rows 4–5 at both stages and on
   row 3 at post-synth only (99,751 post-opt) — SRL shift registers from the dataflow schedule;
   BRAM ≈7% used — not a gap discount, not a VU13P concern. The row-5
   margin (1.9%) is within what place-and-route or the target part could move either way.
4. **Clock.** At the 2.5 ns constraint no zero-DSP row meets timing (row 1's +0.164 is post-hoc
   static timing on an unconstrained-synthesis netlist). **Row 6 — the row-5 RTL constrained at
   5.000 ns — meets timing pre-route (post-opt WNS +0.557 ns, 0 failing endpoints) at 0 DSP and
   91.6% of the VU13P LUTs**: one jet every 48 cycles = 240 ns, 333-cycle latency = 1.67 µs at
   5 ns. Rows 5 and 6 are different timing-driven netlists of the same RTL and are both kept.
5. Never quote a csynth LUT as silicon; never pool the ratios.
6. **Row 9 is a different network**: the same architecture exported at conventional W8A8
   precision (C-sim ≥0.997 but not bit-exact; AUC-neutral), included as the vanilla baseline.
   The schedule-matched comparator is row 2 (both II=1): +19.8% LUT plus a 5,550-vs-0 DSP
   demand. Against the shipped operating point (row 7, II=48 — a different schedule) it is
   1.50× the LUTs while demanding 3.2× the OOC part's DSP sites. Its post-synth WNS meets
   2.5 ns where the binary rows do not — 1,721 pipelined DSP48E2s carry the arithmetic; not a
   like-for-like timing comparison.

## 3. Provenance

- Row 1: `results/synthesis/runs/38a20c62/w1a8-s3-r14n8/postsyn_xczu7ev/` (`post_synth_util.rpt`
  l.35 CLB LUTs 1869030; l.93 DSPs 1728; `post_synth_timing.rpt` WNS 0.164); csynth
  `…/csynth_rf1/csynth_report.json`; DSP demand 8,229 from mulder `vivado.log:30091` — the `[Synth 8-3323]` line and its context
  are excerpted in `…/postsyn_xczu7ev/vivado_log_excerpt_dsp_demand.txt` (fetched 2026-08-23;
  full log on mulder), also transcribed in the experiment log (2026-08-15 verification item D.1).
- Row 2: `…/w1a8-s3-r14n8/postsyn_xczu7ev_fabric_v2/{post_synth_util,post_opt_util,post_synth_timing,post_opt_timing}.rpt`;
  v1 non-timing-driven 2,011,660 in `…/postsyn_xczu7ev_fabric/post_synth_util.rpt`; csynth
  `…/csynth_rf1_fabric/csynth_report.json`.
- Row 3: `…/w1a8-s3-r14n8-pf1fab/{csynth_pf1fab/csynth_report.json,postsyn_xczu7ev/*.rpt}`.
- Row 4: `…/w1a8-s3-r14n8-pf1scoped/{csynth_pf1scoped/{csynth_report.json,myproject_csynth.rpt},postsyn_xczu7ev/{*.rpt,vivado_run.log:81820}}`.
- Row 5: `…/w1a8-s3-r14n8-beta1sm4i0/{csynth_beta1sm4i0/{csynth_report.json,myproject_csynth.rpt,defines.h},postsyn_xczu7ev/*.rpt}`.
- Row 6: `…/w1a8-s3-r14n8-beta1sm4i0/postsyn_xczu7ev_5ns/{post_synth_util,post_synth_timing,post_opt_util,post_opt_timing}.rpt` (+ `clock.xdc` 5.000 ns, `synth_ooc.tcl`, `vivado_run.log`, `rss_sampler.log`); harvested 2026-08-23; re-derived cell-for-cell from the stored reports 2026-08-25 (rows 6–8 pass, incl. Logic+Memory closure and zero `[Synth 8-3323]` lines).
- Row 9: `results/synthesis/runs/9cc6e336/w8a8-s3-r14n8/{csynth_rf1/csynth_report.json,postsyn_xczu7ev/*.rpt}`;
  DSP demand 5,550 = the `[Synth 8-3323]` line at `vivado_run.log:17955`, excerpted in
  `…/postsyn_xczu7ev/vivado_log_excerpt_dsp_demand.txt` (harvested 2026-08-25; full log
  git-ignored per the store manifest, copy on mulder).
- Per-family attribution and single-lever checks: `code/hgq2/parse_families.py --diff`;
  narrative `.claude/memory/experiment-log.md` 2026-08-14 … 2026-08-23; frozen report
  `docs/reports/job-alpha-fit-campaign-2026-08-17.pdf` (Addenda 1–3).

## Verification

- [x] results-analyst pass, 2026-08-23 (numbers-gate workflow, independent agent; see
  experiment log 2026-08-23 "RESEARCH.md numbers gate"): all LUT / % / DSP / WNS / register
  cells of §1 re-derived from the stored `post_{synth,opt}_{util,timing}.rpt`, `csynth_report.json`
  and `vivado_run.log`; corrections applied: row 2 post-opt split 2,052,237 + 56,506 →
  **2,051,098 + 57,645** (the former was the post-synth Logic count), row 4 post-synth WNS
  **−2.132** added, opt_design recovery for row 4 (1.82%) added, reading rule 3 narrowed to the
  rows where LUT-as-Memory actually exceeds the part. Row 1's 8,229 DSP demand: log excerpt fetched into the store 2026-08-23.
- [x] Row 9 (W8A8 baseline, added 2026-08-25): every cell and rule-6 ratio re-derived from the
  raw stored reports by an independent audit pass the same day (36 checks, zero mismatches;
  family attribution re-derived via `parse_families.py` with DSP closure 872+512 = 1,384 /
  3,621+512 = 4,133; cross-doc sweep findings — all wording, no numbers — fixed and logged).
