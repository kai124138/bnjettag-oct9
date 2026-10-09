#!/usr/bin/env python3
"""Local client compatibility for the single observed NRP admission environment value."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

PREPARATION_SHA = "8c69531f21c59b42cf5b24ed5cbf6cf2995f0882743fdb1f73798fec42a53a1a"
ALLOWED_POD_ENV = [{"name": "NVIDIA_VISIBLE_DEVICES", "value": "void"}]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def validate_with_admission(original, planned, configmap, access, pvc_uid):
    observed = access["pod"]["spec"]["containers"]
    assert len(observed) == 1, "unexpected Pod container count"
    env = observed[0].get("env")
    assert env is None or env == [] or env == ALLOWED_POD_ENV, "unreviewed Pod environment"
    checked = copy.deepcopy(access)
    if env == ALLOWED_POD_ENV:
        del checked["pod"]["spec"]["containers"][0]["env"]
    result = original(planned, configmap, checked, pvc_uid)
    result["local_receiver_sha256"] = sha(Path(__file__).read_bytes())
    result["admission_environment_exception"] = {
        "scope": "Pod container env only; original Job template and every other check unchanged",
        "observed": env,
        "captured_pod_canonical_sha256": sha(json.dumps(access["pod"], sort_keys=True).encode()),
        "validation_pod_canonical_sha256": sha(json.dumps(checked["pod"], sort_keys=True).encode()),
    }
    return result


def load_original(preparation, expected):
    assert expected == PREPARATION_SHA, "only the approved original preparation is supported"
    raw = preparation.read_bytes()
    assert sha(raw) == expected, "original preparation identity mismatch"
    record = json.loads(raw)
    for name, digest in record["files"].items():
        assert re.fullmatch(r"[A-Za-z0-9_.-]+", name)
        assert sha((preparation.parent / name).read_bytes()) == digest, "original frozen bytes changed"
    sys.path.insert(0, str(preparation.parent.resolve()))
    spec = importlib.util.spec_from_file_location("original_frozen_receiver", preparation.parent / "receive.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--expected-preparation-sha256", required=True)
    args, _ = parser.parse_known_args()
    module = load_original(args.preparation, args.expected_preparation_sha256)
    original = module.validate_access
    module.validate_access = lambda planned, cm, access, uid: validate_with_admission(original, planned, cm, access, uid)
    module.main()


if __name__ == "__main__":
    main()
