---
title: FPGA synthesis
status: current
date: 2026-09-26
---

# FPGA synthesis

Applies whenever a model goes through hls4ml to Vitis, or a resource or latency number is
stated.

## Toolchain

- hls4ml export → Vitis HLS 2023.2 on `mulder` (`mulder.t2.ucsd.edu`, full `settings64.sh`),
  target `xcvu13p-flga2577-2-e` at 2.5 ns. C-synthesis needs no licence; csynth is
  single-threaded, so parallelise across configs. Source: `.claude/skills/vitis-mulder`,
  `docs/infrastructure/mulder-setup.md`.
- The parse of a csynth report into the resource table is `parse_csynth.py`; the table
  columns are LUT, FF, DSP, BRAM, II, latency (cycles and ns), Fmax.

## What a number means

- **C-synthesis estimates precede logic optimisation and place-and-route.** They are
  reported as estimates. "Implemented" means a Vivado result exists; none has been produced
  for the binary model as of 2026-09-26 (R4 attempt failed in the HLS front end, runbook
  2026-09-17).
- The **DSP = 0** claim applies to the binary weight layers. Any layer that keeps DSPs
  (softmax, normalisation, non-binary heads) is listed with its count; the claim is stated
  per layer and for the whole design separately.
- The W8A8 baseline at C-synthesis: 5,550 DSPs, 146 % of the VU13P (research commit
  66c4e50, `RESEARCH.md`); binary needed half the LUTs and zero weight-layer DSPs
  (commit ecf224b). Quote from RESEARCH.md with its section, or re-parse the report.

## Required validation checks

1. **Fidelity**: the exported fixed-point model reproduces the checkpoint on a sample
   (4,096 jets in the R4 export, bit-exact export-to-C; two changed argmax decisions vs the
   float checkpoint were recorded, not hidden).
2. Reuse factor and II stated; a latency number without its II and clock is incomplete.
3. Resource numbers come from the report JSON, never typed from memory.
4. The synthesised checkpoint is the selected one from VERIFY.md (sha recorded).

## Pitfalls, with the incident

- HLS front-end exits 1 before RTL generation; splitting interface pragmas and adding C
  linkage did not help (R4, 2026-09-17). Record the verbatim error and attempt count.
- `/` on mulder was 100 % full (2026-09-17): set `TMPDIR` under `$HOME`; `nrp_doctor mulder`
  now flags it.
- A VU13P Vivado licence probe failed while the xczu7ev probe passed: HLS on VU13P and
  Vivado on xczu7ev are different stages and are labelled separately.
