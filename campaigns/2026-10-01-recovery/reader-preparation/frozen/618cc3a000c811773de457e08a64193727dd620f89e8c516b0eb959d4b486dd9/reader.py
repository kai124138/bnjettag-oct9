#!/usr/bin/env python3
"""Finite read-only PVC evidence staging and loopback content-hash export."""
import argparse
import hashlib
import http.server
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time

from recovery_filters import cache_identity, credential_json, redact

METADATA = ("config.json", "data_info.json", "latest.json", "state.json", "DIVERGED.json",
            "RSS_GATE_FAIL.json", "source_manifest.json", "input_std.json", "COMPLETE.json",
            "TRAINING_COMPLETE.json", "VERIFIED_COMPLETE.json", "screen_result.json")
CHECKPOINTS = ("state.json", "model.keras", "optimizer.npz", "model_best.keras",
               "model_best_auc_feasible.keras", "model_min_ebops.keras", "model_unconstrained.keras")
MAX_FILE = {".json": 2 << 20, ".log": 16 << 20, ".keras": 128 << 20, ".npz": 128 << 20}
MAX_TOTAL = 2 << 30
MAX_FILES = 640
MAX_LOGS = 128


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def verify_bundle(path, expected):
    raw = path.read_bytes()
    if sha(raw) != expected:
        raise ValueError("bundle identity mismatch")
    bundle = json.loads(raw)
    for name, digest in bundle["files"].items():
        if not re.fullmatch(r"[A-Za-z0-9_.-]+", name) or sha((path.parent / name).read_bytes()) != digest:
            raise ValueError("payload identity mismatch")
    if bundle["authorization_status"] != "pending_explicit_recovery_exception":
        raise ValueError("unexpected preparation state")
    return bundle


def parts(path):
    if not isinstance(path, str) or not path.startswith("/data/"):
        raise ValueError("outside PVC root")
    values = path[len("/data/"):].split("/")
    if not values or any(not p or p in {".", ".."} or "\\" in p or "\x00" in p for p in values):
        raise ValueError("unsafe path")
    return values


def state(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class PVC:
    """Descriptor-relative traversal: reject symlinks and nonregular final objects."""
    def __init__(self, root):
        self.fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)

    def open(self, path, directory=False):
        tokens = parts(path)
        fd = os.dup(self.fd)
        try:
            for index, token in enumerate(tokens):
                is_dir = index < len(tokens) - 1 or directory
                flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
                if is_dir:
                    flags |= os.O_DIRECTORY
                nxt = os.open(token, flags, dir_fd=fd)
                os.close(fd)
                fd = nxt
            mode = os.fstat(fd).st_mode
            if not (stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)):
                raise ValueError("special object refused")
            result, fd = fd, None
            return result
        finally:
            if fd is not None:
                os.close(fd)

    def inspect(self, path, directory=False):
        fd = self.open(path, directory)
        try:
            return state(os.fstat(fd))
        finally:
            os.close(fd)

    def list(self, path):
        fd = self.open(path, True)
        try:
            return sorted(os.listdir(fd))
        finally:
            os.close(fd)

    def close(self):
        os.close(self.fd)


