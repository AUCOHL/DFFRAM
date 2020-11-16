# DFFRAM
Standard Cell Library based Memory Compiler using DFF cells

The objective of this project is to develop DFF-based RAM and Register File (RegF) compiler that utilizes standard cell libraries following a standard ASIC implementation approach. The compiler generates different views (HDL netlist, HDL functional models, LEF, GDS, Timing, …) for a given configuration set. 

The layout generated from the compiler will be highly compacted (we target over 95% placement density) as the cells are placed on the floor plan using a custom placer. Moreover, the custom placer ensures that the routing will be a seamless one. The project will consider the creation of a custom router if automatic routing using open-source global and detailed routers does not give good results. 

Currenly, the repo has only a handcrafted parameterized memory (1, 2 or 4 kbytes) targeting the SKY130 PDK. Also, it contains all the building blocks and a self-checking testbench. 

##Handcrafted Memory
Two modules are provided:
- [DFFRAM](https://github.com/shalan/DFFRAM/blob/ec4cad3cc4d421492ec9dbf9eb5d70b53d24aa03/Handcrafted/Models/DFFRAM.v#L1 "DFFRAM"): parameterized 1, 2 or 4 kbytes memory module.
- [DFFRAM_256x32](https://github.com/shalan/DFFRAM/blob/ec4cad3cc4d421492ec9dbf9eb5d70b53d24aa03/Handcrafted/Models/DFFRAM_256x32.v#L1 "DFFRAM_256x32"): 1kbyte memory module

### Memory Interface
| Port  | Direction  | Size  | Function |
| ------------ | ------------ | ------------ |
| CLK | input  | 1  | Clock (positive edge triggered) |
| EN  | input | 1 | Memory enable. Do is 0 when memory is disabled |
| WE | input  |  4 | Write enable (byte level) |
| A | input  | 8, 9, 10  | Address lines |
| Di  | input  | 32  | Data in |
| Do  | output  | 32  | Data out |

###Simulating the Memory
The [file](https://github.com/shalan/DFFRAM/blob/ec4cad3cc4d421492ec9dbf9eb5d70b53d24aa03/Handcrafted/Verification/tb_DFFRAM.v#L1 "file") contains a self checking testbench that can be simulated using [Icarus Verilog](https://iverilog.fandom.com/wiki/Main_Page). Also, it contains a [behavioral model ](https://github.com/shalan/DFFRAM/blob/ec4cad3cc4d421492ec9dbf9eb5d70b53d24aa03/Handcrafted/Verification/tb_DFFRAM.v#L50-L60) for the memory. 

To run the simulation, you need to have the SKY130 open PDK installed. A [makefile](https://github.com/shalan/DFFRAM/blob/97f1ade330a06a4fc2ffbabe576d7cff9f222448/Handcrafted/Verification/Makefile#L1 "makefile") is provided to run the simulation.

### Hardening the Memory
Untill the compiler is ready, you may use [OpenLANE](https://github.com/efabless/openlane "OpenLANE") to harden the memory. Make sure that the flow configuration parameter `SYNTH_READ_BLACKBOX_LIB` is set to 1. A smaple OpenLANE design configuration file can be found [here](https://github.com/shalan/DFFRAM/blob/22d62832ef3b4b1d53bcfc8cb2460ff20d21449f/Handcrafted/OpenLANE/config.tcl#L1 "here").

When hardened using OpenLANE, the DFFRAM_256x32 achieved a placement density of 85%. We target above 95% placement density using the DDFRAM compiler custom placer. 

