/*
    Copyright ©2020-2021 The American University in Cairo

    This file is part of the DFFRAM Memory Compiler.
    See https://github.com/Cloud-V/DFFRAM for further info.

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
*/

// Add 1x2 binary decoder
`default_nettype none

module DEC1x2 (
    input           EN,
    input           A,
    output [1:0]    SEL
);
    sky130_fd_sc_hd__and2b_2 AND0 ( .X(SEL[0]), .A_N(A), .B(EN) );
    sky130_fd_sc_hd__and2_2 AND1 ( .X(SEL[1]), .A(A) , .B(EN) );

endmodule

module DEC2x4 (
    input           EN,
    input   [1:0]   A,
    output  [3:0]   SEL
);
    sky130_fd_sc_hd__nor3b_2    AND0 ( .Y(SEL[0]), .A(A[0]),   .B(A[1]), .C_N(EN) );
    sky130_fd_sc_hd__and3b_2    AND1 ( .X(SEL[1]), .A_N(A[1]), .B(A[0]), .C(EN) );
    sky130_fd_sc_hd__and3b_2    AND2 ( .X(SEL[2]), .A_N(A[0]), .B(A[1]), .C(EN) ); // 4.600000
    sky130_fd_sc_hd__and3_2     AND3 ( .X(SEL[3]), .A(A[1]),   .B(A[0]), .C(EN) ); // 4.14
    
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
    
    (* keep = "true" *)
    sky130_fd_sc_hd__nor4b_2   AND0 ( .Y(SEL[0])  , .A(A_buf[0]), .B(A_buf[1])  , .C(A_buf[2]), .D_N(EN_buf) ); // 000

    sky130_fd_sc_hd__and4bb_2   AND1 ( .X(SEL[1])  , .A_N(A_buf[2]), .B_N(A_buf[1]), .C(A_buf[0])  , .D(EN_buf) ); // 001
    sky130_fd_sc_hd__and4bb_2   AND2 ( .X(SEL[2])  , .A_N(A_buf[2]), .B_N(A_buf[0]), .C(A_buf[1])  , .D(EN_buf) ); // 010
    sky130_fd_sc_hd__and4b_2    AND3 ( .X(SEL[3])  , .A_N(A_buf[2]), .B(A_buf[1]), .C(A_buf[0])  , .D(EN_buf) );   // 011
    sky130_fd_sc_hd__and4bb_2   AND4 ( .X(SEL[4])  , .A_N(A_buf[0]), .B_N(A_buf[1]), .C(A_buf[2])  , .D(EN_buf) ); // 100
    sky130_fd_sc_hd__and4b_2    AND5 ( .X(SEL[5])  , .A_N(A_buf[1]), .B(A_buf[0]), .C(A_buf[2])  , .D(EN_buf) );   // 101
    sky130_fd_sc_hd__and4b_2    AND6 ( .X(SEL[6])  , .A_N(A_buf[0]), .B(A_buf[1]), .C(A_buf[2])  , .D(EN_buf) );   // 110
    sky130_fd_sc_hd__and4_2     AND7 ( .X(SEL[7])  , .A(A_buf[0]), .B(A_buf[1]), .C(A_buf[2])  , .D(EN_buf) ); // 111
endmodule

module DEC5x32 (
    input   [4:0]   A,
    output  [31:0]  SEL
);
	wire [3:0]  EN;
	DEC3x8 D0 ( .A(A[2:0]), .SEL(SEL[7:0]),   .EN(EN[0]) );
	DEC3x8 D1 ( .A(A[2:0]), .SEL(SEL[15:8]),  .EN(EN[1]) );
	DEC3x8 D2 ( .A(A[2:0]), .SEL(SEL[23:16]), .EN(EN[2]) );
	DEC3x8 D3 ( .A(A[2:0]), .SEL(SEL[31:24]), .EN(EN[3]) );

    wire hi;
    sky130_fd_sc_hd__conb_1 TIE  (.LO(), .HI(hi));

	DEC2x4 D ( .A(A[4:3]), .SEL(EN), .EN(hi) );
endmodule

module MUX4x1 #(parameter   WIDTH=32)
(
    input   wire [WIDTH-1:0]     A0, A1, A2, A3,
    input   wire [1:0]          S,
    output  wire [WIDTH-1:0]     X
);
    localparam SIZE = WIDTH/8;
    wire [SIZE-1:0] SEL0, SEL1;

`ifndef NO_DIODES
    (* keep = "true" *)
    sky130_fd_sc_hd__diode_2 SEL_DIODE [1:0] (.DIODE(S));
