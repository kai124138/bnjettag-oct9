"""E-A′ — the 8-bit denominator at layer scale (COMPILER.md lane, 2026-07-25).

The whole project prices binary weights against nothing: all 16 whole-model
csynth XMLs are W1 variants, and no W8A8 synthesis exists at any scale.  Since
the capacity study showed 8-bit weights are accuracy-free at every scale
measured (96-106% of FP32 rejection from 5.3k to 6.4M params), the binary design
point is only defensible if 8-bit weights are materially more expensive in
hardware.  Nobody has measured that here.

This emits the CHEAPEST honest version of that measurement: the same layer, the
same emission style, the same fixed-point types, changing ONLY the weights.

  P8  naive spatial x10, real trained 8-bit weights   -> vs E1 arm P (270,382 LUT)
  A8  token-folded x10, II=10, same weights           -> vs E1 arm A  (29,029 LUT)

P8/P is the weight-precision cost per MAC at matched emission.  A8/P8 tests a
claim the fold program has been ASSUMING but never measured: that folding is
precision-agnostic (it deletes physical instances, so it should give ~10x for any
weight width).  If folding helps binary more than 8-bit, that is a new and
separate argument for binary; if it helps both equally, the precision comparison
is unaffected by the compiler and can be made at layer scale.

Weights: `bit_block_0_ffn_fc1` of the round-8 W8A8-std flagship (W&B
`r8-small-w8a8-std-s2`, ROC-test 0.9151 +- 0.0009), passed through the layer's
own trained weight quantizer, i.e. the values that would be deployed.  Measured:
22 distinct levels on a 1/32 grid, integers in [-11, +11] -- the "8-bit" weights
occupy ~4.5 effective bits, so a naive "8x an XNOR" intuition is NOT safe and
the constant multipliers may be much cheaper than a general 8x8 product.

Exactness: weights are c/32 (5 frac bits), inputs ap_fixed<8,4> (4 frac bits), so
every product has 9 frac bits and |row sum| <= 32 * (11/32) * 8 = 88.  The E1
accumulator ap_fixed<26,10> (16 frac, int range +-512) covers both exactly, so
the 8-bit arms reuse the binary arms' types UNCHANGED -- the only difference
between P8 and P is the weight values.

Usage: .venv-hgq2/bin/python bnjettag/code/analysis/e1_w8_emit.py
Output: bnjettag/results/adder-graph/e1w8/{p8,a8}/ + run_all.sh
"""

from pathlib import Path

import numpy as np

import e1_emit as E1

REPO = Path(__file__).resolve().parents[2]
CKPT = REPO / "r7/models/w8a8-std-s2/small-w8a8std-s2/model_best.keras"
OUT = REPO / "results/adder-graph/e1w8"
LAYER = "bit_block_0_ffn_fc1"
GRID = 32.0                      # 1/32 = the measured deployed weight step (5 frac bits)
BIAS_FRAC = 16                   # ap_fixed<18,2> -> 16 fractional bits


def load_w8_layer():
    """Deployed 8-bit kernel + bias for LAYER, as exact multiples of 1/GRID."""
    import sys
    sys.path.insert(0, str(REPO / "code/hgq2"))
    import roc_final
    roc_final._prepare_env()
    import keras

    m = keras.models.load_model(str(CKPT), compile=False)
    ly = next(l for l in m.layers if l.name == LAYER)
    eff = np.asarray(keras.ops.convert_to_numpy(ly.kq(ly._kernel)), dtype=np.float64)
    assert eff.shape == (E1.N_IN, E1.N_OUT), eff.shape
    ints = eff * GRID
    assert np.allclose(ints, np.round(ints)), "weights are not exact multiples of 1/32"
    ints = np.round(ints).astype(int).T                       # -> (N_OUT, N_IN)
    b = np.asarray(keras.ops.convert_to_numpy(ly.bias), dtype=np.float64)
    assert b.shape == (E1.N_OUT,), b.shape
    # Put the bias on the deployed bias_t grid (ap_fixed<18,2> -> 16 frac bits,
    # AP_TRN) before it reaches either the design or the reference. The binary
    # arms read an already-quantized b25.txt out of the converted project; this
    # checkpoint's bias is raw float, and leaving it raw makes the testbench fail
    # by ~1 LSB (measured 9.1e-6 < 1/65536) for reasons that have nothing to do
    # with the experiment.
    b = np.floor(b * (1 << BIAS_FRAC)) / (1 << BIAS_FRAC)
    assert np.abs(b).max() < 2, "bias outside ap_fixed<18,2> range"

    # exactness bound: max |row sum| with |x| <= 8 (ap_fixed<8,4>)
    bound = float(np.abs(ints).sum(axis=1).max()) / GRID * 8.0 + float(np.abs(b).max())
    assert bound < 512, f"row-sum bound {bound} exceeds ap_fixed<26,10> integer range"
    print(f"[w8] {LAYER}: {ints.shape}  levels={len(np.unique(ints))}  "
          f"int range [{ints.min()}, {ints.max()}]  row-sum bound {bound:.1f} < 512")
    return ints, b


