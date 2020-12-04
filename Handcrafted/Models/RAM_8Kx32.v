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

    reg         _EN_ [7:0];
    wire [31:0] _Do_ [7:0];
    reg [31:0]  Do;

    DFFRAM #(.COLS(4)) RAM [7:0] (
        .CLK(CLK),
        .WE(WE),
        .EN(_EN_),
        .Di(Di),
        .Do(_Do_),
        .A(A[9:0])
    );

    integer i;
    
    always @* begin
        _EN_ = 8'd0;
        for(i=0; i<8; i=i+1)
            if(i==A[12:10]) _EN_[i]=1'b1;
    end

    always @* begin
        for(i=0; i<8; i=i+1)
            if(i==A[12:10]) Do=_Do_[i];
    end

        
endmodule
