"""E-1diag — diagnostic re-emissions of e1 arms P and B with structural
sub-blocks kept out of inlining (`#pragma HLS INLINE off`), so the csynth report
and a hierarchical Vivado utilization pass can attribute area to sub-blocks.
Closes two open gates left by Experiment 1:

  (P-diag) the 1.1509x parity offset: how much is the top-level I/O wrapper,
           how much the in-kernel bias add + output cast, how much the trees.
           Hierarchy: myproject -> token_dense x10 -> {adder_trees, bias_cast}.
  (B-diag) the FR realization discount (counted 3.07x -> measured 2.07x, ~33%):
           does the loss live in the Gray-chain pattern tables
           (matrix-independent => architectural, unfixable) or in the
           recombination rows (=> sharing may be recoverable)?
           Hierarchy: myproject -> token_dense x10 -> {fr_tables, fr_recombine}.

The sub-block bodies are e1_emit's own generated lines, split mechanically —
never re-derived — so the expressions are identical to the headline arms and the
tb EXACT_MATCH gate applies unchanged. Headline numbers remain e1's inlined
builds; these builds exist for attribution only and are never quoted as the
arm's area. The diag-total vs e1-inlined-total gap is itself a measurement:
what cross-boundary optimization was worth on this arm.

Usage: .venv-hgq2/bin/python bnjettag/code/analysis/e1_diag_emit.py
Output: bnjettag/results/adder-graph/e1diag/{p,b}/ + run_all.sh + postsyn/
"""

import re
from pathlib import Path

import e1_emit as E1

OUT = E1.REPO / "results/adder-graph/e1diag"

P_KERNEL = """static void adder_trees(input_t x[N_IN], acc_t s[N_OUT]) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
{trees}
}}

static void bias_cast(acc_t s[N_OUT], result_t y[N_OUT]) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
{bias}
}}

static void token_dense(input_t x[N_IN], result_t y[N_OUT]) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
  acc_t s[N_OUT];
#pragma HLS ARRAY_PARTITION variable=s complete dim=0
  adder_trees(x, s);
  bias_cast(s, y);
}}
"""

B_KERNEL = """static void fr_tables(input_t x[N_IN], gsum_t S[{ngrp}][{npat}]) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
{tables}
}}

static void fr_recombine(gsum_t S[{ngrp}][{npat}], result_t y[N_OUT]) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
{rows}
}}

static void token_dense(input_t x[N_IN], result_t y[N_OUT]) {{
#pragma HLS INLINE off
#pragma HLS PIPELINE II=1
  gsum_t S[{ngrp}][{npat}];
#pragma HLS ARRAY_PARTITION variable=S complete dim=0
  fr_tables(x, S);
  fr_recombine(S, y);
}}
"""

RUN_ALL = """#!/bin/bash
# E-1diag — sequential, guarded (shared box; see docs/infrastructure/mulder-setup.md)
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
for arm in p b; do
  guard
  echo "=== e1diag arm $arm: $(date) ==="
  (cd "$arm" && vitis_hls -f build.tcl > vitis_hls.log 2>&1)
  echo "=== e1diag arm $arm done rc=$? $(date) ==="
done
echo "E1DIAG_DONE"
"""

SYNTH_HIER_TCL = """set arm [lindex $argv 0]
set part "xczu7ev-ffvc1156-2-e"
set src "$::env(HOME)/csynth/e1diag/$arm/prj_$arm/sol1/syn/verilog"
foreach f [lsort [glob $src/*.v]] { puts "READ $f"; read_verilog $f }
read_xdc ../clk.xdc
synth_design -top myproject -part $part -mode out_of_context -flatten_hierarchy none
report_utilization -file util_$arm.rpt
report_utilization -hierarchical -file util_hier_$arm.rpt
report_timing_summary -file timing_$arm.rpt
puts "ARM_DONE $arm"
exit
"""

