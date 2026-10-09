create_clock -name ap_clk -period 2.500 [get_ports ap_clk]
# Clock-only OOC constraint matches the historical Vivado comparison.
# HLS independently retains its exported 27% scheduling uncertainty.
