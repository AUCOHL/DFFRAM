#	Yosys script
#	The main purpose is to elaborate the design only!	
#
#   Author: Mohamed Shalan (mshalan@aucegypt.edu)
#

yosys -import
<<<<<<< HEAD
#set PDK_PATH /ef/tech/SW/sky130A
set DESIGN 	RAM512x32
set SCL		../../pdk/sc_hd_tt.lib
read_liberty -lib -ignore_miss_dir -setattr blackbox $SCL
read_verilog  ../Models/BB.v
#../Models/$DESIGN.v
=======

set PDK_PATH /ef/tech/SW/sky130A
if [info exists env(PDK_ROOT)] {
    set PDK_PATH $env(PDK_ROOT)/sky130/sky130A
}

if [info exists env(LIBERTY)] {
    set SCL $env(LIBERTY)
} else {
    set SCL	$PDK_PATH/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib
}

if [info exists env(DESIGN)] {
    set DESIGN $env(DESIGN)
} else {
    set DESIGN DFFRAM
}


read_liberty -lib -ignore_miss_dir -setattr blackbox $SCL
read_verilog  BB.v 
>>>>>>> 120f659c4e05ee482c8f93dabf24a0269783b697

hierarchy -check -top $DESIGN

synth -top $DESIGN -flatten

splitnets
opt_clean -purge

write_verilog -noattr -noexpr -nodec $DESIGN.gl.v
stat -top $DESIGN -liberty $SCL 

exit

