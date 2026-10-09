#!/usr/bin/env python3
"""One-shot legacy evidence collection. No workload creation or archived-code execution."""
import argparse
import base64
import datetime as dt
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile

HERE = Path(__file__).resolve().parent
LAB = HERE.parent.parent
CONF = LAB / "campaigns/2026-09-23-confirmation"
CHANG = LAB / "campaigns/2026-09-26-training-batch"
JOBS = (
    "kai-confirm-onegpu-0924-e0c0a3-r2",
    "kai-chang0926-pilotb5-42abed",
    "kai-chang0926-readoutb5-42abed",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(path.read_text())


def write_new(path, value):
    with path.open("x") as handle:
        json.dump(value, handle, indent=2, sort_keys=True)
        handle.write("\n")


SECRET_KEY = re.compile(r"(?i)(?:api[_-]?key|access[_-]?token|refresh[_-]?token|authorization|password|client[_-]?secret|secret)$")
QUOTED_OR_TOKEN = r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^\s,;]+)'''


def redact_text(text):
    # Consume authorization schemes and their values before generic key/value rules.
    text = re.sub(r'''(?i)(["']?authorization["']?\s*[=:]\s*)(?:(?:Bearer|Basic)\s+[^\s,;]+|'''
                  + QUOTED_OR_TOKEN + ")", r"\1[REDACTED]", text)
    text = re.sub(r"(?i)\bBearer\s+[^\s,;]+", "Bearer [REDACTED]", text)
    text = re.sub(r'''(?i)(["']?(?:[A-Za-z0-9_-]*api[_-]?key|access[_-]?token|refresh[_-]?token|password|client[_-]?secret|secret)["']?\s*[=:]\s*)'''
                  + QUOTED_OR_TOKEN, r"\1[REDACTED]", text)
    text = re.sub(r"\b(?:wandb_v1_|sk-|ghp_|github_pat_)[A-Za-z0-9_-]+", "[REDACTED]", text)
    return re.sub(r"\b[0-9a-fA-F]{40}\b", "[REDACTED_40_HEX]", text)


def sanitize_json(value):
    """Walk objects before serializing, so redaction cannot invalidate JSON syntax."""
    if isinstance(value, dict):
        return {key: "[REDACTED]" if SECRET_KEY.search(key) else sanitize_json(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_json(item) for item in value]
    return redact_text(value) if isinstance(value, str) else value


def credential_json(value):
    if isinstance(value, dict):
        return any(SECRET_KEY.search(key) or credential_json(item) for key, item in value.items())
    if isinstance(value, list):
        return any(credential_json(item) for item in value)
    return isinstance(value, str) and redact_text(value) != value


def redact(text):
    # Logs are sanitized derivatives. These rules are not a universal secret detector.
    try:
        value = json.loads(text)
    except ValueError:
        return redact_text(text)
    sanitized = sanitize_json(value)
    return json.dumps(sanitized) if sanitized != value else text


def frozen_bundle(configmap, manifest):
    cm, record = read_json(configmap), read_json(manifest)
    payload = base64.b64decode(cm["binaryData"]["hgq2.tar.gz"], validate=True)
    expected = record.get("bundle_sha256", record.get("sha256"))
    if sha(payload) != expected:
        raise ValueError("historical bundle checksum mismatch")
    files = {}
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        names = set()
        for member in archive:
            path = PurePosixPath(member.name)
            if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "code":
                raise ValueError("unsafe archive path")
            if member.name in names:
                raise ValueError("duplicate archive path")
            names.add(member.name)
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError("archive links/special files refused")
            files[str(path.relative_to("code"))] = sha(archive.extractfile(member).read())
    if files != record["files"]:
        raise ValueError("historical file inventory mismatch")
    return {"configmap": cm["metadata"]["name"], "configmap_file": str(configmap.relative_to(LAB)),
            "configmap_file_sha256": sha(configmap.read_bytes()), "bundle_sha256": expected,
            "manifest_file": str(manifest.relative_to(LAB)), "manifest_file_sha256": sha(manifest.read_bytes()),
            "regular_files_verified": len(files), "status": "stored_bytes_verified_no_execution"}


def recovery_manifest():
    conf_cm = read_json(CONF / "one-gpu-configmap.json")
    conf_manifest = read_json(CONF / "one-gpu-manifest.json")
    configs_digest = sha(json.dumps(conf_cm["data"], sort_keys=True).encode())
    if configs_digest != conf_manifest["configs_sha256"]:
        raise ValueError("confirmation ConfigMap content digest mismatch")
    index = json.loads(conf_cm["data"]["index-one-gpu.json"])
    chang = read_json(CHANG / "manifests/bundle-manifest-42abed4b.json")
    runs = [{"name": r["name"], "run_dir": r["output_root"] + "/" + r["name"],
             "cache_dir": r["data_cache"], "kind": "confirmation"} for r in index["runs"]]
    runs += [{"name": n, "run_dir": chang["run_root"] + "/runs/" + n,
              "cache_dir": chang["data_root"] + "/n64/data", "kind": "chang_b5"}
             for n in chang["pilot_b"]["k5"]["runs"]]
    n8 = read_json(CONF / "preflight-result.json")["data"]
    n64 = read_json(CONF / "n64-full-preflight-result.json")["data"]
    line = next(s for s in (CHANG / "PREFLIGHT.md").read_text().splitlines() if s.startswith("DATA_INFO {"))
    chang_info = json.loads(line[len("DATA_INFO "):])
    return {
        "schema_version": 1, "scope": "read-only evidence recovery; no launch authorization",
        "jobs": list(JOBS), "namespace": "cms-ml", "owner_label": "user=kai",
        "frozen_bundles": [
            frozen_bundle(LAB / "campaigns/2026-09-22-constituent-screen/study-configmap.json",
                          LAB / "campaigns/2026-09-22-constituent-screen/bundle-manifest.json"),
            frozen_bundle(CHANG / "manifests/configmap-42abed4b.json", CHANG / "manifests/bundle-manifest-42abed4b.json")],
        "confirmation_configmap": {"path": str((CONF / "one-gpu-configmap.json").relative_to(LAB)),
            "sha256": sha((CONF / "one-gpu-configmap.json").read_bytes()),
            "content_sha256": configs_digest, "content_digest_status": "matches historical one-gpu-manifest.json",
            "name": conf_cm["metadata"]["name"], "note": "digest records stored ConfigMap JSON bytes"},
        "runs": runs,
        "caches": [
            {"path": "/data/constituent-study-20260922/n8/data/data_info.json", "expected_array_sha256": n8,
             "expected_n_train": 496000, "expected_n_val": 124000, "source": "confirmation/preflight-result.json"},
            {"path": "/data/constituent-study-20260922/n64/data/data_info.json", "expected_array_sha256": n64,
             "expected_n_train": 496000, "expected_n_val": 124000, "source": "confirmation/n64-full-preflight-result.json"},
            {"path": "/data/chang-n64-20260926/n64/data/data_info.json",
             "expected_array_sha256": chang_info["array_sha256"], "expected_n_train": 558000, "expected_n_val": 62000,
             "expected_pt_gate_gev": 2.0, "expected_cache_code_sha256": chang_info["code_sha256"],
             "source": "training-batch/PREFLIGHT.md DATA_INFO; full actual cache export still required"}],
        "log_dirs": ["/data/confirmation-20260923/architecture/logs", "/data/chang-n64-20260926/pilot-b/logs"],
        "b5_readout_dir": "/data/chang-n64-20260926/pilot-b/readout-epoch-0500-42abed-b5",
        "scientific_gate": "pending: terminal b5 readout plus Kai (c)/(d); K1 not cleared",
        "legacy_handoff_status": "context unavailable unless a valid record and annotation binding are recovered; local legacy manifests alone are not immutable launch records",
        "excluded_evidence": "code/evidence/dry_readout_b5* are synthetic fixtures, never terminal cluster outcomes",
    }


def safe_object(obj):
    """Drop command, env, volumes, managedFields and arbitrary annotations."""
    metadata = obj.get("metadata", {})
    result = {"kind": obj.get("kind"), "metadata": {k: metadata[k] for k in
              ("name", "namespace", "uid", "creationTimestamp", "deletionTimestamp", "ownerReferences") if k in metadata},
              "status": obj.get("status", {})}
    result["metadata"]["labels"] = {k: v for k, v in metadata.get("labels", {}).items()
                                     if k in {"user", "job-name", "batch.kubernetes.io/job-name", "bnjettag.io/run-id"}}
    result["metadata"]["annotations"] = {k: v for k, v in metadata.get("annotations", {}).items() if k.startswith("bnjettag.io/")}
    result["nodeName"] = obj.get("spec", {}).get("nodeName")
    return sanitize_json(result)


def owned_pod(pod, job_name, job_uid=None):
    meta = pod.get("metadata", {})
    labels = meta.get("labels", {})
    return (bool(job_uid) and labels.get("user") == "kai" and labels.get("job-name", labels.get("batch.kubernetes.io/job-name")) == job_name
            and any(o.get("kind") == "Job" and o.get("name") == job_name
                    and o.get("uid") == job_uid for o in meta.get("ownerReferences", [])))


def owned_job(job, name):
    meta = job.get("metadata", {})
    return meta.get("name") == name and meta.get("labels", {}).get("user") == "kai"


def list_items(response):
    if not isinstance(response, dict) or not isinstance(response.get("items"), list):
        raise ValueError("invalid object listing")
    for obj in response["items"]:
        if not isinstance(obj, dict) or not isinstance(obj.get("metadata"), dict):
            raise ValueError("invalid object metadata")
    return response["items"]


def job_items(response, name):
    items = list_items(response)
    if len(items) > 1 or any(not owned_job(item, name) or not isinstance(item["metadata"].get("uid"), str)
                             or not item["metadata"]["uid"] for item in items):
        raise ValueError("unresolved Job identity")
    return items


def validate_context(context):
    if not context or not re.fullmatch(r"[A-Za-z0-9_.:@/-]+", context) or context.startswith("-"):
        raise ValueError("an explicit existing kubeconfig context is required")
    try:
        result = subprocess.run(["kubectl", "config", "get-contexts", context, "-o", "name"],
                                capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ValueError("context unavailable: " + type(error).__name__) from None
    if result.returncode or result.stdout.strip() != context:
        raise ValueError("named context is absent or ambiguous; no cluster request made")


def collect_cluster(out, context):
    """Validate a named local context, then only get/logs against cms-ml."""
    validate_context(context)
    out.mkdir(parents=True, exist_ok=False)
    receipts = []
    ownership = []

    def call(args, filename, transform=None):
        command = ["kubectl", "--context", context, "-n", "cms-ml", "--request-timeout=20s"] + args
        entry = {"command": command, "file": filename}
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=45, check=False)
        except (OSError, subprocess.TimeoutExpired) as error:
            entry.update(status="unavailable", reason=type(error).__name__)
            receipts.append(entry)
            return None
        entry["exit_code"] = result.returncode
        if result.returncode:
            # Server errors can contain credential details; record the failure without stderr.
            entry["status"] = "unavailable"
            receipts.append(entry)
            return None
        entry["source_stdout_sha256"] = sha(result.stdout.encode())
        try:
            value = json.loads(result.stdout) if transform else result.stdout
            rendered = json.dumps(transform(value), indent=2) if transform else redact(value)
        except (ValueError, KeyError, TypeError, AttributeError):
            entry["status"] = "invalid_response"
            receipts.append(entry)
            return None
        (out / filename).write_text(rendered + "\n")
        entry.update(status="collected_sanitized_derivative", stored_sha256=sha((out / filename).read_bytes()))
        receipts.append(entry)
        return value

    for job_name in JOBS:
        job = call(["get", "jobs", "-l", "user=kai", "--field-selector", "metadata.name=" + job_name, "-o", "json"],
                   job_name + ".job.json", lambda d: [safe_object(o) for o in job_items(d, job_name)])
        if job is None:
            ownership.append({"job": job_name, "status": "job_read_unavailable_or_invalid", "job_uid": None,
                              "logs": "skipped_unresolved_identity"})
            continue
        objects = job_items(job, job_name)
        if not objects:
            ownership.append({"job": job_name, "status": "job_observed_absent", "job_uid": None,
                              "logs": "skipped_no_orphan_recovery"})
            continue
        uid = objects[0]["metadata"]["uid"]
        ownership.append({"job": job_name, "status": "job_observed_uid_bound", "job_uid": uid})
        pods = call(["get", "pods", "-l", "user=kai,job-name=" + job_name, "-o", "json"],
                    job_name + ".pods.json", lambda d: [safe_object(o) for o in list_items(d) if owned_pod(o, job_name, uid)])
        for pod in (pods or {}).get("items", []):
            if not owned_pod(pod, job_name, uid):
                continue
            name = pod["metadata"]["name"]
            containers = pod.get("spec", {}).get("initContainers", []) + pod.get("spec", {}).get("containers", [])
            for container in containers:
                cname = container["name"]
                for previous in (False, True):
                    args = ["logs", name, "-c", cname, "--timestamps=true"] + (["--previous=true"] if previous else [])
                    call(args, name + "." + cname + (".previous" if previous else "") + ".log")
    write_new(out / "receipt.json", {"collected_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
              "scope": "one-shot read-only; logs and metadata are sanitized derivatives", "operations": receipts,
              "ownership_checks": ownership})


def source_path(root, pvc_path):
    """Resolve only non-symlinked paths below the caller's existing /data export."""
    relative = PurePosixPath(pvc_path).relative_to("/data")
    if ".." in relative.parts:
        raise ValueError("unsafe PVC path")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("symlinked PVC source refused")
    return current


def cache_identity(info, expected):
    failures = []
    if info.get("array_sha256") != expected["expected_array_sha256"]:
        failures.append("array_sha256_missing_or_mismatched")
    for key in ("n_train", "n_val", "pt_gate_gev"):
        if "expected_" + key in expected and info.get(key) != expected["expected_" + key]:
            failures.append(key + "_missing_or_mismatched")
    if "expected_cache_code_sha256" in expected and info.get("code_sha256") != expected["expected_cache_code_sha256"]:
        failures.append("cache_code_sha256_missing_or_mismatched")
    return {"status": "metadata_matches_historical_expectations" if not failures else "identity_unavailable_or_mismatched",
            "failures": failures, "limitation": "metadata comparison only; actual array bytes are not rehashed"}


def file_state(path):
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns


def read_source_bytes(path):
    before = file_state(path)
    raw = path.read_bytes()
    try:
        after = file_state(path)
    except OSError:
        after = None
    return raw, "unchanged_during_read" if before == after and before[2] == len(raw) else "changed_or_disappeared"


def export_pvc(root, out, checkpoints=False):
    """Read an already authorized mounted/exported data root; never mount or exec."""
    root = root.resolve(strict=True)
    if out.resolve().is_relative_to(root):
        raise ValueError("output must be outside the source export")
    manifest = recovery_manifest()
    out.mkdir(parents=True, exist_ok=False)
    receipts = []
    identities = []
    selections = []
    copied = {}
    failure = None

    def copy(pvc_path):
        if pvc_path in copied:
            return copied[pvc_path]
        row = {"pvc_path": pvc_path, "accepted": False}
        copied[pvc_path] = row
        receipts.append(row)
        try:
            path = source_path(root, pvc_path)
            if not path.is_file():
                row["status"] = "missing"
                return row
            raw, stability = read_source_bytes(path)
            row.update(source_sha256=sha(raw), source_stability=stability)
            target = out / PurePosixPath(pvc_path).relative_to("/data")
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".log":
                output = redact(raw.decode("utf-8", errors="replace")).encode()
                row["status"] = "sanitized_log_derivative"
            else:
                if path.suffix == ".json":
                    try:
                        value = json.loads(raw)
                    except (ValueError, UnicodeDecodeError):
                        row["status"] = "invalid_json"
                        return row
                    if credential_json(value):
                        row["status"] = "refused_possible_credential"
                        return row
                output = raw
                row["status"] = "copied"
            with target.open("xb") as handle:
                handle.write(output)
            row.update(accepted=True, bytes=len(output), sha256=sha(output))
            if stability != "unchanged_during_read":
                row["status"] = "copied_source_changed"
        except FileNotFoundError:
            row.update(status="missing_or_disappeared", reason="FileNotFoundError")
        except ValueError:
            row.update(status="refused_unsafe_path", reason="ValueError")
        except OSError as error:
            row.update(status="copy_failed", reason=type(error).__name__)
        return row

    try:
        for cache in manifest["caches"]:
            for name in ("data_info.json", "READY.json"):
                copy(str(PurePosixPath(cache["path"]).parent / name))
            exported = out / PurePosixPath(cache["path"]).relative_to("/data")
            identities.append({"path": cache["path"], **(cache_identity(read_json(exported), cache)
                               if copied[cache["path"]]["accepted"] else
                               {"status": "context unavailable", "reason": "actual cache data_info.json missing or refused"})})
        for run in manifest["runs"]:
            directory = run["run_dir"]
            for name in ("config.json", "data_info.json", "latest.json", "state.json", "DIVERGED.json", "RSS_GATE_FAIL.json",
                         "source_manifest.json", "input_std.json", "COMPLETE.json", "TRAINING_COMPLETE.json",
                         "VERIFIED_COMPLETE.json", "screen_result.json"):
                copy(directory + "/" + name)
            directories = [(directory + "/snapshots/epoch-0500", "snapshot")] if run["kind"] == "chang_b5" else []
            pointer_row = copied[directory + "/latest.json"]
            selection = {"run_dir": directory, "pointer_status": pointer_row["status"],
                         "pointer_sha256": pointer_row.get("sha256"), "generation": None}
            selections.append(selection)
            if pointer_row["accepted"]:
                # Select from the exact exported bytes, never a second read of live latest.json.
                pointer = out / PurePosixPath(directory + "/latest.json").relative_to("/data")
                value = read_json(pointer)
                leaf = value.get("checkpoint", "") if isinstance(value, dict) else ""
                if isinstance(leaf, str) and re.fullmatch(r"epoch-[A-Za-z0-9_-]+", leaf):
                    selection.update(generation=leaf, status="selected_from_exported_pointer")
                    directories.append((directory + "/checkpoints/" + leaf, "current_generation"))
                else:
                    selection["status"] = "invalid_pointer_not_followed"
            else:
                selection["status"] = "pointer_unavailable_or_refused_not_followed"
            selection["checkpoints"] = []
            for checkpoint, kind in directories:
                source = source_path(root, checkpoint)
                try:
                    before = file_state(source)
                except OSError:
                    before = None
                required = ["state.json"] + (["model.keras", "optimizer.npz"]
                                              if checkpoints and kind == "current_generation" else [])
                names = ["state.json"] + (["model.keras", "optimizer.npz", "model_best.keras", "model_best_auc_feasible.keras",
                         "model_min_ebops.keras", "model_unconstrained.keras"] if checkpoints else [])
                rows = {name: copy(checkpoint + "/" + name) for name in names}
                try:
                    after = file_state(source)
                except OSError:
                    after = None
                complete = (before is not None and before == after and
                            all(rows[name]["accepted"] for name in required) and
                            all(row.get("source_stability", "unchanged_during_read") == "unchanged_during_read" for row in rows.values()))
                selection["checkpoints"].append({"path": checkpoint, "kind": kind,
                    "status": "requested_files_copied_requires_review" if complete else "incomplete_or_source_changed",
                    "directory_unchanged_during_copy": before is not None and before == after,
                    "required_files": required})
        for directory in manifest["log_dirs"]:
            path = source_path(root, directory)
            if path.is_dir():
                for file in sorted(path.glob("*.log")):
                    if any(file.name.startswith(r["name"] + "-") for r in manifest["runs"]):
                        copy(directory + "/" + file.name)
        for name in ("certify-snapshot-0500.json", "a26-entropy-epoch-0500.json"):
            copy(manifest["b5_readout_dir"] + "/" + name)
    except BaseException as error:
        failure = type(error).__name__
        raise
    finally:
        write_new(out / "export-receipt.json", {"collected_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "source": str(root), "checkpoints_requested": checkpoints, "files": receipts,
                  "cache_identities": identities, "checkpoint_selections": selections, "interrupted_by": failure,
                  "status": "partial evidence retained; no checkpoint validity or terminal clearance inferred"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["manifest", "cluster", "export-pvc"])
    parser.add_argument("--out", type=Path, required=True, help="new output path; existing output is refused")
    parser.add_argument("--pvc-root", type=Path, help="existing authorized mount/export corresponding to PVC /data")
    parser.add_argument("--context", help="explicit existing kubeconfig context; required for cluster reads")
    parser.add_argument("--checkpoints", action="store_true", help="also copy selected model and optimizer files")
    args = parser.parse_args()
    if args.action == "manifest":
        write_new(args.out, recovery_manifest())
    elif args.action == "cluster":
        if not args.context:
            parser.error("cluster requires an explicit --context; the current default is never used")
        collect_cluster(args.out, args.context)
    else:
        if args.pvc_root is None:
            parser.error("export-pvc requires --pvc-root")
        export_pvc(args.pvc_root, args.out, args.checkpoints)


if __name__ == "__main__":
    main()
