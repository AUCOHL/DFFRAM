set ::env(DESIGN_NAME) ${design}
# Change if needed
set ::env(VERILOG_FILES) [glob $::env(DESIGN_DIR)/*.v]

# Fill this
set ::env(SYNTH_READ_BLACKBOX_LIB) 1
# Fill this
set ::env(CLOCK_PERIOD) "10"
set ::env(CLOCK_PORT) "CLK"
set ::env(CLOCK_TREE_SYNTH) 1

set ::env(FP_PIN_ORDER_CFG) $::env(DESIGN_DIR)/pin_order.cfg


set ::env(FP_CORE_UTIL) 40
set ::env(PL_TARGET_DENSITY) 0.45

set ::env(GLB_RT_MAXLAYER) 5

set ::env(PL_OPENPHYSYN_OPTIMIZATIONS) 0

set ::env(CELL_PAD) 0
set ::env(FP_PDN_CHECK_NODES) 0
set ::env(DIODE_INSERTION_STRATEGY) 4


set ::env(PL_RESIZER_DESIGN_OPTIMIZATIONS) 0
set ::env(PL_RESIZER_TIMING_OPTIMIZATIONS) 0
set ::env(ROUTING_CORES) 10