/*
    An auto generated testbench to verify RAM{word_num}x{word_size}
    Authors: Mohamed Shalan (mshalan@aucegypt.edu)
             Ahmed Nofal (nofal.o.ahmed@gmail.com)
*/
`define     VERBOSE_1
`define     VERBOSE_2

`define     UNIT_DELAY  #1

`define     USE_LATCH   1

`define tb_DFFRF_module(count, width) tb_DFFRF``count``x``width``_2R1W
`define tb_DFFRF_module_vcd_file(count, width) `"tb_DFFRF``count``x``width``_2R1W.vcd`"


/* Those macros are passed on the command line */
/* `define     RWIDTH */
/* `define     RCOUNT */
/* `include `MODEL_FILEPATH */

`include "hd_primitives.v"
`include "hd_functional.v"

`include "../platforms/sky130A/BB/rf/model.v"


module `tb_DFFRF_module(`RCOUNT, `RWIDTH);

    localparam RWIDTH = `RWIDTH;
    localparam RCOUNT = `RCOUNT;
    localparam SIZE = RWIDTH/8;
    localparam A_W = $clog2(RWIDTH);

    reg  [4:0]               RA, RB, RW;
    reg  [(RWIDTH-1):0]      DW;
    wire [(RWIDTH-1):0]      DA, DB;
    reg                      CLK;
    reg  [7:0]               Phase;
    reg  [7:0]               RANDOM_BYTE;
    reg                      WE;
    event                    done;

    DFFRF_2R1W #(.RWIDTH(RWIDTH), .RCOUNT(RCOUNT), .R0_ZERO(1) ) RFILE
    (   .RA(RA),
        .RB(RB),
        .RW(RW),
        .DW(DW),
        .DA(DA),
        .DB(DB),
        .CLK(CLK),
        .WE(WE)
    );

    initial begin
        $dumpfile(`tb_DFFRF_module_vcd_file(`RCOUNT, `RWIDTH));
        $dumpvars(0, `tb_DFFRF_module(`RCOUNT, `RWIDTH));
        @(done) $finish;
    end

     /* Memory golden Model */
    reg [(RWIDTH-1):0]      DFFRF[(RCOUNT-1):0];
    reg [(RWIDTH-1):0]      DFFRF_DATA_READA;
    reg [(RWIDTH-1):0]      DFFRF_DATA_READB;

    always @(posedge CLK) begin
        DFFRF_DATA_READA <= DFFRF[RA];
        DFFRF_DATA_READB <= DFFRF[RB];
        if(WE) DFFRF[RW] <= DW;
    end

    always #10 CLK = !CLK;

    integer i;

    initial begin
        CLK = 0;
        WE = 0;

        Phase = 0;
        // Perform a 2 word write then read 2 words
        mem_write_word({SIZE{8'h90}}, 4);
        mem_write_word({SIZE{8'h33}}, 8);
        mem_read_2words(4,8);

/***********************************************************

        Write and read from different ports

************************************************************/

        // Fill the memory with a known pattern
        // Word Write then Read
        Phase = 1;
`ifdef  VERBOSE_1
        $display("\n\tFinished Phase 0, starting Phase 1\n");
`endif
        for(i=1; i<RCOUNT; i=i+1) begin
            RANDOM_BYTE = $urandom;
            mem_write_word({SIZE{RANDOM_BYTE}}, i);
            mem_read_word_B(i);
        end


/***********************************************************

        Write and read from same port

************************************************************/
        Phase = 2;
`ifdef  VERBOSE_1
        $display("\n\tFinished Phase 1, starting Phase 2\n");
`endif
        for(i=1; i<RCOUNT; i=i+1) begin
            RANDOM_BYTE = $urandom;
            mem_write_word({SIZE{RANDOM_BYTE}}, i);
            mem_read_word_A(i);
        end

        Phase = 3;
`ifdef  VERBOSE_1
        $display("\n\tFinished Phase 2, starting Phase 3\n");
`endif
        for(i=1; i<RCOUNT; i=i+1) begin
            RANDOM_BYTE = $urandom;
            mem_read_2words_write_1($urandom % RCOUNT, 
                $urandom % RCOUNT, 
                $urandom % RCOUNT, 
                {SIZE{RANDOM_BYTE}});
        end

        $display ("\n>> Test Passed! <<\n");
        -> done;
    end

/***********************************************************

        TASKS

************************************************************/
    task mem_write_word(input [RWIDTH-1:0] word, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        RW = addr;
        WE = 1;
        DW = word;
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE WORD: 0x%X to %D", word, addr);
`endif
        WE = 0;
    end
    endtask

    task mem_read_word_A(input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        RA = addr;//[9:2];
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORD A: 0x%X from %D", DA, RA);
`endif
        checkA();
    end
    endtask

    task checkA; begin
        if(DFFRF_DATA_READA !== DA) begin
            $display("\n>>Test Failed! CheckA <<\t(Phase: %0d, Iteration: %0d", Phase, i);
            $display("Register: %D, READ: 0x%X - Should be: 0x%X", RA, DA, DFFRF[RA]);
            $fatal(1);
        end
    end
    endtask

    task mem_read_word_B(input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        RB = addr;
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORD B: 0x%X from %0D", DB, RB);
`endif
        checkB();
    end
    endtask

    task checkB; begin
        if(DFFRF_DATA_READB !== DB) begin
            $display("\n >>Test Failed! checkB << \t(Phase: %0d, Iteration: %0d", Phase, i);
            $display("Register: %D, READ: 0x%X - Should be: 0x%X", RB, DB, DFFRF[RB]);
            $fatal(1);
        end
    end
    endtask

    task mem_read_2words(input [A_W-1:0] addr0,
            input [A_W-1:0] addr1);
    begin
        @(posedge CLK);
        RA= addr0;
        RB= addr1;
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORDA: 0x%X from %D", DA, addr0);
        $display("READ WORDB: 0x%X from %D", DB, addr1);
`endif
        checkA();
        checkB();
    end
    endtask
    task mem_read_2words_write_1(input [A_W-1:0] addrA,

            input [A_W-1:0] addrB,
            input [A_W-1:0] addrW, 
            input [RWIDTH-1:0] dataW);
    begin
        @(posedge CLK);
        RA= addrA;
        RB= addrB;
        RW= addrW;
        DW= dataW;
        WE= 1;
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORDA: 0x%X from %D", DA, addrA);
        $display("READ WORDB: 0x%X from %D", DB, addrB);
        $display("WRITE WORD: 0x%X to %D", dataW, addrW);
`endif
        checkA();
        checkB();
        WE= 0;
    end
    endtask

endmodule
