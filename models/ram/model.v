/*
    Copyright ©2020-2022 The American University in Cairo

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


module RAM8 #( parameter    USE_LATCH=1,
                            WSIZE=1 ) (
    input   wire                CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,     // EN0: 1
    input   wire [2:0]           A0,      // A: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0
);

    wire    [7:0]         SEL0;
    wire    [WSIZE-1:0]   WE0_buf; 
    wire                  CLK_buf;

    DEC3x8 DEC0 (.EN(EN0), .A(A0), .SEL(SEL0));
    CLKBUF_2 WEBUF[WSIZE-1:0] (.X(WE0_buf), .A(WE0));
    CLKBUF_2 CLKBUF (.X(CLK_buf), .A(CLK));

    generate
        genvar i;
        for (i=0; i< 8; i=i+1) begin : WORD
            WORD #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) W ( .CLK(CLK_buf), .WE0(WE0_buf), .SEL0(SEL0[i]), .Di0(Di0), .Do0(Do0) );
        end
    endgenerate

endmodule

module RAM8_1RW1R #( parameter     USE_LATCH=1,
                                    WSIZE=1 ) (
    input   wire                 CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,     // EN0: 1
    input                        EN1,
    input   wire [2:0]           A0,     // A: 1
    input   wire [2:0]           A1,     // A: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0,
    output  wire [(WSIZE*8-1):0] Do1
);

    wire    [7:0]           SEL0, SEL1;
    wire    [WSIZE-1:0]     WE0_buf; 
    wire                    CLK_buf;

    DEC3x8 DEC0 (.EN(EN0), .A(A0), .SEL(SEL0));
    DEC3x8 DEC1 (.EN(EN1), .A(A1), .SEL(SEL1));
    
    CLKBUF_2 WEBUF[(WSIZE-1):0]   (.X(WE0_buf), .A(WE0));
    CLKBUF_2 CLKBUF (.X(CLK_buf), .A(CLK));

    generate
        genvar i;
        for (i=0; i< 8; i=i+1) begin : WORD
            WORD_1RW1R #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) W ( 
                .CLK(CLK_buf), 
                .WE0(WE0_buf), 
                .SEL0(SEL0[i]),
                .SEL1(SEL1[i]),
                .Di0(Di0), 
                .Do0(Do0),
                .Do1(Do1) 
            );
        end
    endgenerate

endmodule

// 2 x RAM8 slices (64 bytes) with registered outout 
module RAM16 #( parameter   USE_LATCH=1,
                            WSIZE=1 ) 
(
    input   wire                 CLK,    // FO: 2
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,     // FO: 1
    input   wire [3:0]           A0,      // FO: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0
    
);
    wire [1:0]           SEL0;
    wire [3:0]           A0_buf;
    wire                 CLK_buf;
    wire [WSIZE-1:0]     WE0_buf;
    wire                 EN0_buf;

    wire [(WSIZE*8-1):0] Do0_pre;
    //wire [(WSIZE*8-1):0] Di0_buf;

    // Buffers
    // Di Buffers
    // CLKBUF_16  DIBUF[(WSIZE*8-1):0] (.X(Di0_buf), .A(Di0));
    // Control signals buffers
 
`ifndef NO_DIODES   
    (* keep = "true" *)
    DIODE    DIODE_CLK         (.DIODE(CLK));
`endif
    
    CLKBUF_4   CLKBUF              (.X(CLK_buf), .A(CLK));
    
    CLKBUF_2   WEBUF[(WSIZE-1):0]  (.X(WE0_buf), .A(WE0));
 
`ifndef NO_DIODES   
    (* keep = "true" *)
    DIODE    DIODE_A0 [4:0]    (.DIODE(A0[4:0]));
`endif

    CLKBUF_2   A0BUF[3:0]           (.X(A0_buf),  .A(A0[3:0]));
    CLKBUF_2   EN0BUF               (.X(EN0_buf), .A(EN0));

    //DEC2x4 DEC0 (.EN(EN0_buf), .A(A0_buf[4:3]), .SEL(SEL0));
    DEC1x2 DEC0 (.EN(EN0_buf), .A(A0_buf[3:3]), .SEL(SEL0));
    
    generate
        genvar i;
        for (i=0; i< 2; i=i+1) begin : SLICE
            RAM8 #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM8 (.CLK(CLK_buf), .WE0(WE0_buf),.EN0(SEL0[i]), .Di0(Di0), .Do0(Do0_pre), .A0(A0_buf[2:0]) ); 
        end
    endgenerate

    // Ensure that the Do0_pre lines are not floating when EN = 0
    wire [WSIZE-1:0] lo;
    wire [WSIZE-1:0] float_buf_en;
    CLKBUF_2   FBUFENBUF0[WSIZE-1:0] ( .X(float_buf_en), .A(EN0) );
    CONB     TIE0[WSIZE-1:0] (.LO(lo), .HI());

    // Following split by group because each is done by one TIE CELL and ONE CLKINV_4
    // Provides default values for floating lines (lo)
    generate
        for (i=0; i< WSIZE; i=i+1) begin : BYTE
            EBUFN_2 FLOATBUF0[(8*(i+1))-1:8*i] ( .A( lo[i] ), .Z(Do0_pre[(8*(i+1))-1:8*i]), .TE_B(float_buf_en[i]) );        
        end
    endgenerate

    OUTREG #(.WIDTH(WSIZE*8)) Do0_REG ( .CLK(CLK_buf), .Di(Do0_pre), .Do(Do0) );

endmodule

// 2 x RAM16 slices (128 bytes) with registered outout 
module RAM32 #( parameter    USE_LATCH=1,
                                WSIZE=4 ) 
(
    input   wire                 CLK,     // FO: 2
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,     // FO: 1
    input   wire [4:0]           A0,      // FO: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0
);

    wire                    EN0_buf;
    wire [1:0]              SEL0;
    wire [4:0]              A0_buf;
    wire [(WSIZE-1):0]      WE0_buf;
    wire [(WSIZE*8-1):0]    Do0_pre[1:0];
    wire [(WSIZE*8-1):0]    Di0_buf;

    CLKBUF_16  DIBUF[(WSIZE*8-1):0] (.X(Di0_buf), .A(Di0));
    
    
    CLKBUF_2   WEBUF[(WSIZE-1):0]   (.X(WE0_buf), .A(WE0));
    CLKBUF_2   A0BUF[4:0]           (.X(A0_buf),  .A(A0[4:0]));
    CLKBUF_2   EN0BUF               (.X(EN0_buf), .A(EN0));

    //DEC2x4 DEC0 (.EN(EN0_buf), .A(A0_buf[6:5]), .SEL(SEL0));

    DEC1x2 DEC0 (.EN(EN0_buf), .A(A0_buf[4]), .SEL(SEL0));
     generate
        genvar i;
        for (i=0; i< 2; i=i+1) begin : SLICE_16
            RAM16 #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM16 (.CLK(CLK), .EN0(SEL0[i]), .WE0(WE0_buf), .Di0(Di0_buf), .Do0(Do0_pre[i]), .A0(A0_buf[3:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX2x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .S(A0_buf[4]), .X(Do0) );
endmodule 



module RAM32_1RW1R #( parameter     USE_LATCH=1,
                                    WSIZE=1 ) 
(
    input   wire                 CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,    // FO: 1
    input                        EN1,
    input   wire [4:0]           A0,     // FO: 1
    input   wire [4:0]           A1,
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0,
    output  wire [(WSIZE*8-1):0] Do1
    
);
    wire [3:0]           SEL0, SEL1;
    wire [4:0]           A0_buf, A1_buf;
    wire                 CLK_buf;
    wire [WSIZE-1:0]     WE0_buf;
    wire                 EN0_buf, EN1_buf;

    wire [(WSIZE*8-1):0] Do0_pre, Do1_pre;
    wire [(WSIZE*8-1):0] Di0_buf;

    // Buffers
    // Di Buffers
    CLKBUF_16  DIBUF[(WSIZE*8-1):0] (.X(Di0_buf), .A(Di0));
    // Control signals buffers
    (* keep = "true" *)

`ifndef NO_DIODES
    DIODE    DIODE_CLK         (.DIODE(CLK));
`endif
    CLKBUF_4   CLKBUF               (.X(CLK_buf),  .A(CLK));


    CLKBUF_2   WEBUF[(WSIZE-1):0]   (.X(WE0_buf), .A(WE0));


`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_A0 [4:0]    (.DIODE(A0[4:0]));
`endif
    CLKBUF_2   A0BUF[4:0]           (.X(A0_buf),  .A(A0));
    CLKBUF_2   EN0BUF               (.X(EN0_buf), .A(EN0));

`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_A1 [4:0]    (.DIODE(A0[4:0]));
`endif
    CLKBUF_2   A1BUF[4:0]           (.X(A1_buf),  .A(A1));
    CLKBUF_2   EN1BUF               (.X(EN1_buf), .A(EN1));

    DEC2x4 DEC0 (.EN(EN0_buf), .A(A0_buf[4:3]), .SEL(SEL0));
    DEC2x4 DEC1 (.EN(EN1_buf), .A(A1_buf[4:3]), .SEL(SEL1));


    generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : SLICE
            RAM8_1RW1R #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM8 (
                .CLK(CLK_buf), 
                .WE0(WE0_buf),
                .EN0(SEL0[i]), 
                .EN1(SEL1[i]), 
                .Di0(Di0_buf), 
                .Do0(Do0_pre), 
                .Do1(Do1_pre), 
                .A0(A0_buf[2:0]),
                .A1(A1_buf[2:0])  
            ); 
        end
    endgenerate

    // Ensure that the Do0_pre lines are not floating when EN = 0
    wire [WSIZE-1:0] lo0, lo1;
    wire [WSIZE-1:0] float_buf_en0, float_buf_en1;
    CLKBUF_2   FBUFENBUF0[WSIZE-1:0] ( .X(float_buf_en0), .A(EN0) );
    CLKBUF_2   FBUFENBUF1[WSIZE-1:0] ( .X(float_buf_en1), .A(EN1) );
    CONB     TIE0[WSIZE-1:0] (.LO(lo0), .HI());
    CONB     TIE1[WSIZE-1:0] (.LO(lo1), .HI());
    

    // Following split by group because each is done by one TIE CELL and ONE CLKINV_4
    // Provides default values for floating lines (lo)
    generate
        for (i=0; i< WSIZE; i=i+1) begin : BYTE
            EBUFN_2 FLOATBUF0[(8*(i+1))-1:8*i] ( .A( lo0[i] ), .Z(Do0_pre[(8*(i+1))-1:8*i]), .TE_B(float_buf_en0[i]) );
            EBUFN_2 FLOATBUF1[(8*(i+1))-1:8*i] ( .A( lo1[i] ), .Z(Do1_pre[(8*(i+1))-1:8*i]), .TE_B(float_buf_en1[i]) );
        end
    endgenerate

    OUTREG #(.WIDTH(WSIZE*8)) Do0_REG ( .CLK(CLK_buf), .Di(Do0_pre), .Do(Do0) );
    OUTREG #(.WIDTH(WSIZE*8)) Do1_REG ( .CLK(CLK_buf), .Di(Do1_pre), .Do(Do1) );
    
endmodule

/*
    4 x RAM32 Blocks
*/

