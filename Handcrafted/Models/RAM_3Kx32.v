`timescale 1ns / 1ps
`default_nettype none

module RAM_3Kx32 (
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
    input   [11:0]   A;

    localparam BLOCKS=3;
    wire  [3:0]       _EN_ ;
    wire [31:0] _Do_ [BLOCKS-1:0];
    wire [31:0] Do_pre;

    generate 
        genvar gi;
        for(gi=0; gi<BLOCKS; gi=gi+1) 

`ifdef USE_DFFRAM_BEH
	DFFRAM_beh 
`else
	DFFRAM
`endif
            #(.COLS(4)) RAM (
                .CLK(CLK),
                .WE(WE),
                .EN(_EN_[gi]),
                .Di(Di),
                .Do(_Do_[gi]),
                .A(A[9:0])
            );
        
    endgenerate 
    
    MUX4x1_32 MUX ( .A0(_Do_[0]), .A1(_Do_[1]), .A2(_Do_[2]), .A3(32'b0), .S(A[11:10]), .X(Do_pre) );
    DEC2x4 DEC ( .EN(EN), .A(A[11:10]), .SEL(_EN_) );

    sky130_fd_sc_hd__clkbuf_4 DOBUF[31:0] (.X(Do), .A(Do_pre));
    
endmodule