/*
    Building blocks for DFF based RAM compiler for SKY130A 
    BYTE        :   8 memory cells used as a building block for WORD module
    WORD        :   32-bit memory word with select and byte-level WE
    DEC6x64     :   2x4 Binary Decoder
    DEC6x64     :   6x64 Binary decoder
    MUX4x1_32   :   32-bit 4x1 MUX
    MUX2x1_32   :   32-bit 2x1 MUX
    SRAM64x32   :   Tri-state buffers based 64x32 DFF RAM 
    DFFRAM_COL4 :   A single column of 4 SRAM64x32 blocks using 4x1 multiplexors
*/
/*
    Author: Mohamed Shalan (mshalan@aucegypt.edu)
*/

module BYTE (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input CLK,
    input WE,
    input SEL,
    input [7:0] Di,
    output [7:0] Do
);

    wire [7:0]  q_wire;
    wire        we_wire;
    wire        SEL_B;
    wire        GCLK;

    sky130_fd_sc_hd__inv_1 INV(
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .Y(SEL_B),
        .A(SEL)
    );

    sky130_fd_sc_hd__and2_1 CGAND(
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .A(SEL),
        .B(WE),
        .X(we_wire)
    );

    sky130_fd_sc_hd__dlclkp_1 CG(
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .CLK(CLK),
        .GCLK(GCLK),
        .GATE(we_wire)
    );

    generate
        genvar i;
        for(i=0; i<8; i=i+1) begin : BIT
            sky130_fd_sc_hd__dfxtp_1 FF (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
                .VPB(VPWR),
                .VNB(VGND),
            `endif
                .D(Di[i]),
                .Q(q_wire[i]),
                .CLK(GCLK)
            );

            sky130_fd_sc_hd__ebufn_2 OBUF (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
                .VPB(VPWR),
                .VNB(VGND),
            `endif
                .A(q_wire[i]),
                .Z(Do[i]),
                .TE_B(SEL_B)
            );
        end
    endgenerate

endmodule

module BYTE_LATCH (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input CLK,
    input WE,
    input SEL,
    input [7:0] Di,
    output [7:0] Do
);

    wire [7:0]  q_wire;
    wire        we_wire;
    wire        SEL_B;
    wire        GCLK;
    wire        CLK_B;

    sky130_fd_sc_hd__inv_1 SELINV(
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .Y(SEL_B),
        .A(SEL)
    );

    sky130_fd_sc_hd__inv_1 CLKINV(
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .Y(CLK_B),
        .A(CLK)
    );

    sky130_fd_sc_hd__and2_1 CGAND(
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .A(SEL),
        .B(WE),
        .X(we_wire)
    );

    sky130_fd_sc_hd__dlclkp_1 CG(
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .CLK(CLK_B),
        .GCLK(GCLK),
        .GATE(we_wire)
    );

    generate
        genvar i;
        for(i=0; i<8; i=i+1) begin : BIT
            //sky130_fd_sc_hd__dfxtp_1 FF (
            //`ifdef USE_POWER_PINS
            //    .VPWR(VPWR),
            //    .VGND(VGND),
            //    .VPB(VPWR),
            //    .VNB(VGND),
            //`endif
            //    .D(Di[i]),
            //    .Q(q_wire[i]),
            //    .CLK(GCLK)
            //);
            sky130_fd_sc_hd__dlxtp_1 LATCH (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
                .VPB(VPWR),
                .VNB(VGND),
            `endif
                .Q(q_wire[i]),
                .D(Di[i]),
                .GATE(GCLK)
            );

            sky130_fd_sc_hd__ebufn_2 OBUF (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
                .VPB(VPWR),
                .VNB(VGND),
            `endif
                .A(q_wire[i]),
                .Z(Do[i]),
                .TE_B(SEL_B)
            );
        end
    endgenerate

endmodule

