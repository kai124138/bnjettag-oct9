"""CPU preflight for the six immutable A00/A02/A03 seed-confirmation configs."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
os.environ.setdefault("WANDB_MODE", "disabled")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
os.environ.setdefault("NVIDIA_TF32_OVERRIDE", "0")

import keras
import numpy as np

import run_engram


def cfg_digest(cfg):
    return hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest()


def main():
    index = json.loads(Path("/configs/index.json").read_text())
    configs = [json.loads((Path("/configs") / row["file"]).read_text()) for row in index["runs"]]
    assert len(configs) == 6
    assert {(cfg["experiment"]["seed"], cfg["experiment"]["source_arm"]) for cfg in configs} == {
        (seed, arm) for seed in (2, 3) for arm in ("a00", "a02", "a03")
    }
    arrays, info = run_engram.load_cache(Path("/data/constituent-study-20260922/n8/data"), configs[0])
    sample = np.asarray(arrays[0][:256])
    reports = []
    for cfg in configs:
        run_engram.validate_cfg(cfg)
        assert cfg["train"]["epochs"] == 1000
        assert cfg["train"]["batch"] == 256
        assert cfg["train"]["val_batch"] == 4096
        assert cfg["train"]["lr"] == 2e-5
        assert cfg["train"]["ebops"]["pid"]["warmup"] == 10
        assert cfg["train"]["ebops"]["selection"] == "max_accuracy"
        model, evidence = run_engram.builder_for(info)(cfg, sample, cfg["experiment"]["seed"])
        ablation, _ = run_engram.runtime()
        trace = ablation.compute_ebops(model, sample[:32])
        expected = np.asarray(model(sample[:16], training=False))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.keras"
            model.save(path)
            loaded = keras.models.load_model(path, compile=False)
            np.testing.assert_allclose(loaded(sample[:16], training=False), expected, atol=2e-6, rtol=2e-6)
            retrace = ablation.compute_ebops(loaded, sample[:32])
            assert retrace["total"] == trace["total"]
        reports.append({
            "name": cfg["name"],
            "config_sha256": cfg_digest(cfg),
            "parameters": model.count_params(),
            "initial_ebops": trace["total"],
            "initialization": evidence,
        })
        del model, loaded
        keras.utils.clear_session()
        print("CONFIG_PREFLIGHT_PASS", cfg["name"], flush=True)
    result = {
        "status": "PASS",
        "source": run_engram.source_manifest(),
        "data": info["engram_array_sha256"],
        "configs": reports,
    }
    Path("/work/preflight.json").write_text(json.dumps(result, indent=2) + "\n")
    print("PREFLIGHT_ALL_PASS " + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
