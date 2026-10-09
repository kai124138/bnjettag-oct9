"""E-D1 — the token-serial block-0 slice: does the fold compose to a whole-block II=10?

E1 folded one dense layer (9.3x). E-C folded the two attention einsums (6.46x). Both
were single layers in isolation. The open question the fit claim actually rests on is
whether those folds COMPOSE: a real encoder block alternates per-token stages with a
per-jet barrier (QK^T needs every key; attn.V needs every softmax row), and nothing so
far shows that a chain of II=10 stages separated by such a barrier still runs at II=10.

This emits block 0 of the r8 stdnn flagship as one token-serial datapath:

  stage A  (token-serial, II=10)  h[t] -> q[t], k[t], v[t]      3 x folded 32->32 binary dense
  stage B  (token-serial, II=10)  q,k  -> scores[h][t][s]       folded QK^T   (E-C's f12 body)
  stage C  (per-jet BARRIER)      softmax over 400              hls4ml's own kernel
  stage D  (token-serial, II=10)  attn,v -> ctx[t] -> Wo -> affine -> residual
  stage E  (token-serial, II=10)  fc1 -> relu -> fc2 -> affine -> residual

`#pragma HLS DATAFLOW` at the top, so the stages run concurrently on different jets and
the block's initiation interval is max(stage II) = 10 rather than their sum.

HYBRID BY DESIGN. The folded weighted stages are emitted here; softmax, ReLU, the two
affines and the two residual adds are hls4ml's own `nnet::` kernels, called with the
project's own configs. That keeps the glue byte-identical to the deployed block, so the
measurement isolates the schedule change instead of also measuring a different softmax.

Bit-exactness: the testbench holds a SPATIAL reference of the same block (same types,
same nnet:: calls, same weights, no folding) and requires the folded top to match it
exactly on every output. Reference lives in tb.cpp so it is never synthesized.

Usage: .venv-hgq2/bin/python bnjettag/code/analysis/ed1_emit.py
Output: bnjettag/results/adder-graph/ed1/ (self-contained Vitis project + run_all.sh)
"""

import re
import shutil
from pathlib import Path

import numpy as np

import e1_emit as E1

REPO = Path(__file__).resolve().parents[2]
PRJ = REPO / "r7/results/convert/r8stdnn-s2/rf8/hls_prj_rf8"
FW = PRJ / "firmware"
OUT = REPO / "results/adder-graph/ed1"

T, H, E, D, F = 10, 4, 8, 32, 64          # tokens, heads, d_head, d_model, ffn

# The six per-token weighted layers of block 0, with their hls4ml layer indices.
# shape = (n_in, n_out) as stored in wN.txt (row-major [in][out]).
LAYERS = {
    "wq": (7, D, D), "wk": (9, D, D), "wv": (15, D, D),
    "wo": (20, D, D), "fc1": (25, D, F), "fc2": (28, F, D),
}


def load_sign(idx: int, n_in: int, n_out: int):
    """Deployed +-1 matrix (n_out, n_in) and its per-token-identical bias."""
    w = np.loadtxt(FW / f"weights/w{idx}.txt", delimiter=",").reshape(n_in, n_out).T
    assert set(np.unique(w)) <= {-1.0, 1.0}, f"w{idx} is not +-1"
    bp = FW / f"weights/b{idx}.txt"
    b = np.loadtxt(bp, delimiter=",") if bp.exists() else np.zeros(n_out)
    b = b.reshape(-1, n_out)
    assert all(np.array_equal(b[0], r) for r in b), f"b{idx} not per-token-identical"
    return w.astype(int), b[0]


def dense_expr(w, b, xname, yname, n_in, n_out, acc="acc_t", bias="BIAS"):
    """Fully unrolled +-x sum per output, pure expression of the leaves (the arm-P
    width lesson: never seed the chain from the wide accumulator)."""
    lines = []
    for o in range(n_out):
        terms = " ".join(("+ " if w[o, i] > 0 else "- ") + f"{xname}[{i}]"
                         for i in range(n_in)).lstrip("+ ")
        if w[o, 0] < 0:
            terms = "- " + terms.lstrip("- ")
        lines.append(f"    {yname}[{o}] = ({acc})({terms}) + ({acc}){bias}[{o}];")
    return "\n".join(lines)


