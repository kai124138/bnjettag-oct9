#!/usr/bin/env python3
"""bib_check.py — the BibTeX validator: every citation must resolve to a real record.

    python3 tools/bib_check.py references.bib [--online]
    python3 tools/bib_check.py --help

A  an entry with neither a DOI nor an arXiv id (eprint / arxiv / url containing arxiv.org)
A  with --online: an arXiv id that does not resolve (no entry in the export API, or a 404 on
   the arxiv.org abstract page) or cannot exist (month outside 01–12, before 0704, or the
   wrong number of digits for its year)
A  with --online: a DOI that does not resolve (404 at doi.org/api/handles)
A  with --online: the entry's title does not match the arXiv or Crossref record's title
   (difflib ratio < 0.80 after folding case, punctuation, LaTeX braces and commands)
A  duplicate keys
B  with --online: a near-match title (ratio 0.80–0.95); the record's title is printed
B  with --online: could not check an id (timeout, network error, or an HTTP status that is not
   a verdict: arXiv answers 406/429/503 when it throttles); re-run before the bib ships
B  an entry without a year or without a title (a bare numeric `year = 2024` counts as a year)
C  with --online: a DOI that resolves but is not in Crossref, so its title was not compared
C  a title containing LaTeX math ($...$), which citeproc double-escapes

Stdlib only. --online sends a descriptive User-Agent, waits 10 s per lookup, and spaces arXiv
calls at least 3 s apart (export.arxiv.org first, arxiv.org/abs when the API throttles).
"""
from __future__ import annotations

import difflib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ENTRY = re.compile(r"@(\w+)\s*\{\s*([^,\s]+)\s*,(.*?)\n\}", re.S)
FIELD = re.compile(r"(\w+)\s*=\s*[{\"](.*?)[}\"]\s*,?\s*\n", re.S)
BARE = re.compile(r"^\s*(\w+)\s*=\s*(\d+)\s*,?\s*$", re.M)
ARXIV = re.compile(r"(\d{4}\.\d{4,5})(v\d+)?")

UA = "bnjettag-bib-check/1.0 (mailto:none)"
TIMEOUT = 10
ARXIV_GAP = 3.0
MATCH, NEAR = 0.95, 0.80
ATOM = "{http://www.w3.org/2005/Atom}"
_last_arxiv = [0.0]


