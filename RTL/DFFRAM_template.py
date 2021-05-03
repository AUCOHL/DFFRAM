parameterized_module = """
 module DFFRAM_RTL_{size}
 (
     CLK,
     WE,
     EN,
     Di,
     Do,
     A
 );
    localparam A_WIDTH = {addr_width};

    input   wire            CLK;
    input   wire    [3:0]   WE;
    input   wire            EN;
    input   wire    [31:0]  Di;
    output  reg     [31:0]  Do;
    input   wire    [(A_WIDTH - 1): 0]   A;
    reg [31:0] RAM[({words_num})-1 : 0];

    always @(posedge CLK)
        if(EN) begin
            Do <= RAM[A];
            if(WE[0]) RAM[A][ 7: 0] <= Di[7:0];
            if(WE[1]) RAM[A][15:8] <= Di[15:8];
            if(WE[2]) RAM[A][23:16] <= Di[23:16];
            if(WE[3]) RAM[A][31:24] <= Di[31:24];
        end
        else
            Do <= 32'b0;
 endmodule
 """

parameterized_config = """
set ::env(DESIGN_NAME) {design}
# Change if needed
set ::env(VERILOG_FILES) [glob $::env(DESIGN_DIR)/src/*.v]

# Fill this
set ::env(SYNTH_READ_BLACKBOX_LIB) 1
# Fill this
set ::env(CLOCK_PERIOD) "10"
set ::env(CLOCK_PORT) "CLK"
set ::env(CLOCK_TREE_SYNTH) 0

set ::env(FP_PIN_ORDER_CFG) $::env(DESIGN_DIR)/pin_order.cfg


set ::env(FP_CORE_UTIL) 75
set ::env(PL_TARGET_DENSITY) 0.80

set ::env(PDN_CFG) $::env(DESIGN_DIR)/pdn.tcl
set ::env(GLB_RT_MAXLAYER) 5

set ::env(PL_OPENPHYSYN_OPTIMIZATIONS) 0

set ::env(CELL_PAD) 0
set ::env(DIODE_INSERTION_STRATEGY) 4


set ::env(PL_RESIZER_DESIGN_OPTIMIZATIONS) 0
set ::env(PL_RESIZER_TIMING_OPTIMIZATIONS) 0
set ::env(ROUTING_CORES) 10
"""
