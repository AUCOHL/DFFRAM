#	Yosys script
#	The main purpose is to elaborate the design only!	
#
#   Author: Mohamed Shalan (mshalan@aucegypt.edu)
#

yosys -import
set DESIGN 	DFFRAM
set SCL		./syn/sc_hd_tt.lib

read_liberty -lib -ignore_miss_dir -setattr blackbox ./syn/sc_hd_tt.lib
read_verilog  DFFRAMBB.v $DESIGN.v

hierarchy -check -top $DESIGN

synth -top $DESIGN -flatten

splitnets
opt_clean -purge

write_verilog -noattr -noexpr -nohex -nodec $DESIGN.gl.v
stat -top $DESIGN -liberty ./syn/sc_hd_tt.lib > $DESIGN.stats.txt

exit

