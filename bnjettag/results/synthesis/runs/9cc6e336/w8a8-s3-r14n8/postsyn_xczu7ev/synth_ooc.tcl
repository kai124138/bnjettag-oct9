# W8A8 n8 RF=1 baseline OOC (2026-08-24): read_xdc before synth_design, then opt_design; part xczu7ev.
set vdir ../w8a8-n8-rf1/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
read_xdc ./clock.xdc
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
opt_design
report_utilization -file post_opt_util.rpt
report_timing_summary -file post_opt_timing.rpt -delay_type max -max_paths 5
