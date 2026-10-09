#!/usr/bin/env python3
"""Round-12 knowledge-distillation trainer: the d32 flagship as a student of a
round-11 d128 teacher.

`python distill_r12.py --config configs/r12-distill-d32-w1a8.json --seed <n>
 --out-dir <dir> [--smoke]`

WHY (W1.5, COMPILER.md campaign): the fit levers (fold, FR) spend accuracy nowhere,
but the campaign has an AUC floor of 0.8835 and the flagship sits at 0.8902
(ROC-test, 3 seeds).  KD banks headroom the levers can later spend.  PROMOTE if the
student reaches ROC-test macro-OvR AUC >= 0.8952; KILL if <= 0.8922 after the LR
sweep (pre-registered).

DESIGN — everything about the student is the round-8 flagship recipe verbatim:
  * The student model is built by `bnhgq2.qat.build_qat_model` from the config's
    arch+quant blocks, which are byte-identical to `r8-small-w1a8-stdnn.json`
    (asserted by preflight_r12.sh), so `model_best.keras` drops into the existing
    convert / ROC pipeline unchanged.
  * Data loading, shuffle/split, input standardization, activation calibration,
    the binary {-1,+1} gate, optimizer (Adam beta2=0.98, clipvalue), warmup+poly
    LR schedule, val-macro-AUC checkpointing and early stopping are all IMPORTED
    from `bnhgq2` (train.py / qat.py / data.py) — called, never copied.
Only the LOSS differs: standard Hinton KD,
    L = alpha * CE(labels, student_logits)
      + (1 - alpha) * T^2 * KL( softmax(teacher/T) || softmax(student/T) ),
with alpha and T from the config's "distill" block (defaults 0.5 / 3.0).

TEACHER — one fixed, pre-registered checkpoint for every student seed
(cfg["distill"]["teacher_run"]).  Pods are PVC-free, so the teacher is fetched
from W&B by run name (project kayamaguchi-uc-san-diego/bnjettag-final) using the
pod's WANDB_API_KEY; locally an existing copy under models/r11/ (eval_r11.py
layout) or $BNHGQ2_TEACHER_DIR is used without any network.  The teacher is
frozen, so its logits are precomputed ONCE over the student's train split
(offline KD) — no teacher forward in the training loop.  Teacher and student
each standardize the RAW constituents with their OWN input_std stats (teacher:
its shipped input_std.json; student: stats from its own train split, saved
beside the checkpoint per the round-8 contract), so both operate in the regime
they were / are trained in.

ARTIFACT CONTRACT (identical to bnhgq2.train): model_best.keras (best epoch by
val macro-OvR AUC; re-saved UNCOMPILED after training so the existing pipeline
can `keras.models.load_model` it without this module), input_std.json,
train_meta.json; all uploaded to W&B (project from train.wandb_project) with the
same durability gate as train.py — the run is the checkpoint's only durable home.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# KD defaults (used when the config's "distill" block omits them)
DEFAULT_ALPHA = 0.5
DEFAULT_TEMPERATURE = 3.0
TEACHER_PROJECT_DEFAULT = "kayamaguchi-uc-san-diego/bnjettag-final"


# --------------------------------------------------------------------------- #
# KD loss                                                                     #
# --------------------------------------------------------------------------- #
def make_kd_loss_class():
    """Return the KDLoss class (deferred so import of this module is keras-free).

    y_true is the CONCATENATION [onehot_labels (C) | teacher_logits (C)] — the
    only way to route the per-sample teacher logits through model.fit without
    touching the imported training machinery.  y_pred is the student's logits.
    Registered as serializable so the per-epoch best-checkpoint save (which
    stores the compile config) works; the final artifact is re-saved uncompiled
    so the downstream pipeline never needs this class.
    """
    import keras
    from keras import ops

    @keras.saving.register_keras_serializable(package="bnhgq2_distill")
    class KDLoss(keras.losses.Loss):
        def __init__(self, n_classes: int, alpha: float = DEFAULT_ALPHA,
                     temperature: float = DEFAULT_TEMPERATURE, name="kd_loss", **kw):
            super().__init__(name=name, **kw)
            self.n_classes = int(n_classes)
            self.alpha = float(alpha)
            self.temperature = float(temperature)

        def call(self, y_true, y_pred):
            C = self.n_classes
            y = y_true[:, :C]                       # one-hot labels
            t = y_true[:, C:]                       # teacher logits
            ce = keras.losses.categorical_crossentropy(y, y_pred, from_logits=True)
            T = self.temperature
            pt = ops.softmax(t / T, axis=-1)
            log_pt = ops.log_softmax(t / T, axis=-1)
            log_ps = ops.log_softmax(y_pred / T, axis=-1)
            kl = ops.sum(pt * (log_pt - log_ps), axis=-1)
            return self.alpha * ce + (1.0 - self.alpha) * (T * T) * kl

        def get_config(self):
            c = super().get_config()
            c.update(n_classes=self.n_classes, alpha=self.alpha,
                     temperature=self.temperature)
            return c

    return KDLoss


# --------------------------------------------------------------------------- #
# teacher fetch (PVC-free: local copy first, else W&B by run name)            #
# --------------------------------------------------------------------------- #
def fetch_teacher(run_name: str, project: str) -> str:
    """Return a directory containing the teacher's model_best.keras +
    input_std.json.  Search order:
      1. $BNHGQ2_TEACHER_DIR (pod: the download target; local: an override)
      2. <repo>/bnjettag/models/r11/<run>/<run>/ (the eval_r11.py local layout)
      3. download from W&B (needs WANDB_API_KEY; duplicate runs ranked exactly
         as eval_r11.fetch: finished + has best_val_macro_auc + newest first).
    """
    def has_both(d):
        return (os.path.isfile(os.path.join(d, "model_best.keras"))
                and os.path.isfile(os.path.join(d, "input_std.json")))

    env_dir = os.environ.get("BNHGQ2_TEACHER_DIR")
    cands = []
    if env_dir:
        cands += [os.path.join(env_dir, run_name), env_dir]
    repo_models = os.path.abspath(os.path.join(HERE, "..", "..", "models", "r11"))
    cands.append(os.path.join(repo_models, run_name, run_name))
    for d in cands:
        if has_both(d):
            print(f"[teacher] using local copy {d}", flush=True)
            return d

    if not os.environ.get("WANDB_API_KEY"):
        raise SystemExit(f"[teacher] {run_name}: no local copy and WANDB_API_KEY "
                         "not set — cannot fetch (never echo the key)")
    import wandb

    dest = os.path.join(env_dir or "/work/teacher", run_name)
    os.makedirs(dest, exist_ok=True)
    api = wandb.Api(timeout=180)
    hits = [r for r in api.runs(project) if r.name == run_name]
    if not hits:
        raise SystemExit(f"[teacher] {run_name}: no W&B run in {project}")
    want = (f"{run_name}/model_best.keras", f"{run_name}/input_std.json")

    def rank(r):
        return (r.state == "finished",
                r.summary.get("best_val_macro_auc") is not None, str(r.created_at))

    for r in sorted(hits, key=rank, reverse=True):
        got = set()
        for f in r.files():
            if f.name in want:
                f.download(root=dest, replace=True)
                got.add(f.name)
        if len(got) == 2:
            d = os.path.join(dest, run_name)
            print(f"[teacher] fetched {run_name} from W&B "
                  f"({len(hits)} run(s); took state={r.state} {r.id}) -> {d}", flush=True)
            return d
    raise SystemExit(f"[teacher] {run_name}: {len(hits)} W&B run(s), "
                     f"none carrying both {want}")


def load_teacher(teacher_dir: str):
    """Load the frozen teacher + its input_std stats. Import bnhgq2.qat first so
    every custom layer (BitQ*, AddPositional, ...) is registered."""
    import keras
    from bnhgq2.compat import apply_keras_compat
    from bnhgq2.subln import register_subln
    apply_keras_compat()
    register_subln()
    import bnhgq2.qat  # noqa: F401  (registers custom layers for deserialization)

    model = keras.models.load_model(
        os.path.join(teacher_dir, "model_best.keras"), compile=False)
    model.trainable = False
    with open(os.path.join(teacher_dir, "input_std.json")) as f:
        std = json.load(f)
    mu = np.asarray(std["mu"], dtype="float32")
    sigma = np.asarray(std["sigma"], dtype="float32")
    return model, mu, sigma


def teacher_logits(model, X_raw: np.ndarray, mu, sigma, batch: int = 4096) -> np.ndarray:
    """Standardize RAW constituents with the TEACHER's stats and predict logits."""
    from bnhgq2.data import apply_input_std
    outs = []
    for i in range(0, len(X_raw), batch):
        xb = apply_input_std(X_raw[i:i + batch], mu, sigma)
        outs.append(np.asarray(model.predict(xb, batch_size=batch, verbose=0)))
    return np.concatenate(outs).astype("float32")


