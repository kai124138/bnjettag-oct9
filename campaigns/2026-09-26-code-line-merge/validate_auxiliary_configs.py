#!/usr/bin/env python3
"""Validate preserved non-model config structure without importing ML packages."""
import hashlib
import json
import tarfile
from pathlib import Path

CAMPAIGN = Path(__file__).resolve().parent
LAB = CAMPAIGN.parents[1]
CANDIDATE = LAB / "publication/code/hgq2"


def main():
    capture = json.loads((CAMPAIGN / "originals/capture_20261001.json").read_text())
    public = next(row for row in capture["originals"] if row["side"] == "publication")
    archive = CAMPAIGN / public["archive"]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == public["archive_sha256"]
    rows = []
    with tarfile.open(archive, "r:gz") as source:
        for relative in ("configs/layer-configs-da13.json", "configs/batch20260918/index.json"):
            original = source.extractfile("hgq2/" + relative).read()
            current = (CANDIDATE / relative).read_bytes()
            assert current == original, relative
            data = json.loads(current)
            if "runs" in data:
                runs = data["runs"]
                assert [row["index"] for row in runs] == list(range(len(runs)))
                assert len({row["name"] for row in runs}) == len(runs)
                for row in runs:
                    config = json.loads((CANDIDATE / "configs/batch20260918" / (row["name"] + ".json")).read_text())
                    assert config["name"] == row["name"]
                    assert isinstance(row["seed"], int) and row["seed"] > 0
                    assert config["experiment"]["seed"] == row["seed"]
                    assert config["experiment"]["arm"] == row["name"]
                assert (CANDIDATE / "configs/batch20260917" / (data["reference"] + ".json")).is_file()
                details = {"index_entries": len(runs), "referenced_configs_present": True}
            else:
                assert isinstance(data, dict) and data
                assert all(isinstance(name, str) and isinstance(options, dict) and options == {"Strategy": "distributed_arithmetic"} for name, options in data.items())
                details = {"layer_override_entries": len(data), "scope": "JSON structure and preserved bytes; HLS applicability pending synthesis"}
            rows.append({"path": relative, "sha256": hashlib.sha256(current).hexdigest(), "status": "PASS", **details})
    report = {"status": "PASS", "scope": "non-model JSON structural validation only", "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "rows": rows}
    (CAMPAIGN / "evidence/auxiliary_configs_v1.json").write_text(json.dumps(report, indent=2) + "\n")
    print("PASS", len(rows), "non-model JSON identities")


if __name__ == "__main__":
    main()
