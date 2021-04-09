#	OpenSTA script
#	Clock frequency: 250 MHz (perioc = 4 ns)
#	Input delay (A and Di) : 800ps
#	Load on output ports (Do) : 0.0136390000 pF (pin cap of buf_16
#
#   Author: Mohamed Shalan (mshalan@aucegypt.edu)
#

#   docker run -e DESIGN -it -v $(pwd):/data openroad/opensta -f /data/sta.tcl

set_units -time ns -capacitance pF -current mA -voltage V -resistance kOhm


#set PDK_PATH /ef/tech/SW/sky130A
set DESIGN  RAM32x32
set SCL		/data/sc_hd_tt.lib
set VLG     /data/$DESIGN.gl.v
read_liberty -min $SCL
read_liberty -max $SCL
read_verilog $VLG
link_design $DESIGN

set IO_PCT          0.2     
set CLOCK_PERIOD    0
create_clock [get_ports CLK]  -name clk  -period $CLOCK_PERIOD
set input_delay_value [expr $CLOCK_PERIOD * $IO_PCT]
set output_delay_value [expr $CLOCK_PERIOD * $IO_PCT]

set_input_delay $input_delay_value  -clock clk [get_port A]
set_input_delay $input_delay_value  -clock clk [get_port EN]
set_input_delay $input_delay_value  -clock clk [get_port Di]
set_input_delay $input_delay_value  -clock clk [get_port WE]

set_output_delay $output_delay_value  -clock clk [get_port Do]


set_load  0.0136390000 [all_outputs] 

#report_checks -fields {capacitance slew input_pins nets fanout} -group_count 100  -slack_max -0.01 > /data/timing.rpt
#report_net -connections Do_pre[0]
#report_net -connections Do_pre[0]
report_checks -fields {capacitance slew input_pins nets fanout}  -path_delay max_rise -group_count 2 > /data/timing.rpt
exit