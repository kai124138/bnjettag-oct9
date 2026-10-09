#!/usr/bin/env python3
"""
claims.py — pull every quantitative claim out of the docs, with its exact source line.

    python3 tools/claims.py                       # every number in the living + frozen docs
    python3 tools/claims.py --kind auc            # just the AUCs
    python3 tools/claims.py --unlabeled           # numbers missing a metric/era/status label ← the useful one
    python3 tools/claims.py --dupes               # the same figure quoted in several places (drift risk)
    python3 tools/claims.py --file RESEARCH.md

The house rule is that a number may only be reported with its metric (validation AUC vs
ROC-test AUC), its era (era-1 private 2-class / era-2 public 5-class / era-final), and
its status (single-run vs seed-averaged). `--unlabeled` finds the lines that break it,
and `--dupes` finds the same number living in two files, which is how a report goes
stale without anyone noticing.

This tool locates claims. It does not verify them — that is the results-analyst's job
against the .npz (see .claude/skills/verify-roc/SKILL.md). Stdlib only.
"""

import argparse
import os
import re
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

DEFAULT_DOCS = [
    "RESEARCH.md", "FAQ.md", "00-START-HERE.md", "ROADMAP.md", "FULL-SYNTHESIS.md",
    "reports", "bnjettag/results", "bnjettag/roc-results",
]

KINDS = {
    # kind        pattern                                              context words that must be near
    "auc":     (r"\b0\.[6-9]\d{2,4}\b", ("auc", "roc")),
    "dsp":     (r"\b\d[\d,]*\s*(?:DSPs?|DSP48)\b|\bDSP\s*=?\s*\d+\b", ("dsp",)),
    "lut":     (r"\b[\d,.]+\s*[KMkm]?\s*LUTs?\b|\bLUT\s*[:=]\s*[\d,.]+", ("lut",)),
    "latency": (r"\b[\d,.]+\s*(?:cycles?|ns|µs|us|ms)\b", ("latency", "cycle", "ii")),
    "percent": (r"\b\d{1,3}(?:\.\d+)?\s*%", ()),
    "params":  (r"\b[\d,.]+\s*[KMkm]\s*(?:params?|parameters)\b", ("param",)),
}

ERA_WORDS = ("era-1", "era 1", "era-2", "era 2", "era-final", "era final",
             "private", "public", "5-class", "2-class", "hls4ml lhc jet")
METRIC_WORDS = ("validation auc", "val auc", "val-auc", "roc-test", "roc test", "test auc",
                "macro-ovr", "macro ovr", "one-vs-rest", "auc pts", "auc points")
STATUS_WORDS = ("seed-averaged", "seed averaged", "single-run", "single run", "n =", "n=")


def walk(targets):
    for t in targets:
        full = os.path.join(REPO, t)
        if os.path.isfile(full) and full.endswith(".md"):
            yield full
        elif os.path.isdir(full):
            for root, _, files in os.walk(full):
                if any(p in root for p in (".git", "__pycache__", "archive")):
                    continue
                for f in sorted(files):
                    if f.endswith(".md"):
                        yield os.path.join(root, f)


def context(lines, i, span=3, heading=True):
    """Nearby lines, optionally plus the section heading above — RESEARCH.md carries the
    era label in its headings ('§5 Era-1 results'), not on every table row."""
    lo, hi = max(0, i - span), min(len(lines), i + span + 1)
    near = list(lines[lo:hi])
    if heading:
        for j in range(i, -1, -1):
            if lines[j].lstrip().startswith("#"):
                near.append(lines[j])
                break
    return " ".join(near).lower()


