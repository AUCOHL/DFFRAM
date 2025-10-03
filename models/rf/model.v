// SPDX-License-Identifier: Apache-2.0
// Copyright ©2020-2022, The American University in Cairo
/* 
	Module: DFFRF_2R1W
    Author: Mohamed Shalan (mshalan@aucegypt.edu)
	32x32 Register File with 2RW1W ports and clock gating for SKY130A 
	~ 3550 Cells
	< 2ns (no input or output delays)
*/

`timescale 1ns / 1ps
`default_nettype none

module DFFRF_2R1W #(parameter   WSIZE=32,
                                RCOUNT=32,
                                R0_ZERO=1 )
(
	input   wire    [4:0]                   RA, RB, RW,
	input   wire    [WSIZE-1:0]         	DW,
	output  wire    [WSIZE-1:0]        	DA, DB,
	input   wire                            CLK,
	input   wire                            WE
);
	wire [RCOUNT-1:0] sel1, sel2, selw;

	DEC5x32 DEC0 ( .A(RA), .SEL(sel1) );
	DEC5x32 DEC1 ( .A(RB), .SEL(sel2) );
	DEC5x32 DEC2 ( .A(RW), .SEL(selw) );
	
	generate
		genvar e;
        if(R0_ZERO == 1)
            RFWORD0 #(.WSIZE(WSIZE)) RFW0 ( .CLK(CLK), .SEL1(sel1[0]), .SEL2(sel2[0]), .SELW(selw[0]), .D1(DA), .D2(DB));	
        else
            RFWORD #(.WSIZE(WSIZE)) RFW0 ( .CLK(CLK), .WE(WE), .SEL1(sel1[0]), .SEL2(sel2[0]), .SELW(selw[0]), .D1(DA), .D2(DB), .DW(DW) );

        for(e=1; e<RCOUNT; e=e+1) begin : REGF 
			RFWORD #(.WSIZE(WSIZE)) RFW ( .CLK(CLK), .WE(WE), .SEL1(sel1[e]), .SEL2(sel2[e]), .SELW(selw[e]), .D1(DA), .D2(DB), .DW(DW) );	
        end
	endgenerate
endmodule
