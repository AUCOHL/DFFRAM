#	Yosys script
#	The main purpose is to elaborate the design only!	
#
#   Author: Mohamed Shalan (mshalan@aucegypt.edu)
#

yosys -import
#set PDK_PATH /ef/tech/SW/sky130A
set DESIGN 	RAM512x32
set SCL		../../pdk/sc_hd_tt.lib
read_liberty -lib -ignore_miss_dir -setattr blackbox $SCL
read_verilog  ../Models/BB.v
#../Models/$DESIGN.v

hierarchy -check -top $DESIGN

synth -top $DESIGN -flatten

splitnets
opt_clean -purge

write_verilog -noattr -noexpr -nodec $DESIGN.gl.v
stat -top $DESIGN -liberty $SCL 

exit

