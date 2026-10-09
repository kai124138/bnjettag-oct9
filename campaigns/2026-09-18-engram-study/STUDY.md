---
id: 2026-09-18-engram-study
date: 2026-09-18
type: engram
status: unreviewed
question: Engram-inspired memory tables in the binary tagger: accuracy first under an augmented cost cap (E00–E03 pilot)
supersedes: 
superseded_by: 
code_sha: 
wandb: 
results: 
generated: auto-stub 2026-09-26 by tools/index.py init; not provenance, edit by hand
---

# Engram-inspired memory tables in the binary tagger: accuracy first under an augmented cost cap (E00–E03 pilot)

<!-- Phase artifacts live beside this file: PREFLIGHT.md, RUN.md, VERIFY.md, REPORT.md. -->
**Question.** 

**Design.** arms / seeds / selection rule / falsifier

**Result.** 
Control histories (W&B `BNJetTag-Engram-Experimental`, runs `engram-e00-s1` 10dd9f63e913 and `engram-e01-s1` a768d794fb1a, `scan_history`, saved 2026-09-26 to `control-histories-20260926.json`; validation macro AUC on the internal split, n = 124,000, single seed, not a result): both controls trained normally first, with validation macro AUC peaking near epoch 50 at 0.881 (e00) and 0.872 (e01) while native HGQ2 eBOPs were still 2.44 M and 1.32 M, so the collapse to about 0.64 at epoch 999 (`status-20260923.json`) is not a training failure that was flat from the start.
The shape is a budget squeeze: cost fell about six-fold between epochs 20 and 200 (e00 4.30 M to 0.72 M, e01 2.16 M to 0.39 M) and validation AUC fell with it, e01 slowly (0.836 at epoch 100, 0.806 at 300, 0.788 at 500, 0.737 at 700, 0.645 at 999) while its cost crept down to 0.362 M against the 350,000 target.
e00 differs: its cost stopped falling at 0.72 M by epoch 200, twice the target, yet its AUC had already collapsed to 0.68 by then and oscillated between 0.56 and 0.72 for the remaining 800 epochs with cost flat, so once the squeeze had bitten the damage did not reverse; `cost/custom_estimated_bitops` logged 0 on every epoch of both runs and is not usable.

**Interpretation.** 
