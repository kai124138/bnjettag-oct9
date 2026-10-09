from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAX_BYTES = 96_000


class LabError(ValueError):
    """A bounded, user-readable failure without request bodies or credentials."""


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".pending-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def credential() -> tuple[str | None, str]:
    """Read the existing local key without executing a shell profile."""
    key = os.environ.get("TYPESAFE_API_KEY")
    if key:
        return key, "environment"
    path = Path.home() / ".typesafe.env"
    if not path.is_file():
        return None, "missing"
    if path.stat().st_mode & 0o077:
        raise LabError("~/.typesafe.env must be private: chmod 600 ~/.typesafe.env")
    if path.stat().st_size > 8192:
        raise LabError("TypeSafe environment file is unexpectedly large")
    for line in path.read_text().splitlines():
        parts = shlex.split(line, comments=True)
        if parts and parts[0] == "export":
            parts = parts[1:]
        if len(parts) == 1 and parts[0].startswith("TYPESAFE_API_KEY="):
            value = parts[0].partition("=")[2]
            if value and not any(c in value for c in "\n\r`$;"):
                return value, "private local environment file"
    return None, "missing"


def reject_secrets(value: object) -> None:
    text = canonical(value).decode()
    key, _ = credential()
    if (key and key in text) or re.search(
        r"(?:-----BEGIN .*PRIVATE KEY|\bBearer\s+[A-Za-z0-9_.-]{12,}|"
        r"\b(?:sk-(?:or-)?|ts_|jv_live_)[A-Za-z0-9_-]{16,}|"
        r"(?:API_KEY|PASSWORD|TOKEN)\s*[=:]\s*[\"']?[A-Za-z0-9_-]{16,})",
        text, re.I,
    ):
        raise LabError("Input contains possible credentials; supply a redacted excerpt")


def local_path(path: str, root: Path = ROOT) -> Path:
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise LabError("Path must remain inside the canonical lab")
    parts = resolved.relative_to(root.resolve()).parts
    forbidden = {".git", ".ssh", ".venv", "jev-runtime", "_attic", "archive", "research"}
    if forbidden.intersection(parts) or re.search(
        r"(?:^\.env|api[-_]?key|credentials|secrets|\.pem$|\.key$|kubeconfig)",
        resolved.name, re.I,
    ):
        raise LabError("Credential, runtime, and historical paths are excluded")
    return resolved


def read_text(path: str, root: Path = ROOT) -> str:
    target = local_path(path, root)
    if not target.is_file() or target.stat().st_size > MAX_BYTES:
        raise LabError("Source is missing, not a file, or exceeds the excerpt limit")
    try:
        with target.open("rb") as stream:
            data = stream.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise LabError("Source exceeds the excerpt limit")
        text = data.decode("utf-8")
    except (UnicodeError, OSError):
        raise LabError("Source must be a readable text file") from None
    reject_secrets(text)
    return text


def policy_snapshot(root: Path = ROOT) -> dict:
    paths = ["AGENTS.md", "CLAUDE.md", "SYSTEM.md", "RULES.md",
             "docs/methodology/03-phases.md", "docs/methodology/06-review.md",
             "docs/conventions/jet-tagging-metrics.md",
             "docs/conventions/quantization-and-cost.md",
             "docs/infrastructure/run-handoff.md", "tools/jev/catalog.json"]
    return {path: hashlib.sha256(read_text(path, root).encode()).hexdigest() for path in paths}
