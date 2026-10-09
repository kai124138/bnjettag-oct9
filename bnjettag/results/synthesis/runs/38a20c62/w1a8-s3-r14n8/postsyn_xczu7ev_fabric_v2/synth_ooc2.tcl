# Job Alpha 2026-08-15 v2: CORRECTED post-synthesis of the 0-DSP fabric variant.
# Fixes from the verification pass: constraints read BEFORE synth_design (timing-driven),
# and opt_design run afterwards (v1 numbers were pre-opt upper bounds).
set vdir ../r14n8-fabric/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
read_xdc ./clock.xdc
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
opt_design
report_utilization -file post_opt_util.rpt
report_timing_summary -file post_opt_timing.rpt -delay_type max -max_paths 5
write_checkpoint -force post_opt.dcp