`endif

    sky130_fd_sc_hd__clkbuf_2 SEL0BUF[SIZE-1:0] (.X(SEL0), .A(S[0]));
    sky130_fd_sc_hd__clkbuf_2 SEL1BUF[SIZE-1:0] (.X(SEL1), .A(S[1]));
    generate
        genvar i;

        for(i=0; i<SIZE; i=i+1) begin : M
`ifndef NO_DIODES
            (* keep = "true" *)
            sky130_fd_sc_hd__diode_2 DIODE_A0MUX [(i+1)*8-1:i*8] (.DIODE(A0[(i+1)*8-1:i*8]));   
            (* keep = "true" *)
            sky130_fd_sc_hd__diode_2 DIODE_A1MUX [(i+1)*8-1:i*8] (.DIODE(A1[(i+1)*8-1:i*8]));   
            (* keep = "true" *)
            sky130_fd_sc_hd__diode_2 DIODE_A2MUX [(i+1)*8-1:i*8] (.DIODE(A2[(i+1)*8-1:i*8]));   
            (* keep = "true" *)
            sky130_fd_sc_hd__diode_2 DIODE_A3MUX [(i+1)*8-1:i*8] (.DIODE(A3[(i+1)*8-1:i*8]));
`endif

            sky130_fd_sc_hd__mux4_1 MUX[7:0] (
                .A0(A0[(i+1)*8-1:i*8]), 
                .A1(A1[(i+1)*8-1:i*8]), 
                .A2(A2[(i+1)*8-1:i*8]), 
                .A3(A3[(i+1)*8-1:i*8]), 
                .S0(SEL0[i]), 
                .S1(SEL1[i]), 
                .X(X[(i+1)*8-1:i*8])
            );
        end
    endgenerate
endmodule

module MUX2x1 #(parameter   WIDTH=32)
(
    input   wire [WIDTH-1:0]    A0, A1,
    input   wire                S,
    output  wire [WIDTH-1:0]    X
);
    localparam SIZE = WIDTH/8;
    wire [SIZE-1:0] SEL;
    sky130_fd_sc_hd__clkbuf_2 SEL0BUF[SIZE-1:0] (.X(SEL), .A(S));
    generate
        genvar i;
        for(i=0; i<SIZE; i=i+1) begin : M
`ifndef NO_DIODES
            (* keep = "true" *)
            sky130_fd_sc_hd__diode_2 DIODE_A0MUX [(i+1)*8-1:i*8] (.DIODE(A0[(i+1)*8-1:i*8]));   
            (* keep = "true" *)
            sky130_fd_sc_hd__diode_2 DIODE_A1MUX [(i+1)*8-1:i*8] (.DIODE(A1[(i+1)*8-1:i*8])); 