module WORD32 #(parameter USE_LATCH=1)(
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input CLK,
    input [3:0] WE,
    input SEL,
    input [31:0] Di,
    output [31:0] Do
);

    generate
        if(USE_LATCH == 1) begin
            BYTE_LATCH B0 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK),
                .WE(WE[0]),
                .SEL(SEL),
                .Di(Di[7:0]),
                .Do(Do[7:0])
            );

            BYTE_LATCH B1 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK),
                .WE(WE[1]),
                .SEL(SEL),
                .Di(Di[15:8]),
                .Do(Do[15:8])
            );

            BYTE_LATCH B2 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK),
                .WE(WE[2]),
                .SEL(SEL),
                .Di(Di[23:16]),
                .Do(Do[23:16])
            );

            BYTE_LATCH B3 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK),
                .WE(WE[3]),
                .SEL(SEL),
                .Di(Di[31:24]),
                .Do(Do[31:24])
            );
        end else begin
            BYTE B0 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK),
                .WE(WE[0]),
                .SEL(SEL),
                .Di(Di[7:0]),
                .Do(Do[7:0])
            );

            BYTE B1 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK),
                .WE(WE[1]),
                .SEL(SEL),
                .Di(Di[15:8]),
                .Do(Do[15:8])
            );

            BYTE B2 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK),
                .WE(WE[2]),
                .SEL(SEL),
                .Di(Di[23:16]),
                .Do(Do[23:16])
            );

            BYTE B3 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK),
                .WE(WE[3]),
                .SEL(SEL),
                .Di(Di[31:24]),
                .Do(Do[31:24])
            );
        end
    endgenerate
endmodule

module DEC1x2 (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input           EN,
    input   [0:0]   A,
    output  [1:0]   SEL
);
    sky130_fd_sc_hd__and2b_2    AND1 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[0]),
        .A_N(A),
        .B(EN)
    );

    sky130_fd_sc_hd__and2_2     AND3 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[1]),
        .A(A),
        .B(A[0])
    );

endmodule

module DEC2x4 (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input           EN,
    input   [1:0]   A,
    output  [3:0]   SEL
);
    sky130_fd_sc_hd__nor3b_4    AND0 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .Y(SEL[0]),
        .A(A[0]),
        .B(A[1]),
        .C_N(EN)
    );

    sky130_fd_sc_hd__and3b_4    AND1 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[1]),
        .A_N(A[1]),
        .B(A[0]),
        .C(EN)
    );

    sky130_fd_sc_hd__and3b_4    AND2 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[2]),
        .A_N(A[0]),
        .B(A[1]),
        .C(EN)
    );

    sky130_fd_sc_hd__and3_4     AND3 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[3]),
        .A(A[1]),
        .B(A[0]),
        .C(EN)
    );

endmodule

module DEC3x8 (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input           EN,
    input [2:0]     A,
    output [7:0]    SEL
);

    wire [2:0]  A_buf;
    wire        EN_buf;

    sky130_fd_sc_hd__clkbuf_1 ABUF[2:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(A_buf),
        .A(A)
    );

    sky130_fd_sc_hd__clkbuf_2 ENBUF (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(EN_buf),
        .A(EN)
    );

    sky130_fd_sc_hd__nor4b_2   AND0 ( // 000
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .Y(SEL[0]),
        .A(A_buf[0]),
        .B(A_buf[1]),
        .C(A_buf[2]),
        .D_N(EN_buf)
    );

    sky130_fd_sc_hd__and4bb_2   AND1 ( // 001
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[1]),
        .A_N(A_buf[2]),
        .B_N(A_buf[1]),
        .C(A_buf[0]),
        .D(EN_buf)
    );

    sky130_fd_sc_hd__and4bb_2   AND2 ( // 010
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[2]),
        .A_N(A_buf[2]),
        .B_N(A_buf[0]),
        .C(A_buf[1]),
        .D(EN_buf)
    );

    sky130_fd_sc_hd__and4b_2    AND3 ( // 011
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[3]),
        .A_N(A_buf[2]),
        .B(A_buf[1]),
        .C(A_buf[0]),
        .D(EN_buf)
    );

    sky130_fd_sc_hd__and4bb_2   AND4 ( // 100
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[4]),
        .A_N(A_buf[0]),
        .B_N(A_buf[1]),
        .C(A_buf[2]),
        .D(EN_buf)
    );

    sky130_fd_sc_hd__and4b_2    AND5 ( // 101
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[5]),
        .A_N(A_buf[1]),
        .B(A_buf[0]),
        .C(A_buf[2]),
        .D(EN_buf)
    );

    sky130_fd_sc_hd__and4b_2    AND6 ( // 110
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[6]),
        .A_N(A_buf[0]),
        .B(A_buf[1]),
        .C(A_buf[2]),
        .D(EN_buf)
    );

    sky130_fd_sc_hd__and4_2     AND7 ( // 111
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL[7]),
        .A(A_buf[0]),
        .B(A_buf[1]),
        .C(A_buf[2]),
        .D(EN_buf)
    );
