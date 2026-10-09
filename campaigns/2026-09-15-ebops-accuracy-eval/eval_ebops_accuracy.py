#!/usr/bin/env python3
"""Evaluate EBOP-ablation checkpoints with top-1 categorical accuracy.

The reported test metric is mean(argmax(model output) == argmax(label)) on the
full 260,000-jet held-out split. The internal 124,000-jet validation accuracy is
also recorded, but model selection remains the pre-registered validation AUC.
"""
from __future__ import annotations

import gc
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

import numpy as np


CODE_DIR = Path("/work/code")
ROOT = Path("/data/ebops-n8-20260912-ablation")
RUN_ROOT = ROOT / "runs"
TEST_DATA = Path("/data/hls4ml_lhc_jet/val/val")
OUTPUT_DIR = ROOT / "evaluation"
OUTPUT_JSON = OUTPUT_DIR / "categorical_accuracy_260k.json"
OUTPUT_MD = OUTPUT_DIR / "categorical_accuracy_260k.md"
SNAPSHOT_DIR = Path("/work/checkpoint-snapshots")
DEFAULT_ARMS = (
    "r0-baseline",
    "r1-channel",
    "r2-ffn32",
    "r3-prob8",
    "r4-gradual",
    "r5-recovery",
    "r6-distill",
)
ARMS = tuple(
    arm.strip()
    for arm in os.environ.get("EVAL_ARMS", ",".join(DEFAULT_ARMS)).split(",")
    if arm.strip()
)
MERGE_EXISTING = os.environ.get("MERGE_EXISTING", "0") == "1"

sys.path.insert(0, str(CODE_DIR))

from bnhgq2.compat import apply_keras_compat  # noqa: E402
from bnhgq2.data import apply_input_std, load_eval_set  # noqa: E402
from bnhgq2.subln import register_subln  # noqa: E402
import bnhgq2.qat  # noqa: F401,E402 - registers custom Keras layers
import keras  # noqa: E402
import tensorflow as tf  # noqa: E402


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    os.replace(temporary, path)


