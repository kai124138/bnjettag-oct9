#!/usr/bin/env python3
"""Campaign-local recovery adapter: offline unless an exact exception authorizes submit."""
import argparse
from collections import Counter
import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

from receive import verify_preparation
from reader import encoded, sha

EXCEPTIONS = {"read_only_bootstrap_without_training_handoff_init", "reviewed_campaign_recovery_adapter"}
OPERATIONS = {"create_immutable_reader_configmap", "create_finite_readonly_reader_job", "loopback_port_forward", "read_reader_status_logs", "download_allowlisted_evidence"}


def authorization(value, preparation_sha, approval_ref):
    assert value["approval_status"] == "approved", "explicit approval is absent"
    assert approval_ref and value["approval_ref"] == approval_ref
    for key in ("approval_ref", "user_authorization_reference"):
        text = value[key]
        assert isinstance(text, str) and text.strip()
        assert not re.search(r"\b(?:pending|todo|tbd|placeholder|example|fixture)\b", text, re.I), "placeholder approval reference"
    timestamp = dt.datetime.fromisoformat(value["authorized_at_utc"].replace("Z", "+00:00"))
    assert timestamp.utcoffset() == dt.timedelta(0), "authorization timestamp must be explicit UTC"
    assert value["preparation_sha256"] == preparation_sha
    assert set(value["exceptions"]) == EXCEPTIONS
    assert set(value["operations"]) == OPERATIONS
    assert value["context"] == "nautilus" and value["namespace"] == "cms-ml"


def kubectl(args):
    result = subprocess.run(["kubectl", "--context", "nautilus", "--request-timeout=25s", "-n", "cms-ml", *args], capture_output=True, timeout=45)
    if result.returncode:
        raise RuntimeError("kubectl action failed; output withheld, no retry or fallback")
    return result.stdout


def check_lint(job, doctor):
    spec = importlib.util.spec_from_file_location("recovery_nrp_doctor", doctor)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    report = module.lint_job(job, {}, Counter())
    assert not report.errors, "nrp_doctor lint errors"
    return {"errors": report.errors, "warnings": report.warns, "notes": report.notes,
            "scope": "existing lint_job, offline CPU-only shape; no GPU discovery needed"}


def submit(path, expected_sha, approval_file, approval_ref, events, doctor):
    record = verify_preparation(path, expected_sha)
    expected_events = path.resolve().parents[2] / "submissions" / expected_sha
    assert events.resolve() == expected_events, "submission ledger must use the fixed campaign preparation identity"
    assert not events.exists(), "prior submission intent exists; no replay"
    auth_raw = approval_file.read_bytes()
    authorization(json.loads(auth_raw), expected_sha, approval_ref)
    job = json.loads((path.parent / "job.json").read_bytes())
    lint = check_lint(job, doctor)
    context = subprocess.run(["kubectl", "config", "get-contexts", "nautilus", "-o", "name"], capture_output=True, timeout=15)
    assert context.returncode == 0 and context.stdout.strip() == b"nautilus", "explicit context unavailable"
    pvc = json.loads(kubectl(["get", "pvc", "kai-data", "-o", "json"]))
    assert pvc["metadata"]["uid"] == record["pvc_uid"] and pvc["status"]["phase"] == "Bound", "PVC changed"
    for kind, name in (("job", record["job_name"]), ("configmap", record["configmap_name"])):
        assert not kubectl(["get", kind, name, "--ignore-not-found", "-o", "json"]).strip(), "existing object; no adoption or replay"
    events.mkdir(parents=True, exist_ok=False, mode=0o700)
    intent = {"status": "intent_before_create", "preparation_sha256": expected_sha, "approval_ref": approval_ref,
              "approval_record_sha256": sha(auth_raw), "pvc_uid": record["pvc_uid"], "lint": lint, "created_unix_time": time.time()}
    with (events / "intent.json").open("x") as handle:
        handle.write(encoded(intent).decode())
        handle.flush()
        os.fsync(handle.fileno())
    try:
        for filename in ("configmap.json", "job.json"):
            verify_preparation(path, expected_sha)
            raw = kubectl(["create", "-f", str(path.parent / filename), "-o", "json"])
            obj = json.loads(raw)
            receipt = {"kind": obj["kind"], "name": obj["metadata"]["name"], "uid": obj["metadata"]["uid"],
                       "response_sha256": sha(raw), "status": "created", "preparation_sha256": expected_sha}
            with (events / (filename + ".created.json")).open("x") as handle:
                handle.write(encoded(receipt).decode())
    except BaseException as error:
        with (events / "incomplete.json").open("x") as handle:
            handle.write(encoded({"status": "ambiguous_or_partial_submission_no_retry", "error_type": type(error).__name__}).decode())
        raise


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--expected-preparation-sha256", required=True)
    p.add_argument("--doctor", type=Path, required=True)
    p.add_argument("--submit", action="store_true")
    p.add_argument("--approval-record", type=Path)
    p.add_argument("--approval-ref")
    p.add_argument("--events", type=Path)
    a = p.parse_args()
    record = verify_preparation(a.preparation, a.expected_preparation_sha256)
    job = json.loads((a.preparation.parent / "job.json").read_bytes())
    lint = check_lint(job, a.doctor)
    if not a.submit:
        print(json.dumps({"status": "OFFLINE_PREPARATION_VALID_NO_SUBMISSION", "job": record["job_name"], "lint": lint}, indent=2))
        return
    if not all((a.approval_record, a.approval_ref, a.events)):
        p.error("submit requires an explicit approved exception record, exact reference and fresh durable events directory")
    submit(a.preparation, a.expected_preparation_sha256, a.approval_record, a.approval_ref, a.events, a.doctor)


if __name__ == "__main__":
    main()
