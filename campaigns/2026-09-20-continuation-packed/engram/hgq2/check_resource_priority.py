#!/usr/bin/env python3
"""Cost-priority checkpoint/stop checks; cluster-only synthetic trainer integration."""
import copy
import json
import os
from pathlib import Path
import sys
import tempfile

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
if "--gpu" not in sys.argv:
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
import keras
import numpy as np
import tensorflow as tf
from bnhgq2.compat import apply_keras_compat
from bnhgq2 import qat
from bnhgq2.ebops_calc import compute_ebops
from bnhgq2.ebops_target import BudgetMonitor
from bnhgq2.train import ebops_callbacks
from hgq.utils.sugar import BetaPID
sys.path.insert(0, str(Path(__file__).parent / "configs"))
from gen_ebops_n8 import make_cost_first


def main():
    apply_keras_compat()
    if "--gpu" in sys.argv:
        assert tf.config.list_physical_devices("GPU"), "GPU is required for this smoke"
    cfg = make_cost_first()
    x = np.random.default_rng(1).normal(size=(8, 8, 3)).astype("float32")
    model, _ = qat.build_qat_model(cfg, seed=1)
    with tempfile.TemporaryDirectory() as out:
        monitor = BudgetMonitor(model, x, cfg, out)
        monitor.set_model(model)
        cbs, _ = ebops_callbacks(monitor.runtime_cfg, out, monitor)
        pid = next(c for c in cbs if isinstance(c, BetaPID))
        pid.set_model(model)
        pid.on_train_begin({})
        pid.on_epoch_begin(0, {})
        beta0 = pid.beta
        pid.on_epoch_end(0, {})
        pid.on_epoch_begin(1, {})
        assert pid.beta > beta0 >= 1e-4
        monitor.on_epoch_end(0, {"val_macro_auc": .9})
        assert monitor.best is None and monitor.lowest["epoch"] == 0
        assert not getattr(model, "stop_training", False)
        q = model.get_layer("input_proj").iq.quantizer
        q._f.assign(q._f - 1)
        # Lower accuracy MUST NOT prevent the cheaper checkpoint from replacing it.
        monitor.on_epoch_end(1, {"val_macro_auc": .5})
        assert monitor.lowest["epoch"] == 1
        saved = keras.models.load_model(Path(out) / "model_min_ebops.keras", compile=False)
        assert compute_ebops(saved, x)["total"] == monitor.lowest["ebops"]
        monitor.target = monitor.lowest["ebops"]
        monitor.on_epoch_end(2, {"val_macro_auc": .5})
        assert monitor.best["epoch"] == 2 and model.stop_training
        saved = keras.models.load_model(Path(out) / "model_best.keras", compile=False)
        assert compute_ebops(saved, x)["total"] <= monitor.target
        monitor.stop_on_target = False
        q._f.assign(q._f - 1)
        monitor.on_epoch_end(3, {"val_macro_auc": .4})
        assert monitor.best["epoch"] == 3, "Feasible selection must also ignore AUC"
    if "--integration" in sys.argv:
        from bnhgq2 import train as trainer, wandb_util
        rng = np.random.default_rng(10)
        sx = rng.normal(size=(400, 8, 3)).astype("float32")
        sy = np.eye(5, dtype="float32")[np.arange(400) % 5]
        trainer.load_train_data = lambda *a, **kw: (sx.copy(), sy.copy(), 1)
        wandb_util.wandb_enabled = lambda *a, **kw: False
        for feasible in (True, False):
            c = copy.deepcopy(cfg)
            c["train"]["epochs"] = 2
            c["train"]["ebops"]["pid"]["target_ebops"] = 1e9 if feasible else 1.
            with tempfile.TemporaryDirectory() as out:
                meta = trainer.train(c, seed=1, out_dir=out)
                result = meta["ebops_budget"]
                assert result["budget_met"] is feasible
                assert meta["jit_compile"] is False
                assert meta["epochs_run"] == (1 if feasible else 2)
                assert result["checkpoint"] == ("model_best.keras" if feasible else "model_min_ebops.keras")
                history = [json.loads(s) for s in (Path(out) / "activation_widths.jsonl").read_text().splitlines()]
                assert result["checkpoint_ebops"] == min(r["ebops"] for r in history)
                if not feasible:
                    assert result["best_feasible"] is None
    print("EBOPS_COSTFIRST_ALL_PASS", flush=True)


if __name__ == "__main__":
    main()
