"""Experiment-1 emitter (COMPILER.md, pre-registered 2026-07-24).

Emits five standalone Vitis HLS projects for ONE layer of the r8 stdnn flagship
(bit_block_0_ffn_fc1, 32->64, weights w25 = {-1,+1}, per-token-identical bias),
plus testbenches proving bit-exactness against a double-precision reference:

  P   naive spatial x10        (parity control vs the whole-model census)
  A   token-folded x10, II=10  (one constant datapath, activations muxed)
  A2  token-folded x2  (x5)    (monotonicity control)
  B   spatial x10, FR-k4       (Four-Russians subset-sum restructuring)
  C   token-folded x10 + FR-k4 (the composition)

Arms P and C additionally run `export_design -flow syn` (Vivado synthesis) for
the post-csynth anchor (arm V). Note: arm B is FR-k4 alone — the affine
transform is an alternative decomposition, not a composable one, and FR
dominates it on this layer (counting study); recorded as a deviation from the
registered arm label.

Exactness argument: inputs ap_fixed<8,4> (4 frac bits), all intermediates in
ap_fixed<26,10> (16 frac bits >= 4, integer range covers |sum| <= 32*8 + |bias|
< 512) -> every addition is exact, so any summation order is bit-identical and
double precision is an exact reference.

Usage: .venv-hgq2/bin/python bnjettag/code/analysis/e1_emit.py
Output: bnjettag/results/adder-graph/e1/{p,a,a2,b,c}/ + run_all.sh
"""

import re
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
PRJ = REPO / "r7/results/convert/r8stdnn-s2/rf8/hls_prj_rf8"
OUT = REPO / "results/adder-graph/e1"
PART = "xcvu13p-flga2577-2-e"
CLOCK = "2.5"
N_TOK, N_IN, N_OUT, K = 10, 32, 64, 4
N_GRP = N_IN // K


def load_layer():
    w = np.loadtxt(PRJ / "firmware/weights/w25.txt", delimiter=",").reshape(N_IN, N_OUT).T
    assert set(np.unique(w)) <= {-1.0, 1.0}
    b = np.loadtxt(PRJ / "firmware/weights/b25.txt", delimiter=",").reshape(N_TOK, N_OUT)
    assert all(np.array_equal(b[0], b[i]) for i in range(N_TOK)), "bias not per-token-identical"
    d = (PRJ / "firmware/defines.h").read_text()
    def typ(name, fallback):
        m = re.search(rf"typedef\s+(ap_u?fixed<[^>]+>)\s+{name};", d)
        return m.group(1) if m else fallback
    in_t = typ("bit_block_0_ffn_fc1_iq_t", "ap_fixed<8,4>")
    wi, ii = map(int, re.match(r"ap_u?fixed<(\d+),\s*(-?\d+)", in_t).groups())
    lg = (K - 1).bit_length()                     # ceil(log2 K) for K a power of 2
    gsum_t = f"ap_fixed<{wi + lg},{ii + lg}>"     # exact signed K-term sum width
    return w.astype(int), b[0], dict(
        in_t=in_t,
        acc_t=typ("bit_block_0_ffn_fc1_accum_t", "ap_fixed<26,10>"),
        out_t=typ("bit_block_0_ffn_fc1_t", "ap_fixed<26,10>"),
        bias_t=typ("bit_block_0_ffn_fc1_bias_t", "ap_fixed<26,10>"),
        gsum_t=gsum_t)


def bias_decl(b, t):
    vals = ", ".join(f"{v:.16f}" for v in b)
    return f"static const bias_t BIAS[{N_OUT}] = {{{vals}}};"


def naive_body(w):
    """Fully unrolled +-x sum per output, as a pure expression of the 8-bit
    leaves so Vitis's balanced tree grows widths naturally (9,10,11,...) —
    seeding the chain with a 26-bit accumulator was measured to inflate the
    tree ~1.8x (arm-P parity failure, 2026-07-24)."""
    lines = []
    for o in range(N_OUT):
        terms = " ".join(("+ " if w[o, i] > 0 else "- ") + f"x[{i}]"
                         for i in range(N_IN)).lstrip("+ ")
        if w[o, 0] < 0:
            terms = "- " + terms.lstrip("- ")
        lines.append(f"  y[{o}] = (acc_t)({terms}) + (acc_t)BIAS[{o}];")
    return "\n".join(lines)


