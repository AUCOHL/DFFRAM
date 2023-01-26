/*
    Copyright ©2020-2021 The American University in Cairo and the Cloud V Project.

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

    wire A_N; 

    gf180mcu_fd_sc_mcu7t5v0__inv_2 INV1 (.ZN(A_N), .I(A));
    
    gf180mcu_fd_sc_mcu7t5v0__and2_2 AND0 ( .Z(SEL[0]), .A1(A_N), .A2(EN) );
    
    gf180mcu_fd_sc_mcu7t5v0__and2_2 AND1 ( .Z(SEL[1]), .A1(A) , .A2(EN) );

endmodule

module DEC2x4 (
    input           EN,
    input   [1:0]   A,
    output  [3:0]   SEL
);

wire [1:0] A_N;
wire       EN_N;   

    gf180mcu_fd_sc_mcu7t5v0__inv_2 INV1 (.ZN(A_N[0]), .I(A[0]));
    gf180mcu_fd_sc_mcu7t5v0__inv_2 INV2 (.ZN(A_N[1]), .I(A[1]));
    gf180mcu_fd_sc_mcu7t5v0__inv_2 INV3 (.ZN(EN_N), .I(EN));

    gf180mcu_fd_sc_mcu7t5v0__nor3_2    AND0 ( .ZN(SEL[0]), .A1(A[0]),   .A2(A[1]), .A3(EN_N) );
    gf180mcu_fd_sc_mcu7t5v0__and3_2    AND1 ( .Z(SEL[1]), .A1(A_N[1]), .A2(A[0]), .A3(EN) );
    gf180mcu_fd_sc_mcu7t5v0__and3_2    AND2 ( .Z(SEL[2]), .A1(A_N[0]), .A2(A[1]), .A3(EN) ); // 4.600000
    gf180mcu_fd_sc_mcu7t5v0__and3_2     AND3 ( .Z(SEL[3]), .A1(A[1]),   .A2(A[0]), .A3(EN) ); // 4.14
    
endmodule

module DEC3x8 (
    input           EN,
    input [2:0]     A,
    output [7:0]    SEL
);

    wire [2:0]  A_buf;
    wire        EN_buf;

    wire [2:0] A_buf_N; 
    wire       EN_buf_N;




    gf180mcu_fd_sc_mcu7t5v0__clkbuf_2 ABUF[2:0] (.Z(A_buf), .I(A));
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_2 ENBUF (.Z(EN_buf), .I(EN));

    gf180mcu_fd_sc_mcu7t5v0__inv_2 INV1 (.ZN(A_buf_N[0]), .I(A_buf[0]));
    gf180mcu_fd_sc_mcu7t5v0__inv_2 INV2 (.ZN(A_buf_N[1]), .I(A_buf[1]));
    gf180mcu_fd_sc_mcu7t5v0__inv_2 INV3 (.ZN(A_buf_N[1]), .I(A_buf[1]));

    gf180mcu_fd_sc_mcu7t5v0__inv_2 INV4 (.ZN(EN_buf_N), .I(EN_buf));
    
    gf180mcu_fd_sc_mcu7t5v0__nor4_2   AND0 ( .ZN(SEL[0])  , .A1(A_buf[0]), .A2(A_buf[1])  , .A3(A_buf[2]), .A4(EN_buf_N) ); // 000
    gf180mcu_fd_sc_mcu7t5v0__and4_2   AND1 ( .Z(SEL[1])  , .A1(A_buf_N[2]), .A2(A_buf_N[1]), .A3(A_buf[0])  , .A4(EN_buf) ); // 001
    gf180mcu_fd_sc_mcu7t5v0__and4_2   AND2 ( .Z(SEL[2])  , .A1(A_buf_N[2]), .A2(A_buf_N[0]), .A3(A_buf[1])  , .A4(EN_buf) ); // 010
    gf180mcu_fd_sc_mcu7t5v0__and4_2    AND3 ( .Z(SEL[3])  , .A1(A_buf_N[2]), .A2(A_buf[1]), .A3(A_buf[0])  , .A4(EN_buf) );   // 011
    gf180mcu_fd_sc_mcu7t5v0__and4_2   AND4 ( .Z(SEL[4])  , .A1(A_buf_N[0]), .A2(A_buf_N[1]), .A3(A_buf[2])  , .A4(EN_buf) ); // 100
    gf180mcu_fd_sc_mcu7t5v0__and4_2    AND5 ( .Z(SEL[5])  , .A1(A_buf_N[1]), .A2(A_buf[0]), .A3(A_buf[2])  , .A4(EN_buf) );   // 101
    gf180mcu_fd_sc_mcu7t5v0__and4_2    AND6 ( .Z(SEL[6])  , .A1(A_buf_N[0]), .A2(A_buf[1]), .A3(A_buf[2])  , .A4(EN_buf) );   // 110
    gf180mcu_fd_sc_mcu7t5v0__and4_2     AND7 ( .Z(SEL[7])  , .A1(A_buf[0]), .A2(A_buf[1]), .A3(A_buf[2])  , .A4(EN_buf) ); // 111
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
    gf180mcu_fd_sc_mcu7t5v0__tieh TIE  (.Z(hi));

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
    gf180mcu_fd_sc_mcu7t5v0__antenna SEL_DIODE [1:0] (.I(S));
`endif

    gf180mcu_fd_sc_mcu7t5v0__clkbuf_2 SEL0BUF[SIZE-1:0] (.Z(SEL0), .I(S[0]));
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_2 SEL1BUF[SIZE-1:0] (.Z(SEL1), .I(S[1]));
    generate
        genvar i;

        for(i=0; i<SIZE; i=i+1) begin : M
`ifndef NO_DIODES
            (* keep = "true" *)
            gf180mcu_fd_sc_mcu7t5v0__antenna DIODE_A0MUX [(i+1)*8-1:i*8] (.I(A0[(i+1)*8-1:i*8]));   
            (* keep = "true" *)
            gf180mcu_fd_sc_mcu7t5v0__antenna DIODE_A1MUX [(i+1)*8-1:i*8] (.I(A1[(i+1)*8-1:i*8]));   
            (* keep = "true" *)
            gf180mcu_fd_sc_mcu7t5v0__antenna DIODE_A2MUX [(i+1)*8-1:i*8] (.I(A2[(i+1)*8-1:i*8]));   
            (* keep = "true" *)
            gf180mcu_fd_sc_mcu7t5v0__antenna DIODE_A3MUX [(i+1)*8-1:i*8] (.I(A3[(i+1)*8-1:i*8]));
`endif

            gf180mcu_fd_sc_mcu7t5v0__mux4_1 MUX[7:0] (
                .I0(A0[(i+1)*8-1:i*8]),
                .I1(A1[(i+1)*8-1:i*8]),
                .I2(A2[(i+1)*8-1:i*8]),
                .I3(A3[(i+1)*8-1:i*8]),
                .S0(SEL0[i]), 
                .S1(SEL1[i]), 
                .Z(X[(i+1)*8-1:i*8])
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
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_2 SEL0BUF[SIZE-1:0] (.Z(SEL), .I(S));
    generate
        genvar i;
        for(i=0; i<SIZE; i=i+1) begin : M
`ifndef NO_DIODES
            (* keep = "true" *)
            gf180mcu_fd_sc_mcu7t5v0__antenna DIODE_A0MUX [(i+1)*8-1:i*8] (.I(A0[(i+1)*8-1:i*8]));   
            (* keep = "true" *)
            gf180mcu_fd_sc_mcu7t5v0__antenna DIODE_A1MUX [(i+1)*8-1:i*8] (.I(A1[(i+1)*8-1:i*8])); 
`endif
            gf180mcu_fd_sc_mcu7t5v0__mux2_1 MUX[7:0] (.I0(A0[(i+1)*8-1:i*8]), .I1(A1[(i+1)*8-1:i*8]), .S(SEL[i]), .Z(X[(i+1)*8-1:i*8]) );
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
    
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_4 Root_CLKBUF (.Z(CLK_buf), .I(CLK));
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_4 Do_CLKBUF [BYTE_CNT-1:0] (.Z(CLKBUF), .I(CLK_buf) );
    
    generate
        genvar i;
        for(i=0; i<BYTE_CNT; i=i+1) begin : OUTREG_BYTE
            `ifndef NO_DIODES    
                (* keep = "true" *)
                gf180mcu_fd_sc_mcu7t5v0__antenna DIODE [7:0] (.I(Di[(i+1)*8-1:i*8]));
            `endif
            gf180mcu_fd_sc_mcu7t5v0__dffq_1 Do_FF [7:0] ( .D(Di[(i+1)*8-1:i*8]), .Q(Do[(i+1)*8-1:i*8]), .CLK(CLKBUF[i]) );
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
    wire        SEL0_B_N;

    generate 
        genvar i;
`ifndef NO_DIODES
        (* keep = "true" *)
        gf180mcu_fd_sc_mcu7t5v0__antenna DIODE_CLK (.I(CLK));
`endif

        if(USE_LATCH == 1) begin
            gf180mcu_fd_sc_mcu7t5v0__inv_2 CLKINV(.ZN(CLK_B), .I(CLK));
            gf180mcu_fd_sc_mcu7t5v0__icgtp_1  CG ( .TE(WE0_WIRE), .E(WE0_WIRE), .CLK(CLK_B), .Q(GCLK) );
        end else begin
            gf180mcu_fd_sc_mcu7t5v0__icgtp_1  CG ( .TE(WE0_WIRE), .E(WE0_WIRE), .CLK(CLK), .Q(GCLK) );
            
        end
    
        gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL0INV(.ZN(SEL0_B), .I(SEL0));
        gf180mcu_fd_sc_mcu7t5v0__and2_1 CGAND( .A1(SEL0), .A2(WE0), .Z(WE0_WIRE) );
    
        for(i=0; i<8; i=i+1) begin : BIT
            if(USE_LATCH == 0)
                gf180mcu_fd_sc_mcu7t5v0__dffq_1 STORAGE ( .D(Di0[i]), .Q(Q_WIRE[i]), .CLK(GCLK) );
            else 
                gf180mcu_fd_sc_mcu7t5v0__latq_1 STORAGE (.Q(Q_WIRE[i]), .D(Di0[i]), .E(GCLK) );
            
            gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL0_BINV (.ZN(SEL0_B_N), .I(SEL0_B));
            gf180mcu_fd_sc_mcu7t5v0__bufz_1 OBUF0 ( .I(Q_WIRE[i]), .Z(Do0[i]), .EN(SEL0_B_N) );
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
    wire        SEL0_B_N, SEL1_B_N;
    wire        GCLK;
    wire        CLK_B;
    

    generate 
        genvar i;
`ifndef NO_DIODES
        (* keep = "true" *)
        gf180mcu_fd_sc_mcu7t5v0__antenna DIODE_CLK (.I(CLK));
`endif

        if(USE_LATCH == 1) begin
            gf180mcu_fd_sc_mcu7t5v0__inv_2 CLKINV(.ZN(CLK_B), .I(CLK));
            gf180mcu_fd_sc_mcu7t5v0__icgtp_1  CG ( .TE(WE0_WIRE), .E(WE0_WIRE), .CLK(CLK_B), .Q(GCLK) );
        end else
            gf180mcu_fd_sc_mcu7t5v0__icgtp_1  CG ( .TE(WE0_WIRE), .E(WE0_WIRE), .CLK(CLK), .Q(GCLK) );
    
        gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL0INV (.ZN(SEL0_B), .I(SEL0));
        gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL1INV (.ZN(SEL1_B), .I(SEL1));
        gf180mcu_fd_sc_mcu7t5v0__and2_1 CGAND( .A1(SEL0), .A2(WE0), .Z(WE0_WIRE) );
    
        for(i=0; i<8; i=i+1) begin : BIT
            if(USE_LATCH == 0)
                gf180mcu_fd_sc_mcu7t5v0__dffq_1 STORAGE ( .D(Di0[i]), .Q(Q_WIRE[i]), .CLK(GCLK) );
            else 
                gf180mcu_fd_sc_mcu7t5v0__latq_1 STORAGE (.Q(Q_WIRE[i]), .D(Di0[i]), .E(GCLK) );

            gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL0_BINV (.ZN(SEL0_B_N), .I(SEL0_B));
            gf180mcu_fd_sc_mcu7t5v0__bufz_1 OBUF0 ( .I(Q_WIRE[i]), .Z(Do0[i]), .EN(SEL0_B) );

            gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL1_BINV (.ZN(SEL1_B_N), .I(SEL1_B));
            gf180mcu_fd_sc_mcu7t5v0__bufz_1 OBUF1 ( .I(Q_WIRE[i]), .Z(Do1[i]), .EN(SEL1_B) );
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

    gf180mcu_fd_sc_mcu7t5v0__clkbuf_4 CLKBUF (.Z(CLK_buf), .I(CLK));
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_2 SEL0BUF (.Z(SEL0_buf), .I(SEL0));
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
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_2 SEL0BUF (.Z(SEL0_buf), .I(SEL0));
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_2 SEL1BUF (.Z(SEL1_buf), .I(SEL1));
    gf180mcu_fd_sc_mcu7t5v0__clkbuf_4 CLKBUF (.Z(CLK_buf), .I(CLK));
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

gf180mcu_fd_sc_mcu7t5v0__clkbuf_2  __cell__ (.Z(X), .I(A)); 

endmodule


module CLKBUF_16 (input A, output X); 

gf180mcu_fd_sc_mcu7t5v0__clkbuf_16 __cell__ (.Z(X), .I(A));

endmodule

module DIODE (input DIODE);

gf180mcu_fd_sc_mcu7t5v0__antenna __cell__ (.I(DIODE));

endmodule

module CLKBUF_4 (input A, output X); 

gf180mcu_fd_sc_mcu7t5v0__clkbuf_4 __cell__ (.Z(X), .I(A));

endmodule

module CONB (output HI, output LO); 

gf180mcu_fd_sc_mcu7t5v0__tiel __cell__ (.ZN(LO)); 

endmodule

module EBUFN_2 (input A, input TE_B, output Z); 

// tristate buffer
wire TE_BN; 

gf180mcu_fd_sc_mcu7t5v0__inv_2 TE_BINV (.ZN(TE_BN), .I(TE_B));
gf180mcu_fd_sc_mcu7t5v0__bufz_1 __cell__ ( .I(A), .Z(Z), .EN(TE_BN) );

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
    wire [(WSIZE/8)-1:0]                  SEL1_B_N, SEL2_B_N;
    wire [(WSIZE/8)-1:0]          GCLK;

    gf180mcu_fd_sc_mcu7t5v0__inv_4 INV1[(WSIZE/8)-1:0] (.ZN(SEL1_B), .I(SEL1));
	gf180mcu_fd_sc_mcu7t5v0__inv_4 INV2[(WSIZE/8)-1:0] (.ZN(SEL2_B), .I(SEL2));

    gf180mcu_fd_sc_mcu7t5v0__and2_1 CGAND ( .A1(SELW), .A2(WE), .Z(we_wire) );
    gf180mcu_fd_sc_mcu7t5v0__icgtp_1  CG ( .TE(we_wire), .E(we_wire), .CLK(CLK), .Q(GCLK) );

    generate 
        genvar i;
        for(i=0; i<WSIZE; i=i+1) begin : BIT
            gf180mcu_fd_sc_mcu7t5v0__dffq_1 FF ( .D(DW[i]), .Q(q_wire[i]), .CLK(GCLK[i/8]) );
            
            gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL1_BINV (.ZN(SEL1_B_N[i/8]), .I(SEL1_B[i/8]));
            gf180mcu_fd_sc_mcu7t5v0__bufz_1 OBUF1 ( .I(q_wire[i]), .Z(D1[i]), .EN(SEL1_B_N[i/8]));
            
            gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL2_BINV (.ZN(SEL2_B_N[i/8]), .I(SEL2_B[i/8]));
            gf180mcu_fd_sc_mcu7t5v0__bufz_1 OBUF2 ( .I(q_wire[i]), .Z(D2[i]), .EN(SEL2_B_N[i/8]) );
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
    wire [(WSIZE/8)-1:0]                  SEL1_B_N, SEL2_B_N;
    wire [(WSIZE/8)-1:0]                  GCLK;
	wire [7:0]	                lo;

    gf180mcu_fd_sc_mcu7t5v0__inv_4 INV1[(WSIZE/8)-1:0] (.ZN(SEL1_B), .I(SEL1));
	gf180mcu_fd_sc_mcu7t5v0__inv_4 INV2[(WSIZE/8)-1:0] (.ZN(SEL2_B), .I(SEL2));

	gf180mcu_fd_sc_mcu7t5v0__tiel TIE [7:0] ( .ZN(lo) );

    generate 
        genvar i;
        for(i=0; i<WSIZE; i=i+1) begin : BIT


            gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL1_BINV (.ZN(SEL1_B_N[i/8]), .I(SEL1_B[i/8]));
            gf180mcu_fd_sc_mcu7t5v0__bufz_1 OBUF1 ( .I(lo[i/8]), .Z(D1[i]), .EN(SEL1_B_N[i/8]));

            gf180mcu_fd_sc_mcu7t5v0__inv_2 SEL2_BINV (.ZN(SEL2_B_N[i/8]), .I(SEL2_B[i/8]));
            gf180mcu_fd_sc_mcu7t5v0__bufz_1 OBUF2 ( .I(lo[4+i/8]), .Z(D2[i]), .EN(SEL2_B_N[i/8]) );
        end
    endgenerate 
endmodule