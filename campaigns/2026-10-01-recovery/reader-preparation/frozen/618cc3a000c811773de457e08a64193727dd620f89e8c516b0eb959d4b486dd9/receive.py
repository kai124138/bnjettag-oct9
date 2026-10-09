#!/usr/bin/env python3
"""Verify reader object identity and transfer allowlisted blobs to a new local mirror."""
import argparse
import hashlib
import http.client
import json
from pathlib import Path, PurePosixPath
import re
import time

from reader import CHECKPOINTS, MAX_FILES, MAX_FILE, MAX_TOTAL, METADATA, encoded, parts, sha, verify_bundle


def subset(expected, actual):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and subset(v, actual[k]) for k, v in expected.items())
    if isinstance(expected, list):
        return isinstance(actual, list) and len(expected) == len(actual) and all(subset(a, b) for a, b in zip(expected, actual))
    return expected == actual


def validate_access(planned, expected_cm, access, pvc_uid):
    job, pod, pvc, cm = [access[k] for k in ("job", "pod", "pvc", "configmap")]
    for obj in (job, pod, pvc, cm):
        assert obj["metadata"]["namespace"] == "cms-ml", "namespace mismatch"
        assert isinstance(obj["metadata"].get("uid"), str) and obj["metadata"]["uid"], "missing live UID"
    assert job["kind"] == "Job" and pod["kind"] == "Pod" and pvc["kind"] == "PersistentVolumeClaim" and cm["kind"] == "ConfigMap"
    assert job["metadata"]["name"] == planned["metadata"]["name"]
    assert subset(planned["metadata"]["labels"], job["metadata"].get("labels", {}))
    assert subset(planned["spec"], job["spec"]), "Job bounds differ"
    assert subset(planned["metadata"].get("annotations", {}), job["metadata"].get("annotations", {}))
    assert any(o.get("kind") == "Job" and o.get("name") == job["metadata"]["name"] and o.get("uid") == job["metadata"]["uid"] and o.get("controller") is True for o in pod["metadata"].get("ownerReferences", [])), "pod owner mismatch"
    assert pvc["metadata"]["name"] == "kai-data" and pvc["metadata"]["uid"] == pvc_uid and pvc["status"]["phase"] == "Bound", "PVC identity mismatch"
    assert cm["metadata"]["name"] == expected_cm["metadata"]["name"] and cm.get("immutable") is True
    assert cm.get("data") == expected_cm["data"] and not cm.get("binaryData"), "ConfigMap bytes differ"
    expected = planned["spec"]["template"]["spec"]
    for actual in (job["spec"]["template"]["spec"], pod["spec"]):
        assert subset(expected, actual), "reader pod differs from reviewed manifest"
        assert not actual.get("initContainers") and not actual.get("ephemeralContainers"), "extra containers"
        assert not actual.get("hostNetwork") and not actual.get("hostPID") and not actual.get("hostIPC")
        assert "fsGroup" not in actual.get("securityContext", {}), "PVC permission mutation risk"
        assert len(actual["containers"]) == 1 and len(actual["volumes"]) == 3
        assert not actual["containers"][0].get("env") and not actual["containers"][0].get("envFrom")
        assert not actual["containers"][0].get("lifecycle")
        assert not actual["containers"][0].get("volumeDevices")
        assert not actual["containers"][0]["securityContext"].get("privileged")
        assert not actual["containers"][0]["securityContext"].get("capabilities", {}).get("add")
        assert all("subPath" not in mount and "subPathExpr" not in mount and "mountPropagation" not in mount for mount in actual["containers"][0]["volumeMounts"])
        assert all(not k.startswith("nvidia.com/") for b in ("requests", "limits") for k in actual["containers"][0]["resources"][b])
    assert pod["status"]["phase"] == "Running", "reader is not running"
    return {"job_name": job["metadata"]["name"], "job_uid": job["metadata"]["uid"],
            "pod_name": pod["metadata"]["name"], "pod_uid": pod["metadata"]["uid"],
            "pvc_uid": pvc_uid, "configmap_uid": cm["metadata"]["uid"],
            "limitation": "validated captured API objects; no cryptographic runtime attestation"}


def allowed(path, scope, selections):
    parts(path)
    if any(path in (cache["path"], str(PurePosixPath(cache["path"]).parent / "READY.json")) for cache in scope["caches"]):
        return True
    if path in [scope["b5_readout_dir"] + "/" + n for n in ("certify-snapshot-0500.json", "a26-entropy-epoch-0500.json")]:
        return True
    for run in scope["runs"]:
        base = run["run_dir"]
        if path in [base + "/" + n for n in METADATA]:
            return True
        roots = [base + "/snapshots/epoch-0500"] if run["kind"] == "chang_b5" else []
        generation = selections.get(base, {}).get("generation")
        if isinstance(generation, str) and re.fullmatch(r"epoch-[A-Za-z0-9_-]{1,120}", generation):
            roots.append(base + "/checkpoints/" + generation)
        if path in [root + "/" + name for root in roots for name in CHECKPOINTS]:
            return True
        for logdir in scope["log_dirs"]:
            if (run["kind"] == "confirmation") != ("confirmation-20260923" in logdir):
                continue
            if re.fullmatch(re.escape(logdir + "/" + run["name"]) + r"-[A-Za-z0-9_.-]{1,100}\.log", path):
                return True
    return False


