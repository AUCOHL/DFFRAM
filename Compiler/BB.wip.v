module BYTE #(  parameter   USE_LATCH=1)( 
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

    generate 
        genvar i;

        if(USE_LATCH == 1) begin
            sky130_fd_sc_hd__inv_1 CLKINV(.Y(CLK_B), .A(CLK));
            sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK_B), .GCLK(GCLK), .GATE(we_wire) );
        end else
            sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK), .GCLK(GCLK), .GATE(we_wire) );
    
        sky130_fd_sc_hd__inv_1 SELINV(.Y(SEL_B), .A(SEL));
        sky130_fd_sc_hd__and2_1 CGAND( .A(SEL), .B(WE), .X(we_wire) );
    
        for(i=0; i<8; i=i+1) begin : BIT
            if(USE_LATCH == 0)
                sky130_fd_sc_hd__dfxtp_1 FF ( .D(Di[i]), .Q(q_wire[i]), .CLK(GCLK) );
            else 
                sky130_fd_sc_hd__dlxtp_1 LATCH (.Q(q_wire[i]), .D(Di[i]), .GATE(GCLK) );
            sky130_fd_sc_hd__ebufn_2 OBUF ( .A(q_wire[i]), .Z(Do[i]), .TE_B(SEL_B) );
        end
    endgenerate 
  
endmodule

module BYTE_1RW1R #(  parameter   USE_LATCH=1)( 
    input   wire        CLK,    // FO: 1
    input   wire        WE,     // FO: 1
    input   wire        SEL0,   // FO: 2
    input   wire        SEL1,   // FO: 2
    input   wire [7:0]  Di,     // FO: 1
    output  wire [7:0]  Do0,
    output  wire [7:0]  Do1
);

    wire [7:0]  q_wire;
    wire        we_wire;
    wire        SEL0_B, SEL1_B;
    wire        GCLK;
    wire        CLK_B;

    generate 
        genvar i;

        if(USE_LATCH == 1) begin
            sky130_fd_sc_hd__inv_1 CLKINV(.Y(CLK_B), .A(CLK));
            sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK_B), .GCLK(GCLK), .GATE(we_wire) );
        end else
            sky130_fd_sc_hd__dlclkp_1 CG( .CLK(CLK), .GCLK(GCLK), .GATE(we_wire) );
    
        sky130_fd_sc_hd__inv_1 SEL0_INV (.Y(SEL0_B), .A(SEL0));
        sky130_fd_sc_hd__inv_1 SEL1_INV (.Y(SEL1_B), .A(SEL1));
        sky130_fd_sc_hd__and2_1 CGAND( .A(SEL0), .B(WE), .X(we_wire) );
    
        for(i=0; i<8; i=i+1) begin : BIT
            if(USE_LATCH == 0)
                sky130_fd_sc_hd__dfxtp_1 FF ( .D(Di[i]), .Q(q_wire[i]), .CLK(GCLK) );
            else 
                sky130_fd_sc_hd__dlxtp_1 LATCH (.Q(q_wire[i]), .D(Di[i]), .GATE(GCLK) );

            sky130_fd_sc_hd__ebufn_2 OBUF0 ( .A(q_wire[i]), .Z(Do0[i]), .TE_B(SEL0_B) );
            sky130_fd_sc_hd__ebufn_2 OBUF1 ( .A(q_wire[i]), .Z(Do1[i]), .TE_B(SEL1_B) );
        end
    endgenerate 
  
endmodule

module WORD #( parameter    USE_LATCH=1,
                            SIZE=1 ) (
    input   wire                CLK,    // FO: 1
    input   wire [SIZE-1:0]     WE,     // FO: 1
    input   wire                SEL,    // FO: 1
    input   wire [(SIZE*8-1):0] Di,     // FO: 1
    output  wire [(SIZE*8-1):0] Do
);

    wire SEL_buf;
    wire CLK_buf;
    sky130_fd_sc_hd__clkbuf_2 SELBUF (.X(SEL_buf), .A(SEL));
    sky130_fd_sc_hd__clkbuf_1 CLKBUF (.X(CLK_buf), .A(CLK));
    generate
        genvar i;
            for(i=0; i<SIZE; i=i+1) 
                BYTE #(.USE_LATCH(USE_LATCH)) B ( .CLK(CLK_buf), .WE(WE[i]), .SEL(SEL_buf), .Di(Di[i*8-1:0]), .Do(Do[i*8-1:0]) );
    endgenerate
    