endmodule

module DEC6x64 (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input           EN,
    input   [5:0]   A,
    output  [63:0] SEL
);
    wire [7:0] SEL0_w ;
    wire [2:0] A_buf;

    DEC3x8 DEC_L0 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .EN(EN),
        .A(A[5:3]),
        .SEL(SEL0_w)
    );

    sky130_fd_sc_hd__clkbuf_16 ABUF[2:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(A_buf),
        .A(A[2:0])
    );

    generate
        genvar i;
        for(i=0; i<8; i=i+1) begin : DEC_L1
            DEC3x8 U (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .EN(SEL0_w[i]),
                .A(A_buf),
                .SEL(SEL[7+8*i: 8*i])
            );
        end
    endgenerate
endmodule

module MUX2x1_32(
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input   [31:0]      A0, A1,
    input   [0:0]       S,
    output  [31:0]      X
);
    sky130_fd_sc_hd__mux2_1 MUX[31:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .A0(A0),
        .A1(A1),
        .S(S[0]),
        .X(X)
    );
endmodule

module MUX4x1_32(
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input   [31:0]      A0, A1, A2, A3,
    input   [1:0]       S,
    output  [31:0]      X
);
    sky130_fd_sc_hd__mux4_1 MUX[31:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .A0(A0),
        .A1(A1),
        .A2(A2),
        .A3(A3),
        .S0(S[0]),
        .S1(S[1]),
        .X(X)
    );
endmodule

module PASS (input [31:0] A, output [31:0] X);
    assign X = A;
endmodule

module SRAM8x32 #(parameter USE_LATCH=0) (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input CLK,
    input [3:0] WE,
    input EN,
    input [31:0] Di,
    output [31:0] Do,
    input [2:0] A
);

    wire  [7:0] SEL, SEL_buf, CLK_buf;
    wire [3:0] WE_buf[7:0]; // WE_buf!

    DEC3x8 DEC (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .EN(EN),
        .A(A),
        .SEL(SEL)
    );

    sky130_fd_sc_hd__clkbuf_2 SELBUF[7:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(SEL_buf),
        .A(SEL)
    );

    generate
        genvar i;
        for (i=0; i< 8; i=i+1) begin : WORD
            WORD32 #(.USE_LATCH(USE_LATCH)) W (
                `ifdef USE_POWER_PINS
                    .VPWR(VPWR),
                    .VGND(VGND),
                `endif
                    .CLK(CLK_buf[i]),
                    .WE(WE_buf[i]),
                    .SEL(SEL_buf[i]),
                    .Di(Di),
                    .Do(Do)
                );

            sky130_fd_sc_hd__clkbuf_1 CLKBUF (
                `ifdef USE_POWER_PINS
                    .VPWR(VPWR),
                    .VGND(VGND),
                    .VPB(VPWR),
                    .VNB(VGND),
                `endif
                    .X(CLK_buf[i]),
                    .A(CLK)
                );

            sky130_fd_sc_hd__clkbuf_1 WEBUF[3:0] (
                `ifdef USE_POWER_PINS
                    .VPWR(VPWR),
                    .VGND(VGND),
                    .VPB(VPWR),
                    .VNB(VGND),
                `endif
                    .X(WE_buf[i]),
                    .A(WE)
                );
        end
    endgenerate

