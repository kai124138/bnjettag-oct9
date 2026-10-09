#!/usr/bin/env python3
"""pdf_check.py — the rendering reviewer's mechanical half. Compiles a .tex with tectonic and
inspects the log and the PDF for the things a referee notices first.

    python3 tools/pdf_check.py docs/style/report-template.tex [more.tex ...]

A  compilation failed
A  unresolved references ("??" in the text, "undefined" in the log), missing citations
A  a figure file that could not be found
A  literal "$" or "\\" sequences visible in the rendered text (raw LaTeX leaked)
B  overfull boxes (more than 5), page count under 1 or over 100
C  warnings count

Needs tectonic and PyMuPDF (`uv run --with pymupdf`); the script re-executes itself under uv
if pymupdf is missing.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    import pymupdf  # type: ignore
except ImportError:  # re-exec under uv with the dependency
    if os.environ.get("PDF_CHECK_REEXEC") != "1":
        os.environ["PDF_CHECK_REEXEC"] = "1"
        sys.exit(subprocess.call(["uv", "run", "--quiet", "--with", "pymupdf", "python", __file__, *sys.argv[1:]]))
    raise


def check(tex: Path) -> tuple[str, list[str]]:
    findings: list[str] = []
    cwd = tex.parent
    run = subprocess.run(["tectonic", "-X", "compile", "--keep-logs", tex.name], cwd=cwd,
                         capture_output=True, text=True)
    log = (run.stdout + run.stderr)
    logfile = cwd / (tex.stem + ".log")
    if logfile.exists():
        log += logfile.read_text(errors="replace")
    if run.returncode != 0:
        findings.append("A  compilation failed:\n" + "\n".join(l for l in log.splitlines() if "error" in l.lower())[:2000])
        return "A", findings
    if re.search(r"undefined references|Citation .* undefined|Reference .* undefined", log):
        findings.append("A  undefined references or citations in the log")
    if re.search(r"File `.*' not found|LaTeX Error: File", log):
        findings.append("A  a file (figure or input) was not found")
    over = len(re.findall(r"Overfull \\hbox", log))
    if over > 5:
        findings.append(f"B  {over} overfull boxes")
    warns = len(re.findall(r"LaTeX Warning", log))
    if warns:
        findings.append(f"C  {warns} LaTeX warnings")
    pdf = cwd / (tex.stem + ".pdf")
    if not pdf.exists():
        findings.append("A  no PDF produced")
        return "A", findings
    doc = pymupdf.open(pdf)
    text = "\n".join(page.get_text() for page in doc)
    if "??" in text:
        findings.append("A  '??' visible in the rendered text (unresolved reference)")
    if re.search(r"\$[^$\n]{1,40}\$", text) or "\\textbf" in text or "\\ref" in text:
        findings.append("A  raw LaTeX visible in the rendered text")
    n = doc.page_count
    if n < 1 or n > 100:
        findings.append(f"B  page count {n}")
    doc.close()
    worst = min((f[0] for f in findings), default="C")
    return worst, findings


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    if not shutil.which("tectonic"):
        print("tectonic not found on PATH")
        return 2
    worst_all = "C"
    for arg in argv:
        tex = Path(arg)
        worst, findings = check(tex)
        print(f"== {tex}")
        for f in findings or ["   ok"]:
            print("   " + f if not f.startswith("   ") else f)
        worst_all = min(worst_all, worst)
    print(f"\nworst grade: {worst_all}" + ("  (A = red flag; blocks)" if worst_all == "A" else ""))
    return 1 if worst_all == "A" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
