#!/usr/bin/env python3
'Convert a floating-point training baseline to a controlled fixed-point HLS realization.'
from __future__ import annotations

import argparse
import copy
import json
import os
import platform
import re
import sys
import time

import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from bnhgq2.config import load_config, cfg_hash, PROJECT_ROOT  # noqa: E402

import convert_binary as cf  # noqa: E402  -- reuse the proven helpers, touch nothing

WEIGHT_LAYER_ATTR = "kq"          # every weighted HGQ2 layer carries a kernel quantizer
LADDER_DEFAULT = (8, 12, 16, 20, 24)


# --------------------------------------------------------------------------- #
# fixed-point helpers (numpy images of the KIF / ap_fixed grids)              #
# --------------------------------------------------------------------------- #
def kif_grid(i: int, f: int, signed: bool = True):
    """(step, lo, hi) of a KIF grid == ap_fixed<signed+i+f, signed+i> (RND_CONV/SAT)."""
    step = 2.0 ** (-f)
    if signed:
        return step, -(2.0 ** i), 2.0 ** i - step
    return step, 0.0, 2.0 ** i - step


def quantize_kif(x, i: int, f: int, signed: bool = True):
    step, lo, hi = kif_grid(i, f, signed)
    return np.clip(np.round(np.asarray(x, dtype=np.float64) / step) * step, lo, hi)


def grid_from_absmax(absmax: float, width: int, i_min: int = -8):
    """`intW_absmax`: the `_static_w8` rule generalised to width W.

    Return (i, f) with f = W-1-i, i the NARROWEST signed integer width whose SAT range
    [-2^i, 2^i - 2^-f] contains `absmax`. i is allowed to go negative (Vitis accepts
    ap_fixed<W, I<=0>); the floor `i_min` exists only so a degenerate all-zero kernel
    terminates. No silent clamping -- the chosen i is recorded per layer and the emitted
    container is verified against it."""
    a = float(absmax)
    hi_i = width - 2                      # guarantee f = W-1-i >= 1
    for i in range(i_min, hi_i + 1):
        f = width - 1 - i
        _, _, hi = kif_grid(i, f)
        if a <= hi:
            return i, f
    return hi_i, width - 1 - hi_i


_PREC_RE = re.compile(r"ap_(u?)fixed<\s*(-?\d+)\s*,\s*(-?\d+)")


def parse_prec(s: str):
    """'ap_fixed<24,12,AP_RND_CONV,AP_SAT>' -> dict(width, integer, signed)."""
    m = _PREC_RE.search(str(s))
    if not m:
        return None
    return {"raw": str(s).strip(), "signed": m.group(1) != "u",
            "width": int(m.group(2)), "integer": int(m.group(3))}


def container_holds(values, prec: dict):
    """max|value - value_as_stored_in(prec)|. 0.0 == the container represents the grid
    exactly; anything else is silent truncation (falsifier F6)."""
    signed = bool(prec["signed"])
    i = int(prec["integer"]) - (1 if signed else 0)
    f = int(prec["width"]) - int(prec["integer"])
    q = quantize_kif(values, i, f, signed=signed)
    return float(np.abs(np.asarray(values, dtype=np.float64) - q).max())


# --------------------------------------------------------------------------- #
# step 2 -- EXPORT: the FP32 graph minus pos_enc, PE folded into input_proj    #
# --------------------------------------------------------------------------- #
def build_fp32_export(cfg: dict, qat_model, seed: int):
    """Rebuild the FP32 graph without AddPositional, port every layer's variables by
    name, fold the trained pos table into input_proj's (T,D) bias. Both graphs are FP32
    (dummy quantizers) so the variable counts DO match here and per-layer set_weights is
    exact. Returns (export_model, n_layers_ported, max_abs_pos)."""
    from bnhgq2.qat import build_qat_model

    export, _taps = build_qat_model(cfg, seed=seed, with_pos_enc=False)

    qat_names = {ly.name for ly in qat_model.layers}
    exp_names = {ly.name for ly in export.layers}
    missing, extra = qat_names - exp_names, exp_names - qat_names
    if missing != {"pos_enc"} or extra:
        raise SystemExit(f"export graph mismatch: missing={sorted(missing)} "
                         f"extra={sorted(extra)} (expected exactly {{'pos_enc'}} missing)")

    n_ported = 0
    for ly in export.layers:
        src = qat_model.get_layer(ly.name)
        ws, dst = src.get_weights(), ly.get_weights()
        if not ws and not dst:
            continue
        if len(ws) != len(dst):
            raise SystemExit(f"{ly.name}: variable count mismatch {len(ws)} vs {len(dst)}")
        for a, b in zip(ws, dst):
            if tuple(np.shape(a)) != tuple(np.shape(b)):
                raise SystemExit(f"{ly.name}: variable shape mismatch "
                                 f"{np.shape(a)} vs {np.shape(b)}")
        ly.set_weights(ws)
        n_ported += 1

    # the fold: (x.W + b) + pos == x.W + (b + pos) -- exact constant-add identity
    pos = cf._to_np(qat_model.get_layer("pos_enc").pos)          # (1, T, D)
    ip = export.get_layer("input_proj")
    bv = getattr(ip, "_bias", None)
    if bv is None:
        bv = ip.bias
    bv.assign((cf._to_np(bv) + pos[0]).astype("float32"))
    return export, n_ported, float(np.abs(pos).max())


# --------------------------------------------------------------------------- #
# step 3 -- REALIZATION: a live-quantizer graph at width W                     #
# --------------------------------------------------------------------------- #
def derive_realization_cfg(cfg: dict, width: int, weight_width: int = None) -> dict:
    """The fp32 config with a live datapath bolted on. `int8_absmax` selects the stock
    QEinsumDense/QDense + static KIF weight/activation grids branch of build_qat_model
    (the same layer classes the fp32 branch builds, so the graph topology and layer names
    are IDENTICAL -- verified by name-set equality in build_realization). The 8-bit grid
    it installs is then REPLACED per layer by the width-W absmax grid, so nothing 8-bit
    survives; the mode string is only the branch selector.

    `act_calib` is forced to 'frozen' so the activation quantizers are explicit KIF
    (both `_i` and `_f` written by calibrate_activations, exactly the `_static_quant_np`
    semantics the MSE calibration optimises); the config's training-time 'trainable'
    setting is meaningless for a post-training realization."""
    c = copy.deepcopy(cfg)
    c["quant"]["weight"] = "int8_absmax"
    c["quant"]["act_bits"] = int(width)
    c["quant"]["act_calib"] = "frozen"
    ww = int(width if weight_width is None else weight_width)
    c["name"] = (f"{cfg['name']}-realization-w{int(width)}" if ww == int(width)
                 else f"{cfg['name']}-realization-w{ww}a{int(width)}")
    return c


def _kernel_var(ly):
    """The layer's kernel VARIABLE (never the quantized view), or None. HGQ2 layers hold
    the latent float kernel on `_kernel` and expose the quantized one as `qkernel`."""
    v = getattr(ly, "_kernel", None)
    return getattr(ly, "kernel", None) if v is None else v


def _bias_var(ly):
    v = getattr(ly, "_bias", None)
    if v is None:
        v = getattr(ly, "bias", None)
    return v


