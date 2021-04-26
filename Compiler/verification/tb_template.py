changeable_sub = """
/*
    An auto generated testbench to verify RAM{word_num}x{word_size}
    Author: Mohamed Shalan (mshalan@aucegypt.edu)
*/
`define     VERBOSE_1
`define     VERBOSE_2

`define     UNIT_DELAY  #1

`define     USE_LATCH   1

//`include "libs.ref/sky130_fd_sc_hd/verilog/primitives.v"
//`include "libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"

`include "hd_primitives.v"
`include "hd_functional.v"

`include "BB.v"

module tb_RAM{word_num}x{word_size};

    localparam A_W = {addr_width}+2;
    localparam M_SZ = 2**A_W;

    reg             CLK;
    reg  [3:0]      WE;
    reg             EN;
    reg  [31:0]     Di;
    wire [31:0]     Do;
    reg  [A_W-1:0]  A, ADDR;
    reg  [3:0]      HEX_DIG;
    reg  [7:0]      Phase;

    event           done;

    RAM{word_num}x{word_size} #(.USE_LATCH(`USE_LATCH)) SRAM (
        .CLK(CLK),
        .WE(WE),
        .EN(EN),
        .Di(Di),
        .Do(Do),
        .A(A[A_W-1:2])
    );

    initial begin
        $dumpfile("tb_RAM{word_num}x{word_size}.vcd");
        $dumpvars(0, tb_RAM{word_num}x{word_size});
        @(done) $finish;
    end

"""
constant_sub="""
    always #10 CLK = !CLK;

    integer i;

     /* Memory golden Model */
    reg [31:0]      RAM[(M_SZ)-1 : 0];
    reg [31:0]      RAM_DATA;

    always @(posedge CLK)
        if(EN) begin
            RAM_DATA <= RAM[A/4];
            if(WE[0]) RAM[A/4][ 7: 0] <= Di[7:0];
            if(WE[1]) RAM[A/4][15:8] <= Di[15:8];
            if(WE[2]) RAM[A/4][23:16] <= Di[23:16];
            if(WE[3]) RAM[A/4][31:24] <= Di[31:24];
        end

    initial begin
        CLK = 0;
        WE = 0;
        EN = 1;

        Phase = 0;
        // Perform a single word write then read
        mem_write_word(32'hA5337090, 4);
        mem_read_word(4);

        // Fill the memory with a known pattern
        for(i=0; i<M_SZ; i=i+4) begin
            HEX_DIG = $urandom%16;
            mem_write_word({8{HEX_DIG}},i);
            mem_read_word(i);
        end

        // Word Write then Read
        Phase = 1;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 0, starting Phase 1");
`endif
        for(i=0; i<M_SZ; i=i+4) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFC ;
            mem_write_word( $urandom, ADDR);
            mem_read_word( ADDR );
        end

        // HWord Write then Read
        Phase = 2;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 1, starting Phase 2");
`endif
        for(i=0; i<M_SZ; i=i+2) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFE;
            mem_write_hword($urandom&'hFFFF, ADDR );
            mem_read_word( ADDR & 'hFFFF_FFFC );
        end

        // Byte Write then Read
        Phase = 3;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 2, starting Phase 3");
`endif
        for(i=0; i<M_SZ; i=i+1) begin
            ADDR = (($urandom%M_SZ));
            mem_write_byte($urandom%255, ADDR);
            mem_read_word(ADDR & 'hFFFF_FFFC );
        end
        $display ("\\n>> Test Passed! <<\\n");
        -> done;
    end

    task mem_write_byte(input [7:0] byte, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A = addr;//[A_WIDTH:2];
        WE = (1 << addr[1:0]);
        Di = (byte << (addr[1:0] * 8));
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE BYTE: 0x%X to %0X(%0D) (0x%X, %B)", byte, addr, addr, Di, WE);
`endif
        WE = 4'b0;
    end
    endtask

    task mem_write_hword(input [15:0] hword, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A = addr;//[A_WIDTH:2];
        WE = {{2{addr[1]}},{2{~addr[1]}}};
        Di = (hword << (addr[1] * 16));
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE BYTE: 0x%X to %0X(%0D) (0x%X, %B)", hword, addr, addr, Di, WE);
`endif
        WE = 4'b0;
    end
    endtask

    task mem_write_word(input [31:0] word, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A = addr;
        WE = 4'b1111;
        Di = word;
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE BYTE: 0x%X to %0X(%0D) (0x%X, %B)", word, addr, addr, Di, WE);
`endif
        WE = 4'b0;
    end
    endtask

    task mem_read_word(input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A = addr;//[9:2];
        WE = 4'b0;
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORD: 0x%X from %0D", Do, addr);
`endif
        check();
    end
    endtask

    task check; begin
        if(RAM_DATA !== Do) begin
            $display("\\n>>Test Failed! <<\\t(Pahse: %0d, Iteration: %0d", Phase, i);
            $display("Address: 0x%X, READ: 0x%X - Should be: 0x%X", A, Do, RAM[A/4]);
            $fatal(1);
        end
    end
    endtask
endmodule
"""