module RAM128 #(parameter   USE_LATCH=1,
                            WSIZE=1 ) 
(
    input   wire                 CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,     // FO: 1
    input   wire [6:0]           A0,      // FO: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0
    
);

    wire                     CLK_buf;
    wire [WSIZE-1:0]         WE0_buf;
    wire                     EN0_buf;
    wire [6:0]               A0_buf;
    wire [(WSIZE*8-1):0]     Di0_buf;

    wire [3:0]               SEL0;
    wire [(WSIZE*8-1):0]     Do0_pre[3:0]; 
                            
    // Buffers
`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_DI [WSIZE*8-1:0]  (.DIODE(Di0));
`endif
    CLKBUF_16  DIBUF[(WSIZE*8-1):0]    (.X(Di0_buf),  .A(Di0));

`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_CLK            (.DIODE(CLK));
`endif
    CLKBUF_4   CLKBUF          (.X(CLK_buf), .A(CLK));

    CLKBUF_2   WEBUF[WSIZE-1:0]     (.X(WE0_buf),  .A(WE0));
    CLKBUF_2   EN0BUF                (.X(EN0_buf),  .A(EN0));

`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_A0 [6:0]    (.DIODE(A0[6:0]));
`endif
    CLKBUF_2   A0BUF[6:0]        (.X(A0_buf),   .A(A0));


    DEC2x4 DEC0 (.EN(EN0_buf), .A(A0_buf[6:5]), .SEL(SEL0));

     generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : BLOCK
            RAM32 #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM32 (.CLK(CLK_buf), .EN0(SEL0[i]), .WE0(WE0_buf), .Di0(Di0_buf), .Do0(Do0_pre[i]), .A0(A0_buf[4:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX4x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .A2(Do0_pre[2]), .A3(Do0_pre[3]), .S(A0_buf[6:5]), .X(Do0) );

