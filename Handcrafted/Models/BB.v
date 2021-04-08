/*
    Building blocks for DFF based RAM compiler for SKY130A 
    BYTE        :   8 memory cells used as a building block for WORD module (FF based)
    BYTE_LATCH  :   8 memory cells used as a building block for WORD module (Latch based)  
    WORD        :   32-bit memory word with select and byte-level WE
    DEC2x4      :   2x4 Binary Decoder
    DEC3x8      :   3x8 Binary decoder
    MUX4x1_32   :   32-bit 4x1 MUX
    RAM8x32     :   8x32 (8 32-bit words) RAM with tri-state output 
    RAM16x32    :   32 words RAM with registered output
    RAM128x32   :   512 bytes (128x32) RAM
    RAM512x32   :   2 kbytes (512x32) RAM
*/

module BYTE (
    input   wire        CLK,    // FO: 1
    input   wire        WE,     // FO: 1
    input   wire        SEL,    // FO: 2
    input   wire [7:0]  Di,     // FO: 1
    output  wire [7:0]  Do
);

    wire [7:0]  q_wire;
    wire        we_wire;
    wire        SEL_B;
    wire        GCLK;

    sky130_fd_sc_hd__inv_1 SELINV(.Y(SEL_B), .A(SEL));
    sky130_fd_sc_hd__and2_1 CGAND( .A(SEL), .B(WE), .X(we_wire) );
    sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK), .GCLK(GCLK), .GATE(we_wire) );
    generate 
        genvar i;
        for(i=0; i<8; i=i+1) begin : BIT
            sky130_fd_sc_hd__dfxtp_1 FF ( .D(Di[i]), .Q(q_wire[i]), .CLK(GCLK) );
            sky130_fd_sc_hd__ebufn_2 OBUF ( .A(q_wire[i]), .Z(Do[i]), .TE_B(SEL_B) );
        end
    endgenerate 
  
endmodule

module BYTE_LATCH (
    input   wire        CLK,    // FO: 1
    input   wire        WE,     // FO: 1
    input   wire        SEL,    // FO: 2
    input   wire [7:0]  Di,     // FO: 1
    output  wire [7:0]  Do
);

    wire [7:0]  q_wire;
    wire        we_wire;
    wire        SEL_B;
    wire        GCLK;
    wire        CLK_B;

    sky130_fd_sc_hd__inv_1 CLKINV(.Y(CLK_B), .A(CLK));
    sky130_fd_sc_hd__inv_1 SELINV(.Y(SEL_B), .A(SEL));
    sky130_fd_sc_hd__and2_1 CGAND( .A(SEL), .B(WE), .X(we_wire) );
    sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK_B), .GCLK(GCLK), .GATE(we_wire) );

    generate 
        genvar i;
        for(i=0; i<8; i=i+1) begin : BIT
            sky130_fd_sc_hd__dlxtp_1 LATCH (.Q(q_wire[i]), .D(Di[i]), .GATE(GCLK) );
            sky130_fd_sc_hd__ebufn_2 OBUF ( .A(q_wire[i]), .Z(Do[i]), .TE_B(SEL_B) );
        end
    endgenerate 

endmodule

module WORD32 #(parameter USE_LATCH=1)(
    input   wire        CLK,    // FO: 1
    input   wire [3:0]  WE,     // FO: 1
    input   wire        SEL,    // FO: 1
    input   wire [31:0] Di,     // FO: 1
    output  wire [31:0] Do
);

    wire SEL_buf;
    wire CLK_buf;
    sky130_fd_sc_hd__clkbuf_2 SELBUF (.X(SEL_buf), .A(SEL));
    sky130_fd_sc_hd__clkbuf_1 CLKBUF (.X(CLK_buf), .A(CLK));
    generate
        if(USE_LATCH == 1) begin
            BYTE_LATCH B0 ( .CLK(CLK_buf), .WE(WE[0]), .SEL(SEL_buf), .Di(Di[7:0]), .Do(Do[7:0]) );
            BYTE_LATCH B1 ( .CLK(CLK_buf), .WE(WE[1]), .SEL(SEL_buf), .Di(Di[15:8]), .Do(Do[15:8]) );
            BYTE_LATCH B2 ( .CLK(CLK_buf), .WE(WE[2]), .SEL(SEL_buf), .Di(Di[23:16]), .Do(Do[23:16]) );
            BYTE_LATCH B3 ( .CLK(CLK_buf), .WE(WE[3]), .SEL(SEL_buf), .Di(Di[31:24]), .Do(Do[31:24]) );
        end else begin
            BYTE B0 ( .CLK(CLK_buf), .WE(WE[0]), .SEL(SEL_buf), .Di(Di[7:0]), .Do(Do[7:0]) );
            BYTE B1 ( .CLK(CLK_buf), .WE(WE[1]), .SEL(SEL_buf), .Di(Di[15:8]), .Do(Do[15:8]) );
            BYTE B2 ( .CLK(CLK_buf), .WE(WE[2]), .SEL(SEL_buf), .Di(Di[23:16]), .Do(Do[23:16]) );
            BYTE B3 ( .CLK(CLK_buf), .WE(WE[3]), .SEL(SEL_buf), .Di(Di[31:24]), .Do(Do[31:24]) );
        end
    endgenerate
