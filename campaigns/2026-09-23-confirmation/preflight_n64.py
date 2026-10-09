"""CPU preflight for full N64 A07/E02/E05 runs at five million eBOPs."""
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


def main():
    index = json.loads(Path("/configs/index-n64.json").read_text())
    configs = [json.loads((Path("/configs") / row["file"]).read_text()) for row in index["runs"]]
    assert {(cfg["experiment"]["seed"], cfg["experiment"]["source_arm"]) for cfg in configs} == {
        (seed, arm) for seed in (2, 3) for arm in ("a07", "e02", "e05")
    }
    arrays, info = run_engram.load_cache(Path("/data/constituent-study-20260922/n64/data"), configs[0])
    sample = np.asarray(arrays[0][:256])
    reports = []
    for cfg in configs:
        run_engram.validate_cfg(cfg)
        assert cfg["arch"]["n_part"] == 64
        assert cfg["train"]["epochs"] == 1000
        assert cfg["train"]["batch"] == 256
        assert cfg["train"]["decay_epochs"] == 999
        assert cfg["train"]["ebops"]["pid"]["target_ebops"] == 5_000_000
        model, evidence = run_engram.builder_for(info)(cfg, sample, cfg["experiment"]["seed"])
        ablation, engram = run_engram.runtime()
        trace = ablation.compute_ebops(model, sample[:32])
        expected = np.asarray(model(sample[:8], training=False))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.keras"
            model.save(path)
            loaded = keras.models.load_model(path, compile=False)
            np.testing.assert_allclose(loaded(sample[:8], training=False), expected, atol=2e-6, rtol=2e-6)
            assert ablation.compute_ebops(loaded, sample[:32])["total"] == trace["total"]
        spec = cfg["engram_study"]["module"]
        reports.append({
            "name": cfg["name"],
            "config_sha256": hashlib.sha256(json.dumps(cfg, sort_keys=True).encode()).hexdigest(),
            "parameters": model.count_params(),
            "initial_ebops": trace["total"],
            "memory": None if spec is None else engram.cost_ledger(spec, 64, cfg["arch"]["d_model"]),
            "initialization": evidence,
        })
        del model, loaded
        keras.utils.clear_session()
        print("CONFIG_PREFLIGHT_PASS", cfg["name"], flush=True)
    result = {"status": "PASS", "budget_ebops": 5_000_000,
              "source": run_engram.source_manifest(), "data": info["engram_array_sha256"],
              "configs": reports}
    print("PREFLIGHT_ALL_PASS " + json.dumps(result, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