def affine_arrs(idx, n, pref):
    """s{idx}/b{idx} as literal arrays -- avoids hls4ml's runtime weight loading,
    which a standalone project does not set up (it is what made csim abort)."""
    sv = np.loadtxt(FW / f"weights/s{idx}.txt", delimiter=",").reshape(-1)[:n]
    bv = np.loadtxt(FW / f"weights/b{idx}.txt", delimiter=",").reshape(-1)[:n]
    return (f"static const float {pref}_S[{n}] = {{" + ", ".join(f"{v:.10f}f" for v in sv) + "};\n"
            f"static const float {pref}_B[{n}] = {{" + ", ".join(f"{v:.10f}f" for v in bv) + "};")


def bias_arr(name, b, t):
    return f"static const {t} {name}[{len(b)}] = {{" + ", ".join(f"{v:.16f}" for v in b) + "};"


def qi(t, h, e):
    return (t * H + h) * E + e


def si(h, t, s):
    return (h * T + t) * S_ + s


S_ = T   # keys == tokens


def scores_fold_body():
    """One query token per call: mux its 32 q values, then 40 dot products of length 8."""
    L = ["    qkv_t qt[32];",
         "#pragma HLS ARRAY_PARTITION variable=qt complete dim=0",
         "    for (int i = 0; i < 32; i++) {",
         "#pragma HLS UNROLL",
         "      qt[i] = q[t * 32 + i];",
         "    }"]
    for h in range(H):
        for s in range(S_):
            terms = " + ".join(f"qt[{h * E + e}] * k[{qi(s, h, e)}]" for e in range(E))
            L.append(f"    scores[{h * T * S_} + t * {S_} + {s}] = (score_t)({terms});")
    return "\n".join(L)


def ctx_fold_body():
    """One output token per call: mux its 40 attention weights, then 32 dots of length 10."""
    L = ["    sm_t at[40];",
         "#pragma HLS ARRAY_PARTITION variable=at complete dim=0"]
    for h in range(H):
        for s in range(S_):
            L.append(f"    at[{h * S_ + s}] = attn[{h * T * S_} + t * {S_} + {s}];")
    for h in range(H):
        for e in range(E):
            terms = " + ".join(f"at[{h * S_ + s}] * v[{qi(s, h, e)}]" for s in range(S_))
            L.append(f"    ctxv[{h * E + e}] = (cacc_t)({terms});")
    return "\n".join(L)


def scores_spatial():
    """All 400 scores, every index a compile-time constant (no fold, no loop)."""
    return "\n".join(
        f"    scores[{si(h, t, s)}] = (score_t)("
        + " + ".join(f"q[{qi(t, h, e)}] * k[{qi(s, h, e)}]" for e in range(E)) + ");"
        for h in range(H) for t in range(T) for s in range(S_))


