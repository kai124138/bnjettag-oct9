#!/usr/bin/env python3
"""Regenerate the starter notebooks in notebooks/ from this file.

The notebooks are meant to be edited freely once they are on the cluster; this
script exists so the *starting* state is reproducible and reviewable as plain
text rather than as committed JSON nobody reads.
"""
import json
import os
import textwrap

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "notebooks")

KERNEL = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"},
}


def md(src):
    return {"cell_type": "markdown", "metadata": {},
            "source": textwrap.dedent(src).strip("\n").splitlines(keepends=True)}


def code(src):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [],
            "source": textwrap.dedent(src).strip("\n").splitlines(keepends=True)}


def write(name, cells):
    # Compile every code cell before writing. A stray "\n" in one of the triple-quoted
    # blocks below becomes a real newline, which both breaks the string literal and
    # robs textwrap.dedent of its common prefix - silently emitting a notebook whose
    # cell is indented and cannot run. That shipped once; this is why it cannot again.
    for i, c in enumerate(cells):
        # nbformat 4.5 requires a stable per-notebook cell id. Deterministic ids keep
        # regenerated notebooks reviewable instead of producing random JSON churn.
        c.setdefault("id", f"cell-{i:03d}")
        if c["cell_type"] != "code":
            continue
        src = "".join(c["source"])
        try:
            compile(src, f"<{name} cell {i}>", "exec")
        except SyntaxError as e:
            raise SystemExit(f"{name}: cell {i} does not compile: {e}\n---\n{src}\n---")

    nb = {"cells": cells, "metadata": KERNEL, "nbformat": 4, "nbformat_minor": 5}
    path = os.path.join(OUT, name)
    with open(path, "w") as f:
        json.dump(nb, f, indent=1)
        f.write("\n")
    print("wrote", path)


# --------------------------------------------------------------------------- #
nb00 = [
    md("""
    # 00 — Is this kernel actually what I think it is?

    Six checks, in order, each one cheap. If a cell fails, stop there: everything
    below it depends on it.

    This is also a rough draft of a tutorial to my work, and it serves as documentation,
    and a source code to what I'm doing in my research.

    1. the kernel's environment,
    2. TensorFlow can see the GPU,
    3. `bnhgq2` imports, and from the copy `lab.sh sync` pushed,
    4. one `.h5` file loads with the round-14 `(N, 3)` inputs,
    5. the model the config describes builds,
    6. it runs a forward pass.
    """),

    md("### 1 — environment"),
    code("""
    import os, sys, shutil, platform, subprocess

    print("python :", sys.version.split()[0])
    print("prefix :", sys.prefix)
    print("host   :", platform.platform(), "|", platform.machine())
    for k in ("KERAS_BACKEND", "BNHGQ2_TRAIN_DATA", "BNHGQ2_OUT_ROOT",
              "BNHGQ2_STORE", "PYTHONPATH", "WANDB_MODE", "WANDB_PROJECT"):
        print(f"  {k:18s} = {os.environ.get(k)}")

    # nvidia-smi exists in the pod and not on the laptop; absence is information,
    # not an error - section 2 is what actually decides which device we get.
    if shutil.which("nvidia-smi"):
        print(subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv"],
            capture_output=True, text=True).stdout)
    else:
        print("\\nno nvidia-smi on this host (expected on the laptop)")
    """),

    md("### 2 — which device are we actually on?\n\nOn the NRP pod a GPU is the whole "
       "point, so its absence is a hard failure — a kernel that quietly fell back to CPU "
       "would be a pod worth deleting. On the laptop CPU is the expected answer: at 18,657 "
       "parameters the measured smoke train is *faster* on the M5's CPU than on the pod's "
       "2080 Ti, because dispatch overhead dominates long before the FLOPs do."),
    code("""
    import tensorflow as tf

    print("tensorflow", tf.__version__)
    gpus = tf.config.list_physical_devices("GPU")
    print("GPUs:", gpus or "none — running on CPU")
    if platform.system() == "Linux":
        assert gpus, "no GPU visible to TensorFlow (on the pod this is fatal)"
    """),

    md("### 3 — our code imports, and from the synced copy"),
    code("""
    import inspect
    import bnhgq2
    from bnhgq2 import config as bncfg, data as bndata, qat
    from bnhgq2 import train as bntrain

    print("bnhgq2 :", os.path.dirname(inspect.getfile(bnhgq2)))
    print("PROJECT_ROOT :", bncfg.PROJECT_ROOT)
    """),

    md("### 4 — a small sample: one `.h5` file, round-14 `(N, 3)` inputs\n\n"
       "`load_train_data` is the same function the cluster training job calls. "
       "`max_files=1` is the only thing making this small."),
    code("""
    import numpy as np

    CONFIG = os.path.join(os.environ["PYTHONPATH"], "configs", "r14-l1x3-n8-w1a8.json")
    cfg = bncfg.load_config(CONFIG)
    A = cfg["arch"]
    print(cfg["name"], "| n_part", A["n_part"], "| features", A["features"],
          "| weight", cfg["quant"]["weight"], "| act_bits", cfg["quant"]["act_bits"])

    X, Y, nfiles = bntrain.load_train_data(
        os.environ["BNHGQ2_TRAIN_DATA"], A["n_part"],
        max_files=1, features=A["features"])

    print("files :", nfiles)
    print("X     :", X.shape, X.dtype)
    print("Y     :", Y.shape, Y.dtype)
    print("class counts:", dict(zip(bndata.CLASS_NICE, Y.sum(0).astype(int))))
    """),

    md("### 5 — build the model the config describes"),
    code("""
    model, taps = qat.build_qat_model(cfg, seed=1)
    model.summary()
    # count_params() is the TOTAL (trainable + non-trainable); the summary above
    # splits them. For r14-l1x3-n8-w1a8 the total is 18,657.
    print("total parameters:", model.count_params())
    """),

    md("### 6 — one forward pass"),
    code("""
    import time

    xb = X[:256]
    _ = model(xb[:8], training=False)                     # trace/compile once
    t0 = time.time()
    logits = model(xb, training=False)
    dt = time.time() - t0
    print("logits :", np.asarray(logits).shape)
    print(f"forward pass on 256 jets: {dt * 1e3:.1f} ms")
    """),

    md("""
    ---
    If all six passed, the kernel is real, the data is reachable and the model
    builds. Next: **`01_smoke_train.ipynb`** actually trains it (3 epochs, 2 files).
    """),
]

# --------------------------------------------------------------------------- #
nb01 = [
    md("""
    # 01 — Smoke train: does the whole training path run?

    `smoke=True` is the project's own small-sample switch, not something invented
    here — `bnhgq2.train.train` reads it and caps the run to **3 epochs over 2
    `.h5` files** with no warmup. It exercises the same code the 6-hour cluster
    jobs run, in a couple of minutes.

    **This produces no result worth quoting.** The AUC printed below is from ~3
    epochs on ~2% of the data. Nothing here goes near `RESEARCH.md`.

    W&B is off in this pod (no API key is mounted), so nothing lands next to the
    round-14 record.
    """),

    md("### setup"),
    code("""
    import os, json, time
    from bnhgq2 import config as bncfg
    from bnhgq2.train import train

    CONFIG = os.path.join(os.environ["PYTHONPATH"], "configs", "r14-l1x3-n8-w1a8.json")
    cfg = bncfg.load_config(CONFIG)
    h = bncfg.cfg_hash(cfg)
    out_dir = os.path.join(os.environ["BNHGQ2_OUT_ROOT"], f"smoke-{cfg['name']}-s1")

    from bnhgq2 import wandb_util as wbu
    print("config   :", cfg["name"], "| hash", h)
    print("out_dir  :", out_dir)
    print("wandb on :", wbu.wandb_enabled(cfg["train"].get("wandb_project")))
    """),

    md("### run it"),
    code("""
    t0 = time.time()
    meta = train(cfg, seed=1, out_dir=out_dir, smoke=True, cfg_hash=h)
    print(f"\\nwall clock: {(time.time() - t0) / 60:.1f} min")
    meta
    """),

    md("### what it left behind"),
    code("""
    for f in sorted(os.listdir(out_dir)):
        p = os.path.join(out_dir, f)
        print(f"{os.path.getsize(p) / 1e6:9.2f} MB  {f}")

    with open(os.path.join(out_dir, "train_meta.json")) as fh:
        meta = json.load(fh)

    # The full meta carries the per-site activation grids, which are long; print the
    # fields that say whether the run was sane, and keep `meta` around to inspect.
    for k in ("config", "config_hash", "variant", "weight", "act_bits", "params",
              "trainable_params", "smoke", "epochs_run", "n_files", "n_train",
              "n_val", "best_epoch", "best_val_macro_auc", "train_seconds"):
        print(f"  {k:20s} {meta[k]}")
    print("\\nact sites tracked:", len(meta["act_grid_after"]),
          "| grids that moved:",
          sum(1 for k in meta["act_grid_before"]
              if meta["act_grid_before"][k] != meta["act_grid_after"][k]))
    """),

    md("""
    ---
    A `model_best.keras` plus a `train_meta.json` with `"smoke": true` means the
    training path is intact end to end.

    To change what is being tested, point `CONFIG` at a different file in
    `configs/` — `r14-l1x3-n8-w1a4.json` (4-bit activations),
    `...-fp32.json` (the float baseline), `...-n64-...` (64 constituents). The
    architecture and precision live entirely in that JSON.
    """),
]



