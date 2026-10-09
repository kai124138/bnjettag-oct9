#!/usr/bin/env python3
"""Quantization-aware ROC / eval driver for the HGQ2-native BitNet jet tagger.

The quantization-aware training  trains natively in HGQ2 so the trained
`.keras` IS the hardware model. This driver evaluates those checkpoints on the
held-out val split and produces the verifiable ROC deliverables:

  * per-model `.npz`  — keys y (one-hot, N×5 float32), score (N×5 softmax float32),
    meta (json string). Same key convention as roc-results/reference experiment/*.npz, so verify-roc /
    results-analyst recompute AUC from these exactly as they do for reference experiment.
  * roc_auc.md        — per-seed AUC table + per-variant seed-averaged (mean±std) rows,
    macro one-vs-rest + 5 per-class AUCs, labeled ROC-test.
  * roc_overlay.png   — HEP-style overlay (TPR linear x, mistag-rate FPR LOG y),
    one curve per variant (seed-1 by default) per class + a macro summary panel.

Unlike the QKeras make_roc.py, HGQ2 models are fully self-describing `.keras` files
(quantizers are baked into the layer configs — no BN_* env globals), so a SINGLE process
loads the val data ONCE and evaluates the whole 15-model matrix in a loop (`eval-all`).

Contract (INTERFACE, 2026-07-07): W&B project `binary-transformer`, entity
configured tracking entity; 15 runs `final-<variant>-s<seed>`,
variant in {fp32,w8a8,w1a8,w1a6,w1a4}, seed in {1,2,3}; each run + PVC path
`/data/outputs/final/<variant>-s<seed>/model_best.keras` carries `model_best.keras`
loadable via `import hgq` + `bnhgq2.subln.register_subln()` + compat patches +
`keras.models.load_model`.

Subcommands:
  eval      one checkpoint (explicit --keras, or resolved by variant/seed) -> npz
  eval-all  the whole matrix in one process (loads data once) -> npz's + roc_auc.md + png
  plot      aggregate existing npz's -> roc_auc.md + roc_overlay.png (re-run friendly)

NEVER conflate val_auc (the training monitor) with roc_test_auc (this file's output);
different data, different evaluation. Numbers here are comparable only against results at
the same input set and the same N (verify-roc SKILL).
"""
from __future__ import annotations

import argparse
import datetime
import glob
import json
import os
import sys

import numpy as np

# code/hgq2/evaluate_roc.py -> add code/hgq2 so `import bnhgq2` works (mirrors run_stage.py)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bnhgq2.data import CLASS_NICE, load_eval_set  # noqa: E402  (g/q/W/Z/t)

N_CLASSES = 5
N_PART = int(os.environ.get("BN_N_PART", "10"))
EXPECT_N_DEFAULT = int(os.environ.get("BNF_EXPECT_N", "260000"))
ENTITY = os.environ.get("WANDB_ENTITY", os.environ.get("WANDB_ENTITY", ""))
FINAL_PROJECT = os.environ.get("WANDB_PROJECT", "binary-transformer")

# variant -> npz key + nominal weight/activation bit-widths (metadata only)
VARIANT_META = {
    "fp32": {"key": "FP32", "weight_bits": 32, "act_bits": 32},
    "w8a8": {"key": "W8A8", "weight_bits": 8, "act_bits": 8},
    "w1a8": {"key": "W1A8", "weight_bits": 1, "act_bits": 8},
    "w1a6": {"key": "W1A6", "weight_bits": 1, "act_bits": 6},
    "w1a4": {"key": "W1A4", "weight_bits": 1, "act_bits": 4},
}
VARIANTS = list(VARIANT_META)
SEEDS = [1, 2, 3]

# Optional SIZE axis (reference experiment deployable-scale matrix). The quantization-aware training has NO size
# axis: passing no --sizes keeps size="" everywhere and every output byte-identical to the
# pre-reference experiment driver. reference experiment passes --sizes small,tiny --run-prefix reference experiment, which yields W&B
# runs reference experiment-<size>-<variant>-s<seed>, ckpt subdir / PVC tag <size>-<variant>-s<seed>, and
# npz + table key <SIZE>-<VARIANT> (e.g. SMALL-W1A8-s1.npz).
SIZE_KEY = {"small": "SMALL", "tiny": "TINY"}       # size token -> npz/table KEY
SIZE_ORDER = {"": 0, "SMALL": 1, "TINY": 2}          # "" (final) sorts first, stable
RUN_PREFIX_DEFAULT = os.environ.get("BNF_RUN_PREFIX", "final")


