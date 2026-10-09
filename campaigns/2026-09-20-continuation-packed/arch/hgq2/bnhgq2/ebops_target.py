"""Opt-in EBOPs budget control and measured activation-width history.

The budget is an HGQ2 cost per inference, not a MAC count or a synthesis limit.
Only input quantizers are logged; fixed softmax tables remain fixed.
"""
from __future__ import annotations

import copy
import json
import math
import os
from pathlib import Path

import keras
import numpy as np
from keras import ops

from .ebops_calc import compute_ebops


def activation_quantizers(model):
    for layer in model.layers:
        iq = getattr(layer, "iq", None)
        if iq is None:
            continue
        qs = list(iq) if hasattr(iq, "__len__") else [iq]
        for index, q in enumerate(qs):
            qz = getattr(q, "quantizer", None)
            if qz is None or getattr(qz, "__dummy__", False):
                continue
            name = layer.name if len(qs) == 1 else f"{layer.name}__in{index}"
            yield name, qz


def width_snapshot(model):
    trainable_ids = {id(v) for v in model.trainable_variables}
    result = {}
    for name, q in activation_quantizers(model):
        if not hasattr(q, "fbits"):
            continue
        def scalar(value):
            a = np.asarray(ops.convert_to_numpy(value))
            return float(a.item()) if a.size == 1 else a.tolist()
        result[name] = {
            "bits": scalar(q.fbits), "i": scalar(q.i), "f": scalar(q.f),
            "raw_i": scalar(q._i),
            "raw_f": scalar(q._f) if hasattr(q, "_f") else None,
            "width_trainable": all(id(getattr(q, key, None)) in trainable_ids
                                   for key in ("_i", "_f")),
        }
    return result


def resolve_budget(cfg, initial_ebops):
    """Resolve a fraction once, after calibration, without mutating the input config."""
    runtime = copy.deepcopy(cfg)
    eb = runtime["train"]["ebops"]
    controller = eb.get("controller", "schedule")
    if controller != "pid":
        return runtime
    if cfg["quant"].get("act_calib") != "free":
        raise ValueError("BetaPID requires quant.act_calib='free' in this binary pilot")
    if not eb.get("enable") or eb.get("beta_schedule"):
        raise ValueError("Enable EBOPs and choose only one of BetaPID and beta_schedule")
    pid = eb.setdefault("pid", {})
    ratio = eb.get("target_ratio")
    if (ratio is None) == (pid.get("target_ebops") is None):
        raise ValueError("Specify exactly one of target_ratio or pid.target_ebops")
    if ratio is not None:
        if not math.isfinite(float(ratio)) or not 0 < float(ratio) <= 1:
            raise ValueError("target_ratio must be in (0, 1]")
        pid["target_ebops"] = float(initial_ebops) * float(ratio)
    if not math.isfinite(float(pid["target_ebops"])) or float(pid["target_ebops"]) <= 0:
        raise ValueError("target_ebops must be finite and positive")
    initial_beta = float(pid.get("init_beta", cfg["quant"].get("beta0", 0)))
    if not math.isfinite(initial_beta) or initial_beta <= 0:
        raise ValueError("BetaPID needs a positive finite init_beta")
    pid["init_beta"] = initial_beta
    if float(pid.get("i", 2e-3)) <= 0:
        raise ValueError("BetaPID integral gain must be positive")
    eb["threshold"] = float(pid["target_ebops"])
    return runtime