# --------------------------------------------------------------------------- #
# 02 — binary-transformer debugging and resource workbench                    #
# --------------------------------------------------------------------------- #
nb02 = [
    md("""
    # Binary transformer debug workbench

    An interactive place to inspect, change, and debug the real BNJetTag binary
    transformer one stage at a time. Every model cell calls the functions the cluster
    jobs call; the notebook does not carry a second implementation that can drift from
    the pipeline.

    **The claim being built.** A jet tagger for the CMS Level-1 trigger whose weights are
    binary: `{-1, +1}` times one scale per tensor. A multiply by ±1 is a sign flip, and an
    FPGA does sign flips in logic (LUTs) rather than in a DSP block. DSPs are the scarce
    resource on a trigger board, so a binary core that uses none of them buys room for
    everything else. What that costs in tagging accuracy is the question the project
    exists to answer.

    **Normal loop:** edit the controls cell below, restart the kernel, and run through
    Parts 0–11. Those cells load one data file, expose intermediate tensors, check one
    backward pass, and report model/runtime resources without changing weights. Parts
    12–13 are an optional smoke train and score pass.

    Resource numbers have deliberately different labels:

    - **parameters / payload / MACs** are structural estimates;
    - **EBOPs** come from HGQ2's quantizers and graph;
    - **latency / RAM / GPU memory** are measurements on this kernel;
    - **LUT / FF / DSP / BRAM / cycle latency** only come from Vitis synthesis. This
      notebook does not relabel a software estimate as FPGA utilization.

    Nothing produced here is a research result.
    """),

    md("""
    ---
    ## Part 0 — controls and environment

    `bnhgq2` is nine modules that matter. This notebook imports six of them:

    | module | what it owns | used in |
    | --- | --- | --- |
    | `config.py` | load / validate a config JSON, hash it | Part 2 |
    | `data.py` | the eval loader, feature selection, input standardization | Parts 1, 13 |
    | `binarize.py` | absmean binarization + the β-fold bookkeeping | Part 3 |
    | `qat.py` | **the training model**: binary layers, quantizer configs, calibration | Parts 5–11 |
    | `train.py` | the training loop, the train-split loader | Parts 1, 12 |
    | `gold.py` | an independent numpy model, and the AUC helper | Part 13 |

    The three it does *not* import, because they belong to the export half of the
    pipeline: `build.py` (re-emits the trained model as a static hardware graph),
    `convert.py` (hls4ml), `verify.py` (the three fidelity gates). Part 14 says where
    those fit.

    Everything below runs against whatever `PYTHONPATH` points at. Change only this
    first code cell for the usual experiments, then use **Restart Kernel and Run All**.
    Leave `RUN_SMOKE_TRAIN = False` while debugging; Part 8 already checks gradients
    without updating a weight.
    """),
    code("""
    import os, sys, json, glob, time, platform, resource
    import numpy as np
    import tensorflow as tf

    # ---- workbench controls -------------------------------------------------
    CONFIG_NAME = "r14-l1x3-n8-w1a8.json"
    DATA_FILES = 1
    DEBUG_BATCH = 32
    CALIBRATION_JETS = 4096
    BENCHMARK_STEPS = 20
    RUN_EBOPS = True
    RUN_SMOKE_TRAIN = False       # opt in: 3 epochs over 2 files
    SEED = 1

    CODE = os.environ["PYTHONPATH"]
    TRAIN_DIR = os.environ["BNHGQ2_TRAIN_DATA"]

    print("python :", sys.version.split()[0], "|", platform.platform())
    print("code   :", CODE)
    print("train  :", TRAIN_DIR)
    print("wandb  :", os.environ.get("WANDB_MODE"), "->", os.environ.get("WANDB_PROJECT"))

    from bnhgq2 import config as bncfg, data as bndata, qat
    from bnhgq2 import train as bntrain
    from bnhgq2.binarize import absmean_binarize
    from bnhgq2.gold import macro_ovr_auc, softmax64
    import bnhgq2

    CONFIG = os.path.join(CODE, "configs", CONFIG_NAME)
    cfg = bncfg.load_config(CONFIG)
    h = bncfg.cfg_hash(cfg)
    A = cfg["arch"]

    print()
    print("bnhgq2 loaded from:", os.path.dirname(bnhgq2.__file__))
    print("config loaded from :", CONFIG)
    print("config/hash        :", cfg["name"], h)
    print("device             :", tf.config.list_physical_devices("GPU") or "CPU")
    print("smoke training     :", "ENABLED" if RUN_SMOKE_TRAIN else "off")
    """),

    md("""
    ---
    ## Part 1 — the data

    The public HLS4ML LHC Jet dataset (Zenodo record 3602260). Each `.h5` holds 10,000
    jets. A *jet* is the spray of particles produced when a quark or gluon is knocked out
    of a proton collision; the task is to say what started it. Five classes: gluon, light
    quark, W boson, Z boson, top quark.

    Each jet arrives as a list of up to 150 constituent particles with 16 features each.
    `load_train_data` reduces that to what a trigger could actually receive, and three
    things happen inside it that all matter downstream:

    1. **sort by descending pT.** A particle list has no intrinsic order, so a canonical
       one is imposed — hardest particle first. Without this the model would have to
       learn to be permutation-invariant for free.
    2. **truncate to `n_part`.** The trigger has a fixed input budget. This config keeps 8.
    3. **select features, *after* the sort** — so the particle ordering is identical
       whichever features you choose. `["pt", "etarel", "phirel"]` is the L1-realistic
       set the field standardized on (Odagiu et al., arXiv:2402.01876): transverse
       momentum, and position relative to the jet axis.
    """),
    code("""
    X1, Y1, nfiles = bntrain.load_train_data(
        TRAIN_DIR, n_part=A["n_part"], max_files=DATA_FILES,
        features=A.get("features"))

    print(f"{nfiles} file -> X {X1.shape} {X1.dtype}, Y {Y1.shape}")
    print("   (jets, constituents, features)      (jets, classes) one-hot")
    print()
    print("classes:", dict(zip(bndata.CLASS_NICE, Y1.sum(0).astype(int))))
    print()
    print("jet 0 -- constituent features", A.get("features"), ":")
    print(np.round(X1[0], 4))
    print()
    print("this jet is a:", bndata.CLASS_NICE[int(Y1[0].argmax())])
    if A.get("features") and "pt" in A["features"]:
        pt_i = A["features"].index("pt")
        print("pT descending within every jet:",
              bool(np.all(np.diff(X1[:, :, pt_i], axis=1) <= 1e-6)))
    """),

    md("""
    Note the scales: pT is hundreds of GeV while `etarel`/`phirel` are hundredths. A
    network fed that raw would spend its early training just undoing the scale. `data.py`
    provides `input_std_stats` / `apply_input_std` for a per-feature z-score computed on
    the **train split only**, and the training run writes those statistics to
    `input_std.json` beside the checkpoint. Part 13 has to reuse them, and Part 14
    explains why the hardware does too.
    """),

    md("""
    ### Prepare the tiny workbench input

    The model expects standardized inputs when `arch.input_std` is enabled. For this
    scratch-only pass we estimate the statistics from the one loaded file. A real train
    computes them from its training partition and saves them with the checkpoint.
    """),
    code("""
    debug_mu = debug_sigma = None
    if A.get("input_std", False):
        debug_mu, debug_sigma = bndata.input_std_stats(X1)
        X_debug = bndata.apply_input_std(X1, debug_mu, debug_sigma)
    else:
        X_debug = X1

    X_debug = X_debug[:max(DEBUG_BATCH, CALIBRATION_JETS)]
    print("X_debug:", X_debug.shape, X_debug.dtype)
    print("finite :", bool(np.isfinite(X_debug).all()))
    print("range  :", float(X_debug.min()), "to", float(X_debug.max()))
    """),

    md("""
    ---
    ## Part 2 — the config *is* the experiment

    One JSON fully describes a model and its quantization. The pipeline reads
    architecture and precision from nowhere else, so an experiment is reproducible by
    quoting a filename. `cfg_hash` is an 8-hex fingerprint of the scientific content
    (private keys excluded) — same hash, same experiment.
    """),
    code("""
    print(cfg["name"], "| hash", h, "| era", cfg["era"])
    print()
    for k, note in [("n_part", "constituents kept"), ("n_feat", "features per constituent"),
                    ("d_model", "embedding width"), ("n_heads", "attention heads"),
                    ("n_layers", "transformer blocks"), ("ffn_dim", "feed-forward width"),
                    ("n_classes", "output classes"), ("pool", "how tokens are pooled"),
                    ("norm", "normalization (none = the norm-free variant)")]:
        print(f"  arch.{k:10s} {str(A[k]):8s}  {note}")
    print()
    for k, v in cfg["quant"].items():
        print(f"  quant.{k:22s} {v}")
    """),

    md("""
    `quant.weight = binary_absmean` is the thesis. `act_bits = 8` is how far the
    *activations* are quantized — the second axis of the study. The round-14 grid is this
    same architecture across both axes:
    """),
    code("""
    names = sorted(os.path.basename(p) for p in
                   glob.glob(os.path.join(CODE, "configs", "r14-*.json")))
    widths = sorted({n.split("-")[2] for n in names}, key=lambda s: int(s[1:]))
    precs  = sorted({n.split("-")[3].removesuffix(".json") for n in names})
    print("constituents :", widths)
    print("precisions   :", precs)
    print()
    print(f"{len(names)} configs = {len(widths)} widths x {len(precs)} precisions")
    print("w1 = binary weights (the thesis) | w8a8, fp32 = baselines | a8/a6/a4 = activation ladder")
    """),

    md("""
    ---
    ## Part 3 — the binarizer, on eight numbers you can check by hand

    `binarize.absmean_binarize` is the whole idea, and it is four lines of numpy
    (BitNet, arXiv:2310.11453):

    ```
    alpha = mean(W)          # centre the tensor
    Wc    = W - alpha
    beta  = mean(|Wc|)       # one scale for the whole tensor
    q     = sign(Wc)         # one bit per weight
    ```

    The stored weight is `q * beta`. `n_zero` **must** be 0: a weight of exactly zero
    would be a third state, and binary hardware has no third state, so the pipeline
    treats any zero as a stop condition rather than rounding it away.
    """),
    code("""
    W = np.array([[-0.9, 0.2, 0.5, -0.1],
                  [ 0.3, 0.8, -0.4, 0.05]], dtype=np.float32)
    q, beta, alpha, n_zero = absmean_binarize(W)

    print("W      =\\n", W)
    print()
    print("alpha  =", round(alpha, 6), "   mean(W)")
    print("beta   =", round(beta, 6), "   mean(|W - alpha|) + 1e-6")
    print("q      =\\n", q)
    print("n_zero =", n_zero, "  <- must be 0")
    print()
    print("effective weight q*beta =\\n", np.round(q * beta, 6))
    print("distinct values:", np.unique(np.round(q * beta, 10)))
    print()
    print("compression: 32 bits/weight ->", f"1 bit/weight + one {beta:.6f} per tensor")
    """),

    md("""
    ---
    ## Part 4 — what HGQ2 actually is

    HGQ2 (`import hgq`) is the quantization-aware-training library this project builds
    on. Its unit is the **quantizer config**: a description of a fixed-point grid, which
    gets attached to a layer's weights, its inputs, or its bias.

    A `QuantizerConfig` answers four questions:

    | field | means |
    | --- | --- |
    | `q_type` | how the grid is parametrized — `kif` (keep/integer/fractional bits) or `kbi` (keep/**b**its-total/integer) |
    | `place` | what it quantizes: `weight`, `datalane` (activations), `bias`, `table` |
    | `round_mode` | what happens between grid points — `RND`, `RND_CONV` (round-half-to-even) |
    | `overflow_mode` | what happens outside the range — `SAT` (clip), `SAT_SYM`, `WRAP` |

    `kif` vs `kbi` looks like a detail and is the hinge of two different experiments.
    `kif` carries integer bits `i` and fractional bits `f` independently, so the total
    width is whatever they add to. `kbi` carries a **total** width `b` and the integer
    split `i`, deriving `f = b - i`. If you want to pin a width at 4 bits and let the
    model slide the binary point around during training, you need `kbi` — you constrain
    `b` and leave `i` free. That is exactly `qat._trainable_act`.

    Here is a quantizer on its own, with no model around it:
    """),
    code("""
    import keras
    from hgq.quantizer import Quantizer, QuantizerConfig

    def grid_of(bits, i, x):
        \"\"\"Push x through a signed fixed<bits, 1+i> datalane grid and return it.\"\"\"
        c = QuantizerConfig("kif", "datalane", k0=1, i0=i, f0=bits - 1 - i,
                            round_mode="RND_CONV", overflow_mode="SAT",
                            trainable=False, heterogeneous_axis=())
        qz = Quantizer(c); qz.build(x.shape)
        return np.asarray(keras.ops.convert_to_numpy(qz(keras.ops.convert_to_tensor(x))))

    x = np.linspace(-3, 3, 2001, dtype="float32")
    grids = {}
    for bits, i in [(8, 2), (4, 2), (4, 0)]:
        y = grid_of(bits, i, x)
        u = np.unique(y)
        grids[(bits, i)] = (float(np.diff(u).min()), float(u.min()), float(u.max()))
        print(f"fixed<{bits},1+{i}>  f={bits - 1 - i}  levels={len(u):4d}  "
              f"step={grids[(bits, i)][0]:.5f}  "
              f"reaches [{u.min():+.3f}, {u.max():+.3f}]")

    print()
    print("The step is 2^-f and the reach is +/-2^i, so at a FIXED width the two trade:")
    for (bits, i), (step, lo, hi) in grids.items():
        print(f"  fixed<{bits},1+{i}>: step {step:g}, reach {hi:+g}")
    s8, s4 = grids[(8, 2)][0], grids[(4, 2)][0]
    print()
    print(f"Same i, half the bits: step went {s8:g} -> {s4:g} ({s4 / s8:.0f}x coarser).")
    r2, r0 = grids[(4, 2)][2], grids[(4, 0)][2]
    t2, t0 = grids[(4, 2)][0], grids[(4, 0)][0]
    print(f"Same width, i 2 -> 0: reach {r2:+g} -> {r0:+g}, but step {t2:g} -> {t0:g}.")
    print()
    print("(The 8-bit row saturates at the input's own +/-3, not at its 2^i=4 limit.)")
    print("Choosing i per tensor is what 'calibration' means -- see Part 9.")
    """),

    md("""
    ---
    ## Part 5 — why the stock quantizer cannot do binary

    The obvious way to get binary weights out of HGQ2 is to ask for a 1-bit weight
    quantizer: `kbi`, `b=1`, `i=1`, symmetric saturation. It does not work, and the
    reason is worth seeing rather than being told.

    A 1-bit *fixed-point* grid is not `{-1, +1}`. Fixed point is a uniform grid that
    **includes zero** — with one bit plus a sign you get `{-1, 0, +1}`. That is ternary.
    And since it rounds each latent weight to the nearest grid point, small weights do
    not become ±1: they become 0.

    The module docstring in `qat.py` records this as probe T1 — 4096 of 4096 latents went
    to zero. Reproduce it:
    """),
    code("""
    latents = np.random.default_rng(0).normal(0, 0.05, size=(64, 64)).astype("float32")

    kbi1 = QuantizerConfig("kbi", "weight", k0=1, b0=1, i0=1,
                           round_mode="RND", overflow_mode="SAT_SYM",
                           trainable=False, heterogeneous_axis=())
    qz = Quantizer(kbi1); qz.build(latents.shape)
    stock = np.asarray(keras.ops.convert_to_numpy(qz(keras.ops.convert_to_tensor(latents))))

    print("stock HGQ2 1-bit weight quantizer, on 4096 realistic latents")
    print("  distinct output values :", np.unique(stock))
    print("  exact zeros            :", int((stock == 0).sum()), "of", stock.size)
    print()
    print("  -> not binary. Every weight was annihilated.")
    print()
    print("the project's binarizer, same tensor:")
    q2, beta2, _, nz2 = absmean_binarize(latents)
    print("  distinct output values :", np.unique(np.round(q2 * beta2, 10)))
    print("  exact zeros            :", nz2)
    """),

    md("""
    This is why `qat.py` defines its own weight path instead of configuring one. The
    layers `BitQEinsumDense` / `BitQDense` subclass HGQ2's `QEinsumDense` / `QDense` and
    replace one line of `call()` — the kernel is binarized in the forward pass by
    `bitnet_binary_ste` instead of being passed through a fixed-point quantizer.

    The layers still carry a 1-bit `kq_conf` (`qat._binary_kq`). Not for arithmetic —
    purely so that EBOPs accounting and hls4ml *report* one bit for the weights, which
    they must, because one bit is what the hardware will store.
    """),

    md("""
    ---
    ## Part 6 — the straight-through estimator

    Binarizing in the forward pass creates a training problem: `sign` has zero gradient
    almost everywhere, so nothing upstream would ever learn. The straight-through
    estimator is the standard answer — use the binarized value going forward, but pretend
    the binarization was the identity going backward.

    In `qat.bitnet_binary_ste` that is the line `wq = ws + stop_gradient(q - ws)`. Forward
    it equals `q`; backward the `stop_gradient` term vanishes and the gradient flows
    through `ws` to the latent float weight, which is what actually gets updated. The
    binary weights are never stored during training — they are recomputed from the
    latents on every forward pass.

    Two deliberate departures from the QKeras reference are documented at `qat.py:43`: a
    strict bipolar sign so a tie goes to `+1` and never to `0`, and a bounded backward
    that removed a NaN observed at 4-bit activations.
    """),
    code("""
    lat = keras.ops.convert_to_tensor(latents)
    ste = np.asarray(keras.ops.convert_to_numpy(qat.bitnet_binary_ste(lat)))

    print("forward output of the STE:")
    print("  distinct values :", np.unique(np.round(ste, 8)))
    print("  matches the numpy binarizer:",
          bool(np.allclose(ste, q2 * beta2, atol=1e-7)))
    print()
    print("The training graph and the export path run the SAME arithmetic --")
    print("that is why the exported hardware model reproduces the trained one.")
    """),

    md("""
    ---
    ## Part 7 — the model

    `build_qat_model(cfg, seed)` returns `(model, taps)`. It is a small transformer
    encoder: project each constituent to `d_model`, add a learned positional encoding,
    run `n_layers` attention+FFN blocks, average over the constituents, classify.

    `taps` is the second return value and easy to overlook — it is a dict of
    *pre-quantization* tensors, one per activation site, kept so that Part 9 can measure
    the real distribution flowing into each quantizer.
    """),
    code("""
    model, taps = qat.build_qat_model(
        cfg, seed=SEED, input_mu=debug_mu, input_sigma=debug_sigma)

    print("total parameters    :", f"{model.count_params():,}")
    print("trainable parameters:", f"{sum(int(np.prod(v.shape)) for v in model.trainable_variables):,}")
    print("activation tap sites:", len(taps))
    print()
    kinds = {}
    for ly in model.layers:
        kinds[type(ly).__name__] = kinds.get(type(ly).__name__, 0) + 1
    for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"  {v:3d}  {k}")
    """),

    md("""
    The names are not decoration — `build.py` and `port.py` match layers by name when the
    trained model is re-emitted for hardware, so the graph below is also the export map.
    """),
    code("""
    for ly in model.layers[:14]:
        shp = tuple(ly.output.shape) if hasattr(ly, "output") else None
        star = " *" if type(ly).__name__.startswith("Bit") else "  "
        print(f"{star} {ly.name:28s} {type(ly).__name__:26s} {shp}")
    print("   ... block 1 repeats, then:")
    for ly in model.layers[-4:]:
        shp = tuple(ly.output.shape) if hasattr(ly, "output") else None
        star = " *" if type(ly).__name__.startswith("Bit") else "  "
        print(f"{star} {ly.name:28s} {type(ly).__name__:26s} {shp}")
    print()
    print("* = binary-weight layer")
    """),

    md("""
    Reading one block: `Wq`/`Wk` produce queries and keys, `scores` is their einsum,
    `softmax` normalizes it, `Wv` produces values, `ctx` mixes them, `Wo` projects back,
    and `add_attn` is the residual. Then `fc1 -> ReLU -> fc2` and a second residual. All
    six matmuls in the block are binary; the softmax and the two einsums are not — they
    have no weights.

    `arch.norm = "none"` in this config means the LayerNorms are identity passthroughs.
    That is the norm-free variant: no parameters, no DSPs, and (per `binarize.py`) it
    changes how every β must be handled at export, because there is no normalization
    downstream to absorb a scale.
    """),

    md("""
    ---
    ## Part 8 — step through one forward and backward pass

    This probe model returns the real intermediate tensors without modifying the model.
    Start here when a shape, range, NaN, softmax, or residual looks wrong. Add or remove
    a layer name in `PROBE_NAMES`; the full list is printed in Part 7.
    """),
    code("""
    PROBE_NAMES = [
        "input_proj", "pos_enc",
        "bit_block_0_attn_Wq", "bit_block_0_attn_Wk", "bit_block_0_attn_Wv",
        "bit_block_0_attn_scores", "bit_block_0_attn_softmax",
        "bit_block_0_attn_ctx", "bit_block_0_attn_Wo", "bit_block_0_add_attn",
        "bit_block_0_ffn_fc1", "bit_block_0_ffn_act",
        "bit_block_0_ffn_fc2", "bit_block_0_add_ffn",
        "gap", "head_fc1", "head_act", "head_fc2",
    ]
    PROBE_NAMES = [name for name in PROBE_NAMES
                   if any(layer.name == name for layer in model.layers)]
    probe = keras.Model(
        model.inputs,
        {name: model.get_layer(name).output for name in PROBE_NAMES},
        name="binary_transformer_probe")

    probe_out = probe([X_debug[:DEBUG_BATCH]], training=False)
    print(f"{'layer':32s} {'shape':18s} {'min':>11s} {'max':>11s} {'mean':>11s} {'finite':>7s}")
    print("-" * 96)
    for name, tensor in probe_out.items():
        arr = np.asarray(tensor)
        print(f"{name:32s} {str(arr.shape):18s} {arr.min():11.4g} {arr.max():11.4g} "
              f"{arr.mean():11.4g} {str(bool(np.isfinite(arr).all())):>7s}")
    """),

    md("""
    ### Check gradients without applying an optimizer step

    This catches a disconnected graph or exploding/NaN gradients while leaving every
    weight untouched. The variables are still the latent float weights; the forward pass
    sees their binary effective values through the STE. `training=False` avoids HGQ2's
    training-time EBOP-loss hook while the gradient tape still differentiates the graph.
    """),
    code("""
    xb = tf.convert_to_tensor(X_debug[:DEBUG_BATCH])
    yb = tf.convert_to_tensor(Y1[:DEBUG_BATCH])
    with tf.GradientTape() as tape:
        logits_debug = model(xb, training=False)
        loss_debug = tf.reduce_mean(keras.losses.categorical_crossentropy(
            yb, logits_debug, from_logits=True))
    grads = tape.gradient(loss_debug, model.trainable_variables)

    none_count = sum(g is None for g in grads)
    bad_count = 0
    rows = []
    for variable, grad in zip(model.trainable_variables, grads):
        if grad is None:
            continue
        grad_arr = np.asarray(tf.convert_to_tensor(grad))
        finite = bool(np.isfinite(grad_arr).all())
        bad_count += not finite
        rows.append((getattr(variable, "path", variable.name), variable.shape,
                     float(np.linalg.norm(grad_arr)), finite))

    print("loss:", float(loss_debug.numpy()))
    print("variables:", len(grads), "| disconnected:", none_count,
          "| non-finite gradients:", bad_count)
    for name, shape, norm, finite in rows[:12]:
        print(f"  {name:48s} {str(tuple(shape)):16s} norm={norm:10.3g} finite={finite}")
    assert bad_count == 0, "non-finite gradient found"
    """),

    md("""
    ---
    ## Part 9 — activation quantization and calibration

    Weights are only half of it. Every tensor flowing between layers also has to land on
    a fixed-point grid, and each site needs its own integer/fractional split: attention
    scores, ReLU outputs and pooled embeddings do not share a range.

    `calibrate_activations` picks that split from data. For each tap it tries every legal
    integer-bit count and keeps the one with the lowest mean-squared error against the
    unquantized tensor. The docstring records why MSE rather than max-plus-margin: at 4
    bits, range-based calibration leaves zero fractional bits — an integer-only grid that
    flattens the signal.
    """),
    code("""
    before = qat.act_grid_params(model)
    site_i = qat.calibrate_activations(
        model, taps, X_debug[:CALIBRATION_JETS], int(cfg["quant"]["act_bits"]))
    after = qat.act_grid_params(model)

    ab = int(cfg["quant"]["act_bits"])
    print(f"calibrated {len(site_i)} sites at {ab} bits (i = integer bits, f = {ab}-1-i)\\n")
    print(f"  {'site':30s} {'i before':>9s} {'i after':>8s}")
    moved = 0
    for k in list(site_i)[:8]:
        b_i = before.get(k, ("-", "-"))[0]
        a_i = after.get(k, ("-", "-"))[0]
        moved += (b_i != a_i)
        print(f"  {k:30s} {str(b_i):>9s} {str(a_i):>8s}")
    print("  ...")
    print()
    print("distinct integer-bit choices across all sites:", sorted(set(site_i.values())))
    print("-> the sites genuinely disagree; one global grid would be wrong for most of them.")
    """),

    md("""
    `act_calib` in the config decides what happens next. `frozen` keeps this grid for the
    whole run. `trainable` (used here) pins the *width* with a constraint and lets the
    integer split keep training, so the grid follows the activations as they drift — the
    rescue for 4-bit, where a first-batch grid was measured to stall. `free` lets the
    width itself train under an EBOPs penalty, which is a different experiment entirely.
    """),

    md("""
    ---
    ## Part 10 — the gate that enforces the claim

    A model is only binary if its effective forward weights really are two values,
    symmetric about zero, with nothing between. `effective_weight_values` runs the
    binarizer over every bit-layer and reports what it finds; `train.py` asserts on this
    before a single epoch runs. If it ever failed the headline claim would be void, so it
    is checked rather than assumed.
    """),
    code("""
    effs = qat.effective_weight_values(model)
    assert effs, ("the selected config has no binary layers; choose a "
                  "binary_absmean config for this workbench")
    print(f"{len(effs)} binary layers\\n")
    for name, vals in list(effs.items())[:5]:
        print(f"  {name:28s} {np.round(vals, 6)}   beta = {vals[1]:.6f}")
    print("  ...")
    print()
    two_valued = all(len(v) == 2 for v in effs.values())
    symmetric  = all(len(v) == 2 and abs(v[0] + v[1]) < 1e-12 for v in effs.values())
    no_zero    = all(not (v == 0).any() for v in effs.values())
    print("exactly two values per layer :", two_valued)
    print("symmetric about zero         :", symmetric)
    print("no zero state                :", no_zero)
    assert two_valued and symmetric and no_zero, "BINARY GATE FAILED"
    print("\\nbinary gate OK -- every layer is {-beta, +beta}")
    print("note each layer has its OWN beta: one float per tensor, not one for the model.")
    """),

    md("""
    ---
    ## Part 11 — resource usage

    These first numbers are architecture accounting, so they are stable across machines.
    A MAC is one multiply-accumulate. Binary-weight MACs can become sign/select-and-add
    logic in hardware; activation-by-activation MACs in attention cannot. The packed
    payload estimate is storage only, not a BRAM prediction: synthesis may partition,
    duplicate, stream, or optimize arrays.
    """),
    code("""
    from math import ceil

    T = int(A["n_part"]); F = int(A["n_feat"]); D = int(A["d_model"])
    H = int(A["n_heads"]); L = int(A["n_layers"])
    FFN = int(A["ffn_dim"]); C = int(A["n_classes"])

    bit_layers = [layer for layer in model.layers
                  if isinstance(layer, (qat.BitQEinsumDense, qat.BitQDense))]
    binary_params = sum(int(np.prod(layer._kernel.shape)) for layer in bit_layers)
    total_params = int(model.count_params())
    other_params = total_params - binary_params
    latent_bytes = sum(int(np.prod(v.shape)) * np.dtype(str(v.dtype)).itemsize
                       for v in model.weights)
    packed_binary_bytes = ceil(binary_params / 8) + 4 * len(bit_layers)
    rough_deployed_bytes = packed_binary_bytes + 4 * other_params

    input_proj_macs = T * F * D
    block_weight_macs = L * (4 * T * D * D + 2 * T * D * FFN)
    attention_data_macs = L * (2 * T * T * D)
    head_macs = D * D + D * C
    weighted_macs = input_proj_macs + block_weight_macs + head_macs
    total_macs = weighted_macs + attention_data_macs

    print("model parameters            :", f"{total_params:,}")
    print("binary kernel parameters    :", f"{binary_params:,}",
          f"across {len(bit_layers)} layers")
    print("latent model weight storage :", f"{latent_bytes / 1024:.1f} KiB")
    print("packed binary kernels + beta:", f"{packed_binary_bytes / 1024:.1f} KiB")
    print("rough full weight payload   :", f"{rough_deployed_bytes / 1024:.1f} KiB")
    print()
    print("MACs per jet")
    print("  input projection          :", f"{input_proj_macs:,}")
    print("  binary-weight blocks      :", f"{block_weight_macs:,}")
    print("  attention act x act       :", f"{attention_data_macs:,}")
    print("  classifier head           :", f"{head_macs:,}")
    print("  total                     :", f"{total_macs:,}")
    if A.get("pair_bias"):
        print("WARNING: pair_bias is enabled; its MACs are not included in this compact estimate.")

    # Largest inspected live tensor for one jet. This is a useful software/debugging
    # bound, not an FPGA memory schedule; HLS can stream and reuse these buffers.
    per_jet_values = {name: int(np.asarray(tensor).size // np.asarray(tensor).shape[0])
                      for name, tensor in probe_out.items()}
    peak_name = max(per_jet_values, key=per_jet_values.get)
    peak_values = per_jet_values[peak_name]
    print()
    print("largest probed activation   :", peak_name, f"({peak_values:,} values/jet)")
    print(f"at {int(cfg['quant']['act_bits'])} bits/value       :",
          f"{ceil(peak_values * int(cfg['quant']['act_bits']) / 8) / 1024:.2f} KiB/jet")
    """),

    md("""
    ### HGQ2 EBOP estimate

    This runs HGQ2's own graph/quantizer accounting. It is more faithful to the mixed
    precision graph than raw MACs, but it is still an operation-cost metric, not the
    LUT/FF/DSP/BRAM report from Vitis.
    """),
    code("""
    if RUN_EBOPS:
        from bnhgq2.ebops_calc import compute_ebops

        # HGQ2 0.1.9 reads EinsumDense.full_output_shape while computing bias
        # EBOPs. Keras 3.15 no longer leaves that compatibility attribute behind.
        # Restore only the missing shape metadata; this does not change arithmetic.
        repaired = []
        for layer in model.layers:
            if hasattr(layer, "equation") and not hasattr(layer, "full_output_shape"):
                layer.full_output_shape = tuple(layer.output.shape)
                repaired.append(layer.name)
        if repaired:
            print("HGQ2/Keras shape compatibility applied to", len(repaired), "layers")

        ebops = compute_ebops(
            model, X_debug[:CALIBRATION_JETS],
            batch_size=min(2048, len(X_debug)))
        print("HGQ2 total EBOPs:", f"{ebops['total']:,}")
        print("largest layer contributions:")
        for name, value in sorted(
                ebops["per_layer"].items(), key=lambda item: -item[1])[:12]:
            print(f"  {name:38s} {value:14,d}")
    else:
        print("Skipped. Set RUN_EBOPS = True in Part 0 and rerun this cell.")
    """),

    md("""
    ### Runtime and process/device memory

    This measures this exact kernel after one warm-up call. It includes TensorFlow
    runtime behavior and is useful for comparing code changes on the same machine. It
    says nothing about FPGA cycle latency.
    """),
    code("""
    bench_x = tf.convert_to_tensor(X_debug[:DEBUG_BATCH])
    bench_batch = int(bench_x.shape[0])
    _ = float(tf.reduce_sum(model(bench_x, training=False)).numpy())  # trace + synchronize

    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        try:
            tf.config.experimental.reset_memory_stats("GPU:0")
        except Exception as exc:
            print("GPU memory reset unavailable:", exc)

    t0 = time.perf_counter()
    for _ in range(BENCHMARK_STEPS):
        bench_y = model(bench_x, training=False)
        _ = float(tf.reduce_sum(bench_y).numpy())       # force completion each step
    elapsed = time.perf_counter() - t0

    current_rss_mb = None
    try:
        import psutil
        current_rss_mb = psutil.Process().memory_info().rss / 1024 ** 2
    except ImportError:
        pass
    raw_peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_rss_mb = raw_peak_rss / (1024 ** 2 if platform.system() == "Darwin" else 1024)

    print("batch / steps        :", bench_batch, "/", BENCHMARK_STEPS)
    print("mean batch latency   :", f"{elapsed / BENCHMARK_STEPS * 1e3:.3f} ms")
    print("mean latency per jet :", f"{elapsed / BENCHMARK_STEPS / bench_batch * 1e6:.3f} us")
    print("throughput           :", f"{BENCHMARK_STEPS * bench_batch / elapsed:,.1f} jets/s")
    if current_rss_mb is not None:
        print("current process RSS  :", f"{current_rss_mb:,.1f} MiB")
    print("process peak RSS     :", f"{peak_rss_mb:,.1f} MiB (kernel lifetime)")
    if gpus:
        try:
            gpu_mem = tf.config.experimental.get_memory_info("GPU:0")
            print("GPU current / peak   :",
                  f"{gpu_mem['current'] / 1024 ** 2:.1f} / {gpu_mem['peak'] / 1024 ** 2:.1f} MiB")
        except Exception as exc:
            print("GPU memory counters unavailable:", exc)
    """),

    md("""
    ---
    ## Part 12 — optional smoke train

    `smoke=True` is the project's small-sample switch: 3 epochs over 2 files, no warmup.
    It runs the *same* code path as a real job rather than a separate reduced one — a
    shortcut that skips code cannot tell you the code works.

    `train` builds its own model internally (the one above is only for inspection), runs the
    calibration pass, asserts the binary gate, trains, and writes `model_best.keras`,
    `train_meta.json` and `input_std.json`.
    """),
    code("""
    OUT = os.path.join(os.environ["BNHGQ2_OUT_ROOT"], "workbench-" + cfg["name"])
    if RUN_SMOKE_TRAIN:
        t0 = time.time()
        meta = bntrain.train(cfg, seed=SEED, out_dir=OUT, smoke=True, cfg_hash=h)
        print(f"\\nwall clock: {time.time() - t0:.0f} s")
    else:
        print("Skipped. Set RUN_SMOKE_TRAIN = True in Part 0, restart, and run all.")
    """),

    md("""
    ---
    ## Part 13 — score the optional smoke model on unseen data

    Trained on the train split, evaluated on `data/val`. Two things are easy to get wrong
    and both silently ruin the number:

    - the model was trained on **standardized** inputs, so val must be standardized with
      the *same* mu/sigma — which is why the run wrote them to `input_std.json`;
    - loading the checkpoint needs `bnhgq2.qat` **imported** first, or Keras cannot find
      `BitQEinsumDense`. Importing the package is not enough: the
      `@register_keras_serializable` decorators live in the module, and `__init__.py`
      does not import it.
    """),
    code("""
    scores = None
    if RUN_SMOKE_TRAIN:
        VAL_DIR = os.path.join(bncfg.PROJECT_ROOT, "data", "val")
        assert os.path.isdir(VAL_DIR), f"no val split at {VAL_DIR}"

        Xv, Yv, nv = bntrain.load_train_data(
            VAL_DIR, n_part=A["n_part"], max_files=3, features=A.get("features"))

        std_path = os.path.join(OUT, "input_std.json")
        if A.get("input_std", False):
            std = json.load(open(std_path))
            Xv = bndata.apply_input_std(Xv, np.array(std["mu"], "float32"),
                                        np.array(std["sigma"], "float32"))
        print(f"val: {nv} files, {len(Xv)} jets, never seen in training")

        best = keras.saving.load_model(os.path.join(OUT, "model_best.keras"))
        logits = np.concatenate([np.asarray(best(Xv[i:i + 4096], training=False))
                                 for i in range(0, len(Xv), 4096)])
        scores = softmax64(logits).astype("float32")

        auc, per_class = macro_ovr_auc(Yv, scores)
        print(f"\\nmacro-OvR AUC {auc:.4f}")
        for c, a in zip(bndata.CLASS_NICE, per_class):
            print(f"  {c}  {a:.4f}")
        print("\\n*** A three-epoch smoke metric, not a result. ***")
    else:
        print("Skipped because RUN_SMOKE_TRAIN is False.")
    """),

    md("""
    Read the per-class column, not just the average. A class scoring *below* 0.5 is not
    simply "undertrained" — undertraining pulls a score toward 0.5, not past it. Below
    chance means the model learned that class **backwards**: anti-correlated, systematically
    confusing it with something else.

    Expect to see that for `q`, with `g` scoring highest. Light-quark and gluon jets are
    the notoriously hard pair — they differ only in subtle radiation patterns — and three
    epochs is enough to latch onto the q/g axis while still having its sign wrong. A good
    illustration of why a macro average can hide what a model is doing.
    """),

    md("""
    ### the ROC, drawn the way the field draws it

    Signal efficiency against background rejection `1/mistag`, log vertical axis. The log
    axis is not decoration: a trigger operates at a mistag rate of `1e-3` or below, so the
    part of the curve anyone cares about is crushed into the left edge of a linear plot.
    """),
    code("""
    import matplotlib.pyplot as plt
    from sklearn.metrics import roc_curve

    if scores is None:
        print("Skipped because RUN_SMOKE_TRAIN is False.")
    else:
        fig, ax = plt.subplots(figsize=(5.4, 4.3), dpi=120)
        for c, nice in enumerate(bndata.CLASS_NICE):
            fpr, tpr, _ = roc_curve(Yv[:, c], scores[:, c])
            keep = fpr > 0
            ax.plot(tpr[keep], 1.0 / fpr[keep], lw=1.4,
                    label=f"{nice}  AUC {per_class[c]:.3f}")

        ax.set_yscale("log")
        ax.set_xlabel("signal efficiency")
        ax.set_ylabel("background rejection  1/mistag")
        ax.set_title(f"{cfg['name']} · {h} · smoke (3 epochs)\\nNOT A RESULT",
                     fontsize=8)
        ax.grid(alpha=0.3, which="both", lw=0.4)
        ax.legend(fontsize=7, loc="upper right")
        fig.tight_layout()
        plt.show()
    """),

    md("""
    ---
    ## Part 14 — where software profiling stops

    `run_stage.py` runs the pipeline as stages. This notebook has walked the first one.

    ```
    train  ->  extract  ->  calibrate  ->  build  ->  verify  ->  ebops  ->  convert
    ```

    - **extract** reads the trained latent kernels out by layer name.
    - **calibrate** fixes the final static activation grids.
    - **build** (`build.py`) re-emits the model as a static hardware graph: the latents
      are re-binarized with the *same* `absmean_binarize` from Part 3, and each β is
      disposed of according to the fold table in `binarize.py` — folded into a bias,
      into the attention score scale, absorbed by a downstream LayerNorm, or kept as an
      explicit affine when it reaches a residual or the logits.
    - **verify** (`verify.py`) runs three fidelity gates: the rebuilt model against the
      stored reference scores, the Keras forward against an independent numpy
      implementation in `gold.py` (same math, so any disagreement is a build bug), and
      the hls4ml C-simulation against Keras — which is required to be **bit-exact**,
      `max |delta| == 0`.
    - **ebops** estimates the bit-operation cost.
    - **convert** (`convert.py`) emits HLS, and C-synthesis runs on `mulder`
      (Vitis 2023.2, VU13P) to produce the LUT/FF/DSP/BRAM and latency tables — the
      numbers that carry the "0 DSP in the binary core" claim.

    **None of that runs on a laptop, and nothing above is quotable.** This is a scratch
    environment, drifted from the cluster's on at least one pin. Every number that reaches
    `RESEARCH.md` or a report comes from a cluster Job and is recomputed from the stored
    `.npz` arrays through the `verify-roc` skill. What this notebook is for is
    understanding the code, and checking that it still runs.
    """),
]