def collect(targets, kinds):
    out = []
    for path in walk(targets):
        try:
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
        except OSError:
            continue
        in_fence = False
        for i, line in enumerate(lines):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence or not line.strip():
                continue
            low = line.lower()
            near = context(lines, i, span=1, heading=False)   # is this line even a claim?
            wide = context(lines, i, span=3, heading=True)    # is the claim labeled?
            for kind, (pat, need) in KINDS.items():
                if kinds and kind not in kinds:
                    continue
                if need and not any(w in low or w in near for w in need):
                    continue
                for m in re.finditer(pat, line):
                    out.append({
                        "kind": kind,
                        "value": m.group(0).strip(),
                        "file": os.path.relpath(path, REPO),
                        "line": i + 1,
                        "text": line.strip()[:110],
                        "has_era": any(w in wide for w in ERA_WORDS),
                        "has_metric": any(w in wide for w in METRIC_WORDS),
                        "has_status": any(w in wide for w in STATUS_WORDS),
                    })
    return out


def main():
    ap = argparse.ArgumentParser(prog="claims", description=__doc__.split("\n")[1])
    ap.add_argument("--kind", choices=sorted(KINDS), nargs="*")
    ap.add_argument("--file", nargs="*", help="restrict to these paths (default: the doc set)")
    ap.add_argument("--unlabeled", action="store_true", help="only claims missing era/metric labels")
    ap.add_argument("--dupes", action="store_true", help="only values that appear in >1 file")
    args = ap.parse_args()

    claims = collect(args.file or DEFAULT_DOCS, args.kind)
    if not claims:
        print("claims: none found.")
        return

    if args.dupes:
        by_val = defaultdict(list)
        for c in claims:
            if c["kind"] in ("auc", "dsp", "lut", "latency"):
                by_val[(c["kind"], c["value"])].append(c)
        multi = {k: v for k, v in by_val.items()
                 if len({c["file"] for c in v}) > 1}
        if not multi:
            print("claims: no figure is quoted in more than one file.")
            return
        print("claims: %d figure(s) quoted in several files — keep them in sync\n" % len(multi))
        for (kind, val), cs in sorted(multi.items(), key=lambda kv: -len(kv[1])):
            print("%s  %s" % (kind.upper().ljust(8), val))
            for c in cs:
                print("    %s:%d  %s" % (c["file"], c["line"], c["text"][:80]))
            print()
        return

    if args.unlabeled:
        bad = [c for c in claims
               if c["kind"] in ("auc",) and not (c["has_era"] and c["has_metric"])]
        if not bad:
            print("claims: every AUC in scope carries an era and a metric label. Good.")
            return
        print("claims: %d of %d AUC(s) have no era and/or metric label nearby "
              "(checked ±3 lines and the section heading)\n"
              % (len(bad), sum(1 for c in claims if c["kind"] == "auc")))
        for c in bad:
            miss = ",".join(k for k, v in
                            (("era", c["has_era"]), ("metric", c["has_metric"]), ("status", c["has_status"]))
                            if not v)
            print("  %-40s %-8s missing:%-18s %s"
                  % ("%s:%d" % (c["file"], c["line"]), c["value"], miss, c["text"][:60]))
        print("\nHouse rule: metric (val vs ROC-test) + era (1 / 2 / final) + status (single vs seed-avg).")
        return

    by_kind = defaultdict(list)
    for c in claims:
        by_kind[c["kind"]].append(c)
    for kind in sorted(by_kind):
        cs = by_kind[kind]
        print("\n── %s (%d) ─────────────────────────" % (kind, len(cs)))
        for c in cs[:40]:
            labels = "".join(("e" if c["has_era"] else "·", "m" if c["has_metric"] else "·",
                              "s" if c["has_status"] else "·"))
            print("  %-8s [%s]  %-34s %s" % (c["value"][:8], labels, "%s:%d" % (c["file"], c["line"]),
                                             c["text"][:60]))
        if len(cs) > 40:
            print("  … and %d more" % (len(cs) - 40))
    print("\n[e|m|s] = era / metric / status label found nearby. Run --unlabeled for the violations.")


if __name__ == "__main__":
    main()
