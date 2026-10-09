# Job Alpha 2026-08-15: post-synthesis calibration of the r14n8 fx8 baseline RTL.
# E-B2 recipe re-derived: Vivado 2023.2 synth_design OOC on xczu7ev (largest licensed
# part; xcvu13p blocked [Common 17-345]). Utilization is the target figure; timing
# reported against the 2.5 ns constraint for the WNS caveat register.
set vdir ../r14n8-w1a8s3-fx8-rf1/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
foreach f [glob -nocomplain $vdir/*.tcl] { source $f }
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
create_clock -period 2.5 -name ap_clk [get_ports ap_clk]
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
write_checkpoint -force post_synth.dcp
