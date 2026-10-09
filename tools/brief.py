#!/usr/bin/env python3
"""brief.py — the session-start brief. Local files only, under forty lines, always exits 0.

Registered as a SessionStart hook in .claude/settings.json; its stdout is injected into the
session's context, so orientation costs nothing. It never calls the cluster (OIDC login can
open a browser and the hook has a timeout): jobs in flight come from the newest
launch-record.json under local/ and from a cached `nrp_doctor status` if one is under a day old.
"""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX = 40


def lines_of(path: Path) -> list[str]:
    try:
        return path.read_text(errors="replace").splitlines()
    except OSError:
        return []


def main() -> int:
    out: list[str] = [f"# Brief {dt.datetime.now():%Y-%m-%d %H:%M}  (tools/brief.py; local files only)"]

    # 1. index head: open studies + pending decisions
    head = lines_of(ROOT / ".claude/memory/index-head.md")
    keep = [l for l in head if l.startswith(("- ", "**"))]
    out += keep[:14] or ["(no index yet: run `python3 tools/index.py init && python3 tools/index.py build`)"]

    # 2. last solo verdict (critical-reviewer rounds / red team / gates)
    rep = lines_of(ROOT / ".claude/memory/review-reports.md")
    when = next((l[3:].strip() for l in rep if l.startswith("## ")), None)
    verdict = next((l.strip() for l in rep if l.strip().startswith("VERDICT")), None)
    out.append("")
    out.append(f"**critical-reviewer:** {when} — {verdict}" if when else "**critical-reviewer:** no report in this repo yet (`/rounds`)")

    # 3. jobs in flight, from local records only
    recs = sorted(ROOT.glob("local/*/launch-record*.json"), key=lambda p: p.stat().st_mtime)
    if recs:
        p = recs[-1]
        age = (dt.datetime.now() - dt.datetime.fromtimestamp(p.stat().st_mtime)).days
        try:
            d = json.loads(p.read_text())
            scalars = {k: v for k, v in d.items() if isinstance(v, (str, int, float))} if isinstance(d, dict) else {}
            summary = ", ".join(f"{k}={v}" for k, v in list(scalars.items())[:4])
        except Exception:  # noqa: BLE001
            summary = "(unparseable)"
        out.append(f"**newest launch record:** `{p.relative_to(ROOT)}` ({age} d old) {summary}"[:200])
    cache = ROOT / "nrp-lab/.status-cache.txt"
    if cache.exists() and (dt.datetime.now() - dt.datetime.fromtimestamp(cache.stat().st_mtime)).total_seconds() < 86400:
        out.append("**cluster status (cached <24 h):**")
        out += ["  " + l for l in lines_of(cache)[:6]]
    else:
        out.append("**cluster:** not queried at start (run `python3 nrp-lab/nrp_doctor.py status` when it matters)")

    # 4. standing rules that were once forgotten
    out += ["", "**Gates:** manifests are linted by the PreToolUse hook before any `kubectl apply`; "
                "numbers enter the record only from a VERIFY.md; nothing goes outward without Kai."]

    text = "\n".join(out[:MAX])
    print(text)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"# Brief unavailable: {exc}")
        sys.exit(0)
