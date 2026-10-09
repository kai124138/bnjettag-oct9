#!/usr/bin/env python3
"""plot_check.py — programmatic figure validation. A script, not an opinion.

    python3 tools/plot_check.py <script.py|dir> [...]
    python3 tools/plot_check.py --help

Modelled on the plot-validator of Moreno et al. (arXiv:2603.20179), but narrower: this one
checks style and labelling only. The numeric sanity checks their validator also runs
(non-negative yields, efficiencies in [0,1]) belong in VERIFY.md's recompute here. Findings
are graded A (red flag, blocks: no reviewer or arbiter may downgrade it), B (fix before it ships),
C (style). Exit 1 on any A.

What it checks in a figure script
  A  a forbidden plotting library (plotly, seaborn, bokeh) is imported
  A  an axis label (plain, f-, r- or rf-string) that names AUC or accuracy without saying
     which split (validation / held-out / ROC-test) — the metric/split rule in CLAUDE.md
  A  a ROC or mistag-rate plot without a log y axis (HEP convention). A ROC plot is one with
     ROC content: roc_curve, fpr/tpr, "ROC" (not "ROC-test" or "ROC AUC"), mistag, false or
     true positive, signal/background efficiency, background rejection
  B  the house style is not applied (no plt.style.use(...bnjettag.mplstyle))
  B  ax.set_title / title= present (journal style: the caption carries the message)
  B  no provenance caption (fig.supxlabel / fig.text naming seeds, source, or n)
  B  savefig without both .png and .svg, or without bbox_inches="tight" (a loop such as
     `for ext in ("png", "svg"): fig.savefig(f"x.{ext}")` counts as both)
  C  hard-coded fontsize= (belongs in the .mplstyle)
  C  plt.close(fig) missing after savefig
What it checks in an output directory
  B  a .png without a .svg beside it (or the reverse)
  A  an empty or unreadable image file

Directives in a script's comments:  `# plot_check: allow-title`, `# plot_check: allow-fontsize`
(use them when the exception is deliberate, e.g. a contact sheet that compares styles).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FORBIDDEN = ("plotly", "seaborn", "bokeh", "altair")
METRIC = re.compile(r"(auc|accuracy)", re.I)
SPLIT = re.compile(r"(validation|held-out|held out|roc-test|test set|test split|n\s*=)", re.I)
LABEL = re.compile(r"(?:set_[xy]label\(|[xy]label\s*=\s*)\s*(?P<prefix>[rRfFuU]{0,2})(?P<q>['\"])(?P<text>.*?)(?P=q)")
CAPTION = re.compile(r"supxlabel\(|fig\.text\(|figtext\(|caption")
TITLE = re.compile(r"set_title\(|\btitle\s*=\s*['\"]")
FONTSIZE = re.compile(r"fontsize\s*=")
STYLE = re.compile(r"style\.use\([^)]*bnjettag\.mplstyle")
ROC = re.compile(r"\broc_curve\b|\b[ft]pr\b|mistag|(?:false|true)[ -]positive|(?:signal|background) efficiency|"
                 r"background rejection", re.I)
ROC_WORD = re.compile(r"\bROC\b(?![ -]?(?:test|AUC|auc)\b)")   # case-sensitive: not roc-results/, ROC-test
FMT_LOOP = re.compile(r"for\s+(?P<var>\w+)\s+in\s+[(\[{](?P<items>[^)\]}]*)[)\]}]\s*:")
LOGY = re.compile(r"yscale\s*=\s*['\"]log['\"]|set_yscale\(\s*['\"]log['\"]|semilogy\(")
LOGX = re.compile(r"xscale\s*=\s*['\"]log['\"]|set_xscale\(\s*['\"]log['\"]|semilogx\(")
SAVE = re.compile(r"savefig\(")


def savefig_args(src: str) -> list[str]:
    """The argument text of every savefig( ... ) call, balanced over parentheses."""
    out = []
    for m in SAVE.finditer(src):
        depth, i = 1, m.end()
        while i < len(src) and depth:
            depth += {"(": 1, ")": -1}.get(src[i], 0)
            i += 1
        out.append(src[m.end():i - 1])
    return out


def saved_formats(src: str) -> set[str]:
    """png/svg named as a '.png' literal, or iterated in `for ext in ('png', 'svg'):` and used
    inside a savefig call (f-string, concatenation or format=)."""
    fmts = {ext for ext in ("png", "svg") if f".{ext}" in src}
    calls = savefig_args(src)
    for m in FMT_LOOP.finditer(src):
        exts = set(re.findall(r"['\"]\.?(png|svg)['\"]", m.group("items")))
        if exts and any(re.search(rf"\b{m.group('var')}\b", c) for c in calls):
            fmts |= exts
    return fmts


def check_script(path: Path) -> list[tuple[str, str]]:
    src = path.read_text(errors="replace")
    allow_title = "plot_check: allow-title" in src
    allow_font = "plot_check: allow-fontsize" in src
    f: list[tuple[str, str]] = []
    for lib in FORBIDDEN:
        if re.search(rf"^\s*(import|from)\s+{lib}\b", src, re.M):
            f.append(("A", f"imports {lib}; figures are matplotlib with the house style"))
    if not STYLE.search(src):
        f.append(("B", "house style not applied: expected plt.style.use('<path>/docs/style/bnjettag.mplstyle')"))
    for m in LABEL.finditer(src):
        text = m.group("text")
        if METRIC.search(text) and not SPLIT.search(text):
            f.append(("A", f"label names a metric without its split: {text!r}"))
    if ROC.search(src) or ROC_WORD.search(src):
        if not LOGY.search(src) and not LOGX.search(src):
            f.append(("A", "ROC/mistag plot with no log axis at all (the mistag rate must be on a log scale)"))
        elif not LOGY.search(src):
            f.append(("B", "ROC plot has the mistag rate on a log x axis; house convention is efficiency on x, mistag rate on log y (verify-roc skill)"))
    if TITLE.search(src) and not allow_title:
        f.append(("B", "axes title present; journal style puts the message in the caption (or add '# plot_check: allow-title')"))
    if SAVE.search(src):
        if not CAPTION.search(src):
            f.append(("B", "no provenance caption (fig.supxlabel / fig.text with seeds, n, or source)"))
        if saved_formats(src) != {"png", "svg"}:
            f.append(("B", "savefig should write both .png and .svg (the svg is the editable record)"))
        if 'bbox_inches="tight"' not in src and "bbox_inches='tight'" not in src:
            f.append(("B", "savefig without bbox_inches=\"tight\""))
        if "plt.close" not in src:
            f.append(("C", "no plt.close after savefig"))
    if FONTSIZE.search(src) and not allow_font:
        f.append(("C", f"{len(FONTSIZE.findall(src))} hard-coded fontsize= (belongs in the .mplstyle)"))
    return f


def check_dir(path: Path) -> list[tuple[str, str]]:
    f: list[tuple[str, str]] = []
    pngs = {p.stem: p for p in path.glob("*.png")}
    svgs = {p.stem: p for p in path.glob("*.svg")}
    for stem, p in pngs.items():
        if p.stat().st_size < 1000:
            f.append(("A", f"{p.name}: empty or truncated image"))
        if stem not in svgs and not stem.startswith(("contact-sheet", "variant-")):
            f.append(("B", f"{p.name}: no .svg beside it"))
    for stem, p in svgs.items():
        if stem not in pngs:
            f.append(("B", f"{p.name}: no .png beside it (the quick-look copy)"))
    return f


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    if not argv:
        print(__doc__)
        return 2
    worst = "C"
    for arg in argv:
        path = Path(arg)
        findings = check_dir(path) if path.is_dir() else check_script(path)
        print(f"== {path}")
        if not findings:
            print("   ok")
        for grade, msg in sorted(findings):
            print(f"   {grade}  {msg}")
            worst = min(worst, grade)
    print(f"\nworst grade: {worst}" + ("  (A = red flag; blocks)" if worst == "A" else ""))
    return 1 if worst == "A" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
