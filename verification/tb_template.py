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

RAM_instantiation = """
/*
    An auto generated testbench to verify RAM{word_num}x{word_size}
    Authors: Mohamed Shalan (mshalan@aucegypt.edu)
             Ahmed Nofal (nofal.o.ahmed@gmail.com)
*/
`define     VERBOSE_1
`define     VERBOSE_2

`define     UNIT_DELAY  #1

`define     USE_LATCH   1

`define     SIZE        {word_size}/8

//`include "{pdk_root}/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v"
//`include "{pdk_root}/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"
// // Temporary override: IcarusVerilog cannot read these for some reason ^
`include "hd_primitives.v"
`include "hd_functional.v"

`include "{filename}"

module tb_RAM{word_num}x{word_size};

    localparam SIZE = `SIZE;
    localparam A_W = {addr_width}+$clog2(SIZE);
    localparam M_SZ = 2**A_W;

    reg                     CLK;
    reg  [(SIZE-1):0]       WE0;
    reg                     EN0;
    reg  [(SIZE*8-1):0]     Di0;
    wire [(SIZE*8-1):0]     Do0;
    reg  [A_W-1:0]          A0, ADDR;
    reg  [7:0]              Phase;
    reg  [7:0]      RANDOM_BYTE;

    event           done;

    RAM{word_num} #(.USE_LATCH(`USE_LATCH), .WSIZE(SIZE)) SRAM (
        .CLK(CLK),
        .WE0(WE0),
        .EN0(EN0),
        .Di0(Di0),
        .Do(Do0),
        .A0(A0[A_W-1:$clog2(SIZE)])
    );

    initial begin
        $dumpfile("tb_RAM{word_num}x{word_size}.vcd");
        $dumpvars(0, tb_RAM{word_num}x{word_size});
        @(done) $finish;
    end

     /* Memory golden Model */
    reg [(SIZE*8-1):0]      RAM[(M_SZ)-1 : 0];
    reg [(SIZE*8-1):0]      RAM_DATA_RW;

    genvar c;
    generate
    for (c=0; c < SIZE; c = c+1) begin: mem_golden_model
        always @(posedge CLK) begin
            if(EN0) begin
                RAM_DATA_RW <= RAM[A0/SIZE];
                if(WE0[c]) RAM[A0/SIZE][8*(c+1)-1:8*c] <= Di0[8*(c+1)-1:8*c];
            end
        end
    end
    endgenerate
"""

begin_single_ported_test = """
    initial begin
        CLK = 0;
        WE0 = 0;
        EN0 = 1;
"""

single_ported_custom_test = """
        Phase = 0;
        // Perform a single word write then read
        mem_write_word({{SIZE{{8'h90}}}}, 4);
        mem_read_word_0(4);
"""

