"""E-C — does the token fold apply to the WEIGHTLESS attention core? (2026-07-25)

COMPILER.md §5 states the attention floor as immune to the compiler, and for
*weight* binarization that is right: QK^T and attn.V carry no weights.  But
folding is not a weight transform -- it is a schedule transform, and it applies
to any computation that is spatially replicated over the token axis.  Nobody has
tested it there, and after folding the dense stack the attention core is ~56% of
what remains (789,076 of a projected 1,414,413 LUT).

The motivating measurement (first per-module RF=1 vs RF=8 comparison of the stdnn
flagship, 2026-07-25): time-multiplexing act x act by REUSE FACTOR moved
QK^T 211,200 -> 272,938 LUT (+29.2%) and attn.V 821,760 -> 516,138 (-37.2%), net
-23.6%.  Reuse factor fails on act x act much as it failed on +-1 dense (-7%,
then 0%), where the fold nevertheless delivered 9.3x.  So the fold is genuinely
open here, in both directions.

Arms (block 0 of the r8 stdnn flagship, real shapes and real fixed-point types):

  s12  QK^T   spatial, all 400 scores in parallel, II=1
  f12  QK^T   folded over the QUERY token index, II=10
  s18  attn.V spatial, all 320 context outputs in parallel, II=1
  f18  attn.V folded over the OUTPUT token index, II=10

Both einsums accumulate EXACTLY in their deployed accumulators -- scores
ap_fixed<29,21> carries 8 frac bits against 8-frac products, ctx ap_fixed<40,14>
carries 26 against 26 -- so summation order is irrelevant and a nested-loop
golden in the same types is an exact reference.  Every arm must match it bitwise
before its resource number counts (GATE2 tradition).

Legality of the fold: at cycle t the folded QK^T needs every key, and the folded
attn.V needs every softmax row -- both are available, because the folded QKV
stage upstream has already emitted all ten tokens by the time this stage starts.
That is a pipeline barrier, not an obstruction, and it is exactly the whole-model
II composition question E-D1 has to answer.

Usage: .venv-hgq2/bin/python bnjettag/code/analysis/e1_attn_emit.py
Output: bnjettag/results/adder-graph/e1attn/{s12,f12,s18,f18}/ + run_all.sh
"""

from pathlib import Path

import e1_emit as E1

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "results/adder-graph/e1attn"

T, H, E, S = 10, 4, 8, 10          # tokens, heads, d_head, keys
QKV_T = "ap_fixed<13,9,AP_RND_CONV,AP_SAT,0>"
SCORE_T = "ap_fixed<29,21>"                     # accum == out for config12
SOFTMAX_T = "ap_ufixed<23,1,AP_RND_CONV,AP_SAT,0>"
CTX_ACC_T = "ap_fixed<40,14>"
CTX_T = "ap_fixed<15,8,AP_RND_CONV,AP_SAT,0>"

# hls4ml layouts, verified against firmware/myproject.cpp:
#   layer7/9/15_out[10*4*8]  = q/k/v  [t][h][e]
#   layer12/13_out[4*10*10]  = scores/softmax [h][t][s]
#   layer18_out[10*4*8]      = ctx    [t][h][e]
def qi(t, h, e):
    return (t * H + h) * E + e


def si(h, t, s):
    return (h * T + t) * S + s


def scores_rows(ts):
    """score[h][t][s] = sum_e q[t][h][e] * k[s][h][e], as pure product sums."""
    out = []
    for h in range(H):
        for t in ts:
            for s in range(S):
                terms = " + ".join(f"q[{qi(t, h, e)}] * k[{qi(s, h, e)}]" for e in range(E))
                out.append(f"  out[{si(h, t, s)}] = (score_t)({terms});")
    return out


def ctx_rows(ts):
    """ctx[t][h][e] = sum_s a[h][t][s] * v[s][h][e]."""
    out = []
    for t in ts:
        for h in range(H):
            for e in range(E):
                terms = " + ".join(f"a[{si(h, t, s)}] * v[{qi(s, h, e)}]" for s in range(S))
                out.append(f"  out[{qi(t, h, e)}] = (ctx_t)((acc_t)({terms}));")
    return out


