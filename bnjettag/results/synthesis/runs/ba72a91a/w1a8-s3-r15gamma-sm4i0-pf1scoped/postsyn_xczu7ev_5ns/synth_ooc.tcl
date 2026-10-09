# Job Gamma (2026-08-24): Vivado OOC of the TRAINED 4-bit-softmax-grid arm, folded + scoped binding, at 5.000 ns.
# Same recipe as BETA-0/BETA-1 OOCs: read_xdc before synth_design (timing-driven), then opt_design; part xczu7ev.
set vdir ../gamma-sm4i0-n8-pf1scoped/myproject_prj/solution1/syn/verilog
read_verilog [glob $vdir/*.v]
read_xdc ./clock.xdc
synth_design -mode out_of_context -top myproject -part xczu7ev-ffvc1156-2-e
report_utilization -file post_synth_util.rpt
report_timing_summary -file post_synth_timing.rpt -delay_type max -max_paths 5
opt_design
report_utilization -file post_opt_util.rpt
report_timing_summary -file post_opt_timing.rpt -delay_type max -max_paths 5
