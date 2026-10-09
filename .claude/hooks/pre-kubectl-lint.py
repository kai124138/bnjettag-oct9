#!/usr/bin/env python3
"""PreToolUse hook: no manifest reaches the cluster without passing nrp_doctor lint.

Claude Code calls this before every Bash tool call with the tool input as JSON on stdin.
Anything that is not `kubectl (apply|create|replace) ... -f <file>` passes through in
milliseconds. A matching command runs `nrp-lab/nrp_doctor.py lint` on each named file;
a lint ERROR, a missing file, or a lint that cannot run blocks the call (exit 2, message on
stderr, which Claude sees). Warnings are shown but do not block.

The rule this encodes: docs/infrastructure/nrp-nautilus-setup.md, "run it before any
kubectl apply". It used to be a sentence; now it is a gate.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

VERB = re.compile(r"\bkubectl\b(?P<rest>[^|;&\n]*)")
APPLY = re.compile(r"\b(apply|create|replace)\b")
FILE = re.compile(r"(?:^|\s)(?:-f|--filename)(?:=|\s+)(?P<path>[^\s;|&]+)")


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except Exception:
        return 0
    if event.get("tool_name") != "Bash":
        return 0
    command = (event.get("tool_input") or {}).get("command") or ""
    # Campaign 2026-10-08-discovery-350k: its GPU-hour limit is checked by tools/harness.py
    # submit, which calls run_handoff itself. A direct submit of its handoffs would skip that check.
    # Only an actual invocation counts (a command segment that runs run_handoff.py launch --submit),
    # not text that mentions it, e.g. inside a heredoc.
    in_campaign_dir = "discovery-350k" in str(event.get("cwd") or "")
    # Heredoc bodies are data (documentation, files being written), not commands.
    commands_only = re.sub(r"<<-?\s*['\"]?(\w+)['\"]?[^\n]*\n.*?\n\s*\1\s*(?:\n|$)", "\n", command, flags=re.S)
    for segment in re.split(r"\n|;|&&|\|\||\|", commands_only):
        if (re.match(r"\s*(?:\S*python3?\s+)?\S*run_handoff\.py\s+launch\b", segment)
                and "--submit" in segment
                and ("discovery-350k" in segment or in_campaign_dir)):
            print("BLOCKED: handoffs of campaign 2026-10-08-discovery-350k are submitted only "
                  "through `python3 tools/harness.py submit` (GPU-hour limit and reservation).",
                  file=sys.stderr)
            return 2
    if "kubectl" not in command:
        return 0

    targets, stdin_used = [], False
    for m in VERB.finditer(command):
        rest = m.group("rest")
        if not APPLY.search(rest):
            continue
        for f in FILE.finditer(rest):
            p = f.group("path").strip("'\"")
            if p == "-":
                stdin_used = True
            else:
                targets.append(p)
    if not targets and not stdin_used:
        return 0

    cwd = Path(event.get("cwd") or os.getcwd())
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
    doctor = root / "nrp-lab" / "nrp_doctor.py"
    if stdin_used:
        print("BLOCKED: stdin manifests cannot carry a verified local run handoff. "
              "Use tools/run_handoff.py for Jobs.", file=sys.stderr)
        return 2

    failures = []
    for t in targets:
        path = (cwd / t).resolve() if not Path(t).is_absolute() else Path(t)
        if not path.exists():
            failures.append(f"{t}: file not found from {cwd}")
            continue
        # Generated campaign JSON Jobs must pass the handoff launcher, which validates
        # checksums and calls nrp_doctor itself. ConfigMaps keep the existing lint path.
        try:
            value = json.loads(path.read_text())
            objects = value.get('items', []) if value.get('kind') == 'List' else [value]
            is_job = any(obj.get('kind') in ('Job', 'CronJob') for obj in objects)
        except (ValueError, OSError, AttributeError):
            # YAML Jobs require explicit conversion/review; never silently skip them.
            is_job = bool(re.search(r'(?m)^\s*kind:\s*(?:Job|CronJob)\s*$', path.read_text()))
        if is_job:
            failures.append(f"{t}: direct Job submission blocked. Prepare and validate a run "
                            "handoff, then use tools/run_handoff.py launch (offline by default).")
            continue
        try:
            run = subprocess.run([sys.executable, str(doctor), "lint", str(path)],
                                 capture_output=True, text=True, timeout=100, cwd=str(root))
        except subprocess.TimeoutExpired:
            failures.append(f"{t}: nrp_doctor lint timed out (cluster unreachable?). "
                            f"Refusing to launch unlinted; run the lint by hand.")
            continue
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{t}: nrp_doctor lint could not run: {exc}")
            continue
        out = (run.stdout + run.stderr).strip()
        # nrp_doctor lint exits 0 clean, 1 warnings only, 2 on any ERROR. Only 2 blocks.
        if run.returncode >= 2:
            failures.append(f"{t}: lint ERROR (exit {run.returncode})\n{out}")
        elif run.returncode == 1:
            print(f"pre-kubectl-lint: {t} passed with WARNINGS (read them; they have cost runs before)\n{out}",
                  file=sys.stderr)
        elif out:
            print(f"pre-kubectl-lint: {t} passed lint\n{out}", file=sys.stderr)

    if failures:
        print("BLOCKED by pre-kubectl-lint: fix the manifest, then re-run.\n" + "\n\n".join(failures),
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