endmodule

module RAM128_1RW1R #( parameter    USE_LATCH=1,
                                    WSIZE=1 ) 
(
    input   wire                 CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,    // FO: 1
    input                        EN1,
    input   wire [6:0]           A0,     // FO: 1
    input   wire [6:0]           A1,
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0,
    output  wire [(WSIZE*8-1):0] Do1
    
);

    wire                     CLK_buf;
    wire [WSIZE-1:0]         WE0_buf;
    wire                     EN0_buf;
    wire                     EN1_buf;
    wire [6:0]               A0_buf;
    wire [6:0]               A1_buf;
    wire [(WSIZE*8-1):0]     Di0_buf;
    wire [3:0]               SEL0;
    wire [3:0]               SEL1;

    wire [(WSIZE*8-1):0]    Do0_pre[3:0]; 
    wire [(WSIZE*8-1):0]    Do1_pre[3:0]; 
                            
    // Buffers
`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_DI [WSIZE*8-1:0]  (.DIODE(Di0));
`endif
    CLKBUF_16  DIBUF[(WSIZE*8-1):0] (.X(Di0_buf),  .A(Di0));

`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_CLK            (.DIODE(CLK));
`endif
    CLKBUF_4   CLKBUF         (.X(CLK_buf), .A(CLK));

    CLKBUF_2   WEBUF[WSIZE-1:0]     (.X(WE0_buf),  .A(WE0));
    