class Export:
    def __init__(self, pvc, target, scope, bundle_sha, deadline):
        self.pvc, self.target, self.scope, self.deadline = pvc, target, scope, deadline
        target.mkdir(parents=True, exist_ok=False)
        self.blobs = target / "blobs"
        self.blobs.mkdir()
        self.rows, self.copied, self.total = [], {}, 0
        self.receipt = {"schema_version": 1, "bundle_sha256": bundle_sha, "files": self.rows,
                        "scope_sha256": sha(encoded(scope)), "cache_identities": [],
                        "checkpoint_selections": [], "status": "staging",
                        "claim": "recovered bytes only; no dataset rehash, model load, scientific or terminal clearance"}

    def check(self):
        if time.monotonic() >= self.deadline:
            raise TimeoutError("reader deadline")

    def copy(self, path):
        self.check()
        if path in self.copied:
            return self.copied[path]
        if len(self.rows) >= MAX_FILES:
            raise ValueError("file count budget")
        row = {"pvc_path": path, "accepted": False}
        self.rows.append(row)
        self.copied[path] = row
        temporary = self.target / "pending"
        try:
            suffix = PurePosixPath(path).suffix
            limit = MAX_FILE[suffix]
            fd = self.pvc.open(path)
            try:
                before = state(os.fstat(fd))
                if before[2] > limit or self.total + before[2] > MAX_TOTAL:
                    raise ValueError("byte budget")
                digest, size = hashlib.sha256(), 0
                with temporary.open("xb") as out:
                    while True:
                        self.check()
                        raw = os.read(fd, 1 << 20)
                        if not raw:
                            break
                        size += len(raw)
                        if size > limit or self.total + size > MAX_TOTAL:
                            raise ValueError("byte budget")
                        digest.update(raw)
                        out.write(raw)
                after = state(os.fstat(fd))
            finally:
                os.close(fd)
            row.update(source_sha256=digest.hexdigest(), source_bytes=size)
            if before != after or before != self.pvc.inspect(path) or size != before[2]:
                raise ValueError("source changed during read")
            row["source_stability"] = "unchanged_during_read"
            row["source_state"] = list(before)
            if suffix in {".json", ".log"}:
                raw = temporary.read_bytes()
                if suffix == ".json":
                    if credential_json(json.loads(raw)):
                        raise ValueError("possible credential in JSON")
                else:
                    raw = redact(raw.decode("utf-8", errors="replace")).encode()
                    if len(raw) > limit:
                        raise ValueError("sanitized log exceeds byte limit")
                    temporary.write_bytes(raw)
            stored_sha = sha(temporary.read_bytes()) if suffix in {".json", ".log"} else digest.hexdigest()
            stored_size = temporary.stat().st_size
            destination = self.blobs / stored_sha
            if destination.exists():
                if destination.stat().st_size != stored_size:
                    raise ValueError("content identity collision")
                temporary.unlink()
            else:
                temporary.rename(destination)
                destination.chmod(0o444)
            self.total += size
            row.update(accepted=True, status="sanitized_log_derivative" if suffix == ".log" else "copied",
                       stored_sha256=stored_sha, stored_bytes=stored_size)
        except FileNotFoundError:
            row["status"] = "missing_or_disappeared"
        except (ValueError, KeyError, UnicodeError, OSError) as error:
            row.update(status="refused_or_unavailable", reason=type(error).__name__)
        finally:
            temporary.unlink(missing_ok=True)
        return row

    def run(self):
        try:
            for cache in self.scope["caches"]:
                for name in ("data_info.json", "READY.json"):
                    self.copy(str(PurePosixPath(cache["path"]).parent / name))
                row = self.copied[cache["path"]]
                identity = cache_identity(json.loads((self.blobs / row["stored_sha256"]).read_bytes()), cache) if row["accepted"] else {"status": "context unavailable"}
                self.receipt["cache_identities"].append({"path": cache["path"], **identity})
            for run in self.scope["runs"]:
                directory = run["run_dir"]
                for name in METADATA:
                    self.copy(directory + "/" + name)
                pointer = self.copied[directory + "/latest.json"]
                selected = {"run_dir": directory, "pointer_status": pointer["status"],
                            "pointer_sha256": pointer.get("stored_sha256"), "generation": None, "checkpoints": []}
                self.receipt["checkpoint_selections"].append(selected)
                dirs = [(directory + "/snapshots/epoch-0500", "snapshot")] if run["kind"] == "chang_b5" else []
                if pointer["accepted"]:
                    value = json.loads((self.blobs / pointer["stored_sha256"]).read_bytes())
                    leaf = value.get("checkpoint", "") if isinstance(value, dict) else ""
                    if isinstance(leaf, str) and re.fullmatch(r"epoch-[A-Za-z0-9_-]{1,120}", leaf):
                        selected.update(generation=leaf, status="selected_from_staged_pointer")
                        dirs.append((directory + "/checkpoints/" + leaf, "current_generation"))
                    else:
                        selected["status"] = "invalid_pointer_not_followed"
                else:
                    selected["status"] = "pointer_unavailable_not_followed"
                for path, kind in dirs:
                    try:
                        before = self.pvc.inspect(path, True)
                    except (OSError, ValueError):
                        before = None
                    rows = {name: self.copy(path + "/" + name) for name in CHECKPOINTS}
                    try:
                        after = self.pvc.inspect(path, True)
                    except (OSError, ValueError):
                        after = None
                    required = ("state.json", "model.keras", "optimizer.npz") if kind == "current_generation" else ("state.json",)
                    complete = before is not None and before == after and all(rows[name]["accepted"] for name in required)
                    selected["checkpoints"].append({"path": path, "kind": kind, "required_files": required,
                        "directory_unchanged_during_copy": before is not None and before == after,
                        "status": "copied_requires_review" if complete else "incomplete_or_source_changed"})
            for directory in self.scope["log_dirs"]:
                try:
                    names = self.pvc.list(directory)
                except (OSError, ValueError):
                    self.receipt.setdefault("log_directories", []).append({"path": directory, "status": "unavailable"})
                    continue
                allowed_runs = [r["name"] for r in self.scope["runs"] if (r["kind"] == "confirmation") == ("confirmation-20260923" in directory)]
                names = [name for name in names if any(re.fullmatch(re.escape(run) + r"-[A-Za-z0-9_.-]{1,100}\.log", name) for run in allowed_runs)]
                if len(names) > MAX_LOGS:
                    raise ValueError("log count budget")
                for name in names:
                    self.copy(directory + "/" + name)
            for name in ("certify-snapshot-0500.json", "a26-entropy-epoch-0500.json"):
                self.copy(self.scope["b5_readout_dir"] + "/" + name)
            self.receipt["status"] = "staged_evidence_requires_review"
        except Exception as error:
            self.receipt.update(status="incomplete", interrupted_by=type(error).__name__)
        finally:
            self.receipt["source_bytes_read"] = self.total
            (self.target / "manifest.json").write_bytes(encoded(self.receipt))
        return self.receipt


