"""Deterministic protocol drift checks; semantic checks live in the Jev service.

A protocol snapshot is not a training-code freeze or scientific approval.
"""
from __future__ import annotations

import json
import math
import hashlib
from pathlib import Path

from .common import ROOT, LabError, digest, policy_snapshot, read_text, write_json


def differences(left: object, right: object, path: str = "") -> list[dict]:
    if isinstance(left, dict) and isinstance(right, dict):
        out = []
        for key in sorted(left.keys() | right.keys()):
            child = f"{path}.{key}" if path else key
            if key not in left or key not in right:
                out.append({"field": child, "before": left.get(key), "after": right.get(key)})
            else:
                out.extend(differences(left[key], right[key], child))
        return out
    if left != right:
        return [{"field": path, "before": left, "after": right}]
    return []


def check_protocol(protocol: dict) -> list[dict]:
    findings = []
    def flag(field: str, message: str):
        findings.append({"field": field, "severity": "block", "message": message})
    required = {"version", "purpose", "scope", "dataset", "inputs", "arms", "selection", "metrics", "stop_rules", "outputs"}
    for key in sorted(required - protocol.keys()):
        flag(key, "Required protocol field is missing")
    if findings:
        return findings
    if protocol["version"] != 1:
        flag("version", "Unsupported protocol schema")
    if protocol["scope"] not in {"screen", "claim"}:
        flag("scope", "Declare screen or claim")
    if not isinstance(protocol["purpose"], str) or not protocol["purpose"].strip():
        flag("purpose", "Purpose must be stated")
    dataset = protocol["dataset"]
    if not isinstance(dataset, dict):
        flag("dataset", "Dataset must be a structured object")
    else:
        for key in ("id", "identity_sha256", "train_split", "validation_split", "test_split"):
            if not dataset.get(key):
                flag(f"dataset.{key}", "Dataset identity and split definitions cannot be assumed")
        sha = dataset.get("identity_sha256", "")
        if not isinstance(sha, str) or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha):
            flag("dataset.identity_sha256", "Supply the actual dataset identity hash")
        splits = [dataset.get(x) for x in ("train_split", "validation_split", "test_split")]
        if all(isinstance(x, str) for x in splits) and len(set(splits)) != 3:
            flag("dataset", "Training, validation, and held-out split definitions must be distinct")
    inputs = protocol["inputs"]
    if not isinstance(inputs, dict) or type(inputs.get("n_constituents")) is not int or inputs["n_constituents"] < 1 or not isinstance(inputs.get("features"), list) or not inputs["features"]:
        flag("inputs", "State constituent count and feature set")
    selection = protocol["selection"]
    if not isinstance(selection, dict) or selection.get("split") != "validation" or not selection.get("metric") or not selection.get("rule"):
        flag("selection", "State a validation-only selection metric and registered rule")
    elif selection.get("cost_checkpoint") != "selected":
        flag("selection.cost_checkpoint", "Cost must refer to the selected checkpoint")
    metrics = protocol["metrics"]
    if not isinstance(metrics, list) or not metrics:
        flag("metrics", "Declare output metrics with split, n, and status")
    else:
        for i, metric in enumerate(metrics):
            if not isinstance(metric, dict) or any(not metric.get(k) for k in ("name", "split", "n", "status")):
                flag(f"metrics[{i}]", "Metric, split, actual n, and status are required")
            elif type(metric["n"]) is not int or metric["n"] < 1:
                flag(f"metrics[{i}].n", "Use the actual positive split size")
    arms = protocol["arms"]
    if not isinstance(arms, list) or not arms:
        flag("arms", "Declare all arms")
    else:
        names, seeds = set(), {}
        baseline = None
        for i, arm in enumerate(arms):
            field = f"arms[{i}]"
            if not isinstance(arm, dict) or any(k not in arm for k in ("name", "group", "seed", "schedule", "quantization", "changed_factors")):
                flag(field, "Arm needs name, group, seed, schedule, quantization, and changed_factors")
                continue
            if not isinstance(arm["name"], str) or not arm["name"] or arm["name"] in names:
                flag(field+".name", "Arm names must be nonempty and unique")
            names.add(str(arm["name"]))
            if not isinstance(arm["group"], str) or not arm["group"] or type(arm["seed"]) is not int:
                flag(field, "Each arm needs a group and integer seed")
                continue
            if arm["seed"] in seeds.setdefault(arm["group"], set()):
                flag(field+".seed", "A seed is repeated in the same arm group")
            seeds[arm["group"]].add(arm["seed"])
            schedule = arm["schedule"]
            if not isinstance(schedule, dict) or any(not schedule.get(k) for k in ("epochs", "batch_size", "optimizer", "learning_rate")):
                flag(field+".schedule", "Declare the complete training schedule")
            else:
                for key in ("epochs", "batch_size"):
                    if type(schedule[key]) is not int or schedule[key] <= 0:
                        flag(field+".schedule."+key, "Must be a positive integer")
                if type(schedule["learning_rate"]) not in (int, float) or not math.isfinite(schedule["learning_rate"]) or schedule["learning_rate"] <= 0:
                    flag(field+".schedule.learning_rate", "Must be a positive number")
            factors = arm["changed_factors"]
            if not isinstance(factors, list) or any(not isinstance(x, str) for x in factors):
                flag(field+".changed_factors", "Declare changed factors as field paths")
                continue
            matched = {"inputs": arm.get("inputs", inputs), "schedule": schedule, "quantization": arm["quantization"]}
            if baseline is None:
                baseline = matched
            else:
                for change in differences(baseline, matched):
                    if not any(change["field"] == f or change["field"].startswith(f+".") for f in factors):
                        flag(field+"."+change["field"], "Unregistered difference from the first arm")
        if protocol["scope"] == "claim":
            expected_gap = protocol.get("expected_auc_gap")
            minimum = 8 if type(expected_gap) in (int, float) and abs(expected_gap) < 0.005 else 3
            for group, values in seeds.items():
                if len(values) < minimum:
                    flag("arms."+group, f"This claim requires at least {minimum} seeds")
            if len({tuple(sorted(x)) for x in seeds.values()}) > 1:
                flag("arms", "Compared arm groups must use paired seeds")
            if not protocol.get("interval_method"):
                flag("interval_method", "Declare the interval method for claimed gaps")
    if not isinstance(protocol["stop_rules"], list):
        flag("stop_rules", "Declare approved stop rules explicitly; an empty list means none")
    if not isinstance(protocol["outputs"], list) or not protocol["outputs"]:
        flag("outputs", "Declare durable outputs")
    return findings


