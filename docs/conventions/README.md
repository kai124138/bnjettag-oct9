---
title: Conventions
status: current
date: 2026-09-26
---

# Conventions

What an experienced analyst on this project knows and a general model cannot infer: how the
metrics are defined and labelled, how quantized cost is accounted, what a synthesis number
means, how a figure is drawn. The methodology says *that* a claim needs a matched baseline
and an interval; a convention says *which* baseline and *which* interval. (JFC's
"conventions over encoded physics".)

| file | applies when |
| --- | --- |
| `jet-tagging-metrics.md` | any number about tagging performance is computed, compared or quoted |
| `quantization-and-cost.md` | any arm is quantized, budgeted by eBOPs, or selected under a cap |
| `fpga-synthesis.md` | any model goes through hls4ml to Vitis, or a resource / latency number is stated |
| `figures.md` | any figure or schematic is made |

Each file: when it applies, standard configuration, required validation checks, required
comparisons, known pitfalls (each with the incident that taught it).

Consulted at STUDY (the compliance table), VERIFY (the checks) and REPORT (the final sweep).
Agent-maintained: when a campaign teaches something, the agent adds it with the date and the
campaign id; Kai reviews before it is treated as settled. Every number in these files carries
its source path; none is quotable without recomputation.
