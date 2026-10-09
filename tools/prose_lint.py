#!/usr/bin/env python3
"""
prose_lint.py — catch the tells that make writing read as machine-made.

    python3 tools/prose_lint.py README.md
    python3 tools/prose_lint.py reports/*.md --strict
    python3 tools/prose_lint.py --diff              # only files changed vs main

It flags the vocabulary, rhythm, and structure that LLM prose falls into: the stock
verbs, the triads, the uniform sentence lengths, the bullet-for-everything layout, the
"it's worth noting that". None of these are wrong on their own — the signal is the
*density*. A human research write-up trips two or three of these. A generated one trips
twenty.

This is a mirror, not a judge: fix what makes the writing worse, ignore what doesn't.
Stdlib only.
"""

import argparse
import glob
import os
import re
import statistics
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# (pattern, why it reads as machine-made)
WORDS = [
    (r"\bdelve[sd]?\b", "'delve' — nobody says this"),
    (r"\bleverag(e|es|ed|ing)\b", "'leverage' — say 'use'"),
    (r"\bseamless(ly)?\b", "'seamless' — marketing register"),
    (r"\brobust\b", "'robust' — usually means nothing; say what holds"),
    (r"\bcomprehensive\b", "'comprehensive' — claim, not description"),
    (r"\bcrucial(ly)?\b|\bpivotal\b|\bvital\b", "importance-adverb; show it instead"),
    (r"\bit'?s worth noting\b|\bit is worth noting\b", "filler throat-clearing"),
    (r"\bit'?s important to (note|remember)\b", "filler throat-clearing"),
    (r"\bin conclusion\b|\bin summary\b|\bto summarize\b", "essay scaffolding"),
    (r"\b(furthermore|moreover|additionally)\b", "connector nobody uses out loud"),
    (r"\bunderscore[sd]?\b|\bhighlight[s]? the importance\b", "stock emphasis verb"),
    (r"\b(landscape|realm|domain) of\b", "'the realm of' — filler"),
    (r"\bshowcase[sd]?\b|\belevate[sd]?\b|\bunleash\b", "product-launch register"),
    (r"\bcutting[- ]edge\b|\bstate[- ]of[- ]the[- ]art\b", "hype (unless citing SOTA numbers)"),
    (r"\bgame[- ]chang(er|ing)\b|\brevolutioniz", "hype"),
    (r"\btapestry\b|\bsymphony\b|\bbeacon\b", "purple metaphor"),
    (r"\bnot only\b[^.]{0,60}\bbut also\b", "'not only… but also' — LLM cadence"),
    (r"\bnavigat(e|ing) the\b", "'navigating the …' — filler"),
    (r"\bensur(e|es|ing) that\b", "'ensure that' — often just 'so'"),
    (r"\bcan help (to )?\b", "hedge-verb padding"),
    (r"\bdive (deep )?into\b", "'dive into' — blog register"),
    (r"\bplays? a (key|vital|crucial|significant) role\b", "stock phrase"),
    (r"\ba testament to\b", "stock phrase"),
    (r"\bin today'?s\b", "listicle opener"),
    (r"\bwhen it comes to\b", "filler opener"),
    (r"\bthat being said\b|\bwith that said\b", "filler pivot"),
    (r"\bmeticulous(ly)?\b|\bintricate\b", "stock adjective"),
    (r"\bfoster(s|ing)?\b", "'foster' — corporate"),
    (r"\bembark\b", "'embark' — corporate"),
    (r"\bmyriad\b|\bplethora\b", "thesaurus word"),
    (r"\bharness(es|ing)?\b", "'harness' — say 'use'"),
    (r"\bempower(s|ing|ed)?\b", "'empower' — corporate"),
    (r"\bstreamlin(e|es|ed|ing)\b", "corporate"),
    (r"\bunparalleled\b|\bunmatched\b", "hype"),
    (r"\bjourney\b", "'journey' — unless literal"),
    (r"🚀|✨|🔥|💡|🎯|📈", "emoji in technical prose"),
]

STRUCTURE_HINTS = """
What usually fixes a high score:
  · Delete the summary paragraph that repeats what you just said.
  · Turn a bullet list back into two sentences of prose. Lists are for things that are
    genuinely parallel — steps, options, results — not for every third thought.
  · Vary sentence length on purpose. Write one that runs long and does real work, then
    a short one. Uniform 18-word sentences are the loudest tell there is.
  · Cut every adverb of importance ('crucially', 'notably', 'significantly').
  · Say the number instead of describing it as impressive.
  · Let a sentence start with 'But' or 'So'. Humans do.
"""


