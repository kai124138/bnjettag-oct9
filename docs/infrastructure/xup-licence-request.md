---
title: Action: Vivado licence covering xcvu13p (Xilinx/AMD University Program)
status: current
date: 2026-09-08
---

# Action: Vivado licence covering xcvu13p (Xilinx/AMD University Program)

**Status: waiting on Kai to send the request (drafted 2026-07-26).**

## Why

The fit claim's final rung ("Level 2: device truth" in the fit-campaign plan) needs
Vivado synthesis — ideally place-and-route — on the real target, `xcvu13p-flga2577-2-e`.
The licence on mulder is device-scoped: `xcvu13p` fails with `[Common 17-345]` while
seven smaller parts synthesize (see `_attic/compiler-workstream/adder-graph/e1/POSTSYN.md`). All
post-synthesis anchors so far run on `xczu7ev` (same LUT6+CARRY8 fabric generation) and
are usable as ratios only, never as VU13P absolutes.

This matters more after 2026-07-26: the closest published system (arXiv:2510.24784,
dossier in `docs/literature/jet-tagging-transformers/`) reports post-P&R numbers, and our own
anchor shows csynth over-estimating post-synth LUT ≈2.3–2.5×. Whether the flagship fits
may literally be a question of which tool stage is allowed to answer.

## What to request

- AMD/Xilinx **University Program (XUP) donation licence** (or a CMS/UCSD group licence)
  including **Virtex UltraScale+ VU13P** support for **Vivado 2023.2** (the version on
  mulder; a newer version is fine if it can be installed alongside).
- Node-locked to mulder or floating for the group — either works; mulder is where the
  RTL and flows already live.

## Who to ask

1. The UCSD CMS group's usual Xilinx licence contact (whoever maintains the current
   mulder licence — it covers seven parts already, so a contact exists).
2. Failing that: AMD University Program directly (https://www.amd.com/en/corporate/university-program.html)
   with the research context (CMS Level-1 trigger R&D).

## Draft email

> Subject: Vivado licence extension for VU13P (CMS L1 trigger research)
>
> Hi —, I'm working on FPGA implementations of ML triggers for CMS Level-1 (jet
> tagging on Virtex UltraScale+ VU13P, the CMS L1 correlator target). The Vivado
> 2023.2 installation on our group machine has a licence covering several smaller
> parts, but `synth_design` for `xcvu13p` fails with a licence error
> (`[Common 17-345]`), so we can't produce post-synthesis resource/timing numbers on
> the actual trigger part. Could we extend the licence (or obtain an AMD University
> Program licence) to include VU13P support? Happy to provide any project details
> needed. Thanks!

## Interim fallback (already running)

Until the licence lands, the campaign uses the `xczu7ev` out-of-context anchor for
csynth→post-synth ratios (E-B, E-B2, e1diag hierarchical passes), reported as ratios
with the device caveat stated.
