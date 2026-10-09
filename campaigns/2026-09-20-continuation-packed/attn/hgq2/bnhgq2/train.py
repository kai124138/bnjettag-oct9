'Native HGQ2 quantization-aware training with macro one-vs-rest AUC checkpoint selection.\n\nWrites model_best.keras, input_std.json, and train_meta.json. Dataset and output\nlocations can be overridden with BNHGQ2_TRAIN_DATA and BNHGQ2_OUT_ROOT.'
from __future__ import annotations

import glob
import json
import os
import time

import numpy as np


# --------------------------------------------------------------------------- #
# data (top-N by pT — byte-identical logic to data.load_eval_set)       #
# --------------------------------------------------------------------------- #
def load_train_data(data_dir: str, n_part: int, max_files: int | None = None,
                    features=None):
    import h5py
    from .data import CLASS_LABELS, feature_indices

    files = sorted(glob.glob(os.path.join(data_dir, "*.h5")))
    if not files:
        raise FileNotFoundError(f"no .h5 files in {data_dir}")
    if max_files:
        files = files[:max_files]

    def _names(ds):
        return [n.decode() if isinstance(n, bytes) else str(n) for n in ds]

    Xs, Ys = [], []
    for fp in files:
        with h5py.File(fp, "r") as hf:
            const = hf["jetConstituentList"][:]
            jets = hf["jets"][:]
            jnames = _names(hf["jetFeatureNames"][:])
            pnames = _names(hf["particleFeatureNames"][:])
        miss = [l for l in CLASS_LABELS if l not in jnames]
        if miss:
            raise KeyError(f"{fp}: labels {miss} not in jetFeatureNames")
        lab_idx = [jnames.index(l) for l in CLASS_LABELS]
        pt_col = next((i for i, n in enumerate(pnames) if n.endswith("_pt")), None)
        if pt_col is not None:
            order = np.argsort(-const[:, :, pt_col], axis=1, kind="stable")
            const = np.take_along_axis(const, order[:, :, None], axis=1)
        # feature subset AFTER the pT sort/truncation: ordering is identical
        # regardless of the subset (pre-conference L1-realistic inputs, e.g.
        # ["pt","etarel","phirel"]); absent => all 16, byte-identical behaviour.
        const = const[:, :n_part, :]
        if features:
            const = const[:, :, feature_indices(pnames, features)]
        Xs.append(const.astype("float32"))
        Ys.append(jets[:, lab_idx].astype("float32"))
    return np.concatenate(Xs), np.concatenate(Ys), len(files)


# --------------------------------------------------------------------------- #
# metric + callbacks                                                           #
# --------------------------------------------------------------------------- #
def macro_ovr_auc(y_onehot, scores):
    from sklearn.metrics import roc_auc_score
    per = []
    for c in range(y_onehot.shape[1]):
        yc = y_onehot[:, c]
        per.append(roc_auc_score(yc, scores[:, c]) if 0 < yc.sum() < len(yc) else float("nan"))
    return float(np.nanmean(per)), [float(p) for p in per]


def _softmax(z):
    z = z.astype(np.float64)
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def _recalib_callback(qat, model, taps, X, act_bits, epochs):
    """Callback: re-run MSE activation calibration on the drifted activations at the start
    of each epoch in `epochs`, then re-freeze (act_calib='recalib', mechanism 2)."""
    import keras

    class Recalibrate(keras.callbacks.Callback):
        def on_epoch_begin(self, epoch, logs=None):
            if epoch in epochs:
                si = qat.calibrate_activations(self.model, taps, X, act_bits)
                if si:
                    v = list(si.values())
                    print(f"  [recalib epoch {epoch}] {len(si)} act sites -> i in "
                          f"[{min(v)},{max(v)}] (re-froze on drifted activations)", flush=True)
    return Recalibrate()


