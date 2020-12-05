`timescale 1ns / 1ps
`default_nettype none

module RAM_8Kx32 (
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
    input   [12:0]   A;

    reg  [7:0]       _EN_ ;
    wire [31:0] _Do_ [7:0];
    reg [31:0]  Do;

    generate 
        genvar gi;
        for(gi=0; gi<8; gi=gi+1) 
            DFFRAM #(.COLS(4)) RAM (
                .CLK(CLK),
                .WE(WE),
                .EN(_EN_[gi]),
                .Di(Di),
                .Do(_Do_[gi]),
                .A(A[9:0])
            );
    endgenerate 
    integer i;

    always @* begin
        for(i=0; i<8; i=i+1)
            if(i==A[12:10]) _EN_[i]=1'b1;
            else _EN_[i] = 1'b0;
    end

    always @* begin
        Do = 32'h0;
        for(i=0; i<8; i=i+1)
            if(i==A[12:10]) Do=_Do_[i];
    end

        
endmodule
