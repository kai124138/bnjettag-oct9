# Job Alpha 2026-08-15: post-synthesis of the 0-DSP fabric variant (the thesis point).
# No DSP demand -> no part-DSP-shortfall artifact; xczu7ev part caveat still applies.
set vdir ../r14n8-fabric/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
foreach f [glob -nocomplain $vdir/*.tcl] { source $f }
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
create_clock -period 2.5 -name ap_clk [get_ports ap_clk]
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
write_checkpoint -force post_synth.dcp
