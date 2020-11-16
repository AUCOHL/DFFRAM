set ::env(DESIGN_NAME) DFFRAM
set ::env(VERILOG_FILES) [glob $::env(DESIGN_DIR)/DFFRAM/Handcrafted/Models/*.v]
set ::env(SYNTH_TOP_LEVEL) 1
set ::env(SYNTH_READ_BLACKBOX_LIB) 1
set ::env(CLOCK_PERIOD) "10"
set ::env(CLOCK_PORT) "CLK"
set ::env(CLOCK_TREE_SYNTH) 0
set ::env(FP_CORE_UTIL) 83
set ::env(PL_TARGET_DENSITY) 0.89
set ::env(FP_ASPECT_RATIO) 0.6
set ::env(CELL_PAD) 0
set ::env(PL_OPENPHYSYN_OPTIMIZATIONS) 0
set ::env(DIODE_INSERTION_STRATEGY) 0