def sentences(text):
    text = re.sub(r"```.*?```", " ", text, flags=re.S)      # ignore code fences
    text = re.sub(r"^\s*[-*|#>].*$", " ", text, flags=re.M)  # ignore lists/headers/tables
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in parts if len(s.split()) >= 4]


def lint(path, strict=False):
    try:
        raw = open(path, encoding="utf-8", errors="replace").read()
    except OSError as exc:
        print("lint: %s" % exc)
        return 0

    lines = raw.splitlines()
    hits = []
    in_fence = False
    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for pat, why in WORDS:
            for m in re.finditer(pat, line, re.I):
                hits.append((i, m.group(0).strip(), why))

    body = [l for l in lines if l.strip() and not l.lstrip().startswith(("#", "|", "```"))]
    bullets = sum(1 for l in body if re.match(r"^\s*[-*+]\s|^\s*\d+\.\s", l))
    bullet_ratio = bullets / len(body) if body else 0

    sents = sentences(raw)
    lens = [len(s.split()) for s in sents]
    stdev = statistics.pstdev(lens) if len(lens) > 1 else 0
    mean = statistics.mean(lens) if lens else 0

    em_dashes = raw.count("—")
    per_100 = em_dashes / max(1, len(raw.split())) * 100

    # score: word hits dominate; rhythm and layout are secondary signals
    score = len(hits) * 2
    if bullet_ratio > 0.45 and len(body) > 12:
        score += 6
    if lens and stdev < 4.5 and len(lens) > 8:
        score += 6
    if per_100 > 1.2:
        score += 3

    name = os.path.relpath(path, REPO)
    verdict = ("reads human" if score <= 4 else
               "a few tells" if score <= 12 else
               "reads machine-made" if score <= 30 else "reads very machine-made")
    print("\n%s  —  score %d, %s" % (name, score, verdict))
    print("  %d words · %d sentences · mean %.0f words (σ=%.1f) · %.0f%% bullets · %d em-dashes"
          % (len(raw.split()), len(sents), mean, stdev, bullet_ratio * 100, em_dashes))

    if hits:
        print("  ── phrases ──")
        shown = hits if strict else hits[:20]
        for ln, txt, why in shown:
            print("  %5d  %-22s %s" % (ln, txt[:22], why))
        if len(hits) > len(shown):
            print("  %5s  … and %d more (use --strict)" % ("", len(hits) - len(shown)))

    if lens and stdev < 4.5 and len(lens) > 8:
        print("  ── rhythm ── sentence lengths are too uniform (σ=%.1f). Break the meter." % stdev)
    if bullet_ratio > 0.45 and len(body) > 12:
        print("  ── layout ── %.0f%% of lines are bullets. Prose carries argument; lists don't."
              % (bullet_ratio * 100))
    if per_100 > 1.2:
        print("  ── punctuation ── %d em-dashes (%.1f per 100 words). Some should be commas or periods."
              % (em_dashes, per_100))
    return score


def changed_files():
    try:
        base = subprocess.run(["git", "merge-base", "HEAD", "main"], cwd=REPO,
                              capture_output=True, text=True).stdout.strip() or "HEAD"
        out = subprocess.run(["git", "diff", "--name-only", base], cwd=REPO,
                             capture_output=True, text=True).stdout
        return [os.path.join(REPO, f) for f in out.split() if f.endswith((".md", ".txt", ".rst"))]
    except OSError:
        return []


def main():
    ap = argparse.ArgumentParser(prog="lint", description=__doc__.split("\n")[1])
    ap.add_argument("paths", nargs="*", help="markdown/text files (globs ok)")
    ap.add_argument("--strict", action="store_true", help="show every hit")
    ap.add_argument("--diff", action="store_true", help="lint prose files changed vs main")
    args = ap.parse_args()

    paths = []
    for p in args.paths:
        paths.extend(glob.glob(p) if any(c in p for c in "*?[") else [p])
    if args.diff or not paths:
        paths = changed_files() or paths
    if not paths:
        sys.exit("lint: nothing to lint (pass files, or --diff with changes on the branch)")

    scores = [lint(p, args.strict) for p in paths if os.path.isfile(p)]
    if scores and max(scores) > 12:
        print(STRUCTURE_HINTS)


if __name__ == "__main__":
    main()
