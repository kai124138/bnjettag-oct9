#!/usr/bin/env python3
"""index.py — one table of everything, nothing moves.

    python3 tools/index.py init     # add STUDY.md stubs / doc headers where missing (idempotent)
    python3 tools/index.py build    # write INDEX.md and .claude/memory/index-head.md
    python3 tools/index.py check    # context budget: CLAUDE.md + imports must stay under the cap

The attic moved things and hid them. This indexes them in place. A study is any directory
under a STUDY_ROOT that has (or gets) a STUDY.md with a small YAML header; a document is any
markdown file under a DOC_ROOT with a small header. Code trees are listed with their git
state so the canonical-tree decision has its facts in front of it. Stubs are marked as
auto-generated and carry status `unreviewed`; they are never provenance.
"""
from __future__ import annotations

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Layout-agnostic: works in the lab repo (studies under local/) and in the unified workspace
# (studies under campaigns/). Only roots that exist are scanned.
STUDY_ROOTS = ["campaigns", "local"]
SKIP_DIRS = {"outputs", "store", "wandb", "__pycache__", ".ipynb_checkpoints", "notebooks"}
DOC_ROOTS = [".", "docs", "messages", "nrp-lab", "local"]   # *.md directly under these (docs recursive)
DOC_SKIP = {"INDEX.md", "CLAUDE.md", "proposed-user-CLAUDE.md", "MOVED.md"}
TREE_ROOTS = [".", "publication", "published/bnjettag_results", "published/bnjettag-code",
              "published/bnjettag-methodology",
              "publication-engram-20260921", "publication-status-20260921",
              "publication-status-20260920", "research"]
LOG = ROOT / ".claude/memory/experiment-log.md"
SYSTEM = ROOT / "SYSTEM.md"
HEAD_OUT = ROOT / ".claude/memory/index-head.md"
INDEX_OUT = ROOT / "INDEX.md"
CONTEXT_CAP = 150   # lines: CLAUDE.md plus everything it imports
TODAY = dt.date.today().isoformat()

STATUSES = ("scratch", "running", "verified", "published", "superseded", "unreviewed")


# ---------------------------------------------------------------- headers

def read_header(path: Path) -> dict:
    """Minimal YAML-ish front matter: `key: value` lines between two `---` lines."""
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end < 0:
        return {}
    out = {}
    for line in text[3:end].splitlines():
        if ":" in line and not line.startswith((" ", "#")):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip()
    return out


def write_header(path: Path, fields: dict, body: str) -> None:
    lines = ["---"] + [f"{k}: {v}" for k, v in fields.items()] + ["---", ""]
    path.write_text("\n".join(lines) + body)


def date_from_name(name: str) -> str | None:
    m = re.search(r"(\d{4})-?(\d{2})-?(\d{2})", name)
    if m:
        y, mo, d = m.groups()
        try:
            return dt.date(int(y), int(mo), int(d)).isoformat()
        except ValueError:
            return None
    return None


def dir_date(d: Path) -> str:
    stamps = [p.stat().st_mtime for p in d.rglob("*") if p.is_file()]
    t = min(stamps) if stamps else d.stat().st_mtime
    return dt.date.fromtimestamp(t).isoformat()


def log_question(date: str | None) -> str:
    """Experiment-log entry header on that date, if any: '## 2026-09-23 — <text>'."""
    if not date or not LOG.exists():
        return ""
    for line in LOG.read_text(errors="replace").splitlines():
        m = re.match(rf"##\s+{re.escape(date)}\s+[—–-]+\s+(.*)", line)
        if m:
            return m.group(1).strip()
    return ""


def readme_heading(d: Path) -> str:
    for name in ("README.md", "readme.md"):
        p = d / name
        if p.exists():
            for line in p.read_text(errors="replace").splitlines():
                if line.startswith("# "):
                    return line[2:].strip()
    return ""


# ---------------------------------------------------------------- init

def study_dirs() -> list[Path]:
    out = []
    for r in STUDY_ROOTS:
        base = ROOT / r
        if not base.is_dir():
            continue
        for d in sorted(base.iterdir()):
            if d.is_dir() and d.name not in SKIP_DIRS and not d.name.startswith("."):
                out.append(d)
    return out


