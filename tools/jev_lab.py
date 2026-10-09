#!/usr/bin/env python3
"""CLI and MCP entrypoint; uses an isolated local runtime when installed."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "local/jev-runtime/bin/python"
if RUNTIME.exists() and Path(sys.prefix).resolve() != RUNTIME.parent.parent.resolve():
    os.execv(str(RUNTIME), [str(RUNTIME), str(Path(__file__).resolve()), *sys.argv[1:]])

from jev.common import LabError, read_text
from jev.service import Service


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor")
    doctor.add_argument("--live", action="store_true")
    sub.add_parser("mcp")
    call = sub.add_parser("call")
    call.add_argument("tool")
    call.add_argument("--input", default="-", help="Lab JSON file or - for stdin")
    args = parser.parse_args()
    try:
        if args.command == "mcp":
            from jev.server import main as serve
            serve()
            return 0
        if args.command == "doctor":
            result = Service().doctor(args.live)
        else:
            text = sys.stdin.read(100_001) if args.input == "-" else read_text(args.input)
            if len(text.encode()) > 96_000:
                raise LabError("Input exceeds the excerpt limit")
            result = Service().call(args.tool, json.loads(text))
        print(json.dumps(result, indent=2, allow_nan=False))
        return 0
    except (LabError, ValueError, OSError) as error:
        message = str(error) if isinstance(error, LabError) else type(error).__name__
        print(json.dumps({"error": message, "context": "unavailable"}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