def ebops_callbacks(cfg: dict, out_dir: str, monitor=None):
    """reference experiment EBOPs-pressure callbacks, config-gated on `train.ebops`.

    ABSENT `train.ebops` (or `enable: false`) => returns [] => an reference experiment/reference experiment/reference experiment config
    produces byte-identical callbacks to before. Present, it returns, IN ORDER:

      BetaScheduler(PieceWiseSchedule(...))  sets each layer's `_beta` at epoch begin and
                                             writes logs['beta'] at epoch end
      FreeEBOPs                              writes logs['ebops'] (HGQ2's own accounting —
                                             the ONE EBOPs number reference experiment reports)
      ParetoFront                            saves one checkpoint per non-dominated
                                             (val_macro_auc up, ebops down) epoch, admitted
                                             only when ebops <= `threshold`

    Callback ORDER MATTERS and is the reason this returns a list to be APPENDED after
    make_callbacks(): MacroAUC (logs['val_macro_auc']) and FreeEBOPs (logs['ebops']) must
    both have run before ParetoFront reads them.

    Config block (all keys optional except `enable`):
      "ebops": {"enable": true,
                "beta_schedule": [[0, 0.0, "constant"], [300, 1e-9, "log"],
                                  [600, 1e-3, "constant"]],
                "threshold": 5e5,
                "front_dir": "front",
                "metrics": ["val_macro_auc", "ebops"], "sides": [1, -1]}
    A schedule of `null`/absent means "no BetaScheduler" (beta stays at quant.beta0) — that
    is how the beta = 0 control arms keep the identical front machinery without the pressure.
    """
    eb = (cfg.get("train", {}) or {}).get("ebops") or {}
    if not eb.get("enable", False):
        return [], None
    from hgq.utils.sugar import BetaScheduler, FreeEBOPs, ParetoFront, PieceWiseSchedule

    cbs = [monitor] if monitor is not None else []
    if eb.get("controller") == "pid":
        from hgq.utils.sugar import BetaPID
        if monitor is None:
            raise ValueError("PID configuration must be resolved by BudgetMonitor first")
        cbs.append(BetaPID(**eb["pid"]))
    sched = eb.get("beta_schedule")
    if sched:
        pts = [(int(e), float(b), str(k)) for e, b, k in sched]
        cbs.append(BetaScheduler(PieceWiseSchedule(pts)))
    cbs.append(FreeEBOPs())
    front_dir = os.path.join(out_dir, str(eb.get("front_dir", "front")))
    thr = eb.get("threshold")
    enable_if = None
    if thr is not None:
        thr = float(thr)
        enable_if = lambda logs: float(logs.get("ebops", float("inf"))) <= thr  # noqa: E731
    cbs.append(ParetoFront(
        path=front_dir,
        metrics=list(eb.get("metrics", ["val_macro_auc", "ebops"])),
        sides=list(eb.get("sides", [1, -1])),
        fname_format="epoch={epoch}_auc={val_macro_auc:.5f}_ebops={ebops}.keras",
        enable_if=enable_if))
    print(f"[train] EBOPs pressure ON: beta_schedule={sched} threshold={thr} "
          f"front -> {front_dir}", flush=True)
    return cbs, front_dir