`endif
            sky130_fd_sc_hd__mux2_1 MUX[7:0] (.A0(A0[(i+1)*8-1:i*8]), .A1(A1[(i+1)*8-1:i*8]), .S(SEL[i]), .X(X[(i+1)*8-1:i*8]) );
        end
    endgenerate
endmodule

module OUTREG #(parameter WIDTH=32)
(
    input   wire                CLK,        // FO: 8
    input   wire [WIDTH-1:0]    Di,         
    output  wire [WIDTH-1:0]    Do  
);
    localparam BYTE_CNT = WIDTH / 8;

    wire [BYTE_CNT-1:0] CLKBUF;
    wire CLK_buf;
    
    sky130_fd_sc_hd__clkbuf_4 Root_CLKBUF (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_4 Do_CLKBUF [BYTE_CNT-1:0] (.X(CLKBUF), .A(CLK_buf) );
    
    generate
        genvar i;
        for(i=0; i<BYTE_CNT; i=i+1) begin : OUTREG_BYTE
            `ifndef NO_DIODES    
                (* keep = "true" *)
                sky130_fd_sc_hd__diode_2 DIODE [7:0] (.DIODE(Di[(i+1)*8-1:i*8]));
            `endif
            sky130_fd_sc_hd__dfxtp_1 Do_FF [7:0] ( .D(Di[(i+1)*8-1:i*8]), .Q(Do[(i+1)*8-1:i*8]), .CLK(CLKBUF[i]) );
        end
    endgenerate
endmodule

module BYTE #(  parameter   USE_LATCH=1)( 
    input   wire        CLK,    // FO: 1
    input   wire        WE0,     // FO: 1
    input   wire        SEL0,    // FO: 2
    input   wire [7:0]  Di0,     // FO: 1
    output  wire [7:0]  Do0
);

    wire [7:0]  Q_WIRE;
    wire        WE0_WIRE;
    wire        SEL0_B;
    wire        GCLK;
    wire        CLK_B;

    generate 
        genvar i;
`ifndef NO_DIODES
        (* keep = "true" *)
        sky130_fd_sc_hd__diode_2 DIODE_CLK (.DIODE(CLK));
`endif

        if(USE_LATCH == 1) begin
            sky130_fd_sc_hd__inv_1 CLKINV(.Y(CLK_B), .A(CLK));
            sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK_B), .GCLK(GCLK), .GATE(WE0_WIRE) );
        end else begin
            sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK), .GCLK(GCLK), .GATE(WE0_WIRE) );
        end
    
        sky130_fd_sc_hd__inv_1 SEL0INV(.Y(SEL0_B), .A(SEL0));
        sky130_fd_sc_hd__and2_1 CGAND( .A(SEL0), .B(WE0), .X(WE0_WIRE) );
    
        for(i=0; i<8; i=i+1) begin : BIT
            if(USE_LATCH == 0)
                sky130_fd_sc_hd__dfxtp_1 STORAGE ( .D(Di0[i]), .Q(Q_WIRE[i]), .CLK(GCLK) );
            else 
                sky130_fd_sc_hd__dlxtp_1 STORAGE (.Q(Q_WIRE[i]), .D(Di0[i]), .GATE(GCLK) );
            sky130_fd_sc_hd__ebufn_2 OBUF0 ( .A(Q_WIRE[i]), .Z(Do0[i]), .TE_B(SEL0_B) );
        end
    endgenerate 
  
endmodule

module BYTE_1RW1R #(  parameter   USE_LATCH=1)( 
    input   wire        CLK,    // FO: 1
    input   wire        WE0,     // FO: 1
    input   wire        SEL0,   // FO: 2
    input   wire        SEL1,   // FO: 2
    input   wire [7:0]  Di0,     // FO: 1
    output  wire [7:0]  Do0,
    output  wire [7:0]  Do1
);

    wire [7:0]  Q_WIRE;
    wire        WE0_WIRE;
    wire        SEL0_B, SEL1_B;
    wire        GCLK;
    wire        CLK_B;

    generate 
        genvar i;
`ifndef NO_DIODES
        (* keep = "true" *)
        sky130_fd_sc_hd__diode_2 DIODE_CLK (.DIODE(CLK));
