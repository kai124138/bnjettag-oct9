---
title: Figures
status: current
date: 2026-09-26
---

# Figures

Applies whenever a figure or schematic is made. The kit is `docs/style/`; the check is
`tools/plot_check.py`; the picks are in `docs/style/CHOICES.md`.

- Plots of measured numbers: matplotlib with `docs/style/bnjettag.mplstyle` (journal pick,
  2026-09-26). No axes title; the caption carries the message. Save `.png` and `.svg` with
  `bbox_inches="tight"`, close the figure. Font sizes come from the style, not the call.
- Every label names the metric and the split ("Held-out macro one-vs-rest AUC"). Every
  figure has a provenance caption: seeds, n, error-bar definition, source file.
- ROC curves: tagging efficiency on x, mistag rate on a log y axis (HEP convention).
- Colours follow the entity, in fixed order: FP32, W8A8, W1A8, W1A6, W1A4 as in the style's
  cycle. A ninth series folds into small multiples, never a new hue.
- One axis per panel; two measures of different scale are two panels.
- Schematics (architecture, pipeline, FPGA mapping) are TikZ: `docs/figures/<name>.tex`
  with `\input{../style/bnjettag.tikzstyles.tex}`, rendered by `docs/figures/render.sh`.
  Every arrow that carries data is labelled with its shape. Facts drawn (layer counts, bit
  widths, N) come from the config, not memory.
- Poster or talk: the C variant of the style (`docs/figures/style/bnjettag-c-poster.mplstyle`)
  is the alternate; it is a pick, not a default.
- Read the rendered PNG before calling a figure done; the checker reads code, not pictures.

Pitfall: the publication tree's `publication/code/analysis/build_figures.py` predates the kit (titles, inline
rcParams, mistag on log x); it fails `plot_check` and is a REPORT-phase fix, not a rule.