endmodule 


module DEC2x4 (
    input           EN,
    input   [1:0]   A,
    output  [3:0]   SEL
);
    sky130_fd_sc_hd__nor3b_4    AND0 ( .Y(SEL[0]), .A(A[0]),   .B(A[1]), .C_N(EN) );
    sky130_fd_sc_hd__and3b_4    AND1 ( .X(SEL[1]), .A_N(A[1]), .B(A[0]), .C(EN) );
    sky130_fd_sc_hd__and3b_4    AND2 ( .X(SEL[2]), .A_N(A[0]), .B(A[1]), .C(EN) );
    sky130_fd_sc_hd__and3_4     AND3 ( .X(SEL[3]), .A(A[1]),   .B(A[0]), .C(EN) );
    
endmodule

module DEC3x8 (
    input           EN,
    input [2:0]     A,
    output [7:0]    SEL
);

    wire [2:0]  A_buf;
    wire        EN_buf;

    sky130_fd_sc_hd__clkbuf_2 ABUF[2:0] (.X(A_buf), .A(A));
    sky130_fd_sc_hd__clkbuf_2 ENBUF (.X(EN_buf), .A(EN));
    
    sky130_fd_sc_hd__nor4b_2   AND0 ( .Y(SEL[0])  , .A(A_buf[0]), .B(A_buf[1])  , .C(A_buf[2]), .D_N(EN_buf) ); // 000
    sky130_fd_sc_hd__and4bb_2   AND1 ( .X(SEL[1])  , .A_N(A_buf[2]), .B_N(A_buf[1]), .C(A_buf[0])  , .D(EN_buf) ); // 001
    sky130_fd_sc_hd__and4bb_2   AND2 ( .X(SEL[2])  , .A_N(A_buf[2]), .B_N(A_buf[0]), .C(A_buf[1])  , .D(EN_buf) ); // 010
    sky130_fd_sc_hd__and4b_2    AND3 ( .X(SEL[3])  , .A_N(A_buf[2]), .B(A_buf[1]), .C(A_buf[0])  , .D(EN_buf) );   // 011
    sky130_fd_sc_hd__and4bb_2   AND4 ( .X(SEL[4])  , .A_N(A_buf[0]), .B_N(A_buf[1]), .C(A_buf[2])  , .D(EN_buf) ); // 100
    sky130_fd_sc_hd__and4b_2    AND5 ( .X(SEL[5])  , .A_N(A_buf[1]), .B(A_buf[0]), .C(A_buf[2])  , .D(EN_buf) );   // 101
    sky130_fd_sc_hd__and4b_2    AND6 ( .X(SEL[6])  , .A_N(A_buf[0]), .B(A_buf[1]), .C(A_buf[2])  , .D(EN_buf) );   // 110
    sky130_fd_sc_hd__and4_2     AND7 ( .X(SEL[7])  , .A(A_buf[0]), .B(A_buf[1]), .C(A_buf[2])  , .D(EN_buf) ); // 111
endmodule


module MUX4x1_32(
    input   wire [31:0]      A0, A1, A2, A3,
    input   wire [1:0]       S,
    output  wire [31:0]      X
);
    sky130_fd_sc_hd__mux4_1 MUX[31:0] (.A0(A0), .A1(A1), .A2(A2), .A3(A3), .S0(S[0]), .S1(S[1]), .X(X) );
endmodule