`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_A0 [6:0]    (.DIODE(A0[6:0]));
`endif
    CLKBUF_2   A0BUF[6:0]           (.X(A0_buf),   .A(A0));
    CLKBUF_2   EN0BUF               (.X(EN0_buf),  .A(EN0));
    
`ifndef NO_DIODES
    (* keep = "true" *)
    DIODE    DIODE_A1 [6:0]    (.DIODE(A0[6:0]));
`endif
    CLKBUF_2   A1BUF[6:0]           (.X(A1_buf),   .A(A1));
    CLKBUF_2   EN1BUF               (.X(EN1_buf),  .A(EN1));

    DEC2x4 DEC0 (.EN(EN0_buf), .A(A0_buf[6:5]), .SEL(SEL0));
    DEC2x4 DEC1 (.EN(EN1_buf), .A(A1_buf[6:5]), .SEL(SEL1));

     generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : BLOCK
            RAM32_1RW1R #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM32 (.CLK(CLK_buf), .EN0(SEL0[i]), .EN1(SEL1[i]), .WE0(WE0_buf), .Di0(Di0_buf), .Do0(Do0_pre[i]), .Do1(Do1_pre[i]), .A0(A0_buf[4:0]), .A1(A1_buf[4:0]) );        
        end
     endgenerate

    // Output MUXs
    MUX4x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .A2(Do0_pre[2]), .A3(Do0_pre[3]), .S(A0_buf[6:5]), .X(Do0) );
    MUX4x1 #(.WIDTH(WSIZE*8)) Do1MUX ( .A0(Do1_pre[0]), .A1(Do1_pre[1]), .A2(Do1_pre[2]), .A3(Do1_pre[3]), .S(A1_buf[6:5]), .X(Do1) );
    