def ctx_spatial():
    """All 320 context accumulators, likewise fully constant-indexed."""
    return "\n".join(
        f"    ctxv[{t}][{h * E + e}] = (cacc_t)("
        + " + ".join(f"attn[{si(h, t, s)}] * v[{qi(s, h, e)}]" for s in range(S_)) + ");"
        for t in range(T) for h in range(H) for e in range(E))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # self-contained project: hls4ml's firmware provides ap_types, defines.h,
    # parameters.h, nnet_utils and the weight headers used by the nnet:: glue.
    for sub in ("ap_types", "nnet_utils", "weights"):
        dst = OUT / "firmware" / sub
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(FW / sub, dst)
    for f in ("defines.h", "parameters.h"):
        shutil.copy(FW / f, OUT / "firmware" / f)

    W = {k: load_sign(i, a, b) for k, (i, a, b) in LAYERS.items()}
    src = SRC.format(
        b_wq=bias_arr("B_WQ", W["wq"][1], "model_default_t"),
        b_wk=bias_arr("B_WK", W["wk"][1], "model_default_t"),
        b_wv=bias_arr("B_WV", W["wv"][1], "model_default_t"),
        b_wo=bias_arr("B_WO", W["wo"][1], "model_default_t"),
        b_fc1=bias_arr("B_FC1", W["fc1"][1], "bit_block_0_ffn_fc1_bias_t"),
        b_fc2=bias_arr("B_FC2", W["fc2"][1], "bit_block_0_ffn_fc2_bias_t"),
        wq=dense_expr(W["wq"][0], None, "xq", "qo", D, D, "qacc_t", "B_WQ"),
        wk=dense_expr(W["wk"][0], None, "xk", "ko", D, D, "qacc_t", "B_WK"),
        wv=dense_expr(W["wv"][0], None, "xv", "vo", D, D, "qacc_t", "B_WV"),
        wo=dense_expr(W["wo"][0], None, "cx", "wo_o", D, D, "oacc_t", "B_WO"),
        fc1=dense_expr(W["fc1"][0], None, "x1", "y1", D, F, "f1acc_t", "B_FC1"),
        fc2=dense_expr(W["fc2"][0], None, "x2", "y2", F, D, "f2acc_t", "B_FC2"),
        aff=affine_arrs(22, D, "A22") + "\n" + affine_arrs(30, D, "A30"),
        scores=scores_fold_body(), ctx=ctx_fold_body())
    (OUT / "myproject.h").write_text(HDR)
    (OUT / "tb.cpp").write_text(TB)
    ref = REF.format(
        b_wq=bias_arr("R_WQ", W["wq"][1], "model_default_t"),
        b_wk=bias_arr("R_WK", W["wk"][1], "model_default_t"),
        b_wv=bias_arr("R_WV", W["wv"][1], "model_default_t"),
        b_wo=bias_arr("R_WO", W["wo"][1], "model_default_t"),
        b_fc1=bias_arr("R_FC1", W["fc1"][1], "bit_block_0_ffn_fc1_bias_t"),
        b_fc2=bias_arr("R_FC2", W["fc2"][1], "bit_block_0_ffn_fc2_bias_t"),
        wq=dense_expr(W["wq"][0], None, "xq", "qo", D, D, "qacc_t", "R_WQ"),
        wk=dense_expr(W["wk"][0], None, "xk", "ko", D, D, "qacc_t", "R_WK"),
        wv=dense_expr(W["wv"][0], None, "xv", "vo", D, D, "qacc_t", "R_WV"),
        wo=dense_expr(W["wo"][0], None, "cx", "wo_o", D, D, "oacc_t", "R_WO"),
        fc1=dense_expr(W["fc1"][0], None, "x1", "y1", D, F, "f1acc_t", "R_FC1"),
        fc2=dense_expr(W["fc2"][0], None, "x2", "y2", F, D, "f2acc_t", "R_FC2"),
        scores=scores_spatial(), ctx=ctx_spatial())
    (OUT / "myproject.cpp").write_text(src + "\n" + ref)
    (OUT / "build.tcl").write_text(BUILD)
    (OUT / "run_all.sh").write_text(RUN)
    (OUT / "run_all.sh").chmod(0o755)
    print(f"[ed1] emitted token-serial block-0 -> {OUT}")
    print(f"[ed1] folded stages: qkv({D}->{D} x3), scores, ctx+Wo, fc1({D}->{F})+fc2({F}->{D})")


HDR = '''#ifndef ED1_H_
#define ED1_H_
#include "firmware/defines.h"

typedef bit_block_0_attn_Wq_iq_t   qkv_in_t;
typedef bit_block_0_attn_Wq_t      qkv_t;
typedef bit_block_0_attn_Wq_accum_t qacc_t;
typedef bit_block_0_attn_scores_t  score_t;
typedef bit_block_0_attn_softmax_t sm_t;
typedef bit_block_0_attn_ctx_accum_t cacc_t;
typedef bit_block_0_attn_ctx_t     ctx_t;
typedef bit_block_0_attn_Wo_accum_t oacc_t;
typedef bit_block_0_attn_Wo_t      wo_t;
typedef bit_block_0_ffn_fc1_accum_t f1acc_t;
typedef bit_block_0_ffn_fc1_t      f1_t;
typedef bit_block_0_ffn_fc2_accum_t f2acc_t;
typedef bit_block_0_ffn_fc2_t      f2_t;
typedef input_proj_affine_t        hin_t;
typedef bit_block_0_add_ffn_t      hout_t;

#define NT 10
#define ND 32
#define NF 64
#define NS 400

void myproject(hin_t h_in[NT * ND], hout_t h_out[NT * ND]);
#endif
'''

