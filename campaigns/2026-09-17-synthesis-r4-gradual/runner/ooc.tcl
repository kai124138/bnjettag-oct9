# Invoked only after successful HLS report and nonempty emitted RTL checks.
if {$argc != 4} {
    error "usage: ooc.tcl RTL_DIRECTORY REPORT_DIRECTORY TOP CLOCK_XDC"
}
set rtl_dir [file normalize [lindex $argv 0]]
set report_dir [file normalize [lindex $argv 1]]
set top_name [lindex $argv 2]
set xdc_path [file normalize [lindex $argv 3]]
set target_part xczu7ev-ffvc1156-2-e
set_param general.maxThreads 4
file mkdir $report_dir
create_project -in_memory -part $target_part
set sources [lsort [glob -nocomplain -directory $rtl_dir *.v]]
set sv_sources [lsort [glob -nocomplain -directory $rtl_dir *.sv]]
if {[llength $sources] + [llength $sv_sources] == 0} {error "No emitted RTL"}
if {[llength $sources]} {read_verilog $sources}
if {[llength $sv_sources]} {read_verilog -sv $sv_sources}
set memory_files [glob -nocomplain -directory $rtl_dir *.dat *.mem]
if {[llength $memory_files]} {add_files -norecurse $memory_files}
# Clock constraints are loaded BEFORE synthesis, not merely before reporting.
read_xdc $xdc_path
synth_design -top $top_name -part $target_part -mode out_of_context
report_utilization -file [file join $report_dir post_synth_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file [file join $report_dir post_synth_timing.rpt]
write_checkpoint -force [file join $report_dir post_synth.dcp]
opt_design
report_utilization -file [file join $report_dir post_opt_utilization.rpt]
report_timing_summary -delay_type min_max -report_unconstrained -check_timing_verbose -file [file join $report_dir post_opt_timing.rpt]
write_checkpoint -force [file join $report_dir post_opt.dcp]
puts "VIVADO_OOC_REPORTS_COMPLETE target=$target_part"
exit
