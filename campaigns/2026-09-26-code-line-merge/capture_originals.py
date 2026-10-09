#!/usr/bin/env python3
"""Capture actual merge inputs as immutable reference archives, without ML imports."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


CAMPAIGN = Path(__file__).resolve().parent
LAB = CAMPAIGN.parents[1]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encoded(obj):
    return (json.dumps(obj, sort_keys=True, indent=2) + "\n").encode()


def write_readonly(path, content):
    if path.exists():
        if path.read_bytes() != content:
            raise RuntimeError(f"Refusing to overwrite different capture: {path}")
    else:
        with path.open("xb") as stream:
            stream.write(content)
    path.chmod(0o444)


def main():
    inventory_path = CAMPAIGN / "inventory_20261001.json"
    inventory_bytes = inventory_path.read_bytes()
    inventory = json.loads(inventory_bytes)
    dest = CAMPAIGN / "originals"
    dest.mkdir(exist_ok=True)
    records = []
    for side, root in inventory["roots"].items():
        entries, contents = [], {}
        for row in inventory["files"]:
            ref = row["sides"][side]
            if ref is None:
                continue
            path = LAB / root / row["path"]
            if path.is_symlink() or not path.is_file():
                raise RuntimeError(f"Invalid source: {path}")
            data = path.read_bytes()
            if sha(data) != ref["sha256"] or len(data) != ref["size_bytes"]:
                raise RuntimeError(f"Source differs from reviewed inventory: {path}")
            contents[row["path"]] = data
            entries.append({"path": row["path"], "sha256": sha(data), "size_bytes": len(data)})
        manifest = {"schema_version": 1, "side": side, "source_root": root,
                    "inventory_sha256": sha(inventory_bytes), "files": entries,
                    "scope": "Actual regular source/config working files listed in inventory; not a historical training-source reconstruction."}
        manifest_bytes = encoded(manifest)
        raw = io.BytesIO()
        with tarfile.open(fileobj=raw, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for name, data in [("SOURCE_MANIFEST.json", manifest_bytes),
                               *[("hgq2/" + p, d) for p, d in sorted(contents.items())]]:
                member = tarfile.TarInfo(name)
                member.size, member.mode = len(data), 0o444
                member.mtime, member.uid, member.gid = 0, 0, 0
                member.uname = member.gname = ""
                tar.addfile(member, io.BytesIO(data))
        archive = gzip.compress(raw.getvalue(), compresslevel=9, mtime=0)
        archive_sha = sha(archive)
        archive_path = dest / f"{side}-{archive_sha}.tar.gz"
        write_readonly(archive_path, archive)
        manifest_path = dest / f"{side}-{sha(manifest_bytes)}.manifest.json"
        write_readonly(manifest_path, manifest_bytes)
        with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
            for entry in entries:
                assert sha(tar.extractfile("hgq2/" + entry["path"]).read()) == entry["sha256"]
        records.append({"side": side, "file_count": len(entries),
                        "archive": str(archive_path.relative_to(CAMPAIGN)),
                        "archive_sha256": archive_sha,
                        "manifest": str(manifest_path.relative_to(CAMPAIGN)),
                        "manifest_sha256": sha(manifest_bytes),
                        "verified_each_archive_member": True, "mode": "0444"})
    capture = {"schema_version": 1, "date": "2026-10-01",
               "inventory_sha256": sha(inventory_bytes), "originals": records,
               "baseline_execution": "Only verified archive members may populate temporary read-only subprocess inputs; delete temporary inputs after execution. No active editing checkout is created."}
    write_readonly(dest / "capture_20261001.json", encoded(capture))

    references = []
    for path in sorted({p["train_meta_path"] for p in inventory["checkpoints"] if p["train_meta_path"]}):
        data = (LAB / path).read_bytes()
        meta = json.loads(data)
        references.append({
            "metadata_path": path, "metadata_sha256": sha(data),
            "config_name": meta.get("config"), "config_hash_lookup_only": meta.get("config_hash"),
            "seed": meta.get("seed"),
            "metric_reference": {"quantity": "validation_macro_ovr_auc",
                                 "json_field": "best_val_macro_auc",
                                 "present": "best_val_macro_auc" in meta,
                                 "split": "internal validation; exact dataset and row identities pending",
                                 "n_field": "n_val", "n": meta.get("n_val")},
            "selection_rule_field_present": "selection_rule" in meta,
            "has_budget_record": "ebops_budget" in meta,
            "checkpoint_candidates": [p["path"] for p in inventory["checkpoints"] if p["train_meta_path"] == path],
            "applicability": "CANDIDATE: establish saved checkpoint-to-selected-metric relation before requiring replay; adjacent metadata alone is insufficient for Pareto/front or unconstrained checkpoints.",
            "metric_gate_status": "PENDING_PROVENANCE",
        })
    ref_payload = {"schema_version": 1, "date": "2026-10-01",
                   "method": "Metadata references only; no metric recomputed, no model or dataset arrays read.",
                   "references": references,
                   "unidentified_checkpoint_paths": [p["path"] for p in inventory["checkpoints"] if not p["train_meta_path"]],
                   "configs_without_exact_hash_metadata_candidates": [c["path"] for c in inventory["model_configs"] if not c["checkpoint_candidates_by_exact_config_hash"]],
                   "convention": "docs/conventions/quantization-and-cost.md:43-45; applicable metric tolerance 1e-7 with TF32 off",
                   "no_run_inference": "Missing metadata does not prove a config was never run. Unknown remains unknown."}
    ref_path = CAMPAIGN / "metric_reference_inventory_20261001.json"
    write_readonly(ref_path, encoded(ref_payload))
    print(json.dumps({"originals": records, "metadata_reference_candidates": len(references),
                      "reference_inventory": str(ref_path.relative_to(CAMPAIGN))}, indent=2))


if __name__ == "__main__":
    main()
