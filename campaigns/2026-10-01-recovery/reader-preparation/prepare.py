#!/usr/bin/env python3
"""Freeze a recovery-only reader package locally; never submit cluster objects."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parents[2]


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def prepare():
    scope_raw = (HERE / "scope.json").read_bytes()
    assert scope_raw == (HERE.parent / "recovery-manifest.json").read_bytes()
    scope = json.loads(scope_raw)
    assert len(scope["runs"]) == 17 and len(scope["caches"]) == 3
    pvc_raw = (HERE.parent / "captures/access-20261001T0518Z/pvc.json").read_bytes()
    pvc = json.loads(pvc_raw)["data"]
    image_raw = (LAB / "local/2026-10-01-execution/python-reader-image.json").read_bytes()
    image = json.loads(image_raw)
    assert pvc["name"] == "kai-data" and pvc["phase"] == "Bound"
    assert image["registry_digest_matches_downloaded_manifest_bytes"] is True
    brief = {
        "purpose": "Recover missing terminal confirmation and Chang b5 evidence from the existing kai-data PVC without modifying its contents.",
        "changes": "New finite read-only recovery transport; existing training/readout Jobs and historical source bundles unchanged.",
        "approval_ref": "PENDING: Kai must authorize this exact recovery-only exception before any create or port-forward.",
        "authorization_status": "pending_explicit_recovery_exception",
        "scientific_gate": {"status": "pending", "reference": scope["scientific_gate"], "applicability": "No scientific computation; this recovery transport cannot clear the gate."},
        "runs": scope["runs"], "caches": scope["caches"], "readout_directory": scope["b5_readout_dir"],
        "expected_metrics": [{"name": "evidence presence, byte identity and source stability", "split": "not applicable: opaque evidence transport", "expectation": "Actual terminal status, checkpoints and cache metadata are unknown until exported; absence/mismatch remains explicit."}],
        "stop_rules": [{"condition": "1800 seconds since reader startup; 2100-second Job deadline", "action": "terminate reader", "approval_ref": "part of requested finite-reader exception"},
                       {"condition": "hash mismatch, unsafe path, symlink, nonregular file, limit or source mutation", "action": "refuse affected evidence; retain incomplete receipt", "approval_ref": "part of requested finite-reader exception"},
                       {"condition": "verified client finishes all accepted blobs", "action": "clean server exit", "approval_ref": "part of requested finite-reader exception"}],
        "outputs": ["new local transport directory with PVC-shaped mirror and transfer receipt", "new recover.py export-pvc directory and export receipt", "terminal reader Job/pod status and bounded readiness log"],
        "pvc": {"name": "kai-data", "uid": pvc["uid"], "namespace": "cms-ml", "read_only": True},
        "limits": {"reader_seconds": 1800, "job_deadline_seconds": 2100, "file_count": 640, "source_byte_budget": 2147483648, "metadata_file_bytes": 2097152, "log_file_bytes": 16777216, "checkpoint_file_bytes": 134217728},
        "required_exception": "One immutable ConfigMap plus one finite read-only CPU reader Job and one loopback kubectl port-forward may use the explicitly reviewed create route instead of the supported training handoff. The training adapter requires cache identity not yet recovered and writes provenance via its init container; both are inapplicable to this recovery-only bootstrap. No data identity, scientific approval or historical launch context is invented. No training/readout launch, resume, PVC write, permission change, Service, RBAC, service account or persistent monitor is included.",
        "existing_adapter_status": "No compliant read-only recovery adapter is implemented in tools/run_handoff.py; that tool remains unchanged.",
    }
    files = {name: (HERE / name).read_bytes() for name in ("reader.py", "receive.py", "launch.py", "recovery_filters.py", "scope.json")}
    files.update({"brief.json": encoded(brief), "pvc-observation.json": pvc_raw, "image-receipt.json": image_raw})
    bundle = {"schema_version": 1, "authorization_status": brief["authorization_status"], "pvc_uid": pvc["uid"],
              "image": image["pinned_image"], "files": {name: sha(raw) for name, raw in files.items()},
              "source_filter_origin_sha256": sha((HERE.parent / "recover.py").read_bytes()),
              "scope": "recovery only; no scientific/hardware clearance or dataset payload export"}
    bundle_raw = encoded(bundle)
    digest = sha(bundle_raw)
    name = "kai-recovery-ro-1001-" + digest[:10]
    cm_name = name + "-code"
    cm = {"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": cm_name, "namespace": "cms-ml", "labels": {"user": "kai"}},
          "immutable": True, "data": {**{n: r.decode() for n, r in files.items()}, "BUNDLE.json": bundle_raw.decode()}}
    annotations = {"bnjettag.io/recovery-bundle-sha256": digest,
                   "bnjettag.io/recovery-scope": "finite-readonly-legacy-evidence", "bnjettag.io/launch-authorization": "pending-explicit-exception"}
    labels = {"user": "kai", "bnjettag.io/purpose": "evidence-recovery"}
    pod = {"restartPolicy": "Never", "automountServiceAccountToken": False, "enableServiceLinks": False,
           "terminationGracePeriodSeconds": 10,
           "securityContext": {"runAsNonRoot": True, "runAsUser": 1000, "runAsGroup": 1000, "seccompProfile": {"type": "RuntimeDefault"}},
           "containers": [{"name": "reader", "image": image["pinned_image"], "imagePullPolicy": "IfNotPresent",
               "command": ["python3", "-B", "/reader/reader.py"],
               "args": ["--bundle", "/reader/BUNDLE.json", "--expected-bundle-sha256", digest],
               "resources": {"requests": {"cpu": "100m", "memory": "256Mi", "ephemeral-storage": "256Mi"},
                             "limits": {"cpu": "1", "memory": "512Mi", "ephemeral-storage": "3Gi"}},
               "securityContext": {"allowPrivilegeEscalation": False, "readOnlyRootFilesystem": True, "capabilities": {"drop": ["ALL"]}},
               "volumeMounts": [{"name": "data", "mountPath": "/data", "readOnly": True},
                                {"name": "code", "mountPath": "/reader", "readOnly": True},
                                {"name": "scratch", "mountPath": "/work"}]}],
           "volumes": [{"name": "data", "persistentVolumeClaim": {"claimName": "kai-data", "readOnly": True}},
                       {"name": "code", "configMap": {"name": cm_name, "defaultMode": 292}},
                       {"name": "scratch", "emptyDir": {"sizeLimit": "2304Mi"}}],
           "affinity": {"nodeAffinity": {"requiredDuringSchedulingIgnoredDuringExecution": {"nodeSelectorTerms": [{"matchExpressions": [{"key": "kubernetes.io/hostname", "operator": "NotIn", "values": ["nautilus-ext-gpu01.fullerton.edu"]}]}]}}}}
    job = {"apiVersion": "batch/v1", "kind": "Job", "metadata": {"name": name, "namespace": "cms-ml", "labels": labels, "annotations": annotations},
           "spec": {"backoffLimit": 0, "completions": 1, "parallelism": 1, "activeDeadlineSeconds": 2100, "ttlSecondsAfterFinished": 3600,
                    "template": {"metadata": {"labels": labels, "annotations": annotations}, "spec": pod}}}
    destination = HERE / "frozen" / digest
    destination.mkdir(parents=True, exist_ok=False)
    all_files = {**files, "BUNDLE.json": bundle_raw, "job.json": encoded(job), "configmap.json": encoded(cm)}
    record = {"schema_version": 1, "status": "prepared_not_authorized_not_submitted", "bundle_sha256": digest,
              "job_name": name, "configmap_name": cm_name, "namespace": "cms-ml", "pvc_uid": pvc["uid"],
              "files": {n: sha(r) for n, r in all_files.items()}}
    for filename, raw in {**all_files, "preparation.json": encoded(record)}.items():
        path = destination / filename
        with path.open("xb") as handle:
            handle.write(raw)
        path.chmod(0o444)
    print(json.dumps({"directory": str(destination), "bundle_sha256": digest, "preparation_sha256": sha(encoded(record)), "job_sha256": record["files"]["job.json"], "configmap_sha256": record["files"]["configmap.json"]}, indent=2))


if __name__ == "__main__":
    prepare()