# ---------------------------------------------------------------------------
# The FOLDED bodies. These must be ONE datapath re-used across tokens, with the
# token index entering only through array indexing (which Vitis turns into a mux
# on a fully partitioned array) -- exactly the mechanism E1's dense fold used via
# `token_dense(in[t], out[t])`.
#
# Emitting `switch (t) { case 0: ...; case 1: ...; }` would instead instantiate
# ten DIFFERENT bodies behind a mux and share nothing; that is not a fold, and it
# would have made this experiment report a false negative.
# ---------------------------------------------------------------------------
def scores_fold_body():
    """One query token per call: mux its 32 q values, then 40 dot products of length 8."""
    lines = ["  qkv_t qt[32];",
             "#pragma HLS ARRAY_PARTITION variable=qt complete dim=0",
             "  for (int i = 0; i < 32; i++) {",
             "#pragma HLS UNROLL",
             "    qt[i] = q[t * 32 + i];",          # q is [t][h][e] -> t-slice contiguous
             "  }"]
    for h in range(H):
        for s in range(S):
            terms = " + ".join(f"qt[{h * E + e}] * k[{qi(s, h, e)}]" for e in range(E))
            lines.append(f"  out[{h * T * S} + t * {S} + {s}] = (score_t)({terms});")
    return "\n".join(lines)


def ctx_fold_body():
    """One output token per call: mux its 40 attention weights, then 32 dot products of length 10."""
    lines = ["  sm_t at[40];",
             "#pragma HLS ARRAY_PARTITION variable=at complete dim=0"]
    for h in range(H):
        for s in range(S):
            lines.append(f"  at[{h * S + s}] = a[{h * T * S} + t * {S} + {s}];")
    for h in range(H):
        for e in range(E):
            terms = " + ".join(f"at[{h * S + s}] * v[{qi(s, h, e)}]" for s in range(S))
            lines.append(f"  out[t * 32 + {h * E + e}] = (ctx_t)((acc_t)({terms}));")
    return "\n".join(lines)


HEADER = """#include "ap_fixed.h"
typedef {qkv} qkv_t;
typedef {score} score_t;
typedef {sm} sm_t;
typedef {acc} acc_t;
typedef {ctx} ctx_t;
#define N_Q {nq}
#define N_S {ns}
"""

# ---- QK^T ------------------------------------------------------------------
H12 = HEADER + "void myproject(qkv_t q[{nq}], qkv_t k[{nq}], score_t out[{ns}]);\n"
KERNEL12 = """static void score_slice(qkv_t q[N_Q], qkv_t k[N_Q], score_t out[N_S], int t) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
{body}
}}
"""
TOP12_SPATIAL = """void myproject(qkv_t q[N_Q], qkv_t k[N_Q], score_t out[N_S]) {{
#pragma HLS ARRAY_PARTITION variable=q complete dim=0
#pragma HLS ARRAY_PARTITION variable=k complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0
#pragma HLS PIPELINE II=1
{body}
}}
"""
TOP12_FOLD = """void myproject(qkv_t q[N_Q], qkv_t k[N_Q], score_t out[N_S]) {{
#pragma HLS ARRAY_PARTITION variable=q complete dim=0
#pragma HLS ARRAY_PARTITION variable=k complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0
TOK: for (int t = 0; t < 10; t++) {{
#pragma HLS PIPELINE II=1 rewind
    score_slice(q, k, out, t);
  }}
}}
"""

# ---- attn . V --------------------------------------------------------------
H18 = HEADER + "void myproject(sm_t a[{ns}], qkv_t v[{nq}], ctx_t out[{nq}]);\n"
KERNEL18 = """static void ctx_slice(sm_t a[N_S], qkv_t v[N_Q], ctx_t out[N_Q], int t) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
{body}
}}
"""
TOP18_SPATIAL = """void myproject(sm_t a[N_S], qkv_t v[N_Q], ctx_t out[N_Q]) {{
#pragma HLS ARRAY_PARTITION variable=a complete dim=0
#pragma HLS ARRAY_PARTITION variable=v complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0
#pragma HLS PIPELINE II=1
{body}
}}
"""
TOP18_FOLD = """void myproject(sm_t a[N_S], qkv_t v[N_Q], ctx_t out[N_Q]) {{
#pragma HLS ARRAY_PARTITION variable=a complete dim=0
#pragma HLS ARRAY_PARTITION variable=v complete dim=0
#pragma HLS ARRAY_PARTITION variable=out complete dim=0
TOK: for (int t = 0; t < 10; t++) {{
#pragma HLS PIPELINE II=1 rewind
    ctx_slice(a, v, out, t);
  }}
}}
"""

