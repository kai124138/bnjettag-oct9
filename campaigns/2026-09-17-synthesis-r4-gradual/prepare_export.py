"""Faithful R4 learned-width export; no training and no vendor synthesis here.

Run with the existing HGQ2 environment and publication/code/hgq2 on PYTHONPATH.
The legacy exporter rebuilds eight-bit dense inputs. This adapter copies the
effective learned KIF grids and sizes affine carry grids analytically instead.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time
import importlib.metadata
import tarfile

import numpy as np
import keras
from bnhgq2.compat import apply_keras_compat
import bnhgq2.qat
from bnhgq2.ebops_calc import compute_ebops
from convert_binary import (qat_binz_pe, read_qat_act_ibits, qat_stream_ranges,
                            build_export, gate1, predict, patch_relu_parse,
                            fix_relu_saturation, patch_resource_einsum_check)


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def package_project(project, archive):
    # Python tar avoids macOS AppleDouble siblings outside the project root;
    # Linux compilation rebuilds native libraries, so do not ship Mach-O files.
    def source_only(info):
        if any(p.startswith("._") for p in Path(info.name).parts) or info.name.endswith(".so"):
            return None
        return info
    with tarfile.open(archive, "w:gz") as tar:
        tar.add(project, arcname="hls_prj_rf1", filter=source_only)


def scalar_grid(iq):
    values = [np.asarray(v) for v in iq.quantizer.kif]
    assert all(np.unique(v).size == 1 for v in values), "per-tensor adapter only"
    return [int(v.flat[0]) for v in values]


def set_grid(iq, grid):
    for name, value in zip(("_k", "_i", "_f"), grid):
        var = getattr(iq.quantizer, name)
        var.assign(np.full(var.shape, value, dtype=np.float32))
    assert scalar_grid(iq) == grid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--csim", action="store_true")
    ap.add_argument("--trace", action="store_true")
    args = ap.parse_args()
    root = args.root.resolve()
    src = root / "source"
    out = root / "export"
    out.mkdir(exist_ok=True)
    apply_keras_compat()
    cfg = json.loads((src / "config.json").read_text())
    assert cfg["experiment"]["arm"] == "r4-gradual"
    assert cfg["arch"]["norm"] == "none"
    cfg["hls"].update(rf=1, clock_ns=2.5, backend="Vitis", io="io_parallel")
    model = keras.models.load_model(src / "model_best.keras", compile=False)
    x = np.load(src / "x_gate.npy")
    assert x.shape == (4096, 8, 3) and np.isfinite(x).all()
    binz, pe, names = qat_binz_pe(model, cfg)
    kernel_audit = {}
    for name in names:
        effective = np.asarray(model.get_layer(name).qkernel)
        signs = np.asarray(binz[name]["q"]).reshape(effective.shape)
        assert np.array_equal(np.sign(effective), signs), name
        kernel_audit[name] = {"sign_match": True,
                             "effective_kernel_max_error": float(np.max(np.abs(
                                 effective - signs * np.float32(binz[name]["beta"]))))}
    calib = read_qat_act_ibits(model, names)
    calib.update(qat_stream_ranges(model, cfg, binz, x[:2048]))
    exported = build_export(cfg, binz, calib, pe, beta_mode="exact", qat_model=model)
    grids = {}
    for name in names:
        trained = model.get_layer(name)
        dense = exported.get_layer(name)
        grid = scalar_grid(trained.iq)
        set_grid(dense.iq, grid)
        # A pure-sign contraction adds at most fanin inputs. Its fractional
        # grid is unchanged. Input projection also carries the folded PE bias.
        shape = binz[name]["q"].shape
        fanin = int(shape[0] if name.endswith(("_Wq", "_Wk", "_Wv"))
                    else np.prod(shape[:-1]))
        bound = fanin * 2.0 ** grid[1]
        frac = grid[2]
        if name == "input_proj":
            bound += float(np.max(np.abs(np.asarray(dense.bias)))) + 1.0
            frac = max(frac, 16)
        carry = [1, int(np.ceil(np.log2(max(bound, 1e-12)))) + 1, frac]
        set_grid(exported.get_layer(name + "_affine").iq, carry)
        grids[name] = {"trained_kif": grid, "export_kif": scalar_grid(dense.iq),
                       "width": sum(grid), "carry_kif": carry, "fanin": fanin}
    write(out / "learned_grids.json", grids)
    g1 = gate1(model, exported, x)
    # Correlation alone can hide class-decision changes. Require both.
    g1["pass"] = bool(g1["corr_scores"] >= 0.997 and g1["argmax_agreement"] >= 0.995)
    g1["thresholds"] = {"score_correlation": 0.997, "argmax_agreement": 0.995}
    report = {"run": "ebops-n8-20260912-ablation-r4-gradual-w1a8-s1",
              "checkpoint_sha256": hashlib.sha256((src / "model_best.keras").read_bytes()).hexdigest(),
              "sample_sha256": hashlib.sha256((src / "x_gate.npy").read_bytes()).hexdigest(),
              "sample": "first 4096 internal-validation jets, already training-standardized",
              "rf": 1, "clock_ns": 2.5, "hls_part": cfg["hls"]["part"],
              "beta_mode": "exact constants, legacy affine quantizer fractional width 16",
              "gate1": g1, "kernel_audit": kernel_audit,
              "versions": {p: importlib.metadata.version(p) for p in
                           ("keras", "numpy", "tensorflow", "hgq2", "hls4ml", "quantizers")}}
    print("GATE1", json.dumps(g1), flush=True)
    # Cost tracing is deliberately after the gate, on the reference model only.
    report["native_checkpoint_ebops"] = compute_ebops(model, x[:2048])["total"]
    assert report["native_checkpoint_ebops"] == 349550
    write(out / "verification.json", report)
    write(out / "hardware_config.json", cfg)
    if not g1["pass"]:
        raise SystemExit("Export fidelity failed: synthesis prohibited")
    if not args.csim:
        return
    from bnhgq2.convert import convert
    patch_resource_einsum_check()
    patch_relu_parse()
    ref = predict(exported, x)
    np.save(out / "csim_inputs.npy", x)
    np.save(out / "csim_reference.npy", ref)
    def post_parse(hm):
        fix_relu_saturation(hm)
        # hls4ml 1.3.0 turns a ReLU followed by signed KIF(1,0,0)
        # (levels {-1,0}, therefore identically zero on ReLU outputs) into
        # unsigned fixed<1,0> (levels {0,0.5}). Preserve the original signed
        # saturating cast so every nonnegative input correctly becomes zero.
        from hls4ml.model.types import RoundingMode, SaturationMode
        fixes = []
        by = {l.name: l for l in hm.get_layers()}
        for li in range(cfg["arch"]["n_layers"]):
            name = f"bit_block_{li}_ffn_fc2"
            if grids[name]["trained_kif"] != [1, 0, 0]:
                continue
            relu_name = f"bit_block_{li}_ffn_act"
            node = by[relu_name]
            assert node.get_attr("activation") == "relu"
            p = node.get_output_variable().type.precision
            p.width, p.integer, p.signed = 1, 1, True
            p.rounding_mode, p.saturation_mode = RoundingMode.RND_CONV, SaturationMode.SAT
            fixes.append({"node": relu_name, "reason": "ReLU followed by signed {-1,0} quantizer is zero"})
        report["zero_grid_repairs"] = fixes
    hm, conversion = convert(exported, cfg, str(out / "hls_prj_rf1"), rf=1,
                             strategy="Latency", csim_X=x, keras_ref=ref,
                             post_parse=post_parse,
                             layer_configs=({l.name: {"Trace": True} for l in exported.layers}
                                            if args.trace else None))
    # The gate is strict bit equality, not merely correlated outputs.
    cs = conversion["csim"]
    report["gate2"] = cs
    report["gate2_pass"] = bool(cs["bit_exact"])
    write(out / "verification.json", report)
    print("GATE2", json.dumps(cs), flush=True)
    if args.trace:
        # trace() rewrites the project; retain the existing macOS header repair.
        import platform
        if platform.system() == "Darwin":
            from bnhgq2.compat import patch_project_for_macos
            original_write = hm.write
            def patched_write():
                original_write()
                patch_project_for_macos(out / "hls_prj_rf1")
            hm.write = patched_write
        _, traces = hm.trace(np.ascontiguousarray(x[:32]))
        probe = keras.Model(exported.inputs, [l.output for l in exported.layers])
        values = probe(x[:32], training=False)
        records = []
        for layer, value in zip(exported.layers, values):
            if layer.name not in traces:
                continue
            a = np.asarray(value)
            b = np.asarray(traces[layer.name]).reshape(a.shape)
            records.append({"layer": layer.name, "max_diff": float(np.abs(a-b).max()),
                            "mean_diff": float(np.abs(a-b).mean()),
                            "keras_range": [float(a.min()),float(a.max())],
                            "hls_range": [float(b.min()),float(b.max())]})
        write(out / "trace_differences.json", records)
        print("TRACE", json.dumps(records), flush=True)
    if not report["gate2_pass"]:
        raise SystemExit("C simulation not bit-exact: synthesis prohibited")
    package_project(out / "hls_prj_rf1", out / "hls_prj_rf1.tar.gz")
    report["hls_archive_sha256"] = hashlib.sha256((out / "hls_prj_rf1.tar.gz").read_bytes()).hexdigest()
    write(out / "verification.json", report)
    print("EXPORT_READY_FOR_SYNTHESIS", flush=True)


if __name__ == "__main__":
    main()