`endif

        if(USE_LATCH == 1) begin
            sky130_fd_sc_hd__inv_1 CLKINV(.Y(CLK_B), .A(CLK));
            sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK_B), .GCLK(GCLK), .GATE(WE0_WIRE) );
        end else
            sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK), .GCLK(GCLK), .GATE(WE0_WIRE) );
    
        sky130_fd_sc_hd__inv_1 SEL0INV (.Y(SEL0_B), .A(SEL0));
        sky130_fd_sc_hd__inv_1 SEL1INV (.Y(SEL1_B), .A(SEL1));
        sky130_fd_sc_hd__and2_1 CGAND( .A(SEL0), .B(WE0), .X(WE0_WIRE) );
    
        for(i=0; i<8; i=i+1) begin : BIT
            if(USE_LATCH == 0)
                sky130_fd_sc_hd__dfxtp_1 STORAGE ( .D(Di0[i]), .Q(Q_WIRE[i]), .CLK(GCLK) );
            else 
                sky130_fd_sc_hd__dlxtp_1 STORAGE (.Q(Q_WIRE[i]), .D(Di0[i]), .GATE(GCLK) );

            sky130_fd_sc_hd__ebufn_2 OBUF0 ( .A(Q_WIRE[i]), .Z(Do0[i]), .TE_B(SEL0_B) );
            sky130_fd_sc_hd__ebufn_2 OBUF1 ( .A(Q_WIRE[i]), .Z(Do1[i]), .TE_B(SEL1_B) );
        end
    endgenerate 
  
endmodule

module WORD #( parameter    USE_LATCH=0,
                            WSIZE=1 ) (
    input   wire                 CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input   wire                 SEL0,    // FO: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0
);

    wire CLK_buf;
    wire SEL0_buf;

    sky130_fd_sc_hd__clkbuf_4 CLKBUF (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_2 SEL0BUF (.X(SEL0_buf), .A(SEL0));
    generate
        genvar i;
            for(i=0; i<WSIZE; i=i+1) begin : BYTE
                BYTE #(.USE_LATCH(USE_LATCH)) B ( .CLK(CLK_buf), .WE0(WE0[i]), .SEL0(SEL0_buf), .Di0(Di0[(i+1)*8-1:i*8]), .Do0(Do0[(i+1)*8-1:i*8]) );
            end
    endgenerate
    
endmodule 

module WORD_1RW1R #( parameter  USE_LATCH=1,
                                WSIZE=1 ) (
    input   wire                CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input   wire                SEL0,    // FO: 1
    input   wire                SEL1,    // FO: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0,
    output  wire [(WSIZE*8-1):0] Do1
);

    wire SEL0_buf, SEL1_buf;
    wire CLK_buf;
    sky130_fd_sc_hd__clkbuf_2 SEL0BUF (.X(SEL0_buf), .A(SEL0));
    sky130_fd_sc_hd__clkbuf_2 SEL1BUF (.X(SEL1_buf), .A(SEL1));
    sky130_fd_sc_hd__clkbuf_4 CLKBUF (.X(CLK_buf), .A(CLK));
    generate
        genvar i;
            for(i=0; i<WSIZE; i=i+1) begin : BYTE
                BYTE_1RW1R #(.USE_LATCH(USE_LATCH)) B ( 
                    .CLK(CLK_buf), 
                    .WE0(WE0[i]), 
                    .SEL0(SEL0_buf), 
                    .SEL1(SEL1_buf), 
                    .Di0(Di0[(i+1)*8-1:i*8]), 
                    .Do0(Do0[(i+1)*8-1:i*8]),
                    .Do1(Do1[(i+1)*8-1:i*8])  
                );
            end
    endgenerate
    
endmodule 


module  CLKBUF_2  (input A, output X); 

sky130_fd_sc_hd__clkbuf_2  cell (.A(A), .X(X)); 

endmodule


module CLKBUF_16 (input A, output X); 

sky130_fd_sc_hd__clkbuf_16 cell (.A(A), .X(X));

endmodule

module DIODE (input DIODE);

sky130_fd_sc_hd__diode_2 cell (.DIODE(DIODE));

endmodule

module CLKBUF_4 (input A, output X); 

sky130_fd_sc_hd__clkbuf_4 cell (.A(A), .X(X));

endmodule

module CONB (output HI, output LO); 

sky130_fd_sc_hd__conb_1 cell (.HI(), .LO(LO)); 

endmodule

module EBUFN_2 (input A, input TE_B, output Z); 

sky130_fd_sc_hd__ebufn_2 cell ( .A(A), .TE_B(TE_B), .Z(Z));

endmodule

module RFWORD #(parameter WSIZE=32) 
(
    input   wire                CLK,
    input   wire                WE,
    input   wire                SEL1, 
    input   wire                SEL2, 
    input   wire                SELW,
    output  wire [WSIZE-1:0]   D1, D2,
    input   wire [WSIZE-1:0]   DW
);

    wire [WSIZE-1:0]   q_wire;
    wire                we_wire;
    wire [(WSIZE/8)-1:0]          SEL1_B, SEL2_B;
    wire [(WSIZE/8)-1:0]          GCLK;

    sky130_fd_sc_hd__inv_4 INV1[(WSIZE/8)-1:0] (.Y(SEL1_B), .A(SEL1));
	sky130_fd_sc_hd__inv_4 INV2[(WSIZE/8)-1:0] (.Y(SEL2_B), .A(SEL2));

    sky130_fd_sc_hd__and2_1 CGAND ( .A(SELW), .B(WE), .X(we_wire) );
    sky130_fd_sc_hd__dlclkp_1 CG[(WSIZE/8)-1:0] ( .CLK(CLK), .GCLK(GCLK), .GATE(we_wire) );

    generate 
        genvar i;
        for(i=0; i<WSIZE; i=i+1) begin : BIT
            sky130_fd_sc_hd__dfxtp_1 FF ( .D(DW[i]), .Q(q_wire[i]), .CLK(GCLK[i/8]) );
            sky130_fd_sc_hd__ebufn_2 OBUF1 ( .A(q_wire[i]), .Z(D1[i]), .TE_B(SEL1_B[i/8]) );
			sky130_fd_sc_hd__ebufn_2 OBUF2 ( .A(q_wire[i]), .Z(D2[i]), .TE_B(SEL2_B[i/8]) );
        end
		
    endgenerate 
endmodule

module RFWORD0 #(parameter WSIZE=32)
(
    input   wire                CLK,
    input   wire                SEL1, 
    input   wire                SEL2, 
    input   wire                SELW,
    output  wire [WSIZE-1:0]   D1, D2
);

    wire [WSIZE-1:0]           q_wire;
    wire                        we_wire;
    wire [(WSIZE/8)-1:0]                  SEL1_B, SEL2_B;
    wire [(WSIZE/8)-1:0]                  GCLK;
	wire [7:0]	                lo;

    sky130_fd_sc_hd__inv_4 INV1[(WSIZE/8)-1:0] (.Y(SEL1_B), .A(SEL1));
	sky130_fd_sc_hd__inv_4 INV2[(WSIZE/8)-1:0] (.Y(SEL2_B), .A(SEL2));

	sky130_fd_sc_hd__conb_1 TIE [7:0] (.LO(lo), .HI());

    generate 
        genvar i;
        for(i=0; i<WSIZE; i=i+1) begin : BIT
            sky130_fd_sc_hd__ebufn_2 OBUF1 ( .A(lo[i/8]), .Z(D1[i]), .TE_B(SEL1_B[i/8]) );
			sky130_fd_sc_hd__ebufn_2 OBUF2 ( .A(lo[4+i/8]), .Z(D2[i]), .TE_B(SEL2_B[i/8]) );
        end
    endgenerate 
endmodule