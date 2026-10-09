# BRIEF — 2026-09-26-delta (orchestrator → every agent in this campaign)

Written by the orchestrator, 2026-09-26. Every agent in this campaign reads this file first.

## What Kai asked for (2026-09-26, 23:5x)

"Use Chang's method" (the Sun et al. recipe, arXiv:2510.24784, code
`reference-code/HGQ2-examples/jsc150/`), combined with: a design for future work in which agents
do deep research on the theory and ideas for how to move forward, and **code ready to run for all
of them, close to 100 methods, including combinations**. For now: the theory and ideas part, and
the code ready. **No launch in this campaign** (no `kubectl apply`, no cluster jobs). The
earlier voice note asking to launch 40-60 Chang-recipe runs is reference for the recipe only;
that launch belongs to `campaigns/2026-09-26-training-batch/` (wave 0 here), which is at STUDY
review v2 = ITERATE.

The recipe, as Kai described it: N = 64 constituents, 7,000 epochs, batch 2,790, LR 3e-3 with
cosine restarts every 500 epochs, the pT ≥ 2 GeV constituent gate, no class/sample weights,
EBOPs target enforced (350k in their paper); some runs at a lower EBOPs limit, some "the way
it's implemented" in our code, some with a changed architecture. Our binary `{−1,+1}` weights.

## The anchor (wave 0)

`campaigns/2026-09-26-training-batch/STUDY.md` (7 arms × 8 seeds = 56 runs, A07-N64: d32/h4/L1/
FFN32, learned PE, binary_absmean, learned activation widths from 8-bit init, BetaPID, 90/10
split, validation-only selection) and its review `review/STUDY_arbiter_v2.md`. Every method in
Delta is a delta from arm A of that study ("the anchor") unless its card says otherwise, and
is paired to the anchor at the same seed where shapes allow.

**Anchor amendment, 2026-09-27 (Kai-confirmed [D19] and [D21], `decisions.md` 2026-09-27 08:40
PDT; supersedes the arm description above).** Arm A = E at 350k under [D21] (Kai-confirmed
2026-09-27): d24, 2 heads, 1 block, FFN 32, no PE. A07 at 350k is the descriptive arm A07-350;
C is A07 at 5M. B is E at 250k, D and R run on E, and F is E + learned PE. Every arm uses
**Chang's quantizers** [D19] (WRAP datalane activations and Q/K/V streams, 0 bits reachable;
learned softmax output; softmax exp/inv tables kbi SAT_SYM, trainable, ≥ 4 bits), not the SAT
k=1 / fixed-10-bit-softmax quantizer, whose A07 floor is 4,580,398 EBOPs (CPU trace). **CPU trace
(2026-09-27, synthetic input, staged in `campaigns/2026-09-26-training-batch/code/`, committed at
72a1290, not the final anchor sha; not results):** the softmax exp input stays SAT, adding
16,384 (A07) and 8,192 (E) to the arbiter's 326,656 and 163,328, plus a LUT term of 13 and 6,
so the traced 0-bit floors are A07 343,053 and E 171,526; with 1 bit alive, 1,005,741 and
619,198. A07 at 350k therefore keeps at most 6,947 EBOPs outside its floor, below the 8,192 that
data-dependent attention needs, which is why it is descriptive only. The Delta anchor is **arm
A (E at 350k)**: every Delta 350k accuracy cell and FF2 pair with arm A, the floor family builds
on A07-350 and reads its feasibility against it, and every 5M cell pairs with C (`DELTA.md` §0,
§3.3). The anchor study's selection rule now requires a non-degenerate checkpoint (traced EBOPs
≤ target, EBOPs above the 0-bit floor, validation accuracy > p_maj + 5·SE), and Delta
inherits it (`DELTA.md` §5.1). Its second wave adds arm H (Chang's jsc150 xfm-n64 on our split)
and arm NB (learned-width weights on the arm-A recipe); NB covers Delta M049's 350k cell. If arm
A has no feasible checkpoint (pilot rule at epoch 500, or production), the anchor becomes the
arm Kai names; C at 5M is the remaining fallback.

## What this campaign produces

```
campaigns/2026-09-26-delta/
  BRIEF.md                   this file
  plan.md                    orchestrator notebook
  inventory/code-surface.md  ml-engineer: every config knob in each code state; what exists
  inventory/tried-already.md every method already tried, with outcome and mechanism
  research/<family>.md       physics-researcher: method cards, one family per file
  DELTA.md                   experiment-designer: the catalogue (~100 entries), tiers, waves,
                             combos, budget, pre-registration rules for the per-wave STUDYs
  code/                      ml-engineer: generator, patch set, generated configs, gate report
```

## Method-card schema (research/<family>.md)

One card per method, headed `### <family-letter><nn> — <short name>`:

- **Mechanism.** What changes in the forward or backward pass, or the training loop, in two to
  five sentences.
- **Why it could matter for binary weights here.** Specific to a ±1-weight, norm-free, small
  transformer on 3-feature jet constituents under an EBOPs budget. If there is no binary-specific
  reason, say so.
- **Primary source.** Authors, title, arXiv id or venue, year, URL. Date accessed.
- **Published effect.** Quote the number with its metric, dataset, model and table/figure, or
  write "no prior number". Never an expected gain from memory.
- **Knob or code change.** The config field(s) and values if one exists; otherwise the smallest
  code change, the file it touches, and a size estimate (lines).
- **Hazards.** What it does to HLS conversion, EBOPs accounting, DSP use (the 0-DSP headline),
  latency, or the binary constraint (a layer with more than two weight values breaks the thesis).
- **Tried here?** Leave for the tried-already inventory unless you know from a file; cite it.
- **Combines with.** Other cards it is expected to interact with, and why.

## Rules (from CLAUDE.md; they bind every agent here)

- Never invent a number. Every number carries metric, split, n, status, and a source file or URL.
- Binary is the thesis; ternary or multi-bit weights appear only as labelled baselines.
- Nothing heavy on the laptop: CPU build/reload gates only, no training beyond a few steps.
- Do not append to the shared logs (`research-log.md`, `experiment-log.md`, `decisions.md`,
  `literature/INDEX.md`) from a parallel agent. Put the lines you would append in a final
  section of your own file, "Log lines to append"; the orchestrator appends them once.
- Do not repair, commit to, or push any git repository. `publication/` is a broken worktree
  (its gitdir points to the pre-migration path); that is a Kai decision.
- Do not enter `research/` at the repo root (a symlink into another tree) except to read a file
  a card cites.