# --------------------------------------------------------------------------- #
# the stage                                                                   #
# --------------------------------------------------------------------------- #
def distill(cfg: dict, seed: int, out_dir: str, smoke: bool = False,
            cfg_hash_val: str = "") -> dict:
    import keras
    from bnhgq2.compat import apply_keras_compat
    from bnhgq2.subln import register_subln
    from bnhgq2 import qat
    from bnhgq2.train import load_train_data, make_callbacks, macro_ovr_auc, _softmax
    from bnhgq2.data import input_std_stats, apply_input_std

    apply_keras_compat()
    register_subln()
    keras.utils.set_random_seed(int(seed))

    tr = cfg["train"]
    A = cfg["arch"]
    dz = cfg.get("distill", {})
    n_part = A["n_part"]
    n_classes = int(A["n_classes"])
    act_bits = int(cfg["quant"]["act_bits"])
    alpha = float(dz.get("alpha", DEFAULT_ALPHA))
    temperature = float(dz.get("temperature", DEFAULT_TEMPERATURE))
    teacher_run = dz["teacher_run"]
    teacher_project = dz.get("teacher_project", TEACHER_PROJECT_DEFAULT)
    os.makedirs(out_dir, exist_ok=True)

    if not A.get("input_std", False):
        raise SystemExit("r12 KD assumes the round-8 input_std contract "
                         "(arch.input_std must be true)")

    epochs = 3 if smoke else int(tr["epochs"])
    warmup = 0 if smoke else int(tr["warmup_epochs"])
    decay = 2 if smoke else int(tr["decay_epochs"])
    max_files = 2 if smoke else tr.get("max_files")

    # ---- data: byte-identical flow to bnhgq2.train.train (same seed => same split) ----
    data_dir = os.environ.get("BNHGQ2_TRAIN_DATA", tr["data"])
    X, Y, nfiles = load_train_data(data_dir, n_part, max_files=max_files)
    rng = np.random.default_rng(int(seed))
    idx = rng.permutation(len(X))
    X, Y = X[idx], Y[idx]
    vsplit = float(tr.get("validation_split", 0.20))
    nval = int(len(X) * vsplit)
    Xval_raw, Yval = X[:nval], Y[:nval]
    Xtr_raw, Ytr = X[nval:], Y[nval:]
    del X
    print(f"[distill] data: {nfiles} files, {len(Xtr_raw)} train / {len(Xval_raw)} val, "
          f"class counts {Y.sum(0).astype(int).tolist()}", flush=True)

    # ---- student standardization (round-8 contract: stats from TRAIN split only) ----
    mu_s, sigma_s = input_std_stats(Xtr_raw)
    Xtr = apply_input_std(Xtr_raw, mu_s, sigma_s)
    Xval = apply_input_std(Xval_raw, mu_s, sigma_s)
    std_path = os.path.join(out_dir, "input_std.json")
    with open(std_path, "w") as f:
        json.dump({"mu": mu_s.tolist(), "sigma": sigma_s.tolist(),
                   "computed_from": "train split only",
                   "contract": "hardware receives standardized inputs (offline preprocessing)"},
                  f, indent=1)
    print(f"[distill] student input_std from train split "
          f"(|mu|max={float(np.abs(mu_s).max()):.4g}, "
          f"sigma_max={float(sigma_s.max()):.4g}) -> input_std.json", flush=True)

    # ---- teacher: fetch, load frozen, precompute logits ONCE (offline KD) ----
    tdir = fetch_teacher(teacher_run, teacher_project)
    teacher, mu_t, sigma_t = load_teacher(tdir)
    t0 = time.time()
    Ttr = teacher_logits(teacher, Xtr_raw, mu_t, sigma_t)
    Tval = teacher_logits(teacher, Xval_raw, mu_t, sigma_t)
    t_scores = _softmax(Tval)
    t_val_auc, _ = macro_ovr_auc(Yval, t_scores)
    t_acc = float((np.argmax(Tval, 1) == np.argmax(Yval, 1)).mean())
    print(f"[distill] teacher {teacher_run}: params={teacher.count_params():,} "
          f"logits precomputed in {time.time() - t0:.0f}s | on the student's val "
          f"split: macro-OvR AUC={t_val_auc:.5f} acc={t_acc:.4f}", flush=True)
    del Xtr_raw, Xval_raw
    if not smoke and t_val_auc < 0.93:
        raise SystemExit(f"[distill] FATAL: teacher val AUC {t_val_auc:.5f} < 0.93 — "
                         "wrong checkpoint or standardization mismatch")

    # ---- student model + activation calibration (all imported from bnhgq2.qat) ----
    model, taps = qat.build_qat_model(cfg, seed=seed)
    site_i = qat.calibrate_activations(model, taps, Xtr, act_bits)
    nparams = int(model.count_params())
    ntrain = int(sum(np.prod(v.shape) for v in model.trainable_variables))
    print(f"[distill] student {cfg['name']} params={nparams:,} trainable={ntrain:,} "
          f"act_sites={len(site_i)} alpha={alpha} T={temperature}", flush=True)
    if cfg["quant"]["weight"] == "binary_absmean":
        effs = qat.effective_weight_values(model)
        ok = all(len(v) == 2 and not (v == 0).any() for v in effs.values())
        assert ok, "BINARY GATE FAILED at build: effective weights not exactly two-valued"
        print(f"[distill] binary gate OK ({len(effs)} bit-layers exactly +/-beta)", flush=True)

    # ---- optimizer: same contract as bnhgq2.train (Adam b2=0.98, clipvalue) ----
    lr = float(tr["lr"])
    clip_mode = tr.get("clip_mode", "value")
    opt_kw = dict(learning_rate=lr, beta_1=0.9, beta_2=float(tr.get("beta2", 0.98)),
                  weight_decay=float(tr.get("weight_decay", 0.01)))
    if clip_mode == "norm":
        opt_kw["global_clipnorm"] = float(tr.get("clipnorm", 1.0))
    else:
        opt_kw["clipvalue"] = float(tr.get("clipvalue", 1.0))
    KDLoss = make_kd_loss_class()
    model.compile(loss=KDLoss(n_classes, alpha=alpha, temperature=temperature),
                  optimizer=keras.optimizers.Adam(**opt_kw))

    # ---- wandb (layout: bnhgq2.wandb_util — entity/group/tags from env) ----
    from bnhgq2 import wandb_util as wbu
    use_wandb = wbu.wandb_enabled(tr.get("wandb_project"))
    if use_wandb:
        import wandb
        wandb.init(**wbu.init_kwargs(
            name=os.environ.get("WANDB_RUN_NAME") or f"{cfg['name']}-s{seed}",
            job_type="distill", cfg_project=tr.get("wandb_project"),
            tags=["distill", f"s{seed}"],
            config={"variant": "w1a8-distill", "seed": int(seed),
                           "act_bits": act_bits, "weight": cfg["quant"]["weight"],
                           "config_hash": cfg_hash_val, "params": nparams,
                           "lr": lr, "clip_mode": clip_mode, "smoke": smoke,
                           "kd_alpha": alpha, "kd_temperature": temperature,
                           "teacher_run": teacher_run,
                           "teacher_val_macro_auc_on_student_split": t_val_auc,
                           **{f"arch_{k}": v for k, v in A.items()}}))

    # ---- train (callbacks imported: val macro-AUC checkpointing + ES + LR schedule) ----
    best_path = os.path.join(out_dir, "model_best.keras")
    state = {"best_auc": -1.0, "best_epoch": -1}
    cbs = make_callbacks(Xval, Yval, best_path, int(tr.get("es_patience", 10)),
                         lr, warmup, decay, float(tr.get("decay_power", 1.0)),
                         use_wandb, state)
    Ykd = np.concatenate([Ytr, Ttr], axis=1).astype("float32")  # [onehot | teacher logits]
    t0 = time.time()
    model.fit(Xtr, Ykd, epochs=epochs, batch_size=int(tr.get("batch", 256)),
              verbose=2, callbacks=cbs)
    dt = time.time() - t0

    if state["best_epoch"] < 0:  # degenerate smoke: save final
        model.save(best_path)
        scores = _softmax(np.asarray(model.predict(Xval, batch_size=1024, verbose=0)))
        state["best_auc"], _ = macro_ovr_auc(Yval, scores)
        state["best_epoch"] = epochs - 1

    # ---- re-save the best checkpoint UNCOMPILED so the existing convert/ROC pipeline
    # can load it without this module (train.py's CE compile deserializes anywhere;
    # the KD compile would not). Weight order is identical (same builder, same cfg),
    # and equality is asserted before overwriting. ----
    best = keras.models.load_model(best_path, compile=False)
    clean, _ = qat.build_qat_model(cfg, seed=seed)
    clean.set_weights(best.get_weights())
    a = np.asarray(best.predict(Xval[:1024], batch_size=1024, verbose=0))
    b = np.asarray(clean.predict(Xval[:1024], batch_size=1024, verbose=0))
    dmax = float(np.abs(a - b).max())
    assert dmax < 1e-5, f"clean re-save mismatch: max|delta|={dmax}"
    clean.save(best_path)
    print(f"[distill] re-saved best checkpoint uncompiled (max|delta|={dmax:.2e})", flush=True)

    meta = {
        "variant": "w1a8-distill", "seed": int(seed), "config": cfg["name"],
        "config_hash": cfg_hash_val, "params": nparams, "trainable_params": ntrain,
        "best_epoch": state["best_epoch"], "best_val_macro_auc": state["best_auc"],
        "act_bits": act_bits, "weight": cfg["quant"]["weight"],
        "lr": lr, "clip_mode": clip_mode, "epochs_run": epochs, "smoke": smoke,
        "n_train": int(len(Xtr)), "n_val": int(len(Xval)), "n_files": nfiles,
        "train_seconds": round(dt, 1), "act_calib_i": site_i,
        "kd_alpha": alpha, "kd_temperature": temperature,
        "teacher_run": teacher_run, "teacher_project": teacher_project,
        "teacher_val_macro_auc_on_student_split": t_val_auc,
        "teacher_val_acc_on_student_split": t_acc,
        "started": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(t0)),
        "finished": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
    }
    meta_path = os.path.join(out_dir, "train_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"[distill] DONE best_epoch={state['best_epoch']} "
          f"best_val_macro_auc={state['best_auc']:.5f} in {dt:.0f}s", flush=True)
    print(f"[distill] wrote {best_path} + {meta_path}", flush=True)

    # ---- W&B upload + durability gate (same policy as bnhgq2.train: pods are
    # emptyDir-only, the run is the checkpoint's only durable home) ----
    if use_wandb:
        import wandb
        # Legacy run-file mirror (best-effort); the durability contract is the
        # versioned `model` artifact below (same policy as bnhgq2.train, 2026-08-01).
        try:
            base = os.path.dirname(os.path.abspath(out_dir))
            wandb.save(best_path, base_path=base, policy="now")
            wandb.save(meta_path, base_path=base, policy="now")
            wandb.save(std_path, base_path=base, policy="now")
            wandb.summary["best_val_macro_auc"] = state["best_auc"]
            wandb.summary["best_epoch"] = state["best_epoch"]
            wandb.summary["teacher_val_macro_auc_on_student_split"] = t_val_auc
        except Exception as e:
            print(f"[distill] wandb.save warn: {e}", flush=True)
        leaf = os.path.basename(os.path.abspath(out_dir))
        offline = os.environ.get("WANDB_MODE", "").lower().startswith(("off", "dis"))
        try:
            wbu.log_files_artifact(
                wandb.run, name=f"model-{leaf}", type="model",
                files=[best_path, meta_path, std_path],
                metadata={"variant": "w1a8-distill", "seed": int(seed),
                          "config_hash": cfg_hash_val,
                          "best_val_macro_auc": state["best_auc"],
                          "best_epoch": state["best_epoch"],
                          "teacher_run": teacher_run,
                          "kd_alpha": alpha, "kd_temperature": temperature})
        except Exception as e:
            if not smoke and not offline:
                wandb.finish()
                raise SystemExit(f"[distill] FATAL: model artifact for {leaf} not "
                                 f"durable on W&B: {e}")
            print(f"[distill] artifact warn (smoke/offline, non-fatal): {e}", flush=True)
        wandb.finish()
    return meta


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--out-dir", default=None)
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()

    from bnhgq2.config import load_config, cfg_hash
    cfg = load_config(a.config)
    if "distill" not in cfg or "teacher_run" not in cfg.get("distill", {}):
        raise SystemExit(f"{cfg['name']}: not a KD config (no distill.teacher_run)")
    h = cfg_hash(cfg)
    print(f"=== {cfg['name']} [{h}] seed={a.seed} ===", flush=True)
    out_dir = a.out_dir or os.path.join(
        os.environ.get("BNHGQ2_OUT_ROOT", os.path.join(HERE, "..", "..", "models", "r12")),
        f"{cfg['name']}-s{a.seed}")
    distill(cfg, seed=a.seed, out_dir=out_dir, smoke=a.smoke, cfg_hash_val=h)


if __name__ == "__main__":
    main()