def fetch(url: str, accept: str) -> tuple[int, bytes, str]:
    """(HTTP status, body, why); status 0 when the server could not be reached."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return r.status, r.read(), ""
    except urllib.error.HTTPError as e:
        return e.code, b"", f"HTTP {e.code}"
    except Exception as e:  # noqa: BLE001 — timeouts, resets, bad URLs: never a verdict
        return 0, b"", f"network: {getattr(e, 'reason', e) or type(e).__name__}"


def arxiv_get(url: str, accept: str) -> tuple[int, bytes, str]:
    wait = ARXIV_GAP - (time.monotonic() - _last_arxiv[0])
    if wait > 0:
        time.sleep(wait)
    try:
        return fetch(url, accept)
    finally:
        _last_arxiv[0] = time.monotonic()


def arxiv_valid(aid: str) -> bool:
    """YYMM.NNNN (0704–1412) or YYMM.NNNNN (1501 on), month 01–12."""
    yymm, num = aid.split("v")[0].split(".")
    return 1 <= int(yymm[2:]) <= 12 and int(yymm) >= 704 and len(num) == (5 if int(yymm) >= 1501 else 4)


def arxiv_record(aid: str) -> tuple[str, str]:
    """('ok', title) | ('missing', '') | ('invalid', '') | ('unchecked', why)."""
    if not arxiv_valid(aid):
        return "invalid", ""
    status, body, why = arxiv_get(f"https://export.arxiv.org/api/query?id_list={aid}", "application/atom+xml")
    if status == 200:
        try:
            titles = [" ".join((e.findtext(f"{ATOM}title") or "").split())
                      for e in ET.fromstring(body).findall(f"{ATOM}entry")]
        except ET.ParseError:
            titles = None
        if titles is not None:
            titles = [t for t in titles if t and t != "Error"]
            return ("ok", titles[0]) if titles else ("missing", "")
        why = "unparsable API response"
    # the API throttles with an empty 406/429/503; the abstract page is the second opinion
    status, body, why2 = arxiv_get(f"https://arxiv.org/abs/{aid}", "text/html")
    if status == 404:
        return "missing", ""
    if status == 200:
        m = re.search(r'<meta name="citation_title" content="([^"]*)"', body.decode(errors="replace"))
        if m:
            return "ok", " ".join(m.group(1).split())
        why2 = "no citation_title on the abstract page"
    return "unchecked", f"export.arxiv.org {why or status}, arxiv.org/abs {why2 or status}"


def doi_record(doi: str) -> tuple[str, str]:
    """('ok', title) | ('missing', '') | ('notitle', '') | ('unchecked', why)."""
    doi = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:)", "", doi, flags=re.I)
    q = urllib.parse.quote(doi, safe="/")
    status, _, why = fetch(f"https://doi.org/api/handles/{q}", "application/json")
    if status == 404:
        return "missing", ""
    if status != 200:
        return "unchecked", f"doi.org {why}"
    status, body, why = fetch(f"https://api.crossref.org/works/{q}", "application/json")
    if status == 404:
        return "notitle", ""
    if status != 200:
        return "unchecked", f"api.crossref.org {why}"
    try:
        title = (json.loads(body)["message"].get("title") or [""])[0]
    except (ValueError, KeyError, IndexError, TypeError):
        return "unchecked", "unparsable Crossref response"
    return ("ok", " ".join(title.split())) if title else ("notitle", "")


def norm_title(t: str) -> str:
    t = re.sub(r"\\[a-zA-Z]+\s*", " ", t)          # \textit, \emph, ...
    t = re.sub(r"\\.", "", t)                        # \" \' accents
    t = re.sub(r"<[^>]+>", " ", t)                   # Crossref <i>...</i>
    t = re.sub(r"[^\w\s]|_", " ", t.replace("{", "").replace("}", "").replace("$", ""))
    return " ".join(t.lower().split())


def compare_title(key: str, where: str, mine: str, theirs: str) -> tuple[str, str] | None:
    r = difflib.SequenceMatcher(None, norm_title(mine), norm_title(theirs)).ratio()
    if r >= MATCH:
        return None
    grade = "A" if r < NEAR else "B"
    word = "does not match" if grade == "A" else "near-matches"
    return grade, f"{key}: title {word} {where} (ratio {r:.2f}); record has {theirs!r}"


def main(argv: list[str]) -> int:
    if argv and argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0
    online = "--online" in argv
    files = [a for a in argv if a != "--online"]
    if not files:
        print(__doc__)
        return 2
    worst = "C"
    for f in files:
        text = Path(f).read_text(errors="replace")
        keys: dict[str, int] = {}
        findings: list[tuple[str, str]] = []
        for m in ENTRY.finditer(text):
            kind, key, body = m.group(1), m.group(2), m.group(3) + "\n"
            keys[key] = keys.get(key, 0) + 1
            fields = {k.lower(): v.strip() for k, v in FIELD.findall(body)}
            for k, v in BARE.findall(body):
                fields.setdefault(k.lower(), v)
            doi = fields.get("doi")
            eprint = fields.get("eprint") or fields.get("arxiv") or ""
            url = fields.get("url", "")
            aid = None
            for cand in (eprint, url):
                mm = ARXIV.search(cand or "")
                if mm:
                    aid = mm.group(1) + (mm.group(2) or "")
                    break
            if not doi and not aid:
                findings.append(("A", f"{key}: neither DOI nor arXiv id"))
            if online and aid:
                state, got = arxiv_record(aid)
                if state == "missing":
                    findings.append(("A", f"{key}: arXiv {aid} does not resolve"))
                elif state == "invalid":
                    findings.append(("A", f"{key}: arXiv {aid} cannot exist (not a valid YYMM.NNNNN id)"))
                elif state == "unchecked":
                    findings.append(("B", f"{key}: could not check arXiv {aid} ({got})"))
                elif "title" in fields:
                    hit = compare_title(key, f"arXiv {aid}", fields["title"], got)
                    if hit:
                        findings.append(hit)
            if online and doi:
                state, got = doi_record(doi)
                if state == "missing":
                    findings.append(("A", f"{key}: DOI {doi} does not resolve"))
                elif state == "unchecked":
                    findings.append(("B", f"{key}: could not check DOI {doi} ({got})"))
                elif state == "notitle":
                    findings.append(("C", f"{key}: DOI {doi} resolves but is not in Crossref; title not compared"))
                elif "title" in fields:
                    hit = compare_title(key, f"DOI {doi}", fields["title"], got)
                    if hit:
                        findings.append(hit)
            if "year" not in fields:
                findings.append(("B", f"{key}: no year"))
            if "title" not in fields:
                findings.append(("B", f"{key}: no title"))
            elif "$" in fields["title"]:
                findings.append(("C", f"{key}: LaTeX math in title (citeproc double-escapes it)"))
        for k, n in keys.items():
            if n > 1:
                findings.append(("A", f"duplicate key {k} ×{n}"))
        print(f"== {f}  ({len(keys)} entries{', online' if online else ''})")
        if not findings:
            print("   ok")
        for grade, msg in sorted(findings):
            print(f"   {grade}  {msg}")
            worst = min(worst, grade)
    print(f"\nworst grade: {worst}" + ("  (A = red flag; blocks)" if worst == "A" else ""))
    return 1 if worst == "A" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