def _size_key(size):
    """Size token -> its NPZ/table KEY ('' for the no-size final campaign)."""
    return (SIZE_KEY.get(size, size.upper()) if size else "")


def _tag(variant, seed, size=""):
    """Checkpoint subdir / PVC tag: <size>-<variant>-s<seed> (or <variant>-s<seed>)."""
    return f"{size}-{variant}-s{seed}" if size else f"{variant}-s{seed}"


# plot styling (one colour per variant); ORDER fixes legend / row order
COLORS = {"FP32": "#e87bd0", "W8A8": "#d2691e",
          "W1A8": "#56b4b0", "W1A6": "#e6a817", "W1A4": "#cf3bc4"}
ORDER = {"FP32": 0, "W8A8": 1, "W1A8": 2, "W1A6": 3, "W1A4": 4}


# --------------------------------------------------------------------------- #
# model loading (the contract's load incantation)                             #
# --------------------------------------------------------------------------- #
_ENV_READY = False


def _prepare_env():
    """Register everything keras.models.load_model needs for an HGQ2 model.

    Idempotent. `import hgq` registers the Q* layers; importing bnhgq2.subln
    registers the PSubLN keras-serializable; apply_keras_compat re-adds
    keras-3.15's dropped EinsumDense.full_output_shape (hgq reads it at call).
    register_subln() is the contract's incantation (harmless for a pure keras
    load); never let its hls4ml-side registration abort an eval.
    """
    global _ENV_READY
    if _ENV_READY:
        return
    import hgq  # noqa: F401  (registers hgq Q* layers for deserialization)
    import bnhgq2.qat  # noqa: F401  (registers BitQEinsumDense/BitQDense/AddPositional
    #                     — the QAT-trained final checkpoints deserialize through these;
    #                     without this import load_model fails on every kai-bnf ckpt)
    from bnhgq2.compat import apply_keras_compat
    from bnhgq2.subln import register_subln  # import registers PSubLN serializable

    apply_keras_compat()
    try:
        register_subln()
    except Exception as e:  # pragma: no cover - defensive
        sys.stderr.write(f"[warn] register_subln skipped ({e!r}); keras load still OK\n")
    _ENV_READY = True


def load_final_model(keras_path):
    _prepare_env()
    import keras
    return keras.models.load_model(keras_path, compile=False)


def predict_in_batches(model, X, batch=8192):
    outs = []
    for i in range(0, len(X), batch):
        outs.append(np.asarray(model(X[i:i + batch], training=False)))
    return np.concatenate(outs)


def softmax64(logits):
    z = logits.astype(np.float64)
    z = z - z.max(axis=-1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=-1, keepdims=True)


def macro_ovr_auc(y_onehot, scores):
    """Project-canonical macro one-vs-rest AUC (verify.py / verify-roc SKILL):
    per-class sklearn roc_auc_score, macro = unweighted mean. float64 inside."""
    from sklearn.metrics import roc_auc_score
    per = [float(roc_auc_score(y_onehot[:, c], scores[:, c]))
           for c in range(y_onehot.shape[1])]
    return float(np.mean(per)), per


# --------------------------------------------------------------------------- #
# data                                                                        #
# --------------------------------------------------------------------------- #
def load_data_checked(data_dir, expect_n, n_part=N_PART, features=None):
    X, y = load_eval_set(data_dir, n_part=n_part, features=features)
    if expect_n and len(X) != expect_n:
        raise AssertionError(
            f"held-out split n={len(X)} != expected {expect_n} "
            f"(data_dir={data_dir}); refuse to evaluate a wrong/partial split")
    if y.shape[1] != N_CLASSES:
        raise AssertionError(f"labels have {y.shape[1]} columns, expected {N_CLASSES}")
    return X, y