RAM_instantiation_1RW1R = """
/*
    An auto generated testbench to verify RAM{word_num}x{word_size}
    Authors: Mohamed Shalan (mshalan@aucegypt.edu)
             Ahmed Nofal (nofal.o.ahmed@gmail.com)
*/
`define     VERBOSE_1
`define     VERBOSE_2

`define     UNIT_DELAY  #1

`define     USE_LATCH   1

`define     SIZE        {word_size}/8
//`include "{pdk_root}/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v"
//`include "{pdk_root}/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"
// // Temporary override: IcarusVerilog cannot read these for some reason ^
`include "hd_primitives.v"
`include "hd_functional.v"

`include "{filename}"

module tb_RAM{word_num}x{word_size}_1RW1R;

    localparam SIZE = `SIZE;
    localparam A_W = {addr_width}+$clog2(SIZE);
    localparam M_SZ = 2**A_W;

    reg                   CLK;
    reg  [(SIZE-1):0]       WE0;
    reg                  EN0;
    reg                  ENR;
    reg  [(SIZE*8-1):0]   Di0;
    wire [(SIZE*8-1):0]   Do0;
    wire [(SIZE*8-1):0]   Do1;
    reg  [A_W-1:0]  A0, A1, ADDR;
    reg  [7:0]      Phase;
    reg  [7:0]      RANDOM_BYTE;
    event           done;

    RAM{word_num}_1RW1R #(.USE_LATCH(`USE_LATCH), .WSIZE(`SIZE)) SRAM (
        .CLK(CLK),
        .WE0(WE0),
        .EN0(EN0),
        .EN1(ENR),
        .Di0(Di0),
        .Do0(Do0),
        .Do1(Do1),
        .A0(A0[A_W-1:$clog2(SIZE)]),
        .A1(A1[A_W-1:$clog2(SIZE)])
    );

    initial begin
        $dumpfile("tb_RAM{word_num}x{word_size}_1RW1R.vcd");
        $dumpvars(0, tb_RAM{word_num}x{word_size}_1RW1R);
        @(done) $finish;
    end

     /* Memory golden Model */
    reg [(SIZE*8-1):0]      RAM[(M_SZ)-1 : 0];
    reg [(SIZE*8-1):0]      RAM_DATA_RW;
    reg [(SIZE*8-1):0]      RAM_DATA_R;

    genvar c;
    generate
    for (c=0; c < SIZE; c = c+1) begin: mem_golden_model
        always @(posedge CLK) begin
            if(EN0) begin
                RAM_DATA_RW <= RAM[A0/SIZE];
                if(WE0[c]) RAM[A0/SIZE][8*(c+1)-1:8*c] <= Di0[8*(c+1)-1:8*c];
            end
            if (ENR) begin
                RAM_DATA_R <= RAM[A1/SIZE];
            end
        end
    end
    endgenerate
"""

begin_dual_ported_test = """

    initial begin
        CLK = 0;
        WE0 = 0;
        EN0 = 1;
        ENR = 1;

"""

dual_ported_custom_test = """
        Phase = 0;
        // Perform a 2 word write then read 2 words
        mem_write_word({{SIZE{{8'h90}}}}, 4);
        mem_write_word({{SIZE{{8'h33}}}}, 8);
        mem_read_2words(4,8);

"""

start_test_common = """
    always #10 CLK = !CLK;

    integer i;
"""

test_port_1RW1R = """
/***********************************************************

        Write and read from different ports

************************************************************/

        // Fill the memory with a known pattern
        // Word Write then Read
        Phase = 1;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 0, starting Phase 1");
`endif
        for(i=0; i<M_SZ; i=i+SIZE) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFC ;
            RANDOM_BYTE = $urandom;
            mem_write_word( {SIZE{RANDOM_BYTE}}, ADDR);
            mem_read_word_1( ADDR );
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
            mem_read_word_1( ADDR & {{SIZE-1{8'hFF}}, 8'hFC} );
        end

        // Byte Write then Read
        Phase = 3;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 2, starting Phase 3");
`endif
        for(i=0; i<M_SZ; i=i+1) begin
            ADDR = (($urandom%M_SZ));
            mem_write_byte($urandom%255, ADDR);
            mem_read_word_1(ADDR & {{SIZE-1{8'hFF}}, 8'hFC} );
        end

"""

test_port_RW = """
/***********************************************************

        Write and read from same port

************************************************************/
        Phase = 4;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 3, starting Phase 4");
`endif
        for(i=0; i<M_SZ; i=i+SIZE) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFC ;
            RANDOM_BYTE = $urandom;
            mem_write_word( {SIZE{RANDOM_BYTE}}, ADDR);
            mem_read_word_0( ADDR );
        end

        // HWord Write then Read
        Phase = 5;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 4, starting Phase 5");
`endif
        for(i=0; i<M_SZ; i=i+SIZE/2) begin
            ADDR = (($urandom%M_SZ)) & 'hFFFF_FFFE;
            RANDOM_BYTE = $urandom;
            mem_write_hword( {SIZE/2{RANDOM_BYTE}}, ADDR);
            mem_read_word_0( ADDR & {{SIZE-1{8'hFF}}, 8'hFC} );
        end

        // Byte Write then Read
        Phase = 6;
`ifdef  VERBOSE_1
        $display("\\nFinished Phase 5, starting Phase 6");
`endif
        for(i=0; i<M_SZ; i=i+1) begin
            ADDR = (($urandom%M_SZ));
            mem_write_byte($urandom%255, ADDR);
            mem_read_word_0(ADDR & {{SIZE-1{8'hFF}}, 8'hFC} );
        end
        $display ("\\n>> Test Passed! <<\\n");
        -> done;
"""