endmodule

module SRAM64x32 #(parameter USE_LATCH=0) (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input CLK,
    input [3:0] WE,
    input EN,
    input [31:0] Di,
    output [31:0] Do,
    input [5:0] A
);
    wire [7:0] SEL;
    wire [2:0] A_buf;
    wire CLK_buf;
    wire [3:0] WE_buf;

    wire [31:0]     Do_pre;
    wire [31:0]     Di_buf;

    sky130_fd_sc_hd__clkbuf_16 DIBUF[31:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(Di_buf),
        .A(Di)
    );

    sky130_fd_sc_hd__clkbuf_2 CLKBUF (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(CLK_buf),
        .A(CLK)
    );

    sky130_fd_sc_hd__clkbuf_2 WEBUF[3:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(WE_buf),
        .A(WE)
    );

    sky130_fd_sc_hd__clkbuf_1 ABUF[2:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
       .X(A_buf),
       .A(A[2:0])
    );

    DEC3x8 DEC (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .EN(EN),
        .A(A[5:3]),
        .SEL(SEL)
    );

    generate
        genvar i;
        for (i=0; i< 8; i=i+1) begin : SLICE
            SRAM8x32 #(.USE_LATCH(USE_LATCH)) RAM8x32 (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK_buf),
                .WE(WE_buf),
                .EN(SEL[i]),
                .Di(Di_buf),
                .Do(Do_pre),
                .A(A_buf)
            );
        end
    endgenerate

    // Ensure that the Do_pre lines are not floating when EN = 0
    wire [3:0] lo;
    wire [3:0] float_buf_en;

    sky130_fd_sc_hd__clkbuf_4 FBUFENBUF [3:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(float_buf_en),
        .A(EN)
    );

    sky130_fd_sc_hd__conb_1 TIE [3:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .LO(lo),
        .HI()
    );

    sky130_fd_sc_hd__ebufn_2 FLOATBUF_B0[7:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .A(lo[0]),
        .Z(Do_pre[7:0]),
        .TE_B(float_buf_en[0])
    );

    sky130_fd_sc_hd__ebufn_2 FLOATBUF_B1[15:8] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .A(lo[1]),
        .Z(Do_pre[15:8]),
        .TE_B(float_buf_en[1])
    );

    sky130_fd_sc_hd__ebufn_2 FLOATBUF_B2[23:16] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .A(lo[2]),
        .Z(Do_pre[23:16]),
        .TE_B(float_buf_en[2])
    );

    sky130_fd_sc_hd__ebufn_2 FLOATBUF_B3[31:24] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .A(lo[3]),
        .Z(Do_pre[31:24]),
        .TE_B(float_buf_en[3])
    );

    generate
        //genvar i;
        for(i=0; i<32; i=i+1) begin : OUT
            sky130_fd_sc_hd__dfxtp_1 FF (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
                .VPB(VPWR),
                .VNB(VGND),
            `endif
                .D(Do_pre[i]),
                .Q(Do[i]),
                .CLK(CLK)
            );
        end
    endgenerate

endmodule

/*
module SRAM64x32 #(parameter USE_LATCH=0) (
    input CLK,
    input [3:0] WE,
    input EN,
    input [31:0] Di,
    output [31:0] Do,
    input [5:0] A
);

    wire [63:0]     SEL;
    wire [31:0]     Do_pre;
    wire [31:0]     Di_buf;
    wire            CLK_buf;
    wire [3:0]      WE_buf;

    sky130_fd_sc_hd__clkbuf_16 CLKBUF (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_16 WEBUF[3:0] (.X(WE_buf), .A(WE));
    sky130_fd_sc_hd__clkbuf_16 DIBUF[31:0] (.X(Di_buf), .A(Di));

    DEC6x64 DEC  ( .EN(EN), .A(A), .SEL(SEL) );

    generate
        genvar i;
        for (i=0; i< 64; i=i+1) begin : WORD
            WORD32 #(.USE_LATCH(USE_LATCH)) W (
            `ifdef USE_POWER_PINS
                .VPWR(VPWR),
                .VGND(VGND),
            `endif
                .CLK(CLK_buf),
                .WE(WE_buf),
                .SEL(SEL[i]),
                .Di(Di_buf),
                .Do(Do_pre)
            );
        end
    endgenerate

    // Ensure that the Do_pre lines are not floating when EN = 0
    wire lo;
    wire float_buf_en;
    sky130_fd_sc_hd__clkbuf_4 FBUFENBUF( .X(float_buf_en), .A(EN) );
    sky130_fd_sc_hd__conb_1 TIE (.LO(lo), .HI());
    sky130_fd_sc_hd__ebufn_4 FLOATBUF[31:0] ( .A( lo ), .Z(Do_pre), .TE_B(float_buf_en) );

    generate
        //genvar i;
        for(i=0; i<32; i=i+1) begin : OUT
            sky130_fd_sc_hd__dfxtp_1 FF ( .D(Do_pre[i]), .Q(Do[i]), .CLK(CLK) );
        end
    endgenerate

endmodule
*/
module DFFRAM_COL4 #( parameter USE_LATCH=0 ) (
`ifdef USE_POWER_PINS
    input VPWR,
    input VGND,
`endif
    input           CLK,
    input   [3:0]   WE,
    input           EN,
    input   [31:0]  Di,
    output  [31:0]  Do,
    input   [7:0]   A
);

    wire [31:0]     Di_buf;
    wire [31:0]     Do_pre;
    wire            CLK_buf;
    wire [3:0]      WE_buf;
    wire [7:0]      A_buf;

    wire [31:0]     Do_B_0_0;
    wire [31:0]     Do_B_0_1;
    wire [31:0]     Do_B_0_2;
    wire [31:0]     Do_B_0_3;

    wire [3:0]      row_sel;

    sky130_fd_sc_hd__clkbuf_4 CLKBUF (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(CLK_buf),
        .A(CLK)
    );

    sky130_fd_sc_hd__clkbuf_4 WEBUF[3:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(WE_buf),
        .A(WE)
    );

    sky130_fd_sc_hd__clkbuf_8 DIBUF[31:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(Di_buf),
        .A(Di)
    );

    sky130_fd_sc_hd__clkbuf_8 ABUF[7:0] (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
        .VPB(VPWR),
        .VNB(VGND),
    `endif
        .X(A_buf),
        .A(A[7:0])
    );

    DEC2x4 DEC (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .EN(EN),
        .A(A[7:6]),
        .SEL(row_sel)
    );

    SRAM64x32 #(.USE_LATCH(USE_LATCH)) B_0_0 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .CLK(CLK_buf),
        .WE(WE_buf),
        .EN(row_sel[0]),
        .Di(Di_buf),
        .Do(Do_B_0_0),
        .A(A_buf[5:0])
    );

    SRAM64x32 #(.USE_LATCH(USE_LATCH)) B_0_1 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .CLK(CLK_buf),
        .WE(WE_buf),
        .EN(row_sel[1]),
        .Di(Di_buf),
        .Do(Do_B_0_1),
        .A(A_buf[5:0])
    );

    SRAM64x32 #(.USE_LATCH(USE_LATCH)) B_0_2 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .CLK(CLK_buf),
        .WE(WE_buf),
        .EN(row_sel[2]),
        .Di(Di_buf),
        .Do(Do_B_0_2),
        .A(A_buf[5:0])
    );

    SRAM64x32 #(.USE_LATCH(USE_LATCH)) B_0_3 (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .CLK(CLK_buf),
        .WE(WE_buf),
        .EN(row_sel[3]),
        .Di(Di_buf),
        .Do(Do_B_0_3),
        .A(A_buf[5:0])
    );

    MUX4x1_32 MUX (
    `ifdef USE_POWER_PINS
        .VPWR(VPWR),
        .VGND(VGND),
    `endif
        .A0(Do_B_0_0),
        .A1(Do_B_0_1),
        .A2(Do_B_0_2),
        .A3(Do_B_0_3),
        .S(A_buf[7:6]),
        .X(Do)
    );
endmodule