# --------------------------------------------------------------------------- #
# checkpoint resolution (PVC primary, W&B fallback) — knob CKPT_SOURCE=pvc|wandb #
# --------------------------------------------------------------------------- #
def _wandb_download_ckpt(variant, seed, workdir, project, entity,
                         size="", run_prefix="final"):
    """Download model_best.keras for run <run_prefix>-[<size>-]<variant>-s<seed>.
    Artifact-first (model-<run> versioned artifact, 2026-08+ runs) with run-file
    fallback for pre-overhaul runs — both via bnhgq2.wandb_util.fetch_checkpoint.
    None if absent."""
    tag = _tag(variant, seed, size)
    name = f"{run_prefix}-{tag}"
    try:
        from bnhgq2 import wandb_util as wbu
        d = wbu.fetch_checkpoint(name, os.path.join(workdir, tag),
                                 project=project, entity=entity)
    except Exception as e:  # pragma: no cover
        sys.stderr.write(f"[warn] W&B fetch failed for {name} ({e!r})\n")
        return None
    if d is None:
        sys.stderr.write(f"[warn] {name}: no W&B checkpoint (artifact or run files)\n")
        return None
    p = os.path.join(d, "model_best.keras")
    return p if os.path.isfile(p) else None


def resolve_checkpoint(variant, seed, ckpt_root, source, project, entity,
                       workdir, allow_wandb_fallback, size="", run_prefix="final"):
    """Return (path, source_label) or (None, None) so a missing model is SKIPPED."""
    tag = _tag(variant, seed, size)
    if source == "pvc":
        p = os.path.join(ckpt_root, tag, "model_best.keras")
        if os.path.exists(p):
            return p, "pvc"
        if allow_wandb_fallback:
            p = _wandb_download_ckpt(variant, seed, workdir, project, entity,
                                     size, run_prefix)
            if p:
                return p, "wandb(fallback)"
        return None, None
    if source == "wandb":
        p = _wandb_download_ckpt(variant, seed, workdir, project, entity,
                                 size, run_prefix)
        return (p, "wandb") if p else (None, None)
    raise ValueError(f"unknown checkpoint source {source!r} (use pvc|wandb)")


# --------------------------------------------------------------------------- #
# eval one model -> npz                                                        #
# --------------------------------------------------------------------------- #
def eval_one(keras_path, X, y, variant, seed, source, npz_path, batch=8192, size=""):
    vm = VARIANT_META[variant]
    skey = _size_key(size)
    label = f"{skey}-{vm['key']}-s{seed}" if skey else f"{vm['key']}-s{seed}"
    model = load_final_model(keras_path)
    raw = predict_in_batches(model, X, batch)
    assert raw.ndim == 2 and raw.shape[1] == N_CLASSES, (
        f"{keras_path}: model outputs {raw.shape}, expected (*,{N_CLASSES})")
    # bnhgq2.build heads output LOGITS (no final softmax) -> apply softmax once, exactly
    # like make_roc.py. Guard the contract: if a checkpoint ever already emits a
    # probability simplex, use it as-is (re-softmaxing would corrupt per-column ranking).
    rowsum = raw.astype(np.float64).sum(axis=1)
    if raw.min() >= -1e-6 and np.allclose(rowsum, 1.0, atol=1e-3):
        sys.stderr.write(f"[warn] {os.path.basename(keras_path)}: output already looks like "
                         "a probability simplex — using as-is (NOT re-softmaxing)\n")
        score = raw.astype("float32")
    else:
        score = softmax64(raw).astype("float32")
    macro, per = macro_ovr_auc(y, score)  # from the SAME array written to npz
    meta = dict(
        label=label, key=vm["key"], variant=variant, seed=int(seed),
        weight_bits=vm["weight_bits"], act_bits=vm["act_bits"],
        auc=macro, auc_per_class=dict(zip(CLASS_NICE, per)),
        n=int(len(y)), checkpoint=os.path.abspath(keras_path),
        checkpoint_source=source, model=os.path.basename(keras_path),
        campaign=("round7" if skey else "final"), era=2,
        metric="roc_test_auc_macro_ovr",
        date=datetime.date.today().isoformat(),
    )
    if skey:  # reference experiment only: preserves byte-identical final-campaign npz meta
        meta["size"] = skey
    os.makedirs(os.path.dirname(os.path.abspath(npz_path)), exist_ok=True)
    np.savez_compressed(npz_path, y=y.astype("float32"), score=score,
                        meta=json.dumps(meta))
    return meta


