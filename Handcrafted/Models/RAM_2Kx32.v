`timescale 1ns / 1ps
`default_nettype none

module RAM_2Kx32 (
    CLK,
    WE,
    EN,
    Di,
    Do,
    A
);
    input           CLK;
    input   [3:0]   WE;
    input           EN;
    input   [31:0]  Di;
    output  [31:0]  Do;
    input   [10:0]   A;

    wire _EN_[1:0];
    wire [31:0] _Do_ [1:0];
    wire [31:0] Do_pre;
    wire A10_buf;
    
`ifdef USE_DFFRAM_BEH
	DFFRAM_beh 
`else
	DFFRAM
`endif
            #(.COLS(4)) RAM (
                .CLK(CLK),
                .WE(WE),
                .EN(_EN_[0]),
                .Di(Di),
                .Do(_Do_[0]),
                .A(A[9:0])
            );
        
`ifdef USE_DFFRAM_BEH
	DFFRAM_beh 
`else
	DFFRAM
`endif
            #(.COLS(4)) RAM (
                .CLK(CLK),
                .WE(WE),
                .EN(_EN_[1]),
                .Di(Di),
                .Do(_Do_[1]),
                .A(A[9:0])
            );

    sky130_fd_sc_hd__clkbuf_8 A10BUF (.X(A10_buf), .A(A[10]));
    
    MUX2x1_32 MUX ( .A0(_Do_[0]), .A1(_Do_[1]), .S(A10_buf), .X(Do_pre) );
    
    assign _EN_[0] = ~A10_buf;
    assign _EN_[0] = A10_buf;
    
    sky130_fd_sc_hd__clkbuf_4 DOBUF[31:0] (.X(Do), .A(Do_pre));
    
endmodule