def make_callbacks(Xval, Yval, best_path, es_patience, lr, warmup_epochs,
                   decay_epochs, decay_power, use_wandb, state,
                   val_batch=1024, lr_schedule="poly", lr_cycle_epochs=0,
                   lr_min_frac=0.0):
    import keras

    class MacroAUC(keras.callbacks.Callback):
        """Compute val macro-OvR AUC, write logs['val_macro_auc'], save best checkpoint."""

        def on_epoch_end(self, epoch, logs=None):
            logs = logs if logs is not None else {}
            scores = _softmax(np.asarray(self.model.predict(Xval,
                                                            batch_size=int(val_batch),
                                                            verbose=0)))
            auc, per = macro_ovr_auc(Yval, scores)
            logs["val_macro_auc"] = auc
            print(f"  [epoch {epoch}] val_macro_auc={auc:.5f} per_class={[round(p,4) for p in per]}",
                  flush=True)
            if auc > state["best_auc"]:
                state["best_auc"], state["best_epoch"] = auc, epoch
                self.model.save(best_path)
                print(f"  [epoch {epoch}] new best -> saved {best_path}", flush=True)
            if use_wandb:
                import wandb
                wandb.log({**logs, "epoch": epoch, "val_macro_auc": auc,
                           **{f"val_auc_{i}": p for i, p in enumerate(per)}})

    cbs = [MacroAUC()]
    # es_patience <= 0 DISABLES early stopping (reference experiment: under EBOPs pressure the val AUC
    # is *expected* to decline as bitwidths anneal, so stopping on it would truncate the
    # front). Any positive value reproduces the previous behavior exactly.
    if es_patience and int(es_patience) > 0:
        cbs.append(keras.callbacks.EarlyStopping(monitor="val_macro_auc", mode="max",
                                                 patience=int(es_patience), verbose=1,
                                                 restore_best_weights=True))

    if str(lr_schedule).lower() == "cosine_restarts":
        # jsc150's shape: linear warmup, then cosine cycles of `lr_cycle_epochs`. Each
        # restart re-escapes the discrete perturbation a bitwidth drop inflicts.
        cyc = max(1, int(lr_cycle_epochs))

        def sched(epoch, _lr):
            if warmup_epochs > 0 and epoch < warmup_epochs:
                return lr * float(epoch + 1) / float(warmup_epochs)
            t = (epoch - warmup_epochs) % cyc
            cos = 0.5 * (1.0 + np.cos(np.pi * float(t) / float(cyc)))
            return float(lr * (lr_min_frac + (1.0 - lr_min_frac) * cos))
        cbs.append(keras.callbacks.LearningRateScheduler(sched, verbose=0))
    elif warmup_epochs > 0 or decay_epochs > 0:
        def sched(epoch, _lr):
            if warmup_epochs > 0 and epoch < warmup_epochs:
                return lr * float(epoch + 1) / float(warmup_epochs)
            if decay_epochs > 0:
                prog = min(1.0, float(epoch - warmup_epochs) / float(decay_epochs))
                return lr * (1.0 - prog) ** decay_power
            return lr
        cbs.append(keras.callbacks.LearningRateScheduler(sched, verbose=0))
    return cbs


# --------------------------------------------------------------------------- #
# reference experiment Pareto front bookkeeping                                             #
# --------------------------------------------------------------------------- #
_FRONT_RE = r"epoch=(\d+)_auc=([0-9.]+)_ebops=(\d+)\.keras$"


def summarize_front(front_dir: str) -> list:
    """[{epoch, val_macro_auc, ebops, file}] parsed from the ParetoFront filenames.
    Only files ParetoFront actually kept are on disk, so this IS the front."""
    import re
    if not front_dir or not os.path.isdir(front_dir):
        return []
    pts = []
    for fn in sorted(os.listdir(front_dir)):
        m = re.search(_FRONT_RE, fn)
        if m:
            pts.append({"epoch": int(m.group(1)), "val_macro_auc": float(m.group(2)),
                        "ebops": int(m.group(3)), "file": fn})
    return sorted(pts, key=lambda p: p["ebops"])


def select_front_point(front: list):
    """The PRE-REGISTERED reference experiment selection rule (reference experiment.md §5): among the admitted
    points (ParetoFront's enable_if already applied the EBOPs threshold), the highest
    validation macro-OvR AUC; ties -> lower EBOPs -> earlier epoch. Returns None when
    the front is empty ("no admission" — a result, not a failure)."""
    if not front:
        return None
    return sorted(front, key=lambda p: (-p["val_macro_auc"], p["ebops"], p["epoch"]))[0]