def gray_order(k):
    return [i ^ (i >> 1) for i in range(2 ** (k - 1))]


def fr_body(w):
    """FR-k4: per 4-input group, all 2^(k-1) canonical signed sums via Gray
    chaining (first input sign fixed +); each row wires one sum per group.
    Group sums live in the narrow gsum_t (input width + log2(k) bits), and row
    sums are pure gsum-leaf expressions — never seeded from the 26-bit
    accumulator (the arm-P width lesson applies here doubly)."""
    lines = [f"  gsum_t S[{N_GRP}][{2**(K-1)}];",
             "#pragma HLS ARRAY_PARTITION variable=S complete dim=0"]
    order = gray_order(K)
    for g in range(N_GRP):
        base = g * K
        xs = [f"x[{base+i}]" for i in range(K)]
        # pattern p bits 0..k-2 = signs of inputs 1..k-1 (bit set => minus)
        prev = None
        for p in order:
            expr_terms = [xs[0]] + [("- " if (p >> (i - 1)) & 1 else "+ ") + xs[i]
                                    for i in range(1, K)]
            if prev is None:
                lines.append(f"  S[{g}][{p}] = {' '.join(expr_terms)};")
            else:
                flip = (p ^ prev).bit_length() - 1  # which sign bit flipped
                i = flip + 1
                sgn = "-" if (p >> flip) & 1 else "+"
                lines.append(f"  S[{g}][{p}] = S[{g}][{prev}] {sgn} "
                             f"(gsum_t)(((gsum_t){xs[i]}) << 1);")
            prev = p
    for o in range(N_OUT):
        sels = []
        for g in range(N_GRP):
            sg = w[o, g * K:(g + 1) * K]
            glob = int(sg[0])                       # canonical first sign
            p = sum(((1 if sg[i] * glob < 0 else 0) << (i - 1)) for i in range(1, K))
            sels.append(("+ " if glob > 0 else "- ") + f"S[{g}][{p}]")
        expr = " ".join(sels).lstrip("+ ")
        if expr.startswith("- ") is False and sels[0].startswith("- "):
            expr = "- " + expr
        lines.append(f"  y[{o}] = (acc_t)({expr}) + (acc_t)BIAS[{o}];")
    return "\n".join(lines)


HEADER = """#include "ap_fixed.h"
typedef {in_t} input_t;
typedef {acc_t} acc_t;
typedef {out_t} result_t;
typedef {bias_t} bias_t;
typedef {gsum_t} gsum_t;
#define N_TOK {n_tok}
#define N_IN {n_in}
#define N_OUT {n_out}
void myproject(input_t in[N_TOK][N_IN], result_t out[N_TOK][N_OUT]);
"""

KERNEL = """static void token_dense(input_t x[N_IN], result_t y[N_OUT]) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
{body}
}}
"""

TOP_SPATIAL = """void myproject(input_t in[N_TOK][N_IN], result_t out[N_TOK][N_OUT]) {{
#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0
#pragma HLS PIPELINE II=1
TOK: for (int t = 0; t < N_TOK; t++) {{
#pragma HLS UNROLL
    token_dense(in[t], out[t]);
  }}
}}
"""

TOP_FOLD = """void myproject(input_t in[N_TOK][N_IN], result_t out[N_TOK][N_OUT]) {{
#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0
TOK: for (int t = 0; t < N_TOK; t++) {{
#pragma HLS PIPELINE II=1 rewind
    token_dense(in[t], out[t]);
  }}
}}
"""

TOP_FOLD2 = """void myproject(input_t in[N_TOK][N_IN], result_t out[N_TOK][N_OUT]) {{
#pragma HLS ARRAY_PARTITION variable=in complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0
GRP: for (int g = 0; g < 5; g++) {{
#pragma HLS UNROLL
TOK: for (int i = 0; i < 2; i++) {{
#pragma HLS PIPELINE II=1
      token_dense(in[2 * g + i], out[2 * g + i]);
    }}
  }}
}}
"""