SRC = '''#include "myproject.h"
#include "firmware/parameters.h"

{b_wq}
{b_wk}
{b_wv}
{b_wo}
{b_fc1}
{b_fc2}
{aff}

// ---------------- stage A: per-token Q/K/V (folded x10) --------------------
static void stage_qkv(hin_t h[NT * ND], qkv_t q[NT * ND], qkv_t k[NT * ND],
                      qkv_t v[NT * ND]) {{
#pragma HLS INLINE off
TOKA: for (int t = 0; t < NT; t++) {{
#pragma HLS PIPELINE II=1 rewind
    qkv_in_t xq[ND], xk[ND], xv[ND];
#pragma HLS ARRAY_PARTITION variable=xq complete dim=0
#pragma HLS ARRAY_PARTITION variable=xk complete dim=0
#pragma HLS ARRAY_PARTITION variable=xv complete dim=0
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      xq[i] = (qkv_in_t)h[t * ND + i];
      xk[i] = (qkv_in_t)h[t * ND + i];
      xv[i] = (qkv_in_t)h[t * ND + i];
    }}
    qkv_t qo[ND], ko[ND], vo[ND];
#pragma HLS ARRAY_PARTITION variable=qo complete dim=0
#pragma HLS ARRAY_PARTITION variable=ko complete dim=0
#pragma HLS ARRAY_PARTITION variable=vo complete dim=0
{wq}
{wk}
{wv}
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      q[t * ND + i] = qo[i]; k[t * ND + i] = ko[i]; v[t * ND + i] = vo[i];
    }}
  }}
}}

// ---------------- stage B: QK^T (folded x10 over the query token) ----------
static void stage_scores(qkv_t q[NT * ND], qkv_t k[NT * ND], score_t scores[NS]) {{
#pragma HLS INLINE off
TOKB: for (int t = 0; t < NT; t++) {{
#pragma HLS PIPELINE II=1 rewind
{scores}
  }}
}}

// ---------------- stage C: the per-jet BARRIER (hls4ml's own softmax) ------
static void stage_softmax(score_t scores[NS], sm_t attn[NS]) {{
#pragma HLS INLINE off
  nnet::softmax_multidim<score_t, sm_t, softmax_config13>(scores, attn);
}}

// ---------------- stage D: attn.V (folded) -> Wo -> affine -> residual ----
static void stage_ctx_wo(sm_t attn[NS], qkv_t v[NT * ND], hin_t h[NT * ND],
                         bit_block_0_add_attn_t hres[NT * ND]) {{
#pragma HLS INLINE off
TOKD: for (int t = 0; t < NT; t++) {{
#pragma HLS PIPELINE II=1 rewind
    cacc_t ctxv[ND];
#pragma HLS ARRAY_PARTITION variable=ctxv complete dim=0
{ctx}
    ctx_t cx[ND];
#pragma HLS ARRAY_PARTITION variable=cx complete dim=0
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      cx[i] = (ctx_t)ctxv[i];
    }}
    oacc_t wo_o[ND];
#pragma HLS ARRAY_PARTITION variable=wo_o complete dim=0
{wo}
    wo_t won[ND]; bit_block_0_attn_Wo_affine_t woa[ND];
#pragma HLS ARRAY_PARTITION variable=won complete dim=0
#pragma HLS ARRAY_PARTITION variable=woa complete dim=0
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      won[i] = (wo_t)wo_o[i];
    }}
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      woa[i] = (bit_block_0_attn_Wo_affine_t)(won[i] * (wo_t)A22_S[i] + (wo_t)A22_B[i]);
    }}
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      hres[t * ND + i] = (bit_block_0_add_attn_t)(h[t * ND + i] + woa[i]);
    }}
  }}
}}

// ---------------- stage E: FFN (folded) -> affine -> residual -------------
static void stage_ffn(bit_block_0_add_attn_t hres[NT * ND], hout_t h_out[NT * ND]) {{
#pragma HLS INLINE off
TOKE: for (int t = 0; t < NT; t++) {{
#pragma HLS PIPELINE II=1 rewind
    bit_block_0_ffn_fc1_iq_t x1[ND];
#pragma HLS ARRAY_PARTITION variable=x1 complete dim=0
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      x1[i] = (bit_block_0_ffn_fc1_iq_t)hres[t * ND + i];
    }}
    f1acc_t y1[NF];
#pragma HLS ARRAY_PARTITION variable=y1 complete dim=0
{fc1}
    f1_t y1n[NF]; bit_block_0_ffn_act_t x2[NF];
#pragma HLS ARRAY_PARTITION variable=y1n complete dim=0
#pragma HLS ARRAY_PARTITION variable=x2 complete dim=0
    for (int i = 0; i < NF; i++) {{
#pragma HLS UNROLL
      y1n[i] = (f1_t)y1[i];                       // hls4ml casts to the layer type first
      x2[i] = (y1n[i] > (f1_t)0) ? (bit_block_0_ffn_act_t)y1n[i]
                                 : (bit_block_0_ffn_act_t)0;
    }}
    f2acc_t y2[ND];
#pragma HLS ARRAY_PARTITION variable=y2 complete dim=0
{fc2}
    f2_t y2n[ND]; bit_block_0_ffn_fc2_affine_t y2a[ND];
#pragma HLS ARRAY_PARTITION variable=y2n complete dim=0
#pragma HLS ARRAY_PARTITION variable=y2a complete dim=0
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      y2n[i] = (f2_t)y2[i];
    }}
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      y2a[i] = (bit_block_0_ffn_fc2_affine_t)(y2n[i] * (f2_t)A30_S[i] + (f2_t)A30_B[i]);
    }}
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      h_out[t * ND + i] = (hout_t)(hres[t * ND + i] + y2a[i]);
    }}
  }}
}}

// ---------------- top: the four token-serial stages + the barrier ---------
void myproject(hin_t h_in[NT * ND], hout_t h_out[NT * ND]) {{
#pragma HLS ARRAY_PARTITION variable=h_in complete dim=0
#pragma HLS ARRAY_PARTITION variable=h_out complete dim=0
#pragma HLS DATAFLOW
  qkv_t q[NT * ND], k[NT * ND], v[NT * ND];
#pragma HLS ARRAY_PARTITION variable=q complete dim=0
#pragma HLS ARRAY_PARTITION variable=k complete dim=0
#pragma HLS ARRAY_PARTITION variable=v complete dim=0
  score_t scores[NS];
#pragma HLS ARRAY_PARTITION variable=scores complete dim=0
  sm_t attn[NS];
#pragma HLS ARRAY_PARTITION variable=attn complete dim=0
  bit_block_0_add_attn_t hres[NT * ND];
#pragma HLS ARRAY_PARTITION variable=hres complete dim=0

  stage_qkv(h_in, q, k, v);
  stage_scores(q, k, scores);
  stage_softmax(scores, attn);
  stage_ctx_wo(attn, v, h_in, hres);
  stage_ffn(hres, h_out);
}}
'''