endmodule

module RAM256 #(parameter   USE_LATCH=1,
                            WSIZE=1 ) 
(
    input   wire                CLK,    // FO: 2
    input   wire [WSIZE-1:0]     WE0,     // FO: 2
    input                        EN0,     // FO: 2
    input   wire [7:0]           A0,      // FO: 5
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 2
    output  wire [(WSIZE*8-1):0] Do0

);

    wire [1:0]             SEL0;
    wire [(WSIZE*8-1):0]    Do0_pre[1:0]; 

    // 1x2 DEC
    DEC1x2 DEC0 (.EN(EN0), .A(A0[7]), .SEL(SEL0));

    generate
        genvar i;
        for (i=0; i< 2; i=i+1) begin : BANK128
            RAM128 #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM128 (.CLK(CLK), .EN0(SEL0[i]), .WE0(WE0), .Di0(Di0), .Do0(Do0_pre[i]), .A0(A0[6:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX2x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .S(A0[7]), .X(Do0) );

endmodule

module RAM256_1RW1R #(parameter USE_LATCH=1,
                                WSIZE=1 ) 
(
    input   wire                 CLK,    // FO: 2
    input   wire [WSIZE-1:0]     WE0,     // FO: 2
    input                        EN0,    // FO: 2
    input                        EN1,
    input   wire [7:0]           A0,     // FO: 5
    input   wire [7:0]           A1,
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 2
    output  wire [(WSIZE*8-1):0] Do0,
    output  wire [(WSIZE*8-1):0] Do1
    
);

    wire [1:0]               SEL0, SEL1;
    wire [(WSIZE*8-1):0]     Do0_pre[1:0],
                             Do1_pre[1:0]; 
    // 1x2 DEC
    DEC1x2 DEC0 (.EN(EN0), .A(A0[7]), .SEL(SEL0));
    DEC1x2 DEC1 (.EN(EN1), .A(A1[7]), .SEL(SEL1));

    generate
        genvar i;
        for (i=0; i< 2; i=i+1) begin : BANK128
            RAM128_1RW1R #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM128 (.CLK(CLK), .EN0(SEL0[i]), .EN1(SEL1[i]), .WE0(WE0), .Di0(Di0), .Do0(Do0_pre[i]), .Do1(Do1_pre[i]), .A0(A0[6:0]), .A1(A1[6:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX2x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .S(A0[7]), .X(Do0) );
    MUX2x1 #(.WIDTH(WSIZE*8)) Do1MUX ( .A0(Do1_pre[0]), .A1(Do1_pre[1]), .S(A1[7]), .X(Do1) );

endmodule


module RAM512 #(parameter   USE_LATCH=1,
                            WSIZE=1 ) 
(
    input   wire                 CLK,    // FO: 4
    input   wire [WSIZE-1:0]     WE0,     // FO: 4
    input                        EN0,     // FO: 4
    input   wire [8:0]           A0,      // FO: 5
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 4
    output  wire [(WSIZE*8-1):0] Do0
    
);

    wire [3:0]              SEL0;
    wire [(WSIZE*8-1):0]    Do0_pre[3:0]; 

    DEC2x4 DEC0 (.EN(EN0), .A(A0[8:7]), .SEL(SEL0));

    generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : BANK128
            RAM128 #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM128 (.CLK(CLK), 
                .EN0(SEL0[i]), 
                .WE0(WE0), 
                .Di0(Di0), 
                .Do0(Do0_pre[i]), 
                .A0(A0[6:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX4x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), 
        .A1(Do0_pre[1]), 
        .A2(Do0_pre[2]), 
        .A3(Do0_pre[3]), 
        .S(A0[8:7]), 
        .X(Do0) );

