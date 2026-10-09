#!/usr/bin/env python3
"""merge_logs.py — merge two copies of an append-only, newest-on-top memory log.

    python3 tools/merge_logs.py <primary.md> <secondary.md> <out.md> [--dry-run]

The two agent layers kept separate copies of experiment-log.md, decisions.md and
research-log.md after 2026-09-08 and both kept growing. This merges them by entry
(`## YYYY-MM-DD — title` headers), newest first, without dropping anything:

  - the same header in both with the same body: kept once;
  - the same header with different bodies: the primary's body is kept, the secondary's
    is appended under a `<!-- secondary variant -->` marker;
  - the primary file's preamble (text before its first entry) is kept; the secondary's
    preamble is appended under a marker only if it is not already present.

Prints counts (primary, secondary, merged, collisions). With --dry-run writes nothing.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

HEADER = re.compile(r"^## (\d{4}-\d{2}-\d{2})(.*)$")
# a file's description block that ended up mid-file because entries were prepended above it
PREAMBLE_MARK = re.compile(r"^(# |Agent-facing log|Written by |History up to |Newest on top)", re.I)


def split(text: str) -> tuple[str, list[tuple[str, str, str]]]:
    """-> (preamble, [(date, header_line, body)]) in file order."""
    lines = text.splitlines()
    pre, entries, cur, pre_mode = [], [], None, False
    for line in lines:
        m = HEADER.match(line)
        if m:
            if cur:
                entries.append(cur)
            cur = [m.group(1), line, []]
            pre_mode = False
        elif pre_mode:
            if line.strip():
                pre.append(line)
            else:
                pre_mode = False   # a blank line ends the lifted block; what follows is body again
        elif PREAMBLE_MARK.match(line):
            pre.append(line)
            pre_mode = True
        elif cur:
            cur[2].append(line)
        else:
            pre.append(line)
    if cur:
        entries.append(cur)
    return "\n".join(pre).strip("\n"), [(d, h, "\n".join(b).strip("\n")) for d, h, b in entries]


def merge(primary: str, secondary: str) -> tuple[str, dict]:
    p_pre, p_ent = split(primary)
    s_pre, s_ent = split(secondary)
    merged: dict[str, tuple[str, str, str]] = {}
    order: list[str] = []
    collisions = 0
    for d, h, b in p_ent:
        key = h.strip()
        if key not in merged:
            merged[key] = (d, h, b)
            order.append(key)
        else:  # duplicate header inside the primary itself: keep both bodies
            merged[key] = (d, h, merged[key][2] + "\n\n<!-- duplicate header in primary -->\n" + b)
    for d, h, b in s_ent:
        key = h.strip()
        if key not in merged:
            merged[key] = (d, h, b)
            order.append(key)
        elif merged[key][2].strip() != b.strip():
            collisions += 1
            merged[key] = (d, h, merged[key][2] + "\n\n<!-- secondary variant -->\n" + b)
    # newest first; stable within a date in primary-then-secondary order
    ranked = sorted(order, key=lambda k: merged[k][0], reverse=True)
    out = [p_pre] if p_pre else []
    if s_pre and s_pre not in primary:
        out.append("<!-- secondary preamble -->\n" + s_pre)
    for k in ranked:
        d, h, b = merged[k]
        out.append(h + ("\n" + b if b else ""))
    stats = {"primary": len(p_ent), "secondary": len(s_ent), "merged": len(ranked), "collisions": collisions}
    return "\n\n".join(out).rstrip("\n") + "\n", stats


def main(argv: list[str]) -> int:
    dry = "--dry-run" in argv
    args = [a for a in argv if a != "--dry-run"]
    if len(args) != 3:
        print(__doc__)
        return 2
    p, s, o = (Path(a) for a in args)
    text, stats = merge(p.read_text(errors="replace"), s.read_text(errors="replace"))
    print(f"{o.name}: primary {stats['primary']} entries, secondary {stats['secondary']}, "
          f"merged {stats['merged']}, collisions {stats['collisions']}" + ("  [dry run]" if dry else ""))
    if not dry:
        o.parent.mkdir(parents=True, exist_ok=True)
        o.write_text(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