# --------------------------------------------------------------------------- #
nb03 = [
    md("""
    # 03 — `einsum` vs `tf.matmul`
    """),
    md("""
    ## 1 — vectors
    """),
    md("""
    ### Create small random query, key, and value matrices
    """),
    code("""
    # start with random tensors so the attention math is easy to inspect.
    import numpy as np
    import tensorflow as tf

    T, S, E = 4, 4, 3                       # queries, keys, per-head width
    # use a fixed seed so both implementations receive exactly the same inputs.
    rng = np.random.default_rng(0)
    r = lambda *s: tf.constant(rng.standard_normal(s), dtype=tf.float32)

    Q, K, V = r(T, E), r(S, E), r(S, E)
    # Q and K are compared to make scores; V is combined after softmax.
    print("Q", tuple(Q.shape), " K", tuple(K.shape), " V", tuple(V.shape))
    """),
    md("""
    ### Compute attention logits two equivalent ways

    Compare matrix multiplication with an explicit `einsum` dot product.
    """),
    code("""
    # calculate the same query-key scores in two different ways.
    # matrix multiplication computes all pairwise dot products at once.
    # einsum writes the shared embedding dimension explicitly.
    logits_mm = tf.matmul(Q, K, transpose_b=True)          # (T,E) x (E,S)
    logits_es = tf.einsum("te,se->ts", Q, K)

    np.testing.assert_allclose(logits_mm, logits_es, rtol=1e-5, atol=1e-6)
    print("logits", tuple(logits_mm.shape),
          " max|diff|", float(np.max(np.abs(logits_mm - logits_es))))
    """),
    md("""
    ### Convert logits to attention weights and compute context

    Scale the scores, apply softmax, and combine the value vectors.
    """),
    code("""
    # turn the scores into attention weights, then use them to mix the values.
    # softmax makes each row sum to one, so the result is a weighted average.
    a_mm = tf.nn.softmax(logits_mm / np.sqrt(E), axis=-1)
    a_es = tf.nn.softmax(logits_es / np.sqrt(E), axis=-1)

    ctx_mm = tf.matmul(a_mm, V)                            # (T,S) x (S,E)
    ctx_es = tf.einsum("ts,se->te", a_es, V)

    np.testing.assert_allclose(ctx_mm, ctx_es, rtol=1e-5, atol=1e-6)
    print("context", tuple(ctx_mm.shape),
          " max|diff|", float(np.max(np.abs(ctx_mm - ctx_es))))
    """),
    md("""
    ### Count MACs and estimated FLOPs for the toy example
    """),
    code("""
    def einsum_macs(equation, *shapes, batch_axis=""):
        # count one multiply-accumulate for each combination of indices.
        lhs, out = equation.split("->")
        dims = {}
        for spec, shape in zip(lhs.split(","), shapes):
            assert len(spec) == len(shape), f"{spec} vs {tuple(shape)}"
            for ch, n in zip(spec, shape):
                assert dims.setdefault(ch, int(n)) == int(n), f"index '{ch}' mismatch"
        macs = 1
        for ch in (set(lhs) - {","}) | set(out):
            if ch != batch_axis:
                macs *= dims[ch]
        return macs

    # check the einsum count against the matrix-multiplication count by hand.
    for name, eq, shapes, by_hand in [
        ("QK^T",   "te,se->ts", [(T, E), (S, E)], T * E * S),
        ("attn.V", "ts,se->te", [(T, S), (S, E)], T * S * E),
    ]:
        m = einsum_macs(eq, *shapes)
        assert m == by_hand, f"{name}: einsum {m} != matmul {by_hand}"
        print(f"{name:7s} {eq:12s} einsum {m:5d}  matmul {by_hand:5d}  FLOPs {2 * m:5d}")
    """),
    md("""
    ## 2 — the same checks at `qat.py` shapes
    """),
    md("""
    ### Load the model architecture dimensions
    """),
    code("""
    import os
    from keras.layers import Dense, EinsumDense

    CODE = os.environ["PYTHONPATH"]
    from bnhgq2 import config as bncfg
    from bnhgq2.qat import bitnet_binary_ste

    # load the architecture so the test uses the same dimensions as qat.py.
    cfg = bncfg.load_config(os.path.join(CODE, "configs", "r14-l1x3-n8-w1a8.json"))
    A = cfg["arch"]

    # keep the batch size small while preserving the model's real tensor shapes.
    B   = 4
    T   = int(A["n_part"])
    F   = int(A["n_feat"])
    D   = int(A["d_model"])
    H   = int(A["n_heads"])
    E   = D // H
    FFN = int(A["ffn_dim"])
    assert H * E == D

    print(cfg["name"], "-> T", T, "| F", F, "| D", D, "| H", H, "| E", E, "| FFN", FFN)
    """),
    md("""
    ### Create random inputs, weights, and an equality-check helper
    """),
    code("""
    # generate reproducible float32 test tensors from the shared random generator.
    def rand(*shape):
        return tf.constant(rng.standard_normal(shape), dtype=tf.float32)

    # compare two implementations and report the largest numerical difference.
    def same(name, a, b):
        a, b = np.asarray(a), np.asarray(b)
        assert a.shape == b.shape, f"{name}: {a.shape} vs {b.shape}"
        np.testing.assert_allclose(a, b, rtol=1e-5, atol=1e-6)
        print(f"  OK  {name:22s} {str(tuple(a.shape)):18s}"
              f" max|diff| {float(np.max(np.abs(a - b))):.3e}")

    # x is the input sequence; the four weight tensors are used by attention.
    x  = rand(B, T, D)
    Wq = rand(D, H, E)
    Wk = rand(D, H, E)
    Wv = rand(D, H, E)
    Wo = rand(H, E, D)
    """),
    md("""
    ### Project the input into queries, keys, and values

    Verify `einsum` and reshaped matrix multiplication produce identical Q, K, and V tensors.
    """),
    code("""
    # project each token into queries, keys, and values for every head.
    # the shared d index is summed over during each projection.
    q_e = tf.einsum("btd,dhe->bthe", x, Wq)
    k_e = tf.einsum("btd,dhe->bthe", x, Wk)
    v_e = tf.einsum("btd,dhe->bthe", x, Wv)

    def proj_matmul(x, W):
        Dw, Hw, Ew = W.shape
        # flatten the head dimensions so a regular matmul can do the projection.
        flat = tf.matmul(x, tf.reshape(W, (Dw, Hw * Ew)))      # (B,T,D) x (D,H*E)
        # put the head dimensions back after the matmul.
        return tf.reshape(flat, (-1, x.shape[1], Hw, Ew))      # -> (B,T,H,E)

    q_m, k_m, v_m = proj_matmul(x, Wq), proj_matmul(x, Wk), proj_matmul(x, Wv)
    same("Q", q_e, q_m)
    same("K", k_e, k_m)
    same("V", v_e, v_m)
    """),
    md("""
    ### Compute attention scores and softmax weights

    Transpose the head and sequence dimensions for batched matrix multiplication, then compare it with `einsum`.
    """),
    code("""
    # compare every query with every key to get the attention logits.
    # each score is a dot product over the per-head embedding dimension.
    scores_e = tf.einsum("bthe,bshe->bhts", q_e, k_e)

    qh = tf.transpose(q_m, [0, 2, 1, 3])                       # (B,T,H,E) -> (B,H,T,E)
    kh = tf.transpose(k_m, [0, 2, 1, 3])
    scores_m = tf.matmul(qh, kh, transpose_b=True)             # -> (B,H,T,S)
    same("QK^T", scores_e, scores_m)

    # scale before softmax so the scores stay well behaved as E grows.
    scale  = 1.0 / np.sqrt(E)
    attn_e = tf.nn.softmax(scores_e * scale, axis=-1)
    attn_m = tf.nn.softmax(scores_m * scale, axis=-1)
    same("softmax(QK^T/sqrt E)", attn_e, attn_m)
    """),
    md("""
    ### Compute context and project the heads back to model width

    Combine values using the attention weights, then apply the output projection `W_o`.
    """),
    code("""
    # use the attention weights to make a weighted combination of the values.
    # transpose the values so their dimensions line up with the batched matmul.
    ctx_e = tf.einsum("bhts,bshe->bthe", attn_e, v_e)

    vh    = tf.transpose(v_m, [0, 2, 1, 3])                    # (B,S,H,E) -> (B,H,S,E)
    ctx_m = tf.transpose(tf.matmul(attn_m, vh), [0, 2, 1, 3])  # (B,H,T,E) -> (B,T,H,E)
    same("attn . V", ctx_e, ctx_m)

    # combine the heads back into the original model dimension.
    out_e = tf.einsum("bthe,hed->btd", ctx_e, Wo)
    out_m = tf.matmul(tf.reshape(ctx_m, (-1, T, H * E)), tf.reshape(Wo, (H * E, D)))
    same("W_o", out_e, out_m)
    """),
    md("""
    ### Repeat the projection check with a binary weight kernel
    """),
    code("""
    # repeat the projection check after replacing the weights with binary values.
    # the binary kernel should contain only the intended {-1, +1} values.
    Wq_b = bitnet_binary_ste(Wq)
    print("distinct Wq values:", np.unique(np.round(np.asarray(Wq_b), 8)))
    same("Q (binary W)", tf.einsum("btd,dhe->bthe", x, Wq_b), proj_matmul(x, Wq_b))
    """),
    md("""
    ## 3 — parameter counts
    """),
    md("""
    `EinsumDense` vs `Dense`: this section checks how many stored weights each layer
    creates.
    """),
    code("""
    # EinsumDense vs Dense, identical weights
    ein = EinsumDense("btd,dhe->bthe", output_shape=(T, H, E), bias_axes=None)
    ein.build((None, T, D))
    ein.set_weights([np.asarray(Wq)])

    den = Dense(H * E, use_bias=False)
    den.build((None, T, D))
    den.set_weights([np.asarray(tf.reshape(Wq, (D, H * E)))])

    same("layer output", ein(x), tf.reshape(den(x), (-1, T, H, E)))
    print("  EinsumDense kernel", tuple(ein.kernel.shape),
          "->", int(np.prod(ein.kernel.shape)), "params")
    print("  Dense       kernel", tuple(den.kernel.shape),
          "->", int(np.prod(den.kernel.shape)), "params")
    """),
    code("""
    def ed_params(equation, output_shape, input_shape, bias_axes=None):
        lyr = EinsumDense(equation, output_shape=output_shape, bias_axes=bias_axes)
        lyr.build(input_shape)
        k = int(np.prod(lyr.kernel.shape))
        b = int(np.prod(lyr.bias.shape)) if lyr.bias is not None else 0
        bs = tuple(lyr.bias.shape) if lyr.bias is not None else None
        return tuple(lyr.kernel.shape), k, bs, b

    # Same output shape, same MACs, different parameter count. This is the failure mode:
    # EinsumDense sizes its kernel from the WEIGHT subscript, so a stray 't' costs T x.
    for label, eq, bax in [
        ("correct",          "btd,dhe->bthe",  None),
        ("t in weight spec", "btd,tdhe->bthe", None),
        ("t in bias spec",   "btd,dhe->bthe",  "the"),
    ]:
        ks, k, bs, b = ed_params(eq, (T, H, E), (None, T, D), bax)
        print(f"  {label:18s} {eq:16s} kernel {str(ks):16s}"
              f" bias {str(bs):12s} total {k + b:6d}")

    base = ed_params("btd,dhe->bthe", (T, H, E), (None, T, D))[1]
    bad  = ed_params("btd,tdhe->bthe", (T, H, E), (None, T, D))[1]
    print(f"  wrong weight spec costs {bad // base}x the weights ({base} -> {bad})")
    """),
    code("""
    # the built model, not standalone layers
    from bnhgq2 import qat

    model, taps = qat.build_qat_model(cfg, seed=1)

    hdr = f"{'layer':30s} {'equation':16s} {'kernel':14s} {'K':>6s} {'bias':>10s} {'B':>5s}"
    print(hdr)
    print("-" * len(hdr))
    for lyr in model.layers:
        k = getattr(lyr, "_kernel", None)
        if k is None:
            continue
        b  = getattr(lyr, "bias", None)
        nb = int(np.prod(b.shape)) if b is not None else 0
        print(f"{lyr.name:30s} {getattr(lyr, 'equation', 'matmul (QDense)'):16s}"
              f" {str(tuple(k.shape)):14s} {int(np.prod(k.shape)):6d}"
              f" {str(tuple(b.shape)) if b is not None else '-':>10s} {nb:5d}")
    """),
    code("""
    wq = model.get_layer("bit_block_0_attn_Wq")
    print("class    :", type(wq).__name__)
    print("equation :", wq.equation)
    print("kernel   :", tuple(wq._kernel.shape), " expected", (D, H, E))
    print("bias     :", wq.bias)
    assert tuple(wq._kernel.shape) == (D, H, E), "Wq kernel is not (D,H,E)!"
    assert wq.bias is None, "Wq grew a bias"
    print(f"=> {D * H * E} weights per projection, not {T * D * H * E}")
    """),
    md("""
    ## 4 — MACs / FLOPs at `qat.py` shapes
    """),
    code("""
    ROWS = [
        ("Wq projection", "btd,dhe->bthe",   [(B,T,D), (D,H,E)],     T*D*H*E, "(T x D) x (D x HE)",      "weighted"),
        ("Wk projection", "btd,dhe->bthe",   [(B,T,D), (D,H,E)],     T*D*H*E, "(T x D) x (D x HE)",      "weighted"),
        ("Wv projection", "btd,dhe->bthe",   [(B,T,D), (D,H,E)],     T*D*H*E, "(T x D) x (D x HE)",      "weighted"),
        ("QK^T logits",   "bthe,bshe->bhts", [(B,T,H,E), (B,T,H,E)], H*T*T*E, "H x [(T x E) x (E x S)]", "act x act"),
        ("attn . V",      "bhts,bshe->bthe", [(B,H,T,T), (B,T,H,E)], H*T*T*E, "H x [(T x S) x (S x E)]", "act x act"),
        ("Wo projection", "bthe,hed->btd",   [(B,T,H,E), (H,E,D)],   T*H*E*D, "(T x HE) x (HE x D)",     "weighted"),
    ]

    hdr = f"{'op':14s} {'equation':18s} {'einsum':>9s} {'matmul':>9s}  {'matmul spelling':26s} kind"
    print(hdr)
    print("-" * len(hdr))
    tot = wgt = act = 0
    for name, eq, shapes, by_hand, form, kind in ROWS:
        m = einsum_macs(eq, *shapes, batch_axis="b")
        assert m == by_hand, f"{name}: einsum {m} != matmul {by_hand}"
        tot += m
        wgt += m if kind == "weighted" else 0
        act += m if kind != "weighted" else 0
        print(f"{name:14s} {eq:18s} {m:9,d} {by_hand:9,d}  {form:26s} {kind}")
    print("-" * len(hdr))
    print(f"  attention block: {tot:,} MACs/jet = {2 * tot:,} FLOPs/jet")
    print(f"  weighted contractions   : {wgt:6,d} MACs/jet  <- binary kernels")
    print(f"  activation x activation : {act:6,d} MACs/jet  <- no stored weights")
    """),
]