# --------------------------------------------------------------------------- #
# aggregate npz -> table + overlay                                             #
# --------------------------------------------------------------------------- #
def _key_from_meta(m):
    if "key" in m:
        return m["key"]
    return VARIANT_META.get(m.get("variant", ""), {}).get("key", m.get("variant", "?"))


def runs_from_npz(files):
    """Load npz's and RECOMPUTE AUC from the stored arrays so the table equals
    exactly what verify-roc / results-analyst recompute from the same npz."""
    runs = []
    for f in sorted(files):
        d = np.load(f, allow_pickle=True)
        m = json.loads(str(d["meta"]))
        macro, per = macro_ovr_auc(d["y"], d["score"])
        m["auc"] = macro
        m["auc_per_class"] = dict(zip(CLASS_NICE, per))
        m["key"] = _key_from_meta(m)
        m["_file"] = os.path.abspath(f)
        runs.append(m)
    return runs


def _mean_std(vals):
    a = np.asarray(vals, dtype=np.float64)
    return float(a.mean()), (float(a.std(ddof=1)) if len(a) > 1 else 0.0)


def write_auc_table(runs, path, n=None, with_size=None,
                    title_line=None, source_line=None):
    """Per-seed + seed-averaged AUC table. When any run carries a `size` (reference experiment) an
    extra SIZE column is emitted and seed-averaging groups per size×variant; when none do
    (final campaign) the output is byte-identical to the pre-reference experiment driver. `title_line`
    / `source_line` override the header (default = the Quantization-aware strings)."""
    if with_size is None:
        with_size = any(m.get("size") for m in runs)
    title_line = title_line or \
        "# FINAL campaign — ROC-test AUC (public HLS4ML LHC Jet, 5-class)"
    source_line = source_line or "# source : recomputed from results/predictions/pre_conference/*.npz (y, score)"
    sz_hdr = "size | " if with_size else ""
    sz_extra = 1 if with_size else 0
    rs = sorted(runs, key=lambda m: (SIZE_ORDER.get(m.get("size", ""), 99),
                                     ORDER.get(m["key"], 99), m.get("seed", 0)))
    n = n if n is not None else (rs[0]["n"] if rs else "?")
    L = [
        title_line,
        "#",
        "# metric : ROC-test macro one-vs-rest AUC on the held-out val split",
        "#          (sklearn roc_auc_score per class; macro = unweighted mean) — NOT val AUC",
        f"# n_eval : {n} jets    (comparable only at matched input set and N)",
        source_line,
        f"# gen    : {datetime.date.today().isoformat()} by code/hgq2/evaluate_roc.py",
        "",
        "## Per-seed",
        "",
        "| run | " + sz_hdr + "variant | w/a bits | seed | "
        + " | ".join(f"AUC({c})" for c in CLASS_NICE) + " | macro | n |",
        "|" + "---|" * (len(CLASS_NICE) + 5 + sz_extra),
    ]
    for m in rs:
        wa = f"{m.get('weight_bits', '?')}/{m.get('act_bits', '?')}"
        sz_cell = f"{m.get('size', '')} | " if with_size else ""
        L.append(
            f"| {m['label']} | " + sz_cell + f"{m['variant']} | {wa} | {m.get('seed', '?')} | "
            + " | ".join(f"{m['auc_per_class'][c]:.4f}" for c in CLASS_NICE)
            + f" | **{m['auc']:.4f}** | {m['n']} |")
    L += [
        "",
        "## Seed-averaged (mean ± sample std over available seeds)",
        "",
        "| " + sz_hdr + "variant | w/a bits | seeds | "
        + " | ".join(f"AUC({c})" for c in CLASS_NICE) + " | macro | n_seed |",
        "|" + "---|" * (len(CLASS_NICE) + 4 + sz_extra),
    ]
    by_var = {}
    for m in rs:
        by_var.setdefault((m.get("size", ""), m["key"]), []).append(m)
    for gk in sorted(by_var, key=lambda k: (SIZE_ORDER.get(k[0], 99), ORDER.get(k[1], 99))):
        ms = by_var[gk]
        wa = f"{ms[0].get('weight_bits', '?')}/{ms[0].get('act_bits', '?')}"
        seeds = ",".join(str(m.get("seed")) for m in sorted(ms, key=lambda m: m.get("seed", 0)))
        cells = []
        for c in CLASS_NICE:
            mu, sd = _mean_std([m["auc_per_class"][c] for m in ms])
            cells.append(f"{mu:.4f}±{sd:.4f}")
        mu, sd = _mean_std([m["auc"] for m in ms])
        sz_cell = f"{gk[0]} | " if with_size else ""
        L.append(
            "| " + sz_cell + f"{ms[0]['variant']} | {wa} | {seeds} | " + " | ".join(cells)
            + f" | **{mu:.4f}±{sd:.4f}** | {len(ms)} |")
    table = "\n".join(L) + "\n"
    if path:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as fh:
            fh.write(table)
        print(f"[roc] wrote {path}")
    return table