TB = '''#include <cstdio>
#include <cstdlib>
#include "myproject.h"

// Spatial reference: identical types, identical nnet:: glue, identical weights,
// no folding. Lives here so it is never synthesized.
extern void ed1_reference(hin_t h[NT * ND], hout_t out[NT * ND]);

int main() {
  srand(20260726);
  int bad = 0;
  for (int trial = 0; trial < 64; trial++) {
    hin_t h[NT * ND];
    for (int i = 0; i < NT * ND; i++)
      h[i] = (hin_t)(((rand() % 4096) - 2048) / 256.0);
    hout_t got[NT * ND], ref[NT * ND];
    myproject(h, got);
    ed1_reference(h, ref);
    for (int i = 0; i < NT * ND; i++)
      if (got[i] != ref[i]) {
        if (bad < 5)
          printf("MISMATCH i=%d got=%.10f ref=%.10f\\n", i,
                 got[i].to_double(), ref[i].to_double());
        bad++;
      }
  }
  printf(bad ? "FAIL %d mismatches\\n" : "EXACT_MATCH\\n", bad);
  return bad ? 1 : 0;
}
'''

BUILD = '''open_project -reset prj_ed1
set_top myproject
add_files myproject.cpp -cflags "-I."
add_files -tb tb.cpp -cflags "-I."
open_solution -reset sol1
set_part xcvu13p-flga2577-2-e
create_clock -period 2.5
csim_design
csynth_design
exit
'''

