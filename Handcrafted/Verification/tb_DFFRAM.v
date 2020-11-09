/*
    Create an instance of OpenRAM memory model in addition to DFFRAM
    1) fill both memories with a word that matches the block (256bytes) number. 
       Addresses 0-252 get 0x11111111, 256-508 get 0x22222222, ....
    2) randomly write 32 half words (at random locations) to every 256 memory block (in both memories)
    3) randomly write 64 bytess (at random locations) to every 256 memory block (in both memories)
    4) Read both memories from start till the end and compare the contents
*/

module tb_DFFRAM;
    reg CLK;
    reg [3:0] WE;
    reg EN;
    reg [31:0] Di;
    wire [31:0] Do;
    reg [9:0] A;

    event   done;
    
    DFFRAM SRAM #(COLS=1)
    (
        .CLK(CLK),
        .WE(WE),
        .EN(EN),
        .Di(Di),
        .Do(Do),
        .A(A[9:2])
    );

    initial begin
        $dumpfile("tb_DFFRAM.vcd");
        $dumpvars;
        @(done) $finish;
    end

    always #10 CLK = !CLK;

    initial begin
        CLK = 0;
        WE = 0;
        EN = 1;
       
/*
mem_write_word(32'hAA000000,0);
mem_write_word(32'hAA000001,64);
mem_write_word(32'hAA000002,128);
mem_write_word(32'hAA000003,192);
mem_write_word(32'hAA000004,256);
mem_write_word(32'hAA000005,512);
mem_write_word(32'hAA000006,768);
mem_write_word(32'hAA000007,1020);

mem_read_word(0);
mem_read_word(64);
mem_read_word(128);
mem_read_word(192);
mem_read_word(256);
mem_read_word(512);
mem_read_word(768);
mem_read_word(1020);
*/
/*
mem_write_word(32'h88776655, 0);
mem_read_word(0);
mem_write_byte(8'hAB, 1);
mem_read_word(0);
mem_write_word(32'hEEEEEEEE, 4);
mem_write_hword(16'hABCD, 6);
mem_read_word(4);


mem_write_word(32'h88776655, 68);
mem_read_word(68);
mem_write_byte(8'hAB, 70);
mem_read_word(68);
mem_write_word(32'hEEEEEEEE, 72);
mem_write_hword(16'hABCD, 72);
mem_read_word(72);

mem_write_word(32'h88776655, 128);
mem_read_word(0);
mem_read_word(64);
mem_read_word(128);
*/
    -> done;
end

task mem_write_byte(input [7:0] byte, input [9:0] addr);
begin
    @(posedge CLK);
    A = addr[9:2];
    WE = (1 << addr[1:0]);
    Di = (byte << (addr[1:0] * 8));
    @(posedge CLK);
    $display("WRITE BYTE: 0x%X to %0D (0x%X, %B)", byte, addr, Di, WE);
end
endtask

task mem_write_hword(input [15:0] hword, input [9:0] addr);
begin
    @(posedge CLK);
    A = addr[9:2];
    WE = {{2{addr[1]}},{2{~addr[1]}}};
    Di = (hword << (addr[1] * 16));
    @(posedge CLK);
    $display("WRITE HWORD: 0x%X to %0D (0x%X, %B)", hword, addr, Di, WE);
end
endtask

task mem_write_word(input [31:0] word, input [9:0] addr);
begin
    @(posedge CLK);
    A = addr[9:2];
    WE = 4'b1111;
    Di = word; 
    @(posedge CLK);
    $display("WRITE WORD: 0x%X to %0D (0x%X, %B)", word, addr, Di, WE);
end
endtask

task mem_read_word(input [9:0] addr);
begin
    @(posedge CLK);
    A = addr[9:2];
    WE = 4'b0;
    @(posedge CLK);
    #5;
    $display("READ WORD: 0x%X from %0D", Do, addr);
end
endtask

endmodule