endmodule 

module WORD_1RW1R #( parameter  USE_LATCH=1,
                                SIZE=1 ) (
    input   wire                CLK,    // FO: 1
    input   wire [SIZE-1:0]     WE,     // FO: 1
    input   wire                SEL0,    // FO: 1
    input   wire                SEL1,    // FO: 1
    input   wire [(SIZE*8-1):0] Di,     // FO: 1
    output  wire [(SIZE*8-1):0] Do0,
    output  wire [(SIZE*8-1):0] Do1
);

    wire SEL0_buf, SEL1_buf;
    wire CLK_buf;
    sky130_fd_sc_hd__clkbuf_2 SEL0BUF (.X(SEL0_buf), .A(SEL0));
    sky130_fd_sc_hd__clkbuf_2 SEL1BUF (.X(SEL1_buf), .A(SEL1));
    sky130_fd_sc_hd__clkbuf_1 CLKBUF (.X(CLK_buf), .A(CLK));
    generate
        genvar i;
            for(i=0; i<SIZE; i=i+1) 
                BYTE_1RW1R #(.USE_LATCH(USE_LATCH)) B ( 
                    .CLK(CLK_buf), 
                    .WE(WE[i]), 
                    .SEL0(SEL0_buf), 
                    .SEL1(SEL1_buf), 
                    .Di(Di[i*8-1:0]), 
                    .Do0(Do0[i*8-1:0]),
                    .Do1(Do1[i*8-1:0])  
                );
    endgenerate
    
endmodule 

module SLICE #( parameter    USE_LATCH=1,
                            SIZE=1 ) (
    input   wire                CLK,    // FO: 1
    input   wire [SIZE-1:0]     WE,     // FO: 1
    input                       EN,     // EN: 1
    input   wire [2:0]          A,      // A: 1
    input   wire [(SIZE*8-1):0] Di,     // FO: 1
    output  wire [(SIZE*8-1):0] Do
);

    wire    [7:0]   SEL;
    wire            WE_buf; 
    wire            CLK_buf;

    DEC3x8 DEC (.EN(EN), .A(A), .SEL(SEL));
    sky130_fd_sc_hd__clkbuf_2 WEBUF (.X(WE_buf), .A(WE));
    sky130_fd_sc_hd__clkbuf_2 CLKBUF (.X(CLK_buf), .A(CLK));

    generate
        genvar i;
        for (i=0; i< 8; i=i+1) begin : WORD
            WORD #(.USE_LATCH(USE_LATCH), .SIZE(SIZE)) W ( .CLK(CLK_buf), .WE(WE_buf), .SEL(SEL[i]), .Di(Di), .Do(Do) );
        end
    endgenerate

endmodule

module SLICE_1RW1R #( parameter     USE_LATCH=1,
                                    SIZE=1 ) (
    input   wire                CLK,    // FO: 1
    input   wire [SIZE-1:0]     WE,     // FO: 1
    input                       EN0,     // EN: 1
    input                       EN1,
    input   wire [2:0]          A0,     // A: 1
    input   wire [2:0]          A1,     // A: 1
    input   wire [(SIZE*8-1):0] Di,     // FO: 1
    output  wire [(SIZE*8-1):0] Do0,
    output  wire [(SIZE*8-1):0] Do1
);

    wire    [7:0]   SEL0, SEL1;
    wire            WE_buf; 
    wire            CLK_buf;

    DEC3x8 DEC0 (.EN(EN0), .A(A0), .SEL(SEL0));
    DEC3x8 DEC1 (.EN(EN1), .A(A1), .SEL(SEL1));
    
    sky130_fd_sc_hd__clkbuf_2 WEBUF (.X(WE_buf), .A(WE));
    sky130_fd_sc_hd__clkbuf_2 CLKBUF (.X(CLK_buf), .A(CLK));

    generate
        genvar i;
        for (i=0; i< 8; i=i+1) begin : WORD
            WORD_1RW1R #(.USE_LATCH(USE_LATCH), .SIZE(SIZE)) W ( 
                .CLK(CLK_buf), 
                .WE(WE_buf), 
                .SEL0(SEL0[i]),
                .SEL1(SEL1[i]),
                .Di(Di), 
                .Do0(Do0),
                .Do1(Do1) 
            );
        end
    endgenerate