RUN = '''#!/bin/bash
# E-D1 — token-serial block-0 slice. Guarded (shared box).
set -u
source /data/software/xilinx/Vitis/2023.2/settings64.sh
cd "$(dirname "$0")"
while true; do
  nv=$(pgrep -c vitis_hls || true); free_gb=$(free -g | awk '/Mem:/{print $7}')
  [ "${nv:-0}" -le 2 ] && [ "${free_gb:-0}" -ge 40 ] && break
  echo "guard: vitis=$nv free=${free_gb}G — waiting 60s"; sleep 60
done
echo "=== ed1: $(date) ==="
vitis_hls -f build.tcl > vitis_hls.log 2>&1
echo "=== ed1 done rc=$? $(date) ==="
echo "ED1_DONE"
'''



REF = '''#ifndef __SYNTHESIS__
// ---------------------------------------------------------------------------
// Spatial reference for E-D1: the same block, same types, same nnet:: glue, same
// weights, computed with every index a compile-time constant and no folding. The
// folded top must match this bit for bit. Compiled into the testbench only.

{b_wq}
{b_wk}
{b_wv}
{b_wo}
{b_fc1}
{b_fc2}

void ed1_reference(hin_t h[NT * ND], hout_t out[NT * ND]) {{
  qkv_t q[NT * ND], k[NT * ND], v[NT * ND];
  for (int t = 0; t < NT; t++) {{
    qkv_in_t xq[ND], xk[ND], xv[ND];
    for (int i = 0; i < ND; i++) {{
      xq[i] = (qkv_in_t)h[t * ND + i];
      xk[i] = (qkv_in_t)h[t * ND + i];
      xv[i] = (qkv_in_t)h[t * ND + i];
    }}
    qacc_t qo[ND], ko[ND], vo[ND];
{wq}
{wk}
{wv}
    for (int i = 0; i < ND; i++) {{
      q[t * ND + i] = qo[i]; k[t * ND + i] = ko[i]; v[t * ND + i] = vo[i];
    }}
  }}

  score_t scores[NS];
{scores}

  sm_t attn[NS];
  nnet::softmax_multidim<score_t, sm_t, softmax_config13>(scores, attn);

  cacc_t ctxv[NT][ND];
{ctx}

  bit_block_0_add_attn_t hres[NT * ND];
  for (int t = 0; t < NT; t++) {{
    ctx_t cx[ND];
    for (int i = 0; i < ND; i++) cx[i] = (ctx_t)ctxv[t][i];
    oacc_t wo_o[ND];
{wo}
    wo_t won[ND]; bit_block_0_attn_Wo_affine_t woa[ND];
    for (int i = 0; i < ND; i++) won[i] = (wo_t)wo_o[i];
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      woa[i] = (bit_block_0_attn_Wo_affine_t)(won[i] * (wo_t)A22_S[i] + (wo_t)A22_B[i]);
    }}
    for (int i = 0; i < ND; i++)
      hres[t * ND + i] = (bit_block_0_add_attn_t)(h[t * ND + i] + woa[i]);
  }}

  for (int t = 0; t < NT; t++) {{
    bit_block_0_ffn_fc1_iq_t x1[ND];
    for (int i = 0; i < ND; i++)
      x1[i] = (bit_block_0_ffn_fc1_iq_t)hres[t * ND + i];
    f1acc_t y1[NF];
{fc1}
    f1_t y1n[NF]; bit_block_0_ffn_act_t x2[NF];
    for (int i = 0; i < NF; i++) {{
      y1n[i] = (f1_t)y1[i];
      x2[i] = (y1n[i] > (f1_t)0) ? (bit_block_0_ffn_act_t)y1n[i]
                                 : (bit_block_0_ffn_act_t)0;
    }}
    f2acc_t y2[ND];
{fc2}
    f2_t y2n[ND]; bit_block_0_ffn_fc2_affine_t y2a[ND];
    for (int i = 0; i < ND; i++) y2n[i] = (f2_t)y2[i];
    for (int i = 0; i < ND; i++) {{
#pragma HLS UNROLL
      y2a[i] = (bit_block_0_ffn_fc2_affine_t)(y2n[i] * (f2_t)A30_S[i] + (f2_t)A30_B[i]);
    }}
    for (int i = 0; i < ND; i++)
      out[t * ND + i] = (hout_t)(hres[t * ND + i] + y2a[i]);
  }}
}}
#endif  // __SYNTHESIS__
'''

if __name__ == "__main__":
    main()