# --------------------------------------------------------------------------- #
# the stage                                                                    #
# --------------------------------------------------------------------------- #
def train(cfg: dict, seed: int, out_dir: str, smoke: bool = False,
          cfg_hash: str = "") -> dict:
    import keras
    import tensorflow as tf
    from .compat import apply_keras_compat
    from .subln import register_subln
    from . import qat

    apply_keras_compat()
    register_subln()
    keras.utils.set_random_seed(int(seed))

    tr = cfg["train"]
    A = cfg["arch"]
    n_part = A["n_part"]
    act_bits = int(cfg["quant"]["act_bits"])
    os.makedirs(out_dir, exist_ok=True)

    epochs = 3 if smoke else int(tr["epochs"])
    warmup = (0 if smoke else int(tr["warmup_epochs"]))
    decay = (2 if smoke else int(tr["decay_epochs"]))
    max_files = 2 if smoke else tr.get("max_files")

    # ---- data (BNHGQ2_TRAIN_DATA overrides the config path for local/portable runs) ----
    # arch.features (pre-conference): explicit constituent-feature subset, must match n_feat.
    features = A.get("features")
    if features:
        if len(features) != int(A["n_feat"]):
            raise SystemExit(f"arch.features has {len(features)} entries but "
                             f"n_feat={A['n_feat']}")
        if A.get("pair_bias"):
            raise SystemExit("arch.pair_bias needs the px/py/pz/e/pt/eta/phi columns — "
                             "incompatible with a feature subset")
        print(f"[train] L1-realistic feature subset: {features}", flush=True)
    data_dir = os.environ.get("BNHGQ2_TRAIN_DATA", tr["data"])
    X, Y, nfiles = load_train_data(data_dir, n_part, max_files=max_files,
                                   features=features)
    rng = np.random.default_rng(int(seed))
    idx = rng.permutation(len(X))
    X, Y = X[idx], Y[idx]
    vsplit = float(tr.get("validation_split", 0.20))
    nval = int(len(X) * vsplit)
    Xval, Yval = X[:nval], Y[:nval]
    Xtr, Ytr = X[nval:], Y[nval:]
    print(f"[train] data: {nfiles} files, {len(X)} jets ({len(Xtr)} train / {len(Xval)} val), "
          f"class counts {Y.sum(0).astype(int).tolist()}", flush=True)

    # reference experiment knob (guarded; absent key => byte-identical behavior): offline per-feature
    # standardization from the TRAIN split only. Stats travel with the checkpoint as
    # input_std.json — eval/convert must apply the SAME stats via their --input-std flag.
    input_std = bool(cfg["arch"].get("input_std", False))
    std_path = None
    input_mu = input_sigma = None          # passed to the builder for the pair_bias branch
    if input_std:
        from .data import input_std_stats, apply_input_std
        mu, sigma = input_std_stats(Xtr)
        input_mu, input_sigma = mu, sigma
        Xtr = apply_input_std(Xtr, mu, sigma)
        Xval = apply_input_std(Xval, mu, sigma)
        std_path = os.path.join(out_dir, "input_std.json")
        with open(std_path, "w") as f:
            json.dump({"mu": mu.tolist(), "sigma": sigma.tolist(),
                       "computed_from": "train split only",
                       "contract": "hardware receives standardized inputs (offline preprocessing)"},
                      f, indent=1)
        print(f"[train] input_std ON: per-feature z-score from train split "
              f"(|mu|max={float(np.abs(mu).max()):.4g}, sigma_max={float(sigma.max()):.4g}) "
              f"-> input_std.json", flush=True)

    # ---- model + activation calibration ----
    model, taps = qat.build_qat_model(cfg, seed=seed,
                                      input_mu=input_mu, input_sigma=input_sigma)
    site_i = qat.calibrate_activations(model, taps, Xtr, act_bits)
    act_calib = str(cfg["quant"].get("act_calib", "frozen")).lower()
    grid_before = qat.act_grid_params(model)
    budget_monitor = None
    runtime_cfg = cfg
    eb_cfg = tr.get("ebops") or {}
    if eb_cfg.get("enable") and eb_cfg.get("monitor_widths"):
        from .ebops_target import BudgetMonitor
        budget_monitor = BudgetMonitor(model, Xtr[:256], cfg, out_dir)
        runtime_cfg = budget_monitor.runtime_cfg
        print(f"[budget] initial={budget_monitor.initial['total']} "
              f"target={budget_monitor.target}", flush=True)
    nparams = int(model.count_params())
    ntrain = int(sum(np.prod(v.shape) for v in model.trainable_variables))
    print(f"[train] {cfg['name']} params={nparams:,} trainable={ntrain:,} "
          f"act_sites={len(site_i)} act_calib={act_calib}", flush=True)
    if cfg["quant"]["weight"] == "binary_absmean":
        effs = qat.effective_weight_values(model)
        ok = all(len(v) == 2 and not (v == 0).any() for v in effs.values())
        assert ok, "BINARY GATE FAILED at build: effective weights not exactly two-valued"
        print(f"[train] binary gate OK ({len(effs)} bit-layers exactly +/-beta)", flush=True)

    # ---- optimizer (clipvalue: overflow-safe unit-scale clip, see module docstring) ----
    lr = float(tr["lr"])
    clip_mode = tr.get("clip_mode", "value")
    opt_kw = dict(learning_rate=lr, beta_1=0.9, beta_2=float(tr.get("beta2", 0.98)),
                  weight_decay=float(tr.get("weight_decay", 0.01)))
    if clip_mode == "norm":
        opt_kw["global_clipnorm"] = float(tr.get("clipnorm", 1.0))
    else:
        opt_kw["clipvalue"] = float(tr.get("clipvalue", 1.0))
    optimizer = keras.optimizers.Adam(**opt_kw)
    model.compile(loss=keras.losses.CategoricalCrossentropy(from_logits=True),
                  optimizer=optimizer, metrics=["categorical_accuracy"],
                  **({"jit_compile": tr["jit_compile"]} if "jit_compile" in tr else {}))

    # ---- wandb (layout: wandb_util — entity/group/tags from env, job_type=train) ----
    from . import wandb_util as wbu
    use_wandb = wbu.wandb_enabled(tr.get("wandb_project"))
    if use_wandb:
        import wandb
        wandb.init(**wbu.init_kwargs(
            name=os.environ.get("WANDB_RUN_NAME") or f"final-{_variant(cfg)}-s{seed}",
            job_type="train", cfg_project=tr.get("wandb_project"),
            tags=[_variant(cfg), f"s{seed}"],
            config={"variant": _variant(cfg), "seed": int(seed),
                    "act_bits": act_bits, "weight": cfg["quant"]["weight"],
                    "config_hash": cfg_hash, "params": nparams,
                    "lr": lr, "clip_mode": clip_mode, "smoke": smoke,
                    **{f"arch_{k}": v for k, v in A.items()}}))
        try:  # dataset lineage (declare-only; the data itself streams from Zenodo in-pod)
            wandb.run.use_artifact("hls4ml-lhc-jet-5class-train:latest")
        except Exception:
            pass  # artifact not registered yet / offline — lineage is best-effort

    if use_wandb and budget_monitor is not None:
        wandb.config.update({"ebops_budget": budget_monitor.info, "quant": cfg["quant"],
                             "train_ebops": runtime_cfg["train"]["ebops"],
                             "jit_compile": model.jit_compile,
                             "warmup_epochs": warmup, "decay_epochs": decay})

    # ---- train ----
    constrained = budget_monitor is not None and budget_monitor.target is not None
    best_path = os.path.join(out_dir, "model_unconstrained.keras" if constrained
                            else "model_best.keras")
    state = {"best_auc": -1.0, "best_epoch": -1}
    cbs = make_callbacks(Xval, Yval, best_path, int(tr.get("es_patience", 10)),
                         lr, warmup, decay, float(tr.get("decay_power", 1.0)),
                         use_wandb and budget_monitor is None, state,
                         val_batch=int(tr.get("val_batch", 1024)),
                         lr_schedule=str(tr.get("lr_schedule", "poly")),
                         lr_cycle_epochs=int(tr.get("lr_cycle_epochs", 0)),
                         lr_min_frac=float(tr.get("lr_min_frac", 0.0)))
    # reference experiment EBOPs pressure (appended LAST so FreeEBOPs/MacroAUC precede ParetoFront).
    eb_cbs, front_dir = ebops_callbacks(runtime_cfg, out_dir, monitor=budget_monitor)
    cbs.extend(eb_cbs)
    # act_calib="recalib": re-run MSE calibration on the DRIFTED activations at the given
    # epoch boundaries, then re-freeze (cheap; no quantizer surgery). Distributions have
    # stabilized by then, so the frozen grid re-aligns. (Mechanism 2 / fallback.)
    recal_epochs = [int(e) for e in cfg["quant"].get("act_recalib_epochs", [])]
    if act_calib == "recalib" and recal_epochs and not smoke:
        cbs.append(_recalib_callback(qat, model, taps, Xtr, act_bits, recal_epochs))
    elif act_calib == "recalib" and recal_epochs:  # smoke: recalibrate on epoch 1 to exercise it
        cbs.append(_recalib_callback(qat, model, taps, Xtr, act_bits, [1]))
    if use_wandb and budget_monitor is not None:
        from .ebops_target import LogBudgetToWandb
        cbs.append(LogBudgetToWandb())
    t0 = time.time()
    model.fit(Xtr, Ytr, epochs=epochs, batch_size=int(tr.get("batch", 256)),
              verbose=2, callbacks=cbs)
    dt = time.time() - t0
    grid_after = qat.act_grid_params(model)
    if act_calib == "trainable":
        moved = sum(1 for k in grid_before if grid_before.get(k) != grid_after.get(k))
        print(f"[train] trainable-scale grids moved at {moved}/{len(grid_before)} sites "
              f"during training (drift tracking)", flush=True)

    cost_first = budget_monitor is not None and budget_monitor.selection == "min_ebops"
    def selected_front(points):
        if cost_first:
            return min(points, key=lambda p: (p["ebops"], p["epoch"])) if points else None
        return select_front_point(points)
    selection_rule = ("lowest ebops; ties -> earlier epoch; AUC diagnostic only" if cost_first
                      else "highest val_macro_auc among admitted points; ties -> lower ebops -> earlier epoch")

    # ---- reference experiment Pareto front summary (the DELIVERABLE, even when empty) ----
    front = summarize_front(front_dir) if front_dir else []
    if front_dir:
        with open(os.path.join(out_dir, "front.json"), "w") as f:
            json.dump({"front_dir": front_dir, "n_points": len(front),
                       "selection_rule": selection_rule,
                       "points": front}, f, indent=2)
        sel = selected_front(front)
        print(f"[train] pareto front: {len(front)} admitted point(s); "
              f"selected={sel}", flush=True)

    if state["best_epoch"] < 0:  # no epoch improved (e.g. degenerate smoke) -> save final
        model.save(best_path)
        scores = _softmax(np.asarray(model.predict(Xval, batch_size=1024, verbose=0)))
        state["best_auc"], _ = macro_ovr_auc(Yval, scores)
        state["best_epoch"] = epochs - 1

    unconstrained_state = dict(state)
    budget_result = None
    if budget_monitor is not None:
        selected = budget_monitor.best
        if constrained and selected is not None:
            best_path = os.path.join(out_dir, "model_best.keras")
            state.update(best_auc=selected["val_macro_auc"], best_epoch=selected["epoch"])
        elif constrained and cost_first and budget_monitor.lowest is not None:
            selected = budget_monitor.lowest
            best_path = os.path.join(out_dir, "model_min_ebops.keras")
            state.update(best_auc=selected["val_macro_auc"], best_epoch=selected["epoch"])
        # Re-load the actual delivered checkpoint, not the last in-memory epoch.
        from .ebops_calc import compute_ebops
        from .ebops_target import width_snapshot
        delivered = keras.models.load_model(best_path, compile=False)
        measured = compute_ebops(delivered, budget_monitor.sample)
        if constrained and budget_monitor.best is not None and measured["total"] > budget_monitor.target:
            raise RuntimeError("Reloaded selected checkpoint exceeds the EBOPs budget")
        budget_result = {**budget_monitor.info, "budget_met":
                         (measured["total"] <= budget_monitor.target if constrained else None),
                         "selected": selected, "best_feasible": budget_monitor.best,
                         "checkpoint": os.path.basename(best_path),
                         "checkpoint_ebops": measured["total"],
                         "checkpoint_widths": width_snapshot(delivered),
                         "unconstrained_best": unconstrained_state}
        (budget_monitor.out_dir / "ebops_budget.json").write_text(
            json.dumps(budget_result, indent=2) + "\n")
        if use_wandb:
            wandb.summary.update({"budget_met": budget_result["budget_met"],
                                  "checkpoint_ebops": measured["total"],
                                  "target_ebops": budget_monitor.target,
                                  "checkpoint": os.path.basename(best_path)})
        del delivered

    meta = {
        "variant": _variant(cfg), "seed": int(seed), "config": cfg["name"],
        "config_hash": cfg_hash, "params": nparams, "trainable_params": ntrain,
        "best_epoch": state["best_epoch"], "best_val_macro_auc": state["best_auc"],
        "act_bits": act_bits, "weight": cfg["quant"]["weight"],
        "lr": lr, "clip_mode": clip_mode, "epochs_run": len(model.history.epoch),
        "epochs_requested": epochs, "selection_rule": selection_rule,
        "jit_compile": model.jit_compile, "smoke": smoke,
        "n_train": int(len(Xtr)), "n_val": int(len(Xval)), "n_files": nfiles,
        "features": features, "train_seconds": round(dt, 1), "act_calib_i": site_i,
        "act_calib": act_calib, "act_recalib_epochs": recal_epochs,
        "act_grid_before": grid_before, "act_grid_after": grid_after,
        **({"ebops_budget": budget_result} if budget_result is not None else {}),
        "front": front, "front_selected": selected_front(front),
        "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t0)),
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
    }
    meta_path = os.path.join(out_dir, "train_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[train] DONE best_epoch={state['best_epoch']} "
          f"best_val_macro_auc={state['best_auc']:.5f} in {dt:.0f}s", flush=True)
    print(f"[train] wrote {best_path} + {meta_path}", flush=True)

    if use_wandb:
        import wandb
        # Legacy run-file mirror (best-effort): pre-2026-08 consumers (evaluate_roc's
        # run-file fallback, evaluation, distill's teacher fetch) read <leaf>/model_best.keras
        # off the run. The DURABILITY contract moved to the versioned artifact below.
        try:
            base = os.path.dirname(os.path.abspath(out_dir))
            wandb.save(best_path, base_path=base, policy="now")
            wandb.save(meta_path, base_path=base, policy="now")
            if std_path:
                wandb.save(std_path, base_path=base, policy="now")
            if front_dir:
                wandb.save(os.path.join(out_dir, "front.json"), base_path=base,
                           policy="now")
                for p in front:
                    wandb.save(os.path.join(front_dir, p["file"]), base_path=base,
                               policy="now")
            wandb.summary["best_val_macro_auc"] = state["best_auc"]
            wandb.summary["best_epoch"] = state["best_epoch"]
        except Exception as e:
            print(f"[train] wandb.save warn: {e}", flush=True)
        # Durability gate v2 (2026-08-01, replaces the 5-retry size-compare loop of
        # 2026-07-15): one versioned `model` artifact holds everything the ROC/convert
        # pipeline needs; log_files_artifact blocks on the server commit (checksummed)
        # and raises if any file is missing from the manifest. The pod is emptyDir-only,
        # so failure to commit is FATAL for a real run.
        leaf = os.path.basename(os.path.abspath(out_dir))
        offline = os.environ.get("WANDB_MODE", "").lower().startswith(("off", "dis"))
        try:
            from . import wandb_util as wbu
            files = [best_path, meta_path] + ([std_path] if std_path else [])
            if budget_monitor is not None:
                files += [str(budget_monitor.history), str(budget_monitor.out_dir / "ebops_budget.json")]
                unconstrained_path = os.path.join(out_dir, "model_unconstrained.keras")
                if constrained and unconstrained_path != best_path:
                    files.append(unconstrained_path)
            if front_dir and front:
                files += [os.path.join(out_dir, "front.json"), front_dir]
            wbu.log_files_artifact(
                wandb.run, name=f"model-{leaf}", type="model", files=files,
                metadata={"variant": _variant(cfg), "seed": int(seed),
                          "config_hash": cfg_hash,
                          "best_val_macro_auc": state["best_auc"],
                          "best_epoch": state["best_epoch"],
                          "front_selected": selected_front(front),
                          **({"ebops_budget": budget_result} if budget_result is not None else {})})
        except Exception as e:
            if not smoke and not offline:
                wandb.finish()
                raise SystemExit(f"[train] FATAL: model artifact for {leaf} not "
                                 f"durable on W&B: {e}")
            print(f"[train] artifact warn (smoke/offline, non-fatal): {e}", flush=True)
        wandb.finish()
    return meta


def _variant(cfg: dict) -> str:
    w = cfg["quant"]["weight"]
    if w == "none":
        return "fp32"
    if w == "int8_absmax":
        return "w8a8"
    if w == "kbi_learnable":               # reference experiment A2 control (multi-bit, learnable)
        return f"wqa{cfg['quant']['act_bits']}"
    return f"w1a{cfg['quant']['act_bits']}"
