//`define USE_DFFRAM_BEH
module RAM_5Kx32 (
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

    localparam BLOCKS=5;

    wire  [BLOCKS-1:0]       _EN_ ;
    wire [31:0] _Do_ [BLOCKS-1:0];

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
    
    // The block decoder
    assign _EN_[0] = A[12:10] == 3'd0;
    assign _EN_[1] = A[12:10] == 3'd1;
    assign _EN_[2] = A[12:10] == 3'd2;
    assign _EN_[3] = A[12:10] == 3'd3;
    assign _EN_[4] = A[12:10] == 3'd4;
    //assign _EN_[5] = A[12:10] == 3'd5;
    
    
    // Output Data multiplexor
    assign Do = (A[12:10] == 3'd0) ? _Do_[0] : 
                (A[12:10] == 3'd1) ? _Do_[1] : 
                (A[12:10] == 3'd2) ? _Do_[2] :
                (A[12:10] == 3'd3) ? _Do_[3] : 
                (A[12:10] == 3'd4) ? _Do_[4] : 
                //(A[12:10] == 3'd5) ? _Do_[5] : 
                32'd0;
    
endmodule