endmodule

// 8 Slices block (128 bytes) with registered outout 
module BLOCK #( parameter   USE_LATCH=1,
                            SIZE=1 ) (
    input   wire                CLK,    // FO: 1
    input   wire [SIZE-1:0]     WE,     // FO: 1
    input                       EN,     // FO: 1
    input   wire [4:0]          A,       // FO: 1
    input   wire [(SIZE*8-1):0] Di,     // FO: 1
    output  wire [(SIZE*8-1):0] Do
    
);
    wire [3:0]          SEL;
    wire [4:0]          A_buf;
    wire                CLK_buf;
    wire [SIZe-1:0]     WE_buf;
    wire                EN_buf;

    wire [(SIZE*8-1):0] Do_pre;
    wire [(SIZE*8-1):0] Di_buf;

    // Buffers
    // Di Buffers
    sky130_fd_sc_hd__clkbuf_16  DIBUF[(SIZE*8-1):0] (.X(Di_buf), .A(Di));
    // Control signals buffers
    sky130_fd_sc_hd__clkbuf_2   CLKBUF              (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_2   WEBUF[(SIZE-1):0]   (.X(WE_buf), .A(WE));
    sky130_fd_sc_hd__clkbuf_2   ABUF[4:0]           (.X(A_buf), .A(A[4:0]));
    sky130_fd_sc_hd__clkbuf_2   ENBUF               (.X(EN_buf), .A(EN));

    DEC2x4 DEC (.EN(EN_buf), .A(A_buf[4:3]), .SEL(SEL));

    generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : SLICE
            SLICE #(.USE_LATCH(USE_LATCH), .SIZE(SIZE)) RAM8 (.CLK(CLK_buf), .WE(WE_buf),.EN(SEL[i]), .Di(Di_buf), .Do(Do_pre), .A(A_buf[2:0]) ); 
        end
    endgenerate

    // Ensure that the Do_pre lines are not floating when EN = 0
    wire [SIZE-1:0] lo;
    wire [SIZE-1:0] float_buf_en;
    sky130_fd_sc_hd__clkbuf_2   FBUFENBUF[SIZE-1:0] ( .X(float_buf_en), .A(EN) );
    sky130_fd_sc_hd__conb_1     TIE[SIZ-1:0] (.LO(lo), .HI());

    // Following split by group because each is done by one TIE CELL and ONE CLKINV_4
    // Provides default values for floating lines (lo)
    generate
        for (i=0; i< SIZE; i=i+1) begin : BYTE
            sky130_fd_sc_hd__ebufn_2 FLOATBUF_B0[i*SIZE-1:0] ( .A( lo[i] ), .Z(Do_pre[i*SIZE-1:0]), .TE_B(float_buf_en[i]) );        
        end
    endgenerate
    
    sky130_fd_sc_hd__dfxtp_1 Do_FF[SIZE*9-1:0] ( .D(Do_pre), .Q(Do), .CLK(CLK) );

endmodule

module BLOCK_1RW1R #( parameter     USE_LATCH=1,
                                    SIZE=1 ) (
    input   wire                CLK,    // FO: 1
    input   wire [SIZE-1:0]     WE,     // FO: 1
    input                       EN0,     // FO: 1
    input                       EN1,
    input   wire [4:0]          A0,       // FO: 1
    input   wire [4:0]          A1,
    input   wire [(SIZE*8-1):0] Di,     // FO: 1
    output  wire [(SIZE*8-1):0] Do0,
    output  wire [(SIZE*8-1):0] Do1
    
);
    wire [3:0]          SEL0, SEL1;
    wire [4:0]          A0_buf, A1_buf;
    wire                CLK_buf;
    wire [SIZe-1:0]     WE_buf;
    wire                EN0_buf, EN1_buf;

    wire [(SIZE*8-1):0] Do0_pre, Do1_pre;
    wire [(SIZE*8-1):0] Di_buf;

    // Buffers
    // Di Buffers
    sky130_fd_sc_hd__clkbuf_16  DIBUF[(SIZE*8-1):0] (.X(Di_buf), .A(Di));
    // Control signals buffers
    sky130_fd_sc_hd__clkbuf_2   CLKBUF              (.X(CLK_buf), .A(CLK));
    sky130_fd_sc_hd__clkbuf_2   WEBUF[(SIZE-1):0]   (.X(WE_buf), .A(WE));
    sky130_fd_sc_hd__clkbuf_2   A0BUF[4:0]           (.X(A0_buf), .A(A0[4:0]));
    sky130_fd_sc_hd__clkbuf_2   A1BUF[4:0]           (.X(A1_buf), .A(A1[4:0]));
    sky130_fd_sc_hd__clkbuf_2   EN0BUF               (.X(EN0_buf), .A(EN0));
    sky130_fd_sc_hd__clkbuf_2   EN1BUF               (.X(EN1_buf), .A(EN1));

    DEC2x4 DEC0 (.EN(EN_buf), .A(A0_buf[4:3]), .SEL(SEL0));
    DEC2x4 DEC1 (.EN(EN_buf), .A(A1_buf[4:3]), .SEL(SEL1));


    generate
        genvar i;
        for (i=0; i< 4; i=i+1) begin : SLICE
            SLICE_1RW1R #(.USE_LATCH(USE_LATCH), .SIZE(SIZE)) RAM8 (
                .CLK(CLK_buf), 
                .WE(WE_buf),
                .EN0(SEL0[i]), 
                .EN1(SEL1[i]), 
                .Di(Di_buf), 
                .Do0(Do0_pre), 
                .Do1(Do1_pre), 
                .A0(A0_buf[2:0]),
                .A1(A1_buf[2:0])  
            ); 
        end
    endgenerate

    // Ensure that the Do_pre lines are not floating when EN = 0
    wire [SIZE-1:0] lo0, lo1;
    wire [SIZE-1:0] float_buf_en0, float_buf_en1;
    sky130_fd_sc_hd__clkbuf_2   FBUFENBUF0[SIZE-1:0] ( .X(float_buf_en0), .A(EN0) );
    sky130_fd_sc_hd__clkbuf_2   FBUFENBUF1[SIZE-1:0] ( .X(float_buf_en1), .A(EN1) );
    sky130_fd_sc_hd__conb_1     TIE0[SIZ-1:0] (.LO(lo0), .HI());
    sky130_fd_sc_hd__conb_1     TIE1[SIZ-1:0] (.LO(lo1), .HI());
    

    // Following split by group because each is done by one TIE CELL and ONE CLKINV_4
    // Provides default values for floating lines (lo)
    generate
        for (i=0; i< SIZE; i=i+1) begin : BYTE
            sky130_fd_sc_hd__ebufn_2 FLOATBUF0[i*SIZE-1:0] ( .A( lo0[i] ), .Z(Do0_pre[i*SIZE-1:0]), .TE_B(float_buf_en0[i]) );
            sky130_fd_sc_hd__ebufn_2 FLOATBUF1[i*SIZE-1:0] ( .A( lo1[i] ), .Z(Do1_pre[i*SIZE-1:0]), .TE_B(float_buf_en1[i]) );
        end
    endgenerate
    
    sky130_fd_sc_hd__dfxtp_1 Do0_FF[SIZE*9-1:0] ( .D(Do0_pre), .Q(Do0), .CLK(CLK) );
    sky130_fd_sc_hd__dfxtp_1 Do1_FF[SIZE*9-1:0] ( .D(Do1_pre), .Q(Do1), .CLK(CLK) );
    

endmodule