def make_overlay(runs, png, title, overlay_seed=1):
    """HEP-style overlay: x=TPR (tagging efficiency), y=FPR mistag rate on LOG axis.
    One curve per variant for `overlay_seed`; last panel = macro-AUC summary."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve

    sel = [m for m in runs if m.get("seed") == overlay_seed]
    if not sel:
        sel = runs  # fallback: whatever we have
    sel = sorted(sel, key=lambda m: ORDER.get(m["key"], 99))

    fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.6), dpi=150)
    axes = axes.ravel()
    for k, c in enumerate(CLASS_NICE):
        ax = axes[k]
        for m in sel:
            d = np.load(m["_file"], allow_pickle=True)
            fpr, tpr, _ = roc_curve(d["y"][:, k], d["score"][:, k])
            ok = fpr > 0
            ax.plot(tpr[ok], fpr[ok], color=COLORS.get(m["key"]), lw=1.6,
                    label=f'{m["key"]} (AUC={m["auc_per_class"][c]:.4f})')
        ax.set_yscale("log")
        ax.set(xlabel=f"{c} tagging efficiency (TPR)",
               ylabel="Mistag rate (FPR, one-vs-rest)",
               title=f"{c} vs rest", xlim=(0, 1))
        ax.legend(loc="upper left", fontsize=7)
        ax.grid(alpha=0.3, which="both")
    axm = axes[-1]
    axm.axis("off")
    lines = [f'{m["key"]:6s} macro AUC = {m["auc"]:.4f}' for m in sel]
    axm.text(0.02, 0.95, f"Macro (mean OvR) AUC  (seed {overlay_seed})\n" + "\n".join(lines),
             family="monospace", fontsize=9, va="top")
    fig.suptitle(title, fontsize=13)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    os.makedirs(os.path.dirname(os.path.abspath(png)), exist_ok=True)
    fig.savefig(png)
    plt.close(fig)
    print(f"[roc] wrote {png}")


# --------------------------------------------------------------------------- #
# W&B eval logging (opt-in --wandb-log; W&B layout 2026-08-01)                 #
# --------------------------------------------------------------------------- #
def _wandb_log_eval(runs, out_dir, run_prefix, project, entity):
    """One job_type=eval run for the evaluated matrix: per-model ROC-test AUCs as
    summary metrics, the npz/table/overlay bundle as a versioned `evaluation`
    artifact, and a `test_macro_auc` backfill onto each source training run so
    val and ROC-test AUC sit side by side. Metrics here are PROVENANCE — the
    number of record stays the local recompute from the .npz (verify-roc)."""
    from bnhgq2 import wandb_util as wbu
    if not wbu.wandb_enabled(project):
        print("[wandb] --wandb-log requested but WANDB_API_KEY not set — skipping")
        return
    import wandb
    run = wandb.init(**wbu.init_kwargs(
        name=f"{run_prefix}-roc-eval", job_type="eval",
        cfg_project=project, tags=["eval", "roc-test"],
        config={"run_prefix": run_prefix, "n_models": len(runs),
                "n_eval": runs[0]["n"] if runs else 0,
                "metric": "roc_test_auc_macro_ovr", "era": 2}))
    for m in runs:
        run.summary[f"test_macro_auc/{m['label']}"] = m["auc"]
        for c, v in m["auc_per_class"].items():
            run.summary[f"test_auc_{c}/{m['label']}"] = v
    try:
        wbu.log_files_artifact(
            run, name=f"evaluation-{run_prefix}", type="evaluation", files=[out_dir],
            metadata={"models": {m["label"]: m["auc"] for m in runs},
                      "n_eval": runs[0]["n"] if runs else 0, "era": 2,
                      "metric": "roc_test_auc_macro_ovr"})
    except Exception as e:
        print(f"[wandb] evaluation artifact warn: {e}", flush=True)
    # backfill each training run's summary (best-effort; pre-overhaul runs included)
    api = wandb.Api(timeout=120)
    ent = entity or wbu.resolve_entity()
    proj = project or wbu.resolve_project()
    for m in runs:
        # npz label SIZE-KEY-s<seed> -> training run name <prefix>-[<size>-]<variant>-s<seed>
        src = f"{run_prefix}-{m['label'].lower()}"
        try:
            rs = list(api.runs(f"{ent}/{proj}", filters={"display_name": src}))
            for r in rs:
                r.summary["test_macro_auc"] = m["auc"]
                r.summary.update()
            if rs:
                print(f"[wandb] backfilled test_macro_auc={m['auc']:.4f} -> {src} "
                      f"({len(rs)} run(s))", flush=True)
        except Exception as e:
            print(f"[wandb] backfill warn for {src}: {e}", flush=True)
    wandb.finish()


# --------------------------------------------------------------------------- #
# subcommands                                                                  #
# --------------------------------------------------------------------------- #
def cmd_eval(a):
    os.environ.setdefault("MPLBACKEND", "Agg")
    feats = [f for f in getattr(a, "features", "").split(",") if f] or None
    X, y = load_data_checked(a.data, a.expect_n, n_part=a.n_part, features=feats)
    print(f"[data] X{X.shape} y{y.shape} (n={len(X)}, n_part={a.n_part}, "
          f"features={feats or 'all16'})", flush=True)
    if getattr(a, "input_std", ""):
        import json as _json
        from bnhgq2.data import apply_input_std
        st = _json.load(open(a.input_std))
        X = apply_input_std(X, st["mu"], st["sigma"])
        print(f"[data] input_std applied from {a.input_std} (input-standardized model contract)", flush=True)
    if a.keras:
        ck, src = a.keras, "explicit"
    else:
        ck, src = resolve_checkpoint(a.variant, a.seed, a.ckpt_root, a.ckpt_source,
                                     a.wandb_project, a.entity, a.workdir,
                                     a.allow_wandb_fallback,
                                     size=a.size, run_prefix=getattr(a, "run_prefix", "final"))
    if ck is None:
        print(f"[skip] {_tag(a.variant, a.seed, a.size)}: no checkpoint")
        return
    meta = eval_one(ck, X, y, a.variant, a.seed, src, a.npz, batch=a.batch, size=a.size)
    percls = "  ".join(f"{c}={meta['auc_per_class'][c]:.4f}" for c in CLASS_NICE)
    print(f"[roc] {meta['label']:10s} macroAUC={meta['auc']:.4f}  [{percls}]  "
          f"n={meta['n']}  src={meta['checkpoint_source']}  ({meta['model']})")


def cmd_eval_all(a):
    os.environ.setdefault("MPLBACKEND", "Agg")
    variants = a.variants.split(",") if a.variants else VARIANTS
    seeds = [int(s) for s in a.seeds.split(",")] if a.seeds else SEEDS
    # --sizes empty => no size axis (final campaign); reference experiment passes small,tiny
    sizes = a.sizes.split(",") if a.sizes else [""]
    run_prefix = getattr(a, "run_prefix", "final")
    feats = [f for f in getattr(a, "features", "").split(",") if f] or None
    X, y = load_data_checked(a.data, a.expect_n, n_part=a.n_part, features=feats)
    print(f"[data] held-out split: X{X.shape} y{y.shape} (n={len(X)}, "
          f"n_part={a.n_part}, features={feats or 'all16'})", flush=True)
    os.makedirs(a.out, exist_ok=True)
    workdir = a.workdir or os.path.join(a.out, "_ckpt_dl")

    done = []
    for sz in sizes:
        skey = _size_key(sz)
        for v in variants:
            for s in seeds:
                key = VARIANT_META[v]["key"]
                tag = f"{skey}-{key}-s{s}" if skey else f"{key}-s{s}"
                npz = os.path.join(a.out, f"{tag}.npz")
                ck, src = resolve_checkpoint(v, s, a.ckpt_root, a.ckpt_source,
                                             a.wandb_project, a.entity, workdir,
                                             a.allow_wandb_fallback,
                                             size=sz, run_prefix=run_prefix)
                if ck is None:
                    print(f"[skip] {tag}: no checkpoint "
                          f"(source={a.ckpt_source}, root={a.ckpt_root})", flush=True)
                    continue
                print(f"[eval] {tag}  <- {ck}  ({src})", flush=True)
                # reference experiment input_std contract: if the checkpoint ships its train-split
                # stats (the artifact fetch delivers input_std.json beside the model),
                # standardize a COPY of X with THAT model's stats before predicting.
                Xm = X
                std_p = os.path.join(os.path.dirname(ck), "input_std.json")
                if os.path.isfile(std_p):
                    from bnhgq2.data import apply_input_std
                    st = json.load(open(std_p))
                    Xm = apply_input_std(X, st["mu"], st["sigma"])
                    print(f"[eval] {tag}: input_std applied from checkpoint", flush=True)
                meta = eval_one(ck, Xm, y, v, s, src, npz, batch=a.batch, size=sz)
                percls = "  ".join(f"{c}={meta['auc_per_class'][c]:.4f}" for c in CLASS_NICE)
                print(f"[eval] {meta['label']:14s} macroAUC={meta['auc']:.4f}  [{percls}]  "
                      f"n={meta['n']}", flush=True)
                done.append(npz)

    if not done:
        print("[warn] no checkpoints evaluated — nothing to aggregate", flush=True)
        return
    runs = runs_from_npz(glob.glob(os.path.join(a.out, "*.npz")))
    write_auc_table(runs, os.path.join(a.out, "roc_auc.md"), n=len(y),
                    title_line=(getattr(a, "table_title", "") or None),
                    source_line=(getattr(a, "table_source", "") or None))
    if a.sizes:  # reference experiment: one HEP-style overlay PER SIZE (SMALL / TINY)
        for sz in sizes:
            skey = _size_key(sz)
            srun = [m for m in runs if m.get("size") == skey]
            if srun:
                png = os.path.join(a.out, f"roc_overlay_{skey}.png")
                make_overlay(srun, png, f"{a.title} — {skey}", overlay_seed=a.overlay_seed)
    else:        # final campaign: single overlay (byte-identical call)
        make_overlay(runs, os.path.join(a.out, "roc_overlay.png"), a.title,
                     overlay_seed=a.overlay_seed)
    if getattr(a, "wandb_log", False):
        _wandb_log_eval(runs, a.out, run_prefix, a.wandb_project, a.entity)
    print(f"[done] {len(done)} models evaluated -> {a.out} "
          f"(roc_auc.md + roc_overlay*.png)", flush=True)


def cmd_plot(a):
    os.environ.setdefault("MPLBACKEND", "Agg")
    files = sorted(glob.glob(a.glob))
    if not files:
        raise FileNotFoundError(f"no .npz match {a.glob}")
    runs = runs_from_npz(files)
    table = write_auc_table(runs, a.table or None,
                            title_line=(getattr(a, "table_title", "") or None),
                            source_line=(getattr(a, "table_source", "") or None))
    if a.png:
        sizes_present = sorted({m.get("size", "") for m in runs if m.get("size")})
        if sizes_present:  # reference experiment: one overlay per size, suffixing the --png stem
            base, ext = os.path.splitext(a.png)
            for sk in sizes_present:
                srun = [m for m in runs if m.get("size") == sk]
                make_overlay(srun, f"{base}_{sk}{ext}", f"{a.title} — {sk}",
                             overlay_seed=a.overlay_seed)
        else:
            make_overlay(runs, a.png, a.title, overlay_seed=a.overlay_seed)
    print(table)


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def _add_resolve_args(p):
    p.add_argument("--ckpt-root", default="outputs/models",
                   help="PVC root: <root>/<variant>-s<seed>/model_best.keras")
    p.add_argument("--ckpt-source", choices=["pvc", "wandb"], default="pvc")
    p.add_argument("--wandb-project", default=FINAL_PROJECT)
    p.add_argument("--entity", default=ENTITY)
    p.add_argument("--workdir", default="", help="dir for W&B checkpoint downloads")
    p.add_argument("--allow-wandb-fallback", action="store_true",
                   help="if a PVC checkpoint is missing, try the W&B copy")
    p.add_argument("--n-part", type=int, default=N_PART,
                   help="top-N constituents by pT (pre-conference sweeps 8/16/32/64; "
                        "default %(default)s)")
    p.add_argument("--features", default="",
                   help="comma list of constituent-feature suffixes (pre-conference "
                        "L1-realistic: pt,etarel,phirel); empty = all 16")
    p.add_argument("--run-prefix", default=RUN_PREFIX_DEFAULT,
                   help="W&B run-name prefix <prefix>-[<size>-]<variant>-s<seed> "
                        "(default %(default)s; custom experiment prefix)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    e = sub.add_parser("eval", help="evaluate ONE checkpoint -> npz")
    e.add_argument("--keras", default="", help="explicit model_best.keras (skips resolution)")
    e.add_argument("--input-std", default="", help="input_std.json (input-standardized model: standardize X "
                   "with the checkpoint's train-split stats before eval)")
    e.add_argument("--variant", choices=VARIANTS, required=True)
    e.add_argument("--seed", type=int, required=True)
    e.add_argument("--data", required=True, help="held-out val dir (NRP: data/val)")
    e.add_argument("--npz", required=True)
    e.add_argument("--size", default="", help="optional size axis (round-7: small|tiny)")
    e.add_argument("--expect-n", type=int, default=EXPECT_N_DEFAULT,
                   help="assert loaded n (0 disables; default %(default)s)")
    e.add_argument("--batch", type=int, default=8192)
    _add_resolve_args(e)
    e.set_defaults(fn=cmd_eval)

    a = sub.add_parser("eval-all", help="evaluate the whole matrix in one process")
    a.add_argument("--data", required=True)
    a.add_argument("--out", required=True, help="output dir for npz + roc_auc.md + png")
    a.add_argument("--expect-n", type=int, default=EXPECT_N_DEFAULT)
    a.add_argument("--batch", type=int, default=8192)
    a.add_argument("--variants", default="", help="comma list (default all 5)")
    a.add_argument("--seeds", default="", help="comma list (default 1,2,3)")
    a.add_argument("--sizes", default="",
                   help="comma list of size tokens (round-7: small,tiny). Empty => no "
                        "size axis, byte-identical final-campaign behaviour")
    a.add_argument("--overlay-seed", type=int, default=1)
    a.add_argument("--title", default="FINAL BitNet jet tagger — ROC (HLS4ML LHC Jet, held-out val)")
    a.add_argument("--table-title", default="", help="override roc_auc.md header title line")
    a.add_argument("--table-source", default="", help="override roc_auc.md '# source' line")
    a.add_argument("--wandb-log", action="store_true",
                   help="log ROC-test AUCs + the npz bundle to W&B (job_type=eval run "
                        "+ versioned `evaluation` artifact + test_macro_auc backfill "
                        "onto the training runs); provenance only — the number of "
                        "record stays the local recompute")
    _add_resolve_args(a)
    a.set_defaults(fn=cmd_eval_all)

    q = sub.add_parser("plot", help="aggregate existing npz -> roc_auc.md + roc_overlay.png")
    q.add_argument("--glob", required=True)
    q.add_argument("--png", default="")
    q.add_argument("--table", default="")
    q.add_argument("--overlay-seed", type=int, default=1)
    q.add_argument("--title", default="FINAL BitNet jet tagger — ROC (HLS4ML LHC Jet, held-out val)")
    q.add_argument("--table-title", default="", help="override roc_auc.md header title line")
    q.add_argument("--table-source", default="", help="override roc_auc.md '# source' line")
    q.set_defaults(fn=cmd_plot)

    args = ap.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