def build_realization(cfg: dict, export_model, seed: int, width: int,
                      X_calib: np.ndarray, weight_width: int = None):
    """Build the width-W live-quantizer graph, port kernels/biases BY NAME from the
    float export, install the intW_absmax weight grids, MSE-calibrate the activation
    grids. Returns (model, record)."""
    from bnhgq2.qat import build_qat_model, calibrate_activations, _assign_if

    w_w = int(width if weight_width is None else weight_width)
    cfg_r = derive_realization_cfg(cfg, width, weight_width)
    model, taps = build_qat_model(cfg_r, seed=seed, with_pos_enc=False)

    a_names = {ly.name for ly in export_model.layers}
    b_names = {ly.name for ly in model.layers}
    if a_names != b_names:
        raise SystemExit(f"realization graph mismatch: only-in-export="
                         f"{sorted(a_names - b_names)} only-in-realization="
                         f"{sorted(b_names - a_names)}")

    n_vars_export = len(export_model.variables)
    n_vars_real = len(model.variables)

    # ---- port kernels and biases BY NAME (never whole-layer set_weights) ----
    n_k = n_b = 0
    port_max_abs = 0.0
    for ly in model.layers:
        src = export_model.get_layer(ly.name)
        for reader, counter in ((_kernel_var, "k"), (_bias_var, "b")):
            dv, sv = reader(ly), reader(src)
            if dv is None and sv is None:
                continue
            if (dv is None) != (sv is None):
                raise SystemExit(f"{ly.name}: {counter} present on one graph only")
            a = cf._to_np(sv)
            if tuple(np.shape(a)) != tuple(dv.shape):
                raise SystemExit(f"{ly.name}: {counter} shape mismatch "
                                 f"{np.shape(a)} vs {tuple(dv.shape)}")
            dv.assign(a.astype("float32"))
            port_max_abs = max(port_max_abs, float(np.abs(cf._to_np(dv) - a).max()))
            if counter == "k":
                n_k += 1
            else:
                n_b += 1

    # ---- weight grids: intW_absmax ----
    grids = {}
    for ly in model.layers:
        if not hasattr(ly, WEIGHT_LAYER_ATTR):
            continue
        k = cf._to_np(_kernel_var(ly)).astype(np.float64)
        amax = float(np.abs(k).max())
        i, f = grid_from_absmax(amax, w_w)
        qz = ly.kq.quantizer
        _assign_if(qz, i, f)
        # verify the assign took AND that the effective forward kernel really lands on
        # the 2^-f lattice inside the SAT range (a silently-ignored assign is caught here,
        # before a C-sim is spent on it).
        qk = cf._to_np(ly.qkernel).astype(np.float64)
        lattice_err = float(np.abs(qk - quantize_kif(qk, i, f)).max())
        round_err = float(np.abs(qk - k).max())
        bound = 0.5 * (2.0 ** -f) + 1e-12
        clipped = bool(amax > kif_grid(i, f)[2] + 1e-12)
        ok = (lattice_err == 0.0) and (round_err <= bound) and not clipped
        grids[ly.name] = {
            "kernel_absmax": amax, "i": int(i), "f": int(f),
            "total_bits": int(1 + i + f),
            "ap_fixed": f"ap_fixed<{1 + i + f},{1 + i}>",
            "reported_bits": float(np.asarray(cf._to_np(qz.bits)).ravel()[0]),
            "qkernel_lattice_max_abs_err": lattice_err,
            "qkernel_vs_float_max_abs_err": round_err,
            "half_lsb_bound": bound, "grid_assign_ok": ok,
        }
        if not ok:
            raise SystemExit(
                f"STOP: weight-grid assign did not take on {ly.name} at W={width} "
                f"(lattice_err={lattice_err:g}, round_err={round_err:g} > "
                f"half-LSB {bound:g}, clipped={clipped})")

    # ---- activation grids: MSE calibration at act_bits = W ----
    # calibrate_activations defaults to batch=4096; the memo pins calib_n, so pass it.
    n_calib = int(len(X_calib))
    site_i = calibrate_activations(model, taps, X_calib, act_bits=width, batch=n_calib)

    from bnhgq2.qat import act_grid_params
    act_grids = {k: {"i": v[0], "f": v[1], "total_bits": float(v[0] + v[1] + 1)}
                 for k, v in act_grid_params(model).items()}

    wf = [g["f"] for g in grids.values()]
    frac_default = max(12, max(wf) if wf else 12)
    record = {
        "width": int(width),
        "act_width": int(width),
        "weight_width": int(w_w),
        "width_decoupled": bool(w_w != int(width)),
        "width_decoupling_note": (
            "activation grids are calibrated at act_bits = act_width; the intW_absmax "
            "weight grids are built at weight_width. When the two differ this arm is a "
            "WEIGHT-WIDTH-MATCHED control (design memo CORRECTION C1.3): it exists to "
            "hold the einsum operand (activation) width fixed at the comparator's while "
            "moving ONLY the weight lattice. It is NOT an operating point."),
        "derived_config": cfg_r["quant"],
        "n_variables_export_fp32": n_vars_export,
        "n_variables_realization": n_vars_real,
        "port": {"mechanism": "by-name kernel/bias assign (NOT whole-layer set_weights)",
                 "n_kernels": n_k, "n_biases": n_b,
                 "max_abs_assign_residual": port_max_abs},
        "weight_grids": grids,
        "weight_grid_rule": (f"intW_absmax at W={w_w}: narrowest signed KIF i with "
                             "2^i - 2^-(W-1-i) >= max|kernel|, f = W-1-i "
                             "(the _static_w8 rule generalised)"),
        "act_calibration": {"policy": "static_per_tensor_mse_calibrated",
                            "act_bits": int(width), "n_calib_jets": n_calib,
                            "n_sites": len(site_i), "site_i": site_i},
        "act_grids": act_grids,
        "model_default_frac_required": int(frac_default),
        "model_precision_rule": (f"fixed<{12 + frac_default},12> -- integer width held "
                                 "at the w8a8 value 12, fractional width widened to "
                                 "contain the widest weight grid (EinsumDense weights "
                                 "have no per-layer typedef in hls4ml 1.3.0 and land on "
                                 "the Model fallback)"),
        "model_precision": f"fixed<{12 + frac_default},12>",
    }
    return model, record


# --------------------------------------------------------------------------- #
# step 5 -- firmware read-back / falsifier F6                                  #
# --------------------------------------------------------------------------- #
def audit_fp32_firmware(out_dir: str):
    """Parse the emitted firmware verbatim: model default, per-layer weight typedefs,
    which weight array feeds which core, and the container type each array is LOADED as
    (`load_weights_from_txt<TYPE, N>` -- the authoritative container)."""
    fw = os.path.join(out_dir, "firmware")
    defines = open(os.path.join(fw, "defines.h")).read()
    params = open(os.path.join(fw, "parameters.h")).read()
    cpp = open(os.path.join(fw, "myproject.cpp")).read()

    m = re.search(r"typedef\s+(.+?)\s+model_default_t;", defines)
    weight_typedefs = {layer: typ for typ, layer in
                       re.findall(r"typedef\s+(ap_u?fixed<[^>]*>)\s+(\w+)_weight_t;", defines)}
    bias_typedefs = {layer: typ for typ, layer in
                     re.findall(r"typedef\s+(ap_u?fixed<[^>]*>)\s+(\w+)_bias_t;", defines)}
    arrays = {name: {"type": t.strip(), "n": int(n)} for t, n, name in
              re.findall(r"load_weights_from_txt<([^,]+),\s*(\d+)>\((\w+),", cpp)}

    calls, n_einsum_dense, n_dense = {}, 0, 0
    for kind, args, layer in re.findall(
            r"nnet::(einsum_dense|dense\w*)<[^>]*>\(([^)]*)\);\s*//\s*(\w+)", cpp):
        warr = [a.strip() for a in args.split(",") if re.fullmatch(r"w\d+", a.strip())]
        rec = {"core": kind}
        if warr:
            rec["weight_array"] = warr[0]
            if warr[0] in arrays:
                rec.update(arrays[warr[0]])
        calls[layer] = rec
        n_einsum_dense += (kind == "einsum_dense")
        n_dense += (kind != "einsum_dense")

    return {
        "model_default_t": m.group(1) if m else None,
        "weight_typedefs": weight_typedefs,
        "n_weight_typedefs": len(weight_typedefs),
        "bias_typedefs": bias_typedefs,
        "config_weight_t_kinds": sorted(set(re.findall(r"typedef\s+(\w+)\s+weight_t;", params))),
        "n_model_default_weight_t": params.count("typedef model_default_t weight_t;"),
        "n_model_default_bias_t": params.count("typedef model_default_t bias_t;"),
        "weighted_cores": calls,
        "n_einsum_dense": n_einsum_dense,
        "n_dense": n_dense,
    }