def init_studies() -> int:
    n = 0
    for d in study_dirs():
        f = d / "STUDY.md"
        if f.exists():
            continue
        date = date_from_name(d.name) or dir_date(d)
        slug = re.sub(r"[-_]?\d{8}|[-_]?\d{4}-\d{2}-\d{2}", "", d.name).strip("-_") or d.name
        q = readme_heading(d) or log_question(date)
        fields = {
            "id": f"{date}-{slug}",
            "date": date,
            "type": slug.split("-")[0],
            "status": "unreviewed",
            "question": q,
            "supersedes": "",
            "superseded_by": "",
            "code_sha": "",
            "wandb": "",
            "results": "",
            "generated": f"auto-stub {TODAY} by tools/index.py init; not provenance, edit by hand",
        }
        body = ("\n# " + (q or d.name) + "\n\n"
                "<!-- Phase artifacts live beside this file: PREFLIGHT.md, RUN.md, VERIFY.md, REPORT.md. -->\n"
                "**Question.** \n\n**Design.** arms / seeds / selection rule / falsifier\n\n"
                "**Result.** \n\n**Interpretation.** \n")
        write_header(f, fields, body)
        n += 1
    return n


def doc_files() -> list[Path]:
    seen, out = set(), []
    for r in DOC_ROOTS:
        for p in doc_files_under(r):
            if p not in seen:
                seen.add(p)
                out.append(p)
    return out


def init_docs() -> int:
    n = 0
    for p in doc_files():
        if read_header(p):
            continue
        text = p.read_text(errors="replace")
        title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), p.stem)
        date = date_from_name(p.name) or dt.date.fromtimestamp(p.stat().st_mtime).isoformat()
        write_header(p, {"title": title, "status": "current", "date": date}, "\n" + text)
        n += 1
    return n


# ---------------------------------------------------------------- build

def git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                              timeout=10).stdout.strip()
    except Exception:  # noqa: BLE001
        return ""


def trees() -> list[dict]:
    out = []
    for r in TREE_ROOTS:
        p = ROOT / r
        if not p.exists():
            continue
        real = p.resolve()
        out.append({
            "name": r + ("  →  " + str(real) if p.is_symlink() else ""),
            "head": git(real, "rev-parse", "--short", "HEAD") or "?",
            "date": git(real, "log", "-1", "--format=%cs") or "?",
            "dirty": len(git(real, "status", "--porcelain").splitlines()) if git(real, "rev-parse", "HEAD") else "?",
        })
    return out


def studies() -> list[dict]:
    rows = []
    for d in study_dirs():
        h = read_header(d / "STUDY.md")
        if not h:
            continue
        phases = "".join(ch for ch, f in (("P", "PREFLIGHT.md"), ("R", "RUN.md"), ("V", "VERIFY.md"), ("T", "REPORT.md"))
                         if (d / f).exists()) or "–"
        rows.append({"dir": d.relative_to(ROOT).as_posix(), "date": h.get("date", ""), "status": h.get("status", "?"),
                     "type": h.get("type", ""), "question": h.get("question", ""), "phases": phases,
                     "superseded_by": h.get("superseded_by", ""), "stub": "generated" in h})
    rows.sort(key=lambda r: r["date"], reverse=True)
    return rows


def doc_files_under(root: str) -> list[Path]:
    base = ROOT / root
    if not base.is_dir():
        return []
    it = base.rglob("*.md") if root == "docs" else base.glob("*.md")
    return [p for p in sorted(it) if p.name not in DOC_SKIP and "/retired/" not in str(p)
            and "/archive/" not in str(p) and "/templates/" not in str(p)]