# --------------------------------------------------------------------------- #
# 04 — conference figures before EBOPs-target enforcement                     #
# --------------------------------------------------------------------------- #
nb04 = [
    md("""
    # Conference visual bundle — fixed-precision Round 14

    This notebook rebuilds the project-owned diagrams and plots used for the
    FastML conference material, plus the per-class ROC overlays kept as backup
    figures. It is deliberately a **historical, pre-target-enforcement view**.

    The scope boundary is concrete:

    - included: the fixed-precision Round-14 `r14` ROC arrays and EBOPs table,
      the stored N=8 synthesis reports, and the architecture TikZ source;
    - excluded: `ebops-n8-20260910/`, `ebops-n8-costfirst-20260910/`,
      `ebops-n8-long-20260911/`, `ebops-n8-ablation-20260912/`, and every
      checkpoint produced by an enforced EBOPs target;
    - no training or synthesis runs here: every number is recomputed from a
      stored `.npz`, JSON, or raw synthesis report.

    The notebook writes a fresh bundle under `BNHGQ2_OUT_ROOT` (or the path in
    `BNJETTAG_CONFERENCE_OUT`) and never overwrites the frozen conference files.
    Each plot is saved as PNG and PDF; the architecture remains TikZ + SVG.
    """),

    md("""
    ## Visual inventory

    | visual | status in this notebook | source of record |
    | --- | --- | --- |
    | BNJetTag architecture | rendered from project TikZ when `tectonic` is available; otherwise the verified SVG is bundled with its TikZ source | `docs/figures/bnjettag-architecture.tex` |
    | AUC vs constituent count | regenerated | 60 Round-14 ROC `.npz` arrays |
    | AUC vs EBOPs | regenerated | the same ROC arrays + `ebops_r14.json` |
    | per-class ROC overlays, N=8/16/32/64 | regenerated | the same ROC arrays, seed 1 |
    | LUT attribution | regenerated | raw HLS instance report + Vivado utilization report |
    | BitNet explainer | copied and credited, not redrawn | Wang et al., arXiv:2310.11453, Fig. 2 |
    | CMS trigger flow | copied and credited, not redrawn | M. Pierini conference figure |

    The last two are externally sourced context figures. Calling a file copy a
    generated result would erase that distinction, so the manifest records them
    as `reference-only` assets.
    """),

    md("## 1 — setup, output directory, and the era firewall"),
    code("""
    from pathlib import Path
    from datetime import datetime, timezone
    import csv, hashlib, importlib, json, os, re, shutil, subprocess, sys, tempfile

    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    from IPython.display import Image, SVG, display
    from sklearn.metrics import roc_auc_score, roc_curve

    def find_research_root():
        candidates = []
        if os.environ.get("BNJETTAG_REPO"):
            candidates.append(Path(os.environ["BNJETTAG_REPO"]))
        if os.environ.get("PYTHONPATH"):
            for raw in os.environ["PYTHONPATH"].split(os.pathsep):
                p = Path(raw).expanduser()
                if p.name == "hgq2" and len(p.parents) >= 3:
                    candidates.append(p.parents[2])
        here = Path.cwd().resolve()
        for base in (here, *here.parents):
            candidates.extend((base, base / "research"))
        seen = set()
        for candidate in candidates:
            try:
                candidate = candidate.expanduser().resolve()
            except OSError:
                continue
            if candidate in seen:
                continue
            seen.add(candidate)
            if ((candidate / "RESEARCH.md").is_file() and
                    (candidate / "bnjettag/roc-results/r14").is_dir()):
                return candidate
        raise FileNotFoundError(
            "Cannot find the research tree. Run ./setup.sh or set BNJETTAG_REPO. "
            "The cluster notebook pod normally syncs code only, so run this figure "
            "bundle locally unless the Round-14 result stores are also mounted."
        )

    ROOT = find_research_root()
    BN = ROOT / "bnjettag"
    ROC_ROOT = BN / "roc-results" / "r14"
    RESULT_ROOT = BN / "results" / "r14"
    default_output = Path(os.environ.get("BNHGQ2_OUT_ROOT", Path.cwd() / "outputs"))
    OUT = Path(os.environ.get("BNJETTAG_CONFERENCE_OUT", default_output)) / "conference-pre-ebops"
    OUT.mkdir(parents=True, exist_ok=True)

    # Era firewall: later target-enforcement stores are never candidates for a load.
    FORBIDDEN = (
        "ebops-n8-20260910", "ebops-n8-costfirst-20260910",
        "ebops-n8-long-20260911", "ebops-n8-ablation-20260912",
        "r15-gamma",
    )

    def source_path(path):
        path = Path(path).resolve()
        text = str(path)
        assert not any(token in text for token in FORBIDDEN), f"post-cutoff source rejected: {path}"
        assert path.is_file(), f"missing source: {path}"
        return path

    def relative(path):
        path = Path(path).resolve()
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return str(path)

    def bundle_relative(path):
        return str(Path(path).resolve().relative_to(OUT.resolve()))

    COLORS = {"FP32": "#E78AC3", "W8A8": "#D55E00", "W1A8": "#009E73",
              "W1A6": "#E69F00", "W1A4": "#CC79A7"}
    ARMS = ["FP32", "W8A8", "W1A8", "W1A6", "W1A4"]
    N_SWEEP = [8, 16, 32, 64]
    CLASSES = ["g", "q", "W", "Z", "t"]
    N_EVAL = 260_000
    ASSETS = []

    def save_figure(fig, stem, sources, caption):
        paths = []
        for ext in ("png", "pdf"):
            path = OUT / f"{stem}.{ext}"
            fig.savefig(path, dpi=220 if ext == "png" else None, bbox_inches="tight")
            paths.append(path)
        ASSETS.append({
            "name": stem, "kind": "generated-plot",
            "outputs": [bundle_relative(p) for p in paths],
            "sources": [relative(source_path(p)) for p in sources],
            "caption": caption,
        })
        display(fig)
        plt.close(fig)
        return paths

    print("research root :", ROOT)
    print("output bundle :", OUT)
    print("scope         : fixed-precision Round 14 only; enforced-EBOPs-target runs excluded")
    """),

    md("""
    ## 2 — recompute the Round-14 AUC table

    All 60 source arrays are checked before plotting: expected input set, era,
    metric, five-class shapes, three seeds per arm, and exact agreement between
    the recomputed macro one-vs-rest AUC and the value stored in each array's
    metadata. The plots below use the recomputation, never the stored summary.
    """),
    code("""
    aucs = {}
    roc_files = []
    rows = []
    for n in N_SWEEP:
        for arm in ARMS:
            for seed in (1, 2, 3):
                path = source_path(ROC_ROOT / f"n{n}" / f"{arm}-s{seed}.npz")
                with np.load(path, allow_pickle=True) as data:
                    y = data["y"]
                    score = data["score"]
                    meta = json.loads(str(data["meta"]))
                    assert y.shape == score.shape == (N_EVAL, 5), path
                    assert meta["era"] == 2 and meta["campaign"] == "final", path
                    assert meta["metric"] == "roc_test_auc_macro_ovr", path
                    assert meta["key"] == arm and int(meta["seed"]) == seed, path
                    per_class = [roc_auc_score(y[:, k], score[:, k]) for k in range(5)]
                macro = float(np.mean(per_class))
                assert abs(macro - float(meta["auc"])) < 1e-12, path
                aucs.setdefault((n, arm), []).append(macro)
                roc_files.append(path)
                rows.append([n, arm, seed, macro, *per_class, relative(path)])

    assert len(roc_files) == 60
    summary_csv = OUT / "round14_auc_recomputed.csv"
    with summary_csv.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["N", "arm", "seed", "macro_ovr_auc", *[f"auc_{c}" for c in CLASSES], "source"])
        writer.writerows(rows)

    print("AUC gate passed: 60/60 arrays; wrote", summary_csv)
    print("\\nseed mean +/- sample s.d.")
    for n in N_SWEEP:
        print(f"N={n:2d}", "  ".join(
            f"{arm}={np.mean(aucs[(n, arm)]):.4f}+/-{np.std(aucs[(n, arm)], ddof=1):.4f}"
            for arm in ARMS))
    """),

    md("## 3 — conference plot: held-out AUC vs constituent count"),
    code("""
    fig, ax = plt.subplots(figsize=(9.4, 6.3))
    for arm in ARMS:
        mu = [np.mean(aucs[(n, arm)]) for n in N_SWEEP]
        sd = [np.std(aucs[(n, arm)], ddof=1) for n in N_SWEEP]
        ax.errorbar(N_SWEEP, mu, yerr=sd, color=COLORS[arm], marker="o",
                    markersize=7, linewidth=2.2, capsize=4)
        ax.annotate(arm, (N_SWEEP[-1] * 1.04, mu[-1]), color=COLORS[arm],
                    fontsize=14, fontweight="bold", va="center")
    ax.set_xscale("log", base=2)
    ax.set_xticks(N_SWEEP, [str(n) for n in N_SWEEP])
    ax.set_xlim(7, 92)
    ax.set_xlabel(r"Constituents per jet, $N$ (top-$N$ by $p_T$)", fontsize=15)
    ax.set_ylabel("Held-out macro one-vs-rest AUC", fontsize=15)
    ax.set_title("Tagging accuracy vs constituent count, by precision", fontsize=17)
    ax.tick_params(labelsize=13)
    ax.grid(alpha=0.28)
    fig.text(0.5, 0.01,
             "HLS4ML LHC Jet, 5 classes | inputs: pT, eta_rel, phi_rel | "
             "ROC-test n=260,000 | mean +/- sample s.d., 3 seeds | fixed-precision R14",
             ha="center", fontsize=8.5, color="0.35")
    fig.tight_layout(rect=[0, 0.035, 1, 1])
    save_figure(
        fig, "fig_auc_vs_n_conference_pre_ebops", roc_files,
        "Held-out macro one-vs-rest AUC versus constituent count for the five fixed-precision "
        "Round-14 arms; points show the three-seed mean and bars the sample standard deviation."
    )
    """),

    md("## 4 — conference plot: held-out AUC vs checkpoint EBOPs"),
    code("""
    ebops_path = source_path(RESULT_ROOT / "ebops_r14.json")
    ebops_raw = json.loads(ebops_path.read_text())
    assert ebops_raw["convention"].startswith("hgq2_trace_minmax")
    ebops = {}
    for row in ebops_raw["models"].values():
        key = (int(row["n_part"]), str(row["variant"]).upper())
        ebops.setdefault(key, []).append(float(row["ebops"]))

    fig, ax = plt.subplots(figsize=(9.4, 6.3))
    for arm in ["W8A8", "W1A8", "W1A6", "W1A4"]:
        x = [np.mean(ebops[(n, arm)]) for n in N_SWEEP]
        y = [np.mean(aucs[(n, arm)]) for n in N_SWEEP]
        yerr = [np.std(aucs[(n, arm)], ddof=1) for n in N_SWEEP]
        ax.errorbar(x, y, yerr=yerr, color=COLORS[arm], marker="o",
                    markersize=7, linewidth=2.2, capsize=4)
        ax.annotate(arm, (x[-1] * 1.08, y[-1]), color=COLORS[arm],
                    fontsize=14, fontweight="bold", va="center")
        if arm == "W1A8":
            for n, xx, yy in zip(N_SWEEP, x, y):
                ax.annotate(f"N={n}", (xx, yy), xytext=(-8, 9),
                            textcoords="offset points", fontsize=10, color="0.3")
    ax.set_xscale("log")
    ax.set_xlabel("Estimated bit-operations per jet (EBOPs), three-seed mean", fontsize=15)
    ax.set_ylabel("Held-out macro one-vs-rest AUC", fontsize=15)
    ax.set_title("Tagging accuracy vs estimated arithmetic cost", fontsize=17)
    ax.tick_params(labelsize=13)
    ax.grid(alpha=0.28, which="both")
    fig.text(0.5, 0.01,
             "HGQ2 trace_minmax checkpoint EBOPs | same R14 ROC-test arrays as AUC-vs-N | "
             "FP32 omitted: it has no quantizers and therefore no checkpoint EBOP count",
             ha="center", fontsize=8.2, color="0.35")
    fig.tight_layout(rect=[0, 0.035, 1, 1])
    save_figure(
        fig, "fig_auc_vs_ebops_conference_pre_target", [*roc_files, ebops_path],
        "Held-out macro one-vs-rest AUC versus HGQ2 trace_minmax checkpoint EBOPs for the "
        "four quantized fixed-precision Round-14 arms; FP32 is omitted because the metric "
        "is defined from quantizers."
    )
    """),

    md("""
    ## 5 — conference backup plots: per-class ROC overlays

    HEP convention is enforced here: tagging efficiency (TPR) is the linear x
    axis and mistag rate (FPR) is the logarithmic y axis. These overlays use seed
    1, matching the existing conference backup figures; AUC-vs-N above carries
    the three-seed uncertainty summary.
    """),
    code("""
    for n in N_SWEEP:
        selected = [source_path(ROC_ROOT / f"n{n}" / f"{arm}-s1.npz") for arm in ARMS]
        curves = {}
        for arm, path in zip(ARMS, selected):
            with np.load(path, allow_pickle=True) as data:
                y, score = data["y"], data["score"]
                curves[arm] = []
                for k in range(5):
                    fpr, tpr, _ = roc_curve(y[:, k], score[:, k])
                    curves[arm].append((fpr, tpr, roc_auc_score(y[:, k], score[:, k])))

        fig, axes = plt.subplots(2, 3, figsize=(16.5, 9.6))
        axes = axes.ravel()
        for k, cls in enumerate(CLASSES):
            ax = axes[k]
            for arm in ARMS:
                fpr, tpr, auc = curves[arm][k]
                positive = fpr > 0
                ax.plot(tpr[positive], fpr[positive], color=COLORS[arm], linewidth=1.8,
                        label=f"{arm} (AUC={auc:.4f})")
            ax.set_yscale("log")
            ax.set_xlim(0, 1)
            ax.set_xlabel(f"{cls} tagging efficiency (TPR)", fontsize=11)
            ax.set_ylabel("Mistag rate (FPR, one-vs-rest)", fontsize=11)
            ax.set_title(f"{cls} vs rest", fontsize=13)
            ax.legend(loc="upper left", fontsize=8)
            ax.grid(alpha=0.28, which="both")
        axes[-1].axis("off")
        axes[-1].text(
            0.03, 0.95,
            "Round 14, seed 1\\n" + "\\n".join(
                f"{arm:5s} macro AUC = {aucs[(n, arm)][0]:.4f}" for arm in ARMS),
            family="monospace", fontsize=12, va="top")
        fig.suptitle(
            f"Per-class ROC — N={n}, pT/eta_rel/phi_rel inputs, fixed-precision Round 14",
            fontsize=16)
        fig.text(0.5, 0.012,
                 "HLS4ML LHC Jet, ROC-test n=260,000 | one-vs-rest | seed 1 | "
                 "linear tagging-efficiency axis, logarithmic mistag-rate axis",
                 ha="center", fontsize=9, color="0.35")
        fig.tight_layout(rect=[0, 0.035, 1, 0.96])
        save_figure(
            fig, f"roc_overlay_n{n}_conference_pre_ebops", selected,
            f"Seed-1 per-class one-vs-rest ROC overlay at N={n}; tagging efficiency is "
            "linear and mistag rate is logarithmic."
        )
    """),

    md("""
    ## 6 — conference plot: where the LUTs go

    The bars come from the per-instance table of the raw Vitis HLS report. The
    HLS total is read from `csynth_report.json`; the post-Vivado number in the
    footer is parsed from `post_opt_util.rpt`. No utilization number is typed
    into the plotting cell.
    """),
    code("""
    hls_dir = BN / "results/synthesis/runs/38a20c62/w1a8-s3-r14n8-beta1sm4i0/csynth_beta1sm4i0"
    rpt_path = source_path(hls_dir / "myproject_csynth.rpt")
    csynth_json = source_path(hls_dir / "csynth_report.json")
    vivado_util = source_path(hls_dir.parent / "postsyn_xczu7ev/post_opt_util.rpt")

    parser_dir = BN / "code/hgq2"
    if str(parser_dir) not in sys.path:
        sys.path.insert(0, str(parser_dir))
    parse_families = importlib.import_module("parse_families")
    families, _instance_rows, trusted = parse_families.load(str(rpt_path))
    assert trusted, "the trusted per-instance HLS table is required"

    hls_total = int(json.loads(csynth_json.read_text())["LUT"])
    match = re.search(r"^\\| CLB LUTs\\*?\\s*\\|\\s*([0-9,]+)\\s*\\|", vivado_util.read_text(), re.M)
    assert match, "could not parse post-opt CLB LUT total"
    vivado_total = int(match.group(1).replace(",", ""))

    buckets = [
        ("Binary linear layers (+/-1 weights)", ["einsum_dense", "dense_latency"]),
        ("beta rescaling in LUT logic", ["normalize"]),
        ("Attention activation x activation", ["einsum(actxact)"]),
        ("Activation requantization", ["thresholded_relu"]),
        ("Softmax", ["softmax", "Loop_VITIS_LOOP_408_1_proc", "Loop_VITIS_LOOP_408_1_proc111"]),
        ("Residual adds and pooling", ["add", "global_pooling1d_cl"]),
    ]
    lut_by_family = {key: value["LUT"] for key, value in families.items() if key != "(top-level)"}
    used = set()
    values = []
    for label, keys in buckets:
        count = sum(lut_by_family.get(key, 0) for key in keys)
        used.update(keys)
        values.append((label, count))
    ungrouped_modules = sum(value for key, value in lut_by_family.items() if key not in used)
    grouped = sum(value for _, value in values)
    values.append(("Inter-layer buffers and control", hls_total - grouped))
    assert sum(value for _, value in values) == hls_total
    values.sort(key=lambda item: item[1], reverse=True)

    labels = [label for label, _ in values]
    counts = [value for _, value in values]
    shares = [100 * value / hls_total for value in counts]
    fig, ax = plt.subplots(figsize=(12.5, 6.4))
    y_pos = list(range(len(values)))[::-1]
    ax.barh(y_pos, shares, color="#0B5394", height=0.62)
    for y, share, count in zip(y_pos, shares, counts):
        ax.text(share + 0.6, y, f"{share:.0f}%  ({count/1e3:,.0f}k)",
                va="center", fontsize=14, color="#1A1A1A")
    ax.set_yticks(y_pos, labels, fontsize=14)
    ax.set_xlabel("Share of HLS-estimated design LUTs (%) — N=8, W1A8", fontsize=14)
    ax.set_xlim(0, max(shares) * 1.34)
    ax.tick_params(axis="x", labelsize=12, colors="#555F66")
    ax.xaxis.grid(True, color="#DDDDDD", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.5, 0.012,
             f"Vitis HLS per-instance attribution: {hls_total:,} LUT total | "
             f"same build after Vivado post-opt: {vivado_total:,} CLB LUT | "
             "shares describe the HLS estimate, not the post-opt netlist",
             ha="center", fontsize=9, color="#555F66")
    fig.tight_layout(rect=[0, 0.045, 1, 1])
    save_figure(
        fig, "fig_lut_attribution_n8_conference_pre_ebops",
        [rpt_path, csynth_json, vivado_util],
        "Vitis HLS LUT attribution by module family for the N=8 W1A8 fitting "
        "characterization build; percentages use the HLS total, while the parsed "
        "Vivado post-opt total is provided only as implementation context."
    )
    print("ungrouped module LUTs included in buffers/control:", ungrouped_modules)
    """),

    md("""
    ## 7 — project diagram: BNJetTag architecture

    TikZ remains the source of record. If a local `tectonic` executable is
    available, this cell renders that source to PDF, SVG, and PNG. If it is not,
    the cell bundles the committed SVG with the exact TikZ source and records the
    fallback in the manifest. The fallback is explicit because a copied render is
    not a fresh render.
    """),
    code("""
    tex_source = source_path(ROOT / "docs/figures/bnjettag-architecture.tex")
    svg_source = source_path(ROOT / "docs/figures/bnjettag-architecture.svg")
    tex_out = OUT / "bnjettag-architecture.tex"
    shutil.copy2(tex_source, tex_out)

    tectonic = shutil.which("tectonic")
    if tectonic is None and Path("/opt/homebrew/bin/tectonic").is_file():
        tectonic = "/opt/homebrew/bin/tectonic"

    render_mode = "fresh local TikZ render"
    svg_out = OUT / "bnjettag-architecture.svg"
    png_out = OUT / "bnjettag-architecture.png"
    pdf_out = OUT / "bnjettag-architecture.pdf"
    try:
        if tectonic is None:
            raise FileNotFoundError("tectonic executable is unavailable")
        wrapper = (
            "\\\\documentclass[tikz,border=4pt]{standalone}\\n"
            "\\\\usepackage{tikz}\\n"
            "\\\\begin{document}\\n" + tex_source.read_text() +
            "\\n\\\\end{document}\\n"
        )
        with tempfile.TemporaryDirectory(prefix="bnjettag-tikz-", dir=OUT) as tmp:
            tmp = Path(tmp)
            wrapper_path = tmp / "architecture-wrapper.tex"
            wrapper_path.write_text(wrapper)
            completed = subprocess.run(
                [tectonic, "--outdir", str(tmp), str(wrapper_path)],
                cwd=tmp, capture_output=True, text=True, timeout=180)
            if completed.returncode:
                raise RuntimeError(completed.stderr[-2000:])
            shutil.copy2(tmp / "architecture-wrapper.pdf", pdf_out)
        import pymupdf
        document = pymupdf.open(pdf_out)
        page = document[0]
        svg_out.write_text(page.get_svg_image(text_as_path=False))
        page.get_pixmap(matrix=pymupdf.Matrix(3, 3), alpha=False).save(png_out)
        document.close()
        outputs = [tex_out, svg_out, png_out, pdf_out]
    except Exception as exc:
        render_mode = f"verified committed SVG fallback ({type(exc).__name__}: {exc})"
        shutil.copy2(svg_source, svg_out)
        try:
            import pymupdf
            document = pymupdf.open(svg_out)
            page = document[0]
            page.get_pixmap(matrix=pymupdf.Matrix(3, 3), alpha=False).save(png_out)
            document.close()
            outputs = [tex_out, svg_out, png_out]
        except Exception:
            outputs = [tex_out, svg_out]

    ASSETS.append({
        "name": "bnjettag-architecture", "kind": "generated-diagram",
        "outputs": [bundle_relative(path) for path in outputs],
        "sources": [relative(tex_source), relative(svg_source)],
        "method": render_mode,
        "caption": "BNJetTag fixed-precision Round-14 architecture: L1-realistic (N,3) inputs, "
                   "two encoder blocks, binary linear layers, mean pooling, and five-class output."
    })
    print("architecture mode:", render_mode)
    display(SVG(filename=str(svg_out)))
    """),

    md("""
    ## 8 — externally sourced context diagrams

    These are part of the conference visual bundle but are not project-generated
    evidence. The notebook preserves the files byte-for-byte, prints their hashes,
    displays their credits, and marks them `reference-only` in the manifest.
    """),
    code("""
    references = [
        ("bitnet-explainer-wang-fig2", source_path(ROOT / "bitnet-arch.png"),
         "Wang et al., BitNet, arXiv:2310.11453, Fig. 2."),
        ("cms-trigger-flow-pierini", source_path(ROOT / "ByMaurizio.png"),
         "CMS trigger data-flow figure credited to M. Pierini in the conference poster."),
    ]
    for name, src, credit in references:
        dst = OUT / f"{name}{src.suffix.lower()}"
        shutil.copy2(src, dst)
        digest = hashlib.sha256(dst.read_bytes()).hexdigest()
        ASSETS.append({
            "name": name, "kind": "reference-only",
            "outputs": [bundle_relative(dst)], "sources": [relative(src)],
            "sha256": digest, "credit": credit,
            "caption": credit,
        })
        print(f"{name}: {digest} | {credit}")
        display(Image(filename=str(dst)))
    """),

    md("## 9 — write and audit the bundle manifest"),
    code("""
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "generator": "nrp-lab/notebooks/04_conference_figures_pre_ebops.ipynb",
        "scope": "fixed-precision Round 14 conference visuals before EBOPs-target enforcement",
        "included_roots": [
            "bnjettag/roc-results/r14",
            "bnjettag/results/r14/ebops_r14.json",
            "bnjettag/results/synthesis/runs/38a20c62/w1a8-s3-r14n8-beta1sm4i0",
            "docs/figures/bnjettag-architecture.tex",
        ],
        "excluded_tokens": list(FORBIDDEN),
        "auc_gate": "60/60 .npz arrays recomputed; metadata macro AUC matched to <1e-12",
        "assets": ASSETS,
    }
    manifest_path = OUT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\\n")

    forbidden_hits = [
        source for asset in ASSETS for source in asset.get("sources", [])
        if any(token in source for token in FORBIDDEN)
    ]
    assert not forbidden_hits, forbidden_hits
    generated = [asset for asset in ASSETS if asset["kind"] != "reference-only"]
    assert len(generated) == 8, [(asset["name"], asset["kind"]) for asset in ASSETS]

    print(f"bundle complete: {len(ASSETS)} assets ({len(generated)} generated, 2 reference-only)")
    print("manifest:", manifest_path)
    for asset in ASSETS:
        print("\\n-", asset["name"], f"[{asset['kind']}]")
        print("  output :", ", ".join(asset["outputs"]))
        print("  source :", ", ".join(asset["sources"]))
        print("  caption:", asset["caption"])
    """),

    md("""
    ---
    **Expected bundle:** AUC-vs-N, AUC-vs-EBOPs, four ROC overlays, LUT
    attribution, the architecture diagram, two credited context images, the
    recomputed AUC CSV, and `manifest.json`. The manifest is the audit trail and
    the machine-readable statement that no EBOPs-target-enforcement result entered
    the conference visuals.
    """),
]


# Keep this block LAST: it references every nbNN above, so a notebook defined below it
# would raise NameError at import time.
if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    write("00_env_check.ipynb", nb00)
    write("01_smoke_train.ipynb", nb01)
    write("02_binary_transformer_workbench.ipynb", nb02)
    write("03_einsum_vs_matmul.ipynb", nb03)
    write("04_conference_figures_pre_ebops.ipynb", nb04)
