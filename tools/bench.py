#!/usr/bin/env python3
"""bench.py — one read-only JSON snapshot of where the research stands, for the Bench mod.

    python3 tools/bench.py snapshot --json     # what the mod polls
    python3 tools/bench.py snapshot            # the same, as a short text summary

Local files only: no kubectl, no network, no model calls, no writes. Design and schema:
docs/design/bench-mod.md. Execution status and verification status are separate fields; a
number appears here only as a campaign's VERIFY.md states it (this script never computes one).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import index  # noqa: E402  (read_header, study_dirs, pending_decisions)

try:  # the harness owns the approval and GPU-h rules; reuse them rather than restate them
    import harness  # noqa: E402
except Exception:  # pragma: no cover - the snapshot still draws without the harness
    harness = None

SCHEMA = 0
PHASES = [("STUDY", "STUDY.md"), ("PREFLIGHT", "PREFLIGHT.md"), ("RUN", "RUN.md"),
          ("VERIFY", "VERIFY.md"), ("REPORT", "REPORT.md")]
CLOSED = ("verified", "published", "superseded")
VERDICT = re.compile(r"\b(PASS|ITERATE|ESCALATE)\b")
SINCE = "2026-09-20"   # older campaigns are archive; the index-head lists the same open set


def rel(p: Path) -> str:
    return p.relative_to(ROOT).as_posix()


def read(p: Path) -> str:
    try:
        return p.read_text(errors="replace")
    except OSError:
        return ""


def load_json(p: Path):
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return None


def section(text: str, heading: str) -> str:
    """Body of the first markdown section whose heading contains `heading`."""
    m = re.search(rf"^(#+) [^\n]*{re.escape(heading)}[^\n]*\n(.*?)(?=^#{{1,2}} |\Z)", text, re.S | re.M | re.I)
    return m.group(2) if m else ""


def tables(text: str) -> list[list[list[str]]]:
    """Every markdown table as rows of cells; the separator row is dropped."""
    out, cur = [], []
    for line in text.splitlines() + [""]:
        s = line.strip()
        if s.startswith("|") and s.endswith("|"):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
                cur.append(cells)
        elif cur:
            out.append(cur)
            cur = []
    return out


def clean(s: str) -> str:
    return re.sub(r"`|\*\*", "", s).strip()


# ---------------------------------------------------------------- studies

def review_verdicts(d: Path) -> list[dict]:
    out = []
    for f in sorted((d / "review").glob("*.md")) if (d / "review").is_dir() else []:
        m = re.match(r"([A-Z]+)_([a-z_]+?)_v(\d+)$", f.stem)
        if not m:
            continue
        phase, role, ver = m.group(1), m.group(2), int(m.group(3))
        h = index.read_header(f)
        verdict = (h.get("verdict") or "").split()[0:1]
        if not verdict:
            text = read(f)
            if re.search(r"no verdict", text[:600], re.I):   # panel reviewers leave the verdict to the arbiter
                text = ""
            pos = re.search(r"verdict", text, re.I)
            hit = VERDICT.search(text, pos.start()) if pos else None
            verdict = [hit.group(1)] if hit else []
        out.append({"phase": phase, "role": role, "version": ver,
                    "verdict": verdict[0].strip("*.") if verdict else "unparsed", "path": rel(f)})
    out.sort(key=lambda r: (r["phase"], r["version"], r["role"]))
    return out


def latest_by_phase(verdicts: list[dict]) -> dict:
    """The deciding verdict per phase: the arbiter at the highest version; a phase with no arbiter
    (critical reviewer alone, as at PREFLIGHT and RUN) takes the highest critical version."""
    best: dict = {}
    for v in verdicts:
        if v["role"] not in ("arbiter", "critical") or v["verdict"] == "unparsed":
            continue
        cur = best.get(v["phase"])
        key = (v["role"] == "arbiter", v["version"])
        if cur is None or key > (cur["role"] == "arbiter", cur["version"]):
            best[v["phase"]] = v
    return best


def frozen(d: Path, brief: dict | None) -> list[dict]:
    out = []
    for path, want in ((brief or {}).get("frozen_files") or {}).items():
        p = d / path
        try:
            have = hashlib.sha256(p.read_bytes()).hexdigest()
        except OSError:
            have = None
        out.append({"path": rel(p) if p.exists() else f"{rel(d)}/{path}",
                    "state": "missing" if have is None else ("intact" if have == want else "changed")})
    return out


def frozen_dirs(d: Path) -> list[str]:
    """RULES section 5: once RUN.md exists, the campaign's code, configs and manifests are frozen."""
    if not (d / "RUN.md").exists():
        return []
    return [rel(p) + "/" for p in sorted(d.iterdir())
            if p.is_dir() and (p.name in ("code", "configs", "settings", "eval") or p.name.startswith("manifests"))]


