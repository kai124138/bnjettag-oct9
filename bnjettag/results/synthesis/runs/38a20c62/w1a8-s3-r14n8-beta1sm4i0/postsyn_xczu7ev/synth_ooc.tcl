# Job Gamma (Job Beta close-out) BETA-1 OOC, 2026-08-23: post-synthesis of the scoped-fabric
# folded point with the ctx-einsum softmax operand forced to ap_ufixed<4,0> (beta1-r14n8-sm4i0).
# Same recipe as BETA-0 step (b): constraints before synth_design (timing-driven) + opt_design.
# Part caveat: xczu7ev. PRIMARY quantity = whole-model DSP (pre-registered, experiment-log 2026-08-23).
set vdir ../beta1-r14n8-sm4i0/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
read_xdc ./clock.xdc
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
opt_design
report_utilization -file post_opt_util.rpt
report_timing_summary -file post_opt_timing.rpt -delay_type max -max_paths 5