def config_sources(protocol: dict, root: Path) -> dict:
    sources = {}
    for arm in protocol.get("arms", []) if isinstance(protocol.get("arms"), list) else []:
        if isinstance(arm, dict) and arm.get("config_path"):
            path = arm["config_path"]
            if not isinstance(path, str):
                raise LabError("config_path must name an explicit lab text file")
            sources[path] = hashlib.sha256(read_text(path, root).encode()).hexdigest()
    return sources


def inspect_protocol(path: str, baseline_path: str | None = None, root: Path = ROOT) -> dict:
    protocol = json.loads(read_text(path, root))
    if not isinstance(protocol, dict):
        raise LabError("Protocol must be a JSON object")
    findings = check_protocol(protocol)
    sources = config_sources(protocol, root)
    drift = []
    if baseline_path:
        baseline = json.loads(read_text(baseline_path, root))
        if not isinstance(baseline, dict) or baseline.get("sha256") != digest(baseline.get("record")):
            raise LabError("Protocol snapshot hash does not match")
        if baseline["record"].get("kind") != "training-methods-v1":
            raise LabError("Not a training-methods snapshot")
        drift = differences(baseline["record"]["protocol"], protocol)
        drift += differences(baseline["record"].get("config_sources", {}), sources, "config_sources")
        for change in differences(baseline["record"]["policy"], policy_snapshot(root)):
            findings.append({"field": "policy."+change["field"], "severity": "block", "message": "Methodology changed since snapshot"})
    return {"protocol_sha256": digest(protocol), "config_sources": sources,
            "structural_valid": not findings, "findings": findings,
            "drift": drift, "matches_snapshot": baseline_path is not None and not drift and not findings,
            "scientific_gate": "not_evaluated", "launch_authorized": False,
            "limitations": "Checks declared protocol fields, not training execution or dataset bytes."}


def freeze_protocol(path: str, root: Path = ROOT) -> dict:
    protocol = json.loads(read_text(path, root))
    if not isinstance(protocol, dict) or check_protocol(protocol):
        raise LabError("Protocol has blocking structural findings; inspect it before freezing")
    record = {"kind": "training-methods-v1", "protocol": protocol,
              "config_sources": config_sources(protocol, root), "policy": policy_snapshot(root)}
    sha = digest(record)
    target = root / "local/jev-protocols" / f"{sha}.json"
    value = {"sha256": sha, "record": record}
    if target.exists() and json.loads(target.read_text()) != value:
        raise LabError("Existing protocol snapshot differs; refusing to replace it")
    if not target.exists():
        write_json(target, value)
    return {"snapshot_path": str(target.relative_to(root)), "sha256": sha,
            "scientific_gate": "not_evaluated", "launch_authorized": False,
            "note": "Protocol snapshot only. Existing campaign freeze and handoff are still required."}