def w8_body(wi: np.ndarray) -> str:
    """Row sums as pure expressions of constant x activation products.

    Constants are emitted as literals (not a ROM) so Vitis inlines them exactly
    as hls4ml's Latency strategy does, and the products are never seeded from the
    26-bit accumulator -- the arm-P width lesson (chain seeding cost ~1.8x LUT).
    Zero weights are dropped, which is what any emitter would do; the count is
    reported so the comparison against the dense +-1 arm stays honest.
    """
    n_zero = int((wi == 0).sum())
    print(f"[w8] zero weights dropped: {n_zero}/{wi.size} "
          f"({100 * n_zero / wi.size:.1f}%)  -- +-1 arm has 0")
    lines = []
    for o in range(E1.N_OUT):
        terms = []
        for i in range(E1.N_IN):
            c = int(wi[o, i])
            if c == 0:
                continue
            lit = f"(wt_t){abs(c) / GRID:.6f}"
            terms.append(("- " if c < 0 else "+ ") + f"{lit} * x[{i}]")
        expr = " ".join(terms).lstrip("+ ") if terms else "(wt_t)0"
        lines.append(f"  y[{o}] = (acc_t)({expr}) + (acc_t)BIAS[{o}];")
    return "\n".join(lines)


def w_ref_decl_w8(wi: np.ndarray, b: np.ndarray) -> str:
    rows = ",\n".join("  {" + ", ".join(f"{v / GRID:.16f}" for v in wi[o]) + "}"
                      for o in range(E1.N_OUT))
    bs = ", ".join(f"{v:.16f}" for v in b)
    return (f"extern const double W_REF[N_OUT][N_IN] = {{\n{rows}\n}};\n"
            f"extern const double B_REF[N_OUT] = {{{bs}}};\n")


RUN_ALL = """#!/bin/bash
# E-A' — the 8-bit denominator at layer scale. Sequential, guarded (shared box).
set -u
source /data/software/xilinx/Vitis/2023.2/settings64.sh
cd "$(dirname "$0")"
guard() {
  while true; do
    nv=$(pgrep -c vitis_hls || true); free_gb=$(free -g | awk '/Mem:/{print $7}')
    [ "${nv:-0}" -le 2 ] && [ "${free_gb:-0}" -ge 40 ] && break
    echo "guard: vitis=$nv free=${free_gb}G — waiting 60s"; sleep 60
  done
}
for arm in p8 a8; do
  guard
  echo "=== arm $arm: $(date) ==="
  (cd "$arm" && vitis_hls -f build.tcl > vitis_hls.log 2>&1)
  echo "=== arm $arm done rc=$? $(date) ==="
done
echo "ALL_W8_ARMS_DONE"
"""


def emit(name, top, body, wi, b, types):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    hdr = (E1.HEADER.format(n_tok=E1.N_TOK, n_in=E1.N_IN, n_out=E1.N_OUT, **types)
           + f"typedef {types['wt_t']} wt_t;\n")
    src = ('#include "myproject.h"\n' + E1.bias_decl(b, types["bias_t"]) + "\n"
           + E1.KERNEL.format(body=body) + top.format() + "\n"
           + w_ref_decl_w8(wi, b))
    (d / "myproject.h").write_text(hdr)
    (d / "myproject.cpp").write_text(src)
    (d / "tb.cpp").write_text(E1.TB.format())
    (d / "build.tcl").write_text(E1.BUILD_TCL.format(name=name, part=E1.PART,
                                                     clock=E1.CLOCK, export=""))


def main():
    _, _, types = E1.load_layer()          # identical types to the binary arms
    types = dict(types, wt_t="ap_fixed<8,3>")   # the deployed grid: 5 frac bits
    wi, b = load_w8_layer()
    body = w8_body(wi)
    emit("p8", E1.TOP_SPATIAL, body, wi, b, types)
    emit("a8", E1.TOP_FOLD, body, wi, b, types)
    run = OUT / "run_all.sh"
    run.write_text(RUN_ALL)
    run.chmod(0o755)
    print(f"[w8] types: {types}")
    print(f"[w8] emitted 2 arms -> {OUT}")


if __name__ == "__main__":
    main()