def get(port, endpoint, limit, target=None, expected=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
    handle = None
    try:
        conn.request("GET", endpoint)
        response = conn.getresponse()
        assert response.status == 200, "transfer HTTP status"
        size = int(response.getheader("Content-Length", "-1"))
        assert 0 <= size <= limit, "transfer size limit"
        advertised = response.getheader("X-Content-SHA256")
        assert isinstance(advertised, str) and re.fullmatch(r"[a-f0-9]{64}", advertised)
        assert expected is None or advertised == expected, "advertised hash mismatch"
        digest, received, chunks = hashlib.sha256(), 0, []
        if target:
            handle = target.open("xb")
        while chunk := response.read(min(1 << 20, size - received + 1)):
            received += len(chunk)
            assert received <= size, "oversized transfer"
            digest.update(chunk)
            if handle:
                handle.write(chunk)
            else:
                chunks.append(chunk)
        assert received == size and digest.hexdigest() == advertised, "truncated or altered transfer"
        return {"bytes": received, "sha256": digest.hexdigest()}, b"".join(chunks)
    finally:
        if handle:
            handle.close()
        conn.close()


def verify_preparation(path, expected_sha):
    raw = path.read_bytes()
    assert sha(raw) == expected_sha, "preparation identity mismatch"
    record = json.loads(raw)
    for name, digest in record["files"].items():
        assert re.fullmatch(r"[A-Za-z0-9_.-]+", name)
        assert sha((path.parent / name).read_bytes()) == digest, "prepared bytes changed"
    return record


def receive(port, output, preparation, expected_preparation_sha, access):
    record = verify_preparation(preparation, expected_preparation_sha)
    bundle_path = preparation.parent / "BUNDLE.json"
    expected_sha = record["bundle_sha256"]
    bundle = verify_bundle(bundle_path, expected_sha)
    source = bundle_path.parent
    planned, cm = [json.loads((source / name).read_bytes()) for name in ("job.json", "configmap.json")]
    scope = json.loads((source / "scope.json").read_bytes())
    identity = validate_access(planned, cm, access, bundle["pvc_uid"])
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    receipt = {"status": "incomplete", "bundle_sha256": expected_sha, "identity": identity, "files": []}
    try:
        info, raw = get(port, "/manifest/" + expected_sha, 2 << 20)
        manifest = json.loads(raw)
        assert manifest["bundle_sha256"] == expected_sha and manifest["scope_sha256"] == sha(encoded(scope))
        assert len(manifest["files"]) <= MAX_FILES
        rows = manifest["files"]
        assert len({r["pvc_path"] for r in rows}) == len(rows), "duplicate source paths"
        selections = {r["run_dir"]: r for r in manifest["checkpoint_selections"]}
        assert set(selections).issubset({r["run_dir"] for r in scope["runs"]})
        accepted = [r for r in rows if r["accepted"]]
        assert all(allowed(r["pvc_path"], scope, selections) for r in rows), "non-allowlisted path"
        assert sum(r["stored_bytes"] for r in accepted) <= MAX_TOTAL
        assert all(re.fullmatch(r"[a-f0-9]{64}", r["stored_sha256"]) and re.fullmatch(r"[a-f0-9]{64}", r["source_sha256"]) for r in accepted)
        (output / "transport-manifest.json").write_bytes(raw)
        receipt["manifest_sha256"] = info["sha256"]
        mirror = output / "pvc"
        mirror.mkdir(mode=0o700)
        for row in accepted:
            target = mirror.joinpath(*parts(row["pvc_path"]))
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".partial")
            meta, _ = get(port, "/blob/" + row["stored_sha256"], min(MAX_FILE[PurePosixPath(row["pvc_path"]).suffix], row["stored_bytes"]), temporary, row["stored_sha256"])
            assert meta["bytes"] == row["stored_bytes"]
            temporary.rename(target)
            receipt["files"].append({"pvc_path": row["pvc_path"], **meta})
        for base, selection in selections.items():
            if selection.get("generation"):
                path = mirror.joinpath(*parts(base + "/latest.json"))
                assert sha(path.read_bytes()) == selection["pointer_sha256"]
                assert json.loads(path.read_bytes())["checkpoint"] == selection["generation"], "generation differs from accepted pointer"
        receipt["status"] = "transfer_verified_evidence_requires_review"
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=30)
        try:
            conn.request("POST", "/finish/" + expected_sha, body=b"")
            receipt["reader_finish_status"] = conn.getresponse().status
            assert receipt["reader_finish_status"] == 204
        finally:
            conn.close()
    except Exception as error:
        receipt.update(status="incomplete", interrupted_by=type(error).__name__)
        raise
    finally:
        receipt["finished_unix_time"] = time.time()
        with (output / "transfer-receipt.json").open("x") as handle:
            json.dump(receipt, handle, indent=2, sort_keys=True)
            handle.write("\n")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preparation", type=Path, required=True)
    p.add_argument("--expected-preparation-sha256", required=True)
    p.add_argument("--port", type=int, default=18765)
    p.add_argument("--out", type=Path, required=True)
    for name in ("job", "pod", "pvc", "configmap"):
        p.add_argument("--" + name + "-json", type=Path, required=True)
    a = p.parse_args()
    receive(a.port, a.out, a.preparation, a.expected_preparation_sha256,
            {k: json.loads(getattr(a, k + "_json").read_bytes()) for k in ("job", "pod", "pvc", "configmap")})


if __name__ == "__main__":
    main()
