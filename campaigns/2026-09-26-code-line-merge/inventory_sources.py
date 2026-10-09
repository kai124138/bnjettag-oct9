#!/usr/bin/env python3
"""Inventory merge inputs without importing ML packages or reading model arrays."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path


LAB = Path(__file__).resolve().parents[2]
ROOTS = {
    "research": LAB / "bnjettag/code/hgq2",
    "publication": LAB / "publication/code/hgq2",
}
EXCLUDED = {"__pycache__", ".git", "wandb", "outputs", "slack"}
CHECKPOINT_ROOTS = [
    LAB / "bnjettag/models",
    LAB / "bnjettag/roc-results",
    LAB / "bnjettag/results",
    LAB / "publication/outputs/models",
    LAB / "publication/results/predictions",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical_sha(obj):
    return sha(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())


class RemoveDocstrings(ast.NodeTransformer):
    def visit(self, node):
        node = super().visit(node)
        if (
            hasattr(node, "body")
            and isinstance(node.body, list)
            and node.body
            and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)
        ):
            node.body = node.body[1:]
        return node


def walk_config_diff(a, b, prefix=""):
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            path = f"{prefix}.{key}" if prefix else key
            if key not in a or key not in b:
                result.append(path)
            else:
                result.extend(walk_config_diff(a[key], b[key], path))
        return result
    return [] if a == b else [prefix]


def main():
    files = {
        side: {
            p.relative_to(root).as_posix(): p
            for p in root.rglob("*")
            if p.is_file()
            and not p.is_symlink()
            and not set(p.relative_to(root).parts) & EXCLUDED
        }
        for side, root in ROOTS.items()
    }
    rows, configs = [], []
    for name in sorted(set().union(*(set(v) for v in files.values()))):
        paths = {side: entries.get(name) for side, entries in files.items()}
        kind = "python" if name.endswith(".py") else "other"
        if name.startswith("configs/") and name.endswith(".json"):
            kind = "config"
        row = {"path": name, "kind": kind, "sides": {}}
        for side, p in paths.items():
            row["sides"][side] = (
                {"sha256": sha(p.read_bytes()), "size_bytes": p.stat().st_size}
                if p else None
            )
        if paths["publication"] is None:
            status = "research_only"
        elif paths["research"] is None:
            status = "publication_only"
        elif row["sides"]["research"]["sha256"] == row["sides"]["publication"]["sha256"]:
            status = "identical"
        else:
            status = "different"
        row["status"] = status
        if status == "different" and kind == "python":
            trees = [ast.parse(p.read_text()) for p in paths.values()]
            row["python_ast_equal"] = ast.dump(trees[0]) == ast.dump(trees[1])
            trees = [RemoveDocstrings().visit(t) for t in trees]
            row["python_ast_equal_ignoring_docstrings"] = ast.dump(trees[0]) == ast.dump(trees[1])
        if kind == "config":
            row["json"] = {}
            for side, p in paths.items():
                if p is None:
                    continue
                obj = json.loads(p.read_text())
                is_model = isinstance(obj, dict) and {"arch", "quant", "name"} <= obj.keys()
                role = "model" if is_model else "index" if p.name == "index.json" else "layer_override"
                row["json"][side] = {"canonical_sha256": canonical_sha(obj), "role": role}
                if is_model:
                    configs.append({
                        "side": side, "path": str(p.relative_to(LAB)),
                        "name": obj["name"], "canonical_sha256": canonical_sha(obj),
                        "config_hash": canonical_sha(obj)[:8],
                        "arch_quant_sha256": canonical_sha({k: obj[k] for k in ("arch", "quant")}),
                        "kind": "train" if "train" in obj else "rebuild", "data": obj,
                    })
        rows.append(row)

    by_arch = {}
    for c in configs:
        by_arch.setdefault(c["arch_quant_sha256"], []).append(c)
    matches = []
    for group in by_arch.values():
        for a in (c for c in group if c["side"] == "research"):
            for b in (c for c in group if c["side"] == "publication"):
                matches.append({
                    "research": a["path"], "publication": b["path"],
                    "equal_arch_and_quant": True,
                    "different_config_fields": walk_config_diff(a["data"], b["data"]),
                    "equivalence_warning": "Equal arch/quant does not establish equal training or provenance.",
                })

    checkpoints = []
    for root in CHECKPOINT_ROOTS:
        for p in sorted(root.rglob("*.keras")) if root.exists() else []:
            if p.is_symlink():
                continue
            meta = p.with_name("train_meta.json")
            obj = json.loads(meta.read_text()) if meta.exists() else {}
            checkpoints.append({
                "path": str(p.relative_to(LAB)), "size_bytes": p.stat().st_size,
                "train_meta_path": str(meta.relative_to(LAB)) if meta.exists() else None,
                "train_meta_sha256": sha(meta.read_bytes()) if meta.exists() else None,
                "config": obj.get("config"), "config_hash": obj.get("config_hash"),
                "seed": obj.get("seed"), "input_std_present": p.with_name("input_std.json").exists(),
                "checkpoint_content_not_read": True,
            })
    for c in configs:
        c.pop("data")
        c["checkpoint_candidates_by_exact_config_hash"] = [
            p["path"] for p in checkpoints if p["config_hash"] == c["config_hash"]
        ]
        c["checkpoint_candidates_by_exact_config_name"] = [
            p["path"] for p in checkpoints if p["config"] == c["name"]
        ]
        c["checkpoint_reload_status"] = "pending"
    counts = {
        "file_union": len(rows),
        "by_status": dict(Counter(r["status"] for r in rows)),
        "by_kind": dict(Counter(r["kind"] for r in rows)),
        "python_differences_beyond_docstrings": sum(
            r["kind"] == "python" and r["status"] == "different"
            and not r["python_ast_equal_ignoring_docstrings"] for r in rows),
        "python_docstring_only_differences": sum(r.get("python_ast_equal_ignoring_docstrings", False) for r in rows),
        "model_configs_by_side": dict(Counter(c["side"] for c in configs)),
        "checkpoint_files": len(checkpoints),
        "checkpoint_metadata_config_seed_identities": len({(p["config"], p["seed"]) for p in checkpoints if p["config"]}),
        "configs_with_exact_hash_checkpoint_metadata": sum(bool(c["checkpoint_candidates_by_exact_config_hash"]) for c in configs),
    }
    inventory = {
        "schema_version": 1, "date": "2026-10-01",
        "roots": {s: str(p.relative_to(LAB)) for s, p in ROOTS.items()},
        "excluded_path_components": sorted(EXCLUDED),
        "method": "Regular non-symlink files; hashes and Python AST after removing docstrings; checkpoints inspected by stat and adjacent train_meta.json only. No model arrays or scientific metrics read.",
        "counts": counts, "files": rows, "model_configs": configs,
        "architecture_quantizer_matches": matches,
        "checkpoint_roots": [{"path": str(p.relative_to(LAB)), "exists": p.exists()} for p in CHECKPOINT_ROOTS],
        "checkpoints": checkpoints,
        "gates": {"design_review": "pending", "cpu_build": "pending", "historical_reload": "pending", "training": "not_authorized_by_this_inventory"},
    }
    out = Path(__file__).with_name("inventory_20261001.json")
    out.write_text(json.dumps(inventory, indent=2) + "\n")
    print(json.dumps(counts, indent=2))


if __name__ == "__main__":
    main()
