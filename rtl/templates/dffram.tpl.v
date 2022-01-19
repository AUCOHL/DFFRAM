<%
    import math
    
    words_num = size // 4
    addr_width = int(math.log2(words_num))
%>


 module DFFRAM_RTL_${size}
 (
     CLK,
     WE,
     EN,
     Di,
     Do,
     A
 );
    localparam A_WIDTH = ${addr_width};

    input   wire            CLK;
    input   wire    [3:0]   WE;
    input   wire            EN;
    input   wire    [31:0]  Di;
    output  reg     [31:0]  Do;
    input   wire    [(A_WIDTH - 1): 0]   A;
    reg [31:0] RAM[(${words_num})-1 : 0];

    always @(posedge CLK)
        if(EN) begin
            Do <= RAM[A];
            if(WE[0]) RAM[A][ 7: 0] <= Di[7:0];
            if(WE[1]) RAM[A][15:8] <= Di[15:8];
            if(WE[2]) RAM[A][23:16] <= Di[23:16];
            if(WE[3]) RAM[A][31:24] <= Di[31:24];
        end
        else
            Do <= 32'b0;
 endmodule