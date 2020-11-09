#	OpenSTA script
#	Clock frequency: 250 MHz (perioc = 4 ns)
#	Input delay (A and Di) : 800ps
#	Load on output ports (Do) : 0.0136390000 pF (pin cap of buf_16
#
#   Author: Mohamed Shalan (mshalan@aucegypt.edu)
#

set_cmd_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm -distance um

set DESIGN  DFFRAM
set SCL		./syn/sc_hd_tt.lib

read_liberty -min $SCL
read_liberty -max $SCL
read_verilog $DESIGN.gl.v
link_design $DESIGN

set IO_PCT          0.2     
set CLOCK_PERIOD    4
create_clock [get_ports CLK]  -name clk  -period $CLOCK_PERIOD
set input_delay_value [expr $CLOCK_PERIOD * $IO_PCT]
set output_delay_value [expr $CLOCK_PERIOD * $IO_PCT]

set_input_delay $input_delay_value  -clock clk [get_port A]
set_input_delay $input_delay_value  -clock clk [get_port EN]
set_input_delay $input_delay_value  -clock clk [get_port Di]
set_input_delay $input_delay_value  -clock clk [get_port WE]

set_load  0.0136390000 [all_outputs] 

report_checks -fields {capacitance slew input_pins nets fanout} -group_count 100  -slack_max -0.01 > ./syn/timing.rpt
#report_net -connections Do_pre[0]
#report_net -connections Do_pre[0]
exit