def pending_decisions() -> list[str]:
    if not SYSTEM.exists():
        return []
    text = SYSTEM.read_text(errors="replace")
    m = re.search(r"^## Pending decisions\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    if not m:
        return []
    return [l.strip()[2:].strip() for l in m.group(1).splitlines() if l.strip().startswith("- ")]


def newest_log_headers(n: int = 3) -> list[str]:
    if not LOG.exists():
        return []
    return [l[3:].strip() for l in LOG.read_text(errors="replace").splitlines() if l.startswith("## ")][:n]


def build() -> None:
    st, tr, docs = studies(), trees(), doc_files()
    lines = [f"# Index  (built {TODAY} by tools/index.py; edit STUDY.md headers, not this file)", "",
             "## Campaigns  (newest first; the type is the kind of job; phases: P preflight, R run, V verify, T report)", "",
             "| date | type | status | campaign | phases | question |", "| --- | --- | --- | --- | --- | --- |"]
    for r in st:
        q = r["question"] or "*(no question recorded)*"
        if r["superseded_by"]:
            q += f" → superseded by {r['superseded_by']}"
        tag = " *(stub)*" if r["stub"] else ""
        lines.append(f"| {r['date']} | {r['type']} | {r['status']} | `{r['dir']}`{tag} | {r['phases']} | {q} |")
    lit = ROOT / "literature" / "INDEX.md"
    if not lit.exists():
        lit = ROOT / "research" / "docs" / "literature" / "INDEX.md"
    if lit.exists():
        n = sum(1 for p in lit.parent.rglob("*.md") if p.name != "INDEX.md")
        lines += ["", f"## Literature  ({n} notes; entry point `{lit.relative_to(ROOT).as_posix()}`, never glob the folder)"]
    lines += ["", "## Code trees  (the canonical-tree decision needs these facts)", "",
              "| tree | HEAD | last commit | uncommitted files |", "| --- | --- | --- | --- |"]
    for t in tr:
        lines.append(f"| `{t['name']}` | {t['head']} | {t['date']} | {t['dirty']} |")
    lines += ["", "## Documents", "", "| date | status | document | title |", "| --- | --- | --- | --- |"]
    for p in sorted(docs, key=lambda p: read_header(p).get("date", ""), reverse=True):
        h = read_header(p)
        lines.append(f"| {h.get('date', '')} | {h.get('status', '')} | `{p.relative_to(ROOT).as_posix()}` | {h.get('title', p.stem)} |")
    sessions = sorted((ROOT / "sessions").glob("*.md")) if (ROOT / "sessions").is_dir() else []
    if sessions:
        lines += ["", f"## Sessions  ({len(sessions)} notes in `sessions/`, newest `{sessions[-1].name}`)"]
    INDEX_OUT.write_text("\n".join(lines) + "\n")

    # the head: what a session needs at start, capped
    study_root = next((r for r in STUDY_ROOTS if (ROOT / r).is_dir()), "campaigns")
    head = [f"<!-- generated {TODAY} by tools/index.py build; do not edit -->",
            "## Index head", "",
            f"Full table: `INDEX.md`. A campaign is `{study_root}/<date>-<type>/` with STUDY → PREFLIGHT → RUN → VERIFY → REPORT."]
    open_rows = [r for r in st if r["status"] in ("running", "scratch", "verified", "unreviewed", "designed", "frozen") and not r["superseded_by"]][:8]
    if open_rows:
        head += ["", "**Open campaigns** (running / unverified / unpublished):"]
        for r in open_rows:
            head.append(f"- {r['date']} `{r['dir']}` [{r['type']}; {r['status']}, {r['phases']}] {r['question'] or '(no question recorded)'}"[:160])
    pend = pending_decisions()
    if pend:
        head += ["", "**Pending decisions (Kai):**"] + [f"- {p}" for p in pend[:5]]
    head += ["", "**Code trees:** " + "; ".join(f"`{t['name'].split('  →')[0]}` {t['head']} ({t['dirty']} dirty)" for t in tr)]
    logs = newest_log_headers()
    if logs:
        head += ["", "**Newest experiment-log entries:**"] + [f"- {l}" for l in logs]
    HEAD_OUT.write_text("\n".join(head[:60]) + "\n")
    print(f"INDEX.md: {len(st)} studies, {len(tr)} trees, {len(docs)} docs; index-head.md: {min(len(head), 60)} lines")


# ---------------------------------------------------------------- check

def context_lines() -> tuple[int, list[str]]:
    claude = ROOT / "CLAUDE.md"
    if not claude.exists():
        return 0, []
    text = claude.read_text(errors="replace")
    total, parts = len(text.splitlines()), ["CLAUDE.md"]
    for m in re.finditer(r"^@(\S+)", text, re.M):
        p = ROOT / m.group(1)
        if p.exists():
            total += len(p.read_text(errors="replace").splitlines())
            parts.append(m.group(1))
    return total, parts


def check() -> int:
    total, parts = context_lines()
    ok = total <= CONTEXT_CAP
    print(f"context budget: {total} lines across {' + '.join(parts)} (cap {CONTEXT_CAP}) -> {'ok' if ok else 'OVER'}")
    return 0 if ok else 1


def main(argv: list[str]) -> int:
    cmd = argv[0] if argv else "build"
    if cmd == "init":
        print(f"stubs written: {init_studies()} STUDY.md, {init_docs()} doc headers")
        return 0
    if cmd == "build":
        build()
        return check()
    if cmd == "check":
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