// A slice of 8 words
module RAM8x32 #(parameter USE_LATCH=0) (
    input   wire        CLK,    // FO: 1
    input   wire [3:0]  WE,     // FO: 1
    input               EN,     // EN: 1
    input   wire [31:0] Di,
    output  wire [31:0] Do,
    input   wire [2:0]  A       // A: 1
);

    wire    [7:0]   SEL;
    wire    [3:0]   WE_buf; 
    wire            CLK_buf;

    DEC3x8 DEC (.EN(EN), .A(A), .SEL(SEL));
    sky130_fd_sc_hd__clkbuf_2 WEBUF[3:0] (.X(WE_buf), .A(WE));
    sky130_fd_sc_hd__clkbuf_2 CLKBUF (.X(CLK_buf), .A(CLK));

    generate
        genvar i;
        for (i=0; i< 8; i=i+1) begin : WORD
            WORD32 #(.USE_LATCH(USE_LATCH)) W ( .CLK(CLK_buf), .WE(WE_buf), .SEL(SEL[i]), .Di(Di), .Do(Do) );
        end
    endgenerate

endmodule

// 8 Slices block (128 bytes) with registered outout 
module RAM32x32 #(parameter USE_LATCH=0) (
    input   wire        CLK,    // FO: 1
    input   wire [3:0]  WE,     // FO: 1
    input               EN,     // FO: 1
    input   wire [31:0] Di,     // FO: 1
    output  wire [31:0] Do,
    input   wire [4:0]  A       // FO: 1
);
    wire [3:0]  SEL;
    wire [4:0]  A_buf;
    wire        CLK_buf;
    wire [3:0]  WE_buf;
    wire        EN_buf;

    wire [31:0] Do_pre;
    wire [31:0] Di_buf;

    // Buffers
    sky130_fd_sc_hd__clkbuf_16 DIBUF[31:0] (.X(Di_buf), .A(Di));
    sky130_fd_sc_hd__clkbuf_2 CLKBUF (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_2 WEBUF[3:0] (.X(WE_buf), .A(WE));

    // Should be in decoder?
    sky130_fd_sc_hd__clkbuf_2 ABUF[4:0] (.X(A_buf), .A(A[4:0]));
    sky130_fd_sc_hd__clkbuf_2 ENBUF (.X(EN_buf), .A(EN));

    DEC2x4 DEC (.EN(EN_buf), .A(A_buf[4:3]), .SEL(SEL));

    generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : SLICE
            RAM8x32 #(.USE_LATCH(USE_LATCH)) RAM8x32 (.CLK(CLK_buf), .WE(WE_buf),.EN(SEL[i]), .Di(Di_buf), .Do(Do_pre), .A(A_buf[2:0]) ); 
        end
    endgenerate

    // Ensure that the Do_pre lines are not floating when EN = 0
    wire [3:0] lo;
    wire [3:0] float_buf_en;
    sky130_fd_sc_hd__clkinv_4 FBUFENBUF [3:0] ( .Y(float_buf_en), .A(EN) );
    sky130_fd_sc_hd__conb_1 TIE [3:0] (.LO(lo), .HI());

    // Following split by group because each is done by one TIE CELL and ONE CLKINV_4

    // Provides default values for floating lines (lo)
    sky130_fd_sc_hd__ebufn_2 FLOATBUF_B0[7:0] ( .A( lo[0] ), .Z(Do_pre[7:0]), .TE_B(float_buf_en[0]) );
    sky130_fd_sc_hd__ebufn_2 FLOATBUF_B1[15:8] ( .A( lo[1] ), .Z(Do_pre[15:8]), .TE_B(float_buf_en[1]) );
    sky130_fd_sc_hd__ebufn_2 FLOATBUF_B2[23:16] ( .A( lo[2] ), .Z(Do_pre[23:16]), .TE_B(float_buf_en[2]) );
    sky130_fd_sc_hd__ebufn_2 FLOATBUF_B3[31:24] ( .A( lo[3] ), .Z(Do_pre[31:24]), .TE_B(float_buf_en[3]) );

    generate 
        //genvar i;
        for(i=0; i<32; i=i+1) begin : OUT
            sky130_fd_sc_hd__dfxtp_1 FF ( .D(Do_pre[i]), .Q(Do[i]), .CLK(CLK) );
        end
    endgenerate 

endmodule

// 512 bytes RAM made out of blocks and muxes
module RAM128x32 #(parameter USE_LATCH=0) (
    input   wire        CLK,    // FO: 1
    input   wire [3:0]  WE,     // FO: 1
    input               EN,     // FO: 1
    input   wire [31:0] Di,     // FO: 1
    output  wire [31:0] Do,
    input   wire [6:0]  A       // FO: 1
);

    wire        CLK_buf;
    wire [3:0]  WE_buf;
    wire        EN_buf;
    wire [4:0]  A_buf;
    wire [31:0] Di_buf;

    wire [31:0] Do_0, Do_1, Do_2, Do_3;

    // Buffers
    sky130_fd_sc_hd__clkbuf_16  DIBUF[31:0] (.X(Di_buf),  .A(Di));
    sky130_fd_sc_hd__clkbuf_2   CLKBUF      (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_2   WEBUF[3:0]  (.X(WE_buf),  .A(WE));
    sky130_fd_sc_hd__clkbuf_2   ENBUF       (.X(EN_buf),  .A(EN));
    sky130_fd_sc_hd__clkbuf_2   ABUF[4:0]   (.X(A_buf),   .A(A[4:0]));

    // 32x32 RAM Banks
    RAM32x32 #(.USE_LATCH(USE_LATCH)) B0 (.CLK(CLK_buf), .EN(EN), .Di(Di_buf), .Do(Do_0), .A(A_buf[4:0]) );    
    RAM32x32 #(.USE_LATCH(USE_LATCH)) B1 (.CLK(CLK_buf), .EN(EN), .Di(Di_buf), .Do(Do_1), .A(A_buf[4:0]) );    
    RAM32x32 #(.USE_LATCH(USE_LATCH)) B2 (.CLK(CLK_buf), .EN(EN), .Di(Di_buf), .Do(Do_1), .A(A_buf[4:0]) );    
    RAM32x32 #(.USE_LATCH(USE_LATCH)) B3 (.CLK(CLK_buf), .EN(EN), .Di(Di_buf), .Do(Do_1), .A(A_buf[4:0]) );    

    // Output MUX
    MUX4x1_32 DoMUX ( .A0(Do_0), .A1(Do_1), .A2(Do_2), .A3(Do_3), .S(A_buf[6:5]), .X(Do) );

endmodule

// 2kbytes RAM made out of 16 blocks (4x4)
module RAM512x32 #(parameter USE_LATCH=0) (
    input   wire        CLK,    // FO: 1
    input   wire [3:0]  WE,     // FO: 1
    input               EN,     // FO: 1
    input   wire [31:0] Di,     // FO: 1
    output  wire [31:0] Do,
    input   wire [8:0]  A       // FO: 1
);

    wire        CLK_buf;
    wire [3:0]  WE_buf;
    wire        EN_buf;
    wire [6:0]  A_buf;
    wire [31:0] Di_buf;

    wire [31:0] Do_0, Do_1, Do_2, Do_3;

    // Buffers
    sky130_fd_sc_hd__clkbuf_16  DIBUF[31:0] (.X(Di_buf),  .A(Di));
    sky130_fd_sc_hd__clkbuf_2   CLKBUF      (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_2   WEBUF[3:0]  (.X(WE_buf),  .A(WE));
    sky130_fd_sc_hd__clkbuf_1   ENBUF       (.X(EN_buf),  .A(EN));
    sky130_fd_sc_hd__clkbuf_2   ABUF[6:0]   (.X(A_buf),   .A(A[6:0]));

    // 32x32 RAM Banks
    RAM128x32 #(.USE_LATCH(USE_LATCH)) B0 (.CLK(CLK_buf), .EN(EN), .Di(Di_buf), .Do(Do_0), .A(A_buf[6:0]) );    
    RAM128x32 #(.USE_LATCH(USE_LATCH)) B1 (.CLK(CLK_buf), .EN(EN), .Di(Di_buf), .Do(Do_1), .A(A_buf[6:0]) );    
    RAM128x32 #(.USE_LATCH(USE_LATCH)) B2 (.CLK(CLK_buf), .EN(EN), .Di(Di_buf), .Do(Do_1), .A(A_buf[6:0]) );    
    RAM128x32 #(.USE_LATCH(USE_LATCH)) B3 (.CLK(CLK_buf), .EN(EN), .Di(Di_buf), .Do(Do_1), .A(A_buf[6:0]) );    

    // Output MUX
    MUX4x1_32 DoMUX ( .A0(Do_0), .A1(Do_1), .A2(Do_2), .A3(Do_3), .S(A_buf[8:7]), .X(Do) );

endmodule