TB = """#include <cstdio>
#include <cstdlib>
#include <cmath>
#include "myproject.h"
extern const double W_REF[N_OUT][N_IN];
extern const double B_REF[N_OUT];
int main() {{
  srand(20260724);
  int bad = 0;
  for (int trial = 0; trial < 256; trial++) {{
    input_t in[N_TOK][N_IN];
    double din[N_TOK][N_IN];
    for (int t = 0; t < N_TOK; t++)
      for (int i = 0; i < N_IN; i++) {{
        int q = (rand() % 256) - 128;          // full ap_fixed<8,4> grid
        din[t][i] = q / 16.0;
        in[t][i] = (input_t)din[t][i];
      }}
    result_t out[N_TOK][N_OUT];
    myproject(in, out);
    for (int t = 0; t < N_TOK; t++)
      for (int o = 0; o < N_OUT; o++) {{
        double ref = B_REF[o];
        for (int i = 0; i < N_IN; i++) ref += W_REF[o][i] * din[t][i];
        if (std::fabs(out[t][o].to_double() - ref) > 1e-12) {{
          if (bad < 5) printf("MISMATCH t=%d o=%d got=%.10f ref=%.10f\\n",
                              t, o, out[t][o].to_double(), ref);
          bad++;
        }}
      }}
  }}
  printf(bad ? "FAIL %d mismatches\\n" : "EXACT_MATCH\\n", bad);
  return bad ? 1 : 0;
}}
"""

BUILD_TCL = """open_project -reset prj_{name}
set_top myproject
add_files myproject.cpp
add_files -tb tb.cpp
open_solution -reset sol1
set_part {part}
create_clock -period {clock}
csim_design
csynth_design
{export}
exit
"""

RUN_ALL = """#!/bin/bash
# Experiment 1 — sequential, guarded (shared box; see docs/infrastructure/mulder-setup.md)
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
for arm in p a a2 b c; do
  guard
  echo "=== arm $arm: $(date) ==="
  (cd "$arm" && vitis_hls -f build.tcl > vitis_hls.log 2>&1)
  echo "=== arm $arm done rc=$? $(date) ==="
done
echo "ALL_ARMS_DONE"
"""


def w_ref_decl(w, b):
    rows = ",\n".join("  {" + ", ".join(f"{int(v)}.0" for v in w[o]) + "}"
                      for o in range(N_OUT))
    bs = ", ".join(f"{v:.16f}" for v in b)
    return (f"extern const double W_REF[N_OUT][N_IN] = {{\n{rows}\n}};\n"
            f"extern const double B_REF[N_OUT] = {{{bs}}};\n")


def emit(name, top, body, w, b, types, export_syn=False):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    hdr = HEADER.format(n_tok=N_TOK, n_in=N_IN, n_out=N_OUT, **types)
    src = ('#include "myproject.h"\n' + bias_decl(b, types["bias_t"]) + "\n"
           + KERNEL.format(body=body) + top.format() + "\n" + w_ref_decl(w, b))
    (d / "myproject.h").write_text(hdr)
    (d / "myproject.cpp").write_text(src)
    (d / "tb.cpp").write_text(TB.format())
    exp = ('config_export -format ip_catalog -rtl verilog\n'
           'export_design -flow syn') if export_syn else ""
    (d / "build.tcl").write_text(BUILD_TCL.format(name=name, part=PART,
                                                  clock=CLOCK, export=exp))


def main():
    w, b, types = load_layer()
    print("types:", types)
    nb = naive_body(w)
    fb = fr_body(w)
    emit("p", TOP_SPATIAL, nb, w, b, types, export_syn=True)
    emit("a", TOP_FOLD, nb, w, b, types)
    emit("a2", TOP_FOLD2, nb, w, b, types)
    emit("b", TOP_SPATIAL, fb, w, b, types)
    emit("c", TOP_FOLD, fb, w, b, types, export_syn=True)
    run = OUT / "run_all.sh"
    run.write_text(RUN_ALL)
    run.chmod(0o755)
    print(f"emitted 5 arms -> {OUT}")


if __name__ == "__main__":
    main()
