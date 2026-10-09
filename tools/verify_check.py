#!/usr/bin/env python3
"""verify_check.py — numeric sanity on a VERIFY.md. The classifier-study counterpart of the
JFC plot validator's physics checks: objective, so they run every time. Red flags are
Category A and the arbiter may not downgrade them.

    python3 tools/verify_check.py campaigns/<id>/VERIFY.md
    python3 tools/verify_check.py --help

A  an AUC outside [0.5, 1.0], an accuracy outside [0, 1], a negative resource count, a
   non-positive eBOP count, NaN or inf
A  a number labelled AUC or accuracy on a line that names neither a split (validation /
   held-out / ROC-test) nor a table whose header does
A  a "gap" / "Δ" / "difference" line with no interval ("±", "[a, b]", "CI", "sd")
A  suspiciously good: macro AUC ≥ 0.95, or a seed sd of exactly 0 over > 1 seed
B  a held-out number without n on the line or in its table header (n = 260,000 expected)
B  the word "seed" absent from the file, or fewer than 3 seeds stated anywhere
B  no "recompute" / "recomputed" / "uv run" evidence in the file
C  a number with more than 5 decimals (false precision)

verify.json beside VERIFY.md (a JSON list, one object per quoted number; results-analyst):
A  missing, for a campaign directory (campaigns/ or local/YYYY-MM-DD-...) dated after
   2026-09-26, or whose name carries no date
B  missing, for a campaign dated 2026-09-26 or earlier (predates verify.json; not required)
A  it does not parse, or is not a list of objects
A  a row missing a required field (claim, quantity, value, metric, split, n, seeds, status,
   source), or holding it as null / ""
A  an AUC row (metric or quantity names AUC) whose value is not a number in [0.5, 1]; rows
   whose quantity, metric or status names a gap, Δ, "−", difference, sd or interval are exempt
B  a row's value that VERIFY.md does not print at the precision verify.json writes it
   (0.8711 needs 0.8711 or a finer number rounding to it; 0.87113 is not matched by 0.8711;
   thousands separators, unicode minus and % are read, so 0.941 matches "94.1 %")

Heuristic by design: it reads markdown, not arrays. A clean run is necessary, not sufficient.
"""
from __future__ import annotations

import datetime
import json
import math
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

NUM = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?(?:e-?\d+)?)(?![\w.])")
SPLIT = re.compile(r"validation|held-out|held out|roc-test|test set|test split", re.I)
INTERVAL = re.compile(r"±|\+/-|\[\s*-?\d|\bCI\b|\bsd\b|\bstd\b|interval|bootstrap", re.I)
GAP = re.compile(r"\bgap\b|Δ|\bdelta\b|\bdifference\b|(?<!one-)\bvs\.?\b(?!-rest)|paired", re.I)
AUC = re.compile(r"\bAUC\b", re.I)
ACC = re.compile(r"accuracy|acc\b", re.I)
RES = re.compile(r"\b(LUT|FF|DSP|BRAM)\b")
EBOP = re.compile(r"ebop", re.I)
SEEDS = re.compile(r"(\d+)\s*seeds?|seeds?\s*(?:=|:)\s*(\d+)|seeds?\s+1\s*[–-]\s*(\d+)", re.I)
REQUIRED = ("claim", "quantity", "value", "metric", "split", "n", "seeds", "status", "source")
JSON_FROM = datetime.date(2026, 9, 26)     # verify.json is required for campaigns dated after this
DATED = re.compile(r"^(\d{4})-(\d{2})-(\d{2})-")
MDNUM = re.compile(r"(?<![\w.])(-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)(?!\w|\.\d)(\s*%)?")


def campaign_date(path: Path) -> datetime.date | None:
    m = DATED.match(path.resolve().parent.name)
    try:
        return datetime.date(*map(int, m.groups())) if m else None
    except ValueError:
        return None


def as_number(v: object) -> float | None:
    if isinstance(v, bool):
        return None
    try:
        return float(v)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None


def decimals(tok: str) -> int | None:
    try:
        return max(0, -Decimal(tok.strip()).as_tuple().exponent)  # type: ignore[operator]
    except (InvalidOperation, TypeError):
        return None


def md_numbers(text: str) -> list[tuple[float, int]]:
    """(value, decimals as printed) for every number in the markdown; "94.1 %" also as (0.941, 3)."""
    text = re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", text.replace("−", "-"))
    out = []
    for m in MDNUM.finditer(text):
        d = decimals(m.group(1))
        if d is not None:
            out.append((float(m.group(1)), d))
            if m.group(2):
                out.append((float(m.group(1)) / 100, d + 2))
    return out


def printed(raw: object, v: float, nums: list[tuple[float, int]]) -> bool:
    """VERIFY.md prints v at the precision verify.json writes it (or finer, rounding to v)."""
    dj = decimals(raw if isinstance(raw, str) else repr(raw))
    if dj is None:
        return True
    return any(d >= dj and abs(t - v) <= 0.5 * 10 ** -dj + 1e-12 for t, d in nums)