def check_realization_emitted(audit: dict, realization_model, grids: dict, width: int):
    """FALSIFIER F6, decided on the EMITTED firmware, not on intent.

    For every weighted layer: resolve the container the weights are actually LOADED as
    (`load_weights_from_txt<TYPE,...>`; `model_default_t` resolves through the defines),
    then check that container represents the layer's realization grid EXACTLY
    (max|w - w_as_stored| == 0). This is stricter and more honest than asserting
    'typedef width == W': hls4ml's BitExact legitimately TIGHTENS a named weight typedef
    to the range the values occupy (the shipped w8a8 article emits ap_fixed<6,1> for an
    8-bit grid), so a width-equality test would false-abort, while a container too NARROW
    to hold the grid -- the actual F6 failure -- is caught exactly."""
    default = parse_prec(audit.get("model_default_t") or "")
    by_name = {ly.name: ly for ly in realization_model.layers}
    per_layer, offenders = {}, []
    for name, g in grids.items():
        core = audit["weighted_cores"].get(name, {})
        tname = core.get("type")
        if tname == "model_default_t":
            prec = default
        else:
            prec = parse_prec(audit["weight_typedefs"].get(name, "")) or \
                parse_prec(tname or "")
        qk = cf._to_np(by_name[name].qkernel).astype(np.float64)
        if prec is None:
            per_layer[name] = {"container": tname, "resolved": None,
                               "max_abs_truncation": None, "ok": False,
                               "why": "container type could not be parsed"}
            offenders.append(name)
            continue
        trunc = container_holds(qk, prec)
        ok = (trunc == 0.0)
        per_layer[name] = {
            "core": core.get("core"), "weight_array": core.get("weight_array"),
            "container_typedef": tname, "container": prec["raw"],
            "container_width": prec["width"], "container_integer": prec["integer"],
            "container_frac": prec["width"] - prec["integer"],
            "grid": g["ap_fixed"], "grid_frac": g["f"],
            "max_abs_truncation": trunc, "ok": ok,
        }
        if not ok:
            offenders.append(name)
    return {
        "falsifier": "F6 -- emitted precision must represent the intended realization",
        "intended_width": int(width),
        "model_default_t": audit.get("model_default_t"),
        "n_weighted_layers": len(grids),
        "per_layer": per_layer,
        "offenders": sorted(offenders),
        "pass": len(offenders) == 0,
        "rule": ("container must hold every quantized weight EXACTLY "
                 "(max|w - stored(w)| == 0); BitExact narrowing of a named typedef to "
                 "the occupied range is NOT a failure, silent truncation is"),
    }


# --------------------------------------------------------------------------- #
# step 6 -- fidelity metrics                                                   #
# --------------------------------------------------------------------------- #
def _auc_fast(y_bin: np.ndarray, score: np.ndarray) -> float:
    """Rank (Mann-Whitney) AUC with average ranks for ties -- identical to
    sklearn.metrics.roc_auc_score, ~100x faster, which is what makes a 1000-draw paired
    bootstrap at n=32,768 affordable. Verified against sklearn in --self-test."""
    from scipy.stats import rankdata
    y = np.asarray(y_bin).astype(bool)
    n_pos = int(y.sum())
    n_neg = int(y.size - n_pos)
    if n_pos == 0 or n_neg == 0:
        return float("nan")
    r = rankdata(np.asarray(score, dtype=np.float64))
    return float((r[y].sum() - n_pos * (n_pos + 1) / 2.0) / (n_pos * n_neg))


def _macro_auc(y_oh: np.ndarray, s: np.ndarray):
    per = [_auc_fast(y_oh[:, c], s[:, c]) for c in range(s.shape[1])]
    return float(np.mean(per)), per


CLASSES = ["g", "q", "W", "Z", "t"]     # verified order of the pre-conference score arrays
FPR_TARGETS = (0.01, 0.10)              # make_working_points.FPR_TARGETS