endmodule



module RAM512_1RW1R  #(parameter    USE_LATCH=1,
                                    WSIZE=1 ) 
(
    input   wire                    CLK,    // FO: 4
    input   wire [WSIZE-1:0]        WE0,     // FO: 4
    input                           EN0,     // FO: 4
    input                           EN1,     // FO: 4
    input   wire [8:0]              A0,      // FO: 5
    input   wire [8:0]              A1,      // FO: 5
    input   wire [(WSIZE*8-1):0]    Di0,     // FO: 4
    output  wire [(WSIZE*8-1):0]    Do0,
    output  wire [(WSIZE*8-1):0]    Do1  
);

    wire [3:0]              SEL0, SEL1;
    wire [(WSIZE*8-1):0]    Do0_pre[3:0],
                            Do1_pre[3:0]; 

    DEC2x4 DEC0 (.EN(EN0), .A(A0[8:7]), .SEL(SEL0));
    DEC2x4 DEC1 (.EN(EN1), .A(A1[8:7]), .SEL(SEL1));

    generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : BANK128
            RAM128_1RW1R #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM128 (.CLK(CLK), .EN0(SEL0[i]), .EN1(SEL1[i]), .WE0(WE0), .Di0(Di0), .Do0(Do0_pre[i]), .Do1(Do1_pre[i]), .A0(A0[6:0]), .A1(A1[6:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX4x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .A2(Do0_pre[2]), .A3(Do0_pre[3]), .S(A0[8:7]), .X(Do0) );
    MUX4x1 #(.WIDTH(WSIZE*8)) Do1MUX ( .A0(Do1_pre[0]), .A1(Do1_pre[1]), .A2(Do1_pre[2]), .A3(Do1_pre[3]), .S(A1[8:7]), .X(Do1) );

endmodule

module RAM1024 #(parameter  USE_LATCH=1,
                            WSIZE=1 ) 
(
    input   wire                 CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,     // FO: 1
    input   wire [9:0]           A0,      // FO: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0
    
);

    wire                     CLK_buf;
    wire [WSIZE-1:0]         WE0_buf;
    wire                     EN0_buf;
    wire [9:0]               A0_buf;
    wire [(WSIZE*8-1):0]     Di0_buf;
    wire [1:0]               SEL0;

    wire [(WSIZE*8-1):0]     Do0_pre[1:0]; 
                            
    // Buffers
    CLKBUF_16  DIBUF[(WSIZE*8-1):0] (.X(Di0_buf),  .A(Di0));
    CLKBUF_4   CLKBUF               (.X(CLK_buf),  .A(CLK));
    CLKBUF_2   WEBUF[WSIZE-1:0]     (.X(WE0_buf),  .A(WE0));
    CLKBUF_2   EN0BUF                (.X(EN0_buf),  .A(EN0));
    CLKBUF_2   A0BUF[9:0]            (.X(A0_buf),   .A(A0));

    // 1x2 DEC
    DEC1x2 DEC0 (.EN(EN0_buf), .A(A0[9]), .SEL(SEL0));

     generate
        genvar i;
        for (i=0; i< 2; i=i+1) begin : BANK512
            RAM512 #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM512 (.CLK(CLK_buf), .EN0(SEL0[i]), .WE0(WE0_buf), .Di0(Di0_buf), .Do0(Do0_pre[i]), .A0(A0_buf[8:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX2x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .S(A0_buf[9]), .X(Do0) );

endmodule

module RAM1024_1RW1R #(parameter  USE_LATCH=1,
                            WSIZE=1 ) 