class BudgetMonitor(keras.callbacks.Callback):
    """Refresh costs BEFORE BetaPID/ParetoFront and save the best feasible epoch."""
    def __init__(self, model, sample, cfg, out_dir):
        super().__init__()
        self.sample = np.asarray(sample, dtype="float32")
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.initial = compute_ebops(model, self.sample)
        if self.initial["total"] <= 0:
            raise ValueError("Initial EBOPs must be positive")
        self.runtime_cfg = resolve_budget(cfg, self.initial["total"])
        eb = self.runtime_cfg["train"]["ebops"]
        self.target = eb.get("threshold") if eb.get("controller") == "pid" else None
        self.initial_widths = width_snapshot(model)
        if not any(v["width_trainable"] for v in self.initial_widths.values()):
            raise ValueError("No activation-width variables are optimizer-trainable")
        self.selection = eb.get("selection", "max_auc")
        if self.selection not in ("max_auc", "min_ebops"):
            raise ValueError("EBOPs selection must be max_auc or min_ebops")
        self.stop_on_target = bool(eb.get("stop_on_target", False))
        if self.stop_on_target and self.target is None:
            raise ValueError("stop_on_target requires a resolved budget")
        self.lowest = None
        self.best = None
        self.last = None
        self.history = self.out_dir / "activation_widths.jsonl"
        if self.history.exists():
            raise FileExistsError(f"Refusing to mix runs in {self.out_dir}")
        self.info = {"initial_ebops": self.initial["total"], "target_ebops": self.target,
                     "controller": eb.get("controller"), "pid": eb.get("pid"),
                     "selection": self.selection, "stop_on_target": self.stop_on_target,
                     "initial_widths": self.initial_widths, "convention": "hgq2_trace_minmax",
                     "code_sha256": os.environ.get("BNHGQ2_CODE_SHA256")}
        (self.out_dir / "ebops_budget.json").write_text(json.dumps(self.info, indent=2) + "\n")

    def on_epoch_end(self, epoch, logs=None):
        if logs is None:
            raise ValueError("Epoch logs are required")
        cost = compute_ebops(self.model, self.sample)
        widths = width_snapshot(self.model)
        free = {n: w for n, w in widths.items() if w["width_trainable"]}
        logs["ebops"] = cost["total"]
        logs["ebops_fraction_initial"] = cost["total"] / self.initial["total"]
        logs["activation_bits_mean"] = float(np.mean(np.concatenate([np.asarray(w["bits"]).ravel() for w in free.values()])))
        logs["activation_width_sites_changed"] = sum(
            not np.array_equal(w["bits"], self.initial_widths[n]["bits"]) for n, w in free.items())
        if self.target is not None:
            logs["target_ebops"] = self.target
            logs["budget_met"] = int(cost["total"] <= self.target)
            auc = float(logs["val_macro_auc"])
            point = {"epoch": epoch, "val_macro_auc": auc, "ebops": cost["total"]}
            if not math.isfinite(auc):
                raise RuntimeError("Nonfinite validation AUC; refusing to report a valid checkpoint")
            if self.selection == "min_ebops":
                rank = (-cost["total"], -epoch)
                old_rank = ((-self.best["ebops"], -self.best["epoch"])
                            if self.best else None)
                if self.lowest is None or cost["total"] < self.lowest["ebops"]:
                    self.model.save(self.out_dir / "model_min_ebops.keras")
                    self.lowest = point
            else:
                rank = (auc, -cost["total"], -epoch)
                old_rank = ((self.best["val_macro_auc"], -self.best["ebops"], -self.best["epoch"])
                            if self.best else None)
            if logs["budget_met"] and (old_rank is None or rank > old_rank):
                self.model.save(self.out_dir / "model_best.keras")
                self.best = point
            if logs["budget_met"] and self.stop_on_target:
                self.model.stop_training = True
                logs["stopped_on_ebops_target"] = 1
                print("[budget] measured target reached; stopping compression", flush=True)
        for name, width in widths.items():
            logs[f"activation_bits/{name}"] = float(np.mean(width["bits"]))
        self.last = {"epoch": epoch, "ebops": cost["total"], "per_layer": cost["per_layer"],
                     "widths": widths, "best_feasible": self.best, "lowest_ebops": self.lowest}
        with self.history.open("a") as f:
            f.write(json.dumps(self.last, allow_nan=False) + "\n")
        print(f"[budget] epoch={epoch} ebops={cost['total']} target={self.target} "
              f"width_sites_changed={logs['activation_width_sites_changed']}", flush=True)


class LogBudgetToWandb(keras.callbacks.Callback):
    """Run after all metric producers; MacroAUC defers its logging for these runs."""
    def on_epoch_end(self, epoch, logs=None):
        import wandb
        wandb.log({**(logs or {}), "epoch": epoch})