def _wp():
    """The project's working-point function, imported VERBATIM from
    `code/analysis/make_working_points.py` (physics sign-off 2026-09-02: do not
    reimplement the working-point logic). That module is import-safe -- its module level
    only builds Path objects."""
    global _WP_FN
    try:
        return _WP_FN
    except NameError:
        pass
    import importlib.util
    p = os.path.join(PROJECT_ROOT, "code", "analysis", "make_working_points.py")
    spec = importlib.util.spec_from_file_location("_bn_make_working_points", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if tuple(mod.FPR_TARGETS) != FPR_TARGETS:
        raise SystemExit(f"make_working_points.FPR_TARGETS changed: {mod.FPR_TARGETS}")
    _WP_FN = mod.working_points
    return _WP_FN


def _per_class_stats(y_oh, s):
    """(auc[C], eff@1%[C], eff@10%[C]) -- one roc_curve per class covers BOTH FPR
    targets, so eff@10% is free (the physics sign-off says report it only if free)."""
    wp = _wp()
    C = s.shape[1]
    auc = np.empty(C); e01 = np.empty(C); e10 = np.empty(C)
    for c in range(C):
        auc[c] = _auc_fast(y_oh[:, c], s[:, c])
        tpr_at_fpr, _rej, _cl = wp(y_oh[:, c].astype(int), s[:, c])
        e01[c] = tpr_at_fpr[0.01]
        e10[c] = tpr_at_fpr[0.10]
    return auc, e01, e10


def tie_plateau(y_bin, score, target_fpr=0.01):
    """Does a TIE PLATEAU form at the fixed-mistag threshold?

    The deployment-fatal failure mode named by the physics sign-off (2026-09-02): a
    coarse static grid can collapse many jets onto one score value at the working point.
    That does not merely shift epsilon_S -- it destroys threshold tunability, and a
    fixed-rate L1 algorithm cannot sit on a plateau whatever the AUC says.

    Returns the threshold at `target_fpr`, the fraction of jets/backgrounds/signals
    sharing that exact score, the FPR immediately below vs at-or-above it, and whether
    that discontinuity STRADDLES the target rate (the fatal case: no threshold realizes
    the target FPR)."""
    from sklearn.metrics import roc_curve
    y = np.asarray(y_bin).astype(bool)
    sc = np.asarray(score, dtype=np.float64)
    n, n_neg, n_pos = sc.size, int((~y).sum()), int(y.sum())
    fpr, tpr, thr = roc_curve(y.astype(int), sc)
    k = int(np.searchsorted(fpr, target_fpr, side="left"))
    k = min(max(k, 1), len(thr) - 1)
    t_star = float(thr[k])
    at = (sc == t_star)
    fpr_below = float((sc[~y] > t_star).mean()) if n_neg else float("nan")
    fpr_at = float((sc[~y] >= t_star).mean()) if n_neg else float("nan")
    return {
        "target_fpr": float(target_fpr),
        "threshold": t_star,
        "n_unique_scores": int(np.unique(sc).size),
        "unique_fraction": float(np.unique(sc).size / n),
        "tie_fraction_all": float(at.mean()),
        "tie_fraction_background": float(at[~y].mean()) if n_neg else float("nan"),
        "tie_fraction_signal": float(at[y].mean()) if n_pos else float("nan"),
        "fpr_strictly_above_threshold": fpr_below,
        "fpr_at_or_above_threshold": fpr_at,
        "fpr_jump": float(fpr_at - fpr_below),
        "straddles_target": bool(fpr_below < target_fpr < fpr_at),
        "note": ("straddles_target=True means NO threshold realizes the target mistag "
                 "rate: the working point is untunable, which is fatal for a fixed-rate "
                 "L1 algorithm regardless of AUC"),
    }


def fidelity_block(y_ref_logits, y_test_logits, y_oh, *, label: str,
                   n_boot: int = 1000, boot_seed: int = 20260902,
                   classes=CLASSES):
    """Everything a fidelity bar could be powered on, for ONE pair of arms on ONE jet
    set: correlations, argmax agreement, residues, per-class AUC and per-class signal
    efficiency at fixed mistag for BOTH arms, all paired deltas, paired-bootstrap 95%
    UPPER BOUNDS on |delta| for macro AUC, per-class AUC and per-class eff@1%, and the
    tie-plateau diagnostic at the 1%-mistag working point.

    `n_boot=0` skips the bootstrap. The bootstrap resamples JETS and scores BOTH arms on
    the SAME resampled indices. Both arms are the SAME trained article (fixed s3
    weights), so the only term is finite-sample noise: no seed spread is involved and no
    +-sigma from seed variation may ever be attached to these deltas."""
    yr = np.asarray(y_ref_logits, dtype=np.float64)
    yt = np.asarray(y_test_logits, dtype=np.float64).reshape(yr.shape)
    sr, st = cf._softmax(yr), cf._softmax(yt)
    d = np.abs(yt - yr)
    n, C = int(len(yr)), sr.shape[1]
    cls = list(classes)[:C]

    auc_r, e01_r, e10_r = _per_class_stats(y_oh, sr)
    auc_t, e01_t, e10_t = _per_class_stats(y_oh, st)

    out = {
        "label": label, "n": n, "class_order": cls,
        "corr_logits": float(np.corrcoef(yt.ravel(), yr.ravel())[0, 1]),
        "corr_scores": float(np.corrcoef(st.ravel(), sr.ravel())[0, 1]),
        "corr_scores_per_class": [float(np.corrcoef(st[:, c], sr[:, c])[0, 1])
                                  for c in range(C)],
        "argmax_agreement": float(np.mean(st.argmax(1) == sr.argmax(1))),
        "max_abs_diff_logits": float(d.max()),
        "mean_abs_diff_logits": float(d.mean()),
        "max_abs_diff_scores": float(np.abs(st - sr).max()),
        "bit_exact": bool(d.max() == 0.0),
        "macro_ovr_auc_ref": float(auc_r.mean()),
        "macro_ovr_auc_test": float(auc_t.mean()),
        "delta_macro_auc": float(auc_t.mean() - auc_r.mean()),
        "per_class_auc_ref": {k: float(v) for k, v in zip(cls, auc_r)},
        "per_class_auc_test": {k: float(v) for k, v in zip(cls, auc_t)},
        "delta_per_class_auc": {k: float(a - b) for k, a, b in zip(cls, auc_t, auc_r)},
        "signal_efficiency_at_fixed_mistag": {
            "source": ("code/analysis/make_working_points.py::working_points, imported "
                       "verbatim (physics sign-off 2026-09-02)"),
            "fpr_0.01": {
                "eff_ref": {k: float(v) for k, v in zip(cls, e01_r)},
                "eff_test": {k: float(v) for k, v in zip(cls, e01_t)},
                "delta": {k: float(a - b) for k, a, b in zip(cls, e01_t, e01_r)},
                "rel_delta": {k: float((a - b) / b) if b else float("nan")
                              for k, a, b in zip(cls, e01_t, e01_r)},
                "macro_ref": float(e01_r.mean()), "macro_test": float(e01_t.mean()),
                "delta_macro": float(e01_t.mean() - e01_r.mean()),
            },
            "fpr_0.10": {
                "eff_ref": {k: float(v) for k, v in zip(cls, e10_r)},
                "eff_test": {k: float(v) for k, v in zip(cls, e10_t)},
                "delta": {k: float(a - b) for k, a, b in zip(cls, e10_t, e10_r)},
                "note": ("free -- one roc_curve per class covers both targets; the "
                         "physics sign-off records it as nearly inert"),
            },
        },
        "tie_plateau_at_1pct_fpr": {
            "ref": {k: tie_plateau(y_oh[:, c], sr[:, c], 0.01)
                    for c, k in enumerate(cls)},
            "test": {k: tie_plateau(y_oh[:, c], st[:, c], 0.01)
                     for c, k in enumerate(cls)},
        },
    }

    if n_boot and n_boot > 0:
        rng = np.random.default_rng(boot_seed)
        dm = np.empty(n_boot)
        da = np.empty((n_boot, C)); de1 = np.empty((n_boot, C)); de10 = np.empty((n_boot, C))
        for b in range(n_boot):
            idx = rng.integers(0, n, size=n)          # SAME indices for both arms
            yb = y_oh[idx]
            ar, br, cr = _per_class_stats(yb, sr[idx])
            at_, bt, ct = _per_class_stats(yb, st[idx])
            dm[b] = at_.mean() - ar.mean()
            da[b] = at_ - ar
            de1[b] = bt - br
            de10[b] = ct - cr

        def _summ(v):
            lo, hi = np.percentile(v, [2.5, 97.5])
            # AMENDMENT A1 rule reference experiment: with K rungs evaluated, bounds are read at
            # 1 - 0.05/K (K = 5 -> 99%). Emitted alongside the 95% fields, which are
            # untouched, so every historical field keeps its meaning.
            lo99, hi99 = np.percentile(v, [0.5, 99.5])
            return {"mean": float(v.mean()), "std": float(v.std(ddof=1)),
                    "ci95_lo": float(lo), "ci95_hi": float(hi),
                    "abs_delta_upper95": float(max(abs(lo), abs(hi))),
                    "ci99_lo": float(lo99), "ci99_hi": float(hi99),
                    "abs_delta_upper99": float(max(abs(lo99), abs(hi99)))}

        out["paired_bootstrap"] = {
            "B": int(n_boot), "seed": int(boot_seed),
            "rule": ("paired over jets, same resampled indices for both arms; the "
                     "selection statistic is the 95% UPPER BOUND on |delta|, not the "
                     "point estimate (uncertainty sign-off 2026-09-02). Finite-sample "
                     "noise only -- NOT a seed-variance interval."),
            "delta_macro_auc": _summ(dm),
            "delta_per_class_auc": {k: _summ(da[:, c]) for c, k in enumerate(cls)},
            "delta_per_class_eff_at_fpr_0.01": {k: _summ(de1[:, c])
                                                for c, k in enumerate(cls)},
            "delta_per_class_eff_at_fpr_0.10": {k: _summ(de10[:, c])
                                                for c, k in enumerate(cls)},
        }
        pb = out["paired_bootstrap"]
        out["worst_class"] = {
            "auc": max(cls, key=lambda k: pb["delta_per_class_auc"][k]["abs_delta_upper95"]),
            "eff_at_1pct": max(
                cls, key=lambda k: pb["delta_per_class_eff_at_fpr_0.01"][k]["abs_delta_upper95"]),
        }
        out["candidate_bar_checks"] = _bar_checks(out)
    return out


# candidate bars, ALL provisional -- recorded, evaluated, but never used here to pick W*
CANDIDATE_BARS = {
    "corr_scores_min": 0.999,
    "argmax_agreement_min": 0.98,
    "abs_delta_macro_auc_upper95_max": 0.0005,
    "abs_delta_per_class_auc_upper95_max": 0.0015,
    "abs_delta_per_class_eff1pct_upper95_max": 0.010,
}
ARGMAX_BAR_NOTE = (
    "DEFECT IN THE PRE-REGISTERED GATE, corrected here (physics sign-off 2026-09-02): "
    "memo §5 pre-registers argmax_agreement >= 0.999, but the W8A8 realization the memo "
    "cites as its own precedent measured 0.98779 at n=4,096 -- as written the bar "
    "REJECTS the one realization already accepted on the record. Set to >= 0.98 (near "
    "the precedent). It is NOT a working-point guard: it is bulk-dominated and reads "
    "1.00000 even under top-5% saturation.")


def _bar_checks(block: dict):
    pb = block["paired_bootstrap"]
    wa = {k: v["abs_delta_upper95"] for k, v in pb["delta_per_class_auc"].items()}
    we = {k: v["abs_delta_upper95"]
          for k, v in pb["delta_per_class_eff_at_fpr_0.01"].items()}
    tie = block["tie_plateau_at_1pct_fpr"]["test"]
    checks = {
        "corr_scores": {"value": block["corr_scores"],
                        "bar": CANDIDATE_BARS["corr_scores_min"],
                        "pass": block["corr_scores"] >= CANDIDATE_BARS["corr_scores_min"]},
        "argmax_agreement": {"value": block["argmax_agreement"],
                             "bar": CANDIDATE_BARS["argmax_agreement_min"],
                             "pass": (block["argmax_agreement"]
                                      >= CANDIDATE_BARS["argmax_agreement_min"]),
                             "note": ARGMAX_BAR_NOTE},
        "abs_delta_macro_auc_upper95": {
            "value": pb["delta_macro_auc"]["abs_delta_upper95"],
            "bar": CANDIDATE_BARS["abs_delta_macro_auc_upper95_max"],
            "pass": (pb["delta_macro_auc"]["abs_delta_upper95"]
                     <= CANDIDATE_BARS["abs_delta_macro_auc_upper95_max"])},
        "worst_class_abs_delta_auc_upper95": {
            "value": max(wa.values()), "class": max(wa, key=wa.get),
            "per_class": wa,
            "bar": CANDIDATE_BARS["abs_delta_per_class_auc_upper95_max"],
            "pass": (max(wa.values())
                     <= CANDIDATE_BARS["abs_delta_per_class_auc_upper95_max"]),
            "note": "PROVISIONAL calibration, pending uncertainty-analyst ratification"},
        "worst_class_abs_delta_eff1pct_upper95": {
            "value": max(we.values()), "class": max(we, key=we.get),
            "per_class": we,
            "bar": CANDIDATE_BARS["abs_delta_per_class_eff1pct_upper95_max"],
            "pass": (max(we.values())
                     <= CANDIDATE_BARS["abs_delta_per_class_eff1pct_upper95_max"]),
            "note": "PROVISIONAL calibration, pending uncertainty-analyst ratification"},
        "no_tie_plateau_straddling_1pct": {
            "value": {k: v["straddles_target"] for k, v in tie.items()},
            "pass": not any(v["straddles_target"] for v in tie.values()),
            "note": ("a plateau straddling the target mistag rate destroys threshold "
                     "tunability -- deployment-fatal whatever the AUC says")},
    }
    checks["ALL_candidate_bars"] = {
        "pass": all(v["pass"] for k, v in checks.items() if k != "ALL_candidate_bars"),
        "note": ("recorded for convenience ONLY. This driver does NOT declare W*: the "
                 "per-class AUC and efficiency bars are provisional pending "
                 "uncertainty-analyst ratification.")}
    return checks


# --------------------------------------------------------------------------- #
# gate-set construction (nested, so the 4,096 set is a SUBSET of the big one)  #
# --------------------------------------------------------------------------- #
def load_nested_gate(data_dir, n_part, n_big, n_small, features=None):
    """Return (X, y, idx_small) where idx_small selects a nested n_small subset.

    The uncertainty sign-off (2026-09-02) requires the selection gate at n = 32,768 with
    the 4,096 comparison set NESTED inside it. `convert_binary._load_jets` takes an
    evenly-spaced linspace subsample of the val store; here the big set is that
    subsample and the small set is every (n_big/n_small)-th element of it. NOTE: the
    nested 4,096 is therefore NOT the same jet list as `convert_w8a8.py`'s
    linspace-4,096 -- it is a matched-n set from the same store, not a matched-jets set."""
    X, y = cf._load_jets(data_dir, n_part, n_big, features=features)
    n_big = len(X)
    step = max(1, n_big // n_small)
    idx_small = np.arange(0, n_big, step)[:n_small]
    return X, y, idx_small


# --------------------------------------------------------------------------- #
# one rung                                                                     #
# --------------------------------------------------------------------------- #
def run_rung(width, *, cfg, cfg_h, export_model, seed, tag, rf, strategy,
             weight_width=None,
             Xg, yg, idx_small, X_calib, run_root, n_csim, n_ebops, data_dir,
             input_std_rel, checkpoint_rel, meta, n_boot, fix_relu_parse,
             model_precision_override=None, pin_default_24_12=False,
             pack=True, std=None):
    """Convert + C-sim one ladder rung. Writes its artifacts as it goes."""
    w_w = int(width if weight_width is None else weight_width)
    leaf = (f"fp32-s{seed}" + (f"-{tag}" if tag else "")
            + (f"-w{width}" if w_w == int(width) else f"-w{w_w}a{width}"))
    run_dir = os.path.join(run_root, leaf)
    os.makedirs(run_dir, exist_ok=True)
    t0 = time.time()
    print(f"\n=== rung W={width} (weights W={w_w}, acts A={width})  -> {leaf} ===",
          flush=True)

    real_model, real_rec = build_realization(cfg, export_model, seed, width, X_calib,
                                             weight_width=w_w)
    grids = real_rec["weight_grids"]
    wbits = sorted({g["total_bits"] for g in grids.values()})
    print(f"[realization] W={width}: {len(grids)} weight grids "
          f"(total_bits={wbits}), {real_rec['act_calibration']['n_sites']} activation "
          f"sites calibrated on {real_rec['act_calibration']['n_calib_jets']} jets; "
          f"ported {real_rec['port']['n_kernels']}k/{real_rec['port']['n_biases']}b by "
          f"name ({real_rec['n_variables_export_fp32']} vars -> "
          f"{real_rec['n_variables_realization']} vars)", flush=True)

    if pin_default_24_12:
        model_precision = "fixed<24,12>"
        real_rec["model_precision_choice"] = "pinned fixed<24,12> (--pin-default-24-12)"
    elif model_precision_override:
        model_precision = model_precision_override
        real_rec["model_precision_choice"] = f"CLI override {model_precision}"
    else:
        model_precision = real_rec["model_precision"]
        real_rec["model_precision_choice"] = "widened-fallback rule (default)"
    real_rec["model_precision_used"] = model_precision
    cf._store(run_dir, "realization.json", real_rec)

    # ---- convert ----
    from bnhgq2.convert import convert, package_hls_project
    cf.patch_resource_einsum_check()
    if fix_relu_parse:
        cf.patch_relu_parse()
    out = os.path.join(run_dir, f"hls_prj_rf{rf}")
    csim_X = Xg[:n_csim]
    keras_ref = cf.predict(export_model, csim_X)         # the FLOAT export is the ref
    relu_fixed = {"n": 0}

    def _post_parse(hm):
        relu_fixed["n"] = cf.fix_relu_saturation(hm)

    hm, report = convert(real_model, cfg, out, rf=rf, strategy=strategy,
                         csim_X=csim_X, keras_ref=keras_ref, post_parse=_post_parse,
                         model_precision=model_precision)

    # ---- F6 read-back BEFORE any fidelity number is recorded ----
    audit = audit_fp32_firmware(out)
    f6 = check_realization_emitted(audit, real_model, grids, width)
    cf._store(run_dir, "firmware_audit.json", {"audit": audit, "f6": f6,
                                               "model_precision_used": model_precision})
    print(f"[F6] model_default_t={audit['model_default_t']} "
          f"einsum_dense={audit['n_einsum_dense']} dense={audit['n_dense']} "
          f"named weight typedefs={audit['n_weight_typedefs']} "
          f"model_default weight_t={audit['n_model_default_weight_t']} "
          f"-> pass={f6['pass']}", flush=True)
    if not f6["pass"]:
        raise SystemExit(
            f"STOP (falsifier F6): emitted precision cannot represent the W={width} "
            f"realization on layers {f6['offenders']}. The run would be measuring the "
            "hls4ml fallback, not the design. Not recording a fidelity number.")

    # ---- GATE 2 ----
    tp = time.time()
    y_big_h = np.asarray(hm.predict(np.ascontiguousarray(Xg.astype(np.float32))))
    t_pred = time.time() - tp
    y_big_e = cf.predict(export_model, Xg)
    y_big_h = y_big_h.reshape(y_big_e.shape)
    y_big_r = cf.predict(real_model, Xg)

    blocks = {
        "csim_vs_float_export__big":
            fidelity_block(y_big_e, y_big_h, yg, n_boot=n_boot,
                           label="C-sim vs FLOAT export (the realization cost)"),
        "csim_vs_float_export__n4096_nested":
            fidelity_block(y_big_e[idx_small], y_big_h[idx_small], yg[idx_small],
                           n_boot=n_boot,
                           label="C-sim vs FLOAT export, nested 4,096 (matched-n to "
                                 "the W8A8 precedent)"),
        "csim_vs_realization_keras__big":
            fidelity_block(y_big_r, y_big_h, yg, n_boot=0,
                           label="C-sim vs REALIZATION keras (port check: should be "
                                 "near-bit-exact under bit_exact=True)"),
        "realization_keras_vs_float_export__big":
            fidelity_block(y_big_e, y_big_r, yg, n_boot=n_boot,
                           label="REALIZATION keras vs FLOAT export (quantization cost "
                                 "alone, no hls4ml)"),
    }

    cs = report.get("csim", {})
    big = blocks["csim_vs_float_export__big"]
    sml = blocks["csim_vs_float_export__n4096_nested"]
    port = blocks["csim_vs_realization_keras__big"]

    csim_verify = {
        "config": cfg["name"], "config_hash": cfg_h, "variant": "fp32-realization",
        "width": int(width), "act_width": int(width), "weight_width": int(w_w),
        "seed": seed, "tag": tag, "rf": rf, "strategy": strategy,
        "backend": report.get("backend"),
        "macos_local_csim": platform.system() == "Darwin",
        "csim_headline_n128": cs,
        "candidate_bars": CANDIDATE_BARS,
        "gate2_rule": ("uncertainty sign-off 2026-09-02: the AUC bar is a paired-"
                       "bootstrap 95% UPPER BOUND on |delta macro-OvR AUC| at "
                       "n=32,768, not a point estimate -- |delta| <= 0.0005 is NOT "
                       "resolvable at n=4,096 (95% half-width 2.5e-4..4.4e-4 there). "
                       "The 4,096 block is reported for matched-n comparison with the "
                       "W8A8 precedent only. Physics sign-off 2026-09-02 adds per-class "
                       "|dOvR-AUC| (bar 0.0015) and per-class |d eps_S @ 1% FPR| (bar "
                       "0.010) as 95% upper bounds, plus the tie-plateau check at the "
                       "1%-mistag working point, because macro AUC is bulk-weighted and "
                       "blind to shoulder clipping by an MSE-calibrated static grid -- "
                       "which is exactly what the realization step is. Both added bars "
                       "are PROVISIONAL. NO W* is declared by this driver."),
        "argmax_bar_defect": ARGMAX_BAR_NOTE,
        "blocks": blocks,
        "relu_sat_fix": relu_fixed["n"],
        "relu_parse_fix": bool(fix_relu_parse),
        "widen_accum": False,
        "widen_accum_note": ("deliberately OFF: accumulator widening is the binary DSP-0 "
                             "trick; this baseline exists to measure real multipliers"),
        "csim_predict_seconds_big": t_pred,
    }
    cf._store(run_dir, "csim_verify.json", csim_verify)

    bc = big["candidate_bar_checks"]
    print(f"[GATE2] W={width} vs FLOAT export  n={big['n']}: "
          f"corr={big['corr_scores']:.6f} argmax={big['argmax_agreement']:.6f} "
          f"dAUC={big['delta_macro_auc']:+.6f} "
          f"|d|95<={big['paired_bootstrap']['delta_macro_auc']['abs_delta_upper95']:.6f} "
          f"max|d|logits={big['max_abs_diff_logits']:.4g}", flush=True)
    print(f"[GATE2] W={width} worst class: "
          f"AUC {bc['worst_class_abs_delta_auc_upper95']['class']} "
          f"|d|95<={bc['worst_class_abs_delta_auc_upper95']['value']:.6f} | "
          f"eps@1%FPR {bc['worst_class_abs_delta_eff1pct_upper95']['class']} "
          f"|d|95<={bc['worst_class_abs_delta_eff1pct_upper95']['value']:.5f} | "
          f"deps(g)={big['signal_efficiency_at_fixed_mistag']['fpr_0.01']['delta']['g']:+.5f} "
          f"| tie-plateau straddles: "
          f"{[k for k, v in bc['no_tie_plateau_straddling_1pct']['value'].items() if v]}",
          flush=True)
    print(f"[GATE2] W={width} vs FLOAT export  n={sml['n']} (nested): "
          f"corr={sml['corr_scores']:.6f} argmax={sml['argmax_agreement']:.6f} "
          f"dAUC={sml['delta_macro_auc']:+.6f} "
          f"|d|95<={sml['paired_bootstrap']['delta_macro_auc']['abs_delta_upper95']:.6f}",
          flush=True)
    print(f"[PORT ] W={width} C-sim vs realization keras: "
          f"corr={port['corr_scores']:.6f} max|d|={port['max_abs_diff_logits']:.4g} "
          f"bit_exact={port['bit_exact']}", flush=True)

    tar = package_hls_project(out, out + ".tar.gz") if pack else None

    convert_rec = {
        "config_hash": cfg_h, "variant": "fp32-realization", "width": int(width),
        "act_width": int(width), "weight_width": int(w_w),
        "seed": seed, "tag": tag,
        "output_dir": os.path.relpath(out, PROJECT_ROOT),
        "tarball": (os.path.relpath(tar, PROJECT_ROOT) if tar else None),
        "rf": rf, "strategy": strategy,
        "rf_note": (f"ReuseFactor OVERRIDDEN to {rf}; the config carries "
                    f"hls.rf={cfg['hls'].get('rf')} which is NOT the comparator"),
        "realization": "PTQ static grids at width W (memo reading (b)); NOT float silicon",
        "model_precision_used": model_precision,
        "part": cfg["hls"].get("part"), "clock_ns": cfg["hls"].get("clock_ns"),
        "io": cfg["hls"].get("io"),
        "checkpoint": checkpoint_rel, "input_std": input_std_rel, "train_meta": meta,
        "firmware_audit": audit, "f6": f6,
        "stage": "convert + C-sim only (LOCAL) -- no synthesis was run by this driver",
        "synthesis_command": ("vitis_hls -f build_prj.tcl" if tar else None),
    }
    cf._store(run_dir, "convert.json", convert_rec)

    # ---- EBOPs LAST ----
    ebops_total = None
    if n_ebops:
        from bnhgq2.ebops_calc import compute_ebops
        Xe, _ = cf._load_jets(data_dir, cfg["arch"]["n_part"], n_ebops,
                              features=cfg["arch"].get("features"))
        if std is not None:
            from bnhgq2.data import apply_input_std
            Xe = apply_input_std(Xe, std["mu"], std["sigma"])
        eb = compute_ebops(real_model, Xe)
        eb.update({"config": cfg["name"], "config_hash": cfg_h,
                   "variant": "fp32-realization", "width": int(width), "seed": seed,
                   "convention": "HGQ2_native_trace_minmax",
                   "order_note": "computed AFTER conversion + gates"})
        cf._store(run_dir, "ebops.json", eb)
        ebops_total = eb["total"]
        print(f"[EBOPs] W={width} total = {ebops_total:,}", flush=True)

    dt = time.time() - t0
    print(f"[rung ] W={width} done in {dt/60:.1f} min -> "
          f"{os.path.relpath(run_dir, PROJECT_ROOT)}", flush=True)

    return {
        "width": int(width), "act_width": int(width), "weight_width": int(w_w),
        "run_dir": os.path.relpath(run_dir, PROJECT_ROOT),
        "leaf": leaf, "seconds": dt, "f6_pass": f6["pass"],
        "weight_grid_total_bits": wbits,
        "model_precision_used": model_precision,
        "ebops": ebops_total,
        "csim_n128": cs,
        "vs_float_export_big": big,
        "vs_float_export_n4096_nested": sml,
        "csim_vs_realization_keras": {k: port[k] for k in
                                      ("n", "corr_scores", "max_abs_diff_logits",
                                       "argmax_agreement", "bit_exact")},
        "realization_keras_vs_float_export":
            {k: blocks["realization_keras_vs_float_export__big"][k] for k in
             ("n", "corr_scores", "argmax_agreement", "delta_macro_auc")},
        "candidate_bar_checks_big": big["candidate_bar_checks"],
    }


# --------------------------------------------------------------------------- #
# driver                                                                       #
# --------------------------------------------------------------------------- #
def run_fp32_ladder(seed: int, *, widths=LADDER_DEFAULT, checkpoint=None, tag=None,
                    rf=1, strategy="Latency", n_gate=32768, n_gate_small=4096,
                    n_csim=128, n_ebops=4096, n_boot=1000, data_dir=None,
                    store_root=None, run_root=None, config_path=None,
                    input_std_path=None, fix_relu_parse=False,
                    model_precision=None, pin_default_24_12=False, pack=True,
                    weight_width=None):
    cfg_path = config_path or os.path.join(_HERE, "configs", "pre_conference-n8-fp32.json")
    cfg = load_config(cfg_path)
    if cfg["quant"]["weight"] != "none":
        raise SystemExit(f"{cfg['name']}: convert_fp32 only converts quant.weight='none' "
                         f"(FP32) configs; got {cfg['quant']['weight']!r}")
    h = cfg_hash(cfg)
    A = cfg["arch"]
    data_dir = data_dir or os.path.join(PROJECT_ROOT, "data", "val")
    store_root = store_root or os.path.join(PROJECT_ROOT, "results", "synthesis")
    run_root = run_root or os.path.join(store_root, "runs", h)
    os.makedirs(run_root, exist_ok=True)

    # ---- PREFLIGHT-3: checkpoint + input_std ----
    kp = os.path.abspath(checkpoint or os.path.join(
        PROJECT_ROOT, "outputs", "models", "cache", f"pre_conference-n8-fp32-s{seed}",
        "model_best.keras"))
    if not os.path.isfile(kp):
        raise SystemExit(f"checkpoint not found: {kp}")
    mp = os.path.join(os.path.dirname(kp), "train_meta.json")
    meta = json.load(open(mp)) if os.path.isfile(mp) else {}
    if input_std_path is None:
        cand = os.path.join(os.path.dirname(kp), "input_std.json")
        input_std_path = cand if os.path.isfile(cand) else None
    import hashlib
    ck_sha = hashlib.sha256(open(kp, "rb").read()).hexdigest()

    rel = (lambda p: os.path.relpath(p, PROJECT_ROOT) if p and p.startswith(PROJECT_ROOT)
           else p)
    print(f"=== convert_fp32 ladder  cfg={cfg['name']} [{h}] seed={seed} "
          f"widths={list(widths)} rf={rf} strategy={strategy} ===", flush=True)
    print(f"[ckpt] {rel(kp)}\n       sha256={ck_sha} size={os.path.getsize(kp)}",
          flush=True)

    qat_model = cf.load_qat_model(kp)
    print(f"[load] params={qat_model.count_params():,} "
          f"variables={len(qat_model.variables)}", flush=True)

    # ---- gate data (nested) + calibration data ----
    Xg, yg, idx_small = load_nested_gate(data_dir, A["n_part"], n_gate, n_gate_small,
                                         features=A.get("features"))
    calib_n = int(cfg["quant"].get("calib_n", 8192))
    Xc, _yc = cf._load_jets(data_dir, A["n_part"], calib_n, features=A.get("features"))
    std = None
    if input_std_path:
        from bnhgq2.data import apply_input_std
        std = json.load(open(input_std_path))
        Xg = apply_input_std(Xg, std["mu"], std["sigma"])
        Xc = apply_input_std(Xc, std["mu"], std["sigma"])
        print(f"[data] input_std applied from {rel(input_std_path)} (input-standardized model contract)",
              flush=True)
    print(f"[data] gate n={len(Xg)} (nested small n={len(idx_small)}), "
          f"calib n={len(Xc)}, from {rel(data_dir)}", flush=True)

    # ---- step 2: EXPORT + GATE 1 (shared by every rung) ----
    export_model, n_ported, pos_max = build_fp32_export(cfg, qat_model, seed)
    g1 = cf.gate1(qat_model, export_model, Xg[idx_small])
    # every variable is a straight copy on this path; the only float operation is the
    # (bias + pos) reassociation, so the port residual must be exactly 0
    wmax = 0.0
    for ly in export_model.layers:
        kv = getattr(ly, "_kernel", None)
        if kv is None:
            continue
        wmax = max(wmax, float(np.abs(cf._to_np(kv) -
                                      cf._to_np(_kernel_var(qat_model.get_layer(ly.name)))
                                      ).max()))
    g1["weight_port_max_abs_diff"] = wmax
    g1_pass = g1["corr_scores"] >= 0.997
    print(f"[GATE1] export vs FP32 QAT: corr_scores={g1['corr_scores']:.6f} "
          f"corr_logits={g1['corr_logits']:.6f} argmax={g1['argmax_agreement']:.6f} "
          f"weight|d|={wmax:.3e} pass={g1_pass}", flush=True)
    if g1["corr_scores"] < 0.9999 or wmax != 0.0:
        raise SystemExit("STOP: GATE1 below the 0.9999 sanity bar (or the kernels are "
                         "not exact copies). There is NO quantization on this path -- "
                         "the export IS the trained function up to the (bias + pos) "
                         "float reassociation, so anything lower is a porting bug. "
                         "Not writing artifacts.")

    export_verify = {
        "config": cfg["name"], "config_hash": h, "variant": "fp32", "seed": seed,
        "tag": tag, "checkpoint": rel(kp), "checkpoint_sha256": ck_sha,
        "checkpoint_bytes": os.path.getsize(kp), "train_meta": meta,
        "checkpoint_path_note": ("the design memo's §9 names "
                                 "results/predictions/pre_conference/n8/_ckpt_dl/fp32-s3/model_best.keras; "
                                 "the verified artifact is at "
                                 "outputs/models/cache/pre_conference-n8-fp32-s3/ "
                                 "(corrected 2026-09-02)"),
        "mechanism": ("FP32 QAT graph (dummy quantizers, no datapath) rebuilt WITHOUT "
                      "the AddPositional layer (build_qat_model with_pos_enc=False), "
                      "all variables copied per layer, the trained (T,D) pos table "
                      "folded into input_proj's bias_axes='td' bias"),
        "pos_fold": {"max_abs_pos": pos_max, "layers_ported": n_ported},
        "n_variables_qat": len(qat_model.variables),
        "n_variables_export": len(export_model.variables),
        "input_std": rel(input_std_path),
        "gate1": g1, "gate1_pass": bool(g1_pass), "gate1_threshold": 0.997,
        "gate1_abort_bar": 0.9999,
        "gate1_scope": ("STRUCTURAL PORT ONLY. The realization (width-W static grids) "
                        "is a SEPARATE, LABELLED step and its error is charged to "
                        "GATE 2, not here."),
        "gate_data": {"n_big": int(len(Xg)), "n_small": int(len(idx_small)),
                      "nested": True, "calib_n": int(len(Xc)),
                      "overlap_note": ("the gate jets are drawn from the same data/val "
                                       "store as the calibration jets -- recorded as a "
                                       "caveat, not corrected, because it matches the "
                                       "W8A8 comparator's practice")},
    }
    cf._store(run_root, f"fp32-s{seed}" + (f"-{tag}" if tag else "") +
              "-export_verify.json", export_verify)

    # ---- the ladder ----
    ladder_path = os.path.join(
        run_root, f"fp32-s{seed}" + (f"-{tag}" if tag else "") + "-ladder.json")
    rungs, failures = [], []
    for W in widths:
        try:
            r = run_rung(W, cfg=cfg, cfg_h=h, export_model=export_model, seed=seed,
                         weight_width=weight_width,
                         tag=tag, rf=rf, strategy=strategy, Xg=Xg, yg=yg,
                         idx_small=idx_small, X_calib=Xc, run_root=run_root,
                         n_csim=n_csim, n_ebops=n_ebops, data_dir=data_dir,
                         input_std_rel=rel(input_std_path), checkpoint_rel=rel(kp),
                         meta=meta, n_boot=n_boot, fix_relu_parse=fix_relu_parse,
                         model_precision_override=model_precision,
                         pin_default_24_12=pin_default_24_12, pack=pack, std=std)
            rungs.append(r)
        except SystemExit as e:                       # a rung failing is DATA, not a crash
            print(f"[rung ] W={W} ABORTED: {e}", flush=True)
            failures.append({"width": int(W), "error": str(e)})
        # incremental save after every rung -- this machine has slept mid-run before
        cf._store(run_root, os.path.basename(ladder_path),
                  _ladder_record(cfg, h, seed, tag, rf, strategy, widths, rungs,
                                 failures, export_verify, len(Xg), len(idx_small),
                                 n_boot))

    print("\n" + _ladder_table(rungs), flush=True)
    print(f"\n[done] ladder -> {os.path.relpath(ladder_path, PROJECT_ROOT)}", flush=True)
    return {"rungs": rungs, "failures": failures, "ladder": ladder_path}


def _ladder_record(cfg, h, seed, tag, rf, strategy, widths, rungs, failures,
                   export_verify, n_big, n_small, n_boot):
    return {
        "config": cfg["name"], "config_hash": h, "seed": seed, "tag": tag,
        "rf": rf, "strategy": strategy, "widths_requested": list(widths),
        "weight_width_override": (None if not rungs else rungs[0].get("weight_width")),
        "stage": "LOCAL convert + C-sim only. Nothing was synthesized.",
        "realization_label": ("wide ap_fixed realization of the FP32-TRAINED network "
                              "(design memo reading (b)). Literal float silicon is NOT "
                              "measured and is not planned."),
        "gate1": export_verify["gate1"],
        "gate_data": {"n_big": n_big, "n_small_nested": n_small},
        "selection": {
            "declared": False,
            "why": ("W* is deliberately NOT declared here. The physics sign-off on "
                    "whether macro-OvR AUC or signal efficiency at a low fixed mistag "
                    "rate is the right quantity was still outstanding when this ladder "
                    "ran; every rung therefore carries per-class AUC, per-class "
                    "efficiency at FPR 1e-2 and 1e-3, correlations, argmax agreement "
                    "and a paired-bootstrap interval, so any bar can be applied "
                    "afterwards without re-running."),
            "candidate_bars": CANDIDATE_BARS,
            "candidate_bar_provenance": {
                "corr_scores_min": "memo §5",
                "argmax_agreement_min": ARGMAX_BAR_NOTE,
                "abs_delta_macro_auc_upper95_max": (
                    "memo §5 value 0.0005, but as a paired-bootstrap 95% UPPER bound at "
                    "n=32,768 rather than a point estimate at n=4,096 "
                    "(uncertainty sign-off 2026-09-02)"),
                "abs_delta_per_class_auc_upper95_max": (
                    "physics sign-off 2026-09-02, PROVISIONAL pending uncertainty "
                    "ratification (measured per-class SE 0.62e-4..0.99e-4 at n=32,768)"),
                "abs_delta_per_class_eff1pct_upper95_max": (
                    "physics sign-off 2026-09-02, PROVISIONAL pending uncertainty "
                    "ratification (measured SE 0.0020..0.0035 at n=32,768). Macro AUC is "
                    "bulk-weighted and blind to shoulder clipping: top-3% saturation "
                    "passes corr/argmax/macro-AUC while the working point degrades."),
                "tie_plateau": ("no class may have a tie plateau straddling the 1% "
                                "mistag rate -- that destroys threshold tunability"),
            },
            "n_boot": n_boot,
        },
        "rungs": rungs, "failures": failures,
    }


def _ladder_table(rungs):
    """The per-rung ladder. Every bar shown is CANDIDATE; no W* is chosen here."""
    hdr = (f"{'W':>3} {'wbits':>9} {'corr':>9} {'argmax':>8} {'dAUC32k':>9} "
           f"{'|dA|95':>8} {'dAUC4k':>9} {'|dA|95_4k':>9} "
           f"{'wcAUC':>6} {'|d|95':>8} {'wcEff':>6} {'|d|95':>8} "
           f"{'d.eps(g)':>9} {'plateau':>8} {'bars':>5}")
    lines = [hdr, "-" * len(hdr)]
    for r in rungs:
        b, sm = r["vs_float_export_big"], r["vs_float_export_n4096_nested"]
        bc = r["candidate_bar_checks_big"]
        wa, we = bc["worst_class_abs_delta_auc_upper95"], bc["worst_class_abs_delta_eff1pct_upper95"]
        pl = [k for k, v in bc["no_tie_plateau_straddling_1pct"]["value"].items() if v]
        lines.append(
            f"{r['width']:>3} {str(r['weight_grid_total_bits']):>9} "
            f"{b['corr_scores']:>9.6f} {b['argmax_agreement']:>8.5f} "
            f"{b['delta_macro_auc']:>+9.6f} "
            f"{b['paired_bootstrap']['delta_macro_auc']['abs_delta_upper95']:>8.6f} "
            f"{sm['delta_macro_auc']:>+9.6f} "
            f"{sm['paired_bootstrap']['delta_macro_auc']['abs_delta_upper95']:>9.6f} "
            f"{wa['class']:>6} {wa['value']:>8.6f} {we['class']:>6} {we['value']:>8.5f} "
            f"{b['signal_efficiency_at_fixed_mistag']['fpr_0.01']['delta']['g']:>+9.5f} "
            f"{(','.join(pl) or '-'):>8} "
            f"{('PASS' if bc['ALL_candidate_bars']['pass'] else 'fail'):>5}")
    lines += ["",
              "wbits  = distinct total weight-grid widths across the 15 weighted layers",
              "dAUC   = paired delta macro-OvR AUC (C-sim minus float export)",
              "|dA|95 = paired-bootstrap 95% UPPER bound on |delta macro AUC|",
              "wcAUC  = worst class by |delta per-class OvR AUC| upper95 (bar 0.0015, PROVISIONAL)",
              "wcEff  = worst class by |delta eps_S @ 1% FPR| upper95 (bar 0.010, PROVISIONAL)",
              "d.eps(g) = delta signal efficiency at 1% mistag for the exposed class g",
              "plateau = classes whose tie plateau STRADDLES the 1% mistag rate (untunable)",
              "bars   = all candidate bars simultaneously; NOT a selection of W*."]
    return "\n".join(lines)


def _self_test():
    """Cheap local checks that need no model: the grid rule, the container check and
    _auc_fast vs sklearn."""
    from sklearn.metrics import roc_auc_score
    rng = np.random.default_rng(0)
    for W in (8, 12, 16, 20, 24):
        for a in (0.03, 0.3, 0.97, 1.0, 1.5, 3.7, 9.9):
            i, f = grid_from_absmax(a, W)
            assert f == W - 1 - i, (W, a, i, f)
            assert kif_grid(i, f)[2] >= a - 1e-12, (W, a, i, f)
            if i > -8:
                assert kif_grid(i - 1, f + 1)[2] < a, ("not narrowest", W, a, i)
    p = parse_prec("ap_fixed<24,12,AP_RND_CONV,AP_SAT>")
    assert p == {"raw": "ap_fixed<24,12,AP_RND_CONV,AP_SAT>", "signed": True,
                 "width": 24, "integer": 12}, p
    v = quantize_kif(rng.normal(size=1000), 0, 7)
    assert container_holds(v, {"width": 24, "integer": 12, "signed": True}) == 0.0
    assert container_holds(quantize_kif(rng.normal(size=1000), 0, 15),
                           {"width": 24, "integer": 12, "signed": True}) > 0.0
    y = (rng.random(5000) < 0.3).astype(int)
    s = rng.random(5000) + 0.4 * y
    assert abs(_auc_fast(y, s) - roc_auc_score(y, s)) < 1e-12
    s2 = np.round(s * 4) / 4                     # heavy ties
    assert abs(_auc_fast(y, s2) - roc_auc_score(y, s2)) < 1e-12
    wp = _wp()                                   # the verbatim working-point function
    t01, _r, _c = wp(y, s)
    assert 0.0 <= t01[0.01] <= 1.0 and 0.0 <= t01[0.10] <= 1.0
    tp_fine = tie_plateau(y, s, 0.01)
    tp_coarse = tie_plateau(y, np.round(s * 8) / 8, 0.01)
    assert tp_fine["tie_fraction_all"] < tp_coarse["tie_fraction_all"]
    assert tp_coarse["straddles_target"] and not tp_fine["straddles_target"]
    print("self-test OK "
          f"(coarse-grid tie fraction {tp_coarse['tie_fraction_all']:.3f} "
          f"straddles={tp_coarse['straddles_target']})")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--widths", default=",".join(str(w) for w in LADDER_DEFAULT),
                    help="ladder widths, comma separated (memo §5: 8,12,16,20,24; "
                         "extend to 28,32 one step at a time only if needed)")
    ap.add_argument("--checkpoint", default=None,
                    help="local model_best.keras (default: models/cache/"
                         "pre_conference-n8-fp32-s<seed>/model_best.keras)")
    ap.add_argument("--config", default=None)
    ap.add_argument("--tag", default=None, help="results leaf suffix, e.g. 'pre_conference_n8'")
    ap.add_argument("--rf", type=int, default=1,
                    help="ReuseFactor. Default 1 -- the comparator. The config's "
                         "hls.rf=256 is deliberately OVERRIDDEN.")
    ap.add_argument("--strategy", default="Latency")
    ap.add_argument("--n-gate", type=int, default=32768,
                    help="selection gate size (uncertainty sign-off 2026-09-02)")
    ap.add_argument("--n-gate-small", type=int, default=4096,
                    help="nested subset reported for matched-n comparison with W8A8")
    ap.add_argument("--n-csim", type=int, default=128)
    ap.add_argument("--n-ebops", type=int, default=4096, help="0 disables EBOPs")
    ap.add_argument("--n-boot", type=int, default=1000)
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--run-root", default=None)
    ap.add_argument("--store-root", default=None)
    ap.add_argument("--input-std", default=None)
    ap.add_argument("--fix-relu-parse", action="store_true")
    ap.add_argument("--model-precision", default=None,
                    help="override the hls4ml Model fallback Precision string")
    ap.add_argument("--pin-default-24-12", action="store_true",
                    help="control arm: pin the fallback to the historical fixed<24,12> "
                         "(expected to TRIP falsifier F6 for W >= 14 -- the EinsumDense "
                         "weight container would truncate to 12 fractional bits)")
    ap.add_argument("--weight-width", type=int, default=None,
                    help="decouple the WEIGHT grid width from the activation width. "
                         "Default None == weight width equals --widths (every "
                         "historical invocation is byte-identical). Set it to build a "
                         "WEIGHT-WIDTH-MATCHED control: activations stay at --widths "
                         "(the comparator's operand width) while the intW_absmax weight "
                         "lattice moves alone (design memo CORRECTION C1.3).")
    ap.add_argument("--no-pack", action="store_true", help="skip HLS project packaging")
    ap.add_argument("--self-test", action="store_true",
                    help="run the model-free unit checks and exit")
    a = ap.parse_args()
    if a.self_test:
        _self_test()
        return
    widths = tuple(int(w) for w in a.widths.split(",") if w.strip())
    run_fp32_ladder(a.seed, widths=widths, checkpoint=a.checkpoint, tag=a.tag,
                    rf=a.rf, strategy=a.strategy, n_gate=a.n_gate,
                    n_gate_small=a.n_gate_small, n_csim=a.n_csim, n_ebops=a.n_ebops,
                    n_boot=a.n_boot, data_dir=a.data_dir, run_root=a.run_root,
                    weight_width=a.weight_width,
                    store_root=a.store_root, config_path=a.config,
                    input_std_path=a.input_std, fix_relu_parse=a.fix_relu_parse,
                    model_precision=a.model_precision,
                    pin_default_24_12=a.pin_default_24_12, pack=not a.no_pack)


if __name__ == "__main__":
    main()