(
    input   wire                    CLK,    // FO: 1
    input   wire [WSIZE-1:0]        WE0,    // FO: 1
    input                           EN0,    // FO: 1
    input                           EN1,    // FO: 1
    input   wire [9:0]              A0,     // FO: 1
    input   wire [9:0]              A1,     // FO: 1
    input   wire [(WSIZE*8-1):0]    Di0,    // FO: 1
    output  wire [(WSIZE*8-1):0]    Do0,
    output  wire [(WSIZE*8-1):0]    Do1  
);

    wire                    CLK_buf;
    wire [WSIZE-1:0]        WE0_buf;
    wire                    EN0_buf;
    wire                    EN1_buf;
    wire [9:0]              A0_buf;
    wire [9:0]              A1_buf;
    wire [(WSIZE*8-1):0]    Di0_buf;
    wire [1:0]              SEL0;
    wire [1:0]              SEL1;
    wire [(WSIZE*8-1):0]    Do0_pre[1:0]; 
    wire [(WSIZE*8-1):0]    Do1_pre[1:0]; 
                            
    // Buffers
    CLKBUF_16  DIBUF[(WSIZE*8-1):0] (.X(Di0_buf),  .A(Di0));
    CLKBUF_4   CLKBUF               (.X(CLK_buf),  .A(CLK));
    CLKBUF_2   WEBUF[WSIZE-1:0]     (.X(WE0_buf),  .A(WE0));
    CLKBUF_2   EN0BUF               (.X(EN0_buf),  .A(EN0));
    CLKBUF_2   A0BUF[9:0]           (.X(A0_buf),   .A(A0));
    CLKBUF_2   EN1BUF               (.X(EN1_buf),  .A(EN1));
    CLKBUF_2   A1BUF[9:0]           (.X(A1_buf),   .A(A1));

    // 1x2 DEC
    DEC1x2 DEC0 (.EN(EN0_buf), .A(A0[9]), .SEL(SEL0));
    DEC1x2 DEC1 (.EN(EN1_buf), .A(A1[9]), .SEL(SEL1));

     generate
        genvar i;
        for (i=0; i< 2; i=i+1) begin : BANK512
            RAM512_1RW1R #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM512 (.CLK(CLK_buf), .EN0(SEL0[i]), .EN1(SEL1[i]), .WE0(WE0_buf), .Di0(Di0_buf), .Do0(Do0_pre[i]), .Do1(Do1_pre[i]), .A0(A0_buf[8:0]), .A1(A1_buf[8:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX2x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .S(A0_buf[9]), .X(Do0) );
    MUX2x1 #(.WIDTH(WSIZE*8)) Do1MUX ( .A0(Do1_pre[0]), .A1(Do1_pre[1]), .S(A1_buf[9]), .X(Do1) );

endmodule

module RAM2048 #(parameter  USE_LATCH=1,
                            WSIZE=1 ) 
(
    input   wire                 CLK,    // FO: 1
    input   wire [WSIZE-1:0]     WE0,     // FO: 1
    input                        EN0,     // FO: 1
    input   wire [10:0]          A0,      // FO: 1
    input   wire [(WSIZE*8-1):0] Di0,     // FO: 1
    output  wire [(WSIZE*8-1):0] Do0
    
);

    wire                     CLK_buf;
    wire [WSIZE-1:0]         WE0_buf;
    wire                     EN0_buf;
    wire [10:0]              A0_buf;
    wire [(WSIZE*8-1):0]     Di0_buf;
    wire [3:0]               SEL0;

    wire [(WSIZE*8-1):0]     Do0_pre[3:0]; 
                            
    // Buffers
    CLKBUF_16  DIBUF[(WSIZE*8-1):0] (.X(Di0_buf),  .A(Di0));
    CLKBUF_4   CLKBUF               (.X(CLK_buf), .A(CLK));
    CLKBUF_2   WEBUF[WSIZE-1:0]     (.X(WE0_buf),  .A(WE0));
    CLKBUF_2   EN0BUF                (.X(EN0_buf),  .A(EN0));
    CLKBUF_2   A0BUF[10:0]           (.X(A0_buf),   .A(A0));

    DEC2x4 DEC0 (.EN(EN0_buf), .A(A0_buf[10:9]), .SEL(SEL0));

     generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : BANK512
            RAM512 #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM512 (.CLK(CLK_buf), .EN0(SEL0[i]), .WE0(WE0_buf), .Di0(Di0_buf), .Do0(Do0_pre[i]), .A0(A0_buf[8:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX4x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .A2(Do0_pre[2]), .A3(Do0_pre[3]), .S(A0_buf[10:9]), .X(Do0) );

