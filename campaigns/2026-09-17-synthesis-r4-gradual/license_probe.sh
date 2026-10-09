#!/usr/bin/env bash
set -euo pipefail
RUN_ROOT="$HOME/bnjet_ebops_r4_20260917"
cd "$RUN_ROOT/license_probe"
export TMPDIR="$RUN_ROOT/tmp"
source /data/software/xilinx/Vitis/2023.2/settings64.sh
cat > probe.v <<'VERILOG'
module probe(input ap_clk, input a, output reg q);
always @(posedge ap_clk) q <= a;
endmodule
VERILOG
cat > probe.tcl <<'TCL'
set_param general.maxThreads 2
read_verilog probe.v
synth_design -mode out_of_context -top probe -part xcvu13p-flga2577-2-e
report_utilization -file probe_util.rpt
TCL
set +e
timeout --kill-after=30s 180s vivado -mode batch -source probe.tcl > probe.log 2>&1
rc=$?
printf '%s\n' "$rc" > exit_code
tail -18 probe.log
exit "$rc"