RUN_SYNTH_HIER = """#!/bin/bash
set -u
source /data/software/xilinx/Vivado/2023.2/settings64.sh
cd "$(dirname "$0")"
for arm in p b; do
  mkdir -p "$arm"; pushd "$arm" >/dev/null
  echo "=== VIVADO HIER SYNTH arm $arm start $(date -u) ==="
  vivado -mode batch -nojournal -log vivado_$arm.log -source ../synth_arm_hier.tcl -tclargs $arm > synth_$arm.out 2>&1
  echo "=== VIVADO HIER SYNTH arm $arm rc=$? end $(date -u) ==="
  popd >/dev/null
done
echo "ALL_HIER_SYNTH_DONE"
"""

CLK_XDC = 'create_clock -period 2.500 -name ap_clk [get_ports ap_clk]\n'

Y_LINE = re.compile(r"^  y\[(\d+)\] = \(acc_t\)\((.*)\) \+ \(acc_t\)BIAS\[\1\];$")


def split_naive(body):
    """e1's naive lines 'y[o] = (acc_t)(terms) + (acc_t)BIAS[o];' ->
    trees 's[o] = (acc_t)(terms);' + bias 'y[o] = s[o] + (acc_t)BIAS[o];'."""
    trees, bias = [], []
    for ln in body.split("\n"):
        m = Y_LINE.match(ln)
        assert m, f"unexpected naive line: {ln!r}"
        o, terms = m.group(1), m.group(2)
        trees.append(f"  s[{o}] = (acc_t)({terms});")
        bias.append(f"  y[{o}] = s[{o}] + (acc_t)BIAS[{o}];")
    return "\n".join(trees), "\n".join(bias)


def split_fr(body):
    """e1's fr_body -> (Gray-chain table lines, row-recombination lines).
    The S declaration + partition pragma are dropped (S becomes the interface
    array declared in token_dense)."""
    lines = body.split("\n")
    tables = [l for l in lines if l.startswith("  S[")]
    rows = [l for l in lines if l.startswith("  y[")]
    dropped = len(lines) - len(tables) - len(rows)
    assert dropped == 2, f"expected to drop exactly decl+pragma, dropped {dropped}"
    return "\n".join(tables), "\n".join(rows)


def emit(name, kernel_src, w, b, types):
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    hdr = E1.HEADER.format(n_tok=E1.N_TOK, n_in=E1.N_IN, n_out=E1.N_OUT, **types)
    src = ('#include "myproject.h"\n' + E1.bias_decl(b, types["bias_t"]) + "\n"
           + kernel_src + E1.TOP_SPATIAL.format() + "\n" + E1.w_ref_decl(w, b))
    (d / "myproject.h").write_text(hdr)
    (d / "myproject.cpp").write_text(src)
    (d / "tb.cpp").write_text(E1.TB.format())
    (d / "build.tcl").write_text(E1.BUILD_TCL.format(
        name=name, part=E1.PART, clock=E1.CLOCK, export=""))


def main():
    w, b, types = E1.load_layer()
    trees, bias = split_naive(E1.naive_body(w))
    tables, rows = split_fr(E1.fr_body(w))
    npat = 2 ** (E1.K - 1)
    emit("p", P_KERNEL.format(trees=trees, bias=bias), w, b, types)
    emit("b", B_KERNEL.format(ngrp=E1.N_GRP, npat=npat, tables=tables, rows=rows),
         w, b, types)
    run = OUT / "run_all.sh"
    run.write_text(RUN_ALL)
    run.chmod(0o755)
    ps = OUT / "postsyn"
    ps.mkdir(exist_ok=True)
    (ps / "synth_arm_hier.tcl").write_text(SYNTH_HIER_TCL)
    (ps / "clk.xdc").write_text(CLK_XDC)
    sh = ps / "run_synth_hier.sh"
    sh.write_text(RUN_SYNTH_HIER)
    sh.chmod(0o755)
    print(f"[e1diag] emitted arms p, b -> {OUT}")


if __name__ == "__main__":
    main()