def serve(export, bundle_sha, deadline, port):
    manifest = (export.target / "manifest.json").read_bytes()
    blobs = {r["stored_sha256"]: r["stored_bytes"] for r in export.rows if r["accepted"]}
    sent, finished = set(), False

    class Handler(http.server.BaseHTTPRequestHandler):
        def setup(self):
            super().setup()
            self.connection.settimeout(10)

        def log_message(self, *unused):
            pass

        def do_GET(self):
            if self.path == "/manifest/" + bundle_sha:
                self.send_response(200)
                self.send_header("Content-Length", str(len(manifest)))
                self.send_header("X-Content-SHA256", sha(manifest))
                self.end_headers()
                self.wfile.write(manifest)
            elif self.path.startswith("/blob/") and self.path[6:] in blobs:
                digest = self.path[6:]
                self.send_response(200)
                self.send_header("Content-Length", str(blobs[digest]))
                self.send_header("X-Content-SHA256", digest)
                self.end_headers()
                with (export.blobs / digest).open("rb") as source:
                    while raw := source.read(1 << 20):
                        if time.monotonic() >= deadline:
                            raise TimeoutError("reader deadline")
                        self.wfile.write(raw)
                sent.add(digest)
            else:
                self.send_error(404)

        def do_POST(self):
            nonlocal finished
            if self.path != "/finish/" + bundle_sha or sent != set(blobs) or self.headers.get("Content-Length", "0") != "0":
                self.send_error(409)
                return
            self.send_response(204)
            self.end_headers()
            finished = True

    with http.server.HTTPServer(("127.0.0.1", port), Handler) as server:
        server.timeout = 1
        print(json.dumps({"event": "reader_ready", "bundle_sha256": bundle_sha, "manifest_sha256": sha(manifest), "status": export.receipt["status"]}), flush=True)
        while not finished and time.monotonic() < deadline:
            server.handle_request()
    return 0 if finished else 2


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--bundle", type=Path, required=True)
    p.add_argument("--expected-bundle-sha256", required=True)
    p.add_argument("--pvc-root", default="/data")
    p.add_argument("--stage", type=Path, default=Path("/work/evidence"))
    p.add_argument("--seconds", type=int, default=1800)
    p.add_argument("--port", type=int, default=8765)
    a = p.parse_args()
    if a.seconds != 1800 or a.port != 8765:
        p.error("only reviewed time/port bounds are supported")
    verify_bundle(a.bundle, a.expected_bundle_sha256)
    deadline = time.monotonic() + a.seconds
    scope = json.loads((a.bundle.parent / "scope.json").read_bytes())
    pvc = PVC(a.pvc_root)
    try:
        export = Export(pvc, a.stage, scope, a.expected_bundle_sha256, deadline)
        export.run()
    finally:
        pvc.close()
    return serve(export, a.expected_bundle_sha256, deadline, a.port)


if __name__ == "__main__":
    raise SystemExit(main())