end_test = """
    end
"""

tasks = """
    task mem_write_byte(input [7:0] byte, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A0 = addr;//[A_WIDTH:2];
        WE0 = (1 << addr[$clog2(SIZE)-1:0]);
        Di0 = (byte << (addr[$clog2(SIZE)-1:0] * 8));
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE BYTE: 0x%X to %0X(%0D) (0x%X, %B)", byte, addr, addr, Di0, WE0);
`endif
        WE0 = {SIZE{8'h00}};
    end
    endtask

    task mem_write_hword(input [SIZE*8-1:0] hword, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A0 = addr;//[A_WIDTH:$clog2(SIZE)];
        WE0 = {{SIZE/2{addr[$clog2(SIZE)-1]}},{SIZE/2{~addr[$clog2(SIZE)-1]}}};
        Di0 = (hword << (addr[$clog2(SIZE)-1] * (SIZE/2)*8));
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE HWORD: 0x%X to %0X(%0D) (0x%X, %B)", hword, addr, addr, Di0, WE0);
`endif
        WE0 = {SIZE{8'h00}};
    end
    endtask

    task mem_write_word(input [SIZE*8-1:0] word, input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A0 = addr;
        WE0 = {SIZE{8'hFF}};
        Di0 = word;
        @(posedge CLK);
`ifdef  VERBOSE_2
        $display("WRITE WORD: 0x%X to %0X(%0D) (0x%X, %B)", word, addr, addr, Di0, WE0);
`endif
        WE0 = {SIZE{8'h00}};
    end
    endtask

    task mem_read_word_0(input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A0 = addr;//[9:2];
        WE0 = {SIZE{8'h00}};
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORD: 0x%X from %0D", Do0, addr);
`endif
        check0();
    end
    endtask

    task check0; begin
        if(RAM_DATA_RW !== Do0) begin
            $display("\\n>>Test Failed! <<\\t(Phase: %0d, Iteration: %0d", Phase, i);
            $display("Address: 0x%X, READ: 0x%X - Should be: 0x%X", A0, Do0, RAM[A0/SIZE]);
            $fatal(1);
        end
    end
    endtask

"""
dual_ported_tasks = """
    task mem_read_2words(input [A_W-1:0] addr0,
            input [A_W-1:0] addr1);
    begin
        @(posedge CLK);
        A0= addr0;//[9:2];
        A1= addr1;//[9:2];
        WE0 = {SIZE{8'h00}};
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

    task mem_read_word_1(input [A_W-1:0] addr);
    begin
        @(posedge CLK);
        A1 = addr;//[9:2];
        WE0 = {SIZE{8'h00}};
        @(posedge CLK);
        #5;
`ifdef  VERBOSE_2
        $display("READ WORD: 0x%X from %0D", Do1, addr);
`endif
        check1();
    end
    endtask

    task check1; begin
        if(RAM_DATA_R !== Do1) begin
            $display("\\n>>Test Failed! <<\\t(Phase: %0d, Iteration: %0d", Phase, i);
            $display("Address: 0x%X, READ: 0x%X - Should be: 0x%X", A1, Do1, RAM[A1/SIZE]);
            $fatal(1);
        end
    end
    endtask
"""

endmodule = """
endmodule
"""
