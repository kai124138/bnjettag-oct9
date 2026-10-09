"""Deterministically reload and evaluate the frozen A02/A11 selected checkpoints."""
from __future__ import annotations

import gc
import hashlib
import json
import os
from pathlib import Path
import time

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
os.environ.setdefault("WANDB_MODE", "disabled")
os.environ.setdefault("NVIDIA_TF32_OVERRIDE", "0")

import keras
import numpy as np
from sklearn.metrics import confusion_matrix, roc_auc_score
import tensorflow as tf

from bnhgq2.compat import apply_keras_compat
from bnhgq2.data import apply_input_std, load_eval_set
import bnhgq2.qat  # noqa: F401 -- register custom layers


ROOT = Path("/data/batch20260917/n8")
OUTPUT = Path("/data/confirmation-20260923/eval-a02-a11-r4")
ARMS = ("batch20260917-a02-s1", "batch20260917-a11-s1")
HISTORICAL_METRIC_TOLERANCE = 1e-6


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def softmax(logits: np.ndarray) -> np.ndarray:
    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp / exp.sum(axis=1, keepdims=True)


def predict(model, values: np.ndarray, batch_size: int = 4096) -> tuple[np.ndarray, float]:
    signature = tf.TensorSpec([None, 8, 3], tf.float32)

    @tf.function(input_signature=[signature], reduce_retracing=True)
    def infer(batch):
        return model(batch, training=False)

    infer(np.asarray(values[:8], dtype=np.float32))
    start = time.perf_counter()
    result = np.concatenate([
        np.asarray(infer(np.asarray(values[i:i + batch_size], dtype=np.float32)))
        for i in range(0, len(values), batch_size)
    ])
    seconds = time.perf_counter() - start
    assert result.shape == (len(values), 5) and np.isfinite(result).all()
    return result, seconds


def metrics(logits: np.ndarray, labels: np.ndarray) -> dict:
    scores = softmax(logits.astype(np.float64))
    truth = labels.argmax(axis=1)
    pred = scores.argmax(axis=1)
    # Mirror the training callback exactly.  The multiclass sklearn API follows
    # a separate validation path and need not be bit-identical across versions.
    per_class = np.asarray([
        roc_auc_score(labels[:, class_index], scores[:, class_index])
        for class_index in range(labels.shape[1])
    ])
    return {
        "categorical_accuracy": float((pred == truth).mean()),
        "macro_ovr_auc": float(per_class.mean()),
        "per_class_ovr_auc": {name: float(value) for name, value in zip(("g", "q", "W", "Z", "t"), per_class)},
        "confusion_matrix": confusion_matrix(truth, pred, labels=range(5)).tolist(),
    }


def load_and_predict(path: Path, validation: np.ndarray, held_out: np.ndarray):
    model = keras.models.load_model(path, compile=False)
    validation_logits, validation_seconds = predict(model, validation)
    held_out_logits, held_out_seconds = predict(model, held_out)
    del model
    keras.utils.clear_session()
    gc.collect()
    return validation_logits, held_out_logits, validation_seconds, held_out_seconds


def main():
    tf.config.threading.set_intra_op_parallelism_threads(4)
    tf.config.threading.set_inter_op_parallelism_threads(2)
    tf.config.experimental.enable_op_determinism()
    apply_keras_compat()
    OUTPUT.mkdir(parents=True, exist_ok=False)

    validation_x = np.load(ROOT / "data/x_val.npy", mmap_mode="r")
    validation_y = np.load(ROOT / "data/y_val.npy")
    held_out_x, held_out_y = load_eval_set(
        "/data/hls4ml_lhc_jet/val/val", n_part=8, features=["pt", "etarel", "phirel"]
    )
    assert validation_x.shape == (124000, 8, 3) and held_out_x.shape == (260000, 8, 3)
    report = {
        "scope": "Frozen selected-checkpoint evaluation; held-out data are never used for selection.",
        "versions": {"numpy": np.__version__, "tensorflow": tf.__version__, "keras": keras.__version__},
        "devices": [device.name for device in tf.config.list_physical_devices()],
        "inference_batch_size": 4096,
        "historical_metric_tolerance": HISTORICAL_METRIC_TOLERANCE,
        "determinism_tolerance": 1e-7,
        "runs": [],
    }
    for arm in ARMS:
        run = ROOT / "runs" / arm
        assert (run / "COMPLETE.json").exists()
        generation = json.loads((run / "latest.json").read_text())["checkpoint"]
        checkpoint = run / "checkpoints" / generation
        state = json.loads((checkpoint / "state.json").read_text())
        selected = state["best_feasible"]
        assert selected is not None
        model_path = checkpoint / "model_best.keras"
        std = json.loads((run / "input_std.json").read_text())
        held_out_std = apply_input_std(held_out_x, std["mu"], std["sigma"])

        val1, test1, val_seconds, test_seconds = load_and_predict(model_path, validation_x, held_out_std)
        val2, test2, _, _ = load_and_predict(model_path, validation_x, held_out_std)
        val_max_abs = float(np.max(np.abs(val1 - val2)))
        test_max_abs = float(np.max(np.abs(test1 - test2)))
        assert val_max_abs <= 1e-7 and test_max_abs <= 1e-7
        validation_metrics = metrics(val1, validation_y)
        held_out_metrics = metrics(test1, held_out_y)
        print("VALIDATION_REPLAY=" + json.dumps({
            "arm": arm,
            "selected": selected,
            "replayed": validation_metrics,
            "accuracy_delta": validation_metrics["categorical_accuracy"] - selected["val_categorical_accuracy"],
            "auc_delta": validation_metrics["macro_ovr_auc"] - selected["val_macro_auc"],
        }, sort_keys=True), flush=True)
        accuracy_delta = validation_metrics["categorical_accuracy"] - selected["val_categorical_accuracy"]
        auc_delta = validation_metrics["macro_ovr_auc"] - selected["val_macro_auc"]
        assert abs(accuracy_delta) <= HISTORICAL_METRIC_TOLERANCE
        assert abs(auc_delta) <= HISTORICAL_METRIC_TOLERANCE

        prediction_path = OUTPUT / f"{arm}.npz"
        np.savez_compressed(prediction_path, validation_logits=val1, held_out_logits=test1)
        row = {
            "arm": arm,
            "checkpoint_generation": generation,
            "checkpoint_sha256": digest(model_path),
            "selected": selected,
            "validation": validation_metrics,
            "held_out": held_out_metrics,
            "historical_validation_delta": {"categorical_accuracy": accuracy_delta, "macro_ovr_auc": auc_delta},
            "reload_max_abs_logit_difference": {"validation": val_max_abs, "held_out": test_max_abs},
            "inference_seconds": {"validation": val_seconds, "held_out": test_seconds},
            "prediction_sha256": digest(prediction_path),
        }
        report["runs"].append(row)
        (OUTPUT / "results.json").write_text(json.dumps(report, indent=2) + "\n")
        print("RESULT=" + json.dumps(row, sort_keys=True), flush=True)
        del val1, val2, test1, test2, held_out_std
        gc.collect()
    print("DETERMINISTIC_EVALUATION_PASS", flush=True)


if __name__ == "__main__":
    main()
