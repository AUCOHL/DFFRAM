/*
	1KByte DFF based RAM (a single column) for SKY130A
*/

/*
    Author: Mohamed Shalan (mshalan@aucegypt.edu)
*/

module DFFRAM_256x32 #( parameter COLS=1, parameter ROWS=4)
(
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
    input   [7:0]   A;

    
    wire [31:0]     Di_buf;
    wire [31:0]     Do_pre;
    wire            CLK_buf;
    wire [3:0]      WE_buf;

    wire [31:0]     Do_B_0_0;
    wire [31:0]     Do_B_0_1;
    wire [31:0]     Do_B_0_2;
    wire [31:0]     Do_B_0_3;

    wire [3:0]      row_sel;

    sky130_fd_sc_hd__clkbuf_8 CLKBUF (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_8 WEBUF[3:0] (.X(WE_buf), .A(WE));
    sky130_fd_sc_hd__clkbuf_8 DIBUF[31:0] (.X(Di_buf), .A(Di));

    DEC2x4 DEC ( .EN(EN), .A(A[7:6]), .SEL(row_sel) );

    SRAM64x32 B_0_0 ( .CLK(CLK_buf), .WE(WE_buf), .EN(row_sel[0]), .Di(Di_buf), .Do(Do_B_0_0), .A(A[5:0]) );
    SRAM64x32 B_0_1 ( .CLK(CLK_buf), .WE(WE_buf), .EN(row_sel[1]), .Di(Di_buf), .Do(Do_B_0_1), .A(A[5:0]) );
    SRAM64x32 B_0_2 ( .CLK(CLK_buf), .WE(WE_buf), .EN(row_sel[2]), .Di(Di_buf), .Do(Do_B_0_2), .A(A[5:0]) );
    SRAM64x32 B_0_3 ( .CLK(CLK_buf), .WE(WE_buf), .EN(row_sel[3]), .Di(Di_buf), .Do(Do_B_0_3), .A(A[5:0]) );

    MUX4x1_32 MUX1 ( .A0(Do_B_0_0), .A1(Do_B_0_1), .A2(Do_B_0_2), .A3(Do_B_0_3), .S(A[7:6]), .X(Do_pre) );

    sky130_fd_sc_hd__clkbuf_4 DOBUF[31:0] (.X(Do), .A(Do_pre));

endmodule