def write_markdown(payload: dict) -> None:
    lines = [
        "# EBOP-ablation categorical accuracy",
        "",
        "Top-1 categorical accuracy is computed as `mean(argmax(logits) == argmax(labels))`.",
        "The test column uses the full held-out 260,000-jet split; validation contains 124,000 jets.",
        "",
        "| Run | Status at evaluation | EBOPs | Selected validation AUC | Validation accuracy | Test accuracy |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for record in payload["runs"]:
        if "test_accuracy" not in record:
            lines.append(
                f"| {record['run']} | {record['status']} | — | — | — | — |"
            )
            continue
        lines.append(
            f"| {record['run']} | {record['status']} | {record['ebops']:,} "
            f"| {record['selected_val_macro_auc']:.4f} "
            f"| {100 * record['validation_accuracy']:.2f}% "
            f"| **{100 * record['test_accuracy']:.2f}%** |"
        )
    lines += [
        "",
        "R3 and R6 values are checkpoint snapshots, not final completed-run results.",
        "R4 has no point until a checkpoint satisfies the final 350k-EBOP constraint.",
        "",
    ]
    temporary = OUTPUT_MD.with_suffix(".md.tmp")
    temporary.write_text("\n".join(lines))
    os.replace(temporary, OUTPUT_MD)


def snapshot_file(source: Path, destination: Path) -> str:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    shutil.copyfile(source, temporary)
    os.replace(temporary, destination)
    return sha256(destination)


def load_model(path: Path):
    apply_keras_compat()
    register_subln()
    return keras.models.load_model(path)


def top1_accuracy(model, x, y, *, mu=None, sigma=None, batch_size=4096) -> float:
    correct = 0
    count = 0
    for start in range(0, len(x), batch_size):
        stop = min(start + batch_size, len(x))
        xb = np.asarray(x[start:stop], dtype=np.float32)
        if mu is not None:
            xb = apply_input_std(xb, mu, sigma)
        logits = np.asarray(model(xb, training=False))
        if not np.isfinite(logits).all():
            raise RuntimeError(f"non-finite output in rows {start}:{stop}")
        truth = np.asarray(y[start:stop]).argmax(axis=1)
        correct += int(np.count_nonzero(logits.argmax(axis=1) == truth))
        count += stop - start
    return correct / count


def save(payload: dict) -> None:
    order = {arm: index for index, arm in enumerate(DEFAULT_ARMS)}
    payload["runs"].sort(key=lambda item: order.get(item["arm"], len(order)))
    atomic_json(OUTPUT_JSON, payload)
    write_markdown(payload)


def selected_metadata(run_dir: Path) -> tuple[dict | None, str]:
    budget_file = run_dir / "ebops_budget.json"
    if budget_file.exists():
        return json.loads(budget_file.read_text())["selected"], "final budget record"

    latest_file = run_dir / "latest.json"
    if not latest_file.exists():
        return None, "missing latest checkpoint metadata"
    latest = json.loads(latest_file.read_text())["checkpoint"]
    state_file = run_dir / "checkpoints" / latest / "state.json"
    if not state_file.exists():
        return None, "missing resumable checkpoint state"
    state = json.loads(state_file.read_text())
    return state.get("best_feasible"), f"resumable checkpoint {latest}"


def main() -> None:
    tf.config.set_visible_devices([], "GPU")
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)

    print(f"[data] loading held-out split from {TEST_DATA}", flush=True)
    x_test, y_test = load_eval_set(
        str(TEST_DATA), n_part=8, features=["pt", "etarel", "phirel"]
    )
    if len(x_test) != 260_000 or y_test.shape != (260_000, 5):
        raise AssertionError(f"unexpected held-out shapes: {x_test.shape}, {y_test.shape}")
    x_val = np.load(ROOT / "data" / "x_val.npy", mmap_mode="r")
    y_val = np.load(ROOT / "data" / "y_val.npy", mmap_mode="r")
    if len(x_val) != 124_000 or y_val.shape != (124_000, 5):
        raise AssertionError(f"unexpected validation shapes: {x_val.shape}, {y_val.shape}")

    payload = {
        "generated_unix": time.time(),
        "definition": "mean(argmax(model_output, axis=1) == argmax(one_hot_label, axis=1))",
        "test_split": str(TEST_DATA),
        "n_test": int(len(x_test)),
        "n_validation": int(len(x_val)),
        "input": {"particles": 8, "features": ["pt", "etarel", "phirel"]},
        "versions": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "keras": keras.__version__,
            "tensorflow": tf.__version__,
        },
        "runs": [],
    }
    if MERGE_EXISTING and OUTPUT_JSON.exists():
        existing = json.loads(OUTPUT_JSON.read_text())
        payload["runs"] = existing.get("runs", [])
    save(payload)

    for arm in ARMS:
        run_dir = RUN_ROOT / arm
        checkpoint = run_dir / "model_best.keras"
        complete = (run_dir / "COMPLETE.json").exists()
        status = "finished" if complete else "interim checkpoint"
        selected, metadata_source = selected_metadata(run_dir)
        payload["runs"] = [record for record in payload["runs"] if record["arm"] != arm]
        if not checkpoint.exists() or selected is None:
            record = {
                "run": arm.split("-")[0].upper(),
                "arm": arm,
                "status": "no <=350k checkpoint yet",
            }
            payload["runs"].append(record)
            save(payload)
            print(f"[{arm}] skipped: no qualifying checkpoint", flush=True)
            continue

        snap_dir = SNAPSHOT_DIR / arm
        snap_checkpoint = snap_dir / "model_best.keras"
        snap_config = snap_dir / "config.json"
        snap_std = snap_dir / "input_std.json"
        checkpoint_sha = snapshot_file(checkpoint, snap_checkpoint)
        snapshot_file(run_dir / "config.json", snap_config)
        snapshot_file(run_dir / "input_std.json", snap_std)
        config = json.loads(snap_config.read_text())
        if config["arch"]["n_part"] != 8 or config["arch"]["features"] != ["pt", "etarel", "phirel"]:
            raise AssertionError(f"{arm}: unexpected input config")
        std = json.loads(snap_std.read_text())

        print(f"[{arm}] loading selected checkpoint {checkpoint_sha[:12]}", flush=True)
        model = load_model(snap_checkpoint)
        validation_accuracy = top1_accuracy(model, x_val, y_val)
        test_accuracy = top1_accuracy(
            model, x_test, y_test, mu=std["mu"], sigma=std["sigma"]
        )
        record = {
            "run": arm.split("-")[0].upper(),
            "arm": arm,
            "status": status,
            "selection_metadata_source": metadata_source,
            "checkpoint_sha256": checkpoint_sha,
            "selected_epoch_zero_based": int(selected["epoch"]),
            "selected_epoch_one_based": int(selected["epoch"]) + 1,
            "ebops": int(selected["ebops"]),
            "selected_val_macro_auc": float(selected["val_macro_auc"]),
            "validation_accuracy": float(validation_accuracy),
            "test_accuracy": float(test_accuracy),
        }
        payload["runs"].append(record)
        save(payload)
        print(
            f"[{arm}] val_acc={validation_accuracy:.8f} "
            f"test_acc={test_accuracy:.8f}",
            flush=True,
        )
        del model
        keras.utils.clear_session()
        gc.collect()

    print(f"[done] {OUTPUT_JSON}", flush=True)
    print(f"[done] {OUTPUT_MD}", flush=True)


if __name__ == "__main__":
    main()
