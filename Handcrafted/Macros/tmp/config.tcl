set script_dir [file dirname [file normalize [info script]]]
# User config
set ::env(DESIGN_NAME) RAM_6Kx32

set ::env(DESIGN_IS_CORE) 0
set ::env(LVS_INSERT_POWER_PINS) 0

set ::env(ROUTING_CORES) 8

# Change if needed
set ::env(VERILOG_FILES) "\
	$script_dir/src/DFFRAM.v
	$script_dir/src/DFFRAMBB.v
	$script_dir/src/RAM_6Kx32.v"
	
# set ::env(SYNTH_TOP_LEVEL) 1
set ::env(SYNTH_READ_BLACKBOX_LIB) 1
# Fill this
set ::env(CLOCK_PERIOD) "10"
set ::env(CLOCK_PORT) "CLK"
set ::env(CLOCK_TREE_SYNTH) 0

set ::env(FP_PIN_ORDER_CFG) $::env(DESIGN_DIR)/pin_order-bot.cfg

set ::env(FP_SIZING) absolute
set ::env(DIE_AREA) "0 0 2900 3100"
set ::env(GLB_RT_OBS) "met5 $::env(DIE_AREA)"

#set ::env(FP_CORE_UTIL) 80
# set ::env(PL_TARGET_DENSITY) 0.

set ::env(PDN_CFG) $script_dir/pdn.tcl
set ::env(GLB_RT_MAXLAYER) 5

set ::env(PL_OPENPHYSYN_OPTIMIZATIONS) 0
set ::env(PL_TARGET_DENSITY) 0.85
set ::env(CELL_PAD) 0
set ::env(DIODE_INSERTION_STRATEGY) 3
