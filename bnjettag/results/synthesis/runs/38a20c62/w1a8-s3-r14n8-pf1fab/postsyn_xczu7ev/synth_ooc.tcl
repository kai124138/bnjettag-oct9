# 2026-08-18: post-synthesis of the folded 0-DSP point (pf1 + fabric), corrected recipe:
# constraints before synth_design (timing-driven) + opt_design. Part caveat: xczu7ev.
set vdir ../r14n8-w1a8s3-fx8-pf1fab/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
read_xdc ./clock.xdc
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
opt_design
report_utilization -file post_opt_util.rpt
report_timing_summary -file post_opt_timing.rpt -delay_type max -max_paths 5