def check_json(path: Path, text: str) -> list[tuple[str, int, str]]:
    f: list[tuple[str, int, str]] = []
    jpath = path.parent / "verify.json"
    if not jpath.exists():
        day = campaign_date(path)
        if day is None:
            f.append(("A", 0, "no verify.json beside VERIFY.md, and the campaign directory name carries no date"))
        elif day > JSON_FROM:
            f.append(("A", 0, f"no verify.json beside VERIFY.md (required for campaigns after {JSON_FROM})"))
        else:
            f.append(("B", 0, f"no verify.json (campaign dated {day} predates verify.json; not required)"))
        return f
    try:
        rows = json.loads(jpath.read_text())
    except (ValueError, UnicodeDecodeError) as e:
        return [("A", 0, f"verify.json does not parse: {e}")]
    if not isinstance(rows, list):
        return [("A", 0, "verify.json is not a JSON list of rows")]
    nums = md_numbers(text)
    for k, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            f.append(("A", 0, f"verify.json row {k} is not an object"))
            continue
        tag = f"verify.json row {k} ({row.get('quantity') or row.get('claim') or '?'})"
        missing = [r for r in REQUIRED if row.get(r) in (None, "")]
        if missing:
            f.append(("A", 0, f"{tag}: missing {', '.join(missing)}"))
        raw, v = row.get("value"), as_number(row.get("value"))
        what = f"{row.get('quantity', '')} {row.get('metric', '')}"
        diff = f"{what} {row.get('status', '')}"
        is_diff = bool(GAP.search(diff) or INTERVAL.search(diff) or "−" in diff)
        if raw not in (None, "") and AUC.search(what) and not is_diff:
            if v is None or not 0.5 <= v <= 1.0:
                f.append(("A", 0, f"{tag}: AUC {raw!r} outside [0.5, 1]"))
        if v is not None and math.isfinite(v) and not printed(raw, v, nums):
            f.append(("B", 0, f"{tag}: value {raw} appears nowhere in VERIFY.md at that precision"))
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
        text = path.read_text(errors="replace")
        lines = text.splitlines()
        findings: list[tuple[str, int, str]] = []
        header_split_ok = False
        header_n_ok = False
        for i, line in enumerate(lines, 1):
            if line.startswith("|") and ("---" not in line) and i + 1 <= len(lines) and "---" in lines[i] if i < len(lines) else False:
                header_split_ok = bool(SPLIT.search(line))
                header_n_ok = bool(re.search(r"\bn\b", line))
            # drop hyphenated tokens (top-1, s1-8, df7, W1A8, N64) before reading numbers
            clean = re.sub(r"\b[A-Za-z]+-?\d+(?:[–-]\d+)?\b", " ", line)
            nums = [float(x) for x in NUM.findall(clean) if x not in ("", "-")]
            if any(math.isnan(v) or math.isinf(v) for v in nums) or re.search(r"\bnan\b|\binf\b", line, re.I):
                findings.append(("A", i, "NaN or inf"))
            is_gap = bool(GAP.search(line) or INTERVAL.search(line) or "−" in line)
            if AUC.search(line):
                for v in nums:
                    # a difference line (Δ, ±, an interval, a unicode minus) legitimately holds small values
                    if 0 < v < 1 and not (0.5 <= v <= 1.0) and not is_gap:
                        findings.append(("A", i, f"AUC {v} outside [0.5, 1]"))
                    if 0.95 <= v < 1.0 and "macro" in line.lower() and not is_gap:
                        findings.append(("A", i, f"suspiciously good macro AUC {v}; check for leakage"))
                if nums and not SPLIT.search(line) and not header_split_ok and not is_gap:
                    findings.append(("A", i, "AUC value without its split (validation / held-out)"))
                if line.startswith("|") and re.search(r"held-?out|roc-test", line, re.I) and not re.search(r"\bn\s*=|\bn\b", line) and not header_n_ok:
                    findings.append(("B", i, "held-out number without n (table row)"))
            if ACC.search(line):
                if nums and not SPLIT.search(line) and not header_split_ok and not is_gap:
                    findings.append(("A", i, "accuracy value without its split"))
            if RES.search(line):
                for v in nums:
                    if v < 0:
                        findings.append(("A", i, f"negative resource count {v}"))
            if EBOP.search(line):
                for v in nums:
                    if v <= 0 and v != 0.0:
                        findings.append(("A", i, f"non-positive eBOP count {v}"))
            if GAP.search(line) and nums and not INTERVAL.search(line) and not line.startswith("|") and "verdict" not in line.lower():
                findings.append(("A", i, "a gap stated without an interval or sd"))
            if re.search(r"sd\s*(=|:)?\s*0(\.0+)?\b", line) and re.search(r"[2-9]\s*seeds|\d\d\s*seeds", line):
                findings.append(("A", i, "seed sd exactly 0 over several seeds"))
            for m in re.finditer(r"\d\.\d{6,}", line):
                findings.append(("C", i, f"false precision: {m.group(0)}"))
        seeds = [int(g) for m in SEEDS.finditer(text) for g in m.groups() if g]
        if "seed" not in text.lower():
            findings.append(("B", 0, "no mention of seeds"))
        elif seeds and max(seeds) < 3:
            findings.append(("B", 0, f"fewer than 3 seeds stated (max found {max(seeds)})"))
        if not re.search(r"recomput|uv run", text, re.I):
            findings.append(("B", 0, "no recompute evidence (command or 'recomputed')"))
        findings += check_json(path, text)
        print(f"== {path}")
        if not findings:
            print("   ok")
        for grade, ln, msg in sorted(findings, key=lambda f: (f[0], f[1])):
            print(f"   {grade}  line {ln}: {msg}")
            worst = min(worst, grade)
    print(f"\nworst grade: {worst}" + ("  (A = red flag; blocks)" if worst == "A" else ""))
    return 1 if worst == "A" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