def handoff(d: Path) -> list[str]:
    body = section(read(d / "HANDOFF.md"), "Where things stand")
    return [l.strip()[2:] for l in body.splitlines() if l.strip().startswith("- ")][:6]


def harness_state(d: Path) -> dict | None:
    if not (d / "BRIEF.md").exists() or harness is None:
        return None
    try:
        brief = harness.load_brief(str(d))
    except Exception as e:
        return {"error": f"BRIEF.md does not load: {str(e)[:160]}"}
    state = load_json(d / "STATE.json") or {}
    try:
        approved = harness.current_approval(str(d)) is not None if (d / "APPROVAL.json").exists() else False
    except Exception:
        approved = False
    try:
        spent = harness.committed_gpu_h(state) if state.get("resources") else None
    except Exception:
        spent = None
    jobs = {}
    for obs in (state.get("observations") or {}).values():
        jobs[obs.get("status", "?")] = jobs.get(obs.get("status", "?"), 0) + 1
    notify = read(d / "NOTIFY.log").splitlines()
    return {"brief": brief, "approved": approved, "has_approval_file": (d / "APPROVAL.json").exists(),
            "gpu_h": {"spent": spent, "cap": brief.get("gpu_h_max")}, "jobs": jobs,
            "notices": state.get("notices") or [], "stopped": state.get("stopped"),
            "monitor_last_ok": (state.get("monitor") or {}).get("last_ok"),
            "notify_tail": notify[-4:]}