endmodule


module RAM2048_1RW1R #(parameter    USE_LATCH=1,
                                    WSIZE=1 ) 
(
    input   wire                    CLK,    // FO: 1
    input   wire [WSIZE-1:0]        WE0,    // FO: 1
    input                           EN0,    // FO: 1
    input                           EN1,    // FO: 1
    input   wire [10:0]             A0,     // FO: 1
    input   wire [10:0]             A1,     // FO: 1
    input   wire [(WSIZE*8-1):0]    Di0,    // FO: 1
    output  wire [(WSIZE*8-1):0]    Do0,
    output  wire [(WSIZE*8-1):0]    Do1  
);
    wire                    CLK_buf;
    wire [WSIZE-1:0]        WE0_buf;
    wire                    EN0_buf;
    wire                    EN1_buf;
    wire [10:0]              A0_buf;
    wire [10:0]              A1_buf;
    wire [(WSIZE*8-1):0]    Di0_buf;
    wire [3:0]              SEL0;
    wire [3:0]              SEL1;
    wire [(WSIZE*8-1):0]    Do0_pre[3:0]; 
    wire [(WSIZE*8-1):0]    Do1_pre[3:0]; 
                            
    // Buffers
    CLKBUF_16  DIBUF[(WSIZE*8-1):0] (.X(Di0_buf),  .A(Di0));
    CLKBUF_4   CLKBUF               (.X(CLK_buf), .A(CLK));
    CLKBUF_2   WEBUF[WSIZE-1:0]     (.X(WE0_buf),  .A(WE0));
    CLKBUF_2   EN0BUF               (.X(EN0_buf),  .A(EN0));
    CLKBUF_2   A0BUF[10:0]          (.X(A0_buf),   .A(A0));
    CLKBUF_2   EN1BUF               (.X(EN1_buf),  .A(EN1));
    CLKBUF_2   A1BUF[10:0]          (.X(A1_buf),   .A(A1));

    DEC2x4 DEC0 (.EN(EN0_buf), .A(A0_buf[10:9]), .SEL(SEL0));
    DEC2x4 DEC1 (.EN(EN1_buf), .A(A1_buf[10:9]), .SEL(SEL1));

     generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : BANK512      
            RAM512_1RW1R #(.USE_LATCH(USE_LATCH), .WSIZE(WSIZE)) RAM512 (.CLK(CLK_buf), .EN0(SEL0[i]), .EN1(SEL1[i]), .WE0(WE0_buf), .Di0(Di0_buf), .Do0(Do0_pre[i]), .Do1(Do1_pre[i]), .A0(A0_buf[8:0]), .A1(A1_buf[8:0]) );        
        end
     endgenerate

    // Output MUX    
    MUX4x1 #(.WIDTH(WSIZE*8)) Do0MUX ( .A0(Do0_pre[0]), .A1(Do0_pre[1]), .A2(Do0_pre[2]), .A3(Do0_pre[3]), .S(A0_buf[10:9]), .X(Do0) );
    MUX4x1 #(.WIDTH(WSIZE*8)) Do1MUX ( .A0(Do1_pre[0]), .A1(Do1_pre[1]), .A2(Do1_pre[2]), .A3(Do1_pre[3]), .S(A1_buf[10:9]), .X(Do1) );

endmodule


