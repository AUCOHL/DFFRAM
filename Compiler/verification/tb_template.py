# Copyright ©2020-2021 The American University in Cairo and the Cloud V Project.
#
# This file is part of the DFFRAM Memory Compiler.
# See https://github.com/Cloud-V/DFFRAM for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

changeable_sub = """
/*
    An auto generated testbench to verify RAM{word_num}x{word_size}
    Author: Mohamed Shalan (mshalan@aucegypt.edu)
*/
`define     VERBOSE_1
`define     VERBOSE_2

`define     UNIT_DELAY  #1

`define     USE_LATCH   1

`define     SIZE        {word_size}/8

//`include "libs.ref/sky130_fd_sc_hd/verilog/primitives.v"
//`include "libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"

`include "hd_primitives.v"
`include "hd_functional.v"

`include "{filename}"

module tb_RAM{word_num}x{word_size};

    localparam SIZE = `SIZE;
    localparam A_W = {addr_width}+$clog2(SIZE);
    localparam M_SZ = 2**A_W;

    reg                     CLK;
    reg  [(SIZE-1):0]       WE;
    reg                     EN;
    reg  [(SIZE*8-1):0]     Di;
    wire  [(SIZE*8-1):0]     Do;
    reg  [A_W-1:0]          A, ADDR;
    reg  [3:0]              HEX_DIG;
    reg  [7:0]              Phase;
    reg  [7:0]      RANDOM_BYTE;

    event           done;

    RAM{word_num} #(.USE_LATCH(`USE_LATCH), .WSIZE(SIZE)) SRAM (
        .CLK(CLK),
        .WE(WE),
        .EN(EN),
        .Di(Di),
        .Do(Do),
        .A(A[A_W-1:$clog2(SIZE)])
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
    reg [(SIZE*8-1):0]      RAM[(M_SZ)-1 : 0];
    reg [(SIZE*8-1):0]      RAM_DATA;

    genvar c;
    generate
    for (c=0; c < SIZE; c = c+1) begin: mem_golden_model
        always @(posedge CLK) begin
            if(EN) begin
                RAM_DATA <= RAM[A/SIZE];
                if(WE[c]) RAM[A/SIZE][8*(c+1)-1:8*c] <= Di[8*(c+1)-1:8*c];
            end
        end
    end
    endgenerate
    // always @(posedge CLK)
    //     if(EN) begin
    //         RAM_DATA <= RAM[A/4];
    //         if(WE[0]) RAM[A/4][ 7: 0] <= Di[7:0];
    //         if(WE[1]) RAM[A/4][15:8] <= Di[15:8];
    //         if(WE[2]) RAM[A/4][23:16] <= Di[23:16];
    //         if(WE[3]) RAM[A/4][31:24] <= Di[31:24];
    //     end

    initial begin
        CLK = 0;
        WE = 0;
        EN = 1;

        Phase = 0;
        // Perform a single word write then read
        mem_write_word({SIZE{8'h90}}, 4);
        mem_read_word(4);

        // Word Write then Read
        Phase = 1;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 0, starting Phase 1");
`endif
        for(i=0; i<M_SZ; i=i+SIZE) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFC ;
            RANDOM_BYTE = $urandom;
            mem_write_word( {SIZE{RANDOM_BYTE}}, ADDR);
            mem_read_word( ADDR );
        end

        // HWord Write then Read
        Phase = 2;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 1, starting Phase 2");
`endif
        for(i=0; i<M_SZ; i=i+SIZE/2) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFE;
            RANDOM_BYTE = $urandom;
            mem_write_hword( {SIZE/2{RANDOM_BYTE}}, ADDR);
            mem_read_word( ADDR & {{SIZE-1{8'hFF}}, 8'hFC} );
        end

        // Byte Write then Read
        Phase = 3;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 2, starting Phase 3");
`endif
        for(i=0; i<M_SZ; i=i+1) begin
            ADDR = (($urandom%M_SZ));
            mem_write_byte($urandom%255, ADDR);
            mem_read_word(ADDR & {{SIZE-1{8'hFF}}, 8'hFC} );
        end
        $display ("\\n>> Test Passed! <<\\n");
        -> done;
    end

    task mem_write_byte(input [7:0] byte, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A = addr;//[A_WIDTH:2];
        WE = (1 << addr[$clog2(SIZE)-1:0]);
        Di = (byte << (addr[$clog2(SIZE)-1:0] * 8));
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE BYTE: 0x%X to %0X(%0D) (0x%X, %B)", byte, addr, addr, Di, WE);
`endif
        WE = {SIZE{8'h00}};
    end
    endtask

    task mem_write_hword(input [SIZE*8-1:0] hword, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A = addr;//[A_WIDTH:$clog2(SIZE)];
        WE = {{SIZE/2{addr[$clog2(SIZE)-1]}},{SIZE/2{~addr[$clog2(SIZE)-1]}}};
        Di = (hword << (addr[$clog2(SIZE)-1] * (SIZE/2)*8));
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE HWORD: 0x%X to %0X(%0D) (0x%X, %B)", hword, addr, addr, Di, WE);
`endif
        WE = {SIZE{8'h00}};
    end
    endtask

    task mem_write_word(input [SIZE*8-1:0] word, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A = addr;
        WE = {SIZE{8'hFF}};
        Di = word;
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE WORD: 0x%X to %0X(%0D) (0x%X, %B)", word, addr, addr, Di, WE);
`endif
        WE = {SIZE{8'h00}};
    end
    endtask

    task mem_read_word(input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A = addr;//[9:2];
        WE = {SIZE{8'h00}};
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
