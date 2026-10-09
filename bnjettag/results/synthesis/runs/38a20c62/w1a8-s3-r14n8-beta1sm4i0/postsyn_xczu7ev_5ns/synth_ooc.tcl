# Job Gamma Track 5, 2026-08-23: EASED-CLOCK OOC (5.000 ns) of the BETA-1 RTL (the fitting 0-DSP point).
# Same recipe as the 2.5-ns run (read_xdc before synth_design, then opt_design); ONLY clock.xdc differs.
# PRIMARY = post-opt WNS at 5 ns (experiment-log 2026-08-23). Part caveat: xczu7ev.
# This netlist NEVER replaces the 2.5-ns post-opt LUT (1,694,625) as the fit number.
set vdir ../beta1-r14n8-sm4i0/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
read_xdc ./clock.xdc
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
opt_design
report_utilization -file post_opt_util.rpt
report_timing_summary -file post_opt_timing.rpt -delay_type max -max_paths 5