# Testbench: nested-loop golden in the SAME ap_fixed types (exact, see docstring),
# bitwise comparison, 256 random input sets on the full input grids.
TB12 = """#include <cstdio>
#include <cstdlib>
#include "myproject.h"
int main() {
  srand(20260725);
  int bad = 0;
  for (int trial = 0; trial < 256; trial++) {
    qkv_t q[N_Q], k[N_Q];
    for (int i = 0; i < N_Q; i++) {
      q[i] = (qkv_t)(((rand() % 8192) - 4096) / 16.0);
      k[i] = (qkv_t)(((rand() % 8192) - 4096) / 16.0);
    }
    score_t out[N_S], ref[N_S];
    for (int h = 0; h < 4; h++)
      for (int t = 0; t < 10; t++)
        for (int s = 0; s < 10; s++) {
          score_t acc = 0;
          for (int e = 0; e < 8; e++)
            acc += (score_t)(q[(t * 4 + h) * 8 + e] * k[(s * 4 + h) * 8 + e]);
          ref[(h * 10 + t) * 10 + s] = acc;
        }
    myproject(q, k, out);
    for (int i = 0; i < N_S; i++)
      if (out[i] != ref[i]) {
        if (bad < 5) printf("MISMATCH i=%d got=%.10f ref=%.10f\\n",
                            i, out[i].to_double(), ref[i].to_double());
        bad++;
      }
  }
  printf(bad ? "FAIL %d mismatches\\n" : "EXACT_MATCH\\n", bad);
  return bad ? 1 : 0;
}
"""

TB18 = """#include <cstdio>
#include <cstdlib>
#include "myproject.h"
int main() {
  srand(20260725);
  int bad = 0;
  for (int trial = 0; trial < 256; trial++) {
    sm_t a[N_S]; qkv_t v[N_Q];
    for (int i = 0; i < N_S; i++) a[i] = (sm_t)((rand() % 8388608) / 8388608.0);
    for (int i = 0; i < N_Q; i++) v[i] = (qkv_t)(((rand() % 8192) - 4096) / 16.0);
    ctx_t out[N_Q], ref[N_Q];
    for (int t = 0; t < 10; t++)
      for (int h = 0; h < 4; h++)
        for (int e = 0; e < 8; e++) {
          acc_t acc = 0;
          for (int s = 0; s < 10; s++)
            acc += (acc_t)(a[(h * 10 + t) * 10 + s] * v[(s * 4 + h) * 8 + e]);
          ref[(t * 4 + h) * 8 + e] = (ctx_t)acc;
        }
    myproject(a, v, out);
    for (int i = 0; i < N_Q; i++)
      if (out[i] != ref[i]) {
        if (bad < 5) printf("MISMATCH i=%d got=%.10f ref=%.10f\\n",
                            i, out[i].to_double(), ref[i].to_double());
        bad++;
      }
  }
  printf(bad ? "FAIL %d mismatches\\n" : "EXACT_MATCH\\n", bad);
  return bad ? 1 : 0;
}
"""

RUN_ALL = """#!/bin/bash
# E-C — attention token fold. Sequential, guarded (shared box).
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
for arm in s12 f12 s18 f18; do
  guard
  echo "=== arm $arm: $(date) ==="
  (cd "$arm" && vitis_hls -f build.tcl > vitis_hls.log 2>&1)
  echo "=== arm $arm done rc=$? $(date) ==="
done
echo "ALL_ATTN_ARMS_DONE"
"""


def emit(name, hdr, kernel, top, body_or_cases, tb, nq, ns):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    types = dict(qkv=QKV_T, score=SCORE_T, sm=SOFTMAX_T, acc=CTX_ACC_T, ctx=CTX_T,
                 nq=nq, ns=ns)
    (d / "myproject.h").write_text(hdr.format(**types))
    src = '#include "myproject.h"\n'
    if kernel:
        src += kernel.format(body=body_or_cases) + top.format()
    else:
        src += top.format(body=body_or_cases)
    (d / "myproject.cpp").write_text(src)
    (d / "tb.cpp").write_text(tb)
    (d / "build.tcl").write_text(E1.BUILD_TCL.format(name=name, part=E1.PART,
                                                     clock=E1.CLOCK, export=""))


def main():
    nq, ns = T * H * E, H * T * S
    emit("s12", H12, None, TOP12_SPATIAL, "\n".join(scores_rows(range(T))), TB12, nq, ns)
    emit("f12", H12, KERNEL12, TOP12_FOLD, scores_fold_body(), TB12, nq, ns)
    # N_Q / N_S keep their meaning across both einsums (N_Q = the 10x4x8 q/k/v/ctx
    # tensor, N_S = the 4x10x10 score/softmax tensor); H18 already picks the right
    # one per argument, so the call order is the same as for the QK^T arms.
    emit("s18", H18, None, TOP18_SPATIAL, "\n".join(ctx_rows(range(T))), TB18, nq, ns)
    emit("f18", H18, KERNEL18, TOP18_FOLD, ctx_fold_body(), TB18, nq, ns)
    run = OUT / "run_all.sh"
    run.write_text(RUN_ALL)
    run.chmod(0o755)
    print(f"[attn] emitted 4 arms -> {OUT}")
    print(f"[attn] census comparators (rf8 stdnn): QK^T 136,469 LUT · attn.V 257,749 LUT")


if __name__ == "__main__":
    main()
