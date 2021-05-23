
/*
    An auto generated testbench to verify RAM32x32
    Authors:Mohamed Shalan (mshalan@aucegypt.edu)
            Ahmed Nofal (nofal.o.ahmed@gmail.com)
*/
`define     VERBOSE_1
`define     VERBOSE_2

`define     UNIT_DELAY  #1

`define     USE_LATCH   1

`define     SIZE        32/8
//`include "libs.ref/sky130_fd_sc_hd/verilog/primitives.v"
//`include "libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"

`include "hd_primitives.v"
`include "hd_functional.v"

`include "/home/nofal/Documents/auc_eda_group/DFFRAM_bak/Compiler/sky130A/BB/experimental/model.v"
// `include "BB.v"

module tb_RAM32x32_1RW1R;

    localparam SIZE = `SIZE;
    localparam A_W = 5+2;
    localparam M_SZ = 2**A_W;

    reg                   CLK;
    reg  [(SIZE-1):0]       WE;
    reg                  EN0;
    reg                  EN1;
    reg  [(SIZE*8-1):0]   Di;
    wire [(SIZE*8-1):0]   Do0;
    wire [(SIZE*8-1):0]   Do1;
    reg  [A_W-1:0]  A0, A1, ADDR;
    reg  [3:0]      HEX_DIG;
    reg  [7:0]      Phase;
    reg  [7:0]      RANDOM_BYTE;
    event           done;

    RAM32_1RW1R #(.USE_LATCH(`USE_LATCH), .WSIZE(`SIZE)) SRAM (
        .CLK(CLK),
        .WE(WE),
        .EN0(EN0),
        .EN1(EN1),
        .Di(Di),
        .Do0(Do0),
        .Do1(Do1),
        .A0(A0[A_W-1:2]),
        .A1(A1[A_W-1:2])
    );

    initial begin
        $dumpfile("tb_RAM32x32_1RW1R.vcd");
        $dumpvars(0, tb_RAM32x32_1RW1R);
        @(done) $finish;
    end


    always #10 CLK = !CLK;

    integer i;

     /* Memory golden Model */
    reg [(SIZE*8-1):0]      RAM[(M_SZ)-1 : 0];
    reg [(SIZE*8-1):0]      RAM_DATA0;
    reg [(SIZE*8-1):0]      RAM_DATA1;

    genvar c;
    generate
    for (c=0; c < SIZE; c = c+1) begin: mem_golden_model
        always @(posedge CLK) begin
            if(EN0) begin
                RAM_DATA0 <= RAM[A0/4];
                if(WE[c]) RAM[A0/4][8*(c+1)-1:8*c] <= Di[8*(c+1)-1:8*c];
            end
            if (EN1) begin
                RAM_DATA1 <= RAM[A1/4];
            end
        end
    end
    endgenerate

    initial begin
        CLK = 0;
        WE = 0;
        EN0 = 1;
        EN1 = 1;


        Phase = 0;
        // Perform a 2 word write then read 2 words
        mem_write_word({SIZE{8'h90}}, 4);
        mem_write_word({SIZE{8'h33}}, 8);
        mem_read_2words(4,8);

/***********************************************************

        Write and read from different ports

************************************************************/

        // Fill the memory with a known pattern
        for(i=0; i<M_SZ; i=i+4) begin
            HEX_DIG = $urandom%16;
            mem_write_word({8{HEX_DIG}},i);
            mem_read_word_1(i);
        end

        // Word Write then Read
        Phase = 1;
`ifdef  VERBOSE_1
        $display("\nFinished Phase 0, starting Phase 1");
`endif
        for(i=0; i<M_SZ; i=i+4) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFC ;
            RANDOM_BYTE = $urandom;
            mem_write_word( {SIZE{RANDOM_BYTE}}, ADDR);
            mem_read_word_1( ADDR );
        end

        // HWord Write then Read
        Phase = 2;
`ifdef  VERBOSE_1
        $display("\nFinished Phase 1, starting Phase 2");
`endif
        for(i=0; i<M_SZ; i=i+2) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFE;
            mem_write_hword($urandom&'hFFFF, ADDR );
            mem_read_word_1( ADDR & 'hFFFF_FFFC );
        end

        // Byte Write then Read
        Phase = 3;
`ifdef  VERBOSE_1
        $display("\nFinished Phase 2, starting Phase 3");
`endif
        for(i=0; i<M_SZ; i=i+1) begin
            ADDR = (($urandom%M_SZ));
            mem_write_byte($urandom%255, ADDR);
            mem_read_word_1(ADDR & 'hFFFF_FFFC );
        end

/***********************************************************

        Write and read from same port

************************************************************/
        Phase = 4;
`ifdef  VERBOSE_1
        $display("\nFinished Phase 3, starting Phase 4");
`endif
        for(i=0; i<M_SZ; i=i+4) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFC ;
            mem_write_word( $urandom, ADDR);
            mem_read_word_0( ADDR );
        end

        // HWord Write then Read
        Phase = 5;
`ifdef  VERBOSE_1
        $display("\nFinished Phase 4, starting Phase 5");
`endif
        for(i=0; i<M_SZ; i=i+2) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFE;
            mem_write_hword($urandom&'hFFFF, ADDR );
            mem_read_word_0( ADDR & 'hFFFF_FFFC );
        end

        // Byte Write then Read
        Phase = 6;
`ifdef  VERBOSE_1
        $display("\nFinished Phase 5, starting Phase 6");
`endif
        for(i=0; i<M_SZ; i=i+1) begin
            ADDR = (($urandom%M_SZ));
            mem_write_byte($urandom%255, ADDR);
            mem_read_word_0(ADDR & 'hFFFF_FFFC );
        end
        $display ("\n>> Test Passed! <<\n");
        -> done;
    end

    task mem_write_byte(input [7:0] byte, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A0 = addr;//[A_WIDTH:2];
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
        A0 = addr;//[A_WIDTH:2];
        WE = {{2{addr[1]}},{2{~addr[1]}}};
        Di = (hword << (addr[1] * 16));
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE HALFWORD: 0x%X to %0X(%0D) (0x%X, %B)", hword, addr, addr, Di, WE);
`endif
        WE = 4'b0;
    end
    endtask

    task mem_write_word(input [SIZE*8-1:0] word, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A0 = addr;
        WE = {SIZE{8'hFF}};
        Di = word;
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE WORD: 0x%X to %0X(%0D) (0x%X, %B)", word, addr, addr, Di, WE);
`endif
        WE = 4'b0;
    end
    endtask

    task mem_read_word_0(input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A0 = addr;//[9:2];
        WE = {SIZE{8'h00}};
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORD: 0x%X from %0D", Do0, addr);
`endif
        check0();
    end
    endtask

    task mem_read_word_1(input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A1 = addr;//[9:2];
        WE = {SIZE{8'h00}};
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORD: 0x%X from %0D", Do1, addr);
`endif
        check1();
    end
    endtask

    task mem_read_2words(input [A_W-1:0] addr0,
            input [A_W-1:0] addr1);
    begin
        @(posedge CLK);
        A0= addr0;//[9:2];
        A1= addr1;//[9:2];
        WE = 4'b0;
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORD0: 0x%X from %0D", Do0, addr0);
        $display("READ WORD1: 0x%X from %0D", Do1, addr1);
`endif
        check0();
        check1();
    end
    endtask

    task check0; begin
        if(RAM_DATA0 !== Do0) begin
            $display("\n>>Test Failed! <<\t(Phase: %0d, Iteration: %0d", Phase, i);
            $display("Address: 0x%X, READ: 0x%X - Should be: 0x%X", A0, Do0, RAM[A0/4]);
            $fatal(1);
        end
    end
    endtask

    task check1; begin
        if(RAM_DATA1 !== Do1) begin
            $display("\n>>Test Failed! <<\t(Phase: %0d, Iteration: %0d", Phase, i);
            $display("Address: 0x%X, READ: 0x%X - Should be: 0x%X", A1, Do1, RAM[A1/4]);
            $fatal(1);
        end
    end
    endtask
endmodule
