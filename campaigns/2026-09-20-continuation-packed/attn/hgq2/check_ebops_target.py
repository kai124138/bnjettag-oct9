#!/usr/bin/env python3
"""Cheap CPU preflight: real-model EBOP gradients, width movement, PID, reload.

No dataset training. A temporary one-bit perturbation verifies that changing the
free quantizer affects cost, then is restored. Run before submitting GPU jobs.
"""
import copy
import json
import os
from pathlib import Path
import tempfile
import sys

os.environ.setdefault("KERAS_BACKEND", "tensorflow")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
import keras
import numpy as np
import tensorflow as tf

from bnhgq2.compat import apply_keras_compat
from bnhgq2.config import load_config
from bnhgq2 import qat
from bnhgq2.ebops_calc import compute_ebops
from bnhgq2.ebops_target import BudgetMonitor, activation_quantizers, resolve_budget, width_snapshot
from bnhgq2.train import ebops_callbacks
from hgq.utils.sugar import BetaPID

apply_keras_compat()
ROOT = Path(__file__).parent


def main():
    cfgs = sorted(p for p in (ROOT / "configs").glob("post_conference_budget_pilot-*.json")
                  if "costfirst" not in p.name)
    assert len(cfgs) == 4
    cfg = load_config(next(p for p in cfgs if "b75" in p.name))
    x = np.random.default_rng(1).normal(size=(8, 8, 3)).astype("float32")
    model, _ = qat.build_qat_model(cfg, seed=1)
    variables = []
    for name, q in activation_quantizers(model):
        if hasattr(q, "_f") and q.trainable:
            assert any(q._i is v for v in model.trainable_variables), name
            assert any(q._f is v for v in model.trainable_variables), name
            variables.extend([q._i, q._f])
    assert variables
    with tf.GradientTape() as tape:
        model(x, training=True)
        # Use the actual differentiable cost expression. Stored _ebops values are
        # assignments for reporting and cannot be used to test gradient flow.
        penalty = tf.add_n(model.losses)
    grads = tape.gradient(penalty, variables)
    assert all(g is not None and np.isfinite(g.numpy()).all() for g in grads)
    assert any(np.any(g.numpy() != 0) for g in grads)
    # Exclude tiny MonoL1 gradients: compare beta=0 and beta>0 explicitly.
    for layer in model._flatten_layers():
        if getattr(layer, "_beta", None) is not None:
            layer._beta.assign(0.)
    with tf.GradientTape() as tape:
        model(x, training=True)
        no_beta_penalty = tf.add_n(model.losses)
    no_beta_grads = tape.gradient(no_beta_penalty, variables)
    assert any(np.any(np.abs(a.numpy() - b.numpy()) > 1e-9)
               for a, b in zip(grads, no_beta_grads))
    before = compute_ebops(model, x)["total"]
    q = model.get_layer("input_proj").iq.quantizer
    original_f = q._f.numpy().copy()
    q._f.assign(original_f - 1)
    after = compute_ebops(model, x)["total"]
    assert after < before, (before, after)
    q._f.assign(original_f)
    # Frozen attention-probability operand remains explicitly reported as frozen.
    widths = width_snapshot(model)
    assert widths["input_proj"]["width_trainable"]
    assert not widths["bit_block_0_attn_ctx__in0"]["width_trainable"]
    old = copy.deepcopy(cfg)
    old["quant"]["act_calib"] = "trainable"
    try:
        resolve_budget(old, before)
        raise AssertionError("Fixed-width PID was accepted")
    except ValueError:
        pass
    for bad in (0, -1, float("nan")):
        old = copy.deepcopy(cfg)
        old["train"]["ebops"]["pid"]["init_beta"] = bad
        try:
            resolve_budget(old, before)
            raise AssertionError("Invalid initial beta was accepted")
        except ValueError:
            pass
    with tempfile.TemporaryDirectory() as out:
        monitor = BudgetMonitor(model, x, cfg, out)
        callbacks, _ = ebops_callbacks(monitor.runtime_cfg, out, monitor)
        pid = next(c for c in callbacks if isinstance(c, BetaPID))
        for cb in callbacks:
            cb.set_model(model)
            cb.on_train_begin({})
        # Actual PID increases pressure after warmup while above the budget.
        warmup = pid.warmup
        pid.on_epoch_end(0, {})
        pid.on_epoch_begin(warmup, {})
        beta_start = pid.beta
        pid.on_epoch_begin(warmup + 1, {})
        assert pid.beta > beta_start > 0
        monitor.on_epoch_end(0, {"val_macro_auc": .8})
        assert monitor.best is None and not (Path(out) / "model_best.keras").exists()
        # Make the test budget feasible, then ensure a worse feasible AUC does
        # not replace the best checkpoint. No optimizer/training run is needed.
        monitor.target = before + 1
        monitor.on_epoch_end(1, {"val_macro_auc": .8})
        monitor.on_epoch_end(2, {"val_macro_auc": .7})
        assert monitor.best["epoch"] == 1
        reloaded = keras.models.load_model(Path(out) / "model_best.keras", compile=False)
        assert width_snapshot(reloaded) == width_snapshot(model)
        assert compute_ebops(reloaded, x)["total"] == before
        np.testing.assert_allclose(model(x, training=False), reloaded(x, training=False), atol=1e-6)
        assert len((Path(out) / "activation_widths.jsonl").read_text().splitlines()) == 3
    # Every generated config builds; the no-pressure control really has zero beta.
    for path in cfgs:
        c = load_config(path)
        m, _ = qat.build_qat_model(c, seed=1)
        cst = compute_ebops(m, x)["total"]
        assert cst == before
        if "control" in path.name:
            assert c["quant"]["beta0"] == 0 and c["train"]["ebops"]["controller"] == "none"
        print(f"[check] {c['name']} params={m.count_params()} initial_ebops={cst}")
    print(f"[check] {len(variables)} width variables have finite connected gradients; "
          f"one-bit perturbation changes EBOPs {before}->{after}")
    if "--integration" in sys.argv:
        from bnhgq2 import train as trainer
        from bnhgq2 import wandb_util
        # Cluster CPU-only integration smoke, synthetic data, no W&B writes.
        rng = np.random.default_rng(10)
        sx = rng.normal(size=(400, 8, 3)).astype("float32")
        sy = np.eye(5, dtype="float32")[np.arange(400) % 5]
        trainer.load_train_data = lambda *a, **kw: (sx.copy(), sy.copy(), 1)
        wandb_util.wandb_enabled = lambda *a, **kw: False
        for feasible in (True, False):
            c = copy.deepcopy(cfg)
            eb = c["train"]["ebops"]
            eb.pop("target_ratio")
            eb["pid"].update(target_ebops=1e9 if feasible else 1., warmup=0)
            with tempfile.TemporaryDirectory() as output:
                meta = trainer.train(c, seed=1, out_dir=output, smoke=True)
                result = meta["ebops_budget"]
                assert result["budget_met"] is feasible
                expected = "model_best.keras" if feasible else "model_unconstrained.keras"
                assert result["checkpoint"] == expected
                assert (Path(output) / expected).exists()
                if not feasible:
                    assert not (Path(output) / "model_best.keras").exists()
                assert len((Path(output) / "activation_widths.jsonl").read_text().splitlines()) == 3
        print("[check] feasible and unmet-budget training integration PASS")
    print("EBOPS_TARGET_ALL_PASS")


if __name__ == "__main__":
    main()
