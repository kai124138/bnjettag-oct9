---
id: 2026-09-26-delta
date: 2026-09-26
type: delta
status: designed
question: Which of about 100 binarization, recipe, activation-width/EBOPs, architecture and input methods, alone or in pre-registered combinations, change the validation accuracy or 350k feasibility of the binary-weight N=64 tagger relative to the Sun et al. recipe anchor at the same seed, and which of those survive a full-recipe 8-seed confirmation?
supersedes:
superseded_by:
code_sha: not fixed. Delta patches are staged against the screen bundle (tarball sha256 26f3cc40...5a45) and rebased onto the anchor patch series sha once it lands; ml-engineer records both in code/
wandb: BNJetTag-Delta / delta-20260926-w2 (singles), delta-20260926-w3 (combos), delta-20260926-w4 (confirm); proposed, never BNJetTagAug
results:
---

# Delta (index pointer, not a STUDY)

This campaign is a pre-registered queue of 103 entries, not one experiment, so it has no single
question, null or falsifier here. The design is `DELTA.md` (machine-readable copy `delta.json`);
each wave becomes its own campaign with its own STUDY.md through `/new-experiment`, reviewed by the
panel before any launch. This file exists so `tools/index.py` lists the campaign; its header is
copied from `DELTA.md`, which wins if the two differ.