def study_rows() -> tuple[list[dict], list[dict]]:
    rows, gates = [], []
    for d in index.study_dirs():
        h = index.read_header(d / "STUDY.md")
        hs = harness_state(d)
        date = h.get("date") or index.date_from_name(d.name) or ""
        if not h and not hs:
            continue
        if date < SINCE:
            continue
        status = h.get("status") or ("harness" if hs else "?")
        question = h.get("question") or index.readme_heading(d) or clean(read(d / "PROPOSAL.md").split("\n", 1)[0].lstrip("# "))
        verdicts = review_verdicts(d)
        deciding = latest_by_phase(verdicts)
        phases = []
        for name, f in PHASES:
            p = d / f
            ph = index.read_header(p) if p.exists() else {}
            phases.append({"phase": name, "exists": p.exists(), "path": rel(p) if p.exists() else None,
                           "status": ph.get("status"), "verdict": (deciding.get(name) or {}).get("verdict")})
        current = next((ph["phase"] for ph in reversed(phases) if ph["exists"]), "STUDY")
        is_open = not any(status.lower().startswith(c) for c in CLOSED)
        row = {"id": d.name, "dir": rel(d), "date": date, "type": h.get("type", "harness" if hs else ""),
               "question": question, "status": status, "phase": current, "open": is_open,
               "phases": phases, "verdicts": verdicts, "handoff": handoff(d),
               "frozen": frozen(d, hs.get("brief") if hs and "brief" in hs else None),
               "frozen_dirs": frozen_dirs(d) if is_open else [],
               "code_sha": h.get("code_sha"), "harness": None}
        if hs:
            row["harness"] = {k: v for k, v in hs.items() if k != "brief"}
        rows.append(row)
        if not is_open:
            continue

        # gates: what is waiting on Kai, with what it commits and where it is written
        prog = load_json(d / "PROGRAM.json")
        if prog is not None and not prog.get("signed_by_kai"):
            gates.append({"study": d.name, "kind": "program-unsigned",
                          "what": f"PROGRAM.json not signed (mode {prog.get('mode', '?')}); its launches are not approved",
                          "commits": caps_line(prog), "source": rel(d / "PROGRAM.json"),
                          "prompt": f"Review the unsigned PROGRAM.json for {d.name} and tell me what signing it commits."})
        if hs and "error" not in hs and not hs["approved"]:
            why = "APPROVAL.json does not match the BRIEF authority block" if hs["has_approval_file"] else "no APPROVAL.json"
            gates.append({"study": d.name, "kind": "approval-void", "what": f"{why}; harness submissions refused",
                          "commits": f"up to {hs['gpu_h']['cap']} GPU-h", "source": rel(d / "BRIEF.md"),
                          "prompt": f"Review the approval for {d.name}: what changed in the BRIEF authority block?"})
        reached = [p["phase"] for p in phases if p["exists"]]
        for ph, v in deciding.items():
            # an escalation is settled once a later phase artifact exists
            is_settled = ph in reached and reached.index(ph) < len(reached) - 1
            if v["verdict"] == "ESCALATE" and not is_settled:
                gates.append({"study": d.name, "kind": "escalate", "what": f"{ph} {v['role']} v{v['version']} escalated",
                              "commits": "", "source": v["path"],
                              "prompt": f"Summarise the ESCALATE in {v['path']} and what decision it needs from me."})
        for n in (hs or {}).get("notices") or []:
            gates.append({"study": d.name, "kind": "hold", "what": str(n)[:200], "commits": "",
                          "source": rel(d / "STATE.json"),
                          "prompt": f"Explain the harness notice for {d.name}: {str(n)[:120]}"})
        if hs and hs.get("stopped"):
            gates.append({"study": d.name, "kind": "hold", "what": f"harness stopped: {str(hs['stopped'])[:160]}",
                          "commits": "", "source": rel(d / "STATE.json"),
                          "prompt": f"Why did the harness stop {d.name}, and what does restarting it need?"})
    rows.sort(key=lambda r: r["date"], reverse=True)
    for item in index.pending_decisions():
        gates.append({"study": "", "kind": "queued-for-kai", "what": clean(item)[:220], "commits": "",
                      "source": "SYSTEM.md", "prompt": f"Walk me through this pending decision: {clean(item)[:160]}"})
    return rows, gates


def caps_line(prog: dict) -> str:
    caps = prog.get("caps") or prog.get("spend_caps") or {}
    if isinstance(caps, dict) and caps:
        return ", ".join(f"{k} {v}" for k, v in list(caps.items())[:4])
    return ""


# ---------------------------------------------------------------- hypotheses

def hypothesis_rows(studies: list[dict]) -> list[dict]:
    out = []
    for s in studies:
        if not s["open"]:
            continue
        d = ROOT / s["dir"]
        text = read(d / "STUDY.md")
        hyp = {}
        for t in tables(text):
            head = [c.lower() for c in t[0]]
            if head[:2] == ["#", "hypothesis"] and len(head) >= 4:
                for r in t[1:]:
                    hyp[clean(r[0]).split()[0]] = {"statement": clean(r[1]), "prediction": clean(r[2]),
                                                   "refutation": clean(r[3])}
            elif head[:3] == ["hyp", "round", "lead"] and len(head) >= 5:
                for r in t[1:]:
                    k = clean(r[0]).split()[0]
                    hyp.setdefault(k, {}).update({"round": clean(r[1]), "lead_if": clean(r[2]),
                                                  "not_supported_if": clean(r[3]), "otherwise": clean(r[4])})
        if not hyp:
            continue
        readout = [p for p in d.rglob("readout*.json")
                   if not any(x in p.parts for x in ("code", "superseded-1f7c4e")) and "manifests" not in p.parent.name
                   and "job" not in p.stem]
        for k, v in hyp.items():
            out.append({"study": s["id"], "id": k, **v,
                        "readout": rel(readout[0]) if readout else None,
                        "state": "readout exists; read it by hand" if readout else "awaiting readout"})
    return out


# ---------------------------------------------------------------- numbers

