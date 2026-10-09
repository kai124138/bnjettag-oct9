# Job Beta BETA-0 step (b), 2026-08-19: post-synthesis of the SCOPED-fabric folded 0-DSP point.
# constraints before synth_design (timing-driven) + opt_design. Part caveat: xczu7ev.
set vdir ../beta0-r14n8-pf1scoped/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
read_xdc ./clock.xdc
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
opt_design
report_utilization -file post_opt_util.rpt
report_timing_summary -file post_opt_timing.rpt -delay_type max -max_paths 5