def number_rows(studies: list[dict]) -> tuple[list[dict], list[dict]]:
    nums, gaps = [], []
    for s in studies:
        d = ROOT / s["dir"]
        v = d / "VERIFY.md"
        text = read(v)
        if not text:
            continue
        cfg = re.search(r"input set (\S+?),\s*N\s*=\s*(\d+)", text)
        status_par = re.search(r"\*\*Status of this verification\.\*\*\s*(.*?)\n\n", text, re.S)
        caveat = re.sub(r"\s+", " ", status_par.group(1)).strip() if status_par else ""
        base = {"study": s["id"], "source": rel(v), "status": "verified" if s["phases"][3]["exists"] else "?",
                "input_set": cfg.group(1) if cfg else None, "N": int(cfg.group(2)) if cfg else None,
                "caveat": caveat, "host": None, "in_record": None, "lead_or_readout": "readout"}
        for t in tables(text):
            head = [c.lower() for c in t[0]]
            if any("mean ± sd" in c for c in head) and "seeds" in head:
                for r in t[1:]:
                    parts = [p.strip() for p in r[1].split("·")]
                    nums.append({**base, "claim": f"{clean(r[0])} {parts[0]}", "quantity": clean(r[0]),
                                 "metric": parts[0], "split": parts[1] if len(parts) > 1 else None,
                                 "n": int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None,
                                 "value": clean(r[2]), "interval": "mean ± sample sd (ddof 1)",
                                 "seeds": int(r[3]) if r[3].isdigit() else None})
            elif any("mean δ" in c for c in head) and any("interval" in c for c in head):
                n_head = re.search(r"n = ([\d,]+)", t[0][0])
                for r in t[1:]:
                    n = re.search(r"n = ([\d,]+)", r[0]) or n_head
                    gaps.append({**base, "comparison": clean(r[0]), "delta": clean(r[1]), "interval": clean(r[2]),
                                 "seeds_lower": clean(r[3]), "verdict": clean(r[4]).split(";")[0],
                                 "n": int(n.group(1).replace(",", "")) if n else None})
    return nums, gaps


# ---------------------------------------------------------------- snapshot

def snapshot() -> dict:
    studies, gates = study_rows()
    nums, gaps = number_rows(studies)
    open_ = [s for s in studies if s["open"]]
    active = next((s for s in open_ if s["harness"]), open_[0] if open_ else None)
    band = {"active": active["id"] if active else None, "phase": active["phase"] if active else None,
            "waiting": len(gates), "jobs": {}, "gpu_h": None}
    for s in open_:
        h = s["harness"] or {}
        for k, n in (h.get("jobs") or {}).items():
            band["jobs"][k] = band["jobs"].get(k, 0) + n
        if h.get("gpu_h") and band["gpu_h"] is None:
            band["gpu_h"] = {**h["gpu_h"], "study": s["id"]}
    return {"schema": SCHEMA, "at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "band": band, "studies": studies, "gates": gates, "hypotheses": hypothesis_rows(studies),
            "numbers": nums, "gaps": gaps,
            "limits": ["Numbers come only from VERIFY.md tables; lab-pod and home-PC values are not shown.",
                       "No entered-the-record mark exists yet (SYSTEM.md decision point): in_record is null.",
                       "Hypothesis rows carry no verdict until a readout file exists."]}


def main(argv: list[str]) -> int:
    if not argv or argv[0] != "snapshot":
        print(__doc__)
        return 2
    snap = snapshot()
    if "--json" in argv:
        json.dump(snap, sys.stdout, separators=(",", ":"))
        return 0
    b = snap["band"]
    print(f"active {b['active']} ({b['phase']}); {b['waiting']} waiting on Kai; jobs {b['jobs']}; gpu_h {b['gpu_h']}")
    for g in snap["gates"]:
        print(f"  gate {g['kind']:16} {g['study']:32} {g['what'][:90]}")
    for s in snap["studies"]:
        if s["open"]:
            print(f"  {s['id']:36} {s['phase']:9} {s['status'][:40]}")
    print(f"  {len(snap['hypotheses'])} hypotheses, {len(snap['numbers'])} numbers, {len(snap['gaps'])} gaps")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
